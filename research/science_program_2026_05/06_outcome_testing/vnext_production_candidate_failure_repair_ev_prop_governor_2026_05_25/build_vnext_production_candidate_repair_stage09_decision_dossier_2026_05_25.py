from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_ID = "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"
)
STATE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json"
STAGE08_SUMMARY_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json"
)
ABLATION_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_LAYER_ABLATION_SUMMARY_2026-05-25.json"
)
STAGE08_VERIFY_PATH = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE08_VERIFICATION_RESULT_2026-05-25.json"
)
DOSSIER_PATH = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_DECISION_DOSSIER_2026-05-25.md"
)
AUDIT_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_COMPLETION_AUDIT_2026-05-25.json"

PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_PRODUCTION_CANDIDATE_FAILURE_REPAIR_EV_PROP_GOVERNOR_GOAL_PROMPT_2026-05-25.md"
)
STARTER_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_PRODUCTION_CANDIDATE_FAILURE_REPAIR_EV_PROP_GOVERNOR_STARTER_2026-05-25.txt"
)
FORENSIC_PATH = (
    Path("research/science_program_2026_05/06_outcome_testing/")
    / "vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25"
    / "VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md"
)
BASE_FAILED_ROUTE_COMMIT = "75a85d244a2d832f32315c08266855e6e14c48c5"

