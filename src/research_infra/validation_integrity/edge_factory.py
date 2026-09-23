"""Edge-factory pipeline (North-Star A1 / F-phase — the self-manufacturing engine).

Codifies the loop the orchestrator ran by hand across cycles 1-6 into ONE reusable, deterministic
certification engine: a candidate sleeve in -> a defensible INTEGRATE / MAP-CONDITIONAL / REJECT
decision out, with honest numbers. It chains the standing gates in the correct order:

  1. GENUINE EDGE   (dsr.probabilistic_sharpe_ratio vs 0  +  perm_null.block_permutation_test)
  2. REGIME-CLEAN   (regime_inflation.regime_inflation_diagnostic — not selection/regime-inflated)
  3. STANDALONE     (dsr.deflated_sharpe_ratio at the honest trial budget — informational; single new
                     sleeves are NOT expected to clear this, the diversifier gate is the operative test)
  4. DIVERSIFIER    (portfolio_contribution.certify_diversifier — does it raise the BOOK Sharpe with a
                     bootstrap delta-CI excluding 0, OOS-robust, low-corr, no risk regression)

Decision policy (the honest, build-quality rule the manual cycles followed):
  - INTEGRATE      : genuine_edge AND regime_clean AND diversifier == CERTIFIED_DIVERSIFIER.
  - MAP-CONDITIONAL: genuine_edge (real edge) but fails regime-clean or diversifier -> log as a
                     conditional/missed-opportunity with its upgrade path; do NOT add to the book.
  - REJECT         : not a genuine edge (PSR/perm fail) -> map as a dead-end, never silently drop.

This is the engine that lets the program PROVE replacement-rate > decay-rate: new INTEGRATE decisions
vs decay_monitor demote-candidates.

CRITICAL DISCIPLINE — the gates can be FOOLED by a leaky RETURN DEFINITION (cycle-14 lesson):
DSR/PBO/permutation/diversifier all test "is this return series real vs noise / does it raise the book".
They CANNOT detect that the return *generation* is tautological — a leaky R-definition (e.g. rolling-z
mean-reversion, where the trailing mean chases the series so "exit at z->0" wins on ANY pair) produces
genuinely-significant-looking returns that pass every gate. A cointegration sleeve scored INTEGRATE at
+88% book Sharpe and was pure artifact (random unrelated pairs scored identically).
=> ANY candidate whose R is NOT produced by the standard leak-free price/stop labeler
   (geometry_lib.simulate, R = price-move / stop-distance) MUST FIRST pass a NULL-MECHANISM PLACEBO
   control: re-run the SAME generator on randomized / unrelated inputs; the edge must VANISH. Only then
   is the factory verdict trustworthy. The standard directional sleeves (price/stop R) are not exposed to
   this class of artifact; the placebo guard is mandatory for new/non-standard mechanisms.

2nd CRITICAL DISCIPLINE — the gates (and even the placebo) miss CELL-SELECTION leakage (cycle-23 lesson):
DSR/PBO/perm/regime/diversifier AND the random-day placebo all test the RECONSTRUCTED RETURN SERIES. They
CANNOT detect that the CELLS/CONFIGS composing the sleeve were SELECTED on the same data the series spans.
A substrate index sleeve (41 cells selected on data through 2026) passed EVERY gate (PSR 1.0, perm 0.0002,
CERTIFIED_DIVERSIFIER +23% book Sharpe) and was pure selection artifact: walk-forward cell selection
(select cells on entry-years <=2021 ONLY, test on 2022-2026 never seen) showed the edge go NEGATIVE OOS
(in-sample +0.32 -> OOS -0.058).
=> ANY sleeve built by SELECTING cells/configs from a screened set (substrate cells, grid-mined configs,
   top-N anything) MUST FIRST pass a WALK-FORWARD-SELECTION control: re-run the selection on a PAST-only
   window and confirm the edge holds on a future window the selection never touched. A single
   pre-registered rule (no per-cell selection) is not exposed; the guard is mandatory for selection-derived
   sleeves. See CYCLE23_oos_remine.py for the reusable control.

3rd CRITICAL DISCIPLINE — a REGIME label is just another selection dimension (cycles 30→32 lesson):
after walk-forward CELL selection was hardened, the program tried discovering market REGIMES (k-means on
leak-free past-only features) and concentrating an edge into its in-sample-best regime. Cycle-30 reported
a metals "IC upgrade" (R2 train-best AND OOS-best, +0.772) — but cycle-32 swept 96 reasonable specs
(feature-subset × K × seed) and the in-sample-best regime beat the FULL sleeve OOS in only 54% (mean
improvement ≈ 0): a favorable DRAW, not a stable edge.
=> ANY sleeve built by SUB-SELECTING an edge into a data-discovered group (regime/cluster/threshold/
   top-N) MUST pass `selection_stability.subselection_stability`: concentrating to the in-sample-best
   group must BEAT the full population OOS across the LARGE MAJORITY of (feature, K, seed) specs (beat-rate
   >= 0.75, mean OOS delta > 0). A coin-flip beat-rate => deploy the FULL population, reject the sub-gate.

4th CRITICAL DISCIPLINE — INSTRUMENT-SUBSET selection (cycles 47-49 lesson): a CROSS-SECTIONAL / multi-
instrument edge can be real on a hand-picked instrument SUBSET yet INVERT when the comparable universe is
broadened (cycle-49: an FX volume-climax reversal was +0.25 OOS Sharpe on 14 crosses, −0.18 on the full
28 G10 crosses). The placebo / walk-forward-cell-selection / sub-selection-stability guards test the
return series / cells / regime — NONE tests the INSTRUMENT-SET selection. Also note (process discipline):
a Workflow/subagent "CONFIRMED_REAL" is a CANDIDATE FILTER, not certification — independently re-derive
every candidate; cycle-48 found a subagent-confirmed XS edge did not even reproduce from its spec.
=> ANY cross-sectional / multi-instrument edge MUST pass `selection_stability.universe_robustness`: the
   edge must hold on the FULL comparable universe AND on the majority of random subsets (not just the
   selected subset). Fails => instrument-set overfitting; do NOT deploy.
"""
from __future__ import annotations

