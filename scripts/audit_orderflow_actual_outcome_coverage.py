#!/usr/bin/env python3
"""Audit actual realized-R coverage for orderflow candidate diagnostics.

Research/tooling only. This script explains why the orderflow outcome join is
mostly synthetic-label based and identifies which rows can be reconciled to
broker-realized outcomes from existing trade records.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_features import generated_at_utc  # noqa: E402


DEFAULT_OUTCOME_JOIN = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_CANDIDATE_OUTCOME_JOIN_OF_DATA_4_2026-05-02.json"
)
DEFAULT_CANDIDATE_JOIN = (
    "data/external/validation/calendar_macro_bundle_v1/candidate_join/"
    "phase3_candidate_calendar_macro_join_2022_2026_plus_gap_m5_sim_v2_20260501T015608Z.jsonl"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_ACTUAL_OUTCOME_COVERAGE_AUDIT_OF_DATA_6_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_ACTUAL_OUTCOME_COVERAGE_AUDIT_OF_DATA_6_2026-05-02.md"
)

NON_EXECUTION_OUTCOMES = {
    "REJECTED_L2",
    "REJECTED_GATE1_SAFETY",
    "REJECTED_GATE3_SAFETY",
    "REJECTED_PRE_AI",
    "NO_TRADE",
}


def normalize_symbol(symbol: str | None) -> str | None:
    if symbol == "US30_cash":
        return "US30"
    return symbol


def candidate_key(symbol: str | None, candle_close_utc: str | None) -> tuple[str | None, str | None]:
    return (normalize_symbol(symbol), candle_close_utc)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def index_candidate_rows(rows: list[dict[str, Any]]) -> dict[tuple[str | None, str | None], dict[str, Any]]:
    indexed: dict[tuple[str | None, str | None], dict[str, Any]] = {}
    for row in rows:
        key = candidate_key(row.get("candidate__symbol"), row.get("candidate__candle_close_utc"))
        indexed[key] = row
    return indexed


def resolve_repo_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _find_first_numeric_by_key(obj: Any, wanted: set[str]) -> float | None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in wanted and isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        for value in obj.values():
            found = _find_first_numeric_by_key(value, wanted)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _find_first_numeric_by_key(value, wanted)
            if found is not None:
                return found
    return None


def inspect_trade_record(path_value: str | None) -> dict[str, Any]:
    path = resolve_repo_path(path_value)
    if path is None:
        return {"path_status": "no_path"}
    if not path.exists():
        return {"path_status": "missing", "path": str(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"path_status": "invalid_json", "path": str(path), "error": str(exc)}

    pipeline = payload.get("decision_pipeline") if isinstance(payload, dict) else {}
    exit_payload = payload.get("exit") if isinstance(payload, dict) else None
    actual_r = None
    if isinstance(exit_payload, dict):
        actual_r = _find_first_numeric_by_key(exit_payload, {"actual_r", "realized_R", "realized_r"})
    if actual_r is None:
        actual_r = _find_first_numeric_by_key(payload, {"actual_r", "realized_R", "realized_r"})

    return {
        "path_status": "exists",
        "path": str(path.relative_to(PROJECT_ROOT)),
        "record_final_outcome": pipeline.get("final_outcome") if isinstance(pipeline, dict) else None,
        "has_execution_payload": bool(payload.get("execution")) if isinstance(payload, dict) else False,
        "has_limit_intent": bool(payload.get("limit_intent")) if isinstance(payload, dict) else False,
        "has_exit_payload": isinstance(exit_payload, dict),
        "trade_record_actual_r": actual_r,
    }


def classify_coverage(candidate: dict[str, Any] | None, record: dict[str, Any]) -> str:
    if candidate is None:
        return "candidate_join_missing"
    if candidate.get("candidate__realized_r_available") and candidate.get("candidate__realized_r") is not None:
        return "actual_realized_r_available"
    if record.get("trade_record_actual_r") is not None:
        return "trade_record_actual_r_available_not_in_candidate_join"
    path_status = record.get("path_status")
    if path_status in {"no_path", "missing", "invalid_json"}:
        return f"trade_record_{path_status}"
    final_outcome = candidate.get("candidate__final_outcome") or record.get("record_final_outcome")
    if final_outcome in NON_EXECUTION_OUTCOMES:
        return "no_actual_by_design_pre_execution_reject"
    if final_outcome == "LIMIT_PLACED":
        return "limit_placed_no_broker_close_in_join"
    return "unknown_no_actual_realized_r"


def build_audit_rows(
    outcome_rows: list[dict[str, Any]],
    candidate_index: dict[tuple[str | None, str | None], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in outcome_rows:
        key = candidate_key(row.get("symbol"), row.get("canonical_m15_close_utc"))
        candidate = candidate_index.get(key)
        record = inspect_trade_record(candidate.get("candidate__trade_record_path") if candidate else None)
        coverage_class = classify_coverage(candidate, record)
        rows.append(
            {
                "symbol": normalize_symbol(row.get("symbol")),
                "candle_close_utc": row.get("canonical_m15_close_utc"),
                "candidate_join_matched": candidate is not None,
                "synthetic_realized_r_available": row.get("candidate__synthetic_realized_r") is not None,
                "synthetic_realized_r": row.get("candidate__synthetic_realized_r"),
                "synthetic_outcome": row.get("candidate__synthetic_outcome"),
                "actual_realized_r_available": bool(candidate and candidate.get("candidate__realized_r_available")),
                "actual_realized_r": candidate.get("candidate__realized_r") if candidate else None,
                "actual_missing_reason": candidate.get("candidate__realized_r_missing_reason") if candidate else None,
                "final_outcome": candidate.get("candidate__final_outcome") if candidate else None,
                "trade_record_matched": candidate.get("candidate__trade_record_matched") if candidate else None,
                "trade_record_path": candidate.get("candidate__trade_record_path") if candidate else None,
                "coverage_class": coverage_class,
                **{f"record__{key}": value for key, value in record.items()},
            }
        )
    return rows


def summarize_audit(
    *,
    candidate_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    all_actual = [row for row in candidate_rows if row.get("candidate__realized_r_available")]
    orderflow_actual = [row for row in audit_rows if row.get("actual_realized_r_available")]
    orderflow_synthetic = [row for row in audit_rows if row.get("synthetic_realized_r_available")]

    by_symbol: dict[str, dict[str, Any]] = {}
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audit_rows:
        buckets[str(row.get("symbol"))].append(row)
    for symbol, rows in sorted(buckets.items()):
        by_symbol[symbol] = {
            "n": len(rows),
            "synthetic_target_available": sum(bool(row.get("synthetic_realized_r_available")) for row in rows),
            "actual_realized_available": sum(bool(row.get("actual_realized_r_available")) for row in rows),
            "coverage_class_counts": dict(sorted(Counter(row.get("coverage_class") for row in rows).items())),
            "final_outcome_counts": dict(
                sorted(Counter(row.get("final_outcome") or "none" for row in rows).items())
            ),
        }

    actual_vs_synthetic = []
    for row in orderflow_actual:
        synthetic = row.get("synthetic_realized_r")
        actual = row.get("actual_realized_r")
        actual_vs_synthetic.append(
            {
                "symbol": row.get("symbol"),
                "candle_close_utc": row.get("candle_close_utc"),
                "synthetic_realized_r": synthetic,
                "actual_realized_r": actual,
                "actual_minus_synthetic": (
                    None if synthetic is None or actual is None else float(actual) - float(synthetic)
                ),
            }
        )

    return {
        "candidate_join_rows_total": len(candidate_rows),
        "candidate_join_actual_realized_available_total": len(all_actual),
        "orderflow_feature_candidate_rows": len(audit_rows),
        "orderflow_synthetic_target_available": len(orderflow_synthetic),
        "orderflow_actual_realized_available": len(orderflow_actual),
        "coverage_class_counts": dict(sorted(Counter(row.get("coverage_class") for row in audit_rows).items())),
        "actual_missing_reason_counts": dict(
            sorted(Counter(row.get("actual_missing_reason") or "none" for row in audit_rows).items())
        ),
        "final_outcome_counts": dict(sorted(Counter(row.get("final_outcome") or "none" for row in audit_rows).items())),
        "record_path_status_counts": dict(
            sorted(Counter(row.get("record__path_status") or "none" for row in audit_rows).items())
        ),
        "by_symbol": by_symbol,
        "actual_vs_synthetic": actual_vs_synthetic,
    }


def build_readout(summary: dict[str, Any]) -> list[str]:
    actual = summary["orderflow_actual_realized_available"]
    total = summary["orderflow_feature_candidate_rows"]
    synthetic = summary["orderflow_synthetic_target_available"]
    classes = summary["coverage_class_counts"]
    bullets = [
        f"Orderflow feature candidate rows have actual realized-R coverage {actual}/{total}; synthetic target coverage is {synthetic}/{total}.",
        "The actual-R blocker is mostly structural, not a parser miss: rejected candidates do not create broker exits.",
    ]
    limit_missing = classes.get("limit_placed_no_broker_close_in_join", 0)
    if limit_missing:
        bullets.append(
            f"{limit_missing} orderflow rows were LIMIT_PLACED without actual R in the join; those are the only near-term broker-history enrichment targets."
        )
    pre_reject = classes.get("no_actual_by_design_pre_execution_reject", 0)
    if pre_reject:
        bullets.append(
            f"{pre_reject} orderflow rows were rejected before execution, so they can only be evaluated with synthetic/path labels."
        )
    bullets.append("Depth/orderflow hypotheses should not be scored on actual realized R until forward collection or broker-history reconciliation expands coverage.")
    return bullets


def build_payload(outcome_payload: dict[str, Any], candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_index = index_candidate_rows(candidate_rows)
    audit_rows = build_audit_rows(outcome_payload["joined_rows"], candidate_index)
    summary = summarize_audit(candidate_rows=candidate_rows, audit_rows=audit_rows)
    return {
        "schema_version": "orderflow_actual_outcome_coverage_audit_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "outcome_join_schema_version": outcome_payload.get("schema_version"),
            "candidate_join_rows_loaded": len(candidate_rows),
            "candidate_outcome_rows_loaded": len(outcome_payload["joined_rows"]),
        },
        "audit_rows": audit_rows,
        "synthesis": {
            "summary": (
                "This audit separates actual realized-R availability from synthetic/path outcome availability "
                "for the current orderflow candidate diagnostic sample."
            ),
            **summary,
            "readout": build_readout(summary),
            "ambiguities": [
                "Synthetic/path R remains the only label for pre-execution rejects; this is not equivalent to broker realized R.",
                "Existing trade records prove actual-R extraction works when broker exits are reconciled, but coverage is sparse.",
                "LIMIT_PLACED rows without actual R may represent unfilled limits, still-open/missing close records, or absent broker-history backfill.",
                "Rejected CANDIDATE rows can still be useful for market-state diagnostics but cannot answer execution-quality questions.",
            ],
            "open_questions": [
                "Can broker-history reconciliation recover additional LIMIT_PLACED rows in this orderflow subset?",
                "How often do synthetic labels disagree with actual broker R once more actual rows are available?",
                "Should forward orderflow research separate pre-execution filter diagnostics from executed-trade diagnostics?",
                "Which depth/orderflow features explain rejected loser-like synthetic paths without overfitting to post-event data?",
            ],
            "next_steps": [
                "Backfill broker-history actual R only for LIMIT_PLACED rows that lack actual R.",
                "Keep rejected rows in a separate synthetic/path-outcome diagnostic bucket.",
                "Do not promote any orderflow filter until actual-R coverage or pre-registered synthetic-label methodology is sufficient.",
                "Use this audit to scope the first depth pilot to rows where outcome interpretation is least ambiguous.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    lines = [
        "# Orderflow Actual Outcome Coverage Audit",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Coverage",
        "",
        f"- Candidate join rows loaded: {synth['candidate_join_rows_total']}",
        f"- Candidate join actual-R available total: {synth['candidate_join_actual_realized_available_total']}",
        f"- Orderflow feature candidate rows: {synth['orderflow_feature_candidate_rows']}",
        f"- Orderflow synthetic target available: {synth['orderflow_synthetic_target_available']}",
        f"- Orderflow actual realized-R available: {synth['orderflow_actual_realized_available']}",
        f"- Coverage class counts: {synth['coverage_class_counts']}",
        f"- Final outcome counts: {synth['final_outcome_counts']}",
        f"- Record path status counts: {synth['record_path_status_counts']}",
        "",
        "## Readout",
        "",
        *[f"- {item}" for item in synth["readout"]],
        "",
        "## By Symbol",
        "",
        "| Symbol | n | synthetic target | actual R | coverage classes | final outcomes |",
        "|---|---:|---:|---:|---|---|",
    ]
    for symbol, row in synth["by_symbol"].items():
        lines.append(
            "| "
            f"{symbol} | {row['n']} | {row['synthetic_target_available']} | "
            f"{row['actual_realized_available']} | {row['coverage_class_counts']} | "
            f"{row['final_outcome_counts']} |"
        )
    lines.extend(
        [
            "",
            "## Actual vs Synthetic Rows",
            "",
            "| Symbol | Candle close UTC | synthetic R | actual R | actual - synthetic |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in synth["actual_vs_synthetic"]:
        lines.append(
            "| "
            f"{row['symbol']} | {row['candle_close_utc']} | "
            f"{_fmt(row['synthetic_realized_r'])} | {_fmt(row['actual_realized_r'])} | "
            f"{_fmt(row['actual_minus_synthetic'])} |"
        )
    if not synth["actual_vs_synthetic"]:
        lines.append("| n/a | n/a |  |  |  |")
    lines.extend(
        [
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguities"]],
            "",
            "## Open Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["open_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outcome-join", default=DEFAULT_OUTCOME_JOIN)
    parser.add_argument("--candidate-join", default=DEFAULT_CANDIDATE_JOIN)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    outcome_path = Path(args.outcome_join)
    candidate_path = Path(args.candidate_join)
    if not outcome_path.exists():
        parser.exit(2, f"outcome join not found: {outcome_path}\n")
    if not candidate_path.exists():
        parser.exit(2, f"candidate join not found: {candidate_path}\n")
    payload = build_payload(load_json(outcome_path), read_jsonl(candidate_path))
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"orderflow_actual_r={payload['synthesis']['orderflow_actual_realized_available']}/"
        f"{payload['synthesis']['orderflow_feature_candidate_rows']} "
        f"synthetic={payload['synthesis']['orderflow_synthetic_target_available']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
