"""LANE I prep: five-month cached candidate population -> one compact parquet."""
import gzip, pickle, json, time, sys
from pathlib import Path
import numpy as np, pandas as pd

CACHE = Path("/private/tmp/w21-puzzle-cache")
OUT = Path("/tmp/lane_i")
MONTHS = ["feb", "apr", "may", "jun", "jul"]

CAT = ['symbol','side','origin_family','utc_session','proposed_order_type','utc_hour','weekday',
       'symbol_x_family','family_x_session','symbol_x_side','poi_mitigation_status',
       'limit_marketable_at_decision','trend_state_m15','trend_transition_flag']
NUM = ['cost_r','spread_r','expected_slippage_r','swap_cost_r','commission_r','distance_to_limit_atr',
       'distance_to_limit_risk','risk_over_atr','risk_fraction_of_entry','poi_age_hours',
       'poi_distance_to_midpoint_atr','poi_distance_to_zone_atr','poi_touch_count',
       'poi_max_mitigation_fraction','poi_touch_episode_count','poi_overlap_bar_count',
       'atr14_over_atr50','stop_distance_atr','target_distance_atr','close_position_in_lookback_range',
       'dist_to_prior_high20_atr','dist_to_prior_low20_atr','trigger_bar_range_atr','trigger_bar_body_atr',
       'compression_ratio_prior_bar','bars_since_session_open','close_to_close_vol_8_over_48',
       'sweep_depth_atr','session_open_range_width_atr']
META = ['candidate_occurrence_key','decision_window_id','trading_day','label_span_start_utc',
        'label_span_end_utc','expiry_utc','lifecycle_label_status','cost_label_status',
        'terminal_net_r','deductible_cost_r','predecision_geometry_valid','pred_month_boundary','month']
KEEP = META + CAT + NUM

frames = []
t0 = time.time()
for m in MONTHS:
    with gzip.open(CACHE / f"rows_{m}.pkl.gz", "rb") as fh:
        rows = pickle.load(fh)
    df = pd.DataFrame([{k: r.get(k) for k in KEEP} for r in rows])
    del rows
    frames.append(df)
    print(json.dumps({"month": m, "rows": len(df), "t": round(time.time()-t0,1)}), flush=True)
df = pd.concat(frames, ignore_index=True)
del frames
for c in CAT + ['lifecycle_label_status','cost_label_status','month','trading_day']:
    df[c] = df[c].astype(str).astype("category")
for c in NUM + ['terminal_net_r','deductible_cost_r','pred_month_boundary']:
    df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
df['predecision_geometry_valid'] = df['predecision_geometry_valid'].astype(bool)
for c in ['label_span_start_utc','label_span_end_utc','expiry_utc']:
    df[c] = pd.to_datetime(df[c], utc=True, format='mixed')
df['resolved'] = ~df['lifecycle_label_status'].astype(str).str.startswith('CENSORED_')
df['eligible'] = df['predecision_geometry_valid'] & df['cost_r'].notna() & np.isfinite(df['cost_r']) & (df['cost_r'] <= 0.20)
df.to_parquet(OUT/"pop.parquet")
print(json.dumps({"total": len(df), "eligible": int(df.eligible.sum()),
                  "resolved_eligible": int((df.eligible & df.resolved).sum()),
                  "has_pred": int(df.pred_month_boundary.notna().sum()),
                  "t": round(time.time()-t0,1)}, indent=1))
print(df.groupby('month', observed=True).agg(n=('month','size'), elig=('eligible','sum'),
      res_elig=('resolved','sum')).to_string())
