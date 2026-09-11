"""Independent arithmetic review of the biology lead's continuation receipt.

Reads a supplied biology package, never runs or writes its model. This is an
interface review, not a fifth common-engine adapter or a trajectory replication.
"""
from pathlib import Path
from fractions import Fraction as F
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--biology-root", required=True)
    args = parser.parse_args()
    bio = Path(args.biology_root).resolve()
    paths = [bio / "results/continuation.json", bio / "continuation_inquiry.json"]
    data, inquiry = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    cases = data["observer_intervals"]
    rows = []
    for row in data["table"]:
        intervals = cases[row["observer"]]
        names = ["q", "G_total", "N", "Vreg", "Jg"]
        if any(intervals[k] is None for k in names):
            exact = None
            conclusion = "unresolved"
        else:
            bounds = []
            for k in names:
                lo, hi = map(lambda x: F(str(x)), intervals[k])
                assert 0 <= lo <= hi
                bounds.append(hi)
            q, total, n, regen, g_source = bounds
            assert q <= 1
            duration = F(str(row["horizon_min"]))
            assert duration >= 0
            # Integrate Jp = Jreg + Jg/2 - Bdot and discard B(T)>=0.
            exact = q * total / 2 + n + duration * (regen + g_source / 2)
            conclusion = "excluded" if F(str(row["target_gpx_clearance_mM"])) > exact else "not_excluded"
        assert row["upper_bound_exact"] == (str(exact) if exact is not None else None)
        assert row["budget_conclusion"] == conclusion
        rows.append({"observer": row["observer"], "target_mM": row["target_gpx_clearance_mM"],
                     "upper_bound_exact": str(exact) if exact is not None else None,
                     "conclusion": conclusion})
    indexed = {(r["observer"], str(r["target_mM"])): r for r in rows}
    assert indexed["fraction_plus_absolute_pool", "0.6"]["conclusion"] == "not_excluded"
    assert indexed["fraction_pool_and_cofactor", "0.6"]["conclusion"] == "excluded"
    assert indexed["cofactor_without_regeneration_ceiling", "0.6"]["conclusion"] == "unresolved"
    assert indexed["cofactor_with_added_gsh_source", "0.6"]["conclusion"] == "not_excluded"
    bound_results = [r for r in inquiry["results"] if r["id"] != "BIO-CONT-MOIETY"]
    assert len(rows) == len(bound_results) == 24
    assert all(r["value"]["budget_conclusion"] == indexed[r["value"]["observer"], str(r["value"]["target_gpx_clearance_mM"])]["conclusion"] for r in bound_results)
    findings = []
    if any("BIO-ENV" not in r["depends_on"] for r in bound_results):
        findings.append({"id": "BIO-REVIEW-FIXED-VOLUME", "status": "integration_obligation",
                         "detail": "The result uses concentrations. Bind fixed common volume and complete reaction accounting to each bound; BIO-ENV is declared but absent from these result dependency lists. The same requirement applies to the concentration moiety claim. A dedicated narrower premise is also valid."})
    result = {"review_version": "0.1.0", "status": "arithmetic_passed",
              "rows_recomputed": len(rows), "cases": rows, "findings": findings,
              "input_sha256": {str(p): sha(p) for p in paths},
              "review_code_sha256": sha(Path(__file__)),
              "scope": "Exact rational recomputation of reported decimal inputs. Does not rerun the ODE, validate empirical calibration, authenticate sources, or establish successful clearance. Missing bound means unresolved only by this inequality."}
    (ROOT / "receipts/biology_interface_review.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"biology_interface": result["status"], "rows": len(rows), "integration_findings": len(findings)}))


if __name__ == "__main__":
    main()
