#!/usr/bin/env python3
"""Three-month postmortem — stage 5: candidate pass-bar options, priced retrospectively.

Computes, for each PROPOSED pass-bar option in the V2 spec, what February and April+May
would have said under it — so the owner chooses a standard knowing what it would have done
on every window read so far. Retrospective by construction; choosing a bar because of
these verdicts is the owner's explicit risk to take, and the spec says so.

No new window is read. All numbers come from the two sealed results and the stage-3
family-scope receipt.

Writes RECEIPTS/PM_PASS_BARS_V1.json.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import numpy as np

RECEIPTS = Path(__file__).resolve().parent
OA = RECEIPTS.parent

FEB = json.loads((OA / "FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json").read_text())
APRMAY = json.loads(
    (OA / "APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json").read_text()
)
SCOPE = json.loads((RECEIPTS / "PM_FAMILY_SCOPE_V1.json").read_text())

SEED = 20260811
N_BOOT = 20000


def day_series(result):
    """Per-day worst-case net of the main policy, all days (no-trade days count 0)."""
    out = []
    for day in sorted(result["days"]):
        portfolio = result["days"][day]["policies"]["market_top_abstain"]["portfolio"]
        out.append((day, float(portfolio.get("worst_case_net_r") or 0.0)))
    return out


def bootstrap_p05(values):
    rng = np.random.default_rng(SEED)
    arr = np.asarray(values, dtype=float)
    sums = rng.choice(arr, size=(N_BOOT, len(arr)), replace=True).sum(axis=1)
    return float(np.percentile(sums, 5)), float(np.percentile(sums, 50))


def max_drawdown(values):
    cum = np.cumsum(np.asarray(values, dtype=float))
    return float(np.max(np.maximum.accumulate(cum) - cum)) if len(cum) else 0.0


def window_stats(result):
    series = day_series(result)
    values = [v for _d, v in series]
    pooled = result["pooled"]["market_top_abstain"]
    mixed = result["pooled"]["mixed"]
    p05, p50 = bootstrap_p05(values)
    return {
        "n_days": len(values),
        "pooled_worst_case_net_r": pooled["worst_case_net_r"],
        "pooled_resolved": pooled["resolved"],
        "positive_active_days": pooled.get("positive_active_days"),
        "negative_active_days": pooled.get("negative_active_days"),
        "discipline_minus_mixed_worst_case_r": round(
            pooled["worst_case_net_r"] - mixed["worst_case_net_r"], 4
        ),
        "bootstrap_day_resample": {
            "n_boot": N_BOOT, "seed": SEED,
            "pooled_sum_p05": round(p05, 4), "pooled_sum_p50": round(p50, 4),
        },
        "max_drawdown_r_daily_worst_case": round(max_drawdown(values), 4),
        "worst_day_r": round(min(values), 4),
    }


def lsr_scope_stability():
    """The scoped claim is RULE-SELECTED liquidity_sweep_reclaim, not the family's raw
    population (which is heavily negative every month — see PM_FAMILY_SCOPE_V1.json).
    Months: January from the frozen-rule reproduction, February and April/May from the
    sealed results' per-month family nets."""
    jan = json.loads((RECEIPTS / "PM_JAN_FROZEN_RULE_V1.json").read_text())
    by_month = {
        "jan": jan["liquidity_sweep_reclaim_subset"]["net_r"],
        "feb": FEB["pooled"]["market_top_abstain"]["net_by_family"][
            "liquidity_sweep_reclaim"
        ],
        "april": APRMAY["per_month"]["april_2026"]["net_by_family"][
            "liquidity_sweep_reclaim"
        ],
        "may": APRMAY["per_month"]["may_2026"]["net_by_family"][
            "liquidity_sweep_reclaim"
        ],
    }
    population_by_month = {
        month: cell["dedup"]["net_r_sum"]
        for month, cell in sorted(
            SCOPE["families"].get("liquidity_sweep_reclaim", {}).items()
        )
    }
    return by_month, all(value > 0 for value in by_month.values()), population_by_month


