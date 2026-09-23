"""Verify/write the prefill registry metadata after far-miss control repair."""

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


ROOT = find_repo_root(Path(__file__).resolve())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.forward_capture import FOLLOW_STRATEGY_REGISTRY

ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization"
SOURCE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_FAR_MISS_RETEST_CONTROL_DECISION_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_FAR_MISS_CONTROL_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_FAR_MISS_CONTROL_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_FAR_MISS_CONTROL_OUTPUT_MANIFEST_{DATE}.json"

EXPECTED_BRANCH = "PREFILL_FAR_MISS_RETEST_CONTROL_DEFAULT_OFF_WITH_CONCENTRATION_GUARD"
EXPECTED_IMPL = "KEEP_DEFAULT_OFF_PREFILL_FAR_MISS_RETEST_CONTROL_CANDIDATE_WITH_CONCENTRATION_GUARD"
STALE_TOKENS = [
    "84 kill / 10 redesign",
    "KEEP_PREFILL_KILL_REDESIGN_SPLIT_AND_DESIGN_FAR_MISS_RETEST_CONTROL_FOR_10_ROWS",
    "PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_WITH_KILL_REDESIGN_SPLIT",
]
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_info(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path) if path.exists() else None,
    }


def prefill_registry_row() -> dict[str, Any]:
    for row in FOLLOW_STRATEGY_REGISTRY:
        if row.get("strategy_id") == "PREFILL_DELIVERY_REVERSAL_PATH":
            return dict(row)
    raise RuntimeError("PREFILL_DELIVERY_REVERSAL_PATH not found")


def main() -> None:
    source = json.loads(SOURCE_SUMMARY.read_text(encoding="utf-8"))
    registry = prefill_registry_row()
    text = " ".join(str(registry.get(key, "")) for key in ("branch_decision", "decision_evidence", "implementation_candidate"))
    stale = [token for token in STALE_TOKENS if token in text]
    row = {
        "route_id": ROUTE_ID,
        "row_id": "MAIN-ORCH24-PREFILL-REGISTRY-FAR-MISS-CONTROL-001",
        "strategy_id": "PREFILL_DELIVERY_REVERSAL_PATH",
        "evidence_class": "MAIN_ORCH24_PREFILL_REGISTRY_AFTER_FAR_MISS_CONTROL_DECISION",
        "generated_utc": utc_now(),
        "branch_decision": registry.get("branch_decision"),
        "implementation_candidate": registry.get("implementation_candidate"),
        "decision_evidence": registry.get("decision_evidence"),
        "metadata_rows_with_stale_tokens": len(stale),
        "stale_tokens": stale,
        "action_class_delta_vs_previous": source["action_class_delta_vs_previous"],
        "redesign_rows_before": source["redesign_rows_before"],
        "redesign_rows_after": source["redesign_rows_after"],
        "affected_candidate_rows": source["affected_candidate_rows"],
        "affected_entry_offset_proxy_rows": source["affected_entry_offset_proxy_rows"],
        "affected_entry_offset_proxy_r_sum": source["affected_entry_offset_proxy_r_sum"],
        "prefill_metadata_proxy_rows": source["prefill_metadata_proxy_rows"],
        "exact_r_rows": source["exact_r_rows"],
        "safe_flags": SAFE_FLAGS,
    }
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": row["generated_utc"],
        "evidence_class": row["evidence_class"],
        "claim_boundary": (
            "Forward-capture strategy registry metadata now cites the far-miss retest-control default-off "
            "decision. Metadata-only; no shadow append, live behavior, validation, or promotion claim."
        ),
        "rows": 1,
        "expected_branch_decision": EXPECTED_BRANCH,
        "expected_implementation_candidate": EXPECTED_IMPL,
        "metadata_rows_with_stale_tokens": len(stale),
        "action_class_delta_vs_previous": source["action_class_delta_vs_previous"],
        "redesign_rows_after": source["redesign_rows_after"],
        "affected_candidate_rows": source["affected_candidate_rows"],
        "affected_entry_offset_proxy_rows": source["affected_entry_offset_proxy_rows"],
        "affected_entry_offset_proxy_r_sum": source["affected_entry_offset_proxy_r_sum"],
        "prefill_metadata_proxy_rows": source["prefill_metadata_proxy_rows"],
        "exact_r_rows": source["exact_r_rows"],
        "safe_flags": SAFE_FLAGS,
        "plate_decision": "PREFILL_REGISTRY_METADATA_REFRESHED_AFTER_FAR_MISS_CONTROL_DECISION",
    }
    OUTPUT_LEDGER.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "route_id": ROUTE_ID,
        "evidence_class": row["evidence_class"],
        "generated_utc": row["generated_utc"],
        "inputs": {
            "source_summary": file_info(SOURCE_SUMMARY),
            "forward_capture": file_info(ROOT / "src/research_infra/forward_capture.py"),
            "forward_capture_tests": file_info(ROOT / "tests/test_forward_capture_shadow_loggers.py"),
        },
        "outputs": {
            "ledger": file_info(OUTPUT_LEDGER),
            "summary": file_info(OUTPUT_SUMMARY),
        },
        "summary_counts": {
            "rows": 1,
            "metadata_rows_with_stale_tokens": len(stale),
            "redesign_rows_after": source["redesign_rows_after"],
            "affected_candidate_rows": source["affected_candidate_rows"],
            "affected_entry_offset_proxy_r_sum": source["affected_entry_offset_proxy_r_sum"],
            "exact_r_rows": source["exact_r_rows"],
        },
        "safe_flags": SAFE_FLAGS,
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
