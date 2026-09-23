#!/usr/bin/env python3
"""Phase 0 control — the ORIGINAL arm must reproduce the sealed labels exactly.

If this does not hold bit-for-bit, nothing else in Phase 0 is admissible: the
inverted arm is only trustworthy because it is the same function of the same
inputs with one argument triple changed.
"""
from __future__ import annotations

import gzip
import json
import pickle
from pathlib import Path

OUT = Path("/private/tmp/phase0-inversion")
CACHE = Path("/private/tmp/w21-puzzle-cache")
MONTHS = ("feb", "apr", "may", "jun", "jul")


def main():
    report = {
        "control": "walk ORIG arm vs the sealed w21-puzzle-cache rows",
        "sealed_cache": str(CACHE),
        "per_month": {},
    }
    total = mismatch = 0
    for month in MONTHS:
        walk = pickle.load(gzip.open(OUT / f"walk_{month}.pkl.gz", "rb"))
        cache = {
            row["candidate_occurrence_key"]: row
            for row in pickle.load(gzip.open(CACHE / f"rows_{month}.pkl.gz", "rb"))
        }
        compared = status_ok = net_ok = missing = 0
        worst = 0.0
        for rec in walk:
            sealed = cache.get(rec["key"])
            if sealed is None:
                missing += 1
                continue
            compared += 1
            status_ok += sealed["lifecycle_label_status"] == rec["orig"]["status"]
            a, b = sealed["terminal_net_r"], rec["orig"]["net"]
            if a is None and b is None:
                net_ok += 1
            elif a is not None and b is not None:
                worst = max(worst, abs(a - b))
                net_ok += abs(a - b) == 0.0
        report["per_month"][month] = {
            "walk_rows": len(walk),
            "compared": compared,
            "missing_from_cache": missing,
            "lifecycle_status_identical": status_ok,
            "terminal_net_r_identical": net_ok,
            "max_abs_net_difference": worst,
            "PASS": compared > 0
            and status_ok == compared
            and net_ok == compared
            and missing == 0,
        }
        total += compared
        mismatch += (compared - status_ok) + (compared - net_ok) + missing
    report["total_compared"] = total
    report["total_mismatches"] = mismatch
    report["PASS"] = mismatch == 0 and total > 0
    path = OUT / "receipts/P0_CONTROL.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps(report["per_month"], indent=1, sort_keys=True))
    print("TOTAL", total, "MISMATCHES", mismatch, "PASS", report["PASS"])


if __name__ == "__main__":
    main()
