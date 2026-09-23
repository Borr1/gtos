from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


DATE = "2026-05-26"
FULL_REPLAY_DATE = "2026-05-24"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_broader_origin_ohlc_context_replay_prototype"
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from src.research.dynamic_execution_policy import (  # noqa: E402
    be_only_policy,
    legacy_fixed_target_policy,
    observation_from_ohlc,
    simulate_policy,
)

ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)
FULL_REPLAY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24"
)

STAGE02_BUILDER = FULL_REPLAY_DIR / "build_vnext_full_replay_stage02_candidate_generation_2026_05_24.py"
STAGE04_BUILDER = FULL_REPLAY_DIR / "build_vnext_full_replay_stage04_source_mode_path_r_2026_05_24.py"
STAGE05_BUILDER = FULL_REPLAY_DIR / "build_vnext_full_replay_stage05_dominance_mixed_2026_05_24.py"
STAGE05_SHARD_STATUS = FULL_REPLAY_DIR / f"VNEXT_FULL_REPLAY_STAGE05_SHARD_STATUS_LEDGER_{FULL_REPLAY_DATE}.jsonl"
STAGE05_ACTIVATED_MANIFEST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_{DATE}.jsonl"
)
MARKET_AWARENESS_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_MARKET_AWARENESS_FEATURE_LEDGER_{DATE}.jsonl"
ML_FEATURE_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_FEATURE_LEDGER_{DATE}.jsonl"
STAGE10_ROUTER_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_DEFAULT_OFF_ROUTER_REPLAY_LEDGER_{DATE}.jsonl"
STAGE10_VERIFICATION = MOONSHOT_DIR / f"VNEXT_MOONSHOT_STAGE10_VERIFICATION_RESULT_{DATE}.json"
SOURCE_CAPABILITY_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_LEDGER_{DATE}.jsonl"
SOURCE_CAPABILITY_SUMMARY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE}.json"
ORIGIN_REGISTRY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_{DATE}.jsonl"
ORIGIN_SUMMARY = MOONSHOT_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_SUMMARY_{DATE}.json"
STAGE06_MARKET_AWARENESS_BUILDER = (
    MOONSHOT_DIR / "build_vnext_moonshot_stage06_market_awareness_enrichment_2026_05_26.py"
)
STAGE10_BUILDER = MOONSHOT_DIR / "build_vnext_moonshot_stage10_runtime_integration_2026_05_26.py"
ECONOMIC_CALENDAR = REPO_ROOT / "data/economic_calendar.csv"
CNR_CANDIDATES = REPO_ROOT / "shadow_logs/continuation_no_retrace_candidates.jsonl"
CNR_RESOLUTIONS = REPO_ROOT / "shadow_logs/continuation_no_retrace_resolutions.jsonl"

OUTPUT_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_CONTRACT_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_SUMMARY_{DATE}.json"
)
OUTPUT_PATHS_READ = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_PATHS_READ_{DATE}.json"
)

TARGET_FAMILIES = (
    "liquidity_sweep_reclaim",
    "displacement_continuation",
    "volatility_compression_expansion",
    "session_open_range_break",
    "regime_transition_break",
    "news_volatility_reprice",
    "cross_asset_lead_lag",
    "structural_distance_extreme",
    "continuation_no_retrace",
)

SESSION_WINDOWS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "XAUUSD": (("london", "07:00", "10:30"), ("ny", "13:00", "17:00")),
    "XAGUSD": (("london", "07:00", "10:30"), ("ny", "13:00", "17:00")),
    "US30": (("london", "08:00", "10:30"), ("ny", "13:30", "16:00")),
    "US30_cash": (("london", "08:00", "10:30"), ("ny", "13:30", "16:00")),
    "NAS100": (("ny", "13:00", "17:00"),),
    "USDJPY": (("tokyo", "00:00", "03:00"), ("london", "07:00", "09:30"), ("ny", "13:00", "15:30")),
    "GBPJPY": (("tokyo", "00:00", "03:00"), ("london", "07:00", "09:30"), ("ny", "13:00", "15:30")),
    "GBPUSD": (("london", "07:00", "12:00"), ("ny", "13:00", "15:30")),
    "EURUSD": (("london", "07:00", "12:00"), ("ny", "13:00", "15:30")),
    "NZDUSD": (("london", "07:00", "12:00"), ("ny", "13:00", "15:30")),
    "UK100": (("london", "08:00", "10:30"),),
}

LEAD_LAG_PAIRS = (
    ("XAGUSD", "XAUUSD"),
    ("XAUUSD", "XAGUSD"),
    ("NAS100", "US30_cash"),
    ("US30_cash", "NAS100"),
    ("USDJPY", "GBPJPY"),
    ("GBPJPY", "USDJPY"),
)
SELECTED_DYNAMIC_POLICY = "be_after_trigger"
SAME_BAR_POLICY = "conservative"
REPLAY_HORIZON_BARS = 192


@dataclass
class BarSeries:
    source_path: str
    source_sha256: str
    symbol: str
    timeframe: str
    times: list[datetime]
    opens: list[float]
    highs: list[float]
    lows: list[float]
    closes: list[float]


