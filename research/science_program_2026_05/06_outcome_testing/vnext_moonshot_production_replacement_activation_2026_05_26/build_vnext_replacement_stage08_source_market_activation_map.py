from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

MOONSHOT_ROUTE = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

STAGE05_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE}.json"
STAGE05_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_{DATE}.json"
STAGE05_SHARD_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_{DATE}.jsonl"
STAGE06_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_VERIFIER_{DATE}.json"
STAGE07_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_QUESTION_CLOSURE_SUMMARY_{DATE}.json"
SOURCE_CAPABILITY_SUMMARY = MOONSHOT_ROUTE / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE}.json"
SOURCE_CAPABILITY_LEDGER = MOONSHOT_ROUTE / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_LEDGER_{DATE}.jsonl"
MOONSHOT_FORWARD_REQUIREMENTS = MOONSHOT_ROUTE / f"VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_{DATE}.jsonl"
STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"

OUTPUT_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
OUTPUT_CAPTURE = ROUTE_DIR / f"VNEXT_REPLACEMENT_SOURCE_CAPTURE_REQUIREMENTS_{DATE}.jsonl"
OUTPUT_EXCLUSIONS = ROUTE_DIR / f"VNEXT_REPLACEMENT_ACTIVATION_EXCLUSION_LEDGER_{DATE}.jsonl"
BROKER_ONBOARDING_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_BROKER_MARKET_ONBOARDING_VERIFIER_{DATE}.json"
BROKER_ONBOARDING_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_BROKER_MARKET_ONBOARDING_LEDGER_{DATE}.jsonl"

LIVE_DEPLOYMENT_SYMBOLS = {
    "GBPJPY": {"broker_symbol": "GBPJPY", "role": "live_trading"},
    "GBPUSD": {"broker_symbol": "GBPUSD", "role": "observer_or_live_config_dependent"},
    "NAS100": {"broker_symbol": "NAS100", "role": "observe_then_live_config_dependent"},
    "US30_cash": {"broker_symbol": "US30_cash", "role": "live_trading_alias_for_us30_cash"},
    "USDJPY": {"broker_symbol": "USDJPY", "role": "live_trading"},
    "XAGUSD": {"broker_symbol": "XAGUSD", "role": "live_trading"},
    "XAUUSD": {"broker_symbol": "XAUUSD", "role": "live_trading"},
}

