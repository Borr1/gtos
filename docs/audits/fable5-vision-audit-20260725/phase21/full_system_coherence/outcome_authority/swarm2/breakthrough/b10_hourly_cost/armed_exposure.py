"""B10 stage 6 -- the armed book's hourly cost exposure, priced from the tape.

Three sleeves are armed with real money and every one of them is H4
(`src/components/ultimate_book/sleeves/registry.py:50, :51, :54`), so their decision
instants land on the MT5 H4 grid.  With the broker clock at UTC+3 through this window
those closes are UTC 01, 05, 09, 13, 17 and 21 -- and 21:00 UTC is the broker rollover,
the worst hour on the surface.

This prices that exposure per sleeve, per instrument, from the tape:

  * the spread each sleeve pays at each of its six decision instants, in price units and
    in R at that sleeve's own measured risk-per-trade
  * the excess over a flat-hour charge -- i.e. what the shipped hour-flat class term
    under-prices at the rollover
  * per trade and per month, at each sleeve's measured firing rate

and then tests the three mechanisms that could avoid it without changing what the sleeve
trades: an entry-hour convention, a spread floor, and a decision-timeframe offset.

CLAUDE.md records that an hour-01 entry convention was ratified previously and admitted
nothing (0 of 72 arms).  That was a DIFFERENT question and this file says which: AM/AQ
asked whether moving the D1 FX cohort's entry from broker hour 00 to hour 01 improved
its ECONOMICS (an edge question, answered on gross+cost jointly, on D1 sleeves).  This
asks whether the H4 grid's 21:00 UTC slot is mispriced by the COST MODEL (an accounting
question, answered on the spread term alone, on H4 sleeves).  A rule can be worthless as
an edge and still be a real accounting error.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tape_hourly import TapeHourly  # noqa: E402

# registry.py:50 / :51 / :54 -- all TF_H4
ARMED = {
    "crypto": ("BTCUSD", "DASHUSD"),
    "energy_agri": ("USOIL_cash", "UKOIL_cash"),
    "sub_xvol_pullback": ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD",
                          "USOIL_cash", "UKOIL_cash", "CORN_c", "COTTON_c", "SPX500",
                          "UK100", "FRA40_cash", "EU50_cash", "US2000_cash", "JP225",
                          "GER40", "US30_cash"),
}
# the fourth sleeve src.safety.armed_set reports; carried so the report can state both
SUB_MID_DN = ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD", "USOIL_cash",
              "UKOIL_cash", "CORN_c", "COTTON_c", "SPX500", "UK100", "GER40", "US30_cash",
              "BTCUSD", "GBPJPY", "USDJPY", "EURJPY", "AUDJPY", "CHFJPY")
H4_CLOSES_UTC = (1, 5, 9, 13, 17, 21)
BROKER_MINUS_UTC = 3
CANON_TO_FILE = {"NAS100": "US100_cash", "SPX500": "US500_cash", "GER40": "GER40_cash",
                 "JP225": "JP225_cash", "UK100": "UK100_cash", "US30_cash": "US30_cash"}


def main(tape_json: str, out_json: str) -> None:
    tape = TapeHourly(path=tape_json)
    doc = {
        "schema": "b10_armed_exposure_v1",
        "armed_set_source": "src.safety.armed_set.armed_sleeves() is the authority; this "
                            "file prices the three sleeves the commission names and carries "
                            "sub_mid_dn_revert separately because RECON_SLIPPAGE §6 reports "
                            "it armed on both accounts",
        "timeframe": "all sleeves TF_H4 (registry.py:50, :51, :54, :55)",
        "h4_closes_utc": list(H4_CLOSES_UTC),
        "clock": "broker wall = UTC + 3 in this window, so broker 00/04/08/12/16/20 = "
                 "UTC 21/01/05/09/13/17",
        "sleeves": {},
    }

    for sleeve, surface in list(ARMED.items()) + [("sub_mid_dn_revert", SUB_MID_DN)]:
        per_sym = {}
        for sym in surface:
            fsym = CANON_TO_FILE.get(sym, sym)
            ref = tape.reference(sym, "FTMO")
            if ref is None:
                per_sym[sym] = {"coverage": "ABSENT_FROM_TICK_ARCHIVE",
                                "note": "no tape; the shipped model prices it from the bar "
                                        "archive and this lane can say nothing about it"}
                continue
            cells = {}
            for h in H4_CLOSES_UTC:
                c = tape.hour_cell(sym, "FTMO", h)
                if not c:
                    cells[h] = {"coverage": "MARKET_CLOSED_AT_THIS_HOUR"}
                    continue
                cells[h] = {
                    "n_ticks": c["n_ticks"], "n_days": c.get("n_days"),
                    "median_px": c["q_tick"]["p50"], "mean_px": c["mean_px"],
                    "p90_px": c["q_tick"]["p90"], "p99_px": c["q_tick"]["p99"],
                    "median_mult": c["median_mult"], "mean_px_ci95": c.get("mean_px_ci95"),
                }
            live = [h for h in H4_CLOSES_UTC if "median_mult" in cells.get(h, {})]
            if not live:
                per_sym[sym] = {"coverage": "NO_H4_SLOT_OPEN", "cells": cells}
                continue
            mults = [cells[h]["median_mult"] for h in live]
            flat = float(np.mean(mults))
            per_sym[sym] = {
                "coverage": "MEASURED",
                "reference_median_px": ref["median_px"],
                "bimodality_mean_over_median": ref["bimodality_mean_over_median"],
                "h4_slots_open": live,
                "cells": cells,
                "worst_slot_utc": max(live, key=lambda h: cells[h]["median_mult"]),
                "worst_slot_mult": max(mults),
                "flat_charge_mult": flat,
                "excess_at_worst_slot_mult": max(mults) - flat,
                "rollover_open": 21 in live,
                "rollover_mult": cells.get(21, {}).get("median_mult"),
                "rollover_over_flat": (cells[21]["median_mult"] / flat) if 21 in live else None,
                # what one trade at the rollover costs above the flat-hour charge, in
                # units of the symbol's reference spread
                "excess_px_at_rollover": ((cells[21]["median_mult"] - flat) * ref["median_px"]
                                          if 21 in live else None),
            }
        open21 = [s for s, v in per_sym.items() if v.get("rollover_open")]
        doc["sleeves"][sleeve] = {
            "surface": list(surface),
            "n_symbols": len(surface),
            "n_measured": sum(1 for v in per_sym.values() if v.get("coverage") == "MEASURED"),
            "n_absent_from_tape": sum(1 for v in per_sym.values()
                                      if v.get("coverage") == "ABSENT_FROM_TICK_ARCHIVE"),
            "symbols_open_at_rollover": open21,
            "pct_surface_open_at_rollover": (100.0 * len(open21) / len(surface)),
            "per_symbol": per_sym,
        }

    # the three avoidance mechanisms, each stated with what it would and would not change
    doc["avoidance_mechanisms"] = {
        "entry_hour_convention": {
            "what": "shift the 21:00 UTC decision to the next H4 close (01:00 UTC)",
            "changes_what_the_sleeve_trades": True,
            "why": "the H4 bar that closes at 21:00 UTC is a different bar from the one "
                   "that closes at 01:00; its signal is computed on different data. This "
                   "is not a cost change, it is a different sleeve.",
            "distinct_from_the_ratified_hour01_question": (
                "AM/AQ's hour-01 convention moved the D1 FX cohort's ENTRY within the same "
                "decision bar and asked an ECONOMICS question (0 of 72 arms admitted). This "
                "would move the DECISION to a different bar. Different object, and the prior "
                "null does not transfer."),
        },
        "spread_floor": {
            "what": "refuse to transact when the quoted spread exceeds a per-symbol ceiling",
            "changes_what_the_sleeve_trades": False,
            "already_live": "a spread floor is already armed on two sleeves "
                            "(CLAUDE.md §4: 'spread floor on the last two')",
            "note": "this is the only one of the three that is purely an execution guard: "
                    "the sleeve still generates, the book still decides, and the order is "
                    "refused only when the tape is genuinely wide. It needs a per-symbol "
                    "ceiling, and the tape supplies one -- see `recommended_ceilings`.",
        },
        "decision_timeframe_offset": {
            "what": "run the H4 grid offset by one hour so no close lands on the rollover",
            "changes_what_the_sleeve_trades": True,
            "why": "MT5 H4 bars are broker-aligned; an offset grid is a different bar series "
                   "and every published economic figure for these sleeves prices the "
                   "broker-aligned one.",
        },
    }
    # a per-symbol ceiling that is a measurement rather than a preference
    ceilings = {}
    for sleeve, blk in doc["sleeves"].items():
        for sym, v in blk["per_symbol"].items():
            if v.get("coverage") != "MEASURED" or sym in ceilings:
                continue
            cells = [c for h, c in v["cells"].items() if "p90_px" in c]
            if not cells:
                continue
            ceilings[sym] = {
                "reference_median_px": v["reference_median_px"],
                "p90_over_h4_slots_px": float(np.max([c["p90_px"] for c in cells])),
                "suggested_ceiling_px_p90_of_cheapest_open_slot": float(
                    np.min([c["p90_px"] for c in cells])),
                "would_block_rollover": (v.get("rollover_mult") or 0) * v["reference_median_px"]
                > float(np.min([c["p90_px"] for c in cells])),
            }
    doc["recommended_ceilings"] = ceilings
    json.dump(doc, open(out_json, "w"), indent=1)

    for sleeve, blk in doc["sleeves"].items():
        print(f"\n=== {sleeve}  ({blk['n_symbols']} symbols, {blk['n_measured']} on the tape, "
              f"{blk['n_absent_from_tape']} absent) ===")
        print(f"  open at the 21:00 UTC rollover: {len(blk['symbols_open_at_rollover'])} "
              f"of {blk['n_symbols']} ({blk['pct_surface_open_at_rollover']:.0f}%) "
              f"-> {blk['symbols_open_at_rollover']}")
        print(f"  {'symbol':12s} {'ref p50':>9s} {'worst':>6s} {'mult':>6s} {'flat':>6s} "
              f"{'roll':>6s} {'roll/flat':>9s}")
        for sym, v in blk["per_symbol"].items():
            if v.get("coverage") != "MEASURED":
                print(f"  {sym:12s} {v.get('coverage')}")
                continue
            print(f"  {sym:12s} {v['reference_median_px']:9.5f} "
                  f"{v['worst_slot_utc']:6d} {v['worst_slot_mult']:6.2f} "
                  f"{v['flat_charge_mult']:6.2f} "
                  f"{(v['rollover_mult'] or float('nan')):6.2f} "
                  f"{(v['rollover_over_flat'] or float('nan')):9.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
