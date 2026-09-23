"""Compacted per-symbol M15 series: PRINTED bars only, which is what the live engine's
`_trading_m15_bars_since` counts (execution.py:8953-8958) and therefore what the live
sleeves' `time_stop_bars` means.  A 1280-bar time stop is 320 TRADING hours, not 320
calendar hours: weekends do not consume the budget."""
from __future__ import annotations
import csv
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

BARS = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
M15_DIR = BARS/"bridge_ftmo_m15_20250601_20260610"
T0 = datetime(2025,6,1,tzinfo=timezone.utc)

class CTape:
    def __init__(self, symbols):
        self.h={}; self.l={}; self.c={}; self.tmin={}
        for sym in symbols:
            p=M15_DIR/f"{sym}_M15.csv"
            th=[];tl=[];tc=[];tt=[]
            if p.is_file():
                with p.open() as fh:
                    for row in csv.DictReader(fh):
                        ts=datetime.fromisoformat(row["time"])
                        tt.append(int((ts-T0).total_seconds()//60))
                        th.append(float(row["high"])); tl.append(float(row["low"])); tc.append(float(row["close"]))
            self.h[sym]=np.array(th); self.l[sym]=np.array(tl); self.c[sym]=np.array(tc)
            self.tmin[sym]=np.array(tt,dtype=np.int64)
    def minutes(self, iso):
        return int((datetime.fromisoformat(iso)-T0).total_seconds()//60)
    def pos(self, sym, iso):
        """index of the first PRINTED bar stamped at or after the decision instant."""
        return int(np.searchsorted(self.tmin[sym], self.minutes(iso), side="left"))
