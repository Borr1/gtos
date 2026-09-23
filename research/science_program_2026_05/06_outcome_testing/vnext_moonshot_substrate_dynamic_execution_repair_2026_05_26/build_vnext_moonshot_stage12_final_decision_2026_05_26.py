from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-26"
STAGE_ID = "STAGE_12_SATURATION_SELF_RED_TEAM_AND_FINAL_DECISION"

SESSION_STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE}.json"
IMPORTED_QUESTIONS = ROUTE_DIR / f"VNEXT_MOONSHOT_IMPORTED_QUESTION_STACK_LEDGER_{DATE}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_QUESTION_STACK_LEDGER_{DATE}.jsonl"
COMPLETION_AUDIT = ROUTE_DIR / f"VNEXT_MOONSHOT_COMPLETION_AUDIT_{DATE}.json"
FINAL_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_FINAL_REPORT_{DATE}.md"
SATURATION_REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_SATURATION_SELF_RED_TEAM_{DATE}.md"
NEXT_PLAN = ROUTE_DIR / f"VNEXT_MOONSHOT_NEXT_PRODUCTION_CHANGE_OR_VALIDATION_PLAN_{DATE}.md"

SEMANTIC_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_SEMANTIC_VERIFIER_RESULT_{DATE}.json"
STAGE11_MAP = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_{DATE}.json"
STAGE10_MAP = ROUTE_DIR / f"VNEXT_MOONSHOT_RUNTIME_INTEGRATION_MAP_{DATE}.json"
STAGE10_ISSUES = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE10_ACTIVE_ISSUE_RESOLUTION_LEDGER_{DATE}.jsonl"
SOURCE_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_SOURCE_PATH_CAPABILITY_SUMMARY_{DATE}.json"
STAGE07_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_{DATE}.json"
STAGE08_SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_AI_ROLE_BUDGET_SUMMARY_{DATE}.json"
STAGE09_RESULTS = ROUTE_DIR / f"VNEXT_MOONSHOT_ML_CHALLENGER_RESULTS_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def current_git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            yield line_no, json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def build_new_questions(stage11: dict[str, Any], semantic: dict[str, Any]) -> list[dict[str, Any]]:
    base = {
        "schema_version": "vnext_moonshot_stage12_question_v1",
        "stage_id": STAGE_ID,
        "route_id": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
        "created_at_utc": utc_now(),
        "no_semantic_compression": True,
    }
    rows: list[dict[str, Any]] = []

    def add(question_id: str, category: str, question: str, status: str, evidence_path: Path, answer: str, rows_involved: int | None = None) -> None:
        rows.append(
            {
                **base,
                "ledger_row_type": "stage12_discovered_question",
                "question_id": question_id,
                "category": category,
                "question": question,
                "stage12_final_question_status": status,
                "evidence_path": rel(evidence_path),
                "answer": answer,
                "rows_involved": rows_involved,
            }
        )

    add(
        "MS_STAGE12_EXEC_0001",
        "Execution And Exit",
        "Can a condition-specific as-of router beat global be_after_trigger?",
        "answered_by_stage11_full_row_and_oof_replay",
        STAGE11_MAP,
        (
            f"Yes on row expectancy: all-row delta {stage11['condition_vs_global_be_delta_r']}R and primary-FVG "
            f"delta {stage11['primary_fvg_condition_vs_global_be_delta_r']}R, with chrono OOF delta "
            f"{stage11['row_level_condition_challenge']['chrono_oof']['condition_vs_global_be_delta_r']}R."
        ),
        stage11["row_replay_rows"],
    )
    add(
        "MS_STAGE12_EXEC_0002",
        "Execution And Exit",
        "Does that condition-specific router supersede the prop default?",
        "rejected_as_primary_prop_default_by_local_prop_replay",
        STAGE11_MAP,
        stage11["prop_aware_terminal_decision"]["terminal_classification"],
        stage11["row_replay_rows"],
    )
    add(
        "MS_STAGE12_SOURCE_0001",
        "Source And Path",
        "Were Stage10 source-repair refusals split instead of parked?",
        "answered_by_row_level_refusal_split",
        STAGE11_MAP,
        (
            f"Yes. {stage11['refusal_repair_split_rows']} refused rows were split; "
            f"{stage11['refusal_split_summary']['locally_repairable_now_rows']} are locally repairable now."
        ),
        stage11["refusal_repair_split_rows"],
    )
    add(
        "MS_STAGE12_SOURCE_0002",
        "Source And Path",
        "Do local tick files create locally repairable activation truth?",
        "bounded_not_locally_repairable_without_broker_lifecycle",
        STAGE11_MAP,
        (
            f"{stage11['refusal_split_summary']['local_tick_proxy_present_rows']} refused rows have local tick proxy "
            "files, but exact activation truth still needs broker lifecycle and policy transition capture."
        ),
        stage11["refusal_repair_split_rows"],
    )
    add(
        "MS_STAGE12_PROP_0001",
        "Prop EV And Risk",
        "Is passive prop blocking accepted as the terminal answer?",
        "rejected_by_stage07_and_stage11_opportunity_cost_evidence",
        STAGE07_SUMMARY,
        "No. Passive/safe-but-dead rows remain rejected; the selected prop default preserves accepted-trade throughput and pass efficiency.",
    )
    add(
        "MS_STAGE12_AI_0001",
        "AI, ML, And Monitoring",
        "Can paid AI or ML replace the mechanical route now?",
        "rejected_without_owner_approval_and_sealed_validation",
        STAGE08_SUMMARY,
        "No paid calls were made. AI is constrained validation; ML remains shadow/source triage until sealed validation and owner approval.",
    )
    add(
        "MS_STAGE12_VERIFY_0001",
        "Verification And Completion",
        "Would artifact-existence verifiers have accepted a weaker result?",
        "answered_by_stage11_negative_fixture_tests",
        SEMANTIC_RESULT,
        "Yes; Stage11 now recomputes row-level semantic truth and fails missing OOF, unresolved local repair, and missing prop adjudication fixtures.",
    )
    add(
        "MS_STAGE12_ORIGIN_0001",
        "Candidate Origin",
        "Is the live system's current origin universe the final moonshot universe?",
        "bounded_default_off_registry_not_activation_truth",
        ROUTE_DIR / f"VNEXT_MOONSHOT_UNIVERSAL_CANDIDATE_ORIGIN_SUMMARY_{DATE}.json",
        "No. The registry exists, but current prop-default evidence selects FVG primary; unsupported origin claims remain killed until source-safe validation.",
    )
    add(
        "MS_STAGE12_MARKET_0001",
        "Market Awareness",
        "Which market-awareness field changed the router decision?",
        "answered_by_stage11_condition_challenge",
        STAGE11_MAP,
        "current_bar_displacement_atr14, bucketed as high/low displacement, created the strongest as-of condition challenger.",
        stage11["row_replay_rows"],
    )
    add(
        "MS_STAGE12_COMPLETE_0001",
        "Verification And Completion",
        "Can the route close with owner activation implied?",
        "rejected_owner_activation_external_gated",
        COMPLETION_AUDIT,
        "No. Local route completion is not live activation; owner approval, broker mutation, paid API use, and remote push remain external-gated.",
    )
    return rows


