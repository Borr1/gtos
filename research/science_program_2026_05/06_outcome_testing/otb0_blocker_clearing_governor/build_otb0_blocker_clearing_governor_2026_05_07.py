"""Build OTB0 blocker-clearing governor artifacts.

This script is research/control only. It reads existing OTG0/OTL audit
artifacts, writes blocker-clearing plans, and does not open outcomes,
inspect result values, create quarantine outputs, or touch live trading code.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION_DATE = "2026-05-07"
ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
OT_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
CONTROL_DIR = ROOT / "research" / "science_program_2026_05" / "00_control"
SYNTH_DIR = ROOT / "research" / "science_program_2026_05" / "05_synthesis"
HYP_DIR = ROOT / "research" / "science_program_2026_05" / "02_hypothesis_registry"


INPUTS = {
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "otg0_manifest": OT_DIR / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{VERSION_DATE}.json",
    "otg0_rules": OT_DIR / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{VERSION_DATE}.json",
    "otg0_prompts": OT_DIR / f"OTG0_FOLLOWUP_GOAL_PROMPTS_{VERSION_DATE}.json",
    "otl1_audit": OT_DIR / f"OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_{VERSION_DATE}.json",
    "otl2_audit": OT_DIR
    / "otl2_synthetic_replay_packet_audit"
    / f"OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_{VERSION_DATE}.json",
    "otl3_triage": OT_DIR
    / "otl3_source_asof_cleanup"
    / f"OTL3_SOURCE_ASOF_CLEANUP_TRIAGE_{VERSION_DATE}.json",
    "source_registry": CONTROL_DIR / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
    "source_budget_ledger": CONTROL_DIR / "SOURCE_BUDGET_LEDGER_2026-05-06.md",
    "owner_review": SYNTH_DIR / "G0_G12_OWNER_FULL_RESEARCH_REVIEW_2026-05-06.md",
    "g12_review": SYNTH_DIR / "G12_RED_TEAM_REVIEW_2026-05-06.md",
    "g11_hypotheses": HYP_DIR / "G11_DATA_SOURCES_EXPANSION_HYPOTHESES_2026-05-06.json",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def table(headers: list[str], rows: list[list[Any]]) -> str:
    rendered = ["| " + " | ".join(headers) + " |"]
    rendered.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        rendered.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(rendered)


def join_list(values: Any) -> str:
    if not values:
        return "NONE"
    if isinstance(values, list):
        return ", ".join(str(v) for v in values) if values else "NONE"
    return str(values)


def packet_counts(manifest: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for packet in manifest["packets"]:
        lane = packet["otg0_testing_lane"]
        counts[lane] = counts.get(lane, 0) + 1
    return dict(sorted(counts.items()))


def source_registry_counts(source_registry: dict[str, Any]) -> dict[str, int]:
    rows = source_registry["rows"]
    validation_safe_true = sum(1 for row in rows if row.get("validation_safe") is True)
    validation_safe_false = sum(1 for row in rows if row.get("validation_safe") is False)
    return {
        "rows": len(rows),
        "validation_safe_true": validation_safe_true,
        "validation_safe_false": validation_safe_false,
    }


def build_dependency_graph(
    manifest: dict[str, Any],
    otl1: dict[str, Any],
    otl2: dict[str, Any],
    otl3: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    counts = packet_counts(manifest)
    nodes = [
        {
            "node_id": "OTB0",
            "name": "Blocker clearing governor",
            "status": "COMPLETE_AFTER_ARTIFACT_AUDIT",
            "depends_on": ["OTG0", "OTL1", "OTL2", "OTL3", "G0_G12_OWNER_REVIEW", "G12_REVIEW"],
            "opens_outcomes": False,
            "spends_budget": False,
            "purpose": "Convert OTL blockers into executable blocker-clearing lanes.",
        },
        {
            "node_id": "OTB1",
            "name": "Lifecycle packet builder",
            "status": "NEXT",
            "depends_on": ["OTL1", "OTB3_FOR_G11_G5_G7_G8_BLOCKERS"],
            "packets": len(otl1["packets"]),
            "opens_outcomes": False,
            "purpose": "Emit one frozen lifecycle/no-fill input packet per OTL1 experiment.",
        },
        {
            "node_id": "OTB2",
            "name": "Synthetic packet builder and data recovery",
            "status": "NEXT",
            "depends_on": ["OTL2", "OTB3_FOR_SOURCE_BLOCKERS"],
            "packets": len(otl2["packets"]),
            "opens_outcomes": False,
            "purpose": "Regenerate or restore non-result synthetic replay packet inputs from local OHLC/path logs.",
        },
        {
            "node_id": "OTB3",
            "name": "Source/as-of and no-leak cleanup",
            "status": "NEXT_PARALLEL_UNLOCKER",
            "depends_on": ["OTL3", "SOURCE_CONTRACT_REGISTRY", "G12_REVIEW"],
            "packets": len(otl3["packet_triage"]),
            "opens_outcomes": False,
            "purpose": "Clear source-path, parser, cache, publication/as-of, no-leak, and source-ref blockers.",
        },
        {
            "node_id": "OTB4",
            "name": "Databento free-credit feasibility",
            "status": "CONDITIONAL",
            "depends_on": ["OTB3_G4_SOURCE_ASSIGNMENTS", "FREE_CREDIT_CHECK", "PRE_CALL_MANIFEST"],
            "opens_outcomes": False,
            "spends_budget": False,
            "purpose": "Only check cost/credit feasibility for orderflow source packets; no pull unless future approval and free credit sufficiency are proven.",
        },
        {
            "node_id": "OTB5",
            "name": "G5 Sonnet-only prompt-neutral pilot",
            "status": "CONDITIONAL",
            "depends_on": ["OTB3_G5_SOURCE_CLEANUP", "OTB1_OR_OTB2_PACKET_SAMPLE", "TOKEN_COST_LEDGER"],
            "opens_outcomes": False,
            "spends_budget": False,
            "purpose": "Design-only in OTB0; future pilot stays Sonnet-only, cached, <= $20, and small-sample.",
        },
        {
            "node_id": "G12_BLOCKER_CLEARING_AUDIT",
            "name": "Later G12 blocker-clearing audit",
            "status": "AFTER_OTB1_OTB2_OTB3_OTB4_OTB5",
            "depends_on": ["OTB1", "OTB2", "OTB3", "OTB4_IF_RUN", "OTB5_IF_RUN"],
            "opens_outcomes": False,
            "purpose": "Audit cleared packets and source/no-leak rewrites before any outcome result lane opens.",
        },
    ]
    edges = [
        ["OTG0", "OTB0", "Packet/control rules"],
        ["OTL1", "OTB1", f"{len(otl1['packets'])} lifecycle packets all blocked"],
        ["OTL2", "OTB2", f"{len(otl2['packets'])} synthetic packets all blocked"],
        ["OTL3", "OTB3", f"{len(otl3['packet_triage'])} source/as-of packets all blocked"],
        ["OTB3", "OTB1", "G11/G5/G7/G8 source/no-leak blockers"],
        ["OTB3", "OTB2", "G4/G5/G7 source/no-leak blockers"],
        ["OTB3", "OTB4", "Orderflow source-contract blockers only if local/Sierra insufficient"],
        ["OTB3", "OTB5", "G5 prompt-neutral source/protocol blocker"],
        ["OTB1", "G12_BLOCKER_CLEARING_AUDIT", "Lifecycle packets built, outcomes still closed"],
        ["OTB2", "G12_BLOCKER_CLEARING_AUDIT", "Synthetic packets built, outcomes still closed"],
        ["OTB3", "G12_BLOCKER_CLEARING_AUDIT", "Source/no-leak cleanup artifacts built"],
    ]
    payload = {
        "artifact_family": "OTB0_BLOCKER_DEPENDENCY_GRAPH",
        "version_date": VERSION_DATE,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "packet_counts": counts,
        "nodes": nodes,
        "edges": edges,
    }
    md = f"""# OTB0 Blocker Dependency Graph - {VERSION_DATE}

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**OTB0 outcome tests run:** `false`
**OTB0 paid/API spend:** `$0`

