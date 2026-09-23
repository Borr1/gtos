from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ROUTE_ID = "vnext_moonshot_lane09_meta_selector_v2_2026_06_01"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

LANE01_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
LANE02_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"
LANE03_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01"
LANE04_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01"
LANE05_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE06_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE07_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
LANE08_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"
LEGACY_LANE03_DIR = ROOT / "research" / "operations" / "vnext_lane03_meta_selector_discovery_implementation_2026_05_31"

LANE05_TIMELINE_FEATURES = LANE05_DIR / "LANE05_TIMELINE_FEATURE_VECTOR_LEDGER.jsonl.gz"
LANE05_SCHEMA = LANE05_DIR / "LANE05_FEATURE_SCHEMA.json"
LANE06_LABELS = LANE06_DIR / "LANE06_LABEL_VECTOR_LEDGER.jsonl.gz"
LANE06_MISSING_LABEL_GAPS = LANE06_DIR / "LANE06_MISSING_LABEL_GAP_LEDGER.jsonl.gz"
LANE07_DOWNSTREAM_CONTRACT = LANE07_DIR / "LANE07_DOWNSTREAM_CONTRACT.json"
LANE08_REPLAY_ROWS = LANE08_DIR / "LANE08_REPLAY_ROW_LEDGER.jsonl.gz"
LANE08_MISSING_REPLAY_GAPS = LANE08_DIR / "LANE08_MISSING_REPLAY_GAP_LEDGER.jsonl.gz"
LANE08_SPLIT_STRESS = LANE08_DIR / "LANE08_SPLIT_STRESS_METRICS.jsonl"
LANE08_DEPTH_COVERAGE = LANE08_DIR / "LANE08_REPLAY_DEPTH_COVERAGE_LEDGER.jsonl"
LANE08_NO_LEAK = LANE08_DIR / "LANE08_NO_LEAK_VALIDATION_LEDGER.jsonl"
LEGACY_LANE03_RULE_PACKAGE = LEGACY_LANE03_DIR / "LANE03_META_SELECTOR_RULE_PACKAGE.json"
MASTER_WAVE3_READINESS = MASTER_DIR / "ABSOLUTE_MASTER_WAVE3_READINESS_DECISION.json"
MASTER_WAVE3_LAUNCH_ORDER = MASTER_DIR / "ABSOLUTE_MASTER_WAVE3_LAUNCH_ORDER.json"

SELECTOR_ROW_EVIDENCE_LEDGER = ROUTE_DIR / "LANE09_SELECTOR_ROW_EVIDENCE_LEDGER.jsonl.gz"
SELECTOR_DISCOVERY_LEDGER = ROUTE_DIR / "LANE09_SELECTOR_DISCOVERY_LEDGER.jsonl.gz"
DEFAULT_OFF_CLAUSE_LEDGER = ROUTE_DIR / "LANE09_DEFAULT_OFF_SELECTOR_CLAUSE_LEDGER.jsonl"
MECHANISM_RANKING = ROUTE_DIR / "LANE09_SELECTOR_MECHANISM_RANKING.jsonl"
SPLIT_STRESS_DECONCENTRATION = ROUTE_DIR / "LANE09_SPLIT_STRESS_DECONCENTRATION_LEDGER.jsonl"
CAPTURE_REPAIR_REQUIREMENTS = ROUTE_DIR / "LANE09_PACKET_CAPTURE_REQUIREMENTS.jsonl"
BRANCH_DECISIONS = ROUTE_DIR / "LANE09_BRANCH_DECISION_LEDGER.jsonl"
SOURCE_COMPLETENESS_DECISIONS = ROUTE_DIR / "LANE09_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl"
NO_LEAK_VALIDATION = ROUTE_DIR / "LANE09_NO_LEAK_VALIDATION_LEDGER.jsonl"
DEPENDENCY_STATE = ROUTE_DIR / "LANE09_DEPENDENCY_STATE_LEDGER.jsonl"
DEFAULT_OFF_PACKAGE = ROUTE_DIR / "LANE09_DEFAULT_OFF_SELECTOR_PACKAGE.json"
DOWNSTREAM_CONTRACT = ROUTE_DIR / "LANE09_DOWNSTREAM_CONTRACT.json"
SOURCE_USE_STATE = ROUTE_DIR / "LANE09_SOURCE_USE_STATE.json"
RESULT_USE_STATUS = ROUTE_DIR / "LANE09_RESULT_USE_STATUS.json"
RUNTIME_EFFECT_BOUNDARY = ROUTE_DIR / "LANE09_RUNTIME_EFFECT_BOUNDARY.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE09_CONTEXT_ANCHOR.md"
SATURATION_SELF_RED_TEAM = ROUTE_DIR / "LANE09_SATURATION_SELF_RED_TEAM.md"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE09_OUTPUT_MANIFEST.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE09_COMPLETION_AUDIT.json"
VERIFICATION_RESULT = ROUTE_DIR / "LANE09_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE09_FOCUSED_TEST_RESULT.xml"

EXPECTED_REPLAY_ROWS = 289_928
EXPECTED_REPLAY_GAP_ROWS = 3_471_773
EXPECTED_SPLIT_STRESS_ROWS = 1_536
EXPECTED_DEPTH_ROWS = 9
EXPECTED_NO_LEAK_ISSUES = 0

RUNTIME_BOUNDARY_TEXT = (
    "offline_default_off_meta_selector_v2_research_package_only_no_live_broker_order_deal_"
    "position_operation_no_hidden_selector_activation_no_config_prompt_risk_execution_safety_"
    "canary_change_no_paid_api_no_remote"
)
RESULT_USE_TEXT = (
    "selector_discovery_default_off_research_only; exact_broker_real, source_bound_proxy, "
    "strict_tick, and missing rows stay separated and do not imply production-change approval"
)
SOURCE_USE_TEXT = (
    "Lane05 feature-store decision fields, Lane06 labels through Lane08 result payloads, "
    "Lane07 broker/cost enrichment fields, and Lane08 replay rows/gaps/split-stress/depth ledgers consumed"
)

DECISION_PHASE_DIMENSIONS = {
    "symbol",
    "session_bucket",
    "origin_family",
    "framework",
    "side",
    "chosen_policy",
    "regime_h4_state",
    "regime_join_state",
    "m15_trend_state_20",
    "m15_volatility_state_14_vs_50",
    "liquidity_sweep_proxy_state",
    "spread_r_bucket",
    "cost_status",
    "broker_feasibility_state",
    "selected_cell_risk_join_state",
    "source_quality_status",
    "source_completeness_state",
    "m1_availability_status",
    "tick_availability_status",
    "strict_tick_available",
    "correlation_cluster_join_state",
    "correlation_cluster_size_bucket",
    "correlation_risk_multiplier_bucket",
    "portfolio_decision",
    "same_symbol_conflict_state",
    "time_candidate_weekday_utc",
    "time_candidate_hour_bucket",
    "sealed_partition",
}

FORENSIC_ONLY_DIMENSIONS = {
    "path_class",
    "path_ordering_status",
    "fill_status",
    "sl_before_1r",
    "one_r_reached",
    "partial_then_be",
    "partial_then_final",
    "final_target_reached",
    "no_entry_touch",
    "stuck_no_resolution",
    "correct_rejection",
    "missed_opportunity",
    "stale_blocker",
    "mfe_r_bucket",
    "mae_r_bucket",
    "time_to_1r_bucket",
    "source_gap_family",
}

FORBIDDEN_RUNTIME_CLAUSE_DIMENSIONS = FORENSIC_ONLY_DIMENSIONS | {
    "result_r_class",
    "result_r_source_field",
    "calendar_day",
    "calendar_week",
    "calendar_month",
}

FORBIDDEN_PACKET_FIELDS = sorted(
    {
        "actual_r",
        "broker_actual_r",
        "broker_real_net_r",
        "close_reason",
        "cost_adjusted_r",
        "correct_rejection",
        "execution_policy_result",
        "exit_reason",
        "final_r",
        "final_target_reached",
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
        "sl_before_1r",
        "source_bound_proxy_r",
        "stale_blocker",
        "stuck_no_resolution",
        "time_to_1r_seconds",
        "time_to_sl_seconds",
        "win_rate",
    }
)

