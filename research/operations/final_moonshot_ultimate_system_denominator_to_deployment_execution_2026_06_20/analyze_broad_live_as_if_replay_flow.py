#!/usr/bin/env python3
"""Summarize broad live-as-if replay behavior from completed route ledgers.

This reads the BROAD_LIVE_AS_IF_REPLAY artifacts emitted by
run_broad_live_as_if_replay_harness.py and writes deterministic diagnostics for
raw-vs-guarded behavior. It is replay-only: broker/live/final authority remains
closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROUTE = Path(__file__).resolve().parent
PREFIX = "BROAD_LIVE_AS_IF_REPLAY"

SUMMARY_PATH = ROUTE / f"{PREFIX}_SUMMARY.json"
COMPARISON_PATH = ROUTE / f"{PREFIX}_COMPARISON_LEDGER.jsonl"
TRADE_PATH = ROUTE / f"{PREFIX}_TRADE_LEDGER.jsonl"
ORDER_PATH = ROUTE / f"{PREFIX}_ORDER_LEDGER.jsonl"
CANDIDATE_PATH = ROUTE / f"{PREFIX}_CANDIDATE_LEDGER.jsonl"
CANDIDATE_INDEX_PATH = ROUTE / f"{PREFIX}_CANDIDATE_INDEX_LEDGER.jsonl"
DECISION_PATH = ROUTE / f"{PREFIX}_DECISION_LEDGER.jsonl"
MISSED_PATH = ROUTE / f"{PREFIX}_MISSED_OPPORTUNITY_LEDGER.jsonl"
SCORECARD_PATH = ROUTE / f"{PREFIX}_SCORECARD_LEDGER.jsonl"
CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH = (
    ROUTE / "CANDIDATE_INSTANCE_PARITY_PROJECTION_LEDGER.jsonl"
)

FLOW_SUMMARY_PATH = ROUTE / f"{PREFIX}_FLOW_DIAGNOSTIC_SUMMARY.json"
FLOW_BUCKET_PATH = ROUTE / f"{PREFIX}_FLOW_BUCKET_LEDGER.jsonl"
FLOW_DOSSIER_PATH = ROUTE / f"{PREFIX}_FLOW_DIAGNOSTIC_DOSSIER.md"

PROFILE_RAW = "raw_package_live_as_if"
PROFILE_GUARDED = "guarded_causal_admission_repair_v2"
PROFILE_REPAIRED = "repaired_package_conversion_v3"
GUARD_POLICY_PROFILES = {PROFILE_GUARDED, PROFILE_REPAIRED}
JSONL_BINARY_STREAM_MIN_BYTES = 1_000_000
JSONL_LOCAL_CACHE_DIR = Path(
    os.environ.get("GTOS_JSONL_LOCAL_CACHE_DIR", "/tmp/gtos_route_jsonl_cache")
)
JSONL_LOCAL_CACHE_ENABLED = os.environ.get(
    "GTOS_JSONL_LOCAL_CACHE_ENABLED", "1"
).strip().lower() not in {"0", "false", "no", "off"}


def configure_paths(prefix: str) -> None:
    global PREFIX
    global SUMMARY_PATH
    global COMPARISON_PATH
    global TRADE_PATH
    global ORDER_PATH
    global CANDIDATE_PATH
    global CANDIDATE_INDEX_PATH
    global DECISION_PATH
    global MISSED_PATH
    global SCORECARD_PATH
    global CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH
    global FLOW_SUMMARY_PATH
    global FLOW_BUCKET_PATH
    global FLOW_DOSSIER_PATH

    PREFIX = prefix
    SUMMARY_PATH = ROUTE / f"{PREFIX}_SUMMARY.json"
    COMPARISON_PATH = ROUTE / f"{PREFIX}_COMPARISON_LEDGER.jsonl"
    TRADE_PATH = ROUTE / f"{PREFIX}_TRADE_LEDGER.jsonl"
    ORDER_PATH = ROUTE / f"{PREFIX}_ORDER_LEDGER.jsonl"
    CANDIDATE_PATH = ROUTE / f"{PREFIX}_CANDIDATE_LEDGER.jsonl"
    CANDIDATE_INDEX_PATH = ROUTE / f"{PREFIX}_CANDIDATE_INDEX_LEDGER.jsonl"
    DECISION_PATH = ROUTE / f"{PREFIX}_DECISION_LEDGER.jsonl"
    MISSED_PATH = ROUTE / f"{PREFIX}_MISSED_OPPORTUNITY_LEDGER.jsonl"
    SCORECARD_PATH = ROUTE / f"{PREFIX}_SCORECARD_LEDGER.jsonl"
    artifact_tag = (
        PREFIX.removeprefix("BROAD_LIVE_AS_IF_REPLAY_")
        if PREFIX.startswith("BROAD_LIVE_AS_IF_REPLAY_")
        else ""
    )
    projection_suffix = f"_{artifact_tag}" if artifact_tag else ""
    CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH = (
        ROUTE
        / f"CANDIDATE_INSTANCE_PARITY_PROJECTION{projection_suffix}_LEDGER.jsonl"
    )
    CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH = (
        resolve_candidate_instance_parity_projection_path(
            broad_summary_path=SUMMARY_PATH,
            fallback_path=CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH,
        )
    )
    FLOW_SUMMARY_PATH = ROUTE / f"{PREFIX}_FLOW_DIAGNOSTIC_SUMMARY.json"
    FLOW_BUCKET_PATH = ROUTE / f"{PREFIX}_FLOW_BUCKET_LEDGER.jsonl"
    FLOW_DOSSIER_PATH = ROUTE / f"{PREFIX}_FLOW_DIAGNOSTIC_DOSSIER.md"


def resolve_candidate_instance_parity_projection_path(
    *,
    broad_summary_path: Path,
    fallback_path: Path,
) -> Path:
    """Bind the analyzer to the projection path declared by its parity producer."""

    matches: list[tuple[int, Path]] = []
    for parity_summary_path in ROUTE.glob(
        "SOURCE_BOUND_TO_EXECUTED_PARITY_*_SUMMARY.json"
    ):
        try:
            payload = json.loads(parity_summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        artifacts = payload.get("artifacts")
        artifacts = artifacts if isinstance(artifacts, Mapping) else {}
        declared_broad_summary = str(artifacts.get("broad_replay_summary") or "")
        if Path(declared_broad_summary).name != broad_summary_path.name:
            continue
        declared_projection = str(
            artifacts.get("candidate_instance_parity_projection_ledger") or ""
        )
        if not declared_projection:
            continue
        projection_path = Path(declared_projection)
        if not projection_path.exists():
            projection_path = ROUTE / projection_path.name
        if not projection_path.exists():
            continue
        try:
            modified_ns = parity_summary_path.stat().st_mtime_ns
        except OSError:
            modified_ns = 0
        matches.append((modified_ns, projection_path))
    if not matches:
        return fallback_path
    return max(matches, key=lambda item: item[0])[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        raise SystemExit(f"required completed artifact missing or empty: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"expected object JSON at {path}")
    return data


def local_cached_jsonl_path(path: Path) -> Path:
    if not JSONL_LOCAL_CACHE_ENABLED:
        return path
    path_size = path.stat().st_size if path.exists() else 0
    if path_size < JSONL_BINARY_STREAM_MIN_BYTES:
        return path
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return path
    cache_key = hashlib.sha256(
        f"{path.resolve()}|{path_size}|{mtime_ns}".encode("utf-8")
    ).hexdigest()[:24]
    cached = JSONL_LOCAL_CACHE_DIR / f"{cache_key}_{path.name}"
    if cached.exists() and cached.stat().st_size == path_size:
        return cached
    JSONL_LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = cached.with_suffix(cached.suffix + ".tmp")
    if tmp.exists():
        try:
            if tmp.stat().st_size == path_size:
                tmp.replace(cached)
                return cached
            tmp.unlink()
        except OSError:
            return path
    try:
        subprocess.run(
            ["/bin/cp", "-p", str(path), str(tmp)],
            check=True,
            timeout=600,
        )
        tmp.replace(cached)
        return cached
    except (OSError, TimeoutError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return path


def iter_binary_text_lines(path: Path, *, chunk_size: int = 4 * 1024 * 1024):
    pending = b""
    timeout_retries = 0
    with path.open("rb") as handle:
        while True:
            try:
                chunk = handle.read(chunk_size)
            except TimeoutError:
                timeout_retries += 1
                if timeout_retries > 1200:
                    raise
                time.sleep(0.5)
                continue
            timeout_retries = 0
            if not chunk:
                if pending:
                    yield pending.decode("utf-8")
                break
            parts = chunk.splitlines(keepends=True)
            if pending:
                parts[0] = pending + parts[0]
                pending = b""
            if parts and not parts[-1].endswith((b"\n", b"\r")):
                pending = parts.pop()
            for raw_line in parts:
                yield raw_line.decode("utf-8")


def iter_text_lines(path: Path) -> Iterable[str]:
    path_size = path.stat().st_size if path.exists() else 0
    if path_size >= JSONL_BINARY_STREAM_MIN_BYTES:
        yield from iter_binary_text_lines(local_cached_jsonl_path(path))
        return
    with path.open("r", encoding="utf-8") as handle:
        yield from handle


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for attempt in range(6):
        try:
            for line_number, line in enumerate(iter_text_lines(path), start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SystemExit(
                        f"invalid JSONL at {path}:{line_number}: {exc}"
                    ) from exc
                if isinstance(row, dict):
                    yield row
            return
        except TimeoutError:
            if attempt >= 5:
                raise
            time.sleep(0.25 * (attempt + 1))


def candidate_flow_rows() -> Iterable[dict[str, Any]]:
    """Read full candidates when present, otherwise compact candidate-index rows."""

    if CANDIDATE_PATH.exists():
        yield from iter_jsonl(CANDIDATE_PATH)
        return
    yield from iter_jsonl(CANDIDATE_INDEX_PATH)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def summary_declared_row_counts(summary: Mapping[str, Any]) -> dict[str, int]:
    stats = summary.get("split_profile_stats")
    if not isinstance(stats, list) or not stats:
        return {}
    counts = {
        "decision": 0,
        "candidate": 0,
        "scorecard": 0,
        "order": 0,
        "trade": 0,
        "missed": 0,
    }
    for row in stats:
        if not isinstance(row, Mapping):
            continue
        counts["decision"] += int(row.get("decision_rows") or 0)
        counts["candidate"] += int(row.get("candidate_rows") or 0)
        counts["scorecard"] += int(row.get("scorecard_rows") or 0)
        counts["order"] += int(row.get("order_rows") or 0)
        trade_rows = row.get("trade_rows")
        if trade_rows is None:
            trade_rows = row.get("filled_trade_count")
        counts["trade"] += int(trade_rows or 0)
        counts["missed"] += int(row.get("missed_opportunity_rows") or 0)
    return counts


def safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def parse_utc(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def add_number(current: float, value: Any) -> float:
    number = safe_float(value)
    if number is None:
        return current
    return round(current + number, 10)


def text(value: Any, default: str = "unknown") -> str:
    if value is None or value == "":
        return default
    return str(value)


def trade_r_source_label(row: Mapping[str, Any]) -> str:
    """Classify terminal trade-R provenance from the serialized trade row."""

    path_source = text(row.get("path_source"), "").strip().lower()
    path_timeframe = text(row.get("path_source_timeframe"), "").strip().upper()
    terminal_status = text(
        row.get("terminal_r_scoreability_status"), ""
    ).strip().lower()
    source_boundaries = "|".join(
        text(row.get(field), "").strip().lower()
        for field in (
            "selected_execution_policy_replay_source_boundary",
            "fill_realism_source_boundary",
            "entry_fill_authority_source_boundary",
        )
    )
    ordered_tick_truth = row.get("ordered_tick_truth_satisfied") is True

    if path_source == "tick" or path_timeframe == "TICK":
        return (
            "simulated_ordered_tick_path"
            if ordered_tick_truth
            else "simulated_tick_path_without_ordered_tick_truth"
        )
    if path_source == "m1" or path_timeframe == "M1":
        return "simulated_ordered_m1_path_proxy"
    if ordered_tick_truth:
        return "simulated_ordered_tick_path"
    if "ordered_tick" in terminal_status or "ordered_tick" in source_boundaries:
        return "simulated_tick_path_without_explicit_path_source"
    if "m1" in terminal_status or "m1" in source_boundaries:
        return "simulated_ordered_m1_path_proxy"
    return "simulated_path_source_unreported"


def trade_r_evidence_boundary(
    trade_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Summarize mixed terminal-R sources without promoting broker authority."""

    source_counts: Counter[str] = Counter()
    scoreable_source_counts: Counter[str] = Counter()
    unscoreable_source_counts: Counter[str] = Counter()
    source_by_symbol: dict[str, Counter[str]] = defaultdict(Counter)
    path_source_counts: Counter[str] = Counter()
    path_timeframe_counts: Counter[str] = Counter()
    entry_source_counts: Counter[str] = Counter()
    fill_realism_source_counts: Counter[str] = Counter()
    terminal_status_counts: Counter[str] = Counter()

    for row in trade_rows:
        source_label = trade_r_source_label(row)
        symbol = text(row.get("symbol"))
        source_counts[source_label] += 1
        source_by_symbol[symbol][source_label] += 1
        path_source_counts[text(row.get("path_source"), "unreported")] += 1
        path_timeframe_counts[
            text(row.get("path_source_timeframe"), "unreported")
        ] += 1
        entry_source_counts[
            text(row.get("entry_fill_authority_source_boundary"), "unreported")
        ] += 1
        fill_realism_source_counts[
            text(row.get("fill_realism_source_boundary"), "unreported")
        ] += 1
        terminal_status_counts[
            text(row.get("terminal_r_scoreability_status"), "unreported")
        ] += 1
        if row.get("net_proxy_r") is None:
            unscoreable_source_counts[source_label] += 1
        else:
            scoreable_source_counts[source_label] += 1

    if not source_counts:
        aggregate_source = "no_executed_trade_rows"
        source_mix_status = "none"
    elif len(source_counts) == 1:
        aggregate_source = next(iter(source_counts))
        source_mix_status = "single_source"
    else:
        aggregate_source = "mixed_simulated_ordered_path_sources"
        source_mix_status = "mixed_sources"

    return {
        "executed_trade_r_source": aggregate_source,
        "executed_trade_r_source_mix_status": source_mix_status,
        "executed_trade_r_source_row_count": sum(source_counts.values()),
        "executed_trade_r_source_counts": dict(sorted(source_counts.items())),
        "scoreable_trade_r_source_counts": dict(
            sorted(scoreable_source_counts.items())
        ),
        "unscoreable_trade_r_source_counts": dict(
            sorted(unscoreable_source_counts.items())
        ),
        "executed_trade_r_source_by_symbol": {
            symbol: dict(sorted(counts.items()))
            for symbol, counts in sorted(source_by_symbol.items())
        },
        "path_source_counts": dict(sorted(path_source_counts.items())),
        "path_source_timeframe_counts": dict(
            sorted(path_timeframe_counts.items())
        ),
        "entry_fill_authority_source_boundary_counts": dict(
            sorted(entry_source_counts.items())
        ),
        "fill_realism_source_boundary_counts": dict(
            sorted(fill_realism_source_counts.items())
        ),
        "terminal_r_scoreability_status_counts": dict(
            sorted(terminal_status_counts.items())
        ),
        "trade_r_source_attribution_authority": (
            "serialized_trade_row_path_source_timeframe_ordered_tick_truth_"
            "and_terminal_scoreability"
        ),
        "missed_opportunity_r_source": "post_asof_timewarp_replay_label",
        "broker_real_cash_pnl_available": False,
        "exact_broker_lifecycle_truth_available": False,
        "missing_or_reconstructed_r": (
            "trade R provenance is preserved per serialized trade row and may "
            "mix ordered-tick truth with ordered-M1 proxy outcomes; exact broker "
            "fill lifecycle/cash R remains unavailable"
        ),
    }


