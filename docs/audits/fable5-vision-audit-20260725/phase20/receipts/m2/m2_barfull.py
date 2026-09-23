"""m2_barfull — the FULL population bar walk, so the tick cohort can be placed.

Walks every `structural_distance_extreme` roster row (8 windows x 24 symbols, k=15) on the
true-UTC M1 packs with the estate's own convention, and stamps each row with the estate's
era-aware modelled spread (`walkforward.quote_side.spread_for`, the source r1 used).

Purpose: (a) reproduce the published family figure with independent code, (b) measure where
the four tick-covered instruments sit in the family's spread-over-risk distribution, so the
uncovered 20 can be BOUNDED rather than extrapolated.
"""
from __future__ import annotations

import csv
import datetime as dt
import glob
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
sys.path.insert(0, REPO)
from src.research_infra.walkforward.quote_side import spread_for, SpreadUnavailable  # noqa: E402

M1 = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
          "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
ROSTER = {"202510": "/tmp/f1/roster_202510", "202511": "/tmp/f1/roster_202511",
          "202512": "/tmp/f1/roster_202512", "202601": "/tmp/pbg_full_jan",
          "202602": "/tmp/pbg_full_feb", "202603": "/tmp/pbg_full_mar",
          "202604": "/tmp/f1/roster_202604", "202605": "/tmp/f1/roster_202605"}
NEXT = {"202510": "202511", "202511": "202512", "202512": "202601", "202601": "202602",
        "202602": "202603", "202603": "202604", "202604": "202605", "202605": None}
FAM = "structural_distance_extreme"
BIG = 1 << 62
SPREAD_NAME = {"GER40": "GER40.cash", "JP225": "JP225.cash", "NAS100": "US100.cash",
               "SPX500": "US500.cash", "UK100": "UK100.cash", "US30_cash": "US30.cash",
               "UKOIL_cash": "UKOIL.cash", "USOIL_cash": "USOIL.cash"}


def load_m1(sym, months):
    y, m = int(months[0][:4]), int(months[0][4:])
    t0 = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
    y2, m2 = int(months[-1][:4]), int(months[-1][4:])
    y3, m3 = (y2 + 1, 1) if m2 == 12 else (y2, m2 + 1)
    n = int((dt.datetime(y3, m3, 1, tzinfo=dt.timezone.utc) - t0).total_seconds() // 60)
    H = np.full(n, np.nan); L = np.full(n, np.nan); C = np.full(n, np.nan)
    for mm in months:
        p = M1 / f"bridge_ftmo_m1_{mm}" / f"{sym}_M1.csv"
        if not p.is_file():
            continue
        with p.open() as fh:
            for r in csv.DictReader(fh):
                k = int((dt.datetime.fromisoformat(r["time"]) - t0).total_seconds() // 60)
                if 0 <= k < n:
                    H[k] = float(r["high"]); L[k] = float(r["low"]); C[k] = float(r["close"])
    return t0, n, H, L, C


def walk(H, L, C, i0, i1, lng, sl, tp):
    hs = (L[i0:i1] <= sl) if lng else (H[i0:i1] >= sl)
    ht = (H[i0:i1] >= tp) if lng else (L[i0:i1] <= tp)
    a_s = int(np.argmax(hs)) if hs.any() else BIG
    a_t = int(np.argmax(ht)) if ht.any() else BIG
    if a_s == BIG and a_t == BIG:
        v = C[i0:i1]; v = v[~np.isnan(v)]
        if not len(v):
            return None
        return float(v[-1]), 2
    if a_s <= a_t:
        return sl, 0
    return tp, 1


def main(month, out):
    months = [month] + ([NEXT[month]] if NEXT.get(month) else [])
    rows = []
    for f in sorted(glob.glob(ROSTER[month] + "/*.jsonl.gz")):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                if '"structural_distance_extreme"' not in line:
                    continue
                r = json.loads(line)
                if r["f"] == FAM and r["k"] == 15:
                    rows.append(r)
    by_sym = defaultdict(list)
    for r in rows:
        by_sym[r["s"]].append(r)

    res = []
    spread_cache = {}
    for sym, rs in sorted(by_sym.items()):
        t0, n, H, L, C = load_m1(sym, months)
        sname = SPREAD_NAME.get(sym, sym)
        for r in rs:
            T = dt.datetime.fromisoformat(r["t"])
            i = int((T - t0).total_seconds() // 60)
            if not (0 < i < n - 2):
                continue
            e = float(r["e"]); slv = float(r["sl"]); d = abs(e - slv)
            if not (d > 0):
                continue
            lng = r["d"] == "L"
            s = 1.0 if lng else -1.0
            rec = {"sym": sym, "mm": month, "day": r["t"][:10], "long": lng,
                   "d_bps": d / e * 1e4}
            ck = (sname, r["t"][:13])
            sp = spread_cache.get(ck)
            if sp is None:
                try:
                    sp = spread_for(sname, T, account="FTMO", band="mid")
                except SpreadUnavailable:
                    sp = float("nan")
                spread_cache[ck] = sp
            rec["spread_model"] = sp
            rec["spread_over_d"] = sp / d if sp == sp else None
            for tr, hm in ((1.5, 120), (2.0, 240)):
                tp = e + s * tr * d
                w = walk(H, L, C, i, min(i + hm, n), lng, slv, tp)
                rec[f"bar_{tr:g}_{hm}"] = None if w is None else s * (w[0] - e) / d
                rec[f"code_{tr:g}_{hm}"] = None if w is None else w[1]
            res.append(rec)
    Path(out).write_text(json.dumps({"month": month, "n": len(res), "rows": res}))
    sys.stderr.write(f"{month}: {len(res)} rows\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
