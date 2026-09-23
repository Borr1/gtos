#!/usr/bin/env python3
"""Read-only dual MT5/account/symbol probe for the dual-broker supervisor.

The probe intentionally does not call ``symbol_select`` and never sends,
modifies, cancels, or closes broker orders. It verifies profile/account
identity, terminal paths, open broker state, and symbol existence while
preserving the memory-conscious FTMO follower design.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE_ID = "vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02"
EVIDENCE_CLASS = "DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
PROFILES = {
    "redacted_account": REPO_ROOT / "config" / "profiles" / "redacted_account.yaml",
    "operator_profile": REPO_ROOT / "config" / "profiles" / "operator_profile.yaml",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def snapshot(obj: Any) -> dict[str, Any] | None:
    if obj is None:
        return None
    if hasattr(obj, "_asdict"):
        return dict(obj._asdict())
    if isinstance(obj, dict):
        return dict(obj)
    return {
        name: getattr(obj, name)
        for name in dir(obj)
        if not name.startswith("_") and not callable(getattr(obj, name))
    }


def login_hash(account: dict[str, Any] | None) -> str | None:
    if not account or account.get("login") in (None, ""):
        return None
    return hashlib.sha256(str(account["login"]).encode("utf-8")).hexdigest()


def compact_account(account: dict[str, Any] | None) -> dict[str, Any] | None:
    if not account:
        return None
    return {
        "balance": account.get("balance"),
        "company": account.get("company"),
        "currency": account.get("currency"),
        "equity": account.get("equity"),
        "leverage": account.get("leverage"),
        "login_sha256": login_hash(account),
        "margin": account.get("margin"),
        "margin_free": account.get("margin_free"),
        "margin_level": account.get("margin_level"),
        "server": account.get("server"),
        "trade_allowed": account.get("trade_allowed"),
        "trade_expert": account.get("trade_expert"),
        "trade_mode": account.get("trade_mode"),
    }


def compact_terminal(terminal: dict[str, Any] | None) -> dict[str, Any] | None:
    if not terminal:
        return None
    return {
        "build": terminal.get("build"),
        "company": terminal.get("company"),
        "connected": terminal.get("connected"),
        "data_path": terminal.get("data_path"),
        "name": terminal.get("name"),
        "path": terminal.get("path"),
        "trade_allowed": terminal.get("trade_allowed"),
    }


def compact_position(position: dict[str, Any]) -> dict[str, Any]:
    return {
        "comment": position.get("comment"),
        "magic": position.get("magic"),
        "price_current": position.get("price_current"),
        "price_open": position.get("price_open"),
        "profit": position.get("profit"),
        "sl": position.get("sl"),
        "swap": position.get("swap"),
        "symbol": position.get("symbol"),
        "ticket": position.get("ticket"),
        "time": position.get("time"),
        "tp": position.get("tp"),
        "type": position.get("type"),
        "volume": position.get("volume"),
    }


def compact_order(order: dict[str, Any]) -> dict[str, Any]:
    return {
        "comment": order.get("comment"),
        "magic": order.get("magic"),
        "price_open": order.get("price_open"),
        "sl": order.get("sl"),
        "state": order.get("state"),
        "symbol": order.get("symbol"),
        "ticket": order.get("ticket"),
        "time_setup": order.get("time_setup"),
        "tp": order.get("tp"),
        "type": order.get("type"),
        "volume_current": order.get("volume_current"),
        "volume_initial": order.get("volume_initial"),
    }


def tick_quality(tick: dict[str, Any] | None) -> str:
    if not tick:
        return "absent_without_mass_symbol_select"
    bid = tick.get("bid")
    ask = tick.get("ask")
    try:
        bid_f = float(bid)
        ask_f = float(ask)
    except (TypeError, ValueError):
        return "invalid_quote"
    if bid_f <= 0 or ask_f <= 0 or ask_f < bid_f:
        return "invalid_quote"
    return "positive_quote"


def symbol_checks(mt5_module: Any, profile: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for logical_symbol, spec in sorted((profile.get("instruments") or {}).items()):
        market = spec.get("market") or {}
        mt5_symbol = market.get("mt5_symbol") or logical_symbol
        info = snapshot(mt5_module.symbol_info(mt5_symbol))
        tick = snapshot(mt5_module.symbol_info_tick(mt5_symbol))
        rows.append(
            {
                "logical_symbol": logical_symbol,
                "mt5_symbol": mt5_symbol,
                "profile_trade_mode": market.get("trade_mode"),
                "profile_volume_min": market.get("volume_min"),
                "profile_volume_max": market.get("volume_max"),
                "profile_volume_step": market.get("volume_step"),
                "symbol_info_found": info is not None,
                "terminal_visible": None if info is None else info.get("visible"),
                "terminal_select": None if info is None else info.get("select"),
                "terminal_trade_mode": None if info is None else info.get("trade_mode"),
                "terminal_volume_min": None if info is None else info.get("volume_min"),
                "terminal_volume_max": None if info is None else info.get("volume_max"),
                "terminal_volume_step": None if info is None else info.get("volume_step"),
                "tick_quality_without_mass_select": tick_quality(tick),
                "tick_time": None if tick is None else tick.get("time"),
                "tick_time_msc": None if tick is None else tick.get("time_msc"),
            }
        )
    return rows


def account_matches(profile: dict[str, Any], account: dict[str, Any] | None, terminal: dict[str, Any] | None) -> dict[str, bool]:
    expected = ((profile.get("broker_profile") or {}).get("expected_account") or {})
    actual_account = compact_account(account)
    actual_terminal = compact_terminal(terminal)
    return {
        "company": bool(actual_account and actual_account.get("company") == expected.get("company")),
        "currency": bool(actual_account and actual_account.get("currency") == expected.get("currency")),
        "login_sha256": bool(actual_account and actual_account.get("login_sha256") == expected.get("login_sha256")),
        "server": bool(actual_account and actual_account.get("server") == expected.get("server")),
        "terminal_data_path": bool(actual_terminal and actual_terminal.get("data_path") == expected.get("terminal_data_path")),
        "terminal_path_prefix": bool(
            actual_terminal
            and expected.get("terminal_path")
            and str(actual_terminal.get("path") or "").lower().startswith(str(expected.get("terminal_path")).lower())
        ),
    }


def probe_profile(label: str, profile_path: Path, mt5_module: Any) -> dict[str, Any]:
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    mt5_cfg = profile.get("mt5") or {}
    terminal_path = str(mt5_cfg.get("terminal_path") or "")
    portable = bool(mt5_cfg.get("portable", False))
    result: dict[str, Any] = {
        "captured_at_utc": utc_now(),
        "label": label,
        "no_symbol_select_called": True,
        "path_exists": Path(terminal_path).exists(),
        "profile_name": profile.get("profile_name"),
        "profile_path": str(profile_path.relative_to(REPO_ROOT)),
        "requested_terminal_path": terminal_path,
        "requested_portable": portable,
        "runtime_namespace": (profile.get("runtime") or {}).get("broker_account_namespace")
        or (profile.get("runtime") or {}).get("profile_namespace"),
        "schema_version": "dual_readonly_mt5_profile_probe_v1",
    }
    init_kwargs: dict[str, Any] = {"path": terminal_path} if terminal_path else {}
    if portable:
        init_kwargs["portable"] = True
    initialized = bool(mt5_module.initialize(**init_kwargs))
    result["initialize_ok"] = initialized
    result["last_error"] = mt5_module.last_error()
    if not initialized:
        return result
    try:
        terminal = snapshot(mt5_module.terminal_info())
        account = snapshot(mt5_module.account_info())
        positions = [snapshot(row) for row in (mt5_module.positions_get() or [])]
        orders = [snapshot(row) for row in (mt5_module.orders_get() or [])]
        positions = [row for row in positions if row]
        orders = [row for row in orders if row]
        symbols = symbol_checks(mt5_module, profile)
        result.update(
            {
                "terminal_info": compact_terminal(terminal),
                "account_info": compact_account(account),
                "account_match": account_matches(profile, account, terminal),
                "account_match_all": all(account_matches(profile, account, terminal).values()),
                "positions_total": len(positions),
                "orders_total": len(orders),
                "positions": [compact_position(row) for row in positions],
                "orders": [compact_order(row) for row in orders],
                "symbol_check_summary": {
                    "configured_symbols": len(symbols),
                    "symbol_info_found": sum(1 for row in symbols if row["symbol_info_found"]),
                    "positive_ticks_without_mass_select": sum(
                        1 for row in symbols if row["tick_quality_without_mass_select"] == "positive_quote"
                    ),
                    "absent_ticks_without_mass_select": sum(
                        1 for row in symbols if row["tick_quality_without_mass_select"] == "absent_without_mass_symbol_select"
                    ),
                    "invalid_ticks_without_mass_select": sum(
                        1 for row in symbols if row["tick_quality_without_mass_select"] == "invalid_quote"
                    ),
                    "unselected_symbols": sum(1 for row in symbols if row["terminal_select"] is False),
                },
                "symbol_checks": symbols,
            }
        )
    finally:
        mt5_module.shutdown()
    return result


def ledger_base(recorded_at: str) -> dict[str, Any]:
    return {
        "evidence_class": EVIDENCE_CLASS,
        "recorded_at_utc": recorded_at,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": "read_only_mt5_account_terminal_position_order_symbol_inspection_no_symbol_select_no_broker_mutation",
    }


def write_ledgers(payload: dict[str, Any]) -> None:
    recorded_at = payload["recorded_at_utc"]
    base = ledger_base(recorded_at)
    probes = payload["probes"]
    append_jsonl(
        ROUTE_DIR / "DUAL_ACCOUNT_PROFILE_LEDGER.jsonl",
        {
            **base,
            "artifact": "DUAL_ACCOUNT_PROFILE_LEDGER.jsonl",
            "status": "dual_profile_account_identity_checked",
            "profiles": {
                name: {
                    "account_match": probe.get("account_match"),
                    "account_match_all": probe.get("account_match_all"),
                    "profile_path": probe.get("profile_path"),
                    "requested_terminal_path": probe.get("requested_terminal_path"),
                    "runtime_namespace": probe.get("runtime_namespace"),
                }
                for name, probe in probes.items()
            },
        },
    )
    append_jsonl(
        ROUTE_DIR / "DUAL_MT5_SYMBOL_SPEC_LEDGER.jsonl",
        {
            **base,
            "artifact": "DUAL_MT5_SYMBOL_SPEC_LEDGER.jsonl",
            "status": "dual_symbol_specs_checked_without_mass_symbol_select",
            "symbol_check_summary": {
                name: probe.get("symbol_check_summary") for name, probe in probes.items()
            },
        },
    )
    append_jsonl(
        ROUTE_DIR / "DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl",
        {
            **base,
            "artifact": "DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl",
            "status": "dual_open_positions_orders_read_only_checked",
            "positions_total": {name: probe.get("positions_total") for name, probe in probes.items()},
            "orders_total": {name: probe.get("orders_total") for name, probe in probes.items()},
            "positions": {name: probe.get("positions", []) for name, probe in probes.items()},
            "broker_mutation_status": "none",
        },
    )
    append_jsonl(
        ROUTE_DIR / "DUAL_BROKER_RECONCILIATION_LEDGER.jsonl",
        {
            **base,
            "artifact": "DUAL_BROKER_RECONCILIATION_LEDGER.jsonl",
            "status": "dual_broker_read_only_reconciliation_checkpoint",
            "account_match_all": {name: probe.get("account_match_all") for name, probe in probes.items()},
            "positions_total": {name: probe.get("positions_total") for name, probe in probes.items()},
            "orders_total": {name: probe.get("orders_total") for name, probe in probes.items()},
            "broker_mutation_status": "none",
        },
    )
    append_jsonl(
        ROUTE_DIR / "DUAL_RISK_EXPOSURE_LEDGER.jsonl",
        {
            **base,
            "artifact": "DUAL_RISK_EXPOSURE_LEDGER.jsonl",
            "status": "dual_account_equity_margin_exposure_read_only_checked",
            "accounts": {
                name: {
                    "balance": (probe.get("account_info") or {}).get("balance"),
                    "equity": (probe.get("account_info") or {}).get("equity"),
                    "margin": (probe.get("account_info") or {}).get("margin"),
                    "margin_free": (probe.get("account_info") or {}).get("margin_free"),
                    "positions_total": probe.get("positions_total"),
                    "orders_total": probe.get("orders_total"),
                }
                for name, probe in probes.items()
            },
        },
    )
    append_jsonl(
        ROUTE_DIR / "DUAL_SUPERVISOR_ACTION_LEDGER.jsonl",
        {
            **base,
            "action": "recorded_dual_mt5_readonly_probe",
            "artifact": "DUAL_SUPERVISOR_ACTION_LEDGER.jsonl",
            "status": "completed",
        },
    )


def main() -> int:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "FAILED", "error": f"import_failed:{exc!r}"}, indent=2), file=sys.stderr)
        return 2

    recorded_at = utc_now()
    probes = {name: probe_profile(name, path, mt5) for name, path in PROFILES.items()}
    payload = {
        "account_probe_status": "performed_read_only_current_post_reboot",
        "broker_mutation_status": "none",
        "evidence_class": EVIDENCE_CLASS,
        "probes": probes,
        "recorded_at_utc": recorded_at,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": "read_only_mt5_account_terminal_position_order_symbol_inspection_no_symbol_select_no_broker_mutation",
        "schema_version": "dual_mt5_terminal_account_probe_v1",
        "status": "passed"
        if all(probe.get("initialize_ok") and probe.get("account_match_all") for probe in probes.values())
        else "issues_detected",
    }
    write_json(ROUTE_DIR / "DUAL_MT5_TERMINAL_ACCOUNT_PROBE.json", payload)
    write_ledgers(payload)
    print(json.dumps(
        {
            "account_probe_status": payload["account_probe_status"],
            "positions_total": {name: probe.get("positions_total") for name, probe in probes.items()},
            "orders_total": {name: probe.get("orders_total") for name, probe in probes.items()},
            "status": payload["status"],
            "symbol_check_summary": {
                name: probe.get("symbol_check_summary") for name, probe in probes.items()
            },
        },
        indent=2,
        sort_keys=True,
    ))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
