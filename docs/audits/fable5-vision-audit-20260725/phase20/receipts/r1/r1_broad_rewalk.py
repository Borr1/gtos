"""r1-5b — re-walk the BROAD V4 family's roster on both quote conventions.

Population: all **1,211,077** emissions of the eight open windows (2025-10..2026-05), from
the concurrent `d8` lane's emission arrays (`D8_EMIT_<mm>.npz`), read-only. Nothing
sampled; the sealed three (Jun/Aug/Sep 2025) are not opened.

ANCHORING — measured, not assumed
----------------------------------
The broad family is **LEVEL**-anchored, and the generator says so:
`broader_origin_generators.py:1697-1712` records `"zone_midpoint": entry` — the entry is
the POI's own midpoint and the stop is the zone edge plus an ATR buffer, both absolute
structural prices, and the target is `entry + target_rr * (entry - stop)`. Nothing hangs
off a fill.

On a BID tape that gives a different correction from the live book's:

    LONG  — SL/TP are bid-quoted, so they resolve on the tape unshifted; the displacement
            lands on the ENTRY trigger (a buy fills when the ASK reaches the level, i.e.
            one spread early in tape terms) and the trade is then walked from a market
            that is one spread below where the unshifted walk believes it is.
    SHORT — the entry trigger is exact and both exit legs take the full shift.

Both are produced by `walkforward.quote_side` and both are published, together with the
FILL-anchored variant, because the FILL number is the one comparable to the live sleeve
estate and to d8x's own symmetric bound.

CONTROL
-------
`median_d_bps` per symbol must reproduce `D8X_GEOM_V1.json → per_symbol` to 1e-3 on all
24 symbols, or the roster/tape join is wrong and the run refuses to write.
"""

from __future__ import annotations

import collections
import csv
import datetime as dt
import json
import math
import statistics
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

from src.research_infra.walkforward.quote_side import (  # noqa: E402
    BarQuote,
    SpreadUnavailable,
    spread_for,
)

HERE = Path(__file__).resolve().parent
DISC = REPO / "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
EMIT = DISC / "d8"
GEOM = DISC / "D8X_GEOM_V1.json"
M1 = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
          "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
OUT = HERE / "R1_BROAD_DELTA_V1.json"

MONTHS = ("202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605")
TARGET_R = 2.0
HORIZON = 240  # the shipped contract d8x priced

#: the broad universe's own names -> the broker names the spread model is keyed on
SPREAD_NAME = {
    "GER40": "GER40.cash", "JP225": "JP225.cash", "NAS100": "US100.cash",
    "SPX500": "US500.cash", "UK100": "UK100.cash", "US30_cash": "US30.cash",
    "UKOIL_cash": "UKOIL.cash", "USOIL_cash": "USOIL.cash",
}