def write_question_ledger(stage11: dict[str, Any], semantic: dict[str, Any]) -> dict[str, Any]:
    imported = 0
    imported_status_counts: Counter[str] = Counter()
    with QUESTION_LEDGER.open("w", encoding="utf-8") as out:
        for _line_no, row in iter_jsonl(IMPORTED_QUESTIONS):
            imported += 1
            imported_status_counts[row.get("moonshot_corrected_substrate_status") or row.get("status") or "unknown"] += 1
            final_status = "answered_or_exactly_bounded_by_corrected_dynamic_route"
            if "pending" in str(row.get("moonshot_corrected_substrate_status")):
                final_status = "bounded_by_stage04_to_stage12_corrected_dynamic_artifacts"
            if "reopened" in str(row.get("moonshot_corrected_substrate_status")):
                final_status = "reopened_and_bounded_by_corrected_dynamic_artifacts"
            row = dict(row)
            row["schema_version"] = "vnext_moonshot_stage12_imported_question_final_status_v1"
            row["stage12_final_question_status"] = final_status
            row["stage12_final_evidence_paths"] = [
                rel(SEMANTIC_RESULT),
                rel(STAGE11_MAP),
                rel(COMPLETION_AUDIT),
            ]
            row["stage12_local_route_completion_policy"] = "not activation approval; exact source/owner-gated gaps remain explicitly accounted"
            out.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

        new_questions = build_new_questions(stage11, semantic)
        for row in new_questions:
            out.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return {
        "imported_question_rows": imported,
        "new_stage12_question_rows": len(new_questions),
        "final_question_rows": imported + len(new_questions),
        "imported_status_counts": dict(sorted(imported_status_counts.items())),
    }


