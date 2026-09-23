"""m3-3 — does the exit-contract ordering survive a correction larger than itself?

    python3 .../m3/m3_exit_contract.py

THE QUESTION, STATED PRECISELY
------------------------------
Wave 19's one transferable asset is an ORDERING, not a level: swapping the shipped
`target_2.0R` for `stop_only_horizon` is worth **+0.03500 R/trade** pooled over eight open
windows, 8/8 positive, with **zero cost content** (`d2_RESULT.json ->
DEPLOYABLE_DELTAS.exit_2R_to_stop_only_horizon_full_pop`; `p1 §5.1`). Out of sample it
shrank to **+0.01002** and failed its own +0.02 bar (`p2` H3).

Lane r1 then measured that the walker those numbers came from was on the wrong side of the
book, by **−0.0696 to −0.1160 R/fill** on this family — 2x to 3.3x the effect. Wave 19's own
owner report drew the conclusion that the lever is "below the walker-bias floor".

**That conclusion does not follow, and this file measures whether it is true.** A paired
difference between two exit contracts on the SAME rows is not a level: any component of the
bias common to both contracts cancels exactly. The bias is common wherever the two contracts
resolve the same way, which is every row on which `target_2.0R` never reaches its target.
What does NOT cancel is the target-crossing subpopulation — and that is precisely where a
one-spread displacement changes an outcome. So the delta is neither invariant nor doomed;
it is an empirical question with a measurable answer.

METHOD
------
The same roster, tape, spread model and walker lane r1 used
(`r1_broad_rewalk.py`), extended to walk BOTH contracts in one pass:

    target_2.0R          stop at -1d, target at +2d, path end at horizon
    stop_only_horizon    stop at -1d, NO target,     path end at horizon

on three anchorings:

    old      the published convention — every level unshifted on a BID tape
    level    the broad family's own geometry (structural levels), quote-corrected
    fill     the live book's convention (cross, then hang both legs off the fill)

Nothing is sampled: all 1,211,077 emissions of the eight open windows. The sealed three are
not opened.

CONTROLS
--------
C1  `median_d_bps` per symbol must reproduce `D8X_GEOM_V1.json` (r1's own control).
C2  the `old` arm's per-month `target_2.0R -> stop_only_horizon` delta must carry d2's sign
    in all eight months. It is a DIFFERENT roster read from d2's AT_MARKET cohort
    (1.13 M walked vs 141,230), so the magnitudes are not required to match and are
    published side by side rather than asserted equal.
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
D2 = DISC / "d2_RESULT.json"
M1 = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
          "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
OUT = HERE / "M3_EXIT_CONTRACT_V1.json"

MONTHS = ("202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605")
TARGET_R = 2.0
HORIZON = 240

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


def walk_levels(hi, lo, cl, i, long, stop, tgt, horizon=HORIZON):
    """r1's walker verbatim; `tgt=None` is the stop-only contract."""
    a, b = i + 1, min(i + 1 + horizon, len(cl))
    if a >= b:
        return None
    h, l, c = hi[a:b], lo[a:b], cl[a:b]
    ok = ~np.isnan(c)
    if not ok.any():
        return None
    h, l, c = h[ok], l[ok], c[ok]
    hs = (l <= stop) if long else (h >= stop)
    iss = int(np.argmax(hs)) if hs.any() else None
    if tgt is None:
        if iss is not None:
            return stop, "stop"
        return float(c[-1]), "path_end"
    ht = (h >= tgt) if long else (l <= tgt)
    it = int(np.argmax(ht)) if ht.any() else None
    if iss is not None and (it is None or iss <= it):
        return stop, "stop"
    if it is not None:
        return tgt, "target"
    return float(c[-1]), "path_end"


def summ(v):
    n = len(v)
    return ({"n": 0} if not n else
            {"n": n, "mean": round(statistics.fmean(v), 6),
             "se": round(statistics.pstdev(v) / math.sqrt(n), 6) if n > 1 else None})


