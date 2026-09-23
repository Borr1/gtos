"""d6_dedup — the candidate under the LIVE placement contract.

`PlacementLedger.already_placed_today(sleeve, symbol, decision_day)`
(`src/components/ultimate_book/placement_ledger.py:166`, enforced at
`book_owner.py:2056`) allows ONE placement per (sleeve, symbol, decision_day),
first qualifying moment wins.  PB's book keys a setup on (symbol, family, side,
BAR), so it takes every bar that qualifies — 5.4x more trades per
(family, symbol, day) than any deployable contract permits.

This module re-prices both arms under the live rule and under a family of
relaxations, so the deployable number is separated from the research one.

    python3 d6_dedup.py --months 202601,202602,202603 --out /tmp/d6/D6_DEDUP_V1.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import d6_lib as D  # noqa: E402


def first_per_key(rows, arm, keyfn, tkey):
    """Earliest emission per placement key, in the arm's own clock."""
    best = {}
    for r in rows:
        a = r.get(arm)
        if not a:
            continue
        t = r[tkey]
        if t is None:
            continue
        k = keyfn(r)
        cur = best.get(k)
        if cur is None or t < cur[1]:
            best[k] = (r, t)
    return [(r, arm) for r, _t in best.values()]


def build(rows, mode, side_in_key=True):
    """Return (close_book, partial_book) as [(row, armkey)] under a dedup mode.

    mode 'live'   : one per (family, symbol, day)          — the ledger's rule
    mode 'side'   : one per (family, symbol, side, day)
    mode 'none'   : PB's population, one per (family, symbol, side, bar)
    """
    if mode == "none":
        close = [(r, "C") for r in rows if r.get("C")]
        part = [(r, "P") for r in rows if r.get("P")]
        return close, part

    def kc(r):
        return (r["f"], r["s"], r["day_close"]) + ((r["sd"],) if mode == "side" else ())

    def kp(r):
        return (r["f"], r["s"], r["day_part"]) + ((r["sd"],) if mode == "side" else ())

    close = first_per_key([r for r in rows if r.get("C")], "C", kc, "t_close")
    part = first_per_key([r for r in rows if r.get("P")], "P", kp, "t_part")
    return close, part


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    months = [m for m in args.months.split(",") if m] or D.months_available()

    res = {"months": months, "generated_utc": datetime.now(timezone.utc).isoformat(),
           "contract": "PlacementLedger.already_placed_today(sleeve,symbol,decision_day) "
                       "— placement_ledger.py:166, book_owner.py:2056"}

    cohorts = {"EARLY5": set(D.EARLY5), "AT_MARKET": set(D.AT_MARKET)}
    for cname, fams in cohorts.items():
        res[cname] = {}
        for mode in ("none", "side", "live"):
            allc, allp = [], []
            per_month = {}
            for m in months:
                rr = [r for r in D.load(m, fams=fams)]
                c, p = build(rr, mode)
                per_month[m] = {
                    "close": D.summarise(c, f"{m}_close"),
                    "partial": D.summarise(p, f"{m}_partial"),
                }
                allc += c
                allp += p
            res[cname][mode] = {
                "pooled_close": D.summarise(allc, "close"),
                "pooled_partial": D.summarise(allp, "partial"),
                "by_month": per_month,
            }
            # what fraction of the deduped partial book is a phantom
            ph = sum(1 for r, a in allp if not r.get("C"))
            res[cname][mode]["partial_phantom_share"] = ph / len(allp) if allp else None

    Path(args.out).write_text(json.dumps(res, indent=1))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
