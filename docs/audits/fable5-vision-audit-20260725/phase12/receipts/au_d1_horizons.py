"""Session AU — the D1 cohort's time-stop horizon, gated at the ratified rule.

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/au_d1_horizons.py
    ... --no-ledger

WHY THIS RUNS AT ALL

AQ repaired the `mx_*` D1 cohort's `time_stop_bars` from 96 (the M15-per-D1 conversion RATIO) to 7680
(the 80-D1-bar research horizon) and then measured something the repair does not settle: **on five of
the ten generating sleeves the accidental one-bar stop was BETTER than the research horizon**, and
both ATR-mean-reversion sleeves flip from strongly negative to positive under it. AQ's own conclusion:
*"for those five the follow-up is to declare a short horizon DELIBERATELY on the evidence rather than
inherit one from a bug. That is an exit-frontier decision, and it is routed as one."*

AD's frontier already contains a `time_stop_1` cell per D1 sleeve, and AQ recorded why reading it is
not an answer: it is at the **flat** band, on **ALL_ERAS**, at the historical 69-look family, and on
`mx_btcusd` the flat/all-eras delta reads +0.1405 R/day against the ratified rule's **+0.2722** -- a
1.9x difference. So the grid is re-gated here at `RECORDED`, `B_balanced` alpha 0.10, with the band
column alongside a flat CONTROL.

THE CUT RULE, DECLARED BEFORE ANY GATE RAN (agreement §1: declare the cut rule, not just the axis)

`HORIZON_GRID` below is a FIXED geometric ladder in the sleeve's OWN bars -- 1, 2, 3, 5, 10, 20, 40,
80 -- chosen for two reasons that are not outcomes: 1 is the accidental stop the cohort actually ran,
80 is the research horizon and `maxbars`, and the rest are a log-spaced ladder between them. There is
no median split, no threshold fitted to a result, and no per-sleeve grid. `AU_MEASURED_BEST` is
reported for every sleeve whether or not it is better than 80, so the ladder cannot be read as a
search that only reports its winners.

AND THE SEARCH IS PRICED. Picking the best of 8 horizons per sleeve is a search even when every cell
is an exit-cell re-measurement that BH charges nothing for (AI §0). So every sleeve's row carries
`p_min_over_grid` next to `expected_min_p_under_global_null` = 1-(1-p)^k for k=8 -- AR's own standard,
applied prospectively instead of in a correction. A `p_min` that the global null would return most of
the time is not evidence, and the row says so on its face.

MULTIPLICITY. No new looks (AI §0). Every arm ledgered including NOT_EVALUABLE (B1267).
BOUNDARY. Offline and pure. No broker module, no order, no VPS.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

import au_live_contract as LC  # noqa: E402

AD = LC.AD

from src.components.ultimate_book.execution_packets import (  # noqa: E402
    MARKET_EXPANSION_TARGET2_SLEEVES,
    SLEEVE_EXIT_PROFILES,
)
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as POP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AM_SUBMID = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts/AM_SUBMID_TRADES.json.gz"
FAMILY_V5 = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/CANDIDATE_FAMILY_V5.json"
OUT = HERE / "AU_D1_HORIZONS_V1.json"

ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
BANDS = (None, "low", "mid", "high")
POPULATION = "RECORDED"
OPTION = "B_balanced"
SUBMID = "sub_mid_dn_revert"

#: DECLARED CUT RULE — a fixed geometric ladder in the sleeve's own D1 bars. 1 is the accidental
#: stop the cohort ran until 2026-07-30; 80 is the research horizon and `maxbars`, so the 80 cell is
#: R-identical to no time stop at all (AQ's C1 control, 2,086/2,086 trades). Nothing here is fitted.
HORIZON_GRID: tuple[int, ...] = (1, 2, 3, 5, 10, 20, 40, 80)
#: The five AQ measured as better under the accidental stop, named here so the artifact can say
#: whether the grid AGREES with that reading rather than inheriting it.
AQ_FAVOURED_SHORT = ("mx_us100_cash_d1_atr_mean_reversion", "mx_us500_cash_d1_atr_mean_reversion",
                     "mx_ger40_cash_d1_volume_surge_reversal",
                     "mx_us30_cash_d1_volume_surge_reversal",
                     "mx_nzdjpy_d1_donchian_20_breakout")
#: `vol_compression` is a D1 sleeve whose 80-bar horizon was declared CORRECTLY all along. It rides
#: the same grid as a control: if the ladder says a one-bar stop is better for it too, the ladder is
#: measuring something about the harness rather than about the mis-scaled cohort.
CONTROL_SLEEVE = "vol_compression"


def build_substrate() -> dict:
    t0 = time.time()
    raw = json.load(gzip.open(AA_IN, "rt"))
    base = {s: list(r) for s, r in raw["trades"].items() if r}
    subm = json.load(gzip.open(AM_SUBMID, "rt"))
    base[SUBMID] = subm["trades"]["server_repaired"]
    series, index, _ = AD.load_bars()
    cohort = tuple(s for s in MARKET_EXPANSION_TARGET2_SLEEVES if s in base) + (CONTROL_SLEEVE,)
    print(f"substrate in {time.time() - t0:.0f}s: {len(base)} sleeves, cohort {len(cohort)}",
          flush=True)
    return {"base": base, "costs": AD.load_broker_true_costs(AD.COSTS),
            "rule": AD.resolve_rule(SERVER), "series": series, "index": index,
            "allowlist": AD.allowlist(), "family": CF.load_candidate_family(FAMILY_V5),
            "cohort": cohort}


def relabel(sub: dict, h: int) -> tuple[dict, dict]:
    """Every cohort sleeve at a time stop of `h` OWN bars; every other sleeve as walked."""
    out = {s: list(r) for s, r in sub["base"].items()}
    tel = {}
    v = AD.Variant(name=f"ts{h}", family="time_stop", time_stop_bars=(None if h >= LC.MAXBARS else h),
                   target_mode="native",
                   note=(f"time stop at {h} own D1 bars"
                         + (" == maxbars, i.e. NO time stop" if h >= LC.MAXBARS else "")))
    for s in sub["cohort"]:
        rows, t = AD.resimulate(sub["base"][s], v, sub["series"], sub["index"], sub["costs"],
                                ACCOUNT, sub["rule"])
        out[s] = rows
        tel[s] = {"variant": v.as_dict(), **LC.maxbars_share(t)}
    return out, tel


def row_of(sv, res, spec, *, band, h, seconds, mix, tel) -> dict:
    fam = (res.family or {}).get("multiplicity", {}) or {}
    base = {"horizon_own_bars": h, "population": POPULATION,
            "band": band if band is not None else "flat_37_day_snapshot",
            "band_is_control": band is None,
            "declared_family_size": spec.declared_family_size,
            "effective_family_size": fam.get("effective_family_size"),
            "spec_sha256": spec.seal(), "population_mix": mix, "seconds": round(seconds, 2),
            "maxbars_share": tel.get("maxbars_share"),
            "time_stop_share": tel.get("time_stop_share"),
            "horizon_share": tel.get("horizon_share"),
            "exit_reasons": tel.get("exit_reasons")}
    if sv is None:
        return {**base, "verdict": "ABSENT"}
    st = sv.gates.get("stability", {})
    t = sv.telemetry or {}
    ri = t.get("regime_inflation") or {}
    ins = t.get("in_sample") or {}
    fl = t.get("p_floor") or {}
    hold = (sv.diagnostics or {}).get("holding") or {}
    return {**base,
            "verdict": sv.verdict.value, "n_trades": sv.n_trades,
            "pooled_oos_mean_r": sv.pooled_oos_mean_r,
            "p_raw": sv.p_raw, "q_value": sv.q_value,
            "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                               "robustness", "significance")
                                   if not sv.gates.get(g, {}).get("pass")],
            "fold_means": st.get("fold_means"),
            "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
            "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
            "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
            "p_floor": fl.get("p_floor"), "n_blocks": fl.get("n_blocks"),
            "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                                 if (sv.p_raw is not None and fl.get("p_floor")) else None),
            "regime_inflation_contaminated": ri.get("contamination_flag"),
            "recommended_magnitude_haircut": ri.get("recommended_magnitude_haircut"),
            "haircut_at_floor": ri.get("haircut_at_floor"),
            "haircut_binding_term": ri.get("haircut_binding_term"),
            "in_sample_mean_is_r": ins.get("mean_is_r"),
            "in_sample_mean_oos_r": ins.get("mean_oos_r"),
            "in_sample_sign_inversion": (
                None if (ins.get("mean_is_r") is None or ins.get("mean_oos_r") is None)
                else bool(float(ins["mean_is_r"]) < 0 <= float(ins["mean_oos_r"]))),
            "median_hold_hours": hold.get("median_hours"),
            "reasons": list(sv.reasons)}


def run_grid(sub: dict, ledger: TrialLedger | None) -> dict:
    arms: dict[str, dict] = {}
    for h in HORIZON_GRID:
        labelled, tel = relabel(sub, h)
        for band in BANDS:
            t0 = time.time()
            o = OPTIONS[OPTION]
            spec = o.with_(spec_id=f"{o.spec_id}_au_d1h_{h}",
                           sleeve_symbol_allowlist=sub["allowlist"], spread_band=band)
            spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=sub["family"])
            recs0 = {s: AD.to_records(r) for s, r in labelled.items()}
            recs, spec, mix = POP.apply(POPULATION, recs0, spec, account=ACCOUNT,
                                        band=(band or "mid"))
            res = run_gate(recs, spec, costs=sub["costs"], server=SERVER, diagnose=True)
            wo = (res.family or {}).get("wipeout") or {}
            if wo.get("wiped_out"):
                raise RuntimeError(f"gate wipeout at h={h}/{band}: {wo}. Refusing to publish.")
            el = time.time() - t0
            key = f"{h}|{band or 'flat'}"
            arms[key] = {}
            for s in sub["cohort"]:
                sv = res.verdicts.get(s)
                arms[key][s] = row_of(sv, res, spec, band=band, h=h, seconds=el, mix=mix,
                                      tel=tel.get(s, {}))
                if ledger is not None and sv is not None:
                    ledger.record(
                        mechanism="d1_horizon_grid", sleeve=s,
                        variant={"horizon_own_bars": h, "population": POPULATION,
                                 "band": arms[key][s]["band"], "option": OPTION},
                        window="full_archive", spec_sha256=spec.seal(),
                        outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                 "NOT_EVALUABLE": "not_evaluable"}.get(sv.verdict.value,
                                                                       "evaluated"),
                        metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                        note=f"AU D1 horizon grid, h={h} own bars @ {arms[key][s]['band']}")
            shown = []
            for s in sub["cohort"][:4]:
                v = arms[key][s].get("pooled_oos_mean_r")
                short = s.split("_")[1]
                shown.append(f"{short}:{v:+.3f}" if isinstance(v, (int, float))
                             else f"{short}:—")
            print(f"  h={h:3d} band={str(band):5s} " + " ".join(shown), flush=True)
    return arms


def summarise(sub: dict, arms: dict) -> dict:
    """Per sleeve: the whole ladder at mid, the declared best, and the search's own price."""
    out = {}
    k = len(HORIZON_GRID)
    for s in sub["cohort"]:
        ladder = {}
        for h in HORIZON_GRID:
            r = arms[f"{h}|mid"][s]
            ladder[h] = {"r_per_day": r.get("pooled_oos_mean_r"), "p_raw": r.get("p_raw"),
                         "verdict": r.get("verdict"), "n": r.get("n_trades"),
                         "folds": r.get("fold_means"),
                         "folds_positive": r.get("oos_positive_fold_frac"),
                         "median_hold_hours": r.get("median_hold_hours"),
                         "horizon_share": r.get("horizon_share"),
                         "failing": r.get("failing_core_gates")}
        rated = [(v["r_per_day"], h) for h, v in ladder.items()
                 if isinstance(v["r_per_day"], (int, float))]
        ps = [v["p_raw"] for v in ladder.values() if isinstance(v["p_raw"], (int, float))]
        best_h = max(rated)[1] if rated else None
        res_h = LC.MAXBARS
        rec = {
            "evaluable": bool(rated),
            "aq_favoured_short": s in AQ_FAVOURED_SHORT,
            "is_control_sleeve": s == CONTROL_SLEEVE,
            "declared_time_stop_m15": SLEEVE_EXIT_PROFILES.get(s, {}).get("time_stop_bars"),
            "ladder_at_mid": ladder,
            "best_horizon_own_bars": best_h,
            "research_horizon_own_bars": res_h,
            "best_beats_research_horizon": (
                None if best_h is None else
                (ladder[best_h]["r_per_day"] - ladder[res_h]["r_per_day"])
                if isinstance(ladder[res_h]["r_per_day"], (int, float)) else None),
            "best_is_the_accidental_one_bar_stop": (best_h == 1),
            # the search's own price, stated on the row rather than in a footnote
            "p_min_over_grid": (min(ps) if ps else None),
            "k_cells_searched": k,
            "expected_min_p_under_global_null": (
                None if not ps else round(1.0 - (1.0 - min(ps)) ** k, 6)),
            "band_envelope_at_best": (
                None if best_h is None else
                {(b or "flat"): arms[f"{best_h}|{b or 'flat'}"][s].get("pooled_oos_mean_r")
                 for b in BANDS}),
            "verdict_envelope_at_best": (
                None if best_h is None else
                {(b or "flat"): arms[f"{best_h}|{b or 'flat'}"][s].get("verdict")
                 for b in BANDS}),
        }
        out[s] = rec
    return out


