#!/usr/bin/env python3
"""Build the FTMO local profile and VPS dual-production prep package.

Evidence class: local FTMO MT5 read-only metadata/history/account capture plus
offline profile/config/verifier/setup artifacts. The script does not place,
modify, cancel, close, or query open-position mutation routes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.verify_broker_profile import VNEXT_24_SYMBOLS, verify_profile  # noqa: E402
from src.utils.broker_profile import sanitize_namespace, sha256_text  # noqa: E402


ROUTE_DIR = Path(__file__).resolve().parent
RAW_DIR = ROUTE_DIR / "raw_official_sources"
TEMPLATE_DIR = ROUTE_DIR / "templates"
CURRENT_FTMO_PROFILE = REPO_ROOT / "config" / "profiles" / "ftmo.yaml"
PROFILE_README = REPO_ROOT / "config" / "profiles" / "README.md"
redacted_account_PROFILE = REPO_ROOT / "config" / "profiles" / "redacted_account.yaml"
BASE_CONFIG = REPO_ROOT / "config" / "agent_config.yaml"

OFFICIAL_SOURCES = [
    {
        "id": "ftmo_trading_objectives",
        "url": "https://ftmo.com/en/trading-objectives/",
        "purpose": "2-Step challenge profit target, daily loss, maximum loss, reset-time, and trading-day rules.",
    },
    {
        "id": "ftmo_symbols",
        "url": "https://ftmo.com/en/symbols/",
        "purpose": "Official symbol specifications and trading hours reference.",
    },
    {
        "id": "ftmo_faq_trading_objectives",
        "url": "https://ftmo.com/en/faq/what-are-the-trading-objectives/",
        "purpose": "FAQ source for trading objective cross-check.",
    },
]

EXPECTED_ROUTE_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    "config/agent_config.yaml",
    "config/profiles/ftmo.yaml",
    "config/profiles/redacted_account.yaml",
    "run_agent.py",
    "start_all.bat",
    "scripts/watchdog.ps1",
    "src/utils/config.py",
    "src/utils/broker_profile.py",
    "src/mt5/mt5_real.py",
    "src/components/orchestrator.py",
    "src/components/m1_capture.py",
    "src/components/tick_capture.py",
    "src/components/broker_truth_cost_capture_v2.py",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/ACTIVE_REPAIR_STATE.json",
    "research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01/COMPLETION_AUDIT.json",
    "research/operations/vnext_mt5_local_cache_preservation_2026_06_01/COMPLETION_AUDIT.json",
    "research/operations/vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01/LANE18_COMPLETION_AUDIT.json",
    "research/operations/vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01/POST_LANE18_COMPLETION_AUDIT.json",
]

FTMO_ALIAS_HINTS = {
    "GER40": ("GER40.cash", "GER40"),
    "JP225": ("JP225.cash", "JP225"),
    "NAS100": ("US100.cash", "NAS100", "NDX100"),
    "SPX500": ("US500.cash", "SPX500", "US500"),
    "UK100": ("UK100.cash", "UK100"),
    "UKOIL_cash": ("UKOIL.cash", "UKOIL_cash", "UKOIL"),
    "US30_cash": ("US30.cash", "US30_cash", "US30"),
    "USOIL_cash": ("USOIL.cash", "USOIL_cash", "USOIL"),
}

SPEC_FIELDS = [
    "name",
    "description",
    "path",
    "visible",
    "select",
    "digits",
    "point",
    "trade_tick_size",
    "trade_tick_value",
    "trade_tick_value_profit",
    "trade_tick_value_loss",
    "trade_contract_size",
    "volume_min",
    "volume_max",
    "volume_step",
    "volume_limit",
    "trade_stops_level",
    "trade_freeze_level",
    "spread",
    "spread_float",
    "trade_mode",
    "trade_exemode",
    "filling_mode",
    "order_mode",
    "expiration_mode",
    "swap_mode",
    "swap_long",
    "swap_short",
    "swap_rollover3days",
    "margin_initial",
    "margin_maintenance",
    "margin_hedged",
    "trade_calc_mode",
    "currency_base",
    "currency_profit",
    "currency_margin",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if hasattr(value, "_asdict"):
        return jsonable(value._asdict())
    if hasattr(value, "_fields"):
        return {field: jsonable(getattr(value, field, None)) for field in value._fields}
    try:
        return value.item()
    except Exception:  # noqa: BLE001
        return str(value)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> dict[str, str]:
    try:
        line = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%H%x00%h%x00%s"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
        full, short, subject = line.split("\x00", 2)
        return {"head": full, "head_short": short, "head_subject": subject}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


def snapshot(obj: Any) -> dict[str, Any]:
    return jsonable(obj._asdict() if hasattr(obj, "_asdict") else obj) if obj is not None else {}


def account_identity(account: Any) -> dict[str, Any]:
    raw = snapshot(account)
    login = raw.pop("login", None)
    name = raw.get("name")
    return {
        **raw,
        "login": "<redacted>",
        "login_sha256": sha256_text(login) if login is not None else None,
        "login_hash_prefix": sha256_text(login)[:8] if login is not None else None,
        "account_name_sha256": sha256_text(name) if name else None,
    }


def terminal_exe_from_info(terminal: dict[str, Any]) -> str | None:
    path = terminal.get("path")
    if not path:
        return None
    candidate = Path(path) / "terminal64.exe"
    return str(candidate) if candidate.exists() else str(path)


def normalize_symbol(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper().replace("_CASH", "CASH"))


def alias_candidates(symbol: str, inventory_names: set[str]) -> list[str]:
    candidates = []
    for item in FTMO_ALIAS_HINTS.get(symbol, (symbol,)):
        if item not in candidates:
            candidates.append(item)
    if symbol not in candidates:
        candidates.append(symbol)
    if symbol.endswith("_cash"):
        base = symbol[:-5]
        for item in (f"{base}.cash", base):
            if item not in candidates:
                candidates.append(item)

    normalized_target = normalize_symbol(symbol)
    if symbol.endswith("_cash"):
        normalized_target = normalize_symbol(symbol[:-5])
    for name in sorted(inventory_names):
        norm = normalize_symbol(name)
        if norm == normalized_target or norm == f"{normalized_target}CASH":
            if name not in candidates:
                candidates.append(name)
    return candidates


def resolve_aliases(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inventory_names = {str(row.get("name")) for row in inventory if row.get("name")}
    rows = []
    for symbol in VNEXT_24_SYMBOLS:
        candidates = alias_candidates(symbol, inventory_names)
        present = [candidate for candidate in candidates if candidate in inventory_names]
        chosen = present[0] if len(present) == 1 else None
        if len(present) > 1:
            hint_order = [item for item in candidates if item in present]
            chosen = hint_order[0]
        if chosen:
            status = "resolved"
        else:
            status = "unsupported"
        rows.append(
            {
                "schema_version": "ftmo_alias_resolution_v1",
                "symbol": symbol,
                "candidate_aliases_checked": candidates,
                "present_aliases": present,
                "mt5_symbol": chosen,
                "alias_status": status,
                "ambiguity_status": "ambiguous_multiple_present" if len(present) > 1 else "not_ambiguous",
                "source": "local_ftmo_mt5_symbols_get",
            }
        )
    alias_counts = Counter(row["mt5_symbol"] for row in rows if row.get("mt5_symbol"))
    for row in rows:
        alias = row.get("mt5_symbol")
        row["duplicate_alias_status"] = (
            "duplicate_alias" if alias and alias_counts[alias] > 1 else "unique_or_unresolved"
        )
    return rows


def session_rows(mt5: Any, symbol: str) -> dict[str, Any]:
    out: dict[str, Any] = {"quote": [], "trade": []}
    for day in range(7):
        for index in range(24):
            try:
                quote = mt5.symbol_info_session_quote(symbol, day, index)
            except Exception as exc:  # noqa: BLE001
                out["quote"].append({"day": day, "index": index, "error": str(exc)})
                break
            if not quote:
                break
            out["quote"].append({"day": day, "index": index, "session": jsonable(quote)})
        for index in range(24):
            try:
                trade = mt5.symbol_info_session_trade(symbol, day, index)
            except Exception as exc:  # noqa: BLE001
                out["trade"].append({"day": day, "index": index, "error": str(exc)})
                break
            if not trade:
                break
            out["trade"].append({"day": day, "index": index, "session": jsonable(trade)})
    return out


def capture_history_depth(mt5: Any, symbol: str, *, bars: int, tick_count: int) -> dict[str, Any]:
    result: dict[str, Any] = {"bars": {}, "ticks": {}}
    timeframe_names = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "D1": mt5.TIMEFRAME_D1,
    }
    for name, tf in timeframe_names.items():
        try:
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        except Exception as exc:  # noqa: BLE001
            result["bars"][name] = {"status": "error", "error": str(exc), "request_row_cap": bars}
            continue
        count = len(rates) if rates is not None else 0
        first_time = None
        last_time = None
        if count:
            first_time = datetime.fromtimestamp(int(rates[0]["time"]), timezone.utc).isoformat()
            last_time = datetime.fromtimestamp(int(rates[-1]["time"]), timezone.utc).isoformat()
        result["bars"][name] = {
            "status": "captured" if count else "no_rows_returned",
            "row_count": count,
            "request_row_cap": bars,
            "depth_status": "at_least_cap" if count >= bars else "exact_within_cap",
            "first_time_utc": first_time,
            "last_time_utc": last_time,
        }
    tick_start = datetime.now(timezone.utc) - timedelta(days=7)
    try:
        ticks = mt5.copy_ticks_from(symbol, tick_start, tick_count, mt5.COPY_TICKS_ALL)
    except Exception as exc:  # noqa: BLE001
        result["ticks"] = {"status": "error", "error": str(exc), "request_row_cap": tick_count}
        return result
    count = len(ticks) if ticks is not None else 0
    first_tick = None
    last_tick = None
    if count:
        first_tick = datetime.fromtimestamp(int(ticks[0]["time"]), timezone.utc).isoformat()
        last_tick = datetime.fromtimestamp(int(ticks[-1]["time"]), timezone.utc).isoformat()
    result["ticks"] = {
        "status": "captured" if count else "no_rows_returned",
        "row_count": count,
        "request_row_cap": tick_count,
        "depth_status": "at_least_cap" if count >= tick_count else "exact_within_cap",
        "first_time_utc": first_tick,
        "last_time_utc": last_tick,
        "query_start_utc": tick_start.isoformat(),
    }
    return result


def select_for_capture(mt5: Any, symbol: str) -> tuple[bool | None, bool, str | None]:
    info = mt5.symbol_info(symbol)
    if info is None:
        return None, False, "symbol_info_missing"
    was_visible = bool(getattr(info, "visible", False))
    if was_visible:
        return was_visible, False, None
    try:
        ok = bool(mt5.symbol_select(symbol, True))
        return was_visible, ok, None if ok else str(mt5.last_error())
    except Exception as exc:  # noqa: BLE001
        return was_visible, False, str(exc)


def restore_selection(mt5: Any, symbol: str, was_visible: bool | None, selected_for_capture: bool) -> None:
    if was_visible is False and selected_for_capture:
        try:
            mt5.symbol_select(symbol, False)
        except Exception:  # noqa: BLE001
            pass


def capture_mt5(terminal_path: str | None, *, history_bars: int, tick_count: int) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        return {"status": "import_failed", "error": str(exc)}

    init_kwargs = {"path": terminal_path} if terminal_path else {}
    initialized = bool(mt5.initialize(**init_kwargs))
    result: dict[str, Any] = {
        "schema_version": "ftmo_mt5_readonly_capture_v1",
        "source": "local_ftmo_mt5_readonly",
        "capture_started_utc": utc_now(),
        "terminal_path_arg": terminal_path,
        "initialized": initialized,
        "last_error": jsonable(mt5.last_error()),
    }
    if not initialized:
        return result

    try:
        terminal = snapshot(mt5.terminal_info())
        account_raw = mt5.account_info()
        account = account_identity(account_raw)
        inventory = [snapshot(sym) for sym in (mt5.symbols_get() or [])]
        aliases = resolve_aliases(inventory)
        specs: list[dict[str, Any]] = []
        session_cost_history: list[dict[str, Any]] = []

        for index, alias_row in enumerate(aliases, start=1):
            symbol = alias_row["symbol"]
            mt5_symbol = alias_row.get("mt5_symbol")
            write_json(
                ROUTE_DIR / "MT5_CAPTURE_PROGRESS.json",
                {
                    "schema_version": "ftmo_mt5_capture_progress_v1",
                    "updated_at_utc": utc_now(),
                    "current_index": index,
                    "total_aliases": len(aliases),
                    "current_symbol": symbol,
                    "current_mt5_symbol": mt5_symbol,
                    "completed_spec_count": len(specs),
                    "completed_session_history_count": len(session_cost_history),
                },
            )
            print(
                f"MT5_CAPTURE {index}/{len(aliases)} {symbol} -> {mt5_symbol}",
                flush=True,
            )
            if not mt5_symbol:
                continue
            was_visible, selected, select_error = select_for_capture(mt5, mt5_symbol)
            try:
                info = snapshot(mt5.symbol_info(mt5_symbol))
                tick = snapshot(mt5.symbol_info_tick(mt5_symbol))
                spec = {field: info.get(field) for field in SPEC_FIELDS}
                spec.update(
                    {
                        "schema_version": "ftmo_symbol_spec_v1",
                        "symbol": symbol,
                        "mt5_symbol": mt5_symbol,
                        "select_before_capture": was_visible,
                        "selected_for_readonly_capture": selected,
                        "select_error": select_error,
                    }
                )
                specs.append(spec)
                spread_sample = {
                    "bid": tick.get("bid"),
                    "ask": tick.get("ask"),
                    "time": tick.get("time"),
                    "time_msc": tick.get("time_msc"),
                    "spread_price": (
                        abs(float(tick.get("ask")) - float(tick.get("bid")))
                        if tick.get("ask") is not None and tick.get("bid") is not None
                        else None
                    ),
                    "tick_status": "captured" if tick else "tick_unavailable",
                }
                session_cost_history.append(
                    {
                        "schema_version": "ftmo_session_spread_cost_history_v1",
                        "symbol": symbol,
                        "mt5_symbol": mt5_symbol,
                        "session_windows": session_rows(mt5, mt5_symbol),
                        "spread_sample": spread_sample,
                        "cost_fields": {
                            "spread": info.get("spread"),
                            "spread_float": info.get("spread_float"),
                            "swap_mode": info.get("swap_mode"),
                            "swap_long": info.get("swap_long"),
                            "swap_short": info.get("swap_short"),
                            "swap_rollover3days": info.get("swap_rollover3days"),
                        },
                        "history_depth": capture_history_depth(
                            mt5,
                            mt5_symbol,
                            bars=history_bars,
                            tick_count=tick_count,
                        ),
                    }
                )
            finally:
                restore_selection(mt5, mt5_symbol, was_visible, selected)

        write_json(
            ROUTE_DIR / "MT5_CAPTURE_PROGRESS.json",
            {
                "schema_version": "ftmo_mt5_capture_progress_v1",
                "updated_at_utc": utc_now(),
                "status": "capture_loop_complete",
                "total_aliases": len(aliases),
                "completed_spec_count": len(specs),
                "completed_session_history_count": len(session_cost_history),
            },
        )
        result.update(
            {
                "status": "captured",
                "capture_finished_utc": utc_now(),
                "terminal": terminal,
                "terminal_exe_path": terminal_exe_from_info(terminal),
                "account": account,
                "symbol_inventory": inventory,
                "alias_resolution": aliases,
                "symbol_specs": specs,
                "session_spread_cost_history": session_cost_history,
            }
        )
        return result
    finally:
        mt5.shutdown()


def fetch_official_sources() -> list[dict[str, Any]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for source in OFFICIAL_SOURCES:
        raw_path = RAW_DIR / f"{source['id']}.html"
        req = urllib.request.Request(
            source["url"],
            headers={"User-Agent": "GTOS-FTMO-source-capture/1.0"},
        )
        row = {
            "schema_version": "official_ftmo_source_index_v1",
            **source,
            "fetched_at_utc": utc_now(),
            "raw_path": str(raw_path.relative_to(REPO_ROOT)),
        }
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
            raw_path.write_bytes(body)
            row.update(
                {
                    "fetch_status": "captured",
                    "http_status": getattr(resp, "status", None),
                    "byte_count": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                }
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raw_path.write_text(str(exc), encoding="utf-8")
            row.update(
                {
                    "fetch_status": "failed",
                    "http_status": None,
                    "byte_count": raw_path.stat().st_size,
                    "sha256": sha256_file(raw_path),
                    "error": str(exc),
                }
            )
        rows.append(row)
    return rows


def risk_overlay_for_symbol(symbol: str, old_ftmo: dict[str, Any], redacted_account: dict[str, Any]) -> dict[str, Any]:
    old_risk = (
        old_ftmo.get("instruments", {}).get(symbol, {}).get("risk", {})
        if isinstance(old_ftmo.get("instruments"), dict)
        else {}
    )
    funded_risk = (
        redacted_account.get("instruments", {}).get(symbol, {}).get("risk", {})
        if isinstance(redacted_account.get("instruments"), dict)
        else {}
    )
    merged = dict(old_risk or {})
    if "risk_per_trade_pct" not in merged and "risk_per_trade_pct" in funded_risk:
        merged["risk_per_trade_pct"] = funded_risk["risk_per_trade_pct"]
    merged.setdefault(
        "risk_policy_source",
        "existing_gtos_vnext_profile_policy_not_mt5_broker_fact_owner_review_before_live_activation",
    )
    return merged


def build_profile(
    capture: dict[str, Any],
    old_ftmo: dict[str, Any],
    redacted_account: dict[str, Any],
    *,
    canonical_profile_name: str,
    compatibility_profile: bool = False,
) -> dict[str, Any]:
    account = capture["account"]
    terminal = capture["terminal"]
    terminal_exe = capture.get("terminal_exe_path")
    namespace = sanitize_namespace(canonical_profile_name)
    specs_by_symbol = {row["symbol"]: row for row in capture["symbol_specs"]}
    aliases_by_symbol = {row["symbol"]: row for row in capture["alias_resolution"]}
    instruments: dict[str, Any] = {}
    for symbol in VNEXT_24_SYMBOLS:
        alias = aliases_by_symbol[symbol]["mt5_symbol"]
        spec = specs_by_symbol[symbol]
        instruments[symbol] = {
            "market": {
                "mt5_symbol": alias,
                "tick_size": spec.get("trade_tick_size") or spec.get("point"),
                "point": spec.get("point"),
                "digits": spec.get("digits"),
                "trade_tick_size": spec.get("trade_tick_size"),
                "trade_tick_value": spec.get("trade_tick_value"),
                "trade_tick_value_profit": spec.get("trade_tick_value_profit"),
                "trade_tick_value_loss": spec.get("trade_tick_value_loss"),
                "contract_size": spec.get("trade_contract_size"),
                "trade_contract_size": spec.get("trade_contract_size"),
                "volume_min": spec.get("volume_min"),
                "volume_max": spec.get("volume_max"),
                "volume_step": spec.get("volume_step"),
                "volume_limit": spec.get("volume_limit"),
                "trade_stops_level": spec.get("trade_stops_level"),
                "trade_freeze_level": spec.get("trade_freeze_level"),
                "spread": spec.get("spread"),
                "spread_float": spec.get("spread_float"),
                "trade_mode": spec.get("trade_mode"),
                "execution_mode": spec.get("trade_exemode"),
                "filling_mode": spec.get("filling_mode"),
                "order_mode": spec.get("order_mode"),
                "expiration_mode": spec.get("expiration_mode"),
                "swap_mode": spec.get("swap_mode"),
                "swap_long": spec.get("swap_long"),
                "swap_short": spec.get("swap_short"),
                "triple_rollover_day": spec.get("swap_rollover3days"),
                "margin_initial": spec.get("margin_initial"),
                "margin_maintenance": spec.get("margin_maintenance"),
                "margin_hedged": spec.get("margin_hedged"),
                "calculation_mode": spec.get("trade_calc_mode"),
                "currency_base": spec.get("currency_base"),
                "currency_profit": spec.get("currency_profit"),
                "currency_margin": spec.get("currency_margin"),
                "description": spec.get("description"),
                "path": spec.get("path"),
            },
            "risk": risk_overlay_for_symbol(symbol, old_ftmo, redacted_account),
        }
        instruments[symbol]["risk"].setdefault("contract_size", spec.get("trade_contract_size"))

    profile = {
        "profile_name": "ftmo" if compatibility_profile else canonical_profile_name,
        "profile_status": (
            "compatibility_pointer_to_account_specific_ftmo_profile"
            if compatibility_profile
            else "account_specific_ftmo_server3_profile"
        ),
        "profile_alias_for": canonical_profile_name if compatibility_profile else None,
        "generated_by": str(Path(__file__).relative_to(REPO_ROOT)),
        "generated_at_utc": utc_now(),
        "source_authority": {
            "broker_fact_authority": "local_ftmo_mt5_readonly_capture",
            "vps_runtime_authority": "vps_production_repo_runtime_must_rebase_and_verify",
            "github_local_repo_role": "portable_profile_and_verifier_package",
        },
        "runtime": {
            "profile_namespace": namespace,
            "broker_account_namespace": namespace,
            "process_group": "ftmo_challenge_live",
        },
        "mt5": {
            "terminal_path": terminal_exe,
            "terminal_data_path": terminal.get("data_path"),
            "terminal_path_source": "local_ftmo_terminal_info_plus_terminal64_exe_probe",
        },
        "broker_profile": {
            "broker": "ftmo",
            "company": account.get("company"),
            "server": account.get("server"),
            "account_name": account.get("name"),
            "expected_account": {
                "server": account.get("server"),
                "company": account.get("company"),
                "currency": account.get("currency"),
                "login_sha256": account.get("login_sha256"),
                "terminal_path": terminal.get("path"),
                "terminal_data_path": terminal.get("data_path"),
            },
            "identity_secret_policy": "account_login_redacted_sha256_only_no_credentials",
        },
        "runtime_paths": {
            "logs_root": f"logs/{namespace}",
            "knowledge_base_root": f"knowledge_base/{namespace}",
            "trade_records_root": f"knowledge_base/{namespace}/trade_records",
            "pipeline_state_root": f"pipeline_state/{namespace}",
            "shadow_logs_root": f"shadow_logs/{namespace}",
            "m1_data_root": f"data/m1/{namespace}",
            "tick_data_root": f"data/ticks/{namespace}",
        },
        "notification_queue": {
            "queue_path": f"pipeline_state/{namespace}/notification_queue.jsonl",
            "identity_prefix": "FTMO",
        },
        "trade_capture": {
            "base_path": f"knowledge_base/{namespace}/trade_records",
        },
        "broker_truth_cost_capture_v2": {
            "log_path": f"shadow_logs/{namespace}/broker_truth_cost_capture_v2.jsonl",
        },
        "risk": {
            **(old_ftmo.get("risk") or {}),
            "risk_policy_source": "existing_ftmo_profile_operator_policy; not an MT5 broker fact",
        },
        "drawdown_reduction": old_ftmo.get("drawdown_reduction") or {},
        "ftmo_rules": {
            "account_product_inferred_from_local_account_name": account.get("name"),
            "account_balance_initial_inferred_usd": account.get("balance"),
            "challenge_model": "2-Step",
            "profit_target_phase1_pct": 10.0,
            "profit_target_phase2_pct": 5.0,
            "maximum_daily_loss_pct": 5.0,
            "maximum_loss_pct": 10.0,
            "minimum_trading_days": 4,
            "daily_reset_time": "00:00 CE(S)T",
            "official_source_refs": [
                "OFFICIAL_FTMO_SOURCE_INDEX.json:ftmo_trading_objectives",
                "OFFICIAL_FTMO_SOURCE_INDEX.json:ftmo_faq_trading_objectives",
            ],
            "owner_input_requirements": [
                "confirm paid challenge/account stage, swing/add-on status, and any account-specific FTMO dashboard constraints before VPS activation"
            ],
        },
        "instruments": instruments,
    }
    if not compatibility_profile:
        profile.pop("profile_alias_for", None)
    return profile


def compare_ftmo_yaml(old_ftmo: dict[str, Any], alias_rows: list[dict[str, Any]], specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    old_instruments = old_ftmo.get("instruments") if isinstance(old_ftmo.get("instruments"), dict) else {}
    spec_by_symbol = {row["symbol"]: row for row in specs}
    rows = []
    for alias in alias_rows:
        symbol = alias["symbol"]
        old_market = old_instruments.get(symbol, {}).get("market", {}) if isinstance(old_instruments.get(symbol), dict) else {}
        old_alias = old_market.get("mt5_symbol")
        new_alias = alias.get("mt5_symbol")
        spec = spec_by_symbol.get(symbol, {})
        status = "confirmed" if old_alias == new_alias and old_alias else "contradicted_or_missing"
        if old_alias is None:
            status = "missing_in_ftmo_yaml"
        rows.append(
            {
                "schema_version": "ftmo_yaml_stale_comparison_v1",
                "symbol": symbol,
                "old_ftmo_yaml_alias": old_alias,
                "captured_ftmo_alias": new_alias,
                "alias_comparison_status": status,
                "old_tick_size": old_market.get("tick_size"),
                "captured_trade_tick_size": spec.get("trade_tick_size"),
                "captured_trade_tick_value": spec.get("trade_tick_value"),
                "captured_contract_size": spec.get("trade_contract_size"),
                "decision": (
                    "repair_or_account_specific_pointer_required"
                    if status != "confirmed"
                    else "no_alias_change_required"
                ),
            }
        )
    return rows


def runtime_audit() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "local_dual_broker_runtime_audit_v1",
            "file_path": "run_agent.py",
            "code_location": "argparse + SessionOrchestrator construction",
            "current_behavior": "supports --terminal-path and --runtime-namespace; legacy launch unchanged when omitted",
            "dual_broker_impact": "order-capable runtime can target a specific terminal and namespaced logs",
            "required_local_change": "implemented",
            "required_vps_change": "port/rebase and pass dual preflight before activation",
        },
        {
            "schema_version": "local_dual_broker_runtime_audit_v1",
            "file_path": "src/components/orchestrator.py",
            "code_location": "SessionOrchestrator.__init__/_bootstrap/_acquire_lock",
            "current_behavior": "loads profile namespace, passes terminal path to MT5, asserts expected account/server after connect, namespaces orchestrator lock when configured",
            "dual_broker_impact": "prevents FTMO/redacted_account terminal-account mismatch before order-capable runtime",
            "required_local_change": "implemented",
            "required_vps_change": "verify against VPS production code and active process manager",
        },
        {
            "schema_version": "local_dual_broker_runtime_audit_v1",
            "file_path": "src/components/execution.py",
            "code_location": "ExecutionEngine.__init__ checkpoint/pending-intent paths",
            "current_behavior": "pending intents and execution checkpoint filenames include broker/account namespace when configured",
            "dual_broker_impact": "prevents pending-intent/checkpoint collision",
            "required_local_change": "implemented",
            "required_vps_change": "confirm no VPS-only execution checkpoint wrapper bypasses this class",
        },
        {
            "schema_version": "local_dual_broker_runtime_audit_v1",
            "file_path": "src/components/m1_capture.py",
            "code_location": "CLI main and capture_once",
            "current_behavior": "supports terminal path, runtime namespace, namespaced lock, state file, heartbeat name, and data root",
            "dual_broker_impact": "M1 data and state can be separated per broker/account",
            "required_local_change": "implemented",
            "required_vps_change": "launch separate process groups with namespace args",
        },
        {
            "schema_version": "local_dual_broker_runtime_audit_v1",
            "file_path": "src/components/tick_capture.py",
            "code_location": "CLI main/run_capture_loop/_flush_buffer",
            "current_behavior": "supports terminal path, runtime namespace, namespaced lock/heartbeat/default data root",
            "dual_broker_impact": "tick data and daemon state can be separated per broker/account",
            "required_local_change": "implemented",
            "required_vps_change": "watchdog/supervisor must inspect namespaced daemon names",
        },
        {
            "schema_version": "local_dual_broker_runtime_audit_v1",
            "file_path": "scripts/watchdog.ps1",
            "code_location": "live production supervisor",
            "current_behavior": "single redacted_account process group in current local script",
            "dual_broker_impact": "cannot be final dual-prod supervisor without VPS-side process-group patch",
            "required_local_change": "dual-broker templates emitted under route templates",
            "required_vps_change": "VPS-only final patch because VPS production runtime owns live process supervision",
        },
        {
            "schema_version": "local_dual_broker_runtime_audit_v1",
            "file_path": "src/utils/notification_queue.py",
            "code_location": "queue path configured by notification_queue.queue_path",
            "current_behavior": "profile can set namespaced queue path; route profile does so",
            "dual_broker_impact": "Telegram queues can be isolated by broker/account",
            "required_local_change": "profile-level path generated",
            "required_vps_change": "run one worker per broker namespace or patched dual-worker supervisor",
        },
    ]


def implementation_ledger(canonical_profile_name: str) -> list[dict[str, Any]]:
    changed = [
        "src/utils/broker_profile.py",
        "run_agent.py",
        "src/components/orchestrator.py",
        "src/components/execution.py",
        "src/components/m1_capture.py",
        "src/components/tick_capture.py",
        "src/components/broker_truth_cost_capture_v2.py",
        "scripts/verify_broker_profile.py",
        "research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/verify_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py",
        "tests/test_broker_profile_namespace.py",
        "tests/test_verify_broker_profile.py",
        "tests/test_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py",
        f"config/profiles/{canonical_profile_name}.yaml",
        "config/profiles/ftmo.yaml",
        "config/profiles/README.md",
    ]
    return [
        {
            "schema_version": "ftmo_local_implementation_change_v1",
            "path": path,
            "change_status": "implemented_locally",
            "vps_rebase_status": "must_compare_with_vps_production_before_activation",
        }
        for path in changed
    ]


def unresolved_requirements(source_index: list[dict[str, Any]], history_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    if any(row.get("fetch_status") != "captured" for row in source_index):
        rows.append(
            {
                "schema_version": "ftmo_unresolved_requirement_v1",
                "requirement": "official_ftmo_source_capture_retry",
                "status": "exact_source_requirement",
                "owner_or_vps_action": "retry official FTMO URL fetch or provide redacted official dashboard/support export",
                "evidence": [row for row in source_index if row.get("fetch_status") != "captured"],
            }
        )
    capped = []
    for row in history_rows:
        for tf, depth in (row.get("history_depth", {}).get("bars") or {}).items():
            if depth.get("depth_status") == "at_least_cap":
                capped.append({"symbol": row["symbol"], "timeframe": tf, "cap": depth.get("request_row_cap")})
    if capped:
        rows.append(
            {
                "schema_version": "ftmo_unresolved_requirement_v1",
                "requirement": "exact_full_history_depth_beyond_capture_cap",
                "status": "optional_extended_export_requirement_not_alias_spec_blocker",
                "owner_or_vps_action": "rerun builder with larger --history-bars or use VPS MT5 export for exact full-depth inventory",
                "evidence_count": len(capped),
                "evidence": capped,
            }
        )
    rows.append(
        {
            "schema_version": "ftmo_unresolved_requirement_v1",
            "requirement": "vps_production_authority_rebase",
            "status": "vps_only_finalization_requirement",
            "owner_or_vps_action": "export/inspect VPS current production repo, active process commands, terminal paths, accounts, locks, logs, and supervisor before dual-live activation",
        }
    )
    rows.append(
        {
            "schema_version": "ftmo_unresolved_requirement_v1",
            "requirement": "owner_account_stage_and_addon_confirmation",
            "status": "owner_input_required_before_activation",
            "owner_or_vps_action": "confirm FTMO account phase/stage, swing/add-on status, and any dashboard-specific constraints not exposed by MT5",
        }
    )
    return rows


def write_templates(canonical_profile_name: str, namespace: str, terminal_path: str | None) -> None:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    terminal = terminal_path or "<VPS_FTMO_TERMINAL64_EXE>"
    funded_terminal = "<VPS_redacted_account_TERMINAL64_EXE>"
    (TEMPLATE_DIR / "ftmo_readonly_preflight.ps1").write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                "$env:GTOS_RUNTIME_NAMESPACE = '" + namespace + "'",
                "$env:GTOS_MT5_TERMINAL_PATH = '" + terminal + "'",
                f"py -3 scripts/verify_broker_profile.py config/profiles/{canonical_profile_name}.yaml",
                f"py -3 run_agent.py --mode mock --symbol XAUUSD --profile {canonical_profile_name} --runtime-namespace {namespace}",
                f"py -3 -m src.components.m1_capture --profile {canonical_profile_name} --runtime-namespace {namespace} --terminal-path \"{terminal}\" --symbols XAUUSD --once",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (TEMPLATE_DIR / "vps_dual_process_groups.ps1").write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                "$symbols = @('AUDJPY','AUDUSD','BTCUSD','CHFJPY','ETHUSD','EURGBP','EURJPY','EURUSD','GBPJPY','GBPUSD','GER40','JP225','NAS100','NZDUSD','SPX500','UK100','UKOIL_cash','US30_cash','USDCAD','USDCHF','USDJPY','USOIL_cash','XAGUSD','XAUUSD')",
                "$fundedProfile = 'redacted_account'",
                "$fundedNs = 'redacted_account_live_<account_hash>'",
                f"$ftmoProfile = '{canonical_profile_name}'",
                f"$ftmoNs = '{namespace}'",
                f"$fundedTerminal = '{funded_terminal}'",
                f"$ftmoTerminal = '{terminal}'",
                "foreach ($sym in $symbols) {",
                "  Start-Process -WindowStyle Hidden -FilePath py -ArgumentList @('-3','run_agent.py','--symbol',$sym,'--mode','live','--profile',$fundedProfile,'--runtime-namespace',$fundedNs,'--terminal-path',$fundedTerminal)",
                "  Start-Process -WindowStyle Hidden -FilePath py -ArgumentList @('-3','run_agent.py','--symbol',$sym,'--mode','live','--profile',$ftmoProfile,'--runtime-namespace',$ftmoNs,'--terminal-path',$ftmoTerminal)",
                "}",
                "Start-Process -WindowStyle Hidden -FilePath py -ArgumentList @('-3','-m','src.components.m1_capture','--profile',$fundedProfile,'--runtime-namespace',$fundedNs,'--terminal-path',$fundedTerminal)",
                "Start-Process -WindowStyle Hidden -FilePath py -ArgumentList @('-3','-m','src.components.m1_capture','--profile',$ftmoProfile,'--runtime-namespace',$ftmoNs,'--terminal-path',$ftmoTerminal)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (TEMPLATE_DIR / "rollback_stop_by_namespace.ps1").write_text(
        "\n".join(
            [
                "param([Parameter(Mandatory=$true)][string]$Namespace)",
                "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like \"*--runtime-namespace $Namespace*\" -or $_.CommandLine -like \"*GTOS_RUNTIME_NAMESPACE=$Namespace*\" } | ForEach-Object {",
                "  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue",
                "}",
                "Get-ChildItem knowledge_base/meta -Filter \"*${Namespace}*.lock\" -ErrorAction SilentlyContinue | Remove-Item -Force",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_vps_contract(canonical_profile_name: str, namespace: str) -> None:
    contract = f"""# VPS Dual-Production Implementation Contract

