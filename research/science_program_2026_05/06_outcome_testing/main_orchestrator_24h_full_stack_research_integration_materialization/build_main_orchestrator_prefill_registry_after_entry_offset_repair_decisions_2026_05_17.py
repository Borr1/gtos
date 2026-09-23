"""Materialize prefill registry metadata after entry-offset repair decisions."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import FOLLOW_STRATEGY_REGISTRY


DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
BOUNDARY_FIELDS = {
    "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
    "validation_result_status": "NOT_OPENED_BY_METADATA_REFRESH",
    "outcome_result_rows_status": "NOT_OPENED_BY_METADATA_REFRESH",
    "broker_runtime_change_status": "NO_BROKER_OR_RUNTIME_CHANGE_FROM_METADATA_REFRESH",
}

INPUT_DECISION_SUMMARY = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_SUMMARY_{DATE}.json"
)
INPUT_FORWARD_CAPTURE = Path("src/research_infra/forward_capture.py")
INPUT_FORWARD_CAPTURE_TESTS = Path("tests/test_forward_capture_shadow_loggers.py")

OUTPUT_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_ENTRY_REPAIR_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_ENTRY_REPAIR_SUMMARY_{DATE}.json"
)
OUTPUT_MANIFEST = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_ENTRY_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
)

STRATEGY_ID = "PREFILL_DELIVERY_REVERSAL_PATH"
EXPECTED_BRANCH_DECISION = "PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_WITH_KILL_REDESIGN_SPLIT"
EXPECTED_IMPLEMENTATION = (
    "KEEP_PREFILL_KILL_REDESIGN_SPLIT_AND_DESIGN_FAR_MISS_RETEST_CONTROL_FOR_10_ROWS"
)
STALE_TOKENS = (
    "PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_WITH_ENTRY_OFFSET_PROXY_BOUNDARY",
    "KEEP_BUCKETED_PREFILL_DELIVERY_SCORER_AND_BUILD_FAR_MISS_RETEST_CONTROL_MODEL",
    "94 far-miss retest-redesign controls",
    "95 numeric proxy rows",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def stale_tokens(snapshot: dict[str, Any]) -> list[str]:
    text = " ".join(
        str(snapshot.get(field) or "")
        for field in ("branch_decision", "decision_evidence", "implementation_candidate")
    )
    return [token for token in STALE_TOKENS if token in text]


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    registry = {str(item.get("strategy_id") or ""): dict(item) for item in FOLLOW_STRATEGY_REGISTRY}
    strategy = registry[STRATEGY_ID]
    decision = read_json(INPUT_DECISION_SUMMARY)
    row = {
        "row_id": "MAIN-ORCH24-PREFILL-REGISTRY-AFTER-ENTRY-OFFSET-REPAIR-001",
        "route_id": ROUTE_ID,
        "generated_utc": generated,
        "strategy_id": STRATEGY_ID,
        "family": strategy.get("family"),
        "evidence_role": strategy.get("evidence_role"),
        "result_use_status": strategy.get("result_use_status"),
        "branch_decision": strategy.get("branch_decision"),
        "decision_evidence": strategy.get("decision_evidence"),
        "implementation_candidate": strategy.get("implementation_candidate"),
        "stale_metadata_tokens": stale_tokens(strategy),
        "action_rows": decision["rows"],
        "prefill_target_rows": decision["prefill_target_rows"],
        "target_action_class_counts_before": decision[
            "prefill_target_action_class_counts_before"
        ],
        "target_action_class_counts_after": decision["prefill_target_action_class_counts_after"],
        "target_branch_decision_counts_after": decision[
            "prefill_target_branch_decision_counts_after"
        ],
        "action_class_delta_vs_previous": decision["action_class_delta_vs_previous"],
        "linked_entry_offset_before_numeric_proxy_rows": decision[
            "linked_entry_offset_before_numeric_proxy_rows"
        ],
        "linked_entry_offset_after_numeric_proxy_rows": decision[
            "linked_entry_offset_after_numeric_proxy_rows"
        ],
        "linked_entry_offset_numeric_proxy_row_delta": decision[
            "linked_entry_offset_numeric_proxy_row_delta"
        ],
        "linked_entry_offset_before_proxy_r_sum": decision[
            "linked_entry_offset_before_proxy_r_sum"
        ],
        "linked_entry_offset_after_proxy_r_sum": decision["linked_entry_offset_after_proxy_r_sum"],
        "linked_entry_offset_proxy_r_sum_delta": decision[
            "linked_entry_offset_proxy_r_sum_delta"
        ],
        "prefill_metadata_numeric_proxy_rows": decision["prefill_metadata_numeric_proxy_rows"],
        "prefill_metadata_proxy_r_sum": decision["prefill_metadata_proxy_r_sum"],
        "exact_r_rows": decision["exact_r_rows"],
        "boundary_fields": BOUNDARY_FIELDS,
        "broker_runtime_change_status": "NO_BROKER_OR_RUNTIME_CHANGE_FROM_METADATA_REFRESH",
        "no_shadow_log_append": True,
    }
    rows = [row]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated,
        "evidence_class": "MAIN_ORCH24_PREFILL_REGISTRY_AFTER_ENTRY_OFFSET_REPAIR_DECISION",
        "claim_boundary": (
            "Forward-capture strategy registry metadata is refreshed after prefill rows "
            "consume repaired entry-offset branch decisions. This changes future strategy "
            "snapshot metadata only; it does not append shadow logs, rescore historical rows, "
            "change broker/runtime behavior, or open live-use assertions."
        ),
        "boundary_fields": BOUNDARY_FIELDS,
        "rows": len(rows),
        "watched_strategy_ids": [STRATEGY_ID],
        "expected_branch_decision": EXPECTED_BRANCH_DECISION,
        "expected_implementation_candidate": EXPECTED_IMPLEMENTATION,
        "metadata_rows_with_stale_tokens": 1 if row["stale_metadata_tokens"] else 0,
        "action_rows": row["action_rows"],
        "prefill_target_rows": row["prefill_target_rows"],
        "target_action_class_counts_before": row["target_action_class_counts_before"],
        "target_action_class_counts_after": row["target_action_class_counts_after"],
        "target_branch_decision_counts_after": row["target_branch_decision_counts_after"],
        "action_class_delta_vs_previous": row["action_class_delta_vs_previous"],
        "linked_entry_offset_before_numeric_proxy_rows": row[
            "linked_entry_offset_before_numeric_proxy_rows"
        ],
        "linked_entry_offset_after_numeric_proxy_rows": row[
            "linked_entry_offset_after_numeric_proxy_rows"
        ],
        "linked_entry_offset_numeric_proxy_row_delta": row[
            "linked_entry_offset_numeric_proxy_row_delta"
        ],
        "linked_entry_offset_after_proxy_r_sum": row["linked_entry_offset_after_proxy_r_sum"],
        "linked_entry_offset_proxy_r_sum_delta": row["linked_entry_offset_proxy_r_sum_delta"],
        "prefill_metadata_numeric_proxy_rows": row["prefill_metadata_numeric_proxy_rows"],
        "prefill_metadata_proxy_r_sum": row["prefill_metadata_proxy_r_sum"],
        "exact_r_rows": row["exact_r_rows"],
        "plate_decision": "PREFILL_REGISTRY_METADATA_REFRESHED_AFTER_ENTRY_OFFSET_REPAIR_DECISIONS",
    }
    return rows, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "prefill_after_entry_offset_repair_decision_summary": INPUT_DECISION_SUMMARY,
        "forward_capture": INPUT_FORWARD_CAPTURE,
        "forward_capture_tests": INPUT_FORWARD_CAPTURE_TESTS,
    }
    outputs = {
        "ledger": OUTPUT_LEDGER,
        "summary": OUTPUT_SUMMARY,
    }
    return {
        "route_id": ROUTE_ID,
        "generated_utc": summary["generated_utc"],
        "evidence_class": summary["evidence_class"],
        "boundary_fields": BOUNDARY_FIELDS,
        "inputs": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else None,
            }
            for name, path in inputs.items()
        },
        "outputs": {
            name: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for name, path in outputs.items()
        },
        "summary_counts": {
            "rows": summary["rows"],
            "metadata_rows_with_stale_tokens": summary["metadata_rows_with_stale_tokens"],
            "prefill_target_rows": summary["prefill_target_rows"],
            "target_action_class_counts_after": summary["target_action_class_counts_after"],
            "action_class_delta_vs_previous": summary["action_class_delta_vs_previous"],
            "linked_entry_offset_numeric_proxy_row_delta": summary[
                "linked_entry_offset_numeric_proxy_row_delta"
            ],
            "linked_entry_offset_proxy_r_sum_delta": summary[
                "linked_entry_offset_proxy_r_sum_delta"
            ],
            "exact_r_rows": summary["exact_r_rows"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
