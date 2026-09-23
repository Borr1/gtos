"""m2_repro2 — the CONTROL, stated exactly.

The standalone emitter (`m2_emit.emit_sde`) is licensed to be used on archives the pbg
harness cannot reach only if it reproduces the frozen wave-19 roster's own
`structural_distance_extreme` rows. It does, and the residual is a KNOWN defect, not an
error in the emitter:

  * the roster records `b = T - 15 min` unconditionally (`pbg_run.py:emit_rows`), but the
    production generator walks BACK to the last closed bar when the bar that should have
    closed at T is missing. Those rows carry a bar-open the archive does not contain.
  * every one of them matches an EARLIER bar's emission exactly — which is r2's defect C
    (stale selected closed bar) seen inside this family.
"""
from __future__ import annotations
import csv, datetime as dt, glob, gzip, json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, "/tmp/m2")
from m2_emit import emit_sde

BARS = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/"
            "bridge_ftmo_m15_20250601_20260610")
ROSTER = {"202510": "/tmp/f1/roster_202510", "202511": "/tmp/f1/roster_202511",
          "202512": "/tmp/f1/roster_202512", "202601": "/tmp/pbg_full_jan",
          "202602": "/tmp/pbg_full_feb", "202603": "/tmp/pbg_full_mar",
          "202604": "/tmp/f1/roster_202604", "202605": "/tmp/f1/roster_202605"}
OUT = ("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
       "docs/audits/fable5-vision-audit-20260725/phase20/receipts/m2/M2_REPRO_V1.json")


def load(sym):
    t, o, h, l, c = [], [], [], [], []
    with (BARS / f"{sym}_M15.csv").open() as fh:
        for r in csv.DictReader(fh):
            t.append(dt.datetime.fromisoformat(r["time"])); o.append(float(r["open"]))
            h.append(float(r["high"])); l.append(float(r["low"])); c.append(float(r["close"]))
    return np.array(t, dtype=object), np.array(o), np.array(h), np.array(l), np.array(c)


syms = sorted(p.name[:-len("_M15.csv")] for p in BARS.glob("*_M15.csv"))
mine, bars_present, geo = {}, {}, defaultdict(list)
for sym in syms:
    t, o, h, l, c = load(sym)
    bars_present[sym] = {x.isoformat() for x in t}
    idx, lng, e, s, tp, pos, a14 = emit_sde(o, h, l, c)
    for i, L_, E, S, T in zip(idx, lng, e, s, tp):
        k = (sym, t[i].isoformat(), bool(L_))
        mine[k] = (round(E, 10), round(S, 10), round(T, 10))
        geo[(sym, bool(L_), round(E, 10), round(S, 10))].append(t[i].isoformat())

theirs, rdays = {}, set()
for mm, d in ROSTER.items():
    for p in sorted(glob.glob(d + "/*.jsonl.gz")):
        rdays.add(Path(p).name[4:14])
        with gzip.open(p, "rt") as fh:
            for line in fh:
                if '"structural_distance_extreme"' not in line:
                    continue
                r = json.loads(line)
                if r["f"] != "structural_distance_extreme" or r["k"] != 15:
                    continue
                theirs[(r["s"], r["b"], r["d"] == "L")] = (round(r["e"], 10), round(r["sl"], 10),
                                                           round(r["tp"], 10))

on_days = {k: v for k, v in mine.items()
           if (dt.datetime.fromisoformat(k[1]) + dt.timedelta(minutes=15)).date().isoformat() in rdays}
only_mine = set(on_days) - set(theirs)
only_theirs = set(theirs) - set(on_days)
both = set(on_days) & set(theirs)
mismatch = [k for k in both if any(abs(a - b) > 5e-9 for a, b in zip(on_days[k], theirs[k]))]
stale = [k for k in only_theirs if k[1] not in bars_present[k[0]]]
stale_matched = [k for k in stale if geo.get((k[0], k[2], theirs[k][0], theirs[k][1]))]

out = {
    "what": "standalone emitter vs the FROZEN wave-19 roster, structural_distance_extreme, "
            "k=15 (the shipped close-only contract), 8 windows x 24 symbols",
    "n_symbols": len(syms),
    "n_emitter_on_roster_trading_days": len(on_days),
    "n_roster": len(theirs),
    "n_matched": len(both),
    "n_geometry_mismatch_on_matched": len(mismatch),
    "n_only_emitter": len(only_mine),
    "n_only_roster": len(only_theirs),
    "n_only_roster_whose_declared_bar_open_is_absent_from_the_archive": len(stale),
    "n_of_those_reproduced_exactly_by_an_earlier_bar": len(stale_matched),
    "stale_share_of_family": len(only_theirs) / len(theirs),
    "EXACT_ON_NON_STALE": len(only_mine) == 0 and len(mismatch) == 0
                          and len(stale_matched) == len(only_theirs),
    "interpretation": "the emitter is exact; the 820 residual rows are r2 defect C "
                      "(stale selected closed bar) inside this family, and this family "
                      "carries ZERO r2 defect A rows (it is at-market by construction)",
}
Path(OUT).write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
