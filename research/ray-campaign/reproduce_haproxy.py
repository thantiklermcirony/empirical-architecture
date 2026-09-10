#!/usr/bin/env python3
"""Linux-only, isolated Serve/HAProxy experiment for ray-project/ray#63784.

This file is a prospective integration harness, not a claimed passing test.
See HAPROXY_REPRODUCTION.md for environment setup, scope and evidence rules.
The parent process never imports Ray. Only its marked child starts a local cluster.
"""

import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import uuid


PIN = "80142bad1d1db176f19c7e3aff6b6448631e66c2"
MARKER_ENV = "RAY_ISSUE63784_REPRO_RUN"
ROUTE = "/probe-63784"
OLD_BODY = "catch-all:issue63784"
NEW_BODY = "new-route:issue63784"
MODULES = ("long_poll", "haproxy", "api", "controller", "client", "proxy", "router")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    pending.replace(path)


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.STDOUT, timeout=20
    )


@contextlib.contextmanager
def bounded(seconds, phase):
    """Bound synchronous Serve APIs as well as our explicit ray.get calls.

    A separate supervisor enforces a hard total bound if a native call ignores
    Python's signal. This process is dedicated to the experiment.
    """
    def expired(_signum, _frame):
        raise TimeoutError(f"Phase exceeded {seconds}s: {phase}")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def free_ports(count):
    # Hold all reservations simultaneously so these ports are distinct. There is
    # an unavoidable bind race after release; a collision invalidates the run.
    with contextlib.ExitStack() as stack:
        sockets = [stack.enter_context(socket.socket()) for _ in range(count)]
        for sock in sockets:
            sock.bind(("127.0.0.1", 0))
        return [sock.getsockname()[1] for sock in sockets]


def manager_snapshot(actor):
    """Read only, executed through Ray's DeveloperAPI __ray_call__ method."""
    import hashlib
    from pathlib import Path

    import ray
    from ray.serve._private import haproxy, long_poll

    lp = actor.long_poll_client
    hp = actor._haproxy
    cfg = Path(hp.config_file_path)
    raw = cfg.read_bytes() if cfg.exists() else b""
    process = hp._proc
    return {
        "class_name": type(actor).__name__,
        "actor_id": ray.get_runtime_context().get_actor_id(),
        "node_id": ray.get_runtime_context().get_node_id(),
        "manager_pid": os.getpid(),
        "long_poll_running": lp.is_running,
        "long_poll_host_id": lp.host_actor._actor_id.hex(),
        "snapshot_ids": {str(k): v for k, v in lp.snapshot_ids.items()},
        "target_groups": [group.model_dump(mode="json") for group in actor._target_groups],
        "haproxy_pid": process.pid if process is not None else None,
        "haproxy_returncode": process.returncode if process is not None else None,
        "config_path": str(cfg),
        "config_sha256": hashlib.sha256(raw).hexdigest(),
        "config_mtime_ns": cfg.stat().st_mtime_ns if cfg.exists() else None,
        "config_text": raw.decode(errors="replace"),
        "source_sha256": {
            "long_poll": hashlib.sha256(Path(long_poll.__file__).read_bytes()).hexdigest(),
            "haproxy": hashlib.sha256(Path(haproxy.__file__).read_bytes()).hexdigest(),
        },
    }