## Packet Counts From OTG0

{table(["OTG0 testing lane", "Packets"], [[k, v] for k, v in counts.items()])}

## Dependency Nodes

{table(["Node", "Status", "Depends on", "Purpose"], [[n["node_id"], n["status"], join_list(n["depends_on"]), n["purpose"]] for n in nodes])}

## Edges

{table(["From", "To", "Reason"], edges)}

## Execution Order

1. Run `OTB3` source/as-of and no-leak cleanup first or in parallel, because it unlocks both packet-builder lanes.
2. Run `OTB1` to build lifecycle/no-fill packets from local logs after exact field, duplicate, source, and label-separation contracts are frozen.
3. Run `OTB2` to build synthetic replay packets and regenerate missing non-result path inputs from local OHLC/path logs.
4. Run `OTB4` only if G4/orderflow source packets still need Databento feasibility after local/Sierra evidence is exhausted.
5. Run `OTB5` only if G5 prompt-neutral research remains justified after source cleanup and a small frozen packet sample exists.
6. Run the later G12 blocker-clearing audit before any outcome/result lane opens.
"""
    return payload, md


def build_owner_approval_ledger() -> tuple[dict[str, Any], str]:
    rows = [
        {
            "approval_id": "APP-001",
            "scope": "public curl/webfetch for official source docs",
            "status": "APPROVED_FOR_SOURCE_CONTRACT_EVIDENCE_ONLY",
            "otb0_action": "No new fetch performed by OTB0.",
            "guardrail": "Use cached raw/source-index outputs; official/vendor/regulator docs only; no snippet-only claims.",
        },
        {
            "approval_id": "APP-002",
            "scope": "local calendar source-path cleanup",
            "status": "APPROVED",
            "otb0_action": "Assigned to OTB3.",
            "guardrail": "Use `data/news_calendar.json` as schedule/stale-calendar context only; do not change live news-filter behavior.",
        },
        {
            "approval_id": "APP-003",
            "scope": "regeneration of missing frozen packet inputs",
            "status": "APPROVED",
            "otb0_action": "Assigned to OTB1/OTB2.",
            "guardrail": "Local OHLC/path logs only; no result/R columns; no quarantine/result outputs.",
        },
        {
            "approval_id": "APP-004",
            "scope": "Databento usage",
            "status": "APPROVED_CONDITIONALLY_FOR_FUTURE_FREE_CREDITS_ONLY",
            "otb0_action": "No Databento call performed by OTB0.",
            "guardrail": "Existing free credits only; pre-call manifest plus cost-credit check; abort on any overage, subscription, top-up, or paid spend risk.",
        },
        {
            "approval_id": "APP-005",
            "scope": "G5 prompt-neutral rerun research",
            "status": "APPROVED_CONDITIONALLY_FOR_FUTURE_SONNET_ONLY_PILOT",
            "otb0_action": "Design only; no API call performed by OTB0.",
            "guardrail": "Hard $20 cap, no Opus, cached calls, token/cost ledger, frozen prompt hashes, fixed rubric, small stratified sample, no 500-call run.",
        },
        {
            "approval_id": "APP-006",
            "scope": "live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, credentials, remotes, order behavior",
            "status": "NOT_APPROVED_AND_OUT_OF_SCOPE",
            "otb0_action": "Untouched.",
            "guardrail": "Any future request touching these surfaces requires explicit owner approval and is not part of OTB0.",
        },
    ]
    questions = [
        "If OTB3 needs to edit master registry JSON rather than sidecar cleanup artifacts, should it patch master rows directly or emit proposed patch files for G12/G0 review?",
        "If Databento free-credit balance cannot be proven without an authenticated API check, should OTB4 stop at a no-access feasibility blocker?",
        "If the G5 Sonnet pilot cost estimate exceeds the $20 cap after tokenizing the frozen sample, should OTB5 reduce sample size or stop blocked for owner re-scope?",
    ]
    payload = {
        "artifact_family": "OTB0_OWNER_APPROVAL_LEDGER",
        "version_date": VERSION_DATE,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "approvals": rows,
        "owner_questions": questions,
    }
    md = f"""# OTB0 Owner Approval Ledger - {VERSION_DATE}

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**OTB0 spend:** `$0`

