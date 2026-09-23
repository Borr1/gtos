#!/usr/bin/env python3
"""Puzzle autopsy stage 1: build the five-month population cache.

Loads Feb/Apr/May/Jun/Jul full candidate populations (features + labels) through
the frozen r2 loader chain, fits the frozen ridge at each month boundary on the
frozen prequential protocol (training = everything before that month, in read
order), predicts every eligible row of the month, and dumps per-month gzip
pickles + a compact summary. Post-read autopsy — all five months are read.
"""
import gzip
import json
import pickle
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
OA = WT / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
sys.path.insert(0, str(WT))
sys.path.insert(0, str(OA))

import importlib.util


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


r4 = load_module("r4d_frozen", OA / "w21_score_junjul_r4d.py")
r3 = r4.r3
s2 = r4.s2
r = r4.r

HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST_DIR = HOLD / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"
OUT = Path("/private/tmp/w21-puzzle-cache")
OUT.mkdir(exist_ok=True)

prereg = json.loads((OA / "JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1_3.json").read_text())
tr = prereg["training"]
WINDOWS = [
    ("feb", FEB_ROOT := Path("/private/tmp/w21-market-top-feb-r2"), "february_2026",
     tr["february_manifest_root_sha256"], tr["february_days"]),
    ("apr", Path("/private/tmp/w21-market-top-aprmay-r3"), "april_2026",
     tr["april_manifest_root_sha256"], tr["april_days"]),
    ("may", Path("/private/tmp/w21-market-top-aprmay-r3"), "may_2026",
     tr["may_manifest_root_sha256"], tr["may_days"]),
    ("jun", Path("/private/tmp/w21-market-top-junjul-r4"), "june_2026",
     next(w["manifest_root_sha256"] for w in prereg["validation"]["windows"] if w["window_id"] == "june_2026"),
     next(w["days"] for w in prereg["validation"]["windows"] if w["window_id"] == "june_2026")),
    ("jul", Path("/private/tmp/w21-market-top-junjul-r4"), "july_2026",
     next(w["manifest_root_sha256"] for w in prereg["validation"]["windows"] if w["window_id"] == "july_2026"),
     next(w["days"] for w in prereg["validation"]["windows"] if w["window_id"] == "july_2026")),
]

T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


# ---- training bootstrap (dev + january), as the frozen protocol ---------------
initial, january = r.load_all()
training = r.resolved_eligible(initial)
for day, _authority in r.j.JAN_RUNS:
    training.extend(r.resolved_eligible(january[day]))
log(stage="bootstrap", training_rows=len(training))

summary = {}
old_root = s2.ROOT
for month, root, window_id, expected_root, days in WINDOWS:
    root_sha, sources = r3.load_m1_sources(MANIFEST_DIR / f"{window_id}.json", expected_root)
    log(stage="m1_loaded", month=month)
    # month-boundary fit: train on everything read before this month
    model = r.make_model()
    train_y = np.asarray([float(row.get("terminal_net_r") or 0.0) for row in training], dtype=float)
    model.fit(r.frame(training), train_y, ridge__sample_weight=r.weights(training))
    month_rows = []
    s2.ROOT = root
    try:
        for day in days:
            _raw, rows, _summary = s2.load_day(day, root_sha, sources)
            test = r.eligible(rows)
            if test:
                predictions = model.predict(r.frame(test))
                for row, pred in zip(test, predictions):
                    row["pred_month_boundary"] = float(pred)
            for row in rows:
                row["month"] = month
            month_rows.extend(rows)
            training.extend(r.resolved_eligible(rows))
    finally:
        s2.ROOT = old_root
    del sources
    eligible = [row for row in month_rows if row.get("pred_month_boundary") is not None]
    resolved = [row for row in eligible if r.m.fit._state(row) is not None]
    summary[month] = {
        "occurrences": len(month_rows),
        "eligible": len(eligible),
        "resolved_eligible": len(resolved),
        "families": dict(Counter(row["origin_family"] for row in month_rows)),
        "training_rows_at_fit": int(len(train_y)),
    }
    with gzip.open(OUT / f"rows_{month}.pkl.gz", "wb") as fh:
        pickle.dump(month_rows, fh, protocol=5)
    log(stage="month_done", month=month, **{k: v for k, v in summary[month].items() if k != "families"})

(OUT / "build_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
log(stage="ALL_DONE", out=str(OUT))
