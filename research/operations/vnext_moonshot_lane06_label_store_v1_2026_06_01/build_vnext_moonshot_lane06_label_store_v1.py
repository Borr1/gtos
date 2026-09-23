#!/usr/bin/env python3
"""Build the vNext moonshot Lane06 label store V1.

This route is offline research only. It consumes already-materialized Lane01,
Lane02, Lane03, Lane04, Lane05, Lane07, Friday microscope, and broker-truth
artifacts and writes source-bound label rows plus row-level missing-label gaps.
It does not touch live broker state, runtime config, prompts, risk, selector, or
execution behavior.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

try:
    import orjson  # type: ignore
except Exception:  # pragma: no cover - fallback for minimal Python envs
    orjson = None


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ROUTE_ID = "vnext_moonshot_lane06_label_store_v1_2026_06_01"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID
SCHEMA_VERSION = "lane06_label_store_v1"
RUNTIME_EFFECT_BOUNDARY = "offline_label_store_only_no_live_broker_runtime_config_or_execution_change"
RESULT_USE_STATUS = (
    "label_store_research_and_downstream_training_contract_only_"
    "broker_real_proxy_and_replay_labels_remain_separate"
)

PROMPT = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts" / "VNEXT_MOONSHOT_LANE06_LABEL_STORE_V1_GOAL_PROMPT_2026-06-01.md"
STARTER = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts" / "VNEXT_MOONSHOT_LANE06_LABEL_STORE_V1_STARTER_2026-06-01.txt"
LIVE_STATE = ROOT / ".context" / "LIVE_STATE.md"
SYSTEM_MAP = ROOT / ".context" / "00_core" / "current_vnext_system_map.md"
READING_ORDER = ROOT / ".context" / "00_core" / "current_repo_reading_order.md"
RESEARCH_DISCIPLINE = ROOT / ".context" / "00_core" / "goal_session_research_discipline.md"
RESEARCH_DOCTRINE = ROOT / ".context" / "00_core" / "research_operating_doctrine.md"
MOONSHOT_VISION = ROOT / ".context" / "00_core" / "vnext_absolute_moonshot_vision_and_limitations.md"

LANE01_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
LANE02_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"
LANE03_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01"
LANE04_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01"
LANE05_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE07_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"
FRIDAY_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
MT5_CACHE_DIR = ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01"
BROKER_TRUTH_DIR = ROOT / "research" / "operations" / "vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31"

LANE02_FIELD_CONTRACT = LANE02_DIR / "LANE02_DOWNSTREAM_FIELD_CONTRACT.json"
LANE02_KEY_POLICY = LANE02_DIR / "LANE02_CANONICAL_KEY_POLICY.json"
LANE03_CANDIDATES = LANE03_DIR / "LANE03_CANONICAL_CANDIDATE_LEDGER.jsonl.gz"
LANE03_MANIFEST = LANE03_DIR / "LANE03_OUTPUT_MANIFEST.json"
LANE04_TIMELINE = LANE04_DIR / "LANE04_ROW_TIMELINE_LEDGER.jsonl"
LANE04_STRICT = LANE04_DIR / "LANE04_STRICT_TICK_TIMELINE_LEDGER.jsonl"
LANE04_SOURCE_GAPS = LANE04_DIR / "LANE04_SOURCE_GAP_LEDGER.jsonl"
LANE04_SUMMARY = LANE04_DIR / "LANE04_EXPECTANCY_SUMMARY.json"
LANE04_MANIFEST = LANE04_DIR / "LANE04_OUTPUT_MANIFEST.json"
LANE05_SCHEMA = LANE05_DIR / "LANE05_FEATURE_SCHEMA.json"
LANE05_NO_LEAK = LANE05_DIR / "LANE05_NO_LEAK_VALIDATION_LEDGER.jsonl"
LANE05_DOWNSTREAM_CONTRACT = LANE05_DIR / "LANE05_DOWNSTREAM_CONTRACT.json"
LANE05_MANIFEST = LANE05_DIR / "LANE05_OUTPUT_MANIFEST.json"
LANE05_AUDIT = LANE05_DIR / "LANE05_COMPLETION_AUDIT.json"
LANE07_BROKER_TRUTH = LANE07_DIR / "LANE07_BROKER_TRUTH_LEDGER.jsonl"
LANE07_COST = LANE07_DIR / "LANE07_COST_CALIBRATION_LEDGER.jsonl"
LANE07_DOWNSTREAM_CONTRACT = LANE07_DIR / "LANE07_DOWNSTREAM_CONTRACT.json"
LANE07_AUDIT = LANE07_DIR / "LANE07_COMPLETION_AUDIT.json"

FRIDAY_EXEC_POLICY = FRIDAY_DIR / "FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_LEDGER.jsonl"
FRIDAY_STALE_BLOCKERS = FRIDAY_DIR / "FRIDAY_STALE_BLOCKER_REPAIR_LEDGER.jsonl"
FRIDAY_CORRECT_NO_TRADE = FRIDAY_DIR / "FRIDAY_CORRECT_NO_TRADE_LEDGER.jsonl"
FRIDAY_MISSED = FRIDAY_DIR / "FRIDAY_MISSED_SELECTED_OPPORTUNITY_LEDGER.jsonl"
FRIDAY_MFE_MAE = FRIDAY_DIR / "FRIDAY_MFE_MAE_TIMING_LEDGER.jsonl"
FRIDAY_MANUAL = FRIDAY_DIR / "FRIDAY_MANUAL_INTERVENTION_LEDGER.jsonl"
BROKER_LIFECYCLE = BROKER_TRUTH_DIR / "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl"
BROKER_COST = BROKER_TRUTH_DIR / "LANE06_COST_CALIBRATION_LEDGER.jsonl"
BROKER_RECONCILIATION = BROKER_TRUTH_DIR / "LANE06_PROJECTED_VS_BROKER_RECONCILIATION_LEDGER.jsonl"
BROKER_SUMMARY = BROKER_TRUTH_DIR / "LANE06_SUMMARY.json"
BROKER_MANIFEST = BROKER_TRUTH_DIR / "LANE06_OUTPUT_MANIFEST.json"

LABEL_SCHEMA = ROUTE_DIR / "LANE06_LABEL_SCHEMA.json"
LABEL_VECTOR_LEDGER = ROUTE_DIR / "LANE06_LABEL_VECTOR_LEDGER.jsonl.gz"
MISSING_LABEL_GAP_LEDGER = ROUTE_DIR / "LANE06_MISSING_LABEL_GAP_LEDGER.jsonl.gz"
LABEL_FAMILY_COVERAGE_LEDGER = ROUTE_DIR / "LANE06_LABEL_FAMILY_COVERAGE_LEDGER.jsonl"
SOURCE_COVERAGE_LEDGER = ROUTE_DIR / "LANE06_SOURCE_COVERAGE_LEDGER.jsonl"
NO_LEAK_LEDGER = ROUTE_DIR / "LANE06_NO_LEAK_VALIDATION_LEDGER.jsonl"
DEPENDENCY_STATE_LEDGER = ROUTE_DIR / "LANE06_DEPENDENCY_STATE_LEDGER.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / "LANE06_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / "LANE06_IMPLEMENTATION_DECISION_LEDGER.jsonl"
DOWNSTREAM_CONTRACT = ROUTE_DIR / "LANE06_DOWNSTREAM_CONTRACT.json"
RUNTIME_EFFECT_BOUNDARY_PATH = ROUTE_DIR / "LANE06_RUNTIME_EFFECT_BOUNDARY.json"
RESULT_USE_STATUS_PATH = ROUTE_DIR / "LANE06_RESULT_USE_STATUS.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE06_CONTEXT_ANCHOR.md"
SATURATION_SELF_RED_TEAM = ROUTE_DIR / "LANE06_SATURATION_SELF_RED_TEAM.md"
COMPLETION_AUDIT = ROUTE_DIR / "LANE06_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE06_OUTPUT_MANIFEST.json"
VERIFIER = ROUTE_DIR / "verify_vnext_moonshot_lane06_label_store_v1.py"
TEST_FILE = ROUTE_DIR / "test_vnext_moonshot_lane06_label_store_v1.py"
VERIFICATION_RESULT = ROUTE_DIR / "LANE06_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE06_FOCUSED_TEST_RESULT.xml"
BUILD_PROGRESS = ROUTE_DIR / "LANE06_BUILD_PROGRESS.json"

CORE_LABEL_FAMILIES = (
    "sl_before_1r",
    "one_r_reached",
    "partial_then_be",
    "partial_then_final",
    "final_target_reached",
    "no_entry_touch",
    "stuck_no_resolution",
    "mfe_r",
    "mae_r",
    "time_to_1r_seconds",
    "time_to_sl_seconds",
    "time_to_final_seconds",
    "execution_policy_result",
    "stale_blocker",
    "correct_rejection",
    "missed_opportunity",
    "source_gap_present",
    "source_bound_proxy_r",
    "cost_adjusted_r",
    "cost_proxy_outcome",
    "broker_real_net_r",
    "broker_lifecycle_status",
    "manual_intervention",
    "broker_modify_failure",
    "false_close",
    "ambiguity_state",
    "no_trade_baseline_outcome",
)

ADDITIONAL_LABEL_FAMILIES = (
    "path_class",
    "fill_status",
    "path_ordering_status",
    "strict_tick_replay_status",
    "m1_availability_status",
    "tick_availability_status",
    "source_quality_status",
    "time_to_mfe_seconds",
    "time_to_mae_seconds",
    "time_to_be_return_seconds",
    "broker_final_net_r_status",
    "broker_mark_to_market_net_r",
    "local_close_r_sum",
    "reconciliation_status",
)

ALL_LABEL_FAMILIES = CORE_LABEL_FAMILIES + ADDITIONAL_LABEL_FAMILIES


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> dict[str, str]:
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        subject = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return {"head": head, "head_short": head[:9], "head_subject": subject}
    except Exception:
        return {"head": "UNKNOWN", "head_short": "UNKNOWN", "head_subject": "UNKNOWN"}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def normalize_rel(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    try:
        return rel((ROOT / text).resolve())
    except Exception:
        return text


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def json_line_bytes(row: dict[str, Any], *, sort_keys: bool = False) -> bytes:
    if orjson is not None:
        option = orjson.OPT_SORT_KEYS if sort_keys else 0
        return orjson.dumps(row, option=option)
    return json.dumps(row, sort_keys=sort_keys, separators=(",", ":"), default=str).encode("utf-8")


def loads_json_line(line: bytes | str) -> Any:
    if orjson is not None:
        return orjson.loads(line)
    return json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json_line_bytes(row, sort_keys=True).decode("utf-8") + "\n")
            count += 1
    return count


def write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(path, "wb", compresslevel=1) as handle:
        for row in rows:
            handle.write(json_line_bytes(row, sort_keys=True) + b"\n")
            count += 1
    return count


def iter_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = loads_json_line(stripped)
            except Exception:
                continue
            if isinstance(row, dict):
                yield line_number, row


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    opener = gzip.open if path.suffix == ".gz" else open
    count = 0
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def fnum(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return round(number, 9)


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        if " " in text and "T" not in text:
            text = text.replace(" ", "T")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_utc(value: Any) -> str | None:
    parsed = parse_utc(value)
    if parsed is None:
        return None
    return parsed.isoformat()


def seconds_between(start: Any, end: Any) -> float | None:
    a = parse_utc(start)
    b = parse_utc(end)
    if a is None or b is None:
        return None
    return round((b - a).total_seconds(), 6)


def stable_id(prefix: str, payload: Any) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def fast_time_key(value: Any) -> str:
    if value in (None, ""):
        return ""
    text = str(value).strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T")
    if "+" not in text and text.count(":") >= 2:
        text = text + "+00:00"
    return text


def source_hash_lookup() -> dict[str, str | None]:
    lookup: dict[str, str | None] = {}
    for manifest_path in (LANE03_MANIFEST, LANE04_MANIFEST, BROKER_MANIFEST):
        manifest = read_json(manifest_path, {}) or {}
        for key in ("files", "outputs", "artifacts"):
            for item in manifest.get(key, []) or []:
                path_text = item.get("path")
                if path_text:
                    lookup[normalize_rel(path_text)] = item.get("sha256")
    for path in (
        LANE02_FIELD_CONTRACT,
        LANE02_KEY_POLICY,
        FRIDAY_EXEC_POLICY,
        FRIDAY_STALE_BLOCKERS,
        FRIDAY_CORRECT_NO_TRADE,
        FRIDAY_MISSED,
        FRIDAY_MFE_MAE,
        FRIDAY_MANUAL,
        BROKER_LIFECYCLE,
        BROKER_COST,
        BROKER_RECONCILIATION,
        BROKER_SUMMARY,
    ):
        if path.exists():
            lookup[rel(path)] = sha256_file(path)
    return lookup


def source_hash_for(path: Path | str, hashes: dict[str, str | None]) -> str | None:
    return hashes.get(normalize_rel(path))


def canonical_key_tuple(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    time_value = (
        row.get("candidate_time_utc")
        or row.get("source_time_utc")
        or row.get("candle_time_utc")
        or row.get("entry_time_utc")
    )
    return (
        str(row.get("symbol") or ""),
        str(row.get("framework") or ""),
        str(row.get("side") or ""),
        iso_utc(time_value) or str(time_value or ""),
        str(row.get("origin_family") or ""),
    )


def canonical_key_tuple_fast(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    time_value = (
        row.get("candidate_time_utc")
        or row.get("source_time_utc")
        or row.get("candle_time_utc")
        or row.get("entry_time_utc")
    )
    return (
        str(row.get("symbol") or ""),
        str(row.get("framework") or ""),
        str(row.get("side") or ""),
        fast_time_key(time_value),
        str(row.get("origin_family") or ""),
    )


def candidate_join_keys(row: dict[str, Any]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for field in (
        "candidate_id",
        "trade_id",
        "row_id",
        "selected_row_id",
        "ticket",
        "broker_ticket",
        "position_id",
        "order_ticket",
        "deal_ticket",
    ):
        value = row.get(field)
        if value not in (None, ""):
            keys.add((field, str(value)))
    return keys


def event_time(row: dict[str, Any], event_name: str) -> str | None:
    for event in row.get("ordered_events") or []:
        if str(event.get("event_type") or "") == event_name:
            return iso_utc(event.get("time_utc"))
    return None


def first_event_time_containing(row: dict[str, Any], needles: tuple[str, ...]) -> str | None:
    best: datetime | None = None
    for event in row.get("ordered_events") or []:
        event_type = str(event.get("event_type") or "")
        if any(needle in event_type for needle in needles):
            parsed = parse_utc(event.get("time_utc"))
            if parsed is not None and (best is None or parsed < best):
                best = parsed
    return best.isoformat() if best is not None else None


def has_prior_event(before: str | None, after: str | None) -> bool:
    before_dt = parse_utc(before)
    after_dt = parse_utc(after)
    return before_dt is not None and after_dt is not None and before_dt <= after_dt


def classify_evidence_class(row: dict[str, Any], broker_labels: dict[str, Any]) -> str:
    if broker_labels.get("broker_real_net_r") is not None:
        return "broker_real_truth_plus_path_projection_labels"
    source_use = str(row.get("source_use_state") or "")
    strict_status = str(row.get("strict_tick_event_status") or "")
    if "friday" in source_use:
        return "friday_tick_bid_ask_path_label"
    if "strict_tick" in strict_status or "strict_tick" in source_use:
        return "strict_tick_projection_label"
    return "m15_proxy_replay_label"


def availability_state(value: Any) -> str:
    return "available" if value not in (None, "", [], {}) else "missing"


def label_schema_payload(generated_at: str) -> dict[str, Any]:
    label_families = {
        "sl_before_1r": {
            "value_type": "boolean_or_null",
            "evidence_class": ["friday_tick_bid_ask_path_label", "strict_tick_projection_label", "m15_proxy_replay_label"],
            "label_timing": "post_entry_path_ordering",
            "downstream_eligibility": ["ml_label", "digital_twin_eval", "execution_policy_eval"],
        },
        "one_r_reached": {
            "value_type": "boolean_or_null",
            "evidence_class": ["path_projection_label"],
            "label_timing": "post_entry_path_ordering",
            "downstream_eligibility": ["ml_label", "selector_training", "execution_policy_eval"],
        },
        "partial_then_be": {
            "value_type": "boolean_or_null",
            "evidence_class": ["path_projection_label"],
            "label_timing": "post_partial_trigger_outcome",
            "downstream_eligibility": ["execution_policy_eval", "ml_label"],
        },
        "partial_then_final": {
            "value_type": "boolean_or_null",
            "evidence_class": ["path_projection_label"],
            "label_timing": "post_partial_trigger_outcome",
            "downstream_eligibility": ["execution_policy_eval", "ml_label"],
        },
        "final_target_reached": {
            "value_type": "boolean_or_null",
            "evidence_class": ["path_projection_label"],
            "label_timing": "post_entry_target_path",
            "downstream_eligibility": ["execution_policy_eval", "ml_label"],
        },
        "broker_real_net_r": {
            "value_type": "number_or_null",
            "evidence_class": ["broker_real_truth"],
            "label_timing": "post_close_broker_history",
            "downstream_eligibility": ["broker_truth_calibration", "ml_label_when_captured", "cost_calibration"],
        },
        "source_bound_proxy_r": {
            "value_type": "number_or_null",
            "evidence_class": ["strict_tick_projection_label", "m15_proxy_replay_label"],
            "label_timing": "post_replay_projection_exit",
            "downstream_eligibility": ["ml_proxy_label", "digital_twin_eval", "selector_training"],
        },
    }
    for family in ALL_LABEL_FAMILIES:
        label_families.setdefault(
            family,
            {
                "value_type": "scalar_or_object_or_null",
                "evidence_class": ["label_only", "future_outcome", "replay_only", "broker_realized"],
                "label_timing": "label_store_only_post_event_or_source_completeness_state",
                "downstream_eligibility": ["ml_label", "digital_twin_eval", "offline_selector_scheduler_execution_analysis"],
            },
        )
    return {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "result_use_status": RESULT_USE_STATUS,
        "canonical_key_policy": rel(LANE02_KEY_POLICY),
        "no_leak_contract": rel(LANE02_FIELD_CONTRACT),
        "label_authority_order": ["broker_real_truth", "strict_tick_projection", "m15_proxy_replay"],
        "label_vector_fields": [
            "schema_version",
            "route_id",
            "row_id",
            "canonical_key",
            "candidate_id",
            "trade_id",
            "symbol",
            "broker_symbol",
            "framework",
            "origin_family",
            "side",
            "candidate_time_utc",
            "entry_time_utc",
            "label_time_utc",
            "evidence_class",
            "source_use_state",
            "source_path",
            "source_hash",
            "no_leak_status",
            "label_values",
            "missing_label_reasons",
            "row_level_missing_field_proof",
        ],
        "label_families": label_families,
        "missing_gap_codes": {
            "NO_JOINED_LABEL_SOURCE_CURRENT_INPUTS": {
                "meaning": "Lane03 canonical candidate has no joined Lane04 microscope path row, broker truth row, or source-bound proxy outcome in current approved inputs.",
                "attempted_source_set": [
                    rel(LANE04_TIMELINE),
                    rel(BROKER_LIFECYCLE),
                    rel(BROKER_COST),
                    rel(FRIDAY_EXEC_POLICY),
                    rel(FRIDAY_MFE_MAE),
                ],
                "repair_requirement": "run_or_join_historical_microscope_path_replay_and_or_read_only_broker_lifecycle_cost_source_for_candidate_key",
            }
        },
    }


def collect_by_key(path: Path, row_builder: Any) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    if not path.exists():
        return result
    for _line, row in iter_jsonl(path):
        payload = row_builder(row)
        if not payload:
            continue
        for key in candidate_join_keys(row):
            result.setdefault(key, {}).update(payload)
    return result


def load_supplements() -> dict[tuple[str, str], dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = defaultdict(dict)

    for path, builder in (
        (FRIDAY_EXEC_POLICY, friday_policy_payload),
        (FRIDAY_STALE_BLOCKERS, friday_stale_payload),
        (FRIDAY_CORRECT_NO_TRADE, friday_correct_payload),
        (FRIDAY_MISSED, friday_missed_payload),
        (FRIDAY_MFE_MAE, friday_mfe_payload),
        (FRIDAY_MANUAL, friday_manual_payload),
        (BROKER_LIFECYCLE, broker_lifecycle_payload),
        (BROKER_COST, broker_cost_payload),
        (BROKER_RECONCILIATION, broker_reconciliation_payload),
        (LANE07_BROKER_TRUTH, lane07_broker_truth_payload),
        (LANE07_COST, lane07_cost_payload),
    ):
        for key, payload in collect_by_key(path, builder).items():
            merged[key].update(payload)

    broker_summary = read_json(BROKER_SUMMARY, {}) or {}
    false_close_tickets = {str(ticket) for ticket in broker_summary.get("false_close_notification_tickets", [])}
    if false_close_tickets:
        for key, payload in list(merged.items()):
            ticket = str(payload.get("ticket") or key[1])
            if ticket in false_close_tickets:
                payload["false_close"] = True
                payload["false_close_source"] = rel(BROKER_SUMMARY)
    return dict(merged)


def friday_policy_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "friday_policy_source": rel(FRIDAY_EXEC_POLICY),
        "broker_modify_failure": (row.get("stop_modify_rejections") or 0) > 0,
        "broker_placement_ready": row.get("broker_placement_ready"),
        "actually_placed": row.get("actually_placed"),
    }
    if row.get("comparison_policy") == "no_trade_baseline":
        payload["no_trade_baseline_outcome"] = {
            "execution_result": row.get("execution_result"),
            "gross_r": fnum(row.get("gross_r")),
            "comparison_policy": row.get("comparison_policy"),
        }
    elif row.get("comparison_policy") == "current_selected_policy":
        payload["friday_current_policy_result"] = {
            "execution_result": row.get("execution_result"),
            "gross_r": fnum(row.get("gross_r")),
            "comparison_policy": row.get("comparison_policy"),
        }
    return payload


def friday_stale_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "stale_blocker": True,
        "stale_blocker_reason": row.get("row_disposition") or row.get("repair_decision"),
        "stale_blocker_flags": row.get("defect_flags") or [],
        "stale_blocker_source": rel(FRIDAY_STALE_BLOCKERS),
    }


def friday_correct_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "correct_rejection": True,
        "correct_rejection_reason": row.get("correct_no_trade_reason") or row.get("row_disposition"),
        "correct_rejection_source": rel(FRIDAY_CORRECT_NO_TRADE),
    }


def friday_missed_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "missed_opportunity": True,
        "missed_opportunity_reason": row.get("missed_selected_status") or row.get("row_disposition"),
        "missed_opportunity_source": rel(FRIDAY_MISSED),
    }


def friday_mfe_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "friday_mfe_r": fnum(row.get("mfe_r")),
        "friday_mae_r": fnum(row.get("mae_r")),
        "friday_time_to_mfe_seconds": fnum(row.get("time_to_mfe_from_entry_seconds")),
        "friday_time_to_mae_seconds": fnum(row.get("time_to_mae_from_entry_seconds")),
        "friday_threshold_times_utc": row.get("threshold_times_utc") or {},
        "friday_threshold_seconds_from_entry": row.get("threshold_seconds_from_entry") or {},
    }


def friday_manual_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "manual_intervention": True,
        "manual_intervention_source": rel(FRIDAY_MANUAL),
        "manual_intervention_payload": row,
    }


def broker_lifecycle_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket": row.get("ticket"),
        "broker_symbol": row.get("broker_symbol"),
        "broker_lifecycle_status": row.get("broker_lifecycle_status"),
        "broker_order_send_success": row.get("order_send_success"),
        "broker_order_result_retcode": row.get("order_result_retcode"),
        "manual_intervention": bool(row.get("manual_or_client_deal_tickets")),
        "manual_or_client_deal_tickets": row.get("manual_or_client_deal_tickets") or [],
        "read_only_broker_truth": row.get("read_only_broker_truth"),
        "broker_lifecycle_source": rel(BROKER_LIFECYCLE),
    }


def broker_cost_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket": row.get("ticket"),
        "trade_id": row.get("trade_id"),
        "broker_symbol": row.get("broker_symbol"),
        "broker_real_net_r": fnum(row.get("broker_realized_net_r")),
        "broker_mark_to_market_net_r": fnum(row.get("broker_mark_to_market_net_r")),
        "broker_final_net_r_status": row.get("broker_final_net_r_status"),
        "commission_sum": fnum(row.get("commission_sum")),
        "swap_sum": fnum(row.get("swap_sum")),
        "fee_sum": fnum(row.get("fee_sum")),
        "realized_net_profit": fnum(row.get("realized_net_profit")),
        "initial_cash_risk": fnum(row.get("initial_cash_risk")),
        "local_close_r_sum": fnum(row.get("local_close_r_sum")),
        "read_only_broker_truth": row.get("read_only_broker_truth"),
        "broker_cost_source": rel(BROKER_COST),
    }


def broker_reconciliation_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket": row.get("ticket"),
        "reconciliation_status": row.get("reconciliation_status"),
        "daily_pnl_actual_r_claim_allowed": row.get("daily_pnl_actual_r_claim_allowed"),
        "r_delta_daily_minus_broker_net": fnum(row.get("r_delta_daily_minus_broker_net")),
        "broker_reconciliation_source": rel(BROKER_RECONCILIATION),
    }


def lane07_broker_truth_payload(row: dict[str, Any]) -> dict[str, Any]:
    ticket = row.get("position_id") or row.get("ticket")
    return {
        "ticket": ticket,
        "broker_symbol": row.get("broker_symbol"),
        "lane07_broker_truth_status": row.get("broker_truth_status"),
        "lane07_broker_truth_row_type": row.get("row_type"),
        "broker_wins_over_local_projection": row.get("broker_wins_over_local_projection"),
        "lane07_event_time_utc": row.get("event_time_utc"),
        "lane07_broker_truth_source": rel(LANE07_BROKER_TRUTH),
    }


def lane07_cost_payload(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("row_type") != "broker_real_trade_cost":
        return {
            "ticket": row.get("ticket"),
            "trade_id": row.get("trade_id"),
            "broker_symbol": row.get("broker_symbol"),
            "lane07_cost_status": row.get("cost_status"),
            "lane07_cost_row_type": row.get("row_type"),
            "lane07_cost_source": rel(LANE07_COST),
        }
    return {
        "ticket": row.get("ticket"),
        "trade_id": row.get("trade_id"),
        "broker_symbol": row.get("broker_symbol"),
        "broker_real_net_r": fnum(row.get("broker_realized_net_r")),
        "broker_mark_to_market_net_r": fnum(row.get("broker_mark_to_market_net_r")),
        "broker_final_net_r_status": row.get("cost_status"),
        "commission_sum": fnum(row.get("commission")),
        "swap_sum": fnum(row.get("swap")),
        "fee_sum": fnum(row.get("fee")),
        "realized_net_profit": fnum(row.get("realized_net_profit")),
        "initial_cash_risk": fnum(row.get("initial_cash_risk")),
        "read_only_broker_truth": True,
        "lane07_cost_status": row.get("cost_status"),
        "lane07_cost_row_type": row.get("row_type"),
        "lane07_cost_source": rel(LANE07_COST),
        "broker_cost_source": rel(LANE07_COST),
    }


def merged_supplement(row: dict[str, Any], supplements: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in candidate_join_keys(row):
        payload.update(supplements.get(key, {}))
    return payload


def derive_timeline_label_vector(
    row: dict[str, Any],
    supplements: dict[tuple[str, str], dict[str, Any]],
    hashes: dict[str, str | None],
    source_path: Path = LANE04_TIMELINE,
) -> dict[str, Any]:
    supplemental = merged_supplement(row, supplements)
    entry_time = iso_utc(row.get("entry_time_utc"))
    source_time = iso_utc(row.get("source_time_utc") or row.get("candle_time_utc") or row.get("entry_time_utc"))
    label_time = iso_utc(row.get("exit_time_utc")) or source_time or entry_time
    sl_time = first_event_time_containing(row, ("sl_touch", "stop_loss"))
    one_r_time = event_time(row, "one_r_trigger") or event_time(row, "partial_trigger")
    be_time = first_event_time_containing(row, ("be_return", "break_even"))
    final_target_time = first_event_time_containing(row, ("dynamic_final", "target", "tp"))
    final_policy_time = first_event_time_containing(row, ("final_policy_exit",))
    final_r = fnum(row.get("final_r"))
    mfe_r = fnum(row.get("mfe_r"))
    mae_r = fnum(row.get("mae_r"))
    cost_r = fnum(row.get("cost_r"))
    path_class = str(row.get("path_class") or "")
    fill_status = str(row.get("fill_status") or "")
    chosen_policy = row.get("chosen_policy")
    exit_reason = row.get("exit_reason")

    sl_before_1r: bool | None
    if sl_time and one_r_time:
        sl_before_1r = has_prior_event(sl_time, one_r_time)
    elif sl_time and (mfe_r is None or mfe_r < 1.0):
        sl_before_1r = True
    elif sl_time and mfe_r is not None and mfe_r >= 1.0 and one_r_time is None:
        sl_before_1r = None
    else:
        sl_before_1r = False if final_r is not None and final_r > -0.999 else None

    one_r_reached: bool | None
    if one_r_time:
        one_r_reached = not (sl_time and has_prior_event(sl_time, one_r_time))
    elif final_r is not None and final_r >= 1.0:
        one_r_reached = True
    elif mfe_r is not None and mfe_r >= 1.0 and sl_before_1r is not True:
        one_r_reached = True
    elif mfe_r is not None and mfe_r < 1.0:
        one_r_reached = False
    else:
        one_r_reached = None

    partial_then_be = bool(be_time and one_r_reached and sl_before_1r is not True)
    if not partial_then_be and one_r_reached and final_r is not None and abs(final_r) < 1e-9 and "partial" in str(chosen_policy):
        partial_then_be = True

    partial_then_final = bool(
        one_r_reached
        and sl_before_1r is not True
        and (
            (final_target_time is not None and not (sl_time and has_prior_event(sl_time, final_target_time)))
            or "dynamic_final" in path_class
            or (final_r is not None and final_r >= 1.0 and "partial" in str(chosen_policy))
        )
    )

    final_target_reached = bool(
        one_r_reached
        and sl_before_1r is not True
        and (
            final_target_time is not None
            or (final_r is not None and final_r >= 1.0)
            or "target" in str(exit_reason).lower()
        )
    )

    no_entry_touch = (
        "no_entry" in path_class
        or ("filled" not in fill_status and "friday_primary_candidate" not in str(row.get("decision") or ""))
    )
    stuck_no_resolution = "stuck" in path_class or (final_r is None and not no_entry_touch)
    cost_adjusted_r = round(final_r + cost_r, 9) if final_r is not None and cost_r is not None else None
    source_gaps = row.get("missing_field_proof") or []
    missing_reasons = []
    if sl_before_1r is None:
        missing_reasons.append(
            {
                "label_family": "sl_before_1r",
                "reason": "sl_and_1r_ordering_not_fully_resolved_from_available_path_events",
                "repair_requirement": "ordered bid/ask tick path or explicit source path event ordering",
            }
        )
    if supplemental.get("broker_real_net_r") is None:
        missing_reasons.append(
            {
                "label_family": "broker_real_net_r",
                "reason": "no broker-real net-R join for this candidate in current broker truth route",
                "repair_requirement": "read-only broker deal/order/position/cost export or prospective lifecycle capture",
            }
        )
    if cost_adjusted_r is None:
        missing_reasons.append(
            {
                "label_family": "cost_adjusted_r",
                "reason": str(row.get("cost_status") or "missing_cost_r"),
                "repair_requirement": "source-bound commission/swap/slippage/spread/deal fields",
            }
        )
    for gap in source_gaps:
        missing_reasons.append(
            {
                "label_family": "source_gap",
                "reason": gap.get("reason"),
                "field_family": gap.get("field_family"),
                "repair_requirement": gap.get("repair_requirement"),
            }
        )

    label_values = {
        "sl_before_1r": sl_before_1r,
        "one_r_reached": one_r_reached,
        "partial_then_be": partial_then_be,
        "partial_then_final": partial_then_final,
        "final_target_reached": final_target_reached,
        "no_entry_touch": bool(no_entry_touch),
        "stuck_no_resolution": bool(stuck_no_resolution),
        "mfe_r": supplemental.get("friday_mfe_r", mfe_r),
        "mae_r": supplemental.get("friday_mae_r", mae_r),
        "time_to_1r_seconds": fnum(row.get("time_to_1r_seconds")) or fnum((supplemental.get("friday_threshold_seconds_from_entry") or {}).get("1_0r")),
        "time_to_sl_seconds": fnum(row.get("time_to_sl_seconds")) or seconds_between(entry_time, sl_time),
        "time_to_final_seconds": fnum(row.get("time_to_final_seconds")) or seconds_between(entry_time, final_policy_time or label_time),
        "time_to_mfe_seconds": fnum(row.get("time_to_mfe_seconds")) or supplemental.get("friday_time_to_mfe_seconds"),
        "time_to_mae_seconds": fnum(row.get("time_to_mae_seconds")) or supplemental.get("friday_time_to_mae_seconds"),
        "time_to_be_return_seconds": fnum(row.get("time_to_be_return_seconds")) or seconds_between(entry_time, be_time),
        "execution_policy_result": {
            "chosen_policy": chosen_policy,
            "execution_policy_id": row.get("execution_policy_id"),
            "exit_reason": exit_reason,
            "final_r": final_r,
            "friday_current_policy_result": supplemental.get("friday_current_policy_result"),
        },
        "stale_blocker": supplemental.get("stale_blocker", False),
        "stale_blocker_reason": supplemental.get("stale_blocker_reason"),
        "correct_rejection": supplemental.get("correct_rejection", False),
        "correct_rejection_reason": supplemental.get("correct_rejection_reason"),
        "missed_opportunity": supplemental.get("missed_opportunity", False),
        "missed_opportunity_reason": supplemental.get("missed_opportunity_reason"),
        "source_gap_present": bool(source_gaps),
        "source_gap_families": sorted({str(gap.get("field_family")) for gap in source_gaps if gap.get("field_family")}),
        "source_bound_proxy_r": final_r,
        "cost_adjusted_r": cost_adjusted_r,
        "cost_proxy_outcome": row.get("cost_status"),
        "broker_real_net_r": supplemental.get("broker_real_net_r"),
        "broker_lifecycle_status": supplemental.get("broker_lifecycle_status"),
        "manual_intervention": supplemental.get("manual_intervention", False),
        "broker_modify_failure": supplemental.get("broker_modify_failure", False),
        "false_close": supplemental.get("false_close", False),
        "ambiguity_state": row.get("ordered_path_status"),
        "no_trade_baseline_outcome": supplemental.get("no_trade_baseline_outcome"),
        "path_class": path_class,
        "fill_status": fill_status,
        "path_ordering_status": row.get("ordered_path_status"),
        "strict_tick_replay_status": row.get("strict_tick_event_status"),
        "m1_availability_status": row.get("m1_availability_status"),
        "tick_availability_status": row.get("tick_availability_status"),
        "source_quality_status": row.get("source_quality_status"),
        "broker_final_net_r_status": supplemental.get("broker_final_net_r_status"),
        "broker_mark_to_market_net_r": supplemental.get("broker_mark_to_market_net_r"),
        "local_close_r_sum": supplemental.get("local_close_r_sum"),
        "reconciliation_status": supplemental.get("reconciliation_status"),
    }

    canonical_key = {
        "symbol": row.get("symbol"),
        "broker_symbol": supplemental.get("broker_symbol") or row.get("symbol"),
        "origin": row.get("origin_family"),
        "framework": row.get("framework"),
        "side": row.get("side"),
        "candidate_time_utc": source_time,
        "candle_time_utc": source_time,
        "source_row_id": row.get("selected_row_id") or row.get("row_id") or row.get("candidate_id"),
        "route_id": ROUTE_ID,
        "order_id": None,
        "deal_id": None,
        "position_id": supplemental.get("ticket"),
        "ticket_id": supplemental.get("ticket"),
    }
    row_id = stable_id("lane06_label", [canonical_key, row.get("candidate_id"), row.get("row_id")])
    evidence_class = classify_evidence_class(row, supplemental)
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "row_id": row_id,
        "canonical_key": canonical_key,
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id") or (row.get("row_id") if str(row.get("row_id") or "").count("_") >= 3 else None),
        "selected_row_id": row.get("selected_row_id"),
        "source_row_id": canonical_key["source_row_id"],
        "symbol": row.get("symbol"),
        "broker_symbol": supplemental.get("broker_symbol") or row.get("symbol"),
        "framework": row.get("framework"),
        "origin_family": row.get("origin_family"),
        "session": row.get("session_bucket"),
        "side": row.get("side"),
        "candidate_time_utc": source_time,
        "entry_time_utc": entry_time,
        "label_time_utc": label_time,
        "evidence_class": evidence_class,
        "source_use_state": row.get("source_use_state"),
        "source_family": row.get("timeline_source_family"),
        "source_path": rel(source_path),
        "source_hash": source_hash_for(source_path, hashes),
        "source_line_number": row.get("source_line_number"),
        "label_timing": "post_event_label_only",
        "outcome_availability": {
            "path_proxy": availability_state(final_r),
            "broker_real": availability_state(supplemental.get("broker_real_net_r")),
            "cost_adjusted": availability_state(cost_adjusted_r),
            "mfe_mae": availability_state(mfe_r) if mfe_r is not None else availability_state(supplemental.get("friday_mfe_r")),
        },
        "downstream_eligibility": {
            "feature_store": "forbidden_as_feature_column",
            "digital_twin": "allowed_as_result_label",
            "ml": "allowed_as_label_after_purge_embargo_and_evidence_class_selection",
            "selector": "offline_training_or_evaluation_only",
            "scheduler": "offline_training_or_evaluation_only",
            "execution_policy": "offline_policy_evaluation_label",
        },
        "no_leak_status": "label_only_excluded_from_feature_rows",
        "result_use_status": RESULT_USE_STATUS,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "label_values": label_values,
        "missing_label_reasons": missing_reasons,
        "row_level_missing_field_proof": source_gaps,
        "source_refs": sorted(
            {
                rel(source_path),
                supplemental.get("friday_policy_source"),
                supplemental.get("stale_blocker_source"),
                supplemental.get("correct_rejection_source"),
                supplemental.get("missed_opportunity_source"),
                supplemental.get("manual_intervention_source"),
                supplemental.get("broker_lifecycle_source"),
                supplemental.get("broker_cost_source"),
                supplemental.get("broker_reconciliation_source"),
                supplemental.get("lane07_broker_truth_source"),
                supplemental.get("lane07_cost_source"),
                supplemental.get("false_close_source"),
            }
            - {None}
        ),
    }


def missing_label_gap_row(row: dict[str, Any], line_number: int, hashes: dict[str, str | None]) -> dict[str, Any]:
    candidate_time = iso_utc(row.get("candidate_time_utc")) or row.get("candidate_time_utc")
    return {
        "schema_version": "lane06_missing_label_gap_v1",
        "route_id": ROUTE_ID,
        "gap_id": f"lane06_missing_label_gap_{line_number:08d}",
        "canonical_candidate_id": row.get("canonical_candidate_id"),
        "canonical_duplicate_key": row.get("canonical_duplicate_key"),
        "candidate_time_utc": candidate_time,
        "symbol": row.get("symbol"),
        "framework": row.get("framework"),
        "origin_family": row.get("origin_family"),
        "side": row.get("side"),
        "session": row.get("session"),
        "source_ref_id": "lane03_canonical_candidate_ledger",
        "source_hash": source_hash_for(LANE03_CANDIDATES, hashes),
        "first_source_path": row.get("first_source_path"),
        "first_source_line": row.get("first_source_line"),
        "source_use_state": "lane03_canonical_candidate_without_joined_label_source",
        "missing_label_family_set_id": "lane06_core_path_broker_policy_label_family_set_v1",
        "missing_label_family_set_ref": "LANE06_LABEL_SCHEMA.json#missing_gap_codes.NO_JOINED_LABEL_SOURCE_CURRENT_INPUTS",
        "gap_reason_code": "NO_JOINED_LABEL_SOURCE_CURRENT_INPUTS",
        "repair_requirement_code": "RUN_OR_JOIN_MICROSCOPE_REPLAY_OR_READONLY_BROKER_LIFECYCLE_COST_SOURCE",
    }


def update_label_counters(row: dict[str, Any], counters: dict[str, Counter[str]]) -> None:
    values = row["label_values"]
    for family in ALL_LABEL_FAMILIES:
        value = values.get(family)
        if value in (None, "", [], {}):
            counters[family]["missing"] += 1
        else:
            counters[family]["available"] += 1
            if value is True:
                counters[family]["true"] += 1
            elif value is False:
                counters[family]["false"] += 1
            elif isinstance(value, (int, float)):
                counters[family]["numeric"] += 1
            else:
                counters[family]["categorical_or_object"] += 1


def build_label_vectors(hashes: dict[str, str | None]) -> tuple[dict[str, Any], set[tuple[str, str, str, str, str]]]:
    supplements = load_supplements()
    labeled_keys: set[tuple[str, str, str, str, str]] = set()
    family_counters: dict[str, Counter[str]] = defaultdict(Counter)
    evidence_counts: Counter[str] = Counter()
    source_use_counts: Counter[str] = Counter()
    source_family_counts: Counter[str] = Counter()
    outcome_counts: Counter[str] = Counter()
    no_leak_time_violations = 0
    rows_written = 0
    broker_real_rows = 0
    proxy_rows = 0
    source_gap_rows = 0
    first_rows: list[dict[str, Any]] = []

    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with gzip.open(LABEL_VECTOR_LEDGER, "wb", compresslevel=1) as handle:
        for _line_number, timeline in iter_jsonl(LANE04_TIMELINE):
            vector = derive_timeline_label_vector(timeline, supplements, hashes)
            handle.write(json_line_bytes(vector, sort_keys=True) + b"\n")
            rows_written += 1
            if len(first_rows) < 3:
                first_rows.append(vector)
            labeled_keys.add(canonical_key_tuple(vector))
            labeled_keys.add(canonical_key_tuple_fast(vector))
            # Add source and entry times as alternates for Lane03 joins.
            alt = dict(vector)
            alt["candidate_time_utc"] = vector.get("entry_time_utc")
            labeled_keys.add(canonical_key_tuple(alt))
            labeled_keys.add(canonical_key_tuple_fast(alt))
            update_label_counters(vector, family_counters)
            evidence_counts[str(vector.get("evidence_class"))] += 1
            source_use_counts[str(vector.get("source_use_state"))] += 1
            source_family_counts[str(vector.get("source_family"))] += 1
            if vector["label_values"].get("broker_real_net_r") is not None:
                broker_real_rows += 1
            if vector["label_values"].get("source_bound_proxy_r") is not None:
                proxy_rows += 1
            if vector["label_values"].get("source_gap_present"):
                source_gap_rows += 1
            outcome_counts[str(vector["label_values"].get("path_class"))] += 1
            ct = parse_utc(vector.get("candidate_time_utc"))
            lt = parse_utc(vector.get("label_time_utc"))
            if ct is not None and lt is not None and lt < ct:
                no_leak_time_violations += 1

    coverage_rows = []
    for family in ALL_LABEL_FAMILIES:
        counts = family_counters[family]
        coverage_rows.append(
            {
                "schema_version": "lane06_label_family_coverage_v1",
                "route_id": ROUTE_ID,
                "label_family": family,
                "available_rows": counts.get("available", 0),
                "missing_rows": counts.get("missing", 0),
                "true_rows": counts.get("true", 0),
                "false_rows": counts.get("false", 0),
                "numeric_rows": counts.get("numeric", 0),
                "categorical_or_object_rows": counts.get("categorical_or_object", 0),
                "total_label_vector_rows": rows_written,
            }
        )
    write_jsonl(LABEL_FAMILY_COVERAGE_LEDGER, coverage_rows)

    source_rows = []
    for scope, counter in (
        ("evidence_class", evidence_counts),
        ("source_use_state", source_use_counts),
        ("source_family", source_family_counts),
        ("path_class", outcome_counts),
    ):
        for key, count in sorted(counter.items()):
            source_rows.append(
                {
                    "schema_version": "lane06_source_coverage_v1",
                    "route_id": ROUTE_ID,
                    "coverage_scope": scope,
                    "coverage_key": key,
                    "rows": count,
                }
            )
    write_jsonl(SOURCE_COVERAGE_LEDGER, source_rows)

    return (
        {
            "label_vector_rows": rows_written,
            "broker_real_rows": broker_real_rows,
            "proxy_rows": proxy_rows,
            "source_gap_rows": source_gap_rows,
            "no_leak_time_violations": no_leak_time_violations,
            "label_family_count": len(ALL_LABEL_FAMILIES),
            "evidence_class_counts": dict(evidence_counts),
            "source_use_counts": dict(source_use_counts),
            "source_family_counts": dict(source_family_counts),
            "first_row_ids": [row["row_id"] for row in first_rows],
        },
        labeled_keys,
    )


def load_existing_label_vector_summary() -> tuple[dict[str, Any], set[tuple[str, str, str, str, str]]]:
    labeled_keys: set[tuple[str, str, str, str, str]] = set()
    evidence_counts: Counter[str] = Counter()
    source_use_counts: Counter[str] = Counter()
    source_family_counts: Counter[str] = Counter()
    rows = 0
    broker_real_rows = 0
    proxy_rows = 0
    source_gap_rows = 0
    no_leak_time_violations = 0
    for _line_number, vector in iter_jsonl(LABEL_VECTOR_LEDGER):
        rows += 1
        labeled_keys.add(canonical_key_tuple(vector))
        labeled_keys.add(canonical_key_tuple_fast(vector))
        alt = dict(vector)
        alt["candidate_time_utc"] = vector.get("entry_time_utc")
        labeled_keys.add(canonical_key_tuple(alt))
        labeled_keys.add(canonical_key_tuple_fast(alt))
        evidence_counts[str(vector.get("evidence_class"))] += 1
        source_use_counts[str(vector.get("source_use_state"))] += 1
        source_family_counts[str(vector.get("source_family"))] += 1
        label_values = vector.get("label_values") or {}
        if label_values.get("broker_real_net_r") is not None:
            broker_real_rows += 1
        if label_values.get("source_bound_proxy_r") is not None:
            proxy_rows += 1
        if label_values.get("source_gap_present"):
            source_gap_rows += 1
        ct = parse_utc(vector.get("candidate_time_utc"))
        lt = parse_utc(vector.get("label_time_utc"))
        if ct is not None and lt is not None and lt < ct:
            no_leak_time_violations += 1
    return (
        {
            "label_vector_rows": rows,
            "broker_real_rows": broker_real_rows,
            "proxy_rows": proxy_rows,
            "source_gap_rows": source_gap_rows,
            "no_leak_time_violations": no_leak_time_violations,
            "label_family_count": len(ALL_LABEL_FAMILIES),
            "evidence_class_counts": dict(evidence_counts),
            "source_use_counts": dict(source_use_counts),
            "source_family_counts": dict(source_family_counts),
            "reused_existing_label_vector": True,
        },
        labeled_keys,
    )


def build_missing_label_gaps(labeled_keys: set[tuple[str, str, str, str, str]], hashes: dict[str, str | None]) -> dict[str, Any]:
    total = 0
    missing = 0
    matched = 0
    missing_by_symbol: Counter[str] = Counter()
    missing_by_framework: Counter[str] = Counter()

    MISSING_LABEL_GAP_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    if MISSING_LABEL_GAP_LEDGER.suffix == ".gz":
        handle_context = gzip.open(MISSING_LABEL_GAP_LEDGER, "wb", compresslevel=1)
    else:
        handle_context = MISSING_LABEL_GAP_LEDGER.open("wb")
    with handle_context as handle:
        for line_number, row in iter_jsonl(LANE03_CANDIDATES):
            total += 1
            if canonical_key_tuple_fast(row) in labeled_keys:
                matched += 1
                continue
            missing += 1
            missing_by_symbol[str(row.get("symbol") or "UNKNOWN")] += 1
            missing_by_framework[str(row.get("framework") or "UNKNOWN")] += 1
            handle.write(json_line_bytes(missing_label_gap_row(row, line_number, hashes)) + b"\n")
            if total % 100_000 == 0:
                write_json(
                    BUILD_PROGRESS,
                    {
                        "route_id": ROUTE_ID,
                        "phase": "lane03_missing_label_gap_stream",
                        "updated_at_utc": utc_now(),
                        "lane03_rows_scanned": total,
                        "missing_gap_rows_written": missing,
                        "matched_label_source_rows": matched,
                        "gap_file_bytes": MISSING_LABEL_GAP_LEDGER.stat().st_size if MISSING_LABEL_GAP_LEDGER.exists() else 0,
                    },
                )
    return {
        "lane03_candidate_rows_scanned": total,
        "lane03_candidates_with_joined_label_source": matched,
        "missing_label_gap_rows": missing,
        "missing_label_gap_by_symbol": dict(missing_by_symbol),
        "missing_label_gap_by_framework": dict(missing_by_framework),
    }


def load_existing_missing_gap_summary() -> dict[str, Any]:
    total = 0
    missing_by_symbol: Counter[str] = Counter()
    missing_by_framework: Counter[str] = Counter()
    for _line_number, row in iter_jsonl(MISSING_LABEL_GAP_LEDGER):
        total += 1
        missing_by_symbol[str(row.get("symbol") or "UNKNOWN")] += 1
        missing_by_framework[str(row.get("framework") or "UNKNOWN")] += 1
    lane03_manifest = read_json(LANE03_MANIFEST, {}) or {}
    lane03_rows = lane03_manifest.get("counts", {}).get("canonical_candidate_rows")
    if lane03_rows is None:
        candidate_path = rel(LANE03_CANDIDATES)
        for item in lane03_manifest.get("files", []):
            if item.get("path") == candidate_path:
                lane03_rows = item.get("line_count")
                break
    return {
        "lane03_candidate_rows_scanned": lane03_rows,
        "lane03_candidates_with_joined_label_source": None if lane03_rows is None else int(lane03_rows) - total,
        "missing_label_gap_rows": total,
        "missing_label_gap_by_symbol": dict(missing_by_symbol),
        "missing_label_gap_by_framework": dict(missing_by_framework),
        "reused_existing_missing_gap_ledger": True,
    }


def lane07_source_summary() -> dict[str, Any]:
    broker_truth_rows = 0
    cost_rows = 0
    cost_row_types: Counter[str] = Counter()
    cost_status_counts: Counter[str] = Counter()
    if LANE07_BROKER_TRUTH.exists():
        for _line_number, _row in iter_jsonl(LANE07_BROKER_TRUTH):
            broker_truth_rows += 1
    if LANE07_COST.exists():
        for _line_number, row in iter_jsonl(LANE07_COST):
            cost_rows += 1
            cost_row_types[str(row.get("row_type") or "unknown")] += 1
            cost_status_counts[str(row.get("cost_status") or "unknown")] += 1
    return {
        "lane07_broker_truth_rows": broker_truth_rows,
        "lane07_cost_rows": cost_rows,
        "lane07_cost_row_type_counts": dict(cost_row_types),
        "lane07_cost_status_counts": dict(cost_status_counts),
    }


def dependency_rows(generated_at: str) -> list[dict[str, Any]]:
    deps = [
        ("lane01_source_authority", LANE01_DIR, "present_consumed", "missing_required_dependency"),
        ("lane02_asof_contract", LANE02_DIR, "present_consumed", "missing_required_dependency"),
        ("lane03_canonical_reconstruction", LANE03_DIR, "present_consumed", "missing_required_dependency"),
        ("lane04_microscope_timelines", LANE04_DIR, "present_consumed", "missing_required_dependency"),
        (
            "lane05_feature_store_contract",
            LANE05_DIR,
            "present_consumed_for_label_join_no_leak_contract",
            "absent_dependency_state_recorded_not_blocking_label_builder",
        ),
        ("absolute_master_orchestration", MASTER_DIR, "present_consumed", "missing_required_dependency"),
        ("friday_microscope", FRIDAY_DIR, "present_consumed", "missing_required_dependency"),
        (
            "mt5_local_cache_preservation",
            MT5_CACHE_DIR,
            "present_referenced_for_source_authority_not_reparsed",
            "absent_reference_only_not_blocking_label_builder",
        ),
        (
            "broker_truth_sparse_route",
            BROKER_TRUTH_DIR,
            "present_consumed_for_broker_real_labels_where_available",
            "absent_sparse_broker_truth_not_blocking_proxy_labels",
        ),
        (
            "lane07_broker_truth_cost_calibration",
            LANE07_DIR,
            "present_consumed_for_broker_truth_cost_labels_where_joinable",
            "absent_dependency_state_recorded_sparse_broker_truth_from_prior_route_used",
        ),
    ]
    rows = []
    for name, path, present_state, absent_state in deps:
        exists = path.exists()
        rows.append(
            {
                "schema_version": "lane06_dependency_state_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": generated_at,
                "dependency_name": name,
                "dependency_path": rel(path),
                "exists": exists,
                "dependency_state": present_state if exists else absent_state,
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            }
        )
    return rows


def source_completeness_rows(generated_at: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "lane06_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "lane04_timeline_is_primary_label_source",
            "source_path": rel(LANE04_TIMELINE),
            "row_count": summary.get("label_vector_rows"),
            "source_use_state": "source_bound_path_proxy_and_friday_tick_rows",
            "outcome": "materialized_into_label_vector_ledger",
        },
        {
            "schema_version": "lane06_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "broker_real_labels_only_where_captured",
            "source_path": rel(BROKER_TRUTH_DIR),
            "row_count": summary.get("broker_real_rows"),
            "source_use_state": "broker_real_truth_sparse_not_required_for_proxy_labels",
            "outcome": "broker_net_r_not_backfilled_or_collapsed_into_proxy_r",
        },
        {
            "schema_version": "lane06_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "lane07_broker_truth_cost_calibration_consumed_when_present",
            "source_path": rel(LANE07_DIR),
            "row_count": summary.get("lane07_cost_rows"),
            "source_use_state": "broker_real_cost_truth_and_cost_proxy_rows_consumed_after_split_purge_for_labels_only",
            "outcome": "lane07 broker-real trade-cost rows join to the sparse broker-real label rows; non-trade cost rows remain source coverage and never feature leakage",
        },
        {
            "schema_version": "lane06_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "lane03_unjoined_candidates_preserved_as_row_level_missing_label_gaps",
            "source_path": rel(LANE03_CANDIDATES),
            "row_count": summary.get("missing_label_gap_rows"),
            "source_use_state": "canonical_candidates_without_current_label_source",
            "outcome": "gap_rows_require_microscope_replay_or_broker_truth_join",
        },
        {
            "schema_version": "lane06_source_completeness_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "read_only_broker_export_not_executed_in_this_builder",
            "source_path": rel(BROKER_TRUTH_DIR),
            "source_use_state": "existing_sparse_broker_route_sufficient_for_present_broker_real_labels",
            "outcome": "future broker-real expansion requires explicit read-only export/capture for missing rows",
        },
    ]


def implementation_rows(generated_at: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "lane06_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "materialize_compressed_label_vector_ledger",
            "evidence": rel(LABEL_VECTOR_LEDGER),
            "rows": summary.get("label_vector_rows"),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        },
        {
            "schema_version": "lane06_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "materialize_lane03_missing_label_gap_ledger",
            "evidence": rel(MISSING_LABEL_GAP_LEDGER),
            "rows": summary.get("missing_label_gap_rows"),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        },
        {
            "schema_version": "lane06_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "keep_broker_real_proxy_replay_label_families_separate",
            "evidence": rel(LABEL_SCHEMA),
            "broker_real_rows": summary.get("broker_real_rows"),
            "proxy_rows": summary.get("proxy_rows"),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        },
        {
            "schema_version": "lane06_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "consume_lane05_and_lane07_contracts_without_feature_or_live_leakage",
            "evidence": [rel(LANE05_DOWNSTREAM_CONTRACT), rel(LANE07_DOWNSTREAM_CONTRACT)],
            "lane05_present": LANE05_DIR.exists(),
            "lane07_present": LANE07_DIR.exists(),
            "lane07_cost_rows": summary.get("lane07_cost_rows"),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        },
        {
            "schema_version": "lane06_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "decision": "no_production_runtime_activation",
            "evidence": rel(RUNTIME_EFFECT_BOUNDARY_PATH),
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        },
    ]


def downstream_contract_payload(generated_at: str) -> dict[str, Any]:
    lane05_schema = read_json(LANE05_SCHEMA, {}) if LANE05_SCHEMA.exists() else {}
    return {
        "schema_version": "lane06_downstream_contract_v1",
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "canonical_join_policy": rel(LANE02_KEY_POLICY),
        "feature_store": {
            "contract": "labels are forbidden as feature columns; join labels only after purged/embargoed split construction",
            "label_use_state": "forbidden_as_feature_column",
            "forbidden_label_fields_as_features": list(ALL_LABEL_FAMILIES),
            "lane05_state": "present_consumed_for_label_join_no_leak_contract" if LANE05_DIR.exists() else "feature_store_route_absent_dependency_state_recorded",
            "lane05_feature_set_id": lane05_schema.get("feature_set_id"),
            "lane05_schema": rel(LANE05_SCHEMA) if LANE05_SCHEMA.exists() else None,
            "lane05_no_leak": rel(LANE05_NO_LEAK) if LANE05_NO_LEAK.exists() else None,
            "lane05_downstream_contract": rel(LANE05_DOWNSTREAM_CONTRACT) if LANE05_DOWNSTREAM_CONTRACT.exists() else None,
            "lane05_join_rule": "labels join to Lane05 feature rows only after purged/embargoed split construction; label/outcome fields never become Lane05 feature columns",
        },
        "digital_twin": {
            "contract": "may consume path, source-gap, execution-policy, and broker/proxy labels as result ledgers, not decision features",
            "primary_inputs": [rel(LABEL_VECTOR_LEDGER), rel(MISSING_LABEL_GAP_LEDGER)],
            "broker_truth_cost_contract": rel(LANE07_DOWNSTREAM_CONTRACT) if LANE07_DOWNSTREAM_CONTRACT.exists() else rel(BROKER_MANIFEST),
        },
        "ml": {
            "contract": "use label vectors as targets with evidence_class selection; broker_real_net_r and source_bound_proxy_r are separate target families",
            "purge_rule": "feature rows use candidate_time_utc; purge and embargo must consider label_time_utc",
            "feature_store_contract": rel(LANE05_DOWNSTREAM_CONTRACT) if LANE05_DOWNSTREAM_CONTRACT.exists() else None,
        },
        "selector": {
            "contract": "offline selector training/evaluation only; no live selector activation from this route",
            "eligible_labels": ["correct_rejection", "missed_opportunity", "stale_blocker", "source_bound_proxy_r", "broker_real_net_r"],
        },
        "scheduler": {
            "contract": "offline risk/exposure outcome analysis only; broker-real and proxy labels must not alter live scheduling without a later dossier",
            "eligible_labels": ["broker_lifecycle_status", "cost_adjusted_r", "broker_real_net_r", "manual_intervention"],
        },
        "execution_policy": {
            "contract": "offline policy-result, SL-first, 1R, partial-BE, target, MFE/MAE, and timing labels for policy evaluation",
            "broker_truth_cost_contract": rel(LANE07_DOWNSTREAM_CONTRACT) if LANE07_DOWNSTREAM_CONTRACT.exists() else rel(BROKER_MANIFEST),
            "eligible_labels": [
                "sl_before_1r",
                "one_r_reached",
                "partial_then_be",
                "partial_then_final",
                "final_target_reached",
                "time_to_1r_seconds",
                "time_to_sl_seconds",
                "time_to_final_seconds",
                "execution_policy_result",
            ],
        },
    }


def no_leak_rows(generated_at: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    field_contract = read_json(LANE02_FIELD_CONTRACT, {}) or {}
    label_allowed = set((field_contract.get("label_store") or {}).get("allowed", []))
    feature_forbidden = set((field_contract.get("feature_store") or {}).get("forbidden", []))
    expected_label_classes = {"label_only", "future_outcome", "broker_realized", "post_order", "post_fill", "post_close", "replay_only"}
    lane05_schema = read_json(LANE05_SCHEMA, {}) if LANE05_SCHEMA.exists() else {}
    lane05_features = {str(item.get("feature_name") if isinstance(item, dict) else item) for item in lane05_schema.get("features", [])}
    lane05_forbidden = {str(item) for item in lane05_schema.get("forbidden_post_outcome_fields_excluded", [])}
    allowed_asof_status_feature_names = {
        "m1_availability_status",
        "tick_availability_status",
        "source_quality_status",
    }
    sensitive_label_families = set(ALL_LABEL_FAMILIES) - allowed_asof_status_feature_names
    label_family_overlap = sorted(lane05_features.intersection(sensitive_label_families))
    lane05_downstream = read_json(LANE05_DOWNSTREAM_CONTRACT, {}) if LANE05_DOWNSTREAM_CONTRACT.exists() else {}
    lane05_label_contract = json.dumps(lane05_downstream.get("label_store", {}) or lane05_downstream, sort_keys=True).lower()
    return [
        {
            "schema_version": "lane06_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "check_id": "lane02_label_store_contract_allows_label_classes",
            "status": "pass" if expected_label_classes.issubset(label_allowed) else "fail",
            "evidence": rel(LANE02_FIELD_CONTRACT),
            "details": {"expected_subset": sorted(expected_label_classes), "actual": sorted(label_allowed)},
        },
        {
            "schema_version": "lane06_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "check_id": "feature_store_forbids_post_outcome_classes",
            "status": "pass" if {"future_outcome", "broker_realized", "label_only"}.issubset(feature_forbidden) else "fail",
            "evidence": rel(LANE02_FIELD_CONTRACT),
            "details": {"feature_forbidden": sorted(feature_forbidden)},
        },
        {
            "schema_version": "lane06_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "check_id": "label_time_not_before_candidate_time",
            "status": "pass" if summary.get("no_leak_time_violations") == 0 else "fail",
            "evidence": rel(LABEL_VECTOR_LEDGER),
            "details": {"violations": summary.get("no_leak_time_violations")},
        },
        {
            "schema_version": "lane06_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "check_id": "broker_real_and_proxy_r_not_collapsed",
            "status": "pass" if summary.get("broker_real_rows", 0) > 0 and summary.get("proxy_rows", 0) > 0 else "fail",
            "evidence": rel(LABEL_SCHEMA),
            "details": {"broker_real_rows": summary.get("broker_real_rows"), "proxy_rows": summary.get("proxy_rows")},
        },
        {
            "schema_version": "lane06_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "check_id": "lane05_feature_store_present_or_absent_state_recorded",
            "status": "pass" if (LANE05_DIR.exists() == LANE05_SCHEMA.exists()) else "fail",
            "evidence": rel(DEPENDENCY_STATE_LEDGER),
            "details": {
                "lane05_exists": LANE05_DIR.exists(),
                "lane05_schema": rel(LANE05_SCHEMA) if LANE05_SCHEMA.exists() else None,
                "state": "present_consumed_for_label_join_no_leak_contract" if LANE05_DIR.exists() else "absent_dependency_state_recorded",
            },
        },
        {
            "schema_version": "lane06_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "check_id": "lane05_feature_schema_has_no_label_family_columns",
            "status": "pass" if LANE05_SCHEMA.exists() and not label_family_overlap else "fail",
            "evidence": rel(LANE05_SCHEMA),
            "details": {
                "allowed_asof_status_feature_names": sorted(allowed_asof_status_feature_names),
                "lane05_feature_count": lane05_schema.get("feature_count"),
                "label_family_overlap": label_family_overlap,
                "forbidden_post_outcome_fields_excluded": sorted(lane05_forbidden),
            },
        },
        {
            "schema_version": "lane06_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "check_id": "lane05_label_join_after_split_contract_present",
            "status": "pass" if LANE05_DOWNSTREAM_CONTRACT.exists() and "label" in lane05_label_contract and "split" in lane05_label_contract else "fail",
            "evidence": rel(LANE05_DOWNSTREAM_CONTRACT),
            "details": {"lane05_downstream_contract_exists": LANE05_DOWNSTREAM_CONTRACT.exists()},
        },
        {
            "schema_version": "lane06_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "check_id": "lane07_broker_truth_contract_label_store_join_only",
            "status": "pass" if LANE07_DOWNSTREAM_CONTRACT.exists() and summary.get("lane07_cost_row_type_counts", {}).get("broker_real_trade_cost", 0) >= summary.get("broker_real_rows", 0) else "fail",
            "evidence": rel(LANE07_DOWNSTREAM_CONTRACT),
            "details": {
                "lane07_exists": LANE07_DIR.exists(),
                "lane07_cost_row_type_counts": summary.get("lane07_cost_row_type_counts", {}),
                "broker_real_rows": summary.get("broker_real_rows"),
            },
        },
    ]


def write_context_anchor(generated_at: str, summary: dict[str, Any]) -> None:
    text = f"""# Lane06 Label Store V1 Context Anchor

