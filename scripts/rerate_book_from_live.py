#!/usr/bin/env python3
"""Run the book-lane rerate over the live record and publish what it says.

    python3 scripts/rerate_book_from_live.py --packets <ultimate_book_runtime_learning_packets.jsonl.gz>

Answers, from committed code rather than a bespoke analysis, the question Stage 5 exists to answer:
*what does the live record say about each armed sleeve, priced at broker truth, at what evidence
class, and would it move the weight?*

Default-off by construction: `rerate_book(..., enabled=False)`. Nothing here mutates a config, a
broker, or a live namespace. It prints and (with -o) writes a JSON receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.components.ultimate_book.cost_true_splits import (
    build_cost_true_evidence,
    evidence_table,
    load_splits,
)
from src.components.ultimate_book.learning_actuator import rerate_book
from src.components.ultimate_book.live_evidence import (
    build_sleeve_evidence,
    collect_realized_fills,
    iter_packets,
    load_calibration,
    reconcile_cost,
)

REPO = Path(__file__).resolve().parents[1]

# THE BACKTEST HALF IS NO LONGER A CONSTANT IN THIS FILE. Until 2026-07-30 it was seven hand-carried
# CP4/CP5 triples priced by the legacy cost map -- the one F38 found charged zero commission and F39
# found credited tick erosion with the wrong sign. It is now Session AA's broker-true estate walk,
# read through `cost_true_splits.build_cost_true_evidence()`: 29 sleeves instead of 7, cost-true
# instead of legacy, and day-blocked instead of raw trade counts. The retired constant is in git
# history at 066d552b0 if a comparison is ever wanted; the two are compared in
# `phase7/receipts/AE_LEGACY_VS_COST_TRUE.json`.

# CORRECTED 2026-08-07 (wave-20 lane p4). The comment that used to stand here said the armed set
# "is read from the artifact, never from this file... a hardcoded tuple here would quietly become a
# third opinion" -- and then hardcoded one three lines later. It did become a third opinion, and it
# was wrong: `("crypto", "energy_agri", "sub_xvol_pullback")` omits `sub_mid_dn_revert`, armed on
# BOTH accounts since 2026-07-30.
#
# It was wrong twice over, because SURVIVOR and ARMED are different sets and this file conflated
# them. `SURVIVOR_BOOK_V1.json -> accounts.<acct>.survivors` is the W7 re-cost SURVIVOR book: FTMO's
# four survivors include `metals_core`, which was pulled from the live book on 2026-07-29 at 14:25,
# and exclude `sub_mid_dn_revert`, which is armed. A survivor is a sleeve that passed a cost-true
# screen; an armed sleeve is one the launcher actually passes in `--tags`. Only the second decides
# what trades.
#
# Authority for ARMED is now `src/safety/armed_set.py`, reconciled against the launcher and pinned
# by `tests/safety/test_armed_set_single_source.py`. `survivor_sets()` is kept under its true name
# because the tier work below genuinely wants the survivor screen.
SURVIVOR_BOOK = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"


def survivor_sets() -> dict:
    """{account: (sleeve, ...)} — `accounts.<acct>.survivors` from the W7 re-cost survivor book.

    NOT the armed set. See the note above; use `armed_sets()` for what is actually trading.
    """
    if not SURVIVOR_BOOK.is_file():
        return {}
    book = json.loads(SURVIVOR_BOOK.read_text())
    return {a: tuple(b.get("survivors") or []) for a, b in (book.get("accounts") or {}).items()}


def armed_sets() -> dict:
    """{account: (sleeve, ...)} — what the live launchers arm at the PRODUCTION dial.

    Production surfaces only. A minimal-size experiment surface runs a much wider sleeve list
    at a fixed few dollars a trade under its own broker identity; feeding it into a re-rate
    that produces per-sleeve up/down-weight recommendations for a 2 % book would recommend
    sizing decisions for sleeves that are not trading at that size at all."""
    from src.safety.armed_set import production_arming

    return {ns: tuple(sorted(row.armed)) for ns, row in production_arming().items()}


def _armed_union() -> tuple[str, ...]:
    from src.safety.armed_set import armed_sleeves

    return tuple(sorted(armed_sleeves()))


ARMED = _armed_union()

G4_RATE = REPO / "docs/audits/fable5-vision-audit-20260725/phase3/receipts/G4_GENERATION_RATE.json"
G4_WINDOW_DAYS = 38.0  # the live window K's G4 calibrated against (B120-129)
# Structural horizon in hours, from SURVIVOR_BOOK_V1.json. A fill produces no evidence until it
# CLOSES, so time-to-first-action is generation time plus one horizon, not generation time alone.
HORIZON_H = {"crypto": 320.0, "energy_agri": 320.0, "sub_xvol_pullback": 320.0,
             # added 2026-08-07: sub_mid_dn_revert is armed on both accounts and had no
             # horizon here, so time_to_first_action silently skipped it.
             "sub_mid_dn_revert": 320.0}


def time_to_first_action(calibration: dict) -> dict:
    """How long before the rule could act on an armed sleeve at measured generation rates.

    This is the honest answer to 'what would it need before it would do anything at all'. It is a
    projection from K's calibrated G4 rates, not a measurement of the future — labelled as such.
    """
    if not G4_RATE.is_file():
        return {"status": "unavailable", "reason": f"missing {G4_RATE}"}
    g4 = json.loads(G4_RATE.read_text()).get("rows", {})
    out: dict = {
        "basis": f"G4 calibrated fires over a {G4_WINDOW_DAYS:g}-day live window "
                 f"({G4_RATE.relative_to(REPO)}), plus one structural horizon for the fill to close",
        "evidence_class": "PROJECTION — not a measurement of future generation",
        "sleeves": {},
    }
    for s in ARMED:
        row = g4.get(s)
        if not row:
            out["sleeves"][s] = {"status": "no_measured_generation_rate",
                                 "note": "K's G4 measured 5 sleeves; this one is not among them — "
                                         "a coverage gap, not a rate of zero"}
            continue
        per_day = float(row["calibrated"]) / G4_WINDOW_DAYS
        entry = {"calibrated_fires_per_38d": row["calibrated"], "fires_per_day": round(per_day, 4)}
        for account, sleeves in calibration.get("accounts", {}).items():
            cal = sleeves.get(s) or {}
            n_down = cal.get("stop_outs_to_down_weight")
            if not cal.get("calibrated") or not n_down or per_day <= 0:
                continue
            days = n_down / per_day + HORIZON_H.get(s, 0.0) / 24.0
            entry[account] = {
                "fills_needed_worst_case": n_down,
                "projected_days_to_first_possible_down_weight": round(days, 1),
            }
        out["sleeves"][s] = entry
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--packets", type=Path, default=None,
                    help="runtime learning packet JSONL(.gz). Omit to run the backtest half alone, "
                         "which is what the armed book's own record supports today: none of the "
                         "armed sleeves has a closed live position (R section 5).")
    ap.add_argument("--calibration", type=Path, default=None)
    ap.add_argument("--splits", type=Path, default=None,
                    help="cost-true sleeve splits (default: AA_SLEEVE_SPLITS_V1.json)")
    ap.add_argument("--owner-dial-cap", type=float, default=None,
                    help="the owner's ceiling on any recommended multiplier; no recommendation may "
                         "exceed it whatever the evidence says (default MAX_UP)")
    ap.add_argument("-o", "--out", type=Path, default=None)
    args = ap.parse_args()

    cal = load_calibration(args.calibration)
    splits_doc = load_splits(args.splits)
    backtest = build_cost_true_evidence(splits_doc)
    print(f"cost-true backtest evidence : {len(backtest)} sleeves from "
          f"{splits_doc.get('cost_artifact')}")
    rep = (collect_realized_fills(iter_packets(args.packets)) if args.packets
           else collect_realized_fills([]))

    print(f"packet rows scanned      : {rep.total_rows}")
    print(f"position_closed rows     : {rep.closed_rows}")
    print(f"admitted as realized R   : {len(rep.fills)}")
    if rep.rejected:
        print("refused (published, not dropped):")
        for reason, cnt in sorted(rep.rejected.items(), key=lambda kv: -kv[1]):
            print(f"    {cnt:5d}  {reason}")

    doc: dict = {
        "schema": "gtos.learning_lane.live_rerate.v2",
        "packets": str(args.packets) if args.packets else None,
        "calibration": str(args.calibration or "default"),
        "backtest_evidence": {
            "basis": "cost_true",
            "source": str(args.splits or "AA_SLEEVE_SPLITS_V1.json"),
            "cost_artifact": splits_doc.get("cost_artifact"),
            "cost_look_ahead": splits_doc.get("cost_look_ahead"),
            "n_sleeves": len(backtest),
            "retired": "the seven CP4/CP5 legacy-cost triples that lived in this script until "
                       "2026-07-30 (F38/F39 cost map)",
        },
        "owner_dial_cap": args.owner_dial_cap,
        "armed_sets": {a: list(s) for a, s in armed_sets().items()},
        "survivor_sets": {a: list(s) for a, s in survivor_sets().items()},
        "armed_vs_survivor": ("these are DIFFERENT sets and this script conflated them until 2026-08-07: metals_core is an FTMO survivor and is not armed; sub_mid_dn_revert is armed on both accounts and is not a survivor"),
        "rows_scanned": rep.total_rows,
        "position_closed_rows": rep.closed_rows,
        "admitted_fills": len(rep.fills),
        "refused": rep.rejected,
        "refused_examples": rep.rejected_examples,
        "armed_sleeves": list(ARMED),
        "accounts": {},
    }

    # cost-layer reconciliation over the admitted fills (the tripwire input)
    recon = [reconcile_cost(f) for f in rep.fills]
    ok = [r for r in recon if r["status"] == "reconciled"]
    # Decompose the residual. cost_r's commission is a fitted per-lot schedule (Session J measured
    # it to 0.000535 R over 175 deals); its swap term additionally depends on rollover counting
    # against a hold time whose anchor Session P showed is ambiguous by 44%. Splitting the error
    # says which of the two owns it, rather than reporting one number and guessing.
    zero_swap = [abs(r["predicted_commission_r"] - r["realized_cost_r"]) for r in ok]
    doc["cost_reconciliation"] = {
        "n_reconciled": len(ok),
        "n_unpriceable": sum(1 for r in recon if r["status"] == "unpriceable_by_cost_layer"),
        "n_no_hold_time": sum(1 for r in recon if r["status"] == "no_hold_time"),
        "compared": "cost_r commission_r + swap_r vs realized (commission+swap+fee)/risk_cash; "
                    "spread and slippage excluded — they are inside the realized fill price",
        "mean_abs_error_r": (sum(r["abs_error_r"] for r in ok) / len(ok)) if ok else None,
        "worst_abs_error_r": max((r["abs_error_r"] for r in ok), default=None),
        "mean_abs_error_r_commission_only": (sum(zero_swap) / len(zero_swap)) if zero_swap else None,
        "mean_predicted_swap_r": (sum(r["predicted_swap_r"] for r in ok) / len(ok)) if ok else None,
        "coverage_classes": sorted({r["predicted_coverage"] for r in ok}),
    }
    print("\ncost-layer reconciliation:", json.dumps(doc["cost_reconciliation"]))

    armed = armed_sets()
    for account in sorted(cal.get("accounts", {})):
        ev = build_sleeve_evidence(rep.fills, account=account, calibration=cal, backtest=backtest)
        recs = rerate_book(list(ev.values()), enabled=False, owner_dial_cap=args.owner_dial_cap)
        armed_here = set(armed.get(account) or ARMED)
        print(f"\n=== {account} — default-off recommendations (cost-true backtest half) ===")
        print(f"{'sleeve':38s} {'tier':26s} {'train':>16s} {'oos':>16s} {'sealed':>16s} "
              f"{'live_n':>6s} {'live_verdict':>21s} {'verdict':>21s} {'x':>6s}")
        acc: dict = {}
        for s, r in sorted(recs.items()):
            e = ev[s]
            mark = " *" if s in armed_here else ""

            def _sp(m, n, d):
                return f"{m:+.3f}/{n}/{d}" if m is not None else "--"

            print(f"{s:38s} {str(e.cost_true_tier or '-'):26s} "
                  f"{_sp(e.train_meanR, e.train_n, e.train_days):>16s} "
                  f"{_sp(e.oos_meanR, e.oos_n, e.oos_days):>16s} "
                  f"{_sp(e.sealed_meanR, e.sealed_n, e.sealed_days):>16s} "
                  f"{r.live_n:6d} {r.live_verdict:>21s} {r.verdict:>21s} "
                  f"{r.conf_mult:6.2f}{mark}")
            acc[s] = {
                "armed": s in armed_here,
                "cost_true_tier": e.cost_true_tier,
                "evidence_basis": e.evidence_basis,
                "splits": {
                    "train": {"meanR": e.train_meanR, "n_trades": e.train_n, "n_days": e.train_days},
                    "oos": {"meanR": e.oos_meanR, "n_trades": e.oos_n, "n_days": e.oos_days},
                    "sealed": {"meanR": e.sealed_meanR, "n_trades": e.sealed_n,
                               "n_days": e.sealed_days},
                },
                "live_n": r.live_n,
                "live_day_blocks": r.live_day_blocks,
                "live_meanR": e.live_meanR,
                "live_sum_r": r.live_sum_r,
                "live_verdict": r.live_verdict,
                "live_evaluation": r.live_evaluation,
                "live_first_passage_n": r.live_first_passage_n,
                "live_raised": r.live_raised,
                "backtest_verdict": r.backtest_verdict,
                "verdict": r.verdict,
                "conf_mult": r.conf_mult,
                "gate": r.gate,
                "actuated": r.actuated,
                "live_cost_coverage": e.live_cost_coverage,
                "reason": r.reason,
            }
        doc["accounts"][account] = acc
        assert not any(v["actuated"] for v in acc.values()), "default-off violated"
        # The size-up half of the rule may never contradict the broker-true re-cost. The veto that
        # used to enforce this is retired; this asserts the property still holds on real evidence
        # rather than trusting that it does (the tripwire, mirrored in the test suite).
        bad = [s for s, v in acc.items()
               if v["conf_mult"] > 1.0 and v["cost_true_tier"] not in
               (None, "UNCONDITIONAL", "MEASURED_LIVE_CARRY", "CARRY_CONDITIONAL_LIVE_SUPPORTED")]
        assert not bad, f"{account}: cost-discredited sleeves sized up: {bad}"

    doc["time_to_first_action"] = time_to_first_action(cal)
    print("\n=== what it would take before the rule acts on an armed sleeve (PROJECTION) ===")
    for s, e in doc["time_to_first_action"].get("sleeves", {}).items():
        if "status" in e:
            print(f"  {s:20s} {e['status']}: {e.get('note','')}")
            continue
        parts = [f"{a}: {v['fills_needed_worst_case']} fills -> "
                 f"~{v['projected_days_to_first_possible_down_weight']:.0f}d"
                 for a, v in e.items() if isinstance(v, dict)]
        print(f"  {s:20s} {e['fires_per_day']:.3f} fires/day | " + " | ".join(parts))

    print("\n* = armed sleeve. actuated=False everywhere by construction (enabled=False).")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
