"""r2_regen — regenerate the eight-window roster under a NAMED emission policy.

Drives the committed Session-PB harness (`phase19/receipts/pbg/pbg_run.py`) and
the unmodified production generator, injecting only the
``gtos_vnext_runtime.broad_origin_*`` keys.  Two arms:

  legacy  — the pre-repair contract via the escape hatch (must reproduce the
            frozen wave-19 roster exactly)
  default — HEAD defaults (what the repair ships)

Usage: python3 r2_regen.py <legacy|default|gapr> <month> <workers> <outdir>
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, PBG)
sys.path.insert(0, REPO)

import pbg_run as R  # noqa: E402
import pbg_lib as L  # noqa: E402

from src.components.broad_origin_emission_contract import (  # noqa: E402
    MAX_ADMISSION_GAP_R_KEY,
    MAX_SELECTED_BAR_AGE_PERIODS_KEY,
    REFUSE_PAST_STOP_KEY,
)

ARMS = {
    # the escape hatch, set to the pre-repair contract
    "legacy": {
        REFUSE_PAST_STOP_KEY: False,
        MAX_ADMISSION_GAP_R_KEY: None,
        MAX_SELECTED_BAR_AGE_PERIODS_KEY: None,
    },
    # HEAD defaults, stated explicitly so the arm is self-describing
    "default": {
        REFUSE_PAST_STOP_KEY: True,
        MAX_ADMISSION_GAP_R_KEY: None,
        MAX_SELECTED_BAR_AGE_PERIODS_KEY: 1.0,
    },
    # the far-side R radius at the candidate's own reward-to-risk
    "gapr": {
        REFUSE_PAST_STOP_KEY: True,
        MAX_ADMISSION_GAP_R_KEY: 1.5,
        MAX_SELECTED_BAR_AGE_PERIODS_KEY: 1.0,
    },
    # each defect isolated, so the blast radius decomposes
    "stale_only": {
        REFUSE_PAST_STOP_KEY: False,
        MAX_ADMISSION_GAP_R_KEY: None,
        MAX_SELECTED_BAR_AGE_PERIODS_KEY: 1.0,
    },
    "paststop_only": {
        REFUSE_PAST_STOP_KEY: True,
        MAX_ADMISSION_GAP_R_KEY: None,
        MAX_SELECTED_BAR_AGE_PERIODS_KEY: None,
    },
}

_ORIG = R.build_day_context


def patched(symbols, day, min_rr, m1_months):
    sources, m1, scfg = _ORIG(symbols, day, min_rr, m1_months)
    overrides = ARMS[ARM]
    for sym, cfg in scfg.items():
        runtime = cfg.setdefault("gtos_vnext_runtime", {})
        runtime.update(overrides)
    return sources, m1, scfg


if __name__ == "__main__":
    ARM = sys.argv[1]
    month = sys.argv[2]
    workers = int(sys.argv[3])
    out = Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    R.build_day_context = patched
    globals()["ARM"] = ARM
    R.__dict__["build_day_context"] = patched

    if len(sys.argv) > 5:
        days = [x for x in sys.argv[5].split(",") if x]
    else:
        y, m = int(month[:4]), int(month[4:])
        d = datetime(y, m, 1, tzinfo=timezone.utc)
        days = []
        while d.month == m:
            if d.weekday() < 5 and d.date().isoformat() not in R.HOLIDAYS:
                days.append(d.date().isoformat())
            d += timedelta(days=1)

    import multiprocessing as mp

    class Job:
        def __init__(self, symbols, out_dir, min_rr, arm):
            self.a = (symbols, out_dir, min_rr, arm)

        def __call__(self, day):
            symbols, out_dir, min_rr, arm = self.a
            globals()["ARM"] = arm
            R.build_day_context = patched
            return R.run_day(
                day, symbols=symbols, minutes=[], out_dir=out_dir,
                min_rr=min_rr, m1_months=[],
            )

    syms = list(L.SYMBOLS)
    with mp.get_context("fork").Pool(workers) as pool:
        for st in pool.imap_unordered(Job(syms, out, 1.5, ARM), days):
            print(json.dumps(st), flush=True)
    print("ARM_DONE", ARM, month, flush=True)
