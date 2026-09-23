from __future__ import annotations

import json
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from typing import Any

from build_vnext_replacement_stage13_full_moonshot_production_selector import (
    canonical_symbol,
    production_route_session_for_row,
)


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_redacted_account_broker_risk_geometry"

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]

BROKER_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_BROKER_MARKET_ONBOARDING_LEDGER_{DATE}.jsonl"
BROKER_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
SELECTOR_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
REPAIRED_BRANCH_ALLOWLIST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_REPAIRED_BRANCH_ALLOWLIST_{DATE}.json"
BROADER_ORIGIN_ALLOWLIST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"
CONDITION_CELL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_CELL_LEDGER_{DATE}.jsonl"
ACTIVATION_EXCLUSION_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_ACTIVATION_EXCLUSION_LEDGER_{DATE}.jsonl"
BROADER_CONTRACT_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_CONTRACT_LEDGER_{DATE}.jsonl"
AGENT_CONFIG = REPO_ROOT / "config/agent_config.yaml"
redacted_account_PROFILE = REPO_ROOT / "config/profiles/redacted_account.yaml"
ACCOUNT_HISTORY_DIR = REPO_ROOT / "data/account_history"

BROKER_SPEC_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_SPEC_LEDGER_{DATE}.jsonl"
EFFECTIVE_CONFIG_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_EFFECTIVE_CONFIG_LEDGER_{DATE}.jsonl"
SELECTED_CELL_RISK_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_SELECTED_CELL_RISK_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_BROKER_RISK_GEOMETRY_SUMMARY_{DATE}.json"
COMMISSION_EVIDENCE_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_redacted_account_COMMISSION_EVIDENCE_LEDGER_{DATE}.jsonl"

REQUIRED_BROKER_GEOMETRY_FIELDS = (
    "digits",
    "spread",
    "trade_tick_size",
    "trade_tick_value",
    "trade_tick_value_profit",
    "trade_tick_value_loss",
    "trade_contract_size",
    "volume_min",
    "volume_step",
    "volume_max",
    "trade_stops_level",
    "trade_freeze_level",
    "point",
    "trade_exemode",
    "filling_mode",
    "order_mode",
    "trade_calc_mode",
    "expiration_mode",
)

redacted_account_INITIAL_BALANCE = 100000.0
redacted_account_DAILY_LOSS_LIMIT_PCT = 5.0
redacted_account_STATIC_MAX_LOSS_PCT = 10.0
redacted_account_RESET_TZ = "GMT+3"

EXECUTION_CRITICAL_UNRESOLVED_PREFIXES = (
    "digits_",
    "filling_mode_",
    "order_mode_",
    "price_rounding_",
    "lot_rounding_",
    "spread_p95_",
)

EXECUTION_CRITICAL_UNRESOLVED_EXACT = {
    "eligible_symbol_has_missing_broker_geometry_field_no_default_substitution_allowed",
    "old_three_repaired_branch_allowlist_side_not_dimensioned",
    "selected_cell_sl_distance_distribution_missing_or_incomplete",
}

COMMISSION_SYMBOL_INFO_ABSENT_REASON = (
    "commission_fields_not_exposed_in_current_symbol_info_snapshot"
)
COMMISSION_SYMBOL_INFO_ABSENT_POLICY = (
    "symbol_info_commission_fields_absent_live_pretrade_cost_model_and_deal_capture_required"
)


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def iter_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return iter_jsonl(path)


def commission_symbol_aliases(symbol: Any) -> set[str]:
    raw = str(symbol or "")
    upper = raw.upper().replace(".", "_")
    aliases = {raw, upper}
    if upper == "US30":
        aliases.add("US30_cash")
    if upper == "US30_CASH":
        aliases.add("US30")
    if upper == "NDX100":
        aliases.add("NAS100")
    if upper == "NAS100":
        aliases.add("NDX100")
    return {alias for alias in aliases if alias}


def build_commission_evidence_rows() -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for path in sorted(ACCOUNT_HISTORY_DIR.glob("mt5_deals_*.jsonl")):
        for row in iter_jsonl_if_exists(path):
            commission = row.get("commission")
            volume = row.get("volume")
            symbol = row.get("symbol")
            if commission is None or volume in (None, "") or not symbol:
                continue
            try:
                volume_f = float(volume)
                commission_f = float(commission)
            except (TypeError, ValueError):
                continue
            if volume_f <= 0:
                continue
            for alias in commission_symbol_aliases(symbol):
                bucket = grouped.setdefault(
                    alias,
                    {
                        "symbol": alias,
                        "record_type": "redacted_account_commission_evidence",
                        "schema_version": "vnext_replacement_stage13_redacted_account_commission_evidence_v1",
                        "route_id": ROUTE_ID,
                        "stage_id": STAGE_ID,
                        "source_paths": Counter(),
                        "source_symbols": Counter(),
                        "deal_rows": 0,
                        "entry_deal_rows": 0,
                        "volume_sum": 0.0,
                        "abs_commission_sum": 0.0,
                        "max_abs_commission_per_lot": 0.0,
                    },
                )
                bucket["deal_rows"] += 1
                if row.get("entry") == 0:
                    bucket["entry_deal_rows"] += 1
                bucket["volume_sum"] += volume_f
                bucket["abs_commission_sum"] += abs(commission_f)
                bucket["max_abs_commission_per_lot"] = max(
                    float(bucket["max_abs_commission_per_lot"]),
                    abs(commission_f) / volume_f,
                )
                bucket["source_paths"][rel(path)] += 1
                bucket["source_symbols"][str(symbol)] += 1
    evidence_rows: list[dict[str, Any]] = []
    for symbol, bucket in sorted(grouped.items()):
        volume_sum = float(bucket["volume_sum"])
        row = dict(bucket)
        row["source_paths"] = dict(sorted(bucket["source_paths"].items()))
        row["source_symbols"] = dict(sorted(bucket["source_symbols"].items()))
        row["avg_abs_commission_per_lot"] = (
            float(bucket["abs_commission_sum"]) / volume_sum if volume_sum > 0 else None
        )
        row["commission_model_status"] = "resolved_from_local_mt5_account_history"
        evidence_rows.append(row)
    return evidence_rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment guard
        raise SystemExit(f"PyYAML is required to read {rel(path)}: {exc}") from exc
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = deepcopy(base)
        for key, value in override.items():
            merged[key] = deep_merge(merged.get(key), value)
        return merged
    if override is None:
        return deepcopy(base)
    return deepcopy(override)


