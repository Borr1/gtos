#!/usr/bin/env python3
"""B2 step 0: materialize the dev+January bootstrap training rows ONCE.

The sealed prequential chain starts from `w21_predecision_ridge.load_all()`
(dev runs + the 16 January days), which costs ~470 s of sealed-sink reads.
Lane 3's `step2_daily_refit.py` pays it on every run; this pays it once and
caches the compact rows (CAT + NUM + label fields only) to scratch so the
composed-rule walk can be re-run cheaply.

Writes: bootstrap_rows.pkl.gz  -> list[dict], already `resolved_eligible`.
"""
import gzip
import importlib.util
import json
import pickle
import sys
import time
from pathlib import Path

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/b2")
OUT.mkdir(parents=True, exist_ok=True)
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def lm(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


r = lm("w21_predecision_ridge_b2", Path("/private/tmp/w21_predecision_ridge.py"))

KEEP = tuple(r.CAT) + tuple(r.NUM) + (
    "candidate_occurrence_key", "decision_window_id", "trading_day",
    "label_span_start_utc", "label_span_end_utc", "expiry_utc",
    "lifecycle_label_status", "cost_label_status", "terminal_net_r",
    "predecision_geometry_valid",
)


def compact(row):
    return {k: row.get(k) for k in KEEP}


initial, january = r.load_all()
log(stage="loaded", initial=len(initial), january_days=len(january))

training = [compact(row) for row in r.resolved_eligible(initial)]
for day, _authority in r.j.JAN_RUNS:
    training.extend(compact(row) for row in r.resolved_eligible(january[day]))

with gzip.open(OUT / "bootstrap_rows.pkl.gz", "wb") as fh:
    pickle.dump(training, fh, protocol=5)
log(stage="DONE", bootstrap_training_rows=len(training))