def run_worker(args):
    data = {
        "schema": 1, "label": args.label, "base_commit": PIN,
        "classification": "invalid", "phase": "preflight",
        "run_dir": args.run_dir, "started_at_unix": time.time(),
        "parameters": {"phase_timeout": args.phase_timeout,
                       "observe_seconds": args.observe_seconds,
                       "outage_seconds": args.outage_seconds},
        "expected": {"route": ROUTE, "old_body": OLD_BODY, "new_body": NEW_BODY},
    }
    ray = None
    managers = {}

    def checkpoint(phase):
        data["phase"] = phase
        write_json(args.output, data)

    try:
        root = Path(args.source_root).resolve()
        assert git(root, "rev-parse", "HEAD").decode().strip() == PIN, (
            "Use a checkout at the pinned commit, with the candidate as an uncommitted patch."
        )
        diff = git(root, "diff", "--binary", PIN, "--", "python/ray")
        untracked = git(root, "ls-files", "--others", "--exclude-standard", "--", "python/ray")
        untracked_paths = untracked.decode().splitlines()
        data["source"] = {
            "root": str(root), "head": PIN, "diff_sha256": hashlib.sha256(diff).hexdigest(),
            "untracked_sha256": {path: sha(root / path) for path in untracked_paths},
        }
        Path(args.output).with_suffix(".source.diff").write_bytes(diff)
        if args.label == "baseline":
            assert not untracked_paths, "Baseline must contain no untracked Python source."
            assert not diff, "Baseline must contain no Python changes from the pinned commit."
        else:
            assert diff, "Candidate must contain a recorded Python patch against the pin."

        # Set before importing Ray or Serve; child Ray processes inherit these.
        run_dir = Path(args.run_dir)
        http_port, stats_port, metrics_port = free_ports(3)
        settings = {
            "RAY_SERVE_ENABLE_HA_PROXY": "1",
            "RAY_SERVE_HAPROXY_CONFIG_FILE_LOC": str(run_dir / "haproxy.cfg"),
            "RAY_SERVE_HAPROXY_SOCKET_PATH": str(run_dir / "admin.sock"),
            "RAY_SERVE_HAPROXY_METRICS_SOCKET_PATH": str(run_dir / "metrics.sock"),
            "RAY_SERVE_HAPROXY_SERVER_STATE_BASE": str(run_dir),
            "RAY_SERVE_HAPROXY_SERVER_STATE_FILE": str(run_dir / "server-state"),
            "RAY_SERVE_HAPROXY_STATS_PORT": str(stats_port),
            "RAY_SERVE_HAPROXY_METRICS_PORT": str(metrics_port),
            "RAY_USAGE_STATS_ENABLED": "0",
        }
        os.environ.update(settings)
        # address='local' also prevents RAY_ADDRESS from selecting another cluster.
        os.environ.pop("RAY_ADDRESS", None)
        os.environ.pop("RAY_NAMESPACE", None)
        import ray
        import ray._raylet
        from ray import serve
        from ray.serve.api import RunTarget
        from ray.serve._private.constants import SERVE_CONTROLLER_NAME, SERVE_NAMESPACE
        from ray.serve._private.haproxy import get_haproxy_binary
        from ray.serve.context import _get_global_client
        from starlette.responses import PlainTextResponse
        import requests

        modules = {}
        for name in MODULES:
            module = __import__(f"ray.serve._private.{name}", fromlist=[name])
            source = root / "python/ray/serve/_private" / f"{name}.py"
            assert sha(module.__file__) == sha(source), f"Wrong imported source: {name}"
            modules[name] = {"path": str(Path(module.__file__).resolve()), "sha256": sha(source)}
        core_path = Path(ray._raylet.__file__).resolve()
        # setup-dev over a wheel is supported only when its native runtime is pinned.
        # A full editable source build can retain the templated commit string.
        built_in_source = core_path.is_relative_to(root)
        assert ray.__commit__ == PIN or (built_in_source and ray.__commit__ == "{{RAY_COMMIT_SHA}}"), (
            f"Ray native build is not identified with the pin: {ray.__commit__!r}, {core_path}"
        )
        hp_binary = Path(get_haproxy_binary()).resolve()
        hp_version = subprocess.check_output([str(hp_binary), "-vv"], timeout=10).decode()
        data["runtime"] = {
            "python": sys.version, "platform": platform.platform(),
            "ray_version": ray.__version__, "ray_commit": ray.__commit__,
            "ray_core_sha256": sha(core_path), "modules": modules,
            "haproxy_binary": str(hp_binary), "haproxy_sha256": sha(hp_binary),
            "haproxy_version": hp_version,
            "packages": sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()),
        }
        data["settings"] = settings
        data["http_port"] = http_port
        checkpoint("start_cluster")
        with bounded(args.phase_timeout, "ray.init"):
            info = ray.init(address="local", num_cpus=4, include_dashboard=False,
                            namespace=f"repro63784-{args.run_id}",
                            _temp_dir=str(run_dir / "ray"),
                            runtime_env={"env_vars": {MARKER_ENV: args.run_id}})
        data["cluster_address"] = info.address_info["address"]
        start_options = {"proxy_location": "HeadOnly", "http_options": {"host": "127.0.0.1", "port": http_port}}
        with bounded(args.phase_timeout, "initial serve.start"):
            serve.start(**start_options)
        controller = _get_global_client()._controller

        @serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.25})
        class Marker:
            def __init__(self, body):
                self.body = body

            async def __call__(self, request):
                return PlainTextResponse(self.body)

            def marker(self):
                return self.body

        session = requests.Session()
        session.trust_env = False
        url = f"http://127.0.0.1:{http_port}"

        def request(path):
            start = time.monotonic()
            try:
                response = session.get(url + path, timeout=2, allow_redirects=False,
                                       headers={"Connection": "close"})
                return {"status": response.status_code, "body": response.text,
                        "elapsed_seconds": time.monotonic() - start}
            except requests.RequestException as exc:
                return {"error": str(exc), "elapsed_seconds": time.monotonic() - start}

        def exact(response, body):
            return response.get("status") == 200 and response.get("body") == body

        def wait_for(predicate, label, timeout=None):
            deadline = time.monotonic() + (timeout or args.phase_timeout)
            last = None
            while time.monotonic() < deadline:
                last = predicate()
                if last:
                    return last
                time.sleep(0.25)
            raise TimeoutError(f"Timed out: {label}; last={last!r}")

        def proxies():
            return ray.get(controller.get_proxies.remote(), timeout=5)

        def ids(handles):
            return {str(node): handle._actor_id.hex() for node, handle in handles.items()}

        def snapshots(handles):
            result = {str(node): ray.get(handle.__ray_call__.remote(manager_snapshot), timeout=5)
                      for node, handle in handles.items()}
            for value in result.values():
                assert value["class_name"] == "HAProxyManager", value
                assert value["haproxy_pid"] and value["haproxy_returncode"] is None, value
                assert Path(value["config_path"]).resolve().is_relative_to(run_dir), value
                for name in ("long_poll", "haproxy"):
                    assert value["source_sha256"][name] == modules[name]["sha256"]
            return result

        def app_running(name):
            details = ray.get(controller.get_serve_instance_details.remote(), timeout=5)
            status = details.get("applications", {}).get(name, {}).get("status")
            return details if status == "RUNNING" else None

        def deploy(name, body, route):
            with bounded(args.phase_timeout, f"deploy {name}"):
                handles = serve.run_many(
                    [RunTarget(target=Marker.bind(body), name=name, route_prefix=route)],
                    wait_for_ingress_deployment_creation=False,
                    wait_for_applications_running=False,
                )
            wait_for(lambda: app_running(name), f"{name} RUNNING")
            assert handles[0].marker.remote().result(timeout_s=10) == body
            return handles[0]

        checkpoint("deploy_catch_all")
        deploy("catchall", OLD_BODY, "/")
        wait_for(lambda: exact(request(ROUTE + "/check"), OLD_BODY), "initial catch-all body")
        managers = wait_for(proxies, "HAProxy manager exists")
        assert len(managers) == 1, "This bounded harness expects one HeadOnly manager."
        old_controller_id = controller._actor_id.hex()
        initial_ids = ids(managers)
        data["before"] = {"controller_id": old_controller_id, "manager_ids": initial_ids,
                          "managers": snapshots(managers), "probe": request(ROUTE + "/check")}

        checkpoint("replace_controller")
        # no_restart=False is the same actor identity and does not reproduce #63784.
        ray.kill(controller, no_restart=True)

        def old_name_gone():
            try:
                found = ray.get_actor(SERVE_CONTROLLER_NAME, namespace=SERVE_NAMESPACE)
            except ValueError:
                return True
            return found._actor_id.hex() != old_controller_id

        with bounded(args.phase_timeout, "old controller name disappears"):
            wait_for(old_name_gone, "old controller name gone")
        # Give the in-flight long poll time to receive its terminal actor error.
        outage_end = time.monotonic() + args.outage_seconds
        while time.monotonic() < outage_end:
            time.sleep(max(0, min(0.25, outage_end - time.monotonic())))
        data["during_outage"] = snapshots(managers)
        with bounded(args.phase_timeout, "replacement serve.start"):
            serve.start(**start_options)
        controller = _get_global_client()._controller
        new_controller_id = controller._actor_id.hex()
        assert new_controller_id != old_controller_id, "Controller identity did not change."
        current = wait_for(proxies, "replacement controller discovers proxies")
        assert ids(current) == initial_ids, "Manager actors were recreated; this is a different scenario."
        wait_for(lambda: app_running("catchall"), "catch-all recovered from checkpoint")
        wait_for(lambda: exact(request("/"), OLD_BODY), "catch-all survives replacement")
        data["replacement"] = {"controller_id": new_controller_id, "manager_ids": ids(current),
                               "managers": snapshots(managers)}

        checkpoint("deploy_new_route")
        new_handle = deploy("newroute", NEW_BODY, ROUTE)
        data["new_application"] = app_running("newroute")
        data["direct_new_replica_body"] = new_handle.marker.remote().result(timeout_s=10)
        checkpoint("observe_http")
        observed = []
        started = time.monotonic()
        while time.monotonic() - started < args.observe_seconds:
            result = request(ROUTE + "/check")
            result["seconds_after_deploy"] = time.monotonic() - started
            observed.append(result)
            time.sleep(0.5)
        data["observations"] = observed
        final_proxies = proxies()
        final = snapshots(managers)
        data["after"] = {"controller_id": controller._actor_id.hex(),
                         "manager_ids": ids(final_proxies), "managers": final,
                         "catch_all_probe": request("/")}
        assert ids(final_proxies) == initial_ids, "Manager identity changed during observation."
        assert exact(data["after"]["catch_all_probe"], OLD_BODY), "Catch-all stopped serving."
        assert app_running("newroute"), "New app stopped running."
        assert len(observed) >= 3, "Insufficient observations."
        recovered = (
            all(exact(item, NEW_BODY) for item in observed[-3:])
            and all(item["long_poll_running"] and item["long_poll_host_id"] == new_controller_id
                    and ROUTE in item["config_text"]
                    and any(group.get("route_prefix") == ROUTE for group in item["target_groups"])
                    for item in final.values())
        )
        stale = (
            all(exact(item, OLD_BODY) for item in observed)
            and all(not item["long_poll_running"] and item["long_poll_host_id"] == old_controller_id
                    and ROUTE not in item["config_text"]
                    and not any(group.get("route_prefix") == ROUTE for group in item["target_groups"])
                    for item in final.values())
        )
        data["classification"] = "recovered" if recovered else "stale_reproduced" if stale else "inconclusive"
        data["expected_result_met"] = data["classification"] == (
            "stale_reproduced" if args.label == "baseline" else "recovered"
        )
    except BaseException as exc:
        data["error"] = f"{type(exc).__name__}: {exc}"
        data["traceback"] = traceback.format_exc()
        data["expected_result_met"] = False
    finally:
        data["last_experiment_phase"] = data["phase"]
        checkpoint("cleanup")
        cleanup = []
        if ray is not None and ray.is_initialized():
            try:
                with bounded(35, "Serve shutdown"):
                    from ray import serve
                    serve.shutdown()
                cleanup.append("serve.shutdown completed")
            except BaseException as exc:
                cleanup.append(f"Serve shutdown: {type(exc).__name__}: {exc}")
            # Handles belong exclusively to the cluster created above. If Serve
            # teardown failed, give surviving managers a bounded subprocess stop.
            for handle in managers.values():
                try:
                    ray.get(handle.shutdown.remote(), timeout=5)
                except Exception:
                    pass  # Already-dead managers are normal after serve.shutdown.
            try:
                with bounded(10, "Ray shutdown"):
                    ray.shutdown()
                cleanup.append("ray.shutdown completed")
            except BaseException as exc:
                cleanup.append(f"Ray shutdown: {type(exc).__name__}: {exc}")
        data["worker_cleanup"] = cleanup
        data["phase"] = "finished"
        data["finished_at_unix"] = time.time()
        write_json(args.output, data)
    return 0 if data.get("expected_result_met") else 1


