from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
ROUTE_DIR = REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28"
CHECKPOINT_PATH = ROUTE_DIR / "LIVE_COMPANION_CURRENT_CHECKPOINT.json"
ACTIVE_STATE_PATH = ROUTE_DIR / "ACTIVE_REPAIR_STATE.json"
ACTIVE_LEDGER_PATH = ROUTE_DIR / "ACTIVE_REPAIR_LEDGER.jsonl"
POST_RELOAD_TS = "2026-05-28T17:17:05+00:00"
POST_786_COMMIT_TS = "2026-05-28T19:51:06+00:00"
REQUIRED_POST_786_COMMIT = "786ecb4f4224a6f7f6deae157868357d7c098f00"
STATIC_15R_ROUTE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
)
STATIC_15R_SUMMARY = STATIC_15R_ROUTE_DIR / "ei15r/summary.json"
STATIC_15R_VERIFIER = STATIC_15R_ROUTE_DIR / "verify_execution_intelligence_static_15r_ceiling_repair.py"
PENDING_LIMIT_LIFECYCLE_PATH = REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl"
LANE06_BROKER_LIFECYCLE_PATH = (
    REPO_ROOT
    / "research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31"
    / "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl"
)
GTOS_MAGIC_NUMBER = 20260401

EXPECTED_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

RUNTIME_HASH_FILES = [
    "config/agent_config.yaml",
    "config/profiles/redacted_account.yaml",
    "src/components/orchestrator.py",
    "src/components/gtos_vnext_runtime.py",
    "src/components/execution.py",
    "src/research/moonshot_default_off_policy_router.py",
]

ROUTE_ARTIFACT_HASH_FILES = [
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/ACTIVE_REPAIR_STATE.json",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/ACTIVE_REPAIR_LEDGER.jsonl",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_STARVATION_INTELLIGENCE_SUMMARY.json",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_STARVATION_INTELLIGENCE_LEDGER.jsonl",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_STARVATION_INTELLIGENCE_REFUSAL_BREAKDOWN.jsonl",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_STARVATION_INTELLIGENCE_VERIFICATION.json",
]


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _active_redacted_account_config() -> dict[str, Any]:
    try:
        import yaml
        from src.utils.config import apply_profile_overrides
    except Exception:
        return {}
    try:
        raw = yaml.safe_load((REPO_ROOT / "config/agent_config.yaml").read_text(encoding="utf-8")) or {}
        merged = apply_profile_overrides(raw, "redacted_account")
        return merged if isinstance(merged, dict) else {}
    except Exception:
        return {}


def _fallback_broker_alias(symbol: str) -> str:
    aliases = {
        "GER40": "GER30",
        "NAS100": "NDX100",
        "UKOIL_cash": "UKOUSD",
        "US30_cash": "US30",
        "USOIL_cash": "USOUSD",
    }
    return aliases.get(symbol, symbol)


def _active_broker_symbol_map() -> dict[str, str]:
    config = _active_redacted_account_config()
    instruments = config.get("instruments") if isinstance(config, dict) else {}
    out: dict[str, str] = {}
    if isinstance(instruments, dict):
        for symbol in EXPECTED_SYMBOLS:
            instrument_cfg = instruments.get(symbol) or {}
            market = instrument_cfg.get("market") if isinstance(instrument_cfg, dict) else {}
            broker_symbol = None
            if isinstance(market, dict):
                broker_symbol = market.get("mt5_symbol") or market.get("broker_symbol") or market.get("symbol")
            out[symbol] = str(broker_symbol or _fallback_broker_alias(symbol))
    for symbol in EXPECTED_SYMBOLS:
        out.setdefault(symbol, _fallback_broker_alias(symbol))
    return out


def _parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except ValueError:
        return None


def _age_s(value: Any, now_utc: datetime) -> float | None:
    ts = _parse_utc(value)
    if ts is None:
        return None
    return round(max(0.0, (now_utc - ts).total_seconds()), 1)


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _broker_epoch_to_utc_iso(value: Any, broker_offset_seconds: int) -> str | None:
    try:
        epoch = float(value)
    except (TypeError, ValueError):
        return None
    if epoch <= 0:
        return None
    return datetime.fromtimestamp(epoch - broker_offset_seconds, tz=timezone.utc).isoformat()


def _mt5_record_to_dict(record: Any, *, broker_offset_seconds: int) -> dict[str, Any]:
    raw = record._asdict() if hasattr(record, "_asdict") else {}
    result: dict[str, Any] = {}
    time_fields = {
        "time",
        "time_msc",
        "time_update",
        "time_update_msc",
        "time_setup",
        "time_setup_msc",
        "time_done",
        "time_done_msc",
        "time_expiration",
    }
    for key, value in raw.items():
        if value is None:
            continue
        result[key] = value
        if key in time_fields:
            seconds = float(value) / 1000.0 if str(key).endswith("_msc") else value
            iso_value = _broker_epoch_to_utc_iso(seconds, broker_offset_seconds)
            if iso_value:
                result[f"{key}_utc"] = iso_value
    return result


def _detect_mt5_broker_offset_seconds(mt5: Any, now_utc: datetime) -> int:
    for symbol in ["XAUUSD", *EXPECTED_SYMBOLS]:
        try:
            tick = mt5.symbol_info_tick(symbol)
        except Exception:  # noqa: BLE001 - read-only proof must degrade safely
            continue
        if tick is None or getattr(tick, "time", None) is None:
            continue
        try:
            raw = float(tick.time) - now_utc.timestamp()
            rounded = round(raw / 1800.0) * 1800
        except (TypeError, ValueError):
            continue
        return 0 if abs(rounded) < 60 else int(rounded)
    return 0


def _ps_json(command: str) -> list[dict[str, Any]]:
    output = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = output.strip()
    if not text:
        return []
    value = json.loads(text)
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    return []


def _sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _combined_hash(paths: list[str]) -> dict[str, Any]:
    rows = []
    digest = hashlib.sha256()
    for relative in paths:
        path = REPO_ROOT / relative
        file_hash = _sha256_file(path)
        rows.append({"path": relative, "sha256": file_hash, "exists": path.exists()})
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update((file_hash or "missing").encode("utf-8"))
        digest.update(b"\0")
    return {"sha256": digest.hexdigest(), "files": rows}


def _process_creation_utc_from_ps(value: Any) -> str | None:
    if not value:
        return None
    text = str(value)
    match = re.search(r"/Date\((\d+)\)/", text)
    if match:
        ts = datetime.fromtimestamp(int(match.group(1)) / 1000.0, tz=timezone.utc)
        return ts.isoformat()
    parsed = _parse_utc(text)
    return parsed.isoformat() if parsed else None


def _cli_arg(command_line: str, flag: str) -> str | None:
    pattern = rf"{re.escape(flag)}\s+([^\s]+)"
    match = re.search(pattern, command_line or "")
    if not match:
        return None
    return match.group(1).strip('"')


def _git_head() -> dict[str, Any]:
    try:
        full = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        short = subprocess.check_output(
            ["git", "rev-parse", "--short=9", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        subject = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        return {
            "head": full,
            "head_short": short,
            "head_subject": subject,
        }
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"head": None, "head_error": str(exc)}


def _latest_commit_for_paths(paths: list[str]) -> dict[str, Any]:
    try:
        output = subprocess.check_output(
            ["git", "log", "-1", "--format=%H%x00%cI%x00%s", "--", *paths],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"head": None, "error": str(exc)}
    if not output:
        return {"head": None}
    parts = output.split("\x00", 2)
    return {
        "head": parts[0] if len(parts) > 0 else None,
        "committed_at_utc": parts[1] if len(parts) > 1 else None,
        "subject": parts[2] if len(parts) > 2 else None,
        "paths": paths,
    }


def _process_rows() -> dict[str, Any]:
    rows = _ps_json(
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -match 'python' -and ("
        "$_.CommandLine -like '*run_agent.py*' -or "
        "$_.CommandLine -like '*m1_capture*' -or "
        "$_.CommandLine -like '*notification*worker*' -or "
        "$_.CommandLine -like '*heartbeat_monitor*' -or "
        "$_.CommandLine -like '*displacement*logger*') } | "
        "Select-Object ProcessId,Name,CreationDate,CommandLine | ConvertTo-Json -Depth 4"
    )
    orchestrators = []
    support_counts = Counter()
    for row in rows:
        cmd = row.get("CommandLine") or ""
        if "run_agent.py" in cmd and "--mode live" in cmd:
            match = re.search(r"--symbol\s+([^\s]+)", cmd)
            profile_match = re.search(r"--profile\s+([^\s]+)", cmd)
            orchestrators.append(
                {
                    "pid": row.get("ProcessId"),
                    "symbol": match.group(1).strip('"') if match else None,
                    "profile": profile_match.group(1).strip('"') if profile_match else None,
                    "creation_date_utc": _process_creation_utc_from_ps(row.get("CreationDate")),
                    "profile_proof": "--profile redacted_account" if "--profile redacted_account" in cmd else cmd,
                }
            )
        elif "m1_capture" in cmd:
            support_counts["m1_capture_python"] += 1
        elif "notification" in cmd and "worker" in cmd:
            support_counts["notification_worker_python"] += 1
        elif "heartbeat_monitor" in cmd:
            support_counts["heartbeat_monitor_python"] += 1
        elif "displacement" in cmd and "logger" in cmd:
            support_counts["displacement_python"] += 1
    symbols = sorted({row["symbol"] for row in orchestrators if row.get("symbol")})
    profile_counts = Counter(str(row.get("profile") or "missing") for row in orchestrators)
    required_commit_ts = _parse_utc(POST_786_COMMIT_TS)
    starts = [_parse_utc(row.get("creation_date_utc")) for row in orchestrators]
    starts = [start for start in starts if start is not None]
    process_start_after_required_commit = bool(
        required_commit_ts
        and len(starts) == len(EXPECTED_SYMBOLS)
        and all(start >= required_commit_ts for start in starts)
    )
    return {
        "orchestrator_python": len(orchestrators),
        "orchestrator_symbols": symbols,
        "orchestrators": sorted(orchestrators, key=lambda item: str(item.get("symbol") or "")),
        "missing_orchestrator_symbols": sorted(set(EXPECTED_SYMBOLS) - set(symbols)),
        "extra_orchestrator_symbols": sorted(set(symbols) - set(EXPECTED_SYMBOLS)),
        "profile_counts": dict(profile_counts),
        "profile_mismatches": [
            {"pid": row.get("pid"), "symbol": row.get("symbol"), "profile": row.get("profile")}
            for row in orchestrators
            if row.get("profile") != "redacted_account"
        ],
        "required_post_786_commit": REQUIRED_POST_786_COMMIT,
        "required_post_786_commit_time_utc": POST_786_COMMIT_TS,
        "all_orchestrators_started_after_required_post_786_commit": process_start_after_required_commit,
        "oldest_orchestrator_start_utc": min((start.isoformat() for start in starts), default=None),
        "newest_orchestrator_start_utc": max((start.isoformat() for start in starts), default=None),
        **dict(support_counts),
    }


def _heartbeat_summary(now_utc: datetime) -> dict[str, Any]:
    rows = []
    for path in sorted((REPO_ROOT / "pipeline_state").glob("heartbeat_*.json")):
        data = _read_json(path, {})
        if not isinstance(data, dict):
            continue
        symbol = data.get("symbol") or path.stem.replace("heartbeat_", "")
        ts = data.get("utc") or data.get("timestamp_utc")
        rows.append({"symbol": symbol, "age_s": _age_s(ts, now_utc), "utc": ts})
    ages = [row["age_s"] for row in rows if isinstance(row.get("age_s"), (int, float))]
    stale = [row for row in rows if isinstance(row.get("age_s"), (int, float)) and row["age_s"] > 120]
    return {
        "count": len(rows),
        "per_symbol": rows,
        "max_age_s": max(ages) if ages else None,
        "stale_over_120s": stale,
    }


def _tick_capture_process_map() -> dict[str, dict[str, Any]]:
    rows = _ps_json(
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -match 'python' -and $_.CommandLine -like '*-m src.components.tick_capture*' } | "
        "Select-Object ProcessId,Name,CreationDate,CommandLine | ConvertTo-Json -Depth 4"
    )
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        cmd = str(row.get("CommandLine") or "")
        symbol = _cli_arg(cmd, "--symbol")
        if not symbol:
            continue
        result[symbol] = {
            "pid": row.get("ProcessId"),
            "creation_date_utc": _process_creation_utc_from_ps(row.get("CreationDate")),
            "mt5_symbol": _cli_arg(cmd, "--mt5-symbol") or symbol,
            "command_contains_tick_capture_module": "-m src.components.tick_capture" in cmd,
        }
    return result


def _session_status(symbol: str, now_utc: datetime) -> dict[str, Any]:
    try:
        from src.safety.heartbeat_monitor import KILL_ZONES_UTC
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "session_proof_unavailable",
            "error": str(exc),
            "configured_windows_utc": [],
        }
    windows = [
        {
            "start": f"{start[0]:02d}:{start[1]:02d}",
            "end": f"{end[0]:02d}:{end[1]:02d}",
        }
        for row_symbol, start, end in KILL_ZONES_UTC
        if row_symbol == symbol
    ]
    minute = now_utc.hour * 60 + now_utc.minute
    active = False
    for row_symbol, start, end in KILL_ZONES_UTC:
        if row_symbol != symbol:
            continue
        start_minute = start[0] * 60 + start[1]
        end_minute = end[0] * 60 + end[1]
        if start_minute <= minute < end_minute:
            active = True
            break
    return {
        "status": "inside_repo_configured_session" if active else "outside_repo_configured_session",
        "configured_windows_utc": windows,
        "current_utc_hhmm": f"{now_utc.hour:02d}:{now_utc.minute:02d}",
    }


