from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
sys.path.insert(0, str(REPO_ROOT))
DATE = "2026-05-27"
OUTPUT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE03_PRODUCTION_EXTRACTION_PROOF_{DATE}.json"
CONFIG_PATH = REPO_ROOT / "config" / "agent_config.yaml"
PROFILE = "redacted_account"
SYMBOLS = ("GER40", "UKOIL_cash", "USOIL_cash")
DEFAULT_RANGE_START = "2026-05-26T00:00:00+00:00"
DEFAULT_RANGE_END = "2026-05-27T00:00:00+00:00"


def _parse_dt(value: str) -> datetime:
    ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _first_last(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"first_utc": None, "last_utc": None, "rows": 0}
    return {
        "first_utc": rows[0].get("time"),
        "last_utc": rows[-1].get("time"),
        "rows": len(rows),
    }


def _rate_time(row: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(row["time"]), tz=timezone.utc).isoformat()
    except Exception:
        return None


def _direct_range_probe(api: Any, mt5_symbol: str, start: datetime, end: datetime) -> dict[str, Any]:
    rates = api.copy_rates_range(mt5_symbol, api.TIMEFRAME_M15, start, end)
    rows = 0 if rates is None else int(len(rates))
    return {
        "api": "MetaTrader5.copy_rates_range",
        "end_utc": end.isoformat(),
        "first_m15_utc": _rate_time(rates[0]) if rows else None,
        "last_error": str(api.last_error()),
        "last_m15_utc": _rate_time(rates[-1]) if rows else None,
        "rows": rows,
        "start_utc": start.isoformat(),
        "timeframe": "M15",
    }


def _load_effective_config(symbol: str) -> dict[str, Any]:
    from src.utils.config import apply_instrument_overrides, apply_profile_overrides

    base = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    profiled = apply_profile_overrides(base, PROFILE)
    return apply_instrument_overrides(profiled, symbol)