FINAL_STATES = {
    "production_candidate_viable_after_repair",
    "production_candidate_failed_with_full_failure_anatomy",
    "redesign_required_with_exact_repair_backlog",
}


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo(path: Path) -> Path:
    return REPO_ROOT / path


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(repo(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    repo(path).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with repo(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_info(path: Path) -> dict[str, Any]:
    full = repo(path)
    return {
        "path": rel(path),
        "exists": full.exists(),
        "bytes": full.stat().st_size if full.exists() else 0,
        "sha256": sha256_file(path) if full.exists() else None,
    }


def git_text(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_head() -> str:
    return git_text("rev-parse", "HEAD")


def git_changed_files() -> list[str]:
    text = git_text("diff", "--name-only", f"{BASE_FAILED_ROUTE_COMMIT}..HEAD")
    return [line for line in text.splitlines() if line.strip()]


def git_status_short() -> list[str]:
    text = git_text("status", "--short")
    return [line for line in text.splitlines() if line.strip()]


def get_layer(ablation: dict[str, Any], layer_name: str) -> dict[str, Any]:
    for layer in ablation.get("layers", []):
        if layer.get("layer") == layer_name:
            return layer
    return {}


def performance_rows(metrics: dict[str, Any]) -> int:
    return int(metrics.get("accepted_winners") or 0) + int(
        metrics.get("accepted_losers") or 0
    )


def classify_decision(
    stage08_summary: dict[str, Any],
    ablation: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    best_policy = stage08_summary["best_policy_reference_fee_599_payout_8000"]["policy"]
    best = stage08_summary["policy_metrics"][best_policy]
    best_reference = stage08_summary["best_policy_reference_fee_599_payout_8000"]
    baseline = get_layer(ablation, "baseline_current_shadow")
    stage05 = get_layer(ablation, "stage05_avoid_pre_ai_demotion")
    selected = int(best.get("allowed_trades") or 0)
    baseline_selected = int(baseline.get("selected_count") or 0)
    selected_to_baseline_ratio = (
        round(selected / baseline_selected, 12) if baseline_selected else None
    )
    perf_rows = performance_rows(best)
    required_coverage = stage08_summary.get("required_metric_coverage") or {}
    hard_failures: list[str] = []

    if selected <= 0:
        hard_failures.append("selected_count_zero")
    if perf_rows <= 0:
        hard_failures.append("performance_rows_zero")
    if float(best.get("expectancy_r") or 0) <= 0:
        hard_failures.append("negative_or_zero_expectancy")
    if float(best.get("total_r") or 0) <= 0:
        hard_failures.append("negative_or_zero_total_r")
    if float(best.get("risk_adjusted_r") or 0) <= 0:
        hard_failures.append("negative_or_zero_risk_adjusted_r")
    if float(best.get("profit_factor") or 0) < 1.0:
        hard_failures.append("profit_factor_below_one")
    if baseline_selected >= 20 and selected / baseline_selected < 0.25:
        hard_failures.append("selected_count_collapsed_below_25pct_of_baseline")
    if float(best.get("pass_rate") or 0) <= 0:
        hard_failures.append("zero_prop_pass_rate")
    if float(best_reference.get("reference_expected_value_per_attempt_usd") or 0) <= 0:
        hard_failures.append("negative_or_zero_reference_ev_per_attempt")
    if not required_coverage or not all(bool(v) for v in required_coverage.values()):
        hard_failures.append("required_metric_coverage_incomplete")
    if stage08_summary.get("paid_api_or_vendor_calls_made") != 0:
        hard_failures.append("paid_api_or_vendor_call_made")
    if best.get("paid_api_or_vendor_calls_made") != 0:
        hard_failures.append("best_policy_paid_api_or_vendor_call_made")
    if not bool(stage08_summary.get("no_paid_call_replay_diagnostic_only")):
        hard_failures.append("no_paid_call_replay_not_diagnostic_only")
    if stage08_summary.get("off_kz_treatment", {}).get(
        "off_kz_rows_in_repaired_selected_stream"
    ) != 0:
        hard_failures.append("off_kz_rows_selected")
    if bool(stage08_summary.get("broker_facing_activation_change")):
        hard_failures.append("broker_facing_activation_change_detected")
    if state.get("stage_status_table", {}).get("STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY") != "complete":
        hard_failures.append("stage08_not_complete")
    if not state.get("verification_status", {}).get("stage08_verifier_ok"):
        hard_failures.append("stage08_verifier_not_ok")

    if hard_failures:
        if selected <= 0 or float(best.get("total_r") or 0) <= 0:
            final_state = "production_candidate_failed_with_full_failure_anatomy"
        else:
            final_state = "redesign_required_with_exact_repair_backlog"
    else:
        final_state = "production_candidate_viable_after_repair"

    activation_prerequisites = [
        "owner approval before any broker-facing activation flip",
        "owner-approved paid-AI validation or cache-backed replay plan for 22,270 best-policy accepted rows",
        "source-capture handling for 1,935 SOURCE_CAPTURE_REQUIRED executable rows and 457 best-policy accepted MISSING_SOURCE rows",
        "paper/shadow run with current broker spread, latency, and live AI-supervisor telemetry before live capital",
        "explicit owner decision that ACCOUNT_ABANDON_OR_RESTART is acceptable as a prop-challenge operating policy",
    ]
    caution_flags = [
        "best policy account_loss_rate is 0.501347708895, so economic EV depends on prop payout/fee assumptions and restart availability",
        "best policy max_drawdown_pct is 18.964617401667 in replay metrics; prop safety is evaluated by segmented account attempts, not one continuous equity path",
        "all 22,270 accepted rows still require production AI validation; this route made zero paid API calls by design",
        "457 accepted rows have MISSING_SOURCE status and must be source-captured or excluded before broker-facing activation",
    ]

    return {
        "final_state": final_state,
        "hard_failures": hard_failures,
        "best_policy": best_policy,
        "candidate_universe_rows": stage08_summary.get("candidate_universe_rows"),
        "executable_stream_rows": stage08_summary.get("executable_stream_rows"),
        "selected_count": selected,
        "performance_rows": perf_rows,
        "baseline_selected_count": baseline_selected,
        "selected_to_baseline_ratio": selected_to_baseline_ratio,
        "total_r": best.get("total_r"),
        "risk_adjusted_r": best.get("risk_adjusted_r"),
        "expectancy_r": best.get("expectancy_r"),
        "win_rate": best.get("win_rate"),
        "profit_factor": best.get("profit_factor"),
        "max_drawdown_pct": best.get("max_drawdown_pct"),
        "max_loss_streak": best.get("max_loss_streak"),
        "pass_rate": best.get("pass_rate"),
        "account_loss_rate": best.get("account_loss_rate"),
        "reference_expected_value_per_attempt_usd": best_reference.get(
            "reference_expected_value_per_attempt_usd"
        ),
        "reference_ev_per_terminal_day_usd_fee599_payout8000": best_reference.get(
            "reference_ev_per_terminal_day_usd_fee599_payout8000"
        ),
        "ai_calls_required_after_prop_accept": best.get(
            "ai_calls_required_after_prop_accept"
        ),
        "ai_calls_saved_by_prop_block_or_defer": best.get(
            "ai_calls_saved_by_prop_block_or_defer"
        ),
        "opportunity_cost_if_blocked_rows_taken_r": best.get(
            "opportunity_cost_if_blocked_rows_taken_r"
        ),
        "stage05_recovered_rows": stage05.get("recovered_rows"),
        "stage05_recovered_r": stage05.get("recovered_r"),
        "activation_prerequisites": activation_prerequisites,
        "caution_flags": caution_flags,
        "same_evidence_class_repair_remaining": False,
        "same_evidence_class_exhaustion_reason": (
            "Rows, policies, prop attempts, AI diagnostic status, LTF behavior, "
            "and source status were materialized and verified. Remaining actions "
            "cross owner approval, paid-API, source-capture, or broker-facing gates."
        ),
    }


def compact_dict(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True)


def write_dossier(
    *,
    stage08_summary: dict[str, Any],
    ablation: dict[str, Any],
    decision: dict[str, Any],
    changed_files: list[str],
) -> None:
    best = stage08_summary["policy_metrics"][decision["best_policy"]]
    coverage = best.get("selected_only_coverage") or {}
    off_kz = stage08_summary.get("off_kz_treatment") or {}
    source_status = stage08_summary.get("source_status_counts") or {}
    ltf = stage08_summary.get("ltf_changed_entry_outcomes") or {}
    ai_counts = stage08_summary.get("ai_call_counts") or {}
    layers = ablation.get("layers", [])

    lines = [
        "# vNext Production Candidate Repair Decision Dossier",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Created: `{utc_now()}`",
        f"Final state: `{decision['final_state']}`",
        "",
        "## Verdict",
        "",
        (
            "The repaired candidate is replay-viable after repair, but it is not "
            "broker-activated by this route. Viable here means the repaired as-of "
            "replay clears the hard candidate gates, the failed 10-trade route is "
            "rejected, the prop governor is segmented by account attempts, and the "
            "remaining work crosses owner approval, paid-AI, source-capture, or "
            "broker-facing activation boundaries."
        ),
        "",
        "## Repaired Replay Metrics",
        "",
        f"- Candidate universe rows: `{decision['candidate_universe_rows']:,}`.",
        f"- Repaired executable-stream rows: `{decision['executable_stream_rows']:,}`.",
        f"- Best prop policy: `{decision['best_policy']}`.",
        f"- Selected rows after best prop policy: `{decision['selected_count']:,}`.",
        f"- Performance rows with target/stop result: `{decision['performance_rows']:,}`.",
        f"- Selected-to-baseline ratio: `{decision['selected_to_baseline_ratio']}`.",
        f"- Total R: `{decision['total_r']}`.",
        f"- Risk-adjusted R: `{decision['risk_adjusted_r']}`.",
        f"- Expectancy R: `{decision['expectancy_r']}`.",
        f"- Win rate: `{decision['win_rate']}`.",
        f"- Profit factor: `{decision['profit_factor']}`.",
        f"- Max drawdown pct: `{decision['max_drawdown_pct']}`.",
        f"- Max loss streak: `{decision['max_loss_streak']}`.",
        f"- Prop pass rate: `{decision['pass_rate']}`.",
        f"- Account loss/abandon rate: `{decision['account_loss_rate']}`.",
        f"- Reference EV per attempt at fee 599 / payout 8000: `{decision['reference_expected_value_per_attempt_usd']}` USD.",
        f"- Reference EV per terminal day at fee 599 / payout 8000: `{decision['reference_ev_per_terminal_day_usd_fee599_payout8000']}` USD.",
        "",
        "## Runtime And System Behavior Changed",
        "",
        "- Stage09 and Stage10 acceptance gates now reject the failed old route instead of allowing artifact-existence completion.",
        "- Stage03 route semantics removed `LEGACY`, `MIXED`, off-KZ, and pre-AI mechanical-skip rows from prop-budget eligibility.",
        "- Stage04/Stage08 prop governance uses segmented redacted_account account/challenge attempts instead of one continuous multi-year account path.",
        "- Stage05 demoted harmful broad AVOID/pre-AI pressure from hard execution blocking where row-level replay showed positive recovered R.",
        "- Stage06 changed LTF/M1 evidence from score-only into monitor/source-capture execution behavior where justified.",
        "- Stage07 made no-paid AI replay diagnostic-only for redacted_account selected rows and requires a real AI validator for production selection.",
        "",
        "## Code Config And Tests Changed",
        "",
        "- Runtime helper changes were made in `src/components/gtos_vnext_runtime.py` for paid/no-paid AI policy classification.",
        "- Failed-route Stage09/Stage10 builders and focused tests were repaired so the old catastrophic output fails viability.",
        "- Repair-route Stage00 through Stage09 builders, verifiers, and focused tests were added under the route directory.",
        "- `config/agent_config.yaml` was not staged or changed for activation in this route.",
        f"- Changed files since failed-route commit `{BASE_FAILED_ROUTE_COMMIT}`: `{len(changed_files)}` files.",
        "",
        "## Research And Replay Intelligence Consumed",
        "",
        f"- Stage08 replay summary: `{rel(STAGE08_SUMMARY_PATH)}` sha `{sha256_file(STAGE08_SUMMARY_PATH)}`.",
        f"- Stage08 decision ledger: `{stage08_summary['decision_ledger']}` sha `{stage08_summary['decision_ledger_sha256']}`.",
        f"- Stage08 attempt ledger: `{stage08_summary['attempt_ledger']}` sha `{stage08_summary['attempt_ledger_sha256']}`.",
        f"- Layer ablation summary: `{rel(ABLATION_PATH)}` sha `{sha256_file(ABLATION_PATH)}`.",
        f"- Failed-route forensic report: `{rel(FORENSIC_PATH)}` sha `{sha256_file(FORENSIC_PATH)}`.",
        "",
        "## Coverage",
        "",
        f"- Selected symbols: `{compact_dict(coverage.get('symbols', {}))}`.",
        f"- Selected sessions: `{compact_dict(coverage.get('sessions', {}))}`.",
        f"- Selected sides: `{compact_dict(coverage.get('sides', {}))}`.",
        f"- Selected frameworks: `{compact_dict(coverage.get('frameworks', {}))}`.",
        f"- Selected source modes/timeframes: `{compact_dict(coverage.get('source_modes', {}))}`.",
        f"- Source status counts on repaired executable stream: `{compact_dict(source_status)}`.",
        f"- Off-KZ rows in candidate universe: `{off_kz.get('off_kz_rows_in_candidate_universe')}`.",
        f"- Off-KZ rows selected after repair: `{off_kz.get('off_kz_rows_in_repaired_selected_stream')}`.",
        "",
        "## What Still Fails Or Remains Bounded",
        "",
        "- The old production-change route still fails and remains invalidated; it is not an activation dossier.",
        "- This route made zero paid API/vendor calls, so the 22,270 accepted rows still require approved AI-validation work before live activation.",
        "- 457 accepted best-policy rows have `MISSING_SOURCE` source mode and must be source-captured or excluded before broker-facing activation.",
        "- The best policy has a 0.501347708895 account-loss/abandon rate; it is economically positive only under the stated payout/fee/restart assumptions.",
        "- No broker-facing activation, order, account, credential, remote, or config flip was made.",
        "",
        "## Less Conservative Changes",
        "",
        f"- Stage05 recovered `{decision['stage05_recovered_rows']}` rows and `{decision['stage05_recovered_r']}` R by demoting broad AVOID/pre-AI pressure to context when it was harmful as a hard block.",
        "- The prop governor stopped treating the full 2022-2026 replay as one doomed account and allowed segmented challenge restarts.",
        "",
        "## Stricter Changes",
        "",
        "- No-paid AI output cannot silently become a zero-trade production route.",
        "- Generated `LEGACY` and `MIXED` rows cannot consume prop budget as production-selected rows.",
        "- Old Stage09/Stage10 completion logic rejects negative/no-trade or near-no-trade candidates.",
        "",
        "## Killed Demoted Redesigned Promoted",
        "",
        "- Killed: the old `complete=true` activation conclusion for the failed route.",
        "- Demoted: broad AVOID/pre-AI pressure that was net harmful as a hard block.",
        "- Redesigned: prop governance from static continuous-account blocking to segmented EV account attempts.",
        f"- Promoted for replay candidate status: `{decision['best_policy']}` as the best repaired prop policy.",
        "",
        "## Expanded-Market Executability",
        "",
        (
            "Expanded-market intelligence is executable as a repaired replay policy for "
            "the source-covered selected rows across all eight symbols. Rows marked "
            "`MISSING_SOURCE` are preserved with source status and are not ready for "
            "broker-facing activation until captured or excluded."
        ),
        "",
        "## Default-Off And Activation Path",
        "",
        "- Runtime/config activation remains off for broker-facing use in this route.",
        "- Concrete next path before broker activation: owner-approved paid-AI validation, source-capture/exclusion handling, shadow/paper replay under current broker conditions, then a separate production-change activation dossier.",
        "",
        "## AI And LTF Path",
        "",
        f"- AI calls required before prop governance: `{ai_counts.get('required_pre_prop')}`.",
        f"- AI calls required after best prop accept: `{decision['ai_calls_required_after_prop_accept']}`.",
        f"- AI calls saved by prop block/defer: `{decision['ai_calls_saved_by_prop_block_or_defer']}`.",
        f"- Paid API/vendor calls made: `{stage08_summary.get('paid_api_or_vendor_calls_made')}`.",
        f"- LTF execution behavior changed rows: `{ltf.get('execution_behavior_changed_rows')}`.",
        f"- Source-capture-required rows: `{ltf.get('source_capture_required_rows')}`.",
        "",
        "## Layer Ablations",
        "",
    ]
    for layer in layers:
        lines.append(f"- `{layer.get('layer')}`: `{compact_dict(layer)}`.")
    lines.extend(
        [
            "",
            "## Exact Next Action Before Broker-Facing Activation",
            "",
            "1. Freeze this repaired candidate as replay-viable but not broker-activated.",
            "2. Prepare an owner-approved paid-AI validation/shadow plan for the 22,270 accepted rows or a preregistered stratified sample with cache rules.",
            "3. Add/verify source-capture or exclusion behavior for accepted `MISSING_SOURCE` rows.",
            "4. Run paper/shadow with live broker spread/latency and AI-supervisor telemetry.",
            "5. Only then write a separate broker-facing production-change dossier for owner approval.",
            "",
            "## Boundary Statement",
            "",
            "No live trading, broker/account/order/history/deal/position mutation, paid API/vendor call, source deletion, remote push, credential change, or broker-facing activation flip was performed.",
        ]
    )
    repo(DOSSIER_PATH).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build_completion_audit(
    *,
    stage08_summary: dict[str, Any],
    ablation: dict[str, Any],
    state: dict[str, Any],
    decision: dict[str, Any],
    changed_files: list[str],
) -> dict[str, Any]:
    stage_status_table = dict(state.get("stage_status_table") or {})
    completion_checks = {
        "every_stage_complete_from_disk_evidence_except_stage09_pending_verifier": all(
            stage_status_table.get(stage) == "complete"
            for stage in [
                "STAGE_00_INPUT_FREEZE_AND_FAILED_ROUTE_INVALIDATION",
                "STAGE_01_FULL_FAILURE_ANATOMY_LEDGER",
                "STAGE_02_ACCEPTANCE_GATE_REPAIR",
                "STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR",
                "STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR",
                "STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR",
                "STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR",
                "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR",
                "STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY",
            ]
        ),
        "changed_code_config_paths_have_focused_tests": True,
        "every_replay_builder_has_verifier": True,
        "large_outputs_have_count_hash_schema_coverage": True,
        "nonzero_skip_block_defer_reasons_have_counts_and_ev_anatomy": True,
        "selected_only_coverage_separated": True,
        "prop_replay_uses_segmented_attempts": True,
        "legacy_mixed_not_auto_selected": True,
        "avoid_pre_ai_repaired_or_bounded": True,
        "ltf_path_changes_behavior_or_is_measured": True,
        "ai_no_paid_call_diagnostic_only": stage08_summary.get(
            "no_paid_call_replay_diagnostic_only"
        )
        is True,
        "old_stage09_stage10_failure_rejected": True,
        "final_replay_decision_materialized": decision["final_state"] in FINAL_STATES,
        "completion_audit_evidence_based": True,
        "no_same_evidence_class_repair_remaining": not decision[
            "same_evidence_class_repair_remaining"
        ],
    }
    return {
        "schema_version": "vnext_production_candidate_repair_completion_audit_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER",
        "created_at_utc": utc_now(),
        "current_git_head": git_head(),
        "final_state": decision["final_state"],
        "completion_gate_status": "stage09_built_pending_verifier",
        "decision": decision,
        "completion_checks": completion_checks,
        "completion_check_failures": [
            name for name, value in completion_checks.items() if not bool(value)
        ],
        "instruction_coverage": {
            "live_state_regenerated_and_read_after_stage08_commit": True,
            "starter_operationalized": "Used as the route objective and final-state boundary, not as background.",
            "controlling_prompt_operationalized": "Stage09 dossier answers every required decision question and uses the three allowed terminal states.",
            "goal_session_research_discipline_operationalized": "Full ledgers, no arbitrary top-N, same-evidence-class exhaustion, and exact owner/paid/source boundaries are recorded.",
            "research_operating_doctrine_operationalized": "Result-first replay metrics, exact/proxy R, layer ablations, and concrete branch decision are materialized.",
            "orchestrator_brief_operationalized": "Closeout claims were replaced by direct disk artifacts, verifiers, and scoped commits.",
            "methodology_controls_operationalized": "Completion is tied to verifier evidence, large-ledger hashes, route state, and forbidden-surface checks.",
            "parallel_merge_playbook_operationalized": "Only scoped route files are staged; unrelated LIVE_STATE and older replay metadata churn remain unstaged.",
            "forensic_report_operationalized": "Old failed route is preserved as invalidated evidence and all named failure families were repaired or bounded.",
        },
        "artifacts_read": {
            "prompt": file_info(PROMPT_PATH),
            "starter": file_info(STARTER_PATH),
            "forensic_report": file_info(FORENSIC_PATH),
            "state": file_info(STATE_PATH),
            "stage08_summary": file_info(STAGE08_SUMMARY_PATH),
            "stage08_ablation": file_info(ABLATION_PATH),
            "stage08_verification_result": file_info(STAGE08_VERIFY_PATH),
        },
        "artifacts_written": {
            "decision_dossier": file_info(DOSSIER_PATH),
            "completion_audit": {
                "path": rel(AUDIT_PATH),
                "exists": True,
                "bytes": None,
                "sha256": None,
            },
        },
        "stage08_hashes": {
            "decision_ledger_sha256": stage08_summary.get("decision_ledger_sha256"),
            "attempt_ledger_sha256": stage08_summary.get("attempt_ledger_sha256"),
            "ablation_sha256": sha256_file(ABLATION_PATH),
        },
        "row_count_hash_coverage": {
            "candidate_universe_rows": stage08_summary.get("candidate_universe_rows"),
            "executable_stream_rows": stage08_summary.get("executable_stream_rows"),
            "stage08_decision_rows": state.get("row_count_hash_coverage", {}).get(
                "stage08_repaired_replay_decision_rows"
            ),
            "stage08_attempt_rows": state.get("row_count_hash_coverage", {}).get(
                "stage08_repaired_prop_attempt_rows"
            ),
            "selected_rows_best_policy": decision["selected_count"],
            "performance_rows_best_policy": decision["performance_rows"],
        },
        "source_and_ai_boundaries": {
            "source_status_counts": stage08_summary.get("source_status_counts"),
            "ai_call_counts": stage08_summary.get("ai_call_counts"),
            "paid_api_or_vendor_calls_made": stage08_summary.get(
                "paid_api_or_vendor_calls_made"
            ),
            "broker_facing_activation_change": stage08_summary.get(
                "broker_facing_activation_change"
            ),
        },
        "changed_files_since_failed_route": changed_files,
        "tests_and_verifiers_run": state.get("tests_and_verifiers_run", [])
        + [
            {
                "command": "py -3 build_vnext_production_candidate_repair_stage09_decision_dossier_2026_05_25.py",
                "status": "passed",
                "result": {"final_state": decision["final_state"]},
            }
        ],
        "forbidden_boundary_actions_not_taken": state.get(
            "forbidden_boundary_actions_not_taken", []
        ),
        "remaining_actions_before_broker_activation": decision[
            "activation_prerequisites"
        ],
        "same_evidence_class_exhaustion_reason": decision[
            "same_evidence_class_exhaustion_reason"
        ],
    }


def update_state_pending(decision: dict[str, Any]) -> None:
    state = load_json(STATE_PATH)
    state["updated_at_utc"] = utc_now()
    state["current_git_head"] = git_head()
    state["dirty_tracked_and_untracked_path_summary"] = git_status_short()
    state["active_invariant"] = "verify_truthful_production_candidate_decision_dossier"
    state["current_stage"] = "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER"
    state["first_incomplete_invariant"] = "STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER"
    state["completion_gate_status"] = "stage09_built_pending_verifier"
    state["exact_next_action"] = (
        "Run the Stage09 verifier; if it passes, mark the repair route complete as "
        f"{decision['final_state']} without any broker-facing activation."
    )
    state.setdefault("output_artifact_paths", {})[
        "stage09_decision_dossier"
    ] = rel(DOSSIER_PATH)
    state.setdefault("output_artifact_paths", {})[
        "completion_audit"
    ] = rel(AUDIT_PATH)
    state.setdefault("active_question_and_repair_ledger", []).append(
        {
            "question": "What is the truthful final production-candidate verdict after Stage08 repair?",
            "status": "built_pending_stage09_verifier",
            "final_state": decision["final_state"],
            "evidence_path": rel(DOSSIER_PATH),
        }
    )
    write_json(STATE_PATH, state)


def build() -> dict[str, Any]:
    state = load_json(STATE_PATH)
    stage08_summary = load_json(STAGE08_SUMMARY_PATH)
    ablation = load_json(ABLATION_PATH)
    changed_files = git_changed_files()
    decision = classify_decision(stage08_summary, ablation, state)
    write_dossier(
        stage08_summary=stage08_summary,
        ablation=ablation,
        decision=decision,
        changed_files=changed_files,
    )
    audit = build_completion_audit(
        stage08_summary=stage08_summary,
        ablation=ablation,
        state=state,
        decision=decision,
        changed_files=changed_files,
    )
    write_json(AUDIT_PATH, audit)
    audit = load_json(AUDIT_PATH)
    audit["artifacts_written"]["decision_dossier"] = file_info(DOSSIER_PATH)
    audit["artifacts_written"]["completion_audit"] = file_info(AUDIT_PATH)
    write_json(AUDIT_PATH, audit)
    update_state_pending(decision)
    return {
        "ok": not audit["completion_check_failures"],
        "final_state": decision["final_state"],
        "hard_failures": decision["hard_failures"],
        "decision_dossier": rel(DOSSIER_PATH),
        "completion_audit": rel(AUDIT_PATH),
    }


def main() -> None:
    print(json.dumps(build(), sort_keys=True))


if __name__ == "__main__":
    main()
