#!/usr/bin/env python3
"""Run applicable upstream hooks on an applied patch in a disposable full clone."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


PIN = "80142bad1d1db176f19c7e3aff6b6448631e66c2"
HOOKS = ("buildifier", "buildifier-lint", "mypy", "pyrefly-serve", "docstyle",
         "ruff", "black", "pydoclint", "trailing-whitespace", "end-of-file-fixer", "check-ast")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()
    root = Path(args.source_root).resolve()
    patch = Path(args.patch).resolve()
    evidence = Path(args.evidence_dir).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    result = {"base_commit": PIN, "hooks": [], "all_checks_passed": False}

    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(root), *arguments], timeout=30)

    try:
        if git("rev-parse", "HEAD").decode().strip() != PIN:
            raise ValueError("Wrong source commit")
        if git("status", "--porcelain").strip():
            raise ValueError("Lint checkout is not clean before applying the patch")
        result["patch_sha256"] = hashlib.sha256(patch.read_bytes()).hexdigest()
        git("apply", "--check", str(patch))
        git("apply", str(patch))
        paths = sorted(set(git("diff", "--name-only", PIN).decode().splitlines()
                           + git("ls-files", "--others", "--exclude-standard").decode().splitlines()))
        if not paths:
            raise ValueError("No candidate files to check")
        result["files"] = paths
        initial = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}
        for hook in HOOKS:
            record = {"hook": hook, "started_at_unix": time.time()}
            result["hooks"].append(record)
            command = [sys.executable, "-m", "pre_commit", "run", hook,
                       "--show-diff-on-failure", "--files", *paths]
            record["command"] = command
            try:
                with (evidence / f"{hook}.log").open("w") as log:
                    completed = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                               timeout=300, check=False)
                record["returncode"] = completed.returncode
                record["passed"] = completed.returncode == 0
            except subprocess.TimeoutExpired:
                record["timed_out"] = True
                record["passed"] = False
            record["finished_at_unix"] = time.time()
            (evidence / "lint-summary.json").write_text(json.dumps(result, indent=2) + "\n")
            print(f"{hook}: {'PASS' if record['passed'] else 'FAIL'}", flush=True)
        final = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}
        result["candidate_files_unchanged_by_hooks"] = initial == final
        result["all_checks_passed"] = initial == final and all(hook["passed"] for hook in result["hooks"])
    except Exception:
        result["fatal_error"] = traceback.format_exc()
    finally:
        (evidence / "lint-summary.json").write_text(json.dumps(result, indent=2) + "\n")
        try:
            (evidence / "after-hooks.diff").write_bytes(git("diff", "--binary", PIN))
            (evidence / "after-hooks-status.txt").write_bytes(git("status", "--short"))
        except Exception:
            pass
        report = "Ray candidate Linux lint: " + ("PASS" if result["all_checks_passed"] else "FAIL") + "\n\n"
        report += "\n".join(f"- {item['hook']}: {'PASS' if item['passed'] else 'FAIL'}" for item in result["hooks"])
        report += "\n\nUses the pinned upstream hook configuration on candidate files; no native Ray runtime or tests in this job.\n"
        if result.get("fatal_error"):
            report += "Setup failed or the run was incomplete; see lint-summary.json.\n"
        (evidence / "lint-summary.md").write_text(report)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as stream:
                stream.write(report)
    return 0 if result["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
