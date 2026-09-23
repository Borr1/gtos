"""Recompute pending lifecycle source derivations against current rows.

This is read-only for shadow logs. It verifies how many pending lifecycle
source-capture fields can be derived now from existing lifecycle/path evidence
without changing R, broker truth, or live behavior.
"""

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

from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    PENDING_LIFECYCLE_CAPTURE_FIELDS,
    PENDING_LIMIT_STRATEGY_ID,
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    read_jsonl,
)

from build_main_orchestrator_fvg_structural_scorer_candidate_recompute_2026_05_16 import (  # noqa: E402
    latest_by_candidate,
    latest_mechanical_by_candidate_strategy,
    latest_path_by_candidate,
    parse_utc,
    safe_float,
)


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUTS = {
    "strategy_follow_candidates": Path("shadow_logs/strategy_follow_candidates.jsonl"),
    "candidate_path_follow": Path("shadow_logs/candidate_path_follow.jsonl"),
    "live_mechanical_strategy_shadow_outcomes": Path(
        "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"
    ),
    "pending_limit_lifecycle": Path("shadow_logs/pending_limit_lifecycle.jsonl"),
    "candidate_ltf_path_order": Path("shadow_logs/candidate_ltf_path_order.jsonl"),
}

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_OUTPUT_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def status_counts(statuses: dict[str, str] | None) -> dict[str, Any]:
    statuses = statuses or {}
    derived = [
        field
        for field, status in statuses.items()
        if status.startswith("DERIVED_")
    ]
    captured = [
        field
        for field, status in statuses.items()
        if status == "SOURCE_CAPTURED"
    ]
    missing = [
        field
        for field in PENDING_LIFECYCLE_CAPTURE_FIELDS
        if statuses.get(field) in {None, "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW"}
    ]
    return {
        "derived_field_count": len(derived),
        "captured_field_count": len(captured),
        "missing_field_count": len(missing),
        "derived_fields": derived,
        "captured_fields": captured,
        "missing_fields": missing,
    }


def implementation_decision(after: dict[str, Any]) -> str:
    statuses = after.get("pending_lifecycle_source_capture_statuses")
    if not isinstance(statuses, dict):
        return "KEEP_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_SCORER"
    counts = status_counts(statuses)
    if after.get("pending_lifecycle_source_capture_complete") is True:
        return "KEEP_PENDING_LIFECYCLE_SCORER_WITH_CAPTURE_FIELDS_COMPLETE"
    if counts["derived_field_count"] > 0:
        return "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_SOURCE_FIELDS_CURRENT_ROWS_PARTIAL"
    return "KEEP_PENDING_LIFECYCLE_SCORER_FORWARD_CAPTURE_FIELDS_IMPLEMENTED_CURRENT_ROWS_PARTIAL"


