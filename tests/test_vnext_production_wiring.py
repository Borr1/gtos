from __future__ import annotations

import ast
import importlib.util
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from src.utils.config import apply_instrument_overrides, apply_profile_overrides


REPO_ROOT = Path(__file__).resolve().parents[1]

ACTIVATION_MAP_PATH = REPO_ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_production_replacement_activation_2026_05_26/"
    "VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_2026-05-26.json"
)
AGENT_CONFIG_PATH = REPO_ROOT / "config" / "agent_config.yaml"
START_ALL_PATH = REPO_ROOT / "start_all.bat"
WATCHDOG_PATH = REPO_ROOT / "scripts" / "watchdog.ps1"

EXACT_STAGE08_EXCLUSIONS: set[str] = set()
CURRENT_BROKER_PROFILE = "redacted_account"
EXPECTED_CURRENT_PROFILE_ALIASES = {
    "GER40": "GER30",
    "NAS100": "NDX100",
    "UKOIL_cash": "UKOUSD",
    "US30_cash": "US30",
    "USOIL_cash": "USOUSD",
}


@lru_cache(maxsize=None)
def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=None)
def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _activation_map() -> dict[str, Any]:
    return _json(ACTIVATION_MAP_PATH)


def _eligible_symbols() -> list[str]:
    return list(_activation_map()["broker_native_activation_eligible_symbols"])


def _excluded_symbols() -> set[str]:
    return set(_activation_map()["broker_native_exact_excluded_symbols"])


def _assert_no_missing(surface: str, expected: set[str], actual: set[str]) -> None:
    missing = sorted(expected - actual)
    assert not missing, f"{surface} missing symbols: {missing}"


def _python_constant(rel_path: str, name: str) -> Any:
    tree = ast.parse(_text(REPO_ROOT / rel_path), filename=rel_path)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{rel_path} does not define {name}")


