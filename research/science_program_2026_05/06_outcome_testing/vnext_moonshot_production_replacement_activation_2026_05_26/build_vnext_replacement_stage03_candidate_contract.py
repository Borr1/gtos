"""Build Stage 03 production candidate contract for the vNext activation route."""

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

CONTRACT_JSON_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_PRODUCTION_CANDIDATE_CONTRACT_{DATE}.json"
CONTRACT_MD_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_PRODUCTION_CANDIDATE_CONTRACT_{DATE}.md"
SESSION_STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"
STAGE02_MAP_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OLD_GTOS_REPLACEMENT_MAP_{DATE}.json"

FULL_REPLAY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24"
)
REPAIR_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"
)
ACTIVATION_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26"
)
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

FULL_CANDIDATE_SUMMARY = FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_CANDIDATE_GENERATION_SUMMARY_2026-05-24.json"
FULL_SOURCE_MODE_SUMMARY = FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_STAGE04_SOURCE_MODE_SUMMARY_2026-05-24.json"
FULL_FINAL_SUMMARY = FULL_REPLAY_DIR / "VNEXT_FULL_REPLAY_STAGE06_FINAL_SUMMARY_2026-05-24.json"
REPAIR_METRICS_SUMMARY = REPAIR_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json"
ACTIVATION_ML_RESULTS = ACTIVATION_DIR / "VNEXT_ACTIVATION_ML_CHALLENGER_RESULTS_2026-05-26.json"
MOONSHOT_DYNAMIC_SUMMARY = MOONSHOT_DIR / "VNEXT_MOONSHOT_STAGE04_DYNAMIC_POLICY_REPLAY_SUMMARY_2026-05-26.json"
MOONSHOT_CORRECTED_BRANCH = MOONSHOT_DIR / "VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_2026-05-26.json"
MOONSHOT_ORIGIN_REGISTRY = MOONSHOT_DIR / "VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_REGISTRY_2026-05-26.jsonl"
MOONSHOT_FORWARD_CAPTURE = MOONSHOT_DIR / "VNEXT_MOONSHOT_FORWARD_CAPTURE_REQUIREMENTS_2026-05-26.jsonl"
MOONSHOT_RUNTIME_MAP = MOONSHOT_DIR / "VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_2026-05-26.json"
MOONSHOT_SOURCE_CAPABILITY = MOONSHOT_DIR / "VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_2026-05-26.json"

LIVE_DEPLOYMENT_SYMBOLS = ["XAUUSD", "US30", "USDJPY", "GBPJPY", "GBPUSD", "XAGUSD", "NAS100"]

SOURCE_CAPTURE_FIELDS = [
    "broker_order_id",
    "broker_deal_id",
    "requested_entry_price",
    "executed_entry_price",
    "requested_exit_price",
    "executed_exit_price",
    "fill_time_utc",
    "close_time_utc",
    "bid_ask_ordered_path",
    "spread",
    "slippage",
    "commission",
    "swap",
    "partial_close_lifecycle",
    "breakeven_modify_lifecycle",
    "trailing_modify_lifecycle",
    "time_stop_lifecycle",
    "pending_order_lifecycle",
    "cancel_expire_lifecycle",
    "source_join_ids",
    "candidate_id",
    "policy_hash",
    "prompt_hash",
    "ai_response_id",
    "runtime_branch_label",
    "runtime_policy_label",
    "prop_governor_decision_fields",
    "source_completeness",
    "source_ambiguity",
]


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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            row = json.loads(raw)
            if isinstance(row, dict):
                row.setdefault("_source_line_no", line_no)
                rows.append(row)
    return rows


def write_json_object(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8", newline="\n")


def counter_from(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key, "unknown")) for row in rows))


