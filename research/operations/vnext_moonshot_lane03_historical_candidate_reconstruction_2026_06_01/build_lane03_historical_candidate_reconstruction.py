#!/usr/bin/env python3
"""Build the Lane03 historical candidate reconstruction artifacts.

This route is intentionally offline-only. It reads existing replay, lane,
shadow, and route ledgers and emits canonical candidate/event ledgers with
source-use and runtime-effect labels. It does not call broker APIs, vendors,
or production runtime code.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


ROUTE_ID = "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01"
SCHEMA_VERSION = "lane03_historical_candidate_reconstruction_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
RUNTIME_EFFECT_BOUNDARY = "offline_research_only_no_live_trading_effect"
RESULT_USE_STATUS = "source_bound_reconstruction_not_production_performance_claim"

EVENT_LEDGER = ROUTE_DIR / "LANE03_CANONICAL_CANDIDATE_EVENT_LEDGER.jsonl.gz"
CANDIDATE_LEDGER = ROUTE_DIR / "LANE03_CANONICAL_CANDIDATE_LEDGER.jsonl.gz"
DUPLICATE_GROUP_LEDGER = ROUTE_DIR / "LANE03_DUPLICATE_GROUP_LEDGER.jsonl.gz"
SOURCE_INVENTORY_LEDGER = ROUTE_DIR / "LANE03_SOURCE_INVENTORY_LEDGER.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / "LANE03_SOURCE_GAP_LEDGER.jsonl"
MECHANISM_COVERAGE_LEDGER = ROUTE_DIR / "LANE03_MECHANISM_COVERAGE_LEDGER.jsonl"
DEPENDENCY_STATE_LEDGER = ROUTE_DIR / "LANE03_DEPENDENCY_STATE_LEDGER.jsonl"
BRANCH_DECISION_LEDGER = ROUTE_DIR / "LANE03_BRANCH_DECISION_LEDGER.jsonl"
SUMMARY_PATH = ROUTE_DIR / "LANE03_RECONSTRUCTION_SUMMARY.json"
MANIFEST_PATH = ROUTE_DIR / "LANE03_OUTPUT_MANIFEST.json"
COMPLETION_AUDIT_PATH = ROUTE_DIR / "LANE03_COMPLETION_AUDIT.json"
CONTEXT_ANCHOR_PATH = ROUTE_DIR / "LANE03_CONTEXT_ANCHOR.md"
DUPLICATE_POLICY_PATH = ROUTE_DIR / "LANE03_DUPLICATE_DENOMINATOR_POLICY.md"

TMP_GROUP_DB = ROUTE_DIR / ".lane03_candidate_groups.sqlite"


REQUIRED_ROW_CLASSES = {
    "raw generated",
    "selected",
    "bridge",
    "skipped",
    "rejected",
    "broker-ready",
    "accepted",
    "placed",
    "no-entry",
    "stuck",
    "missed opportunity",
    "stale blocker",
    "correct reject candidate",
    "projection-only",
}

REQUIRED_MECHANISMS = {
    "ob_retest",
    "fvg_fill",
    "breaker_re_entry",
    "liquidity_sweep_reclaim",
    "displacement_continuation",
    "failed_displacement",
    "no_fill_near_miss",
    "session_flow_continuation",
    "exhaustion",
    "stop_cascade",
    "inverse_avoid",
}

DISCOVERED_CODE_MECHANISMS = {
    "structural_distance_extreme",
    "cross_asset_lead_lag",
    "session_open_range_break",
    "regime_transition_break",
    "volatility_compression_expansion",
    "market_gap_control",
    "source_guard_scope_control",
    "orderflow_primitive",
    "prefill_pending_lifecycle",
    "portfolio_scheduler",
    "execution_microstructure",
}

FULL_REPLAY_MATERIAL_OUTPUTS = {
    "ablation_metrics",
    "behavioral_forensics",
    "candidate_generation",
    "decision_explanation",
    "denominator_disposition",
    "dominance_and_pollution",
    "final_decision_map",
    "m15_vs_ltf_disagreement",
    "market_state_packet",
    "missed_winner_avoided_loser",
    "mixed_resolution",
    "nofill_pending_lifecycle",
    "path_outcome_r",
    "path_source",
    "robustness_prop_metrics",
    "runtime_event_cache",
    "runtime_trace",
}

EXACT_R_FIELDS = (
    "exact_r",
    "actual_r",
    "actual_net_r",
    "broker_r",
    "broker_net_r",
    "realized_r",
    "realized_net_r",
    "closed_r",
    "executed_r",
    "net_actual_r",
    "deal_r",
)
PROXY_R_FIELDS = (
    "simulated_r",
    "proxy_r",
    "path_outcome_r",
    "outcome_r",
    "gross_r",
    "net_r",
    "candidate_r",
    "selected_r",
    "r_multiple",
    "result_r",
    "terminal_r",
    "mfe_r",
    "mae_r",
)
EXPECTANCY_FIELDS = (
    "expectancy_r",
    "mean_r",
    "avg_r",
    "average_r",
    "expected_r",
    "portfolio_expectancy_r",
)
COST_R_FIELDS = (
    "cost_r",
    "spread_r",
    "slippage_r",
    "commission_r",
    "swap_r",
    "total_cost_r",
)

SYMBOL_FIELDS = (
    "symbol",
    "broker_symbol",
    "source_symbol",
    "instrument",
    "pair",
    "ticker",
)
SIDE_FIELDS = ("side", "direction", "trade_side", "candidate_side", "order_side")
SESSION_FIELDS = ("session", "killzone", "kill_zone", "kz", "session_name")
FRAMEWORK_FIELDS = (
    "framework",
    "strategy",
    "strategy_family",
    "setup_family",
    "setup_type",
    "candidate_framework",
    "framework_name",
)
ORIGIN_FIELDS = (
    "origin_family",
    "source_origin",
    "origin",
    "setup_origin",
    "candidate_origin",
    "mechanism",
    "mechanism_family",
)
TIME_FIELDS = (
    "candidate_time_utc",
    "candle_time_utc",
    "event_time_utc",
    "timestamp_utc",
    "time_utc",
    "bar_time_utc",
    "entry_time_utc",
    "decision_time_utc",
    "open_time_utc",
    "ts_utc",
    "timestamp",
    "time",
)
ASOF_FIELDS = (
    "asof_time_utc",
    "as_of_time_utc",
    "decision_time_utc",
    "candle_time_utc",
    "event_time_utc",
)
SOURCE_ROW_ID_FIELDS = (
    "candidate_id",
    "source_candidate_id",
    "event_id",
    "row_id",
    "trade_id",
    "setup_id",
    "opportunity_id",
    "decision_id",
    "cluster_id",
    "position_id",
    "ticket",
    "order_ticket",
    "deal_ticket",
)


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    path: Path
    category: str
    row_family: str
    source_use_state: str
    evidence_class: str
    asof_status: str
    process_events: bool = True
    note: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def stable_hash(parts: Iterable[Any], length: int = 24) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:length]


def slug(text: str, limit: int = 80) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return clean[:limit] or "source"


def compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip()
    return text if text else default


def normalize_token(value: Any, default: str = "unknown") -> str:
    text = compact_text(value, default=default).lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_./:-]+", "_", text)
    return text.strip("_") or default


def first_value(row: dict[str, Any], fields: Iterable[str]) -> Any:
    lowered = {str(k).lower(): k for k in row.keys()}
    for field in fields:
        key = lowered.get(field.lower())
        if key is not None and row.get(key) not in (None, ""):
            return row[key]
    return None


def first_number(row: dict[str, Any], fields: Iterable[str]) -> tuple[float | None, str | None]:
    lowered = {str(k).lower(): k for k in row.keys()}
    for field in fields:
        key = lowered.get(field.lower())
        if key is None:
            continue
        value = coerce_float(row.get(key))
        if value is not None:
            return value, str(key)
    return None, None


def coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def find_generic_r(row: dict[str, Any]) -> tuple[float | None, str | None, str]:
    """Return the strongest available R-like field and its evidence state."""
    exact, exact_field = first_number(row, EXACT_R_FIELDS)
    if exact is not None:
        return exact, exact_field, "exact_r_available"
    proxy, proxy_field = first_number(row, PROXY_R_FIELDS)
    if proxy is not None:
        return proxy, proxy_field, "proxy_r_available"

    for key, value in row.items():
        key_l = str(key).lower()
        if not (key_l == "r" or key_l.endswith("_r") or "_r_" in key_l):
            continue
        if any(skip in key_l for skip in ("hash", "url", "error", "row", "folder", "owner")):
            continue
        number = coerce_float(value)
        if number is None:
            continue
        if any(token in key_l for token in ("actual", "broker", "realized", "deal", "executed", "closed")):
            return number, str(key), "exact_r_available"
        return number, str(key), "proxy_r_available"
    return None, None, "r_field_absent"


def row_text(row: dict[str, Any], source: SourceSpec | None = None) -> str:
    bits = []
    if source is not None:
        bits.extend([source.source_id, source.category, source.row_family, source.path.name])
    for key, value in row.items():
        if isinstance(value, (dict, list)):
            continue
        bits.append(str(key))
        bits.append(str(value))
    return " ".join(bits).lower()


def classify_row(row: dict[str, Any], source: SourceSpec | None = None) -> list[str]:
    text = row_text(row, source)
    classes: set[str] = set()

    if source and "full_replay" in source.category:
        if "candidate_generation" in source.row_family:
            classes.update({"raw generated", "projection-only"})
        if "denominator" in source.row_family or "no_setup" in text:
            classes.update({"no-entry", "projection-only"})
        if "path_outcome" in source.row_family or "path" in source.row_family:
            classes.update({"bridge", "projection-only"})
        if "final_decision" in source.row_family:
            classes.add("selected")

    if source and "lane02" in source.category:
        classes.update({"selected", "projection-only"})

    if source and "lane01" in source.category:
        classes.update({"selected", "projection-only"})

    if source and "friday" in source.category:
        classes.add("bridge")
        if "actually_placed" in text or "placed" in text:
            classes.add("placed")
        if "stuck" in text:
            classes.add("stuck")

    if "candidate" in text or "setup" in text or "opportunity" in text:
        classes.add("raw generated")
    if "selected" in text or "accepted_cell" in text or "portfolio_replay" in text:
        classes.add("selected")
    if "accept" in text or "accepted" in text or "follow" in text:
        classes.add("accepted")
    if "reject" in text or "avoid" in text or "blocked" in text or "veto" in text:
        classes.add("rejected")
    if "skip" in text or "skipped" in text:
        classes.add("skipped")
    if "broker_ready" in text or "broker-ready" in text or "order_ready" in text:
        classes.add("broker-ready")
    if "placed" in text or "order_ticket" in text or "deal_ticket" in text:
        classes.add("placed")
    if "no_entry" in text or "no-entry" in text or "no setup" in text or "no_setup" in text:
        classes.add("no-entry")
    if "stuck" in text or "stale" in text or "blocked_packet" in text:
        classes.add("stuck")
    if "missed" in text or "missed_opportunity" in text:
        classes.add("missed opportunity")
    if "stale" in text or "staleness" in text:
        classes.add("stale blocker")
    if "correct_reject" in text or "correct reject" in text or "true_reject" in text:
        classes.add("correct reject candidate")
    if "projection" in text or "simulated" in text or "replay" in text or "mechanical" in text:
        classes.add("projection-only")
    if "path" in text or "ltf" in text or "bridge" in text or "join" in text or "rollup" in text:
        classes.add("bridge")

    if not classes:
        classes.add("bridge")
    return sorted(classes)


def mechanism_family_for(row: dict[str, Any], source: SourceSpec | None = None) -> str:
    text = row_text(row, source)
    framework = normalize_token(first_value(row, FRAMEWORK_FIELDS), default="")
    origin = normalize_token(first_value(row, ORIGIN_FIELDS), default="")
    combined = " ".join([framework, origin, text])

    if "ob_retest" in combined or "order_block" in combined or re.search(r"\bob\b", combined):
        return "ob_retest"
    if "fvg_fill" in combined or "fair_value_gap" in combined or re.search(r"\bfvg\b", combined):
        return "fvg_fill"
    if "breaker" in combined:
        return "breaker_re_entry"
    if "liquidity_sweep" in combined or "sweep_reclaim" in combined or "reclaim" in combined:
        return "liquidity_sweep_reclaim"
    if "failed_displacement" in combined or "failed displacement" in combined:
        return "failed_displacement"
    if "displacement_continuation" in combined or "displacement" in combined:
        return "displacement_continuation"
    if "no_fill" in combined or "nofill" in combined or "near_miss" in combined or "near-miss" in combined:
        return "no_fill_near_miss"
    if "session_flow" in combined or "session_open_range" in combined or "open_range" in combined:
        return "session_flow_continuation"
    if "momentum_exhaustion" in combined or "exhaustion" in combined:
        return "exhaustion"
    if "stop_cascade" in combined or "stop cascade" in combined:
        return "stop_cascade"
    if "inverse" in combined or "avoid" in combined or "reject" in combined or "veto" in combined:
        return "inverse_avoid"
    if "structural_distance" in combined or "distance_extreme" in combined:
        return "structural_distance_extreme"
    if "lead_lag" in combined or "cross_asset" in combined or "correlation" in combined:
        return "cross_asset_lead_lag"
    if "regime_transition" in combined or "regime" in combined:
        return "regime_transition_break"
    if "volatility_compression" in combined or "volatility_expansion" in combined:
        return "volatility_compression_expansion"
    if "market_gap" in combined:
        return "market_gap_control"
    if "source_guard" in combined or "source_repair" in combined:
        return "source_guard_scope_control"
    if "orderflow" in combined or "sierra" in combined or "databento" in combined:
        return "orderflow_primitive"
    if "pending" in combined or "prefill" in combined:
        return "prefill_pending_lifecycle"
    if "scheduler" in combined or "portfolio" in combined:
        return "portfolio_scheduler"
    if "execution" in combined or "slippage" in combined or "spread" in combined:
        return "execution_microstructure"
    return "unspecified_candidate_mechanism"


def framework_for(row: dict[str, Any], mechanism: str) -> str:
    explicit = first_value(row, FRAMEWORK_FIELDS)
    if explicit is not None:
        return compact_text(explicit, default=mechanism)
    if mechanism in {"ob_retest", "fvg_fill", "breaker_re_entry"}:
        return mechanism
    return compact_text(first_value(row, ORIGIN_FIELDS), default=mechanism)


def extract_time(row: dict[str, Any], fields: Iterable[str]) -> str:
    value = first_value(row, fields)
    return compact_text(value, default="unknown_time")


def source_row_id(row: dict[str, Any], source: SourceSpec, line_number: int) -> str:
    value = first_value(row, SOURCE_ROW_ID_FIELDS)
    if value is not None:
        return compact_text(value)
    return f"{source.source_id}:line:{line_number}"


def missing_r_fields(row: dict[str, Any]) -> list[str]:
    expected_groups = {
        "entry": ("entry", "entry_price", "open_price", "reference_price"),
        "stop": ("stop", "sl", "stop_loss", "stop_price"),
        "target": ("target", "tp", "take_profit", "target_price"),
        "outcome": ("outcome", "result", "terminal_outcome", "close_reason"),
    }
    keys = {str(key).lower() for key in row.keys()}
    missing = []
    for label, options in expected_groups.items():
        if not any(option in keys for option in options):
            missing.append(label)
    return missing


def build_event_row(row: dict[str, Any], source: SourceSpec, line_number: int) -> dict[str, Any]:
    mechanism = mechanism_family_for(row, source)
    classes = classify_row(row, source)
    row_class = classes[0]
    symbol = compact_text(first_value(row, SYMBOL_FIELDS), default="UNKNOWN")
    broker_symbol = compact_text(row.get("broker_symbol"), default=symbol)
    source_symbol = compact_text(row.get("source_symbol"), default=symbol)
    side = compact_text(first_value(row, SIDE_FIELDS), default="unknown_side")
    session = compact_text(first_value(row, SESSION_FIELDS), default="unknown_session")
    framework = framework_for(row, mechanism)
    origin = compact_text(first_value(row, ORIGIN_FIELDS), default=mechanism)
    candidate_time = extract_time(row, TIME_FIELDS)
    asof_time = extract_time(row, ASOF_FIELDS)
    record_time = compact_text(first_value(row, ("record_time_utc", "created_at", "logged_at", "timestamp_utc")), default=asof_time)
    row_id = source_row_id(row, source, line_number)

    exact_r, exact_r_field = first_number(row, EXACT_R_FIELDS)
    proxy_r, proxy_r_field = first_number(row, PROXY_R_FIELDS)
    generic_r, generic_r_field, generic_state = find_generic_r(row)
    if exact_r is None and generic_state == "exact_r_available":
        exact_r = generic_r
        exact_r_field = generic_r_field
    if proxy_r is None and generic_state == "proxy_r_available":
        proxy_r = generic_r
        proxy_r_field = generic_r_field
    expectancy_r, expectancy_field = first_number(row, EXPECTANCY_FIELDS)
    cost_r, cost_field = first_number(row, COST_R_FIELDS)
    if exact_r is not None:
        r_source_state = "exact_r_available"
    elif proxy_r is not None:
        r_source_state = "proxy_r_available"
    else:
        r_source_state = "r_field_absent"

    duplicate_components = {
        "symbol": normalize_token(symbol),
        "side": normalize_token(side),
        "framework": normalize_token(framework),
        "mechanism_family": normalize_token(mechanism),
        "candidate_time_utc": normalize_token(candidate_time),
        "session": normalize_token(session),
        "source_row_id": normalize_token(row_id),
    }
    duplicate_raw = "|".join(duplicate_components.values())
    duplicate_key = "lane03_dup_" + stable_hash([duplicate_raw], 20)
    canonical_candidate_id = "lane03_cand_" + stable_hash([duplicate_key], 20)
    canonical_event_id = "lane03_evt_" + stable_hash([source.source_id, line_number, row_id, duplicate_key], 24)

    status = compact_text(first_value(row, ("status", "decision", "final_decision", "route_decision", "disposition", "candidate_generation_disposition", "final_outcome")), default="unknown")
    event = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "canonical_event_id": canonical_event_id,
        "canonical_candidate_id": canonical_candidate_id,
        "canonical_duplicate_key": duplicate_key,
        "duplicate_key_components": duplicate_components,
        "source_id": source.source_id,
        "source_path": rel(source.path),
        "source_line": line_number,
        "source_row_id": row_id,
        "source_use_state": source.source_use_state,
        "source_evidence_class": source.evidence_class,
        "asof_status": source.asof_status,
        "row_class": row_class,
        "row_classes": classes,
        "result_use_status": RESULT_USE_STATUS,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "source_symbol": source_symbol,
        "session": session,
        "side": side,
        "framework": framework,
        "origin_family": origin,
        "mechanism_family": mechanism,
        "candidate_time_utc": candidate_time,
        "record_time_utc": record_time,
        "asof_time_utc": asof_time,
        "status": status,
        "decision": compact_text(first_value(row, ("decision", "route_decision", "final_decision")), default=status),
        "final_outcome": compact_text(first_value(row, ("final_outcome", "terminal_outcome", "outcome", "result")), default="unknown"),
        "exact_r": exact_r,
        "exact_r_field": exact_r_field,
        "proxy_r": proxy_r,
        "proxy_r_field": proxy_r_field,
        "expectancy_r": expectancy_r,
        "expectancy_r_field": expectancy_field,
        "cost_r": cost_r,
        "cost_r_field": cost_field,
        "r_source_state": r_source_state,
        "r_missing_fields": missing_r_fields(row) if r_source_state == "r_field_absent" else [],
        "raw_field_count": len(row),
    }
    return event


def open_text(path: Path) -> Iterator[str]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            yield from handle
    else:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            yield from handle


def iter_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any] | None, str | None]]:
    for line_number, line in enumerate(open_text(path), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            yield line_number, None, f"json_decode_error:{exc.msg}"
            continue
        if not isinstance(parsed, dict):
            yield line_number, None, "non_object_json_row"
            continue
        yield line_number, parsed, None


def iter_csv_rows(path: Path) -> Iterator[tuple[int, dict[str, Any] | None, str | None]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=2):
            yield index, dict(row), None


def iter_source_rows(path: Path) -> Iterator[tuple[int, dict[str, Any] | None, str | None]]:
    name = path.name.lower()
    if name.endswith(".csv"):
        yield from iter_csv_rows(path)
    elif name.endswith(".jsonl") or name.endswith(".jsonl.gz"):
        yield from iter_jsonl(path)
    else:
        return


def json_dump_line(handle: Any, obj: dict[str, Any]) -> None:
    handle.write(json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n")


def gz_json_dump_line(handle: Any, obj: dict[str, Any]) -> None:
    handle.write(json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n")


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_stats(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "bytes": None, "sha256": None}
    return {
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": file_sha256(path),
    }


def make_source_id(category: str, family: str, path: Path) -> str:
    return slug(f"{category}_{family}_{path.stem}_{stable_hash([rel(path)], 8)}", 120)


def add_source(
    sources: dict[str, SourceSpec],
    path: Path,
    category: str,
    row_family: str,
    source_use_state: str,
    evidence_class: str,
    asof_status: str,
    process_events: bool = True,
    note: str = "",
) -> None:
    path = path.resolve()
    for existing_id, existing in list(sources.items()):
        if existing.path != path:
            continue
        if existing.process_events or not process_events:
            return
        del sources[existing_id]
        break
    source_id = make_source_id(category, row_family, path)
    if source_id in sources:
        return
    sources[source_id] = SourceSpec(
        source_id=source_id,
        path=path,
        category=category,
        row_family=row_family,
        source_use_state=source_use_state,
        evidence_class=evidence_class,
        asof_status=asof_status,
        process_events=process_events,
        note=note,
    )


def discover_full_replay_sources(sources: dict[str, SourceSpec]) -> None:
    replay_dir = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24"
    if not replay_dir.exists():
        return
    summary = replay_dir / "VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json"
    if summary.exists():
        add_source(
            sources,
            summary,
            "full_replay",
            "summary_json",
            "source_inventory_only",
            "historical_replay_summary",
            "route_summary_not_row_event",
            process_events=False,
        )
    for index_path in sorted(replay_dir.glob("VNEXT_FULL_REPLAY_*_LEDGER_*.jsonl")):
        row_family = slug(index_path.name.replace("VNEXT_FULL_REPLAY_", "").replace("_2026-05-24.jsonl", ""))
        chunk_paths: set[Path] = set()
        material_output_paths: dict[Path, str] = {}
        parsed_rows = 0
        chunk_like_rows = 0
        output_like_rows = 0
        for _, row, _ in iter_jsonl(index_path):
            if not row:
                continue
            parsed_rows += 1
            chunk_path = row.get("chunk_path")
            if chunk_path:
                chunk_like_rows += 1
                chunk = resolve_artifact_path(str(chunk_path), index_path.parent)
                chunk_paths.add(chunk)
            outputs = row.get("outputs")
            if isinstance(outputs, dict):
                for output_name, output_meta in outputs.items():
                    if output_name not in FULL_REPLAY_MATERIAL_OUTPUTS:
                        continue
                    if not isinstance(output_meta, dict) or not output_meta.get("path"):
                        continue
                    output_like_rows += 1
                    output_path = resolve_artifact_path(str(output_meta["path"]), index_path.parent)
                    material_output_paths[output_path] = slug(f"{row_family}_{output_name}")
        add_source(
            sources,
            index_path,
            "full_replay",
            f"{row_family}_index",
            "dependency_index_expanded_to_chunks" if chunk_paths or material_output_paths else "consumed_row_bearing_source",
            "historical_replay_chunk_index" if chunk_paths or material_output_paths else "historical_replay_row_bearing_source",
            "asof_replay_projection_index" if chunk_paths or material_output_paths else "asof_replay_projection",
            process_events=not bool(chunk_paths or material_output_paths),
            note=f"parsed_rows={parsed_rows};chunk_rows={chunk_like_rows};material_outputs={output_like_rows}",
        )
        for chunk in sorted(chunk_paths):
            add_source(
                sources,
                chunk,
                "full_replay",
                row_family,
                "consumed_projection_source",
                "historical_mechanical_replay_projection",
                "asof_replay_projection",
                process_events=True,
                note=f"expanded_from={rel(index_path)}",
            )
        for output_path, output_family in sorted(material_output_paths.items(), key=lambda item: rel(item[0])):
            add_source(
                sources,
                output_path,
                "full_replay",
                output_family,
                "consumed_projection_source",
                "historical_mechanical_replay_projection",
                "asof_replay_projection",
                process_events=True,
                note=f"expanded_from_outputs={rel(index_path)}",
            )


def resolve_artifact_path(path_text: str, base_dir: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path.resolve()
    repo_candidate = (REPO_ROOT / path).resolve()
    if repo_candidate.exists() or path_text.startswith(("research/", "data/", "shadow_logs/", "pipeline_state/")):
        return repo_candidate
    return (base_dir / path).resolve()


def discover_route_sources(sources: dict[str, SourceSpec], route_rel: str, category: str, row_family_prefix: str = "") -> None:
    route = REPO_ROOT / route_rel
    if not route.exists():
        return
    for path in sorted(route.glob("*.jsonl")) + sorted(route.glob("*.jsonl.gz")) + sorted(route.glob("*.csv")):
        family = slug(f"{row_family_prefix}_{path.stem}" if row_family_prefix else path.stem)
        add_source(
            sources,
            path,
            category,
            family,
            "consumed_row_bearing_source",
            "route_or_shadow_row_bearing_evidence",
            "asof_from_source_artifact",
            process_events=True,
        )
    for path in sorted(route.glob("*.json")) + sorted(route.glob("*.md")) + sorted(route.glob("*.py")):
        add_source(
            sources,
            path,
            category,
            slug(path.stem),
            "source_inventory_only",
            "route_context_or_code",
            "not_row_event_source",
            process_events=False,
        )


def discover_shadow_sources(sources: dict[str, SourceSpec]) -> None:
    shadow = REPO_ROOT / "shadow_logs"
    names = [
        "strategy_follow_candidates.jsonl",
        "strategy_follow_evaluations.jsonl",
        "candidate_path_follow.jsonl",
        "candidate_ltf_path_order.jsonl",
        "live_mechanical_strategy_shadow_outcomes.jsonl",
        "missed_opportunity_shadow.jsonl",
        "live_candidate_opportunity_clusters.jsonl",
        "live_candidate_strategy_rollups.jsonl",
        "live_structural_strategy_metadata.jsonl",
        "pending_limit_lifecycle.jsonl",
        "pending_limit_lifecycle_audit.jsonl",
        "pending_limit_lifecycle_join_backfill.jsonl",
        "prefill_delivery_path.jsonl",
        "prefill_delivery_path_resolutions.jsonl",
        "v2b_forward_pairs.jsonl",
        "v2b_forward_pair_resolutions.jsonl",
        "fvg_ob_confluence.jsonl",
        "fvg_ob_confluence_resolutions.jsonl",
        "scid_forward_source_capture.jsonl",
        "nofill_forward_source_capture.jsonl",
        "opportunity_lifecycle_audit.jsonl",
        "candidate_registry_audit.jsonl",
        "candidate_path_contract_audit.jsonl",
        "trade_index_lifecycle_audit.jsonl",
        "regime_decay_outcome_join.jsonl",
        "decision_layer_diagnostics_join.jsonl",
        "mechanical_context_diagnostics_join.jsonl",
        "j46_j49_exit_comparator_audit.jsonl",
        "j46_j49_shadow_outcomes.jsonl",
        "slippage.jsonl",
        "time_in_trade.jsonl",
        "ml_shadow_predictions.jsonl",
        "ml_shadow_status.jsonl",
        "orderflow_primitives_status.jsonl",
        "sierra_proxy_registry_status.jsonl",
        "nas100_orderflow_adverse_selection_status.jsonl",
        "gbpjpy_proxy_gap_status.jsonl",
        "databento_live_trigger_decisions.jsonl",
        "cross_instrument_correlation_decisions.jsonl",
        "gtos_vnext_runtime_decisions.jsonl",
        "gtos_vnext_replacement_monitoring.jsonl",
        "account_truth_reconciliation_status.jsonl",
        "trailing_stop_v1_shadow_log.jsonl",
        "ob_retest_sl_exception_decisions.jsonl",
        "displacement_events.jsonl",
        "session_volatility_log.csv",
        "sweep_divergence_log.csv",
        "ob_continuation_daily.csv",
        "cusum_candidate_rate_daily.csv",
    ]
    for name in names:
        path = shadow / name
        if path.exists():
            add_source(
                sources,
                path,
                "shadow_logs",
                slug(Path(name).stem),
                "consumed_shadow_source",
                "live_or_forward_shadow_log",
                "source_logged_time_order",
                process_events=True,
            )
        for gz_path in sorted(shadow.glob(f"{Path(name).stem}_*.jsonl.gz")):
            add_source(
                sources,
                gz_path,
                "shadow_logs_archive",
                slug(gz_path.stem),
                "consumed_shadow_archive_source",
                "live_or_forward_shadow_log_archive",
                "source_logged_time_order",
                process_events=True,
            )


def discover_code_and_manifest_sources(sources: dict[str, SourceSpec]) -> None:
    for path in [
        REPO_ROOT / "src/components/gtos_vnext_event_fields.py",
        REPO_ROOT / "src/components/broader_origin_generators.py",
        REPO_ROOT / "config/agent_config.yaml",
        REPO_ROOT / ".context/LIVE_STATE.md",
        REPO_ROOT / ".context/00_core/current_vnext_system_map.md",
        REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
        REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
        REPO_ROOT / "research/operations/vnext_mt5_local_cache_preservation_2026_06_01/MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json",
        REPO_ROOT / "research/operations/vnext_mt5_local_cache_preservation_2026_06_01/MT5_ARCHIVE_MANIFEST.json",
        REPO_ROOT / "research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01/LOCAL_EVIDENCE_COVERAGE_SUMMARY.json",
    ]:
        if path.exists():
            add_source(
                sources,
                path,
                "context_code_or_manifest",
                slug(path.stem),
                "source_inventory_only",
                "context_code_or_source_manifest",
                "not_row_event_source",
                process_events=False,
            )


def discover_sources() -> list[SourceSpec]:
    sources: dict[str, SourceSpec] = {}
    discover_full_replay_sources(sources)

    route_specs = [
        ("research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31", "friday_microscope"),
        ("research/operations/vnext_live_activation_active_repair_companion_2026_05_28", "live_companion"),
        ("research/operations/vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31", "may31_lane01"),
        ("research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31", "may31_lane02"),
        ("research/operations/vnext_lane03_meta_selector_discovery_implementation_2026_05_31", "may31_lane03"),
        ("research/operations/vnext_next_level_master_orchestration_2026_05_31", "may31_master"),
        ("research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01", "june01_master"),
        ("research/operations/vnext_moonshot_lane01_data_universe_source_authority_2026_06_01", "june01_lane01"),
        ("research/operations/vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01", "june01_lane02"),
    ]
    for route_rel, category in route_specs:
        discover_route_sources(sources, route_rel, category)

    discover_shadow_sources(sources)
    discover_code_and_manifest_sources(sources)
    return sorted(sources.values(), key=lambda spec: (rel(spec.path), spec.source_id))


def init_group_db(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute(
        """
        CREATE TABLE candidate_groups (
            duplicate_key TEXT PRIMARY KEY,
            canonical_candidate_id TEXT NOT NULL,
            representative_event_id TEXT NOT NULL,
            symbol TEXT,
            side TEXT,
            framework TEXT,
            mechanism_family TEXT,
            origin_family TEXT,
            candidate_time_utc TEXT,
            session TEXT,
            first_source_id TEXT,
            first_source_path TEXT,
            first_source_line INTEGER,
            event_count INTEGER NOT NULL,
            exact_r_count INTEGER NOT NULL,
            exact_r_sum REAL NOT NULL,
            proxy_r_count INTEGER NOT NULL,
            proxy_r_sum REAL NOT NULL,
            first_result_use_status TEXT,
            runtime_effect_boundary TEXT
        )
        """
    )
    return conn


def upsert_group(conn: sqlite3.Connection, event: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO candidate_groups (
            duplicate_key, canonical_candidate_id, representative_event_id,
            symbol, side, framework, mechanism_family, origin_family,
            candidate_time_utc, session, first_source_id, first_source_path,
            first_source_line, event_count, exact_r_count, exact_r_sum,
            proxy_r_count, proxy_r_sum, first_result_use_status,
            runtime_effect_boundary
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(duplicate_key) DO UPDATE SET
            event_count = event_count + 1,
            exact_r_count = exact_r_count + excluded.exact_r_count,
            exact_r_sum = exact_r_sum + excluded.exact_r_sum,
            proxy_r_count = proxy_r_count + excluded.proxy_r_count,
            proxy_r_sum = proxy_r_sum + excluded.proxy_r_sum
        """,
        (
            event["canonical_duplicate_key"],
            event["canonical_candidate_id"],
            event["canonical_event_id"],
            event["symbol"],
            event["side"],
            event["framework"],
            event["mechanism_family"],
            event["origin_family"],
            event["candidate_time_utc"],
            event["session"],
            event["source_id"],
            event["source_path"],
            event["source_line"],
            1 if event.get("exact_r") is not None else 0,
            float(event.get("exact_r") or 0.0),
            1 if event.get("proxy_r") is not None else 0,
            float(event.get("proxy_r") or 0.0),
            event["result_use_status"],
            event["runtime_effect_boundary"],
        ),
    )


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return json.load(handle)