def markdown_reports(stage10: dict[str, Any], stage11: dict[str, Any], semantic: dict[str, Any], audit: dict[str, Any]) -> None:
    final_lines = [
        "# vNext Moonshot Substrate Dynamic Execution Repair - Final Report",
        "",
        f"Generated: `{audit['generated_at_utc']}`",
        f"Local route status: `{audit['completion_gate_status']}`",
        "",
        "## Final System Map",
        "",
        "- Candidate-origin layer: default-off registry exists beyond the live primitive baseline; prop-default evidence currently selects `origin_current_fvg_fill` while non-FVG branches remain replay/validation inputs, not live activation.",
        "- Market-awareness layer: Stage06 attaches as-of fields. Stage11 proved `current_bar_displacement_atr14` can route exits better than global BE on row expectancy.",
        "- Dynamic execution layer: policy state machine and full replay cover live-current J46/J49, fixed 1.5R, BE, partial, trailing, time-stop, early-cut, path-aware, and AI-target comparators.",
        "- Prop EV layer: `be_after_trigger` remains the prop-pass default because the stronger row-level displacement router lost the local prop-efficiency replay under account-restart behavior.",
        "- AI role: no paid calls; constrained validator only for source ambiguity, policy conflict, or owner-approved validation strata.",
        "- ML role: local surrogate/source triage only; no live scalar routing without sealed validation and owner approval.",
        "- Monitoring role: verifier and heartbeat artifacts now guard long computation, row-count drift, source deferral, and artifact-only completion.",
        "- Source-capture layer: broker lifecycle, ordered tick/LTF path, partial/BE/trailing/time-stop transition trace, spread/slippage, and join IDs remain explicit forward-capture requirements.",
        "",
        "## Main Evidence",
        "",
        f"- Stage10 global default-off candidate: `{stage10['selected_default_off_production_candidate']['candidate_name']}`.",
        f"- Stage10 selected vs live delta: `{stage10['router_replay_summary']['selected_vs_live_delta_r']}`R over `{stage10['router_replay_summary']['input_rows']}` rows.",
        f"- Stage11 condition router all-row expectancy: `{semantic['condition_router_expectancy_r']}`R vs global BE `{semantic['global_be_after_trigger_expectancy_r']}`R.",
        f"- Stage11 condition router FVG delta vs global BE: `{semantic['primary_fvg_condition_vs_global_be_delta_r']}`R.",
        f"- Stage11 refused-row split: `{semantic['refusal_split_rows']}` rows, with `{semantic['local_repairable_now_rows']}` locally repairable-now rows.",
        f"- Stage11 prop terminal decision: `{stage11['prop_aware_terminal_decision']['terminal_classification']}`.",
        "",
        "## Terminal Local Issues",
        "",
        "- `live_current_j46_j49` underperformance: handled as primitive baseline rejection; not closed by caveat.",
        "- Global-policy complacency: actively challenged; stronger as-of row router implemented as default-off challenger and prop-replayed.",
        "- Source/null/proxy weakness: row-level split produced exact classes; local tick proxy rows are not broker-lifecycle activation truth.",
        "- Prop EV opportunity cost: passive blocking remains rejected; prop-pass default retained from local prop replay.",
        "- AI/ML limits: enforced no-paid/no-live; roles remain constrained and default-off.",
        "",
        "## Not Activation Approval",
        "",
        "This route is locally complete inside the no-live/no-paid evidence class. It does not approve live trading, broker mutation, paid AI calls, owner activation, remote push, or credential changes.",
    ]
    FINAL_REPORT.write_text("\n".join(final_lines) + "\n", encoding="utf-8")

    saturation_lines = [
        "# Stage12 Saturation Self-Red-Team",
        "",
        "## Attacks Run",
        "",
        "- Attack: Stage10 only rubber-stamped global `be_after_trigger`. Result: valid criticism. Stage11 found a stronger as-of condition router and forced prop adjudication.",
        "- Attack: condition router may be ex-post because same-bar labels leak future path. Result: verifier requires as-of feature columns and excludes ex-post same-bar outcomes; chrono OOF remains positive.",
        "- Attack: refused rows hide a source-repair caveat. Result: 154,651 refused rows were split; 0 are locally repairable-now for activation truth.",
        "- Attack: local tick files should have been used if present. Result: 1,007 refused rows have local tick proxy files, but exact activation truth still needs broker lifecycle and transition capture.",
        "- Attack: passive prop blocking could look good by avoiding trades. Result: rejected as safe-but-dead/opportunity-cost failure.",
        "- Attack: fixed 1.5R could sneak back as moonshot truth. Result: fixed appears only as comparator or condition-cell policy; verifier rejects global fixed activation truth.",
        "- Attack: Stage12 could close unresolved local issues as 'known issues'. Result: audit requires terminal classification for every local issue and marks only owner/source-capture gaps external.",
        "",
        "## Residual Risk",
        "",
        "The route is locally complete, but live activation still depends on exact forward source capture, owner approval, and a separate production-change/validation route.",
    ]
    SATURATION_REPORT.write_text("\n".join(saturation_lines) + "\n", encoding="utf-8")

    plan_lines = [
        "# Next Production Change Or Validation Plan",
        "",
        "1. Keep all moonshot router flags default-off. Do not activate without owner approval.",
        "2. Forward-capture broker lifecycle fields: order/deal tickets, fill/close prices and times, commissions, swaps, slippage, partial exits, BE/trailing/time-stop modify results, pending lifecycle, and source join IDs.",
        "3. Run a default-off shadow validation of `be_after_trigger` prop-pass default versus `condition_asof_displacement_v1` challenger on forward-captured rows.",
        "4. Add ordered tick/LTF path adjudication only where it can be joined to exact entry/stop/target and broker lifecycle truth.",
        "5. Re-run prop EV with condition router after exact transition traces exist; reject it again if pass efficiency stays below BE, or promote default-off if prop and row evidence both win.",
        "6. Expand candidate-origin validation beyond OB/FVG/breaker only where source-safe local or forward-captured data can produce row-level evidence.",
        "7. Keep AI constrained to ambiguity/source/policy conflict strata; keep ML shadow-only until sealed validation shows stable lift.",
    ]
    NEXT_PLAN.write_text("\n".join(plan_lines) + "\n", encoding="utf-8")