@dataclass
class Candidate:
    origin_family: str
    symbol: str
    timeframe: str
    decision_time: datetime
    side: str
    entry: float
    stop: float
    target: float
    source_path: str
    source_sha256: str
    source_row_index: int | None
    source_fields: dict[str, Any]
    blocker_class: str | None = None
    blocker_detail: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


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
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def dt_s(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def fnum(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:length]}"


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def read_csv_series(source_path: str, source_sha256: str | None = None) -> BarSeries | None:
    path = repo_path(source_path)
    if not path.exists() or path.suffix.lower() != ".csv":
        return None
    times: list[datetime] = []
    opens: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"time", "open", "high", "low", "close"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            return None
        for row in reader:
            parsed = parse_time(row.get("time"))
            if parsed is None:
                continue
            try:
                open_ = float(row["open"])
                high = float(row["high"])
                low = float(row["low"])
                close = float(row["close"])
            except (TypeError, ValueError):
                continue
            times.append(parsed)
            opens.append(open_)
            highs.append(high)
            lows.append(low)
            closes.append(close)
    if not times:
        return None
    symbol = path.stem.split("_")[0]
    timeframe = "M15"
    for token in ("M15", "M5", "M1", "H1", "H4", "D1"):
        if f"_{token}" in path.stem or path.stem.endswith(token):
            timeframe = token
            break
    return BarSeries(
        source_path=rel(path),
        source_sha256=source_sha256 or sha256_file(path) or "sha256_unavailable",
        symbol=symbol,
        timeframe=timeframe,
        times=times,
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
    )


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def prior_high(series: BarSeries, index: int, lookback: int) -> float | None:
    start = max(0, index - lookback)
    return max(series.highs[start:index]) if index > start else None


def prior_low(series: BarSeries, index: int, lookback: int) -> float | None:
    start = max(0, index - lookback)
    return min(series.lows[start:index]) if index > start else None


def atr(series: BarSeries, index: int, lookback: int) -> float | None:
    start = max(0, index - lookback + 1)
    ranges = [series.highs[pos] - series.lows[pos] for pos in range(start, index + 1)]
    return mean(ranges)


def close_position(series: BarSeries, index: int, lookback: int) -> float | None:
    start = max(0, index - lookback + 1)
    high = max(series.highs[start : index + 1])
    low = min(series.lows[start : index + 1])
    if high <= low:
        return None
    return (series.closes[index] - low) / (high - low)


def trend_state(series: BarSeries, index: int, atr50: float | None) -> str:
    if index < 20 or not atr50 or atr50 <= 0:
        return "insufficient_lookback"
    score = (series.closes[index] - series.closes[index - 20]) / atr50
    if score >= 2.0:
        return "strong_up"
    if score >= 0.75:
        return "up"
    if score <= -2.0:
        return "strong_down"
    if score <= -0.75:
        return "down"
    return "flat"


def session_at(symbol: str, ts: datetime) -> str:
    for name, start, end in SESSION_WINDOWS.get(symbol, ()):
        start_h, start_m = [int(part) for part in start.split(":")]
        end_h, end_m = [int(part) for part in end.split(":")]
        start_dt = ts.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        end_dt = ts.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
        if start_dt <= ts < end_dt:
            return name
    return "off_configured_session"


def make_trade_candidate(
    *,
    origin_family: str,
    series: BarSeries,
    index: int,
    side: str,
    entry: float,
    stop: float,
    target: float | None = None,
    source_fields: dict[str, Any],
    blocker_class: str | None = None,
    blocker_detail: str | None = None,
) -> Candidate:
    risk = abs(entry - stop)
    if target is None and risk > 0:
        target = entry + 1.5 * risk if side == "LONG" else entry - 1.5 * risk
    if target is None:
        target = entry
    return Candidate(
        origin_family=origin_family,
        symbol=series.symbol,
        timeframe=series.timeframe,
        decision_time=series.times[index],
        side=side,
        entry=entry,
        stop=stop,
        target=target,
        source_path=series.source_path,
        source_sha256=series.source_sha256,
        source_row_index=index,
        source_fields=source_fields,
        blocker_class=blocker_class,
        blocker_detail=blocker_detail,
    )


def valid_geometry(entry: float, stop: float, target: float, side: str) -> bool:
    if side == "LONG":
        return stop < entry < target
    if side == "SHORT":
        return target < entry < stop
    return False


def simulate_fixed_r(series: BarSeries, candidate: Candidate, horizon_bars: int = 192) -> dict[str, Any]:
    if not valid_geometry(candidate.entry, candidate.stop, candidate.target, candidate.side):
        return {
            "prototype_replay_status": "blocked",
            "blocker_class": "invalid_generated_entry_stop_target_geometry",
            "final_r": None,
        }
    start = int(candidate.source_row_index or 0)
    end = min(len(series.times), start + horizon_bars + 1)
    risk = abs(candidate.entry - candidate.stop)
    entry_hit: int | None = None
    stop_hit: int | None = None
    target_hit: int | None = None
    for pos in range(start, end):
        if series.lows[pos] <= candidate.entry <= series.highs[pos]:
            entry_hit = pos
            break
    if entry_hit is None:
        return {
            "prototype_replay_status": "replayed_no_fill",
            "entry_touched": False,
            "entry_first_touch_utc": None,
            "terminal_outcome": "no_fill",
            "final_r": 0.0,
            "blocker_class": "full_dynamic_replay_not_wired_for_non_current_origin",
        }
    for pos in range(entry_hit, end):
        if candidate.side == "LONG":
            stop_now = series.lows[pos] <= candidate.stop
            target_now = series.highs[pos] >= candidate.target
        else:
            stop_now = series.highs[pos] >= candidate.stop
            target_now = series.lows[pos] <= candidate.target
        if stop_now and stop_hit is None:
            stop_hit = pos
        if target_now and target_hit is None:
            target_hit = pos
        if stop_hit is not None or target_hit is not None:
            break
    post_high = max(series.highs[entry_hit:end])
    post_low = min(series.lows[entry_hit:end])
    if candidate.side == "LONG":
        mfe_r = (post_high - candidate.entry) / risk
        mae_r = (post_low - candidate.entry) / risk
    else:
        mfe_r = (candidate.entry - post_low) / risk
        mae_r = (candidate.entry - post_high) / risk
    if stop_hit is not None and target_hit is not None and stop_hit == target_hit:
        terminal = "same_bar_ambiguous_unresolved"
        final_r = None
    elif target_hit is not None and (stop_hit is None or target_hit < stop_hit):
        terminal = "target_first"
        final_r = abs(candidate.target - candidate.entry) / risk
    elif stop_hit is not None:
        terminal = "stop_first"
        final_r = -1.0
    else:
        terminal = "timeout_mark_to_market"
        last_close = series.closes[end - 1]
        final_r = (last_close - candidate.entry) / risk if candidate.side == "LONG" else (candidate.entry - last_close) / risk
    return {
        "prototype_replay_status": "replayed_fixed_r_ohlc",
        "entry_touched": True,
        "entry_index": entry_hit,
        "path_end_index": end,
        "entry_first_touch_utc": dt_s(series.times[entry_hit]),
        "sl_first_touch_utc": dt_s(series.times[stop_hit]) if stop_hit is not None else None,
        "tp_first_touch_utc": dt_s(series.times[target_hit]) if target_hit is not None else None,
        "terminal_outcome": terminal,
        "final_r": final_r,
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "blocker_class": "full_dynamic_replay_not_wired_for_non_current_origin",
    }


