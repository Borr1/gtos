#!/usr/bin/env python3
"""Build source-bound-to-executed replay provenance and leakage ledgers.

The source package's 82 sleeves / 1,101 member axes do not carry exact broad
replay candidate IDs. This builder therefore records two evidence classes:

- exact package candidate IDs where the package replay-authority ledger has one
- sleeve/member axis overlap joins where only symbol/side/framework/origin/session
  provenance is available

Broker/live/final authority remains closed. The output is deterministic from
route artifacts on disk and labels broad replay observations as partial when the
broad summary/comparison files have not been written yet.
"""

from __future__ import annotations

import json
import math
import argparse
import gc
import hashlib
import os
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence, TextIO

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.reduced_risk_action_reason_contract import (
    REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS,
    SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS,
    SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS,
    SOURCE_COMPLETENESS_BLOCKED_STATUS_TOKENS,
)
from src.components.session_namespace import utc_hour_bucket_aliases
from src.components.poi_state_contract import (
    POI_STATE_ATOMIC_FIELDS,
    poi_state_contract_failures,
    poi_state_required,
)
from src.research.moonshot_scheduler_v4_best_trade_allocator import (
    PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS,
    PACKAGE_NEW_ENTRY_AUTHORITY_EXECUTION_FILLABILITY_CLASS,
    PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT,
    PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA,
    package_new_entry_authority_payload_hash_sha256,
    package_new_entry_authority_required_payload_atom_failures,
    package_new_entry_authority_scope_for_action_intent,
    resolve_execution_fillability_surfaces,
)

FINAL_PACKAGE_SYNTHESIS = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_final_package_synthesis_2026_06_19"
)
CONVERGENCE = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_convergence_2026_06_19"
)
SCHEDULER_V3 = ROOT / "research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01"

SURFACE_PATH = ROUTE / "ULTIMATE_CANDIDATE_PACKAGE_SURFACE.json"
SLEEVE_REGISTRY_PATH = ROUTE / "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl"
SLEEVE_MEMBER_PATH = ROUTE / "SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl"
PACKAGE_CANDIDATE_PATH = (
    ROUTE / "ULTIMATE_CANDIDATE_PACKAGE_REPLAY_AUTHORITY_CANDIDATE_LEDGER.jsonl"
)

BROAD_PREFIX = "BROAD_LIVE_AS_IF_REPLAY"
BROAD_SUMMARY_PATH = ROUTE / f"{BROAD_PREFIX}_SUMMARY.json"
BROAD_COMPARISON_PATH = ROUTE / f"{BROAD_PREFIX}_COMPARISON_LEDGER.jsonl"
BROAD_CANDIDATE_PATH = ROUTE / f"{BROAD_PREFIX}_CANDIDATE_LEDGER.jsonl"
BROAD_CANDIDATE_INDEX_PATH = ROUTE / f"{BROAD_PREFIX}_CANDIDATE_INDEX_LEDGER.jsonl"
BROAD_SCORECARD_PATH = ROUTE / f"{BROAD_PREFIX}_SCORECARD_LEDGER.jsonl"
BROAD_ORDER_PATH = ROUTE / f"{BROAD_PREFIX}_ORDER_LEDGER.jsonl"
BROAD_ORACLE_PATH = ROUTE / f"{BROAD_PREFIX}_ORDERED_PATH_ORACLE_LEDGER.jsonl"
BROAD_TRADE_PATH = ROUTE / f"{BROAD_PREFIX}_TRADE_LEDGER.jsonl"
BROAD_MISSED_PATH = ROUTE / f"{BROAD_PREFIX}_MISSED_OPPORTUNITY_LEDGER.jsonl"
BROAD_PACKET_SIDECAR_PATH = ROUTE / f"{BROAD_PREFIX}_PACKET_SIDECAR_LEDGER.jsonl"

BIG_R_PROVENANCE_PATH = ROUTE / "BIG_R_PROVENANCE_BREAKDOWN.json"
PARITY_LEDGER_PATH = ROUTE / "SOURCE_BOUND_TO_EXECUTED_PARITY_LEDGER.jsonl"
PARITY_SUMMARY_PATH = ROUTE / "SOURCE_BOUND_TO_EXECUTED_PARITY_SUMMARY.json"
CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH = (
    ROUTE / "CANDIDATE_INSTANCE_PARITY_PROJECTION_LEDGER.jsonl"
)
LEAKAGE_BUCKET_PATH = ROUTE / "EXECUTION_LEAKAGE_BUCKET_LEDGER.jsonl"
REPAIR_PLAN_PATH = ROUTE / "EXECUTION_LEAKAGE_REPAIR_PLAN.json"

PROFILE_RAW = "raw_package_live_as_if"
PROFILE_GUARDED = "guarded_causal_admission_repair_v2"
PROFILES = (PROFILE_RAW, PROFILE_GUARDED)
BLOCKED_COUNTERFACTUAL_MISSED_LABELS = {
    "candidate_generated_selector_reject",
    "candidate_generated_broker_cost_refused_not_executable",
}
BLOCKED_COUNTERFACTUAL_MISSED_LABEL_PREFIXES = (
    "candidate_generated_broker_cost_source_gap_not_executable:",
)
EXECUTABLE_SCHEDULER_ACTION_INTENTS = {
    "new_position",
    "same_direction_scale_in",
    "close_and_reverse",
    "reduce_existing",
    "close_existing",
    "wait",
    "cancel_pending",
    "replace_pending",
}
PACKAGE_NEW_ENTRY_AUTHORITY_VALID_STATUS = "valid_signed_predecision_new_entry_authority"
MIN_EXECUTABLE_SOURCE_COMPLETENESS = 0.95
MIN_EXECUTABLE_FILL_PROBABILITY = 0.25
ROUTER_REFUSAL_MIN_EXPECTED_NET_R = 1.10
ROUTER_REFUSAL_MIN_PROBABILITY = 0.90
ROUTER_REFUSAL_MIN_FILL_PROBABILITY = 0.90
ROUTER_REFUSAL_MIN_SOURCE_COMPLETENESS = 0.95
SOURCE_BOUND_ROUTER_REFUSAL_MIN_EXPECTED_NET_R = 0.55
SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY = 0.70
SOURCE_BOUND_ROUTER_REFUSAL_MIN_FILL_PROBABILITY = 0.80
SOURCE_BOUND_ROUTER_REFUSAL_MIN_SOURCE_COMPLETENESS = 0.95
SCHEDULER_MATERIALIZATION_SOFT_TRANSFER_SKIP_TOKENS = (
    "not_scheduler_selected",
    "scheduler_not_selected",
    "scheduler_selection",
    "selected_competing_candidate",
    "selector_materialization",
    "runtime_eligible_no_selected",
    "no_selected_id",
    "selector_not_risk_bearing",
)
SCHEDULER_MATERIALIZATION_TERMINAL_SKIP_TOKENS = (
    "cost",
    "refused",
    "source_gap",
    "source_required",
    "fillability",
    "fill_probability",
    "unfillable",
    "marketable",
    "geometry",
    "invalid",
    "terminal",
    "expiry",
    "expired",
    "fallback",
    "lifecycle",
    "off_configured",
    "authority_missing",
)
JSONL_BINARY_STREAM_MIN_BYTES = 64_000_000
JSONL_LOCAL_CACHE_DIR = Path(
    os.environ.get("GTOS_JSONL_LOCAL_CACHE_DIR", "/tmp/gtos_route_jsonl_cache")
)
JSONL_LOCAL_CACHE_ENABLED = os.environ.get(
    "GTOS_JSONL_LOCAL_CACHE_ENABLED", "1"
).strip().lower() not in {"0", "false", "no", "off"}


def configure_artifact_paths(*, broad_prefix: str, artifact_tag: str = "") -> None:
    """Bind broad replay and parity output paths for deterministic reruns."""

    global BROAD_PREFIX
    global BROAD_SUMMARY_PATH
    global BROAD_COMPARISON_PATH
    global BROAD_CANDIDATE_PATH
    global BROAD_CANDIDATE_INDEX_PATH
    global BROAD_SCORECARD_PATH
    global BROAD_ORDER_PATH
    global BROAD_ORACLE_PATH
    global BROAD_TRADE_PATH
    global BROAD_MISSED_PATH
    global BROAD_PACKET_SIDECAR_PATH
    global BIG_R_PROVENANCE_PATH
    global PARITY_LEDGER_PATH
    global PARITY_SUMMARY_PATH
    global CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH
    global LEAKAGE_BUCKET_PATH
    global REPAIR_PLAN_PATH

    BROAD_PREFIX = broad_prefix
    BROAD_SUMMARY_PATH = ROUTE / f"{BROAD_PREFIX}_SUMMARY.json"
    BROAD_COMPARISON_PATH = ROUTE / f"{BROAD_PREFIX}_COMPARISON_LEDGER.jsonl"
    BROAD_CANDIDATE_PATH = ROUTE / f"{BROAD_PREFIX}_CANDIDATE_LEDGER.jsonl"
    BROAD_CANDIDATE_INDEX_PATH = ROUTE / f"{BROAD_PREFIX}_CANDIDATE_INDEX_LEDGER.jsonl"
    BROAD_SCORECARD_PATH = ROUTE / f"{BROAD_PREFIX}_SCORECARD_LEDGER.jsonl"
    BROAD_ORDER_PATH = ROUTE / f"{BROAD_PREFIX}_ORDER_LEDGER.jsonl"
    BROAD_ORACLE_PATH = ROUTE / f"{BROAD_PREFIX}_ORDERED_PATH_ORACLE_LEDGER.jsonl"
    BROAD_TRADE_PATH = ROUTE / f"{BROAD_PREFIX}_TRADE_LEDGER.jsonl"
    BROAD_MISSED_PATH = ROUTE / f"{BROAD_PREFIX}_MISSED_OPPORTUNITY_LEDGER.jsonl"
    BROAD_PACKET_SIDECAR_PATH = ROUTE / f"{BROAD_PREFIX}_PACKET_SIDECAR_LEDGER.jsonl"
    suffix = f"_{artifact_tag}" if artifact_tag else ""
    BIG_R_PROVENANCE_PATH = ROUTE / f"BIG_R_PROVENANCE_BREAKDOWN{suffix}.json"
    PARITY_LEDGER_PATH = ROUTE / f"SOURCE_BOUND_TO_EXECUTED_PARITY{suffix}_LEDGER.jsonl"
    PARITY_SUMMARY_PATH = ROUTE / f"SOURCE_BOUND_TO_EXECUTED_PARITY{suffix}_SUMMARY.json"
    CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH = (
        ROUTE / f"CANDIDATE_INSTANCE_PARITY_PROJECTION{suffix}_LEDGER.jsonl"
    )
    LEAKAGE_BUCKET_PATH = ROUTE / f"EXECUTION_LEAKAGE_BUCKET{suffix}_LEDGER.jsonl"
    REPAIR_PLAN_PATH = ROUTE / f"EXECUTION_LEAKAGE_REPAIR_PLAN{suffix}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def required_numeric_source_value(
    key: str,
    *sources: tuple[Mapping[str, Any], Path],
) -> tuple[float, Path]:
    """Resolve a required provenance component without silently inventing zero."""

    for payload, path in sources:
        value = payload.get(key) if isinstance(payload, Mapping) else None
        if value in (None, "") or isinstance(value, bool):
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric):
            return numeric, path
    searched = ",".join(str(path) for _, path in sources)
    raise ValueError(f"required_provenance_component_missing:{key}:{searched}")


def broad_quality_artifact_tag(prefix: str) -> str:
    stem = "BROAD_LIVE_AS_IF_REPLAY_"
    if prefix.startswith(stem):
        return prefix[len(stem) :]
    if prefix == "BROAD_LIVE_AS_IF_REPLAY":
        return ""
    return prefix


def broad_summary_completed(summary_payload: Mapping[str, Any]) -> bool:
    return (
        summary_payload.get("status")
        == "broad_live_as_if_replay_materialized_broker_live_closed"
        and summary_payload.get("live_broker_authority") is False
        and summary_payload.get("broker_mutation_enabled") is False
        and summary_payload.get("final_selection_claim") is False
    )


def broad_summary_sort_key(path: Path) -> tuple[str, float, str]:
    payload = read_json(path)
    generated = str(payload.get("generated_at_utc") or payload.get("generated_utc") or "")
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    return generated, mtime, path.name


def latest_completed_broad_prefix() -> str:
    explicit = os.environ.get("GTOS_BROAD_QUALITY_PARITY_PREFIX", "").strip()
    if explicit:
        return explicit
    for path in sorted(
        ROUTE.glob("BROAD_LIVE_AS_IF_REPLAY*_SUMMARY.json"),
        key=broad_summary_sort_key,
        reverse=True,
    ):
        prefix = path.name[: -len("_SUMMARY.json")]
        if prefix.endswith(
            (
                "_PARTIAL",
                "_FLOW_DIAGNOSTIC",
                "_BEHAVIOR_COMPARISON",
                "_COST_DELTA",
            )
        ):
            continue
        if broad_summary_completed(read_json(path)):
            return prefix
    return "BROAD_LIVE_AS_IF_REPLAY"


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


def iter_binary_text_lines(
    path: Path,
    *,
    chunk_size: int = 1024 * 1024,
    max_timeout_retries: int = 3600,
    reopen_after_timeout_retries: int = 20,
):
    pending = b""
    byte_offset = 0
    timeout_retries = 0
    active_chunk_size = chunk_size
    handle = path.open("rb")
    try:
        while True:
            try:
                chunk = handle.read(active_chunk_size)
            except TimeoutError:
                timeout_retries += 1
                if timeout_retries > max_timeout_retries:
                    raise
                if timeout_retries % reopen_after_timeout_retries == 0:
                    try:
                        byte_offset = handle.tell()
                    except OSError:
                        pass
                    try:
                        handle.close()
                    except OSError:
                        pass
                    time.sleep(1.0)
                    handle = path.open("rb")
                    handle.seek(byte_offset)
                    active_chunk_size = max(64 * 1024, active_chunk_size // 2)
                    continue
                time.sleep(0.5)
                continue
            timeout_retries = 0
            active_chunk_size = chunk_size
            if not chunk:
                if pending:
                    yield pending.decode("utf-8")
                break
            byte_offset += len(chunk)
            parts = chunk.splitlines(keepends=True)
            if pending:
                parts[0] = pending + parts[0]
                pending = b""
            if parts and not parts[-1].endswith((b"\n", b"\r")):
                pending = parts.pop()
            for raw_line in parts:
                yield raw_line.decode("utf-8")
    finally:
        try:
            handle.close()
        except OSError:
            pass


def iter_text_lines(path: Path) -> Iterable[str]:
    # Route evidence can intermittently raise TimeoutError even on small JSONL
    # files. Keep all JSONL reads on the retrying binary stream path instead of
    # letting small files bypass the timeout recovery used for large ledgers.
    yield from iter_binary_text_lines(local_cached_jsonl_path(path))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    line_number = 0
    for line in iter_text_lines(path):
        line_number += 1
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if isinstance(row, dict):
            yield row


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        count = write_jsonl_rows(handle, rows)
    tmp.replace(path)
    return count


def write_jsonl_rows(
    handle: TextIO,
    rows: Iterable[Mapping[str, Any]],
) -> int:
    """Write rows to an already-staged stream without retaining them."""

    count = 0
    for row in rows:
        handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
        count += 1
    return count


def rows_with_sink(
    rows: Iterable[dict[str, Any]],
    sink: Callable[[Mapping[str, Any]], None],
) -> Iterator[dict[str, Any]]:
    """Yield one-shot rows after forwarding each row to a bounded sink."""

    for row in rows:
        sink(row)
        yield row


def text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    value_text = str(value).strip()
    return value_text if value_text else default


RISK_BEARING_SELECTOR_ACTIONS = {"trade", "reduce-risk", "open-reduced-risk"}


def valid_package_new_entry_effective_selector_action(
    row: Mapping[str, Any],
) -> str:
    """Return materialized package action only when signed authority is valid."""

    action_intent = text(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
    )
    envelope = package_new_entry_authority_envelope_selection(
        row,
        action_intent=action_intent or None,
    )
    if envelope.get("valid") is not True:
        return ""
    payload = envelope.get("payload")
    payload = payload if isinstance(payload, Mapping) else {}
    action = text(payload.get("selector_action"))
    if action not in RISK_BEARING_SELECTOR_ACTIONS:
        return ""
    source_boundary = text(payload.get("source_boundary")).lower()
    if "predecision" not in source_boundary or "no_outcome" not in source_boundary:
        return ""
    if payload.get("uses_outcome_fields") is not False:
        return ""
    return action


def effective_selector_action(row: Mapping[str, Any], default: str = "") -> str:
    signed_package_action = valid_package_new_entry_effective_selector_action(row)
    return text(
        row.get("effective_selector_action")
        or row.get("scheduler_materialization_effective_selector_action")
        or row.get("selected_scheduler_effective_selector_action")
        or row.get("risk_finalizer_effective_selector_action")
        or signed_package_action
        or row.get("scheduler_materialization_selector_action")
        or row.get("risk_finalizer_selector_action_for_finalizer")
        or row.get("selector_action_for_finalizer")
        or row.get("materialized_effective_selector_action")
        or row.get("selector_action"),
        default,
    )


def effective_selector_reason(row: Mapping[str, Any], default: str = "") -> str:
    signed_package_action = valid_package_new_entry_effective_selector_action(row)
    return text(
        row.get("effective_selector_reason")
        or row.get("scheduler_materialization_effective_selector_reason")
        or row.get("risk_finalizer_effective_selector_reason")
        or row.get("risk_finalizer_scheduler_materialization_selector_reason")
        or (
            row.get("package_new_entry_authority_selector_reason")
            if signed_package_action
            else None
        )
        or row.get("scheduler_materialization_selector_reason")
        or row.get("selector_reason"),
        default,
    )


ORDER_ARCHITECTURE_LABELS = {
    "limit_first_guarded_market_fallback",
    "limit_first_with_guarded_market_fallback",
    "limit_first_reduced_risk",
}


def order_architecture_from_order_row(row: Mapping[str, Any]) -> str:
    """Return package/order architecture without collapsing it into order type."""

    for key in (
        "selected_order_type_architecture",
        "order_execution_path",
        "package_execution_policy_order_entry",
    ):
        value = row.get(key)
        if value not in (None, ""):
            return text(value, "unknown")
    return "unknown"


def order_type_from_order_row(row: Mapping[str, Any]) -> str:
    """Return the primitive executed order type, not the package architecture."""

    for key in (
        "effective_order_type",
        "primary_order_type",
        "order_type",
    ):
        value = row.get(key)
        if value not in (None, ""):
            value_text = text(value, "unknown")
            if norm(value_text) in ORDER_ARCHITECTURE_LABELS:
                continue
            if "guarded_market" in norm(value_text) and "limit" not in norm(value_text):
                return "market"
            if norm(value_text) in {"limit", "market", "none", "non_limit"}:
                return norm(value_text)
            return value_text
    simulated_limit_order = row.get("simulated_limit_order")
    if simulated_limit_order is True:
        return "limit"
    if simulated_limit_order is False:
        return "non_limit"
    return "unknown"


def upper(value: Any) -> str:
    return text(value).upper()


def norm(value: Any) -> str:
    return text(value).lower()


def family_aliases(value: Any) -> set[str]:
    raw = norm(value)
    if not raw:
        return set()
    aliases = {raw}
    if raw.startswith("origin_"):
        aliases.add(raw.removeprefix("origin_"))
    else:
        aliases.add(f"origin_{raw}")
    if raw.startswith("current_"):
        aliases.add(raw.removeprefix("current_"))
    else:
        aliases.add(f"current_{raw}")
    for alias in list(aliases):
        if alias.startswith("origin_current_"):
            aliases.add(alias.replace("origin_current_", "current_", 1))
        if alias.startswith("current_origin_"):
            aliases.add(alias.replace("current_origin_", "origin_", 1))
    return aliases


def family_matches(left: Any, right: Any) -> bool:
    left_text = text(left)
    right_text = text(right)
    if not left_text or not right_text:
        return True
    if wildcard(left_text) or wildcard(right_text):
        return True
    return bool(family_aliases(left_text) & family_aliases(right_text))


def side(value: Any) -> str:
    raw = upper(value)
    if raw in {"BUY", "BULL", "BULLISH", "LONG", "UP"}:
        return "LONG"
    if raw in {"SELL", "BEAR", "BEARISH", "SHORT", "DOWN"}:
        return "SHORT"
    return raw


def safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, "") or isinstance(value, bool):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def optional_float(value: Any) -> float | None:
    number = safe_float(value, default=math.nan)
    return number if math.isfinite(number) else None


EXECUTION_FILLABILITY_MISSING_SOURCE = "execution_fillability_missing_source_bound_input"
_EXECUTION_FILLABILITY_AUTHORITY_KEYS = (
    "pending_limit_fillability_probability",
    "predecision_limit_fillability_probability",
    "limit_fillability_probability",
    "package_new_entry_authority_predecision_limit_fillability_probability",
    "package_new_entry_authority_limit_fillability_probability",
    "limit_fill_probability",
)
_EXECUTION_FILLABILITY_DIRECT_KEYS = (
    "execution_fill_probability",
    "package_new_entry_authority_execution_fill_probability",
)
_EXECUTION_FILLABILITY_AUTHORITY_SOURCE_MARKERS = (
    "predecision_limit_fillability",
    "limit_fillability",
    "execution_fill_probability",
    "pending_limit_fillability",
)


def execution_fillability_authority(row: Mapping[str, Any]) -> tuple[float | None, str]:
    detail = resolve_execution_fillability_surfaces(row)
    value = optional_float(detail.get("value"))
    if value is not None:
        return max(0.0, min(1.0, value)), text(detail.get("source"))
    source = text(detail.get("source"))
    if source:
        return None, source
    return None, EXECUTION_FILLABILITY_MISSING_SOURCE


def missing_value(value: Any) -> bool:
    return value in (None, "", [], {})


def value_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "allowed", "pass", "eligible"}
    return bool(value)


def first_present(*values: Any) -> Any:
    for value in values:
        if not missing_value(value):
            return value
    return None


PACKAGE_NEW_ENTRY_AUTHORITY_SURFACE_FIELDS = (
    "ultimate_candidate_package_open_reduced_risk_authority",
    "ultimate_candidate_package_reduce_risk_authority",
    "ultimate_candidate_package_reduced_risk_authority",
    "package_new_entry_authority",
)
PACKAGE_NEW_ENTRY_AUTHORITY_REQUIRED_PAYLOAD_ATOMS = {
    "identity": (
        "candidate_id",
        "candidate_id_source",
        "decision_time_utc",
        "canonical_replay_candidate_instance_key",
        "source_bound_replay_candidate_instance_key",
        "candidate_instance_identity_status",
    ),
    "action": (
        "selector_action",
        "selector_reason",
        "target_action_intent",
    ),
    "scope": ("scope",),
    "source": (
        "uses_outcome_fields",
        "authority_applies",
        "authority_allowed",
        "authority_family",
        "authority_source",
        "source_boundary",
        "source_bound_package_candidate_use_allowed",
        "source_completeness_status",
    ),
    "quality": (
        "expected_net_r",
        "expected_net_r_semantics",
        "expected_net_r_semantics_source",
        "probability",
        "fill_probability",
        "source_completeness",
        "candidate_decision_quality_field_sources",
        "candidate_decision_quality_source_boundary",
        "candidate_decision_quality_alias_status",
        "candidate_decision_quality_alias_mismatches",
        "candidate_decision_quality_provenance_failures",
    ),
    "cost": (
        "pretrade_cost_packet_status",
        "cost_source_gap_status",
        "cost_authority",
        "candidate_cost_r_fallback_is_authority",
    ),
    "fill": (
        "execution_fill_probability",
        "execution_fill_probability_source",
        "execution_fill_probability_source_time_utc",
        "execution_fill_probability_source_boundary",
        "execution_fill_probability_authority_class",
        "entry_quality_fill_probability",
        "limit_fillability_probability",
        "predecision_limit_fillability_probability",
    ),
    "policy": (
        "selected_policy_for_expected_net_r",
        "selected_policy_expected_net_calibration_status",
        "selected_policy_expected_net_calibrated",
        "selected_policy_expected_net_calibration_required",
        "selected_policy_expected_net_calibration_source",
        "selected_policy_expected_net_calibration_source_boundary",
        "selected_policy_expected_net_calibration_hash",
    ),
    "order": (
        "package_replay_order_executable_candidate_use_allowed",
        "package_replay_order_executable_candidate_use_allowed_reason",
        "package_replay_order_executable_authority_source",
    ),
}
PACKAGE_NEW_ENTRY_AUTHORITY_REQUIRED_SEQUENCE_ATOMS = {
    "candidate_decision_quality_alias_mismatches",
    "candidate_decision_quality_provenance_failures",
}
PACKAGE_NEW_ENTRY_AUTHORITY_REQUIRED_BOOLEAN_ATOMS = {
    "uses_outcome_fields",
    "authority_applies",
    "authority_allowed",
    "source_bound_package_candidate_use_allowed",
    "candidate_cost_r_fallback_is_authority",
    "selected_policy_expected_net_calibrated",
    "selected_policy_expected_net_calibration_required",
    "package_replay_order_executable_candidate_use_allowed",
}
PACKAGE_NEW_ENTRY_AUTHORITY_REQUIRED_NUMERIC_ATOMS = {
    "expected_net_r",
    "probability",
    "fill_probability",
    "source_completeness",
    "execution_fill_probability",
    "entry_quality_fill_probability",
    "limit_fillability_probability",
    "predecision_limit_fillability_probability",
}
PACKAGE_NEW_ENTRY_AUTHORITY_EMPTY_POLICY_ATOMS = {
    "selected_policy_expected_net_calibration_source",
    "selected_policy_expected_net_calibration_source_boundary",
    "selected_policy_expected_net_calibration_hash",
}
PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_PROJECTIONS = {
    "payload_schema": "package_new_entry_authority_payload_schema",
    "scope": "package_new_entry_authority_scope",
    "target_action_intent": "package_new_entry_authority_target_action_intent",
    "uses_outcome_fields": "package_new_entry_authority_uses_outcome_fields",
    "candidate_id": "package_new_entry_authority_candidate_id",
    "candidate_id_source": "package_new_entry_authority_candidate_id_source",
    "decision_time_utc": "package_new_entry_authority_decision_time_utc",
    "canonical_replay_candidate_instance_key": (
        "package_new_entry_authority_canonical_replay_candidate_instance_key"
    ),
    "source_bound_replay_candidate_instance_key": (
        "package_new_entry_authority_source_bound_replay_candidate_instance_key"
    ),
    "candidate_instance_identity_status": (
        "package_new_entry_authority_candidate_instance_identity_status"
    ),
    "selector_action": "package_new_entry_authority_selector_action",
    "selector_reason": "package_new_entry_authority_selector_reason",
    "authority_family": "package_new_entry_authority_authority_family",
    "source_boundary": "package_new_entry_authority_source_boundary",
    "expected_net_r": "package_new_entry_authority_expected_net_r",
    "expected_net_r_semantics": (
        "package_new_entry_authority_expected_net_r_semantics"
    ),
    "expected_net_r_semantics_source": (
        "package_new_entry_authority_expected_net_r_semantics_source"
    ),
    "probability": "package_new_entry_authority_probability",
    "fill_probability": "package_new_entry_authority_fill_probability",
    "source_completeness": "package_new_entry_authority_source_completeness",
    "candidate_decision_quality_field_sources": (
        "package_new_entry_authority_candidate_decision_quality_field_sources"
    ),
    "candidate_decision_quality_source_boundary": (
        "package_new_entry_authority_candidate_decision_quality_source_boundary"
    ),
    "candidate_decision_quality_alias_status": (
        "package_new_entry_authority_candidate_decision_quality_alias_status"
    ),
    "candidate_decision_quality_alias_mismatches": (
        "package_new_entry_authority_candidate_decision_quality_alias_mismatches"
    ),
    "candidate_decision_quality_provenance_failures": (
        "package_new_entry_authority_candidate_decision_quality_provenance_failures"
    ),
    "pretrade_cost_packet_status": (
        "package_new_entry_authority_pretrade_cost_packet_status"
    ),
    "cost_source_gap_status": "package_new_entry_authority_cost_source_gap_status",
    "cost_authority": "package_new_entry_authority_cost_authority",
    "candidate_cost_r_fallback_is_authority": (
        "package_new_entry_authority_candidate_cost_r_fallback_is_authority"
    ),
    "source_completeness_status": (
        "package_new_entry_authority_source_completeness_status"
    ),
    "execution_fill_probability": (
        "package_new_entry_authority_execution_fill_probability"
    ),
    "execution_fill_probability_source": (
        "package_new_entry_authority_execution_fill_probability_source"
    ),
    "execution_fill_probability_source_time_utc": (
        "package_new_entry_authority_execution_fill_probability_source_time_utc"
    ),
    "execution_fill_probability_source_boundary": (
        "package_new_entry_authority_execution_fill_probability_source_boundary"
    ),
    "execution_fill_probability_authority_class": (
        "package_new_entry_authority_execution_fill_probability_authority_class"
    ),
    "entry_quality_fill_probability": (
        "package_new_entry_authority_entry_quality_fill_probability"
    ),
    "limit_fillability_probability": (
        "package_new_entry_authority_limit_fillability_probability"
    ),
    "predecision_limit_fillability_probability": (
        "package_new_entry_authority_predecision_limit_fillability_probability"
    ),
    "causal_poi_lifecycle_required": (
        "package_new_entry_authority_causal_poi_lifecycle_required"
    ),
    "causal_poi_lifecycle": (
        "package_new_entry_authority_causal_poi_lifecycle"
    ),
    "causal_poi_lifecycle_hash_sha256": (
        "package_new_entry_authority_causal_poi_lifecycle_hash_sha256"
    ),
    "causal_poi_lifecycle_source": (
        "package_new_entry_authority_causal_poi_lifecycle_source"
    ),
    "causal_poi_lifecycle_atomic_conflicts": (
        "package_new_entry_authority_causal_poi_lifecycle_atomic_conflicts"
    ),
    "causal_poi_lifecycle_contract_failures": (
        "package_new_entry_authority_causal_poi_lifecycle_contract_failures"
    ),
    "poi_scheduler_rankable_now": (
        "package_new_entry_authority_poi_scheduler_rankable_now"
    ),
    "poi_execution_allowed_by_lifecycle": (
        "package_new_entry_authority_poi_execution_allowed_by_lifecycle"
    ),
    "selected_policy_for_expected_net_r": (
        "package_new_entry_authority_selected_policy_for_expected_net_r"
    ),
    "selected_policy_expected_net_calibration_status": (
        "package_new_entry_authority_selected_policy_expected_net_calibration_status"
    ),
    "selected_policy_expected_net_calibrated": (
        "package_new_entry_authority_selected_policy_expected_net_calibrated"
    ),
    "selected_policy_expected_net_calibration_required": (
        "package_new_entry_authority_selected_policy_expected_net_calibration_required"
    ),
    "selected_policy_expected_net_calibration_source": (
        "package_new_entry_authority_selected_policy_expected_net_calibration_source"
    ),
    "selected_policy_expected_net_calibration_source_boundary": (
        "package_new_entry_authority_selected_policy_expected_net_calibration_source_boundary"
    ),
    "selected_policy_expected_net_calibration_hash": (
        "package_new_entry_authority_selected_policy_expected_net_calibration_hash"
    ),
    "package_replay_order_executable_candidate_use_allowed": (
        "package_new_entry_authority_package_replay_order_executable_candidate_use_allowed"
    ),
    "package_replay_order_executable_candidate_use_allowed_reason": (
        "package_new_entry_authority_package_replay_order_executable_candidate_use_allowed_reason"
    ),
    "package_replay_order_executable_authority_source": (
        "package_new_entry_authority_package_replay_order_executable_authority_source"
    ),
}


def package_new_entry_authority_payload_atom_reasons(
    payload: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    for atom_class, fields in PACKAGE_NEW_ENTRY_AUTHORITY_REQUIRED_PAYLOAD_ATOMS.items():
        for field in fields:
            if field not in payload:
                reasons.append(
                    f"package_new_entry_authority_payload_atom_missing:{atom_class}:{field}"
                )
                continue
            value = payload.get(field)
            invalid = False
            if field in PACKAGE_NEW_ENTRY_AUTHORITY_REQUIRED_SEQUENCE_ATOMS:
                invalid = not isinstance(value, list)
            elif field in PACKAGE_NEW_ENTRY_AUTHORITY_REQUIRED_BOOLEAN_ATOMS:
                invalid = not isinstance(value, bool)
            elif field in PACKAGE_NEW_ENTRY_AUTHORITY_REQUIRED_NUMERIC_ATOMS:
                invalid = (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                )
            elif field == "candidate_decision_quality_field_sources":
                invalid = not isinstance(value, Mapping) or not value
            elif field not in PACKAGE_NEW_ENTRY_AUTHORITY_EMPTY_POLICY_ATOMS:
                invalid = value in (None, "", [], {})
            if invalid:
                reasons.append(
                    f"package_new_entry_authority_payload_atom_invalid:{atom_class}:{field}"
                )
    return reasons


def package_new_entry_authority_claim_present(surface: Mapping[str, Any]) -> bool:
    return any(
        surface.get(field) not in (None, "", [], {})
        for field in (
            "package_new_entry_authority_payload",
            "package_new_entry_authority_payload_contract",
            "package_new_entry_authority_hash_sha256",
            "expected_package_new_entry_authority_hash_sha256",
            "package_new_entry_authority_status",
        )
    ) or surface.get("package_new_entry_authority_valid") is not None or any(
        str(field).startswith("package_new_entry_authority_")
        for field in surface
    ) or any(
        field in surface
        for field in ("allowed", "applies", "authority_family", "authority_source")
    )


def package_new_entry_authority_surfaces(
    row: Mapping[str, Any],
) -> list[tuple[str, Mapping[str, Any]]]:
    surfaces: list[tuple[str, Mapping[str, Any]]] = []
    for field in PACKAGE_NEW_ENTRY_AUTHORITY_SURFACE_FIELDS:
        surface = row.get(field)
        if isinstance(surface, Mapping) and package_new_entry_authority_claim_present(surface):
            surfaces.append((field, surface))
    if package_new_entry_authority_claim_present(row):
        surfaces.append(("root", row))
    return surfaces


def canonical_json_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def package_new_entry_authority_surface_reasons(
    surface: Mapping[str, Any],
    *,
    identity_row: Mapping[str, Any],
    action_intent: str | None = None,
) -> list[str]:
    reasons: list[str] = []
    if surface.get("package_new_entry_authority_required") is not True:
        reasons.append("package_new_entry_authority_required_missing_or_false")
    if surface.get("package_new_entry_authority_valid") is not True:
        reasons.append("package_new_entry_authority_valid_missing_or_false")
    if text(surface.get("package_new_entry_authority_status")) != PACKAGE_NEW_ENTRY_AUTHORITY_VALID_STATUS:
        reasons.append("package_new_entry_authority_status_not_valid")
    failures = as_list(surface.get("package_new_entry_authority_failures"))
    if failures:
        reasons.append("package_new_entry_authority_failures_present")

    payload = surface.get("package_new_entry_authority_payload")
    if not isinstance(payload, Mapping):
        return list(dict.fromkeys([*reasons, "package_new_entry_authority_payload_missing"]))
    if surface.get("package_new_entry_authority_payload_contract") != (
        PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
    ):
        reasons.append("package_new_entry_authority_payload_contract_invalid")
    if payload.get("payload_contract") != PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT:
        reasons.append("package_new_entry_authority_payload_contract_unbound")
    if payload.get("payload_schema") != PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA:
        reasons.append("package_new_entry_authority_payload_schema_invalid")
    reasons.extend(package_new_entry_authority_payload_atom_reasons(payload))
    reasons.extend(
        "package_new_entry_authority_payload_contract:"
        + failure
        for failure in package_new_entry_authority_required_payload_atom_failures(
            payload
        )
    )

    computed_hash = package_new_entry_authority_payload_hash_sha256(payload)
    authority_hash = text(surface.get("package_new_entry_authority_hash_sha256"))
    expected_hash = text(
        surface.get("expected_package_new_entry_authority_hash_sha256")
    )
    if len(authority_hash) != 64 or authority_hash != computed_hash:
        reasons.append("package_new_entry_authority_payload_hash_mismatch")
    if len(expected_hash) != 64 or expected_hash != computed_hash:
        reasons.append("expected_package_new_entry_authority_payload_hash_mismatch")

    payload_action = text(payload.get("target_action_intent"))
    expected_action = text(action_intent) or payload_action
    if not payload_action or payload_action != expected_action:
        reasons.append("package_new_entry_authority_payload_action_intent_mismatch")
    if payload.get("scope") != package_new_entry_authority_scope_for_action_intent(
        expected_action
    ):
        reasons.append("package_new_entry_authority_payload_scope_invalid")
    candidate_id = text(payload.get("candidate_id"))
    decision_time = text(payload.get("decision_time_utc"))
    instance_key = f"{candidate_id}@@{decision_time}" if candidate_id and decision_time else ""
    if (
        not instance_key
        or payload.get("canonical_replay_candidate_instance_key") != instance_key
        or payload.get("source_bound_replay_candidate_instance_key") != instance_key
        or text(payload.get("candidate_instance_identity_status")) != "materialized"
    ):
        reasons.append("package_new_entry_authority_payload_identity_invalid")
    for field in (
        "candidate_id",
        "decision_time_utc",
        "canonical_replay_candidate_instance_key",
        "source_bound_replay_candidate_instance_key",
    ):
        current_value = identity_row.get(field)
        if current_value not in (None, "", [], {}) and str(current_value) != str(
            payload.get(field) or ""
        ):
            reasons.append(f"package_new_entry_authority_payload_{field}_mismatch")

    source_boundary = norm(payload.get("source_boundary"))
    if "predecision" not in source_boundary or "no_outcome" not in source_boundary:
        reasons.append("package_new_entry_authority_payload_source_boundary_invalid")
    if payload.get("uses_outcome_fields") is not False:
        reasons.append("package_new_entry_authority_payload_uses_outcome_fields")
    if payload.get("authority_applies") is not True:
        reasons.append("package_new_entry_authority_payload_authority_not_applied")
    if payload.get("authority_allowed") is not True:
        reasons.append("package_new_entry_authority_payload_authority_not_allowed")
    if payload.get("source_bound_package_candidate_use_allowed") is not True:
        reasons.append("package_new_entry_authority_payload_source_bound_not_allowed")

    quality_sources = payload.get("candidate_decision_quality_field_sources")
    quality_sources = quality_sources if isinstance(quality_sources, Mapping) else {}
    for field in ("expected_net_r", "probability", "fill_probability", "source_completeness"):
        if not text(quality_sources.get(field)):
            reasons.append(
                f"package_new_entry_authority_payload_quality_source_missing:{field}"
            )
    if payload.get("candidate_decision_quality_alias_status") != "exact_materialized":
        reasons.append("package_new_entry_authority_payload_quality_alias_not_exact")
    if as_list(payload.get("candidate_decision_quality_alias_mismatches")):
        reasons.append("package_new_entry_authority_payload_quality_alias_mismatches_present")
    if as_list(payload.get("candidate_decision_quality_provenance_failures")):
        reasons.append("package_new_entry_authority_payload_quality_provenance_failures_present")
    if upper(payload.get("pretrade_cost_packet_status")) != "PASSED":
        reasons.append("package_new_entry_authority_payload_cost_status_not_passed")
    if payload.get("cost_source_gap_status") != "source_bound_cost_authority_present":
        reasons.append("package_new_entry_authority_payload_cost_source_gap")
    if payload.get("cost_authority") != "broker_calibrated_replay_cost":
        reasons.append("package_new_entry_authority_payload_cost_authority_invalid")
    if payload.get("candidate_cost_r_fallback_is_authority") is not False:
        reasons.append("package_new_entry_authority_payload_cost_fallback_is_authority")
    if not text(payload.get("execution_fill_probability_source")):
        reasons.append("package_new_entry_authority_payload_fill_source_missing")
    if payload.get("execution_fill_probability_authority_class") != (
        PACKAGE_NEW_ENTRY_AUTHORITY_EXECUTION_FILLABILITY_CLASS
    ):
        reasons.append(
            "package_new_entry_authority_payload_fill_authority_class_invalid"
        )
    if not isinstance(
        payload.get("package_replay_order_executable_candidate_use_allowed"), bool
    ):
        reasons.append("package_new_entry_authority_payload_order_permission_invalid")

    for payload_field, projection_field in PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_PROJECTIONS.items():
        payload_value = payload.get(payload_field)
        projected_value = surface.get(projection_field)
        if payload_value in (None, "") and projected_value in (None, ""):
            continue
        if projection_field not in surface:
            reasons.append(
                f"package_new_entry_authority_payload_projection_missing:{payload_field}"
            )
        elif canonical_json_value(payload_value) != canonical_json_value(projected_value):
            reasons.append(
                f"package_new_entry_authority_payload_projection_mismatch:{payload_field}"
            )
    return list(dict.fromkeys(reasons))


def package_new_entry_authority_envelope_selection(
    row: Mapping[str, Any],
    *,
    action_intent: str | None = None,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for source, surface in package_new_entry_authority_surfaces(row):
        payload = surface.get("package_new_entry_authority_payload")
        payload = payload if isinstance(payload, Mapping) else {}
        reasons = package_new_entry_authority_surface_reasons(
            surface,
            identity_row=row,
            action_intent=action_intent,
        )
        records.append(
            {
                "source": source,
                "surface": surface,
                "payload": payload,
                "digest": (
                    package_new_entry_authority_payload_hash_sha256(payload)
                    if payload
                    else ""
                ),
                "valid": not reasons,
                "reasons": reasons,
            }
        )
    valid_records = [record for record in records if record["valid"]]
    valid_digests = {record["digest"] for record in valid_records}
    if len(valid_digests) > 1:
        return {
            "valid": False,
            "status": "conflicting_current_authority_envelopes",
            "reasons": ["multiple_distinct_current_authority_envelopes"],
            "records": records,
        }
    if valid_records:
        selected = valid_records[0]
        conflicting_payloads = {
            record["digest"]
            for record in records
            if record["payload"] and record["digest"] != selected["digest"]
        }
        if conflicting_payloads:
            return {
                "valid": False,
                "status": "conflicting_current_authority_envelopes",
                "reasons": ["mixed_current_authority_envelope_payloads"],
                "records": records,
            }
        return {
            **selected,
            "status": "single_current_schema_immutable_envelope",
            "records": records,
            "valid_sources": [record["source"] for record in valid_records],
        }
    reasons = [
        f"{record['source']}:{reason}"
        for record in records
        for reason in record["reasons"]
    ]
    return {
        "valid": False,
        "status": (
            "legacy_or_hash_only_authority_diagnostic_only"
            if records
            else "authority_envelope_missing"
        ),
        "reasons": reasons or ["package_new_entry_authority_envelope_missing"],
        "records": records,
    }


def compact_package_new_entry_authority_envelope_selection(
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    """Retain cross-stage envelope truth without retaining source rows."""

    compact_records: list[dict[str, Any]] = []
    for record in selection.get("records") or []:
        if not isinstance(record, Mapping):
            continue
        compact_records.append(
            {
                "source": text(record.get("source")),
                "digest": text(record.get("digest")),
                "valid": record.get("valid") is True,
                "reasons": list(record.get("reasons") or []),
            }
        )
    payload = selection.get("payload")
    payload = payload if isinstance(payload, Mapping) else {}
    surface = selection.get("surface")
    surface = surface if isinstance(surface, Mapping) else {}
    return {
        "valid": selection.get("valid") is True,
        "status": text(selection.get("status")),
        "source": text(selection.get("source")),
        "digest": text(selection.get("digest")),
        "reasons": list(selection.get("reasons") or []),
        "payload": {
            field: payload.get(field)
            for field in (
                "selector_action",
                "selector_reason",
                "package_replay_order_executable_candidate_use_allowed",
                "package_replay_order_executable_candidate_use_allowed_reason",
            )
            if field in payload
        },
        "surface": {
            "package_new_entry_authority_status": surface.get(
                "package_new_entry_authority_status"
            )
        }
        if "package_new_entry_authority_status" in surface
        else {},
        "records": compact_records,
        "valid_sources": string_list(selection.get("valid_sources")),
    }


def candidate_decision_quality_envelope(fields: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical nested quality object; flat fields remain compatibility API."""

    existing = fields.get("candidate_decision_quality")
    envelope = dict(existing) if isinstance(existing, Mapping) else {}
    scalar_aliases = {
        "expected_net_r": ("expected_net_r", "candidate_expected_net_r"),
        "candidate_expected_net_r": ("candidate_expected_net_r", "expected_net_r"),
        "probability": ("probability", "candidate_probability"),
        "candidate_probability": ("candidate_probability", "probability"),
        "confidence": ("confidence", "candidate_confidence", "scheduler_confidence"),
        "candidate_confidence": (
            "candidate_confidence",
            "confidence",
            "scheduler_confidence",
        ),
        "fill_probability": ("fill_probability", "candidate_fill_probability"),
        "candidate_fill_probability": ("candidate_fill_probability", "fill_probability"),
        "source_completeness": (
            "source_completeness",
            "candidate_source_completeness",
        ),
        "source_completeness_status": (
            "source_completeness_status",
            "candidate_source_completeness_status",
        ),
        "expected_cost_r": (
            "expected_cost_r",
            "predecision_expected_cost_r",
            "cost_total_r",
            "cost_r",
        ),
        "cost_total_r": ("cost_total_r", "expected_cost_r", "cost_r"),
        "cost_r": ("cost_r", "expected_cost_r", "cost_total_r"),
        "source_boundary": (
            "source_boundary",
            "candidate_decision_quality_source_boundary",
        ),
        "selected_policy_for_expected_net_r": (
            "selected_policy_for_expected_net_r",
            "expected_net_r_selected_policy",
            "dynamic_geometry_policy",
        ),
        "selected_policy_expected_net_r": (
            "selected_policy_expected_net_r",
            "expected_net_r",
            "candidate_expected_net_r",
        ),
        "selected_policy_probability": (
            "selected_policy_probability",
            "probability",
            "candidate_probability",
        ),
        "selected_policy_source_completeness": (
            "selected_policy_source_completeness",
            "source_completeness",
            "candidate_source_completeness",
        ),
        "selected_policy_quality_alias_status": (
            "selected_policy_quality_alias_status",
        ),
        "selected_policy_quality_source_boundary": (
            "selected_policy_quality_source_boundary",
            "candidate_decision_quality_source_boundary",
            "source_boundary",
        ),
        "selected_policy_expected_net_calibration_status": (
            "selected_policy_expected_net_calibration_status",
            "selected_policy_expected_net_r_calibration_status",
        ),
        "selected_policy_expected_net_calibrated": (
            "selected_policy_expected_net_calibrated",
        ),
        "selected_policy_expected_net_calibration_required": (
            "selected_policy_expected_net_calibration_required",
        ),
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_expected_net_calibration_source",
            "selected_policy_expected_net_r_calibration_source",
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "selected_policy_expected_net_calibration_source_boundary",
            "selected_policy_expected_net_calibration_boundary",
        ),
        "selected_policy_expected_net_assumption_hash": (
            "selected_policy_expected_net_assumption_hash",
            "selected_policy_expected_net_r_assumption_hash",
            "selected_policy_expected_net_calibration_hash",
        ),
    }
    for out_key, candidates in scalar_aliases.items():
        value = first_present(*(fields.get(key) for key in candidates))
        if not missing_value(value):
            envelope[out_key] = value
    field_sources = first_present(
        fields.get("candidate_decision_quality_field_sources"),
        fields.get("field_sources"),
        envelope.get("field_sources"),
    )
    if isinstance(field_sources, Mapping):
        envelope["field_sources"] = dict(field_sources)
        envelope["candidate_decision_quality_field_sources"] = dict(field_sources)
    for out_key, candidates in {
        "alias_status": ("candidate_decision_quality_alias_status", "alias_status"),
        "alias_mismatches": (
            "candidate_decision_quality_alias_mismatches",
            "alias_mismatches",
        ),
        "provenance_failures": (
            "candidate_decision_quality_provenance_failures",
            "provenance_failures",
        ),
        "source_boundary": (
            "candidate_decision_quality_source_boundary",
            "source_boundary",
        ),
    }.items():
        value = first_present(*(fields.get(key) for key in candidates))
        if not missing_value(value):
            envelope[out_key] = list(value) if isinstance(value, tuple) else value
            if out_key == "source_boundary":
                envelope["candidate_decision_quality_source_boundary"] = value
    return {
        key: value
        for key, value in envelope.items()
        if not missing_value(value)
    }


ROUTE_PROVENANCE_KEYS = (
    "framework",
    "current_framework",
    "origin_family",
    "candidate_origin_family",
    "route_family",
    "route_session",
    "session",
    "session_bucket",
    "setup_family",
    "dynamic_geometry_policy",
)


def route_provenance_fields(*rows: Mapping[str, Any] | None) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for key in ROUTE_PROVENANCE_KEYS:
        value = None
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            value = first_present(
                row.get(key),
                row.get(f"candidate_{key}"),
                row.get(f"risk_finalizer_{key}"),
                row.get(f"finalizer_primary_probe_{key}"),
            )
            if not missing_value(value):
                break
        if not missing_value(value):
            fields[key] = value
    if "current_framework" not in fields and not missing_value(fields.get("framework")):
        fields["current_framework"] = fields["framework"]
    if "route_session" not in fields:
        route_session = first_present(fields.get("session"), fields.get("session_bucket"))
        if not missing_value(route_session):
            fields["route_session"] = route_session
    if "session_bucket" not in fields:
        session_bucket = first_present(fields.get("route_session"), fields.get("session"))
        if not missing_value(session_bucket):
            fields["session_bucket"] = session_bucket
    if "session" not in fields:
        session = first_present(fields.get("session_bucket"), fields.get("route_session"))
        if not missing_value(session):
            fields["session"] = session
    return fields


def source_completeness_executable_block_reason(row: Mapping[str, Any]) -> str | None:
    raw_value = row.get("source_completeness")
    if raw_value in (None, ""):
        return "source_completeness_missing"
    source_completeness = safe_float(raw_value, default=-1.0)
    if source_completeness < MIN_EXECUTABLE_SOURCE_COMPLETENESS:
        return f"source_completeness_below_floor:{source_completeness:.3f}"
    source_status = text(row.get("source_completeness_status"))
    source_status_lower = source_status.lower()
    if any(token in source_status_lower for token in SOURCE_COMPLETENESS_BLOCKED_STATUS_TOKENS):
        return f"source_completeness_status_not_executable:{source_status_lower}"
    return None


ROUTER_REFUSAL_AUTHORITY_FAMILIES = {
    "router_refusal_softening",
    "source_bound_router_refusal_materialization",
    "source_bound_router_refusal_replay_materialization",
}


def explicit_package_authority_family(row: Mapping[str, Any]) -> str:
    authority = row.get("ultimate_candidate_package_open_reduced_risk_authority")
    authority = authority if isinstance(authority, Mapping) else {}
    return text(
        row.get("package_new_entry_authority_authority_family")
        or row.get("package_open_reduced_authority_family")
        or authority.get("package_new_entry_authority_authority_family")
        or authority.get("authority_family")
    )


def source_bound_router_refusal_materialization_applies(row: Mapping[str, Any]) -> bool:
    authority_family = explicit_package_authority_family(row)
    if authority_family and authority_family not in ROUTER_REFUSAL_AUTHORITY_FAMILIES:
        return False
    if authority_family in {
        "source_bound_router_refusal_materialization",
        "source_bound_router_refusal_replay_materialization",
    }:
        return True
    selector_reason = text(row.get("selector_reason"))
    authority_reason = text(row.get("package_new_entry_authority_selector_reason"))
    authority_source = text(
        row.get("authority_source")
        or row.get("package_new_entry_authority_authority_source")
    )
    authority = row.get("ultimate_candidate_package_open_reduced_risk_authority")
    authority = authority if isinstance(authority, Mapping) else {}
    nested_reason = text(
        authority.get("selector_reason")
        or authority.get("original_selector_reason")
        or authority.get("authority_reason")
        or authority.get("package_new_entry_authority_selector_reason")
    )
    nested_source = text(
        authority.get("authority_source")
        or authority.get("package_new_entry_authority_authority_source")
    )
    return bool(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
        in {selector_reason, authority_reason, nested_reason}
        or "derived_from_source_bound_router_refusal_package_authority"
        in {authority_source, nested_source}
    )


def scheduler_materialization_skip_is_soft_transfer(
    row: Mapping[str, Any],
    skip_reason: str,
) -> bool:
    """Allow only self-referential scheduler/materialization skips past B7 gates."""

    reason = skip_reason.strip().lower()
    if not reason:
        return False
    if row.get("package_replay_order_executable_candidate_use_allowed") is False:
        return False
    if any(token in reason for token in SCHEDULER_MATERIALIZATION_TERMINAL_SKIP_TOKENS):
        return False
    has_soft_skip_shape = any(
        token in reason for token in SCHEDULER_MATERIALIZATION_SOFT_TRANSFER_SKIP_TOKENS
    )
    if not has_soft_skip_shape:
        return False
    blocker_class = text(row.get("package_replay_order_executable_final_blocker_class"))
    if (
        row.get("package_replay_order_executable_candidate_use_allowed") is True
        and blocker_class in {"scheduler_selection", "selector_materialization"}
    ):
        return True
    soft_guard_contract = row.get("scheduler_terminal_vs_soft_guard")
    soft_guard_contract = soft_guard_contract if isinstance(soft_guard_contract, Mapping) else {}
    soft_vetoes = (
        string_list(row.get("reallocation_soft_guard_vetoes"))
        or string_list(row.get("scheduler_reallocation_soft_guard_vetoes"))
        or string_list(soft_guard_contract.get("soft_guard_vetoes"))
    )
    terminal_vetoes = (
        string_list(row.get("terminal_vetoes"))
        or string_list(row.get("scheduler_terminal_vetoes"))
        or string_list(row.get("reallocation_soft_guard_pool_terminal_vetoes"))
        or string_list(soft_guard_contract.get("terminal_vetoes"))
    )
    pool_status = text(
        row.get("reallocation_soft_guard_pool_status")
        or soft_guard_contract.get("pool_status")
    ).lower()
    pool_eligible = value_truthy(
        first_present(
            row.get("reallocation_soft_guard_pool_eligible"),
            soft_guard_contract.get("pool_eligible"),
        )
    )
    return bool(
        pool_eligible
        and soft_vetoes
        and not terminal_vetoes
        and pool_status in {"", "eligible"}
    )


def signed_package_new_entry_authority_block_reason(
    row: Mapping[str, Any],
    *,
    action_intent: str,
) -> str | None:
    envelope = package_new_entry_authority_envelope_selection(
        row,
        action_intent=action_intent,
    )
    if envelope.get("valid") is not True:
        reasons = list(envelope.get("reasons") or [])
        return "immutable_authority_envelope_invalid:" + (
            reasons[0] if reasons else text(envelope.get("status"), "unknown")
        )
    surface = envelope.get("surface")
    surface = surface if isinstance(surface, Mapping) else {}
    payload = envelope.get("payload")
    payload = payload if isinstance(payload, Mapping) else {}
    authority_bound_row = dict(row)
    authority_bound_row.update(surface)
    for field in (
        "expected_net_r",
        "probability",
        "fill_probability",
        "source_completeness",
        "source_completeness_status",
        "pretrade_cost_packet_status",
        "cost_source_gap_status",
        "cost_authority",
        "candidate_cost_r_fallback_is_authority",
        "execution_fill_probability",
        "execution_fill_probability_source",
        "entry_quality_fill_probability",
        "limit_fillability_probability",
        "predecision_limit_fillability_probability",
    ):
        if field in payload:
            authority_bound_row[field] = payload.get(field)
    row = authority_bound_row
    if row.get("package_new_entry_authority_required") is not True:
        return "package_new_entry_authority_required_missing_or_false"
    if row.get("package_new_entry_authority_valid") is not True:
        status = text(row.get("package_new_entry_authority_status") or "missing")
        return f"package_new_entry_authority_invalid:{status}"
    failures = as_list(row.get("package_new_entry_authority_failures"))
    if failures:
        return "package_new_entry_authority_failures_present"
    authority_hash = text(row.get("package_new_entry_authority_hash_sha256"))
    expected_hash = text(row.get("expected_package_new_entry_authority_hash_sha256"))
    if not authority_hash:
        return "package_new_entry_authority_hash_missing"
    if not expected_hash:
        return "expected_package_new_entry_authority_hash_missing"
    if authority_hash != expected_hash:
        return "package_new_entry_authority_hash_mismatch"
    if text(row.get("package_new_entry_authority_status")) != PACKAGE_NEW_ENTRY_AUTHORITY_VALID_STATUS:
        return "package_new_entry_authority_status_not_valid"
    target_action = text(row.get("package_new_entry_authority_target_action_intent"))
    if target_action != action_intent:
        return "package_new_entry_authority_target_action_intent_mismatch"
    source_boundary = text(row.get("package_new_entry_authority_source_boundary")).lower()
    if "predecision" not in source_boundary or "no_outcome" not in source_boundary:
        return "package_new_entry_authority_source_boundary_not_predecision_no_outcome"
    if row.get("package_new_entry_authority_uses_outcome_fields") is True:
        return "package_new_entry_authority_uses_outcome_fields"
    authority_family = explicit_package_authority_family(row)
    selector_reason = text(row.get("selector_reason"))
    authority_reason = text(row.get("package_new_entry_authority_selector_reason"))
    router_refusal_reasons = {
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
        "source_bound_router_refusal_open_reduced_materialized_for_replay",
    }
    if authority_family and authority_family not in ROUTER_REFUSAL_AUTHORITY_FAMILIES:
        return None
    if (
        authority_family in ROUTER_REFUSAL_AUTHORITY_FAMILIES
        or selector_reason in router_refusal_reasons
        or authority_reason in router_refusal_reasons
    ):
        if source_bound_router_refusal_materialization_applies(row):
            min_expected_net_r = SOURCE_BOUND_ROUTER_REFUSAL_MIN_EXPECTED_NET_R
            min_probability = SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY
            min_fill_probability = SOURCE_BOUND_ROUTER_REFUSAL_MIN_FILL_PROBABILITY
            min_source_completeness = SOURCE_BOUND_ROUTER_REFUSAL_MIN_SOURCE_COMPLETENESS
        else:
            min_expected_net_r = ROUTER_REFUSAL_MIN_EXPECTED_NET_R
            min_probability = ROUTER_REFUSAL_MIN_PROBABILITY
            min_fill_probability = ROUTER_REFUSAL_MIN_FILL_PROBABILITY
            min_source_completeness = ROUTER_REFUSAL_MIN_SOURCE_COMPLETENESS
        expected_net_r = safe_float(
            row.get("expected_net_r") or row.get("candidate_expected_net_r"),
            default=-1.0,
        )
        probability = safe_float(
            row.get("probability") or row.get("candidate_probability"),
            default=-1.0,
        )
        fill_probability, _fill_source = execution_fillability_authority(row)
        fill_probability = -1.0 if fill_probability is None else fill_probability
        source_completeness = safe_float(row.get("source_completeness"), default=-1.0)
        if expected_net_r < min_expected_net_r:
            return "router_refusal_expected_net_r_below_floor"
        if probability < min_probability:
            return "router_refusal_probability_below_floor"
        if fill_probability < min_fill_probability:
            return "router_refusal_fill_probability_below_floor"
        if source_completeness < min_source_completeness:
            return "router_refusal_source_completeness_below_floor"
    return None


def replay_executable_package_use_detail(
    row: Mapping[str, Any],
    *,
    source_bound_allowed: Any,
    package_replay_allowed: Any,
) -> tuple[bool, str]:
    """Split source-bound membership from executable replay package authority."""

    if not source_bound_allowed or not package_replay_allowed:
        return False, "source_bound_package_replay_not_allowed"
    effective_allowed = row.get("ultimate_package_effective_source_bound_candidate_use_allowed")
    if effective_allowed is False:
        return False, "ultimate_package_effective_source_bound_not_allowed"
    effective_admission_count = row.get("ultimate_package_effective_admission_count")
    if effective_admission_count not in (None, "") and safe_float(effective_admission_count) <= 0.0:
        return False, "ultimate_package_effective_admission_count_zero"
    action_hint = text(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
    )
    selector_hint = effective_selector_action(row)
    signed_reduced_new_entry_required = bool(
        (
            selector_hint == "reduce-risk"
            and action_hint not in SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS
        )
        or (
            selector_hint == "open-reduced-risk"
            and action_hint in REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS
        )
    )
    immutable_order_authority_valid = False
    authority_surfaces = package_new_entry_authority_surfaces(row)
    if authority_surfaces:
        envelope = package_new_entry_authority_envelope_selection(
            row,
            action_intent=action_hint or None,
        )
        if envelope.get("valid") is not True:
            if signed_reduced_new_entry_required:
                return False, text(
                    envelope.get("status"),
                    "legacy_or_hash_only_authority_diagnostic_only",
                )
        else:
            payload = envelope.get("payload")
            payload = payload if isinstance(payload, Mapping) else {}
            if payload.get("package_replay_order_executable_candidate_use_allowed") is not True:
                return False, text(
                    payload.get(
                        "package_replay_order_executable_candidate_use_allowed_reason"
                    ),
                    "immutable_authority_order_permission_false",
                )
            surface = envelope.get("surface")
            surface = surface if isinstance(surface, Mapping) else {}
            authority_bound_row = dict(row)
            authority_bound_row.update(surface)
            for field in (
                "pretrade_cost_packet_status",
                "cost_source_gap_status",
                "cost_authority",
                "candidate_cost_r_fallback_is_authority",
                "source_completeness",
                "source_completeness_status",
                "execution_fill_probability",
                "execution_fill_probability_source",
                "entry_quality_fill_probability",
                "limit_fillability_probability",
                "predecision_limit_fillability_probability",
                "package_replay_order_executable_candidate_use_allowed",
                "package_replay_order_executable_candidate_use_allowed_reason",
                "package_replay_order_executable_authority_source",
            ):
                if field in payload:
                    authority_bound_row[field] = payload.get(field)
            row = authority_bound_row
            immutable_order_authority_valid = True
    cost_status = upper(row.get("pretrade_cost_packet_status"))
    if not cost_status:
        return False, "broker_cost_packet_status_missing"
    if cost_status == "REFUSED":
        return False, "broker_cost_packet_refused"
    if cost_status != "PASSED":
        return False, f"broker_cost_packet_not_passed:{cost_status}"
    cost_authority = text(
        row.get("cost_authority") or row.get("pretrade_cost_packet_authority")
    )
    if not cost_authority:
        return False, "broker_cost_authority_missing"
    if cost_authority != "broker_calibrated_replay_cost":
        return False, f"broker_cost_authority_unexpected:{cost_authority}"
    cost_source_gap_status = text(row.get("cost_source_gap_status"))
    if not cost_source_gap_status:
        return False, "broker_cost_source_gap_status_missing"
    if cost_source_gap_status != "source_bound_cost_authority_present":
        return False, f"broker_cost_source_gap_not_executable:{cost_source_gap_status}"
    if bool(row.get("source_gap_cost_fallback_blocked")):
        return False, "source_gap_cost_fallback_blocked"
    if bool(row.get("candidate_cost_r_fallback_is_authority")):
        return False, "candidate_cost_r_fallback_not_order_authority"
    source_block_reason = source_completeness_executable_block_reason(row)
    if source_block_reason:
        return False, source_block_reason
    package_geometry_flag = row.get("package_authority_has_order_geometry")
    package_geometry_status = text(row.get("package_authority_order_geometry_status"))
    entry_price = safe_float(row.get("entry_price"))
    stop_loss = safe_float(row.get("stop_loss"))
    target_price = safe_float(
        row.get("take_profit_1")
        or row.get("take_profit")
        or row.get("target_price")
    )
    has_order_geometry = bool(entry_price and stop_loss and target_price)
    if package_geometry_flag is False:
        return False, "package_authority_candidate_missing_entry_stop_target_geometry"
    if (
        package_geometry_status
        == "package_authority_candidate_missing_entry_stop_target_geometry"
    ):
        return False, "package_authority_candidate_missing_entry_stop_target_geometry"
    if row.get("selected_package_replay_row") is True and not has_order_geometry:
        return False, "selected_package_replay_row_missing_entry_stop_target_geometry"
    scheduler_skip_reason = text(row.get("scheduler_materialization_skip_reason"))
    if scheduler_skip_reason and not scheduler_materialization_skip_is_soft_transfer(
        row,
        scheduler_skip_reason,
    ):
        return False, f"scheduler_materialization_skipped:{scheduler_skip_reason}"
    action_intent = text(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
    )
    if not action_intent:
        return False, "scheduler_materialization_action_intent_missing"
    if action_intent.startswith("invalid_action_intent:"):
        return False, f"scheduler_materialization_invalid_action:{action_intent}"
    if action_intent not in EXECUTABLE_SCHEDULER_ACTION_INTENTS:
        return False, f"scheduler_materialization_action_intent_unknown:{action_intent}"
    if immutable_order_authority_valid:
        return True, "broker_cost_selector_and_scheduler_action_executable"
    pre_fill_action_intent = text(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
    )
    pre_fill_selector_action = effective_selector_action(row)
    if (
        pre_fill_selector_action == "reduce-risk"
        and pre_fill_action_intent not in SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS
    ):
        block_reason = signed_package_new_entry_authority_block_reason(
            row,
            action_intent=pre_fill_action_intent,
        )
        if block_reason:
            return False, f"selector_reduce_risk_new_entry_authority:{block_reason}"
    if (
        pre_fill_selector_action == "open-reduced-risk"
        and pre_fill_action_intent in REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS
    ):
        block_reason = signed_package_new_entry_authority_block_reason(
            row,
            action_intent=pre_fill_action_intent,
        )
        if block_reason:
            return False, (
                "selector_open_reduced_risk_new_entry_authority:"
                f"{block_reason}"
            )
    fill_probability, fill_probability_source = execution_fillability_authority(row)
    if fill_probability is None:
        return False, EXECUTION_FILLABILITY_MISSING_SOURCE
    if fill_probability < MIN_EXECUTABLE_FILL_PROBABILITY:
        return False, (
            f"execution_fillability_below_floor:{fill_probability:.3f}:"
            f"{fill_probability_source}"
        )
    if package_geometry_flag is False:
        return False, "package_authority_candidate_missing_entry_stop_target_geometry"
    if (
        package_geometry_status
        == "package_authority_candidate_missing_entry_stop_target_geometry"
    ):
        return False, "package_authority_candidate_missing_entry_stop_target_geometry"
    if row.get("selected_package_replay_row") is True and not has_order_geometry:
        return False, "selected_package_replay_row_missing_entry_stop_target_geometry"
    selector_action = effective_selector_action(row)
    replay_override_applied = bool(
        row.get("scheduler_materialization_source_required_selector_hold_override_applied")
        or row.get("scheduler_materialization_source_required_fail_closed_override_applied")
    )
    if not selector_action:
        return False, "selector_action_missing"
    if selector_action and selector_action not in {
        "trade",
        "reduce-risk",
        "open-reduced-risk",
    } and not replay_override_applied:
        return False, "selector_not_risk_bearing"
    if (
        selector_action == "reduce-risk"
        and action_intent not in SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS
    ):
        block_reason = signed_package_new_entry_authority_block_reason(
            row,
            action_intent=action_intent,
        )
        if block_reason:
            return False, f"selector_reduce_risk_new_entry_authority:{block_reason}"
    if (
        selector_action == "open-reduced-risk"
        and action_intent in REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS
    ):
        block_reason = signed_package_new_entry_authority_block_reason(
            row,
            action_intent=action_intent,
        )
        if block_reason:
            return False, (
                "selector_open_reduced_risk_new_entry_authority:"
                f"{block_reason}"
            )
    if (
        selector_action == "open-reduced-risk"
        and action_intent not in SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS
    ):
        return False, (
            "selector_open_reduced_risk_action_intent_not_order_authority:"
            f"{action_intent}"
        )
    return True, "broker_cost_selector_and_scheduler_action_executable"


def add(current: Any, value: Any) -> float:
    return round(safe_float(current) + safe_float(value), 10)


def pct(part: Any, whole: Any) -> float | None:
    whole_float = safe_float(whole, 0.0)
    if abs(whole_float) <= 1e-12:
        return None
    return round((safe_float(part, 0.0) / whole_float) * 100.0, 6)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return [value]


def string_list(value: Any) -> list[str]:
    return [str(item) for item in as_list(value) if text(item)]


def parse_utc(value: Any) -> datetime | None:
    raw = text(value)
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


SESSION_ALIAS_MAP: dict[str, tuple[str, ...]] = {
    "tokyo": ("tokyo_broad",),
    "tokyo_broad": ("tokyo",),
    "london": ("london_broad",),
    "london_broad": ("london",),
    "ny": ("ny_broad", "new_york"),
    "new_york": ("ny", "ny_broad"),
    "ny_broad": ("ny", "new_york"),
    "off_configured": ("off_configured_session", "off_kz_broad"),
    "off_configured_session": ("off_configured", "off_kz_broad"),
    "off_kz_broad": ("off_configured", "off_configured_session"),
}


def session_aliases(values: Iterable[Any]) -> set[str]:
    """Return symmetric aliases for broad/source session namespace joins."""

    aliases: set[str] = set()
    for value in values:
        raw = text(value)
        if not raw:
            continue
        candidates = {raw, raw.lower()}
        for candidate in list(candidates):
            candidates.update(utc_hour_bucket_aliases(candidate))
            if candidate.startswith("moonshot_h"):
                candidates.add(candidate.removeprefix("moonshot_"))
            candidates.update(SESSION_ALIAS_MAP.get(candidate, ()))
        aliases.update(candidates)
    return aliases


def session_tokens(row: Mapping[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for key in ("session_bucket", "session", "route_session", "utc_hour_bucket"):
        raw = text(row.get(key))
        if raw:
            tokens.add(raw)
            tokens.update(utc_hour_bucket_aliases(raw))
            if raw.startswith("moonshot_h"):
                tokens.add(raw.removeprefix("moonshot_"))
    parsed = parse_utc(
        row.get("decision_time_utc")
        or row.get("asof_utc")
        or row.get("timestamp_utc")
    )
    if parsed is not None:
        hour = parsed.hour
        tokens.add(f"h{hour:02d}_{(hour + 1) % 24:02d}")
        tokens.add(f"moonshot_h{hour:02d}_{(hour + 1) % 24:02d}")
        if 0 <= hour < 7:
            tokens.add("tokyo_broad")
        elif 7 <= hour < 12:
            tokens.add("london_broad")
        elif 12 <= hour < 17:
            tokens.add("ny_broad")
        else:
            tokens.add("off_kz_broad")
    return session_aliases(tokens)


def wildcard(value: Any) -> bool:
    return norm(value) in {"*", "all", "any", "broader_origin", "all_origins"}


def package_role_for_sleeve_type(sleeve_type: Any) -> str:
    value = text(sleeve_type)
    return {
        "scheduler_lifecycle_merge_sleeve": "scheduler_lifecycle_core",
        "promote_default_off_signal_sleeve": "promote_default_off_signal",
        "avoid_failure_feature_sleeve": "avoid_failure_feature",
        "redesign_repair_sleeve": "redesign_repair_candidate",
        "source_required_hold_sleeve": "source_required_hold",
    }.get(value, "unknown_sleeve_type")


EXECUTABLE_SOURCE_BOUND_ROLES = {
    "scheduler_lifecycle_core",
    "promote_default_off_signal",
}


def source_axis_replay_class(package_role: Any) -> str:
    role = text(package_role)
    if role in EXECUTABLE_SOURCE_BOUND_ROLES:
        return "executable_admission_axis"
    if role == "avoid_failure_feature":
        return "non_admission_failure_feature_axis"
    if role == "source_required_hold":
        return "source_required_hold_axis"
    if role == "redesign_repair_candidate":
        return "redesign_repair_axis"
    return "unknown_source_axis_role"


def axis_unmatched_diagnostic(
    axis: Mapping[str, Any],
    profile_member_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Explain why a source/member axis had no matched replay candidates."""

    axis_framework = text(axis.get("framework"))
    axis_origin = text(axis.get("origin_family"))
    axis_sessions = session_aliases(
        string_list(axis.get("session_buckets") or axis.get("session_bucket"))
    )
    if not profile_member_candidates:
        return {
            "candidate_generation_mismatch_reason": (
                "no_symbol_side_candidates_in_selected_replay_window"
            ),
            "candidate_generation_mismatch_fields": [],
            "same_symbol_side_candidate_count": 0,
            "same_symbol_side_candidate_framework_counts": {},
            "same_symbol_side_candidate_origin_counts": {},
            "same_symbol_side_candidate_session_token_counts": {},
        }

    framework_matches = [
        row
        for row in profile_member_candidates
        if (
            not axis_framework
            or not row.get("framework")
            or family_matches(axis_framework, row.get("framework"))
        )
    ]
    origin_matches = [
        row
        for row in profile_member_candidates
        if (
            not axis_origin
            or not row.get("origin_family")
            or family_matches(axis_origin, row.get("origin_family"))
        )
    ]
    session_matches = [
        row
        for row in profile_member_candidates
        if (
            not axis_sessions
            or any(wildcard(token) for token in axis_sessions)
            or axis_sessions & set(row.get("session_tokens") or [])
        )
    ]
    mismatch_fields: list[str] = []
    if not framework_matches:
        mismatch_fields.append("framework")
    if not origin_matches:
        mismatch_fields.append("origin")
    if not session_matches:
        mismatch_fields.append("session")
    reason = (
        f"mismatch_{'_'.join(mismatch_fields)}"
        if mismatch_fields
        else "candidate_namespace_tuple_mismatch"
    )
    return {
        "candidate_generation_mismatch_reason": reason,
        "candidate_generation_mismatch_fields": mismatch_fields,
        "same_symbol_side_candidate_count": len(profile_member_candidates),
        "same_symbol_side_candidate_framework_counts": top_counter(
            Counter(text(row.get("framework"), "unknown") for row in profile_member_candidates)
        ),
        "same_symbol_side_candidate_origin_counts": top_counter(
            Counter(
                text(row.get("origin_family"), "unknown")
                for row in profile_member_candidates
            )
        ),
        "same_symbol_side_candidate_session_token_counts": top_counter(
            Counter(
                text(token, "unknown")
                for row in profile_member_candidates
                for token in as_list(row.get("session_tokens"))
            )
        ),
    }


def zero_candidate_leakage_label(
    *,
    package_role: Any,
    mismatch_reason: str,
) -> str:
    role = text(package_role)
    if role in EXECUTABLE_SOURCE_BOUND_ROLES:
        if mismatch_reason == "no_symbol_side_candidates_in_selected_replay_window":
            return "executable_axis_not_observed_in_selected_replay_window"
        return f"candidate_generation_namespace_mismatch:{mismatch_reason}"
    role_label = non_executable_role_leakage_label(role)
    if role_label:
        return role_label
    return "candidate_not_generated_unknown_source_axis_role"


def non_executable_role_leakage_label(package_role: Any) -> str:
    role = text(package_role)
    if role == "avoid_failure_feature":
        return "non_admission_failure_feature_axis_no_trade_candidate_expected"
    if role == "source_required_hold":
        return "source_required_hold_not_executable_without_source"
    if role == "redesign_repair_candidate":
        return "redesign_repair_axis_not_executable_generator_authority"
    return ""


def selected_package_bridge_materialized(member: Mapping[str, Any]) -> bool:
    return (
        safe_float(member.get("selected_package_replay_bridge_candidate_rows")) > 0
        or member.get("candidate_id_carried_to_member") is True
        or member.get("decision_window_id_carried_to_member") is True
    )


def selected_package_bridge_lifecycle_context_present(member: Mapping[str, Any]) -> bool:
    if member.get("selected_package_replay_bridge_lifecycle_label_context_present") is True:
        return True
    if safe_float(member.get("selected_package_replay_bridge_lifecycle_label_context_rows")) > 0:
        return True
    if safe_float(member.get("selected_package_replay_bridge_label_window_match_count")) > 0:
        return True
    for field in (
        "pending_lifecycle_v4_state_groups",
        "fillability_label_families",
        "fill_no_fill_labels",
    ):
        if string_list(member.get(field)):
            return True
    return False


def selected_package_source_axis_lifecycle_context_available(
    member: Mapping[str, Any],
) -> bool:
    """Axis-level lifecycle context must be backed by source-axis context IDs."""

    if safe_float(member.get("source_axis_lifecycle_label_context_id_count")) > 0:
        return True
    if string_list(member.get("source_axis_lifecycle_label_context_ids")):
        return True
    return False


def selected_package_exact_denominator_join_rows(member: Mapping[str, Any]) -> int:
    return int(safe_float(member.get("exact_denominator_join_rows")))


def selected_package_lifecycle_context_attribution_scope(
    member: Mapping[str, Any],
) -> str:
    scope = text(member.get("source_axis_lifecycle_context_attribution_scope"))
    if scope:
        return scope
    if selected_package_exact_denominator_join_rows(member) > 0:
        return "bridge_exact_denominator_join"
    if selected_package_bridge_lifecycle_context_present(member):
        return "bridge_window_label_context_without_denominator_authority"
    if selected_package_source_axis_lifecycle_context_available(member):
        return "symbol_side_pair_broadcast_only"
    return "no_lifecycle_context"


def selected_package_lifecycle_window_transfer_status(
    member: Mapping[str, Any],
) -> str:
    status = text(
        member.get("source_axis_lifecycle_bridge_window_transfer_status")
        or member.get("source_materialization_transfer_status")
    )
    if status:
        return status
    if not selected_package_source_axis_lifecycle_context_available(member):
        return "no_axis_lifecycle_context"
    source_windows = set(
        string_list(member.get("source_axis_lifecycle_decision_window_id_samples"))
    )
    bridge_windows = set(
        string_list(member.get("selected_package_replay_bridge_decision_window_id_samples"))
    )
    if source_windows & bridge_windows:
        return "bridge_window_overlap"
    if not source_windows:
        return "source_window_missing"
    if not bridge_windows:
        return "bridge_window_missing"
    return "bridge_window_mismatch"


def selected_package_legacy_aggregate_lifecycle_context_present(
    member: Mapping[str, Any],
) -> bool:
    return safe_float(member.get("context_lifecycle_label_rows")) > 0


def selected_package_replay_source_materialization_status(
    member: Mapping[str, Any],
    *,
    package_role: Any,
) -> str:
    role = text(package_role)
    if role not in EXECUTABLE_SOURCE_BOUND_ROLES:
        return "non_executable_source_axis_role"
    if selected_package_bridge_materialized(member):
        return "row_bound_selected_package_replay_source_materialized"
    exact_status = text(member.get("exact_join_status"))
    if exact_status == "context_labels_available_but_no_selected_package_replay_rows_in_lifecycle_window":
        return "selected_package_replay_source_not_materialized_in_current_lifecycle_window"
    if exact_status == "no_hydrated_selector_candidate_rows_for_member_axis":
        return "selected_package_replay_source_not_materialized_no_hydrated_selector_candidate_rows"
    if exact_status == "axis_candidate_namespace_materialized_no_lifecycle_label_context":
        return "candidate_namespace_materialized_without_lifecycle_label_context"
    if exact_status:
        return f"selected_package_replay_source_status:{exact_status}"
    return "selected_package_replay_source_status:unknown"


def selected_package_lifecycle_label_context_status(
    member: Mapping[str, Any],
    *,
    package_role: Any,
) -> str:
    role = text(package_role)
    if role not in EXECUTABLE_SOURCE_BOUND_ROLES:
        return "non_executable_source_axis_role"
    if selected_package_bridge_lifecycle_context_present(member):
        if selected_package_exact_denominator_join_rows(member) > 0:
            return "lifecycle_label_context_present"
        return "lifecycle_label_context_present_denominator_authority_closed"
    if selected_package_bridge_materialized(
        member
    ) and selected_package_source_axis_lifecycle_context_available(member):
        transfer_status = selected_package_lifecycle_window_transfer_status(member)
        scope = selected_package_lifecycle_context_attribution_scope(member)
        prefix = (
            "axis_lifecycle_label_context"
            if scope == "bridge_exact_denominator_join"
            else "pair_broadcast_lifecycle_context"
        )
        if transfer_status == "bridge_window_overlap":
            return (
                f"{prefix}_bridge_window_overlap_but_"
                "denominator_authority_closed"
            )
        if transfer_status == "bridge_window_overlap_denominator_authority_closed":
            return (
                f"{prefix}_bridge_window_overlap_"
                "denominator_authority_closed"
            )
        if transfer_status == "bridge_window_overlap_pair_broadcast_context_only":
            return (
                "pair_broadcast_lifecycle_context_bridge_window_overlap_"
                "denominator_authority_closed"
            )
        if transfer_status == "source_window_missing_pending_created_proxy_only":
            return (
                f"{prefix}_available_"
                "source_window_missing_pending_created_proxy_only"
            )
        if transfer_status == "source_window_missing_exact_decision_time_recovered":
            return (
                f"{prefix}_available_"
                "source_window_missing_exact_decision_time_recovered"
            )
        if transfer_status == "source_window_missing_exact_decision_time_capture_required":
            return (
                f"{prefix}_available_"
                "source_window_missing_exact_decision_time_capture_required"
            )
        if transfer_status == "source_window_missing":
            return f"{prefix}_available_source_window_missing"
        if transfer_status == "bridge_window_missing":
            return f"{prefix}_available_bridge_window_missing"
        if transfer_status == "bridge_window_mismatch":
            mismatch_status = text(
                member.get("source_axis_lifecycle_bridge_window_mismatch_status")
            )
            if mismatch_status:
                return (
                    f"{prefix}_available_"
                    f"bridge_window_mismatch_{mismatch_status}"
                )
            return f"{prefix}_available_bridge_window_mismatch"
        return f"{prefix}_available_not_stable_window_matched"
    if selected_package_bridge_materialized(
        member
    ) and selected_package_legacy_aggregate_lifecycle_context_present(member):
        return "axis_lifecycle_label_context_aggregate_only_producer_gap"
    exact_status = text(member.get("exact_join_status"))
    if selected_package_bridge_materialized(member):
        return "row_bound_selected_package_replay_source_without_lifecycle_label_context"
    if exact_status == "axis_candidate_namespace_materialized_no_lifecycle_label_context":
        return "candidate_namespace_materialized_lifecycle_label_context_source_gap"
    if exact_status == "context_labels_available_but_no_selected_package_replay_rows_in_lifecycle_window":
        return "lifecycle_label_context_present_but_selected_package_replay_source_missing"
    return "lifecycle_label_context_not_materialized"


def selected_package_bridge_materialization_label(
    member: Mapping[str, Any],
    *,
    package_role: Any,
) -> str:
    role = text(package_role)
    if role not in EXECUTABLE_SOURCE_BOUND_ROLES:
        return ""
    if not selected_package_bridge_materialized(member):
        return ""
    exact_status = text(member.get("exact_join_status"))
    if exact_status in {
        "selected_package_replay_bridge_candidate_materialized_no_lifecycle_label_join",
        "axis_candidate_namespace_materialized_no_lifecycle_label_context",
    }:
        if selected_package_bridge_lifecycle_context_present(member):
            if selected_package_exact_denominator_join_rows(member) <= 0:
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    "window_lifecycle_label_context_denominator_authority_closed"
                )
            return (
                "source_axis_selected_package_bridge_materialized_"
                "stable_window_lifecycle_label_context"
            )
        if selected_package_source_axis_lifecycle_context_available(member):
            transfer_status = selected_package_lifecycle_window_transfer_status(member)
            scope = selected_package_lifecycle_context_attribution_scope(member)
            context_prefix = (
                "axis_lifecycle_label_context"
                if scope == "bridge_exact_denominator_join"
                else "pair_broadcast_lifecycle_context"
            )
            if transfer_status == "bridge_window_overlap":
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    f"{context_prefix}_bridge_window_overlap"
                )
            if transfer_status == "bridge_window_overlap_denominator_authority_closed":
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    f"{context_prefix}_bridge_window_overlap_"
                    "denominator_authority_closed"
                )
            if transfer_status == "bridge_window_overlap_pair_broadcast_context_only":
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    "pair_broadcast_lifecycle_context_bridge_window_overlap_"
                    "denominator_authority_closed"
                )
            if transfer_status == "source_window_missing_pending_created_proxy_only":
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    f"{context_prefix}_source_window_missing_"
                    "pending_created_proxy_only"
                )
            if transfer_status == "source_window_missing_exact_decision_time_recovered":
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    f"{context_prefix}_source_window_missing_"
                    "exact_decision_time_recovered"
                )
            if transfer_status == "source_window_missing_exact_decision_time_capture_required":
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    f"{context_prefix}_source_window_missing_"
                    "exact_decision_time_capture_required"
                )
            if transfer_status == "source_window_missing":
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    f"{context_prefix}_source_window_missing"
                )
            if transfer_status == "bridge_window_missing":
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    f"{context_prefix}_bridge_window_missing"
                )
            if transfer_status == "bridge_window_mismatch":
                mismatch_status = text(
                    member.get("source_axis_lifecycle_bridge_window_mismatch_status")
                )
                if mismatch_status:
                    return (
                        "source_axis_selected_package_bridge_materialized_"
                        f"{context_prefix}_bridge_window_mismatch_"
                        f"{mismatch_status}"
                    )
                return (
                    "source_axis_selected_package_bridge_materialized_"
                    f"{context_prefix}_bridge_window_mismatch"
                )
            return (
                "source_axis_selected_package_bridge_materialized_"
                f"{context_prefix}_not_stable_window_matched"
            )
        if selected_package_legacy_aggregate_lifecycle_context_present(member):
            return (
                "source_axis_selected_package_bridge_materialized_"
                "axis_lifecycle_label_context_aggregate_only_producer_gap"
            )
        return (
            "source_axis_selected_package_bridge_materialized_"
            "no_lifecycle_label_context"
        )
    return "source_axis_selected_package_bridge_materialized_no_broad_replay_candidate_match"


def executable_axis_missing_row_bound_selected_package_source(
    member: Mapping[str, Any],
    *,
    package_role: Any,
) -> bool:
    """Separate source-materialization gaps from true generator mismatches."""

    role = text(package_role)
    if role not in EXECUTABLE_SOURCE_BOUND_ROLES:
        return False
    if member.get("candidate_id_carried_to_member") is True:
        return False
    if member.get("decision_window_id_carried_to_member") is True:
        return False
    if safe_float(member.get("selected_package_replay_bridge_candidate_rows")) > 0:
        return False
    exact_status = text(member.get("exact_join_status"))
    return exact_status in {
        "context_labels_available_but_no_selected_package_replay_rows_in_lifecycle_window",
        "no_hydrated_selector_candidate_rows_for_member_axis",
    }


def artifact_status() -> str:
    summary = read_json(BROAD_SUMMARY_PATH)
    if summary.get("status") == "broad_live_as_if_replay_materialized_broker_live_closed":
        return "completed_broad_replay_summary_present"
    return "partial_broad_replay_ledgers_summary_or_comparison_empty"


def discover_profiles(candidates: Mapping[Any, Mapping[str, Any]]) -> tuple[str, ...]:
    """Return profiles actually present for the selected broad replay prefix."""

    summary = read_json(BROAD_SUMMARY_PATH)
    summary_profiles = [
        text(profile)
        for profile in as_list(summary.get("profiles"))
        if text(profile)
    ]
    candidate_profiles = sorted(
        {
            text(row.get("broad_replay_profile"))
            for row in candidates.values()
            if text(row.get("broad_replay_profile"))
        }
    )
    profiles = summary_profiles or candidate_profiles or list(PROFILES)
    return tuple(dict.fromkeys(profiles))


def profile_from_summary(summary: Mapping[str, Any]) -> str:
    for key in ("broad_replay_profile", "profile", "selected_profile"):
        value = text(summary.get(key))
        if value:
            return value
    profiles = [text(profile) for profile in as_list(summary.get("profiles")) if text(profile)]
    if len(profiles) == 1:
        return profiles[0]
    stats = summary.get("split_profile_stats")
    if isinstance(stats, list):
        stat_profiles = [
            text(row.get("profile") or row.get("broad_replay_profile"))
            for row in stats
            if isinstance(row, Mapping)
            if text(row.get("profile") or row.get("broad_replay_profile"))
        ]
        if len(set(stat_profiles)) == 1:
            return stat_profiles[0]
    return ""


def profile_from_row_or_summary(
    row: Mapping[str, Any],
    summary: Mapping[str, Any] | None = None,
) -> str:
    for key in ("broad_replay_profile", "profile", "replay_profile"):
        value = text(row.get(key))
        if value:
            return value
    if summary:
        value = profile_from_summary(summary)
        if value:
            return value
    return "unknown_profile"


def broad_summary_declared_candidate_rows(summary: Mapping[str, Any]) -> int | None:
    """Mirror the flow analyzer's canonical candidate row-count contract."""

    for key in (
        "candidate_rows_written",
        "candidate_index_rows_written",
        "candidate_rows",
    ):
        written_count = summary.get(key)
        if written_count not in (None, ""):
            count = int(written_count)
            if count > 0:
                return count
    ledger_counts = summary.get("ledger_write_row_counts")
    if isinstance(ledger_counts, Mapping):
        for key in ("candidate", "candidate_index"):
            count = int(ledger_counts.get(key) or 0)
            if count > 0:
                return count
    stats = summary.get("split_profile_stats")
    if not isinstance(stats, list) or not stats:
        return None
    candidate_rows = 0
    for row in stats:
        if not isinstance(row, Mapping):
            continue
        candidate_rows += int(row.get("candidate_rows") or 0)
    return candidate_rows if candidate_rows > 0 else None


def summary_selected_profiles(summary: Mapping[str, Any]) -> list[str]:
    profiles = [
        text(value)
        for value in as_list(summary.get("profiles"))
        if text(value)
    ]
    for key in (
        "broad_replay_profile",
        "profile",
        "selected_profile",
        "bound_profile",
    ):
        value = text(summary.get(key))
        if value:
            profiles.append(value)
    stats = summary.get("split_profile_stats")
    if isinstance(stats, list):
        profiles.extend(
            text(row.get("profile") or row.get("broad_replay_profile"))
            for row in stats
            if isinstance(row, Mapping)
            and text(row.get("profile") or row.get("broad_replay_profile"))
        )
    return sorted(set(profiles))


def summary_selected_days(summary: Mapping[str, Any]) -> list[str]:
    days: set[str] = set()
    days_by_split = summary.get("days_by_split")
    if isinstance(days_by_split, Mapping):
        for values in days_by_split.values():
            days.update(text(value) for value in as_list(values) if text(value))
    days.update(
        text(value)
        for value in as_list(
            first_present(
                summary.get("bound_replay_days"),
                summary.get("source_replay_days"),
                summary.get("selected_replay_days"),
                summary.get("requested_replay_days"),
            )
        )
        if text(value)
    )
    day_summaries = summary.get("day_summaries")
    if isinstance(day_summaries, list):
        days.update(
            text(row.get("trading_day"))
            for row in day_summaries
            if isinstance(row, Mapping) and text(row.get("trading_day"))
        )
    if days:
        return sorted(days)
    start = parse_utc(
        first_present(
            summary.get("bound_date_start"),
            summary.get("source_date_start"),
            summary.get("date_start"),
        )
    )
    end = parse_utc(
        first_present(
            summary.get("bound_date_end"),
            summary.get("source_date_end"),
            summary.get("date_end"),
        )
    )
    if start is None or end is None or end < start:
        return []
    current = start.date()
    end_date = end.date()
    while current <= end_date:
        days.add(current.isoformat())
        current += timedelta(days=1)
    return sorted(days)


def read_first_jsonl_object(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size <= 0:
        return {}
    try:
        with path.open("rb") as handle:
            raw = handle.readline()
        row = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return row if isinstance(row, dict) else {}


def bridge_artifact_tag(path: Path) -> str:
    suffix = "_COMPACT_CANDIDATE_LEDGER"
    return path.stem[: -len(suffix)] if path.stem.endswith(suffix) else path.stem


def bridge_declared_candidate_rows(summary: Mapping[str, Any]) -> int:
    for key in ("compact_candidate_rows", "candidate_rows"):
        count = int(safe_float(summary.get(key)))
        if count > 0:
            return count
    ledger_counts = summary.get("ledger_write_row_counts")
    if isinstance(ledger_counts, Mapping):
        for key in ("compact_candidate", "candidate", "candidate_index"):
            count = int(safe_float(ledger_counts.get(key)))
            if count > 0:
                return count
    return 0


BRIDGE_SCOPE_CONTAINERS = (
    "projection_source_scope",
    "broad_replay_binding",
    "source_scope",
)


def bridge_scope_values(
    payloads: Sequence[Mapping[str, Any]],
    *keys: str,
) -> list[Any]:
    values: list[Any] = []
    for payload in payloads:
        containers: list[Mapping[str, Any]] = [payload]
        containers.extend(
            nested
            for name in BRIDGE_SCOPE_CONTAINERS
            if isinstance((nested := payload.get(name)), Mapping)
        )
        for container in containers:
            for key in keys:
                value = container.get(key)
                if not missing_value(value):
                    values.append(value)
    return values


def bridge_source_scope_decision(
    *,
    path: Path,
    summary: Mapping[str, Any],
    first_row: Mapping[str, Any],
    selected_prefix: str,
    selected_days: Sequence[str],
    selected_profiles: Sequence[str],
) -> dict[str, Any]:
    artifact_tag = bridge_artifact_tag(path)
    declared_rows = bridge_declared_candidate_rows(summary)
    standalone_selected = (
        artifact_tag == selected_prefix
        and text(summary.get("output_prefix")) == selected_prefix
    )
    if standalone_selected:
        return {
            "path": str(path),
            "artifact_tag": artifact_tag,
            "included": True,
            "binding_status": "standalone_selected_package_bridge_explicitly_selected",
            "declared_candidate_rows": declared_rows,
            "standalone_selected": True,
        }

    prefix_values = bridge_scope_values(
        (summary, first_row),
        "bound_broad_prefix",
        "source_broad_prefix",
        "broad_replay_prefix",
        "parent_broad_replay_prefix",
        "selected_broad_replay_prefix",
        "projection_source_broad_prefix",
    )
    bound_prefixes = sorted(
        {
            text(value)
            for raw in prefix_values
            for value in as_list(raw)
            if text(value)
        }
    )
    if not bound_prefixes:
        reason = "bridge_exact_broad_prefix_binding_missing"
    elif bound_prefixes != [selected_prefix]:
        reason = "bridge_exact_broad_prefix_binding_mismatch"
    else:
        bridge_days = summary_selected_days(summary)
        if not bridge_days:
            reason = "bridge_selected_window_binding_missing"
        elif list(selected_days) and bridge_days != list(selected_days):
            reason = "bridge_selected_window_binding_mismatch"
        else:
            explicit_profiles = bridge_scope_values(
                (summary,),
                "bound_profiles",
                "source_broad_profiles",
                "broad_replay_profiles",
                "profiles",
                "broad_replay_profile",
                "profile",
                "selected_profile",
            )
            bridge_profiles = sorted(
                {
                    text(value)
                    for raw in explicit_profiles
                    for value in as_list(raw)
                    if text(value)
                }
            )
            if not bridge_profiles:
                reason = "bridge_selected_profile_binding_missing"
            elif list(selected_profiles) and bridge_profiles != list(selected_profiles):
                reason = "bridge_selected_profile_binding_mismatch"
            else:
                return {
                    "path": str(path),
                    "artifact_tag": artifact_tag,
                    "included": True,
                    "binding_status": (
                        "bridge_summary_exact_prefix_window_profile_bound"
                    ),
                    "declared_candidate_rows": declared_rows,
                    "standalone_selected": False,
                }
    return {
        "path": str(path),
        "artifact_tag": artifact_tag,
        "included": False,
        "binding_status": reason,
        "declared_candidate_rows": declared_rows,
        "standalone_selected": False,
        "observed_bound_prefixes": bound_prefixes,
        "observed_days": summary_selected_days(summary),
        "observed_profiles": summary_selected_profiles(summary),
    }


def exact_candidate_relational_materialization_count(
    summary: Mapping[str, Any],
) -> int | None:
    relational = summary.get("candidate_relational_materialization")
    relational = relational if isinstance(relational, Mapping) else {}
    if not (
        summary.get("candidate_ledger_omitted") is True
        and summary.get("candidate_index_ledger_omitted") is True
        and relational.get("schema")
        == "gtos.final_moonshot.broad_replay.candidate_relational_materialization.v1"
        and relational.get("enabled") is True
        and relational.get("exact") is True
        and relational.get("status")
        == "exact_candidate_equals_missed_order_trade_union"
    ):
        return None
    relational_count = int(relational.get("candidate_rows") or 0)
    relational_unique = int(
        relational.get("candidate_unique_profile_scoped_instance_keys") or 0
    )
    terminal_unique = int(
        relational.get("terminal_union_unique_profile_scoped_instance_keys")
        or 0
    )
    missing_counts = relational.get("missing_instance_key_counts")
    missing_counts = missing_counts if isinstance(missing_counts, Mapping) else {}
    if not {"candidate", "missed", "order", "trade"}.issubset(missing_counts):
        return None
    invalid = any(
        (
            int(summary.get("candidate_rows") or 0) != relational_count,
            relational_unique != relational_count,
            terminal_unique != relational_count,
            bool(
                int(
                    relational.get(
                        "candidate_duplicate_profile_scoped_instance_rows"
                    )
                    or 0
                )
            ),
            bool(int(relational.get("candidate_minus_terminal_union_count") or 0)),
            bool(int(relational.get("terminal_union_minus_candidate_count") or 0)),
            any(int(value or 0) for value in missing_counts.values()),
            bool(int(summary.get("candidate_rows_written") or 0)),
            bool(int(summary.get("candidate_index_rows_written") or 0)),
        )
    )
    return None if invalid else relational_count


def broad_physical_candidate_ledger_rows(summary: Mapping[str, Any]) -> tuple[int, str]:
    relational_count = exact_candidate_relational_materialization_count(summary)
    if relational_count is not None:
        return (
            relational_count,
            "exact_missed_order_trade_relational_candidate_rows",
        )
    if summary.get("candidate_ledger_omitted") is True:
        path = BROAD_CANDIDATE_INDEX_PATH
        label = "candidate_index_physical_rows"
    else:
        path = BROAD_CANDIDATE_PATH
        label = "candidate_ledger_physical_rows"
    if path.exists() and path.stat().st_size > 0:
        return row_count(path), label
    fallback = BROAD_CANDIDATE_INDEX_PATH if path == BROAD_CANDIDATE_PATH else BROAD_CANDIDATE_PATH
    fallback_label = (
        "candidate_index_physical_rows_fallback"
        if fallback == BROAD_CANDIDATE_INDEX_PATH
        else "candidate_ledger_physical_rows_fallback"
    )
    if fallback.exists() and fallback.stat().st_size > 0:
        return row_count(fallback), fallback_label
    return 0, f"{label}_missing_or_empty"


def row_count(path: Path) -> int:
    return sum(1 for _row in iter_jsonl(path))


def counter_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def top_counter(counter: Counter[str], limit: int = 12) -> dict[str, int]:
    return dict(counter.most_common(limit))


def rank_scheduler_options(options: Any) -> list[tuple[int, dict[str, Any]]]:
    """Return score-desc scheduler options with a stable 1-based rank."""

    if not isinstance(options, list):
        return []
    option_rows = [option for option in options if isinstance(option, dict)]
    ranked = sorted(
        enumerate(option_rows),
        key=lambda item: (
            -safe_float(item[1].get("score")),
            safe_float(item[1].get("input_sequence"), default=999999.0),
            text(item[1].get("option_id")),
            item[0],
        ),
    )
    return [(rank, option) for rank, (_index, option) in enumerate(ranked, start=1)]


def candidate_key(row: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        text(row.get("broad_replay_profile")),
        text(row.get("candidate_id")),
        text(row.get("decision_time_utc")),
        upper(row.get("symbol")),
        side(row.get("side") or row.get("direction")),
    )


def candidate_instance_key(row: Mapping[str, Any]) -> str:
    return "|".join(
        (
            text(row.get("broad_replay_profile")),
            text(row.get("candidate_id")),
            text(row.get("decision_time_utc")),
            upper(row.get("symbol")),
            side(row.get("side") or row.get("direction")),
            text(row.get("split")),
            text(row.get("chunk_id")),
        )
    )


def candidate_instance_parity_key(row: Mapping[str, Any]) -> str:
    """Canonical cross-ledger identity required by the V220 projection."""

    return f"{text(row.get('candidate_id'))}@@{text(row.get('decision_time_utc'))}"


def package_candidate_exact_instance_key(
    row: Mapping[str, Any],
) -> tuple[str, str, str, str] | None:
    """Return the exact package/replay join key or fail closed when incomplete."""

    candidate_id = text(row.get("candidate_id"))
    decision_time = text(row.get("decision_time_utc"))
    symbol = upper(row.get("symbol"))
    direction = side(row.get("side") or row.get("direction"))
    if not all((candidate_id, decision_time, symbol, direction)):
        return None
    return candidate_id, decision_time, symbol, direction


def package_candidate_signed_instance_keys(row: Mapping[str, Any]) -> list[str]:
    return sorted(
        {
            text(row.get(field))
            for field in (
                "canonical_replay_candidate_instance_key",
                "source_bound_replay_candidate_instance_key",
                "risk_finalizer_probe_instance_key",
            )
            if text(row.get(field))
        }
    )


def resolve_package_candidate(
    candidate: Mapping[str, Any],
    package_candidate_index: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str, int]:
    """Resolve package authority by signed or exact instance, never bare id."""

    by_signed = package_candidate_index.get("by_signed_instance")
    by_exact = package_candidate_index.get("by_exact_instance")
    by_candidate_id = package_candidate_index.get("by_candidate_id")
    by_signed = by_signed if isinstance(by_signed, Mapping) else {}
    by_exact = by_exact if isinstance(by_exact, Mapping) else {}
    by_candidate_id = by_candidate_id if isinstance(by_candidate_id, Mapping) else {}

    signed_matches: list[Mapping[str, Any]] = []
    for identity in package_candidate_signed_instance_keys(candidate):
        rows = by_signed.get(identity) or []
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
            signed_matches.extend(row for row in rows if isinstance(row, Mapping))
    signed_matches = list({id(row): row for row in signed_matches}.values())
    if len(signed_matches) == 1:
        resolved = dict(signed_matches[0])
        resolved["package_candidate_identity_match_status"] = (
            "exact_signed_candidate_instance_match"
        )
        resolved["package_candidate_identity_match_count"] = 1
        return resolved, "exact_signed_candidate_instance_match", 1
    if len(signed_matches) > 1:
        return None, "ambiguous_signed_candidate_instance_match", len(signed_matches)

    exact_key = package_candidate_exact_instance_key(candidate)
    exact_matches = by_exact.get(exact_key, []) if exact_key is not None else []
    if isinstance(exact_matches, Sequence) and not isinstance(
        exact_matches,
        (str, bytes, bytearray),
    ):
        exact_matches = [row for row in exact_matches if isinstance(row, Mapping)]
    else:
        exact_matches = []
    if len(exact_matches) == 1:
        resolved = dict(exact_matches[0])
        resolved["package_candidate_identity_match_status"] = (
            "exact_candidate_time_symbol_side_match"
        )
        resolved["package_candidate_identity_match_count"] = 1
        return resolved, "exact_candidate_time_symbol_side_match", 1
    if len(exact_matches) > 1:
        return None, "ambiguous_candidate_time_symbol_side_match", len(exact_matches)

    candidate_id = text(candidate.get("candidate_id"))
    bare_matches = by_candidate_id.get(candidate_id, []) if candidate_id else []
    bare_count = (
        len(bare_matches)
        if isinstance(bare_matches, Sequence)
        and not isinstance(bare_matches, (str, bytes, bytearray))
        else 0
    )
    if bare_count:
        return None, "candidate_id_only_non_exact_match_rejected", bare_count
    return None, "package_candidate_instance_missing", 0


def axis_candidate_generated(row: Mapping[str, Any]) -> bool:
    return bool(
        row.get("broad_replay_candidate_generated") is True
        or row.get("selected_package_bridge_candidate_generated") is True
        or text(row.get("candidate_generation_label"))
        in {
            "candidate_generated",
            "candidate_generated_via_selected_package_bridge",
        }
    )


EXECUTABLE_REPLAY_CONTRACT_FIELDS = (
    "ultimate_package_effective_source_bound_candidate_use_allowed",
    "ultimate_package_effective_admission_count",
    "selected_package_replay_row",
    "pretrade_cost_packet_status",
    "pretrade_cost_refusal_reasons",
    "cost_source_gap_status",
    "cost_authority",
    "pretrade_cost_packet_authority",
    "source_gap_cost_fallback_blocked",
    "candidate_cost_r_fallback_is_authority",
    "source_completeness",
    "source_completeness_status",
    "pending_limit_fillability_probability",
    "pending_fill_probability",
    "predecision_limit_fillability_probability",
    "limit_fillability_probability",
    "limit_fill_probability",
    "execution_fill_probability",
    "execution_fill_probability_source",
    "execution_fill_probability_source_time_utc",
    "execution_fill_probability_source_boundary",
    "execution_fill_probability_authority_class",
    "execution_fillability_source",
    "execution_fillability_source_time_utc",
    "execution_fillability_source_boundary",
    "execution_fillability_authority_class",
    "execution_fillability_atomic_failure",
    "execution_fillability_atomic_conflicts",
    "predecision_limit_fillability",
    "entry_quality_fill_probability",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "take_profit",
    "target_price",
    "package_authority_has_order_geometry",
    "package_authority_order_geometry_status",
    "scheduler_materialization_action_intent",
    "scheduler_materialization_skip_reason",
    "scheduler_materialization_selector_action",
    "scheduler_materialization_selector_reason",
    "materialized_selector_action",
    "materialized_selector_reason",
    "effective_selector_action_before_risk_expression",
    "effective_selector_reason_before_risk_expression",
    "action_intent",
    "lifecycle_action",
    "scheduler_terminal_vs_soft_guard",
    "reallocation_soft_guard_vetoes",
    "reallocation_soft_guard_pool_eligible",
    "reallocation_soft_guard_pool_status",
    "terminal_vetoes",
    "scheduler_materialization_source_required_selector_hold_override_applied",
    "scheduler_materialization_source_required_fail_closed_override_applied",
)


PROJECTION_STAGE_FIELDS = (
    "projection_source_scope_mode",
    "projection_source_prefix",
    "projection_selected_date_start",
    "projection_selected_date_end",
    "projection_selected_profiles",
    "projection_candidate_source_class",
    "projection_candidate_source_path",
    "projection_candidate_source_binding_status",
    "raw_selector_action",
    "raw_selector_reason",
    "effective_selector_action",
    "effective_selector_reason",
    "selector_action",
    "selector_reason",
    "package_new_entry_authority_valid",
    "package_new_entry_authority_status",
    "package_new_entry_authority_failures",
    "package_replay_order_executable_candidate_use_allowed",
    "package_replay_order_executable_candidate_use_allowed_reason",
    "package_replay_order_executable_transfer_status",
    "package_replay_order_executable_final_blocker_class",
    "package_replay_order_executable_final_blocker_reason",
    "package_replay_order_executable_final_blocker_source",
    "package_replay_order_executable_bound_order_id",
    "package_replay_order_executable_bound_trade_id",
    "package_replay_terminal_binding_status",
    "package_replay_terminal_bound_order_id",
    "package_replay_terminal_bound_trade_id",
    "risk_finalizer_decision",
    "risk_finalizer_reason",
    "risk_finalizer_selected",
    "risk_finalizer_rank",
    "risk_finalizer_probe_risk_decision",
    "risk_decision",
    "effective_risk_decision",
    "risk_decision_reason",
    "risk_decision_family",
    "risk_expression_ladder_tier",
    "risk_expression_ladder_tier_causes",
    "scheduler_rank",
    "scheduler_final_selected",
    "scheduler_selection_disposition",
    "scheduler_option_status",
    "scheduler_option_reason",
    "same_symbol_lifecycle_action",
    "same_symbol_lifecycle_reason",
    "risk_lifecycle_action",
    "simulated_order_id",
    "simulated_trade_id",
    "order_status",
    "fill_status",
    "terminal_outcome",
    "guarded_market_fallback_configured",
    "guarded_market_fallback_status",
    "guarded_market_fallback_reason",
    "guarded_market_fallback_reasons",
    "guarded_market_fallback_attempted",
    "guarded_market_fallback_applied",
    "planned_guarded_market_fallback_status",
    "planned_guarded_market_fallback_reason",
    "passive_limit_fallback_envelope_status",
    "passive_limit_fallback_envelope_guarded_market_route_available",
    "passive_limit_fallback_envelope_unusable_guarded_fallback_reasons",
    "counterfactual_fill_status",
    "counterfactual_order_fill_status",
    "counterfactual_order_terminal_outcome",
    "counterfactual_order_close_mark_r",
    "miss_reason",
    "missed_opportunity_counterfactual_scoreable",
    "opportunity_net_proxy_r",
    "net_proxy_r",
    *EXECUTABLE_REPLAY_CONTRACT_FIELDS,
)


def pre_risk_selector_action(row: Mapping[str, Any], default: str = "") -> str:
    """Resolve selector admission before runtime risk-expression translation."""

    signed_package_action = valid_package_new_entry_effective_selector_action(row)
    return text(
        row.get("materialized_selector_action")
        or row.get("scheduler_materialization_selector_action")
        or row.get("effective_selector_action_before_risk_expression")
        or signed_package_action
        or row.get("effective_selector_action")
        or row.get("selector_action"),
        default,
    )


def pre_risk_selector_reason(row: Mapping[str, Any], default: str = "") -> str:
    signed_package_action = valid_package_new_entry_effective_selector_action(row)
    return text(
        row.get("materialized_selector_reason")
        or row.get("scheduler_materialization_selector_reason")
        or row.get("effective_selector_reason_before_risk_expression")
        or (
            row.get("package_new_entry_authority_selector_reason")
            if signed_package_action
            else None
        )
        or row.get("effective_selector_reason")
        or row.get("selector_reason"),
        default,
    )


def projection_stage_binding(
    row: Mapping[str, Any],
    *,
    stage: str,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    binding = {
        field: row.get(field)
        for field in PROJECTION_STAGE_FIELDS
        if field in row
    }
    binding.update(route_provenance_fields(row))
    selector_action = pre_risk_selector_action(row)
    selector_reason = pre_risk_selector_reason(row)
    if selector_action:
        binding["effective_selector_action"] = selector_action
    if selector_reason:
        binding["effective_selector_reason"] = selector_reason
    if overrides:
        binding.update(overrides)
    binding["package_new_entry_authority_envelope_record"] = (
        compact_package_new_entry_authority_envelope_selection(
            package_new_entry_authority_envelope_selection(
                row,
                action_intent=text(
                    row.get("scheduler_materialization_action_intent")
                    or row.get("action_intent")
                    or row.get("lifecycle_action")
                )
                or None,
            )
        )
    )
    binding["stage"] = stage
    return binding


def remember_projection_stage_binding(
    enrichment_row: dict[str, Any],
    *,
    stage: str,
    binding: Mapping[str, Any],
    prefer: bool = False,
) -> None:
    count_key = f"{stage}_binding_count"
    row_key = f"{stage}_binding"
    enrichment_row[count_key] = int(enrichment_row.get(count_key) or 0) + 1
    if prefer or not enrichment_row.get(row_key):
        enrichment_row[row_key] = dict(binding)


def stable_window(row: Mapping[str, Any]) -> str:
    parsed = parse_utc(row.get("decision_time_utc"))
    decision_time = parsed.isoformat() if parsed is not None else text(row.get("decision_time_utc"))
    return (
        f"decision_window:{upper(row.get('symbol'))}:"
        f"{side(row.get('side') or row.get('direction'))}:"
        f"{decision_time}"
    )


def package_member_axis_ids(row: Mapping[str, Any]) -> list[str]:
    return sorted(
        {
            value
            for value in (
                *string_list(row.get("matched_stable_member_axis_ids")),
                *string_list(row.get("ultimate_package_matched_member_axis_ids")),
                *string_list(row.get("selected_package_matched_member_axis_ids")),
            )
            if value
        }
    )


def package_new_entry_authority_projection_fields(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    action_intent = text(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
    )
    envelope = package_new_entry_authority_envelope_selection(
        row,
        action_intent=action_intent or None,
    )
    projected = {
        "package_new_entry_authority_envelope_status": envelope.get("status"),
        "package_new_entry_authority_envelope_valid": envelope.get("valid") is True,
        "package_new_entry_authority_envelope_reasons": list(
            envelope.get("reasons") or []
        ),
        "package_new_entry_authority_envelope_source": envelope.get("source"),
        "package_new_entry_authority_envelope_digest_sha256": envelope.get("digest"),
    }
    if envelope.get("valid") is not True:
        if package_new_entry_authority_surfaces(row):
            projected.update(
                {
                    "package_new_entry_authority_valid": False,
                    "package_new_entry_authority_status": (
                        "legacy_or_invalid_authority_diagnostic_only"
                    ),
                    "package_replay_candidate_use_allowed": False,
                    "package_replay_executable_candidate_use_allowed": False,
                    "replay_candidate_use_allowed_now": False,
                    "diagnostic_package_new_entry_authority_hash_sha256": text(
                        row.get("package_new_entry_authority_hash_sha256")
                    ),
                }
            )
        return projected
    surface = envelope.get("surface")
    surface = surface if isinstance(surface, Mapping) else {}
    for field in PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS:
        if field in surface:
            projected[field] = surface.get(field)
    return projected


def reduced_candidate(row: Mapping[str, Any]) -> dict[str, Any]:
    lifecycle_packet = row.get("lifecycle_packet")
    lifecycle_action = ""
    lifecycle_reason = ""
    lifecycle_permitted: bool | None = None
    if isinstance(lifecycle_packet, dict):
        lifecycle_action = text(lifecycle_packet.get("action"))
        lifecycle_reason = text(lifecycle_packet.get("reason"))
        permitted = lifecycle_packet.get("permitted_order_intent")
        lifecycle_permitted = permitted if isinstance(permitted, bool) else None
    scheduler_materialization_action_intent = text(
        row.get("scheduler_materialization_action_intent")
        or row.get("scheduler_action_class")
        or row.get("selected_action_class")
        or row.get("action_intent")
        or lifecycle_action
    )
    source_fields = row.get("source_fields") if isinstance(row.get("source_fields"), dict) else {}
    source_completeness = safe_float(
        row.get("source_completeness", source_fields.get("source_completeness")),
        default=0.0,
    )
    member_axis_ids = package_member_axis_ids(row)
    execution_fill_probability, fill_probability_source = (
        execution_fillability_authority(row)
    )
    diagnostic_fill_probability = math.nan
    for key in (
        "candidate_fill_probability",
        "entry_quality_fill_probability",
        "fill_probability",
    ):
        diagnostic_fill_probability = safe_float(row.get(key), default=math.nan)
        if math.isfinite(diagnostic_fill_probability):
            break
    if not math.isfinite(diagnostic_fill_probability):
        diagnostic_fill_probability = (
            execution_fill_probability
            if execution_fill_probability is not None
            else 0.0
        )
    execution_fill_probability_value = (
        execution_fill_probability if execution_fill_probability is not None else None
    )
    expected_net_r = safe_float(
        row.get("candidate_expected_net_r", row.get("expected_net_r"))
    )
    probability = safe_float(row.get("candidate_probability", row.get("probability")))
    confidence = safe_float(
        row.get(
            "confidence",
            row.get(
                "candidate_confidence",
                row.get("scheduler_confidence", row.get("confluence_confidence")),
            ),
        )
    )
    source_bound_allowed = row.get(
        "source_bound_package_candidate_use_allowed",
        row.get("ultimate_package_source_bound_candidate_use_allowed"),
    )
    package_replay_allowed = row.get(
        "package_replay_source_bound_candidate_use_allowed",
        source_bound_allowed,
    )
    executable_package_allowed, executable_package_reason = (
        replay_executable_package_use_detail(
            row,
            source_bound_allowed=source_bound_allowed,
            package_replay_allowed=package_replay_allowed,
        )
    )
    source_bound_diagnostic_present = bool(
        source_bound_allowed
        or package_replay_allowed
        or row.get("ultimate_package_effective_source_bound_candidate_use_allowed")
    )
    source_bound_non_executable = (
        source_bound_diagnostic_present and not executable_package_allowed
    )
    authority_projection = package_new_entry_authority_projection_fields(row)
    projection_fields = projection_stage_binding(row, stage="candidate")
    projection_fields.pop("stage", None)
    return {
        **projection_fields,
        "broad_replay_profile": profile_from_row_or_summary(row),
        "candidate_id": text(row.get("candidate_id")),
        "candidate_instance_key": candidate_instance_key(row),
        "decision_window_id": text(row.get("decision_window_id")),
        "candidate_set_id": text(row.get("candidate_set_id")),
        "decision_time_utc": text(row.get("decision_time_utc")),
        "stable_decision_window_id": text(
            row.get("stable_decision_window_id"),
            stable_window(row),
        ),
        "selected_candidate_id": text(row.get("selected_candidate_id")),
        "selected_candidate_ids": string_list(row.get("selected_candidate_ids")),
        "packet_sidecar_id": text(row.get("packet_sidecar_id")),
        "packet_sidecar_hash_sha256": text(row.get("packet_sidecar_hash_sha256")),
        "packet_sidecar_artifact": text(row.get("packet_sidecar_artifact")),
        "scheduler_packet_sidecar_id": text(row.get("scheduler_packet_sidecar_id")),
        "scheduler_packet_sidecar_hash_sha256": text(
            row.get("scheduler_packet_sidecar_hash_sha256")
        ),
        "replay_identity_tuple_status": text(row.get("replay_identity_tuple_status")),
        "split": text(row.get("split")),
        "chunk_id": text(row.get("chunk_id")),
        "selected_package_replay_bridge_artifact_tag": text(
            row.get("selected_package_replay_bridge_artifact_tag")
        ),
        "compact_bridge_candidate_source_path": text(
            row.get("compact_bridge_candidate_source_path")
        ),
        "trading_day": text(row.get("trading_day")),
        "symbol": upper(row.get("symbol")),
        "side": side(row.get("side") or row.get("direction")),
        "direction": side(row.get("side") or row.get("direction")),
        "timeframe": text(
            row.get("timeframe") or row.get("market_timeframe") or row.get("decision_timeframe")
        ),
        "market_timeframe": text(
            row.get("market_timeframe") or row.get("timeframe") or row.get("decision_timeframe")
        ),
        "decision_timeframe": text(
            row.get("decision_timeframe") or row.get("timeframe") or row.get("market_timeframe")
        ),
        **route_provenance_fields(row),
        "route_session_raw": text(row.get("route_session_raw") or row.get("route_session")),
        "route_session_applied": text(
            row.get("route_session_applied") or row.get("session_bucket") or row.get("session")
        ),
        "session": text(row.get("session") or row.get("session_bucket") or row.get("route_session")),
        "kill_zone": text(row.get("kill_zone") or row.get("session_bucket") or row.get("session")),
        "utc_hour_bucket": text(row.get("utc_hour_bucket")),
        "session_tokens": sorted(session_tokens(row)),
        "selector_action": effective_selector_action(row, "unknown"),
        "selector_reason": effective_selector_reason(row, "unknown"),
        "raw_selector_action": text(
            row.get("raw_selector_action") or row.get("selector_action"),
            "unknown",
        ),
        "candidate_decision_quality_field_sources": row.get(
            "candidate_decision_quality_field_sources"
        ),
        "candidate_decision_quality_alias_status": row.get(
            "candidate_decision_quality_alias_status"
        ),
        "candidate_decision_quality_source_boundary": row.get(
            "candidate_decision_quality_source_boundary"
        ),
        "candidate_decision_quality_alias_mismatches": row.get(
            "candidate_decision_quality_alias_mismatches"
        ),
        "candidate_decision_quality_provenance_failures": row.get(
            "candidate_decision_quality_provenance_failures"
        ),
        "candidate_decision_quality": candidate_decision_quality_envelope(
            {
                **dict(row),
                "candidate_probability": probability,
                "probability": probability,
                "candidate_confidence": confidence,
                "confidence": confidence,
                "candidate_fill_probability": diagnostic_fill_probability,
                "fill_probability": diagnostic_fill_probability,
                "execution_fill_probability": execution_fill_probability_value,
                "execution_fill_probability_source": fill_probability_source,
                "candidate_expected_net_r": expected_net_r,
                "expected_net_r": expected_net_r,
                "source_completeness": source_completeness,
                "source_completeness_status": text(row.get("source_completeness_status")),
            }
        ),
        "candidate_ev_r": safe_float(row.get("candidate_ev_r")),
        "candidate_probability": probability,
        "probability": probability,
        "candidate_confidence": confidence,
        "confidence": confidence,
        "candidate_fill_probability": diagnostic_fill_probability,
        "fill_probability": diagnostic_fill_probability,
        "execution_fill_probability": execution_fill_probability_value,
        "execution_fill_probability_source": fill_probability_source,
        "candidate_expected_net_r": expected_net_r,
        "expected_net_r": expected_net_r,
        "expected_cost_r": safe_float(row.get("expected_cost_r") or row.get("cost_r")),
        "pretrade_cost_packet_status": text(row.get("pretrade_cost_packet_status")),
        "cost_authority": text(
            row.get("cost_authority") or row.get("pretrade_cost_packet_authority")
        ),
        "pretrade_cost_packet_authority": text(
            row.get("pretrade_cost_packet_authority") or row.get("cost_authority")
        ),
        "pretrade_cost_refusal_reasons": string_list(
            row.get("pretrade_cost_refusal_reasons")
        ),
        "cost_source_gap_status": text(row.get("cost_source_gap_status")),
        "source_gap_cost_fallback_blocked": row.get("source_gap_cost_fallback_blocked"),
        "candidate_cost_r_fallback_is_authority": row.get(
            "candidate_cost_r_fallback_is_authority"
        ),
        "scheduler_materialization_action_intent": (
            scheduler_materialization_action_intent
        ),
        "scheduler_materialization_skip_reason": text(
            row.get("scheduler_materialization_skip_reason")
        ),
        "action_intent": text(row.get("action_intent") or scheduler_materialization_action_intent),
        "dynamic_geometry_policy": text(row.get("dynamic_geometry_policy")),
        "lifecycle_action": lifecycle_action,
        "lifecycle_reason": lifecycle_reason,
        "lifecycle_permitted": lifecycle_permitted,
        "source_completeness": source_completeness,
        "source_completeness_status": text(row.get("source_completeness_status")),
        "lifecycle_label_context_present": row.get("lifecycle_label_context_present"),
        "lifecycle_label_context_row_count": int(
            safe_float(row.get("lifecycle_label_context_row_count"))
        ),
        "pending_lifecycle_v4_state_group": text(
            row.get("pending_lifecycle_v4_state_group")
        ),
        "pending_lifecycle_v4_state_groups": string_list(
            row.get("pending_lifecycle_v4_state_groups")
        ),
        "fillability_label_family": text(row.get("fillability_label_family")),
        "fillability_label_families": string_list(
            row.get("fillability_label_families")
        ),
        "fill_no_fill_label": text(row.get("fill_no_fill_label")),
        "fill_no_fill_labels": string_list(row.get("fill_no_fill_labels")),
        "source_bound_package_candidate_use_allowed": source_bound_allowed,
        "ultimate_package_source_bound_candidate_use_allowed": source_bound_allowed,
        "package_replay_source_bound_candidate_use_allowed": package_replay_allowed,
        "package_replay_candidate_use_allowed": executable_package_allowed,
        "package_replay_executable_candidate_use_allowed": executable_package_allowed,
        "package_replay_executable_candidate_use_allowed_reason": (
            executable_package_reason
        ),
        "replay_candidate_use_allowed_now": executable_package_allowed,
        "replay_candidate_use_allowed_now_reason": executable_package_reason,
        "matched_stable_member_axis_ids": member_axis_ids,
        "ultimate_package_matched_member_axis_ids": member_axis_ids,
        "selected_package_matched_member_axis_ids": member_axis_ids,
        "ultimate_package_matched_member_axis_count": safe_float(
            row.get("ultimate_package_matched_member_axis_count")
            or row.get("member_axis_match_count")
        ),
        "ultimate_package_admission_member_axis_match_count": safe_float(
            row.get("ultimate_package_admission_member_axis_match_count")
        ),
        "ultimate_package_matched_member_axis_role_counts": (
            row.get("ultimate_package_matched_member_axis_role_counts")
            if isinstance(row.get("ultimate_package_matched_member_axis_role_counts"), dict)
            else {}
        ),
        "ultimate_package_member_axis_source_bound_signal_r_sum": safe_float(
            row.get("ultimate_package_member_axis_source_bound_signal_r_sum")
        ),
        "ultimate_package_member_axis_max_source_bound_signal_r": safe_float(
            row.get("ultimate_package_member_axis_max_source_bound_signal_r")
        ),
        "ultimate_package_effective_matched_count": safe_float(
            row.get("ultimate_package_effective_matched_count")
        ),
        "ultimate_package_effective_admission_count": safe_float(
            row.get("ultimate_package_effective_admission_count")
        ),
        "ultimate_package_effective_source_bound_signal_r": safe_float(
            row.get("ultimate_package_effective_source_bound_signal_r")
        ),
        "ultimate_package_effective_source_bound_candidate_use_allowed": row.get(
            "ultimate_package_effective_source_bound_candidate_use_allowed"
        ),
        "diagnostic_ultimate_package_effective_source_bound_signal_r": safe_float(
            row.get("diagnostic_ultimate_package_effective_source_bound_signal_r")
            or row.get("ultimate_package_effective_source_bound_signal_r")
        )
        if source_bound_non_executable
        else safe_float(row.get("diagnostic_ultimate_package_effective_source_bound_signal_r")),
        "diagnostic_ultimate_package_effective_source_bound_candidate_use_allowed": (
            row.get("diagnostic_ultimate_package_effective_source_bound_candidate_use_allowed")
            if not source_bound_non_executable
            else row.get("ultimate_package_effective_source_bound_candidate_use_allowed")
        ),
        "ultimate_package_effective_source_bound_non_executable": (
            source_bound_non_executable
        ),
        "ultimate_package_effective_source_bound_non_executable_reason": (
            executable_package_reason if source_bound_non_executable else ""
        ),
        "ultimate_package_effective_executable_authority_allowed": (
            executable_package_allowed
        ),
        "ultimate_package_effective_executable_authority_reason": (
            executable_package_reason
        ),
        "ultimate_package_effective_evidence_source": text(
            row.get("ultimate_package_effective_evidence_source")
        ),
        "ultimate_package_executable_admission_status": text(
            row.get("ultimate_package_executable_admission_status")
        ),
        "ultimate_package_scheduler_consumed_status": text(
            row.get("ultimate_package_scheduler_consumed_status")
        ),
        **authority_projection,
    }


PACKAGE_NEW_ENTRY_AUTHORITY_FIELDS = (
    "package_new_entry_authority_required",
    "package_new_entry_authority_valid",
    "package_new_entry_authority_status",
    "package_new_entry_authority_failures",
    "package_new_entry_authority_hash_sha256",
    "expected_package_new_entry_authority_hash_sha256",
    "package_new_entry_authority_payload_schema",
    "package_new_entry_authority_scope",
    "package_new_entry_authority_target_action_intent",
    "package_new_entry_authority_authority_field",
    "package_new_entry_authority_authority_family",
    "package_new_entry_authority_source_boundary",
    "package_new_entry_authority_uses_outcome_fields",
    "package_new_entry_authority_selector_action",
    "package_new_entry_authority_selector_reason",
    "package_new_entry_authority_candidate_decision_quality",
    "package_new_entry_authority_candidate_decision_quality_field_sources",
    "package_new_entry_authority_candidate_decision_quality_source_boundary",
    "package_new_entry_authority_candidate_decision_quality_alias_status",
    "package_new_entry_authority_candidate_decision_quality_alias_mismatches",
    "package_new_entry_authority_candidate_decision_quality_provenance_failures",
    *PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS,
)


def executable_proof_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    action_intent = text(
        row.get("scheduler_materialization_action_intent")
        or row.get("scheduler_action_class")
        or row.get("selected_action_class")
        or row.get("action_intent")
        or row.get("lifecycle_action")
    )
    selector_action = text(
        pre_risk_selector_action(row)
        or row.get("selector_action_origin")
        or row.get("risk_decision")
    )
    proof = {
        field: row.get(field)
        for field in EXECUTABLE_REPLAY_CONTRACT_FIELDS
        if field in row
    }
    proof.update({
        "pretrade_cost_packet_status": row.get("pretrade_cost_packet_status"),
        "cost_authority": row.get("cost_authority")
        or row.get("pretrade_cost_packet_authority"),
        "pretrade_cost_packet_authority": row.get("pretrade_cost_packet_authority")
        or row.get("cost_authority"),
        "cost_source_gap_status": row.get("cost_source_gap_status"),
        "source_gap_cost_fallback_blocked": row.get("source_gap_cost_fallback_blocked"),
        "candidate_cost_r_fallback_is_authority": row.get(
            "candidate_cost_r_fallback_is_authority"
        ),
        "scheduler_materialization_skip_reason": row.get(
            "scheduler_materialization_skip_reason"
        ),
        "scheduler_materialization_action_intent": action_intent,
        "selector_action": selector_action,
        "raw_selector_action": row.get("raw_selector_action")
        or row.get("selector_action_origin")
        or row.get("selector_action"),
        "effective_selector_action": pre_risk_selector_action(row) or None,
        "selector_reason": pre_risk_selector_reason(row)
        or row.get("selector_action_origin_reason")
        or row.get("risk_decision_reason"),
        "entry_price": row.get("entry_price"),
        "stop_loss": row.get("stop_loss"),
        "take_profit_1": row.get("take_profit_1")
        or row.get("take_profit")
        or row.get("target_price"),
    })
    for field in PACKAGE_NEW_ENTRY_AUTHORITY_FIELDS:
        if field in row:
            proof[field] = row.get(field)
    return proof


def remember_executable_proof(
    enrichment_row: dict[str, Any],
    row: Mapping[str, Any],
) -> None:
    proof = executable_proof_fields(row)
    if proof.get("pretrade_cost_packet_status") != "PASSED":
        return
    if proof.get("cost_source_gap_status") != "source_bound_cost_authority_present":
        return
    if not proof.get("scheduler_materialization_action_intent"):
        return
    if not proof.get("selector_action"):
        return
    if not enrichment_row.get("executable_proof_row"):
        enrichment_row["executable_proof_row"] = proof


def candidate_matches_stable_member_axis_id(
    member: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> bool:
    stable_axis_id = text(member.get("stable_member_axis_id"))
    if not stable_axis_id:
        return False
    return stable_axis_id in set(package_member_axis_ids(candidate))


def sleeve_axis_matches_candidate(axis: Mapping[str, Any], candidate: Mapping[str, Any]) -> bool:
    axis_symbol = upper(axis.get("symbol") or axis.get("normalized_symbol"))
    axis_side = side(axis.get("side"))
    axis_framework = text(axis.get("framework"))
    axis_origin = text(axis.get("origin_family"))
    axis_sessions = session_aliases(
        string_list(axis.get("session_buckets") or axis.get("session_bucket"))
    )
    symbol_wildcard = wildcard(axis_symbol)
    side_wildcard = wildcard(axis_side)
    session_wildcard = any(wildcard(token) for token in axis_sessions)

    if axis_symbol and not symbol_wildcard and candidate["symbol"] and axis_symbol != candidate["symbol"]:
        return False
    if axis_side and not side_wildcard and candidate["side"] and axis_side != candidate["side"]:
        return False
    if (
        axis_framework
        and candidate["framework"]
        and not family_matches(axis_framework, candidate["framework"])
    ):
        return False
    if (
        axis_origin
        and candidate["origin_family"]
        and not family_matches(axis_origin, candidate["origin_family"])
    ):
        return False
    if (
        axis_sessions
        and not session_wildcard
        and not (axis_sessions & set(candidate["session_tokens"]))
    ):
        return False
    return True


class SparseCandidateEnrichment(dict[str, Any]):
    """Materialize mutable enrichment containers only when a join uses them."""

    _COUNTER_FIELDS = frozenset(
        {
            "candidate_lifecycle_action_counts",
            "candidate_lifecycle_reason_counts",
            "close_reason_counts",
            "counterfactual_fill_status_counts",
            "exit_result_counts",
            "fill_status_counts",
            "fillability_status_counts",
            "miss_reason_counts",
            "order_architecture_counts",
            "order_policy_counts",
            "order_status_counts",
            "order_type_counts",
            "risk_decision_counts",
            "risk_decision_reason_counts",
            "risk_lifecycle_action_counts",
            "risk_lifecycle_permitted_counts",
            "scheduler_action_class_counts",
            "scheduler_decision_status_counts",
            "scheduler_option_reason_counts",
            "selected_action_class_counts",
            "source_join_class_counts",
            "terminal_outcome_counts",
        }
    )
    _SET_FIELDS = frozenset(
        {
            "candidate_ids",
            "packet_sidecar_hashes",
            "packet_sidecar_ids",
            "selected_candidate_ids",
            "trade_candidate_ids",
            "trade_candidate_instance_keys",
        }
    )
    _DICT_FIELDS = frozenset(
        {
            "trade_actual_r_by_candidate_id",
            "trade_actual_r_by_candidate_instance_key",
            "trade_cash_pnl_by_candidate_id",
            "trade_cash_pnl_by_candidate_instance_key",
            "trade_final_r_by_candidate_id",
            "trade_final_r_by_candidate_instance_key",
            "trade_gross_r_by_candidate_id",
            "trade_gross_r_by_candidate_instance_key",
        }
    )
    _LIST_FIELDS = frozenset({"scheduler_option_samples"})
    _BOOLEAN_FIELDS = frozenset(
        {
            "missed_present",
            "oracle_present",
            "order_present",
            "packet_sidecar_present",
            "scheduler_option_present",
            "scheduler_selected",
            "scorecard_present",
            "trade_present",
        }
    )
    _INTEGER_FIELDS = frozenset(
        {"missed_count", "scheduler_option_count", "trade_count"}
    )
    _FLOAT_FIELDS = frozenset(
        {
            "cash_pnl",
            "final_r",
            "gross_r",
            "missed_negative_net_r",
            "missed_net_proxy_r",
            "missed_positive_net_r",
            "net_r",
            "risk_cash",
            "risk_pct",
        }
    )
    _NONE_FIELDS = frozenset({"scheduler_rank_min", "scheduler_score_max"})

    def __missing__(self, key: str) -> Any:
        if key in self._COUNTER_FIELDS:
            value: Any = Counter()
        elif key in self._SET_FIELDS:
            value = set()
        elif key in self._DICT_FIELDS:
            value = {}
        elif key in self._LIST_FIELDS:
            value = []
        elif key in self._BOOLEAN_FIELDS:
            value = False
        elif key in self._INTEGER_FIELDS:
            value = 0
        elif key in self._FLOAT_FIELDS:
            value = 0.0
        elif key in self._NONE_FIELDS:
            value = None
        else:
            raise KeyError(key)
        self[key] = value
        return value


def _load_broad_indexes_with_scope() -> tuple[
    dict[tuple[str, str, str, str, str], dict[str, Any]],
    dict[tuple[str, str], list[dict[str, Any]]],
    dict[tuple[str, str], dict[str, Any]],
    dict[str, Any],
]:
    candidates: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    candidate_instances: dict[str, dict[str, Any]] = {}
    by_axis: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    broad_summary = read_json(BROAD_SUMMARY_PATH)
    broad_profile = profile_from_summary(broad_summary)
    selected_days = summary_selected_days(broad_summary)
    selected_profiles = summary_selected_profiles(broad_summary)
    source_row_counts: Counter[str] = Counter()
    deduplicated_source_row_counts: Counter[str] = Counter()

    bridge_decisions: list[dict[str, Any]] = []
    if BROAD_CANDIDATE_PATH.parent == ROUTE:
        for path in sorted(
            ROUTE.glob("*_REPLAY_BRIDGE*_COMPACT_CANDIDATE_LEDGER.jsonl")
        ):
            artifact_tag = bridge_artifact_tag(path)
            bridge_summary = read_json(path.with_name(f"{artifact_tag}_SUMMARY.json"))
            decision = bridge_source_scope_decision(
                path=path,
                summary=bridge_summary,
                first_row=read_first_jsonl_object(path),
                selected_prefix=BROAD_PREFIX,
                selected_days=selected_days,
                selected_profiles=selected_profiles,
            )
            decision["summary_path"] = str(
                path.with_name(f"{artifact_tag}_SUMMARY.json")
            )
            bridge_decisions.append(decision)
    standalone_bridge_decisions = [
        row
        for row in bridge_decisions
        if row.get("included") is True and row.get("standalone_selected") is True
    ]
    source_scope_mode = (
        "standalone_selected_package_bridge"
        if standalone_bridge_decisions
        else "exact_broad_prefix"
    )
    selected_date_start = (
        selected_days[0]
        if selected_days
        else text(broad_summary.get("date_start"))
    )
    selected_date_end = (
        selected_days[-1]
        if selected_days
        else text(broad_summary.get("date_end"))
    )
    source_scope: dict[str, Any] = {
        "schema": (
            "gtos.final_moonshot.denominator_to_deployment."
            "candidate_projection_source_scope.v1"
        ),
        "mode": source_scope_mode,
        "selected_prefix": BROAD_PREFIX,
        "selected_date_start": selected_date_start,
        "selected_date_end": selected_date_end,
        "selected_days": selected_days,
        "selected_profiles": selected_profiles,
        "candidate_producer_policy": (
            "authoritative_candidate_or_index_first_order_trade_missed_enrichment_only;"
            "fallback_materialization_only_when_authoritative_candidate_source_unavailable"
        ),
        "bridge_artifacts_considered": len(bridge_decisions),
        "bridge_artifacts_included": sum(
            int(row.get("included") is True) for row in bridge_decisions
        ),
        "bridge_artifacts_excluded": sum(
            int(row.get("included") is not True) for row in bridge_decisions
        ),
        "included_bridge_artifacts": [
            row for row in bridge_decisions if row.get("included") is True
        ],
        "excluded_bridge_artifacts": [
            row for row in bridge_decisions if row.get("included") is not True
        ],
        "excluded_bridge_declared_candidate_rows": sum(
            int(row.get("declared_candidate_rows") or 0)
            for row in bridge_decisions
            if row.get("included") is not True
        ),
        "authoritative_candidate_source_available": False,
        "authoritative_candidate_source_class": "",
        "authoritative_candidate_source_paths": [],
        "authoritative_candidate_declared_rows": None,
        "fallback_candidate_materialization_enabled": False,
        "bridge_candidate_producer_artifacts_suppressed_by_authoritative_source": [],
        "bridge_candidate_producer_rows_suppressed_by_authoritative_source": 0,
    }

    def annotated_candidate_rows(
        path: Path,
        *,
        source_class: str,
        binding_status: str,
        source_summary: Mapping[str, Any],
        bridge_artifact: str = "",
        fallback_split: str = "",
    ) -> Iterable[Mapping[str, Any]]:
        for row in iter_jsonl(path):
            source_row_counts[source_class] += 1
            enriched = dict(row)
            enriched["broad_replay_profile"] = profile_from_row_or_summary(
                enriched,
                source_summary,
            )
            if enriched["broad_replay_profile"] == "unknown_profile" and broad_profile:
                enriched["broad_replay_profile"] = broad_profile
            if fallback_split:
                enriched.setdefault("split", fallback_split)
                enriched.setdefault("chunk_id", path.stem)
                enriched.setdefault(
                    "ledger_materialized_candidate_source_path",
                    str(path),
                )
            if bridge_artifact:
                enriched.setdefault("split", "selected_package_replay_bridge")
                enriched.setdefault("chunk_id", path.stem)
                enriched.setdefault(
                    "selected_package_replay_bridge_artifact_tag",
                    bridge_artifact,
                )
                enriched.setdefault("compact_bridge_candidate_source_path", str(path))
            enriched.update(
                {
                    "projection_source_scope_mode": source_scope_mode,
                    "projection_source_prefix": BROAD_PREFIX,
                    "projection_selected_date_start": selected_date_start,
                    "projection_selected_date_end": selected_date_end,
                    "projection_selected_profiles": selected_profiles,
                    "projection_candidate_source_class": source_class,
                    "projection_candidate_source_path": str(path),
                    "projection_candidate_source_binding_status": binding_status,
                }
            )
            yield enriched

    def active_candidate_rows() -> Iterable[Mapping[str, Any]]:
        candidate_ledger_available = (
            BROAD_CANDIDATE_PATH.exists()
            and BROAD_CANDIDATE_PATH.stat().st_size > 0
        )
        candidate_index_available = (
            BROAD_CANDIDATE_INDEX_PATH.exists()
            and BROAD_CANDIDATE_INDEX_PATH.stat().st_size > 0
        )
        authoritative_source_available = False
        if standalone_bridge_decisions:
            authoritative_source_available = True
            source_scope["authoritative_candidate_source_available"] = True
            source_scope["authoritative_candidate_source_class"] = (
                "standalone_selected_package_bridge_candidate_ledger"
            )
            source_scope["authoritative_candidate_source_paths"] = [
                text(row.get("path")) for row in standalone_bridge_decisions
            ]
            source_scope["authoritative_candidate_declared_rows"] = sum(
                int(row.get("declared_candidate_rows") or 0)
                for row in standalone_bridge_decisions
            ) or None
        elif candidate_ledger_available:
            authoritative_source_available = True
            source_scope["authoritative_candidate_source_available"] = True
            source_scope["authoritative_candidate_source_class"] = (
                "authoritative_broad_candidate_ledger"
            )
            source_scope["authoritative_candidate_source_paths"] = [
                str(BROAD_CANDIDATE_PATH)
            ]
            source_scope["authoritative_candidate_declared_rows"] = (
                broad_summary_declared_candidate_rows(broad_summary)
            )
            yield from annotated_candidate_rows(
                BROAD_CANDIDATE_PATH,
                source_class="authoritative_broad_candidate_ledger",
                binding_status="exact_selected_broad_prefix_candidate_authority",
                source_summary=broad_summary,
            )
        elif candidate_index_available:
            authoritative_source_available = True
            source_scope["authoritative_candidate_source_available"] = True
            source_scope["authoritative_candidate_source_class"] = (
                "authoritative_broad_candidate_index"
            )
            source_scope["authoritative_candidate_source_paths"] = [
                str(BROAD_CANDIDATE_INDEX_PATH)
            ]
            source_scope["authoritative_candidate_declared_rows"] = (
                broad_summary_declared_candidate_rows(broad_summary)
            )
            yield from annotated_candidate_rows(
                BROAD_CANDIDATE_INDEX_PATH,
                source_class="authoritative_broad_candidate_index",
                binding_status="exact_selected_broad_prefix_candidate_index_authority",
                source_summary=broad_summary,
            )

        for decision in bridge_decisions:
            if decision.get("included") is not True:
                continue
            if (
                authoritative_source_available
                and decision.get("standalone_selected") is not True
            ):
                source_scope[
                    "bridge_candidate_producer_artifacts_suppressed_by_authoritative_source"
                ].append(text(decision.get("artifact_tag")))
                source_scope[
                    "bridge_candidate_producer_rows_suppressed_by_authoritative_source"
                ] += int(decision.get("declared_candidate_rows") or 0)
                continue
            path = Path(text(decision.get("path")))
            artifact_tag = text(decision.get("artifact_tag"))
            bridge_summary = read_json(
                Path(text(decision.get("summary_path")))
            )
            source_class = (
                "standalone_selected_package_bridge_candidate_ledger"
                if decision.get("standalone_selected") is True
                else "exact_bound_selected_package_bridge_candidate_ledger"
            )
            yield from annotated_candidate_rows(
                path,
                source_class=source_class,
                binding_status=text(decision.get("binding_status")),
                source_summary=bridge_summary,
                bridge_artifact=artifact_tag,
            )
            if not authoritative_source_available:
                authoritative_source_available = True
                source_scope["authoritative_candidate_source_available"] = True
                source_scope["authoritative_candidate_source_class"] = source_class
                source_scope["authoritative_candidate_source_paths"] = [str(path)]
                source_scope["authoritative_candidate_declared_rows"] = int(
                    decision.get("declared_candidate_rows") or 0
                ) or None

        if authoritative_source_available:
            return
        source_scope["fallback_candidate_materialization_enabled"] = True
        source_scope["authoritative_candidate_source_class"] = (
            "fallback_current_prefix_order_trade_missed_materialization"
        )
        materialized_candidate_sources = (
            (BROAD_ORDER_PATH, "fallback_broad_order_materialized_candidate"),
            (BROAD_TRADE_PATH, "fallback_broad_trade_materialized_candidate"),
            (BROAD_MISSED_PATH, "fallback_broad_missed_materialized_candidate"),
        )
        for source_path, source_class in materialized_candidate_sources:
            yield from annotated_candidate_rows(
                source_path,
                source_class=source_class,
                binding_status=(
                    "authoritative_candidate_ledger_and_index_unavailable_"
                    "current_prefix_fallback_materialization"
                ),
                source_summary=broad_summary,
                fallback_split=source_class,
            )

    for row in active_candidate_rows():
        reduced = reduced_candidate(row)
        key = candidate_key(reduced)
        if not key[1]:
            continue
        existing = candidates.get(key)
        if existing is not None:
            source_class = text(
                reduced.get("projection_candidate_source_class"),
                "unknown_candidate_source",
            )
            deduplicated_source_row_counts[source_class] += 1
            existing_executable = existing.get("package_replay_candidate_use_allowed") is True
            reduced_executable = reduced.get("package_replay_candidate_use_allowed") is True
            if reduced_executable and not existing_executable:
                existing_instance_key = existing["candidate_instance_key"]
                source_metadata = {
                    field: value
                    for field, value in existing.items()
                    if field.startswith("projection_")
                }
                existing.update(reduced)
                existing["candidate_instance_key"] = existing_instance_key
                existing.update(source_metadata)
            existing_axis_ids = set(package_member_axis_ids(existing))
            new_axis_ids = set(package_member_axis_ids(reduced))
            if new_axis_ids - existing_axis_ids:
                merged_axis_ids = sorted(existing_axis_ids | new_axis_ids)
                existing["matched_stable_member_axis_ids"] = merged_axis_ids
                existing["ultimate_package_matched_member_axis_ids"] = merged_axis_ids
                existing["selected_package_matched_member_axis_ids"] = merged_axis_ids
            continue
        candidates[key] = reduced
        candidate_instances[reduced["candidate_instance_key"]] = reduced
        by_axis[(reduced["symbol"], reduced["side"])].append(reduced)

    enrichment: dict[str, SparseCandidateEnrichment] = defaultdict(
        SparseCandidateEnrichment
    )
    candidate_id_index: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in candidates.values():
        candidate_id_index[(row["broad_replay_profile"], row["candidate_id"])].append(
            row["candidate_instance_key"]
        )

    def fallback_instance_keys(
        row: Mapping[str, Any],
        *,
        require_unique: bool = False,
    ) -> list[str]:
        profile = text(row.get("broad_replay_profile"))
        candidate_id = text(row.get("candidate_id"))
        if not candidate_id:
            return []
        fallback = candidate_id_index.get((profile, candidate_id), [])
        if not fallback:
            return []

        decision_time = text(row.get("decision_time_utc"))
        row_symbol = upper(row.get("symbol"))
        row_side = side(row.get("side") or row.get("direction"))
        row_split = text(row.get("split"))
        row_chunk = text(row.get("chunk_id"))
        matches: list[str] = []
        for key in fallback:
            candidate = candidate_instances.get(key)
            if not candidate:
                continue
            if decision_time and candidate.get("decision_time_utc") != decision_time:
                continue
            if row_symbol and candidate.get("symbol") != row_symbol:
                continue
            if row_side and candidate.get("side") != row_side:
                continue
            if row_split and candidate.get("split") != row_split:
                continue
            if row_chunk and candidate.get("chunk_id") != row_chunk:
                continue
            matches.append(key)
        if require_unique and len(matches) != 1:
            return []
        return matches

    def enrich_keys(
        row: Mapping[str, Any],
        *,
        allow_fallback: bool,
        require_unique_fallback: bool = False,
    ) -> list[tuple[str, str]]:
        exact = candidate_instance_key(row)
        if exact in candidate_instances:
            return [(exact, "candidate_instance_exact")]
        if allow_fallback:
            return [
                (key, "candidate_id_fallback_non_exact")
                for key in fallback_instance_keys(
                    row,
                    require_unique=require_unique_fallback,
                )
            ]
        return []

    for row in candidates.values():
        item = enrichment[row["candidate_instance_key"]]
        item["source_join_class_counts"]["candidate_instance_exact"] += 1
        remember_executable_proof(item, row)
        if row.get("lifecycle_action"):
            item["candidate_lifecycle_action_counts"][text(row.get("lifecycle_action"))] += 1
        if row.get("lifecycle_reason"):
            item["candidate_lifecycle_reason_counts"][text(row.get("lifecycle_reason"))] += 1
        if row.get("lifecycle_permitted") is not None:
            item["risk_lifecycle_permitted_counts"][
                f"candidate_lifecycle_permitted_{bool(row.get('lifecycle_permitted'))}"
            ] += 1
        if row.get("packet_sidecar_id"):
            item["packet_sidecar_ids"].add(text(row.get("packet_sidecar_id")))
        if row.get("packet_sidecar_hash_sha256"):
            item["packet_sidecar_hashes"].add(text(row.get("packet_sidecar_hash_sha256")))

    for row in iter_jsonl(BROAD_PACKET_SIDECAR_PATH):
        candidate_ids = [
            candidate_id
            for candidate_id in [
                text(row.get("candidate_id")),
                *string_list(row.get("selected_candidate_ids")),
            ]
            if candidate_id
        ]
        candidate_ids = list(dict.fromkeys(candidate_ids))
        if not candidate_ids:
            continue
        for candidate_id in candidate_ids:
            sidecar_join_row = {**row, "candidate_id": candidate_id}
            for key, join_class in enrich_keys(sidecar_join_row, allow_fallback=True):
                item = enrichment[key]
                item["source_join_class_counts"][join_class] += 1
                item["packet_sidecar_present"] = True
                item["packet_sidecar_ids"].add(text(row.get("packet_sidecar_id")))
                item["packet_sidecar_hashes"].add(
                    text(
                        row.get("packet_hash_sha256")
                        or row.get("packet_sidecar_hash_sha256")
                    )
                )

    for row in iter_jsonl(BROAD_SCORECARD_PATH):
        selected_id = text(row.get("selected_candidate_id"))
        profile = text(row.get("broad_replay_profile"))
        scheduler_packet = row.get("scheduler_packet")
        scheduler_decision = (
            scheduler_packet.get("decision") if isinstance(scheduler_packet, dict) else {}
        )
        if not isinstance(scheduler_decision, dict):
            scheduler_decision = {}
        selected_ids = set(string_list(scheduler_decision.get("selected_candidate_ids")))
        if selected_id:
            selected_ids.add(selected_id)
        options = row.get("scheduler_option_trace")
        if not isinstance(options, list) or not options:
            options = (
                scheduler_packet.get("all_options_preserved")
                if isinstance(scheduler_packet, dict)
                else []
            )
        if not isinstance(options, list) or not options:
            finalizer = row.get("risk_admitted_scheduler_finalizer")
            probe_rows = (
                finalizer.get("probe_rows")
                if isinstance(finalizer, dict)
                else []
            )
            options = [
                {
                    "candidate_id": probe.get("candidate_id"),
                    **route_provenance_fields(probe),
                    "action_class": probe.get("scheduler_action_class"),
                    "score": probe.get("scheduler_score"),
                    "decision_status": probe.get("risk_decision"),
                    "reason": probe.get("risk_decision_reason"),
                    "runtime_eligible": probe.get("selected") is True
                    or probe.get("risk_decision") in {"trade", "reduce-risk"},
                    "approved_risk_pct": probe.get("final_approved_risk_pct"),
                    "requested_risk_pct": probe.get("final_approved_risk_pct"),
                    "input_sequence": probe.get("rank"),
                    "scheduler_rank": probe.get("rank"),
                }
                for probe in probe_rows
                if isinstance(probe, dict)
            ]
        for rank, option in rank_scheduler_options(options):
            candidate_id = text(option.get("candidate_id"))
            if not candidate_id:
                continue
            for key, join_class in enrich_keys(
                {
                    **row,
                    "candidate_id": candidate_id,
                    "symbol": option.get("symbol") or row.get("symbol"),
                    "side": option.get("side") or row.get("side"),
                },
                allow_fallback=True,
            ):
                item = enrichment[key]
                item["source_join_class_counts"][join_class] += 1
                item["scorecard_present"] = True
                item["scheduler_option_present"] = True
                item["scheduler_option_count"] += 1
                score = safe_float(option.get("score"))
                item["scheduler_rank_min"] = (
                    rank
                    if item["scheduler_rank_min"] is None
                    else min(int(item["scheduler_rank_min"]), rank)
                )
                item["scheduler_score_max"] = (
                    score
                    if item["scheduler_score_max"] is None
                    else max(safe_float(item["scheduler_score_max"]), score)
                )
                item["scheduler_action_class_counts"][text(option.get("action_class"), "unknown")] += 1
                item["scheduler_decision_status_counts"][
                    text(option.get("decision_status"), "unknown")
                ] += 1
                item["scheduler_option_reason_counts"][text(option.get("reason"), "unknown")] += 1
                remember_projection_stage_binding(
                    item,
                    stage="scorecard",
                    binding=projection_stage_binding(
                        option,
                        stage="scorecard",
                        overrides={
                            **route_provenance_fields(option, row),
                            "scheduler_rank": int(
                                safe_float(option.get("scheduler_rank"), rank)
                            ),
                            "scheduler_score": score,
                            "scheduler_selected": candidate_id in selected_ids,
                            "risk_finalizer_action": first_present(
                                option.get("risk_finalizer_decision"),
                                option.get("risk_decision"),
                                option.get("decision_status"),
                            ),
                            "risk_finalizer_reason": first_present(
                                option.get("risk_finalizer_reason"),
                                option.get("risk_decision_reason"),
                                option.get("reason"),
                            ),
                        },
                    ),
                )
                if len(item["scheduler_option_samples"]) < 5:
                    item["scheduler_option_samples"].append(
                        {
                            "decision_time_utc": text(row.get("decision_time_utc")),
                            "scheduler_rank": rank,
                            "scheduler_score": score,
                            "scheduler_action_class": text(option.get("action_class"), "unknown"),
                            "scheduler_decision_status": text(
                                option.get("decision_status"), "unknown"
                            ),
                            "scheduler_reason": text(option.get("reason"), "unknown"),
                            "scheduler_approved_risk_pct": safe_float(
                                option.get("approved_risk_pct")
                            ),
                            "scheduler_requested_risk_pct": safe_float(
                                option.get("requested_risk_pct")
                            ),
                            "scheduler_runtime_eligible": option.get("runtime_eligible"),
                            "source_join_class": join_class,
                        }
                    )
                if candidate_id in selected_ids:
                    item["scheduler_selected"] = True
                    item["selected_action_class_counts"][
                        text(row.get("selected_action_class") or option.get("action_class"), "unknown")
                    ] += 1
                    item["selected_candidate_ids"].add(candidate_id)
        for candidate_id in selected_ids:
            if not candidate_id:
                continue
            for key, join_class in enrich_keys(
                {
                    **row,
                    "candidate_id": candidate_id,
                },
                allow_fallback=True,
                require_unique_fallback=True,
            ):
                item = enrichment[key]
                item["source_join_class_counts"][join_class] += 1
                item["scorecard_present"] = True
                item["scheduler_selected"] = True
                if not item.get("scorecard_binding"):
                    remember_projection_stage_binding(
                        item,
                        stage="scorecard",
                        binding=projection_stage_binding(
                            row,
                            stage="scorecard",
                            overrides={
                                "scheduler_selected": True,
                                "risk_finalizer_action": first_present(
                                    row.get("risk_finalizer_decision"),
                                    row.get("risk_decision"),
                                ),
                                "risk_finalizer_reason": first_present(
                                    row.get("risk_finalizer_reason"),
                                    row.get("risk_decision_reason"),
                                ),
                            },
                        ),
                    )
                if not item.get("scheduler_option_present"):
                    item["selected_action_class_counts"][
                        text(row.get("selected_action_class"), "unknown")
                    ] += 1
                item["selected_candidate_ids"].add(candidate_id)

    for row in iter_jsonl(BROAD_ORDER_PATH):
        for key, join_class in enrich_keys(row, allow_fallback=False):
            item = enrichment[key]
            item["source_join_class_counts"][join_class] += 1
            item["scheduler_selected"] = True
            item["selected_candidate_ids"].add(text(row.get("candidate_id")))
            item["order_present"] = True
            item["order_status_counts"][text(row.get("order_status"), "unknown")] += 1
            item["risk_decision_counts"][text(row.get("risk_decision"), "unknown")] += 1
            item["risk_decision_reason_counts"][text(row.get("risk_decision_reason"), "unknown")] += 1
            item["order_policy_counts"][text(row.get("dynamic_geometry_policy"), "unknown")] += 1
            item["order_architecture_counts"][order_architecture_from_order_row(row)] += 1
            item["order_type_counts"][order_type_from_order_row(row)] += 1
            remember_projection_stage_binding(
                item,
                stage="order",
                binding=projection_stage_binding(row, stage="order"),
            )
            remember_executable_proof(item, row)
            risk_authority = row.get("risk_authority")
            if isinstance(risk_authority, dict):
                lifecycle_action = text(
                    row.get("same_symbol_lifecycle_action")
                    or risk_authority.get("same_symbol_lifecycle_action")
                )
                if lifecycle_action:
                    item["risk_lifecycle_action_counts"][lifecycle_action] += 1
                lifecycle_permitted = (
                    row.get("same_symbol_lifecycle_permitted")
                    if row.get("same_symbol_lifecycle_permitted") is not None
                    else risk_authority.get("same_symbol_lifecycle_permitted")
                )
                if lifecycle_permitted is not None:
                    item["risk_lifecycle_permitted_counts"][
                        f"risk_lifecycle_permitted_{bool(lifecycle_permitted)}"
                    ] += 1
            item["candidate_ids"].add(text(row.get("candidate_id")))

    for row in iter_jsonl(BROAD_ORACLE_PATH):
        for key, join_class in enrich_keys(row, allow_fallback=False):
            item = enrichment[key]
            item["source_join_class_counts"][join_class] += 1
            item["scheduler_selected"] = True
            item["selected_candidate_ids"].add(text(row.get("candidate_id")))
            item["oracle_present"] = True
            item["fill_status_counts"][text(row.get("fill_status"), "unknown")] += 1
            item["counterfactual_fill_status_counts"][
                text(row.get("counterfactual_fill_status"), "unknown")
            ] += 1
            item["fillability_status_counts"][
                text(
                    row.get("fill_status")
                    or row.get("counterfactual_fill_status")
                    or row.get("status"),
                    "unknown",
                )
            ] += 1
            item["terminal_outcome_counts"][text(row.get("terminal_outcome"), "unknown")] += 1
            remember_projection_stage_binding(
                item,
                stage="oracle",
                binding=projection_stage_binding(row, stage="oracle"),
            )

    for row in iter_jsonl(BROAD_TRADE_PATH):
        for key, join_class in enrich_keys(
            row,
            allow_fallback=True,
            require_unique_fallback=True,
        ):
            item = enrichment[key]
            item["source_join_class_counts"][join_class] += 1
            item["scheduler_selected"] = True
            trade_candidate_id = text(row.get("candidate_id"))
            item["selected_candidate_ids"].add(trade_candidate_id)
            item["trade_present"] = True
            item["trade_count"] += 1
            item["trade_candidate_instance_keys"].add(key)
            item["trade_actual_r_by_candidate_instance_key"][key] = add(
                item["trade_actual_r_by_candidate_instance_key"].get(key),
                row.get("net_proxy_r") or row.get("net_r"),
            )
            item["trade_gross_r_by_candidate_instance_key"][key] = add(
                item["trade_gross_r_by_candidate_instance_key"].get(key),
                row.get("gross_r"),
            )
            item["trade_final_r_by_candidate_instance_key"][key] = add(
                item["trade_final_r_by_candidate_instance_key"].get(key),
                row.get("final_r"),
            )
            item["trade_cash_pnl_by_candidate_instance_key"][key] = add(
                item["trade_cash_pnl_by_candidate_instance_key"].get(key),
                row.get("pnl_cash"),
            )
            if trade_candidate_id:
                item["trade_candidate_ids"].add(trade_candidate_id)
                item["trade_actual_r_by_candidate_id"][trade_candidate_id] = add(
                    item["trade_actual_r_by_candidate_id"].get(trade_candidate_id),
                    row.get("net_proxy_r") or row.get("net_r"),
                )
                item["trade_gross_r_by_candidate_id"][trade_candidate_id] = add(
                    item["trade_gross_r_by_candidate_id"].get(trade_candidate_id),
                    row.get("gross_r"),
                )
                item["trade_final_r_by_candidate_id"][trade_candidate_id] = add(
                    item["trade_final_r_by_candidate_id"].get(trade_candidate_id),
                    row.get("final_r"),
                )
                item["trade_cash_pnl_by_candidate_id"][trade_candidate_id] = add(
                    item["trade_cash_pnl_by_candidate_id"].get(trade_candidate_id),
                    row.get("pnl_cash"),
                )
            item["close_reason_counts"][text(row.get("close_reason"), "unknown")] += 1
            item["terminal_outcome_counts"][text(row.get("terminal_outcome"), "unknown")] += 1
            item["exit_result_counts"][
                text(
                    row.get("terminal_outcome")
                    or row.get("close_reason")
                    or row.get("profit_harvest_mfe_capture_replay_exit"),
                    "unknown",
                )
            ] += 1
            item["gross_r"] = add(item["gross_r"], row.get("gross_r"))
            item["final_r"] = add(item["final_r"], row.get("final_r"))
            item["net_r"] = add(item["net_r"], row.get("net_proxy_r") or row.get("net_r"))
            item["cash_pnl"] = add(item["cash_pnl"], row.get("pnl_cash"))
            item["risk_cash"] = add(item["risk_cash"], row.get("risk_cash"))
            item["risk_pct"] = add(item["risk_pct"], row.get("risk_pct"))
            remember_projection_stage_binding(
                item,
                stage="trade",
                binding=projection_stage_binding(row, stage="trade"),
            )
            remember_executable_proof(item, row)

    for row in iter_jsonl(BROAD_MISSED_PATH):
        for key, join_class in enrich_keys(row, allow_fallback=False):
            net = safe_float(
                row.get("net_proxy_r")
                if row.get("net_proxy_r") not in (None, "")
                else row.get("opportunity_net_proxy_r")
            )
            item = enrichment[key]
            item["source_join_class_counts"][join_class] += 1
            item["missed_present"] = True
            item["missed_count"] += 1
            item["miss_reason_counts"][text(row.get("miss_reason"), "unknown")] += 1
            item["missed_net_proxy_r"] = add(item["missed_net_proxy_r"], net)
            if net > 0:
                item["missed_positive_net_r"] = add(item["missed_positive_net_r"], net)
            elif net < 0:
                item["missed_negative_net_r"] = add(item["missed_negative_net_r"], net)
            remember_projection_stage_binding(
                item,
                stage="missed",
                binding=projection_stage_binding(row, stage="missed"),
            )
            remember_executable_proof(item, row)

    source_scope["candidate_source_rows_read"] = sum(source_row_counts.values())
    source_scope["candidate_source_row_counts"] = counter_dict(source_row_counts)
    source_scope["candidate_source_rows_deduplicated"] = sum(
        deduplicated_source_row_counts.values()
    )
    source_scope["candidate_source_deduplicated_counts"] = counter_dict(
        deduplicated_source_row_counts
    )
    source_scope["candidate_instances_materialized"] = len(candidates)
    source_scope["order_trade_missed_candidate_producer_rows"] = sum(
        count
        for source_class, count in source_row_counts.items()
        if source_class.startswith("fallback_broad_")
    )
    return candidates, by_axis, enrichment, source_scope


def load_broad_indexes() -> tuple[
    dict[tuple[str, str, str, str, str], dict[str, Any]],
    dict[tuple[str, str], list[dict[str, Any]]],
    dict[tuple[str, str], dict[str, Any]],
]:
    """Compatibility wrapper for callers that do not consume source scope."""

    candidates, by_axis, enrichment, _source_scope = (
        _load_broad_indexes_with_scope()
    )
    return candidates, by_axis, enrichment


def summarize_enrichment(items: list[dict[str, Any]], enrichment: Mapping[tuple[str, str], Mapping[str, Any]]) -> dict[str, Any]:
    selector_action_counts: Counter[str] = Counter()
    selector_reason_counts: Counter[str] = Counter()
    scheduler_action_counts: Counter[str] = Counter()
    scheduler_status_counts: Counter[str] = Counter()
    scheduler_reason_counts: Counter[str] = Counter()
    selected_action_counts: Counter[str] = Counter()
    risk_decision_counts: Counter[str] = Counter()
    risk_reason_counts: Counter[str] = Counter()
    order_status_counts: Counter[str] = Counter()
    order_policy_counts: Counter[str] = Counter()
    order_architecture_counts: Counter[str] = Counter()
    order_type_counts: Counter[str] = Counter()
    fill_status_counts: Counter[str] = Counter()
    counterfactual_fill_status_counts: Counter[str] = Counter()
    fillability_status_counts: Counter[str] = Counter()
    terminal_counts: Counter[str] = Counter()
    close_counts: Counter[str] = Counter()
    exit_result_counts: Counter[str] = Counter()
    candidate_lifecycle_action_counts: Counter[str] = Counter()
    candidate_lifecycle_reason_counts: Counter[str] = Counter()
    risk_lifecycle_action_counts: Counter[str] = Counter()
    risk_lifecycle_permitted_counts: Counter[str] = Counter()
    miss_reason_counts: Counter[str] = Counter()
    pretrade_cost_status_counts: Counter[str] = Counter()
    cost_source_gap_status_counts: Counter[str] = Counter()
    pretrade_cost_refusal_reason_counts: Counter[str] = Counter()
    candidate_ids: set[str] = set()
    candidate_instance_keys: set[str] = set()
    selected_ids: set[str] = set()
    selected_instance_keys: set[str] = set()
    trade_candidate_ids: set[str] = set()
    trade_candidate_instance_keys: set[str] = set()
    unique_trade_actual_r_by_candidate_id: dict[str, float] = {}
    unique_trade_gross_r_by_candidate_id: dict[str, float] = {}
    unique_trade_final_r_by_candidate_id: dict[str, float] = {}
    unique_trade_cash_pnl_by_candidate_id: dict[str, float] = {}
    unique_trade_actual_r_by_candidate_instance_key: dict[str, float] = {}
    unique_trade_gross_r_by_candidate_instance_key: dict[str, float] = {}
    unique_trade_final_r_by_candidate_instance_key: dict[str, float] = {}
    unique_trade_cash_pnl_by_candidate_instance_key: dict[str, float] = {}
    decision_windows: set[str] = set()
    scheduler_option_candidate_ids: set[str] = set()
    scheduler_ranks: list[int] = []
    scheduler_scores: list[float] = []
    trade_count = 0
    missed_count = 0
    actual_r_sum = 0.0
    gross_r_sum = 0.0
    final_r_sum = 0.0
    cash_pnl_sum = 0.0
    risk_cash_sum = 0.0
    risk_pct_sum = 0.0
    missed_net = 0.0
    missed_positive = 0.0
    missed_negative = 0.0
    order_present_count = 0
    oracle_present_count = 0
    scorecard_selected_count = 0
    scorecard_present_count = 0

    for row in items:
        candidate_ids.add(row["candidate_id"])
        candidate_instance_keys.add(row["candidate_instance_key"])
        decision_windows.add(row["stable_decision_window_id"])
        selector_action_counts[row["selector_action"]] += 1
        selector_reason_counts[row["selector_reason"]] += 1
        pretrade_cost_status_counts[
            text(row.get("pretrade_cost_packet_status"), "unknown")
        ] += 1
        cost_source_gap_status_counts[
            text(row.get("cost_source_gap_status"), "unknown")
        ] += 1
        pretrade_cost_refusal_reason_counts.update(
            string_list(row.get("pretrade_cost_refusal_reasons"))
        )
        key = row["candidate_instance_key"]
        enrich = enrichment.get(key, {})
        if enrich.get("scheduler_selected"):
            scorecard_selected_count += 1
            selected_instance_keys.add(row["candidate_instance_key"])
        if enrich.get("scorecard_present"):
            scorecard_present_count += 1
        if enrich.get("order_present"):
            order_present_count += 1
        if enrich.get("oracle_present"):
            oracle_present_count += 1
        for counter_name, target in (
            ("scheduler_action_class_counts", scheduler_action_counts),
            ("scheduler_decision_status_counts", scheduler_status_counts),
            ("scheduler_option_reason_counts", scheduler_reason_counts),
            ("selected_action_class_counts", selected_action_counts),
            ("risk_decision_counts", risk_decision_counts),
            ("risk_decision_reason_counts", risk_reason_counts),
            ("order_status_counts", order_status_counts),
            ("order_policy_counts", order_policy_counts),
            ("order_architecture_counts", order_architecture_counts),
            ("order_type_counts", order_type_counts),
            ("fill_status_counts", fill_status_counts),
            ("counterfactual_fill_status_counts", counterfactual_fill_status_counts),
            ("fillability_status_counts", fillability_status_counts),
            ("terminal_outcome_counts", terminal_counts),
            ("close_reason_counts", close_counts),
            ("exit_result_counts", exit_result_counts),
            ("candidate_lifecycle_action_counts", candidate_lifecycle_action_counts),
            ("candidate_lifecycle_reason_counts", candidate_lifecycle_reason_counts),
            ("risk_lifecycle_action_counts", risk_lifecycle_action_counts),
            ("risk_lifecycle_permitted_counts", risk_lifecycle_permitted_counts),
            ("miss_reason_counts", miss_reason_counts),
        ):
            target.update(enrich.get(counter_name, {}))
        if enrich.get("scheduler_option_present"):
            scheduler_option_candidate_ids.add(row["candidate_id"])
        if enrich.get("scheduler_rank_min") is not None:
            scheduler_ranks.append(int(enrich["scheduler_rank_min"]))
        if enrich.get("scheduler_score_max") is not None:
            scheduler_scores.append(safe_float(enrich.get("scheduler_score_max")))
        selected_ids.update(enrich.get("selected_candidate_ids", set()))
        trade_candidate_ids.update(enrich.get("trade_candidate_ids", set()))
        trade_candidate_instance_keys.update(
            enrich.get("trade_candidate_instance_keys", set())
        )
        for source_name, target in (
            ("trade_actual_r_by_candidate_id", unique_trade_actual_r_by_candidate_id),
            ("trade_gross_r_by_candidate_id", unique_trade_gross_r_by_candidate_id),
            ("trade_final_r_by_candidate_id", unique_trade_final_r_by_candidate_id),
            ("trade_cash_pnl_by_candidate_id", unique_trade_cash_pnl_by_candidate_id),
        ):
            for candidate_id, value in (enrich.get(source_name) or {}).items():
                target[text(candidate_id)] = add(target.get(text(candidate_id)), value)
        for source_name, target in (
            (
                "trade_actual_r_by_candidate_instance_key",
                unique_trade_actual_r_by_candidate_instance_key,
            ),
            (
                "trade_gross_r_by_candidate_instance_key",
                unique_trade_gross_r_by_candidate_instance_key,
            ),
            (
                "trade_final_r_by_candidate_instance_key",
                unique_trade_final_r_by_candidate_instance_key,
            ),
            (
                "trade_cash_pnl_by_candidate_instance_key",
                unique_trade_cash_pnl_by_candidate_instance_key,
            ),
        ):
            for instance_key, value in (enrich.get(source_name) or {}).items():
                target[text(instance_key)] = add(target.get(text(instance_key)), value)
        trade_count += int(enrich.get("trade_count", 0))
        missed_count += int(enrich.get("missed_count", 0))
        actual_r_sum = add(actual_r_sum, enrich.get("net_r"))
        gross_r_sum = add(gross_r_sum, enrich.get("gross_r"))
        final_r_sum = add(final_r_sum, enrich.get("final_r"))
        cash_pnl_sum = add(cash_pnl_sum, enrich.get("cash_pnl"))
        risk_cash_sum = add(risk_cash_sum, enrich.get("risk_cash"))
        risk_pct_sum = add(risk_pct_sum, enrich.get("risk_pct"))
        missed_net = add(missed_net, enrich.get("missed_net_proxy_r"))
        missed_positive = add(missed_positive, enrich.get("missed_positive_net_r"))
        missed_negative = add(missed_negative, enrich.get("missed_negative_net_r"))

    return {
        "candidate_generated_count": len(candidate_instance_keys),
        "candidate_generated_bare_id_count": len(candidate_ids),
        "unique_decision_windows": len(decision_windows),
        "selector_action_counts": counter_dict(selector_action_counts),
        "selector_reason_counts": top_counter(selector_reason_counts),
        "pretrade_cost_packet_status_counts": counter_dict(pretrade_cost_status_counts),
        "cost_source_gap_status_counts": counter_dict(cost_source_gap_status_counts),
        "pretrade_cost_refusal_reason_counts": top_counter(
            pretrade_cost_refusal_reason_counts
        ),
        "scorecard_present_count": scorecard_present_count,
        "scheduler_option_present_count": scorecard_present_count,
        "scheduler_rank_min": min(scheduler_ranks) if scheduler_ranks else None,
        "scheduler_score_max": max(scheduler_scores) if scheduler_scores else None,
        "scheduler_action_class_counts": counter_dict(scheduler_action_counts),
        "scheduler_decision_status_counts": top_counter(scheduler_status_counts),
        "scheduler_option_reason_counts": top_counter(scheduler_reason_counts),
        "scorecard_selected_count": scorecard_selected_count,
        "selected_candidate_count": len(selected_instance_keys),
        "selected_bare_candidate_id_count": len(selected_ids),
        "selected_action_class_counts": counter_dict(selected_action_counts),
        "order_present_count": order_present_count,
        "oracle_present_count": oracle_present_count,
        "risk_decision_counts": counter_dict(risk_decision_counts),
        "risk_decision_reason_counts": top_counter(risk_reason_counts),
        "order_status_counts": counter_dict(order_status_counts),
        "order_policy_counts": counter_dict(order_policy_counts),
        "order_architecture_counts": counter_dict(order_architecture_counts),
        "order_type_counts": counter_dict(order_type_counts),
        "fill_status_counts": counter_dict(fill_status_counts),
        "counterfactual_fill_status_counts": counter_dict(counterfactual_fill_status_counts),
        "fillability_status_counts": counter_dict(fillability_status_counts),
        "terminal_outcome_counts": counter_dict(terminal_counts),
        "close_reason_counts": counter_dict(close_counts),
        "exit_result_counts": counter_dict(exit_result_counts),
        "candidate_lifecycle_action_counts": counter_dict(candidate_lifecycle_action_counts),
        "candidate_lifecycle_reason_counts": top_counter(candidate_lifecycle_reason_counts),
        "risk_lifecycle_action_counts": counter_dict(risk_lifecycle_action_counts),
        "risk_lifecycle_permitted_counts": counter_dict(risk_lifecycle_permitted_counts),
        "trade_count": trade_count,
        "axis_attributed_trade_count": trade_count,
        "unique_trade_candidate_count": len(trade_candidate_instance_keys),
        "unique_trade_candidate_instance_count": len(trade_candidate_instance_keys),
        "unique_trade_bare_candidate_id_count": len(trade_candidate_ids),
        "unique_replay_trade_identity": (
            "candidate_instance_key_exact_within_broad_replay_profile"
        ),
        "gross_r_sum": gross_r_sum,
        "final_r_sum": final_r_sum,
        "actual_r_sum": actual_r_sum,
        "axis_attributed_actual_r_sum": actual_r_sum,
        "unique_actual_r_sum": sum(
            unique_trade_actual_r_by_candidate_instance_key.values()
        ),
        "unique_gross_r_sum": sum(
            unique_trade_gross_r_by_candidate_instance_key.values()
        ),
        "unique_final_r_sum": sum(
            unique_trade_final_r_by_candidate_instance_key.values()
        ),
        "unique_cash_pnl_sum": sum(
            unique_trade_cash_pnl_by_candidate_instance_key.values()
        ),
        "unique_trade_actual_r_by_candidate_instance_key": dict(
            sorted(unique_trade_actual_r_by_candidate_instance_key.items())
        ),
        "unique_trade_gross_r_by_candidate_instance_key": dict(
            sorted(unique_trade_gross_r_by_candidate_instance_key.items())
        ),
        "unique_trade_final_r_by_candidate_instance_key": dict(
            sorted(unique_trade_final_r_by_candidate_instance_key.items())
        ),
        "unique_trade_cash_pnl_by_candidate_instance_key": dict(
            sorted(unique_trade_cash_pnl_by_candidate_instance_key.items())
        ),
        "unique_trade_actual_r_by_candidate_id": dict(
            sorted(unique_trade_actual_r_by_candidate_id.items())
        ),
        "unique_trade_gross_r_by_candidate_id": dict(
            sorted(unique_trade_gross_r_by_candidate_id.items())
        ),
        "unique_trade_final_r_by_candidate_id": dict(
            sorted(unique_trade_final_r_by_candidate_id.items())
        ),
        "unique_trade_cash_pnl_by_candidate_id": dict(
            sorted(unique_trade_cash_pnl_by_candidate_id.items())
        ),
        "cash_pnl_sum": cash_pnl_sum,
        "risk_cash_sum": risk_cash_sum,
        "risk_pct_sum": risk_pct_sum,
        "missed_count": missed_count,
        "miss_reason_counts": top_counter(miss_reason_counts),
        "missed_net_proxy_r_sum": missed_net,
        "missed_positive_net_r_sum": missed_positive,
        "missed_negative_net_r_sum": missed_negative,
        "candidate_id_samples": sorted(candidate_ids)[:8],
        "selected_candidate_id_samples": sorted(selected_ids)[:8],
        "trade_candidate_id_samples": sorted(trade_candidate_ids)[:8],
        "trade_candidate_instance_key_samples": sorted(
            trade_candidate_instance_keys
        )[:8],
    }


def order_status_indicates_unfilled(status: Any) -> bool:
    text_value = str(status or "").strip().lower()
    if not text_value:
        return False
    if text_value in {"expired", "not_filled", "unfilled"}:
        return True
    return any(
        token in text_value
        for token in (
            "expired_unfilled",
            "accepted_not_filled",
            "pending_until_expiry",
            "not_filled",
            "unfilled",
        )
    )


def leakage_label(summary: Mapping[str, Any]) -> str:
    if int(summary.get("candidate_generated_count", 0)) <= 0:
        return "candidate_not_generated"
    selector_counts = summary.get("selector_action_counts") or {}
    if int(summary.get("scorecard_selected_count", 0)) <= 0:
        if selector_counts and set(selector_counts) <= {"reject"}:
            cost_status_counts = summary.get("pretrade_cost_packet_status_counts") or {}
            if cost_status_counts and set(cost_status_counts) <= {"REFUSED"}:
                return "candidate_generated_broker_cost_refused_not_executable"
            cost_source_gap_counts = summary.get("cost_source_gap_status_counts") or {}
            executable_cost_statuses = {
                "source_bound_cost_authority_present",
                "unknown",
            }
            if cost_source_gap_counts and not set(cost_source_gap_counts) <= executable_cost_statuses:
                top_cost_gap = max(
                    cost_source_gap_counts,
                    key=lambda status: (
                        int(cost_source_gap_counts.get(status) or 0),
                        str(status),
                    ),
                )
                return f"candidate_generated_broker_cost_source_gap_not_executable:{top_cost_gap}"
            downstream_execution_counts = {
                "scheduler_option_present_count": int(
                    summary.get("scheduler_option_present_count") or 0
                ),
                "order_present_count": int(summary.get("order_present_count") or 0),
                "oracle_present_count": int(summary.get("oracle_present_count") or 0),
                "trade_count": int(summary.get("trade_count") or 0),
            }
            nonzero_downstream = [
                name for name, count in downstream_execution_counts.items() if count > 0
            ]
            if nonzero_downstream:
                return (
                    "candidate_generated_selector_reject_downstream_execution_"
                    f"materialized:{nonzero_downstream[0]}"
                )
            return "candidate_generated_selector_reject"
        if "reduce-risk" in selector_counts and "trade" not in selector_counts:
            cost_status_counts = summary.get("pretrade_cost_packet_status_counts") or {}
            if cost_status_counts and set(cost_status_counts) <= {"REFUSED"}:
                return "candidate_generated_broker_cost_refused_not_executable"
            miss_reason_counts = summary.get("miss_reason_counts") or {}
            top_miss_reason = ""
            if miss_reason_counts:
                top_miss_reason = max(
                    miss_reason_counts,
                    key=lambda reason: (
                        int(miss_reason_counts.get(reason) or 0),
                        str(reason),
                    ),
                )
            risk_reason_counts = summary.get("risk_decision_reason_counts") or {}
            top_risk_reason = ""
            if risk_reason_counts:
                top_risk_reason = max(
                    risk_reason_counts,
                    key=lambda reason: (
                        int(risk_reason_counts.get(reason) or 0),
                        str(reason),
                    ),
                )
            if top_miss_reason == "risk_finalizer_rejected_preselected_candidate":
                suffix = f":{top_risk_reason}" if top_risk_reason else ""
                return (
                    "candidate_generated_selector_reduce_risk_ranked_"
                    f"risk_finalizer_rejected{suffix}"
                )
            if top_miss_reason == "scheduler_zero_trade_window_candidate_not_preselected":
                return (
                    "candidate_generated_selector_reduce_risk_"
                    "zero_trade_conversion_disabled"
                )
            if top_miss_reason == "scheduler_selected_competing_candidate":
                return (
                    "candidate_generated_selector_reduce_risk_"
                    "scheduler_competing_candidate"
                )
            if top_miss_reason == "scheduler_option_missing_nonselected_candidate":
                return (
                    "candidate_generated_selector_reduce_risk_"
                    "scheduler_option_missing"
                )
            return "candidate_generated_selector_reduce_risk_not_scheduler_selected"
        return "candidate_generated_not_scheduler_selected"
    if int(summary.get("order_present_count", 0)) <= 0:
        return "scheduler_selected_no_order_row"
    risk_counts = summary.get("risk_decision_counts") or {}
    order_status_counts = summary.get("order_status_counts") or {}
    if int(summary.get("trade_count", 0)) <= 0:
        if risk_counts.get("reject", 0) > 0:
            return "scheduler_selected_risk_rejected"
        if any(
            int(count or 0) > 0 and order_status_indicates_unfilled(status)
            for status, count in order_status_counts.items()
        ):
            return "order_accepted_not_filled"
        return "scheduler_selected_no_trade"
    if safe_float(summary.get("actual_r_sum")) > 0:
        return "executed_positive_r"
    if safe_float(summary.get("actual_r_sum")) < 0:
        return "executed_negative_r"
    return "executed_flat_r"


def apply_execution_leakage_accounting(
    summary: Mapping[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    """Separate blocked counterfactuals from executable missed-opportunity R."""

    adjusted = dict(summary)
    missed_count = int(adjusted.get("missed_count") or 0)
    missed_net = safe_float(adjusted.get("missed_net_proxy_r_sum"))
    missed_positive = safe_float(adjusted.get("missed_positive_net_r_sum"))
    missed_negative = safe_float(adjusted.get("missed_negative_net_r_sum"))
    miss_reasons = adjusted.get("miss_reason_counts") or {}
    adjusted.setdefault("blocked_counterfactual_missed_count", 0)
    adjusted.setdefault("blocked_counterfactual_missed_net_proxy_r_sum", 0.0)
    adjusted.setdefault("blocked_counterfactual_missed_positive_net_r_sum", 0.0)
    adjusted.setdefault("blocked_counterfactual_missed_negative_net_r_sum", 0.0)
    adjusted.setdefault("blocked_counterfactual_miss_reason_counts", {})
    adjusted["missed_opportunity_accounting"] = "execution_stage_missed_opportunity"
    if label in BLOCKED_COUNTERFACTUAL_MISSED_LABELS or any(
        label.startswith(prefix) for prefix in BLOCKED_COUNTERFACTUAL_MISSED_LABEL_PREFIXES
    ):
        adjusted["blocked_counterfactual_missed_count"] = missed_count
        adjusted["blocked_counterfactual_missed_net_proxy_r_sum"] = missed_net
        adjusted["blocked_counterfactual_missed_positive_net_r_sum"] = missed_positive
        adjusted["blocked_counterfactual_missed_negative_net_r_sum"] = missed_negative
        adjusted["blocked_counterfactual_miss_reason_counts"] = miss_reasons
        adjusted["missed_count"] = 0
        adjusted["miss_reason_counts"] = {}
        adjusted["missed_net_proxy_r_sum"] = 0.0
        adjusted["missed_positive_net_r_sum"] = 0.0
        adjusted["missed_negative_net_r_sum"] = 0.0
        adjusted["missed_opportunity_accounting"] = (
            "blocked_counterfactual_not_execution_leakage"
        )
    return adjusted


def candidate_deviation_reason(
    candidate: Mapping[str, Any],
    enrich: Mapping[str, Any],
) -> str:
    selector_action = text(candidate.get("selector_action"), "unknown")
    if selector_action == "reject":
        downstream_execution_fields = []
        if enrich.get("scheduler_option_present"):
            downstream_execution_fields.append("scheduler_option_present")
        if enrich.get("order_present"):
            downstream_execution_fields.append("order_present")
        if enrich.get("oracle_present"):
            downstream_execution_fields.append("oracle_present")
        if int(enrich.get("trade_count") or 0) > 0:
            downstream_execution_fields.append("trade_present")
        if int(enrich.get("missed_count") or 0) > 0:
            downstream_execution_fields.append("missed_present")
        if downstream_execution_fields:
            return (
                "selector_reject_downstream_execution_materialized:"
                f"{downstream_execution_fields[0]}:"
                f"{text(candidate.get('selector_reason'), 'unknown')}"
            )
        if text(candidate.get("pretrade_cost_packet_status")) == "REFUSED":
            reasons = string_list(candidate.get("pretrade_cost_refusal_reasons"))
            reason = reasons[0] if reasons else text(candidate.get("selector_reason"), "unknown")
            return f"broker_cost_refused:{reason}"
        return f"selector_reject:{text(candidate.get('selector_reason'), 'unknown')}"
    if not enrich.get("scheduler_option_present"):
        return "candidate_generated_not_present_in_scheduler_scorecard"
    if not enrich.get("scheduler_selected"):
        return "candidate_generated_scheduler_not_selected"
    if not enrich.get("order_present"):
        return "scheduler_selected_no_order_row"
    risk_counts = enrich.get("risk_decision_counts") or {}
    if isinstance(risk_counts, Counter) and risk_counts.get("reject", 0) > 0:
        return "scheduler_selected_risk_rejected"
    if not enrich.get("trade_present"):
        order_counts = enrich.get("order_status_counts") or {}
        if isinstance(order_counts, Counter) and any(
            int(count or 0) > 0 and order_status_indicates_unfilled(status)
            for status, count in order_counts.items()
        ):
            return "order_accepted_not_filled"
        return "scheduler_selected_no_trade"
    net_r = safe_float(enrich.get("net_r"))
    if net_r > 0:
        return "executed_positive_r"
    if net_r < 0:
        return "executed_negative_r"
    return "executed_flat_r"


def reduced_package_candidate(row: Mapping[str, Any]) -> dict[str, Any]:
    entry_price = safe_float(row.get("entry_price"))
    stop_loss = safe_float(row.get("stop_loss"))
    target_price = safe_float(
        row.get("take_profit_1")
        or row.get("take_profit")
        or row.get("target_price")
    )
    has_order_geometry = bool(entry_price and stop_loss and target_price)
    source_bound_allowed = row.get(
        "source_bound_package_candidate_use_allowed",
        row.get(
            "ultimate_package_source_bound_candidate_use_allowed",
            row.get("package_replay_source_bound_candidate_use_allowed"),
        ),
    )
    package_replay_source_bound_allowed = row.get(
        "package_replay_source_bound_candidate_use_allowed",
        source_bound_allowed,
    )
    authority_row = {
        **dict(row),
        "package_authority_has_order_geometry": has_order_geometry,
        "package_authority_order_geometry_status": (
            "order_geometry_present"
            if has_order_geometry
            else "package_authority_candidate_missing_entry_stop_target_geometry"
        ),
    }
    if not has_order_geometry:
        executable_allowed = False
        executable_reason = "package_authority_candidate_missing_entry_stop_target_geometry"
    else:
        executable_allowed, executable_reason = replay_executable_package_use_detail(
            authority_row,
            source_bound_allowed=source_bound_allowed,
                package_replay_allowed=package_replay_source_bound_allowed,
            )
    source_bound_diagnostic_present = bool(
        source_bound_allowed
        or package_replay_source_bound_allowed
        or row.get("ultimate_package_effective_source_bound_candidate_use_allowed")
    )
    source_bound_non_executable = (
        source_bound_diagnostic_present and not executable_allowed
    )
    return {
        "candidate_id": text(row.get("candidate_id")),
        "decision_time_utc": text(row.get("decision_time_utc")),
        "canonical_replay_candidate_instance_key": text(
            row.get("canonical_replay_candidate_instance_key")
        ),
        "source_bound_replay_candidate_instance_key": text(
            row.get("source_bound_replay_candidate_instance_key")
        ),
        "risk_finalizer_probe_instance_key": text(
            row.get("risk_finalizer_probe_instance_key")
        ),
        "candidate_instance_identity_status": text(
            row.get("candidate_instance_identity_status")
        ),
        "symbol": upper(row.get("symbol")),
        "side": side(row.get("side") or row.get("direction")),
        "framework": text(row.get("framework")),
        "origin_family": text(row.get("origin_family")),
        "session_bucket": text(row.get("session_bucket")),
        "source_bound_package_candidate_use_allowed": source_bound_allowed,
        "ultimate_package_source_bound_candidate_use_allowed": source_bound_allowed,
        "package_replay_source_bound_candidate_use_allowed": (
            package_replay_source_bound_allowed
        ),
        "package_replay_candidate_use_allowed": executable_allowed,
        "package_replay_executable_candidate_use_allowed": executable_allowed,
        "package_replay_executable_candidate_use_allowed_reason": executable_reason,
        "replay_candidate_use_allowed_now": executable_allowed,
        "replay_candidate_use_allowed_now_reason": executable_reason,
        "ultimate_package_effective_executable_authority_allowed": executable_allowed,
        "ultimate_package_effective_executable_authority_reason": executable_reason,
        "ultimate_package_effective_source_bound_non_executable": (
            source_bound_non_executable
        ),
        "ultimate_package_effective_source_bound_non_executable_reason": (
            executable_reason if source_bound_non_executable else ""
        ),
        "package_authority_has_order_geometry": has_order_geometry,
        "package_authority_order_geometry_status": (
            "order_geometry_present"
            if has_order_geometry
            else "package_authority_candidate_missing_entry_stop_target_geometry"
        ),
        "package_authority_executable_candidate_status": (
            "package_authority_candidate_executable"
            if executable_allowed
            else executable_reason
        ),
        "selected_by_package_replay": row.get("selected_by_package_replay"),
        "role_disposition": text(row.get("role_disposition")),
        "replay_action": text(row.get("replay_action")),
        "replay_order_policy": text(row.get("replay_order_policy")),
        "replay_fill_status": text(row.get("replay_fill_status")),
        "replay_order_result_r": safe_float(row.get("replay_order_result_r")),
        "package_replay_score": safe_float(row.get("package_replay_score")),
        "candidate_expected_net_r": safe_float(
            row.get("candidate_expected_net_r") or row.get("expected_net_r")
        ),
        "probability": safe_float(row.get("probability") or row.get("candidate_probability")),
        "fill_probability": safe_float(row.get("fill_probability")),
        "source_completeness": safe_float(row.get("source_completeness")),
        "matched_sleeve_count": int(safe_float(row.get("matched_sleeve_count"))),
        "admission_sleeve_match_count": int(safe_float(row.get("admission_sleeve_match_count"))),
        "source_required_hold_match_count": int(
            safe_float(row.get("source_required_hold_match_count"))
        ),
        "avoid_failure_feature_match_count": int(
            safe_float(row.get("avoid_failure_feature_match_count"))
        ),
        "redesign_repair_match_count": int(safe_float(row.get("redesign_repair_match_count"))),
        "matched_package_role_counts": row.get("matched_package_role_counts")
        if isinstance(row.get("matched_package_role_counts"), dict)
        else {},
    }


def counter_snapshot(value: Any, *, limit: int = 8) -> dict[str, int]:
    if isinstance(value, Counter):
        return top_counter(value, limit=limit)
    if isinstance(value, dict):
        counter = Counter({text(key): int(safe_float(val)) for key, val in value.items()})
        return top_counter(counter, limit=limit)
    return {}


def representative_candidate_quality_fields(
    trace_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Promote the best available generated-candidate quality fields to axis rows."""

    generated_rows = [row for row in trace_rows if row.get("candidate_generated")]
    source = next(
        (
            row
            for row in generated_rows
            if row.get("package_replay_executable_candidate_use_allowed") is True
            and row.get("pretrade_cost_packet_status") == "PASSED"
            and row.get("cost_source_gap_status")
            == "source_bound_cost_authority_present"
            and (
                row.get("scheduler_materialization_action_intent")
                or row.get("action_intent")
                or row.get("lifecycle_action")
            )
        ),
        generated_rows[0] if generated_rows else {},
    )
    fields = {
        "candidate_id": source.get("candidate_id"),
        "decision_time_utc": source.get("decision_time_utc"),
        "stable_decision_window_id": source.get("stable_decision_window_id"),
        "expected_net_r": source.get("expected_net_r"),
        "candidate_expected_net_r": source.get("candidate_expected_net_r"),
        "probability": source.get("probability"),
        "candidate_probability": source.get("candidate_probability"),
        "fill_probability": source.get("fill_probability"),
        "candidate_fill_probability": source.get("candidate_fill_probability"),
        "source_completeness": source.get("source_completeness"),
        "source_completeness_status": source.get("source_completeness_status"),
        "candidate_decision_quality_field_sources": source.get(
            "candidate_decision_quality_field_sources"
        ),
        "candidate_decision_quality_alias_status": source.get(
            "candidate_decision_quality_alias_status"
        ),
        "candidate_decision_quality_source_boundary": source.get(
            "candidate_decision_quality_source_boundary"
        ),
        "candidate_decision_quality_alias_mismatches": source.get(
            "candidate_decision_quality_alias_mismatches"
        ),
        "candidate_decision_quality_provenance_failures": source.get(
            "candidate_decision_quality_provenance_failures"
        ),
        "candidate_decision_quality": source.get("candidate_decision_quality")
        or candidate_decision_quality_envelope(source),
        "source_bound_package_candidate_use_allowed": source.get(
            "source_bound_package_candidate_use_allowed"
        ),
        "ultimate_package_source_bound_candidate_use_allowed": source.get(
            "ultimate_package_source_bound_candidate_use_allowed"
        ),
        "package_replay_source_bound_candidate_use_allowed": source.get(
            "package_replay_source_bound_candidate_use_allowed"
        ),
        "package_replay_candidate_use_allowed": source.get(
            "package_replay_candidate_use_allowed"
        ),
        "package_replay_executable_candidate_use_allowed": source.get(
            "package_replay_executable_candidate_use_allowed"
        ),
        "package_replay_executable_candidate_use_allowed_reason": source.get(
            "package_replay_executable_candidate_use_allowed_reason"
        ),
        "replay_candidate_use_allowed_now": source.get(
            "replay_candidate_use_allowed_now"
        ),
        "replay_candidate_use_allowed_now_reason": source.get(
            "replay_candidate_use_allowed_now_reason"
        ),
        "pretrade_cost_packet_status": source.get("pretrade_cost_packet_status"),
        "cost_authority": source.get("cost_authority"),
        "pretrade_cost_packet_authority": source.get(
            "pretrade_cost_packet_authority"
        ),
        "cost_source_gap_status": source.get("cost_source_gap_status"),
        "source_gap_cost_fallback_blocked": source.get(
            "source_gap_cost_fallback_blocked"
        ),
        "candidate_cost_r_fallback_is_authority": source.get(
            "candidate_cost_r_fallback_is_authority"
        ),
        "scheduler_materialization_action_intent": source.get(
            "scheduler_materialization_action_intent"
        )
        or source.get("action_intent")
        or source.get("lifecycle_action"),
        "scheduler_materialization_skip_reason": source.get(
            "scheduler_materialization_skip_reason"
        ),
        "selector_action": source.get("selector_action"),
        "selector_reason": source.get("selector_reason"),
        "representative_candidate_quality_status": (
            "materialized" if source else "no_generated_candidate_trace"
        ),
    }
    for field in PACKAGE_NEW_ENTRY_AUTHORITY_FIELDS:
        if field in source:
            fields[field] = source.get(field)
    return fields


def candidate_trace(
    *,
    candidate: Mapping[str, Any],
    enrich: Mapping[str, Any],
    package_candidate: Mapping[str, Any] | None,
    exact_package_candidate_ids: set[str],
    source_bound_r: float,
) -> dict[str, Any]:
    scheduler_rank = enrich.get("scheduler_rank_min")
    scheduler_rank_value = int(scheduler_rank) if scheduler_rank is not None else None
    package_candidate = package_candidate or {}
    package_replay_allowed = package_candidate.get(
        "package_replay_source_bound_candidate_use_allowed",
        package_candidate.get(
            "source_bound_package_candidate_use_allowed",
            candidate.get(
                "package_replay_source_bound_candidate_use_allowed",
                candidate.get("source_bound_package_candidate_use_allowed"),
            ),
        ),
    )
    source_bound_allowed = candidate.get(
        "source_bound_package_candidate_use_allowed",
        candidate.get("ultimate_package_source_bound_candidate_use_allowed"),
    )
    if source_bound_allowed in (None, ""):
        source_bound_allowed = package_candidate.get(
            "source_bound_package_candidate_use_allowed",
            package_candidate.get("ultimate_package_source_bound_candidate_use_allowed"),
        )
    executable_proof_row = enrich.get("executable_proof_row")
    if not isinstance(executable_proof_row, Mapping):
        executable_proof_row = {}
    scorecard_binding = enrich.get("scorecard_binding") or {}
    order_binding = enrich.get("order_binding") or {}
    trade_binding = enrich.get("trade_binding") or {}
    missed_binding = enrich.get("missed_binding") or {}
    authority_envelope = projection_authority_envelope_selection(
        candidate=candidate,
        package_candidate=package_candidate,
        scorecard=scorecard_binding,
        order=order_binding,
        trade=trade_binding,
        missed=missed_binding,
    )
    stage_binding_by_name = {
        "candidate": candidate,
        "package_candidate": package_candidate,
        "scorecard": scorecard_binding,
        "order": order_binding,
        "trade": trade_binding,
        "missed": missed_binding,
    }
    authority_stage_binding = stage_binding_by_name.get(
        text(authority_envelope.get("stage")),
        {},
    )
    authority_stage_binding = (
        authority_stage_binding
        if isinstance(authority_stage_binding, Mapping)
        else {}
    )
    authority_surface = authority_envelope.get("surface")
    authority_surface = (
        authority_surface if isinstance(authority_surface, Mapping) else {}
    )
    current_execution_contract_stage = "candidate"
    current_execution_contract_binding: Mapping[str, Any] = {}
    for stage, present, binding in (
        ("trade", enrich.get("trade_present"), trade_binding),
        ("order", enrich.get("order_present"), order_binding),
        ("missed", enrich.get("missed_present"), missed_binding),
        ("scorecard", enrich.get("scorecard_present"), scorecard_binding),
    ):
        if present and isinstance(binding, Mapping) and binding:
            current_execution_contract_stage = stage
            current_execution_contract_binding = binding
            break
    merged_candidate = {
        **dict(package_candidate),
        **dict(candidate),
        **dict(executable_proof_row),
        **dict(current_execution_contract_binding),
        **dict(authority_stage_binding),
        **dict(authority_surface),
    }
    candidate_entry_price = safe_float(merged_candidate.get("entry_price"))
    candidate_stop_loss = safe_float(merged_candidate.get("stop_loss"))
    candidate_target_price = safe_float(
        merged_candidate.get("take_profit_1")
        or merged_candidate.get("take_profit")
        or merged_candidate.get("target_price")
    )
    if candidate_entry_price and candidate_stop_loss and candidate_target_price:
        merged_candidate["package_authority_has_order_geometry"] = True
        merged_candidate["package_authority_order_geometry_status"] = (
            "order_geometry_present_from_generated_candidate"
        )
    executable_allowed, executable_reason = replay_executable_package_use_detail(
        merged_candidate,
        source_bound_allowed=source_bound_allowed,
        package_replay_allowed=package_replay_allowed,
    )
    diagnostic_source_bound_r = source_bound_r
    effective_source_bound_r = source_bound_r if executable_allowed else 0.0
    resolved_execution_fill_probability, resolved_execution_fill_source = (
        execution_fillability_authority(merged_candidate)
    )
    materialized_action_intent = text(
        merged_candidate.get("scheduler_materialization_action_intent")
        or merged_candidate.get("action_intent")
        or merged_candidate.get("lifecycle_action")
    )
    raw_selector_action = text(
        candidate.get("raw_selector_action")
        or candidate.get("selector_action_origin")
        or candidate.get("selector_action")
    )
    materialized_selector_action = effective_selector_action(
        merged_candidate,
        raw_selector_action,
    )
    materialized_selector_reason = effective_selector_reason(
        merged_candidate,
        text(
            candidate.get("selector_reason")
            or candidate.get("selector_action_origin_reason")
            or candidate.get("risk_decision_reason")
        ),
    )
    trace = {
        "candidate_generated": True,
        "candidate_id": candidate.get("candidate_id"),
        "candidate_instance_key": candidate.get("candidate_instance_key"),
        "candidate_decision_window_id": candidate.get("decision_window_id"),
        "candidate_set_id": candidate.get("candidate_set_id"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "stable_decision_window_id": candidate.get("stable_decision_window_id"),
        "candidate_selected_candidate_id": candidate.get("selected_candidate_id"),
        "candidate_selected_candidate_ids": candidate.get("selected_candidate_ids"),
        "candidate_packet_sidecar_id": candidate.get("packet_sidecar_id"),
        "candidate_packet_sidecar_hash_sha256": candidate.get(
            "packet_sidecar_hash_sha256"
        ),
        "candidate_scheduler_packet_sidecar_id": candidate.get(
            "scheduler_packet_sidecar_id"
        ),
        "candidate_scheduler_packet_sidecar_hash_sha256": candidate.get(
            "scheduler_packet_sidecar_hash_sha256"
        ),
        "candidate_replay_identity_tuple_status": candidate.get(
            "replay_identity_tuple_status"
        ),
        "split": candidate.get("split"),
        "chunk_id": candidate.get("chunk_id"),
        "symbol": candidate.get("symbol"),
        "side": candidate.get("side"),
        "direction": candidate.get("direction") or candidate.get("side"),
        "timeframe": candidate.get("timeframe"),
        "market_timeframe": candidate.get("market_timeframe") or candidate.get("timeframe"),
        "decision_timeframe": candidate.get("decision_timeframe") or candidate.get("timeframe"),
        **route_provenance_fields(candidate, merged_candidate),
        "route_session_raw": candidate.get("route_session_raw"),
        "route_session_applied": candidate.get("route_session_applied"),
        "kill_zone": candidate.get("kill_zone"),
        "selector_action": materialized_selector_action,
        "selector_reason": materialized_selector_reason,
        "raw_selector_action": raw_selector_action,
        "candidate_probability": candidate.get("candidate_probability"),
        "probability": candidate.get("probability") or candidate.get("candidate_probability"),
        "candidate_fill_probability": candidate.get("candidate_fill_probability"),
        "fill_probability": candidate.get("fill_probability"),
        "source_completeness": merged_candidate.get("source_completeness"),
        "source_completeness_status": merged_candidate.get(
            "source_completeness_status"
        ),
        "execution_fill_probability": resolved_execution_fill_probability,
        "execution_fill_probability_source": resolved_execution_fill_source,
        "execution_fill_probability_source_time_utc": merged_candidate.get(
            "execution_fill_probability_source_time_utc"
        ),
        "execution_fill_probability_source_boundary": merged_candidate.get(
            "execution_fill_probability_source_boundary"
        ),
        "execution_fill_probability_authority_class": merged_candidate.get(
            "execution_fill_probability_authority_class"
        ),
        "projection_execution_contract_stage": current_execution_contract_stage,
        "projection_authority_envelope_stage": authority_envelope.get("stage"),
        "projection_authority_envelope_status": authority_envelope.get("status"),
        "candidate_decision_quality_field_sources": merged_candidate.get(
            "candidate_decision_quality_field_sources"
        ),
        "candidate_decision_quality_alias_status": merged_candidate.get(
            "candidate_decision_quality_alias_status"
        ),
        "candidate_decision_quality_source_boundary": merged_candidate.get(
            "candidate_decision_quality_source_boundary"
        ),
        "candidate_decision_quality_alias_mismatches": merged_candidate.get(
            "candidate_decision_quality_alias_mismatches"
        ),
        "candidate_decision_quality_provenance_failures": merged_candidate.get(
            "candidate_decision_quality_provenance_failures"
        ),
        "candidate_decision_quality": candidate_decision_quality_envelope(
            {
                **dict(merged_candidate),
                "candidate_probability": candidate.get("candidate_probability"),
                "probability": candidate.get("probability")
                or candidate.get("candidate_probability"),
                "candidate_fill_probability": candidate.get("candidate_fill_probability"),
                "fill_probability": candidate.get("fill_probability"),
                "source_completeness": merged_candidate.get("source_completeness"),
                "source_completeness_status": merged_candidate.get(
                    "source_completeness_status"
                ),
                "candidate_expected_net_r": candidate.get("candidate_expected_net_r"),
                "expected_net_r": candidate.get("expected_net_r")
                or candidate.get("candidate_expected_net_r"),
            }
        ),
        "lifecycle_label_context_present": candidate.get(
            "lifecycle_label_context_present"
        ),
        "lifecycle_label_context_row_count": candidate.get(
            "lifecycle_label_context_row_count"
        ),
        "pending_lifecycle_v4_state_group": candidate.get(
            "pending_lifecycle_v4_state_group"
        ),
        "pending_lifecycle_v4_state_groups": candidate.get(
            "pending_lifecycle_v4_state_groups"
        ),
        "fillability_label_family": candidate.get("fillability_label_family"),
        "fillability_label_families": candidate.get("fillability_label_families"),
        "fill_no_fill_label": candidate.get("fill_no_fill_label"),
        "fill_no_fill_labels": candidate.get("fill_no_fill_labels"),
        "candidate_ev_r": candidate.get("candidate_ev_r"),
        "candidate_expected_net_r": candidate.get("candidate_expected_net_r"),
        "expected_net_r": candidate.get("expected_net_r")
        or candidate.get("candidate_expected_net_r"),
        "expected_cost_r": candidate.get("expected_cost_r"),
        "pretrade_cost_packet_status": merged_candidate.get(
            "pretrade_cost_packet_status"
        ),
        "cost_authority": merged_candidate.get("cost_authority")
        or merged_candidate.get("pretrade_cost_packet_authority"),
        "pretrade_cost_packet_authority": merged_candidate.get(
            "pretrade_cost_packet_authority"
        )
        or merged_candidate.get("cost_authority"),
        "pretrade_cost_refusal_reasons": merged_candidate.get(
            "pretrade_cost_refusal_reasons"
        ),
        "cost_source_gap_status": merged_candidate.get("cost_source_gap_status"),
        "source_gap_cost_fallback_blocked": merged_candidate.get(
            "source_gap_cost_fallback_blocked"
        ),
        "candidate_cost_r_fallback_is_authority": merged_candidate.get(
            "candidate_cost_r_fallback_is_authority"
        ),
        "scheduler_materialization_action_intent": materialized_action_intent,
        "scheduler_materialization_skip_reason": merged_candidate.get(
            "scheduler_materialization_skip_reason"
        ),
        "action_intent": (
            merged_candidate.get("action_intent") or materialized_action_intent
        ),
        "candidate_dynamic_geometry_policy": first_present(
            candidate.get("dynamic_geometry_policy"),
            merged_candidate.get("dynamic_geometry_policy"),
        ),
        "dynamic_geometry_policy": first_present(
            candidate.get("dynamic_geometry_policy"),
            merged_candidate.get("dynamic_geometry_policy"),
        ),
        "candidate_lifecycle_action": candidate.get("lifecycle_action"),
        "lifecycle_action": (
            candidate.get("lifecycle_action") or materialized_action_intent
        ),
        "candidate_lifecycle_reason": candidate.get("lifecycle_reason"),
        "candidate_lifecycle_permitted": candidate.get("lifecycle_permitted"),
        "scheduler_scorecard_present": bool(enrich.get("scorecard_present")),
        "scheduler_option_present": bool(enrich.get("scheduler_option_present")),
        "scheduler_rank": scheduler_rank_value,
        "scheduler_score": enrich.get("scheduler_score_max"),
        "scheduler_selected": bool(enrich.get("scheduler_selected")),
        "scheduler_option_count": int(enrich.get("scheduler_option_count") or 0),
        "scheduler_action_class_counts": counter_snapshot(
            enrich.get("scheduler_action_class_counts")
        ),
        "scheduler_decision_status_counts": counter_snapshot(
            enrich.get("scheduler_decision_status_counts")
        ),
        "scheduler_option_reason_counts": counter_snapshot(
            enrich.get("scheduler_option_reason_counts")
        ),
        "scheduler_option_samples": enrich.get("scheduler_option_samples") or [],
        "source_join_class_counts": counter_snapshot(
            enrich.get("source_join_class_counts")
        ),
        "packet_sidecar_present": bool(enrich.get("packet_sidecar_present")),
        "packet_sidecar_ids": sorted(enrich.get("packet_sidecar_ids") or []),
        "packet_sidecar_hashes": sorted(enrich.get("packet_sidecar_hashes") or []),
        "risk_decision_counts": counter_snapshot(enrich.get("risk_decision_counts")),
        "risk_decision_reason_counts": counter_snapshot(
            enrich.get("risk_decision_reason_counts")
        ),
        "risk_lifecycle_action_counts": counter_snapshot(
            enrich.get("risk_lifecycle_action_counts")
        ),
        "risk_lifecycle_permitted_counts": counter_snapshot(
            enrich.get("risk_lifecycle_permitted_counts")
        ),
        "order_present": bool(enrich.get("order_present")),
        "order_status_counts": counter_snapshot(enrich.get("order_status_counts")),
        "order_policy_counts": counter_snapshot(enrich.get("order_policy_counts")),
        "order_architecture_counts": counter_snapshot(
            enrich.get("order_architecture_counts")
        ),
        "order_type_counts": counter_snapshot(enrich.get("order_type_counts")),
        "oracle_present": bool(enrich.get("oracle_present")),
        "fill_status_counts": counter_snapshot(enrich.get("fill_status_counts")),
        "counterfactual_fill_status_counts": counter_snapshot(
            enrich.get("counterfactual_fill_status_counts")
        ),
        "fillability_status_counts": counter_snapshot(
            enrich.get("fillability_status_counts")
        ),
        "trade_present": bool(enrich.get("trade_present")),
        "trade_count": int(enrich.get("trade_count") or 0),
        "terminal_outcome_counts": counter_snapshot(enrich.get("terminal_outcome_counts")),
        "exit_result_counts": counter_snapshot(enrich.get("exit_result_counts")),
        "close_reason_counts": counter_snapshot(enrich.get("close_reason_counts")),
        "actual_r": safe_float(enrich.get("net_r")),
        "gross_r": safe_float(enrich.get("gross_r")),
        "final_r": safe_float(enrich.get("final_r")),
        "cash_pnl": safe_float(enrich.get("cash_pnl")),
        "risk_cash": safe_float(enrich.get("risk_cash")),
        "risk_pct": safe_float(enrich.get("risk_pct")),
        "deviation_reason": candidate_deviation_reason(candidate, enrich),
        "package_candidate_identity_match_status": package_candidate.get(
            "package_candidate_identity_match_status",
            "package_candidate_instance_missing",
        ),
        "package_candidate_identity_match_count": int(
            package_candidate.get("package_candidate_identity_match_count") or 0
        ),
        "exact_package_candidate_match": text(
            package_candidate.get("package_candidate_identity_match_status")
        ).startswith("exact_"),
        "diagnostic_package_source_bound_r": diagnostic_source_bound_r,
        "diagnostic_source_bound_r": diagnostic_source_bound_r,
        "effective_package_source_bound_r": effective_source_bound_r,
        "effective_source_bound_r": effective_source_bound_r,
        "package_source_bound_r": effective_source_bound_r,
        "source_bound_r": effective_source_bound_r,
        "source_bound_r_additive_unit": "source_member_axis_not_candidate_trace",
        "source_bound_r_diagnostic_additive_unit": "source_member_axis_not_candidate_trace",
        "source_bound_package_candidate_use_allowed": source_bound_allowed,
        "ultimate_package_source_bound_candidate_use_allowed": source_bound_allowed,
        "package_replay_source_bound_candidate_use_allowed": package_replay_allowed,
        "package_replay_candidate_use_allowed": executable_allowed,
        "package_replay_executable_candidate_use_allowed": executable_allowed,
        "package_replay_executable_candidate_use_allowed_reason": executable_reason,
        "replay_candidate_use_allowed_now": executable_allowed,
        "replay_candidate_use_allowed_now_reason": executable_reason,
        "package_selected_by_replay": package_candidate.get("selected_by_package_replay"),
        "package_role_disposition": package_candidate.get("role_disposition"),
        "package_replay_action": package_candidate.get("replay_action"),
        "package_replay_order_policy": package_candidate.get("replay_order_policy"),
        "package_replay_fill_status": package_candidate.get("replay_fill_status"),
        "package_replay_order_result_r": package_candidate.get("replay_order_result_r"),
        "package_replay_score": package_candidate.get("package_replay_score"),
        "package_authority_has_order_geometry": package_candidate.get(
            "package_authority_has_order_geometry"
        ),
        "package_authority_order_geometry_status": package_candidate.get(
            "package_authority_order_geometry_status"
        ),
        "package_authority_executable_candidate_status": package_candidate.get(
            "package_authority_executable_candidate_status"
        ),
        "package_matched_sleeve_count": package_candidate.get("matched_sleeve_count"),
        "package_admission_sleeve_match_count": package_candidate.get(
            "admission_sleeve_match_count"
        ),
        "package_source_required_hold_match_count": package_candidate.get(
            "source_required_hold_match_count"
        ),
    }
    for field in PACKAGE_NEW_ENTRY_AUTHORITY_FIELDS:
        if field in merged_candidate:
            trace[field] = merged_candidate.get(field)
    return trace


def canonical_quality_projection(candidate: Mapping[str, Any]) -> dict[str, Any]:
    quality = candidate_decision_quality_envelope(candidate)
    field_sources = first_present(
        quality.get("field_sources"),
        quality.get("candidate_decision_quality_field_sources"),
        candidate.get("candidate_decision_quality_field_sources"),
    )
    field_sources = dict(field_sources) if isinstance(field_sources, Mapping) else {}
    source = text(
        first_present(
            quality.get("source_boundary"),
            quality.get("candidate_decision_quality_source_boundary"),
            candidate.get("candidate_decision_quality_source_boundary"),
        )
    )
    values = {
        "expected_net_r": optional_float(
            first_present(
                quality.get("expected_net_r"),
                candidate.get("expected_net_r"),
                candidate.get("candidate_expected_net_r"),
            )
        ),
        "probability": optional_float(
            first_present(
                quality.get("probability"),
                candidate.get("probability"),
                candidate.get("candidate_probability"),
            )
        ),
        "source_completeness": optional_float(
            first_present(
                quality.get("source_completeness"),
                candidate.get("source_completeness"),
            )
        ),
    }
    violations: list[str] = []
    if not source:
        violations.append("canonical_quality_source_missing")
    for field, value in values.items():
        if value is None:
            violations.append(f"canonical_quality_{field}_missing")
        if not text(field_sources.get(field)):
            violations.append(f"canonical_quality_{field}_source_missing")
    completeness = values["source_completeness"]
    if completeness is not None and not 0.0 <= completeness <= 1.0:
        violations.append("canonical_quality_source_completeness_out_of_range")
    for prefix, raw_failures in (
        (
            "alias_mismatch",
            first_present(
                quality.get("alias_mismatches"),
                candidate.get("candidate_decision_quality_alias_mismatches"),
            ),
        ),
        (
            "provenance_failure",
            first_present(
                quality.get("provenance_failures"),
                candidate.get("candidate_decision_quality_provenance_failures"),
            ),
        ),
        (
            "scheduler_parity_mismatch",
            candidate.get("candidate_scheduler_quality_parity_mismatches"),
        ),
    ):
        for failure in string_list(raw_failures):
            violations.append(f"canonical_quality_{prefix}:{failure}")
    return {
        "canonical_quality_source": source,
        "canonical_quality_field_sources": {
            field: text(field_sources.get(field))
            for field in ("expected_net_r", "probability", "source_completeness")
        },
        "canonical_expected_net_r": values["expected_net_r"],
        "canonical_probability": values["probability"],
        "canonical_source_completeness": values["source_completeness"],
        "canonical_quality_contract_status": (
            "pass" if not violations else "violation"
        ),
        "canonical_quality_contract_violations": violations,
    }


def first_binding_value(
    bindings: Sequence[Mapping[str, Any]],
    *fields: str,
) -> Any:
    for binding in bindings:
        if not isinstance(binding, Mapping):
            continue
        value = first_present(*(binding.get(field) for field in fields))
        if not missing_value(value):
            return value
    return None


def binding_poi_state(row: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        return {}
    candidates: list[Mapping[str, Any]] = []
    if isinstance(row.get("poi_state"), Mapping):
        candidates.append(row["poi_state"])
    for fields_key in ("source_fields", "candidate_source_fields"):
        fields = row.get(fields_key)
        if isinstance(fields, Mapping) and isinstance(fields.get("poi_state"), Mapping):
            candidates.append(fields["poi_state"])
    for inputs_key in (
        "candidate_decision_inputs",
        "scheduler_candidate_decision_inputs",
    ):
        inputs = row.get(inputs_key)
        if not isinstance(inputs, Mapping):
            continue
        if isinstance(inputs.get("poi_state"), Mapping):
            candidates.append(inputs["poi_state"])
        for fields_key in ("source_fields", "candidate_source_fields"):
            fields = inputs.get(fields_key)
            if isinstance(fields, Mapping) and isinstance(fields.get("poi_state"), Mapping):
                candidates.append(fields["poi_state"])
    for payload_key in (
        "package_new_entry_authority_payload",
        "selected_package_new_entry_authority_payload",
    ):
        payload = row.get(payload_key)
        if isinstance(payload, Mapping) and isinstance(payload.get("poi_state"), Mapping):
            candidates.append(payload["poi_state"])
    flat = {
        field: row.get(field)
        for field in (*POI_STATE_ATOMIC_FIELDS, "poi_state_hash_sha256")
        if field in row
    }
    if flat.get("poi_id"):
        candidates.append(flat)
    return dict(candidates[0]) if candidates else {}


def poi_lineage_projection_fields(
    *,
    candidate: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    order: Mapping[str, Any],
    trade: Mapping[str, Any],
    missed: Mapping[str, Any],
) -> dict[str, Any]:
    bindings = {
        "candidate": candidate,
        "scorecard": scorecard,
        "order": order,
        "trade": trade,
        "missed": missed,
    }
    required = poi_state_required(candidate)
    stage_states = {
        stage: binding_poi_state(binding)
        for stage, binding in bindings.items()
        if binding
    }
    stage_presence = {
        stage: bool(state)
        for stage, state in stage_states.items()
    }
    stage_ids = {
        stage: text(state.get("poi_id"))
        for stage, state in stage_states.items()
        if state
    }
    stage_hashes = {
        stage: text(state.get("poi_state_hash_sha256"))
        for stage, state in stage_states.items()
        if state
    }
    candidate_state = stage_states.get("candidate", {})
    contract_failures = list(
        poi_state_contract_failures(
            candidate_state,
            decision_time_utc=candidate.get("decision_time_utc"),
        )
    ) if candidate_state else (["poi_state_missing"] if required else [])
    present_binding_stages = [stage for stage, binding in bindings.items() if binding]
    missing_stages = [
        stage
        for stage in present_binding_stages
        if not stage_presence.get(stage, False)
    ]
    exact = bool(
        (not required)
        or (
            candidate_state
            and not contract_failures
            and not missing_stages
            and len(set(stage_ids.values())) == 1
            and len(set(stage_hashes.values())) == 1
        )
    )
    return {
        "poi_state_required": required,
        "poi_id": text(candidate_state.get("poi_id")),
        "poi_state_hash_sha256": text(
            candidate_state.get("poi_state_hash_sha256")
        ),
        "poi_state_contract_failures": contract_failures,
        "poi_stage_presence": stage_presence,
        "poi_stage_ids": stage_ids,
        "poi_stage_hashes": stage_hashes,
        "poi_missing_bound_stages": missing_stages,
        "poi_cross_stage_lineage_exact": exact,
        "poi_lineage_status": (
            "exact_cross_stage_poi_lineage"
            if exact and required
            else "not_applicable_non_poi_candidate"
            if exact
            else "poi_lineage_mismatch"
        ),
    }


def projection_authority_envelope_selection(
    *,
    candidate: Mapping[str, Any],
    package_candidate: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    order: Mapping[str, Any],
    trade: Mapping[str, Any],
    missed: Mapping[str, Any],
) -> dict[str, Any]:
    stage_bindings = (
        ("order", order),
        ("trade", trade),
        ("missed", missed),
        ("scorecard", scorecard),
        ("candidate", candidate),
        ("package_candidate", package_candidate),
    )
    stage_records: list[dict[str, Any]] = []
    observed_payload_digests: set[str] = set()
    for stage, binding in stage_bindings:
        if not isinstance(binding, Mapping) or not binding:
            continue
        selection = binding.get("package_new_entry_authority_envelope_record")
        if not isinstance(selection, Mapping):
            selection = package_new_entry_authority_envelope_selection(
                binding,
                action_intent=text(
                    binding.get("scheduler_materialization_action_intent")
                    or candidate.get("scheduler_materialization_action_intent")
                    or candidate.get("action_intent")
                    or candidate.get("lifecycle_action")
                )
                or None,
            )
        for record in selection.get("records") or []:
            if isinstance(record, Mapping) and text(record.get("digest")):
                observed_payload_digests.add(text(record.get("digest")))
        if selection.get("valid") is True:
            stage_records.append({**dict(selection), "stage": stage})

    valid_digests = {text(record.get("digest")) for record in stage_records}
    if len(valid_digests) > 1 or (
        valid_digests and observed_payload_digests - valid_digests
    ):
        return {
            "valid": False,
            "status": "cross_stage_authority_envelope_mismatch",
            "reasons": ["multiple_distinct_stage_authority_envelopes"],
            "stage_records": stage_records,
            "observed_payload_digests": sorted(observed_payload_digests),
        }
    if stage_records:
        selected = stage_records[0]
        return {
            **selected,
            "status": "single_recorded_stage_authority_envelope",
            "stage_records": stage_records,
            "observed_payload_digests": sorted(observed_payload_digests),
        }
    return {
        "valid": False,
        "status": "no_current_stage_authority_envelope",
        "reasons": ["current_stage_authority_envelope_missing_or_invalid"],
        "stage_records": [],
        "observed_payload_digests": sorted(observed_payload_digests),
    }


def risk_behavior_from_projection(
    *,
    tier: Any,
    decision: Any,
) -> str:
    tier_text = text(tier).lower().replace("_", "-")
    decision_text = text(decision).lower().replace("_", "-")
    if tier_text in {"full", "full-risk"} or decision_text == "trade":
        return "full-risk"
    if tier_text in {"reduced", "reduced-risk"} or decision_text in {
        "open-reduced-risk",
        "reduce-risk",
    }:
        return "reduced-risk"
    return "diagnostic-or-non-entry"


def fallback_eligibility(
    bindings: Sequence[Mapping[str, Any]],
) -> tuple[bool | None, str, str]:
    status = text(
        first_binding_value(
            bindings,
            "guarded_market_fallback_status",
            "planned_guarded_market_fallback_status",
            "passive_limit_fallback_envelope_status",
        )
    )
    applied = first_binding_value(bindings, "guarded_market_fallback_applied")
    attempted = first_binding_value(bindings, "guarded_market_fallback_attempted")
    route_available = first_binding_value(
        bindings,
        "passive_limit_fallback_envelope_guarded_market_route_available",
    )
    status_lower = status.lower()
    eligibility: bool | None = None
    if applied is True:
        eligibility = True
    elif status_lower:
        if "not_eligible" in status_lower or "not-eligible" in status_lower:
            eligibility = False
        elif "eligible" in status_lower:
            eligibility = True
        elif status_lower.startswith("not_attempted") or status_lower in {
            "not_applicable",
            "not_configured",
        }:
            eligibility = False
    if eligibility is None and isinstance(route_available, bool):
        eligibility = route_available
    blocker = text(
        first_binding_value(
            bindings,
            "guarded_market_fallback_reason",
            "planned_guarded_market_fallback_reason",
        )
    )
    if not blocker:
        reasons = first_binding_value(
            bindings,
            "guarded_market_fallback_reasons",
            "passive_limit_fallback_envelope_unusable_guarded_fallback_reasons",
        )
        reason_rows = string_list(reasons)
        blocker = reason_rows[0] if reason_rows else ""
    if not status and attempted is True:
        status = "attempted_status_missing"
    return eligibility, status, blocker


def counterfactual_presence(
    bindings: Sequence[Mapping[str, Any]],
) -> tuple[bool, str]:
    fields = (
        "counterfactual_fill_status",
        "counterfactual_order_fill_status",
        "counterfactual_order_terminal_outcome",
        "counterfactual_order_close_mark_r",
        "missed_opportunity_counterfactual_scoreable",
        "opportunity_net_proxy_r",
    )
    present_fields = [
        field
        for field in fields
        if not missing_value(first_binding_value(bindings, field))
    ]
    return bool(present_fields), present_fields[0] if present_fields else ""


def selected_expiry_projection(row: Mapping[str, Any]) -> bool:
    if not row.get("scheduler_selected") or not row.get("order_present"):
        return False
    if row.get("trade_present"):
        return False
    terminal_text = " ".join(
        text(row.get(field)).lower()
        for field in (
            "order_status",
            "terminal_fill_status",
            "terminal_outcome",
        )
    )
    return "expir" in terminal_text or "not_filled" in terminal_text


def exact_projection_deviation(row: Mapping[str, Any]) -> tuple[str, str]:
    source_completeness = optional_float(row.get("canonical_source_completeness"))
    source_required_text = " ".join(
        text(row.get(field)).lower()
        for field in (
            "raw_selector_action",
            "effective_selector_action",
            "effective_selector_reason",
            "package_order_executable_reason",
            "package_order_executable_blocker_class",
            "package_order_executable_blocker_reason",
            "risk_finalizer_action",
            "risk_finalizer_reason",
            "lifecycle_action",
            "lifecycle_reason",
            "miss_reason",
        )
    )
    source_required = "source_required" in source_required_text or "source-required" in source_required_text
    if source_required and source_completeness is not None and source_completeness >= 1.0:
        blocker_class = text(row.get("package_order_executable_blocker_class"))
        blocker_reason = text(
            row.get("package_order_executable_blocker_reason")
            or row.get("miss_reason")
            or row.get("risk_finalizer_reason")
        )
        cost_text = " ".join(
            (
                blocker_class.lower(),
                blocker_reason.lower(),
                text(row.get("pretrade_cost_packet_status")).lower(),
            )
        )
        if "cost" in cost_text or "refused" in cost_text:
            return (
                "cost_authority",
                f"source_required_cost_authority_blocked:{blocker_reason or blocker_class or 'cost_refused'}",
            )
        authority_text = " ".join(
            (
                blocker_reason.lower(),
                text(row.get("package_authority_status")).lower(),
                text(row.get("risk_finalizer_reason")).lower(),
            )
        )
        if row.get("package_authority_valid") is False or any(
            token in authority_text
            for token in ("signed", "authority", "hash_missing", "hash_mismatch")
        ):
            return (
                "signed_authority",
                "source_required_signed_authority_blocked:"
                f"{blocker_reason or text(row.get('package_authority_status')) or 'invalid_signed_authority'}",
            )
        lifecycle_reason = text(
            row.get("lifecycle_reason")
            or row.get("lifecycle_action")
            or blocker_reason
        )
        return (
            "lifecycle",
            f"source_required_lifecycle_blocked:{lifecycle_reason or 'source_required_lifecycle_hold'}",
        )

    blocker_reason = text(row.get("package_order_executable_blocker_reason"))
    blocker_class = text(row.get("package_order_executable_blocker_class"))
    if row.get("package_order_executable_allowed") is False and blocker_reason:
        return (
            blocker_class or "package_order_executable",
            f"package_order_not_executable:{blocker_class or 'unknown'}:{blocker_reason}",
        )
    effective_action = text(row.get("effective_selector_action"), "unknown")
    if effective_action in {"reject", "source-required", "source_required"}:
        if text(row.get("pretrade_cost_packet_status")) == "REFUSED":
            return (
                "cost_authority",
                f"broker_cost_refused:{text(row.get('effective_selector_reason'), 'unknown')}",
            )
        return (
            "selector",
            f"selector_{effective_action}:{text(row.get('effective_selector_reason'), 'unknown')}",
        )
    violations = string_list(row.get("canonical_quality_contract_violations"))
    if violations and not row.get("scorecard_present"):
        return "canonical_quality", violations[0]
    if not row.get("scorecard_present"):
        return "scorecard", "candidate_not_present_in_scheduler_scorecard"
    if not row.get("scheduler_selected"):
        reason = text(
            row.get("risk_finalizer_reason")
            or row.get("miss_reason")
            or "scheduler_not_selected"
        )
        return "scheduler", f"scheduler_not_selected:{reason}"
    if not row.get("order_present"):
        reason = text(
            row.get("risk_finalizer_reason")
            or row.get("miss_reason")
            or "selected_candidate_no_order"
        )
        return "order", f"scheduler_selected_no_order:{reason}"
    if not row.get("trade_present"):
        if row.get("selected_expiry_fallback"):
            blocker = text(row.get("terminal_fallback_blocker"))
            status = text(row.get("terminal_fallback_status"), "unknown")
            if blocker:
                return "terminal_fallback", f"selected_expiry_fallback_blocked:{blocker}"
            return "terminal_fallback", f"selected_expiry_fallback_not_filled:{status}"
        reason = text(row.get("miss_reason") or row.get("terminal_outcome"))
        return "fill", f"order_not_filled:{reason or 'terminal_reason_missing'}"
    terminal = text(row.get("terminal_outcome"), "unknown")
    net_r = optional_float(row.get("actual_r")) or 0.0
    if net_r > 0:
        return "trade", f"executed_positive_r:{terminal}"
    if net_r < 0:
        return "trade", f"executed_negative_r:{terminal}"
    return "trade", f"executed_flat_r:{terminal}"


def candidate_instance_projection(
    *,
    candidate: Mapping[str, Any],
    enrich: Mapping[str, Any],
    package_candidate: Mapping[str, Any] | None,
    generated: str,
) -> dict[str, Any]:
    package_candidate = package_candidate or {}
    scorecard = enrich.get("scorecard_binding") or {}
    order = enrich.get("order_binding") or {}
    oracle = enrich.get("oracle_binding") or {}
    trade = enrich.get("trade_binding") or {}
    missed = enrich.get("missed_binding") or {}
    downstream_bindings = [order, trade, missed, scorecard, candidate, package_candidate]
    terminal_bindings = [oracle, order, trade, missed, candidate]
    quality = canonical_quality_projection(candidate)
    authority_envelope = projection_authority_envelope_selection(
        candidate=candidate,
        package_candidate=package_candidate,
        scorecard=scorecard,
        order=order,
        trade=trade,
        missed=missed,
    )
    authority_payload = authority_envelope.get("payload")
    authority_payload = (
        authority_payload if isinstance(authority_payload, Mapping) else {}
    )
    authority_surface = authority_envelope.get("surface")
    authority_surface = (
        authority_surface if isinstance(authority_surface, Mapping) else {}
    )
    stage_binding_by_name = {
        "candidate": candidate,
        "package_candidate": package_candidate,
        "scorecard": scorecard,
        "order": order,
        "trade": trade,
        "missed": missed,
    }
    authority_stage_binding = stage_binding_by_name.get(
        text(authority_envelope.get("stage")),
        {},
    )

    raw_selector_action = text(
        first_present(
            candidate.get("raw_selector_action"),
            candidate.get("selector_action_origin"),
            candidate.get("selector_action"),
        ),
        "unknown",
    )
    package_authority_valid = authority_envelope.get("valid") is True
    effective_action = text(
        authority_payload.get("selector_action")
        if package_authority_valid
        else None,
        raw_selector_action,
    )
    effective_reason = text(
        authority_payload.get("selector_reason")
        if package_authority_valid
        else None,
        text(candidate.get("selector_reason"), "unknown"),
    )
    package_authority_status = text(
        authority_surface.get("package_new_entry_authority_status")
        if package_authority_valid
        else authority_envelope.get("status"),
        "unknown",
    )
    package_order_allowed = (
        authority_payload.get(
            "package_replay_order_executable_candidate_use_allowed"
        )
        if package_authority_valid
        else False
    )
    package_order_reason = text(
        authority_payload.get(
            "package_replay_order_executable_candidate_use_allowed_reason"
        )
        if package_authority_valid
        else authority_envelope.get("status"),
        "unknown",
    )
    package_order_transfer_status = text(
        authority_stage_binding.get("package_replay_order_executable_transfer_status"),
        "unknown",
    )
    blocker_class = text(
        authority_stage_binding.get(
            "package_replay_order_executable_final_blocker_class"
        )
    )
    blocker_reason = text(
        authority_stage_binding.get(
            "package_replay_order_executable_final_blocker_reason"
        )
    )
    blocker_source = text(
        authority_stage_binding.get(
            "package_replay_order_executable_final_blocker_source"
        )
    )
    risk_finalizer_action = text(
        first_binding_value(
            downstream_bindings,
            "risk_finalizer_action",
            "risk_finalizer_decision",
            "risk_finalizer_probe_risk_decision",
            "risk_decision",
            "effective_risk_decision",
        ),
        "unknown",
    )
    risk_finalizer_reason = text(
        first_binding_value(
            downstream_bindings,
            "risk_finalizer_reason",
            "risk_decision_reason",
        ),
        "unknown",
    )
    risk_tier = text(
        first_binding_value(
            [trade, order, missed, candidate],
            "risk_expression_ladder_tier",
        ),
        "unknown",
    )
    risk_decision = text(
        first_binding_value(
            [trade, order, missed, candidate],
            "effective_risk_decision",
            "risk_decision",
        ),
        risk_finalizer_action,
    )
    scheduler_rank_raw = first_present(
        enrich.get("scheduler_rank_min"),
        first_binding_value([scorecard, missed, candidate], "scheduler_rank", "risk_finalizer_rank"),
    )
    scheduler_rank = (
        int(safe_float(scheduler_rank_raw))
        if not missing_value(scheduler_rank_raw)
        else None
    )
    scheduler_selected = bool(
        enrich.get("scheduler_selected")
        or first_binding_value(
            [scorecard, order, trade, missed, candidate],
            "scheduler_selected",
            "scheduler_final_selected",
            "risk_finalizer_selected",
        )
    )

    order_id = text(
        first_binding_value(
            [order, trade, oracle, missed],
            "simulated_order_id",
            "package_replay_order_executable_bound_order_id",
            "package_replay_terminal_bound_order_id",
        )
    )
    trade_id = text(
        first_binding_value(
            [trade, order, oracle, missed],
            "simulated_trade_id",
            "package_replay_order_executable_bound_trade_id",
            "package_replay_terminal_bound_trade_id",
        )
    )
    order_present = bool(enrich.get("order_present"))
    trade_present = bool(enrich.get("trade_present"))
    order_binding_status = (
        "order_bound" if order_present and order_id else
        "order_present_id_missing" if order_present else
        "order_absent"
    )
    trade_binding_status = (
        "trade_bound" if trade_present and trade_id else
        "trade_present_id_missing" if trade_present else
        "trade_absent"
    )
    if trade_present:
        trade_bound_order_id = text(
            first_binding_value(
                [trade],
                "package_replay_order_executable_bound_order_id",
                "package_replay_terminal_bound_order_id",
                "simulated_order_id",
            )
        )
        order_trade_binding_status = (
            "exact_order_trade_bound"
            if order_id and trade_id and (not trade_bound_order_id or trade_bound_order_id == order_id)
            else "order_trade_binding_mismatch_or_missing_id"
        )
    elif order_present:
        order_trade_binding_status = "order_bound_trade_absent"
    else:
        order_trade_binding_status = "order_and_trade_absent"

    fallback_eligible, fallback_status, fallback_blocker = fallback_eligibility(
        terminal_bindings
    )
    counterfactual_present, counterfactual_source = counterfactual_presence(
        terminal_bindings
    )
    lifecycle_action = text(
        first_binding_value(
            [order, missed, candidate, scorecard],
            "same_symbol_lifecycle_action",
            "risk_lifecycle_action",
            "lifecycle_action",
            "scheduler_materialization_action_intent",
        )
    )
    lifecycle_reason = text(
        first_binding_value(
            [order, missed, candidate, scorecard],
            "same_symbol_lifecycle_reason",
            "lifecycle_reason",
            "scheduler_materialization_skip_reason",
        )
    )
    miss_reason = text(first_binding_value([missed], "miss_reason"))
    route_fields = route_provenance_fields(candidate, scorecard, order, trade, missed)
    poi_lineage = poi_lineage_projection_fields(
        candidate=candidate,
        scorecard=scorecard,
        order=order,
        trade=trade,
        missed=missed,
    )
    selected_date_start = text(candidate.get("projection_selected_date_start"))
    selected_date_end = text(candidate.get("projection_selected_date_end"))
    selected_profiles = string_list(candidate.get("projection_selected_profiles"))
    trading_day = parse_utc(candidate.get("trading_day"))
    decision_time = parse_utc(candidate.get("decision_time_utc"))
    start_time = parse_utc(selected_date_start)
    end_time = parse_utc(selected_date_end)
    source_window_time = trading_day or decision_time
    source_window_time_source = (
        "candidate.trading_day"
        if trading_day is not None
        else "candidate.decision_time_utc"
        if decision_time is not None
        else "unavailable"
    )
    if (
        source_window_time is not None
        and start_time is not None
        and end_time is not None
    ):
        source_window_status = (
            "inside_selected_window"
            if start_time.date() <= source_window_time.date() <= end_time.date()
            else "outside_selected_window"
        )
    else:
        source_window_status = "selected_window_or_trading_day_unavailable"
    candidate_profile = text(candidate.get("broad_replay_profile"))
    source_profile_status = (
        "inside_selected_profile"
        if not selected_profiles or candidate_profile in selected_profiles
        else "outside_selected_profile"
    )
    row = {
        "schema": "gtos.final_moonshot.denominator_to_deployment.candidate_instance_parity_projection.v1",
        "generated_utc": generated,
        "row_type": "candidate_instance_parity_projection",
        "candidate_instance_parity_key": candidate_instance_parity_key(candidate),
        "candidate_id": text(candidate.get("candidate_id")),
        "decision_time_utc": text(candidate.get("decision_time_utc")),
        **poi_lineage,
        "broad_replay_profile": text(candidate.get("broad_replay_profile")),
        "projection_source_scope_mode": text(
            candidate.get("projection_source_scope_mode"),
            "unknown_source_scope",
        ),
        "projection_source_prefix": text(
            candidate.get("projection_source_prefix")
        ),
        "projection_selected_date_start": selected_date_start,
        "projection_selected_date_end": selected_date_end,
        "projection_selected_profiles": selected_profiles,
        "projection_candidate_source_class": text(
            candidate.get("projection_candidate_source_class"),
            "unknown_candidate_source",
        ),
        "projection_candidate_source_path": text(
            candidate.get("projection_candidate_source_path")
        ),
        "projection_candidate_source_binding_status": text(
            candidate.get("projection_candidate_source_binding_status"),
            "unknown_source_binding",
        ),
        "projection_source_window_date": (
            source_window_time.date().isoformat()
            if source_window_time is not None
            else None
        ),
        "projection_source_window_date_source": source_window_time_source,
        "projection_source_window_status": source_window_status,
        "projection_source_profile_status": source_profile_status,
        "symbol": upper(candidate.get("symbol")),
        "side": side(candidate.get("side") or candidate.get("direction")),
        "origin_family": text(
            route_fields.get("origin_family")
            or candidate.get("candidate_origin_family"),
            "unknown",
        ),
        "candidate_present": True,
        "scorecard_present": bool(enrich.get("scorecard_present")),
        "scheduler_selected": scheduler_selected,
        "scheduler_rank": scheduler_rank,
        "order_present": order_present,
        "trade_present": trade_present,
        "missed_present": bool(enrich.get("missed_present")),
        "raw_selector_action": raw_selector_action,
        "effective_selector_action": effective_action,
        "effective_selector_reason": effective_reason,
        **quality,
        "package_authority_valid": package_authority_valid,
        "package_authority_status": package_authority_status,
        "package_authority_envelope_status": authority_envelope.get("status"),
        "package_authority_envelope_source_stage": authority_envelope.get("stage"),
        "package_authority_envelope_source_surface": authority_envelope.get("source"),
        "package_authority_envelope_digest_sha256": authority_envelope.get("digest"),
        "package_authority_envelope_reasons": list(
            authority_envelope.get("reasons") or []
        ),
        "package_authority_projection_valid": package_authority_valid,
        "package_order_executable_permission_envelope_digest_sha256": (
            authority_envelope.get("digest") if package_authority_valid else None
        ),
        "package_authority_projection_permission_same_envelope": bool(
            package_authority_valid
            and authority_envelope.get("digest")
            and isinstance(package_order_allowed, bool)
        ),
        "package_order_executable_allowed": package_order_allowed,
        "package_order_executable_reason": package_order_reason,
        "package_order_executable_transfer_status": package_order_transfer_status,
        "package_order_executable_blocker_class": blocker_class,
        "package_order_executable_blocker_reason": blocker_reason,
        "package_order_executable_blocker_source": blocker_source,
        "risk_finalizer_action": risk_finalizer_action,
        "risk_finalizer_reason": risk_finalizer_reason,
        "risk_expression_ladder_tier": risk_tier,
        "risk_behavior": risk_behavior_from_projection(
            tier=risk_tier,
            decision=risk_decision,
        ),
        "order_binding_status": order_binding_status,
        "order_id": order_id,
        "trade_binding_status": trade_binding_status,
        "trade_id": trade_id,
        "order_trade_binding_status": order_trade_binding_status,
        "order_status": text(first_binding_value([order], "order_status")),
        "terminal_fill_status": text(
            first_binding_value([oracle, missed], "fill_status", "counterfactual_order_fill_status")
        ),
        "terminal_outcome": text(
            first_binding_value(
                [trade, oracle, missed],
                "terminal_outcome",
                "counterfactual_order_terminal_outcome",
            )
        ),
        "terminal_fallback_configured": first_binding_value(
            terminal_bindings,
            "guarded_market_fallback_configured",
        ),
        "terminal_fallback_eligible": fallback_eligible,
        "terminal_fallback_status": fallback_status,
        "terminal_fallback_blocker": fallback_blocker,
        "terminal_fallback_attempted": first_binding_value(
            terminal_bindings,
            "guarded_market_fallback_attempted",
        ),
        "terminal_fallback_applied": first_binding_value(
            terminal_bindings,
            "guarded_market_fallback_applied",
        ),
        "terminal_counterfactual_present": counterfactual_present,
        "terminal_counterfactual_source": counterfactual_source,
        "lifecycle_action": lifecycle_action,
        "lifecycle_reason": lifecycle_reason,
        "miss_reason": miss_reason,
        "actual_r": safe_float(enrich.get("net_r")),
        "broker_live_authority": False,
        "final_selection_claim": False,
    }
    row["selected_expiry_fallback"] = selected_expiry_projection(row)
    deviation_stage, deviation_reason = exact_projection_deviation(row)
    row["exact_deviation_stage"] = deviation_stage
    row["exact_deviation_reason"] = deviation_reason
    return row


def iter_candidate_instance_projection_rows(
    *,
    candidates: Mapping[Any, Mapping[str, Any]],
    enrichment: Mapping[str, Mapping[str, Any]],
    package_candidate_index: Mapping[str, Mapping[str, Any]],
    generated: str,
) -> Iterator[dict[str, Any]]:
    """Yield exact candidate projections in their canonical output order."""

    for candidate in sorted(
        candidates.values(),
        key=lambda row: (
            text(row.get("broad_replay_profile")),
            text(row.get("decision_time_utc")),
            upper(row.get("symbol")),
            side(row.get("side") or row.get("direction")),
            text(row.get("candidate_id")),
        ),
    ):
        package_candidate, match_status, match_count = resolve_package_candidate(
            candidate,
            package_candidate_index,
        )
        projection = candidate_instance_projection(
            candidate=candidate,
            enrich=enrichment.get(text(candidate.get("candidate_instance_key")), {}),
            package_candidate=package_candidate,
            generated=generated,
        )
        projection["package_candidate_identity_match_status"] = match_status
        projection["package_candidate_identity_match_count"] = match_count
        yield projection


def build_candidate_instance_projection_rows(
    *,
    candidates: Mapping[Any, Mapping[str, Any]],
    enrichment: Mapping[str, Mapping[str, Any]],
    package_candidate_index: Mapping[str, Mapping[str, Any]],
    generated: str,
) -> list[dict[str, Any]]:
    """Compatibility materializer for bounded callers and focused tests."""

    return list(
        iter_candidate_instance_projection_rows(
            candidates=candidates,
            enrichment=enrichment,
            package_candidate_index=package_candidate_index,
            generated=generated,
        )
    )


def summarize_candidate_instance_projection_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_scope: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    key_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    profile_stage_counts: dict[str, Counter[str]] = defaultdict(Counter)
    package_candidate_identity_match_status_counts: Counter[str] = Counter()
    selector_transfer_counts: Counter[str] = Counter()
    quality_status_counts: Counter[str] = Counter()
    quality_violation_counts: Counter[str] = Counter()
    quality_source_counts: Counter[str] = Counter()
    quality_field_source_counts: dict[str, Counter[str]] = {
        field: Counter()
        for field in ("expected_net_r", "probability", "source_completeness")
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
    binding_status_counts: Counter[str] = Counter()
    fallback_status_counts: Counter[str] = Counter()
    fallback_blocker_counts: Counter[str] = Counter()
    counterfactual_source_counts: Counter[str] = Counter()
    deviation_stage_counts: Counter[str] = Counter()
    deviation_reason_counts: Counter[str] = Counter()
    source_scope_mode_counts: Counter[str] = Counter()
    source_prefix_counts: Counter[str] = Counter()
    candidate_source_class_counts: Counter[str] = Counter()
    candidate_source_path_counts: Counter[str] = Counter()
    candidate_source_binding_counts: Counter[str] = Counter()
    source_window_date_source_counts: Counter[str] = Counter()
    source_window_status_counts: Counter[str] = Counter()
    source_profile_status_counts: Counter[str] = Counter()
    origin_transfer: dict[str, Counter[str]] = defaultdict(Counter)
    selected_expiry = Counter()
    min_decision_time: tuple[datetime, str] | None = None
    max_decision_time: tuple[datetime, str] | None = None
    row_count = 0

    for row in rows:
        row_count += 1
        profile = text(row.get("broad_replay_profile"), "unknown")
        package_candidate_identity_match_status_counts[
            text(
                row.get("package_candidate_identity_match_status"),
                "missing",
            )
        ] += 1
        source_scope_mode_counts[
            text(row.get("projection_source_scope_mode"), "unknown_source_scope")
        ] += 1
        source_prefix_counts[
            text(row.get("projection_source_prefix"), "missing_source_prefix")
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
        window_status = text(
            row.get("projection_source_window_status"),
            "selected_window_or_trading_day_unavailable",
        )
        source_window_status_counts[window_status] += 1
        profile_status = text(
            row.get("projection_source_profile_status"),
            "selected_profile_or_candidate_profile_unavailable",
        )
        source_profile_status_counts[profile_status] += 1
        decision_time_text = text(row.get("decision_time_utc"))
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
        for stage, field in (
            ("candidate", "candidate_present"),
            ("scorecard", "scorecard_present"),
            ("scheduler_selected", "scheduler_selected"),
            ("order", "order_present"),
            ("trade", "trade_present"),
            ("missed", "missed_present"),
        ):
            present = int(row.get(field) is True)
            stage_counts[stage] += present
            profile_stage_counts[profile][stage] += present
        selector_transfer_counts[
            f"{text(row.get('raw_selector_action'), 'unknown')}->{text(row.get('effective_selector_action'), 'unknown')}"
        ] += 1
        quality_status_counts[
            text(row.get("canonical_quality_contract_status"), "unknown")
        ] += 1
        quality_violation_counts.update(
            string_list(row.get("canonical_quality_contract_violations"))
        )
        quality_source_counts[
            text(row.get("canonical_quality_source"), "missing")
        ] += 1
        field_sources = row.get("canonical_quality_field_sources")
        field_sources = field_sources if isinstance(field_sources, Mapping) else {}
        for field, counter in quality_field_source_counts.items():
            counter[text(field_sources.get(field), "missing")] += 1
        package_authority_valid_counts[
            text(row.get("package_authority_valid"), "unknown")
        ] += 1
        package_authority_status_counts[
            text(row.get("package_authority_status"), "unknown")
        ] += 1
        package_order_allowed_counts[
            text(row.get("package_order_executable_allowed"), "unknown")
        ] += 1
        package_order_reason_counts[
            text(row.get("package_order_executable_reason"), "unknown")
        ] += 1
        package_order_transfer_status_counts[
            text(row.get("package_order_executable_transfer_status"), "unknown")
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
            text(row.get("risk_finalizer_action"), "unknown")
        ] += 1
        risk_finalizer_reason_counts[
            text(row.get("risk_finalizer_reason"), "unknown")
        ] += 1
        risk_behavior = text(row.get("risk_behavior"), "unknown")
        risk_behavior_counts[risk_behavior] += 1
        if row.get("order_present"):
            order_risk_behavior_counts[risk_behavior] += 1
        if row.get("trade_present"):
            filled_risk_behavior_counts[risk_behavior] += 1
        scheduler_rank_counts[
            text(row.get("scheduler_rank"), "not_ranked")
        ] += 1
        for field in (
            "order_binding_status",
            "trade_binding_status",
            "order_trade_binding_status",
        ):
            binding_status_counts[f"{field}:{text(row.get(field), 'unknown')}"] += 1
        fallback_status_counts[
            text(row.get("terminal_fallback_status"), "missing")
        ] += 1
        fallback_blocker_counts[
            text(row.get("terminal_fallback_blocker"), "none")
        ] += 1
        counterfactual_source_counts[
            text(row.get("terminal_counterfactual_source"), "none")
        ] += 1
        deviation_stage_counts[
            text(row.get("exact_deviation_stage"), "unknown")
        ] += 1
        deviation_reason_counts[
            text(row.get("exact_deviation_reason"), "unknown")
        ] += 1

        origin = text(row.get("origin_family"), "unknown")
        transfer = origin_transfer[origin]
        transfer["candidate"] += 1
        transfer["scorecard"] += int(row.get("scorecard_present") is True)
        transfer["scheduler_selected"] += int(row.get("scheduler_selected") is True)
        transfer["order"] += int(row.get("order_present") is True)
        transfer["fill"] += int(row.get("trade_present") is True)
        transfer["missed"] += int(row.get("missed_present") is True)
        if row.get("scorecard_present") and row.get("order_present"):
            transfer["scorecard_to_order"] += 1
        if row.get("order_present") and row.get("trade_present"):
            transfer["order_to_fill"] += 1

        if row.get("selected_expiry_fallback"):
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
                bool(text(row.get("terminal_fallback_blocker")))
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
            proof_complete = (
                isinstance(row.get("terminal_fallback_eligible"), bool)
                and bool(text(row.get("terminal_fallback_status")))
                and (
                    row.get("terminal_fallback_eligible") is True
                    or bool(text(row.get("terminal_fallback_blocker")))
                )
                and row.get("terminal_counterfactual_present") is True
            )
            selected_expiry["proof_complete"] += int(proof_complete)

    origin_output: dict[str, dict[str, Any]] = {}
    for origin, counts in sorted(origin_transfer.items()):
        output = counter_dict(counts)
        for field in (
            "candidate",
            "scorecard",
            "scheduler_selected",
            "order",
            "fill",
            "missed",
            "scorecard_to_order",
            "order_to_fill",
        ):
            output.setdefault(field, 0)
        output["scorecard_to_order_rate"] = pct(
            output.get("scorecard_to_order", 0),
            output.get("scorecard", 0),
        )
        output["order_to_fill_rate"] = pct(
            output.get("order_to_fill", 0),
            output.get("order", 0),
        )
        origin_output[origin] = output
    duplicate_keys = sorted(key for key, count in key_counts.items() if count > 1)
    duplicate_key_count = sum(
        count - 1 for count in key_counts.values() if count > 1
    )
    scope_output = dict(source_scope or {})
    expected_candidate_rows_raw = scope_output.get(
        "authoritative_candidate_declared_rows"
    )
    expected_candidate_rows = (
        int(expected_candidate_rows_raw)
        if expected_candidate_rows_raw not in (None, "")
        else None
    )
    included_bridges = scope_output.get("included_bridge_artifacts")
    included_bridges = included_bridges if isinstance(included_bridges, list) else []
    exact_bound_bridge_supplement = any(
        isinstance(item, Mapping)
        and item.get("included") is True
        and item.get("standalone_selected") is not True
        for item in included_bridges
    )
    if expected_candidate_rows is None:
        candidate_count_status = "not_applicable_declared_count_unavailable"
    elif exact_bound_bridge_supplement:
        candidate_count_status = (
            "pass"
            if row_count >= expected_candidate_rows
            else "fail_below_authoritative_declared_count"
        )
    else:
        candidate_count_status = (
            "pass"
            if row_count == expected_candidate_rows
            else "fail_authoritative_declared_count_mismatch"
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
    authoritative_source_available = (
        scope_output.get("authoritative_candidate_source_available") is True
    )
    producer_rows = int(
        safe_float(scope_output.get("order_trade_missed_candidate_producer_rows"))
    )
    producer_policy_status = (
        "pass"
        if not authoritative_source_available or producer_rows == 0
        else "fail_enrichment_source_materialized_candidates"
    )
    materialized_rows_raw = scope_output.get("candidate_instances_materialized")
    materialized_rows = (
        int(materialized_rows_raw)
        if materialized_rows_raw not in (None, "")
        else None
    )
    materialized_count_status = (
        "not_applicable_loader_count_unavailable"
        if materialized_rows is None
        else "pass"
        if materialized_rows == row_count
        else "fail_loader_projection_count_mismatch"
    )
    assertion_statuses = (
        candidate_count_status,
        producer_policy_status,
        materialized_count_status,
        "pass" if duplicate_key_count == 0 else "fail_duplicate_projection_keys",
        "pass"
        if out_of_window_count == 0 and unavailable_window_count == 0
        else "fail_projection_rows_outside_or_unverifiable_window",
        "pass"
        if out_of_profile_count == 0 and unavailable_profile_count == 0
        else "fail_projection_rows_outside_or_unverifiable_profile",
    )
    scope_output.update(
        {
            "projection_row_count": row_count,
            "min_decision_time_utc": (
                min_decision_time[1] if min_decision_time is not None else None
            ),
            "max_decision_time_utc": (
                max_decision_time[1] if max_decision_time is not None else None
            ),
            "row_source_scope_mode_counts": counter_dict(source_scope_mode_counts),
            "row_source_prefix_counts": counter_dict(source_prefix_counts),
            "row_candidate_source_class_counts": counter_dict(
                candidate_source_class_counts
            ),
            "row_candidate_source_path_counts": counter_dict(
                candidate_source_path_counts
            ),
            "row_candidate_source_binding_status_counts": counter_dict(
                candidate_source_binding_counts
            ),
            "row_source_window_date_source_counts": counter_dict(
                source_window_date_source_counts
            ),
            "row_source_window_status_counts": counter_dict(
                source_window_status_counts
            ),
            "row_source_profile_status_counts": counter_dict(
                source_profile_status_counts
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
                "authoritative_candidate_count": {
                    "status": candidate_count_status,
                    "expected_declared_rows": expected_candidate_rows,
                    "actual_projection_rows": row_count,
                    "exact_bound_bridge_supplement_allowed": (
                        exact_bound_bridge_supplement
                    ),
                },
                "loader_projection_count": {
                    "status": materialized_count_status,
                    "loader_materialized_candidate_instances": materialized_rows,
                    "actual_projection_rows": row_count,
                },
                "order_trade_missed_candidate_producer_policy": {
                    "status": producer_policy_status,
                    "authoritative_candidate_source_available": (
                        authoritative_source_available
                    ),
                    "candidate_producer_rows": producer_rows,
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
            "assertion_status": (
                "fail"
                if any(status.startswith("fail") for status in assertion_statuses)
                else "pass"
            ),
        }
    )
    return {
        "schema": "gtos.final_moonshot.denominator_to_deployment.candidate_instance_parity_projection.summary.v1",
        "row_count": row_count,
        "unique_candidate_instance_parity_key_count": len(key_counts),
        "duplicate_candidate_instance_parity_key_count": duplicate_key_count,
        "duplicate_candidate_instance_parity_key_samples": duplicate_keys[:12],
        "projection_source_scope": scope_output,
        "stage_presence_counts": counter_dict(stage_counts),
        "profile_stage_presence_counts": {
            profile: counter_dict(counts)
            for profile, counts in sorted(profile_stage_counts.items())
        },
        "package_candidate_identity_match_status_counts": counter_dict(
            package_candidate_identity_match_status_counts
        ),
        "raw_to_effective_selector_action_counts": top_counter(
            selector_transfer_counts, limit=24
        ),
        "canonical_quality_contract": {
            "status_counts": counter_dict(quality_status_counts),
            "violation_row_count": int(quality_status_counts.get("violation", 0)),
            "violation_reason_counts": top_counter(quality_violation_counts, limit=32),
            "source_counts": top_counter(quality_source_counts, limit=24),
            "field_source_counts": {
                field: top_counter(counter, limit=24)
                for field, counter in quality_field_source_counts.items()
            },
        },
        "package_authority_valid_counts": counter_dict(package_authority_valid_counts),
        "package_authority_status_counts": top_counter(
            package_authority_status_counts, limit=24
        ),
        "package_order_executable_allowed_counts": counter_dict(
            package_order_allowed_counts
        ),
        "package_order_executable_reason_counts": top_counter(
            package_order_reason_counts, limit=32
        ),
        "package_order_executable_transfer_status_counts": top_counter(
            package_order_transfer_status_counts, limit=24
        ),
        "package_order_executable_blocker_class_counts": top_counter(
            package_order_blocker_counts, limit=24
        ),
        "package_order_executable_blocker_reason_counts": top_counter(
            package_order_blocker_reason_counts, limit=32
        ),
        "package_order_executable_blocker_source_counts": top_counter(
            package_order_blocker_source_counts, limit=24
        ),
        "risk_finalizer_action_counts": counter_dict(risk_finalizer_action_counts),
        "risk_finalizer_reason_counts": top_counter(
            risk_finalizer_reason_counts, limit=32
        ),
        "scheduler_rank_counts": top_counter(scheduler_rank_counts, limit=24),
        "binding_status_counts": counter_dict(binding_status_counts),
        "terminal_fallback_status_counts": top_counter(
            fallback_status_counts, limit=24
        ),
        "terminal_fallback_blocker_counts": top_counter(
            fallback_blocker_counts, limit=24
        ),
        "terminal_counterfactual_source_counts": top_counter(
            counterfactual_source_counts, limit=24
        ),
        "exact_deviation_stage_counts": counter_dict(deviation_stage_counts),
        "exact_deviation_reason_counts": top_counter(
            deviation_reason_counts, limit=48
        ),
        "origin_family_scorecard_order_fill_transfer": origin_output,
        "selected_expiry_fallback_proof": counter_dict(selected_expiry),
        "full_reduced_risk_behavior": {
            "all_candidate_instance_counts": counter_dict(risk_behavior_counts),
            "order_counts": counter_dict(order_risk_behavior_counts),
            "filled_trade_counts": counter_dict(filled_risk_behavior_counts),
        },
    }


def build_big_r_provenance(observation_status: str) -> dict[str, Any]:
    surface = read_json(SURFACE_PATH)
    synthesis_summary = read_json(FINAL_PACKAGE_SYNTHESIS / "FINAL_PACKAGE_SYNTHESIS_SUMMARY.json")
    convergence_audit = read_json(CONVERGENCE / "ULTIMATE_SYSTEM_CONVERGENCE_EXTREME_R_AUDIT.json")
    scheduler_status = read_json(SCHEDULER_V3 / "SCHEDULER_V3_RESULT_USE_STATUS.json")

    sleeve_type_counts: Counter[str] = Counter()
    package_role_counts: Counter[str] = Counter()
    member_rows_by_type: Counter[str] = Counter()
    source_disposition_counts: Counter[str] = Counter()
    exact_join_status_counts: Counter[str] = Counter()
    exact_join_rows = 0
    candidate_id_carried = 0
    decision_window_carried = 0

    for row in iter_jsonl(SLEEVE_REGISTRY_PATH):
        sleeve_type_counts[text(row.get("sleeve_type"), "unknown")] += 1
        package_role_counts[text(row.get("package_role"), "unknown")] += 1

    for row in iter_jsonl(SLEEVE_MEMBER_PATH):
        member_rows_by_type[text(row.get("sleeve_type"), "unknown")] += 1
        source_disposition_counts[text(row.get("source_disposition"), "unknown")] += 1
        exact_join_status_counts[text(row.get("exact_join_status"), "unknown")] += 1
        exact_join_rows += int(safe_float(row.get("exact_denominator_join_rows")))
        candidate_id_carried += 1 if row.get("candidate_id_carried_to_member") is True else 0
        decision_window_carried += 1 if row.get("decision_window_id_carried_to_member") is True else 0

    candidate_level, candidate_level_source_path = required_numeric_source_value(
        "candidate_level_source_bound_r_sum",
        (surface, SURFACE_PATH),
        (
            synthesis_summary,
            FINAL_PACKAGE_SYNTHESIS / "FINAL_PACKAGE_SYNTHESIS_SUMMARY.json",
        ),
    )
    selector_lift = safe_float(surface.get("selector_lift_sum"))
    scheduler_result = safe_float(surface.get("scheduler_result_r_sum"))
    formula_sum = round(candidate_level + selector_lift + scheduler_result, 10)

    convergence_rows = convergence_audit.get("rows") if isinstance(convergence_audit.get("rows"), list) else []
    scheduler_proxy = (
        scheduler_status.get("exact_proxy_expectancy_by_class", {})
        .get("source_bound_proxy", {})
        .get("r_sum")
        if isinstance(scheduler_status.get("exact_proxy_expectancy_by_class"), dict)
        else None
    )

    return {
        "schema": "gtos.final_moonshot.denominator_to_deployment.big_r_provenance_breakdown.v1",
        "generated_utc": utc_now(),
        "route_id": ROUTE.name,
        "broad_replay_prefix": BROAD_PREFIX,
        "broad_replay_observation_status": observation_status,
        "broker_live_authority": False,
        "final_selection_claim": False,
        "claims": [
            {
                "claim_id": "ultimate_candidate_package_surface_combined",
                "value_r": surface.get("combined_source_bound_signal_r_sum"),
                "artifact_path": str(SURFACE_PATH),
                "json_key": "combined_source_bound_signal_r_sum",
                "formula": "candidate_level_source_bound_r_sum + selector_lift_sum + scheduler_result_r_sum",
                "formula_sum_r": formula_sum,
                "formula_delta_r": round(
                    safe_float(surface.get("combined_source_bound_signal_r_sum")) - formula_sum,
                    10,
                ),
                "formula_components": [
                    {
                        "component": "candidate_level_source_bound",
                        "value_r": candidate_level,
                        "artifact_path": str(candidate_level_source_path),
                        "source_value_key": "candidate_level_source_bound_r_sum",
                        "upstream_row_count": synthesis_summary.get("candidate_level_source_bound_rows")
                        or synthesis_summary.get("candidate_rows")
                        or 38863,
                    },
                    {
                        "component": "selector_lift",
                        "value_r": selector_lift,
                        "artifact_path": str(SURFACE_PATH),
                        "source_value_key": "selector_lift_sum",
                    },
                    {
                        "component": "scheduler_result",
                        "value_r": scheduler_result,
                        "artifact_path": str(SURFACE_PATH),
                        "source_value_key": "scheduler_result_r_sum",
                    },
                ],
            },
            {
                "claim_id": "scheduler_lifecycle_combined_source_bound_signal",
                "value_r": surface.get("scheduler_lifecycle_combined_source_bound_signal_r_sum"),
                "artifact_path": str(SURFACE_PATH),
                "json_key": "scheduler_lifecycle_combined_source_bound_signal_r_sum",
            },
            {
                "claim_id": "final_package_synthesis_candidate_level_source_bound",
                "value_r": synthesis_summary.get("candidate_level_source_bound_r_sum"),
                "artifact_path": str(FINAL_PACKAGE_SYNTHESIS / "FINAL_PACKAGE_SYNTHESIS_SUMMARY.json"),
                "json_key": "candidate_level_source_bound_r_sum",
            },
            {
                "claim_id": "convergence_selector_v3_source_bound_proxy",
                "value_r": convergence_rows[0].get("total_r") if convergence_rows else None,
                "artifact_path": str(CONVERGENCE / "ULTIMATE_SYSTEM_CONVERGENCE_EXTREME_R_AUDIT.json"),
                "json_key": "rows[0].total_r",
            },
            {
                "claim_id": "scheduler_v3_source_bound_proxy",
                "value_r": scheduler_proxy,
                "artifact_path": str(SCHEDULER_V3 / "SCHEDULER_V3_RESULT_USE_STATUS.json"),
                "json_key": "exact_proxy_expectancy_by_class.source_bound_proxy.r_sum",
            },
        ],
        "compressed_surface": {
            "sleeve_rows": surface.get("compressed_sleeve_rows"),
            "member_rows": surface.get("compressed_member_rows"),
            "sleeve_type_counts": surface.get("sleeve_type_counts") or counter_dict(sleeve_type_counts),
            "member_rows_by_sleeve_type": surface.get("member_rows_by_sleeve_type")
            or counter_dict(member_rows_by_type),
            "package_role_counts": surface.get("package_role_counts")
            or counter_dict(package_role_counts),
            "scheduler_shadow_ledger_rows": surface.get("scheduler_shadow_ledger_rows"),
            "selector_shadow_ledger_rows": surface.get("selector_shadow_ledger_rows"),
        },
        "overlap_audit": {
            "classes_are_not_additive": True,
            "source_member_rows": sum(member_rows_by_type.values()),
            "source_member_candidate_id_carried_rows": candidate_id_carried,
            "source_member_decision_window_id_carried_rows": decision_window_carried,
            "source_member_exact_denominator_join_rows": exact_join_rows,
            "source_disposition_counts": counter_dict(source_disposition_counts),
            "exact_join_status_counts": top_counter(exact_join_status_counts),
            "join_key_policy": (
                "exact package candidate IDs are exact; source sleeve/member rows use "
                "symbol/side/framework/origin/session overlap and are not additive as exact R proof"
            ),
        },
        "breakdown_fields": [
            "sleeve_type",
            "package_role",
            "source_disposition",
            "symbol",
            "side",
            "session_bucket",
            "framework",
            "origin_family",
            "selector_action",
            "scheduler_rank",
            "scheduler_selection",
            "risk_decision",
            "order_policy",
            "order_status",
            "fillability_status",
            "fill_status",
            "lifecycle_action",
            "exit_result",
            "terminal_outcome",
            "close_reason",
            "actual_r",
            "deviation_reason",
            "diagnostic_package_source_bound_r",
            "diagnostic_source_bound_r",
            "effective_package_source_bound_r",
            "effective_source_bound_r",
            "package_source_bound_r",
            "source_bound_r",
        ],
    }


def _build_parity_rows_and_projection() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    return _build_parity_rows_and_projection_with_sinks()


def _build_parity_rows_and_projection_with_sinks(
    *,
    candidate_projection_sink: Callable[[Mapping[str, Any]], None] | None = None,
    candidate_trace_sink: Callable[[Mapping[str, Any]], None] | None = None,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Build parity proof, optionally streaming its two high-cardinality rows.

    With sinks, the returned parity list contains only the axis prefix and the
    returned projection list is empty. Counts and summaries remain complete;
    callers concatenate the streamed trace spool after the axis prefix.
    """

    observation_status = artifact_status()
    candidates, by_axis, enrichment, projection_source_scope = (
        _load_broad_indexes_with_scope()
    )
    profiles = discover_profiles(candidates)

    exact_package_candidate_ids: set[str] = set()
    package_candidate_index: dict[str, Any] = {
        "by_signed_instance": defaultdict(list),
        "by_exact_instance": defaultdict(list),
        "by_candidate_id": defaultdict(list),
    }
    exact_package_candidate_rows = 0
    package_authority_order_geometry_status_counts: Counter[str] = Counter()
    for row in iter_jsonl(PACKAGE_CANDIDATE_PATH):
        candidate_id = text(row.get("candidate_id"))
        if candidate_id:
            exact_package_candidate_ids.add(candidate_id)
            package_candidate = reduced_package_candidate(row)
            package_candidate_index["by_candidate_id"][candidate_id].append(
                package_candidate
            )
            for signed_key in package_candidate_signed_instance_keys(package_candidate):
                package_candidate_index["by_signed_instance"][signed_key].append(
                    package_candidate
                )
            exact_key = package_candidate_exact_instance_key(package_candidate)
            if exact_key is not None:
                package_candidate_index["by_exact_instance"][exact_key].append(
                    package_candidate
                )
            package_authority_order_geometry_status_counts[
                text(
                    package_candidate.get("package_authority_order_geometry_status"),
                    "unknown",
                )
            ] += 1
            exact_package_candidate_rows += 1

    axis_rows: list[dict[str, Any]] = []
    candidate_trace_rows: list[dict[str, Any]] = []
    candidate_trace_row_count = 0
    generated = utc_now()
    candidate_instance_projection_iter = iter_candidate_instance_projection_rows(
        candidates=candidates,
        enrichment=enrichment,
        package_candidate_index=package_candidate_index,
        generated=generated,
    )
    if candidate_projection_sink is None:
        candidate_instance_projection_rows = list(
            candidate_instance_projection_iter
        )
        candidate_instance_projection_summary = (
            summarize_candidate_instance_projection_rows(
                candidate_instance_projection_rows,
                source_scope=projection_source_scope,
            )
        )
    else:
        candidate_instance_projection_rows = []
        candidate_instance_projection_summary = (
            summarize_candidate_instance_projection_rows(
                rows_with_sink(
                    candidate_instance_projection_iter,
                    candidate_projection_sink,
                ),
                source_scope=projection_source_scope,
            )
        )
    for member in iter_jsonl(SLEEVE_MEMBER_PATH):
        axis_symbol = upper(member.get("symbol") or member.get("normalized_symbol"))
        axis_side = side(member.get("side"))
        member_candidates = by_axis.get((axis_symbol, axis_side), [])
        for profile_name in profiles:
            profile_member_candidates = [
                row
                for row in member_candidates
                if row["broad_replay_profile"] == profile_name
            ]
            profile_axis_identity_candidates = [
                row
                for row in profile_member_candidates
                if candidate_matches_stable_member_axis_id(member, row)
            ]
            profile_candidates = [
                row
                for row in profile_member_candidates
                if sleeve_axis_matches_candidate(member, row)
            ]
            if profile_axis_identity_candidates:
                candidate_by_instance = {
                    row["candidate_instance_key"]: row
                    for row in [
                        *profile_axis_identity_candidates,
                        *profile_candidates,
                    ]
                }
                profile_candidates = list(candidate_by_instance.values())
            summary = summarize_enrichment(profile_candidates, enrichment)
            resolved_package_candidates = {
                row["candidate_instance_key"]: resolve_package_candidate(
                    row,
                    package_candidate_index,
                )
                for row in profile_candidates
            }
            exact_matches = [
                row["candidate_instance_key"]
                for row in profile_candidates
                if resolved_package_candidates[row["candidate_instance_key"]][1].startswith(
                    "exact_"
                )
            ]
            exact_match_candidate_ids = [
                row["candidate_id"]
                for row in profile_candidates
                if row["candidate_instance_key"] in set(exact_matches)
            ]
            source_bound_r = safe_float(member.get("combined_source_bound_signal_r"))
            trace_rows = [
                candidate_trace(
                    candidate=row,
                    enrich=enrichment.get(row["candidate_instance_key"], {}),
                    package_candidate=resolved_package_candidates[
                        row["candidate_instance_key"]
                    ][0],
                    exact_package_candidate_ids=exact_package_candidate_ids,
                    source_bound_r=source_bound_r,
                )
                for row in sorted(
                    profile_candidates,
                    key=lambda item: (
                        item["decision_time_utc"],
                        item["symbol"],
                        item["side"],
                        item["candidate_id"],
                    ),
                )
            ]
            trace_sample_limit = 12
            axis_effective_source_bound_r = (
                source_bound_r
                if any(
                    row.get("package_replay_executable_candidate_use_allowed") is True
                    for row in trace_rows
                )
                else 0.0
            )
            package_role = member.get("package_role") or package_role_for_sleeve_type(
                member.get("sleeve_type")
            )
            bridge_materialized = selected_package_bridge_materialized(member)
            generated_label = (
                "candidate_generated"
                if summary["candidate_generated_count"] > 0
                else "candidate_generated_via_selected_package_bridge"
                if bridge_materialized
                else "candidate_not_generated"
            )
            source_axis_class = source_axis_replay_class(package_role)
            mismatch = axis_unmatched_diagnostic(member, profile_member_candidates)
            if int(summary.get("candidate_generated_count") or 0) <= 0:
                exact_join_status = text(member.get("exact_join_status"))
                bridge_label = selected_package_bridge_materialization_label(
                    member,
                    package_role=package_role,
                )
                if bridge_label:
                    label = bridge_label
                elif (
                    exact_join_status
                    == "axis_candidate_namespace_materialized_no_lifecycle_label_context"
                    and text(package_role) in EXECUTABLE_SOURCE_BOUND_ROLES
                ):
                    label = (
                        "selected_package_candidate_namespace_materialized_"
                        "lifecycle_label_context_source_gap"
                    )
                elif executable_axis_missing_row_bound_selected_package_source(
                    member,
                    package_role=package_role,
                ):
                    materialization_status = (
                        selected_package_replay_source_materialization_status(
                            member,
                            package_role=package_role,
                        )
                    )
                    if materialization_status == (
                        "selected_package_replay_source_not_materialized_in_current_lifecycle_window"
                    ):
                        label = (
                            "selected_package_lifecycle_context_without_current_replay_"
                            "source_materialization"
                        )
                    elif materialization_status == (
                        "selected_package_replay_source_not_materialized_no_hydrated_selector_candidate_rows"
                    ):
                        label = (
                            "selected_package_replay_source_not_materialized_"
                            "no_hydrated_selector_candidate_rows"
                        )
                    else:
                        label = (
                            "executable_axis_missing_row_bound_selected_package_replay_"
                            "candidate_or_decision_window"
                        )
                else:
                    label = zero_candidate_leakage_label(
                        package_role=package_role,
                        mismatch_reason=text(
                            mismatch.get("candidate_generation_mismatch_reason")
                        ),
                    )
            else:
                label = non_executable_role_leakage_label(package_role) or leakage_label(
                    summary
                )
            summary = apply_execution_leakage_accounting(summary, label=label)
            axis_identity = {
                "source_axis_row_index": member.get("source_axis_row_index"),
                "stable_member_axis_id": member.get("stable_member_axis_id"),
                "sleeve_id": member.get("sleeve_id"),
                "sleeve_type": member.get("sleeve_type"),
                "package_role": package_role,
                "source_axis_replay_class": source_axis_class,
                "source_disposition": member.get("source_disposition"),
                "source_framework": member.get("framework"),
                "source_origin_family": member.get("origin_family"),
                "source_side": axis_side,
                "source_symbol": axis_symbol,
                "source_session_bucket": member.get("session_bucket"),
                "combined_source_bound_signal_r": source_bound_r,
                "diagnostic_source_bound_r": source_bound_r,
                "diagnostic_package_source_bound_r": source_bound_r,
                "effective_source_bound_r": axis_effective_source_bound_r,
                "effective_package_source_bound_r": axis_effective_source_bound_r,
                "source_bound_r": axis_effective_source_bound_r,
                "package_source_bound_r": axis_effective_source_bound_r,
                "source_bound_r_evidence_class": (
                    "source_member_axis_overlap_not_additive_exact_execution_r"
                ),
                "source_bound_r_additive_allowed": False,
                "source_bound_r_additive_unit": "source_member_axis",
                "exact_denominator_join_rows": int(
                    safe_float(member.get("exact_denominator_join_rows"))
                ),
                "exact_join_status": member.get("exact_join_status"),
                "selected_package_replay_bridge_candidate_rows": int(
                    safe_float(member.get("selected_package_replay_bridge_candidate_rows"))
                ),
                "selected_package_replay_bridge_materialization_scope": member.get(
                    "selected_package_replay_bridge_materialization_scope"
                ),
                "selected_package_replay_bridge_source_counts": member.get(
                    "selected_package_replay_bridge_source_counts"
                )
                or {},
                "selected_package_replay_bridge_materialization_binding_statuses": string_list(
                    member.get(
                        "selected_package_replay_bridge_materialization_binding_statuses"
                    )
                ),
                "selected_package_replay_bridge_evidence_classes": string_list(
                    member.get("selected_package_replay_bridge_evidence_classes")
                ),
                "selected_package_replay_bridge_decision_time_sources": string_list(
                    member.get("selected_package_replay_bridge_decision_time_sources")
                ),
                "selected_package_replay_bridge_source_truth_scopes": string_list(
                    member.get("selected_package_replay_bridge_source_truth_scopes")
                ),
                "selected_package_replay_bridge_lifecycle_label_context_present": (
                    selected_package_bridge_lifecycle_context_present(member)
                ),
                "selected_package_replay_bridge_lifecycle_label_context_rows": int(
                    safe_float(
                        member.get(
                            "selected_package_replay_bridge_lifecycle_label_context_rows"
                        )
                    )
                ),
                "selected_package_source_axis_lifecycle_label_context_available": (
                    selected_package_source_axis_lifecycle_context_available(member)
                ),
                "selected_package_source_axis_lifecycle_label_context_rows": int(
                    safe_float(
                        member.get("source_axis_lifecycle_label_context_rows")
                    )
                ),
                "selected_package_legacy_context_lifecycle_label_rows": int(
                    safe_float(member.get("context_lifecycle_label_rows"))
                ),
                "selected_package_source_axis_lifecycle_label_context_id_count": int(
                    safe_float(
                        member.get("source_axis_lifecycle_label_context_id_count")
                    )
                ),
                "selected_package_source_axis_lifecycle_label_context_ids": string_list(
                    member.get("source_axis_lifecycle_label_context_ids")
                ),
                "selected_package_source_axis_lifecycle_context_attribution_scope": (
                    selected_package_lifecycle_context_attribution_scope(member)
                ),
                "selected_package_source_axis_lifecycle_decision_window_id_samples": (
                    string_list(
                        member.get("source_axis_lifecycle_decision_window_id_samples")
                    )
                ),
                "selected_package_source_axis_lifecycle_bridge_window_transfer_status": (
                    selected_package_lifecycle_window_transfer_status(member)
                ),
                "selected_package_source_materialization_transfer_status": (
                    selected_package_lifecycle_window_transfer_status(member)
                ),
                "selected_package_source_axis_lifecycle_source_window_recoverability_status": text(
                    member.get(
                        "source_axis_lifecycle_source_window_recoverability_status"
                    )
                ),
                "selected_package_source_axis_lifecycle_bridge_window_mismatch_status": text(
                    member.get(
                        "source_axis_lifecycle_bridge_window_mismatch_status"
                    )
                ),
                "selected_package_source_axis_lifecycle_missing_decision_label_count": int(
                    safe_float(
                        member.get(
                            "source_axis_lifecycle_missing_decision_label_count"
                        )
                    )
                ),
                "selected_package_source_axis_lifecycle_pending_created_proxy_only_label_count": int(
                    safe_float(
                        member.get(
                            "source_axis_lifecycle_pending_created_proxy_only_label_count"
                        )
                    )
                ),
                "selected_package_source_axis_lifecycle_exact_decision_time_recovered_label_count": int(
                    safe_float(
                        member.get(
                            "source_axis_lifecycle_exact_decision_time_recovered_label_count"
                        )
                    )
                ),
                "selected_package_source_axis_lifecycle_bridge_decision_window_overlap_count": int(
                    safe_float(
                        member.get(
                            "source_axis_lifecycle_bridge_decision_window_overlap_count"
                        )
                    )
                ),
                "selected_package_source_axis_lifecycle_bridge_decision_window_overlap_samples": (
                    string_list(
                        member.get(
                            "source_axis_lifecycle_bridge_decision_window_overlap_samples"
                        )
                    )
                ),
                "selected_package_replay_source_materialization_status": (
                    selected_package_replay_source_materialization_status(
                        member,
                        package_role=package_role,
                    )
                ),
                "selected_package_lifecycle_label_context_status": (
                    selected_package_lifecycle_label_context_status(
                        member,
                        package_role=package_role,
                    )
                ),
                "pending_lifecycle_v4_state_groups": string_list(
                    member.get("pending_lifecycle_v4_state_groups")
                ),
                "fillability_label_families": string_list(
                    member.get("fillability_label_families")
                ),
                "fill_no_fill_labels": string_list(member.get("fill_no_fill_labels")),
                "selected_package_replay_bridge_candidate_id_samples": string_list(
                    member.get("selected_package_replay_bridge_candidate_id_samples")
                )[:8],
                "selected_package_replay_bridge_decision_window_id_samples": string_list(
                    member.get("selected_package_replay_bridge_decision_window_id_samples")
                )[:8],
                "candidate_id_carried_to_member": member.get("candidate_id_carried_to_member"),
                "decision_window_id_carried_to_member": member.get(
                    "decision_window_id_carried_to_member"
                ),
                "row_bound_selected_package_source_materialized": not (
                    executable_axis_missing_row_bound_selected_package_source(
                        member,
                        package_role=package_role,
                    )
                ),
            }
            axis_row = {
                "schema": "gtos.final_moonshot.denominator_to_deployment.source_bound_to_executed_parity.v1",
                "generated_utc": generated,
                "row_type": "source_member_axis_to_executable_replay",
                "broad_replay_observation_status": observation_status,
                "join_method": (
                    "candidate_bound_member_axis_identity_then_tuple_overlap"
                    if profile_axis_identity_candidates
                    else "sleeve_member_axis_overlap"
                ),
                "candidate_bound_member_axis_identity_match_count": len(
                    profile_axis_identity_candidates
                ),
                "exact_package_candidate_match_count": len(set(exact_matches)),
                "exact_package_candidate_instance_key_samples": sorted(
                    set(exact_matches)
                )[:8],
                "exact_package_candidate_id_samples": sorted(
                    set(exact_match_candidate_ids)
                )[:8],
                "framework": member.get("framework"),
                "origin_family": member.get("origin_family"),
                "side": axis_side,
                "symbol": axis_symbol,
                "session_bucket": member.get("session_bucket"),
                **axis_identity,
                **mismatch,
                "candidate_generated": generated_label == "candidate_generated",
                "broad_replay_candidate_generated": (
                    summary["candidate_generated_count"] > 0
                ),
                "selected_package_bridge_candidate_generated": (
                    generated_label
                    == "candidate_generated_via_selected_package_bridge"
                ),
                "candidate_generation_label": generated_label,
                "candidate_generation_observation_scope": (
                    "selected_broad_replay_window_not_full_available_universe"
                ),
                "candidate_trace_row_count": len(trace_rows),
                "candidate_trace_sample_count": min(len(trace_rows), trace_sample_limit),
                "candidate_trace_samples_truncated": len(trace_rows) > trace_sample_limit,
                "candidate_execution_trace_samples": trace_rows[:trace_sample_limit],
                **representative_candidate_quality_fields(trace_rows),
                "execution_leakage_label": label,
                "deviation_reason": label,
                "broad_replay_profile": profile_name,
                **summary,
                "broker_live_authority": False,
                "final_selection_claim": False,
                "actual_r_evidence_class": (
                    "simulated_account_research_not_broker_real_cash_or_lifecycle_truth"
                ),
            }
            axis_rows.append(axis_row)
            trace_common = {
                "schema": "gtos.final_moonshot.denominator_to_deployment.source_bound_to_executed_parity.v1",
                "generated_utc": generated,
                "row_type": "source_member_axis_candidate_execution_trace",
                "broad_replay_observation_status": observation_status,
                "join_method": "sleeve_member_axis_overlap",
                "broad_replay_profile": profile_name,
                "execution_leakage_label": label,
                "broker_live_authority": False,
                "final_selection_claim": False,
                "actual_r_evidence_class": (
                    "simulated_account_research_not_broker_real_cash_or_lifecycle_truth"
                ),
                **axis_identity,
            }
            if trace_rows:
                for trace in trace_rows:
                    trace_row = {
                        **trace_common,
                        **trace,
                        "candidate_generation_label": "candidate_generated",
                    }
                    if candidate_trace_sink is None:
                        candidate_trace_rows.append(trace_row)
                    else:
                        candidate_trace_sink(trace_row)
                    candidate_trace_row_count += 1
            else:
                trace_row = {
                    **trace_common,
                    "candidate_generated": False,
                    "candidate_generation_label": "candidate_not_generated",
                    "candidate_id": "",
                    "decision_time_utc": "",
                    "stable_decision_window_id": "",
                    "selector_action": "",
                    "selector_reason": "",
                    "scheduler_rank": None,
                    "scheduler_selected": False,
                    "risk_decision_counts": {},
                    "order_policy_counts": {},
                    "order_status_counts": {},
                    "fillability_status_counts": {},
                    "candidate_lifecycle_action": "",
                    "risk_lifecycle_action_counts": {},
                    "exit_result_counts": {},
                    "actual_r": 0.0,
                    "candidate_generation_observation_scope": (
                        "selected_broad_replay_window_not_full_available_universe"
                    ),
                    **mismatch,
                    "deviation_reason": label,
                }
                if candidate_trace_sink is None:
                    candidate_trace_rows.append(trace_row)
                else:
                    candidate_trace_sink(trace_row)
                candidate_trace_row_count += 1

    parity_rows = axis_rows + candidate_trace_rows
    bucket_rows = build_leakage_buckets(axis_rows, generated)
    broad_summary = read_json(BROAD_SUMMARY_PATH)
    broad_candidate_expanded_index_count = len(candidates)
    broad_candidate_declared_count = broad_summary_declared_candidate_rows(
        broad_summary
    )
    broad_candidate_physical_count, broad_candidate_physical_count_source = (
        broad_physical_candidate_ledger_rows(broad_summary)
    )
    summary = build_parity_summary(
        parity_rows=axis_rows,
        bucket_rows=bucket_rows,
        observation_status=observation_status,
        exact_package_candidate_rows=exact_package_candidate_rows,
        exact_package_candidate_ids=len(exact_package_candidate_ids),
        package_authority_order_geometry_status_counts=top_counter(
            package_authority_order_geometry_status_counts,
            limit=8,
        ),
        broad_candidate_count=(
            broad_candidate_declared_count
            if broad_candidate_declared_count is not None
            else broad_candidate_physical_count
        ),
        broad_candidate_physical_count=broad_candidate_physical_count,
        broad_candidate_physical_count_source=broad_candidate_physical_count_source,
        broad_candidate_expanded_index_count=broad_candidate_expanded_index_count,
        profiles=profiles,
        candidate_instance_projection_summary=(
            candidate_instance_projection_summary
        ),
    )
    summary["source_member_axis_parity_rows"] = len(axis_rows)
    summary["candidate_execution_trace_ledger_rows"] = candidate_trace_row_count
    summary["parity_ledger_rows"] = len(axis_rows) + candidate_trace_row_count
    summary["parity_ledger_row_type_counts"] = {
        "source_member_axis_candidate_execution_trace": candidate_trace_row_count,
        "source_member_axis_to_executable_replay": len(axis_rows),
    }
    summary["candidate_instance_parity_projection"] = (
        candidate_instance_projection_summary
    )
    summary["candidate_instance_parity_projection_rows"] = int(
        candidate_instance_projection_summary.get("row_count") or 0
    )
    summary.setdefault("artifacts", {})[
        "candidate_instance_parity_projection_ledger"
    ] = str(CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH)
    return parity_rows, bucket_rows, candidate_instance_projection_rows, summary


def build_parity_rows() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Compatibility wrapper for existing callers that consume three artifacts."""

    parity_rows, bucket_rows, _projection_rows, summary = (
        _build_parity_rows_and_projection()
    )
    return parity_rows, bucket_rows, summary


def bucket_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("broad_replay_profile"),
        row.get("sleeve_type"),
        row.get("package_role"),
        row.get("framework"),
        row.get("origin_family"),
        row.get("side"),
        row.get("symbol"),
        row.get("session_bucket"),
        row.get("execution_leakage_label"),
    )


def build_leakage_buckets(rows: list[dict[str, Any]], generated: str) -> list[dict[str, Any]]:
    buckets: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = bucket_key(row)
        bucket = buckets.setdefault(
            key,
            {
                "schema": "gtos.final_moonshot.denominator_to_deployment.execution_leakage_bucket.v1",
                "generated_utc": generated,
                "row_type": "execution_leakage_bucket",
                "broad_replay_observation_status": row.get("broad_replay_observation_status"),
                "broad_replay_profile": row.get("broad_replay_profile"),
                "sleeve_type": row.get("sleeve_type"),
                "package_role": row.get("package_role"),
                "framework": row.get("framework"),
                "origin_family": row.get("origin_family"),
                "side": row.get("side"),
                "symbol": row.get("symbol"),
                "session_bucket": row.get("session_bucket"),
                "execution_leakage_label": row.get("execution_leakage_label"),
                "rows": 0,
                "candidate_generated_count": 0,
                "candidate_not_generated_count": 0,
                "broad_replay_candidate_generated_count": 0,
                "selected_package_bridge_candidate_generated_count": 0,
                "selected_package_replay_bridge_candidate_rows": 0,
                "candidate_trace_row_count": 0,
                "unique_decision_windows": 0,
                "scheduler_option_present_count": 0,
                "scheduler_rank_min": None,
                "scheduler_score_max": None,
                "scheduler_selected_count": 0,
                "order_present_count": 0,
                "trade_count": 0,
                "missed_count": 0,
                "actual_r_sum": 0.0,
                "gross_r_sum": 0.0,
                "final_r_sum": 0.0,
                "cash_pnl_sum": 0.0,
                "risk_cash_sum": 0.0,
                "risk_pct_sum": 0.0,
                "missed_net_proxy_r_sum": 0.0,
                "missed_positive_net_r_sum": 0.0,
                "missed_negative_net_r_sum": 0.0,
                "blocked_counterfactual_missed_count": 0,
                "blocked_counterfactual_missed_net_proxy_r_sum": 0.0,
                "blocked_counterfactual_missed_positive_net_r_sum": 0.0,
                "blocked_counterfactual_missed_negative_net_r_sum": 0.0,
                "source_combined_signal_r_sum": 0.0,
                "diagnostic_package_source_bound_r_sum": 0.0,
                "diagnostic_source_bound_r_sum": 0.0,
                "effective_package_source_bound_r_sum": 0.0,
                "effective_source_bound_r_sum": 0.0,
                "package_source_bound_r_sum": 0.0,
                "source_bound_r_sum": 0.0,
                "source_bound_r_additive_allowed": False,
                "selector_action_counts": Counter(),
                "pretrade_cost_packet_status_counts": Counter(),
                "pretrade_cost_refusal_reason_counts": Counter(),
                "cost_source_gap_status_counts": Counter(),
                "scheduler_action_class_counts": Counter(),
                "scheduler_decision_status_counts": Counter(),
                "scheduler_option_reason_counts": Counter(),
                "risk_decision_counts": Counter(),
                "risk_decision_reason_counts": Counter(),
                "order_status_counts": Counter(),
                "order_policy_counts": Counter(),
                "order_architecture_counts": Counter(),
                "order_type_counts": Counter(),
                "fill_status_counts": Counter(),
                "counterfactual_fill_status_counts": Counter(),
                "fillability_status_counts": Counter(),
                "candidate_lifecycle_action_counts": Counter(),
                "risk_lifecycle_action_counts": Counter(),
                "risk_lifecycle_permitted_counts": Counter(),
                "terminal_outcome_counts": Counter(),
                "miss_reason_counts": Counter(),
                "close_reason_counts": Counter(),
                "exit_result_counts": Counter(),
                "broker_live_authority": False,
                "final_selection_claim": False,
            },
        )
        bucket["rows"] += 1
        if axis_candidate_generated(row):
            bucket["candidate_generated_count"] += 1
        else:
            bucket["candidate_not_generated_count"] += 1
        if row.get("broad_replay_candidate_generated") is True:
            bucket["broad_replay_candidate_generated_count"] += 1
        if row.get("selected_package_bridge_candidate_generated") is True:
            bucket["selected_package_bridge_candidate_generated_count"] += 1
        bucket["selected_package_replay_bridge_candidate_rows"] += int(
            row.get("selected_package_replay_bridge_candidate_rows") or 0
        )
        bucket["candidate_trace_row_count"] += int(row.get("candidate_trace_row_count") or 0)
        bucket["unique_decision_windows"] += int(row.get("unique_decision_windows") or 0)
        bucket["scheduler_option_present_count"] += int(
            row.get("scheduler_option_present_count") or 0
        )
        if row.get("scheduler_rank_min") is not None:
            rank = int(row.get("scheduler_rank_min"))
            bucket["scheduler_rank_min"] = (
                rank
                if bucket["scheduler_rank_min"] is None
                else min(int(bucket["scheduler_rank_min"]), rank)
            )
        if row.get("scheduler_score_max") is not None:
            score = safe_float(row.get("scheduler_score_max"))
            bucket["scheduler_score_max"] = (
                score
                if bucket["scheduler_score_max"] is None
                else max(safe_float(bucket["scheduler_score_max"]), score)
            )
        bucket["scheduler_selected_count"] += int(row.get("scorecard_selected_count") or 0)
        bucket["order_present_count"] += int(row.get("order_present_count") or 0)
        bucket["trade_count"] += int(row.get("trade_count") or 0)
        bucket["missed_count"] += int(row.get("missed_count") or 0)
        bucket["blocked_counterfactual_missed_count"] += int(
            row.get("blocked_counterfactual_missed_count") or 0
        )
        for target, source in (
            ("actual_r_sum", "actual_r_sum"),
            ("gross_r_sum", "gross_r_sum"),
            ("final_r_sum", "final_r_sum"),
            ("cash_pnl_sum", "cash_pnl_sum"),
            ("risk_cash_sum", "risk_cash_sum"),
            ("risk_pct_sum", "risk_pct_sum"),
            ("missed_net_proxy_r_sum", "missed_net_proxy_r_sum"),
            ("missed_positive_net_r_sum", "missed_positive_net_r_sum"),
            ("missed_negative_net_r_sum", "missed_negative_net_r_sum"),
            (
                "blocked_counterfactual_missed_net_proxy_r_sum",
                "blocked_counterfactual_missed_net_proxy_r_sum",
            ),
            (
                "blocked_counterfactual_missed_positive_net_r_sum",
                "blocked_counterfactual_missed_positive_net_r_sum",
            ),
            (
                "blocked_counterfactual_missed_negative_net_r_sum",
                "blocked_counterfactual_missed_negative_net_r_sum",
            ),
            ("source_combined_signal_r_sum", "combined_source_bound_signal_r"),
            ("diagnostic_package_source_bound_r_sum", "diagnostic_package_source_bound_r"),
            ("diagnostic_source_bound_r_sum", "diagnostic_source_bound_r"),
            ("effective_package_source_bound_r_sum", "effective_package_source_bound_r"),
            ("effective_source_bound_r_sum", "effective_source_bound_r"),
            ("package_source_bound_r_sum", "package_source_bound_r"),
            ("source_bound_r_sum", "source_bound_r"),
        ):
            bucket[target] = add(bucket[target], row.get(source))
        bucket["selector_action_counts"].update(row.get("selector_action_counts") or {})
        bucket["pretrade_cost_packet_status_counts"].update(
            row.get("pretrade_cost_packet_status_counts") or {}
        )
        bucket["pretrade_cost_refusal_reason_counts"].update(
            row.get("pretrade_cost_refusal_reason_counts") or {}
        )
        bucket["cost_source_gap_status_counts"].update(
            row.get("cost_source_gap_status_counts") or {}
        )
        bucket["scheduler_action_class_counts"].update(
            row.get("scheduler_action_class_counts") or {}
        )
        bucket["scheduler_decision_status_counts"].update(
            row.get("scheduler_decision_status_counts") or {}
        )
        bucket["scheduler_option_reason_counts"].update(
            row.get("scheduler_option_reason_counts") or {}
        )
        bucket["risk_decision_counts"].update(row.get("risk_decision_counts") or {})
        bucket["risk_decision_reason_counts"].update(
            row.get("risk_decision_reason_counts") or {}
        )
        bucket["order_status_counts"].update(row.get("order_status_counts") or {})
        bucket["order_policy_counts"].update(row.get("order_policy_counts") or {})
        bucket["order_architecture_counts"].update(
            row.get("order_architecture_counts") or {}
        )
        bucket["order_type_counts"].update(row.get("order_type_counts") or {})
        bucket["fill_status_counts"].update(row.get("fill_status_counts") or {})
        bucket["counterfactual_fill_status_counts"].update(
            row.get("counterfactual_fill_status_counts") or {}
        )
        bucket["fillability_status_counts"].update(row.get("fillability_status_counts") or {})
        bucket["candidate_lifecycle_action_counts"].update(
            row.get("candidate_lifecycle_action_counts") or {}
        )
        bucket["risk_lifecycle_action_counts"].update(
            row.get("risk_lifecycle_action_counts") or {}
        )
        bucket["risk_lifecycle_permitted_counts"].update(
            row.get("risk_lifecycle_permitted_counts") or {}
        )
        bucket["terminal_outcome_counts"].update(row.get("terminal_outcome_counts") or {})
        bucket["miss_reason_counts"].update(row.get("miss_reason_counts") or {})
        bucket["close_reason_counts"].update(row.get("close_reason_counts") or {})
        bucket["exit_result_counts"].update(row.get("exit_result_counts") or {})

    out: list[dict[str, Any]] = []
    for bucket in buckets.values():
        for key in (
            "selector_action_counts",
            "pretrade_cost_packet_status_counts",
            "pretrade_cost_refusal_reason_counts",
            "cost_source_gap_status_counts",
            "scheduler_action_class_counts",
            "scheduler_decision_status_counts",
            "scheduler_option_reason_counts",
            "risk_decision_counts",
            "risk_decision_reason_counts",
            "order_status_counts",
            "order_policy_counts",
            "order_architecture_counts",
            "order_type_counts",
            "fill_status_counts",
            "counterfactual_fill_status_counts",
            "fillability_status_counts",
            "candidate_lifecycle_action_counts",
            "risk_lifecycle_action_counts",
            "risk_lifecycle_permitted_counts",
            "terminal_outcome_counts",
            "miss_reason_counts",
            "close_reason_counts",
            "exit_result_counts",
        ):
            bucket[key] = counter_dict(bucket[key])
        out.append(bucket)
    return sorted(
        out,
        key=lambda row: (
            row["broad_replay_profile"],
            row["execution_leakage_label"],
            row["sleeve_type"] or "",
            row["symbol"] or "",
            row["session_bucket"] or "",
        ),
    )


def repair_stage_for_label(label: str) -> str:
    if (
        label
        == "executable_axis_missing_row_bound_selected_package_replay_candidate_or_decision_window"
    ):
        return "selected_package_replay_source_materialization"
    if label in {
        "selected_package_lifecycle_context_without_current_replay_source_materialization",
        "selected_package_replay_source_not_materialized_no_hydrated_selector_candidate_rows",
    }:
        return "selected_package_replay_source_materialization"
    if (
        label
        == "executable_axis_candidate_namespace_materialized_no_lifecycle_label_context"
    ):
        return "lifecycle_label_context_materialization"
    if label == "selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap":
        return "lifecycle_label_context_materialization"
    if (
        label
        == "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_not_stable_window_matched"
    ):
        return "selected_package_bridge_stable_window_lifecycle_context_materialization"
    if label in {
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_bridge_window_overlap",
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_source_window_missing",
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_bridge_window_missing",
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_bridge_window_mismatch",
        "source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_bridge_window_overlap_denominator_authority_closed",
        "source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_source_window_missing",
        "source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_bridge_window_missing",
        "source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_bridge_window_mismatch",
        "source_axis_selected_package_bridge_materialized_window_lifecycle_label_context_denominator_authority_closed",
    }:
        return "selected_package_bridge_stable_window_lifecycle_context_materialization"
    if label.startswith(
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_source_window_missing_"
    ):
        return "selected_package_bridge_stable_window_lifecycle_context_materialization"
    if label.startswith(
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_bridge_window_mismatch_"
    ):
        return "selected_package_bridge_stable_window_lifecycle_context_materialization"
    if label.startswith(
        "source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_source_window_missing_"
    ):
        return "selected_package_bridge_stable_window_lifecycle_context_materialization"
    if label.startswith(
        "source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_bridge_window_mismatch_"
    ):
        return "selected_package_bridge_stable_window_lifecycle_context_materialization"
    if (
        label
        == "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_aggregate_only_producer_gap"
    ):
        return "selected_package_bridge_lifecycle_context_materialization"
    if label.startswith("source_axis_selected_package_bridge_materialized"):
        return "selected_package_bridge_lifecycle_context_materialization"
    if label == "candidate_not_generated" or label.startswith(
        "candidate_generation_namespace_mismatch:"
    ):
        return "candidate_generation_parity"
    if label == "executable_axis_not_observed_in_selected_replay_window":
        return "replay_coverage_expansion"
    if label == "non_admission_failure_feature_axis_no_trade_candidate_expected":
        return "non_admission_source_bound_accounting"
    if label == "source_required_hold_not_executable_without_source":
        return "source_required_hold_gap"
    if label == "redesign_repair_axis_not_executable_generator_authority":
        return "redesign_repair_materialization"
    if label.startswith("candidate_generated_selector_reject_downstream_execution_"):
        return "selector_admission_calibration"
    if "scheduler" in label or "not_scheduler" in label:
        return "scheduler_ranking_reallocation"
    if "selector" in label:
        return "selector_admission_calibration"
    if "cost" in label:
        return "cost_authority_non_executable"
    if "risk" in label or "guard" in label:
        return "risk_guard_reallocation"
    if "order" in label or "fill" in label:
        return "order_fillability_fallback"
    if "lifecycle" in label or "cancel" in label or "expire" in label:
        return "lifecycle_cancel_replace_expiry"
    if "negative" in label or "positive" in label or "executed" in label:
        return "exit_trade_result_quality"
    return "unclassified_execution_parity"


def build_execution_leakage_repair_plan(
    *,
    summary: Mapping[str, Any],
    bucket_rows: list[dict[str, Any]],
    observation_status: str,
) -> dict[str, Any]:
    stage_rows: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "bucket_rows": 0,
            "axis_rows": 0,
            "candidate_trace_rows": 0,
            "diagnostic_source_bound_r_sum": 0.0,
            "source_bound_r_sum": 0.0,
            "actual_r_sum": 0.0,
            "missed_net_proxy_r_sum": 0.0,
            "blocked_counterfactual_missed_net_proxy_r_sum": 0.0,
            "labels": Counter(),
            "profiles": Counter(),
        }
    )
    for row in bucket_rows:
        label = text(row.get("execution_leakage_label"), "unknown")
        stage = repair_stage_for_label(label)
        payload = stage_rows[stage]
        payload["bucket_rows"] += 1
        payload["axis_rows"] += int(row.get("rows") or 0)
        payload["candidate_trace_rows"] += int(row.get("candidate_trace_row_count") or 0)
        payload["diagnostic_source_bound_r_sum"] = add(
            payload["diagnostic_source_bound_r_sum"],
            row.get("diagnostic_source_bound_r_sum"),
        )
        payload["source_bound_r_sum"] = add(
            payload["source_bound_r_sum"], row.get("source_bound_r_sum")
        )
        payload["actual_r_sum"] = add(payload["actual_r_sum"], row.get("actual_r_sum"))
        payload["missed_net_proxy_r_sum"] = add(
            payload["missed_net_proxy_r_sum"], row.get("missed_net_proxy_r_sum")
        )
        payload["blocked_counterfactual_missed_net_proxy_r_sum"] = add(
            payload["blocked_counterfactual_missed_net_proxy_r_sum"],
            row.get("blocked_counterfactual_missed_net_proxy_r_sum"),
        )
        payload["labels"][label] += int(row.get("rows") or 0)
        payload["profiles"][text(row.get("broad_replay_profile"), "unknown")] += int(
            row.get("rows") or 0
        )

    action_catalog = {
        "candidate_generation_parity": {
            "priority": 10,
            "repair_action": "repair_candidate_generation_namespace_and_field_parity_for_source_bound_axes",
            "owned_components": [
                "src/components/broader_origin_generators.py",
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
            ],
            "acceptance_gate": "source-bound high-R axes become broad replay candidates or carry explicit non-executable source-gap labels",
        },
        "selected_package_replay_source_materialization": {
            "priority": 12,
            "repair_action": "materialize_row_bound_selected_package_replay_candidate_or_decision_window_sources_before_treating_member_axis_overlap_as_executable_generator_failure",
            "owned_components": [
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py",
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py",
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
            ],
            "acceptance_gate": "every executable source-bound axis either carries exact candidate_id/decision_window_id selected-package replay source, becomes a broad replay candidate, or remains explicitly non-executable as a materialization gap",
        },
        "lifecycle_label_context_materialization": {
            "priority": 13,
            "repair_action": "materialize_lifecycle_label_context_for_axes_that_already_have_candidate_namespace_before_counting_them_as_selected_package_source_gaps",
            "owned_components": [
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py",
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py",
            ],
            "acceptance_gate": "candidate-namespace-materialized axes remain separate from missing selected-package row-bound source and require lifecycle-label context rerun or explicit source-gap status",
        },
        "selected_package_bridge_stable_window_lifecycle_context_materialization": {
            "priority": 14,
            "repair_action": "materialize_stable_window_lifecycle_label_context_for_selected_package_bridge_candidates_that_have_axis_level_lifecycle_context_before_counting_them_as_no-context rows",
            "owned_components": [
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py",
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py",
            ],
            "acceptance_gate": "selected-package bridge axes with axis-level lifecycle context are reported as stable-window context gaps, not no-lifecycle-context rows",
        },
        "selector_admission_calibration": {
            "priority": 20,
            "repair_action": "calibrate_selector_admission_so_package_admission_sleeves_override_generic_router_refusal_as_reduce_risk_not_hard_reject",
            "owned_components": ["src/components/selector_v4.py"],
            "acceptance_gate": "selector dynamic-router refusal no longer hard-blocks package-admitted source-bound candidates",
        },
        "scheduler_ranking_reallocation": {
            "priority": 30,
            "repair_action": "rank_and_reallocate_over_risk_admitted_scheduler_options_with_predecision_fillability_weight_before_zero_trade_or_flat_skip",
            "owned_components": [
                "src/research/moonshot_scheduler_v4_best_trade_allocator.py",
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
            ],
            "acceptance_gate": "scheduler-selected risk-rejected, zero-trade, and expired-unfilled opportunity buckets fall because fillable package candidates outrank unreachable resting limits while holdout net R does not degrade",
        },
        "risk_guard_reallocation": {
            "priority": 40,
            "repair_action": "use_replay_conversion_accounting_for_dynamic_budget_attempt_spend_plus_package_admission_reserve_release_micro_allocation_and_quality_gated_order_cap_release_before_flat_skip",
            "owned_components": [
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
                "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py",
            ],
            "acceptance_gate": "risk-finalizer zero-trade buckets fall because expired/unfilled accepted attempts no longer consume replay drawdown budget and package-admitted high-quality candidates can use replay-only reserve release, micro allocation, and order-cap release inside existing drawdown/portfolio/cluster caps; blocked losses and blocked winners remain reported separately",
        },
        "order_fillability_fallback": {
            "priority": 50,
            "repair_action": "execute_replay_only_limit_first_guarded_market_fallback_with_cost_and_fillability_metadata",
            "owned_components": [
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
                "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py",
            ],
            "acceptance_gate": "expired-unfilled guarded-market eligible rows become fallback-filled or explicit guard-rejected rows",
        },
        "cost_authority_non_executable": {
            "priority": 55,
            "repair_action": "preserve_broker_calibrated_cost_refusal_as_non_executable_and_reallocate_to_next_cost_passed_candidate_without_executing_refused_cost_rows",
            "owned_components": [
                "src/components/broker_net_cost_engine.py",
                "src/components/selector_v4.py",
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
            ],
            "acceptance_gate": "cost-refused rows are not treated as selector bugs, never execute as filled trades, and scheduler/risk can reallocate only to broker-cost-passed candidates",
        },
        "lifecycle_cancel_replace_expiry": {
            "priority": 60,
            "repair_action": "commit_pending_cancel_replace_only_after_replacement_risk_and_execution_admission",
            "owned_components": ["src/research_infra/v4_timewarp_simulated_live_research_loop.py"],
            "acceptance_gate": "no cancelled_replaced_by_scheduler_v4 row references a risk-rejected or execution-blocked replacement",
        },
        "exit_trade_result_quality": {
            "priority": 70,
            "repair_action": "separate_raw_exit_damage_from_guarded_policy_and_demote_unproven_profit_harvest_overlays_until causal proof exists",
            "owned_components": ["src/research_infra/v4_timewarp_simulated_live_research_loop.py"],
            "acceptance_gate": "raw vs guarded vs repaired reports show exit/profit-harvest impact separately from selection and order fillability",
        },
        "unclassified_execution_parity": {
            "priority": 90,
            "repair_action": "classify_remaining_trace_rows_with_exact_deviation_stage_before_promotion",
            "owned_components": [
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py"
            ],
            "acceptance_gate": "no high-R axis remains unclassified without exact source-gap proof",
        },
        "replay_coverage_expansion": {
            "priority": 15,
            "repair_action": "expand_broad_replay_window_or_materialize_compact_universe_replay_before_treating_unobserved_executable_axes_as_generator_failure",
            "owned_components": [
                "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py",
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py",
            ],
            "acceptance_gate": "executable admission axes are observed across a broad enough replay window or remain explicitly coverage-bounded",
        },
        "non_admission_source_bound_accounting": {
            "priority": 80,
            "repair_action": "account_for_avoid_failure_feature_sleeves_as_guard_features_not_trade_candidates",
            "owned_components": [
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py"
            ],
            "acceptance_gate": "avoid/failure-feature sleeves are not counted as missing trade candidates unless they were meant to admit orders",
        },
        "source_required_hold_gap": {
            "priority": 85,
            "repair_action": "preserve_source_required_hold_axes_as_explicit_source_gaps_until_required_evidence_is_available",
            "owned_components": [
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py"
            ],
            "acceptance_gate": "source-required hold axes carry explicit source-gap labels rather than generic generator failure labels",
        },
        "redesign_repair_materialization": {
            "priority": 25,
            "repair_action": "materialize_redesign_repair_axes_as_replay_generators_or_keep_them_out_of_candidate_generation_parity_denominator",
            "owned_components": [
                "src/components/broader_origin_generators.py",
                "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
                "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py",
            ],
            "acceptance_gate": "redesign/repair sleeves either generate executable replay candidates or are reported as design-materialization work, not missing historical candidates",
        },
    }
    actions = []
    for stage, payload in sorted(
        stage_rows.items(),
        key=lambda item: (
            -max(
                abs(safe_float(item[1].get("diagnostic_source_bound_r_sum"))),
                abs(safe_float(item[1].get("source_bound_r_sum"))),
            ),
            action_catalog.get(item[0], {}).get("priority", 999),
            item[0],
        ),
    ):
        catalog = action_catalog.get(stage, action_catalog["unclassified_execution_parity"])
        actions.append(
            {
                "stage": stage,
                "priority": catalog["priority"],
                "repair_action": catalog["repair_action"],
                "acceptance_gate": catalog["acceptance_gate"],
                "owned_components": catalog["owned_components"],
                "observed_bucket_rows": payload["bucket_rows"],
                "observed_axis_rows": payload["axis_rows"],
                "candidate_trace_rows": payload["candidate_trace_rows"],
                "diagnostic_source_bound_r_sum": round(
                    payload["diagnostic_source_bound_r_sum"], 10
                ),
                "source_bound_r_sum": round(payload["source_bound_r_sum"], 10),
                "actual_r_sum": round(payload["actual_r_sum"], 10),
                "missed_net_proxy_r_sum": round(payload["missed_net_proxy_r_sum"], 10),
                "blocked_counterfactual_missed_net_proxy_r_sum": round(
                    payload["blocked_counterfactual_missed_net_proxy_r_sum"], 10
                ),
                "label_counts": counter_dict(payload["labels"]),
                "profile_counts": counter_dict(payload["profiles"]),
                "status": "implemented_this_checkpoint"
                if stage
                in {
                    "risk_guard_reallocation",
                    "scheduler_ranking_reallocation",
                    "order_fillability_fallback",
                    "lifecycle_cancel_replace_expiry",
                }
                else "open_material_leak_or_requires_post_repair_rerun",
            }
        )
    return {
        "schema": "gtos.final_moonshot.execution_leakage_repair_plan.v1",
        "generated_utc": utc_now(),
        "route_id": ROUTE.name,
        "broad_replay_prefix": BROAD_PREFIX,
        "broad_replay_observation_status": observation_status,
        "status": (
            "repairs_implemented_pending_repaired_replay_rerun"
            if observation_status != "completed_broad_replay_summary_present"
            else "repairs_ranked_from_completed_broad_replay"
        ),
        "broker_live_authority": False,
        "final_selection_claim": False,
        "coverage": {
            "source_member_axis_rows": summary.get("source_member_axis_rows"),
            "profile_count": summary.get("profile_count"),
            "parity_ledger_rows": summary.get("parity_ledger_rows"),
            "candidate_execution_trace_ledger_rows": summary.get(
                "candidate_execution_trace_ledger_rows"
            ),
            "source_axis_rows_with_exact_package_candidate_match": summary.get(
                "source_axis_rows_with_exact_package_candidate_match"
            ),
            "broad_candidate_rows_indexed": summary.get("broad_candidate_rows_indexed"),
        },
        "implemented_repairs_this_checkpoint": [
            "dynamic_budget_replay_conversion_accounting_excludes_accepted_attempt_spend",
            "dynamic_budget_package_admission_reserve_release_and_micro_allocation",
            "dynamic_budget_package_quality_gated_order_cap_release",
            "scheduler_predecision_fillability_signal_and_repaired_profile_score_weight",
            "market_state_replay_side_effect_writes_disabled",
            "replay_order_fillability_policy_v1_guarded_market_fallback",
            "pending_replacement_cancel_commit_after_replacement_admission",
        ],
        "repair_actions": actions,
        "acceptance_gates": [
            "every high-R source-bound axis has a generated candidate trace or explicit non-executable source-gap label",
            "selector rejects, scheduler zero-trade, risk/guard blocks, order expiry, lifecycle cancel-replace, and exit damage are reported as separate deviation stages",
            "risk-finalizer zero-trade rows separate scheduler-before-finalizer candidate selection from final risk rejection reasons",
            "guarded-market fallback rows are either filled with conservative extra cost or rejected with a deterministic guard reason",
            "cancel-replace rows never cancel incumbents before replacement risk/execution admission",
            "raw, guarded, and repaired holdout reports improve or identify the next limiting leak with exact row counts",
        ],
        "artifacts": {
            **dict(summary.get("artifacts") or {}),
            "execution_leakage_repair_plan": str(REPAIR_PLAN_PATH),
        },
    }


def build_exact_replay_window_transfer_summary(
    *,
    parity_rows: list[dict[str, Any]],
    profile_metrics: Mapping[str, Mapping[str, Any]],
    candidate_instance_projection_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    broad_summary = read_json(BROAD_SUMMARY_PATH)
    full_available_day_count = int(
        safe_float(broad_summary.get("full_available_configured_day_count"), 0.0)
    )
    selected_day_count = int(safe_float(broad_summary.get("selected_day_count"), 0.0))
    coverage_status = text(broad_summary.get("coverage_status"), "unknown")
    full_universe_behavioral_coverage_claim_allowed = bool(
        full_available_day_count > 0
        and selected_day_count >= full_available_day_count
        and "full" in coverage_status.lower()
        and "bounded" not in coverage_status.lower()
    )
    headline_stats_by_profile: dict[str, Mapping[str, Any]] = {}
    split_profile_stats = broad_summary.get("split_profile_stats")
    if isinstance(split_profile_stats, Sequence) and not isinstance(
        split_profile_stats,
        (str, bytes, bytearray),
    ):
        for row in split_profile_stats:
            if not isinstance(row, Mapping):
                continue
            profile_key = text(row.get("profile"), "")
            if profile_key:
                headline_stats_by_profile[profile_key] = row
    by_profile: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "package_axis_rows_in_parity_scope": 0,
            "package_axes_available_inside_replay_window": 0,
            "source_bound_r_nonzero_package_axes_inside_replay_window": 0,
            "source_bound_r_positive_package_axes_inside_replay_window": 0,
            "package_axes_in_global_diagnostic_surface": 0,
            "candidate_generated_axes_inside_replay_window": 0,
            "scorecard_present_axes_inside_replay_window": 0,
            "scheduler_selected_axes_inside_replay_window": 0,
            "order_present_axes_inside_replay_window": 0,
            "scorecard_or_order_present_axes_inside_replay_window": 0,
            "filled_trade_axes_inside_replay_window": 0,
            "non_additive_executable_gated_source_bound_signal_r_inside_replay_window": 0.0,
            "non_additive_executable_gated_package_source_bound_signal_r_inside_replay_window": 0.0,
            "source_bound_r_available_inside_replay_window": 0.0,
            "package_source_bound_r_available_inside_replay_window": 0.0,
            "diagnostic_global_source_bound_r_sum_not_denominator": 0.0,
            "diagnostic_global_package_source_bound_r_sum_not_denominator": 0.0,
            "axis_attributed_actual_executable_r_inside_replay_window": 0.0,
        }
    )
    for row in parity_rows:
        profile = text(row.get("broad_replay_profile"), "unknown")
        metrics = by_profile[profile]
        source_bound_r = safe_float(row.get("source_bound_r"), 0.0)
        package_source_bound_r = safe_float(row.get("package_source_bound_r"), 0.0)
        effective_source_bound_r = safe_float(row.get("effective_source_bound_r"), 0.0)
        effective_package_source_bound_r = safe_float(
            row.get("effective_package_source_bound_r"),
            0.0,
        )
        diagnostic_source_bound_r = safe_float(row.get("diagnostic_source_bound_r"), 0.0)
        diagnostic_package_source_bound_r = safe_float(
            row.get("diagnostic_package_source_bound_r"),
            0.0,
        )
        generated_axis = axis_candidate_generated(row)
        scorecard_axis = int(row.get("scheduler_option_present_count") or 0) > 0
        selected_axis = int(row.get("scorecard_selected_count") or 0) > 0
        order_axis = int(row.get("order_present_count") or 0) > 0
        trade_axis = int(row.get("trade_count") or 0) > 0
        window_axis_nonzero = any(
            abs(value) > 1e-12
            for value in (
                source_bound_r,
                package_source_bound_r,
                effective_source_bound_r,
                effective_package_source_bound_r,
            )
        )
        window_axis_positive = any(
            value > 1e-12
            for value in (
                source_bound_r,
                package_source_bound_r,
                effective_source_bound_r,
                effective_package_source_bound_r,
            )
        )
        diagnostic_axis_visible = any(
            abs(value) > 1e-12
            for value in (
                diagnostic_source_bound_r,
                diagnostic_package_source_bound_r,
            )
        )
        metrics["package_axis_rows_in_parity_scope"] += 1
        metrics["package_axes_available_inside_replay_window"] += 1
        if window_axis_nonzero:
            metrics["source_bound_r_nonzero_package_axes_inside_replay_window"] += 1
        if window_axis_positive:
            metrics["source_bound_r_positive_package_axes_inside_replay_window"] += 1
        if diagnostic_axis_visible:
            metrics["package_axes_in_global_diagnostic_surface"] += 1
        if generated_axis:
            metrics["candidate_generated_axes_inside_replay_window"] += 1
        if scorecard_axis:
            metrics["scorecard_present_axes_inside_replay_window"] += 1
        if selected_axis:
            metrics["scheduler_selected_axes_inside_replay_window"] += 1
        if order_axis:
            metrics["order_present_axes_inside_replay_window"] += 1
        if scorecard_axis or order_axis:
            metrics["scorecard_or_order_present_axes_inside_replay_window"] += 1
        if trade_axis:
            metrics["filled_trade_axes_inside_replay_window"] += 1
        metrics["source_bound_r_available_inside_replay_window"] = add(
            metrics["source_bound_r_available_inside_replay_window"],
            source_bound_r,
        )
        metrics[
            "non_additive_executable_gated_source_bound_signal_r_inside_replay_window"
        ] = add(
            metrics[
                "non_additive_executable_gated_source_bound_signal_r_inside_replay_window"
            ],
            source_bound_r,
        )
        metrics["package_source_bound_r_available_inside_replay_window"] = add(
            metrics["package_source_bound_r_available_inside_replay_window"],
            package_source_bound_r,
        )
        metrics[
            "non_additive_executable_gated_package_source_bound_signal_r_inside_replay_window"
        ] = add(
            metrics[
                "non_additive_executable_gated_package_source_bound_signal_r_inside_replay_window"
            ],
            package_source_bound_r,
        )
        metrics["diagnostic_global_source_bound_r_sum_not_denominator"] = add(
            metrics["diagnostic_global_source_bound_r_sum_not_denominator"],
            diagnostic_source_bound_r,
        )
        metrics[
            "diagnostic_global_package_source_bound_r_sum_not_denominator"
        ] = add(
            metrics["diagnostic_global_package_source_bound_r_sum_not_denominator"],
            diagnostic_package_source_bound_r,
        )
        metrics["axis_attributed_actual_executable_r_inside_replay_window"] = add(
            metrics["axis_attributed_actual_executable_r_inside_replay_window"],
            row.get("actual_r_sum"),
        )

    serializable: dict[str, dict[str, Any]] = {}
    projection_profile_stages = (
        (candidate_instance_projection_summary or {}).get(
            "profile_stage_presence_counts"
        )
        or {}
    )
    for profile, metrics in sorted(by_profile.items()):
        output = dict(metrics)
        profile_metric = profile_metrics.get(profile) or {}
        profile_projection_stages = projection_profile_stages.get(profile) or {}
        axis_selected_count = int(
            profile_metric.get("scorecard_selected_count") or 0
        )
        axis_order_count = int(
            profile_metric.get("order_present_count") or 0
        )
        axis_trade_count = int(
            profile_metric.get("trade_count") or 0
        )
        output[
            "axis_attributed_scorecard_selected_count_inside_replay_window"
        ] = axis_selected_count
        output[
            "axis_attributed_order_present_count_inside_replay_window"
        ] = axis_order_count
        output["axis_attributed_trade_count_inside_replay_window"] = (
            axis_trade_count
        )
        output["scorecard_selected_count_inside_replay_window"] = int(
            profile_projection_stages.get("scheduler_selected")
            if "scheduler_selected" in profile_projection_stages
            else axis_selected_count
        )
        output["order_present_count_inside_replay_window"] = int(
            profile_projection_stages.get("order")
            if "order" in profile_projection_stages
            else axis_order_count
        )
        output["trade_count_inside_replay_window"] = int(
            profile_projection_stages.get("trade")
            if "trade" in profile_projection_stages
            else profile_metric.get("unique_trade_candidate_count")
            if profile_metric.get("unique_trade_candidate_count") is not None
            else axis_trade_count
        )
        output["candidate_instance_rows_inside_replay_window"] = int(
            profile_projection_stages.get("candidate") or 0
        )
        output[
            "scorecard_present_candidate_instance_rows_inside_replay_window"
        ] = int(profile_projection_stages.get("scorecard") or 0)
        output[
            "scheduler_selected_candidate_instance_rows_inside_replay_window"
        ] = int(
            profile_projection_stages.get("scheduler_selected")
            if "scheduler_selected" in profile_projection_stages
            else axis_selected_count
        )
        output["order_present_candidate_instance_rows_inside_replay_window"] = int(
            profile_projection_stages.get("order")
            if "order" in profile_projection_stages
            else axis_order_count
        )
        output["filled_candidate_instance_rows_inside_replay_window"] = int(
            profile_projection_stages.get("trade")
            if "trade" in profile_projection_stages
            else axis_trade_count
        )
        output["missed_candidate_instance_rows_inside_replay_window"] = int(
            profile_projection_stages.get("missed") or 0
        )
        output["candidate_instance_count_authority"] = (
            "candidate_instance_parity_projection_exact_unique"
            if profile_projection_stages
            else "axis_attribution_fallback_projection_profile_counts_unavailable"
        )
        output["actual_executable_r_inside_replay_window"] = safe_float(
            profile_metric.get("unique_actual_r_sum"),
            safe_float(profile_metric.get("actual_r_sum"), 0.0),
        )
        output["gross_executable_r_inside_replay_window"] = safe_float(
            profile_metric.get("unique_gross_r_sum"),
            safe_float(profile_metric.get("gross_r_sum"), 0.0),
        )
        output["final_executable_r_inside_replay_window"] = safe_float(
            profile_metric.get("unique_final_r_sum"),
            safe_float(profile_metric.get("final_r_sum"), 0.0),
        )
        output["cash_pnl_inside_replay_window"] = safe_float(
            profile_metric.get("unique_cash_pnl_sum"),
            safe_float(profile_metric.get("cash_pnl_sum"), 0.0),
        )
        headline_stats = headline_stats_by_profile.get(profile) or {}
        headline_net_r = (
            safe_float(
                first_present(
                    headline_stats.get("headline_net_r"),
                    headline_stats.get("net_r"),
                    headline_stats.get("all_executed_net_r"),
                ),
                math.nan,
            )
            if headline_stats
            else math.nan
        )
        headline_gross_r = (
            safe_float(
                first_present(
                    headline_stats.get("headline_gross_r"),
                    headline_stats.get("gross_r"),
                ),
                math.nan,
            )
            if headline_stats
            else math.nan
        )
        headline_final_r = (
            safe_float(
                first_present(
                    headline_stats.get("headline_final_r"),
                    headline_stats.get("final_r"),
                ),
                math.nan,
            )
            if headline_stats
            else math.nan
        )
        headline_cash_pnl = (
            safe_float(
                first_present(
                    headline_stats.get("headline_cash_pnl"),
                    headline_stats.get("cash_pnl"),
                ),
                math.nan,
            )
            if headline_stats
            else math.nan
        )
        headline_trade_rows = (
            int(
                safe_float(
                    first_present(
                        headline_stats.get("headline_trade_rows"),
                        headline_stats.get("trade_rows"),
                        headline_stats.get("filled_trade_count"),
                    ),
                    0.0,
                )
            )
            if headline_stats
            else None
        )
        unique_actual_r = safe_float(
            output["actual_executable_r_inside_replay_window"],
            0.0,
        )
        axis_attributed_actual_r = safe_float(
            output["axis_attributed_actual_executable_r_inside_replay_window"],
            0.0,
        )
        headline_vs_unique_delta = (
            round(headline_net_r - unique_actual_r, 10)
            if math.isfinite(headline_net_r)
            else None
        )
        headline_vs_axis_delta = (
            round(headline_net_r - axis_attributed_actual_r, 10)
            if math.isfinite(headline_net_r)
            else None
        )
        unique_vs_axis_delta = round(unique_actual_r - axis_attributed_actual_r, 10)
        if not headline_stats:
            reconciliation_status = "headline_replay_summary_missing"
        elif (
            abs(headline_vs_unique_delta or 0.0) <= 1e-8
            and abs(headline_vs_axis_delta or 0.0) <= 1e-8
        ):
            reconciliation_status = "headline_unique_axis_r_aligned"
        else:
            reconciliation_status = "headline_unique_axis_r_surfaces_differ_explicit"
        output["headline_replay_net_r_inside_replay_window"] = (
            round(headline_net_r, 10) if math.isfinite(headline_net_r) else None
        )
        output["headline_replay_gross_r_inside_replay_window"] = (
            round(headline_gross_r, 10) if math.isfinite(headline_gross_r) else None
        )
        output["headline_replay_final_r_inside_replay_window"] = (
            round(headline_final_r, 10) if math.isfinite(headline_final_r) else None
        )
        output["headline_replay_cash_pnl_inside_replay_window"] = (
            round(headline_cash_pnl, 10) if math.isfinite(headline_cash_pnl) else None
        )
        output["headline_replay_trade_rows_inside_replay_window"] = headline_trade_rows
        output["headline_vs_unique_actual_r_delta"] = headline_vs_unique_delta
        output["headline_vs_axis_attributed_actual_r_delta"] = headline_vs_axis_delta
        output["unique_actual_vs_axis_attributed_actual_r_delta"] = (
            unique_vs_axis_delta
        )
        output["r_metric_reconciliation_status"] = reconciliation_status
        output["r_metric_reconciliation_note"] = (
            "headline replay R counts filled replay trades; unique actual R "
            "deduplicates by exact candidate instance inside the profile; axis-attributed "
            "R sums source-bound parity axis attribution. These surfaces must "
            "not be compared as the same denominator unless deltas are zero."
        )
        output["candidate_generated_axis_pct_of_window_package_axes"] = pct(
            output["candidate_generated_axes_inside_replay_window"],
            output["package_axes_available_inside_replay_window"],
        )
        output["scorecard_or_order_axis_pct_of_candidate_generated_axes"] = pct(
            output["scorecard_or_order_present_axes_inside_replay_window"],
            output["candidate_generated_axes_inside_replay_window"],
        )
        output["filled_axis_pct_of_scorecard_or_order_axes"] = pct(
            output["filled_trade_axes_inside_replay_window"],
            output["scorecard_or_order_present_axes_inside_replay_window"],
        )
        output["source_bound_r_additive_allowed"] = False
        output["package_source_bound_r_additive_allowed"] = False
        output["executable_r_to_source_bound_r_percentage_allowed"] = False
        output["source_bound_signal_evidence_class"] = (
            "source_member_axis_overlap_not_additive_exact_execution_r"
        )
        output["source_bound_r_available_inside_replay_window_semantics"] = (
            "legacy_compatibility_alias_for_non_additive_executable_gated_"
            "source_member_axis_signal"
        )
        output[
            "package_source_bound_r_available_inside_replay_window_semantics"
        ] = (
            "legacy_compatibility_alias_for_non_additive_executable_gated_"
            "package_source_member_axis_signal"
        )
        output["actual_executable_r_pct_of_window_source_bound_r"] = None
        output["actual_executable_r_pct_disposition"] = (
            "forbidden_non_additive_source_member_axis_overlap_signal"
        )
        output["diagnostic_global_r_is_denominator"] = False
        serializable[profile] = output

    return {
        "schema": (
            "gtos.final_moonshot.denominator_to_deployment."
            "exact_replay_window_transfer.v1"
        ),
        "broad_replay_prefix": BROAD_PREFIX,
        "date_start": broad_summary.get("date_start"),
        "date_end": broad_summary.get("date_end"),
        "selected_day_count": selected_day_count,
        "days_by_split": broad_summary.get("days_by_split") or {},
        "coverage_status": coverage_status,
        "full_available_configured_day_count": full_available_day_count,
        "full_available_days_by_split": broad_summary.get(
            "full_available_days_by_split"
        )
        or {},
        "denominator_scope": (
            "selected_replay_window_axis_presence_with_non_additive_"
            "source_member_signal_diagnostics"
        ),
        "source_bound_r_additive_allowed": False,
        "package_source_bound_r_additive_allowed": False,
        "executable_r_to_source_bound_r_percentage_allowed": False,
        "source_bound_r_denominator_field": None,
        "package_source_bound_r_denominator_field": None,
        "source_bound_signal_evidence_class": (
            "source_member_axis_overlap_not_additive_exact_execution_r"
        ),
        "legacy_compatibility_non_additive_signal_fields": [
            "source_bound_r_available_inside_replay_window",
            "package_source_bound_r_available_inside_replay_window",
        ],
        "canonical_non_additive_signal_fields": [
            "non_additive_executable_gated_source_bound_signal_r_inside_replay_window",
            "non_additive_executable_gated_package_source_bound_signal_r_inside_replay_window",
        ],
        "diagnostic_reservoir_fields_not_denominator": [
            "diagnostic_source_bound_r",
            "diagnostic_package_source_bound_r",
        ],
        "full_universe_behavioral_coverage_claim_allowed": (
            full_universe_behavioral_coverage_claim_allowed
        ),
        "full_reservoir_transfer_claim_allowed": False,
        "interpretation": (
            "This smoke proves or disproves the local repair; it does not prove "
            "total reservoir conversion."
            if not full_universe_behavioral_coverage_claim_allowed
            else (
                "The selected replay window covers the configured full available "
                "universe, but source member-axis signal remains non-additive and "
                "cannot be used as an executable-R denominator."
            )
        ),
        "profiles": serializable,
    }


def build_parity_summary(
    *,
    parity_rows: list[dict[str, Any]],
    bucket_rows: list[dict[str, Any]],
    observation_status: str,
    exact_package_candidate_rows: int,
    exact_package_candidate_ids: int,
    package_authority_order_geometry_status_counts: dict[str, int],
    broad_candidate_count: int,
    broad_candidate_physical_count: int,
    broad_candidate_physical_count_source: str,
    broad_candidate_expanded_index_count: int,
    profiles: tuple[str, ...],
    candidate_instance_projection_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    profile_counts: dict[str, Counter[str]] = defaultdict(Counter)
    profile_metrics: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "rows": 0,
            "candidate_generated_axis_rows": 0,
            "broad_replay_candidate_generated_axis_rows": 0,
            "selected_package_bridge_candidate_generated_axis_rows": 0,
            "candidate_not_generated_axis_rows": 0,
            "candidate_trace_row_count": 0,
            "scheduler_option_present_count": 0,
            "scorecard_selected_count": 0,
            "order_present_count": 0,
            "trade_count": 0,
            "axis_attributed_trade_count": 0,
            "scorecard_present_axis_rows": 0,
            "scheduler_selected_axis_rows": 0,
            "order_present_axis_rows": 0,
            "filled_trade_axis_rows": 0,
            "unique_trade_candidate_instance_keys": set(),
            "unique_trade_actual_r_by_candidate_instance_key": {},
            "unique_trade_gross_r_by_candidate_instance_key": {},
            "unique_trade_final_r_by_candidate_instance_key": {},
            "unique_trade_cash_pnl_by_candidate_instance_key": {},
            "actual_r_sum": 0.0,
            "axis_attributed_actual_r_sum": 0.0,
            "missed_net_proxy_r_sum": 0.0,
            "missed_positive_net_r_sum": 0.0,
            "missed_negative_net_r_sum": 0.0,
            "blocked_counterfactual_missed_count": 0,
            "blocked_counterfactual_missed_net_proxy_r_sum": 0.0,
            "blocked_counterfactual_missed_positive_net_r_sum": 0.0,
            "blocked_counterfactual_missed_negative_net_r_sum": 0.0,
            "source_combined_signal_r_sum": 0.0,
            "diagnostic_package_source_bound_r_sum": 0.0,
            "diagnostic_source_bound_r_sum": 0.0,
            "effective_package_source_bound_r_sum": 0.0,
            "effective_source_bound_r_sum": 0.0,
            "package_source_bound_r_sum": 0.0,
            "source_bound_r_sum": 0.0,
            "source_bound_r_additive_allowed": False,
        }
    )
    exact_axis_rows = 0
    for row in parity_rows:
        profile = text(row.get("broad_replay_profile"), "unknown")
        label = text(row.get("execution_leakage_label"), "unknown")
        profile_counts[profile][label] += 1
        metrics = profile_metrics[profile]
        metrics["rows"] += 1
        broad_candidate_generated = row.get("broad_replay_candidate_generated") is True or (
            row.get("candidate_generation_label") == "candidate_generated"
        )
        bridge_candidate_generated = (
            row.get("selected_package_bridge_candidate_generated") is True
        )
        if broad_candidate_generated:
            metrics["broad_replay_candidate_generated_axis_rows"] += 1
        if bridge_candidate_generated:
            metrics["selected_package_bridge_candidate_generated_axis_rows"] += 1
        metrics["candidate_generated_axis_rows"] += int(axis_candidate_generated(row))
        metrics["candidate_not_generated_axis_rows"] = (
            metrics["rows"] - metrics["candidate_generated_axis_rows"]
        )
        metrics["candidate_trace_row_count"] += int(row.get("candidate_trace_row_count") or 0)
        metrics["scheduler_option_present_count"] += int(
            row.get("scheduler_option_present_count") or 0
        )
        metrics["scorecard_present_axis_rows"] += int(
            int(row.get("scheduler_option_present_count") or 0) > 0
        )
        metrics["scorecard_selected_count"] += int(row.get("scorecard_selected_count") or 0)
        metrics["scheduler_selected_axis_rows"] += int(
            int(row.get("scorecard_selected_count") or 0) > 0
        )
        metrics["order_present_count"] += int(row.get("order_present_count") or 0)
        metrics["order_present_axis_rows"] += int(
            int(row.get("order_present_count") or 0) > 0
        )
        metrics["trade_count"] += int(row.get("trade_count") or 0)
        metrics["filled_trade_axis_rows"] += int(
            int(row.get("trade_count") or 0) > 0
        )
        metrics["axis_attributed_trade_count"] += int(row.get("trade_count") or 0)
        metrics["unique_trade_candidate_instance_keys"].update(
            (row.get("unique_trade_actual_r_by_candidate_instance_key") or {}).keys()
        )
        metrics["actual_r_sum"] = add(metrics["actual_r_sum"], row.get("actual_r_sum"))
        metrics["axis_attributed_actual_r_sum"] = add(
            metrics["axis_attributed_actual_r_sum"], row.get("actual_r_sum")
        )
        for source_field, target_field in (
            (
                "unique_trade_actual_r_by_candidate_instance_key",
                "unique_trade_actual_r_by_candidate_instance_key",
            ),
            (
                "unique_trade_gross_r_by_candidate_instance_key",
                "unique_trade_gross_r_by_candidate_instance_key",
            ),
            (
                "unique_trade_final_r_by_candidate_instance_key",
                "unique_trade_final_r_by_candidate_instance_key",
            ),
            (
                "unique_trade_cash_pnl_by_candidate_instance_key",
                "unique_trade_cash_pnl_by_candidate_instance_key",
            ),
        ):
            for instance_key, value in (row.get(source_field) or {}).items():
                metrics[target_field][text(instance_key)] = safe_float(value)
        metrics["missed_net_proxy_r_sum"] = add(
            metrics["missed_net_proxy_r_sum"], row.get("missed_net_proxy_r_sum")
        )
        metrics["missed_positive_net_r_sum"] = add(
            metrics["missed_positive_net_r_sum"], row.get("missed_positive_net_r_sum")
        )
        metrics["missed_negative_net_r_sum"] = add(
            metrics["missed_negative_net_r_sum"], row.get("missed_negative_net_r_sum")
        )
        metrics["blocked_counterfactual_missed_count"] += int(
            row.get("blocked_counterfactual_missed_count") or 0
        )
        metrics["blocked_counterfactual_missed_net_proxy_r_sum"] = add(
            metrics["blocked_counterfactual_missed_net_proxy_r_sum"],
            row.get("blocked_counterfactual_missed_net_proxy_r_sum"),
        )
        metrics["blocked_counterfactual_missed_positive_net_r_sum"] = add(
            metrics["blocked_counterfactual_missed_positive_net_r_sum"],
            row.get("blocked_counterfactual_missed_positive_net_r_sum"),
        )
        metrics["blocked_counterfactual_missed_negative_net_r_sum"] = add(
            metrics["blocked_counterfactual_missed_negative_net_r_sum"],
            row.get("blocked_counterfactual_missed_negative_net_r_sum"),
        )
        metrics["source_combined_signal_r_sum"] = add(
            metrics["source_combined_signal_r_sum"], row.get("combined_source_bound_signal_r")
        )
        metrics["diagnostic_package_source_bound_r_sum"] = add(
            metrics["diagnostic_package_source_bound_r_sum"],
            row.get("diagnostic_package_source_bound_r"),
        )
        metrics["diagnostic_source_bound_r_sum"] = add(
            metrics["diagnostic_source_bound_r_sum"], row.get("diagnostic_source_bound_r")
        )
        metrics["effective_package_source_bound_r_sum"] = add(
            metrics["effective_package_source_bound_r_sum"],
            row.get("effective_package_source_bound_r"),
        )
        metrics["effective_source_bound_r_sum"] = add(
            metrics["effective_source_bound_r_sum"], row.get("effective_source_bound_r")
        )
        metrics["package_source_bound_r_sum"] = add(
            metrics["package_source_bound_r_sum"], row.get("package_source_bound_r")
        )
        metrics["source_bound_r_sum"] = add(metrics["source_bound_r_sum"], row.get("source_bound_r"))
        exact_axis_rows += 1 if int(row.get("exact_package_candidate_match_count") or 0) > 0 else 0

    serializable_profile_metrics: dict[str, dict[str, Any]] = {}
    for profile, metrics in sorted(profile_metrics.items()):
        output = dict(metrics)
        unique_ids = set(output.pop("unique_trade_candidate_instance_keys", set()))
        actual_by_id = output.pop("unique_trade_actual_r_by_candidate_instance_key", {})
        gross_by_id = output.pop("unique_trade_gross_r_by_candidate_instance_key", {})
        final_by_id = output.pop("unique_trade_final_r_by_candidate_instance_key", {})
        cash_by_id = output.pop("unique_trade_cash_pnl_by_candidate_instance_key", {})
        unique_ids.update(key for key, value in actual_by_id.items() if value is not None)
        output["axis_attributed_trade_count"] = output.get("axis_attributed_trade_count", output.get("trade_count", 0))
        output["axis_attributed_actual_r_sum"] = output.get("axis_attributed_actual_r_sum", output.get("actual_r_sum", 0.0))
        output["unique_trade_candidate_count"] = len(unique_ids)
        output["unique_replay_trade_identity"] = (
            "candidate_instance_key_exact_within_broad_replay_profile"
        )
        output["unique_actual_r_sum"] = sum(
            value for value in actual_by_id.values() if value is not None
        )
        output["unique_gross_r_sum"] = sum(
            value for value in gross_by_id.values() if value is not None
        )
        output["unique_final_r_sum"] = sum(
            value for value in final_by_id.values() if value is not None
        )
        output["unique_cash_pnl_sum"] = sum(
            value for value in cash_by_id.values() if value is not None
        )
        output["executable_gated_vs_diagnostic_reservoir_delta_r"] = (
            safe_float(output.get("effective_package_source_bound_r_sum"))
            - safe_float(output.get("diagnostic_package_source_bound_r_sum"))
        )
        output["diagnostic_reservoir_minus_executable_gated_r"] = (
            safe_float(output.get("diagnostic_package_source_bound_r_sum"))
            - safe_float(output.get("effective_package_source_bound_r_sum"))
        )
        output["unique_trade_candidate_instance_key_samples"] = sorted(unique_ids)[:8]
        serializable_profile_metrics[profile] = output
    exact_window_transfer = build_exact_replay_window_transfer_summary(
        parity_rows=parity_rows,
        profile_metrics=serializable_profile_metrics,
        candidate_instance_projection_summary=(
            candidate_instance_projection_summary
        ),
    )

    return {
        "schema": "gtos.final_moonshot.denominator_to_deployment.source_bound_to_executed_parity.summary.v1",
        "generated_utc": utc_now(),
        "route_id": ROUTE.name,
        "broad_replay_prefix": BROAD_PREFIX,
        "broad_replay_observation_status": observation_status,
        "broker_live_authority": False,
        "final_selection_claim": False,
        "source_member_axis_rows": len(parity_rows) // len(profiles) if profiles else len(parity_rows),
        "profile_count": len(profiles),
        "profiles": list(profiles),
        "parity_ledger_rows": len(parity_rows),
        "leakage_bucket_rows": len(bucket_rows),
        "exact_package_candidate_rows": exact_package_candidate_rows,
        "exact_package_candidate_unique_ids": exact_package_candidate_ids,
        "package_authority_order_geometry_status_counts": (
            package_authority_order_geometry_status_counts
        ),
        "broad_candidate_rows_indexed": broad_candidate_count,
        "broad_candidate_declared_or_physical_rows": broad_candidate_count,
        "broad_candidate_physical_rows": broad_candidate_physical_count,
        "broad_candidate_physical_rows_source": broad_candidate_physical_count_source,
        "broad_candidate_expanded_index_rows": broad_candidate_expanded_index_count,
        "broad_candidate_physical_rows_indexed": broad_candidate_expanded_index_count,
        "broad_candidate_physical_rows_indexed_semantics": (
            "legacy_name_expanded_join_index_rows_not_physical_ledger_rows"
        ),
        "broad_candidate_rows_indexed_source": (
            "broad_summary_or_ledger_declared_candidate_rows"
            if broad_candidate_count != broad_candidate_expanded_index_count
            else "expanded_candidate_join_index_rows"
        ),
        "source_axis_rows_with_exact_package_candidate_match": exact_axis_rows,
        "row_level_fields_included": [
            "candidate_generated",
            "candidate_generation_label",
            "candidate_generation_observation_scope",
            "source_axis_replay_class",
            "candidate_generation_mismatch_reason",
            "candidate_generation_mismatch_fields",
            "same_symbol_side_candidate_count",
            "selector_action_counts",
            "scheduler_rank_min",
            "scheduler_score_max",
            "scheduler_option_present_count",
            "scorecard_selected_count",
            "risk_decision_counts",
            "order_policy_counts",
            "order_status_counts",
            "fillability_status_counts",
            "candidate_lifecycle_action_counts",
            "risk_lifecycle_action_counts",
            "exit_result_counts",
            "actual_r_sum",
            "axis_attributed_actual_r_sum",
            "unique_actual_r_sum",
            "deviation_reason",
            "package_source_bound_r",
            "source_bound_r",
            "candidate_execution_trace_samples",
        ],
        "profile_leakage_label_counts": {
            profile: counter_dict(counts) for profile, counts in sorted(profile_counts.items())
        },
        "profile_metrics": serializable_profile_metrics,
        "exact_replay_window_transfer": exact_window_transfer,
        "artifacts": {
            "big_r_provenance_breakdown": str(BIG_R_PROVENANCE_PATH),
            "source_bound_to_executed_parity_ledger": str(PARITY_LEDGER_PATH),
            "source_bound_to_executed_parity_summary": str(PARITY_SUMMARY_PATH),
            "execution_leakage_bucket_ledger": str(LEAKAGE_BUCKET_PATH),
            "execution_leakage_repair_plan": str(REPAIR_PLAN_PATH),
            "broad_replay_summary": str(BROAD_SUMMARY_PATH),
            "broad_replay_comparison": str(BROAD_COMPARISON_PATH),
        },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--broad-prefix",
        default=None,
        help=(
            "Broad replay prefix to analyze. Defaults to the newest completed "
            "broker-live-closed replay summary unless GTOS_BROAD_QUALITY_PARITY_PREFIX is set."
        ),
    )
    parser.add_argument(
        "--artifact-tag",
        default="",
        help="Optional suffix tag for parity outputs; empty writes canonical names.",
    )
    return parser.parse_args()


def staged_artifact_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".building.tmp")


def write_json_payload_file(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    broad_prefix = str(args.broad_prefix or latest_completed_broad_prefix())
    artifact_tag = str(args.artifact_tag or "").strip() or broad_quality_artifact_tag(
        broad_prefix
    )
    configure_artifact_paths(
        broad_prefix=broad_prefix,
        artifact_tag=artifact_tag,
    )
    observation_status = artifact_status()
    big_r_provenance = build_big_r_provenance(observation_status)
    final_to_stage = {
        BIG_R_PROVENANCE_PATH: staged_artifact_path(BIG_R_PROVENANCE_PATH),
        PARITY_LEDGER_PATH: staged_artifact_path(PARITY_LEDGER_PATH),
        PARITY_SUMMARY_PATH: staged_artifact_path(PARITY_SUMMARY_PATH),
        CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH: staged_artifact_path(
            CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH
        ),
        LEAKAGE_BUCKET_PATH: staged_artifact_path(LEAKAGE_BUCKET_PATH),
        REPAIR_PLAN_PATH: staged_artifact_path(REPAIR_PLAN_PATH),
    }
    trace_spool_path = PARITY_LEDGER_PATH.with_suffix(
        PARITY_LEDGER_PATH.suffix + ".candidate-trace.spool.tmp"
    )
    temporary_paths = [*final_to_stage.values(), trace_spool_path]
    for path in temporary_paths:
        path.unlink(missing_ok=True)

    try:
        projection_stage = final_to_stage[
            CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH
        ]
        with projection_stage.open("w", encoding="utf-8") as projection_handle:
            with trace_spool_path.open("w", encoding="utf-8") as trace_handle:
                cyclic_gc_was_enabled = gc.isenabled()
                if cyclic_gc_was_enabled:
                    gc.disable()
                try:
                    parity_rows, bucket_rows, _projection_rows, summary = (
                        _build_parity_rows_and_projection_with_sinks(
                            candidate_projection_sink=lambda row: projection_handle.write(
                                json.dumps(row, sort_keys=True, default=str) + "\n"
                            ),
                            candidate_trace_sink=lambda row: trace_handle.write(
                                json.dumps(row, sort_keys=True, default=str) + "\n"
                            ),
                        )
                    )
                finally:
                    if cyclic_gc_was_enabled:
                        gc.enable()

        parity_stage = final_to_stage[PARITY_LEDGER_PATH]
        with parity_stage.open("w", encoding="utf-8") as parity_handle:
            write_jsonl_rows(parity_handle, parity_rows)
            with trace_spool_path.open("r", encoding="utf-8") as trace_handle:
                shutil.copyfileobj(trace_handle, parity_handle, length=16 * 1024 * 1024)

        with final_to_stage[LEAKAGE_BUCKET_PATH].open(
            "w", encoding="utf-8"
        ) as bucket_handle:
            write_jsonl_rows(bucket_handle, bucket_rows)

        repair_plan = build_execution_leakage_repair_plan(
            summary=summary,
            bucket_rows=bucket_rows,
            observation_status=observation_status,
        )
        write_json_payload_file(
            final_to_stage[BIG_R_PROVENANCE_PATH],
            big_r_provenance,
        )
        write_json_payload_file(final_to_stage[REPAIR_PLAN_PATH], repair_plan)
        write_json_payload_file(final_to_stage[PARITY_SUMMARY_PATH], summary)

        # Publish ledgers before the summary, which is the completion marker.
        for final_path in (
            BIG_R_PROVENANCE_PATH,
            PARITY_LEDGER_PATH,
            CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH,
            LEAKAGE_BUCKET_PATH,
            REPAIR_PLAN_PATH,
            PARITY_SUMMARY_PATH,
        ):
            final_to_stage[final_path].replace(final_path)
    finally:
        for path in temporary_paths:
            path.unlink(missing_ok=True)

    print(
        json.dumps(
            {
                "status": "source_bound_execution_parity_materialized",
                "broad_replay_prefix": BROAD_PREFIX,
                "broad_replay_observation_status": observation_status,
                "parity_rows": int(summary.get("parity_ledger_rows") or 0),
                "leakage_bucket_rows": len(bucket_rows),
                "candidate_instance_parity_projection_rows": int(
                    summary.get("candidate_instance_parity_projection_rows") or 0
                ),
                "artifacts": summary["artifacts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
