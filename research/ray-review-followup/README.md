# Ray PR #66039 follow-up review bundle

This is a proposed, unsubmitted follow-up to original PR commit `3f7ccd74a11a64e813e6e4e158ac0c994a1c2a8c`. Review `Ray_Followup.patch`: it contains only the three-file delta, SHA256 `ed1680fe02bb545cfa95c67093152190c37336a4bd56611f0bab8a445c88a0e5`.

The change retries `GetTimeoutError` from named-actor lookup, adds a real-actor test with that specific resolver outcome injected, verifies `RuntimeError` and `RaySystemError` remain terminal, and adds the required `__main__` entrypoint to both new test files. The test controls the lookup result; it does not simulate a live GCS outage. This follow-up does not change its lifecycle behavior.

## Linux validation

Publish the support files in this directory under `research/ray-review-followup/` on the owner's `empirical-architecture` audit branch `audit/ray-review-followup`, and copy `ray-review-followup.yml` to `.github/workflows/ray-review-followup.yml`. The branch push triggers validation; workflow dispatch is also available. The workflow never commits, pushes, or modifies upstream.

Both jobs fetch original base `80142bad1d1db176f19c7e3aff6b6448631e66c2`, fetch the exact submitted PR commit from `thantiklermcirony/ray`, verify its parent and file hashes, and apply the delta after verifying its SHA256. The original five-file PR remains intact, including its BUILD registration. Full source is checked out for normal fixtures and type resolution.

The runtime job uses Python 3.12 and the official matching Linux wheel with SHA256 `59d62dcfdf70053b47875c4e354e04bcbfaab107e8f8365b03d1e8644f7f7a41`. It installs dependencies once, records `pip freeze`, and runs:

1. The unmodified upstream `ci/lint/pytest_checker.py` CLI on both new files: expected missing-entrypoint failure before, success after. Its input is selected-path query JSON matching the files identified by Buildkite; this is not execution of the full Bazel query.
2. The same three selected resolver tests against original LongPoll: the timeout regression must fail while both terminal-error cases pass.
3. All 15 candidate actor tests, the shutdown test, and all 16 existing LongPoll tests, in separate bounded processes with standard source conftest imports. Required skipped, missing, or errored cases fail validation.

The second job runs `pre-commit==3.5.0` using the full unchanged upstream configuration on all five PR files. No hook ID is skipped manually; normal file filtering applies. Formatter modifications, hook failures, and timeouts remain failures. This includes the BUILD entry for buildifier. Artifacts are uploaded even on failure. These runs do not repeat the full HTTP/HAProxy experiment; the implementation delta only changes the resolver exception policy.


The original human review and 14-case local test confirmation covered the submitted commit. This additional delta requires its own human review before updating the upstream PR. Validation results belong to their linked workflow run; preparing this bundle alone is not a passing result.