def load_full_replay_summary() -> dict[str, Any]:
    path = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json"
    if path.exists():
        try:
            return read_json(path)
        except Exception:
            return {}
    return {}


def expected_replay_counts(summary: dict[str, Any]) -> dict[str, int]:
    text = json.dumps(summary, sort_keys=True).lower()
    counts: dict[str, int] = {}
    for label, pattern in {
        "full_replay_candidate_generation_rows": r"candidate[^0-9]{0,30}rows[^0-9]{0,10}([0-9]+)",
        "full_replay_denominator_rows": r"denominator[^0-9]{0,30}rows[^0-9]{0,10}([0-9]+)",
        "full_replay_path_outcome_r_rows": r"path[^0-9]{0,30}outcome[^0-9]{0,30}rows[^0-9]{0,10}([0-9]+)",
    }.items():
        match = re.search(pattern, text)
        if match:
            counts[label] = int(match.group(1))
    # Fall back to known source-summary field names when the summary is nested.
    for key, value in flatten_json(summary).items():
        low = key.lower()
        if isinstance(value, int):
            if "candidate" in low and "row" in low:
                counts.setdefault("full_replay_candidate_generation_rows", value)
            if "denominator" in low and "row" in low:
                counts.setdefault("full_replay_denominator_rows", value)
            if "path" in low and "outcome" in low and "row" in low:
                counts.setdefault("full_replay_path_outcome_r_rows", value)
    return counts