def cleanup_owned_processes(run_id):
    """Never pkill/ray-stop: match this child's random inherited token exactly."""
    import psutil

    scan_errors = set()

    def scan():
        owned = []
        for proc in psutil.process_iter(["pid", "uids"]):
            if proc.pid == os.getpid() or proc.info["uids"].real != os.getuid():
                continue
            try:
                if proc.environ().get(MARKER_ENV) == run_id:
                    owned.append(proc)
            except psutil.NoSuchProcess:
                continue
            except psutil.AccessDenied:
                scan_errors.add(proc.pid)
        return owned

    terminated = set()
    # Re-scan for children created between discovery and parent termination.
    for _ in range(2):
        owned = scan()
        if not owned:
            break
        terminated.update(p.pid for p in owned)
        for proc in owned:
            with contextlib.suppress(psutil.NoSuchProcess):
                proc.terminate()
        _, alive = psutil.wait_procs(owned, timeout=5)
        for proc in alive:
            with contextlib.suppress(psutil.NoSuchProcess):
                proc.kill()
        psutil.wait_procs(alive, timeout=5)
    remaining = scan()
    return {"forced_cleanup_pids": sorted(terminated), "remaining_owned_pids": [p.pid for p in remaining],
            "inaccessible_same_uid_pids": sorted(scan_errors),
            "scope": "exact inherited random run token; no global process-name cleanup"}


