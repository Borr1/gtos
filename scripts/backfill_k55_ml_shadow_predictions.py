#!/usr/bin/env python3
"""Backfill append-only LTO-023 K55 ML shadow feature/prediction rows."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.k55_ml_shadow import (  # noqa: E402
    DEFAULT_MODEL_REGISTRY_PATH,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_ml_shadow_rows,
    report_payload,
    target_registry_payload,
    write_registry_markdown,
    write_report_markdown,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_MSO_JOINS = Path("shadow_logs/candidate_mso_snapshot_joins.jsonl")
DEFAULT_ACCOUNT_TRUTH = Path("shadow_logs/account_truth_reconciliation_status.jsonl")
DEFAULT_BROKER_AUDIT = Path("shadow_logs/broker_actual_r_audit.jsonl")
DEFAULT_J46_J49 = Path("shadow_logs/j46_j49_exit_comparator_audit.jsonl")
DEFAULT_S79 = Path("shadow_logs/s79_side_aware_risk_context.jsonl")
DEFAULT_REGIME = Path("shadow_logs/regime_decay_outcome_join.jsonl")
DEFAULT_DECISION = Path("shadow_logs/decision_layer_diagnostics_join.jsonl")
DEFAULT_MECHANICAL = Path("shadow_logs/mechanical_context_diagnostics_join.jsonl")
DEFAULT_DATABENTO_TRIGGER = Path("shadow_logs/databento_live_trigger_decisions.jsonl")
DEFAULT_SIERRA_PROXY = Path("shadow_logs/sierra_proxy_registry_status.jsonl")
DEFAULT_SIERRA_DEPTH_FEATURES = Path("shadow_logs/sierra_depth_feature_snapshots.jsonl")
DEFAULT_ORDERFLOW_STATUS = Path("shadow_logs/orderflow_primitives_status.jsonl")
DEFAULT_SIERRA_DEPTH_STATUS = Path("shadow_logs/sierra_depth_enrichment_status.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/ml_shadow_predictions.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.md")
DEFAULT_REGISTRY_JSON = Path("research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.json")
DEFAULT_REGISTRY_MD = Path("research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md")


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


def existing_row_keys(path: Path) -> set[str]:
    return {str(row.get("row_key")) for _, row in read_jsonl_with_lines(path) if row.get("row_key")}


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--mso-joins", type=Path, default=DEFAULT_MSO_JOINS)
    parser.add_argument("--account-truth", type=Path, default=DEFAULT_ACCOUNT_TRUTH)
    parser.add_argument("--broker-audit", type=Path, default=DEFAULT_BROKER_AUDIT)
    parser.add_argument("--j46-j49", type=Path, default=DEFAULT_J46_J49)
    parser.add_argument("--s79", type=Path, default=DEFAULT_S79)
    parser.add_argument("--regime", type=Path, default=DEFAULT_REGIME)
    parser.add_argument("--decision", type=Path, default=DEFAULT_DECISION)
    parser.add_argument("--mechanical", type=Path, default=DEFAULT_MECHANICAL)
    parser.add_argument("--databento-trigger", type=Path, default=DEFAULT_DATABENTO_TRIGGER)
    parser.add_argument("--sierra-proxy", type=Path, default=DEFAULT_SIERRA_PROXY)
    parser.add_argument("--sierra-depth-features", type=Path, default=DEFAULT_SIERRA_DEPTH_FEATURES)
    parser.add_argument("--orderflow-status", type=Path, default=DEFAULT_ORDERFLOW_STATUS)
    parser.add_argument("--sierra-depth-status", type=Path, default=DEFAULT_SIERRA_DEPTH_STATUS)
    parser.add_argument("--model-artifact", type=Path, default=DEFAULT_MODEL_REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--registry-md", type=Path, default=DEFAULT_REGISTRY_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    candidate_rows = read_jsonl_with_lines(args.candidates)
    sources = {
        "candidate_rows": len(candidate_rows),
        "mso_join_rows": len(read_jsonl_with_lines(args.mso_joins)),
        "account_truth_rows": len(read_jsonl_with_lines(args.account_truth)),
        "broker_audit_rows": len(read_jsonl_with_lines(args.broker_audit)),
        "j46_j49_rows": len(read_jsonl_with_lines(args.j46_j49)),
        "s79_rows": len(read_jsonl_with_lines(args.s79)),
        "regime_rows": len(read_jsonl_with_lines(args.regime)),
        "decision_rows": len(read_jsonl_with_lines(args.decision)),
        "mechanical_rows": len(read_jsonl_with_lines(args.mechanical)),
        "databento_trigger_rows": len(read_jsonl_with_lines(args.databento_trigger)),
        "sierra_proxy_rows": len(read_jsonl_with_lines(args.sierra_proxy)),
        "sierra_depth_feature_rows": len(read_jsonl_with_lines(args.sierra_depth_features)),
        "orderflow_status_rows": len(read_jsonl_with_lines(args.orderflow_status)),
        "sierra_depth_status_rows": len(read_jsonl_with_lines(args.sierra_depth_status)),
    }
    rows = build_ml_shadow_rows(
        candidate_rows,
        mso_rows=read_jsonl_with_lines(args.mso_joins),
        account_truth_rows=read_jsonl_with_lines(args.account_truth),
        broker_rows=read_jsonl_with_lines(args.broker_audit),
        j46_rows=read_jsonl_with_lines(args.j46_j49),
        s79_rows=read_jsonl_with_lines(args.s79),
        regime_rows=read_jsonl_with_lines(args.regime),
        decision_rows=read_jsonl_with_lines(args.decision),
        mechanical_rows=read_jsonl_with_lines(args.mechanical),
        databento_trigger_rows=read_jsonl_with_lines(args.databento_trigger),
        sierra_proxy_rows=read_jsonl_with_lines(args.sierra_proxy),
        sierra_depth_rows=read_jsonl_with_lines(args.sierra_depth_features),
        orderflow_status_rows=read_jsonl_with_lines(args.orderflow_status),
        sierra_status_rows=read_jsonl_with_lines(args.sierra_depth_status),
        model_artifact_path=args.model_artifact,
        generated_at_utc=generated_at,
    )
    existing = existing_row_keys(args.output)
    appended = [row for row in rows if str(row.get("row_key")) not in existing]
    append_jsonl(args.output, appended)

    registry = target_registry_payload(generated_at_utc=generated_at)
    write_json(args.registry_json, registry)
    write_registry_markdown(registry, args.registry_md)
    report = report_payload(
        rows,
        appended,
        args.output,
        source_counts=sources,
        model_artifact_path=args.model_artifact,
        generated_at_utc=generated_at,
    )
    write_json(args.report_json, report)
    write_report_markdown(report, args.report_md)
    print(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "promotion_verdict": PROMOTION_VERDICT,
                "rows_computed": len(rows),
                "rows_appended": len(appended),
                "report_json": str(args.report_json),
                "report_md": str(args.report_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
