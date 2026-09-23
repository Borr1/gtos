from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTE_ID = "vnext_lane08_execution_policy_microstructure_stress_2026_05_31"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

LANE02_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31"
)
LANE06_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31"
)
FRIDAY_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
)
LIVE_COMPANION_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_live_activation_active_repair_companion_2026_05_28"
)
ACTIVATION_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
)
SELECTED_TRADE_SHARD_DIR = ACTIVATION_DIR / "stage04_canonical_selected_trade_shards"
TICK_ROOT = ROOT / "data" / "ticks"

LANE02_REPLAY = LANE02_DIR / "LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl"
LANE02_SUMMARY = LANE02_DIR / "LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json"
LANE02_COST_SUMMARY = LANE02_DIR / "LANE02_COST_EXPOSURE_STRESS_SUMMARY.json"
LANE06_COST_LEDGER = LANE06_DIR / "LANE06_COST_CALIBRATION_LEDGER.jsonl"
LANE06_SUMMARY = LANE06_DIR / "LANE06_SUMMARY.json"
FRIDAY_POLICY_REPLAY = FRIDAY_DIR / "FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_LEDGER.jsonl"
FRIDAY_BROKER_READY = FRIDAY_DIR / "FRIDAY_EXECUTION_POLICY_BROKER_READY_LEDGER.jsonl"
FRIDAY_TRAILING = FRIDAY_DIR / "FRIDAY_REAL_TRAILING_SIMULATION_LEDGER.jsonl"
LIVE_SYMBOL_SPEC = LIVE_COMPANION_DIR / "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl"

POLICY_ROW_LEDGER = ROUTE_DIR / "LANE08_POLICY_ROW_LEDGER.jsonl"
POLICY_SUMMARY_LEDGER = ROUTE_DIR / "LANE08_POLICY_SUMMARY_LEDGER.jsonl"
SPLIT_STRESS_LEDGER = ROUTE_DIR / "LANE08_POLICY_SPLIT_STRESS_LEDGER.jsonl"
MICROSTRUCTURE_LEDGER = ROUTE_DIR / "LANE08_MICROSTRUCTURE_STRESS_LEDGER.jsonl"
BROKER_CONSTRAINT_LEDGER = ROUTE_DIR / "LANE08_BROKER_CONSTRAINT_LEDGER.jsonl"
STRICT_TICK_POLICY_LEDGER = ROUTE_DIR / "LANE08_STRICT_TICK_POLICY_LEDGER.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / "LANE08_SOURCE_COMPLETENESS_LEDGER.jsonl"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / "LANE08_IMPLEMENTATION_DECISION_LEDGER.jsonl"
EXPECTANCY_SUMMARY = ROUTE_DIR / "LANE08_EXPECTANCY_SUMMARY.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE08_COMPLETION_AUDIT.json"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE08_OUTPUT_MANIFEST.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE08_CONTEXT_ANCHOR.md"
VERIFIER = ROUTE_DIR / "verify_lane08_execution_policy_microstructure_stress.py"
VERIFICATION_RESULT = ROUTE_DIR / "LANE08_VERIFICATION_RESULT.json"
BUILD_LOCK = ROUTE_DIR / ".lane08_build.lock"

POLICY_FIELDS = {
    "fixed_1_5r": "comparison_fixed_1_5r_r",
    "be_after_trigger": "comparison_be_after_trigger_r",
    "partial_be_runner": "comparison_partial_be_runner_r",
    "momentum_exhaustion": "comparison_momentum_exhaustion_r",
    "time_stop": "comparison_time_stop_r",
    "trailing_runner": "comparison_trailing_runner_r",
}
POLICIES = tuple(POLICY_FIELDS.keys())
MODIFY_DEPENDENT_POLICIES = {
    "be_after_trigger",
    "partial_be_runner",
    "momentum_exhaustion",
    "trailing_runner",
}
SPLIT_FIELDS = (
    "chosen_policy",
    "symbol",
    "session_bucket",
    "origin_family",
    "framework",
    "side",
    "microstructure_realism_class",
)
COST_SCENARIOS_R = (0.0, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5)
MODIFY_REJECT_SCENARIOS = (0.0, 0.01, 0.05)
STRICT_TICK_REPLAY_HORIZON_HOURS = 50
STRICT_TICK_TIME_STOP_HOURS = 8


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield line_number, row


