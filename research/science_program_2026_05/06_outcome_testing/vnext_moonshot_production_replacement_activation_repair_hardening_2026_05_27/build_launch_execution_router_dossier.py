from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
sys.path.insert(0, str(REPO_ROOT))

from src.research.moonshot_default_off_policy_router import (
    DEFAULT_POLICY,
    EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES,
    EXECUTION_POLICY_IDS,
    MOMENTUM_EXHAUSTION_POLICY,
    PARTIAL_BE_RUNNER_POLICY,
    SUPPORTED_LIVE_EXECUTION_POLICIES,
)


DATE = "2026-05-27"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
SUMMARY = ROUTE_DIR / "ei15r" / "summary.json"
FINAL_ROUTER_SUMMARY = ROUTE_DIR / "ei15r" / "final_dynamic_router_replay_summary.json"
PROMOTION_SUMMARY = ROUTE_DIR / "ei15r" / "momentum_policy_promotion_summary.json"
PROMOTION_VERIFIER = ROUTE_DIR / "verify_execution_policy_momentum_promotion.py"
OUTPUT = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_EXECUTION_ROUTER_LAUNCH_DOSSIER_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=9", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def nested_get(mapping: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def resolve_symbol_rows(config: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, Any]]:
    runtime = config["gtos_vnext_runtime"]
    symbols = list(runtime["moonshot_dynamic_execution_router_broker_native_eligible_symbols"])
    base_risk_pct = nested_get(profile, "risk", "risk_per_trade_pct", default=nested_get(config, "risk", "risk_per_trade_pct"))
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        base_inst = nested_get(config, "instruments", symbol, default={}) or {}
        prof_inst = nested_get(profile, "instruments", symbol, default={}) or {}
        mt5_symbol = (
            nested_get(prof_inst, "market", "mt5_symbol")
            or nested_get(base_inst, "market", "mt5_symbol")
            or nested_get(base_inst, "market", "symbol")
            or symbol
        )
        tick_size = (
            nested_get(prof_inst, "market", "tick_size")
            or nested_get(base_inst, "market", "tick_size")
        )
        trading_enabled = (
            nested_get(prof_inst, "trading_enabled")
            if nested_get(prof_inst, "trading_enabled") is not None
            else nested_get(base_inst, "trading_enabled", default=True)
        )
        risk_pct = (
            nested_get(prof_inst, "risk", "risk_per_trade_pct")
            or nested_get(base_inst, "risk", "risk_per_trade_pct")
            or base_risk_pct
        )
        rows.append(
            {
                "config_symbol": symbol,
                "mt5_symbol": mt5_symbol,
                "trading_enabled": bool(trading_enabled),
                "profile_risk_pct": risk_pct,
                "tick_size": tick_size,
                "orchestrator_start_command": (
                    f"python run_agent.py --symbol {symbol} --mode %GTOS_MODE% --profile %GTOS_PROFILE%"
                ),
                "manual_launch_command": (
                    f"python run_agent.py --symbol {symbol} --mode live --profile redacted_account"
                ),
                "watchdog_log_path": f"logs/{symbol.lower().replace('_cash', '').replace('ukoil', 'ukoil')}.log",
                "tick_capture_command": (
                    f"python -m src.components.tick_capture --symbol {symbol} --mt5-symbol {mt5_symbol}"
                ),
            }
        )
    return rows


def route_policy_map() -> list[dict[str, Any]]:
    rows = [
        {
            "framework": "*",
            "origin_family": "*",
            "session_bucket": "*",
            "rule": "primary_policy",
            "raw_asof_policy": MOMENTUM_EXHAUSTION_POLICY,
            "live_execution_policy": MOMENTUM_EXHAUSTION_POLICY,
            "execution_policy_id": EXECUTION_POLICY_IDS[MOMENTUM_EXHAUSTION_POLICY],
            "fixed_15r_fallback_rewritten_to_default": False,
        }
    ]
    for family in EVIDENCE_BACKED_PARTIAL_BE_EXCEPTION_ORIGIN_FAMILIES:
        rows.append(
            {
                "framework": "*",
                "origin_family": family,
                "session_bucket": "*",
                "rule": "evidence_backed_origin_family_exception",
                "raw_asof_policy": PARTIAL_BE_RUNNER_POLICY,
                "live_execution_policy": PARTIAL_BE_RUNNER_POLICY,
                "execution_policy_id": EXECUTION_POLICY_IDS[PARTIAL_BE_RUNNER_POLICY],
                "fixed_15r_fallback_rewritten_to_default": False,
            }
        )
    return rows


