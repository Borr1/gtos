"""Materialize current impact of moonshot selected-action forward-shadow registry wiring."""

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
    MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY,
)
from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    DEFAULT_CANDIDATES,
    DEFAULT_PATHS,
    MOONSHOT_SELECTED_ACTION_STRATEGY_IDS,
    build_strategy_outcome_rows,
    latest_path_rows_by_candidate,
    read_jsonl,
)

ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_FORWARD_SHADOW_REGISTRY_INTEGRATION_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_FORWARD_SHADOW_REGISTRY_INTEGRATION_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_FORWARD_SHADOW_REGISTRY_INTEGRATION_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def moonshot_snapshots() -> list[dict[str, Any]]:
    return [
        {
            **dict(item),
            "applicability": "candidate_relevant",
            "decision_time_status": "PROJECTED_ON_CURRENT_CANDIDATE_DENOMINATOR",
            "outcome_status": "UNRESOLVED_REQUIRES_FORWARD_SOURCE_CAPTURE",
        }
        for item in MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY
    ]


def build() -> dict[str, Any]:
    generated_utc = datetime.now(UTC).isoformat()
    candidates = {
        str(row.get("candidate_id") or ""): row
        for row in read_jsonl(DEFAULT_CANDIDATES)
        if row.get("candidate_id")
    }
    raw_paths = read_jsonl(DEFAULT_PATHS)
    latest_paths = latest_path_rows_by_candidate(raw_paths)
    projected_rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    snapshots = moonshot_snapshots()

    for path_row in latest_paths:
        candidate_id = str(path_row.get("candidate_id") or "")
        candidate = candidates.get(candidate_id)
        if not candidate:
            skipped["candidate_missing_for_path"] += 1
            continue
        projected_candidate = {**candidate, "strategy_snapshots": snapshots}
        for row in build_strategy_outcome_rows(
            projected_candidate,
            path_row,
            created_at_utc=generated_utc,
        ):
            if str(row.get("strategy_id") or "") not in MOONSHOT_SELECTED_ACTION_STRATEGY_IDS:
                continue
            row["projection_source"] = "CURRENT_LATEST_PATH_DENOMINATOR_WITH_NEW_MOONSHOT_REGISTRY_SNAPSHOTS"
            row["safe_flags"] = SAFE_FLAGS
            row["counted_exact_r"] = False
            row["counted_proxy_r"] = False
            row["runtime_score_allowed"] = False
            row["candidate_use_allowed_now"] = False
            row["live_effect"] = False
            projected_rows.append(row)

    strategy_counts = Counter(str(row.get("strategy_id") or "") for row in projected_rows)
    status_counts = Counter(str(row.get("strategy_status") or "") for row in projected_rows)
    score_counts = Counter(str(row.get("score_status") or "") for row in projected_rows)
    source_capture_status_counts = Counter(
        str(row.get("moonshot_selected_action_source_capture_status") or "")
        for row in projected_rows
    )
    missing_field_counts: Counter[str] = Counter()
    for row in projected_rows:
        for field in row.get("source_capture_missing_fields") or []:
            missing_field_counts[str(field)] += 1

    summary = {
        "route_id": "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION",
        "date": DATE,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "input_files": {
            "strategy_follow_candidates": {
                "path": str(DEFAULT_CANDIDATES),
                "sha256": sha256_file(DEFAULT_CANDIDATES),
                "size_bytes": DEFAULT_CANDIDATES.stat().st_size,
                "rows": len(candidates),
            },
            "candidate_path_follow": {
                "path": str(DEFAULT_PATHS),
                "sha256": sha256_file(DEFAULT_PATHS),
                "size_bytes": DEFAULT_PATHS.stat().st_size,
                "raw_rows": len(raw_paths),
                "latest_path_rows": len(latest_paths),
            },
        },
        "moonshot_registry_strategy_count": len(MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY),
        "moonshot_registry_strategy_ids": sorted(MOONSHOT_SELECTED_ACTION_STRATEGY_IDS),
        "projected_rows": len(projected_rows),
        "projected_candidate_count": len({str(row.get("candidate_id") or "") for row in projected_rows}),
        "strategy_counts": dict(sorted(strategy_counts.items())),
        "strategy_status_counts": dict(sorted(status_counts.items())),
        "score_status_counts": dict(sorted(score_counts.items())),
        "moonshot_selected_action_source_capture_status_counts": dict(
            sorted(source_capture_status_counts.items())
        ),
        "source_capture_ready_rows": sum(row.get("source_capture_ready") is True for row in projected_rows),
        "source_capture_waiting_rows": sum(row.get("source_capture_ready") is not True for row in projected_rows),
        "source_capture_missing_field_counts": dict(sorted(missing_field_counts.items())),
        "proxy_r_rows": sum(row.get("strategy_proxy_r") is not None for row in projected_rows),
        "exact_r_rows": 0,
        "counted_proxy_r_rows": sum(row.get("counted_proxy_r") is True for row in projected_rows),
        "runtime_score_allowed_rows": sum(row.get("runtime_score_allowed") is True for row in projected_rows),
        "candidate_use_allowed_now_rows": sum(row.get("candidate_use_allowed_now") is True for row in projected_rows),
        "live_effect_true_rows": sum(row.get("live_effect") is True for row in projected_rows),
        "skipped": dict(sorted(skipped.items())),
        "research_safety": {
            "changes_live_behavior": False,
            "changes_prompt_risk_selector_execution": False,
            "changes_shadow_log_history": False,
            "opens_exact_r": False,
            "opens_counted_proxy_r": False,
            "uses_proxy_delta_as_r": False,
        },
    }

    write_jsonl(OUTPUT_LEDGER, projected_rows)
    write_json(SUMMARY_PATH, summary)
    manifest = {
        "route_id": summary["route_id"],
        "date": DATE,
        "generated_utc": generated_utc,
        "description": "Current-denominator projection of default-off moonshot selected-action registry wiring.",
        "output_files": {
            "projection_ledger": {
                "path": str(OUTPUT_LEDGER),
                "sha256": sha256_file(OUTPUT_LEDGER),
                "size_bytes": OUTPUT_LEDGER.stat().st_size,
                "rows": len(projected_rows),
            },
            "summary": {
                "path": str(SUMMARY_PATH),
                "sha256": sha256_file(SUMMARY_PATH),
                "size_bytes": SUMMARY_PATH.stat().st_size,
            },
        },
        "counts": {
            "projected_rows": summary["projected_rows"],
            "projected_candidate_count": summary["projected_candidate_count"],
            "moonshot_registry_strategy_count": summary["moonshot_registry_strategy_count"],
            "source_capture_waiting_rows": summary["source_capture_waiting_rows"],
            "proxy_r_rows": summary["proxy_r_rows"],
        },
        "safe_flags": SAFE_FLAGS,
    }
    write_json(MANIFEST_PATH, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
