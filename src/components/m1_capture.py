"""Continuous MT5 M1 bar capture for vNext forward intelligence.

This daemon is data-only. It does not place, modify, or cancel orders.
The main orchestrator still owns trading decisions; this process persists
closed M1 bars so vNext research/runtime audits are not limited to M15 trade
records plus tick parquet sidecars.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.mt5_daemon_runtime import (  # noqa: E402
    acquire_single_instance_lock,
    install_signal_handlers,
    release_single_instance_lock,
    write_daemon_heartbeat,
)
from src.components.data_ingestion import repair_malformed_ohlc_from_ticks  # noqa: E402
from src.mt5.mt5_real import RealMT5  # noqa: E402
from src.utils.broker_profile import (  # noqa: E402
    broker_account_namespace,
    namespaced_daemon_name,
    namespaced_directory_path,
    namespaced_file_path,
    resolve_mt5_terminal_path,
)
from src.utils.config import (  # noqa: E402
    apply_instrument_overrides,
    apply_profile_overrides,
    resolve_profile,
)

LOGGER = logging.getLogger(__name__)

DATA_ROOT = PROJECT_ROOT / "data" / "m1"
STATE_PATH = PROJECT_ROOT / "pipeline_state" / "m1_capture_state.json"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "agent_config.yaml"
LOCK_NAME = "m1_capture_all"
CSV_FIELDS = (
    "time_utc",
    "symbol",
    "broker_symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "captured_at_utc",
)

_STOP = False


def _request_stop() -> None:
    global _STOP
    _STOP = True


def _load_config(path: Path, profile: str | None) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    return apply_profile_overrides(cfg, profile)


def _symbol_map(config: dict[str, Any], symbols: list[str] | None) -> dict[str, str]:
    instruments = config.get("instruments", {})
    if not isinstance(instruments, dict):
        instruments = {}
    selected = symbols or sorted(str(sym) for sym in instruments)
    out: dict[str, str] = {}
    for symbol in selected:
        merged = apply_instrument_overrides(config, symbol)
        market = merged.get("market", {}) if isinstance(merged, dict) else {}
        broker = str(market.get("mt5_symbol") or symbol)
        out[symbol] = broker
    return out


def _load_state(path: Path = STATE_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"symbols": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"symbols": {}}


def _save_state(state: dict[str, Any], path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(str(tmp), str(path))


def _csv_path(symbol: str, bar_time_utc: str, root: Path = DATA_ROOT) -> Path:
    day = bar_time_utc[:10]
    return root / symbol / f"{day}.csv"


def _append_rows(rows: list[dict[str, Any]], root: Path = DATA_ROOT) -> None:
    by_path: dict[Path, list[dict[str, Any]]] = {}
    for row in rows:
        by_path.setdefault(_csv_path(str(row["symbol"]), str(row["time_utc"]), root), []).append(row)

    for path, path_rows in by_path.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        if path.exists() and path.stat().st_size > 0:
            with path.open("r", newline="", encoding="utf-8") as fh:
                for existing in csv.DictReader(fh):
                    key = (str(existing.get("symbol") or ""), str(existing.get("time_utc") or ""))
                    if key[0] and key[1]:
                        merged[key] = {field: existing.get(field) for field in CSV_FIELDS}
        for row in path_rows:
            key = (str(row.get("symbol") or ""), str(row.get("time_utc") or ""))
            if key[0] and key[1]:
                merged[key] = {field: row.get(field) for field in CSV_FIELDS}
        ordered_rows = sorted(
            merged.values(),
            key=lambda row: (str(row.get("symbol") or ""), str(row.get("time_utc") or "")),
        )
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        with tmp.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for row in ordered_rows:
                writer.writerow({field: row.get(field) for field in CSV_FIELDS})
        os.replace(str(tmp), str(path))


def _closed_m1_rows(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # RealMT5 returns the broker's current forming bar at the end. Persist only
    # closed bars so the forward dataset is stable and deduplicable.
    if len(candles) <= 1:
        return []
    return candles[:-1]


def _parse_utc_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_seconds(*, now_utc: str, then_utc: str | None) -> float | None:
    now_dt = _parse_utc_timestamp(now_utc)
    then_dt = _parse_utc_timestamp(then_utc)
    if now_dt is None or then_dt is None:
        return None
    return round(max(0.0, (now_dt - then_dt).total_seconds()), 3)


def _no_new_row_reason(
    *,
    previous_last_time_utc: str,
    newest_closed_time_utc: str | None,
    closed_row_count: int,
) -> str | None:
    if closed_row_count <= 0:
        return "no_closed_m1_bar_returned"
    if previous_last_time_utc and newest_closed_time_utc and newest_closed_time_utc <= previous_last_time_utc:
        return "latest_closed_m1_bar_not_new"
    return None


def _latest_symbol_progress_utc(state: dict[str, Any]) -> str | None:
    symbols = state.get("symbols") if isinstance(state, dict) else None
    if not isinstance(symbols, dict):
        return None
    latest: datetime | None = None
    latest_text: str | None = None
    for item in symbols.values():
        if not isinstance(item, dict):
            continue
        stamp = item.get("last_progress_utc") or item.get("last_time_utc")
        parsed = _parse_utc_timestamp(str(stamp) if stamp else None)
        if parsed is not None and (latest is None or parsed > latest):
            latest = parsed
            latest_text = str(stamp)
    return latest_text


def capture_once(
    *,
    mt5: RealMT5,
    symbols: dict[str, str],
    state: dict[str, Any],
    fetch_bars: int,
    data_root: Path = DATA_ROOT,
    state_path: Path = STATE_PATH,
    heartbeat_name: str = LOCK_NAME,
    config: dict[str, Any] | None = None,
) -> tuple[int, list[str]]:
    captured_at = datetime.now(timezone.utc).isoformat()
    symbol_state = state.setdefault("symbols", {})
    new_rows: list[dict[str, Any]] = []
    errors: list[str] = []

    for symbol, broker_symbol in symbols.items():
        try:
            if mt5._mt5 is not None:  # noqa: SLF001 - runtime bridge to MT5 package
                mt5._mt5.symbol_select(broker_symbol, True)  # noqa: SLF001
            candles = mt5.get_candles(broker_symbol, mt5._mt5.TIMEFRAME_M1, fetch_bars)  # noqa: SLF001
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{symbol}:{exc}")
            symbol_state[symbol] = {
                **(symbol_state.get(symbol) or {}),
                "broker_symbol": broker_symbol,
                "last_seen_at_utc": captured_at,
                "last_cycle_status": "mt5_read_error",
                "last_error": str(exc),
                "last_rows_written": 0,
                "last_fetch_bars_requested": fetch_bars,
            }
            continue

        previous_last_time = str((symbol_state.get(symbol) or {}).get("last_time_utc") or "")
        last_time = previous_last_time
        rows_written_for_symbol = 0
        closed_rows = _closed_m1_rows(candles)
        anchor_price = None
        try:
            tick = mt5.get_tick(broker_symbol) if hasattr(mt5, "get_tick") else None
            anchor_price = getattr(tick, "bid", None) if tick is not None else None
        except Exception:  # noqa: BLE001
            anchor_price = None
        closed_rows, repair_report = repair_malformed_ohlc_from_ticks(
            closed_rows,
            symbol,
            "M1",
            config,
            anchor_price=anchor_price,
        )
        newest_closed_time = str((closed_rows[-1] if closed_rows else {}).get("time") or "") or None
        repair_failed_count = 0
        for candle in closed_rows:
            time_utc = str(candle.get("time") or "")
            if not time_utc or time_utc <= last_time:
                continue
            repair_status = (
                (candle.get("ohlc_source_repair") or {}).get("status")
                if isinstance(candle, dict)
                else None
            )
            if str(repair_status or "").startswith("repair_failed"):
                repair_failed_count += 1
                continue
            new_rows.append(
                {
                    "time_utc": time_utc,
                    "symbol": symbol,
                    "broker_symbol": broker_symbol,
                    "open": candle.get("open"),
                    "high": candle.get("high"),
                    "low": candle.get("low"),
                    "close": candle.get("close"),
                    "volume": candle.get("volume"),
                    "captured_at_utc": captured_at,
                }
            )
            last_time = time_utc
            rows_written_for_symbol += 1

        symbol_state[symbol] = {
            **(symbol_state.get(symbol) or {}),
            "broker_symbol": broker_symbol,
            "last_seen_at_utc": captured_at,
            "last_cycle_status": "ok",
            "last_rows_written": rows_written_for_symbol,
            "last_fetch_bars_requested": fetch_bars,
            "last_closed_candle_time_utc": newest_closed_time,
            "last_closed_candle_age_seconds": _age_seconds(
                now_utc=captured_at,
                then_utc=newest_closed_time,
            ),
            "last_ohlc_repair": repair_report,
            "last_ohlc_anchor_tick_bid": anchor_price,
            "last_no_new_row_reason": (
                None
                if rows_written_for_symbol
                else "malformed_m1_source_repair_failed"
                if repair_failed_count
                else _no_new_row_reason(
                    previous_last_time_utc=previous_last_time,
                    newest_closed_time_utc=newest_closed_time,
                    closed_row_count=len(closed_rows),
                )
            ),
        }
        if last_time:
            symbol_state[symbol]["last_time_utc"] = last_time
        if rows_written_for_symbol:
            symbol_state[symbol]["last_progress_utc"] = captured_at

    if new_rows:
        if data_root == DATA_ROOT:
            _append_rows(new_rows)
        else:
            _append_rows(new_rows, root=data_root)
    state["updated_at_utc"] = captured_at
    state["symbol_count"] = len(symbols)
    state["last_rows_written"] = len(new_rows)
    state["last_error_count"] = len(errors)
    state["last_errors"] = errors[:20]
    if state_path == STATE_PATH:
        _save_state(state)
    else:
        _save_state(state, path=state_path)
    last_progress_text = _latest_symbol_progress_utc(state)
    write_daemon_heartbeat(
        heartbeat_name,
        last_progress_at=_parse_utc_timestamp(last_progress_text),
        extra={
            "symbol_count": len(symbols),
            "rows_written": len(new_rows),
            "error_count": len(errors),
            "liveness_utc": datetime.now(timezone.utc).isoformat(),
            "last_progress_source": (
                "current_cycle_new_rows"
                if new_rows
                else "persisted_symbol_last_progress_utc"
                if last_progress_text
                else "no_symbol_progress_recorded"
            ),
        },
    )
    return len(new_rows), errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture closed M1 bars from MT5.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--symbols", nargs="*", default=None)
    parser.add_argument("--poll", type=float, default=10.0)
    parser.add_argument("--fetch-bars", type=int, default=5)
    parser.add_argument("--terminal-path", default=None)
    parser.add_argument("--runtime-namespace", default=None)
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--state-path", type=Path, default=None)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    install_signal_handlers(_request_stop)
    profile = resolve_profile(args.profile) or "redacted_account"
    config = _load_config(args.config, profile)
    namespace = broker_account_namespace(config, args.runtime_namespace)
    lock_name = namespaced_daemon_name(LOCK_NAME, namespace)
    data_root = args.data_root or namespaced_directory_path(DATA_ROOT, namespace)
    state_path = args.state_path or namespaced_file_path(STATE_PATH, namespace)

    acquired, conflict = acquire_single_instance_lock(
        lock_name,
        argv_marker="src.components.m1_capture",
    )
    if not acquired:
        LOGGER.warning("m1_capture already running at PID=%s", conflict)
        return 0

    mt5 = RealMT5(terminal_path=resolve_mt5_terminal_path(config, args.terminal_path))
    try:
        symbols = _symbol_map(config, args.symbols)
        if not symbols:
            LOGGER.error("No symbols configured for M1 capture")
            return 2
        if not mt5.connect():
            LOGGER.error("MT5 initialize failed")
            return 2
        state = _load_state(state_path)
        LOGGER.info(
            "M1 capture starting: symbols=%d profile=%s namespace=%s poll=%.1fs",
            len(symbols),
            profile,
            namespace or "legacy",
            args.poll,
        )
        while True:
            rows, errors = capture_once(
                mt5=mt5,
                symbols=symbols,
                state=state,
                fetch_bars=args.fetch_bars,
                data_root=data_root,
                state_path=state_path,
                heartbeat_name=lock_name,
                config=config,
            )
            if rows or errors:
                LOGGER.info("M1 capture cycle: rows=%d errors=%d", rows, len(errors))
            if args.once or _STOP:
                return 0 if not errors else 1
            end = time.monotonic() + max(1.0, args.poll)
            while time.monotonic() < end and not _STOP:
                time.sleep(min(0.5, end - time.monotonic()))
            if _STOP:
                return 0
    finally:
        try:
            mt5.disconnect()
        finally:
            release_single_instance_lock(lock_name)


if __name__ == "__main__":
    raise SystemExit(main())
