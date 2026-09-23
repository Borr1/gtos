#!/usr/bin/env python3
"""Three-month postmortem — stage 8: the frozen rule's January, reproduced with family split.

The rule of record carries January only as a headline (development_finding: 52 selected,
+10.536 R). Family scope needs January's family split under THE FROZEN RULE (not the
source-features ridge arm, whose January is a different selection). This replays the
prequential exactly as the rule describes — Oct/Nov bootstrap, then day-by-day January —
using the same frozen module chain, and verifies the headline before reporting the split.

Writes RECEIPTS/PM_JAN_FROZEN_RULE_V1.json.
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

RECEIPTS = Path(__file__).resolve().parent
OA = RECEIPTS.parent
CACHE = Path("/private/tmp/w21-postmortem-cache-20260811")


def load_module(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


T0 = time.time()


def log(**kw):
    print(json.dumps({"t": round(time.time() - T0, 1), **kw}, sort_keys=True), flush=True)


log(stage="loading_module_chain")
r3b = load_module("pm_jan_r3b", OA / "w21_score_aprmay_r3b.py")
s2 = r3b.s2
r = r3b.r
m = r.m
j = r.j


def read_rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh]
    # cache round-trip stores NaN as None; the frozen frame() expects float NaN in NUM
    nan = float("nan")
    for row in rows:
        for key in r.NUM:
            if row.get(key) is None:
                row[key] = nan
    return rows


def main() -> None:
    octnov = read_rows(CACHE / "rows_octnov.jsonl.gz")
    jan = read_rows(CACHE / "rows_jan.jsonl.gz")
    jan_by_day = defaultdict(list)
    for row in jan:
        jan_by_day[row["trading_day"]].append(row)

    training = r.resolved_eligible(octnov)
    selected_all, day_summaries = [], {}
    for day, _authority in j.JAN_RUNS:
        rows = jan_by_day[day]
        test = r.eligible(rows)
        model = r.make_model()
        train_y = np.asarray(
            [float(row.get("terminal_net_r") or 0.0) for row in training], dtype=float
        )
        model.fit(r.frame(training), train_y, ridge__sample_weight=r.weights(training))
        predictions = model.predict(r.frame(test))
        chosen, dispositions = s2.select(test, predictions, policy="market_top_abstain")
        day_summaries[day] = {
            "dispositions": dispositions,
            "portfolio": s2.summary(chosen),
        }
        selected_all.extend(chosen)
        training.extend(r.resolved_eligible(rows))
        log(scored=day, trades=dispositions.get("trade", 0))

    pooled = s2.summary(selected_all)
    development_finding = json.loads(
        (OA / "MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json").read_text()
    )["development_finding"]
    lsr = [row for row in selected_all if row["origin_family"] == "liquidity_sweep_reclaim"]
    lsr_by_day = defaultdict(float)
    for row in lsr:
        if m.fit._state(row) is not None:
            lsr_by_day[row["trading_day"]] += float(row.get("terminal_net_r") or 0.0)
    receipt = {
        "schema": "gtos.wave21.postmortem.jan_frozen_rule.v1",
        "status": "DEVELOPMENT_DIAGNOSTIC_REPRODUCTION_OF_THE_RULE_OF_RECORD_JANUARY",
        "verification_vs_development_finding": {
            "selected_mine": pooled["selected"],
            "selected_recorded": development_finding["selected"],
            "actual_net_r_mine": pooled["actual_net_r"],
            "actual_net_r_recorded": development_finding[
                "actual_complete_modelled_net_r"
            ],
        },
        "pooled": pooled,
        "liquidity_sweep_reclaim_subset": {
            "selected": len(lsr),
            "net_r": round(
                sum(
                    float(row.get("terminal_net_r") or 0.0)
                    for row in lsr
                    if m.fit._state(row) is not None
                ),
                4,
            ),
            "outcomes": dict(sorted(Counter(
                m.fit._state(row) or "CENSORED" for row in lsr
            ).items())),
            "by_day": {day: round(value, 4) for day, value in sorted(lsr_by_day.items())},
        },
        "days": day_summaries,
    }
    (RECEIPTS / "PM_JAN_FROZEN_RULE_V1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    log(done=True,
        verify=receipt["verification_vs_development_finding"],
        lsr=receipt["liquidity_sweep_reclaim_subset"]["net_r"])


if __name__ == "__main__":
    main()
