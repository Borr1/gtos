from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
ROUTE_ID = "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"

STAGE03_LEDGER_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_LEDGER_2026-05-25.jsonl"
)
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
PROP_ATTEMPT_LEDGER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_PROP_ATTEMPT_LEDGER_2026-05-25.jsonl"
)
PROP_POLICY_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_PROP_POLICY_COMPARISON_SUMMARY_2026-05-25.json"
)
STAGE04_DECISION_LEDGER_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE04_PROP_GOVERNOR_DECISION_LEDGER_2026-05-25.jsonl"
)

INITIAL_BALANCE = 100000.0
FULL_RISK_PCT = 2.0
MIN_REDUCED_RISK_PCT = 0.25
MICRO_RISK_PCT = 0.10
SPREAD_BUFFER_PCT = 0.10
DAILY_LOSS_LIMIT_PCT = 5.0
OVERALL_MAX_LOSS_PCT = 10.0
PHASE_TARGETS = {1: 8.0, 2: 5.0}

SCENARIOS = {
    "baseline_executable_stream_plus_prop_contract": "baseline_executable_stream_plus_prop_contract",
    "vnext_executable_stream_with_ev_prop_governance_contract": (
        "vnext_executable_stream_with_ev_prop_governance_contract"
    ),
}

POLICIES = (
    "ALLOW_FULL_RISK_SEGMENTED",
    "REDUCE_RISK_TO_BUDGET",
    "MICRO_RISK_NEAR_BUDGET",
    "HIGH_QUALITY_ONLY",
    "DEFER_UNTIL_RESET",
    "ACCOUNT_ABANDON_OR_RESTART",
    "BLOCK_ALL_NEAR_LIMIT",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def git_status_short() -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return ["GIT_STATUS_FAILED"]
    return [line for line in output.splitlines() if line.strip()]


def parse_utc(value: Any) -> datetime:
    text = str(value or "")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def reset_day_key(as_of: datetime) -> str:
    return (as_of + timedelta(hours=3)).date().isoformat()


def iter_stage03_rows() -> Iterable[dict[str, Any]]:
    with STAGE03_LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def high_quality_row(row: dict[str, Any]) -> bool:
    source_mode = str(row.get("source_mode") or "")
    session = str(row.get("session") or "")
    terminal = str(row.get("terminal_outcome") or "")
    return (
        source_mode in {"OHLC_M1_CSV", "LOCAL_TICK_PARQUET", "SIERRA_SCID_CONVERTED_M1_PROXY"}
        and session in {"london", "ny", "tokyo"}
        and terminal != "missing_source_denominator_excluded"
    )


@dataclass
class AttemptState:
    scenario: str
    policy: str
    attempt_id: int = 1
    phase: int = 1
    equity: float = INITIAL_BALANCE
    day_start_equity: float = INITIAL_BALANCE
    current_day_key: str | None = None
    attempt_start_utc: str | None = None
    phase_start_utc: str | None = None
    trades: int = 0
    phase1_passed: bool = False

    def roll_day(self, as_of: datetime) -> None:
        day_key = reset_day_key(as_of)
        if self.current_day_key != day_key:
            self.current_day_key = day_key
            self.day_start_equity = self.equity

    def daily_floor(self) -> float:
        return self.day_start_equity - INITIAL_BALANCE * DAILY_LOSS_LIMIT_PCT / 100.0

    def overall_floor(self) -> float:
        return INITIAL_BALANCE * (1.0 - OVERALL_MAX_LOSS_PCT / 100.0)

    def target_equity(self) -> float:
        return INITIAL_BALANCE * (1.0 + PHASE_TARGETS[self.phase] / 100.0)

    def reset_for_new_attempt(self, next_attempt_id: int, as_of: datetime) -> None:
        self.attempt_id = next_attempt_id
        self.phase = 1
        self.equity = INITIAL_BALANCE
        self.day_start_equity = INITIAL_BALANCE
        self.current_day_key = reset_day_key(as_of)
        self.attempt_start_utc = as_of.isoformat()
        self.phase_start_utc = as_of.isoformat()
        self.trades = 0
        self.phase1_passed = False

    def reset_for_phase2(self, as_of: datetime) -> None:
        self.phase = 2
        self.equity = INITIAL_BALANCE
        self.day_start_equity = INITIAL_BALANCE
        self.current_day_key = reset_day_key(as_of)
        self.phase_start_utc = as_of.isoformat()
        self.phase1_passed = True


@dataclass
class PolicyMetrics:
    scenario: str
    policy: str
    input_rows: int = 0
    allowed_trades: int = 0
    blocked_trades: int = 0
    reduced_risk_trades: int = 0
    micro_risk_trades: int = 0
    high_quality_skips: int = 0
    deferred_trades: int = 0
    abandon_restarts: int = 0
    accepted_winners: int = 0
    accepted_losers: int = 0
    missed_winners: int = 0
    avoided_losers: int = 0
    total_r: float = 0.0
    risk_adjusted_r: float = 0.0
    blocked_positive_r: float = 0.0
    blocked_negative_r: float = 0.0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0
    phase1_passes: int = 0
    phase2_passes: int = 0
    failed_attempts: int = 0
    abandoned_attempts: int = 0
    open_attempts: int = 0
    attempts_started: int = 1
    max_drawdown_pct: float = 0.0
    max_loss_streak: int = 0
    current_loss_streak: int = 0
    terminal_attempt_days: list[float] = field(default_factory=list)
    pass_attempt_days: list[float] = field(default_factory=list)
    fail_or_abandon_attempt_days: list[float] = field(default_factory=list)
    selected_coverage: dict[str, Counter[str]] = field(
        default_factory=lambda: {
            "symbols": Counter(),
            "sessions": Counter(),
            "sides": Counter(),
            "frameworks": Counter(),
            "source_modes": Counter(),
            "months": Counter(),
        }
    )

    def observe_block(self, row: dict[str, Any], reason: str) -> None:
        self.blocked_trades += 1
        r_value = _as_float(row.get("simulated_r"))
        if r_value is None:
            return
        if r_value > 0:
            self.missed_winners += 1
            self.blocked_positive_r += r_value
        elif r_value < 0:
            self.avoided_losers += 1
            self.blocked_negative_r += abs(r_value)

    def observe_trade(self, row: dict[str, Any], risk_pct: float, before_equity: float, after_equity: float) -> None:
        self.allowed_trades += 1
        for key, source_key in (
            ("symbols", "symbol"),
            ("sessions", "session"),
            ("sides", "side"),
            ("frameworks", "framework"),
            ("source_modes", "source_mode"),
            ("months", "month"),
        ):
            self.selected_coverage[key][str(row.get(source_key) or "")] += 1
        r_value = _as_float(row.get("simulated_r"))
        if r_value is None:
            return
        self.total_r += r_value
        self.risk_adjusted_r += r_value * (risk_pct / FULL_RISK_PCT)
        if r_value > 0:
            self.accepted_winners += 1
            self.gross_win_r += r_value
            self.current_loss_streak = 0
        elif r_value < 0:
            self.accepted_losers += 1
            self.gross_loss_r += abs(r_value)
            self.current_loss_streak += 1
            self.max_loss_streak = max(self.max_loss_streak, self.current_loss_streak)
        drawdown = 0.0 if before_equity <= 0 else max(0.0, (before_equity - after_equity) / before_equity * 100.0)
        self.max_drawdown_pct = max(self.max_drawdown_pct, drawdown)

    def observe_attempt_terminal(self, status: str, duration_days: float | None) -> None:
        if duration_days is None:
            return
        self.terminal_attempt_days.append(duration_days)
        if status == "phase2_passed_challenge_complete":
            self.pass_attempt_days.append(duration_days)
        if status in {"failed_prop_limit", "abandoned_for_restart"}:
            self.fail_or_abandon_attempt_days.append(duration_days)

    def to_record(self) -> dict[str, Any]:
        performance_count = self.accepted_winners + self.accepted_losers
        expectancy = self.total_r / performance_count if performance_count else None
        win_rate = self.accepted_winners / performance_count if performance_count else None
        profit_factor = None if self.gross_loss_r == 0 else self.gross_win_r / self.gross_loss_r
        completed_attempts = self.phase2_passes + self.failed_attempts + self.abandoned_attempts
        attempted = max(1, self.attempts_started)
        account_loss_rate = (self.failed_attempts + self.abandoned_attempts) / attempted
        pass_rate = self.phase2_passes / attempted
        payout_grid = []
        for account_fee in (549.0, 599.0, 999.0):
            for payout_proxy in (4000.0, 8000.0, 12000.0):
                expected = pass_rate * payout_proxy - account_loss_rate * account_fee
                payout_grid.append(
                    {
                        "account_fee_usd": account_fee,
                        "payout_proxy_usd": payout_proxy,
                        "expected_value_per_attempt_usd": round(expected, 6),
                    }
                )
        avg_terminal_days = (
            sum(self.terminal_attempt_days) / len(self.terminal_attempt_days)
            if self.terminal_attempt_days
            else None
        )
        avg_pass_days = (
            sum(self.pass_attempt_days) / len(self.pass_attempt_days)
            if self.pass_attempt_days
            else None
        )
        avg_fail_days = (
            sum(self.fail_or_abandon_attempt_days) / len(self.fail_or_abandon_attempt_days)
            if self.fail_or_abandon_attempt_days
            else None
        )
        reference_ev = payout_grid[4]["expected_value_per_attempt_usd"]
        reference_ev_per_terminal_day = (
            reference_ev / max(1.0, avg_terminal_days)
            if avg_terminal_days is not None
            else None
        )
        return {
            "scenario": self.scenario,
            "policy": self.policy,
            "input_rows": self.input_rows,
            "attempts_started": self.attempts_started,
            "completed_attempts": completed_attempts,
            "open_attempts": self.open_attempts,
            "phase1_passes": self.phase1_passes,
            "phase2_passes": self.phase2_passes,
            "failed_attempts": self.failed_attempts,
            "abandoned_attempts": self.abandoned_attempts,
            "account_loss_rate": round(account_loss_rate, 12),
            "pass_rate": round(pass_rate, 12),
            "allowed_trades": self.allowed_trades,
            "blocked_trades": self.blocked_trades,
            "reduced_risk_trades": self.reduced_risk_trades,
            "micro_risk_trades": self.micro_risk_trades,
            "high_quality_skips": self.high_quality_skips,
            "deferred_trades": self.deferred_trades,
            "abandon_restarts": self.abandon_restarts,
            "accepted_winners": self.accepted_winners,
            "accepted_losers": self.accepted_losers,
            "missed_winners": self.missed_winners,
            "avoided_losers": self.avoided_losers,
            "blocked_positive_r": round(self.blocked_positive_r, 12),
            "blocked_negative_r": round(self.blocked_negative_r, 12),
            "opportunity_cost_if_blocked_rows_taken_r": round(
                self.blocked_positive_r - self.blocked_negative_r,
                12,
            ),
            "total_r": round(self.total_r, 12),
            "risk_adjusted_r": round(self.risk_adjusted_r, 12),
            "expectancy_r": round(expectancy, 12) if expectancy is not None else None,
            "win_rate": round(win_rate, 12) if win_rate is not None else None,
            "profit_factor": round(profit_factor, 12) if profit_factor is not None else None,
            "max_drawdown_pct": round(self.max_drawdown_pct, 12),
            "max_loss_streak": self.max_loss_streak,
            "avg_time_to_terminal_days": (
                round(avg_terminal_days, 6) if avg_terminal_days is not None else None
            ),
            "avg_time_to_pass_days": round(avg_pass_days, 6) if avg_pass_days is not None else None,
            "avg_time_to_fail_or_abandon_days": (
                round(avg_fail_days, 6) if avg_fail_days is not None else None
            ),
            "reference_ev_per_terminal_day_usd_fee599_payout8000": (
                round(reference_ev_per_terminal_day, 6)
                if reference_ev_per_terminal_day is not None
                else None
            ),
            "selected_only_coverage": {
                key: dict(counter.most_common())
                for key, counter in self.selected_coverage.items()
            },
            "payout_sensitivity_grid": payout_grid,
            "ev_reference": {
                "account_fee_unknown": True,
                "payout_amount_unknown": True,
                "formula": "pass_rate*payout_proxy_usd - account_loss_rate*account_fee_usd",
            },
        }


def budget_cushions(state: AttemptState) -> dict[str, float]:
    return {
        "daily_floor": state.daily_floor(),
        "overall_floor": state.overall_floor(),
        "remaining_daily_cushion": state.equity - state.daily_floor(),
        "remaining_overall_cushion": state.equity - state.overall_floor(),
    }


def max_risk_pct_available(state: AttemptState) -> float:
    cushions = budget_cushions(state)
    max_amount = min(cushions["remaining_daily_cushion"], cushions["remaining_overall_cushion"])
    max_amount -= state.equity * SPREAD_BUFFER_PCT / 100.0
    if state.equity <= 0:
        return 0.0
    return max(0.0, max_amount / state.equity * 100.0)


def choose_action(policy: str, row: dict[str, Any], state: AttemptState) -> dict[str, Any]:
    max_pct = max_risk_pct_available(state)
    cushions = budget_cushions(state)
    daily_binding = cushions["remaining_daily_cushion"] <= cushions["remaining_overall_cushion"]
    quality = high_quality_row(row)

    def decision(action: str, risk_pct: float, reason: str) -> dict[str, Any]:
        return {
            "action": action,
            "risk_pct": round(max(0.0, risk_pct), 12),
            "reason": reason,
            "max_available_risk_pct": round(max_pct, 12),
            "remaining_daily_cushion": round(cushions["remaining_daily_cushion"], 6),
            "remaining_overall_cushion": round(cushions["remaining_overall_cushion"], 6),
            "decision_inputs_no_future_r": True,
            "row_quality": "HIGH_QUALITY" if quality else "STANDARD_OR_SOURCE_WEAK",
        }

    if policy == "HIGH_QUALITY_ONLY" and not quality:
        return decision("BLOCK", 0.0, "high_quality_only_source_session_filter")
    if policy == "BLOCK_ALL_NEAR_LIMIT" and max_pct < FULL_RISK_PCT * 2:
        return decision("BLOCK", 0.0, "block_all_near_limit_buffer")
    if max_pct >= FULL_RISK_PCT:
        risk = 1.0 if policy == "HIGH_QUALITY_ONLY" else FULL_RISK_PCT
        return decision("ALLOW", risk, "budget_allows_policy_risk")
    if policy in {"ALLOW_FULL_RISK_SEGMENTED", "BLOCK_ALL_NEAR_LIMIT"}:
        return decision("BLOCK", 0.0, "budget_does_not_allow_full_risk")
    if policy == "DEFER_UNTIL_RESET":
        if daily_binding and cushions["remaining_overall_cushion"] >= state.equity * MIN_REDUCED_RISK_PCT / 100.0:
            return decision("DEFER_UNTIL_RESET", 0.0, "daily_binding_defer_until_reset")
        return decision("BLOCK", 0.0, "overall_or_min_budget_block")
    if policy == "REDUCE_RISK_TO_BUDGET":
        if max_pct >= MIN_REDUCED_RISK_PCT:
            return decision("REDUCE_RISK", min(FULL_RISK_PCT, max_pct), "reduce_to_available_budget")
        if daily_binding:
            return decision("DEFER_UNTIL_RESET", 0.0, "below_min_risk_daily_binding_defer")
        return decision("BLOCK", 0.0, "below_min_risk_overall_block")
    if policy == "MICRO_RISK_NEAR_BUDGET":
        if max_pct >= MICRO_RISK_PCT:
            return decision("MICRO_RISK", MICRO_RISK_PCT, "micro_risk_fits_budget")
        if daily_binding:
            return decision("DEFER_UNTIL_RESET", 0.0, "micro_risk_daily_binding_defer")
        return decision("BLOCK", 0.0, "micro_risk_not_fit_overall_block")
    if policy == "ACCOUNT_ABANDON_OR_RESTART":
        if max_pct >= MIN_REDUCED_RISK_PCT:
            return decision("REDUCE_RISK", min(FULL_RISK_PCT, max_pct), "restart_policy_reduce_to_budget")
        if daily_binding and cushions["remaining_overall_cushion"] >= state.equity * MIN_REDUCED_RISK_PCT / 100.0:
            return decision("DEFER_UNTIL_RESET", 0.0, "restart_policy_daily_defer")
        return decision("ACCOUNT_ABANDON_OR_RESTART", 0.0, "overall_budget_exhausted_restart_attempt")
    return decision("BLOCK", 0.0, "unknown_policy_block")


def selected_rows_by_scenario() -> dict[str, list[dict[str, Any]]]:
    rows = {name: [] for name in SCENARIOS}
    for row in iter_stage03_rows():
        membership = row.get("scenario_membership") or {}
        for scenario, key in SCENARIOS.items():
            if membership.get(key):
                rows[scenario].append(row)
    for scenario_rows in rows.values():
        scenario_rows.sort(key=lambda item: str(item.get("as_of_utc") or ""))
    return rows


def finalize_attempt(
    *,
    attempt_rows: list[dict[str, Any]],
    scenario: str,
    policy: str,
    state: AttemptState,
    status: str,
    reason: str,
    out_attempt,
) -> float | None:
    if not attempt_rows and status == "open_no_trades":
        return None
    first = attempt_rows[0]["as_of_utc"] if attempt_rows else state.attempt_start_utc
    last = attempt_rows[-1]["as_of_utc"] if attempt_rows else state.phase_start_utc
    duration_days = None
    if first and last:
        duration_days = max(0.0, (parse_utc(last) - parse_utc(first)).total_seconds() / 86400.0)
    out_attempt.write(
        json.dumps(
            {
                "schema_version": "vnext_production_candidate_repair_stage04_prop_attempt_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR",
                "scenario": scenario,
                "policy": policy,
                "attempt_id": state.attempt_id,
                "terminal_status": status,
                "terminal_reason": reason,
                "phase": state.phase,
                "phase1_passed": state.phase1_passed,
                "start_utc": first,
                "end_utc": last,
                "duration_days": round(duration_days, 6) if duration_days is not None else None,
                "trade_count": len(attempt_rows),
                "ending_equity": round(state.equity, 6),
                "daily_floor": round(state.daily_floor(), 6),
                "overall_floor": round(state.overall_floor(), 6),
                "segmented_account_attempt": True,
            },
            sort_keys=True,
        )
        + "\n"
    )
    return duration_days


def run_policy_replay(
    *,
    scenario: str,
    policy: str,
    rows: list[dict[str, Any]],
    out_decision,
    out_attempt,
) -> PolicyMetrics:
    metrics = PolicyMetrics(scenario=scenario, policy=policy, input_rows=len(rows))
    state = AttemptState(scenario=scenario, policy=policy)
    attempt_rows: list[dict[str, Any]] = []
    next_attempt_id = 1
    equity_peak = INITIAL_BALANCE

    for index, row in enumerate(rows, start=1):
        as_of = parse_utc(row.get("as_of_utc"))
        if state.attempt_start_utc is None:
            state.reset_for_new_attempt(next_attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, next_attempt_id)
        state.roll_day(as_of)
        action = choose_action(policy, row, state)
        if action["action"] == "ACCOUNT_ABANDON_OR_RESTART":
            metrics.abandon_restarts += 1
            metrics.abandoned_attempts += 1
            duration_days = finalize_attempt(
                attempt_rows=attempt_rows,
                scenario=scenario,
                policy=policy,
                state=state,
                status="abandoned_for_restart",
                reason=action["reason"],
                out_attempt=out_attempt,
            )
            metrics.observe_attempt_terminal("abandoned_for_restart", duration_days)
            next_attempt_id += 1
            state.reset_for_new_attempt(next_attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, next_attempt_id)
            attempt_rows = []
            action = choose_action(policy, row, state)
        decision_attempt_id = state.attempt_id
        decision_phase = state.phase

        r_value = _as_float(row.get("simulated_r"))
        selected = action["action"] in {"ALLOW", "REDUCE_RISK", "MICRO_RISK"}
        before_equity = state.equity
        after_equity = before_equity
        terminal_event: str | None = None

        if not selected:
            if action["action"] == "DEFER_UNTIL_RESET":
                metrics.deferred_trades += 1
            if action["reason"] == "high_quality_only_source_session_filter":
                metrics.high_quality_skips += 1
            metrics.observe_block(row, action["reason"])
        else:
            if action["action"] == "REDUCE_RISK":
                metrics.reduced_risk_trades += 1
            if action["action"] == "MICRO_RISK":
                metrics.micro_risk_trades += 1
            if r_value is not None:
                after_equity = before_equity + before_equity * action["risk_pct"] / 100.0 * r_value
                state.equity = after_equity
                equity_peak = max(equity_peak, state.equity)
            state.trades += 1
            attempt_rows.append(
                {
                    "as_of_utc": row.get("as_of_utc"),
                    "candidate_id": row.get("candidate_id"),
                    "risk_pct": action["risk_pct"],
                    "simulated_r": r_value,
                }
            )
            metrics.observe_trade(row, action["risk_pct"], equity_peak, after_equity)
            if state.equity <= state.daily_floor() or state.equity <= state.overall_floor():
                metrics.failed_attempts += 1
                terminal_event = "failed_prop_limit"
                duration_days = finalize_attempt(
                    attempt_rows=attempt_rows,
                    scenario=scenario,
                    policy=policy,
                    state=state,
                    status=terminal_event,
                    reason="daily_or_overall_floor_breached_after_trade",
                    out_attempt=out_attempt,
                )
                metrics.observe_attempt_terminal("failed_prop_limit", duration_days)
                next_attempt_id += 1
                state.reset_for_new_attempt(next_attempt_id, as_of)
                metrics.attempts_started = max(metrics.attempts_started, next_attempt_id)
                attempt_rows = []
            elif state.equity >= state.target_equity():
                if state.phase == 1:
                    metrics.phase1_passes += 1
                    terminal_event = "phase1_passed"
                    state.reset_for_phase2(as_of)
                else:
                    metrics.phase2_passes += 1
                    terminal_event = "phase2_passed_challenge_complete"
                    duration_days = finalize_attempt(
                        attempt_rows=attempt_rows,
                        scenario=scenario,
                        policy=policy,
                        state=state,
                        status=terminal_event,
                        reason="phase2_target_reached",
                        out_attempt=out_attempt,
                    )
                    metrics.observe_attempt_terminal(
                        "phase2_passed_challenge_complete",
                        duration_days,
                    )
                    next_attempt_id += 1
                    state.reset_for_new_attempt(next_attempt_id, as_of)
                    metrics.attempts_started = max(metrics.attempts_started, next_attempt_id)
                    attempt_rows = []

        out_decision.write(
            json.dumps(
                {
                    "schema_version": "vnext_production_candidate_repair_stage04_prop_decision_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR",
                    "scenario": scenario,
                    "policy": policy,
                    "row_index": index,
                    "candidate_id": row.get("candidate_id"),
                    "as_of_utc": row.get("as_of_utc"),
                    "symbol": row.get("symbol"),
                    "session": row.get("session"),
                    "side": row.get("side"),
                    "framework": row.get("framework"),
                    "source_mode": row.get("source_mode"),
                    "month": row.get("month"),
                    "attempt_id": decision_attempt_id,
                    "phase": decision_phase,
                    "action": action["action"],
                    "risk_pct": action["risk_pct"],
                    "reason": action["reason"],
                    "selected": selected,
                    "simulated_r_scoring_only": r_value,
                    "decision_inputs_no_future_r": action["decision_inputs_no_future_r"],
                    "pre_trade_equity": round(before_equity, 6),
                    "post_trade_equity": round(after_equity, 6),
                    "remaining_daily_cushion": action["remaining_daily_cushion"],
                    "remaining_overall_cushion": action["remaining_overall_cushion"],
                    "terminal_event_after_scoring": terminal_event,
                },
                sort_keys=True,
            )
            + "\n"
        )

    if attempt_rows:
        metrics.open_attempts += 1
        duration_days = finalize_attempt(
            attempt_rows=attempt_rows,
            scenario=scenario,
            policy=policy,
            state=state,
            status="open_at_replay_end",
            reason="historical_stream_ended_before_pass_or_fail",
            out_attempt=out_attempt,
        )
        metrics.observe_attempt_terminal("open_at_replay_end", duration_days)
    return metrics


def best_policy(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        records.values(),
        key=lambda item: (
            item.get("reference_ev_per_terminal_day_usd_fee599_payout8000") or -10**9,
            item["payout_sensitivity_grid"][4]["expected_value_per_attempt_usd"],
            item["risk_adjusted_r"],
            item["pass_rate"],
            -item["account_loss_rate"],
        ),
        reverse=True,
    )
    return {
        "policy": ranked[0]["policy"],
        "reference_expected_value_per_attempt_usd": ranked[0]["payout_sensitivity_grid"][4][
            "expected_value_per_attempt_usd"
        ],
        "reference_ev_per_terminal_day_usd_fee599_payout8000": ranked[0].get(
            "reference_ev_per_terminal_day_usd_fee599_payout8000"
        ),
        "avg_time_to_pass_days": ranked[0].get("avg_time_to_pass_days"),
        "avg_time_to_terminal_days": ranked[0].get("avg_time_to_terminal_days"),
        "risk_adjusted_r": ranked[0]["risk_adjusted_r"],
        "pass_rate": ranked[0]["pass_rate"],
        "account_loss_rate": ranked[0]["account_loss_rate"],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_stage04() -> dict[str, Any]:
    if not STAGE03_LEDGER_PATH.exists():
        raise FileNotFoundError(STAGE03_LEDGER_PATH)
    rows_by_scenario = selected_rows_by_scenario()
    summary_records: dict[str, dict[str, Any]] = {}
    with STAGE04_DECISION_LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as out_decision, PROP_ATTEMPT_LEDGER_PATH.open(
        "w", encoding="utf-8", newline="\n"
    ) as out_attempt:
        for scenario, rows in rows_by_scenario.items():
            for policy in POLICIES:
                metrics = run_policy_replay(
                    scenario=scenario,
                    policy=policy,
                    rows=rows,
                    out_decision=out_decision,
                    out_attempt=out_attempt,
                )
                summary_records[f"{scenario}|{policy}"] = metrics.to_record()

    by_scenario: dict[str, dict[str, Any]] = {}
    for scenario in SCENARIOS:
        records = {
            policy: summary_records[f"{scenario}|{policy}"]
            for policy in POLICIES
        }
        by_scenario[scenario] = {
            "input_rows": len(rows_by_scenario[scenario]),
            "policy_metrics": records,
            "best_policy_reference_fee_599_payout_8000": best_policy(records),
        }
    summary = {
        "schema_version": "vnext_production_candidate_repair_stage04_prop_policy_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR",
        "created_at_utc": utc_now(),
        "current_git_head": git_head(),
        "input_stage03_ledger": rel(STAGE03_LEDGER_PATH),
        "input_stage03_sha256": sha256_file(STAGE03_LEDGER_PATH),
        "segmented_attempt_model": {
            "initial_balance": INITIAL_BALANCE,
            "daily_loss_limit_pct": DAILY_LOSS_LIMIT_PCT,
            "overall_max_loss_pct": OVERALL_MAX_LOSS_PCT,
            "daily_reset": "00:00_GMT_PLUS_3",
            "phase_targets": PHASE_TARGETS,
            "segmented_account_attempts_not_continuous_2022_2026": True,
            "decision_inputs_exclude_future_r": True,
        },
        "policies_compared": list(POLICIES),
        "scenarios": by_scenario,
        "decision_ledger": rel(STAGE04_DECISION_LEDGER_PATH),
        "attempt_ledger": rel(PROP_ATTEMPT_LEDGER_PATH),
        "stage04_decision": "segmented_ev_prop_governor_policy_matrix_built",
    }
    write_json(PROP_POLICY_SUMMARY_PATH, summary)
    update_state(summary)
    return summary


def update_state(summary: dict[str, Any]) -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["current_stage"] = "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR"
    state["active_invariant"] = "build_segmented_ev_optimized_prop_challenge_governor"
    state["first_incomplete_invariant"] = "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR"
    state["exact_next_action"] = (
        "Run Stage04 verifier, then repair harmful vNext AVOID/pre-AI pressure with selected-only EV evidence."
    )
    state.setdefault("stage_status_table", {})[
        "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR"
    ] = "in_progress"
    state.setdefault("output_artifact_paths", {}).update(
        {
            "stage04_prop_governor_decision_ledger": rel(STAGE04_DECISION_LEDGER_PATH),
            "prop_attempt_ledger": rel(PROP_ATTEMPT_LEDGER_PATH),
            "prop_policy_comparison_summary": rel(PROP_POLICY_SUMMARY_PATH),
        }
    )
    state.setdefault("row_count_hash_coverage", {}).update(
        {
            "stage04_prop_governor_decision_rows": sum(
                scenario["input_rows"] * len(POLICIES)
                for scenario in summary["scenarios"].values()
            ),
            "stage04_prop_attempt_ledger_sha256": sha256_file(PROP_ATTEMPT_LEDGER_PATH),
            "stage04_prop_decision_ledger_sha256": sha256_file(STAGE04_DECISION_LEDGER_PATH),
        }
    )
    state.setdefault("repairs_applied", []).append(
        "stage04_segmented_ev_prop_challenge_governor_policy_matrix_materialized"
    )
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "Which prop governance policy has the best account-attempt EV after segmentation?",
            "status": "closed_stage04_policy_matrix_built_pending_verifier",
            "evidence_path": rel(PROP_POLICY_SUMMARY_PATH),
            "best_policy_by_scenario": {
                scenario: data["best_policy_reference_fee_599_payout_8000"]
                for scenario, data in summary["scenarios"].items()
            },
        }
    )
    state["updated_at_utc"] = utc_now()
    write_json(STATE_PATH, state)


if __name__ == "__main__":
    result = build_stage04()
    print(
        json.dumps(
            {
                "ok": True,
                "summary": rel(PROP_POLICY_SUMMARY_PATH),
                "decision_ledger": rel(STAGE04_DECISION_LEDGER_PATH),
                "attempt_ledger": rel(PROP_ATTEMPT_LEDGER_PATH),
                "best_policy_by_scenario": {
                    scenario: data["best_policy_reference_fee_599_payout_8000"]["policy"]
                    for scenario, data in result["scenarios"].items()
                },
            },
            sort_keys=True,
        )
    )
