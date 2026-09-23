from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_ROUTE_DIR = REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28"
REPLAY_ROUTE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
)
LEDGER_PATH = LIVE_ROUTE_DIR / "LIVE_REPLAY_GATE_STACK_INVENTORY_LEDGER.jsonl"
SUMMARY_PATH = LIVE_ROUTE_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json"

REQUIRED_GATE_IDS = [
    "gate0_deployment_profile_trading_enabled",
    "gate1_vnext_executable_geometry_repair",
    "gate1_sl_absolute_min_after_repair",
    "gate1_m15_atr_after_repair",
    "gate1_sl_too_wide_after_repair",
    "gate1_min_rr_and_dynamic_tp_sanity",
    "gate1_ob_only_structural_exception_legacy_scope",
    "gate1_grade_direction_touch_inverted_liquidity_cluster",
    "vnext_broader_origin_allowlist_source_risk",
    "selected_cell_allowlist_risk_proof",
    "redacted_account_prop_governor_risk_geometry",
    "broker_symbol_spec_tick_stop_freeze_volume_contract_spread",
    "session_kill_zone_outside_session",
    "orchestrator_pre_candle_halt_sprt_kz_trade_cap",
    "old_primary_analyzer_l2_fallback_leakage",
    "ai_no_paid_call_required_no_call",
    "news_calendar_freshness_and_block",
    "correlation_max_concurrent_drawdown_daily_equity",
    "m1_tick_ltf_availability",
    "pending_limit_placement_fill_expiry",
    "execution_order_send_retcode_volume_margin",
    "dynamic_execution_lifecycle",
    "telegram_order_deal_reconciliation_lifecycle",
    "candidate_intelligence_packet_null_zero_guard",
    "heartbeat_flatten_orphan_reconciliation",
    "watchdog_startup_monitor",
    "stale_config_profile_instrument_overrides",
]


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    value = json.loads(line)
                    if isinstance(value, dict):
                        rows.append(value)
    except (OSError, json.JSONDecodeError):
        return rows
    return rows


def _counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "missing") for row in rows))


def _config() -> dict[str, Any]:
    return yaml.safe_load((REPO_ROOT / "config/agent_config.yaml").read_text(encoding="utf-8"))


def _stage04_summary() -> dict[str, Any]:
    return _read_json(
        REPLAY_ROUTE_DIR / "VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_2026-05-27.json",
        {},
    )


def _dynamic_summary() -> dict[str, Any]:
    return _read_json(REPLAY_ROUTE_DIR / "ei15r/final_dynamic_router_replay_summary.json", {})


def _momentum_promotion_summary() -> dict[str, Any]:
    return _read_json(REPLAY_ROUTE_DIR / "ei15r/momentum_policy_promotion_summary.json", {})


