"""m1 — one per-row measurement of the broad V4 family on the REPAIRED instrument.

WHAT THIS IS
------------
Wave 19 published the family's funnel, family table, win rates and toll deciles on a
walker that never crossed the spread (r1) and a generator that emitted orders whose stop
the market had already breached and decisions priced off bars that closed hours earlier
(r2).  This re-measures every one of those numbers on the repaired instrument, over the
whole eight-window open population.  Nothing is sampled.

STRUCTURE — one walk, many groupbys
-----------------------------------
r2's blast-radius proof (`R2_BLAST_V1.json`, independently reproduced by v1) established
that the generator repair is strictly SUBTRACTIVE on this population: 0 emissions added,
90,217 removed, 0 surviving geometry moved, exact on all eight windows.  So the repaired
roster is a FILTER over the frozen wave-19 roster, and every arm's economics is an exact
groupby of one measurement rather than a re-walk.  This script re-verifies that claim
per window (`subtractive_check`) rather than assuming it.

THE TWO QUOTE CONVENTIONS, both from the canonical module
---------------------------------------------------------
`src.research_infra.walkforward.quote_side` derives the convention from the live engine.
Two anchorings apply here and the family uses both, by ORDER TYPE:

  at-market families (7 of 10) — the entry IS the decision-instant close (r2 measured
      fill_gap_R == 0 on 144,725 of 144,725 rows), i.e. a market order.  A market order
      transacts on the far side and the estate's only order router then hangs both exit
      legs off the transacted price (`order_router.py:66-73`), so the whole correction is
      `anchor = entry + direction * spread` — the entire geometry translates.

  POI limit families (3 of 10) — a pending order rests at an emitted structural level, so
      it transacts AT that level.  `level_anchor_for_replay` then gives the exit anchor
      (LONG: unchanged; SHORT: level - spread) and `entry_trigger_level_on_tape` gives the
      fill trigger (LONG: level - spread, i.e. a buy limit fills LATER and LESS often;
      SHORT: unchanged).

Both are exactly the offsets the shipped module returns; `_assert_module_agreement` pins
that at import so the hot loop cannot drift from the module it claims to implement.

THE SPREAD
----------
Primary is the toll's OWN spread term (`pbg_econ.CostModel.spread_bps`, hour-aware tick
spread).  That is deliberate: r1 established that charging the spread as a cost LEVEL and
as a geometry shift at the same time double-counts it, so the corrected net drops the
spread term and keeps commission + slippage + swap.  Using the same number in both places
makes that substitution exact.  The era-aware model (`quote_side.spread_for`) is carried
per row as a sensitivity arm.

CONTROL
-------
The uncorrected arm must reproduce `R2_ARM_ECON_V1.json -> arms.legacy` exactly
(n 1,167,099, gross -0.022564, cost 0.084479, net -0.107043, fills 345,963).  It is the
same contract as f1/r2: at-market -> market order at the decision instant, POI -> honest
resting limit, horizon 120 M1 bars, target 1.5 R, cost charged once on fill, in R.
"""
from __future__ import annotations

import bisect
import csv
import glob
import gzip
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, PBG)
sys.path.insert(0, REPO)
os.chdir(REPO)

import pbg_lib as PL  # noqa: E402
import pbg_econ as E  # noqa: E402

from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    SpreadUnavailable,
    entry_quote_offset,
    exit_quote_offset,
    spread_for,
)

RR = 1.5
HOR = 120
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
Q = BarQuote.BID

LEGACY = {
    "2025-10": "/tmp/f1/roster_202510",
    "2025-11": "/tmp/f1/roster_202511",
    "2025-12": "/tmp/f1/roster_202512",
    "2026-01": "/tmp/d4/rosters/202601",
    "2026-02": "/tmp/d4/rosters/202602",
    "2026-03": "/tmp/d4/rosters/202603",
    "2026-04": "/tmp/f1/roster_202604",
    "2026-05": "/tmp/f1/roster_202605",
}
REPAIRED = {w: "/tmp/r2/arm_default/" + w.replace("-", "") for w in LEGACY}
NEXT = {"2025-10": "202511", "2025-11": "202512", "2025-12": "202601", "2026-01": "202602",
        "2026-02": "202603", "2026-03": "202604", "2026-04": "202605", "2026-05": None}

#: broad-universe name -> the broker name the era-aware spread model is keyed on
SPREAD_NAME = {"GER40": "GER40.cash", "JP225": "JP225.cash", "NAS100": "US100.cash",
               "SPX500": "US500.cash", "UK100": "UK100.cash", "US30_cash": "US30.cash",
               "UKOIL_cash": "UKOIL.cash", "USOIL_cash": "USOIL.cash"}

REASON = {"stop": 0, "target": 1, "path_end": 2, "no_fill": 3}


def _assert_module_agreement() -> None:
    """The offsets the hot loop hard-codes ARE the shipped module's, on both sides."""
    s = 0.5
    assert entry_quote_offset(1, Q, s) == s and exit_quote_offset(1, Q, s) == 0.0
    assert entry_quote_offset(-1, Q, s) == 0.0 and exit_quote_offset(-1, Q, s) == s


