# Mathematical foundations and executable theory atlas

Public distribution 0.1.1 of the reviewed mathematical atlas 0.1.0, 12 September 2026. This release makes the source inventory and execution paths portable; it preserves the mathematical results and the 16 original rule definitions.

Start with [the programme atlas](ATLAS.md), [actual source coverage](COVERAGE.md), [three ranked connections](CONNECTIONS.md), and [source findings](SOURCE_FINDINGS.md). [PROOFS.md](PROOFS.md) separates supplied human arguments from exact arithmetic. [MIGRATION.md](MIGRATION.md) describes the proposed register and the bounded admission interface.

The release contains 41 source records, 32 proposed rules, four common inquiry packages and four executable certificates. These span composition/geometry, adaptation/resources, observer/action/evidence and structural transfer. It is a set of authored mathematical fixtures with explicit application checks; it is not a general theorem prover or an empirical validation of the programme.

## Reproduce

Python 3.10 or later, using only the standard library. The checks were executed with Python 3.12.14. Obtain the exact source-text snapshots listed by filename and SHA-256 in `coverage.json`, then set `ATLAS_SOURCE_ROOT` to their directory. The original manuscripts and third-party environments are not bundled. Source links identify the works, but downloading or re-extracting a newer PDF is not guaranteed to reproduce these text hashes. Without the matching snapshots, source-bound execution is unavailable; the proofs, code and recorded receipts remain inspectable.

From this directory, in PowerShell:

```powershell
$env:ATLAS_SOURCE_ROOT = '/path/to/source-text-snapshots'
python -B run_all.py
python -B validate_atlas.py
```

On a POSIX shell:

```sh
export ATLAS_SOURCE_ROOT=/path/to/source-text-snapshots
python -B run_all.py
python -B validate_atlas.py
```

These commands regenerate `receipts/`. Use a copied checkout when comparing to the frozen manifest. Expected outcomes are four passed certificates, four admitted baseline packages, eight actual negative admission fixtures, preservation of 16 original rules within the 32-rule proposal, verification of 41 source hashes, and nine independently enumerated diagnostic risks. Authored check counts are not theorem-coverage metrics.

`python -B run_admission.py --case composition --package changed.json --out changed-report.json` checks a submitted package against the reviewed fixed contract. Missing required premises narrow the relevant conclusion; changed formulas are out of scope. The resource/diagnostic connection requires the exact admitted resource parent. The caller must choose trusted contracts and freshly produced receipts. Hashes are integrity evidence, not signatures or proof of scientific truth.

The optional [biology interface review](BIOLOGY_INTERFACE_REVIEW.md) recomputes 24 reported observer/target rows from an external biology package. It does not rerun that package's ODE. Its recorded source hashes identify the reviewed revision; the fixed-volume dependency correction must be considered when importing a newer revision.

## Publication scope

The public distribution preserves the four core certificate implementations and every original rule definition. It replaces host-specific source paths with `sources/<filename>`, removes internal producing-task identifiers, updates package/parent/receipt/contract integrity bindings, and records fresh public-distribution checks. The original base-register hash remains a historical provenance value; `public_base_register_sha256` identifies the portable base copy.

No hosted Site or central engine integration is claimed by publishing this directory. Empirical likelihoods, physical units and source calibration remain domain obligations. Full higher-dimensional classification and journal-version reconciliation remain open. The most useful next integration links admitted resource ceilings with measurement-conditioned action exclusions.

`MANIFEST.sha256.json` inventories this public distribution. Existing upstream authorship and license terms remain applicable to the rational kernel and base-register material; this release adds no new license grant. No credentials, board messages, machine paths, manuscript texts or dependency environments are included.