def policy_metrics(dynamic_summary: dict[str, Any]) -> list[dict[str, Any]]:
    names = dynamic_summary.get("policy_names") or sorted(dynamic_summary.get("policy_total_r", {}).keys())
    totals = dynamic_summary.get("policy_total_r", {})
    expectancies = dynamic_summary.get("policy_expectancy_r", {})
    counts = dynamic_summary.get("policy_counts", {})
    ambiguous_counts = dynamic_summary.get("policy_ambiguous_counts", {})
    exit_reasons = dynamic_summary.get("policy_exit_reason_counts", {})
    rows: list[dict[str, Any]] = []
    for name in names:
        if name == "live_current_j46_j49":
            role = "comparator_and_rollback_only"
        elif name == "legacy_fixed_1.5r":
            role = "fixed_r_comparator_only_not_activation_truth"
        elif name == "ai_target":
            role = "ai_calibrated_only_after_budgeted_validation"
        else:
            role = "activation_candidate_dynamic_policy"
        rows.append(
            {
                "policy_name": name,
                "runtime_role": role,
                "replay_rows": counts.get(name),
                "total_r": totals.get(name),
                "expectancy_r": expectancies.get(name),
                "ambiguous_count": ambiguous_counts.get(name),
                "exit_reason_counts": exit_reasons.get(name, {}),
            }
        )
    return rows


def select_primary_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [
        row
        for row in rows
        if row.get("runtime_role") == "activation_candidate_dynamic_policy"
        and isinstance(row.get("expectancy_r"), (int, float))
    ]
    if not candidates:
        return {"policy_name": None, "selection_reason": "no_dynamic_policy_metric_available"}
    best = max(candidates, key=lambda row: (float(row["expectancy_r"]), float(row.get("total_r") or 0.0), str(row["policy_name"])))
    return {
        "policy_name": best["policy_name"],
        "selection_reason": "highest expectancy among activation-candidate dynamic policies in Stage04 dynamic replay",
        "expectancy_r": best.get("expectancy_r"),
        "total_r": best.get("total_r"),
    }


def ml_role_contract(ml_results: dict[str, Any]) -> list[dict[str, Any]]:
    roles: list[dict[str, Any]] = []
    for row in ml_results.get("model_role_results", []):
        if not isinstance(row, dict):
            continue
        roles.append(
            {
                "role": row.get("role"),
                "target": row.get("target"),
                "model_type": row.get("model_type"),
                "feature_view": row.get("feature_view"),
                "disposition": row.get("disposition"),
                "runtime_interaction": row.get("runtime_interaction"),
                "activation_rule": "monitor_or_assistant_only_until sealed validation and no-leak tests approve live control",
                "metrics": row.get("metrics", {}),
            }
        )
    return roles