_assert_module_agreement()


class M15Series:
    __slots__ = ("t", "c")

    def __init__(self, rows):
        self.t = [r[0] for r in rows]
        self.c = [r[1] for r in rows]


def load_m15():
    out = {}
    for p in sorted(glob.glob(os.path.join(str(PL.M15_DIR), "*_M15.csv"))):
        sym = os.path.basename(p)[: -len("_M15.csv")]
        rows = []
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append((datetime.fromisoformat(r["time"]).replace(tzinfo=None),
                             float(r["close"])))
        rows.sort()
        out[sym] = M15Series(rows)
    return out


def walk_market(hi, lo, cl, n, i, *, stop, tgt, long, d, anchor, horizon=HOR):
    """Market order sent at stamp i; path is stamps [i+1, i+1+horizon).  Stop wins ties.

    `stop`/`tgt` are ABSOLUTE tape prices and `anchor` the transacted price, so the
    uncorrected arm is recovered exactly by passing the emitted levels with anchor=entry.
    """
    a = i + 1
    b = min(a + horizon, n)
    if a >= b:
        return None
    h, l, c = hi[a:b], lo[a:b], cl[a:b]
    ok = ~np.isnan(c)
    if not ok.any():
        return None
    h, l, c = h[ok], l[ok], c[ok]
    if long:
        ht, hs = h >= tgt, l <= stop
    else:
        ht, hs = l <= tgt, h >= stop
    it = int(np.argmax(ht)) if ht.any() else None
    iss = int(np.argmax(hs)) if hs.any() else None
    if iss is not None and (it is None or iss <= it):
        return (-1.0, "stop", iss + 1)
    if it is not None:
        return (float(RR), "target", it + 1)
    last = float(c[-1])
    return ((last - anchor) / d if long else (anchor - last) / d, "path_end", len(c))


def walk_limit(hi, lo, cl, n, i, *, trigger, stop, tgt, long, d, anchor, horizon=HOR):
    """Resting limit at `trigger` from stamp i; walk starts the bar AFTER the fill.

    Never touched inside the horizon -> 0.0 R and no cost: you did not trade.
    Exactly `f1_walk.walk_limit2`'s contract, with the trigger and the exit geometry
    supplied separately so the corrected arm can move one without the other.
    """
    a = i
    b = min(a + horizon, n)
    if a >= b:
        return None
    h, l = hi[a:b], lo[a:b]
    ok = ~np.isnan(h)
    if not ok.any():
        return None
    idxs = np.nonzero(ok)[0]
    touched = (l[idxs] <= trigger) if long else (h[idxs] >= trigger)
    if not touched.any():
        return (0.0, "no_fill", 0)
    j = int(idxs[int(np.argmax(touched))])
    res = walk_market(hi, lo, cl, n, a + j, stop=stop, tgt=tgt, long=long, d=d,
                      anchor=anchor, horizon=horizon - j - 1)
    if res is None:
        return (0.0, "no_fill", 0)
    return res


def roster_keys(rd):
    """The identity of every emission in a roster directory, for the subtractive check."""
    out = set()
    for f in sorted(glob.glob(os.path.join(rd, "*.jsonl.gz"))):
        if not os.path.exists(f.replace(".jsonl.gz", ".stats.json")):
            continue
        for line in gzip.open(f, "rt"):
            r = json.loads(line)
            if r["k"] != 15:
                continue
            out.add((r["t"], r["s"], r["f"], r["d"], round(r["e"], 10), round(r["sl"], 10)))
    return out


