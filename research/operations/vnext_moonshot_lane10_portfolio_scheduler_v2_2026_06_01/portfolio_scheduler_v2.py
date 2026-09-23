"""Offline Portfolio Scheduler V2 engine for the vNext moonshot Lane10 route.

The engine is intentionally route-local and default-off. It models admission
from account-risk exposure, not stale count caps, and exposes the decision
details needed by the Lane10 replay builder, verifier, and focused tests.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        if " " in text and "T" not in text:
            text = text.replace(" ", "T")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def fnum(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return number


def round6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def round9(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 9)


def money(amount: float | None) -> float | None:
    if amount is None:
        return None
    return round(float(amount), 2)


def market_type(symbol: str) -> str:
    symbol = str(symbol or "").upper()
    if symbol in {"BTCUSD", "ETHUSD"}:
        return "crypto"
    if symbol in {"XAUUSD", "XAGUSD"}:
        return "metals"
    if symbol in {"UKOIL_CASH", "USOIL_CASH"}:
        return "energy"
    if symbol in {"GER40", "JP225", "NAS100", "SPX500", "UK100", "US30_CASH"}:
        return "index_cfd"
    if len(symbol) == 6 and symbol.isalpha():
        return "fx"
    return "unknown_market"


def correlation_cluster(symbol: str) -> str:
    key = str(symbol or "").upper()
    clusters = {
        "metals": {"XAUUSD", "XAGUSD"},
        "crypto": {"BTCUSD", "ETHUSD"},
        "us_index": {"NAS100", "SPX500", "US30_CASH"},
        "europe_index": {"GER40", "UK100"},
        "energy": {"UKOIL_CASH", "USOIL_CASH"},
        "jpy_fx": {"AUDJPY", "CHFJPY", "EURJPY", "GBPJPY", "USDJPY", "JP225"},
        "usd_fx": {"AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF"},
    }
    for cluster, members in clusters.items():
        if key in members:
            return cluster
    return f"solo_{key.lower() or 'unknown'}"


def session_priority(session: str) -> float:
    key = str(session or "").lower()
    if "london" in key:
        return 0.30
    if key.startswith("ny") or "new_york" in key:
        return 0.25
    if "tokyo" in key:
        return 0.15
    if "h23" in key or "h00" in key:
        return 0.05
    return 0.10


def origin_priority(origin: str) -> float:
    key = str(origin or "").lower()
    if "liquidity_sweep" in key:
        return 0.30
    if "displacement" in key:
        return 0.25
    if "ob_retest" in key:
        return 0.18
    if "fvg" in key or "breaker" in key:
        return 0.14
    return 0.05


def cost_priority(cost_bucket: str) -> float:
    key = str(cost_bucket or "").lower()
    if "missing" in key:
        return 0.02
    if "le_0_02" in key:
        return 0.12
    if "0_02_to_0_05" in key:
        return 0.09
    if "0_05_to_0_10" in key:
        return 0.05
    if "0_10_to_0_20" in key:
        return 0.02
    return 0.0


@dataclass
class SchedulerConfig:
    initial_balance: float = 100000.0
    starting_equity: float = 100824.89
    risk_base_amount: float = 100000.0
    base_portfolio_ceiling_pct: float = 7.23983929
    portfolio_buffer_pct: float = 0.10
    external_daily_loss_limit_pct: float = 5.0
    internal_daily_overlay_pct: float = 4.0
    overall_loss_limit_pct: float = 10.0
    correlated_cluster_ceiling_pct: float = 4.0
    cushion_expansion_trigger_pct: float = 1.0
    cushion_expansion_factor: float = 0.25
    cushion_expansion_cap_pct: float = 2.0
    drawdown_safety_buffer_pct: float = 0.50
    min_reduced_risk_pct: float = 0.25
    allow_reduced_risk: bool = True
    same_symbol_conflict: bool = True
    correlated_cluster_enforced: bool = True


@dataclass
class SchedulerCandidate:
    row_id: str
    candidate_id: str
    selected_row_id: str
    symbol: str
    side: str
    decision_dt: datetime
    entry_dt: datetime
    exit_dt: datetime
    risk_release_dt: datetime
    partial_release_dt: datetime | None
    result_r: float | None
    result_r_class: str
    requested_risk_pct: float | None
    source_scheduler_state: str
    source_family: str
    source_priority_state: str
    session_bucket: str
    origin_family: str
    framework: str
    chosen_policy: str
    cost_status: str
    spread_r_bucket: str
    broker_ready_state: str
    no_leak_status: str
    stale_blocker: bool = False
    source_gap: bool = False
    pending_risk_pct: float = 0.0
    input_sequence: int = 0

    @property
    def cluster(self) -> str:
        return correlation_cluster(self.symbol)

    @property
    def priority_score(self) -> float:
        score = 0.0
        score += 0.40 if (self.requested_risk_pct or 0.0) > 0 else -1.0
        score += session_priority(self.session_bucket)
        score += origin_priority(self.origin_family)
        score += cost_priority(self.spread_r_bucket)
        score += 0.12 if self.broker_ready_state == "joined_lane07_symbol_spec" else 0.0
        score += 0.10 if self.chosen_policy == "partial_be_runner" else 0.05
        score += 0.10 if not self.source_gap else -0.05
        score += 0.05 if self.no_leak_status == "pass" else -0.25
        return round(score, 9)

    @property
    def priority_components(self) -> dict[str, Any]:
        return {
            "risk_proof_component": 0.40 if (self.requested_risk_pct or 0.0) > 0 else -1.0,
            "session_component": session_priority(self.session_bucket),
            "origin_component": origin_priority(self.origin_family),
            "cost_component": cost_priority(self.spread_r_bucket),
            "broker_ready_component": (
                0.12 if self.broker_ready_state == "joined_lane07_symbol_spec" else 0.0
            ),
            "policy_component": 0.10 if self.chosen_policy == "partial_be_runner" else 0.05,
            "source_gap_component": 0.10 if not self.source_gap else -0.05,
            "no_leak_component": 0.05 if self.no_leak_status == "pass" else -0.25,
            "uses_result_fields": False,
        }


@dataclass
class ActiveExposure:
    row_id: str
    selected_row_id: str
    symbol: str
    cluster: str
    side: str
    exit_dt: datetime
    risk_release_dt: datetime
    partial_release_dt: datetime | None
    requested_risk_pct: float
    approved_risk_pct: float
    residual_exposure_pct: float
    result_r: float
    pnl_realized: bool = False


@dataclass
class SchedulerDecision:
    accepted: bool
    decision: str
    reason: str
    requested_risk_pct: float | None
    approved_risk_pct: float
    new_trade_risk_amount: float
    approved_new_trade_risk_amount: float
    cost_buffer_pct: float
    open_risk_pct_before: float
    pending_risk_pct_before: float
    same_symbol_risk_pct_before: float
    correlated_cluster_risk_pct_before: float
    residual_exposure_pct_before: float
    total_risk_pct_before: float
    total_risk_pct_after: float
    dynamic_portfolio_ceiling_pct: float
    account_available_risk_pct: float
    day_start_baseline: float
    current_equity: float
    realized_proxy_pnl: float
    daily_cushion_before: float
    overall_cushion_before: float
    internal_daily_cushion_before: float
    same_symbol_conflict_ids: list[str]
    correlated_cluster_conflict_ids: list[str]
    priority_rank_in_batch: int
    priority_score: float
    priority_components: dict[str, Any]
    opportunity_cost_r: float
    opportunity_cost_amount: float
    risk_release_dt: datetime | None

    def asdict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "decision": self.decision,
            "reason": self.reason,
            "requested_risk_pct": round9(self.requested_risk_pct),
            "approved_risk_pct": round9(self.approved_risk_pct),
            "new_trade_risk_amount": money(self.new_trade_risk_amount),
            "approved_new_trade_risk_amount": money(self.approved_new_trade_risk_amount),
            "cost_buffer_pct": round9(self.cost_buffer_pct),
            "open_risk_pct_before": round9(self.open_risk_pct_before),
            "pending_risk_pct_before": round9(self.pending_risk_pct_before),
            "same_symbol_risk_pct_before": round9(self.same_symbol_risk_pct_before),
            "correlated_cluster_risk_pct_before": round9(self.correlated_cluster_risk_pct_before),
            "residual_exposure_pct_before": round9(self.residual_exposure_pct_before),
            "total_risk_pct_before": round9(self.total_risk_pct_before),
            "total_risk_pct_after": round9(self.total_risk_pct_after),
            "dynamic_portfolio_ceiling_pct": round9(self.dynamic_portfolio_ceiling_pct),
            "account_available_risk_pct": round9(self.account_available_risk_pct),
            "day_start_baseline": money(self.day_start_baseline),
            "current_equity": money(self.current_equity),
            "realized_proxy_pnl": money(self.realized_proxy_pnl),
            "daily_cushion_before": money(self.daily_cushion_before),
            "overall_cushion_before": money(self.overall_cushion_before),
            "internal_daily_cushion_before": money(self.internal_daily_cushion_before),
            "same_symbol_conflict_ids": self.same_symbol_conflict_ids,
            "correlated_cluster_conflict_ids": self.correlated_cluster_conflict_ids,
            "priority_rank_in_batch": self.priority_rank_in_batch,
            "priority_score": round9(self.priority_score),
            "priority_components": self.priority_components,
            "opportunity_cost_r": round9(self.opportunity_cost_r),
            "opportunity_cost_amount": money(self.opportunity_cost_amount),
            "risk_release_time_utc": iso(self.risk_release_dt),
        }


@dataclass
class SchedulerRunStats:
    rows: int = 0
    accepted_rows: int = 0
    accepted_full_risk_rows: int = 0
    accepted_reduced_risk_rows: int = 0
    rejected_rows: int = 0
    result_r_sum_all_rows: float = 0.0
    accepted_result_r_sum: float = 0.0
    rejected_opportunity_r_sum: float = 0.0
    accepted_proxy_pnl: float = 0.0
    rejected_opportunity_amount: float = 0.0
    max_active_positions: int = 0
    max_open_risk_pct: float = 0.0
    max_total_risk_pct_after: float = 0.0
    max_correlated_cluster_risk_pct: float = 0.0
    max_same_symbol_risk_pct: float = 0.0
    decision_counts: Counter[str] = field(default_factory=Counter)
    reason_counts: Counter[str] = field(default_factory=Counter)

    def update(self, decision: SchedulerDecision, candidate: SchedulerCandidate) -> None:
        self.rows += 1
        result_r = fnum(candidate.result_r, 0.0) or 0.0
        self.result_r_sum_all_rows += result_r
        self.decision_counts[decision.decision] += 1
        self.reason_counts[decision.reason] += 1
        self.max_open_risk_pct = max(self.max_open_risk_pct, decision.open_risk_pct_before)
        self.max_total_risk_pct_after = max(
            self.max_total_risk_pct_after,
            decision.total_risk_pct_after,
        )
        self.max_correlated_cluster_risk_pct = max(
            self.max_correlated_cluster_risk_pct,
            decision.correlated_cluster_risk_pct_before,
        )
        self.max_same_symbol_risk_pct = max(
            self.max_same_symbol_risk_pct,
            decision.same_symbol_risk_pct_before,
        )
        if decision.accepted:
            self.accepted_rows += 1
            self.accepted_result_r_sum += result_r
            self.accepted_proxy_pnl += (
                result_r * decision.approved_new_trade_risk_amount
            )
            if decision.decision == "ACCEPTED_REDUCED_RISK":
                self.accepted_reduced_risk_rows += 1
            else:
                self.accepted_full_risk_rows += 1
        else:
            self.rejected_rows += 1
            self.rejected_opportunity_r_sum += result_r
            self.rejected_opportunity_amount += decision.opportunity_cost_amount

    def asdict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "accepted_rows": self.accepted_rows,
            "accepted_full_risk_rows": self.accepted_full_risk_rows,
            "accepted_reduced_risk_rows": self.accepted_reduced_risk_rows,
            "rejected_rows": self.rejected_rows,
            "acceptance_rate": round9(self.accepted_rows / self.rows) if self.rows else None,
            "result_r_sum_all_rows": round9(self.result_r_sum_all_rows),
            "accepted_result_r_sum": round9(self.accepted_result_r_sum),
            "rejected_opportunity_r_sum": round9(self.rejected_opportunity_r_sum),
            "accepted_proxy_pnl": money(self.accepted_proxy_pnl),
            "rejected_opportunity_amount": money(self.rejected_opportunity_amount),
            "max_active_positions": self.max_active_positions,
            "max_open_risk_pct_before": round9(self.max_open_risk_pct),
            "max_total_risk_pct_after": round9(self.max_total_risk_pct_after),
            "max_correlated_cluster_risk_pct_before": round9(
                self.max_correlated_cluster_risk_pct
            ),
            "max_same_symbol_risk_pct_before": round9(self.max_same_symbol_risk_pct),
            "decision_counts": dict(sorted(self.decision_counts.items())),
            "reason_counts": dict(sorted(self.reason_counts.items())),
        }


class PortfolioSchedulerV2Engine:
    def __init__(self, config: SchedulerConfig | None = None):
        self.config = config or SchedulerConfig()
        self.active: list[ActiveExposure] = []
        self.realized_proxy_pnl = 0.0
        self.day_start_by_day: dict[str, float] = {}
        self.stats = SchedulerRunStats()

    def _risk_amount(self, risk_pct: float | None) -> float:
        return self.config.risk_base_amount * max(0.0, risk_pct or 0.0) / 100.0

    def _current_equity(self) -> float:
        return self.config.starting_equity + self.realized_proxy_pnl

    def _release_matured(self, decision_dt: datetime) -> None:
        remaining: list[ActiveExposure] = []
        for exposure in self.active:
            if exposure.exit_dt <= decision_dt:
                if not exposure.pnl_realized:
                    self.realized_proxy_pnl += (
                        exposure.result_r * self._risk_amount(exposure.approved_risk_pct)
                    )
                    exposure.pnl_realized = True
                continue
            remaining.append(exposure)
        self.active = remaining

    def _day_start_baseline(self, decision_dt: datetime) -> float:
        key = decision_dt.date().isoformat()
        if key not in self.day_start_by_day:
            self.day_start_by_day[key] = self._current_equity()
        return self.day_start_by_day[key]

    def _open_risk_pct(self, decision_dt: datetime) -> float:
        return sum(
            exposure.approved_risk_pct
            for exposure in self.active
            if exposure.risk_release_dt > decision_dt
        )

    def _residual_exposure_pct(self, decision_dt: datetime) -> float:
        return sum(
            exposure.residual_exposure_pct
            for exposure in self.active
            if exposure.partial_release_dt
            and exposure.partial_release_dt <= decision_dt < exposure.exit_dt
        )

    def _same_symbol_exposures(self, candidate: SchedulerCandidate) -> list[ActiveExposure]:
        return [exposure for exposure in self.active if exposure.symbol == candidate.symbol]

    def _cluster_exposures(self, candidate: SchedulerCandidate) -> list[ActiveExposure]:
        return [exposure for exposure in self.active if exposure.cluster == candidate.cluster]

    def _account_budget(self, decision_dt: datetime) -> dict[str, float]:
        equity = self._current_equity()
        day_start = self._day_start_baseline(decision_dt)
        daily_floor = day_start - (
            self.config.initial_balance * self.config.external_daily_loss_limit_pct / 100.0
        )
        internal_floor = day_start - (
            self.config.initial_balance * self.config.internal_daily_overlay_pct / 100.0
        )
        overall_floor = self.config.initial_balance * (
            1.0 - self.config.overall_loss_limit_pct / 100.0
        )
        daily_cushion = equity - daily_floor
        internal_cushion = equity - internal_floor
        overall_cushion = equity - overall_floor
        available_amount = min(daily_cushion, internal_cushion, overall_cushion)
        return {
            "current_equity": equity,
            "day_start_baseline": day_start,
            "daily_cushion": daily_cushion,
            "internal_daily_cushion": internal_cushion,
            "overall_cushion": overall_cushion,
            "available_risk_pct": available_amount / self.config.risk_base_amount * 100.0,
        }

    def _dynamic_portfolio_ceiling_pct(self, budget: dict[str, float]) -> float:
        day_realized_pct = (
            (budget["current_equity"] - budget["day_start_baseline"])
            / self.config.risk_base_amount
            * 100.0
        )
        ceiling = self.config.base_portfolio_ceiling_pct
        if day_realized_pct >= self.config.cushion_expansion_trigger_pct:
            ceiling += min(
                self.config.cushion_expansion_cap_pct,
                day_realized_pct * self.config.cushion_expansion_factor,
            )
        if day_realized_pct < 0:
            ceiling = min(
                ceiling,
                max(0.0, budget["available_risk_pct"] - self.config.drawdown_safety_buffer_pct),
            )
        return max(0.0, ceiling)

    def _cost_buffer_pct(self, candidate: SchedulerCandidate) -> float:
        requested = max(0.0, candidate.requested_risk_pct or 0.0)
        cost_proxy_r = 0.0
        bucket = str(candidate.spread_r_bucket or "")
        if "gt_0_10" in bucket or "0_20_to_0_50" in bucket:
            cost_proxy_r = 0.20
        elif "0_10_to_0_20" in bucket:
            cost_proxy_r = 0.10
        elif "0_05_to_0_10" in bucket:
            cost_proxy_r = 0.05
        elif "0_02_to_0_05" in bucket:
            cost_proxy_r = 0.03
        elif "le_0_02" in bucket:
            cost_proxy_r = 0.02
        return max(self.config.portfolio_buffer_pct, requested * cost_proxy_r)

    def decide(
        self,
        candidate: SchedulerCandidate,
        *,
        priority_rank_in_batch: int = 1,
    ) -> SchedulerDecision:
        self._release_matured(candidate.decision_dt)
        budget = self._account_budget(candidate.decision_dt)
        open_risk_pct = self._open_risk_pct(candidate.decision_dt)
        pending_risk_pct = max(0.0, candidate.pending_risk_pct)
        residual_pct = self._residual_exposure_pct(candidate.decision_dt)
        same_symbol = self._same_symbol_exposures(candidate)
        same_symbol_risk_pct = sum(exposure.approved_risk_pct for exposure in same_symbol)
        cluster_exposures = self._cluster_exposures(candidate)
        cluster_risk_pct = sum(exposure.approved_risk_pct for exposure in cluster_exposures)
        requested = candidate.requested_risk_pct
        cost_buffer_pct = self._cost_buffer_pct(candidate)
        total_before = open_risk_pct + pending_risk_pct + cost_buffer_pct
        dynamic_ceiling = self._dynamic_portfolio_ceiling_pct(budget)
        account_available_after_existing = budget["available_risk_pct"] - total_before
        requested_amount = self._risk_amount(requested)
        approved_risk_pct = max(0.0, requested or 0.0)
        decision = "ACCEPTED"
        reason = "accepted_money_risk_portfolio_exposure"
        accepted = True

        if requested is None or requested <= 0:
            accepted = False
            decision = "REJECTED"
            reason = (
                "selected_cell_or_effective_risk_missing_nonpositive_stale_source_repair_required"
            )
            approved_risk_pct = 0.0
        elif candidate.no_leak_status not in {"pass", "ok", "PASS"}:
            accepted = False
            decision = "REJECTED"
            reason = "no_leak_status_not_pass"
            approved_risk_pct = 0.0
        elif self.config.same_symbol_conflict and same_symbol:
            accepted = False
            decision = "REJECTED"
            reason = "same_symbol_exposure_conflict_active_until_lifecycle_close"
            approved_risk_pct = 0.0
        elif (
            self.config.correlated_cluster_enforced
            and cluster_risk_pct + requested > self.config.correlated_cluster_ceiling_pct
        ):
            accepted = False
            decision = "REJECTED"
            reason = "correlated_cluster_exposure_ceiling_exceeded"
            approved_risk_pct = 0.0
        else:
            max_by_portfolio = dynamic_ceiling - total_before
            max_by_account = account_available_after_existing
            max_allowed = max(0.0, min(max_by_portfolio, max_by_account))
            if max_allowed + 1e-12 >= requested:
                approved_risk_pct = requested
            elif self.config.allow_reduced_risk and max_allowed >= self.config.min_reduced_risk_pct:
                accepted = True
                decision = "ACCEPTED_REDUCED_RISK"
                reason = "accepted_reduced_risk_to_account_or_portfolio_budget"
                approved_risk_pct = max_allowed
            else:
                accepted = False
                decision = "REJECTED"
                if max_by_account < self.config.min_reduced_risk_pct:
                    reason = "account_daily_or_overall_limit_exceeded"
                elif budget["current_equity"] < budget["day_start_baseline"]:
                    reason = "drawdown_compression_portfolio_budget_exceeded"
                else:
                    reason = "portfolio_total_risk_ceiling_exceeded"
                approved_risk_pct = 0.0

        approved_amount = self._risk_amount(approved_risk_pct)
        total_after = total_before + approved_risk_pct if accepted else total_before + max(0.0, requested or 0.0)
        result_r = fnum(candidate.result_r, 0.0) or 0.0
        opportunity_amount = 0.0 if accepted else result_r * requested_amount

        decision_obj = SchedulerDecision(
            accepted=accepted,
            decision=decision,
            reason=reason,
            requested_risk_pct=requested,
            approved_risk_pct=approved_risk_pct,
            new_trade_risk_amount=requested_amount,
            approved_new_trade_risk_amount=approved_amount,
            cost_buffer_pct=cost_buffer_pct,
            open_risk_pct_before=open_risk_pct,
            pending_risk_pct_before=pending_risk_pct,
            same_symbol_risk_pct_before=same_symbol_risk_pct,
            correlated_cluster_risk_pct_before=cluster_risk_pct,
            residual_exposure_pct_before=residual_pct,
            total_risk_pct_before=total_before,
            total_risk_pct_after=total_after,
            dynamic_portfolio_ceiling_pct=dynamic_ceiling,
            account_available_risk_pct=budget["available_risk_pct"],
            day_start_baseline=budget["day_start_baseline"],
            current_equity=budget["current_equity"],
            realized_proxy_pnl=self.realized_proxy_pnl,
            daily_cushion_before=budget["daily_cushion"],
            overall_cushion_before=budget["overall_cushion"],
            internal_daily_cushion_before=budget["internal_daily_cushion"],
            same_symbol_conflict_ids=[exposure.selected_row_id for exposure in same_symbol],
            correlated_cluster_conflict_ids=[
                exposure.selected_row_id for exposure in cluster_exposures
            ],
            priority_rank_in_batch=priority_rank_in_batch,
            priority_score=candidate.priority_score,
            priority_components=candidate.priority_components,
            opportunity_cost_r=0.0 if accepted else result_r,
            opportunity_cost_amount=opportunity_amount,
            risk_release_dt=candidate.risk_release_dt if accepted else None,
        )
        if accepted:
            residual_fraction = 0.0
            if candidate.partial_release_dt is not None:
                residual_fraction = 0.5
            self.active.append(
                ActiveExposure(
                    row_id=candidate.row_id,
                    selected_row_id=candidate.selected_row_id,
                    symbol=candidate.symbol,
                    cluster=candidate.cluster,
                    side=candidate.side,
                    exit_dt=candidate.exit_dt,
                    risk_release_dt=candidate.risk_release_dt,
                    partial_release_dt=candidate.partial_release_dt,
                    requested_risk_pct=max(0.0, requested or 0.0),
                    approved_risk_pct=approved_risk_pct,
                    residual_exposure_pct=approved_risk_pct * residual_fraction,
                    result_r=result_r,
                )
            )
        self.stats.max_active_positions = max(self.stats.max_active_positions, len(self.active))
        self.stats.update(decision_obj, candidate)
        return decision_obj

    def decide_batch(self, candidates: list[SchedulerCandidate]) -> list[tuple[SchedulerCandidate, SchedulerDecision]]:
        ordered = sorted(
            candidates,
            key=lambda candidate: (-candidate.priority_score, candidate.input_sequence, candidate.row_id),
        )
        decisions: list[tuple[SchedulerCandidate, SchedulerDecision]] = []
        for rank, candidate in enumerate(ordered, start=1):
            decisions.append((candidate, self.decide(candidate, priority_rank_in_batch=rank)))
        return decisions

    def finalize(self) -> None:
        far_future = datetime.max.replace(tzinfo=timezone.utc)
        self._release_matured(far_future)
