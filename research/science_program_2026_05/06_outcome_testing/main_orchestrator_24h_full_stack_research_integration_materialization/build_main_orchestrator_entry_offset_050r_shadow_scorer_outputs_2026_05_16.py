"""Materialize entry-offset 0.50R shadow-scorer output rows.

This builder converts the verified tick-replay decision ledger into rows shaped
like live mechanical shadow scorer outputs for the default-off 0.50R entry
offset challenger. It does not append to shadow logs or change live behavior.
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
STRATEGY_ID = "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

SOURCE_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_MANIFEST_{DATE}.json"


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
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def scorer_state(source: dict[str, Any]) -> dict[str, Any]:
    action = str(source.get("action_class") or "")
    bucket = str(source.get("entry_retest_redesign_bucket") or "")
    shift_status = str(source.get("shift_050_status") or "")
    selected_proxy = safe_float(source.get("selected_shift_proxy_r"))
    shift_proxy = safe_float(source.get("shift_050_proxy_r"))
    if action == "KEEP":
        return {
            "strategy_status": "NOT_APPLICABLE_NOT_ENTRY_REDESIGN_DENOMINATOR",
            "score_status": "NOT_APPLICABLE",
            "outcome_status": "NOT_SCORED",
            "strategy_proxy_r": None,
            "scoring_boundary": "CURRENT_ENTRY_MODEL_ROW_NOT_NO_FILL_TP1_OFFSET_REDESIGN",
            "status_reason": "Candidate is not in the no-fill TP1 entry-offset redesign denominator.",
        }
    if action == "SOURCE_REPAIR":
        return {
            "strategy_status": "SOURCE_REPAIR_REQUIRED_TICK_REPLAY_INCOMPLETE",
            "score_status": "SOURCE_REPAIR_REQUIRED",
            "outcome_status": "NOT_SCORED",
            "strategy_proxy_r": None,
            "scoring_boundary": "NO_ENTRY_OFFSET_PROXY_R_WITHOUT_READABLE_TICK_REPLAY_SOURCE",
            "status_reason": "Tick replay source was missing or unreadable for this candidate window.",
        }
    if action == "IMPLEMENT_DEFAULT_OFF":
        return {
            "strategy_status": "SCORED_ENTRY_OFFSET_050R_TICK_REPLAY_PROXY_DEFAULT_OFF",
            "score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
            "outcome_status": "TP1_AFTER_SHIFT_FILL",
            "strategy_proxy_r": selected_proxy,
            "scoring_boundary": "ENTRY_OFFSET_050R_TICK_REPLAY_PROXY_NO_LIVE_ENTRY_CHANGE",
            "status_reason": "Near-miss no-fill row filled at a 0.50R offset and reached TP1 in spread-aware tick replay.",
        }
    if action == "REDESIGN":
        return {
            "strategy_status": "SCORED_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_PROXY",
            "score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
            "outcome_status": "TP1_AFTER_SHIFT_FILL",
            "strategy_proxy_r": selected_proxy,
            "scoring_boundary": "FAR_MISS_050R_RETEST_CONTROL_PROXY_NOT_DEFAULT_ENTRY",
            "status_reason": "Far-miss row filled at a 0.50R offset and reached TP1, but remains redesign/control rather than default entry.",
        }
    if action == "KILL" and bucket == "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE" and shift_status == "NO_FILL_AT_SHIFT":
        return {
            "strategy_status": "KILLED_ENTRY_OFFSET_050R_NO_FILL",
            "score_status": "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY",
            "outcome_status": "NO_FILL_AT_SHIFT",
            "strategy_proxy_r": shift_proxy,
            "scoring_boundary": "NO_ENTRY_OFFSET_PROXY_UPLIFT_WHEN_050R_SHIFT_STILL_NO_FILL",
            "status_reason": "0.50R offset still did not fill in spread-aware tick replay; kill the current 0.50R scorer row.",
        }
    return {
        "strategy_status": "SOURCE_REPAIR_REQUIRED_UNMAPPED_ENTRY_OFFSET_DECISION",
        "score_status": "SOURCE_REPAIR_REQUIRED",
        "outcome_status": "NOT_SCORED",
        "strategy_proxy_r": None,
        "scoring_boundary": "UNMAPPED_ENTRY_OFFSET_DECISION_REQUIRES_REVIEW",
        "status_reason": f"Unhandled entry-offset action/bucket/status: {action}/{bucket}/{shift_status}",
    }


def build_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    generated = utc_now()
    rows: list[dict[str, Any]] = []
    for source in source_rows:
        state = scorer_state(source)
        rows.append(
            {
                "schema_version": "entry_offset_050r_shadow_scorer_output_projection_v1",
                "row_id": f"MAIN-ORCH24-ENTRY-OFFSET-050R-SCORER-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "generated_utc": generated,
                "source_decision_row_id": source.get("row_id"),
                "source_line_no": source.get("_source_line_no"),
                "candidate_id": source.get("candidate_id"),
                "symbol": source.get("symbol"),
                "broker_symbol": source.get("broker_symbol"),
                "side": source.get("side"),
                "framework": source.get("framework"),
                "decision_time_utc": source.get("decision_time_utc"),
                "asof_latest_candle_utc": source.get("asof_latest_candle_utc"),
                "strategy_id": STRATEGY_ID,
                "strategy_family": "entry_geometry_fillability_tick_path_ordering",
                "strategy_evidence_role": "default_off_entry_offset_challenger",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "entry_retest_redesign_bucket": source.get("entry_retest_redesign_bucket"),
                "entry_touch_distance_status": source.get("entry_touch_distance_status"),
                "m15_nearest_distance_to_entry_r": source.get("m15_nearest_distance_to_entry_r"),
                "minimum_spread_aware_shift_r": source.get("minimum_spread_aware_shift_r"),
                "tick_source_status": source.get("tick_source_status"),
                "tick_count": source.get("tick_count"),
                "shift_025_status": source.get("shift_025_status"),
                "shift_025_proxy_r": source.get("shift_025_proxy_r"),
                "shift_050_status": source.get("shift_050_status"),
                "shift_050_proxy_r": source.get("shift_050_proxy_r"),
                "shift_100_status": source.get("shift_100_status"),
                "shift_100_proxy_r": source.get("shift_100_proxy_r"),
                "branch_decision": source.get("branch_decision"),
                "implementation_candidate": source.get("implementation_candidate"),
                "decision_evidence": "MAIN_ORCH24_ENTRY_OFFSET_050R_CANDIDATE_DECISION_VERIFIED_TICK_REPLAY",
                "action_class": source.get("action_class"),
                "exact_r": None,
                "safe_flags": SAFE_FLAGS,
                "no_shadow_log_append": True,
                "no_live_behavior": True,
                "would_append_to_shadow_strategy_id": STRATEGY_ID,
                **state,
            }
        )
    return rows


def mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("strategy_proxy_r"))) is not None]
    by_status: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_status[str(row.get("strategy_status") or "")].append(row)
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUTS",
        "claim_boundary": (
            "Shadow-scorer output projection from verified spread-aware tick replay. "
            "No shadow log append and no live entry behavior change."
        ),
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "strategy_id": STRATEGY_ID,
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": sum(values),
        "proxy_r_mean": mean(values),
        "exact_r_rows": 0,
        "strategy_status_counts": dict(Counter(str(row.get("strategy_status")) for row in rows)),
        "score_status_counts": dict(Counter(str(row.get("score_status")) for row in rows)),
        "outcome_status_counts": dict(Counter(str(row.get("outcome_status")) for row in rows)),
        "branch_decision_counts": dict(Counter(str(row.get("branch_decision")) for row in rows)),
        "action_class_counts": dict(Counter(str(row.get("action_class")) for row in rows)),
        "entry_redesign_bucket_counts": dict(
            Counter(str(row.get("entry_retest_redesign_bucket")) for row in rows)
        ),
        "tick_source_status_counts": dict(Counter(str(row.get("tick_source_status")) for row in rows)),
        "status_proxy_summary": {
            status: {
                "rows": len(status_rows),
                "numeric_proxy_rows": len(
                    [row for row in status_rows if safe_float(row.get("strategy_proxy_r")) is not None]
                ),
                "proxy_r_sum": sum(
                    float(row["strategy_proxy_r"])
                    for row in status_rows
                    if safe_float(row.get("strategy_proxy_r")) is not None
                ),
            }
            for status, status_rows in sorted(by_status.items())
        },
        "plate_decision": "ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUTS_MATERIALIZED_WITH_PROXY_R_DELTAS",
        "safe_flags": SAFE_FLAGS,
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