def _broker_tick_snapshots(
    stale_rows: list[dict[str, Any]],
    process_map: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not stale_rows:
        return {}
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        return {
            str(row.get("symbol") or "unknown"): {
                "broker_check": "import_failed",
                "error": str(exc),
            }
            for row in stale_rows
        }

    initialized = bool(mt5.initialize())
    result: dict[str, dict[str, Any]] = {}
    try:
        if not initialized:
            for row in stale_rows:
                result[str(row.get("symbol") or "unknown")] = {
                    "broker_check": "initialize_failed",
                    "last_error": mt5.last_error(),
                }
            return result
        active_broker_symbols = _active_broker_symbol_map()
        for row in stale_rows:
            symbol = str(row.get("symbol") or "unknown")
            proc = process_map.get(symbol) or {}
            mt5_symbol = str(
                proc.get("mt5_symbol")
                or row.get("broker_symbol")
                or active_broker_symbols.get(symbol)
                or _fallback_broker_alias(symbol)
            )
            selected = bool(mt5.symbol_select(mt5_symbol, True))
            info = mt5.symbol_info(mt5_symbol)
            tick = mt5.symbol_info_tick(mt5_symbol) if info is not None else None
            last_msc = row.get("last_msc")
            try:
                capture_msc = int(last_msc)
            except (TypeError, ValueError):
                capture_msc = None
            broker_msc = getattr(tick, "time_msc", None) if tick is not None else None
            try:
                broker_msc_int = int(broker_msc)
            except (TypeError, ValueError):
                broker_msc_int = None
            broker_not_advanced = (
                capture_msc is not None
                and broker_msc_int is not None
                and broker_msc_int <= capture_msc
            )
            result[symbol] = {
                "broker_check": "passed" if info is not None else "symbol_info_missing",
                "broker_symbol": mt5_symbol,
                "symbol_select": selected,
                "last_error": mt5.last_error(),
                "info_exists": info is not None,
                "visible": getattr(info, "visible", None) if info is not None else None,
                "trade_mode": getattr(info, "trade_mode", None) if info is not None else None,
                "broker_tick_time_msc": broker_msc_int,
                "broker_tick_bid": getattr(tick, "bid", None) if tick is not None else None,
                "broker_tick_ask": getattr(tick, "ask", None) if tick is not None else None,
                "broker_tick_flags": getattr(tick, "flags", None) if tick is not None else None,
                "broker_tick_not_advanced_since_capture": broker_not_advanced,
            }
    finally:
        try:
            mt5.shutdown()
        except Exception:  # noqa: BLE001
            pass
    return result


def _tick_stale_classification(
    row: dict[str, Any],
    broker: dict[str, Any],
    session: dict[str, Any],
) -> str | None:
    broker_visible = broker.get("info_exists") is True
    outside_repo_session = session.get("status") == "outside_repo_configured_session"
    daemon_alive = row.get("daemon_alive") is True
    daemon_dead = row.get("daemon_alive") is False
    broker_not_advanced = broker.get("broker_tick_not_advanced_since_capture") is True

    if daemon_alive and broker_visible and broker_not_advanced and outside_repo_session:
        return "daemon_alive_outside_repo_session_broker_tick_not_advanced"
    if daemon_alive and broker_visible and broker_not_advanced:
        return "daemon_alive_broker_tick_not_advanced"
    if daemon_dead and broker_visible and broker_not_advanced and outside_repo_session:
        return "daemon_not_running_outside_repo_session_broker_tick_not_advanced"
    if daemon_dead and broker_visible and broker_not_advanced:
        return "daemon_not_running_broker_tick_not_advanced"

    # Weekend/outside-session restarts can create fresh daemon heartbeat rows before the
    # first post-restart broker tick arrives. That is a classified quiet-market state
    # only when the daemon is alive and broker/session proof is present.
    missing_initial_capture = row.get("last_msc") in (None, "")
    zero_ticks_after_restart = int(row.get("total_ticks_written") or 0) == 0
    broker_quote_present = broker.get("broker_tick_time_msc") is not None and (
        broker.get("broker_tick_bid") is not None or broker.get("broker_tick_ask") is not None
    )
    if (
        daemon_alive
        and broker_visible
        and outside_repo_session
        and missing_initial_capture
        and zero_ticks_after_restart
        and broker_quote_present
    ):
        row["no_initial_capture_reason"] = (
            "daemon_alive_outside_repo_session_waiting_for_first_tick_after_restart"
        )
        return "daemon_alive_outside_repo_session_waiting_for_first_broker_tick"

    # Some broker crypto/CFD symbols are configured as 24h in the repo but the
    # broker quote itself can still be frozen across the weekend. When the
    # daemon restarted after the last broker quote and has not written any
    # ticks, classify it as broker/feed idle instead of a daemon failure.
    broker_tick_msc = broker.get("broker_tick_time_msc")
    daemon_start = _parse_utc(row.get("daemon_start_utc"))
    if (
        daemon_alive
        and broker_visible
        and missing_initial_capture
        and zero_ticks_after_restart
        and broker_quote_present
        and broker_tick_msc is not None
        and daemon_start is not None
    ):
        try:
            broker_tick_dt = datetime.fromtimestamp(float(broker_tick_msc) / 1000.0, timezone.utc)
        except (TypeError, ValueError, OSError):
            broker_tick_dt = None
        if broker_tick_dt is not None and broker_tick_dt <= daemon_start:
            row["no_initial_capture_reason"] = (
                "daemon_alive_broker_quote_pre_restart_waiting_for_next_broker_tick"
            )
            return "daemon_alive_broker_quote_pre_restart_no_new_tick_after_restart"

    return None


def _tick_summary(now_utc: datetime) -> dict[str, Any]:
    rows = []
    total_ticks = 0
    process_map = _tick_capture_process_map()
    active_broker_symbols = _active_broker_symbol_map()
    for path in sorted((REPO_ROOT / "pipeline_state").glob("daemon_heartbeat_tick_capture_*.json")):
        data = _read_json(path, {})
        if not isinstance(data, dict):
            continue
        symbol = path.stem.replace("daemon_heartbeat_tick_capture_", "")
        ts = data.get("utc") or data.get("last_saved_at_utc")
        row_ticks = int(
            data.get("total_ticks_written")
            or data.get("ticks_written")
            or data.get("total_ticks")
            or 0
        )
        total_ticks += row_ticks
        process = process_map.get(symbol) or {}
        rows.append(
            {
                "symbol": symbol,
                "age_s": _age_s(ts, now_utc),
                "utc": ts,
                "last_progress_utc": data.get("last_progress_utc"),
                "last_msc": data.get("last_msc"),
                "daemon_alive": bool(process.get("pid")),
                "daemon_pid": process.get("pid"),
                "daemon_start_utc": process.get("creation_date_utc"),
                "broker_symbol": (
                    process.get("mt5_symbol")
                    or active_broker_symbols.get(symbol)
                    or _fallback_broker_alias(symbol)
                ),
                "total_ticks_written": row_ticks,
            }
        )
    ages = [row["age_s"] for row in rows if isinstance(row.get("age_s"), (int, float))]
    stale = [row for row in rows if isinstance(row.get("age_s"), (int, float)) and row["age_s"] > 180]
    broker_ticks = _broker_tick_snapshots(stale, process_map)
    classified_stale = []
    unclassified_stale = []
    if stale:
        stale_by_symbol = {str(row.get("symbol")): row for row in stale}
        for row in stale:
            symbol = str(row.get("symbol") or "unknown")
            session = _session_status(symbol, now_utc)
            broker = broker_ticks.get(symbol) or {}
            row["broker_tick_snapshot"] = broker
            row["session_proof"] = session
            classification = _tick_stale_classification(row, broker, session)
            if classification:
                row["freshness_classification"] = classification
                classified_stale.append(row)
            else:
                row["freshness_classification"] = "unclassified_tick_capture_stale"
                unclassified_stale.append(row)
        # Copy the enriched stale rows back into the full per-symbol list.
        rows = [stale_by_symbol.get(str(row.get("symbol")), row) for row in rows]
    symbols = sorted({row["symbol"] for row in rows if row.get("symbol")})
    return {
        "count": len(rows),
        "lock_count": len(list((REPO_ROOT / "knowledge_base/meta").glob(".tick_capture_*.lock"))),
        "missing_symbols": sorted(set(EXPECTED_SYMBOLS) - set(symbols)),
        "extra_symbols": sorted(set(symbols) - set(EXPECTED_SYMBOLS)),
        "per_symbol": rows,
        "max_age_s": max(ages) if ages else None,
        "stale_over_180s": stale,
        "classified_stale_over_180s": classified_stale,
        "unclassified_stale_over_180s": unclassified_stale,
        "dead_daemon_symbols": sorted(
            row["symbol"] for row in rows
            if row.get("symbol") and row.get("daemon_alive") is False
        ),
        "tick_freshness_classification_status": (
            "all_stale_ticks_classified" if stale and not unclassified_stale
            else "no_stale_ticks" if not stale
            else "unclassified_stale_ticks_present"
        ),
        "total_ticks_reported": total_ticks,
    }


def _m1_summary(now_utc: datetime) -> dict[str, Any]:
    state = _read_json(REPO_ROOT / "pipeline_state/m1_capture_state.json", {})
    heartbeat = _read_json(REPO_ROOT / "pipeline_state/daemon_heartbeat_m1_capture_all.json", {})
    symbols = state.get("symbols") if isinstance(state, dict) else {}
    bar_lags = []
    seen_lags = []
    if isinstance(symbols, dict):
        per_symbol = []
        for symbol, item in symbols.items():
            if not isinstance(item, dict):
                continue
            bar_age = _age_s(item.get("last_time_utc"), now_utc)
            seen_age = _age_s(item.get("last_seen_at_utc"), now_utc)
            if isinstance(bar_age, (int, float)):
                bar_lags.append(bar_age)
            if isinstance(seen_age, (int, float)):
                seen_lags.append(seen_age)
            per_symbol.append(
                {
                    "symbol": symbol,
                    "broker_symbol": item.get("broker_symbol"),
                    "last_time_utc": item.get("last_time_utc"),
                    "last_seen_at_utc": item.get("last_seen_at_utc"),
                    "closed_bar_lag_s": bar_age,
                    "seen_age_s": seen_age,
                }
            )
    else:
        per_symbol = []
    last_rows = state.get("last_rows_written") if isinstance(state, dict) else None
    error_count = state.get("last_error_count") if isinstance(state, dict) else None
    return {
        "state_exists": bool(state),
        "heartbeat_exists": bool(heartbeat),
        "state_age_s": _age_s(state.get("updated_at_utc"), now_utc) if isinstance(state, dict) else None,
        "heartbeat_age_s": _age_s(heartbeat.get("utc"), now_utc) if isinstance(heartbeat, dict) else None,
        "symbol_count": state.get("symbol_count") if isinstance(state, dict) else 0,
        "missing_symbols": sorted(set(EXPECTED_SYMBOLS) - set(symbols if isinstance(symbols, dict) else {})),
        "extra_symbols": sorted(set(symbols if isinstance(symbols, dict) else {}) - set(EXPECTED_SYMBOLS)),
        "per_symbol": sorted(per_symbol, key=lambda row: str(row.get("symbol"))),
        "max_closed_bar_lag_s": max(bar_lags) if bar_lags else None,
        "max_seen_age_s": max(seen_lags) if seen_lags else None,
        "error_count": error_count,
        "zero_error_count_reason": (
            "no capture errors reported"
            if error_count == 0
            else "not_applicable_error_count_nonzero_or_missing"
        ),
        "last_rows_written": last_rows,
        "zero_rows_written_reason": (
            "no new closed M1 bar on last poll"
            if last_rows == 0
            else "not_applicable_rows_written_positive"
        ),
        "last_progress_utc_present": bool(heartbeat.get("last_progress_utc")) if isinstance(heartbeat, dict) else False,
        "last_progress_absent_reason": (
            "daemon heartbeat uses utc plus rows_written for progress; absent on zero-row poll"
            if isinstance(heartbeat, dict) and not heartbeat.get("last_progress_utc")
            else "not_applicable_last_progress_present"
        ),
    }


def _mt5_summary(now_utc: datetime) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        return {"initialized": False, "read_only_check": "import_failed", "error": str(exc)}

    initialized = bool(mt5.initialize())
    result: dict[str, Any] = {"initialized": initialized, "ts_utc": now_utc.isoformat()}
    try:
        if not initialized:
            result["read_only_check"] = "initialize_failed"
            return result
        broker_offset_seconds = _detect_mt5_broker_offset_seconds(mt5, now_utc)
        account = mt5.account_info()
        positions = mt5.positions_get()
        orders = mt5.orders_get()
        history_from_utc = now_utc - timedelta(hours=12)
        history_from = history_from_utc + timedelta(seconds=broker_offset_seconds)
        history_to = now_utc + timedelta(seconds=broker_offset_seconds)
        history_orders = mt5.history_orders_get(history_from, history_to)
        history_deals = mt5.history_deals_get(history_from, history_to)
        position_details = [
            _mt5_record_to_dict(position, broker_offset_seconds=broker_offset_seconds)
            for position in (positions or [])
        ]
        order_details = [
            _mt5_record_to_dict(order, broker_offset_seconds=broker_offset_seconds)
            for order in (orders or [])
        ]
        history_order_details = [
            _mt5_record_to_dict(order, broker_offset_seconds=broker_offset_seconds)
            for order in (history_orders or [])
        ]
        history_deal_details = [
            _mt5_record_to_dict(deal, broker_offset_seconds=broker_offset_seconds)
            for deal in (history_deals or [])
        ]
        result.update(
            {
                "read_only_check": "passed",
                "broker_offset_seconds": broker_offset_seconds,
                "history_query_from_utc": history_from_utc.isoformat(),
                "history_query_to_utc": now_utc.isoformat(),
                "history_query_from_broker_time": history_from.isoformat(),
                "history_query_to_broker_time": history_to.isoformat(),
                "login": getattr(account, "login", None) if account else None,
                "balance": getattr(account, "balance", None) if account else None,
                "equity": getattr(account, "equity", None) if account else None,
                "positions": len(positions or []),
                "orders": len(orders or []),
                "history_orders_12h": len(history_orders or []),
                "history_deals_12h": len(history_deals or []),
                "position_details": position_details,
                "order_details": order_details,
                "history_order_tail": history_order_details[-5:],
                "history_deal_tail": history_deal_details[-5:],
                "system_position_count": sum(
                    1 for row in position_details if row.get("magic") == GTOS_MAGIC_NUMBER
                ),
                "system_order_count": sum(
                    1 for row in order_details if row.get("magic") == GTOS_MAGIC_NUMBER
                ),
                "system_history_order_count_12h": sum(
                    1 for row in history_order_details if row.get("magic") == GTOS_MAGIC_NUMBER
                ),
                "system_history_deal_count_12h": sum(
                    1 for row in history_deal_details if row.get("magic") == GTOS_MAGIC_NUMBER
                ),
            }
        )
    finally:
        try:
            mt5.shutdown()
        except Exception:  # noqa: BLE001
            pass
    return result


def _ticket_keys_from_lifecycle_row(row: dict[str, Any]) -> set[int]:
    keys: set[int] = set()
    for field in (
        "ticket",
        "trade_state_ticket",
        "mt5_position_ticket",
        "mt5_entry_order_ticket",
    ):
        value = _int_or_none(row.get(field))
        if value is not None:
            keys.add(value)
    for field in ("entry_order_tickets", "entry_deal_tickets", "close_order_tickets"):
        values = row.get(field)
        if not isinstance(values, list):
            continue
        for value in values:
            parsed = _int_or_none(value)
            if parsed is not None:
                keys.add(parsed)
    open_snapshot = row.get("open_position_snapshot")
    if isinstance(open_snapshot, dict):
        for field in ("ticket", "identifier"):
            value = _int_or_none(open_snapshot.get(field))
            if value is not None:
                keys.add(value)
    for item in row.get("filled_order_position_join_keys") or []:
        text = str(item)
        if ":" not in text:
            continue
        value = _int_or_none(text.rsplit(":", 1)[-1])
        if value is not None:
            keys.add(value)
    return keys


def _summarize_lifecycle_row(row: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "timestamp_utc",
        "trade_id",
        "candidate_id",
        "symbol",
        "broker_symbol",
        "side",
        "broker_fill_state",
        "fill_no_fill_label",
        "fill_time_utc",
        "executed_entry_price",
        "mt5_position_ticket",
        "mt5_entry_order_ticket",
        "mt5_entry_deal_ticket",
        "gtos_vnext_dynamic_policy_selected",
        "gtos_vnext_execution_policy_id",
        "gtos_vnext_selector_row_id",
        "gtos_vnext_prop_safe_selector_after_risk_pct",
        "gtos_vnext_dynamic_final_target_price",
        "gtos_vnext_dynamic_final_target_r",
        "gtos_vnext_dynamic_be_trigger_price",
        "gtos_vnext_dynamic_be_trigger_r",
        "order_result_retcode",
        "order_send_success",
        "exact_r_join_key_status",
        "ticket",
        "selected_policy",
        "execution_policy_id",
        "broker_lifecycle_status",
        "open_position_present",
        "entry_order_tickets",
        "entry_deal_tickets",
        "partial_close_deal_tickets",
        "close_deal_tickets",
        "source_refs",
        "_checkpoint_lifecycle_source",
    ]
    return {field: row[field] for field in fields if field in row and row[field] is not None}


def _is_vnext_filled_lifecycle_row(row: dict[str, Any]) -> bool:
    if row.get("gtos_vnext_dynamic_policy_applied") is True:
        return row.get("broker_fill_state") == "filled"
    if row.get("schema_version") == "lane06_broker_lifecycle_v1":
        if not row.get("selected_policy") or not row.get("execution_policy_id"):
            return False
        status = str(row.get("broker_lifecycle_status") or "")
        return status not in ("", "NON_VNEXT_BROKER_HISTORY_ROW")
    return False


def _candidate_lifecycle_rows(position_ids: set[int]) -> list[dict[str, Any]]:
    lifecycle_rows: list[dict[str, Any]] = []
    for path, source in (
        (PENDING_LIMIT_LIFECYCLE_PATH, "pending_limit_lifecycle"),
        (LANE06_BROKER_LIFECYCLE_PATH, "lane06_broker_lifecycle"),
    ):
        if not path.exists():
            continue
        try:
            raw_rows = _read_jsonl(path)
        except (OSError, json.JSONDecodeError):
            continue
        for row in raw_rows:
            if not isinstance(row, dict):
                continue
            if not _is_vnext_filled_lifecycle_row(row):
                continue
            if not (position_ids & _ticket_keys_from_lifecycle_row(row)):
                continue
            row = dict(row)
            row["_checkpoint_lifecycle_source"] = source
            lifecycle_rows.append(row)
    return lifecycle_rows


def _broker_lifecycle_summary(mt5: dict[str, Any]) -> dict[str, Any]:
    positions = [
        row for row in mt5.get("position_details", [])
        if isinstance(row, dict) and row.get("magic") == GTOS_MAGIC_NUMBER
    ]
    orders = [
        row for row in mt5.get("order_details", [])
        if isinstance(row, dict) and row.get("magic") == GTOS_MAGIC_NUMBER
    ]
    history_orders = [
        row for row in mt5.get("history_order_tail", [])
        if isinstance(row, dict) and row.get("magic") == GTOS_MAGIC_NUMBER
    ]
    history_deals = [
        row for row in mt5.get("history_deal_tail", [])
        if isinstance(row, dict) and row.get("magic") == GTOS_MAGIC_NUMBER
    ]
    position_ids = {
        ticket for ticket in (_int_or_none(row.get("ticket")) for row in positions)
        if ticket is not None
    }
    lifecycle_rows = _candidate_lifecycle_rows(position_ids)

    lifecycle_position_ids: set[int] = set()
    for row in lifecycle_rows:
        lifecycle_position_ids.update(position_ids & _ticket_keys_from_lifecycle_row(row))

    entry_deals = [
        row for row in history_deals
        if _int_or_none(row.get("entry")) in (None, 0)
        and _int_or_none(row.get("position_id")) in position_ids
    ]
    close_deals = [
        row for row in history_deals
        if _int_or_none(row.get("entry")) == 1
        and _int_or_none(row.get("position_id")) in position_ids
    ]
    entry_deal_position_ids = {
        _int_or_none(deal.get("position_id")) for deal in entry_deals
    }
    entry_deal_position_ids.discard(None)
    # Open MT5 positions are broker truth too. The checkpoint history slice is a
    # short tail, so an older entry deal can age out while the vNext position is
    # still open and ticket-bound to a filled pending lifecycle row.
    reconciled_position_ids = {
        ticket
        for ticket in position_ids
        if ticket in lifecycle_position_ids
        and (ticket in entry_deal_position_ids or ticket in position_ids)
    }
    open_position_entry_deal_aged_out_ids = sorted(
        ticket
        for ticket in reconciled_position_ids
        if ticket not in entry_deal_position_ids
    )
    unreconciled_position_ids = sorted(position_ids - reconciled_position_ids)
    status = "no_real_vnext_broker_lifecycle_yet"
    if positions or orders or history_orders or history_deals:
        status = "real_vnext_lifecycle_unreconciled"
    if reconciled_position_ids and positions:
        status = "open_vnext_position_entry_reconciled_close_pending"
    if reconciled_position_ids and close_deals:
        status = "real_vnext_lifecycle_entry_and_close_reconciled"

    return {
        "schema_version": "vnext_broker_lifecycle_reconciliation_v1",
        "status": status,
        "real_vnext_lifecycle_seen": bool(positions or orders or history_orders or history_deals),
        "open_vnext_position_count": len(positions),
        "open_vnext_order_count": len(orders),
        "history_order_count_12h": mt5.get("system_history_order_count_12h", 0),
        "history_deal_count_12h": mt5.get("system_history_deal_count_12h", 0),
        "entry_deal_reconciled_count": len(entry_deals),
        "close_deal_reconciled_count": len(close_deals),
        "pending_lifecycle_fill_rows_matched": len(lifecycle_rows),
        "reconciled_open_position_ids": sorted(reconciled_position_ids),
        "unreconciled_open_position_ids": unreconciled_position_ids,
        "unreconciled_open_exposure_count": len(unreconciled_position_ids),
        "open_position_entry_deal_aged_out_ids": open_position_entry_deal_aged_out_ids,
        "open_position_entry_deal_aged_out_reason": (
            "open MT5 position ticket matches a vNext filled pending lifecycle row, "
            "but the entry deal is outside the checkpoint history tail"
            if open_position_entry_deal_aged_out_ids
            else None
        ),
        "open_positions": positions,
        "matched_pending_lifecycle_rows": [
            _summarize_lifecycle_row(row) for row in lifecycle_rows
        ],
        "entry_deals": entry_deals[-5:],
        "close_deals": close_deals[-5:],
        "history_orders": history_orders[-5:],
    }


def _process_version_proof(now_utc: datetime, process: dict[str, Any]) -> dict[str, Any]:
    git = _git_head()
    config_hash = _sha256_file(REPO_ROOT / "config/agent_config.yaml")
    runtime_hash = _combined_hash(RUNTIME_HASH_FILES)
    route_artifact_hash = _combined_hash(ROUTE_ARTIFACT_HASH_FILES)
    required_ts = _parse_utc(POST_786_COMMIT_TS)
    runtime_surface_commit = _latest_commit_for_paths(RUNTIME_HASH_FILES)
    runtime_surface_ts = _parse_utc(runtime_surface_commit.get("committed_at_utc"))
    required_runtime_reload_ts = max(
        [ts for ts in (required_ts, runtime_surface_ts) if ts is not None],
        default=None,
    )
    process_rows = process.get("orchestrators") if isinstance(process, dict) else []
    stale_processes = []
    if isinstance(process_rows, list) and required_runtime_reload_ts is not None:
        for row in process_rows:
            if not isinstance(row, dict):
                continue
            start = _parse_utc(row.get("creation_date_utc"))
            if start is None or start < required_runtime_reload_ts:
                stale_processes.append(
                    {
                        "symbol": row.get("symbol"),
                        "pid": row.get("pid"),
                        "creation_date_utc": row.get("creation_date_utc"),
                        "required_runtime_reload_after_utc": required_runtime_reload_ts.isoformat(),
                        "latest_runtime_surface_commit": runtime_surface_commit.get("head"),
                        "latest_runtime_surface_commit_time_utc": runtime_surface_commit.get("committed_at_utc"),
                        "stale_reason": "process_started_before_current_runtime_surface_commit",
                    }
                )
    head = str(git.get("head") or "")
    all_current_runtime_processes = (
        process.get("orchestrator_python") == len(EXPECTED_SYMBOLS)
        and not process.get("missing_orchestrator_symbols")
        and not process.get("extra_orchestrator_symbols")
        and process.get("all_orchestrators_started_after_required_post_786_commit")
        and not stale_processes
    )
    return {
        "schema_version": "vnext_live_process_version_proof_v1",
        "generated_at_utc": now_utc.isoformat(),
        "required_post_786_commit": REQUIRED_POST_786_COMMIT,
        "required_post_786_commit_time_utc": POST_786_COMMIT_TS,
        "latest_runtime_surface_commit": runtime_surface_commit,
        "required_runtime_reload_after_utc": (
            required_runtime_reload_ts.isoformat() if required_runtime_reload_ts else None
        ),
        "current_git_head": head or None,
        "current_git_head_short": git.get("head_short"),
        "current_git_subject": git.get("head_subject"),
        "current_head_is_post_786_or_later": bool(
            head and subprocess.call(
                ["git", "merge-base", "--is-ancestor", REQUIRED_POST_786_COMMIT, "HEAD"],
                cwd=REPO_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        ),
        "config_hash": config_hash,
        "runtime_label_hash": runtime_hash,
        "route_artifact_hash": route_artifact_hash,
        "orchestrator_process_count": process.get("orchestrator_python"),
        "all_expected_symbols_running": (
            process.get("orchestrator_python") == len(EXPECTED_SYMBOLS)
            and not process.get("missing_orchestrator_symbols")
            and not process.get("extra_orchestrator_symbols")
        ),
        "all_orchestrators_started_after_required_post_786_commit": process.get(
            "all_orchestrators_started_after_required_post_786_commit"
        ),
        "all_orchestrators_started_after_current_runtime_surface_commit": all_current_runtime_processes,
        "oldest_orchestrator_start_utc": process.get("oldest_orchestrator_start_utc"),
        "newest_orchestrator_start_utc": process.get("newest_orchestrator_start_utc"),
        "stale_or_unproven_orchestrators": stale_processes,
        "proof_status": (
            "all_24_live_orchestrators_running_current_runtime_surface"
            if all_current_runtime_processes
            else "reload_required_or_process_proof_incomplete"
        ),
    }


def _candidate_summary(now_utc: datetime, *, reload_ts_text: str | None = None) -> dict[str, Any]:
    from scripts.build_vnext_post_reload_candidate_proof import build as build_post_reload

    effective_reload_ts = reload_ts_text or POST_RELOAD_TS
    rows, summary = build_post_reload(
        reload_ts_text=effective_reload_ts,
        snapshot_upper_bound_text=now_utc.isoformat(),
    )
    final_counts = Counter(str(row.get("final_outcome") or "missing") for row in rows)
    policy_counts = Counter(
        str(row.get("dynamic_policy_selected") or "missing") for row in rows
        if row.get("dynamic_policy_selected")
    )
    execution_policy_counts = Counter(
        str(row.get("execution_policy_id") or "missing") for row in rows
        if row.get("execution_policy_id")
    )
    old_pa_count = 0
    old_l2_count = 0
    old_pa_present = 0
    old_l2_present = 0
    old_pa_missing = 0
    old_l2_missing = 0
    native_old_pa_count = 0
    native_old_l2_count = 0
    native_old_pa_present = 0
    native_old_l2_present = 0
    native_old_pa_missing = 0
    native_old_l2_missing = 0
    fixed_target_terms = {
        "J46": 0,
        "J49": 0,
        "live_current_j46_j49": 0,
        "fixed 1.5": 0,
        "fixed-1.5": 0,
        "fixed_15r": 0,
    }
    for row in rows:
        packet = row.get("packet") or {}
        packet_mode = row.get("packet_capture_mode")
        runtime = packet.get("runtime_decision") if isinstance(packet, dict) else {}
        event = runtime.get("event") if isinstance(runtime, dict) and isinstance(runtime.get("event"), dict) else {}
        old_system_absence = (
            packet.get("old_system_absence_proof")
            if isinstance(packet, dict) and isinstance(packet.get("old_system_absence_proof"), dict)
            else {}
        )

        def old_system_field(
            key: str,
            *,
            include_runtime_event: bool,
        ) -> tuple[bool, Any]:
            sources: tuple[dict[str, Any], ...]
            if include_runtime_event:
                sources = (packet, old_system_absence, event)
            else:
                sources = (packet, old_system_absence)
            for source in sources:
                if isinstance(source, dict) and key in source:
                    return True, source.get(key)
            return False, None

        if packet_mode == "native_live_writer" and isinstance(packet, dict):
            native_pa_present, native_pa_value = old_system_field(
                "old_primary_analyzer_called",
                include_runtime_event=False,
            )
            native_l2_present, native_l2_value = old_system_field(
                "old_l2_required",
                include_runtime_event=False,
            )
            if native_pa_present:
                native_old_pa_present += 1
                native_old_pa_count += int(bool(native_pa_value))
            else:
                native_old_pa_missing += 1
            if native_l2_present:
                native_old_l2_present += 1
                native_old_l2_count += int(bool(native_l2_value))
            else:
                native_old_l2_missing += 1
        old_pa_has_field, old_pa_value = old_system_field(
            "old_primary_analyzer_called",
            include_runtime_event=True,
        )
        old_l2_has_field, old_l2_value = old_system_field(
            "old_l2_required",
            include_runtime_event=True,
        )
        if old_pa_has_field:
            old_pa_present += 1
            old_pa_count += int(bool(old_pa_value))
        else:
            old_pa_missing += 1
        if old_l2_has_field:
            old_l2_present += 1
            old_l2_count += int(bool(old_l2_value))
        else:
            old_l2_missing += 1
        row_text = json.dumps(row, sort_keys=True)
        for term in fixed_target_terms:
            fixed_target_terms[term] += row_text.count(term)
    latest_mtime = None
    for row in rows:
        ts = _parse_utc(row.get("record_mtime_utc"))
        if ts and (latest_mtime is None or ts > latest_mtime):
            latest_mtime = ts
    packet_modes = summary.get("packet_capture_mode_counts", {})
    native_live_writer_packet_rows = int(packet_modes.get("native_live_writer") or 0)
    legacy_live_writer_packet_rows = int(packet_modes.get("live_writer") or 0)
    live_writer_packet_rows = native_live_writer_packet_rows + legacy_live_writer_packet_rows
    historical_backfill_rows = int(packet_modes.get("historical_saved_record_backfill") or 0)
    native_old_pa_l2_status = (
        "explicit_false_on_native_live_writer_rows"
        if native_live_writer_packet_rows
        and native_old_pa_present == native_live_writer_packet_rows
        and native_old_l2_present == native_live_writer_packet_rows
        and native_old_pa_count == 0
        and native_old_l2_count == 0
        else "pending_native_live_writer_explicit_false_fields"
    )
    return {
        "reload_timestamp_utc": summary.get("reload_timestamp_utc") or effective_reload_ts,
        "candidate_records_after_reload": len(rows),
        "final_outcome_counts": dict(final_counts),
        "packet_capture_mode_counts": packet_modes,
        "live_writer_packet_rows": live_writer_packet_rows,
        "native_live_writer_packet_rows": native_live_writer_packet_rows,
        "legacy_live_writer_packet_rows": legacy_live_writer_packet_rows,
        "historical_backfill_packet_rows": historical_backfill_rows,
        "live_writer_packet_proof_status": (
            "present"
            if live_writer_packet_rows
            else "pending_next_post_patch_candidate_written_by_live_process"
        ),
        "repair_entry_counts": summary.get("repair_entry_counts", {}),
        "rows_missing_required_packet_fields": summary.get("rows_missing_required_packet_fields", 0),
        "rows_with_null_zero_without_reason": summary.get("rows_with_null_zero_without_reason", 0),
        "order_path_rows": summary.get("order_path_rows", 0),
        "order_path_packet_proof_status": (
            "present"
            if summary.get("order_path_rows", 0)
            else "pending_first_vnext_order_path_record"
        ),
        "selected_policy_counts": dict(policy_counts),
        "execution_policy_id_counts": dict(execution_policy_counts),
        "old_primary_analyzer_called_count": old_pa_count,
        "old_l2_required_count": old_l2_count,
        "old_primary_analyzer_field_present_count": old_pa_present,
        "old_l2_required_field_present_count": old_l2_present,
        "old_primary_analyzer_field_missing_count": old_pa_missing,
        "old_l2_required_field_missing_count": old_l2_missing,
        "old_primary_analyzer_l2_absence_proof_status": (
            "explicit_false_on_all_rows"
            if len(rows) and old_pa_present == len(rows) and old_l2_present == len(rows)
            and old_pa_count == 0 and old_l2_count == 0
            else "not_fully_proven_from_candidate_packets"
        ),
        "native_old_primary_analyzer_called_count": native_old_pa_count,
        "native_old_l2_required_count": native_old_l2_count,
        "native_old_primary_analyzer_field_present_count": native_old_pa_present,
        "native_old_l2_required_field_present_count": native_old_l2_present,
        "native_old_primary_analyzer_field_missing_count": native_old_pa_missing,
        "native_old_l2_required_field_missing_count": native_old_l2_missing,
        "native_old_primary_analyzer_l2_absence_proof_status": native_old_pa_l2_status,
        "fixed_target_legacy_term_scan": fixed_target_terms,
        "fixed_target_legacy_term_hits": sum(fixed_target_terms.values()),
        "candidate_absence_proof_status": (
            "not_applicable_candidates_present"
            if rows
            else "no_post_reload_vnext_candidate_records_since_current_process_reload"
        ),
        "latest_record_mtime_utc": (
            latest_mtime.isoformat()
            if latest_mtime
            else "no_post_reload_candidate_records"
        ),
        "latest_record_age_s": (
            _age_s(latest_mtime.isoformat(), now_utc)
            if latest_mtime
            else "no_post_reload_candidate_records"
        ),
    }


def _calendar_summary(now_utc: datetime) -> dict[str, Any]:
    stale_files: list[dict[str, Any]] = []
    tool_status = "not_run"
    try:
        from scripts.refresh_economic_calendar import collect_stale_files

        stale_files = collect_stale_files(now=now_utc)
        tool_status = "fresh" if not stale_files else "stale_or_missing"
    except Exception as exc:  # noqa: BLE001
        tool_status = f"calendar_tool_exception:{exc}"
    candidates = [
        REPO_ROOT / "data/news_calendar.json",
        REPO_ROOT / "data/economic_calendar.csv",
        REPO_ROOT / "data/economic_calendar.json",
        REPO_ROOT / "data/calendar/news_calendar.json",
        REPO_ROOT / "data/calendar/economic_calendar.json",
    ]
    found = []
    for path in candidates:
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            found.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "mtime_utc": mtime.isoformat(),
                    "age_s": round((now_utc - mtime).total_seconds(), 1),
                }
            )
    return {
        "tool_status": tool_status,
        "stale_or_missing_files": stale_files,
        "local_calendar_files_found": found,
        "note": "tool_status is from scripts.refresh_economic_calendar.collect_stale_files; mtimes are supporting evidence only",
    }


