"""Materialize pending lifecycle registry metadata after touch source repair."""

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
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_TOUCH_REPAIR_SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_NOT_APPLICABLE_TOUCH_REPAIR_SUMMARY_2026-05-17.json"
)
INPUT_DECISION_SPREAD_SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_CAPTURE_SUMMARY_2026-05-17.json"
)
INPUT_FORWARD_CAPTURE = Path("src/research_infra/forward_capture.py")
INPUT_FORWARD_CAPTURE_TESTS = Path("tests/test_forward_capture_shadow_loggers.py")

OUTPUT_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_REGISTRY_AFTER_TOUCH_REPAIR_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_REGISTRY_AFTER_TOUCH_REPAIR_SUMMARY_{DATE}.json"
)
OUTPUT_MANIFEST = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PENDING_LIFECYCLE_REGISTRY_AFTER_TOUCH_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
)

STRATEGY_ID = "PENDING_LIMIT_LIFECYCLE"
STALE_TOKENS = (
    "MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR",
    "SOURCE_DERIVATION_PARTIAL",
    "323 derived source cells",
    "184 missing source cells",
    "no new first-touch row delta",
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
    touch_summary = read_json(INPUT_TOUCH_REPAIR_SUMMARY)
    decision_spread_summary = read_json(INPUT_DECISION_SPREAD_SUMMARY)

    row = {
        "row_id": "MAIN-ORCH24-PENDING-LIFECYCLE-REGISTRY-TOUCH-REPAIR-001",
        "route_id": ROUTE_ID,
        "generated_utc": generated,
        "strategy_id": STRATEGY_ID,
        "family": strategy.get("family"),
        "evidence_role": strategy.get("evidence_role"),
        "promotion_verdict": strategy.get("promotion_verdict"),
        "branch_decision": strategy.get("branch_decision"),
        "decision_evidence": strategy.get("decision_evidence"),
        "implementation_candidate": strategy.get("implementation_candidate"),
        "stale_metadata_tokens": stale_tokens(strategy),
        "current_rows": touch_summary["rows"],
        "current_internal_pending_lifecycle_rows": touch_summary[
            "internal_pending_lifecycle_rows"
        ],
        "current_numeric_proxy_rows": touch_summary["after_numeric_proxy_rows"],
        "current_proxy_r_sum": touch_summary["after_proxy_r_sum"],
        "current_proxy_r_mean": touch_summary["after_proxy_r_mean"],
        "previous_missing_source_field_cells": touch_summary[
            "previous_missing_source_field_cells"
        ],
        "current_missing_source_field_cells": touch_summary[
            "after_missing_source_field_cells"
        ],
        "missing_source_field_cell_delta": touch_summary["missing_source_field_cell_delta"],
        "remaining_missing_field_counts": touch_summary["missing_field_counts"],
        "not_applicable_source_repair_rows": touch_summary[
            "not_applicable_source_repair_rows"
        ],
        "source_repair_rows": touch_summary["source_repair_rows"],
        "decision_spread_future_capture_fields": decision_spread_summary[
            "implemented_source_capture_fields"
        ],
        "historical_gap_boundary": (
            "Current historical pending lifecycle rows still lack decision_spread "
            "value/unit because those fields were not captured on disk before "
            "PendingLimitIntent decision-spread persistence. Future rows are covered "
            "by the implementation in MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_CAPTURE."
        ),
        "metadata_refresh_proxy_row_delta": 0,
        "metadata_refresh_proxy_r_sum_delta": 0.0,
        "exact_r_rows": 0,
        "safe_flags": SAFE_FLAGS,
        "no_live_behavior": True,
        "no_shadow_log_append": True,
    }

    rows = [row]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated,
        "evidence_class": "MAIN_ORCH24_PENDING_LIFECYCLE_REGISTRY_AFTER_TOUCH_REPAIR",
        "claim_boundary": (
            "Forward-capture strategy registry metadata is refreshed after pending lifecycle "
            "not-applicable touch repair. This changes future strategy_follow_candidate "
            "metadata labels only; it does not append shadow logs, rescore historical rows, "
            "change live behavior, or open promotion claims."
        ),
        "safe_flags": SAFE_FLAGS,
        "rows": len(rows),
        "watched_strategy_ids": [STRATEGY_ID],
        "metadata_rows_with_stale_tokens": 1 if row["stale_metadata_tokens"] else 0,
        "current_rows": row["current_rows"],
        "current_internal_pending_lifecycle_rows": row[
            "current_internal_pending_lifecycle_rows"
        ],
        "current_numeric_proxy_rows": row["current_numeric_proxy_rows"],
        "current_proxy_r_sum": row["current_proxy_r_sum"],
        "current_proxy_r_mean": row["current_proxy_r_mean"],
        "previous_missing_source_field_cells": row["previous_missing_source_field_cells"],
        "current_missing_source_field_cells": row["current_missing_source_field_cells"],
        "missing_source_field_cell_delta": row["missing_source_field_cell_delta"],
        "remaining_missing_field_counts": row["remaining_missing_field_counts"],
        "not_applicable_source_repair_rows": row["not_applicable_source_repair_rows"],
        "source_repair_rows": row["source_repair_rows"],
        "metadata_refresh_proxy_row_delta": 0,
        "metadata_refresh_proxy_r_sum_delta": 0.0,
        "exact_r_rows": 0,
        "plate_decision": "PENDING_LIFECYCLE_REGISTRY_METADATA_REFRESHED_AFTER_NOT_APPLICABLE_TOUCH_REPAIR",
    }
    return rows, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "touch_repair_summary": INPUT_TOUCH_REPAIR_SUMMARY,
        "decision_spread_summary": INPUT_DECISION_SPREAD_SUMMARY,
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
        "safe_flags": SAFE_FLAGS,
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
            "current_rows": summary["current_rows"],
            "current_internal_pending_lifecycle_rows": summary[
                "current_internal_pending_lifecycle_rows"
            ],
            "current_numeric_proxy_rows": summary["current_numeric_proxy_rows"],
            "current_proxy_r_sum": summary["current_proxy_r_sum"],
            "current_missing_source_field_cells": summary[
                "current_missing_source_field_cells"
            ],
            "metadata_refresh_proxy_row_delta": summary[
                "metadata_refresh_proxy_row_delta"
            ],
            "metadata_refresh_proxy_r_sum_delta": summary[
                "metadata_refresh_proxy_r_sum_delta"
            ],
            "exact_r_rows": summary["exact_r_rows"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    manifest = build_manifest(summary)
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
