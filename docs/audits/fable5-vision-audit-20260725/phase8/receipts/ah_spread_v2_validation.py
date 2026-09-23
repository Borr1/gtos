"""Session AH deliverable 2 -- assemble SPREAD_MODEL_V2_VALIDATION.json.

    python3 .../ah_spread_v2_validation.py

One artifact a reader can defend the composition repair from: the semantics finding, the
three axes, the declared selection protocol, the fitted exponent with its envelope, the
measured min-to-median bias that is NOT repaired here, and the list of verdicts the repair
moves. Assembled from the four receipts rather than recomputed, so it cannot disagree with
them; the only thing computed here is the min-to-median bias, which nothing else measures.
"""

from __future__ import annotations

import collections
import gzip
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from src.costs.spread_model import (  # noqa: E402
    DEFAULT_COMPOSITION,
    ERA_HOUR_EXPONENT,
    ERA_HOUR_EXPONENT_ENVELOPE,
    PREMIUM_FLOOR,
)

OUT = HERE / "SPREAD_MODEL_V2_VALIDATION.json"
SPREAD_MODEL = REPO / "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"


def min_to_p50_bias() -> dict:
    """The bias the composition repair does NOT fix, sized so the next session can.

    `era_ratio` is a ratio of bar MINIMA (this session's own semantics finding) while the
    anchor is a tick p50. Writing `M = P x k` for an era's min-to-median factor `k`:

        era_ratio_v1 = M_era / M_ref = (P_era / P_ref) x (k_era / k_ref)

    so the quantity the model wants, `P_era / P_ref`, is `era_ratio_v1 x (k_ref / k_era)`.
    `k_ref` is measurable from the reference window (both bar minima and tick p50 exist
    there). `k_era` is not measurable for any historical era -- but for a SCHEDULE-class era
    the recorded series is a CONSTANT, so its min IS its median and `k_era = 1` exactly.
    On those eras the era ratio is therefore inflated by `1 / k_ref`, and that is a number.
    """
    cells = json.loads((HERE / "AH_TICK_HOUR_CELLS.json").read_text())
    doc = json.loads(SPREAD_MODEL.read_text())
    tob = ((doc.get("tick_over_bar_factor") or {}).get("FTMO") or {})
    per_class = collections.defaultdict(list)
    rows = {}
    for sym, rec in cells["symbols"].items():
        by = rec.get("by_hour") or {}
        p50s = [v["p50"] for v in by.values() if v["n"] >= 200 and v["p50"] > 0]
        p5s = [v["p5"] for v in by.values() if v["n"] >= 200 and v["p5"] > 0]
        if len(p50s) < 12 or len(p5s) < 12:
            continue
        # p5 of the tick distribution is the closest observable proxy for "the minimum a
        # 15-minute bar would record" -- an exact per-bar min is in AH_BAR_SPREAD_SEMANTICS,
        # and this is the population-level version of the same ratio.
        k = statistics.median(p5s) / statistics.median(p50s)
        rows[sym] = {"k_ref_p5_over_p50": round(k, 4),
                     "inflation_on_a_constant_era": round(1.0 / k, 4) if k else None,
                     "instrument_class": rec.get("instrument_class")}
        if rec.get("instrument_class"):
            per_class[rec["instrument_class"]].append(k)
    return {
        "what": ("era_ratio is a ratio of bar MINIMA (AH_BAR_SPREAD_SEMANTICS.json) while the "
                 "anchor is a tick p50. Where an era's recorded series is a CONSTANT "
                 "(class SCHEDULE) its min is its median, so the ratio is inflated by "
                 "1 / k_ref, the reference window's own min-to-median factor."),
        "direction": "era_ratio_v1 OVERSTATES the median-level era ratio on constant eras",
        "not_repaired_here": ("it is a defect in the era TERM, not in the composition, and "
                             "repairing it means re-deriving SPREAD_MODEL_V1.json's era "
                             "table on a min-consistent anchor. Sized here so the next "
                             "session can price the decision."),
        "per_symbol": rows,
        "per_class_median_k_ref": {c: round(statistics.median(v), 4)
                                   for c, v in sorted(per_class.items())},
        "per_class_median_inflation": {c: round(1.0 / statistics.median(v), 4)
                                       for c, v in sorted(per_class.items())
                                       if statistics.median(v)},
        "ags_independent_measure": {
            "tick_over_bar_factor_by_class_median": tob.get("by_class_median"),
            "global_median": tob.get("global_median"),
            "note": ("AG measured the same quantity from the other direction (1.00x-1.73x) "
                     "and applies it ONLY to modelled anchors, never to the era ratio"),
        },
    }


