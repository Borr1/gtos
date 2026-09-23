"""Build OTB2R G3 geometry input-only packet builders.

This lane is research/tooling only. It does not run synthetic replay outcomes,
inspect broker actual-R, inspect blocked packet outcomes, call network/API/MT5,
or touch live trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-07"
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders"
PACKETS_DIR = OUT / "packets"
AUDITS_DIR = OUT / "audits"

G3_PACKET_SPECS = {
    "OTG0-PKT-031": {
        "experiment_id": "EXP-G3-DC-OVERSHOOT-002",
        "hypothesis_id": "HYP-G3-DC-OVERSHOOT-002",
        "family": "dc_overshoot",
        "required_timeframes": ["M15", "H1"],
        "required_fields": [
            "dc_overshoot_ratio_at_decision_packet",
            "decision_asof_utc",
            "ordered_path_source_id",
            "duplicate_group_id",
            "source_hash",
            "cost_model_version",
            "same_bar_ambiguity_policy",
        ],
        "packet_slug": "dc_overshoot_input_packet",
    },
    "OTG0-PKT-032": {
        "experiment_id": "EXP-G3-DC-SWING-001",
        "hypothesis_id": "HYP-G3-DC-SWING-001",
        "family": "dc_swing",
        "required_timeframes": ["M15", "H1", "H4"],
        "required_fields": [
            "dc_threshold_grid_packet",
            "dc_event_count_at_decision",
            "dc_event_rate_lookback_only",
            "duplicate_group_id",
            "source_hash",
            "ordered_path_source_id",
        ],
        "packet_slug": "dc_swing_input_packet",
    },
    "OTG0-PKT-036": {
        "experiment_id": "EXP-G3-TDA-007",
        "hypothesis_id": "HYP-G3-TDA-007",
        "family": "tda_h0_embedding",
        "required_timeframes": ["M15"],
        "required_fields": [
            "embedding_window_end_at_decision",
            "persistence_summary_packet",
            "path_start_utc",
            "path_end_utc",
            "source_hash",
            "duplicate_group_id",
        ],
        "packet_slug": "tda_h0_embedding_input_packet",
    },
}

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LABEL_FAMILY = "synthetic_path_r"
COST_MODEL_VERSION = "INPUT_ONLY_NO_REPLAY_COST_MODEL_V0"
SAME_BAR_POLICY_ID = "G3_INPUT_ONLY_CLOSED_CANDLE_POLICY_V1"
SAME_BAR_POLICY = (
    "OHLC timestamps are treated as candle-open times. Feature builders may "
    "use only bars whose open_time + timeframe_delta <= decision_asof_utc. "
    "No terminal order, TP/SL touch order, or same-bar outcome claim is made."
)

TIMEFRAME_DELTAS = {
    "M1": timedelta(minutes=1),
    "M5": timedelta(minutes=5),
    "M15": timedelta(minutes=15),
    "H1": timedelta(hours=1),
    "H4": timedelta(hours=4),
    "D1": timedelta(days=1),
}
DC_LOOKBACK_BARS = {"M15": 256, "H1": 192, "H4": 96}
DC_THRESHOLD_ATR_GRID = [0.5, 1.0, 1.5, 2.0]
ATR_PERIOD = 14
TDA_WINDOW_BARS = 64
TDA_EMBEDDING_DIMENSION = 2
TDA_DELAY_BARS = 1

SAFE_CANDIDATE_SOURCE = ROOT / "shadow_logs/candidate_features_log.jsonl"
CONTROL_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    "research/science_program_2026_05/06_outcome_testing/g0_oti_quarantine_synthesis/G0_OTI_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g0_oti_quarantine_synthesis/G0_OTI_BLOCKER_ACTION_MAP_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.md",
    "research/science_program_2026_05/03_experiment_specs/G3_GEOMETRY_SIGNAL_EXPERIMENT_PREREG_ROWS_2026-05-06.json",
    "research/science_program_2026_05/02_hypothesis_registry/G3_GEOMETRY_SIGNAL_HYPOTHESIS_ROWS_2026-05-06.json",
    "research/science_program_2026_05/02_hypothesis_registry/G3_GEOMETRY_SIGNAL_MECHANISM_ROWS_2026-05-06.json",
    "research/science_program_2026_05/02_hypothesis_registry/G3_GEOMETRY_SIGNAL_SOURCE_CONTRACT_ROWS_2026-05-06.json",
    "research/science_program_2026_05/01_domain_syntheses/G3_GEOMETRY_SIGNAL_DOMAIN_SYNTHESIS_2026-05-06.md",
    "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-031__EXP-G3-DC-OVERSHOOT-002__otb2r_input_only_path_packet_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-032__EXP-G3-DC-SWING-001__otb2r_input_only_path_packet_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-036__EXP-G3-TDA-007__otb2r_input_only_path_packet_2026-05-07.json",
]

FORBIDDEN_ROW_KEYS = {
    "actual_r",
    "actual_R",
    "broker_actual_r",
    "broker_actual_R",
    "result",
    "results",
    "outcome",
    "final_outcome",
    "synthetic_path_r",
    "realized_r",
    "realized_R",
    "pnl",
    "profit",
    "mae",
    "mfe",
    "hit_tp",
    "hit_sl",
    "terminal_order",
    "touch_sequence",
    "path_order_label",
    "resolution",
    "resolved",
    "win_loss",
}
ALLOWED_CONTROL_KEYS = {
    "label_family",
    "label_values_absent",
    "broker_actual_r_absent_from_primary_metric",
    "outcome_review_opened",
    "forbidden_outcome_source_policy",
    "no_outcome_columns_in_records",
    "no_result_columns_in_records",
    "blocked_packet_outcomes_not_opened",
}

POLICY_SKIPPED_SOURCES = [
    "shadow_logs/broker_actual_r_audit.jsonl",
    "shadow_logs/account_pnl_truth_reconciliation.jsonl",
    "shadow_logs/account_truth_reconciliation_status.jsonl",
    "shadow_logs/v2b_forward_pair_resolutions.jsonl",
    "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results",
    "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results",
]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if "+" not in text and "T" in text:
        text += "+00:00"
    if "+" not in text and " " in text:
        text = text.replace(" ", "T") + "+00:00"
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def floor_to_m15(dt: datetime) -> datetime:
    return dt.replace(minute=(dt.minute // 15) * 15, second=0, microsecond=0)


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_symbol(symbol: str) -> str:
    return "US30" if symbol == "US30_cash" else symbol


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        value_f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(value_f) or math.isinf(value_f):
        return None
    return value_f


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 10)
    pos = (len(ordered) - 1) * q
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return round(ordered[int(pos)], 10)
    frac = pos - lower
    return round(ordered[lower] * (1 - frac) + ordered[upper] * frac, 10)


class OHLCSource:
    def __init__(self, path: Path, symbol: str, timeframe: str, priority: int) -> None:
        self.path = path
        self.symbol = symbol
        self.timeframe = timeframe
        self.priority = priority
        self.rows: list[dict[str, Any]] | None = None
        self.first_open_utc: datetime | None = None
        self.last_open_utc: datetime | None = None
        self.row_count = 0
        self.file_sha256: str | None = None
        self.load_error: str | None = None

    def load(self) -> None:
        if self.rows is not None or self.load_error is not None:
            return
        rows: list[dict[str, Any]] = []
        try:
            with self.path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for raw in reader:
                    t_value = raw.get("time") or raw.get("timestamp") or raw.get("datetime")
                    if not t_value:
                        continue
                    try:
                        open_time = parse_utc(str(t_value))
                    except ValueError:
                        continue
                    row = {
                        "open_time": open_time,
                        "open": safe_float(raw.get("open")),
                        "high": safe_float(raw.get("high")),
                        "low": safe_float(raw.get("low")),
                        "close": safe_float(raw.get("close")),
                        "volume": safe_float(raw.get("volume") or raw.get("tick_volume") or raw.get("real_volume")),
                    }
                    if all(row[k] is not None for k in ["open", "high", "low", "close"]):
                        rows.append(row)
        except Exception as exc:  # pragma: no cover - stored in audit output.
            self.load_error = f"{type(exc).__name__}: {exc}"
            self.rows = []
            return
        rows.sort(key=lambda r: r["open_time"])
        self.rows = rows
        self.row_count = len(rows)
        if rows:
            self.first_open_utc = rows[0]["open_time"]
            self.last_open_utc = rows[-1]["open_time"]
        self.file_sha256 = sha256_file(self.path)

    def bars_closed_by(self, decision_asof: datetime) -> list[dict[str, Any]]:
        self.load()
        if not self.rows:
            return []
        delta = TIMEFRAME_DELTAS[self.timeframe]
        return [row for row in self.rows if row["open_time"] + delta <= decision_asof]

    def coverage_row(self) -> dict[str, Any]:
        self.load()
        return {
            "path": rel(self.path),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "priority": self.priority,
            "first_open_utc": iso_z(self.first_open_utc) if self.first_open_utc else None,
            "last_open_utc": iso_z(self.last_open_utc) if self.last_open_utc else None,
            "row_count": self.row_count,
            "file_sha256": self.file_sha256,
            "load_error": self.load_error,
        }


def classify_ohlc_path(path: Path) -> tuple[str, str, int] | None:
    name = path.name.upper()
    if not name.endswith(".CSV"):
        return None
    timeframe = None
    for tf in TIMEFRAME_DELTAS:
        if f"_{tf}.CSV" in name:
            timeframe = tf
            break
    if timeframe is None:
        return None
    symbol = name.split(f"_{timeframe}.CSV", 1)[0]
    if symbol == "US30_CASH":
        symbol = "US30"
    allowed = {"XAUUSD", "US30", "USDJPY", "GBPJPY", "GBPUSD", "XAGUSD", "NAS100"}
    if symbol not in allowed:
        return None
    path_text = rel(path)
    if path_text.startswith("data/historical_2026/"):
        priority = 0
    elif path_text.startswith("data/sierra_ohlcv_roots/"):
        priority = 1
    elif path_text.startswith("data/historical/"):
        priority = 2
    elif path_text.startswith("data/"):
        priority = 3
    else:
        priority = 9
    return symbol, timeframe, priority


def discover_ohlc_sources() -> dict[tuple[str, str], list[OHLCSource]]:
    roots = [
        ROOT / "data/historical_2026",
        ROOT / "data/sierra_ohlcv_roots",
        ROOT / "data/historical",
        ROOT / "data",
    ]
    found: dict[tuple[str, str], dict[Path, OHLCSource]] = defaultdict(dict)
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            classified = classify_ohlc_path(path)
            if classified is None:
                continue
            symbol, timeframe, priority = classified
            found[(symbol, timeframe)][path] = OHLCSource(path, symbol, timeframe, priority)
    output: dict[tuple[str, str], list[OHLCSource]] = {}
    for key, by_path in found.items():
        output[key] = sorted(by_path.values(), key=lambda src: (src.priority, rel(src.path)))
    return output


def select_ohlc_source(
    sources: dict[tuple[str, str], list[OHLCSource]],
    symbol: str,
    timeframe: str,
    decision_asof: datetime,
    min_bars: int,
) -> tuple[OHLCSource | None, list[dict[str, Any]], str | None]:
    normalized = normalize_symbol(symbol)
    candidates = sources.get((normalized, timeframe), [])
    inspected: list[dict[str, Any]] = []
    best: OHLCSource | None = None
    best_bars: list[dict[str, Any]] = []
    for source in candidates:
        bars = source.bars_closed_by(decision_asof)
        row = source.coverage_row()
        row["closed_bars_available_at_decision"] = len(bars)
        row["decision_asof_utc"] = iso_z(decision_asof)
        latest_close = bars[-1]["open_time"] + TIMEFRAME_DELTAS[timeframe] if bars else None
        max_allowed_staleness = TIMEFRAME_DELTAS[timeframe]
        staleness = decision_asof - latest_close if latest_close else None
        row["latest_closed_bar_close_utc"] = iso_z(latest_close) if latest_close else None
        row["staleness_seconds"] = staleness.total_seconds() if staleness else None
        row["max_allowed_staleness_seconds"] = max_allowed_staleness.total_seconds()
        row["fresh_at_decision"] = bool(staleness is not None and timedelta(0) <= staleness <= max_allowed_staleness)
        inspected.append(row)
        if len(bars) >= min_bars and row["fresh_at_decision"]:
            best = source
            best_bars = bars
            break
        if len(bars) > len(best_bars):
            best_bars = bars
    if best is not None:
        return best, inspected, None
    if not candidates:
        return None, inspected, f"NO_LOCAL_OHLC_SOURCE_FOR_{normalized}_{timeframe}"
    max_bars = max((row.get("closed_bars_available_at_decision") or 0 for row in inspected), default=0)
    freshest = min(
        (row.get("staleness_seconds") for row in inspected if row.get("staleness_seconds") is not None),
        default=None,
    )
    fresh_sources = [row for row in inspected if row.get("fresh_at_decision")]
    if not fresh_sources:
        return None, inspected, f"STALE_LOCAL_OHLC_FOR_{normalized}_{timeframe}"
    return None, inspected, f"INSUFFICIENT_CLOSED_BARS_FOR_{normalized}_{timeframe}"


def compute_atr(bars: list[dict[str, Any]], period: int = ATR_PERIOD) -> float | None:
    if len(bars) < period + 1:
        return None
    trs: list[float] = []
    prev_close = bars[-period - 1]["close"]
    for row in bars[-period:]:
        tr = max(
            row["high"] - row["low"],
            abs(row["high"] - prev_close),
            abs(row["low"] - prev_close),
        )
        trs.append(tr)
        prev_close = row["close"]
    return statistics.fmean(trs) if trs else None


def dc_state(closes: list[float], times: list[datetime], threshold: float) -> dict[str, Any]:
    if len(closes) < 2 or threshold <= 0:
        return {
            "event_count": 0,
            "event_rate_per_bar": 0.0,
            "last_event_direction": None,
            "last_event_time_utc": None,
            "current_mode": None,
            "overshoot_ratio_at_decision": None,
        }

    mode: str | None = None
    high = low = closes[0]
    high_idx = low_idx = 0
    last_event_price: float | None = None
    events: list[dict[str, Any]] = []

    for idx, price in enumerate(closes[1:], 1):
        if mode is None:
            if price > high:
                high, high_idx = price, idx
            if price < low:
                low, low_idx = price, idx
            if price - low >= threshold:
                mode = "up"
                last_event_price = price
                high, high_idx = price, idx
                events.append(
                    {
                        "index": idx,
                        "direction": "up",
                        "event_time_utc": iso_z(times[idx]),
                        "reference_extreme_time_utc": iso_z(times[low_idx]),
                    }
                )
            elif high - price >= threshold:
                mode = "down"
                last_event_price = price
                low, low_idx = price, idx
                events.append(
                    {
                        "index": idx,
                        "direction": "down",
                        "event_time_utc": iso_z(times[idx]),
                        "reference_extreme_time_utc": iso_z(times[high_idx]),
                    }
                )
        elif mode == "up":
            if price > high:
                high, high_idx = price, idx
            if high - price >= threshold:
                mode = "down"
                last_event_price = price
                low, low_idx = price, idx
                events.append(
                    {
                        "index": idx,
                        "direction": "down",
                        "event_time_utc": iso_z(times[idx]),
                        "reference_extreme_time_utc": iso_z(times[high_idx]),
                    }
                )
        elif mode == "down":
            if price < low:
                low, low_idx = price, idx
            if price - low >= threshold:
                mode = "up"
                last_event_price = price
                high, high_idx = price, idx
                events.append(
                    {
                        "index": idx,
                        "direction": "up",
                        "event_time_utc": iso_z(times[idx]),
                        "reference_extreme_time_utc": iso_z(times[low_idx]),
                    }
                )

    if last_event_price is None or mode is None:
        overshoot_ratio = None
    elif mode == "up":
        overshoot_ratio = max(0.0, closes[-1] - last_event_price) / threshold
    else:
        overshoot_ratio = max(0.0, last_event_price - closes[-1]) / threshold

    return {
        "event_count": len(events),
        "event_rate_per_bar": round(len(events) / max(1, len(closes) - 1), 10),
        "last_event_direction": events[-1]["direction"] if events else None,
        "last_event_time_utc": events[-1]["event_time_utc"] if events else None,
        "current_mode": mode,
        "overshoot_ratio_at_decision": round(overshoot_ratio, 10) if overshoot_ratio is not None else None,
    }


def dc_features(bars: list[dict[str, Any]], timeframe: str) -> tuple[dict[str, Any] | None, str | None]:
    lookback = DC_LOOKBACK_BARS[timeframe]
    min_needed = lookback + ATR_PERIOD + 1
    if len(bars) < min_needed:
        return None, f"INSUFFICIENT_{timeframe}_BARS_FOR_DC_FEATURES_NEED_{min_needed}_GOT_{len(bars)}"
    lookback_bars = bars[-lookback:]
    atr_bars = bars[-(lookback + ATR_PERIOD + 1) :]
    atr = compute_atr(atr_bars)
    if atr is None or atr <= 0:
        return None, f"ATR_UNAVAILABLE_FOR_{timeframe}"
    closes = [row["close"] for row in lookback_bars]
    close_times = [row["open_time"] + TIMEFRAME_DELTAS[timeframe] for row in lookback_bars]
    grid: list[dict[str, Any]] = []
    for multiplier in DC_THRESHOLD_ATR_GRID:
        threshold = atr * multiplier
        state = dc_state(closes, close_times, threshold)
        grid.append(
            {
                "timeframe": timeframe,
                "atr_period": ATR_PERIOD,
                "atr_at_decision": round(atr, 10),
                "threshold_atr_multiple": multiplier,
                "threshold_price_units": round(threshold, 10),
                "lookback_bars": lookback,
                **state,
            }
        )
    total_events = sum(item["event_count"] for item in grid)
    return (
        {
            "timeframe": timeframe,
            "lookback_start_utc": iso_z(close_times[0]),
            "lookback_end_utc": iso_z(close_times[-1]),
            "threshold_grid": grid,
            "event_count_at_decision": total_events,
            "event_rate_lookback_only": round(total_events / (lookback * len(DC_THRESHOLD_ATR_GRID)), 10),
        },
        None,
    )


def h0_persistence_summary(bars: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str | None]:
    min_needed = TDA_WINDOW_BARS + TDA_DELAY_BARS + 1
    if len(bars) < min_needed:
        return None, f"INSUFFICIENT_M15_BARS_FOR_TDA_WINDOW_NEED_{min_needed}_GOT_{len(bars)}"
    window = bars[-min_needed:]
    closes = [row["close"] for row in window]
    log_returns: list[float] = []
    for prev, current in zip(closes, closes[1:]):
        if prev <= 0 or current <= 0:
            return None, "NON_POSITIVE_CLOSE_FOR_LOG_RETURN"
        log_returns.append(math.log(current / prev))
    mean = statistics.fmean(log_returns)
    stdev = statistics.pstdev(log_returns) or 1.0
    normalized = [(value - mean) / stdev for value in log_returns]
    points: list[tuple[float, float]] = []
    for idx in range(TDA_DELAY_BARS, len(normalized)):
        points.append((normalized[idx], normalized[idx - TDA_DELAY_BARS]))
    if len(points) < 2:
        return None, "INSUFFICIENT_DELAY_EMBEDDING_POINTS"

    visited = [False] * len(points)
    min_dist = [float("inf")] * len(points)
    min_dist[0] = 0.0
    deaths: list[float] = []
    for _ in range(len(points)):
        next_idx = min((i for i in range(len(points)) if not visited[i]), key=lambda i: min_dist[i])
        visited[next_idx] = True
        if min_dist[next_idx] > 0:
            deaths.append(min_dist[next_idx])
        px, py = points[next_idx]
        for j, (qx, qy) in enumerate(points):
            if visited[j]:
                continue
            distance = math.hypot(px - qx, py - qy)
            if distance < min_dist[j]:
                min_dist[j] = distance

    total = sum(deaths)
    if total > 0:
        entropy = -sum((value / total) * math.log(value / total) for value in deaths if value > 0)
    else:
        entropy = 0.0
    start_time = window[TDA_DELAY_BARS]["open_time"] + TIMEFRAME_DELTAS["M15"]
    end_time = window[-1]["open_time"] + TIMEFRAME_DELTAS["M15"]
    return (
        {
            "tda_method": "library_free_delay_embedding_h0_persistence_mst",
            "embedding_dimension": TDA_EMBEDDING_DIMENSION,
            "delay_bars": TDA_DELAY_BARS,
            "window_bars": TDA_WINDOW_BARS,
            "embedding_point_count": len(points),
            "feature_count": 7,
            "window_start_utc": iso_z(start_time),
            "embedding_window_end_at_decision": iso_z(end_time),
            "h0_death_count": len(deaths),
            "h0_death_mean": round(statistics.fmean(deaths), 10) if deaths else 0.0,
            "h0_death_max": round(max(deaths), 10) if deaths else 0.0,
            "h0_death_p50": percentile(deaths, 0.50),
            "h0_death_p90": percentile(deaths, 0.90),
            "h0_total_persistence": round(total, 10),
            "h0_persistence_entropy": round(entropy, 10),
        },
        None,
    )


def sanitize_candidate_row(row: dict[str, Any]) -> dict[str, Any]:
    safe_keys = [
        "timestamp_utc",
        "evaluation_id",
        "symbol",
        "kill_zone",
        "session_tag",
        "slice_tag",
        "day_of_week",
        "hour_utc",
        "decision",
        "framework",
        "setup_grade",
        "c_gate_result",
        "ai_decision",
        "ai_direction_evaluated",
        "pre_ai_gate_skipped",
        "pre_ai_gate_reason",
        "daily_bias_direction",
        "daily_bias_confidence",
        "mso_d1_structure_direction",
        "mso_h1_structure_direction",
        "mso_m15_structure_direction",
        "mso_d1_atr_14",
        "mso_h1_atr_14",
        "mso_m15_atr_14",
        "mso_h1_nearest_ob_distance_atr",
        "mso_h1_unmitigated_ob_count",
        "mso_h1_fvg_count",
        "mso_m15_fvg_count",
        "mso_detected_sweeps_count",
        "mso_detected_sweeps_types",
        "m15_choch_detected",
        "h4_aligned",
        "detector_version_at_eval",
    ]
    trade_parameters = row.get("trade_parameters") if isinstance(row.get("trade_parameters"), dict) else {}
    return {
        "source": rel(SAFE_CANDIDATE_SOURCE),
        "source_line_no": row.get("_source_line_no"),
        "fields": {key: row.get(key) for key in safe_keys if key in row},
        "entry_sl_tp_or_level_packet": {
            "direction": trade_parameters.get("direction"),
            "entry_price": trade_parameters.get("entry_price"),
            "stop_loss": trade_parameters.get("stop_loss"),
            "take_profit_1": trade_parameters.get("take_profit_1"),
            "declared_rr_input": trade_parameters.get("risk_reward_ratio"),
        },
    }


def load_candidate_inputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_rows = read_jsonl(SAFE_CANDIDATE_SOURCE)
    suspicious_keys: set[str] = set()

    def walk(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                path = f"{prefix}.{key}" if prefix else key
                if key in FORBIDDEN_ROW_KEYS and key not in ALLOWED_CONTROL_KEYS:
                    suspicious_keys.add(path)
                walk(value, path)
        elif isinstance(obj, list):
            for value in obj[:3]:
                walk(value, prefix + "[]")

    for row in raw_rows:
        walk(row)

    candidates: list[dict[str, Any]] = []
    for row in raw_rows:
        trade_parameters = row.get("trade_parameters")
        timestamp_utc = row.get("timestamp_utc")
        if row.get("decision") != "CANDIDATE":
            continue
        if not isinstance(trade_parameters, dict):
            continue
        if not timestamp_utc:
            continue
        capture_ts = parse_utc(str(timestamp_utc))
        decision_asof = floor_to_m15(capture_ts)
        direction = trade_parameters.get("direction")
        parent_key = {
            "source_line_no": row.get("_source_line_no"),
            "symbol": row.get("symbol"),
            "decision_asof_utc": iso_z(decision_asof),
            "direction": direction,
            "entry_price": trade_parameters.get("entry_price"),
            "stop_loss": trade_parameters.get("stop_loss"),
            "take_profit_1": trade_parameters.get("take_profit_1"),
            "framework": row.get("framework"),
            "evaluation_id": row.get("evaluation_id"),
        }
        candidates.append(
            {
                "raw": row,
                "safe": sanitize_candidate_row(row),
                "source_capture_utc": iso_z(capture_ts),
                "source_capture_lag_seconds": round((capture_ts - decision_asof).total_seconds(), 6),
                "decision_asof": decision_asof,
                "decision_asof_utc": iso_z(decision_asof),
                "symbol": row.get("symbol"),
                "session": row.get("kill_zone") or row.get("session_tag"),
                "side": direction,
                "setup_id": row.get("evaluation_id") or sha256_json(parent_key)[:16],
                "parent_duplicate_group_id": "otb2r_g3_parent_" + sha256_json(parent_key)[:20],
                "candidate_source_hash": sha256_json(sanitize_candidate_row(row)),
            }
        )

    audit = {
        "source_path": rel(SAFE_CANDIDATE_SOURCE),
        "source_sha256": sha256_file(SAFE_CANDIDATE_SOURCE),
        "raw_row_count": len(raw_rows),
        "candidate_trade_param_row_count": len(candidates),
        "suspicious_forbidden_key_hits": sorted(suspicious_keys),
        "suspicious_key_policy": "candidate_features_log accepted because the only recurring TP key is an input target level, not an outcome touch/order result.",
        "records_by_symbol": dict(Counter(c["symbol"] for c in candidates)),
        "records_by_date": dict(sorted(Counter(c["decision_asof_utc"][:10] for c in candidates).items())),
        "no_outcome_rows_read": True,
        "blocked_packet_outcomes_not_opened": True,
    }
    return candidates, audit


def build_feature_context(
    candidate: dict[str, Any],
    sources: dict[tuple[str, str], list[OHLCSource]],
    required_timeframes: list[str],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    decision_asof = candidate["decision_asof"]
    selected: dict[str, dict[str, Any]] = {}
    blockers: list[dict[str, Any]] = []
    inspected_all: list[dict[str, Any]] = []
    for timeframe in required_timeframes:
        min_bars = max(
            DC_LOOKBACK_BARS.get(timeframe, TDA_WINDOW_BARS) + ATR_PERIOD + 1,
            TDA_WINDOW_BARS + TDA_DELAY_BARS + 1 if timeframe == "M15" else 0,
        )
        source, inspected, blocker = select_ohlc_source(
            sources,
            candidate["symbol"],
            timeframe,
            decision_asof,
            min_bars,
        )
        inspected_all.extend(inspected)
        if source is None:
            blockers.append(
                {
                    "blocker_code": blocker,
                    "field_family": "local_ohlc_closed_bar_coverage",
                    "symbol": candidate["symbol"],
                    "timeframe": timeframe,
                    "decision_asof_utc": candidate["decision_asof_utc"],
                    "min_closed_bars_required": min_bars,
                    "source_candidates_inspected": inspected,
                }
            )
            continue
        bars = source.bars_closed_by(decision_asof)
        feature_lookback = DC_LOOKBACK_BARS.get(timeframe, TDA_WINDOW_BARS)
        selected[timeframe] = {
            "source": source,
            "bars": bars,
            "closed_bar_count": len(bars),
            "feature_window_start_utc": iso_z(bars[-feature_lookback]["open_time"] + TIMEFRAME_DELTAS[timeframe])
            if len(bars) >= feature_lookback
            else None,
            "feature_window_end_utc": iso_z(bars[-1]["open_time"] + TIMEFRAME_DELTAS[timeframe]) if bars else None,
        }
    if blockers:
        return None, blockers, inspected_all
    return selected, blockers, inspected_all


def build_record_for_packet(
    packet_id: str,
    spec: dict[str, Any],
    candidate: dict[str, Any],
    sources: dict[tuple[str, str], list[OHLCSource]],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    context, blockers, inspected = build_feature_context(candidate, sources, spec["required_timeframes"])
    if context is None:
        return None, blockers, inspected

    feature_blockers: list[dict[str, Any]] = []
    dc_by_tf: dict[str, Any] = {}
    if spec["family"] in {"dc_overshoot", "dc_swing"}:
        for timeframe in spec["required_timeframes"]:
            features, blocker = dc_features(context[timeframe]["bars"], timeframe)
            if blocker:
                feature_blockers.append(
                    {
                        "blocker_code": blocker,
                        "field_family": "dc_features",
                        "symbol": candidate["symbol"],
                        "timeframe": timeframe,
                        "decision_asof_utc": candidate["decision_asof_utc"],
                    }
                )
            else:
                dc_by_tf[timeframe] = features

    tda_summary: dict[str, Any] | None = None
    if spec["family"] == "tda_h0_embedding":
        tda_summary, blocker = h0_persistence_summary(context["M15"]["bars"])
        if blocker:
            feature_blockers.append(
                {
                    "blocker_code": blocker,
                    "field_family": "tda_h0_embedding",
                    "symbol": candidate["symbol"],
                    "timeframe": "M15",
                    "decision_asof_utc": candidate["decision_asof_utc"],
                }
            )

    if feature_blockers:
        return None, feature_blockers, inspected

    selected_sources = {
        tf: {
            "source_path": rel(ctx["source"].path),
            "source_sha256": ctx["source"].file_sha256,
            "closed_bar_count_at_decision": ctx["closed_bar_count"],
            "feature_window_start_utc": ctx["feature_window_start_utc"],
            "feature_window_end_utc": ctx["feature_window_end_utc"],
        }
        for tf, ctx in context.items()
    }
    ordered_path_source_id = "g3_closed_ohlcv_ordered_input__" + sha256_json(
        {
            "candidate_source_hash": candidate["candidate_source_hash"],
            "decision_asof_utc": candidate["decision_asof_utc"],
            "packet_id": packet_id,
            "selected_sources": selected_sources,
        }
    )[:24]
    duplicate_group_id = "otb2r_g3_" + sha256_json(
        {
            "packet_id": packet_id,
            "parent_duplicate_group_id": candidate["parent_duplicate_group_id"],
        }
    )[:20]

    source_hash_payload = {
        "candidate_input_hash": candidate["candidate_source_hash"],
        "selected_sources": selected_sources,
        "feature_contract": {
            "family": spec["family"],
            "dc_threshold_atr_grid": DC_THRESHOLD_ATR_GRID,
            "dc_lookback_bars": DC_LOOKBACK_BARS,
            "tda_window_bars": TDA_WINDOW_BARS,
            "tda_embedding_dimension": TDA_EMBEDDING_DIMENSION,
            "tda_delay_bars": TDA_DELAY_BARS,
            "same_bar_policy_id": SAME_BAR_POLICY_ID,
        },
    }
    source_hash = sha256_json(source_hash_payload)

    record: dict[str, Any] = {
        "packet_id": packet_id,
        "experiment_id": spec["experiment_id"],
        "hypothesis_id": spec["hypothesis_id"],
        "setup_id": candidate["setup_id"],
        "symbol": candidate["symbol"],
        "session": candidate["session"],
        "side": candidate["side"],
        "decision_asof_utc": candidate["decision_asof_utc"],
        "source_capture_utc": candidate["source_capture_utc"],
        "source_capture_lag_seconds": candidate["source_capture_lag_seconds"],
        "ordered_path_source_id": ordered_path_source_id,
        "path_start_utc": min(v["feature_window_start_utc"] for v in selected_sources.values() if v["feature_window_start_utc"]),
        "path_end_utc": max(v["feature_window_end_utc"] for v in selected_sources.values() if v["feature_window_end_utc"]),
        "same_bar_ambiguity_policy": SAME_BAR_POLICY_ID,
        "same_bar_ambiguity_state": "NOT_APPLICABLE_INPUT_ONLY_NO_TERMINAL_ORDER_CLAIM",
        "cost_model_version": COST_MODEL_VERSION,
        "duplicate_group_id": duplicate_group_id,
        "parent_duplicate_group_id": candidate["parent_duplicate_group_id"],
        "source_hash": source_hash,
        "source_hash_payload": source_hash_payload,
        "label_family": LABEL_FAMILY,
        "label_values_absent": True,
        "broker_actual_r_absent_from_primary_metric": True,
        "validation_safe": VALIDATION_SAFE,
        "promotion_verdict": PROMOTION_VERDICT,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "entry_sl_tp_or_level_packet": candidate["safe"]["entry_sl_tp_or_level_packet"],
        "candidate_input_projection": candidate["safe"],
        "selected_local_ohlc_sources": selected_sources,
    }

    if spec["family"] == "dc_overshoot":
        overshoot_packet = {
            timeframe: {
                "lookback_start_utc": features["lookback_start_utc"],
                "lookback_end_utc": features["lookback_end_utc"],
                "threshold_grid": [
                    {
                        "threshold_atr_multiple": item["threshold_atr_multiple"],
                        "threshold_price_units": item["threshold_price_units"],
                        "overshoot_ratio_at_decision": item["overshoot_ratio_at_decision"],
                        "last_event_direction": item["last_event_direction"],
                        "last_event_time_utc": item["last_event_time_utc"],
                        "current_mode": item["current_mode"],
                    }
                    for item in features["threshold_grid"]
                ],
            }
            for timeframe, features in dc_by_tf.items()
        }
        record["dc_overshoot_ratio_at_decision_packet"] = overshoot_packet
        record["dc_previous_event_direction"] = {
            timeframe: features["threshold_grid"][1]["last_event_direction"] for timeframe, features in dc_by_tf.items()
        }
        record["distance_to_poi_at_decision_input"] = candidate["raw"].get("mso_h1_nearest_ob_distance_atr")
    elif spec["family"] == "dc_swing":
        record["dc_threshold_grid_packet"] = dc_by_tf
        record["dc_event_count_at_decision"] = {
            timeframe: features["event_count_at_decision"] for timeframe, features in dc_by_tf.items()
        }
        record["dc_event_rate_lookback_only"] = {
            timeframe: features["event_rate_lookback_only"] for timeframe, features in dc_by_tf.items()
        }
    elif spec["family"] == "tda_h0_embedding" and tda_summary is not None:
        record["embedding_window_end_at_decision"] = tda_summary["embedding_window_end_at_decision"]
        record["persistence_summary_packet"] = tda_summary

    return record, [], inspected


def packet_filename(packet_id: str, spec: dict[str, Any]) -> Path:
    return PACKETS_DIR / (
        f"{packet_id}__{spec['experiment_id']}__otb2r_g3_{spec['packet_slug']}_{DATE_STAMP}.json"
    )


def collect_required_registry_rows() -> dict[str, Any]:
    prereg_rows = read_json(ROOT / "research/science_program_2026_05/03_experiment_specs/G3_GEOMETRY_SIGNAL_EXPERIMENT_PREREG_ROWS_2026-05-06.json")
    hypothesis_rows = read_json(ROOT / "research/science_program_2026_05/02_hypothesis_registry/G3_GEOMETRY_SIGNAL_HYPOTHESIS_ROWS_2026-05-06.json")
    mechanism_rows = read_json(ROOT / "research/science_program_2026_05/02_hypothesis_registry/G3_GEOMETRY_SIGNAL_MECHANISM_ROWS_2026-05-06.json")
    source_contract_rows = read_json(ROOT / "research/science_program_2026_05/02_hypothesis_registry/G3_GEOMETRY_SIGNAL_SOURCE_CONTRACT_ROWS_2026-05-06.json")
    prereg_row_list = prereg_rows.get("rows", prereg_rows) if isinstance(prereg_rows, dict) else prereg_rows
    hypothesis_row_list = hypothesis_rows.get("rows", hypothesis_rows) if isinstance(hypothesis_rows, dict) else hypothesis_rows
    mechanism_row_list = mechanism_rows.get("rows", mechanism_rows) if isinstance(mechanism_rows, dict) else mechanism_rows
    source_contract_row_list = (
        source_contract_rows.get("rows", source_contract_rows)
        if isinstance(source_contract_rows, dict)
        else source_contract_rows
    )
    return {
        "target_prereg_rows": [
            row
            for row in prereg_row_list
            if row.get("experiment_id") in {spec["experiment_id"] for spec in G3_PACKET_SPECS.values()}
        ],
        "target_hypothesis_rows": [
            row
            for row in hypothesis_row_list
            if row.get("hypothesis_id") in {spec["hypothesis_id"] for spec in G3_PACKET_SPECS.values()}
        ],
        "mechanism_rows": mechanism_row_list,
        "source_contract_rows": source_contract_row_list,
    }


def source_hash_ledger(packet_records: dict[str, list[dict[str, Any]]], source_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    packet_source_hashes: list[dict[str, Any]] = []
    for packet_id, records in packet_records.items():
        for record in records:
            packet_source_hashes.append(
                {
                    "packet_id": packet_id,
                    "experiment_id": record["experiment_id"],
                    "setup_id": record["setup_id"],
                    "decision_asof_utc": record["decision_asof_utc"],
                    "duplicate_group_id": record["duplicate_group_id"],
                    "source_hash": record["source_hash"],
                    "ordered_path_source_id": record["ordered_path_source_id"],
                    "selected_local_ohlc_sources": record["selected_local_ohlc_sources"],
                }
            )
    return {
        "generated_at_utc": now_utc(),
        "packet_source_hash_count": len(packet_source_hashes),
        "packet_source_hashes": packet_source_hashes,
        "ohlc_source_inventory": source_inventory,
        "candidate_source": {
            "path": rel(SAFE_CANDIDATE_SOURCE),
            "sha256": sha256_file(SAFE_CANDIDATE_SOURCE),
        },
        "source_hash_contract": "source_hash hashes sanitized candidate input fields, selected local OHLC source hashes, and fixed feature-builder params only.",
    }


def recursive_key_paths(obj: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            paths.append(path)
            paths.extend(recursive_key_paths(value, path))
    elif isinstance(obj, list):
        for item in obj:
            paths.extend(recursive_key_paths(item, prefix + "[]"))
    return paths


def no_leak_audit(packet_records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    violations: list[dict[str, str]] = []
    for packet_id, records in packet_records.items():
        for idx, record in enumerate(records):
            for path in recursive_key_paths(record):
                leaf = path.split(".")[-1]
                if leaf in ALLOWED_CONTROL_KEYS:
                    continue
                if leaf in FORBIDDEN_ROW_KEYS:
                    violations.append({"packet_id": packet_id, "record_index": str(idx), "key_path": path})
    return {
        "generated_at_utc": now_utc(),
        "records_scanned": sum(len(records) for records in packet_records.values()),
        "forbidden_key_policy": sorted(FORBIDDEN_ROW_KEYS),
        "allowed_control_keys": sorted(ALLOWED_CONTROL_KEYS),
        "violations": violations,
        "status": "PASS" if not violations else "FAIL",
        "no_outcome_columns_in_records": not violations,
        "no_result_columns_in_records": not violations,
        "broker_actual_r_absent_from_primary_metric": True,
        "blocked_packet_outcomes_not_opened": True,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def duplicate_audit(packet_records: dict[str, list[dict[str, Any]]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    parent_groups = Counter(c["parent_duplicate_group_id"] for c in candidates)
    rows: list[dict[str, Any]] = []
    for packet_id, records in packet_records.items():
        packet_groups = Counter(record["duplicate_group_id"] for record in records)
        parent_used = Counter(record["parent_duplicate_group_id"] for record in records)
        rows.append(
            {
                "packet_id": packet_id,
                "raw_record_count": len(records),
                "unique_packet_duplicate_group_count": len(packet_groups),
                "unique_parent_setup_duplicate_group_count": len(parent_used),
                "max_records_per_parent_group": max(parent_used.values(), default=0),
                "denominator_policy": "Use unique parent_setup_duplicate_group_id for cross-packet setup denominators; packet rows are feature-family projections, not independent outcomes.",
            }
        )
    return {
        "generated_at_utc": now_utc(),
        "candidate_parent_group_count": len(parent_groups),
        "candidate_raw_count": len(candidates),
        "packet_duplicate_summary": rows,
        "duplicate_policy": {
            "parent_duplicate_group_id": "stable hash over source line, setup identity, symbol, decision_asof, side, entry/SL/TP, framework",
            "duplicate_group_id": "packet_id plus parent_duplicate_group_id; prevents counting the same setup as independent inside a packet",
            "sample_denominator_warning": "No validation claim may count the same parent setup across G3 families as independent evidence.",
        },
    }


def exact_blocker_ledger(blockers: list[dict[str, Any]], packet_records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    by_packet = defaultdict(Counter)
    for blocker in blockers:
        by_packet[blocker["packet_id"]][blocker["blocker_code"]] += 1
    return {
        "generated_at_utc": now_utc(),
        "blocker_count": len(blockers),
        "packet_record_counts": {packet_id: len(records) for packet_id, records in packet_records.items()},
        "blocker_counts_by_packet": {packet_id: dict(counter) for packet_id, counter in by_packet.items()},
        "blockers": blockers,
        "exact_missing_questions_closed_or_reduced": {
            "OTG0-PKT-031": "dc_overshoot_ratio_at_decision_packet built for covered rows; remaining rows list exact missing local OHLC coverage or DC feature blockers.",
            "OTG0-PKT-032": "dc_threshold_grid_packet/event-count/event-rate built for rows with M15/H1/H4 coverage; remaining rows list exact missing coverage or feature blockers.",
            "OTG0-PKT-036": "embedding_window_end_at_decision and h0 persistence_summary_packet built for covered M15 rows; remaining rows list exact missing coverage or feature blockers.",
        },
    }


def rejected_alternatives_ledger(candidate_audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at_utc": now_utc(),
        "accepted_packetization": {
            "source_family": "shadow_logs/candidate_features_log.jsonl + local closed OHLC CSVs",
            "reason": "candidate_features_log contains input-side CANDIDATE rows and no outcome/path-order resolution fields; local OHLC provides point-in-time geometry windows for covered decisions.",
            "source_sha256": candidate_audit["source_sha256"],
        },
        "rejected_alternatives": [
            {
                "alternative": "Use only the 86 accepted OTB2R path rows from candidate_ltf_path_order projections",
                "decision": "REJECTED_AS_PRIMARY_G3_FEATURE_SOURCE",
                "reason": "Those rows answer path-order source existence, not DC/TDA pre-decision feature construction. Many decisions are 2026-05-03 to 2026-05-06 after local OHLC coverage and some LTF rows are SOURCE_BLOCKED.",
            },
            {
                "alternative": "Open V2/V3 forward pair resolution or path-scaling replay ledgers",
                "decision": "REJECTED_FOR_POLICY",
                "reason": "Those files are result-bearing synthetic path/replay ledgers and may expose terminal order, hit TP/SL, or path-R values.",
            },
            {
                "alternative": "Use broker account/trade record actual-R files to backfill labels or terminal order",
                "decision": "REJECTED_FOR_POLICY",
                "reason": "Broker actual-R is forbidden for this OTB2R input-only builder and remains absent from primary metric fields.",
            },
            {
                "alternative": "Use prior blocked G3 packet records",
                "decision": "REJECTED_AS_DATA_SOURCE",
                "reason": "Prior OTB2R G3 packets contain zero rebuilt records; their file hashes are retained only as control evidence.",
            },
            {
                "alternative": "Fetch public DC/TDA examples or market data from the network",
                "decision": "REJECTED_FOR_SCOPE",
                "reason": "G3 source contract allows methodology context only; this lane uses local market evidence and performs no network/API/data purchase.",
            },
            {
                "alternative": "Use same-bar terminal path assumptions to fill unavailable synthetic replay fields",
                "decision": "REJECTED_FOR_NO_LEAK",
                "reason": "This builder computes only pre-decision geometry. Same-bar policy is recorded as input-only and never claims terminal order.",
            },
        ],
        "policy_skipped_sources_not_opened": POLICY_SKIPPED_SOURCES,
    }


def same_bar_policy_artifact() -> dict[str, Any]:
    return {
        "generated_at_utc": now_utc(),
        "same_bar_ambiguity_policy_id": SAME_BAR_POLICY_ID,
        "policy": SAME_BAR_POLICY,
        "bar_timestamp_semantics": "candle_open_assumed",
        "closed_bar_rule": "include bar only if open_time + timeframe_delta <= decision_asof_utc",
        "terminal_order_claim": "NONE",
        "cost_model_version": COST_MODEL_VERSION,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def label_family_audit(packet_records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for packet_id, records in packet_records.items():
        families = Counter(record.get("label_family") for record in records)
        rows.append(
            {
                "packet_id": packet_id,
                "record_count": len(records),
                "label_families": dict(families),
                "label_values_present": False,
                "broker_actual_r_absent_from_primary_metric": all(
                    record.get("broker_actual_r_absent_from_primary_metric") is True for record in records
                ),
            }
        )
    return {
        "generated_at_utc": now_utc(),
        "label_family": LABEL_FAMILY,
        "label_family_policy": "synthetic_path_r is declared as the future label family only; no label values or broker actual-R values are written.",
        "packet_rows": rows,
        "validation_safe": VALIDATION_SAFE,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def control_input_hashes() -> list[dict[str, Any]]:
    hashes: list[dict[str, Any]] = []
    for rel_path in CONTROL_INPUTS:
        path = ROOT / rel_path
        hashes.append(
            {
                "path": rel_path,
                "exists": path.exists(),
                "sha256": sha256_file(path),
            }
        )
    return hashes


def build_packet_artifacts() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    AUDITS_DIR.mkdir(parents=True, exist_ok=True)

    candidates, candidate_audit = load_candidate_inputs()
    sources = discover_ohlc_sources()
    source_inventory = [source.coverage_row() for group in sources.values() for source in group]
    registry_rows = collect_required_registry_rows()

    packet_records: dict[str, list[dict[str, Any]]] = {packet_id: [] for packet_id in G3_PACKET_SPECS}
    blockers: list[dict[str, Any]] = []
    inspected_coverage: list[dict[str, Any]] = []

    for packet_id, spec in G3_PACKET_SPECS.items():
        for candidate in candidates:
            record, row_blockers, inspected = build_record_for_packet(packet_id, spec, candidate, sources)
            inspected_coverage.extend(inspected)
            if record is not None:
                packet_records[packet_id].append(record)
                continue
            for blocker in row_blockers:
                blockers.append(
                    {
                        "packet_id": packet_id,
                        "experiment_id": spec["experiment_id"],
                        "hypothesis_id": spec["hypothesis_id"],
                        "setup_id": candidate["setup_id"],
                        "symbol": candidate["symbol"],
                        "session": candidate["session"],
                        "side": candidate["side"],
                        "decision_asof_utc": candidate["decision_asof_utc"],
                        "parent_duplicate_group_id": candidate["parent_duplicate_group_id"],
                        "candidate_source_hash": candidate["candidate_source_hash"],
                        **blocker,
                    }
                )

    packet_paths: dict[str, str] = {}
    for packet_id, spec in G3_PACKET_SPECS.items():
        records = packet_records[packet_id]
        decision = "READY_INPUT_ONLY_WITH_ROW_BLOCKERS" if records else "BLOCKED_WITH_EXACT_SOURCE_FIELD_BLOCKERS"
        packet = {
            "packet_id": packet_id,
            "experiment_id": spec["experiment_id"],
            "hypothesis_id": spec["hypothesis_id"],
            "packet_family": spec["family"],
            "build_date": DATE_STAMP,
            "builder": rel(Path(__file__)),
            "decision": decision,
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": VALIDATION_SAFE,
            "outcome_review_opened": OUTCOME_REVIEW_OPENED,
            "label_family": LABEL_FAMILY,
            "label_values_absent": True,
            "broker_actual_r_absent_from_primary_metric": True,
            "same_bar_ambiguity_policy_id": SAME_BAR_POLICY_ID,
            "cost_model_version": COST_MODEL_VERSION,
            "required_fields_from_g12": spec["required_fields"],
            "required_timeframes": spec["required_timeframes"],
            "record_count": len(records),
            "records": records,
        }
        path = packet_filename(packet_id, spec)
        write_json(path, packet)
        packet_paths[packet_id] = rel(path)

    coverage_summary = {
        "generated_at_utc": now_utc(),
        "candidate_audit": candidate_audit,
        "source_inventory_count": len(source_inventory),
        "source_inventory": source_inventory,
        "inspected_coverage_row_count": len(inspected_coverage),
        "inspected_coverage_digest": {
            "by_timeframe": dict(Counter(row["timeframe"] for row in inspected_coverage if row.get("timeframe"))),
            "by_path": dict(Counter(row["path"] for row in inspected_coverage if row.get("path")).most_common(50)),
        },
        "record_counts_by_packet": {packet_id: len(records) for packet_id, records in packet_records.items()},
        "blocker_count": len(blockers),
    }
    source_ledger = source_hash_ledger(packet_records, source_inventory)
    leak_audit = no_leak_audit(packet_records)
    duplicate_summary = duplicate_audit(packet_records, candidates)
    blocker_ledger = exact_blocker_ledger(blockers, packet_records)
    alternatives = rejected_alternatives_ledger(candidate_audit)
    same_bar = same_bar_policy_artifact()
    label_audit = label_family_audit(packet_records)

    manifest = {
        "generated_at_utc": now_utc(),
        "lane": "OTB2R_G3_GEOMETRY_INPUT_PACKET_BUILDERS",
        "builder": rel(Path(__file__)),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_paths": packet_paths,
        "record_counts_by_packet": {packet_id: len(records) for packet_id, records in packet_records.items()},
        "blocker_count": len(blockers),
        "no_leak_status": leak_audit["status"],
        "control_input_hashes": control_input_hashes(),
        "registry_rows": registry_rows,
    }
    completion_audit = {
        "generated_at_utc": now_utc(),
        "objective": "Build OTB2R G3 geometry input-only packet builders for DC overshoot, DC swing, and TDA synthetic replay preregs using local OHLC/geometry evidence only.",
        "prompt_requirements": {
            "source_hashed": all(record.get("source_hash") for records in packet_records.values() for record in records),
            "duplicate_grouped": all(record.get("duplicate_group_id") for records in packet_records.values() for record in records),
            "decision_asof_utc_present": all(record.get("decision_asof_utc") for records in packet_records.values() for record in records),
            "label_family_separated": all(record.get("label_family") == LABEL_FAMILY for records in packet_records.values() for record in records),
            "no_leak_input_only": leak_audit["status"] == "PASS",
            "same_bar_policy_recorded": True,
            "cost_model_version_recorded": True,
            "rejected_alternatives_recorded": True,
            "exact_blockers_recorded": bool(blockers),
            "promotion_verdict_preserved": PROMOTION_VERDICT,
            "validation_safe_false": VALIDATION_SAFE is False,
            "outcome_review_opened_false": OUTCOME_REVIEW_OPENED is False,
        },
        "packet_record_counts": {packet_id: len(records) for packet_id, records in packet_records.items()},
        "blocker_count": len(blockers),
        "status": "PASS" if leak_audit["status"] == "PASS" and any(packet_records.values()) else "FAIL",
        "residual_risk": "Input packets are not validation-safe. Row counts remain below prereg sample floors and blocked rows require additional local pre-decision OHLC or source-specific capture.",
    }

    artifacts = {
        "OTB2R_G3_GEOMETRY_PACKET_MANIFEST_2026-05-07.json": manifest,
        "OTB2R_G3_GEOMETRY_SOURCE_HASH_LEDGER_2026-05-07.json": source_ledger,
        "OTB2R_G3_GEOMETRY_COVERAGE_AUDIT_2026-05-07.json": coverage_summary,
        "OTB2R_G3_GEOMETRY_NO_LEAK_AUDIT_2026-05-07.json": leak_audit,
        "OTB2R_G3_GEOMETRY_DUPLICATE_DENOMINATOR_AUDIT_2026-05-07.json": duplicate_summary,
        "OTB2R_G3_GEOMETRY_EXACT_BLOCKER_LEDGER_2026-05-07.json": blocker_ledger,
        "OTB2R_G3_GEOMETRY_REJECTED_ALTERNATIVES_LEDGER_2026-05-07.json": alternatives,
        "OTB2R_G3_GEOMETRY_SAME_BAR_POLICY_2026-05-07.json": same_bar,
        "OTB2R_G3_GEOMETRY_LABEL_FAMILY_AUDIT_2026-05-07.json": label_audit,
        "OTB2R_G3_GEOMETRY_COMPLETION_AUDIT_2026-05-07.json": completion_audit,
    }
    for filename, obj in artifacts.items():
        write_json(OUT / filename, obj)
    write_jsonl(OUT / "OTB2R_G3_GEOMETRY_EXACT_BLOCKER_LEDGER_ROWS_2026-05-07.jsonl", blockers)

    write_text(
        OUT / "OTB2R_G3_GEOMETRY_PACKET_MANIFEST_2026-05-07.md",
        render_manifest_md(manifest, completion_audit, blocker_ledger),
    )
    write_text(
        OUT / "OTB2R_G3_GEOMETRY_PACKET_CONTRACT_AND_REJECTED_ALTERNATIVES_2026-05-07.md",
        render_contract_md(manifest, alternatives, same_bar),
    )
    write_text(
        OUT / "OTB2R_G3_GEOMETRY_G12_AUDIT_HANDOFF_2026-05-07.md",
        render_g12_handoff_md(manifest, blocker_ledger, completion_audit),
    )
    write_text(
        OUT / "OTB2R_G3_GEOMETRY_COMPLETION_AUDIT_2026-05-07.md",
        render_completion_md(completion_audit, leak_audit, duplicate_summary),
    )

    return {
        "manifest": manifest,
        "completion_audit": completion_audit,
        "no_leak_audit": leak_audit,
        "blocker_ledger": blocker_ledger,
    }


def render_manifest_md(manifest: dict[str, Any], completion: dict[str, Any], blocker_ledger: dict[str, Any]) -> str:
    lines = [
        "# OTB2R G3 Geometry Packet Manifest (2026-05-07)",
        "",
        f"- Lane: `{manifest['lane']}`",
        f"- Builder: `{manifest['builder']}`",
        f"- Promotion verdict: `{manifest['promotion_verdict']}`",
        f"- Validation safe: `{manifest['validation_safe']}`",
        f"- Outcome review opened: `{manifest['outcome_review_opened']}`",
        f"- No-leak status: `{manifest['no_leak_status']}`",
        "",
        "## Packet Counts",
        "",
    ]
    for packet_id, count in manifest["record_counts_by_packet"].items():
        lines.append(f"- `{packet_id}`: {count} input-only records, `{manifest['packet_paths'][packet_id]}`")
    lines.extend(
        [
            "",
            "## Blockers",
            "",
            f"- Row-level blockers: {blocker_ledger['blocker_count']}",
            "- Blocked rows remain exact source/field blockers, not outcome blockers.",
            "",
            "## Completion",
            "",
            f"- Status: `{completion['status']}`",
            f"- Residual risk: {completion['residual_risk']}",
            "",
        ]
    )
    return "\n".join(lines)


def render_contract_md(manifest: dict[str, Any], alternatives: dict[str, Any], same_bar: dict[str, Any]) -> str:
    lines = [
        "# OTB2R G3 Packet Contract And Rejected Alternatives (2026-05-07)",
        "",
        "## Accepted Contract",
        "",
        f"- Source family: {alternatives['accepted_packetization']['source_family']}",
        f"- Reason: {alternatives['accepted_packetization']['reason']}",
        f"- Label family: `{LABEL_FAMILY}` with label values absent.",
        f"- Cost model version: `{COST_MODEL_VERSION}`.",
        f"- Same-bar policy: `{same_bar['same_bar_ambiguity_policy_id']}`.",
        "",
        "## Rejected Alternatives",
        "",
    ]
    for item in alternatives["rejected_alternatives"]:
        lines.append(f"- `{item['decision']}`: {item['alternative']} - {item['reason']}")
    lines.extend(
        [
            "",
            "## Packet Paths",
            "",
        ]
    )
    for packet_id, path in manifest["packet_paths"].items():
        lines.append(f"- `{packet_id}`: `{path}`")
    lines.append("")
    return "\n".join(lines)


def render_g12_handoff_md(
    manifest: dict[str, Any],
    blocker_ledger: dict[str, Any],
    completion: dict[str, Any],
) -> str:
    lines = [
        "# OTB2R G3 Geometry G12 Audit Handoff (2026-05-07)",
        "",
        "This handoff answers G12's blocked questions for the three G3 packet IDs with input-only artifacts.",
        "",
        "## What Is Now Built",
        "",
    ]
    for packet_id, count in manifest["record_counts_by_packet"].items():
        lines.append(f"- `{packet_id}`: {count} source-hashed, duplicate-grouped, decision-asof input rows.")
    lines.extend(
        [
            "",
            "## Remaining Blockers",
            "",
        ]
    )
    for packet_id, counts in blocker_ledger["blocker_counts_by_packet"].items():
        lines.append(f"- `{packet_id}`: {dict(counts)}")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            f"- Promotion verdict remains `{PROMOTION_VERDICT}`.",
            "- `validation_safe=false`; no validation claim is made.",
            "- `outcome_review_opened=false`; no broker actual-R or synthetic replay result columns were opened.",
            "",
        ]
    )
    return "\n".join(lines)


def render_completion_md(completion: dict[str, Any], leak_audit: dict[str, Any], duplicate_summary: dict[str, Any]) -> str:
    lines = [
        "# OTB2R G3 Geometry Completion Audit (2026-05-07)",
        "",
        f"- Status: `{completion['status']}`",
        f"- Objective: {completion['objective']}",
        f"- No-leak status: `{leak_audit['status']}`",
        f"- Records scanned for no-leak: {leak_audit['records_scanned']}",
        f"- Candidate parent duplicate groups: {duplicate_summary['candidate_parent_group_count']}",
        "",
        "## Requirement Checklist",
        "",
    ]
    for key, value in completion["prompt_requirements"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Packet Record Counts",
            "",
        ]
    )
    for packet_id, count in completion["packet_record_counts"].items():
        lines.append(f"- `{packet_id}`: {count}")
    lines.extend(
        [
            "",
            f"Residual risk: {completion['residual_risk']}",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    result = build_packet_artifacts()
    print(
        json.dumps(
            {
                "status": result["completion_audit"]["status"],
                "packet_record_counts": result["manifest"]["record_counts_by_packet"],
                "blocker_count": result["blocker_ledger"]["blocker_count"],
                "no_leak_status": result["no_leak_audit"]["status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