def main(window, out_path):
    S = load_m15()
    mons = [window.replace("-", "")] + ([NEXT[window]] if NEXT.get(window) else [])
    tape = E.Tape(list(PL.SYMBOLS), mons)
    cm = E.CostModel()

    # ---- subtractive check: repaired roster == legacy roster minus refusals, nothing new
    kl = roster_keys(LEGACY[window])
    kr = roster_keys(REPAIRED[window])
    sub = {"legacy": len(kl), "repaired": len(kr), "added": len(kr - kl),
           "removed": len(kl - kr)}

    fams, syms = [], []
    fi, si = {}, {}
    rec = {k: [] for k in (
        "day", "fam", "sym", "long", "e", "sl", "d", "dbps", "gap", "age",
        "s_tick", "s_era", "g_old", "g_cor", "g_era", "r_old", "r_cor",
        "fill_old", "fill_cor", "px_spread", "px_comm", "px_slip", "px_swap", "kept")}

    scache: dict[tuple, float] = {}
    for f in sorted(glob.glob(os.path.join(LEGACY[window], "*.jsonl.gz"))):
        if not os.path.exists(f.replace(".jsonl.gz", ".stats.json")):
            continue
        for line in gzip.open(f, "rt"):
            r = json.loads(line)
            if r["k"] != 15:
                continue
            sym = r["s"]
            if sym not in tape.c:
                continue
            ser = S.get(sym)
            if ser is None:
                continue
            T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
            j = bisect.bisect_right(ser.t, T - timedelta(minutes=15)
                                    + timedelta(seconds=2)) - 1
            if j < 0:
                continue
            cp = ser.c[j]
            age = int((T - (ser.t[j] + timedelta(minutes=15))).total_seconds() // 60)
            i = tape.idx(r["t"])
            if not (0 < i < tape.n):
                continue
            e, sl = r["e"], r["sl"]
            d = abs(e - sl)
            if not d > 0:
                continue
            lng = r["d"] == "L"
            sgn = 1.0 if lng else -1.0
            gap = (cp - e) / d * sgn
            fam = r["f"]

            # --- the two spreads
            hbroker = cm.broker_hour(r["t"])
            s_tick = cm.spread_bps(sym, hbroker) / 1e4 * e
            ck = (sym, T.date(), T.hour)
            s_era = scache.get(ck)
            if s_era is None:
                try:
                    s_era = spread_for(SPREAD_NAME.get(sym, sym),
                                       T.replace(tzinfo=__import__("datetime").timezone.utc),
                                       account="FTMO", band="mid")
                except SpreadUnavailable:
                    s_era = float("nan")
                scache[ck] = s_era

            tgt = e + sgn * RR * d
            hi, lo, cl, n = tape.h[sym], tape.l[sym], tape.c[sym], tape.n

            if fam in POI:
                o_old = walk_limit(hi, lo, cl, n, i, trigger=e, stop=sl, tgt=tgt,
                                   long=lng, d=d, anchor=e)
                # LEVEL anchoring: transacted price IS the level; only the exit legs and
                # the fill trigger translate, and they translate differently per side.
                def poi(sp):
                    if not np.isfinite(sp):
                        return None
                    trg = e - entry_quote_offset(1 if lng else -1, Q, sp)
                    off = -exit_quote_offset(1 if lng else -1, Q, sp)
                    return walk_limit(hi, lo, cl, n, i, trigger=trg, stop=sl + off,
                                      tgt=tgt + off, long=lng, d=d, anchor=e + off)
                o_cor, o_era = poi(s_tick), poi(s_era)
            else:
                o_old = walk_market(hi, lo, cl, n, i, stop=sl, tgt=tgt, long=lng, d=d,
                                    anchor=e)
                # FILL anchoring: the whole geometry translates by direction * spread.
                def mkt(sp):
                    if not np.isfinite(sp):
                        return None
                    off = sgn * sp
                    return walk_market(hi, lo, cl, n, i, stop=sl + off, tgt=tgt + off,
                                       long=lng, d=d, anchor=e + off)
                o_cor, o_era = mkt(s_tick), mkt(s_era)

            if o_old is None or o_cor is None:
                continue
            px_tot, terms = cm.cost_px(sym, r["t"], e, lng, hold_min=HOR)

            if fam not in fi:
                fi[fam] = len(fams)
                fams.append(fam)
            if sym not in si:
                si[sym] = len(syms)
                syms.append(sym)

            rec["day"].append(int(r["t"][:10].replace("-", "")))
            rec["fam"].append(fi[fam])
            rec["sym"].append(si[sym])
            rec["long"].append(lng)
            rec["e"].append(e)
            rec["sl"].append(sl)
            rec["d"].append(d)
            rec["dbps"].append(d / e * 1e4)
            rec["gap"].append(gap)
            rec["age"].append(age)
            rec["s_tick"].append(s_tick)
            rec["s_era"].append(s_era)
            rec["g_old"].append(o_old[0])
            rec["g_cor"].append(o_cor[0])
            rec["g_era"].append(o_era[0] if o_era else float("nan"))
            rec["r_old"].append(REASON[o_old[1]])
            rec["r_cor"].append(REASON[o_cor[1]])
            rec["fill_old"].append(o_old[1] != "no_fill")
            rec["fill_cor"].append(o_cor[1] != "no_fill")
            rec["px_spread"].append(terms["spread"])
            rec["px_comm"].append(terms["commission"])
            rec["px_slip"].append(terms["slippage"])
            rec["px_swap"].append(terms["swap"])
            rec["kept"].append(
                (r["t"], sym, fam, r["d"], round(e, 10), round(sl, 10)) in kr)

    arr = {}
    for k, v in rec.items():
        if k in ("fam", "sym", "day", "r_old", "r_cor", "age"):
            arr[k] = np.asarray(v, dtype=np.int32)
        elif k in ("long", "fill_old", "fill_cor", "kept"):
            arr[k] = np.asarray(v, dtype=bool)
        else:
            arr[k] = np.asarray(v, dtype=np.float64)
    arr["_fams"] = np.asarray(fams)
    arr["_syms"] = np.asarray(syms)
    arr["_sub"] = np.asarray(json.dumps(sub))
    np.savez_compressed(out_path, **arr)
    print(window, "rows", len(rec["day"]), "sub", sub, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
