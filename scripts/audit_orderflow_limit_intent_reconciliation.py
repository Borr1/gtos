#!/usr/bin/env python3
"""Reconcile orderflow LIMIT_PLACED rows without realized broker R.

Research/tooling only. This script does not backfill or modify trade records.
It distinguishes an internal GTOS pending-limit intent from an executed broker
position, then compares local log evidence with counterfactual M1 path labels.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_features import generated_at_utc  # noqa: E402


DEFAULT_COVERAGE_AUDIT = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_ACTUAL_OUTCOME_COVERAGE_AUDIT_OF_DATA_6_2026-05-02.json"
)
DEFAULT_CANDIDATE_JOIN = (
    "data/external/validation/calendar_macro_bundle_v1/candidate_join/"
    "phase3_candidate_calendar_macro_join_2022_2026_plus_gap_m5_sim_v2_20260501T015608Z.jsonl"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_LIMIT_INTENT_RECONCILIATION_AUDIT_OF_DATA_11_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_LIMIT_INTENT_RECONCILIATION_AUDIT_OF_DATA_11_2026-05-02.md"
)
DEFAULT_M1_ROOTS = (
    "data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1",
    "data/mt5_research_exports/phase3_candidate_gap_20260501",
    "data/historical_2026",
)

NUMERIC_R_KEYS = {"actual_r", "realized_R", "realized_r", "realized_r_multiple"}


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def resolve_repo_path(path_value: str | None, *, project_root: Path = PROJECT_ROOT) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if path.is_absolute():
        return path
    return project_root / path


def candidate_key(symbol: str | None, candle_close_utc: str | None) -> tuple[str | None, str | None]:
    return (symbol, candle_close_utc)


def index_candidate_rows(rows: list[dict[str, Any]]) -> dict[tuple[str | None, str | None], dict[str, Any]]:
    return {
        candidate_key(row.get("candidate__symbol"), row.get("candidate__candle_close_utc")): row
        for row in rows
    }


def find_numeric_key(obj: Any, keys: set[str] = NUMERIC_R_KEYS) -> float | None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in keys and isinstance(value, (int, float)) and not isinstance(value, bool):
                value_f = float(value)
                if not math.isnan(value_f) and not math.isinf(value_f):
                    return value_f
        for value in obj.values():
            found = find_numeric_key(value, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_numeric_key(value, keys)
            if found is not None:
                return found
    return None


def inspect_trade_record(path_value: str | None, *, project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    path = resolve_repo_path(path_value, project_root=project_root)
    if path is None:
        return {"path_status": "no_path"}
    if not path.exists():
        return {"path_status": "missing", "path": str(path)}
    payload = load_json(path)
    pipeline = payload.get("decision_pipeline") or {}
    execution = payload.get("execution")
    exit_payload = payload.get("exit")
    limit_intent = payload.get("limit_intent") or {}
    actual_r = None
    if isinstance(exit_payload, dict):
        actual_r = find_numeric_key(exit_payload)
    if actual_r is None:
        actual_r = find_numeric_key(payload)
    return {
        "path_status": "exists",
        "path": str(path.relative_to(project_root)),
        "metadata_trade_id": (payload.get("metadata") or {}).get("trade_id"),
        "metadata_candle_time": (payload.get("metadata") or {}).get("candle_time"),
        "final_outcome": pipeline.get("final_outcome"),
        "has_execution_payload": isinstance(execution, dict),
        "has_exit_payload": isinstance(exit_payload, dict),
        "actual_r": actual_r,
        "limit_intent": {
            "trade_id": limit_intent.get("trade_id"),
            "limit_price": limit_intent.get("limit_price"),
            "stop_loss": limit_intent.get("stop_loss"),
            "take_profit_1": limit_intent.get("take_profit_1"),
            "expiry_candles": limit_intent.get("expiry_candles"),
        },
    }


def log_file_for_symbol(symbol: str, *, project_root: Path = PROJECT_ROOT) -> Path:
    return project_root / "knowledge_base" / "logs" / f"agent_{symbol}_demo.log"


def _line_no(idx: int) -> int:
    return idx + 1


def _trade_id_variants(trade_id: str | None) -> set[str]:
    if not trade_id:
        return set()
    variants = {trade_id}
    if trade_id.startswith("lim_"):
        variants.add(trade_id.replace("lim_", "lim_filled_", 1))
    return variants


def inspect_log_evidence(
    *,
    symbol: str,
    trade_id: str | None,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    log_path = log_file_for_symbol(symbol, project_root=project_root)
    if not trade_id:
        return {"log_status": "no_trade_id", "log_path": str(log_path)}
    if not log_path.exists():
        return {"log_status": "missing", "log_path": str(log_path)}

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    variants = _trade_id_variants(trade_id)
    matching = [
        {"line": _line_no(idx), "text": line}
        for idx, line in enumerate(lines)
        if any(variant in line for variant in variants)
    ]

    placed_indexes = [
        idx for idx, line in enumerate(lines)
        if f"LIMIT PLACED: {trade_id}" in line
    ]
    discard_indexes = [
        idx for idx, line in enumerate(lines)
        if "Discarding pending_intent" in line and trade_id in line
    ]
    trigger_indexes = [
        idx for idx, line in enumerate(lines)
        if f"Limit triggered: {trade_id}" in line
    ]
    fill_indexes = [
        idx for idx, line in enumerate(lines)
        if any(f"LIMIT FILLED: {variant}" in line for variant in variants)
    ]
    cancel_indexes = [
        idx for idx, line in enumerate(lines)
        if "Limit intent cancelled" in line and trade_id in line
    ]
    expire_indexes = [
        idx for idx, line in enumerate(lines)
        if "Limit intent expired" in line and trade_id in line
    ]
    failed_order_indexes = [
        idx for idx, line in enumerate(lines)
        if "Limit fill order failed" in line and trade_id in line
    ]

    placed_idx = placed_indexes[0] if placed_indexes else None
    end_idx = discard_indexes[0] if discard_indexes else len(lines) - 1
    processing_count = None
    if placed_idx is not None and end_idx is not None and end_idx > placed_idx:
        processing_count = sum(
            1
            for line in lines[placed_idx + 1 : end_idx + 1]
            if "Processing candle" in line
        )

    placed_time_utc = None
    if discard_indexes:
        match = re.search(r"placed=([^,\)]+)", lines[discard_indexes[0]])
        if match:
            placed_time_utc = match.group(1)

    return {
        "log_status": "exists",
        "log_path": str(log_path.relative_to(project_root)),
        "has_limit_placed_log": bool(placed_indexes),
        "has_limit_triggered_log": bool(trigger_indexes),
        "has_limit_filled_log": bool(fill_indexes),
        "has_limit_cancelled_log": bool(cancel_indexes),
        "has_limit_expired_log": bool(expire_indexes),
        "has_limit_fill_order_failed_log": bool(failed_order_indexes),
        "has_pending_discard_log": bool(discard_indexes),
        "processing_candles_after_placement_before_discard": processing_count,
        "placed_time_utc_from_discard": placed_time_utc,
        "evidence_lines": matching[:20],
    }


def _csv_time(value: str) -> datetime | None:
    parsed = parse_utc(value)
    if parsed is not None:
        return parsed
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _float_or_none(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def find_m1_csv(
    *,
    symbol: str,
    candidate: dict[str, Any] | None,
    roots: list[Path],
    project_root: Path = PROJECT_ROOT,
) -> Path | None:
    candidates: list[Path] = []
    source_dir = candidate.get("candidate__synthetic_ohlcv_dir") if candidate else None
    if source_dir:
        candidates.append(resolve_repo_path(source_dir, project_root=project_root) / f"{symbol}_M1.csv")
    for root in roots:
        candidates.append((root if root.is_absolute() else project_root / root) / f"{symbol}_M1.csv")
    for path in candidates:
        if path and path.exists():
            return path
    return None


def simulate_limit_path_from_m1(
    *,
    symbol: str,
    direction: str,
    limit_price: float,
    stop_loss: float,
    take_profit_1: float,
    start_utc: datetime,
    candidate: dict[str, Any] | None,
    roots: list[Path],
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    path = find_m1_csv(symbol=symbol, candidate=candidate, roots=roots, project_root=project_root)
    if path is None:
        return {"status": "m1_csv_missing"}

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            ts = _csv_time(str(raw.get("time") or ""))
            if ts is None or ts < start_utc.replace(second=0, microsecond=0):
                continue
            high = _float_or_none(raw.get("high"))
            low = _float_or_none(raw.get("low"))
            close = _float_or_none(raw.get("close"))
            if high is None or low is None:
                continue
            rows.append({"time": ts, "high": high, "low": low, "close": close})
            if ts > start_utc and ts > start_utc.replace(hour=23, minute=59, second=0, microsecond=0):
                break

    if not rows:
        return {"status": "no_m1_rows_after_start", "m1_csv": str(path.relative_to(project_root))}

    start_floor = start_utc.replace(second=0, microsecond=0)
    entry: dict[str, Any] | None = None
    for idx, row in enumerate(rows):
        touched = row["low"] <= limit_price if direction == "LONG" else row["high"] >= limit_price
        if touched:
            entry = {
                "idx": idx,
                "time_utc": iso_utc(row["time"]),
                "same_minute_as_start": row["time"] == start_floor,
                "bar_low": row["low"],
                "bar_high": row["high"],
            }
            break

    if entry is None:
        return {
            "status": "no_entry_touch",
            "m1_csv": str(path.relative_to(project_root)),
            "rows_scanned": len(rows),
        }

    outcome = "OPEN"
    outcome_time = None
    same_bar_ambiguous = False
    for row in rows[int(entry["idx"]) :]:
        if direction == "LONG":
            hit_sl = row["low"] <= stop_loss
            hit_tp = row["high"] >= take_profit_1
        else:
            hit_sl = row["high"] >= stop_loss
            hit_tp = row["low"] <= take_profit_1
        if hit_sl and hit_tp:
            outcome = "SAME_M1_BAR_SL_TP_AMBIGUOUS"
            outcome_time = row["time"]
            same_bar_ambiguous = True
            break
        if hit_sl:
            outcome = "SL"
            outcome_time = row["time"]
            break
        if hit_tp:
            outcome = "TP"
            outcome_time = row["time"]
            break

    return {
        "status": "ok",
        "m1_csv": str(path.relative_to(project_root)),
        "rows_scanned": len(rows),
        "entry_touch": {key: value for key, value in entry.items() if key != "idx"},
        "outcome": outcome,
        "outcome_time_utc": iso_utc(outcome_time),
        "same_m1_bar_sl_tp_ambiguous": same_bar_ambiguous,
        "counterfactual_realized_r": 1.5 if outcome == "TP" else (-1.0 if outcome == "SL" else None),
    }


def classify_reconciliation(
    record: dict[str, Any],
    log: dict[str, Any],
    path: dict[str, Any],
) -> str:
    if record.get("actual_r") is not None:
        return "actual_broker_r_present"
    if record.get("has_execution_payload") and not record.get("has_exit_payload"):
        return "execution_payload_present_exit_missing"
    if log.get("has_limit_filled_log"):
        return "limit_fill_log_present_exit_missing"
    if log.get("has_limit_triggered_log") and not log.get("has_limit_filled_log"):
        return "triggered_without_fill_log"
    if log.get("has_pending_discard_log"):
        if path.get("counterfactual_realized_r") is not None:
            return "discarded_internal_intent_but_research_path_would_have_filled"
        return "discarded_internal_intent_no_counterfactual_fill"
    if path.get("counterfactual_realized_r") is not None:
        return "no_live_fill_evidence_but_research_path_would_have_filled"
    return "unresolved_no_execution_evidence"


def build_reconciliation_rows(
    coverage_payload: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    *,
    project_root: Path = PROJECT_ROOT,
    m1_roots: list[Path] | None = None,
) -> list[dict[str, Any]]:
    m1_roots = m1_roots or [Path(root) for root in DEFAULT_M1_ROOTS]
    candidate_index = index_candidate_rows(candidate_rows)
    rows: list[dict[str, Any]] = []
    for audit_row in coverage_payload.get("audit_rows") or []:
        if audit_row.get("coverage_class") != "limit_placed_no_broker_close_in_join":
            continue
        symbol = str(audit_row.get("symbol"))
        candle_close = audit_row.get("candle_close_utc")
        candidate = candidate_index.get(candidate_key(symbol, candle_close))
        record = inspect_trade_record(audit_row.get("trade_record_path"), project_root=project_root)
        intent = record.get("limit_intent") or {}
        log = inspect_log_evidence(
            symbol=symbol,
            trade_id=intent.get("trade_id"),
            project_root=project_root,
        )
        placed_start = (
            parse_utc(log.get("placed_time_utc_from_discard"))
            or parse_utc(record.get("metadata_candle_time"))
            or parse_utc(candle_close)
        )
        path_payload: dict[str, Any]
        direction = candidate.get("candidate__direction") if candidate else None
        if (
            placed_start
            and direction
            and intent.get("limit_price") is not None
            and intent.get("stop_loss") is not None
            and intent.get("take_profit_1") is not None
        ):
            path_payload = simulate_limit_path_from_m1(
                symbol=symbol,
                direction=str(direction),
                limit_price=float(intent["limit_price"]),
                stop_loss=float(intent["stop_loss"]),
                take_profit_1=float(intent["take_profit_1"]),
                start_utc=placed_start,
                candidate=candidate,
                roots=m1_roots,
                project_root=project_root,
            )
        else:
            path_payload = {"status": "insufficient_inputs"}
        classification = classify_reconciliation(record, log, path_payload)
        rows.append(
            {
                "symbol": symbol,
                "candle_close_utc": candle_close,
                "candidate_final_outcome": audit_row.get("final_outcome"),
                "candidate_synthetic_outcome": audit_row.get("synthetic_outcome"),
                "candidate_synthetic_realized_r": audit_row.get("synthetic_realized_r"),
                "trade_record_path": audit_row.get("trade_record_path"),
                "record": record,
                "log": log,
                "counterfactual_m1_path": path_payload,
                "reconciliation_class": classification,
            }
        )
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classes = Counter(row.get("reconciliation_class") for row in rows)
    symbols = Counter(row.get("symbol") for row in rows)
    counterfactual_tp = sum(
        1 for row in rows if row.get("counterfactual_m1_path", {}).get("outcome") == "TP"
    )
    broker_actual = sum(1 for row in rows if row.get("record", {}).get("actual_r") is not None)
    filled_logs = sum(1 for row in rows if row.get("log", {}).get("has_limit_filled_log"))
    discarded_logs = sum(1 for row in rows if row.get("log", {}).get("has_pending_discard_log"))
    return {
        "limit_rows_audited": len(rows),
        "reconciliation_class_counts": dict(sorted(classes.items())),
        "symbol_counts": dict(sorted(symbols.items())),
        "broker_actual_r_rows": broker_actual,
        "limit_filled_log_rows": filled_logs,
        "pending_discard_log_rows": discarded_logs,
        "counterfactual_m1_tp_rows": counterfactual_tp,
    }


def build_readout(summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    bullets = [
        f"Audited {summary['limit_rows_audited']} LIMIT_PLACED orderflow rows with missing realized R.",
        f"Broker actual-R rows recovered from local records: {summary['broker_actual_r_rows']}.",
        f"Rows with LIMIT_FILLED log evidence: {summary['limit_filled_log_rows']}; rows with next-day pending-intent discard evidence: {summary['pending_discard_log_rows']}.",
    ]
    if summary["counterfactual_m1_tp_rows"]:
        bullets.append(
            f"{summary['counterfactual_m1_tp_rows']} row(s) had M1 path evidence that the internal limit would have reached TP if filled."
        )
    for row in rows:
        if row.get("symbol") == "XAUUSD" and row.get("candle_close_utc") == "2026-04-17T13:30:00+00:00":
            path = row.get("counterfactual_m1_path", {})
            log = row.get("log", {})
            bullets.append(
                "XAUUSD 2026-04-17 13:30 resolves as an internal intent lifecycle gap: "
                f"log has placed={log.get('has_limit_placed_log')}, trigger={log.get('has_limit_triggered_log')}, "
                f"fill={log.get('has_limit_filled_log')}, discard={log.get('has_pending_discard_log')}; "
                f"M1 counterfactual outcome={path.get('outcome')} at {path.get('outcome_time_utc')}."
            )
    bullets.append(
        "Conclusion: broker-history backfill is not enough for this row; the unresolved part is why the live pending-fill branch did not log a trigger despite counterfactual M1 touch evidence."
    )
    return bullets


def build_payload(
    coverage_payload: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    *,
    project_root: Path = PROJECT_ROOT,
    m1_roots: list[Path] | None = None,
) -> dict[str, Any]:
    rows = build_reconciliation_rows(
        coverage_payload,
        candidate_rows,
        project_root=project_root,
        m1_roots=m1_roots,
    )
    summary = summarize(rows)
    return {
        "schema_version": "orderflow_limit_intent_reconciliation_audit_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "coverage_schema_version": coverage_payload.get("schema_version"),
            "candidate_rows_loaded": len(candidate_rows),
            "m1_roots": [str(path) for path in (m1_roots or [Path(root) for root in DEFAULT_M1_ROOTS])],
        },
        "reconciliation_rows": rows,
        "synthesis": {
            "summary": (
                "This audit reconciles LIMIT_PLACED orderflow rows with missing actual R by separating "
                "internal GTOS limit intent, broker execution evidence, local logs, and M1 counterfactual path."
            ),
            **summary,
            "readout": build_readout(summary, rows),
            "ambiguities": [
                "LIMIT_PLACED is an internal pending intent, not proof of a broker-resting pending order.",
                "Local logs do not record the M15 candle low/high fed into each pending-fill check, so a no-trigger row cannot be fully replayed from logs alone.",
                "M1 OHLC path simulation is counterfactual when no broker fill occurred; it cannot be counted as realized R.",
                "The XAUUSD 2026-04-17 13:30 row remains an execution-telemetry anomaly, not an orderflow-alpha datapoint.",
            ],
            "open_questions": [
                "Why did the live pending-fill branch not log a trigger for XAUUSD 2026-04-17 13:30 when research M1 data later shows price traded through the internal limit?",
                "Were M15 candles empty/stale in the live raw_data object during the pending-intent window?",
                "Should pending-intent monitoring log the checked candle low/high on every active candle for future forensic closure?",
                "Should outcome joins classify internal-intent counterfactual TP separately from broker-realized TP by default?",
            ],
            "next_steps": [
                "Do not backfill XAUUSD 2026-04-17 13:30 as actual realized R unless broker deal evidence appears.",
                "Keep the row out of promotion-grade orderflow scoring; use it only for execution telemetry forensics.",
                "Add forward research telemetry for pending-intent checked candle high/low and trigger decision before relying on future limit-intent outcomes.",
                "Keep synthetic/path labels and actual broker-R labels as separate fields in every orderflow report.",
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
        "# Orderflow Limit Intent Reconciliation Audit",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        synth["summary"],
        "",
        "## Counts",
        "",
        f"- Limit rows audited: {synth['limit_rows_audited']}",
        f"- Reconciliation classes: {synth['reconciliation_class_counts']}",
        f"- Symbol counts: {synth['symbol_counts']}",
        f"- Broker actual-R rows: {synth['broker_actual_r_rows']}",
        f"- Limit-filled log rows: {synth['limit_filled_log_rows']}",
        f"- Pending-discard log rows: {synth['pending_discard_log_rows']}",
        f"- Counterfactual M1 TP rows: {synth['counterfactual_m1_tp_rows']}",
        "",
        "## Readout",
        "",
        *[f"- {item}" for item in synth["readout"]],
        "",
        "## Rows",
        "",
        "| Symbol | Candle close UTC | class | placed | triggered | filled | discarded | M1 outcome | M1 outcome time |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["reconciliation_rows"]:
        log = row.get("log", {})
        path_info = row.get("counterfactual_m1_path", {})
        lines.append(
            "| "
            f"{row.get('symbol')} | {row.get('candle_close_utc')} | "
            f"{row.get('reconciliation_class')} | "
            f"{log.get('has_limit_placed_log')} | "
            f"{log.get('has_limit_triggered_log')} | "
            f"{log.get('has_limit_filled_log')} | "
            f"{log.get('has_pending_discard_log')} | "
            f"{_fmt(path_info.get('outcome'))} | {_fmt(path_info.get('outcome_time_utc'))} |"
        )
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
    parser.add_argument("--coverage-audit", default=DEFAULT_COVERAGE_AUDIT)
    parser.add_argument("--candidate-join", default=DEFAULT_CANDIDATE_JOIN)
    parser.add_argument("--m1-root", action="append", default=None)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    coverage_path = Path(args.coverage_audit)
    candidate_path = Path(args.candidate_join)
    if not coverage_path.exists():
        parser.exit(2, f"coverage audit not found: {coverage_path}\n")
    if not candidate_path.exists():
        parser.exit(2, f"candidate join not found: {candidate_path}\n")
    roots = [Path(root) for root in (args.m1_root or DEFAULT_M1_ROOTS)]
    payload = build_payload(load_json(coverage_path), read_jsonl(candidate_path), m1_roots=roots)
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"limit_rows={payload['synthesis']['limit_rows_audited']} "
        f"classes={payload['synthesis']['reconciliation_class_counts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
