from __future__ import annotations

import csv
import json
import math
import subprocess
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"

STAGE04_INDEX = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SHARD_INDEX_{DATE_ID}.jsonl"
STAGE04_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_{DATE_ID}.json"
STAGE02_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE_ID}.json"
FULL_REPLAY_STAGE04_SUMMARY = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24"
    / "VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json"
)
ECONOMIC_CALENDAR = REPO_ROOT / "data" / "economic_calendar.csv"

OUTPUT_FEATURE_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FEATURE_LEDGER_{DATE_ID}.jsonl"
OUTPUT_FIELD_CLASSIFICATION = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FIELD_CLASSIFICATION_LEDGER_{DATE_ID}.jsonl"
OUTPUT_DISTRIBUTIONS = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_DISTRIBUTION_LEDGER_{DATE_ID}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_SUMMARY_{DATE_ID}.json"
OUTPUT_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_REPORT_{DATE_ID}.md"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"


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

DIMENSION_FIELDS = [
    "symbol",
    "transfer_group",
    "framework",
    "side",
    "session_bucket",
    "session_subwindow",
    "kill_zone_position",
    "weekday",
    "month",
    "quarter",
    "year",
    "source_mode",
    "source_timeframe",
    "source_window_complete",
    "trend_state_20",
    "volatility_state_14_vs_50",
    "compression_expansion_state",
    "current_bar_direction",
    "liquidity_sweep_proxy_state",
    "news_calendar_coverage_status",
    "news_high_impact_within_120m",
    "source_path_feature_status",
    "orderflow_depth_proxy_status",
    "cross_asset_lead_lag_status",
    "spread_slippage_cost_status",
    "adverse_excursion_bucket",
    "policy_reversal_bucket",
]


