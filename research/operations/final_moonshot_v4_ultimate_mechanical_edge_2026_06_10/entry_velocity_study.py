"""Entry-precision + trade-velocity study (owner ultimate-system doctrine).

A) Velocity: per-segment time-to-MFE distributions from oracle rows ->
   time-stop calibration candidates (R/hour focus).
B) Entry precision: counterfactual pullback entries from M1 paths — wait for
   delta-R better price within K bars; EV(delta) = fill_frac * (net + delta)
   vs baseline, per segment. Replay/proxy evidence; boundary stamps.
"""
import json, sys, statistics, collections
from pathlib import Path
ROUTE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE.parents[2]))
from src.research_infra.ultimate_exit_policy_segment_tournament import build_path_dataset
from src.research.dynamic_execution_policy import PolicySpec, simulate_policy
from src.research_infra.learned_edge_dataset_builder import read_jsonl

LEDGERS = ROUTE / "train_ledgers_scale4"
OUT = ROUTE / "ULTIMATE_ENTRY_VELOCITY_STUDY.json"
DELTAS = (0.15, 0.25, 0.4)
WAIT_BARS = 60
WINNER = PolicySpec(name="trailing_t1_g0p1_c6", final_target_r=6.0, trailing_trigger_r=1.0, trailing_gap_r=0.1)
C = 0.17 / 4.0

ds = build_path_dataset([str(LEDGERS)], include_missed=True)
seg_velocity = collections.defaultdict(list)
seg_entry = collections.defaultdict(lambda: {"base": [], **{f"d{d}": [] for d in DELTAS}})
for row in ds.rows:
    seg = (row.asset_class, row.origin_family, row.session_bucket)
    obs = row.observations
    res = simulate_policy(WINNER, obs)
    base_net = float(getattr(res, "final_r", 0.0)) - C
    seg_entry[seg]["base"].append(base_net)
    # time to best MFE (bars to running-max high)
    best, best_i = -9.9, 0
    for i, o in enumerate(obs):
        h = getattr(o, "high_r", None)
        if h is not None and h > best: best, best_i = h, i
    seg_velocity[seg].append(best_i)  # minutes (M1 bars)
    # counterfactual pullback entries: price going delta BELOW entry (long) = low_r <= -delta
    for d in DELTAS:
        fill_i = None
        for i, o in enumerate(obs[:WAIT_BARS]):
            lo = getattr(o, "low_r", None)
            if lo is not None and lo <= -d: fill_i = i; break
        if fill_i is None:
            seg_entry[seg][f"d{d}"].append(None)  # missed
        else:
            res2 = simulate_policy(WINNER, obs[fill_i:])
            # entered d better: shift R frame by +d (risk re-anchored approx)
            seg_entry[seg][f"d{d}"].append(float(getattr(res2, "final_r", 0.0)) + d - C)

out = {"schema_version": "ultimate_entry_velocity_study_v1", "paths": len(ds.rows),
       "winner_policy": "trailing_t1_g0p1_c6", "cost_r": C, "wait_bars": WAIT_BARS,
       "segments": [], "broker_operation": False, "paid_api_or_vendor_call": False,
       "broker_runtime_change_status": False, "validation_result_status": False,
       "outcome_result_rows_status": False}
glob_base, glob_cf = [], {d: [] for d in DELTAS}
for seg, e in seg_entry.items():
    if len(e["base"]) < 100: continue
    vel = sorted(seg_velocity[seg])
    entry_stats = {"base_mean_net": round(statistics.fmean(e["base"]), 4), "n": len(e["base"])}
    glob_base.extend(e["base"])
    for d in DELTAS:
        vals = e[f"d{d}"]
        filled = [v for v in vals if v is not None]
        fill_frac = len(filled) / len(vals) if vals else 0
        ev = (statistics.fmean(filled) * fill_frac) if filled else None  # missed = 0 (no trade)
        entry_stats[f"pullback_{d}"] = {"fill_frac": round(fill_frac, 3),
                                        "mean_net_filled": round(statistics.fmean(filled), 4) if filled else None,
                                        "ev_per_candidate": round(ev, 4) if ev is not None else None}
        glob_cf[d].extend([v if v is not None else 0.0 for v in vals])
    out["segments"].append({"segment": list(seg), **entry_stats,
        "median_minutes_to_mfe": vel[len(vel)//2], "p75_minutes_to_mfe": vel[int(0.75*len(vel))]})
out["global"] = {"base_mean_net": round(statistics.fmean(glob_base), 4),
    **{f"pullback_{d}_ev": round(statistics.fmean(glob_cf[d]), 4) for d in DELTAS}}
OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str))
print(json.dumps(out["global"], sort_keys=True))