def summarize_candidate_instance_parity_projection(
    path: Path,
) -> dict[str, Any]:
    """Recompute V220 projection diagnostics so every contract field is consumed."""

    if not path.exists() or path.stat().st_size <= 0:
        return {
            "status": "candidate_instance_parity_projection_not_materialized",
            "path": str(path),
            "row_count": 0,
        }

    key_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    selector_counts: Counter[str] = Counter()
    quality_status_counts: Counter[str] = Counter()
    quality_violation_counts: Counter[str] = Counter()
    quality_source_counts: Counter[str] = Counter()
    quality_field_source_counts: dict[str, Counter[str]] = {
        field: Counter()
        for field in ("expected_net_r", "probability", "source_completeness")
    }
    quality_value_counts: Counter[str] = Counter()
    quality_value_ranges: dict[str, list[float | None]] = {
        field: [None, None]
        for field in (
            "canonical_expected_net_r",
            "canonical_probability",
            "canonical_source_completeness",
        )
    }
    package_authority_valid_counts: Counter[str] = Counter()
    package_authority_status_counts: Counter[str] = Counter()
    package_order_allowed_counts: Counter[str] = Counter()
    package_order_reason_counts: Counter[str] = Counter()
    package_order_transfer_status_counts: Counter[str] = Counter()
    package_order_blocker_counts: Counter[str] = Counter()
    package_order_blocker_reason_counts: Counter[str] = Counter()
    package_order_blocker_source_counts: Counter[str] = Counter()
    risk_finalizer_action_counts: Counter[str] = Counter()
    risk_finalizer_reason_counts: Counter[str] = Counter()
    risk_behavior_counts: Counter[str] = Counter()
    order_risk_behavior_counts: Counter[str] = Counter()
    filled_risk_behavior_counts: Counter[str] = Counter()
    scheduler_rank_counts: Counter[str] = Counter()
    binding_counts: Counter[str] = Counter()
    fallback_status_counts: Counter[str] = Counter()
    fallback_blocker_counts: Counter[str] = Counter()
    fallback_eligibility_counts: Counter[str] = Counter()
    counterfactual_presence_counts: Counter[str] = Counter()
    counterfactual_source_counts: Counter[str] = Counter()
    deviation_stage_counts: Counter[str] = Counter()
    deviation_reason_counts: Counter[str] = Counter()
    source_scope_mode_counts: Counter[str] = Counter()
    source_prefix_counts: Counter[str] = Counter()
    selected_date_start_counts: Counter[str] = Counter()
    selected_date_end_counts: Counter[str] = Counter()
    selected_profile_contract_counts: Counter[str] = Counter()
    candidate_source_class_counts: Counter[str] = Counter()
    candidate_source_path_counts: Counter[str] = Counter()
    candidate_source_binding_counts: Counter[str] = Counter()
    source_window_date_source_counts: Counter[str] = Counter()
    source_window_status_counts: Counter[str] = Counter()
    source_profile_status_counts: Counter[str] = Counter()
    origin_transfer: dict[str, Counter[str]] = defaultdict(Counter)
    selected_expiry = Counter()
    row_count = 0
    min_decision_time: tuple[datetime, str] | None = None
    max_decision_time: tuple[datetime, str] | None = None

    for row in iter_jsonl(path):
        row_count += 1
        source_scope_mode_counts[
            text(row.get("projection_source_scope_mode"), "unknown_source_scope")
        ] += 1
        source_prefix_counts[
            text(row.get("projection_source_prefix"), "missing_source_prefix")
        ] += 1
        selected_date_start_counts[
            text(row.get("projection_selected_date_start"), "missing_date_start")
        ] += 1
        selected_date_end_counts[
            text(row.get("projection_selected_date_end"), "missing_date_end")
        ] += 1
        selected_profiles = row.get("projection_selected_profiles")
        selected_profile_contract_counts[
            json.dumps(
                selected_profiles if isinstance(selected_profiles, list) else [],
                sort_keys=True,
            )
        ] += 1
        candidate_source_class_counts[
            text(
                row.get("projection_candidate_source_class"),
                "unknown_candidate_source",
            )
        ] += 1
        candidate_source_path_counts[
            text(row.get("projection_candidate_source_path"), "missing_source_path")
        ] += 1
        candidate_source_binding_counts[
            text(
                row.get("projection_candidate_source_binding_status"),
                "unknown_source_binding",
            )
        ] += 1
        source_window_date_source_counts[
            text(
                row.get("projection_source_window_date_source"),
                "unknown_window_date_source",
            )
        ] += 1
        source_window_status_counts[
            text(
                row.get("projection_source_window_status"),
                "selected_window_or_trading_day_unavailable",
            )
        ] += 1
        source_profile_status_counts[
            text(
                row.get("projection_source_profile_status"),
                "selected_profile_or_candidate_profile_unavailable",
            )
        ] += 1
        decision_time_text = text(row.get("decision_time_utc"), "")
        decision_time = parse_utc(decision_time_text)
        if decision_time is not None:
            decision_item = (decision_time, decision_time_text)
            min_decision_time = (
                decision_item
                if min_decision_time is None or decision_time < min_decision_time[0]
                else min_decision_time
            )
            max_decision_time = (
                decision_item
                if max_decision_time is None or decision_time > max_decision_time[0]
                else max_decision_time
            )
        key_counts[text(row.get("candidate_instance_parity_key"), "missing")] += 1
        for stage, field_name in (
            ("candidate", "candidate_present"),
            ("scorecard", "scorecard_present"),
            ("scheduler_selected", "scheduler_selected"),
            ("order", "order_present"),
            ("trade", "trade_present"),
            ("missed", "missed_present"),
        ):
            stage_counts[stage] += int(row.get(field_name) is True)
        selector_counts[
            f"{text(row.get('raw_selector_action'))}->{text(row.get('effective_selector_action'))}"
        ] += 1
        quality_status_counts[
            text(row.get("canonical_quality_contract_status"))
        ] += 1
        violations = row.get("canonical_quality_contract_violations")
        if isinstance(violations, list):
            quality_violation_counts.update(text(value) for value in violations)
        quality_source_counts[text(row.get("canonical_quality_source"), "missing")] += 1
        field_sources = row.get("canonical_quality_field_sources")
        field_sources = field_sources if isinstance(field_sources, Mapping) else {}
        for field_name, counter in quality_field_source_counts.items():
            counter[text(field_sources.get(field_name), "missing")] += 1
        for field_name, bounds in quality_value_ranges.items():
            value = safe_float(row.get(field_name))
            quality_value_counts[f"{field_name}_present"] += int(value is not None)
            if value is None:
                continue
            bounds[0] = value if bounds[0] is None else min(float(bounds[0]), value)
            bounds[1] = value if bounds[1] is None else max(float(bounds[1]), value)
            if field_name == "canonical_source_completeness" and value >= 1.0:
                quality_value_counts["canonical_source_completeness_full"] += 1

        package_authority_valid_counts[
            text(row.get("package_authority_valid"))
        ] += 1
        package_authority_status_counts[
            text(row.get("package_authority_status"))
        ] += 1
        package_order_allowed_counts[
            text(row.get("package_order_executable_allowed"))
        ] += 1
        package_order_reason_counts[
            text(row.get("package_order_executable_reason"))
        ] += 1
        package_order_transfer_status_counts[
            text(row.get("package_order_executable_transfer_status"))
        ] += 1
        package_order_blocker_counts[
            text(row.get("package_order_executable_blocker_class"), "none")
        ] += 1
        package_order_blocker_reason_counts[
            text(row.get("package_order_executable_blocker_reason"), "none")
        ] += 1
        package_order_blocker_source_counts[
            text(row.get("package_order_executable_blocker_source"), "none")
        ] += 1
        risk_finalizer_action_counts[
            text(row.get("risk_finalizer_action"))
        ] += 1
        risk_finalizer_reason_counts[
            text(row.get("risk_finalizer_reason"))
        ] += 1
        risk_behavior = text(row.get("risk_behavior"))
        risk_behavior_counts[risk_behavior] += 1
        if row.get("order_present") is True:
            order_risk_behavior_counts[risk_behavior] += 1
        if row.get("trade_present") is True:
            filled_risk_behavior_counts[risk_behavior] += 1
        scheduler_rank_counts[text(row.get("scheduler_rank"), "not_ranked")] += 1
        for field_name in (
            "order_binding_status",
            "trade_binding_status",
            "order_trade_binding_status",
        ):
            binding_counts[
                f"{field_name}:{text(row.get(field_name))}"
            ] += 1
        fallback_status_counts[
            text(row.get("terminal_fallback_status"), "missing")
        ] += 1
        fallback_blocker_counts[
            text(row.get("terminal_fallback_blocker"), "none")
        ] += 1
        fallback_eligibility_counts[
            text(row.get("terminal_fallback_eligible"))
        ] += 1
        counterfactual_presence_counts[
            text(row.get("terminal_counterfactual_present"))
        ] += 1
        counterfactual_source_counts[
            text(row.get("terminal_counterfactual_source"), "none")
        ] += 1
        deviation_stage_counts[text(row.get("exact_deviation_stage"))] += 1
        deviation_reason_counts[text(row.get("exact_deviation_reason"))] += 1

        origin = text(row.get("origin_family"))
        transfer = origin_transfer[origin]
        transfer["candidate"] += 1
        transfer["scorecard"] += int(row.get("scorecard_present") is True)
        transfer["scheduler_selected"] += int(row.get("scheduler_selected") is True)
        transfer["order"] += int(row.get("order_present") is True)
        transfer["fill"] += int(row.get("trade_present") is True)
        transfer["missed"] += int(row.get("missed_present") is True)
        transfer["scorecard_to_order"] += int(
            row.get("scorecard_present") is True and row.get("order_present") is True
        )
        transfer["order_to_fill"] += int(
            row.get("order_present") is True and row.get("trade_present") is True
        )

        if row.get("selected_expiry_fallback") is True:
            selected_expiry["selected_expiry_candidate_instances"] += 1
            selected_expiry["fallback_configured"] += int(
                row.get("terminal_fallback_configured") is True
            )
            selected_expiry["fallback_eligibility_explicit"] += int(
                isinstance(row.get("terminal_fallback_eligible"), bool)
            )
            selected_expiry["fallback_eligible"] += int(
                row.get("terminal_fallback_eligible") is True
            )
            selected_expiry["fallback_blocked"] += int(
                bool(text(row.get("terminal_fallback_blocker"), ""))
            )
            selected_expiry["fallback_attempted"] += int(
                row.get("terminal_fallback_attempted") is True
            )
            selected_expiry["fallback_applied"] += int(
                row.get("terminal_fallback_applied") is True
            )
            selected_expiry["counterfactual_present"] += int(
                row.get("terminal_counterfactual_present") is True
            )
            selected_expiry["proof_complete"] += int(
                isinstance(row.get("terminal_fallback_eligible"), bool)
                and bool(text(row.get("terminal_fallback_status"), ""))
                and (
                    row.get("terminal_fallback_eligible") is True
                    or bool(text(row.get("terminal_fallback_blocker"), ""))
                )
                and row.get("terminal_counterfactual_present") is True
            )

    origin_output: dict[str, dict[str, Any]] = {}
    for origin, counts in sorted(origin_transfer.items()):
        output = dict(sorted(counts.items()))
        for field_name in (
            "candidate",
            "scorecard",
            "scheduler_selected",
            "order",
            "fill",
            "missed",
            "scorecard_to_order",
            "order_to_fill",
        ):
            output.setdefault(field_name, 0)
        scorecards = int(output.get("scorecard") or 0)
        orders = int(output.get("order") or 0)
        output["scorecard_to_order_rate"] = (
            round(int(output.get("scorecard_to_order") or 0) / scorecards, 8)
            if scorecards
            else None
        )
        output["order_to_fill_rate"] = (
            round(int(output.get("order_to_fill") or 0) / orders, 8)
            if orders
            else None
        )
        origin_output[origin] = output
    duplicate_keys = sorted(key for key, count in key_counts.items() if count > 1)
    duplicate_key_count = sum(
        count - 1 for count in key_counts.values() if count > 1
    )
    out_of_window_count = int(
        source_window_status_counts.get("outside_selected_window", 0)
    )
    unavailable_window_count = sum(
        count
        for status, count in source_window_status_counts.items()
        if status not in {"inside_selected_window", "outside_selected_window"}
    )
    out_of_profile_count = int(
        source_profile_status_counts.get("outside_selected_profile", 0)
    )
    unavailable_profile_count = sum(
        count
        for status, count in source_profile_status_counts.items()
        if status not in {"inside_selected_profile", "outside_selected_profile"}
    )
    source_scope_assertion_status = (
        "fail"
        if duplicate_key_count
        or out_of_window_count
        or unavailable_window_count
        or out_of_profile_count
        or unavailable_profile_count
        else "pass"
    )
    return {
        "status": "candidate_instance_parity_projection_materialized",
        "path": str(path),
        "row_count": row_count,
        "unique_candidate_instance_parity_key_count": len(key_counts),
        "duplicate_candidate_instance_parity_key_count": duplicate_key_count,
        "duplicate_candidate_instance_parity_key_samples": duplicate_keys[:12],
        "projection_source_scope": {
            "projection_row_count": row_count,
            "min_decision_time_utc": (
                min_decision_time[1] if min_decision_time is not None else None
            ),
            "max_decision_time_utc": (
                max_decision_time[1] if max_decision_time is not None else None
            ),
            "row_source_scope_mode_counts": dict(
                sorted(source_scope_mode_counts.items())
            ),
            "row_source_prefix_counts": dict(sorted(source_prefix_counts.items())),
            "row_selected_date_start_counts": dict(
                sorted(selected_date_start_counts.items())
            ),
            "row_selected_date_end_counts": dict(
                sorted(selected_date_end_counts.items())
            ),
            "row_selected_profile_contract_counts": dict(
                sorted(selected_profile_contract_counts.items())
            ),
            "row_candidate_source_class_counts": dict(
                sorted(candidate_source_class_counts.items())
            ),
            "row_candidate_source_path_counts": dict(
                sorted(candidate_source_path_counts.items())
            ),
            "row_candidate_source_binding_status_counts": dict(
                sorted(candidate_source_binding_counts.items())
            ),
            "row_source_window_date_source_counts": dict(
                sorted(source_window_date_source_counts.items())
            ),
            "row_source_window_status_counts": dict(
                sorted(source_window_status_counts.items())
            ),
            "row_source_profile_status_counts": dict(
                sorted(source_profile_status_counts.items())
            ),
            "out_of_window_candidate_instance_count": out_of_window_count,
            "unverifiable_window_candidate_instance_count": (
                unavailable_window_count
            ),
            "out_of_profile_candidate_instance_count": out_of_profile_count,
            "unverifiable_profile_candidate_instance_count": (
                unavailable_profile_count
            ),
            "assertions": {
                "candidate_instance_key_uniqueness": {
                    "status": (
                        "pass"
                        if duplicate_key_count == 0
                        else "fail_duplicate_projection_keys"
                    ),
                    "duplicate_count": duplicate_key_count,
                },
                "selected_window": {
                    "status": (
                        "pass"
                        if out_of_window_count == 0
                        and unavailable_window_count == 0
                        else "fail_projection_rows_outside_or_unverifiable_window"
                    ),
                    "out_of_window_count": out_of_window_count,
                    "unverifiable_count": unavailable_window_count,
                },
                "selected_profile": {
                    "status": (
                        "pass"
                        if out_of_profile_count == 0
                        and unavailable_profile_count == 0
                        else "fail_projection_rows_outside_or_unverifiable_profile"
                    ),
                    "out_of_profile_count": out_of_profile_count,
                    "unverifiable_count": unavailable_profile_count,
                },
            },
            "assertion_status": source_scope_assertion_status,
        },
        "stage_presence_counts": dict(sorted(stage_counts.items())),
        "raw_to_effective_selector_action_counts": dict(
            selector_counts.most_common(24)
        ),
        "canonical_quality_contract": {
            "status_counts": dict(sorted(quality_status_counts.items())),
            "violation_row_count": int(quality_status_counts.get("violation", 0)),
            "violation_reason_counts": dict(quality_violation_counts.most_common(32)),
            "source_counts": dict(quality_source_counts.most_common(24)),
            "field_source_counts": {
                field_name: dict(counter.most_common(24))
                for field_name, counter in quality_field_source_counts.items()
            },
            "value_presence_counts": dict(sorted(quality_value_counts.items())),
            "value_ranges": {
                field_name: {"min": bounds[0], "max": bounds[1]}
                for field_name, bounds in quality_value_ranges.items()
            },
        },
        "package_authority_valid_counts": dict(sorted(package_authority_valid_counts.items())),
        "package_authority_status_counts": dict(package_authority_status_counts.most_common(24)),
        "package_order_executable_allowed_counts": dict(sorted(package_order_allowed_counts.items())),
        "package_order_executable_reason_counts": dict(package_order_reason_counts.most_common(32)),
        "package_order_executable_transfer_status_counts": dict(package_order_transfer_status_counts.most_common(24)),
        "package_order_executable_blocker_class_counts": dict(package_order_blocker_counts.most_common(24)),
        "package_order_executable_blocker_reason_counts": dict(package_order_blocker_reason_counts.most_common(32)),
        "package_order_executable_blocker_source_counts": dict(package_order_blocker_source_counts.most_common(24)),
        "risk_finalizer_action_counts": dict(sorted(risk_finalizer_action_counts.items())),
        "risk_finalizer_reason_counts": dict(risk_finalizer_reason_counts.most_common(32)),
        "scheduler_rank_counts": dict(scheduler_rank_counts.most_common(24)),
        "binding_status_counts": dict(sorted(binding_counts.items())),
        "terminal_fallback_status_counts": dict(fallback_status_counts.most_common(24)),
        "terminal_fallback_blocker_counts": dict(fallback_blocker_counts.most_common(24)),
        "terminal_fallback_eligibility_counts": dict(sorted(fallback_eligibility_counts.items())),
        "terminal_counterfactual_presence_counts": dict(sorted(counterfactual_presence_counts.items())),
        "terminal_counterfactual_source_counts": dict(counterfactual_source_counts.most_common(24)),
        "exact_deviation_stage_counts": dict(sorted(deviation_stage_counts.items())),
        "exact_deviation_reason_counts": dict(deviation_reason_counts.most_common(48)),
        "origin_family_scorecard_order_fill_transfer": origin_output,
        "selected_expiry_fallback_proof": dict(sorted(selected_expiry.items())),
        "full_reduced_risk_behavior": {
            "all_candidate_instance_counts": dict(sorted(risk_behavior_counts.items())),
            "order_counts": dict(sorted(order_risk_behavior_counts.items())),
            "filled_trade_counts": dict(sorted(filled_risk_behavior_counts.items())),
        },
    }