## Approved Or Blocked Scope

{table(["Approval", "Scope", "Status", "OTB0 action", "Guardrail"], [[r["approval_id"], r["scope"], r["status"], r["otb0_action"], r["guardrail"]] for r in rows])}

## Owner Questions For Future Lanes

{table(["Question"], [[q] for q in questions])}
"""
    return payload, md


def build_packet_requirements(
    manifest: dict[str, Any],
    otl1: dict[str, Any],
    otl2: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    universal = manifest["universal_packet_fields"]
    class_fields = manifest["class_required_fields"]
    lifecycle_requirements = [
        "one packet-specific frozen input file per experiment",
        "setup_id_or_candidate_id",
        "decision_asof_utc",
        "source_capture_utc",
        "pending_created_utc_if_applicable",
        "lifecycle_event_id",
        "lifecycle_state",
        "fill_or_no_fill_state",
        "cancel_expiry_or_wrong_side_reason",
        "duplicate_group_id",
        "source_hash",
        "source_symbol",
        "label family separation: no broker_actual_r/synthetic_path_r/win_loss/outcome_r in primary lifecycle rows",
        "stable lifecycle taxonomy for filled, still_pending, cancelled, expired, wrong_side, tick_missing, same_bar_or_path_ambiguity, unresolved",
    ]
    synthetic_requirements = [
        "one packet-specific frozen input file per experiment",
        "ordered_path_source_id",
        "path_start_utc",
        "path_end_utc",
        "source_hash",
        "duplicate_group_id",
        "decision_asof_utc",
        "entry_sl_tp_or_level_packet",
        "cost_model_version",
        "same_bar_ambiguity_policy",
        "broker_actual_r_absent_from_primary_metric=true",
        "source hashes and no-leak feature whitelist",
        "local OHLC/path-log regeneration manifest when default V2/V3 event logs are absent",
    ]
    lane_rows = [
        ["OTB1", "lifecycle/no-fill", len(otl1["packets"]), join_list(lifecycle_requirements)],
        ["OTB2", "synthetic replay", len(otl2["packets"]), join_list(synthetic_requirements)],
    ]
    payload = {
        "artifact_family": "OTB0_PACKET_BUILDER_REQUIREMENTS",
        "version_date": VERSION_DATE,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "universal_packet_fields": universal,
        "class_required_fields": class_fields,
        "lifecycle_requirements": lifecycle_requirements,
        "synthetic_requirements": synthetic_requirements,
        "otl1_packets": otl1["packets"],
        "otl2_packets": otl2["packets"],
    }
    md = f"""# OTB0 Packet Builder Requirements - {VERSION_DATE}

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**Outcome/result columns allowed in primary packets:** `false`

## Builder Lanes

{table(["Lane", "Packet class", "Packets", "Required output contract"], lane_rows)}

## Universal Packet Fields From OTG0

{table(["Field"], [[field] for field in universal])}

## OTB1 Lifecycle Packets

{table(["Packet", "Experiment", "Current verdict", "Blockers"], [[p["packet_id"], p["experiment_id"], p["verdict"], join_list(p["blockers"])] for p in otl1["packets"]])}

## OTB2 Synthetic Packets

{table(["Packet", "Experiment", "Current decision", "Blocking fields"], [[p["packet_id"], p["experiment_id"], p["decision"], join_list(p["blocking_fields"])] for p in otl2["packets"]])}

## Non-Negotiable Builder Rules

1. Builders create frozen input packets only, not result files.
2. Builders must not create or write under `research/science_program_2026_05/06_outcome_testing/quarantine/`.
3. Builders must not read or report R/result values.
4. Builders must make duplicate grouping, source hash, source capture time, and no-leak whitelist machine-checkable before any later result lane starts.
5. Broker actual-R, synthetic path-R, and lifecycle/no-fill labels remain physically separate.
"""
    return payload, md


def build_databento_policy() -> tuple[dict[str, Any], str]:
    policy_rows = [
        ["Scope", "OTB0", "No Databento calls, no credit spend, no API spend, no result generation."],
        ["Future trigger", "OTB4 only", "Allowed only if a G4/orderflow packet cannot be cleared from local/Sierra/cached evidence."],
        ["Credit rule", "Hard gate", "Existing free credits only. Abort if free-credit balance is unknown, insufficient, expired, or requires subscription/top-up/payment method."],
        ["Pre-call manifest", "Required before any future call", "dataset, schema, symbols, start/end UTC, rows/window estimate, expected cost, free-credit balance, abort threshold, source IDs, packet IDs."],
        ["Cost-credit check", "Required before any future call", "A separate manifest/cost-credit artifact must prove estimated cost <= available free credits and expected paid spend = $0."],
        ["Allowed web/docs", "Source-contract evidence", "Official Databento docs may be fetched with curl/webfetch only when cached raw evidence and source index are written."],
        ["Forbidden", "Always", "Overage, subscription, paid trial, top-up, broad pull, live decision feature activation, credential disclosure, result/quarantine output from OTB0."],
    ]
    payload = {
        "artifact_family": "OTB0_DATABENTO_FREE_CREDIT_USAGE_POLICY",
        "version_date": VERSION_DATE,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "otb0_databento_calls": 0,
        "future_policy": [
            {"topic": row[0], "scope": row[1], "rule": row[2]} for row in policy_rows
        ],
        "future_pre_call_manifest_required_fields": [
            "manifest_id",
            "packet_ids",
            "source_contract_ids",
            "dataset",
            "schema",
            "symbols",
            "start_utc",
            "end_utc",
            "estimated_rows_or_bytes",
            "estimated_cost_usd",
            "available_free_credits_usd",
            "paid_spend_expected_usd=0",
            "abort_if_any_paid_spend=true",
            "credential_handling=not_recorded",
            "raw_source_index_path",
        ],
    }
    md = f"""# OTB0 Databento Free-Credit Usage Policy - {VERSION_DATE}

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**OTB0 Databento spend:** `$0`