def _static_15r_blocker_summary() -> dict[str, Any]:
    summary = _read_json(STATIC_15R_SUMMARY, {})
    if not isinstance(summary, dict) or not summary:
        return {
            "status": "blocked_missing_static_15r_summary",
            "summary_path": str(STATIC_15R_SUMMARY.relative_to(REPO_ROOT)),
            "verifier_path": str(STATIC_15R_VERIFIER.relative_to(REPO_ROOT)),
            "missing_summary": True,
            "missing_manifest_count": 0,
            "missing_shard_count": 0,
            "missing_manifests": [],
            "missing_shards": [],
            "row_level_verifier_command": (
                "py -3 "
                f"{STATIC_15R_VERIFIER.relative_to(REPO_ROOT)} --check"
            ),
        }
    outputs = summary.get("outputs") if isinstance(summary.get("outputs"), dict) else {}
    missing_manifests: list[str] = []
    missing_shards: list[str] = []
    checked_manifests: list[str] = []
    for output_name, output_meta in outputs.items():
        if not isinstance(output_meta, dict):
            continue
        manifest_rel = output_meta.get("manifest_path")
        if not manifest_rel:
            continue
        manifest_path = REPO_ROOT / str(manifest_rel)
        checked_manifests.append(str(manifest_path.relative_to(REPO_ROOT)))
        if not manifest_path.exists():
            missing_manifests.append(str(manifest_path.relative_to(REPO_ROOT)))
            continue
        try:
            entries = _read_jsonl(manifest_path)
        except (OSError, json.JSONDecodeError) as exc:
            missing_manifests.append(
                f"{manifest_path.relative_to(REPO_ROOT)}:unreadable:{exc}"
            )
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            shard_rel = entry.get("path")
            if not shard_rel:
                missing_shards.append(
                    f"{manifest_path.relative_to(REPO_ROOT)}:entry_missing_path:{output_name}"
                )
                continue
            shard_path = REPO_ROOT / str(shard_rel)
            if not shard_path.exists():
                missing_shards.append(str(shard_path.relative_to(REPO_ROOT)))
    status = (
        "blocked_missing_manifest_referenced_static_15r_shards"
        if missing_manifests or missing_shards
        else "materialized_row_level_verifier_available"
    )
    return {
        "status": status,
        "summary_path": str(STATIC_15R_SUMMARY.relative_to(REPO_ROOT)),
        "verifier_path": str(STATIC_15R_VERIFIER.relative_to(REPO_ROOT)),
        "checked_manifest_count": len(checked_manifests),
        "checked_manifests": checked_manifests,
        "missing_manifest_count": len(missing_manifests),
        "missing_shard_count": len(missing_shards),
        "missing_manifests": missing_manifests,
        "missing_shards": missing_shards,
        "row_level_verifier_command": (
            "py -3 "
            f"{STATIC_15R_VERIFIER.relative_to(REPO_ROOT)} --check"
        ),
    }


