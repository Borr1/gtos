#!/usr/bin/env python3
"""B3 step 1 -- build the master dataset once and cache it.

Eligible rows only (the funnel's own G0+G1), chain-ordered:
  bootstrap (Oct/Nov 2025 dev + January 2026) then feb, apr, may, jun, jul.
Emits meta (compact per-row dicts), the F0+F1 feature frame, and day indices.
"""
from __future__ import annotations

import json
import pickle
import time
from collections import defaultdict

import b3_lib as L

T0 = time.time()


def main() -> None:
    meta, frame, info = L.load_dataset()
    print(json.dumps({"t": round(time.time() - T0, 1), "stage": "loaded", **info}), flush=True)
    frame = L.add_regime_features(meta, frame)
    print(json.dumps({"t": round(time.time() - T0, 1), "stage": "regime",
                      "cols": len(frame.columns)}), flush=True)

    by_cday = defaultdict(list)
    for i, m in enumerate(meta):
        by_cday[m["cday"]].append(i)
    payload = {"meta": meta, "frame": frame, "by_cday": dict(by_cday), "info": info,
               "cdays": sorted(by_cday)}
    with (L.OUT / "dataset.pkl").open("wb") as fh:
        pickle.dump(payload, fh, protocol=5)
    counts = {m: 0 for m in ("boot", "jan") + L.MONTHS}
    for m in meta:
        counts[m["month"]] += 1
    print(json.dumps({"t": round(time.time() - T0, 1), "stage": "DONE",
                      "rows_by_month": counts, "n_days": len(by_cday)}), flush=True)


if __name__ == "__main__":
    main()
