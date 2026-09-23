"""BH-certified segment book under pullback-0.4R entries (owner doctrine).

Per path: wait for a 0.4R-better price within 60 M1 bars after decision; if
touched, enter there and replay the winner trail policy; missed = no trade
(EV contribution 0). TRAIN-only one-sided t per segment cell on per-CANDIDATE
EV stream (missed candidates as 0.0 keeps the selection-filter honesty);
BH(0.10); VALIDATION evaluated once. Replay/proxy evidence.
"""
import json, math, statistics, sys, collections
from pathlib import Path
ROUTE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE.parents[2]))
from src.research_infra.ultimate_exit_policy_segment_tournament import build_path_dataset
from src.research.dynamic_execution_policy import PolicySpec, simulate_policy
from src.research_infra.learned_edge_dataset_builder import load_partition_registry, partition_role_for_day

DELTA, WAIT, C = 0.4, 60, 0.17 / 4.0
WINNER = PolicySpec(name="trailing_t1_g0p1_c6", final_target_r=6.0, trailing_trigger_r=1.0, trailing_gap_r=0.1)
SURFACE24 = {"AUDJPY","AUDUSD","BTCUSD","CHFJPY","ETHUSD","EURGBP","EURJPY","EURUSD","GBPJPY","GBPUSD",
             "GER40","JP225","NAS100","NZDUSD","SPX500","UK100","UKOIL_cash","US30_cash","USDCAD",
             "USDCHF","USDJPY","USOIL_cash","XAGUSD","XAUUSD"}

registry = load_partition_registry(ROUTE / "ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl")
train, val, val_days = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(set)
dirs = [(str(ROUTE / "train_ledgers_scale4"), None), (str(ROUTE / "experiment_ledgers/universe_ext_probe"), SURFACE24)]
n_paths = 0
for d, skip_syms in dirs:
    ds = build_path_dataset([d], include_missed=True)
    for row in ds.rows:
        if skip_syms and row.symbol in skip_syms: continue
        n_paths += 1
        role, _grade = partition_role_for_day(row.trading_day, registry)
        if role not in ("TRAIN", "TRAIN_DEVELOPMENT_GRADE", "VALIDATION"): continue
        fill_i = None
        for i, o in enumerate(row.observations[:WAIT]):
            lo = getattr(o, "low_r", None)
            if lo is not None and lo <= -DELTA: fill_i = i; break
        ev = 0.0 if fill_i is None else float(getattr(simulate_policy(WINNER, row.observations[fill_i:]), "final_r", 0.0)) + DELTA - C
        seg = (row.asset_class, row.origin_family, row.session_bucket)
        if role == "VALIDATION":
            val[seg].append(ev); val_days[seg].add(row.trading_day)
        else:
            train[seg].append(ev)

tested = []
for seg, evs in train.items():
    if len(evs) < 150: continue
    m, sd = statistics.fmean(evs), statistics.pstdev(evs)
    if sd <= 0: continue
    t = m / (sd / math.sqrt(len(evs)))
    p = 1.0 - 0.5 * (1.0 + math.erf(t / math.sqrt(2.0)))
    tested.append({"segment": seg, "n": len(evs), "mean": m, "t": t, "p": p})
tested.sort(key=lambda r: r["p"])
mtests = len(tested)
max_k = 0
for k, r in enumerate(tested, 1):
    if r["p"] <= 0.10 * k / mtests: max_k = k
bh_book = tested[:max_k]
# Portfolio mode (the deployable statistical unit): pre-registered rule =
# top-15 TRAIN cells by t-stat with n>=150; the BOOK is then tested as ONE
# portfolio on VALIDATION (per-cell certification is power-bound at n~300).
book = sorted(tested, key=lambda r: -r["t"])[:15]
out = {"schema_version": "ultimate_pullback_book_v2_portfolio", "paths_considered": n_paths,
       "selection_rule": "preregistered_top15_train_t_n150_portfolio_certification",
       "bh_percell_survivors": len(bh_book),
       "pullback_delta_r": DELTA, "wait_bars": WAIT, "cells_tested": mtests, "cells_surviving": len(book),
       "book": [], "broker_operation": False, "paid_api_or_vendor_call": False,
       "broker_runtime_change_status": False, "validation_result_status": False, "outcome_result_rows_status": False}
vn, vsum, vdays = 0, 0.0, set()
for r in book:
    seg = r["segment"]; v = val.get(seg, [])
    out["book"].append({"segment": list(seg), "train_n": r["n"], "train_mean_ev": round(r["mean"], 4),
                        "train_t": round(r["t"], 2), "p": r["p"], "validation_n": len(v),
                        "validation_mean_ev": round(statistics.fmean(v), 4) if v else None})
    vn += len(v); vsum += sum(v); vdays |= val_days.get(seg, set())
port_vals = [x for r in book for x in val.get(r["segment"], [])]
port_t = None
if len(port_vals) >= 30:
    pm, psd = statistics.fmean(port_vals), statistics.pstdev(port_vals)
    port_t = pm / (psd / math.sqrt(len(port_vals))) if psd > 0 else None
out["validation_once"] = {"candidates": vn, "ev_sum": round(vsum, 3),
                          "ev_per_candidate": round(vsum / vn, 4) if vn else None,
                          "days": len(vdays), "ev_per_day": round(vsum / max(1, len(vdays)), 3),
                          "portfolio_t": round(port_t, 3) if port_t is not None else None,
                          "portfolio_pass_t165": bool(port_t is not None and port_t > 1.65)}
(ROUTE / "ULTIMATE_PULLBACK_BOOK_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=str))
print(json.dumps({"cells": f"{mtests}->{len(book)}", **out["validation_once"]}, sort_keys=True))