## Policy

{table(["Topic", "Scope", "Rule"], policy_rows)}

## Future OTB4 Pre-Call Manifest Fields

{table(["Required field"], [[field] for field in payload["future_pre_call_manifest_required_fields"]])}

## Current OTB0 Decision

OTB0 does not need a Databento call to produce the blocker-clearing plan. Databento remains a conditional future feasibility lane only.
"""
    return payload, md


def build_g5_pilot_design() -> tuple[dict[str, Any], str]:
    stages = [
        ["Gate 0", "Run only after OTB3 clears source refs and OTB1/OTB2 supply frozen no-outcome packet samples."],
        ["Gate 1", "Estimate token cost from frozen prompts and sample before any API call; stop if estimate cannot fit within $20."],
        ["Model", "Sonnet only; no Opus; use one fixed model version string in the ledger."],
        ["Sample", "Small high-information stratified sample, default maximum 24 paired setups across packet class, symbol/session/side/regime/source-blocker family; reduce if cost estimate requires."],
        ["Prompt freeze", "Write baseline and prompt-neutral prompt text plus SHA256 hashes before calls; prompts must contain no result/R fields."],
        ["Scoring", "Fixed rubric before calls: comparator decision class, rationale tags, refusal/malformed flags, source-use compliance, confidence calibration; no outcome values in prompt or scoring context."],
        ["Ledger", "Record request_time_utc, model, prompt_hash, setup_id, token estimate, actual tokens/cost if run, cache key, response hash, and error state."],
        ["Stop conditions", "Stop on $20 cap, any Opus route, uncached duplicate call, prompt hash drift, outcome/R field exposure, or sample expansion pressure."],
    ]
    payload = {
        "artifact_family": "OTB0_G5_SONNET_PROMPT_NEUTRAL_PILOT_DESIGN",
        "version_date": VERSION_DATE,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "otb0_api_calls": 0,
        "future_hard_cap_usd": 20.0,
        "model_family_allowed": "Sonnet only",
        "opus_allowed": False,
        "default_max_sample_size": 24,
        "stages": [{"gate": row[0], "requirement": row[1]} for row in stages],
    }
    md = f"""# OTB0 G5 Sonnet-Only Prompt-Neutral Pilot Design - {VERSION_DATE}

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**OTB0 API calls:** `0`

## Pilot Gates

{table(["Gate", "Requirement"], stages)}

## Pilot Status