def main() -> None:
    feb = window_stats(FEB)
    aprmay = window_stats(APRMAY)
    lsr_by_month, lsr_all_positive, lsr_population_by_month = lsr_scope_stability()

    fam = APRMAY["family_robustness"]
    feb_net_by_family = FEB["pooled"]["market_top_abstain"]["net_by_family"]
    feb_ex_top = round(
        FEB["pooled"]["market_top_abstain"]["worst_case_net_r"]
        - max(feb_net_by_family.values()),
        4,
    )

    def bar1(w):
        gates = {
            "resolved_ge_40": w["pooled_resolved"] >= 40,
            "pooled_worst_case_gt_0": w["pooled_worst_case_net_r"] > 0,
            "positive_gt_negative_active_days": (
                (w["positive_active_days"] or 0) > (w["negative_active_days"] or 0)
            ),
        }
        return gates, all(gates.values())

    def bar2(w):
        gates = {
            "bootstrap_p05_pooled_sum_gt_0": w["bootstrap_day_resample"]["pooled_sum_p05"] > 0,
            "discipline_beats_mixed_worst_case": w["discipline_minus_mixed_worst_case_r"] > 0,
            "max_drawdown_le_8r": w["max_drawdown_r_daily_worst_case"] <= 8.0,
            "resolved_ge_40": w["pooled_resolved"] >= 40,
        }
        return gates, all(gates.values())

    def bar3(w, window_lsr_positive):
        gates = {
            "discipline_beats_mixed_worst_case": w["discipline_minus_mixed_worst_case_r"] > 0,
            "pooled_worst_case_gt_minus_2r": w["pooled_worst_case_net_r"] > -2.0,
            "scoped_family_lsr_positive_in_window": window_lsr_positive,
            "scoped_family_rule_selected_lsr_positive_every_scored_month": lsr_all_positive,
        }
        return gates, all(gates.values())

    feb_lsr = feb_net_by_family.get("liquidity_sweep_reclaim", 0.0) > 0
    aprmay_lsr = (
        APRMAY["pooled"]["market_top_abstain"]["net_by_family"].get(
            "liquidity_sweep_reclaim", 0.0
        )
        > 0
    )

    options = {}
    for name, fn, feb_args, aprmay_args in (
        ("BAR_1_strict_positivity_status_quo", bar1, (feb,), (aprmay,)),
        ("BAR_2_bootstrap_ci_skill_drawdown", bar2, (feb,), (aprmay,)),
        ("BAR_3_relative_skill_scoped_family", bar3, (feb, feb_lsr), (aprmay, aprmay_lsr)),
    ):
        feb_gates, feb_pass = fn(*feb_args)
        am_gates, am_pass = fn(*aprmay_args)
        options[name] = {
            "february_retrospective": {"gates": feb_gates, "verdict": "PASS" if feb_pass else "REJECT"},
            "april_may_retrospective": {"gates": am_gates, "verdict": "PASS" if am_pass else "REJECT"},
        }

    receipt = {
        "schema": "gtos.wave21.postmortem.pass_bars.v1",
        "status": "RETROSPECTIVE_PRICING_OF_PROPOSED_BARS_NOT_A_PREREG",
        "window_stats": {"february": feb, "april_may": aprmay},
        "family_robustness_inputs": {
            "aprmay_sealed_family_robustness": fam,
            "feb_worst_case_excluding_top_family": feb_ex_top,
            "lsr_rule_selected_net_by_month": lsr_by_month,
            "lsr_rule_selected_positive_every_scored_month": lsr_all_positive,
            "lsr_population_dedup_net_by_month_for_contrast": lsr_population_by_month,
        },
        "options": options,
        "note": (
            "Bar definitions are proposals for the NEXT prereg (June/July 2026, "
            "unmaterialized). Their retrospective verdicts on already-read windows are "
            "shown so the owner can see what each standard would have said; they are not "
            "evidence the bars generalize."
        ),
    }
    (RECEIPTS / "PM_PASS_BARS_V1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"done": True, "options": {
        k: {
            "feb": v["february_retrospective"]["verdict"],
            "aprmay": v["april_may_retrospective"]["verdict"],
        } for k, v in options.items()
    }}, indent=1))


if __name__ == "__main__":
    main()