def main() -> int:
    tests = json.loads((HERE / "AH_COMPOSITION_TESTS.json").read_text())
    sem = json.loads((HERE / "AH_BAR_SPREAD_SEMANTICS.json").read_text())
    moved = json.loads((HERE / "AH_VERDICTS_MOVED.json").read_text())
    entry = json.loads((HERE / "ENTRY_HOUR_FRONTIER_V1.json").read_text())

    fit = tests["fit"]
    out = {
        "schema": "gtos.spread_model_v2_validation.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AH",
        "repairs": "spread_model composition: v1_multiplicative -> v2_damped",
        "defect_repaired": {
            "filed_by": "Session AF §6 (ERA_MODEL_PRODUCT_UNVALIDATED)",
            "what": ("anchor x era_ratio x hour_of_week composed multiplicatively; each "
                     "factor validated ALONE and the product never validated at all"),
            "measured_size": ("198x-880x the modern base on pre-2010 FX; 1.78 R of spread "
                              "charged on NZDUSD in the 2000s, i.e. 178 % of the risk unit"),
            "afs_interim": ("restrict banded pricing to era_class == RECORDED, which DROPS "
                            "trades rather than pricing them. Retired by this repair."),
        },
        "composition": {
            "formula": "spread(sym, era, h) = anchor x era_ratio ** b x hour_mult(h)",
            "default": DEFAULT_COMPOSITION,
            "b": ERA_HOUR_EXPONENT,
            "b_envelope": list(ERA_HOUR_EXPONENT_ENVELOPE),
            "b_standard_error": fit.get("b_se_of_point"),
            "premium_floor": PREMIUM_FLOOR,
            "clamp": "effective hour multiplier >= 1.0",
            "b_equals_1_is_v1": True,
            "reproduces_reference_window_exactly": True,
            "v1_selectable": "pass composition='v1_multiplicative' or GateSpec.spread_composition",
        },
        "instrument_semantics": {
            "finding": "the MT5 bar `spread` column is the MINIMUM spread within the bar",
            "median_exact_match_rate": sem["median_exact_match_rate"],
            "n_symbols": len(sem["symbols"]),
            "timeframe": sem["timeframe"],
            "why_it_matters": ("a four-hour minimum cannot see a one-hour rollover spike, so "
                              "the bar column is structurally incapable of validating the "
                              "hour term at H4 -- which is why the product went unchecked. At "
                              "M15 it CAN, and that is axis C below."),
        },
        "selection_protocol": fit["protocol"],
        "axes": {
            "A_cross_broker": {
                "what": ("the same instrument at the same instant on two accounts whose "
                         "administered spread differs up to 22x. Both servers are "
                         "new_york_plus_7, so an hour cell means the same wall hour on both."),
                "result": tests["A_cross_broker"]["by_hour"].get("0"),
            },
            "B_cross_section": {
                "what": ("61 instruments spanning orders of magnitude of calm-hours spread, "
                         "leave-one-symbol-out per class over four candidate compositions"),
                "hour_00": tests["B_cross_section"]["by_hour"]["0"],
            },
            "C_era_axis": {
                "what": ("the actual axis, from M15 bar minima 2024Q1-2026Q3. Step 1 validates "
                         "the instrument against tick truth in the reference window; step 2 "
                         "fits b on within-symbol demeaned quarter points."),
                "instrument_check_corr": tests["C_era_axis"]["step1_instrument_check"][
                    "corr_bar_vs_tick_h00_mult"],
                "pooled": tests["C_era_axis"]["step2_era_slope"]["pooled_within_symbol"],
            },
        },
        "fit": fit,
        "corrections_to_this_sessions_own_first_run": [
            ("The cross-broker and era-axis regressions first returned b=+1.125 and +0.930, "
             "i.e. 'v1 is fine'. Both were dominated by crypto symbols whose hour-00 "
             "multiplier is exactly 1.00, so h_level == base by construction and the slope is "
             "forced to 1 regardless of which composition is true -- and BTCUSD carries a 22.4x "
             "level difference, so it set the slope by leverage alone. Restricted to cells "
             "where a rollover premium exists (MIN_EFFECT_MULT 1.5) the same regressions give "
             "+0.825 +- 0.935 and +0.669 +- 0.128. Same failure AG hit on the block pairs."),
            ("PREMIUM_FLOOR did not exist in the first implementation, which guarded only on "
             "mult_ref <= 1. Two of AG's tests went red and were right: a 1.14x metals session "
             "multiplier was being rescaled by an exponent fitted on a 10x-35x FX rollover, "
             "and because XAUUSD's 2022 era ratio is 0.178x it went UPWARD -- a repair that "
             "increased the charge on the one class AG had shown was already over-costed."),
            ("This session's brief asked for validation on AG's own held-out block pairs. "
             "Those cannot identify the composition: both sides of every pair are ALL-HOURS "
             "medians, so the hour term is identically 1 in both. Recorded because the brief "
             "is otherwise right -- the fix has to be selected on held-out data, and the three "
             "axes above are the holdouts that vary the interaction."),
        ],
        "verdicts_moved": {
            "population": moved["population"],
            "band": moved["band"],
            "declared_family_size": moved["declared_family_size"],
            "member": {k: v for k, v in moved["moved"]["member"].items() if k != "rows"},
            "family": {k: v for k, v in moved["moved"]["family"].items() if k != "rows"},
            "headline": (
                f"{moved['moved']['member']['n_improved']} of 246 member cells improve and "
                f"{moved['moved']['member']['n_worsened']} worsen; "
                f"{moved['moved']['family']['n_improved']} of 30 families improve and "
                f"{moved['moved']['family']['n_worsened']} worsen. Max member delta "
                f"{moved['moved']['member']['pooled_delta_max']:+.4f} R/day. "
                f"{moved['moved']['member']['n_verdict_changed']} verdicts change: the repair "
                f"moves MAGNITUDE and blocking REASON, not admissions."),
            "families_moved": {
                f: {"v1": r["pooled_v1"], "v2": r["pooled_v2"], "delta": r["pooled_delta"]}
                for f, r in moved["moved"]["family"]["rows"].items()
                if (r["pooled_delta"] or 0) != 0},
        },
        "compounded_with_the_entry_shift": {
            "what": ("item 1's H4 re-entry is the other half: the FX D1 cohort fills at broker "
                     "hour 00 by construction, and the composition repair changes what that "
                     "hour costs. Both are needed to read either."),
            "cost_decomposition_mean_r_per_trade": entry["cost_decomposition"],
            "family_pooled_at_mid": {
                arm: {f: entry["runs"][f"v2_damped|{arm}|family"]["rows"][f][
                    "pooled_oos_mean_r"] for f in
                    entry["runs"][f"v2_damped|{arm}|family"]["rows"]}
                for arm in ("A_d1close_d1exit", "C_h4next_h4exit")},
        },
        "min_to_p50_era_ratio_bias": min_to_p50_bias(),
        "honest_limits": [
            ("b is measured over level ranges of 2x-25x; the pre-2010 FX eras ask for 50x. It "
             "is an extrapolation. The reason to prefer it over v1 is not that it is validated "
             "there but that v1 is REFUTED wherever either can be tested, on the axis the "
             "model extrapolates along."),
            ("The fitted b is the conservative half of the evidence: the era axis alone gives "
             "0.669 and the affected class alone 0.310, and the point estimate sits between. "
             "Every affected verdict is published across the envelope."),
            ("Bands narrow the look-ahead; they do not eliminate it. Only capture does. That "
             "is AG's line and this repair does not soften it."),
            ("The min-to-median era-ratio bias above is measured and NOT repaired. It runs in "
             "the same direction as this repair (both reduce historical FX charges), so the "
             "numbers here are conservative with respect to it."),
        ],
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e3:.0f} KB)")
    print("b =", ERA_HOUR_EXPONENT, "envelope", ERA_HOUR_EXPONENT_ENVELOPE,
          "premium_floor", PREMIUM_FLOOR)
    print("min->p50 inflation on a constant era, per class:",
          out["min_to_p50_era_ratio_bias"]["per_class_median_inflation"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
