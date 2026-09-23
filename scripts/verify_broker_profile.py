#!/usr/bin/env python3
"""Verify a broker profile has account-specific symbol geometry.

The script is offline and read-only. It never connects to MT5; it checks that a
generated profile cannot silently omit active aliases or risk/lot geometry.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.config import resolve_instrument_config_key


VNEXT_24_SYMBOLS = (
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
)

REQUIRED_MARKET_FIELDS = (
    "mt5_symbol",
    "tick_size",
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

redacted_account_ALIAS_LEAKS = {
    "NAS100": {"NDX100"},
    "GER40": {"GER30"},
    "UKOIL_cash": {"UKOUSD"},
    "USOIL_cash": {"USOUSD"},
    "SPX500": {"SPX500"},
    "JP225": {"JP225"},
    "UK100": {"UK100"},
    "US30_cash": {"US30"},
}

redacted_account_KNOWN_UNSUPPORTED_ACTIVE_SYMBOLS = (
    "AVAUSD",
    "CORN_c",
    "COTTON_c",
    "DASHUSD",
    "XAGAUD",
    "XAGEUR",
    "XAUAUD",
    "XAUEUR",
    "XPDUSD",
    "XTZUSD",
)


def active_ultimate_book_symbols(agent_config_path: Path = Path("config/agent_config.yaml")) -> tuple[str, ...]:
    """Return the current configured ultimate-book canonical symbol universe.

    This is intentionally opt-in for the verifier. Older V3/VPS routes still use
    the 24-symbol production surface, while the current W7/candidate/market
    expansion package needs the effective active_specs() surface.
    """
    from src.components.ultimate_book.admission import resolve_market_expansion_sleeves
    from src.components.ultimate_book.sleeves.registry import active_specs

    config = yaml.safe_load(agent_config_path.read_text(encoding="utf-8")) or {}
    runtime = config.get("gtos_vnext_runtime", {}) or {}
    expansion_sleeves, error = resolve_market_expansion_sleeves(
        policy=runtime.get("ultimate_book_market_expansion_policy", "explicit_allowlist"),
        explicit_sleeves=runtime.get("ultimate_book_market_expansion_sleeves") or [],
    )
    if error:
        raise ValueError(f"invalid ultimate-book market expansion policy: {error}")
    specs = active_specs(
        None,
        include_candidate_book=bool(runtime.get("ultimate_book_include_candidate_book", False)),
        candidate_book_sleeves=runtime.get("ultimate_book_candidate_book_sleeves") or None,
        include_market_expansion_book=bool(runtime.get("ultimate_book_include_market_expansion_book", False)),
        market_expansion_sleeves=expansion_sleeves or None,
    )
    return tuple(sorted({symbol for spec in specs for symbol in (spec.on_surface or [])}))


def _as_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def verify_profile(
    profile_path: Path,
    *,
    symbols: tuple[str, ...] = VNEXT_24_SYMBOLS,
    surface: str = "vnext24",
    allowed_missing_symbols: tuple[str, ...] = (),
    allow_duplicate_broker_aliases: bool = False,
) -> dict[str, Any]:
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    instruments = profile.get("instruments")
    issues: list[dict[str, Any]] = []
    allowed_missing = set(allowed_missing_symbols)
    observed_allowed_missing: list[str] = []

    if not isinstance(instruments, dict):
        issues.append({"code": "missing_instruments_mapping"})
        instruments = {}

    expected = (
        profile.get("broker_profile", {}).get("expected_account", {})
        if isinstance(profile.get("broker_profile"), dict)
        else {}
    )
    for field in ("server", "company", "currency", "login_sha256", "terminal_path", "terminal_data_path"):
        if not expected.get(field):
            issues.append({"code": "missing_expected_account_field", "field": field})

    mt5_config = profile.get("mt5") if isinstance(profile.get("mt5"), dict) else {}
    for field in ("terminal_path", "terminal_data_path"):
        if not mt5_config.get(field):
            issues.append({"code": "missing_mt5_field", "field": field})

    runtime = profile.get("runtime") if isinstance(profile.get("runtime"), dict) else {}
    namespace = runtime.get("broker_account_namespace") or runtime.get("profile_namespace")
    if not namespace:
        issues.append({"code": "missing_runtime_namespace"})

    runtime_paths = profile.get("runtime_paths") if isinstance(profile.get("runtime_paths"), dict) else {}
    required_runtime_path_fields = (
        "knowledge_base_root",
        "trade_records_root",
        "pipeline_state_root",
        "shadow_logs_root",
        "m1_data_root",
        "tick_data_root",
    )
    for field in required_runtime_path_fields:
        value = str(runtime_paths.get(field) or "")
        if not value:
            issues.append({"code": "missing_runtime_path", "field": field})
        elif namespace and str(namespace) not in value.replace("\\", "/"):
            issues.append(
                {
                    "code": "runtime_path_namespace_mismatch",
                    "field": field,
                    "namespace": namespace,
                    "value": value,
                }
            )

    alias_to_symbols: dict[str, list[str]] = {}
    for symbol in symbols:
        inst_key = symbol if symbol in instruments else resolve_instrument_config_key(profile, symbol)
        inst = instruments.get(inst_key) if inst_key else None
        if not isinstance(inst, dict):
            if symbol in allowed_missing:
                observed_allowed_missing.append(symbol)
                continue
            issues.append({"code": "missing_active_symbol", "symbol": symbol})
            continue
        market = inst.get("market") if isinstance(inst.get("market"), dict) else {}
        alias = str(market.get("mt5_symbol") or "").strip()
        if alias:
            alias_to_symbols.setdefault(alias.upper(), []).append(symbol)
        for field in REQUIRED_MARKET_FIELDS:
            if field not in market:
                issues.append({"code": "missing_market_field", "symbol": symbol, "field": field})
                continue
            if field in {
                "tick_size",
                "point",
                "trade_tick_size",
                "trade_tick_value",
                "contract_size",
                "volume_min",
                "volume_max",
                "volume_step",
            }:
                number = _as_number(market.get(field))
                if number is None or number <= 0:
                    issues.append(
                        {
                            "code": "non_positive_market_field",
                            "symbol": symbol,
                            "field": field,
                            "value": market.get(field),
                        }
                    )
        profile_name = str(profile.get("profile_name") or "").strip().lower()
        if profile_name != "redacted_account" and alias.upper() in redacted_account_ALIAS_LEAKS.get(symbol, set()):
            issues.append(
                {
                    "code": "redacted_account_alias_leakage",
                    "symbol": symbol,
                    "alias": alias,
                }
            )

    for alias, owners in sorted(alias_to_symbols.items()):
        if len(owners) > 1:
            if not allow_duplicate_broker_aliases:
                issues.append({"code": "duplicate_broker_alias", "alias": alias, "symbols": owners})

    return {
        "schema_version": "broker_profile_verification_result_v1",
        "profile_path": str(profile_path),
        "profile_name": profile.get("profile_name"),
        "surface": surface,
        "active_symbol_count": len(symbols),
        "alias_count": len(alias_to_symbols),
        "missing_symbols_allowed": sorted(observed_allowed_missing),
        "missing_symbols_allowed_count": len(observed_allowed_missing),
        "duplicate_broker_aliases_allowed": bool(allow_duplicate_broker_aliases),
        "duplicate_broker_alias_groups": {
            alias: owners for alias, owners in sorted(alias_to_symbols.items()) if len(owners) > 1
        },
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--result", type=Path, default=None)
    parser.add_argument(
        "--surface",
        choices=("vnext24", "ultimate-active"),
        default="vnext24",
        help="Symbol surface to verify; default preserves the historical 24-symbol verifier.",
    )
    parser.add_argument("--agent-config", type=Path, default=Path("config/agent_config.yaml"))
    parser.add_argument("--allow-missing-active-symbol", action="append", default=[])
    parser.add_argument(
        "--allow-known-redacted_account-active-gaps",
        action="store_true",
        help="Allow the direct-VPS-confirmed redacted_account unsupported active symbols while reporting them.",
    )
    parser.add_argument(
        "--allow-duplicate-broker-aliases",
        action="store_true",
        help="Allow intentional canonical aliases that map to one broker symbol, while reporting groups.",
    )
    args = parser.parse_args(argv)

    symbols = VNEXT_24_SYMBOLS
    if args.surface == "ultimate-active":
        symbols = active_ultimate_book_symbols(args.agent_config)
    allowed_missing = tuple(args.allow_missing_active_symbol or ())
    if args.allow_known_redacted_account_active_gaps:
        allowed_missing = tuple(sorted(set(allowed_missing) | set(redacted_account_KNOWN_UNSUPPORTED_ACTIVE_SYMBOLS)))
    result = verify_profile(
        args.profile,
        symbols=symbols,
        surface=args.surface,
        allowed_missing_symbols=allowed_missing,
        allow_duplicate_broker_aliases=args.allow_duplicate_broker_aliases,
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
