"""Replay-population contracts for repaired-proxy registry scopes."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPLAY_CONTRACT_SURFACE = "src/research_infra/moonshot_repaired_proxy_replay_population.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
OHLC_ALIASES = {
    "open": {"open", "o"},
    "high": {"high", "h"},
    "low": {"low", "l"},
    "close": {"close", "c"},
}


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["replay_contract_surface"] = REPLAY_CONTRACT_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def aggregate_scope_key(row: dict[str, Any]) -> str:
    existing = row.get("aggregate_scope_key")
    if existing:
        return str(existing)
    return "|".join(
        f"{field}={row.get(field) or ''}"
        for field in ("symbol", "route_session", "horizon_id", "source_component")
    )


def normalized_header_names(header: str) -> list[str]:
    return [part.strip().lower().replace(" ", "_") for part in header.strip().split(",") if part.strip()]


def has_ohlc_columns(columns: Iterable[str]) -> bool:
    normalized = set(columns)
    for aliases in OHLC_ALIASES.values():
        if not normalized.intersection(aliases):
            return False
    return True


def source_probe_row(market_row: dict[str, Any], repo_root: Path, index: int) -> dict[str, Any]:
    rel_path = Path(str(market_row.get("source_path") or ""))
    path = repo_root / rel_path
    exists = path.exists()
    header_columns: list[str] = []
    if exists:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            header_columns = normalized_header_names(handle.readline())
    return boundary_row(
        {
            "source_probe_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-SRC-{index:05d}",
            "input_market_replay_population_row_id": market_row.get("market_replay_population_row_id"),
            "symbol": market_row.get("symbol"),
            "timeframe": market_row.get("timeframe"),
            "source_path": market_row.get("source_path"),
            "source_exists": exists,
            "header_columns": header_columns,
            "has_ohlc_columns": has_ohlc_columns(header_columns),
            "source_row_count": market_row.get("source_row_count"),
            "source_sha256": market_row.get("source_sha256"),
            "first_time": market_row.get("first_time"),
            "last_time": market_row.get("last_time"),
        }
    )


def repair_scope_rows_from_executions(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in repair_rows:
        grouped[aggregate_scope_key(row)].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, rows) in enumerate(sorted(grouped.items()), 1):
        first = rows[0]
        output.append(
            boundary_row(
                {
                    "repair_scope_contract_source_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-REPAIR-SCOPE-{index:05d}"
                    ),
                    "registry_family": "source_or_broker_geometry_repair",
                    "aggregate_scope_key": key,
                    "symbol": first.get("symbol"),
                    "route_session": first.get("route_session"),
                    "horizon_id": first.get("horizon_id"),
                    "source_component": first.get("source_component"),
                    "repair_execution_rows": len(rows),
                    "repair_execution_statuses": dict(
                        sorted(Counter(str(row.get("repair_execution_status") or "") for row in rows).items())
                    ),
                }
            )
        )
    return output


def scope_family(scope_row: dict[str, Any]) -> str:
    return str(scope_row.get("registry_family") or "source_or_broker_geometry_repair")


def scope_row_id(scope_row: dict[str, Any]) -> str | None:
    return (
        scope_row.get("default_off_scope_registry_row_id")
        or scope_row.get("avoid_scope_registry_row_id")
        or scope_row.get("repair_scope_contract_source_row_id")
    )


def replay_action(scope_row: dict[str, Any], market_row: dict[str, Any], probe_row: dict[str, Any]) -> str:
    if not probe_row.get("source_exists") or not probe_row.get("has_ohlc_columns"):
        return "SOURCE_PROBE_REPAIR_REQUIRED_BEFORE_REPLAY"
    timeframe = str(market_row.get("timeframe") or "")
    family = scope_family(scope_row)
    if family == "source_or_broker_geometry_repair":
        return "REPAIR_SCOPE_SOURCE_REPLAY_CONTEXT_READY"
    if timeframe == "M15":
        return "SCOPE_READY_FOR_M15_REPLAY_NUMERIC_PASS"
    if timeframe in {"H1", "H4", "D1"}:
        return "SCOPE_READY_FOR_CONTEXT_TIMEFRAME_FEATURE_PASS"
    return "SCOPE_READY_FOR_AUXILIARY_MARKET_CONTEXT_PASS"


def replay_scope_contract_row(
    scope_row: dict[str, Any],
    market_row: dict[str, Any],
    probe_row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    return boundary_row(
        {
            "replay_scope_contract_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-CONTRACT-{index:06d}",
            "input_registry_scope_row_id": scope_row_id(scope_row),
            "input_market_replay_population_row_id": market_row.get("market_replay_population_row_id"),
            "input_source_probe_row_id": probe_row.get("source_probe_row_id"),
            "registry_family": scope_family(scope_row),
            "aggregate_scope_key": aggregate_scope_key(scope_row),
            "symbol": scope_row.get("symbol"),
            "route_session": scope_row.get("route_session"),
            "horizon_id": scope_row.get("horizon_id"),
            "source_component": scope_row.get("source_component"),
            "market_timeframe": market_row.get("timeframe"),
            "market_source_path": market_row.get("source_path"),
            "market_source_row_count": market_row.get("source_row_count"),
            "market_first_time": market_row.get("first_time"),
            "market_last_time": market_row.get("last_time"),
            "source_exists": probe_row.get("source_exists"),
            "has_ohlc_columns": probe_row.get("has_ohlc_columns"),
            "replay_contract_action": replay_action(scope_row, market_row, probe_row),
        }
    )


def control_population_contract_row(
    market_row: dict[str, Any],
    probe_row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    if not probe_row.get("source_exists") or not probe_row.get("has_ohlc_columns"):
        action = "CONTROL_SOURCE_PROBE_REPAIR_REQUIRED"
    else:
        action = "USE_AS_CROSS_MARKET_CONTROL_POPULATION"
    return boundary_row(
        {
            "control_population_contract_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-CONTROL-{index:05d}",
            "input_market_replay_population_row_id": market_row.get("market_replay_population_row_id"),
            "input_source_probe_row_id": probe_row.get("source_probe_row_id"),
            "symbol": market_row.get("symbol"),
            "timeframe": market_row.get("timeframe"),
            "source_path": market_row.get("source_path"),
            "source_row_count": market_row.get("source_row_count"),
            "source_exists": probe_row.get("source_exists"),
            "has_ohlc_columns": probe_row.get("has_ohlc_columns"),
            "control_population_action": action,
        }
    )


def build_scope_rows_by_symbol(
    default_scope_rows: list[dict[str, Any]],
    avoid_scope_rows: list[dict[str, Any]],
    repair_scope_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in [*default_scope_rows, *avoid_scope_rows, *repair_scope_rows]:
        symbol = str(row.get("symbol") or "")
        if symbol:
            output[symbol].append(row)
    return dict(output)


def symbol_summary_rows(
    contract_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    symbols = sorted(
        {
            str(row.get("symbol") or "")
            for row in [*contract_rows, *control_rows]
            if row.get("symbol")
        }
    )
    for index, symbol in enumerate(symbols, 1):
        symbol_contracts = [row for row in contract_rows if row.get("symbol") == symbol]
        symbol_controls = [row for row in control_rows if row.get("symbol") == symbol]
        action_counts = Counter(str(row.get("replay_contract_action") or "") for row in symbol_contracts)
        control_counts = Counter(str(row.get("control_population_action") or "") for row in symbol_controls)
        output.append(
            boundary_row(
                {
                    "replay_symbol_summary_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-SYMBOL-{index:04d}",
                    "symbol": symbol,
                    "replay_scope_contract_rows": len(symbol_contracts),
                    "control_population_contract_rows": len(symbol_controls),
                    "contract_action_counts": dict(sorted(action_counts.items())),
                    "control_action_counts": dict(sorted(control_counts.items())),
                }
            )
        )
    return output


def bucket_rows(
    source_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    specs = [
        ("source_exists", source_rows, "source_exists"),
        ("has_ohlc_columns", source_rows, "has_ohlc_columns"),
        ("replay_contract_action", contract_rows, "replay_contract_action"),
        ("registry_family", contract_rows, "registry_family"),
        ("control_population_action", control_rows, "control_population_action"),
    ]
    for family, rows, field in specs:
        counter = Counter(str(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "replay_contract_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
