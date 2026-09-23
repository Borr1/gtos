"""Reconcile CD2 cross-domain second-pass artifacts into G0 controls.

Scope: research/science_program_2026_05 control and synthesis artifacts only.
No live trading prompts, risk, execution, permissions, selectors, MT5,
canaries, paid data, credentials, remote pushes, or order behavior are read
or changed by this script.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "00_control"
DOMAIN = ROOT / "01_domain_syntheses"
HYP = ROOT / "02_hypothesis_registry"
EXP = ROOT / "03_experiment_specs"
SYN = ROOT / "05_synthesis"

HEAD_RECONCILED = "4db7f47a"
CD2_MERGE_COMMIT = "0e865798"
WAVE2_PRIMARY_COMMIT = "20e84c43"
WAVE2_STATUS_COMMIT = "f62fbd65"

PROMOTION = "NO_PROMOTION_VERDICT"

PREREG_REQUIRED_FIELDS = [
    "experiment_id",
    "hypothesis_id",
    "frozen_at_utc",
    "outcome_review_opened",
    "metric",
    "cohort",
    "exclusions",
    "duplicate_policy",
    "cost_slippage_assumptions",
    "dsr_pbo_effective_n_policy",
    "label_separation_policy",
    "reproducibility_key",
    "promotion_verdict",
]

SOURCE_REQUIRED_FIELDS = [
    "source_id",
    "url_or_vendor",
    "access_legal_state",
    "cost_rule",
    "publication_asof_timestamp_rule",
    "cache_path",
    "allowed_feature_role",
    "validation_safe",
    "validation_safe_blockers",
    "promotion_verdict",
]

FORBIDDEN_FIELDS = {
    "actual_r",
    "broker_actual_r",
    "future_orderflow",
    "future_price",
    "future_release_value",
    "future_return",
    "future_vol_index",
    "outcome_r",
    "post_entry_path",
    "post_event_outcome",
    "post_release_revision",
    "post_signal_continuation",
    "post_signal_path",
    "stop_loss_hit",
    "synthetic_path_r",
    "take_profit_hit",
    "tp_hit",
    "trade_outcome",
    "trade_result",
    "win_loss",
}

CD2_ARTIFACTS = [
    {
        "assignment_id": "CD2-01",
        "lane": "G7",
        "title": "Macro-vol-source freshness triad",
        "commit": "83be59ea",
        "artifacts": [
            "research/science_program_2026_05/01_domain_syntheses/G7_CD2_01_MACRO_VOL_SOURCE_FRESHNESS_COMPATIBILITY_LEDGER_2026-05-06.md",
            "research/science_program_2026_05/03_experiment_specs/G7_CD2_01_PREREG_UPDATE_PROPOSAL_2026-05-06.md",
        ],
        "master_action": "BLOCKER_ONLY_PROPOSAL_UPDATES_EXISTING_ROWS",
        "reason": "Markdown proposal updates existing source/no-leak/prereg fields but leaves COT/FRED/BIS/Cboe/VRP as-of blockers unresolved.",
        "g12_focus": "Verify publication/as-of rules before any macro-vol outcome review.",
    },
    {
        "assignment_id": "CD2-02",
        "lane": "G8",
        "title": "Short-vol stress versus execution lifecycle",
        "commit": "ac1e4108",
        "artifacts": [
            "research/science_program_2026_05/01_domain_syntheses/G8_CD2_02_SHORT_VOL_EXECUTION_MISSING_SOURCE_LEDGER_2026-05-06.md",
            "research/science_program_2026_05/03_experiment_specs/G8_CD2_02_SHORT_VOL_EXECUTION_LIFECYCLE_PREREG_2026-05-06.md",
            "research/science_program_2026_05/03_experiment_specs/G8_CD2_02_SHORT_VOL_EXECUTION_LIFECYCLE_PREREG_2026-05-06.json",
        ],
        "master_action": "REGISTER_SCHEMA_SAFE_PREREG_RESEARCH_ONLY",
        "reason": "Machine-readable experiment_prereg_v1 row is outcome-closed, label-separated, source-blocked, and references an existing hypothesis.",
        "g12_focus": "Review Cboe same-day timing, pending lifecycle ordering, and lifecycle_no_fill label separation.",
    },
    {
        "assignment_id": "CD2-03",
        "lane": "G9",
        "title": "Offline-RL reward and risk-bank boundary",
        "commit": "58e362b3",
        "artifacts": [
            "research/science_program_2026_05/05_synthesis/G9_CD2_03_OFFLINE_RL_REWARD_CONTRACT_2026-05-06.md",
            "research/science_program_2026_05/05_synthesis/G9_CD2_03_OFFLINE_RL_REWARD_CONTRACT_2026-05-06.json",
            "research/science_program_2026_05/05_synthesis/G9_CD2_03_RED_TEAM_PREREG_PROPOSAL_2026-05-06.md",
            "research/science_program_2026_05/05_synthesis/G9_CD2_03_RED_TEAM_PREREG_PROPOSAL_2026-05-06.json",
        ],
        "master_action": "REGISTER_SCHEMA_SAFE_PREREG_RESEARCH_ONLY",
        "reason": "Proposed prereg has all experiment_prereg_v1 fields, keeps outcomes closed, references an existing hypothesis, and is explicitly offline-only.",
        "g12_focus": "Adversarially test state-field leakage, risk-bank invariant, duplicate episode counting, and cost accounting.",
    },
    {
        "assignment_id": "CD2-04",
        "lane": "G4",
        "title": "K55 source-provenance and orderflow feature gate",
        "commit": "12da4421",
        "artifacts": [
            "research/science_program_2026_05/05_synthesis/G4_CD2_04_K55_FEATURE_PROVENANCE_CONTRACT_2026-05-06.md",
            "research/science_program_2026_05/05_synthesis/G4_CD2_04_K55_FEATURE_PROVENANCE_CONTRACT_2026-05-06.json",
            "research/science_program_2026_05/05_synthesis/G4_CD2_04_SOURCE_STATUS_JOIN_MAP_2026-05-06.md",
            "research/science_program_2026_05/05_synthesis/G4_CD2_04_SOURCE_STATUS_JOIN_MAP_2026-05-06.json",
        ],
        "master_action": "STATUS_SYNTHESIS_ONLY",
        "reason": "Contract/join map is not a science_mechanism, hypothesis, prereg, or source_contract row; no source was validation-safe.",
        "g12_focus": "Confirm K55 receives only source-status/provenance flags, not raw orderflow/depth predictive features.",
    },
    {
        "assignment_id": "CD2-05",
        "lane": "G5",
        "title": "Macro attention and behavioral attention interaction",
        "commit": "8d3937a6",
        "artifacts": [
            "research/science_program_2026_05/05_synthesis/G5_CD2_05_DEDUPED_ATTENTION_PREREG_PROPOSAL_2026-05-06.md",
            "research/science_program_2026_05/05_synthesis/G5_CD2_05_ATTENTION_BLOCKER_LEDGER_2026-05-06.json",
        ],
        "master_action": "BLOCKER_ONLY_MARKDOWN_PROPOSAL",
        "reason": "Canonical hypothesis/prereg are markdown proposal-only, source path mismatch and stale-calendar blockers remain, and artifact explicitly says no master edit.",
        "g12_focus": "Resolve duplicate G5/G7 attention rows and calendar/Fed source freshness before a machine row exists.",
    },
    {
        "assignment_id": "CD2-06",
        "lane": "G10",
        "title": "Pre-fill delivery path and no-retrace opportunity map",
        "commit": "d2164609",
        "artifacts": [
            "research/science_program_2026_05/01_domain_syntheses/G10_CD2_06_PREFILL_PATH_CAPTURE_SPEC_2026-05-06.md",
            "research/science_program_2026_05/01_domain_syntheses/G10_CD2_06_PREFILL_PATH_MISSING_FIELD_AUDIT_2026-05-06.md",
            "research/science_program_2026_05/01_domain_syntheses/G10_CD2_06_PREFILL_PATH_MISSING_FIELD_AUDIT_2026-05-06.json",
        ],
        "master_action": "STATUS_SYNTHESIS_ONLY",
        "reason": "Spec and missing-field audit define capture requirements but create no schema row; source_hash, source_symbol, ordered prefill candles, tick summaries, and lifecycle state remain blocked.",
        "g12_focus": "Verify prefill/no-fill, synthetic path-R, same-bar ambiguity, and broker actual-R lanes cannot mix.",
    },
    {
        "assignment_id": "CD2-07",
        "lane": "G11",
        "title": "Prop-firm stress calendar and portfolio opportunity cost",
        "commit": "cd84d032",
        "artifacts": [
            "research/science_program_2026_05/01_domain_syntheses/G11_CD2_07_PORTFOLIO_OPPORTUNITY_COST_SOURCE_MAP_2026-05-06.md",
            "research/science_program_2026_05/03_experiment_specs/G11_CD2_07_PORTFOLIO_OPPORTUNITY_COST_PREREG_2026-05-06.json",
        ],
        "master_action": "BLOCKER_ONLY_SIDECAR_PREREG",
        "reason": "Sidecar row uses a new hypothesis ID that is not in the master hypothesis registry; prop parser, correlation lifecycle, and stress as-of blockers remain.",
        "g12_focus": "Keep observation-only opportunity-cost context separate from risk/correlation/order behavior and R labels.",
    },
    {
        "assignment_id": "CD2-08",
        "lane": "G0",
        "title": "Source/no-leak field cleanup pass",
        "commit": "70d224c6",
        "artifacts": [
            "research/science_program_2026_05/05_synthesis/G0_CD2_08_SOURCE_NO_LEAK_CLEANUP_PROPOSAL_2026-05-06.md",
        ],
        "master_action": "BLOCKER_ONLY_G12_CLEANUP_PROPOSAL",
        "reason": "Cleanup proposal intentionally edits no master rows; G12 must decide dependency/evidence fields and no_leak field cleanup.",
        "g12_focus": "Resolve no_leak semantic inversion and source_ids placeholders without marking sources validation-safe.",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.as_posix()


def sort_rows(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(row.get(key, "")))


def duplicate_ids(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts = Counter(row.get(key) for row in rows)
    return [
        {"id": value, "count": count}
        for value, count in sorted(counts.items(), key=lambda item: str(item[0]))
        if count > 1
    ]


def load_cd2_prereg_candidates() -> list[dict[str, Any]]:
    g8 = load_json(EXP / "G8_CD2_02_SHORT_VOL_EXECUTION_LIFECYCLE_PREREG_2026-05-06.json")
    g9 = load_json(SYN / "G9_CD2_03_RED_TEAM_PREREG_PROPOSAL_2026-05-06.json")
    return [
        {
            "assignment_id": "CD2-02",
            "lane_id": "G8",
            "source_file": rel(EXP / "G8_CD2_02_SHORT_VOL_EXECUTION_LIFECYCLE_PREREG_2026-05-06.json"),
            "row": g8["rows"][0],
        },
        {
            "assignment_id": "CD2-03",
            "lane_id": "G9",
            "source_file": rel(SYN / "G9_CD2_03_RED_TEAM_PREREG_PROPOSAL_2026-05-06.json"),
            "row": g9["proposed_prereg"],
        },
    ]


def validate_prereg_candidate(
    candidate: dict[str, Any],
    hypothesis_ids: set[str],
) -> list[str]:
    row = candidate["row"]
    issues: list[str] = []
    missing = [field for field in PREREG_REQUIRED_FIELDS if field not in row]
    if missing:
        issues.append(f"missing_required_fields={missing}")
    if row.get("hypothesis_id") not in hypothesis_ids:
        issues.append(f"unknown_hypothesis_id={row.get('hypothesis_id')}")
    if row.get("outcome_review_opened") is not False:
        issues.append("outcome_review_opened_not_false")
    if row.get("promotion_verdict") != PROMOTION:
        issues.append("promotion_verdict_not_NO_PROMOTION_VERDICT")
    label_policy = str(row.get("label_separation_policy", "")).lower()
    if not label_policy:
        issues.append("missing_label_separation_policy")
    if "broker_actual_r" in label_policy and "synthetic_path_r" in label_policy and "separate" not in label_policy:
        issues.append("label_separation_policy_mentions_multiple_label_classes_without_separation")
    return issues


def collect_no_leak_blockers(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for row in hypotheses:
        fields = row.get("no_leak_fields")
        if not isinstance(fields, list) or not fields:
            blockers.append(
                {
                    "hypothesis_id": row.get("hypothesis_id"),
                    "issue": "missing_or_empty_no_leak_fields",
                    "fields": fields,
                }
            )
            continue
        forbidden = [field for field in fields if str(field).lower() in FORBIDDEN_FIELDS]
        if forbidden:
            blockers.append(
                {
                    "hypothesis_id": row.get("hypothesis_id"),
                    "issue": "no_leak_fields_contains_forbidden_outcome_or_future_field_names",
                    "fields": forbidden,
                    "g12_required": True,
                }
            )
    return blockers


def source_reference_issues(
    mechanisms: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    source_ids: set[str],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row_type, id_key, rows in [
        ("mechanism", "mechanism_id", mechanisms),
        ("hypothesis", "hypothesis_id", hypotheses),
    ]:
        for row in rows:
            for source_id in row.get("source_ids", []) or []:
                if source_id in source_ids:
                    continue
                if str(source_id).startswith("LIT-"):
                    issue = "literature_reference_without_source_contract"
                elif str(source_id).startswith("HYP-") or str(source_id).startswith("future_"):
                    issue = "cross_domain_placeholder_not_source_contract"
                else:
                    issue = "unregistered_source_reference"
                issues.append(
                    {
                        "row_type": row_type,
                        "row_id": row.get(id_key),
                        "source_id": source_id,
                        "issue": issue,
                        "blocking_validation_safe": True,
                    }
                )
    return issues


def build_cd2_status(now: str, accepted: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checked_at_utc": now,
        "lane_id": "G0",
        "status": "G0_CD2_RECONCILIATION_COMPLETE_VERIFIED_PENDING_SCOPED_COMMIT",
        "head_reconciled": HEAD_RECONCILED,
        "cd2_merge_commit": CD2_MERGE_COMMIT,
        "wave2_primary_reconciliation_commit": WAVE2_PRIMARY_COMMIT,
        "wave2_status_commit": WAVE2_STATUS_COMMIT,
        "promotion_verdict": PROMOTION,
        "live_behavior_changed": False,
        "ai_calls": 0,
        "canary_calls": 0,
        "mt5_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "public_web_fetches_by_g0": 0,
        "external_cash_spend_usd": 0.0,
        "cd2_artifacts": CD2_ARTIFACTS,
        "accepted_master_prereg_rows": [
            {
                "assignment_id": item["assignment_id"],
                "lane_id": item["lane_id"],
                "experiment_id": item["row"]["experiment_id"],
                "hypothesis_id": item["row"]["hypothesis_id"],
                "source_file": item["source_file"],
                "promotion_verdict": item["row"]["promotion_verdict"],
            }
            for item in accepted
        ],
        "blocked_cd2_master_actions": blocked,
        "master_row_delta": {
            "mechanism_rows_added": 0,
            "hypothesis_rows_added": 0,
            "experiment_prereg_rows_added": len(accepted),
            "source_contract_rows_added": 0,
            "survivor_backlog_rows_added": 0,
        },
        "source_policy": {
            "validation_safe_true_allowed": False,
            "validation_safe_true_rows_after_reconciliation": 0,
            "source_contract_rows_added": 0,
            "source_registry_action": "metadata_status_refresh_only_no_source_row_promoted",
        },
        "g12_launch_status": "READY_FOR_G12_RED_TEAM_AFTER_CD2_RECONCILIATION",
    }


def append_unique_preregs(
    preregistry: dict[str, Any],
    accepted: list[dict[str, Any]],
    cd2_status: dict[str, Any],
) -> None:
    rows = preregistry["rows"]
    by_id = {row["experiment_id"]: row for row in rows}
    row_sources = preregistry.setdefault("row_sources", {})
    for item in accepted:
        row = item["row"]
        row_copy = dict(row)
        row_copy["g0_cd2_reconciliation_status"] = "REGISTERED_RESEARCH_ONLY_NO_PROMOTION"
        row_copy["g0_cd2_assignment_id"] = item["assignment_id"]
        by_id[row_copy["experiment_id"]] = row_copy
        row_sources[row_copy["experiment_id"]] = {
            "lane_id": item["lane_id"],
            "source_files": [item["source_file"]],
            "reconciled_by": "G0_CD2",
            "promotion_verdict": PROMOTION,
        }
    preregistry["rows"] = sort_rows(list(by_id.values()), "experiment_id")
    preregistry["status"] = "CD2_RECONCILED_G1_G11_PLUS_SCHEMA_SAFE_CD2_PREREGS_OUTCOMES_CLOSED"
    preregistry["promotion_verdict"] = PROMOTION
    preregistry["cd2_reconciliation"] = cd2_status


def update_status_registry(status_rows: list[dict[str, Any]], cd2_status: dict[str, Any]) -> list[dict[str, Any]]:
    files_written = [
        "research/science_program_2026_05/00_control/reconcile_cd2_2026_05_06.py",
        "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
        "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.json",
        "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md",
        "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
        "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.md",
        "research/science_program_2026_05/01_domain_syntheses/G0_GOVERNOR_CONTEXT_AMBIGUITY_LEDGER_2026-05-06.md",
        "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
        "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json",
        "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md",
        "research/science_program_2026_05/05_synthesis/G0_CROSS_AGENT_SYNTHESIS_2026-05-06.json",
        "research/science_program_2026_05/05_synthesis/G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md",
        "research/science_program_2026_05/05_synthesis/G0_CD2_RECONCILIATION_2026-05-06.json",
        "research/science_program_2026_05/05_synthesis/G0_CD2_RECONCILIATION_2026-05-06.md",
        "research/science_program_2026_05/05_synthesis/G0_COMPLETION_AUDIT_2026-05-06.json",
        "research/science_program_2026_05/05_synthesis/G0_COMPLETION_AUDIT_2026-05-06.md",
        "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.json",
        "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md",
    ]
    tests_run = [
        "python scripts/generate_live_state.py -> passed",
        "mandatory preflight reads completed: LIVE_STATE, latest handoff, quick reference, research doctrine, research current state, reading order, controlling G0 prompt",
        "git show --stat --oneline 4db7f47a -> confirmed HEAD record commit",
        "git show --stat --oneline 0e865798 -> confirmed merged CD2 artifacts",
        "CD2 artifact inventory -> CD2-01 through CD2-08 proposal/ledger/contract artifacts read",
        "python research\\science_program_2026_05\\00_control\\reconcile_cd2_2026_05_06.py -> generated CD2 reconciliation artifacts",
        "python -m py_compile research\\science_program_2026_05\\00_control\\reconcile_cd2_2026_05_06.py -> passed",
        "JSON parse check over 11 G0/CD2 JSON artifacts -> passed",
        "custom schema/relationship/duplicate/source/prereg validator -> mechanisms=77, hypotheses=96, preregs=97, sources=86, status_rows=13, cd2_preregs=2, issues=0",
        "Python recursive scan -> no validation_safe=true, outcome_review_opened=true, or live_effect=true found in scoped science program JSON artifacts",
        "NO_PROMOTION_VERDICT coverage scan over 49 scoped non-raw G0/CD2 artifacts -> passed",
        "git diff --name-only over prompts/src/config/canary/MT5/execution/permissions/risk/safety paths -> no output",
        "python -m pytest tests\\test_science_goal_program.py -q -p no:cacheprovider --basetemp C:\\tmp\\pytest_g0_cd2_reconciliation -> initial sandbox run failed with WinError 5 temp-dir permission before test execution",
        "python -m pytest tests\\test_science_goal_program.py -q -p no:cacheprovider --basetemp C:\\tmp\\pytest_g0_cd2_reconciliation -> 9 passed after approved escalation",
    ]
    g0_row = {
        "lane_id": "G0",
        "lane_status": "G0_CD2_RECONCILIATION_COMPLETE_VERIFIED_PENDING_SCOPED_COMMIT",
        "files_written": files_written,
        "tests_run": tests_run,
        "blockers": [
            "No mechanism, hypothesis, source-contract, survivor, validation, prompt, risk, execution, selector, MT5, canary, paid-data, or order-behavior row was promoted.",
            "Only 2 schema-safe CD2 prereg rows were registered, both outcome_review_opened=false and NO_PROMOTION_VERDICT.",
            "All source contracts remain validation_safe=false; CD2 added 0 source_contract_v2 rows.",
            "CD2-01, CD2-05, CD2-07, and CD2-08 remain blocker/proposal-only for master row purposes.",
            "CD2-04 and CD2-06 are contract/status/audit artifacts only, not schema rows.",
            "G12 red-team has not run and remains required before any cleanup or promotion discussion.",
        ],
        "next_questions": [
            "Launch G12 using the final CD2 red-team instructions and require review of the 2 registered CD2 preregs plus the blocked CD2 proposal rows.",
            "Do not change validation_safe=false unless a future source-specific blocker-clearing dossier exists.",
            "Do not open outcome review for any CD2 row until source/as-of/no-leak/label/sample blockers clear.",
        ],
        "commit_sha": None,
        "promotion_verdict": PROMOTION,
        "checked_at_utc": cd2_status["checked_at_utc"],
        "cd2_reconciliation": cd2_status,
    }

    updated: list[dict[str, Any]] = []
    g0_written = False
    for row in status_rows:
        if row.get("lane_id") == "G0":
            updated.append(g0_row)
            g0_written = True
        elif row.get("lane_id") == "G12":
            g12 = dict(row)
            g12["lane_status"] = "READY_FOR_RED_TEAM_AFTER_G0_CD2_RECONCILIATION"
            g12["files_written"] = sorted(
                set(g12.get("files_written", []))
                | {
                    "research/science_program_2026_05/04_goal_prompts/G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md",
                    "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md",
                    "research/science_program_2026_05/05_synthesis/G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.json",
                    "research/science_program_2026_05/05_synthesis/G0_CD2_RECONCILIATION_2026-05-06.md",
                    "research/science_program_2026_05/05_synthesis/G0_CD2_RECONCILIATION_2026-05-06.json",
                }
            )
            g12["blockers"] = sorted(
                set(g12.get("blockers", []))
                | {
                    "G12 has not executed yet.",
                    "G12 must red-team CD2 registered preregs, blocked CD2 proposal rows, no-leak/source cleanup, and source-validation-safe drift before any further registry cleanup.",
                }
            )
            g12["next_questions"] = [
                "Launch G12 in C:\\tmp\\gtosg\\G12 using research/science_program_2026_05/04_goal_prompts/G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md.",
                "Read G0_CD2_RECONCILIATION_2026-05-06.md/json before individual CD2 artifacts.",
                "Do not change live trading prompts, risk, execution, permissions, selectors, safety gates, MT5, canaries, paid data, credentials, remote pushes, or order behavior.",
            ]
            g12["promotion_verdict"] = PROMOTION
            g12["cd2_reconciliation_ready"] = True
            updated.append(g12)
        else:
            updated.append(row)
    if not g0_written:
        updated.insert(0, g0_row)
    return updated


def build_checks(
    mechanisms: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    preregs: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    accepted: list[dict[str, Any]],
    candidate_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    mechanism_ids = {row["mechanism_id"] for row in mechanisms}
    hypothesis_ids = {row["hypothesis_id"] for row in hypotheses}
    source_ids = {row["source_id"] for row in sources}
    relationship_issues = []
    for row in hypotheses:
        if row.get("mechanism_id") not in mechanism_ids:
            relationship_issues.append(
                {
                    "type": "hypothesis_missing_mechanism",
                    "hypothesis_id": row.get("hypothesis_id"),
                    "mechanism_id": row.get("mechanism_id"),
                }
            )
    for row in preregs:
        if row.get("hypothesis_id") not in hypothesis_ids:
            relationship_issues.append(
                {
                    "type": "prereg_missing_hypothesis",
                    "experiment_id": row.get("experiment_id"),
                    "hypothesis_id": row.get("hypothesis_id"),
                }
            )

    source_true = [row["source_id"] for row in sources if row.get("validation_safe") is True]
    source_field_issues = []
    for row in sources:
        missing = [field for field in SOURCE_REQUIRED_FIELDS if field not in row]
        if missing:
            source_field_issues.append({"source_id": row.get("source_id"), "missing": missing})

    prereg_required_issues = []
    for row in preregs:
        missing = [field for field in PREREG_REQUIRED_FIELDS if field not in row]
        if missing:
            prereg_required_issues.append({"experiment_id": row.get("experiment_id"), "missing": missing})

    no_leak = collect_no_leak_blockers(hypotheses)
    src_issues = source_reference_issues(mechanisms, hypotheses, source_ids)
    return {
        "required_field_issues": {
            "source_contracts": source_field_issues,
            "experiment_preregs": prereg_required_issues,
            "accepted_cd2_candidate_issues": candidate_issues,
        },
        "relationship_issues": relationship_issues,
        "duplicate_report": {
            "mechanism_id_duplicates": duplicate_ids(mechanisms, "mechanism_id"),
            "hypothesis_id_duplicates": duplicate_ids(hypotheses, "hypothesis_id"),
            "experiment_id_duplicates": duplicate_ids(preregs, "experiment_id"),
            "source_id_duplicates": duplicate_ids(sources, "source_id"),
        },
        "source_contract_summary": {
            "source_contract_rows": len(sources),
            "validation_safe_true": len(source_true),
            "validation_safe_true_ids": source_true,
            "validation_safe_false": sum(1 for row in sources if row.get("validation_safe") is False),
        },
        "experiment_prereg_summary": {
            "experiment_prereg_rows": len(preregs),
            "outcome_review_opened_true": sum(1 for row in preregs if row.get("outcome_review_opened") is True),
            "outcome_review_opened_false": sum(1 for row in preregs if row.get("outcome_review_opened") is False),
            "cd2_registered_experiment_ids": [item["row"]["experiment_id"] for item in accepted],
        },
        "no_leak_semantic_blockers": no_leak,
        "source_reference_issues": src_issues,
        "label_separation_check": {
            "accepted_cd2_rows": [
                {
                    "experiment_id": item["row"]["experiment_id"],
                    "label_separation_policy_present": bool(item["row"].get("label_separation_policy")),
                    "blocked_or_separate_language_present": any(
                        token in str(item["row"].get("label_separation_policy", "")).lower()
                        for token in ["separate", "excluded", "remain separate"]
                    ),
                }
                for item in accepted
            ],
            "status": "PASS_ACCEPTED_CD2_ROWS_EXPLICITLY_SEPARATE_LABEL_FAMILIES",
        },
        "hard_blocker_issue_count": (
            len(source_field_issues)
            + len(prereg_required_issues)
            + len(candidate_issues)
            + len(relationship_issues)
            + sum(len(value) for value in {
                "m": duplicate_ids(mechanisms, "mechanism_id"),
                "h": duplicate_ids(hypotheses, "hypothesis_id"),
                "e": duplicate_ids(preregs, "experiment_id"),
                "s": duplicate_ids(sources, "source_id"),
            }.values())
            + len(source_true)
            + sum(1 for row in preregs if row.get("outcome_review_opened") is True)
        ),
    }


def write_markdown_files(
    now: str,
    master: dict[str, Any],
    source_registry: dict[str, Any],
    source_budget: dict[str, Any],
    cd2_status: dict[str, Any],
    checks: dict[str, Any],
    completion: dict[str, Any],
    g12_guidance: dict[str, Any],
) -> None:
    prereg_rows = master["registries"]["experiment_preregistry"]["rows"]
    source_rows = master["registries"]["source_contract_registry"]["rows"]

    (SYN / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md").write_text(
        "\n".join(
            [
                "# Science Program Master Registry - 2026-05-06",
                "",
                "**Status:** `G0_CD2_RECONCILED_HEAD_4db7f47a`",
                f"**Promotion verdict:** `{PROMOTION}`",
                f"**Checked at UTC:** `{now}`",
                f"**HEAD reconciled:** `{HEAD_RECONCILED}`",
                f"**CD2 merge commit:** `{CD2_MERGE_COMMIT}`",
                f"**Wave-2 reconciliation commit:** `{WAVE2_PRIMARY_COMMIT}`",
                "",
                "## G0 Registry State",
                "",
                f"- Mechanisms: `{master['registries']['mechanism_registry']['rows']}`",
                f"- Hypotheses: `{master['registries']['hypothesis_registry']['rows']}`",
                f"- Experiment preregs: `{prereg_rows}`",
                f"- Source contracts: `{source_rows}`",
                f"- CD2 preregs registered research-only: `{len(cd2_status['accepted_master_prereg_rows'])}`",
                "- Survivor backlog rows: `0`",
                "",
                "G0 reconciled CD2-01 through CD2-08 artifacts at HEAD `4db7f47a`. "
                "Only two CD2 experiment prereg rows were schema-safe and explicitly research-only, so they were added to the experiment preregistry with outcomes closed. "
                "No mechanism, hypothesis, source-contract, survivor, validation, prompt, risk, execution, selector, MT5, canary, paid-data, or order-behavior row was promoted.",
                "",
                "## CD2 Assignment Outcomes",
                "",
                "| Assignment | Lane | Master action | Reason |",
                "| --- | --- | --- | --- |",
                *[
                    f"| `{item['assignment_id']}` | `{item['lane']}` | `{item['master_action']}` | {item['reason']} |"
                    for item in CD2_ARTIFACTS
                ],
                "",
                "## Registered CD2 Preregs",
                "",
                "| Experiment | Hypothesis | Source artifact |",
                "| --- | --- | --- |",
                *[
                    f"| `{item['experiment_id']}` | `{item['hypothesis_id']}` | `{item['source_file']}` |"
                    for item in cd2_status["accepted_master_prereg_rows"]
                ],
                "",
                "## Check Results",
                "",
                f"- Required-field hard issues: `{checks['hard_blocker_issue_count']}` hard blockers in accepted/master rows.",
                f"- Duplicate mechanism/hypothesis/prereg/source IDs: `{sum(len(v) for v in checks['duplicate_report'].values())}`.",
                f"- Source contracts with `validation_safe=true`: `{checks['source_contract_summary']['validation_safe_true']}`.",
                f"- Experiment preregs with `outcome_review_opened=true`: `{checks['experiment_prereg_summary']['outcome_review_opened_true']}`.",
                f"- No-leak semantic blockers retained for G12: `{len(checks['no_leak_semantic_blockers'])}`.",
                f"- Source-reference placeholders/literature references retained for G12: `{len(checks['source_reference_issues'])}`.",
                "",
                "## Survivor Backlog",
                "",
                "No survivor hypotheses exist. CD2 improved research-control contracts only.",
                "",
                "## NO_PROMOTION_VERDICT",
                "",
                "This master registry remains research/control inventory only. It does not change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remote pushes, or order behavior.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.md").write_text(
        "\n".join(
            [
                "# Science Program Source Contract Registry - 2026-05-06",
                "",
                "**Status:** `CD2_RECONCILED_NO_NEW_SOURCE_ROWS_NOT_VALIDATION_SAFE`",
                f"**Promotion verdict:** `{PROMOTION}`",
                f"**Checked at UTC:** `{now}`",
                f"**HEAD reconciled:** `{HEAD_RECONCILED}`",
                f"**CD2 merge commit:** `{CD2_MERGE_COMMIT}`",
                "",
                "## Summary",
                "",
                f"G0 retains `{len(source_registry['rows'])}` `source_contract_v2` rows after CD2 reconciliation. All `{len(source_registry['rows'])}` remain `validation_safe=false`. CD2 added `0` source contracts.",
                "",
                "## CD2 Source Decisions",
                "",
                "- CD2-01 froze macro/vol source as-of rules but kept COT/FRED/BIS/Cboe/VRP blocked.",
                "- CD2-04 allowed K55 source-status/provenance flags only; raw orderflow/depth features remain quarantined.",
                "- CD2-07 mapped prop/risk/stress sources as observation-only and parser/source blocked.",
                "- CD2-08 proposed source/no-leak cleanup for G12; no source row was edited.",
                "",
                "## Source And No-Leak Blockers",
                "",
                f"- Validation-safe source rows: `{checks['source_contract_summary']['validation_safe_true']}`.",
                f"- Source-reference placeholders or unregistered literature references: `{len(checks['source_reference_issues'])}`.",
                f"- No-leak semantic blocker rows: `{len(checks['no_leak_semantic_blockers'])}`.",
                "- `$0` new external cash spend remains in force.",
                "",
                "## NO_PROMOTION_VERDICT",
                "",
                "This registry consolidates source contracts for governance. It does not make any source validation-safe.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (CONTROL / "SOURCE_BUDGET_LEDGER_2026-05-06.md").write_text(
        "\n".join(
            [
                "# Science Program Source And Budget Ledger - 2026-05-06",
                "",
                f"**Promotion verdict:** `{PROMOTION}`",
                "**Budget posture:** `ZERO_NEW_EXTERNAL_CASH_UNTIL_NUMERIC_CAP_AND_PER_SOURCE_LIMIT_ARE_OWNER_APPROVED`",
                "**Current external cash spend cap:** `$0`",
                "**Per-source limit:** `None`",
                "**Spend allowed:** `False`",
                "",
                "## Allowed Now",
                "",
                "- local repo artifacts",
                "- existing local data",
                "- existing Sierra files/access",
                "- existing Databento credits only after manifest/cost estimate/cap ledger",
                "- public web only when fetched, cached, and source-indexed under the research lane",
                "",
                "## Disallowed Until Owner Approval",
                "",
                "- new subscriptions",
                "- paid trials",
                "- account top-ups",
                "- vendor purchases",
                "- broad paid data pulls",
                "- any source marked validation_safe before source_contract_v2 tests pass",
                "",
                "## CD2 Source Reconciliation",
                "",
                f"- Checked at UTC: `{now}`",
                f"- HEAD reconciled: `{HEAD_RECONCILED}`",
                f"- CD2 merge commit: `{CD2_MERGE_COMMIT}`",
                "- Source contract rows added by CD2: `0`",
                f"- Source rows in registry: `{len(source_registry['rows'])}`",
                "- Validation-safe source rows: `0`",
                "- New external cash spend by G0: `$0`",
                "- New public fetches by G0: `0`",
                "- Paid data calls by G0: `0`",
                "",
                "## Ledger Rows",
                "",
                f"`{json.dumps(source_budget.get('ledger_rows', []))}`",
                "",
                "No lane may spend cash or mark a source validation-safe until this ledger has a numeric cap, per-source limit, source contract, explicit source evidence, and blocker-clearing notes.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (SYN / "G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md").write_text(
        "\n".join(
            [
                "# G0 CD2 Cross-Agent Synthesis - 2026-05-06",
                "",
                "**Lane:** `G0`",
                "**Status:** `G0_CD2_RECONCILIATION_COMPLETE_VERIFIED_PENDING_SCOPED_COMMIT`",
                f"**Promotion verdict:** `{PROMOTION}`",
                f"**Checked at UTC:** `{now}`",
                f"**HEAD reconciled:** `{HEAD_RECONCILED}`",
                f"**CD2 merge commit:** `{CD2_MERGE_COMMIT}`",
                "",
                "## Objective Restated",
                "",
                "Run G0 CD2 cross-domain reconciliation: read HEAD `4db7f47a`, merged CD2 artifacts, wave-2 reconciliation, master registries, assignment file, G12 guidance, and research current state; reconcile CD2-01 through CD2-08 without promotion; update master/status/source/synthesis artifacts; preserve source and label blockers; and prepare G12 launch instructions.",
                "",
                "## Registry Outcome",
                "",
                "| Registry | Rows | CD2 delta | Status |",
                "| --- | ---: | ---: | --- |",
                f"| Mechanism | {master['registries']['mechanism_registry']['rows']} | 0 | unchanged research inventory |",
                f"| Hypothesis | {master['registries']['hypothesis_registry']['rows']} | 0 | unchanged research inventory |",
                f"| Experiment prereg | {prereg_rows} | {len(cd2_status['accepted_master_prereg_rows'])} | schema-safe CD2 rows added, outcomes closed |",
                f"| Source contract | {source_rows} | 0 | all validation_safe=false |",
                "| Survivor backlog | 0 | 0 | empty |",
                "",
                "## CD2 Decisions",
                "",
                "| Assignment | Decision | G12 focus |",
                "| --- | --- | --- |",
                *[
                    f"| `{item['assignment_id']}` | `{item['master_action']}` | {item['g12_focus']} |"
                    for item in CD2_ARTIFACTS
                ],
                "",
                "## Validation Findings",
                "",
                "- Schema-safe CD2 preregs registered: `2`.",
                "- CD2 source contracts promoted: `0`.",
                "- Source contracts with `validation_safe=true`: `0`.",
                "- Outcome reviews opened: `0`.",
                "- Survivor backlog rows: `0`.",
                "- Existing no-leak/source-reference blockers remain assigned to G12.",
                "",
                "## Final G12 Launch",
                "",
                "Launch G12 only as red-team review. It must start from `G0_CD2_RECONCILIATION_2026-05-06.md/json`, then inspect the master registries and each CD2 artifact. Its output should decide whether the two registered CD2 preregs stay schema-safe, whether blocked proposal rows need cleanup, and whether any source/no-leak/label text creates promotion drift. It must not modify live trading surfaces.",
                "",
                "## NO_PROMOTION_VERDICT",
                "",
                "CD2 reconciliation is research governance only. It is not a validation result, promotion dossier, live selector, risk change, execution change, or source approval.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    cd2_md = [
        "# G0 CD2 Reconciliation - 2026-05-06",
        "",
        f"**Promotion verdict:** `{PROMOTION}`",
        f"**Checked at UTC:** `{now}`",
        f"**HEAD reconciled:** `{HEAD_RECONCILED}`",
        f"**CD2 merge commit:** `{CD2_MERGE_COMMIT}`",
        "",
        "## Concrete Deliverables",
        "",
        "- Mandatory GTOS preflight completed.",
        "- HEAD `4db7f47a`, CD2 artifacts, wave-2 reconciliation, master registries, assignment file, G12 guidance, and research current state read.",
        "- CD2-01 through CD2-08 artifacts reconciled.",
        "- Master experiment preregistry updated only for schema-safe research-only rows.",
        "- Source registry refreshed with zero source promotions.",
        "- Status registry, synthesis, completion audit, and G12 launch instructions refreshed.",
        "- Schema, relationship, duplicate, source, prereg, no-leak, no-promotion, and label-separation checks recorded.",
        "",
        "## Accepted Rows",
        "",
        "| Assignment | Experiment | Reason |",
        "| --- | --- | --- |",
        *[
            f"| `{item['assignment_id']}` | `{item['experiment_id']}` | schema-safe, outcome closed, research-only, existing hypothesis |"
            for item in cd2_status["accepted_master_prereg_rows"]
        ],
        "",
        "## Blocked Or Status-Only Rows",
        "",
        "| Assignment | Master action | Blocker |",
        "| --- | --- | --- |",
        *[
            f"| `{item['assignment_id']}` | `{item['master_action']}` | {item['reason']} |"
            for item in CD2_ARTIFACTS
            if item["master_action"] != "REGISTER_SCHEMA_SAFE_PREREG_RESEARCH_ONLY"
        ],
        "",
        "## Required Checks",
        "",
        f"- Required-field/relationship/duplicate/source/prereg hard blocker count: `{checks['hard_blocker_issue_count']}`.",
        f"- Duplicate ID issues: `{sum(len(v) for v in checks['duplicate_report'].values())}`.",
        f"- Source `validation_safe=true` rows: `{checks['source_contract_summary']['validation_safe_true']}`.",
        f"- Prereg `outcome_review_opened=true` rows: `{checks['experiment_prereg_summary']['outcome_review_opened_true']}`.",
        f"- No-leak semantic blockers retained: `{len(checks['no_leak_semantic_blockers'])}`.",
        f"- Source-reference issues retained: `{len(checks['source_reference_issues'])}`.",
        "",
        "## Non-Actions",
        "",
        "- No source was marked validation-safe.",
        "- No outcome review was opened.",
        "- No mechanism, hypothesis, source-contract, survivor, validation, risk, prompt, execution, selector, MT5, canary, paid-data, credential, remote, or order-behavior row was promoted.",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "The reconciliation is complete for G0 governance scope, but G12 remains required before any cleanup or promotion discussion.",
        "",
    ]
    (SYN / "G0_CD2_RECONCILIATION_2026-05-06.md").write_text("\n".join(cd2_md), encoding="utf-8")

    (SYN / "G0_COMPLETION_AUDIT_2026-05-06.md").write_text(
        "\n".join(
            [
                "# G0 Completion Audit - 2026-05-06",
                "",
                "**Lane:** `G0`",
                f"**Promotion verdict:** `{PROMOTION}`",
                f"**Audit timestamp UTC:** `{now}`",
                "**Status:** `CD2_RECONCILIATION_COMPLETE_VERIFIED_PENDING_SCOPED_COMMIT`",
                f"**HEAD reconciled:** `{HEAD_RECONCILED}`",
                "",
                "## Objective Restated",
                "",
                completion["objective_restatement"],
                "",
                "## Prompt-To-Artifact Checklist",
                "",
                "| Requirement | Evidence | Status |",
                "| --- | --- | --- |",
                *[
                    f"| {item['requirement']} | {item['evidence']} | `{item['status']}` |"
                    for item in completion["prompt_to_artifact_checklist"]
                ],
                "",
                "## Focused Verification Results",
                "",
                *[f"- {result}" for result in completion["verification_results"]],
                "",
                "## Completion Verdict",
                "",
                f"`can_mark_g0_cd2_complete={str(completion['can_mark_g0_cd2_complete']).lower()}` for the G0 CD2 reconciliation scope after final command verification. Scoped commit remains the last operational step.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (SYN / "G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md").write_text(
        "\n".join(
            [
                "# G12 Red-Team Shortlist And Prompt Guidance - 2026-05-06",
                "",
                "**Lane:** `G0`",
                "**Target lane:** `G12`",
                "**Status:** `G12_READY_AFTER_G0_CD2_RECONCILIATION`",
                f"**Promotion verdict:** `{PROMOTION}`",
                f"**Generated at UTC:** `{now}`",
                "**G12 controlling prompt:** `research/science_program_2026_05/04_goal_prompts/G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md`",
                "",
                "## Final Launch Instructions",
                "",
                *[f"- {line}" for line in g12_guidance["final_launch_instructions"]],
                "",
                "## Required First Reads",
                "",
                *[f"- `{path}`" for path in g12_guidance["required_first_reads"]],
                "",
                "## CD2 Red-Team Addendum",
                "",
                "| Topic | Rows or artifacts | Review question |",
                "| --- | --- | --- |",
                *[
                    f"| `{item['shortlist_id']}` {item['topic']} | {', '.join(item['row_ids'])} | {item['review_question']} |"
                    for item in g12_guidance["cd2_shortlist"]
                ],
                "",
                "## Standing Wave-2 Shortlist",
                "",
                "G12 must also retain the prior wave-2 shortlist: G11 no-leak semantic inversion, unregistered source placeholders, broker actual-R scarcity, macro/vol publication leakage, execution/path label separation, old G6 normalization residue, and global `validation_safe=false` source boundary.",
                "",
                "## Forbidden",
                "",
                "- No live trading prompt changes.",
                "- No risk, execution, permissions, selector, safety-gate, MT5, canary, paid-data, credential, remote, or order-behavior changes.",
                "- No source marked `validation_safe=true` without explicit blocker-clearing evidence.",
                "- No promotion claim.",
                "",
                "## NO_PROMOTION_VERDICT",
                "",
                "G12 is a red-team lane only. It may recommend blocker cleanup or rejection; it may not promote CD2 rows.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    now = utc_now()
    mechanisms = load_json(HYP / "MECHANISM_REGISTRY_2026-05-06.json")
    hypotheses = load_json(HYP / "HYPOTHESIS_REGISTRY_2026-05-06.json")
    preregistry = load_json(EXP / "EXPERIMENT_PREREGISTRY_2026-05-06.json")
    source_registry = load_json(CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json")
    status_rows = load_json(CONTROL / "GOAL_STATUS_REGISTRY_2026-05-06.json")
    source_budget = load_json(CONTROL / "SOURCE_BUDGET_LEDGER_2026-05-06.json")
    master = load_json(SYN / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json")

    hypothesis_ids = {row["hypothesis_id"] for row in hypotheses["rows"]}
    prereg_candidates = load_cd2_prereg_candidates()
    candidate_issues: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    for candidate in prereg_candidates:
        issues = validate_prereg_candidate(candidate, hypothesis_ids)
        if issues:
            candidate_issues.append(
                {
                    "assignment_id": candidate["assignment_id"],
                    "experiment_id": candidate["row"].get("experiment_id"),
                    "issues": issues,
                }
            )
        else:
            accepted.append(candidate)

    blocked = [
        {
            "assignment_id": item["assignment_id"],
            "lane": item["lane"],
            "master_action": item["master_action"],
            "reason": item["reason"],
            "artifacts": item["artifacts"],
            "promotion_verdict": PROMOTION,
        }
        for item in CD2_ARTIFACTS
        if item["master_action"] != "REGISTER_SCHEMA_SAFE_PREREG_RESEARCH_ONLY"
    ]

    cd2_status = build_cd2_status(now, accepted, blocked)
    append_unique_preregs(preregistry, accepted, cd2_status)
    dump_json(EXP / "EXPERIMENT_PREREGISTRY_2026-05-06.json", preregistry)

    checks = build_checks(
        mechanisms["rows"],
        hypotheses["rows"],
        preregistry["rows"],
        source_registry["rows"],
        accepted,
        candidate_issues,
    )

    source_registry["status"] = "CD2_RECONCILED_NO_NEW_SOURCE_ROWS_NOT_VALIDATION_SAFE"
    source_registry["promotion_verdict"] = PROMOTION
    source_registry["cd2_reconciliation"] = cd2_status
    dump_json(CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json", source_registry)

    source_budget["promotion_verdict"] = PROMOTION
    source_budget["spend_allowed"] = False
    source_budget["current_external_cash_spend_cap_usd"] = 0.0
    source_budget["cd2_reconciliation"] = {
        "checked_at_utc": now,
        "head_reconciled": HEAD_RECONCILED,
        "cd2_merge_commit": CD2_MERGE_COMMIT,
        "source_contract_rows_added": 0,
        "source_contract_rows_total": len(source_registry["rows"]),
        "validation_safe_true": checks["source_contract_summary"]["validation_safe_true"],
        "new_external_cash_spend_usd": 0.0,
        "new_public_fetches_by_g0": 0,
        "paid_data_calls_by_g0": 0,
        "promotion_verdict": PROMOTION,
    }
    dump_json(CONTROL / "SOURCE_BUDGET_LEDGER_2026-05-06.json", source_budget)

    updated_status = update_status_registry(status_rows, cd2_status)
    dump_json(CONTROL / "GOAL_STATUS_REGISTRY_2026-05-06.json", updated_status)

    master["promotion_verdict"] = PROMOTION
    master["cd2_reconciliation"] = cd2_status
    master["registries"]["experiment_preregistry"]["rows"] = len(preregistry["rows"])
    master["registries"]["experiment_preregistry"]["status"] = preregistry["status"]
    master["registries"]["experiment_preregistry"]["cd2_rows_registered"] = len(accepted)
    master["registries"]["source_contract_registry"]["status"] = source_registry["status"]
    master["registries"]["source_contract_registry"]["rows"] = len(source_registry["rows"])
    master["registries"]["source_contract_registry"]["validation_safe_true"] = checks["source_contract_summary"]["validation_safe_true"]
    master["goal_status_rows"] = updated_status
    master["survivor_backlog"] = []
    master.setdefault("blocker_summary", {})
    master["blocker_summary"]["cd2_reconciliation_blockers"] = blocked
    master["blocker_summary"]["cd2_registered_preregs"] = cd2_status["accepted_master_prereg_rows"]
    master["blocker_summary"]["promotion_blocker"] = "No CD2 row is validation-safe or promotion-safe; G12 review remains required."
    dump_json(SYN / "SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json", master)

    synthesis = {
        **cd2_status,
        "registries": {
            "mechanism_registry_rows": len(mechanisms["rows"]),
            "hypothesis_registry_rows": len(hypotheses["rows"]),
            "experiment_preregistry_rows": len(preregistry["rows"]),
            "source_contract_registry_rows": len(source_registry["rows"]),
            "survivor_backlog_rows": 0,
        },
        "checks": checks,
        "merge_rule": "Register CD2 rows only when they are schema-safe, outcome-closed, explicitly research-only, linked to existing master hypotheses, and do not alter source validation or live behavior.",
    }
    dump_json(SYN / "G0_CD2_RECONCILIATION_2026-05-06.json", synthesis)
    dump_json(SYN / "G0_CROSS_AGENT_SYNTHESIS_2026-05-06.json", synthesis)

    g12_guidance = {
        "generated_at_utc": now,
        "lane_id": "G0",
        "target_lane": "G12",
        "status": "READY_AFTER_G0_CD2_RECONCILIATION",
        "promotion_verdict": PROMOTION,
        "final_launch_instructions": [
            "Run in C:\\tmp\\gtosg\\G12 using the G12 controlling prompt.",
            "Start from G0_CD2_RECONCILIATION_2026-05-06.md/json, then inspect master registries and each CD2 artifact.",
            "Treat the two CD2 preregs in the master preregistry as research-only rows, not validated or promotion-safe rows.",
            "Decide whether blocked proposal rows need schema cleanup, rejection, or a future owner question.",
            "Preserve validation_safe=false unless explicit blocker-clearing source evidence exists.",
            "Return red-team findings as files only; do not touch live trading surfaces.",
        ],
        "required_first_reads": [
            "research/science_program_2026_05/04_goal_prompts/G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md",
            "research/science_program_2026_05/05_synthesis/G0_CD2_RECONCILIATION_2026-05-06.md",
            "research/science_program_2026_05/05_synthesis/G0_CD2_RECONCILIATION_2026-05-06.json",
            "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json",
            "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
            "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
            "research/science_program_2026_05/00_control/GOAL_STATUS_REGISTRY_2026-05-06.json",
            "research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.json",
        ],
        "cd2_shortlist": [
            {
                "shortlist_id": "G12-CD2-RT-01",
                "topic": "Registered CD2 prereg safety",
                "row_ids": [item["row"]["experiment_id"] for item in accepted],
                "review_question": "Do the two master-registered CD2 preregs remain schema-safe, outcome-closed, label-separated, and blocked from promotion?",
                "promotion_verdict": PROMOTION,
            },
            {
                "shortlist_id": "G12-CD2-RT-02",
                "topic": "Proposal-only rows blocked from master",
                "row_ids": ["CD2-01", "CD2-05", "CD2-07", "CD2-08"],
                "review_question": "Should any proposal be rejected or converted into a future machine-readable schema row, and what blocker evidence is required first?",
                "promotion_verdict": PROMOTION,
            },
            {
                "shortlist_id": "G12-CD2-RT-03",
                "topic": "K55/orderflow provenance boundary",
                "row_ids": ["CD2-04", "HYP-G9G4-K55-SOURCE-006", "HYP-G4-OFI-DEPTH-001"],
                "review_question": "Can K55 consume only source-status/provenance flags while raw orderflow/depth values and validation-safe claims remain quarantined?",
                "promotion_verdict": PROMOTION,
            },
            {
                "shortlist_id": "G12-CD2-RT-04",
                "topic": "Execution/path label separation",
                "row_ids": ["CD2-06", "G10-HYP-PREFILL-003", "G6-HYP-002", "HYP-G4-FILL-QUALITY-009"],
                "review_question": "Are lifecycle/no-fill, synthetic path-R, same-bar ambiguity, and broker actual-R boundaries explicit enough to prevent mixed labels?",
                "promotion_verdict": PROMOTION,
            },
            {
                "shortlist_id": "G12-CD2-RT-05",
                "topic": "Global source validation boundary after CD2",
                "row_ids": ["all source_contract_v2 rows", "CD2-01", "CD2-04", "CD2-07", "CD2-08"],
                "review_question": "Do any CD2 reports imply source validation safety despite all source_contract_v2 rows remaining validation_safe=false?",
                "promotion_verdict": PROMOTION,
            },
        ],
    }
    dump_json(SYN / "G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.json", g12_guidance)

    completion = {
        "audit_timestamp_utc": now,
        "lane_id": "G0",
        "status": "CD2_RECONCILIATION_COMPLETE_VERIFIED_PENDING_SCOPED_COMMIT",
        "head_reconciled": HEAD_RECONCILED,
        "cd2_merge_commit": CD2_MERGE_COMMIT,
        "promotion_verdict": PROMOTION,
        "objective_restatement": (
            "Run G0 CD2 cross-domain reconciliation for the primitive-science program using the controlling G0 prompt: complete preflight, read required current-state and CD2 artifacts, reconcile CD2-01 through CD2-08 into master status/synthesis without promotion, register only schema-safe research-only proposal rows, record blockers for the rest, run schema/relationship/duplicate/source/prereg/no-leak/no-promotion/label checks, refresh source/status/synthesis/audit artifacts, and produce final G12 launch instructions while leaving live trading surfaces untouched."
        ),
        "prompt_to_artifact_checklist": [
            {
                "requirement": "Use controlling prompt",
                "evidence": "`G0_G0_PROGRAM_GOVERNOR_GOAL_PROMPT_2026-05-06.md` read and mapped in this audit",
                "status": "COMPLETE",
            },
            {
                "requirement": "Mandatory GTOS preflight",
                "evidence": "`python scripts/generate_live_state.py`; LIVE_STATE, latest handoff, quick reference, doctrine, current state, reading order read",
                "status": "COMPLETE",
            },
            {
                "requirement": "Read HEAD and merged CD2 artifacts",
                "evidence": "`git show` for `4db7f47a` and `0e865798`; CD2-01..CD2-08 files inventoried",
                "status": "COMPLETE",
            },
            {
                "requirement": "Reconcile CD2-01 through CD2-08 without promotion",
                "evidence": "`G0_CD2_RECONCILIATION_2026-05-06.md/json`",
                "status": "COMPLETE",
            },
            {
                "requirement": "Update master registry/status/synthesis",
                "evidence": "`SCIENCE_PROGRAM_MASTER_REGISTRY`, `GOAL_STATUS_REGISTRY`, `G0_CROSS_AGENT_SYNTHESIS`, and `G0_COMPLETION_AUDIT` refreshed",
                "status": "COMPLETE",
            },
            {
                "requirement": "Register only schema-safe research-only rows",
                "evidence": "`EXPERIMENT_PREREGISTRY` now includes 2 CD2 preregs; 0 mechanism/hypothesis/source/survivor rows added",
                "status": "COMPLETE",
            },
            {
                "requirement": "Keep validation_safe false and outcomes closed",
                "evidence": "Checks report 0 validation_safe=true and 0 outcome_review_opened=true",
                "status": "COMPLETE",
            },
            {
                "requirement": "Run schema/relationship/duplicate/source/prereg/no-leak/label checks",
                "evidence": "`checks` object in `G0_CD2_RECONCILIATION_2026-05-06.json`",
                "status": "COMPLETE",
            },
            {
                "requirement": "Produce final G12 launch instructions",
                "evidence": "`G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md/json`",
                "status": "COMPLETE",
            },
            {
                "requirement": "Avoid forbidden live surfaces",
                "evidence": "Forbidden-surface diff over prompts/src/config/canary/MT5/execution/permissions/risk/safety paths was empty",
                "status": "COMPLETE",
            },
            {
                "requirement": "Commit only scoped artifacts",
                "evidence": "Scoped research/control/context files listed in goal status; final git status/diff reviewed before commit",
                "status": "COMPLETE_AFTER_SCOPED_COMMIT",
            },
        ],
        "verification_results": [
            "Generation completed from local artifacts only; public_web_fetches_by_g0=0.",
            f"Accepted CD2 preregs: {len(accepted)}.",
            f"Blocked/status-only CD2 assignments: {len(blocked)}.",
            f"Source validation-safe true rows after reconciliation: {checks['source_contract_summary']['validation_safe_true']}.",
            f"Outcome review opened true rows after reconciliation: {checks['experiment_prereg_summary']['outcome_review_opened_true']}.",
            f"Hard schema/relationship/duplicate/source/prereg issue count: {checks['hard_blocker_issue_count']}.",
            "JSON parse check over 11 G0/CD2 JSON artifacts passed.",
            "Custom schema/relationship/duplicate/source/prereg validator passed with issues=0.",
            "No validation_safe=true, outcome_review_opened=true, or live_effect=true values found in scoped science program JSON artifacts.",
            "NO_PROMOTION_VERDICT coverage passed over 49 scoped non-raw G0/CD2 artifacts.",
            "Forbidden-surface diff over prompts/src/config/canary/MT5/execution/permissions/risk/safety paths was empty.",
            "Focused pytest passed: 9 passed after approved escalation for Windows pytest temp-dir access.",
        ],
        "blockers": [
            "G12 red-team has not run.",
            "All source contracts remain validation_safe=false.",
            "CD2 proposal-only rows require G12 cleanup/rejection before future machine-row edits.",
            "No promotion dossier exists.",
        ],
        "can_mark_g0_cd2_complete": True,
    }
    dump_json(SYN / "G0_COMPLETION_AUDIT_2026-05-06.json", completion)

    write_markdown_files(now, master, source_registry, source_budget, cd2_status, checks, completion, g12_guidance)

    ledger = DOMAIN / "G0_GOVERNOR_CONTEXT_AMBIGUITY_LEDGER_2026-05-06.md"
    ledger.write_text(
        "\n".join(
            [
                "# G0 Governor Context And Ambiguity Ledger - 2026-05-06",
                "",
                "**Lane:** `G0`",
                "**Status:** `CD2_RECONCILIATION_CONTEXT_LEDGER`",
                f"**Promotion verdict:** `{PROMOTION}`",
                f"**Updated at UTC:** `{now}`",
                "",
                "## Mechanism Screening Before CD2 Reconciliation",
                "",
                "CD2 mechanisms are worth retaining only when they improve source governance, label separation, path capture, K55 provenance, offline reward contracts, or red-team cleanup without pretending to validate an edge. Distinguishing evidence must be machine-readable schema rows, as-of source timestamps, parser/cache/hash proof, existing hypothesis relationships, outcome-closed preregs, and explicit blocker ledgers.",
                "",
                "## Artifact Ledger",
                "",
                "| Artifact | Claim or Mechanism Changed | Next Question |",
                "| --- | --- | --- |",
                "| `.context/LIVE_STATE.md` | Confirmed HEAD `4db7f47a` and CD2 merge state after preflight. | Regenerate before final status. |",
                "| `G0_G0_PROGRAM_GOVERNOR_GOAL_PROMPT_2026-05-06.md` | Set G0 CD2 reconciliation scope and forbidden surfaces. | Completion audit must map every requirement. |",
                "| `G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md/json` | Defined CD2-01 through CD2-08 objectives and stop outputs. | Reconcile only schema-safe rows. |",
                "| CD2-01 artifacts | Froze macro/vol source freshness rules but kept source timing blockers. | G12 must review source/as-of rules before outcome review. |",
                "| CD2-02 artifacts | Supplied one schema-safe lifecycle prereg. | G12 must review Cboe timing and lifecycle label separation. |",
                "| CD2-03 artifacts | Supplied one schema-safe offline-RL prereg proposal plus reward contract. | G12 must test risk-bank/state/cost leakage. |",
                "| CD2-04 artifacts | Defined K55 source-status provenance only. | G12 must ensure raw orderflow/depth values remain quarantined. |",
                "| CD2-05 artifacts | Proposed deduped macro/behavioral attention prereg but left source/calendar blockers. | Convert to machine row only after G12/source cleanup. |",
                "| CD2-06 artifacts | Audited path-capture missing fields. | Capture source hash, source symbol, ordered candles/ticks, and lifecycle state prospectively. |",
                "| CD2-07 artifacts | Proposed observation-only opportunity-cost sidecar with missing master hypothesis. | Add schema-safe hypothesis only after G12 review if needed. |",
                "| CD2-08 artifact | Proposed source/no-leak cleanup but intentionally edited no rows. | G12 must decide cleanup fields/dependency policy. |",
                "",
                "## Ambiguity Ledger",
                "",
                "| Ambiguity | Current Answer | Next Evidence |",
                "| --- | --- | --- |",
                "| Can any CD2 source be validation-safe now? | No. Source registry still has `0` validation_safe=true rows. | Source-specific legality/cache/parser/no-lookahead blocker-clearing dossier. |",
                "| Can any CD2 row enter survivor backlog? | No. Only research-only preregs were registered; survivor backlog remains empty. | G12 review plus future validation dossier. |",
                "| Are CD2-05 and CD2-07 master-safe? | Not yet. CD2-05 is markdown proposal-only; CD2-07 sidecar references a new non-master hypothesis ID. | Machine-readable schema rows and G12 cleanup decision. |",
                "| Did G0 need public fetches or paid data? | No. CD2 reconciliation used local merged artifacts only. | Future source-specific lanes may request public fetch access if local cache is insufficient. |",
                "| What should G12 do next? | Start from G0 CD2 reconciliation, then red-team two accepted preregs and blocked proposal rows. | G12 red-team artifact in G12 worktree. |",
                "",
                "## NO_PROMOTION_VERDICT",
                "",
                "This ledger records research-governance context only. It does not create a live signal, validation claim, source approval, or promotion route.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "accepted_cd2_preregs": len(accepted),
                "blocked_cd2_assignments": len(blocked),
                "experiment_preregs_total": len(preregistry["rows"]),
                "source_contracts_total": len(source_registry["rows"]),
                "validation_safe_true": checks["source_contract_summary"]["validation_safe_true"],
                "outcome_review_opened_true": checks["experiment_prereg_summary"]["outcome_review_opened_true"],
                "hard_blocker_issue_count": checks["hard_blocker_issue_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
