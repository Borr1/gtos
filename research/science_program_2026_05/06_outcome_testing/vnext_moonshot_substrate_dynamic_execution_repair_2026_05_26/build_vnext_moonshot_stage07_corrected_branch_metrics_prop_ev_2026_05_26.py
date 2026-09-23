from __future__ import annotations

import json
import math
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"

STAGE04_INDEX = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SHARD_INDEX_{DATE_ID}.jsonl"
STAGE04_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_{DATE_ID}.json"
STAGE05_REGISTRY = ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_{DATE_ID}.jsonl"
STAGE06_FEATURES = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FEATURE_LEDGER_{DATE_ID}.jsonl"
STAGE06_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_SUMMARY_{DATE_ID}.json"
STATE_PATH = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"

OUTPUT_BRANCH_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_METRICS_LEDGER_{DATE_ID}.jsonl"
OUTPUT_PROP_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_PROP_EV_ATTEMPT_LEDGER_{DATE_ID}.jsonl"
OUTPUT_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_PROP_EV_OPPORTUNITY_COST_REPORT_{DATE_ID}.md"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_{DATE_ID}.json"

POLICY_NAMES = [
    "legacy_fixed_1.5r",
    "ai_target",
    "live_current_j46_j49",
    "partial_be_runner",
    "be_after_trigger",
    "trailing_runner",
    "time_stop_only",
    "early_cut_if_no_progress",
    "path_aware_runner",
]

PROP_POLICIES = [
    "ALLOW_FULL_RISK_SEGMENTED",
    "REDUCE_RISK_TO_BUDGET",
    "MICRO_RISK_NEAR_BUDGET",
    "HIGH_QUALITY_ONLY",
    "DEFER_UNTIL_RESET",
    "ACCOUNT_ABANDON_OR_RESTART",
    "BLOCK_ALL_NEAR_LIMIT",
    "EV_OPTIMIZED_REDUCE_OR_DEFER",
]

INITIAL_BALANCE = 100000.0
PHASE_TARGETS = {1: 8.0, 2: 5.0}
redacted_account_DAILY_LOSS_LIMIT_PCT = 5.0
redacted_account_OVERALL_MAX_LOSS_PCT = 10.0
MIN_REDUCED_RISK_PCT = 0.25
MICRO_RISK_PCT = 0.10
SPREAD_BUFFER_PCT = 0.10
REFERENCE_ACCOUNT_FEE_USD = 599.0
REFERENCE_PAYOUT_PROXY_USD = 8000.0

DIMENSIONS = [
    "symbol",
    "transfer_group",
    "framework",
    "side",
    "session_bucket",
    "kill_zone_position",
    "session_subwindow",
    "weekday",
    "month",
    "quarter",
    "source_mode",
    "source_window_complete",
    "trend_state_20",
    "volatility_state_14_vs_50",
    "compression_expansion_state",
    "liquidity_sweep_proxy_state",
    "news_calendar_coverage_status",
    "news_high_impact_within_120m",
    "policy_reversal_bucket",
]

BASE_BRANCHES = [
    {
        "branch_id": "raw_repaired_all_replayable",
        "branch_family": "raw_repaired",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "All Stage04 replayable M15 rows with corrected dynamic policy labels.",
    },
    {
        "branch_id": "source_complete_only",
        "branch_family": "source_complete",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "Rows whose Stage04 source window was marked complete.",
    },
    {
        "branch_id": "missing_source_excluded_asof_computed",
        "branch_family": "missing_source_excluded",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "Rows with as-of OHLC features computed from local source files.",
    },
    {
        "branch_id": "high_quality_source_complete_kz",
        "branch_family": "high_quality",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "Source-complete, configured-kill-zone rows with complete market-awareness fields and no high-impact calendar event within 120 minutes.",
    },
    {
        "branch_id": "high_quality_asof_kz",
        "branch_family": "high_quality",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "As-of-computed configured-kill-zone rows with complete market-awareness fields and no high-impact calendar event within 120 minutes.",
    },
    {
        "branch_id": "aggressive_research_asof_all_sessions",
        "branch_family": "aggressive_research",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "Feature-complete rows across all sessions, including off-kill-zone rows for research-only opportunity sizing.",
    },
    {
        "branch_id": "context_recovery_off_kz_side_aligned",
        "branch_family": "context_recovery",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "Off-kill-zone rows with feature-complete, side-aligned trend context.",
    },
    {
        "branch_id": "ml_candidate_feature_complete",
        "branch_family": "ml",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "Rows with enough decision-safe market-awareness fields for local surrogate/ML experiments.",
    },
    {
        "branch_id": "ai_required_context_rich",
        "branch_family": "ai_required",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "Rows whose as-of context is rich or ambiguous enough to justify paid-AI triage in later budget design.",
    },
    {
        "branch_id": "no_paid_mechanical_diagnostic",
        "branch_family": "no_paid_diagnostic",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "Mechanical-looking rows used only to size no-paid diagnostic coverage, not to approve AI removal.",
    },
    {
        "branch_id": "prop_ev_optimized_side_aligned_kz",
        "branch_family": "prop_ev_optimized",
        "selection_class": "decision_safe_asof",
        "prop_replay_eligible": True,
        "description": "Configured-kill-zone, side-aligned, feature-complete rows with no high-impact calendar proximity.",
    },
    {
        "branch_id": "monitoring_only_ambiguous_path",
        "branch_family": "monitoring_only",
        "selection_class": "post_outcome_diagnostic",
        "prop_replay_eligible": False,
        "description": "Rows whose live-current replay carried same-bar ambiguity; monitoring/verifier use only.",
    },
    {
        "branch_id": "dynamic_repair_needed_legacy_winner_to_live_nonpositive",
        "branch_family": "execution_repair_diagnostic",
        "selection_class": "post_outcome_diagnostic",
        "prop_replay_eligible": False,
        "description": "Fixed-target winners that live-current dynamic management turns non-positive.",
    },
    {
        "branch_id": "dynamic_recovery_legacy_nonpositive_to_live_winner",
        "branch_family": "execution_repair_diagnostic",
        "selection_class": "post_outcome_diagnostic",
        "prop_replay_eligible": False,
        "description": "Legacy non-positive rows rescued by live-current dynamic management.",
    },
]

