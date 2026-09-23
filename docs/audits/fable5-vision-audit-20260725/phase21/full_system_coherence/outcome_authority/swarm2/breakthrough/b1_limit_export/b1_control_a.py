#!/usr/bin/env python3
"""CONTROL A — export fidelity.

B1's exporter must reproduce Lane G's price-bearing output exactly on the MARKET arm, otherwise the
LIMIT export it produces is not comparable to the adjudication's MARKET measurement.

Compares, key by key, every field the slippage measurement reads:
  state, status, gross, fill_price, fill_time, terminal_time, entry/stop/target/risk.
"""
from __future__ import annotations

import gzip
import json
import pickle

OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b1"
FIELDS_TOP = ["symbol", "side", "family", "day", "order_type",
              "entry_price", "stop_price", "target_price", "risk_price"]
FIELDS_ORIG = ["status", "state", "gross", "fill_price", "fill_time", "terminal_time"]

R = {"schema": "b1_control_a_export_fidelity", "months": {}}
tot = dict(n_lg=0, n_b1=0, matched=0, mismatched=0, only_lg=0, only_b1=0)
worst = []

for m in ["jun", "jul"]:
    lg = {r["key"]: r for r in pickle.load(gzip.open(f"/private/tmp/laneG-walk/lg_{m}.pkl.gz", "rb"))}
    b1 = {r["key"]: r for r in pickle.load(gzip.open(f"{OUT}/b1_market_{m}.pkl.gz", "rb"))}
    shared = set(lg) & set(b1)
    mism = 0
    field_mismatch = {}
    for k in shared:
        a, b = lg[k], b1[k]
        bad = []
        for f in FIELDS_TOP:
            if a.get(f) != b.get(f):
                bad.append(f)
        for f in FIELDS_ORIG:
            va, vb = (a.get("orig") or {}).get(f), (b.get("orig") or {}).get(f)
            if isinstance(va, float) and isinstance(vb, float):
                if not (va == vb or abs(va - vb) < 1e-12):
                    bad.append("orig." + f)
            elif str(va) != str(vb):
                bad.append("orig." + f)
        if bad:
            mism += 1
            for f in bad:
                field_mismatch[f] = field_mismatch.get(f, 0) + 1
            if len(worst) < 5:
                worst.append({"key": k, "fields": bad,
                              "lg": {f: str((a.get('orig') or {}).get(f)) for f in FIELDS_ORIG},
                              "b1": {f: str((b.get('orig') or {}).get(f)) for f in FIELDS_ORIG}})
    R["months"][m] = dict(n_lg=len(lg), n_b1=len(b1), shared=len(shared),
                          only_lg=len(set(lg) - set(b1)), only_b1=len(set(b1) - set(lg)),
                          mismatched_rows=mism, field_mismatch=field_mismatch)
    tot["n_lg"] += len(lg); tot["n_b1"] += len(b1)
    tot["matched"] += len(shared) - mism; tot["mismatched"] += mism
    tot["only_lg"] += len(set(lg) - set(b1)); tot["only_b1"] += len(set(b1) - set(lg))

R["totals"] = tot
R["examples"] = worst
R["verdict"] = ("EXACT" if tot["mismatched"] == 0 and tot["only_lg"] == 0 and tot["only_b1"] == 0
                else "DIFFERS")
json.dump(R, open(f"{OUT}/B1_CONTROL_A.json", "w"), indent=1)
print(json.dumps(R, indent=1)[:4000])