def profile(row: Mapping[str, Any]) -> str:
    return text(row.get("broad_replay_profile"), "unknown_profile")


def split(row: Mapping[str, Any]) -> str:
    return text(row.get("split"), "unknown_split")


def segment(row: Mapping[str, Any]) -> str:
    if row.get("repair_seed_window") is True:
        return "repair_seed"
    if split(row) == "holdout":
        return "true_holdout"
    if split(row) == "development":
        return "non_seed_development"
    return split(row)


def session(row: Mapping[str, Any]) -> str:
    return text(row.get("route_session") or row.get("session") or row.get("session_bucket"))


def guard_status_from_order(row: Mapping[str, Any]) -> tuple[str, str, str]:
    authority = row.get("risk_authority")
    guard = authority.get("replay_loss_bucket_guard") if isinstance(authority, dict) else None
    status = row.get("replay_loss_bucket_guard_status")
    rule_id = row.get("replay_loss_bucket_guard_matched_rule_id")
    reason = row.get("replay_loss_bucket_guard_reason")
    if isinstance(guard, dict):
        status = status or guard.get("status")
        rule_id = rule_id or guard.get("matched_rule_id")
        reason = reason or guard.get("reason")
    return text(status, "not_present"), text(rule_id, "no_rule"), text(reason, "no_reason")


