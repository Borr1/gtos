"""m2_tickcache — convert the lane-hold true-UTC tick JSONL to a compact binary cache.

Fields kept: ts (int64 ms since epoch, TRUE UTC from the row's own `time`), bid, ask.
The row's `time`/`ts_utc` are true UTC; `time_msc` is BROKER epoch (p3 §4.1) and is NOT used.
"""
from __future__ import annotations
import os, sys
from array import array
from datetime import datetime, timezone
import numpy as np

TICKS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
         "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/ticks")
OUT = "/tmp/m2/tickcache"
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_DAY = {}


def day_ms(ds: bytes) -> int:
    v = _DAY.get(ds)
    if v is None:
        d = datetime(int(ds[0:4]), int(ds[5:7]), int(ds[8:10]), tzinfo=timezone.utc)
        v = int((d - EPOCH).total_seconds()) * 1000
        _DAY[ds] = v
    return v


def convert(month: str, sym: str):
    p = f"{TICKS}/{month}/{sym}/microstructure_ticks.jsonl"
    if not os.path.isfile(p):
        return None
    dst = f"{OUT}/{sym}_{month}.npz"
    if os.path.isfile(dst):
        return dst
    ts, bd, ak = array('q'), array('d'), array('d')
    with open(p, "rb") as f:
        for line in f:
            try:
                i = line.index(b',', 7)
                a = float(line[7:i])
                j = line.index(b',', i + 7)
                b = float(line[i + 7:j])
                k = line.index(b'"time":"') + 8
                s = line[k:k + 26]
                t = (day_ms(s[0:10]) + int(s[11:13]) * 3600000 + int(s[14:16]) * 60000
                     + int(s[17:19]) * 1000 + int(s[20:23]))
            except Exception:
                continue
            ts.append(t); bd.append(b); ak.append(a)
    T = np.asarray(ts, dtype=np.int64); B = np.asarray(bd); A = np.asarray(ak)
    o = np.argsort(T, kind="stable")
    np.savez(dst + ".tmp.npz", ts=T[o], bid=B[o], ask=A[o])
    os.replace(dst + ".tmp.npz", dst)
    sys.stderr.write(f"{sym} {month} {len(T)} ticks\n")
    return dst


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    months = sys.argv[1].split(",")
    syms = sys.argv[2].split(",")
    for m in months:
        for s in syms:
            convert(m, s)
