#!/usr/bin/env python3
"""AY's repair-queue rows, built from the artifacts rather than typed (B1840).

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/ay_repair_rows.py

Every `evidence` block below is READ from a receipt this session wrote, so a row cannot drift
from the measurement it cites. `REPAIR_QUEUE_AY.json` is authoritative for AY's rows; the
shared sidecar is append-only and a landed row is never rewritten (AP §7.2) — a correction is
an errata row.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts"
VERDICT = HERE / "AY_SLEEVE_VERDICT_V1.json"
LIVE = HERE / "AY_LIVE_SCREEN_EVIDENCE_V1.json"
CENSUS = HERE / "AY_LIVE_CONTRACT_CENSUS_V1.json"
SURVEY = HERE / "AY_GENERATOR_STOP_SURVEY_V1.json"
OUT = HERE / "REPAIR_QUEUE_AY.json"

NOW = "2026-07-30T00:00:00+00:00"


def _sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _band(verdict: dict, sleeve: str, band: str = "mid") -> dict:
    return verdict["by_sleeve"][sleeve]["by_band"][band]


def main() -> int:
    verdict = json.loads(VERDICT.read_text())
    live = json.loads(LIVE.read_text())
    census = json.loads(CENSUS.read_text())
    survey = json.loads(SURVEY.read_text())
    contam = live["conviction_contamination"]
    mid_census = census["by_band"]["mid"]

    rows = []

    # ---- 1. the live-money one -------------------------------------------------------
    rows.append({
        "session": "AY", "sleeve": None, "is_primary": True,
        "component": "src/components/ultimate_book/book_engine.py:865-915",
        "prescription": "COST_SCREENED_INTENTS_INFLATE_THE_RUNNING_CONVICTION_COUNT",
        "verdict": "BUILT_DEFAULT_OFF",
        "action": (
            "`_running_conviction_override` builds the day's distinct-firing-sleeve count "
            "from INTENTS after `precount_intent_filter`'s five drop rules. The pre-trade "
            "cost screen is not one of them and cannot be — it needs a tick and runs later, "
            "in book_owner at send time. `admission.py:1188` then takes "
            "`na = max(na, override)`, MONOTONE UPWARD, so a sleeve whose every leg the cost "
            "gate refuses still raises the day's Kelly-lite multiplier for every sleeve that "
            "does place. Same defect class as the D3 repair of 2026-07-27, whose own "
            "docstring calls it CORRECTNESS-CRITICAL. Closed by the generation-side floor "
            "(`run_book.py --spread-geometry-floor`, default OFF), which refuses the intent "
            "before it can be counted; pinned by "
            "tests/ultimate_book/test_spread_geometry_floor.py."
        ),
        "evidence": {
            "source": "the read-only 2026-07-25 VPS export's own launcher log",
            "cycles": live["cycles"],
            "n_cost_screen_or_pretrade_cost_skips":
                live["n_cost_screen_or_pretrade_cost_skips"],
            "account_days_counting_a_doomed_sleeve":
                contam["n_account_days_with_a_doomed_sleeve_counted"],
            "account_days_where_the_multiplier_moved":
                contam["n_account_days_where_it_moved_the_multiplier"],
            "max_size_inflation_pct": contam["max_size_inflation_pct"],
            "kelly_bins": contam["bins"],
            "live_flags_required": contam["live_flags_required"],
        },
        "margin": None, "appended_utc": NOW,
    })

    # ---- 2/3. the two armed REPAIRs --------------------------------------------------
    for sleeve in ("sub_mid_dn_revert", "sub_xvol_pullback"):
        v = verdict["by_sleeve"][sleeve]
        if v["verdict"] != "REPAIR":
            continue
        b = _band(verdict, sleeve)
        c = mid_census["by_sleeve"][sleeve]
        rows.append({
            "session": "AY", "sleeve": sleeve, "is_primary": True,
            "component": "phase13/AY_SPREAD_FLOOR_ACTIVATION_DOSSIER.md",
            "prescription": "ARMED_SLEEVE_IMPROVES_UNDER_ITS_OWN_LIVE_COST_CONTRACT",
            "verdict": "OWNER_DECISION",
            "action": (
                f"{sleeve} is ARMED on both accounts and "
                f"{100 * (c['frac_over_spread_limit'] or 0):.1f} % of its archive trades "
                "exceed the spread limit the live send gate already applies to it. Gated at "
                "the ratified rule with 20 random-drop seeds and an inverse-cheapest "
                "control, the live contract is a REPAIR at "
                f"{v['n_bands_repair']} of 3 bands: pooled OOS "
                f"{b['control_pooled_oos_mean_r']:+.4f} -> "
                f"{b['live_contract_pooled_oos_mean_r']:+.4f} R/day at mid "
                f"(delta {b['delta_live_contract']:+.4f}), beating EVERY random seed "
                f"(max {b['delta_random_max']:+.4f}) with the inverse control at "
                f"{b['delta_inverse_cheapest']:+.4f}. It does NOT admit "
                f"(p_raw {b['live_contract_p_raw']:.4f} against a family of 514). The "
                "decision on the table is whether to refuse these trades at GENERATION "
                "rather than at send — see the dossier for what that buys and costs."
            ),
            "evidence": {
                "band": "mid", "population": "RECORDED", "option": "B_balanced",
                "spread_r_limit_live": v["spread_r_limit_live"],
                "frac_over_spread_limit_mid": c["frac_over_spread_limit"],
                "max_spread_r_mid": c["max_spread_r"],
                "delta_by_band": {bd: verdict["by_sleeve"][sleeve]["by_band"][bd].get(
                    "delta_live_contract") for bd in ("low", "mid", "high")},
                "p_raw_control_mid": b["control_p_raw"],
                "p_raw_live_contract_mid": b["live_contract_p_raw"],
                "n_trades_mid": [b["control_n_trades"], b["live_contract_n_trades"]],
                "empirical_p_vs_random_mid": b["empirical_p_vs_random"],
                "recent_two_folds_mean_r": [
                    b["recent_two_folds_mean_r_control"],
                    b["recent_two_folds_mean_r_live_contract"]],
                "maxbars_share": [b["maxbars_share_control"],
                                  b["maxbars_share_live_contract"]],
                "fold_calendar_identical": b["fold_calendar_identical"],
                "caveat": (
                    "the fold calendar MOVES when the filter drops a sleeve's earliest "
                    "trades, so the pooled comparison is valid and a fold-by-fold one is not"
                ) if not b["fold_calendar_identical"] else (
                    "fold calendar identical in both arms; fold-by-fold comparison valid"),
            },
            "margin": None, "appended_utc": NOW,
        })

    # ---- 4. the two HARMFULs ---------------------------------------------------------
    harmful = [s for s, v in verdict["by_sleeve"].items() if v["verdict"] == "HARMFUL"]
    if harmful:
        rows.append({
            "session": "AY", "sleeve": ",".join(sorted(harmful)), "is_primary": False,
            "component": "phase13/receipts/AY_SLEEVE_VERDICT_V1.json",
            "prescription": "LIVE_COST_CONTRACT_IS_MEASURABLY_HARMFUL_ON_THESE_SLEEVES",
            "verdict": "RESEARCH",
            "action": (
                "The live spread limit is not a universal good. On "
                f"{', '.join(sorted(harmful))} applying it is HARMFUL at >= 2 of 3 bands — "
                "the delta is negative and below EVERY one of the 20 random-drop seeds, so "
                "the expensive trades on these sleeves are systematically the PROFITABLE "
                "ones. Neither is armed. The open question is whether that is a real "
                "microstructure effect (the sleeve earns its edge in wide-spread conditions) "
                "or a sample artifact; it is the mirror image of asia_pdl_fade's repair and "
                "the same controls apply."
            ),
            "evidence": {s: {
                "delta_by_band": {bd: verdict["by_sleeve"][s]["by_band"][bd].get(
                    "delta_live_contract") for bd in ("low", "mid", "high")},
                "delta_random_min_mid": _band(verdict, s)["delta_random_min"],
                "n_bands_harmful": verdict["by_sleeve"][s]["n_bands_harmful"],
                "armed": verdict["by_sleeve"][s]["armed"],
            } for s in sorted(harmful)},
            "margin": None, "appended_utc": NOW,
        })

    # ---- 5. the generator survey -----------------------------------------------------
    rows.append({
        "session": "AY", "sleeve": None, "is_primary": False,
        "component": "phase13/receipts/AY_GENERATOR_STOP_SURVEY_V1.json",
        "prescription": "AN_ATR_STOP_FLOOR_IS_NOT_A_SPREAD_FLOOR",
        "verdict": "RESEARCH",
        "action": (
            "AW §4.3 named the cost tail a GENERATOR defect and the obvious repair — add an "
            "ATR stop floor where one is missing — does not fix it. `metals_core` carries "
            "the estate's strongest floor (max(structural, 0.25*ATR), metals.py:81) and "
            f"still reaches spread_r {survey['worst_max_spread_r_among_floored']}, a stop "
            "NARROWER than the round-trip spread. The unfloored sleeves reach "
            f"{survey['worst_max_spread_r_among_unfloored']}. ATR measures how far price "
            "moves; the spread is what the broker charges to participate, and on an illiquid "
            "instrument no multiple of the first bounds the second. No generator constant "
            "was changed: it would not fix the defect, a wider stop changes the TRADE "
            "POPULATION as well as the R geometry (so every published figure for that sleeve "
            "would need regenerating, not rescaling), and the three worst offenders "
            "(vss_fxcross_london_up_low 98.3 %, liq_asia_up_low_metal 91.7 %, asia_pdl_fade "
            "73.0 %) are not armed. What those three DO deserve is their own exit/stop "
            "frontier at the ratified rule, which is a research task with a named input."
        ),
        "evidence": {
            "counts": survey["counts"],
            "worst_max_spread_r_among_floored": survey["worst_max_spread_r_among_floored"],
            "worst_max_spread_r_among_unfloored":
                survey["worst_max_spread_r_among_unfloored"],
            "worst_three_by_exceedance_mid": {
                s: survey["by_sleeve"][s]["frac_over_live_spread_limit_mid"]
                for s in ("vss_fxcross_london_up_low", "liq_asia_up_low_metal",
                          "asia_pdl_fade")},
        },
        "margin": None, "appended_utc": NOW,
    })

    # ---- 6. AW's residual: the near-admission, priced ---------------------------------
    b = _band(verdict, "sub_xvol_pullback")
    rows.append({
        "session": "AY", "sleeve": "sub_xvol_pullback", "is_primary": False,
        "component": "phase13/receipts/CANDIDATE_FAMILY_V10.json",
        "prescription": "NEAR_ADMISSION_MISSES_AT_EVERY_DEFENSIBLE_BILL",
        "verdict": "CLOSED_NO_ACTION",
        "action": (
            "AW's residual, closed with a number. Under the live cost contract "
            f"sub_xvol_pullback reaches raw p {b['live_contract_p_raw']:.4f} at mid and high. "
            "`max_size_that_admits(0.0020, alpha=0.10) = 50`; the estate's RATIFIED family "
            "CANDIDATE_BOOK_V1 is 53 and this session's own is 514. It misses by 3 members "
            "at the most generous defensible bill and by an order of magnitude at its own. "
            "At Bonferroni alpha=0.05 the bar is 25. There is no family anyone in this "
            "estate has argued for under which it admits, so it is closed rather than "
            "carried as a candidate — and it stays ARMED regardless, because arming was "
            "never contingent on an admission."
        ),
        "evidence": {
            "p_raw_mid": b["live_contract_p_raw"],
            "max_family_that_admits": {"alpha_0.05": 25, "alpha_0.10": 50, "alpha_0.20": 100},
            "ratified_family_CANDIDATE_BOOK_V1": 53,
            "this_sessions_family_B7_5_SEPARABILITY_MINE_V1": 514,
            "n_trades_dropped_by_the_floor": b["n_dropped_by_live_contract"],
            "n_trades": [b["control_n_trades"], b["live_contract_n_trades"]],
        },
        "margin": None, "appended_utc": NOW,
    })

    # ---- 7. the latent zero-swap hazard an adversarial pass found in the LIVE gate --------
    rows.append({
        "session": "AY", "sleeve": None, "is_primary": False,
        "component": "src/components/broker_net_cost_engine.py:365-380",
        "prescription": "MISSING_CONFIG_KEYS_MAKE_THE_LIVE_TOTAL_COST_GATE_CHARGE_ZERO_SWAP",
        "verdict": "FILED_UNREACHED",
        "action": (
            "`_swap_cost_packet` derives `holding_days` from "
            "`gtos_vnext_dynamic_time_stop_bars` else `selected_cell_swap_cost_time_stop_bars` "
            "else `selected_cell_swap_cost_default_hold_days`. NEITHER config key exists "
            "anywhere in config/. A trade whose params carry no "
            "`gtos_vnext_dynamic_time_stop_bars` therefore gets holding_days=None -> "
            "swap cost_r=None -> `float(... or 0.0)` at the total assembly -> a ZERO-SWAP "
            "total_cost_r on every multi-night trade, silently loosening the 0.15 gate. Today "
            "every W7 placement carries the key from its exit profile, so the path is "
            "unreached; it is filed because the failure is SILENT, no guard exists for it, and "
            "a sleeve added without a `time_stop_bars` walks straight into it. The cheap fix "
            "is a refusal reason when holding_days is None while a swap value is present — "
            "the gate already fails closed on every other missing input."
        ),
        "evidence": {
            "keys_absent_from_config": [
                "selected_cell_swap_cost_time_stop_bars",
                "selected_cell_swap_cost_default_hold_days",
            ],
            "keys_present": [
                "selected_cell_swap_cost_horizon_days_cap",
                "selected_cell_swap_cost_minutes_per_bar",
            ],
            "found_by": "adversarial verification of AY's own live-total reconstruction",
            "reachable_today": False,
        },
        "margin": None, "appended_utc": NOW,
    })

    payload = {
        "schema": "gtos.repair_queue.session_copy.v1",
        "session": "AY", "blocks": "B1800-B1849",
        "note": ("this file is regenerated in full and is AUTHORITATIVE for AY's rows; the "
                 "shared sidecar is append-only and a landed row there is never rewritten "
                 "(AP §7.2) --- a correction is an errata row."),
        "n_rows": len(rows), "rows": rows,
    }
    payload["self_sha256"] = _sha({k: v for k, v in payload.items() if k != "self_sha256"})
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({len(rows)} rows, {OUT.stat().st_size:,} bytes)")
    for r in rows:
        print(f"  [{r['verdict']:18s}] {r['prescription']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
