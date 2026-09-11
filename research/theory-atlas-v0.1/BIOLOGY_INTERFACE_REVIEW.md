# Measurement-conditioned resource ceiling

This addendum reviews the biology lead's continuation handoff at the existing simulated minute-30 state. It is an independent arithmetic and premise review of that handoff, not a rerun of its ODE or empirical validation. The exact external input hashes are in `receipts/biology_interface_review.json`.

Let G and O denote GSH and GSSG concentrations in one fixed-volume compartment, N denote NADPH, and q=G/(G+2O). Write G_total=G+2O in GSH equivalents. From the reaction ledger, B=G/2+N satisfies Bdot=Jreg-Jp+Jg/2. Thus nonnegative state and absolutely continuous trajectories give

`integral_0^T Jp dt <= q(0)*G_total(0)/2 + N(0) + integral_0^T (Jreg+Jg/2) dt`.

Upper bounds on the nonnegative factors and fluxes give the valid, possibly loose rectangular interval bound

`U = q_upper*G_total_upper/2 + N_upper + T*(Vreg_upper+Jg_upper/2)`.

Correlations between interval coordinates can tighten this bound; they are not needed for its validity. The concentrations must use the same compartment and volume, and Jp is the GPx reaction extent per volume and time. General antioxidant removal cannot replace it. Full kinetic equations are unnecessary for this inequality once the ledger, nonnegativity and flux ceilings are established.

The reviewed preparation has q=0.999777356311612, G_total=1 mM GSH equivalents, and N=0.010153867792767448 mM. Over 20 minutes, Vreg<=0.003 mM/min and Jg=0 give:

| Observer information | Upper GPx extent, mM peroxide | Target 0.6 mM |
|---|---:|---|
| q alone, without absolute pool or rate caps | Unresolved | Unresolved |
| q and G_total, with 0<=N<=0.08 mM | 0.639888678155806 | Not excluded |
| Above plus exact simulated N | 0.570042545948573448 | Excluded |
| Illustrative bounded assay errors and rate uncertainty | 0.593153867792767449 | Excluded |
| Exact simulated N, regeneration ceiling removed | Unresolved | Unresolved by this bound |
| Exact simulated N, added GSH source 0.03 mM/min | 0.870042545948573448 | Not excluded |

All 24 observer/target rows were independently recomputed using exact fractions of the reported decimal inputs, including the premise-removal and source-addition cases. Their inquiry conclusions match. Exact decimal arithmetic removes arithmetic roundoff; it does not make the simulated state or assay intervals exact biological facts. The interval widths are illustrative, not confidence bounds. The trajectory, actual alternative-clearance extent and numerical convergence remain the biology lead's results and were not rerun here.

## Admission mapping and one integration obligation

The row-specific dependencies `BIO-STOICH`, `BIO-NONNEG`, `BIO-Q-BOUND`, `BIO-GTOTAL-BOUND`, `BIO-NADPH-BOUND`, `BIO-REGEN-BOUND` and `BIO-GSOURCE-BOUND` map to the atlas's resource ledger and admitted upper endpoints. Missing regeneration information removes this exclusion while leaving the algebraic ledger available under its remaining assumptions. The row's actual interval values must be bound along with the named premises.

The inspected inquiry declares fixed volumes in `BIO-ENV` but omits that ID from the per-result bound dependencies and the concentration moiety dependency. Bind a fixed-common-volume and complete-reaction-accounting premise to those conclusions, either with the existing ID or a narrower one. Otherwise an admission runner that consults only `depends_on` could retain a concentration bound after the volume assumption is withdrawn. This is a dependency correction; the printed fixed-volume calculation is sound. It has been sent to the biology lead and coordinator.

The claimed information gain is conditional: a smaller admissible set of initial states lowers a necessary upper bound. A destructive assay cannot simply be followed by a future trajectory of that same sampled unit. A physical protocol needs nondestructive measurement or a justified matched-unit inference, calibrated intervals, time accounting and disturbance. The result therefore supplies an integration and experiment-design example; it establishes no physiological rescue or new physical law.

## Reproduce the review

With standard-library Python, from a copied atlas directory:

```powershell
python -B check_biology_interface.py --biology-root '/path/to/biology-inquiry'
```

This reads the external biology JSON files and writes only the local review receipt. That package can change; compare the recorded input hashes before attributing this review to a newer release. The four frozen common inquiry packages remain independent of this optional external review.
