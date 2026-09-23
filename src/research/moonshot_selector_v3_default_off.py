"""Default-off Selector V3 package helpers.

This module is deliberately pure: it reads no files, makes no network/API
calls, and cannot touch broker/account/order state. It lets tests and runtime
adapters consume a Selector V3 package only when the caller explicitly passes
the package and event payload.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


SELECTOR_V3_ACTIONS = (
    "trade",
    "reduce_risk",
    "avoid",
    "capture_repair",
    "no_trade_by_evidence",
    "source_required",
)

SELECTOR_V3_TO_ROUTER_ACTION = {
    "trade": "tradeable_now",
    "reduce_risk": "reduce_risk_by_evidence",
    "avoid": "no_trade_by_evidence",
    "capture_repair": "source_capture_required",
    "no_trade_by_evidence": "no_trade_by_evidence",
    "source_required": "source_capture_required",
}

FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS = (
    "actual_r",
    "broker_actual_r",
    "broker_real_net_r",
    "broker_realized_net_r",
    "close_reason",
    "correct_rejection",
    "cost_adjusted_r",
    "execution_policy_result",
    "exit_reason",
    "exact_r",
    "final_r",
    "final_target_reached",
    "gross_r",
    "hindsight_best_policy",
    "hindsight_best_r",
    "mae_r",
    "mfe_r",
    "missed_opportunity",
    "net_r",
    "one_r_reached",
    "partial_then_be",
    "partial_then_final",
    "path_class",
    "path_ordering_status",
    "proxy_r",
    "result_r",
    "sl_before_1r",
    "source_bound_proxy_r",
    "stale_blocker",
    "stuck_no_resolution",
    "time_to_1r_seconds",
    "time_to_sl_seconds",
    "win_rate",
)


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _lower(value: Any) -> str:
    return _text(value).strip().lower()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _lower(value) in {"1", "true", "yes", "y"}


def _symbol(value: Any) -> str:
    return _text(value).strip().upper().replace(".", "_")


def _side(value: Any) -> str:
    return _text(value).strip().upper()


def _origin(value: Any) -> str:
    origin = _lower(value)
    return origin.removeprefix("origin_").removeprefix("current_")


def _session_bucket(value: Any) -> str:
    key = _lower(value).replace("-", "_").replace(" ", "_")
    if not key:
        return ""
    if key.endswith("_broad"):
        return key
    if "tokyo" in key:
        return "tokyo_broad"
    if key in {"ny", "new_york", "newyork"} or "ny" in key:
        return "ny_broad"
    if "london" in key or key in {"ldn", "lon"}:
        return "london_broad"
    if "off" in key or "dead" in key:
        return "off_kz_broad"
    return f"{key}_broad"


def _float_or_none(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ignored_forbidden_runtime_fields(event: Mapping[str, Any]) -> tuple[str, ...]:
    """Return forbidden future/result fields supplied by the caller.

    The helper never consumes these fields for selection. Returning them makes
    no-leak tests and runtime packet audits explicit.
    """

    return tuple(
        field
        for field in FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS
        if event.get(field) not in (None, "")
    )


def selector_v3_rule_specificity(rule: Mapping[str, Any]) -> int:
    return sum(
        1
        for field_name in (
            "symbol",
            "side",
            "framework",
            "origin_family",
            "session",
            "session_bucket",
            "regime_h4_state",
            "spread_r_bucket",
            "source_completeness_state",
        )
        if rule.get(field_name)
    )


def selector_v3_action_priority(action: str) -> int:
    action = _lower(action)
    if action in {"avoid", "no_trade_by_evidence"}:
        return 6
    if action == "source_required":
        return 5
    if action == "capture_repair":
        return 4
    if action == "reduce_risk":
        return 3
    if action == "trade":
        return 2
    return 1


def selector_v3_rule_matches(event: Mapping[str, Any], rule: Mapping[str, Any]) -> bool:
    """Return whether a package rule matches event as-of fields only."""

    if rule.get("symbol") and _symbol(rule.get("symbol")) != _symbol(event.get("symbol")):
        return False
    if rule.get("side") and _side(rule.get("side")) != _side(event.get("side")):
        return False
    if rule.get("framework") and _lower(rule.get("framework")) != _lower(
        event.get("framework") or event.get("route_family")
    ):
        return False
    if rule.get("origin_family") and _origin(rule.get("origin_family")) != _origin(
        event.get("candidate_origin_family") or event.get("origin_family")
    ):
        return False
    rule_session = rule.get("session") or rule.get("session_bucket")
    if rule_session and _session_bucket(rule_session) != _session_bucket(
        event.get("session_bucket") or event.get("route_session")
    ):
        return False
    for field_name in ("regime_h4_state", "spread_r_bucket", "source_completeness_state"):
        if rule.get(field_name) and _lower(rule.get(field_name)) != _lower(event.get(field_name)):
            return False
    return True


def select_selector_v3_rule(
    event: Mapping[str, Any],
    rules: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    """Select the most specific, most protective matching Selector V3 rule."""

    matches = [rule for rule in rules if selector_v3_rule_matches(event, rule)]
    if not matches:
        return None
    return max(
        matches,
        key=lambda rule: (
            selector_v3_action_priority(_lower(rule.get("selector_v3_action") or rule.get("action"))),
            selector_v3_rule_specificity(rule),
            _text(rule.get("rule_id")),
        ),
    )


def runtime_rules_from_selector_v3_package(
    package: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Convert package rules into the existing router's quality-rule shape."""

    router_rules: list[dict[str, Any]] = []
    for rule in package.get("runtime_selector_rules") or []:
        action = _lower(rule.get("selector_v3_action") or rule.get("action"))
        router_action = SELECTOR_V3_TO_ROUTER_ACTION.get(action, "source_capture_required")
        router_rules.append(
            {
                "rule_id": rule.get("rule_id"),
                "action": router_action,
                "selector_v3_action": action,
                "refusal_reason": rule.get("refusal_reason"),
                "risk_multiplier": rule.get("risk_multiplier"),
                "symbol": rule.get("symbol"),
                "side": rule.get("side"),
                "session": rule.get("session") or rule.get("session_bucket"),
                "origin_family": rule.get("origin_family"),
                "framework": rule.get("framework"),
                "regime_h4_state": rule.get("regime_h4_state"),
                "spread_r_bucket": rule.get("spread_r_bucket"),
                "source_completeness_state": rule.get("source_completeness_state"),
            }
        )
    return tuple(router_rules)