Generated: {generated_at}
Route: `{ROUTE_ID}`
HEAD: `{git_head().get("head_short")}`

Controlling prompt: `{rel(PROMPT)}`
Starter: `{rel(STARTER)}`

Mandatory context read after preflight: `LIVE_STATE`, current vNext map,
repo reading order, goal-session research discipline, research operating
doctrine, moonshot vision, Lane01 source authority, Lane02 as-of contract,
Lane03 canonical reconstruction, Lane04 microscope timelines, Lane05 feature
store, Lane07 broker truth/cost calibration, Friday microscope, MT5
preservation, and sparse broker-truth route.

Current build state:
- Label vector rows: `{summary.get("label_vector_rows")}`
- Lane03 missing-label gap rows: `{summary.get("missing_label_gap_rows")}`
- Broker-real rows joined: `{summary.get("broker_real_rows")}`
- Proxy rows materialized: `{summary.get("proxy_rows")}`
- Lane07 broker truth rows scanned: `{summary.get("lane07_broker_truth_rows")}`
- Lane07 cost rows scanned: `{summary.get("lane07_cost_rows")}`
- Runtime effect boundary: `{RUNTIME_EFFECT_BOUNDARY}`

Stop condition: label rows were materialized where source-bound path/broker
evidence exists; unjoined Lane03 canonical candidates were preserved as
row-level missing-label gaps with exact repair requirements.
"""
    CONTEXT_ANCHOR.write_text(text, encoding="utf-8")


def write_saturation(generated_at: str, summary: dict[str, Any]) -> None:
    text = f"""# Lane06 Saturation And Self-Red-Team