def build_rows() -> list[dict[str, Any]]:
    candidates = latest_by_candidate(read_jsonl(INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_jsonl(INPUTS["candidate_path_follow"]))
    mechanical = latest_mechanical_by_candidate_strategy(
        read_jsonl(INPUTS["live_mechanical_strategy_shadow_outcomes"])
    )
    pending_lifecycle_rows = read_jsonl(INPUTS["pending_limit_lifecycle"])
    ltf_rows = read_jsonl(INPUTS["candidate_ltf_path_order"])
    generated = utc_now()

    out: list[dict[str, Any]] = []
    for cid in sorted(candidates):
        candidate = candidates[cid]
        path = paths.get(cid)
        if not path:
            continue
        pending = latest_lifecycle_for_candidate_asof(candidate, path, pending_lifecycle_rows)
        ltf = latest_ltf_for_candidate_asof(candidate, path, ltf_rows)
        after_rows = build_strategy_outcome_rows(
            candidate,
            path,
            pending_lifecycle_row=pending,
            ltf_row=ltf,
            created_at_utc=generated,
        )
        after = next(
            row for row in after_rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID
        )
        before = mechanical.get((cid, PENDING_LIMIT_STRATEGY_ID), {})
        before_counts = status_counts(
            before.get("pending_lifecycle_source_capture_statuses")
            if isinstance(before.get("pending_lifecycle_source_capture_statuses"), dict)
            else None
        )
        after_counts = status_counts(
            after.get("pending_lifecycle_source_capture_statuses")
            if isinstance(after.get("pending_lifecycle_source_capture_statuses"), dict)
            else None
        )
        before_r = before.get("strategy_proxy_r")
        after_r = after.get("strategy_proxy_r")
        out.append(
            {
                "row_id": f"MAIN-ORCH24-PENDING-LIFECYCLE-SOURCE-DERIVATION-{len(out) + 1:05d}",
                "route_id": ROUTE_ID,
                "generated_utc": generated,
                "candidate_id": cid,
                "symbol": after.get("symbol"),
                "side": after.get("side"),
                "asof_latest_candle_utc": after.get("asof_latest_candle_utc"),
                "before_strategy_status": before.get("strategy_status"),
                "after_strategy_status": after.get("strategy_status"),
                "before_score_status": before.get("score_status"),
                "after_score_status": after.get("score_status"),
                "before_outcome_status": before.get("outcome_status"),
                "after_outcome_status": after.get("outcome_status"),
                "before_proxy_r": before_r,
                "after_proxy_r": after_r,
                "proxy_r_delta": None
                if safe_float(before_r) is None or safe_float(after_r) is None
                else round(float(after_r) - float(before_r), 8),
                "before_status_counts": before_counts,
                "after_status_counts": after_counts,
                "after_source_capture_statuses": after.get("pending_lifecycle_source_capture_statuses"),
                "after_source_capture_derivations": after.get("pending_lifecycle_source_capture_derivations"),
                "after_source_capture_complete": after.get("pending_lifecycle_source_capture_complete"),
                "implementation_decision": implementation_decision(after),
                "exact_r": None,
                "safe_flags": SAFE_FLAGS,
                "no_live_behavior": True,
                "no_shadow_log_append": True,
            }
        )
    return out


def mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    before_values = [value for row in rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
    after_values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    internal_rows = [
        row
        for row in rows
        if isinstance(row.get("after_source_capture_statuses"), dict)
    ]
    derived_cells = sum(row["after_status_counts"]["derived_field_count"] for row in internal_rows)
    missing_cells = sum(row["after_status_counts"]["missing_field_count"] for row in internal_rows)
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE",
        "claim_boundary": (
            "Current latest-row recompute of pending lifecycle source-capture derivations only. "
            "Exact broker R is not opened, proxy R is unchanged, and no shadow log append is performed."
        ),
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "internal_pending_lifecycle_rows": len(internal_rows),
        "exact_r_rows": 0,
        "before_numeric_proxy_rows": len(before_values),
        "after_numeric_proxy_rows": len(after_values),
        "numeric_proxy_row_delta": len(after_values) - len(before_values),
        "before_proxy_r_mean": mean(before_values),
        "after_proxy_r_mean": mean(after_values),
        "before_proxy_r_sum": sum(before_values),
        "after_proxy_r_sum": sum(after_values),
        "proxy_r_sum_delta": sum(after_values) - sum(before_values),
        "after_derived_source_field_cells": derived_cells,
        "after_missing_source_field_cells": missing_cells,
        "after_capture_complete_rows": sum(
            1 for row in internal_rows if row.get("after_source_capture_complete") is True
        ),
        "implementation_decision_counts": dict(
            Counter(str(row.get("implementation_decision")) for row in rows)
        ),
        "derived_field_counts": dict(
            Counter(
                field
                for row in internal_rows
                for field in row["after_status_counts"]["derived_fields"]
            )
        ),
        "missing_field_counts": dict(
            Counter(
                field
                for row in internal_rows
                for field in row["after_status_counts"]["missing_fields"]
            )
        ),
        "safe_flags": SAFE_FLAGS,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def build_manifest() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path): {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in INPUTS.values()
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in [OUTPUT_LEDGER, OUTPUT_SUMMARY]
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summarize(rows))
    write_json(OUTPUT_MANIFEST, build_manifest())
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