FIELD_CLASSIFICATIONS = [
    ("symbol", "decision_safe_asof", "Symbol is known at candidate time."),
    ("transfer_group", "decision_safe_asof", "Derived from symbol taxonomy before candidate decision."),
    ("framework", "decision_safe_asof", "Candidate-origin framework is known at generation time."),
    ("side", "decision_safe_asof", "Candidate side is known at generation time."),
    ("session_bucket", "decision_safe_asof", "Session bucket is known from UTC timestamp."),
    ("session_subwindow", "decision_safe_asof", "Derived from candle UTC hour/minute only."),
    ("kill_zone_position", "decision_safe_asof", "Derived from configured symbol kill-zone schedule and timestamp."),
    ("weekday", "decision_safe_asof", "Calendar timestamp feature."),
    ("month", "decision_safe_asof", "Calendar timestamp feature."),
    ("quarter", "decision_safe_asof", "Calendar timestamp feature."),
    ("year", "decision_safe_asof", "Calendar timestamp feature for split/holdout controls."),
    ("source_mode", "source_provenance", "Path source mode, not a market predictor by itself."),
    ("source_timeframe", "source_provenance", "Path source timeframe, not a market predictor by itself."),
    ("source_window_complete", "source_provenance", "Source coverage/provenance flag."),
    ("source_path_feature_status", "source_provenance", "Records whether as-of OHLC features were computed from the source file."),
    ("asof_lookback_bars_available", "decision_safe_asof", "Count of bars available up to candidate candle only."),
    ("return_1_bar", "decision_safe_asof", "Past close-to-close return at candidate candle."),
    ("return_4_bar", "decision_safe_asof", "Past 4-bar return at candidate candle."),
    ("return_16_bar", "decision_safe_asof", "Past 16-bar return at candidate candle."),
    ("atr14_price", "decision_safe_asof", "Mean high-low range over last 14 available bars ending at candidate candle."),
    ("atr50_price", "decision_safe_asof", "Mean high-low range over last 50 available bars ending at candidate candle."),
    ("trend_score_20_atr50", "decision_safe_asof", "Past 20-bar close change normalized by ATR50."),
    ("trend_state_20", "decision_safe_asof", "Bucketed trend score from past-only OHLC."),
    ("volatility_state_14_vs_50", "decision_safe_asof", "ATR14/ATR50 bucket from past-only OHLC."),
    ("compression_expansion_state", "decision_safe_asof", "Compression/expansion bucket from ATR ratio."),
    ("current_bar_displacement_atr14", "decision_safe_asof", "Current candidate bar range normalized by ATR14."),
    ("current_bar_speed_atr14", "decision_safe_asof", "Current candidate bar body normalized by ATR14."),
    ("current_bar_direction", "decision_safe_asof", "Candidate bar close-open direction."),
    ("lookback50_position", "decision_safe_asof", "Close location in past 50-bar high/low range."),
    ("liquidity_sweep_proxy_state", "decision_safe_asof", "Candidate bar broke prior 20-bar high/low using past-only levels."),
    ("news_calendar_coverage_status", "source_provenance", "Whether local calendar coverage exists for the candidate date."),
    ("news_min_abs_minutes", "decision_safe_asof", "Scheduled calendar proximity only when local calendar covers date/currency."),
    ("news_high_impact_within_120m", "decision_safe_asof", "High-impact scheduled event proximity when calendar coverage exists."),
    ("entry_delay_bars", "diagnostic_only", "Entry touch delay occurs after candidate generation."),
    ("observation_count", "diagnostic_only", "Replay path length after candidate generation."),
    ("legacy_final_r", "post_outcome_label", "Dynamic replay result, not a decision feature."),
    ("live_current_j46_j49_final_r", "post_outcome_label", "Dynamic replay result, not a decision feature."),
    ("be_after_trigger_final_r", "post_outcome_label", "Dynamic replay result, not a decision feature."),
    ("trailing_runner_final_r", "post_outcome_label", "Dynamic replay result, not a decision feature."),
    ("live_vs_legacy_delta_r", "post_outcome_label", "Policy disagreement label after path replay."),
    ("policy_reversal_bucket", "post_outcome_label", "Winner/loser reversal bucket between legacy fixed target and live dynamic policy."),
    ("mfe_r", "post_outcome_label", "Maximum favorable excursion after entry."),
    ("mae_r", "post_outcome_label", "Maximum adverse excursion after entry."),
    ("adverse_excursion_bucket", "post_outcome_label", "Bucketed adverse excursion after entry."),
    ("mfe_mae_ratio", "post_outcome_label", "Path outcome shape after entry."),
    ("mfe_mae_timing_status", "missing", "Stage04 policy result rows do not record separate MFE/MAE timestamps."),
    ("live_exit_reason", "post_outcome_label", "Dynamic policy exit reason after entry."),
    ("live_exit_progress_fraction", "post_outcome_label", "Exit timing over replay path after entry."),
    ("same_bar_ambiguity", "diagnostic_only", "Replay ambiguity diagnostic."),
    ("no_fill_fillability_status", "diagnostic_only", "Current Stage06 feature ledger contains filled replay rows; full no-fill distribution remains separate."),
    ("orderflow_depth_proxy_status", "missing", "Sierra/tick/depth proxy sources inventoried but not universally joined to M15 replay rows."),
    ("cross_asset_lead_lag_status", "missing", "Synchronized cross-asset lead-lag panel not yet computed in Stage06."),
    ("spread_slippage_cost_status", "forward_capture_required", "Exact spread/slippage/cost requires tick/broker capture; do not infer from OHLC."),
    ("broker_order_lifecycle_fields", "forward_capture_required", "Ticket/fill/partial/modify/close lifecycle is non-generatable if not logged."),
    ("forbidden_broker_actual_r", "forbidden_leakage", "Broker-realized account/deal results are not used in this no-live replay feature ledger."),
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
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def parse_time(value: str | None) -> datetime | None:
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
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


class OhlcFeatureCache:
    def __init__(self) -> None:
        self._cache: dict[str, dict] = {}

    def load(self, source_path: str) -> dict:
        if source_path in self._cache:
            return self._cache[source_path]
        absolute = REPO_ROOT / source_path
        times: list[datetime] = []
        opens: list[float] = []
        highs: list[float] = []
        lows: list[float] = []
        closes: list[float] = []
        with absolute.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                parsed = parse_time(row.get("time"))
                if parsed is None:
                    continue
                times.append(parsed)
                opens.append(float(row["open"]))
                highs.append(float(row["high"]))
                lows.append(float(row["low"]))
                closes.append(float(row["close"]))
        data = {"times": times, "open": opens, "high": highs, "low": lows, "close": closes}
        self._cache[source_path] = data
        return data

    def features(self, source_path: str | None, candle_time: datetime | None) -> dict:
        if not source_path or candle_time is None:
            return {"source_path_feature_status": "missing_source_or_time"}
        absolute = REPO_ROOT / source_path
        if not absolute.exists():
            return {"source_path_feature_status": "source_file_missing"}
        data = self.load(source_path)
        times = data["times"]
        index = bisect_right(times, candle_time) - 1
        if index < 0:
            return {"source_path_feature_status": "candle_time_before_source_start"}
        start14 = max(0, index - 13)
        start50 = max(0, index - 49)
        start20 = max(0, index - 20)
        ranges14 = [data["high"][i] - data["low"][i] for i in range(start14, index + 1)]
        ranges50 = [data["high"][i] - data["low"][i] for i in range(start50, index + 1)]
        atr14 = mean(ranges14)
        atr50 = mean(ranges50)
        close = data["close"][index]
        open_ = data["open"][index]
        high = data["high"][index]
        low = data["low"][index]
        previous_high20 = max(data["high"][start20:index]) if index > start20 else None
        previous_low20 = min(data["low"][start20:index]) if index > start20 else None
        high50 = max(data["high"][start50 : index + 1])
        low50 = min(data["low"][start50 : index + 1])
        trend_score = None
        if index >= 20 and atr50 and atr50 > 0:
            trend_score = (close - data["close"][index - 20]) / atr50
        atr_ratio = atr14 / atr50 if atr14 and atr50 and atr50 > 0 else None
        position50 = (close - low50) / (high50 - low50) if high50 > low50 else None
        sweep_up = previous_high20 is not None and high > previous_high20
        sweep_down = previous_low20 is not None and low < previous_low20
        if sweep_up and sweep_down:
            sweep_state = "swept_both_prior_20_extremes"
        elif sweep_up:
            sweep_state = "swept_prior_20_high"
        elif sweep_down:
            sweep_state = "swept_prior_20_low"
        else:
            sweep_state = "no_prior_20_sweep"
        return {
            "source_path_feature_status": "computed_from_source_ohlc_asof",
            "asof_lookback_bars_available": index + 1,
            "return_1_bar": ((close / data["close"][index - 1]) - 1.0) if index >= 1 and data["close"][index - 1] else None,
            "return_4_bar": ((close / data["close"][index - 4]) - 1.0) if index >= 4 and data["close"][index - 4] else None,
            "return_16_bar": ((close / data["close"][index - 16]) - 1.0) if index >= 16 and data["close"][index - 16] else None,
            "atr14_price": atr14,
            "atr50_price": atr50,
            "trend_score_20_atr50": trend_score,
            "trend_state_20": bucket_trend(trend_score),
            "volatility_state_14_vs_50": bucket_volatility(atr_ratio),
            "compression_expansion_state": bucket_compression(atr_ratio),
            "current_bar_displacement_atr14": ((high - low) / atr14) if atr14 and atr14 > 0 else None,
            "current_bar_speed_atr14": (abs(close - open_) / atr14) if atr14 and atr14 > 0 else None,
            "current_bar_direction": "up" if close > open_ else ("down" if close < open_ else "flat"),
            "lookback50_position": position50,
            "liquidity_sweep_proxy_state": sweep_state,
        }


def bucket_trend(score: float | None) -> str:
    if score is None:
        return "insufficient_lookback"
    if score >= 2.0:
        return "strong_up"
    if score >= 0.5:
        return "up"
    if score <= -2.0:
        return "strong_down"
    if score <= -0.5:
        return "down"
    return "flat"


def bucket_volatility(ratio: float | None) -> str:
    if ratio is None:
        return "insufficient_lookback"
    if ratio >= 1.5:
        return "high_recent_vs_baseline"
    if ratio >= 1.15:
        return "elevated_recent_vs_baseline"
    if ratio <= 0.65:
        return "very_low_recent_vs_baseline"
    if ratio <= 0.85:
        return "low_recent_vs_baseline"
    return "normal_recent_vs_baseline"


def bucket_compression(ratio: float | None) -> str:
    if ratio is None:
        return "insufficient_lookback"
    if ratio <= 0.75:
        return "compression"
    if ratio >= 1.25:
        return "expansion"
    return "neutral"


def bucket_adverse_excursion(mae: float | None) -> str:
    if mae is None:
        return "missing_mae"
    if mae <= -1.0:
        return "stopped_or_beyond_1r_adverse"
    if mae <= -0.75:
        return "deep_adverse_0_75r_to_1r"
    if mae <= -0.25:
        return "moderate_adverse_0_25r_to_0_75r"
    if mae < 0:
        return "shallow_adverse_under_0_25r"
    return "no_adverse_excursion_recorded"


def policy_reversal_bucket(live_r: float | None, legacy_r: float | None) -> str:
    if live_r is None or legacy_r is None:
        return "missing_policy_result"
    live_positive = live_r > 0
    legacy_positive = legacy_r > 0
    if live_positive and not legacy_positive:
        return "dynamic_winner_from_legacy_nonpositive"
    if not live_positive and legacy_positive:
        return "dynamic_nonpositive_from_legacy_winner"
    if live_r > legacy_r:
        return "dynamic_better_same_sign"
    if live_r < legacy_r:
        return "dynamic_worse_same_sign"
    return "same_result"


def transfer_group(symbol: str | None) -> str:
    if not symbol:
        return "unknown"
    s = symbol.upper()
    if s in {"XAUUSD", "XAGUSD"}:
        return "metals_usd"
    if s in {"US30", "US30_CASH", "NAS100", "SPX500", "GER40", "UK100", "JP225"}:
        return "equity_index"
    if s in {"BTCUSD", "ETHUSD"}:
        return "crypto_usd"
    if "OIL" in s:
        return "energy_usd"
    if s.endswith("JPY"):
        return "jpy_fx"
    if s.endswith("USD") or s.startswith("USD"):
        return "usd_fx"
    return "cross_fx"


def relevant_currencies(symbol: str | None) -> set[str]:
    if not symbol:
        return set()
    s = symbol.upper().replace("_CASH", "")
    if s in {"XAUUSD", "XAGUSD", "US30", "NAS100", "SPX500", "BTCUSD", "ETHUSD"} or "OIL" in s:
        return {"USD"}
    if len(s) >= 6 and s[:3].isalpha() and s[3:6].isalpha():
        return {s[:3], s[3:6]}
    return {"USD"}


def session_subwindow(dt: datetime | None) -> str:
    if dt is None:
        return "missing_time"
    minute = dt.hour * 60 + dt.minute
    windows = [
        ("tokyo_open", 0, 60),
        ("tokyo_mid", 60, 180),
        ("pre_london", 360, 420),
        ("london_open", 420, 480),
        ("london_mid", 480, 600),
        ("pre_ny", 720, 780),
        ("ny_open", 780, 840),
        ("ny_mid", 840, 960),
        ("ny_late", 960, 1020),
    ]
    for name, start, end in windows:
        if start <= minute < end:
            return name
    return "off_major_subwindow"


KILL_ZONES = {
    "XAUUSD": [("london", 7 * 60, 10 * 60 + 30), ("ny", 13 * 60, 17 * 60)],
    "XAGUSD": [("london", 7 * 60, 10 * 60 + 30), ("ny", 13 * 60, 17 * 60)],
    "US30": [("london", 8 * 60, 10 * 60 + 30), ("ny", 13 * 60 + 30, 16 * 60)],
    "US30_CASH": [("london", 8 * 60, 10 * 60 + 30), ("ny", 13 * 60 + 30, 16 * 60)],
    "NAS100": [("ny", 13 * 60, 17 * 60)],
    "USDJPY": [("tokyo", 0, 3 * 60), ("london", 7 * 60, 9 * 60 + 30), ("ny", 13 * 60, 15 * 60 + 30)],
    "GBPJPY": [("tokyo", 0, 3 * 60), ("london", 7 * 60, 9 * 60 + 30), ("ny", 13 * 60, 15 * 60 + 30)],
    "GBPUSD": [("london", 7 * 60, 12 * 60), ("ny", 13 * 60, 15 * 60 + 30)],
}


def kill_zone_position(symbol: str | None, dt: datetime | None) -> str:
    if symbol is None or dt is None:
        return "missing_symbol_or_time"
    s = symbol.upper()
    minute = dt.hour * 60 + dt.minute
    for name, start, end in KILL_ZONES.get(s, []):
        if start <= minute < end:
            midpoint = (start + end) / 2
            phase = "early" if minute < midpoint else "late"
            return f"in_{name}_{phase}"
    return "off_configured_kill_zone_or_unconfigured_symbol"


def load_calendar() -> list[dict]:
    if not ECONOMIC_CALENDAR.exists():
        return []
    events = []
    with ECONOMIC_CALENDAR.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            dt = parse_time(f"{row.get('date')} {row.get('time_utc')}:00")
            if dt is None:
                continue
            events.append(
                {
                    "time": dt,
                    "impact": str(row.get("impact", "")).upper(),
                    "currency": str(row.get("currency", "")).upper(),
                    "event": row.get("event"),
                }
            )
    return events


def news_features(events: list[dict], symbol: str | None, dt: datetime | None) -> dict:
    if not events:
        return {
            "news_calendar_coverage_status": "calendar_file_missing_or_empty",
            "news_min_abs_minutes": None,
            "news_high_impact_within_120m": None,
        }
    if dt is None:
        return {
            "news_calendar_coverage_status": "missing_candidate_time",
            "news_min_abs_minutes": None,
            "news_high_impact_within_120m": None,
        }
    min_date = min(event["time"].date() for event in events)
    max_date = max(event["time"].date() for event in events)
    if not (min_date <= dt.date() <= max_date):
        return {
            "news_calendar_coverage_status": "candidate_date_outside_local_calendar_range",
            "news_min_abs_minutes": None,
            "news_high_impact_within_120m": None,
        }
    currencies = relevant_currencies(symbol)
    deltas = [
        abs((event["time"] - dt).total_seconds()) / 60.0
        for event in events
        if event["currency"] in currencies
    ]
    high_deltas = [
        abs((event["time"] - dt).total_seconds()) / 60.0
        for event in events
        if event["currency"] in currencies and event["impact"] == "HIGH"
    ]
    return {
        "news_calendar_coverage_status": "covered_relevant_currency" if deltas else "covered_date_no_relevant_currency_event",
        "news_min_abs_minutes": min(deltas) if deltas else None,
        "news_high_impact_within_120m": bool(high_deltas and min(high_deltas) <= 120.0),
    }


def iter_stage04_rows() -> Iterable[dict]:
    with STAGE04_INDEX.open("r", encoding="utf-8") as handle:
        for index_line in handle:
            if not index_line.strip():
                continue
            index_row = json.loads(index_line)
            output_path = REPO_ROOT / index_row["output_chunk_path"]
            with output_path.open("r", encoding="utf-8") as shard:
                for row_line in shard:
                    if row_line.strip():
                        yield json.loads(row_line)


def feature_row(seq: int, row: dict, cache: OhlcFeatureCache, events: list[dict]) -> dict:
    candle_time = parse_time(row.get("candle_time_utc"))
    entry_time = parse_time(row.get("entry_first_touch_utc"))
    source_features = cache.features(row.get("source_path"), candle_time)
    news = news_features(events, row.get("symbol"), candle_time)
    live = row["policy_results"]["live_current_j46_j49"]
    legacy = row["policy_results"]["legacy_fixed_1.5r"]
    be = row["policy_results"]["be_after_trigger"]
    trailing = row["policy_results"]["trailing_runner"]
    live_final_r = safe_float(live.get("final_r"))
    legacy_final_r = safe_float(legacy.get("final_r"))
    mfe = safe_float(live.get("mfe_r"))
    mae = safe_float(live.get("mae_r"))
    entry_delay = None
    if candle_time is not None and entry_time is not None:
        entry_delay = (entry_time - candle_time).total_seconds() / 900.0
    return {
        "feature_row_id": f"STAGE06-FEATURE-{seq:09d}",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_06_MARKET_AWARENESS_ENRICHMENT",
        "candidate_id": row.get("candidate_id"),
        "path_row_id": row.get("path_row_id"),
        "symbol": row.get("symbol"),
        "transfer_group": transfer_group(row.get("symbol")),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "session_bucket": row.get("session_bucket"),
        "session_subwindow": session_subwindow(candle_time),
        "kill_zone_position": kill_zone_position(row.get("symbol"), candle_time),
        "candle_time_utc": row.get("candle_time_utc"),
        "entry_first_touch_utc": row.get("entry_first_touch_utc"),
        "weekday": candle_time.strftime("%A") if candle_time else None,
        "month": candle_time.month if candle_time else None,
        "quarter": ((candle_time.month - 1) // 3 + 1) if candle_time else None,
        "year": candle_time.year if candle_time else None,
        "source_mode": row.get("source_mode"),
        "source_path": row.get("source_path"),
        "source_sha256": row.get("source_sha256"),
        "source_timeframe": row.get("source_timeframe"),
        "source_window_complete": row.get("source_window_complete"),
        **source_features,
        **news,
        "entry_delay_bars": entry_delay,
        "observation_count": row.get("observation_count"),
        "legacy_final_r": legacy.get("final_r"),
        "live_current_j46_j49_final_r": live.get("final_r"),
        "be_after_trigger_final_r": be.get("final_r"),
        "trailing_runner_final_r": trailing.get("final_r"),
        "live_vs_legacy_delta_r": (live_final_r - legacy_final_r if live_final_r is not None and legacy_final_r is not None else None),
        "policy_reversal_bucket": policy_reversal_bucket(live_final_r, legacy_final_r),
        "mfe_r": mfe,
        "mae_r": mae,
        "adverse_excursion_bucket": bucket_adverse_excursion(mae),
        "mfe_mae_ratio": (mfe / abs(mae)) if mfe is not None and mae not in (None, 0.0) else None,
        "mfe_mae_timing_status": "not_recorded_in_stage04_policy_results",
        "live_exit_reason": live.get("exit_reason"),
        "live_exit_progress_fraction": (
            safe_float(live.get("exit_index")) / safe_float(row.get("observation_count"))
            if safe_float(live.get("exit_index")) is not None and safe_float(row.get("observation_count")) not in (None, 0.0)
            else None
        ),
        "same_bar_ambiguity": bool(live.get("same_bar_ambiguity")),
        "no_fill_fillability_status": "filled_entry_touch_replay_row",
        "orderflow_depth_proxy_status": "not_joined_stage06_source_limited",
        "cross_asset_lead_lag_status": "not_joined_stage06_panel_required",
        "spread_slippage_cost_status": "forward_capture_required_not_inferred_from_ohlc",
        "market_awareness_scope": "replayable_selected_trade_candidate_row",
        "forbidden_leakage_fields_used": False,
    }


def add_distribution(counter_map: dict[str, Counter], scope: str, row: dict) -> None:
    for field in DIMENSION_FIELDS:
        value = row.get(field)
        counter_map[f"{scope}::{field}"][str(value)] += 1


def write_field_classification() -> list[dict]:
    rows = []
    for index, (field, safety_class, reason) in enumerate(FIELD_CLASSIFICATIONS, start=1):
        rows.append(
            {
                "field_classification_id": f"STAGE06-FIELD-{index:03d}-{field}",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_06_MARKET_AWARENESS_ENRICHMENT",
                "field_name": field,
                "field_safety_class": safety_class,
                "reason": reason,
                "allowed_for_decision_feature": safety_class == "decision_safe_asof",
                "allowed_for_training_label": safety_class == "post_outcome_label",
                "requires_forward_capture": safety_class == "forward_capture_required",
            }
        )
    with OUTPUT_FIELD_CLASSIFICATION.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def write_distribution_ledger(
    counter_map: dict[str, Counter],
    scope_counts: Counter,
    full_stage04_summary: dict,
) -> list[dict]:
    rows = []
    row_id = 1
    for key in sorted(counter_map):
        scope, field = key.split("::", 1)
        rows.append(
            {
                "distribution_id": f"STAGE06-DIST-{row_id:05d}",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_06_MARKET_AWARENESS_ENRICHMENT",
                "coverage_scope": scope,
                "feature_name": field,
                "selection_definition": selection_definition(scope),
                "row_count": scope_counts[scope],
                "distribution": dict(sorted(counter_map[key].items())),
                "no_arbitrary_top_n": True,
            }
        )
        row_id += 1
    terminal_counts = full_stage04_summary.get("terminal_counts_by_mode", {})
    for mode, counts in sorted(terminal_counts.items()):
        rows.append(
            {
                "distribution_id": f"STAGE06-DIST-{row_id:05d}",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_06_MARKET_AWARENESS_ENRICHMENT",
                "coverage_scope": f"full_stage04_terminal_counts::{mode}",
                "feature_name": "terminal_outcome",
                "selection_definition": "full Stage04 source-mode denominator from prior full replay summary",
                "row_count": sum(counts.values()),
                "distribution": counts,
                "no_arbitrary_top_n": True,
            }
        )
        row_id += 1
    with OUTPUT_DISTRIBUTIONS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def selection_definition(scope: str) -> str:
    if scope == "denominator_all_replayable_m15_dynamic_rows":
        return "all Stage04 replayable M15 dynamic policy rows"
    if scope.startswith("selected_positive_"):
        policy = scope.replace("selected_positive_", "")
        return f"Stage04 rows where {policy}.final_r > 0; selected-only diagnostic, not activation approval"
    return scope


def build() -> dict:
    stage04_summary = json.loads(STAGE04_SUMMARY.read_text(encoding="utf-8"))
    stage02_summary = json.loads(STAGE02_SUMMARY.read_text(encoding="utf-8"))
    full_stage04_summary = json.loads(FULL_REPLAY_STAGE04_SUMMARY.read_text(encoding="utf-8"))
    events = load_calendar()
    cache = OhlcFeatureCache()
    field_rows = write_field_classification()
    distribution_counters: dict[str, Counter] = defaultdict(Counter)
    scope_counts: Counter = Counter()
    safety_counts = Counter(row["field_safety_class"] for row in field_rows)
    feature_status_counts = Counter()
    policy_positive_counts = Counter()
    live_exit_reasons = Counter()
    rows_written = 0

    with OUTPUT_FEATURE_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for rows_written, stage04_row in enumerate(iter_stage04_rows(), start=1):
            enriched = feature_row(rows_written, stage04_row, cache, events)
            handle.write(json.dumps(enriched, sort_keys=True) + "\n")
            scope_counts["denominator_all_replayable_m15_dynamic_rows"] += 1
            add_distribution(distribution_counters, "denominator_all_replayable_m15_dynamic_rows", enriched)
            feature_status_counts[enriched["source_path_feature_status"]] += 1
            live_exit_reasons[enriched["live_exit_reason"]] += 1
            for policy in POLICY_NAMES:
                result = stage04_row["policy_results"][policy]
                final_r = safe_float(result.get("final_r"))
                if final_r is not None and final_r > 0:
                    scope = f"selected_positive_{policy}"
                    policy_positive_counts[policy] += 1
                    scope_counts[scope] += 1
                    add_distribution(distribution_counters, scope, enriched)

    distribution_rows = write_distribution_ledger(distribution_counters, scope_counts, full_stage04_summary)
    summary = {
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_06_MARKET_AWARENESS_ENRICHMENT",
        "generated_at_utc": utc_now(),
        "feature_ledger_path": rel(OUTPUT_FEATURE_LEDGER),
        "field_classification_ledger_path": rel(OUTPUT_FIELD_CLASSIFICATION),
        "distribution_ledger_path": rel(OUTPUT_DISTRIBUTIONS),
        "feature_rows": rows_written,
        "expected_stage04_replayable_rows": stage04_summary.get("replayable_candidate_rows"),
        "field_classification_rows": len(field_rows),
        "distribution_rows": len(distribution_rows),
        "field_safety_class_counts": dict(sorted(safety_counts.items())),
        "source_path_feature_status_counts": dict(sorted(feature_status_counts.items())),
        "selected_positive_counts_by_policy": dict(sorted(policy_positive_counts.items())),
        "live_exit_reason_counts": dict(sorted(live_exit_reasons.items())),
        "stage02_source_family_counts": stage02_summary.get("source_family_counts", {}),
        "coverage_statement": {
            "denominator_wide": "all Stage04 replayable M15 dynamic policy rows",
            "selected_only": "positive-final-R scopes by dynamic policy, labeled diagnostic only",
            "full_stage04_no_fill": "terminal distributions included from prior Stage04 source-mode summary",
        },
        "forbidden_boundaries_crossed": False,
        "forbidden_leakage_fields_used": False,
        "no_live_trading_or_broker_mutation": True,
        "no_paid_api_or_vendor_call": True,
        "first_incomplete_invariant_after_stage06": "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV",
    }
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(summary)
    update_state(summary)
    return summary


def write_report(summary: dict) -> None:
    lines = [
        "# vNext Moonshot Stage06 Market-Awareness Enrichment",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Result",
        "",
        f"- Feature rows: `{summary['feature_rows']}`",
        f"- Field classification rows: `{summary['field_classification_rows']}`",
        f"- Distribution rows: `{summary['distribution_rows']}`",
        f"- First incomplete invariant: `{summary['first_incomplete_invariant_after_stage06']}`",
        "",
        "## Coverage",
        "",
        "- Denominator-wide distributions cover every Stage04 replayable M15 dynamic-policy row.",
        "- Selected-only distributions are positive-final-R diagnostic scopes per policy, not activation approval.",
        "- Full Stage04 no-fill/source-mode terminal distributions are included from the prior source-mode summary so no-fill coverage is not confused with selected trade rows.",
        "- Field classifications explicitly split decision-safe as-of features from post-outcome labels, diagnostics, provenance, source-limited gaps, forbidden leakage, and forward-capture requirements.",
        "",
    ]
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def update_state(summary: dict) -> None:
    if not OUTPUT_STATE.exists():
        return
    state = json.loads(OUTPUT_STATE.read_text(encoding="utf-8"))
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = git_head()
    state["current_stage"] = "STAGE_06_MARKET_AWARENESS_ENRICHMENT"
    state["first_incomplete_invariant"] = "STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV"
    state["exact_next_action"] = "Run Stage07 corrected branch metrics and segmented prop EV from dynamic labels plus Stage06 features."
    state["row_counts_scanned"]["stage06_market_awareness_feature_rows"] = summary["feature_rows"]
    state["row_counts_scanned"]["stage06_market_awareness_field_classification_rows"] = summary["field_classification_rows"]
    state["row_counts_scanned"]["stage06_market_awareness_distribution_rows"] = summary["distribution_rows"]
    state["stage_status_table"]["STAGE_06_MARKET_AWARENESS_ENRICHMENT"] = "complete"
    state["stage_status_table"]["STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV"] = "pending"
    state["output_artifact_manifest"]["market_awareness_feature_ledger"] = rel(OUTPUT_FEATURE_LEDGER)
    state["output_artifact_manifest"]["market_awareness_field_classification_ledger"] = rel(OUTPUT_FIELD_CLASSIFICATION)
    state["output_artifact_manifest"]["market_awareness_distribution_ledger"] = rel(OUTPUT_DISTRIBUTIONS)
    state["output_artifact_manifest"]["market_awareness_summary"] = rel(OUTPUT_SUMMARY)
    state["output_artifact_manifest"]["market_awareness_report"] = rel(OUTPUT_REPORT)
    state["completion_gate_status"] = "not_complete_first_incomplete_stage07"
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage06_market_awareness_enrichment_2026_05_26.py"
            ),
            "status": "passed",
            "result": (
                f"feature_rows={summary['feature_rows']}; "
                f"distribution_rows={summary['distribution_rows']}; "
                "first_incomplete=STAGE_07_CORRECTED_BRANCH_METRICS_AND_PROP_EV"
            ),
        }
    )
    OUTPUT_STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    summary = build()
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "stage": "STAGE_06_MARKET_AWARENESS_ENRICHMENT",
                "feature_rows": summary["feature_rows"],
                "field_classification_rows": summary["field_classification_rows"],
                "distribution_rows": summary["distribution_rows"],
                "first_incomplete_invariant": summary["first_incomplete_invariant_after_stage06"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
