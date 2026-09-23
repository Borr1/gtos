"""Append Session AD's repair rows beside AA's, from the measurements rather than by hand.

    python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/ad_repair_queue.py

WHERE THE ROWS GO, AND WHY IT IS TWO PLACES
--------------------------------------------
`WAVE_7_WORKING_AGREEMENT.md` §6.5: *"Repair-queue updates append, never overwrite. Add your
rows beside AA's with your session id; the queue is a shared artifact and its history is part
of the evidence."*

`REPAIR_QUEUE_V1.json` is a single JSON document, so a read-modify-write of its `rows` array
would silently clobber a concurrent session's append — and wave 7 runs three other sessions
against the same artifact. So the canonical append is **`REPAIR_QUEUE_APPEND.jsonl`**, written
beside it with `O_APPEND`, one row per line, the same concurrency contract the trial ledger
already uses and for the same reason. A pointer is then added to `REPAIR_QUEUE_V1.json` under a
NEW top-level key (`appends`) so a reader who opens the queue finds them; AA's `rows`,
`summary` and `diagnostics` are not touched, so the clobber surface is one key that did not
exist before.

WHAT A ROW SAYS
---------------
Same schema as AA's, plus `session`. Every `action` is a next step with a number attached,
because the agreement's §7 is explicit that a failed repair's headline is the next
prescription. No row here says "reject".
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P7 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
QUEUE = P6 / "REPAIR_QUEUE_V1.json"
APPEND = P6 / "REPAIR_QUEUE_APPEND.jsonl"
FRONTIER = P7 / "EXIT_FRONTIER_V1.json"
ANALYSIS = P7 / "AD_FRONTIER_ANALYSIS_V1.json"
TIERS = P7 / "AD_CARRY_TIERS_RESTATED_V1.json"
UNITS = P7 / "AD_TIMESTOP_UNITS_V1.json"

SESSION = "AD"


def row(sleeve: str, prescription: str, component: str, action: str, evidence: dict, *,
        verdict: str = "REJECT", gate: str = "", margin=None, is_primary: bool = False) -> dict:
    return {"session": SESSION, "sleeve": sleeve, "verdict": verdict,
            "prescription": prescription, "component": component, "gate": gate,
            "margin": margin, "is_primary": is_primary, "action": action,
            "evidence": evidence}


def build() -> list[dict]:
    fr = json.loads(FRONTIER.read_text())
    an = json.loads(ANALYSIS.read_text())
    ti = json.loads(TIERS.read_text())
    un = json.loads(UNITS.read_text())
    rows: list[dict] = []

    # ---- 1. the unit finding, as a fidelity row on every sleeve whose live stop binds ----
    for sleeve, c in sorted((un.get("sleeve_contracts") or {}).items()):
        tr = c.get("frac_trades_the_time_stop_would_truncate")
        if not tr or tr < 0.05:
            continue
        rows.append(row(
            sleeve, "LIVE_EXIT_FIDELITY", "generation port / research labelling",
            (f"The live time stop is {c['time_stop_bars_m15']} PRINTED M15 bars "
             f"= {c['time_stop_in_own_bars']:.2f} {c['timeframe']} bars "
             f"= {c['time_stop_trading_hours']:.1f} trading hours, and it would truncate "
             f"{100*tr:.1f} % of the walked trades (realised median hold "
             f"{c['realised_median_hold_hours']} h). Every published economic number for this "
             f"sleeve is labelled under MAXBARS=80 with the time stop NOT applied, so it "
             f"describes a contract the live book does not run. Re-stamp the sleeve's "
             f"economics at its own contract before any composition decision uses them; the "
             f"cell is `time_stop_{max(1, round(c['time_stop_in_own_bars']))}` in "
             f"EXIT_FRONTIER_V1.json."),
            {"unit_resolution": "M15 PRINTED (trading) bars, execution.py:8953-8958",
             "time_stop_bars_m15": c["time_stop_bars_m15"],
             "time_stop_in_own_bars": c["time_stop_in_own_bars"],
             "time_stop_trading_hours": c["time_stop_trading_hours"],
             "m15_per_own_bar_trade_weighted": c["m15_per_own_bar_trade_weighted"],
             "realised_median_hold_hours": c["realised_median_hold_hours"],
             "frac_trades_truncated": tr,
             "source": "AD_TIMESTOP_UNITS_V1.json"},
            verdict="INFORMATIONAL", gate="", is_primary=False))

    # ---- 2. the carry-tier restatement ---------------------------------------------------
    for key, r in sorted((ti.get("rows") or {}).items()):
        if not r.get("restatable"):
            continue
        if r["tier_moved"]:
            rows.append(row(
                r["sleeve"], "CARRY_TIER_PROMOTED", "survivor book / OD-3 input",
                (f"On {r['account']} the published tier {r['published_tier']} is computed at a "
                 f"MODELLED {r['nights_modelled']['mean_held_to_horizon']} charged nights "
                 f"(every trade held to its horizon). MEASURED off AA's simulated path it is "
                 f"{r['nights_measured']['mean']} nights — "
                 f"{100*r['nights_ratio_measured_over_modelled']:.1f} % of the assumption — "
                 f"against a break-even of "
                 f"{r['inputs_held_fixed']['break_even_nights']}. Restated tier: "
                 f"{r['restated_tier']}. Carry is not this sleeve's open question on this "
                 f"account; take it out of the OD-3 carry column and judge it on edge."),
                {"published_tier": r["published_tier"], "restated_tier": r["restated_tier"],
                 "nights_modelled": r["nights_modelled"], "nights_measured": r["nights_measured"],
                 "carry_headroom_measured": r["carry_headroom_measured"],
                 "population_caveat": (ti.get("method") or {}).get("population_caveat"),
                 "source": "AD_CARRY_TIERS_RESTATED_V1.json"},
                verdict="INFORMATIONAL", gate="carry_tier", is_primary=False))
    for key, f in sorted(((ti.get("tier_flip_thresholds") or {}).get("rows") or {}).items()):
        acct, sleeve = key.split("::")
        if not f.get("flippable"):
            continue
        rows.append(row(
            sleeve, "TIME_STOP_FOR_CARRY_TIER", "exit contract",
            (f"On {acct} the restated tier is still CARRY_CONDITIONAL because the rule's "
             f"UNCONDITIONAL test is the p99 crossing count, not the mean — the tail still "
             f"reaches the horizon. The LOOSEST time stop that flips it is "
             f"{f['time_stop_own_bars']} own bars = {f['time_stop_hours']} h = "
             f"{100*(f['as_frac_of_horizon'] or 0):.1f} % of the assumed horizon, truncating "
             f"{100*f['frac_trades_truncated']:.1f} % of trades and taking p99 nights to "
             f"{f['capped_nights_p99']}. Price the R that costs at the matching "
             f"`time_stop_{f['time_stop_own_bars']}` cell in EXIT_FRONTIER_V1.json before "
             f"proposing it — this row prices the carry only."),
            {**f, "account": acct, "source": "AD_CARRY_TIERS_RESTATED_V1.json"},
            verdict="INFORMATIONAL", gate="carry_tier", is_primary=False))

    # ---- 3. per-sleeve exit outcome ------------------------------------------------------
    wins = {w["sleeve"]: w for w in (an.get("winners") or {}).get("rows", [])}
    for sleeve, v in sorted((fr.get("sleeves") or {}).items()):
        if not v.get("available"):
            continue
        w = wins.get(sleeve)
        if not w:
            continue
        aw = v["cells"]["as_walked"]
        improved = (w["delta_pooled"] or 0) > 0
        gates = w["best_failing_gates"]
        only_sig = gates == ["significance"]
        if w["best_verdict"] == "ADMIT":
            presc, comp = "EXIT_REPAIR_LANDED", "exit contract"
            action = (f"`{w['best_cell']}` ADMITs at measured carry "
                      f"({w['best_pooled']:.5f} R/day vs {w['as_walked_pooled']:.5f} "
                      f"as walked). Verify at all three spread bands before proposing it.")
        elif only_sig:
            presc, comp = "BREADTH_AFTER_EXIT", "family pooling"
            action = (f"The exit surface is exhausted for this sleeve and it is not the "
                      f"blocker: at its best cell `{w['best_cell']}` "
                      f"({w['best_pooled']:.5f} R/day, "
                      f"{'+' if improved else ''}{w['delta_pooled']:.5f} vs as walked) the ONLY "
                      f"failing gate is significance — p_raw {w['best_p_raw']}, q "
                      f"{w['best_q']} against a family of 69. No exit change can pay a "
                      f"multiplicity bill. Route to family pooling (Session AF); the exit "
                      f"improvement is banked and should be carried into the pooled test "
                      f"rather than re-derived.")
        elif improved:
            presc, comp = "EXIT_REPAIR_PARTIAL", "exit contract"
            action = (f"`{w['best_cell']}` moves the sleeve "
                      f"{w['delta_pooled']:+.5f} R/day to {w['best_pooled']:.5f} and still "
                      f"fails {gates}. The exit is worth taking and is not sufficient; the "
                      f"remaining gates name the next lane "
                      f"({'stability/robustness -> regime conditioning (AB/AE)' if any(g in gates for g in ('stability', 'robustness')) else 'expectancy -> entry or breadth'}).")
        else:
            presc, comp = "EXIT_SURFACE_EXHAUSTED", "exit contract"
            action = (f"No cell in {len(v['cells'])} beats the as-walked labelling "
                      f"({w['best_pooled']:.5f} vs {w['as_walked_pooled']:.5f}). The exit is "
                      f"not this sleeve's defect. Its failing gates are {gates}; the "
                      f"excursion is mean MFE {aw['mean_mfe_r']} at capture "
                      f"{aw['capture_ratio_pooled']}, so "
                      + ("there IS excursion the exit is not reaching and the next lane is "
                         "ENTRY timing / conditioning, not exits."
                         if (aw["mean_mfe_r"] or 0) > 1.0 else
                         "there is little excursion to reach — the next test is the inverse, "
                         "not another exit."))
        rows.append(row(
            sleeve, presc, comp, action,
            {"best_cell": w["best_cell"], "best_family": w["best_family"],
             "best_pooled_oos_mean_r": w["best_pooled"],
             "as_walked_pooled_oos_mean_r": w["as_walked_pooled"],
             "delta_pooled": w["delta_pooled"],
             "best_verdict": w["best_verdict"], "failing_gates": gates,
             "p_raw": w["best_p_raw"], "q_value": w["best_q"],
             "zero_carry_ceiling_pooled": w["zero_carry_ceiling_pooled"],
             "best_beats_zero_carry_ceiling": w["best_beats_zero_carry_ceiling"],
             "spread_bands": w["spread_bands"],
             "n_cells_swept": len(v["cells"]),
             "mean_mfe_r_as_walked": aw["mean_mfe_r"],
             "capture_as_walked": aw["capture_ratio_pooled"],
             "source": "EXIT_FRONTIER_V1.json"},
            verdict=w["best_verdict"], gate=(gates[0] if gates else ""),
            is_primary=True))

    # ---- 4. the trail-bound correction, as one row against the rule it corrects ----------
    tb = an.get("trail_bounds") or {}
    rows.append(row(
        "*ALL_TRAIL_SLEEVES*", "TRAIL_BOUND_READING_CORRECTED", "walkforward/exits.py",
        (f"B613's RULE — report both intrabar bounds — stands and is followed on every trail "
         f"cell here. Its READING does not: over {tb.get('n_cells_with_both_bounds')} cells "
         f"with both bounds, the intrabar-honest variant is WORSE than production in "
         f"{tb.get('n_honest_worse_than_production')} and BETTER in "
         f"{tb.get('n_honest_better_than_production')}. `simulate`'s same-bar arm-and-fill "
         f"makes the trail exit EARLIER at a price the bar may not have offered in that "
         f"sequence — on a reversion sleeve that over-claims, on a continuation sleeve it "
         f"UNDER-claims because it cuts the runner. So 'production is the upper bound' is a "
         f"property of `asian_fade` (a fade), not of the switch. Keep reporting both; stop "
         f"calling production the optimistic one."),
        {"by_mechanism": tb.get("by_mechanism"), "by_trail_arm_r": tb.get("by_trail_arm_r"),
         "source": "AD_FRONTIER_ANALYSIS_V1.json"},
        verdict="INFORMATIONAL", gate="", is_primary=False))

    # ---- 5. the frontier-algebra correction ----------------------------------------------
    sw = an.get("stop_width_frontier") or {}
    rows.append(row(
        "*ALL_COST_GEOMETRY_SLEEVES*", "FRONTIER_TARGET_CORRECTED",
        "AA_COST_GEOMETRY_FRONTIER_V1.json",
        ("AA's frontier algebra is net(k) = (gross - c_var)/k - c_fixed, which splits cost "
         "into a term scaling as 1/k and a term that does not. Swap is NEITHER: it grows with "
         "the HOLD, and a wider stop lengthens the hold. Measured on every swept sleeve, "
         "charged nights RISE at 2x (see rows). So the published required-gross-multiple "
         "targets are optimistic for any carry-bearing sleeve. Recompute the target with the "
         "hold-extension term before using it as a brief."),
        {"rows": sw.get("rows"), "source": "AD_FRONTIER_ANALYSIS_V1.json"},
        verdict="INFORMATIONAL", gate="", is_primary=False))

    return rows


def main() -> dict:
    rows = build()
    payload = [{"appended_utc": dt.datetime.now(dt.timezone.utc).isoformat(), **r}
               for r in rows]
    # O_APPEND, one write per row: the trial ledger's contract, for the same reason.
    fd = os.open(APPEND, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        for r in payload:
            os.write(fd, (json.dumps(r, sort_keys=True, default=str) + "\n").encode())
    finally:
        os.close(fd)
    print(f"appended {len(payload)} rows to {APPEND.relative_to(REPO)}")

    q = json.loads(QUEUE.read_text())
    appends = q.setdefault("appends", {})
    by_presc: dict[str, int] = {}
    for r in rows:
        by_presc[r["prescription"]] = by_presc.get(r["prescription"], 0) + 1
    appends[SESSION] = {
        "session": SESSION, "wave": 7,
        "file": str(APPEND.relative_to(REPO)),
        "format": "append-only JSONL, O_APPEND per row — safe for concurrent sessions",
        "n_rows": len(rows),
        "by_prescription": dict(sorted(by_presc.items())),
        "note": ("AA's `rows`, `summary` and `diagnostics` are untouched. This key did not "
                 "exist before, so the clobber surface of writing it is one new key."),
        "produced_by": ["EXIT_FRONTIER_V1.json", "AD_FRONTIER_ANALYSIS_V1.json",
                        "AD_CARRY_TIERS_RESTATED_V1.json", "AD_TIMESTOP_UNITS_V1.json"],
    }
    QUEUE.write_text(json.dumps(q, indent=1, default=str))
    print(f"pointer written into {QUEUE.relative_to(REPO)} -> appends.{SESSION}")
    print("by prescription:", json.dumps(dict(sorted(by_presc.items()))))
    return {"n_rows": len(rows), "by_prescription": by_presc}


if __name__ == "__main__":
    main()
