"""Materialize concrete entry-offset implementation decisions.

Consumes the spread-aware tick-offset replay and freezes row-level decisions for
the 0.50R challenger surface. This is research/tooling output only; no shadow
log append and no live entry behavior change.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

SOURCE_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_OUTPUT_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def shift(row: dict[str, Any], value: str) -> dict[str, Any]:
    outcome = row.get("offset_shift_outcomes") or {}
    item = outcome.get(value)
    return item if isinstance(item, dict) else {}


def proxy(row: dict[str, Any], value: str) -> float | None:
    return safe_float(shift(row, value).get("proxy_r"))


def status(row: dict[str, Any], value: str) -> str | None:
    raw = shift(row, value).get("outcome_status")
    return str(raw) if raw not in (None, "") else None


def decision_for(row: dict[str, Any]) -> dict[str, Any]:
    bucket = str(row.get("entry_retest_redesign_bucket") or "")
    tick_status = str(row.get("tick_source_status") or "")
    status_025 = status(row, "0.25")
    status_050 = status(row, "0.5")
    status_100 = status(row, "1")
    if bucket == "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW":
        return {
            "action_class": "KEEP",
            "branch_decision": "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_ENTRY_REDESIGN_DENOMINATOR",
            "implementation_candidate": "NONE_CURRENT_ENTRY_ALREADY_TOUCHED_OR_NOT_TP1_NO_FILL",
            "selected_shift_r": None,
            "selected_shift_proxy_r": None,
            "selected_shift_status": None,
            "kill_025r_reason": "NOT_IN_ENTRY_OFFSET_DENOMINATOR",
            "wider_100r_status": status_100,
        }
    if tick_status != "TICK_REPLAY_SOURCE_COMPLETE":
        return {
            "action_class": "SOURCE_REPAIR",
            "branch_decision": "SOURCE_REPAIR_REQUIRED_FOR_ENTRY_OFFSET_SCORER",
            "implementation_candidate": "REPAIR_TICK_PARQUET_SOURCE_BEFORE_ENTRY_OFFSET_SCORING",
            "selected_shift_r": None,
            "selected_shift_proxy_r": None,
            "selected_shift_status": None,
            "kill_025r_reason": "TICK_SOURCE_INCOMPLETE",
            "wider_100r_status": status_100,
        }
    if bucket == "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE":
        if status_050 == "TP1_AFTER_SHIFT_FILL":
            return {
                "action_class": "IMPLEMENT_DEFAULT_OFF",
                "branch_decision": "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_NEAR_MISS_CHALLENGER",
                "implementation_candidate": "ENTRY_OFFSET_050R_NEAR_MISS_SPREAD_AWARE_CHALLENGER",
                "selected_shift_r": 0.5,
                "selected_shift_proxy_r": proxy(row, "0.5"),
                "selected_shift_status": status_050,
                "kill_025r_reason": f"0.25R_{status_025}",
                "wider_100r_status": status_100,
            }
        return {
            "action_class": "KILL",
            "branch_decision": "KILL_NEAR_MISS_OFFSET_CHALLENGER_NO_050R_TP_AFTER_FILL",
            "implementation_candidate": "NONE_NEAR_MISS_050R_DID_NOT_PRODUCE_TARGET_AFTER_FILL",
            "selected_shift_r": None,
            "selected_shift_proxy_r": None,
            "selected_shift_status": status_050,
            "kill_025r_reason": f"0.25R_{status_025}",
            "wider_100r_status": status_100,
        }
    if bucket == "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE":
        if status_050 == "TP1_AFTER_SHIFT_FILL":
            return {
                "action_class": "REDESIGN",
                "branch_decision": "REDESIGN_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL",
                "implementation_candidate": "ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_NOT_DEFAULT_ENTRY",
                "selected_shift_r": 0.5,
                "selected_shift_proxy_r": proxy(row, "0.5"),
                "selected_shift_status": status_050,
                "kill_025r_reason": f"0.25R_{status_025}",
                "wider_100r_status": status_100,
            }
        return {
            "action_class": "KILL",
            "branch_decision": "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
            "implementation_candidate": "NONE_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE",
            "selected_shift_r": None,
            "selected_shift_proxy_r": None,
            "selected_shift_status": status_050,
            "kill_025r_reason": f"0.25R_{status_025}",
            "wider_100r_status": status_100,
        }
    return {
        "action_class": "SOURCE_REPAIR",
        "branch_decision": "ENTRY_OFFSET_BUCKET_SOURCE_REPAIR_REQUIRED",
        "implementation_candidate": "REPAIR_ENTRY_REDESIGN_BUCKET_SOURCE",
        "selected_shift_r": None,
        "selected_shift_proxy_r": None,
        "selected_shift_status": status_050,
        "kill_025r_reason": f"0.25R_{status_025}",
        "wider_100r_status": status_100,
    }


def build_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    generated = utc_now()
    out: list[dict[str, Any]] = []
    for source in source_rows:
        decision = decision_for(source)
        row = {
            "row_id": f"MAIN-ORCH24-ENTRY-OFFSET-050R-DECISION-{len(out) + 1:05d}",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "source_row_id": source.get("row_id"),
            "source_line_no": source.get("_source_line_no"),
            "candidate_id": source.get("candidate_id"),
            "symbol": source.get("symbol"),
            "broker_symbol": source.get("broker_symbol"),
            "side": source.get("side"),
            "framework": source.get("framework"),
            "decision_time_utc": source.get("decision_time_utc"),
            "asof_latest_candle_utc": source.get("asof_latest_candle_utc"),
            "entry_retest_redesign_bucket": source.get("entry_retest_redesign_bucket"),
            "entry_touch_distance_status": source.get("entry_touch_distance_status"),
            "m15_nearest_distance_to_entry_r": source.get("m15_nearest_distance_to_entry_r"),
            "minimum_spread_aware_shift_r": source.get("minimum_spread_aware_shift_r"),
            "tick_source_status": source.get("tick_source_status"),
            "tick_count": source.get("tick_count"),
            "shift_025_status": status(source, "0.25"),
            "shift_025_proxy_r": proxy(source, "0.25"),
            "shift_050_status": status(source, "0.5"),
            "shift_050_proxy_r": proxy(source, "0.5"),
            "shift_100_status": status(source, "1"),
            "shift_100_proxy_r": proxy(source, "1"),
            "exact_r": None,
            "safe_flags": SAFE_FLAGS,
            "no_shadow_log_append": True,
            "no_live_behavior": True,
            **decision,
        }
        out.append(row)
    return out


def mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def shift_summary(rows: list[dict[str, Any]], shift_name: str) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get(f"shift_{shift_name}_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": sum(values),
        "proxy_r_mean": mean(values),
        "status_counts": dict(Counter(str(row.get(f"shift_{shift_name}_status") or "NO_STATUS") for row in rows)),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_bucket[str(row.get("entry_retest_redesign_bucket") or "")].append(row)
    selected = [row for row in rows if safe_float(row.get("selected_shift_proxy_r")) is not None]
    selected_values = [float(row["selected_shift_proxy_r"]) for row in selected]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ENTRY_OFFSET_050R_IMPLEMENTATION_CANDIDATE_DECISIONS",
        "claim_boundary": (
            "Row-level default-off entry-offset candidate decisions from current spread-aware tick replay. "
            "This is proxy-R research/tooling only, not live entry behavior."
        ),
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "affected_entry_redesign_rows": sum(
            1
            for row in rows
            if row.get("entry_retest_redesign_bucket")
            in {"NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE", "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE"}
        ),
        "exact_r_rows": 0,
        "action_class_counts": dict(Counter(str(row.get("action_class")) for row in rows)),
        "branch_decision_counts": dict(Counter(str(row.get("branch_decision")) for row in rows)),
        "implementation_candidate_counts": dict(
            Counter(str(row.get("implementation_candidate")) for row in rows)
        ),
        "tick_source_status_counts": dict(Counter(str(row.get("tick_source_status")) for row in rows)),
        "selected_shift_numeric_proxy_rows": len(selected_values),
        "selected_shift_proxy_r_sum": sum(selected_values),
        "selected_shift_proxy_r_mean": mean(selected_values),
        "bucket_summary": {
            bucket: {
                "rows": len(bucket_rows),
                "action_class_counts": dict(Counter(str(row.get("action_class")) for row in bucket_rows)),
                "branch_decision_counts": dict(
                    Counter(str(row.get("branch_decision")) for row in bucket_rows)
                ),
                "shift_025": shift_summary(bucket_rows, "025"),
                "shift_050": shift_summary(bucket_rows, "050"),
                "shift_100": shift_summary(bucket_rows, "100"),
            }
            for bucket, bucket_rows in sorted(by_bucket.items())
        },
        "selected_branch_policy": {
            "near_miss": "IMPLEMENT_DEFAULT_OFF_050R_ONLY_WHEN_SPREAD_AWARE_TICK_REPLAY_SHOWS_TP_AFTER_FILL",
            "far_miss": "REDESIGN_CONTROL_ONLY_FOR_050R_TP_AFTER_FILL_ROWS; KILL_NO_FILL_ROWS",
            "shift_025": "KILLED_AS_FILL_PROXY_FOR_CURRENT_TICK_COMPLETE_AFFECTED_ROWS",
            "shift_100": "PRESERVED_AS_WIDER_RETEST_STRESS_ONLY_NOT_SELECTED_FOR_CURRENT_IMPLEMENTATION",
        },
        "safe_flags": SAFE_FLAGS,
        "terminal_decision": "ENTRY_OFFSET_050R_CANDIDATE_DECISIONS_MATERIALIZED_WITH_PROXY_R_DELTAS",
    }


def build_manifest(outputs: list[Path]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            SOURCE_LEDGER.name: {
                "path": str(SOURCE_LEDGER),
                "bytes": SOURCE_LEDGER.stat().st_size,
                "sha256": sha256_file(SOURCE_LEDGER),
            }
        },
        "outputs": {
            path.name: {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in outputs
        },
    }


def main() -> None:
    rows = build_rows(read_jsonl(SOURCE_LEDGER))
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summarize(rows))
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
