#!/usr/bin/env python3
"""Backfill default-off AI-narrowing policy shadow evaluations.

This script reads existing strategy-follow candidate rows, adapts them to the
AI-narrowing policy event contract, and evaluates them against the committed
default-off policy registry. It is research/observability only: it does not
skip AI calls, alter prompts, place orders, call broker APIs, or fetch paid
data.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (  # noqa: E402
    AI_NARROWING_EVENT_REQUIRED_FIELDS,
    AINarrowingPolicyRegistry,
    ai_narrowing_event_from_source_row,
    stable_hash,
    summarize_ai_narrowing_policy_events,
    summarize_ai_narrowing_policy_registry_evaluations,
)


SCHEMA_VERSION = "ai_narrowing_policy_shadow_evaluation_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DEFAULT_POLICY_LEDGER = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_AI_NARROWING_POLICY_LEDGER_2026-05-18.jsonl"
)
DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/ai_narrowing_policy_shadow_evaluations.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/AI_NARROWING_POLICY_SHADOW_EVALUATIONS_2026-05-18.json")
DEFAULT_REPORT_MD = Path("research/program_control/AI_NARROWING_POLICY_SHADOW_EVALUATIONS_2026-05-18.md")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_path(path: Path) -> str | None:
    if not path.exists():
        return None
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append((line_no, row))
    return rows


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) + "\n")


def existing_row_keys(path: Path) -> set[str]:
    return {str(row.get("row_key")) for _, row in read_jsonl_with_lines(path) if row.get("row_key")}


def build_shadow_evaluation_row(
    *,
    candidate: dict[str, Any],
    candidate_line_no: int,
    registry: AINarrowingPolicyRegistry,
    candidate_source_path: Path,
    candidate_source_sha256: str | None,
    policy_ledger_path: Path,
    policy_ledger_sha256: str | None,
    generated_at_utc: str,
) -> dict[str, Any]:
    event_row_id = str(candidate.get("candidate_id") or f"candidate_line_{candidate_line_no}")
    event = ai_narrowing_event_from_source_row(
        candidate,
        event_row_id=event_row_id,
        source_kind="strategy_follow_candidate_forward_shadow",
        source_artifact=str(candidate_source_path).replace("\\", "/"),
        source_line_no=candidate_line_no,
        source_sha256=candidate_source_sha256,
        required_event_fields=AI_NARROWING_EVENT_REQUIRED_FIELDS,
    )
    evaluation_row_id = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "candidate_id": candidate.get("candidate_id"),
            "candidate_line_no": candidate_line_no,
            "candidate_source_sha256": candidate_source_sha256,
            "policy_ledger_sha256": policy_ledger_sha256,
            "selector_scope_key": event.get("selector_scope_key"),
        },
        length=32,
    )
    evaluation = registry.evaluate_event(event, evaluation_row_id=evaluation_row_id)
    row_key = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "evaluation_row_id": evaluation_row_id,
            "event_adapter_status": event.get("event_adapter_status"),
            "registry_eval_status": evaluation.get("ai_narrowing_registry_eval_status"),
            "matched_policy_row_ids": evaluation.get("matched_policy_row_ids"),
        },
        length=32,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": row_key,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "candidate_id": candidate.get("candidate_id"),
        "candidate_source_path": str(candidate_source_path).replace("\\", "/"),
        "candidate_source_line_no": candidate_line_no,
        "candidate_source_sha256": candidate_source_sha256,
        "policy_ledger_path": str(policy_ledger_path).replace("\\", "/"),
        "policy_ledger_sha256": policy_ledger_sha256,
        "event": event,
        "evaluation": evaluation,
        "event_adapter_status": event.get("event_adapter_status"),
        "missing_required_fields": event.get("missing_required_fields") or [],
        "selector_scope_key": event.get("selector_scope_key"),
        "ai_narrowing_registry_eval_status": evaluation.get("ai_narrowing_registry_eval_status"),
        "matched_policy_rows": evaluation.get("matched_policy_rows"),
        "matched_policy_row_ids": evaluation.get("matched_policy_row_ids") or [],
        "ai_narrowing_review_ready": evaluation.get("ai_narrowing_review_ready"),
        "capacity_blocklist_required_before_ai_narrowing": evaluation.get(
            "capacity_blocklist_required_before_ai_narrowing"
        ),
        "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
        "ai_call_skip_allowed_now": False,
        "production_change_opened_now": False,
        "live_ai_runtime_change_now": False,
        "live_selector_change_now": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def build_shadow_evaluations(
    *,
    candidate_rows: list[tuple[int, dict[str, Any]]],
    policy_rows: list[dict[str, Any]],
    candidate_source_path: Path,
    candidate_source_sha256: str | None,
    policy_ledger_path: Path,
    policy_ledger_sha256: str | None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    generated = generated_at_utc or utc_now()
    registry = AINarrowingPolicyRegistry(policy_rows)
    return [
        build_shadow_evaluation_row(
            candidate=row,
            candidate_line_no=line_no,
            registry=registry,
            candidate_source_path=candidate_source_path,
            candidate_source_sha256=candidate_source_sha256,
            policy_ledger_path=policy_ledger_path,
            policy_ledger_sha256=policy_ledger_sha256,
            generated_at_utc=generated,
        )
        for line_no, row in candidate_rows
    ]


def build_report(
    *,
    rows: list[dict[str, Any]],
    appended_rows: list[dict[str, Any]],
    output_path: Path,
    candidate_rows: int,
    policy_rows: int,
    candidate_source_sha256: str | None,
    policy_ledger_sha256: str | None,
) -> dict[str, Any]:
    event_summary = summarize_ai_narrowing_policy_events([row["event"] for row in rows])
    eval_summary = summarize_ai_narrowing_policy_registry_evaluations([row["evaluation"] for row in rows])
    adapter_counts = Counter(str(row.get("event_adapter_status") or "UNKNOWN") for row in rows)
    eval_counts = Counter(str(row.get("ai_narrowing_registry_eval_status") or "UNKNOWN") for row in rows)
    return {
        "schema_version": "ai_narrowing_policy_shadow_evaluations_report_v1",
        "generated_at_utc": utc_now(),
        "status": "OK_DEFAULT_OFF_AI_NARROWING_SHADOW_EVALUATIONS_DOCUMENTED",
        "output_path": str(output_path).replace("\\", "/"),
        "output_schema_version": SCHEMA_VERSION,
        "candidate_rows": candidate_rows,
        "policy_rows": policy_rows,
        "rows_computed": len(rows),
        "rows_appended_this_run": len(appended_rows),
        "candidate_source_sha256": candidate_source_sha256,
        "policy_ledger_sha256": policy_ledger_sha256,
        "event_adapter_status_counts": dict(sorted(adapter_counts.items())),
        "registry_eval_status_counts": dict(sorted(eval_counts.items())),
        "event_summary": event_summary,
        "registry_eval_summary": eval_summary,
        "ai_call_skip_allowed_now_rows": sum(bool(row.get("ai_call_skip_allowed_now")) for row in rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "live_ai_runtime_change_now_rows": sum(bool(row.get("live_ai_runtime_change_now")) for row in rows),
        "live_selector_change_now_rows": sum(bool(row.get("live_selector_change_now")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "claim_boundary": (
            "Rows are default-off policy shadow evaluations only. They do not skip AI, "
            "enable a selector, alter live decisions, call paid APIs, or touch broker state."
        ),
        "promotion_verdict": PROMOTION_VERDICT,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# AI Narrowing Policy Shadow Evaluations - 2026-05-18",
        "",
        f"**Status:** `{report['status']}`",
        f"**Rows computed:** `{report['rows_computed']}`",
        f"**Rows appended this run:** `{report['rows_appended_this_run']}`",
        f"**Candidate rows:** `{report['candidate_rows']}`",
        f"**Policy rows:** `{report['policy_rows']}`",
        "",
        "## Counts",
        "",
        f"- Event adapter statuses: `{report['event_adapter_status_counts']}`",
        f"- Registry eval statuses: `{report['registry_eval_status_counts']}`",
        f"- ai_call_skip_allowed_now_rows: `{report['ai_call_skip_allowed_now_rows']}`",
        f"- runtime_candidate_use_permitted_rows: `{report['runtime_candidate_use_permitted_rows']}`",
        f"- paid_api_or_vendor_call_rows: `{report['paid_api_or_vendor_call_rows']}`",
        "",
        "## Boundary",
        "",
        report["claim_boundary"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--policy-ledger", type=Path, default=DEFAULT_POLICY_LEDGER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args(argv)

    candidate_rows = read_jsonl_with_lines(args.candidates)
    policy_rows = [row for _, row in read_jsonl_with_lines(args.policy_ledger)]
    candidate_sha = sha256_path(args.candidates)
    policy_sha = sha256_path(args.policy_ledger)
    rows = build_shadow_evaluations(
        candidate_rows=candidate_rows,
        policy_rows=policy_rows,
        candidate_source_path=args.candidates,
        candidate_source_sha256=candidate_sha,
        policy_ledger_path=args.policy_ledger,
        policy_ledger_sha256=policy_sha,
    )
    existing = existing_row_keys(args.output)
    appended = [row for row in rows if str(row.get("row_key")) not in existing]
    append_jsonl(args.output, appended)
    report = build_report(
        rows=rows,
        appended_rows=appended,
        output_path=args.output,
        candidate_rows=len(candidate_rows),
        policy_rows=len(policy_rows),
        candidate_source_sha256=candidate_sha,
        policy_ledger_sha256=policy_sha,
    )
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    write_markdown(report, args.report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "rows_computed": report["rows_computed"],
                "rows_appended": report["rows_appended_this_run"],
                "event_adapter_status_counts": report["event_adapter_status_counts"],
                "registry_eval_status_counts": report["registry_eval_status_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