@dataclass(frozen=True)
class SelectorV3DefaultOffDecision:
    package_id: str | None
    enabled: bool
    apply_to_execution: bool
    selector_v3_action: str
    router_rule_action: str
    decision_status: str
    matched_rule_id: str | None = None
    refusal_reason: str | None = None
    risk_multiplier: float | None = None
    runtime_effect_now: bool = False
    candidate_use_allowed_now: bool = False
    broker_operation: bool = False
    paid_api_or_vendor_call: bool = False
    owner_approval_required: bool = True
    ignored_forbidden_fields: tuple[str, ...] = ()
    evidence_notes: tuple[str, ...] = field(default_factory=tuple)

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["ignored_forbidden_fields"] = list(self.ignored_forbidden_fields)
        record["evidence_notes"] = list(self.evidence_notes)
        return record


def apply_selector_v3_default_off(
    event: Mapping[str, Any],
    package: Mapping[str, Any],
    *,
    enabled: bool = False,
    apply_to_execution: bool = False,
) -> SelectorV3DefaultOffDecision:
    """Apply a Selector V3 package without granting live behavior.

    Even if the caller asks for execution application, the package must itself
    allow live activation. The Selector V3 package built by the route is
    research/default-off, so it returns no runtime effect.
    """

    package_id = _text(package.get("package_id")) or None
    forbidden = ignored_forbidden_runtime_fields(event)
    notes = ["selector_v3_default_off_helper_no_file_io_no_broker_io"]
    if forbidden:
        notes.append("forbidden_future_or_result_fields_present_but_ignored")

    if not enabled:
        return SelectorV3DefaultOffDecision(
            package_id=package_id,
            enabled=False,
            apply_to_execution=False,
            selector_v3_action="default_off_disabled",
            router_rule_action="source_capture_required",
            decision_status="disabled_default_off",
            ignored_forbidden_fields=forbidden,
            evidence_notes=tuple(notes),
        )

    rules = package.get("runtime_selector_rules") or []
    matched = select_selector_v3_rule(event, rules)
    if matched is None:
        return SelectorV3DefaultOffDecision(
            package_id=package_id,
            enabled=True,
            apply_to_execution=bool(apply_to_execution),
            selector_v3_action="source_required",
            router_rule_action="source_capture_required",
            decision_status="no_matching_selector_v3_rule_source_required",
            refusal_reason="selector_v3_no_matching_runtime_eligible_rule",
            ignored_forbidden_fields=forbidden,
            evidence_notes=tuple(notes),
        )

    action = _lower(matched.get("selector_v3_action") or matched.get("action"))
    if action not in SELECTOR_V3_ACTIONS:
        action = "source_required"
    router_action = SELECTOR_V3_TO_ROUTER_ACTION[action]
    package_allows_live = _truthy(package.get("live_activation_allowed_by_this_package"))
    allowed_by_action = action in {"trade", "reduce_risk"}
    candidate_allowed = bool(
        enabled and apply_to_execution and package_allows_live and allowed_by_action
    )
    status = (
        "matched_selector_v3_rule_live_activation_not_allowed_by_package"
        if allowed_by_action and not package_allows_live
        else "matched_selector_v3_rule_default_off_hold"
    )
    return SelectorV3DefaultOffDecision(
        package_id=package_id,
        enabled=True,
        apply_to_execution=bool(apply_to_execution),
        selector_v3_action=action,
        router_rule_action=router_action,
        decision_status=status,
        matched_rule_id=_text(matched.get("rule_id")) or None,
        refusal_reason=matched.get("refusal_reason"),
        risk_multiplier=_float_or_none(matched.get("risk_multiplier")),
        runtime_effect_now=candidate_allowed,
        candidate_use_allowed_now=candidate_allowed,
        ignored_forbidden_fields=forbidden,
        evidence_notes=tuple(notes),
    )


__all__ = [
    "FORBIDDEN_SELECTOR_V3_RUNTIME_FIELDS",
    "SELECTOR_V3_ACTIONS",
    "SELECTOR_V3_TO_ROUTER_ACTION",
    "SelectorV3DefaultOffDecision",
    "apply_selector_v3_default_off",
    "ignored_forbidden_runtime_fields",
    "runtime_rules_from_selector_v3_package",
    "select_selector_v3_rule",
    "selector_v3_rule_matches",
]
