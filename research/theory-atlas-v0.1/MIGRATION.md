# Proposed register and adapter migration -0.1.0

The source is the coordinator's `integrated-inquiry-programme-rules` register, schema1.0.0. Its exact snapshot is `register.base.json`; its hash is stored in `register.proposed.json`. The proposal is schema1.1.0-proposed, with **32 rules and41 sources**. All original16 rule IDs and every original per-rule field/value are preserved. Added fields record typed inputs, domains, units, quantifiers, hypotheses, allowed/forbidden inference, counterexamples, source hashes/page markers, proof obligations and specific atlas certificates. Existing implementation/empirical status values were not upgraded by executing selected examples.

New IDs: COMP-03/04; RES-03/04; ADAPT-03; ACT-03; REC-02/03; IDA-01/02; TAO-01; GEOM-01; EVID-02; SIEVE-01; OBS-02; TIME-03. These are proposed additions in the existing namespace; the coordinator should check for concurrent allocations before import. Existing source aliases remain; remaining corpus keys supply new source IDs. Legacy entries are available for provenance without blanket admission of their claims.

The top-level register execution-policy statuses are preserved. Common inquiry packages use the agreed independent `result_kind` and `status` fields. In particular, `formal_under_premises/established_in_scope` is not an empirical-support label. Registration of a formal conditional is not a machine proof of that theorem. The `source_bindings` array supplements original citations without rewriting their established field meanings.

Each package's `execution.proof_obligations` provides stable IDs, a `PROOFS.md` section, the content hash and `supplied_argument` status. These are human arguments, not proof-assistant attestations. `ATLAS-PROOF-H-BIJECTION` replaces the first package's prose dependency string. Parent linkage for the deadline names the exact resource package and its `duration_exclusion` conclusion.

## Bounded admission adapter

`admission_adapter.assess(case, submitted, receipt, trusted, parent=None, source_root=None)` supports only these four fixtures. `trusted_contracts.json` must be selected from the reviewed bundle by the trusted runner. Required premises and expected statements come from that contract, not from submitted witness dependencies. The coordinator owns loading trusted artifacts, running certificate code, receipt authenticity, source selection and general dependency propagation.

The adapter distinguishes fixed-fixture mathematics from application to the submitted inquiry. It checks a fixture receipt fingerprint excluding the Python-version string, the expected scientific input fingerprint, source content/bindings, a premise-status whitelist, required premise statements, named supplied-proof content and the resource parent. A changed formula gets `out_of_scope`; missing necessary premises get `unresolved`; malformed premise records or a mismatched fixture receipt get `execution_error`. Independent fixture facts can remain valid. Submitted arbitrary expressions are never executed by this adapter.

The parent admission must be produced by the same trusted runner from the expected resource package; arbitrary external JSON claiming a successful parent is not an authenticated proof. Trusted contracts, code and expected hashes remain part of the trusted base. The adapter does not prove dependency completeness, physical mechanism adequacy or source truth.

Eight negative admission fixtures are executed in `run_admission.py`. A separate eight witness-mutation suite includes the coordinator's erased-dependency reproduction. Do not conflate the original scripts' authored contrast labels, exact countermodel calculations and the adapter's actual submission-admission tests.

## Small capabilities still missing from the shared engine

| Capability | Minimal useful example | Boundary |
|---|---|---|
| Trusted premise/source/parent propagation | Missing RES-03.P2 blocks duration and its diagnostic descendant while balance remains available | Already coordinator-owned; import domain requirements rather than making the witness choose them |
| Finite set and action-table solver | `{a,b},{b,c},{a,c}` needs2 cells despite pairwise intersections | Scope to finite complete library; estimated success tables need a separate statistical adapter |
| Linear stoichiometric certificate | Verify coefficient vector(.5,0,1,0) times the reaction matrix | Integral trajectory and kinetic adequacy remain separate obligations |
| Analytic theorem/inequality ledger | Scalar comparison a<=min(1,t/tau) and fundamental theorem of calculus | A checked polynomial identity must not impersonate an ODE or integration theorem |
| Ordered matrix/jet adapter | NoncommutingA/B maps preserve cross ratio; phase-sensitive quantum operations | Do not discard complex phase or infer a matrix theorem from a scalar rational core |
| Empirical admission with unit-aware uncertainty | Simultaneous future-law bounds or a diagnostic likelihood | Biology/quantum leads own observation model, sampling unit and calibration; schema validity is insufficient |

These are genuine gaps relative to the inspected scalar rational engine; a later coordinator release may already address some. The atlas does not modify the engine, shared register, Site or another task's files.
