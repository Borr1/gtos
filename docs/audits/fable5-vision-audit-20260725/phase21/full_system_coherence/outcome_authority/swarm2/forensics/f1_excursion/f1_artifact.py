#!/usr/bin/env python3
"""Write the F1 per-trade census artifact (parquet + gzipped JSONL) and its schema doc."""
import gzip, json, pickle, sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DEST = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out"
DEST.mkdir(parents=True, exist_ok=True)
MONTHS = ["feb", "apr", "may", "jun", "jul"]

frames = []
for m in MONTHS:
    frames.append(pd.DataFrame.from_records(
        pickle.load(gzip.open(HERE / f"f1walk_{m}.pkl.gz", "rb"))))
df = pd.concat(frames, ignore_index=True)

# stable column order: identity -> contract -> outcome -> excursion -> path -> ladder
ident = ["k", "month", "trading_day", "symbol", "family", "order_type", "side", "session",
         "utc_hour", "weekday"]
contract = ["entry_price", "stop_price", "target_price", "fill_price", "risk_price",
            "stop_r", "target_r", "entry_slip_r", "fill_at_open", "sub_min", "fill_min",
            "horizon_min", "fill_delay_min", "first_gap_min", "gapped",
            "risk_over_atr", "atr14_over_atr50", "vol_8_over_48", "risk_frac_entry"]
outcome = ["sealed_status", "exit_kind", "gross_r", "cost_r", "net_r", "sealed_net_r",
           "spread_r", "slippage_r", "swap_r", "commission_r",
           "exit_min", "hold_min", "exit_idx"]
exc = ["mfe_r", "mae_r", "t_mfe_min", "t_mae_min", "mfe_bar_idx", "mae_bar_idx",
       "mae_before_mfe", "mfe_pre_exit_r", "mae_pre_exit_r", "giveback_r",
       "mae_headroom_r", "mfe_headroom_r",
       "mfe_full_r", "mae_full_r", "t_mfe_full_min", "t_mae_full_min", "close_full_r",
       "full_gapped", "mfe5_r", "mae5_r", "mfe15_r", "mae15_r", "mfe30_r", "mae30_r",
       "mfe60_r", "mae60_r", "mfe_ext_r", "mae_ext_r", "ext_bars"]
reach = [c for c in df.columns if c.startswith("reach_") or c.startswith("reachpre_")]
path = ["p%d" % (i * 10) for i in range(1, 11)]
lad = [c for c in df.columns if c.startswith("t0p") or c.startswith("t1") or
       c.startswith("t2") or c.startswith("t3")]
cols = ident + contract + outcome + exc + reach + path + sorted(lad)
missing = [c for c in cols if c not in df.columns]
extra = [c for c in df.columns if c not in cols]
assert not missing, "missing columns: %s" % missing
df = df[cols + extra]

# The occurrence key is a 76-char string carrying a 12-char constant prefix; the sealed
# corpus's own identifier is the hex suffix (candidate_funnel_analysis.py:200-202 does the
# same removeprefix). Storing the suffix keeps the join exact and halves the key column.
df["k"] = df["k"].str.removeprefix("candidate_occurrence_")
for c in ("month", "symbol", "family", "order_type", "side", "session", "trading_day",
          "sealed_status", "exit_kind"):
    df[c] = df[c].astype("category")
for c in df.columns:
    if str(df[c].dtype) == "object" and c.endswith(("_kind", "_kindE")):
        df[c] = df[c].astype("category")
for c in df.columns:
    if str(df[c].dtype) == "float64" and c not in ("entry_price", "stop_price", "target_price",
                                                   "fill_price", "risk_price"):
        df[c] = df[c].astype("float32")     # excursion R values: float32 is ~1e-7 relative,
                                            # four orders below the 1e-4 R reporting resolution
pq = DEST / "F1_TRADE_EXCURSION_CENSUS_V1.parquet"
df.to_parquet(pq, index=False, compression="zstd", compression_level=9)

import hashlib
meta = {
    "rows": int(len(df)), "columns": int(len(df.columns)),
    "months": MONTHS, "symbols": int(df["symbol"].nunique()),
    "families": int(df["family"].nunique()), "trading_days": int(df["trading_day"].nunique()),
    "parquet_bytes": pq.stat().st_size, "parquet_sha256": hashlib.sha256(pq.read_bytes()).hexdigest(),
    "column_list": list(df.columns),
    "dtypes": {c: str(t) for c, t in df.dtypes.items()},
}
json.dump(meta, open(DEST / "F1_ARTIFACT_MANIFEST.json", "w"), indent=1)
print(json.dumps({k: v for k, v in meta.items() if k not in ("column_list", "dtypes")}, indent=1))
