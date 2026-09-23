import gzip, pickle, numpy as np, json
from pathlib import Path
CACHE=Path("/private/tmp/w21-puzzle-cache")
MONTHS=["feb","apr","may","jun","jul"]
cols={k:[] for k in ("month","family","symbol","side","session","order_type","status","net","pred","window","day","cost_r","spread_r","tdatr","sdatr")}
for mo in MONTHS:
    with gzip.open(CACHE/f"rows_{mo}.pkl.gz","rb") as fh: rows=pickle.load(fh)
    for r in rows:
        cols["month"].append(mo); cols["family"].append(r["origin_family"]); cols["symbol"].append(r["symbol"])
        cols["side"].append(r["side"]); cols["session"].append(r["utc_session"])
        cols["order_type"].append(r["proposed_order_type"]); cols["status"].append(r["lifecycle_label_status"])
        v=r.get("terminal_net_r"); cols["net"].append(float(v) if v is not None else np.nan)
        p=r.get("pred_month_boundary"); cols["pred"].append(float(p) if p is not None else np.nan)
        cols["window"].append(r["decision_window_id"]); cols["day"].append(r["trading_day"])
        cols["cost_r"].append(float(r.get("cost_r") or np.nan)); cols["spread_r"].append(float(r.get("spread_r") or np.nan))
        cols["tdatr"].append(float(r.get("target_distance_atr") or np.nan)); cols["sdatr"].append(float(r.get("stop_distance_atr") or np.nan))
    print(mo, len(rows), flush=True)
out={k:np.array(v) for k,v in cols.items()}
np.savez_compressed("/private/tmp/laneG-walk/pool_table.npz", **out)
print("saved", {k:out[k].shape for k in out})
