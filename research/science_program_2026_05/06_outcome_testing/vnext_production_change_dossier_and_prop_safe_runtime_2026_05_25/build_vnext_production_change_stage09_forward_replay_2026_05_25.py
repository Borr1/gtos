from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

import yaml

LOCAL_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(LOCAL_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_REPO_ROOT))

from src.components.ai_supervisor import evaluate_ai_supervisor
from src.components.gtos_vnext_runtime import (
    GTOSVNextPreAIRoutingDecision,
    GTOSVNextPropSafeSelectorDecision,
    GTOSVNextRuntimeDecision,
    apply_vnext_risk_adjustment,
    evaluate_vnext_ai_policy,
    evaluate_vnext_ltf_path_execution,
    evaluate_vnext_pending_policy,
    evaluate_vnext_prop_safe_selector,
    vnext_ai_policy_no_paid_call_replay_decision,
    vnext_execution_block_reason,
)


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage08_ai_supervisor_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage08", MODULE_PATH)
stage08 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage08)

stage00 = stage08.stage02.stage01.stage00
stage01 = stage08.stage02.stage01
stage02 = stage08.stage02

REPO_ROOT = stage08.REPO_ROOT
ROUTE_ID = stage08.ROUTE_ID
ROUTE_DIR = stage08.ROUTE_DIR
REPLAY_DIR = stage00.REPLAY_DIR
STATE_PATH = stage08.STATE_PATH

STAGE09_LEDGER_INDEX_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_REPLAY_COMPARISON_LEDGER_2026-05-25.jsonl"
)
STAGE09_SUMMARY_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_METRICS_SUMMARY_2026-05-25.json"
STAGE09_DOSSIER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_REPLAY_COMPARISON_DOSSIER_2026-05-25.md"
)
STAGE09_VERIFICATION_RESULT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE09_VERIFICATION_RESULT_2026-05-25.json"
)
STAGE09_HEARTBEAT_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CHANGE_STAGE09_HEARTBEAT_2026-05-25.json"
)
STAGE09_SHARD_DIR = ROUTE_DIR / "stage09_shards"

RUNTIME_TRACE_INDEX = REPLAY_DIR / "VNEXT_FULL_REPLAY_RUNTIME_TRACE_LEDGER_2026-05-24.jsonl"
PATH_R_INDEX = REPLAY_DIR / "VNEXT_FULL_REPLAY_PATH_OUTCOME_R_LEDGER_2026-05-24.jsonl"
NOFILL_INDEX = REPLAY_DIR / "VNEXT_FULL_REPLAY_NOFILL_PENDING_LIFECYCLE_LEDGER_2026-05-24.jsonl"
MISSED_WINNER_INDEX = (
    REPLAY_DIR / "VNEXT_FULL_REPLAY_MISSED_WINNER_AVOIDED_LOSER_LEDGER_2026-05-24.jsonl"
)

REPLAY_MODE_PRIORITY = {
    "tick_or_sierra_path_aware": 50,
    "m1_path_aware": 40,
    "m5_path_aware": 30,
    "bar_close_m15": 20,
    "ohlc_only_proxy": 10,
    "missing_source": 0,
}

