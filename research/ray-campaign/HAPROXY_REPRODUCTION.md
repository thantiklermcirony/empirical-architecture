# Linux Serve + HAProxy integration reproduction

Status: **authored and statically checked; not executed against Linux, Ray, or HAProxy in this task.** No success/failure JSON has been fabricated. The companion `reproduce_haproxy.py` is an experiment to run, not evidence that the implementation works.

The source contract is Ray commit `80142bad1d1db176f19c7e3aff6b6448631e66c2`, plus the candidate Python patch. The motivating report is [ray-project/ray#63784](https://github.com/ray-project/ray/issues/63784). Root owns duplicate checks and the LongPoll implementation; this harness changes neither Ray nor an external service.

## What the experiment establishes

One fresh CPU-only local Ray cluster starts real HAProxy through Serve's `HAProxyManager`, with a single `HeadOnly` manager. It deploys a plain-text catch-all at `/`, verifies that a future route currently returns `catch-all:issue63784`, kills the controller with `no_restart=True`, leaves its name absent for four seconds, and calls `serve.start()` to create a new controller actor. It requires the new controller's actor ID to differ and the original HAProxyManager actor ID to survive.

It then deploys `/probe-63784`, requires application status `RUNNING`, calls the new deployment directly to verify `new-route:issue63784`, and samples actual HTTP through HAProxy for 30 seconds. HTTP 200 alone does not pass: the exact body must come from the new deployment. The final three candidate responses must match; the baseline requires the wrong catch-all body throughout the observation window. Both also require that the old catch-all still serves at `/`.

Read-only `__ray_call__` snapshots record the manager class, identity, native HAProxy process PID, current long-poll host ID/running state, target groups, config content/hash/mtime, and hashes of the Python code imported inside the manager. `__ray_call__` is an existing Ray DeveloperAPI; the harness does not inject a synthetic long-poll failure or mutate manager state. The baseline classifier requires stopped polling tied to the dead controller and no new route in targets/config. The candidate classifier requires active polling tied to the replacement controller plus the new target/config route.

Actor recreation, checkpoint recovery failure, incorrect installed source, missing HAProxy, an unhealthy new application, port collisions, or a hard timeout produce an invalid experiment rather than a regression claim. Other HTTP outcomes are inconclusive. A finite stale observation demonstrates this reproduction window; it cannot prove that stale routing lasts forever.

## Linux environment

Use a disposable Linux x86-64 VM/container with local process/network access, a recent supported Python in a **virtual environment**, Git, and 4 logical CPUs. About 4–8 GiB RAM and at least 1 GiB `/dev/shm` are reasonable starting resources for runtime testing; a native Ray build needs substantially more RAM/time/disk. No GPU, model download, cloud account, EKS cluster, operational robot, or vehicle is involved. Do not point this at a shared cluster. Ray's direct ingress feature binds replica ports on all interfaces, so keep the disposable host/container network isolated.

Install Ray from the exact pinned source, including its Serve extras and `psutil`, using the repository's [pinned development guide](https://github.com/ray-project/ray/blob/80142bad1d1db176f19c7e3aff6b6448631e66c2/doc/source/ray-contribute/development.md). The full-build path requires the native compiler toolchain and Bazel specified there. After those prerequisites, the key virtual-environment commands are:

```bash
python3 -m venv /workspace/venv-baseline
source /workspace/venv-baseline/bin/activate
cd /workspace/ray-baseline/python
python -m pip install -r requirements.txt
python -m pip install -e '.[serve]' psutil
```

Repeat in a separate candidate checkout/environment at the same `HEAD`, with only the proposed Python changes applied. Keep candidate changes uncommitted for this harness, which enforces the pinned `HEAD`. The candidate JSON records the tracked patch and hashes untracked Python files such as newly added tests. Do not apply an implementation patch to the baseline. Save and review the patch before running.

An exact-commit Linux Ray wheel can avoid rebuilding native code. We separately verified this official CPython 3.12 Linux x86-64 wheel, with SHA-256 `59d62dcfdf70053b47875c4e354e04bcbfaab107e8f8365b03d1e8644f7f7a41`. Use Python 3.12 in both virtual environments. For each environment/check-out pair, substitute the appropriate path:

```bash
curl --fail --location \
  'https://s3-us-west-2.amazonaws.com/ray-wheels/master/80142bad1d1db176f19c7e3aff6b6448631e66c2/ray-3.0.0.dev0-cp312-cp312-manylinux2014_x86_64.whl' \
  --output /workspace/ray-3.0.0.dev0-cp312-cp312-manylinux2014_x86_64.whl
echo '59d62dcfdf70053b47875c4e354e04bcbfaab107e8f8365b03d1e8644f7f7a41  /workspace/ray-3.0.0.dev0-cp312-cp312-manylinux2014_x86_64.whl' | sha256sum --check
python -m pip install '/workspace/ray-3.0.0.dev0-cp312-cp312-manylinux2014_x86_64.whl[serve]' psutil
cd /workspace/ray-baseline
python python/ray/setup-dev.py -y --allow serve
```

Linking only `serve` is sufficient for this Python-only candidate and preserves the matching wheel's other modules/native binaries. The setup helper moves generated protobuf files into the source tree; they are generated build inputs, not candidate implementation changes. Follow the documented Python-only development workflow. Do not substitute an unpinned latest/release wheel and describe it as the pinned runtime. The harness verifies `ray.__commit__`, source hashes and native `_raylet` hash. A full editable source build with Ray's templated commit string is accepted only if `_raylet` resides within the pinned checkout. Retain build logs to substantiate that build provenance; the path check cannot independently prove native source provenance.

The pinned Serve extras specify `ray-haproxy>=2.8.25,<2.9.0` on Linux. Prefer that actual bundled executable for this source contract. A current system HAProxy can instead be selected with an absolute `RAY_SERVE_HAPROXY_BINARY_PATH`, provided it supports the Lua/features used by this source. Do not use a mock executable. The harness captures the chosen binary's SHA-256 and full `haproxy -vv` output. Use the **same binary, Ray native build, Python version and installed dependency versions** for baseline and candidate. An independently rebuilt native library may be nondeterministic; the strict comparator refuses unequal binaries even when both builds may be legitimate.

The script does not install packages, start a Docker daemon, alter a repository, or provision infrastructure. The driver rejects a non-Linux or non-venv runtime before starting Ray. A clean environment is recommended: unrelated pre-existing `RAY_SERVE_*` overrides can change the workload, so unset them except an intentional HAProxy binary override before running.

## Commands and artifacts

The following assumes Linux paths chosen when copying these two review files and source checkouts. Run sequentially, activating the appropriate environment for each:

```bash
/workspace/venv-baseline/bin/python /workspace/review/reproduce_haproxy.py run \
  --label baseline --source-root /workspace/ray-baseline \
  --output /workspace/evidence/haproxy-baseline.json

/workspace/venv-candidate/bin/python /workspace/review/reproduce_haproxy.py run \
  --label candidate --source-root /workspace/ray-candidate \
  --output /workspace/evidence/haproxy-candidate.json

/workspace/venv-candidate/bin/python /workspace/review/reproduce_haproxy.py compare \
  --baseline /workspace/evidence/haproxy-baseline.json \
  --candidate /workspace/evidence/haproxy-candidate.json \
  --output /workspace/evidence/haproxy-comparison.json
```

For a baseline run, exit 0 means the stale-route bug was reproduced. For a candidate run, exit 0 means the defined recovery contract passed. The compare command exits 0 only when baseline reproduces, candidate recovers, protocol/harness/runtime/dependency identities agree, and no marked processes remain. This distinction is intentional: a baseline that unexpectedly recovers is useful information, but it does not validate a candidate fix.

Each run writes a JSON result, a sibling `.log`, and a sibling `.source.diff`. Unique result paths prevent accidental overwriting of previous evidence. A short unique `/tmp/rh_*` directory holds Ray logs and per-node HAProxy configs/sockets/state. It is retained for diagnosis. Config paths are checked to stay inside that run directory; short paths avoid Linux Unix-socket path limits.

Explicit `ray.get` and HTTP calls have short timeouts, phases have a 90-second signal deadline, and a separate supervisor has a 480-second hard run bound. Allow a further roughly 25 seconds for forced cleanup. Observation/outage durations and limits can be changed by flags, but use identical flags for the paired runs. Defaults avoid speeding up the long-poll implementation's normal timing.

Cleanup first calls `serve.shutdown()` while Ray is alive, attempts a bounded shutdown on the original managers if necessary, then `ray.shutdown()`. The supervisor can terminate only same-user processes whose environment contains the exact random token inherited from its own experiment child. It never uses global `pkill`, `pgrep` as a kill list, or `ray stop`, and never connects using `address='auto'`. PID objects retain process creation identity through `psutil`; unrelated HAProxy/Ray processes are not selected. Forced cleanup PIDs, remaining marked PIDs and inaccessible same-user processes are recorded. If the operating system prevents process inspection, this cannot certify the absence of inaccessible leftovers; inspect the disposable environment before discarding it.

## Existing fixture references at the pin

- [test_haproxy.py](https://github.com/ray-project/ray/blob/80142bad1d1db176f19c7e3aff6b6448631e66c2/python/ray/serve/tests/test_haproxy.py): real HAProxy startup, manager actor identity/namespace and shutdown assertions; see `test_deploy_with_no_applications`, `test_single_app_shutdown_actors`, and `test_haproxy_subprocess_killed_on_manager_shutdown`. Its autouse fixture globally invokes `pkill -x haproxy`; this standalone harness intentionally uses only per-experiment cleanup.
- [conftest.py](https://github.com/ray-project/ray/blob/80142bad1d1db176f19c7e3aff6b6448631e66c2/python/ray/serve/tests/conftest.py): `_shared_serve_instance` uses a local CPU cluster and shuts Serve down before Ray because HAProxy subprocesses must stop while managers still run. The harness creates a dedicated cluster instead of consuming that shared fixture.
- [test_failure.py](https://github.com/ray-project/ray/blob/80142bad1d1db176f19c7e3aff6b6448631e66c2/python/ray/serve/tests/test_failure.py): `test_controller_failure` is skipped and uses `no_restart=False`; it does not test the different-ID replacement reported in #63784.
- [api.py](https://github.com/ray-project/ray/blob/80142bad1d1db176f19c7e3aff6b6448631e66c2/python/ray/serve/api.py): `run_many(..., wait_for_ingress_deployment_creation=False, wait_for_applications_running=False)` avoids using proxy readiness as the new-app health oracle. Public `serve.run(blocking=False)` still waits for app/proxy readiness before returning.
- [actor.py](https://github.com/ray-project/ray/blob/80142bad1d1db176f19c7e3aff6b6448631e66c2/python/ray/actor.py): existing `__ray_call__` DeveloperAPI supplies the read-only inspection hook.

## Limits and next integration step

This is a single-node HTTP case that preserves the exact lifecycle defect and user-visible wrong-backend response. It does not replicate the issue's four managers, Kubernetes networking, vLLM workload, gRPC, long-lived requests, autoscaling, or every remaining stale controller reference. Transport-level LongPoll actor tests remain useful separate evidence. A successful run should be adapted into the existing Linux HAProxy test fixture only after checking local timings and teardown behavior; do not call this a passing CI test until it has run there.

Ray's [AGENTS.md](https://github.com/ray-project/ray/blob/80142bad1d1db176f19c7e3aff6b6448631e66c2/AGENTS.md) also requires a human submitter to review and defend every line, run relevant tests locally, disclose AI assistance and duplicate-work checks, and sign commits. This note does not assert those submission requirements have been fulfilled.

