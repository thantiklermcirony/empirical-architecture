#!/usr/bin/env python3
"""Run local Linux validation; never push, commit, or contact a shared Ray cluster."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import traceback
import uuid


PIN = "80142bad1d1db176f19c7e3aff6b6448631e66c2"


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def diagnostics(result_path, evidence):
    """Archive bounded logs from only a run directory named in our own result."""
    if not result_path.exists():
        return None
    result = json.loads(result_path.read_text())
    directory = result.get("run_dir") or result.get("supervisor", {}).get("run_dir")
    if not directory:
        return None
    root = Path(directory).resolve()
    if root.parent != Path("/tmp") or not root.name.startswith("rh_"):
        raise ValueError(f"Unexpected experiment directory: {root}")
    selected, skipped, size = [], [], 0
    target = evidence / f"{result_path.stem}-diagnostics.tar.gz"
    with tarfile.open(target, "w:gz") as archive:
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            if path.suffix not in {".log", ".out", ".err", ".cfg", ".json"}:
                continue
            length = path.stat().st_size
            relative = str(path.relative_to(root))
            if length > 5 * 1024 * 1024 or size + length > 100 * 1024 * 1024:
                skipped.append(relative)
                continue
            archive.add(path, arcname=relative, recursive=False)
            size += length
            selected.append(relative)
    manifest = {"archive": str(target), "source": str(root), "bytes": size,
                "included": selected, "skipped_size_limit": skipped}
    write_json(evidence / f"{result_path.stem}-diagnostics.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--campaign-dir", default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()
    if sys.platform != "linux" or sys.prefix == sys.base_prefix:
        parser.error("Use Linux and an activated virtual environment.")
    source = Path(args.source_root).resolve()
    campaign = Path(args.campaign_dir).resolve()
    evidence = Path(args.evidence_dir).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    summary_path = evidence / "validation-summary.json"
    if summary_path.exists():
        parser.error(f"Refusing to overwrite evidence: {summary_path}")
    harness_path = campaign / "reproduce_haproxy.py"
    patch_path = campaign / "candidate.patch"
    summary = {"schema": 1, "base_commit": PIN, "started_at_unix": time.time(),
               "all_required_checks_passed": False, "stages": []}
    write_json(summary_path, summary)

    # Import the harness's scoped process cleanup only. Its module does not import
    # Ray; every Ray runtime lives in a separate marked subprocess.
    spec = importlib.util.spec_from_file_location("reproduction_harness", harness_path)
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    environment = os.environ.copy()
    environment.pop("RAY_ADDRESS", None)
    environment.pop("RAY_NAMESPACE", None)
    environment.pop("PYTHONPATH", None)
    environment["RAY_USAGE_STATS_ENABLED"] = "0"
    environment["PYTHONUNBUFFERED"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    # Tests exercise their standard proxy configuration. Real HAProxy is enabled
    # explicitly within the independent integration harness child.
    environment.pop("RAY_SERVE_ENABLE_HA_PROXY", None)

    def run(name, command, timeout, *, cwd=source, marked=False):
        record = {"name": name, "command": command, "timeout_seconds": timeout,
                  "started_at_unix": time.time(), "passed": False}
        summary["stages"].append(record)
        write_json(summary_path, summary)
        env = environment.copy()
        run_id = uuid.uuid4().hex
        if marked:
            env[harness.MARKER_ENV] = run_id
        proc = None
        print(f"START {name}", flush=True)
        try:
            with (evidence / f"{name}-stage.log").open("w") as log:
                proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    record["returncode"] = proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    record["timed_out"] = True
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=5)
        except Exception:
            record["error"] = traceback.format_exc()
        finally:
            if marked:
                record["cleanup"] = harness.cleanup_owned_processes(run_id)
            record["finished_at_unix"] = time.time()
            record["passed"] = (record.get("returncode") == 0
                                and not record.get("timed_out")
                                and not record.get("error")
                                and not record.get("cleanup", {}).get("remaining_owned_pids"))
            write_json(summary_path, summary)
        print(f"END {name}: {'PASS' if record['passed'] else 'FAIL'}", flush=True)
        if not record["passed"]:
            log_path = evidence / f"{name}-stage.log"
            if log_path.exists():
                print("\n".join(log_path.read_text(errors="replace").splitlines()[-60:]), flush=True)
        return record["passed"]

    try:
        actual_head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"],
                                              timeout=20).decode().strip()
        if actual_head != PIN:
            raise ValueError(f"Wrong source HEAD: {actual_head}")
        if not patch_path.is_file() or not patch_path.stat().st_size:
            raise ValueError("candidate.patch is absent or empty; no candidate was tested")
        for path in (harness_path, patch_path, Path(__file__).resolve()):
            summary.setdefault("inputs_sha256", {})[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            shutil.copy2(path, evidence / path.name)
        summary["scope"] = "single-node CPU HTTP recovery plus selected Ray LongPoll/HAProxy unit tests"
        run("installed-packages", [sys.executable, "-m", "pip", "freeze", "--all"], 30)
        # Import the actual standard conftest rather than masking it with stubs.
        if not run("fixture-imports", [sys.executable, "-c",
                    "import ray; import ray.tests.conftest; import ray.serve.tests.conftest; "
                    f"assert ray.__commit__ == '{PIN}'; print(ray.__version__, ray.__commit__)"], 60):
            raise RuntimeError("Standard fixture imports failed; see fixture-imports-stage.log")

        common = [sys.executable, str(harness_path), "run", "--source-root", str(source),
                  "--total-timeout", "300"]
        baseline_path = evidence / "haproxy-baseline.json"
        candidate_path = evidence / "haproxy-candidate.json"
        run("haproxy-baseline", [*common, "--label", "baseline", "--output", str(baseline_path)], 340)
        diagnostics(baseline_path, evidence)
        # Apply only to this disposable checkout. Never create an upstream commit.
        if not run("patch-check", ["git", "apply", "--check", str(patch_path)], 30):
            raise RuntimeError("candidate.patch does not apply cleanly to the pin")
        if not run("patch-apply", ["git", "apply", str(patch_path)], 30):
            raise RuntimeError("Applying candidate.patch failed")
        run("haproxy-candidate", [*common, "--label", "candidate", "--output", str(candidate_path)], 340)
        diagnostics(candidate_path, evidence)
        run("haproxy-comparison", [sys.executable, str(harness_path), "compare",
                                  "--baseline", str(baseline_path), "--candidate", str(candidate_path),
                                  "--output", str(evidence / "haproxy-comparison.json")], 30)

        test_base = "python/ray/serve/tests/"
        groups = [
            ("long-poll-reconnect", [test_base + "test_long_poll_reconnect.py"], 240),
            ("long-poll-existing", [test_base + "test_long_poll.py"], 360),
        ]
        # A shutdown regression may be a new file or an addition to a unit file.
        # Limit discovery to changed unit test files; don't run the entire HAProxy suite.
        tracked = subprocess.check_output(["git", "diff", "--name-only", PIN, "--", test_base + "unit"],
                                          cwd=source, timeout=20).decode().splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "--",
                                            test_base + "unit"], cwd=source, timeout=20).decode().splitlines()
        unit_files = sorted({p for p in tracked + untracked
                             if Path(p).name.startswith("test_") and p.endswith(".py")
                             and (source / p).is_file()})
        if unit_files:
            groups.append(("changed-unit-tests", unit_files, 180))
        summary["changed_unit_test_files"] = unit_files
        for name, files, timeout in groups:
            # Import the verified installed native package before pytest walks
            # source parents. The checkout's ray/__init__.py is not a native
            # build; Serve and test subpackages are linked by setup-dev.
            launcher = ("import ray, pytest; "
                        f"assert ray.__commit__ == '{PIN}'; "
                        "raise SystemExit(pytest.main())")
            command = [sys.executable, "-c", launcher, "-q", "--import-mode=importlib",
                       "--timeout=90", "--timeout-method=thread",
                       "-o", "asyncio_mode=auto", "-o", "asyncio_default_fixture_loop_scope=function",
                       f"--junitxml={evidence / (name + '.xml')}", *files]
            run(name, command, timeout, marked=True)
        summary["all_required_checks_passed"] = all(stage["passed"] for stage in summary["stages"])
    except Exception:
        summary["fatal_error"] = traceback.format_exc()
    finally:
        summary["finished_at_unix"] = time.time()
        write_json(summary_path, summary)
        lines = ["Ray controller replacement validation", "", f"Pinned source: `{PIN}`", "",
                 "| Stage | Outcome |", "| --- | --- |"]
        lines += [f"| {stage['name']} | {'PASS' if stage['passed'] else 'FAIL'} |" for stage in summary["stages"]]
        if summary.get("fatal_error"):
            lines += ["", "Validation stopped before all stages completed. See validation-summary.json."]
        lines += ["", "Baseline PASS means the bug was reproduced; candidate PASS means the scoped recovery contract passed.",
                  "A setup failure or missing result is not evidence of recovery.",
                  "All required checks passed: " + str(summary["all_required_checks_passed"]).lower()]
        report = "\n".join(lines) + "\n"
        (evidence / "validation-summary.md").write_text(report)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as stream:
                stream.write(report)
    return 0 if summary["all_required_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
