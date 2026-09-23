"""S3 - the anchor grid.  A0 (Lane 5's construction) against three clean ones."""
from __future__ import annotations
import json, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xs import build_matrices, make_returns, cell   # noqa: E402

OUT = os.path.join(HERE, "receipts")
M = make_returns(build_matrices())
print("panel", M["C"].shape, "symbols", len(M["syms"]),
      "classes", {c: int((M['CL'] == c).sum()) for c in sorted(set(M["CL"]))}, flush=True)

GRID = []
for anchor in ["A0_cc_cc", "A1_cc_gap", "A2_cc_oc", "A3_cc_oo"]:
    for uni, kw in [("FX", dict(classes=["fx"])),
                    ("ALL", dict()),
                    ("NOCRYPTO", dict(exclude=["crypto"])),
                    ("CRYPTO", dict(classes=["crypto"])),
                    ("EQUITY", dict(classes=["equity"]))]:
        GRID.append((f"{anchor}|{uni}", anchor, kw, None))
# currency-neutral residual, FX only, on the clean anchors
for anchor in ["A0_cc_cc", "A2_cc_oc", "A3_cc_oo"]:
    GRID.append((f"{anchor}|FX_CCYNEUTRAL", anchor, dict(classes=["fx"]), "currency"))

rows = []
series = {}
for name, anchor, kw, neu in GRID:
    r = cell(M, anchor=anchor, neutral=neu, nperm=1000, **kw)
    if r is None:
        print(f"{name:34s} insufficient", flush=True); continue
    series[name] = r.pop("_series")
    r["cellname"] = name
    rows.append(r)
    print(f"{name:34s} n={r['n_rebal']:5d} u={r['median_universe']:3d} "
          f"m={r['mean_sigma']:+.5f} t={r['t']:+6.2f} p={r['perm_p']:.4f} "
          f"gross={r['gross_bps_per_rebal']:+7.2f}bps turn={r['turnover']:.2f} "
          f"BE={r['breakeven_bps_leg']:+7.2f} yrs={r['pos_years']}/{r['tot_years']} "
          f"SR={r['sharpe_ann']:+.2f}", flush=True)

df = pd.DataFrame(rows)
df.to_json(f"{OUT}/S3_ANCHOR_GRID.json", orient="records", indent=1)
json.dump({k: v for k, v in series.items()}, open(f"{OUT}/S3_SERIES.json", "w"))
print("\nwritten", f"{OUT}/S3_ANCHOR_GRID.json")