def _selected_trade_projection() -> dict[str, Any]:
    manifest_path = (
        REPLAY_ROUTE_DIR
        / "VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_SELECTED_TRADE_SHARD_MANIFEST_2026-05-27.jsonl"
    )
    manifest_rows = _read_jsonl(manifest_path)
    manifest_source = "stage04_selected_trade_manifest"
    if not manifest_rows:
        shard_dir = REPLAY_ROUTE_DIR / "stage04_canonical_selected_trade_shards"
        manifest_rows = [
            {"path": str(path.relative_to(REPO_ROOT))}
            for path in sorted(shard_dir.glob("*.jsonl.gz"))
        ]
        manifest_source = (
            "materialized_stage04_selected_trade_shard_directory_fallback"
        )
    counts = Counter()
    r_total = 0.0
    symbols: Counter[str] = Counter()
    policies: Counter[str] = Counter()
    components: Counter[str] = Counter()
    for shard in manifest_rows:
        shard_path = REPO_ROOT / str(shard.get("path") or "")
        opener = gzip.open if shard_path.suffix == ".gz" else open
        try:
            with opener(shard_path, "rt", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    counts["rows"] += 1
                    entry = _to_float(row.get("entry_price"))
                    stop = _to_float(row.get("stop_or_invalidation"))
                    target = _to_float(row.get("target_reference"))
                    if entry is not None and stop is not None and target is not None:
                        counts["geometry_fields_present"] += 1
                        sl_distance = abs(entry - stop)
                        if sl_distance > 0:
                            counts["positive_sl_distance"] += 1
                            tp_r = abs(target - entry) / sl_distance
                            if tp_r >= 1.3:
                                counts["tp_rr_at_or_above_legacy_min"] += 1
                            if tp_r > 2.0:
                                counts["tp_rr_above_old_static_2r_ceiling"] += 1
                    if row.get("risk_disposition") == "risk_positive_executable_current_broker_geometry":
                        counts["risk_positive_executable_current_broker_geometry"] += 1
                    if row.get("broker_geometry_status") == "covered_current_redacted_account_geometry":
                        counts["covered_current_redacted_account_geometry"] += 1
                    if row.get("commission_capture_status") == "ACCOUNT_HISTORY_REQUIRED_AT_LIVE_FILL_CLOSE":
                        counts["live_commission_capture_required"] += 1
                    r = _to_float(row.get("r_multiple"))
                    if r is not None:
                        r_total += r
                    symbols[str(row.get("symbol") or "missing")] += 1
                    policies[str(row.get("selected_policy") or "missing")] += 1
                    components[str(row.get("selector_component") or "missing")] += 1
        except OSError:
            counts["unreadable_shards"] += 1
    return {
        "manifest_path": str(manifest_path.relative_to(REPO_ROOT)),
        "manifest_source": manifest_source,
        "counts": dict(counts),
        "gross_static_row_r_sum": round(r_total, 6),
        "symbol_counts": dict(symbols),
        "historical_stage04_projection_policy_counts": dict(policies),
        "historical_stage04_projection_policy_scope": (
            "Stage04 canonical selected-trade projection input only; these "
            "labels predate the promoted momentum/partial live router and "
            "must not be read as current production policy."
        ),
        "selector_component_counts": dict(components),
        "exact_m15_atr_available_in_selected_trade_rows": False,
        "m15_atr_gap_decision": (
            "raw 1.5*M15_ATR Gate1 no longer has terminal authority before "
            "vNext executable geometry repair; future live rows capture the "
            "repair thresholds in trade records"
        ),
    }


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _live_inputs() -> dict[str, Any]:
    candidate_rows = _read_jsonl(LIVE_ROUTE_DIR / "LIVE_CANDIDATE_DECISION_LEDGER.jsonl")
    prop_rows = _read_jsonl(LIVE_ROUTE_DIR / "LIVE_PROP_RISK_GEOMETRY_LEDGER.jsonl")
    broker_rows = _read_jsonl(LIVE_ROUTE_DIR / "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl")
    data_rows = _read_jsonl(LIVE_ROUTE_DIR / "LIVE_DATA_FEED_HEALTH_LEDGER.jsonl")
    tick_rows = _read_jsonl(LIVE_ROUTE_DIR / "LIVE_TICK_CAPTURE_HEALTH_LEDGER.jsonl")
    order_rows = _read_jsonl(LIVE_ROUTE_DIR / "LIVE_ORDER_LIFECYCLE_LEDGER.jsonl")
    deal_rows = _read_jsonl(LIVE_ROUTE_DIR / "LIVE_BROKER_DEAL_RECONCILIATION_LEDGER.jsonl")
    dynamic_rows = _read_jsonl(LIVE_ROUTE_DIR / "LIVE_DYNAMIC_EXECUTION_LIFECYCLE_LEDGER.jsonl")
    cost_rows = _read_jsonl(LIVE_ROUTE_DIR / "LIVE_COST_SLIPPAGE_COMMISSION_LEDGER.jsonl")
    old_leak = _read_json(LIVE_ROUTE_DIR / "LIVE_OLD_SYSTEM_LEAKAGE_AUDIT.json", {})
    startup = _read_json(LIVE_ROUTE_DIR / "LIVE_STARTUP_VERIFICATION.json", {})
    watchdog = _read_json(LIVE_ROUTE_DIR / "LIVE_WATCHDOG_PARITY_VERIFICATION.json", {})
    active_state = _read_json(LIVE_ROUTE_DIR / "ACTIVE_REPAIR_STATE.json", {})
    return {
        "candidate_rows": candidate_rows,
        "prop_rows": prop_rows,
        "broker_rows": broker_rows,
        "data_rows": data_rows,
        "tick_rows": tick_rows,
        "order_rows": order_rows,
        "deal_rows": deal_rows,
        "dynamic_rows": dynamic_rows,
        "cost_rows": cost_rows,
        "old_leak": old_leak,
        "startup": startup,
        "watchdog": watchdog,
        "active_state": active_state,
    }


def _row(
    *,
    gate_id: str,
    gate_name: str,
    code_config_source: list[str],
    runs_live: bool,
    ran_in_vnext_replay: bool,
    classification: str,
    affected: dict[str, Any],
    counts: dict[str, Any],
    r_frequency_impact: dict[str, Any],
    repair_decision: str,
    proof: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "vnext_live_replay_gate_stack_inventory_v1",
        "gate_id": gate_id,
        "gate_name": gate_name,
        "code_config_source": code_config_source,
        "runs_live": runs_live,
        "ran_in_vnext_replay": ran_in_vnext_replay,
        "classification": classification,
        "affected_symbols": affected.get("symbols", []),
        "affected_origin_families": affected.get("origin_families", []),
        "affected_sessions": affected.get("sessions", []),
        "affected_policies": affected.get("policies", []),
        "counts": counts,
        "r_frequency_impact": r_frequency_impact,
        "repair_decision": repair_decision,
        "proof": proof,
    }


def build() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cfg = _config()
    stage04 = _stage04_summary()
    dynamic = _dynamic_summary()
    momentum = _momentum_promotion_summary()
    selected_projection = _selected_trade_projection()
    live = _live_inputs()
    candidate_rows = live["candidate_rows"]
    symbols = sorted({str(row.get("symbol")) for row in candidate_rows if row.get("symbol")})
    origins = sorted({str(row.get("origin_family")) for row in candidate_rows if row.get("origin_family")})
    sessions = sorted({str(row.get("kill_zone")) for row in candidate_rows if row.get("kill_zone")})
    policies = sorted({str(row.get("selected_policy")) for row in candidate_rows if row.get("selected_policy")})
    live_final_counts = _counter(candidate_rows, "final_outcome")
    gate1_reason_counts = Counter()
    for row in candidate_rows:
        reason = str(row.get("permission_reason") or "")
        if reason:
            gate1_reason_counts[reason.split(":", 1)[0]] += 1
    affected = {
        "symbols": symbols,
        "origin_families": origins,
        "sessions": sessions,
        "policies": policies,
    }
    replay_rows = int(stage04.get("order_intent_counts", {}).get("selected_rows") or 0)
    dynamic_metrics = dynamic.get("final_dynamic_router_metrics") or dynamic.get("metrics") or {}
    current_production_policy_distribution = (
        momentum.get("policy_distribution")
        or dynamic.get("policy_distribution")
        or {}
    )
    dynamic_rows = int(
        dynamic.get("replayable_metric_rows")
        or dynamic.get("selected_rows_processed")
        or dynamic.get("selected_rows")
        or replay_rows
    )
    router_refused = int(dynamic.get("router_refused_rows") or 0)
    replay_r = {
        "selected_rows": replay_rows,
        "dynamic_router_replayable_metric_rows": dynamic_rows,
        "dynamic_router_selected_rows_processed": dynamic.get("selected_rows_processed"),
        "dynamic_router_non_replayable_rows": dynamic.get("non_replayable_rows"),
        "router_refused_rows": router_refused,
        "dynamic_replay_total_r": dynamic_metrics.get("total_r"),
        "dynamic_replay_expectancy_r": dynamic_metrics.get("expectancy_r"),
        "dynamic_replay_profit_factor": dynamic_metrics.get("profit_factor"),
        "dynamic_replay_win_rate": dynamic_metrics.get("win_rate"),
    }

    rows = [
        _row(
            gate_id="gate0_deployment_profile_trading_enabled",
            gate_name="Gate0 deployment/profile/trading-enabled/killed-instrument authority",
            code_config_source=[
                "src/components/permissions.py::_reject_if_deployment_phase_blocked",
                "src/components/permissions.py::_reject_if_trading_disabled",
                "src/components/permissions.py::_reject_if_killed_instrument",
                "config/agent_config.yaml::deployment/trading_enabled/killed_instrument_policy",
                "config/profiles/redacted_account.yaml",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "live_rows": len(candidate_rows),
                "live_denials": sum(v for k, v in live_final_counts.items() if "GATE0" in k),
                "deployment_phase": cfg.get("deployment", {}).get("phase"),
                "replay_selected_rows_after_profile_broker_alias_repair": replay_rows,
            },
            r_frequency_impact=replay_r,
            repair_decision="keep; profile and 24-symbol activation already replay-accounted through Stage03 alias/profile repair",
            proof=[
                "src/components/permissions.py",
                "VNEXT_ACTIVATION_REPAIR_STAGE03_BROKER_RUNTIME_SURFACE_2026-05-27.json",
                "LIVE_STARTUP_VERIFICATION.json",
            ],
        ),
        _row(
            gate_id="gate1_vnext_executable_geometry_repair",
            gate_name="Gate1 vNext executable-geometry repair before terminal rejection",
            code_config_source=[
                "src/components/orchestrator.py::_execute_vnext_broader_origin_candidate",
                "src/components/orchestrator.py::_repair_vnext_broader_origin_executable_geometry",
                "src/components/permissions.py::check_permissions(skip_gate1_safety=True)",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "pre_repair_live_gate1_rejections_observed": live_final_counts.get("REJECTED_GATE1_SAFETY", 0),
                "pre_repair_reason_counts": dict(gate1_reason_counts),
                "replay_selected_rows_projected_for_post_repair_geometry": selected_projection["counts"].get("rows", 0),
                "replay_rows_with_entry_stop_target": selected_projection["counts"].get("geometry_fields_present", 0),
                "future_live_repair_rows_capture_thresholds": True,
            },
            r_frequency_impact=replay_r,
            repair_decision=(
                "repaired: broader-origin raw geometry now runs Gate0/Gate3 first, "
                "then LTF entry adjustment, structural/ATR/broker stop expansion, "
                "dynamic target recompute, selected-cell risk/lot proof, prop recheck, "
                "and only then terminal Gate1"
            ),
            proof=[
                "src/components/orchestrator.py::_repair_vnext_broader_origin_executable_geometry",
                "tests/test_vnext_broader_origin_orchestrator.py::test_broader_origin_repairs_gate1_geometry_before_terminal_rejection",
                "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json",
            ],
        ),
        _row(
            gate_id="gate1_sl_absolute_min_after_repair",
            gate_name="Gate1 sl_absolute_min after vNext repair",
            code_config_source=[
                "src/components/permissions.py::_gate1_safety_checks",
                "config/agent_config.yaml::risk.sl_absolute_min",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "pre_repair_live_rejections": gate1_reason_counts.get("sl_below_minimum_floor", 0),
                "repair_threshold_source": "config risk.sl_absolute_min plus instrument override",
                "replay_projection_rows": selected_projection["counts"].get("rows", 0),
            },
            r_frequency_impact=replay_r,
            repair_decision="kept only after repair; no terminal authority on raw broader-origin geometry",
            proof=["src/components/orchestrator.py::_repair_vnext_broader_origin_executable_geometry"],
        ),
        _row(
            gate_id="gate1_m15_atr_after_repair",
            gate_name="Gate1 1.5*M15 ATR after vNext repair",
            code_config_source=[
                "src/components/permissions.py::_gate1_safety_checks",
                "src/components/orchestrator.py::_repair_vnext_broader_origin_executable_geometry",
                "src/components/broader_origin_generators.py::source_fields.atr14",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "pre_repair_live_rejections": gate1_reason_counts.get("sl_too_tight", 0),
                "selected_trade_rows_missing_exact_m15_atr": selected_projection["counts"].get("rows", 0),
                "live_repair_threshold_capture_enabled": True,
            },
            r_frequency_impact={
                **replay_r,
                "exact_replay_filter_impact": "not_reapplied_as_raw_filter; terminal raw authority removed",
            },
            repair_decision=(
                "repaired as stop-expansion threshold using live MSO M15 ATR or "
                "candidate source_fields.atr14 before final Gate1"
            ),
            proof=[
                "src/components/orchestrator.py::_repair_vnext_broader_origin_executable_geometry",
                "src/components/broader_origin_generators.py",
            ],
        ),
        _row(
            gate_id="gate1_sl_too_wide_after_repair",
            gate_name="Gate1 sl_too_wide after repair",
            code_config_source=["src/components/permissions.py::_gate1_safety_checks"],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "pre_repair_live_rejections": gate1_reason_counts.get("sl_too_wide", 0),
                "replay_rows_with_positive_sl_distance": selected_projection["counts"].get("positive_sl_distance", 0),
            },
            r_frequency_impact=replay_r,
            repair_decision="keep after repair as final abnormal-width safety rail",
            proof=["src/components/permissions.py", "src/components/orchestrator.py::_repair_vnext_broader_origin_executable_geometry"],
        ),
        _row(
            gate_id="gate1_min_rr_and_dynamic_tp_sanity",
            gate_name="Gate1 min_rr and TP/SL sanity with dynamic final target awareness",
            code_config_source=[
                "src/components/permissions.py::_gate1_safety_checks",
                "src/components/permissions.py::_vnext_dynamic_geometry_context",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "replay_rows_with_tp_rr_above_old_static_2r_ceiling": selected_projection["counts"].get(
                    "tp_rr_above_old_static_2r_ceiling",
                    0,
                ),
                "dynamic_policy_distribution": dynamic.get("policy_distribution", {}),
            },
            r_frequency_impact=replay_r,
            repair_decision="repaired: old TP1 >2R stale rejection now allows selected vNext dynamic final target R",
            proof=["src/components/permissions.py::_vnext_dynamic_geometry_context"],
        ),
        _row(
            gate_id="gate1_ob_only_structural_exception_legacy_scope",
            gate_name="OB-only structural SL exception",
            code_config_source=["src/components/permissions.py::_evaluate_ob_retest_sl_exception"],
            runs_live=True,
            ran_in_vnext_replay=False,
            classification="stale-old-system-removed-from-vnext-authority",
            affected={"symbols": symbols, "origin_families": ["ob_retest"], "sessions": sessions, "policies": policies},
            counts={"live_rows": len(candidate_rows), "broader_origin_terminal_authority": 0},
            r_frequency_impact={"replay_impact": "not part of vNext broader-origin denominator"},
            repair_decision="do not use as broader-origin repair path; vNext repair is origin-family agnostic",
            proof=["src/components/orchestrator.py::_repair_vnext_broader_origin_executable_geometry"],
        ),
        _row(
            gate_id="gate1_grade_direction_touch_inverted_liquidity_cluster",
            gate_name="Gate1 grade/direction/touch-count/inverted-geometry/liquidity-cluster guards",
            code_config_source=[
                "src/components/permissions.py::_gate1_safety_checks",
                "src/components/permissions.py::_reject_if_touch_count_too_high",
                "src/components/permissions.py::_reject_if_sl_behind_liquidity_cluster",
            ],
            runs_live=True,
            ran_in_vnext_replay=False,
            classification="live-authoritative-vNext-final-sanity-and-legacy-scope-guard",
            affected={
                "symbols": symbols,
                "origin_families": origins + ["ob_retest"],
                "sessions": sessions,
                "policies": policies,
            },
            counts={
                "grade_threshold": ["A+", "A"],
                "touch_count_reject_threshold": (cfg.get("gate1", {}) or {}).get(
                    "touch_count_reject_threshold"
                ),
                "sl_liquidity_cluster_enabled": (cfg.get("gate1", {}) or {}).get(
                    "sl_liquidity_cluster_enabled"
                ),
                "post_repair_live_rows": len(candidate_rows),
            },
            r_frequency_impact={
                "replay_impact": (
                    "not included as separate Stage13 denominator filter; live "
                    "final Gate1 still runs after vNext repair and packet proof "
                    "must classify any rejection"
                )
            },
            repair_decision=(
                "keep as final sanity/capture guard; touch-count and OB-specific "
                "legacy rules have no pre-repair terminal authority over broader-origin rows"
            ),
            proof=[
                "src/components/permissions.py::_gate1_safety_checks",
                "tests/test_vnext_broader_origin_orchestrator.py",
            ],
        ),
        _row(
            gate_id="vnext_broader_origin_allowlist_source_risk",
            gate_name="vNext broader-origin allowlist/source-risk/dynamic refusal",
            code_config_source=[
                "src/components/gtos_vnext_runtime.py::_moonshot_broader_origin_allowlist_match",
                "src/research/moonshot_default_off_policy_router.py::route_moonshot_dynamic_execution",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "live_dynamic_skips": live_final_counts.get("SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC", 0),
                "live_refusal_reason_counts": _counter(candidate_rows, "refusal_reasons"),
                "replay_router_refused_rows": router_refused,
            },
            r_frequency_impact=replay_r,
            repair_decision="keep; this is the selected vNext denominator authority",
            proof=["ei15r/final_dynamic_router_replay_summary.json", "shadow_logs/gtos_vnext_runtime_decisions.jsonl"],
        ),
        _row(
            gate_id="selected_cell_allowlist_risk_proof",
            gate_name="Selected-cell allowlist/risk proof",
            code_config_source=[
                "src/components/gtos_vnext_runtime.py::_moonshot_selected_cell_risk_match",
                "src/components/execution.py::_resolve_vnext_production_risk_pct",
                "config/agent_config.yaml::moonshot_dynamic_execution_router_selected_cell_risk_ledger_path",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "replay_selected_risk_positive_rows": stage04.get("selected_risk_disposition_counts", {}),
                "live_rows_with_selected_policy": sum(1 for row in candidate_rows if row.get("selected_policy")),
            },
            r_frequency_impact=replay_r,
            repair_decision="keep; final order path fails closed if selected risk cell or policy identity is absent",
            proof=["src/components/execution.py::_resolve_vnext_production_risk_pct"],
        ),
        _row(
            gate_id="redacted_account_prop_governor_risk_geometry",
            gate_name="redacted_account prop governor and risk geometry",
            code_config_source=[
                "src/components/gtos_vnext_runtime.py::evaluate_vnext_prop_safe_selector",
                "config/agent_config.yaml::prop_safe_selector_*",
                "config/profiles/redacted_account.yaml",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "live_prop_rows": len(live["prop_rows"]),
                "live_prop_action_counts": _counter(candidate_rows, "prop_action"),
                "replay_prop_proxy_rows": stage04.get("prior_intelligence_consumption", {}).get("disposition_counts", {}),
            },
            r_frequency_impact=replay_r,
            repair_decision="repaired sequencing: prop governor now re-runs after selected-cell risk and geometry repair",
            proof=["src/components/orchestrator.py::_execute_vnext_broader_origin_candidate"],
        ),
        _row(
            gate_id="broker_symbol_spec_tick_stop_freeze_volume_contract_spread",
            gate_name="Broker symbol/spec/tick/stop/freeze/volume/contract-size/spread gates",
            code_config_source=[
                "src/components/execution.py",
                "src/components/permissions.py::_gate3_circuit_breakers",
                "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native-live-broker-verified",
            affected={"symbols": sorted({row.get("symbol") for row in live["broker_rows"] if row.get("symbol")}), "origin_families": origins, "sessions": sessions, "policies": policies},
            counts={
                "live_broker_spec_rows": len(live["broker_rows"]),
                "live_broker_status_counts": _counter(live["broker_rows"], "status"),
                "replay_broker_geometry_rows": selected_projection["counts"].get("covered_current_redacted_account_geometry", 0),
                "live_commission_capture_required_rows": selected_projection["counts"].get("live_commission_capture_required", 0),
            },
            r_frequency_impact=replay_r,
            repair_decision="keep; broker geometry is selected-row proof plus live pre-send enforcement",
            proof=["LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl", "src/components/execution.py::_vnext_pretrade_cost_model"],
        ),
        _row(
            gate_id="session_kill_zone_outside_session",
            gate_name="Session/KZ/outside-session gates",
            code_config_source=[
                "config/agent_config.yaml::market.kill_zones",
                "src/components/gtos_vnext_runtime.py::build_vnext_moonshot_dynamic_execution_event",
                "src/components/orchestrator.py::_process_candle",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "live_session_counts": _counter(candidate_rows, "kill_zone"),
                "replay_selector_component_counts": selected_projection["selector_component_counts"],
            },
            r_frequency_impact=replay_r,
            repair_decision="keep; outside-session expansion is replay-selected only where allowlist/proof exists",
            proof=["VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_2026-05-27.json"],
        ),
        _row(
            gate_id="orchestrator_pre_candle_halt_sprt_kz_trade_cap",
            gate_name="Orchestrator pre-candle halt/SPRT/KZ trade-cap gates",
            code_config_source=[
                "src/components/orchestrator.py::_check_sprt_class_halt_gate",
                "src/components/orchestrator.py::_check_kill_zone_trade_cap",
                "src/components/orchestrator.py::_check_and_trigger_daily_loss_stop",
                "src/safety/dormant_state.py",
            ],
            runs_live=True,
            ran_in_vnext_replay=False,
            classification="live-only-vNext-native-operational-risk-gate",
            affected=affected,
            counts={
                "live_candidate_rows": len(candidate_rows),
                "live_final_counts": live_final_counts,
            },
            r_frequency_impact={
                "replay_impact": "operational account/session halt gate; not a market-row replay filter"
            },
            repair_decision="keep; candidate packets must record if this gate stops a row before order path",
            proof=[
                "src/components/orchestrator.py",
                "src/safety/dormant_state.py",
                "LIVE_CANDIDATE_DECISION_LEDGER.jsonl",
            ],
        ),
        _row(
            gate_id="old_primary_analyzer_l2_fallback_leakage",
            gate_name="Old PrimaryAnalyzer/L2 fallback/leakage gates",
            code_config_source=["src/components/orchestrator.py", "LIVE_OLD_SYSTEM_LEAKAGE_AUDIT.json"],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native-leakage-guard",
            affected=affected,
            counts={
                "live_old_primary_true": sum(1 for row in candidate_rows if row.get("old_primary_analyzer_called") is True),
                "live_old_l2_true": sum(1 for row in candidate_rows if row.get("old_l2_required") is True),
                "old_leakage_audit": live["old_leak"],
            },
            r_frequency_impact=replay_r,
            repair_decision="keep; no fallback to old AI/L2 for broader-origin rows",
            proof=["tests/test_vnext_broader_origin_orchestrator.py", "LIVE_OLD_SYSTEM_LEAKAGE_AUDIT.json"],
        ),
        _row(
            gate_id="ai_no_paid_call_required_no_call",
            gate_name="AI/no-paid/call-required/no-call gates",
            code_config_source=["src/components/orchestrator.py::_create_vnext_broader_origin_record", "src/components/gtos_vnext_runtime.py"],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={"live_broader_origin_rows": len(candidate_rows), "paid_ai_calls_required": 0},
            r_frequency_impact=replay_r,
            repair_decision="keep; broader-origin records explicitly use no paid AI call",
            proof=["src/components/orchestrator.py::_create_vnext_broader_origin_record"],
        ),
        _row(
            gate_id="news_calendar_freshness_and_block",
            gate_name="News/calendar gates",
            code_config_source=["src/components/orchestrator.py::_vnext_broader_origin_safety_gate", "config/agent_config.yaml::news_filter/economic_calendar"],
            runs_live=True,
            ran_in_vnext_replay=False,
            classification="live-only-vNext-native-operational-gate",
            affected=affected,
            counts={
                "live_news_block_rows": live_final_counts.get("SKIP_GTOS_VNEXT_BROADER_ORIGIN_NEWS_BLOCKED", 0),
                "active_state_news_calendar": (live["active_state"].get("gates", {}) or {}).get("news_calendar_configuration_freshness", {}),
            },
            r_frequency_impact={"replay_impact": "not historical-replayed; live operational prop/news compliance gate"},
            repair_decision="keep live-only; repo refresh tool is freshness authority",
            proof=["scripts/refresh_economic_calendar.py", "ACTIVE_REPAIR_STATE.json"],
        ),
        _row(
            gate_id="correlation_max_concurrent_drawdown_daily_equity",
            gate_name="Correlation/max-concurrent/drawdown/daily-loss/equity gates",
            code_config_source=[
                "src/components/permissions.py::_gate3_circuit_breakers",
                "src/components/portfolio_risk.py",
                "src/components/drawdown_manager.py",
                "src/components/cross_instrument_correlation_gate.py",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native-risk-overlay",
            affected=affected,
            counts={
                "live_gate3_denials": sum(v for k, v in live_final_counts.items() if "GATE3" in k),
                "live_prop_rows": len(live["prop_rows"]),
            },
            r_frequency_impact=replay_r,
            repair_decision="keep; final selected-cell/prop recheck now happens before final Gate1/order placement",
            proof=["src/components/orchestrator.py::_execute_vnext_broader_origin_candidate"],
        ),
        _row(
            gate_id="m1_tick_ltf_availability",
            gate_name="M1/tick/LTF availability gates",
            code_config_source=["src/components/m1_capture.py", "src/components/orchestrator.py::_build_gtos_vnext_ltf_path_state", "src/components/gtos_vnext_runtime.py::evaluate_vnext_ltf_path_execution"],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={
                "live_data_feed_rows": len(live["data_rows"]),
                "live_tick_rows": len(live["tick_rows"]),
                "live_tick_status_counts": _counter(live["tick_rows"], "status"),
            },
            r_frequency_impact=replay_r,
            repair_decision="keep; M1-aware entry adjustment is consumed by executable-geometry repair",
            proof=["src/components/m1_capture.py", "src/components/orchestrator.py::_repair_vnext_broader_origin_executable_geometry"],
        ),
        _row(
            gate_id="pending_limit_placement_fill_expiry",
            gate_name="Pending-limit placement/fill/expiry gates",
            code_config_source=["src/components/execution.py::set_limit_intent", "src/components/execution.py::check_pending_limit", "src/components/gtos_vnext_runtime.py::evaluate_vnext_pending_policy"],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={"live_order_lifecycle_rows": len(live["order_rows"]), "live_order_status_counts": _counter(live["order_rows"], "status")},
            r_frequency_impact=replay_r,
            repair_decision="keep; policy context propagates to pending/fill/expiry notifications",
            proof=["src/components/execution.py", "src/notifications.py"],
        ),
        _row(
            gate_id="execution_order_send_retcode_volume_margin",
            gate_name="Execution order-send retcode/volume/margin/price-normalization gates",
            code_config_source=[
                "src/components/execution.py::open_trade",
                "src/components/execution.py::set_limit_intent",
                "src/components/execution.py::_calculate_lots",
                "src/components/execution.py::_normalize_volume",
                "src/components/execution.py::_send_native_pending_order",
            ],
            runs_live=True,
            ran_in_vnext_replay=False,
            classification="live-only-vNext-native-broker-placement-gate",
            affected=affected,
            counts={
                "live_order_rows": len(live["order_rows"]),
                "live_cost_rows": len(live["cost_rows"]),
                "broker_placement_ready_replay_rows": min(
                    selected_projection["counts"].get(
                        "risk_positive_executable_current_broker_geometry",
                        0,
                    ),
                    dynamic_rows - router_refused,
                ),
            },
            r_frequency_impact={
                "replay_impact": "broker retcodes/margin are live-operational; replay supplies broker-geometry-ready denominator only"
            },
            repair_decision=(
                "keep live-only; candidate packet and lifecycle ledgers must capture retcode, volume, margin, "
                "cost/slippage, and exact missing reason when no send occurs"
            ),
            proof=[
                "src/components/execution.py",
                "LIVE_ORDER_LIFECYCLE_LEDGER.jsonl",
                "LIVE_COST_SLIPPAGE_COMMISSION_LEDGER.jsonl",
            ],
        ),
        _row(
            gate_id="dynamic_execution_lifecycle",
            gate_name="Dynamic execution lifecycle gates",
            code_config_source=["src/components/execution.py", "src/components/gtos_vnext_runtime.py", "src/research/moonshot_default_off_policy_router.py"],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native",
            affected=affected,
            counts={"live_dynamic_lifecycle_rows": len(live["dynamic_rows"]), "replay_policy_distribution": dynamic.get("policy_distribution", {})},
            r_frequency_impact=replay_r,
            repair_decision="keep; fixed 1.5R/J46/J49 are comparator only",
            proof=["ei15r/final_dynamic_router_replay_summary.json", "tests/test_limit_order_flow.py"],
        ),
        _row(
            gate_id="telegram_order_deal_reconciliation_lifecycle",
            gate_name="Telegram/order/deal/reconciliation lifecycle gates",
            code_config_source=["src/notifications.py", "src/components/execution.py", "src/components/orchestrator.py"],
            runs_live=True,
            ran_in_vnext_replay=False,
            classification="live-only-vNext-native-lifecycle-gate",
            affected=affected,
            counts={
                "live_order_rows": len(live["order_rows"]),
                "live_deal_reconciliation_rows": len(live["deal_rows"]),
                "live_cost_rows": len(live["cost_rows"]),
            },
            r_frequency_impact={"replay_impact": "historical replay cannot create Telegram/broker deal lifecycle events"},
            repair_decision="repaired in notification parity commit; synthetic tests enforce vNext context",
            proof=["src/notifications.py", "tests/test_notifications.py", "LIVE_BROKER_DEAL_RECONCILIATION_LEDGER.jsonl"],
        ),
        _row(
            gate_id="candidate_intelligence_packet_null_zero_guard",
            gate_name="Candidate-intelligence null/zero/missing-reason guard",
            code_config_source=[
                "src/components/orchestrator.py::_refresh_vnext_candidate_intelligence_packet",
                "tests/test_vnext_broader_origin_orchestrator.py",
            ],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native-observability-and-replay-parity-gate",
            affected=affected,
            counts={
                "post_reload_live_candidate_rows": len(candidate_rows),
                "known_pre_packet_patch_records": sum(
                    1 for row in candidate_rows if not row.get("candidate_intelligence_packet_present")
                ),
                "dynamic_refusal_rows": live_final_counts.get(
                    "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
                    0,
                ),
            },
            r_frequency_impact={
                "replay_impact": "packet is verifier evidence for replay/live denominator parity, not a market filter"
            },
            repair_decision=(
                "repaired writer: every future broader-origin record carries explicit ran/not-run/missing-reason "
                "proof for candidate id, source, LTF/tick/broker, gates, dynamic policy, selected-cell risk, "
                "risk/lot, prop before/after, final order decision, and refusal/repair reasons"
            ),
            proof=[
                "src/components/orchestrator.py::_refresh_vnext_candidate_intelligence_packet",
                "tests/test_vnext_broader_origin_orchestrator.py::test_broader_origin_dynamic_refusal_record_has_complete_candidate_packet",
            ],
        ),
        _row(
            gate_id="heartbeat_flatten_orphan_reconciliation",
            gate_name="Heartbeat flatten/orphan-position/reconciliation monitor gates",
            code_config_source=[
                "src/safety/heartbeat_monitor.py",
                "scripts/watchdog.ps1",
                "scripts/verify_shadow_log_integrity.py::account_truth_reconciliation_status",
            ],
            runs_live=True,
            ran_in_vnext_replay=False,
            classification="live-only-vNext-native-operational-reconciliation-gate",
            affected={"symbols": sorted({row.get("symbol") for row in live["broker_rows"] if row.get("symbol")}), "origin_families": origins, "sessions": sessions, "policies": policies},
            counts={
                "live_deal_reconciliation_rows": len(live["deal_rows"]),
                "watchdog": live["watchdog"],
            },
            r_frequency_impact={
                "replay_impact": "heartbeat/orphan/deal reconciliation is live-broker/account truth only"
            },
            repair_decision="keep live-only; no replay authority, but lifecycle ledgers must carry exact no-event or missing-history proof",
            proof=[
                "src/safety/heartbeat_monitor.py",
                "scripts/watchdog.ps1",
                "LIVE_BROKER_DEAL_RECONCILIATION_LEDGER.jsonl",
            ],
        ),
        _row(
            gate_id="watchdog_startup_monitor",
            gate_name="Watchdog/startup/monitor gates",
            code_config_source=["start_all.bat", "scripts/watchdog.ps1", "src/safety/heartbeat_monitor.py"],
            runs_live=True,
            ran_in_vnext_replay=False,
            classification="live-only-vNext-native-operational-gate",
            affected={"symbols": sorted({row.get("symbol") for row in live["broker_rows"] if row.get("symbol")}), "origin_families": origins, "sessions": sessions, "policies": policies},
            counts={"startup": live["startup"], "watchdog": live["watchdog"]},
            r_frequency_impact={"replay_impact": "operational liveness gate not a historical market-row filter"},
            repair_decision="keep; 24-symbol startup/watchdog parity verified",
            proof=["LIVE_STARTUP_VERIFICATION.json", "LIVE_WATCHDOG_PARITY_VERIFICATION.json"],
        ),
        _row(
            gate_id="stale_config_profile_instrument_overrides",
            gate_name="Stale config/profile/instrument overrides, risk floors, slippage/tick values, old comments",
            code_config_source=["config/agent_config.yaml", "config/profiles/redacted_account.yaml", "VNEXT_ACTIVATION_REPAIR_STAGE03_BROKER_RUNTIME_SURFACE_2026-05-27.json"],
            runs_live=True,
            ran_in_vnext_replay=True,
            classification="vNext-native-with-stale-comment-watch",
            affected={"symbols": sorted({row.get("symbol") for row in live["broker_rows"] if row.get("symbol")}), "origin_families": origins, "sessions": sessions, "policies": policies},
            counts={
                "config_mode": cfg.get("gtos_vnext_runtime", {}).get("mode"),
                "apply_to_execution": cfg.get("gtos_vnext_runtime", {}).get("apply_to_execution"),
                "broker_spec_rows": len(live["broker_rows"]),
                "selected_rows_after_alias_repair": replay_rows,
            },
            r_frequency_impact=replay_r,
            repair_decision="keep under verifier watch; stale comments have no authority over vNext router fields",
            proof=["config/agent_config.yaml", "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl"],
        ),
    ]
    summary = {
        "schema_version": "vnext_live_replay_gate_stack_parity_summary_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "route_id": "vnext_live_activation_active_repair_companion_2026_05_28",
        "required_gate_count": len(REQUIRED_GATE_IDS),
        "ledger_rows": len(rows),
        "missing_required_gate_ids": sorted(set(REQUIRED_GATE_IDS) - {row["gate_id"] for row in rows}),
        "live_candidate_final_counts": live_final_counts,
        "live_gate1_pre_repair_reason_counts": dict(gate1_reason_counts),
        "replay_selected_rows": replay_rows,
        "broker_placement_ready_selected_rows_after_replay_included_live_gates": min(
            selected_projection["counts"].get("risk_positive_executable_current_broker_geometry", 0),
            dynamic_rows - router_refused,
        ),
        "dynamic_replay_metrics_after_replay_included_live_gates": replay_r,
        "current_production_dynamic_policy_distribution": current_production_policy_distribution,
        "current_production_policy_distribution_source": (
            "ei15r/momentum_policy_promotion_summary.json"
            if momentum.get("policy_distribution")
            else "ei15r/final_dynamic_router_replay_summary.json"
        ),
        "selected_trade_projection": selected_projection,
        "repair_assertions": {
            "raw_broader_origin_gate1_terminal_authority_removed": True,
            "final_gate1_runs_after_vnext_repair": True,
            "dynamic_target_gate1_static_2r_ceiling_removed_for_vnext": True,
            "selected_cell_and_prop_rechecked_before_order": True,
            "old_fixed_15r_j46_j49_live_default_allowed": False,
        },
        "outputs": {
            "ledger": str(LEDGER_PATH.relative_to(REPO_ROOT)),
            "summary": str(SUMMARY_PATH.relative_to(REPO_ROOT)),
        },
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify current outputs instead of writing them")
    args = parser.parse_args()
    rows, summary = build()
    if args.check:
        current_rows = _read_jsonl(LEDGER_PATH)
        current_summary = _read_json(SUMMARY_PATH, {})
        comparable_summary = dict(summary)
        comparable_summary.pop("generated_at_utc", None)
        current_comparable = dict(current_summary or {})
        current_comparable.pop("generated_at_utc", None)
        if current_rows != rows or current_comparable != comparable_summary:
            print(json.dumps({"status": "failed", "reason": "outputs_not_current"}, sort_keys=True))
            return 1
        print(json.dumps({"status": "passed", "rows": len(rows)}, sort_keys=True))
        return 0
    LIVE_ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "built", "rows": len(rows), "summary": str(SUMMARY_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