def iter_jsonl_maybe_gzip(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_jsonl_line(handle, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


class RouteBuildLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._fd: int | None = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        self._fd = os.open(str(self.path), flags)
        payload = json.dumps(
            {
                "pid": os.getpid(),
                "created_at_utc": utc_now(),
                "purpose": "single_authoritative_lane08_route_build",
            },
            sort_keys=True,
        )
        os.write(self._fd, payload.encode("utf-8"))
        os.close(self._fd)
        self._fd = None
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def fnum(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    parsed = parse_utc(value)
    return parsed.isoformat() if parsed else str(value)


def round_metric(value: Any, places: int = 9) -> float | None:
    number = fnum(value)
    if number is None:
        return None
    return round(number, places)


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
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for line in handle if line.strip())


def file_record(path: Path, kind: str) -> dict[str, Any]:
    return {
        "bytes": path.stat().st_size if path.exists() else None,
        "kind": kind,
        "line_count": count_jsonl(path) if path.suffix == ".jsonl" and path.exists() else None,
        "path": rel(path),
        "sha256": sha256(path),
    }


def new_metric() -> dict[str, Any]:
    return {
        "rows": 0,
        "total_r": 0.0,
        "wins": 0,
        "losses": 0,
        "breakevens": 0,
        "gross_profit_r": 0.0,
        "gross_loss_r": 0.0,
        "max_drawdown_r": 0.0,
        "max_loss_streak": 0,
        "_equity": 0.0,
        "_peak": 0.0,
        "_loss_streak": 0,
        "_worst_r": None,
        "_best_r": None,
    }


def add_metric(bucket: dict[str, Any], value: float | None) -> None:
    if value is None:
        return
    value = float(value)
    bucket["rows"] += 1
    bucket["total_r"] += value
    bucket["_equity"] += value
    bucket["_peak"] = max(bucket["_peak"], bucket["_equity"])
    bucket["max_drawdown_r"] = max(
        bucket["max_drawdown_r"],
        bucket["_peak"] - bucket["_equity"],
    )
    bucket["_worst_r"] = value if bucket["_worst_r"] is None else min(bucket["_worst_r"], value)
    bucket["_best_r"] = value if bucket["_best_r"] is None else max(bucket["_best_r"], value)
    if value > 0:
        bucket["wins"] += 1
        bucket["gross_profit_r"] += value
        bucket["_loss_streak"] = 0
    elif value < 0:
        bucket["losses"] += 1
        bucket["gross_loss_r"] += value
        bucket["_loss_streak"] += 1
        bucket["max_loss_streak"] = max(bucket["max_loss_streak"], bucket["_loss_streak"])
    else:
        bucket["breakevens"] += 1
        bucket["_loss_streak"] = 0


def close_metric(bucket: dict[str, Any]) -> dict[str, Any]:
    rows = int(bucket["rows"])
    wins = int(bucket["wins"])
    losses = int(bucket["losses"])
    gross_profit = float(bucket["gross_profit_r"])
    gross_loss = float(bucket["gross_loss_r"])
    return {
        "rows": rows,
        "total_r": round(float(bucket["total_r"]), 9),
        "expectancy_r": round(float(bucket["total_r"]) / rows, 9) if rows else None,
        "wins": wins,
        "losses": losses,
        "breakevens": int(bucket["breakevens"]),
        "win_rate": round(wins / rows, 9) if rows else None,
        "win_rate_excluding_be": round(wins / (wins + losses), 9) if wins + losses else None,
        "gross_profit_r": round(gross_profit, 9),
        "gross_loss_r": round(gross_loss, 9),
        "profit_factor": round(gross_profit / abs(gross_loss), 9) if gross_loss else None,
        "max_drawdown_r": round(float(bucket["max_drawdown_r"]), 9),
        "max_loss_streak": int(bucket["max_loss_streak"]),
        "best_r": round_metric(bucket["_best_r"]),
        "worst_r": round_metric(bucket["_worst_r"]),
    }


def stage04_selected_row_id(row: dict[str, Any]) -> str:
    return str(
        row.get("order_intent_id")
        or row.get("dedupe_key")
        or row.get("candidate_id")
        or hashlib.sha256(
            json.dumps(row, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
    )


def load_selected_trade_geometry(selected_ids: set[str]) -> dict[str, dict[str, Any]]:
    remaining = set(selected_ids)
    geometry: dict[str, dict[str, Any]] = {}
    if not SELECTED_TRADE_SHARD_DIR.exists() or not remaining:
        return geometry
    for shard in sorted(SELECTED_TRADE_SHARD_DIR.glob("*.jsonl*")):
        for _, row in iter_jsonl_maybe_gzip(shard):
            row_id = stage04_selected_row_id(row)
            if row_id not in remaining:
                continue
            geometry[row_id] = {
                "selected_row_id": row_id,
                "candidate_id": row.get("candidate_id"),
                "entry_price": row.get("entry_price"),
                "stop_or_invalidation": row.get("stop_or_invalidation"),
                "side": row.get("side"),
                "symbol": row.get("symbol"),
                "source_path": row.get("source_path"),
                "source_row_index": row.get("source_row_index"),
                "decision_time_utc": row.get("decision_time_utc"),
                "risk_per_trade_pct_current": row.get("risk_per_trade_pct_current"),
                "selected_policy": row.get("selected_policy"),
                "broker_geometry_status": row.get("broker_geometry_status"),
            }
            remaining.remove(row_id)
            if not remaining:
                return geometry
    return geometry


class TickDataCache:
    def __init__(self, root: Path = TICK_ROOT) -> None:
        self.root = root
        self._day_cache: dict[tuple[str, str], Any] = {}
        self._symbol_frames: dict[str, Any] = {}
        self.loaded_source_paths: set[str] = set()
        self.load_errors: Counter[str] = Counter()

    def _read_day(self, symbol: str, day: datetime.date):
        key = (symbol, day.isoformat())
        if key in self._day_cache:
            return self._day_cache[key]
        path = self.root / symbol / f"{day.isoformat()}.parquet"
        if not path.exists():
            self._day_cache[key] = None
            return None
        try:
            import pandas as pd
            import pyarrow.parquet as pq

            frame = pq.read_table(path, columns=["ts_utc", "bid", "ask"]).to_pandas()
            frame["ts_utc"] = pd.to_datetime(frame["ts_utc"], utc=True)
        except Exception as exc:  # noqa: BLE001 - source proof records the class.
            self.load_errors[f"{type(exc).__name__}:{symbol}:{day.isoformat()}"] += 1
            self._day_cache[key] = None
            return None
        self.loaded_source_paths.add(rel(path))
        self._day_cache[key] = frame
        return frame

    def prepare(self, required_dates_by_symbol: dict[str, set[Any]]) -> None:
        try:
            import pandas as pd
        except Exception as exc:  # noqa: BLE001
            self.load_errors[f"{type(exc).__name__}:pandas_import"] += 1
            return
        for symbol, dates in sorted(required_dates_by_symbol.items()):
            frames = []
            for day in sorted(dates):
                frame = self._read_day(symbol, day)
                if frame is not None and not frame.empty:
                    frames.append(frame)
            if not frames:
                self._symbol_frames[symbol] = None
                continue
            merged = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
            self._symbol_frames[symbol] = merged.sort_values("ts_utc").reset_index(drop=True)

    def window(self, symbol: str, start: datetime, hours: int):
        try:
            import pandas as pd
        except Exception as exc:  # noqa: BLE001
            self.load_errors[f"{type(exc).__name__}:pandas_import"] += 1
            return None, "pandas_unavailable_for_tick_window"

        end = start + timedelta(hours=hours)
        if symbol in self._symbol_frames:
            frame = self._symbol_frames[symbol]
            if frame is None or frame.empty:
                return None, "no_prepared_tick_parquet_rows_for_symbol"
            ts = frame["ts_utc"]
            left = int(ts.searchsorted(pd.Timestamp(start), side="left"))
            right = int(ts.searchsorted(pd.Timestamp(end), side="right"))
            window = frame.iloc[left:right]
            if window.empty:
                return window, "prepared_tick_parquet_loaded_but_no_ticks_after_entry_time"
            return window, "tick_window_loaded"
        frames = []
        day = start.date()
        while day <= end.date():
            frame = self._read_day(symbol, day)
            if frame is not None and not frame.empty:
                frames.append(frame)
            day = day + timedelta(days=1)
        if not frames:
            return None, "no_tick_parquet_window_rows_loaded"
        frame = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
        mask = (frame["ts_utc"] >= pd.Timestamp(start)) & (
            frame["ts_utc"] <= pd.Timestamp(end)
        )
        window = frame.loc[mask].sort_values("ts_utc")
        if window.empty:
            return window, "tick_parquet_loaded_but_no_ticks_after_entry_time"
        return window, "tick_window_loaded"


def tick_policy_result(
    policy: str,
    *,
    status: str,
    final_r: float | None,
    exit_reason: str | None,
    exit_time: Any,
    mfe: float | None,
    mae: float | None,
    trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "policy_name": policy,
        "simulation_status": status,
        "gross_r": round_metric(final_r, 6),
        "exit_reason": exit_reason,
        "exit_time_utc": iso_utc(exit_time),
        "mfe_r": round_metric(mfe, 6),
        "mae_r": round_metric(mae, 6),
        "transition_trace": trace or {},
    }


def _path_end_result(policy: str, path: list[tuple[Any, float]]) -> dict[str, Any]:
    if not path:
        return tick_policy_result(
            policy,
            status="not_replayable_empty_tick_path",
            final_r=None,
            exit_reason=None,
            exit_time=None,
            mfe=None,
            mae=None,
        )
    values = [point[1] for point in path]
    return tick_policy_result(
        policy,
        status="strict_tick_path_end_mark_to_market",
        final_r=values[-1],
        exit_reason="tick_path_end_mark_to_market",
        exit_time=path[-1][0],
        mfe=max(values),
        mae=min(values),
    )


def simulate_tick_fixed(path: list[tuple[Any, float]]) -> dict[str, Any]:
    mfe = -10**9
    mae = 10**9
    for tick_time, r_value in path:
        mfe = max(mfe, r_value)
        mae = min(mae, r_value)
        if r_value <= -1.0:
            return tick_policy_result(
                "fixed_1_5r",
                status="strict_tick_bid_ask_ordered",
                final_r=-1.0,
                exit_reason="stop_loss",
                exit_time=tick_time,
                mfe=mfe,
                mae=mae,
            )
        if r_value >= 1.5:
            return tick_policy_result(
                "fixed_1_5r",
                status="strict_tick_bid_ask_ordered",
                final_r=1.5,
                exit_reason="final_target",
                exit_time=tick_time,
                mfe=mfe,
                mae=mae,
            )
    return {**_path_end_result("fixed_1_5r", path)}


def simulate_tick_be(path: list[tuple[Any, float]]) -> dict[str, Any]:
    mfe = -10**9
    mae = 10**9
    be_active = False
    trigger_time = None
    for tick_time, r_value in path:
        mfe = max(mfe, r_value)
        mae = min(mae, r_value)
        if not be_active:
            if r_value <= -1.0:
                return tick_policy_result(
                    "be_after_trigger",
                    status="strict_tick_bid_ask_ordered",
                    final_r=-1.0,
                    exit_reason="stop_loss",
                    exit_time=tick_time,
                    mfe=mfe,
                    mae=mae,
                    trace={"be_trigger_r": 1.0, "final_target_r": 1.5},
                )
            if r_value >= 1.5:
                return tick_policy_result(
                    "be_after_trigger",
                    status="strict_tick_bid_ask_ordered",
                    final_r=1.5,
                    exit_reason="final_target_after_tp1_same_tick",
                    exit_time=tick_time,
                    mfe=mfe,
                    mae=mae,
                    trace={"be_trigger_r": 1.0, "final_target_r": 1.5},
                )
            if r_value >= 1.0:
                be_active = True
                trigger_time = tick_time
        else:
            if r_value <= 0.0:
                return tick_policy_result(
                    "be_after_trigger",
                    status="strict_tick_bid_ask_ordered",
                    final_r=0.0,
                    exit_reason="breakeven_stop",
                    exit_time=tick_time,
                    mfe=mfe,
                    mae=mae,
                    trace={"be_trigger_time_utc": iso_utc(trigger_time)},
                )
            if r_value >= 1.5:
                return tick_policy_result(
                    "be_after_trigger",
                    status="strict_tick_bid_ask_ordered",
                    final_r=1.5,
                    exit_reason="final_target",
                    exit_time=tick_time,
                    mfe=mfe,
                    mae=mae,
                    trace={"be_trigger_time_utc": iso_utc(trigger_time)},
                )
    result_row = _path_end_result("be_after_trigger", path)
    result_row["transition_trace"] = {"be_trigger_time_utc": iso_utc(trigger_time)}
    return result_row


def simulate_tick_partial(path: list[tuple[Any, float]]) -> dict[str, Any]:
    if max((point[1] for point in path), default=-10**9) < 1.0:
        fixed = simulate_tick_fixed(path)
        return {**fixed, "policy_name": "partial_be_runner"}
    be = simulate_tick_be(path)
    if be["gross_r"] is None:
        return {**be, "policy_name": "partial_be_runner"}
    final_r = 0.5 + 0.5 * float(be["gross_r"])
    return {
        **be,
        "policy_name": "partial_be_runner",
        "gross_r": round_metric(final_r, 6),
        "exit_reason": f"partial_50_at_1r_then_{be.get('exit_reason')}",
        "transition_trace": {
            **(be.get("transition_trace") or {}),
            "partial_exit_r": 1.0,
            "partial_fraction": 0.5,
        },
    }


def simulate_tick_trailing(path: list[tuple[Any, float]]) -> dict[str, Any]:
    mfe = -10**9
    mae = 10**9
    trail = -1.0
    active = False
    for tick_time, r_value in path:
        mfe = max(mfe, r_value)
        mae = min(mae, r_value)
        if r_value <= trail:
            return tick_policy_result(
                "trailing_runner",
                status="strict_tick_bid_ask_ordered",
                final_r=trail,
                exit_reason="trailing_stop",
                exit_time=tick_time,
                mfe=mfe,
                mae=mae,
                trace={"trail_r": round_metric(trail, 6), "trail_active": active},
            )
        if mfe >= 1.0:
            active = True
            trail = max(trail, mfe - 0.5, 0.0)
        if r_value >= 3.0:
            return tick_policy_result(
                "trailing_runner",
                status="strict_tick_bid_ask_ordered",
                final_r=3.0,
                exit_reason="runner_cap_target",
                exit_time=tick_time,
                mfe=mfe,
                mae=mae,
                trace={"trail_r": round_metric(trail, 6), "trail_active": active},
            )
    result_row = _path_end_result("trailing_runner", path)
    result_row["transition_trace"] = {
        "trail_r": round_metric(trail, 6),
        "trail_active": active,
    }
    return result_row


def simulate_tick_momentum(path: list[tuple[Any, float]]) -> dict[str, Any]:
    mfe = -10**9
    mae = 10**9
    active = False
    for tick_time, r_value in path:
        mfe = max(mfe, r_value)
        mae = min(mae, r_value)
        if r_value <= -1.0 and not active:
            return tick_policy_result(
                "momentum_exhaustion",
                status="strict_tick_bid_ask_ordered",
                final_r=-1.0,
                exit_reason="stop_loss",
                exit_time=tick_time,
                mfe=mfe,
                mae=mae,
            )
        if mfe >= 1.0:
            active = True
        if active and r_value <= max(0.0, mfe - 0.4):
            exit_r = max(0.0, mfe - 0.4)
            return tick_policy_result(
                "momentum_exhaustion",
                status="strict_tick_bid_ask_ordered",
                final_r=exit_r,
                exit_reason="momentum_exhaustion_pullback",
                exit_time=tick_time,
                mfe=mfe,
                mae=mae,
                trace={"pullback_from_mfe_r": 0.4},
            )
        if r_value >= 2.0:
            return tick_policy_result(
                "momentum_exhaustion",
                status="strict_tick_bid_ask_ordered",
                final_r=2.0,
                exit_reason="momentum_runner_cap",
                exit_time=tick_time,
                mfe=mfe,
                mae=mae,
            )
    return _path_end_result("momentum_exhaustion", path)


def simulate_tick_time_stop(
    path: list[tuple[Any, float]],
    start_time: datetime,
) -> dict[str, Any]:
    if not path:
        return _path_end_result("time_stop", path)
    target_time = start_time + timedelta(hours=STRICT_TICK_TIME_STOP_HOURS)
    values: list[float] = []
    for tick_time, r_value in path:
        values.append(r_value)
        parsed = parse_utc(tick_time)
        if parsed and parsed >= target_time:
            return tick_policy_result(
                "time_stop",
                status="strict_tick_bid_ask_ordered",
                final_r=r_value,
                exit_reason="time_stop_8h",
                exit_time=tick_time,
                mfe=max(values),
                mae=min(values),
                trace={"time_stop_hours": STRICT_TICK_TIME_STOP_HOURS},
            )
    result_row = _path_end_result("time_stop", path)
    result_row["transition_trace"] = {
        "time_stop_hours": STRICT_TICK_TIME_STOP_HOURS,
        "time_stop_not_reached": True,
    }
    return result_row


def simulate_strict_tick_policies(
    path: list[tuple[Any, float]],
    start_time: datetime,
) -> dict[str, dict[str, Any]]:
    return {
        "fixed_1_5r": simulate_tick_fixed(path),
        "be_after_trigger": simulate_tick_be(path),
        "partial_be_runner": simulate_tick_partial(path),
        "momentum_exhaustion": simulate_tick_momentum(path),
        "time_stop": simulate_tick_time_stop(path, start_time),
        "trailing_runner": simulate_tick_trailing(path),
    }


def _array_time(times: Any, index: int) -> Any:
    if hasattr(times, "iloc"):
        return times.iloc[index]
    return times[index]


def _array_result(
    policy: str,
    *,
    status: str,
    final_r: float | None,
    exit_reason: str | None,
    index: int | None,
    times: Any,
    values: Any,
    trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if index is None or index < 0:
        return tick_policy_result(
            policy,
            status=status,
            final_r=final_r,
            exit_reason=exit_reason,
            exit_time=None,
            mfe=None,
            mae=None,
            trace=trace,
        )
    prefix = values[: index + 1]
    return tick_policy_result(
        policy,
        status=status,
        final_r=final_r,
        exit_reason=exit_reason,
        exit_time=_array_time(times, index),
        mfe=float(prefix.max()) if len(prefix) else None,
        mae=float(prefix.min()) if len(prefix) else None,
        trace=trace,
    )


def _array_end_result(policy: str, times: Any, values: Any) -> dict[str, Any]:
    if len(values) == 0:
        return tick_policy_result(
            policy,
            status="not_replayable_empty_tick_path",
            final_r=None,
            exit_reason=None,
            exit_time=None,
            mfe=None,
            mae=None,
        )
    return _array_result(
        policy,
        status="strict_tick_path_end_mark_to_market",
        final_r=float(values[-1]),
        exit_reason="tick_path_end_mark_to_market",
        index=len(values) - 1,
        times=times,
        values=values,
    )


def simulate_tick_fixed_arrays(times: Any, values: Any) -> dict[str, Any]:
    import numpy as np

    hits = np.flatnonzero((values <= -1.0) | (values >= 1.5))
    if len(hits):
        index = int(hits[0])
        if float(values[index]) <= -1.0:
            return _array_result(
                "fixed_1_5r",
                status="strict_tick_bid_ask_ordered",
                final_r=-1.0,
                exit_reason="stop_loss",
                index=index,
                times=times,
                values=values,
            )
        return _array_result(
            "fixed_1_5r",
            status="strict_tick_bid_ask_ordered",
            final_r=1.5,
            exit_reason="final_target",
            index=index,
            times=times,
            values=values,
        )
    return _array_end_result("fixed_1_5r", times, values)


def simulate_tick_be_arrays(times: Any, values: Any) -> dict[str, Any]:
    import numpy as np

    pre_hits = np.flatnonzero((values <= -1.0) | (values >= 1.0))
    if not len(pre_hits):
        result_row = _array_end_result("be_after_trigger", times, values)
        result_row["transition_trace"] = {"be_trigger_time_utc": None}
        return result_row
    first = int(pre_hits[0])
    if float(values[first]) <= -1.0:
        return _array_result(
            "be_after_trigger",
            status="strict_tick_bid_ask_ordered",
            final_r=-1.0,
            exit_reason="stop_loss",
            index=first,
            times=times,
            values=values,
            trace={"be_trigger_r": 1.0, "final_target_r": 1.5},
        )
    if float(values[first]) >= 1.5:
        return _array_result(
            "be_after_trigger",
            status="strict_tick_bid_ask_ordered",
            final_r=1.5,
            exit_reason="final_target_after_tp1_same_tick",
            index=first,
            times=times,
            values=values,
            trace={"be_trigger_r": 1.0, "final_target_r": 1.5},
        )
    trigger_time = _array_time(times, first)
    tail = values[first + 1 :]
    post_hits = np.flatnonzero((tail <= 0.0) | (tail >= 1.5))
    if len(post_hits):
        index = first + 1 + int(post_hits[0])
        if float(values[index]) <= 0.0:
            return _array_result(
                "be_after_trigger",
                status="strict_tick_bid_ask_ordered",
                final_r=0.0,
                exit_reason="breakeven_stop",
                index=index,
                times=times,
                values=values,
                trace={"be_trigger_time_utc": iso_utc(trigger_time)},
            )
        return _array_result(
            "be_after_trigger",
            status="strict_tick_bid_ask_ordered",
            final_r=1.5,
            exit_reason="final_target",
            index=index,
            times=times,
            values=values,
            trace={"be_trigger_time_utc": iso_utc(trigger_time)},
        )
    result_row = _array_end_result("be_after_trigger", times, values)
    result_row["transition_trace"] = {"be_trigger_time_utc": iso_utc(trigger_time)}
    return result_row


def simulate_tick_partial_arrays(times: Any, values: Any) -> dict[str, Any]:
    if len(values) == 0 or float(values.max()) < 1.0:
        fixed = simulate_tick_fixed_arrays(times, values)
        return {**fixed, "policy_name": "partial_be_runner"}
    be = simulate_tick_be_arrays(times, values)
    if be["gross_r"] is None:
        return {**be, "policy_name": "partial_be_runner"}
    return {
        **be,
        "policy_name": "partial_be_runner",
        "gross_r": round_metric(0.5 + 0.5 * float(be["gross_r"]), 6),
        "exit_reason": f"partial_50_at_1r_then_{be.get('exit_reason')}",
        "transition_trace": {
            **(be.get("transition_trace") or {}),
            "partial_exit_r": 1.0,
            "partial_fraction": 0.5,
        },
    }


def simulate_tick_trailing_arrays(times: Any, values: Any) -> dict[str, Any]:
    import numpy as np

    if len(values) == 0:
        return _array_end_result("trailing_runner", times, values)
    cummax = np.maximum.accumulate(values)
    prev_cummax = np.empty_like(cummax)
    prev_cummax[0] = -np.inf
    prev_cummax[1:] = cummax[:-1]
    trail_prev = np.where(prev_cummax >= 1.0, np.maximum(prev_cummax - 0.5, 0.0), -1.0)
    stop_indexes = np.flatnonzero(values <= trail_prev)
    cap_indexes = np.flatnonzero(values >= 3.0)
    stop_index = int(stop_indexes[0]) if len(stop_indexes) else None
    cap_index = int(cap_indexes[0]) if len(cap_indexes) else None
    if stop_index is not None and (cap_index is None or stop_index <= cap_index):
        trail = float(trail_prev[stop_index])
        return _array_result(
            "trailing_runner",
            status="strict_tick_bid_ask_ordered",
            final_r=trail,
            exit_reason="trailing_stop",
            index=stop_index,
            times=times,
            values=values,
            trace={
                "trail_r": round_metric(trail, 6),
                "trail_active": bool(prev_cummax[stop_index] >= 1.0),
            },
        )
    if cap_index is not None:
        trail = max(float(cummax[cap_index]) - 0.5, 0.0)
        return _array_result(
            "trailing_runner",
            status="strict_tick_bid_ask_ordered",
            final_r=3.0,
            exit_reason="runner_cap_target",
            index=cap_index,
            times=times,
            values=values,
            trace={"trail_r": round_metric(trail, 6), "trail_active": True},
        )
    result_row = _array_end_result("trailing_runner", times, values)
    final_mfe = float(cummax[-1])
    result_row["transition_trace"] = {
        "trail_r": round_metric(max(final_mfe - 0.5, 0.0) if final_mfe >= 1.0 else -1.0, 6),
        "trail_active": bool(final_mfe >= 1.0),
    }
    return result_row


def simulate_tick_momentum_arrays(times: Any, values: Any) -> dict[str, Any]:
    import numpy as np

    if len(values) == 0:
        return _array_end_result("momentum_exhaustion", times, values)
    cummax = np.maximum.accumulate(values)
    prev_cummax = np.empty_like(cummax)
    prev_cummax[0] = -np.inf
    prev_cummax[1:] = cummax[:-1]
    stop_indexes = np.flatnonzero((values <= -1.0) & (prev_cummax < 1.0))
    pullback_threshold = np.maximum(0.0, cummax - 0.4)
    pullback_indexes = np.flatnonzero((cummax >= 1.0) & (values <= pullback_threshold))
    cap_indexes = np.flatnonzero(values >= 2.0)
    candidates: list[tuple[int, str]] = []
    if len(stop_indexes):
        candidates.append((int(stop_indexes[0]), "stop_loss"))
    if len(pullback_indexes):
        candidates.append((int(pullback_indexes[0]), "momentum_exhaustion_pullback"))
    if len(cap_indexes):
        candidates.append((int(cap_indexes[0]), "momentum_runner_cap"))
    if not candidates:
        return _array_end_result("momentum_exhaustion", times, values)
    index, reason = min(candidates, key=lambda item: item[0])
    if reason == "stop_loss":
        return _array_result(
            "momentum_exhaustion",
            status="strict_tick_bid_ask_ordered",
            final_r=-1.0,
            exit_reason=reason,
            index=index,
            times=times,
            values=values,
        )
    if reason == "momentum_runner_cap":
        return _array_result(
            "momentum_exhaustion",
            status="strict_tick_bid_ask_ordered",
            final_r=2.0,
            exit_reason=reason,
            index=index,
            times=times,
            values=values,
        )
    exit_r = float(pullback_threshold[index])
    return _array_result(
        "momentum_exhaustion",
        status="strict_tick_bid_ask_ordered",
        final_r=exit_r,
        exit_reason=reason,
        index=index,
        times=times,
        values=values,
        trace={"pullback_from_mfe_r": 0.4},
    )


def simulate_tick_time_stop_arrays(
    times: Any,
    values: Any,
    start_time: datetime,
) -> dict[str, Any]:
    if len(values) == 0:
        return _array_end_result("time_stop", times, values)
    target_time = start_time + timedelta(hours=STRICT_TICK_TIME_STOP_HOURS)
    index = int(times.searchsorted(target_time, side="left")) if hasattr(times, "searchsorted") else len(values)
    if index < len(values):
        return _array_result(
            "time_stop",
            status="strict_tick_bid_ask_ordered",
            final_r=float(values[index]),
            exit_reason="time_stop_8h",
            index=index,
            times=times,
            values=values,
            trace={"time_stop_hours": STRICT_TICK_TIME_STOP_HOURS},
        )
    result_row = _array_end_result("time_stop", times, values)
    result_row["transition_trace"] = {
        "time_stop_hours": STRICT_TICK_TIME_STOP_HOURS,
        "time_stop_not_reached": True,
    }
    return result_row


def simulate_strict_tick_policies_arrays(
    times: Any,
    values: Any,
    start_time: datetime,
) -> dict[str, dict[str, Any]]:
    return {
        "fixed_1_5r": simulate_tick_fixed_arrays(times, values),
        "be_after_trigger": simulate_tick_be_arrays(times, values),
        "partial_be_runner": simulate_tick_partial_arrays(times, values),
        "momentum_exhaustion": simulate_tick_momentum_arrays(times, values),
        "time_stop": simulate_tick_time_stop_arrays(times, values, start_time),
        "trailing_runner": simulate_tick_trailing_arrays(times, values),
    }


def strict_tick_path_from_window(
    *,
    frame,
    side: str,
    entry: float,
    stop: float,
) -> tuple[list[tuple[Any, float]], list[float]]:
    risk = abs(entry - stop)
    if risk <= 0:
        return [], []
    path: list[tuple[Any, float]] = []
    spreads: list[float] = []
    side_key = side.upper()
    for tick in frame.itertuples(index=False):
        bid = fnum(getattr(tick, "bid", None))
        ask = fnum(getattr(tick, "ask", None))
        tick_time = getattr(tick, "ts_utc", None)
        if bid is None or ask is None or ask < bid:
            continue
        close_price = bid if side_key == "LONG" else ask
        r_value = (
            (close_price - entry) / risk
            if side_key == "LONG"
            else (entry - close_price) / risk
        )
        path.append((tick_time, float(r_value)))
        spreads.append((ask - bid) / risk)
    return path, spreads


def strict_tick_arrays_from_window(
    *,
    frame,
    side: str,
    entry: float,
    stop: float,
):
    risk = abs(entry - stop)
    if risk <= 0:
        return None, None, None
    valid = frame["bid"].notna() & frame["ask"].notna() & (frame["ask"] >= frame["bid"])
    if not bool(valid.any()):
        return None, None, None
    valid_frame = frame.loc[valid, ["ts_utc", "bid", "ask"]]
    close_price = valid_frame["bid"] if side.upper() == "LONG" else valid_frame["ask"]
    values = (
        (close_price - entry) / risk
        if side.upper() == "LONG"
        else (entry - close_price) / risk
    )
    spreads = (valid_frame["ask"] - valid_frame["bid"]) / risk
    return valid_frame["ts_utc"].reset_index(drop=True), values.to_numpy(dtype=float), spreads.to_numpy(dtype=float)


def strict_tick_replay_for_row(
    row: dict[str, Any],
    geometry: dict[str, Any] | None,
    tick_cache: TickDataCache,
) -> dict[str, Any]:
    base = {
        "schema_version": "lane08_strict_tick_policy_v1",
        "selected_row_id": row.get("selected_row_id"),
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "entry_time_utc": row.get("entry_time_utc"),
        "source_time_utc": row.get("source_time_utc"),
        "portfolio_ready_decision": row.get("decision"),
        "portfolio_decision_reason": row.get("portfolio_decision_reason"),
        "tick_availability_status": row.get("tick_availability_status"),
        "entry_fill_source_status": "entry_touch_inherited_from_m15_replay_no_broker_fill_ticket",
        "broker_lifecycle_status": "historical_replay_no_ticket_bound_order_modify_or_close_retcode",
        "cost_status": "entry_spread_measured_commission_swap_slippage_stressed_not_historical_deal_bound",
    }
    if not geometry:
        return {
            **base,
            "strict_tick_replay_status": "not_replayable_missing_stage04_selected_geometry",
        }
    entry = fnum(geometry.get("entry_price"))
    stop = fnum(geometry.get("stop_or_invalidation"))
    side = str(row.get("side") or geometry.get("side") or "").upper()
    start = parse_utc(
        row.get("entry_time_utc")
        or row.get("source_time_utc")
        or geometry.get("decision_time_utc")
    )
    if entry is None or stop is None or abs(entry - stop) <= 0 or side not in {"LONG", "SHORT"}:
        return {
            **base,
            "entry_price": entry,
            "stop_or_invalidation": stop,
            "strict_tick_replay_status": "not_replayable_invalid_stage04_entry_stop_side",
        }
    if start is None:
        return {
            **base,
            "entry_price": entry,
            "stop_or_invalidation": stop,
            "strict_tick_replay_status": "not_replayable_missing_entry_time",
        }
    frame, window_status = tick_cache.window(
        str(row.get("symbol") or geometry.get("symbol") or ""),
        start,
        STRICT_TICK_REPLAY_HORIZON_HOURS,
    )
    if frame is None or frame.empty:
        return {
            **base,
            "entry_price": entry,
            "stop_or_invalidation": stop,
            "strict_tick_replay_status": window_status,
            "strict_tick_replay_horizon_hours": STRICT_TICK_REPLAY_HORIZON_HOURS,
        }
    times, values, spreads = strict_tick_arrays_from_window(
        frame=frame,
        side=side,
        entry=entry,
        stop=stop,
    )
    if values is None or times is None or spreads is None or len(values) == 0:
        return {
            **base,
            "entry_price": entry,
            "stop_or_invalidation": stop,
            "strict_tick_replay_status": "not_replayable_no_valid_bid_ask_ticks",
            "raw_tick_rows": int(len(frame)),
            "strict_tick_replay_horizon_hours": STRICT_TICK_REPLAY_HORIZON_HOURS,
        }
    policy_results = simulate_strict_tick_policies_arrays(times, values, start)
    record = {
        **base,
        "strict_tick_replay_status": "strict_tick_replayed_ordered_bid_ask_exit_path_from_m15_entry_touch",
        "entry_price": round_metric(entry, 8),
        "stop_or_invalidation": round_metric(stop, 8),
        "risk_price_distance": round_metric(abs(entry - stop), 8),
        "strict_tick_replay_horizon_hours": STRICT_TICK_REPLAY_HORIZON_HOURS,
        "strict_tick_time_stop_hours": STRICT_TICK_TIME_STOP_HOURS,
        "raw_tick_rows": int(len(frame)),
        "valid_bid_ask_tick_rows": int(len(values)),
        "first_tick_time_utc": iso_utc(_array_time(times, 0)),
        "last_tick_time_utc": iso_utc(_array_time(times, len(values) - 1)),
        "entry_spread_r": round_metric(float(spreads[0]) if len(spreads) else None, 9),
        "median_spread_r_in_window": round_metric(
            statistics.median(float(value) for value in spreads) if len(spreads) else None,
            9,
        ),
        "max_spread_r_in_window": round_metric(float(spreads.max()) if len(spreads) else None, 9),
        "tick_source_loaded_file_count": len(tick_cache.loaded_source_paths),
        "source_operation": "stage04_entry_stop_geometry_plus_ordered_local_tick_bid_ask_exit_path",
        "result_scope": "strict_tick_subset_policy_replay_not_full_denominator_broker_net_r",
    }
    for policy, result_row in policy_results.items():
        strict_r = result_row.get("gross_r")
        m15_r = fnum(row.get(POLICY_FIELDS[policy]))
        record[f"strict_tick_{policy}_r"] = strict_r
        record[f"strict_tick_{policy}_exit_reason"] = result_row.get("exit_reason")
        record[f"strict_tick_{policy}_exit_time_utc"] = result_row.get("exit_time_utc")
        record[f"strict_tick_{policy}_simulation_status"] = result_row.get(
            "simulation_status"
        )
        record[f"m15_proxy_{policy}_r"] = round_metric(m15_r)
        record[f"strict_tick_{policy}_delta_vs_m15_proxy_r"] = round_metric(
            strict_r - m15_r if strict_r is not None and m15_r is not None else None
        )
    return record


def build_strict_tick_replay(
    tick_candidate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    selected_ids = {
        str(row.get("selected_row_id"))
        for row in tick_candidate_rows
        if row.get("selected_row_id")
    }
    geometry = load_selected_trade_geometry(selected_ids)
    tick_cache = TickDataCache()
    required_dates_by_symbol: dict[str, set[Any]] = defaultdict(set)
    for row in tick_candidate_rows:
        start = parse_utc(row.get("entry_time_utc") or row.get("source_time_utc"))
        symbol = str(row.get("symbol") or "")
        if not start or not symbol:
            continue
        end = start + timedelta(hours=STRICT_TICK_REPLAY_HORIZON_HOURS)
        day = start.date()
        while day <= end.date():
            required_dates_by_symbol[symbol].add(day)
            day = day + timedelta(days=1)
    tick_cache.prepare(required_dates_by_symbol)
    replay_status_counts: Counter[str] = Counter()
    policy_buckets: dict[tuple[str, str], dict[str, Any]] = defaultdict(new_metric)
    delta_buckets: dict[str, dict[str, Any]] = defaultdict(new_metric)
    spread_bucket = new_metric()
    strict_rows = 0
    geometry_joined_rows = 0
    with STRICT_TICK_POLICY_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for row in tick_candidate_rows:
            row_id = str(row.get("selected_row_id") or "")
            record = strict_tick_replay_for_row(row, geometry.get(row_id), tick_cache)
            if row_id in geometry:
                geometry_joined_rows += 1
            replay_status_counts[str(record.get("strict_tick_replay_status"))] += 1
            if str(record.get("strict_tick_replay_status")).startswith("strict_tick_replayed"):
                strict_rows += 1
                add_metric(spread_bucket, record.get("entry_spread_r"))
                denominators = ["selected"]
                if row.get("decision") == "accept":
                    denominators.append("portfolio_ready")
                for denominator in denominators:
                    for policy in POLICIES:
                        add_metric(
                            policy_buckets[(denominator, policy)],
                            record.get(f"strict_tick_{policy}_r"),
                        )
                for policy in POLICIES:
                    add_metric(
                        delta_buckets[policy],
                        record.get(f"strict_tick_{policy}_delta_vs_m15_proxy_r"),
                    )
            write_jsonl_line(handle, record)
    policy_summary = []
    for (denominator, policy), bucket in sorted(policy_buckets.items()):
        policy_summary.append(
            {
                **close_metric(bucket),
                "denominator": denominator,
                "policy": policy,
                "schema_version": "lane08_strict_tick_policy_summary_v1",
            }
        )
    delta_summary = []
    for policy, bucket in sorted(delta_buckets.items()):
        delta_summary.append(
            {
                **close_metric(bucket),
                "policy": policy,
                "delta_definition": "strict_tick_bid_ask_r_minus_m15_proxy_r",
                "schema_version": "lane08_strict_tick_delta_summary_v1",
            }
        )
    return {
        "candidate_rows": len(tick_candidate_rows),
        "geometry_joined_rows": geometry_joined_rows,
        "strict_tick_replayed_rows": strict_rows,
        "replay_status_counts": dict(sorted(replay_status_counts.items())),
        "policy_summary_by_denominator": policy_summary,
        "delta_vs_m15_proxy_summary": delta_summary,
        "entry_spread_r_summary": close_metric(spread_bucket),
        "tick_source_loaded_file_count": len(tick_cache.loaded_source_paths),
        "tick_source_loaded_paths": sorted(tick_cache.loaded_source_paths),
        "tick_load_error_counts": dict(sorted(tick_cache.load_errors.items())),
        "entry_fill_source_status": "entry touch timing inherited from M15 replay; ordered tick bid/ask path starts at that timestamp; broker ticket fill truth remains Lane06/forward-capture only",
        "source_operation": "local_tick_parquet_read_only_plus_stage04_geometry_join",
        "result_scope": "strict_tick_subset_replay_for_rows_with_local_tick_date_files",
    }


def classify_microstructure(row: dict[str, Any]) -> str:
    tick_status = str(row.get("tick_availability_status") or "")
    m1_status = str(row.get("m1_availability_status") or "")
    ordered_status = str(row.get("ordered_path_status") or "")
    same_bar = bool(row.get("same_bar_ambiguity"))
    cost_status = str(row.get("cost_status") or "")
    if same_bar or ordered_status.startswith("same_bar_ambiguous"):
        return "same_bar_ambiguous_requires_tick_path_replay"
    if tick_status == "local_tick_parquet_available_for_entry_date":
        if "missing_historical_live_cost" in cost_status:
            return "strict_tick_path_available_cost_lifecycle_missing"
        return "strict_tick_path_available_cost_bound"
    if m1_status == "local_m1_bar_available_for_entry_minute":
        return "m1_ordered_path_proxy_cost_lifecycle_missing"
    return "path_proxy_gap_requires_source_repair"


def load_cost_model() -> dict[str, Any]:
    commission_cost_r: list[float] = []
    broker_delta_r: list[float] = []
    closed_rows = 0
    open_rows = 0
    symbols: Counter[str] = Counter()
    for _, row in iter_jsonl(LANE06_COST_LEDGER):
        symbols[str(row.get("symbol") or "unknown")] += 1
        if row.get("broker_final_net_r_status") == "CAPTURED":
            closed_rows += 1
        if row.get("broker_final_net_r_status") == "OPEN_RESIDUAL_FINAL_NET_R_PENDING_BROKER_CLOSE":
            open_rows += 1
        risk = fnum(row.get("initial_cash_risk"))
        if risk and risk > 0:
            cash_cost = abs(
                (fnum(row.get("commission_sum"), 0.0) or 0.0)
                + (fnum(row.get("swap_sum"), 0.0) or 0.0)
                + (fnum(row.get("fee_sum"), 0.0) or 0.0)
            )
            commission_cost_r.append(cash_cost / risk)
        local_r = fnum(row.get("local_close_r_sum"))
        broker_r = fnum(row.get("broker_realized_net_r"))
        if local_r is not None and broker_r is not None:
            broker_delta_r.append(broker_r - local_r)
    median_commission = (
        statistics.median(commission_cost_r) if commission_cost_r else None
    )
    return {
        "broker_cost_model_scope": "sparse_live_vnext_xauusd_nas100_rows_only",
        "closed_rows": closed_rows,
        "open_final_net_r_pending_rows": open_rows,
        "symbols": dict(sorted(symbols.items())),
        "median_commission_swap_fee_cost_r": round_metric(median_commission),
        "max_commission_swap_fee_cost_r": round_metric(max(commission_cost_r) if commission_cost_r else None),
        "median_broker_minus_local_r": round_metric(statistics.median(broker_delta_r) if broker_delta_r else None),
        "source": rel(LANE06_COST_LEDGER),
    }


def load_broker_specs() -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for _, row in iter_jsonl(LIVE_SYMBOL_SPEC):
        symbol = str(row.get("symbol") or "")
        if symbol:
            specs[symbol] = row
    return specs


def load_friday_policy_counts() -> dict[str, Any]:
    counts: dict[str, Any] = {
        "friday_policy_rows": count_jsonl(FRIDAY_POLICY_REPLAY),
        "friday_broker_ready_rows": count_jsonl(FRIDAY_BROKER_READY),
        "friday_real_trailing_rows": count_jsonl(FRIDAY_TRAILING),
        "broker_ready_policy_counts": Counter(),
        "real_trailing_policy_counts": Counter(),
        "broker_ready_price_source_counts": Counter(),
        "broker_ready_modify_rejections": Counter(),
    }
    for _, row in iter_jsonl(FRIDAY_BROKER_READY):
        counts["broker_ready_policy_counts"][str(row.get("comparison_policy") or "unknown")] += 1
        counts["broker_ready_price_source_counts"][str(row.get("price_source") or "unknown")] += 1
        value = row.get("stop_modify_rejections")
        if value is None:
            label = "not_applicable_or_not_recorded"
        else:
            label = str(value)
        counts["broker_ready_modify_rejections"][label] += 1
    for _, row in iter_jsonl(FRIDAY_TRAILING):
        counts["real_trailing_policy_counts"][str(row.get("comparison_policy") or "unknown")] += 1
    return {
        key: dict(value) if isinstance(value, Counter) else value
        for key, value in counts.items()
    }


def stress_total(
    *,
    metric: dict[str, Any],
    policy: str,
    per_trade_cost_r: float,
    modify_reject_rate: float,
    modify_penalty_r: float,
) -> float:
    total = float(metric["total_r"])
    total -= int(metric["rows"]) * per_trade_cost_r
    if policy in MODIFY_DEPENDENT_POLICIES:
        total -= modify_penalty_r * modify_reject_rate
    return round(total, 9)


def build_artifacts() -> dict[str, Any]:
    now = utc_now()
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    cost_model = load_cost_model()
    broker_specs = load_broker_specs()
    friday_counts = load_friday_policy_counts()
    lane02_summary = read_json(LANE02_SUMMARY, {})
    lane02_cost_summary = read_json(LANE02_COST_SUMMARY, {})
    lane06_summary = read_json(LANE06_SUMMARY, {})

    summary_buckets: dict[tuple[str, str], dict[str, Any]] = defaultdict(new_metric)
    split_buckets: dict[tuple[str, str, str, str], dict[str, Any]] = defaultdict(new_metric)
    micro_buckets: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(new_metric)
    micro_counts: Counter[str] = Counter()
    tick_counts: Counter[str] = Counter()
    m1_counts: Counter[str] = Counter()
    ordered_counts: Counter[str] = Counter()
    cost_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    accepted_symbol_counts: Counter[str] = Counter()
    policy_modify_penalty: dict[tuple[str, str], float] = defaultdict(float)
    micro_modify_penalty: dict[tuple[str, str, str], float] = defaultdict(float)
    strict_tick_candidate_rows: list[dict[str, Any]] = []
    row_count = 0
    accepted_count = 0

    with POLICY_ROW_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for _, row in iter_jsonl(LANE02_REPLAY):
            row_count += 1
            accepted = row.get("decision") == "accept"
            if accepted:
                accepted_count += 1
                accepted_symbol_counts[str(row.get("symbol") or "unknown")] += 1
            symbol_counts[str(row.get("symbol") or "unknown")] += 1
            decision_counts[str(row.get("decision") or "unknown")] += 1
            micro_class = classify_microstructure(row)
            micro_counts[micro_class] += 1
            tick_counts[str(row.get("tick_availability_status") or "missing")] += 1
            m1_counts[str(row.get("m1_availability_status") or "missing")] += 1
            ordered_counts[str(row.get("ordered_path_status") or "missing")] += 1
            cost_counts[str(row.get("cost_status") or "missing")] += 1
            if row.get("tick_availability_status") == "local_tick_parquet_available_for_entry_date":
                strict_tick_candidate_rows.append(dict(row))

            policy_values = {
                policy: fnum(row.get(field))
                for policy, field in POLICY_FIELDS.items()
            }
            denominators = ["selected"]
            if accepted:
                denominators.append("portfolio_ready")
            for denominator in denominators:
                for policy, value in policy_values.items():
                    add_metric(summary_buckets[(denominator, policy)], value)
                    add_metric(micro_buckets[(denominator, policy, micro_class)], value)
                    if value is not None and policy in MODIFY_DEPENDENT_POLICIES and value > -1.0:
                        policy_modify_penalty[(denominator, policy)] += value + 1.0
                        micro_modify_penalty[(denominator, policy, micro_class)] += value + 1.0
                    for field in SPLIT_FIELDS:
                        key = micro_class if field == "microstructure_realism_class" else str(row.get(field) or "unknown")
                        add_metric(split_buckets[(denominator, policy, field, key)], value)

            spec = broker_specs.get(str(row.get("symbol") or ""))
            write_jsonl_line(
                handle,
                {
                    "schema_version": "lane08_policy_row_v1",
                    "lane08_sequence": row_count,
                    "selected_row_id": row.get("selected_row_id"),
                    "candidate_id": row.get("candidate_id"),
                    "source_time_utc": row.get("source_time_utc"),
                    "entry_time_utc": row.get("entry_time_utc"),
                    "exit_time_utc": row.get("exit_time_utc"),
                    "symbol": row.get("symbol"),
                    "session_bucket": row.get("session_bucket"),
                    "origin_family": row.get("origin_family"),
                    "framework": row.get("framework"),
                    "side": row.get("side"),
                    "current_selected_policy": row.get("chosen_policy"),
                    "portfolio_ready_decision": row.get("decision"),
                    "portfolio_decision_reason": row.get("portfolio_decision_reason"),
                    "microstructure_realism_class": micro_class,
                    "strict_tick_path_available": micro_class.startswith("strict_tick_path_available"),
                    "m1_fallback_confidence": (
                        "m1_exact_entry_minute_proxy"
                        if row.get("m1_availability_status") == "local_m1_bar_available_for_entry_minute"
                        else "m1_gap_or_outside_coverage"
                    ),
                    "same_bar_ambiguity": row.get("same_bar_ambiguity"),
                    "ordered_path_status": row.get("ordered_path_status"),
                    "tick_availability_status": row.get("tick_availability_status"),
                    "m1_availability_status": row.get("m1_availability_status"),
                    "cost_status": row.get("cost_status"),
                    "broker_spec_status": "broker_symbol_spec_bound" if spec else "broker_symbol_spec_missing",
                    "broker_trade_stops_level": spec.get("trade_stops_level") if spec else None,
                    "broker_trade_freeze_level": spec.get("trade_freeze_level") if spec else None,
                    "broker_volume_min": spec.get("volume_min") if spec else None,
                    "broker_volume_step": spec.get("volume_step") if spec else None,
                    "fixed_1_5r_r": round_metric(policy_values["fixed_1_5r"]),
                    "be_after_trigger_r": round_metric(policy_values["be_after_trigger"]),
                    "partial_be_runner_r": round_metric(policy_values["partial_be_runner"]),
                    "momentum_exhaustion_r": round_metric(policy_values["momentum_exhaustion"]),
                    "time_stop_r": round_metric(policy_values["time_stop"]),
                    "trailing_runner_r": round_metric(policy_values["trailing_runner"]),
                    "fantasy_mfe_shortcut_rejected": True,
                    "result_scope": "selected_and_portfolio_ready_policy_comparison_row",
                    "source_operation": "lane02_dynamic_router_row_policy_fields_plus_lane06_cost_model_and_live_symbol_specs",
                },
            )

    strict_tick_summary = build_strict_tick_replay(strict_tick_candidate_rows)

    summary_rows: list[dict[str, Any]] = []
    for (denominator, policy), bucket in sorted(summary_buckets.items()):
        metric = close_metric(bucket)
        summary_rows.append(
            {
                **metric,
                "denominator": denominator,
                "policy": policy,
                "modify_dependent": policy in MODIFY_DEPENDENT_POLICIES,
                "modify_failure_penalty_envelope_r": round(
                    policy_modify_penalty.get((denominator, policy), 0.0),
                    9,
                ),
                "schema_version": "lane08_policy_summary_v1",
            }
        )
    write_jsonl(POLICY_SUMMARY_LEDGER, summary_rows)

    split_rows: list[dict[str, Any]] = []
    for (denominator, policy, field, key), bucket in sorted(split_buckets.items()):
        split_rows.append(
            {
                **close_metric(bucket),
                "denominator": denominator,
                "policy": policy,
                "split_scope": field,
                "split_key": key,
                "schema_version": "lane08_policy_split_stress_v1",
            }
        )
    write_jsonl(SPLIT_STRESS_LEDGER, split_rows)

    micro_rows: list[dict[str, Any]] = []
    for (denominator, policy, micro_class), bucket in sorted(micro_buckets.items()):
        metric = close_metric(bucket)
        for per_trade_cost_r in COST_SCENARIOS_R:
            for modify_reject_rate in MODIFY_REJECT_SCENARIOS:
                if modify_reject_rate and policy not in MODIFY_DEPENDENT_POLICIES:
                    continue
                micro_rows.append(
                    {
                        **metric,
                        "denominator": denominator,
                        "policy": policy,
                        "microstructure_realism_class": micro_class,
                        "per_trade_cost_r": per_trade_cost_r,
                        "modify_reject_rate": modify_reject_rate,
                        "modify_failure_penalty_envelope_r": round(
                            micro_modify_penalty.get((denominator, policy, micro_class), 0.0),
                            9,
                        ),
                        "stressed_total_r": stress_total(
                            metric=metric,
                            policy=policy,
                            per_trade_cost_r=per_trade_cost_r,
                            modify_reject_rate=modify_reject_rate,
                            modify_penalty_r=micro_modify_penalty.get(
                                (denominator, policy, micro_class),
                                0.0,
                            ),
                        ),
                        "stress_interpretation": (
                            "strict_cost_and_modify_sensitivity_not_exact_broker_net_r"
                        ),
                        "schema_version": "lane08_microstructure_stress_v1",
                    }
                )
    write_jsonl(MICROSTRUCTURE_LEDGER, micro_rows)

    broker_rows = []
    for symbol, spec in sorted(broker_specs.items()):
        broker_rows.append(
            {
                "accepted_rows": accepted_symbol_counts.get(symbol, 0),
                "broker_symbol": spec.get("broker_symbol"),
                "digits": spec.get("digits"),
                "exists": spec.get("exists"),
                "freeze_level": spec.get("trade_freeze_level"),
                "point": spec.get("point"),
                "schema_version": "lane08_broker_constraint_v1",
                "selected_rows": symbol_counts.get(symbol, 0),
                "spread_price_snapshot": spec.get("spread_price"),
                "status": spec.get("status"),
                "stops_level": spec.get("trade_stops_level"),
                "symbol": symbol,
                "tick_available_snapshot": spec.get("tick_available"),
                "trade_contract_size": spec.get("trade_contract_size"),
                "trade_mode": spec.get("trade_mode"),
                "volume_max": spec.get("volume_max"),
                "volume_min": spec.get("volume_min"),
                "volume_step": spec.get("volume_step"),
                "row_level_constraint_status": (
                    "symbol_spec_bound_per_row_stop_volume_modify_exactness_requires_row_geometry"
                ),
            }
        )
    write_jsonl(BROKER_CONSTRAINT_LEDGER, broker_rows)

    source_rows = [
        {
            "schema_version": "lane08_source_completeness_v1",
            "source": rel(LANE02_REPLAY),
            "requirement": "selected_and_portfolio_ready_denominator",
            "status": "CAPTURED",
            "rows": row_count,
            "accepted_rows": accepted_count,
        },
        {
            "schema_version": "lane08_source_completeness_v1",
            "source": rel(LANE06_COST_LEDGER),
            "requirement": "broker_cost_commission_swap_net_r_truth",
            "status": "SPARSE_LIVE_CALIBRATION_CAPTURED_OPEN_FINAL_NET_R_PENDING",
            "details": cost_model,
        },
        {
            "schema_version": "lane08_source_completeness_v1",
            "source": rel(LIVE_SYMBOL_SPEC),
            "requirement": "broker_constraints_stops_freeze_volume_contract",
            "status": "SYMBOL_LEVEL_CAPTURED_ROW_LEVEL_GEOMETRY_PARTIAL",
            "symbol_spec_rows": len(broker_specs),
        },
        {
            "schema_version": "lane08_source_completeness_v1",
            "source": rel(FRIDAY_BROKER_READY),
            "requirement": "friday_tick_broker_ready_policy_rows",
            "status": "CAPTURED_SMALL_BROKER_READY_SLICE",
            "details": friday_counts,
        },
        {
            "schema_version": "lane08_source_completeness_v1",
            "source": rel(LANE02_REPLAY),
            "requirement": "strict_tick_path_full_denominator",
            "status": "PARTIAL_WITH_STRICT_SUBSET_REPLAY_SOURCE_GAP_FOR_MOST_ROWS",
            "tick_availability_counts": dict(tick_counts),
            "microstructure_realism_counts": dict(micro_counts),
        },
        {
            "schema_version": "lane08_source_completeness_v1",
            "source": rel(STRICT_TICK_POLICY_LEDGER),
            "requirement": "strict_tick_subset_ordered_bid_ask_policy_replay",
            "status": "CAPTURED_FOR_LOCAL_TICK_DATE_ROWS",
            "details": {
                "candidate_rows": strict_tick_summary["candidate_rows"],
                "geometry_joined_rows": strict_tick_summary["geometry_joined_rows"],
                "strict_tick_replayed_rows": strict_tick_summary["strict_tick_replayed_rows"],
                "replay_status_counts": strict_tick_summary["replay_status_counts"],
                "entry_fill_source_status": strict_tick_summary["entry_fill_source_status"],
            },
        },
    ]
    write_jsonl(SOURCE_COMPLETENESS_LEDGER, source_rows)

    implementation_rows = [
        {
            "schema_version": "lane08_implementation_decision_v1",
            "decision": "patch_runtime_dynamic_sl_modify_failure_visibility",
            "implementation_status": "patched_local_code_and_focused_test",
            "evidence": [
                "src/components/execution.py::_move_sl_to_dynamic_r",
                "tests/test_execution.py::TestVNextDynamicSLModificationFailure",
            ],
            "reason": (
                "dynamic trailing/momentum starts now record failed initial SL modify, "
                "preserve original SL, and alert instead of emitting an unqualified started state"
            ),
            "runtime_effect_boundary": "local_code_patch_not_live_reloaded_by_lane08",
        },
        {
            "schema_version": "lane08_implementation_decision_v1",
            "decision": "preserve_current_momentum_primary_partial_exception_router",
            "implementation_status": "no_new_policy_promotion_from_lane08",
            "evidence": [
                rel(POLICY_SUMMARY_LEDGER),
                rel(STRICT_TICK_POLICY_LEDGER),
                rel(FRIDAY_BROKER_READY),
                rel(LANE06_SUMMARY),
            ],
            "reason": (
                "broad selected and portfolio-ready denominators remain favorable for current router; "
                "strict tick subset is now materialized and shows policy sensitivity but is a 1790-row "
                "local tick-date subset with inherited M15 entry touch and missing broker deal lifecycle, "
                "while Friday broker-ready rows are too small and negative for a new promotion"
            ),
        },
        {
            "schema_version": "lane08_implementation_decision_v1",
            "decision": "reject_static_fixed_and_be_only_as_live_default",
            "implementation_status": "comparator_only",
            "evidence": [rel(POLICY_SUMMARY_LEDGER)],
            "reason": "fixed_1_5r and BE are retained as comparators, not live defaults",
        },
        {
            "schema_version": "lane08_implementation_decision_v1",
            "decision": "strict_tick_full_denominator_not_claimed",
            "implementation_status": "source_capture_requirement",
            "evidence": [rel(SOURCE_COMPLETENESS_LEDGER), rel(MICROSTRUCTURE_LEDGER)],
            "reason": (
                "only a minority of selected rows have local tick date availability; those rows are replayed "
                "through ordered bid/ask ticks, while most historical rows and all historical rows' exact "
                "commission/swap/deal lifecycle remain source gaps; no MFE fantasy shortcut is accepted"
            ),
        },
        {
            "schema_version": "lane08_implementation_decision_v1",
            "decision": "invalidate_prior_lane09_master_package_until_lane08_strict_tick_refresh_consumed",
            "implementation_status": "downstream_package_refresh_required_before_commit",
            "evidence": [
                rel(STRICT_TICK_POLICY_LEDGER),
                rel(EXPECTANCY_SUMMARY),
                "research/operations/vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31",
                "research/operations/vnext_next_level_master_orchestration_2026_05_31",
            ],
            "reason": (
                "existing Lane09/Master artifacts on disk were generated before the authoritative "
                "strict-tick Lane08 terminal verifier and carry stale Lane08 strict-tick package evidence; "
                "they must be regenerated or explicitly amended before any scoped package commit"
            ),
        },
    ]
    write_jsonl(IMPLEMENTATION_DECISION_LEDGER, implementation_rows)

    best_by_denominator = {}
    for denominator in ("selected", "portfolio_ready"):
        rows = [row for row in summary_rows if row["denominator"] == denominator]
        best = max(rows, key=lambda item: item["total_r"]) if rows else None
        best_by_denominator[denominator] = best

    expectancy = {
        "schema_version": "lane08_expectancy_summary_v1",
        "generated_at_utc": now,
        "route_id": ROUTE_ID,
        "input_rows": row_count,
        "portfolio_ready_rows": accepted_count,
        "lane02_summary": lane02_summary,
        "lane02_cost_summary": lane02_cost_summary,
        "lane06_summary": lane06_summary,
        "cost_model": cost_model,
        "friday_counts": friday_counts,
        "microstructure_realism_counts": dict(micro_counts),
        "tick_availability_counts": dict(tick_counts),
        "m1_availability_counts": dict(m1_counts),
        "ordered_path_counts": dict(ordered_counts),
        "cost_status_counts": dict(cost_counts),
        "decision_counts": dict(decision_counts),
        "best_policy_by_denominator": best_by_denominator,
        "strict_tick_replay_summary": strict_tick_summary,
        "downstream_package_boundary": (
            "Lane09/Master artifacts generated before this Lane08 strict-tick rebuild are stale for "
            "Lane08 consumption and must not be committed as current without refresh"
        ),
        "evidence_boundary": (
            "gross/proxy R over historical selected rows with cost/modify stress; "
            "strict ordered bid/ask tick replay for local tick-date subset; exact broker net R only "
            "for sparse Lane06 live rows"
        ),
    }
    write_json(EXPECTANCY_SUMMARY, expectancy)

    CONTEXT_ANCHOR.write_text(
        "\n".join(
            [
                "# Lane08 Context Anchor",
                "",
                f"Generated: {now}",
                f"Route: `{ROUTE_ID}`",
                "Controlling prompt: `research/science_program_2026_05/04_goal_prompts/VNEXT_LANE08_EXECUTION_POLICY_MICROSTRUCTURE_STRESS_GOAL_PROMPT_2026-05-31.md`",
                "Posture: research/repair/replay/local implementation; no live broker operation or live reload.",
                "Current implementation patch: dynamic SL modify failure visibility and alerting in `src/components/execution.py`.",
                f"Strict tick subset: {strict_tick_summary['strict_tick_replayed_rows']} / {strict_tick_summary['candidate_rows']} local tick-date rows replayed on ordered bid/ask ticks from inherited M15 entry touch.",
                "Current source gap: full selected historical strict tick and exact broker net-R are not available for every row; rows are classified by source completeness.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    VERIFIER.write_text(VERIFY_SCRIPT, encoding="utf-8")

    audit = {
        "schema_version": "lane08_completion_audit_v1",
        "generated_at_utc": now,
        "route_id": ROUTE_ID,
        "status": "complete_for_current_approved_local_source_class_with_explicit_strict_tick_cost_gaps",
        "mandatory_context_use": {
            "live_state_regenerated": True,
            "current_vnext_system_map_read": True,
            "current_repo_reading_order_read": True,
            "quick_reference_card_read": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "lane08_prompt_and_starter_read": True,
        },
        "requirements": [
            {
                "requirement": "selected_denominator_policy_stress",
                "status": "complete",
                "evidence": rel(POLICY_ROW_LEDGER),
                "rows": row_count,
            },
            {
                "requirement": "portfolio_ready_denominator_policy_stress",
                "status": "complete",
                "evidence": rel(POLICY_SUMMARY_LEDGER),
                "rows": accepted_count,
            },
            {
                "requirement": "partial_momentum_fixed_be_time_stop_trailing_variants",
                "status": "complete",
                "evidence": rel(POLICY_SUMMARY_LEDGER),
                "policies": list(POLICY_FIELDS),
            },
            {
                "requirement": "tick_m1_cost_modify_broker_constraint_stress",
                "status": "complete_with_source_class_labels",
                "evidence": [rel(MICROSTRUCTURE_LEDGER), rel(BROKER_CONSTRAINT_LEDGER)],
            },
            {
                "requirement": "strict_tick_subset_ordered_bid_ask_replay",
                "status": "complete_for_local_tick_date_rows",
                "evidence": rel(STRICT_TICK_POLICY_LEDGER),
                "rows": strict_tick_summary["strict_tick_replayed_rows"],
            },
            {
                "requirement": "no_fantasy_mfe_shortcuts",
                "status": "complete",
                "evidence": rel(POLICY_ROW_LEDGER),
            },
            {
                "requirement": "implementation_patch_for_evidence_supported_defect",
                "status": "complete",
                "evidence": rel(IMPLEMENTATION_DECISION_LEDGER),
            },
        ],
        "runtime_effect_boundary": "local_code_and_offline_artifacts_only_no_broker_action_no_live_reload_no_config_change",
        "source_use_state": "local_lane01_lane02_lane06_friday_live_companion_artifacts_only",
        "downstream_package_status": "prior_lane09_master_package_stale_until_refreshed_from_this_lane08_manifest",
        "open_source_gaps_not_hidden": [
            "historical full-denominator exact tick path is unavailable for most rows; local tick-date subset is replayed in LANE08_STRICT_TICK_POLICY_LEDGER.jsonl",
            "historical full-denominator commission/swap/deal lifecycle net-R is unavailable",
            "row-level stop/freeze/modify feasibility is symbol-spec bounded but not exact for every historical row",
            "two Lane06 broker positions still have final net-R pending broker close",
        ],
        "proof_or_impossibility_stop_condition": (
            "current local sources exhausted into ledgers; available local tick-date rows are replayed "
            "through ordered bid/ask ticks, and missing exact full-denominator tick/net broker fields are "
            "classified as source gaps rather than converted to MFE shortcuts"
        ),
    }
    write_json(COMPLETION_AUDIT, audit)
    write_json(OUTPUT_MANIFEST, build_manifest(now))

    completed = subprocess.run(
        [sys.executable, str(VERIFIER), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        return {"ok": False, "returncode": completed.returncode}
    write_json(OUTPUT_MANIFEST, build_manifest(now))
    return {
        "ok": True,
        "route_dir": rel(ROUTE_DIR),
        "input_rows": row_count,
        "portfolio_ready_rows": accepted_count,
        "best_policy_by_denominator": best_by_denominator,
    }


def build_manifest(now: str) -> dict[str, Any]:
    outputs = [
        file_record(POLICY_ROW_LEDGER, "policy_row_ledger"),
        file_record(POLICY_SUMMARY_LEDGER, "policy_summary_ledger"),
        file_record(SPLIT_STRESS_LEDGER, "policy_split_stress_ledger"),
        file_record(MICROSTRUCTURE_LEDGER, "microstructure_stress_ledger"),
        file_record(BROKER_CONSTRAINT_LEDGER, "broker_constraint_ledger"),
        file_record(STRICT_TICK_POLICY_LEDGER, "strict_tick_policy_ledger"),
        file_record(SOURCE_COMPLETENESS_LEDGER, "source_completeness_ledger"),
        file_record(IMPLEMENTATION_DECISION_LEDGER, "implementation_decision_ledger"),
        file_record(EXPECTANCY_SUMMARY, "expectancy_summary"),
        file_record(COMPLETION_AUDIT, "completion_audit"),
        file_record(VERIFICATION_RESULT, "verification_result"),
        file_record(OUTPUT_MANIFEST, "output_manifest"),
        file_record(CONTEXT_ANCHOR, "context_anchor"),
        file_record(VERIFIER, "route_owned_verifier"),
    ]
    return {
        "schema_version": "lane08_output_manifest_v1",
        "generated_at_utc": now,
        "route_id": ROUTE_ID,
        "output_count": len(outputs),
        "outputs": outputs,
    }


VERIFY_SCRIPT = r'''from __future__ import annotations

import argparse
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
POLICIES = {
    "fixed_1_5r",
    "be_after_trigger",
    "partial_be_runner",
    "momentum_exhaustion",
    "time_stop",
    "trailing_runner",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path)) if path.exists() else 0


def verify_route(route_dir: Path = ROUTE_DIR) -> dict:
    issues = []
    paths = {
        "row": route_dir / "LANE08_POLICY_ROW_LEDGER.jsonl",
        "summary": route_dir / "LANE08_POLICY_SUMMARY_LEDGER.jsonl",
        "split": route_dir / "LANE08_POLICY_SPLIT_STRESS_LEDGER.jsonl",
        "micro": route_dir / "LANE08_MICROSTRUCTURE_STRESS_LEDGER.jsonl",
        "broker": route_dir / "LANE08_BROKER_CONSTRAINT_LEDGER.jsonl",
        "strict": route_dir / "LANE08_STRICT_TICK_POLICY_LEDGER.jsonl",
        "source": route_dir / "LANE08_SOURCE_COMPLETENESS_LEDGER.jsonl",
        "decision": route_dir / "LANE08_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "expectancy": route_dir / "LANE08_EXPECTANCY_SUMMARY.json",
        "audit": route_dir / "LANE08_COMPLETION_AUDIT.json",
        "manifest": route_dir / "LANE08_OUTPUT_MANIFEST.json",
    }
    for name, path in paths.items():
        if not path.exists():
            issues.append(f"missing_output:{name}:{path.name}")
    if issues:
        return {
            "ok": False,
            "issue_count": len(issues),
            "issues": issues,
            "schema_version": "lane08_verification_result_v1",
        }

    row_count = count_jsonl(paths["row"])
    if row_count != 289600:
        issues.append(f"policy_row_count_expected_289600_actual_{row_count}")

    summary_rows = list(iter_jsonl(paths["summary"]))
    summary_keys = {(row.get("denominator"), row.get("policy")) for row in summary_rows}
    for denominator in ("selected", "portfolio_ready"):
        for policy in POLICIES:
            if (denominator, policy) not in summary_keys:
                issues.append(f"missing_policy_summary:{denominator}:{policy}")

    expectancy = read_json(paths["expectancy"])
    if expectancy.get("input_rows") != row_count:
        issues.append("expectancy_input_rows_mismatch")
    expected_portfolio_ready = (
        ((expectancy.get("lane02_summary") or {}).get("stats") or {}).get("accepted_rows")
        or expectancy.get("portfolio_ready_rows")
    )
    if expectancy.get("portfolio_ready_rows") != expected_portfolio_ready:
        issues.append(
            f"portfolio_ready_rows_expected_{expected_portfolio_ready}_actual_{expectancy.get('portfolio_ready_rows')}"
        )
    micro_counts = expectancy.get("microstructure_realism_counts") or {}
    if "strict_tick_path_available_cost_lifecycle_missing" not in micro_counts:
        issues.append("strict_tick_microstructure_class_missing")
    if "m1_ordered_path_proxy_cost_lifecycle_missing" not in micro_counts:
        issues.append("m1_proxy_microstructure_class_missing")
    tick_counts = expectancy.get("tick_availability_counts") or {}
    tick_available = int(tick_counts.get("local_tick_parquet_available_for_entry_date") or 0)
    strict_count = count_jsonl(paths["strict"])
    strict_summary = expectancy.get("strict_tick_replay_summary") or {}
    if tick_available <= 0:
        issues.append("no_local_tick_available_rows_recorded")
    if strict_count != tick_available:
        issues.append(f"strict_tick_row_count_expected_{tick_available}_actual_{strict_count}")
    if strict_summary.get("candidate_rows") != tick_available:
        issues.append("strict_tick_candidate_count_mismatch")
    if strict_summary.get("geometry_joined_rows") != tick_available:
        issues.append("strict_tick_geometry_join_incomplete")
    if not strict_summary.get("strict_tick_replayed_rows"):
        issues.append("strict_tick_replayed_rows_missing")
    strict_policy_keys = {
        (row.get("denominator"), row.get("policy"))
        for row in strict_summary.get("policy_summary_by_denominator") or []
    }
    if ("selected", "momentum_exhaustion") not in strict_policy_keys:
        issues.append("strict_tick_selected_momentum_summary_missing")

    decisions = list(iter_jsonl(paths["decision"]))
    if not any(row.get("decision") == "patch_runtime_dynamic_sl_modify_failure_visibility" for row in decisions):
        issues.append("missing_dynamic_sl_modify_patch_decision")
    if not any(row.get("decision") == "strict_tick_full_denominator_not_claimed" for row in decisions):
        issues.append("missing_strict_tick_gap_decision")

    audit = read_json(paths["audit"])
    if audit.get("runtime_effect_boundary") != "local_code_and_offline_artifacts_only_no_broker_action_no_live_reload_no_config_change":
        issues.append("runtime_effect_boundary_missing_or_wrong")
    if not audit.get("open_source_gaps_not_hidden"):
        issues.append("source_gaps_not_recorded")

    if count_jsonl(paths["micro"]) < 100:
        issues.append("microstructure_stress_rows_too_small")
    if count_jsonl(paths["broker"]) < 24:
        issues.append("broker_constraint_rows_expected_24_or_more")
    if count_jsonl(paths["split"]) < 100:
        issues.append("split_stress_rows_too_small")

    result = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "input_rows": row_count,
        "portfolio_ready_rows": expectancy.get("portfolio_ready_rows"),
        "route_id": "vnext_lane08_execution_policy_microstructure_stress_2026_05_31",
        "schema_version": "lane08_verification_result_v1",
    }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    result = verify_route()
    (ROUTE_DIR / "LANE08_VERIFICATION_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    try:
        with RouteBuildLock(BUILD_LOCK):
            result = build_artifacts()
    except FileExistsError:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "lane08_build_lock_exists",
                    "lock_path": rel(BUILD_LOCK),
                    "lock_payload": read_json(BUILD_LOCK, None),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