def policy_result_record(result: Any) -> dict[str, Any]:
    return {
        "replay_status": result.replay_status,
        "final_r": result.final_r,
        "exit_reason": result.exit_reason,
        "exit_index": result.exit_index,
        "exit_time_utc": result.exit_time_utc,
        "mfe_r": result.mfe_r,
        "mae_r": result.mae_r,
        "partial_realized_r": result.partial_realized_r,
        "remaining_fraction": result.remaining_fraction,
        "stop_r_at_exit": result.stop_r_at_exit,
        "same_bar_ambiguity": result.same_bar_ambiguity,
        "source_gap_reason": result.source_gap_reason,
    }


def simulate_origin_native_dynamic_policy(
    series: BarSeries | None,
    candidate: Candidate,
    prototype_replay: dict[str, Any],
    horizon_bars: int = REPLAY_HORIZON_BARS,
) -> dict[str, Any]:
    if series is None:
        return {
            "available": False,
            "source_replay_mode": "bar_close_m15",
            "same_bar_policy": SAME_BAR_POLICY,
            "selected_policy": SELECTED_DYNAMIC_POLICY,
            "selected_policy_final_r": None,
            "blocker_class": candidate.blocker_class or "missing_source_series_for_origin_native_dynamic_replay",
            "source_gap_reason": "missing_source_series",
        }
    if not valid_geometry(candidate.entry, candidate.stop, candidate.target, candidate.side):
        return {
            "available": False,
            "source_replay_mode": "bar_close_m15",
            "same_bar_policy": SAME_BAR_POLICY,
            "selected_policy": SELECTED_DYNAMIC_POLICY,
            "selected_policy_final_r": None,
            "blocker_class": "invalid_generated_entry_stop_target_geometry",
            "source_gap_reason": "invalid_geometry",
        }
    entry_index = prototype_replay.get("entry_index")
    if not isinstance(entry_index, int):
        return {
            "available": False,
            "source_replay_mode": "bar_close_m15",
            "same_bar_policy": SAME_BAR_POLICY,
            "selected_policy": SELECTED_DYNAMIC_POLICY,
            "selected_policy_final_r": None,
            "blocker_class": candidate.blocker_class
            or "origin_native_dynamic_replay_requires_entry_touch",
            "source_gap_reason": "entry_not_touched_or_not_measured",
        }
    end = min(len(series.times), entry_index + horizon_bars + 1)
    observations = []
    for local_index, pos in enumerate(range(entry_index, end), start=1):
        row = {
            "time": dt_s(series.times[pos]),
            "open": series.opens[pos],
            "high": series.highs[pos],
            "low": series.lows[pos],
            "close": series.closes[pos],
        }
        try:
            observations.append(
                observation_from_ohlc(
                    index=local_index,
                    row=row,
                    entry=candidate.entry,
                    stop=candidate.stop,
                    side=candidate.side,
                    time_key="time",
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            return {
                "available": False,
                "source_replay_mode": "bar_close_m15",
                "same_bar_policy": SAME_BAR_POLICY,
                "selected_policy": SELECTED_DYNAMIC_POLICY,
                "selected_policy_final_r": None,
                "blocker_class": "origin_native_dynamic_observation_build_error",
                "source_gap_reason": str(exc),
            }
    if not observations:
        return {
            "available": False,
            "source_replay_mode": "bar_close_m15",
            "same_bar_policy": SAME_BAR_POLICY,
            "selected_policy": SELECTED_DYNAMIC_POLICY,
            "selected_policy_final_r": None,
            "blocker_class": "origin_native_dynamic_no_ordered_observations",
            "source_gap_reason": "empty_observation_window",
        }
    selected_result = simulate_policy(
        be_only_policy(),
        observations,
        same_bar_policy=SAME_BAR_POLICY,
    )
    fixed_result = simulate_policy(
        legacy_fixed_target_policy(1.5),
        observations,
        same_bar_policy=SAME_BAR_POLICY,
    )
    selected_record = policy_result_record(selected_result)
    fixed_record = policy_result_record(fixed_result)
    blocker = None
    if selected_result.final_r is None:
        blocker = "origin_native_dynamic_policy_final_r_missing"
    elif selected_result.same_bar_ambiguity:
        blocker = "selected_policy_ordered_ltf_or_tick_path_required"
    return {
        "available": selected_result.final_r is not None,
        "source_replay_mode": "bar_close_m15",
        "same_bar_policy": SAME_BAR_POLICY,
        "observation_count": len(observations),
        "entry_first_touch_utc": dt_s(series.times[entry_index]),
        "path_window_end_utc": dt_s(series.times[end - 1]),
        "selected_policy": SELECTED_DYNAMIC_POLICY,
        "selected_policy_final_r": selected_result.final_r,
        "selected_policy_exit_reason": selected_result.exit_reason,
        "selected_policy_same_bar_ambiguity": selected_result.same_bar_ambiguity,
        "policy_results": {
            SELECTED_DYNAMIC_POLICY: selected_record,
            "legacy_fixed_1.5r": fixed_record,
        },
        "comparator_delta_be_vs_fixed_1_5r": (
            selected_result.final_r - fixed_result.final_r
            if selected_result.final_r is not None and fixed_result.final_r is not None
            else None
        ),
        "blocker_class": blocker,
        "source_gap_reason": selected_result.source_gap_reason,
    }


def generate_from_series(series: BarSeries, calendar_events: dict[str, list[dict[str, Any]]]) -> Iterator[Candidate]:
    previous_trend = "insufficient_lookback"
    emitted_session_breaks: set[tuple[str, str, str]] = set()
    for i in range(50, len(series.times)):
        ts = series.times[i]
        open_ = series.opens[i]
        high = series.highs[i]
        low = series.lows[i]
        close = series.closes[i]
        atr14 = atr(series, i, 14)
        atr50 = atr(series, i, 50)
        if not atr14 or atr14 <= 0 or not atr50 or atr50 <= 0:
            continue
        p_high20 = prior_high(series, i, 20)
        p_low20 = prior_low(series, i, 20)
        p_high50 = prior_high(series, i, 50)
        p_low50 = prior_low(series, i, 50)
        if p_high20 is None or p_low20 is None or p_high50 is None or p_low50 is None:
            continue
        body = abs(close - open_)
        bar_range = high - low
        atr_ratio = atr14 / atr50
        trend = trend_state(series, i, atr50)
        session = session_at(series.symbol, ts)
        base_fields = {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "atr14": atr14,
            "atr50": atr50,
            "atr14_atr50_ratio": atr_ratio,
            "prior_20_high": p_high20,
            "prior_20_low": p_low20,
            "prior_50_high": p_high50,
            "prior_50_low": p_low50,
            "trend_state_20": trend,
            "session_at_candidate": session,
        }

        swept_high = high > p_high20 and close < p_high20
        swept_low = low < p_low20 and close > p_low20
        if swept_high and not swept_low:
            yield make_trade_candidate(
                origin_family="liquidity_sweep_reclaim",
                series=series,
                index=i,
                side="SHORT",
                entry=close,
                stop=high + 0.25 * atr14,
                source_fields={**base_fields, "sweep_direction": "swept_prior_20_high_reclaimed_below"},
            )
        elif swept_low and not swept_high:
            yield make_trade_candidate(
                origin_family="liquidity_sweep_reclaim",
                series=series,
                index=i,
                side="LONG",
                entry=close,
                stop=low - 0.25 * atr14,
                source_fields={**base_fields, "sweep_direction": "swept_prior_20_low_reclaimed_above"},
            )

        if bar_range / atr14 >= 1.5 and body / atr14 >= 0.75:
            side = "LONG" if close > open_ else "SHORT"
            stop = low - 0.25 * atr14 if side == "LONG" else high + 0.25 * atr14
            yield make_trade_candidate(
                origin_family="displacement_continuation",
                series=series,
                index=i,
                side=side,
                entry=close,
                stop=stop,
                source_fields={**base_fields, "range_atr14": bar_range / atr14, "body_atr14": body / atr14},
            )

        prior_atr14 = atr(series, i - 1, 14)
        prior_atr50 = atr(series, i - 1, 50)
        prior_ratio = prior_atr14 / prior_atr50 if prior_atr14 and prior_atr50 else None
        expansion_break_up = close > p_high20
        expansion_break_down = close < p_low20
        if prior_ratio is not None and prior_ratio <= 0.75 and bar_range / atr14 >= 1.25:
            if expansion_break_up:
                yield make_trade_candidate(
                    origin_family="volatility_compression_expansion",
                    series=series,
                    index=i,
                    side="LONG",
                    entry=close,
                    stop=min(low, p_low20) - 0.20 * atr14,
                    source_fields={**base_fields, "prior_atr14_atr50_ratio": prior_ratio, "break_direction": "up"},
                )
            elif expansion_break_down:
                yield make_trade_candidate(
                    origin_family="volatility_compression_expansion",
                    series=series,
                    index=i,
                    side="SHORT",
                    entry=close,
                    stop=max(high, p_high20) + 0.20 * atr14,
                    source_fields={**base_fields, "prior_atr14_atr50_ratio": prior_ratio, "break_direction": "down"},
                )

        session_key = (series.symbol, ts.date().isoformat(), session)
        if session != "off_configured_session" and session_key not in emitted_session_breaks:
            range_start_index = i
            while range_start_index > 0 and series.times[range_start_index - 1].date() == ts.date() and session_at(series.symbol, series.times[range_start_index - 1]) == session:
                range_start_index -= 1
            range_close_index = range_start_index + 1
            if i > range_close_index:
                range_high = max(series.highs[range_start_index : range_close_index + 1])
                range_low = min(series.lows[range_start_index : range_close_index + 1])
                if close > range_high:
                    emitted_session_breaks.add(session_key)
                    yield make_trade_candidate(
                        origin_family="session_open_range_break",
                        series=series,
                        index=i,
                        side="LONG",
                        entry=close,
                        stop=range_low - 0.10 * atr14,
                        source_fields={**base_fields, "session": session, "open_range_high": range_high, "open_range_low": range_low, "range_closed_index": range_close_index},
                    )
                elif close < range_low:
                    emitted_session_breaks.add(session_key)
                    yield make_trade_candidate(
                        origin_family="session_open_range_break",
                        series=series,
                        index=i,
                        side="SHORT",
                        entry=close,
                        stop=range_high + 0.10 * atr14,
                        source_fields={**base_fields, "session": session, "open_range_high": range_high, "open_range_low": range_low, "range_closed_index": range_close_index},
                    )

        if trend == "strong_up" and previous_trend not in {"strong_up", "up"} and close > p_high20:
            yield make_trade_candidate(
                origin_family="regime_transition_break",
                series=series,
                index=i,
                side="LONG",
                entry=close,
                stop=p_low20 - 0.10 * atr14,
                source_fields={**base_fields, "previous_trend_state_20": previous_trend, "transition": "to_strong_up_break"},
            )
        elif trend == "strong_down" and previous_trend not in {"strong_down", "down"} and close < p_low20:
            yield make_trade_candidate(
                origin_family="regime_transition_break",
                series=series,
                index=i,
                side="SHORT",
                entry=close,
                stop=p_high20 + 0.10 * atr14,
                source_fields={**base_fields, "previous_trend_state_20": previous_trend, "transition": "to_strong_down_break"},
            )
        previous_trend = trend

        for event in calendar_events.get(ts.date().isoformat(), []):
            event_time = parse_time(event.get("event_time_utc"))
            if event_time is None or not (event_time <= ts < event_time + timedelta(minutes=30)):
                continue
            if bar_range / atr14 < 1.2:
                continue
            side = "LONG" if close >= open_ else "SHORT"
            stop = low - 0.25 * atr14 if side == "LONG" else high + 0.25 * atr14
            yield make_trade_candidate(
                origin_family="news_volatility_reprice",
                series=series,
                index=i,
                side=side,
                entry=close,
                stop=stop,
                source_fields={**base_fields, "calendar_event": event, "range_atr14": bar_range / atr14},
            )

        pos50 = close_position(series, i, 50)
        if pos50 is not None and pos50 >= 0.97:
            yield make_trade_candidate(
                origin_family="structural_distance_extreme",
                series=series,
                index=i,
                side="SHORT",
                entry=close,
                stop=high + 0.25 * atr14,
                source_fields={**base_fields, "lookback50_position": pos50, "extreme_side": "upper_range_extreme"},
            )
        elif pos50 is not None and pos50 <= 0.03:
            yield make_trade_candidate(
                origin_family="structural_distance_extreme",
                series=series,
                index=i,
                side="LONG",
                entry=close,
                stop=low - 0.25 * atr14,
                source_fields={**base_fields, "lookback50_position": pos50, "extreme_side": "lower_range_extreme"},
            )


def read_calendar_events() -> dict[str, list[dict[str, Any]]]:
    events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not ECONOMIC_CALENDAR.exists():
        return events
    with ECONOMIC_CALENDAR.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row.get("impact", "")).upper() != "HIGH":
                continue
            event_time = f"{row.get('date')}T{row.get('time_utc')}:00Z"
            events[str(row.get("date"))].append(
                {
                    "event_time_utc": event_time,
                    "event": row.get("event"),
                    "impact": row.get("impact"),
                    "currency": row.get("currency"),
                    "source_path": rel(ECONOMIC_CALENDAR),
                    "source_sha256": sha256_file(ECONOMIC_CALENDAR),
                }
            )
    return events


def load_source_paths() -> list[dict[str, Any]]:
    rows = []
    seen: set[str] = set()
    for row in iter_jsonl(STAGE05_ACTIVATED_MANIFEST):
        source_path = row.get("source_path")
        if not source_path or source_path in seen:
            continue
        seen.add(source_path)
        rows.append(
            {
                "source_path": source_path,
                "source_sha256": sha256_file(repo_path(source_path)),
                "source_index": row.get("source_index"),
            }
        )
    return rows


def source_path_checks(source_paths: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "path": item["source_path"],
            "sha256": item.get("source_sha256"),
            "exists": repo_path(item["source_path"]).exists(),
        }
        for item in source_paths
    ]