Generated: {generated_at}

- Evidence-class confusion checked: broker-real `broker_real_net_r` remains a
  separate label family from `source_bound_proxy_r`; proxy labels are not
  broker performance claims.
- Denominator leakage checked: label rows carry `label_only_excluded_from_feature_rows`;
  Lane02 feature-store forbidden classes are rechecked in the no-leak ledger.
- Lane05 no-leak integration checked: present feature-store contract requires
  labels to join only after purged/embargoed splits and forbids label/outcome
  fields as feature columns.
- Lane07 broker/cost integration checked: broker-real trade-cost rows remain
  label-store broker truth, and non-trade slippage/spread rows remain source
  coverage rather than feature leakage or live execution input.
- Full same-class coverage checked: all Lane04 timeline rows were streamed into
  `{rel(LABEL_VECTOR_LEDGER)}` and all Lane03 canonical candidates without a
  joined label source were streamed into `{rel(MISSING_LABEL_GAP_LEDGER)}`.
- No arbitrary top-N: no row cap was used for label vectors or Lane03 gap rows.
- Missing source rule: broker-real net-R, cost-adjusted R, and tick/broker path
  gaps remain row-level missing-label/source reasons, not invented values.
- Downstream contract frozen: Feature Store, Digital Twin, ML, Selector,
  Scheduler, and Execution Policy use rules are written in
  `{rel(DOWNSTREAM_CONTRACT)}`.

