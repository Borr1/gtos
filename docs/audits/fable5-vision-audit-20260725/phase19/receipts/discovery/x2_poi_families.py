#!/usr/bin/env python3
"""x2 step 4 - the three current_* POI families: when was the setup first detectable?

Zones (broader_origin_generators.py):
  current_fvg_fill        M15 fair_value_gaps, zone=(bottom,top)     :1157-1168
  current_ob_retest       H1  order_blocks,    zone=(low,high)       :1382-1391
  current_breaker_re_entry H1 breaker_blocks,  zone=(zone_low,zone_high) :1436-1446
Geometry (_current_framework_geometry:1616-1629):
  entry = zone midpoint ; stop = zone_low - b*atr14 (LONG) | zone_high + b*atr14 (SHORT)
  b = risk.sl_buffer_atr_multiplier = 0.25 (fvg, breaker) | gate1.ob_retest_sl_min_buffer_atr = 0.5 (ob)
  atr14 = MSO M15 Wilder ATR-14  [CALIBRATED EXACT: max rel err 8.3e-12 vs 6,879 exactly
  reconstructed FVG zones]
  => half_width = risk_distance - b*atr14 ; zone = (entry-half, entry+half)
The ONLY bar-dependent gate is proximity (_zone_proximity_pct:1711-1717):
  gap = 0 if inside zone else min(|p-lo|,|p-hi|);  fire iff gap/p <= poi_proximity_tolerance_pct
  = 0.01  (config/agent_config.yaml:4032)

Writes DISCOVERY/x2_POI_DETECTABILITY_V1.jsonl.gz
"""
import sys, os, json, gzip, collections, datetime as dt
import numpy as np
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x2_bars, w0_ws

TOL = 0.01
BUF = {"current_fvg_fill": 0.25, "current_ob_retest": 0.5, "current_breaker_re_entry": 0.25}
BACK_MIN = 4320          # 3 days of M1 back-scan; longer is censored


def wilder(bars, end, period=14):
    c = bars[max(0, end - 399):end + 1]
    if len(c) < 2:
        return 0.0
    tr = [max(c[i][2] - c[i][3], abs(c[i][2] - c[i - 1][4]), abs(c[i][3] - c[i - 1][4]))
          for i in range(1, len(c))]
    if len(tr) < period:
        return sum(tr) / len(tr)
    a = sum(tr[:period]) / period
    for i in range(period, len(tr)):
        a = (a * (period - 1) + tr[i]) / period
    return a


def main():
    rows = [r for r in w0_ws.load() if r["origin_family"] in BUF]
    fvgz = {}
    with gzip.open(os.path.join(D, "x2_FVG_ZONES_V1.jsonl.gz"), "rt") as fh:
        for l in fh:
            z = json.loads(l)
            if z.get("matched"):
                fvgz[tuple(z["key"])] = z
    bysym = collections.defaultdict(list)
    for r in rows:
        bysym[r["symbol"]].append(r)
    out = []; stats = collections.Counter()
    for sym, rs in sorted(bysym.items()):
        m15 = x2_bars.load_m15(sym)
        m15idx = {b[0]: i for i, b in enumerate(m15)}
        m1 = x2_bars.load_m1(sym, ("202512", "202601"))
        t1 = {b[0]: k for k, b in enumerate(m1)}
        hi = np.array([b[2] for b in m1]); lo = np.array([b[3] for b in m1]); cl = np.array([b[4] for b in m1])
        for r in rs:
            fam = r["origin_family"]
            bt = dt.datetime.fromisoformat(r["decision_time_utc"]) - dt.timedelta(minutes=15)
            di = m15idx.get(bt)
            if di is None:
                stats["no_decision_bar"] += 1; continue
            a14 = wilder(m15, di)
            half = r["risk_distance"] - BUF[fam] * a14
            if half <= 0:
                stats["bad_half"] += 1; continue
            zlo, zhi = r["entry_price"] - half, r["entry_price"] + half
            k = t1.get(bt)
            if k is None:
                stats["no_m1_at_bar"] += 1; continue
            # --- (1) proximity inside the decision bar, per minute
            first_in_bar = None; n_in_bar = 0
            for off in range(15):
                j = t1.get(bt + dt.timedelta(minutes=off))
                if j is None:
                    continue
                p = cl[j]
                gap = 0.0 if zlo <= p <= zhi else min(abs(p - zlo), abs(p - zhi))
                if p > 0 and gap / p <= TOL:
                    n_in_bar += 1
                    if first_in_bar is None:
                        first_in_bar = off
            # --- (2) backward run of continuous proximity before the bar opened
            s = max(0, k - BACK_MIN)
            seg = cl[s:k]
            if seg.size:
                gapv = np.where((seg >= zlo) & (seg <= zhi), 0.0,
                                np.minimum(np.abs(seg - zlo), np.abs(seg - zhi)))
                ok = (gapv / seg) <= TOL
                bad = np.nonzero(~ok)[0]
                run = (seg.size - 1 - bad[-1]) if bad.size else seg.size
                censored = bool(not bad.size)
            else:
                run = 0; censored = False
            # floor from FVG formation (exact); H1 zones have no M15-visible formation bar
            zage = None; zform = None
            zz = fvgz.get(w0_ws.key(r))
            if zz is not None:
                zage = zz["age_bars"]; zform = zz["conf_bar_time"]
            # --- (3) did the entry LIMIT trade before the decision, inside the detectable window?
            s2 = k - int(run)
            touched_before = False; touch_minutes_before = None
            if run > 0:
                hh = hi[s2:k]; ll = lo[s2:k]
                t = np.nonzero((ll <= r["entry_price"]) & (hh >= r["entry_price"]))[0]
                if t.size:
                    touched_before = True
                    touch_minutes_before = int(k - (s2 + t[-1]))
            rec = {"key": list(w0_ws.key(r)), "symbol": sym, "family": fam, "side": r["side"],
                   "bar_time": bt.isoformat(), "entry_price": r["entry_price"],
                   "half_width": half, "zone_low": zlo, "zone_high": zhi, "atr14": a14,
                   "prox_first_off_in_bar": first_in_bar, "prox_minutes_in_bar": n_in_bar,
                   "prox_back_run_minutes": int(run), "prox_back_censored": censored,
                   "fvg_zone_age_m15_bars": zage, "fvg_formation_bar": zform,
                   "entry_touched_before_decision": touched_before,
                   "entry_touch_minutes_before": touch_minutes_before,
                   "gross_r": r["gross_r"], "plain_walk_r": r["plain_walk_r"],
                   "fill_honest_walk_r": r["fill_honest_walk_r"],
                   "which_came_first": r["which_came_first"],
                   "bars_to_entry_touch": r["bars_to_entry_touch"],
                   "entry_touched_after": r["entry_touched"]}
            out.append(rec); stats["rows"] += 1
        print("done", sym, stats["rows"], flush=True)
    with gzip.open(os.path.join(D, "x2_POI_DETECTABILITY_V1.jsonl.gz"), "wt") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    print(json.dumps(dict(stats), indent=1))


if __name__ == "__main__":
    main()