def _probe_symbol(mt5: Any, api: Any, symbol: str, start: datetime, end: datetime) -> dict[str, Any]:
    from src.components.data_ingestion import DataIncompleteError, ingest_live_data

    effective = _load_effective_config(symbol)
    market = effective.get("market", {})
    mt5_symbol = market.get("mt5_symbol") or market.get("symbol") or symbol
    raw_range = _direct_range_probe(api, mt5_symbol, start, end)
    row: dict[str, Any] = {
        "canonical_symbol": symbol,
        "mt5_symbol": mt5_symbol,
        "profile": PROFILE,
        "read_only": True,
        "direct_raw_requested_range_probe": raw_range,
        "production_extraction_api": "src.components.data_ingestion.ingest_live_data -> RealMT5.get_candles -> MetaTrader5.copy_rates_from_pos",
    }
    try:
        raw_data = ingest_live_data(mt5, effective)
    except DataIncompleteError as exc:
        row.update(
            {
                "status": "failed_production_ingest_data_incomplete",
                "error": str(exc),
            }
        )
        return row
    except Exception as exc:  # noqa: BLE001
        row.update(
            {
                "status": "failed_production_ingest_exception",
                "error": repr(exc),
            }
        )
        return row

    candles = raw_data.get("candles") or {}
    timeframe_rows = {
        tf: _first_last(list(candles.get(tf) or []))
        for tf in ("D1", "H4", "H1", "M15")
    }
    production_ok = all(
        timeframe_rows[tf]["rows"] > 0 for tf in ("D1", "H4", "H1", "M15")
    ) and bool(raw_data.get("data_quality", {}).get("all_timeframes_complete"))
    discrepancy_status = (
        "raw_requested_range_empty_but_production_copy_rates_from_pos_has_recent_bars"
        if raw_range["rows"] == 0 and timeframe_rows["M15"]["rows"] > 0
        else "raw_requested_range_and_production_path_both_have_rows"
        if raw_range["rows"] > 0 and timeframe_rows["M15"]["rows"] > 0
        else "production_path_unusable"
    )
    row.update(
        {
            "status": "passed_production_extraction_path" if production_ok else "failed_production_extraction_path",
            "timeframe_rows": timeframe_rows,
            "data_quality": raw_data.get("data_quality"),
            "spread_cents": raw_data.get("spread_cents"),
            "reconciliation_status": discrepancy_status,
        }
    )
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate existing proof without MT5 calls or writes")
    parser.add_argument("--yes-live-readonly", action="store_true")
    parser.add_argument("--range-start", default=DEFAULT_RANGE_START)
    parser.add_argument("--range-end", default=DEFAULT_RANGE_END)
    args = parser.parse_args(argv)

    if args.check:
        payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
        by_symbol = {row.get("canonical_symbol"): row for row in payload.get("symbols") or []}
        issues = []
        if payload.get("status") != "passed_all_production_extraction_paths":
            issues.append(f"status:{payload.get('status')}")
        if payload.get("failed_symbols"):
            issues.append(f"failed_symbols:{payload.get('failed_symbols')}")
        for symbol in SYMBOLS:
            row = by_symbol.get(symbol)
            if not row:
                issues.append(f"{symbol}:missing_symbol_row")
                continue
            if row.get("status") != "passed_production_extraction_path":
                issues.append(f"{symbol}:status:{row.get('status')}")
            if row.get("production_extraction_api") != (
                "src.components.data_ingestion.ingest_live_data -> RealMT5.get_candles -> MetaTrader5.copy_rates_from_pos"
            ):
                issues.append(f"{symbol}:not_exact_production_path")
            tf_rows = row.get("timeframe_rows") or {}
            for timeframe in ("D1", "H4", "H1", "M15"):
                if int((tf_rows.get(timeframe) or {}).get("rows") or 0) <= 0:
                    issues.append(f"{symbol}:{timeframe}:no_rows")
            if int((row.get("direct_raw_requested_range_probe") or {}).get("rows") or 0) <= 0:
                issues.append(f"{symbol}:raw_requested_range_no_rows")
            if row.get("reconciliation_status") == "production_path_unusable":
                issues.append(f"{symbol}:production_path_unusable")
        result = {
            "mode": "check",
            "output": str(OUTPUT),
            "issue_count": len(issues),
            "issues": issues,
            "status": "passed" if not issues else "failed",
            "symbols_checked": list(SYMBOLS),
        }
        print(json.dumps(result, sort_keys=True))
        return 0 if not issues else 1

    from src.mt5.mt5_real import RealMT5

    mt5 = RealMT5()
    if not mt5.connect():
        payload = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
            "schema_version": "vnext_activation_repair_stage03_production_extraction_proof_v1",
            "status": "failed_mt5_connect",
        }
        OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "output": str(OUTPUT)}))
        return 2

    try:
        api = mt5._mt5
        account = api.account_info()
        live_account = bool(account and account.trade_mode != 0)
        if live_account and not args.yes_live_readonly:
            raise RuntimeError("live_account_requires_yes_live_readonly")
        start = _parse_dt(args.range_start)
        end = _parse_dt(args.range_end)
        rows = [_probe_symbol(mt5, api, symbol, start, end) for symbol in SYMBOLS]
        failed = [row["canonical_symbol"] for row in rows if row["status"] != "passed_production_extraction_path"]
        payload = {
            "account": {
                "login": getattr(account, "login", None),
                "server": getattr(account, "server", None),
                "trade_mode": getattr(account, "trade_mode", None),
                "live_account": live_account,
            },
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "failed_symbols": failed,
            "read_only": True,
            "requested_raw_range": {
                "start_utc": start.isoformat(),
                "end_utc": end.isoformat(),
            },
            "schema_version": "vnext_activation_repair_stage03_production_extraction_proof_v1",
            "status": "passed_all_production_extraction_paths" if not failed else "completed_with_failed_symbols",
            "symbols": rows,
        }
        OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"failed": failed, "output": str(OUTPUT), "status": payload["status"]}))
        return 0 if not failed else 1
    finally:
        mt5.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