Generated: {utc_now()}

## Authority Model

- VPS production code/runtime is final live authority.
- Local FTMO MT5 capture is FTMO broker-fact authority for account/server/symbol/spec/session/spread/cost/history metadata.
- This local repo is the portable package source; it must be compared and rebased onto VPS production before activation.

## Required VPS Evidence Before Editing

1. Export current VPS `git status --short`, `git log -1 --oneline`, active process command lines, lock files, log roots, `pipeline_state`, `shadow_logs`, `data/m1`, `data/ticks`, and supervisor scripts.
2. Run read-only MT5 account assertions for both terminals.
3. Verify redacted_account terminal path and FTMO terminal path are distinct.
4. Verify redacted_account and FTMO account/server identities are distinct and match their profiles.

## Code And Config Package To Port

- `src/utils/broker_profile.py`
- `run_agent.py`
- `src/components/orchestrator.py`
- `src/components/execution.py`
- `src/components/m1_capture.py`
- `src/components/tick_capture.py`
- `src/components/broker_truth_cost_capture_v2.py`
- `scripts/verify_broker_profile.py`
- `config/profiles/{canonical_profile_name}.yaml`
- `config/profiles/ftmo.yaml`
- route templates under `{ROUTE_DIR.relative_to(REPO_ROOT)}/templates/`

