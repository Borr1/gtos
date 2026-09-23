#!/usr/bin/env python3
"""Audit active broker profiles against direct MT5 symbol metadata.

This verifier is read-only. It calls MT5 account/terminal/symbol/tick getters
only, never ``symbol_select`` and never order/account mutation methods.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.verify_broker_profile import (  # noqa: E402
    redacted_account_KNOWN_UNSUPPORTED_ACTIVE_SYMBOLS,
    active_ultimate_book_symbols,
)
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.utils.config import apply_profile_overrides, resolve_instrument_config_key  # noqa: E402


SCHEMA_VERSION = "broker_profile_market_detail_audit_v1"
ACTIVE_BRANCH = "vps/ultimate-conditioned-expansion-minimal-2026-06-18"
DEFAULT_AGENT_CONFIG = Path("config/agent_config.yaml")
DEFAULT_PROFILES = (
    "operator_profile",
    "redacted_account",
)

MT5_SYMBOL_FIELDS = (
    "name",
    "path",
    "description",
    "visible",
    "select",
    "custom",
    "digits",
    "point",
    "spread",
    "spread_float",
    "trade_mode",
    "trade_calc_mode",
    "trade_exemode",
    "trade_stops_level",
    "trade_freeze_level",
    "trade_contract_size",
    "trade_tick_size",
    "trade_tick_value",
    "trade_tick_value_profit",
    "trade_tick_value_loss",
    "volume_min",
    "volume_max",
    "volume_step",
    "volume_limit",
    "swap_mode",
    "swap_long",
    "swap_short",
    "swap_rollover3days",
    "margin_initial",
    "margin_maintenance",
    "margin_hedged",
    "currency_base",
    "currency_profit",
    "currency_margin",
    "order_mode",
    "filling_mode",
    "expiration_mode",
    "start_time",
    "expiration_time",
)
MT5_TICK_FIELDS = (
    "time",
    "time_msc",
    "bid",
    "ask",
    "last",
    "volume",
    "volume_real",
    "flags",
)

HARD_PROFILE_FIELDS = (
    "mt5_symbol",
    "point",
    "digits",
    "trade_tick_size",
    "trade_tick_value",
    "contract_size",
    "volume_min",
    "volume_max",
    "volume_step",
    "trade_stops_level",
    "trade_freeze_level",
)
HARD_LIVE_FIELDS = (
    "point",
    "digits",
    "trade_tick_size",
    "trade_tick_value",
    "trade_contract_size",
    "volume_min",
    "volume_max",
    "volume_step",
    "trade_stops_level",
    "trade_freeze_level",
    "trade_mode",
)
STATIC_COMPARE_FIELDS = (
    ("digits", ("digits",), ("digits",), "exact"),
    ("point", ("point",), ("point",), "float_exact"),
    ("trade_tick_size", ("trade_tick_size", "tick_size"), ("trade_tick_size",), "float_exact"),
    ("contract_size", ("trade_contract_size", "contract_size"), ("trade_contract_size",), "float_exact"),
    ("volume_min", ("volume_min",), ("volume_min",), "float_exact"),
    ("volume_max", ("volume_max",), ("volume_max",), "float_exact"),
    ("volume_step", ("volume_step",), ("volume_step",), "float_exact"),
    ("trade_stops_level", ("trade_stops_level",), ("trade_stops_level",), "float_exact"),
    ("trade_freeze_level", ("trade_freeze_level",), ("trade_freeze_level",), "float_exact"),
    ("trade_mode", ("trade_mode",), ("trade_mode",), "exact"),
)
DRIFT_COMPARE_FIELDS = (
    ("trade_tick_value", ("trade_tick_value",), ("trade_tick_value",), 0.25),
    ("swap_long", ("swap_long",), ("swap_long",), 0.20),
    ("swap_short", ("swap_short",), ("swap_short",), 0.20),
)
OPTIONAL_PROFILE_FIELDS = (
    "trade_contract_size",
    "trade_tick_value_profit",
    "trade_tick_value_loss",
    "swap_mode",
    "swap_rollover3days",
    "currency_base",
    "currency_profit",
    "currency_margin",
    "spread_float",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def snapshot(obj: Any, fields: tuple[str, ...] | None = None) -> dict[str, Any] | None:
    if obj is None:
        return None
    if hasattr(obj, "_asdict"):
        raw = dict(obj._asdict())
    elif isinstance(obj, dict):
        raw = dict(obj)
    elif hasattr(obj, "__dict__"):
        raw = {
            name: value
            for name, value in vars(obj).items()
            if not str(name).startswith("_")
        }
    else:
        raw = {
            name: getattr(obj, name)
            for name in dir(obj)
            if not str(name).startswith("_") and not callable(getattr(obj, name))
        }
    if fields is None:
        return raw
    return {field: raw.get(field) for field in fields if field in raw}


def sha256_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def first_present(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return None


def numeric_equal(left: Any, right: Any, *, rel_tol: float = 1e-9, abs_tol: float = 1e-9) -> bool:
    left_n = number(left)
    right_n = number(right)
    if left_n is None or right_n is None:
        return left == right
    return math.isclose(left_n, right_n, rel_tol=rel_tol, abs_tol=abs_tol)


def relative_delta(left: Any, right: Any) -> float | None:
    left_n = number(left)
    right_n = number(right)
    if left_n is None or right_n is None:
        return None
    denom = max(abs(right_n), 1e-12)
    return abs(left_n - right_n) / denom


def compact_account(account: dict[str, Any] | None) -> dict[str, Any] | None:
    if not account:
        return None
    return {
        "balance": account.get("balance"),
        "equity": account.get("equity"),
        "profit": account.get("profit"),
        "currency": account.get("currency"),
        "server": account.get("server"),
        "company": account.get("company"),
        "trade_allowed": account.get("trade_allowed"),
        "trade_expert": account.get("trade_expert"),
        "login_sha256": sha256_text(account.get("login")),
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


def profile_account_comparisons(
    profile: dict[str, Any],
    account: dict[str, Any] | None,
    terminal: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, bool]]:
    expected = ((profile.get("broker_profile") or {}).get("expected_account") or {})
    actual_account = compact_account(account)
    actual_terminal = compact_terminal(terminal)
    actual = {
        "server": (actual_account or {}).get("server"),
        "company": (actual_account or {}).get("company"),
        "currency": (actual_account or {}).get("currency"),
        "login_sha256": (actual_account or {}).get("login_sha256"),
        "terminal_data_path": (actual_terminal or {}).get("data_path"),
        "terminal_path": (actual_terminal or {}).get("path"),
    }
    flags: dict[str, bool] = {}
    issues: list[dict[str, Any]] = []
    for field, expected_value in expected.items():
        if field not in actual or expected_value in (None, ""):
            continue
        actual_value = actual.get(field)
        if field == "terminal_path":
            ok = str(actual_value or "").lower().startswith(str(expected_value).lower())
        else:
            ok = str(actual_value) == str(expected_value)
        flags[field] = ok
        if not ok:
            issues.append(
                {
                    "code": "account_profile_mismatch",
                    "field": field,
                    "expected": expected_value,
                    "actual": actual_value,
                }
            )
    return issues, flags


def issue(code: str, **fields: Any) -> dict[str, Any]:
    return {"code": code, **fields}


def profile_market_for_symbol(profile: dict[str, Any], symbol: str) -> tuple[str | None, dict[str, Any]]:
    inst_key = resolve_instrument_config_key(profile, symbol)
    if not inst_key:
        return None, {}
    row = (profile.get("instruments") or {}).get(inst_key) or {}
    market = row.get("market") if isinstance(row, dict) else {}
    return inst_key, dict(market or {})


def audit_symbol(
    *,
    profile_name: str,
    profile: dict[str, Any],
    symbol: str,
    resolver: Any,
    mt5_module: Any,
    allowed_missing: set[str],
) -> dict[str, Any]:
    supported = bool(getattr(resolver, "supports", lambda value: True)(symbol))
    inst_key, market = profile_market_for_symbol(profile, symbol)
    broker_symbol = resolver(symbol) if supported else None
    symbol_info = None
    tick_info = None
    row_issues: list[dict[str, Any]] = []
    row_warnings: list[dict[str, Any]] = []

    if not supported:
        status = "unsupported_allowed" if symbol in allowed_missing else "unsupported_unexpected"
        if symbol not in allowed_missing:
            row_issues.append(issue("unsupported_active_symbol_unexpected", symbol=symbol))
        return {
            "symbol": symbol,
            "instrument_key": inst_key,
            "broker_symbol": broker_symbol,
            "supported": False,
            "status": status,
            "issues": row_issues,
            "warnings": row_warnings,
        }

    for field in HARD_PROFILE_FIELDS:
        if field not in market or market.get(field) in (None, ""):
            row_issues.append(issue("missing_required_profile_market_field", symbol=symbol, field=field))

    if market.get("mt5_symbol") and broker_symbol and str(market["mt5_symbol"]) != str(broker_symbol):
        row_issues.append(
            issue(
                "profile_resolver_symbol_mismatch",
                symbol=symbol,
                instrument_key=inst_key,
                profile_mt5_symbol=market.get("mt5_symbol"),
                resolver_broker_symbol=broker_symbol,
            )
        )

    try:
        symbol_info = snapshot(mt5_module.symbol_info(str(broker_symbol)), MT5_SYMBOL_FIELDS)
        tick_info = snapshot(mt5_module.symbol_info_tick(str(broker_symbol)), MT5_TICK_FIELDS)
    except Exception as exc:  # noqa: BLE001
        row_issues.append(
            issue("mt5_symbol_probe_exception", symbol=symbol, broker_symbol=broker_symbol, error=repr(exc))
        )

    if symbol_info is None:
        row_issues.append(issue("mt5_symbol_info_missing", symbol=symbol, broker_symbol=broker_symbol))
    else:
        for field in HARD_LIVE_FIELDS:
            if symbol_info.get(field) in (None, ""):
                row_issues.append(issue("missing_required_live_symbol_field", symbol=symbol, field=field))
        if number(symbol_info.get("trade_mode")) != 4.0:
            row_issues.append(
                issue(
                    "live_symbol_not_full_trade_mode",
                    symbol=symbol,
                    broker_symbol=broker_symbol,
                    trade_mode=symbol_info.get("trade_mode"),
                )
            )
        if symbol_info.get("visible") is False:
            row_warnings.append(
                issue("live_symbol_not_visible_without_symbol_select", symbol=symbol, broker_symbol=broker_symbol)
            )

        for label, profile_names, live_names, compare_mode in STATIC_COMPARE_FIELDS:
            profile_value = first_present(market, profile_names)
            live_value = first_present(symbol_info, live_names)
            if profile_value in (None, "") or live_value in (None, ""):
                continue
            if compare_mode == "exact":
                ok = str(profile_value) == str(live_value)
            else:
                ok = numeric_equal(profile_value, live_value)
            if not ok:
                row_issues.append(
                    issue(
                        "profile_live_static_field_mismatch",
                        symbol=symbol,
                        broker_symbol=broker_symbol,
                        field=label,
                        profile_value=profile_value,
                        live_value=live_value,
                    )
                )

        for label, profile_names, live_names, threshold in DRIFT_COMPARE_FIELDS:
            profile_value = first_present(market, profile_names)
            live_value = first_present(symbol_info, live_names)
            if profile_value in (None, "") or live_value in (None, ""):
                continue
            delta = relative_delta(profile_value, live_value)
            if delta is not None and delta > threshold:
                row_warnings.append(
                    issue(
                        "profile_live_drift_warning",
                        symbol=symbol,
                        broker_symbol=broker_symbol,
                        field=label,
                        profile_value=profile_value,
                        live_value=live_value,
                        relative_delta=round(delta, 6),
                        threshold=threshold,
                    )
                )

        for field in OPTIONAL_PROFILE_FIELDS:
            if market.get(field) in (None, "") and symbol_info.get(field) not in (None, ""):
                row_warnings.append(
                    issue(
                        "profile_missing_live_available_optional_field",
                        symbol=symbol,
                        broker_symbol=broker_symbol,
                        field=field,
                        live_value=symbol_info.get(field),
                    )
                )

    tick_quality = "not_checked"
    if tick_info is None:
        tick_quality = "absent_without_symbol_select"
    else:
        bid = number(tick_info.get("bid"))
        ask = number(tick_info.get("ask"))
        if bid is not None and ask is not None and bid > 0 and ask >= bid:
            tick_quality = "positive_quote"
        else:
            tick_quality = "invalid_quote"
            row_warnings.append(
                issue("live_tick_invalid_or_closed_market", symbol=symbol, broker_symbol=broker_symbol)
            )

    status = "ok" if not row_issues else "issues"
    return {
        "symbol": symbol,
        "instrument_key": inst_key,
        "broker_symbol": broker_symbol,
        "supported": True,
        "status": status,
        "profile_market": market,
        "live_symbol_info": symbol_info,
        "live_tick": tick_info,
        "tick_quality_without_symbol_select": tick_quality,
        "issues": row_issues,
        "warnings": row_warnings,
    }


def audit_profile(
    *,
    profile_name: str,
    profile: dict[str, Any],
    config: dict[str, Any],
    symbols: tuple[str, ...],
    mt5_module: Any,
) -> dict[str, Any]:
    cfg = apply_profile_overrides(dict(config), profile_name)
    resolver = build_broker_symbol_resolver(cfg)
    allowed_missing = (
        set(redacted_account_KNOWN_UNSUPPORTED_ACTIVE_SYMBOLS)
        if str(profile.get("profile_name") or profile_name).lower() == "redacted_account"
        else set()
    )
    mt5_cfg = profile.get("mt5") or {}
    terminal_path = str(mt5_cfg.get("terminal_path") or "")
    init_kwargs: dict[str, Any] = {"path": terminal_path} if terminal_path else {}
    if bool(mt5_cfg.get("portable", False)):
        init_kwargs["portable"] = True

    result: dict[str, Any] = {
        "profile_name": profile_name,
        "profile_file_profile_name": profile.get("profile_name"),
        "terminal_path": terminal_path,
        "terminal_path_exists": Path(terminal_path).exists() if terminal_path else False,
        "allowed_missing_symbols": sorted(allowed_missing),
        "initialize_ok": False,
        "last_error": None,
        "account": None,
        "terminal": None,
        "account_match": {},
        "symbols": [],
        "issues": [],
        "warnings": [],
    }
    initialized = bool(mt5_module.initialize(**init_kwargs))
    result["initialize_ok"] = initialized
    result["last_error"] = mt5_module.last_error()
    if not initialized:
        result["issues"].append(
            issue("mt5_initialize_failed", profile=profile_name, terminal_path=terminal_path, error=result["last_error"])
        )
        return finalize_profile_result(result)

    try:
        terminal = snapshot(mt5_module.terminal_info())
        account = snapshot(mt5_module.account_info())
        result["account"] = compact_account(account)
        result["terminal"] = compact_terminal(terminal)
        account_issues, account_match = profile_account_comparisons(profile, account, terminal)
        result["account_match"] = account_match
        result["issues"].extend(account_issues)
        for symbol in symbols:
            row = audit_symbol(
                profile_name=profile_name,
                profile=cfg,
                symbol=symbol,
                resolver=resolver,
                mt5_module=mt5_module,
                allowed_missing=allowed_missing,
            )
            result["symbols"].append(row)
            result["issues"].extend(row.get("issues") or [])
            result["warnings"].extend(row.get("warnings") or [])
    finally:
        mt5_module.shutdown()
    return finalize_profile_result(result)


def finalize_profile_result(result: dict[str, Any]) -> dict[str, Any]:
    symbols = result.get("symbols") or []
    supported = [row for row in symbols if row.get("supported")]
    unsupported = [row for row in symbols if not row.get("supported")]
    result["summary"] = {
        "active_symbol_count": len(symbols),
        "supported_symbol_count": len(supported),
        "unsupported_symbol_count": len(unsupported),
        "unsupported_symbols": sorted(row["symbol"] for row in unsupported),
        "unexpected_unsupported_symbols": sorted(
            row["symbol"] for row in unsupported if row.get("status") == "unsupported_unexpected"
        ),
        "mt5_symbol_info_missing_count": sum(
            1 for row in supported for item in (row.get("issues") or []) if item.get("code") == "mt5_symbol_info_missing"
        ),
        "positive_tick_count": sum(
            1 for row in supported if row.get("tick_quality_without_symbol_select") == "positive_quote"
        ),
        "absent_tick_count": sum(
            1 for row in supported if row.get("tick_quality_without_symbol_select") == "absent_without_symbol_select"
        ),
        "invalid_tick_count": sum(
            1 for row in supported if row.get("tick_quality_without_symbol_select") == "invalid_quote"
        ),
        "issue_count": len(result.get("issues") or []),
        "warning_count": len(result.get("warnings") or []),
    }
    result["ok"] = not bool(result.get("issues"))
    return result


def build_report(
    *,
    agent_config_path: Path,
    profile_names: tuple[str, ...],
    mt5_module: Any,
) -> dict[str, Any]:
    config = yaml.safe_load(agent_config_path.read_text(encoding="utf-8")) or {}
    symbols = active_ultimate_book_symbols(agent_config_path)
    profiles: dict[str, Any] = {}
    for profile_name in profile_names:
        profile_path = REPO_ROOT / "config" / "profiles" / f"{profile_name}.yaml"
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        profiles[profile_name] = audit_profile(
            profile_name=profile_name,
            profile=profile,
            config=config,
            symbols=symbols,
            mt5_module=mt5_module,
        )
    all_issues = [
        {"profile": profile_name, **item}
        for profile_name, result in profiles.items()
        for item in (result.get("issues") or [])
    ]
    all_warnings = [
        {"profile": profile_name, **item}
        for profile_name, result in profiles.items()
        for item in (result.get("warnings") or [])
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "branch": ACTIVE_BRANCH,
        "agent_config": str(agent_config_path),
        "runtime_effect_boundary": (
            "read_only_mt5_account_terminal_symbol_tick_inspection_no_symbol_select_no_broker_mutation"
        ),
        "active_symbol_count": len(symbols),
        "active_symbols": list(symbols),
        "profile_names": list(profile_names),
        "profiles": profiles,
        "ok": not all_issues,
        "issue_count": len(all_issues),
        "warning_count": len(all_warnings),
        "issues": all_issues,
        "warnings": all_warnings,
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# VPS Broker Profile Market Detail Audit",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        f"Branch: `{report['branch']}`",
        f"Runtime effect boundary: `{report['runtime_effect_boundary']}`",
        "",
        f"Overall ok: `{str(report['ok']).lower()}`",
        f"Issue count: `{report['issue_count']}`",
        f"Warning count: `{report['warning_count']}`",
        f"Active canonical symbols: `{report['active_symbol_count']}`",
        "",
        "## Profile Summary",
        "",
        "| Profile | Init | Supported | Unsupported | Positive ticks | Missing symbol_info | Issues | Warnings |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile_name, result in report["profiles"].items():
        summary = result.get("summary") or {}
        lines.append(
            "| {profile} | {init} | {supported} | {unsupported} | {ticks} | {missing} | {issues} | {warnings} |".format(
                profile=profile_name,
                init=str(result.get("initialize_ok")).lower(),
                supported=summary.get("supported_symbol_count"),
                unsupported=summary.get("unsupported_symbol_count"),
                ticks=summary.get("positive_tick_count"),
                missing=summary.get("mt5_symbol_info_missing_count"),
                issues=summary.get("issue_count"),
                warnings=summary.get("warning_count"),
            )
        )
    lines.extend(["", "## Unsupported Symbols", ""])
    for profile_name, result in report["profiles"].items():
        summary = result.get("summary") or {}
        unsupported = summary.get("unsupported_symbols") or []
        unexpected = summary.get("unexpected_unsupported_symbols") or []
        lines.append(f"- `{profile_name}` unsupported: `{', '.join(unsupported) if unsupported else 'none'}`")
        lines.append(f"- `{profile_name}` unexpected unsupported: `{', '.join(unexpected) if unexpected else 'none'}`")
    lines.extend(["", "## Issues", ""])
    if report["issues"]:
        for item in report["issues"]:
            fields = ", ".join(f"{key}={value!r}" for key, value in item.items() if key != "code")
            lines.append(f"- `{item['code']}`: {fields}")
    else:
        lines.append("- `none`")
    lines.extend(["", "## Warning Classes", ""])
    counts: dict[str, int] = {}
    for item in report["warnings"]:
        counts[str(item.get("code"))] = counts.get(str(item.get("code")), 0) + 1
    if counts:
        for code, count in sorted(counts.items()):
            lines.append(f"- `{code}`: `{count}`")
    else:
        lines.append("- `none`")
    lines.extend(["", "## Interpretation", ""])
    lines.append(
        "- Hard issues mean a supported active symbol, account identity, or static symbol field does not match current direct MT5 truth."
    )
    lines.append(
        "- Warnings preserve drift or optional metadata gaps. Live spread, tick value, and swap can move; warnings are review inputs, not automatic runtime blockers."
    )
    lines.append(
        "- This audit intentionally does not call `symbol_select`; absent or invalid ticks can reflect closed-market visibility rather than a profile defect."
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-config", type=Path, default=DEFAULT_AGENT_CONFIG)
    parser.add_argument("--profile", action="append", dest="profiles", default=[])
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": f"MetaTrader5 import failed: {exc!r}"}, indent=2), file=sys.stderr)
        return 2
    profile_names = tuple(args.profiles or DEFAULT_PROFILES)
    report = build_report(
        agent_config_path=args.agent_config,
        profile_names=profile_names,
        mt5_module=mt5,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("ok", "issue_count", "warning_count", "active_symbol_count")}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
