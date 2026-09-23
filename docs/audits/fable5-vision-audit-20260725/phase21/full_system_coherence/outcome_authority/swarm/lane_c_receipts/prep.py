"""Flatten the 5-month cache into numpy arrays once; reused by all LANE C measurements."""
import gzip, pickle, numpy as np, json
CACHE="/private/tmp/w21-puzzle-cache"; MONTHS=("feb","apr","may","jun","jul")
FEATS=["close_position_in_lookback_range","dist_to_prior_high20_atr","dist_to_prior_low20_atr",
 "sweep_depth_atr","trigger_bar_body_atr","trigger_bar_range_atr","compression_ratio_prior_bar",
 "atr14_over_atr50","close_to_close_vol_8_over_48","session_open_range_width_atr",
 "bars_since_session_open","poi_age_hours","poi_distance_to_zone_atr","poi_distance_to_midpoint_atr",
 "poi_max_mitigation_fraction","poi_overlap_bar_count","poi_touch_count","poi_touch_episode_count",
 "risk_over_atr","stop_distance_atr","target_distance_atr","distance_to_limit_atr",
 "distance_to_limit_risk","utc_hour","spread_r","deductible_cost_r","cost_r"]
rows=[]
for m in MONTHS:
    rows += pickle.load(gzip.open(f"{CACHE}/rows_{m}.pkl.gz","rb"))
N=len(rows)
fam=np.array([r["origin_family"] for r in rows]); day=np.array([r["trading_day"] for r in rows])
mon=np.array([r["month"] for r in rows]); sym=np.array([r["symbol"] for r in rows])
side=np.array([r["side"] for r in rows]); st=np.array([r["lifecycle_label_status"] for r in rows])
ses=np.array([str(r.get("utc_session")) for r in rows])
tstate=np.array([str(r.get("trend_state_m15")) for r in rows])
X=np.full((N,len(FEATS)),np.nan)
for j,k in enumerate(FEATS):
    X[:,j]=[(r.get(k) if isinstance(r.get(k),(int,float)) and not isinstance(r.get(k),bool) else np.nan) for r in rows]
tn=np.array([(r["terminal_net_r"] if r.get("terminal_net_r") is not None else np.nan) for r in rows])
e=np.where(st=="RESOLVED_NO_FILL",0.0,tn)          # per-candidate economic R
usable=~np.isnan(e)
np.savez_compressed("arrays.npz",fam=fam,day=day,mon=mon,sym=sym,side=side,st=st,ses=ses,
                    tstate=tstate,X=X,tn=tn,e=e,usable=usable,feats=np.array(FEATS))
print("N",N,"usable",int(usable.sum()),"days",len(set(day)))