from typing import Dict, Optional, Sequence

from . import dsr as _dsr
from . import perm_null as _perm
from . import regime_inflation as _regime
from . import portfolio_contribution as _pc
from . import selection_stability as _selstab  # noqa: F401  (3rd selection-leak guard; see docstring)


def certify_candidate(candidate_by_day: Dict[str, float], book_by_day: Dict[str, float], *,
                      n_trials: int, sealed_start: str, sr_variance: float,
                      weight: float = 0.35, perm_n: int = 3000, n_boot: int = 4000,
                      corr_ceiling: float = 0.35) -> Dict:
    """Run the full gate chain on one candidate sleeve and emit a decision."""
    days = sorted(candidate_by_day)
    ser = [candidate_by_day[d] for d in days]
    dated = [(d, candidate_by_day[d]) for d in days]
    if len(ser) < 30:
        return {"decision": "REJECT", "reason": "insufficient sample (n<30)", "n": len(ser)}

    # 1. genuine edge
    psr = _dsr.probabilistic_sharpe_ratio(ser, 0.0)["psr"]
    permp = _perm.block_permutation_test(ser, block=5, n_perm=perm_n, stat="sharpe")["p_value"]
    genuine = (psr > 0.95) and (permp < 0.05)

    # 2. regime-clean
    ri = _regime.regime_inflation_diagnostic(dated, sealed_start, n_trials, sr_variance=sr_variance)
    regime_clean = ri["contamination_flag"] is False

    # 3. standalone deflated Sharpe (informational)
    dsr_res = _dsr.deflated_sharpe_ratio(ser, n_trials, sr_variance=sr_variance)

    # 4. diversifier (the operative gate)
    div = _pc.certify_diversifier(book_by_day, candidate_by_day, standalone_edge_ok=genuine,
                                  regime_clean=regime_clean, sealed_start=sealed_start,
                                  weight=weight, corr_ceiling=corr_ceiling, n_boot=n_boot)

    if genuine and regime_clean and div["verdict"] == "CERTIFIED_DIVERSIFIER":
        decision, reason = "INTEGRATE", f"genuine + regime-clean + book Sharpe +{div['incremental']['delta_pct']:.1f}% (CI excludes 0)"
    elif genuine:
        fails = div["failed_checks"] if div["verdict"] != "CERTIFIED_DIVERSIFIER" else []
        rc = "" if regime_clean else "regime-contaminated; "
        decision, reason = "MAP-CONDITIONAL", f"genuine edge but {rc}diversifier failed: {fails}"
    else:
        decision, reason = "REJECT", f"not a genuine edge (PSR {psr:.3f}, perm p {permp:.4f})"

    return {
        "decision": decision, "reason": reason,
        "genuine_edge": {"pass": genuine, "psr": psr, "perm_p": permp},
        "regime_clean": {"pass": regime_clean, "fwd_all_ratio": ri["fwd_all_mean_ratio"],
                         "contamination_flag": ri["contamination_flag"]},
        "standalone_dsr": {"dsr": dsr_res["dsr"], "significant": dsr_res["significant"], "n_trials": n_trials},
        "diversifier": {"verdict": div["verdict"], "delta": div["incremental"]["delta"],
                        "delta_pct": div["incremental"]["delta_pct"],
                        "ci_low": div["bootstrap"]["ci_low"], "ci_high": div["bootstrap"]["ci_high"],
                        "ci_excludes_zero": div["bootstrap"]["significant"],
                        "corr_to_book": div["corr_to_book"], "sealed_delta": div["splits"]["sealed"]["delta"]},
        "recommended_weight": weight if decision == "INTEGRATE" else 0.0,
    }


def factory_run(candidates: Dict[str, Dict[str, float]], book_by_day: Dict[str, float], *,
                n_trials: int, sealed_start: str, sr_variance: float, **kw) -> Dict:
    """Run the gate chain over many candidates; summarize integrate/map/reject + replacement count."""
    results = {name: certify_candidate(c, book_by_day, n_trials=n_trials, sealed_start=sealed_start,
                                       sr_variance=sr_variance, **kw)
               for name, c in candidates.items()}
    by = {}
    for r in results.values():
        by[r["decision"]] = by.get(r["decision"], 0) + 1
    return {"results": results, "decision_counts": by,
            "n_integrate": by.get("INTEGRATE", 0), "n_map": by.get("MAP-CONDITIONAL", 0),
            "n_reject": by.get("REJECT", 0),
            "summary": f"{by.get('INTEGRATE',0)} integrate / {by.get('MAP-CONDITIONAL',0)} map / "
                       f"{by.get('REJECT',0)} reject of {len(results)} candidates"}