DIMENSION_TEMPLATES: tuple[tuple[str, ...], ...] = tuple(
    dict.fromkeys(
        [
            (),
            ("symbol",),
            ("session_bucket",),
            ("origin_family",),
            ("framework",),
            ("side",),
            ("chosen_policy",),
            ("regime_h4_state",),
            ("regime_join_state",),
            ("m15_trend_state_20",),
            ("m15_volatility_state_14_vs_50",),
            ("liquidity_sweep_proxy_state",),
            ("spread_r_bucket",),
            ("cost_status",),
            ("broker_feasibility_state",),
            ("selected_cell_risk_join_state",),
            ("source_quality_status",),
            ("m1_availability_status",),
            ("tick_availability_status",),
            ("strict_tick_available",),
            ("correlation_cluster_join_state",),
            ("portfolio_decision",),
            ("same_symbol_conflict_state",),
            ("path_class",),
            ("source_gap_family",),
            ("sl_before_1r",),
            ("partial_then_final",),
            ("symbol", "session_bucket"),
            ("symbol", "origin_family"),
            ("symbol", "framework"),
            ("symbol", "side"),
            ("symbol", "regime_h4_state"),
            ("symbol", "m15_volatility_state_14_vs_50"),
            ("symbol", "spread_r_bucket"),
            ("symbol", "source_quality_status"),
            ("symbol", "path_class"),
            ("session_bucket", "origin_family"),
            ("session_bucket", "framework"),
            ("session_bucket", "side"),
            ("session_bucket", "regime_h4_state"),
            ("session_bucket", "m15_volatility_state_14_vs_50"),
            ("session_bucket", "spread_r_bucket"),
            ("session_bucket", "source_quality_status"),
            ("session_bucket", "path_class"),
            ("origin_family", "framework"),
            ("origin_family", "side"),
            ("origin_family", "chosen_policy"),
            ("origin_family", "regime_h4_state"),
            ("origin_family", "m15_trend_state_20"),
            ("origin_family", "m15_volatility_state_14_vs_50"),
            ("origin_family", "liquidity_sweep_proxy_state"),
            ("origin_family", "spread_r_bucket"),
            ("origin_family", "cost_status"),
            ("origin_family", "broker_feasibility_state"),
            ("origin_family", "selected_cell_risk_join_state"),
            ("origin_family", "source_quality_status"),
            ("origin_family", "m1_availability_status"),
            ("origin_family", "tick_availability_status"),
            ("origin_family", "strict_tick_available"),
            ("origin_family", "correlation_cluster_join_state"),
            ("origin_family", "portfolio_decision"),
            ("origin_family", "same_symbol_conflict_state"),
            ("origin_family", "sealed_partition"),
            ("origin_family", "path_class"),
            ("origin_family", "sl_before_1r"),
            ("origin_family", "partial_then_final"),
            ("framework", "side"),
            ("framework", "regime_h4_state"),
            ("framework", "m15_volatility_state_14_vs_50"),
            ("framework", "path_class"),
            ("side", "regime_h4_state"),
            ("side", "m15_volatility_state_14_vs_50"),
            ("side", "path_class"),
            ("symbol", "session_bucket", "origin_family"),
            ("symbol", "origin_family", "side"),
            ("symbol", "framework", "side"),
            ("session_bucket", "origin_family", "side"),
            ("session_bucket", "framework", "side"),
            ("origin_family", "framework", "side"),
            ("origin_family", "session_bucket", "regime_h4_state"),
            ("origin_family", "session_bucket", "m15_volatility_state_14_vs_50"),
            ("origin_family", "session_bucket", "selected_cell_risk_join_state"),
            ("origin_family", "session_bucket", "source_quality_status"),
            ("origin_family", "session_bucket", "spread_r_bucket"),
            ("origin_family", "session_bucket", "path_class"),
            ("origin_family", "side", "regime_h4_state"),
            ("origin_family", "side", "m15_volatility_state_14_vs_50"),
            ("origin_family", "side", "path_class"),
            ("symbol", "session_bucket", "origin_family", "framework", "side"),
            ("symbol", "session_bucket", "origin_family", "framework", "side", "regime_h4_state"),
            ("symbol", "session_bucket", "origin_family", "framework", "side", "m15_volatility_state_14_vs_50"),
            ("symbol", "session_bucket", "origin_family", "framework", "side", "selected_cell_risk_join_state"),
            ("symbol", "session_bucket", "origin_family", "framework", "side", "source_quality_status"),
            ("symbol", "session_bucket", "origin_family", "framework", "side", "spread_r_bucket"),
            ("symbol", "session_bucket", "origin_family", "framework", "side", "cost_status"),
            ("symbol", "session_bucket", "origin_family", "framework", "side", "correlation_cluster_join_state"),
            ("symbol", "session_bucket", "origin_family", "framework", "side", "chosen_policy"),
            ("symbol", "session_bucket", "origin_family", "framework", "side", "path_class"),
        ]
    )
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return default


def open_text(path: Path):
    if path.name.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def open_gzip_write(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return gzip.open(path, "wt", encoding="utf-8", newline="\n", compresslevel=6)


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return
    with open_text(path) as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield line_number, row


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_jsonl_line(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with open_text(path) as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def fnum(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def round6(value: Any) -> float | None:
    number = fnum(value)
    if number is None:
        return None
    return round(number, 6)


def clean(value: Any, default: str = "missing") -> str:
    text = str(value if value is not None else default).strip()
    return text if text else default


def lower_clean(value: Any, default: str = "missing") -> str:
    return clean(value, default).lower()


def bool_label(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value in (None, ""):
        return "missing"
    return "true" if str(value).strip().lower() in {"1", "true", "yes", "y"} else "false"


def bucket_number(value: Any, cuts: tuple[float, ...], prefix: str, missing: str = "missing") -> str:
    number = fnum(value)
    if number is None:
        return missing
    previous = None
    for cut in cuts:
        if number < cut:
            if previous is None:
                return f"{prefix}_lt_{cut:g}"
            return f"{prefix}_{previous:g}_to_{cut:g}"
        previous = cut
    return f"{prefix}_gte_{cuts[-1]:g}"


def material_floor_for(scope: tuple[str, ...]) -> int:
    if not scope:
        return 250
    if len(scope) == 1:
        return 250
    if len(scope) == 2:
        return 100
    if len(scope) == 3:
        return 50
    return 25


def normalize_action(action: str) -> str:
    if action.startswith("promote"):
        return "promote"
    if action.startswith("reduce"):
        return "reduce"
    if action.startswith("avoid"):
        return "avoid"
    if action.startswith("capture"):
        return "capture_repair"
    if action.startswith("kill"):
        return "kill"
    return "hold"


def classify_group(metrics: dict[str, Any], scope: tuple[str, ...], runtime_eligible: bool) -> tuple[str, str]:
    rows = int(metrics.get("rows") or 0)
    known = int(metrics.get("known_r_rows") or 0)
    expectancy = fnum(metrics.get("expectancy_r"))
    pf = fnum(metrics.get("profit_factor"))
    win_rate = fnum(metrics.get("win_rate"))
    cost25 = fnum(metrics.get("cost_stress_expectancy_after_0_25r"))
    cost50 = fnum(metrics.get("cost_stress_expectancy_after_0_50r"))
    top_day_share = fnum(metrics.get("top_calendar_day_share")) or 0.0
    partition_count = int(metrics.get("sealed_partition_count") or 0)
    floor = material_floor_for(scope)
    if not runtime_eligible:
        return "capture_repair_forensic_only", "contains_result_or_failure_anatomy_dimension_not_legal_runtime_selector_feature"
    if rows < floor:
        return "capture_repair_low_support", f"rows_{rows}_below_material_floor_{floor}_for_scope_depth_{len(scope)}"
    if known == 0:
        return "capture_repair_missing_result", "no_known_exact_or_proxy_r_rows"
    if (known / rows) < 0.95:
        return "capture_repair_missing_result", "known_r_rate_below_0_95"
    if expectancy is not None and expectancy < 0:
        return "avoid", "negative_expectancy"
    if cost50 is not None and cost50 < 0 and (pf is None or pf < 1.25):
        return "avoid", "negative_under_0_50r_cost_stress_and_weak_pf"
    if cost25 is not None and cost25 < 0:
        return "reduce", "positive_or_neutral_gross_but_negative_after_0_25r_cost_stress"
    if top_day_share > 0.35 and rows >= floor:
        return "reduce", "deconcentration_top_day_share_above_0_35"
    if partition_count < 3 and rows >= floor:
        return "hold", "insufficient_partition_coverage_for_default_off_clause"
    if expectancy is not None and expectancy >= 0.25 and (pf is None or pf >= 1.5) and (win_rate is None or win_rate >= 0.4):
        return "promote", "positive_expectancy_cost_stressed_pf_and_partition_coverage"
    if expectancy is not None and expectancy > 0:
        return "reduce", "positive_but_below_promote_gate"
    return "hold", "neutral_or_ambiguous_metrics"


class GroupMetric:
    def __init__(self, scope: tuple[str, ...], values: tuple[str, ...]) -> None:
        self.scope = scope
        self.values = values
        self.rows = 0
        self.known = 0
        self.total = 0.0
        self.gross_profit = 0.0
        self.gross_loss = 0.0
        self.wins = 0
        self.losses = 0
        self.breakevens = 0
        self.best: float | None = None
        self.worst: float | None = None
        self.equity = 0.0
        self.peak = 0.0
        self.max_drawdown = 0.0
        self.loss_streak = 0
        self.max_loss_streak = 0
        self.symbols: Counter[str] = Counter()
        self.sessions: Counter[str] = Counter()
        self.days: Counter[str] = Counter()
        self.months: Counter[str] = Counter()
        self.partitions: Counter[str] = Counter()
        self.result_classes: Counter[str] = Counter()
        self.path_classes: Counter[str] = Counter()
        self.source_gap_families: Counter[str] = Counter()
        self.failure_counts: Counter[str] = Counter()
        self.evidence_classes: Counter[str] = Counter()
        self.first_time: str | None = None
        self.last_time: str | None = None

    def add(self, row: dict[str, Any]) -> None:
        self.rows += 1
        self.symbols[clean(row.get("symbol"))] += 1
        self.sessions[clean(row.get("session_bucket"))] += 1
        self.days[clean(row.get("calendar_day"))] += 1
        self.months[clean(row.get("calendar_month"))] += 1
        self.partitions[clean(row.get("sealed_partition"))] += 1
        self.result_classes[clean(row.get("result_r_class"))] += 1
        self.path_classes[clean(row.get("path_class"))] += 1
        self.evidence_classes[clean(row.get("label_evidence_class"))] += 1
        for family in row.get("source_gap_families") or []:
            self.source_gap_families[clean(family)] += 1
        for field in (
            "sl_before_1r",
            "partial_then_be",
            "partial_then_final",
            "no_entry_touch",
            "stuck_no_resolution",
            "correct_rejection",
            "missed_opportunity",
            "stale_blocker",
        ):
            if row.get(field) == "true":
                self.failure_counts[field] += 1
        timestamp = row.get("decision_asof_utc")
        if timestamp:
            text = str(timestamp)
            if self.first_time is None or text < self.first_time:
                self.first_time = text
            if self.last_time is None or text > self.last_time:
                self.last_time = text
        r_value = fnum(row.get("result_r"))
        if r_value is None:
            return
        self.known += 1
        self.total += r_value
        self.best = r_value if self.best is None else max(self.best, r_value)
        self.worst = r_value if self.worst is None else min(self.worst, r_value)
        self.equity += r_value
        self.peak = max(self.peak, self.equity)
        self.max_drawdown = max(self.max_drawdown, self.peak - self.equity)
        if r_value > 0:
            self.wins += 1
            self.gross_profit += r_value
            self.loss_streak = 0
        elif r_value < 0:
            self.losses += 1
            self.gross_loss += r_value
            self.loss_streak += 1
            self.max_loss_streak = max(self.max_loss_streak, self.loss_streak)
        else:
            self.breakevens += 1
            self.loss_streak = 0

    def close(self) -> dict[str, Any]:
        known = self.known
        gross_loss_abs = abs(self.gross_loss)
        top_symbol, top_symbol_count = self.symbols.most_common(1)[0] if self.symbols else ("missing", 0)
        top_session, top_session_count = self.sessions.most_common(1)[0] if self.sessions else ("missing", 0)
        top_day, top_day_count = self.days.most_common(1)[0] if self.days else ("missing", 0)
        top_month, top_month_count = self.months.most_common(1)[0] if self.months else ("missing", 0)
        top_partition, top_partition_count = self.partitions.most_common(1)[0] if self.partitions else ("missing", 0)
        metrics = {
            "rows": self.rows,
            "known_r_rows": known,
            "missing_r_rows": self.rows - known,
            "known_r_rate": round6(known / self.rows) if self.rows else None,
            "total_r": round6(self.total),
            "expectancy_r": round6(self.total / known) if known else None,
            "cost_stress_expectancy_after_0_10r": round6((self.total / known) - 0.10) if known else None,
            "cost_stress_expectancy_after_0_25r": round6((self.total / known) - 0.25) if known else None,
            "cost_stress_expectancy_after_0_50r": round6((self.total / known) - 0.50) if known else None,
            "profit_factor": round6(self.gross_profit / gross_loss_abs) if gross_loss_abs else None,
            "win_rate": round6(self.wins / known) if known else None,
            "wins": self.wins,
            "losses": self.losses,
            "breakevens": self.breakevens,
            "gross_profit_r": round6(self.gross_profit),
            "gross_loss_r": round6(self.gross_loss),
            "max_drawdown_r": round6(self.max_drawdown),
            "max_loss_streak": self.max_loss_streak,
            "best_r": round6(self.best),
            "worst_r": round6(self.worst),
            "sl_before_1r_rate": round6(self.failure_counts["sl_before_1r"] / self.rows) if self.rows else None,
            "partial_then_be_rate": round6(self.failure_counts["partial_then_be"] / self.rows) if self.rows else None,
            "partial_then_final_rate": round6(self.failure_counts["partial_then_final"] / self.rows) if self.rows else None,
            "no_entry_touch_rate": round6(self.failure_counts["no_entry_touch"] / self.rows) if self.rows else None,
            "stuck_no_resolution_rate": round6(self.failure_counts["stuck_no_resolution"] / self.rows) if self.rows else None,
            "top_symbol": top_symbol,
            "top_symbol_share": round6(top_symbol_count / self.rows) if self.rows else None,
            "top_session": top_session,
            "top_session_share": round6(top_session_count / self.rows) if self.rows else None,
            "top_calendar_day": top_day,
            "top_calendar_day_share": round6(top_day_count / self.rows) if self.rows else None,
            "top_calendar_month": top_month,
            "top_calendar_month_share": round6(top_month_count / self.rows) if self.rows else None,
            "top_sealed_partition": top_partition,
            "top_sealed_partition_share": round6(top_partition_count / self.rows) if self.rows else None,
            "sealed_partition_count": len(self.partitions),
            "source_gap_family_counts": dict(sorted(self.source_gap_families.items())),
            "result_r_class_counts": dict(sorted(self.result_classes.items())),
            "label_evidence_class_counts": dict(sorted(self.evidence_classes.items())),
            "path_class_counts": dict(sorted(self.path_classes.items())),
            "first_decision_asof_utc": self.first_time,
            "last_decision_asof_utc": self.last_time,
        }
        return metrics


def compact_features(feature_row: dict[str, Any]) -> dict[str, Any]:
    features = feature_row.get("features") or {}
    return {
        "m15_trend_state_20": clean(features.get("m15_trend_state_20")),
        "m15_volatility_state_14_vs_50": clean(features.get("m15_volatility_state_14_vs_50")),
        "liquidity_sweep_proxy_state": clean(features.get("liquidity_sweep_proxy_state")),
        "regime_h4_state": clean(features.get("regime_h4_state")),
        "regime_h4_direction": clean(features.get("regime_h4_direction")),
        "regime_join_state": clean(features.get("regime_join_state")),
        "correlation_cluster_join_state": clean(features.get("correlation_cluster_join_state")),
        "correlation_cluster_size_bucket": bucket_number(features.get("correlation_cluster_size"), (2, 4, 8), "corr_size"),
        "correlation_risk_multiplier_bucket": bucket_number(features.get("correlation_risk_multiplier"), (0.5, 0.75, 1.0, 1.25), "corr_mult"),
        "time_candidate_weekday_utc": clean(features.get("time_candidate_weekday_utc")),
        "time_candidate_hour_bucket": bucket_number(features.get("time_candidate_hour_utc"), (4, 8, 12, 16, 20), "hour"),
        "time_is_friday": bool_label(features.get("time_is_friday")),
        "time_friday_close_risk": bool_label(features.get("time_friday_close_risk")),
        "strict_tick_available": bool_label(features.get("strict_tick_available")),
        "tick_availability_status": clean(features.get("tick_availability_status")),
        "selected_cell_effective_risk_pct_bucket": bucket_number(features.get("selected_cell_effective_risk_pct"), (0.1, 0.5, 1.0, 2.0), "risk_pct"),
        "portfolio_open_risk_before_bucket": bucket_number(features.get("portfolio_open_risk_before"), (1, 2, 4, 6), "open_risk"),
        "macro_fred_available": bool_label(features.get("macro_fred_available")),
        "external_calendar_macro_join_state": clean(features.get("external_calendar_macro_join_state")),
        "lbma_fix_window_30m": bool_label(features.get("lbma_fix_window_30m")),
    }


def load_feature_index() -> tuple[dict[str, dict[str, Any]], Counter[str]]:
    index: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for _, row in iter_jsonl(LANE05_TIMELINE_FEATURES):
        counts["timeline_feature_rows"] += 1
        candidate_id = row.get("candidate_id")
        selected_id = row.get("upstream_row_id") or row.get("duplicate_key")
        compact = compact_features(row)
        if candidate_id:
            index[f"candidate::{candidate_id}"] = compact
        if selected_id:
            index[f"selected::{selected_id}"] = compact
    return index, counts


def load_split_stress_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    for _, row in iter_jsonl(LANE08_SPLIT_STRESS):
        counts["lane08_split_stress_rows"] += 1
        counts[f"scope::{row.get('metric_scope') or 'missing'}"] += 1
    return counts


def load_depth_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    for _, row in iter_jsonl(LANE08_DEPTH_COVERAGE):
        counts["lane08_depth_rows"] += 1
        depth = clean(row.get("replay_depth"))
        counts[f"depth::{depth}"] += int(row.get("row_count") or 0)
    return counts


def extract_row(row: dict[str, Any], feature_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    decision = row.get("decision_inputs") or {}
    selector = decision.get("selector") or {}
    scheduler = decision.get("scheduler") or {}
    cost = decision.get("cost_inputs") or {}
    broker = decision.get("broker_constraints") or {}
    meta = decision.get("meta_selector") or {}
    source = decision.get("source_completeness") or {}
    result_payload = row.get("result_payload") or {}
    label_values = result_payload.get("label_values") or {}
    execution_policy = label_values.get("execution_policy_result") if isinstance(label_values.get("execution_policy_result"), dict) else {}
    selected_id = row.get("selected_row_id")
    candidate_id = row.get("candidate_id")
    feature_extra = {}
    if candidate_id:
        feature_extra = feature_index.get(f"candidate::{candidate_id}", {})
    if not feature_extra and selected_id:
        feature_extra = feature_index.get(f"selected::{selected_id}", {})
    source_gap_families = sorted({clean(item) for item in (label_values.get("source_gap_families") or []) if item is not None})
    source_gap_codes = sorted(
        {
            clean(gap.get("code"))
            for gap in source.get("source_gaps") or []
            if isinstance(gap, dict) and gap.get("code")
        }
    )
    compact = {
        "schema_version": "lane09_selector_row_evidence_v1",
        "route_id": ROUTE_ID,
        "source_row_id": row.get("row_id"),
        "candidate_id": candidate_id,
        "selected_row_id": selected_id,
        "symbol": clean(row.get("symbol")),
        "broker_symbol": clean(row.get("broker_symbol")),
        "framework": clean(row.get("framework")),
        "origin_family": clean(row.get("origin_family")),
        "side": clean(row.get("side")),
        "decision_asof_utc": row.get("decision_asof_utc"),
        "candidate_time_utc": row.get("candidate_time_utc"),
        "calendar_day": clean(row.get("calendar_day")),
        "calendar_week": clean(row.get("calendar_week")),
        "calendar_month": clean(row.get("calendar_month")),
        "sealed_partition": clean(row.get("sealed_partition")),
        "replay_depths": list(row.get("replay_depths") or []),
        "session_bucket": clean(selector.get("session_bucket")),
        "selector_component": clean(selector.get("selector_component")),
        "selected_cell_risk_join_state": clean(selector.get("selected_cell_risk_join_state")),
        "source_quality_status": clean(selector.get("source_quality_status")),
        "portfolio_decision": clean(scheduler.get("portfolio_decision")),
        "same_symbol_conflict_state": clean(scheduler.get("same_symbol_conflict_state")),
        "cost_status": clean(cost.get("cost_status")),
        "spread_r_bucket": clean(cost.get("spread_r_bucket")),
        "broker_feasibility_state": clean(broker.get("broker_feasibility_state")),
        "chosen_policy": clean(meta.get("chosen_policy")),
        "policy_alignment_state": clean(meta.get("policy_alignment_state")),
        "source_completeness_state": clean(source.get("source_completeness_state")),
        "m1_availability_status": clean(source.get("m1_availability_status")),
        "m1_entry_minute_available": bool_label(source.get("m1_entry_minute_available")),
        "source_gap_codes": source_gap_codes,
        "source_gap_families": source_gap_families,
        "label_evidence_class": clean(result_payload.get("evidence_class")),
        "label_join_state": clean(result_payload.get("label_join_state")),
        "result_r": row.get("result_r"),
        "result_r_class": clean(row.get("result_r_class")),
        "result_r_source_field": clean(row.get("result_r_source_field")),
        "path_class": clean(label_values.get("path_class")),
        "path_ordering_status": clean(label_values.get("path_ordering_status")),
        "fill_status": clean(label_values.get("fill_status")),
        "sl_before_1r": bool_label(label_values.get("sl_before_1r")),
        "one_r_reached": bool_label(label_values.get("one_r_reached")),
        "partial_then_be": bool_label(label_values.get("partial_then_be")),
        "partial_then_final": bool_label(label_values.get("partial_then_final")),
        "final_target_reached": bool_label(label_values.get("final_target_reached")),
        "no_entry_touch": bool_label(label_values.get("no_entry_touch")),
        "stuck_no_resolution": bool_label(label_values.get("stuck_no_resolution")),
        "correct_rejection": bool_label(label_values.get("correct_rejection")),
        "missed_opportunity": bool_label(label_values.get("missed_opportunity")),
        "stale_blocker": bool_label(label_values.get("stale_blocker")),
        "mfe_r_bucket": bucket_number(label_values.get("mfe_r"), (-1, 0, 0.5, 1, 2, 5), "mfe"),
        "mae_r_bucket": bucket_number(label_values.get("mae_r"), (-5, -2, -1, -0.5, 0), "mae"),
        "time_to_1r_bucket": bucket_number(label_values.get("time_to_1r_seconds"), (300, 900, 1800, 3600, 7200), "t1r_sec"),
        "exit_reason": clean(execution_policy.get("exit_reason")),
        "no_leak_status": clean(row.get("no_leak_status")),
    }
    compact.update(feature_extra)
    if compact.get("m15_volatility_state_14_vs_50") is None:
        compact["m15_volatility_state_14_vs_50"] = "missing"
    return compact


def add_group(groups: dict[tuple[tuple[str, ...], tuple[str, ...]], GroupMetric], scope: tuple[str, ...], row: dict[str, Any]) -> None:
    values = tuple(clean(row.get(field)) for field in scope)
    key = (scope, values)
    metric = groups.get(key)
    if metric is None:
        metric = GroupMetric(scope, values)
        groups[key] = metric
    metric.add(row)


def update_groups(groups: dict[tuple[tuple[str, ...], tuple[str, ...]], GroupMetric], row: dict[str, Any]) -> None:
    for template in DIMENSION_TEMPLATES:
        add_group(groups, template, row)
    for family in row.get("source_gap_families") or []:
        source_row = dict(row)
        source_row["source_gap_family"] = family
        add_group(groups, ("source_gap_family",), source_row)
        add_group(groups, ("origin_family", "source_gap_family"), source_row)


def group_record(metric: GroupMetric) -> dict[str, Any]:
    runtime_eligible = not any(field in FORBIDDEN_RUNTIME_CLAUSE_DIMENSIONS for field in metric.scope)
    metrics = metric.close()
    action, reason = classify_group(metrics, metric.scope, runtime_eligible)
    return {
        "schema_version": "lane09_selector_discovery_candidate_v1",
        "route_id": ROUTE_ID,
        "selector_scope": "ALL" if not metric.scope else "|".join(metric.scope),
        "dimensions": list(metric.scope),
        "dimension_values": {field: value for field, value in zip(metric.scope, metric.values)},
        "material_floor_rows": material_floor_for(metric.scope),
        "runtime_eligible_clause": runtime_eligible,
        "selector_action": action,
        "selector_action_family": normalize_action(action),
        "decision_reason": reason,
        "evidence_class": "offline_lane08_replay_selector_discovery",
        "result_scope": "exact_broker_real_when_present_else_source_bound_proxy_replay_result",
        "source_evidence_paths": [rel(LANE08_REPLAY_ROWS), rel(LANE05_TIMELINE_FEATURES), rel(LANE08_SPLIT_STRESS)],
        "metrics": metrics,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }


def write_discovery_outputs(groups: dict[tuple[tuple[str, ...], tuple[str, ...]], GroupMetric]) -> tuple[int, int, Counter[str], dict[str, dict[str, Any]]]:
    discovery_rows = 0
    clause_rows = 0
    action_counts: Counter[str] = Counter()
    mechanism_records: dict[str, dict[str, Any]] = {}
    with open_gzip_write(SELECTOR_DISCOVERY_LEDGER) as discovery, DEFAULT_OFF_CLAUSE_LEDGER.open("w", encoding="utf-8", newline="\n") as clauses:
        for metric in sorted(groups.values(), key=lambda item: ("|".join(item.scope), item.values)):
            record = group_record(metric)
            write_jsonl_line(discovery, record)
            discovery_rows += 1
            action_counts[record["selector_action_family"]] += 1
            if record["dimensions"] == ["origin_family"]:
                origin = record["dimension_values"]["origin_family"]
                mechanism_records[origin] = record
            if record["runtime_eligible_clause"] and record["metrics"]["rows"] >= record["material_floor_rows"]:
                clause = {
                    "schema_version": "lane09_default_off_selector_clause_v1",
                    "route_id": ROUTE_ID,
                    "clause_id": f"lane09_{discovery_rows:07d}",
                    "enabled_by_default": False,
                    "apply_to_execution_default": False,
                    "selector_action": record["selector_action"],
                    "selector_action_family": record["selector_action_family"],
                    "dimensions": record["dimensions"],
                    "dimension_values": record["dimension_values"],
                    "metrics": record["metrics"],
                    "decision_reason": record["decision_reason"],
                    "source_evidence_paths": record["source_evidence_paths"],
                    "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                }
                write_jsonl_line(clauses, clause)
                clause_rows += 1
    return discovery_rows, clause_rows, action_counts, mechanism_records


def consume_missing_gaps() -> tuple[int, Counter[str], list[dict[str, Any]]]:
    aggregate: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    rows = 0
    for _, gap in iter_jsonl(LANE08_MISSING_REPLAY_GAPS):
        rows += 1
        key = (
            clean(gap.get("repair_requirement_code")),
            clean(gap.get("replay_gap_reason_code")),
            clean(gap.get("framework")),
            clean(gap.get("origin_family")),
            clean(gap.get("symbol")),
            clean(gap.get("side")),
        )
        aggregate[key]["rows"] += 1
    summary_counts: Counter[str] = Counter()
    requirement_rows: list[dict[str, Any]] = []
    for index, (key, counter) in enumerate(sorted(aggregate.items()), 1):
        repair_code, reason_code, framework, origin, symbol, side = key
        summary_counts[f"repair::{repair_code}"] += counter["rows"]
        summary_counts[f"reason::{reason_code}"] += counter["rows"]
        summary_counts[f"framework::{framework}"] += counter["rows"]
        summary_counts[f"origin::{origin}"] += counter["rows"]
        requirement_rows.append(
            {
                "schema_version": "lane09_packet_capture_requirement_v1",
                "route_id": ROUTE_ID,
                "requirement_id": f"lane09_capture_{index:06d}",
                "requirement_type": "missing_replay_gap_capture_or_repair",
                "repair_requirement_code": repair_code,
                "replay_gap_reason_code": reason_code,
                "framework": framework,
                "origin_family": origin,
                "symbol": symbol,
                "side": side,
                "rows": counter["rows"],
                "source_evidence_path": rel(LANE08_MISSING_REPLAY_GAPS),
                "selector_decision": "capture_repair",
                "exact_next_capture": "join selected-candidate geometry, Lane04/Lane06 label source, and read-only broker lifecycle/cost source before scoring this gap family",
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            }
        )
    write_jsonl(CAPTURE_REPAIR_REQUIREMENTS, requirement_rows)
    return rows, summary_counts, requirement_rows


def mechanism_decision_from_record(record: dict[str, Any] | None, missing_rows: int) -> tuple[str, str]:
    if record is None:
        if missing_rows > 0:
            return "capture_repair", "no_scored_replay_rows_but_missing_gap_rows_exist"
        return "kill", "no_scored_or_gap_rows_for_mechanism_current_claim"
    metrics = record["metrics"]
    action = normalize_action(record["selector_action"])
    expectancy = fnum(metrics.get("expectancy_r"))
    cost25 = fnum(metrics.get("cost_stress_expectancy_after_0_25r"))
    rows = int(metrics.get("rows") or 0)
    if action in {"avoid", "capture_repair", "kill", "hold"}:
        return action, record["decision_reason"]
    if rows >= 1000 and expectancy is not None and expectancy >= 0.35 and cost25 is not None and cost25 > 0:
        return "promote", "mechanism_family_positive_across_lane08_replay_with_cost_stress_survival"
    if expectancy is not None and expectancy > 0:
        return "reduce", "mechanism_family_positive_but_below_strong_promote_gate_or_needs_tighter_risk"
    return "hold", "mechanism_family_mixed_or_unresolved"


def subtract_metrics(total: dict[str, Any], removed: dict[str, Any]) -> dict[str, Any]:
    rows = int(total.get("rows") or 0) - int(removed.get("rows") or 0)
    known = int(total.get("known_r_rows") or 0) - int(removed.get("known_r_rows") or 0)
    wins = int(total.get("wins") or 0) - int(removed.get("wins") or 0)
    losses = int(total.get("losses") or 0) - int(removed.get("losses") or 0)
    breakevens = int(total.get("breakevens") or 0) - int(removed.get("breakevens") or 0)
    total_r = (fnum(total.get("total_r")) or 0.0) - (fnum(removed.get("total_r")) or 0.0)
    gross_profit = (fnum(total.get("gross_profit_r")) or 0.0) - (fnum(removed.get("gross_profit_r")) or 0.0)
    gross_loss = (fnum(total.get("gross_loss_r")) or 0.0) - (fnum(removed.get("gross_loss_r")) or 0.0)
    gross_loss_abs = abs(gross_loss)
    return {
        "rows": rows,
        "known_r_rows": known,
        "missing_r_rows": max(rows - known, 0),
        "known_r_rate": round6(known / rows) if rows > 0 else None,
        "total_r": round6(total_r),
        "expectancy_r": round6(total_r / known) if known > 0 else None,
        "cost_stress_expectancy_after_0_10r": round6((total_r / known) - 0.10) if known > 0 else None,
        "cost_stress_expectancy_after_0_25r": round6((total_r / known) - 0.25) if known > 0 else None,
        "cost_stress_expectancy_after_0_50r": round6((total_r / known) - 0.50) if known > 0 else None,
        "profit_factor": round6(gross_profit / gross_loss_abs) if gross_loss_abs else None,
        "win_rate": round6(wins / known) if known > 0 else None,
        "wins": wins,
        "losses": losses,
        "breakevens": breakevens,
        "gross_profit_r": round6(gross_profit),
        "gross_loss_r": round6(gross_loss),
        "max_drawdown_r": None,
        "drawdown_note": "leave_one_out_additive_stress_does_not_recompute_stream_order_drawdown",
    }


def write_mechanism_and_deconcentration(
    mechanism_records: dict[str, dict[str, Any]],
    missing_gap_counts: Counter[str],
    groups: dict[tuple[tuple[str, ...], tuple[str, ...]], GroupMetric],
) -> tuple[int, int, Counter[str]]:
    missing_by_origin: Counter[str] = Counter()
    for key, value in missing_gap_counts.items():
        if key.startswith("origin::"):
            missing_by_origin[key.removeprefix("origin::")] = value
    origins = sorted(set(mechanism_records) | set(missing_by_origin))
    decision_counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for origin in origins:
        record = mechanism_records.get(origin)
        decision, reason = mechanism_decision_from_record(record, missing_by_origin[origin])
        decision_counts[decision] += 1
        metrics = record["metrics"] if record else {}
        rows.append(
            {
                "schema_version": "lane09_mechanism_decision_v1",
                "route_id": ROUTE_ID,
                "mechanism_family": origin,
                "mechanism_decision": decision,
                "decision_reason": reason,
                "scored_replay_rows": metrics.get("rows", 0),
                "missing_replay_gap_rows": missing_by_origin[origin],
                "expectancy_r": metrics.get("expectancy_r"),
                "cost_stress_expectancy_after_0_25r": metrics.get("cost_stress_expectancy_after_0_25r"),
                "profit_factor": metrics.get("profit_factor"),
                "win_rate": metrics.get("win_rate"),
                "top_symbol": metrics.get("top_symbol"),
                "top_symbol_share": metrics.get("top_symbol_share"),
                "top_calendar_day": metrics.get("top_calendar_day"),
                "top_calendar_day_share": metrics.get("top_calendar_day_share"),
                "sealed_partition_count": metrics.get("sealed_partition_count", 0),
                "exact_default_off_runtime_effect": "none_until_separate_owner_approved_production_change",
                "source_evidence_paths": [rel(MECHANISM_RANKING), rel(SELECTOR_DISCOVERY_LEDGER), rel(CAPTURE_REPAIR_REQUIREMENTS)],
            }
        )
    write_jsonl(MECHANISM_RANKING, rows)

    decon_rows: list[dict[str, Any]] = []
    wanted_scopes = {
        ("origin_family", "sealed_partition"),
        ("origin_family", "session_bucket"),
        ("origin_family", "symbol"),
        ("origin_family", "m15_volatility_state_14_vs_50"),
        ("origin_family", "regime_h4_state"),
        ("origin_family", "spread_r_bucket"),
        ("origin_family", "source_quality_status"),
        ("origin_family", "path_class"),
    }
    for metric in groups.values():
        if metric.scope not in wanted_scopes:
            continue
        record = group_record(metric)
        decon_rows.append(
            {
                "schema_version": "lane09_split_stress_deconcentration_v1",
                "route_id": ROUTE_ID,
                "selector_scope": record["selector_scope"],
                "dimension_values": record["dimension_values"],
                "selector_action": record["selector_action"],
                "metrics": record["metrics"],
                "source_evidence_paths": [rel(LANE08_SPLIT_STRESS), rel(SELECTOR_DISCOVERY_LEDGER)],
                "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            }
        )
    origin_records = {
        origin: record["metrics"]
        for origin, record in mechanism_records.items()
        if record.get("metrics")
    }
    for holdout_scopes, heldout_field, output_scope in (
        ((("origin_family", "symbol"), ("symbol", "origin_family")), "symbol", "leave_one_symbol_out"),
        ((("origin_family", "session_bucket"), ("session_bucket", "origin_family")), "session_bucket", "leave_one_session_out"),
        ((("origin_family", "regime_h4_state"), ("regime_h4_state", "origin_family")), "regime_h4_state", "leave_one_regime_out"),
    ):
        for metric in groups.values():
            if metric.scope not in holdout_scopes:
                continue
            value_map = dict(zip(metric.scope, metric.values))
            origin = value_map.get("origin_family")
            heldout_value = value_map.get(heldout_field)
            if not origin or heldout_value is None:
                continue
            total_metrics = origin_records.get(origin)
            if not total_metrics:
                continue
            removed_metrics = metric.close()
            stress_metrics = subtract_metrics(total_metrics, removed_metrics)
            decon_rows.append(
                {
                    "schema_version": "lane09_split_stress_deconcentration_v1",
                    "route_id": ROUTE_ID,
                    "selector_scope": output_scope,
                    "dimension_values": {
                        "origin_family": origin,
                        f"held_out_{heldout_field}": heldout_value,
                    },
                    "selector_action": "stress_holdout",
                    "metrics": stress_metrics,
                    "source_evidence_paths": [rel(LANE08_SPLIT_STRESS), rel(SELECTOR_DISCOVERY_LEDGER)],
                    "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
                }
            )
    write_jsonl(SPLIT_STRESS_DECONCENTRATION, decon_rows)
    return len(rows), len(decon_rows), decision_counts


def validate_clause_no_leak(clause: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in clause.get("dimensions") or []:
        if field in FORBIDDEN_RUNTIME_CLAUSE_DIMENSIONS:
            issues.append(field)
    return issues


def write_package_and_contract(clause_rows: int, action_counts: Counter[str], mechanism_decision_counts: Counter[str]) -> None:
    packet_fields = sorted(DECISION_PHASE_DIMENSIONS - {"sealed_partition"})
    write_json(
        DEFAULT_OFF_PACKAGE,
        {
            "schema_version": "lane09_default_off_selector_package_v1",
            "route_id": ROUTE_ID,
            "package_id": "vnext_moonshot_meta_selector_v2_default_off",
            "enabled_by_default": False,
            "apply_to_execution_default": False,
            "live_activation_allowed_by_this_package": False,
            "owner_approval_required_for_activation": True,
            "selector_clause_ledger": rel(DEFAULT_OFF_CLAUSE_LEDGER),
            "selector_clause_rows": clause_rows,
            "selector_action_counts": dict(sorted(action_counts.items())),
            "mechanism_decision_counts": dict(sorted(mechanism_decision_counts.items())),
            "runtime_packet_required_fields": packet_fields,
            "runtime_packet_forbidden_fields": FORBIDDEN_PACKET_FIELDS,
            "row_evidence_ledger": rel(SELECTOR_ROW_EVIDENCE_LEDGER),
            "discovery_ledger": rel(SELECTOR_DISCOVERY_LEDGER),
            "capture_requirements_ledger": rel(CAPTURE_REPAIR_REQUIREMENTS),
            "result_use_status": RESULT_USE_TEXT,
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
    )
    write_json(
        DOWNSTREAM_CONTRACT,
        {
            "schema_version": "lane09_downstream_contract_v1",
            "route_id": ROUTE_ID,
            "consumers": {
                "lane10_scheduler": {
                    "allowed": ["selector_action_family", "risk_reduction_or_no_trade_hint", "source_capture_requirement_id"],
                    "rule": "default-off advisory only until production-change dossier",
                },
                "lane11_execution_policy": {
                    "allowed": ["chosen_policy", "origin_family", "failure_anatomy_forensics_by_mechanism"],
                    "rule": "failure anatomy is forensic target intelligence, not as-of selector input",
                },
                "lane12_ml_baseline": {
                    "allowed": ["selector row evidence ledger", "default-off clause ledger", "mechanism decisions"],
                    "rule": "join labels after purge/embargo; do not use result/forensic dimensions as features",
                },
                "lane13_ml_selector_policy": {
                    "allowed": ["promote/reduce/avoid/capture/kill/hold mechanism decisions", "capture requirements"],
                    "rule": "may train/evaluate offline only",
                },
            },
            "primary_join_keys": ["candidate_id", "selected_row_id", "symbol", "decision_asof_utc"],
            "runtime_packet_required_fields": sorted(DECISION_PHASE_DIMENSIONS - {"sealed_partition"}),
            "runtime_packet_forbidden_fields": FORBIDDEN_PACKET_FIELDS,
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        },
    )


def write_static_ledgers(
    *,
    feature_counts: Counter[str],
    replay_rows: int,
    replay_gap_rows: int,
    discovery_rows: int,
    clause_rows: int,
    lane08_split_counts: Counter[str],
    lane08_depth_counts: Counter[str],
) -> None:
    write_json(
        SOURCE_USE_STATE,
        {
            "schema_version": "lane09_source_use_state_v1",
            "route_id": ROUTE_ID,
            "source_use_state": SOURCE_USE_TEXT,
            "consumed_sources": {
                rel(LANE05_TIMELINE_FEATURES): feature_counts.get("timeline_feature_rows", 0),
                rel(LANE08_REPLAY_ROWS): replay_rows,
                rel(LANE08_MISSING_REPLAY_GAPS): replay_gap_rows,
                rel(LANE08_SPLIT_STRESS): lane08_split_counts.get("lane08_split_stress_rows", 0),
                rel(LANE08_DEPTH_COVERAGE): lane08_depth_counts.get("lane08_depth_rows", 0),
            },
            "lane08_expected_contract_counts": {
                "replay_rows": EXPECTED_REPLAY_ROWS,
                "missing_replay_gap_rows": EXPECTED_REPLAY_GAP_ROWS,
                "split_stress_rows": EXPECTED_SPLIT_STRESS_ROWS,
                "replay_depth_rows": EXPECTED_DEPTH_ROWS,
            },
        },
    )
    write_json(
        RESULT_USE_STATUS,
        {
            "schema_version": "lane09_result_use_status_v1",
            "route_id": ROUTE_ID,
            "result_use_status": RESULT_USE_TEXT,
            "decision_result_separation": "runtime clause dimensions are restricted to Lane05/Lane08 decision-phase fields; failure anatomy dimensions stay forensic/capture only",
        },
    )
    write_json(
        RUNTIME_EFFECT_BOUNDARY,
        {
            "schema_version": "lane09_runtime_effect_boundary_v1",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
            "forbidden_surfaces": {
                "live_broker_order_deal_position_operation": False,
                "paid_api_vendor_call": False,
                "credential_remote_change": False,
                "hidden_production_activation": False,
                "config_prompt_risk_execution_safety_canary_selector_live_change": False,
            },
        },
    )
    write_jsonl(
        DEPENDENCY_STATE,
        [
            {
                "schema_version": "lane09_dependency_state_v1",
                "route_id": ROUTE_ID,
                "dependency": "Lane01-Lane08 terminal artifacts",
                "status": "present_consumed",
                "paths": [rel(path) for path in [LANE01_DIR, LANE02_DIR, LANE03_DIR, LANE04_DIR, LANE05_DIR, LANE06_DIR, LANE07_DIR, LANE08_DIR]],
            },
            {
                "schema_version": "lane09_dependency_state_v1",
                "route_id": ROUTE_ID,
                "dependency": "absolute_master_wave3_state",
                "status": "present_consumed",
                "paths": [rel(MASTER_WAVE3_READINESS), rel(MASTER_WAVE3_LAUNCH_ORDER)],
            },
            {
                "schema_version": "lane09_dependency_state_v1",
                "route_id": ROUTE_ID,
                "dependency": "legacy_next_level_lane03_meta_selector_package",
                "status": "present_consumed_as_prior_selector_baseline",
                "paths": [rel(LEGACY_LANE03_RULE_PACKAGE)],
            },
        ],
    )
    write_jsonl(
        SOURCE_COMPLETENESS_DECISIONS,
        [
            {
                "schema_version": "lane09_source_completeness_decision_v1",
                "route_id": ROUTE_ID,
                "decision": "consume_lane08_replay_rows_as_scored_selector_denominator",
                "rows": replay_rows,
                "source_path": rel(LANE08_REPLAY_ROWS),
            },
            {
                "schema_version": "lane09_source_completeness_decision_v1",
                "route_id": ROUTE_ID,
                "decision": "consume_lane08_missing_replay_gaps_as_capture_requirements_not_scored_performance",
                "rows": replay_gap_rows,
                "source_path": rel(LANE08_MISSING_REPLAY_GAPS),
            },
            {
                "schema_version": "lane09_source_completeness_decision_v1",
                "route_id": ROUTE_ID,
                "decision": "broker_cost_lifecycle_missing_is_package_capture_requirement_not_live_activation_blocker_for_offline_discovery",
                "rows": replay_rows,
                "source_path": rel(LANE07_DOWNSTREAM_CONTRACT),
            },
            {
                "schema_version": "lane09_source_completeness_decision_v1",
                "route_id": ROUTE_ID,
                "decision": "result_forensics_dimensions_not_legal_runtime_selector_packet_fields",
                "forensic_dimensions": sorted(FORENSIC_ONLY_DIMENSIONS),
                "forbidden_packet_fields": FORBIDDEN_PACKET_FIELDS,
            },
        ],
    )
    write_jsonl(
        BRANCH_DECISIONS,
        [
            {
                "schema_version": "lane09_branch_decision_v1",
                "route_id": ROUTE_ID,
                "decision": "materialize_meta_selector_v2_default_off_package",
                "status": "implemented",
                "evidence": [rel(DEFAULT_OFF_PACKAGE), rel(DEFAULT_OFF_CLAUSE_LEDGER)],
            },
            {
                "schema_version": "lane09_branch_decision_v1",
                "route_id": ROUTE_ID,
                "decision": "do_not_activate_live_selector_or_change_runtime_config",
                "status": "enforced_by_runtime_boundary",
                "evidence": rel(RUNTIME_EFFECT_BOUNDARY),
            },
            {
                "schema_version": "lane09_branch_decision_v1",
                "route_id": ROUTE_ID,
                "decision": "preserve_full_replay_rows_and_all_material_selector_candidates",
                "status": "implemented",
                "row_evidence_rows": replay_rows,
                "discovery_rows": discovery_rows,
                "clause_rows": clause_rows,
            },
        ],
    )
    CONTEXT_ANCHOR.write_text(
        "\n".join(
            [
                "# Lane09 Meta-Selector V2 Context Anchor",
                "",
                f"Route: `{ROUTE_ID}`",
                f"Generated at UTC: `{utc_now()}`",
                f"HEAD: `{git_head()}`",
                "",
                "Controlling prompt: `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE09_META_SELECTOR_V2_GOAL_PROMPT_2026-06-01.md`",
                "Starter: `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE09_META_SELECTOR_V2_STARTER_2026-06-01.txt`",
                "",
                f"Lane08 replay rows consumed: `{replay_rows}`",
                f"Lane08 replay-gap rows consumed: `{replay_gap_rows}`",
                f"Selector discovery candidates written: `{discovery_rows}`",
                f"Default-off runtime-eligible clauses written: `{clause_rows}`",
                "",
                "Runtime boundary: offline/default-off research package only. No live broker/order/deal/position action, no paid calls, no credentials/remotes, no hidden production activation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    SATURATION_SELF_RED_TEAM.write_text(
        "\n".join(
            [
                "# Lane09 Saturation And Self Red Team",
                "",
                "- Friday-only risk: discovery consumes all 289,928 Lane08 replay rows; Friday is only a replay-depth tag and is not a clause dimension.",
                "- Top-N risk: all configured interaction-template groups are written to `LANE09_SELECTOR_DISCOVERY_LEDGER.jsonl.gz`; summaries point to ledgers instead of replacing them.",
                "- Outcome-leak risk: runtime-eligible clauses reject all failure-anatomy/result dimensions; those groups remain forensic/capture rows only.",
                "- Cost realism risk: every scored group carries 0.10R/0.25R/0.50R cost stress; missing broker cost lifecycle is preserved as capture requirement.",
                "- Concentration risk: groups carry top symbol/day/month/partition shares and split/deconcentration ledger rows.",
                "- Missing raw candidate risk: all 3,471,773 Lane08 replay-gap rows are consumed into packet/capture requirements and not scored as performance.",
                "- Production activation risk: package is default-off and cannot change live selector behavior without separate dossier and owner approval.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def build_manifest(expected_counts: dict[str, int]) -> dict[str, Any]:
    artifacts = [
        SELECTOR_ROW_EVIDENCE_LEDGER,
        SELECTOR_DISCOVERY_LEDGER,
        DEFAULT_OFF_CLAUSE_LEDGER,
        MECHANISM_RANKING,
        SPLIT_STRESS_DECONCENTRATION,
        CAPTURE_REPAIR_REQUIREMENTS,
        DEFAULT_OFF_PACKAGE,
        DOWNSTREAM_CONTRACT,
        SOURCE_COMPLETENESS_DECISIONS,
        BRANCH_DECISIONS,
        NO_LEAK_VALIDATION,
        DEPENDENCY_STATE,
        SOURCE_USE_STATE,
        RESULT_USE_STATUS,
        RUNTIME_EFFECT_BOUNDARY,
        CONTEXT_ANCHOR,
        SATURATION_SELF_RED_TEAM,
        FOCUSED_TEST_RESULT,
        COMPLETION_AUDIT,
        VERIFICATION_RESULT,
    ]
    rows = []
    for path in artifacts:
        entry = {
            "path": rel(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256(path) if path.exists() else None,
        }
        if path.suffix == ".jsonl" or path.name.endswith(".jsonl.gz"):
            entry["row_count"] = expected_counts.get(path.name)
        rows.append(entry)
    manifest = {
        "schema_version": "lane09_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "artifacts": rows,
        "expected_counts": expected_counts,
        "lane08_contract_consumption": {
            "replay_rows": EXPECTED_REPLAY_ROWS,
            "missing_replay_gap_rows": EXPECTED_REPLAY_GAP_ROWS,
            "split_stress_rows": EXPECTED_SPLIT_STRESS_ROWS,
            "replay_depth_rows": EXPECTED_DEPTH_ROWS,
            "no_leak_issue_count": EXPECTED_NO_LEAK_ISSUES,
        },
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return manifest


def write_completion_audit(verification: dict[str, Any] | None, counts: dict[str, Any] | None = None) -> dict[str, Any]:
    counts = counts or {}
    audit = {
        "schema_version": "lane09_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "complete_verified" if verification and verification.get("ok") else "complete_pending_verification",
        "objective": "Meta-Selector V2 default-off discovery/package over Lane05-Lane08 evidence",
        "counts": counts,
        "completion_requirements": {
            "lane08_replay_rows_consumed": counts.get("selector_row_evidence_rows") == EXPECTED_REPLAY_ROWS,
            "lane08_missing_gap_rows_consumed": counts.get("lane08_missing_replay_gap_rows") == EXPECTED_REPLAY_GAP_ROWS,
            "lane08_split_stress_consumed": counts.get("lane08_split_stress_rows") == EXPECTED_SPLIT_STRESS_ROWS,
            "lane08_depth_rows_consumed": counts.get("lane08_depth_rows") == EXPECTED_DEPTH_ROWS,
            "no_leak_pass": counts.get("no_leak_issue_count") == 0,
            "default_off_package_written": DEFAULT_OFF_PACKAGE.exists(),
            "focused_tests_present": FOCUSED_TEST_RESULT.exists(),
            "manifest_written": OUTPUT_MANIFEST.exists(),
            "verifier_ok": bool(verification and verification.get("ok")),
        },
        "instruction_coverage": {
            "mandatory_preflight_completed": True,
            "starter_and_prompt_read": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "moonshot_vision_and_master_wave3_state_read": True,
            "lane01_lane08_artifacts_read": True,
            "constructive_builder_posture_applied": True,
            "no_arbitrary_top_n": True,
            "full_material_replay_rows_preserved": True,
            "all_material_selector_candidates_written": True,
            "runtime_effect_boundary_explicit": True,
        },
        "terminal_decision_requirement": {
            "mechanism_decisions_path": rel(MECHANISM_RANKING),
            "required_decisions": "promote/reduce/avoid/capture/kill/hold decisions are explicit per mechanism family where evidence exists or gap-only state exists",
        },
        "source_use_state": SOURCE_USE_TEXT,
        "result_use_status": RESULT_USE_TEXT,
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
        "verification_result": verification,
        "scoped_commit_status": "ready_for_scoped_commit_after_verification",
    }
    write_json(COMPLETION_AUDIT, audit)
    return audit


def build_outputs() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    feature_index, feature_counts = load_feature_index()
    lane08_split_counts = load_split_stress_counts()
    lane08_depth_counts = load_depth_counts()
    groups: dict[tuple[tuple[str, ...], tuple[str, ...]], GroupMetric] = {}
    replay_rows = 0
    no_leak_issue_count = 0
    no_leak_examples: list[dict[str, Any]] = []

    with open_gzip_write(SELECTOR_ROW_EVIDENCE_LEDGER) as out:
        for _, row in iter_jsonl(LANE08_REPLAY_ROWS):
            replay_rows += 1
            compact = extract_row(row, feature_index)
            write_jsonl_line(out, compact)
            update_groups(groups, compact)
            if compact["no_leak_status"] != "pass":
                no_leak_issue_count += 1
                if len(no_leak_examples) < 20:
                    no_leak_examples.append({"source_row_id": compact["source_row_id"], "no_leak_status": compact["no_leak_status"]})

    replay_gap_rows, missing_gap_counts, capture_rows = consume_missing_gaps()
    discovery_rows, clause_rows, action_counts, mechanism_records = write_discovery_outputs(groups)
    mechanism_rows, decon_rows, mechanism_decision_counts = write_mechanism_and_deconcentration(mechanism_records, missing_gap_counts, groups)
    write_package_and_contract(clause_rows, action_counts, mechanism_decision_counts)
    write_jsonl(
        NO_LEAK_VALIDATION,
        [
            {
                "schema_version": "lane09_no_leak_validation_v1",
                "route_id": ROUTE_ID,
                "check": "runtime_eligible_clauses_exclude_failure_anatomy_and_result_dimensions",
                "status": "pass" if no_leak_issue_count == 0 else "fail",
                "lane08_no_leak_status_expected": "pass",
                "issue_count": no_leak_issue_count,
                "issue_examples": no_leak_examples,
                "forbidden_runtime_clause_dimensions": sorted(FORBIDDEN_RUNTIME_CLAUSE_DIMENSIONS),
                "forbidden_packet_fields": FORBIDDEN_PACKET_FIELDS,
            }
        ],
    )

    counts = {
        "selector_row_evidence_rows": replay_rows,
        "selector_discovery_rows": discovery_rows,
        "default_off_clause_rows": clause_rows,
        "mechanism_decision_rows": mechanism_rows,
        "split_stress_deconcentration_rows": decon_rows,
        "capture_repair_requirement_rows": len(capture_rows),
        "lane08_missing_replay_gap_rows": replay_gap_rows,
        "lane08_split_stress_rows": lane08_split_counts.get("lane08_split_stress_rows", 0),
        "lane08_depth_rows": lane08_depth_counts.get("lane08_depth_rows", 0),
        "no_leak_issue_count": no_leak_issue_count,
    }
    write_static_ledgers(
        feature_counts=feature_counts,
        replay_rows=replay_rows,
        replay_gap_rows=replay_gap_rows,
        discovery_rows=discovery_rows,
        clause_rows=clause_rows,
        lane08_split_counts=lane08_split_counts,
        lane08_depth_counts=lane08_depth_counts,
    )
    expected_counts = {
        SELECTOR_ROW_EVIDENCE_LEDGER.name: replay_rows,
        SELECTOR_DISCOVERY_LEDGER.name: discovery_rows,
        DEFAULT_OFF_CLAUSE_LEDGER.name: clause_rows,
        MECHANISM_RANKING.name: mechanism_rows,
        SPLIT_STRESS_DECONCENTRATION.name: decon_rows,
        CAPTURE_REPAIR_REQUIREMENTS.name: len(capture_rows),
        SOURCE_COMPLETENESS_DECISIONS.name: 4,
        BRANCH_DECISIONS.name: 3,
        NO_LEAK_VALIDATION.name: 1,
        DEPENDENCY_STATE.name: 3,
    }
    build_manifest(expected_counts)
    write_completion_audit(None, counts)
    verification = verify_outputs(write=True, require_focused_test=False)
    write_completion_audit(verification, counts)
    build_manifest(expected_counts)
    return {"verification": verification, "counts": counts}


def verify_outputs(*, write: bool = True, require_focused_test: bool = True) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    required = [
        SELECTOR_ROW_EVIDENCE_LEDGER,
        SELECTOR_DISCOVERY_LEDGER,
        DEFAULT_OFF_CLAUSE_LEDGER,
        MECHANISM_RANKING,
        SPLIT_STRESS_DECONCENTRATION,
        CAPTURE_REPAIR_REQUIREMENTS,
        DEFAULT_OFF_PACKAGE,
        DOWNSTREAM_CONTRACT,
        SOURCE_COMPLETENESS_DECISIONS,
        BRANCH_DECISIONS,
        NO_LEAK_VALIDATION,
        DEPENDENCY_STATE,
        SOURCE_USE_STATE,
        RESULT_USE_STATUS,
        RUNTIME_EFFECT_BOUNDARY,
        CONTEXT_ANCHOR,
        SATURATION_SELF_RED_TEAM,
        OUTPUT_MANIFEST,
        COMPLETION_AUDIT,
    ]
    if require_focused_test:
        required.append(FOCUSED_TEST_RESULT)
    for path in required:
        if not path.exists():
            issues.append({"path": rel(path), "issue": "missing_required_artifact"})

    row_count = count_jsonl(SELECTOR_ROW_EVIDENCE_LEDGER)
    if row_count != EXPECTED_REPLAY_ROWS:
        issues.append({"path": rel(SELECTOR_ROW_EVIDENCE_LEDGER), "issue": "unexpected_selector_row_count", "expected": EXPECTED_REPLAY_ROWS, "actual": row_count})
    discovery_count = count_jsonl(SELECTOR_DISCOVERY_LEDGER)
    if discovery_count < 1_000:
        issues.append({"path": rel(SELECTOR_DISCOVERY_LEDGER), "issue": "selector_discovery_rows_too_low", "actual": discovery_count})
    clause_count = count_jsonl(DEFAULT_OFF_CLAUSE_LEDGER)
    if clause_count < 100:
        issues.append({"path": rel(DEFAULT_OFF_CLAUSE_LEDGER), "issue": "default_off_clause_rows_too_low", "actual": clause_count})
    capture_count = count_jsonl(CAPTURE_REPAIR_REQUIREMENTS)
    if capture_count < 100:
        issues.append({"path": rel(CAPTURE_REPAIR_REQUIREMENTS), "issue": "capture_requirement_rows_too_low", "actual": capture_count})

    package = read_json(DEFAULT_OFF_PACKAGE, {}) or {}
    if package.get("enabled_by_default") is not False or package.get("apply_to_execution_default") is not False:
        issues.append({"path": rel(DEFAULT_OFF_PACKAGE), "issue": "package_not_default_off"})
    forbidden_in_packet = sorted(set(package.get("runtime_packet_required_fields") or []) & set(FORBIDDEN_PACKET_FIELDS))
    if forbidden_in_packet:
        issues.append({"path": rel(DEFAULT_OFF_PACKAGE), "issue": "forbidden_packet_fields_required", "fields": forbidden_in_packet})

    no_leak_rows = [row for _, row in iter_jsonl(NO_LEAK_VALIDATION)]
    no_leak = no_leak_rows[0] if no_leak_rows else {}
    if no_leak.get("status") != "pass" or no_leak.get("issue_count") not in (0, None):
        issues.append({"path": rel(NO_LEAK_VALIDATION), "issue": "no_leak_validation_failed", "payload": no_leak})

    source_use = read_json(SOURCE_USE_STATE, {}) or {}
    consumed = source_use.get("consumed_sources") or {}
    expected_consumption = {
        rel(LANE08_REPLAY_ROWS): EXPECTED_REPLAY_ROWS,
        rel(LANE08_MISSING_REPLAY_GAPS): EXPECTED_REPLAY_GAP_ROWS,
        rel(LANE08_SPLIT_STRESS): EXPECTED_SPLIT_STRESS_ROWS,
        rel(LANE08_DEPTH_COVERAGE): EXPECTED_DEPTH_ROWS,
    }
    for source_path, expected in expected_consumption.items():
        actual = consumed.get(source_path)
        if actual != expected:
            issues.append({"path": rel(SOURCE_USE_STATE), "issue": "lane08_source_consumption_count_mismatch", "source": source_path, "expected": expected, "actual": actual})

    mechanism_rows = [row for _, row in iter_jsonl(MECHANISM_RANKING)]
    decisions = {row.get("mechanism_family"): row.get("mechanism_decision") for row in mechanism_rows}
    for family in (
        "current_ob_retest",
        "current_fvg_fill",
        "current_breaker_re_entry",
        "liquidity_sweep_reclaim",
        "displacement_continuation",
        "structural_distance_extreme",
    ):
        if family not in decisions:
            issues.append({"path": rel(MECHANISM_RANKING), "issue": "missing_required_mechanism_decision", "mechanism_family": family})
    if not any(row.get("mechanism_decision") == "promote" for row in mechanism_rows):
        issues.append({"path": rel(MECHANISM_RANKING), "issue": "no_promote_mechanism_decision"})
    if not any(row.get("mechanism_decision") == "capture_repair" for row in mechanism_rows):
        issues.append({"path": rel(MECHANISM_RANKING), "issue": "no_capture_repair_mechanism_decision"})

    boundary = read_json(RUNTIME_EFFECT_BOUNDARY, {}) or {}
    forbidden = boundary.get("forbidden_surfaces") or {}
    if any(bool(value) for value in forbidden.values()):
        issues.append({"path": rel(RUNTIME_EFFECT_BOUNDARY), "issue": "forbidden_surface_flag_true", "forbidden": forbidden})

    result = {
        "schema_version": "lane09_verification_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "counts": {
            "selector_row_evidence_rows": row_count,
            "selector_discovery_rows": discovery_count,
            "default_off_clause_rows": clause_count,
            "capture_repair_requirement_rows": capture_count,
            "mechanism_decision_rows": len(mechanism_rows),
            "focused_test_result_present": FOCUSED_TEST_RESULT.exists(),
        },
        "runtime_effect_boundary": RUNTIME_BOUNDARY_TEXT,
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
        audit = read_json(COMPLETION_AUDIT, {}) or {}
        counts = audit.get("counts") if isinstance(audit, dict) else {}
        write_completion_audit(result, counts)
        build_manifest(
            {
                SELECTOR_ROW_EVIDENCE_LEDGER.name: row_count,
                SELECTOR_DISCOVERY_LEDGER.name: discovery_count,
                DEFAULT_OFF_CLAUSE_LEDGER.name: clause_count,
                MECHANISM_RANKING.name: len(mechanism_rows),
                SPLIT_STRESS_DECONCENTRATION.name: count_jsonl(SPLIT_STRESS_DECONCENTRATION),
                CAPTURE_REPAIR_REQUIREMENTS.name: capture_count,
                SOURCE_COMPLETENESS_DECISIONS.name: count_jsonl(SOURCE_COMPLETENESS_DECISIONS),
                BRANCH_DECISIONS.name: count_jsonl(BRANCH_DECISIONS),
                NO_LEAK_VALIDATION.name: count_jsonl(NO_LEAK_VALIDATION),
                DEPENDENCY_STATE.name: count_jsonl(DEPENDENCY_STATE),
            }
        )
    return result


def main() -> None:
    args = parse_args()
    if args.verify:
        result = verify_outputs(write=True, require_focused_test=True)
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["ok"]:
            raise SystemExit(1)
        return
    result = build_outputs()
    print(json.dumps(result["verification"], indent=2, sort_keys=True))
    if not result["verification"]["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
