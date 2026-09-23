"""Default-off V3 package runtime helpers.

The functions in this module load compact V3 package artifacts, record
provenance, and build decision packets for Selector V3, Scheduler V3, and
Execution Policy V3. They do not call MT5, do not place/modify/close orders,
do not call network/vendor APIs, and keep runtime effect disabled unless both
the caller and the package explicitly allow it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.research.moonshot_default_off_policy_router import (
    DEFAULT_POLICY,
    EXECUTION_POLICY_IDS,
    PARTIAL_BE_RUNNER_POLICY,
    SUPPORTED_LIVE_EXECUTION_POLICIES,
    execution_policy_id_for,
)
from src.research.moonshot_selector_v3_default_off import apply_selector_v3_default_off


SELECTOR_V3_PACKAGE_PATH = Path(
    "research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/"
    "SELECTOR_V3_DEFAULT_OFF_PACKAGE.json"
)
SELECTOR_V3_PACKET_SCHEMA_PATH = Path(
    "research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/"
    "SELECTOR_V3_RUNTIME_PACKET_SCHEMA.json"
)
SCHEDULER_V3_PACKAGE_PATH = Path(
    "research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/"
    "SCHEDULER_V3_DEFAULT_OFF_PACKAGE.json"
)
EXECUTION_POLICY_V3_PACKAGE_PATH = Path(
    "research/operations/vnext_absolute_moonshot_execution_policy_v3_2026_06_01/"
    "V3_DEFAULT_OFF_EXECUTION_POLICY_PACKAGE.json"
)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _float(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class V3PackageProvenance:
    package_role: str
    path: str
    sha256: str
    size_bytes: int
    package_id: str | None
    route_id: str | None
    schema_version: str | None
    generated_at_utc: str | None
    enabled_by_default: bool
    apply_to_execution_default: bool
    live_activation_allowed_by_package: bool
    runtime_effect_now: bool
    runtime_effect_boundary: str | None
    owner_approval_required_for_live_use: bool

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class V3RuntimePackage:
    role: str
    data: Mapping[str, Any]
    provenance: V3PackageProvenance


def load_v3_package(path: Path, *, role: str) -> V3RuntimePackage:
    data = json.loads(path.read_text(encoding="utf-8"))
    provenance = V3PackageProvenance(
        package_role=role,
        path=str(path),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        package_id=data.get("package_id"),
        route_id=data.get("route_id"),
        schema_version=data.get("schema_version"),
        generated_at_utc=data.get("generated_at_utc"),
        enabled_by_default=_truthy(data.get("enabled_by_default")),
        apply_to_execution_default=_truthy(data.get("apply_to_execution_default")),
        live_activation_allowed_by_package=_truthy(
            data.get("live_activation_allowed_by_this_package")
            or data.get("live_activation_allowed_by_this_schema")
        ),
        runtime_effect_now=_truthy(data.get("runtime_effect_now")),
        runtime_effect_boundary=data.get("runtime_effect_boundary"),
        owner_approval_required_for_live_use=_truthy(
            data.get("owner_approval_required_for_live_use")
            or data.get("owner_approval_required_for_activation")
        ),
    )
    return V3RuntimePackage(role=role, data=data, provenance=provenance)


def load_v3_runtime_package_set(root: Path | str = Path(".")) -> dict[str, V3RuntimePackage]:
    base = Path(root)
    return {
        "selector_v3": load_v3_package(base / SELECTOR_V3_PACKAGE_PATH, role="selector_v3"),
        "selector_v3_packet_schema": load_v3_package(
            base / SELECTOR_V3_PACKET_SCHEMA_PATH,
            role="selector_v3_packet_schema",
        ),
        "scheduler_v3": load_v3_package(base / SCHEDULER_V3_PACKAGE_PATH, role="scheduler_v3"),
        "execution_policy_v3": load_v3_package(
            base / EXECUTION_POLICY_V3_PACKAGE_PATH,
            role="execution_policy_v3",
        ),
    }


def build_selector_v3_packet(
    event: Mapping[str, Any],
    package: V3RuntimePackage,
    *,
    enabled: bool = False,
    apply_to_execution: bool = False,
) -> dict[str, Any]:
    decision = apply_selector_v3_default_off(
        event,
        package.data,
        enabled=enabled,
        apply_to_execution=apply_to_execution,
    ).to_record()
    return {
        "schema_version": "selector_v3_runtime_packet_record_v1",
        "component": "selector_v3",
        "package_provenance": package.provenance.to_record(),
        "decision": decision,
        "runtime_effect_now": bool(decision.get("runtime_effect_now")),
        "broker_operation": False,
        "order_calls": 0,
        "paid_api_or_vendor_call": False,
    }


def scheduler_v3_missing_money_risk_fields(
    account_state: Mapping[str, Any],
    package: V3RuntimePackage,
) -> tuple[str, ...]:
    required = package.data.get("required_money_risk_fields") or ()
    return tuple(field for field in required if account_state.get(field) in (None, ""))


@dataclass(frozen=True)
class SchedulerV3Decision:
    enabled: bool
    apply_to_execution: bool
    action_class: str
    decision_status: str
    missing_money_risk_fields: tuple[str, ...] = ()
    reason: str | None = None
    runtime_effect_now: bool = False
    broker_operation: bool = False
    paid_api_or_vendor_call: bool = False
    owner_approval_required: bool = True
    money_risk_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["missing_money_risk_fields"] = list(self.missing_money_risk_fields)
        return record


def apply_scheduler_v3_default_off(
    account_state: Mapping[str, Any],
    package: V3RuntimePackage,
    *,
    enabled: bool = False,
    apply_to_execution: bool = False,
) -> SchedulerV3Decision:
    missing = scheduler_v3_missing_money_risk_fields(account_state, package)
    snapshot = {
        field: account_state.get(field)
        for field in (
            "account_balance",
            "account_equity",
            "day_start_baseline",
            "realized_broker_or_proxy_pnl",
            "open_worst_case_sl_risk_pct",
            "pending_worst_case_sl_risk_pct",
            "new_trade_worst_case_risk_pct",
            "approved_trade_risk_pct",
            "selected_cell_risk_pct",
            "portfolio_ceiling_pct",
            "correlation_cluster_ceiling_pct",
            "daily_overlay_limit_pct",
            "external_daily_loss_limit_pct",
            "external_total_loss_limit_pct",
        )
    }
    if not enabled:
        return SchedulerV3Decision(
            enabled=False,
            apply_to_execution=False,
            action_class="default_off_disabled",
            decision_status="disabled_default_off",
            missing_money_risk_fields=missing,
            reason="scheduler_v3_default_off_config_disabled",
            money_risk_snapshot=snapshot,
        )
    if missing:
        return SchedulerV3Decision(
            enabled=True,
            apply_to_execution=bool(apply_to_execution),
            action_class="require_source",
            decision_status="money_risk_source_required",
            missing_money_risk_fields=missing,
            reason="scheduler_v3_required_money_risk_fields_missing",
            money_risk_snapshot=snapshot,
        )

    open_risk = _float(account_state.get("open_worst_case_sl_risk_pct")) or 0.0
    pending_risk = _float(account_state.get("pending_worst_case_sl_risk_pct")) or 0.0
    new_risk = _float(account_state.get("new_trade_worst_case_risk_pct")) or 0.0
    selected_cell_risk = _float(account_state.get("selected_cell_risk_pct"))
    portfolio_ceiling = _float(account_state.get("portfolio_ceiling_pct"))
    cluster_ceiling = _float(account_state.get("correlation_cluster_ceiling_pct"))
    same_symbol_risk = _float(account_state.get("same_symbol_risk_pct_before")) or 0.0
    cluster_risk = _float(account_state.get("correlated_cluster_risk_pct_before")) or 0.0
    total_after = open_risk + pending_risk + new_risk
    actual_sl_status = _text(account_state.get("actual_sl_distance_status")).lower()
    lot_status = _text(account_state.get("lot_contract_geometry_status")).lower()
    drawdown_state = _text(account_state.get("drawdown_compression_state")).lower()

    if new_risk <= 0:
        action = "reject"
        status = "new_trade_risk_not_positive"
    elif "missing" in actual_sl_status or "invalid" in actual_sl_status:
        action = "reject"
        status = "actual_sl_distance_not_verified"
    elif "missing" in lot_status or "invalid" in lot_status:
        action = "reject"
        status = "lot_contract_geometry_not_verified"
    elif portfolio_ceiling is not None and total_after > portfolio_ceiling:
        action = "reject"
        status = "portfolio_worst_case_risk_exceeds_ceiling"
    elif cluster_ceiling is not None and cluster_risk + new_risk > cluster_ceiling:
        action = "conflict_net"
        status = "correlated_cluster_risk_exceeds_ceiling"
    elif selected_cell_risk is not None and new_risk > selected_cell_risk:
        action = "admit_reduced_risk"
        status = "new_risk_reduced_to_selected_cell_authority"
    elif "compressed" in drawdown_state or "reduce" in drawdown_state:
        action = "admit_reduced_risk"
        status = "drawdown_compression_requires_reduced_risk"
    elif same_symbol_risk > 0:
        action = "queue"
        status = "same_symbol_existing_risk_requires_queue_or_replace_review"
    else:
        action = "admit"
        status = "account_money_risk_admits_candidate"

    package_allows_live = package.provenance.live_activation_allowed_by_package
    runtime_effect = bool(enabled and apply_to_execution and package_allows_live and action in {"admit", "admit_reduced_risk"})
    return SchedulerV3Decision(
        enabled=True,
        apply_to_execution=bool(apply_to_execution),
        action_class=action,
        decision_status=(
            status if package_allows_live else f"{status}_live_activation_not_allowed_by_package"
        ),
        missing_money_risk_fields=(),
        reason="scheduler_v3_money_risk_authority_default_off_package",
        runtime_effect_now=runtime_effect,
        money_risk_snapshot={**snapshot, "total_worst_case_risk_pct_after": total_after},
    )


def build_scheduler_v3_packet(
    account_state: Mapping[str, Any],
    package: V3RuntimePackage,
    *,
    enabled: bool = False,
    apply_to_execution: bool = False,
) -> dict[str, Any]:
    decision = apply_scheduler_v3_default_off(
        account_state,
        package,
        enabled=enabled,
        apply_to_execution=apply_to_execution,
    ).to_record()
    return {
        "schema_version": "scheduler_v3_runtime_packet_record_v1",
        "component": "scheduler_v3",
        "package_provenance": package.provenance.to_record(),
        "decision": decision,
        "runtime_effect_now": bool(decision.get("runtime_effect_now")),
        "broker_operation": False,
        "order_calls": 0,
        "paid_api_or_vendor_call": False,
    }


@dataclass(frozen=True)
class ExecutionPolicyV3Decision:
    enabled: bool
    apply_to_execution: bool
    selected_policy: str
    execution_policy_id: str | None
    decision_status: str
    lifecycle_source_status: str
    ticket_bound_lifecycle_required: bool
    supported_live_policy: bool
    runtime_effect_now: bool = False
    broker_operation: bool = False
    paid_api_or_vendor_call: bool = False
    owner_approval_required: bool = True
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def apply_execution_policy_v3_default_off(
    context: Mapping[str, Any],
    package: V3RuntimePackage,
    *,
    enabled: bool = False,
    apply_to_execution: bool = False,
) -> ExecutionPolicyV3Decision:
    raw_requested = _text(
        context.get("v3_requested_policy")
        or context.get("selected_policy")
        or context.get("current_policy")
        or DEFAULT_POLICY
    ).strip().lower()
    requested = raw_requested
    if requested in {"", "fixed_1_5r", "j46", "j49", "baseline_fixed"}:
        requested = DEFAULT_POLICY
    requested_supported = raw_requested in SUPPORTED_LIVE_EXECUTION_POLICIES
    selected = requested if requested_supported else DEFAULT_POLICY
    supported = selected in SUPPORTED_LIVE_EXECUTION_POLICIES
    lifecycle_source_complete = _truthy(
        context.get("broker_lifecycle_source_complete")
        or context.get("ticket_bound_lifecycle_source_complete")
    )
    lifecycle_status = "complete" if lifecycle_source_complete else "source_required"
    ticket_required = selected in {
        PARTIAL_BE_RUNNER_POLICY,
        "trailing_runner",
        "time_stop",
        "be_after_trigger",
        "momentum_exhaustion",
    }
    if not enabled:
        status = "disabled_default_off_preserve_current_production_policy"
    elif ticket_required and not lifecycle_source_complete:
        status = "source_required_before_policy_authority"
    elif not package.provenance.live_activation_allowed_by_package:
        status = "v3_policy_matched_live_activation_not_allowed_by_package"
    else:
        status = "v3_policy_authority_available"

    runtime_effect = bool(
        enabled
        and apply_to_execution
        and package.provenance.live_activation_allowed_by_package
        and lifecycle_source_complete
        and supported
    )
    return ExecutionPolicyV3Decision(
        enabled=bool(enabled),
        apply_to_execution=bool(apply_to_execution),
        selected_policy=selected,
        execution_policy_id=execution_policy_id_for(selected) or EXECUTION_POLICY_IDS.get(DEFAULT_POLICY),
        decision_status=status,
        lifecycle_source_status=lifecycle_status,
        ticket_bound_lifecycle_required=ticket_required,
        supported_live_policy=supported,
        runtime_effect_now=runtime_effect,
        diagnostics={
            "raw_requested_policy": raw_requested,
            "requested_policy": requested,
            "requested_policy_supported": requested_supported,
            "selected_policy_supported": supported,
            "current_live_truth": package.data.get("current_production_policy_status", {}).get("current_live_truth"),
            "required_runtime_flags": package.data.get("implementation_contract", {}).get("required_runtime_flags", []),
            "fail_closed_rules": package.data.get("implementation_contract", {}).get("fail_closed_rules", []),
        },
    )


def build_execution_policy_v3_packet(
    context: Mapping[str, Any],
    package: V3RuntimePackage,
    *,
    enabled: bool = False,
    apply_to_execution: bool = False,
) -> dict[str, Any]:
    decision = apply_execution_policy_v3_default_off(
        context,
        package,
        enabled=enabled,
        apply_to_execution=apply_to_execution,
    ).to_record()
    return {
        "schema_version": "execution_policy_v3_runtime_packet_record_v1",
        "component": "execution_policy_v3",
        "package_provenance": package.provenance.to_record(),
        "decision": decision,
        "runtime_effect_now": bool(decision.get("runtime_effect_now")),
        "broker_operation": False,
        "order_calls": 0,
        "paid_api_or_vendor_call": False,
    }


def build_v3_runtime_packet(
    *,
    event: Mapping[str, Any],
    account_state: Mapping[str, Any],
    execution_context: Mapping[str, Any],
    packages: Mapping[str, V3RuntimePackage],
    enabled: bool = False,
    apply_to_execution: bool = False,
) -> dict[str, Any]:
    selector_packet = build_selector_v3_packet(
        event,
        packages["selector_v3"],
        enabled=enabled,
        apply_to_execution=apply_to_execution,
    )
    scheduler_packet = build_scheduler_v3_packet(
        account_state,
        packages["scheduler_v3"],
        enabled=enabled,
        apply_to_execution=apply_to_execution,
    )
    execution_packet = build_execution_policy_v3_packet(
        execution_context,
        packages["execution_policy_v3"],
        enabled=enabled,
        apply_to_execution=apply_to_execution,
    )
    return {
        "schema_version": "v3_runtime_packet_v1",
        "selector_v3": selector_packet,
        "scheduler_v3": scheduler_packet,
        "execution_policy_v3": execution_packet,
        "runtime_effect_now": any(
            bool(packet.get("runtime_effect_now"))
            for packet in (selector_packet, scheduler_packet, execution_packet)
        ),
        "broker_operation": False,
        "order_calls": 0,
        "paid_api_or_vendor_call": False,
        "runtime_effect_boundary": "default_off_v3_package_consumption_no_live_broker_effect",
    }


__all__ = [
    "EXECUTION_POLICY_V3_PACKAGE_PATH",
    "SCHEDULER_V3_PACKAGE_PATH",
    "SELECTOR_V3_PACKAGE_PATH",
    "SELECTOR_V3_PACKET_SCHEMA_PATH",
    "ExecutionPolicyV3Decision",
    "SchedulerV3Decision",
    "V3PackageProvenance",
    "V3RuntimePackage",
    "apply_execution_policy_v3_default_off",
    "apply_scheduler_v3_default_off",
    "build_execution_policy_v3_packet",
    "build_scheduler_v3_packet",
    "build_selector_v3_packet",
    "build_v3_runtime_packet",
    "load_v3_package",
    "load_v3_runtime_package_set",
    "scheduler_v3_missing_money_risk_fields",
    "sha256_file",
]
