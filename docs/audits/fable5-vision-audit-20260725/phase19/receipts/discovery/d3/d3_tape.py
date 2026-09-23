"""d3 — M15 tape over the whole lane-input range, and the contract walker.

M15 is the right resolution: every contract under test has a horizon >= 2 h, the live
sleeves decide on H4/D1, and the M15 CSVs are contiguous 2025-06-01..2026-06-10 so a
320-hour horizon opened at month end still walks forward across the month boundary --
which an M1 per-month tape cannot do.
"""
from __future__ import annotations
import csv, gzip, glob, json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np

BARS = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
M15_DIR = BARS/"bridge_ftmo_m15_20250601_20260610"
T0 = datetime(2025,6,1,tzinfo=timezone.utc)
T1 = datetime(2026,6,11,tzinfo=timezone.utc)
NBAR = int((T1-T0).total_seconds()//900)

class M15Tape:
    def __init__(self, symbols):
        self.n=NBAR; self.t0=T0
        self.h={}; self.l={}; self.c={}
        for sym in symbols:
            p = M15_DIR/f"{sym}_M15.csv"
            h=np.full(NBAR,np.nan); l=np.full(NBAR,np.nan); c=np.full(NBAR,np.nan)
            if p.is_file():
                with p.open() as fh:
                    for row in csv.DictReader(fh):
                        ts=datetime.fromisoformat(row["time"])
                        i=int((ts-T0).total_seconds()//900)
                        if 0<=i<NBAR:
                            h[i]=float(row["high"]); l[i]=float(row["low"]); c[i]=float(row["close"])
            self.h[sym]=h; self.l[sym]=l; self.c[sym]=c
    def idx(self, iso):
        return int((datetime.fromisoformat(iso)-T0).total_seconds()//900)

AT_MARKET = ("displacement_continuation","liquidity_sweep_reclaim","structural_distance_extreme",
             "volatility_compression_expansion","session_open_range_break","regime_transition_break",
             "cross_asset_lead_lag")
POI = ("current_fvg_fill","current_ob_retest","current_breaker_re_entry")

def setup_key(r):
    if r["f"].startswith("current_"):
        return (r["s"], r["f"], r["d"], r["b"], r["cid"])
    return (r["s"], r["f"], r["d"], r["b"])

def load_close_rows(indir, families):
    seen={}
    for p in sorted(glob.glob(os.path.join(indir,"pbg_*.jsonl.gz"))):
        with gzip.open(p,"rt") as fh:
            for line in fh:
                r=json.loads(line)
                if r["k"]!=15 or r["f"] not in families: continue
                k=setup_key(r)
                if k not in seen: seen[k]=r
    return list(seen.values())

WINDOWS = {
 "2025-10":"/tmp/f2_close_202510", "2025-11":"/tmp/f2_close_202511", "2025-12":"/tmp/f2_close_202512",
 "2026-01":"/tmp/pbg_full_jan", "2026-02":"/tmp/pbg_full_feb", "2026-03":"/tmp/pbg_full_mar",
 "2026-04":"/tmp/f2_close_202604", "2026-05":"/tmp/f2_close_202605",
}