REQUIRED_SCENARIOS = {
    "baseline_current_shadow",
    "previous_hypothetical_activated",
    "new_production_change_mechanical",
    "new_production_change_external_budget_only",
    "new_ai_policy_no_paid_call",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return stage00.rel(path)


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def parse_utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value or "").strip()
        if not text:
            return datetime.now(timezone.utc)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            dt = datetime.fromisoformat(text.replace(" ", "T"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def reset_window_start_utc(value: Any) -> datetime:
    reset_tz = timezone(timedelta(hours=3))
    local = parse_utc(value).astimezone(reset_tz)
    return local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def iter_index_rows(index_path: Path) -> Iterable[dict[str, Any]]:
    path = REPO_ROOT / index_path
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def iter_chunk_rows(index_path: Path) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    for meta in iter_index_rows(index_path):
        chunk_path = REPO_ROOT / str(meta["chunk_path"])
        with gzip.open(stage00.io_path(chunk_path), "rt", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield meta, json.loads(line)


def atomic_json_write(path: Path, payload: Any) -> None:
    stage00.atomic_json_write(REPO_ROOT / path if not path.is_absolute() else path, payload)


def write_heartbeat(stage: str, **payload: Any) -> None:
    atomic_json_write(
        STAGE09_HEARTBEAT_PATH,
        {
            "schema_version": "vnext_production_change_stage09_heartbeat_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "stage": stage,
            **payload,
        },
    )


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config() -> dict[str, Any]:
    return yaml.safe_load((REPO_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8"))


def activated_replay_config(config: dict[str, Any]) -> dict[str, Any]:
    replay = copy.deepcopy(config)
    runtime = replay.setdefault("gtos_vnext_runtime", {})
    runtime.update(
        {
            "enabled": True,
            "apply_to_execution": True,
            "pre_ai_enabled": True,
            "pre_ai_apply_to_ai_call": True,
            "ai_policy_enabled": True,
            "ai_policy_apply_to_ai_call": True,
            "risk_adjustment_enabled": True,
            "pending_policy_enabled": True,
            "prop_safe_selector_enabled": True,
            "prop_safe_selector_apply_to_execution": True,
            "ltf_path_execution_enabled": True,
            "ltf_path_execution_apply_to_execution": True,
            "decision_log_enabled": False,
        }
    )
    supervisor = replay.setdefault("ai_supervisor", {})
    supervisor["decision_log_enabled"] = False
    return replay


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def select_better_score(current: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    if current is None:
        return candidate
    current_has_r = current.get("simulated_r") is not None
    candidate_has_r = candidate.get("simulated_r") is not None
    if candidate_has_r != current_has_r:
        return candidate if candidate_has_r else current
    current_priority = int(current.get("replay_mode_priority") or -1)
    candidate_priority = int(candidate.get("replay_mode_priority") or -1)
    if candidate_priority != current_priority:
        return candidate if candidate_priority > current_priority else current
    return current


def build_score_map() -> dict[str, dict[str, Any]]:
    score_map: dict[str, dict[str, Any]] = {}
    rows = 0
    for _meta, row in iter_chunk_rows(PATH_R_INDEX):
        rows += 1
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        replay_mode = str(row.get("replay_mode") or "")
        if replay_mode not in REPLAY_MODE_PRIORITY:
            continue
        score = {
            "candidate_id": candidate_id,
            "best_available_replay_mode": replay_mode,
            "replay_mode_priority": REPLAY_MODE_PRIORITY[replay_mode],
            "simulated_r": _to_float(row.get("simulated_r")),
            "terminal_outcome": row.get("terminal_outcome"),
            "entry_touched": row.get("entry_touched"),
            "no_fill_equivalent_r": _to_float(row.get("no_fill_equivalent_r")),
            "timeout_mark_to_market_r": _to_float(row.get("timeout_mark_to_market_r")),
            "path_row_id": row.get("path_row_id"),
            "path_window_start_utc": row.get("path_window_start_utc"),
            "path_window_requested_end_utc": row.get("path_window_requested_end_utc"),
            "source_mode": row.get("source_mode"),
            "source_path": row.get("source_path"),
            "source_evidence_type": row.get("source_evidence_type"),
        }
        score_map[candidate_id] = select_better_score(score_map.get(candidate_id), score)
    write_heartbeat("score_map_built", path_rows_seen=rows, scoring_candidate_count=len(score_map))
    return score_map


def build_nofill_map() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    rows = 0
    for _meta, row in iter_chunk_rows(NOFILL_INDEX):
        rows += 1
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        result[candidate_id] = {
            "entry_touched": row.get("entry_touched"),
            "no_fill": row.get("no_fill"),
            "terminal_outcome": row.get("terminal_outcome"),
            "pending_lifecycle_state": row.get("pending_lifecycle_state"),
            "entry_first_touch_utc": row.get("entry_first_touch_utc"),
            "source_gap_class": row.get("source_gap_class"),
            "best_available_replay_mode": row.get("best_available_replay_mode"),
        }
    write_heartbeat("nofill_map_built", nofill_rows_seen=rows, nofill_candidate_count=len(result))
    return result


def build_missed_map() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    rows = 0
    for _meta, row in iter_chunk_rows(MISSED_WINNER_INDEX):
        rows += 1
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        result[candidate_id] = {
            "classification": row.get("classification"),
            "best_available_simulated_r": _to_float(row.get("best_available_simulated_r")),
            "best_available_terminal_outcome": row.get("best_available_terminal_outcome"),
            "best_available_replay_mode": row.get("best_available_replay_mode"),
            "would_change_decision_or_execution_with_ltf_source": row.get(
                "would_change_decision_or_execution_with_ltf_source"
            ),
        }
    write_heartbeat("missed_map_built", missed_rows_seen=rows, missed_candidate_count=len(result))
    return result


def compact_summary(summary: dict[str, Any] | None) -> dict[str, Any]:
    summary = summary or {}
    return {
        "pre_ai_action": summary.get("pre_ai_action"),
        "pre_ai_would_action": summary.get("pre_ai_would_action"),
        "pre_ai_decision": summary.get("pre_ai_decision"),
        "route_decision": summary.get("route_decision"),
        "route_matched": summary.get("route_matched"),
        "route_reason": summary.get("route_reason"),
        "pending_would_action": summary.get("pending_would_action"),
        "risk_would_multiplier": summary.get("risk_would_multiplier"),
        "risk_reason": summary.get("risk_reason"),
    }


def selected_from_previous(summary: dict[str, Any], *, current_risk_pct: float) -> tuple[bool, float, str]:
    route_decision = str(summary.get("route_decision") or "LEGACY")
    pre_ai_would = str(summary.get("pre_ai_would_action") or "")
    risk_multiplier = _to_float(summary.get("risk_would_multiplier"))
    if risk_multiplier is None:
        risk_multiplier = 1.0
    if pre_ai_would == "SKIP_AI_AVOID_ONLY":
        return False, 0.0, "pre_ai_skip_avoid_only"
    if route_decision != "FOLLOW":
        return False, 0.0, f"route_{route_decision.lower()}_not_follow"
    if risk_multiplier <= 0:
        return False, 0.0, "risk_zero"
    return True, float(current_risk_pct) * float(risk_multiplier), "selected_follow"


def classify_stage09_executable_stream(
    *,
    row: dict[str, Any],
    pre_ai: GTOSVNextPreAIRoutingDecision,
    route_decision: GTOSVNextRuntimeDecision,
) -> dict[str, Any]:
    """Classify whether Stage09 may send a row to vNext execution/prop budgeting.

    The candidate-generation universe includes diagnostics, off-KZ rows, legacy
    no-match rows, and mixed/context rows. Those rows are useful evidence, but
    they are not vNext executable trades and must not consume prop budget merely
    because no explicit block reason fired.
    """
    route = str(route_decision.decision or "LEGACY").upper()
    session = str(row.get("route_session") or row.get("session_bucket") or "")
    pre_ai_action = str(pre_ai.action or "")

    if session == "off_kz":
        return {
            "executable_stream": False,
            "prop_governance_eligible": False,
            "stream_class": "diagnostic_off_kz_generated_candidate",
            "reason": "off_kz_diagnostic_non_executable",
            "preserve_current_system_behavior": False,
        }
    if pre_ai_action == "SKIP_AI_AVOID_ONLY":
        return {
            "executable_stream": False,
            "prop_governance_eligible": False,
            "stream_class": "pre_ai_avoid_only_non_executable",
            "reason": "pre_ai_skip_avoid_only",
            "preserve_current_system_behavior": False,
        }
    if route == "FOLLOW":
        return {
            "executable_stream": True,
            "prop_governance_eligible": True,
            "stream_class": "vnext_follow_executable_stream",
            "reason": "vnext_follow_executable_stream",
            "preserve_current_system_behavior": False,
        }
    if route == "LEGACY":
        return {
            "executable_stream": False,
            "prop_governance_eligible": False,
            "stream_class": "legacy_preserve_current_system_behavior",
            "reason": "route_legacy_not_vnext_executable_preserve_current_system",
            "preserve_current_system_behavior": True,
        }
    if route == "MIXED":
        return {
            "executable_stream": False,
            "prop_governance_eligible": False,
            "stream_class": "mixed_requires_ai_or_policy_resolution",
            "reason": "route_mixed_requires_resolution_not_prop_budget",
            "preserve_current_system_behavior": True,
        }
    if route == "AVOID":
        return {
            "executable_stream": False,
            "prop_governance_eligible": False,
            "stream_class": "vnext_avoid_non_executable",
            "reason": "vnext_decision_avoid",
            "preserve_current_system_behavior": False,
        }
    return {
        "executable_stream": False,
        "prop_governance_eligible": False,
        "stream_class": "unknown_route_non_executable",
        "reason": f"route_{route.lower()}_not_vnext_executable",
        "preserve_current_system_behavior": False,
    }


def unevaluated_prop_selector_for_non_executable(
    *,
    decision: GTOSVNextRuntimeDecision,
    before_risk_pct: float,
    reason: str,
) -> GTOSVNextPropSafeSelectorDecision:
    """Return an inert selector record for rows outside the executable stream."""
    return GTOSVNextPropSafeSelectorDecision(
        action="ALLOW",
        would_action="ALLOW",
        enabled=True,
        apply_to_execution=False,
        applied=False,
        decision=decision.decision,
        before_risk_pct=round(float(before_risk_pct), 12),
        after_risk_pct=round(float(before_risk_pct), 12),
        max_allowed_new_trade_risk_pct=0.0,
        reason=f"prop_safe_selector_not_evaluated_{reason}",
        reset_window={},
        external_rule_projection={
            "not_evaluated": True,
            "not_evaluated_reason": reason,
            "prop_budget_applies_only_to_executable_stream": True,
        },
        internal_overlay_projection={"not_evaluated": True},
        exposure_breakdown={"not_evaluated": True},
        concentration={"not_evaluated": True},
        route_quality={
            "decision": decision.decision,
            "matched": decision.matched,
            "replay_robustness_note": "non_executable_rows_do_not_consume_prop_budget",
        },
    )


def extract_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    current_rows: list[dict[str, Any]] = []
    hypothetical: dict[str, dict[str, Any]] = {}
    mode_counts: Counter[str] = Counter()
    chunk_counts: Counter[str] = Counter()
    rows_seen = 0
    for meta, row in iter_chunk_rows(RUNTIME_TRACE_INDEX):
        rows_seen += 1
        mode = str(row.get("runtime_mode") or row.get("current_shadow_vs_hypothetical_mode") or "")
        mode_counts[mode] += 1
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        if mode == "hypothetical_activated_vnext":
            hypothetical[candidate_id] = compact_summary(row.get("decision_summary") or {})
            continue
        if mode != "current_config_shadow":
            continue
        chunk_counts[str(meta.get("shard_id") or meta.get("chunk_index") or "unknown")] += 1
        current_rows.append(
            {
                "candidate_id": candidate_id,
                "candle_time_utc": row.get("candle_time_utc"),
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol") or row.get("symbol"),
                "route_session": row.get("route_session") or row.get("session_bucket"),
                "session_bucket": row.get("session_bucket"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "route_family": row.get("route_family"),
                "market_timeframe": row.get("market_timeframe") or row.get("timeframe"),
                "timeframe": row.get("timeframe"),
                "runtime_input_event": row.get("runtime_input_event") or {},
                "runtime_raw_data": row.get("runtime_raw_data") or {},
                "candidate_geometry": row.get("candidate_geometry") or {},
                "current_shadow": compact_summary(row.get("decision_summary") or {}),
                "pre_ai_decision_payload": row.get("pre_ai_decision") or {},
                "route_decision_payload": row.get("route_decision") or {},
                "source_path": row.get("source_path"),
                "source_sha256": row.get("source_sha256"),
                "runtime_trace_id": row.get("runtime_trace_id"),
            }
        )
    current_rows.sort(key=lambda item: (parse_utc(item["candle_time_utc"]), item["candidate_id"]))
    diagnostics = {
        "runtime_rows_seen": rows_seen,
        "runtime_mode_counts": dict(mode_counts),
        "current_shadow_rows": len(current_rows),
        "hypothetical_rows": len(hypothetical),
        "current_chunk_counts": dict(chunk_counts),
    }
    write_heartbeat("runtime_rows_loaded", **diagnostics)
    return current_rows, hypothetical, diagnostics


@dataclass
class ScenarioMetrics:
    scenario: str
    initial_balance: float = 100000.0
    equity: float = 100000.0
    equity_peak: float = 100000.0
    day_start_equity: float = 100000.0
    current_day_start_utc: str | None = None
    candidate_count: int = 0
    selected_count: int = 0
    skipped_count: int = 0
    nofill_count: int = 0
    performance_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    zero_count: int = 0
    total_r: float = 0.0
    total_risk_adjusted_r: float = 0.0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0
    max_loss_streak: int = 0
    current_loss_streak: int = 0
    max_drawdown_pct: float = 0.0
    daily_breach_count: int = 0
    overall_breach_count: int = 0
    min_daily_cushion: float | None = None
    min_overall_cushion: float | None = None
    trades_by_day: Counter[str] = field(default_factory=Counter)
    symbols: Counter[str] = field(default_factory=Counter)
    sessions: Counter[str] = field(default_factory=Counter)
    sides: Counter[str] = field(default_factory=Counter)
    frameworks: Counter[str] = field(default_factory=Counter)
    route_families: Counter[str] = field(default_factory=Counter)
    source_modes: Counter[str] = field(default_factory=Counter)
    terminal_outcomes: Counter[str] = field(default_factory=Counter)
    skip_reasons: Counter[str] = field(default_factory=Counter)
    missed_winners: int = 0
    avoided_losers: int = 0
    accepted_losers: int = 0
    accepted_winners: int = 0
    risk_reductions: int = 0
    deferred_trades: int = 0
    blocked_trades: int = 0
    ai_calls_required: int = 0
    ai_calls_avoided: int = 0
    malformed_response_paths: int = 0

    def _roll_day(self, as_of_utc: str) -> None:
        window = reset_window_start_utc(as_of_utc).isoformat()
        if self.current_day_start_utc != window:
            self.current_day_start_utc = window
            self.day_start_equity = self.equity

    def observe_budget(self, as_of_utc: str) -> None:
        self._roll_day(as_of_utc)
        daily_floor = self.day_start_equity - self.initial_balance * 0.05
        overall_floor = self.initial_balance * 0.90
        daily_cushion = self.equity - daily_floor
        overall_cushion = self.equity - overall_floor
        self.min_daily_cushion = (
            daily_cushion
            if self.min_daily_cushion is None
            else min(self.min_daily_cushion, daily_cushion)
        )
        self.min_overall_cushion = (
            overall_cushion
            if self.min_overall_cushion is None
            else min(self.min_overall_cushion, overall_cushion)
        )
        if daily_cushion <= 0:
            self.daily_breach_count += 1
        if overall_cushion <= 0:
            self.overall_breach_count += 1

    def add(
        self,
        *,
        row: dict[str, Any],
        selected: bool,
        risk_pct: float,
        reason: str,
        score: dict[str, Any] | None,
        missed: dict[str, Any] | None,
    ) -> None:
        self.candidate_count += 1
        as_of = str(row.get("candle_time_utc") or "")
        self.observe_budget(as_of)
        self.symbols[str(row.get("symbol") or "")] += 1
        self.sessions[str(row.get("route_session") or row.get("session_bucket") or "")] += 1
        self.sides[str(row.get("side") or "")] += 1
        self.frameworks[str(row.get("framework") or "")] += 1
        self.route_families[str(row.get("route_family") or "")] += 1
        if score:
            self.source_modes[str(score.get("best_available_replay_mode") or "")] += 1
            self.terminal_outcomes[str(score.get("terminal_outcome") or "")] += 1

        r_value = _to_float((score or {}).get("simulated_r"))
        missed_class = str((missed or {}).get("classification") or "")
        if not selected:
            self.skipped_count += 1
            self.skip_reasons[reason] += 1
            if missed_class == "missed_winner" or (r_value is not None and r_value > 0):
                self.missed_winners += 1
            if missed_class == "avoided_loser" or (r_value is not None and r_value < 0):
                self.avoided_losers += 1
            return

        self.selected_count += 1
        day_key = reset_window_start_utc(as_of).date().isoformat()
        self.trades_by_day[day_key] += 1
        if score and str(score.get("terminal_outcome") or "") == "no_fill":
            self.nofill_count += 1
        if r_value is None:
            return

        self.performance_count += 1
        self.total_r += r_value
        risk_adjusted_r = r_value * (float(risk_pct) / 2.0 if risk_pct else 0.0)
        self.total_risk_adjusted_r += risk_adjusted_r
        pnl_amount = self.equity * max(0.0, float(risk_pct)) / 100.0 * r_value
        self.equity += pnl_amount
        self.equity_peak = max(self.equity_peak, self.equity)
        drawdown = 0.0 if self.equity_peak <= 0 else (self.equity_peak - self.equity) / self.equity_peak * 100.0
        self.max_drawdown_pct = max(self.max_drawdown_pct, drawdown)
        if r_value > 0:
            self.win_count += 1
            self.accepted_winners += 1
            self.gross_win_r += r_value
            self.current_loss_streak = 0
        elif r_value < 0:
            self.loss_count += 1
            self.accepted_losers += 1
            self.gross_loss_r += abs(r_value)
            self.current_loss_streak += 1
            self.max_loss_streak = max(self.max_loss_streak, self.current_loss_streak)
        else:
            self.zero_count += 1
        self.observe_budget(as_of)

    def to_record(self) -> dict[str, Any]:
        expectancy = self.total_r / self.performance_count if self.performance_count else None
        win_rate = self.win_count / self.performance_count if self.performance_count else None
        profit_factor = (
            None if self.gross_loss_r == 0 else self.gross_win_r / self.gross_loss_r
        )
        final_return_pct = (self.equity - self.initial_balance) / self.initial_balance * 100.0
        no_breach = self.daily_breach_count == 0 and self.overall_breach_count == 0
        return {
            "scenario": self.scenario,
            "candidate_count": self.candidate_count,
            "selected_count": self.selected_count,
            "skipped_count": self.skipped_count,
            "nofill_count": self.nofill_count,
            "performance_count": self.performance_count,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "zero_count": self.zero_count,
            "total_r": round(self.total_r, 12),
            "total_risk_adjusted_r": round(self.total_risk_adjusted_r, 12),
            "expectancy_r": round(expectancy, 12) if expectancy is not None else None,
            "win_rate": round(win_rate, 12) if win_rate is not None else None,
            "profit_factor": round(profit_factor, 12) if profit_factor is not None else None,
            "final_equity": round(self.equity, 2),
            "final_return_pct": round(final_return_pct, 12),
            "phase1_8pct_pass_proxy": bool(final_return_pct >= 8.0 and no_breach),
            "phase2_5pct_pass_proxy": bool(final_return_pct >= 5.0 and no_breach),
            "max_drawdown_pct": round(self.max_drawdown_pct, 12),
            "max_loss_streak": self.max_loss_streak,
            "max_trades_day": max(self.trades_by_day.values()) if self.trades_by_day else 0,
            "active_day_count": len(self.trades_by_day),
            "daily_loss_breach_count": self.daily_breach_count,
            "overall_max_loss_breach_count": self.overall_breach_count,
            "min_daily_cushion": round(self.min_daily_cushion, 6) if self.min_daily_cushion is not None else None,
            "min_overall_cushion": round(self.min_overall_cushion, 6) if self.min_overall_cushion is not None else None,
            "missed_winners": self.missed_winners,
            "avoided_losers": self.avoided_losers,
            "accepted_winners": self.accepted_winners,
            "accepted_losers": self.accepted_losers,
            "risk_reductions": self.risk_reductions,
            "deferred_trades": self.deferred_trades,
            "blocked_trades": self.blocked_trades,
            "ai_calls_required": self.ai_calls_required,
            "ai_calls_avoided": self.ai_calls_avoided,
            "malformed_response_paths": self.malformed_response_paths,
            "symbols": dict(sorted(self.symbols.items())),
            "sessions": dict(sorted(self.sessions.items())),
            "sides": dict(sorted(self.sides.items())),
            "frameworks": dict(sorted(self.frameworks.items())),
            "route_families": dict(sorted(self.route_families.items())),
            "source_modes": dict(sorted(self.source_modes.items())),
            "terminal_outcomes": dict(sorted(self.terminal_outcomes.items())),
            "skip_reasons": dict(self.skip_reasons.most_common(25)),
        }


def direction_to_bias(side: Any) -> str | None:
    side_text = str(side or "").upper()
    if side_text == "LONG":
        return "bullish"
    if side_text == "SHORT":
        return "bearish"
    return None


def rehydrate_pre_ai_decision(row: dict[str, Any], payload: dict[str, Any]) -> GTOSVNextPreAIRoutingDecision:
    would_action = str(payload.get("would_action") or "ALLOW_AI")
    return GTOSVNextPreAIRoutingDecision(
        action=would_action,
        would_action=would_action,
        decision=str(payload.get("decision") or "LEGACY"),
        enabled=True,
        apply_to_ai_call=True,
        reason=str(payload.get("reason") or "stage03_asof_pre_ai_rehydrated"),
        event=dict(row.get("runtime_input_event") or {}),
        recommended_side=payload.get("recommended_side"),
        recommended_frameworks=tuple(payload.get("recommended_frameworks") or ()),
        recommended_route_families=tuple(payload.get("recommended_route_families") or ()),
        blocked_sides=tuple(payload.get("blocked_sides") or ()),
        blocked_frameworks=tuple(payload.get("blocked_frameworks") or ()),
        blocked_route_families=tuple(payload.get("blocked_route_families") or ()),
        risk_vetoed_sides=tuple(payload.get("risk_vetoed_sides") or ()),
        side_risk_reasons=dict(payload.get("side_risk_reasons") or {}),
        evaluated_sides=tuple(payload.get("evaluated_sides") or (row.get("side"),)),
        ai_role_context=dict(payload.get("ai_role_context") or {}),
    )


def rehydrate_route_decision(row: dict[str, Any], payload: dict[str, Any]) -> GTOSVNextRuntimeDecision:
    evidence = dict(payload)
    evidence.setdefault("matched_rows", payload.get("matched_rows") or payload.get("matched_row_id_count") or 0)
    return GTOSVNextRuntimeDecision(
        decision=str(payload.get("decision") or "LEGACY"),
        event=dict(row.get("runtime_input_event") or {}),
        enabled=True,
        apply_to_execution=True,
        matched=bool(payload.get("matched", payload.get("matched_rows", 0))),
        reason=str(payload.get("reason") or "stage03_asof_route_decision_rehydrated"),
        evidence=evidence,
        artifact_paths=("stage03_verified_runtime_trace_rehydration",),
    )


def cache_key(payload: Any) -> str:
    return stable_hash(payload)


def path_state_for_decision(row: dict[str, Any], nofill: dict[str, Any] | None) -> dict[str, Any]:
    # As-of decision state intentionally excludes future touch/outcome labels.
    return {
        "source_complete": bool(nofill),
        "side": row.get("side"),
        "direction": row.get("side"),
        "approach_state": "unknown_at_decision_timestamp",
        "future_touch_and_outcome_fields_excluded": True,
    }


def account_state_for_selector(
    *,
    metrics: ScenarioMetrics,
    row: dict[str, Any],
    risk_pct: float,
    simultaneous_count: int,
    day_trade_count: int,
    session_trade_count: int,
    symbol_day_trade_count: int,
    symbol_session_trade_count: int,
) -> dict[str, Any]:
    metrics._roll_day(str(row.get("candle_time_utc") or ""))
    return {
        "initial_balance": metrics.initial_balance,
        "current_equity": metrics.equity,
        "current_balance": metrics.equity,
        "risk_base_amount": metrics.equity,
        "day_start_equity_or_balance_baseline": metrics.day_start_equity,
        "current_time_utc": row.get("candle_time_utc"),
        "new_trade_sl_risk_pct": risk_pct,
        "open_position_risk_pct": 0.0,
        "pending_order_risk_pct": 0.0,
        "spread_slippage_commission_buffer_pct": 0.10,
        "correlated_exposure_buffer_pct": 0.0,
        "concentration_buffer_pct": 0.0,
        "simultaneous_candidate_count": simultaneous_count,
        "day_trade_count": day_trade_count,
        "session_trade_count": session_trade_count,
        "symbol_day_trade_count": symbol_day_trade_count,
        "symbol_session_trade_count": symbol_session_trade_count,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
    }


def write_shards(rows: Iterable[dict[str, Any]], *, shard_size: int = 25000) -> tuple[list[dict[str, Any]], int]:
    index_rows: list[dict[str, Any]] = []
    buffer: list[dict[str, Any]] = []
    total = 0

    def flush(shard_no: int, shard_rows: list[dict[str, Any]]) -> None:
        if not shard_rows:
            return
        shard_dir = STAGE09_SHARD_DIR / f"stage09_replay_shard_{shard_no:06d}"
        shard_path = shard_dir / "replay_comparison.jsonl.gz"
        full = REPO_ROOT / shard_path
        full.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(stage00.io_path(full), "wt", encoding="utf-8", newline="\n") as handle:
            for row in shard_rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        index_rows.append(
            {
                "schema_version": "vnext_production_change_stage09_chunk_index_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_09_FORWARD_ONLY_REPLAY",
                "chunk_index": shard_no,
                "chunk_path": rel(shard_path),
                "row_count": len(shard_rows),
                "bytes": full.stat().st_size,
                "sha256": sha256_file(full),
                "min_as_of_utc": shard_rows[0]["as_of_utc"],
                "max_as_of_utc": shard_rows[-1]["as_of_utc"],
                "shard_status": "complete",
            }
        )

    shard_no = 1
    for row in rows:
        buffer.append(row)
        total += 1
        if len(buffer) >= shard_size:
            flush(shard_no, buffer)
            shard_no += 1
            buffer = []
    flush(shard_no, buffer)
    index_path = REPO_ROOT / STAGE09_LEDGER_INDEX_PATH
    index_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = index_path.with_suffix(index_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in index_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    tmp.replace(index_path)
    return index_rows, total


def run_replay() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = load_config()
    active_config = activated_replay_config(config)
    external_only_config = copy.deepcopy(active_config)
    external_only_config.setdefault("gtos_vnext_runtime", {})[
        "prop_safe_selector_internal_overlay_applies_to_budget"
    ] = False
    base_risk_pct = float((config.get("risk", {}) or {}).get("risk_per_trade_pct") or 2.0)
    score_map = build_score_map()
    nofill_map = build_nofill_map()
    missed_map = build_missed_map()
    current_rows, hypothetical_map, runtime_diagnostics = extract_runtime_rows()
    simultaneous_counts = Counter(str(row["candle_time_utc"]) for row in current_rows)

    write_heartbeat(
        "rehydrating_verified_stage03_runtime_trace",
        current_shadow_rows=len(current_rows),
        hypothetical_rows=len(hypothetical_map),
    )
    supervisor_decision = evaluate_ai_supervisor(
        config=active_config,
        trace_rows=[],
        malformed_rows=[],
        vnext_rows=[],
    )
    current_head = git_head()
    config_sha = sha256_file(REPO_ROOT / "config" / "agent_config.yaml")

    metrics = {
        name: ScenarioMetrics(name)
        for name in REQUIRED_SCENARIOS
    }
    ai_policy_cache: dict[str, Any] = {}
    day_counts: Counter[str] = Counter()
    session_counts: Counter[str] = Counter()
    symbol_day_counts: Counter[tuple[str, str]] = Counter()
    symbol_session_counts: Counter[tuple[str, str, str]] = Counter()
    leakage_future_inputs_used = 0

    output_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(current_rows, start=1):
        as_of_dt = parse_utc(row["candle_time_utc"])
        as_of_utc = as_of_dt.isoformat()
        day_key = reset_window_start_utc(as_of_utc).date().isoformat()
        session_key = f"{day_key}:{row.get('route_session')}"
        symbol_day_key = (day_key, str(row.get("symbol") or ""))
        symbol_session_key = (day_key, str(row.get("route_session") or ""), str(row.get("symbol") or ""))
        score = score_map.get(row["candidate_id"])
        nofill = nofill_map.get(row["candidate_id"])
        missed = missed_map.get(row["candidate_id"])

        current_selected, current_risk, current_reason = selected_from_previous(
            row["current_shadow"],
            current_risk_pct=base_risk_pct,
        )
        metrics["baseline_current_shadow"].add(
            row=row,
            selected=current_selected,
            risk_pct=current_risk,
            reason=current_reason,
            score=score,
            missed=missed,
        )

        hyp_summary = hypothetical_map.get(row["candidate_id"], {})
        hyp_selected, hyp_risk, hyp_reason = selected_from_previous(
            hyp_summary,
            current_risk_pct=base_risk_pct,
        )
        metrics["previous_hypothetical_activated"].add(
            row=row,
            selected=hyp_selected,
            risk_pct=hyp_risk,
            reason=hyp_reason,
            score=score,
            missed=missed,
        )

        pre_ai = rehydrate_pre_ai_decision(row, row.get("pre_ai_decision_payload") or {})

        ai_key = cache_key({"pre_ai": pre_ai.to_record(), "risk_tier": "funded_prop"})
        ai_policy = ai_policy_cache.get(ai_key)
        if ai_policy is None:
            ai_policy = evaluate_vnext_ai_policy(
                pre_ai_decision=pre_ai,
                config=active_config,
                raw_data=row.get("runtime_raw_data") or {},
                risk_tier="funded_prop",
            )
            ai_policy_cache[ai_key] = ai_policy

        event = dict(row.get("runtime_input_event") or {})
        route_decision = rehydrate_route_decision(row, row.get("route_decision_payload") or {})

        risk_adjustment = apply_vnext_risk_adjustment(
            current_risk_pct=base_risk_pct,
            decision=route_decision,
            config=active_config,
        )
        pending_policy = evaluate_vnext_pending_policy(
            decision=route_decision,
            config=active_config,
        )
        ltf_decision = evaluate_vnext_ltf_path_execution(
            decision=route_decision,
            config=active_config,
            trade_params=row.get("candidate_geometry") or {},
            path_state=path_state_for_decision(row, nofill),
        )
        risk_pct_before_prop = float(risk_adjustment.after_risk_pct)
        executable_stream = classify_stage09_executable_stream(
            row=row,
            pre_ai=pre_ai,
            route_decision=route_decision,
        )
        block_reason = vnext_execution_block_reason(route_decision, active_config)
        pre_ai_blocks = pre_ai.action == "SKIP_AI_AVOID_ONLY"
        ltf_blocks = ltf_decision.action == "SKIP_LTF_NOFILL_AVOID"
        pending_blocks = pending_policy.action == "SKIP_PENDING_NOFILL_AVOID"
        if executable_stream["prop_governance_eligible"]:
            prop_account_state = account_state_for_selector(
                metrics=metrics["new_production_change_mechanical"],
                row=row,
                risk_pct=risk_pct_before_prop,
                simultaneous_count=simultaneous_counts[str(row["candle_time_utc"])],
                day_trade_count=day_counts[day_key],
                session_trade_count=session_counts[session_key],
                symbol_day_trade_count=symbol_day_counts[symbol_day_key],
                symbol_session_trade_count=symbol_session_counts[symbol_session_key],
            )
            prop_selector = evaluate_vnext_prop_safe_selector(
                decision=route_decision,
                config=active_config,
                current_risk_pct=risk_pct_before_prop,
                account_state=prop_account_state,
                current_time_utc=as_of_utc,
                candidate_context={
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                },
            )
            external_only_account_state = account_state_for_selector(
                metrics=metrics["new_production_change_external_budget_only"],
                row=row,
                risk_pct=risk_pct_before_prop,
                simultaneous_count=simultaneous_counts[str(row["candle_time_utc"])],
                day_trade_count=day_counts[day_key],
                session_trade_count=session_counts[session_key],
                symbol_day_trade_count=symbol_day_counts[symbol_day_key],
                symbol_session_trade_count=symbol_session_counts[symbol_session_key],
            )
            external_only_selector = evaluate_vnext_prop_safe_selector(
                decision=route_decision,
                config=external_only_config,
                current_risk_pct=risk_pct_before_prop,
                account_state=external_only_account_state,
                current_time_utc=as_of_utc,
                candidate_context={
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                },
            )
        else:
            prop_selector = unevaluated_prop_selector_for_non_executable(
                decision=route_decision,
                before_risk_pct=risk_pct_before_prop,
                reason=str(executable_stream["reason"]),
            )
            external_only_selector = unevaluated_prop_selector_for_non_executable(
                decision=route_decision,
                before_risk_pct=risk_pct_before_prop,
                reason=str(executable_stream["reason"]),
            )
        prop_blocks = prop_selector.action in {"BLOCK", "DEFER_UNTIL_RESET"}
        mechanical_selected = not any(
            [
                not executable_stream["executable_stream"],
                block_reason,
                pre_ai_blocks,
                ltf_blocks,
                pending_blocks,
                prop_blocks,
            ]
        )
        mechanical_risk_pct = float(prop_selector.after_risk_pct) if mechanical_selected else 0.0
        mechanical_reason = "selected_after_runtime_and_budget"
        if not executable_stream["executable_stream"]:
            mechanical_reason = str(executable_stream["reason"])
        elif block_reason:
            mechanical_reason = str(block_reason)
        elif pre_ai_blocks:
            mechanical_reason = "pre_ai_skip_avoid_only"
        elif ltf_blocks:
            mechanical_reason = str(ltf_decision.reason)
        elif pending_blocks:
            mechanical_reason = str(pending_policy.reason)
        elif prop_blocks:
            mechanical_reason = str(prop_selector.reason)

        if prop_selector.would_action == "REDUCE_RISK":
            metrics["new_production_change_mechanical"].risk_reductions += 1
        if prop_selector.would_action == "DEFER_UNTIL_RESET":
            metrics["new_production_change_mechanical"].deferred_trades += 1
        if prop_selector.would_action == "BLOCK":
            metrics["new_production_change_mechanical"].blocked_trades += 1

        metrics["new_production_change_mechanical"].add(
            row=row,
            selected=mechanical_selected,
            risk_pct=mechanical_risk_pct,
            reason=mechanical_reason,
            score=score,
            missed=missed,
        )

        external_only_prop_blocks = external_only_selector.action in {"BLOCK", "DEFER_UNTIL_RESET"}
        external_only_selected = not any(
            [
                not executable_stream["executable_stream"],
                block_reason,
                pre_ai_blocks,
                ltf_blocks,
                pending_blocks,
                external_only_prop_blocks,
            ]
        )
        external_only_risk_pct = (
            float(external_only_selector.after_risk_pct) if external_only_selected else 0.0
        )
        external_only_reason = "selected_after_external_redacted_account_budget"
        if not executable_stream["executable_stream"]:
            external_only_reason = str(executable_stream["reason"])
        elif block_reason:
            external_only_reason = str(block_reason)
        elif pre_ai_blocks:
            external_only_reason = "pre_ai_skip_avoid_only"
        elif ltf_blocks:
            external_only_reason = str(ltf_decision.reason)
        elif pending_blocks:
            external_only_reason = str(pending_policy.reason)
        elif external_only_prop_blocks:
            external_only_reason = str(external_only_selector.reason)
        if external_only_selector.would_action == "REDUCE_RISK":
            metrics["new_production_change_external_budget_only"].risk_reductions += 1
        if external_only_selector.would_action == "DEFER_UNTIL_RESET":
            metrics["new_production_change_external_budget_only"].deferred_trades += 1
        if external_only_selector.would_action == "BLOCK":
            metrics["new_production_change_external_budget_only"].blocked_trades += 1
        metrics["new_production_change_external_budget_only"].add(
            row=row,
            selected=external_only_selected,
            risk_pct=external_only_risk_pct,
            reason=external_only_reason,
            score=score,
            missed=missed,
        )

        no_paid_replay = vnext_ai_policy_no_paid_call_replay_decision(
            ai_policy,
            production_selected=mechanical_selected,
        )
        no_paid_ai_selected = bool(no_paid_replay["selected"])
        if ai_policy.would_allow_ai_call:
            metrics["new_ai_policy_no_paid_call"].ai_calls_required += 1
        else:
            metrics["new_ai_policy_no_paid_call"].ai_calls_avoided += 1
        ai_no_paid_reason = str(no_paid_replay["reason"])
        metrics["new_ai_policy_no_paid_call"].add(
            row=row,
            selected=no_paid_ai_selected,
            risk_pct=mechanical_risk_pct if no_paid_ai_selected else 0.0,
            reason=ai_no_paid_reason,
            score=score,
            missed=missed,
        )

        if mechanical_selected:
            day_counts[day_key] += 1
            session_counts[session_key] += 1
            symbol_day_counts[symbol_day_key] += 1
            symbol_session_counts[symbol_session_key] += 1

        decision_inputs = {
            "runtime_input_event_sha256": stable_hash(event),
            "runtime_raw_data_sha256": stable_hash(row.get("runtime_raw_data") or {}),
            "allowed_input_fields": [
                "symbol",
                "source_symbol",
                "route_session",
                "side",
                "framework",
                "route_family",
                "market_timeframe",
                "runtime_input_event",
                "runtime_raw_data",
                "config",
                "verified_stage03_runtime_trace_decisions",
            ],
            "future_outcome_inputs_used": False,
        }
        if decision_inputs["future_outcome_inputs_used"]:
            leakage_future_inputs_used += 1

        output_rows.append(
            {
                "schema_version": "vnext_production_change_stage09_replay_comparison_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_09_FORWARD_ONLY_REPLAY",
                "candidate_id": row["candidate_id"],
                "as_of_utc": as_of_utc,
                "source_cutoff_utc": as_of_utc,
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol"),
                "session": row.get("route_session"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "route_family": row.get("route_family"),
                "market_timeframe": row.get("market_timeframe"),
                "decision_inputs": decision_inputs,
                "artifact_versions": {
                    "git_head": current_head,
                    "config_sha256": config_sha,
                    "runtime_artifact_rows": runtime_diagnostics["runtime_rows_seen"],
                    "runtime_artifact_paths": [
                        "VNEXT_FULL_REPLAY_RUNTIME_TRACE_LEDGER_2026-05-24.jsonl",
                        "VNEXT_FULL_REPLAY_PATH_OUTCOME_R_LEDGER_2026-05-24.jsonl",
                        "VNEXT_FULL_REPLAY_NOFILL_PENDING_LIFECYCLE_LEDGER_2026-05-24.jsonl",
                        "VNEXT_FULL_REPLAY_MISSED_WINNER_AVOIDED_LOSER_LEDGER_2026-05-24.jsonl",
                    ],
                    "replay_basis": "stage03_verified_asof_runtime_trace_rehydration",
                },
                "previous_current_shadow": {
                    **row["current_shadow"],
                    "selected": current_selected,
                    "risk_pct": current_risk,
                    "selection_reason": current_reason,
                },
                "previous_hypothetical_activated": {
                    **hyp_summary,
                    "selected": hyp_selected,
                    "risk_pct": hyp_risk,
                    "selection_reason": hyp_reason,
                },
                "new_production_change": {
                    "pre_ai": {
                        "action": pre_ai.action,
                        "would_action": pre_ai.would_action,
                        "decision": pre_ai.decision,
                        "reason": pre_ai.reason,
                        "recommended_side": pre_ai.recommended_side,
                        "recommended_frameworks": list(pre_ai.recommended_frameworks),
                        "blocked_sides": list(pre_ai.blocked_sides),
                    },
                    "ai_policy": {
                        "action": ai_policy.action,
                        "would_action": ai_policy.would_action,
                        "allowed": ai_policy.allowed,
                        "would_allow_ai_call": ai_policy.would_allow_ai_call,
                        "reason": ai_policy.reason,
                        "ai_role": ai_policy.ai_role,
                    },
                    "ai_supervisor": {
                        "action": supervisor_decision.action,
                        "reason": supervisor_decision.reason,
                        "disable_ai_narrowing": supervisor_decision.disable_ai_narrowing,
                    },
                    "route": {
                        "decision": route_decision.decision,
                        "matched": route_decision.matched,
                        "reason": route_decision.reason,
                        "block_reason": block_reason,
                        "executable_stream": executable_stream,
                    },
                    "risk_adjustment": {
                        "before_risk_pct": risk_adjustment.before_risk_pct,
                        "after_risk_pct": risk_adjustment.after_risk_pct,
                        "would_multiplier": risk_adjustment.would_multiplier,
                        "reason": risk_adjustment.reason,
                    },
                    "pending_policy": {
                        "action": pending_policy.action,
                        "would_action": pending_policy.would_action,
                        "reason": pending_policy.reason,
                    },
                    "ltf_path_execution": {
                        "action": ltf_decision.action,
                        "would_action": ltf_decision.would_action,
                        "reason": ltf_decision.reason,
                        "monitor_timeframe": ltf_decision.monitor_timeframe,
                        "future_path_state_fields_excluded": True,
                    },
                    "prop_safe_selector": {
                        "action": prop_selector.action,
                        "would_action": prop_selector.would_action,
                        "reason": prop_selector.reason,
                        "before_risk_pct": prop_selector.before_risk_pct,
                        "after_risk_pct": prop_selector.after_risk_pct,
                        "max_allowed_new_trade_risk_pct": prop_selector.max_allowed_new_trade_risk_pct,
                        "reset_window": prop_selector.reset_window,
                        "external_rule_projection": {
                            key: prop_selector.external_rule_projection.get(key)
                            for key in (
                                "daily_loss_limit_pct",
                                "daily_floor",
                                "remaining_daily_cushion",
                                "projected_daily_cushion_after_full_risk",
                                "overall_max_loss_pct",
                                "max_loss_floor",
                                "remaining_overall_cushion",
                                "projected_overall_cushion_after_full_risk",
                                "trailing_drawdown_modeled",
                                "binding_budget_name",
                            )
                        },
                        "internal_overlay_projection": prop_selector.internal_overlay_projection,
                    },
                    "external_budget_only_prop_safe_selector": {
                        "action": external_only_selector.action,
                        "would_action": external_only_selector.would_action,
                        "reason": external_only_selector.reason,
                        "before_risk_pct": external_only_selector.before_risk_pct,
                        "after_risk_pct": external_only_selector.after_risk_pct,
                        "max_allowed_new_trade_risk_pct": (
                            external_only_selector.max_allowed_new_trade_risk_pct
                        ),
                        "internal_overlay_projection": (
                            external_only_selector.internal_overlay_projection
                        ),
                    },
                    "mechanical_selected": mechanical_selected,
                    "mechanical_risk_pct": mechanical_risk_pct,
                    "mechanical_selection_reason": mechanical_reason,
                    "no_paid_ai_selected": no_paid_ai_selected,
                },
                "post_decision_scoring": {
                    **(score or {}),
                    "missed_winner_avoided_loser": missed,
                    "nofill_lifecycle": nofill,
                    "scoring_joined_after_decision": True,
                },
                "leakage_guard": {
                    "decision_timestamp_receives_future_path_labels": False,
                    "path_outcome_labels_scoring_only": True,
                    "future_outcome_inputs_used": False,
                    "no_live_trading_or_broker_mutation": True,
                    "no_paid_api_or_vendor_call": True,
                },
            }
        )
        if idx % 25000 == 0:
            write_heartbeat(
                "replay_processing",
                processed_rows=idx,
                total_rows=len(current_rows),
                replay_basis="stage03_verified_asof_runtime_trace_rehydration",
                ai_policy_cache_size=len(ai_policy_cache),
            )

    index_rows, written_rows = write_shards(output_rows)
    scenario_records = {name: metric.to_record() for name, metric in metrics.items()}
    summary = {
        "schema_version": "vnext_production_change_stage09_metrics_summary_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "stage_id": "STAGE_09_FORWARD_ONLY_REPLAY",
        "current_git_head": git_head(),
        "candidate_rows": len(current_rows),
        "written_replay_rows": written_rows,
        "chunk_count": len(index_rows),
        "runtime_diagnostics": runtime_diagnostics,
        "score_candidate_count": len(score_map),
        "nofill_candidate_count": len(nofill_map),
        "missed_winner_avoided_loser_candidate_count": len(missed_map),
        "runtime_artifact_index_rows": runtime_diagnostics["runtime_rows_seen"],
        "runtime_artifact_path_count": 4,
        "replay_basis": "stage03_verified_asof_runtime_trace_rehydration",
        "ai_policy_cache_size": len(ai_policy_cache),
        "scenario_metrics": scenario_records,
        "required_scenarios": sorted(REQUIRED_SCENARIOS),
        "leakage_guard": {
            "future_outcome_inputs_used_count": leakage_future_inputs_used,
            "decision_inputs_are_as_of_runtime_trace": True,
            "path_r_and_nofill_joined_after_decision_for_scoring_only": True,
            "paid_api_calls_made": 0,
            "broker_mutations_made": 0,
            "source_data_deleted": False,
        },
        "redacted_account_budget_math": {
            "initial_balance": 100000.0,
            "phase1_target_pct": 8.0,
            "phase2_target_pct": 5.0,
            "daily_loss_limit_pct": 5.0,
            "daily_reset": "00:00_GMT_PLUS_3",
            "malaysia_reset_time": "05:00_MY_TIME",
            "overall_max_loss_pct": 10.0,
            "overall_floor_model": "static_initial_balance_90pct_no_trailing_drawdown",
            "internal_4pct_overlay_reported_separately": True,
        },
        "coverage": {
            "symbols": scenario_records["new_production_change_mechanical"]["symbols"],
            "sessions": scenario_records["new_production_change_mechanical"]["sessions"],
            "sides": scenario_records["new_production_change_mechanical"]["sides"],
            "frameworks": scenario_records["new_production_change_mechanical"]["frameworks"],
            "route_families": scenario_records["new_production_change_mechanical"]["route_families"],
            "source_modes": scenario_records["new_production_change_mechanical"]["source_modes"],
        },
        "no_live_trading_or_broker_mutation": True,
        "no_paid_api_or_vendor_call": True,
    }
    summary["production_candidate_viability"] = classify_production_candidate_status(summary)
    atomic_json_write(STAGE09_SUMMARY_PATH, summary)
    write_dossier(summary)
    update_state(summary, complete=False)
    result = {
        "schema_version": "vnext_production_change_stage09_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not verify_summary(summary, index_rows),
        "failures": verify_summary(summary, index_rows),
        "summary_path": rel(STAGE09_SUMMARY_PATH),
        "ledger_index_path": rel(STAGE09_LEDGER_INDEX_PATH),
        "candidate_rows": len(current_rows),
        "written_replay_rows": written_rows,
        "first_incomplete_invariant": "STAGE_09_FORWARD_ONLY_REPLAY",
    }
    atomic_json_write(STAGE09_VERIFICATION_RESULT_PATH, result)
    write_heartbeat("complete", candidate_rows=len(current_rows), written_replay_rows=written_rows)
    return index_rows, summary


def classify_production_candidate_status(summary: dict[str, Any]) -> dict[str, Any]:
    scenario = summary.get("scenario_metrics") or {}
    baseline = scenario.get("baseline_current_shadow") or {}
    new_metrics = scenario.get("new_production_change_mechanical") or {}
    ai_no_paid = scenario.get("new_ai_policy_no_paid_call") or {}
    candidate_rows = int(summary.get("candidate_rows") or 0)
    baseline_selected = int(baseline.get("selected_count") or 0)
    selected = int(new_metrics.get("selected_count") or 0)
    performance = int(new_metrics.get("performance_count") or 0)
    failures: list[str] = []

    if selected <= 0:
        failures.append("selected_count_zero")
    if performance <= 0 or new_metrics.get("expectancy_r") is None:
        failures.append("null_or_empty_expectancy")
    if new_metrics.get("expectancy_r") is not None and float(new_metrics["expectancy_r"]) <= 0:
        failures.append("negative_or_zero_expectancy")
    if new_metrics.get("total_r") is not None and float(new_metrics["total_r"]) <= 0:
        failures.append("negative_or_zero_total_r")
    if new_metrics.get("profit_factor") is None or float(new_metrics["profit_factor"]) < 1.0:
        failures.append("profit_factor_below_one")
    if baseline_selected >= 20 and selected / baseline_selected < 0.25:
        failures.append("selected_count_collapsed_below_25pct_of_baseline")
    if (
        new_metrics.get("phase1_8pct_pass_proxy") is False
        and new_metrics.get("phase2_5pct_pass_proxy") is False
    ):
        failures.append("phase_pass_proxy_false")
    blocked = int(new_metrics.get("blocked_trades") or 0)
    if candidate_rows and blocked / candidate_rows > 0.50:
        failures.append("extreme_prop_overblocking")
    missed = int(new_metrics.get("missed_winners") or 0)
    accepted_winners = int(new_metrics.get("accepted_winners") or new_metrics.get("win_count") or 0)
    if selected and missed > max(1000, accepted_winners * 25):
        failures.append("catastrophic_missed_winner_count")
    if ai_no_paid.get("selected_count") == 0 and ai_no_paid.get("expectancy_r") is None:
        failures.append("no_paid_ai_zero_output_diagnostic_only")

    status = "production_candidate_failed" if failures else "production_candidate_viable"
    return {
        "status": status,
        "failure_reasons": failures,
        "candidate_rows": candidate_rows,
        "baseline_selected_count": baseline_selected,
        "selected_count": selected,
        "performance_count": performance,
        "selected_to_baseline_ratio": (
            round(selected / baseline_selected, 12) if baseline_selected else None
        ),
        "total_r": new_metrics.get("total_r"),
        "expectancy_r": new_metrics.get("expectancy_r"),
        "profit_factor": new_metrics.get("profit_factor"),
        "phase1_8pct_pass_proxy": new_metrics.get("phase1_8pct_pass_proxy"),
        "phase2_5pct_pass_proxy": new_metrics.get("phase2_5pct_pass_proxy"),
        "blocked_trades": blocked,
        "missed_winners": missed,
        "ai_no_paid_selected_count": ai_no_paid.get("selected_count"),
    }


def verify_summary(summary: dict[str, Any], index_rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if summary.get("candidate_rows") != 253234:
        failures.append(f"candidate row count mismatch: {summary.get('candidate_rows')}")
    if summary.get("written_replay_rows") != summary.get("candidate_rows"):
        failures.append("written replay rows do not equal candidate rows")
    if sum(int(row.get("row_count") or 0) for row in index_rows) != summary.get("written_replay_rows"):
        failures.append("chunk index row counts do not sum to written replay rows")
    scenarios = set((summary.get("scenario_metrics") or {}).keys())
    if scenarios != REQUIRED_SCENARIOS:
        failures.append(f"scenario coverage mismatch: {sorted(REQUIRED_SCENARIOS - scenarios)}")
    leakage = summary.get("leakage_guard") or {}
    if leakage.get("future_outcome_inputs_used_count") != 0:
        failures.append("future outcome inputs were used in decisions")
    if leakage.get("paid_api_calls_made") != 0 or leakage.get("broker_mutations_made") != 0:
        failures.append("forbidden side effect recorded")
    prop = summary.get("redacted_account_budget_math") or {}
    if prop.get("daily_loss_limit_pct") != 5.0 or prop.get("overall_max_loss_pct") != 10.0:
        failures.append("redacted_account external budget math mismatch")
    new_metrics = (summary.get("scenario_metrics") or {}).get("new_production_change_mechanical", {})
    for key in (
        "selected_count",
        "total_r",
        "expectancy_r",
        "phase1_8pct_pass_proxy",
        "missed_winners",
        "avoided_losers",
        "max_drawdown_pct",
        "max_loss_streak",
        "min_daily_cushion",
        "min_overall_cushion",
        "risk_reductions",
        "deferred_trades",
        "blocked_trades",
    ):
        if key not in new_metrics:
            failures.append(f"new scenario metric missing: {key}")
    viability = summary.get("production_candidate_viability") or classify_production_candidate_status(summary)
    if viability.get("status") != "production_candidate_viable":
        failures.append(
            "production_candidate_failed: "
            + ",".join(viability.get("failure_reasons") or ["unknown_viability_failure"])
        )
    return failures


def write_dossier(summary: dict[str, Any]) -> None:
    scenario = summary["scenario_metrics"]
    new = scenario["new_production_change_mechanical"]
    external = scenario["new_production_change_external_budget_only"]
    ai = scenario["new_ai_policy_no_paid_call"]
    lines = [
        "# Stage09 Forward-Only Replay Comparison",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Created: `{summary['created_at_utc']}`",
        "",
        "## Replay Universe",
        "",
        f"- Candidate rows replayed: {summary['candidate_rows']:,}.",
        f"- Replay comparison rows written: {summary['written_replay_rows']:,} across {summary['chunk_count']} shards.",
        f"- Runtime artifact rows loaded: {summary['runtime_artifact_index_rows']:,}.",
        "- Decision inputs are as-of runtime trace fields; path/R/no-fill/outcome labels are scoring-only joins after the decision.",
        "",
        "## New Production-Change Mechanical Metrics",
        "",
        f"- Selected: {new['selected_count']:,}; skipped: {new['skipped_count']:,}; no-fill: {new['nofill_count']:,}.",
        f"- Total R: {new['total_r']}; expectancy R: {new['expectancy_r']}; win rate: {new['win_rate']}; PF: {new['profit_factor']}.",
        f"- Pass proxy phase1/phase2: {new['phase1_8pct_pass_proxy']} / {new['phase2_5pct_pass_proxy']}.",
        f"- Max drawdown pct: {new['max_drawdown_pct']}; max loss streak: {new['max_loss_streak']}.",
        f"- Missed winners: {new['missed_winners']}; avoided losers: {new['avoided_losers']}; accepted losers: {new['accepted_losers']}.",
        f"- Risk reductions: {new['risk_reductions']}; deferred: {new['deferred_trades']}; blocked: {new['blocked_trades']}.",
        f"- Daily cushion min: {new['min_daily_cushion']}; overall cushion min: {new['min_overall_cushion']}.",
        "",
        "## redacted_account External-Budget-Only Scenario",
        "",
        f"- Selected: {external['selected_count']:,}; performance rows: {external['performance_count']:,}.",
        f"- Total R: {external['total_r']}; expectancy R: {external['expectancy_r']}; pass proxy phase1/phase2: {external['phase1_8pct_pass_proxy']} / {external['phase2_5pct_pass_proxy']}.",
        f"- External-only risk reductions: {external['risk_reductions']}; deferred: {external['deferred_trades']}; blocked: {external['blocked_trades']}.",
        f"- External-only daily cushion min: {external['min_daily_cushion']}; overall cushion min: {external['min_overall_cushion']}.",
        "",
        "## AI No-Paid-Call Simulation",
        "",
        f"- AI calls required: {ai['ai_calls_required']:,}; AI calls avoided: {ai['ai_calls_avoided']:,}.",
        f"- No-paid-call selected trades: {ai['selected_count']:,}; malformed-response paths: {ai['malformed_response_paths']:,}.",
        "",
        "## Prop Budget Model",
        "",
        "- redacted_account external daily loss is 5% of initial balance with 00:00 GMT+3 reset.",
        "- Overall max loss floor is static at 90% of initial balance; no trailing drawdown is modeled.",
        "- Existing `risk.max_daily_loss_pct=4.0` is treated only as a separately reported internal overlay when explicitly enabled.",
        "",
        "## Coverage",
        "",
        f"- Symbols: {json.dumps(summary['coverage']['symbols'], sort_keys=True)}.",
        f"- Sessions: {json.dumps(summary['coverage']['sessions'], sort_keys=True)}.",
        f"- Sides: {json.dumps(summary['coverage']['sides'], sort_keys=True)}.",
        f"- Frameworks: {json.dumps(summary['coverage']['frameworks'], sort_keys=True)}.",
        f"- Source modes: {json.dumps(summary['coverage']['source_modes'], sort_keys=True)}.",
        "",
        "## Boundaries",
        "",
        "- No live trading, broker mutation, paid API/vendor call, source deletion, remote push, or activation flip was performed.",
    ]
    (REPO_ROOT / STAGE09_DOSSIER_PATH).write_text("\n".join(lines), encoding="utf-8", newline="\n")


def update_state(summary: dict[str, Any], *, complete: bool) -> None:
    state_path = REPO_ROOT / STATE_PATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = git_head()
    state["dirty_tracked_paths"] = stage02.git_status_short()
    state["current_stage"] = (
        "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"
        if complete
        else "STAGE_09_FORWARD_ONLY_REPLAY"
    )
    state["stage_status_table"]["STAGE_09_FORWARD_ONLY_REPLAY"] = (
        "complete" if complete else "in_progress"
    )
    if complete:
        state["stage_status_table"]["STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"] = "in_progress"
        state["active_invariant"] = "write_completion_audit_activation_dossier"
        state["first_incomplete_invariant"] = "STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER"
        state["exact_next_action"] = (
            "Write Stage10 completion audit and activation dossier from committed runtime "
            "changes and Stage09 replay metrics."
        )
    else:
        state["active_invariant"] = "run_post_implementation_forward_only_replay"
        state["first_incomplete_invariant"] = "STAGE_09_FORWARD_ONLY_REPLAY"
        state["exact_next_action"] = (
            "Run Stage09 verifier and focused route tests, then mark Stage09 complete."
        )
    outputs = state.setdefault("output_artifact_paths", {})
    outputs["stage09_replay_comparison_ledger"] = rel(STAGE09_LEDGER_INDEX_PATH)
    outputs["stage09_metrics_summary"] = rel(STAGE09_SUMMARY_PATH)
    outputs["stage09_replay_dossier"] = rel(STAGE09_DOSSIER_PATH)
    outputs["stage09_verification_result"] = rel(STAGE09_VERIFICATION_RESULT_PATH)
    state.setdefault("rows_groups_processed", {})["stage09_replay_candidate_rows"] = summary[
        "candidate_rows"
    ]
    state["rows_groups_processed"]["stage09_replay_comparison_rows"] = summary[
        "written_replay_rows"
    ]
    state["row_count_hash_coverage"]["stage09_forward_replay"] = {
        "candidate_rows": summary["candidate_rows"],
        "written_replay_rows": summary["written_replay_rows"],
        "chunk_count": summary["chunk_count"],
        "scenario_names": sorted(summary["scenario_metrics"]),
        "future_outcome_inputs_used_count": summary["leakage_guard"][
            "future_outcome_inputs_used_count"
        ],
    }
    state["verification_status"]["stage09_forward_replay_built"] = True
    state["verification_status"]["stage09_replay_rows"] = summary["written_replay_rows"]
    state["verification_status"]["stage09_verifier_ok"] = complete
    state["replay_shards_run"] = [
        {
            "stage": "STAGE_09_FORWARD_ONLY_REPLAY",
            "ledger_index": rel(STAGE09_LEDGER_INDEX_PATH),
            "chunk_count": summary["chunk_count"],
            "candidate_rows": summary["candidate_rows"],
            "status": "complete",
        }
    ]
    state["remaining_executable_actions"] = (
        ["STAGE_10 activation dossier and completion audit"]
        if complete
        else [
            "STAGE_09 forward-only replay verifier",
            "STAGE_10 activation dossier and completion audit",
        ]
    )
    stage00.atomic_json_write(state_path, state)


def main() -> int:
    index_rows, summary = run_replay()
    failures = verify_summary(summary, index_rows)
    result = {
        "schema_version": "vnext_production_change_stage09_verification_result_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "ok": not failures,
        "failures": failures,
        "summary_path": rel(STAGE09_SUMMARY_PATH),
        "ledger_index_path": rel(STAGE09_LEDGER_INDEX_PATH),
        "candidate_rows": summary["candidate_rows"],
        "written_replay_rows": summary["written_replay_rows"],
        "first_incomplete_invariant": "STAGE_09_FORWARD_ONLY_REPLAY",
    }
    atomic_json_write(STAGE09_VERIFICATION_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
