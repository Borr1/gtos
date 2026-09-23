#!/usr/bin/env python3
"""T2 — golden conversion cross-check: export overlap vs existing may_2026 lane files.

Converts the raw export rows through the PRODUCER's own clock function
(lane_rematerialization._parse_broker_bar_time, imported from the origin/main
runtime worktree) and compares OHLCV per shared true-UTC timestamp against the
existing may_2026 pack's bar source files in the hold. Read-only everywhere.
"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RT = Path("/tmp/junjul-lane-mat-20260810/rt-wt")
sys.path.insert(0, str(RT))
from src.research_infra import lane_rematerialization as lane  # noqa: E402

HOLD = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
EXPORT = Path("/tmp/junjul-lane-mat-20260810/export/junjul_2026_lane_source_20260811")
OUT = Path("/tmp/junjul-lane-mat-20260810/overlap_check/T2_RESULT.json")

manifest = json.loads((HOLD / "manifests/may_2026.json").read_text())
by_key = {
    (row["symbol"], row["timeframe"]): row for row in manifest["bar_sources"]
}

symbols = sorted({row["symbol"] for row in manifest["bar_sources"]})
assert len(symbols) == 24, symbols

def read_lane(path: Path):
    out = {}
    with path.open("r", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            t = datetime.fromisoformat(row["time"])
            out[t] = row
    return out

def read_export_converted(path: Path):
    out = {}
    with path.open("r", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            t = lane._parse_broker_bar_time(row["time"])
            out[t] = row
    return out

NUM = ("open", "high", "low", "close", "volume")
report = {}
total_compared = 0
total_mismatch = 0
for tf in ("D1", "H4", "M15", "M1"):
    tf_compared = 0
    tf_value_mismatch = 0
    tf_missing_in_export = 0
    tf_missing_in_lane = 0
    tf_sym = 0
    examples = []
    for sym in symbols:
        entry = by_key[(sym, tf)]
        lane_path = HOLD / entry["lane_relpath"]
        exp_path = EXPORT / f"{sym}_{tf}.csv"
        if not exp_path.is_file():
            raise SystemExit(f"export file missing: {exp_path}")
        lane_rows = read_lane(lane_path)
        exp_rows = read_export_converted(exp_path)
        lo = max(min(lane_rows), min(exp_rows))
        hi = min(max(lane_rows), max(exp_rows))
        lane_in = {t: r for t, r in lane_rows.items() if lo <= t <= hi}
        exp_in = {t: r for t, r in exp_rows.items() if lo <= t <= hi}
        shared = lane_in.keys() & exp_in.keys()
        only_lane = lane_in.keys() - exp_in.keys()
        only_exp = exp_in.keys() - lane_in.keys()
        tf_missing_in_export += len(only_lane)
        tf_missing_in_lane += len(only_exp)
        for t in shared:
            a, b = lane_in[t], exp_in[t]
            bad = [
                c for c in NUM
                if float(a[c]) != float(b[c])
            ]
            tf_compared += 1
            if bad:
                tf_value_mismatch += 1
                if len(examples) < 5:
                    examples.append(
                        {
                            "symbol": sym,
                            "utc": t.isoformat(),
                            "cols": bad,
                            "lane": {c: a[c] for c in NUM},
                            "export": {c: b[c] for c in NUM},
                        }
                    )
        if only_lane and len(examples) < 5:
            examples.append(
                {
                    "symbol": sym,
                    "missing_in_export_first": sorted(x.isoformat() for x in only_lane)[:3],
                }
            )
        if only_exp and len(examples) < 5:
            examples.append(
                {
                    "symbol": sym,
                    "missing_in_lane_first": sorted(x.isoformat() for x in only_exp)[:3],
                }
            )
        tf_sym += 1
    report[tf] = {
        "symbols": tf_sym,
        "compared_rows": tf_compared,
        "value_mismatch_rows": tf_value_mismatch,
        "rows_missing_in_export_within_span": tf_missing_in_export,
        "rows_missing_in_lane_within_span": tf_missing_in_lane,
        "examples": examples,
    }
    total_compared += tf_compared
    total_mismatch += tf_value_mismatch + tf_missing_in_export + tf_missing_in_lane
    print(
        f"{tf}: compared={tf_compared} value_mismatch={tf_value_mismatch} "
        f"missing_in_export={tf_missing_in_export} missing_in_lane={tf_missing_in_lane}"
    )

verdict = "PASS" if total_mismatch == 0 else "FAIL"
print("TOTAL compared:", total_compared, "| any-mismatch:", total_mismatch, "| VERDICT:", verdict)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"verdict": verdict, "total_compared": total_compared, "per_timeframe": report}, indent=1, default=str))
print("wrote", OUT)
