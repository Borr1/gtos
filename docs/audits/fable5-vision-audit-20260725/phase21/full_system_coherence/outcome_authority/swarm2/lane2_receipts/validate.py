#!/usr/bin/env python3
"""Fidelity receipt: the SEALED arm at 1x must reproduce the sealed corpus label."""
import gzip, pickle, json, sys
from collections import Counter
import numpy as np

ERRMAP = {
 "NO_FILL":"RESOLVED_NO_FILL",
 "submission_bar_missing":"CENSORED_SOURCE_INTERVAL_GAP",
 "no_contiguous_successor":"CENSORED_SOURCE_INTERVAL_GAP",
 "gap_before_limit_expiry":"CENSORED_SOURCE_INTERVAL_GAP",
 "market_expires_before_successor":"CENSORED_GEOMETRY",
 "CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING":"CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING",
 "CENSORED_ORDERING_AMBIGUITY":"CENSORED_ORDERING_AMBIGUITY",
 "CENSORED_INVALID_GAP_THROUGH_SL_OR_TP":"CENSORED_INVALID_GAP_THROUGH_SL_OR_TP",
}

def sealed_1x(rec):
    if rec["H1"] <= 0: return "CENSORED_GEOMETRY", None   # quote_side.py:1147-1148 submission<expiry
    if rec.get("err"): return ERRMAP.get(rec["err"], "OTHER:"+rec["err"]), None
    hz = rec["sub"] + rec["H1"]
    if rec["fill_min"] + 1 > hz: return "CENSORED_SOURCE_INTERVAL_GAP", None
    h = rec.get("h1")
    if h is None: return "CENSORED_SOURCE_INTERVAL_GAP", None
    fg = rec["first_gap_min"]
    reach = min(h["end"], hz)
    if fg is not None and fg <= reach and fg <= hz:
        # the committed resolver walks bar-by-bar and censors the moment it needs a bar
        # past a gap; it only reaches the gap if no terminal fired strictly before it
        if h["end"] > fg or (h["kind"] == "TIME_STOP" and fg <= hz):
            return "CENSORED_SOURCE_INTERVAL_GAP", None
    if h["kind"] == "CENSOR": return "CENSORED_ORDERING_AMBIGUITY", None
    return "RESOLVED_FILLED_" + h["kind"], h["gross"]

out = {}
for m in sys.argv[1:] or ["feb","apr","may","jun","jul"]:
    recs = pickle.load(gzip.open(f"walk_{m}.pkl.gz","rb"))
    agree = Counter(); dis = Counter(); dr = []
    for r in recs:
        got, gross = sealed_1x(r)
        want = r["sealed_status"]
        if got == want:
            agree[want] += 1
            if gross is not None and r["sealed_net"] is not None:
                dr.append(abs((gross - r["ded"]) - r["sealed_net"]))
        else:
            dis[(want, got)] += 1
    tot = sum(agree.values()) + sum(dis.values())
    dr = np.array(dr) if dr else np.array([0.0])
    out[m] = {"n": tot, "agree": sum(agree.values()), "agree_frac": sum(agree.values())/tot,
              "net_r_max_abs_dev": float(dr.max()), "net_r_p999_dev": float(np.percentile(dr,99.9)),
              "n_net_compared": int(len(dr)),
              "top_disagreements": [{"sealed":k[0],"walk":k[1],"n":v} for k,v in dis.most_common(8)]}
    print(json.dumps({m: out[m]}, indent=1), flush=True)
json.dump(out, open("VALIDATE_1X.json","w"), indent=1)