def load_cnr_candidates() -> list[Candidate]:
    rows: list[Candidate] = []
    if not CNR_CANDIDATES.exists():
        return rows
    shadow_hash = sha256_file(CNR_CANDIDATES)
    for index, row in enumerate(iter_jsonl(CNR_CANDIDATES), start=1):
        decision_time = parse_time(row.get("decision_time_utc"))
        geometry = row.get("original_trade_geometry") or {}
        side = geometry.get("side") or row.get("side")
        entry = fnum((row.get("decision_price_proxy") or {}).get("price"))
        stop = fnum(geometry.get("stop_loss"))
        target = fnum(geometry.get("take_profit_1"))
        if decision_time is None or side not in {"LONG", "SHORT"}:
            continue
        if entry is None:
            entry = fnum(geometry.get("entry_price")) or 0.0
        if stop is None:
            stop = entry
        if target is None:
            target = entry
        rows.append(
            Candidate(
                origin_family="continuation_no_retrace",
                symbol=str(row.get("symbol")),
                timeframe="shadow_decision_clock",
                decision_time=decision_time,
                side=side,
                entry=entry,
                stop=stop,
                target=target,
                source_path=rel(CNR_CANDIDATES),
                source_sha256=shadow_hash or "sha256_unavailable",
                source_row_index=index,
                source_fields={
                    "candidate_id": row.get("candidate_id"),
                    "source_decision_clock": row.get("decision_time_utc"),
                    "decision_price_proxy_status": (row.get("decision_price_proxy") or {}).get("price_source_status"),
                    "entry_models": row.get("entry_models"),
                    "original_trade_geometry": geometry,
                    "no_leak_status": row.get("no_leak_status"),
                    "resolution_source_path": rel(CNR_RESOLUTIONS) if CNR_RESOLUTIONS.exists() else None,
                    "resolution_source_sha256": sha256_file(CNR_RESOLUTIONS) if CNR_RESOLUTIONS.exists() else None,
                },
                blocker_class="strict_replay_entry_price_missing_or_proxy_only",
                blocker_detail="Shadow CNR decision clock is present, but executable decision-time quote/entry is missing or proxy-only; no origin-native dynamic final_r replay is available.",
            )
        )
    return rows


