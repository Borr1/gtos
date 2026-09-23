"""Ruin-aware risk governor V4 — pure deterministic budget/breaker math.

Default-OFF component for the ultimate mechanical edge route. The governor
turns one admission request into an approved risk slice using a day-level
risk budget with profit recycling, correlation-aware open heat, opportunity
pacing, and hard circuit breakers.

Budget law (all values in % of day-anchor equity):

    B_t = (daily_limit - hard_reserve)
          + kappa * max(0, realized_day_pnl)   # profit recycle
          + min(0, realized_day_pnl)           # losses shrink 1:1
          - OpenHeat

    OpenHeat = sum_i live_risk_i * rho_i       # live risk 0 after BE
    rho_i    = 1 + min(corr_heat_cap - 1, mean |corr| with other open clusters)
    pacing   = 1 / (1 + remaining_opportunity_weight * pacing_alpha)
    approved = clamp(min(requested, B_t * pacing), 0 or [min_slice, max_slice])

Doctrine:
- Pure function, no I/O, no clock, no broker calls. Deterministic.
- vNext decision surface: fails CLOSED on missing/invalid state and on a
  missing cluster-correlation source (unknown pairs are treated as |corr|=1).
- Predecision boundary: the state must never carry candidate outcome fields
  (``FORBIDDEN_STATE_FIELDS``); offering one refuses the request.
- Broker-real cushion validation stays in
  ``src/components/prop_firm_headroom_v4.py`` (Prague-anchor math is NOT
  reimplemented here); callers supply already-computed drawdown percentages.
- Default-off: with ``apply_to_execution`` false the decision is shadow-only
  (``applied=False`` and ``would_*`` mirrors are populated).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = "risk_governor_decision_v4"
COMPONENT = "risk_governor_v4"

BOUNDARY = {
    "broker_operation": False,
    "paid_api_or_vendor_call": False,
    "broker_runtime_change_status": False,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
}

ACTION_ALLOW = "allow"
ACTION_REDUCE = "reduce"
ACTION_REFUSE = "refuse"
ACTION_FLATTEN_HALT = "flatten_halt_until_reset"
ACTION_FLOOR_REVIEW = "floor_risk_owner_review"

ACTIONS = (
    ACTION_ALLOW,
    ACTION_REDUCE,
    ACTION_REFUSE,
    ACTION_FLATTEN_HALT,
    ACTION_FLOOR_REVIEW,
)

REQUIRED_STATE_FIELDS = (
    "realized_day_pnl_pct",
    "open_positions",
    "requested_risk_pct",
    "remaining_opportunity_weight",
    "intraday_conservative_dd_pct",
    "overall_dd_pct",
)

# Candidate-outcome fields may never reach the governor's predecision state
# (mirrors FORBIDDEN_SELECTOR_V4_RUNTIME_FIELDS / FORBIDDEN_FEATURE_TOKENS
# doctrine). ``realized_day_pnl_pct`` is closed-trade account state, not a
# candidate outcome, and is explicitly allowed.
FORBIDDEN_STATE_FIELDS = (
    "final_r",
    "net_r",
    "gross_r",
    "actual_r",
    "counterfactual_final_r",
    "mfe_r",
    "mae_r",
    "terminal_outcome",
    "close_reason",
    "fill_status",
    "hindsight_r",
    "realized_r",
)

_CONFIG_KEY_PREFIX = "risk_governor_v4_"
_EPS = 1e-9


@dataclass(frozen=True)
class GovernorConfigV4:
    enabled: bool = False
    apply_to_execution: bool = False
    daily_limit_pct: float = 5.0
    hard_reserve_pct: float = 0.5
    profit_recycle_fraction: float = 0.5
    corr_heat_cap: float = 1.5
    pacing_alpha: float = 1.0
    min_slice_pct: float = 0.25
    max_slice_pct: float = 2.0
    breaker_dd_pct: float = 4.2
    overall_dd_floor_pct: float = 8.0

    @classmethod
    def from_runtime_config(cls, config: Mapping[str, Any] | None) -> "GovernorConfigV4":
        """Read ``gtos_vnext_runtime.risk_governor_v4_*`` keys with defaults.

        Accepts the full agent config (with a ``gtos_vnext_runtime`` block) or
        the runtime block itself. Every key is optional; defaults are the
        in-code default-off values.
        """

        runtime: Mapping[str, Any] = {}
        if isinstance(config, Mapping):
            block = config.get("gtos_vnext_runtime")
            runtime = block if isinstance(block, Mapping) else config

        def _bool(key: str, default: bool) -> bool:
            value = runtime.get(_CONFIG_KEY_PREFIX + key, default)
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)

        def _float(key: str, default: float) -> float:
            value = runtime.get(_CONFIG_KEY_PREFIX + key, default)
            try:
                parsed = float(value if value not in (None, "") else default)
            except (TypeError, ValueError):
                return default
            return parsed if math.isfinite(parsed) else default

        daily_limit = max(0.01, _float("daily_limit_pct", 5.0))
        reserve = min(daily_limit, max(0.0, _float("hard_reserve_pct", 0.5)))
        min_slice = max(0.0, _float("min_slice_pct", 0.25))
        max_slice = max(min_slice, _float("max_slice_pct", 2.0))
        return cls(
            enabled=_bool("enabled", False),
            apply_to_execution=_bool("apply_to_execution", False),
            daily_limit_pct=daily_limit,
            hard_reserve_pct=reserve,
            profit_recycle_fraction=min(1.0, max(0.0, _float("profit_recycle_fraction", 0.5))),
            corr_heat_cap=max(1.0, _float("corr_heat_cap", 1.5)),
            pacing_alpha=max(0.0, _float("pacing_alpha", 1.0)),
            min_slice_pct=min_slice,
            max_slice_pct=max_slice,
            breaker_dd_pct=max(0.01, _float("breaker_dd_pct", 4.2)),
            overall_dd_floor_pct=max(0.01, _float("overall_dd_floor_pct", 8.0)),
        )


@dataclass(frozen=True)
class GovernorDecisionV4:
    action: str
    approved_risk_pct: float
    requested_risk_pct: float | None
    applied: bool
    enabled: bool
    apply_to_execution: bool
    budget_total_pct: float | None
    budget_base_pct: float | None
    profit_recycle_pct: float | None
    loss_drag_pct: float | None
    open_heat_pct: float | None
    pacing_fraction: float | None
    remaining_opportunity_weight: float | None
    intraday_conservative_dd_pct: float | None
    overall_dd_pct: float | None
    reasons: tuple[str, ...]
    would_action: str | None
    would_approved_risk_pct: float | None

    def to_packet(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "component": COMPONENT,
            "action": self.action,
            "approved_risk_pct": self.approved_risk_pct,
            "requested_risk_pct": self.requested_risk_pct,
            "applied": self.applied,
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "execution_binding": (
                "applied_to_execution" if self.applied else "shadow_only_not_applied_to_execution"
            ),
            "budget_total_pct": self.budget_total_pct,
            "budget_base_pct": self.budget_base_pct,
            "profit_recycle_pct": self.profit_recycle_pct,
            "loss_drag_pct": self.loss_drag_pct,
            "open_heat_pct": self.open_heat_pct,
            "pacing_fraction": self.pacing_fraction,
            "remaining_opportunity_weight": self.remaining_opportunity_weight,
            "intraday_conservative_dd_pct": self.intraday_conservative_dd_pct,
            "overall_dd_pct": self.overall_dd_pct,
            "reasons": list(self.reasons),
            "would_action": self.would_action,
            "would_approved_risk_pct": self.would_approved_risk_pct,
            "decision_surface": "fail_closed_on_missing_source",
            **BOUNDARY,
        }


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def pair_abs_correlation(lookup: Any, cluster_a: str, cluster_b: str) -> float:
    """|corr| between two clusters; fails CLOSED to 1.0 on a missing source.

    ``lookup`` may be a callable ``(a, b) -> corr`` or a mapping keyed by
    ``(a, b)`` / ``(b, a)`` / ``"a|b"`` / ``"b|a"``. Same cluster is 1.0 by
    definition. Any missing/unparseable entry counts as full correlation
    (maximum heat — the conservative direction for a risk budget).
    """

    if cluster_a == cluster_b:
        return 1.0
    if callable(lookup):
        try:
            value = _finite(lookup(cluster_a, cluster_b))
        except Exception:
            value = None
        return min(1.0, abs(value)) if value is not None else 1.0
    if isinstance(lookup, Mapping):
        for key in (
            (cluster_a, cluster_b),
            (cluster_b, cluster_a),
            f"{cluster_a}|{cluster_b}",
            f"{cluster_b}|{cluster_a}",
        ):
            if key in lookup:
                value = _finite(lookup[key])
                return min(1.0, abs(value)) if value is not None else 1.0
        return 1.0
    return 1.0


def _open_heat_pct(
    open_positions: list[Mapping[str, Any]],
    lookup: Any,
    corr_heat_cap: float,
) -> float:
    live: list[tuple[float, str]] = []
    for position in open_positions:
        if bool(position.get("be_reached")):
            continue  # BE reached -> live risk 0, heat freed
        risk = _finite(position.get("risk_pct")) or 0.0
        if risk <= 0.0:
            continue
        live.append((risk, str(position.get("cluster") or "unknown")))

    heat = 0.0
    for index, (risk, cluster) in enumerate(live):
        other_clusters = sorted(
            {other_cluster for j, (_, other_cluster) in enumerate(live) if j != index}
        )
        if other_clusters:
            mean_abs = sum(
                pair_abs_correlation(lookup, cluster, other) for other in other_clusters
            ) / len(other_clusters)
            rho = 1.0 + min(corr_heat_cap - 1.0, mean_abs)
        else:
            rho = 1.0
        heat += risk * rho
    return heat


def evaluate_risk_governor_v4(
    cfg: GovernorConfigV4, state: Mapping[str, Any]
) -> GovernorDecisionV4:
    """Evaluate one admission request against the day risk budget.

    ``state`` keys (all required unless noted):

    - ``realized_day_pnl_pct``           signed closed-trade day PnL %
    - ``open_positions``                 list of {risk_pct, cluster, be_reached}
    - ``cluster_correlation``            callable/mapping (optional; missing
                                         pairs fail closed to |corr|=1)
    - ``requested_risk_pct``             requested slice %
    - ``remaining_opportunity_weight``   [0, 1] from the caller's hourly curve
    - ``intraday_conservative_dd_pct``   conservative intraday drawdown % (>=0)
    - ``overall_dd_pct``                 overall drawdown % (>=0)
    """

    applied = bool(cfg.enabled and cfg.apply_to_execution)

    def _decide(
        action: str,
        approved: float,
        reasons: list[str],
        *,
        requested: float | None = None,
        budget_total: float | None = None,
        budget_base: float | None = None,
        recycle: float | None = None,
        loss_drag: float | None = None,
        open_heat: float | None = None,
        pacing: float | None = None,
        weight: float | None = None,
        intraday_dd: float | None = None,
        overall_dd: float | None = None,
    ) -> GovernorDecisionV4:
        all_reasons = list(reasons)
        if not cfg.enabled:
            all_reasons.append("governor_disabled_default_off")
        if not applied:
            all_reasons.append("shadow_only_not_applied_to_execution")
        return GovernorDecisionV4(
            action=action,
            approved_risk_pct=approved,
            requested_risk_pct=requested,
            applied=applied,
            enabled=cfg.enabled,
            apply_to_execution=cfg.apply_to_execution,
            budget_total_pct=budget_total,
            budget_base_pct=budget_base,
            profit_recycle_pct=recycle,
            loss_drag_pct=loss_drag,
            open_heat_pct=open_heat,
            pacing_fraction=pacing,
            remaining_opportunity_weight=weight,
            intraday_conservative_dd_pct=intraday_dd,
            overall_dd_pct=overall_dd,
            reasons=tuple(all_reasons),
            would_action=None if applied else action,
            would_approved_risk_pct=None if applied else approved,
        )

    if not isinstance(state, Mapping):
        return _decide(ACTION_REFUSE, 0.0, ["missing_required_state:state_not_a_mapping"])

    forbidden = sorted(key for key in FORBIDDEN_STATE_FIELDS if key in state)
    if forbidden:
        return _decide(
            ACTION_REFUSE,
            0.0,
            [f"forbidden_outcome_field_in_state:{key}" for key in forbidden],
        )

    missing: list[str] = []
    pnl = _finite(state.get("realized_day_pnl_pct"))
    if pnl is None:
        missing.append("realized_day_pnl_pct")
    requested = _finite(state.get("requested_risk_pct"))
    if requested is None:
        missing.append("requested_risk_pct")
    weight = _finite(state.get("remaining_opportunity_weight"))
    if weight is None:
        missing.append("remaining_opportunity_weight")
    intraday_dd = _finite(state.get("intraday_conservative_dd_pct"))
    if intraday_dd is None:
        missing.append("intraday_conservative_dd_pct")
    overall_dd = _finite(state.get("overall_dd_pct"))
    if overall_dd is None:
        missing.append("overall_dd_pct")

    raw_positions = state.get("open_positions")
    open_positions: list[Mapping[str, Any]] = []
    if not isinstance(raw_positions, (list, tuple)):
        missing.append("open_positions")
    else:
        for position in raw_positions:
            if not isinstance(position, Mapping):
                missing.append("open_positions:entry_not_a_mapping")
                break
            if not bool(position.get("be_reached")) and _finite(position.get("risk_pct")) is None:
                missing.append("open_positions:risk_pct")
                break
            open_positions.append(position)

    if missing:
        return _decide(
            ACTION_REFUSE,
            0.0,
            [f"missing_required_state:{name}" for name in dict.fromkeys(missing)],
            requested=requested,
        )

    weight = min(1.0, max(0.0, weight))
    intraday_dd = max(0.0, intraday_dd)
    overall_dd = max(0.0, overall_dd)

    lookup = state.get("cluster_correlation")
    open_heat = _open_heat_pct(open_positions, lookup, cfg.corr_heat_cap)
    budget_base = cfg.daily_limit_pct - cfg.hard_reserve_pct
    recycle = cfg.profit_recycle_fraction * max(0.0, pnl)
    loss_drag = min(0.0, pnl)
    budget_total = budget_base + recycle + loss_drag - open_heat
    pacing = 1.0 / (1.0 + weight * cfg.pacing_alpha)

    common = {
        "requested": requested,
        "budget_total": budget_total,
        "budget_base": budget_base,
        "recycle": recycle,
        "loss_drag": loss_drag,
        "open_heat": open_heat,
        "pacing": pacing,
        "weight": weight,
        "intraday_dd": intraday_dd,
        "overall_dd": overall_dd,
    }

    if overall_dd >= cfg.overall_dd_floor_pct - _EPS:
        return _decide(
            ACTION_FLOOR_REVIEW,
            0.0,
            [f"overall_dd_{overall_dd:.4f}pct_at_or_above_floor_{cfg.overall_dd_floor_pct}pct"],
            **common,
        )
    if intraday_dd >= cfg.breaker_dd_pct - _EPS:
        return _decide(
            ACTION_FLATTEN_HALT,
            0.0,
            [
                "intraday_conservative_dd_"
                f"{intraday_dd:.4f}pct_at_or_above_breaker_{cfg.breaker_dd_pct}pct"
            ],
            **common,
        )
    if requested <= 0.0:
        return _decide(ACTION_REFUSE, 0.0, ["non_positive_requested_risk"], **common)
    if budget_total <= cfg.min_slice_pct + _EPS:
        return _decide(
            ACTION_REFUSE,
            0.0,
            [f"budget_{budget_total:.4f}pct_at_or_below_min_slice_{cfg.min_slice_pct}pct"],
            **common,
        )

    raw_approved = min(requested, budget_total * pacing)
    if raw_approved < cfg.min_slice_pct - _EPS:
        return _decide(
            ACTION_REFUSE,
            0.0,
            [f"approved_slice_{raw_approved:.4f}pct_below_min_slice_{cfg.min_slice_pct}pct"],
            **common,
        )

    reasons: list[str] = []
    approved = raw_approved
    if approved > cfg.max_slice_pct + _EPS:
        approved = cfg.max_slice_pct
        reasons.append(f"clamped_to_max_slice_{cfg.max_slice_pct}pct")
    if approved + _EPS < requested:
        reasons.append("budget_or_pacing_reduced_below_request")
        return _decide(ACTION_REDUCE, approved, reasons, **common)
    return _decide(ACTION_ALLOW, approved, reasons or ["within_budget"], **common)


def governor_config_packet(cfg: GovernorConfigV4) -> dict[str, Any]:
    """Telemetry echo of the active governor configuration."""

    return {
        "schema_version": "risk_governor_config_v4",
        "component": COMPONENT,
        **asdict(cfg),
        **BOUNDARY,
    }


__all__ = [
    "ACTIONS",
    "ACTION_ALLOW",
    "ACTION_FLATTEN_HALT",
    "ACTION_FLOOR_REVIEW",
    "ACTION_REDUCE",
    "ACTION_REFUSE",
    "BOUNDARY",
    "FORBIDDEN_STATE_FIELDS",
    "GovernorConfigV4",
    "GovernorDecisionV4",
    "REQUIRED_STATE_FIELDS",
    "SCHEMA_VERSION",
    "evaluate_risk_governor_v4",
    "governor_config_packet",
    "pair_abs_correlation",
]