def source_for_field(
    field: str,
    base_global: dict[str, Any],
    profile_global: dict[str, Any],
    base_symbol: dict[str, Any],
    profile_symbol: dict[str, Any],
) -> str:
    if field in profile_symbol:
        return "redacted_account_symbol_profile"
    if field in profile_global:
        return "redacted_account_global_profile"
    if field in base_symbol:
        return "base_symbol_config"
    if field in base_global:
        return "base_global_config"
    return "missing"


def decimal_places(value: Any) -> int | None:
    if value is None:
        return None
    try:
        exponent = Decimal(str(value)).normalize().as_tuple().exponent
    except (InvalidOperation, ValueError):
        return None
    return int(max(0, -exponent))


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def positive_number(value: Any) -> bool:
    try:
        return value is not None and float(value) > 0.0
    except (TypeError, ValueError):
        return False


def metric_positive(metrics: dict[str, Any]) -> bool:
    rows = int(metrics.get("performance_rows") or metrics.get("selected_count") or 0)
    return rows > 0 and positive_number(metrics.get("expectancy_r")) and positive_number(metrics.get("profit_factor"))


def selected_metrics(entry: dict[str, Any]) -> dict[str, Any]:
    metrics = entry.get("repaired_branch_metrics") or entry.get("metrics") or {}
    return dict(metrics) if isinstance(metrics, dict) else {}


def compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "selected_count",
        "performance_rows",
        "wins",
        "win_rate",
        "gross_win_r",
        "gross_loss_r",
        "total_r",
        "expectancy_r",
        "profit_factor",
    )
    return {key: metrics.get(key) for key in keys}


