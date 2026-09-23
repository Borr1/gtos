"""Materialize prefill delivery registry metadata after bucketed scorer output."""

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

INPUT_BUCKETED_SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_SUMMARY_2026-05-17.json"
)
INPUT_FORWARD_CAPTURE = Path("src/research_infra/forward_capture.py")
INPUT_FORWARD_CAPTURE_TESTS = Path("tests/test_forward_capture_shadow_loggers.py")

OUTPUT_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_REGISTRY_AFTER_BUCKETED_SCORER_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_REGISTRY_AFTER_BUCKETED_SCORER_SUMMARY_{DATE}.json"
)
OUTPUT_MANIFEST = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PREFILL_DELIVERY_REGISTRY_AFTER_BUCKETED_SCORER_OUTPUT_MANIFEST_{DATE}.json"
)

STRATEGY_ID = "PREFILL_DELIVERY_REVERSAL_PATH"
STALE_TOKENS = (
    "MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR",
    "REDESIGN_WITH_ENTRY_OFFSET_050R_AND_PREFILL_ADVERSE_NO_FILL_ROW_LEVEL_GATES",
    "PREFILL_ADVERSE_NO_FILL_ENTRY_OFFSET_050R_REDESIGN_GATE",
    "3 implement, 10 redesign-control, 84 killed",
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
    bucketed = read_json(INPUT_BUCKETED_SUMMARY)
    row = {
        "row_id": "MAIN-ORCH24-PREFILL-DELIVERY-REGISTRY-BUCKETED-SCORER-001",
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
        "action_rows": bucketed["rows"],
        "prefill_target_rows": bucketed["prefill_target_rows"],
        "generic_no_scorer_rows_before": bucketed["generic_no_scorer_rows_before"],
        "generic_no_scorer_rows_after": bucketed["generic_no_scorer_rows_after"],
        "bucket_counts": bucketed["entry_retest_redesign_bucket_counts"],
        "target_action_class_counts": bucketed["prefill_target_action_class_counts"],
        "target_implementation_decision_counts": bucketed[
            "prefill_target_implementation_decision_counts"
        ],
        "metadata_proxy_row_delta": bucketed["numeric_proxy_row_delta"],
        "metadata_proxy_r_sum_delta": bucketed["proxy_r_sum_delta"],
        "exact_r_rows": bucketed["exact_r_rows"],
        "linked_entry_offset_no_fill_rows": bucketed["linked_entry_offset_no_fill_rows"],
        "linked_entry_offset_numeric_proxy_rows": bucketed[
            "linked_entry_offset_numeric_proxy_rows"
        ],
        "linked_entry_offset_proxy_r_sum": bucketed["linked_entry_offset_proxy_r_sum"],
        "safe_flags": SAFE_FLAGS,
        "no_live_behavior": True,
        "no_shadow_log_append": True,
    }
    rows = [row]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated,
        "evidence_class": "MAIN_ORCH24_PREFILL_DELIVERY_REGISTRY_AFTER_BUCKETED_SCORER",
        "claim_boundary": (
            "Forward-capture strategy registry metadata is refreshed after prefill delivery "
            "bucketed scorer output. This changes future strategy snapshot metadata only; "
            "it does not append shadow logs, rescore historical rows, change live behavior, "
            "or open promotion claims."
        ),
        "safe_flags": SAFE_FLAGS,
        "rows": len(rows),
        "watched_strategy_ids": [STRATEGY_ID],
        "metadata_rows_with_stale_tokens": 1 if row["stale_metadata_tokens"] else 0,
        "action_rows": row["action_rows"],
        "prefill_target_rows": row["prefill_target_rows"],
        "generic_no_scorer_rows_before": row["generic_no_scorer_rows_before"],
        "generic_no_scorer_rows_after": row["generic_no_scorer_rows_after"],
        "bucket_counts": row["bucket_counts"],
        "target_action_class_counts": row["target_action_class_counts"],
        "target_implementation_decision_counts": row[
            "target_implementation_decision_counts"
        ],
        "metadata_proxy_row_delta": row["metadata_proxy_row_delta"],
        "metadata_proxy_r_sum_delta": row["metadata_proxy_r_sum_delta"],
        "exact_r_rows": row["exact_r_rows"],
        "linked_entry_offset_no_fill_rows": row["linked_entry_offset_no_fill_rows"],
        "linked_entry_offset_numeric_proxy_rows": row[
            "linked_entry_offset_numeric_proxy_rows"
        ],
        "linked_entry_offset_proxy_r_sum": row["linked_entry_offset_proxy_r_sum"],
        "plate_decision": "PREFILL_DELIVERY_REGISTRY_METADATA_REFRESHED_AFTER_BUCKETED_SCORER_OUTPUT",
    }
    return rows, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "bucketed_scorer_summary": INPUT_BUCKETED_SUMMARY,
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
            "prefill_target_rows": summary["prefill_target_rows"],
            "generic_no_scorer_rows_after": summary["generic_no_scorer_rows_after"],
            "metadata_proxy_row_delta": summary["metadata_proxy_row_delta"],
            "metadata_proxy_r_sum_delta": summary["metadata_proxy_r_sum_delta"],
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