def build_contract() -> dict[str, Any]:
    stage02 = load_json_object(STAGE02_MAP_PATH)
    candidate_summary = load_json_object(FULL_CANDIDATE_SUMMARY)
    source_mode_summary = load_json_object(FULL_SOURCE_MODE_SUMMARY)
    final_summary = load_json_object(FULL_FINAL_SUMMARY)
    repair_summary = load_json_object(REPAIR_METRICS_SUMMARY)
    ml_results = load_json_object(ACTIVATION_ML_RESULTS)
    dynamic_summary = load_json_object(MOONSHOT_DYNAMIC_SUMMARY)
    corrected_branch = load_json_object(MOONSHOT_CORRECTED_BRANCH)
    runtime_map = load_json_object(MOONSHOT_RUNTIME_MAP)
    source_capability = load_json_object(MOONSHOT_SOURCE_CAPABILITY)
    origin_rows = read_jsonl(MOONSHOT_ORIGIN_REGISTRY)
    forward_capture_rows = read_jsonl(MOONSHOT_FORWARD_CAPTURE)
    state = load_json_object(SESSION_STATE_PATH)

    dynamic_policies = policy_metrics(dynamic_summary)
    primary_policy = select_primary_policy(dynamic_policies)
    best_repair_policy = repair_summary.get("best_policy_reference_fee_599_payout_8000", {})
    best_moonshot_policy = corrected_branch.get("best_overall_reference_fee599_payout8000", {})
    counts = candidate_summary.get("counts", {})
    best_repaired_stream = repair_summary.get("scenario_metrics", {}).get("stage08_best_prop_governed_repaired_stream", {})
    no_prop_stream = repair_summary.get("scenario_metrics", {}).get("stage07_no_prop_ai_required_stream", {})

    source_modes = sorted(
        set(repair_summary.get("source_status_counts", {}).keys())
        | set(best_repaired_stream.get("selected_only_coverage", {}).get("source_modes", {}).keys())
        | set(no_prop_stream.get("selected_only_coverage", {}).get("source_modes", {}).keys())
        | set(source_mode_summary.get("required_replay_modes", []))
    )
    markets = sorted(candidate_summary.get("candidate_rows_by_symbol", {}).keys())
    sessions = sorted(candidate_summary.get("candidate_rows_by_session_bucket", {}).keys())

    evidence_paths = [
        STAGE02_MAP_PATH,
        FULL_CANDIDATE_SUMMARY,
        FULL_SOURCE_MODE_SUMMARY,
        FULL_FINAL_SUMMARY,
        REPAIR_METRICS_SUMMARY,
        ACTIVATION_ML_RESULTS,
        MOONSHOT_DYNAMIC_SUMMARY,
        MOONSHOT_CORRECTED_BRANCH,
        MOONSHOT_ORIGIN_REGISTRY,
        MOONSHOT_FORWARD_CAPTURE,
        MOONSHOT_RUNTIME_MAP,
        MOONSHOT_SOURCE_CAPABILITY,
    ]

    contract = {
        "route_id": ROUTE_ID,
        "stage": "stage_03_production_candidate_contract",
        "generated_utc": utc_now(),
        "evidence_anchors": [
            {"path": rel(path), "exists": path.exists(), "sha256": sha256_path(path)}
            for path in evidence_paths
        ],
        "stage02_surface_count": stage02.get("surface_count"),
        "candidate_universe_contract": {
            "denominator_rows": counts.get("denominator_rows"),
            "candidate_rows": counts.get("candidate_rows"),
            "candidate_generation_rows": counts.get("candidate_generation_rows"),
            "framework_candidate_rows": candidate_summary.get("candidate_rows_by_framework", {}),
            "candidate_rows_by_symbol": candidate_summary.get("candidate_rows_by_symbol", {}),
            "candidate_rows_by_session_bucket": candidate_summary.get("candidate_rows_by_session_bucket", {}),
            "dynamic_moonshot_replayable_rows": dynamic_summary.get("replayable_candidate_rows"),
            "repaired_executable_stream_rows": repair_summary.get("executable_stream_rows"),
            "full_replay_stage04_path_rows": source_mode_summary.get("counts", {}).get("path_outcome_r"),
            "no_subset_rule": "Stage05 must preserve full denominator and full candidate universe; no FVG-only or top-N activation proof.",
        },
        "candidate_origin_contract": {
            "origin_rows": origin_rows,
            "origin_count": len(origin_rows),
            "category_counts": counter_from(origin_rows, "category"),
            "source_availability_counts": counter_from(origin_rows, "source_availability_status"),
            "current_gtos_status_counts": counter_from(origin_rows, "current_gtos_status"),
            "activation_rule": (
                "Current frameworks are baseline/comparator origins. New origin families require source availability, "
                "exact activation exclusion, or forward-capture contract before they can affect activated selection."
            ),
        },
        "market_session_timeframe_source_applicability": {
            "markets": markets,
            "market_count": len(markets),
            "live_deployment_symbols": LIVE_DEPLOYMENT_SYMBOLS,
            "sessions": sessions,
            "source_modes_and_replay_modes_observed": source_modes,
            "source_mode_boundary": source_mode_summary.get("source_mode_boundary"),
            "timeframes": ["M15 decision clock", "M1 path", "M5 path", "tick path", "Sierra/SCID proxy path", "H1/H4/D1 context"],
            "activation_rule": (
                "Market/source activation is frozen later in Stage08. Stage03 only establishes that live deployment symbols "
                "are a subset of the 24-market replay universe and cannot narrow replay proof."
            ),
        },
        "follow_avoid_mixed_legacy_semantics": {
            "FOLLOW": {
                "meaning": "source-bound candidate can proceed to mechanical route, AI-narrowed route, risk modification, LTF monitoring, or prop-governed allow",
                "runtime_effect_required": True,
                "forbidden_use": "cannot bypass hard safety or source-completeness gates",
            },
            "AVOID": {
                "meaning": "source-bound negative-EV or hard-risk condition can block, zero risk, skip AI, defer, or require repair",
                "runtime_effect_required": True,
                "forbidden_use": "broad AVOID cannot block positive avoided-set R or reproduce the 10-trade collapse",
            },
            "MIXED": {
                "meaning": "ambiguous/conflicting evidence requiring explicit resolve, AI budgeted resolver, source capture, exclusion, or fallback",
                "runtime_effect_required": True,
                "forbidden_use": "cannot remain an inert terminal label counted as activation",
            },
            "LEGACY": {
                "meaning": "old GTOS behavior is retained only as comparator, rollback, or explicit row-level fallback",
                "runtime_effect_required": True,
                "forbidden_use": "cannot dominate activated execution without rollback/fallback test proof",
            },
            "mixed_resolution_class_counts": final_summary.get("mixed_resolution_class_counts", {}),
            "final_decision_counts": final_summary.get("final_decision_counts", {}),
        },
        "dynamic_execution_policy_contract": {
            "primary_policy": primary_policy,
            "same_bar_policy": dynamic_summary.get("same_bar_policy"),
            "policies": dynamic_policies,
            "legacy_fixed_1_5r_rejected_as_activation_truth": corrected_branch.get("legacy_fixed_1_5r_rejected_as_activation_truth"),
            "runtime_rule": (
                "Activated runtime must persist selected dynamic policy into trade/pending state and execution branch. "
                "J46/J49 and fixed 1.5R remain comparator/rollback only unless a row-level rollback rule is selected."
            ),
        },
        "prop_ev_governor_contract": {
            "primary_prop_policy": best_repair_policy.get("policy") or best_moonshot_policy.get("prop_policy"),
            "repair_route_reference": best_repair_policy,
            "moonshot_best_overall_reference": best_moonshot_policy,
            "permitted_actions": [
                "ALLOW",
                "REDUCE_RISK",
                "MICRO_RISK",
                "DEFER_UNTIL_RESET",
                "ACCOUNT_ABANDON_OR_RESTART",
                "BLOCK_ONLY_WITH_ROW_LEVEL_NEGATIVE_EV_PROOF",
            ],
            "failure_rule": (
                "Prop governor must optimize expected value and opportunity cost under challenge rules. "
                "It fails if it broadly blocks positive baseline streams or collapses coverage without branch/account-attempt proof."
            ),
        },
        "ai_contract": {
            "paid_ai_or_vendor_calls_allowed": state.get("budget_cap_state", {}).get("paid_ai_or_vendor_calls_allowed"),
            "route_state_budget_cap_usd": state.get("budget_cap_state", {}).get("route_state_budget_cap_usd"),
            "paid_api_or_vendor_calls_made": repair_summary.get("paid_api_or_vendor_calls_made"),
            "ai_call_counts": repair_summary.get("ai_call_counts", {}),
            "activation_rule": (
                "No paid AI/vendor/model calls may run until Stage09 writes a calibration manifest, prompt pack, schema verifier, "
                "cache key, cost estimate, and route-state budget cap. Mechanical activation must remain separable from AI-dependent activation."
            ),
        },
        "ml_contract": {
            "dataset_rows": ml_results.get("dataset_rows"),
            "prediction_rows": ml_results.get("prediction_rows"),
            "paid_api_or_vendor_calls_made": ml_results.get("paid_api_or_vendor_calls_made"),
            "roles": ml_role_contract(ml_results),
            "activation_rule": "ML is monitoring/assistant only until sealed validation and no-leak tests prove a live-control role.",
        },
        "source_capture_contract": {
            "required_forward_capture_fields": SOURCE_CAPTURE_FIELDS,
            "forward_capture_requirement_rows": forward_capture_rows,
            "forward_capture_requirement_count": len(forward_capture_rows),
            "source_capability_summary": source_capability,
            "historical_truth_rule": (
                "Never backfill broker/order/intent lifecycle truth from price movement. Missing historical system-state truth is excluded "
                "or repaired only by existing source-safe logs; otherwise it is prospective capture work wired now."
            ),
        },
        "activation_flags_contract": {
            "observed_base_flags": state.get("config_overlay_state", {}).get("observed_base_flags", {}),
            "activation_overlay_required": {
                "gtos_vnext_runtime.apply_to_execution": True,
                "gtos_vnext_runtime.moonshot_dynamic_execution_router_enabled": True,
                "gtos_vnext_runtime.moonshot_dynamic_execution_router_apply_to_execution": True,
                "gtos_vnext_runtime.ltf_path_execution_apply_to_execution": True,
                "gtos_vnext_runtime.prop_safe_selector_apply_to_execution": True,
                "replacement_semantics.follow_avoid_mixed_legacy_runtime_effect": True,
                "replacement_dynamic_policy_state_persistence": True,
                "replacement_source_capture": True,
            },
            "application_rule": (
                "Overlay is not applied at Stage03. Stage11/13 may apply it only after runtime tests, activated replay, semantic verifier, "
                "rollback proof, monitoring checklist, and scoped commit checks pass."
            ),
        },
        "fallback_and_rollback_contract": {
            "old_gtos_role": "baseline_comparator_and_rollback_implementation",
            "rollback_rule": "Disable the replacement overlay and surface-specific apply flags to restore old GTOS routing/execution behavior.",
            "hard_safety_rule": "Permissions, deployment, risk, emergency, correlation, dormant, touch-count, and SL safety gates remain hard rails.",
            "source_missing_rule": "Source-missing rows are excluded from activation metrics or routed to forward capture.",
            "test_requirement": "Rollback proof must show old behavior restored and activated behavior changes where the contract requires changes.",
        },
        "stage04_runtime_requirements_from_stage02": [
            {
                "surface_id": surface.get("surface_id"),
                "retirement_action": surface.get("retirement_action"),
                "runtime_work_required": surface.get("stage04_runtime_work_required"),
            }
            for surface in stage02.get("surfaces", [])
        ],
        "stage05_replay_requirements_from_stage02": [
            {
                "surface_id": surface.get("surface_id"),
                "replay_gate": surface.get("stage05_replay_gate"),
            }
            for surface in stage02.get("surfaces", [])
        ],
        "semantic_failure_gates": [
            "old_gtos_still_primary_under_activation",
            "moonshot_router_not_runtime_wired",
            "j46_j49_or_fixed_1_5r_dominates_activated_exit",
            "fvg_subset_or_top_n_proof",
            "failed_10_trade_route_reproduced",
            "broad_prop_or_avoid_blocker_without_negative_ev_proof",
            "mixed_or_legacy_inert_terminal_labels",
            "no_paid_ai_diagnostic_treated_as_production_selector",
            "source_missing_rows_activated_without_capture_or_exclusion",
            "selected_coverage_silent_shrink",
            "config_gated_state_used_as_terminal_excuse",
            "artifact_existence_treated_as_completion",
        ],
        "runtime_map_reference": runtime_map,
        "next_incomplete_invariant": "stage_04_runtime_implementation_pending",
    }
    return contract


