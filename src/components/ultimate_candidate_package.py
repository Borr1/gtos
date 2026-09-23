"""Default-off ultimate candidate package surface.

This module turns the compressed final-package sleeve ledger into a runtime
readable selector/scheduler surface. It is shadow-only by default and never
places orders, calls brokers, mutates account/order/deal/position state,
reveals credentials, calls paid APIs, or starts remote/VPS work.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.components.session_namespace import utc_hour_bucket_aliases


SCHEMA_VERSION = "ultimate_candidate_package_v1"
COMPONENT = "ultimate_candidate_package"
EVIDENCE_CLASS = "production_code_integration_default_off_shadow_candidate_package"
RESULT_USE_STATUS = "RESULT_MATERIALIZATION_REQUIRED"

SURFACE_SCHEMA = "gtos.final_moonshot.ultimate_candidate_package.surface.v1"
SLEEVE_REGISTRY_SCHEMA = "gtos.final_moonshot.ultimate_candidate_package.sleeve_registry.v1"
SELECTOR_SHADOW_LEDGER_SCHEMA = (
    "gtos.final_moonshot.ultimate_candidate_package.selector_shadow_ledger.v1"
)
SCHEDULER_SHADOW_LEDGER_SCHEMA = (
    "gtos.final_moonshot.ultimate_candidate_package.scheduler_shadow_ledger.v1"
)
SELECTOR_PACKET_SCHEMA = "gtos.final_moonshot.ultimate_candidate_package.selector_packet.v1"
SCHEDULER_PACKET_SCHEMA = "gtos.final_moonshot.ultimate_candidate_package.scheduler_packet.v1"
EXECUTION_POLICY_PACKET_SCHEMA = (
    "gtos.final_moonshot.ultimate_candidate_package.execution_policy_packet.v1"
)
VERIFICATION_SCHEMA = "gtos.final_moonshot.ultimate_candidate_package.verification.v1"
REPLAY_AUTHORITY_CANDIDATE_LEDGER_SCHEMA = (
    "gtos.final_moonshot.ultimate_candidate_package.replay_authority_candidate.v1"
)
REPLAY_AUTHORITY_SCORECARD_LEDGER_SCHEMA = (
    "gtos.final_moonshot.ultimate_candidate_package.replay_authority_scorecard.v1"
)
REPLAY_AUTHORITY_ORDER_POLICY_LEDGER_SCHEMA = (
    "gtos.final_moonshot.ultimate_candidate_package.replay_authority_order_policy.v1"
)

SCHEDULER_LIFECYCLE_MERGE_TYPE = "scheduler_lifecycle_merge_sleeve"
PROMOTE_DEFAULT_OFF_TYPE = "promote_default_off_signal_sleeve"
AVOID_FAILURE_FEATURE_TYPE = "avoid_failure_feature_sleeve"
REDESIGN_REPAIR_TYPE = "redesign_repair_sleeve"
SOURCE_REQUIRED_HOLD_TYPE = "source_required_hold_sleeve"
DEFAULT_PACKAGE_REGISTRY_PATH = (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl"
)
DEFAULT_COMPRESSED_SLEEVE_SOURCE_PATH = (
    "research/operations/"
    "final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19/"
    "FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
REPLAY_MISSING_SOURCE_COMPLETENESS_DEFAULT = 0.25
REPLAY_MIN_EXECUTABLE_SOURCE_COMPLETENESS = 0.95
REPLAY_MISSING_CONFIDENCE_DEFAULT = 0.55
REPLAY_MISSING_CONFIDENCE_SOURCE = "scheduler_default_missing_confidence_0_55"
REPLAY_MISSING_CONFIDENCE_WARNING = (
    f"confidence_source_inferred:{REPLAY_MISSING_CONFIDENCE_SOURCE}"
)
REPLAY_MISSING_CONFIDENCE_DEGRADED_WARNING = (
    "confidence_missing_degraded_default_applied"
)
REPLAY_MISSING_SOURCE_COMPLETENESS_STATUS = (
    "source_completeness_missing_degraded_default"
)
REPLAY_AUTHORITY_GEOMETRY_FIELDS = (
    "entry_price",
    "entry_reference",
    "stop_loss",
    "stop_or_invalidation",
    "take_profit_1",
    "take_profit",
    "target_reference",
    "risk_reward_ratio",
    "trade_parameters",
    "geometry_contract",
    "dynamic_geometry_policy",
    "dynamic_execution_policy_id",
    "canonical_geometry_status",
    "canonical_geometry_source",
    "canonical_geometry_target_recomputed",
)
REPLAY_QUALITY_FIELDS = (
    "expected_net_r",
    "probability",
    "fill_probability",
    "source_completeness",
)
REPLAY_EXACT_QUALITY_ALIAS_STATUSES = {
    "exact_materialized",
    "exact_materialized_from_complete_predecision_quality_sources",
}
REPLAY_MATERIALIZED_ALIAS_STATUS_UPGRADE = (
    "exact_materialized_from_complete_predecision_quality_sources"
)
REPLAY_ALIAS_STATUS_MATERIALIZED_FAILURE = (
    "candidate_decision_quality_alias_status:materialized"
)

FORBIDDEN_RUNTIME_OUTCOME_FIELDS = (
    "actual_r",
    "actual_exact_r",
    "actual_broker_real_pnl_cash",
    "broker_actual_r",
    "broker_cash_pnl",
    "broker_real_net_r",
    "broker_realized_net_r",
    "close_reason",
    "exact_r",
    "final_r",
    "gross_r",
    "hindsight_best_action",
    "hindsight_best_policy",
    "hindsight_best_r",
    "mae_r",
    "mfe_r",
    "net_r",
    "path_outcome",
    "proxy_r",
    "realized_pnl",
    "result_r",
    "source_bound_proxy_r",
)


@dataclass(frozen=True)
class UltimateCandidatePackageConfig:
    enabled: bool = False
    shadow_enabled: bool = True
    replay_admission_enabled: bool = True
    apply_to_execution: bool = False
    live_activation_allowed: bool = False
    final_package_selected: bool = False

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any] | None,
    ) -> "UltimateCandidatePackageConfig":
        data = value if isinstance(value, Mapping) else {}
        runtime = data.get("gtos_vnext_runtime")
        if isinstance(runtime, Mapping):
            data = runtime
        nested = data.get("ultimate_candidate_package")
        if isinstance(nested, Mapping):
            data = {**data, **nested}
        shadow_enabled = _truthy(
            data.get(
                "ultimate_candidate_package_shadow_enabled",
                data.get("shadow_enabled", True),
            )
        )
        return cls(
            enabled=_truthy(data.get("ultimate_candidate_package_enabled", data.get("enabled"))),
            shadow_enabled=shadow_enabled,
            replay_admission_enabled=_truthy(
                data.get(
                    "ultimate_candidate_package_replay_admission_enabled",
                    data.get("replay_admission_enabled", shadow_enabled),
                )
            ),
            apply_to_execution=_truthy(
                data.get("ultimate_candidate_package_apply_to_execution", data.get("apply_to_execution"))
            ),
            live_activation_allowed=_truthy(
                data.get("ultimate_candidate_package_live_activation_allowed", data.get("live_activation_allowed"))
            ),
            final_package_selected=_truthy(
                data.get("ultimate_candidate_package_final_package_selected", data.get("final_package_selected"))
            ),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _packet_hash(payload: Any) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _norm(value: Any) -> str:
    return _text(value).lower()


def _upper(value: Any) -> str:
    return _text(value).upper()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _norm(value) in {"1", "true", "yes", "y", "enabled", "on"}


def _num(value: Any, default: float = 0.0) -> float:
    if value in (None, "") or isinstance(value, bool):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return number


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    return [value]


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _as_list(value) if _text(item)]


def _side(value: Any) -> str:
    raw = _upper(value)
    if raw in {"BUY", "BULL", "BULLISH", "LONG", "UP"}:
        return "LONG"
    if raw in {"SELL", "BEAR", "BEARISH", "SHORT", "DOWN"}:
        return "SHORT"
    return raw


def _role_for_sleeve_type(sleeve_type: str) -> str:
    if sleeve_type == SCHEDULER_LIFECYCLE_MERGE_TYPE:
        return "scheduler_lifecycle_core"
    if sleeve_type == PROMOTE_DEFAULT_OFF_TYPE:
        return "promote_default_off_signal"
    if sleeve_type == AVOID_FAILURE_FEATURE_TYPE:
        return "avoid_failure_feature"
    if sleeve_type == REDESIGN_REPAIR_TYPE:
        return "redesign_repair_candidate"
    if sleeve_type == SOURCE_REQUIRED_HOLD_TYPE:
        return "source_required_hold"
    return "unknown_sleeve_type"


def _sleeve_wildcard_token(value: str) -> bool:
    return _norm(value) in {"*", "all", "any", "broader_origin", "all_origins"}


def _runtime_closed_gates() -> dict[str, bool]:
    return {
        "runtime_effect_now": False,
        "candidate_use_allowed_now": False,
        "selected_package_denominator_use_allowed": False,
        "denominator_expansion_allowed": False,
        "clean_label_use_allowed": False,
        "training_use_allowed": False,
        "model_training_allowed": False,
        "final_package_selection_allowed": False,
        "deployment_dossier_allowed": False,
        "vps_handoff_allowed": False,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
        "broker_operation": False,
        "order_calls": False,
        "paid_api_or_vendor_call": False,
    }


def _noneish(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _first_present(*values: Any) -> Any:
    for value in values:
        if not _noneish(value):
            return value
    return None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_mapping(*values: Any) -> Mapping[str, Any]:
    for value in values:
        if isinstance(value, Mapping) and value:
            return value
    return {}


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _gate_not_false(packet: Mapping[str, Any], key: str) -> bool:
    value = packet.get(key)
    return value is not False and value not in (None, "")


def _order_calls_not_zero(packet: Mapping[str, Any]) -> bool:
    value = packet.get("order_calls")
    if value in (None, "", False, 0):
        return False
    try:
        return float(value) != 0.0
    except (TypeError, ValueError):
        return True


def find_ultimate_candidate_package_shadow_source(
    fields: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Find the package shadow packet across scheduler/execution packet shapes."""
    scheduler_packet = _mapping(fields.get("gtos_vnext_scheduler_v4_packet"))
    scheduler_decision = _mapping(scheduler_packet.get("decision"))
    execution_packet = _mapping(fields.get("gtos_vnext_execution_manager_v4_packet"))
    execution_scheduler = _mapping(execution_packet.get("scheduler_v4"))
    execution_scheduler_packet = _mapping(execution_scheduler.get("packet"))
    execution_scheduler_decision = _mapping(execution_scheduler_packet.get("decision"))

    return _first_mapping(
        fields.get("ultimate_candidate_package_shadow"),
        scheduler_packet.get("ultimate_candidate_package_shadow"),
        scheduler_decision.get("ultimate_candidate_package_shadow"),
        execution_scheduler.get("ultimate_candidate_package_shadow"),
        execution_scheduler_packet.get("ultimate_candidate_package_shadow"),
        execution_scheduler_decision.get("ultimate_candidate_package_shadow"),
    )


