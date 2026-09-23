"""Origin-discovery miner: conditional forward-return mining over raw M15 bars.

The generation-layer pivot (2026-06-12 branch verdict): instead of testing
hand-designed setups, scan every M15 bar-close decision point across the
46-symbol year for feature-state cells with significant forward drift.

Method (honesty-first):
- State vector per bar-close from closed bars only (trend state, ATR regime,
  range position, compression, session hour-block, asset class).
- Forward return over H in {4, 8, 16, 32} M15 bars, ATR-normalized, minus a
  per-symbol spread proxy (cost-aware effect sizes).
- Cells = (feature_a-state x feature_b-state x horizon x asset_class).
- TRAIN days only (partition registry; SEALED excluded by construction).
- Day-clustered t-statistics (per symbol-day means -> t across days) so
  overlapping forward windows cannot inflate significance.
- Benjamini-Hochberg at Q=0.05 across ALL cells + effect floor; survivors are
  PRE-REGISTERED hypotheses for a single out-of-time confirmation pass.

Replay/proxy evidence; no broker calls; research-only.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.learned_edge_dataset_builder import (  # noqa: E402
    ASSET_CLASS_BY_SYMBOL,
    load_partition_registry,
    partition_role_for_day,
)

DATA = REPO_ROOT / "data/mt5_research_exports"
M15_DIRS = (DATA / "bridge_ftmo_m15_20250601_20260610", DATA / "bridge_ftmo_ext_m15_20250601_20260611")
HORIZONS = (4, 8, 16, 32)
ATR_N = 14
BH_Q = 0.05
EFFECT_FLOOR_ATR = 0.06  # net of spread proxy, per-bar drift floor
MIN_DAYS = 60
MIN_OBS = 1500

# Measured live spreads (price units) per symbol; true cost per cell is
# measured as mean(spread_price / bar ATR) over that cell's own bars —
# quiet-hour cells with shrunken ATR carry their honest, larger relative cost.
SPREADS = json.loads((ROUTE / "ULTIMATE_SYMBOL_SPREAD_SNAPSHOT.json").read_text())


def bars_from_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                yield (str(row["time"])[:19], float(row["open"]), float(row["high"]),
                       float(row["low"]), float(row["close"]))
            except (KeyError, ValueError):
                continue


def state_features(closes, highs, lows, i, atr):
    """Discrete state from closed bars <= i. None if insufficient lookback."""
    if i < 60 or atr <= 0:
        return None
    c = closes[i]
    # trend: EMA20 vs EMA50 proxy via simple means (cheap, deterministic)
    m20 = sum(closes[i - 19:i + 1]) / 20.0
    m50 = sum(closes[i - 49:i + 1]) / 50.0
    trend = "up" if m20 > m50 * 1.0005 else ("down" if m20 < m50 * 0.9995 else "flat")
    # range position over 48 bars
    hi48, lo48 = max(highs[i - 47:i + 1]), min(lows[i - 47:i + 1])
    pos = (c - lo48) / (hi48 - lo48) if hi48 > lo48 else 0.5
    pos_b = "low" if pos < 0.25 else ("high" if pos > 0.75 else "mid")
    # volatility regime: ATR14 vs ATR48
    tr48 = [max(highs[j] - lows[j], abs(highs[j] - closes[j - 1]), abs(lows[j] - closes[j - 1]))
            for j in range(i - 47, i + 1)]
    atr48 = sum(tr48) / len(tr48)
    vol = "expand" if atr > atr48 * 1.15 else ("contract" if atr < atr48 * 0.85 else "norm")
    # last-bar thrust
    rng = highs[i] - lows[i]
    body = abs(closes[i] - (closes[i - 1] if i else closes[i]))
    thrust = "big" if rng > 1.5 * atr else ("small" if rng < 0.5 * atr else "mid")
    _ = body
    return {"trend": trend, "pos": pos_b, "vol": vol, "thrust": thrust}


def main() -> int:
    registry = load_partition_registry(ROUTE / "ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl")
    role_cache: dict[str, str | None] = {}

    def role_for(day: str):
        if day not in role_cache:
            role_cache[day] = partition_role_for_day(day, registry)[0]
        return role_cache[day]

    # cell -> {symbol-day -> [fwd values]}
    train_cells: dict[tuple, dict[tuple, list[float]]] = defaultdict(lambda: defaultdict(list))
    val_cells: dict[tuple, dict[tuple, list[float]]] = defaultdict(lambda: defaultdict(list))
    cell_costs: dict[tuple, list[float]] = defaultdict(lambda: [0.0, 0.0])  # [sum spread/ATR, n]
    FEATURE_PAIRS = (("trend", "pos"), ("trend", "vol"), ("pos", "vol"),
                     ("trend", "thrust"), ("vol", "thrust"), ("pos", "thrust"))
    hour_block = lambda t: f"h{int(t[11:13]) // 4 * 4:02d}"

    n_files = n_obs = 0
    for d in M15_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*_M15.csv")):
            symbol = f.name[: -len("_M15.csv")]
            ac = ASSET_CLASS_BY_SYMBOL.get(symbol)
            if ac is None:
                continue
            n_files += 1
            rows = list(bars_from_csv(f))
            times = [r[0] for r in rows]
            highs = [r[2] for r in rows]
            lows = [r[3] for r in rows]
            closes = [r[4] for r in rows]
            spread_price = float((SPREADS.get(symbol) or {}).get("spread_price") or 0.0)
            if spread_price <= 0:
                continue
            trs = [0.0] * len(rows)
            for i in range(1, len(rows)):
                trs[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]),
                             abs(lows[i] - closes[i - 1]))
            max_h = max(HORIZONS)
            for i in range(60, len(rows) - max_h):
                day = times[i][:10]
                role = role_for(day)
                if role not in ("TRAIN", "TRAIN_DEVELOPMENT_GRADE", "VALIDATION"):
                    continue
                atr = sum(trs[i - ATR_N + 1:i + 1]) / ATR_N
                st = state_features(closes, highs, lows, i, atr)
                if st is None:
                    continue
                n_obs += 1
                hb = hour_block(times[i])
                bucket = train_cells if role != "VALIDATION" else val_cells
                key_day = (symbol, day)
                sp_atr = spread_price / atr
                for h in HORIZONS:
                    fwd = (closes[i + h] - closes[i]) / atr
                    for fa, fb in FEATURE_PAIRS:
                        cell = (ac, hb, f"{fa}={st[fa]}", f"{fb}={st[fb]}", h)
                        bucket[cell][key_day].append(fwd)
                        if role != "VALIDATION":
                            cc = cell_costs[cell]
                            cc[0] += sp_atr
                            cc[1] += 1.0

    tested = []
    for cell, day_map in train_cells.items():
        if len(day_map) < MIN_DAYS:
            continue
        day_means = [statistics.fmean(v) for v in day_map.values()]
        nobs = sum(len(v) for v in day_map.values())
        if nobs < MIN_OBS:
            continue
        m = statistics.fmean(day_means)
        sd = statistics.pstdev(day_means)
        if sd <= 0:
            continue
        cc = cell_costs.get(cell) or [0.0, 1.0]
        cell_cost = cc[0] / cc[1] if cc[1] else 0.06
        net_effect = abs(m) - cell_cost
        t = m / (sd / math.sqrt(len(day_means)))
        p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t) / math.sqrt(2.0))))
        tested.append({"cell": cell, "days": len(day_means), "obs": nobs, "mean_atr": m,
                       "cell_spread_atr": round(cell_cost, 4),
                       "net_effect_atr": net_effect, "t_dayclustered": t, "p": p})

    tested.sort(key=lambda r: r["p"])
    mt = len(tested)
    max_k = 0
    for k, r in enumerate(tested, 1):
        if r["p"] <= BH_Q * k / mt:
            max_k = k
    bh = tested[:max_k]
    survivors = [r for r in bh if r["net_effect_atr"] >= EFFECT_FLOOR_ATR]

    # single out-of-time confirmation on pre-registered survivors
    confirmed = []
    for r in survivors:
        vmap = val_cells.get(r["cell"], {})
        if len(vmap) < 5:
            continue
        v_day_means = [statistics.fmean(v) for v in vmap.values()]
        vm = statistics.fmean(v_day_means)
        same_sign = (vm > 0) == (r["mean_atr"] > 0)
        confirmed.append({**r, "val_days": len(v_day_means), "val_mean_atr": vm,
                          "val_same_sign": same_sign})

    out = {
        "schema_version": "ultimate_origin_discovery_mine_v2_measured_costs",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": n_files, "bar_observations": n_obs,
        "cells_tested": mt, "bh_survivors": len(bh),
        "effect_floor_survivors": len(survivors),
        "confirmed_out_of_time_same_sign": sum(1 for c in confirmed if c["val_same_sign"]),
        "confirmed_total_evaluable": len(confirmed),
        "survivors": sorted(survivors, key=lambda r: -abs(r["net_effect_atr"]))[:200],
        "confirmations": confirmed[:200],
        "broker_operation": False, "paid_api_or_vendor_call": False,
        "broker_runtime_change_status": False, "validation_result_status": False,
        "outcome_result_rows_status": False,
    }
    (ROUTE / "ULTIMATE_ORIGIN_DISCOVERY_MINE_V2.json").write_text(
        json.dumps(out, indent=1, sort_keys=True, default=str))
    print(json.dumps({k: out[k] for k in ("files", "bar_observations", "cells_tested",
                                          "bh_survivors", "effect_floor_survivors",
                                          "confirmed_out_of_time_same_sign",
                                          "confirmed_total_evaluable")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