def candidate_cost_r(row: Mapping[str, Any]) -> float:
    authority = row.get("risk_authority")
    guard = authority.get("replay_loss_bucket_guard") if isinstance(authority, dict) else None
    if isinstance(guard, dict):
        cost = safe_float(guard.get("candidate_cost_r"))
        if cost is not None:
            return cost
    cost = safe_float(row.get("expected_cost_r"))
    return cost if cost is not None else 0.0


def trade_headline_result_eligible(row: Mapping[str, Any]) -> bool:
    """Return whether a trade row is headline executable, not diagnostic overlay."""

    if row.get("terminal_r_scoreable") is False:
        return False
    explicit = row.get("headline_result_eligible")
    if explicit is False:
        return False
    reason = str(row.get("headline_result_exclusion_reason") or "").strip()
    if reason and reason != "headline_result_eligible":
        return False
    scope = str(row.get("result_scope") or "").strip().lower()
    if scope.startswith("diagnostic_"):
        return False
    fill_realism_class = str(row.get("fill_realism_class") or "").strip().lower()
    if row.get("diagnostic_fill_only") is True:
        return False
    if row.get("fill_realism_executable") is False:
        return False
    if fill_realism_class in {
        "m15_proxy",
        "first_touch_optimistic",
        "ordered_tick_required_source_gap",
        "guarded_market_fallback_elapsed_path",
        "source_gap",
    }:
        return False
    return True