SOURCE_HANDLING_RULES = {
    "broker_market_onboarding": {
        "activation_rule": "Replay markets are eligible only from exact broker-native MT5/redacted_account contract evidence, not from the stale legacy deployment list.",
        "historical_truth_boundary": "Historical-only, source-missing, or Sierra-delayed labels are not proof that redacted_account lacks the market.",
        "live_rule": "Run read-only broker symbol/contract/tick/bar verification; exclude only with exact unavailable, non-tradeable, feed-missing, invalid-metadata, or unrepairable-capture evidence.",
    },
    "broker_native_live_feed": {
        "activation_rule": "Use only in demo/shadow/paper capture until Stage11/Stage12 overlay, rollback, and monitoring gates pass.",
        "historical_truth_boundary": "Broker/order/account/deal lifecycle truth is non-generatable unless already logged.",
        "live_rule": "Broker-native feed may supply current bars/ticks for configured live symbols; no account/order mutation is performed by this route.",
    },
    "mt5_ohlc_csv": {
        "activation_rule": "Valid for no-paid historical market replay and source-bound proxy path when path ambiguity is labelled.",
        "historical_truth_boundary": "OHLC cannot prove broker fill, spread, slippage, partial close, BE modify, trailing modify, or account attempt state.",
        "live_rule": "Requires broker-native feed and runtime source-capture fields before production activation.",
    },
    "tick_parquet": {
        "activation_rule": "Highest local market-path priority when symbol/window exists and hashes/as-of are recorded.",
        "historical_truth_boundary": "Tick path is market-data truth, not order lifecycle truth.",
        "live_rule": "Prospective tick capture should be monitored for freshness and joined by candidate/source ids.",
    },
    "sierra_scid_or_export": {
        "activation_rule": "Proxy/delayed context only unless a symbol-specific live proxy contract is accepted.",
        "historical_truth_boundary": "Sierra/SCID can support path/orderflow context but does not prove broker-CFD execution.",
        "live_rule": "Use as delayed/proxy context; do not allow it to create broker-native activation by itself.",
    },
    "missing_source": {
        "activation_rule": "Excluded from activation truth; prospective capture is required.",
        "historical_truth_boundary": "Missing path/source windows cannot be inferred from later summaries.",
        "live_rule": "Runtime must log source completeness and ambiguity before execution effect.",
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_line_number"] = line_number
                rows.append(row)
    return rows


def _rel(path: Path | str) -> str:
    if isinstance(path, str):
        path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def _add_counter(target: Counter[str], source: dict[str, Any]) -> None:
    for key, value in source.items():
        target[str(key)] += int(value)


def _symbol_from_source_path(path: str, symbols: list[str]) -> str | None:
    upper = path.upper()
    normalized = upper.replace("-", "_").replace("/", "_").replace("\\", "_")
    for symbol in sorted(symbols, key=len, reverse=True):
        token = symbol.upper()
        loose = token.replace("_CASH", "")
        if re.search(rf"(^|[_\.]){re.escape(token)}([_\.]|$)", normalized):
            return symbol
        if loose != token and re.search(rf"(^|[_\.]){re.escape(loose)}([_\.]|$)", normalized):
            return symbol
    return None


def _aggregate_stage05_by_symbol(symbols: list[str]) -> dict[str, dict[str, Any]]:
    aggregates: dict[str, dict[str, Any]] = {
        symbol: {
            "activated_runtime_effect_rows": 0,
            "candidate_rows": 0,
            "condition_selected_policy_counts": Counter(),
            "disposition_counts": Counter(),
            "dynamic_policy_replay_rows": 0,
            "framework_counts": Counter(),
            "scenario_expectancy_r_values": [],
            "scenario_total_r": Counter(),
            "secondary_framework_replay_only_rows": 0,
            "source_excluded_rows": 0,
            "source_mode_counts": Counter(),
            "source_paths": [],
            "source_window_complete_counts": Counter(),
            "stage04_should_replay_rows": 0,
        }
        for symbol in symbols
    }
    for row in _read_jsonl(STAGE05_SHARD_MANIFEST):
        metrics = row["metrics"]
        row_symbols = list(metrics.get("symbol_counts", {}))
        if len(row_symbols) != 1:
            raise RuntimeError(f"unexpected shard symbol count for {row.get('shard_id')}: {row_symbols}")
        symbol = row_symbols[0]
        agg = aggregates[symbol]
        agg["candidate_rows"] += int(metrics["candidate_rows"])
        agg["activated_runtime_effect_rows"] += int(metrics["activated_runtime_effect_rows"])
        agg["dynamic_policy_replay_rows"] += int(metrics["dynamic_policy_replay_rows"])
        agg["stage04_should_replay_rows"] += int(metrics["stage04_should_replay_rows"])
        agg["secondary_framework_replay_only_rows"] += int(metrics["secondary_framework_replay_only_rows"])
        agg["source_excluded_rows"] += int(metrics["source_excluded_rows"])
        agg["source_paths"].append(row["source_path"])
        _add_counter(agg["framework_counts"], metrics.get("framework_counts", {}))
        _add_counter(agg["disposition_counts"], metrics.get("disposition_counts", {}))
        _add_counter(agg["condition_selected_policy_counts"], metrics.get("condition_selected_policy_counts", {}))
        _add_counter(agg["source_mode_counts"], metrics.get("source_mode_counts", {}))
        _add_counter(agg["source_window_complete_counts"], metrics.get("source_window_complete_counts", {}))
        _add_counter(agg["scenario_total_r"], metrics.get("scenario_total_r", {}))
        agg["scenario_expectancy_r_values"].append(metrics.get("scenario_expectancy_r", {}))
    return aggregates


def _source_capability_by_symbol(symbols: list[str]) -> dict[str, dict[str, Any]]:
    capability = {
        symbol: {
            "dynamic_execution_usable_rows": 0,
            "historical_truth_class_counts": Counter(),
            "source_family_counts": Counter(),
            "source_path_count": 0,
            "source_priority_counts": Counter(),
        }
        for symbol in symbols
    }
    for row in _read_jsonl(SOURCE_CAPABILITY_LEDGER):
        symbol = _symbol_from_source_path(str(row.get("source_path", "")), symbols)
        if not symbol:
            continue
        data = capability[symbol]
        data["source_path_count"] += 1
        data["source_family_counts"][str(row.get("source_family"))] += 1
        data["source_priority_counts"][str(row.get("source_priority_label"))] += 1
        data["historical_truth_class_counts"][str(row.get("historical_truth_class"))] += 1
        if row.get("dynamic_execution_usable") is True:
            data["dynamic_execution_usable_rows"] += 1
    return capability


def _broker_onboarding_by_symbol() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    if not BROKER_ONBOARDING_SUMMARY.exists() or not BROKER_ONBOARDING_LEDGER.exists():
        return (
            {
                "status": "missing",
                "mt5_access_status": "not_run",
                "eligible_symbols": [],
                "exact_excluded_symbols": [],
                "pending_symbols_not_excluded": [],
            },
            {},
        )
    summary = _read_json(BROKER_ONBOARDING_SUMMARY)
    rows = {row.get("symbol"): row for row in _read_jsonl(BROKER_ONBOARDING_LEDGER)}
    return summary, rows


def _decide_market_class(
    symbol: str,
    metrics: dict[str, Any],
    capability: dict[str, Any],
    onboarding: dict[str, Any] | None,
) -> dict[str, Any]:
    onboarding = onboarding or {
        "broker_contract_status": "verification_pending_not_excluded",
        "broker_symbol": None,
        "eligible_for_vnext_activation": False,
        "eligibility_reason": "Broker onboarding verifier has not run for this replay market.",
        "exact_exclusion_reason": None,
        "mt5_access_status": "not_run",
    }
    legacy_info = LIVE_DEPLOYMENT_SYMBOLS.get(symbol)
    broker_contract_status = str(onboarding.get("broker_contract_status") or "verification_pending_not_excluded")
    broker_symbol = onboarding.get("broker_symbol")
    exact_exclusion_reason = onboarding.get("exact_exclusion_reason")
    is_broker_verified = onboarding.get("eligible_for_vnext_activation") is True
    source_family_counts = dict(capability["source_family_counts"])
    has_sierra = source_family_counts.get("sierra_source", 0) > 0
    has_tick = source_family_counts.get("tick_parquet", 0) > 0
    has_ohlc = source_family_counts.get("ohlc_bars", 0) > 0 or bool(metrics["source_paths"])
    complete_rows = int(metrics["source_window_complete_counts"].get("True", 0))
    incomplete_rows = int(metrics["source_window_complete_counts"].get("False", 0))
    candidate_rows = int(metrics["candidate_rows"])
    complete_ratio = complete_rows / candidate_rows if candidate_rows else 0.0

    if is_broker_verified:
        market_class = "broker_native_redacted_account_contract_verified"
        activation_status = "forward_capture_required_before_execution_activation"
        live_rule = "Broker-native MT5/redacted_account contract verified by the route onboarding verifier; activation remains demo/shadow/paper until semantic, rollback, and source-capture gates pass."
    elif exact_exclusion_reason:
        market_class = str(exact_exclusion_reason)
        activation_status = f"excluded_{exact_exclusion_reason}"
        live_rule = f"Excluded by exact read-only broker onboarding evidence: {exact_exclusion_reason}."
    elif broker_contract_status == "verification_pending_not_excluded":
        market_class = "broker_contract_verification_pending"
        activation_status = "broker_contract_verification_required_not_excluded"
        live_rule = "Not excluded: the route lacks current read-only MT5/redacted_account contract proof. Historical-only, missing-source, or Sierra context is not broker-unavailability evidence."
    elif has_sierra:
        market_class = "broker_contract_verification_pending_sierra_context_only"
        activation_status = "broker_contract_verification_required_not_excluded"
        live_rule = "Sierra/SCID is context only. Broker-native MT5 availability must be verified before execution activation; no exclusion is claimed without exact broker evidence."
    elif has_ohlc:
        market_class = "broker_contract_verification_pending_historical_ohlc"
        activation_status = "broker_contract_verification_required_not_excluded"
        live_rule = "Historical MT5/OHLC replay exists, but this is not proof of redacted_account live availability or unavailability; run broker onboarding verification."
    else:
        market_class = "broker_contract_verification_pending_no_local_source"
        activation_status = "broker_contract_verification_required_not_excluded"
        live_rule = "No sufficient local market source was found, but broker unavailability is not inferred without exact onboarding evidence."

    historical_status = (
        "source_complete_historical_replay_rows_present"
        if complete_ratio == 1.0
        else "partial_source_complete_historical_replay_with_forward_capture_required"
    )

    return {
        "activation_status": activation_status,
        "broker_contract_status": broker_contract_status,
        "broker_market_onboarding": {
            "alias_candidates_checked": onboarding.get("alias_candidates_checked", []),
            "broker_symbol": broker_symbol,
            "eligibility_reason": onboarding.get("eligibility_reason"),
            "eligible_for_vnext_activation": is_broker_verified,
            "exact_exclusion_reason": exact_exclusion_reason,
            "mt5_access_status": onboarding.get("mt5_access_status"),
        },
        "broker_native_live_feed_available_now": is_broker_verified,
        "broker_symbol_or_alias": broker_symbol,
        "candidate_rows": candidate_rows,
        "dynamic_policy_replay_rows": metrics["dynamic_policy_replay_rows"],
        "historical_source_status": historical_status,
        "legacy_live_deployment_role": legacy_info["role"] if legacy_info else "not_in_current_live_deployment",
        "legacy_live_deployment_symbol_list_is_activation_ceiling": False,
        "live_source_rule": live_rule,
        "market_activation_class": market_class,
        "primary_historical_source_paths": sorted(set(metrics["source_paths"])),
        "source_capability": {
            "dynamic_execution_usable_rows": capability["dynamic_execution_usable_rows"],
            "has_ohlc_source": has_ohlc,
            "has_sierra_source": has_sierra,
            "has_tick_parquet": has_tick,
            "historical_truth_class_counts": dict(capability["historical_truth_class_counts"]),
            "source_family_counts": source_family_counts,
            "source_path_count": capability["source_path_count"],
            "source_priority_counts": dict(capability["source_priority_counts"]),
        },
        "source_window_complete_ratio": complete_ratio,
        "source_window_complete_rows": complete_rows,
        "source_window_incomplete_rows": incomplete_rows,
        "stage05_disposition_counts": dict(metrics["disposition_counts"]),
        "stage05_framework_counts": dict(metrics["framework_counts"]),
        "symbol": symbol,
    }


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    stage05 = _read_json(STAGE05_SUMMARY)
    stage05_verifier = _read_json(STAGE05_VERIFIER)
    stage06_verifier = _read_json(STAGE06_VERIFIER)
    stage07_summary = _read_json(STAGE07_SUMMARY)
    source_summary = _read_json(SOURCE_CAPABILITY_SUMMARY)
    forward_requirements = _read_jsonl(MOONSHOT_FORWARD_REQUIREMENTS)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)
    previous_current_stage = state.get("current_stage")
    previous_first_incomplete = state.get("first_incomplete_invariant")
    previous_exact_next_action = state.get("exact_next_action")

    symbols = sorted(stage05["coverage"]["symbol_counts"])
    symbol_metrics = _aggregate_stage05_by_symbol(symbols)
    capability_by_symbol = _source_capability_by_symbol(symbols)
    broker_onboarding_summary, broker_onboarding_rows = _broker_onboarding_by_symbol()
    markets = [
        _decide_market_class(symbol, symbol_metrics[symbol], capability_by_symbol[symbol], broker_onboarding_rows.get(symbol))
        for symbol in symbols
    ]
    class_counts = Counter(market["market_activation_class"] for market in markets)
    activation_status_counts = Counter(market["activation_status"] for market in markets)
    broker_verified_symbols = sorted(
        market["symbol"] for market in markets if market.get("broker_native_live_feed_available_now") is True
    )
    broker_pending_symbols = sorted(
        market["symbol"]
        for market in markets
        if market.get("activation_status") == "broker_contract_verification_required_not_excluded"
    )
    broker_exact_excluded_symbols = sorted(
        market["symbol"] for market in markets if str(market.get("activation_status", "")).startswith("excluded_")
    )

    capture_rows: list[dict[str, Any]] = []
    for row in forward_requirements:
        capture_rows.append(
            {
                "activation_dependency": "must_capture_or_verify_before_live_activation_truth_claim",
                "blocker_class": row.get("blocker_class"),
                "capture_surface": row.get("capture_surface"),
                "exact_action": row.get("exact_action"),
                "field_or_contract": row.get("field_or_contract"),
                "historical_reconstruction_policy": row.get("historical_reconstruction_policy"),
                "record_type": "source_capture_requirement",
                "replacement_requirement_id": f"STAGE08-IMPORTED-{row.get('_line_number'):03d}-{row.get('field_or_contract')}",
                "route_id": ROUTE_ID,
                "schema_version": "vnext_replacement_stage08_source_capture_requirement_v1",
                "source_requirement_id": row.get("requirement_id"),
                "source_route_id": row.get("route_id"),
                "stage_id": "stage_08_source_and_market_activation_map",
                "why_needed": row.get("why_needed"),
            }
        )

    additional_requirements = [
        ("candidate_id", "orchestrator_candidate_event", "Stable candidate/source join key required for replay-to-runtime monitoring."),
        ("source_join_ids", "orchestrator_candidate_event", "Every source path used by runtime/replay must be joined to candidate records."),
        ("source_completeness_flags", "orchestrator_candidate_event", "Activation must know whether M1/M5/tick/Sierra path windows are complete."),
        ("same_bar_ambiguity_status", "ltf_path_monitor", "Same-bar stop/target ambiguity must fail closed or use ordered path source."),
        ("dynamic_execution_policy_hash", "execution_policy_router", "Runtime dynamic policy must be reproducible and tied to code/config hashes."),
        ("runtime_branch_policy_label", "execution_trade_record", "Trade records must carry active vNext branch/policy labels."),
        ("prop_governor_decision_fields", "prop_governor_monitor", "Prop action sequence is not historically present and must be captured prospectively."),
        ("ai_response_id_and_prompt_hash", "ai_calibration_path", "AI-dependent rows require cache, prompt hash, schema, and response id when budget-capped calls run."),
        ("old_gtos_fallback_reason", "runtime_fallback_logger", "Any fallback/leakage to old GTOS must be explicit and auditable."),
        ("market_source_activation_class", "runtime_source_monitor", "Runtime must emit market/source activation class for every evaluated candidate."),
    ]
    for index, (field, surface, why) in enumerate(additional_requirements, start=1):
        capture_rows.append(
            {
                "activation_dependency": "required_by_replacement_route_stage08",
                "blocker_class": "prospective_runtime_capture_required",
                "capture_surface": surface,
                "exact_action": "add_or_verify_forward_logger_field_before_activation_truth_claim",
                "field_or_contract": field,
                "historical_reconstruction_policy": "do_not_infer_from_price_alone",
                "record_type": "source_capture_requirement",
                "replacement_requirement_id": f"STAGE08-ROUTE-{index:03d}-{field}",
                "route_id": ROUTE_ID,
                "schema_version": "vnext_replacement_stage08_source_capture_requirement_v1",
                "source_requirement_id": None,
                "source_route_id": ROUTE_ID,
                "stage_id": "stage_08_source_and_market_activation_map",
                "why_needed": why,
            }
        )
    for market in markets:
        if market["activation_status"] == "broker_contract_verification_required_not_excluded":
            capture_rows.append(
                {
                    "activation_dependency": "required_by_market_source_activation_invariant",
                    "blocker_class": "broker_contract_verification_pending",
                    "capture_surface": "read_only_mt5_redacted_account_symbol_contract_verifier",
                    "exact_action": "verify exact redacted_account MT5 symbol alias, visibility, trade_mode, ticks, required timeframes, spread, tick/contract/lot metadata, stops/freeze, sessions, filling, commission/swap fields, then rerun Stage08 map",
                    "field_or_contract": f"broker_market_contract::{market['symbol']}",
                    "historical_reconstruction_policy": "do_not_treat_historical_only_source_missing_or_sierra_context_as_broker_unavailability",
                    "record_type": "source_capture_requirement",
                    "replacement_requirement_id": f"STAGE08-BROKER-{market['symbol']}",
                    "route_id": ROUTE_ID,
                    "schema_version": "vnext_replacement_stage08_source_capture_requirement_v1",
                    "source_requirement_id": None,
                    "source_route_id": ROUTE_ID,
                    "stage_id": "stage_08_source_and_market_activation_map",
                    "why_needed": "Replay market is not excluded, but no exact valid broker-native contract evidence exists yet.",
                }
            )

    exclusion_rows: list[dict[str, Any]] = []
    for market in markets:
        if str(market["activation_status"]).startswith("excluded_"):
            exclusion_rows.append(
                {
                    "activation_exclusion_id": f"STAGE08-MARKET-{market['symbol']}",
                    "candidate_rows": market["candidate_rows"],
                    "exclusion_scope": "market",
                    "exclusion_status": market["activation_status"],
                    "market_activation_class": market["market_activation_class"],
                    "record_type": "activation_exclusion",
                    "route_id": ROUTE_ID,
                    "schema_version": "vnext_replacement_stage08_activation_exclusion_v1",
                    "stage_id": "stage_08_source_and_market_activation_map",
                    "symbol": market["symbol"],
                    "why_excluded": market["live_source_rule"],
                }
            )
    global_exclusions = [
        (
            "STAGE08-GLOBAL-DEFAULT-SOURCE-BOUND-PRIMARY",
            "activation_overlay",
            "current_default_source_bound_primary_projection_excluded",
            stage06_verifier["overall_scenario_metrics"]["activated_default_source_bound_primary"]["performance_count"],
            "Stage06 verifier shows negative expectancy for the current default source-bound primary projection; Stage12 must fail overlays that use it without repair.",
        ),
        (
            "STAGE08-GLOBAL-SOURCE-MISSING",
            "source_mode",
            "source_missing_rows_excluded",
            stage05_verifier["nested_source_mode_counts"]["MISSING_SOURCE"],
            "Missing-source rows are not activation truth and require prospective capture or exclusion.",
        ),
        (
            "STAGE08-GLOBAL-SECONDARY-FRAMEWORK",
            "replay_disposition",
            "secondary_framework_replay_only_excluded",
            stage05["coverage"]["secondary_framework_replay_only_rows"],
            "Secondary framework replay rows are comparator/context until source-bound activation rules explicitly include them.",
        ),
        (
            "STAGE08-GLOBAL-DYNAMIC-EXCLUDED",
            "dynamic_policy",
            "dynamic_policy_replay_excluded",
            stage05["coverage"]["disposition_counts"]["dynamic_policy_replay_excluded"],
            "Rows without dynamic policy performance denominator are excluded from activation performance truth.",
        ),
    ]
    for exclusion_id, scope, status, rows, reason in global_exclusions:
        exclusion_rows.append(
            {
                "activation_exclusion_id": exclusion_id,
                "candidate_rows": rows,
                "exclusion_scope": scope,
                "exclusion_status": status,
                "market_activation_class": None,
                "record_type": "activation_exclusion",
                "route_id": ROUTE_ID,
                "schema_version": "vnext_replacement_stage08_activation_exclusion_v1",
                "stage_id": "stage_08_source_and_market_activation_map",
                "symbol": None,
                "why_excluded": reason,
            }
        )

    output_map = {
        "activation_status_counts": dict(sorted(activation_status_counts.items())),
        "broker_live_deployment_symbols": broker_verified_symbols,
        "broker_market_onboarding_verifier": {
            "ledger_path": _rel(BROKER_ONBOARDING_LEDGER),
            "summary": broker_onboarding_summary,
            "summary_path": _rel(BROKER_ONBOARDING_SUMMARY),
        },
        "broker_native_activation_eligible_symbols": broker_verified_symbols,
        "broker_native_exact_excluded_symbols": broker_exact_excluded_symbols,
        "broker_native_pending_not_excluded_symbols": broker_pending_symbols,
        "capture_requirement_rows": len(capture_rows),
        "exclusion_rows": len(exclusion_rows),
        "first_incomplete_invariant_after_stage08": "stage_09_ai_calibration_package_pending",
        "legacy_live_deployment_symbols_not_activation_ceiling": sorted(LIVE_DEPLOYMENT_SYMBOLS),
        "generated_at_utc": generated_at,
        "market_activation_class_counts": dict(sorted(class_counts.items())),
        "markets": markets,
        "nested_source_mode_counts": stage05_verifier["nested_source_mode_counts"],
        "no_live_or_broker_mutation": True,
        "question_closure_rows_consumed": stage07_summary["output_ledger_rows"],
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage08_market_source_activation_map_v2",
        "source_capability_summary": {
            "forward_capture_requirement_rows": source_summary["forward_capture_requirement_rows"],
            "source_capability_rows": source_summary["source_capability_rows"],
            "source_family_counts": source_summary["source_family_counts"],
            "source_priority_counts": source_summary["source_priority_counts"],
            "source_priority_order": source_summary["source_priority_order"],
        },
        "source_handling_rules": SOURCE_HANDLING_RULES,
        "stage05_candidate_rows": stage05["coverage"]["candidate_rows"],
        "stage_id": "stage_08_source_and_market_activation_map",
    }
    _write_json(OUTPUT_MAP, output_map)

    with OUTPUT_CAPTURE.open("w", encoding="utf-8", newline="\n") as handle:
        for row in capture_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with OUTPUT_EXCLUSIONS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in exclusion_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_MAP.name, "stage": "stage_08", "status": "created", "markets": len(markets)},
    )
    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_CAPTURE.name, "stage": "stage_08", "status": "created", "rows": len(capture_rows)},
    )
    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_EXCLUSIONS.name, "stage": "stage_08", "status": "created", "rows": len(exclusion_rows)},
    )
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage08_market_rows"] = len(markets)
    evidence["stage08_source_capture_requirement_rows"] = len(capture_rows)
    evidence["stage08_activation_exclusion_rows"] = len(exclusion_rows)
    evidence["stage08_source_capability_rows_consumed"] = source_summary["source_capability_rows"]
    evidence["stage08_broker_verified_symbols"] = len(broker_verified_symbols)
    evidence["stage08_broker_pending_not_excluded_symbols"] = len(broker_pending_symbols)
    evidence["stage08_broker_exact_excluded_symbols"] = len(broker_exact_excluded_symbols)
    if previous_first_incomplete == "stage_09_ai_calibration_package_pending" or previous_current_stage in {
        "stage_08_source_and_market_activation_map",
        "stage_09_ai_calibration_package",
    }:
        state["current_stage"] = "stage_09_ai_calibration_package"
        state["first_incomplete_invariant"] = "stage_09_ai_calibration_package_pending"
        state["exact_next_action"] = (
            "Build AI calibration manifest, prompt/context packet ledger, schema/cache verifier, and spend request; do not run paid calls because route_state_budget_cap_usd is null."
        )
    else:
        state["current_stage"] = previous_current_stage
        state["first_incomplete_invariant"] = previous_first_incomplete
        state["exact_next_action"] = previous_exact_next_action
    state.setdefault("stage_status", {})[
        "stage_08_source_and_market_activation_map"
    ] = "completed_market_source_map_written_with_broker_onboarding_invariant"
    state.setdefault("stage_status", {})["stage_09_ai_calibration_package"] = "pending"
    _append_test_result(
        state,
        _rel(Path(__file__)),
        "passed; wrote Stage08 market source activation map, capture requirements, and exclusion ledger",
        generated_at,
    )
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_08_source_and_market_activation_map_completed",
            "broker_exact_excluded_symbols": broker_exact_excluded_symbols,
            "broker_pending_not_excluded_symbols": broker_pending_symbols,
            "broker_verified_symbols": broker_verified_symbols,
            "generated_at_utc": generated_at,
            "market_rows": len(markets),
            "route_id": ROUTE_ID,
            "source_capture_requirement_rows": len(capture_rows),
            "stage_id": "stage_08_source_and_market_activation_map",
        }
    )

    print(json.dumps({"markets": len(markets), "next": state["first_incomplete_invariant"], "stage": "stage_08_source_and_market_activation_map"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
