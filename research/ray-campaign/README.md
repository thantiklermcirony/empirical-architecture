# Ray Serve: recovery after controller replacement

Candidate investigation for [ray-project/ray#63784](https://github.com/ray-project/ray/issues/63784), based on source and native runtime `80142bad1d1db176f19c7e3aff6b6448631e66c2`.

**Status: validated scoped candidate, not submitted upstream or accepted by Ray.** [Linux run 34425598056](https://github.com/thantiklermcirony/empirical-architecture/actions/runs/34425598056) passes the real HTTP comparison, all 30 selected tests and applicable source checks. The original returns the old application in all 60 probes; the candidate returns the new application in all 60 probes, over a 30-second observation window. Both preserve their original HAProxy manager while replacing the controller actor.

Read [the contribution report](Ray_Contribution_Report.md), [validation record](Ray_Validation.json), or [download the complete evidence package](Ray_Contribution_Package.zip).

## The problem

A surviving service can keep serving old routes after its controller is replaced with a new actor. Its subscription remains attached to the dead actor. The candidate gives HAProxyManager an opt-in way to find the replacement through its stable name, then reload the replacement's state. Deliberate shutdown cancels recovery and waits for pending configuration work before stopping HAProxy.

The existing [PR #63785](https://github.com/ray-project/ray/pull/63785) addresses checkpoint compatibility and diagnostics. This experiment targets the remaining subscription recovery behavior. Its narrower scope does not enable automatic recovery for every Serve consumer.

## What the framework contributes

Our working method is to turn a perspective change into a falsifiable state contract: a stable name is not an actor incarnation, and a snapshot version is meaningful only within that incarnation. The regression deliberately replaces the host while reusing the same version number. That prevents accidental success caused by random version differences.

This is a concrete distributed-systems engineering test. It does not establish that the broader scientific framework is uniquely necessary for this fix, nor does it measure AI model quality or compute savings.

## Evidence and reproduction

- `candidate.patch`: the implementation and regression tests, against the pinned source.
- `baseline-current.json` and `candidate-current-final.json`: actual Windows/native Ray actor transport before and after; distinct actor IDs, both using snapshot version 7.
- `candidate-reconnect-final.xml`: 14 passing cases: 13 actor lifecycle regressions and the HAProxy shutdown unit.
- `candidate-runtime-final.json` and `candidate-manifest.json`: source identities and hashes.
- `reproduce_haproxy.py` and `HAPROXY_REPRODUCTION.md`: the isolated Linux HTTP experiment, including evidence and cleanup requirements.
- The [Ray controller replacement validation](https://github.com/thantiklermcirony/empirical-architecture/actions/workflows/ray-recovery.yml) Actions workflow stores before/after records, test logs and environment details. Inspect its artifacts and classifications; failed or inconclusive runs remain failed evidence.

The local baseline delivers only `epoch-A` and stops; the candidate delivers `epoch-A` then `epoch-B`. Timing in these records describes individual controlled runs, not a production latency guarantee. A separate unit test checks that shutdown waits for cancellation cleanup before stopping HAProxy.

## Limits and upstream handoff

Only HAProxyManager enables replacement discovery. Standard proxy, router and metrics consumers have separate ownership and retained-handle concerns. The long-poll protocol also distinguishes a published empty value from a key that a new host never publishes; resetting versions does not invent a missing publication.

Ray's [contribution policy](https://github.com/ray-project/ray/blob/80142bad1d1db176f19c7e3aff6b6448631e66c2/AGENTS.md) requires human review, human-run local tests, AI disclosure, duplicate-work checks and signed-off commits. This evidence package is preparation for that review. It is not a claim of maintainer endorsement or an upstream pull request.

