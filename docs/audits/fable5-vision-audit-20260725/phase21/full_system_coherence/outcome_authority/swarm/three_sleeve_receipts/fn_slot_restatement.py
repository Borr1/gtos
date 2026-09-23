#!/usr/bin/env python3
"""Restate each account's SYMBOL SLOT surface for the three-sleeve armed book.

Measurement only.  Reads the 2026-08-11 live symbol probe
(`live_book_integrity_receipts/SYMBOL_UNIVERSE_V1.json`, captured on the host at 10:26Z with
`symbols_get` / `symbol_info` only) and re-derives the per-account slot counts for the book
that is armed AFTER the 11:47Z sleeve pull.  No broker is contacted here; the probe is the
evidence and this is arithmetic on it.

`SLEEVE_PULL_SUB_MID_DN_REVERT_V1.md` records that `sub_mid_dn_revert` carried 20 of FTMO's
42 armed slots.  The open question it leaves (§6.1) is how much of redacted_account's already
smaller book survives, and whether the two accounts have converged or diverged.

Usage: python3 fn_slot_restatement.py [out.json]
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SWARM = HERE.parent
PROBE = SWARM / "live_book_integrity_receipts/SYMBOL_UNIVERSE_V1.json"
REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))
from src.safety.armed_set import armed_sleeves      # noqa: E402

THREE = sorted(armed_sleeves())
PULLED = "sub_mid_dn_revert"

P = json.loads(PROBE.read_text())
out = {
    "schema": "gtos.wave21.fn_slot_restatement.v1",
    "measurement_only": True,
    "probe_as_of_utc": P["as_of_utc"],
    "probe_armed_tags_then": P["armed_tags"],
    "armed_sleeves_now": THREE,
    "accounts": {},
}

for acct, a in P["accounts"].items():
    slots = a["slots"]
    unreach = {(u.get("sleeve"), u.get("symbol") or u.get("canonical")) for u in a["unreachable_slots"]}
    unreach_sym_by_sleeve = collections.defaultdict(set)
    for sl, sym in unreach:
        unreach_sym_by_sleeve[sl].add(sym)

    def count(book):
        tot = [s for s in slots if s.get("sleeve") in book]
        bad = [s for s in tot
               if (s.get("symbol") or s.get("canonical")) in unreach_sym_by_sleeve.get(s.get("sleeve"), set())]
        return len(tot), len(tot) - len(bad), len(bad)

    t4, r4, u4 = count(set(THREE) | {PULLED})
    t3, r3, u3 = count(set(THREE))
    per = {}
    for sl in sorted(set(THREE) | {PULLED}):
        tt, rr, uu = count({sl})
        per[sl] = dict(slots=tt, reachable=rr, unreachable=uu)
    out["accounts"][acct] = dict(
        broker_server=a["broker_server"],
        broker_total_symbol_count=a["broker_total_symbol_count"],
        four_sleeve_slots=t4, four_sleeve_reachable=r4, four_sleeve_unreachable=u4,
        three_sleeve_slots=t3, three_sleeve_reachable=r3, three_sleeve_unreachable=u3,
        slots_lost_to_the_pull=t4 - t3,
        reachable_lost_to_the_pull=r4 - r3,
        reachable_pct_lost=round(100.0 * (r4 - r3) / max(1, r4), 2),
        per_sleeve=per,
        unreachable_symbols_now=sorted({s for sl in THREE for s in unreach_sym_by_sleeve.get(sl, ())}),
    )

f = out["accounts"]["FTMO"]
n = out["accounts"]["redacted_account"]
out["divergence"] = dict(
    reachable_ratio_ftmo_over_fn_four_sleeve=round(f["four_sleeve_reachable"]
                                                   / max(1, n["four_sleeve_reachable"]), 4),
    reachable_ratio_ftmo_over_fn_three_sleeve=round(f["three_sleeve_reachable"]
                                                    / max(1, n["three_sleeve_reachable"]), 4),
    verdict=("CONVERGED slightly" if abs(f["three_sleeve_reachable"] / max(1, n["three_sleeve_reachable"])
                                         - 1) < abs(f["four_sleeve_reachable"] / max(1, n["four_sleeve_reachable"]) - 1)
             else "DIVERGED slightly"),
)

DEST = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "FN_SLOT_RESTATEMENT_V1.json"
DEST.write_text(json.dumps(out, indent=1))
print("WROTE", DEST)
print(json.dumps(out["accounts"], indent=1))
print(json.dumps(out["divergence"], indent=1))