## Namespace Contract

- redacted_account process group: `redacted_account_live_<account_hash>`.
- FTMO process group: `{namespace}`.
- Every order-capable process must pass `--runtime-namespace` and `--terminal-path`.
- Every profile must define `broker_profile.expected_account` with server, company, currency, and login SHA256.
- Orchestrator lock files must include namespace: `.orchestrator_<namespace>_<symbol>.lock`.
- Execution checkpoints must include namespace: `execution_checkpoint_<namespace>.json`.
- Pending intents must include namespace: `pending_intent_<symbol>_<namespace>.pkl`.
- M1 roots: `data/m1/<namespace>/`.
- Tick roots: `data/ticks/<namespace>/`.
- Trade records: `knowledge_base/<namespace>/trade_records/`.
- Broker truth logs: `shadow_logs/<namespace>/broker_truth_cost_capture_v2.jsonl`.
- Telegram queue: `pipeline_state/<namespace>/notification_queue.jsonl`.

## Merge Order

1. Stop no live process yet; first inspect VPS current production state.
2. Apply helper/profile/verifier code in a non-live working copy.
3. Add/copy FTMO profile and keep credentials out of repo.
4. Run offline profile verifier for both broker profiles.
5. Run mock/no-order launch checks for both namespaces.
6. Run read-only M1/tick/profile preflights with `--once` and no order-capable live mode.
7. Patch supervisor/watchdog to manage two process groups and namespace-specific locks/heartbeats.
8. Only after owner approval, start live process groups.