def build_cross_asset_candidates(series_by_symbol: dict[str, BarSeries]) -> list[Candidate]:
    rows: list[Candidate] = []
    for leader_symbol, lag_symbol in LEAD_LAG_PAIRS:
        leader = series_by_symbol.get(leader_symbol)
        lag = series_by_symbol.get(lag_symbol)
        if leader is None or lag is None:
            continue
        leader_time_index = {ts: idx for idx, ts in enumerate(leader.times)}
        for lag_index in range(50, len(lag.times)):
            ts = lag.times[lag_index]
            prev_ts = ts - timedelta(minutes=15)
            leader_index = leader_time_index.get(prev_ts)
            if leader_index is None or leader_index < 50:
                continue
            leader_atr = atr(leader, leader_index, 14)
            lag_atr = atr(lag, lag_index, 14)
            if not leader_atr or not lag_atr:
                continue
            leader_move = leader.closes[leader_index] - leader.closes[leader_index - 1]
            lag_move = lag.closes[lag_index] - lag.closes[lag_index - 1]
            leader_impulse = abs(leader_move) / leader_atr
            lag_response = abs(lag_move) / lag_atr
            if leader_impulse < 1.0 or lag_response > 0.5:
                continue
            side = "LONG" if leader_move > 0 else "SHORT"
            entry = lag.closes[lag_index]
            stop = lag.lows[lag_index] - 0.25 * lag_atr if side == "LONG" else lag.highs[lag_index] + 0.25 * lag_atr
            rows.append(
                make_trade_candidate(
                    origin_family="cross_asset_lead_lag",
                    series=lag,
                    index=lag_index,
                    side=side,
                    entry=entry,
                    stop=stop,
                    source_fields={
                        "leader_symbol": leader_symbol,
                        "lag_symbol": lag_symbol,
                        "leader_source_path": leader.source_path,
                        "leader_source_sha256": leader.source_sha256,
                        "leader_move_time_utc": dt_s(prev_ts),
                        "leader_move_atr14": leader_impulse,
                        "lag_prior_response_atr14": lag_response,
                        "leader_move_price": leader_move,
                        "lag_move_price": lag_move,
                    },
                )
            )
    return rows