def prescriptions(summary: dict) -> dict:
    """A declared short-horizon contract per sleeve that wants one — and the honest refusals.

    A sleeve gets a PRESCRIPTION only when all four hold, declared before the numbers were read:
      1. its best ladder cell is SHORTER than the 80-bar research horizon;
      2. the improvement over the research horizon is positive at EVERY cost band;
      3. the best cell's R/day is positive (a less-negative loss is not a contract to declare);
      4. the best cell's chronological folds are majority-positive.
    Anything else is reported as MEASURED_BUT_NOT_PRESCRIBED with the clause that failed, because a
    grid's argmax is not a recommendation.
    """
    out = {}
    for s, r in summary.items():
        if not r["evaluable"]:
            out[s] = {"prescription": "NOT_EVALUABLE", "why": "no gated cell on RECORDED"}
            continue
        bh = r["best_horizon_own_bars"]
        cell = r["ladder_at_mid"][bh]
        env = r["band_envelope_at_best"] or {}
        res_at = {b: r["ladder_at_mid"][LC.MAXBARS]["r_per_day"] for b in env}
        fails = []
        if bh >= LC.MAXBARS:
            fails.append("best cell IS the research horizon; no short horizon is indicated")
        better_all = all(isinstance(env.get(b), (int, float))
                         and isinstance(res_at.get(b), (int, float))
                         and env[b] > res_at[b] for b in env)
        if bh < LC.MAXBARS and not better_all:
            fails.append("the improvement does not hold at every cost band")
        if not (isinstance(cell["r_per_day"], (int, float)) and cell["r_per_day"] > 0):
            fails.append(f"the best cell is not positive ({cell['r_per_day']})")
        fp = cell.get("folds_positive")
        if not (isinstance(fp, (int, float)) and fp > 0.5):
            fails.append(f"chronological folds are not majority positive ({fp})")
        out[s] = {
            "prescription": ("DECLARE_SHORT_HORIZON" if not fails else
                             ("KEEP_THE_RESEARCH_HORIZON" if bh >= LC.MAXBARS
                              else "MEASURED_BUT_NOT_PRESCRIBED")),
            "horizon_own_bars": bh,
            "horizon_m15_expression": (f"time_stop_m15({bh}, \"D1\")" if bh < LC.MAXBARS
                                       else "time_stop_m15(80, \"D1\")  # unchanged"),
            "r_per_day_at_mid": cell["r_per_day"],
            "delta_vs_research_horizon": r["best_beats_research_horizon"],
            "verdict_at_mid": cell["verdict"],
            "folds": cell["folds"], "folds_positive": fp,
            "median_hold_hours": cell["median_hold_hours"],
            "horizon_share": cell["horizon_share"],
            "p_min_over_grid": r["p_min_over_grid"],
            "expected_min_p_under_global_null": r["expected_min_p_under_global_null"],
            "clauses_failed": fails,
            "agrees_with_aq_reading": (r["aq_favoured_short"] == (bh < LC.MAXBARS)),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ledger", action="store_true")
    a = ap.parse_args()
    sub = build_substrate()
    ledger = None if a.no_ledger else TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AU")
    arms = run_grid(sub, ledger)
    summary = summarise(sub, arms)
    doc = {
        "schema": "gtos.au.d1_horizons.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/"
                        "au_d1_horizons.py",
        "session": "AU", "blocks": "B1550-B1599",
        "what": ("the D1 cohort's time-stop horizon re-gated at the RATIFIED rule, so the five "
                 "sleeves AQ measured as better under the accidental one-bar stop get a horizon "
                 "declared on the evidence instead of inherited from a bug"),
        "declared_cut_rule": {
            "grid_own_bars": list(HORIZON_GRID),
            "why_these": ("1 is the accidental stop the cohort ran until 2026-07-30; 80 is the "
                          "research horizon and `maxbars`, so the 80 cell is R-identical to no "
                          "time stop; the rest are a log-spaced ladder between them. Fixed set, "
                          "no median split, no per-sleeve grid, nothing fitted to an outcome."),
            "declared_before_gating": True,
            "search_priced": ("every sleeve row carries p_min_over_grid beside "
                              "1-(1-p)^8, so a p the global null returns most of the time "
                              "cannot read as evidence"),
        },
        "gate": {"population": POPULATION, "option": OPTION,
                 "declared_family": "CANDIDATE_BOOK_V1 @ CANDIDATE_FAMILY_V5.json",
                 "bands": ["flat_37_day_snapshot (CONTROL)", "low", "mid", "high"],
                 "multiplicity_note": "no new looks; exit-cell re-measurements (AI §0)"},
        "cohort": list(sub["cohort"]),
        "control_sleeve": CONTROL_SLEEVE,
        "aq_favoured_short": list(AQ_FAVOURED_SHORT),
        "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "arms": arms,
        "summary": summary,
        "prescriptions": prescriptions(summary),
    }
    OUT.write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