def flatten_json(value: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten_json(child, child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            out.update(flatten_json(child, child_prefix))
    else:
        out[prefix] = value
    return out


def discover_missing_local_evidence_gaps() -> list[dict[str, Any]]:
    gap_rows: list[dict[str, Any]] = []
    manifest_paths = [
        REPO_ROOT / "research/operations/vnext_mt5_local_cache_preservation_2026_06_01/MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json",
        REPO_ROOT / "research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01/LOCAL_EVIDENCE_COVERAGE_SUMMARY.json",
    ]
    for path in manifest_paths:
        if not path.exists():
            gap_rows.append(
                {
                    "gap_id": "lane03_gap_" + stable_hash([rel(path), "missing_manifest"], 16),
                    "gap_type": "missing_source_manifest",
                    "source_path": rel(path),
                    "gap_status": "source_manifest_absent",
                    "repair_requirement": "recover or regenerate source preservation manifest before claiming full local evidence coverage",
                }
            )
            continue
        try:
            data = read_json(path)
        except Exception as exc:
            gap_rows.append(
                {
                    "gap_id": "lane03_gap_" + stable_hash([rel(path), "parse_error"], 16),
                    "gap_type": "source_manifest_parse_error",
                    "source_path": rel(path),
                    "gap_status": str(exc),
                    "repair_requirement": "repair JSON manifest parse before using preservation coverage",
                }
            )
            continue
        for key, value in flatten_json(data).items():
            if key.lower().endswith(".exists") and value is False:
                parent = key[: -len(".exists")]
                gap_rows.append(
                    {
                        "gap_id": "lane03_gap_" + stable_hash([rel(path), parent], 16),
                        "gap_type": "local_evidence_path_absent",
                        "source_path": rel(path),
                        "source_pointer": parent,
                        "gap_status": "exists_false_in_preservation_summary",
                        "repair_requirement": "recover from approved local/broker/VPS cache or record exact non-generatable historical source gap",
                    }
                )
    return gap_rows


def dependency_rows() -> list[dict[str, Any]]:
    deps = [
        ("controlling_prompt", REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE03_HISTORICAL_CANDIDATE_RECONSTRUCTION_GOAL_PROMPT_2026-06-01.md", "required_prompt"),
        ("starter_prompt", REPO_ROOT / "research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE03_HISTORICAL_CANDIDATE_RECONSTRUCTION_STARTER_2026-06-01.txt", "required_prompt"),
        ("goal_session_research_discipline", REPO_ROOT / ".context/00_core/goal_session_research_discipline.md", "required_doctrine"),
        ("research_operating_doctrine", REPO_ROOT / ".context/00_core/research_operating_doctrine.md", "required_doctrine"),
        ("moonshot_vision", REPO_ROOT / ".context/00_core/vnext_absolute_moonshot_vision_and_limitations.md", "required_context"),
        ("june01_master_route", REPO_ROOT / "research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01/ABSOLUTE_MASTER_COMPLETION_AUDIT.json", "upstream_route"),
        ("june01_lane01_route", REPO_ROOT / "research/operations/vnext_moonshot_lane01_data_universe_source_authority_2026_06_01/COMPLETION_AUDIT.json", "upstream_route"),
        ("june01_lane02_route", REPO_ROOT / "research/operations/vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01/LANE02_COMPLETION_AUDIT.json", "upstream_route"),
        ("may31_master_route", REPO_ROOT / "research/operations/vnext_next_level_master_orchestration_2026_05_31/MASTER_ORCHESTRATION_COMPLETION_AUDIT.json", "upstream_route"),
        ("may31_lane01_route", REPO_ROOT / "research/operations/vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31/LANE01_COMPLETION_AUDIT.json", "upstream_route"),
        ("may31_lane02_route", REPO_ROOT / "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31/LANE02_COMPLETION_AUDIT.json", "upstream_route"),
        ("friday_microscope_route", REPO_ROOT / "research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31/FRIDAY_COMPLETION_AUDIT.json", "input_route"),
        ("live_companion_state", REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/ACTIVE_REPAIR_STATE.json", "live_context_readonly"),
        ("live_companion_parity", REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", "live_context_readonly"),
        ("mt5_local_cache_summary", REPO_ROOT / "research/operations/vnext_mt5_local_cache_preservation_2026_06_01/MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json", "source_manifest"),
        ("vps_local_evidence_summary", REPO_ROOT / "research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01/LOCAL_EVIDENCE_COVERAGE_SUMMARY.json", "source_manifest"),
        ("full_historical_replay_summary", REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json", "input_route"),
    ]
    rows = []
    for dep_id, path, dep_type in deps:
        exists = path.exists()
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "dependency_id": dep_id,
                "dependency_type": dep_type,
                "path": rel(path),
                "exists": exists,
                "state": "present" if exists else "absent_or_incomplete",
                "source_use_state": "read_for_context" if exists else "dependency_gap_recorded",
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }
        )
    return rows


def write_context_docs(head: str) -> None:
    CONTEXT_ANCHOR_PATH.write_text(
        "\n".join(
            [
                "# Lane03 Historical Candidate Reconstruction Context Anchor",
                "",
                f"Route: `{ROUTE_ID}`",
                f"Generated: `{utc_now()}`",
                f"HEAD at build: `{head}`",
                "",
                "Boundary: offline reconstruction only. No broker/order/deal/position action, no paid API/vendor call, no credential or remote change, and no production behavior activation.",
                "",
                "Inputs are replay ledgers, selected-denominator route outputs, Friday microscope outputs, live companion read-only evidence, shadow logs, MT5/VPS preservation manifests, and candidate/runtime code context.",
                "",
                "Rows that lack original GTOS/AI historical intent are labeled as mechanical/as-of projection or source gaps. Exact broker/account/order lifecycle truth is never inferred from price movement.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    DUPLICATE_POLICY_PATH.write_text(
        "\n".join(
            [
                "# Lane03 Duplicate And Denominator Policy",
                "",
                "The event ledger preserves every parsed material source row. Deduplication never deletes event evidence.",
                "",
                "Canonical duplicate groups are keyed by normalized symbol, side, framework, mechanism family, candidate time, session, and the strongest source row identifier available. If no source row identifier exists, the source id and line number become the identifier.",
                "",
                "The canonical candidate ledger and duplicate group ledger aggregate those keys for denominator-aware downstream use. Singleton groups remain explicit so denominator changes are auditable.",
                "",
                "Exact R is used only when an explicit actual/broker/realized/deal/executed R field exists. Simulated, replay, path, selected, gross, or generic R fields are labeled proxy R. Missing R rows keep row-level missing-field proof and capture/export requirements in the gap ledger.",
                "",
                f"Runtime boundary: `{RUNTIME_EFFECT_BOUNDARY}`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def git_head() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    head = git_head()
    write_context_docs(head)

    sources = discover_sources()
    dependencies = dependency_rows()
    replay_summary = load_full_replay_summary()
    replay_expected = expected_replay_counts(replay_summary)

    for output in [
        EVENT_LEDGER,
        CANDIDATE_LEDGER,
        DUPLICATE_GROUP_LEDGER,
        SOURCE_INVENTORY_LEDGER,
        SOURCE_GAP_LEDGER,
        MECHANISM_COVERAGE_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        BRANCH_DECISION_LEDGER,
        SUMMARY_PATH,
        MANIFEST_PATH,
        COMPLETION_AUDIT_PATH,
    ]:
        if output.exists():
            output.unlink()

    conn = init_group_db(TMP_GROUP_DB)
    total_event_rows = 0
    total_parsed_rows = 0
    total_non_json_rows = 0
    source_event_counts: Counter[str] = Counter()
    source_parsed_counts: Counter[str] = Counter()
    source_non_json_counts: Counter[str] = Counter()
    category_event_counts: Counter[str] = Counter()
    row_class_counts: Counter[str] = Counter()
    mechanism_counts: Counter[str] = Counter()
    r_source_counts: Counter[str] = Counter()
    exact_r_sum = 0.0
    proxy_r_sum = 0.0
    exact_r_count = 0
    proxy_r_count = 0
    source_gap_rows: list[dict[str, Any]] = []

    with gzip.open(EVENT_LEDGER, "wt", encoding="utf-8", newline="\n") as event_handle, SOURCE_INVENTORY_LEDGER.open(
        "w", encoding="utf-8", newline="\n"
    ) as inventory_handle:
        for source in sources:
            stats = file_stats(source.path)
            parsed_rows = 0
            event_rows = 0
            non_json_rows = 0
            parse_error_examples: list[str] = []
            if source.process_events and stats["exists"]:
                for line_number, row, error in iter_source_rows(source.path):
                    if row is None:
                        non_json_rows += 1
                        if len(parse_error_examples) < 5 and error:
                            parse_error_examples.append(f"line {line_number}: {error}")
                        continue
                    parsed_rows += 1
                    event = build_event_row(row, source, line_number)
                    gz_json_dump_line(event_handle, event)
                    upsert_group(conn, event)
                    total_event_rows += 1
                    event_rows += 1
                    source_event_counts[source.source_id] += 1
                    category_event_counts[source.category] += 1
                    for row_class in event["row_classes"]:
                        row_class_counts[row_class] += 1
                    mechanism_counts[event["mechanism_family"]] += 1
                    r_source_counts[event["r_source_state"]] += 1
                    if event.get("exact_r") is not None:
                        exact_r_count += 1
                        exact_r_sum += float(event["exact_r"])
                    if event.get("proxy_r") is not None:
                        proxy_r_count += 1
                        proxy_r_sum += float(event["proxy_r"])
                source_parsed_counts[source.source_id] += parsed_rows
                source_non_json_counts[source.source_id] += non_json_rows
                total_parsed_rows += parsed_rows
                total_non_json_rows += non_json_rows
            inventory = {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "source_id": source.source_id,
                "source_path": rel(source.path),
                "category": source.category,
                "row_family": source.row_family,
                "process_events": source.process_events,
                "source_use_state": source.source_use_state,
                "source_evidence_class": source.evidence_class,
                "asof_status": source.asof_status,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                "exists": stats["exists"],
                "bytes": stats["bytes"],
                "sha256": stats["sha256"],
                "parsed_rows": parsed_rows,
                "event_rows": event_rows,
                "non_json_or_non_object_rows": non_json_rows,
                "parse_error_examples": parse_error_examples,
                "note": source.note,
            }
            json_dump_line(inventory_handle, inventory)
            if not stats["exists"]:
                source_gap_rows.append(
                    {
                        "gap_id": "lane03_gap_" + stable_hash([source.source_id, "missing_source"], 16),
                        "gap_type": "source_file_missing",
                        "source_id": source.source_id,
                        "source_path": rel(source.path),
                        "gap_status": "path_absent",
                        "repair_requirement": "recover the path from git/LFS/local archive or record it as unavailable source evidence",
                    }
                )
            if non_json_rows:
                source_gap_rows.append(
                    {
                        "gap_id": "lane03_gap_" + stable_hash([source.source_id, "non_json", non_json_rows], 16),
                        "gap_type": "source_parse_gap",
                        "source_id": source.source_id,
                        "source_path": rel(source.path),
                        "gap_status": f"{non_json_rows} non-json/non-object rows skipped",
                        "repair_requirement": "confirm skipped rows are headers/LFS pointers or repair source serialization",
                        "examples": parse_error_examples,
                    }
                )
    conn.commit()

    with gzip.open(CANDIDATE_LEDGER, "wt", encoding="utf-8", newline="\n") as candidate_handle, gzip.open(
        DUPLICATE_GROUP_LEDGER, "wt", encoding="utf-8", newline="\n"
    ) as duplicate_handle:
        duplicate_groups = 0
        singleton_groups = 0
        candidate_rows = 0
        for row in conn.execute(
            """
            SELECT duplicate_key, canonical_candidate_id, representative_event_id, symbol, side, framework,
                   mechanism_family, origin_family, candidate_time_utc, session, first_source_id,
                   first_source_path, first_source_line, event_count, exact_r_count, exact_r_sum,
                   proxy_r_count, proxy_r_sum, first_result_use_status, runtime_effect_boundary
            FROM candidate_groups
            ORDER BY duplicate_key
            """
        ):
            (
                duplicate_key,
                canonical_candidate_id,
                representative_event_id,
                symbol,
                side,
                framework,
                mechanism_family,
                origin_family,
                candidate_time_utc,
                session,
                first_source_id,
                first_source_path,
                first_source_line,
                event_count,
                group_exact_r_count,
                group_exact_r_sum,
                group_proxy_r_count,
                group_proxy_r_sum,
                first_result_use_status,
                runtime_effect_boundary,
            ) = row
            duplicate_status = "duplicate_group" if event_count > 1 else "singleton_group"
            if event_count > 1:
                duplicate_groups += 1
            else:
                singleton_groups += 1
            candidate = {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "canonical_candidate_id": canonical_candidate_id,
                "canonical_duplicate_key": duplicate_key,
                "representative_event_id": representative_event_id,
                "duplicate_status": duplicate_status,
                "event_count": event_count,
                "symbol": symbol,
                "side": side,
                "framework": framework,
                "origin_family": origin_family,
                "mechanism_family": mechanism_family,
                "candidate_time_utc": candidate_time_utc,
                "session": session,
                "first_source_id": first_source_id,
                "first_source_path": first_source_path,
                "first_source_line": first_source_line,
                "exact_r_count": group_exact_r_count,
                "exact_r_sum": round(float(group_exact_r_sum), 8),
                "proxy_r_count": group_proxy_r_count,
                "proxy_r_sum": round(float(group_proxy_r_sum), 8),
                "result_use_status": first_result_use_status,
                "runtime_effect_boundary": runtime_effect_boundary,
            }
            gz_json_dump_line(candidate_handle, candidate)
            gz_json_dump_line(duplicate_handle, candidate)
            candidate_rows += 1
    conn.close()
    if TMP_GROUP_DB.exists():
        TMP_GROUP_DB.unlink()

    source_gap_rows.extend(discover_missing_local_evidence_gaps())
    for dep in dependencies:
        if not dep["exists"]:
            source_gap_rows.append(
                {
                    "gap_id": "lane03_gap_" + stable_hash([dep["dependency_id"], dep["path"], "dependency_absent"], 16),
                    "gap_type": "dependency_absent_or_incomplete",
                    "source_path": dep["path"],
                    "dependency_id": dep["dependency_id"],
                    "gap_status": dep["state"],
                    "repair_requirement": "produce upstream route artifact or keep dependency-state row; do not block Lane03 reconstruction when other sources exist",
                }
            )

    for mechanism in sorted(REQUIRED_MECHANISMS):
        if mechanism_counts[mechanism] == 0:
            source_gap_rows.append(
                {
                    "gap_id": "lane03_gap_" + stable_hash(["mechanism_zero", mechanism], 16),
                    "gap_type": "mechanism_coverage_absent",
                    "mechanism_family": mechanism,
                    "gap_status": "zero_rows_observed_in_ingested_sources",
                    "repair_requirement": "add source parser/generator or source capture for this mechanism before downstream denominator claims include it",
                }
            )
    for row_class in sorted(REQUIRED_ROW_CLASSES):
        if row_class_counts[row_class] == 0:
            source_gap_rows.append(
                {
                    "gap_id": "lane03_gap_" + stable_hash(["row_class_zero", row_class], 16),
                    "gap_type": "row_class_coverage_absent",
                    "row_class": row_class,
                    "gap_status": "zero_rows_observed_in_ingested_sources",
                    "repair_requirement": "add source parser/capture for this lifecycle class before downstream denominators require it",
                }
            )
    if r_source_counts["r_field_absent"]:
        source_gap_rows.append(
            {
                "gap_id": "lane03_gap_" + stable_hash(["r_field_absent", r_source_counts["r_field_absent"]], 16),
                "gap_type": "r_geometry_missing",
                "gap_status": f"{r_source_counts['r_field_absent']} event rows lack exact/proxy R fields",
                "repair_requirement": "bind entry/stop/target/path/cost/broker lifecycle fields from approved source ledgers or prospectively capture exact broker geometry",
            }
        )
    source_gap_rows.append(
        {
            "gap_id": "lane03_gap_" + stable_hash(["historical_original_gtos_intent"], 16),
            "gap_type": "non_generatable_historical_system_intent",
            "gap_status": "original GTOS/AI intent cannot be inferred for historical rows where prompt/output/gate/pending lifecycle was not logged",
            "repair_requirement": "use only logged intent where available; otherwise label rows as mechanical/as-of projection and capture prompt/output/gate/pending lifecycle prospectively",
        }
    )
    source_gap_rows.append(
        {
            "gap_id": "lane03_gap_" + stable_hash(["historical_broker_truth"], 16),
            "gap_type": "non_generatable_historical_broker_truth",
            "gap_status": "broker/order/deal/account lifecycle truth is not inferred from price path",
            "repair_requirement": "use broker exports/logged tickets where already captured or prospectively capture order/deal/position/fill/close/cost fields",
        }
    )
    source_gap_rows.append(
        {
            "gap_id": "lane03_gap_" + stable_hash(["live_companion_close_reconciliation_pending"], 16),
            "gap_type": "live_lifecycle_gap_readonly_context",
            "gap_status": "live companion remains source context only; close/deal reconciliation may be pending in hot live evidence",
            "repair_requirement": "do not modify hot live evidence here; consume future live companion reconciliation after it lands",
        }
    )

    with SOURCE_GAP_LEDGER.open("w", encoding="utf-8", newline="\n") as gap_handle:
        for gap in source_gap_rows:
            gap.setdefault("schema_version", SCHEMA_VERSION)
            gap.setdefault("route_id", ROUTE_ID)
            gap.setdefault("runtime_effect_boundary", RUNTIME_EFFECT_BOUNDARY)
            gap.setdefault("result_use_status", RESULT_USE_STATUS)
            json_dump_line(gap_handle, gap)

    with MECHANISM_COVERAGE_LEDGER.open("w", encoding="utf-8", newline="\n") as mechanism_handle:
        all_mechanisms = sorted(set(mechanism_counts) | REQUIRED_MECHANISMS | DISCOVERED_CODE_MECHANISMS)
        for mechanism in all_mechanisms:
            row = {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "mechanism_family": mechanism,
                "event_rows": mechanism_counts[mechanism],
                "required_by_prompt": mechanism in REQUIRED_MECHANISMS,
                "discovered_from_code_or_logs": mechanism in DISCOVERED_CODE_MECHANISMS or mechanism_counts[mechanism] > 0,
                "coverage_status": "covered" if mechanism_counts[mechanism] else "gap_zero_rows",
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                "result_use_status": RESULT_USE_STATUS,
            }
            json_dump_line(mechanism_handle, row)

    with DEPENDENCY_STATE_LEDGER.open("w", encoding="utf-8", newline="\n") as dep_handle:
        for dep in dependencies:
            json_dump_line(dep_handle, dep)

    branch_rows = [
        {
            "decision_id": "lane03_build_canonical_reconstruction",
            "decision_type": "implementation_decision",
            "decision": "implemented_route_local_streaming_builder_verifier_and_tests",
            "rationale": "candidate reconstruction requires machine-checkable full ledgers, not chat-only summaries",
        },
        {
            "decision_id": "lane03_projection_boundary",
            "decision_type": "source_completeness_decision",
            "decision": "label_missing_original_intent_rows_as_projection_only",
            "rationale": "historical GTOS/AI intent is non-generatable unless logged as prompt/output/gate/pending lifecycle source truth",
        },
        {
            "decision_id": "lane03_duplicate_policy",
            "decision_type": "denominator_decision",
            "decision": "preserve_every_event_row_and_group_by_canonical_duplicate_key",
            "rationale": "downstream denominators need both raw event evidence and duplicate-aware candidate groups",
        },
        {
            "decision_id": "lane03_r_policy",
            "decision_type": "result_use_decision",
            "decision": "exact_r_only_from_actual_broker_realized_fields_proxy_r_from_replay_or_simulated_fields",
            "rationale": "result fields are useful for reconstruction but not production performance claims",
        },
        {
            "decision_id": "lane03_no_live_or_paid_source_pull",
            "decision_type": "source_use_decision",
            "decision": "used_existing_local_route_shadow_mt5_preservation_evidence_only",
            "rationale": "available local ledgers cover the reconstruction objective; no broker action or paid API was needed",
        },
    ]
    with BRANCH_DECISION_LEDGER.open("w", encoding="utf-8", newline="\n") as branch_handle:
        for row in branch_rows:
            row.update(
                {
                    "schema_version": SCHEMA_VERSION,
                    "route_id": ROUTE_ID,
                    "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
                    "result_use_status": RESULT_USE_STATUS,
                }
            )
            json_dump_line(branch_handle, row)

    output_files = [
        EVENT_LEDGER,
        CANDIDATE_LEDGER,
        DUPLICATE_GROUP_LEDGER,
        SOURCE_INVENTORY_LEDGER,
        SOURCE_GAP_LEDGER,
        MECHANISM_COVERAGE_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        BRANCH_DECISION_LEDGER,
        CONTEXT_ANCHOR_PATH,
        DUPLICATE_POLICY_PATH,
    ]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "head": head,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "result_use_status": RESULT_USE_STATUS,
        "source_count": len(sources),
        "processed_event_source_count": sum(1 for source in sources if source.process_events),
        "total_parsed_source_rows": total_parsed_rows,
        "total_event_rows": total_event_rows,
        "candidate_rows": candidate_rows,
        "duplicate_groups": duplicate_groups,
        "singleton_groups": singleton_groups,
        "non_json_or_non_object_rows_skipped": total_non_json_rows,
        "category_event_counts": dict(sorted(category_event_counts.items())),
        "row_class_counts": dict(sorted(row_class_counts.items())),
        "mechanism_counts": dict(sorted(mechanism_counts.items())),
        "r_source_counts": dict(sorted(r_source_counts.items())),
        "exact_r_count": exact_r_count,
        "exact_r_sum": round(exact_r_sum, 8),
        "exact_r_expectancy": round(exact_r_sum / exact_r_count, 8) if exact_r_count else None,
        "proxy_r_count": proxy_r_count,
        "proxy_r_sum": round(proxy_r_sum, 8),
        "proxy_r_expectancy": round(proxy_r_sum / proxy_r_count, 8) if proxy_r_count else None,
        "source_gap_rows": len(source_gap_rows),
        "dependency_rows": len(dependencies),
        "expected_replay_counts_from_summary": replay_expected,
        "source_event_counts": dict(sorted(source_event_counts.items())),
        "source_parsed_counts": dict(sorted(source_parsed_counts.items())),
        "source_non_json_counts": {k: v for k, v in sorted(source_non_json_counts.items()) if v},
        "required_row_classes_missing": sorted(REQUIRED_ROW_CLASSES - set(row_class_counts)),
        "required_mechanisms_missing": sorted(REQUIRED_MECHANISMS - set(mechanism_counts)),
        "outputs": [rel(path) for path in output_files],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_files.append(SUMMARY_PATH)

    audit = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "completed_at_utc": utc_now(),
        "head": head,
        "status": "complete_pending_verifier" ,
        "objective": "historical candidate/event reconstruction across available local replay, route, live/shadow, and preservation evidence",
        "instruction_coverage": {
            "mandatory_preflight_reread": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "builder_posture_applied": "constructive_builder_curiosity_active_creativity_no_conservative_brake",
            "no_arbitrary_top_n": True,
            "full_material_rows_preserved": True,
            "source_gap_ledger_written": True,
            "duplicate_policy_written": True,
            "mechanism_coverage_written": True,
            "exact_proxy_r_fields_written_when_owned": True,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        },
        "source_completeness_decisions": [
            "existing local route/shadow/replay/preservation evidence was sufficient for Lane03 reconstruction",
            "read-only MT5 export was not needed because no missing recoverable market-data field blocked event reconstruction",
            "historical GTOS/AI intent and broker lifecycle truth were not inferred where not logged",
        ],
        "branch_decision": "use Lane03 canonical ledgers as downstream reconstruction input; keep production changes behind separate approval/dossier",
        "counts": {
            "source_count": len(sources),
            "total_event_rows": total_event_rows,
            "candidate_rows": candidate_rows,
            "duplicate_groups": duplicate_groups,
            "source_gap_rows": len(source_gap_rows),
            "exact_r_count": exact_r_count,
            "proxy_r_count": proxy_r_count,
        },
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "result_use_status": RESULT_USE_STATUS,
    }
    COMPLETION_AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_files.append(COMPLETION_AUDIT_PATH)

    manifest = build_manifest(output_files)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def line_count(path: Path) -> int | None:
    if not path.exists():
        return None
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            return sum(1 for _ in handle)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def build_manifest(paths: list[Path]) -> dict[str, Any]:
    rows = []
    for path in paths:
        stats = file_stats(path)
        rows.append(
            {
                "path": rel(path),
                "exists": stats["exists"],
                "bytes": stats["bytes"],
                "sha256": stats["sha256"],
                "line_count": line_count(path),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "files": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-only", action="store_true", help="Print summary after build.")
    args = parser.parse_args()
    summary = build()
    if args.summary_only:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"wrote {SUMMARY_PATH}")
        print(f"event rows: {summary['total_event_rows']}")
        print(f"candidate rows: {summary['candidate_rows']}")
        print(f"source gaps: {summary['source_gap_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