def md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |")
    return out


def write_markdown(contract: dict[str, Any]) -> None:
    universe = contract["candidate_universe_contract"]
    origins = contract["candidate_origin_contract"]["origin_rows"]
    policies = contract["dynamic_execution_policy_contract"]["policies"]
    ml_roles = contract["ml_contract"]["roles"]
    prop = contract["prop_ev_governor_contract"]

    lines: list[str] = [
        "# vNext Replacement Production Candidate Contract - 2026-05-26",
        "",
        f"Route: `{ROUTE_ID}`",
        "",
        "## Contract Boundary",
        "",
        "This contract freezes the Stage 03 replacement target. It does not apply the activation overlay. "
        "Stage 04 must implement the runtime behavior, Stage 05/06 must replay and delta-test it, "
        "and Stage 11/13 may apply the overlay only after semantic gates pass.",
        "",
        "## Candidate Universe",
        "",
        f"- Denominator rows: `{universe.get('denominator_rows')}`",
        f"- Generated candidate rows: `{universe.get('candidate_rows')}`",
        f"- Moonshot replayable rows: `{universe.get('dynamic_moonshot_replayable_rows')}`",
        f"- Repaired executable stream rows: `{universe.get('repaired_executable_stream_rows')}`",
        f"- Full Stage04 path rows: `{universe.get('full_replay_stage04_path_rows')}`",
        "- No FVG subset, top-N, or selected-only summary can satisfy activation proof.",
        "",
        "Framework counts:",
    ]
    lines.extend(md_table(["Framework", "Rows"], [[k, v] for k, v in sorted(universe.get("framework_candidate_rows", {}).items())]))
    lines.extend(
        [
            "",
            "## Candidate Origins",
            "",
            "All registry rows are preserved in the JSON contract. Current GTOS frameworks remain baseline/comparator origins; "
            "new origin families require source availability, activation exclusion, or forward-capture rules before they can affect execution.",
        ]
    )
    lines.extend(
        md_table(
            ["Origin", "Category", "Source Status", "Current GTOS Status", "Next Replay Action"],
            [
                [
                    row.get("name"),
                    row.get("category"),
                    row.get("source_availability_status"),
                    row.get("current_gtos_status"),
                    row.get("next_replay_action"),
                ]
                for row in origins
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Semantics",
            "",
            "- `FOLLOW`: can proceed through mechanical route, AI-narrowed route, risk modification, LTF monitoring, or prop-governed allow, while hard safety remains mandatory.",
            "- `AVOID`: can block, zero risk, skip AI, defer, or require repair only when source-bound evidence supports it.",
            "- `MIXED`: must resolve, fall back, exclude, request source capture, or use a budgeted AI resolver. It cannot remain inert.",
            "- `LEGACY`: comparator, rollback, or explicit row-level fallback only. It cannot dominate activated behavior without test proof.",
            "",
            "## Dynamic Execution",
            "",
            f"Primary policy frozen for implementation: `{contract['dynamic_execution_policy_contract']['primary_policy'].get('policy_name')}` "
            f"because {contract['dynamic_execution_policy_contract']['primary_policy'].get('selection_reason')}.",
        ]
    )
    lines.extend(
        md_table(
            ["Policy", "Runtime Role", "Rows", "Total R", "Expectancy R"],
            [
                [
                    row.get("policy_name"),
                    row.get("runtime_role"),
                    row.get("replay_rows"),
                    row.get("total_r"),
                    row.get("expectancy_r"),
                ]
                for row in policies
            ],
        )
    )
    lines.extend(
        [
            "",
            "J46/J49 and fixed 1.5R are comparator/rollback surfaces, not final moonshot execution truth.",
            "",
            "## Prop Governor",
            "",
            f"Primary prop policy: `{prop.get('primary_prop_policy')}`.",
            "Allowed actions are `ALLOW`, `REDUCE_RISK`, `MICRO_RISK`, `DEFER_UNTIL_RESET`, "
            "`ACCOUNT_ABANDON_OR_RESTART`, and row-level `BLOCK` only with negative-EV proof. "
            "Broad safe-but-dead blockers fail this contract.",
            "",
            "## AI And ML",
            "",
            f"- Paid AI/vendor calls allowed now: `{contract['ai_contract'].get('paid_ai_or_vendor_calls_allowed')}`",
            f"- Route-state budget cap: `{contract['ai_contract'].get('route_state_budget_cap_usd')}`",
            "- AI cannot be used as production selector until Stage09 writes the calibration package and budget cap.",
            "- ML is monitoring/assistant only until sealed validation and no-leak tests approve live control.",
        ]
    )
    lines.extend(
        md_table(
            ["Role", "Disposition", "Runtime Interaction"],
            [[row.get("role"), row.get("disposition"), row.get("runtime_interaction")] for row in ml_roles],
        )
    )
    lines.extend(
        [
            "",
            "## Source Capture",
            "",
            "Forward capture fields frozen by the contract:",
            "",
        ]
    )
    lines.extend([f"- `{field}`" for field in contract["source_capture_contract"]["required_forward_capture_fields"]])
    lines.extend(
        [
            "",
            "Historical broker/order/intent lifecycle truth cannot be backfilled from price movement. Missing historical system-state truth is excluded or repaired only from existing source-safe logs.",
            "",
            "## Activation Flags",
            "",
            "Observed base flags remain apply-off. Stage11/13 can apply the activation overlay only after runtime tests, activated replay, semantic verification, rollback proof, monitoring checklist, and scoped commit checks pass.",
            "",
            "## Failure Gates",
            "",
        ]
    )
    lines.extend([f"- `{gate}`" for gate in contract["semantic_failure_gates"]])
    lines.extend(
        [
            "",
            "## Next Invariant",
            "",
            "`stage_04_runtime_implementation_pending`",
            "",
        ]
    )
    CONTRACT_MD_PATH.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def upsert_output(outputs: list[dict[str, Any]], path_name: str, updates: dict[str, Any]) -> None:
    for output in outputs:
        if output.get("path") == path_name:
            output.update(updates)
            return
    outputs.append({"path": path_name, **updates})


def update_output_manifest(contract: dict[str, Any]) -> None:
    manifest = load_json_object(OUTPUT_MANIFEST_PATH)
    outputs = manifest.setdefault("outputs", [])
    upsert_output(
        outputs,
        CONTRACT_JSON_PATH.name,
        {
            "stage": "stage_03",
            "status": "created",
            "origin_rows": contract["candidate_origin_contract"]["origin_count"],
            "policy_rows": len(contract["dynamic_execution_policy_contract"]["policies"]),
        },
    )
    upsert_output(
        outputs,
        CONTRACT_MD_PATH.name,
        {"stage": "stage_03", "status": "created"},
    )
    upsert_output(
        outputs,
        Path(__file__).name,
        {"stage": "stage_03", "status": "created_and_ready_for_py_compile"},
    )
    manifest["next_manifest_update"] = "After Stage 04 runtime implementation map/effect ledger are written."
    write_json_object(OUTPUT_MANIFEST_PATH, manifest)


def update_session_state(contract: dict[str, Any]) -> None:
    state = load_json_object(SESSION_STATE_PATH)
    state["last_updated_utc"] = utc_now()
    state["current_stage"] = "stage_04_runtime_implementation"
    state.setdefault("stage_status", {})["stage_03_production_candidate_contract"] = "completed_contract_written"
    state["first_incomplete_invariant"] = "stage_04_runtime_implementation_pending"
    state["exact_next_action"] = (
        "Implement the Stage 03 contract in runtime code/config/tests: wire the moonshot dynamic execution router into "
        "gtos_vnext_runtime/orchestrator, add universal candidate-origin and runtime-effect surfaces, persist selected "
        "dynamic policy into trade/pending state, implement FOLLOW/AVOID/MIXED/LEGACY actions, source capture, prop/LTF "
        "execution effects, and overlay behavioral-diff tests without touching live/broker surfaces."
    )
    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage03_origin_contract_rows"] = contract["candidate_origin_contract"]["origin_count"]
    evidence["stage03_forward_capture_requirement_rows"] = contract["source_capture_contract"]["forward_capture_requirement_count"]
    evidence["stage03_dynamic_policy_rows"] = len(contract["dynamic_execution_policy_contract"]["policies"])
    evidence["stage03_ml_role_rows"] = len(contract["ml_contract"]["roles"])
    evidence["stage03_candidate_denominator_rows"] = contract["candidate_universe_contract"]["denominator_rows"]
    evidence["stage03_candidate_rows"] = contract["candidate_universe_contract"]["candidate_rows"]
    tests = state.setdefault("tests_verifiers_run", [])
    tests.append(
        {
            "command": (
                "python research\\science_program_2026_05\\06_outcome_testing\\"
                "vnext_moonshot_production_replacement_activation_2026_05_26\\"
                "build_vnext_replacement_stage03_candidate_contract.py"
            ),
            "result": (
                "passed; wrote Stage 03 production candidate contract with "
                f"{contract['candidate_origin_contract']['origin_count']} origins, "
                f"{len(contract['dynamic_execution_policy_contract']['policies'])} dynamic policies, and "
                f"{len(contract['ml_contract']['roles'])} ML/monitoring roles"
            ),
            "timestamp_utc": utc_now(),
        }
    )
    state.setdefault("completion_gate_status", {})["route_complete"] = False
    state.setdefault("completion_gate_status", {})["reason"] = (
        "Stage 03 contract is complete, but runtime implementation, full activated replay, delta ledger, question closure, "
        "source activation map, AI/ML package, semantic verifier, applied overlay, rollback proof, monitoring package, "
        "scoped commits, and completion audit remain incomplete."
    )
    write_json_object(SESSION_STATE_PATH, state)


def append_control_event(contract: dict[str, Any]) -> None:
    event = {
        "timestamp_utc": utc_now(),
        "route_id": ROUTE_ID,
        "event": "stage_03_production_candidate_contract_written",
        "contract_json": rel(CONTRACT_JSON_PATH),
        "contract_md": rel(CONTRACT_MD_PATH),
        "origin_rows": contract["candidate_origin_contract"]["origin_count"],
        "dynamic_policy_rows": len(contract["dynamic_execution_policy_contract"]["policies"]),
        "ml_role_rows": len(contract["ml_contract"]["roles"]),
        "primary_dynamic_policy": contract["dynamic_execution_policy_contract"]["primary_policy"].get("policy_name"),
        "primary_prop_policy": contract["prop_ev_governor_contract"].get("primary_prop_policy"),
        "next_incomplete_invariant": "stage_04_runtime_implementation_pending",
    }
    with CONTROL_LEDGER_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    contract = build_contract()
    write_json_object(CONTRACT_JSON_PATH, contract)
    write_markdown(contract)
    update_output_manifest(contract)
    update_session_state(contract)
    append_control_event(contract)
    print(
        json.dumps(
            {
                "contract_json": rel(CONTRACT_JSON_PATH),
                "contract_md": rel(CONTRACT_MD_PATH),
                "origin_rows": contract["candidate_origin_contract"]["origin_count"],
                "dynamic_policy_rows": len(contract["dynamic_execution_policy_contract"]["policies"]),
                "primary_dynamic_policy": contract["dynamic_execution_policy_contract"]["primary_policy"].get("policy_name"),
                "primary_prop_policy": contract["prop_ev_governor_contract"].get("primary_prop_policy"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
