#!/usr/bin/env python3
"""l3_build - lane l3 substrate. Working set + born-state anchor + engineered
pre-decision features. Writes a pickle to $TMPDIR for fast reload by later steps.

born state (W0-capture, no look-ahead): m = mkt_r_prev_close = signed R distance of the
close of the M1 bar stamped decision-1min (bars are OPEN-stamped so that bar CLOSES at the
decision instant) from entry_price, in the trade's own direction.
  m <= -1.0 -> born_past_stop   (stop price already breached: never takeable)
  -1 < m < 0 -> born_marketable (limit already through the market)
  m == 0.0   -> born_at_limit   (entry == decision-instant price: an at-market order)
  m > 0.0    -> born_resting    (a genuine resting limit)
"""
import gzip, json, os, math, pickle, sys
import pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "w0_WORKING_SET.jsonl.gz")
ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
TMP = os.environ.get("TMPDIR", "/tmp")
OUT = os.path.join(TMP, "l3_frame.pkl")

def rd(p):
    with gzip.open(p, "rt") as fh:
        return [json.loads(l) for l in fh if l.strip()]

ws = pd.DataFrame(rd(WS))
an = pd.DataFrame(rd(ANCHOR))[["candidate_id","decision_time_utc","anchor_bar_time","anchor_exact",
                               "mkt_r_prev_close","mkt_r_close","mkt_r_open","mkt_r_high","mkt_r_low"]]
df = ws.merge(an, on=["candidate_id","decision_time_utc"], how="left", validate="one_to_one")

m = df["mkt_r_prev_close"]
df["born_state"] = np.where(m.isna(), "unanchored",
                    np.where(m <= -1.0, "born_past_stop",
                    np.where(m < 0.0, "born_marketable",
                    np.where(m == 0.0, "born_at_limit", "born_resting"))))
df["takeable"] = df["born_state"].isin(["born_at_limit","born_marketable","born_resting"])

# ---- engineered PRE-DECISION features
dt = pd.to_datetime(df["decision_time_utc"], utc=True, format="ISO8601")
df["utc_hour"] = dt.dt.hour
df["utc_minute"] = dt.dt.minute
df["utc_dow"] = dt.dt.dayofweek
df["utc_dom"] = dt.dt.day
df["utc_week"] = dt.dt.isocalendar().week.astype(int)
df["risk_distance_pct_of_price"] = 100.0*df["risk_distance"]/df["entry_price"].abs()
df["log_risk_distance_pct"] = np.log10(df["risk_distance_pct_of_price"].clip(lower=1e-9))
df["implied_target_r"] = (df["take_profit_1"]-df["entry_price"]).abs()/df["risk_distance"]
df["entry_offset_r"] = df["mkt_r_prev_close"]          # signed distance market->entry at decision
df["abs_entry_offset_r"] = df["mkt_r_prev_close"].abs()
df["cost_over_target"] = df["cost_r"]/df["implied_target_r"].replace(0,np.nan)
df["ev_minus_cost_r"] = df["candidate_ev_r"]-df["cost_r"]
df["spread_share_of_cost"] = df["spread_r"]/df["cost_r"].replace(0,np.nan)
df["is_first_emission_b"] = df["is_first_emission"].astype(bool)

df.to_pickle(OUT)

wins = (df["outcome_band"]=="ge_target"); stops = (df["outcome_band"]=="full_stop")
rep = {
 "rows": int(len(df)),
 "anchored": int(df["mkt_r_prev_close"].notna().sum()),
 "band_counts": df["outcome_band"].value_counts().to_dict(),
 "cohort_full_target_n": int(wins.sum()),
 "cohort_full_stop_n": int(stops.sum()),
 "born_state_counts": df["born_state"].value_counts().to_dict(),
 "born_x_band_full_target": df.loc[wins,"born_state"].value_counts().to_dict(),
 "born_x_band_full_stop": df.loc[stops,"born_state"].value_counts().to_dict(),
 "takeable_n": int(df["takeable"].sum()),
 "takeable_full_target_n": int((wins&df["takeable"]).sum()),
 "takeable_full_stop_n": int((stops&df["takeable"]).sum()),
 "pickle": OUT,
}
json.dump(rep, open(os.path.join(HERE,"l3_COHORTS_V1.json"),"w"), indent=1, default=str)
print(json.dumps(rep, indent=1, default=str))