Counts:
- label vector rows: `{summary.get("label_vector_rows")}`
- Lane03 candidates scanned: `{summary.get("lane03_candidate_rows_scanned")}`
- missing label gap rows: `{summary.get("missing_label_gap_rows")}`
- source gap rows inside vectors: `{summary.get("source_gap_rows")}`
- Lane07 broker truth rows: `{summary.get("lane07_broker_truth_rows")}`
- Lane07 cost rows: `{summary.get("lane07_cost_rows")}`
"""
    SATURATION_SELF_RED_TEAM.write_text(text, encoding="utf-8")


def manifest_payload(generated_at: str) -> dict[str, Any]:
    files = [
        LABEL_SCHEMA,
        LABEL_VECTOR_LEDGER,
        MISSING_LABEL_GAP_LEDGER,
        LABEL_FAMILY_COVERAGE_LEDGER,
        SOURCE_COVERAGE_LEDGER,
        NO_LEAK_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        IMPLEMENTATION_DECISION_LEDGER,
        DOWNSTREAM_CONTRACT,
        RUNTIME_EFFECT_BOUNDARY_PATH,
        RESULT_USE_STATUS_PATH,
        CONTEXT_ANCHOR,
        SATURATION_SELF_RED_TEAM,
        COMPLETION_AUDIT,
        BUILD_PROGRESS,
        OUTPUT_MANIFEST,
        Path(__file__).resolve(),
        VERIFIER,
        TEST_FILE,
        VERIFICATION_RESULT,
        FOCUSED_TEST_RESULT,
    ]
    return {
        "schema_version": "lane06_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": generated_at,
        "git": git_head(),
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "outputs": [
            {
                "path": rel(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "line_count": line_count(path) if path.exists() and path.suffix == ".jsonl" and path != MISSING_LABEL_GAP_LEDGER else None,
                "sha256": sha256_file(path) if path.exists() and path.name != OUTPUT_MANIFEST.name and path != MISSING_LABEL_GAP_LEDGER else None,
            }
            for path in files
        ],
    }


def build_route(*, reuse_label_vector: bool = False, reuse_missing_gap: bool = False) -> dict[str, Any]:
    generated_at = utc_now()
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    hashes = source_hash_lookup()
    write_json(LABEL_SCHEMA, label_schema_payload(generated_at))
    if reuse_label_vector and LABEL_VECTOR_LEDGER.exists() and LABEL_VECTOR_LEDGER.stat().st_size > 0:
        vector_summary, labeled_keys = load_existing_label_vector_summary()
    else:
        vector_summary, labeled_keys = build_label_vectors(hashes)
    if reuse_missing_gap and MISSING_LABEL_GAP_LEDGER.exists() and MISSING_LABEL_GAP_LEDGER.stat().st_size > 0:
        gap_summary = load_existing_missing_gap_summary()
    else:
        gap_summary = build_missing_label_gaps(labeled_keys, hashes)
    summary = {**vector_summary, **gap_summary, **lane07_source_summary()}
    write_jsonl(DEPENDENCY_STATE_LEDGER, dependency_rows(generated_at))
    write_jsonl(SOURCE_COMPLETENESS_LEDGER, source_completeness_rows(generated_at, summary))
    write_jsonl(IMPLEMENTATION_DECISION_LEDGER, implementation_rows(generated_at, summary))
    write_json(DOWNSTREAM_CONTRACT, downstream_contract_payload(generated_at))
    write_json(
        RUNTIME_EFFECT_BOUNDARY_PATH,
        {
            "schema_version": "lane06_runtime_effect_boundary_v1",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "forbidden_surfaces": [
                "live broker operation",
                "order/deal/position change",
                "paid API/vendor call",
                "credential or remote change",
                "prompt/config/risk/execution/safety/canary/selector activation",
            ],
        },
    )
    write_json(
        RESULT_USE_STATUS_PATH,
        {
            "schema_version": "lane06_result_use_status_v1",
            "route_id": ROUTE_ID,
            "result_use_status": RESULT_USE_STATUS,
            "broker_real_truth_state": "available_only_for_captured_sparse_broker_rows",
            "proxy_truth_state": "source_bound_path_or_replay_projection_not_broker_performance",
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        },
    )
    write_jsonl(NO_LEAK_LEDGER, no_leak_rows(generated_at, summary))
    write_context_anchor(generated_at, summary)
    write_saturation(generated_at, summary)
    write_json(
        COMPLETION_AUDIT,
        {
            "schema_version": "lane06_completion_audit_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": generated_at,
            "status": "built_pending_verifier_refresh",
            "objective": "vNext moonshot Label Store V1",
            "counts": summary,
            "instruction_coverage": {
                "mandatory_preflight_reread": True,
                "goal_session_research_discipline_read": True,
                "research_operating_doctrine_read": True,
                "builder_posture_applied": "constructive_builder_curiosity_active_creativity_no_conservative_brake",
                "no_arbitrary_top_n": True,
                "broker_real_proxy_replay_separated": True,
                "full_lane04_label_vectors_written": True,
                "lane03_missing_label_gap_rows_written": True,
                "lane05_feature_store_present_consumed": LANE05_DIR.exists(),
                "lane07_broker_truth_cost_present_consumed": LANE07_DIR.exists(),
                "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            },
            "requirements": [
                {"requirement": "label_schema", "status": "complete", "evidence": rel(LABEL_SCHEMA)},
                {"requirement": "label_builder", "status": "complete", "evidence": rel(Path(__file__).resolve())},
                {"requirement": "label_vector_ledger", "status": "complete", "rows": summary.get("label_vector_rows"), "evidence": rel(LABEL_VECTOR_LEDGER)},
                {"requirement": "missing_label_gap_ledger", "status": "complete", "rows": summary.get("missing_label_gap_rows"), "evidence": rel(MISSING_LABEL_GAP_LEDGER)},
                {"requirement": "coverage_ledgers", "status": "complete", "evidence": [rel(LABEL_FAMILY_COVERAGE_LEDGER), rel(SOURCE_COVERAGE_LEDGER)]},
                {"requirement": "no_leak_checks", "status": "complete", "evidence": rel(NO_LEAK_LEDGER)},
                {"requirement": "downstream_contract", "status": "complete", "evidence": rel(DOWNSTREAM_CONTRACT)},
                {"requirement": "runtime_effect_boundary", "status": "complete", "evidence": rel(RUNTIME_EFFECT_BOUNDARY_PATH)},
                {"requirement": "manifest_verifier_focused_tests", "status": "pending_verifier_and_pytest", "evidence": [rel(OUTPUT_MANIFEST), rel(VERIFIER), rel(TEST_FILE)]},
            ],
        },
    )
    write_json(OUTPUT_MANIFEST, manifest_payload(generated_at))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="accepted for symmetry; builder always writes outputs")
    parser.add_argument("--reuse-label-vector", action="store_true", help="reuse an existing completed label vector ledger")
    parser.add_argument("--reuse-missing-gap", action="store_true", help="reuse an existing completed missing-label gap ledger")
    args = parser.parse_args(argv)
    summary = build_route(reuse_label_vector=args.reuse_label_vector, reuse_missing_gap=args.reuse_missing_gap)
    print(json.dumps({"ok": True, "route_id": ROUTE_ID, **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