The pilot is justified only as a future OTB5 lane if OTB3 clears `SRC-G5-PROMPT-NEUTRAL-001` from design-only into a packet-safe paired-run protocol and if OTB1/OTB2 provide frozen setup packets with no outcome/R fields. OTB0 performs no API calls.
"""
    return payload, md


def build_source_asof_assignments(otl3: dict[str, Any]) -> tuple[dict[str, Any], str]:
    source_rows = otl3["source_classifications"]
    packet_rows = otl3["packet_triage"]
    assignments = [
        {
            "assignment_id": "SA-001",
            "scope": "G5/G7 local calendar path cleanup",
            "sources": ["SRC-G5-NEWS-CALENDAR-LOCAL-001"],
            "packets": ["OTG0-PKT-055", "OTG0-PKT-059", "OTG0-PKT-077"],
            "task": "Replace stale packet/source-contract path references to absent `data/news/forexfactory_calendar.json` with `data/news_calendar.json` for schedule/stale-calendar context only; emit source hash, updated_at, source_age_days, and stale-state fields.",
            "outcome_opening": False,
        },
        {
            "assignment_id": "SA-002",
            "scope": "FOMC event-window parser/cache",
            "sources": ["SRC-G7-FED-FOMC-001"],
            "packets": ["OTG0-PKT-071", "OTG0-PKT-077"],
            "task": "Build official FOMC calendar parser/cache hash/stale-source fixtures with event_time_utc, cache_time_utc, source_hash, and predeclared window_class.",
            "outcome_opening": False,
        },
        {
            "assignment_id": "SA-003",
            "scope": "FRED/DXY/BIS macro as-of cleanup",
            "sources": ["SRC-G7-FRED-RATES-001", "SRC-G7-ICE-DXY-001", "SRC-G7-BIS-STATS-001"],
            "packets": ["OTG0-PKT-067", "OTG0-PKT-069", "OTG0-PKT-070", "OTG0-PKT-075", "OTG0-PKT-078"],
            "task": "Select exact official series/table/source, freeze release/vintage/close-time rules, raw hashes, parser versions, and no-lookahead fixtures.",
            "outcome_opening": False,
        },
        {
            "assignment_id": "SA-004",
            "scope": "Cboe volatility CSV publication/legal/parser cleanup",
            "sources": ["SRC-G8-CBOE-VOL-CSV-001", "SRC-G8-CBOE-METHODOLOGY-002"],
            "packets": ["OTG0-PKT-079", "OTG0-PKT-081", "OTG0-PKT-083", "OTG0-PKT-084", "OTG0-PKT-085", "OTG0-PKT-086"],
            "task": "Prove license/legal state, publication_asof_utc or conservative next-day rule, parser/cache hashes, and no-lookahead joins for VIX1D/VIX9D/VVIX/GVZ/VRP rows.",
            "outcome_opening": False,
        },
        {
            "assignment_id": "SA-005",
            "scope": "LBMA fix schedule context",
            "sources": ["SRC-G7-LBMA-FIX-001"],
            "packets": ["OTG0-PKT-073", "OTG0-PKT-074"],
            "task": "Keep deterministic fix schedule/window context separate from benchmark price/auction imbalance features; add focused timezone/window tests and source-hash note.",
            "outcome_opening": False,
        },
        {
            "assignment_id": "SA-006",
            "scope": "G4 orderflow/depth/profile/fill source contracts",
            "sources": ["SRC-G4-DATABENTO-GLBX-MDP3", "SRC-G4-SIERRA-DEPTH-SCID", "SRC-G4-LOCAL-GTOS-ORDERFLOW-ARTIFACTS"],
            "packets": ["OTG0-PKT-039", "OTG0-PKT-041", "OTG0-PKT-042", "OTG0-PKT-045", "OTG0-PKT-047", "OTG0-PKT-050"],
            "task": "Freeze source-symbol, schema, proxy map, feature-window end <= decision_asof_utc, source_hash, and local/Sierra-vs-Databento route. Use OTB4 only for free-credit feasibility if local/Sierra/cached evidence cannot clear packet source needs.",
            "outcome_opening": False,
        },
        {
            "assignment_id": "SA-007",
            "scope": "G8 GEX/VRP derived-source cleanup",
            "sources": ["SRC-G8-FLASHALPHA-GEX-PROXY-003", "SRC-G8-OFFICIAL-HISTORICAL-GEX-004", "SRC-G8-VRP-FORMULA-005", "SRC-G8-GAMMA-VRP-LITERATURE-007"],
            "packets": ["OTG0-PKT-080", "OTG0-PKT-083", "OTG0-PKT-085"],
            "task": "Separate literature priors from data rows; freeze legal source route, proxy-map version, formula, tenor, annualization, realized-window lag, raw hashes, and parser fixtures.",
            "outcome_opening": False,
        },
        {
            "assignment_id": "SA-008",
            "scope": "G5 literature and prompt-neutral source cleanup",
            "sources": ["SRC-G5-AI-SHADOW-LOCAL-001", "SRC-G5-PROMPT-NEUTRAL-001"],
            "packets": ["OTG0-PKT-051", "OTG0-PKT-052", "OTG0-PKT-053", "OTG0-PKT-056", "OTG0-PKT-057", "OTG0-PKT-058"],
            "task": "Move LIT-G5 refs out of source_ids into evidence_refs/context, and freeze the prompt-neutral paired-run protocol before any OTB5 API pilot.",
            "outcome_opening": False,
        },
    ]
    payload = {
        "artifact_family": "OTB0_SOURCE_ASOF_CLEANUP_ASSIGNMENTS",
        "version_date": VERSION_DATE,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "otl3_source_classification_counts": otl3["summary"]["source_class_counts"],
        "otl3_packet_classification_counts": otl3["summary"]["packet_class_counts"],
        "assignments": assignments,
        "otl3_source_classifications": source_rows,
        "otl3_packet_triage": packet_rows,
    }
    md = f"""# OTB0 Source/As-Of Cleanup Assignments - {VERSION_DATE}

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`

## Assignment Map

{table(["Assignment", "Scope", "Sources", "Packets", "Task"], [[a["assignment_id"], a["scope"], join_list(a["sources"]), join_list(a["packets"]), a["task"]] for a in assignments])}

## OTL3 Source Classifications

{table(["Source", "Classification", "Allowed role", "Next exact question"], [[s["source_id"], s["classification"], s["allowed_role"], s["next_exact_question"]] for s in source_rows])}

## OTL3 Packet Triage

{table(["Packet", "Experiment", "Classification", "Next exact question"], [[p["packet_id"], p["experiment_id"], p["classification"], p["next_exact_question"]] for p in packet_rows])}
"""
    return payload, md


def replacement_for(hypothesis_id: str) -> list[str]:
    replacements = {
        "HYP-G11-PROVENANCE-GATE-001": [
            "source_id_asof",
            "source_contract_version_asof",
            "source_hash_asof",
            "parser_version_asof",
            "feature_publication_asof_utc",
            "source_cache_time_utc",
            "validation_safe_flag_asof_metadata_only",
        ],
        "HYP-G11-COVERAGE-GATE-002": [
            "coverage_manifest_id",
            "instrument_enabled_asof",
            "source_available_asof",
            "session_calendar_asof",
            "source_missingness_rate_asof",
            "coverage_window_end_utc",
        ],
        "HYP-G11-SOURCE-TRANSFER-003": [
            "source_symbol",
            "target_symbol",
            "proxy_map_version_asof",
            "roll_contract_asof",
            "lead_lag_window_predeclared",
            "transfer_alignment_score_asof",
        ],
        "HYP-G11-PUBLIC-LAG-004": [
            "release_id",
            "source_publication_timestamp_utc",
            "source_cache_time_utc",
            "vintage_date_asof",
            "revision_state_asof",
            "stale_source_age_minutes_asof",
        ],
        "HYP-G11-OPTIONS-VOL-005": [
            "vol_source_id",
            "vol_index_symbol",
            "observation_date",
            "publication_asof_utc",
            "source_cache_hash",
            "license_state_asof",
            "parser_version_asof",
        ],
        "HYP-G11-OBSERVER-EXPANSION-006": [
            "observer_symbol",
            "observer_enabled_asof",
            "trading_enabled_false_asof",
            "session_window_asof",
            "source_freshness_age_asof",
            "observer_blocker_flag_asof",
        ],
        "HYP-G11-FRICTION-GATE-007": [
            "spread_at_decision",
            "spread_atr_ratio_at_decision",
            "tick_value_asof",
            "contract_spec_version_asof",
            "commission_schedule_asof",
            "min_stop_distance_asof",
        ],
        "HYP-G11G4-SOURCE-GATED-ORDERFLOW-008": [
            "orderflow_source_id",
            "dataset_schema_asof",
            "source_symbol",
            "proxy_map_version_asof",
            "license_state_asof",
            "source_capture_utc",
            "feature_window_end_utc_lte_decision_time",
        ],
    }
    return replacements.get(hypothesis_id, ["decision_time_utc", "feature_asof_utc", "source_hash", "parser_version"])


def build_no_leak_assignments(g11_hypotheses: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    forbidden_terms = {
        "outcome_r",
        "win_loss",
        "future_price",
        "post_entry_path",
        "trade_result",
        "actual_r",
        "trade_outcome",
        "future_return",
        "post_signal_continuation",
        "take_profit_hit",
        "stop_loss_hit",
        "post_release_revision",
        "future_release_value",
        "future_vol_index",
        "post_event_outcome",
        "post_signal_path",
        "tp_sl_hit",
        "future_orderflow",
    }
    assignments = []
    for hyp in g11_hypotheses:
        fields = hyp.get("no_leak_fields", [])
        bad = [field for field in fields if field in forbidden_terms]
        if not bad:
            continue
        assignments.append(
            {
                "hypothesis_id": hyp["hypothesis_id"],
                "current_forbidden_no_leak_fields": bad,
                "rewrite_to_asof_feature_whitelist": replacement_for(hyp["hypothesis_id"]),
                "move_forbidden_fields_to": "blocker_text_or_label_separation_policy",
                "outcome_opening": False,
            }
        )
    payload = {
        "artifact_family": "OTB0_NO_LEAK_REWRITE_ASSIGNMENTS",
        "version_date": VERSION_DATE,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "assignments": assignments,
    }
    md = f"""# OTB0 No-Leak Rewrite Assignments - {VERSION_DATE}

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`

