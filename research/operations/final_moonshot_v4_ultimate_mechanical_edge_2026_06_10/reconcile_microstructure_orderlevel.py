"""Order-level reconciliation of the microstructure go-live book.

The decisive go-live test: do the absorption + volume-delta setups survive the
REAL fill machine (entry geometry + fill timing the timewarp actually produced)
plus REAL per-asset-class cost — not the bar-engine's bar-close assumption?

Source: train_ledgers_micro (full universe, microstructure generators ON).
build_path_dataset(include_missed=True) reconstructs each candidate's real
post-fill M1 path. We replay the book's exit design over that real path:
  - disaster stop 2.5xATR (the R unit)
  - fixed-horizon exits at H in {240,480,960} M1 bars (4h/8h/16h, spanning the
    book's M15 horizons) -- volume-exhaust needs per-bar volume the M1 path
    doesn't carry, so we use the book's fixed-exit variants (which validated).
Real cost from ULTIMATE_REAL_COST_MAP (per asset class). Grouped by
(family, asset_class, side), regime-baselined (always-on per ac+horizon),
TRAIN 2025-07..2026-04 vs VALIDATION (registry roles), month-chunked.

Replay/proxy evidence; no broker calls.
"""
import json, math, statistics, sys, collections
from pathlib import Path

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from src.research_infra.ultimate_exit_policy_segment_tournament import build_path_dataset
from src.research_infra.learned_edge_dataset_builder import load_partition_registry, partition_role_for_day

LEDGERS = ROUTE / "train_ledgers_micro"
COST = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GLOBAL_COST = COST.get("_global_median", 0.095)
STOP_ATR = 2.5
HORIZONS_M1 = (240, 480, 960)
MICRO = ("microstructure_absorption_reversal", "microstructure_vdelta_divergence")


def cost_for(ac): return float(COST.get(ac, GLOBAL_COST))


def exit_net(obs, d, h, c):
    # obs entries carry close_r/high_r/low_r in R units (1R = 2.5xATR by build);
    # disaster stop at -STOP_ATR; else close at horizon h.
    end = min(h, len(obs)) - 1
    if end < 0:
        return None
    for j in range(end + 1):
        lo = getattr(obs[j], "low_r", None); hi = getattr(obs[j], "high_r", None)
        if lo is None or hi is None:
            continue
        if d > 0 and lo <= -STOP_ATR:
            return -STOP_ATR - c
        if d < 0 and hi >= STOP_ATR:
            return -STOP_ATR - c
    cl = getattr(obs[end], "close_r", None)
    if cl is None:
        return None
    return d * float(cl) - c  # close_r already signed in path frame; d aligns long/short


