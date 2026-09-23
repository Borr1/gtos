"""Materialize strategy registry metadata refresh against current action rows."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
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

INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_LEDGER_2026-05-17.jsonl"
)
INPUT_ACTION_SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_SUMMARY_2026-05-17.json"
)
INPUT_FORWARD_CAPTURE = Path("src/research_infra/forward_capture.py")
INPUT_FORWARD_CAPTURE_TESTS = Path("tests/test_forward_capture_shadow_loggers.py")

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_STRATEGY_REGISTRY_METADATA_REFRESH_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_STRATEGY_REGISTRY_METADATA_REFRESH_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_STRATEGY_REGISTRY_METADATA_REFRESH_OUTPUT_MANIFEST_{DATE}.json"

WATCHED_STRATEGY_IDS = [
    "V2_STRUCT_FVG_MID_EDGE",
    "V3_FVG_ONLY_RESCUE_RISK_BANK",
    "FVG_OB_CONFLUENCE_OB_AFTER_FVG",
    "V2_STRUCT_SWING_PROTECTED",
    "V2_STRUCT_COMPOSITE_ANY",
    "V3_FVG_THEN_OB_TAIL_RISK_BANK",
    "V3_OB_LOCK_PULLBACK_RISK_BANK",
    "V3_OB_LOCK_COST_AWARE_MIN_R",
    "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
    "PENDING_LIMIT_LIFECYCLE",
]


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def registry_action_class(branch_decision: str) -> str:
    if branch_decision.startswith("IMPLEMENT") or branch_decision.startswith("KEEP_DEFAULT_OFF"):
        return "IMPLEMENT_OR_KEEP_DEFAULT_OFF_METADATA"
    if branch_decision.startswith("KEEP"):
        return "KEEP_SOURCE_CAPTURE_OR_CONTEXT_METADATA"
    if branch_decision.startswith("REDESIGN"):
        return "REDESIGN_METADATA"
    if branch_decision.startswith("SOURCE_CAPTURE"):
        return "SOURCE_REPAIR_METADATA"
    return "PRESERVE_METADATA"


def proxy_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [safe_float(row.get("after_proxy_r")) for row in rows]
    numeric = [value for value in values if value is not None]
    total = sum(numeric)
    return {
        "numeric_proxy_rows": len(numeric),
        "proxy_r_sum": round(total, 8),
        "proxy_r_mean": round(total / len(numeric), 8) if numeric else None,
    }


def action_rows_for_strategy(action_rows: list[dict[str, Any]], strategy_id: str) -> list[dict[str, Any]]:
    if strategy_id == "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER":
        return [
            row
            for row in action_rows
            if "ENTRY_OFFSET_050R" in str(row.get("implementation_decision") or "")
        ]
    return [row for row in action_rows if row.get("strategy_id") == strategy_id]


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    action_summary = read_json(INPUT_ACTION_SUMMARY)
    registry = {str(item.get("strategy_id") or ""): dict(item) for item in FOLLOW_STRATEGY_REGISTRY}
    output_rows: list[dict[str, Any]] = []

    for strategy_id in WATCHED_STRATEGY_IDS:
        snapshot = registry[strategy_id]
        rows = action_rows_for_strategy(action_rows, strategy_id)
        stats = proxy_stats(rows)
        output_rows.append(
            {
                "row_id": f"MAIN-ORCH24-STRATEGY-REGISTRY-METADATA-{len(output_rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "generated_utc": generated,
                "strategy_id": strategy_id,
                "family": snapshot.get("family"),
                "evidence_role": snapshot.get("evidence_role"),
                "promotion_verdict": snapshot.get("promotion_verdict"),
                "branch_decision": snapshot.get("branch_decision"),
                "implementation_candidate": snapshot.get("implementation_candidate"),
                "decision_evidence": snapshot.get("decision_evidence"),
                "registry_action_class": registry_action_class(str(snapshot.get("branch_decision") or "")),
                "current_action_rows": len(rows),
                "current_action_class_counts": dict(Counter(row.get("action_class") for row in rows)),
                "current_implementation_decision_counts": dict(
                    Counter(row.get("implementation_decision") for row in rows)
                ),
                "current_numeric_proxy_rows": stats["numeric_proxy_rows"],
                "current_proxy_r_sum": stats["proxy_r_sum"],
                "current_proxy_r_mean": stats["proxy_r_mean"],
                "exact_r_rows": 0,
                "metadata_refresh_proxy_row_delta": 0,
                "metadata_refresh_proxy_r_sum_delta": 0.0,
                "safe_flags": SAFE_FLAGS,
                "no_live_behavior": True,
                "no_shadow_log_append": True,
            }
        )

    branch_counts = Counter(row["branch_decision"] for row in output_rows)
    summary = {
        "route_id": ROUTE_ID,
        "evidence_class": "MAIN_ORCH24_STRATEGY_REGISTRY_METADATA_REFRESH",
        "generated_utc": generated,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": (
            "Forward-capture strategy snapshot metadata refreshed to match current materialized "
            "action/scorer/source-capture evidence. This changes future metadata labels only; it "
            "does not append shadow logs, change live behavior, or open promotion claims."
        ),
        "rows": len(output_rows),
        "watched_strategy_ids": WATCHED_STRATEGY_IDS,
        "current_action_rows": len(action_rows),
        "current_action_summary_source": str(INPUT_ACTION_SUMMARY),
        "action_queue_proxy_after": action_summary.get("proxy_after"),
        "action_queue_remaining_source_repair_rows": action_summary.get(
            "remaining_source_repair_rows_after"
        ),
        "action_queue_remaining_source_repair_decision_counts": action_summary.get(
            "remaining_source_repair_decision_counts"
        ),
        "metadata_refresh_proxy_row_delta": 0,
        "metadata_refresh_proxy_r_sum_delta": 0.0,
        "exact_r_rows": 0,
        "branch_decision_counts": dict(sorted(branch_counts.items())),
        "registry_action_class_counts": dict(
            Counter(row["registry_action_class"] for row in output_rows)
        ),
        "strategy_proxy_snapshot": {
            row["strategy_id"]: {
                "current_action_rows": row["current_action_rows"],
                "current_numeric_proxy_rows": row["current_numeric_proxy_rows"],
                "current_proxy_r_sum": row["current_proxy_r_sum"],
                "current_action_class_counts": row["current_action_class_counts"],
                "current_implementation_decision_counts": row[
                    "current_implementation_decision_counts"
                ],
            }
            for row in output_rows
        },
        "plate_decision": "STRATEGY_REGISTRY_METADATA_REFRESHED_TO_CURRENT_ACTION_QUEUE",
    }
    return output_rows, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "input_action_ledger": INPUT_ACTION_LEDGER,
        "input_action_summary": INPUT_ACTION_SUMMARY,
        "forward_capture": INPUT_FORWARD_CAPTURE,
        "forward_capture_tests": INPUT_FORWARD_CAPTURE_TESTS,
    }
    outputs = {
        "ledger": OUTPUT_LEDGER,
        "summary": OUTPUT_SUMMARY,
    }
    return {
        "route_id": ROUTE_ID,
        "evidence_class": summary["evidence_class"],
        "generated_utc": summary["generated_utc"],
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
            "metadata_refresh_proxy_row_delta": summary["metadata_refresh_proxy_row_delta"],
            "metadata_refresh_proxy_r_sum_delta": summary["metadata_refresh_proxy_r_sum_delta"],
            "current_action_rows": summary["current_action_rows"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(
        json.dumps(
            {
                "ok": True,
                "rows": summary["rows"],
                "current_action_rows": summary["current_action_rows"],
                "metadata_refresh_proxy_row_delta": summary["metadata_refresh_proxy_row_delta"],
                "metadata_refresh_proxy_r_sum_delta": summary[
                    "metadata_refresh_proxy_r_sum_delta"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