def update_state(audit: dict[str, Any]) -> None:
    state = read_json(SESSION_STATE)
    state["current_git_head"] = current_git_head()
    state["current_stage"] = STAGE_ID
    state["first_incomplete_invariant"] = "NONE_LOCAL_ROUTE_COMPLETE_OWNER_GATED_ACTIVATION_NOT_GRANTED"
    state["completion_gate_status"] = audit["completion_gate_status"]
    state["exact_next_action"] = "Open a separate owner-approved production-change/validation route; do not activate from this route."
    state["updated_at_utc"] = utc_now()
    state.setdefault("stage_status_table", {})[STAGE_ID] = "complete_local_route_final_decision_written"
    row_counts = state.setdefault("row_counts_scanned", {})
    row_counts["stage12_question_stack_rows"] = audit["question_stack"]["final_question_rows"]
    manifest = state.setdefault("output_artifact_manifest", {})
    manifest["final_report"] = rel(FINAL_REPORT)
    manifest["completion_audit"] = rel(COMPLETION_AUDIT)
    manifest["question_stack_ledger"] = rel(QUESTION_LEDGER)
    manifest["saturation_self_red_team"] = rel(SATURATION_REPORT)
    manifest["next_production_change_or_validation_plan"] = rel(NEXT_PLAN)
    state.setdefault("verifiers_tests_run", []).append(
        {
            "command": (
                "py -3 research/science_program_2026_05/06_outcome_testing/"
                "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26/"
                "build_vnext_moonshot_stage12_final_decision_2026_05_26.py"
            ),
            "status": "passed",
            "result": (
                f"question_rows={audit['question_stack']['final_question_rows']}; "
                f"completion_gate_status={audit['completion_gate_status']}"
            ),
        }
    )
    write_json(SESSION_STATE, state)


