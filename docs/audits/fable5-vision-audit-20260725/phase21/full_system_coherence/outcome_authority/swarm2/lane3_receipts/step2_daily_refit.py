#!/usr/bin/env python3
"""LANE 3 step 2: reproduce the EXACT sealed prequential daily refit.

The three sealed reads chain: feb r2 trains on dev+January then walks February
day by day; aprmay r3 continues with April then May; junjul r4 continues with
June then July.  A single continuous prequential pass over
feb -> apr -> may -> jun -> jul, extending training with
``r.resolved_eligible(rows)`` after each day, reproduces all three.

Rows come from the puzzle cache (population verified byte-exact against all
three sealed ``population`` blocks in step1).  Only the model fit is recomputed.
Writes {occurrence_key: prediction} to preds_daily.pkl.gz.
"""
import gzip
import importlib.util
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
OA = WT / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
CACHE = Path("/private/tmp/w21-puzzle-cache")
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane3/out")
OUT.mkdir(exist_ok=True)
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def lm(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


r = lm("w21_predecision_ridge_lane3", Path("/private/tmp/w21_predecision_ridge.py"))

prereg = json.loads((OA / "JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1_3.json").read_text())
tr = prereg["training"]
DAY_ORDER = [
    ("feb", tr["february_days"]),
    ("apr", tr["april_days"]),
    ("may", tr["may_days"]),
    ("jun", next(w["days"] for w in prereg["validation"]["windows"] if w["window_id"] == "june_2026")),
    ("jul", next(w["days"] for w in prereg["validation"]["windows"] if w["window_id"] == "july_2026")),
]

initial, january = r.load_all()
training = r.resolved_eligible(initial)
for day, _authority in r.j.JAN_RUNS:
    training.extend(r.resolved_eligible(january[day]))
del initial, january
log(stage="bootstrap", training_rows=len(training))

preds = {}
for month, days in DAY_ORDER:
    with gzip.open(CACHE / f"rows_{month}.pkl.gz", "rb") as fh:
        month_rows = pickle.load(fh)
    by_day = {}
    for row in month_rows:
        by_day.setdefault(row["trading_day"], []).append(row)
    del month_rows
    for day in days:
        rows = by_day.get(day, [])
        test = r.eligible(rows)
        if test:
            model = r.make_model()
            train_y = np.asarray(
                [float(row.get("terminal_net_r") or 0.0) for row in training], dtype=float
            )
            model.fit(r.frame(training), train_y, ridge__sample_weight=r.weights(training))
            predictions = model.predict(r.frame(test))
            for row, pred in zip(test, predictions):
                preds[row["candidate_occurrence_key"]] = float(pred)
        training.extend(r.resolved_eligible(rows))
        log(stage="day", month=month, day=day, n_test=len(test), training=len(training))
    del by_day

with gzip.open(OUT / "preds_daily.pkl.gz", "wb") as fh:
    pickle.dump(preds, fh, protocol=5)
log(stage="DONE", n_preds=len(preds))
