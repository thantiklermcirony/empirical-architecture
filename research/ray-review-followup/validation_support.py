"""Small, bounded validation utilities; this module never imports Ray."""

import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

BASE = "80142bad1d1db176f19c7e3aff6b6448631e66c2"
SUBMITTED = "3f7ccd74a11a64e813e6e4e158ac0c994a1c2a8c"
DELTA = "ed1680fe02bb545cfa95c67093152190c37336a4bd56611f0bab8a445c88a0e5"
LP = "python/ray/serve/_private/long_poll.py"
HP = "python/ray/serve/_private/haproxy.py"
RECONNECT = "python/ray/serve/tests/test_long_poll_reconnect.py"
SHUTDOWN = "python/ray/serve/tests/unit/test_haproxy_manager_shutdown.py"
EXISTING = "python/ray/serve/tests/test_long_poll.py"
MARKER = "RAY_FOLLOWUP_VALIDATION_TOKEN"


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(folder):
    value = json.loads((folder / "followup-manifest.json").read_text(encoding="utf-8"))
    assert value["base_commit"] == BASE
    assert value["submitted_commit"] == SUBMITTED
    assert value["delta_sha256"] == DELTA == sha(folder / "Ray_Followup.patch")
    assert value["changed_files"] == [LP, RECONNECT, SHUTDOWN]
    return value


def verify_sources(root, value, phase="candidate"):
    for relative, hashes in value["files"].items():
        assert sha(root / relative) == hashes[f"{phase}_sha256"], relative


def cleanup_owned(token):
    """Clean only same-user processes inheriting this subprocess's random token."""
    import psutil

    owner = psutil.Process().username()
    inaccessible = set()

    def scan():
        found = []
        for process in psutil.process_iter():
            if process.pid == os.getpid():
                continue
            try:
                if process.username() == owner and process.environ().get(MARKER) == token:
                    found.append(process)
            except psutil.NoSuchProcess:
                continue
            except psutil.AccessDenied:
                inaccessible.add(process.pid)
        return found

    terminated = set()
    for _ in range(2):
        owned = scan()
        if not owned:
            break
        terminated.update(p.pid for p in owned)
        for process in owned:
            with contextlib.suppress(psutil.NoSuchProcess):
                process.terminate()
        _, alive = psutil.wait_procs(owned, timeout=5)
        for process in alive:
            with contextlib.suppress(psutil.NoSuchProcess):
                process.kill()
        psutil.wait_procs(alive, timeout=5)
    return {
        "terminated_owned_pids": sorted(terminated),
        "remaining_owned_pids": [p.pid for p in scan()],
        "inaccessible_pids": sorted(inaccessible),
        "scope": "Exact random inherited token and matching user; no global Ray stop",
    }


def run_stage(evidence, name, command, cwd, timeout, *, owned=False, input_text=None, env_extra=None):
    env = os.environ.copy()
    for name_to_remove in ["RAY_ADDRESS", "RAY_NAMESPACE", "PYTHONPATH", "RAY_SERVE_ENABLE_HA_PROXY"]:
        env.pop(name_to_remove, None)
    env.update(RAY_USAGE_STATS_ENABLED="0", RAY_ENABLE_AUTO_CONNECT="0", PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1")
    env.update(env_extra or {})
    token = uuid.uuid4().hex
    if owned:
        env[MARKER] = token
    record = {"name": name, "command": [str(x) for x in command], "started_at_unix": time.time(), "passed": False}
    print(f"START {name}", flush=True)
    process = None
    try:
        with (evidence / f"{name}.log").open("w", encoding="utf-8") as output:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output,
                                       stderr=subprocess.STDOUT, stdin=subprocess.PIPE if input_text else None,
                                       text=True, start_new_session=True)
            try:
                process.communicate(input=input_text, timeout=timeout)
                record["returncode"] = process.returncode
            except subprocess.TimeoutExpired:
                record["timed_out"] = True
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    finally:
        if owned:
            record["cleanup"] = cleanup_owned(token)
        record["finished_at_unix"] = time.time()
        record["passed"] = (record.get("returncode") == 0 and not record.get("timed_out")
                            and not record.get("cleanup", {}).get("remaining_owned_pids"))
        write_json(evidence / f"{name}-stage.json", record)
    print(f"END {name}: exit {record.get('returncode')}", flush=True)
    if not record["passed"]:
        print("\n".join((evidence / f"{name}.log").read_text(encoding="utf-8", errors="replace").splitlines()[-50:]), flush=True)
    return record


def junit(path):
    cases = list(ET.parse(path).getroot().iter("testcase"))
    return {
        "total": len(cases),
        "failed": [c.attrib["name"] for c in cases if c.find("failure") is not None],
        "errors": [c.attrib["name"] for c in cases if c.find("error") is not None],
        "skipped": [c.attrib["name"] for c in cases if c.find("skipped") is not None],
    }