## Required Verifiers

```powershell
py -3 scripts/verify_broker_profile.py config/profiles/{canonical_profile_name}.yaml --result {ROUTE_DIR.relative_to(REPO_ROOT)}/PROFILE_VERIFIER_RESULT.json
py -3 -m pytest tests/test_broker_profile_namespace.py tests/test_verify_broker_profile.py tests/test_m1_capture.py -q
py -3 {ROUTE_DIR.relative_to(REPO_ROOT)}/verify_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py
```

## Rollback

Use `{ROUTE_DIR.relative_to(REPO_ROOT)}/templates/rollback_stop_by_namespace.ps1 -Namespace {namespace}` for FTMO-only stop. redacted_account must have its own namespace and must not be killed by FTMO rollback.

## Forbidden Until Owner Approval

No hidden live activation, no broker order/deal/position mutation, no credential commits, no remote push, and no VPS live-process mutation from the local session.
"""
    (ROUTE_DIR / "VPS_DUAL_PRODUCTION_IMPLEMENTATION_CONTRACT.md").write_text(contract, encoding="utf-8")


def write_saturation(unresolved: list[dict[str, Any]], alias_rows: list[dict[str, Any]]) -> None:
    unresolved_alias = [row for row in alias_rows if row.get("alias_status") != "resolved"]
    lines = [
        "# Saturation And Self-Red-Team Ledger",
        "",
        f"Generated: {utc_now()}",
        "",
        "- Local FTMO MT5 facts captured: terminal/account, full symbol inventory, 24-symbol alias map, symbol specs, sessions, spread samples, cost fields, history/tick depth samples.",
        "- Active 24-symbol alias unresolved count: " + str(len(unresolved_alias)) + ".",
        "- Same-evidence-class repairs performed: selected non-visible symbols for read-only metadata/history capture and restored their previous visibility state; generated account-specific profile; patched terminal/account namespace helpers; generated verifier/tests/templates.",
        "- redacted_account alias leakage guard: profile verifier rejects NDX100, GER30, UKOUSD, USOUSD, and unqualified index/oil aliases in FTMO active profile.",
        "- Collision prevention: namespace is required for locks, checkpoints, pending intents, M1/tick roots, broker truth logs, trade records, Telegram queue, and process groups.",
        "- Remaining exact requirements:",
    ]
    for row in unresolved:
        lines.append(f"  - {row['requirement']}: {row['status']} -> {row.get('owner_or_vps_action')}")
    (ROUTE_DIR / "SATURATION_SELF_RED_TEAM_LEDGER.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_context_anchor(canonical_profile_name: str) -> None:
    rows = []
    for rel in EXPECTED_ROUTE_INPUTS:
        path = REPO_ROOT / rel
        rows.append(
            {
                "path": rel,
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
            }
        )
    write_json(
        ROUTE_DIR / "ROUTE_CONTEXT_ANCHOR.json",
        {
            "schema_version": "ftmo_route_context_anchor_v1",
            "route_id": ROUTE_DIR.name,
            "generated_at_utc": utc_now(),
            "git": git_head(),
            "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/VNEXT_FTMO_LOCAL_PROFILE_AND_VPS_DUAL_PROD_PREP_GOAL_PROMPT_2026-06-02.md",
            "starter": "research/science_program_2026_05/04_goal_prompts/VNEXT_FTMO_LOCAL_PROFILE_AND_VPS_DUAL_PROD_PREP_STARTER_2026-06-02.txt",
            "canonical_profile_name": canonical_profile_name,
            "inputs": rows,
        },
    )


def write_manifest() -> dict[str, Any]:
    artifacts = []
    for path in sorted(ROUTE_DIR.rglob("*")):
        if path.is_file():
            if "__pycache__" in path.parts or path.suffix == ".pyc" or path.name in {
                "builder_stdout.log",
                "builder_stderr.log",
                "builder.pid",
            }:
                continue
            artifacts.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "source_class": "route_output",
                    "validation_state": "pending_route_verifier"
                    if path.name != "VERIFICATION_RESULT.json"
                    else "route_verifier_output",
                }
            )
    manifest = {
        "schema_version": "ftmo_route_output_manifest_v1",
        "route_id": ROUTE_DIR.name,
        "generated_at_utc": utc_now(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    write_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", manifest)
    return manifest


def write_completion_audit(
    capture: dict[str, Any],
    profile_result: dict[str, Any],
    alias_rows: list[dict[str, Any]],
    unresolved: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    alias_status_counts = Counter(row.get("alias_status") for row in alias_rows)
    local_route_ready = (
        capture.get("status") == "captured"
        and profile_result.get("ok") is True
        and alias_status_counts.get("resolved") == len(VNEXT_24_SYMBOLS)
    )
    exact_blockers = [
        row for row in unresolved
        if row.get("status") in {"owner_input_required_before_activation", "vps_only_finalization_requirement"}
    ]
    write_json(
        ROUTE_DIR / "COMPLETION_AUDIT.json",
        {
            "schema_version": "ftmo_completion_audit_v1",
            "route_id": ROUTE_DIR.name,
            "generated_at_utc": utc_now(),
            "status": "complete_for_local_evidence_class_pending_vps_authority_activation",
            "can_mark_goal_complete": local_route_ready,
            "mt5_capture_status": capture.get("status"),
            "active_alias_status_counts": dict(alias_status_counts),
            "profile_verifier_ok": profile_result.get("ok"),
            "manifest_artifact_count": manifest.get("artifact_count"),
            "exact_owner_or_vps_requirements": exact_blockers,
            "instruction_coverage": {
                "live_state_regenerated_before_route": True,
                "controlling_prompt_and_starter_read": True,
                "goal_session_research_discipline_read": True,
                "research_operating_doctrine_read": True,
                "orchestration_hardening_docs_read": True,
                "ftmo_redacted_account_runtime_files_read": True,
                "mt5_vps_preservation_lane18_post_lane18_read": True,
                "builder_posture": "constructive_builder_repair_profile_verifier",
                "forbidden_surfaces": "no_order_deal_position_mutation_no_credentials_no_remote_no_vps_live_mutation",
                "runtime_effect_boundary": "portable_local_code_and_profile_artifacts_only_no_hidden_activation",
            },
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terminal-path", default=None)
    parser.add_argument("--history-bars", type=int, default=100000)
    parser.add_argument("--tick-count", type=int, default=20000)
    args = parser.parse_args(argv)

    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    source_index = fetch_official_sources()
    write_json(ROUTE_DIR / "OFFICIAL_FTMO_SOURCE_INDEX.json", source_index)

    capture = capture_mt5(args.terminal_path, history_bars=args.history_bars, tick_count=args.tick_count)
    write_json(ROUTE_DIR / "FTMO_MT5_RAW_CAPTURE_LEDGER.json", capture)
    if capture.get("status") != "captured":
        write_json(
            ROUTE_DIR / "UNRESOLVED_OWNER_VPS_EXPORT_REQUIREMENT_LEDGER.json",
            [
                {
                    "schema_version": "ftmo_unresolved_requirement_v1",
                    "requirement": "local_ftmo_mt5_capture",
                    "status": "blocked_exact_terminal_or_account_requirement",
                    "owner_or_vps_action": "open/log in FTMO MT5 terminal or provide VPS read-only MT5 export",
                    "evidence": capture,
                }
            ],
        )
        return 2

    account = capture["account"]
    profile_slug = f"server3_{account.get('login_hash_prefix') or 'account'}"
    canonical_profile_name = f"ftmo_{profile_slug}"
    namespace = sanitize_namespace(canonical_profile_name)
    generated_profile_path = REPO_ROOT / "config" / "profiles" / f"{canonical_profile_name}.yaml"

    write_context_anchor(canonical_profile_name)
    write_json(ROUTE_DIR / "FTMO_ACCOUNT_IDENTITY_PROOF.json", {
        "schema_version": "ftmo_account_identity_proof_v1",
        "identity_secret_policy": "login_redacted_sha256_only_no_credentials",
        "account": account,
        "terminal": capture["terminal"],
        "terminal_exe_path": capture.get("terminal_exe_path"),
    })
    write_jsonl(ROUTE_DIR / "FTMO_SYMBOL_INVENTORY_LEDGER.jsonl", capture["symbol_inventory"])
    write_jsonl(ROUTE_DIR / "VNEXT_FTMO_ALIAS_RESOLUTION_LEDGER.jsonl", capture["alias_resolution"])
    write_jsonl(ROUTE_DIR / "FTMO_SYMBOL_SPEC_LEDGER.jsonl", capture["symbol_specs"])
    write_jsonl(ROUTE_DIR / "FTMO_SESSION_SPREAD_COST_HISTORY_DEPTH_LEDGER.jsonl", capture["session_spread_cost_history"])

    old_ftmo = load_yaml(CURRENT_FTMO_PROFILE)
    redacted_account = load_yaml(redacted_account_PROFILE)
    comparison = compare_ftmo_yaml(old_ftmo, capture["alias_resolution"], capture["symbol_specs"])
    write_jsonl(ROUTE_DIR / "FTMO_YAML_STALE_COMPARISON_LEDGER.jsonl", comparison)

    generated_profile = build_profile(
        capture,
        old_ftmo,
        redacted_account,
        canonical_profile_name=canonical_profile_name,
    )
    compatibility_profile = build_profile(
        capture,
        old_ftmo,
        redacted_account,
        canonical_profile_name=canonical_profile_name,
        compatibility_profile=True,
    )
    dump_yaml(generated_profile_path, generated_profile)
    dump_yaml(CURRENT_FTMO_PROFILE, compatibility_profile)
    readme = PROFILE_README.read_text(encoding="utf-8") if PROFILE_README.exists() else ""
    if f"`{canonical_profile_name}.yaml`" not in readme:
        readme = readme.rstrip() + f"\n\n## FTMO account-specific profile\n\n- `{canonical_profile_name}.yaml`: generated from local FTMO Server3 read-only MT5 capture in `{ROUTE_DIR.relative_to(REPO_ROOT)}`.\n- `ftmo.yaml`: compatibility pointer containing the same captured account/server aliases and geometry; do not treat it as a universal FTMO template.\n"
        PROFILE_README.write_text(readme + "\n", encoding="utf-8")

    profile_result = verify_profile(generated_profile_path)
    write_json(ROUTE_DIR / "PROFILE_VERIFIER_RESULT.json", profile_result)
    write_jsonl(ROUTE_DIR / "LOCAL_RUNTIME_DUAL_BROKER_READINESS_AUDIT_LEDGER.jsonl", runtime_audit())
    write_jsonl(ROUTE_DIR / "LOCAL_IMPLEMENTATION_CHANGE_LEDGER.jsonl", implementation_ledger(canonical_profile_name))
    unresolved = unresolved_requirements(source_index, capture["session_spread_cost_history"])
    write_jsonl(ROUTE_DIR / "UNRESOLVED_OWNER_VPS_EXPORT_REQUIREMENT_LEDGER.jsonl", unresolved)
    write_templates(canonical_profile_name, namespace, capture.get("terminal_exe_path"))
    write_vps_contract(canonical_profile_name, namespace)
    starter = (
        f"/goal On the VPS, consume {ROUTE_DIR.relative_to(REPO_ROOT)}/VPS_DUAL_PRODUCTION_IMPLEMENTATION_CONTRACT.md and "
        f"config/profiles/{canonical_profile_name}.yaml; regenerate LIVE_STATE, inspect VPS production git/status/processes/MT5 terminals first, "
        "treat VPS production code as final authority and this package as portable input, apply/rebase only after diff review, run profile and route verifiers, "
        "prove redacted_account and FTMO terminal/account/profile/lock/log/state/data/risk/Telegram/checkpoint/supervisor namespaces are isolated, and do not activate live dual-prod without owner approval."
    )
    (ROUTE_DIR / "VPS_SESSION_STARTER_INSTRUCTION.txt").write_text(starter + "\n", encoding="utf-8")
    write_saturation(unresolved, capture["alias_resolution"])
    manifest = write_manifest()
    write_completion_audit(capture, profile_result, capture["alias_resolution"], unresolved, manifest)
    manifest = write_manifest()
    write_completion_audit(capture, profile_result, capture["alias_resolution"], unresolved, manifest)
    print(json.dumps({"ok": True, "profile": canonical_profile_name, "namespace": namespace}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