def _powershell_ordered_map(path: Path, variable_name: str) -> dict[str, str]:
    text = _text(path)
    pattern = re.compile(
        rf"\${re.escape(variable_name)}\s*=\s*\[ordered\]@\{{(?P<body>.*?)^\}}",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    assert match, f"{path.relative_to(REPO_ROOT)} missing ${variable_name}"
    return {
        key: value
        for key, value in re.findall(r'"([^"]+)"\s*=\s*"([^"]*)"', match.group("body"))
    }


def _start_all_launch_symbols() -> set[str]:
    return set(re.findall(r"run_agent\.py\s+--symbol\s+([A-Za-z0-9_]+)", _text(START_ALL_PATH)))


def _live_monitor_module() -> Any:
    path = REPO_ROOT / "scripts" / "_live_monitor_iter.py"
    spec = importlib.util.spec_from_file_location("_live_monitor_iter_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _config_instrument_symbols(config: dict[str, Any]) -> set[str]:
    instruments = config.get("instruments") or {}
    assert isinstance(instruments, dict)
    return set(instruments)


def _effective_kill_zone_windows(symbol: str) -> tuple[tuple[str, str, str], ...]:
    config = _yaml(AGENT_CONFIG_PATH)
    effective = apply_instrument_overrides(config, symbol)
    kill_zones = effective.get("market", {}).get("kill_zones") or {}
    assert isinstance(kill_zones, dict), f"{symbol} missing effective kill_zones"
    return tuple(
        (str(name), str(schedule.get("start_utc")), str(schedule.get("end_utc")))
        for name, schedule in kill_zones.items()
        if isinstance(schedule, dict)
    )


def _profile_effective_config(profile_name: str, symbol: str) -> dict[str, Any]:
    base = _yaml(AGENT_CONFIG_PATH)
    profiled = apply_profile_overrides(base, profile_name)
    return apply_instrument_overrides(profiled, symbol)


def _broader_origin_windows(symbol: str) -> tuple[tuple[str, str, str], ...]:
    windows = _python_constant(
        "src/components/broader_origin_generators.py",
        "SESSION_WINDOWS",
    )
    symbol_key = symbol.upper()
    for candidate in (
        symbol,
        symbol_key,
        symbol.replace("_cash", ".cash"),
        symbol_key.replace("_CASH", ".cash"),
    ):
        if candidate in windows:
            return tuple(tuple(row) for row in windows[candidate])
    raise AssertionError(f"SESSION_WINDOWS missing {symbol}")


def _displacement_windows(symbol: str) -> tuple[tuple[str, str, str], ...]:
    zones = _python_constant("scripts/displacement_logger.py", "KILL_ZONES")
    rows = zones.get(symbol)
    assert rows, f"scripts/displacement_logger.py KILL_ZONES missing {symbol}"
    return tuple(
        (name, f"{start_h:02d}:{start_m:02d}", f"{end_h:02d}:{end_m:02d}")
        for name, start_h, start_m, end_h, end_m in rows
    )


def _heartbeat_window_pairs(symbol: str) -> tuple[tuple[str, str], ...]:
    zones = _python_constant("src/safety/heartbeat_monitor.py", "KILL_ZONES_UTC")
    return tuple(
        (f"{start[0]:02d}:{start[1]:02d}", f"{end[0]:02d}:{end[1]:02d}")
        for row_symbol, start, end in zones
        if row_symbol == symbol
    )


def _flatten_config_symbol_lists(node: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "instruments" and isinstance(value, list):
                found.update(str(item) for item in value)
            else:
                found.update(_flatten_config_symbol_lists(value))
    elif isinstance(node, list):
        for item in node:
            found.update(_flatten_config_symbol_lists(item))
    return found


def test_stage08_activation_map_defines_exact_broker_native_universe() -> None:
    activation = _activation_map()
    eligible = set(_eligible_symbols())

    assert len(eligible) == 24
    assert _excluded_symbols() == EXACT_STAGE08_EXCLUSIONS
    assert activation["activation_status_counts"] == {
        "production_replacement_active_forward_capture_required_for_actual_cost_lifecycle_truth": 24,
    }
    assert set(activation["broker_live_deployment_symbols"]) == eligible

    market_rows = activation["markets"]
    row_eligible = {
        row["symbol"]
        for row in market_rows
        if row.get("broker_market_onboarding", {}).get("eligible_for_vnext_activation")
    }
    row_excluded = {
        row["symbol"]
        for row in market_rows
        if not row.get("broker_market_onboarding", {}).get("eligible_for_vnext_activation")
    }
    assert row_eligible == eligible
    assert row_excluded == EXACT_STAGE08_EXCLUSIONS


def test_agent_config_wires_every_stage08_eligible_instrument_for_production() -> None:
    config = _yaml(AGENT_CONFIG_PATH)
    eligible = _eligible_symbols()
    instruments = config.get("instruments") or {}

    failures: list[str] = []
    for symbol in eligible:
        block = instruments.get(symbol)
        if not isinstance(block, dict):
            failures.append(f"{symbol}: missing instruments.{symbol} block")
            continue

        market = block.get("market") if isinstance(block.get("market"), dict) else {}
        risk = block.get("risk") if isinstance(block.get("risk"), dict) else {}
        kill_zones = market.get("kill_zones") if isinstance(market, dict) else None

        if block.get("trading_enabled") is not True:
            failures.append(f"{symbol}: trading_enabled is not true")
        if market.get("symbol") != symbol:
            failures.append(f"{symbol}: market.symbol is not {symbol!r}")
        if not isinstance(market.get("tick_size"), (int, float)) or market.get("tick_size") <= 0:
            failures.append(f"{symbol}: market.tick_size missing or non-positive")
        if not isinstance(kill_zones, dict) or not kill_zones:
            failures.append(f"{symbol}: market.kill_zones missing or empty")
        else:
            for session_name, session in kill_zones.items():
                if not isinstance(session, dict) or not session.get("start_utc") or not session.get("end_utc"):
                    failures.append(f"{symbol}: kill_zones.{session_name} missing start_utc/end_utc")
        if not isinstance(risk.get("contract_size"), (int, float)) or risk.get("contract_size") <= 0:
            failures.append(f"{symbol}: risk.contract_size missing or non-positive")

    assert not failures, "\n".join(failures)


def test_deployment_phase_is_live_micro_phase_3() -> None:
    config = _yaml(AGENT_CONFIG_PATH)
    assert config.get("deployment", {}).get("phase") == 3


def test_stage08_exclusions_are_not_production_instrument_blocks_enabled() -> None:
    config = _yaml(AGENT_CONFIG_PATH)
    instruments = config.get("instruments") or {}

    enabled_exclusions = sorted(
        symbol
        for symbol in _excluded_symbols()
        if isinstance(instruments.get(symbol), dict)
        and instruments[symbol].get("trading_enabled") is True
    )
    assert not enabled_exclusions, f"Stage08 broker-unavailable exclusions enabled: {enabled_exclusions}"


def test_start_all_launches_every_stage08_eligible_symbol_and_no_exclusions() -> None:
    launch_symbols = _start_all_launch_symbols()

    _assert_no_missing("start_all.bat launch lines", set(_eligible_symbols()), launch_symbols)
    assert not (_excluded_symbols() & launch_symbols)


def test_watchdog_symbol_maps_supervise_every_stage08_eligible_symbol_and_no_exclusions() -> None:
    expected = set(_eligible_symbols())
    excluded = _excluded_symbols()

    symbol_map = _powershell_ordered_map(WATCHDOG_PATH, "SymbolMap")
    tick_symbol_map = _powershell_ordered_map(WATCHDOG_PATH, "TickSymbolMap")

    _assert_no_missing("scripts/watchdog.ps1 $SymbolMap keys", expected, set(symbol_map))
    _assert_no_missing("scripts/watchdog.ps1 $TickSymbolMap keys", expected, set(tick_symbol_map))

    supervised_literals = set(symbol_map) | set(symbol_map.values()) | set(tick_symbol_map) | set(tick_symbol_map.values())
    assert not (excluded & supervised_literals)


def test_current_profile_defines_market_alias_and_risk_overlay_for_every_stage08_eligible_symbol() -> None:
    eligible = _eligible_symbols()
    failures: list[str] = []

    profile = _yaml(REPO_ROOT / "config" / "profiles" / f"{CURRENT_BROKER_PROFILE}.yaml")
    instruments = profile.get("instruments") or {}
    for symbol in eligible:
        block = instruments.get(symbol)
        if not isinstance(block, dict):
            failures.append(f"{CURRENT_BROKER_PROFILE}: missing instruments.{symbol} overlay")
            continue

        market = block.get("market") if isinstance(block.get("market"), dict) else {}
        risk = block.get("risk") if isinstance(block.get("risk"), dict) else {}
        market_alias = market.get("mt5_symbol") or market.get("symbol")

        if not market_alias:
            failures.append(f"{CURRENT_BROKER_PROFILE}: {symbol} missing market.mt5_symbol or market.symbol alias")
        if not risk:
            failures.append(f"{CURRENT_BROKER_PROFILE}: {symbol} missing non-empty risk overlay")

    assert not failures, "\n".join(failures)


def test_current_profile_overlay_matches_current_stage03_resolvable_symbols() -> None:
    eligible = set(_eligible_symbols())
    failures: list[str] = []

    profile = _yaml(REPO_ROOT / "config" / "profiles" / f"{CURRENT_BROKER_PROFILE}.yaml")
    instruments = set((profile.get("instruments") or {}))
    extra = sorted(instruments - eligible)
    missing = sorted(eligible - instruments)
    if extra:
        failures.append(f"{CURRENT_BROKER_PROFILE}: non-Stage03 profile overlays: {extra}")
    if missing:
        failures.append(f"{CURRENT_BROKER_PROFILE}: missing profile overlays: {missing}")

    assert not failures, "\n".join(failures)


def test_redacted_account_us30_alias_resolves_to_us30_cash_without_base_pseudo_sessions() -> None:
    effective = _profile_effective_config("redacted_account", "US30")
    kill_zones = effective.get("market", {}).get("kill_zones") or {}

    assert effective["market"]["symbol"] == "US30_cash"
    assert effective["market"]["requested_symbol"] == "US30"
    assert effective["market"]["mt5_symbol"] == "US30"
    assert "missing_session" not in kill_zones
    assert "off_configured_session" not in kill_zones


def test_profile_mt5_aliases_match_profile_specific_broker_contract() -> None:
    failures: list[str] = []

    for symbol in _eligible_symbols():
        expected = EXPECTED_CURRENT_PROFILE_ALIASES.get(symbol, symbol)
        effective = _profile_effective_config(CURRENT_BROKER_PROFILE, symbol)
        observed = effective.get("market", {}).get("mt5_symbol") or effective.get("market", {}).get("symbol")
        if observed != expected:
            failures.append(
                f"{CURRENT_BROKER_PROFILE}: {symbol} mt5 alias {observed!r} != {expected!r}"
            )

    assert not failures, "\n".join(failures)


def test_economic_calendar_currency_map_covers_every_stage08_eligible_symbol() -> None:
    config = _yaml(AGENT_CONFIG_PATH)
    currency_map = config.get("economic_calendar", {}).get("currency_map") or {}
    missing = [
        symbol
        for symbol in _eligible_symbols()
        if not isinstance(currency_map.get(symbol), list) or not currency_map[symbol]
    ]
    assert not missing, f"economic_calendar.currency_map missing symbols: {missing}"


def test_correlation_groups_cover_every_stage08_eligible_symbol() -> None:
    config = _yaml(AGENT_CONFIG_PATH)
    covered = _flatten_config_symbol_lists(config.get("correlation_groups") or {})
    _assert_no_missing("correlation_groups instruments", set(_eligible_symbols()), covered)


def test_sprt_halt_classes_cover_every_stage08_eligible_symbol() -> None:
    config = _yaml(AGENT_CONFIG_PATH)
    classes = config.get("sprt_halt", {}).get("per_class_thresholds") or {}
    covered = _flatten_config_symbol_lists(classes)
    _assert_no_missing("sprt_halt.per_class_thresholds instruments", set(_eligible_symbols()), covered)


def test_hard_coded_monitor_symbol_lists_cover_every_stage08_eligible_symbol_and_no_exclusions() -> None:
    expected = set(_eligible_symbols())
    excluded = _excluded_symbols()
    live_monitor = _live_monitor_module()
    monitor_surfaces: dict[str, set[str]] = {
        "src/safety/heartbeat_monitor.py KILL_ZONES_UTC": {
            row[0] for row in _python_constant("src/safety/heartbeat_monitor.py", "KILL_ZONES_UTC")
        },
        "scripts/no_data_alert_monitor.py SYMBOL_LOG_MAP": set(
            _python_constant("scripts/no_data_alert_monitor.py", "SYMBOL_LOG_MAP")
        ),
        "scripts/no_data_alert_monitor.py SYMBOL_HEARTBEAT_MAP": set(
            _python_constant("scripts/no_data_alert_monitor.py", "SYMBOL_HEARTBEAT_MAP")
        ),
        "scripts/displacement_logger.py INSTRUMENTS": set(
            _python_constant("scripts/displacement_logger.py", "INSTRUMENTS")
        ),
        "scripts/displacement_logger.py KILL_ZONES": set(
            _python_constant("scripts/displacement_logger.py", "KILL_ZONES")
        ),
        "scripts/ob_continuation_monitor.py SYMBOLS": set(
            _python_constant("scripts/ob_continuation_monitor.py", "SYMBOLS")
        ),
        "scripts/ob_continuation_monitor.py _SL_BUFFER_CONFIG": set(
            _python_constant("scripts/ob_continuation_monitor.py", "_SL_BUFFER_CONFIG")
        ),
        "scripts/monthly_decay_monitor.py DEFAULT_INSTRUMENTS": set(
            _python_constant("scripts/monthly_decay_monitor.py", "DEFAULT_INSTRUMENTS")
        ),
        "scripts/monthly_decay_monitor.py BREAKEVEN_WR": set(
            _python_constant("scripts/monthly_decay_monitor.py", "BREAKEVEN_WR")
        ),
        "src/components/ai_tools/base.py LIVE_SYMBOLS": set(
            _python_constant("src/components/ai_tools/base.py", "LIVE_SYMBOLS")
        ),
        "scripts/_live_monitor_iter.py FALLBACK_INSTRUMENTS": set(live_monitor.FALLBACK_INSTRUMENTS),
        "scripts/_live_monitor_iter.py FALLBACK_KZ_SCHEDULE": set(live_monitor.FALLBACK_KZ_SCHEDULE),
    }

    failures: list[str] = []
    for surface, symbols in monitor_surfaces.items():
        missing = sorted(expected - symbols)
        unexpected_exclusions = sorted(excluded & symbols)
        if missing:
            failures.append(f"{surface} missing symbols: {missing}")
        if unexpected_exclusions:
            failures.append(f"{surface} includes Stage08 exclusions: {unexpected_exclusions}")

    assert not failures, "\n".join(failures)


def test_live_monitor_runtime_universe_is_config_derived_and_matches_stage03_surface() -> None:
    monitor = _live_monitor_module()
    eligible = _eligible_symbols()

    assert monitor.load_monitor_universe(AGENT_CONFIG_PATH) == eligible
    assert monitor.INSTRUMENTS == eligible
    assert set(monitor.TICK_CAPTURE_DAEMONS) == {f"tick_capture_{symbol}" for symbol in eligible}
    assert set(monitor.KZ_SCHEDULE) == set(eligible)


def test_ob_continuation_sl_buffer_config_matches_effective_agent_config() -> None:
    monitor_sl_buffers = _python_constant("scripts/ob_continuation_monitor.py", "_SL_BUFFER_CONFIG")
    failures: list[str] = []

    for symbol in _eligible_symbols():
        expected_value = apply_instrument_overrides(_yaml(AGENT_CONFIG_PATH), symbol).get("risk", {}).get(
            "sl_buffer_dollars"
        )
        observed = monitor_sl_buffers.get(symbol)
        if not isinstance(observed, dict):
            failures.append(f"{symbol}: missing _SL_BUFFER_CONFIG row")
            continue
        if observed.get("mode") != "abs":
            failures.append(f"{symbol}: _SL_BUFFER_CONFIG mode {observed.get('mode')!r} != 'abs'")
        if abs(float(observed.get("value")) - float(expected_value)) > 1e-12:
            failures.append(
                f"{symbol}: _SL_BUFFER_CONFIG value {observed.get('value')!r} "
                f"!= effective risk.sl_buffer_dollars {expected_value!r}"
            )

    assert not failures, "\n".join(failures)


def test_no_stale_old_live_symbol_text_in_production_wiring_files() -> None:
    production_paths = [
        "config/agent_config.yaml",
        "config/profiles/redacted_account.yaml",
        "scripts/displacement_logger.py",
        "scripts/no_data_alert_monitor.py",
        "scripts/ob_continuation_monitor.py",
        "scripts/watchdog.ps1",
        "src/components/orchestrator.py",
        "src/safety/heartbeat_monitor.py",
        "start_all.bat",
    ]
    stale_patterns = [
        r"\ball 7\b",
        r"\ball 21\b",
        r"\b5/7\b",
        r"\b7-symbol\b",
        r"\b21-symbol\b",
        r"\bseven-symbol\b",
        r"\bseven orchestrators\b",
        r"\b21 orchestrators\b",
        r"Stage08 verified 21",
        r"\bseven known\b",
        r"Other 3 instruments",
        r"live-observe",
    ]

    failures: list[str] = []
    for rel_path in production_paths:
        text = _text(REPO_ROOT / rel_path)
        for pattern in stale_patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                failures.append(f"{rel_path}: stale old-live wording matched {pattern!r}")

    assert not failures, "\n".join(failures)


def test_effective_instrument_kill_zones_do_not_inherit_base_pseudo_sessions() -> None:
    failures: list[str] = []
    crypto_24h_symbols = {"BTCUSD", "ETHUSD"}

    for symbol in _eligible_symbols():
        effective = apply_instrument_overrides(_yaml(AGENT_CONFIG_PATH), symbol)
        kill_zones = effective.get("market", {}).get("kill_zones") or {}
        if "missing_session" in kill_zones:
            failures.append(f"{symbol}: inherited missing_session into effective config")
        if symbol in crypto_24h_symbols:
            expected = {
                "off_configured_session": {
                    "start_utc": "00:00",
                    "end_utc": "23:59",
                    "core_end_utc": "23:59",
                }
            }
            if kill_zones != expected:
                failures.append(f"{symbol}: expected explicit 24h crypto contract, got {kill_zones}")
        elif "off_configured_session" in kill_zones:
            failures.append(f"{symbol}: inherited off_configured_session outside explicit crypto 24h contract")

    assert not failures, "\n".join(failures)


def test_effective_session_windows_match_broader_origin_and_monitoring_contracts() -> None:
    failures: list[str] = []

    for symbol in _eligible_symbols():
        effective_windows = _effective_kill_zone_windows(symbol)
        broader_windows = _broader_origin_windows(symbol)
        displacement_windows = _displacement_windows(symbol)
        heartbeat_pairs = _heartbeat_window_pairs(symbol)

        if effective_windows != broader_windows:
            failures.append(
                f"{symbol}: effective config windows {effective_windows} != broader-origin {broader_windows}"
            )
        if effective_windows != displacement_windows:
            failures.append(
                f"{symbol}: effective config windows {effective_windows} != displacement logger {displacement_windows}"
            )

        effective_pairs = tuple((start, end) for _, start, end in effective_windows)
        if effective_pairs != heartbeat_pairs:
            failures.append(
                f"{symbol}: effective window pairs {effective_pairs} != heartbeat monitor {heartbeat_pairs}"
            )

    assert not failures, "\n".join(failures)


def test_news_filter_affected_currencies_cover_stage08_currency_union() -> None:
    config = _yaml(AGENT_CONFIG_PATH)
    currency_map = config.get("economic_calendar", {}).get("currency_map") or {}
    expected_currencies: set[str] = set()
    for symbol in _eligible_symbols():
        expected_currencies.update(currency_map.get(symbol) or [])

    affected = set(config.get("news_filter", {}).get("affected_currencies") or [])
    _assert_no_missing("news_filter.affected_currencies", expected_currencies, affected)
