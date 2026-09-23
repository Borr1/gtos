#!/usr/bin/env python3
"""B3 step 7 -- mean realized R by each arm's OWN prediction decile.

Lane 3 measured this for the shipped ridge (D10 worst of ten).  Generalising it
to every arm answers R2 mechanically: is the top of the ranking the worst region
for every statistic, or only for the shipped one?
"""
import gzip, json, pickle
from collections import defaultdict
from pathlib import Path
import numpy as np
import b3_lib as L

LANE3 = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane3/out/preds_daily.pkl.gz")
with (L.OUT / "dataset.pkl").open("rb") as fh:
    data = pickle.load(fh)
meta = data["meta"]; n = len(meta)
keypos = {m["key"]: i for i, m in enumerate(meta)}
idx_all = [i for i, m in enumerate(meta) if m["month"] in L.MONTHS]

arrays = {}
with gzip.open(LANE3, "rb") as fh:
    sealed = pickle.load(fh)
a = np.full(n, np.nan)
for k, v in sealed.items():
    j = keypos.get(k)
    if j is not None: a[j] = v
arrays["SHIPPED_SEALED"] = a
for stage in L.complete_stages():
    p = L.OUT / f"preds_{stage}.npz"
    if p.exists():
        blob = np.load(p)
        for arm in blob.files:
            if np.isfinite(blob[arm]).sum() >= 100000: arrays[arm] = blob[arm]

out = {}
for arm, arr in sorted(arrays.items()):
    windows, _ = L.run_windows(meta, idx_all, arr)
    w = [x for x in windows if x["pick_actual"] is not None]
    if len(w) < 100: continue
    preds = np.array([x["top_pred"] for x in w])
    nets  = np.array([x["pick_actual"] for x in w])
    nofill= np.array([1.0 if x["pick_actual"] == 0.0 else 0.0 for x in w])
    mkt   = np.array([1.0 if x["top_order_type"] == "MARKET" else 0.0 for x in w])
    order = np.argsort(preds)
    rows = []
    k = len(order)//10
    for d in range(10):
        sl = order[d*k:(d+1)*k] if d < 9 else order[9*k:]
        rows.append({"decile": d+1, "n": int(len(sl)),
                     "mean_pred": round(float(preds[sl].mean()), 5),
                     "mean_net_r": round(float(nets[sl].mean()), 5),
                     "no_fill_share": round(float(nofill[sl].mean()), 4),
                     "market_share": round(float(mkt[sl].mean()), 4)})
    out[arm] = {"deciles": rows,
                "D10_minus_D1_net": round(rows[9]["mean_net_r"] - rows[0]["mean_net_r"], 5),
                "top_decile_is_worst": bool(rows[9]["mean_net_r"] == min(r["mean_net_r"] for r in rows))}
    print(f"{arm:16s} D1 {rows[0]['mean_net_r']:+.4f}  D5 {rows[4]['mean_net_r']:+.4f}  "
          f"D10 {rows[9]['mean_net_r']:+.4f}  (D10 mkt {rows[9]['market_share']:.2f} nofill {rows[9]['no_fill_share']:.2f})  "
          f"top_worst={out[arm]['top_decile_is_worst']}", flush=True)
(L.OUT / "DECILE_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=float))
