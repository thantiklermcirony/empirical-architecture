"""Validate a hash-pinned follow-up in an expendable Linux Ray checkout."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET

from validation_support import BASE, SUBMITTED, LP, RECONNECT, SHUTDOWN, EXISTING, junit, manifest, run_stage, sha, verify_sources, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "runtime", "lint"])
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()
    if sys.platform != "linux" or sys.prefix == sys.base_prefix:
        parser.error("Use Linux and a dedicated virtual environment")
    folder = Path(__file__).resolve().parent
    root = Path(args.source_root).resolve()
    evidence = Path(args.evidence_dir).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    summary = {"phase": args.phase, "passed": False, "base_commit": BASE,
               "submitted_commit": SUBMITTED, "bundle_commit": os.environ.get("GITHUB_SHA"), "stages": []}

    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(root), *arguments], timeout=60)

    def run(name, command, timeout=60, **kwargs):
        item = run_stage(evidence, name, command, root, timeout, **kwargs)
        summary["stages"].append(item)
        write_json(evidence / f"{args.phase}-summary.json", summary)
        return item

    def checker(name):
        checker_path = root / "ci/lint/pytest_checker.py"
        assert sha(checker_path) == value["pytest_checker_sha256"]
        item = run(name, [sys.executable, str(checker_path)], input_text=(folder / "selected-paths-query.json").read_text(encoding="utf-8"))
        item["scope"] = "Unmodified upstream checker CLI, selected two-path query JSON; full Bazel query not executed"
        return item

    def tests(name, paths, timeout, expected_count, selector=None, expected_failure=None):
        xml = evidence / f"{name}.xml"
        # The launcher verifies actual imported module paths and hashes, not
        # just the files that setup-dev was expected to link into the wheel.
        command = [sys.executable, str(folder / "run_source_pytest.py"),
                   "--source-root", str(root), "--identity-output", str(evidence / f"{name}-identity.json"),
                   "--implementation", "submitted" if expected_failure else "candidate", "--",
                   "-q", "--import-mode=importlib",
                   "--timeout=90", "--timeout-method=thread", "-o", "asyncio_mode=auto",
                   "-o", "asyncio_default_fixture_loop_scope=function", f"--junitxml={xml}", *paths]
        if selector:
            command.extend(["-k", selector])
        item = run(name, command, timeout, owned=True)
        if not xml.exists():
            item["error"] = "Pytest produced no JUnit report; collection/setup did not complete"
            item["passed"] = False
            return item
        parsed = junit(xml)
        item["junit"] = parsed
        valid_cases = parsed["total"] == expected_count and not parsed["errors"] and not parsed["skipped"]
        if expected_failure:
            # A setup error, timeout, unrelated failed test, or missing case is
            # never counted as successful reproduction of the regression.
            item["expected_failure"] = expected_failure
            failure_nodes = list(ET.parse(xml).getroot().iter("failure"))
            failure_text = failure_nodes[0].text or "" if len(failure_nodes) == 1 else ""
            item["expected_failure_assertion_matched"] = (
                "assert client.is_running" in failure_text
                and "E       assert False" in failure_text
                and failure_text.rstrip().endswith("AssertionError")
            )
            item["passed"] = (valid_cases and item.get("returncode") == 1
                              and parsed["failed"] == [expected_failure]
                              and item["expected_failure_assertion_matched"]
                              and not item.get("timed_out")
                              and not item.get("cleanup", {}).get("remaining_owned_pids"))
        else:
            item["passed"] = item["passed"] and valid_cases and not parsed["failed"]
        write_json(evidence / f"{name}-stage.json", item)
        return item

    try:
        value = manifest(folder)
        summary["delta_sha256"] = value["delta_sha256"]
        if args.phase == "prepare":
            assert git("rev-parse", "HEAD").decode().strip() == BASE
            assert not git("status", "--porcelain").strip(), "Checkout must start clean"
            # Fetch the immutable submitted commit, never a moving PR ref.
            assert run("fetch-submitted", ["git", "fetch", "--no-tags", "--depth=2",
                       "https://github.com/thantiklermcirony/ray.git", SUBMITTED], 180)["passed"]
            assert git("rev-parse", f"{SUBMITTED}^").decode().strip() == BASE
            assert run("checkout-submitted", ["git", "checkout", "--detach", SUBMITTED])["passed"]
            verify_sources(root, value, "submitted")
            before = checker("pytest-checker-before")
            before_log = (evidence / "pytest-checker-before.log").read_text(encoding="utf-8")
            before["expected_failure"] = "Both originally submitted files lack __main__"
            before["passed"] = (before.get("returncode") == 1 and not before.get("timed_out")
                                and "Found py_test files without" in before_log
                                and Path(RECONNECT).name in before_log and Path(SHUTDOWN).name in before_log)
            write_json(evidence / "pytest-checker-before-stage.json", before)
            assert before["passed"], "Original checker did not fail for the expected reason"
            assert run("delta-check", ["git", "apply", "--check", str(folder / "Ray_Followup.patch")])["passed"]
            assert run("delta-apply", ["git", "apply", str(folder / "Ray_Followup.patch")])["passed"]
            verify_sources(root, value)
            assert checker("pytest-checker-after")["passed"]
            for name in ["Ray_Followup.patch", "followup-manifest.json", "selected-paths-query.json"]:
                shutil.copy2(folder / name, evidence / name)
        else:
            assert git("rev-parse", "HEAD").decode().strip() == SUBMITTED
            verify_sources(root, value)
            if args.phase == "runtime":
                fixture_command = (f"import ray; assert ray.__commit__ == '{BASE}'; "
                                   "import ray.tests.conftest; import ray.serve.tests.conftest; "
                                   "print(ray.__version__, ray.__commit__)")
                assert run("standard-fixture-imports", [sys.executable, "-c", fixture_command])["passed"]
                assert run("pip-freeze", [sys.executable, "-m", "pip", "freeze", "--all"])["passed"]
                candidate = (root / LP).read_bytes()
                try:
                    (root / LP).write_bytes(git("show", f"{SUBMITTED}:{LP}"))
                    summary["baseline_implementation_sha256"] = sha(root / LP)
                    assert summary["baseline_implementation_sha256"] == value["files"][LP]["submitted_sha256"]
                    tests("submitted-timeout-regression", [RECONNECT], 240, 3,
                          selector="named_lookup_timeouts_are_retried or unexpected_resolver_error_is_terminal",
                          expected_failure="test_named_lookup_timeouts_are_retried")
                finally:
                    (root / LP).write_bytes(candidate)
                verify_sources(root, value)
                tests("candidate-reconnect", [RECONNECT], 480, 15)
                tests("candidate-shutdown", [SHUTDOWN], 180, 1)
                tests("existing-long-poll", [EXISTING], 480, 16)
                verify_sources(root, value)
                summary["scope"] = "Same native wheel and dependencies for before/after timeout policy; 32 candidate tests; no full HAProxy experiment or live GCS outage"
            else:
                files = sorted(set(git("diff", "--name-only", BASE).decode().splitlines()))
                expected = sorted([LP, "python/ray/serve/_private/haproxy.py", RECONNECT, SHUTDOWN,
                                   "python/ray/serve/tests/BUILD.bazel"])
                assert files == expected, files
                # Include all five PR files, including the existing Bazel entry.
                # All configured hooks run with normal file filtering; none are
                # manually skipped or marked successful after an error.
                summary["files"] = files
                original_diff = git("diff", "--binary", BASE)
                result = run("full-pre-commit", [sys.executable, "-m", "pre_commit", "run",
                             "--show-diff-on-failure", "--files", *files], 1800)
                final_diff = git("diff", "--binary", BASE)
                summary["candidate_unchanged_by_hooks"] = original_diff == final_diff
                (evidence / "after-hooks.diff").write_bytes(final_diff)
                (evidence / "after-hooks-status.txt").write_bytes(git("status", "--short"))
                result["passed"] = result["passed"] and summary["candidate_unchanged_by_hooks"]
                verify_sources(root, value)
        summary["passed"] = bool(summary["stages"]) and all(s["passed"] for s in summary["stages"])
    except Exception:
        summary["error"] = traceback.format_exc()
        print(summary["error"], flush=True)
    finally:
        write_json(evidence / f"{args.phase}-summary.json", summary)
        lines = [f"Ray follow-up {args.phase}: {'PASS' if summary['passed'] else 'FAIL'}", "",
                 f"Original PR commit: `{SUBMITTED}`", f"Native/base: `{BASE}`", ""]
        lines.extend(f"- {s['name']}: {'PASS' if s['passed'] else 'FAIL'}" for s in summary["stages"])
        lines += ["", "Expected baseline/checker failures are accepted only after their specific failure contracts match.",
                  "Missing results, setup errors, timeouts, skipped required tests, and formatter changes fail validation."]
        report = "\n".join(lines) + "\n"
        (evidence / f"{args.phase}-summary.md").write_text(report, encoding="utf-8")
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
                stream.write(report)
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