def dayboot(pairs, draws=20000, seed=20260807):
    """Day-block bootstrap on a paired per-row delta. `pairs` = list[(day, delta)]."""
    by = collections.defaultdict(list)
    for d, x in pairs:
        by[d].append(x)
    days = sorted(by)
    sums = np.array([math.fsum(by[d]) for d in days])
    cnts = np.array([len(by[d]) for d in days], dtype=float)
    if not len(days):
        return {}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(days), size=(draws, len(days)))
    m = sums[idx].sum(1) / cnts[idx].sum(1)
    return {"mean": round(float(sums.sum() / cnts.sum()), 6),
            "ci95_lo": round(float(np.percentile(m, 2.5)), 6),
            "ci95_hi": round(float(np.percentile(m, 97.5)), 6),
            "p_le_0": round(float((m <= 0).mean()), 5),
            "n_days": len(days)}


def main() -> int:
    geom = json.load(open(GEOM))["per_symbol"]
    d2 = json.load(open(D2))["DEPLOYABLE_DELTAS"]
    ARMS = ("old", "level", "fill")
    # per arm -> per contract -> list of R; plus paired deltas per (arm, month)
    R = {a: {"t2": [], "so": []} for a in ARMS}
    reason = {a: {"t2": collections.Counter(), "so": collections.Counter()} for a in ARMS}
    per_month = {m: {a: {"t2": [], "so": []} for a in ARMS} for m in MONTHS}
    pair_days = {a: [] for a in ARMS}
    dcheck = collections.defaultdict(list)
    n_seen = n_walked = 0
    skips = collections.Counter()
    t0 = time.time()

    for month in MONTHS:
        z = np.load(EMIT / f"D8_EMIT_{month}.npz", allow_pickle=True)
        syms = list(z["syms"])
        sym_i = z["sym"]
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
            ii, ll, dd, aa, dy = (idx[m], long[m], dbps[m].astype(float),
                                  anchor[m].astype(float), day[m])
            dcheck[sname].extend(dd.tolist())
            spname = SPREAD_NAME.get(sname, sname)
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
                # --- old: both contracts on unshifted levels ------------------------
                a2 = walk_levels(hi, lo, cl, i, L, stop, tgt)
                a1 = walk_levels(hi, lo, cl, i, L, stop, None)
                if a2 is None or a1 is None:
                    skips["no_path"] += 1
                    continue
                r_old_t2 = sgn * (a2[0] - e) / d
                r_old_so = sgn * (a1[0] - e) / d

                # --- level anchoring: the broad family's structural levels ----------
                # LONG  — exits bid-quoted, tape IS the bid: unshifted, R unchanged.
                # SHORT — exits ask-quoted: fire at tape >= S-s / <= T-s, buy back +s.
                if L:
                    r_lvl_t2, r_lvl_so = r_old_t2, r_old_so
                    w_lvl_t2, w_lvl_so = a2[1], a1[1]
                else:
                    b2 = walk_levels(hi, lo, cl, i, L, stop - s, tgt - s)
                    b1 = walk_levels(hi, lo, cl, i, L, stop - s, None)
                    if b2 is None or b1 is None:
                        skips["no_path_level"] += 1
                        continue
                    w_lvl_t2, w_lvl_so = b2[1], b1[1]
                    r_lvl_t2 = (-1.0 if w_lvl_t2 == "stop" else
                                TARGET_R if w_lvl_t2 == "target" else (e - (b2[0] + s)) / d)
                    r_lvl_so = (-1.0 if w_lvl_so == "stop" else (e - (b1[0] + s)) / d)

                # --- fill anchoring: the live book's convention ----------------------
                ef = e + sgn * s
                c2 = walk_levels(hi, lo, cl, i, L, ef - sgn * d, ef + sgn * TARGET_R * d)
                c1 = walk_levels(hi, lo, cl, i, L, ef - sgn * d, None)
                if c2 is None or c1 is None:
                    skips["no_path_fill"] += 1
                    continue
                r_fil_t2 = sgn * (c2[0] - ef) / d
                r_fil_so = sgn * (c1[0] - ef) / d

                dstr = str(dy[k])
                for arm, (rt, rs, wt, ws) in (
                        ("old", (r_old_t2, r_old_so, a2[1], a1[1])),
                        ("level", (r_lvl_t2, r_lvl_so, w_lvl_t2, w_lvl_so)),
                        ("fill", (r_fil_t2, r_fil_so, c2[1], c1[1]))):
                    R[arm]["t2"].append(rt)
                    R[arm]["so"].append(rs)
                    reason[arm]["t2"][wt] += 1
                    reason[arm]["so"][ws] += 1
                    per_month[month][arm]["t2"].append(rt)
                    per_month[month][arm]["so"].append(rs)
                    pair_days[arm].append((dstr, rs - rt))
                n_walked += 1
        print(f"  {month} done  n_walked={n_walked}  {time.time()-t0:.0f}s", flush=True)

    # ---- C1 -------------------------------------------------------------------------
    ctl, worst = {}, 0.0
    for sname, v in sorted(dcheck.items()):
        want = geom.get(sname, {}).get("median_d_bps")
        fin = [x for x in v if math.isfinite(x)]
        got = float(np.median(fin)) if fin else float("nan")
        ctl[sname] = {"d8x": want, "here": got}
        if not want or not math.isfinite(got):
            worst = float("inf")
        else:
            worst = max(worst, abs(got - want) / want)
    if not (worst <= 0.02):
        print("CONTROL C1 FAILED", worst)
        (HERE / "M3_EXIT_CONTROL_FAILURE.json").write_text(json.dumps(ctl, indent=1))
        return 2

    table = {}
    for arm in ARMS:
        dl = [b - a for a, b in zip(R[arm]["t2"], R[arm]["so"])]
        table[arm] = {
            "target_2.0R": summ(R[arm]["t2"]),
            "stop_only_horizon": summ(R[arm]["so"]),
            "paired_delta": summ(dl),
            "paired_delta_dayblock": dayboot(pair_days[arm]),
            "frac_rows_delta_nonzero": round(
                sum(1 for x in dl if abs(x) > 1e-12) / len(dl), 6) if dl else None,
            "exit_reasons_target_2.0R": dict(sorted(reason[arm]["t2"].items())),
            "exit_reasons_stop_only": dict(sorted(reason[arm]["so"].items())),
        }
    months_tbl = {}
    for mth in MONTHS:
        months_tbl[mth] = {}
        for arm in ARMS:
            t2 = per_month[mth][arm]["t2"]
            so = per_month[mth][arm]["so"]
            months_tbl[mth][arm] = {
                "n": len(t2),
                "target_2.0R": round(statistics.fmean(t2), 6) if t2 else None,
                "stop_only_horizon": round(statistics.fmean(so), 6) if so else None,
                "delta": round(statistics.fmean([b - a for a, b in zip(t2, so)]), 6) if t2 else None,
            }
        months_tbl[mth]["d2_published_delta_net"] = (
            d2["exit_per_month"].get(mth, {}).get("delta"))

    c2 = {"months_positive_here_old": sum(
        1 for mth in MONTHS if (months_tbl[mth]["old"]["delta"] or 0) > 0),
        "months_positive_d2": sum(
            1 for mth in MONTHS if (d2["exit_per_month"].get(mth, {}).get("delta") or 0) > 0),
        "d2_full_pop": d2["exit_2R_to_stop_only_horizon_full_pop"],
        "note": ("d2's roster is the PB AT_MARKET cohort (n 141,230, 172 days); this is the "
                 "d8 emission roster (n {:,} walked). The SIGN and the 8/8 persistence are "
                 "the comparable claims; the magnitudes are not required to "
                 "match.".format(n_walked))}

    out = {
        "what": ("does the exit-contract ORDERING survive the quote-side correction — "
                 "target_2.0R vs stop_only_horizon, paired, on three anchorings"),
        "population": f"{n_seen} emissions declared, {n_walked} walked",
        "windows": list(MONTHS),
        "contract": {"target_r": TARGET_R, "horizon_m1_bars": HORIZON, "tie": "stop wins"},
        "spread_source": "src.costs.spread_model, era-aware, band=mid, per (symbol, day, hour)",
        "cost_note": ("the exit swap carries ZERO cost content — p1 §5.1 measured the cost "
                      "delta at exactly 0.00000 in all eight months — so a GROSS comparison "
                      "is the whole comparison here"),
        "control_C1_median_d_bps_max_rel_err": worst,
        "control_C2_vs_d2": c2,
        "skips": dict(skips),
        "table": table,
        "per_month": months_tbl,
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("WROTE", OUT)
    print(json.dumps({a: {"paired_delta": table[a]["paired_delta"],
                          "dayblock": table[a]["paired_delta_dayblock"]} for a in ARMS},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