@dataclass
class Metric:
    rows: int = 0
    all_trade_rows: int = 0
    all_trade_scoreable_rows: int = 0
    all_trade_missing_r_rows: int = 0
    all_trade_win_count: int = 0
    all_trade_loss_count: int = 0
    all_trade_flat_count: int = 0
    all_trade_net_r: float = 0.0
    all_trade_gross_r: float = 0.0
    all_trade_final_r: float = 0.0
    all_trade_expected_cost_r: float = 0.0
    all_trade_cash_pnl: float = 0.0
    all_trade_risk_cash: float = 0.0
    all_trade_risk_pct: float = 0.0
    diagnostic_only_trade_rows: int = 0
    diagnostic_only_scoreable_rows: int = 0
    diagnostic_only_missing_r_rows: int = 0
    diagnostic_only_win_count: int = 0
    diagnostic_only_loss_count: int = 0
    diagnostic_only_flat_count: int = 0
    diagnostic_only_net_r: float = 0.0
    entry_fill_executable_rows: int = 0
    terminal_r_unscoreable_rows: int = 0
    scoreable_rows: int = 0
    missing_r_rows: int = 0
    win_count: int = 0
    loss_count: int = 0
    flat_count: int = 0
    gross_r: float = 0.0
    final_r: float = 0.0
    net_r: float = 0.0
    expected_cost_r: float = 0.0
    cash_pnl: float = 0.0
    risk_cash: float = 0.0
    risk_pct: float = 0.0
    filled_count: int = 0
    blocked_count: int = 0
    blocked_scoreable_count: int = 0
    blocked_win_count: int = 0
    blocked_loss_count: int = 0
    blocked_flat_count: int = 0
    blocked_counterfactual_net_r: float = 0.0
    blocked_counterfactual_final_r: float = 0.0
    missed_scoreable_count: int = 0
    missed_unscoreable_count: int = 0
    missed_net_r: float = 0.0
    missed_positive_net_r: float = 0.0
    missed_negative_net_r: float = 0.0
    missed_flat_count: int = 0
    missed_executable_scoreable_count: int = 0
    missed_executable_net_r: float = 0.0
    missed_executable_positive_count: int = 0
    missed_executable_positive_net_r: float = 0.0
    missed_executable_negative_count: int = 0
    missed_executable_negative_net_r: float = 0.0
    missed_executable_flat_count: int = 0
    missed_diagnostic_scoreable_count: int = 0
    missed_diagnostic_net_r: float = 0.0
    missed_diagnostic_positive_count: int = 0
    missed_diagnostic_positive_net_r: float = 0.0
    missed_diagnostic_negative_count: int = 0
    missed_diagnostic_negative_net_r: float = 0.0
    missed_diagnostic_flat_count: int = 0
    counters: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))

    def add_trade(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        gross = safe_float(row.get("gross_r"))
        final = safe_float(row.get("final_r"))
        net = safe_float(row.get("net_proxy_r"))
        if net is None:
            net = safe_float(row.get("net_r"))
        self.all_trade_rows += 1
        if row.get("entry_fill_executable") is True:
            self.entry_fill_executable_rows += 1
        if row.get("terminal_r_scoreable") is False:
            self.terminal_r_unscoreable_rows += 1
        if net is None:
            self.all_trade_missing_r_rows += 1
        else:
            self.all_trade_scoreable_rows += 1
            self.all_trade_net_r = add_number(self.all_trade_net_r, net)
            if net > 0:
                self.all_trade_win_count += 1
            elif net < 0:
                self.all_trade_loss_count += 1
            else:
                self.all_trade_flat_count += 1
        self.all_trade_gross_r = add_number(self.all_trade_gross_r, gross)
        self.all_trade_final_r = add_number(self.all_trade_final_r, final)
        self.all_trade_expected_cost_r = add_number(
            self.all_trade_expected_cost_r, row.get("expected_cost_r")
        )
        self.all_trade_cash_pnl = add_number(self.all_trade_cash_pnl, row.get("pnl_cash"))
        self.all_trade_risk_cash = add_number(self.all_trade_risk_cash, row.get("risk_cash"))
        self.all_trade_risk_pct = add_number(self.all_trade_risk_pct, row.get("risk_pct"))
        self.counters["headline_result_exclusion_reason"][
            text(row.get("headline_result_exclusion_reason"), "headline_result_eligible")
        ] += 1
        self.counters["result_scope"][text(row.get("result_scope"), "not_reported")] += 1
        self.counters["entry_fill_executable"][
            str(row.get("entry_fill_executable"))
        ] += 1
        self.counters["terminal_r_scoreable"][
            str(row.get("terminal_r_scoreable"))
        ] += 1
        self.counters["terminal_r_scoreability_status"][
            text(row.get("terminal_r_scoreability_status"), "not_reported")
        ] += 1
        if not trade_headline_result_eligible(row):
            self.diagnostic_only_trade_rows += 1
            if net is None:
                self.diagnostic_only_missing_r_rows += 1
            else:
                self.diagnostic_only_scoreable_rows += 1
                self.diagnostic_only_net_r = add_number(self.diagnostic_only_net_r, net)
                if net > 0:
                    self.diagnostic_only_win_count += 1
                elif net < 0:
                    self.diagnostic_only_loss_count += 1
                else:
                    self.diagnostic_only_flat_count += 1
            return
        self.filled_count += 1
        if net is None:
            self.missing_r_rows += 1
        else:
            self.scoreable_rows += 1
            self.net_r = add_number(self.net_r, net)
            if net > 0:
                self.win_count += 1
            elif net < 0:
                self.loss_count += 1
            else:
                self.flat_count += 1
        self.gross_r = add_number(self.gross_r, gross)
        self.final_r = add_number(self.final_r, final)
        self.expected_cost_r = add_number(self.expected_cost_r, row.get("expected_cost_r"))
        self.cash_pnl = add_number(self.cash_pnl, row.get("pnl_cash"))
        self.risk_cash = add_number(self.risk_cash, row.get("risk_cash"))
        self.risk_pct = add_number(self.risk_pct, row.get("risk_pct"))

    def add_order(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        status, rule_id, reason = guard_status_from_order(row)
        self.counters["order_status"][text(row.get("order_status"))] += 1
        self.counters["risk_decision"][text(row.get("risk_decision"))] += 1
        self.counters["risk_decision_reason"][text(row.get("risk_decision_reason"))] += 1
        self.counters["order_intent_materialized"][
            str(row.get("order_intent_materialized"))
        ] += 1
        self.counters["entry_fill_executable"][
            str(row.get("entry_fill_executable"))
        ] += 1
        self.counters["terminal_r_scoreable"][
            str(row.get("terminal_r_scoreable"))
        ] += 1
        self.counters["execution_manager_action"][
            text(row.get("execution_manager_action"))
        ] += 1
        self.counters["execution_manager_should_block"][
            str(bool(row.get("execution_manager_should_block")))
        ] += 1
        self.counters["execution_manager_replay_should_block"][
            str(bool(row.get("execution_manager_replay_should_block")))
        ] += 1
        self.counters["execution_manager_replay_admission_status"][
            text(row.get("execution_manager_replay_admission_status"))
        ] += 1
        self.counters["execution_manager_replay_override_applied"][
            str(bool(row.get("execution_manager_replay_override_applied")))
        ] += 1
        for reason in row.get("execution_manager_fatal_reasons") or []:
            self.counters["execution_manager_fatal_reason"][text(reason)] += 1
        for reason in row.get("execution_manager_live_promotion_blocker_reasons") or []:
            self.counters["execution_manager_live_promotion_blocker_reason"][
                text(reason)
            ] += 1
        for reason in row.get("execution_manager_replay_blocking_reasons") or []:
            self.counters["execution_manager_replay_blocking_reason"][text(reason)] += 1
        self.counters["guard_status"][status] += 1
        self.counters["guard_rule_id"][rule_id] += 1
        self.counters["guard_reason"][reason] += 1
        if row.get("pending_replacement_applied") is True:
            self.counters["lifecycle_action"]["cancel_replace_or_pending_replacement"] += 1
        if status == "blocked":
            self.blocked_count += 1
            final_r = safe_float(row.get("counterfactual_final_r"))
            if final_r is None:
                self.missing_r_rows += 1
                return
            net_r = round(final_r - candidate_cost_r(row), 10)
            self.blocked_scoreable_count += 1
            self.blocked_counterfactual_final_r = add_number(
                self.blocked_counterfactual_final_r, final_r
            )
            self.blocked_counterfactual_net_r = add_number(
                self.blocked_counterfactual_net_r, net_r
            )
            if net_r > 0:
                self.blocked_win_count += 1
            elif net_r < 0:
                self.blocked_loss_count += 1
            else:
                self.blocked_flat_count += 1

    def add_candidate(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        self.counters["selector_action"][text(row.get("selector_action"))] += 1
        self.counters["selector_reason"][text(row.get("selector_reason"))] += 1
        self.counters["origin_family"][text(row.get("origin_family") or row.get("candidate_origin_family"))] += 1
        self.counters["framework"][text(row.get("framework"))] += 1
        self.counters["dynamic_policy"][text(row.get("dynamic_geometry_policy"))] += 1

    def add_decision(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        self.counters["raw_data_status"][text(row.get("raw_data_status"))] += 1
        self.counters["source_window_status"][text(row.get("source_path_feature_status"))] += 1

    def add_scorecard(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        self.counters["selected_action_class"][text(row.get("selected_action_class"))] += 1

    def add_missed(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        scoreability_status = text(
            row.get("missed_opportunity_r_scoreability_status"), "not_reported"
        )
        self.counters["missed_opportunity_r_scoreability_status"][
            scoreability_status
        ] += 1
        self.counters["missed_opportunity_accounting_scope"][
            text(row.get("missed_opportunity_accounting_scope"), "not_reported")
        ] += 1

        headline_scoreable = bool(
            scoreability_status == "headline_r_scoreable"
            or row.get("missed_opportunity_headline_r_scoreable") is True
        )
        diagnostic_scoreable = bool(
            scoreability_status == "diagnostic_opportunity_r_scoreable"
            or row.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
        )
        explicit_unscoreable = bool(
            scoreability_status not in {
                "not_reported",
                "headline_r_scoreable",
                "diagnostic_opportunity_r_scoreable",
            }
            and "unscoreable" in scoreability_status
        )

        scope = "unscoreable"
        net: float | None = None
        if not explicit_unscoreable and headline_scoreable:
            net = safe_float(row.get("net_proxy_r"))
            if net is None:
                net = safe_float(row.get("opportunity_net_proxy_r"))
            scope = "executable"
        elif not explicit_unscoreable and diagnostic_scoreable:
            net = safe_float(row.get("opportunity_net_proxy_r"))
            scope = "diagnostic"
        elif scoreability_status == "not_reported":
            # Backward compatibility for pre-scoreability ledgers. A legacy
            # net_proxy_r was the only missed-R authority exposed by the row.
            net = safe_float(row.get("net_proxy_r"))
            if net is not None:
                scope = "executable"

        if net is None:
            self.missed_unscoreable_count += 1
            self.missing_r_rows += 1
            return
        self.missed_scoreable_count += 1
        self.missed_net_r = add_number(self.missed_net_r, net)
        if net > 0:
            self.missed_positive_net_r = add_number(self.missed_positive_net_r, net)
        elif net < 0:
            self.missed_negative_net_r = add_number(self.missed_negative_net_r, net)
        else:
            self.missed_flat_count += 1

        if scope == "executable":
            self.missed_executable_scoreable_count += 1
            self.missed_executable_net_r = add_number(
                self.missed_executable_net_r, net
            )
            if net > 0:
                self.missed_executable_positive_count += 1
                self.missed_executable_positive_net_r = add_number(
                    self.missed_executable_positive_net_r, net
                )
            elif net < 0:
                self.missed_executable_negative_count += 1
                self.missed_executable_negative_net_r = add_number(
                    self.missed_executable_negative_net_r, net
                )
            else:
                self.missed_executable_flat_count += 1
        elif scope == "diagnostic":
            self.missed_diagnostic_scoreable_count += 1
            self.missed_diagnostic_net_r = add_number(
                self.missed_diagnostic_net_r, net
            )
            if net > 0:
                self.missed_diagnostic_positive_count += 1
                self.missed_diagnostic_positive_net_r = add_number(
                    self.missed_diagnostic_positive_net_r, net
                )
            elif net < 0:
                self.missed_diagnostic_negative_count += 1
                self.missed_diagnostic_negative_net_r = add_number(
                    self.missed_diagnostic_negative_net_r, net
                )
            else:
                self.missed_diagnostic_flat_count += 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "all_trade_rows": self.all_trade_rows,
            "all_trade_scoreable_rows": self.all_trade_scoreable_rows,
            "all_trade_missing_r_rows": self.all_trade_missing_r_rows,
            "all_trade_win_count": self.all_trade_win_count,
            "all_trade_loss_count": self.all_trade_loss_count,
            "all_trade_flat_count": self.all_trade_flat_count,
            "all_trade_net_r": round(self.all_trade_net_r, 8),
            "all_trade_gross_r": round(self.all_trade_gross_r, 8),
            "all_trade_final_r": round(self.all_trade_final_r, 8),
            "all_trade_expected_cost_r": round(self.all_trade_expected_cost_r, 8),
            "all_trade_cash_pnl": round(self.all_trade_cash_pnl, 8),
            "all_trade_risk_cash": round(self.all_trade_risk_cash, 8),
            "all_trade_risk_pct": round(self.all_trade_risk_pct, 8),
            "diagnostic_only_trade_rows": self.diagnostic_only_trade_rows,
            "diagnostic_only_scoreable_rows": self.diagnostic_only_scoreable_rows,
            "diagnostic_only_missing_r_rows": self.diagnostic_only_missing_r_rows,
            "diagnostic_only_win_count": self.diagnostic_only_win_count,
            "diagnostic_only_loss_count": self.diagnostic_only_loss_count,
            "diagnostic_only_flat_count": self.diagnostic_only_flat_count,
            "diagnostic_only_net_r": round(self.diagnostic_only_net_r, 8),
            "entry_fill_executable_rows": self.entry_fill_executable_rows,
            "terminal_r_unscoreable_rows": self.terminal_r_unscoreable_rows,
            "scoreable_rows": self.scoreable_rows,
            "missing_r_rows": self.missing_r_rows,
            "filled_count": self.filled_count,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "flat_count": self.flat_count,
            "gross_r": round(self.gross_r, 8),
            "final_r": round(self.final_r, 8),
            "net_r": round(self.net_r, 8),
            "expected_cost_r": round(self.expected_cost_r, 8),
            "cash_pnl": round(self.cash_pnl, 8),
            "risk_cash": round(self.risk_cash, 8),
            "risk_pct": round(self.risk_pct, 8),
            "win_rate": round(self.win_count / self.scoreable_rows, 8)
            if self.scoreable_rows
            else None,
            "blocked_count": self.blocked_count,
            "blocked_scoreable_count": self.blocked_scoreable_count,
            "blocked_win_count": self.blocked_win_count,
            "blocked_loss_count": self.blocked_loss_count,
            "blocked_flat_count": self.blocked_flat_count,
            "blocked_counterfactual_final_r": round(self.blocked_counterfactual_final_r, 8),
            "blocked_counterfactual_net_r": round(self.blocked_counterfactual_net_r, 8),
            "missed_scoreable_count": self.missed_scoreable_count,
            "missed_unscoreable_count": self.missed_unscoreable_count,
            "missed_net_r": round(self.missed_net_r, 8),
            "missed_positive_net_r": round(self.missed_positive_net_r, 8),
            "missed_negative_net_r": round(self.missed_negative_net_r, 8),
            "missed_flat_count": self.missed_flat_count,
            "missed_executable_scoreable_count": self.missed_executable_scoreable_count,
            "missed_executable_net_r": round(self.missed_executable_net_r, 8),
            "missed_executable_positive_count": self.missed_executable_positive_count,
            "missed_executable_positive_net_r": round(
                self.missed_executable_positive_net_r, 8
            ),
            "missed_executable_negative_count": self.missed_executable_negative_count,
            "missed_executable_negative_net_r": round(
                self.missed_executable_negative_net_r, 8
            ),
            "missed_executable_flat_count": self.missed_executable_flat_count,
            "missed_diagnostic_scoreable_count": self.missed_diagnostic_scoreable_count,
            "missed_diagnostic_net_r": round(self.missed_diagnostic_net_r, 8),
            "missed_diagnostic_positive_count": self.missed_diagnostic_positive_count,
            "missed_diagnostic_positive_net_r": round(
                self.missed_diagnostic_positive_net_r, 8
            ),
            "missed_diagnostic_negative_count": self.missed_diagnostic_negative_count,
            "missed_diagnostic_negative_net_r": round(
                self.missed_diagnostic_negative_net_r, 8
            ),
            "missed_diagnostic_flat_count": self.missed_diagnostic_flat_count,
            "counters": {
                name: dict(counter.most_common())
                for name, counter in sorted(self.counters.items())
            },
        }


class Collector:
    def __init__(self) -> None:
        self.trade: dict[tuple[str, ...], Metric] = defaultdict(Metric)
        self.order: dict[tuple[str, ...], Metric] = defaultdict(Metric)
        self.candidate: dict[tuple[str, ...], Metric] = defaultdict(Metric)
        self.decision: dict[tuple[str, ...], Metric] = defaultdict(Metric)
        self.scorecard: dict[tuple[str, ...], Metric] = defaultdict(Metric)
        self.missed: dict[tuple[str, ...], Metric] = defaultdict(Metric)
        self.row_counts: Counter[str] = Counter()

    def keys(self, row: Mapping[str, Any]) -> list[tuple[str, ...]]:
        base = profile(row)
        row_split = split(row)
        row_segment = segment(row)
        symbol = text(row.get("symbol"))
        side = text(row.get("side") or row.get("direction"))
        day = text(row.get("trading_day") or str(row.get("decision_time_utc") or "")[:10])
        row_session = session(row)
        return [
            ("overall", "all", "all", "all"),
            ("profile", base, "all", "all"),
            ("profile_split", base, row_split, "all"),
            ("profile_segment", base, row_segment, "all"),
            ("symbol", base, row_split, symbol),
            ("trading_day", base, row_split, day),
            ("side", base, row_split, side),
            ("session", base, row_split, row_session),
            ("symbol_side_session", base, row_split, f"{symbol}|{side}|{row_session}"),
            ("symbol_day", base, row_split, f"{symbol}|{day}"),
        ]

    def add_trade(self, row: Mapping[str, Any]) -> None:
        self.row_counts["trade"] += 1
        for key in self.keys(row):
            self.trade[key].add_trade(row)

    def add_order(self, row: Mapping[str, Any]) -> None:
        self.row_counts["order"] += 1
        status, rule_id, _reason = guard_status_from_order(row)
        keys = self.keys(row)
        keys.extend(
            [
                ("order_status", profile(row), split(row), text(row.get("order_status"))),
                ("risk_decision", profile(row), split(row), text(row.get("risk_decision"))),
                ("guard_status", profile(row), split(row), status),
                ("guard_rule_id", profile(row), split(row), rule_id),
                (
                    "execution_manager_replay_admission_status",
                    profile(row),
                    split(row),
                    text(row.get("execution_manager_replay_admission_status")),
                ),
            ]
        )
        for key in keys:
            self.order[key].add_order(row)

    def add_candidate(self, row: Mapping[str, Any]) -> None:
        self.row_counts["candidate"] += 1
        keys = self.keys(row)
        keys.extend(
            [
                ("selector_action", profile(row), split(row), text(row.get("selector_action"))),
                ("selector_reason", profile(row), split(row), text(row.get("selector_reason"))),
                (
                    "origin_family",
                    profile(row),
                    split(row),
                    text(row.get("origin_family") or row.get("candidate_origin_family")),
                ),
            ]
        )
        for key in keys:
            self.candidate[key].add_candidate(row)

    def add_decision(self, row: Mapping[str, Any]) -> None:
        self.row_counts["decision"] += 1
        for key in self.keys(row):
            self.decision[key].add_decision(row)

    def add_scorecard(self, row: Mapping[str, Any]) -> None:
        self.row_counts["scorecard"] += 1
        for key in self.keys(row):
            self.scorecard[key].add_scorecard(row)

    def add_missed(self, row: Mapping[str, Any]) -> None:
        self.row_counts["missed"] += 1
        keys = self.keys(row)
        keys.extend(
            [
                ("miss_reason", profile(row), split(row), text(row.get("miss_reason"))),
                (
                    "opportunity_close_reason",
                    profile(row),
                    split(row),
                    text(row.get("opportunity_close_reason")),
                ),
            ]
        )
        for key in keys:
            self.missed[key].add_missed(row)


def bucket_rows(surface: str, buckets: Mapping[tuple[str, ...], Metric]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (key, metric) in enumerate(sorted(buckets.items()), start=1):
        bucket_type, bucket_profile, bucket_split, bucket_value = key
        rows.append(
            {
            "schema": "gtos.final_moonshot.broad_live_as_if_replay.flow_bucket.v1",
            "row_number": index,
            "surface": surface,
                "bucket_type": bucket_type,
                "profile": bucket_profile,
                "split_or_segment": bucket_split,
                "bucket_value": bucket_value,
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
            "final_selection_claim": False,
            **metric.as_dict(),
        }
        )
    return rows


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            count += 1
    tmp.replace(path)
    return count


def guard_rule_shape(summary: Mapping[str, Any]) -> dict[str, Any]:
    rules = summary.get("guarded_policy", {})
    rule_count = int(rules.get("rule_count") or 0) if isinstance(rules, dict) else 0
    rule_rows: list[dict[str, Any]] = []
    for row in iter_jsonl(ORDER_PATH):
        if profile(row) not in GUARD_POLICY_PROFILES:
            continue
        authority = row.get("risk_authority")
        guard = authority.get("replay_loss_bucket_guard") if isinstance(authority, dict) else None
        config = authority.get("risk_config") if isinstance(authority, dict) else None
        if not isinstance(config, dict):
            config = row.get("risk_config") if isinstance(row.get("risk_config"), dict) else None
        configured_rules = config.get("replay_loss_bucket_guard_rules") if isinstance(config, dict) else None
        if isinstance(configured_rules, list) and configured_rules:
            rule_rows = [dict(item) for item in configured_rules if isinstance(item, dict)]
            break
        if isinstance(guard, dict) and isinstance(guard.get("matched_rule"), dict):
            rule_rows.append(dict(guard["matched_rule"]))
    exact_day = [row for row in rule_rows if row.get("trading_day")]
    wildcard_symbol = [row for row in rule_rows if row.get("symbol") in (None, "*")]
    explicit_symbol_session_side = [
        row
        for row in rule_rows
        if row.get("symbol") not in (None, "*")
        and row.get("session") not in (None, "*")
        and row.get("side") not in (None, "*")
    ]
    selector_action_rules = [row for row in rule_rows if row.get("selector_action")]
    selector_reason_rules = [row for row in rule_rows if row.get("selector_reason")]
    numeric_mixed_count_rules = [
        row
        for row in rule_rows
        if row.get("numeric_mixed_count") not in (None, "", "*")
        or row.get("min_numeric_mixed_count") not in (None, "", "*")
        or row.get("max_numeric_mixed_count") not in (None, "", "*")
    ]
    causal_predecision_rules = [
        row
        for row in rule_rows
        if row.get("selector_action") and not row.get("trading_day")
    ]
    return {
        "configured_rule_count": rule_count or len(rule_rows),
        "rules_observed_in_order_config": len(rule_rows),
        "date_specific_rule_count": len(exact_day),
        "wildcard_symbol_rule_count": len(wildcard_symbol),
        "explicit_symbol_session_side_rule_count": len(explicit_symbol_session_side),
        "selector_action_rule_count": len(selector_action_rules),
        "selector_reason_rule_count": len(selector_reason_rules),
        "numeric_mixed_count_rule_count": len(numeric_mixed_count_rules),
        "causal_predecision_rule_count": len(causal_predecision_rules),
        "interpretation": (
            "guard_uses_selector_admission_predecision_fields_without_date_specific_rules;"
            "treat positive guarded replay as bounded proxy evidence until broader coverage passes"
        ),
        "rule_ids": [text(row.get("rule_id"), "missing_rule_id") for row in rule_rows],
    }


def comparison_digest(summary: Mapping[str, Any]) -> dict[str, Any]:
    comparison_rows = list(iter_jsonl(COMPARISON_PATH))
    split_stats = summary.get("split_profile_stats", [])
    by_key = {
        (row.get("profile"), row.get("split")): row
        for row in split_stats
        if isinstance(row, dict)
    }
    holdout_raw = by_key.get((PROFILE_RAW, "holdout"), {})
    holdout_guarded = by_key.get((PROFILE_GUARDED, "holdout"), {})
    development_raw = by_key.get((PROFILE_RAW, "development"), {})
    development_guarded = by_key.get((PROFILE_GUARDED, "development"), {})
    guarded_holdout_net = safe_float(holdout_guarded.get("net_r"))
    raw_holdout_net = safe_float(holdout_raw.get("net_r"))
    development_guarded_net = safe_float(development_guarded.get("net_r"))
    development_raw_net = safe_float(development_raw.get("net_r"))
    development_delta = (
        round(development_guarded_net - development_raw_net, 8)
        if development_guarded_net is not None and development_raw_net is not None
        else None
    )
    holdout_delta = (
        round(guarded_holdout_net - raw_holdout_net, 8)
        if guarded_holdout_net is not None and raw_holdout_net is not None
        else None
    )
    return {
        "comparison_rows": comparison_rows,
        "development": {
            "raw_net_r": development_raw.get("net_r"),
            "guarded_net_r": development_guarded.get("net_r"),
            "delta_guarded_minus_raw_net_r": development_delta,
            "raw_trades": development_raw.get("filled_trade_count"),
            "guarded_trades": development_guarded.get("filled_trade_count"),
        },
        "holdout": {
            "raw_net_r": holdout_raw.get("net_r"),
            "guarded_net_r": holdout_guarded.get("net_r"),
            "delta_guarded_minus_raw_net_r": holdout_delta,
            "raw_trades": holdout_raw.get("filled_trade_count"),
            "guarded_trades": holdout_guarded.get("filled_trade_count"),
        },
        "guarded_holdout_positive": (
            guarded_holdout_net is not None and guarded_holdout_net > 0.0
        ),
        "guarded_holdout_beats_raw": (
            guarded_holdout_net is not None
            and raw_holdout_net is not None
            and guarded_holdout_net > raw_holdout_net
        ),
        "stress_and_monte_carlo_by_profile_split": {
            f"{profile_name}:{split_name}": {
                "stress": row.get("stress"),
                "monte_carlo": row.get("monte_carlo"),
            }
            for (profile_name, split_name), row in by_key.items()
        },
    }


def top_bucket(rows: list[dict[str, Any]], surface: str, bucket_type: str, limit: int = 12) -> list[dict[str, Any]]:
    selected = [
        row
        for row in rows
        if row["surface"] == surface and row["bucket_type"] == bucket_type
    ]
    selected.sort(key=lambda row: (safe_float(row.get("net_r")) or 0.0, row.get("rows") or 0))
    return selected[:limit]


def dossier(summary: Mapping[str, Any], diagnostics: Mapping[str, Any], all_bucket_rows: list[dict[str, Any]]) -> str:
    comparison = diagnostics["raw_vs_guarded"]
    holdout = comparison["holdout"]
    development = comparison["development"]
    trade_overall = [
        row for row in all_bucket_rows
        if row["surface"] == "trade" and row["bucket_type"] == "profile_split"
    ]
    order_guard = [
        row for row in all_bucket_rows
        if row["surface"] == "order" and row["bucket_type"] == "guard_status"
    ]
    worst_symbols = top_bucket(all_bucket_rows, "trade", "symbol")
    missed_overall = [
        row
        for row in all_bucket_rows
        if row["surface"] == "missed_opportunity"
        and row["bucket_type"] == "profile_split"
    ]
    lines = [
        "# Broad Live-As-If Replay Flow Diagnostic",
        "",
        f"Generated: {diagnostics['generated_at_utc']}",
        "",
        "Broker/live/final authority remains closed. All cash and R results are simulated replay outputs.",
        "",
        "## Raw vs Guarded",
        "",
        f"- Coverage: {summary.get('coverage_status')} ({summary.get('selected_day_count')} selected days of {summary.get('full_available_configured_day_count')} configured days).",
        f"- Development raw net R: {development.get('raw_net_r')} across {development.get('raw_trades')} trades.",
        f"- Development guarded net R: {development.get('guarded_net_r')} across {development.get('guarded_trades')} trades.",
        f"- Holdout raw net R: {holdout.get('raw_net_r')} across {holdout.get('raw_trades')} trades.",
        f"- Holdout guarded net R: {holdout.get('guarded_net_r')} across {holdout.get('guarded_trades')} trades.",
        f"- Holdout guarded-minus-raw delta R: {holdout.get('delta_guarded_minus_raw_net_r')}.",
        "",
        "## Trade Buckets",
        "",
    ]
    for row in trade_overall:
        lines.append(
            "- "
            f"{row['profile']} {row['split_or_segment']}: headline_trades={row['filled_count']} "
            f"win/loss/flat={row['win_count']}/{row['loss_count']}/{row['flat_count']} "
            f"headline_net_r={row['net_r']} cash_pnl={row['cash_pnl']} risk_cash={row['risk_cash']} "
            f"all_trade_rows={row.get('all_trade_rows')} all_trade_net_r={row.get('all_trade_net_r')} "
            f"diagnostic_only_rows={row.get('diagnostic_only_trade_rows')} "
            f"diagnostic_only_net_r={row.get('diagnostic_only_net_r')}"
        )
    lines.extend(["", "## Guard Blocks", ""])
    for row in order_guard:
        if row["profile"] == PROFILE_GUARDED:
            lines.append(
                "- "
                f"{row['split_or_segment']} {row['bucket_value']}: orders={row['rows']} "
                f"blocked={row['blocked_count']} scoreable_blocked={row['blocked_scoreable_count']} "
                f"blocked_net_r={row['blocked_counterfactual_net_r']} "
                f"blocked_w/l/f={row['blocked_win_count']}/{row['blocked_loss_count']}/{row['blocked_flat_count']}"
            )
    lines.extend(["", "## Missed Opportunities", ""])
    for row in missed_overall:
        lines.append(
            "- "
            f"{row['profile']} {row['split_or_segment']}: rows={row['rows']} "
            f"scoreable/unscoreable={row['missed_scoreable_count']}/{row['missed_unscoreable_count']} "
            f"all_scoreable_net_r={row['missed_net_r']} "
            f"executable_rows/net_r={row['missed_executable_scoreable_count']}/{row['missed_executable_net_r']} "
            f"diagnostic_rows/net_r={row['missed_diagnostic_scoreable_count']}/{row['missed_diagnostic_net_r']} "
            f"diagnostic_positive={row['missed_diagnostic_positive_count']}/{row['missed_diagnostic_positive_net_r']} "
            f"diagnostic_negative={row['missed_diagnostic_negative_count']}/{row['missed_diagnostic_negative_net_r']} "
            f"diagnostic_flat={row['missed_diagnostic_flat_count']}"
        )
    lines.extend(["", "## Worst Trade Buckets", ""])
    for row in worst_symbols:
        lines.append(
            "- "
            f"{row['profile']} {row['split_or_segment']} {row['bucket_value']}: "
            f"headline_trades={row['filled_count']} headline_net_r={row['net_r']} "
            f"all_trade_rows={row.get('all_trade_rows')} all_trade_net_r={row.get('all_trade_net_r')} "
            f"cash_pnl={row['cash_pnl']} w/l/f={row['win_count']}/{row['loss_count']}/{row['flat_count']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Guarded positivity is not accepted as proof unless holdout is positive and beats raw.",
            "- Date/symbol/session loss-bucket rules are labeled overfit risk until converted to causal pre-decision conditions.",
            "- Exact broker lifecycle and broker cash truth remain missing; this artifact is replay/proxy evidence only.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", default=PREFIX)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_paths(str(args.prefix or PREFIX))
    completed_summary = read_json(SUMMARY_PATH)
    collector = Collector()
    trade_source_rows: list[dict[str, Any]] = []
    for row in iter_jsonl(TRADE_PATH):
        collector.add_trade(row)
        trade_source_rows.append(row)
    for row in iter_jsonl(ORDER_PATH):
        collector.add_order(row)
    for row in candidate_flow_rows():
        collector.add_candidate(row)
    for row in iter_jsonl(DECISION_PATH):
        collector.add_decision(row)
    for row in iter_jsonl(SCORECARD_PATH):
        collector.add_scorecard(row)
    for row in iter_jsonl(MISSED_PATH):
        collector.add_missed(row)

    all_bucket_rows = [
        *bucket_rows("trade", collector.trade),
        *bucket_rows("order", collector.order),
        *bucket_rows("candidate", collector.candidate),
        *bucket_rows("decision", collector.decision),
        *bucket_rows("scorecard", collector.scorecard),
        *bucket_rows("missed_opportunity", collector.missed),
    ]
    bucket_row_count = write_jsonl(FLOW_BUCKET_PATH, all_bucket_rows)
    ledger_row_counts = dict(collector.row_counts)
    declared_row_counts = summary_declared_row_counts(completed_summary)
    flow_row_counts = dict(ledger_row_counts)
    if declared_row_counts:
        flow_row_counts.update(declared_row_counts)
    candidate_instance_projection = summarize_candidate_instance_parity_projection(
        CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH
    )
    diagnostics = {
        "schema": "gtos.final_moonshot.broad_live_as_if_replay.flow_diagnostic_summary.v1",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE.name,
        "output_prefix": PREFIX,
        "source_summary_path": str(SUMMARY_PATH),
        "coverage_status": completed_summary.get("coverage_status"),
        "selected_day_count": completed_summary.get("selected_day_count"),
        "full_available_configured_day_count": completed_summary.get(
            "full_available_configured_day_count"
        ),
        "profiles": completed_summary.get("profiles"),
        "date_start": completed_summary.get("date_start"),
        "date_end": completed_summary.get("date_end"),
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "raw_vs_guarded": comparison_digest(completed_summary),
        "guard_rule_shape": guard_rule_shape(completed_summary),
        "row_counts": flow_row_counts,
        "ledger_row_counts": ledger_row_counts,
        "summary_declared_row_counts": declared_row_counts,
        "row_counts_source": (
            "split_profile_stats_canonical_counts_with_ledger_diagnostics"
            if declared_row_counts
            else "ledger_row_counts"
        ),
        "bucket_row_count": bucket_row_count,
        "trade_overall": {
            "|".join(key): metric.as_dict()
            for key, metric in sorted(collector.trade.items())
            if key[0] in {"overall", "profile", "profile_split", "profile_segment"}
        },
        "order_guard_overall": {
            "|".join(key): metric.as_dict()
            for key, metric in sorted(collector.order.items())
            if key[0] in {"guard_status", "guard_rule_id", "profile_split", "profile_segment"}
        },
        "candidate_decision_overall": {
            "candidate": {
                "|".join(key): metric.as_dict()
                for key, metric in sorted(collector.candidate.items())
                if key[0] in {"profile_split", "profile_segment", "selector_action", "origin_family"}
            },
            "decision": {
                "|".join(key): metric.as_dict()
                for key, metric in sorted(collector.decision.items())
                if key[0] in {"profile_split", "profile_segment"}
            },
            "scorecard": {
                "|".join(key): metric.as_dict()
                for key, metric in sorted(collector.scorecard.items())
                if key[0] in {"profile_split", "profile_segment"}
            },
        },
        "missed_opportunity_overall": {
            "|".join(key): metric.as_dict()
            for key, metric in sorted(collector.missed.items())
            if key[0] in {"profile_split", "profile_segment", "miss_reason"}
        },
        "candidate_instance_parity_projection": candidate_instance_projection,
        "r_evidence_boundary": trade_r_evidence_boundary(trade_source_rows),
        "artifacts": {
            "flow_summary": str(FLOW_SUMMARY_PATH),
            "flow_bucket_ledger": str(FLOW_BUCKET_PATH),
            "flow_dossier": str(FLOW_DOSSIER_PATH),
            "candidate_instance_parity_projection_ledger": str(
                CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH
            ),
        },
    }
    atomic_write_json(FLOW_SUMMARY_PATH, diagnostics)
    atomic_write_text(FLOW_DOSSIER_PATH, dossier(completed_summary, diagnostics, all_bucket_rows))
    print(
        json.dumps(
            {
                "status": "broad_live_as_if_flow_diagnostic_written",
                "bucket_row_count": bucket_row_count,
                "candidate_instance_parity_projection_rows": (
                    candidate_instance_projection.get("row_count")
                ),
                "summary": str(FLOW_SUMMARY_PATH),
                "dossier": str(FLOW_DOSSIER_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
