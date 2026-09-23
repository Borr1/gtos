"""Materialize the moonshot selected-action source-capture contract.

This is the concrete bridge between the selected-action implementation rows and
future scorer computation. It records the required source fields, current source
log boundary, and current projection denominator without counting proxy R or
allowing candidate/runtime use.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import (  # noqa: E402
    MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_PATH,
    MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_SCHEMA_VERSION,
    MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY,
)


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

PROJECTION_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_FORWARD_SHADOW_REGISTRY_INTEGRATION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CAPTURE_CONTRACT_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_SOURCE_CAPTURE_CONTRACT_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def source_capture_keys(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        if candidate_id and strategy_id:
            keys.add((candidate_id, strategy_id))
    return keys


def build() -> dict[str, Any]:
    generated_utc = datetime.now(UTC).isoformat()
    projection_rows = read_jsonl(PROJECTION_LEDGER)
    source_capture_path = REPO_ROOT / MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_PATH
    source_rows = read_jsonl(source_capture_path)
    source_keys = source_capture_keys(source_rows)
    projection_counts = Counter(str(row.get("strategy_id") or "") for row in projection_rows)
    waiting_counts = Counter(
        str(row.get("strategy_id") or "")
        for row in projection_rows
        if row.get("strategy_status") == "WAITING_FOR_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE"
    )
    ready_counts = Counter(
        str(row.get("strategy_id") or "")
        for row in projection_rows
        if row.get("source_capture_ready") is True
    )

    output_rows: list[dict[str, Any]] = []
    for item in MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY:
        strategy_id = str(item.get("strategy_id") or "")
        required_fields = [str(field) for field in item.get("source_capture_required_fields") or []]
        output_rows.append(
            {
                "schema_version": "moonshot_selected_action_source_capture_contract_v1",
                "route_id": ROUTE_ID,
                "date": DATE,
                "generated_utc": generated_utc,
                "safe_flags": SAFE_FLAGS,
                "strategy_id": strategy_id,
                "strategy_family": item.get("family"),
                "strategy_evidence_role": item.get("evidence_role"),
                "branch_decision": item.get("branch_decision"),
                "implementation_candidate": item.get("implementation_candidate"),
                "decision_evidence": item.get("decision_evidence"),
                "source_capture_required_fields": required_fields,
                "source_capture_required_field_count": len(required_fields),
                "source_capture_log_path": MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_PATH,
                "source_capture_log_exists": source_capture_path.exists(),
                "source_capture_log_rows_seen": len(source_rows),
                "source_capture_latest_keys_seen": len(source_keys),
                "source_capture_schema_version": MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_SCHEMA_VERSION,
                "source_capture_writer": (
                    "src.research_infra.forward_capture.record_moonshot_selected_action_source_capture"
                ),
                "scorer_consumer": "src.research_infra.live_mechanical_shadow._moonshot_selected_action_status",
                "backfill_cli_argument": "--moonshot-selected-action-source-capture",
                "current_projection_rows_for_strategy": projection_counts.get(strategy_id, 0),
                "current_projection_waiting_rows_for_strategy": waiting_counts.get(strategy_id, 0),
                "current_projection_source_ready_rows_for_strategy": ready_counts.get(strategy_id, 0),
                "current_projection_runtime_score_allowed_rows": 0,
                "current_projection_candidate_use_allowed_now_rows": 0,
                "current_projection_live_effect_rows": 0,
                "proxy_delta_reference_counted_as_r": False,
                "counted_exact_r": False,
                "counted_proxy_r": False,
                "runtime_score_allowed": False,
                "candidate_use_allowed_now": False,
                "validation_safe": False,
                "live_effect": False,
                "opportunity_preservation_status": "PRESERVED_AS_SOURCE_CAPTURE_REQUIREMENT_AND_DEFAULT_OFF_SCORER_INPUT",
                "opportunity_owner_row_id": strategy_id,
                "opportunity_owner_source_artifact": "MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY",
                "opportunity_proxy_r_reference": None,
                "opportunity_proxy_reference_status": "NOT_COUNTED_SOURCE_CAPTURE_CONTRACT_ONLY",
                "opportunity_not_independently_countable_reason": (
                    "Selected-action proxy evidence remains owned by the upstream action-selection ledgers until "
                    "candidate-specific source-capture rows provide exact controls and scorer inputs."
                ),
                "opportunity_useful_mechanism": (
                    "The selected-action mechanism is preserved as a default-off scorer/source requirement that "
                    "can become computable once the listed fields are captured per candidate and strategy."
                ),
                "opportunity_downstream_paths": [
                    "source requirement",
                    "default-off scorer input",
                    "context feature",
                    "broader system component",
                ],
                "underlying_intelligence_preserved": True,
                "missed_opportunity_audit": {
                    "kill_scope": "NOT_KILLED_SOURCE_CAPTURE_CONTRACT",
                    "current_claim": item.get("branch_decision"),
                    "unsupported_reason": "CURRENT_CANDIDATES_LACK_SELECTED_ACTION_SOURCE_CAPTURE_ROWS",
                    "what_was_tried": (
                        "Wired source-capture writer, backfill CLI path, live-mechanical scorer consumer, "
                        "and current-denominator projection."
                    ),
                    "what_could_make_it_work": (
                        "Append candidate/strategy source-capture rows with all required fields and exact "
                        "control denominator artifacts, then recompute the default-off selected-action scorer."
                    ),
                    "preserve_as": "SOURCE_CAPTURE_REQUIREMENT_AND_DEFAULT_OFF_SELECTED_ACTION_SCORER_INPUT",
                    "next_route": "CAPTURE_SELECTED_ACTION_SOURCE_ROWS_AND_RECOMPUTE_DEFAULT_OFF_SCORER_OUTPUTS",
                    "path_status": {
                        "current_projection_waiting_rows_for_strategy": waiting_counts.get(strategy_id, 0),
                        "current_projection_source_ready_rows_for_strategy": ready_counts.get(strategy_id, 0),
                        "required_fields": required_fields,
                    },
                },
            }
        )

    write_jsonl(OUTPUT_LEDGER, output_rows)
    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "strategy_rows": len(output_rows),
        "strategy_ids": sorted(row["strategy_id"] for row in output_rows),
        "total_required_fields": sum(row["source_capture_required_field_count"] for row in output_rows),
        "source_capture_log_path": MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_PATH,
        "source_capture_log_exists": source_capture_path.exists(),
        "source_capture_log_rows_seen": len(source_rows),
        "source_capture_latest_keys_seen": len(source_keys),
        "projection_ledger": str(PROJECTION_LEDGER),
        "projection_ledger_rows": len(projection_rows),
        "projection_waiting_rows": sum(waiting_counts.values()),
        "projection_source_ready_rows": sum(ready_counts.values()),
        "projection_rows_per_strategy": dict(sorted(projection_counts.items())),
        "projection_waiting_rows_per_strategy": dict(sorted(waiting_counts.items())),
        "proxy_r_rows_opened": 0,
        "exact_r_rows_opened": 0,
        "counted_proxy_r_rows": 0,
        "runtime_score_allowed_rows": 0,
        "candidate_use_allowed_now_rows": 0,
        "live_effect_true_rows": 0,
        "rows_with_missed_opportunity_audit": sum(
            isinstance(row.get("missed_opportunity_audit"), dict) for row in output_rows
        ),
        "rows_with_underlying_intelligence_preserved": sum(
            row.get("underlying_intelligence_preserved") is True for row in output_rows
        ),
        "research_safety": {
            "changes_live_behavior": False,
            "changes_prompt_risk_selector_execution": False,
            "changes_shadow_log_history": False,
            "opens_exact_r": False,
            "opens_counted_proxy_r": False,
            "uses_proxy_delta_as_r": False,
        },
    }
    write_json(SUMMARY_PATH, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated_utc,
        "description": "Moonshot selected-action source-capture contract and current scorer-consumption boundary.",
        "output_files": {
            "contract_ledger": {
                "path": str(OUTPUT_LEDGER),
                "sha256": sha256_file(OUTPUT_LEDGER),
                "size_bytes": OUTPUT_LEDGER.stat().st_size,
                "rows": len(output_rows),
            },
            "summary": {
                "path": str(SUMMARY_PATH),
                "sha256": sha256_file(SUMMARY_PATH),
                "size_bytes": SUMMARY_PATH.stat().st_size,
            },
        },
        "input_files": {
            "projection_ledger": {
                "path": str(PROJECTION_LEDGER),
                "sha256": sha256_file(PROJECTION_LEDGER),
                "rows": len(projection_rows),
            },
            "source_capture_log": {
                "path": MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_PATH,
                "exists": source_capture_path.exists(),
                "sha256": sha256_file(source_capture_path),
                "rows": len(source_rows),
            },
        },
        "counts": {
            "strategy_rows": summary["strategy_rows"],
            "total_required_fields": summary["total_required_fields"],
            "projection_ledger_rows": summary["projection_ledger_rows"],
            "projection_waiting_rows": summary["projection_waiting_rows"],
            "source_capture_log_rows_seen": summary["source_capture_log_rows_seen"],
        },
        "safe_flags": SAFE_FLAGS,
    }
    write_json(MANIFEST_PATH, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