def supervise(args):
    if sys.platform != "linux":
        raise SystemExit("Run this integration harness in an isolated Linux environment.")
    if sys.flags.optimize:
        raise SystemExit("Do not use python -O: this experiment requires its assertions.")
    if sys.prefix == sys.base_prefix:
        raise SystemExit("Activate a virtual environment first (Ray AGENTS.md).")
    import psutil  # Fail before cluster creation if scoped cleanup is unavailable.
    del psutil
    args.run_id = uuid.uuid4().hex
    args.run_dir = tempfile.mkdtemp(prefix="rh_", dir="/tmp")
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite prior evidence: {output}")
    args.output = str(output)
    env = os.environ.copy()
    env[MARKER_ENV] = args.run_id
    command = [sys.executable, str(Path(__file__).resolve()), "run", "--worker",
               "--label", args.label, "--source-root", str(Path(args.source_root).resolve()),
               "--output", str(output), "--run-id", args.run_id, "--run-dir", args.run_dir,
               "--phase-timeout", str(args.phase_timeout), "--observe-seconds", str(args.observe_seconds),
               "--outage-seconds", str(args.outage_seconds)]
    timed_out = False
    interrupted = False
    returncode = None
    with output.with_suffix(".log").open("w") as log:
        worker = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                  env=env, start_new_session=True)
        try:
            returncode = worker.wait(timeout=args.total_timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        except KeyboardInterrupt:
            interrupted = True
        finally:
            cleanup = cleanup_owned_processes(args.run_id)
            with contextlib.suppress(subprocess.TimeoutExpired):
                worker.wait(timeout=5)
    data = json.loads(output.read_text()) if output.exists() else {
        "schema": 1, "label": args.label, "base_commit": PIN, "classification": "invalid"
    }
    data["supervisor"] = {"total_timeout_seconds": args.total_timeout,
                          "timed_out": timed_out, "interrupted": interrupted,
                          "worker_returncode": returncode, "run_dir": args.run_dir,
                          "cleanup": cleanup, "harness_sha256": sha(__file__)}
    if (timed_out or interrupted or cleanup["remaining_owned_pids"]
            or data.get("phase") != "finished"
            or (data.get("expected_result_met") and returncode != 0)):
        data["classification"] = "invalid"
        data["expected_result_met"] = False
    write_json(output, data)
    print(json.dumps({"output": str(output), "classification": data["classification"],
                      "expected_result_met": data.get("expected_result_met", False)}))
    return 0 if data.get("expected_result_met") else 1


def compare(args):
    baseline = json.loads(Path(args.baseline).read_text())
    candidate = json.loads(Path(args.candidate).read_text())
    checks = {
        "correct_labels": baseline.get("label") == "baseline" and candidate.get("label") == "candidate",
        "baseline_reproduced": baseline.get("classification") == "stale_reproduced",
        "candidate_recovered": candidate.get("classification") == "recovered",
        "same_pin": baseline.get("base_commit") == candidate.get("base_commit") == PIN,
        "same_protocol": baseline.get("expected") == candidate.get("expected")
                         and baseline.get("parameters") == candidate.get("parameters"),
        "same_harness": baseline.get("supervisor", {}).get("harness_sha256")
                        == candidate.get("supervisor", {}).get("harness_sha256"),
    }
    for key in ("python", "platform", "ray_version", "ray_commit", "ray_core_sha256",
                "haproxy_sha256", "packages"):
        checks[f"same_{key}"] = baseline.get("runtime", {}).get(key) == candidate.get("runtime", {}).get(key)
    checks["no_owned_processes_remain"] = all(
        item.get("supervisor", {}).get("cleanup", {}).get("remaining_owned_pids") == []
        for item in (baseline, candidate)
    )
    result = {"schema": 1, "checks": checks, "comparison_passed": all(checks.values()),
              "baseline": str(Path(args.baseline).resolve()),
              "candidate": str(Path(args.candidate).resolve()),
              "claim": "single-node CPU HTTP route propagation after different-ID controller replacement",
              "not_tested": ["multi-node EKS", "models/GPU", "gRPC", "autoscaling",
                             "all controller-owned client lifetimes", "long-duration reliability"]}
    write_json(args.output, result)
    print(json.dumps(result, indent=2))
    return 0 if result["comparison_passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--label", choices=("baseline", "candidate"), required=True)
    run.add_argument("--source-root", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--phase-timeout", type=float, default=90)
    run.add_argument("--observe-seconds", type=float, default=30)
    run.add_argument("--outage-seconds", type=float, default=4)
    run.add_argument("--total-timeout", type=float, default=480)
    run.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    run.add_argument("--run-id", help=argparse.SUPPRESS)
    run.add_argument("--run-dir", help=argparse.SUPPRESS)
    comparison = commands.add_parser("compare")
    comparison.add_argument("--baseline", required=True)
    comparison.add_argument("--candidate", required=True)
    comparison.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "compare":
        return compare(args)
    if min(args.phase_timeout, args.observe_seconds, args.outage_seconds, args.total_timeout) <= 0:
        parser.error("Timeouts and observation durations must be positive.")
    if args.observe_seconds < 5 or args.outage_seconds < 2:
        parser.error("Use at least 5s observation and 2s controller absence.")
    return run_worker(args) if args.worker else supervise(args)


if __name__ == "__main__":
    raise SystemExit(main())