def candidate_to_row(
    candidate: Candidate,
    series: BarSeries | None,
    replay: dict[str, Any],
    dynamic_replay: dict[str, Any],
) -> dict[str, Any]:
    final_r = replay.get("final_r")
    prototype_replayed = replay.get("prototype_replay_status") in {
        "replayed_fixed_r_ohlc",
        "replayed_no_fill",
    }
    dynamic_final_r = fnum(dynamic_replay.get("selected_policy_final_r"))
    origin_native_dynamic_replayed = bool(
        dynamic_replay.get("available")
        and dynamic_final_r is not None
    )
    selected_same_bar = bool(dynamic_replay.get("selected_policy_same_bar_ambiguity"))
    activation_ready = bool(
        origin_native_dynamic_replayed
        and not selected_same_bar
        and candidate.blocker_class is None
        and valid_geometry(candidate.entry, candidate.stop, candidate.target, candidate.side)
    )
    blocker = None if activation_ready else (
        candidate.blocker_class
        or dynamic_replay.get("blocker_class")
        or replay.get("blocker_class")
        or "origin_native_dynamic_policy_replay_not_activation_ready"
    )
    blocker_detail = None if activation_ready else (
        candidate.blocker_detail
        or dynamic_replay.get("source_gap_reason")
        or "Origin-native dynamic policy replay exists only as route-local Stage13 evidence; runtime candidate generator and verifier application must be patched before production activation."
    )
    row_id = stable_id(
        "broad_origin",
        {
            "origin": candidate.origin_family,
            "symbol": candidate.symbol,
            "time": dt_s(candidate.decision_time),
            "side": candidate.side,
            "entry": candidate.entry,
            "source": candidate.source_path,
        },
    )
    return {
        "schema_version": "vnext_replacement_stage13_broader_origin_candidate_contract_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "row_id": row_id,
        "row_type": "candidate_contract",
        "origin_family": candidate.origin_family,
        "candidate_origin_family": f"origin_{candidate.origin_family}",
        "generation_status": "generated_executable_contract" if valid_geometry(candidate.entry, candidate.stop, candidate.target, candidate.side) else "generated_contract_blocked",
        "activation_ready": activation_ready,
        "activation_ready_blocker_class": blocker,
        "activation_ready_blocker_detail": blocker_detail,
        "origin_native_dynamic_replay_exists": origin_native_dynamic_replayed,
        "origin_native_dynamic_replay_engine": "src/research/dynamic_execution_policy.py::simulate_policy",
        "origin_native_dynamic_final_r": dynamic_final_r,
        "origin_native_dynamic_selected_policy": dynamic_replay.get("selected_policy"),
        "origin_native_dynamic_selected_policy_same_bar_ambiguity": selected_same_bar,
        "prototype_fixed_r_replay_exists": prototype_replayed,
        "decision_time_utc": dt_s(candidate.decision_time),
        "symbol": candidate.symbol,
        "timeframe": candidate.timeframe,
        "side": candidate.side,
        "entry_price": round(candidate.entry, 8),
        "stop_or_invalidation": round(candidate.stop, 8),
        "target_reference": round(candidate.target, 8),
        "rr": round(abs(candidate.target - candidate.entry) / abs(candidate.entry - candidate.stop), 8)
        if abs(candidate.entry - candidate.stop) > 0
        else None,
        "source_path": candidate.source_path,
        "source_sha256": candidate.source_sha256,
        "source_row_index": candidate.source_row_index,
        "asof_source_contract": {
            "source_path": candidate.source_path,
            "source_sha256": candidate.source_sha256,
            "decision_time_utc": dt_s(candidate.decision_time),
            "source_fields_past_or_current_bar_only": True,
            "live_broker_or_paid_api_used": False,
        },
        "source_fields": candidate.source_fields,
        "prototype_replay": replay,
        "prototype_final_r": final_r,
        "origin_native_dynamic_policy_replay": dynamic_replay,
        "exact_blocker_required_for_activation": {
            "blocker_class": blocker,
            "missing_surface": None if activation_ready else "runtime_candidate_generation_or_ordered_ltf_path",
            "next_repair_action": None if activation_ready else "wire activation-ready broader-origin candidates into runtime candidate generation/selector before production activation",
        },
    }


