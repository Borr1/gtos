#!/usr/bin/env python3
"""lane e-coherence: build ONE canonical base frame joining the working set to the
w0-capture no-look-ahead decision anchor, so every mechanism can be measured on the
SAME rows with the SAME conventions.  Writes a pickle for fast reuse."""
import gzip, json, os, sys, pickle
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa

OUT = "/tmp/ecoh/e_base.pkl"

rows = w0_ws.load()
df = pd.DataFrame(rows)

anchor = {}
with gzip.open(os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as fh:
    for line in fh:
        if not line.strip():
            continue
        a = json.loads(line)
        anchor[(a["candidate_id"], a["decision_time_utc"])] = a

df["_key"] = list(zip(df["candidate_id"], df["decision_time_utc"]))
# CLEAN anchor: bars are OPEN-stamped, so the bar stamped at the decision MINUTE is
# entirely POST-decision (w0-capture self-correction).  The close of the PREVIOUS bar is
# the last price knowable at the decision instant.  mkt_r_close is the look-ahead anchor
# and is carried only for the adjudication of that correction.
df["mkt_r"] = [anchor.get(k, {}).get("mkt_r_prev_close") for k in df["_key"]]
df["mkt_r_lookahead"] = [anchor.get(k, {}).get("mkt_r_close") for k in df["_key"]]
df["anchor_exact"] = [anchor.get(k, {}).get("anchor_exact") for k in df["_key"]]

m = df["mkt_r"]
born = np.where(m.isna(), "unanchored",
       np.where(m <= -1.0, "past_stop",
       np.where(m < 0.0, "marketable",
       np.where(m == 0.0, "at_limit", "resting"))))
df["born"] = born

# corrected-cost columns (spread over-charge divisor applied to the spread limb only)
for div, name in ((1.0, "cost_r_d1"), (7.3, "cost_r_d73"), (8.5, "cost_r_d85")):
    df[name] = (df["spread_r"] / div) + df["commission_r"] + df["expected_slippage_r"] + df["swap_cost_r"]

df["gate_spread"] = df["spread_r"] <= 0.10
df["gate_total"] = df["cost_r"] <= 0.15
df["gate_both"] = df["gate_spread"] & df["gate_total"]

df["day"] = df["decision_time_utc"].str[:10]
df["hour"] = df["decision_time_utc"].str[11:13].astype(int)

with open(OUT, "wb") as fh:
    pickle.dump(df, fh)

summary = {
    "n": int(len(df)),
    "born_counts": df["born"].value_counts().to_dict(),
    "anchored": int(df["mkt_r"].notna().sum()),
    "gross_mean": float(df["gross_r"].mean()),
    "honest_mean": float(df["fill_honest_walk_r"].mean()),
    "plain_mean": float(df["plain_walk_r"].mean()),
    "entry_touched_true": int(df["entry_touched"].sum()),
    "bar1_fill": int((df["bars_to_entry_touch"] == 1).sum()),
    "cols": len(df.columns),
}
print(json.dumps(summary, indent=1, default=str))