def utc_hour_bucket_from_timestamp(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        from datetime import datetime, timezone

        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return None
    return f"h{parsed.hour:02d}_{(parsed.hour + 1) % 24:02d}"


def risk_cell_key_from_entry(entry: dict[str, Any]) -> tuple[str, str, str, str, str]:
    family = str(entry.get("origin_family") or entry.get("candidate_origin_family") or "").removeprefix("origin_")
    return (
        family,
        canonical_symbol(entry.get("symbol")),
        str(entry.get("route_session") or entry.get("session_bucket") or ""),
        str(entry.get("side") or ""),
        str(entry.get("utc_hour_bucket") or ""),
    )


def risk_cell_key_from_broader_row(row: dict[str, Any]) -> tuple[str, str, str, str, str] | None:
    symbol = canonical_symbol(row.get("symbol"))
    side = str(row.get("side") or "")
    family = str(row.get("origin_family") or "").removeprefix("origin_")
    route_session, session_allowed, _session_status = production_route_session_for_row(row)
    hour_bucket = ""
    if not session_allowed:
        hour_bucket = utc_hour_bucket_from_timestamp(row.get("decision_time_utc") or row.get("candle_time_utc")) or ""
        route_session = f"moonshot_{hour_bucket}" if hour_bucket else "moonshot_extended_unbucketed"
    return (family, symbol, str(route_session), side, hour_bucket)


def empty_cell_stats(status: str, reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "rows": 0,
        "reason": reason,
        "sl_distance_distribution": None,
        "same_bar_ambiguity_rows": 0,
        "selected_policy_exit_reason_counts": {},
        "source_mode_counts": {},
    }


def build_broader_cell_stats(selected_entries: list[dict[str, Any]]) -> dict[tuple[str, str, str, str, str], dict[str, Any]]:
    selected_keys = {risk_cell_key_from_entry(entry) for entry in selected_entries}
    values: dict[tuple[str, str, str, str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "rows": 0,
            "sl_distances": [],
            "same_bar_ambiguity_rows": 0,
            "selected_policy_exit_reason_counts": Counter(),
            "source_mode_counts": Counter(),
        }
    )
    if not BROADER_CONTRACT_LEDGER.exists():
        return {}
    for row in iter_jsonl(BROADER_CONTRACT_LEDGER):
        if row.get("row_type") != "candidate_contract":
            continue
        if row.get("activation_ready") is not True:
            continue
        if row.get("origin_native_dynamic_final_r") is None:
            continue
        key = risk_cell_key_from_broader_row(row)
        if key not in selected_keys:
            continue
        entry = values[key]
        entry["rows"] += 1
        try:
            entry_price = float(row.get("entry_price"))
            stop_price = float(row.get("stop_or_invalidation"))
            sl_distance = abs(entry_price - stop_price)
        except (TypeError, ValueError):
            sl_distance = 0.0
        if sl_distance > 0:
            entry["sl_distances"].append(sl_distance)
        replay = row.get("origin_native_dynamic_policy_replay") or {}
        if replay.get("selected_policy_same_bar_ambiguity"):
            entry["same_bar_ambiguity_rows"] += 1
        exit_reason = replay.get("selected_policy_exit_reason") or "missing_exit_reason"
        entry["selected_policy_exit_reason_counts"][str(exit_reason)] += 1
        entry["source_mode_counts"][str(row.get("source_path") or "missing_source_path")] += 1

    output: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for key, raw in values.items():
        distances = raw["sl_distances"]
        rows = int(raw["rows"])
        output[key] = {
            "status": "available_from_broader_origin_candidate_contract_rows"
            if rows and len(distances) == rows
            else "incomplete_sl_distance_distribution",
            "rows": rows,
            "sl_distance_distribution": {
                "min": min(distances) if distances else None,
                "p10": percentile(distances, 0.10),
                "p50": percentile(distances, 0.50),
                "p90": percentile(distances, 0.90),
                "p95": percentile(distances, 0.95),
                "max": max(distances) if distances else None,
                "sample_rows": len(distances),
            },
            "same_bar_ambiguity_rows": int(raw["same_bar_ambiguity_rows"]),
            "selected_policy_exit_reason_counts": dict(sorted(raw["selected_policy_exit_reason_counts"].items())),
            "source_mode_counts": dict(raw["source_mode_counts"].most_common(10)),
        }
    return output


def build_broker_spec_rows(
    broker_rows: list[dict[str, Any]],
    exclusion_rows: list[dict[str, Any]],
    commission_evidence_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    exclusion_by_symbol = {
        row.get("symbol"): row
        for row in exclusion_rows
        if row.get("record_type") == "activation_exclusion" and row.get("exclusion_scope") == "market"
    }
    output: list[dict[str, Any]] = []
    commission_by_symbol = {str(row.get("symbol")): row for row in commission_evidence_rows}
    for index, row in enumerate(broker_rows, start=1):
        selected = row.get("selected_alias_check") or {}
        metadata = selected.get("contract_metadata") or {}
        tick = selected.get("tick") or {}
        spread_evidence = selected.get("spread_evidence") or {}
        order_mode_decoded = selected.get("order_mode_decoded") or {}
        filling_mode_decoded = selected.get("filling_mode_decoded") or {}
        swap_fields = selected.get("swap_fields") or {}
        commission_fields = selected.get("commission_fields") or {}
        symbol = row.get("symbol")
        broker_alias = row.get("broker_symbol")
        commission_evidence = (
            commission_by_symbol.get(str(symbol))
            or commission_by_symbol.get(str(broker_alias))
            or {}
        )
        broker_status = row.get("broker_contract_status")
        eligible = bool(row.get("eligible_for_vnext_activation"))
        exact_unresolved: list[str] = []
        exact_excluded: list[str] = []

        if not eligible:
            reason = row.get("exact_exclusion_reason") or broker_status or "not_eligible_for_vnext_activation"
            exact_excluded.append(str(reason))
        for field in REQUIRED_BROKER_GEOMETRY_FIELDS:
            if metadata.get(field) is None:
                exact_unresolved.append(f"{field}_missing_from_selected_broker_contract_metadata")
        if metadata.get("filling_mode") is None:
            exact_unresolved.append("filling_mode_missing_from_selected_broker_contract_metadata")
        if metadata.get("digits") is None:
            exact_unresolved.append("digits_not_captured_by_current_broker_onboarding_ledger")
        if metadata.get("order_mode") is None:
            exact_unresolved.append("order_mode_not_captured_by_current_broker_onboarding_ledger")
        if metadata.get("trade_exemode") is None:
            exact_unresolved.append("trade_exemode_not_captured_by_current_broker_onboarding_ledger")
        if spread_evidence.get("tick_history_p95_points") is None:
            exact_unresolved.append("spread_p95_not_captured_from_tick_history")
        commission_cost_policy = (
            "symbol_info_commission_fields_captured"
            if commission_fields
            else "local_mt5_account_history_commission_model_captured"
            if commission_evidence
            else COMMISSION_SYMBOL_INFO_ABSENT_POLICY
        )
        # MT5 commonly does not expose commission in symbol_info. That source
        # fact is preserved in commission_source_status/cost_policy, while live
        # execution still runs quote spread/cost pretrade validation before
        # order readiness.

        point = metadata.get("point")
        trade_tick_size = metadata.get("trade_tick_size")
        volume_step = metadata.get("volume_step")
        stops_level = metadata.get("trade_stops_level")
        freeze_level = metadata.get("trade_freeze_level")
        price_rounding_source = "broker_trade_tick_size" if positive_number(trade_tick_size) else "broker_point"
        price_rounding_increment = trade_tick_size if positive_number(trade_tick_size) else point
        lot_rounding_increment = volume_step

        if not positive_number(price_rounding_increment):
            exact_unresolved.append("price_rounding_increment_unavailable_from_trade_tick_size_or_point")
        if not positive_number(lot_rounding_increment):
            exact_unresolved.append("lot_rounding_increment_unavailable_from_volume_step")

        stop_distance = None
        freeze_distance = None
        if stops_level is not None and point is not None:
            stop_distance = float(stops_level) * float(point)
        if freeze_level is not None and point is not None:
            freeze_distance = float(freeze_level) * float(point)

        pending_market_status = (
            "market_and_pending_limit_supported_by_decoded_order_mode"
            if eligible and order_mode_decoded.get("allows_market_orders") and order_mode_decoded.get("allows_limit_orders")
            else "market_supported_pending_limit_unavailable_from_decoded_order_mode"
            if eligible and order_mode_decoded.get("allows_market_orders")
            else f"excluded_{broker_status or 'broker_contract_not_valid'}"
        )
        exclusion = exclusion_by_symbol.get(symbol) or {}
        output.append(
            {
                "alias_candidates_checked": row.get("alias_candidates_checked") or [],
                "broker_alias": broker_alias,
                "broker_contract_status": broker_status,
                "broker_field_default_used": False,
                "broker_spec_id": f"STAGE13-FN-BROKER-SPEC-{index:06d}",
                "commission_availability": (
                    "captured_from_symbol_info"
                    if commission_fields
                    else "resolved_from_local_mt5_account_history"
                    if commission_evidence
                    else "unresolved_not_exposed_in_symbol_info_snapshot"
                ),
                "commission_cost_policy": commission_cost_policy,
                "commission_source_status": (
                    "source_resolved"
                    if commission_fields or commission_evidence
                    else "non_blocking_symbol_info_absent_live_pretrade_cost_model_required"
                ),
                "commission_evidence": commission_evidence,
                "commission_fields": commission_fields,
                "contract_size": metadata.get("trade_contract_size"),
                "digits": metadata.get("digits"),
                "effective_broker_tick_size_for_rounding": price_rounding_increment,
                "eligible_for_vnext_activation": eligible,
                "exact_excluded_reasons": sorted(set(exact_excluded)),
                "exact_unresolved_reasons": sorted(set(exact_unresolved)),
                "filling_mode": metadata.get("filling_mode"),
                "filling_mode_decoded": filling_mode_decoded,
                "filling_order_mode_status": {
                    "filling_mode": metadata.get("filling_mode"),
                    "filling_mode_decoded": filling_mode_decoded,
                    "order_mode": metadata.get("order_mode"),
                    "order_mode_decoded": order_mode_decoded,
                    "order_mode_status": (
                        "captured"
                        if metadata.get("order_mode") is not None
                        else "unresolved_not_captured_by_current_broker_onboarding_ledger"
                    ),
                },
                "freeze_distance_price": freeze_distance,
                "mt5_access_status": row.get("mt5_access_status"),
                "order_mode": metadata.get("order_mode"),
                "order_mode_decoded": order_mode_decoded,
                "pending_market_behavior_status": pending_market_status,
                "point": point,
                "price_rounding_policy": {
                    "decimals_from_increment": decimal_places(price_rounding_increment),
                    "increment": price_rounding_increment,
                    "source": price_rounding_source,
                    "status": "verified_from_broker_spec" if positive_number(price_rounding_increment) else "unresolved",
                },
                "record_type": "redacted_account_broker_spec",
                "route_id": ROUTE_ID,
                "schema_version": "vnext_replacement_stage13_redacted_account_broker_spec_v1",
                "selected_alias_contract_failures": selected.get("contract_failures") or [],
                "source_activation_exclusion_id": exclusion.get("activation_exclusion_id"),
                "source_activation_exclusion_reason": exclusion.get("why_excluded"),
                "source_broker_onboarding_row_sha256": canonical_hash(row),
                "source_broker_row_index": index,
                "source_capture": row.get("source_capture") or {},
                "source_ledger_path": rel(BROKER_LEDGER),
                "spread": metadata.get("spread"),
                "spread_evidence": spread_evidence,
                "spread_float": metadata.get("spread_float"),
                "spread_mode_status": "floating_spread" if metadata.get("spread_float") else "fixed_or_unreported_spread_float_false",
                "stage_id": STAGE_ID,
                "stop_distance_price": stop_distance,
                "stops_level": stops_level,
                "swap_availability": "captured" if swap_fields else "unresolved_not_exposed_in_symbol_info_snapshot",
                "swap_fields": swap_fields,
                "symbol": symbol,
                "symbol_info_available": bool(selected.get("info_found")),
                "tick_available": bool(tick.get("available")),
                "tick_size": metadata.get("trade_tick_size"),
                "tick_value": metadata.get("trade_tick_value"),
                "trade_calc_mode": metadata.get("trade_calc_mode"),
                "trade_exemode": metadata.get("trade_exemode"),
                "trade_freeze_level": freeze_level,
                "trade_contract_size": metadata.get("trade_contract_size"),
                "trade_tick_value_loss": metadata.get("trade_tick_value_loss"),
                "trade_tick_value_profit": metadata.get("trade_tick_value_profit"),
                "trade_stops_level": stops_level,
                "trade_tick_size": trade_tick_size,
                "trade_tick_value": metadata.get("trade_tick_value"),
                "expiration_mode": metadata.get("expiration_mode"),
                "volume_max": metadata.get("volume_max"),
                "volume_min": metadata.get("volume_min"),
                "volume_rounding_policy": {
                    "clamp_max": metadata.get("volume_max"),
                    "clamp_min": metadata.get("volume_min"),
                    "decimals_from_step": decimal_places(lot_rounding_increment),
                    "step": lot_rounding_increment,
                    "status": "verified_from_broker_spec" if positive_number(lot_rounding_increment) else "unresolved",
                },
                "volume_step": volume_step,
            }
        )
    return output


def build_effective_config_rows(
    broker_spec_rows: list[dict[str, Any]],
    agent_config: dict[str, Any],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    base_global_risk = agent_config.get("risk") or {}
    profile_global_risk = profile.get("risk") or {}
    effective_global_risk = deep_merge(base_global_risk, profile_global_risk)
    base_global_drawdown = agent_config.get("drawdown_reduction") or {}
    profile_global_drawdown = profile.get("drawdown_reduction") or {}
    effective_drawdown = deep_merge(base_global_drawdown, profile_global_drawdown)
    base_instruments = agent_config.get("instruments") or {}
    profile_instruments = profile.get("instruments") or {}

    output: list[dict[str, Any]] = []
    for index, broker in enumerate(broker_spec_rows, start=1):
        symbol = broker["symbol"]
        base_block = base_instruments.get(symbol) or {}
        profile_block = profile_instruments.get(symbol) or {}
        effective_block = deep_merge(base_block, profile_block)
        base_market = (base_block.get("market") or {}) if isinstance(base_block, dict) else {}
        profile_market = (profile_block.get("market") or {}) if isinstance(profile_block, dict) else {}
        effective_market = effective_block.get("market") or {}
        base_symbol_risk = (base_block.get("risk") or {}) if isinstance(base_block, dict) else {}
        profile_symbol_risk = (profile_block.get("risk") or {}) if isinstance(profile_block, dict) else {}
        effective_symbol_risk = effective_block.get("risk") or {}

        def risk_value(key: str) -> Any:
            if key in effective_symbol_risk:
                return effective_symbol_risk.get(key)
            return effective_global_risk.get(key)

        def risk_source(key: str) -> str:
            return source_for_field(
                key,
                base_global_risk,
                profile_global_risk,
                base_symbol_risk,
                profile_symbol_risk,
            )

        profile_alias = profile_market.get("mt5_symbol")
        effective_mt5_symbol = effective_market.get("mt5_symbol") or effective_market.get("symbol") or symbol
        broker_tick = broker.get("trade_tick_size")
        broker_point = broker.get("point")
        config_tick = effective_market.get("tick_size")
        effective_price_increment = broker_tick if positive_number(broker_tick) else (config_tick or broker_point)
        sl_min_ticks = risk_value("sl_buffer_min_ticks")
        sl_buffer_min_price = None
        if sl_min_ticks is not None and effective_price_increment is not None:
            sl_buffer_min_price = float(sl_min_ticks) * float(effective_price_increment)
        stop_distance = broker.get("stop_distance_price")
        freeze_distance = broker.get("freeze_distance_price")
        required_geometry_missing = [
            field
            for field in REQUIRED_BROKER_GEOMETRY_FIELDS
            if broker.get(field) is None
        ]
        uses_unverified_default = bool(broker.get("eligible_for_vnext_activation") and required_geometry_missing)
        exact_reasons = list(broker.get("exact_unresolved_reasons") or [])
        if uses_unverified_default:
            exact_reasons.append(
                "eligible_symbol_has_missing_broker_geometry_field_no_default_substitution_allowed"
            )

        output.append(
            {
                "base_config_instrument_present": bool(base_block),
                "broker_alias": broker.get("broker_alias"),
                "broker_contract_size": broker.get("contract_size"),
                "broker_freeze_distance_price": freeze_distance,
                "broker_point": broker_point,
                "broker_spec_id": broker.get("broker_spec_id"),
                "broker_spec_status": broker.get("broker_contract_status"),
                "broker_stop_distance_price": stop_distance,
                "broker_tick_size": broker_tick,
                "broker_volume_max": broker.get("volume_max"),
                "broker_volume_min": broker.get("volume_min"),
                "broker_volume_step": broker.get("volume_step"),
                "configured_contract_size": risk_value("contract_size"),
                "configured_market_tick_size": config_tick,
                "configured_max_spread_cents": risk_value("max_spread_cents"),
                "configured_min_rr": effective_global_risk.get("min_rr"),
                "configured_sl_absolute_min": risk_value("sl_absolute_min"),
                "configured_sl_buffer_dollars": risk_value("sl_buffer_dollars"),
                "drawdown_reduced_risk_pct": effective_drawdown.get("reduced_risk_pct"),
                "drawdown_threshold": effective_drawdown.get("threshold"),
                "effective_broker_bound_freeze_distance_price": freeze_distance,
                "effective_broker_bound_stop_distance_price": stop_distance,
                "effective_lot_rounding_step": broker.get("volume_step"),
                "effective_market_symbol": effective_market.get("symbol") or symbol,
                "effective_max_concurrent": effective_global_risk.get("max_concurrent"),
                "effective_max_daily_loss_pct": effective_global_risk.get("max_daily_loss_pct"),
                "effective_mt5_symbol": effective_mt5_symbol,
                "effective_price_rounding_increment": effective_price_increment,
                "configured_profile_risk_per_trade_pct": risk_value("risk_per_trade_pct"),
                "effective_risk_per_trade_pct": risk_value("risk_per_trade_pct"),
                "effective_sl_buffer_atr_multiplier": risk_value("sl_buffer_atr_multiplier"),
                "effective_sl_buffer_breaker_atr_multiplier": risk_value("sl_buffer_breaker_atr_multiplier"),
                "effective_sl_buffer_min_ticks": sl_min_ticks,
                "effective_sl_buffer_min_price": sl_buffer_min_price,
                "exact_unresolved_reasons": sorted(set(exact_reasons)),
                "profile_alias": profile_alias,
                "profile_config_instrument_present": bool(profile_block),
                "profile_name": profile.get("profile_name"),
                "prop_firm_rules": {
                    "daily_loss_limit_pct": redacted_account_DAILY_LOSS_LIMIT_PCT,
                    "static_max_loss_from_initial_balance_pct": redacted_account_STATIC_MAX_LOSS_PCT,
                    "reset_timezone": redacted_account_RESET_TZ,
                },
                "record_type": "redacted_account_effective_config",
                "required_broker_geometry_missing": required_geometry_missing,
                "risk_field_sources": {
                    "contract_size": risk_source("contract_size"),
                    "max_spread_cents": risk_source("max_spread_cents"),
                    "risk_per_trade_pct": risk_source("risk_per_trade_pct"),
                    "sl_absolute_min": risk_source("sl_absolute_min"),
                    "sl_buffer_atr_multiplier": risk_source("sl_buffer_atr_multiplier"),
                    "sl_buffer_breaker_atr_multiplier": risk_source("sl_buffer_breaker_atr_multiplier"),
                    "sl_buffer_dollars": risk_source("sl_buffer_dollars"),
                    "sl_buffer_min_ticks": risk_source("sl_buffer_min_ticks"),
                },
                "risk_geometry_status": (
                    "broker_native_geometry_bound"
                    if broker.get("eligible_for_vnext_activation") and not required_geometry_missing
                    else "excluded_or_missing_broker_geometry"
                ),
                "route_id": ROUTE_ID,
                "schema_version": "vnext_replacement_stage13_redacted_account_effective_config_v1",
                "source_agent_config_hash": file_sha256(AGENT_CONFIG),
                "source_agent_config_path": rel(AGENT_CONFIG),
                "source_broker_spec_id": broker.get("broker_spec_id"),
                "source_redacted_account_profile_hash": file_sha256(redacted_account_PROFILE),
                "source_redacted_account_profile_path": rel(redacted_account_PROFILE),
                "stage_id": STAGE_ID,
                "symbol": symbol,
                "trading_enabled": bool(effective_block.get("trading_enabled", False)),
                "uses_unverified_default": uses_unverified_default,
            }
        )
    return output


def condition_index(condition_rows: list[dict[str, Any]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    index: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in condition_rows:
        key = (
            str(row.get("family") or ""),
            str(row.get("symbol") or ""),
            str(row.get("session_bucket") or ""),
            str(row.get("side") or ""),
        )
        index[key] = row
    return index


def execution_critical_unresolved(reasons: list[str]) -> list[str]:
    critical: list[str] = []
    for reason in reasons:
        if reason in EXECUTION_CRITICAL_UNRESOLVED_EXACT:
            critical.append(reason)
            continue
        if any(reason.startswith(prefix) for prefix in EXECUTION_CRITICAL_UNRESOLVED_PREFIXES):
            critical.append(reason)
    return sorted(set(critical))


def spread_slippage_sensitivity(broker: dict[str, Any], sl_stats: dict[str, Any]) -> dict[str, Any]:
    spread_evidence = broker.get("spread_evidence") or {}
    sl_distribution = sl_stats.get("sl_distance_distribution") or {}
    point = broker.get("point")
    spread_points = spread_evidence.get("tick_history_p95_points")
    if spread_points is None:
        spread_points = spread_evidence.get("current_spread_points") or broker.get("spread")
    try:
        spread_price = float(spread_points) * float(point)
    except (TypeError, ValueError):
        spread_price = None
    try:
        sl_p50 = float(sl_distribution.get("p50"))
    except (TypeError, ValueError):
        sl_p50 = None
    ratio = spread_price / sl_p50 if spread_price is not None and sl_p50 and sl_p50 > 0 else None
    return {
        "basis": "tick_history_p95_spread_points_over_cell_median_sl_distance",
        "spread_points": spread_points,
        "spread_price": spread_price,
        "sl_distance_p50": sl_p50,
        "spread_to_sl_p50_ratio": ratio,
    }


def choose_evidence_risk_pct(metrics: dict[str, Any], sensitivity: dict[str, Any]) -> dict[str, Any]:
    rows = int(metrics.get("performance_rows") or metrics.get("selected_count") or 0)
    try:
        expectancy = float(metrics.get("expectancy_r"))
        profit_factor = float(metrics.get("profit_factor"))
        win_rate = float(metrics.get("win_rate") or 0.0)
    except (TypeError, ValueError):
        return {
            "risk_pct": 0.0,
            "risk_decision_basis": "risk_zero_metrics_not_numeric",
            "risk_policy_thresholds": {},
        }

    risk_pct = 0.25
    tier = "micro_positive_ev_floor"
    if rows >= 250 and expectancy >= 0.25 and profit_factor >= 1.5:
        risk_pct = 0.50
        tier = "moderate_positive_ev_rows_pf_expectancy"
    if rows >= 500 and expectancy >= 0.35 and profit_factor >= 2.0:
        risk_pct = 0.75
        tier = "strong_positive_ev_rows_pf_expectancy"
    if rows >= 1000 and expectancy >= 0.45 and profit_factor >= 2.5 and win_rate >= 0.50:
        risk_pct = 1.00
        tier = "maximum_evidence_backed_redacted_account_cell_risk"

    ratio = sensitivity.get("spread_to_sl_p50_ratio")
    spread_cap = "no_spread_cap"
    if ratio is None:
        return {
            "risk_pct": 0.0,
            "risk_decision_basis": "risk_zero_spread_to_sl_sensitivity_unavailable",
            "risk_policy_thresholds": {},
        }
    if ratio > 0.20:
        risk_pct = min(risk_pct, 0.25)
        spread_cap = "capped_to_0_25pct_for_historical_spread_cost_above_20pct_median_sl_live_pretrade_required"
    elif ratio > 0.10:
        risk_pct = min(risk_pct, 0.25)
        spread_cap = "capped_to_0_25pct_for_spread_cost_above_10pct_median_sl"
    elif ratio > 0.05:
        risk_pct = min(risk_pct, 0.50)
        spread_cap = "capped_to_0_50pct_for_spread_cost_above_5pct_median_sl"

    return {
        "risk_pct": risk_pct,
        "risk_decision_basis": f"vnext_cell_evidence_tier:{tier};{spread_cap};redacted_account_5pct_daily_10pct_static",
        "risk_policy_thresholds": {
            "rows": rows,
            "expectancy_r": expectancy,
            "profit_factor": profit_factor,
            "win_rate": win_rate,
            "spread_to_sl_p50_ratio": ratio,
            "max_cell_risk_pct": 1.0,
            "daily_loss_limit_pct": redacted_account_DAILY_LOSS_LIMIT_PCT,
            "static_max_loss_pct": redacted_account_STATIC_MAX_LOSS_PCT,
        },
    }


def expected_lot_distribution(
    risk_pct: float,
    broker: dict[str, Any],
    sl_stats: dict[str, Any],
) -> dict[str, Any]:
    distribution = sl_stats.get("sl_distance_distribution") or {}
    tick_size = broker.get("trade_tick_size")
    tick_value = broker.get("trade_tick_value")
    volume_min = broker.get("volume_min")
    volume_step = broker.get("volume_step")
    volume_max = broker.get("volume_max")
    lots: dict[str, Any] = {}
    if risk_pct <= 0:
        return {"status": "risk_zero_no_lots", "lots": lots}
    try:
        tick_size_f = float(tick_size)
        tick_value_f = float(tick_value)
        step_f = float(volume_step)
        min_f = float(volume_min)
        max_f = float(volume_max)
    except (TypeError, ValueError):
        return {"status": "broker_lot_geometry_unavailable", "lots": lots}
    risk_amount = redacted_account_INITIAL_BALANCE * (risk_pct / 100.0)
    for key in ("p10", "p50", "p90", "p95"):
        sl_distance = distribution.get(key)
        try:
            sl_f = float(sl_distance)
        except (TypeError, ValueError):
            lots[key] = None
            continue
        if sl_f <= 0 or tick_size_f <= 0 or tick_value_f <= 0 or step_f <= 0:
            lots[key] = None
            continue
        raw_lot = risk_amount / ((sl_f / tick_size_f) * tick_value_f)
        rounded = int(raw_lot / step_f) * step_f
        lots[key] = max(min_f, min(max_f, rounded))
    return {
        "status": "derived_from_cell_sl_distribution_and_broker_tick_value",
        "risk_amount_usd": risk_amount,
        "lots": lots,
    }


def make_risk_row(
    cell_index: int,
    selector_component: str,
    entry: dict[str, Any],
    broker_by_symbol: dict[str, dict[str, Any]],
    config_by_symbol: dict[str, dict[str, Any]],
    condition_by_key: dict[tuple[str, str, str, str], dict[str, Any]],
    broader_cell_stats: dict[tuple[str, str, str, str, str], dict[str, Any]],
    source_path: Path,
) -> dict[str, Any]:
    symbol = entry.get("symbol")
    broker = broker_by_symbol.get(symbol or "")
    config = config_by_symbol.get(symbol or "")
    metrics = selected_metrics(entry)
    metrics_ok = metric_positive(metrics)
    broker_ok = bool(broker and broker.get("eligible_for_vnext_activation"))
    config_ok = bool(config and not config.get("uses_unverified_default"))
    source_risk_pct = config.get("effective_risk_per_trade_pct") if config else None
    unresolved = list((broker or {}).get("exact_unresolved_reasons") or [])
    excluded = list((broker or {}).get("exact_excluded_reasons") or [])
    if not broker:
        excluded.append("missing_broker_spec_row_for_selected_cell_symbol")
    if broker and not broker_ok:
        excluded.extend(broker.get("exact_excluded_reasons") or [broker.get("broker_contract_status")])
    if not config:
        excluded.append("missing_effective_config_row_for_selected_cell_symbol")
    if config and config.get("uses_unverified_default"):
        unresolved.extend(config.get("exact_unresolved_reasons") or ["effective_config_uses_unverified_default"])
    if not metrics_ok:
        excluded.append("selector_metrics_nonpositive_or_missing_expectancy_profit_factor_or_rows")

    family = entry.get("candidate_origin_family") or entry.get("origin_family")
    session = entry.get("route_session") or entry.get("session_bucket")
    side = entry.get("side")
    cell_key = risk_cell_key_from_entry(entry)
    sl_stats = empty_cell_stats("not_applicable", "selector_component_has_no_row_level_candidate_contract_join")
    condition_row = None
    if selector_component == "broader_origin":
        sl_stats = broader_cell_stats.get(cell_key) or empty_cell_stats(
            "missing",
            "selected_broader_origin_allowlist_entry_missing_candidate_contract_join",
        )
        if sl_stats.get("status") != "available_from_broader_origin_candidate_contract_rows":
            unresolved.append("selected_cell_sl_distance_distribution_missing_or_incomplete")
        condition_row = condition_by_key.get((str(family or ""), str(symbol or ""), str(session or ""), str(side or "")))
        if condition_row is None:
            unresolved.append("condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry")
    else:
        if side is None:
            unresolved.append("old_three_repaired_branch_allowlist_side_not_dimensioned")

    critical_unresolved = execution_critical_unresolved([str(reason) for reason in unresolved])
    sensitivity = spread_slippage_sensitivity(broker or {}, sl_stats) if selector_component == "broader_origin" else {
        "basis": "unavailable_for_old_three_aggregate_allowlist_without_row_level_side_join",
        "spread_to_sl_p50_ratio": None,
    }
    risk_decision = choose_evidence_risk_pct(metrics, sensitivity) if metrics_ok else {
        "risk_pct": 0.0,
        "risk_decision_basis": "risk_zero_selector_metrics_not_positive",
        "risk_policy_thresholds": {},
    }
    risk_pct = float(risk_decision["risk_pct"]) if broker_ok and config_ok and metrics_ok and not critical_unresolved else 0.0
    if not broker_ok or not config_ok:
        risk_decision["risk_decision_basis"] = "risk_zero_until_broker_config_requirements_pass"
    elif critical_unresolved:
        risk_decision["risk_decision_basis"] = "risk_zero_execution_critical_evidence_unresolved"
    final_reasons = list(unresolved + excluded)
    if risk_pct <= 0:
        final_reasons.append(risk_decision["risk_decision_basis"])
    stale_profile_risk_without_cell_evidence = risk_pct > 0 and (
        source_risk_pct is not None and float(source_risk_pct) == risk_pct and "vnext_cell_evidence_tier" not in risk_decision["risk_decision_basis"]
    )
    expectancy = metrics.get("expectancy_r")
    total_r = metrics.get("total_r")
    risked_expectancy_pct = None
    risked_total_pct = None
    if risk_pct > 0 and expectancy is not None:
        risked_expectancy_pct = risk_pct * float(expectancy)
    if risk_pct > 0 and total_r is not None:
        risked_total_pct = risk_pct * float(total_r)

    return {
        "broker_alias": (broker or {}).get("broker_alias"),
        "broker_spec_id": (broker or {}).get("broker_spec_id"),
        "candidate_origin_family": family,
        "cell_evidence_granularity": (
            "symbol_session_side_origin_family"
            if selector_component == "broader_origin"
            else "symbol_framework_session_branch_aggregate"
        ),
        "condition_cell_id": (condition_row or {}).get("condition_cell_id"),
        "condition_cell_metrics": compact_metrics(
            ((condition_row or {}).get("metrics") or {}).get("condition_challenger_on_computable_rows") or {}
        )
        if condition_row
        else None,
        "configured_profile_risk_per_trade_pct": source_risk_pct,
        "commission_availability": (broker or {}).get("commission_availability"),
        "commission_cost_policy": (broker or {}).get("commission_cost_policy"),
        "commission_source_status": (broker or {}).get("commission_source_status"),
        "correlation_portfolio_heat_proxy": {
            "basis": "selected_cell_symbol_count_share_of_allowlist",
            "symbol": symbol,
            "note": "final portfolio heat is enforced by runtime correlation/prop governance; cell risk is capped at 1pct before portfolio state",
        },
        "dynamic_execution_sizing_policy": {
            "selected_policy": entry.get("selected_policy"),
            "be_after_trigger_replay_policy": "software_be_move_then_final_target_or_stop_from_origin_native_dynamic_replay",
            "pending_fill_policy": "risk_geometry_fields_propagate_through_pending_intent_to_open_trade",
        },
        "effective_lot_rounding_step": (config or {}).get("effective_lot_rounding_step"),
        "effective_price_rounding_increment": (config or {}).get("effective_price_rounding_increment"),
        "effective_risk_per_trade_pct": risk_pct,
        "effective_sl_buffer_min_price": (config or {}).get("effective_sl_buffer_min_price"),
        "exact_unresolved_or_excluded_reasons": sorted(set(str(reason) for reason in final_reasons if reason)),
        "family": entry.get("origin_family") or family,
        "framework": entry.get("framework"),
        "kill_zone_bucket": entry.get("kill_zone_bucket"),
        "metric_profit_factor": metrics.get("profit_factor"),
        "metric_selected_count": metrics.get("selected_count"),
        "metric_total_r": metrics.get("total_r"),
        "metric_win_rate": metrics.get("win_rate"),
        "metrics": compact_metrics(metrics),
        "nonpositive_expectancy_or_pf_for_risk_gt_zero": bool(
            risk_pct > 0 and not (positive_number(metrics.get("expectancy_r")) and positive_number(metrics.get("profit_factor")))
        ),
        "price_rounding_policy": (broker or {}).get("price_rounding_policy"),
        "profile_name": (config or {}).get("profile_name"),
        "prop_rule_pressure": {
            "daily_loss_limit_pct": redacted_account_DAILY_LOSS_LIMIT_PCT,
            "static_max_loss_from_initial_balance_pct": redacted_account_STATIC_MAX_LOSS_PCT,
            "reset_timezone": redacted_account_RESET_TZ,
            "opportunity_cost_policy": "runtime_prop_governor_compares_allow_reduce_micro_risk_defer_block_from_account_cushion_and_trade_quality",
            "cell_risk_cap_pct": 1.0,
        },
        "record_type": "redacted_account_selected_cell_risk",
        "risk_cell_id": f"STAGE13-FN-RISK-CELL-{cell_index:06d}",
        "risk_decision_basis": risk_decision["risk_decision_basis"],
        "risk_policy_thresholds": risk_decision.get("risk_policy_thresholds") or {},
        "risk_multiplier_from_cell_evidence": risk_pct / float(source_risk_pct) if risk_pct > 0 and source_risk_pct else 0.0,
        "risked_expectancy_pct": risked_expectancy_pct,
        "risked_total_pct": risked_total_pct,
        "route_id": ROUTE_ID,
        "route_session": entry.get("route_session"),
        "schema_version": "vnext_replacement_stage13_redacted_account_selected_cell_risk_v1",
        "selected_policy": entry.get("selected_policy"),
        "selector_cell_metrics_status": "positive_selector_cell_metrics" if metrics_ok else "metrics_not_positive",
        "selector_component": selector_component,
        "session_bucket": session,
        "side": side,
        "sl_distance_distribution": sl_stats.get("sl_distance_distribution"),
        "source_effective_config_status": (config or {}).get("risk_geometry_status"),
        "source_selector_entry_sha256": canonical_hash(entry),
        "source_selector_path": rel(source_path),
        "stage_id": STAGE_ID,
        "stale_old_profile_risk_without_cell_evidence": stale_profile_risk_without_cell_evidence,
        "spread_slippage_sensitivity": sensitivity,
        "symbol": symbol,
        "uses_unverified_default": bool((config or {}).get("uses_unverified_default")),
        "expected_lot_size_distribution": expected_lot_distribution(risk_pct, broker or {}, sl_stats),
        "volume_rounding_policy": (broker or {}).get("volume_rounding_policy"),
    }


def build_selected_cell_risk_rows(
    broker_spec_rows: list[dict[str, Any]],
    config_rows: list[dict[str, Any]],
    condition_rows: list[dict[str, Any]],
    repaired_allowlist: dict[str, Any],
    broader_allowlist: dict[str, Any],
) -> list[dict[str, Any]]:
    broker_by_symbol = {row["symbol"]: row for row in broker_spec_rows}
    config_by_symbol = {row["symbol"]: row for row in config_rows}
    cond_by_key = condition_index(condition_rows)
    broader_cell_stats = build_broader_cell_stats(list(broader_allowlist.get("entries") or []))
    output: list[dict[str, Any]] = []
    cell_index = 1
    for entry in repaired_allowlist.get("entries") or []:
        output.append(
            make_risk_row(
                cell_index,
                "old_three_repaired_branch",
                entry,
                broker_by_symbol,
                config_by_symbol,
                cond_by_key,
                broader_cell_stats,
                REPAIRED_BRANCH_ALLOWLIST,
            )
        )
        cell_index += 1
    for entry in broader_allowlist.get("entries") or []:
        output.append(
            make_risk_row(
                cell_index,
                "broader_origin",
                entry,
                broker_by_symbol,
                config_by_symbol,
                cond_by_key,
                broader_cell_stats,
                BROADER_ORIGIN_ALLOWLIST,
            )
        )
        cell_index += 1
    return output


def summarize(
    broker_spec_rows: list[dict[str, Any]],
    config_rows: list[dict[str, Any]],
    risk_rows: list[dict[str, Any]],
    selector_summary: dict[str, Any],
) -> dict[str, Any]:
    input_paths = [
        BROKER_LEDGER,
        BROKER_MAP,
        SELECTOR_SUMMARY,
        REPAIRED_BRANCH_ALLOWLIST,
        BROADER_ORIGIN_ALLOWLIST,
        CONDITION_CELL_LEDGER,
        ACTIVATION_EXCLUSION_LEDGER,
        AGENT_CONFIG,
        redacted_account_PROFILE,
    ]
    output_paths = [COMMISSION_EVIDENCE_LEDGER, BROKER_SPEC_LEDGER, EFFECTIVE_CONFIG_LEDGER, SELECTED_CELL_RISK_LEDGER]
    risk_positive_rows = [row for row in risk_rows if float(row.get("effective_risk_per_trade_pct") or 0.0) > 0.0]
    return {
        "schema_version": "vnext_replacement_stage13_redacted_account_broker_risk_geometry_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "deterministic_build": False,
        "status": "built",
        "input_hashes": {rel(path): file_sha256(path) for path in input_paths},
        "output_hashes": {rel(path): file_sha256(path) for path in output_paths},
        "output_paths": {
            "broker_spec_ledger": rel(BROKER_SPEC_LEDGER),
            "commission_evidence_ledger": rel(COMMISSION_EVIDENCE_LEDGER),
            "effective_config_ledger": rel(EFFECTIVE_CONFIG_LEDGER),
            "selected_cell_risk_ledger": rel(SELECTED_CELL_RISK_LEDGER),
        },
        "row_counts": {
            "broker_spec_rows": len(broker_spec_rows),
            "commission_evidence_symbol_rows": sum(1 for row in broker_spec_rows if row.get("commission_evidence")),
            "effective_config_rows": len(config_rows),
            "selected_cell_risk_rows": len(risk_rows),
            "selected_cell_risk_positive_rows": len(risk_positive_rows),
            "selected_cell_risk_zero_rows": len(risk_rows) - len(risk_positive_rows),
        },
        "broker_contract_status_counts": dict(Counter(row.get("broker_contract_status") for row in broker_spec_rows)),
        "broker_eligible_symbols": sorted(
            row.get("symbol") for row in broker_spec_rows if row.get("eligible_for_vnext_activation")
        ),
        "broker_excluded_symbols": sorted(
            row.get("symbol") for row in broker_spec_rows if not row.get("eligible_for_vnext_activation")
        ),
        "risk_rows_by_selector_component": dict(Counter(row.get("selector_component") for row in risk_rows)),
        "risk_rows_by_symbol": dict(Counter(row.get("symbol") for row in risk_rows)),
        "risk_rows_by_configured_profile_risk_pct": dict(
            Counter(str(row.get("configured_profile_risk_per_trade_pct")) for row in risk_rows)
        ),
        "risk_rows_by_effective_selected_cell_risk_pct": dict(
            Counter(str(row.get("effective_risk_per_trade_pct")) for row in risk_rows)
        ),
        "risk_unresolved_reason_counts": dict(
            Counter(
                reason
                for row in risk_rows
                for reason in (row.get("exact_unresolved_or_excluded_reasons") or [])
            )
        ),
        "selector_summary_selected_rows": {
            "old_three_selected_rows": selector_summary.get("old_three_selected_rows"),
            "broader_origin_selected_rows": selector_summary.get("broader_origin_selected_rows"),
            "combined_selected_rows": selector_summary.get("combined_selected_rows"),
        },
        "selector_summary_metrics": {
            "old_three_component_metrics": selector_summary.get("old_three_component_metrics"),
            "broader_origin_selected_metrics": selector_summary.get("broader_origin_selected_metrics"),
            "combined_production_selector_metrics": selector_summary.get("combined_production_selector_metrics"),
        },
    }


def main() -> None:
    broker_rows = iter_jsonl(BROKER_LEDGER)
    exclusion_rows = iter_jsonl(ACTIVATION_EXCLUSION_LEDGER)
    selector_summary = read_json(SELECTOR_SUMMARY)
    repaired_allowlist = read_json(REPAIRED_BRANCH_ALLOWLIST)
    broader_allowlist = read_json(BROADER_ORIGIN_ALLOWLIST)
    condition_rows = iter_jsonl(CONDITION_CELL_LEDGER)
    agent_config = load_yaml(AGENT_CONFIG)
    redacted_account_profile = load_yaml(redacted_account_PROFILE)
    read_json(BROKER_MAP)

    commission_evidence_rows = build_commission_evidence_rows()
    broker_spec_rows = build_broker_spec_rows(
        broker_rows,
        exclusion_rows,
        commission_evidence_rows,
    )
    config_rows = build_effective_config_rows(broker_spec_rows, agent_config, redacted_account_profile)
    risk_rows = build_selected_cell_risk_rows(
        broker_spec_rows,
        config_rows,
        condition_rows,
        repaired_allowlist,
        broader_allowlist,
    )

    write_jsonl(COMMISSION_EVIDENCE_LEDGER, commission_evidence_rows)
    write_jsonl(BROKER_SPEC_LEDGER, broker_spec_rows)
    write_jsonl(EFFECTIVE_CONFIG_LEDGER, config_rows)
    write_jsonl(SELECTED_CELL_RISK_LEDGER, risk_rows)
    summary = summarize(broker_spec_rows, config_rows, risk_rows, selector_summary)
    write_json(SUMMARY_PATH, summary)
    print(json.dumps(summary, sort_keys=True, ensure_ascii=True))


if __name__ == "__main__":
    main()