CURRENT_FRAMEWORK_BRANCHES = [
    ("ob_retest", "origin_current_ob_retest"),
    ("fvg_fill", "origin_current_fvg_fill"),
    ("breaker_re_entry", "origin_current_breaker_re_entry"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def parse_time(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_stage04_rows() -> Iterable[dict[str, Any]]:
    with STAGE04_INDEX.open("r", encoding="utf-8") as index_handle:
        for index_line in index_handle:
            if not index_line.strip():
                continue
            index_row = json.loads(index_line)
            with (REPO_ROOT / index_row["output_chunk_path"]).open("r", encoding="utf-8") as shard:
                for row_line in shard:
                    if row_line.strip():
                        yield json.loads(row_line)


def risk_pct_for_symbol(symbol: Any) -> float:
    text = str(symbol or "").upper()
    if text in {"XAUUSD", "XAGUSD"}:
        return 1.0
    if text == "NAS100":
        return 0.25
    return 2.0


def is_in_kill_zone(feature: dict[str, Any]) -> bool:
    text = str(feature.get("kill_zone_position") or "")
    return text.startswith("in_")


def is_off_kill_zone(feature: dict[str, Any]) -> bool:
    return not is_in_kill_zone(feature)


def source_computed(feature: dict[str, Any]) -> bool:
    return feature.get("source_path_feature_status") == "computed_from_source_ohlc_asof"


def source_complete(feature: dict[str, Any]) -> bool:
    return bool(feature.get("source_window_complete"))


def no_high_news(feature: dict[str, Any]) -> bool:
    return feature.get("news_high_impact_within_120m") is not True


def feature_complete(feature: dict[str, Any]) -> bool:
    return (
        source_computed(feature)
        and feature.get("trend_state_20") != "insufficient_lookback"
        and feature.get("volatility_state_14_vs_50") != "insufficient_lookback"
    )


def side_aligned(feature: dict[str, Any]) -> bool:
    side = str(feature.get("side") or "").upper()
    trend = str(feature.get("trend_state_20") or "")
    if trend == "flat":
        return True
    if side == "LONG":
        return trend in {"up", "strong_up"}
    if side == "SHORT":
        return trend in {"down", "strong_down"}
    return False


def context_rich(feature: dict[str, Any]) -> bool:
    volatility = str(feature.get("volatility_state_14_vs_50") or "")
    trend = str(feature.get("trend_state_20") or "")
    displacement = safe_float(feature.get("current_bar_displacement_atr14"))
    return (
        feature.get("news_high_impact_within_120m") is True
        or volatility in {"high_recent_vs_baseline", "elevated_recent_vs_baseline"}
        or str(feature.get("compression_expansion_state") or "") == "expansion"
        or trend in {"strong_up", "strong_down"}
        or (displacement is not None and displacement >= 1.5)
        or is_off_kill_zone(feature)
        or not source_complete(feature)
    )


def mechanical_no_paid(feature: dict[str, Any]) -> bool:
    volatility = str(feature.get("volatility_state_14_vs_50") or "")
    trend = str(feature.get("trend_state_20") or "")
    displacement = safe_float(feature.get("current_bar_displacement_atr14"))
    return (
        is_in_kill_zone(feature)
        and feature_complete(feature)
        and no_high_news(feature)
        and volatility in {"normal_recent_vs_baseline", "low_recent_vs_baseline", "very_low_recent_vs_baseline"}
        and trend in {"flat", "up", "down"}
        and (displacement is None or displacement < 1.5)
    )


def branch_memberships(feature: dict[str, Any]) -> dict[str, bool]:
    memberships = {
        "raw_repaired_all_replayable": True,
        "source_complete_only": source_complete(feature),
        "missing_source_excluded_asof_computed": source_computed(feature),
        "high_quality_source_complete_kz": (
            source_complete(feature) and is_in_kill_zone(feature) and feature_complete(feature) and no_high_news(feature)
        ),
        "high_quality_asof_kz": is_in_kill_zone(feature) and feature_complete(feature) and no_high_news(feature),
        "aggressive_research_asof_all_sessions": feature_complete(feature),
        "context_recovery_off_kz_side_aligned": (
            is_off_kill_zone(feature) and feature_complete(feature) and side_aligned(feature) and no_high_news(feature)
        ),
        "ml_candidate_feature_complete": feature_complete(feature),
        "ai_required_context_rich": feature_complete(feature) and context_rich(feature),
        "no_paid_mechanical_diagnostic": mechanical_no_paid(feature),
        "prop_ev_optimized_side_aligned_kz": (
            is_in_kill_zone(feature) and feature_complete(feature) and side_aligned(feature) and no_high_news(feature)
        ),
        "monitoring_only_ambiguous_path": bool(feature.get("same_bar_ambiguity")),
        "dynamic_repair_needed_legacy_winner_to_live_nonpositive": (
            feature.get("policy_reversal_bucket") == "dynamic_nonpositive_from_legacy_winner"
        ),
        "dynamic_recovery_legacy_nonpositive_to_live_winner": (
            feature.get("policy_reversal_bucket") == "dynamic_winner_from_legacy_nonpositive"
        ),
    }
    for framework, branch_id in CURRENT_FRAMEWORK_BRANCHES:
        memberships[branch_id] = feature.get("framework") == framework
    return memberships


def branch_catalog() -> list[dict[str, Any]]:
    rows = [dict(row) for row in BASE_BRANCHES]
    for framework, branch_id in CURRENT_FRAMEWORK_BRANCHES:
        rows.append(
            {
                "branch_id": branch_id,
                "branch_family": "current_candidate_origin",
                "selection_class": "decision_safe_asof",
                "prop_replay_eligible": True,
                "description": f"Current GTOS framework branch for {framework}.",
            }
        )
    return rows


@dataclass
class BranchPolicyStats:
    branch_id: str
    policy_name: str
    row_count: int = 0
    wins: int = 0
    losses: int = 0
    zeros: int = 0
    total_r: float = 0.0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0
    exit_reason_counts: Counter[str] = field(default_factory=Counter)
    transition_counts: Counter[str] = field(default_factory=Counter)
    dimension_counts: dict[str, Counter[str]] = field(
        default_factory=lambda: {dimension: Counter() for dimension in DIMENSIONS}
    )

    def update(self, event: dict[str, Any], result: dict[str, Any], legacy_r: float | None) -> None:
        self.row_count += 1
        r_value = safe_float(result.get("final_r"))
        if r_value is not None:
            self.total_r += r_value
            if r_value > 0:
                self.wins += 1
                self.gross_win_r += r_value
            elif r_value < 0:
                self.losses += 1
                self.gross_loss_r += abs(r_value)
            else:
                self.zeros += 1
        else:
            self.zeros += 1
        self.exit_reason_counts[str(result.get("exit_reason") or "unknown")] += 1
        if legacy_r is None or r_value is None:
            transition = "missing_legacy_or_policy_r"
        elif legacy_r > 0 and r_value <= 0:
            transition = "legacy_winner_to_policy_nonpositive"
        elif legacy_r <= 0 and r_value > 0:
            transition = "legacy_nonpositive_to_policy_winner"
        elif r_value > legacy_r:
            transition = "policy_better_same_sign_or_both_positive"
        elif r_value < legacy_r:
            transition = "policy_worse_same_sign_or_both_nonpositive"
        else:
            transition = "same_r"
        self.transition_counts[transition] += 1
        feature = event["feature"]
        for dimension in DIMENSIONS:
            self.dimension_counts[dimension][str(feature.get(dimension))] += 1

    def to_record(self, catalog_row: dict[str, Any]) -> dict[str, Any]:
        denominator = self.row_count
        expectancy = self.total_r / denominator if denominator else None
        win_rate = self.wins / denominator if denominator else None
        profit_factor = None if self.gross_loss_r == 0 else self.gross_win_r / self.gross_loss_r
        return {
            "schema_version": "vnext_moonshot_corrected_branch_metrics_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV",
            "branch_id": self.branch_id,
            "branch_family": catalog_row["branch_family"],
            "selection_class": catalog_row["selection_class"],
            "prop_replay_eligible": catalog_row["prop_replay_eligible"],
            "policy_name": self.policy_name,
            "row_count": denominator,
            "wins": self.wins,
            "losses": self.losses,
            "zeros": self.zeros,
            "total_r": round(self.total_r, 12),
            "expectancy_r": round(expectancy, 12) if expectancy is not None else None,
            "win_rate": round(win_rate, 12) if win_rate is not None else None,
            "profit_factor": round(profit_factor, 12) if profit_factor is not None else None,
            "gross_win_r": round(self.gross_win_r, 12),
            "gross_loss_r": round(self.gross_loss_r, 12),
            "exit_reason_counts": dict(sorted(self.exit_reason_counts.items())),
            "legacy_fixed_1_5r_transition_counts": dict(sorted(self.transition_counts.items())),
            "market_awareness_distribution_counts": {
                dimension: dict(sorted(counter.items()))
                for dimension, counter in sorted(self.dimension_counts.items())
            },
            "corrected_dynamic_label_source": "Stage04 policy_results.final_r",
            "fixed_1_5r_used_as_activation_truth": False,
            "description": catalog_row["description"],
        }


@dataclass
class AttemptState:
    phase: int = 1
    attempt_id: int = 1
    equity: float = INITIAL_BALANCE
    day_start_equity: float = INITIAL_BALANCE
    current_day_key: str | None = None
    attempt_start_utc: datetime | None = None
    phase_start_utc: datetime | None = None
    trades_in_attempt: int = 0
    phase1_passed: bool = False

    def reset_for_new_attempt(self, attempt_id: int, as_of: datetime) -> None:
        self.phase = 1
        self.attempt_id = attempt_id
        self.equity = INITIAL_BALANCE
        self.day_start_equity = INITIAL_BALANCE
        self.current_day_key = reset_day_key(as_of)
        self.attempt_start_utc = as_of
        self.phase_start_utc = as_of
        self.trades_in_attempt = 0
        self.phase1_passed = False

    def reset_for_phase2(self, as_of: datetime) -> None:
        self.phase = 2
        self.equity = INITIAL_BALANCE
        self.day_start_equity = INITIAL_BALANCE
        self.current_day_key = reset_day_key(as_of)
        self.phase_start_utc = as_of
        self.phase1_passed = True

    def roll_day(self, as_of: datetime) -> None:
        key = reset_day_key(as_of)
        if self.current_day_key != key:
            self.current_day_key = key
            self.day_start_equity = self.equity

    def daily_floor(self) -> float:
        return self.day_start_equity - INITIAL_BALANCE * redacted_account_DAILY_LOSS_LIMIT_PCT / 100.0

    def overall_floor(self) -> float:
        return INITIAL_BALANCE * (1.0 - redacted_account_OVERALL_MAX_LOSS_PCT / 100.0)

    def target_equity(self) -> float:
        return INITIAL_BALANCE * (1.0 + PHASE_TARGETS[self.phase] / 100.0)


@dataclass
class PropMetrics:
    branch_id: str
    policy_name: str
    prop_policy: str
    branch_expectancy_r: float | None
    input_rows: int = 0
    allowed_trades: int = 0
    blocked_trades: int = 0
    deferred_trades: int = 0
    reduced_risk_trades: int = 0
    micro_risk_trades: int = 0
    abandon_restarts: int = 0
    attempts_started: int = 0
    phase1_passes: int = 0
    phase2_passes: int = 0
    failed_attempts: int = 0
    abandoned_attempts: int = 0
    open_attempts: int = 0
    accepted_winners: int = 0
    accepted_losers: int = 0
    accepted_zero_or_null: int = 0
    missed_winners: int = 0
    avoided_losers: int = 0
    blocked_positive_r: float = 0.0
    blocked_negative_r: float = 0.0
    total_r: float = 0.0
    risk_adjusted_r: float = 0.0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0
    max_drawdown_pct: float = 0.0
    max_loss_streak: int = 0
    current_loss_streak: int = 0
    action_counts: Counter[str] = field(default_factory=Counter)
    terminal_status_counts: Counter[str] = field(default_factory=Counter)
    terminal_days: list[float] = field(default_factory=list)
    pass_days: list[float] = field(default_factory=list)
    fail_or_abandon_days: list[float] = field(default_factory=list)

    def observe_block(self, r_value: float | None, action: str) -> None:
        self.action_counts[action] += 1
        if action == "DEFER_UNTIL_RESET":
            self.deferred_trades += 1
        elif action == "ACCOUNT_ABANDON_OR_RESTART":
            self.abandon_restarts += 1
        else:
            self.blocked_trades += 1
        if r_value is None:
            return
        if r_value > 0:
            self.missed_winners += 1
            self.blocked_positive_r += r_value
        elif r_value < 0:
            self.avoided_losers += 1
            self.blocked_negative_r += abs(r_value)

    def observe_trade(
        self,
        *,
        r_value: float | None,
        base_risk_pct: float,
        risk_pct: float,
        before_equity: float,
        after_equity: float,
        equity_peak: float,
        action: str,
    ) -> None:
        self.action_counts[action] += 1
        self.allowed_trades += 1
        if action == "REDUCE_RISK":
            self.reduced_risk_trades += 1
        if action == "MICRO_RISK":
            self.micro_risk_trades += 1
        if r_value is None:
            self.accepted_zero_or_null += 1
            return
        self.total_r += r_value
        risk_denominator = base_risk_pct if base_risk_pct > 0 else risk_pct
        self.risk_adjusted_r += r_value * (risk_pct / risk_denominator if risk_denominator > 0 else 0.0)
        if r_value > 0:
            self.accepted_winners += 1
            self.gross_win_r += r_value
            self.current_loss_streak = 0
        elif r_value < 0:
            self.accepted_losers += 1
            self.gross_loss_r += abs(r_value)
            self.current_loss_streak += 1
            self.max_loss_streak = max(self.max_loss_streak, self.current_loss_streak)
        else:
            self.accepted_zero_or_null += 1
        drawdown = 0.0 if equity_peak <= 0 else max(0.0, (equity_peak - after_equity) / equity_peak * 100.0)
        self.max_drawdown_pct = max(self.max_drawdown_pct, drawdown)

    def observe_terminal(self, status: str, duration_days: float | None) -> None:
        self.terminal_status_counts[status] += 1
        if duration_days is None:
            return
        self.terminal_days.append(duration_days)
        if status == "phase2_passed_challenge_complete":
            self.pass_days.append(duration_days)
        if status in {"failed_prop_limit", "abandoned_for_restart"}:
            self.fail_or_abandon_days.append(duration_days)

    def to_record(self) -> dict[str, Any]:
        attempts = max(1, self.attempts_started)
        completed_attempts = self.phase2_passes + self.failed_attempts + self.abandoned_attempts
        account_loss_rate = (self.failed_attempts + self.abandoned_attempts) / attempts
        pass_rate = self.phase2_passes / attempts
        expectancy = self.total_r / self.allowed_trades if self.allowed_trades else None
        win_rate = self.accepted_winners / self.allowed_trades if self.allowed_trades else None
        profit_factor = None if self.gross_loss_r == 0 else self.gross_win_r / self.gross_loss_r
        reference_ev = pass_rate * REFERENCE_PAYOUT_PROXY_USD - account_loss_rate * REFERENCE_ACCOUNT_FEE_USD
        avg_terminal = average(self.terminal_days)
        avg_pass = average(self.pass_days)
        avg_fail = average(self.fail_or_abandon_days)
        ev_per_day = reference_ev / max(1.0, avg_terminal) if avg_terminal is not None else None
        return {
            "schema_version": "vnext_moonshot_prop_ev_attempt_stream_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV",
            "branch_id": self.branch_id,
            "policy_name": self.policy_name,
            "prop_policy": self.prop_policy,
            "segmented_account_attempts_modelled": True,
            "attempt_segmentation_level": "aggregate_over_all_segmented_attempts",
            "input_rows": self.input_rows,
            "attempts_started": self.attempts_started,
            "completed_attempts": completed_attempts,
            "open_attempts": self.open_attempts,
            "phase1_passes": self.phase1_passes,
            "phase2_passes": self.phase2_passes,
            "failed_attempts": self.failed_attempts,
            "abandoned_attempts": self.abandoned_attempts,
            "terminal_status_counts": dict(sorted(self.terminal_status_counts.items())),
            "account_loss_rate": round(account_loss_rate, 12),
            "pass_probability_proxy": round(pass_rate, 12),
            "allowed_trades": self.allowed_trades,
            "blocked_trades": self.blocked_trades,
            "deferred_trades": self.deferred_trades,
            "reduced_risk_trades": self.reduced_risk_trades,
            "micro_risk_trades": self.micro_risk_trades,
            "abandon_restarts": self.abandon_restarts,
            "action_counts": dict(sorted(self.action_counts.items())),
            "accepted_winners": self.accepted_winners,
            "accepted_losers": self.accepted_losers,
            "accepted_zero_or_null": self.accepted_zero_or_null,
            "missed_winners": self.missed_winners,
            "avoided_losers": self.avoided_losers,
            "blocked_positive_r": round(self.blocked_positive_r, 12),
            "blocked_negative_r": round(self.blocked_negative_r, 12),
            "trade_opportunity_cost_r": round(self.blocked_positive_r - self.blocked_negative_r, 12),
            "total_r": round(self.total_r, 12),
            "risk_adjusted_r": round(self.risk_adjusted_r, 12),
            "expectancy_r": round(expectancy, 12) if expectancy is not None else None,
            "branch_expectancy_r": (
                round(self.branch_expectancy_r, 12) if self.branch_expectancy_r is not None else None
            ),
            "win_rate": round(win_rate, 12) if win_rate is not None else None,
            "profit_factor": round(profit_factor, 12) if profit_factor is not None else None,
            "max_drawdown_pct": round(self.max_drawdown_pct, 12),
            "max_loss_streak": self.max_loss_streak,
            "avg_time_to_terminal_days": round(avg_terminal, 6) if avg_terminal is not None else None,
            "avg_time_to_pass_days": round(avg_pass, 6) if avg_pass is not None else None,
            "avg_time_to_fail_or_abandon_days": round(avg_fail, 6) if avg_fail is not None else None,
            "expected_payout_proxy_usd_fee599_payout8000": round(reference_ev, 6),
            "reference_ev_per_terminal_day_usd_fee599_payout8000": (
                round(ev_per_day, 6) if ev_per_day is not None else None
            ),
            "redacted_account_rules_modelled": {
                "initial_balance": INITIAL_BALANCE,
                "daily_loss_limit_pct_gmt_plus_3": redacted_account_DAILY_LOSS_LIMIT_PCT,
                "overall_max_loss_pct_static": redacted_account_OVERALL_MAX_LOSS_PCT,
                "phase1_target_pct": PHASE_TARGETS[1],
                "phase2_target_pct": PHASE_TARGETS[2],
            },
            "expected_value_formula": "pass_probability_proxy*payout_proxy_usd - account_loss_rate*account_fee_usd",
        }


def average(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def reset_day_key(as_of: datetime) -> str:
    return (as_of + timedelta(hours=3)).date().isoformat()


def remaining_cushions(state: AttemptState) -> dict[str, float]:
    return {
        "daily": state.equity - state.daily_floor(),
        "overall": state.equity - state.overall_floor(),
    }


def max_risk_pct_available(state: AttemptState) -> float:
    if state.equity <= 0:
        return 0.0
    cushions = remaining_cushions(state)
    max_amount = min(cushions["daily"], cushions["overall"])
    max_amount -= state.equity * SPREAD_BUFFER_PCT / 100.0
    return max(0.0, max_amount / state.equity * 100.0)


def choose_prop_action(
    *,
    prop_policy: str,
    event: dict[str, Any],
    state: AttemptState,
    branch_expectancy_r: float | None,
) -> dict[str, Any]:
    full_risk = event["base_risk_pct"]
    max_pct = max_risk_pct_available(state)
    cushions = remaining_cushions(state)
    daily_binding = cushions["daily"] <= cushions["overall"]
    high_quality = bool(event["branches"].get("high_quality_asof_kz"))

    def result(action: str, risk_pct: float, reason: str) -> dict[str, Any]:
        return {
            "action": action,
            "risk_pct": round(max(0.0, risk_pct), 12),
            "reason": reason,
            "max_available_risk_pct": round(max_pct, 12),
            "decision_inputs_no_future_row_r": True,
        }

    if prop_policy == "HIGH_QUALITY_ONLY" and not high_quality:
        return result("BLOCK", 0.0, "high_quality_only_asof_filter")
    if prop_policy == "BLOCK_ALL_NEAR_LIMIT" and max_pct < full_risk * 2:
        return result("BLOCK", 0.0, "block_all_near_limit_buffer")
    if prop_policy == "EV_OPTIMIZED_REDUCE_OR_DEFER" and (branch_expectancy_r is None or branch_expectancy_r <= 0):
        return result("BLOCK", 0.0, "branch_expectancy_nonpositive_ev_block")
    if max_pct >= full_risk:
        return result("ALLOW", full_risk, "budget_allows_symbol_full_risk")
    if prop_policy in {"ALLOW_FULL_RISK_SEGMENTED", "BLOCK_ALL_NEAR_LIMIT"}:
        return result("BLOCK", 0.0, "budget_does_not_allow_full_symbol_risk")
    if prop_policy == "DEFER_UNTIL_RESET":
        if daily_binding and cushions["overall"] >= state.equity * MIN_REDUCED_RISK_PCT / 100.0:
            return result("DEFER_UNTIL_RESET", 0.0, "daily_binding_defer_until_gmt3_reset")
        return result("BLOCK", 0.0, "overall_or_min_budget_block")
    if prop_policy in {"REDUCE_RISK_TO_BUDGET", "EV_OPTIMIZED_REDUCE_OR_DEFER"}:
        if max_pct >= MIN_REDUCED_RISK_PCT:
            return result("REDUCE_RISK", min(full_risk, max_pct), "reduce_to_available_budget")
        if daily_binding:
            return result("DEFER_UNTIL_RESET", 0.0, "below_min_risk_daily_binding_defer")
        return result("BLOCK", 0.0, "below_min_risk_overall_block")
    if prop_policy == "MICRO_RISK_NEAR_BUDGET":
        if max_pct >= MICRO_RISK_PCT:
            return result("MICRO_RISK", min(MICRO_RISK_PCT, full_risk), "micro_risk_fits_budget")
        if daily_binding:
            return result("DEFER_UNTIL_RESET", 0.0, "micro_risk_daily_binding_defer")
        return result("BLOCK", 0.0, "micro_risk_not_fit_overall_block")
    if prop_policy == "ACCOUNT_ABANDON_OR_RESTART":
        if max_pct >= MIN_REDUCED_RISK_PCT:
            return result("REDUCE_RISK", min(full_risk, max_pct), "restart_policy_reduce_to_budget")
        if daily_binding and cushions["overall"] >= state.equity * MIN_REDUCED_RISK_PCT / 100.0:
            return result("DEFER_UNTIL_RESET", 0.0, "restart_policy_daily_defer")
        return result("ACCOUNT_ABANDON_OR_RESTART", 0.0, "overall_budget_exhausted_restart_attempt")
    return result("BLOCK", 0.0, "unknown_prop_policy_block")


def duration_days(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None:
        return None
    return max(0.0, (end - start).total_seconds() / 86400.0)


def run_prop_stream(
    *,
    branch_id: str,
    policy_name: str,
    prop_policy: str,
    branch_expectancy_r: float | None,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics = PropMetrics(
        branch_id=branch_id,
        policy_name=policy_name,
        prop_policy=prop_policy,
        branch_expectancy_r=branch_expectancy_r,
    )
    state = AttemptState()
    attempt_id = 1
    equity_peak = INITIAL_BALANCE
    attempt_has_trade = False

    for event in events:
        if not event["branches"].get(branch_id):
            continue
        metrics.input_rows += 1
        as_of = event["time"]
        if state.attempt_start_utc is None:
            state.reset_for_new_attempt(attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, attempt_id)
            equity_peak = state.equity
        state.roll_day(as_of)
        action = choose_prop_action(
            prop_policy=prop_policy,
            event=event,
            state=state,
            branch_expectancy_r=branch_expectancy_r,
        )
        if action["action"] == "ACCOUNT_ABANDON_OR_RESTART":
            metrics.abandoned_attempts += 1
            metrics.observe_block(event["policy_r"][policy_name], action["action"])
            metrics.observe_terminal(
                "abandoned_for_restart",
                duration_days(state.attempt_start_utc, as_of),
            )
            attempt_id += 1
            state.reset_for_new_attempt(attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, attempt_id)
            equity_peak = state.equity
            attempt_has_trade = False
            action = choose_prop_action(
                prop_policy=prop_policy,
                event=event,
                state=state,
                branch_expectancy_r=branch_expectancy_r,
            )

        r_value = event["policy_r"][policy_name]
        selected = action["action"] in {"ALLOW", "REDUCE_RISK", "MICRO_RISK"}
        if not selected:
            metrics.observe_block(r_value, action["action"])
            continue

        before_equity = state.equity
        after_equity = before_equity
        if r_value is not None:
            after_equity = before_equity + before_equity * action["risk_pct"] / 100.0 * r_value
            state.equity = after_equity
            equity_peak = max(equity_peak, state.equity)
        state.trades_in_attempt += 1
        attempt_has_trade = True
        metrics.observe_trade(
            r_value=r_value,
            base_risk_pct=event["base_risk_pct"],
            risk_pct=action["risk_pct"],
            before_equity=before_equity,
            after_equity=after_equity,
            equity_peak=equity_peak,
            action=action["action"],
        )
        if state.equity <= state.daily_floor() or state.equity <= state.overall_floor():
            metrics.failed_attempts += 1
            metrics.observe_terminal("failed_prop_limit", duration_days(state.attempt_start_utc, as_of))
            attempt_id += 1
            state.reset_for_new_attempt(attempt_id, as_of)
            metrics.attempts_started = max(metrics.attempts_started, attempt_id)
            equity_peak = state.equity
            attempt_has_trade = False
        elif state.equity >= state.target_equity():
            if state.phase == 1:
                metrics.phase1_passes += 1
                state.reset_for_phase2(as_of)
                equity_peak = state.equity
            else:
                metrics.phase2_passes += 1
                metrics.observe_terminal(
                    "phase2_passed_challenge_complete",
                    duration_days(state.attempt_start_utc, as_of),
                )
                attempt_id += 1
                state.reset_for_new_attempt(attempt_id, as_of)
                metrics.attempts_started = max(metrics.attempts_started, attempt_id)
                equity_peak = state.equity
                attempt_has_trade = False

    if attempt_has_trade:
        metrics.open_attempts += 1
        last_time = max((event["time"] for event in events if event["branches"].get(branch_id)), default=None)
        metrics.observe_terminal("open_at_replay_end", duration_days(state.attempt_start_utc, last_time))
    return metrics.to_record()


def load_events_and_branch_metrics() -> tuple[list[dict[str, Any]], dict[tuple[str, str], BranchPolicyStats]]:
    catalog_by_id = {row["branch_id"]: row for row in branch_catalog()}
    stats: dict[tuple[str, str], BranchPolicyStats] = {}
    events: list[dict[str, Any]] = []
    features_iter = iter_jsonl(STAGE06_FEATURES)
    for seq, (stage04_row, feature) in enumerate(zip(iter_stage04_rows(), features_iter), start=1):
        if stage04_row.get("candidate_id") != feature.get("candidate_id"):
            raise ValueError(f"Stage04/Stage06 row mismatch at {seq}")
        time = parse_time(stage04_row.get("candle_time_utc"))
        if time is None:
            continue
        memberships = branch_memberships(feature)
        policy_r = {
            name: safe_float(stage04_row["policy_results"][name].get("final_r"))
            for name in POLICY_NAMES
        }
        event = {
            "candidate_id": stage04_row.get("candidate_id"),
            "time": time,
            "base_risk_pct": risk_pct_for_symbol(stage04_row.get("symbol")),
            "feature": feature,
            "branches": memberships,
            "policy_r": policy_r,
        }
        events.append(event)
        legacy_r = policy_r["legacy_fixed_1.5r"]
        for branch_id, selected in memberships.items():
            if not selected:
                continue
            catalog = catalog_by_id[branch_id]
            for policy_name in POLICY_NAMES:
                key = (branch_id, policy_name)
                if key not in stats:
                    stats[key] = BranchPolicyStats(branch_id=branch_id, policy_name=policy_name)
                stats[key].update(event, stage04_row["policy_results"][policy_name], legacy_r)
    try:
        next(features_iter)
        raise ValueError("Stage06 feature ledger has extra rows after Stage04 rows ended")
    except StopIteration:
        pass
    events.sort(key=lambda item: item["time"])
    return events, stats


def registry_only_records(existing_branch_ids: set[str]) -> list[dict[str, Any]]:
    records = []
    for row in iter_jsonl(STAGE05_REGISTRY):
        name = row.get("name")
        current_branch_id = f"origin_current_{name}" if name in {"ob_retest", "fvg_fill", "breaker_re_entry"} else None
        if current_branch_id in existing_branch_ids:
            continue
        records.append(
            {
                "schema_version": "vnext_moonshot_corrected_branch_metrics_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV",
                "branch_id": f"origin_registry_only_{name}",
                "branch_family": row.get("category"),
                "selection_class": "candidate_origin_registry_only",
                "prop_replay_eligible": False,
                "policy_name": None,
                "row_count": 0,
                "wins": None,
                "losses": None,
                "zeros": None,
                "total_r": None,
                "expectancy_r": None,
                "win_rate": None,
                "profit_factor": None,
                "gross_win_r": None,
                "gross_loss_r": None,
                "exit_reason_counts": {},
                "legacy_fixed_1_5r_transition_counts": {},
                "market_awareness_distribution_counts": {},
                "corrected_dynamic_label_source": "not_replayable_yet_registry_only",
                "fixed_1_5r_used_as_activation_truth": False,
                "source_availability_status": row.get("source_availability_status"),
                "next_replay_action": row.get("next_replay_action"),
                "description": "Stage05 candidate-origin family is registered but has no row-level generator/replay in Stage07 evidence class.",
            }
        )
    return records


def best_by_branch_policy(prop_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in prop_rows:
        grouped[(row["branch_id"], row["policy_name"])].append(row)
    best = {}
    for key, rows in grouped.items():
        best[key] = sorted(
            rows,
            key=lambda item: (
                item.get("reference_ev_per_terminal_day_usd_fee599_payout8000") or -10**12,
                item.get("expected_payout_proxy_usd_fee599_payout8000") or -10**12,
                item.get("risk_adjusted_r") or -10**12,
                item.get("pass_probability_proxy") or 0,
                -(item.get("account_loss_rate") or 1),
            ),
            reverse=True,
        )[0]
    return best


def safe_but_dead_rejections(prop_rows: list[dict[str, Any]], best_rows: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rejected = []
    for row in prop_rows:
        if row["prop_policy"] not in {"BLOCK_ALL_NEAR_LIMIT", "HIGH_QUALITY_ONLY"}:
            continue
        best = best_rows[(row["branch_id"], row["policy_name"])]
        if best["prop_policy"] == row["prop_policy"]:
            continue
        if row["input_rows"] == 0:
            continue
        allowed_ratio = row["allowed_trades"] / row["input_rows"]
        if allowed_ratio <= 0.05 and (
            row["trade_opportunity_cost_r"] > 0
            or row["expected_payout_proxy_usd_fee599_payout8000"]
            < best["expected_payout_proxy_usd_fee599_payout8000"]
        ):
            rejected.append(
                {
                    "branch_id": row["branch_id"],
                    "policy_name": row["policy_name"],
                    "safe_policy_rejected": row["prop_policy"],
                    "best_policy": best["prop_policy"],
                    "allowed_ratio": round(allowed_ratio, 12),
                    "trade_opportunity_cost_r": row["trade_opportunity_cost_r"],
                    "safe_policy_ev_usd": row["expected_payout_proxy_usd_fee599_payout8000"],
                    "best_policy_ev_usd": best["expected_payout_proxy_usd_fee599_payout8000"],
                    "reason": "safe_but_dead_selector_loses_to_opportunity_preserving_alternative",
                }
            )
    return rejected


def build() -> dict[str, Any]:
    stage04_summary = json.loads(STAGE04_SUMMARY.read_text(encoding="utf-8"))
    stage06_summary = json.loads(STAGE06_SUMMARY.read_text(encoding="utf-8"))
    catalog = branch_catalog()
    catalog_by_id = {row["branch_id"]: row for row in catalog}
    events, stats = load_events_and_branch_metrics()
    if len(events) != stage04_summary.get("replayable_candidate_rows"):
        raise ValueError(f"event count mismatch: {len(events)} != {stage04_summary.get('replayable_candidate_rows')}")
    if len(events) != stage06_summary.get("feature_rows"):
        raise ValueError(f"Stage06 feature count mismatch: {len(events)} != {stage06_summary.get('feature_rows')}")

    branch_records = []
    for (branch_id, policy_name), stat in sorted(stats.items()):
        branch_records.append(stat.to_record(catalog_by_id[branch_id]))
    branch_records.extend(registry_only_records(set(catalog_by_id)))
    with OUTPUT_BRANCH_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in branch_records:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    expectancy_by_branch_policy = {
        (row["branch_id"], row["policy_name"]): row.get("expectancy_r")
        for row in branch_records
        if row.get("policy_name") in POLICY_NAMES
    }
    prop_rows = []
    prop_eligible_branches = [
        row["branch_id"]
        for row in catalog
        if row["prop_replay_eligible"]
        and stats.get(
            (row["branch_id"], "live_current_j46_j49"),
            BranchPolicyStats(row["branch_id"], "live_current_j46_j49"),
        ).row_count
        > 0
    ]
    events_by_branch = {
        branch_id: [event for event in events if event["branches"].get(branch_id)]
        for branch_id in prop_eligible_branches
    }
    for branch_id in prop_eligible_branches:
        for policy_name in POLICY_NAMES:
            branch_expectancy = expectancy_by_branch_policy.get((branch_id, policy_name))
            for prop_policy in PROP_POLICIES:
                prop_rows.append(
                    run_prop_stream(
                        branch_id=branch_id,
                        policy_name=policy_name,
                        prop_policy=prop_policy,
                        branch_expectancy_r=branch_expectancy,
                        events=events_by_branch[branch_id],
                    )
                )
    with OUTPUT_PROP_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in prop_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    best_rows = best_by_branch_policy(prop_rows)
    safe_dead = safe_but_dead_rejections(prop_rows, best_rows)
    best_overall = sorted(
        best_rows.values(),
        key=lambda item: (
            item.get("reference_ev_per_terminal_day_usd_fee599_payout8000") or -10**12,
            item.get("expected_payout_proxy_usd_fee599_payout8000") or -10**12,
            item.get("risk_adjusted_r") or -10**12,
        ),
        reverse=True,
    )[0]
    branch_row_counts = {
        branch_id: stats.get((branch_id, "live_current_j46_j49"), BranchPolicyStats(branch_id, "live_current_j46_j49")).row_count
        for branch_id in catalog_by_id
    }
    summary = {
        "schema_version": "vnext_moonshot_corrected_branch_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV",
        "generated_at_utc": utc_now(),
        "current_git_head": git_head(),
        "branch_metrics_ledger_path": rel(OUTPUT_BRANCH_LEDGER),
        "prop_ev_attempt_ledger_path": rel(OUTPUT_PROP_LEDGER),
        "opportunity_cost_report_path": rel(OUTPUT_REPORT),
        "corrected_branch_metric_rows": len(branch_records),
        "prop_ev_attempt_rows": len(prop_rows),
        "events_replayed": len(events),
        "stage04_replayable_rows": stage04_summary.get("replayable_candidate_rows"),
        "stage06_feature_rows": stage06_summary.get("feature_rows"),
        "policies_compared": POLICY_NAMES,
        "prop_policies_compared": PROP_POLICIES,
        "prop_eligible_branches": prop_eligible_branches,
        "branch_row_counts_live_current": dict(sorted(branch_row_counts.items())),
        "best_overall_reference_fee599_payout8000": best_overall,
        "safe_but_dead_rejection_count": len(safe_dead),
        "safe_but_dead_rejections": safe_dead,
        "legacy_fixed_1_5r_rejected_as_activation_truth": True,
        "segmented_prop_attempts_not_continuous_account": True,
        "redacted_account_rules_modelled": {
            "initial_balance": INITIAL_BALANCE,
            "daily_loss_limit_pct_gmt_plus_3": redacted_account_DAILY_LOSS_LIMIT_PCT,
            "overall_max_loss_pct_static": redacted_account_OVERALL_MAX_LOSS_PCT,
            "phase1_target_pct": PHASE_TARGETS[1],
            "phase2_target_pct": PHASE_TARGETS[2],
            "risk_source": "config/profiles/redacted_account.yaml base/instrument risk schedule; XAU/XAG 1%, NAS100 0.25%, others 2%",
        },
        "forbidden_boundaries_crossed": False,
        "no_live_trading_or_broker_mutation": True,
        "no_paid_api_or_vendor_call": True,
        "first_incomplete_invariant_after_stage07": "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN",
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    update_state(summary)
    return summary


def write_report(summary: dict[str, Any]) -> None:
    best = summary["best_overall_reference_fee599_payout8000"]
    lines = [
        "# vNext Moonshot Stage07 Prop EV Opportunity Cost",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Corrected Substrate",
        "",
        f"- Dynamic replay events: `{summary['events_replayed']}`",
        f"- Corrected branch metric rows: `{summary['corrected_branch_metric_rows']}`",
        f"- Prop EV attempt-stream rows: `{summary['prop_ev_attempt_rows']}`",
        "- Fixed 1.5R labels are retained only as comparators; activation truth uses corrected dynamic policy labels.",
        "",
        "## Best Reference Stream",
        "",
        f"- Branch: `{best['branch_id']}`",
        f"- Dynamic policy: `{best['policy_name']}`",
        f"- Prop policy: `{best['prop_policy']}`",
        f"- Pass probability proxy: `{best['pass_probability_proxy']}`",
        f"- Account loss rate: `{best['account_loss_rate']}`",
        f"- Expected payout proxy, fee 599 payout 8000: `{best['expected_payout_proxy_usd_fee599_payout8000']}`",
        f"- EV per terminal day: `{best['reference_ev_per_terminal_day_usd_fee599_payout8000']}`",
        "",
        "## Opportunity Cost",
        "",
        f"- Safe-but-dead selector rejections: `{summary['safe_but_dead_rejection_count']}`",
        "- Rejections are emitted when a near-blocking safety selector allows almost no trades and loses to an opportunity-preserving alternative on EV or missed-winner opportunity cost.",
        "- redacted_account attempts are segmented by challenge attempt and phase, with GMT+3 daily reset and static 10% max-loss rules.",
        "",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def update_state(summary: dict[str, Any]) -> None:
    if not STATE_PATH.exists():
        return
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = git_head()
    state["current_stage"] = "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV"
    state["first_incomplete_invariant"] = "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN"
    state["exact_next_action"] = "Run Stage08 AI role and budget design from corrected branch metrics and prop EV streams."
    state["completion_gate_status"] = "not_complete_first_incomplete_stage08"
    state["stage_status_table"]["STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV"] = "complete"
    state["stage_status_table"]["STAGE_08_AI_ROLE_AND_BUDGET_DESIGN"] = "pending"
    state["row_counts_scanned"]["stage07_corrected_branch_metric_rows"] = summary["corrected_branch_metric_rows"]
    state["row_counts_scanned"]["stage07_prop_ev_attempt_rows"] = summary["prop_ev_attempt_rows"]
    state["output_artifact_manifest"]["corrected_branch_metrics_ledger"] = rel(OUTPUT_BRANCH_LEDGER)
    state["output_artifact_manifest"]["prop_ev_attempt_ledger"] = rel(OUTPUT_PROP_LEDGER)
    state["output_artifact_manifest"]["prop_ev_opportunity_cost_report"] = rel(OUTPUT_REPORT)
    state["output_artifact_manifest"]["corrected_branch_summary"] = rel(OUTPUT_SUMMARY)
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage07_corrected_branch_metrics_prop_ev_2026_05_26.py"
            ),
            "status": "passed",
            "result": (
                f"branch_rows={summary['corrected_branch_metric_rows']}; "
                f"prop_rows={summary['prop_ev_attempt_rows']}; "
                "first_incomplete=STAGE_08_AI_ROLE_AND_BUDGET_DESIGN"
            ),
        }
    )
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    summary = build()
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV",
                "branch_metric_rows": summary["corrected_branch_metric_rows"],
                "prop_ev_attempt_rows": summary["prop_ev_attempt_rows"],
                "first_incomplete_invariant": summary["first_incomplete_invariant_after_stage07"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
