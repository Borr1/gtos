#!/usr/bin/env python3
"""B3 step 0 -- materialise the frozen bootstrap training corpus ONCE.

The sealed prequential chain trains on ``dev (Oct/Nov 2025) + January 2026``
before it ever sees February.  ``w21_predecision_ridge.load_all`` rebuilds that
corpus from the sealed replay sinks in ~540 s.  Every downstream arm needs the
same corpus, so it is built once here and pickled.

Read-only with respect to everything: it opens sealed sinks through
``ReplayCompactEventSink.open_sealed`` (hash-verified) and writes a single
pickle under the job scratch.  No repo file, no config, no broker.
"""
from __future__ import annotations

import importlib.util
import json
import pickle
import sys
import time
from pathlib import Path

SCRATCH = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/b3")
OUT = SCRATCH / "out"
OUT.mkdir(parents=True, exist_ok=True)
T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ridge = load_module("w21_predecision_ridge_b3", Path("/private/tmp/w21_predecision_ridge.py"))
    log(stage="module_loaded")
    initial, january = ridge.load_all()
    log(stage="loaded", initial=len(initial), january_days=len(january),
        january_rows=sum(len(v) for v in january.values()))
    payload = {
        "initial": initial,
        "january": january,
        "jan_runs": [day for day, _authority in ridge.j.JAN_RUNS],
        "cat": list(ridge.CAT),
        "num": list(ridge.NUM),
    }
    with (OUT / "bootstrap_rows.pkl").open("wb") as fh:
        pickle.dump(payload, fh, protocol=5)
    log(stage="DONE", path=str(OUT / "bootstrap_rows.pkl"))


if __name__ == "__main__":
    main()