def build_checkpoint() -> dict[str, Any]:
    now_utc = datetime.now(timezone.utc)
    process = _process_rows()
    process_proof = _process_version_proof(now_utc, process)
    heartbeat = _heartbeat_summary(now_utc)
    tick = _tick_summary(now_utc)
    m1 = _m1_summary(now_utc)
    mt5 = _mt5_summary(now_utc)
    broker_lifecycle = _broker_lifecycle_summary(mt5)
    base_reload = _parse_utc(POST_RELOAD_TS)
    process_reload = _parse_utc(process.get("oldest_orchestrator_start_utc"))
    candidate_reload = base_reload
    if process_reload and (candidate_reload is None or process_reload > candidate_reload):
        candidate_reload = process_reload
    candidate = _candidate_summary(
        now_utc,
        reload_ts_text=(candidate_reload.isoformat() if candidate_reload else POST_RELOAD_TS),
    )
    gate_verification = _read_json(ROUTE_DIR / "LIVE_REPLAY_GATE_STACK_VERIFICATION.json", {})
    policy_summary = _read_json(ROUTE_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", {})
    calendar = _calendar_summary(now_utc)
    static_15r = _static_15r_blocker_summary()

    issues: list[dict[str, Any]] = []
    evidence_gaps: list[dict[str, Any]] = []
    if process["orchestrator_python"] != len(EXPECTED_SYMBOLS):
        issues.append({"code": "unexpected_orchestrator_process_count", "value": process["orchestrator_python"]})
    if process["missing_orchestrator_symbols"] or process["extra_orchestrator_symbols"]:
        issues.append(
            {
                "code": "orchestrator_symbol_set_mismatch",
                "missing": process["missing_orchestrator_symbols"],
                "extra": process["extra_orchestrator_symbols"],
            }
        )
    if process.get("profile_mismatches"):
        issues.append(
            {
                "code": "orchestrator_profile_mismatch",
                "profile_mismatches": process.get("profile_mismatches"),
                "profile_counts": process.get("profile_counts"),
            }
        )
    support_requirements = {
        "m1_capture_python": 1,
        "notification_worker_python": 1,
        "heartbeat_monitor_python": 1,
        "displacement_python": 1,
    }
    missing_support = {
        name: process.get(name, 0)
        for name, expected in support_requirements.items()
        if int(process.get(name, 0) or 0) < expected
    }
    if missing_support:
        issues.append(
            {
                "code": "live_support_processes_not_running",
                "missing_or_low_counts": missing_support,
                "expected_minimums": support_requirements,
            }
        )
    if process_proof.get("proof_status") != "all_24_live_orchestrators_running_current_runtime_surface":
        issues.append({"code": "live_process_version_proof_incomplete", "process_version_proof": process_proof})
    if heartbeat["count"] != len(EXPECTED_SYMBOLS) or heartbeat["stale_over_120s"]:
        issues.append({"code": "orchestrator_heartbeat_not_fresh", "heartbeat": heartbeat})
    if tick.get("dead_daemon_symbols"):
        issues.append(
            {
                "code": "tick_capture_daemons_not_running",
                "dead_daemon_symbols": tick.get("dead_daemon_symbols"),
                "classification": "daemon_process_absent_current_liveness_defect",
            }
        )
    if (
        tick["count"] != len(EXPECTED_SYMBOLS)
        or tick.get("unclassified_stale_over_180s")
        or tick.get("missing_symbols")
        or tick.get("extra_symbols")
    ):
        issues.append({"code": "tick_capture_not_fresh", "tick": tick})
    elif tick.get("classified_stale_over_180s"):
        evidence_gaps.append(
            {
                "code": "tick_capture_daemon_alive_no_new_broker_tick",
                "classification": tick.get("tick_freshness_classification_status"),
                "symbols": [
                    row.get("symbol") for row in tick.get("classified_stale_over_180s") or []
                ],
                "reason": (
                    "tick daemon is alive and broker symbol tick_msc has not advanced; "
                    "checkpoint records broker/session proof instead of failing as a dead feed"
                ),
            }
        )
    if (
        m1["symbol_count"] != len(EXPECTED_SYMBOLS)
        or m1["error_count"] not in (0, None)
        or m1.get("missing_symbols")
        or m1.get("extra_symbols")
    ):
        issues.append({"code": "m1_capture_unhealthy", "m1": m1})
    if isinstance(m1.get("state_age_s"), (int, float)) and m1["state_age_s"] > 120:
        issues.append({"code": "m1_capture_state_stale", "age_s": m1["state_age_s"]})
    if not mt5.get("initialized") or mt5.get("read_only_check") != "passed":
        issues.append({"code": "mt5_read_only_check_failed", "mt5": mt5})
    if broker_lifecycle.get("unreconciled_open_exposure_count", 0) or mt5.get("orders", 0):
        issues.append(
            {
                "code": "broker_open_exposure_present_requires_lifecycle_reconciliation",
                "positions": mt5.get("positions"),
                "orders": mt5.get("orders"),
                "broker_lifecycle": broker_lifecycle,
            }
        )
    if candidate["rows_missing_required_packet_fields"]:
        issues.append({"code": "candidate_packet_missing_fields", "count": candidate["rows_missing_required_packet_fields"]})
    if candidate["rows_with_null_zero_without_reason"]:
        issues.append(
            {
                "code": "candidate_packet_null_zero_without_reason",
                "count": candidate["rows_with_null_zero_without_reason"],
            }
        )
    if candidate["old_primary_analyzer_called_count"] or candidate["old_l2_required_count"]:
        issues.append(
            {
                "code": "old_primary_analyzer_or_l2_leakage",
                "old_pa": candidate["old_primary_analyzer_called_count"],
                "old_l2": candidate["old_l2_required_count"],
            }
        )
    if candidate.get("fixed_target_legacy_term_hits"):
        issues.append(
            {
                "code": "fixed_target_j46_j49_legacy_term_hit_in_post_reload_candidates",
                "scan": candidate.get("fixed_target_legacy_term_scan"),
            }
        )
    if candidate.get("native_live_writer_packet_rows", 0) == 0:
        no_candidate_records = candidate.get("candidate_records_after_reload") == 0
        evidence_gaps.append(
            {
                "code": "no_live_writer_candidate_packet_yet",
                "classification": "native_live_writer_candidate_packet_pending",
                "reason": (
                    "no post-reload vNext candidate record has been written since the current process reload"
                    if no_candidate_records
                    else "post-reload candidate records currently prove backfilled saved-record packet completeness only"
                ),
            }
        )
    if candidate.get("order_path_rows", 0) == 0:
        evidence_gaps.append(
            {
                "code": "no_vnext_order_path_packet_yet",
                "classification": "vnext_order_fill_close_packet_pending",
                "reason": "no post-reload vNext row reached repaired geometry/order placement/fill/close lifecycle",
            }
        )
    if (
        candidate.get("native_old_primary_analyzer_l2_absence_proof_status")
        != "explicit_false_on_native_live_writer_rows"
    ):
        evidence_gaps.append(
            {
                "code": "old_pa_l2_absence_not_explicit_in_candidate_packets",
                "classification": "explicit_old_pa_l2_absence_in_native_packets_pending",
                "reason": "current native live-writer candidate packets must carry explicit old PA/L2 false fields",
                "old_primary_analyzer_field_missing_count": candidate.get(
                    "native_old_primary_analyzer_field_missing_count"
                ),
                "old_l2_required_field_missing_count": candidate.get(
                    "native_old_l2_required_field_missing_count"
                ),
            }
        )
    if gate_verification.get("ok") is not True:
        issues.append({"code": "gate_stack_verification_not_ok", "verification": gate_verification})
    if calendar.get("tool_status") != "fresh":
        issues.append({"code": "calendar_freshness_not_ok", "calendar": calendar})

    current_policy = policy_summary.get("current_production_dynamic_policy_distribution", {})
    if "momentum_exhaustion" not in current_policy or "partial_be_runner" not in current_policy:
        issues.append({"code": "current_policy_distribution_missing_momentum_or_partial", "policy_distribution": current_policy})
    if set(current_policy) == {"be_after_trigger"}:
        issues.append({"code": "stale_be_only_current_policy_distribution"})
    if not broker_lifecycle.get("real_vnext_lifecycle_seen"):
        evidence_gaps.append(
            {
                "code": "no_real_vnext_broker_lifecycle_yet",
                "classification": "real_broker_lifecycle_reconciliation_pending",
                "reason": "MT5 is flat and has zero deals in the checkpoint window",
            }
        )
    elif (
        broker_lifecycle.get("open_vnext_position_count", 0)
        and broker_lifecycle.get("close_deal_reconciled_count", 0) == 0
    ):
        evidence_gaps.append(
            {
                "code": "vnext_open_position_close_reconciliation_pending",
                "classification": "real_broker_lifecycle_open_position_close_pending",
                "reason": (
                    "real vNext order/fill/open-position is reconciled to MT5 and internal "
                    "pending lifecycle; close/partial/BE/final deal reconciliation remains "
                    "pending while the position is open"
                ),
                "reconciled_open_position_ids": broker_lifecycle.get(
                    "reconciled_open_position_ids", []
                ),
                "entry_deal_reconciled_count": broker_lifecycle.get(
                    "entry_deal_reconciled_count", 0
                ),
            }
        )

    return {
        "schema_version": "vnext_live_activation_companion_checkpoint_v1",
        "generated_at_utc": now_utc.isoformat(),
        "route_id": "vnext_live_activation_active_repair_companion_2026_05_28",
        "git": _git_head(),
        "status": "ok" if not issues else "needs_repair",
        "issue_count": len(issues),
        "issues": issues,
        "evidence_gap_count": len(evidence_gaps),
        "evidence_gaps": evidence_gaps,
        "process": process,
        "process_version_proof": process_proof,
        "orchestrator_heartbeat": heartbeat,
        "tick_capture": tick,
        "m1_capture": m1,
        "mt5": mt5,
        "post_reload_candidate_flow": candidate,
        "calendar_local_files": calendar,
        "gate_stack_verification": gate_verification,
        "current_production_dynamic_policy_distribution": current_policy,
        "static_15r_ceiling_reproducibility": static_15r,
        "broker_lifecycle": broker_lifecycle,
    }


def _update_state_and_ledger(checkpoint: dict[str, Any]) -> None:
    state = _read_json(ACTIVE_STATE_PATH, {})
    now_utc = _parse_utc(checkpoint.get("generated_at_utc")) or datetime.now(timezone.utc)
    now_local = now_utc.astimezone(timezone(timedelta(hours=8)))
    state["updated_at"] = now_local.isoformat()
    state["current_head"] = checkpoint.get("git")
    broker_lifecycle = checkpoint.get("broker_lifecycle") or {}
    lifecycle_seen = bool(broker_lifecycle.get("real_vnext_lifecycle_seen"))
    close_reconciled = bool(broker_lifecycle.get("close_deal_reconciled_count", 0))
    state["status"] = (
        "live_vnext_order_fill_reconciled_open_position_awaiting_close_reconciliation"
        if checkpoint["status"] == "ok" and lifecycle_seen and not close_reconciled
        else "live_candidate_packet_repaired_verified_live_running_awaiting_real_vnext_lifecycle"
        if checkpoint["status"] == "ok"
        else "live_companion_checkpoint_detected_repair_needed"
    )
    gates = state.setdefault("gates", {})
    gates["live_health_latest_checkpoint"] = {
        "status": "live_fresh_vnext_open_position_entry_reconciled_close_pending"
        if checkpoint["status"] == "ok" and lifecycle_seen and not close_reconciled
        else "live_fresh_flat_current_no_vnext_lifecycle_yet"
        if checkpoint["status"] == "ok"
        else "live_checkpoint_detected_repair_needed",
        "summary": (
            "Current checkpoint verifies 24 live orchestrators, fresh heartbeats, fresh tick and M1 capture, "
            "MT5 read-only connectivity, complete post-reload candidate packets, no observed old PA/L2 leakage, "
            "and broker lifecycle exposure classified as reconciled-in-progress instead of flat once a real vNext fill exists."
        ),
        "evidence": {
            "measured_at_utc": checkpoint["generated_at_utc"],
            "process_summary": checkpoint["process"],
            "mt5_positions": checkpoint["mt5"].get("positions"),
            "mt5_pending_orders": checkpoint["mt5"].get("orders"),
            "mt5_history_orders_12h": checkpoint["mt5"].get("history_orders_12h"),
            "mt5_history_deals_12h": checkpoint["mt5"].get("history_deals_12h"),
            "broker_lifecycle": broker_lifecycle,
            "post_reload_candidate_rows": checkpoint["post_reload_candidate_flow"].get(
                "candidate_records_after_reload"
            ),
            "post_reload_candidate_outcomes": checkpoint["post_reload_candidate_flow"].get(
                "final_outcome_counts"
            ),
            "candidate_packet_null_zero_without_reason": checkpoint[
                "post_reload_candidate_flow"
            ].get("rows_with_null_zero_without_reason"),
            "issue_count": checkpoint["issue_count"],
            "issues": checkpoint["issues"],
            "evidence_gap_count": checkpoint.get("evidence_gap_count", 0),
            "evidence_gaps": checkpoint.get("evidence_gaps", []),
        },
        "evidence_files": [
            "scripts/build_vnext_live_activation_checkpoint.py",
            "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_COMPANION_CURRENT_CHECKPOINT.json",
        ],
    }
    gates["post_reload_candidate_proof"] = {
        **gates.get("post_reload_candidate_proof", {}),
        "status": "verified_current_no_order_path_yet"
        if checkpoint["post_reload_candidate_flow"].get("order_path_rows") == 0
        else "verified_current_order_path_present_requires_lifecycle_followup",
        "evidence": {
            **(gates.get("post_reload_candidate_proof", {}).get("evidence") or {}),
            **checkpoint["post_reload_candidate_flow"],
        },
    }
    gates["mt5_tick_data_watchdog_runtime"] = {
        **gates.get("mt5_tick_data_watchdog_runtime", {}),
        "status": "live_fresh_verified_current_after_checkpoint"
        if checkpoint["status"] == "ok"
        else "live_checkpoint_detected_runtime_issue",
        "evidence": {
            **(gates.get("mt5_tick_data_watchdog_runtime", {}).get("evidence") or {}),
            "measured_at_utc": checkpoint["generated_at_utc"],
            "heartbeat_count": checkpoint["orchestrator_heartbeat"].get("count"),
            "heartbeat_max_age_seconds": checkpoint["orchestrator_heartbeat"].get("max_age_s"),
            "tick_heartbeat_count": checkpoint["tick_capture"].get("count"),
            "tick_heartbeat_max_age_seconds": checkpoint["tick_capture"].get("max_age_s"),
            "m1_capture_error_count": checkpoint["m1_capture"].get("error_count"),
            "m1_error_count_zero_reason": checkpoint["m1_capture"].get("zero_error_count_reason"),
            "m1_capture_max_bar_lag_seconds": checkpoint["m1_capture"].get("max_closed_bar_lag_s"),
            "mt5_positions": checkpoint["mt5"].get("positions"),
            "mt5_orders": checkpoint["mt5"].get("orders"),
            "broker_lifecycle_status": broker_lifecycle.get("status"),
            "broker_lifecycle_reconciled_open_position_ids": broker_lifecycle.get(
                "reconciled_open_position_ids", []
            ),
        },
    }
    static_15r = checkpoint.get("static_15r_ceiling_reproducibility") or {}
    route_verifier_suite = gates.get("route_verifier_suite", {})
    gates["route_verifier_suite"] = {
        **route_verifier_suite,
        "status": route_verifier_suite.get(
            "status",
            "dynamic_and_momentum_reproducibility_restored_static_15r_extra_recheck_blocked",
        ),
        "summary": (
            "Dynamic-router and momentum-promotion ei15r verifiers are tracked separately; "
            "the static 1.5R ceiling row-level verifier remains blocked only by manifest-referenced shards absent on current disk."
        ),
        "evidence": {
            **(route_verifier_suite.get("evidence") or {}),
            "static_15r_ceiling_verifier_status": static_15r.get("status"),
            "static_15r_missing_manifest_count": static_15r.get("missing_manifest_count"),
            "static_15r_missing_shard_count": static_15r.get("missing_shard_count"),
            "static_15r_missing_shards_sample": (static_15r.get("missing_shards") or [])[:10],
            "static_15r_row_level_verifier": static_15r.get("row_level_verifier_command"),
        },
    }
    pending = []
    for item in state.get("known_pending_work", []):
        text = str(item)
        if "No eligible live broker lifecycle event" in text:
            continue
        if "No eligible real vNext broker fill/close/reconciliation" in text:
            continue
        if "static 1.5R ceiling verifier" in text or "static 15r" in text:
            continue
        pending.append(item)
    if static_15r.get("missing_manifest_count") or static_15r.get("missing_shard_count"):
        pending.append(
            "Separate static 1.5R ceiling row-level verifier remains blocked by "
            f"{static_15r.get('missing_shard_count')} manifest-referenced shards absent on current disk; "
            "dynamic-router and momentum-promotion ei15r verifiers remain the current reproducibility proof."
        )
    if not lifecycle_seen:
        pending.append(
            "No eligible real vNext broker fill/close/reconciliation lifecycle event is present in the current checkpoint; lifecycle Telegram parity remains synthetic/code-proven until the first real event appears."
        )
    elif not close_reconciled:
        pending.append(
            "Real vNext order/fill/open-position lifecycle is reconciled to MT5 and internal pending lifecycle; close/partial/BE/final deal reconciliation remains pending while the position is open."
        )
    seen = set()
    state["known_pending_work"] = [
        item for item in pending if not (str(item) in seen or seen.add(str(item)))
    ]
    _write_json(ACTIVE_STATE_PATH, state)

    row = {
        "route_id": checkpoint["route_id"],
        "ts": now_local.isoformat(),
        "event": "live_activation_companion_checkpoint",
        "status": checkpoint["status"],
        "details": {
            "issue_count": checkpoint["issue_count"],
            "evidence_gap_count": checkpoint.get("evidence_gap_count", 0),
            "process_count": checkpoint["process"].get("orchestrator_python"),
            "heartbeat_count": checkpoint["orchestrator_heartbeat"].get("count"),
            "tick_heartbeat_count": checkpoint["tick_capture"].get("count"),
            "m1_symbol_count": checkpoint["m1_capture"].get("symbol_count"),
            "mt5_positions": checkpoint["mt5"].get("positions"),
            "mt5_orders": checkpoint["mt5"].get("orders"),
            "history_deals_12h": checkpoint["mt5"].get("history_deals_12h"),
            "broker_lifecycle_status": broker_lifecycle.get("status"),
            "broker_lifecycle_open_vnext_position_count": broker_lifecycle.get(
                "open_vnext_position_count"
            ),
            "broker_lifecycle_entry_deal_reconciled_count": broker_lifecycle.get(
                "entry_deal_reconciled_count"
            ),
            "broker_lifecycle_close_deal_reconciled_count": broker_lifecycle.get(
                "close_deal_reconciled_count"
            ),
            "broker_lifecycle_reconciled_open_position_ids": broker_lifecycle.get(
                "reconciled_open_position_ids", []
            ),
            "candidate_records_after_reload": checkpoint["post_reload_candidate_flow"].get(
                "candidate_records_after_reload"
            ),
            "candidate_null_zero_without_reason": checkpoint[
                "post_reload_candidate_flow"
            ].get("rows_with_null_zero_without_reason"),
            "old_pa_count": checkpoint["post_reload_candidate_flow"].get(
                "old_primary_analyzer_called_count"
            ),
            "old_l2_count": checkpoint["post_reload_candidate_flow"].get("old_l2_required_count"),
            "live_writer_packet_rows": checkpoint["post_reload_candidate_flow"].get(
                "live_writer_packet_rows"
            ),
            "order_path_rows": checkpoint["post_reload_candidate_flow"].get("order_path_rows"),
            "static_15r_missing_shard_count": (
                checkpoint.get("static_15r_ceiling_reproducibility") or {}
            ).get("missing_shard_count"),
        },
    }
    rows = []
    if ACTIVE_LEDGER_PATH.exists():
        rows = [
            json.loads(line)
            for line in ACTIVE_LEDGER_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if rows and rows[-1].get("event") == row["event"]:
        rows[-1] = row
    else:
        rows.append(row)
    ACTIVE_LEDGER_PATH.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in rows),
        encoding="utf-8",
    )