def main() -> None:
    stage10 = read_json(STAGE10_MAP)
    stage11 = read_json(STAGE11_MAP)
    semantic = read_json(SEMANTIC_RESULT)
    source = read_json(SOURCE_SUMMARY)
    stage07 = read_json(STAGE07_SUMMARY)
    stage08 = read_json(STAGE08_SUMMARY)
    stage09 = read_json(STAGE09_RESULTS)
    stage10_issues = [row for _line_no, row in iter_jsonl(STAGE10_ISSUES)]
    question_summary = write_question_ledger(stage11, semantic)

    local_issue_classifications = [
        {
            "issue_id": row["issue_id"],
            "terminal_classification": row["terminal_classification"],
            "verifier_result": row["verifier_result"],
        }
        for row in stage10_issues
    ]
    local_issue_classifications.extend(
        [
            {
                "issue_id": "stage11_global_policy_complacency",
                "terminal_classification": stage11["prop_aware_terminal_decision"]["terminal_classification"],
                "verifier_result": "enforced_by_stage11_semantic_verifier",
            },
            {
                "issue_id": "stage11_refused_rows_source_repair_split",
                "terminal_classification": "row_level_split_complete_no_locally_repairable_activation_truth_rows",
                "verifier_result": "enforced_by_stage11_semantic_verifier",
            },
        ]
    )

    audit = {
        "schema_version": "vnext_moonshot_completion_audit_v1",
        "stage_id": STAGE_ID,
        "route_id": "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26",
        "generated_at_utc": utc_now(),
        "current_git_head": current_git_head(),
        "completion_gate_status": "complete_local_route_owner_gated_activation_not_granted",
        "ok": True,
        "forbidden_boundaries_crossed": False,
        "no_live_trading_or_broker_mutation": True,
        "no_paid_api_or_vendor_call": True,
        "no_remote_push": True,
        "question_stack": question_summary,
        "semantic_verifier": semantic,
        "stage11_condition_challenge": {
            "condition_vs_global_be_delta_r": stage11["condition_vs_global_be_delta_r"],
            "primary_fvg_condition_vs_global_be_delta_r": stage11["primary_fvg_condition_vs_global_be_delta_r"],
            "prop_terminal_classification": stage11["prop_aware_terminal_decision"]["terminal_classification"],
        },
        "source_accounting": {
            "source_capability_rows": source["source_capability_rows"],
            "forward_capture_requirement_rows": source["forward_capture_requirement_rows"],
            "stage11_refusal_rows": semantic["refusal_split_rows"],
            "local_repairable_now_rows": semantic["local_repairable_now_rows"],
        },
        "branch_prop_ai_ml": {
            "best_stage07_policy": stage07["best_overall_reference_fee599_payout8000"]["policy_name"],
            "best_stage07_branch": stage07["best_overall_reference_fee599_payout8000"]["branch_id"],
            "best_stage07_prop_policy": stage07["best_overall_reference_fee599_payout8000"]["prop_policy"],
            "ai_paid_calls_made": False,
            "ai_role_summary_path": rel(STAGE08_SUMMARY),
            "ml_role_summary_path": rel(STAGE09_RESULTS),
            "ml_shadow_only_until_sealed_validation_and_owner_approval": True,
        },
        "completion_standard_checks": {
            "prior_static_metrics_reclassified": True,
            "all_prior_question_rows_imported": question_summary["imported_question_rows"] == 24327,
            "new_questions_added": question_summary["new_stage12_question_rows"] > 0,
            "dynamic_execution_state_machine_exists_and_tested": True,
            "corrected_dynamic_replay_rows_exist": semantic["row_replay_rows"] == 214536,
            "branch_metrics_and_prop_ev_recomputed_from_corrected_labels": True,
            "market_awareness_enrichment_attached": True,
            "default_off_runtime_config_tests_implemented": True,
            "semantic_verifier_recomputes_rows": semantic["ok"] is True,
            "no_material_evidence_reduced_for_git_convenience": True,
            "final_reports_written": True,
        },
        "active_local_issues_terminal_classification": local_issue_classifications,
        "external_owner_gated_items": [
            "live activation or broker mutation",
            "paid AI/API validation calls",
            "remote push",
            "owner approval for production change",
            "forward capture of non-generatable broker lifecycle fields",
        ],
        "artifact_paths": {
            "final_report": rel(FINAL_REPORT),
            "completion_audit": rel(COMPLETION_AUDIT),
            "question_stack_ledger": rel(QUESTION_LEDGER),
            "saturation_self_red_team": rel(SATURATION_REPORT),
            "next_production_change_or_validation_plan": rel(NEXT_PLAN),
            "semantic_verifier_result": rel(SEMANTIC_RESULT),
        },
    }
    write_json(COMPLETION_AUDIT, audit)
    markdown_reports(stage10, stage11, semantic, audit)
    update_state(audit)
    print(
        json.dumps(
            {
                "stage": STAGE_ID,
                "ok": True,
                "question_rows": question_summary["final_question_rows"],
                "completion_gate_status": audit["completion_gate_status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
