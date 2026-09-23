#!/usr/bin/env python3
"""Verify default-off candidate-book promotion plumbing.

This verifier proves the runtime-executable candidate path exists, stays default-off in active config, and
does not distort native exits. It does not touch MT5, brokers, VPS processes, credentials, or live orders.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


ROUTE = Path(__file__).resolve().parent
REPO = ROUTE.parents[2]
sys.path.insert(0, str(REPO))

RESULT_PATH = ROUTE / "CANDIDATE_PROMOTION_PLUMBING_RESULT.json"
MANIFEST_PATH = ROUTE / "CANDIDATE_PROMOTION_PLUMBING_OUTPUT_MANIFEST.json"
AUDIT_PATH = ROUTE / "CANDIDATE_PROMOTION_PLUMBING_COMPLETION_AUDIT.json"

EXPECTED_EXECUTABLE = {
    "vol_compression",
    "asian_fade",
    "ny_crypto_momentum",
    "metal_session_reversion",
    "asia_pdl_fade",
    "orb_crypto_london",
    "liq_asia_up_low_metal",
    "kz_london_crypto_low",
    "vss_fxcross_london_up_low",
}
EXPECTED_EXIT_PROFILES = {
    "vol_compression": {"policy": "time_stop", "final_from_intent": True, "final_target_r": 3.0, "time_stop_bars": 7680},
    "asian_fade": {"policy": "trailing_runner", "final_target_r": None, "broker_take_profit_mode": "none", "trigger_r": 0.5, "trail_gap_r": 0.5, "time_stop_bars": 48},
    "ny_crypto_momentum": {"policy": "time_stop", "final_target_r": None, "broker_take_profit_mode": "none", "time_stop_bars": 20},
    "metal_session_reversion": {"policy": "trailing_runner", "final_target_r": None, "broker_take_profit_mode": "none", "trigger_r": 0.6, "trail_gap_r": 0.5, "time_stop_bars": 24},
    "asia_pdl_fade": {"policy": "time_stop", "final_from_intent": True, "final_target_r": 3.0, "time_stop_bars": 32},
    "orb_crypto_london": {"policy": "time_stop", "final_from_intent": True, "final_target_r": 2.0, "time_stop_bars": 80},
    "liq_asia_up_low_metal": {"policy": "time_stop", "final_from_intent": True, "final_target_r": 3.0, "time_stop_bars": 16},
    "kz_london_crypto_low": {"policy": "time_stop", "final_target_r": None, "broker_take_profit_mode": "none", "time_stop_bars": 32},
    "vss_fxcross_london_up_low": {"policy": "time_stop", "final_from_intent": True, "final_target_r": 2.0, "time_stop_bars": 48},
}


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not contain a JSON object")
    return data


def main() -> int:
    from src.components.ultimate_book import admission
    from src.components.ultimate_book.bridge import DEFAULT_CONFIG
    from src.components.ultimate_book.execution_packets import SLEEVE_EXIT_PROFILES
    from src.components.ultimate_book.sleeves import candidate_registry
    from src.components.ultimate_book.sleeves.registry import CANDIDATE_BUILT, active_specs

    errors: list[dict] = []
    warnings: list[dict] = []

    def require(name: str, cond: bool, detail: object = None) -> None:
        if not cond:
            errors.append({"check": name, "detail": detail})

    cfg = yaml.safe_load((REPO / "config/agent_config.yaml").read_text(encoding="utf-8"))
    runtime_cfg = cfg.get("gtos_vnext_runtime", {})

    require("bridge_default_candidate_book_off", DEFAULT_CONFIG["ultimate_book_include_candidate_book"] is False)
    require("active_config_candidate_book_off", runtime_cfg.get("ultimate_book_include_candidate_book") is False)
    require(
        "candidate_profile_matches",
        runtime_cfg.get("ultimate_book_candidate_book_profile") == admission.CANDIDATE_BOOK_PROFILE,
        runtime_cfg.get("ultimate_book_candidate_book_profile"),
    )

    require(
        "runtime_executable_candidate_set_exact",
        set(candidate_registry.RUNTIME_EXECUTABLE_CANDIDATE_NAMES) == EXPECTED_EXECUTABLE,
        sorted(candidate_registry.RUNTIME_EXECUTABLE_CANDIDATE_NAMES),
    )
    require(
        "native_exit_work_set_empty",
        candidate_registry.CANDIDATE_RUNTIME_BLOCKERS == {},
        sorted(candidate_registry.CANDIDATE_RUNTIME_BLOCKERS),
    )

    reg_off = admission.effective_registry(include_clean3=False, include_clean4=False)
    reg_on = admission.effective_registry(
        include_clean3=False,
        include_clean4=False,
        include_candidate_book=True,
    )
    require("effective_registry_default_excludes_candidates", not (EXPECTED_EXECUTABLE & set(reg_off)))
    require("effective_registry_flag_includes_executable", EXPECTED_EXECUTABLE <= set(reg_on), sorted(reg_on))

    specs_default = {s.tag for s in active_specs(None)}
    specs_candidate = {s.tag for s in active_specs(None, include_candidate_book=True)}
    require("generation_default_excludes_candidates", not (EXPECTED_EXECUTABLE & specs_default))
    require("generation_flag_includes_candidates", EXPECTED_EXECUTABLE <= specs_candidate, sorted(specs_candidate))
    require("candidate_generation_registry_exact", set(CANDIDATE_BUILT) == EXPECTED_EXECUTABLE, sorted(CANDIDATE_BUILT))
    require(
        "vss_aux_d1_required",
        CANDIDATE_BUILT["vss_fxcross_london_up_low"].aux_count > 0
        and CANDIDATE_BUILT["vss_fxcross_london_up_low"].aux_timeframe is not None,
    )

    for sleeve, expected in EXPECTED_EXIT_PROFILES.items():
        prof = SLEEVE_EXIT_PROFILES.get(sleeve)
        require(f"{sleeve}_exit_profile_present", isinstance(prof, dict), prof)
        if not isinstance(prof, dict):
            continue
        for key, expected_value in expected.items():
            require(f"{sleeve}_{key}", prof.get(key) == expected_value, prof)

    unified_path = (
        REPO
        / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/UNIFIED_BOOK_MC_RESULT.json"
    )
    unified = _read_json(unified_path)
    current = unified.get("current_canonical", {})
    mc = current.get("mc", {})
    require("unified_book_still_marked_not_live_authority", "NOT_LIVE_AUTHORITY" in str(unified.get("decision", "")))
    require("unified_book_confidence_matches_catalog", unified.get("conf") == candidate_registry.CANDIDATE_CONFIDENCE)

    instrument_map = cfg.get("instruments", {}) or {}
    all_candidate_symbols = sorted(
        {sym for name in EXPECTED_EXECUTABLE for sym in candidate_registry.CANDIDATES[name].on_surface}
    )
    missing_base_instruments = [sym for sym in all_candidate_symbols if sym not in instrument_map]
    if missing_base_instruments:
        warnings.append({
            "check": "candidate_symbol_profile_alias_work_item",
            "detail": missing_base_instruments,
        })

    activation_work_items = [
        "rerun unified MC/replay on the actual core8+A8 active profile before any candidate-book live activation",
        "prove broker-profile symbol aliases and MT5 history availability for candidate-only symbols and reintroduced FX candidate symbols",
        "seal May 2026 rolling/stress replay artifacts into tracked manifests before deployment dossier claims",
        "package foundation vol/distribution/MoE as shadow-only shrink-first intelligence, not as live trained AI",
    ]

    result = {
        "schema": "gtos.final_moonshot.candidate_promotion_plumbing_result.v2",
        "ok": not errors,
        "decision": "INSTALL_DEFAULT_OFF_RUNTIME_EXECUTABLE_NATIVE_EXIT_CANDIDATE_BOOK_PLUMBING",
        "runtime_effect_now": "none_candidate_book_flag_false_in_active_config",
        "orderflow_used": False,
        "no_broker_or_order_mutation": True,
        "candidate_book_profile": admission.CANDIDATE_BOOK_PROFILE,
        "runtime_executable_candidate_names": sorted(EXPECTED_EXECUTABLE),
        "native_exit_work_item_candidates": candidate_registry.CANDIDATE_RUNTIME_BLOCKERS,
        "native_exit_contracts_supported": [
            "fixed_target_time_stop_with_broker_tp",
            "capless_trailing_runner_no_broker_tp",
            "targetless_time_stop_no_broker_tp",
        ],
        "quarantined_candidates": sorted(
            name for name, confidence in candidate_registry.CANDIDATE_CONFIDENCE.items() if confidence == 0.0
        ),
        "unified_book_context": {
            "decision": unified.get("decision"),
            "current_canonical_sharpe": current.get("sharpe"),
            "current_canonical_train_oos_sealed": current.get("splits"),
            "current_canonical_mc": mc,
            "monthly_pct": mc.get("monthly_pct"),
            "p_pass": mc.get("p_pass"),
            "p_fail_dd": mc.get("p_fail_dd"),
            "worst_day_pct": mc.get("worst_day_pct"),
        },
        "candidate_symbol_profile_alias_work_items": missing_base_instruments,
        "activation_work_items": activation_work_items,
        "errors": errors,
        "warnings": warnings,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest_files = sorted(p.name for p in ROUTE.iterdir() if p.is_file() and p.name != MANIFEST_PATH.name)
    manifest = {
        "schema": "gtos.final_moonshot.candidate_promotion_plumbing_manifest.v2",
        "ok": True,
        "route": str(ROUTE.relative_to(REPO)),
        "files": manifest_files,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit = {
        "schema": "gtos.final_moonshot.candidate_promotion_plumbing_completion_audit.v2",
        "ok": not errors,
        "result_path": str(RESULT_PATH.relative_to(REPO)),
        "manifest_path": str(MANIFEST_PATH.relative_to(REPO)),
        "no_broker_or_order_mutation": True,
        "mt5_bridge_touched": False,
        "vps_process_touched": False,
        "runtime_behavior_mutation": "none_active_candidate_book_flag_false",
        "errors": errors,
        "warnings": warnings,
    }
    AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
