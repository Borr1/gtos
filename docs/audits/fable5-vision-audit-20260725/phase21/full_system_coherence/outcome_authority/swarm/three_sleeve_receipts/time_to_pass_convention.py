#!/usr/bin/env python3
"""`median_calendar_days_to_pass` is in WEEKDAY SESSIONS, not calendar days. Measured.

Measurement only.

`mc_firm_rules._derived` computes
    median_calendar_days_to_pass = med_days_pass * weekday_sessions / book_days
and `weekday_sessions(a, b)` (`mc_firm_rules.py:245-247`) counts only `weekday() < 5`. So the
published field is a count of WEEKDAY sessions wearing a calendar label, and it understates
true elapsed time. `SURVIVOR_BOOK_V1.json`, `BOOKS_MC_V1.json` and
`LIVE_BOOK_INTEGRITY_V1.md` §1.3 ("48 -> 112 days") all quote it.

`W7_INSTRUMENT_RESTATEMENT_V1.md` §1.6 quotes the OTHER convention for the same cell --
`med_days_pass / book_days_per_calendar_month * 30.4369` -> 89 days where `_derived` gives 57.
**Two conventions, one name, differing by ~1.56x on the same cell.** This restates every
time-to-pass figure in `THREE_SLEEVE_BOOK_RESTATEMENT_V1.md` on the calendar convention, with
the weekday-session value alongside so a reader can reconcile either published source.

Usage: python3 time_to_pass_convention.py [book.json] [out.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "THREE_SLEEVE_BOOK_V1.json"
DEST = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "TIME_TO_PASS_CONVENTION_V1.json"
DAYS_PER_MONTH = 30.4369

D = json.loads(BOOK.read_text())
out = {
    "schema": "gtos.wave21.time_to_pass_convention.v1",
    "measurement_only": True,
    "defect": ("mc_firm_rules._derived names its output `median_calendar_days_to_pass` but "
               "builds it from `weekday_sessions`, which counts weekday() < 5 only "
               "(mc_firm_rules.py:245-247). It is a weekday-session count, not calendar days."),
    "conventions": {
        "weekday_sessions_AS_PUBLISHED": "med_days_pass * weekday_sessions / book_days",
        "calendar_days_TRUE": "med_days_pass / book_days_per_calendar_month * 30.4369",
    },
    "cells": {},
}

for key, c in D["cells"].items():
    bd, wds, bdpm = c["book_days"], c["weekday_sessions"], c["book_days_per_month"]
    mbd = c["uncorrected"]["median_book_days_to_pass"]
    if not mbd:
        continue
    # ratio converting a weekday-session figure into calendar days for THIS cell
    ratio = (DAYS_PER_MONTH * bd) / (bdpm * wds)
    ci = c["corrected_instrument"].get("median_calendar_days_to_pass") or {}
    row = {
        "book_days": bd, "weekday_sessions_in_span": wds,
        "book_days_per_calendar_month": bdpm,
        "median_book_days_to_pass": mbd,
        "as_published_weekday_sessions": round(mbd * wds / bd),
        "TRUE_calendar_days_uncorrected": round(mbd / bdpm * DAYS_PER_MONTH),
        "weekday_to_calendar_ratio_this_cell": round(ratio, 4),
    }
    if ci.get("median") is not None:
        row["TRUE_calendar_days_corrected"] = {
            "median": round(ci["median"] * ratio),
            "p2_5": round(ci["p2_5"] * ratio),
            "p97_5": round(ci["p97_5"] * ratio),
        }
        row["as_published_weekday_sessions_corrected"] = {
            "median": round(ci["median"]), "p2_5": round(ci["p2_5"]),
            "p97_5": round(ci["p97_5"])}
    out["cells"][key] = row

DEST.write_text(json.dumps(out, indent=1))
print("WROTE", DEST)
for k, v in out["cells"].items():
    tc = v.get("TRUE_calendar_days_corrected", {})
    print(f"{k:52s} med_book_days={v['median_book_days_to_pass']:3d}  "
          f"as_published(weekday)={v['as_published_weekday_sessions']:4d}  "
          f"TRUE calendar unc={v['TRUE_calendar_days_uncorrected']:4d}  "
          f"corrected={tc.get('median')} [{tc.get('p2_5')}, {tc.get('p97_5')}]  "
          f"ratio={v['weekday_to_calendar_ratio_this_cell']}")
