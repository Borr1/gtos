"""Microstructure miner — the untested layer: VOLUME + liquidity events.

Every prior mine used price geometry only (trend/pos/vol-as-ATR-ratio) and
found no surviving edge. This miner adds the participation footprint that
"market-maker waves" actually live in, all from data already on disk
(tick_volume is in every bar):

  - rel_volume       = vol / SMA20(vol)               (participation surge)
  - vol_efficiency   = bar_range / vol                (absorption vs expansion)
  - vol_state        = surge / normal / dry
  - liquidity sweep  = wick beyond prior_high/low(20) + close back inside
                       on a volume surge  (stop-run / market-maker grab)
  - reclaim          = sweep followed by close re-entering the range

Discipline carried from the failures (this is the asset):
  - EPISODE semantics: only the first bar of a state run (entry-on-change).
  - Measured per-cell cost = spread_price / ATR (from live snapshot).
  - REGIME BASELINE subtracted: report edge OVER always-long AND always-short
    of the same asset class on the same bars — never mistake beta for alpha
    again.
  - TRAIN 2022..2025, VALIDATION 2026-01..04 evaluated once; 2026-05+ untouched.
  - BH(0.05) across all cells + out-of-time same-sign + edge-over-baseline gate.

Replay/proxy evidence; research-only; no broker calls.
"""
import csv, json, math, statistics, sys, collections
from pathlib import Path

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

SNAP = json.loads((ROUTE / "ULTIMATE_SYMBOL_SPREAD_SNAPSHOT.json").read_text())
D = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
HORIZONS = (3, 6, 12, 24)   # H4 bars: 0.5d .. 4d
STOP_ATR = 2.5
BH_Q = 0.05
MIN_EPISODES = 80


def price_state(closes, highs, lows, i, atr):
    m20 = sum(closes[i - 19:i + 1]) / 20
    m50 = sum(closes[i - 49:i + 1]) / 50
    trend = "up" if m20 > m50 * 1.001 else ("down" if m20 < m50 * 0.999 else "flat")
    hi, lo = max(highs[i - 47:i + 1]), min(lows[i - 47:i + 1])
    pos = (closes[i] - lo) / (hi - lo) if hi > lo else 0.5
    posb = "low" if pos < 0.25 else ("high" if pos > 0.75 else "mid")
    return trend, posb


def vol_state(vols, ranges, i):
    base = statistics.fmean(vols[i - 19:i + 1]) or 1.0
    rel = vols[i] / base
    vs = "surge" if rel >= 1.8 else ("dry" if rel <= 0.6 else "norm")
    eff = ranges[i] / vols[i] if vols[i] > 0 else 0.0
    base_eff = statistics.fmean([ranges[j] / vols[j] if vols[j] > 0 else 0.0
                                 for j in range(i - 19, i + 1)]) or 1e-9
    effb = "expansion" if eff >= base_eff * 1.4 else ("absorption" if eff <= base_eff * 0.6 else "norm")
    return vs, effb, rel