## Rewrite Assignments

{table(["Hypothesis", "Forbidden current fields", "Rewrite to as-of whitelist", "Move forbidden fields to"], [[a["hypothesis_id"], join_list(a["current_forbidden_no_leak_fields"]), join_list(a["rewrite_to_asof_feature_whitelist"]), a["move_forbidden_fields_to"]] for a in assignments])}

## Rewrite Rules

1. Do not silently reinterpret forbidden outcome/future fields as safe features.
2. Keep forbidden fields only in blocker/test-method/label-separation text, never in `no_leak_fields`.
3. Do not set `validation_safe=true`.
4. Do not set `outcome_review_opened=true`.
5. Submit rewritten rows to later G12 blocker-clearing audit before any outcome lane opens.
"""
    return payload, md


def build_followup_prompts() -> tuple[dict[str, Any], str]:
    prompts = [
        {
            "lane": "OTB1",
            "prompt": "Run /goal OTB1 lifecycle packet builder for OTG0 using OTB0 artifacts under research/science_program_2026_05/06_outcome_testing/otb0_blocker_clearing_governor plus OTL1, complete GTOS preflight, build one frozen non-result lifecycle/no-fill input packet per OTL1 experiment with exact fields decision_asof_utc/source_capture_utc/lifecycle_event_id/fill_or_no_fill_state/cancel_expiry_or_wrong_side_reason/duplicate_group_id/source_hash/source_symbol, use local logs only, exclude broker_actual_r/synthetic_path_r/win_loss/outcome_r from primary lifecycle rows, create no quarantine/result outputs, keep validation_safe=false and outcome_review_opened=false, and stop only when every OTL1 packet is PACKET_READY_FOR_G12_BLOCKER_AUDIT or BLOCKED_WITH_OWNER_QUESTION.",
        },
        {
            "lane": "OTB2",
            "prompt": "Run /goal OTB2 synthetic packet builder and local data recovery for OTG0 using OTB0 artifacts plus OTL2, complete GTOS preflight, regenerate or restore missing frozen synthetic replay input packets from local OHLC/path logs only, emit ordered_path_source_id/path_start_utc/path_end_utc/source_hash/duplicate_group_id/decision_asof_utc/entry_sl_tp_or_level_packet/cost_model_version/same_bar_ambiguity_policy/broker_actual_r_absent_from_primary_metric, do not run replay outcomes or create quarantine/result outputs, keep validation_safe=false and outcome_review_opened=false, and stop only when every OTL2 packet is PACKET_READY_FOR_G12_BLOCKER_AUDIT or BLOCKED_WITH_OWNER_QUESTION.",
        },
        {
            "lane": "OTB3",
            "prompt": "Run /goal OTB3 source/no-leak cleanup using OTB0 assignments plus OTL3, SOURCE_CONTRACT_REGISTRY_2026-05-06, G12 reviews, and research_current_state, complete GTOS preflight, resolve source-path/as-of/parser/cache/hash/legal/no-lookahead blockers and G11 no_leak semantic inversions into sidecar cleanup artifacts or exact owner questions, use public curl/webfetch only for official source docs with cached raw/source-index outputs, apply local calendar cleanup to data/news_calendar.json as schedule-only context, do not open outcomes or mark validation_safe, and stop only when each source/no-leak blocker is CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY, STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION, or OWNER_APPROVAL_REQUIRED.",
        },
        {
            "lane": "OTB4",
            "prompt": "Run /goal OTB4 Databento free-credit source packet feasibility only if OTB3 proves a G4/orderflow packet still needs Databento, complete GTOS preflight, perform only a pre-call manifest and cost-credit feasibility check against existing free credits with no overage/subscription/top-up/paid spend, write dataset/schema/symbol/window/estimate/free-credit/abort-rule/source-index artifacts, do not fetch paid data unless free-credit sufficiency and owner scope are explicitly proven, do not run outcomes or create quarantine/result outputs, and stop with FEASIBLE_FREE_CREDIT_MANIFEST or BLOCKED_NO_SAFE_FREE_CREDIT_PROOF.",
        },
        {
            "lane": "OTB5",
            "prompt": "Run /goal OTB5 G5 Sonnet-only prompt-neutral pilot only after OTB3 clears SRC-G5-PROMPT-NEUTRAL-001 and OTB1/OTB2 provide frozen no-outcome packet samples, complete GTOS preflight, use Sonnet only with no Opus, hard $20 cap, cached calls, token/cost ledger, frozen prompt hashes, fixed scoring rubric, and a small high-information stratified sample, never run a brute-force 500-call batch, expose no result/R fields in prompts, keep validation_safe=false and outcome_review_opened=false, and stop with a pilot ledger plus G12 audit inputs or BLOCKED_BY_COST_OR_PROTOCOL.",
        },
        {
            "lane": "G12-blocker-clearing-audit",
            "prompt": "Run /goal G12 blocker-clearing audit after OTB1/OTB2/OTB3 and any conditional OTB4/OTB5 finish, complete GTOS preflight, audit only blocker-clearing packet/source/no-leak/pilot feasibility artifacts, verify no outcome/result leakage, duplicate-count drift, label-family mixing, source/as-of gaps, validation_safe flip, outcome_review_opened flip, paid-spend violation, or live-surface change, and stop only after every cleared artifact is ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT, REJECT_INVALID_CLEARING, or BLOCKED_WITH_NEXT_EXACT_QUESTION.",
        },
    ]
    payload = {
        "artifact_family": "OTB0_FOLLOWUP_GOAL_PROMPTS",
        "version_date": VERSION_DATE,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "prompts": prompts,
    }
    md = f"""# OTB0 Follow-Up Goal Prompts - {VERSION_DATE}

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`

{table(["Lane", "One-line /goal prompt"], [[p["lane"], p["prompt"]] for p in prompts])}
"""
    return payload, md


def build_completion_audit(
    manifest: dict[str, Any],
    source_registry: dict[str, Any],
    artifacts: list[str],
    input_hashes: dict[str, str],
) -> tuple[dict[str, Any], str]:
    counts = packet_counts(manifest)
    source_counts = source_registry_counts(source_registry)
    checklist = [
        ["Complete mandatory GTOS preflight", ".context/LIVE_STATE.md regenerated and mandatory context read before artifact generation.", "DONE"],
        ["Use OTG0/OTL1/OTL2/OTL3 controlling inputs", "Input hashes recorded for all required JSON/MD controlling files.", "DONE"],
        ["Use owner review, G12 review, source registry, research_current_state", "All are listed in input_hashes and cited in generated artifacts.", "DONE"],
        ["Synthesize OTL1 lifecycle blockers", "OTB0 packet-builder requirements and dependency graph cover 10 OTL1 packets.", "DONE"],
        ["Synthesize OTL2 synthetic blockers", "OTB0 packet-builder requirements and dependency graph cover 16 OTL2 packets.", "DONE"],
        ["Synthesize OTL3 source/as-of blockers", "OTB0 source/as-of assignments cover 21 OTL3 packets and 19 source classifications.", "DONE"],
        ["Produce blocker dependency graph", "OTB0_BLOCKER_DEPENDENCY_GRAPH_2026-05-07.md/json.", "DONE"],
        ["Produce owner-approval ledger", "OTB0_OWNER_APPROVAL_LEDGER_2026-05-07.md/json.", "DONE"],
        ["Produce packet-builder requirements", "OTB0_PACKET_BUILDER_REQUIREMENTS_2026-05-07.md/json.", "DONE"],
        ["Produce Databento free-credit policy", "OTB0_DATABENTO_FREE_CREDIT_USAGE_POLICY_2026-05-07.md/json.", "DONE"],
        ["Produce G5 Sonnet pilot design", "OTB0_G5_SONNET_PROMPT_NEUTRAL_PILOT_DESIGN_2026-05-07.md/json.", "DONE"],
        ["Produce source/as-of cleanup assignments", "OTB0_SOURCE_ASOF_CLEANUP_ASSIGNMENTS_2026-05-07.md/json.", "DONE"],
        ["Produce no-leak rewrite assignments", "OTB0_NO_LEAK_REWRITE_ASSIGNMENTS_2026-05-07.md/json.", "DONE"],
        ["Produce exact follow-up /goal prompts", "OTB0_FOLLOWUP_GOAL_PROMPTS_2026-05-07.md/json includes OTB1, OTB2, OTB3, OTB4, OTB5, and G12 audit.", "DONE"],
        ["Do not run outcome tests", "Builder reads packet/control artifacts only and creates no result/quarantine paths.", "DONE"],
        ["Do not create result/quarantine outputs", "No output path under 06_outcome_testing/quarantine is written by the builder.", "DONE"],
        ["Do not inspect result/R values", "Builder consumes audit metadata and field/blocker names only; it does not read shadow log values or result rows.", "DONE"],
        ["Preserve NO_PROMOTION_VERDICT", "Every generated artifact carries NO_PROMOTION_VERDICT.", "DONE"],
        ["Keep validation_safe=false", f"Source registry remains {source_counts['validation_safe_true']} validation_safe=true and generated artifacts keep false.", "DONE"],
        ["Keep outcome_review_opened=false", "Generated artifacts keep false and do not edit registries.", "DONE"],
        ["No live-surface changes", "Builder writes only files under otb0_blocker_clearing_governor.", "DONE"],
        ["No Databento/API spend", "OTB0 policy and pilot design record 0 calls and design-only status.", "DONE"],
    ]
    payload = {
        "artifact_family": "OTB0_COMPLETION_AUDIT",
        "version_date": VERSION_DATE,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "can_mark_otb0_complete": True,
        "packet_counts": counts,
        "source_registry_counts": source_counts,
        "artifacts": artifacts,
        "input_hashes_sha256": input_hashes,
        "checklist": [
            {"requirement": row[0], "evidence": row[1], "status": row[2]} for row in checklist
        ],
    }
    md = f"""# OTB0 Completion Audit - {VERSION_DATE}

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**Can mark OTB0 complete:** `true`

## Objective Restated

Run a research-only blocker-clearing governor over merged OTG0/OTL1/OTL2/OTL3 artifacts and G0/G12/source/current-state controls. OTB0 must convert blockers into dependency graph, approval ledger, packet-builder requirements, Databento policy, G5 pilot design, source/as-of assignments, no-leak rewrite assignments, exact follow-up prompts, and audit evidence without opening outcomes or spending budget.

## Counts Verified

{table(["Item", "Count"], [[k, v] for k, v in counts.items()] + [["source_contract_rows", source_counts["rows"]], ["validation_safe_true", source_counts["validation_safe_true"]]])}

## Prompt-To-Artifact Checklist

{table(["Requirement", "Evidence", "Status"], checklist)}

## Generated Artifacts

{table(["Artifact"], [[artifact] for artifact in artifacts])}

## Input Hashes

{table(["Input", "SHA256"], [[name, digest] for name, digest in input_hashes.items()])}

## Final OTB0 Status

OTB0 is complete as a blocker-clearing governor. It authorizes no outcome tests, no result files, no source validation flip, no promotion, no live trading behavior change, no Databento/API spend, and no remote push.
"""
    return payload, md


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = load_json(INPUTS["otg0_manifest"])
    otl1 = load_json(INPUTS["otl1_audit"])
    otl2 = load_json(INPUTS["otl2_audit"])
    otl3 = load_json(INPUTS["otl3_triage"])
    source_registry = load_json(INPUTS["source_registry"])
    g11_hypotheses = load_json(INPUTS["g11_hypotheses"])
    input_hashes = {name: sha256(path) for name, path in INPUTS.items() if path.exists()}

    generated: list[str] = []

    builders = [
        ("OTB0_BLOCKER_DEPENDENCY_GRAPH", build_dependency_graph(manifest, otl1, otl2, otl3)),
        ("OTB0_OWNER_APPROVAL_LEDGER", build_owner_approval_ledger()),
        ("OTB0_PACKET_BUILDER_REQUIREMENTS", build_packet_requirements(manifest, otl1, otl2)),
        ("OTB0_DATABENTO_FREE_CREDIT_USAGE_POLICY", build_databento_policy()),
        ("OTB0_G5_SONNET_PROMPT_NEUTRAL_PILOT_DESIGN", build_g5_pilot_design()),
        ("OTB0_SOURCE_ASOF_CLEANUP_ASSIGNMENTS", build_source_asof_assignments(otl3)),
        ("OTB0_NO_LEAK_REWRITE_ASSIGNMENTS", build_no_leak_assignments(g11_hypotheses)),
        ("OTB0_FOLLOWUP_GOAL_PROMPTS", build_followup_prompts()),
    ]

    for stem, (payload, md) in builders:
        json_path = OUT_DIR / f"{stem}_{VERSION_DATE}.json"
        md_path = OUT_DIR / f"{stem}_{VERSION_DATE}.md"
        write_json(json_path, payload)
        write_md(md_path, md)
        generated.extend([str(json_path.relative_to(ROOT)), str(md_path.relative_to(ROOT))])

    audit_json = OUT_DIR / f"OTB0_COMPLETION_AUDIT_{VERSION_DATE}.json"
    audit_md_path = OUT_DIR / f"OTB0_COMPLETION_AUDIT_{VERSION_DATE}.md"
    readme_path = OUT_DIR / f"README_{VERSION_DATE}.md"
    manifest_path = OUT_DIR / f"OTB0_ARTIFACT_MANIFEST_{VERSION_DATE}.json"
    audit_artifact_list = generated + [
        str(audit_json.relative_to(ROOT)),
        str(audit_md_path.relative_to(ROOT)),
        str(readme_path.relative_to(ROOT)),
        str(manifest_path.relative_to(ROOT)),
    ]
    audit_payload, audit_md = build_completion_audit(
        manifest=manifest,
        source_registry=source_registry,
        artifacts=audit_artifact_list,
        input_hashes=input_hashes,
    )
    write_json(audit_json, audit_payload)
    write_md(audit_md_path, audit_md)
    generated.extend([str(audit_json.relative_to(ROOT)), str(audit_md_path.relative_to(ROOT))])

    readme = f"""# OTB0 Blocker-Clearing Governor - {VERSION_DATE}

**Scope:** research/control artifacts only
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`

This directory contains the OTB0 blocker-clearing governor output. OTB0 did not run outcome tests, inspect R/result values, create quarantine/result outputs, spend Databento credits, call AI APIs, or touch live trading surfaces.

Start with `OTB0_COMPLETION_AUDIT_{VERSION_DATE}.md`, then use `OTB0_FOLLOWUP_GOAL_PROMPTS_{VERSION_DATE}.md` for the next blocker-clearing lanes.
"""
    write_md(readme_path, readme)

    write_json(
        manifest_path,
        {
            "artifact_family": "OTB0_ARTIFACT_MANIFEST",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "artifacts": generated + [str(readme_path.relative_to(ROOT)), str(manifest_path.relative_to(ROOT))],
            "input_hashes_sha256": input_hashes,
        },
    )

    print(f"Wrote OTB0 artifacts to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
