from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-27"
OUTPUT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE03_MT5_ALIAS_VERIFICATION_{DATE}.json"

ALIASES = (
    ("GER40", "GER30"),
    ("UKOIL_cash", "UKOUSD"),
    ("USOIL_cash", "USOUSD"),
)


def _rate_time(row: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(row["time"]), tz=timezone.utc).isoformat()
    except Exception:
        return None


def _tick_payload(tick: Any) -> dict[str, Any] | None:
    if tick is None:
        return None
    data = tick._asdict() if hasattr(tick, "_asdict") else {}
    if "time" in data:
        try:
            data["time_utc"] = datetime.fromtimestamp(
                int(data["time"]),
                tz=timezone.utc,
            ).isoformat()
        except Exception:
            data["time_utc"] = None
    return data


def _info_payload(info: Any) -> dict[str, Any] | None:
    if info is None:
        return None
    data = info._asdict() if hasattr(info, "_asdict") else {}
    keys = (
        "name",
        "path",
        "visible",
        "select",
        "trade_mode",
        "trade_calc_mode",
        "trade_contract_size",
        "trade_tick_size",
        "trade_tick_value",
        "volume_min",
        "volume_step",
        "volume_max",
        "filling_mode",
        "spread",
        "digits",
        "point",
        "currency_base",
        "currency_profit",
        "currency_margin",
    )
    return {key: data.get(key) for key in keys if key in data}


def _probe_symbol(mt5: Any, file_symbol: str, mt5_symbol: str) -> dict[str, Any]:
    before_info = mt5.symbol_info(mt5_symbol)
    select_ok = bool(mt5.symbol_select(mt5_symbol, True))
    select_error = mt5.last_error()
    info = mt5.symbol_info(mt5_symbol)
    tick = mt5.symbol_info_tick(mt5_symbol) if select_ok else None
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    rates = None
    rates_error = None
    if select_ok:
        rates = mt5.copy_rates_range(mt5_symbol, mt5.TIMEFRAME_M15, start, now)
        rates_error = mt5.last_error()
    rows = 0 if rates is None else int(len(rates))
    status = "verified_broker_symbol_with_recent_m15_rates"
    failed_fields: list[str] = []
    if before_info is None and info is None:
        status = "failed_symbol_info_none"
        failed_fields.append("symbol_info")
    elif not select_ok:
        status = "failed_symbol_select"
        failed_fields.append("symbol_select")
    elif rows <= 0:
        status = "failed_no_recent_m15_rates"
        failed_fields.append("copy_rates_range_M15_last_7d")
    if tick is None:
        failed_fields.append("symbol_info_tick")
        if status == "verified_broker_symbol_with_recent_m15_rates":
            status = "failed_no_current_tick"
    return {
        "failed_fields": failed_fields,
        "file_symbol": file_symbol,
        "first_m15_utc": _rate_time(rates[0]) if rows else None,
        "last_error_after_rates": str(rates_error),
        "last_error_after_select": str(select_error),
        "last_m15_utc": _rate_time(rates[-1]) if rows else None,
        "mt5_symbol": mt5_symbol,
        "recent_m15_rows_7d": rows,
        "selected": select_ok,
        "status": status,
        "symbol_info": _info_payload(info),
        "symbol_info_before_select": _info_payload(before_info),
        "tick": _tick_payload(tick),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate existing proof without MT5 calls or writes")
    parser.add_argument("--yes-live-readonly", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expected = {file_symbol for file_symbol, _ in ALIASES}
        verified = set(payload.get("verified_aliases") or [])
        failed = list(payload.get("failed_aliases") or [])
        issues = []
        if payload.get("status") != "passed_all_aliases":
            issues.append(f"status:{payload.get('status')}")
        if verified != expected:
            issues.append(f"verified_aliases:{sorted(verified)}")
        if failed:
            issues.append(f"failed_aliases:{failed}")
        for row in payload.get("aliases") or []:
            if row.get("status") != "verified_broker_symbol_with_recent_m15_rates":
                issues.append(f"{row.get('file_symbol')}:status:{row.get('status')}")
            if int(row.get("recent_m15_rows_7d") or 0) <= 0:
                issues.append(f"{row.get('file_symbol')}:no_recent_rows")
            if not row.get("symbol_info") or not row.get("tick"):
                issues.append(f"{row.get('file_symbol')}:missing_symbol_info_or_tick")
        result = {
            "mode": "check",
            "output": str(OUTPUT),
            "issue_count": len(issues),
            "issues": issues,
            "status": "passed" if not issues else "failed",
            "verified_aliases": sorted(verified),
        }
        print(json.dumps(result, sort_keys=True))
        return 0 if not issues else 1

    import MetaTrader5 as mt5  # noqa: PLC0415

    if not mt5.initialize():
        payload = {
            "aliases": [],
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "initialize_error": str(mt5.last_error()),
            "read_only": True,
            "schema_version": "vnext_activation_repair_stage03_mt5_alias_verification_v1",
            "status": "failed_mt5_initialize",
        }
        OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "output": str(OUTPUT)}))
        return 2
    try:
        account = mt5.account_info()
        if account is None:
            raise RuntimeError(f"account_info_none:{mt5.last_error()}")
        live_account = account.trade_mode != 0
        if live_account and not args.yes_live_readonly:
            raise RuntimeError("live_account_requires_yes_live_readonly")
        aliases = [_probe_symbol(mt5, file_symbol, mt5_symbol) for file_symbol, mt5_symbol in ALIASES]
        verified = [
            row["file_symbol"]
            for row in aliases
            if row["status"] == "verified_broker_symbol_with_recent_m15_rates"
        ]
        failed = [row["file_symbol"] for row in aliases if row["file_symbol"] not in verified]
        payload = {
            "account": {
                "login": account.login,
                "server": account.server,
                "trade_mode": account.trade_mode,
                "live_account": live_account,
            },
            "aliases": aliases,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "failed_aliases": failed,
            "read_only": True,
            "schema_version": "vnext_activation_repair_stage03_mt5_alias_verification_v1",
            "status": "completed_with_failed_aliases" if failed else "passed_all_aliases",
            "verified_aliases": verified,
        }
        OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"failed": failed, "output": str(OUTPUT), "status": payload["status"], "verified": verified}))
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