def main():
    train = collections.defaultdict(list)
    val = collections.defaultdict(list)
    base_long = collections.defaultdict(list)   # asset_class,horizon -> always-long net
    base_short = collections.defaultdict(list)
    n_eps = 0
    for f in sorted(D.glob("*_H4.csv")):
        symbol = f.name[:-7]
        ac = ASSET_CLASS_BY_SYMBOL.get(symbol)
        sp = float((SNAP.get(symbol) or {}).get("spread_price") or 0)
        if ac is None or sp <= 0:
            continue
        rows = [(str(r["time"])[:19], float(r["open"]), float(r["high"]),
                 float(r["low"]), float(r["close"]), float(r["volume"]))
                for r in csv.DictReader(open(f)) if r.get("close") and r.get("volume")]
        if len(rows) < 200:
            continue
        times = [r[0] for r in rows]; highs = [r[2] for r in rows]
        lows = [r[3] for r in rows]; closes = [r[4] for r in rows]; vols = [r[5] for r in rows]
        ranges = [highs[k] - lows[k] for k in range(len(rows))]
        trs = [0.0] * len(rows)
        for i in range(1, len(rows)):
            trs[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))

        def prior_high(i, n): return max(highs[i - n:i])
        def prior_low(i, n): return min(lows[i - n:i])

        def sim(i, atr, direction):
            stop = closes[i] - direction * STOP_ATR * atr
            for j in range(i + 1, i + maxh + 1):
                if direction > 0 and lows[j] <= stop: return -STOP_ATR - sp / atr
                if direction < 0 and highs[j] >= stop: return -STOP_ATR - sp / atr
            return direction * (closes[i + h] - closes[i]) / atr - sp / atr

        maxh = max(HORIZONS)
        prev = None
        for i in range(60, len(rows) - maxh):
            atr = sum(trs[i - 13:i + 1]) / 14
            if atr <= 0:
                continue
            month = times[i][:7]
            if month >= "2026-05":
                continue
            ps = price_state(closes, highs, lows, i, atr)
            vs, effb, rel = vol_state(vols, ranges, i)
            # liquidity sweep + reclaim (stop run): wick beyond prior extreme,
            # close back inside, on a volume surge -> market-maker grab.
            ph, pl = prior_high(i, 20), prior_low(i, 20)
            swept_high = highs[i] > ph and closes[i] < ph and rel >= 1.5
            swept_low = lows[i] < pl and closes[i] > pl and rel >= 1.5
            sweep = "sweep_high" if swept_high else ("sweep_low" if swept_low else "none")
            state = (ps[0], ps[1], vs, effb, sweep)
            is_entry = state != prev
            prev = state
            for h in HORIZONS:
                bucket = val if month >= "2026-01" else train
                # regime baselines on EVERY maxh-th bar (unconditional exposure)
                if i % maxh == 0:
                    (val if month >= "2026-01" else train)  # noqa
                    base_long[(ac, h)].append(sim(i, atr, +1))
                    base_short[(ac, h)].append(sim(i, atr, -1))
                if not is_entry:
                    continue
                # directional hypothesis per setup:
                #  sweep_low -> long (grab below, reclaim up); sweep_high -> short
                #  else reversion at extremes: pos=low long, pos=high short
                if sweep == "sweep_low":
                    d = +1
                elif sweep == "sweep_high":
                    d = -1
                elif ps[1] == "low":
                    d = +1
                elif ps[1] == "high":
                    d = -1
                else:
                    continue
                cell = (ac, *state, h, "long" if d > 0 else "short")
                bucket[cell].append(sim(i, atr, d))
            n_eps += 1

    # baselines (pooled across train+val for a stable beta estimate per ac,h,dir)
    bl = {k: statistics.fmean(v) for k, v in base_long.items() if v}
    bs = {k: statistics.fmean(v) for k, v in base_short.items() if v}

    tested = []
    for cell, vals_t in train.items():
        if len(vals_t) < MIN_EPISODES:
            continue
        m, sd = statistics.fmean(vals_t), statistics.pstdev(vals_t)
        if sd <= 0:
            continue
        ac, h, direction = cell[0], cell[-2], cell[-1]
        beta = bl.get((ac, h), 0.0) if direction == "long" else bs.get((ac, h), 0.0)
        edge = m - beta
        t = m / (sd / math.sqrt(len(vals_t)))
        edge_t = edge / (sd / math.sqrt(len(vals_t)))
        p = 2 * (1 - 0.5 * (1 + math.erf(abs(edge_t) / math.sqrt(2))))
        tested.append({"cell": list(cell), "n": len(vals_t), "raw_mean_r": round(m, 4),
                       "beta_baseline_r": round(beta, 4), "edge_over_beta_r": round(edge, 4),
                       "edge_t": round(edge_t, 2), "p_edge": p})

    tested.sort(key=lambda r: r["p_edge"])
    mt = len(tested); mk = 0
    for k, r in enumerate(tested, 1):
        if r["p_edge"] <= BH_Q * k / mt:
            mk = k
    surv = tested[:mk]
    conf = []
    for r in surv:
        v = val.get(tuple(r["cell"]), [])
        if len(v) >= 10:
            ac, h, direction = r["cell"][0], r["cell"][-2], r["cell"][-1]
            beta = bl.get((ac, h), 0.0) if direction == "long" else bs.get((ac, h), 0.0)
            vedge = statistics.fmean(v) - beta
            conf.append({**r, "val_n": len(v), "val_edge_over_beta_r": round(vedge, 4),
                         "same_sign": (vedge > 0) == (r["edge_over_beta_r"] > 0)})

    out = {"schema_version": "ultimate_microstructure_mine_v1", "episodes": n_eps,
           "cells_tested": mt, "bh_survivors": len(surv),
           "confirmed_edge_same_sign": sum(1 for c in conf if c["same_sign"]),
           "confirm_evaluable": len(conf),
           "top_by_edge": sorted(surv, key=lambda r: -r["edge_over_beta_r"])[:30],
           "confirmations": sorted(conf, key=lambda r: -r["val_edge_over_beta_r"])[:40],
           "broker_operation": False, "paid_api_or_vendor_call": False,
           "broker_runtime_change_status": False, "validation_result_status": False,
           "outcome_result_rows_status": False}
    (ROUTE / "ULTIMATE_MICROSTRUCTURE_MINE_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps({k: out[k] for k in ("episodes", "cells_tested", "bh_survivors",
                                          "confirmed_edge_same_sign", "confirm_evaluable")}, sort_keys=True))
    for c in out["confirmations"][:10]:
        print(f"  {c['cell']}  edge {c['edge_over_beta_r']:+.3f}R (t={c['edge_t']}) val {c['val_edge_over_beta_r']:+.3f}R n={c['n']}/{c['val_n']}")


if __name__ == "__main__":
    main()
