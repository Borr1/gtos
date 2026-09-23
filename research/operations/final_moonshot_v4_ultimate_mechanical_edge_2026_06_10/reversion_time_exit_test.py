"""Reconciliation test: does the mined reversion drift survive order-level
accounting under its OWN exit design (time exit at H bars + wide stop)?

Uses the reconstructed M1 paths of range_extreme_reversion candidates
(R units: 1R == 1x ATR14 by generator construction). Policy: enter at path
start, exit at the close of M15-bar horizon H (H*15 M1 bars), disaster stop
at -3R intrabar. Cost = measured spread/ATR per symbol. TRAIN t-stats
(day-clustered) per (asset_class, session); VALIDATION checked once.
"""
import json, math, statistics, sys, collections
from pathlib import Path
ROUTE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE.parents[2]))
from src.research_infra.ultimate_exit_policy_segment_tournament import build_path_dataset
from src.research_infra.learned_edge_dataset_builder import load_partition_registry, partition_role_for_day

SPREADS = json.loads((ROUTE / "ULTIMATE_SYMBOL_SPREAD_SNAPSHOT.json").read_text())
registry = load_partition_registry(ROUTE / "ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl")
HORIZONS_M15 = (4, 8, 16)
STOP_R = -3.0

months = collections.defaultdict(set)
for line in open(ROUTE / "train_ledgers_univ/ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl"):
    r = json.loads(line)
    if r.get("status") == "completed":
        d = str(r["trading_day"]); months[d[:7]].add(d)

train = collections.defaultdict(lambda: collections.defaultdict(list))
val = collections.defaultdict(lambda: collections.defaultdict(list))
n_paths = 0
for month in sorted(months):
    ds = build_path_dataset([str(ROUTE / "train_ledgers_univ")], include_missed=True,
                            day_filter=months[month])
    for row in ds.rows:
        if row.origin_family != "range_extreme_reversion": continue
        role, _ = partition_role_for_day(row.trading_day, registry)
        if role not in ("TRAIN", "TRAIN_DEVELOPMENT_GRADE", "VALIDATION"): continue
        n_paths += 1
        atr = abs(row.entry - row.stop)  # 1R in price = 1x ATR14
        sp = float((SPREADS.get(row.symbol) or {}).get("spread_price") or 0.0)
        cost_r = sp / atr if atr > 0 else 0.2
        obs = row.observations
        for H in HORIZONS_M15:
            m1_bars = H * 15
            stopped = False
            net = None
            for i, o in enumerate(obs[:m1_bars]):
                lo = getattr(o, "low_r", None)
                if lo is not None and lo <= STOP_R:
                    net = STOP_R - cost_r; stopped = True; break
            if not stopped:
                k = min(m1_bars, len(obs)) - 1
                if k < 0: continue
                c = getattr(obs[k], "close_r", None)
                if c is None: continue
                net = float(c) - cost_r
            seg = (row.asset_class, row.session_bucket, H)
            bucket = train if role != "VALIDATION" else val
            bucket[seg][(row.symbol, row.trading_day)].append(net)
    print(f"[{month}] cumulative reversion paths: {n_paths}", flush=True)

out = []
for seg, daymap in train.items():
    if len(daymap) < 40: continue
    dm = [statistics.fmean(v) for v in daymap.values()]
    m, sd = statistics.fmean(dm), statistics.pstdev(dm)
    if sd <= 0: continue
    t = m / (sd / math.sqrt(len(dm)))
    vmap = val.get(seg, {})
    vdm = [statistics.fmean(v) for v in vmap.values()]
    out.append({"segment": list(seg), "train_days": len(dm), "train_mean_r": round(m, 4),
                "t": round(t, 2), "obs": sum(len(v) for v in daymap.values()),
                "val_days": len(vdm), "val_mean_r": round(statistics.fmean(vdm), 4) if vdm else None})
out.sort(key=lambda r: -r["t"])
res = {"schema_version": "reversion_time_exit_reconciliation_v1", "paths": n_paths,
       "stop_r": STOP_R, "cells": out[:60],
       "positive_train_cells_t2": sum(1 for r in out if r["t"] >= 2 and r["train_mean_r"] > 0),
       "broker_operation": False, "paid_api_or_vendor_call": False,
       "broker_runtime_change_status": False, "validation_result_status": False,
       "outcome_result_rows_status": False}
(ROUTE / "ULTIMATE_REVERSION_TIME_EXIT_TEST.json").write_text(json.dumps(res, indent=1, sort_keys=True))
top = [r for r in out if r["t"] >= 2 and r["train_mean_r"] > 0][:10]
print(json.dumps({"paths": n_paths, "cells_tested": len(out), "train_pos_t2": len([r for r in out if r['t']>=2 and r['train_mean_r']>0]),
                  "top": top}, sort_keys=True))
