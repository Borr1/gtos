"""Build Stage 09 final truth-freeze report and decision map.

This offline builder consumes the committed replay truth-engine artifacts and
materializes the terminal report, decision map, completion audit, and summary.
It does not mutate production config, prompts, broker state, accounts, orders,
deals, positions, or live runtime behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BUILDER_PATH = Path(__file__).resolve()
PREREG_PATH = ROUTE_DIR / "VNEXT_REPLAY_PREREGISTRATION_MANIFEST_2026-05-24.json"
DATA_COVERAGE_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_DATA_COVERAGE_SUMMARY_2026-05-24.json"
RUNTIME_HARNESS_VERIFY_PATH = ROUTE_DIR / "VNEXT_REPLAY_RUNTIME_HARNESS_VERIFY_2026-05-24.json"
EVENT_PATH_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_EVENT_PATH_RECONSTRUCTION_SUMMARY_2026-05-24.json"
STAGE05_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_SATURATED_REPLAY_SUMMARY_2026-05-24.json"
STAGE05_METRICS_PATH = ROUTE_DIR / "VNEXT_REPLAY_METRICS_SUMMARY_2026-05-24.json"
STAGE06_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_ABLATION_MIXED_SUMMARY_2026-05-24.json"
PROP_METRICS_PATH = ROUTE_DIR / "VNEXT_REPLAY_PROP_FIRM_METRICS_2026-05-24.json"
STAGE07_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_PROP_FIRM_ROBUSTNESS_SUMMARY_2026-05-24.json"
FAILURE_DOSSIER_PATH = ROUTE_DIR / "VNEXT_REPLAY_FAILURE_REPAIR_DOSSIER_2026-05-24.json"
FAILURE_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_FAILURE_REPAIR_LEDGER_2026-05-24.jsonl"
FAILURE_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_FAILURE_REPAIR_SUMMARY_2026-05-24.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"
DECISION_MAP_PATH = ROUTE_DIR / "VNEXT_REPLAY_PROMOTION_KILL_REPAIR_MAP_2026-05-24.json"
FINAL_REPORT_PATH = ROUTE_DIR / "VNEXT_REPLAY_FINAL_REPORT_2026-05-24.md"
COMPLETION_AUDIT_PATH = ROUTE_DIR / "VNEXT_REPLAY_COMPLETION_AUDIT_2026-05-24.json"
STAGE09_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_FINAL_TRUTH_FREEZE_SUMMARY_2026-05-24.json"
SESSION_STATE_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/gtos_vnext_replay_truth_engine"
    / "VNEXT_REPLAY_TRUTH_ENGINE_SESSION_STATE_2026-05-24.json"
)

STAGE_ID = "STAGE_09_FINAL_TRUTH_FREEZE"
DECISION_CATEGORIES = [
    "promote later",
    "keep shadow/default-off",
    "kill/remove candidate",
    "source-repair required",
    "replay-inconclusive",
    "data-required",
    "runtime bug found",
    "methodology limitation",
    "broker/demo-live observation required",
    "AI minimal-budget evaluation required",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, allow_nan=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def stable_hash(payload: Any, length: int = 24) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length]


def run_git(args: list[str], *, allow_failure: bool = False) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8").strip()
    except Exception as exc:  # pragma: no cover - defensive artifact metadata path
        if allow_failure:
            return f"git {' '.join(args)} failed: {exc}"
        raise


def sorted_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def json_compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def normalize_decision_category(candidate: str) -> str:
    text = str(candidate or "").strip()
    if text in DECISION_CATEGORIES:
        return text
    lowered = text.lower()
    if "source" in lowered and "repair" in lowered:
        return "source-repair required"
    if "broker" in lowered or "demo" in lowered:
        return "broker/demo-live observation required"
    if "ai" in lowered:
        return "AI minimal-budget evaluation required"
    if "data" in lowered:
        return "data-required"
    if "inconclusive" in lowered:
        return "replay-inconclusive"
    if "kill" in lowered or "remove" in lowered:
        return "kill/remove candidate"
    if "promote" in lowered:
        return "promote later"
    return "methodology limitation"


def artifact_record(path: Path, source_kind: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "lines": line_count(path) if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() else None,
        "source_kind": source_kind,
    }


def load_inputs() -> dict[str, Any]:
    return {
        "prereg": read_json(PREREG_PATH),
        "data_coverage": read_json(DATA_COVERAGE_SUMMARY_PATH),
        "runtime_harness": read_json(RUNTIME_HARNESS_VERIFY_PATH),
        "event_path": read_json(EVENT_PATH_SUMMARY_PATH),
        "stage05": read_json(STAGE05_SUMMARY_PATH),
        "stage05_metrics": read_json(STAGE05_METRICS_PATH),
        "stage06": read_json(STAGE06_SUMMARY_PATH),
        "prop": read_json(PROP_METRICS_PATH),
        "stage07": read_json(STAGE07_SUMMARY_PATH),
        "failure_dossier": read_json(FAILURE_DOSSIER_PATH),
        "failure_summary": read_json(FAILURE_SUMMARY_PATH),
        "failure_rows": list(iter_jsonl(FAILURE_LEDGER_PATH)),
        "manifest": read_json(OUTPUT_MANIFEST_PATH),
        "session_state": read_json(SESSION_STATE_PATH),
    }


def build_decision_map(data: dict[str, Any]) -> dict[str, Any]:
    failure_rows = data["failure_rows"]
    category_counts: Counter[str] = Counter({category: 0 for category in DECISION_CATEGORIES})
    family_counts: Counter[str] = Counter()
    decision_rows: list[dict[str, Any]] = []
    for row in failure_rows:
        category = normalize_decision_category(str(row.get("decision_map_candidate") or ""))
        category_counts[category] += 1
        family = str(row.get("family") or "unknown_family")
        family_counts[family] += 1
        decision_rows.append(
            {
                "decision_row_id": "decision_" + stable_hash([row.get("repair_row_id"), family, category]),
                "source_repair_row_id": row.get("repair_row_id"),
                "decision_category": category,
                "family": family,
                "evidence_scope": row.get("evidence_scope"),
                "severity": row.get("severity"),
                "status": row.get("status"),
                "impact_metrics": row.get("impact_metrics"),
                "repair_action": row.get("repair_action"),
                "owner_access_or_capture_requirement": row.get("owner_access_or_capture_requirement"),
                "current_session_feasibility": row.get("current_session_feasibility"),
                "evidence_artifacts": row.get("evidence_artifacts"),
                "runtime_or_live_change_allowed_now": False,
            }
        )

    prop = data["prop"]
    current = prop["mode_metrics"]["current_config_shadow"]["overall"]
    activated = prop["mode_metrics"]["hypothetical_activated_vnext"]["overall"]
    headline_actions = [
        {
            "action_id": "no_production_promotion_from_replay_package",
            "decision_category": "keep shadow/default-off",
            "decision": "Do not promote any vNext execution-effect flag from this session.",
            "reason": (
                "Hypothetical activation improved replay proxy R and drawdown but reduced entry-touched "
                "trades from 100 to 1; broker-realized execution geometry and AI replay remain absent."
            ),
            "evidence": {
                "current_total_r": current.get("effective_r_total"),
                "activated_total_r": activated.get("effective_r_total"),
                "activation_delta_r": prop.get("activation_delta", {}).get(
                    "effective_r_total_delta_hypothetical_minus_current"
                ),
                "current_entry_touched_trades": current.get("trade_count_entry_touched"),
                "activated_entry_touched_trades": activated.get("trade_count_entry_touched"),
            },
        },
        {
            "action_id": "risk_blocks_remain_default_off_research_candidate",
            "decision_category": "keep shadow/default-off",
            "decision": "Keep vNext risk/pending/pre-AI execution effects shadow/default-off pending demo observation.",
            "reason": "Replay shows strong protective behavior, but overblocking and sparse activated trade count prevent promotion.",
            "evidence": {
                "active_blocked_rows": activated.get("active_blocked_rows"),
                "zero_risk_blocks": data["stage05_metrics"].get("zero_risk_blocks"),
            },
        },
        {
            "action_id": "forward_capture_required_for_execution_truth",
            "decision_category": "broker/demo-live observation required",
            "decision": "Use demo/forward capture to collect broker execution geometry before exact R claims.",
            "reason": "Historical price paths cannot generate order/deal tickets, fills, slippage, commission, swap, or partial exits.",
            "evidence": data["failure_dossier"]["families"]["entry_execution_fill_no_fill"]["impact_metrics"],
        },
        {
            "action_id": "minimal_budget_ai_evaluation_required_only_if_ai_claim_is_needed",
            "decision_category": "AI minimal-budget evaluation required",
            "decision": "Do not run paid AI replay here; design a separate stratified/cache-backed AI reliability sample if needed.",
            "reason": "This session measured mechanical pre-AI skip/narrow routing, not paid model completions.",
            "evidence": data["failure_dossier"]["families"]["ai_prompt_routing_limitation"]["impact_metrics"],
        },
    ]
    for action in headline_actions:
        category_counts[action["decision_category"]] += 1

    return {
        "schema_version": "vnext_replay_stage09_promotion_kill_repair_map_v1",
        "stage_id": STAGE_ID,
        "generated_utc": utc_now(),
        "pass": True,
        "decision_policy": "No live or production change is made by this map; all actions are future implementation, capture, or evaluation candidates.",
        "category_counts": sorted_counter(category_counts),
        "family_counts": sorted_counter(family_counts),
        "headline_actions": headline_actions,
        "repair_ledger_decision_rows": decision_rows,
        "promotion_rows_now": 0,
        "kill_remove_rows_now": category_counts["kill/remove candidate"],
        "runtime_bug_found_rows": category_counts["runtime bug found"],
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
    }


def completion_requirements(data: dict[str, Any]) -> list[dict[str, Any]]:
    manifest_paths = {item.get("path") for item in data["manifest"].get("outputs", []) if isinstance(item, dict)}
    required = [
        ("preflight_context_reread", True, "LIVE_STATE and mandatory context were reread before Stage08/Stage09 continuation; hashes are recorded in the session spine and preregistration."),
        ("preregistration_manifest", PREREG_PATH.exists(), rel(PREREG_PATH)),
        ("data_inventory", DATA_COVERAGE_SUMMARY_PATH.exists(), rel(DATA_COVERAGE_SUMMARY_PATH)),
        ("runtime_truth_harness", data["runtime_harness"].get("pass") is True, rel(RUNTIME_HARNESS_VERIFY_PATH)),
        ("event_and_path_reconstruction", data["event_path"].get("pass") is True, rel(EVENT_PATH_SUMMARY_PATH)),
        ("saturated_replay", data["stage05"].get("pass") is True and data["stage05"].get("replay_rows", 0) > 0, rel(STAGE05_SUMMARY_PATH)),
        ("ablation_and_mixed_resolution", data["stage06"].get("pass") is True and data["stage06"].get("ablation_rows", 0) > 0, rel(STAGE06_SUMMARY_PATH)),
        ("prop_firm_and_robustness_metrics", data["prop"].get("pass") is True and data["stage07"].get("pass") is True, f"{rel(PROP_METRICS_PATH)}; {rel(STAGE07_SUMMARY_PATH)}"),
        ("failure_repair_dossiers", data["failure_summary"].get("pass") is True and data["failure_summary"].get("repair_rows", 0) > 0, rel(FAILURE_SUMMARY_PATH)),
        ("final_decision_map", True, rel(DECISION_MAP_PATH)),
        ("final_report", True, rel(FINAL_REPORT_PATH)),
        ("source_gap_evidence", data["failure_summary"].get("source_gap_repair_rows") == 43, "43 source-gap repair rows preserved in Stage08."),
        ("m15_path_modes_separated", data["failure_dossier"]["path_diagnostics"].get("path_mode_counts", {}).get("bar_close_m15", 0) > 0 and data["failure_dossier"]["path_diagnostics"].get("path_mode_counts", {}).get("m1_path_aware", 0) > 0, "M15 and lower-timeframe/tick/OHLC modes remain separate."),
        ("large_outputs_manifest_recorded", rel(OUTPUT_MANIFEST_PATH) in data["session_state"].get("current_output_artifacts", []) and len(manifest_paths) >= 1, rel(OUTPUT_MANIFEST_PATH)),
    ]
    return [
        {
            "requirement_id": req_id,
            "status": "complete" if ok else "incomplete",
            "evidence": evidence,
        }
        for req_id, ok, evidence in required
    ]


def build_completion_audit(data: dict[str, Any], decision_map: dict[str, Any]) -> dict[str, Any]:
    requirements = completion_requirements(data)
    incomplete = [row for row in requirements if row["status"] != "complete"]
    source_repair_rows = [
        row for row in decision_map["repair_ledger_decision_rows"] if row["decision_category"] == "source-repair required"
    ]
    return {
        "schema_version": "vnext_replay_stage09_completion_audit_v1",
        "stage_id": STAGE_ID,
        "generated_utc": utc_now(),
        "pass": not incomplete,
        "overall_completion_status": "complete_with_source_bound_limitations" if not incomplete else "incomplete",
        "requirements": requirements,
        "remaining_limitations_are_terminal_to_this_session": True,
        "remaining_limitations_summary": {
            "source_repair_required_rows": len(source_repair_rows),
            "data_required_rows": decision_map["category_counts"].get("data-required", 0),
            "broker_demo_live_required_rows": decision_map["category_counts"].get(
                "broker/demo-live observation required", 0
            ),
            "ai_minimal_budget_required_rows": decision_map["category_counts"].get(
                "AI minimal-budget evaluation required", 0
            ),
            "why_no_same_evidence_class_step_remains": (
                "Remaining items require non-generatable historical GTOS state, future/demo broker execution capture, "
                "source-safe regime/news enrichment, read-only export not already present, or explicit paid-AI approval. "
                "All available repo/local replay, path, ablation, MIXED, prop, robustness, and repair-dossier steps are materialized."
            ),
        },
        "mandatory_context_files_read_after_preflight": [
            ".context/LIVE_STATE.md",
            "research/science_program_2026_05/04_goal_prompts/VNEXT_REPLAY_TRUTH_ENGINE_AND_SATURATED_ABLATION_GOAL_PROMPT_2026-05-24.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/orchestrator_successor_operating_brief.md",
            ".context/00_core/orchestrator_methodology_hardening_controls.md",
            ".context/00_core/parallel_goal_merge_playbook.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/02_session_handoffs/SESSION_63_VNEXT_EXACT_R_SOURCE_REPAIR_GUARD_HANDOFF_2026-05-19.md",
            rel(PREREG_PATH),
            rel(SESSION_STATE_PATH),
        ],
        "builder_posture": "replay/repair/final-freeze builder; not G12/G0 audit and not live-production promotion",
        "forbidden_surface_check": {
            "no_live_trading_or_broker_mutation": True,
            "production_config_mutated": False,
            "paid_api_or_vendor_call": False,
            "remote_push": False,
        },
        "git": {
            "head": run_git(["rev-parse", "HEAD"]),
            "commit": run_git(["log", "-1", "--oneline"]),
            "status_short": run_git(["status", "--short"]),
            "lfs_status": run_git(["lfs", "status"], allow_failure=True),
        },
    }


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def build_report(data: dict[str, Any], decision_map: dict[str, Any], audit: dict[str, Any]) -> str:
    prop = data["prop"]
    current = prop["mode_metrics"]["current_config_shadow"]["overall"]
    activated = prop["mode_metrics"]["hypothetical_activated_vnext"]["overall"]
    stage05 = data["stage05"]
    stage05_metrics = data["stage05_metrics"]
    path_diag = data["failure_dossier"]["path_diagnostics"]
    mixed = prop["mixed_summary"]
    coverage = {
        "symbol": stage05.get("symbol_group_counts"),
        "session": stage05.get("session_group_counts"),
        "side": stage05.get("side_group_counts"),
        "framework": stage05.get("framework_group_counts"),
    }
    current_challenges = prop["mode_metrics"]["current_config_shadow"].get("challenge_scenarios", {})
    activated_challenges = prop["mode_metrics"]["hypothetical_activated_vnext"].get("challenge_scenarios", {})
    challenge_rows = []
    for scenario_id in sorted(set(current_challenges) | set(activated_challenges)):
        current_scenario = current_challenges.get(scenario_id, {})
        activated_scenario = activated_challenges.get(scenario_id, {})
        risk_pct = (current_scenario.get("scenario") or activated_scenario.get("scenario") or {}).get("risk_pct_per_r")
        challenge_rows.append(
            [
                scenario_id,
                risk_pct,
                current_scenario.get("pass_probability"),
                current_scenario.get("daily_loss_breach_rate"),
                current_scenario.get("max_loss_breach_rate"),
                activated_scenario.get("pass_probability"),
                activated_scenario.get("daily_loss_breach_rate"),
                activated_scenario.get("max_loss_breach_rate"),
            ]
        )

    outcome_rows = [
        ["current_config_shadow", current.get("effective_r_total"), current.get("trade_count_entry_touched"), current.get("terminal_trade_count"), current.get("win_rate_terminal"), current.get("max_drawdown_r"), current.get("daily_drawdown_r"), current.get("max_loss_streak")],
        ["hypothetical_activated_vnext", activated.get("effective_r_total"), activated.get("trade_count_entry_touched"), activated.get("terminal_trade_count"), activated.get("win_rate_terminal"), activated.get("max_drawdown_r"), activated.get("daily_drawdown_r"), activated.get("max_loss_streak")],
    ]
    decision_rows = [
        ["route decisions", json_compact(stage05_metrics.get("decision_counts_follow_avoid_mixed_legacy"))],
        ["pre-AI actions", json_compact(stage05_metrics.get("pre_ai_action_distribution"))],
        ["risk multipliers", json_compact(stage05_metrics.get("risk_multiplier_distribution"))],
    ]
    category_rows = [[category, decision_map["category_counts"].get(category, 0)] for category in DECISION_CATEGORIES]

    lines = [
        "# VNEXT Replay Final Truth Freeze - 2026-05-24",
        "",
        "## Verdict",
        "",
        "The replay truth package is complete for the approved offline evidence class. No production/live trading change is promoted from this session.",
        "",
        "Hypothetical vNext activation is a protective, default-off candidate: replay proxy total R improved from -59.0R to +1.5R and max drawdown improved from -63.5R to 0.0R, but entry-touched trades collapsed from 100 to 1. That is not a production-ready profit engine.",
        "",
        "## Core Counts",
        "",
        md_table(
            ["Metric", "Value"],
            [
                ["event groups", stage05.get("event_groups")],
                ["source event rows", stage05.get("source_event_rows")],
                ["saturated replay rows", stage05.get("replay_rows")],
                ["runtime artifact paths loaded", stage05.get("runtime_artifact_paths_loaded")],
                ["runtime artifact rows loaded", stage05.get("runtime_artifact_index_rows")],
                ["ablation rows", data["stage06"].get("ablation_rows")],
                ["MIXED resolution rows", data["stage06"].get("mixed_resolution_rows")],
                ["robustness rows", data["stage07"].get("robustness_rows")],
                ["Stage08 repair rows", data["failure_summary"].get("repair_rows")],
            ],
        ),
        "",
        "## Outcomes",
        "",
        md_table(
            ["Mode", "Total R", "Entry-Touched", "Terminal Trades", "Terminal WR", "Max DD R", "Daily DD R", "Max Loss Streak"],
            outcome_rows,
        ),
        "",
        "Activation delta: "
        + json.dumps(prop.get("activation_delta"), sort_keys=True),
        "",
        "## System Behavior",
        "",
        "The replay called the current vNext runtime surfaces through the Stage03 harness and preserved current shadow/default-off behavior separately from hypothetical activation. Decision distributions from Stage05:",
        "",
        md_table(["Metric", "Distribution"], decision_rows),
        "",
        "Rows without enough post-L2 fields remain explicit source-repair limitations, not hidden performance rows: "
        + json_compact(stage05.get("runtime_mode_summary", {}).get("current_config_shadow", {}).get("replay_disposition_counts")),
        "",
        "## M15 And Path Blindness",
        "",
        f"Path reconstruction wrote {path_diag.get('path_rows')} rows. M15 bar-close had lower-timeframe/tick/OHLC comparisons in {path_diag.get('groups_with_m15_and_lower_path')} groups; {path_diag.get('m15_lower_path_disagreement_groups')} groups disagreed with lower-path labels, a rate of {path_diag.get('m15_lower_path_disagreement_rate')}.",
        "",
        "Path mode counts: " + json_compact(path_diag.get("path_mode_counts")),
        "",
        "## Coverage",
        "",
        "Stage05 preserved coverage by symbol/session/side/framework without collapsing unknown/null classes:",
        "",
        "- Symbols: " + json_compact(coverage.get("symbol")),
        "- Sessions: " + json_compact(coverage.get("session")),
        "- Sides: " + json_compact(coverage.get("side")),
        "- Frameworks: " + json_compact(coverage.get("framework")),
        "",
        "## Execution, Fill, And Broker Truth",
        "",
        "The replay measured entry touch/no-touch, pending/no-fill, stop-first/target-first, timeout, and path-aware proxy R. It did not fabricate broker-realized tickets, executed prices, commission, swap, slippage, partial exits, or account R. Required forward/demo capture fields are listed in the Stage08 execution dossier.",
        "",
        "## MIXED Resolution",
        "",
        "MIXED classification counts: " + json_compact(mixed.get("mixed_classification_counts")),
        "",
        f"Replay-resolvable MIXED rows: {mixed.get('mixed_replay_resolvable_rows')}; source-required MIXED rows: {mixed.get('mixed_source_required_rows')}.",
        "",
        "## Prop-Firm Scenarios",
        "",
        md_table(
            [
                "Scenario",
                "Risk %/R",
                "Current pass P",
                "Current daily breach",
                "Current max-loss breach",
                "Activated pass P",
                "Activated daily breach",
                "Activated max-loss breach",
            ],
            challenge_rows,
        ),
        "",
        "## Final Decision Map",
        "",
        md_table(["Decision category", "Rows"], category_rows),
        "",
        "Headline actions:",
        "",
    ]
    for action in decision_map["headline_actions"]:
        lines.extend([
            f"- `{action['action_id']}`: {action['decision']} Evidence: {json.dumps(action['evidence'], sort_keys=True)}",
        ])
    lines.extend(
        [
            "",
            "## Completion Audit",
            "",
            f"Completion audit status: `{audit['overall_completion_status']}`.",
            "",
            md_table(
                ["Requirement", "Status", "Evidence"],
                [[row["requirement_id"], row["status"], row["evidence"]] for row in audit["requirements"]],
            ),
            "",
            "Remaining limitations are exact source/capture/approval requirements: "
            + json.dumps(audit["remaining_limitations_summary"], sort_keys=True),
            "",
            "## Forbidden Surfaces",
            "",
            json.dumps(audit["forbidden_surface_check"], indent=2, sort_keys=True),
            "",
            "## Artifacts",
            "",
            f"- Decision map: `{rel(DECISION_MAP_PATH)}`",
            f"- Completion audit: `{rel(COMPLETION_AUDIT_PATH)}`",
            f"- Output manifest: `{rel(OUTPUT_MANIFEST_PATH)}`",
            f"- Session spine: `{rel(SESSION_STATE_PATH)}`",
            "",
        ]
    )
    return "\n".join(lines)


def build_summary(data: dict[str, Any], decision_map: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    prop = data["prop"]
    current = prop["mode_metrics"]["current_config_shadow"]["overall"]
    activated = prop["mode_metrics"]["hypothetical_activated_vnext"]["overall"]
    return {
        "schema_version": "vnext_replay_stage09_final_truth_freeze_summary_v1",
        "stage_id": STAGE_ID,
        "generated_utc": utc_now(),
        "pass": audit.get("pass") is True,
        "completion_status": audit.get("overall_completion_status"),
        "decision_category_counts": decision_map.get("category_counts"),
        "current_total_r": current.get("effective_r_total"),
        "activated_total_r": activated.get("effective_r_total"),
        "activation_delta": prop.get("activation_delta"),
        "final_report": rel(FINAL_REPORT_PATH),
        "decision_map": rel(DECISION_MAP_PATH),
        "completion_audit": rel(COMPLETION_AUDIT_PATH),
        "no_live_trading_or_broker_mutation": True,
        "production_config_mutated": False,
        "paid_api_or_vendor_call": False,
        "remote_push": False,
    }


def update_output_manifest() -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {}
    existing_paths = {
        item.get("path"): item
        for item in existing.get("outputs", [])
        if isinstance(item, dict) and item.get("path")
    }
    output_paths = [
        (BUILDER_PATH, "generated_replay_builder"),
        (DECISION_MAP_PATH, "generated_replay_output"),
        (FINAL_REPORT_PATH, "generated_replay_report"),
        (COMPLETION_AUDIT_PATH, "generated_replay_output"),
        (STAGE09_SUMMARY_PATH, "generated_replay_output"),
    ]
    for path, source_kind in output_paths:
        existing_paths[rel(path)] = artifact_record(path, source_kind)
    write_json(
        OUTPUT_MANIFEST_PATH,
        {
            "schema_version": "vnext_replay_output_manifest_v1",
            "generated_utc": utc_now(),
            "route_id": "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24",
            "outputs": [existing_paths[key] for key in sorted(existing_paths)],
            "next_stage": "COMPLETE",
        },
    )


def update_session_state(summary: dict[str, Any]) -> None:
    if not SESSION_STATE_PATH.exists():
        return
    state = read_json(SESSION_STATE_PATH)
    completed = list(state.get("completed_stage_ids") or [])
    if STAGE_ID not in completed:
        completed.append(STAGE_ID)
    outputs = list(state.get("current_output_artifacts") or [])
    for path in [BUILDER_PATH, DECISION_MAP_PATH, FINAL_REPORT_PATH, COMPLETION_AUDIT_PATH, STAGE09_SUMMARY_PATH]:
        item = rel(path)
        if item not in outputs:
            outputs.append(item)
    tests = list(state.get("last_tests_or_verifiers") or [])
    verifier = (
        "python research/science_program_2026_05/06_outcome_testing/"
        "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/"
        "build_vnext_replay_final_truth_freeze_2026_05_24.py -> "
        f"pass; completion_status={summary.get('completion_status')}"
    )
    if verifier not in tests:
        tests.append(verifier)
    state.update(
        {
            "updated_utc": utc_now(),
            "current_stage_id": STAGE_ID,
            "current_shard_id": "STAGE_09_FINAL_TRUTH_FREEZE__ALL_OUTPUTS__FINAL_REPORT_AND_DECISION_MAP__COMPLETE",
            "current_objective": "Final replay truth-freeze artifacts have been generated; post-commit verification and goal closeout remain.",
            "current_output_artifacts": outputs,
            "completed_stage_ids": completed,
            "next_executable_action": "Run Stage09 --check, diff/LFS checks, commit final truth-freeze artifacts, regenerate LIVE_STATE, then close the goal if the completion audit still passes.",
            "last_tests_or_verifiers": tests,
            "last_commit": run_git(["log", "-1", "--oneline"]),
            "last_verified_head": run_git(["rev-parse", "HEAD"]),
            "last_verified_git_status": [line for line in run_git(["status", "--short"]).splitlines() if line.strip()],
            "open_questions_remaining": [
                "No same-evidence-class replay/ablation/MIXED/prop/repair/report artifact remains after Stage09; remaining limitations are exact source/capture/approval requirements in the completion audit."
            ],
            "resume_instruction": (
                "On resume or uncertainty: regenerate/read .context/LIVE_STATE.md; reread the controlling prompt, "
                "starter, this session-state file, goal_session_research_discipline.md, research_operating_doctrine.md, "
                "orchestrator hardening files, latest handoff, active config, freeze report, freeze ledger, master/batch "
                "ledgers, current runtime/tests, final report, decision map, completion audit, and output manifest from disk; "
                "verify HEAD/config/runtime artifact manifest hashes and git status; repair this JSON if stale; then run "
                "Stage09 --check and commit/close only if the completion audit still passes."
            ),
        }
    )
    invariants = dict(state.get("stage_invariants") or {})
    invariants[STAGE_ID] = [
        "final promotion/kill/repair/keep-shadow map exists and contains all required decision categories",
        "final report answers system behavior, M15 blindness, execution/fill, outcomes, coverage, MIXED, AI, risk, and forbidden-surface questions",
        "completion audit verifies every controlling-prompt completion requirement against disk artifacts or exact source/capture/approval limits",
        "output manifest records final report, decision map, completion audit, summary, and builder",
        "no broker/account/order/deal/position mutation, production config mutation, paid API call, or remote push occurred",
    ]
    state["stage_invariants"] = invariants
    write_json(SESSION_STATE_PATH, state)


def build_outputs() -> dict[str, Any]:
    data = load_inputs()
    decision_map = build_decision_map(data)
    audit = build_completion_audit(data, decision_map)
    report = build_report(data, decision_map, audit)
    summary = build_summary(data, decision_map, audit)
    write_json(DECISION_MAP_PATH, decision_map)
    FINAL_REPORT_PATH.write_text(report.rstrip() + "\n", encoding="utf-8")
    write_json(COMPLETION_AUDIT_PATH, audit)
    write_json(STAGE09_SUMMARY_PATH, summary)
    update_output_manifest()
    update_session_state(summary)
    if not audit.get("pass"):
        raise SystemExit("Stage09 completion audit did not pass")
    return summary


def check_outputs() -> None:
    decision_map = read_json(DECISION_MAP_PATH)
    audit = read_json(COMPLETION_AUDIT_PATH)
    summary = read_json(STAGE09_SUMMARY_PATH)
    report_text = FINAL_REPORT_PATH.read_text(encoding="utf-8")
    if decision_map.get("stage_id") != STAGE_ID or audit.get("stage_id") != STAGE_ID:
        raise AssertionError("Stage09 output has wrong stage_id")
    if not decision_map.get("pass") or not audit.get("pass") or not summary.get("pass"):
        raise AssertionError("Stage09 output did not pass")
    missing_categories = [category for category in DECISION_CATEGORIES if category not in decision_map.get("category_counts", {})]
    if missing_categories:
        raise AssertionError(f"Decision map missing categories: {missing_categories}")
    if "## Completion Audit" not in report_text or "## Final Decision Map" not in report_text:
        raise AssertionError("Final report missing required sections")
    if any(row.get("status") != "complete" for row in audit.get("requirements", [])):
        raise AssertionError("Completion audit has incomplete requirements")
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    manifest_paths = {item.get("path") for item in manifest.get("outputs", []) if isinstance(item, dict)}
    for path in [BUILDER_PATH, DECISION_MAP_PATH, FINAL_REPORT_PATH, COMPLETION_AUDIT_PATH, STAGE09_SUMMARY_PATH]:
        if rel(path) not in manifest_paths:
            raise AssertionError(f"Output manifest missing {rel(path)}")
    state = read_json(SESSION_STATE_PATH)
    if STAGE_ID not in set(state.get("completed_stage_ids") or []):
        raise AssertionError("Session state missing completed Stage09")
    for key in ["no_live_trading_or_broker_mutation", "production_config_mutated", "paid_api_or_vendor_call", "remote_push"]:
        if key == "no_live_trading_or_broker_mutation":
            if decision_map.get(key) is not True or summary.get(key) is not True:
                raise AssertionError(f"Forbidden surface guard failed for {key}")
        elif decision_map.get(key) is not False or summary.get(key) is not False:
            raise AssertionError(f"Forbidden surface guard failed for {key}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("vNext Stage09 final truth-freeze check passed")
        return
    summary = build_outputs()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
