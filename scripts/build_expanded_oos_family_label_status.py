#!/usr/bin/env python3
"""Build first-wave expanded-OOS replay/label-status artifacts.

This is a research-only control artifact builder. It does not replay strategy
logic, open outcome slices, call AI APIs, or pull vendor data. Its job is to
close the "silent skip" gap for first-wave families that were converted to
GTOS OHLCV roots but did not yet have a replay or label-status artifact.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DATE = "2026-05-04"
NO_PROMOTION = "NO_PROMOTION_VERDICT"

OUT_DIR = ROOT / "research" / "program_control"
DEFAULT_MATRIX_JSON = OUT_DIR / f"EXPANDED_OOS_FIRST_WAVE_FAMILY_STATUS_MATRIX_{DATE}.json"
DEFAULT_CONVERSION_STATUS_JSON = (
    OUT_DIR / f"EXPANDED_OOS_FIRST_WAVE_BOUNDED_CONVERSION_STATUS_{DATE}.json"
)
DEFAULT_REPLAY_SPEC_JSON = (
    ROOT
    / "research"
    / "phase_3_external_feed_validation"
    / "RAW_OHLC_PREQUENTIAL_REPLAY_SPEC_V1.json"
)
DEFAULT_OUTPUT_JSON = OUT_DIR / f"EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_{DATE}.json"
DEFAULT_OUTPUT_MD = OUT_DIR / f"EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_{DATE}.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: str | Path | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except (OSError, ValueError):
        return str(path).replace("\\", "/")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def split_cohort_symbol(cohort_key: str) -> str:
    parts = str(cohort_key).split("|")
    return parts[0] if parts else ""


def replay_spec_cohorts(spec: Mapping[str, Any]) -> dict[str, list[str]]:
    cohorts: dict[str, list[str]] = {}
    for row in spec.get("cohorts") or []:
        key = str(row.get("cohort_key") or "")
        symbol = split_cohort_symbol(key)
        if symbol:
            cohorts.setdefault(symbol, []).append(key)
    return {symbol: sorted(keys) for symbol, keys in sorted(cohorts.items())}


def target_families(matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for family in matrix.get("families") or []:
        status = str(family.get("replay_or_label_status") or "")
        if status.startswith("NOT_OPENED"):
            rows.append(dict(family))
    return rows


def conversion_rows_by_source(conversion_status: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_source: dict[str, list[dict[str, Any]]] = {}
    for row in conversion_status.get("m15_inventory") or []:
        source = str(row.get("source_symbol") or "")
        if source:
            by_source.setdefault(source, []).append(dict(row))
    return by_source


def rows_for_family(
    family: Mapping[str, Any],
    by_source: Mapping[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in family.get("converted_sources") or []:
        rows.extend(by_source.get(str(source), []))
    return sorted(rows, key=lambda row: (str(row.get("file_symbol")), str(row.get("source_symbol"))))


def source_row_status(row: Mapping[str, Any]) -> str:
    rows = int(row.get("rows") or 0)
    gap_count = int(row.get("gap_count") or 0)
    source_symbol = str(row.get("source_symbol") or "")
    if rows <= 0:
        return "NO_M15_ROWS"
    if source_symbol in {"SIM26-COMEX", "SILM26-COMEX", "VXMM26-CFE"}:
        return "SPARSE_SOURCE_WARNING"
    if gap_count >= 40:
        return "GAPPY_SOURCE_WARNING"
    return "M15_AVAILABLE"


def classify_family_status(
    *,
    source_rows: list[Mapping[str, Any]],
    matched_cohorts: Mapping[str, list[str]],
) -> str:
    if not source_rows:
        return "CONVERSION_STATUS_MISSING"
    if any(matched_cohorts.values()):
        return "REPLAY_READY_HAS_REGISTERED_COHORT"
    evidence_classes = {str(row.get("evidence_class") or "") for row in source_rows}
    if evidence_classes == {"CROSS_INSTRUMENT_TRANSFER"}:
        return "LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT"
    return "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT"


def reason_for_status(status: str, family: Mapping[str, Any]) -> str:
    if status == "CONVERSION_STATUS_MISSING":
        return "No converted M15 source rows were found for this family in the bounded first-wave conversion status."
    if status == "REPLAY_READY_HAS_REGISTERED_COHORT":
        return "At least one converted file symbol has a matching raw-OHLC replay cohort; deterministic replay can be registered separately before outcomes."
    if status == "LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT":
        return (
            "This family is registered as cross-instrument/control evidence. The current frozen "
            "raw-OHLC strategy cohort spec has no direct trade-label cohort for it, so this audit "
            "records source/label status without opening outcomes."
        )
    return (
        "Converted source rows exist, but the current frozen raw-OHLC replay cohort spec has no "
        "matching cohort for this family. Creating a new strategy cohort would be a separate "
        f"pre-registered research step, not part of this label-status audit for {family.get('family')}."
    )


def build_family_status_rows(
    *,
    matrix: Mapping[str, Any],
    conversion_status: Mapping[str, Any],
    replay_spec: Mapping[str, Any],
) -> list[dict[str, Any]]:
    cohorts_by_symbol = replay_spec_cohorts(replay_spec)
    by_source = conversion_rows_by_source(conversion_status)
    rows: list[dict[str, Any]] = []
    for family in target_families(matrix):
        source_rows = rows_for_family(family, by_source)
        matched: dict[str, list[str]] = {}
        source_summaries = []
        for source in source_rows:
            file_symbol = str(source.get("file_symbol") or "")
            source_summaries.append(
                {
                    "file_symbol": file_symbol,
                    "source_symbol": source.get("source_symbol"),
                    "evidence_class": source.get("evidence_class"),
                    "price_transform": source.get("price_transform"),
                    "m15_rows": int(source.get("rows") or 0),
                    "first": source.get("first"),
                    "last": source.get("last"),
                    "gap_count": int(source.get("gap_count") or 0),
                    "invalid_records_skipped": int(source.get("invalid_records_skipped") or 0),
                    "source_row_status": source_row_status(source),
                }
            )
            matched[file_symbol] = cohorts_by_symbol.get(file_symbol, [])
        status = classify_family_status(source_rows=source_rows, matched_cohorts=matched)
        rows.append(
            {
                "family": family.get("family"),
                "evidence_class": family.get("evidence_class"),
                "prior_replay_or_label_status": family.get("replay_or_label_status"),
                "label_status": status,
                "label_status_reason": reason_for_status(status, family),
                "converted_sources": family.get("converted_sources") or [],
                "source_rows": source_summaries,
                "matched_raw_replay_cohorts_by_file_symbol": matched,
                "outcome_slice_status": "NOT_OPENED_BY_LABEL_STATUS_AUDIT",
                "opened_outcome_rows": 0,
                "ai_api_calls": 0,
                "databento_spend_usd": 0.0,
                "next_action": family.get("next_action"),
            }
        )
    return rows


def build_payload(
    *,
    matrix: Mapping[str, Any],
    conversion_status: Mapping[str, Any],
    replay_spec: Mapping[str, Any],
    matrix_path: Path = DEFAULT_MATRIX_JSON,
    conversion_status_path: Path = DEFAULT_CONVERSION_STATUS_JSON,
    replay_spec_path: Path = DEFAULT_REPLAY_SPEC_JSON,
) -> dict[str, Any]:
    rows = build_family_status_rows(
        matrix=matrix,
        conversion_status=conversion_status,
        replay_spec=replay_spec,
    )
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("label_status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "schema_version": "expanded_oos_first_wave_label_status_audit_v1",
        "created_at_utc": utc_now(),
        "program": "expanded_oos_full_unblocking",
        "scope": "research/tooling only",
        "status": "FIRST_WAVE_LABEL_STATUS_AUDIT_CURRENT_NOT_TERMINAL",
        "promotion_verdict": NO_PROMOTION,
        "live_trading_logic_changed": False,
        "prompts_changed": False,
        "risk_or_execution_changed": False,
        "ai_api_calls": 0,
        "databento_spend_usd": 0.0,
        "inputs": {
            "family_status_matrix": rel(matrix_path),
            "bounded_conversion_status": rel(conversion_status_path),
            "raw_ohlc_replay_spec": rel(replay_spec_path),
        },
        "summary": {
            "target_families_from_matrix": len(rows),
            "families_with_label_status_artifact": len(rows),
            "families_replay_ready_under_current_spec": status_counts.get(
                "REPLAY_READY_HAS_REGISTERED_COHORT", 0
            ),
            "families_label_status_only_no_registered_cohort": status_counts.get(
                "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT", 0
            ),
            "families_control_status_only": status_counts.get(
                "LABEL_STATUS_ONLY_CONTROL_NO_DIRECT_TRADE_COHORT", 0
            ),
            "families_missing_conversion_status": status_counts.get("CONVERSION_STATUS_MISSING", 0),
            "opened_outcome_slices": 0,
            "opened_outcome_rows": 0,
            "status_counts": dict(sorted(status_counts.items())),
        },
        "families": rows,
        "completion_impact": [
            "This audit creates replay/label-status artifacts for the five first-wave families that were converted but not opened.",
            "It does not create replay results, strategy labels, p-values, DSR/PBO/effective-N, or promotion evidence.",
            "Families without current raw-OHLC cohorts require a separate pre-registered cohort/question before deterministic replay outcomes can be opened.",
            "Cross-instrument controls remain context/control evidence only and cannot validate the original trading edge.",
        ],
        "remaining_goal_gaps": [
            "Candidate survival table by evidence class is still incomplete.",
            "Instrument/source expansion scorecard needs to absorb this audit plus replay/depth statuses.",
            "Opened/burned/reserved ledger is still partial at goal level.",
            "No final synthesis exists after the first-wave label-status and depth/sampling audits.",
        ],
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    out.extend("| " + " | ".join(fmt(item) for item in row) + " |" for row in rows)
    return "\n".join(out)


def compact_source_summary(row: Mapping[str, Any]) -> str:
    sources = []
    for source in row.get("source_rows") or []:
        sources.append(
            f"{source.get('file_symbol')}:{source.get('m15_rows')}r/"
            f"g{source.get('gap_count')}/{source.get('source_row_status')}"
        )
    return "; ".join(sources) or "none"


def write_markdown(path: Path, payload: Mapping[str, Any]) -> None:
    summary = payload.get("summary") or {}
    lines = [
        "# Expanded OOS First-Wave Label-Status Audit - 2026-05-04",
        "",
        f"**Status:** `{payload.get('status')}`",
        f"**Promotion verdict:** `{payload.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only.",
        "- No live trading logic, prompts, risk, execution, or safety settings changed.",
        "- No AI/API calls, no new Databento pulls, and no outcome slices opened.",
        "",
        "## Summary",
        "",
        table(
            ["Metric", "Value"],
            [[key, value] for key, value in summary.items() if key != "status_counts"]
            + [["status_counts", summary.get("status_counts")]],
        ),
        "",
        "## Family Status",
        "",
        table(
            ["Family", "Label status", "Sources", "Matched replay cohorts", "Next action"],
            [
                [
                    row.get("family"),
                    row.get("label_status"),
                    compact_source_summary(row),
                    row.get("matched_raw_replay_cohorts_by_file_symbol"),
                    row.get("next_action"),
                ]
                for row in payload.get("families") or []
            ],
        ),
        "",
        "## Status Reasons",
        "",
    ]
    for row in payload.get("families") or []:
        lines.extend(
            [
                f"### {row.get('family')}",
                "",
                f"- `{row.get('label_status')}`: {row.get('label_status_reason')}",
                f"- Outcome slice status: `{row.get('outcome_slice_status')}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Completion Impact",
            "",
            *[f"- {item}" for item in payload.get("completion_impact") or []],
            "",
            "## Remaining Goal Gaps",
            "",
            *[f"- {item}" for item in payload.get("remaining_goal_gaps") or []],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-json", type=Path, default=DEFAULT_MATRIX_JSON)
    parser.add_argument("--conversion-status-json", type=Path, default=DEFAULT_CONVERSION_STATUS_JSON)
    parser.add_argument("--replay-spec-json", type=Path, default=DEFAULT_REPLAY_SPEC_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        matrix=load_json(args.matrix_json),
        conversion_status=load_json(args.conversion_status_json),
        replay_spec=load_json(args.replay_spec_json),
        matrix_path=args.matrix_json,
        conversion_status_path=args.conversion_status_json,
        replay_spec_path=args.replay_spec_json,
    )
    write_json(args.output_json, payload)
    write_markdown(args.output_md, payload)
    summary = payload["summary"]
    print(
        "wrote "
        f"{rel(args.output_json)} and {rel(args.output_md)} "
        f"families={summary['target_families_from_matrix']} "
        f"opened_outcomes={summary['opened_outcome_slices']} "
        f"promotion={payload['promotion_verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
