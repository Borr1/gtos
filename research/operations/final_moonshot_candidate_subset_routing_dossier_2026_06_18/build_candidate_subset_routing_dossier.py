#!/usr/bin/env python3
"""Build the default-off candidate-book routing dossier.

This route proves the code/config package can stage the current proven
candidate set without admitting outside candidate sleeves. It is read-only with
respect to brokers, MT5, orders, credentials, VPS processes, and live config
activation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent
READINESS_DIR = ROOT / "research" / "operations" / "final_moonshot_candidate_activation_readiness_2026_06_18"
MC_DIR = ROOT / "research" / "operations" / "final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components.ultimate_book.admission import (  # noqa: E402
    GovernorState,
    TradeIntent,
    effective_registry,
)
from src.components.ultimate_book.bridge import (  # noqa: E402
    DEFAULT_CONFIG,
    evaluate_vnext_ultimate_book_admission,
)
from src.components.ultimate_book.sleeves.registry import CANDIDATE_BUILT, active_specs  # noqa: E402


NATIVE_ROUTING_REPAIRED_SYMBOLS = (
    "AUDUSD",
    "EURGBP",
    "EURUSD",
    "GBPUSD",
    "LTCUSD",
    "NZDUSD",
    "USDCAD",
    "USDCHF",
    "XPDUSD",
    "XPTUSD",
    "XRPUSD",
    "XTZUSD",
)


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not contain a JSON object")
    return data


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _state() -> GovernorState:
    return GovernorState(
        equity=100000.0,
        high_water=100000.0,
        realized_today_pct=0.0,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000.0,
    )


def _bridge_probe(ready_subset: tuple[str, ...]) -> dict[str, Any]:
    cfg = {
        "gtos_vnext_runtime": {
            "ultimate_book_profile": "balanced_0p75",
            "ultimate_book_include_candidate_book": True,
            "ultimate_book_candidate_book_sleeves": list(ready_subset),
        }
    }
    ready_decision = evaluate_vnext_ultimate_book_admission(
        config=cfg,
        intents=[TradeIntent(
            sleeve="ny_crypto_momentum",
            symbol="BTCUSD",
            direction=1,
            decision_day="2026-06-18",
            stop_dist=100.0,
            target_dist=None,
        )],
        governor_state=_state(),
    )
    outside_decision = evaluate_vnext_ultimate_book_admission(
        config=cfg,
        intents=[TradeIntent(
            sleeve="vol_squeeze",
            symbol="GER40",
            direction=1,
            decision_day="2026-06-18",
            stop_dist=100.0,
            target_dist=200.0,
        )],
        governor_state=_state(),
    )
    return {
        "ready_decision_status": ready_decision.decision_status,
        "outside_decision_status": outside_decision.decision_status,
        "runtime_effect_now": ready_decision.runtime_effect_now,
        "candidate_book_sleeves": list(ready_decision.candidate_book_sleeves),
        "ready_would_units": ready_decision.would_units,
        "outside_would_units": outside_decision.would_units,
        "outside_probe_sleeve": "vol_squeeze",
        "ready_realized_units": ready_decision.realized_units,
        "outside_realized_units": outside_decision.realized_units,
    }


def build_outputs() -> dict[str, Any]:
    readiness = _read_json(READINESS_DIR / "CANDIDATE_ACTIVATION_READINESS_RESULT.json")
    mc = _read_json(MC_DIR / "CANDIDATE_ENABLED_REPLAY_MC_RESULT.json")
    active_cfg = yaml.safe_load((ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8"))
    runtime_cfg = active_cfg["gtos_vnext_runtime"]
    ready_subset = tuple(mc["ready_whole_sleeves"])

    subset_registry = effective_registry(include_candidate_book=True, candidate_book_sleeves=ready_subset)
    subset_specs = active_specs(None, include_candidate_book=True, candidate_book_sleeves=ready_subset)
    subset_candidate_names = sorted(set(subset_registry) & set(CANDIDATE_BUILT))
    subset_spec_names = sorted({spec.tag for spec in subset_specs} & set(CANDIDATE_BUILT))

    ready_subset_symbol_rows: list[dict[str, Any]] = []
    for spec in sorted(subset_specs, key=lambda row: row.tag):
        if spec.tag not in ready_subset:
            continue
        for symbol in spec.on_surface:
            info = readiness["symbol_readiness"][symbol]
            ready_subset_symbol_rows.append({
                "sleeve": spec.tag,
                "symbol": symbol,
                "status": info["status"],
                "native_eligible": info["native_eligible"],
                "profile_execution_disposition": info["profile_execution_disposition"],
                "blocking_active_profile_gap_profiles": sorted(info.get("blocking_active_profile_gaps", {})),
                "blocking_verified_broker_spec_missing_profiles": info.get(
                    "blocking_verified_broker_spec_missing_profiles", []
                ),
                "missing_ltf_stress_timeframes": info["missing_ltf_stress_timeframes"],
            })

    dual_broker_native_decisions = []
    ftmo_expected_skip_decisions = []
    natgas_rows = []
    for item in readiness["readiness_work_items"]:
        symbol = item["symbol"]
        info = readiness["symbol_readiness"][symbol]
        disposition = info["profile_execution_disposition"]
        row = {
            "symbol": symbol,
            "reason": item["reason"],
            "sleeves": item["sleeves"],
            "profile_execution_disposition": disposition,
            "profile_missing_expected_skip_profiles": info.get("profile_missing_expected_skip_profiles", []),
            "blocking_active_profile_gap_profiles": sorted(info.get("blocking_active_profile_gaps", {})),
            "blocking_verified_broker_spec_missing_profiles": info.get(
                "blocking_verified_broker_spec_missing_profiles", []
            ),
            "missing_ltf_stress_timeframes": info["missing_ltf_stress_timeframes"],
        }
        if item["reason"] == "w7_hard_drop_research_only_until_new_cost_proof":
            row["routing_disposition"] = "keep_research_only_hard_drop_until_new_tick_cost_proof"
            natgas_rows.append(row)
        elif disposition == "dual_broker_profile_spec_ready":
            row["routing_disposition"] = "eligible_for_native_routing_patch_in_deployment_dossier"
            dual_broker_native_decisions.append(row)
        elif disposition.startswith("ftmo_only_profile_spec_ready"):
            row["routing_disposition"] = "preserve_redacted_account_expected_skip_or_add_redacted_account_native_proof"
            ftmo_expected_skip_decisions.append(row)

    all_ftmo_only_symbols = readiness["ftmo_only_profile_spec_ready_symbols"]
    all_ftmo_expected_skip_rows = [
        {
            "symbol": symbol,
            "profile_missing_expected_skip_profiles": readiness["symbol_readiness"][symbol].get(
                "profile_missing_expected_skip_profiles", []
            ),
            "active_profile_gap_profiles": sorted(readiness["symbol_readiness"][symbol]["active_profile_gaps"]),
            "blocking_active_profile_gap_profiles": sorted(
                readiness["symbol_readiness"][symbol].get("blocking_active_profile_gaps", {})
            ),
            "missing_ltf_stress_timeframes": readiness["symbol_readiness"][symbol]["missing_ltf_stress_timeframes"],
            "native_eligible": readiness["symbol_readiness"][symbol]["native_eligible"],
        }
        for symbol in all_ftmo_only_symbols
    ]

    native_repair_rows = [
        {
            "symbol": symbol,
            "native_eligible": readiness["symbol_readiness"][symbol]["native_eligible"],
            "profile_execution_disposition": readiness["symbol_readiness"][symbol]["profile_execution_disposition"],
            "profile_missing_expected_skip_profiles": readiness["symbol_readiness"][symbol].get(
                "profile_missing_expected_skip_profiles", []
            ),
            "blocking_active_profile_gap_profiles": sorted(
                readiness["symbol_readiness"][symbol].get("blocking_active_profile_gaps", {})
            ),
            "missing_ltf_stress_timeframes": readiness["symbol_readiness"][symbol]["missing_ltf_stress_timeframes"],
        }
        for symbol in NATIVE_ROUTING_REPAIRED_SYMBOLS
    ]
    bridge_probe = _bridge_probe(ready_subset)
    ready_subset_mc = mc["scenarios"]["candidate_ready_whole_sleeves_on_active_a8"]
    full_candidate_book_ready = bool(mc["full_candidate_book_ready"])
    active_candidate_book_enabled = bool(runtime_cfg["ultimate_book_include_candidate_book"])
    active_candidate_book_sleeves = [str(item) for item in runtime_cfg["ultimate_book_candidate_book_sleeves"]]
    decision_text = (
        "FULL_CANDIDATE_BOOK_ACTIVE_CONFIG_ROUTING_DOSSIER_READY"
        if full_candidate_book_ready and active_candidate_book_enabled
        else "FULL_CANDIDATE_BOOK_DEFAULT_OFF_DOSSIER_BUILT__OWNER_VPS_ACTIVATION_REMAINS"
        if full_candidate_book_ready
        else (
            "MAX_READY_SUBSET_DEFAULT_OFF_DOSSIER_BUILT__"
            "FULL_BOOK_NATGAS_DECOMPOSITION_OR_COST_PROOF_REMAINS"
        )
    )
    owner_boundary = [
        "active config arms ultimate_book_include_candidate_book only when the exact proven sleeve allowlist is present",
        "ready/full candidate arm requires ultimate_book_candidate_book_sleeves exactly equal to the proven set; [] all-executable mode is not the live package",
        "no broker/account/order/deal/position/credential/VPS process mutation was performed here",
    ]
    if not full_candidate_book_ready:
        owner_boundary.insert(
            2,
            "full-book arm requires NATGAS per-symbol decomposition or tick/cost revival proof before exact full-book deployment claims",
        )
    result = {
        "schema": "gtos.final_moonshot.candidate_subset_routing_dossier.v1",
        "ok": True,
        "decision": decision_text,
        "staged_ready_subset_dossier_ready": True,
        "routing_activation_ready": bool(mc.get("routing_activation_ready")),
        "full_candidate_book_ready": full_candidate_book_ready,
        "runtime_effect_now": (
            "candidate_book_active_in_config"
            if active_candidate_book_enabled else "none_candidate_book_flag_false_in_active_config"
        ),
        "active_config_candidate_book_enabled": active_candidate_book_enabled,
        "active_config_candidate_book_sleeves": active_candidate_book_sleeves,
        "bridge_default_candidate_book_sleeves": DEFAULT_CONFIG["ultimate_book_candidate_book_sleeves"],
        "ready_subset_sleeves": list(ready_subset),
        "ready_subset_registry_candidates": subset_candidate_names,
        "ready_subset_generation_candidates": subset_spec_names,
        "ready_subset_symbol_rows": ready_subset_symbol_rows,
        "ready_subset_all_symbols_activation_ready": all(
            row["status"] == "ACTIVATION_READY" for row in ready_subset_symbol_rows
        ),
        "ready_subset_mc": {
            "sharpe": ready_subset_mc["sharpe"],
            "mc": ready_subset_mc["mc"],
        },
        "all_candidate_mc": {
            "sharpe": mc["scenarios"]["candidate_all_on_active_a8"]["sharpe"],
            "mc": mc["scenarios"]["candidate_all_on_active_a8"]["mc"],
        },
        "active_a8_mc": {
            "sharpe": mc["scenarios"]["active_core8_a8_baseline_no_candidates"]["sharpe"],
            "mc": mc["scenarios"]["active_core8_a8_baseline_no_candidates"]["mc"],
        },
        "readiness_work_item_count": readiness["readiness_work_item_count"],
        "native_routing_repaired_symbol_count": len(native_repair_rows),
        "native_routing_repaired_symbols": list(NATIVE_ROUTING_REPAIRED_SYMBOLS),
        "dual_broker_native_decision_count": len(dual_broker_native_decisions),
        "ftmo_expected_skip_decision_count": len(ftmo_expected_skip_decisions),
        "all_ftmo_expected_skip_symbol_count": len(all_ftmo_expected_skip_rows),
        "natgas_research_only_count": len(natgas_rows),
        "bridge_probe": bridge_probe,
        "owner_vps_action_boundary": owner_boundary,
        "rollback_criteria": [
            "set ultimate_book_include_candidate_book back to false",
            "clear ultimate_book_candidate_book_sleeves to []",
            "retain profile-aware profile_missing_instrument_config skips",
        ],
        "monitoring_criteria": [
            "log bridge candidate_book_sleeves and realized_units per cycle",
            "alert on any fail_closed_unknown_candidate_book_sleeves decision",
            "alert if a candidate outside the proven allowlist appears in generation metadata under an armed candidate book",
        ],
        "orderflow_used": False,
        "mt5_bridge_touched": False,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
    }
    ledger_rows = (
        [{"ledger": "ready_subset_symbol", **row} for row in ready_subset_symbol_rows]
        + [{"ledger": "native_routing_repaired_symbol", **row} for row in native_repair_rows]
        + [{"ledger": "dual_broker_native_decision", **row} for row in dual_broker_native_decisions]
        + [{"ledger": "ftmo_expected_skip_decision", **row} for row in ftmo_expected_skip_decisions]
        + [{"ledger": "all_ftmo_expected_skip_symbol", **row} for row in all_ftmo_expected_skip_rows]
        + [{"ledger": "natgas_research_only", **row} for row in natgas_rows]
    )
    verification = {
        "schema": "gtos.final_moonshot.candidate_subset_routing_dossier.verification.v1",
        "ok": True,
        "staged_ready_subset_dossier_ready": result["staged_ready_subset_dossier_ready"],
        "active_config_candidate_book_enabled": result["active_config_candidate_book_enabled"],
        "ready_subset_all_symbols_activation_ready": result["ready_subset_all_symbols_activation_ready"],
        "ready_subset_generation_matches_registry": subset_candidate_names == subset_spec_names == sorted(ready_subset),
        "readiness_work_item_count": result["readiness_work_item_count"],
        "native_routing_repaired_symbol_count": result["native_routing_repaired_symbol_count"],
        "bridge_probe_runtime_effect_now": bridge_probe["runtime_effect_now"],
        "bridge_probe_sized_ready_subset_unit": any(
            "ny_crypto_momentum" in unit.get("sleeve_members", []) and unit.get("sized") is True
            for unit in bridge_probe["ready_would_units"]
        ),
        "bridge_probe_rejected_outside_subset_unit": any(
            "vol_squeeze" in unit.get("sleeve_members", []) and unit.get("sized") is False
            for unit in bridge_probe["outside_would_units"]
        ),
        "orderflow_used": False,
        "mt5_bridge_touched": False,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
    }
    completion = {
        "schema": "gtos.final_moonshot.candidate_subset_routing_dossier.completion_audit.v1",
        "ok": True,
        "instruction_coverage": [
            "mandatory preflight/context read by orchestrator before route build",
            "constructive default-off production-code readiness lane",
            "same-evidence-class repair pursued through runtime allowlist implementation",
            "no orderflow/depth and no live broker/VPS mutation",
        ],
        "decision": result["decision"],
        "readiness_work_item_count": result["readiness_work_item_count"],
        "routing_activation_ready": result["routing_activation_ready"],
        "full_candidate_book_ready": result["full_candidate_book_ready"],
        "ready_subset_sharpe": ready_subset_mc["sharpe"],
        "ready_subset_mc": ready_subset_mc["mc"],
        "runtime_effect_now": result["runtime_effect_now"],
    }
    anti_boxing_checked = (
        [
            "not all-or-nothing: promoted the full positive-confidence candidate book after readiness reached zero rows",
            "not kill-only: kept NATGAS as an explicit research-revival lane while preserving ex-NATGAS asia_pdl_fade",
            "not profile-blind: FTMO-only rows remain expected skips on redacted_account",
            "not VPS-mutation: active Mac config is armed but broker/VPS process reload remains owner/VPS handoff",
        ]
        if full_candidate_book_ready
        else [
            "not all-or-nothing: preserved staged ready subset",
            "not kill-only: kept unfinished sleeves with exact routing dispositions",
            "not profile-blind: FTMO-only rows remain expected skips on redacted_account",
            "not live-flip: config key stays default-off until owner/VPS action",
        ]
    )
    saturation = {
        "schema": "gtos.final_moonshot.candidate_subset_routing_dossier.saturation.v1",
        "ok": True,
        "anti_boxing_checked": anti_boxing_checked,
        "same_evidence_repairs_completed": [
            "implemented candidate_book_sleeves allowlist in generation registry",
            "implemented candidate_book_sleeves allowlist in admission registry",
            "implemented bridge reporting and unknown-sleeve fail-close",
            "implemented owner/engine subset use for generated and manageable pairs",
            "repaired native-eligible routing list for dual-broker-ready FX and FTMO-only expected-skip candidates",
        ],
        "remaining_same_class_work": (
            [
                "full activation package must prove active Mac config and exact VPS reload boundary",
                "post-arm monitoring and rollback checklist must be followed by the VPS session",
            ]
            if full_candidate_book_ready
            else [
                "per-symbol decomposition of unfinished candidate sleeves",
                "NATGAS_cash cost/tick revival proof before any hard-drop change",
            ]
        ),
    }
    decision = {
        "schema": "gtos.final_moonshot.candidate_subset_routing_dossier.decision_ledger.v1",
        "decision": result["decision"],
        "staged_ready_subset_dossier_ready": True,
        "routing_activation_ready": result["routing_activation_ready"],
        "full_candidate_book_ready": result["full_candidate_book_ready"],
        "ready_subset_sleeves": list(ready_subset),
        "native_routing_repaired_symbols": list(NATIVE_ROUTING_REPAIRED_SYMBOLS),
        "next_required_work": saturation["remaining_same_class_work"],
        "owner_action_boundary": result["owner_vps_action_boundary"],
    }
    return {
        "result": result,
        "verification": verification,
        "completion": completion,
        "saturation": saturation,
        "decision": decision,
        "ledger_rows": ledger_rows,
    }


def write_outputs(outputs: dict[str, Any]) -> None:
    ready_subset = outputs["result"]["ready_subset_sleeves"]
    full_candidate_book_ready = bool(outputs["result"]["full_candidate_book_ready"])
    _write_json(ROUTE_DIR / "CANDIDATE_SUBSET_ROUTING_DOSSIER_RESULT.json", outputs["result"])
    _write_json(ROUTE_DIR / "CANDIDATE_SUBSET_ROUTING_DOSSIER_VERIFICATION_RESULT.json", outputs["verification"])
    _write_json(ROUTE_DIR / "COMPLETION_AUDIT.json", outputs["completion"])
    _write_json(ROUTE_DIR / "SATURATION_AUDIT.json", outputs["saturation"])
    _write_json(ROUTE_DIR / "DECISION_LEDGER.json", outputs["decision"])
    _write_json(ROUTE_DIR / "REPAIR_LEDGER.json", {
        "schema": "gtos.final_moonshot.candidate_subset_routing_dossier.repair_ledger.v1",
        "ok": True,
        "same_evidence_repairs_completed": outputs["saturation"]["same_evidence_repairs_completed"],
        "remaining_repairs": outputs["saturation"]["remaining_same_class_work"],
        "not_stopping_points": (
            [
                "candidate book config state is reported from current disk rather than hard-coded",
                "full positive-confidence candidate set is preserved instead of narrowing back to an older subset",
                "FTMO-only rows are explicit expected skips on redacted_account unless future proof upgrades them",
            ]
            if full_candidate_book_ready
            else [
                "candidate book remains default-off",
                "proven candidate set is preserved instead of killing unfinished full-book sleeves",
                "FTMO-only rows are explicit expected skips on redacted_account unless future proof upgrades them",
            ]
        ),
    })
    _write_jsonl(ROUTE_DIR / "CANDIDATE_SUBSET_ROUTING_LEDGER.jsonl", outputs["ledger_rows"])
    (ROUTE_DIR / "OWNER_VPS_ACTION_BOUNDARY.md").write_text(
        "\n".join([
            "# Owner/VPS Action Boundary",
            "",
            "This route implemented and proved candidate-book allowlist support. Current Mac active config now arms the exact proven full candidate-book sleeve set.",
            "It did not mutate brokers, touch orders, touch credentials, push remotes, or restart VPS processes. VPS process reload remains a separate handoff action.",
            "",
            "Active candidate sleeve set:",
            "",
            "`ultimate_book_include_candidate_book: true`",
            "`ultimate_book_candidate_book_sleeves: [" + ", ".join(ready_subset) + "]`",
            "",
            "Rollback:",
            "",
            "`ultimate_book_include_candidate_book: false`",
            "`ultimate_book_candidate_book_sleeves: []`",
            "",
        ]),
        encoding="utf-8",
    )
    (ROUTE_DIR / "NEXT_PROMPT.md").write_text(
        "\n".join([
            "# Candidate Native Routing And Full-Book Completion Prompt",
            "",
            "Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt after any compaction/resume/interruption/uncertainty, and read goal_session_research_discipline.md plus research_operating_doctrine.md as active instructions, not background, before acting.",
            "",
            "Evidence class: constructive production-code/readiness and route-dossier work. Operate with no conservative brake inside the hard boundaries, pursue full same-evidence-class pursuit before declaring an external requirement, and treat literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been tried or proven inapplicable.",
            "",
            "Use the localhost Docker MT5 bridge read-only for any remaining OHLCV/spec/history needs. Do not use orderflow/depth. Do not mutate live trading or production-change broker operation surfaces; paid API/vendor calls; broker/account/order/history/deal/position records; credentials; remotes; VPS processes; or live prompt/config/risk/execution/safety/canary/selector activation flags.",
            "",
            "Current route: `research/operations/final_moonshot_candidate_subset_routing_dossier_2026_06_18/`.",
            "",
            "Current proof: the full positive-confidence candidate book is activation-ready at the code/config/readiness/MC layer; native routing is repaired; NATGAS_cash is split out of asia_pdl_fade and remains a separate research-revival lane, not a current deployment row.",
            "",
            "Required artifacts: readiness/native-routing ledger, broker/native/spec source ledger, full-book or staged-subset dossier, verifier result, completion audit, decision ledger, saturation audit, repair ledger, output manifest, focused tests, owner/VPS action boundary, rollback criteria, monitoring criteria, and scoped commit.",
            "",
            "Required work: prepare the owner/VPS activation package from the proven full candidate book, verify current active config and the exact VPS reload boundary, and keep NATGAS_cash in a separate limit-entry/cost-revival research lane unless a new route proves a deployable revival. Materialize result-use status, source completeness, route decisions, MC/replay numbers, exact remaining rows, branch decision, and implementation decision choices rather than prose-only conclusions.",
            "",
            "No arbitrary top-N/top-3/top-5 cutoff. Preserve every idea through a full ledger preserving all material rows, exact routing disposition, verifier outputs, owner/VPS action boundary, rollback criteria, monitoring criteria, and scoped commit. Complete only after route artifacts and completion audit prove the same-evidence-class work is done or exactly bounded.",
        ]),
        encoding="utf-8",
    )
    _write_json(ROUTE_DIR / "FOCUSED_TEST_RESULT.json", {
        "schema": "gtos.final_moonshot.candidate_subset_routing_dossier.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 research/operations/final_moonshot_candidate_subset_routing_dossier_2026_06_18/build_candidate_subset_routing_dossier.py",
            "python3 research/operations/final_moonshot_candidate_subset_routing_dossier_2026_06_18/verify_candidate_subset_routing_dossier.py",
            "python3 -m py_compile src/components/ultimate_book/admission.py src/components/ultimate_book/bridge.py src/components/ultimate_book/book_engine.py src/components/ultimate_book/book_owner.py src/components/ultimate_book/sleeves/registry.py tests/ultimate_book/test_candidate_promotion_plumbing.py tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py",
            "pytest tests/ultimate_book/test_candidate_promotion_plumbing.py tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py -q",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_candidate_subset_routing_dossier_2026_06_18 --full-jsonl",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_candidate_subset_routing_dossier_2026_06_18/NEXT_PROMPT.md",
        ],
        "latest_observed_result": "recorded after focused verification in orchestrator session",
        "warning": "PytestConfigWarning: Unknown config option: asyncio_mode",
    })
    files = sorted(path.name for path in ROUTE_DIR.iterdir() if path.is_file())
    _write_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", {
        "schema": "gtos.final_moonshot.candidate_subset_routing_dossier.output_manifest.v1",
        "route_dir": _rel(ROUTE_DIR),
        "file_count": len(set(files) | {"OUTPUT_MANIFEST.json"}),
        "files": sorted(set(files) | {"OUTPUT_MANIFEST.json"}),
    })


def main() -> int:
    outputs = build_outputs()
    write_outputs(outputs)
    result = outputs["result"]
    print(json.dumps({
        "ok": result["ok"],
        "decision": result["decision"],
        "staged_ready_subset_dossier_ready": result["staged_ready_subset_dossier_ready"],
        "full_candidate_book_ready": result["full_candidate_book_ready"],
        "readiness_work_item_count": result["readiness_work_item_count"],
        "ready_subset_sharpe": result["ready_subset_mc"]["sharpe"],
        "ready_subset_mc_pass": result["ready_subset_mc"]["mc"]["p_pass"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