def family_blocker_row(family: str, blocker_class: str, blocker_detail: str, source_paths: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "vnext_replacement_stage13_broader_origin_candidate_contract_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "row_id": stable_id("broad_origin_blocker", {"family": family, "blocker": blocker_class}),
        "row_type": "family_blocker",
        "origin_family": family,
        "candidate_origin_family": f"origin_{family}",
        "generation_status": "exact_blocker_no_executable_rows",
        "activation_ready": False,
        "activation_ready_blocker_class": blocker_class,
        "activation_ready_blocker_detail": blocker_detail,
        "origin_native_dynamic_replay_exists": False,
        "origin_native_dynamic_final_r": None,
        "prototype_fixed_r_replay_exists": False,
        "decision_time_utc": None,
        "symbol": None,
        "timeframe": None,
        "side": None,
        "entry_price": None,
        "stop_or_invalidation": None,
        "target_reference": None,
        "rr": None,
        "source_path": source_paths[0] if source_paths else None,
        "source_sha256": sha256_file(repo_path(source_paths[0])) if source_paths else None,
        "source_row_index": None,
        "asof_source_contract": {
            "source_paths_checked": source_paths,
            "live_broker_or_paid_api_used": False,
        },
        "source_fields": {},
        "prototype_replay": {
            "prototype_replay_status": "not_replayed_exact_blocker",
            "final_r": None,
            "blocker_class": blocker_class,
        },
        "prototype_final_r": None,
        "origin_native_dynamic_policy_replay": {
            "available": False,
            "selected_policy": SELECTED_DYNAMIC_POLICY,
            "selected_policy_final_r": None,
            "blocker_class": blocker_class,
        },
        "exact_blocker_required_for_activation": {
            "blocker_class": blocker_class,
            "missing_surface": "candidate_origin_generation_or_origin_native_dynamic_replay",
            "next_repair_action": blocker_detail,
        },
    }


def metric_record(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "performance_rows": 0,
            "total_r": None,
            "expectancy_r": None,
            "win_rate": None,
            "wins": 0,
        }
    wins = sum(1 for value in values if value > 0)
    return {
        "performance_rows": len(values),
        "total_r": round(sum(values), 12),
        "expectancy_r": round(sum(values) / len(values), 12),
        "win_rate": round(wins / len(values), 12),
        "wins": wins,
    }


def summarize(rows: list[dict[str, Any]], paths_read: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, dict[str, Any]] = {}
    for family in TARGET_FAMILIES:
        family_rows = [row for row in rows if row["origin_family"] == family]
        final_rs = [float(row["prototype_final_r"]) for row in family_rows if fnum(row.get("prototype_final_r")) is not None]
        dynamic_rs = [
            float(row["origin_native_dynamic_final_r"])
            for row in family_rows
            if fnum(row.get("origin_native_dynamic_final_r")) is not None
        ]
        activation_rs = [
            float(row["origin_native_dynamic_final_r"])
            for row in family_rows
            if row.get("activation_ready")
            and fnum(row.get("origin_native_dynamic_final_r")) is not None
        ]
        by_family[family] = {
            "total_rows": len(family_rows),
            "candidate_contract_rows": sum(1 for row in family_rows if row.get("row_type") == "candidate_contract"),
            "family_blocker_rows": sum(1 for row in family_rows if row.get("row_type") == "family_blocker"),
            "prototype_replay_rows": sum(1 for row in family_rows if row.get("prototype_fixed_r_replay_exists")),
            "origin_native_dynamic_replay_rows": sum(1 for row in family_rows if row.get("origin_native_dynamic_replay_exists")),
            "activation_ready_rows": sum(1 for row in family_rows if row.get("activation_ready")),
            "generation_status_counts": dict(Counter(str(row.get("generation_status")) for row in family_rows)),
            "blocker_class_counts": dict(Counter(str(row.get("activation_ready_blocker_class")) for row in family_rows)),
            "prototype_metrics": metric_record(final_rs),
            "origin_native_dynamic_metrics": metric_record(dynamic_rs),
            "activation_ready_dynamic_metrics": metric_record(activation_rs),
        }
    return {
        "schema_version": "vnext_replacement_stage13_broader_origin_replay_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "ledger_path": rel(OUTPUT_LEDGER),
        "paths_read_path": rel(OUTPUT_PATHS_READ),
        "row_counts": {
            "ledger_rows": len(rows),
            "candidate_contract_rows": sum(1 for row in rows if row.get("row_type") == "candidate_contract"),
            "family_blocker_rows": sum(1 for row in rows if row.get("row_type") == "family_blocker"),
            "activation_ready_rows": sum(1 for row in rows if row.get("activation_ready")),
            "origin_native_dynamic_replay_rows": sum(1 for row in rows if row.get("origin_native_dynamic_replay_exists")),
            "families_covered": len(by_family),
            "paths_read": len(paths_read),
        },
        "family_summary": by_family,
        "source_boundary": {
            "live_broker_used": False,
            "paid_api_or_network_used": False,
            "runtime_config_touched": False,
            "full_dynamic_replay_wired": True,
            "dynamic_replay_engine": "src/research/dynamic_execution_policy.py::simulate_policy",
            "selected_dynamic_policy": SELECTED_DYNAMIC_POLICY,
            "same_bar_policy": SAME_BAR_POLICY,
            "activation_ready_policy": "rows require origin_native_dynamic_policy_replay_final_r, no selected-policy same-bar ambiguity, valid OHLC-generated geometry, and no exact blocker",
        },
        "paths_read": paths_read,
    }


