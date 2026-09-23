"""Materialize entry-offset registry metadata after M15 hard no-fill repair."""

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

INPUT_REPAIR_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_SUMMARY_2026-05-16.json"
INPUT_FORWARD_CAPTURE = Path("src/research_infra/forward_capture.py")
INPUT_FORWARD_CAPTURE_TESTS = Path("tests/test_forward_capture_shadow_loggers.py")

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_REGISTRY_AFTER_M15_HARD_NO_FILL_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_REGISTRY_AFTER_M15_HARD_NO_FILL_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = (
    ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_REGISTRY_AFTER_M15_HARD_NO_FILL_OUTPUT_MANIFEST_{DATE}.json"
)

STRATEGY_ID = "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
STALE_TOKENS = (
    "MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION",
    "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_TICK_REPLAY_SCORER_WITH_SOURCE_GATES",
    "KEEP_DEFAULT_OFF_ENTRY_OFFSET_050R_TICK_REPLAY_SCORER_WITH_SPREAD_AWARE_FILL_CONTRACT",
    "and 2 tick-source repair rows",
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
    repair = read_json(INPUT_REPAIR_SUMMARY)
    row = {
        "row_id": "MAIN-ORCH24-ENTRY-OFFSET-REGISTRY-M15-HARD-NOFILL-001",
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
        "candidate_rows": repair["candidate_rows"],
        "no_fill_denominator_rows": sum(
            count
            for status, count in repair["after_entry_scorer_status_counts"].items()
            if status != "NOT_APPLICABLE_NOT_ENTRY_REDESIGN_DENOMINATOR"
        ),
        "numeric_proxy_rows": repair["after_numeric_proxy_rows"],
        "proxy_r_sum": repair["after_proxy_r_sum"],
        "numeric_proxy_row_delta_from_repair": repair["numeric_proxy_row_delta"],
        "proxy_r_sum_delta_from_repair": repair["proxy_r_sum_delta"],
        "m15_hard_no_fill_repaired_rows": repair["m15_hard_no_fill_repaired_rows"],
        "source_repair_rows_after": repair["after_entry_action_class_counts"].get("SOURCE_REPAIR", 0),
        "after_entry_action_class_counts": repair["after_entry_action_class_counts"],
        "after_entry_scorer_status_counts": repair["after_entry_scorer_status_counts"],
        "metadata_proxy_row_delta": 0,
        "metadata_proxy_r_sum_delta": 0.0,
        "exact_r_rows": repair["exact_r_rows"],
        "safe_flags": SAFE_FLAGS,
        "no_live_behavior": True,
        "no_shadow_log_append": True,
    }
    rows = [row]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated,
        "evidence_class": "MAIN_ORCH24_ENTRY_OFFSET_REGISTRY_AFTER_M15_HARD_NO_FILL",
        "claim_boundary": (
            "Forward-capture entry-offset strategy registry metadata is refreshed after the "
            "M15 hard no-fill repair. This changes future strategy snapshot metadata only; "
            "it does not append shadow logs, rescore historical rows, change live behavior, "
            "or open promotion claims."
        ),
        "safe_flags": SAFE_FLAGS,
        "rows": len(rows),
        "watched_strategy_ids": [STRATEGY_ID],
        "metadata_rows_with_stale_tokens": 1 if row["stale_metadata_tokens"] else 0,
        "candidate_rows": row["candidate_rows"],
        "no_fill_denominator_rows": row["no_fill_denominator_rows"],
        "numeric_proxy_rows": row["numeric_proxy_rows"],
        "proxy_r_sum": row["proxy_r_sum"],
        "numeric_proxy_row_delta_from_repair": row["numeric_proxy_row_delta_from_repair"],
        "proxy_r_sum_delta_from_repair": row["proxy_r_sum_delta_from_repair"],
        "m15_hard_no_fill_repaired_rows": row["m15_hard_no_fill_repaired_rows"],
        "source_repair_rows_after": row["source_repair_rows_after"],
        "after_entry_action_class_counts": row["after_entry_action_class_counts"],
        "after_entry_scorer_status_counts": row["after_entry_scorer_status_counts"],
        "metadata_proxy_row_delta": 0,
        "metadata_proxy_r_sum_delta": 0.0,
        "exact_r_rows": row["exact_r_rows"],
        "plate_decision": "ENTRY_OFFSET_REGISTRY_METADATA_REFRESHED_AFTER_M15_HARD_NO_FILL_REPAIR",
    }
    return rows, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "entry_offset_m15_hard_no_fill_summary": INPUT_REPAIR_SUMMARY,
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
            "candidate_rows": summary["candidate_rows"],
            "numeric_proxy_rows": summary["numeric_proxy_rows"],
            "source_repair_rows_after": summary["source_repair_rows_after"],
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