def build() -> dict[str, Any]:
    config = read_yaml(REPO_ROOT / "config" / "agent_config.yaml")
    profile = read_yaml(REPO_ROOT / "config" / "profiles" / "redacted_account.yaml")
    runtime = config["gtos_vnext_runtime"]
    summary = read_json(SUMMARY)
    final_router = read_json(FINAL_ROUTER_SUMMARY)
    promotion = read_json(PROMOTION_SUMMARY)
    verdict = summary["dynamic_layer_verdict"]
    policy_metrics = summary["policy_metrics"]
    symbols = resolve_symbol_rows(config, profile)
    telemetry_paths = {
        "runtime_decisions": "shadow_logs/gtos_vnext_runtime_decisions.jsonl",
        "replacement_monitoring": runtime.get("replacement_monitoring_log_path"),
        "pending_limit_lifecycle": "shadow_logs/pending_limit_lifecycle.jsonl",
        "entry_and_close_slippage": "shadow_logs/slippage.jsonl",
        "trade_records": "knowledge_base/trade_records/{SYMBOL}/*.json",
        "tick_capture": "data/ticks/{SYMBOL}/{YYYY-MM-DD}.parquet",
        "tick_capture_heartbeat": "pipeline_state/daemon_heartbeat_tick_capture_{SYMBOL}.json",
    }
    checks = [
        "py -3 research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/verify_execution_intelligence_static_15r_ceiling_repair.py --check",
        "py -3 research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/verify_execution_intelligence_dynamic_router_replay.py --check",
        "py -3 research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/verify_execution_policy_momentum_promotion.py --check",
        "py -3 research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/verify_vnext_activation_repair_output_manifest.py --check",
        "py -3 research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/verify_vnext_activation_repair_route_state_integrity.py --check",
        "py -3 research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/build_vnext_activation_repair_final_semantic_state_proof.py",
        "py -3 -m pytest tests/test_moonshot_default_off_policy_router.py tests/test_limit_order_flow.py research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/test_execution_intelligence_static_15r_ceiling_repair.py -q",
    ]
    return {
        "schema_version": "vnext_launch_execution_router_dossier_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "generated_head": git_head(),
        "status": "launch_execution_router_wired_pending_post_commit_verification",
        "no_live_broker_mutation_performed_by_this_dossier": True,
        "launch_readiness_verdict": "READY_FOR_SUPERVISED_VNEXT_MOMENTUM_PRIMARY_EXCEPTION_ROUTER_LAUNCH_AFTER_CURRENT_ROUTE_VERIFIERS_PASS_FROM_COMMITTED_HEAD",
        "live_policy_contract": {
            "every_selected_trade_gets_execution_policy_id": True,
            "policy_selection_mode": "momentum_primary_with_evidence_backed_partial_exception_layer",
            "condition_challenger_enabled": runtime.get("moonshot_dynamic_execution_router_condition_challenger_enabled"),
            "fixed_1_5r_role": verdict.get("fixed_1_5r_role"),
            "fixed_1_5r_is_default": False,
            "primary_policy": runtime.get("moonshot_dynamic_execution_router_policy"),
            "exception_policy": runtime.get("moonshot_dynamic_execution_router_momentum_exception_policy"),
            "exception_origin_families": runtime.get(
                "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
            ),
            "selector_risk_baseline_scope_note": "Live selected-cell risk proof is selected-policy-aware; BE-keyed historical risk rows require policy-invariant broker geometry proof before runtime use.",
            "supported_live_execution_policies": list(SUPPORTED_LIVE_EXECUTION_POLICIES),
            "launch_router_policy_set": [MOMENTUM_EXHAUSTION_POLICY, PARTIAL_BE_RUNNER_POLICY],
            "execution_policy_ids": EXECUTION_POLICY_IDS,
            "router_feature_inputs": [
                "framework",
                "session_bucket",
                "current_bar_displacement_atr14",
                "liquidity_sweep_proxy_state",
                "candidate_origin_family",
                "selected_cell_risk_policy_identity_status",
            ],
            "unsupported_or_fixed_raw_policy_behavior": "refuse_or_rewrite_to_momentum_primary_without_fixed_1_5r_or_j46_j49_reactivation",
            "full_dynamic_router_replay_rows": final_router.get("selected_rows_processed"),
            "full_dynamic_router_metric_rows": final_router.get("replayable_metric_rows"),
            "condition_router_projection_gap_carried_forward_rows": final_router.get(
                "condition_router_projection_gap_carried_forward_rows"
            ),
            "promotion_metric_rows": (promotion.get("metrics") or {}).get("promoted_dynamic_router", {}).get("rows"),
            "promotion_total_r": (promotion.get("metrics") or {}).get("promoted_dynamic_router", {}).get("total_r"),
            "promotion_policy_distribution": promotion.get("policy_distribution"),
        },
        "policy_routing_rules": route_policy_map(),
        "runtime_surfaces": {
            "pending_intent_fields": [
                "gtos_vnext_execution_policy_id",
                "gtos_vnext_dynamic_policy_selected",
                "gtos_vnext_dynamic_policy_applied",
                "gtos_vnext_dynamic_be_trigger_r",
                "gtos_vnext_dynamic_final_target_r",
                "gtos_vnext_dynamic_trail_gap_r",
                "gtos_vnext_dynamic_momentum_pullback_r",
                "gtos_vnext_selected_cell_risk_selected_policy",
                "gtos_vnext_selected_cell_risk_source_policy",
                "gtos_vnext_selected_cell_risk_policy_identity_status",
            ],
            "fill_to_open_trade_surfaces": [
                "src/components/execution.py::set_limit_intent",
                "src/components/execution.py::check_limit_fill",
                "src/components/execution.py::open_trade",
                "src/components/execution.py::hydrate_vnext_dynamic_policy_from_record",
            ],
            "policy_manager_surfaces": [
                "src/components/execution.py::_execute_tp1_partial",
                "src/components/execution.py::_manage_vnext_trailing_runner",
                "src/components/execution.py::_manage_vnext_momentum_exhaustion",
                "src/components/execution.py::_execute_vnext_dynamic_final_close",
                "src/components/execution.py::_record_close_slippage_event",
            ],
            "orchestrator_surfaces": [
                "src/components/orchestrator.py::_evaluate_gtos_vnext_moonshot_dynamic_execution",
                "src/components/orchestrator.py::_vnext_dynamic_trade_context",
                "src/components/orchestrator.py::_gtos_vnext_pending_telemetry",
            ],
            "launcher_watchdog_surfaces": [
                "start_all.bat:24 orchestrators using %GTOS_MODE%/%GTOS_PROFILE%",
                "scripts/watchdog.ps1:$SymbolMap 24 symbols",
                "scripts/watchdog.ps1:$TickSymbolMap 24 symbol-to-MT5 aliases",
            ],
            "telemetry_paths": telemetry_paths,
            "rollback_apply_flags": [
                "gtos_vnext_runtime.moonshot_dynamic_execution_router_apply_to_execution",
                "gtos_vnext_runtime.moonshot_dynamic_execution_router_condition_challenger_enabled",
                "gtos_vnext_runtime.apply_to_execution",
                "gtos_vnext_runtime.enabled",
            ],
        },
        "launch_universe": {
            "profile": "redacted_account",
            "symbol_count": len(symbols),
            "symbols": symbols,
        },
        "execution_intelligence_evidence": {
            "summary_path": rel(SUMMARY),
            "summary_sha256": sha256_file(SUMMARY),
            "final_dynamic_router_replay_summary_path": rel(FINAL_ROUTER_SUMMARY),
            "final_dynamic_router_replay_summary_sha256": sha256_file(FINAL_ROUTER_SUMMARY),
            "momentum_policy_promotion_summary_path": rel(PROMOTION_SUMMARY),
            "momentum_policy_promotion_summary_sha256": sha256_file(PROMOTION_SUMMARY),
            "momentum_policy_promotion_verifier_path": rel(PROMOTION_VERIFIER),
            "selected_denominator_rows": summary.get("selected_rows_processed"),
            "dynamic_policy_rows": summary.get("dynamic_policy_rows"),
            "promoted_live_dynamic_router": {
                "selected_rows": promotion.get("selected_rows_processed"),
                "metric_rows": (promotion.get("metrics") or {}).get("promoted_dynamic_router", {}).get("rows"),
                "non_replayable_rows": promotion.get("non_replayable_rows"),
                "policy_distribution": promotion.get("policy_distribution"),
                "metrics": (promotion.get("metrics") or {}).get("promoted_dynamic_router"),
                "deltas": promotion.get("deltas"),
                "promotion_decision": promotion.get("promotion_decision"),
            },
            "actual_live_dynamic_router": {
                "role": (
                    "post_promotion_live_router_replay"
                    if promotion.get("source_dynamic_router_state")
                    == "post_promotion_router_already_current"
                    else "pre_promotion_mixed_condition_router_replay_diagnostic_not_launch_policy"
                ),
                "selected_rows": final_router.get("selected_rows_processed"),
                "metric_rows": final_router.get("replayable_metric_rows"),
                "non_replayable_rows": final_router.get("non_replayable_rows"),
                "router_refused_rows": final_router.get("router_refused_rows"),
                "condition_router_projection_gap_carried_forward_rows": final_router.get(
                    "condition_router_projection_gap_carried_forward_rows"
                ),
                "policy_distribution": final_router.get("policy_distribution"),
                "metrics": final_router.get("final_dynamic_router_metrics"),
                "global_policy_comparisons": final_router.get("global_policy_comparison_metrics"),
                "hindsight_best_regret": final_router.get("hindsight_best_regret"),
                "replay_source_class_counts": final_router.get("replay_source_class_counts"),
            },
            "gross_policy_metrics": {
                policy: policy_metrics[policy]
                for policy in (
                    "fixed_1_5r",
                    "be_after_trigger",
                    "partial_be_runner",
                    "trailing_runner",
                    "momentum_exhaustion",
                    "time_stop",
                    "hold_to_structure",
                )
                if policy in policy_metrics
            },
            "best_global_gross_replay_policy": verdict.get("best_implemented_policy"),
            "best_global_gross_replay_is_not_single_launch_policy": verdict.get(
                "gross_replay_policy_ranking_is_diagnostic_not_a_single_launch_policy"
            ),
            "m1_availability_status_counts": summary.get("m1_availability_status_counts"),
            "tick_availability_status_counts": summary.get("tick_availability_status_counts"),
            "missing_field_counts": summary.get("missing_field_counts"),
            "net_cost_verdict": verdict.get("net_r_verdict"),
            "gross_replay_policy_choice_not_erased_by_net_cost_gap": True,
        },
        "start_commands": {
            "batch_launcher": "start_all.bat",
            "watchdog": "powershell -ExecutionPolicy Bypass -File scripts/watchdog.ps1",
            "single_symbol_template": "python run_agent.py --symbol {SYMBOL} --mode live --profile redacted_account",
            "tick_capture_template": "python -m src.components.tick_capture --symbol {SYMBOL} --mt5-symbol {MT5_SYMBOL}",
        },
        "required_post_commit_verification_commands": checks,
    }


def main() -> int:
    payload = build()
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": rel(OUTPUT), "status": payload["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