def build_ultimate_candidate_package_shadow_summary(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a compact fail-closed package boundary summary for capture rows.

    The summary is evidence-only. It records whether a shadow package packet is
    present and whether every runtime/final/live/order gate is still closed.
    """
    source = find_ultimate_candidate_package_shadow_source(fields)
    if not source:
        return {
            "status": "ultimate_candidate_package_shadow_not_present",
            "authority_closed": None,
            "packet_present": False,
            "packet_hash": None,
            "decision_status": None,
            "shadow_selected_candidate_id": None,
            "selected_candidate_id": None,
            "approved_risk_pct": None,
            "runtime_effect_now": None,
            "live_execution_activation_allowed": None,
            "final_package_selection_allowed": None,
            "order_calls": None,
            "execution_policy_status": None,
            "selected_order_type_architecture": None,
            "execution_order_type_policy_selectable": None,
            "gate_violations": [],
            "summary": {
                "status": "ultimate_candidate_package_shadow_not_present",
                "packet_present": False,
                "authority_closed": None,
            },
        }

    packet = _mapping(source.get("packet")) or source
    policy = _mapping(packet.get("execution_policy_shadow"))
    gate_violations = list(source.get("gate_violations") or [])

    for gate in (
        "apply_to_execution",
        "live_activation_allowed_by_config",
        "final_package_selected_by_config",
        "runtime_effect_now",
        "candidate_use_allowed_now",
        "selected_package_denominator_use_allowed",
        "denominator_expansion_allowed",
        "clean_label_use_allowed",
        "training_use_allowed",
        "model_training_allowed",
        "final_package_selection_allowed",
        "deployment_dossier_allowed",
        "vps_handoff_allowed",
        "live_execution_activation_allowed",
        "broker_account_order_history_deal_position_mutation_allowed",
        "broker_operation",
        "paid_api_or_vendor_call",
    ):
        violation = f"{gate}_not_false"
        if _gate_not_false(packet, gate) and violation not in gate_violations:
            gate_violations.append(violation)

    for gate, expected in (("default_off", True), ("shadow_only", True)):
        violation = f"{gate}_not_true"
        if packet.get(gate) is not expected and violation not in gate_violations:
            gate_violations.append(violation)

    if packet.get("selected_candidate_id") not in (None, ""):
        violation = "selected_candidate_id_not_closed"
        if violation not in gate_violations:
            gate_violations.append(violation)

    approved_risk = _float_or_none(
        source.get("approved_risk_pct", packet.get("approved_risk_pct"))
    )
    if approved_risk is not None and approved_risk != 0.0:
        violation = "approved_risk_pct_not_zero"
        if violation not in gate_violations:
            gate_violations.append(violation)
    if _order_calls_not_zero(packet):
        violation = "order_calls_not_zero"
        if violation not in gate_violations:
            gate_violations.append(violation)

    if policy:
        for gate in (
            "apply_to_execution",
            "live_activation_allowed_by_config",
            "final_package_selected_by_config",
            "runtime_effect_now",
            "candidate_use_allowed_now",
            "selected_package_denominator_use_allowed",
            "denominator_expansion_allowed",
            "clean_label_use_allowed",
            "training_use_allowed",
            "model_training_allowed",
            "final_package_selection_allowed",
            "deployment_dossier_allowed",
            "vps_handoff_allowed",
            "live_execution_activation_allowed",
            "broker_account_order_history_deal_position_mutation_allowed",
            "broker_operation",
            "paid_api_or_vendor_call",
            "execution_order_type_policy_selectable",
            "missed_fill_opportunity_cost_allowed",
            "limit_first_vs_guarded_market_comparison_allowed",
            "broker_real_expectancy_claim_allowed",
        ):
            violation = f"execution_policy_shadow.{gate}_not_false"
            if _gate_not_false(policy, gate) and violation not in gate_violations:
                gate_violations.append(violation)
        if policy.get("selected_order_type_architecture") not in (None, ""):
            violation = (
                "execution_policy_shadow.selected_order_type_architecture_not_closed"
            )
            if violation not in gate_violations:
                gate_violations.append(violation)
        policy_risk = _float_or_none(policy.get("approved_risk_pct"))
        if policy_risk is not None and policy_risk != 0.0:
            violation = "execution_policy_shadow.approved_risk_pct_not_zero"
            if violation not in gate_violations:
                gate_violations.append(violation)
        if _order_calls_not_zero(policy):
            violation = "execution_policy_shadow.order_calls_not_zero"
            if violation not in gate_violations:
                gate_violations.append(violation)

    authority_closed = not gate_violations
    status = (
        source.get("status")
        if source.get("status")
        in {
            "default_off_shadow_authority_closed",
            "ultimate_candidate_package_shadow_authority_open",
        }
        else (
            "default_off_shadow_authority_closed"
            if authority_closed
            else "ultimate_candidate_package_shadow_authority_open"
        )
    )
    summary = {
        "status": status,
        "authority_closed": authority_closed,
        "packet_present": True,
        "packet_hash": _first_present(
            source.get("packet_hash"),
            source.get("packet_hash_sha256"),
            packet.get("packet_hash_sha256"),
            packet.get("packet_hash"),
        ),
        "decision_status": _first_present(
            source.get("decision_status"),
            packet.get("decision_status"),
        ),
        "shadow_selected_candidate_id": _first_present(
            source.get("shadow_selected_candidate_id"),
            packet.get("shadow_selected_candidate_id"),
        ),
        "selected_candidate_id": _first_present(
            source.get("selected_candidate_id"),
            packet.get("selected_candidate_id"),
        ),
        "approved_risk_pct": approved_risk,
        "runtime_effect_now": _first_present(
            source.get("runtime_effect_now"),
            packet.get("runtime_effect_now"),
        ),
        "live_execution_activation_allowed": _first_present(
            source.get("live_execution_activation_allowed"),
            packet.get("live_execution_activation_allowed"),
        ),
        "final_package_selection_allowed": _first_present(
            source.get("final_package_selection_allowed"),
            packet.get("final_package_selection_allowed"),
        ),
        "order_calls": _first_present(
            source.get("order_calls"),
            packet.get("order_calls"),
        ),
        "execution_policy_status": _first_present(
            source.get("execution_policy_status"),
            policy.get("policy_status"),
        ),
        "selected_order_type_architecture": _first_present(
            source.get("selected_order_type_architecture"),
            policy.get("selected_order_type_architecture"),
        ),
        "execution_order_type_policy_selectable": _first_present(
            source.get("execution_order_type_policy_selectable"),
            policy.get("execution_order_type_policy_selectable"),
        ),
        "gate_violations": gate_violations,
    }
    return {**summary, "summary": summary}


def _blocked_runtime_fields(row: Mapping[str, Any]) -> list[str]:
    return sorted(field for field in FORBIDDEN_RUNTIME_OUTCOME_FIELDS if field in row)


def _candidate_replay_geometry_fields(candidate: Mapping[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for field in REPLAY_AUTHORITY_GEOMETRY_FIELDS:
        value = candidate.get(field)
        if not _noneish(value):
            fields[field] = value
    trade_parameters = _mapping(candidate.get("trade_parameters"))
    entry_price = _first_present(fields.get("entry_price"), trade_parameters.get("entry_price"))
    stop_loss = _first_present(fields.get("stop_loss"), trade_parameters.get("stop_loss"))
    target = _first_present(
        fields.get("target_reference"),
        fields.get("take_profit_1"),
        fields.get("take_profit"),
        trade_parameters.get("target_reference"),
        trade_parameters.get("take_profit_1"),
        trade_parameters.get("take_profit"),
        trade_parameters.get("target_price"),
    )
    risk_reward_ratio = _first_present(
        fields.get("risk_reward_ratio"),
        trade_parameters.get("risk_reward_ratio"),
        trade_parameters.get("rr"),
    )
    if _noneish(fields.get("entry_reference")) and not _noneish(entry_price):
        fields["entry_reference"] = entry_price
    if _noneish(fields.get("stop_or_invalidation")) and not _noneish(stop_loss):
        fields["stop_or_invalidation"] = stop_loss
    if _noneish(fields.get("target_reference")) and not _noneish(target):
        fields["target_reference"] = target
    if _noneish(fields.get("take_profit")) and not _noneish(target):
        fields["take_profit"] = target
    if _noneish(fields.get("risk_reward_ratio")) and not _noneish(risk_reward_ratio):
        fields["risk_reward_ratio"] = risk_reward_ratio
    if (
        _noneish(fields.get("canonical_geometry_status"))
        and not _noneish(entry_price)
        and not _noneish(stop_loss)
        and not _noneish(target)
    ):
        fields["canonical_geometry_status"] = "canonicalized"
    if (
        _noneish(fields.get("canonical_geometry_source"))
        and not _noneish(entry_price)
        and not _noneish(stop_loss)
        and not _noneish(target)
    ):
        fields["canonical_geometry_source"] = "candidate_order_geometry"
    return fields


def _matched_member_axis_ids(matches: Iterable[Mapping[str, Any]]) -> list[str]:
    ids: list[str] = []
    for match in matches:
        raw_values = _first_present(
            match.get("member_axis_ids"),
            match.get("matched_member_axis_ids"),
            match.get("source_axis_row_ids"),
            match.get("source_axis_row_indexes"),
        )
        if raw_values is None:
            raw_values = _first_present(
                match.get("member_axis_id"),
                match.get("source_axis_row_id"),
                match.get("source_axis_row_index"),
            )
        values = raw_values if isinstance(raw_values, list) else [raw_values]
        for value in values:
            text = _text(value)
            if text and text not in ids:
                ids.append(text)
    return ids


def load_sleeve_rows(path: str | Path) -> list[dict[str, Any]]:
    target = _resolve_package_path(path)
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_ultimate_candidate_package_registry(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load a normalized package registry, or normalize a raw compressed sleeve ledger.

    Runtime config points at the generated route registry. Tests and local
    repair runs may point directly at the acceptance-compression sleeve ledger;
    that raw format is normalized here so selector/scheduler callers share one
    shape.
    """
    target = str(_resolve_package_path(path or DEFAULT_PACKAGE_REGISTRY_PATH))
    active_lease = _ACTIVE_ULTIMATE_PACKAGE_REGISTRY_LEASE.get()
    if active_lease is not None:
        return active_lease.load(target)
    effective = _effective_registry_path(Path(target))
    if effective is None:
        return []
    effective_text = str(effective)
    return list(
        _load_ultimate_candidate_package_registry_cached(
            effective_text,
            _file_mtime(effective_text),
        )
    )


def _file_mtime(path: str) -> float:
    try:
        return _resolve_package_path(path).stat().st_mtime
    except OSError:
        return -1.0


def _resolve_package_path(path: str | Path) -> Path:
    """Resolve repo-root relative package paths from route-local replay cwd."""

    target = Path(path)
    if target.is_absolute() or target.exists():
        return target
    repo_target = REPO_ROOT / target
    if repo_target.exists():
        return repo_target
    return target


class UltimateCandidatePackageRegistryChanged(RuntimeError):
    """Raised when a campaign-pinned registry or its cached rows change."""


@dataclass(frozen=True)
class _RegistryFileIdentity:
    path: str
    exists: bool
    device: int | None
    inode: int | None
    size: int | None
    mtime_ns: int | None
    ctime_ns: int | None
    sha256: str | None


def _registry_file_identity(path: Path) -> _RegistryFileIdentity:
    resolved = _resolve_package_path(path)
    try:
        before = resolved.stat()
    except OSError:
        return _RegistryFileIdentity(
            path=str(resolved),
            exists=False,
            device=None,
            inode=None,
            size=None,
            mtime_ns=None,
            ctime_ns=None,
            sha256=None,
        )
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    after = resolved.stat()
    before_token = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_token = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if before_token != after_token:
        raise UltimateCandidatePackageRegistryChanged(
            "registry_source_changed_during_read"
        )
    return _RegistryFileIdentity(
        path=str(resolved),
        exists=True,
        device=after.st_dev,
        inode=after.st_ino,
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        ctime_ns=after.st_ctime_ns,
        sha256=digest.hexdigest(),
    )


def _effective_registry_path(
    requested_path: Path,
    *,
    replay_lfs_pointer_fallback: bool = False,
) -> Path | None:
    requested = _resolve_package_path(requested_path)
    if requested.exists():
        if not _is_git_lfs_pointer(requested):
            return requested
        if not replay_lfs_pointer_fallback:
            return requested
    fallback = _resolve_package_path(DEFAULT_COMPRESSED_SLEEVE_SOURCE_PATH)
    if requested.exists() and requested == fallback:
        return requested
    return fallback if fallback.exists() else None


def _is_git_lfs_pointer(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(48).startswith(b"version https://git-lfs.github.com/spec/v1")
    except OSError:
        return False


def _load_registry_rows_uncached(target: Path) -> tuple[dict[str, Any], ...]:
    rows = load_sleeve_rows(target)
    if not rows:
        return ()
    if rows[0].get("schema") == SLEEVE_REGISTRY_SCHEMA:
        return tuple(rows)
    surface = build_ultimate_candidate_package_surface(
        rows,
        generated_utc="1970-01-01T00:00:00Z",
        source_sleeve_path=str(target),
    )
    return tuple(surface["sleeve_registry_rows"])


def _registry_rows_root(rows: tuple[dict[str, Any], ...]) -> str:
    return _packet_hash(rows)


@dataclass
class _RegistryLeaseEntry:
    requested_identity: _RegistryFileIdentity
    effective_identity: _RegistryFileIdentity | None
    rows: tuple[dict[str, Any], ...]
    rows_root_sha256: str


@dataclass
class UltimateCandidatePackageRegistryCampaignLease:
    replay_lfs_pointer_fallback: bool = False
    entries: dict[str, _RegistryLeaseEntry] = field(default_factory=dict)
    hit_count: int = 0
    miss_count: int = 0

    def load(self, requested_path: str | Path) -> list[dict[str, Any]]:
        requested = _resolve_package_path(requested_path)
        key = str(requested)
        existing = self.entries.get(key)
        if existing is not None:
            self.hit_count += 1
            return list(existing.rows)
        self.miss_count += 1
        requested_identity = _registry_file_identity(requested)
        effective = _effective_registry_path(
            requested,
            replay_lfs_pointer_fallback=self.replay_lfs_pointer_fallback,
        )
        effective_identity = (
            _registry_file_identity(effective) if effective is not None else None
        )
        rows = _load_registry_rows_uncached(effective) if effective is not None else ()
        if effective is not None and _registry_file_identity(effective) != effective_identity:
            raise UltimateCandidatePackageRegistryChanged(
                "registry_source_changed_during_read"
            )
        entry = _RegistryLeaseEntry(
            requested_identity=requested_identity,
            effective_identity=effective_identity,
            rows=rows,
            rows_root_sha256=_registry_rows_root(rows),
        )
        self.entries[key] = entry
        return list(rows)

    def validate_boundary(self) -> None:
        for entry in self.entries.values():
            requested_path = Path(entry.requested_identity.path)
            if _registry_file_identity(requested_path) != entry.requested_identity:
                raise UltimateCandidatePackageRegistryChanged(
                    "registry_source_changed_during_campaign"
                )
            if entry.effective_identity is not None:
                effective_path = Path(entry.effective_identity.path)
                if _registry_file_identity(effective_path) != entry.effective_identity:
                    raise UltimateCandidatePackageRegistryChanged(
                        "registry_source_changed_during_campaign"
                    )
            if _registry_rows_root(entry.rows) != entry.rows_root_sha256:
                raise UltimateCandidatePackageRegistryChanged(
                    "registry_rows_changed_during_campaign"
                )


_ACTIVE_ULTIMATE_PACKAGE_REGISTRY_LEASE: ContextVar[
    UltimateCandidatePackageRegistryCampaignLease | None
] = ContextVar("gtos_ultimate_package_registry_campaign_lease", default=None)


@contextmanager
def ultimate_candidate_package_registry_campaign_lease(
    *,
    replay_lfs_pointer_fallback: bool = False,
) -> Iterable[UltimateCandidatePackageRegistryCampaignLease]:
    existing = _ACTIVE_ULTIMATE_PACKAGE_REGISTRY_LEASE.get()
    if existing is not None:
        if replay_lfs_pointer_fallback and not existing.replay_lfs_pointer_fallback:
            raise UltimateCandidatePackageRegistryChanged(
                "registry_lease_replay_fallback_scope_mismatch"
            )
        yield existing
        return
    lease = UltimateCandidatePackageRegistryCampaignLease(
        replay_lfs_pointer_fallback=bool(replay_lfs_pointer_fallback)
    )
    token = _ACTIVE_ULTIMATE_PACKAGE_REGISTRY_LEASE.set(lease)
    try:
        yield lease
        lease.validate_boundary()
    finally:
        _ACTIVE_ULTIMATE_PACKAGE_REGISTRY_LEASE.reset(token)


@lru_cache(maxsize=8)
def _load_ultimate_candidate_package_registry_cached(path: str, _mtime: float) -> tuple[dict[str, Any], ...]:
    del _mtime
    target = _effective_registry_path(_resolve_package_path(path))
    return _load_registry_rows_uncached(target) if target is not None else ()


def _normalized_sleeve(
    row: Mapping[str, Any],
    *,
    row_number: int,
    generated_utc: str,
    max_signal: float,
) -> dict[str, Any]:
    sleeve_type = _text(row.get("sleeve_type"))
    role = _role_for_sleeve_type(sleeve_type)
    signal = _num(row.get("combined_source_bound_signal_r"))
    score = 0.0 if max_signal <= 0 else round(max(signal, 0.0) / max_signal, 9)
    scheduler_counts = {
        str(key): _int(value)
        for key, value in (row.get("scheduler_action_class_counts") or {}).items()
    }
    selector_counts = {
        str(key): _int(value)
        for key, value in (row.get("selector_branch_decision_counts") or {}).items()
    }
    registry_row = {
        "schema": SLEEVE_REGISTRY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated_utc,
        "row_number": row_number,
        "sleeve_id": _text(row.get("sleeve_id")),
        "sleeve_type": sleeve_type,
        "package_role": role,
        "framework": _text(row.get("framework")),
        "origin_family": _text(row.get("origin_family")),
        "side": _side(row.get("side")),
        "symbols": _string_list(row.get("symbols")),
        "symbol_count": _int(row.get("symbol_count")),
        "session_buckets": _string_list(row.get("session_buckets")),
        "session_bucket_count": _int(row.get("session_bucket_count")),
        "member_rows": _int(row.get("member_rows")),
        "candidate_level_rows": _int(row.get("candidate_level_rows")),
        "selector_rows": _int(row.get("selector_rows")),
        "scheduler_rows": _int(row.get("scheduler_rows")),
        "selector_positive_lift_rows": _int(row.get("selector_positive_lift_rows")),
        "selector_zero_lift_rows": _int(row.get("selector_zero_lift_rows")),
        "candidate_level_source_bound_r_sum": _num(row.get("candidate_level_source_bound_r_sum")),
        "selector_lift_sum": _num(row.get("selector_lift_sum")),
        "scheduler_result_r_sum": _num(row.get("scheduler_result_r_sum")),
        "scheduler_missed_result_r_sum": _num(row.get("scheduler_missed_result_r_sum")),
        "combined_source_bound_signal_r": signal,
        "selector_shadow_priority_score": score,
        "acceptance_status": _text(row.get("acceptance_status")),
        "broker_actual_r_role": _text(row.get("broker_actual_r_role")),
        "source_gap_family_counts": {
            str(key): _int(value) for key, value in (row.get("source_gap_family_counts") or {}).items()
        },
        "selector_branch_decision_counts": selector_counts,
        "scheduler_action_class_counts": scheduler_counts,
        "default_off": True,
        "shadow_only": True,
        "selector_surface_component": role
        in {"scheduler_lifecycle_core", "promote_default_off_signal", "avoid_failure_feature"},
        "scheduler_surface_component": role == "scheduler_lifecycle_core",
        "execution_policy_component": role == "scheduler_lifecycle_core",
        **_runtime_closed_gates(),
    }
    registry_row["row_hash_sha256"] = _packet_hash(registry_row)
    return registry_row


def build_ultimate_candidate_package_surface(
    sleeve_rows: Iterable[Mapping[str, Any]],
    *,
    member_rows: Iterable[Mapping[str, Any]] = (),
    generated_utc: str | None = None,
    source_sleeve_path: str | None = None,
    source_member_path: str | None = None,
) -> dict[str, Any]:
    generated = generated_utc or _now_iso()
    raw_rows = list(sleeve_rows)
    member_row_list = list(member_rows)
    max_signal = max((_num(row.get("combined_source_bound_signal_r")) for row in raw_rows), default=0.0)
    registry_rows = [
        _normalized_sleeve(row, row_number=index, generated_utc=generated, max_signal=max_signal)
        for index, row in enumerate(raw_rows, start=1)
    ]
    type_counts = Counter(row["sleeve_type"] for row in registry_rows)
    role_counts = Counter(row["package_role"] for row in registry_rows)

    scheduler_rows = _build_scheduler_shadow_rows(registry_rows, generated_utc=generated)
    selector_rows = _build_selector_shadow_rows(registry_rows, generated_utc=generated)
    surface = {
        "schema": SURFACE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "status": "default_off_shadow_ultimate_candidate_package_surface_ready",
        "source_sleeve_path": source_sleeve_path,
        "source_member_path": source_member_path,
        "compressed_sleeve_rows": len(registry_rows),
        "compressed_member_rows": len(member_row_list),
        "sleeve_type_counts": dict(sorted(type_counts.items())),
        "package_role_counts": dict(sorted(role_counts.items())),
        "scheduler_lifecycle_merge_sleeves": type_counts.get(SCHEDULER_LIFECYCLE_MERGE_TYPE, 0),
        "promote_default_off_signal_sleeves": type_counts.get(PROMOTE_DEFAULT_OFF_TYPE, 0),
        "avoid_failure_feature_sleeves": type_counts.get(AVOID_FAILURE_FEATURE_TYPE, 0),
        "redesign_repair_sleeves": type_counts.get(REDESIGN_REPAIR_TYPE, 0),
        "source_required_hold_sleeves": type_counts.get(SOURCE_REQUIRED_HOLD_TYPE, 0),
        "selector_shadow_ledger_rows": len(selector_rows),
        "scheduler_shadow_ledger_rows": len(scheduler_rows),
        "member_rows_by_sleeve_type": _member_counts_by_type(member_row_list),
        "combined_source_bound_signal_r_sum": round(
            sum(row["combined_source_bound_signal_r"] for row in registry_rows),
            9,
        ),
        "scheduler_lifecycle_combined_source_bound_signal_r_sum": round(
            sum(
                row["combined_source_bound_signal_r"]
                for row in registry_rows
                if row["sleeve_type"] == SCHEDULER_LIFECYCLE_MERGE_TYPE
            ),
            9,
        ),
        "promote_default_off_combined_source_bound_signal_r_sum": round(
            sum(
                row["combined_source_bound_signal_r"]
                for row in registry_rows
                if row["sleeve_type"] == PROMOTE_DEFAULT_OFF_TYPE
            ),
            9,
        ),
        "selector_lift_sum": round(sum(row["selector_lift_sum"] for row in registry_rows), 9),
        "scheduler_result_r_sum": round(sum(row["scheduler_result_r_sum"] for row in registry_rows), 9),
        "selector_surface_ready": True,
        "scheduler_surface_ready": True,
        "verifier_ready": True,
        "default_off": True,
        "shadow_only": True,
        "final_package_selected": False,
        "model_training_allowed": False,
        "live_trading_disabled": True,
        **_runtime_closed_gates(),
    }
    surface["packet_hash_sha256"] = _packet_hash(surface)
    verification = verify_ultimate_candidate_package_surface(
        surface,
        registry_rows,
        selector_rows,
        scheduler_rows,
        generated_utc=generated,
    )
    return {
        "surface": surface,
        "sleeve_registry_rows": registry_rows,
        "selector_shadow_rows": selector_rows,
        "scheduler_shadow_rows": scheduler_rows,
        "verification": verification,
    }


def _member_counts_by_type(member_rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(_text(row.get("sleeve_type")) for row in member_rows)
    return dict(sorted(counts.items()))


def _build_selector_shadow_rows(
    registry_rows: Sequence[Mapping[str, Any]],
    *,
    generated_utc: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, sleeve in enumerate(registry_rows, start=1):
        row = {
            "schema": SELECTOR_SHADOW_LEDGER_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "component": COMPONENT,
            "evidence_class": EVIDENCE_CLASS,
            "result_use_status": RESULT_USE_STATUS,
            "generated_utc": generated_utc,
            "row_number": index,
            "sleeve_id": sleeve.get("sleeve_id"),
            "sleeve_type": sleeve.get("sleeve_type"),
            "package_role": sleeve.get("package_role"),
            "framework": sleeve.get("framework"),
            "origin_family": sleeve.get("origin_family"),
            "side": sleeve.get("side"),
            "symbols": sleeve.get("symbols") or [],
            "session_buckets": sleeve.get("session_buckets") or [],
            "selector_shadow_priority_score": sleeve.get("selector_shadow_priority_score"),
            "selector_lift_sum": sleeve.get("selector_lift_sum"),
            "combined_source_bound_signal_r": sleeve.get("combined_source_bound_signal_r"),
            "selector_branch_decision_counts": sleeve.get("selector_branch_decision_counts") or {},
            "would_selector_role": _would_selector_role(sleeve),
            "selector_package_use": "shadow_ranking_and_feature_only_not_final_selection",
            "default_off": True,
            "shadow_only": True,
            **_runtime_closed_gates(),
        }
        row["row_hash_sha256"] = _packet_hash(row)
        rows.append(row)
    return rows


def _would_selector_role(sleeve: Mapping[str, Any]) -> str:
    role = _text(sleeve.get("package_role"))
    if role == "scheduler_lifecycle_core":
        return "core_selector_constraint_with_scheduler_controls"
    if role == "promote_default_off_signal":
        return "promote_candidate_shadow_signal"
    if role == "avoid_failure_feature":
        return "avoid_or_veto_feature_shadow_signal"
    if role == "redesign_repair_candidate":
        return "redesign_candidate_not_runtime_signal"
    if role == "source_required_hold":
        return "source_required_hold_not_runtime_signal"
    return "unknown_shadow_signal"


def _build_scheduler_shadow_rows(
    registry_rows: Sequence[Mapping[str, Any]],
    *,
    generated_utc: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    core_rows = [
        row for row in registry_rows if row.get("sleeve_type") == SCHEDULER_LIFECYCLE_MERGE_TYPE
    ]
    for index, sleeve in enumerate(core_rows, start=1):
        counts = dict(sleeve.get("scheduler_action_class_counts") or {})
        row = {
            "schema": SCHEDULER_SHADOW_LEDGER_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "component": COMPONENT,
            "evidence_class": EVIDENCE_CLASS,
            "result_use_status": RESULT_USE_STATUS,
            "generated_utc": generated_utc,
            "row_number": index,
            "sleeve_id": sleeve.get("sleeve_id"),
            "sleeve_type": sleeve.get("sleeve_type"),
            "package_role": sleeve.get("package_role"),
            "framework": sleeve.get("framework"),
            "origin_family": sleeve.get("origin_family"),
            "side": sleeve.get("side"),
            "symbols": sleeve.get("symbols") or [],
            "session_buckets": sleeve.get("session_buckets") or [],
            "scheduler_rows": sleeve.get("scheduler_rows"),
            "scheduler_result_r_sum": sleeve.get("scheduler_result_r_sum"),
            "scheduler_missed_result_r_sum": sleeve.get("scheduler_missed_result_r_sum"),
            "scheduler_action_class_counts": counts,
            "dominant_scheduler_control": _dominant_control(counts),
            "would_scheduler_action": _would_scheduler_action(counts),
            "scheduler_package_use": (
                "shadow_queue_delay_reduce_replace_controls_not_execution_authority"
            ),
            "default_off": True,
            "shadow_only": True,
            **_runtime_closed_gates(),
        }
        row["row_hash_sha256"] = _packet_hash(row)
        rows.append(row)
    return rows


def _dominant_control(counts: Mapping[str, Any]) -> str:
    if not counts:
        return "none"
    return max(counts.items(), key=lambda item: (_int(item[1]), str(item[0])))[0]


def _would_scheduler_action(counts: Mapping[str, Any]) -> str:
    dominant = _dominant_control(counts)
    if dominant in {"conflict_net", "reject"}:
        return "shadow_block_or_reject"
    if dominant in {"delay", "queue"}:
        return "shadow_queue_or_delay"
    if dominant == "replace":
        return "shadow_replace_pending"
    if dominant == "admit_reduced_risk":
        return "shadow_admit_reduced_risk"
    return "shadow_no_scheduler_control"


def _shadow_execution_policy_from_scheduler_action(
    would_scheduler_action: str,
    dominant_control: str,
) -> dict[str, Any]:
    if would_scheduler_action == "shadow_queue_or_delay":
        return {
            "would_order_entry_policy": "shadow_limit_first_delay_queue",
            "would_primary_order_type": "limit",
            "would_guarded_market_fallback": "guarded_market_after_fillability_cost_proof",
            "would_queue_management": "delay_or_queue_until_fillability_cost_gate",
            "would_cancel_replace_policy": "observe_only",
            "would_sizing_policy": "no_runtime_sizing_shadow_only",
            "policy_reason": "scheduler_lifecycle_core_prefers_queue_or_delay",
        }
    if would_scheduler_action == "shadow_replace_pending":
        return {
            "would_order_entry_policy": "shadow_cancel_replace_pending",
            "would_primary_order_type": "limit",
            "would_guarded_market_fallback": "guarded_market_after_fillability_cost_proof",
            "would_queue_management": "replace_pending_after_time_in_force_proof",
            "would_cancel_replace_policy": "cancel_replace_shadow_required",
            "would_sizing_policy": "no_runtime_sizing_shadow_only",
            "policy_reason": "scheduler_lifecycle_core_prefers_replace",
        }
    if would_scheduler_action == "shadow_admit_reduced_risk":
        return {
            "would_order_entry_policy": "shadow_reduce_or_guarded_entry",
            "would_primary_order_type": "limit",
            "would_guarded_market_fallback": "guarded_market_reduced_risk_after_cost_proof",
            "would_queue_management": "admit_only_after_risk_reduction_gate",
            "would_cancel_replace_policy": "observe_only",
            "would_sizing_policy": "reduced_risk_shadow_required",
            "policy_reason": "scheduler_lifecycle_core_prefers_reduced_risk_admission",
        }
    if would_scheduler_action == "shadow_block_or_reject":
        return {
            "would_order_entry_policy": "shadow_skip_or_reject",
            "would_primary_order_type": "skip",
            "would_guarded_market_fallback": "none_until_rejection_repaired",
            "would_queue_management": "block_until_conflict_or_reject_gate_repaired",
            "would_cancel_replace_policy": "cancel_or_skip_shadow_required",
            "would_sizing_policy": "zero_risk_shadow_required",
            "policy_reason": "scheduler_lifecycle_core_prefers_block_or_reject",
        }
    return {
        "would_order_entry_policy": "shadow_limit_first_observe",
        "would_primary_order_type": "limit",
        "would_guarded_market_fallback": "guarded_market_after_fillability_cost_proof",
        "would_queue_management": (
            "observe_until_scheduler_lifecycle_control_proof"
            if dominant_control == "none"
            else f"observe_dominant_control_{dominant_control}"
        ),
        "would_cancel_replace_policy": "observe_only",
        "would_sizing_policy": "no_runtime_sizing_shadow_only",
        "policy_reason": "no_runtime_scheduler_lifecycle_control_selected",
    }


def build_ultimate_candidate_execution_policy_shadow(
    *,
    decision_window_id: str | None,
    shadow_selected_candidate_id: str | None,
    scheduler_action_class_counts: Mapping[str, Any],
    would_scheduler_action: str,
    dominant_scheduler_control: str,
    config: Mapping[str, Any] | UltimateCandidatePackageConfig | None = None,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Build a fail-closed order-entry architecture packet.

    The packet is intentionally not an execution command. It records the order
    type and lifecycle architecture that the 20 scheduler-lifecycle sleeves
    would inspect, plus the exact proof classes still required before any
    runtime order path can use it.
    """
    generated = generated_utc or _now_iso()
    package_config = (
        config
        if isinstance(config, UltimateCandidatePackageConfig)
        else UltimateCandidatePackageConfig.from_mapping(config)
    )
    counts = {str(key): _int(value) for key, value in scheduler_action_class_counts.items()}
    policy = _shadow_execution_policy_from_scheduler_action(
        would_scheduler_action,
        dominant_scheduler_control,
    )
    packet = {
        "schema": EXECUTION_POLICY_PACKET_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "decision_window_id": decision_window_id,
        "shadow_selected_candidate_id": shadow_selected_candidate_id,
        "enabled": package_config.enabled,
        "shadow_enabled": package_config.shadow_enabled,
        "replay_admission_enabled": package_config.replay_admission_enabled,
        "apply_to_execution": package_config.apply_to_execution,
        "live_activation_allowed_by_config": package_config.live_activation_allowed,
        "final_package_selected_by_config": package_config.final_package_selected,
        "policy_status": "shadow_execution_policy_ready_not_selectable",
        "would_scheduler_action": would_scheduler_action,
        "dominant_scheduler_control": dominant_scheduler_control,
        "scheduler_action_class_counts": counts,
        "selected_order_type_architecture": None,
        "execution_order_type_policy_selectable": False,
        "missed_fill_opportunity_cost_allowed": False,
        "limit_first_vs_guarded_market_comparison_allowed": False,
        "broker_real_expectancy_claim_allowed": False,
        "required_cost_source_fields": [
            "entry_spread",
            "entry_slippage",
            "commission_open_close",
            "swap_source",
            "close_side_all_in_cost",
            "cash_risk_basis",
        ],
        "required_fillability_source_fields": [
            "order_type",
            "pending_ticket",
            "pending_created_time_utc",
            "time_in_force",
            "cancel_replace_state",
            "fill_or_no_fill_outcome",
            "price_improvement_vs_missed_fill",
            "adverse_selection_after_fill",
        ],
        "broker_profile_support_required": ["FTMO", "redacted_account"],
        "proof_boundary": (
            "order_entry_policy_is_shadow_until_exact_denominator_clean_labels_"
            "fillability_cost_validation_and_wave_h_audit_select_final_package"
        ),
        "action": "shadow_no_order_type_selection_no_execution",
        "approved_risk_pct": 0.0,
        "order_calls": 0,
        "default_off": True,
        "shadow_only": True,
        **policy,
        **_runtime_closed_gates(),
    }
    packet["packet_hash_sha256"] = _packet_hash(packet)
    return packet


def _candidate_session_tokens(candidate: Mapping[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for key in ("session_bucket", "session", "route_session", "utc_hour_bucket"):
        raw = _text(candidate.get(key))
        if raw:
            tokens.add(raw)
            tokens.update(utc_hour_bucket_aliases(raw))
            if raw.startswith("moonshot_h"):
                tokens.add(raw.removeprefix("moonshot_"))
    decision_time = _text(
        candidate.get("decision_time_utc")
        or candidate.get("asof_utc")
        or candidate.get("timestamp_utc")
        or candidate.get("candle_close_utc")
        or candidate.get("source_asof_utc")
    )
    if decision_time:
        parsed = _parse_utc(decision_time)
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
    return _session_aliases(tokens)


_SESSION_ALIAS_MAP: dict[str, tuple[str, ...]] = {
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


def _session_aliases(values: Iterable[Any]) -> set[str]:
    aliases: set[str] = set()
    for value in values:
        raw = _text(value)
        if not raw:
            continue
        candidates = {raw, raw.lower()}
        for candidate in list(candidates):
            candidates.update(utc_hour_bucket_aliases(candidate))
            if candidate.startswith("moonshot_h"):
                candidates.add(candidate.removeprefix("moonshot_"))
            candidates.update(_SESSION_ALIAS_MAP.get(candidate, ()))
        aliases.update(candidates)
    return aliases


def _family_aliases(value: Any) -> set[str]:
    raw = _norm(value)
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


def _family_matches(left: Any, right: Any) -> bool:
    left_text = _text(left)
    right_text = _text(right)
    if not left_text or not right_text:
        return False
    if _sleeve_wildcard_token(left_text) or _sleeve_wildcard_token(right_text):
        return True
    return bool(_family_aliases(left_text) & _family_aliases(right_text))


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _candidate_id(candidate: Mapping[str, Any], index: int) -> str:
    for key in ("candidate_id", "row_bound_candidate_id", "original_candidate_id", "id"):
        value = _text(candidate.get(key))
        if value:
            return value
    return f"candidate:{index}"


def _match_sleeve(candidate: Mapping[str, Any], sleeve: Mapping[str, Any]) -> dict[str, Any] | None:
    candidate_symbol = _upper(candidate.get("symbol") or candidate.get("instrument"))
    candidate_side = _side(candidate.get("side") or candidate.get("direction"))
    candidate_framework = _text(candidate.get("framework") or candidate.get("strategy_family"))
    candidate_origin = _text(
        candidate.get("origin_family")
        or candidate.get("candidate_origin_family")
        or candidate.get("candidate_family")
    )
    candidate_sessions = _candidate_session_tokens(candidate)

    sleeve_symbols = {_upper(symbol) for symbol in _string_list(sleeve.get("symbols"))}
    sleeve_side = _side(sleeve.get("side"))
    sleeve_framework = _text(sleeve.get("framework"))
    sleeve_origin = _text(sleeve.get("origin_family"))
    sleeve_sessions = _session_aliases(_string_list(sleeve.get("session_buckets")))
    symbol_is_wildcard = any(_sleeve_wildcard_token(symbol) for symbol in sleeve_symbols)
    side_is_wildcard = _sleeve_wildcard_token(sleeve_side)
    session_is_wildcard = any(_sleeve_wildcard_token(session) for session in sleeve_sessions)

    if sleeve_symbols and not symbol_is_wildcard and (
        not candidate_symbol or candidate_symbol not in sleeve_symbols
    ):
        return None
    if sleeve_side and not side_is_wildcard and (
        not candidate_side or candidate_side != sleeve_side
    ):
        return None
    framework_is_wildcard = _sleeve_wildcard_token(sleeve_framework)
    if sleeve_framework and not framework_is_wildcard:
        if not candidate_framework or not _family_matches(candidate_framework, sleeve_framework):
            return None
    origin_is_wildcard = _sleeve_wildcard_token(sleeve_origin)
    if sleeve_origin and not origin_is_wildcard:
        if not candidate_origin or not _family_matches(candidate_origin, sleeve_origin):
            return None
    if sleeve_sessions and not session_is_wildcard and (
        not candidate_sessions or not (candidate_sessions & sleeve_sessions)
    ):
        return None

    criteria = {
        "symbol": bool(
            candidate_symbol
            and sleeve_symbols
            and (candidate_symbol in sleeve_symbols or symbol_is_wildcard)
        ),
        "side": bool(
            candidate_side
            and sleeve_side
            and (candidate_side == sleeve_side or side_is_wildcard)
        ),
        "framework": bool(
            candidate_framework
            and sleeve_framework
            and (
                _family_matches(candidate_framework, sleeve_framework)
                or framework_is_wildcard
            )
        ),
        "origin_family": bool(
            candidate_origin
            and sleeve_origin
            and (
                _family_matches(candidate_origin, sleeve_origin)
                or origin_is_wildcard
            )
        ),
        "session_bucket": bool(
            candidate_sessions
            and sleeve_sessions
            and (session_is_wildcard or candidate_sessions & sleeve_sessions)
        ),
    }
    match_score = (
        (0.30 if criteria["symbol"] else 0.0)
        + (0.20 if criteria["side"] else 0.0)
        + (0.20 if criteria["framework"] else 0.0)
        + (0.20 if criteria["origin_family"] else 0.0)
        + (0.10 if criteria["session_bucket"] else 0.0)
    )
    return {
        "sleeve_id": sleeve.get("sleeve_id"),
        "row_hash_sha256": sleeve.get("row_hash_sha256"),
        "sleeve_type": sleeve.get("sleeve_type"),
        "package_role": sleeve.get("package_role"),
        "framework": sleeve.get("framework"),
        "origin_family": sleeve.get("origin_family"),
        "side": sleeve.get("side"),
        "matched_criteria": criteria,
        "match_score": round(min(match_score, 1.0), 9),
        "selector_shadow_priority_score": sleeve.get("selector_shadow_priority_score"),
        "combined_source_bound_signal_r": sleeve.get("combined_source_bound_signal_r"),
        "scheduler_action_class_counts": dict(sleeve.get("scheduler_action_class_counts") or {}),
    }


def _package_role_counts(matches: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(_text(row.get("package_role")) for row in matches).items()))


def _match_role_count(role_counts: Mapping[str, Any], role: str) -> int:
    return _int(role_counts.get(role))


def _admission_sleeve_match_count(role_counts: Mapping[str, Any]) -> int:
    return _match_role_count(role_counts, "scheduler_lifecycle_core") + _match_role_count(
        role_counts,
        "promote_default_off_signal",
    )


def _role_disposition(role_counts: Mapping[str, Any], matched_count: int) -> str:
    if matched_count <= 0:
        return "no_sleeve_match"
    if _match_role_count(role_counts, "source_required_hold") > 0:
        return "source_required_hold"
    if _admission_sleeve_match_count(role_counts) <= 0:
        if _match_role_count(role_counts, "redesign_repair_candidate") > 0:
            return "redesign_repair_hold"
        if _match_role_count(role_counts, "avoid_failure_feature") > 0:
            return "avoid_feature_only_veto"
        return "non_admission_sleeve_match_only"
    if _match_role_count(role_counts, "avoid_failure_feature") > 0:
        return "admission_with_avoid_feature_risk_control"
    if _match_role_count(role_counts, "redesign_repair_candidate") > 0:
        return "admission_with_redesign_context"
    return "admission_candidate"


def evaluate_ultimate_candidate_selector_shadow(
    candidate: Mapping[str, Any],
    sleeve_registry_rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any] | UltimateCandidatePackageConfig | None = None,
    *,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_utc or _now_iso()
    package_config = (
        config
        if isinstance(config, UltimateCandidatePackageConfig)
        else UltimateCandidatePackageConfig.from_mapping(config)
    )
    matches = [
        match
        for sleeve in sleeve_registry_rows
        if (match := _match_sleeve(candidate, sleeve)) is not None
    ]
    matches.sort(
        key=lambda row: (
            _num(row.get("selector_shadow_priority_score")),
            _num(row.get("combined_source_bound_signal_r")),
            row.get("match_score") or 0.0,
            str(row.get("sleeve_id")),
        ),
        reverse=True,
    )
    role_counts = _package_role_counts(matches)
    admission_count = _admission_sleeve_match_count(role_counts)
    role_disposition = _role_disposition(role_counts, len(matches))
    score = round(
        sum(
            (_num(row.get("selector_shadow_priority_score")) * 0.65)
            + ((row.get("match_score") or 0.0) * 0.35)
            for row in matches
        ),
        9,
    )
    ev_r = _replay_candidate_ev(candidate)
    probability = _replay_candidate_probability(candidate)
    confidence = _replay_candidate_confidence(candidate)
    cost_r = _replay_candidate_cost(candidate)
    expected_net_r = _replay_candidate_expected_net(candidate)
    fill_probability = _replay_fill_probability(candidate)
    execution_fillability_atom = _replay_execution_fillability_atom(candidate)
    execution_fill_probability = execution_fillability_atom.get(
        "execution_fill_probability"
    )
    source_completeness = _replay_source_completeness(candidate)
    source_completeness_status = _replay_source_completeness_status(candidate)
    quality_field_sources = dict(
        _mapping(candidate.get("candidate_decision_quality_field_sources"))
    )
    confidence_missing_degraded_default = not _has_explicit_number(
        candidate,
        "candidate_confidence",
        "confidence",
        "scheduler_confidence",
        "confluence_confidence",
    )
    quality_optional_warnings = _string_list(
        candidate.get("candidate_decision_quality_optional_provenance_warnings")
    )
    if confidence_missing_degraded_default:
        quality_field_sources.setdefault(
            "confidence",
            REPLAY_MISSING_CONFIDENCE_SOURCE,
        )
        quality_optional_warnings = list(
            dict.fromkeys(
                [
                    *quality_optional_warnings,
                    REPLAY_MISSING_CONFIDENCE_WARNING,
                    REPLAY_MISSING_CONFIDENCE_DEGRADED_WARNING,
                ]
            )
        )
    quality_source_boundary = _text(
        candidate.get("candidate_decision_quality_source_boundary")
    )
    quality_alias_status = _normalized_replay_quality_alias_status(candidate)
    quality_alias_mismatches = _string_list(
        candidate.get("candidate_decision_quality_alias_mismatches")
    )
    quality_provenance_failures = _replay_quality_provenance_failures(candidate)
    source_bound_use_allowed = (
        admission_count > 0
        and role_disposition != "source_required_hold"
        and package_config.replay_admission_enabled
    )
    executable_use_allowed, executable_use_reason = (
        _replay_executable_authority_detail(
            candidate,
            source_bound_use_allowed=source_bound_use_allowed,
            source_completeness=source_completeness,
            source_completeness_status=source_completeness_status,
            require_order_path=False,
        )
    )
    packet = {
        "schema": SELECTOR_PACKET_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "candidate_id": _candidate_id(candidate, 1),
        "enabled": package_config.enabled,
        "shadow_enabled": package_config.shadow_enabled,
        "replay_admission_enabled": package_config.replay_admission_enabled,
        "apply_to_execution": package_config.apply_to_execution,
        "live_activation_allowed_by_config": package_config.live_activation_allowed,
        "final_package_selected_by_config": package_config.final_package_selected,
        "decision_status": (
            "shadow_sleeve_matches_found"
            if matches and package_config.shadow_enabled
            else "shadow_no_sleeve_match"
        ),
        "would_action": "shadow_rank_candidate" if matches else "shadow_source_required",
        "action": "shadow_no_execution",
        "matched_sleeve_count": len(matches),
        "matched_scheduler_lifecycle_merge_sleeves": sum(
            1 for row in matches if row.get("sleeve_type") == SCHEDULER_LIFECYCLE_MERGE_TYPE
        ),
        "matched_promote_default_off_sleeves": sum(
            1 for row in matches if row.get("sleeve_type") == PROMOTE_DEFAULT_OFF_TYPE
        ),
        "matched_package_role_counts": role_counts,
        "matched_sleeve_ids": [str(row.get("sleeve_id") or "") for row in matches],
        "admission_sleeve_match_count": admission_count,
        "non_admission_sleeve_match_count": max(0, len(matches) - admission_count),
        "avoid_failure_feature_match_count": _match_role_count(
            role_counts,
            "avoid_failure_feature",
        ),
        "redesign_repair_match_count": _match_role_count(
            role_counts,
            "redesign_repair_candidate",
        ),
        "source_required_hold_match_count": _match_role_count(
            role_counts,
            "source_required_hold",
        ),
        "role_disposition": role_disposition,
        "candidate_ev_r": round(ev_r, 9),
        "ev_r": round(ev_r, 9),
        "expectancy_r": round(ev_r, 9),
            "candidate_probability": round(probability, 9),
            "probability": round(probability, 9),
            "candidate_confidence": round(confidence, 9),
            "confidence": round(confidence, 9),
            "scheduler_confidence": round(confidence, 9),
            "expected_cost_r": round(cost_r, 9),
        "cost_r": round(cost_r, 9),
        "broker_calibrated_expected_cost_r": round(cost_r, 9),
        "broker_pretrade_cost_r": round(cost_r, 9),
            "candidate_expected_net_r": round(expected_net_r, 9),
            "expected_net_r": round(expected_net_r, 9),
            "candidate_fill_probability": round(fill_probability, 9),
            "fill_probability": round(fill_probability, 9),
            "entry_quality_fill_probability": round(fill_probability, 9),
            "execution_fill_probability": (
                round(execution_fill_probability, 9)
                if execution_fill_probability is not None
                else None
            ),
            "predecision_limit_fillability_probability": (
                round(execution_fill_probability, 9)
                if execution_fill_probability is not None
                else None
            ),
            "limit_fillability_probability": (
                round(execution_fill_probability, 9)
                if execution_fill_probability is not None
                else None
            ),
            **{
                key: value
                for key, value in execution_fillability_atom.items()
                if key
                not in {
                    "execution_fill_probability",
                    "predecision_limit_fillability_probability",
                    "limit_fillability_probability",
                }
            },
        "candidate_decision_quality_field_sources": quality_field_sources,
        "candidate_decision_quality_source_boundary": quality_source_boundary,
        "candidate_decision_quality_alias_status": quality_alias_status,
        "candidate_decision_quality_alias_mismatches": quality_alias_mismatches,
        "candidate_decision_quality_provenance_failures": list(
            quality_provenance_failures
        ),
        "candidate_decision_quality_optional_provenance_warnings": (
            quality_optional_warnings
        ),
        "confidence_missing_degraded_default_applied": (
            confidence_missing_degraded_default
        ),
        "source_completeness": round(source_completeness, 9),
        "source_bound_package_candidate_use_allowed": source_bound_use_allowed,
        "source_bound_package_candidate_use_allowed_reason": (
            "replay_admission_enabled_matched_admission_sleeve"
            if source_bound_use_allowed
            else "source_required_hold_role_disposition"
            if role_disposition == "source_required_hold"
            else "replay_admission_disabled"
            if admission_count > 0
            else "no_admission_sleeve_match"
        ),
        "package_replay_executable_candidate_use_allowed": executable_use_allowed,
        "package_replay_executable_candidate_use_allowed_reason": executable_use_reason,
        "replay_candidate_use_allowed_now": executable_use_allowed,
        "replay_candidate_use_allowed_now_reason": executable_use_reason,
        "selector_shadow_score": score,
        "matched_sleeves": matches,
        "ignored_forbidden_fields": _blocked_runtime_fields(candidate),
        "default_off": True,
        "shadow_only": True,
        **_runtime_closed_gates(),
    }
    packet["packet_hash_sha256"] = _packet_hash(packet)
    return packet


def schedule_ultimate_candidate_package_shadow(
    candidates: Sequence[Mapping[str, Any]],
    sleeve_registry_rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any] | UltimateCandidatePackageConfig | None = None,
    *,
    decision_window_id: str | None = None,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_utc or _now_iso()
    package_config = (
        config
        if isinstance(config, UltimateCandidatePackageConfig)
        else UltimateCandidatePackageConfig.from_mapping(config)
    )
    selector_packets = [
        evaluate_ultimate_candidate_selector_shadow(
            candidate,
            sleeve_registry_rows,
            package_config,
            generated_utc=generated,
        )
        for candidate in candidates
    ]
    rankable_packets = [
        row
        for row in selector_packets
        if row.get("source_bound_package_candidate_use_allowed") is True
    ]
    ranked = sorted(
        rankable_packets,
        key=lambda row: (
            _int(row.get("admission_sleeve_match_count")),
            _num(row.get("source_completeness")),
            _num(row.get("candidate_probability") or row.get("probability")),
            _num(row.get("expected_net_r")),
            _num(row.get("fill_probability")),
            _num(row.get("selector_shadow_score")),
            _int(row.get("matched_scheduler_lifecycle_merge_sleeves")),
            _int(row.get("matched_promote_default_off_sleeves")),
            str(row.get("candidate_id")),
        ),
        reverse=True,
    )
    shadow_selected = ranked[0] if ranked else None
    scheduler_counts: Counter[str] = Counter()
    if shadow_selected is not None:
        for match in shadow_selected.get("matched_sleeves") or []:
            if match.get("sleeve_type") != SCHEDULER_LIFECYCLE_MERGE_TYPE:
                continue
            scheduler_counts.update(
                {
                    str(key): _int(value)
                    for key, value in (match.get("scheduler_action_class_counts") or {}).items()
                }
            )
    counts = dict(sorted(scheduler_counts.items()))
    would_scheduler_action = _would_scheduler_action(counts)
    dominant_scheduler_control = _dominant_control(counts)
    execution_policy_shadow = build_ultimate_candidate_execution_policy_shadow(
        decision_window_id=decision_window_id,
        shadow_selected_candidate_id=(
            shadow_selected.get("candidate_id") if shadow_selected else None
        ),
        scheduler_action_class_counts=counts,
        would_scheduler_action=would_scheduler_action,
        dominant_scheduler_control=dominant_scheduler_control,
        config=package_config,
        generated_utc=generated,
    )
    packet = {
        "schema": SCHEDULER_PACKET_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "decision_window_id": decision_window_id,
        "enabled": package_config.enabled,
        "shadow_enabled": package_config.shadow_enabled,
        "apply_to_execution": package_config.apply_to_execution,
        "live_activation_allowed_by_config": package_config.live_activation_allowed,
        "final_package_selected_by_config": package_config.final_package_selected,
        "decision_status": (
            "shadow_scheduler_ranked_candidates"
            if ranked and package_config.shadow_enabled
            else "shadow_scheduler_no_candidates"
        ),
        "candidate_rows": len(candidates),
        "selector_packets": ranked,
        "shadow_selected_candidate_id": shadow_selected.get("candidate_id") if shadow_selected else None,
        "shadow_selected_expected_net_r": (
            shadow_selected.get("expected_net_r") if shadow_selected else None
        ),
        "shadow_selected_candidate_expected_net_r": (
            shadow_selected.get("candidate_expected_net_r") if shadow_selected else None
        ),
        "shadow_selected_candidate_probability": (
            shadow_selected.get("candidate_probability") if shadow_selected else None
        ),
        "shadow_selected_fill_probability": (
            shadow_selected.get("fill_probability") if shadow_selected else None
        ),
        "shadow_selected_source_completeness": (
            shadow_selected.get("source_completeness") if shadow_selected else None
        ),
        "shadow_selected_broker_pretrade_cost_r": (
            shadow_selected.get("broker_pretrade_cost_r") if shadow_selected else None
        ),
        "shadow_selected_broker_calibrated_expected_cost_r": (
            shadow_selected.get("broker_calibrated_expected_cost_r")
            if shadow_selected
            else None
        ),
        "shadow_selected_role_disposition": (
            shadow_selected.get("role_disposition") if shadow_selected else None
        ),
        "selected_candidate_id": None,
        "would_scheduler_action": would_scheduler_action,
        "dominant_scheduler_control": dominant_scheduler_control,
        "scheduler_action_class_counts": counts,
        "execution_policy_shadow": execution_policy_shadow,
        "action": "shadow_no_trade_no_execution",
        "approved_risk_pct": 0.0,
        "order_calls": 0,
        "default_off": True,
        "shadow_only": True,
        **_runtime_closed_gates(),
    }
    packet["packet_hash_sha256"] = _packet_hash(packet)
    return packet


def _canonical_decision_time(row: Mapping[str, Any]) -> str:
    return _text(
        row.get("decision_time_utc")
        or row.get("asof_utc")
        or row.get("candle_close_utc")
        or row.get("timestamp_utc")
    )


def _order_instance_key(candidate_id: str | None, decision_time: str | None) -> tuple[str, str] | None:
    candidate = _text(candidate_id)
    timestamp = _text(decision_time)
    if not candidate or not timestamp:
        return None
    return (candidate, timestamp)


def _build_replay_order_lookup(
    order_rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[tuple[str, str], Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    by_instance: dict[tuple[str, str], Mapping[str, Any]] = {}
    by_candidate_rows: dict[str, list[Mapping[str, Any]]] = {}
    for row in order_rows:
        candidate_id = _text(row.get("candidate_id"))
        if not candidate_id:
            continue
        decision_time = _canonical_decision_time(row)
        instance_key = _order_instance_key(candidate_id, decision_time)
        if instance_key is not None:
            by_instance[instance_key] = row
        by_candidate_rows.setdefault(candidate_id, []).append(row)
    unique_by_candidate = {
        candidate_id: rows[0]
        for candidate_id, rows in by_candidate_rows.items()
        if len(rows) == 1 and not _canonical_decision_time(rows[0])
    }
    return by_instance, unique_by_candidate


def _lookup_replay_order_row(
    *,
    candidate_id: str | None,
    decision_time: str | None,
    order_by_instance: Mapping[tuple[str, str], Mapping[str, Any]],
    unique_order_by_candidate: Mapping[str, Mapping[str, Any]],
) -> tuple[Mapping[str, Any] | None, str, str | None]:
    candidate = _text(candidate_id)
    timestamp = _text(decision_time)
    instance_key = _order_instance_key(candidate, timestamp)
    if instance_key is not None:
        order = order_by_instance.get(instance_key)
        if isinstance(order, Mapping):
            return order, "exact_candidate_time_join", f"{candidate}@@{timestamp}"
        return None, "exact_candidate_time_missing", f"{candidate}@@{timestamp}"
    if candidate:
        order = unique_order_by_candidate.get(candidate)
        if isinstance(order, Mapping):
            return order, "legacy_unique_candidate_id_join_without_time", candidate
        return None, "legacy_candidate_id_missing_or_nonunique", candidate
    return None, "candidate_id_missing", None


def _replay_order_path_authority_detail(
    order_row: Mapping[str, Any] | None,
    order_join_status: str,
) -> tuple[bool, str]:
    if not isinstance(order_row, Mapping):
        return False, f"replay_order_path_{order_join_status}"
    if order_join_status not in {
        "exact_candidate_time_join",
        "legacy_unique_candidate_id_join_without_time",
    }:
        return False, f"replay_order_path_{order_join_status}"
    if order_row.get("selected_package_non_executable_order_trade_diagnostic") is True:
        return False, "replay_order_path_non_executable_diagnostic"
    if order_row.get("execution_authority") is False:
        return False, "replay_order_path_execution_authority_false"
    if order_row.get("package_replay_executable_candidate_use_allowed") is False:
        return False, "replay_order_path_package_executable_false"
    order_status = _norm(order_row.get("order_status"))
    if order_status in {
        "source_required_lifecycle_gap_diagnostic_only",
        "guarded_market_fallback_contract_unmet",
    }:
        return False, f"replay_order_path_{order_status}"
    return True, f"replay_order_path_{order_join_status}"


def _replay_candidate_ev(row: Mapping[str, Any]) -> float:
    return _num(
        row.get("candidate_ev_r")
        if row.get("candidate_ev_r") is not None
        else row.get("ev_r", row.get("expectancy_r"))
    )


def _replay_candidate_probability(row: Mapping[str, Any]) -> float:
    return _num(
        row.get("candidate_probability")
        if row.get("candidate_probability") is not None
        else row.get("probability")
    )


def _has_explicit_number(row: Mapping[str, Any], *keys: str) -> bool:
    for key in keys:
        value = row.get(key)
        if value in (None, "") or isinstance(value, bool):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number == number and number not in (float("inf"), float("-inf")):
            return True
    return False


def _replay_candidate_confidence(row: Mapping[str, Any]) -> float:
    for key in (
        "candidate_confidence",
        "confidence",
        "scheduler_confidence",
        "confluence_confidence",
    ):
        if row.get(key) not in (None, ""):
            return _num(row.get(key))
    return REPLAY_MISSING_CONFIDENCE_DEFAULT


def _replay_candidate_cost(row: Mapping[str, Any]) -> float:
    return _num(
        row.get("broker_calibrated_expected_cost_r")
        if row.get("broker_calibrated_expected_cost_r") is not None
        else row.get("broker_pretrade_cost_r")
        if row.get("broker_pretrade_cost_r") is not None
        else row.get("expected_cost_r")
        if row.get("expected_cost_r") is not None
        else row.get("cost_r")
    )


def _replay_candidate_expected_net(row: Mapping[str, Any]) -> float:
    if row.get("candidate_expected_net_r") not in (None, ""):
        return _num(row.get("candidate_expected_net_r"))
    if row.get("expected_net_r") not in (None, ""):
        return _num(row.get("expected_net_r"))
    return _replay_candidate_ev(row) - _replay_candidate_cost(row)


def _replay_fill_probability(row: Mapping[str, Any]) -> float:
    if row.get("fill_probability") not in (None, ""):
        return _num(row.get("fill_probability"))
    if row.get("candidate_fill_probability") not in (None, ""):
        return _num(row.get("candidate_fill_probability"))
    if row.get("heuristic_fill_probability") not in (None, ""):
        return _num(row.get("heuristic_fill_probability"))
    fillability = row.get("predecision_limit_fillability")
    if isinstance(fillability, Mapping):
        return _num(fillability.get("fill_probability"))
    return 0.0


def _replay_execution_fill_probability(row: Mapping[str, Any]) -> float | None:
    for key in (
        "execution_fill_probability",
        "predecision_limit_fillability_probability",
        "limit_fillability_probability",
    ):
        if _has_explicit_number(row, key):
            return _num(row.get(key))
    fillability = row.get("predecision_limit_fillability")
    if isinstance(fillability, Mapping) and _has_explicit_number(
        fillability,
        "fill_probability",
        "expected_fill_probability",
        "limit_fill_probability",
    ):
        for key in ("fill_probability", "expected_fill_probability", "limit_fill_probability"):
            if _has_explicit_number(fillability, key):
                return _num(fillability.get(key))
    return None


def _replay_execution_fillability_atom(row: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve executable fillability only as a complete predecision atom."""

    nested = _mapping(row.get("predecision_limit_fillability"))
    value = (
        _num(row.get("execution_fill_probability"))
        if _has_explicit_number(row, "execution_fill_probability")
        else None
    )
    nested_value = None
    for key in (
        "fill_probability",
        "expected_fill_probability",
        "limit_fill_probability",
    ):
        if _has_explicit_number(nested, key):
            nested_value = _num(nested.get(key))
            break
    if value is None:
        value = nested_value
    value_claimed = bool(
        value is not None
        or _has_explicit_number(
            row,
            "predecision_limit_fillability_probability",
            "limit_fillability_probability",
        )
    )
    if value is None:
        return {
            "execution_fill_probability": None,
            "execution_fillability_atomic_failure": None,
            "execution_fillability_atomic_status": "not_present",
        }
    nested_matches = bool(
        nested_value is not None
        and float(value) == float(nested_value)
    )
    source = _text(row.get("execution_fill_probability_source"))
    source_time = row.get("execution_fill_probability_source_time_utc")
    source_boundary = row.get("execution_fill_probability_source_boundary")
    authority_class = _text(
        row.get("execution_fill_probability_authority_class")
    )
    if nested_matches:
        source = source or _text(
            nested.get("execution_fill_probability_source")
            or nested.get("fill_probability_source")
            or "predecision_limit_fillability.fill_probability"
        )
        source_time = source_time or nested.get(
            "current_price_source_time_utc"
        ) or nested.get("source_time_utc")
        source_boundary = source_boundary or nested.get(
            "current_price_source_boundary"
        ) or nested.get("source_boundary")
        authority_class = authority_class or _text(
            nested.get("execution_fill_probability_authority_class")
            or nested.get("fill_probability_authority_class")
            or "predecision_passive_limit_fillability_authority"
        )
    if not source or source_time in (None, "") or source_boundary in (None, ""):
        return {
            "execution_fill_probability": None,
            "execution_fillability_atomic_failure": (
                "execution_fillability_incomplete_value_only_not_propagated"
                if value_claimed
                else None
            ),
            "execution_fillability_atomic_status": "incomplete_not_executable",
        }
    clamped_value = max(0.0, min(1.0, float(value)))
    atom = {
        "execution_fill_probability": clamped_value,
        "predecision_limit_fillability_probability": clamped_value,
        "limit_fillability_probability": clamped_value,
        "execution_fill_probability_source": source,
        "execution_fill_probability_source_time_utc": source_time,
        "execution_fill_probability_source_boundary": source_boundary,
        "execution_fill_probability_authority_class": (
            authority_class or "predecision_execution_fillability_alias"
        ),
        "execution_fillability_atomic_surface": (
            row.get("execution_fillability_atomic_surface")
            or "ultimate_candidate_package.complete_predecision_fillability_atom"
        ),
        "execution_fillability_atomic_failure": None,
        "execution_fillability_atomic_conflicts": [],
        "execution_fillability_atomic_status": "complete",
    }
    for key in (
        "execution_fill_probability_authority_hash_sha256",
        "execution_fillability_signed_value_selected",
    ):
        if row.get(key) not in (None, ""):
            atom[key] = row.get(key)
    if nested:
        atom["predecision_limit_fillability"] = dict(nested)
    return atom


def _has_explicit_fill_probability(row: Mapping[str, Any]) -> bool:
    if _has_explicit_number(
        row,
        "fill_probability",
        "candidate_fill_probability",
        "heuristic_fill_probability",
    ):
        return True
    fillability = row.get("predecision_limit_fillability")
    if isinstance(fillability, Mapping):
        return _has_explicit_number(fillability, "fill_probability")
    return False


def _replay_source_completeness(row: Mapping[str, Any]) -> float:
    value = row.get("source_completeness")
    if isinstance(value, Mapping):
        if value.get("source_complete") is True:
            return 1.0
        if value.get("source_window_complete") is True:
            return 0.9
        return _num(value.get("score"), 0.0)
    if value in (None, ""):
        return REPLAY_MISSING_SOURCE_COMPLETENESS_DEFAULT if row else 0.0
    return _num(value, REPLAY_MISSING_SOURCE_COMPLETENESS_DEFAULT)


def _replay_source_completeness_status(row: Mapping[str, Any]) -> str:
    status = _text(row.get("source_completeness_status"))
    if status:
        return status
    if row.get("source_completeness") in (None, ""):
        return REPLAY_MISSING_SOURCE_COMPLETENESS_STATUS
    return "source_completeness_present"


def _predecision_no_outcome_boundary(value: Any) -> bool:
    text = _norm(value).replace("-", "_").replace(" ", "_")
    return bool("predecision" in text and "no_outcome" in text)


def _replay_quality_provenance_failures(row: Mapping[str, Any]) -> tuple[str, ...]:
    sources = _mapping(row.get("candidate_decision_quality_field_sources"))
    failures: list[str] = []
    for field in REPLAY_QUALITY_FIELDS:
        if not _text(sources.get(field)):
            failures.append(f"{field}_source_missing")
    boundary = _text(row.get("candidate_decision_quality_source_boundary"))
    if not boundary:
        failures.append("candidate_decision_quality_source_boundary_missing")
    elif not _predecision_no_outcome_boundary(boundary):
        failures.append("candidate_decision_quality_source_boundary_not_predecision")
    alias_status = _normalized_replay_quality_alias_status(row)
    if alias_status not in REPLAY_EXACT_QUALITY_ALIAS_STATUSES:
        failures.append(
            f"candidate_decision_quality_alias_status:{alias_status or 'missing'}"
        )
    for field in row.get("candidate_decision_quality_alias_mismatches") or ():
        field_text = _text(field)
        if field_text:
            failures.append(f"candidate_decision_quality_alias_mismatch:{field_text}")
    return tuple(dict.fromkeys(failures))


def _replay_quality_meaningful_provenance_failures(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    failures = _string_list(row.get("candidate_decision_quality_provenance_failures"))
    return tuple(
        failure
        for failure in failures
        if failure != REPLAY_ALIAS_STATUS_MATERIALIZED_FAILURE
    )


def _replay_quality_exactly_materialized_from_complete_sources(
    row: Mapping[str, Any],
) -> bool:
    sources = _mapping(row.get("candidate_decision_quality_field_sources"))
    if not all(_text(sources.get(field)) for field in REPLAY_QUALITY_FIELDS):
        return False
    boundary = _text(row.get("candidate_decision_quality_source_boundary"))
    if not _predecision_no_outcome_boundary(boundary):
        return False
    if _string_list(row.get("candidate_decision_quality_alias_mismatches")):
        return False
    return not _replay_quality_meaningful_provenance_failures(row)


def _normalized_replay_quality_alias_status(row: Mapping[str, Any]) -> str:
    alias_status = _norm(row.get("candidate_decision_quality_alias_status"))
    if alias_status in REPLAY_EXACT_QUALITY_ALIAS_STATUSES:
        return alias_status
    if (
        alias_status == "materialized"
        and _replay_quality_exactly_materialized_from_complete_sources(row)
    ):
        return REPLAY_MATERIALIZED_ALIAS_STATUS_UPGRADE
    return alias_status


def normalize_replay_quality_alias_status(row: Mapping[str, Any]) -> str:
    """Return the executable replay authority quality alias status for a row."""

    return _normalized_replay_quality_alias_status(row)


def replay_quality_provenance_failures(row: Mapping[str, Any]) -> tuple[str, ...]:
    """Return executable replay authority quality failures for a row."""

    return _replay_quality_provenance_failures(row)


def _replay_explicit_cost_packet_status(row: Mapping[str, Any]) -> str:
    return _upper(
        row.get("pretrade_cost_packet_status")
        or row.get("broker_net_cost_packet_status")
    )


def _replay_explicit_cost_source_gap_status(row: Mapping[str, Any]) -> str:
    return _text(row.get("cost_source_gap_status"))


def _replay_explicit_cost_authority(row: Mapping[str, Any]) -> str:
    return _text(row.get("cost_authority") or row.get("pretrade_cost_packet_authority"))


def _replay_executable_authority_detail(
    row: Mapping[str, Any],
    *,
    source_bound_use_allowed: bool,
    source_completeness: float,
    source_completeness_status: str,
    order_row: Mapping[str, Any] | None = None,
    order_join_status: str = "",
    require_order_path: bool = True,
) -> tuple[bool, str]:
    """Separate source-bound package admission from executable replay authority."""

    if not source_bound_use_allowed:
        return False, "source_bound_package_admission_not_allowed"
    quality_failures = _replay_quality_provenance_failures(row)
    if quality_failures:
        return (
            False,
            "candidate_decision_quality_provenance_missing:"
            + ",".join(quality_failures),
        )
    cost_status = _replay_explicit_cost_packet_status(row)
    if not cost_status:
        return False, "broker_cost_packet_status_missing"
    if cost_status != "PASSED":
        return False, f"broker_cost_packet_{cost_status.lower()}"
    cost_gap_status = _replay_explicit_cost_source_gap_status(row)
    if not cost_gap_status:
        return False, "broker_cost_source_gap_status_missing"
    if cost_gap_status != "source_bound_cost_authority_present":
        return False, f"broker_cost_source_gap_{cost_gap_status}"
    cost_authority = _replay_explicit_cost_authority(row)
    if not cost_authority:
        return False, "broker_cost_authority_missing"
    if cost_authority != "broker_calibrated_replay_cost":
        return False, f"broker_cost_authority_unexpected:{cost_authority}"
    if _truthy(row.get("candidate_cost_r_fallback_is_authority")):
        return False, "candidate_cost_r_fallback_authority_not_executable"
    if not _has_explicit_number(row, "candidate_expected_net_r", "expected_net_r"):
        return False, "expected_net_r_missing"
    if not _has_explicit_number(row, "candidate_probability", "probability"):
        return False, "candidate_probability_missing"
    if not _has_explicit_fill_probability(row):
        return False, "fill_probability_missing"
    if source_completeness < REPLAY_MIN_EXECUTABLE_SOURCE_COMPLETENESS:
        return (
            False,
            f"source_completeness_below_floor:{source_completeness:.6f}",
        )
    lowered_status = source_completeness_status.lower()
    if any(
        token in lowered_status
        for token in (
            "missing",
            "degraded",
            "gap",
            "source_required",
            "incomplete",
            "prospective_capture",
            "snapshot_incomplete",
        )
    ):
        return False, f"source_completeness_status_{source_completeness_status}"
    if not require_order_path:
        return True, "broker_cost_and_source_authority_executable"
    order_path_allowed, order_path_reason = _replay_order_path_authority_detail(
        order_row,
        order_join_status,
    )
    if not order_path_allowed:
        return False, order_path_reason
    return True, f"broker_cost_source_and_{order_path_reason}_executable"


def _replay_requested_risk_pct(row: Mapping[str, Any]) -> float:
    for key in (
        "risk_pct",
        "selected_cell_risk_pct",
        "requested_risk_pct",
        "scheduler_approved_risk_pct",
        "risk_per_trade_pct",
    ):
        if row.get(key) not in (None, ""):
            return max(0.0, _num(row.get(key)))
    return 0.0


def _replay_action_from_scheduler_action(would_scheduler_action: str) -> str:
    if would_scheduler_action == "shadow_queue_or_delay":
        return "replay_delay_queue_limit_first"
    if would_scheduler_action == "shadow_replace_pending":
        return "replay_cancel_replace_limit"
    if would_scheduler_action == "shadow_admit_reduced_risk":
        return "replay_admit_reduced_risk"
    if would_scheduler_action == "shadow_block_or_reject":
        return "replay_skip_or_reject"
    return "replay_admit_limit_first"


def _replay_action_for_role_disposition(
    base_action: str,
    *,
    role_disposition: str,
    role_counts: Mapping[str, Any],
    matched_count: int,
) -> str:
    if matched_count <= 0:
        return "replay_skip_no_sleeve_match"
    if role_disposition == "source_required_hold":
        return "replay_hold_source_required"
    if _admission_sleeve_match_count(role_counts) <= 0:
        if role_disposition == "redesign_repair_hold":
            return "replay_hold_redesign_required"
        if role_disposition == "avoid_feature_only_veto":
            return "replay_skip_avoid_feature_only"
        return "replay_skip_no_admission_sleeve"
    if (
        role_disposition == "admission_with_avoid_feature_risk_control"
        and base_action == "replay_admit_limit_first"
    ):
        return "replay_admit_reduced_risk"
    return base_action


def _replay_policy_from_action(
    replay_action: str,
    *,
    approved_risk_pct: float,
    missed_fill_opportunity_cost_r: float,
) -> dict[str, Any]:
    if replay_action == "replay_delay_queue_limit_first":
        selected_architecture = "limit_first_delay_queue"
        primary_order_type = "limit"
        fallback = "guarded_market_after_fillability_cost_proof"
        queue = "delay_or_queue_until_fillability_cost_gate"
        cancel_replace = "observe_then_replace_if_time_in_force_expires"
    elif replay_action == "replay_cancel_replace_limit":
        selected_architecture = "cancel_replace_limit"
        primary_order_type = "limit"
        fallback = "guarded_market_after_fillability_cost_proof"
        queue = "replace_pending_after_time_in_force_proof"
        cancel_replace = "cancel_replace_replay_authorized"
    elif replay_action == "replay_admit_reduced_risk":
        selected_architecture = "limit_first_reduced_risk"
        primary_order_type = "limit"
        fallback = "guarded_market_reduced_risk_after_cost_proof"
        queue = "admit_after_risk_reduction_gate"
        cancel_replace = "observe_only"
    elif replay_action in {
        "replay_skip_or_reject",
        "replay_skip_no_sleeve_match",
        "replay_skip_no_admission_sleeve",
        "replay_skip_avoid_feature_only",
        "replay_hold_redesign_required",
        "replay_hold_source_required",
    }:
        selected_architecture = "skip"
        primary_order_type = "skip"
        if replay_action == "replay_hold_source_required":
            fallback = "none_until_source_requirement_repaired"
            queue = "hold_until_source_requirement_repaired"
            cancel_replace = "cancel_or_hold_replay_authorized"
        elif replay_action == "replay_hold_redesign_required":
            fallback = "none_until_redesign_requirement_repaired"
            queue = "hold_until_redesign_requirement_repaired"
            cancel_replace = "cancel_or_hold_replay_authorized"
        elif replay_action == "replay_skip_avoid_feature_only":
            fallback = "none_for_avoid_feature_only_candidate"
            queue = "skip_avoid_feature_only_candidate"
            cancel_replace = "cancel_or_skip_replay_authorized"
        elif replay_action == "replay_skip_no_admission_sleeve":
            fallback = "none_without_scheduler_or_promote_admission_sleeve"
            queue = "skip_without_admission_sleeve"
            cancel_replace = "cancel_or_skip_replay_authorized"
        else:
            fallback = "none_until_rejection_repaired"
            queue = "skip_or_reject_for_replay_window"
            cancel_replace = "cancel_or_skip_replay_authorized"
        approved_risk_pct = 0.0
    else:
        selected_architecture = "limit_first_with_guarded_market_fallback"
        primary_order_type = "limit"
        fallback = "guarded_market_after_fillability_cost_proof"
        queue = "no_delay"
        cancel_replace = "observe_only"

    return {
        "policy_status": "replay_execution_policy_selected_not_live",
        "selected_order_type_architecture": selected_architecture,
        "execution_order_type_policy_selectable": True,
        "missed_fill_opportunity_cost_allowed": True,
        "limit_first_vs_guarded_market_comparison_allowed": True,
        "broker_real_expectancy_claim_allowed": False,
        "primary_order_type": primary_order_type,
        "guarded_market_fallback": fallback,
        "queue_management": queue,
        "cancel_replace_policy": cancel_replace,
        "approved_risk_pct": round(approved_risk_pct, 9),
        "missed_fill_opportunity_cost_r": round(max(0.0, missed_fill_opportunity_cost_r), 9),
        "simulated_order_decisions": 0 if selected_architecture == "skip" else 1,
        "order_calls": 0,
        "runtime_effect_now": False,
        "local_replay_effect_now": True,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
    }


_REPLAY_TERMINAL_RESULT_R_FIELDS = (
    "counterfactual_final_r",
    "final_r",
    "actual_r",
    "close_mark_r",
)

_REPLAY_EXPECTED_RESULT_DIAGNOSTIC_FIELDS = (
    "expectancy_r",
    "ev_r",
)


def _replay_result_r(row: Mapping[str, Any] | None) -> float | None:
    if not isinstance(row, Mapping):
        return None
    for key in _REPLAY_TERMINAL_RESULT_R_FIELDS:
        if row.get(key) not in (None, ""):
            return _num(row.get(key))
    return None


def _replay_expected_result_r_diagnostic(row: Mapping[str, Any] | None) -> float | None:
    if not isinstance(row, Mapping):
        return None
    for key in _REPLAY_EXPECTED_RESULT_DIAGNOSTIC_FIELDS:
        if row.get(key) not in (None, ""):
            return _num(row.get(key))
    return None


def _replay_result_authority_status(row: Mapping[str, Any] | None) -> str:
    if not isinstance(row, Mapping):
        return "missing_order_row"
    for key in _REPLAY_TERMINAL_RESULT_R_FIELDS:
        if row.get(key) not in (None, ""):
            return f"terminal_replay_result:{key}"
    for key in _REPLAY_EXPECTED_RESULT_DIAGNOSTIC_FIELDS:
        if row.get(key) not in (None, ""):
            return "expected_value_diagnostic_only_not_terminal_result"
    return "missing_terminal_replay_result"


def _replay_fill_status(row: Mapping[str, Any] | None) -> str | None:
    if not isinstance(row, Mapping):
        return None
    return _text(
        row.get("counterfactual_fill_status")
        or row.get("order_status")
        or row.get("broker_order_lifecycle_truth_satisfied")
    ) or None


_REPLAY_QUALITY_PROPAGATION_FIELDS = (
    "symbol",
    "side",
    "direction",
    "timeframe",
    "decision_timeframe",
    "framework",
    "origin_family",
    "candidate_ev_r",
    "ev_r",
    "expectancy_r",
    "candidate_probability",
    "probability",
    "candidate_confidence",
    "confidence",
    "scheduler_confidence",
    "expected_cost_r",
    "cost_r",
    "broker_calibrated_expected_cost_r",
    "broker_pretrade_cost_r",
    "candidate_expected_net_r",
    "expected_net_r",
    "candidate_fill_probability",
    "fill_probability",
    "entry_quality_fill_probability",
    "execution_fill_probability",
    "predecision_limit_fillability_probability",
    "limit_fillability_probability",
    "execution_fill_probability_source",
    "execution_fill_probability_source_time_utc",
    "execution_fill_probability_source_boundary",
    "execution_fill_probability_authority_class",
    "execution_fill_probability_authority_hash_sha256",
    "execution_fillability_signed_value_selected",
    "execution_fillability_atomic_surface",
    "execution_fillability_atomic_failure",
    "execution_fillability_atomic_conflicts",
    "execution_fillability_atomic_status",
    "predecision_limit_fillability",
    "source_completeness",
    "source_completeness_status",
    "candidate_decision_quality_field_sources",
    "candidate_decision_quality_source_boundary",
    "candidate_decision_quality_alias_status",
    "candidate_decision_quality_alias_mismatches",
    "candidate_decision_quality_provenance_failures",
    "source_boundary",
    "cost_authority",
    "pretrade_cost_packet_status",
    "cost_source_gap_status",
    "candidate_cost_r_fallback_is_authority",
    "package_replay_candidate_use_allowed",
    "package_replay_source_bound_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed_reason",
    "source_bound_package_candidate_use_allowed",
    "replay_candidate_use_allowed_now",
    "replay_candidate_use_allowed_now_reason",
    "selector_shadow_score",
    "package_replay_score",
    "matched_sleeve_count",
    "matched_scheduler_lifecycle_merge_sleeves",
    "matched_promote_default_off_sleeves",
    "matched_package_role_counts",
    "admission_sleeve_match_count",
    "non_admission_sleeve_match_count",
    "avoid_failure_feature_match_count",
    "redesign_repair_match_count",
    "source_required_hold_match_count",
    "role_disposition",
    "scheduler_action_class_counts",
    "dominant_scheduler_control",
    "would_scheduler_action",
    "base_replay_action",
    "requested_risk_pct",
    "replay_approved_risk_pct",
)


def _replay_quality_propagation_fields(
    row: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Copy candidate quality/source/cost fields into derived replay ledgers."""

    if not isinstance(row, Mapping):
        return {}
    out = {
        key: row.get(key)
        for key in _REPLAY_QUALITY_PROPAGATION_FIELDS
        if key in row
    }
    if "source_completeness_status" not in out:
        out["source_completeness_status"] = _replay_source_completeness_status(row)
    if "cost_authority" not in out:
        out["cost_authority"] = row.get("cost_authority") or (
            "broker_calibrated_replay_cost"
            if row.get("broker_calibrated_expected_cost_r") not in (None, "")
            else None
        )
    if "pretrade_cost_packet_status" not in out:
        out["pretrade_cost_packet_status"] = _replay_explicit_cost_packet_status(row) or None
    if "candidate_cost_r_fallback_is_authority" not in out:
        out["candidate_cost_r_fallback_is_authority"] = bool(
            row.get("candidate_cost_r_fallback_is_authority", False)
        )
    return out


def _blocked_reference_quality_fields(
    row: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Expose blocked-row quality only under an explicit diagnostic prefix."""

    if not isinstance(row, Mapping):
        return {}
    out = {
        f"blocked_reference_{key}": row.get(key)
        for key in _REPLAY_QUALITY_PROPAGATION_FIELDS
        if key in row
    }
    if "blocked_reference_source_completeness_status" not in out:
        out["blocked_reference_source_completeness_status"] = (
            _replay_source_completeness_status(row)
        )
    if "blocked_reference_cost_authority" not in out:
        out["blocked_reference_cost_authority"] = row.get("cost_authority") or (
            "broker_calibrated_replay_cost"
            if row.get("broker_calibrated_expected_cost_r") not in (None, "")
            else None
        )
    if "blocked_reference_pretrade_cost_packet_status" not in out:
        out["blocked_reference_pretrade_cost_packet_status"] = (
            _replay_explicit_cost_packet_status(row) or None
        )
    if "blocked_reference_candidate_cost_r_fallback_is_authority" not in out:
        out["blocked_reference_candidate_cost_r_fallback_is_authority"] = bool(
            row.get("candidate_cost_r_fallback_is_authority", False)
        )
    out["blocked_reference_candidate_id"] = row.get("candidate_id")
    out["blocked_reference_status"] = "blocked_non_executable"
    return out


def evaluate_ultimate_candidate_package_replay_authority(
    candidate_rows: Sequence[Mapping[str, Any]],
    sleeve_registry_rows: Sequence[Mapping[str, Any]],
    *,
    scorecard_rows: Sequence[Mapping[str, Any]] = (),
    order_rows: Sequence[Mapping[str, Any]] = (),
    source_namespace: str = "replay_authority",
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Evaluate the ultimate package with full local replay authority.

    This is deliberately separate from live/shadow packet authority. It can
    select candidates, order-type policy, replay risk, and opportunity-cost
    comparisons inside local replay ledgers, while broker/live/final gates stay
    closed.
    """
    generated = generated_utc or _now_iso()
    order_by_instance, unique_order_by_candidate = _build_replay_order_lookup(order_rows)
    candidate_records: list[dict[str, Any]] = []
    by_decision_time: dict[str, list[dict[str, Any]]] = {}
    for index, candidate in enumerate(candidate_rows, start=1):
        candidate_id = _candidate_id(candidate, index)
        decision_time = _canonical_decision_time(candidate)
        selector_packet = evaluate_ultimate_candidate_selector_shadow(
            candidate,
            sleeve_registry_rows,
            {
                "ultimate_candidate_package_enabled": True,
                "ultimate_candidate_package_shadow_enabled": True,
                "ultimate_candidate_package_apply_to_execution": True,
                "ultimate_candidate_package_live_activation_allowed": False,
                "ultimate_candidate_package_final_package_selected": False,
            },
            generated_utc=generated,
        )
        scheduler_counts: Counter[str] = Counter()
        for match in selector_packet.get("matched_sleeves") or []:
            if match.get("sleeve_type") == SCHEDULER_LIFECYCLE_MERGE_TYPE:
                scheduler_counts.update(
                    {
                        str(key): _int(value)
                        for key, value in (
                            match.get("scheduler_action_class_counts") or {}
                        ).items()
                    }
                )
        counts = dict(sorted(scheduler_counts.items()))
        would_scheduler_action = _would_scheduler_action(counts)
        dominant_scheduler_control = _dominant_control(counts)
        base_replay_action = _replay_action_from_scheduler_action(would_scheduler_action)
        role_counts = dict(selector_packet.get("matched_package_role_counts") or {})
        matched_count = _int(selector_packet.get("matched_sleeve_count"))
        admission_count = _int(selector_packet.get("admission_sleeve_match_count"))
        role_disposition = _text(selector_packet.get("role_disposition"))
        matched_sleeve_ids = [
            str(value)
            for value in (selector_packet.get("matched_sleeve_ids") or [])
            if _text(value)
        ]
        matched_member_axis_ids = _matched_member_axis_ids(
            selector_packet.get("matched_sleeves") or []
        )
        explicit_member_axis_ids = []
        for value in (
            *matched_member_axis_ids,
            *_string_list(candidate.get("matched_stable_member_axis_ids")),
            *_string_list(candidate.get("ultimate_package_matched_member_axis_ids")),
            *_string_list(candidate.get("selected_package_matched_member_axis_ids")),
        ):
            if value and value not in explicit_member_axis_ids:
                explicit_member_axis_ids.append(value)
        matched_source_axis_row_indexes = _string_list(
            candidate.get("matched_source_axis_row_indexes")
        )
        source_bound_fields = dict(_mapping(candidate.get("source_bound_fields")))
        replay_action = _replay_action_for_role_disposition(
            base_replay_action,
            role_disposition=role_disposition,
            role_counts=role_counts,
            matched_count=matched_count,
        )
        ev_r = _replay_candidate_ev(candidate)
        probability = _replay_candidate_probability(candidate)
        confidence = _replay_candidate_confidence(candidate)
        cost_r = _replay_candidate_cost(candidate)
        expected_net_r = _replay_candidate_expected_net(candidate)
        fill_probability = _replay_fill_probability(candidate)
        source_completeness = _replay_source_completeness(candidate)
        source_completeness_status = _replay_source_completeness_status(candidate)
        quality_field_sources = dict(
            _mapping(candidate.get("candidate_decision_quality_field_sources"))
        )
        quality_source_boundary = _text(
            candidate.get("candidate_decision_quality_source_boundary")
        )
        quality_alias_status = _normalized_replay_quality_alias_status(candidate)
        quality_alias_mismatches = _string_list(
            candidate.get("candidate_decision_quality_alias_mismatches")
        )
        quality_provenance_failures = _replay_quality_provenance_failures(candidate)
        requested_risk_pct = _replay_requested_risk_pct(candidate)
        candidate_use_allowed = admission_count > 0 and replay_action not in {
            "replay_hold_source_required",
            "replay_hold_redesign_required",
            "replay_skip_no_admission_sleeve",
            "replay_skip_avoid_feature_only",
            "replay_skip_no_sleeve_match",
        }
        order_row, order_join_status, order_join_key = _lookup_replay_order_row(
            candidate_id=candidate_id,
            decision_time=decision_time,
            order_by_instance=order_by_instance,
            unique_order_by_candidate=unique_order_by_candidate,
        )
        executable_use_allowed, executable_use_reason = (
            _replay_executable_authority_detail(
                candidate,
                source_bound_use_allowed=candidate_use_allowed,
                source_completeness=source_completeness,
                source_completeness_status=source_completeness_status,
                order_row=order_row,
                order_join_status=order_join_status,
            )
        )
        package_score = round(
            _num(selector_packet.get("selector_shadow_score"))
            + (0.55 * expected_net_r)
            + (0.45 * probability)
            + (0.20 * fill_probability)
            + (0.15 * source_completeness)
            + (
                0.20
                * _int(selector_packet.get("matched_scheduler_lifecycle_merge_sleeves"))
            )
            + (
                0.30
                * _int(selector_packet.get("matched_promote_default_off_sleeves"))
            ),
            9,
        )
        result_r = _replay_result_r(order_row)
        expected_result_r_diagnostic = _replay_expected_result_r_diagnostic(order_row)
        result_authority_status = _replay_result_authority_status(order_row)
        missed_fill_cost_r = 0.0
        fill_status = _replay_fill_status(order_row)
        if result_r is not None and fill_status and "no_fill" in fill_status:
            missed_fill_cost_r = max(result_r, 0.0)
        policy = _replay_policy_from_action(
            replay_action,
            approved_risk_pct=(
                requested_risk_pct
                if replay_action != "replay_admit_reduced_risk"
                else min(requested_risk_pct, max(0.1, requested_risk_pct * 0.5))
            ),
            missed_fill_opportunity_cost_r=missed_fill_cost_r,
        )
        record = {
            "schema": REPLAY_AUTHORITY_CANDIDATE_LEDGER_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "component": COMPONENT,
            "evidence_class": (
                "local_replay_authority_not_live_broker_authority"
            ),
            "result_use_status": "local_replay_scorecard_not_broker_real_result",
            "generated_utc": generated,
            "source_namespace": source_namespace,
            "row_number": index,
            "decision_time_utc": decision_time,
            "candidate_id": candidate_id,
            "symbol": _text(candidate.get("symbol") or candidate.get("instrument")),
            "side": _side(candidate.get("side") or candidate.get("direction")),
            "direction": _side(candidate.get("side") or candidate.get("direction")),
            "route_session": _text(candidate.get("route_session") or candidate.get("session")),
            "session_bucket": _text(
                candidate.get("session_bucket")
                or candidate.get("route_session")
                or candidate.get("session")
            ),
            "timeframe": _text(candidate.get("timeframe") or "M15"),
            "decision_timeframe": _text(candidate.get("decision_timeframe") or candidate.get("timeframe") or "M15"),
            "framework": _text(candidate.get("framework")),
            "origin_family": _text(
                candidate.get("origin_family") or candidate.get("candidate_origin_family")
            ),
            **_candidate_replay_geometry_fields(candidate),
            "package_replay_authority_enabled": True,
            "package_replay_candidate_use_allowed": candidate_use_allowed,
            "package_replay_source_bound_candidate_use_allowed": candidate_use_allowed,
            "package_replay_executable_candidate_use_allowed": executable_use_allowed,
            "package_replay_executable_candidate_use_allowed_reason": executable_use_reason,
            "source_bound_package_candidate_use_allowed": candidate_use_allowed,
            "replay_candidate_use_allowed_now": executable_use_allowed,
            "replay_candidate_use_allowed_now_reason": executable_use_reason,
            "selector_shadow_score": selector_packet.get("selector_shadow_score"),
            "package_replay_score": package_score,
            "matched_sleeve_count": matched_count,
            "matched_sleeve_ids": matched_sleeve_ids,
            "ultimate_package_matched_sleeve_ids": matched_sleeve_ids,
            "matched_stable_member_axis_ids": explicit_member_axis_ids,
            "ultimate_package_matched_member_axis_ids": explicit_member_axis_ids,
            "selected_package_matched_member_axis_ids": explicit_member_axis_ids,
            "matched_source_axis_row_indexes": matched_source_axis_row_indexes,
            "source_bound_fields": source_bound_fields,
            "matched_scheduler_lifecycle_merge_sleeves": selector_packet.get(
                "matched_scheduler_lifecycle_merge_sleeves"
            ),
            "matched_promote_default_off_sleeves": selector_packet.get(
                "matched_promote_default_off_sleeves"
            ),
            "matched_package_role_counts": role_counts,
            "admission_sleeve_match_count": admission_count,
            "non_admission_sleeve_match_count": _int(
                selector_packet.get("non_admission_sleeve_match_count")
            ),
            "avoid_failure_feature_match_count": _int(
                selector_packet.get("avoid_failure_feature_match_count")
            ),
            "redesign_repair_match_count": _int(
                selector_packet.get("redesign_repair_match_count")
            ),
            "source_required_hold_match_count": _int(
                selector_packet.get("source_required_hold_match_count")
            ),
            "role_disposition": role_disposition,
            "scheduler_action_class_counts": counts,
            "dominant_scheduler_control": dominant_scheduler_control,
            "would_scheduler_action": would_scheduler_action,
            "base_replay_action": base_replay_action,
            "replay_action": replay_action,
            "candidate_ev_r": round(ev_r, 9),
            "ev_r": round(ev_r, 9),
            "expectancy_r": round(ev_r, 9),
            "candidate_probability": round(probability, 9),
            "probability": round(probability, 9),
            "candidate_confidence": round(confidence, 9),
            "confidence": round(confidence, 9),
            "scheduler_confidence": round(confidence, 9),
            "expected_cost_r": round(cost_r, 9),
            "cost_r": round(cost_r, 9),
            "broker_calibrated_expected_cost_r": round(cost_r, 9),
            "broker_pretrade_cost_r": round(cost_r, 9),
            "candidate_expected_net_r": round(expected_net_r, 9),
            "expected_net_r": round(expected_net_r, 9),
            "candidate_fill_probability": round(fill_probability, 9),
            "fill_probability": round(fill_probability, 9),
            "model_limit_fill_probability_prior": round(fill_probability, 9),
            "fill_probability_authority_class": (
                "predecision_model_prior_not_fill_execution_authority"
            ),
            "fill_probability_source_bound_input_present": _has_explicit_fill_probability(
                candidate
            ),
            "source_completeness": round(source_completeness, 9),
            "source_completeness_status": source_completeness_status,
            "candidate_decision_quality_field_sources": quality_field_sources,
            "candidate_decision_quality_source_boundary": quality_source_boundary,
            "candidate_decision_quality_alias_status": quality_alias_status,
            "candidate_decision_quality_alias_mismatches": quality_alias_mismatches,
            "candidate_decision_quality_provenance_failures": list(
                quality_provenance_failures
            ),
            "source_boundary": _text(candidate.get("source_boundary")) or None,
            "cost_authority": _text(candidate.get("cost_authority")) or None,
            "pretrade_cost_packet_status": _replay_explicit_cost_packet_status(candidate) or None,
            "cost_source_gap_status": _replay_explicit_cost_source_gap_status(candidate) or None,
            "candidate_cost_r_fallback_is_authority": bool(
                candidate.get("candidate_cost_r_fallback_is_authority", False)
            ),
            "requested_risk_pct": round(requested_risk_pct, 9),
            "replay_approved_risk_pct": policy["approved_risk_pct"],
            "selected_order_type_architecture": policy[
                "selected_order_type_architecture"
            ],
            "execution_order_type_policy_selectable": policy[
                "execution_order_type_policy_selectable"
            ],
            "missed_fill_opportunity_cost_allowed": policy[
                "missed_fill_opportunity_cost_allowed"
            ],
            "missed_fill_opportunity_cost_r": policy[
                "missed_fill_opportunity_cost_r"
            ],
            "limit_first_vs_guarded_market_comparison_allowed": policy[
                "limit_first_vs_guarded_market_comparison_allowed"
            ],
            "replay_order_policy": policy,
            "replay_order_result_r": result_r,
            "replay_order_expected_r_diagnostic": expected_result_r_diagnostic,
            "replay_order_result_authority_status": result_authority_status,
            "replay_order_result_join_status": order_join_status,
            "replay_order_result_join_key": order_join_key,
            "replay_fill_status": fill_status,
            "selected_by_package_replay": False,
            "selected_candidate_id": None,
            "local_replay_effect_now": True,
            "runtime_effect_now": False,
            "live_execution_activation_allowed": False,
            "final_package_selection_allowed": False,
            "broker_account_order_history_deal_position_mutation_allowed": False,
            "broker_operation": False,
            "order_calls": 0,
            "paid_api_or_vendor_call": False,
            "ignored_forbidden_fields": _blocked_runtime_fields(candidate),
        }
        record["row_hash_sha256"] = _packet_hash(record)
        candidate_records.append(record)
        by_decision_time.setdefault(decision_time, []).append(record)

    selected_by_time: dict[str, dict[str, Any]] = {}
    for decision_time, rows in by_decision_time.items():
        eligible = [
            row
            for row in rows
            if row["package_replay_executable_candidate_use_allowed"]
        ]
        if not eligible:
            continue
        ranked = sorted(
            eligible,
            key=lambda row: (
                row.get("package_replay_score") or 0.0,
                row.get("source_completeness") or 0.0,
                row.get("candidate_probability") or row.get("probability") or 0.0,
                row.get("expected_net_r") or 0.0,
                row.get("fill_probability") or 0.0,
                str(row.get("candidate_id")),
            ),
            reverse=True,
        )
        if not ranked:
            continue
        selected = ranked[0]
        selected_by_time[decision_time] = selected
        for row in rows:
            row["selected_by_package_replay"] = (
                row.get("candidate_id") == selected.get("candidate_id")
            )
            row["selected_candidate_id"] = selected.get("candidate_id")
            row["row_hash_sha256"] = _packet_hash(row)

    scorecards: list[dict[str, Any]] = []
    order_policy_rows: list[dict[str, Any]] = []
    scorecard_by_time = {
        _canonical_decision_time(row): row
        for row in scorecard_rows
        if _canonical_decision_time(row)
    }
    all_times = sorted(set(scorecard_by_time) | set(by_decision_time))
    for index, decision_time in enumerate(all_times, start=1):
        rows_for_time = by_decision_time.get(decision_time, [])
        baseline = scorecard_by_time.get(decision_time, {})
        selected = selected_by_time.get(decision_time)
        blocked_reference = None
        if selected is None and rows_for_time:
            blocked_reference = sorted(
                rows_for_time,
                key=lambda row: (
                    row.get("package_replay_score") or 0.0,
                    row.get("expected_net_r") or 0.0,
                    row.get("fill_probability") or 0.0,
                    row.get("candidate_probability") or 0.0,
                    str(row.get("candidate_id")),
                ),
                reverse=True,
            )[0]
        baseline_candidate_id = _text(baseline.get("selected_candidate_id")) or None
        baseline_action = _text(baseline.get("selected_action_class")) or None
        package_candidate_id = selected.get("candidate_id") if selected else None
        if selected:
            package_action = selected.get("replay_action")
        elif blocked_reference:
            package_action = (
                blocked_reference.get("replay_action")
                or "replay_skip_no_admission_sleeve"
            )
        else:
            package_action = "replay_no_candidates"
        if selected is not None:
            package_quality_reference_status = "selected_executable_candidate"
            package_quality_fields = _replay_quality_propagation_fields(selected)
        elif blocked_reference is not None:
            package_quality_reference_status = "blocked_non_executable"
            package_quality_fields = _blocked_reference_quality_fields(blocked_reference)
        else:
            package_quality_reference_status = "no_package_candidate"
            package_quality_fields = {}
        (
            package_order_row,
            package_order_join_status,
            package_order_join_key,
        ) = _lookup_replay_order_row(
            candidate_id=_text(package_candidate_id),
            decision_time=decision_time,
            order_by_instance=order_by_instance,
            unique_order_by_candidate=unique_order_by_candidate,
        )
        (
            baseline_order_row,
            baseline_order_join_status,
            baseline_order_join_key,
        ) = _lookup_replay_order_row(
            candidate_id=_text(baseline_candidate_id),
            decision_time=decision_time,
            order_by_instance=order_by_instance,
            unique_order_by_candidate=unique_order_by_candidate,
        )
        package_result_r = _replay_result_r(package_order_row)
        baseline_result_r = _replay_result_r(baseline_order_row)
        package_expected_r_diagnostic = _replay_expected_result_r_diagnostic(
            package_order_row
        )
        baseline_expected_r_diagnostic = _replay_expected_result_r_diagnostic(
            baseline_order_row
        )
        package_result_authority_status = _replay_result_authority_status(
            package_order_row
        )
        baseline_result_authority_status = _replay_result_authority_status(
            baseline_order_row
        )
        delta_r = (
            round(package_result_r - baseline_result_r, 9)
            if package_result_r is not None and baseline_result_r is not None
            else None
        )
        missed_fill_cost = 0.0
        if package_result_r is not None and package_result_r > 0.0:
            if baseline_action in {None, "", "zero_trade"} or baseline_candidate_id != package_candidate_id:
                missed_fill_cost = package_result_r
        policy = (
            dict(selected.get("replay_order_policy") or {})
            if selected is not None
            else _replay_policy_from_action(
                (
                    package_action
                    if package_action != "replay_no_candidates"
                    else "replay_skip_or_reject"
                ),
                approved_risk_pct=0.0,
                missed_fill_opportunity_cost_r=0.0,
            )
        )
        policy["missed_fill_opportunity_cost_r"] = round(missed_fill_cost, 9)
        scorecard = {
            "schema": REPLAY_AUTHORITY_SCORECARD_LEDGER_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "component": COMPONENT,
            "evidence_class": (
                "local_replay_authority_not_live_broker_authority"
            ),
            "result_use_status": "local_replay_scorecard_not_broker_real_result",
            "generated_utc": generated,
            "source_namespace": source_namespace,
            "row_number": index,
            "decision_time_utc": decision_time,
            "candidate_rows": len(by_decision_time.get(decision_time, [])),
            "package_selected_candidate_id": package_candidate_id,
            "package_selected_action": package_action,
            "package_selected_score": (
                selected.get("package_replay_score") if selected else None
            ),
            "package_quality_reference_status": package_quality_reference_status,
            **package_quality_fields,
            "package_role_disposition": (
                selected.get("role_disposition")
                if selected
                else (
                    blocked_reference.get("role_disposition")
                    if blocked_reference
                    else "no_candidates"
                )
            ),
            "package_admission_sleeve_match_count": (
                selected.get("admission_sleeve_match_count") if selected else 0
            ),
            "package_non_admission_sleeve_match_count": (
                selected.get("non_admission_sleeve_match_count") if selected else 0
            ),
            "package_approved_risk_pct": policy.get("approved_risk_pct"),
            "baseline_selected_candidate_id": baseline_candidate_id,
            "baseline_selected_action_class": baseline_action,
            "package_replay_result_r": package_result_r,
            "baseline_replay_result_r": baseline_result_r,
            "package_expected_r_diagnostic": package_expected_r_diagnostic,
            "baseline_expected_r_diagnostic": baseline_expected_r_diagnostic,
            "package_replay_result_authority_status": (
                package_result_authority_status
            ),
            "baseline_replay_result_authority_status": (
                baseline_result_authority_status
            ),
            "package_vs_baseline_delta_r": delta_r,
            "package_replay_order_result_join_status": package_order_join_status,
            "package_replay_order_result_join_key": package_order_join_key,
            "baseline_replay_order_result_join_status": baseline_order_join_status,
            "baseline_replay_order_result_join_key": baseline_order_join_key,
            "missed_fill_opportunity_cost_r": round(missed_fill_cost, 9),
            "selected_order_type_architecture": policy.get(
                "selected_order_type_architecture"
            ),
            "execution_order_type_policy_selectable": True,
            "limit_first_vs_guarded_market_comparison_allowed": True,
            "package_replay_authority_enabled": True,
            "local_replay_effect_now": True,
            "runtime_effect_now": False,
            "live_execution_activation_allowed": False,
            "final_package_selection_allowed": False,
            "broker_account_order_history_deal_position_mutation_allowed": False,
            "broker_operation": False,
            "order_calls": 0,
            "paid_api_or_vendor_call": False,
        }
        scorecard["row_hash_sha256"] = _packet_hash(scorecard)
        scorecards.append(scorecard)
        order_policy = {
            "schema": REPLAY_AUTHORITY_ORDER_POLICY_LEDGER_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "component": COMPONENT,
            "evidence_class": (
                "local_replay_authority_not_live_broker_authority"
            ),
            "result_use_status": "local_replay_order_policy_not_broker_order",
            "generated_utc": generated,
            "source_namespace": source_namespace,
            "row_number": index,
            "decision_time_utc": decision_time,
            "candidate_id": package_candidate_id,
            "replay_action": package_action,
            "package_quality_reference_status": package_quality_reference_status,
            **package_quality_fields,
            **policy,
            "package_replay_authority_enabled": True,
            "runtime_effect_now": False,
            "live_execution_activation_allowed": False,
            "final_package_selection_allowed": False,
            "broker_account_order_history_deal_position_mutation_allowed": False,
            "broker_operation": False,
            "order_calls": 0,
            "paid_api_or_vendor_call": False,
        }
        order_policy["row_hash_sha256"] = _packet_hash(order_policy)
        order_policy_rows.append(order_policy)

    summary = {
        "schema": "gtos.final_moonshot.ultimate_candidate_package.replay_authority_summary.v1",
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": "local_replay_authority_not_live_broker_authority",
        "result_use_status": "local_replay_scorecard_not_broker_real_result",
        "generated_utc": generated,
        "source_namespace": source_namespace,
        "package_replay_authority_enabled": True,
        "candidate_rows": len(candidate_records),
        "decision_window_rows": len(scorecards),
        "order_policy_rows": len(order_policy_rows),
        "selected_candidate_rows": sum(
            1 for row in candidate_records if row.get("selected_by_package_replay")
        ),
        "source_bound_candidate_use_allowed_rows": sum(
            1
            for row in candidate_records
            if row.get("source_bound_package_candidate_use_allowed")
        ),
        "executable_candidate_use_allowed_rows": sum(
            1
            for row in candidate_records
            if row.get("package_replay_executable_candidate_use_allowed")
        ),
        "executable_candidate_use_allowed_reason_counts": dict(
            sorted(
                Counter(
                    row.get("package_replay_executable_candidate_use_allowed_reason")
                    for row in candidate_records
                ).items()
            )
        ),
        "matched_candidate_rows": sum(
            1 for row in candidate_records if row.get("matched_sleeve_count")
        ),
        "candidate_rows_with_admission_sleeve_match": sum(
            1 for row in candidate_records if row.get("admission_sleeve_match_count")
        ),
        "candidate_rows_with_only_non_admission_sleeve_match": sum(
            1
            for row in candidate_records
            if row.get("matched_sleeve_count")
            and not row.get("admission_sleeve_match_count")
        ),
        "scheduler_lifecycle_matched_candidate_rows": sum(
            1
            for row in candidate_records
            if row.get("matched_scheduler_lifecycle_merge_sleeves")
        ),
        "promote_default_off_matched_candidate_rows": sum(
            1 for row in candidate_records if row.get("matched_promote_default_off_sleeves")
        ),
        "scorecards_with_package_result_r": sum(
            1 for row in scorecards if row.get("package_replay_result_r") is not None
        ),
        "scorecards_with_package_vs_baseline_delta_r": sum(
            1 for row in scorecards if row.get("package_vs_baseline_delta_r") is not None
        ),
        "missed_fill_opportunity_cost_r_sum": round(
            sum(_num(row.get("missed_fill_opportunity_cost_r")) for row in scorecards),
            9,
        ),
        "selected_order_type_architecture_counts": dict(
            sorted(
                Counter(
                    row.get("selected_order_type_architecture")
                    for row in order_policy_rows
                ).items()
            )
        ),
        "role_disposition_counts": dict(
            sorted(Counter(row.get("role_disposition") for row in candidate_records).items())
        ),
        "local_replay_effect_now": True,
        "runtime_effect_now": False,
        "live_execution_activation_allowed": False,
        "final_package_selection_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
        "broker_operation": False,
        "order_calls": 0,
        "paid_api_or_vendor_call": False,
    }
    summary["packet_hash_sha256"] = _packet_hash(summary)
    return {
        "summary": summary,
        "candidate_rows": candidate_records,
        "scorecard_rows": scorecards,
        "order_policy_rows": order_policy_rows,
    }


def verify_ultimate_candidate_package_surface(
    surface: Mapping[str, Any],
    sleeve_registry_rows: Sequence[Mapping[str, Any]],
    selector_shadow_rows: Sequence[Mapping[str, Any]],
    scheduler_shadow_rows: Sequence[Mapping[str, Any]],
    *,
    generated_utc: str | None = None,
    expected_sleeve_rows: int = 82,
    expected_scheduler_lifecycle_merge_sleeves: int = 20,
    expected_promote_default_off_sleeves: int = 3,
) -> dict[str, Any]:
    generated = generated_utc or _now_iso()
    issues: list[str] = []
    type_counts = Counter(row.get("sleeve_type") for row in sleeve_registry_rows)

    if surface.get("schema") != SURFACE_SCHEMA:
        issues.append("surface_schema_mismatch")
    if surface.get("component") != COMPONENT:
        issues.append("surface_component_mismatch")
    if len(sleeve_registry_rows) != expected_sleeve_rows:
        issues.append(f"sleeve_registry_row_count_mismatch:{len(sleeve_registry_rows)}")
    if len(selector_shadow_rows) != len(sleeve_registry_rows):
        issues.append("selector_shadow_row_count_mismatch")
    if type_counts.get(SCHEDULER_LIFECYCLE_MERGE_TYPE, 0) != expected_scheduler_lifecycle_merge_sleeves:
        issues.append("scheduler_lifecycle_merge_sleeve_count_mismatch")
    if type_counts.get(PROMOTE_DEFAULT_OFF_TYPE, 0) != expected_promote_default_off_sleeves:
        issues.append("promote_default_off_sleeve_count_mismatch")
    if len(scheduler_shadow_rows) != expected_scheduler_lifecycle_merge_sleeves:
        issues.append("scheduler_shadow_row_count_mismatch")
    if surface.get("final_package_selected") is not False:
        issues.append("final_package_selected_unexpected")
    if surface.get("selector_surface_ready") is not True:
        issues.append("selector_surface_not_ready")
    if surface.get("scheduler_surface_ready") is not True:
        issues.append("scheduler_surface_not_ready")
    for field, expected in (
        ("compressed_sleeve_rows", len(sleeve_registry_rows)),
        ("selector_shadow_ledger_rows", len(selector_shadow_rows)),
        ("scheduler_shadow_ledger_rows", len(scheduler_shadow_rows)),
        ("scheduler_lifecycle_merge_sleeves", type_counts.get(SCHEDULER_LIFECYCLE_MERGE_TYPE, 0)),
        ("promote_default_off_signal_sleeves", type_counts.get(PROMOTE_DEFAULT_OFF_TYPE, 0)),
    ):
        if surface.get(field) != expected:
            issues.append(f"surface_{field}_mismatch:{surface.get(field)}")
    for index, row in enumerate(sleeve_registry_rows, start=1):
        if row.get("schema") != SLEEVE_REGISTRY_SCHEMA:
            issues.append(f"sleeve_registry_schema_mismatch:{index}")
        if row.get("row_number") != index:
            issues.append(f"sleeve_registry_row_number_mismatch:{index}")
        _append_gate_issues(issues, row, f"sleeve_registry:{index}")
    for index, row in enumerate(selector_shadow_rows, start=1):
        if row.get("schema") != SELECTOR_SHADOW_LEDGER_SCHEMA:
            issues.append(f"selector_shadow_schema_mismatch:{index}")
        if row.get("row_number") != index:
            issues.append(f"selector_shadow_row_number_mismatch:{index}")
        _append_gate_issues(issues, row, f"selector_shadow:{index}")
    for index, row in enumerate(scheduler_shadow_rows, start=1):
        if row.get("schema") != SCHEDULER_SHADOW_LEDGER_SCHEMA:
            issues.append(f"scheduler_shadow_schema_mismatch:{index}")
        if row.get("sleeve_type") != SCHEDULER_LIFECYCLE_MERGE_TYPE:
            issues.append(f"scheduler_shadow_non_core_sleeve:{index}")
        _append_gate_issues(issues, row, f"scheduler_shadow:{index}")
    _append_gate_issues(issues, surface, "surface")

    result = {
        "schema": VERIFICATION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "compressed_sleeve_rows": len(sleeve_registry_rows),
        "scheduler_lifecycle_merge_sleeves": type_counts.get(SCHEDULER_LIFECYCLE_MERGE_TYPE, 0),
        "promote_default_off_signal_sleeves": type_counts.get(PROMOTE_DEFAULT_OFF_TYPE, 0),
        "selector_shadow_ledger_rows": len(selector_shadow_rows),
        "scheduler_shadow_ledger_rows": len(scheduler_shadow_rows),
        "final_package_selected": False,
        "default_off": True,
        "shadow_only": True,
        **_runtime_closed_gates(),
    }
    result["packet_hash_sha256"] = _packet_hash(result)
    return result


def _append_gate_issues(issues: list[str], row: Mapping[str, Any], prefix: str) -> None:
    for gate in (
        "runtime_effect_now",
        "candidate_use_allowed_now",
        "selected_package_denominator_use_allowed",
        "denominator_expansion_allowed",
        "clean_label_use_allowed",
        "training_use_allowed",
        "model_training_allowed",
        "final_package_selection_allowed",
        "deployment_dossier_allowed",
        "vps_handoff_allowed",
        "live_execution_activation_allowed",
        "broker_account_order_history_deal_position_mutation_allowed",
        "broker_operation",
        "paid_api_or_vendor_call",
    ):
        if row.get(gate) is not False:
            issues.append(f"{prefix}_{gate}_unexpected")
    if row.get("order_calls") not in (False, 0):
        issues.append(f"{prefix}_order_calls_unexpected")
