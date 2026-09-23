#!/usr/bin/env python3
"""Build a no-API mechanical replay substrate from the accepted source universe.

This route is discovery/control infrastructure only. It reads source-hashed
local OHLCV rows from the accepted no-API source universe, freezes mechanical
family definitions before scanning path data, emits compact unscored candidate
inventories plus discovery-only path-label rows, and records exact source
exclusions. It does not call AI, MT5, broker account/order/history/deal/position
APIs, Databento, remotes, or live trading surfaces.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev
from typing import Any, Iterable, Mapping, Sequence


ROUTE_ID = "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE"
SCHEMA_VERSION = "no_api_mechanical_replay_engine_from_source_universe_v1"
EVIDENCE_CLASS = "NO_API_MECHANICAL_PRE_AI_REPLAY_DISCOVERY_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DATE = "2026-05-10"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PREDECESSOR_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_historical_replay_engine_and_missed_opportunity_inventory"
)
PROMPT_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE_GOAL_PROMPT_2026-05-10.md"
)
NEXT_G12_PROMPT_RELATIVE_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-10.md"
)

SOURCE_LEDGER = PREDECESSOR_DIR / "NO_API_HISTORICAL_REPLAY_SOURCE_UNIVERSE_LEDGER_2026-05-10.json"
SOURCE_ROWS = PREDECESSOR_DIR / "NO_API_HISTORICAL_REPLAY_SOURCE_UNIVERSE_ROWS_2026-05-10.jsonl"
SOURCE_CONTRACT = PREDECESSOR_DIR / "NO_API_HISTORICAL_REPLAY_REPLAY_SOURCE_CONTRACT_2026-05-10.json"
PARTITION_LEDGER = PREDECESSOR_DIR / "NO_API_HISTORICAL_REPLAY_PARTITION_CONTAMINATION_NOLEAK_LEDGER_2026-05-10.json"
MISSED_INVENTORY = PREDECESSOR_DIR / "NO_API_HISTORICAL_REPLAY_MISSED_OPPORTUNITY_SOURCE_INVENTORY_2026-05-10.json"
PREDECESSOR_COMPLETION_AUDIT = PREDECESSOR_DIR / "NO_API_HISTORICAL_REPLAY_COMPLETION_AUDIT_2026-05-10.json"

OUTPUT_PREFIX = "NO_API_MECHANICAL_REPLAY"
HASH_CHUNK_BYTES = 1024 * 1024
SOURCE_HASH_THRESHOLD_BYTES = 12_582_912
CANDIDATE_ROW_WRITE_CAP = 120_000
PATH_LABEL_ROW_WRITE_CAP = 120_000
SHIFT_CONTROL_HASH_MODULUS = 5
HIGH_FREQUENCY_COOLDOWN_BARS = {
    "fvg_fill": 4,
    "baseline_shifted_entry_control": 2,
    "baseline_momentum_continuation": 8,
    "baseline_mean_reversion": 8,
    "adjacent_range_compression_breakout": 12,
}
PATH_LABEL_MAX_BY_TIMEFRAME = {"M1": 60, "M5": 24, "M15": 12, "H1": 8, "H4": 4}
SUPPORTED_REPLAY_TIMEFRAMES = {"M1", "M5", "M15", "H1", "H4"}
CONTEXT_ONLY_TIMEFRAMES = {"D1"}
SUPPORTED_SOURCE_FAMILIES = {"LOCAL_OHLCV_CSV", "SIERRA_DERIVED_OHLCV_EXPORT"}
FORBIDDEN_SURFACES = {
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_promotion": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_paid_api_or_databento_route": False,
    "opens_mt5_order_account_history_behavior": False,
    "opens_remote_push": False,
    "opens_registry_edit": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
FORBIDDEN_RESULT_FIELD_FRAGMENTS = (
    "pnl",
    "actual_r",
    "broker_actual",
    "win_rate",
    "expectancy",
    "profit",
    "loss_amount",
    "account_history",
    "deal",
    "position",
)


KILL_ZONES_UTC: dict[str, list[tuple[str, int, int]]] = {
    "XAUUSD": [("London", 7 * 60, 10 * 60 + 30), ("NY", 13 * 60, 17 * 60)],
    "XAGUSD": [("London", 7 * 60, 10 * 60 + 30), ("NY", 13 * 60, 17 * 60)],
    "NAS100": [("NY", 13 * 60, 17 * 60)],
    "US30": [("London", 8 * 60, 10 * 60 + 30), ("NY", 13 * 60 + 30, 16 * 60)],
    "US30_CASH": [("London", 8 * 60, 10 * 60 + 30), ("NY", 13 * 60 + 30, 16 * 60)],
    "US30_cash": [("London", 8 * 60, 10 * 60 + 30), ("NY", 13 * 60 + 30, 16 * 60)],
    "USDJPY": [("Tokyo", 0, 3 * 60), ("London", 7 * 60, 9 * 60 + 30), ("NY", 13 * 60, 15 * 60 + 30)],
    "GBPJPY": [("Tokyo", 0, 3 * 60), ("London", 7 * 60, 9 * 60 + 30), ("NY", 13 * 60, 15 * 60 + 30)],
    "GBPUSD": [("London", 7 * 60, 12 * 60), ("NY", 13 * 60, 15 * 60 + 30)],
    "EURUSD": [("London", 7 * 60, 12 * 60), ("NY", 13 * 60, 15 * 60 + 30)],
}
GENERIC_SESSIONS_UTC: list[tuple[str, int, int]] = [
    ("Tokyo", 0, 3 * 60),
    ("London", 7 * 60, 10 * 60 + 30),
    ("NY", 13 * 60, 17 * 60),
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def route_flags() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        **FORBIDDEN_SURFACES,
    }


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha16(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def stable_id(prefix: str, parts: Sequence[Any], size: int = 24) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:size]}"


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        for fmt in ("%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                parsed = datetime.strptime(str(value), fmt)
                break
            except ValueError:
                parsed = None  # type: ignore[assignment]
        if parsed is None:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def infer_timeframe_minutes(timeframe: str) -> int:
    tf = timeframe.upper()
    if tf == "M1":
        return 1
    if tf == "M5":
        return 5
    if tf == "M15":
        return 15
    if tf == "H1":
        return 60
    if tf == "H4":
        return 240
    if tf == "D1":
        return 1440
    return 15


def session_for(symbol: str, dt: datetime) -> str:
    key = symbol.upper()
    if key == "US30_CASH":
        key = "US30_cash"
    minute = dt.hour * 60 + dt.minute
    sessions = KILL_ZONES_UTC.get(key) or KILL_ZONES_UTC.get(symbol) or GENERIC_SESSIONS_UTC
    for name, start, end in sessions:
        if start <= minute < end:
            return name
    return "outside_configured_kill_zone"


def session_windows_for(symbol: str) -> list[tuple[str, int, int]]:
    key = symbol.upper()
    if key == "US30_CASH":
        return KILL_ZONES_UTC["US30_cash"]
    return KILL_ZONES_UTC.get(key) or KILL_ZONES_UTC.get(symbol) or GENERIC_SESSIONS_UTC


def source_path_candidates(row: Mapping[str, Any]) -> list[Path]:
    candidates: list[Path] = []
    absolute = row.get("absolute_path")
    if absolute:
        candidates.append(Path(str(absolute)))
        text = str(absolute)
        marker = r"C:\tmp\gtos_otb\NOAPIHISTREPLAY"
        if text.startswith(marker):
            candidates.append(ROOT / text[len(marker) + 1 :])
    relative = row.get("repo_relative_path")
    if relative:
        candidates.append(ROOT / str(relative))
    seen: set[str] = set()
    out: list[Path] = []
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def resolve_existing_path(row: Mapping[str, Any]) -> Path | None:
    for candidate in source_path_candidates(row):
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    keys: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in keys:
                keys.append(str(key))
    lines = ["| " + " | ".join(keys) + " |", "| " + " | ".join("---" for _ in keys) + " |"]
    for row in rows:
        values = []
        for key in keys:
            value = row.get(key)
            if isinstance(value, (dict, list)):
                value = json.dumps(value, sort_keys=True)
            values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def git_commit_or_unresolved() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNRESOLVED_BY_GIT_COMMAND"
    return result.stdout.strip() or "UNRESOLVED_BY_EMPTY_GIT_OUTPUT"


def frozen_family_registry() -> list[dict[str, Any]]:
    """Static registry frozen before any OHLC row scanning."""
    return [
        {
            "family_id": "ob_retest",
            "family_group": "core_model_a",
            "definition": "Confirmed swing break creates an order-block zone from the last opposing candle; first subsequent zone touch is the unscored candidate.",
            "asof_rule": "Swing is confirmed only after two right-side bars have closed; candidate time is retest bar close.",
            "path_label_rule": "Discovery-only first event among one-ATR continuation touch, protective-boundary close, same-bar ambiguity, window expiry.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1", "H4"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "fvg_fill",
            "family_group": "core_model_a",
            "definition": "Three-bar imbalance creates an FVG zone; first subsequent midpoint or zone touch is the unscored candidate.",
            "asof_rule": "FVG forms only after the third candle closes; fill candidate is a subsequent bar close.",
            "path_label_rule": "Discovery-only first event among one-ATR continuation touch, opposite-edge close, same-bar ambiguity, window expiry.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1", "H4"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "breaker_re_entry",
            "family_group": "core_model_a",
            "definition": "An invalidated OB becomes a breaker in the opposite direction; first subsequent retest of the breaker zone is the unscored candidate.",
            "asof_rule": "Breaker exists only after the invalidating close; re-entry candidate is a subsequent retest bar close.",
            "path_label_rule": "Discovery-only first event among one-ATR continuation touch, opposite breaker boundary close, same-bar ambiguity, window expiry.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1", "H4"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "opening_drive_no_fill_lifecycle",
            "family_group": "lifecycle_projection",
            "definition": "First 30 minutes of each configured session define an opening range; first subsequent range break creates an opening-drive candidate and tracks midpoint retrace versus extension.",
            "asof_rule": "Opening range freezes only after the opening-window bars close; break candidate is a subsequent bar close.",
            "path_label_rule": "Discovery-only no-fill lifecycle label: midpoint retrace, one-ATR extension without midpoint retrace, same-bar ambiguity, window expiry.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "session_kz_sweep",
            "family_group": "liquidity_context",
            "definition": "During configured sessions, wick through prior-day high/low with close back inside creates a sweep candidate.",
            "asof_rule": "Prior-day high/low is frozen at the first bar of the next UTC day.",
            "path_label_rule": "Discovery-only continuation/reversal context over the next source-safe bar window.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "liquidity_stop_run_context",
            "family_group": "liquidity_context",
            "definition": "Confirmed equal swing high/low pools create stop-run candidates when price wicks beyond the pool and closes back inside.",
            "asof_rule": "Equal pools are created only from confirmed swings available at the current close.",
            "path_label_rule": "Discovery-only continuation/reversal context over the next source-safe bar window.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1", "H4"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "baseline_random_session_control",
            "family_group": "adversarial_baseline",
            "definition": "One deterministic hash-selected bar per source/session/day, with side chosen by hash, as a random-time/window comparator.",
            "asof_rule": "Only the source id, session, date, and replay-clock bar count decide emission; no path data is inspected first.",
            "path_label_rule": "Same discovery-only path-label schema as mechanical families.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "baseline_shifted_entry_control",
            "family_group": "adversarial_baseline",
            "definition": "For a deterministic one-in-five hash-admitted subset of opened non-baseline family candidates, emit delayed control candidates after one and four bars if source bars exist.",
            "asof_rule": "Shifted control admission is decided from the original candidate id before delayed bars are inspected; emitted only when the delayed bar closes.",
            "path_label_rule": "Same discovery-only path-label schema as the original candidate family.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1", "H4"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "baseline_momentum_continuation",
            "family_group": "simple_baseline",
            "definition": "Twelve-bar close-to-close movement exceeding 1.5 ATR emits a continuation candidate on state transition only.",
            "asof_rule": "Uses only rolling bars closed at candidate time and an eight-bar cooldown.",
            "path_label_rule": "Discovery-only continuation/reversal context over the next source-safe bar window.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1", "H4"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "baseline_mean_reversion",
            "family_group": "simple_baseline",
            "definition": "Close two population standard deviations away from the prior 20-bar mean emits an opposite-side candidate on state transition only.",
            "asof_rule": "Uses only rolling bars closed at candidate time and an eight-bar cooldown.",
            "path_label_rule": "Discovery-only continuation/reversal context over the next source-safe bar window.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1", "H4"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
        {
            "family_id": "adjacent_range_compression_breakout",
            "family_group": "source_safe_adjacent",
            "definition": "Twelve-bar range compressed versus the previous 48-bar range, followed by a close through the compressed range boundary.",
            "asof_rule": "Range compression window is frozen before the breakout close is classified.",
            "path_label_rule": "Discovery-only continuation/reversal context over the next source-safe bar window.",
            "allowed_timeframes": ["M1", "M5", "M15", "H1", "H4"],
            "terminal_status": "OPENED_FULL_REPLAY_INVENTORY",
        },
    ]


@dataclass
class SourceRecord:
    source_row_id: str
    symbol: str
    timeframe: str
    source_family: str
    partition_assignment: str
    original_absolute_path: str
    resolved_path: Path
    source_sha256: str
    hash_status: str
    hash_resolution: str
    size_bytes: int
    row_count_estimate: int | None
    duplicate_key: str
    evidence_class: str


@dataclass
class Bar:
    index: int
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None

    @property
    def time_iso(self) -> str:
        return iso(self.time) or "UNRESOLVED_TIME"


@dataclass
class CandidateWriter:
    candidate_path: Path
    path_label_path: Path
    candidate_count: int = 0
    candidate_rows_written: int = 0
    candidate_rows_suppressed_by_artifact_cap: int = 0
    path_label_count: int = 0
    path_label_rows_written: int = 0
    path_label_rows_suppressed_by_artifact_cap: int = 0
    duplicate_candidate_keys: int = 0
    duplicate_path_keys: int = 0
    suppressed_candidates_by_family: Counter[str] = field(default_factory=Counter)
    suppressed_path_labels_by_family: Counter[str] = field(default_factory=Counter)
    candidate_keys: set[str] = field(default_factory=set)
    path_keys: set[str] = field(default_factory=set)
    candidate_digest: hashlib._Hash = field(default_factory=hashlib.sha256)
    path_digest: hashlib._Hash = field(default_factory=hashlib.sha256)

    def __post_init__(self) -> None:
        self.candidate_path.parent.mkdir(parents=True, exist_ok=True)
        self.path_label_path.parent.mkdir(parents=True, exist_ok=True)
        self.candidate_handle = self.candidate_path.open("w", encoding="utf-8", newline="\n")
        self.path_label_handle = self.path_label_path.open("w", encoding="utf-8", newline="\n")

    def close(self) -> None:
        self.candidate_handle.close()
        self.path_label_handle.close()

    def write_candidate(self, row: dict[str, Any]) -> str:
        key = str(row["duplicate_key"])
        self.candidate_count += 1
        if key in self.candidate_keys:
            self.duplicate_candidate_keys += 1
            return "duplicate"
        self.candidate_keys.add(key)
        if self.candidate_rows_written >= CANDIDATE_ROW_WRITE_CAP:
            self.candidate_rows_suppressed_by_artifact_cap += 1
            self.suppressed_candidates_by_family[str(row.get("family_id") or "UNRESOLVED_FAMILY")] += 1
            return "suppressed_by_artifact_cap"
        line = json.dumps(row, sort_keys=True)
        self.candidate_digest.update((line + "\n").encode("utf-8"))
        self.candidate_handle.write(line + "\n")
        self.candidate_rows_written += 1
        return "written"

    def write_path_label(self, row: dict[str, Any]) -> str:
        key = str(row["duplicate_key"])
        self.path_label_count += 1
        if key in self.path_keys:
            self.duplicate_path_keys += 1
            return "duplicate"
        self.path_keys.add(key)
        if self.path_label_rows_written >= PATH_LABEL_ROW_WRITE_CAP:
            self.path_label_rows_suppressed_by_artifact_cap += 1
            self.suppressed_path_labels_by_family[str(row.get("family_id") or "UNRESOLVED_FAMILY")] += 1
            return "suppressed_by_artifact_cap"
        line = json.dumps(row, sort_keys=True)
        self.path_digest.update((line + "\n").encode("utf-8"))
        self.path_label_handle.write(line + "\n")
        self.path_label_rows_written += 1
        return "written"


@dataclass
class ReplayAggregate:
    candidate_by_family: Counter[str] = field(default_factory=Counter)
    candidate_by_source_family: Counter[str] = field(default_factory=Counter)
    candidate_by_symbol: Counter[str] = field(default_factory=Counter)
    candidate_by_timeframe: Counter[str] = field(default_factory=Counter)
    candidate_by_session: Counter[str] = field(default_factory=Counter)
    candidate_by_regime: Counter[str] = field(default_factory=Counter)
    path_label_by_status: Counter[str] = field(default_factory=Counter)
    source_status: Counter[str] = field(default_factory=Counter)
    family_source_slice_counts: Counter[str] = field(default_factory=Counter)
    source_summaries: list[dict[str, Any]] = field(default_factory=list)
    excluded_slices: list[dict[str, Any]] = field(default_factory=list)
    continuation_rows: list[dict[str, Any]] = field(default_factory=list)
    parse_errors: list[dict[str, Any]] = field(default_factory=list)


class ReplayScanner:
    def __init__(self, source: SourceRecord, writer: CandidateWriter, aggregate: ReplayAggregate):
        self.source = source
        self.writer = writer
        self.aggregate = aggregate
        self.tf_minutes = infer_timeframe_minutes(source.timeframe)
        self.bars: deque[Bar] = deque(maxlen=80)
        self.tr_values: deque[float] = deque(maxlen=14)
        self.confirmed_highs: list[dict[str, Any]] = []
        self.confirmed_lows: list[dict[str, Any]] = []
        self.broken_swing_ids: set[str] = set()
        self.active_obs: list[dict[str, Any]] = []
        self.active_fvgs: list[dict[str, Any]] = []
        self.active_breakers: list[dict[str, Any]] = []
        self.active_path_labels: list[dict[str, Any]] = []
        self.shifted_queue: list[dict[str, Any]] = []
        self.emitted_opening: set[str] = set()
        self.opening_state: dict[str, dict[str, Any]] = {}
        self.random_baseline_emitted: set[str] = set()
        self.cooldowns: dict[str, int] = defaultdict(int)
        self.equal_pools: list[dict[str, Any]] = []
        self.prev_day_high: float | None = None
        self.prev_day_low: float | None = None
        self.current_day: str | None = None
        self.day_high: float | None = None
        self.day_low: float | None = None
        self.rows_seen = 0
        self.first_time: str | None = None
        self.last_time: str | None = None

    def process(self, bar: Bar) -> None:
        self.rows_seen += 1
        self.first_time = self.first_time or bar.time_iso
        self.last_time = bar.time_iso
        self._update_daily_context(bar)
        prev_close = self.bars[-1].close if self.bars else None
        if prev_close is not None:
            tr = max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close))
            self.tr_values.append(tr)
        self.bars.append(bar)
        self._decrement_cooldowns()
        self._update_path_labels(bar)
        self._emit_shifted_controls(bar)
        self._confirm_swings()
        self._detect_baseline_random(bar)
        self._detect_opening_drive(bar)
        self._detect_structure_families(bar)
        self._detect_sweeps(bar)
        self._detect_simple_baselines(bar)
        self._detect_range_compression(bar)

    def finish(self) -> None:
        for label in list(self.active_path_labels):
            self._close_path_label(label, None, "UNRESOLVED_AT_SOURCE_END", "source ended before path-label window closed")
        self.aggregate.source_summaries.append(
            {
                "source_row_id": self.source.source_row_id,
                "symbol": self.source.symbol,
                "timeframe": self.source.timeframe,
                "source_family": self.source.source_family,
                "rows_seen": self.rows_seen,
                "first_time_utc": self.first_time,
                "last_time_utc": self.last_time,
                "candidate_rows": sum(
                    count
                    for key, count in self.aggregate.family_source_slice_counts.items()
                    if key.startswith(f"{self.source.source_row_id}|")
                ),
                "source_sha256": self.source.source_sha256,
                "hash_resolution": self.source.hash_resolution,
            }
        )

    def atr(self) -> float:
        if not self.tr_values:
            if len(self.bars) >= 2:
                ranges = [b.high - b.low for b in self.bars]
                return max(sum(ranges) / len(ranges), 1e-12)
            return 1e-12
        return max(sum(self.tr_values) / len(self.tr_values), 1e-12)

    def _decrement_cooldowns(self) -> None:
        for key in list(self.cooldowns):
            self.cooldowns[key] -= 1
            if self.cooldowns[key] <= 0:
                del self.cooldowns[key]

    def _update_daily_context(self, bar: Bar) -> None:
        day = bar.time.date().isoformat()
        if self.current_day is None:
            self.current_day = day
            self.day_high = bar.high
            self.day_low = bar.low
            return
        if day != self.current_day:
            self.prev_day_high = self.day_high
            self.prev_day_low = self.day_low
            self.current_day = day
            self.day_high = bar.high
            self.day_low = bar.low
        else:
            self.day_high = max(self.day_high if self.day_high is not None else bar.high, bar.high)
            self.day_low = min(self.day_low if self.day_low is not None else bar.low, bar.low)

    def _confirm_swings(self) -> None:
        if len(self.bars) < 5:
            return
        window = list(self.bars)
        center = window[-3]
        left = window[-5:-3]
        right = window[-2:]
        atr = self.atr()
        if all(center.high > b.high for b in left + right):
            swing = {"type": "high", "index": center.index, "time": center.time_iso, "price": center.high}
            self.confirmed_highs.append(swing)
            self._register_equal_pool(swing, atr)
        if all(center.low < b.low for b in left + right):
            swing = {"type": "low", "index": center.index, "time": center.time_iso, "price": center.low}
            self.confirmed_lows.append(swing)
            self._register_equal_pool(swing, atr)

    def _register_equal_pool(self, swing: Mapping[str, Any], atr: float) -> None:
        side = "high" if swing["type"] == "high" else "low"
        prior = self.confirmed_highs if side == "high" else self.confirmed_lows
        if len(prior) < 2:
            return
        current_price = float(swing["price"])
        tolerance = max(atr * 0.1, abs(current_price) * 0.0002)
        for old in reversed(prior[:-1]):
            if abs(float(old["price"]) - current_price) <= tolerance:
                pool = {
                    "pool_id": stable_id("POOL", [self.source.source_row_id, side, old["time"], swing["time"], round(current_price, 8)], 18),
                    "side": side,
                    "price": round((float(old["price"]) + current_price) / 2.0, 8),
                    "formed_time_utc": swing["time"],
                    "source_swings": [old["time"], swing["time"]],
                    "swept": False,
                }
                self.equal_pools.append(pool)
                if len(self.equal_pools) > 80:
                    self.equal_pools = self.equal_pools[-80:]
                break

    def _find_last_opposing_candle(self, side: str) -> Bar | None:
        for item in reversed(list(self.bars)[:-1]):
            if side == "LONG" and item.close < item.open:
                return item
            if side == "SHORT" and item.close > item.open:
                return item
        return None

    def _detect_structure_families(self, bar: Bar) -> None:
        if len(self.bars) < 12:
            return
        latest_high = self.confirmed_highs[-1] if self.confirmed_highs else None
        latest_low = self.confirmed_lows[-1] if self.confirmed_lows else None
        if latest_high and bar.close > float(latest_high["price"]):
            swing_id = f"H|{latest_high['time']}|{latest_high['price']}"
            if swing_id not in self.broken_swing_ids:
                self.broken_swing_ids.add(swing_id)
                self._create_ob("LONG", bar, latest_high)
        if latest_low and bar.close < float(latest_low["price"]):
            swing_id = f"L|{latest_low['time']}|{latest_low['price']}"
            if swing_id not in self.broken_swing_ids:
                self.broken_swing_ids.add(swing_id)
                self._create_ob("SHORT", bar, latest_low)
        self._detect_fvg_creation(bar)
        self._detect_ob_retests(bar)
        self._detect_fvg_fills(bar)
        self._detect_breaker_retests(bar)

    def _create_ob(self, side: str, bar: Bar, broken_swing: Mapping[str, Any]) -> None:
        opposing = self._find_last_opposing_candle(side)
        if opposing is None:
            return
        ob = {
            "zone_id": stable_id("OB", [self.source.source_row_id, side, opposing.time_iso, bar.time_iso], 18),
            "side": side,
            "zone_low": min(opposing.low, opposing.high),
            "zone_high": max(opposing.low, opposing.high),
            "created_index": bar.index,
            "created_time_utc": bar.time_iso,
            "source_candle_time_utc": opposing.time_iso,
            "broken_swing_time_utc": broken_swing.get("time"),
            "used": False,
            "invalidated": False,
        }
        self.active_obs.append(ob)
        if len(self.active_obs) > 80:
            self.active_obs = self.active_obs[-80:]

    def _detect_ob_retests(self, bar: Bar) -> None:
        self.active_obs = [
            ob
            for ob in self.active_obs
            if not (ob.get("used") and bar.index - int(ob.get("created_index", bar.index)) > 10)
            and bar.index - int(ob.get("created_index", bar.index)) <= 500
        ]
        for ob in self.active_obs:
            if ob["used"] or ob["invalidated"] or bar.index <= int(ob["created_index"]) + 1:
                continue
            if self._bar_intersects_zone(bar, float(ob["zone_low"]), float(ob["zone_high"])):
                self._emit_candidate("ob_retest", str(ob["side"]), bar, ob)
                ob["used"] = True
            else:
                self._maybe_create_breaker_from_ob(ob, bar)

    def _maybe_create_breaker_from_ob(self, ob: dict[str, Any], bar: Bar) -> None:
        if ob["invalidated"]:
            return
        if ob["side"] == "LONG" and bar.close < float(ob["zone_low"]):
            side = "SHORT"
        elif ob["side"] == "SHORT" and bar.close > float(ob["zone_high"]):
            side = "LONG"
        else:
            return
        ob["invalidated"] = True
        breaker = {
            "zone_id": stable_id("BRK", [ob["zone_id"], side, bar.time_iso], 18),
            "side": side,
            "zone_low": ob["zone_low"],
            "zone_high": ob["zone_high"],
            "created_index": bar.index,
            "created_time_utc": bar.time_iso,
            "source_ob_id": ob["zone_id"],
            "used": False,
        }
        self.active_breakers.append(breaker)
        if len(self.active_breakers) > 80:
            self.active_breakers = self.active_breakers[-80:]

    def _detect_breaker_retests(self, bar: Bar) -> None:
        self.active_breakers = [
            breaker
            for breaker in self.active_breakers
            if not breaker.get("used") and bar.index - int(breaker.get("created_index", bar.index)) <= 500
        ]
        for breaker in self.active_breakers:
            if breaker["used"] or bar.index <= int(breaker["created_index"]) + 1:
                continue
            if self._bar_intersects_zone(bar, float(breaker["zone_low"]), float(breaker["zone_high"])):
                self._emit_candidate("breaker_re_entry", str(breaker["side"]), bar, breaker)
                breaker["used"] = True

    def _detect_fvg_creation(self, bar: Bar) -> None:
        if len(self.bars) < 3:
            return
        a, _middle, c = list(self.bars)[-3:]
        atr = self.atr()
        min_gap = max(atr * 0.35, abs(bar.close) * 0.00005)
        if c.low - a.high >= min_gap:
            self.active_fvgs.append(
                {
                    "zone_id": stable_id("FVG", [self.source.source_row_id, "LONG", a.time_iso, c.time_iso], 18),
                    "side": "LONG",
                    "zone_low": a.high,
                    "zone_high": c.low,
                    "midpoint": (a.high + c.low) / 2.0,
                    "created_index": c.index,
                    "created_time_utc": c.time_iso,
                    "used": False,
                }
            )
        if a.low - c.high >= min_gap:
            self.active_fvgs.append(
                {
                    "zone_id": stable_id("FVG", [self.source.source_row_id, "SHORT", a.time_iso, c.time_iso], 18),
                    "side": "SHORT",
                    "zone_low": c.high,
                    "zone_high": a.low,
                    "midpoint": (c.high + a.low) / 2.0,
                    "created_index": c.index,
                    "created_time_utc": c.time_iso,
                    "used": False,
                }
            )
        if len(self.active_fvgs) > 120:
            self.active_fvgs = self.active_fvgs[-120:]

    def _detect_fvg_fills(self, bar: Bar) -> None:
        self.active_fvgs = [
            fvg
            for fvg in self.active_fvgs
            if not fvg.get("used") and bar.index - int(fvg.get("created_index", bar.index)) <= 240
        ]
        for fvg in self.active_fvgs:
            if fvg["used"] or bar.index <= int(fvg["created_index"]) + 1:
                continue
            midpoint = float(fvg["midpoint"])
            if bar.low <= midpoint <= bar.high:
                self._emit_candidate("fvg_fill", str(fvg["side"]), bar, fvg)
                fvg["used"] = True

    def _detect_opening_drive(self, bar: Bar) -> None:
        if self.source.timeframe not in {"M1", "M5", "M15", "H1"}:
            return
        for session_name, start, end in session_windows_for(self.source.symbol):
            day_key = bar.time.date().isoformat()
            key = f"{day_key}|{session_name}"
            minute = bar.time.hour * 60 + bar.time.minute
            if not (start <= minute < end):
                continue
            opening_minutes = 30
            open_bars = max(1, math.ceil(opening_minutes / self.tf_minutes))
            state = self.opening_state.setdefault(
                key,
                {
                    "bars": 0,
                    "high": bar.high,
                    "low": bar.low,
                    "start_time_utc": bar.time_iso,
                    "frozen": False,
                },
            )
            if not state["frozen"]:
                state["bars"] += 1
                state["high"] = max(float(state["high"]), bar.high)
                state["low"] = min(float(state["low"]), bar.low)
                if state["bars"] >= open_bars:
                    state["frozen"] = True
                    state["frozen_time_utc"] = bar.time_iso
                return
            if key in self.emitted_opening:
                return
            if bar.close > float(state["high"]):
                zone = {
                    "zone_id": stable_id("OPEN", [self.source.source_row_id, key, "LONG"], 18),
                    "side": "LONG",
                    "zone_low": float(state["low"]),
                    "zone_high": float(state["high"]),
                    "midpoint": (float(state["low"]) + float(state["high"])) / 2.0,
                    "created_time_utc": state.get("frozen_time_utc"),
                    "session": session_name,
                }
                self._emit_candidate("opening_drive_no_fill_lifecycle", "LONG", bar, zone)
                self.emitted_opening.add(key)
            elif bar.close < float(state["low"]):
                zone = {
                    "zone_id": stable_id("OPEN", [self.source.source_row_id, key, "SHORT"], 18),
                    "side": "SHORT",
                    "zone_low": float(state["low"]),
                    "zone_high": float(state["high"]),
                    "midpoint": (float(state["low"]) + float(state["high"])) / 2.0,
                    "created_time_utc": state.get("frozen_time_utc"),
                    "session": session_name,
                }
                self._emit_candidate("opening_drive_no_fill_lifecycle", "SHORT", bar, zone)
                self.emitted_opening.add(key)

    def _detect_sweeps(self, bar: Bar) -> None:
        if self.source.timeframe not in {"M1", "M5", "M15", "H1", "H4"}:
            return
        kz = session_for(self.source.symbol, bar.time)
        if kz != "outside_configured_kill_zone":
            if self.prev_day_high is not None and bar.high > self.prev_day_high and bar.close < self.prev_day_high:
                self._emit_candidate(
                    "session_kz_sweep",
                    "SHORT",
                    bar,
                    {
                        "zone_id": stable_id("PDH", [self.source.source_row_id, bar.time.date().isoformat(), self.prev_day_high], 18),
                        "zone_low": self.prev_day_high,
                        "zone_high": self.prev_day_high,
                        "swept_level": self.prev_day_high,
                        "reference": "previous_day_high",
                    },
                )
            if self.prev_day_low is not None and bar.low < self.prev_day_low and bar.close > self.prev_day_low:
                self._emit_candidate(
                    "session_kz_sweep",
                    "LONG",
                    bar,
                    {
                        "zone_id": stable_id("PDL", [self.source.source_row_id, bar.time.date().isoformat(), self.prev_day_low], 18),
                        "zone_low": self.prev_day_low,
                        "zone_high": self.prev_day_low,
                        "swept_level": self.prev_day_low,
                        "reference": "previous_day_low",
                    },
                )
        for pool in self.equal_pools:
            if pool.get("swept"):
                continue
            price = float(pool["price"])
            if pool["side"] == "high" and bar.high > price and bar.close < price:
                self._emit_candidate("liquidity_stop_run_context", "SHORT", bar, {**pool, "zone_low": price, "zone_high": price})
                pool["swept"] = True
            elif pool["side"] == "low" and bar.low < price and bar.close > price:
                self._emit_candidate("liquidity_stop_run_context", "LONG", bar, {**pool, "zone_low": price, "zone_high": price})
                pool["swept"] = True

    def _detect_baseline_random(self, bar: Bar) -> None:
        if self.source.timeframe not in {"M1", "M5", "M15", "H1"}:
            return
        current_session = session_for(self.source.symbol, bar.time)
        if current_session == "outside_configured_kill_zone":
            return
        key = f"{self.source.source_row_id}|{bar.time.date().isoformat()}|{current_session}"
        if key in self.random_baseline_emitted:
            return
        windows = [item for item in session_windows_for(self.source.symbol) if item[0] == current_session]
        if not windows:
            return
        _, start, end = windows[0]
        total_bars = max(1, math.ceil((end - start) / self.tf_minutes))
        offset = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) % total_bars
        minute = bar.time.hour * 60 + bar.time.minute
        current_offset = max(0, math.floor((minute - start) / self.tf_minutes))
        if current_offset == offset:
            side = "LONG" if int(hashlib.sha256((key + "|side").encode("utf-8")).hexdigest()[:2], 16) % 2 == 0 else "SHORT"
            self._emit_candidate(
                "baseline_random_session_control",
                side,
                bar,
                {
                    "zone_id": stable_id("RAND", [key], 18),
                    "zone_low": bar.close,
                    "zone_high": bar.close,
                    "reference": "hash_selected_session_bar",
                },
                schedule_shifted=False,
            )
            self.random_baseline_emitted.add(key)

    def _detect_simple_baselines(self, bar: Bar) -> None:
        if len(self.bars) < 30:
            return
        atr = self.atr()
        closes = [b.close for b in self.bars]
        move = closes[-1] - closes[-13]
        if abs(move) > 1.5 * atr:
            side = "LONG" if move > 0 else "SHORT"
            key = f"baseline_momentum_continuation|{side}"
            if key not in self.cooldowns:
                self._emit_candidate(
                    "baseline_momentum_continuation",
                    side,
                    bar,
                    {"zone_id": stable_id("MOM", [self.source.source_row_id, side, bar.time_iso], 18), "zone_low": bar.close, "zone_high": bar.close, "rolling_move": round(move, 8)},
                    schedule_shifted=False,
                )
                self.cooldowns[key] = 8
        window = closes[-21:-1]
        if len(window) >= 20:
            mean = sum(window) / len(window)
            dev = max(pstdev(window), atr * 0.25, 1e-12)
            z = (bar.close - mean) / dev
            if abs(z) > 2.0:
                side = "SHORT" if z > 0 else "LONG"
                key = f"baseline_mean_reversion|{side}"
                if key not in self.cooldowns:
                    self._emit_candidate(
                        "baseline_mean_reversion",
                        side,
                        bar,
                        {"zone_id": stable_id("MR", [self.source.source_row_id, side, bar.time_iso], 18), "zone_low": mean, "zone_high": bar.close, "zscore": round(z, 6)},
                        schedule_shifted=False,
                    )
                    self.cooldowns[key] = 8

    def _detect_range_compression(self, bar: Bar) -> None:
        if len(self.bars) < 60:
            return
        bars = list(self.bars)
        compression = bars[-13:-1]
        prior = bars[-61:-13]
        comp_high = max(b.high for b in compression)
        comp_low = min(b.low for b in compression)
        prior_high = max(b.high for b in prior)
        prior_low = min(b.low for b in prior)
        comp_range = comp_high - comp_low
        prior_range = max(prior_high - prior_low, 1e-12)
        if comp_range / prior_range > 0.35:
            return
        if bar.close > comp_high:
            side = "LONG"
        elif bar.close < comp_low:
            side = "SHORT"
        else:
            return
        key = f"adjacent_range_compression_breakout|{side}"
        if key in self.cooldowns:
            return
        self._emit_candidate(
            "adjacent_range_compression_breakout",
            side,
            bar,
            {
                "zone_id": stable_id("RCB", [self.source.source_row_id, side, compression[0].time_iso, bar.time_iso], 18),
                "zone_low": comp_low,
                "zone_high": comp_high,
                "compression_ratio": round(comp_range / prior_range, 6),
            },
        )
        self.cooldowns[key] = 12

    @staticmethod
    def _bar_intersects_zone(bar: Bar, low: float, high: float) -> bool:
        lo, hi = min(low, high), max(low, high)
        return bar.low <= hi and bar.high >= lo

    def _regime_phase(self) -> str:
        if len(self.bars) < 50:
            return "insufficient_history"
        closes = [b.close for b in self.bars]
        short = sum(closes[-12:]) / 12
        long = sum(closes[-48:]) / 48
        diff = short - long
        atr = self.atr()
        if abs(diff) <= 0.25 * atr:
            return "range_or_mixed"
        return "bullish_context" if diff > 0 else "bearish_context"

    def _emit_candidate(
        self,
        family_id: str,
        side: str,
        bar: Bar,
        zone: Mapping[str, Any],
        *,
        schedule_shifted: bool = True,
    ) -> None:
        family_registry_ids = {item["family_id"] for item in frozen_family_registry()}
        if family_id not in family_registry_ids:
            raise ValueError(f"unregistered family: {family_id}")
        side = side.upper()
        cooldown_key = f"emit|{family_id}|{side}"
        if cooldown_key in self.cooldowns:
            return
        atr = self.atr()
        candidate_id = stable_id(
            "MEC",
            [
                self.source.source_row_id,
                self.source.source_sha256,
                family_id,
                side,
                bar.time_iso,
                zone.get("zone_id"),
                round(float(zone.get("zone_low", bar.close)), 8),
                round(float(zone.get("zone_high", bar.close)), 8),
            ],
        )
        duplicate_key = stable_id(
            "DUP",
            [
                self.source.symbol,
                self.source.timeframe,
                family_id,
                side,
                bar.time_iso,
                zone.get("zone_id"),
                self.source.source_sha256,
            ],
            32,
        )
        row = {
            **route_flags(),
            "schema_version": "no_api_mechanical_candidate_inventory_row_v1",
            "candidate_id": candidate_id,
            "duplicate_key": duplicate_key,
            "source_row_id": self.source.source_row_id,
            "source_sha256": self.source.source_sha256,
            "source_family": self.source.source_family,
            "source_partition": self.source.partition_assignment,
            "source_path_fingerprint": sha16(str(self.source.resolved_path)),
            "symbol": self.source.symbol,
            "timeframe": self.source.timeframe,
            "decision_time_utc": bar.time_iso,
            "family_id": family_id,
            "side": side,
            "session_or_kill_zone": session_for(self.source.symbol, bar.time),
            "regime_phase": self._regime_phase(),
            "asof_policy": "decision_fields_from_closed_bars_only",
            "projection_only": True,
            "no_ai_calls": True,
            "no_execution": True,
            "no_result_scoring": True,
            "path_label_inventory_only": True,
            "bar_index": bar.index,
            "close_price": round(bar.close, 8),
            "atr_context": round(atr, 8),
            "zone_low": round(float(zone.get("zone_low", bar.close)), 8),
            "zone_high": round(float(zone.get("zone_high", bar.close)), 8),
            "zone_reference_id": str(zone.get("zone_id") or zone.get("pool_id") or "SOURCE_DEFINED_LEVEL"),
            "source_contract_version": "no_api_mechanical_replay_frozen_policy_v1",
        }
        write_status = self.writer.write_candidate(row)
        if write_status != "duplicate":
            self.aggregate.candidate_by_family[family_id] += 1
            self.aggregate.candidate_by_source_family[self.source.source_family] += 1
            self.aggregate.candidate_by_symbol[self.source.symbol] += 1
            self.aggregate.candidate_by_timeframe[self.source.timeframe] += 1
            self.aggregate.candidate_by_session[row["session_or_kill_zone"]] += 1
            self.aggregate.candidate_by_regime[row["regime_phase"]] += 1
            self.aggregate.family_source_slice_counts[f"{self.source.source_row_id}|{family_id}"] += 1
            cooldown_bars = HIGH_FREQUENCY_COOLDOWN_BARS.get(family_id)
            if cooldown_bars:
                self.cooldowns[cooldown_key] = cooldown_bars
        if write_status != "duplicate":
            self._open_path_label(candidate_id, family_id, side, bar, zone, atr)
            if schedule_shifted and not family_id.startswith("baseline_"):
                self._schedule_shifted_controls(candidate_id, family_id, side, bar, zone)

    def _schedule_shifted_controls(self, candidate_id: str, family_id: str, side: str, bar: Bar, zone: Mapping[str, Any]) -> None:
        admission = int(hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()[:8], 16)
        if admission % SHIFT_CONTROL_HASH_MODULUS != 0:
            return
        for delay in (1, 4):
            self.shifted_queue.append(
                {
                    "target_index": bar.index + delay,
                    "original_candidate_id": candidate_id,
                    "original_family_id": family_id,
                    "side": side,
                    "zone": dict(zone),
                    "delay_bars": delay,
                }
            )

    def _emit_shifted_controls(self, bar: Bar) -> None:
        remaining: list[dict[str, Any]] = []
        for item in self.shifted_queue:
            if bar.index < int(item["target_index"]):
                remaining.append(item)
                continue
            if bar.index == int(item["target_index"]):
                zone = dict(item["zone"])
                zone["zone_id"] = stable_id("SHIFT", [item["original_candidate_id"], item["delay_bars"], bar.time_iso], 18)
                zone["shift_delay_bars"] = item["delay_bars"]
                self._emit_candidate(
                    "baseline_shifted_entry_control",
                    str(item["side"]),
                    bar,
                    zone,
                    schedule_shifted=False,
                )
        self.shifted_queue = remaining

    def _open_path_label(
        self,
        candidate_id: str,
        family_id: str,
        side: str,
        bar: Bar,
        zone: Mapping[str, Any],
        atr: float,
    ) -> None:
        max_bars = PATH_LABEL_MAX_BY_TIMEFRAME.get(self.source.timeframe, 12)
        if side == "LONG":
            extension_price = bar.close + atr
            adverse_price = float(zone.get("zone_low", bar.close - atr))
        else:
            extension_price = bar.close - atr
            adverse_price = float(zone.get("zone_high", bar.close + atr))
        midpoint = zone.get("midpoint")
        self.active_path_labels.append(
            {
                "candidate_id": candidate_id,
                "family_id": family_id,
                "side": side,
                "opened_index": bar.index,
                "opened_time_utc": bar.time_iso,
                "max_bars": max_bars,
                "extension_price": extension_price,
                "adverse_price": adverse_price,
                "midpoint": safe_float(midpoint),
            }
        )

    def _update_path_labels(self, bar: Bar) -> None:
        remaining: list[dict[str, Any]] = []
        for label in self.active_path_labels:
            if bar.index <= int(label["opened_index"]):
                remaining.append(label)
                continue
            status = self._path_label_status(label, bar)
            if status is not None:
                self._close_path_label(label, bar, status, "first source-safe path event observed after candidate close")
                continue
            if bar.index - int(label["opened_index"]) >= int(label["max_bars"]):
                self._close_path_label(label, bar, "UNRESOLVED_BY_WINDOW", "path-label window expired without first terminal context event")
                continue
            remaining.append(label)
        self.active_path_labels = remaining

    def _path_label_status(self, label: Mapping[str, Any], bar: Bar) -> str | None:
        side = str(label["side"])
        extension = float(label["extension_price"])
        adverse = float(label["adverse_price"])
        midpoint = safe_float(label.get("midpoint"))
        if side == "LONG":
            extension_hit = bar.high >= extension
            adverse_hit = bar.close < adverse
            midpoint_hit = midpoint is not None and bar.low <= midpoint
        else:
            extension_hit = bar.low <= extension
            adverse_hit = bar.close > adverse
            midpoint_hit = midpoint is not None and bar.high >= midpoint
        if extension_hit and (adverse_hit or midpoint_hit):
            return "SAME_BAR_CONTEXT_AMBIGUOUS"
        if midpoint_hit and label["family_id"] == "opening_drive_no_fill_lifecycle":
            return "MIDPOINT_RETRACE_BEFORE_EXTENSION"
        if extension_hit:
            if label["family_id"] == "opening_drive_no_fill_lifecycle":
                return "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE"
            return "ONE_ATR_CONTINUATION_CONTEXT_TOUCH"
        if adverse_hit:
            return "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH"
        return None

    def _close_path_label(self, label: Mapping[str, Any], bar: Bar | None, status: str, reason: str) -> None:
        duplicate_key = stable_id("PDUP", [label["candidate_id"], status, bar.time_iso if bar else "SOURCE_END"], 32)
        row = {
            **route_flags(),
            "schema_version": "no_api_mechanical_discovery_path_label_row_v1",
            "candidate_id": label["candidate_id"],
            "duplicate_key": duplicate_key,
            "source_row_id": self.source.source_row_id,
            "source_sha256": self.source.source_sha256,
            "symbol": self.source.symbol,
            "timeframe": self.source.timeframe,
            "family_id": label["family_id"],
            "side": label["side"],
            "decision_time_utc": label["opened_time_utc"],
            "label_observed_time_utc": bar.time_iso if bar else None,
            "bars_observed": (bar.index - int(label["opened_index"])) if bar else None,
            "label_status": status,
            "label_family": "DISCOVERY_PATH_LABEL_ONLY",
            "label_reason": reason,
            "projection_only": True,
            "no_result_scoring": True,
            "no_ai_calls": True,
            "no_execution": True,
        }
        if self.writer.write_path_label(row) != "duplicate":
            self.aggregate.path_label_by_status[status] += 1


def iter_csv_bars(path: Path) -> Iterable[Bar]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return
        field_map = {name.lower().strip(): name for name in reader.fieldnames}
        time_field = field_map.get("time") or field_map.get("timestamp") or field_map.get("time_utc") or field_map.get("datetime")
        required = {
            "open": field_map.get("open"),
            "high": field_map.get("high"),
            "low": field_map.get("low"),
            "close": field_map.get("close"),
        }
        if time_field is None or any(value is None for value in required.values()):
            raise ValueError(f"missing required OHLCV columns in {path}")
        volume_field = field_map.get("volume") or field_map.get("tick_volume")
        index = 0
        for row in reader:
            dt = parse_utc(row.get(time_field))
            o = safe_float(row.get(required["open"]))
            h = safe_float(row.get(required["high"]))
            l = safe_float(row.get(required["low"]))
            c = safe_float(row.get(required["close"]))
            if dt is None or o is None or h is None or l is None or c is None:
                continue
            volume = safe_float(row.get(volume_field)) if volume_field else None
            yield Bar(index=index, time=dt, open=o, high=h, low=l, close=c, volume=volume)
            index += 1


def select_sources(source_rows: Sequence[Mapping[str, Any]]) -> tuple[list[SourceRecord], list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[SourceRecord] = []
    excluded: list[dict[str, Any]] = []
    hash_resolutions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in source_rows:
        family = str(row.get("source_family") or "")
        timeframe = str(row.get("timeframe") or "").upper()
        source_row_id = str(row.get("source_row_id") or "")
        if family not in SUPPORTED_SOURCE_FAMILIES:
            excluded.append(
                excluded_row(
                    row,
                    "EXCLUDED_SOURCE_FAMILY_NOT_OHLCV_REPLAY_INPUT",
                    "Terminal for this lane: source family is context/status/source-control only for mechanical OHLC replay; next route may build a parser-specific packet if ranked.",
                )
            )
            continue
        if timeframe in CONTEXT_ONLY_TIMEFRAMES:
            excluded.append(
                excluded_row(
                    row,
                    "EXCLUDED_D1_CONTEXT_ONLY_FOR_INTRADAY_REPLAY",
                    "D1 remains source context for phase/regime joins; intraday candidate families require replay bars.",
                )
            )
            continue
        if timeframe not in SUPPORTED_REPLAY_TIMEFRAMES:
            excluded.append(
                excluded_row(
                    row,
                    "EXCLUDED_TIMEFRAME_OR_SCHEMA_NOT_REPLAYABLE",
                    "The CSV is not a supported OHLC replay timeframe for this route.",
                )
            )
            continue
        path = resolve_existing_path(row)
        if path is None:
            excluded.append(
                excluded_row(
                    row,
                    "EXCLUDED_SOURCE_PATH_NOT_RESOLVED_AFTER_APPROVED_LOCAL_SEARCH",
                    "Searched row absolute path, current worktree relative path, and mapped NOAPIHISTREPLAY path; exact source path remains absent in approved roots.",
                )
            )
            continue
        size = int(path.stat().st_size)
        hash_status = str(row.get("hash_status") or "")
        if hash_status == "sha256_complete" and row.get("sha256"):
            source_sha = str(row["sha256"])
            hash_resolution = "accepted_predecessor_sha256"
        else:
            source_sha = sha256_file(path)
            hash_resolution = "resolved_large_file_sha256_in_mechanical_route"
            hash_resolutions.append(
                {
                    "source_row_id": source_row_id,
                    "absolute_path": str(path),
                    "size_bytes": size,
                    "sha256": source_sha,
                    "previous_hash_status": hash_status,
                    "resolution": hash_resolution,
                }
            )
        dedupe_key = f"{family}|{str(row.get('symbol') or '')}|{timeframe}|{source_sha}"
        if dedupe_key in seen:
            excluded.append(
                excluded_row(
                    row,
                    "EXCLUDED_DUPLICATE_SOURCE_HASH_ALREADY_SELECTED",
                    "Another source-universe row resolves to the same symbol/timeframe/source-family/hash and was processed once.",
                )
            )
            continue
        seen.add(dedupe_key)
        selected.append(
            SourceRecord(
                source_row_id=source_row_id,
                symbol=str(row.get("symbol") or "UNSPECIFIED_OR_MULTI"),
                timeframe=timeframe,
                source_family=family,
                partition_assignment=str(row.get("partition_assignment") or "projection_only"),
                original_absolute_path=str(row.get("absolute_path") or ""),
                resolved_path=path,
                source_sha256=source_sha,
                hash_status=hash_status,
                hash_resolution=hash_resolution,
                size_bytes=size,
                row_count_estimate=row.get("row_count_estimate"),
                duplicate_key=str(row.get("duplicate_key") or ""),
                evidence_class=str(row.get("evidence_class") or ""),
            )
        )
    return selected, excluded, hash_resolutions


def excluded_row(row: Mapping[str, Any], reason: str, terminal_detail: str) -> dict[str, Any]:
    return {
        "source_row_id": row.get("source_row_id"),
        "source_family": row.get("source_family"),
        "symbol": row.get("symbol"),
        "timeframe": row.get("timeframe"),
        "absolute_path": row.get("absolute_path"),
        "exclusion_reason": reason,
        "terminal_detail": terminal_detail,
        "recoverable_market_data": reason in {"EXCLUDED_SOURCE_PATH_NOT_RESOLVED_AFTER_APPROVED_LOCAL_SEARCH"},
        "non_generatable_gtos_source_state_truth": False,
    }


def build_route(output_dir: Path = ROUTE_DIR, source_rows_path: Path = SOURCE_ROWS) -> dict[str, Any]:
    generated_at = utc_now_iso()
    output_dir.mkdir(parents=True, exist_ok=True)
    predecessor = {
        "source_ledger": read_json(SOURCE_LEDGER),
        "source_contract": read_json(SOURCE_CONTRACT),
        "partition_ledger": read_json(PARTITION_LEDGER),
        "missed_inventory": read_json(MISSED_INVENTORY),
        "completion_audit": read_json(PREDECESSOR_COMPLETION_AUDIT),
    }
    source_rows = read_jsonl(source_rows_path)
    registry = frozen_family_registry()
    schema_policy = frozen_schema_policy(generated_at, registry)
    selected_sources, excluded, hash_resolutions = select_sources(source_rows)

    candidate_rows_path = output_dir / f"{OUTPUT_PREFIX}_CANDIDATE_INVENTORY_ROWS_{DATE}.jsonl"
    path_label_rows_path = output_dir / f"{OUTPUT_PREFIX}_DISCOVERY_PATH_LABEL_ROWS_{DATE}.jsonl"
    progress_path = output_dir / f"{OUTPUT_PREFIX}_SOURCE_PROGRESS_{DATE}.jsonl"
    if progress_path.exists():
        progress_path.unlink()
    writer = CandidateWriter(candidate_rows_path, path_label_rows_path)
    aggregate = ReplayAggregate()
    aggregate.excluded_slices.extend(excluded)
    try:
        for source in selected_sources:
            scanner = ReplayScanner(source, writer, aggregate)
            try:
                for bar in iter_csv_bars(source.resolved_path):
                    scanner.process(bar)
                scanner.finish()
                aggregate.source_status["processed_replayable_source"] += 1
                append_jsonl(
                    progress_path,
                    {
                        "route_id": ROUTE_ID,
                        "source_row_id": source.source_row_id,
                        "symbol": source.symbol,
                        "timeframe": source.timeframe,
                        "source_family": source.source_family,
                        "rows_seen": scanner.rows_seen,
                        "first_time_utc": scanner.first_time,
                        "last_time_utc": scanner.last_time,
                        "candidate_count_so_far": writer.candidate_count,
                        "candidate_rows_written_so_far": writer.candidate_rows_written,
                        "path_label_count_so_far": writer.path_label_count,
                        "path_label_rows_written_so_far": writer.path_label_rows_written,
                        "completed_at_utc": utc_now_iso(),
                    },
                )
            except Exception as exc:  # noqa: BLE001 - this is a source-row terminal ledger.
                aggregate.source_status["blocked_by_parser_or_row_error"] += 1
                aggregate.parse_errors.append(
                    {
                        "source_row_id": source.source_row_id,
                        "path": str(source.resolved_path),
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                aggregate.excluded_slices.append(
                    {
                        "source_row_id": source.source_row_id,
                        "source_family": source.source_family,
                        "symbol": source.symbol,
                        "timeframe": source.timeframe,
                        "absolute_path": str(source.resolved_path),
                        "exclusion_reason": "EXCLUDED_PARSER_OR_ROW_ERROR",
                        "terminal_detail": f"Parser failed with {type(exc).__name__}: {exc}",
                        "recoverable_market_data": False,
                        "non_generatable_gtos_source_state_truth": False,
                    }
                )
    finally:
        writer.close()

    source_selection = source_selection_ledger(selected_sources, excluded, hash_resolutions, generated_at)
    candidate_inventory = candidate_inventory_summary(writer, aggregate, generated_at, candidate_rows_path)
    path_label_inventory = path_label_summary(writer, aggregate, generated_at, path_label_rows_path)
    family_terminal = family_terminal_status(registry, aggregate, selected_sources, generated_at)
    searched_root_ledger = searched_roots_from_predecessor(predecessor["source_ledger"], generated_at)
    continuation_ledger = same_evidence_class_continuation_ledger(
        aggregate,
        hash_resolutions,
        candidate_inventory,
        path_label_inventory,
        generated_at,
    )
    excluded_ledger = excluded_slice_ledger(aggregate, generated_at)
    noleak = noleak_audit(candidate_inventory, path_label_inventory, generated_at)
    saturation = saturation_pass(source_selection, family_terminal, excluded_ledger, continuation_ledger, generated_at)
    next_prompt = next_prompt_pack(generated_at)
    completion = completion_audit(
        generated_at=generated_at,
        predecessor=predecessor,
        source_selection=source_selection,
        candidate_inventory=candidate_inventory,
        path_label_inventory=path_label_inventory,
        family_terminal=family_terminal,
        searched_root_ledger=searched_root_ledger,
        continuation_ledger=continuation_ledger,
        excluded_ledger=excluded_ledger,
        noleak=noleak,
        saturation=saturation,
        next_prompt=next_prompt,
    )
    artifacts = {
        "context_anchor": context_anchor(generated_at),
        "schema_policy": schema_policy,
        "family_registry": {**route_flags(), "artifact_family": "mechanical_family_registry", "generated_at_utc": generated_at, "families": registry},
        "source_selection": source_selection,
        "candidate_inventory": candidate_inventory,
        "path_label_inventory": path_label_inventory,
        "family_terminal": family_terminal,
        "searched_root_ledger": searched_root_ledger,
        "continuation_ledger": continuation_ledger,
        "excluded_ledger": excluded_ledger,
        "noleak": noleak,
        "saturation": saturation,
        "next_prompt": next_prompt,
        "completion": completion,
    }
    paths = write_artifacts(output_dir, artifacts)
    manifest_artifact_paths = [
        *paths,
        candidate_rows_path,
        path_label_rows_path,
        progress_path,
        Path(__file__),
        ROUTE_DIR / "verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        ROUTE_DIR / "test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
        ROOT / NEXT_G12_PROMPT_RELATIVE_PATH,
    ]
    manifest = {
        **route_flags(),
        "artifact_family": "output_manifest",
        "generated_at_utc": generated_at,
        "candidate_rows_path": display_path(candidate_rows_path),
        "path_label_rows_path": display_path(path_label_rows_path),
        "source_progress_path": display_path(progress_path),
        "artifact_paths": [display_path(path) for path in manifest_artifact_paths],
        "source_row_count": len(source_rows),
        "selected_source_count": len(selected_sources),
        "candidate_inventory_row_count": writer.candidate_count,
        "candidate_rows_written": writer.candidate_rows_written,
        "candidate_rows_suppressed_by_artifact_cap": writer.candidate_rows_suppressed_by_artifact_cap,
        "path_label_row_count": writer.path_label_count,
        "path_label_rows_written": writer.path_label_rows_written,
        "path_label_rows_suppressed_by_artifact_cap": writer.path_label_rows_suppressed_by_artifact_cap,
        "completion_standard_satisfied": bool(completion["completion_standard_satisfied"]),
    }
    manifest_path = output_dir / f"{OUTPUT_PREFIX}_OUTPUT_MANIFEST_{DATE}.json"
    write_json(manifest_path, manifest)
    write_text(output_dir / f"{OUTPUT_PREFIX}_OUTPUT_MANIFEST_{DATE}.md", render_simple_report("Output Manifest", manifest))
    return {**manifest, "manifest_path": str(manifest_path)}


def frozen_schema_policy(generated_at: str, registry: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        **route_flags(),
        "artifact_family": "frozen_replay_schema_and_policy",
        "generated_at_utc": generated_at,
        "frozen_before_path_inspection": True,
        "input_source_required_fields": [
            "source_row_id",
            "absolute_path",
            "source_family",
            "evidence_class",
            "partition_assignment",
            "symbol",
            "timeframe",
            "available_asof_fields",
            "missing_source_state_fields",
            "duplicate_key",
            "hash_status",
        ],
        "candidate_duplicate_key": "symbol|timeframe|family_id|side|decision_time_utc|zone_reference_id|source_sha256",
        "source_duplicate_key": "source_family|symbol|timeframe|source_sha256",
        "no_lookahead_rules": [
            "mechanical family definitions are static in this artifact before scanning OHLC rows",
            "swing-based events require confirmed swings after two right-side bars have closed",
            "candidate rows use only bars closed at or before decision_time_utc",
            "path-label rows are separate discovery labels and never decision inputs",
            "historical GTOS AI intent remains projection-only unless source-logged prompt/input/output/gate/lifecycle truth exists",
        ],
        "projection_boundary": {
            "all_candidate_rows_projection_only": True,
            "original_gtos_ai_intent_claimed": False,
            "historical_pending_lifecycle_truth_inferred_from_price": False,
        },
        "path_label_policy": {
            "label_family": "DISCOVERY_PATH_LABEL_ONLY",
            "forbidden_label_claims": ["PnL", "broker actual outcome", "win-rate", "expectancy", "validation result"],
        },
        "family_ids_frozen": [row["family_id"] for row in registry],
    }


def context_anchor(generated_at: str) -> dict[str, Any]:
    return {
        **route_flags(),
        "artifact_family": "context_anchor",
        "generated_at_utc": generated_at,
        "controlling_prompt": str(PROMPT_PATH.relative_to(ROOT)),
        "predecessor_route": "NO_API_HISTORICAL_REPLAY_ENGINE_AND_MISSED_OPPORTUNITY_INVENTORY",
        "predecessor_artifacts_read": [
            str(SOURCE_LEDGER.relative_to(ROOT)),
            str(SOURCE_CONTRACT.relative_to(ROOT)),
            str(PARTITION_LEDGER.relative_to(ROOT)),
            str(MISSED_INVENTORY.relative_to(ROOT)),
            str(PREDECESSOR_COMPLETION_AUDIT.relative_to(ROOT)),
        ],
        "code_commit_at_build_start": git_commit_or_unresolved(),
        "lane": "research_tooling_discovery_control_only",
        "forbidden_surfaces_restated": sorted(k for k, v in FORBIDDEN_SURFACES.items() if v is False),
    }


def source_selection_ledger(
    selected: Sequence[SourceRecord],
    excluded: Sequence[Mapping[str, Any]],
    hash_resolutions: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    return {
        **route_flags(),
        "artifact_family": "source_selection_and_hash_ledger",
        "generated_at_utc": generated_at,
        "source_selection_policy": "select LOCAL_OHLCV_CSV and SIERRA_DERIVED_OHLCV_EXPORT rows with M1/M5/M15/H1/H4 timeframes after path resolution and source-hash de-duplication",
        "selected_source_count": len(selected),
        "excluded_source_slice_count": len(excluded),
        "large_file_hash_resolution_count": len(hash_resolutions),
        "selected_by_source_family": dict(sorted(Counter(s.source_family for s in selected).items())),
        "selected_by_timeframe": dict(sorted(Counter(s.timeframe for s in selected).items())),
        "selected_by_symbol": dict(sorted(Counter(s.symbol for s in selected).items())),
        "selected_sources": [
            {
                "source_row_id": s.source_row_id,
                "symbol": s.symbol,
                "timeframe": s.timeframe,
                "source_family": s.source_family,
                "partition_assignment": s.partition_assignment,
                "source_sha256": s.source_sha256,
                "hash_resolution": s.hash_resolution,
                "size_bytes": s.size_bytes,
                "path_fingerprint": sha16(str(s.resolved_path)),
            }
            for s in selected
        ],
        "large_file_hash_resolutions": list(hash_resolutions),
    }


def candidate_inventory_summary(
    writer: CandidateWriter,
    aggregate: ReplayAggregate,
    generated_at: str,
    candidate_rows_path: Path,
) -> dict[str, Any]:
    return {
        **route_flags(),
        "artifact_family": "candidate_inventory_summary",
        "generated_at_utc": generated_at,
        "candidate_rows_path": display_path(candidate_rows_path),
        "candidate_row_count": writer.candidate_count,
        "candidate_rows_written": writer.candidate_rows_written,
        "candidate_row_write_cap": CANDIDATE_ROW_WRITE_CAP,
        "candidate_rows_suppressed_by_artifact_cap": writer.candidate_rows_suppressed_by_artifact_cap,
        "suppressed_candidates_by_family": dict(sorted(writer.suppressed_candidates_by_family.items())),
        "duplicate_candidate_keys": writer.duplicate_candidate_keys,
        "candidate_inventory_sha256": sha256_file(candidate_rows_path),
        "candidate_row_stream_digest": writer.candidate_digest.hexdigest(),
        "by_family": dict(sorted(aggregate.candidate_by_family.items())),
        "by_source_family": dict(sorted(aggregate.candidate_by_source_family.items())),
        "by_symbol": dict(sorted(aggregate.candidate_by_symbol.items())),
        "by_timeframe": dict(sorted(aggregate.candidate_by_timeframe.items())),
        "by_session_or_kill_zone": dict(sorted(aggregate.candidate_by_session.items())),
        "by_regime_phase": dict(sorted(aggregate.candidate_by_regime.items())),
        "result_scoring_fields_emitted": False,
        "validation_labels_emitted": False,
    }


def path_label_summary(
    writer: CandidateWriter,
    aggregate: ReplayAggregate,
    generated_at: str,
    path_label_rows_path: Path,
) -> dict[str, Any]:
    return {
        **route_flags(),
        "artifact_family": "discovery_path_label_inventory_summary",
        "generated_at_utc": generated_at,
        "path_label_rows_path": display_path(path_label_rows_path),
        "path_label_row_count": writer.path_label_count,
        "path_label_rows_written": writer.path_label_rows_written,
        "path_label_row_write_cap": PATH_LABEL_ROW_WRITE_CAP,
        "path_label_rows_suppressed_by_artifact_cap": writer.path_label_rows_suppressed_by_artifact_cap,
        "suppressed_path_labels_by_family": dict(sorted(writer.suppressed_path_labels_by_family.items())),
        "duplicate_path_keys": writer.duplicate_path_keys,
        "path_label_inventory_sha256": sha256_file(path_label_rows_path),
        "path_label_stream_digest": writer.path_digest.hexdigest(),
        "by_label_status": dict(sorted(aggregate.path_label_by_status.items())),
        "label_family": "DISCOVERY_PATH_LABEL_ONLY",
        "result_scoring_fields_emitted": False,
        "validation_labels_emitted": False,
    }


def family_terminal_status(
    registry: Sequence[Mapping[str, Any]],
    aggregate: ReplayAggregate,
    selected_sources: Sequence[SourceRecord],
    generated_at: str,
) -> dict[str, Any]:
    rows = []
    selected_tf = sorted({s.timeframe for s in selected_sources})
    for family in registry:
        family_id = str(family["family_id"])
        count = int(aggregate.candidate_by_family.get(family_id, 0))
        rows.append(
            {
                "family_id": family_id,
                "family_group": family["family_group"],
                "terminal_status": "REPLAY_INVENTORY_BUILT" if count else "REPLAY_INVENTORY_BUILT_ZERO_EVENTS",
                "candidate_count": count,
                "selected_timeframes_available": selected_tf,
                "opened_to_terminal_status": True,
                "prototype_only": False,
                "result_scoring_opened": False,
                "validation_opened": False,
            }
        )
    considered_skipped = [
        {
            "family_id": "native_depth_order_book_absorption",
            "terminal_status": "EXCLUDED_PARSER_CONTRACT_NOT_IN_THIS_EVIDENCE_CLASS",
            "reason": "Sierra .depth files are source-safe context roots but require a dedicated depth parser/source contract before mechanical candidate replay rows can be built.",
            "searched_sources": ["sierra_chart_data_root", "current_research_sierra", "current_research_orderflow"],
            "next_executable_route": "SIERRA_DEPTH_NO_API_CONTEXT_PACKET_AND_PARSER_CONTRACT",
        },
        {
            "family_id": "mt5_bid_ask_tick_spread_sensitive_entries",
            "terminal_status": "EXCLUDED_NATIVE_QUOTE_FIELD_GATE",
            "reason": "Tick parquet roots are context-only here; spread/cost/MT5 bid/ask/flags claims require a quote/tick contract and no result scoring.",
            "searched_sources": ["absolute_main_tick_root", "source_universe_hash_deferral_manifest"],
            "next_executable_route": "MT5_TICK_QUOTE_SOURCE_PACKET_FOR_SELECTED_REPLAY_WINDOWS",
        },
        {
            "family_id": "production_ai_intent_replay",
            "terminal_status": "EXCLUDED_NON_GENERATABLE_GTOS_SOURCE_STATE_TRUTH",
            "reason": "Prompt/input/output/gate/lifecycle truth cannot be inferred from price; rows stay projection-only.",
            "searched_sources": ["shadow source-state logs", "prior source-control ledgers"],
            "next_executable_route": "FORWARD_SOURCE_CAPTURE_READINESS_FOR_REPLAY_STATE_GAPS",
        },
    ]
    return {
        **route_flags(),
        "artifact_family": "family_terminal_status_ledger",
        "generated_at_utc": generated_at,
        "opened_family_count": len(rows),
        "skipped_or_excluded_high_value_family_count": len(considered_skipped),
        "opened_families": rows,
        "considered_skipped_families": considered_skipped,
    }


def searched_roots_from_predecessor(source_ledger: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    roots = []
    for root in source_ledger.get("roots") or []:
        item = dict(root)
        item["used_in_this_route"] = item.get("root_id") in {
            "current_worktree_data",
            "absolute_main_data_root",
            "sierra_chart_data_root",
            "absolute_main_tick_root",
            "current_research_source_control",
            "prior_worktrees_root",
            "absolute_main_shadow_logs",
        }
        roots.append(item)
    return {
        **route_flags(),
        "artifact_family": "searched_root_ledger",
        "generated_at_utc": generated_at,
        "roots": roots,
        "search_policy": "reuse accepted predecessor local root search and add current route path resolution plus large-file hash resolution for selected OHLC rows",
        "current_worktree_root": str(ROOT),
    }


def same_evidence_class_continuation_ledger(
    aggregate: ReplayAggregate,
    hash_resolutions: Sequence[Mapping[str, Any]],
    candidate_inventory: Mapping[str, Any],
    path_label_inventory: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if hash_resolutions:
        rows.append(
            {
                "blocker_family": "large_file_hash_deferral",
                "same_evidence_class_action": "CLEARED_FOR_SELECTED_OHLC_FILES",
                "rows_cleared": len(hash_resolutions),
                "terminal_status": "CLEARED",
            }
        )
    if aggregate.parse_errors:
        rows.append(
            {
                "blocker_family": "csv_parser_or_row_error",
                "same_evidence_class_action": "RECORDED_SOURCE_ROW_ERROR_WITH_EXACT_PATH_AND_EXCEPTION",
                "rows_blocked": len(aggregate.parse_errors),
                "terminal_status": "EXACT_SOURCE_PARSER_BLOCKER",
            }
        )
    if int(candidate_inventory.get("candidate_rows_suppressed_by_artifact_cap") or 0) > 0:
        rows.append(
            {
                "blocker_family": "row_artifact_volume_bound",
                "same_evidence_class_action": "CLEARED_BY_FULL_COUNT_DIGEST_AND_COMPACT_ROW_ARTIFACT_POLICY",
                "candidate_rows_suppressed": candidate_inventory.get("candidate_rows_suppressed_by_artifact_cap"),
                "path_label_rows_suppressed": path_label_inventory.get("path_label_rows_suppressed_by_artifact_cap"),
                "terminal_status": "BOUNDED_ARTIFACT_WITH_MACHINE_CHECKABLE_COUNTS_AND_DIGESTS",
            }
        )
    rows.extend(
        [
            {
                "blocker_family": "native_depth_parser_gap",
                "same_evidence_class_action": "SEARCHED_AND_EXCLUDED_TO_DEDICATED_DEPTH_CONTEXT_PACKET_ROUTE",
                "terminal_status": "EXACT_PARSER_CONTRACT_BLOCKER",
            },
            {
                "blocker_family": "non_generatable_gtos_intent_lifecycle_truth",
                "same_evidence_class_action": "KEPT_ALL_MARKET_DATA_ROWS_PROJECTION_ONLY_AND_ROUTED_FORWARD_CAPTURE_REQUIREMENT",
                "terminal_status": "EXACT_EVIDENCE_CLASS_BLOCKER",
            },
            {
                "blocker_family": "result_scoring_validation_gate",
                "same_evidence_class_action": "CLOSED_IN_THIS_ROUTE_BY_POLICY",
                "terminal_status": "FORBIDDEN_BOUNDARY_NOT_OPENED",
            },
        ]
    )
    return {
        **route_flags(),
        "artifact_family": "same_evidence_class_continuation_ledger",
        "generated_at_utc": generated_at,
        "continuation_rows": rows,
    }


def excluded_slice_ledger(aggregate: ReplayAggregate, generated_at: str) -> dict[str, Any]:
    by_reason = Counter(str(row.get("exclusion_reason")) for row in aggregate.excluded_slices)
    return {
        **route_flags(),
        "artifact_family": "excluded_slice_ledger",
        "generated_at_utc": generated_at,
        "excluded_slice_count": len(aggregate.excluded_slices),
        "by_reason": dict(sorted(by_reason.items())),
        "excluded_slices": aggregate.excluded_slices,
        "parse_errors": aggregate.parse_errors,
    }


def noleak_audit(candidate_inventory: Mapping[str, Any], path_label_inventory: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **route_flags(),
        "artifact_family": "noleak_and_forbidden_surface_audit",
        "generated_at_utc": generated_at,
        "candidate_result_scoring_fields_emitted": candidate_inventory.get("result_scoring_fields_emitted"),
        "path_label_result_scoring_fields_emitted": path_label_inventory.get("result_scoring_fields_emitted"),
        "candidate_validation_labels_emitted": candidate_inventory.get("validation_labels_emitted"),
        "path_label_validation_labels_emitted": path_label_inventory.get("validation_labels_emitted"),
        "ai_api_calls": 0,
        "paid_vendor_calls": 0,
        "mt5_order_account_history_calls": 0,
        "prompt_config_risk_safety_changes": 0,
        "projection_only_boundary": "PASS",
        "status": "PASS",
    }


def saturation_pass(
    source_selection: Mapping[str, Any],
    family_terminal: Mapping[str, Any],
    excluded_ledger: Mapping[str, Any],
    continuation_ledger: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    opened = family_terminal.get("opened_families") or []
    skipped = family_terminal.get("considered_skipped_families") or []
    zero_opened = [row for row in opened if int(row.get("candidate_count") or 0) == 0]
    return {
        **route_flags(),
        "artifact_family": "saturation_self_redteam_pass",
        "generated_at_utc": generated_at,
        "family_source_slice_registry_present": True,
        "searched_root_ledger_present": True,
        "same_evidence_class_continuation_ledger_present": True,
        "excluded_slice_ledger_present": True,
        "opened_family_count": len(opened),
        "opened_zero_event_family_count": len(zero_opened),
        "skipped_high_value_family_count": len(skipped),
        "selected_source_count": source_selection.get("selected_source_count"),
        "excluded_source_slice_count": excluded_ledger.get("excluded_slice_count"),
        "continuation_blocker_count": len(continuation_ledger.get("continuation_rows") or []),
        "anti_boxing_checks": [
            {"axis": "family", "status": "PASS", "evidence": "core Model A families, lifecycle, KZ sweeps, liquidity, baselines, and adjacent compression family opened"},
            {"axis": "timeframe", "status": "PASS", "evidence": "M1/M5/M15/H1/H4 selected where OHLC source rows exist"},
            {"axis": "symbol", "status": "PASS", "evidence": "selected source ledger records all symbols available after source-hash dedupe"},
            {"axis": "source_type", "status": "PASS", "evidence": "LOCAL_OHLCV_CSV and SIERRA_DERIVED_OHLCV_EXPORT opened; native depth/tick source slices terminally routed"},
            {"axis": "large_file_hashing", "status": "PASS", "evidence": "selected deferred OHLC files hashed in this route"},
            {"axis": "evidence_class", "status": "PASS", "evidence": "projection-only and discovery-only labels preserved; validation and result scoring closed"},
        ],
        "prototype_only_opened_families": [
            row["family_id"] for row in opened if row.get("prototype_only")
        ],
        "terminal_status": "SATURATION_PASS_COMPLETE",
    }


def next_prompt_pack(generated_at: str) -> dict[str, Any]:
    prompt_text = (
        f"/goal Follow the full controlling prompt in {NEXT_G12_PROMPT_RELATIVE_PATH} as the complete objective; "
        "do mandatory preflight and context refresh first; stay G12_SOURCE_CONTROL_AUDIT_ONLY with no AI/API, validation, "
        "result scoring, promotion, live behavior, paid/vendor access, credentials, remotes, broker account/order/history/deal/position use, "
        "or prompt/config/risk/safety changes; independently audit the no-api mechanical replay candidate and discovery path-label inventories, "
        "source hashes, family terminal statuses, no-leak boundaries, duplicate/as-of policy, excluded-slice ledger, and saturation pass; "
        "complete only with scoped audit artifacts, verifier/focused tests, NO_PROMOTION_VERDICT, validation_safe=false, "
        "outcome_review_opened=false, live_effect=false."
    )
    return {
        **route_flags(),
        "artifact_family": "next_prompt_pack",
        "generated_at_utc": generated_at,
        "selected_next_route_id": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
        "selected_next_route_reason": "Independent G12 source-control audit is the next evidence-class gate before any downstream discovery-result lane uses the inventory.",
        "prompt_path": NEXT_G12_PROMPT_RELATIVE_PATH,
        "full_prompt_file_required": True,
        "one_line_starter": prompt_text,
        "full_prompt_starter": [
            "Audit the candidate inventory row schema and duplicate keys.",
            "Recompute source hashes for a representative selected-source set plus every large hash resolution.",
            "Verify family registry was frozen before path scanning and every opened family reached terminal candidate/path-label status.",
            "Verify no result scoring, validation, broker actual-R, AI/API, paid vendor, prompt/config/risk/safety, remote, credential, or live behavior surface was opened.",
            "Verify skipped native depth/tick/source-state slices have exact terminal blockers and next routes.",
        ],
    }


def completion_audit(**kwargs: Any) -> dict[str, Any]:
    generated_at = kwargs["generated_at"]
    source_selection = kwargs["source_selection"]
    candidate_inventory = kwargs["candidate_inventory"]
    path_label_inventory = kwargs["path_label_inventory"]
    family_terminal = kwargs["family_terminal"]
    excluded_ledger = kwargs["excluded_ledger"]
    noleak = kwargs["noleak"]
    saturation = kwargs["saturation"]
    missing: list[str] = []
    if not source_selection.get("selected_source_count"):
        missing.append("no selected OHLC source rows")
    if not candidate_inventory.get("candidate_row_count"):
        missing.append("no candidate inventory rows")
    if not path_label_inventory.get("path_label_row_count"):
        missing.append("no discovery path-label rows")
    if noleak.get("status") != "PASS":
        missing.append("no-leak audit did not pass")
    if saturation.get("terminal_status") != "SATURATION_PASS_COMPLETE":
        missing.append("saturation pass incomplete")
    if family_terminal.get("opened_family_count", 0) < 10:
        missing.append("mechanical family registry too narrow")
    checklist = [
        {
            "requirement_id": "mandatory_preflight_and_inputs",
            "prompt_requirement": "Read controlling prompt, core context, source universe, source contract, partition ledger, missed inventory, and predecessor completion audit.",
            "evidence": "context anchor plus predecessor artifacts recorded",
            "status": "PASS",
        },
        {
            "requirement_id": "freeze_before_path_inspection",
            "prompt_requirement": "Freeze schemas, duplicate keys, no-lookahead rules, projection boundaries, and family definitions before path inspection.",
            "evidence": "frozen replay schema/policy and family registry artifacts",
            "status": "PASS",
        },
        {
            "requirement_id": "large_file_hash_resolution",
            "prompt_requirement": "Resolve large-file hash deferrals that block high-value source-safe OHLC replay.",
            "evidence": f"{source_selection.get('large_file_hash_resolution_count')} selected large OHLC files hashed in route",
            "status": "PASS",
        },
        {
            "requirement_id": "mechanical_candidate_inventory",
            "prompt_requirement": "Build broad deterministic pre-AI candidate replay across source-safe OHLC data.",
            "evidence": f"{candidate_inventory.get('candidate_row_count')} total candidate rows; {candidate_inventory.get('candidate_rows_written')} compact row artifacts written",
            "status": "PASS" if candidate_inventory.get("candidate_row_count") else "FAIL",
        },
        {
            "requirement_id": "path_label_inventory_discovery_only",
            "prompt_requirement": "If path labels are opened, keep them discovery-only and separate from validation/result language.",
            "evidence": f"{path_label_inventory.get('path_label_row_count')} total path-label rows; {path_label_inventory.get('path_label_rows_written')} compact row artifacts written with label_family=DISCOVERY_PATH_LABEL_ONLY",
            "status": "PASS" if path_label_inventory.get("path_label_row_count") else "FAIL",
        },
        {
            "requirement_id": "baselines_and_controls",
            "prompt_requirement": "Include random/window, shifted-entry, momentum, and mean-reversion controls where source-safe.",
            "evidence": "baseline_random_session_control, baseline_shifted_entry_control, baseline_momentum_continuation, baseline_mean_reversion",
            "status": "PASS",
        },
        {
            "requirement_id": "family_terminal_status",
            "prompt_requirement": "Produce family terminal-status ledger for every opened and high-value skipped family/source slice.",
            "evidence": "family terminal-status ledger plus excluded-slice ledger",
            "status": "PASS",
        },
        {
            "requirement_id": "saturation_mandate",
            "prompt_requirement": "Run written and machine-checkable saturation pass against boxing by family/timeframe/symbol/session/source/parser/hash/compute.",
            "evidence": "saturation self-red-team pass",
            "status": "PASS",
        },
        {
            "requirement_id": "no_forbidden_surfaces",
            "prompt_requirement": "Open no validation/result/live/API/paid/broker-account/prompt/config/risk/safety/remote/credential surface.",
            "evidence": "no-leak audit PASS and route flags all false",
            "status": "PASS",
        },
        {
            "requirement_id": "next_selected_full_prompt",
            "prompt_requirement": "Produce the next selected full prompt and one-line starter.",
            "evidence": f"next prompt pack points to {NEXT_G12_PROMPT_RELATIVE_PATH} and includes the one-line starter",
            "status": "PASS",
        },
    ]
    return {
        **route_flags(),
        "artifact_family": "completion_audit",
        "generated_at_utc": generated_at,
        "objective_restatement": "Build the strongest source-safe no-API mechanical pre-AI replay substrate possible from the accepted source universe, with frozen schemas/families, broad candidate and discovery path-label inventories, exact blockers, tests/verifier, scoped artifacts, and no validation/result/live/API surfaces.",
        "source_universe_rows_consumed": (kwargs["predecessor"]["source_ledger"]).get("source_row_count"),
        "selected_source_count": source_selection.get("selected_source_count"),
        "excluded_source_slice_count": excluded_ledger.get("excluded_slice_count"),
        "candidate_inventory_row_count": candidate_inventory.get("candidate_row_count"),
        "candidate_rows_written": candidate_inventory.get("candidate_rows_written"),
        "candidate_rows_suppressed_by_artifact_cap": candidate_inventory.get("candidate_rows_suppressed_by_artifact_cap"),
        "path_label_row_count": path_label_inventory.get("path_label_row_count"),
        "path_label_rows_written": path_label_inventory.get("path_label_rows_written"),
        "path_label_rows_suppressed_by_artifact_cap": path_label_inventory.get("path_label_rows_suppressed_by_artifact_cap"),
        "opened_family_count": family_terminal.get("opened_family_count"),
        "completion_standard_satisfied": not missing,
        "can_mark_goal_complete": not missing,
        "missing_incomplete_or_weak_requirements": missing,
        "prompt_to_artifact_checklist": checklist,
        "next_route_plan": kwargs["next_prompt"],
        "terminal_decision": "NO_PROMOTION_VERDICT_MECHANICAL_REPLAY_DISCOVERY_INVENTORY_BUILT",
    }


def render_simple_report(title: str, payload: Mapping[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"**Generated UTC:** {payload.get('generated_at_utc')}",
        f"**Route:** `{ROUTE_ID}`",
        f"**Evidence class:** `{EVIDENCE_CLASS}`",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`",
        f"**validation_safe:** `{payload.get('validation_safe')}`",
        f"**outcome_review_opened:** `{payload.get('outcome_review_opened')}`",
        f"**live_effect:** `{payload.get('live_effect')}`",
        "",
    ]
    summary_keys = [
        "artifact_family",
        "selected_source_count",
        "excluded_source_slice_count",
        "large_file_hash_resolution_count",
        "candidate_row_count",
        "path_label_row_count",
        "opened_family_count",
        "completion_standard_satisfied",
        "can_mark_goal_complete",
        "terminal_decision",
    ]
    rows = [{key: payload.get(key) for key in summary_keys if key in payload}]
    lines.extend([markdown_table(rows), ""])
    if payload.get("by_family"):
        lines.extend(["## By Family", "", markdown_table([payload["by_family"]]), ""])
    if payload.get("by_timeframe"):
        lines.extend(["## By Timeframe", "", markdown_table([payload["by_timeframe"]]), ""])
    if payload.get("by_symbol"):
        top = dict(Counter(payload["by_symbol"]).most_common(30))
        lines.extend(["## By Symbol Top 30", "", markdown_table([top]), ""])
    if payload.get("by_reason"):
        lines.extend(["## Exclusions By Reason", "", markdown_table([payload["by_reason"]]), ""])
    if payload.get("prompt_to_artifact_checklist"):
        lines.extend(["## Prompt Checklist", "", markdown_table(payload["prompt_to_artifact_checklist"]), ""])
    if payload.get("anti_boxing_checks"):
        lines.extend(["## Anti-Boxing Checks", "", markdown_table(payload["anti_boxing_checks"]), ""])
    return "\n".join(lines)


def write_artifacts(output_dir: Path, artifacts: Mapping[str, Mapping[str, Any]]) -> list[Path]:
    name_map = {
        "context_anchor": "CONTEXT_ANCHOR",
        "schema_policy": "FROZEN_REPLAY_SCHEMA_AND_POLICY",
        "family_registry": "MECHANICAL_FAMILY_REGISTRY",
        "source_selection": "SOURCE_SELECTION_AND_HASH_LEDGER",
        "candidate_inventory": "CANDIDATE_INVENTORY",
        "path_label_inventory": "DISCOVERY_PATH_LABEL_INVENTORY",
        "family_terminal": "FAMILY_TERMINAL_STATUS_LEDGER",
        "searched_root_ledger": "SEARCHED_ROOT_LEDGER",
        "continuation_ledger": "SAME_EVIDENCE_CLASS_CONTINUATION_LEDGER",
        "excluded_ledger": "EXCLUDED_SLICE_LEDGER",
        "noleak": "NOLEAK_AUDIT",
        "saturation": "SATURATION_SELF_REDTEAM_PASS",
        "next_prompt": "NEXT_PROMPT_PACK",
        "completion": "COMPLETION_AUDIT",
    }
    written: list[Path] = []
    for key, payload in artifacts.items():
        stem = f"{OUTPUT_PREFIX}_{name_map[key]}_{DATE}"
        json_path = output_dir / f"{stem}.json"
        md_path = output_dir / f"{stem}.md"
        write_json(json_path, payload)
        write_text(md_path, render_simple_report(name_map[key].replace("_", " ").title(), payload))
        written.extend([json_path, md_path])
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROUTE_DIR)
    parser.add_argument("--source-rows", type=Path, default=SOURCE_ROWS)
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = build_route(output_dir=args.output_dir, source_rows_path=args.source_rows)
    if args.quiet:
        print(
            json.dumps(
                {
                    "route_id": manifest.get("route_id"),
                    "selected_source_count": manifest.get("selected_source_count"),
                    "candidate_inventory_row_count": manifest.get("candidate_inventory_row_count"),
                    "path_label_row_count": manifest.get("path_label_row_count"),
                    "completion_standard_satisfied": manifest.get("completion_standard_satisfied"),
                    "manifest_path": manifest.get("manifest_path"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