def _null_paths(value: Any, prefix: str = "$") -> list[str]:
    if value is None:
        return [prefix]
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            if item is None and (
                key.endswith("_reason")
                or key.endswith("_missing_reason")
                or (key == "last_msc" and value.get("no_initial_capture_reason"))
            ):
                continue
            paths.extend(_null_paths(item, f"{prefix}.{key}"))
        return paths
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_null_paths(item, f"{prefix}[{index}]"))
        return paths
    return []


def _require_issue(issues: list[dict[str, Any]], source: str, code: str, **details: Any) -> None:
    issues.append({"source": source, "code": code, **details})


def _route_artifact_only_descendant(base_head: str, expected_head: str) -> dict[str, Any]:
    if base_head == expected_head:
        return {"allowed": True, "changed_files": [], "disallowed_files": []}
    ancestor = subprocess.call(
        ["git", "merge-base", "--is-ancestor", base_head, expected_head],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestor != 0:
        return {
            "allowed": False,
            "reason": "checkpoint_head_not_ancestor_of_expected_head",
            "changed_files": [],
            "disallowed_files": [],
        }
    diff = subprocess.run(
        ["git", "diff", "--name-only", f"{base_head}..{expected_head}"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    changed_files = [line.strip().replace("\\", "/") for line in diff.stdout.splitlines() if line.strip()]
    route_prefix = "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/"
    disallowed = [path for path in changed_files if not path.startswith(route_prefix)]
    return {
        "allowed": not disallowed,
        "changed_files": changed_files,
        "disallowed_files": disallowed,
    }


def _proof_quality_issues(
    checkpoint: dict[str, Any],
    *,
    source: str,
    expected_head: str | None,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if checkpoint.get("schema_version") != "vnext_live_activation_companion_checkpoint_v1":
        _require_issue(
            issues,
            source,
            "checkpoint_schema_version_mismatch",
            value=checkpoint.get("schema_version"),
        )
    if checkpoint.get("route_id") != "vnext_live_activation_active_repair_companion_2026_05_28":
        _require_issue(issues, source, "checkpoint_route_id_mismatch", value=checkpoint.get("route_id"))
    if checkpoint.get("status") != "ok" or checkpoint.get("issue_count") != 0:
        _require_issue(
            issues,
            source,
            "checkpoint_not_operationally_ok",
            status=checkpoint.get("status"),
            issue_count=checkpoint.get("issue_count"),
            issues=checkpoint.get("issues"),
        )

    git = checkpoint.get("git") if isinstance(checkpoint.get("git"), dict) else {}
    if not git.get("head"):
        _require_issue(issues, source, "checkpoint_git_head_missing")
    elif expected_head and git.get("head") != expected_head:
        route_descendant = _route_artifact_only_descendant(str(git.get("head")), expected_head)
        if not route_descendant.get("allowed"):
            _require_issue(
                issues,
                source,
                "checkpoint_git_head_mismatch",
                checkpoint_head=git.get("head"),
                expected_head=expected_head,
                route_artifact_only_descendant=route_descendant,
            )

    process = checkpoint.get("process") if isinstance(checkpoint.get("process"), dict) else {}
    if process.get("orchestrator_python") != len(EXPECTED_SYMBOLS):
        _require_issue(
            issues,
            source,
            "process_count_not_24",
            value=process.get("orchestrator_python"),
        )
    if sorted(process.get("orchestrator_symbols") or []) != EXPECTED_SYMBOLS:
        _require_issue(
            issues,
            source,
            "process_symbol_set_mismatch",
            symbols=process.get("orchestrator_symbols"),
        )
    if process.get("missing_orchestrator_symbols") or process.get("extra_orchestrator_symbols"):
        _require_issue(
            issues,
            source,
            "process_missing_or_extra_symbols",
            missing=process.get("missing_orchestrator_symbols"),
            extra=process.get("extra_orchestrator_symbols"),
        )
    if (process.get("profile_counts") or {}).get("redacted_account") != len(EXPECTED_SYMBOLS):
        _require_issue(
            issues,
            source,
            "redacted_account_profile_count_not_24",
            profile_counts=process.get("profile_counts"),
        )
    if process.get("profile_mismatches"):
        _require_issue(
            issues,
            source,
            "process_profile_mismatch",
            profile_mismatches=process.get("profile_mismatches"),
        )
    process_proof = (
        checkpoint.get("process_version_proof")
        if isinstance(checkpoint.get("process_version_proof"), dict)
        else {}
    )
    if process_proof.get("proof_status") != "all_24_live_orchestrators_running_current_runtime_surface":
        _require_issue(
            issues,
            source,
            "live_process_version_proof_incomplete",
            proof_status=process_proof.get("proof_status"),
            stale_or_unproven=process_proof.get("stale_or_unproven_orchestrators"),
        )
    if process_proof.get("current_head_is_post_786_or_later") is not True:
        _require_issue(
            issues,
            source,
            "checkpoint_head_not_post_786",
            current_git_head=process_proof.get("current_git_head"),
        )
    if not process_proof.get("config_hash") or not (process_proof.get("runtime_label_hash") or {}).get("sha256"):
        _require_issue(
            issues,
            source,
            "process_version_hashes_missing",
            config_hash=process_proof.get("config_hash"),
            runtime_label_hash=process_proof.get("runtime_label_hash"),
        )

    heartbeat = (
        checkpoint.get("orchestrator_heartbeat")
        if isinstance(checkpoint.get("orchestrator_heartbeat"), dict)
        else {}
    )
    if heartbeat.get("count") != len(EXPECTED_SYMBOLS) or heartbeat.get("stale_over_120s"):
        _require_issue(
            issues,
            source,
            "heartbeat_not_fresh_or_complete",
            count=heartbeat.get("count"),
            stale=heartbeat.get("stale_over_120s"),
        )
    if len(heartbeat.get("per_symbol") or []) != len(EXPECTED_SYMBOLS):
        _require_issue(
            issues,
            source,
            "heartbeat_per_symbol_not_24",
            count=len(heartbeat.get("per_symbol") or []),
        )

    tick = checkpoint.get("tick_capture") if isinstance(checkpoint.get("tick_capture"), dict) else {}
    if tick.get("count") != len(EXPECTED_SYMBOLS) or len(tick.get("per_symbol") or []) != len(EXPECTED_SYMBOLS):
        _require_issue(
            issues,
            source,
            "tick_capture_not_24",
            count=tick.get("count"),
            per_symbol_count=len(tick.get("per_symbol") or []),
        )
    if tick.get("lock_count") != len(EXPECTED_SYMBOLS):
        _require_issue(issues, source, "tick_capture_lock_count_not_24", lock_count=tick.get("lock_count"))
    if tick.get("missing_symbols") or tick.get("extra_symbols") or tick.get("unclassified_stale_over_180s"):
        _require_issue(
            issues,
            source,
            "tick_capture_missing_extra_or_stale",
            missing=tick.get("missing_symbols"),
            extra=tick.get("extra_symbols"),
            stale=tick.get("unclassified_stale_over_180s"),
        )
    if tick.get("stale_over_180s"):
        classified_symbols = {
            row.get("symbol") for row in tick.get("classified_stale_over_180s") or []
        }
        unclassified_symbols = {
            row.get("symbol") for row in tick.get("unclassified_stale_over_180s") or []
        }
        classified_or_unclassified = classified_symbols | unclassified_symbols
        missing_classification = [
            row.get("symbol")
            for row in tick.get("stale_over_180s") or []
            if row.get("symbol") not in classified_or_unclassified
            or not row.get("freshness_classification")
        ]
        if missing_classification:
            _require_issue(
                issues,
                source,
                "tick_capture_stale_rows_missing_classification",
                symbols=missing_classification,
            )
    zero_tick_rows_classified = (
        tick.get("total_ticks_reported") == 0
        and len(tick.get("per_symbol") or []) == len(EXPECTED_SYMBOLS)
        and all(
            isinstance(row, dict)
            and (
                row.get("no_initial_capture_reason")
                or row.get("freshness_classification")
            )
            for row in tick.get("per_symbol") or []
        )
    )
    if (
        not isinstance(tick.get("total_ticks_reported"), int)
        or tick.get("total_ticks_reported", 0) < 0
        or (tick.get("total_ticks_reported", 0) == 0 and not zero_tick_rows_classified)
    ):
        _require_issue(
            issues,
            source,
            "tick_capture_total_ticks_not_positive",
            total_ticks_reported=tick.get("total_ticks_reported"),
        )

    m1 = checkpoint.get("m1_capture") if isinstance(checkpoint.get("m1_capture"), dict) else {}
    if m1.get("symbol_count") != len(EXPECTED_SYMBOLS) or len(m1.get("per_symbol") or []) != len(EXPECTED_SYMBOLS):
        _require_issue(
            issues,
            source,
            "m1_capture_not_24",
            symbol_count=m1.get("symbol_count"),
            per_symbol_count=len(m1.get("per_symbol") or []),
        )
    if not m1.get("state_exists") or not m1.get("heartbeat_exists"):
        _require_issue(
            issues,
            source,
            "m1_capture_state_or_heartbeat_missing",
            state_exists=m1.get("state_exists"),
            heartbeat_exists=m1.get("heartbeat_exists"),
        )
    if m1.get("missing_symbols") or m1.get("extra_symbols"):
        _require_issue(
            issues,
            source,
            "m1_capture_missing_or_extra_symbols",
            missing=m1.get("missing_symbols"),
            extra=m1.get("extra_symbols"),
        )
    if m1.get("error_count") != 0:
        _require_issue(issues, source, "m1_capture_error_count_nonzero_or_missing", error_count=m1.get("error_count"))
    if isinstance(m1.get("state_age_s"), (int, float)) and m1["state_age_s"] > 120:
        _require_issue(issues, source, "m1_capture_state_stale", age_s=m1.get("state_age_s"))
    if isinstance(m1.get("max_seen_age_s"), (int, float)) and m1["max_seen_age_s"] > 120:
        _require_issue(issues, source, "m1_capture_seen_stale", age_s=m1.get("max_seen_age_s"))

    calendar = (
        checkpoint.get("calendar_local_files")
        if isinstance(checkpoint.get("calendar_local_files"), dict)
        else {}
    )
    if calendar.get("tool_status") != "fresh" or calendar.get("stale_or_missing_files"):
        _require_issue(
            issues,
            source,
            "calendar_not_fresh_by_repo_tool",
            tool_status=calendar.get("tool_status"),
            stale_or_missing_files=calendar.get("stale_or_missing_files"),
        )

    candidate = (
        checkpoint.get("post_reload_candidate_flow")
        if isinstance(checkpoint.get("post_reload_candidate_flow"), dict)
        else {}
    )
    candidate_count = candidate.get("candidate_records_after_reload")
    candidate_absence_proven = (
        candidate_count == 0
        and candidate.get("candidate_absence_proof_status")
        == "no_post_reload_vnext_candidate_records_since_current_process_reload"
    )
    if not isinstance(candidate_count, int) or (candidate_count <= 0 and not candidate_absence_proven):
        _require_issue(
            issues,
            source,
            "post_reload_candidate_records_absent",
            count=candidate_count,
            candidate_absence_proof_status=candidate.get("candidate_absence_proof_status"),
        )
    if int(candidate.get("native_live_writer_packet_rows") or 0) <= 0 and not candidate_absence_proven:
        _require_issue(
            issues,
            source,
            "native_live_writer_packet_absent",
            native_live_writer_packet_rows=candidate.get("native_live_writer_packet_rows"),
            packet_modes=candidate.get("packet_capture_mode_counts"),
        )
    if (
        candidate.get("native_old_primary_analyzer_l2_absence_proof_status")
        != "explicit_false_on_native_live_writer_rows"
        and not candidate_absence_proven
    ):
        _require_issue(
            issues,
            source,
            "native_old_pa_l2_absence_not_explicit_false",
            status=candidate.get("native_old_primary_analyzer_l2_absence_proof_status"),
            old_pa=candidate.get("native_old_primary_analyzer_called_count"),
            old_l2=candidate.get("native_old_l2_required_count"),
            missing_old_pa=candidate.get("native_old_primary_analyzer_field_missing_count"),
            missing_old_l2=candidate.get("native_old_l2_required_field_missing_count"),
        )
    if candidate.get("rows_missing_required_packet_fields") != 0:
        _require_issue(
            issues,
            source,
            "candidate_packet_missing_required_fields",
            count=candidate.get("rows_missing_required_packet_fields"),
        )
    if candidate.get("rows_with_null_zero_without_reason") != 0:
        _require_issue(
            issues,
            source,
            "candidate_packet_null_zero_without_reason",
            count=candidate.get("rows_with_null_zero_without_reason"),
        )
    if candidate.get("fixed_target_legacy_term_hits") != 0:
        _require_issue(
            issues,
            source,
            "candidate_fixed_target_legacy_terms_present",
            scan=candidate.get("fixed_target_legacy_term_scan"),
        )

    gate = (
        checkpoint.get("gate_stack_verification")
        if isinstance(checkpoint.get("gate_stack_verification"), dict)
        else {}
    )
    if gate.get("ok") is not True or gate.get("ledger_rows") != 27:
        _require_issue(
            issues,
            source,
            "gate_stack_verification_not_current_ok",
            ok=gate.get("ok"),
            ledger_rows=gate.get("ledger_rows"),
            issue_count=gate.get("issue_count"),
        )

    policy = (
        checkpoint.get("current_production_dynamic_policy_distribution")
        if isinstance(checkpoint.get("current_production_dynamic_policy_distribution"), dict)
        else {}
    )
    if "momentum_exhaustion" not in policy or "partial_be_runner" not in policy:
        _require_issue(
            issues,
            source,
            "current_policy_distribution_missing_momentum_or_partial",
            policy_distribution=policy,
        )
    if set(policy) == {"be_after_trigger"}:
        _require_issue(issues, source, "current_policy_distribution_stale_be_only")

    mt5 = checkpoint.get("mt5") if isinstance(checkpoint.get("mt5"), dict) else {}
    gap_codes = {
        str(item.get("code"))
        for item in checkpoint.get("evidence_gaps", [])
        if isinstance(item, dict)
    }
    gap_classifications = {
        str(item.get("code")): item.get("classification")
        for item in checkpoint.get("evidence_gaps", [])
        if isinstance(item, dict)
    }
    expected_gap_classifications = {
        "no_live_writer_candidate_packet_yet": "native_live_writer_candidate_packet_pending",
        "no_vnext_order_path_packet_yet": "vnext_order_fill_close_packet_pending",
        "old_pa_l2_absence_not_explicit_in_candidate_packets": "explicit_old_pa_l2_absence_in_native_packets_pending",
        "no_real_vnext_broker_lifecycle_yet": "real_broker_lifecycle_reconciliation_pending",
        "vnext_open_position_close_reconciliation_pending": "real_broker_lifecycle_open_position_close_pending",
    }
    expected_gap_codes: set[str] = set()
    if candidate.get("native_live_writer_packet_rows", 0) == 0:
        expected_gap_codes.add("no_live_writer_candidate_packet_yet")
    if candidate.get("order_path_rows", 0) == 0:
        expected_gap_codes.add("no_vnext_order_path_packet_yet")
    if (
        candidate.get("native_old_primary_analyzer_l2_absence_proof_status")
        != "explicit_false_on_native_live_writer_rows"
    ):
        expected_gap_codes.add("old_pa_l2_absence_not_explicit_in_candidate_packets")
    broker_lifecycle = (
        checkpoint.get("broker_lifecycle")
        if isinstance(checkpoint.get("broker_lifecycle"), dict)
        else {}
    )
    if broker_lifecycle.get("unreconciled_open_exposure_count", 0):
        _require_issue(
            issues,
            source,
            "broker_open_exposure_unreconciled",
            broker_lifecycle=broker_lifecycle,
        )
    if not broker_lifecycle.get("real_vnext_lifecycle_seen"):
        expected_gap_codes.add("no_real_vnext_broker_lifecycle_yet")
    elif (
        broker_lifecycle.get("open_vnext_position_count", 0)
        and broker_lifecycle.get("close_deal_reconciled_count", 0) == 0
    ):
        expected_gap_codes.add("vnext_open_position_close_reconciliation_pending")
    missing_gap_codes = sorted(expected_gap_codes - gap_codes)
    if missing_gap_codes:
        _require_issue(
            issues,
            source,
            "expected_evidence_gaps_not_recorded",
            missing_gap_codes=missing_gap_codes,
        )
    for code in sorted(expected_gap_codes):
        expected_classification = expected_gap_classifications[code]
        if gap_classifications.get(code) != expected_classification:
            _require_issue(
                issues,
                source,
                "evidence_gap_classification_mismatch",
                gap_code=code,
                classification=gap_classifications.get(code),
                expected_classification=expected_classification,
            )

    nulls = _null_paths(checkpoint)
    if nulls:
        _require_issue(
            issues,
            source,
            "checkpoint_contains_null_values",
            null_paths=nulls[:20],
            null_count=len(nulls),
        )
    return issues


def _checkpoint_stable_fingerprint(checkpoint: dict[str, Any]) -> dict[str, Any]:
    candidate = (
        checkpoint.get("post_reload_candidate_flow")
        if isinstance(checkpoint.get("post_reload_candidate_flow"), dict)
        else {}
    )
    mt5 = checkpoint.get("mt5") if isinstance(checkpoint.get("mt5"), dict) else {}
    lifecycle = (
        checkpoint.get("broker_lifecycle")
        if isinstance(checkpoint.get("broker_lifecycle"), dict)
        else {}
    )
    return {
        "status": checkpoint.get("status"),
        "issue_count": checkpoint.get("issue_count"),
        "issue_codes": [
            item.get("code") for item in checkpoint.get("issues", [])
            if isinstance(item, dict)
        ],
        "evidence_gap_codes": [
            [item.get("code"), item.get("classification")]
            for item in checkpoint.get("evidence_gaps", [])
            if isinstance(item, dict)
        ],
        "candidate_records_after_reload": candidate.get("candidate_records_after_reload"),
        "candidate_final_outcome_counts": candidate.get("final_outcome_counts"),
        "candidate_order_path_rows": candidate.get("order_path_rows"),
        "candidate_live_writer_packet_rows": candidate.get("live_writer_packet_rows"),
        "candidate_missing_packet_fields": candidate.get("rows_missing_required_packet_fields"),
        "candidate_null_zero_without_reason": candidate.get("rows_with_null_zero_without_reason"),
        "candidate_old_pa_count": candidate.get("old_primary_analyzer_called_count"),
        "candidate_old_l2_count": candidate.get("old_l2_required_count"),
        "mt5_positions": mt5.get("positions"),
        "mt5_orders": mt5.get("orders"),
        "mt5_history_orders_12h": mt5.get("history_orders_12h"),
        "mt5_history_deals_12h": mt5.get("history_deals_12h"),
        "mt5_system_position_count": mt5.get("system_position_count"),
        "mt5_system_order_count": mt5.get("system_order_count"),
        "mt5_system_history_order_count_12h": mt5.get("system_history_order_count_12h"),
        "mt5_system_history_deal_count_12h": mt5.get("system_history_deal_count_12h"),
        "broker_lifecycle_status": lifecycle.get("status"),
        "broker_lifecycle_open_vnext_position_count": lifecycle.get("open_vnext_position_count"),
        "broker_lifecycle_open_vnext_order_count": lifecycle.get("open_vnext_order_count"),
        "broker_lifecycle_entry_deal_reconciled_count": lifecycle.get(
            "entry_deal_reconciled_count"
        ),
        "broker_lifecycle_close_deal_reconciled_count": lifecycle.get(
            "close_deal_reconciled_count"
        ),
        "broker_lifecycle_reconciled_open_position_ids": lifecycle.get(
            "reconciled_open_position_ids"
        ),
        "broker_lifecycle_unreconciled_open_position_ids": lifecycle.get(
            "unreconciled_open_position_ids"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--update-state", action="store_true")
    args = parser.parse_args()

    checkpoint = build_checkpoint()
    comparable = dict(checkpoint)
    comparable.pop("generated_at_utc", None)
    if args.check:
        current = _read_json(CHECKPOINT_PATH, {})
        current_ts = _parse_utc((current or {}).get("generated_at_utc"))
        current_age_s = (
            round((datetime.now(timezone.utc) - current_ts).total_seconds(), 1)
            if current_ts
            else None
        )
        if not current:
            print(json.dumps({"status": "failed", "reason": "checkpoint_missing"}, sort_keys=True))
            return 1
        if current.get("status") != "ok":
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "reason": "saved_checkpoint_not_ok",
                        "issue_count": current.get("issue_count"),
                    },
                    sort_keys=True,
                )
            )
            return 1
        if checkpoint["status"] != "ok":
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "reason": "current_live_checkpoint_not_ok",
                        "issue_count": checkpoint["issue_count"],
                        "issues": checkpoint["issues"],
                    },
                    sort_keys=True,
                )
            )
            return 1
        expected_head = (_git_head() or {}).get("head")
        proof_issues = _proof_quality_issues(
            current,
            source="saved_checkpoint",
            expected_head=expected_head,
        ) + _proof_quality_issues(
            checkpoint,
            source="current_live_checkpoint",
            expected_head=expected_head,
        )
        if proof_issues:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "reason": "checkpoint_proof_quality_failed",
                        "proof_issue_count": len(proof_issues),
                        "proof_issues": proof_issues,
                    },
                    sort_keys=True,
                )
            )
            return 1
        saved_fingerprint = _checkpoint_stable_fingerprint(current)
        live_fingerprint = _checkpoint_stable_fingerprint(checkpoint)
        if saved_fingerprint != live_fingerprint:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "reason": "saved_checkpoint_not_current",
                        "saved": saved_fingerprint,
                        "current": live_fingerprint,
                    },
                    sort_keys=True,
                )
            )
            return 1
        if isinstance(current_age_s, (int, float)) and current_age_s > 300:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "reason": "saved_checkpoint_stale",
                        "age_s": current_age_s,
                    },
                    sort_keys=True,
                )
            )
            return 1
        print(
            json.dumps(
                {
                    "status": "passed",
                    "evidence_gap_count": checkpoint.get("evidence_gap_count", 0),
                    "issue_count": checkpoint["issue_count"],
                    "proof_issue_count": 0,
                    "saved_checkpoint_age_s": current_age_s,
                },
                sort_keys=True,
            )
        )
        return 0

    _write_json(CHECKPOINT_PATH, checkpoint)
    if args.update_state:
        _update_state_and_ledger(checkpoint)
    print(
        json.dumps(
            {
                "status": checkpoint["status"],
                "issue_count": checkpoint["issue_count"],
                "evidence_gap_count": checkpoint.get("evidence_gap_count", 0),
                "process_count": checkpoint["process"].get("orchestrator_python"),
                "candidate_records_after_reload": checkpoint[
                    "post_reload_candidate_flow"
                ].get("candidate_records_after_reload"),
                "mt5_positions": checkpoint["mt5"].get("positions"),
                "mt5_orders": checkpoint["mt5"].get("orders"),
                "output": str(CHECKPOINT_PATH.relative_to(REPO_ROOT)),
            },
            sort_keys=True,
        )
    )
    return 0 if checkpoint["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