def main() -> None:
    calendar_events = read_calendar_events()
    source_items = load_source_paths()
    paths_read = [
        {"path": rel(STAGE02_BUILDER), "sha256": sha256_file(STAGE02_BUILDER), "read_role": "existing_stage02_builder"},
        {"path": rel(STAGE04_BUILDER), "sha256": sha256_file(STAGE04_BUILDER), "read_role": "existing_stage04_builder"},
        {"path": rel(STAGE05_BUILDER), "sha256": sha256_file(STAGE05_BUILDER), "read_role": "existing_stage05_builder"},
        {"path": rel(STAGE05_SHARD_STATUS), "sha256": sha256_file(STAGE05_SHARD_STATUS), "read_role": "stage05_shard_manifest"},
        {"path": rel(STAGE05_ACTIVATED_MANIFEST), "sha256": sha256_file(STAGE05_ACTIVATED_MANIFEST), "read_role": "replacement_stage05_shard_manifest"},
        {"path": rel(MARKET_AWARENESS_LEDGER), "sha256": sha256_file(MARKET_AWARENESS_LEDGER), "read_role": "stage10_market_awareness_feature_ledger"},
        {"path": rel(ML_FEATURE_LEDGER), "sha256": sha256_file(ML_FEATURE_LEDGER), "read_role": "stage10_ml_feature_ledger"},
        {"path": rel(STAGE10_ROUTER_LEDGER), "sha256": sha256_file(STAGE10_ROUTER_LEDGER), "read_role": "stage10_router_replay_ledger"},
        {"path": rel(STAGE10_VERIFICATION), "sha256": sha256_file(STAGE10_VERIFICATION), "read_role": "stage10_verification"},
        {"path": rel(STAGE06_MARKET_AWARENESS_BUILDER), "sha256": sha256_file(STAGE06_MARKET_AWARENESS_BUILDER), "read_role": "stage10_market_awareness_builder"},
        {"path": rel(STAGE10_BUILDER), "sha256": sha256_file(STAGE10_BUILDER), "read_role": "stage10_runtime_builder"},
        {"path": rel(SOURCE_CAPABILITY_LEDGER), "sha256": sha256_file(SOURCE_CAPABILITY_LEDGER), "read_role": "source_capability_ledger"},
        {"path": rel(SOURCE_CAPABILITY_SUMMARY), "sha256": sha256_file(SOURCE_CAPABILITY_SUMMARY), "read_role": "source_capability_summary"},
        {"path": rel(ORIGIN_REGISTRY), "sha256": sha256_file(ORIGIN_REGISTRY), "read_role": "origin_registry"},
        {"path": rel(ORIGIN_SUMMARY), "sha256": sha256_file(ORIGIN_SUMMARY), "read_role": "origin_summary"},
        {"path": rel(ECONOMIC_CALENDAR), "sha256": sha256_file(ECONOMIC_CALENDAR), "read_role": "news_calendar_context"},
        {"path": rel(CNR_CANDIDATES), "sha256": sha256_file(CNR_CANDIDATES), "read_role": "continuation_no_retrace_candidate_shadow"},
        {"path": rel(CNR_RESOLUTIONS), "sha256": sha256_file(CNR_RESOLUTIONS), "read_role": "continuation_no_retrace_resolution_shadow"},
    ]
    paths_read.extend({"path": item["path"], "sha256": item.get("sha256"), "read_role": "ohlc_candidate_source"} for item in source_path_checks(source_items))

    series_by_symbol: dict[str, BarSeries] = {}
    candidate_rows: list[dict[str, Any]] = []
    generation_counts: Counter[str] = Counter()
    for item in source_items:
        series = read_csv_series(item["source_path"], item.get("source_sha256"))
        if series is None or series.timeframe != "M15":
            continue
        series_by_symbol.setdefault(series.symbol, series)
        for candidate in generate_from_series(series, calendar_events):
            replay = simulate_fixed_r(series, candidate)
            dynamic_replay = simulate_origin_native_dynamic_policy(series, candidate, replay)
            candidate_rows.append(candidate_to_row(candidate, series, replay, dynamic_replay))
            generation_counts[candidate.origin_family] += 1

    for candidate in build_cross_asset_candidates(series_by_symbol):
        series = series_by_symbol.get(candidate.symbol)
        replay = simulate_fixed_r(series, candidate) if series else {
            "prototype_replay_status": "blocked",
            "blocker_class": "lag_symbol_source_series_missing_after_generation",
            "final_r": None,
        }
        dynamic_replay = simulate_origin_native_dynamic_policy(series, candidate, replay)
        candidate_rows.append(candidate_to_row(candidate, series, replay, dynamic_replay))
        generation_counts[candidate.origin_family] += 1

    for candidate in load_cnr_candidates():
        replay = {
            "prototype_replay_status": "not_replayed_exact_entry_price_blocker",
            "entry_touched": None,
            "terminal_outcome": None,
            "final_r": None,
            "blocker_class": candidate.blocker_class,
        }
        dynamic_replay = simulate_origin_native_dynamic_policy(None, candidate, replay)
        candidate_rows.append(candidate_to_row(candidate, None, replay, dynamic_replay))
        generation_counts[candidate.origin_family] += 1

    source_path_list = [item["source_path"] for item in source_items]
    for family in TARGET_FAMILIES:
        if generation_counts[family]:
            continue
        if family == "continuation_no_retrace":
            candidate_rows.append(
                family_blocker_row(
                    family,
                    "strict_non_future_event_clock_not_derivable_from_current_ohlc_context",
                    "No CNR decision-clock rows with executable decision entry were found; forward capture or sanitized historical pending-intent clock is required.",
                    [rel(CNR_CANDIDATES)],
                )
            )
        else:
            candidate_rows.append(
                family_blocker_row(
                    family,
                    "no_executable_rows_generated_from_available_ohlc_context",
                    "The Stage13 prototype scanned all route Stage05 M15 source files and generated no rows for this origin rule; inspect thresholds or add source-specific parser before treating as available.",
                    source_path_list,
                )
            )

    summary = summarize(candidate_rows, paths_read)
    append_jsonl(OUTPUT_LEDGER, candidate_rows)
    write_json(OUTPUT_PATHS_READ, {"schema_version": "vnext_replacement_stage13_broader_origin_paths_read_v1", "paths_read": paths_read})
    write_json(OUTPUT_SUMMARY, summary)
    print(json.dumps({"ledger_rows": len(candidate_rows), "families": summary["family_summary"]}, sort_keys=True))


if __name__ == "__main__":
    main()
