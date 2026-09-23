#!/usr/bin/env python3
"""Emergency-close all redacted_account MT5 exposure and stop GTOS runtime.

This script is intentionally outside the normal orchestrator. It connects
directly to MT5, cancels pending orders, closes every open position on the
connected redacted_account account, writes an audit report, disables autostart, and
terminates GTOS runtime processes.

Dry run:
    python scripts/emergency_close_and_stop_redacted_account.py --dry-run

Live emergency:
    python scripts/emergency_close_and_stop_redacted_account.py --yes

Manual confirmation live emergency:
    python scripts/emergency_close_and_stop_redacted_account.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import MetaTrader5 as mt5
except Exception as exc:  # pragma: no cover - environment dependent
    print(f"ERROR: MetaTrader5 import failed: {exc}", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except Exception as exc:  # pragma: no cover - environment dependent
    print(f"ERROR: PyYAML import failed: {exc}", file=sys.stderr)
    sys.exit(1)


PROFILE = "redacted_account"
RUNTIME_NAMESPACE = "redacted_account_live_bee34003"
EMERGENCY_MAGIC = 20260603
CONFIRM_PHRASE = "EMERGENCY CLOSE redacted_account"

LOCK_DIR = ROOT / "knowledge_base" / "meta"
PIPELINE_STATE_DIR = ROOT / "pipeline_state"
SHADOW_LOG_DIR = ROOT / "shadow_logs"
REPORT_DIR = SHADOW_LOG_DIR / RUNTIME_NAMESPACE
PROFILE_PATH = ROOT / "config" / "profiles" / "redacted_account.yaml"

AUTOSTART_DISABLED_FLAG = LOCK_DIR / "AUTOSTART_DISABLED.flag"
RESEARCH_RUNTIME_HALT_FLAG = PIPELINE_STATE_DIR / "RESEARCH_RUNTIME_HALT.flag"
GTOS_HARD_PRODUCTION_HALT_FLAG = PIPELINE_STATE_DIR / "GTOS_HARD_PRODUCTION_HALT.flag"

DONE_RETCODES = {
    getattr(mt5, "TRADE_RETCODE_DONE", 10009),
    getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", 10010),
}


@dataclass
class OrderSendAttempt:
    request: dict[str, Any]
    retcode: int | None
    comment: str | None
    order: int | None
    deal: int | None
    price: float | None
    last_error: Any = None


@dataclass
class PositionCloseResult:
    ticket: int
    symbol: str
    type: str
    initial_volume: float
    final_status: str
    attempts: list[OrderSendAttempt] = field(default_factory=list)
    error: str | None = None


@dataclass
class PendingOrderCancelResult:
    ticket: int
    symbol: str
    type: int
    volume_initial: float
    retcode: int | None = None
    comment: str | None = None
    error: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_profile() -> dict[str, Any]:
    with PROFILE_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"profile file did not load as dict: {PROFILE_PATH}")
    return data


def sha256_text(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def snapshot(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "_asdict"):
        return dict(value._asdict())
    if hasattr(value, "_fields"):
        return {name: getattr(value, name, None) for name in value._fields}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "__dict__"):
        return {k: v for k, v in vars(value).items() if not k.startswith("_")}
    return {}


def assert_redacted_account_account(profile: dict[str, Any], *, strict: bool) -> dict[str, Any]:
    account = snapshot(mt5.account_info())
    terminal = snapshot(mt5.terminal_info())
    if not account:
        raise RuntimeError("mt5.account_info() returned no account")

    expected = (
        profile.get("broker_profile", {}).get("expected_account", {})
        if isinstance(profile.get("broker_profile"), dict)
        else {}
    )
    actual = {
        "login_sha256": sha256_text(account.get("login")) if account.get("login") else None,
        "server": account.get("server"),
        "company": account.get("company"),
        "currency": account.get("currency"),
        "trade_expert": account.get("trade_expert"),
        "trade_allowed": account.get("trade_allowed"),
        "terminal_path": terminal.get("path"),
        "terminal_data_path": terminal.get("data_path"),
    }
    fields = ("login_sha256", "server", "company", "currency")
    mismatches = {
        field: {"expected": expected.get(field), "actual": actual.get(field)}
        for field in fields
        if expected.get(field) not in (None, "") and str(expected.get(field)) != str(actual.get(field))
    }
    if strict and mismatches:
        raise RuntimeError(f"connected MT5 account is not the configured redacted_account account: {mismatches}")
    return {"expected_checked": fields, "actual": actual, "mismatches": mismatches}


def initialize_mt5(profile: dict[str, Any], terminal_path: str | None) -> dict[str, Any]:
    mt5_cfg = profile.get("mt5") if isinstance(profile.get("mt5"), dict) else {}
    selected_terminal = terminal_path or os.environ.get("GTOS_MT5_TERMINAL_PATH") or mt5_cfg.get("terminal_path")
    selected_terminal = str(selected_terminal).strip() if selected_terminal else ""

    if selected_terminal:
        ok = mt5.initialize(path=selected_terminal)
    else:
        ok = mt5.initialize()
    if not ok:
        raise RuntimeError(f"mt5.initialize() failed: {mt5.last_error()}")
    return {"terminal_path_argument": selected_terminal or None, "version": mt5.version()}


def filling_candidates(info: Any) -> list[int]:
    mode = int(getattr(info, "filling_mode", 0) or 0)
    values: list[int] = []
    if mode & 2:
        values.append(mt5.ORDER_FILLING_IOC)
    if mode & 1:
        values.append(mt5.ORDER_FILLING_FOK)
    values.extend([mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN])
    unique: list[int] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def position_type_name(position_type: int) -> str:
    if position_type == mt5.POSITION_TYPE_BUY:
        return "BUY"
    if position_type == mt5.POSITION_TYPE_SELL:
        return "SELL"
    return str(position_type)


def visible_symbol(symbol: str) -> bool:
    info = mt5.symbol_info(symbol)
    if info is None:
        return False
    if getattr(info, "visible", False):
        return True
    return bool(mt5.symbol_select(symbol, True))


def close_position(ticket: int, *, deviation: int, max_attempts: int, delay_s: float) -> PositionCloseResult:
    current = mt5.positions_get(ticket=ticket)
    if current is None:
        return PositionCloseResult(
            ticket=ticket,
            symbol="unknown",
            type="unknown",
            initial_volume=0.0,
            final_status="MT5_ERROR",
            error=f"positions_get(ticket={ticket}) returned None: {mt5.last_error()}",
        )
    if len(current) == 0:
        return PositionCloseResult(
            ticket=ticket,
            symbol="unknown",
            type="unknown",
            initial_volume=0.0,
            final_status="ALREADY_CLOSED",
        )

    first = current[0]
    result = PositionCloseResult(
        ticket=int(first.ticket),
        symbol=str(first.symbol),
        type=position_type_name(int(first.type)),
        initial_volume=float(first.volume),
        final_status="OPEN",
    )

    for _attempt_no in range(1, max_attempts + 1):
        latest = mt5.positions_get(ticket=ticket)
        if latest is None:
            result.error = f"positions_get returned None while closing: {mt5.last_error()}"
            time.sleep(delay_s)
            continue
        if len(latest) == 0:
            result.final_status = "CLOSED"
            result.error = None
            return result

        position = latest[0]
        symbol = str(position.symbol)
        result.symbol = symbol
        result.type = position_type_name(int(position.type))

        if not visible_symbol(symbol):
            result.error = f"symbol_select({symbol}) failed"
            time.sleep(delay_s)
            continue

        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if info is None:
            result.error = f"symbol_info({symbol}) returned None"
            time.sleep(delay_s)
            continue
        if tick is None:
            result.error = f"symbol_info_tick({symbol}) returned None"
            time.sleep(delay_s)
            continue

        is_buy = int(position.type) == mt5.POSITION_TYPE_BUY
        order_type = mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY
        price = float(tick.bid if is_buy else tick.ask)
        request_base = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(position.volume),
            "type": order_type,
            "position": int(position.ticket),
            "price": price,
            "deviation": deviation,
            "magic": EMERGENCY_MAGIC,
            "comment": "GTOS_EMERGENCY_CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
        }

        sent_done = False
        for filling in filling_candidates(info):
            request = {**request_base, "type_filling": filling}
            send = mt5.order_send(request)
            if send is None:
                result.attempts.append(
                    OrderSendAttempt(
                        request=request,
                        retcode=None,
                        comment=None,
                        order=None,
                        deal=None,
                        price=None,
                        last_error=mt5.last_error(),
                    )
                )
                continue

            attempt = OrderSendAttempt(
                request=request,
                retcode=int(send.retcode),
                comment=str(getattr(send, "comment", "")),
                order=int(getattr(send, "order", 0) or 0),
                deal=int(getattr(send, "deal", 0) or 0),
                price=float(getattr(send, "price", 0.0) or 0.0),
            )
            result.attempts.append(attempt)
            if int(send.retcode) in DONE_RETCODES:
                sent_done = True
                break

        time.sleep(delay_s if sent_done else max(delay_s, 0.75))

    final = mt5.positions_get(ticket=ticket)
    if final is None:
        result.final_status = "UNKNOWN"
        result.error = f"final positions_get returned None: {mt5.last_error()}"
    elif len(final) == 0:
        result.final_status = "CLOSED"
        result.error = None
    else:
        result.final_status = "STILL_OPEN"
        result.error = "max close attempts exhausted"
    return result


def cancel_pending_order(order: Any) -> PendingOrderCancelResult:
    result = PendingOrderCancelResult(
        ticket=int(order.ticket),
        symbol=str(order.symbol),
        type=int(order.type),
        volume_initial=float(getattr(order, "volume_initial", 0.0) or 0.0),
    )
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": int(order.ticket),
        "symbol": str(order.symbol),
        "comment": "GTOS_EMERGENCY_CANCEL",
    }
    send = mt5.order_send(request)
    if send is None:
        result.error = f"order_send(remove) returned None: {mt5.last_error()}"
        return result
    result.retcode = int(send.retcode)
    result.comment = str(getattr(send, "comment", ""))
    if int(send.retcode) not in DONE_RETCODES:
        result.error = f"cancel retcode={send.retcode} comment={result.comment}"
    return result


def read_pid_from_lock(path: Path) -> int | None:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace").strip()
        if not text:
            return None
        if text.startswith("{"):
            data = json.loads(text)
            pid = data.get("pid")
        elif text.startswith("pid="):
            pid = text.split()[0].split("=", 1)[1]
        else:
            pid = text.split()[0]
        pid_int = int(pid)
        return pid_int if pid_int > 0 else None
    except Exception:
        return None


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def terminate_pid(pid: int, *, dry_run: bool, force: bool = True) -> dict[str, Any]:
    detail = {"pid": pid, "alive_before": process_alive(pid), "killed": False, "error": None}
    if dry_run or not detail["alive_before"]:
        return detail
    try:
        if os.name == "nt" and force:
            completed = subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            detail["killed"] = completed.returncode == 0
            if completed.returncode != 0:
                detail["error"] = (completed.stderr or completed.stdout or "").strip()
        else:
            os.kill(pid, signal.SIGTERM)
            detail["killed"] = True
    except Exception as exc:
        detail["error"] = str(exc)
    return detail


def lock_file_patterns(namespace: str) -> list[str]:
    return [
        f".orchestrator_{namespace}_*.lock",
        f".tick_capture_*_{namespace}.lock",
        f".m1_capture_all_{namespace}.lock",
        f".notification_queue_worker_{namespace}.lock",
        f".dual_broker_execution_follower_{namespace}.lock",
        f".dual_broker_trade_record_projector_{namespace}.lock",
        f".watchdog_{namespace}.lock",
        ".displacement_logger.lock",
        ".heartbeat_monitor.lock",
    ]


def stop_processes_from_locks(*, namespace: str, dry_run: bool) -> list[dict[str, Any]]:
    stopped: list[dict[str, Any]] = []
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    seen_paths: set[Path] = set()
    for pattern in lock_file_patterns(namespace):
        for path in LOCK_DIR.glob(pattern):
            if path in seen_paths:
                continue
            seen_paths.add(path)
            pid = read_pid_from_lock(path)
            item = {"source": "lock_file", "path": str(path.relative_to(ROOT)), "pid": pid}
            if pid is not None:
                item.update(terminate_pid(pid, dry_run=dry_run))
            if not dry_run:
                try:
                    path.unlink(missing_ok=True)
                    item["lock_removed"] = True
                except Exception as exc:
                    item["lock_removed"] = False
                    item["lock_remove_error"] = str(exc)
            stopped.append(item)
    return stopped


def powershell_process_sweep(namespace: str, *, dry_run: bool) -> list[dict[str, Any]]:
    """Kill GTOS processes still running even if their lock file is absent."""
    if os.name != "nt":
        return []
    ps = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { "
        "$_.CommandLine -and "
        "($_.CommandLine -like '*ai-trading-agent*') -and "
        "("
        "$_.CommandLine -like '*run_agent.py*' -or "
        "$_.CommandLine -like '*src.components.tick_capture*' -or "
        "$_.CommandLine -like '*src.components.m1_capture*' -or "
        "$_.CommandLine -like '*src.utils.notification_queue*' -or "
        "$_.CommandLine -like '*displacement_logger.py*' -or "
        "$_.CommandLine -like '*src.safety.heartbeat_monitor*' -or "
        "$_.CommandLine -like '*dual_broker_execution_follower.py*' -or "
        "$_.CommandLine -like '*dual_broker_trade_record_projector.py*'"
        ") -and "
        "("
        f"$_.CommandLine -like '*{namespace}*' -or "
        "$_.CommandLine -like '*displacement_logger.py*' -or "
        "$_.CommandLine -like '*src.safety.heartbeat_monitor*'"
        ")"
        "} | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return [{"source": "process_sweep", "error": str(exc)}]
    if completed.returncode != 0:
        return [{"source": "process_sweep", "error": completed.stderr.strip()}]
    text = completed.stdout.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return [{"source": "process_sweep", "error": f"json parse failed: {exc}", "raw": text[:500]}]
    rows = parsed if isinstance(parsed, list) else [parsed]
    killed: list[dict[str, Any]] = []
    current_pid = os.getpid()
    for row in rows:
        pid = int(row.get("ProcessId") or 0)
        if pid <= 0 or pid == current_pid:
            continue
        item = {
            "source": "process_sweep",
            "pid": pid,
            "command_line": str(row.get("CommandLine") or "")[:500],
        }
        item.update(terminate_pid(pid, dry_run=dry_run))
        killed.append(item)
    return killed


def write_kill_switches(*, dry_run: bool) -> dict[str, Any]:
    payload = (
        f"GTOS emergency stop\n"
        f"created_utc={utc_now()}\n"
        f"profile={PROFILE}\n"
        f"runtime_namespace={RUNTIME_NAMESPACE}\n"
        f"script=scripts/emergency_close_and_stop_redacted_account.py\n"
    )
    result: dict[str, Any] = {}
    for path in (
        AUTOSTART_DISABLED_FLAG,
        RESEARCH_RUNTIME_HALT_FLAG,
        GTOS_HARD_PRODUCTION_HALT_FLAG,
    ):
        result[str(path.relative_to(ROOT))] = {"would_write": dry_run, "written": False}
        if dry_run:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        result[str(path.relative_to(ROOT))] = {"would_write": False, "written": True}
    return result


def serialize_dataclass_list(items: list[Any]) -> list[dict[str, Any]]:
    return [asdict(item) for item in items]


def position_row(position: Any) -> dict[str, Any]:
    data = snapshot(position)
    keep = {
        "ticket",
        "symbol",
        "type",
        "volume",
        "price_open",
        "sl",
        "tp",
        "profit",
        "swap",
        "commission",
        "magic",
        "comment",
        "time",
        "time_msc",
    }
    return {key: data.get(key) for key in keep}


def order_row(order: Any) -> dict[str, Any]:
    data = snapshot(order)
    keep = {
        "ticket",
        "symbol",
        "type",
        "volume_initial",
        "volume_current",
        "price_open",
        "sl",
        "tp",
        "magic",
        "comment",
        "time_setup",
        "time_setup_msc",
    }
    return {key: data.get(key) for key in keep}


def write_reports(report: dict[str, Any]) -> dict[str, str]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = REPORT_DIR / f"emergency_close_and_stop_redacted_account_{stamp}.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    csv_path = REPORT_DIR / f"emergency_close_and_stop_redacted_account_{stamp}.csv"
    rows = []
    for item in report.get("position_close_results", []):
        attempts = item.get("attempts") or []
        rows.append(
            {
                "ticket": item.get("ticket"),
                "symbol": item.get("symbol"),
                "type": item.get("type"),
                "initial_volume": item.get("initial_volume"),
                "final_status": item.get("final_status"),
                "attempt_count": len(attempts),
                "last_retcode": attempts[-1].get("retcode") if attempts else None,
                "last_comment": attempts[-1].get("comment") if attempts else None,
                "error": item.get("error"),
            }
        )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "ticket",
                "symbol",
                "type",
                "initial_volume",
                "final_status",
                "attempt_count",
                "last_retcode",
                "last_comment",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return {"json": str(json_path), "csv": str(csv_path)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emergency close all redacted_account MT5 trades and stop GTOS runtime.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Inspect only; do not send MT5 orders or stop processes.")
    parser.add_argument("--yes", action="store_true", help="Skip interactive confirmation.")
    parser.add_argument("--terminal-path", default=None, help="Override MT5 terminal64.exe path.")
    parser.add_argument("--deviation", type=int, default=100, help="MT5 close deviation in points.")
    parser.add_argument("--max-attempts", type=int, default=8, help="Close attempts per position.")
    parser.add_argument("--delay-s", type=float, default=0.75, help="Delay between close attempts.")
    parser.add_argument("--skip-account-guard", action="store_true", help="Do not enforce configured redacted_account account identity.")
    parser.add_argument("--keep-pending-orders", action="store_true", help="Do not cancel pending orders.")
    parser.add_argument("--keep-system-running", action="store_true", help="Close/cancel trades only; do not write stop flags or kill runtime.")
    return parser.parse_args()


def require_confirmation(args: argparse.Namespace) -> None:
    if args.dry_run or args.yes:
        return
    print("LIVE EMERGENCY ACTION: this will close every open MT5 position on the connected redacted_account account.")
    print("It will also cancel pending orders and stop the GTOS runtime unless disabled by flags.")
    phrase = input(f"Type {CONFIRM_PHRASE!r} to continue: ").strip()
    if phrase != CONFIRM_PHRASE:
        raise RuntimeError("confirmation phrase mismatch; aborting")


def main() -> int:
    args = parse_args()
    require_confirmation(args)

    load_dotenv()
    profile = load_profile()
    report: dict[str, Any] = {
        "script": "scripts/emergency_close_and_stop_redacted_account.py",
        "started_utc": utc_now(),
        "profile": PROFILE,
        "runtime_namespace": RUNTIME_NAMESPACE,
        "dry_run": args.dry_run,
        "args": vars(args),
    }

    try:
        report["mt5_initialize"] = initialize_mt5(profile, args.terminal_path)
        report["account_guard"] = assert_redacted_account_account(profile, strict=not args.skip_account_guard)
        account_actual = report["account_guard"]["actual"]
        if not args.dry_run and account_actual.get("trade_expert") is False:
            raise RuntimeError("MT5 Algo Trading is disabled: account_info.trade_expert=False")

        if not args.keep_system_running:
            report["kill_switches_pre_close"] = write_kill_switches(dry_run=args.dry_run)

        positions = list(mt5.positions_get() or [])
        orders = list(mt5.orders_get() or [])
        report["positions_before"] = [position_row(position) for position in positions]
        report["orders_before"] = [order_row(order) for order in orders]

        cancel_results: list[PendingOrderCancelResult] = []
        if not args.keep_pending_orders:
            if args.dry_run:
                report["pending_order_cancel_results"] = [
                    {
                        "ticket": int(order.ticket),
                        "symbol": str(order.symbol),
                        "type": int(order.type),
                        "volume_initial": float(getattr(order, "volume_initial", 0.0) or 0.0),
                        "dry_run": True,
                    }
                    for order in orders
                ]
            else:
                for order in orders:
                    cancel_results.append(cancel_pending_order(order))
                report["pending_order_cancel_results"] = serialize_dataclass_list(cancel_results)
        else:
            report["pending_order_cancel_results"] = []
            report["pending_order_cancel_skipped"] = True

        close_results: list[PositionCloseResult] = []
        if args.dry_run:
            report["position_close_results"] = [
                {
                    "ticket": int(position.ticket),
                    "symbol": str(position.symbol),
                    "type": position_type_name(int(position.type)),
                    "initial_volume": float(position.volume),
                    "final_status": "DRY_RUN_WOULD_CLOSE",
                    "attempts": [],
                    "error": None,
                }
                for position in positions
            ]
        else:
            for position in positions:
                close_results.append(
                    close_position(
                        int(position.ticket),
                        deviation=args.deviation,
                        max_attempts=args.max_attempts,
                        delay_s=args.delay_s,
                    )
                )
            report["position_close_results"] = serialize_dataclass_list(close_results)

        report["positions_after_close"] = [position_row(position) for position in list(mt5.positions_get() or [])]
        report["orders_after_cancel"] = [order_row(order) for order in list(mt5.orders_get() or [])]

        if not args.keep_system_running:
            report["runtime_stop_from_locks"] = stop_processes_from_locks(namespace=RUNTIME_NAMESPACE, dry_run=args.dry_run)
            report["runtime_stop_process_sweep"] = powershell_process_sweep(RUNTIME_NAMESPACE, dry_run=args.dry_run)

        report["positions_final"] = [position_row(position) for position in list(mt5.positions_get() or [])]
        report["orders_final"] = [order_row(order) for order in list(mt5.orders_get() or [])]
        report["finished_utc"] = utc_now()

        report_paths = write_reports(report)
        report["report_paths"] = report_paths
        print(json.dumps(
            {
                "dry_run": args.dry_run,
                "positions_before": len(report["positions_before"]),
                "positions_final": len(report["positions_final"]),
                "orders_before": len(report["orders_before"]),
                "orders_final": len(report["orders_final"]),
                "report": report_paths,
            },
            indent=2,
        ))

        failed_closes = [
            item for item in report.get("position_close_results", [])
            if item.get("final_status") not in {"CLOSED", "ALREADY_CLOSED", "DRY_RUN_WOULD_CLOSE"}
        ]
        if failed_closes or (not args.dry_run and report["positions_final"]):
            return 2
        return 0
    except Exception as exc:
        report["fatal_error"] = str(exc)
        report["finished_utc"] = utc_now()
        try:
            report_paths = write_reports(report)
            print(json.dumps({"fatal_error": str(exc), "report": report_paths}, indent=2), file=sys.stderr)
        except Exception:
            print(f"FATAL: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
