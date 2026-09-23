"""w0-capture step 4: does FILL TIMING explain the walk-vs-record gap?

Step 1 showed a naive walker (fill at decision, 2R/-1R bracket, 120-minute
horizon) reproduces the sealed ``opportunity_net_proxy_r`` on 80.1 % of rows and
is 0.258 R/trade MORE favourable overall.  Step 3 showed the momentum_exhaustion
policy is NOT the cause (it reconciles worse, 57.6 %).

This step tests the remaining structural candidate: the engine fills a PENDING
LIMIT when the path touches it, so favourable excursion between decision and fill
belongs to nobody.  Arms:

  A  fill_at_decision      -- naive (step 1)
  B  fill_on_first_touch   -- limit fills at the first bar whose range covers
                              entry_price; walk starts at that bar
  C  fill_on_first_touch_next_bar -- as B but the outcome walk starts at the bar
                              AFTER the fill bar (no same-bar fill+resolve)

Each arm is scored with the same 2R/-1R bracket, conservative same-bar rule,
120-minute horizon, mark-to-market at the wall.
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import gzip
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
LANE_ROOT = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence"
    "/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
M1_DIR = LANE_ROOT / "sources/bars/bridge_ftmo_m1_202601"
MANIFEST = LANE_ROOT / "manifests/january_2026.json"
POOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools"
    / "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
HORIZONS = [120, 1440, 14400]


def eus(w: dt.datetime) -> int:
    return int(w.timestamp() * 1_000_000)


def load_m1():
    man = json.loads(MANIFEST.read_text())
    want = {
        str(r.get("mapped_symbol") or r.get("symbol")): int(r.get("row_count") or 0)
        for r in (man.get("bar_sources") or [])
        if r.get("timeframe") == "M1" and r.get("source_family") == "bridge_ftmo_m1_202601"
    }
    out = {}
    for sym, rows in sorted(want.items()):
        t, o, h, l, c = [], [], [], [], []
        with (M1_DIR / f"{sym}_M1.csv").open("r", encoding="utf-8") as fh:
            rd = csv.reader(fh)
            next(rd)
            for r in rd:
                t.append(eus(dt.datetime.fromisoformat(r[0])))
                o.append(float(r[1])); h.append(float(r[2])); l.append(float(r[3])); c.append(float(r[4]))
        assert len(t) == rows
        out[sym] = (np.asarray(t, np.int64), np.asarray(o), np.asarray(h), np.asarray(l), np.asarray(c))
    return out


def bracket(hr, lr, cr, target, start):
    """2R/-1R bracket, conservative same-bar, mark at last bar. Returns (r, code, mfe, tgt_i, stop_i)."""
    n = len(hr)
    if start >= n:
        return None, 0, np.nan, -1, -1
    f = hr[start:]
    a = lr[start:]
    rf = np.maximum.accumulate(f)
    ra = np.maximum.accumulate(-a)
    it = int(np.searchsorted(rf, target - 1e-9, side="left"))
    iss = int(np.searchsorted(ra, 1.0 - 1e-9, side="left"))
    m = len(f)
    it = it if it < m else -1
    iss = iss if iss < m else -1
    mfe = float(rf[-1])
    if it >= 0 and (iss < 0 or it < iss):
        return float(target), 1, mfe, it, iss
    if iss >= 0 and (it < 0 or iss < it):
        return -1.0, 2, mfe, it, iss
    if it >= 0 and iss >= 0 and it == iss:
        return -1.0, 4, mfe, it, iss
    return float(max(-1.0, min(cr[-1], target))), 3, mfe, it, iss


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("W0_CAPTURE_FILL_V1.json"))
    args = ap.parse_args()
    series = load_m1()
    pool = []
    with gzip.open(POOL, "rt") as fh:
        for line in fh:
            pool.append(json.loads(line))
    n = len(pool)

    gross_rec = np.full(n, np.nan)
    cost = np.full(n, np.nan)
    fam = np.empty(n, dtype=object)
    fillcls = np.empty(n, dtype=object)
    arms = ["fill_at_decision", "fill_on_first_touch", "fill_on_first_touch_next_bar"]
    R = {a: {h: np.full(n, np.nan) for h in HORIZONS} for a in arms}
    C = {a: {h: np.zeros(n, np.int8) for h in HORIZONS} for a in arms}
    fill_bar = np.full(n, -1, np.int32)
    fill_min = np.full(n, np.nan)
    marketable_at_decision = np.zeros(n, bool)

    for i, r in enumerate(pool):
        fam[i] = r.get("origin_family")
        fillcls[i] = r.get("fill_realism_class")
        if r.get("cost_r") is not None:
            cost[i] = float(r["cost_r"])
            if r.get("opportunity_net_proxy_r") is not None:
                gross_rec[i] = float(r["opportunity_net_proxy_r"]) + float(r["cost_r"])
        t, o, h, l, c = series[r["symbol"]]
        entry = float(r["entry_price"]); stop = float(r["stop_loss"])
        side = str(r["side"]).upper()
        risk = abs(entry - stop)
        d = eus(dt.datetime.fromisoformat(r["decision_time_utc"]))
        s0 = int(np.searchsorted(t, d, side="right"))
        for hmin in HORIZONS:
            e = int(np.searchsorted(t, d + hmin * 60_000_000, side="right"))
            if s0 >= e or risk <= 0:
                continue
            hh = h[s0:e]; ll = l[s0:e]; cc = c[s0:e]
            if side == "LONG":
                hr = (hh - entry) / risk; lr = (ll - entry) / risk; cr = (cc - entry) / risk
            else:
                hr = (entry - ll) / risk; lr = (entry - hh) / risk; cr = (entry - cc) / risk
            # first bar whose range covers the limit price -> fill
            touch = np.nonzero((ll <= entry) & (hh >= entry))[0]
            fi = int(touch[0]) if len(touch) else -1
            if hmin == HORIZONS[0]:
                fill_bar[i] = fi
                if fi >= 0:
                    fill_min[i] = (t[s0 + fi] - d) / 60_000_000
                # already through the limit on the first bar?
                marketable_at_decision[i] = bool(
                    (side == "LONG" and hh[0] >= entry) or (side == "SHORT" and ll[0] <= entry)
                )
            v, code, _mfe, _a, _b = bracket(hr, lr, cr, 2.0, 0)
            R["fill_at_decision"][hmin][i] = np.nan if v is None else v
            C["fill_at_decision"][hmin][i] = code
            if fi >= 0:
                v, code, _mfe, _a, _b = bracket(hr, lr, cr, 2.0, fi)
                R["fill_on_first_touch"][hmin][i] = np.nan if v is None else v
                C["fill_on_first_touch"][hmin][i] = code
                v, code, _mfe, _a, _b = bracket(hr, lr, cr, 2.0, fi + 1)
                R["fill_on_first_touch_next_bar"][hmin][i] = np.nan if v is None else v
                C["fill_on_first_touch_next_bar"][hmin][i] = code

    ok = np.isfinite(gross_rec)
    res = {
        "schema": "gtos-w0-capture-fill-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "billed": False,
        "n": n,
        "fill_diagnostics": {
            "rows_with_limit_touch_within_120m": int((fill_bar >= 0).sum()),
            "rows_without_touch_within_120m": int((fill_bar < 0).sum()),
            "marketable_on_first_bar_after_decision": int(marketable_at_decision.sum()),
            "fill_delay_minutes": {
                "mean": float(np.nanmean(fill_min)),
                "p50": float(np.nanpercentile(fill_min, 50)),
                "p90": float(np.nanpercentile(fill_min, 90)),
                "share_fill_bar_0": float(np.mean(fill_bar == 0)),
            },
            "pool_fill_realism_class": dict(collections.Counter(str(x) for x in fillcls)),
        },
    }

    recs = []
    for a in arms:
        v = R[a][120]
        m = ok & np.isfinite(v)
        d = v - gross_rec
        recs.append(
            {
                "arm": a,
                "n_scored": int(m.sum()),
                "match_within_0p02R": int((m & (np.abs(d) <= 0.02)).sum()),
                "match_share": float((m & (np.abs(d) <= 0.02)).sum() / max(1, m.sum())),
                "mean_abs_diff_R": float(np.nanmean(np.abs(d[m]))),
                "mean_signed_diff_R": float(np.nanmean(d[m])),
                "gross_mean_R_120m": float(np.nanmean(v[m])),
                "gross_mean_R_1d": float(np.nanmean(R[a][1440][m])),
                "gross_mean_R_10d": float(np.nanmean(R[a][14400][m])),
                "recorded_gross_mean_R_same_rows": float(np.nanmean(gross_rec[m])),
                "win_rate_120m": float(np.mean(v[m] > 0)),
                "net_frozen_cost_120m_R": float(np.nanmean(v[m] - cost[m])),
            }
        )
    res["arms"] = recs

    # per-family, best-reconciling arm
    best = max(recs, key=lambda r: r["match_share"])["arm"]
    res["best_reconciling_arm"] = best
    v = R[best][120]
    m = ok & np.isfinite(v)
    fam_rows = []
    for f in sorted({str(x) for x in fam}):
        mm = m & (fam == f)
        if mm.sum() == 0:
            continue
        fam_rows.append(
            {
                "family": f,
                "n": int(mm.sum()),
                "recorded_gross_mean_R": float(np.nanmean(gross_rec[mm])),
                "walk_gross_mean_R_120m": float(np.nanmean(v[mm])),
                "walk_gross_mean_R_1d": float(np.nanmean(R[best][1440][mm])),
                "walk_gross_mean_R_10d": float(np.nanmean(R[best][14400][mm])),
                "gap_walk_minus_recorded_R": float(np.nanmean(v[mm] - gross_rec[mm])),
                "match_share": float(np.mean(np.abs(v[mm] - gross_rec[mm]) <= 0.02)),
                "mean_cost_R": float(np.nanmean(cost[mm])),
                "walk_net_frozen_120m_R": float(np.nanmean(v[mm] - cost[mm])),
            }
        )
    fam_rows.sort(key=lambda r: -r["gap_walk_minus_recorded_R"] * r["n"])
    res["per_family_best_arm"] = fam_rows

    # residual discrepancy under the best arm, by fill class
    d = v - gross_rec
    disc = m & (d > 0.02)
    byfc = collections.Counter()
    for i in np.nonzero(m)[0]:
        byfc[(str(fillcls[i]), bool(disc[i]))] += 1
    res["residual_discrepancy_by_fill_realism_class"] = [
        {"fill_realism_class": k[0], "discrepant": k[1], "n": v2} for k, v2 in byfc.most_common(20)
    ]
    res["residual_discrepancy_totals"] = {
        "n_discrepant": int(disc.sum()),
        "share": float(disc.sum() / max(1, m.sum())),
        "R_total": float(np.nansum(d[disc])),
        "R_per_pool_trade": float(np.nansum(d[disc]) / max(1, m.sum())),
    }

    args.out.write_text(json.dumps(res, indent=1, sort_keys=True))
    print(json.dumps(res["fill_diagnostics"], indent=1))
    print("\narm                             scored  match%   meanAbs  gross120  gross1d  gross10d  recorded  win  netFroz")
    for r in recs:
        print(
            f"{r['arm']:<30} {r['n_scored']:>6} {r['match_share']:.4f} {r['mean_abs_diff_R']:8.4f} "
            f"{r['gross_mean_R_120m']:+.4f} {r['gross_mean_R_1d']:+.4f} {r['gross_mean_R_10d']:+.4f} "
            f"{r['recorded_gross_mean_R_same_rows']:+.4f} {r['win_rate_120m']:.3f} {r['net_frozen_cost_120m_R']:+.4f}"
        )
    print(f"\nbest reconciling arm = {best}")
    print("\nper family (best arm):")
    for r in fam_rows:
        print(
            f"{r['family']:<32} n={r['n']:>5} match={r['match_share']:.3f} rec={r['recorded_gross_mean_R']:+.4f} "
            f"walk120={r['walk_gross_mean_R_120m']:+.4f} walk1d={r['walk_gross_mean_R_1d']:+.4f} "
            f"walk10d={r['walk_gross_mean_R_10d']:+.4f} gap={r['gap_walk_minus_recorded_R']:+.4f} "
            f"netFroz={r['walk_net_frozen_120m_R']:+.4f}"
        )
    print("\nresidual:", json.dumps(res["residual_discrepancy_totals"], indent=1))
    for r in res["residual_discrepancy_by_fill_realism_class"]:
        print("  ", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