def tape(month: str, sym: str):
    p = M1 / f"bridge_ftmo_m1_{month}" / f"{sym}_M1.csv"
    if not p.is_file():
        return None
    y, m = int(month[:4]), int(month[4:])
    t0 = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
    y2, m2 = (y + 1, 1) if m == 12 else (y, m + 1)
    n = int((dt.datetime(y2, m2, 1, tzinfo=dt.timezone.utc) - t0).total_seconds() // 60)
    hi = np.full(n, np.nan)
    lo = np.full(n, np.nan)
    cl = np.full(n, np.nan)
    with p.open() as fh:
        for row in csv.DictReader(fh):
            k = int((dt.datetime.fromisoformat(row["time"]) - t0).total_seconds() // 60)
            if 0 <= k < n:
                hi[k] = float(row["high"])
                lo[k] = float(row["low"])
                cl[k] = float(row["close"])
    return hi, lo, cl, t0


def walk_levels(hi, lo, cl, i, long, entry, stop, tgt, horizon=HORIZON):
    """Level walk on the tape, estate semantics: path is [i+1, i+horizon], stop wins ties."""
    a, b = i + 1, min(i + 1 + horizon, len(cl))
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
        return stop, "stop"
    if it is not None:
        return tgt, "target"
    return float(c[-1]), "path_end"


def main() -> int:
    geom = json.load(open(GEOM))["per_symbol"]
    res = collections.defaultdict(lambda: collections.defaultdict(list))
    dcheck = collections.defaultdict(list)
    n_seen = n_walked = 0
    skips = collections.Counter()
    t0 = time.time()

    for month in MONTHS:
        z = np.load(EMIT / f"D8_EMIT_{month}.npz", allow_pickle=True)
        syms, fams = list(z["syms"]), list(z["fams"])
        sym_i, fam_i = z["sym"], z["fam"]
        idx, long, dbps, anchor, day = z["i"], z["long"], z["d_bps"], z["anchor"], z["day"]
        n_seen += len(idx)
        for si, sname in enumerate(syms):
            m = sym_i == si
            if not m.any():
                continue
            tp = tape(month, sname)
            if tp is None:
                skips[f"no_tape:{sname}:{month}"] += int(m.sum())
                continue
            hi, lo, cl, tstart = tp
            ii, ll, dd, aa, ff, dy = (idx[m], long[m], dbps[m].astype(float),
                                      anchor[m].astype(float), fam_i[m], day[m])
            dcheck[sname].extend(dd.tolist())
            spname = SPREAD_NAME.get(sname, sname)
            # spread once per (symbol, day) — the model's finest live axis is hour-of-week,
            # and a per-row call over 1.2 M rows buys nothing but time
            scache: dict[tuple, float] = {}
            for k in range(len(ii)):
                i = int(ii[k])
                if not (0 <= i < len(cl)):
                    skips["index_out_of_tape"] += 1
                    continue
                e = float(aa[k])
                d = e * float(dd[k]) / 1e4
                if not (d > 0) or not np.isfinite(e):
                    skips["bad_geometry"] += 1
                    continue
                L = bool(ll[k])
                sgn = 1.0 if L else -1.0
                at = tstart + dt.timedelta(minutes=i)
                ck = (spname, at.date(), at.hour)
                s = scache.get(ck)
                if s is None:
                    try:
                        s = spread_for(spname, at, account="FTMO", band="mid")
                    except SpreadUnavailable:
                        s = -1.0
                    scache[ck] = s
                if s < 0:
                    skips[f"no_spread:{spname}"] += 1
                    continue

                stop = e - sgn * d
                tgt = e + sgn * TARGET_R * d
                base = walk_levels(hi, lo, cl, i, L, e, stop, tgt)
                if base is None:
                    skips["no_path"] += 1
                    continue
                px, why = base
                r_old = sgn * (px - e) / d

                # LEVEL anchoring. The transacted entry is the LEVEL on both sides.
                #   LONG  — SL/TP are bid-quoted and the tape is the bid, so both legs
                #           resolve unshifted and R is unchanged. (The long's ENTRY does
                #           displace — it fills when the ask reaches the level, i.e. one
                #           spread early in tape terms — but this roster walks from the
                #           level unconditionally, so no fill question is posed. Stated as
                #           a limit rather than modelled.)
                #   SHORT — SL/TP are ask-quoted: they fire when tape >= S - s and
                #           tape <= T - s, and a path-end exit buys back at tape + s.
                if L:
                    r_lvl = r_old
                else:
                    r2 = walk_levels(hi, lo, cl, i, L, e, stop - s, tgt - s)
                    if r2 is None:
                        skips["no_path_level"] += 1
                        continue
                    p2, w2 = r2
                    if w2 == "stop":
                        r_lvl = -1.0
                    elif w2 == "target":
                        r_lvl = TARGET_R
                    else:
                        r_lvl = (e - (p2 + s)) / d

                # FILL anchoring: the symmetric form, for comparability with the live book
                ef = e + sgn * s
                r3 = walk_levels(hi, lo, cl, i, L, ef, ef - sgn * d,
                                 ef + sgn * TARGET_R * d)
                if r3 is None:
                    skips["no_path_fill"] += 1
                    continue
                r_fill = sgn * (r3[0] - ef) / d

                fam = fams[int(ff[k])]
                for scope in ("ALL", fam):
                    r = res[scope]
                    r["old"].append(r_old)
                    r["level"].append(r_lvl)
                    r["fill"].append(r_fill)
                    r["sd"].append(s / d)
                    r["reason_old"].append(why)
                n_walked += 1
        print(f"  {month} done  n_walked={n_walked}  {time.time()-t0:.0f}s", flush=True)

    # ---- control: median d_bps must reproduce d8x's per-symbol table
    ctl = {}
    worst = 0.0
    for sname, v in sorted(dcheck.items()):
        want = geom.get(sname, {}).get("median_d_bps")
        fin = [x for x in v if math.isfinite(x)]
        got = float(np.median(fin)) if fin else float("nan")
        ctl[sname] = {"d8x": want, "here": got,
                      "rel_err": (abs(got - want) / want if want else None),
                      "n_d8x": geom.get(sname, {}).get("n"), "n_here": len(v)}
        # a NaN must FAIL, not slip through max(); this control silently passed on
        # NaN in its first draft, which is the exact defect class this lane removes
        if not want or not math.isfinite(got):
            worst = float("inf")
        else:
            worst = max(worst, abs(got - want) / want)
    if not (worst <= 0.02):
        (HERE / "R1_BROAD_CONTROL_FAILURE.json").write_text(json.dumps(ctl, indent=1))
        print("CONTROL FAILED — roster/tape join disagrees with D8X_GEOM_V1", worst)
        return 2

    def summ(v):
        n = len(v)
        return ({"n": 0} if not n else
                {"n": n, "mean": round(statistics.fmean(v), 6),
                 "se": round(statistics.pstdev(v) / math.sqrt(n), 6) if n > 1 else None})

    table = {}
    for scope, a in sorted(res.items()):
        rc = collections.Counter(a["reason_old"])
        table[scope] = {
            "n": len(a["old"]),
            "gross_old": summ(a["old"]),
            "gross_level_anchored": summ(a["level"]),
            "gross_fill_anchored": summ(a["fill"]),
            "delta_level": summ([x - y for x, y in zip(a["level"], a["old"])]),
            "delta_fill": summ([x - y for x, y in zip(a["fill"], a["old"])]),
            "spread_over_risk_median": round(float(np.median(a["sd"])), 6),
            "exit_reasons_old": dict(sorted(rc.items())),
        }

    out = {
        "what": ("the broad V4 family re-walked on both quote conventions with the "
                 "canonical instrument"),
        "population": f"{n_seen} emissions declared, {n_walked} walked",
        "windows": list(MONTHS),
        "contract": {"target_r": TARGET_R, "horizon_m1_bars": HORIZON,
                     "tie": "stop wins", "path": "[i+1, i+horizon]"},
        "anchoring_note": ("LEVEL is the broad family's own geometry "
                           "(broader_origin_generators.py:1697-1712, zone_midpoint entry, "
                           "zone-edge stop); FILL is published for comparability with the "
                           "live book and with d8x's symmetric bound"),
        "spread_source": "src.costs.spread_model, era-aware, band=mid, per (symbol, day, hour)",
        "control_median_d_bps_vs_d8x": {"max_rel_err": worst, "per_symbol": ctl},
        "skips": dict(skips),
        "table": table,
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("WROTE", OUT)
    print(json.dumps(table["ALL"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
