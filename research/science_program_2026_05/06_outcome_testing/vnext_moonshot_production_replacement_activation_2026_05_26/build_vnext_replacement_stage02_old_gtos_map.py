"""Build Stage 02 old-GTOS replacement map for the vNext activation route."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
DATE = "2026-05-26"

MAP_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OLD_GTOS_REPLACEMENT_MAP_{DATE}.json"
LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_SURFACE_RETIREMENT_LEDGER_{DATE}.jsonl"
SESSION_STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"
STAGE01_LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_UPSTREAM_EVIDENCE_RECONCILIATION_LEDGER_{DATE}.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def sha256_path(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def write_json_object(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8", newline="\n")


def read_stage01_inventory_stats() -> dict[str, Any]:
    counts: Counter[str] = Counter()
    roles: Counter[str] = Counter()
    row_kinds: Counter[str] = Counter()
    rows = 0
    row_bearing_lines = 0
    if not STAGE01_LEDGER_PATH.exists():
        return {
            "exists": False,
            "rows": 0,
            "sha256": None,
        }
    with STAGE01_LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            row = json.loads(raw)
            rows += 1
            counts.update(row.get("classifications", []))
            roles.update([str(row.get("artifact_role", "unknown"))])
            row_kinds.update([str(row.get("row_kind", "unknown"))])
            row_bearing_lines += int(row.get("row_bearing_rows_scanned") or 0)
    return {
        "exists": True,
        "rows": rows,
        "sha256": sha256_path(STAGE01_LEDGER_PATH),
        "row_kind_counts": dict(row_kinds),
        "classification_counts": dict(counts),
        "artifact_role_counts": dict(roles),
        "row_bearing_lines_scanned": row_bearing_lines,
    }


def legacy_surfaces() -> list[dict[str, Any]]:
    common_negative_gate = (
        "Must not reproduce failed 10-trade production route collapse, FVG-only narrowing, broad AVOID/prop blockers, "
        "or old-GTOS/J46 dominance under activation overlay."
    )
    return [
        {
            "surface_id": "legacy_candidate_origin_generation",
            "old_gtos_surface": "Candidate origins are dominated by current Model A framework generation.",
            "old_behavior_evidence": [
                "config/agent_config.yaml:410 model_a.enabled_frameworks=['ob_retest','fvg_fill','breaker_re_entry']",
                "full replay Stage02 framework rows: fvg_fill=106679, ob_retest=77053, breaker_re_entry=69502",
            ],
            "retirement_action": "narrow_to_rollback_and_expand_origin_contract",
            "replacement_behavior_target": (
                "Use the vNext production candidate contract to enumerate framework candidates plus moonshot origin families; "
                "current three frameworks remain baseline/rollback families, not the production horizon."
            ),
            "replacement_source_artifacts": [
                "VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_2026-05-26.jsonl",
                "VNEXT_MOONSHOT_CANDIDATE_ORIGIN_BOXING_AUDIT_LEDGER_2026-05-26.jsonl",
                "VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json",
            ],
            "activation_rule": "Origin families require source availability or explicit activation exclusion before selected/performance replay.",
            "rollback_rule": "Disable vNext replacement overlay to fall back to Model A framework generation only.",
            "stage04_runtime_work_required": "Add universal candidate event/origin registry surfaces before activation.",
            "stage05_replay_gate": "Full candidate universe 253234 and denominator 903163 must be preserved; no FVG subset proof.",
            "stage12_semantic_gate": common_negative_gate,
            "classification": "override_or_expand",
        },
        {
            "surface_id": "legacy_three_framework_routing",
            "old_gtos_surface": "Production routing still evaluates old framework labels as the main decision family.",
            "old_behavior_evidence": [
                "config/agent_config.yaml:410 old frameworks configured",
                "src/components/orchestrator.py:1308 and related pre-AI framework override helpers still route frameworks",
            ],
            "retirement_action": "retain_as_candidate_family_not_primary_router",
            "replacement_behavior_target": "Route through vNext FOLLOW/AVOID/MIXED/LEGACY plus dynamic execution and source-complete exclusions.",
            "replacement_source_artifacts": [
                "VNEXT_REPLACEMENT_UPSTREAM_EVIDENCE_RECONCILIATION_LEDGER_2026-05-26.jsonl",
                "VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_2026-05-26.json",
            ],
            "activation_rule": "Old framework labels may not dominate activated routing unless a row-level rollback/fallback rule says so.",
            "rollback_rule": "Base config with apply_to_execution=false restores old framework route dominance.",
            "stage04_runtime_work_required": "Wire moonshot/default-off router into runtime/orchestrator rather than research-only tests.",
            "stage05_replay_gate": "Replay must emit old GTOS/current shadow and activated vNext decision columns per candidate.",
            "stage12_semantic_gate": "Fail if activated overlay changes only would_* fields while old framework behavior remains primary.",
            "classification": "narrow_or_override",
        },
        {
            "surface_id": "d1_h4_h1_prescreen_and_static_poi",
            "old_gtos_surface": "D1/H4/H1 prescreen, H1 POI availability, and static POI assumptions can suppress AI and execution before vNext selection.",
            "old_behavior_evidence": [
                "src/components/orchestrator.py:2708-2764 applies H1 POI availability pre-AI skip path",
                "src/components/pre_ai_gates.py is imported at src/components/orchestrator.py:46",
            ],
            "retirement_action": "retain_as_safety_and_source_contract_not_alpha_selector",
            "replacement_behavior_target": (
                "Candidate contract must state which static POI/prescreen rules remain hard safety, which are rollback-only, "
                "and which are replaced by source-bound vNext/LTF/path decisions."
            ),
            "replacement_source_artifacts": [
                "VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json",
                "VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_2026-05-26.json",
            ],
            "activation_rule": "Source-missing/static-only rows require exclusion or forward capture before activation.",
            "rollback_rule": "Old prescreen remains available when vNext activation overlay is disabled.",
            "stage04_runtime_work_required": "Expose prescreen decisions in replacement runtime effect ledger and source-capture requirements.",
            "stage05_replay_gate": "Replay must partition source-complete, proxy-context, and source-missing prescreen effects.",
            "stage12_semantic_gate": "Fail if source-missing rows are activated without capture/exclusion proof.",
            "classification": "narrow_and_source_bind",
        },
        {
            "surface_id": "ai_primary_gate",
            "old_gtos_surface": "Primary analyzer remains a production AI decision gate unless pre-AI/mechanical paths bypass or narrow it.",
            "old_behavior_evidence": [
                "src/components/orchestrator.py:956 evaluates vNext AI policy but config keeps apply flags off",
                "config/agent_config.yaml has gtos_vnext_runtime.ai_policy_enabled=true but ai_policy_apply_to_ai_call=false per AI/ML lane audit",
            ],
            "retirement_action": "constrain_to_budgeted_validator_or_resolver",
            "replacement_behavior_target": "Mechanical vNext/moonshot activation must not depend on unpaid researcher labels; AI use requires route budget cap and calibration package.",
            "replacement_source_artifacts": [
                "VNEXT_ACTIVATION_AI_VALIDATION_BUDGET_PLAN_2026-05-26.json",
                "VNEXT_MOONSHOT_AI_ROLE_DECISION_LEDGER_2026-05-26.jsonl",
            ],
            "activation_rule": "No paid AI/vendor calls without route-state budget cap; no no-paid-AI diagnostic as production selector.",
            "rollback_rule": "Existing analyzer path remains old GTOS fallback where vNext AI policy is not budget-approved.",
            "stage04_runtime_work_required": "Add replacement-specific AI calibration config block, default off/shadow.",
            "stage05_replay_gate": "Replay separates mechanical activation and AI diagnostic/calibrated scenarios.",
            "stage12_semantic_gate": "Fail if AI diagnostic zero/broad suppression is treated as production selection.",
            "classification": "narrow_to_calibrated_validator",
        },
        {
            "surface_id": "vnext_pre_ai_shadow_gate",
            "old_gtos_surface": "vNext pre-AI route is wired but currently mostly shadow/config-gated.",
            "old_behavior_evidence": [
                "src/components/orchestrator.py:2579-2708 evaluates and can apply pre-AI route",
                "src/components/gtos_vnext_runtime.py:10614-11008 defines SKIP_AI, MECHANICAL_FOLLOW, MIXED, and LEGACY AI actions",
            ],
            "retirement_action": "activate_source_bound_mechanical_skip_or_narrow",
            "replacement_behavior_target": "FOLLOW/AVOID/MIXED/LEGACY semantics must become concrete runtime actions or exclusions, not inert labels.",
            "replacement_source_artifacts": [
                "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_AVOID_PRE_AI_REPAIR_SUMMARY_2026-05-25.json",
                "VNEXT_FULL_REPLAY_STAGE06_FINAL_SUMMARY_2026-05-24.json",
            ],
            "activation_rule": "Broad AVOID cannot block positive avoided-set R; MIXED/LEGACY need explicit resolve/fallback/exclude actions.",
            "rollback_rule": "apply_to_execution=false restores shadow-only pre-AI behavior.",
            "stage04_runtime_work_required": "Implement replacement candidate contract actions and test overlay-on behavioral diff.",
            "stage05_replay_gate": "Replay reports blocked winners, avoided losers, saved losers, and old-live leakage.",
            "stage12_semantic_gate": "Fail if MIXED/LEGACY remain non-executing labels while counted as production decisions.",
            "classification": "override_when_source_bound",
        },
        {
            "surface_id": "l2_and_permissions_safety_gates",
            "old_gtos_surface": "L2 checks and permissions gates reject unsafe trades after AI selection.",
            "old_behavior_evidence": [
                "src/components/permissions.py line inventory in LIVE_STATE lists deployment, concurrent, correlation, dormant, touch-count, and SL gates",
                "src/components/orchestrator.py:3263 calls vnext_execution_block_reason before later execution flow",
            ],
            "retirement_action": "retain_as_hard_safety_not_alpha",
            "replacement_behavior_target": "vNext can change selection/execution, but safety gates remain mandatory rollback-compatible hard rails.",
            "replacement_source_artifacts": [
                "config/agent_config.yaml",
                "src/components/permissions.py",
            ],
            "activation_rule": "No activation overlay may weaken emergency/safety gates without explicit owner approval.",
            "rollback_rule": "Safety gates remain active under both old GTOS and vNext overlay.",
            "stage04_runtime_work_required": "Add monitoring fields proving vNext blocks/permits are separate from safety rejections.",
            "stage05_replay_gate": "Replay distinguishes vNext selection deltas from safety-gate non-executable rows.",
            "stage12_semantic_gate": "Fail if prop/vNext blocks are conflated with mandatory safety gates.",
            "classification": "retain_as_safety",
        },
        {
            "surface_id": "j46_j49_exit_policy",
            "old_gtos_surface": "J46/J49 target, BE, TP2, and time-stop behavior dominates active exit management.",
            "old_behavior_evidence": [
                "src/components/execution.py:529-542 overrides broker TP to 6R and stores 3R software TP1 when J46/J49 is enabled",
                "src/components/execution.py:1725-1737 applies J46/J49 BE-only TP1 handling",
                "src/components/execution.py:1865-1909 applies J46/J49 TP2 higher-target close",
            ],
            "retirement_action": "replace_as_primary_exit_with_dynamic_execution_policy",
            "replacement_behavior_target": "Moonshot dynamic execution policy becomes primary under activation; J46/J49 remains comparator/rollback only.",
            "replacement_source_artifacts": [
                "VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_2026-05-26.json",
                "VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_2026-05-26.json",
                "src/research/moonshot_default_off_policy_router.py",
            ],
            "activation_rule": "Activated rows must persist selected dynamic policy and bypass J46/J49 target override except explicit rollback/comparator rows.",
            "rollback_rule": "Rollback overlay re-enables current J46/J49 behavior.",
            "stage04_runtime_work_required": "Add dynamic execution policy state to TradeState/PendingLimitIntent and execution branch.",
            "stage05_replay_gate": "Replay cannot use fixed 1.5R/J46/J49 as final moonshot truth.",
            "stage12_semantic_gate": "Fail if J46/J49 remains dominant under activated overlay.",
            "classification": "retire_primary_retain_rollback",
        },
        {
            "surface_id": "fixed_1_5r_and_static_target_truth",
            "old_gtos_surface": "Risk min RR and older replay labels can treat fixed 1.5R/static targets as final truth.",
            "old_behavior_evidence": [
                "config/agent_config.yaml:35 risk.min_rr=1.5",
                "controlling prompt explicitly forbids fixed 1.5R/J46-J49 as final moonshot execution truth",
            ],
            "retirement_action": "retain_as_minimum_filter_or_comparator_only",
            "replacement_behavior_target": "Dynamic execution, LTF path, and prop-governed branch policy determine activated execution truth.",
            "replacement_source_artifacts": [
                "VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_2026-05-26.json",
                "VNEXT_REPLACEMENT_UPSTREAM_EVIDENCE_RECONCILIATION_LEDGER_2026-05-26.jsonl",
            ],
            "activation_rule": "Fixed-R fields must be labeled comparator/minimum-rule, not final policy, in activated replay and runtime.",
            "rollback_rule": "Old min-R filter remains safety/comparator when overlay off.",
            "stage04_runtime_work_required": "Runtime effect ledger must record dynamic policy vs fixed-R comparator source.",
            "stage05_replay_gate": "Replay columns must separate exact/proxy/dynamic R from fixed comparator R.",
            "stage12_semantic_gate": "Fail if primitive fixed-target labels are accepted as moonshot truth.",
            "classification": "narrow_to_comparator",
        },
        {
            "surface_id": "pending_limit_no_fill_lifecycle",
            "old_gtos_surface": "Pending limit placement/fill/no-fill behavior is old execution flow with vNext policy attached but gated.",
            "old_behavior_evidence": [
                "src/components/orchestrator.py:3631-3647 evaluates and can skip pending no-fill avoid when applied",
                "src/components/execution.py:119 defines PendingLimitIntent and src/components/execution.py:689 builds intents",
            ],
            "retirement_action": "override_with_vnext_pending_ltf_policy_when_applied",
            "replacement_behavior_target": "No-fill/LTF evidence can skip, adjust, convert to market, monitor, or retain pending behavior under activation.",
            "replacement_source_artifacts": [
                "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_SUMMARY_2026-05-25.json",
                "VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json",
            ],
            "activation_rule": "Pending policy may affect execution only when global and surface-specific apply flags are true.",
            "rollback_rule": "Base pending placement restored by overlay off.",
            "stage04_runtime_work_required": "Persist vNext pending/LTF policy fields across pending restore/fill.",
            "stage05_replay_gate": "Replay reports timeout/no-fill behavior and LTF adjusted/market-entry effects.",
            "stage12_semantic_gate": "Fail if selected coverage shrinks silently through pending/no-fill gates.",
            "classification": "override_when_applied",
        },
        {
            "surface_id": "ltf_path_execution_surface",
            "old_gtos_surface": "LTF path execution is wired but not currently allowed to affect execution.",
            "old_behavior_evidence": [
                "config/agent_config.yaml:2268 ltf_path_execution_apply_to_execution=false",
                "src/components/orchestrator.py:3672-3728 evaluates LTF path and can skip/adjust/market-enter only when applied",
                "src/components/orchestrator.py:4784-4786 pending LTF monitor requires apply flag",
            ],
            "retirement_action": "activate_as_execution_modifier_after_gates",
            "replacement_behavior_target": "LTF path actions become concrete execution modifiers under overlay and rollback-safe state.",
            "replacement_source_artifacts": [
                "VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json",
                "VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json",
            ],
            "activation_rule": "Requires ltf_path_execution_apply_to_execution=true plus source-complete path state.",
            "rollback_rule": "Set LTF apply flag false to return to old pending/limit behavior.",
            "stage04_runtime_work_required": "Add overlay config and behavioral diff tests for skip/adjust/market entry.",
            "stage05_replay_gate": "Replay must compare current shadow and activated LTF path effects.",
            "stage12_semantic_gate": "Fail if overlay does not alter LTF action where contract says it should.",
            "classification": "activate_surface",
        },
        {
            "surface_id": "prop_safe_selector_and_risk",
            "old_gtos_surface": "Prop/risk/drawdown rules exist, while vNext prop-safe selector is wired but apply-off.",
            "old_behavior_evidence": [
                "config/agent_config.yaml:2280 prop_safe_selector_apply_to_execution=false",
                "src/components/orchestrator.py:3746-3817 evaluates selector and can reduce/defer/block when applied",
                "risk/drawdown values are summarized in LIVE_STATE active config",
            ],
            "retirement_action": "retain_hard_risk_safety_and_apply_ev_prop_governor",
            "replacement_behavior_target": "Prop governor can resize, defer, abandon/restart, or allow based on executable-stream EV rather than broad blockers.",
            "replacement_source_artifacts": [
                "VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json",
                "VNEXT_ACTIVATION_PROP_EV_ANATOMY_SUMMARY_2026-05-26.json",
            ],
            "activation_rule": "Broad prop blocker must prove source-bound negative EV/opportunity-cost dominance at branch/account-attempt level.",
            "rollback_rule": "Disable prop selector apply flag and retain existing risk/drawdown safety.",
            "stage04_runtime_work_required": "Ensure prop selector modifies risk/defer/block with monitoring and rollback fields.",
            "stage05_replay_gate": "Replay must use executable stream, not non-executable legacy/mixed rows, for prop attempt metrics.",
            "stage12_semantic_gate": "Fail if positive baseline is broadly blocked or selected count collapses without row-level proof.",
            "classification": "activate_ev_governor",
        },
        {
            "surface_id": "mixed_legacy_label_semantics",
            "old_gtos_surface": "MIXED and LEGACY labels are mostly inert under current config.",
            "old_behavior_evidence": [
                "config/agent_config.yaml:2324 mixed_blocks_execution=false",
                "config/agent_config.yaml:2325 legacy_blocks_execution=false",
                "src/components/gtos_vnext_runtime.py:15216 returns no block when decision.apply_to_execution is false",
            ],
            "retirement_action": "replace_inert_labels_with_contract_actions",
            "replacement_behavior_target": "Every MIXED/LEGACY row must resolve, fallback, exclude, request source capture, use AI resolver, or rollback explicitly.",
            "replacement_source_artifacts": [
                "VNEXT_FULL_REPLAY_STAGE06_FINAL_SUMMARY_2026-05-24.json",
                "VNEXT_ACTIVATION_QUESTION_STACK_LEDGER_2026-05-26.jsonl",
            ],
            "activation_rule": "No non-executing MIXED/LEGACY labels may be counted as terminal activated selectors.",
            "rollback_rule": "Explicit rollback rows can use old GTOS behavior with reason and test coverage.",
            "stage04_runtime_work_required": "Implement contract-action mapping and tests for MIXED/LEGACY boundaries.",
            "stage05_replay_gate": "Replay must report MIXED/LEGACY action distribution and execution effect.",
            "stage12_semantic_gate": "Fail if MIXED/LEGACY remain inert labels.",
            "classification": "override_semantics",
        },
        {
            "surface_id": "moonshot_dynamic_router_research_only",
            "old_gtos_surface": "Moonshot dynamic execution router exists in research namespace, not production runtime path.",
            "old_behavior_evidence": [
                "rg found route_moonshot_dynamic_execution only in src/research/moonshot_default_off_policy_router.py and tests, not src/components",
                "config/agent_config.yaml:554-555 moonshot router enabled/apply flags are false",
            ],
            "retirement_action": "wire_into_runtime_as_config_gated_replacement",
            "replacement_behavior_target": "Production runtime consumes moonshot router output with selected policy, refusal reason, source completeness, and rollback comparator.",
            "replacement_source_artifacts": [
                "src/research/moonshot_default_off_policy_router.py",
                "tests/test_moonshot_default_off_policy_router.py",
                "VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_2026-05-26.json",
            ],
            "activation_rule": "Router must be called from runtime/orchestrator and affect behavior under overlay; research-only tests are insufficient.",
            "rollback_rule": "Router flags off restores existing route.",
            "stage04_runtime_work_required": "Import/adapt router into gtos_vnext_runtime/orchestrator and persist selected policy.",
            "stage05_replay_gate": "Replay must compare moonshot BE/dynamic/condition router branches.",
            "stage12_semantic_gate": "Fail if moonshot router remains default-off artifact without runtime behavioral diff.",
            "classification": "wire_missing_surface",
        },
        {
            "surface_id": "source_missing_and_forward_capture",
            "old_gtos_surface": "Old runtime lacks complete source-capture fields for historical broker lifecycle and some candidate origins.",
            "old_behavior_evidence": [
                "VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_2026-05-26.jsonl rows counted in Stage01 inventory",
                "moonshot source capability ledger split includes dynamic usable true/false counts per evidence lane",
            ],
            "retirement_action": "exclude_or_capture_before_activation",
            "replacement_behavior_target": "Source-missing rows are excluded from activated metrics or bound to prospective capture requirements.",
            "replacement_source_artifacts": [
                "VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_2026-05-26.jsonl",
                "VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_2026-05-26.json",
                "shadow_logs/*.jsonl",
            ],
            "activation_rule": "Never activate source-missing rows without capture/exclusion proof.",
            "rollback_rule": "Old source behavior remains comparator only and cannot be used as activation proof.",
            "stage04_runtime_work_required": "Add prospective source-capture schemas/loggers/tests for route-owned surfaces.",
            "stage05_replay_gate": "Replay partitions source-complete, proxy-context, and source-missing rows.",
            "stage12_semantic_gate": "Fail if source-missing rows enter selected/performance metrics.",
            "classification": "source_capture_required",
        },
        {
            "surface_id": "monitoring_canary_and_leakage",
            "old_gtos_surface": "Existing monitoring/canary lacks replacement-specific apply-status, router, label-effect, dynamic-exit, prop, and leakage fields.",
            "old_behavior_evidence": [
                "LIVE_STATE watchdog hooks list existing monitors, not replacement overlay verifier fields",
                "AI/ML lane identified missing Stage10 monitoring integration map and schemas",
            ],
            "retirement_action": "extend_monitoring_not_replace_safety",
            "replacement_behavior_target": "Stage10 adds log schemas and monitors for vNext apply status, router decisions, label effects, exits, source capture, malformed AI, and old-live fallback leakage.",
            "replacement_source_artifacts": [
                "shadow_logs/*.jsonl",
                "src/components/ai_decision_trace_logger.py",
                "src/research_infra/k55_ml_shadow.py",
            ],
            "activation_rule": "Activation dossier must name monitoring fields and rollback thresholds.",
            "rollback_rule": "Existing watchdog remains; replacement monitoring can be disabled with overlay rollback.",
            "stage04_runtime_work_required": "Emit runtime effect ledger fields for every changed behavior.",
            "stage05_replay_gate": "Replay/semantic verifier checks old-live fallback leakage.",
            "stage12_semantic_gate": "Fail if overlay passes while old GTOS effectively remains in control.",
            "classification": "extend_monitoring",
        },
        {
            "surface_id": "activation_overlay_default_off_state",
            "old_gtos_surface": "Current config keeps vNext execution effects and moonshot router default-off.",
            "old_behavior_evidence": [
                "config/agent_config.yaml:550 gtos_vnext_runtime.apply_to_execution=false",
                "config/agent_config.yaml:554-555 moonshot dynamic router flags false",
                "config/agent_config.yaml:2268 and 2280 LTF/prop apply flags false",
            ],
            "retirement_action": "apply_overlay_only_after_semantic_gates",
            "replacement_behavior_target": "Stage11/13 must apply production activation config overlay after replay/runtime/semantic/rollback gates pass.",
            "replacement_source_artifacts": [
                "VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_2026-05-26.yaml",
                "VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_2026-05-26.json",
            ],
            "activation_rule": "Overlay is applied only after verifier proves behavior changes and rollback restores old behavior.",
            "rollback_rule": "Rollback overlay sets apply flags and router flags back to current defaults.",
            "stage04_runtime_work_required": "Add exact activation flags where missing and focused overlay behavioral diff tests.",
            "stage05_replay_gate": "Replay runs under activated-config semantics, not only would_* shadow.",
            "stage12_semantic_gate": "Fail if config-gated state is used as terminal excuse.",
            "classification": "activation_overlay_required",
        },
        {
            "surface_id": "failed_10_trade_route_negative_fixture",
            "old_gtos_surface": "Prior production-change route collapsed to 10 trades and do-not-activate status.",
            "old_behavior_evidence": [
                "VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md",
                "controlling prompt anchors failed selected=10, total R about -4.999959, baseline selected=35983, missed winners=104440",
            ],
            "retirement_action": "retain_as_mandatory_negative_fixture",
            "replacement_behavior_target": "New replacement route must reject any broad blocker/selector that reproduces the failed route.",
            "replacement_source_artifacts": [
                "vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25 route artifacts",
            ],
            "activation_rule": "Semantic verifier must fail 10-trade collapse or unexplained selected coverage shrink.",
            "rollback_rule": "Do not activate if this fixture fails; old GTOS remains rollback comparator.",
            "stage04_runtime_work_required": "Add failure fixture to runtime/replay verifier scope.",
            "stage05_replay_gate": "Activated replay selected coverage cannot silently shrink below stated gate without proof.",
            "stage12_semantic_gate": "Fail if selected count near 10, expectancy/PF negative, or blocked winners dominate.",
            "classification": "negative_fixture",
        },
    ]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def upsert_output(outputs: list[dict[str, Any]], path_name: str, updates: dict[str, Any]) -> None:
    for output in outputs:
        if output.get("path") == path_name:
            output.update(updates)
            return
    outputs.append({"path": path_name, **updates})


def update_output_manifest(rows: list[dict[str, Any]]) -> None:
    manifest = load_json_object(OUTPUT_MANIFEST_PATH)
    outputs = manifest.setdefault("outputs", [])
    upsert_output(
        outputs,
        MAP_PATH.name,
        {"stage": "stage_02", "status": "created", "surfaces": len(rows)},
    )
    upsert_output(
        outputs,
        LEDGER_PATH.name,
        {"stage": "stage_02", "status": "created", "rows": len(rows)},
    )
    upsert_output(
        outputs,
        Path(__file__).name,
        {"stage": "stage_02", "status": "created_and_ready_for_py_compile"},
    )
    manifest["next_manifest_update"] = "After Stage 03 production candidate contract is written."
    write_json_object(OUTPUT_MANIFEST_PATH, manifest)


def update_session_state(rows: list[dict[str, Any]]) -> None:
    state = load_json_object(SESSION_STATE_PATH)
    state["last_updated_utc"] = utc_now()
    state["current_stage"] = "stage_03_production_candidate_contract"
    state.setdefault("stage_status", {})["stage_02_old_gtos_replacement_map"] = "completed_replacement_map_written"
    state["first_incomplete_invariant"] = "stage_03_production_candidate_contract_pending"
    state["exact_next_action"] = (
        "Build VNEXT_REPLACEMENT_PRODUCTION_CANDIDATE_CONTRACT_2026-05-26.md and .json, freezing candidate origins, "
        "FOLLOW/AVOID/MIXED/LEGACY semantics, dynamic execution, prop EV governor, AI/ML roles, source-capture rules, "
        "activation flags, fallback, and rollback semantics from the Stage 02 map."
    )
    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage02_legacy_surface_rows"] = len(rows)
    evidence["stage02_surface_classification_counts"] = dict(Counter(row["classification"] for row in rows))
    tests = state.setdefault("tests_verifiers_run", [])
    tests.append(
        {
            "command": (
                "python research\\science_program_2026_05\\06_outcome_testing\\"
                "vnext_moonshot_production_replacement_activation_2026_05_26\\"
                "build_vnext_replacement_stage02_old_gtos_map.py"
            ),
            "result": f"passed; wrote Stage 02 replacement map and {len(rows)} legacy-surface ledger rows",
            "timestamp_utc": utc_now(),
        }
    )
    state.setdefault("completion_gate_status", {})["route_complete"] = False
    state.setdefault("completion_gate_status", {})["reason"] = (
        "Stage 02 map is complete, but production candidate contract, runtime implementation, full activated replay, "
        "semantic verifier, applied overlay, rollback proof, monitoring package, scoped commits, and completion audit remain incomplete."
    )
    write_json_object(SESSION_STATE_PATH, state)


def append_control_event(rows: list[dict[str, Any]]) -> None:
    event = {
        "timestamp_utc": utc_now(),
        "route_id": ROUTE_ID,
        "event": "stage_02_old_gtos_replacement_map_written",
        "map": rel(MAP_PATH),
        "ledger": rel(LEDGER_PATH),
        "legacy_surface_rows": len(rows),
        "next_incomplete_invariant": "stage_03_production_candidate_contract_pending",
    }
    with CONTROL_LEDGER_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    surfaces = legacy_surfaces()
    stage01_stats = read_stage01_inventory_stats()
    surface_counts = Counter(surface["classification"] for surface in surfaces)
    replacement_map = {
        "route_id": ROUTE_ID,
        "stage": "stage_02_old_gtos_replacement_map",
        "generated_utc": utc_now(),
        "stage01_inventory": stage01_stats,
        "surface_count": len(surfaces),
        "surface_classification_counts": dict(surface_counts),
        "failure_gate": (
            "Old GTOS cannot still dominate when vNext activation flags are enabled unless a row-level rollback/fallback rule "
            "explicitly says so and a test proves the boundary."
        ),
        "next_incomplete_invariant": "stage_03_production_candidate_contract_pending",
        "surfaces": surfaces,
    }
    write_json_object(MAP_PATH, replacement_map)
    write_jsonl(LEDGER_PATH, surfaces)
    update_output_manifest(surfaces)
    update_session_state(surfaces)
    append_control_event(surfaces)
    print(json.dumps({"map": rel(MAP_PATH), "ledger": rel(LEDGER_PATH), "rows": len(surfaces)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
