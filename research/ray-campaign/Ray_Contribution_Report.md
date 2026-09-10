# Ray Serve: restoring routing after controller replacement

**A tested reliability candidate for AI infrastructure. Not submitted upstream.**

Replacing Ray Serve's controller can leave a surviving HAProxy manager subscribed to the dead actor. The service still answers HTTP requests, but newly deployed routes can keep returning the old catch-all application. Our candidate resolves the controller through its stable name, resets snapshot versions for the new incarnation and resumes updates. Shutdown stops recovery and waits for pending configuration cleanup.

In the actual paired Linux experiment, all **60 baseline probes returned the wrong application** and all **60 candidate probes returned the new application**. Both used HTTP 200, showing why a health/status check alone would miss the defect. Each run replaced the controller actor while retaining its original HAProxy manager. The new application was independently confirmed healthy through its deployment handle.

| Executed check | Result |
| --- | --- |
| Original HAProxy HTTP behavior, 30-second observation | Stale routing reproduced: 60/60 old responses |
| Candidate HAProxy HTTP behavior, same protocol | Recovery: 60/60 new responses |
| Paired runtime/source/protocol comparison | Passed |
| New Linux actor lifecycle regressions | 13 passed |
| Complete existing `test_long_poll.py` | 16 passed |
| HAProxy shutdown ordering unit | 1 passed |
| Same 14 new cases on Windows native Ray | 14 passed |
| Applicable Linux formatting, type and build-file hooks | Passed; candidate files unchanged |

[Passing workflow and downloadable artifacts](https://github.com/thantiklermcirony/empirical-architecture/actions/runs/34425598056) · [Patch](candidate.patch) · [Machine-readable validation](Ray_Validation.json) · [Complete package](Ray_Contribution_Package.zip)

## What changed

`LongPollClient` accepts an optional resolver. On actor failure it retries discovery with bounded cadence and jitter, off the event loop, with at most one lookup in flight. It resets every current listener's version to -1 when it adopts the returned host. A cancelled or stopped client cannot accept late discovery results or queued callbacks. Existing clients without a resolver retain their stop-on-actor-failure behavior.

Only `HAProxyManager` opts in, using Ray's stable controller name and namespace. Its shutdown stops the subscription, cancels and awaits a pending coalesced configuration update, then stops HAProxy. Tests cover equal version numbers across different actor IDs, repeated replacement, unavailable names, same-ID native restarts, listeners added during discovery, explicit empty state, stopping at different phases, resolver failures and queued callbacks. The new actor file is registered in Ray's Bazel test list.

The patch is pinned to source/native commit `80142bad1d1db176f19c7e3aff6b6448631e66c2`. Its SHA-256 is `eee705a017b381dbcf78bfcdcd6a6c1d507941a6cc4595bf2f76e81e561fad3c`. The native Linux wheel checksum, installed dependencies, imported module hashes, actual HAProxy executable hash and actor identities are recorded. Baseline and candidate ran sequentially in the same environment with unchanged dependencies. The tests used actual upstream fixtures and native Ray transport.

## What the framework contributed

The useful distinction is between a stable label and the system it currently denotes. A snapshot version belongs to an actor incarnation, not to its reusable name. Turning that distinction into a test—different actor IDs, deliberately equal versions—exposes the missing state transition.

This extends the practical lesson from our Graphiti and NeuroGym work: identify information that a representation forgets, construct a case where that information changes the correct answer, then preserve the surrounding behavior. This is a useful engineering application. It does not prove that our framework is uniquely necessary to discover the defect or validate its broader scientific claims.

## Scope and remaining limits

The HTTP result is one single-node CPU experiment on a pinned current-main nightly. It does not establish multi-node/EKS behavior, GPU/vLLM operation, gRPC, autoscaling or long-duration reliability. The observation window begins after the new application is healthy; it is not a measurement of failover latency, uptime or throughput. No AI model-quality, compute-saving or market-value result is claimed.

Other Serve consumers retain separate controller handles or cache lifetimes and are not enabled for recovery here. The protocol distinguishes an explicitly empty publication from a key the new host never publishes; resetting versions does not manufacture a deletion event. A resolver lookup already running in an executor cannot be forcibly interrupted, although a stopped client discards its result.

Both HTTP experiments returned from Serve/Ray shutdown and needed no forced supervisor cleanup, but both logged a controller shutdown timeout after 30 seconds. That warning is preserved; these are not warning-free or fully graceful teardown results. The existing upstream test group left two tagged processes, which the scoped supervisor terminated. No inspectable tagged processes remained; three inaccessible same-user process environments could not be inspected. This is not a claim that every runner process was inspected.

The earlier [run 34425109302](https://github.com/thantiklermcirony/empirical-architecture/actions/runs/34425109302) was invalid: the harness counted Ray's fallback proxy as a HAProxy manager, and pytest selected the unbuilt source package. These setup errors were corrected, the failure evidence was retained, and the same candidate patch passed the subsequent run. Failed setup was never treated as evidence of recovery.

## Reproduce and review

Use [the workflow setup](VALIDATION_WORKFLOW.md) and [HTTP reproduction instructions](HAPROXY_REPRODUCTION.md). The core Linux driver command after the pinned environment is installed is:

```bash
python research/ray-campaign/run_validation.py \
  --source-root /absolute/path/to/pinned-ray-checkout \
  --evidence-dir /absolute/path/to/new-evidence-directory
```

The evidence directory must be new. The driver records exact subprocess commands and preserves failures. It applies the patch to a disposable checkout and does not commit, push to Ray or contact a shared cluster. The included Windows review script uses the already prepared local environment on this workstation.

## Upstream handoff

This work relates to [issue #63784](https://github.com/ray-project/ray/issues/63784). The existing [PR #63785](https://github.com/ray-project/ray/pull/63785) addresses checkpoint compatibility and diagnostics; our opt-in subscription recovery addresses a different remaining behavior. No competing Ray PR or upstream comment has been posted. The existing discussion and any new competing work must be checked again before submission.

AI assistance was used for investigation, code, tests and this report. Ray's [contribution policy](https://github.com/ray-project/ray/blob/80142bad1d1db176f19c7e3aff6b6448631e66c2/AGENTS.md) requires the submitting human to understand and defend the change, review every changed line and run relevant tests locally before requesting review. It also requires AI disclosure, duplicate-work explanation and DCO sign-off. Agent-run local tests and our own CI do not satisfy the human requirement by themselves.

Prepared 10 September 2026. This is a contribution candidate and review package, not maintainer acceptance.