def main():
    registry = load_partition_registry(ROUTE / "ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl")
    role_cache = {}
    def role_for(day):
        if day not in role_cache:
            role_cache[day] = partition_role_for_day(day, registry)[0]
        return role_cache[day]

    # month list from progress ledger (completed days)
    months = collections.defaultdict(set)
    pl = LEDGERS / "ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl"
    for line in open(pl):
        r = json.loads(line)
        if r.get("status") == "completed":
            d = str(r["trading_day"]); months[d[:7]].add(d)

    # Three windows: TRAIN (<2026-01), OOS_Q1 (2026-01..04, the engine's holdout),
    # OOS_MAY (>=2026-05, registry VALIDATION). Robust go-live read on both OOS.
    def window(day):
        if day < "2026-01": return "train"
        if day < "2026-05": return "oos_q1"
        return "oos_may"

    train = collections.defaultdict(list)
    oos_q1 = collections.defaultdict(list)
    oos_may = collections.defaultdict(list)
    base = collections.defaultdict(list)    # (ac,side,h) -> nets (non-micro baseline; empty if filtered)
    sub = collections.defaultdict(lambda: collections.defaultdict(list))
    n_paths = 0
    for month in sorted(months):
        ds = build_path_dataset([str(LEDGERS)], include_missed=True, day_filter=months[month])
        for r in ds.rows:
            ac = r.asset_class; c = cost_for(ac)
            d = 1 if r.side == "LONG" else -1
            w = window(r.trading_day)
            per = ("2025H2" if r.trading_day < "2026-01"
                   else ("2022H1" if r.trading_day < "2022-07" else r.trading_day[:4]))
            for h in HORIZONS_M1:
                net = exit_net(r.observations, d, h, c)
                if net is None:
                    continue
                if r.origin_family not in MICRO:
                    base[(ac, r.side, h)].append(net)
                    continue
                key = (r.origin_family, ac, r.side, h)
                if w == "train":
                    train[key].append(net); sub[key][per].append(net)
                elif w == "oos_q1":
                    oos_q1[key].append(net)
                else:
                    oos_may[key].append(net)
        n_paths += len(ds.rows)
        print(f"[{month}] cumulative paths {n_paths}", flush=True)

    # clean baseline (non-micro paths as the always-on proxy per ac+side+h)
    base_mean = {}
    for k, v in base.items():
        vv = [x for x in v if x is not None]
        if vv: base_mean[k] = statistics.fmean(vv)

    rows = []
    for key, nets in train.items():
        if len(nets) < 60: continue
        fam, ac, side, h = key
        beta = base_mean.get((ac, side, h), 0.0)
        m = statistics.fmean(nets); sd = statistics.pstdev(nets)
        if sd <= 0: continue
        edge = m - beta; et = edge / (sd / math.sqrt(len(nets)))
        q1 = oos_q1.get(key, []); may = oos_may.get(key, [])
        q1m = (statistics.fmean(q1) - beta) if len(q1) >= 10 else None
        maym = (statistics.fmean(may) - beta) if len(may) >= 10 else None
        rows.append({"key": list(key), "n": len(nets), "raw_r": round(m, 4), "beta": round(beta, 4),
                     "edge_vs_beta": round(edge, 4), "edge_t": round(et, 2),
                     "oos_q1_n": len(q1), "oos_q1_r": round(q1m, 4) if q1m is not None else None,
                     "oos_may_n": len(may), "oos_may_r": round(maym, 4) if maym is not None else None,
                     "oos_q1_same_sign": None if q1m is None else (q1m > 0) == (edge > 0),
                     "oos_may_same_sign": None if maym is None else (maym > 0) == (edge > 0)})
    rows.sort(key=lambda r: -(r["edge_vs_beta"]))
    out = {"schema_version": "microstructure_orderlevel_reconciliation_v2",
           "paths_total": n_paths, "horizons_m1": list(HORIZONS_M1), "stop_atr": STOP_ATR,
           "real_cost_map": COST, "note": "raw_r = realized R after real cost (beta~0 since candidate ledger micro-filtered); edge_vs_beta==raw_r. OOS_Q1=2026-01..04 (engine holdout), OOS_MAY=registry VALIDATION 2026-05.",
           "rows": rows,
           "positive_train": sum(1 for r in rows if r["raw_r"] > 0),
           "positive_oos_q1": sum(1 for r in rows if r["raw_r"] > 0 and r["oos_q1_same_sign"]),
           "positive_oos_may": sum(1 for r in rows if r["raw_r"] > 0 and r["oos_may_same_sign"]),
           "broker_operation": False, "paid_api_or_vendor_call": False,
           "broker_runtime_change_status": False, "validation_result_status": False,
           "outcome_result_rows_status": False}
    (ROUTE / "ULTIMATE_MICROSTRUCTURE_ORDERLEVEL_RECONCILIATION.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps({"paths": n_paths, "rows": len(rows), "positive_train": out["positive_train"],
                      "positive_oos_q1": out["positive_oos_q1"], "positive_oos_may": out["positive_oos_may"]}, sort_keys=True))
    for r in rows[:18]:
        print(f"  {r['key']}  raw {r['raw_r']:+.3f} t={r['edge_t']} q1 {r['oos_q1_r']}({r['oos_q1_same_sign']}) may {r['oos_may_r']}({r['oos_may_same_sign']}) n={r['n']}/{r['oos_q1_n']}/{r['oos_may_n']}")


if __name__ == "__main__":
    main()
