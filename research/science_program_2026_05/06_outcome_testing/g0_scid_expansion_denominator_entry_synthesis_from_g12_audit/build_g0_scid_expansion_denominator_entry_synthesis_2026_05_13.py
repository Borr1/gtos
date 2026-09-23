"""Build G0 expansion denominator-entry/source-materialization synthesis.

This route selects and sequences future source/control routes for quarantined
expansion families. It does not open validation, result scoring, broker
evidence, paid/API access, raw market blob commits, live restarts, or trading
decision behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
R4_DIR = OUTCOME_DIR / "scid_expansion_candidate_acceptance_and_design_route"
G12_DIR = OUTCOME_DIR / "g12_scid_expansion_candidate_acceptance_design_audit"
ANTI_DIR = OUTCOME_DIR / "scid_noapi_cross_domain_anti_boxing_route_intake"
G12_ANTI_DIR = OUTCOME_DIR / "g12_scid_anti_boxing_route_intake_audit"

DATE_TAG = "2026-05-13"
PREFIX = "G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS"
ROUTE_ID = "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_FROM_G12_AUDIT"
EVIDENCE_CLASS = "G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_ONLY"
SCHEMA_VERSION = "g0_scid_expansion_denominator_entry_synthesis_v1"
TERMINAL_DECISION = "ACCEPT_AS_G0_SCID_EXPANSION_DENOMINATOR_ENTRY_SYNTHESIS_WITH_QUARANTINED_ROUTE_PLAN"

FORBIDDEN_SURFACES = (
    "validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/"
    "paid-vendor/broker-account-order-history-deal-position/raw-market-blob/"
    "live-restart/live-behavior/trading-risk-safety-prompt-decision changes"
)

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

PROMPT_CONTEXT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_CANDIDATE_INVENTORY_2026-05-12.json",
    "research/science_program_2026_05/06_outcome_testing/g12_scid_expansion_candidate_acceptance_design_audit/G12_SCID_EXPANSION_AUDIT_DECISION_LEDGER_2026-05-12.json",
]

ROUTE_PACKS: list[dict[str, Any]] = [
    {
        "rank": 1,
        "route_id": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL",
        "route_title": "Local Heavy Root, Parser, Hash, And Lineage Source-Control Route",
        "evidence_class": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY",
        "prompt_file": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_GOAL_PROMPT_2026-05-13.md",
        "starter_file": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_STARTER_2026-05-13.txt",
        "candidate_ids": ["R4-EXP-ROOT-001", "R4-EXP-PARSER-001", "EXP-ADV-001", "R4-EXP-CODEHIST-001"],
        "overflow_route_family_ids": ["ADV-002", "MISS-002", "FAIL-003"],
        "objective": (
            "Materialize source-root coverage, parser/schema fingerprints, hash/deferral policy, and route-lineage "
            "controls needed before any expansion family can enter a future denominator."
        ),
        "outputs": [
            "source-root search and hash-deferral ledger",
            "parser/version/shape-fingerprint matrix",
            "artifact-lineage manifest binding proof",
            "no raw-market-blob commit audit",
        ],
        "why_ranked": "Foundational: every later source-materialization route depends on root, parser, hash, and lineage integrity.",
    },
    {
        "rank": 2,
        "route_id": "G0EXP_R2_DENOMINATOR_ROWSET_PARTITION_MISSINGNESS_SOURCE_CONTROL",
        "route_title": "Denominator, Rowset, Partition, And Missingness Source-Control Route",
        "evidence_class": "G0EXP_R2_DENOMINATOR_ROWSET_PARTITION_MISSINGNESS_SOURCE_CONTROL_ONLY",
        "prompt_file": "G0EXP_R2_DENOMINATOR_ROWSET_PARTITION_MISSINGNESS_SOURCE_CONTROL_GOAL_PROMPT_2026-05-13.md",
        "starter_file": "G0EXP_R2_DENOMINATOR_ROWSET_PARTITION_MISSINGNESS_SOURCE_CONTROL_STARTER_2026-05-13.txt",
        "candidate_ids": [
            "EXP-DENOM-001",
            "EXP-MISS-001",
            "G0-EXP-PARTITION-001",
            "G0-EXP-DOMAIN-MISSINGNESS-001",
            "G0-EXP-ROWSET-001",
            "R4-EXP-CAPGROUP-001",
        ],
        "overflow_route_family_ids": ["ADV-001", "MISS-001", "MISS-003", "MISS-004"],
        "objective": (
            "Freeze denominator keys, rowset materialization controls, source missingness strata, partition/embargo "
            "hygiene, and capture-group gap intersection rules without opening outcomes."
        ),
        "outputs": [
            "candidate and duplicate-key denominator ledger",
            "rowset materialization failure-mode ledger",
            "source missingness and domain-intersection controls",
            "partition/embargo prerequisite checklist",
        ],
        "why_ranked": "Closest to denominator-entry mechanics while keeping accepted-40 and expansion denominators separate.",
    },
    {
        "rank": 3,
        "route_id": "G0EXP_R3_LTF_ORDERFLOW_PROXY_BASIS_ALIAS_COST_SOURCE_STATUS",
        "route_title": "LTF, Orderflow, Proxy, Basis, Alias, And Cost Source-Status Route",
        "evidence_class": "G0EXP_R3_LTF_ORDERFLOW_PROXY_BASIS_ALIAS_COST_SOURCE_STATUS_ONLY",
        "prompt_file": "G0EXP_R3_LTF_ORDERFLOW_PROXY_BASIS_ALIAS_COST_SOURCE_STATUS_GOAL_PROMPT_2026-05-13.md",
        "starter_file": "G0EXP_R3_LTF_ORDERFLOW_PROXY_BASIS_ALIAS_COST_SOURCE_STATUS_STARTER_2026-05-13.txt",
        "candidate_ids": ["EXP-LTF-001", "EXP-PROXY-001", "R4-EXP-ALIAS-001", "R4-EXP-BASIS-001"],
        "overflow_route_family_ids": ["MICRO-001", "MICRO-003", "EXEC-002"],
        "objective": (
            "Materialize LTF availability, orderflow/depth/proxy source status, contract aliases, roll/session maps, "
            "and futures-CFD basis boundaries as source controls only."
        ),
        "outputs": [
            "LTF availability and parser-readiness matrix",
            "proxy/source family validity ledger",
            "alias/contract-roll/session mapping contract",
            "futures-CFD transfer boundary proof",
        ],
        "why_ranked": "Keeps non-OB microstructure/source expansion alive while preventing futures proxy evidence from becoming broker-CFD truth.",
    },
    {
        "rank": 4,
        "route_id": "G0EXP_R4_NEGATIVE_PLACEBO_FAILURE_CONTROL_SOURCE_CONTRACT",
        "route_title": "Negative Evidence, Placebo, And Failure-Anatomy Source-Control Route",
        "evidence_class": "G0EXP_R4_NEGATIVE_PLACEBO_FAILURE_CONTROL_SOURCE_CONTRACT_ONLY",
        "prompt_file": "G0EXP_R4_NEGATIVE_PLACEBO_FAILURE_CONTROL_SOURCE_CONTRACT_GOAL_PROMPT_2026-05-13.md",
        "starter_file": "G0EXP_R4_NEGATIVE_PLACEBO_FAILURE_CONTROL_SOURCE_CONTRACT_STARTER_2026-05-13.txt",
        "candidate_ids": ["G0-EXP-NEGCTRL-001", "R4-EXP-NEG-001", "R4-EXP-PLACEBO-001"],
        "overflow_route_family_ids": ["ADV-004", "FAIL-001", "GEOM-TOPO-001"],
        "objective": (
            "Turn negative evidence, placebo/shuffle controls, and failure anatomy into exact source contracts and "
            "matched-control templates before any future scoring lane."
        ),
        "outputs": [
            "negative-evidence class and missing-source ledger",
            "placebo/shuffle/matched-control template manifest",
            "failure-anatomy source-contract matrix",
            "future result-gate exclusion rules",
        ],
        "why_ranked": "Prevents broad expansion from becoming narrative-only by forcing adversarial controls and failure anatomy into the route plan.",
    },
    {
        "rank": 5,
        "route_id": "G0EXP_R5_CLOCK_CALENDAR_MACRO_COST_ASOF_SOURCE_CONTROL",
        "route_title": "Clock, Calendar, Macro, News, And Cost As-Of Source-Control Route",
        "evidence_class": "G0EXP_R5_CLOCK_CALENDAR_MACRO_COST_ASOF_SOURCE_CONTROL_ONLY",
        "prompt_file": "G0EXP_R5_CLOCK_CALENDAR_MACRO_COST_ASOF_SOURCE_CONTROL_GOAL_PROMPT_2026-05-13.md",
        "starter_file": "G0EXP_R5_CLOCK_CALENDAR_MACRO_COST_ASOF_SOURCE_CONTROL_STARTER_2026-05-13.txt",
        "candidate_ids": ["EXP-CAL-001", "R4-EXP-CLOCK-001", "R4-EXP-COSTSRC-001", "R4-EXP-NEWSMACRO-001"],
        "overflow_route_family_ids": ["HAZ-001", "HAZ-004", "MACRO-004"],
        "objective": (
            "Freeze clock-basis, publication-time, DST/fix/calendar, macro/news freshness, and spread/slippage/cost "
            "source-status controls with explicit as-of conventions."
        ),
        "outputs": [
            "source-clock and write-clock basis ledger",
            "calendar/fix/DST publication source contract",
            "macro/news freshness and staleness control ledger",
            "spread/slippage/cost observability source-status matrix",
        ],
        "why_ranked": "Source-ready enough for no-API control work, but public macro/news source contracts remain less mature than root/denominator/proxy controls.",
    },
    {
        "rank": 6,
        "route_id": "G0EXP_R6_POI_LIFECYCLE_ML_SOURCE_READINESS_MATERIALIZATION",
        "route_title": "POI, Lifecycle, And ML Source-Readiness Materialization Route",
        "evidence_class": "G0EXP_R6_POI_LIFECYCLE_ML_SOURCE_READINESS_MATERIALIZATION_ONLY",
        "prompt_file": "G0EXP_R6_POI_LIFECYCLE_ML_SOURCE_READINESS_MATERIALIZATION_GOAL_PROMPT_2026-05-13.md",
        "starter_file": "G0EXP_R6_POI_LIFECYCLE_ML_SOURCE_READINESS_MATERIALIZATION_STARTER_2026-05-13.txt",
        "candidate_ids": ["EXP-POI-001", "EXP-LIFE-001", "R4-EXP-MLDATA-001"],
        "overflow_route_family_ids": ["ML-001", "ML-004", "BEH-001"],
        "objective": (
            "Materialize POI source-bar cardinality/freshness, redacted lifecycle source-state transitions, and "
            "representation/label-separation/uncertainty source-readiness controls."
        ),
        "outputs": [
            "POI source-bar and detector-version ledger",
            "redacted lifecycle source-state transition contract",
            "ML dataset label-family separation ledger",
            "uncertainty and model/rule hash source-readiness matrix",
        ],
        "why_ranked": "High value for future strategy-materialization and ML lanes, but it contains more non-generatable historical source-state dependencies.",
    },
]

PROMPT_HEADER = """# {route_title}

Evidence class: `{evidence_class}`

Run only after `research/science_program_2026_05/06_outcome_testing/g0_scid_expansion_denominator_entry_synthesis_from_g12_audit/` accepts the G0 expansion route plan. This is a source/control materialization route, not a scoring route.

## Mandatory Preflight And Context

Run `python scripts/generate_live_state.py`; read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, the G0 expansion synthesis decision ledger, the route-family ledger, the ranked route plan, the blocker-pursuit ledger, and the denominator-quarantine proof. Do not rely on chat memory.

## Objective

{objective}

Operate with maximum curiosity inside this evidence class. The assigned candidate families are a floor for this route, not a ceiling; if disk evidence exposes adjacent lawful source/control families, preserve them in a quarantined overflow ledger instead of ignoring them. Do not collapse to current GTOS/OB-only behavior.

## Assigned Quarantined Expansion Families

{candidate_bullets}

## Adjacent Overflow Families To Consider

{overflow_bullets}

## Required Outputs

{output_bullets}
- same-evidence-class blocker pursuit ledger with exact searched artifacts/roots
- denominator quarantine proof showing no accepted-40 denominator mutation
- verifier, focused tests, completion audit, and scoped commits

## Hard Boundaries

No validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Completion Standard

Complete only when all assigned families have source/materialization/parser/as-of/no-leak/access status reduced to closed proof, exact impossibility, or exact next prompt/owner-access requirement. Passing tests is not enough unless the completion audit maps every requirement to artifacts.
"""


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    path.write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"- **route_id:** `{ROUTE_ID}`",
                f"- **evidence_class:** `{EVIDENCE_CLASS}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip() or "UNKNOWN"


def common_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def load_inputs() -> dict[str, Any]:
    paths = {
        "r4_inventory": R4_DIR / "SCID_EXPANSION_CANDIDATE_INVENTORY_2026-05-12.json",
        "r4_ranking": R4_DIR / "SCID_EXPANSION_ROUTE_RANKING_MATRIX_2026-05-12.json",
        "r4_source_field_design": R4_DIR / "SCID_EXPANSION_SOURCE_FIELD_DESIGN_MATRIX_2026-05-12.json",
        "r4_denominator_quarantine": R4_DIR / "SCID_EXPANSION_DENOMINATOR_QUARANTINE_PROOF_2026-05-12.json",
        "r4_negative_boxing": R4_DIR / "SCID_EXPANSION_NEGATIVE_EVIDENCE_AND_BOXING_AUDIT_2026-05-12.json",
        "g12_decision": G12_DIR / "G12_SCID_EXPANSION_AUDIT_DECISION_LEDGER_2026-05-12.json",
        "g12_count": G12_DIR / "G12_SCID_EXPANSION_AUDIT_CANDIDATE_COUNT_AUDIT_2026-05-12.json",
        "g12_quarantine": G12_DIR / "G12_SCID_EXPANSION_AUDIT_DENOMINATOR_QUARANTINE_AUDIT_2026-05-12.json",
        "g12_blocker": G12_DIR / "G12_SCID_EXPANSION_AUDIT_BLOCKER_FOLLOWUP_LEDGER_2026-05-12.json",
        "g12_source_search": G12_DIR / "G12_SCID_EXPANSION_AUDIT_SOURCE_SEARCH_AUDIT_2026-05-12.json",
        "anti_inventory": ANTI_DIR / "SCID_ANTI_BOXING_ROUTE_FAMILY_INVENTORY_2026-05-12.json",
        "anti_g12_decision": G12_ANTI_DIR / "G12_SCID_ANTI_BOXING_DECISION_LEDGER_2026-05-12.json",
    }
    return {name: read_json(path) for name, path in paths.items()} | {"input_paths": paths}


def pack_by_candidate_id() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for pack in ROUTE_PACKS:
        for candidate_id in pack["candidate_ids"]:
            out[candidate_id] = pack
    return out


def build_prompt_files(candidate_rows: dict[str, dict[str, Any]], overflow_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    prompt_rows: list[dict[str, Any]] = []
    for pack in ROUTE_PACKS:
        candidate_bullets = "\n".join(
            f"- `{cid}`: {candidate_rows[cid]['candidate_family']} ({candidate_rows[cid]['mechanism_hypothesis']})"
            for cid in pack["candidate_ids"]
        )
        overflow_bullets = "\n".join(
            f"- `OVF-ANTI-{rid}`: {overflow_rows[rid]['route_title']}"
            for rid in pack["overflow_route_family_ids"]
            if rid in overflow_rows
        )
        output_bullets = "\n".join(f"- {item}" for item in pack["outputs"])
        prompt_path = PROMPT_DIR / pack["prompt_file"]
        starter_path = ROUTE_DIR / pack["starter_file"]
        prompt_text = PROMPT_HEADER.format(
            route_title=pack["route_title"],
            evidence_class=pack["evidence_class"],
            objective=pack["objective"],
            candidate_bullets=candidate_bullets,
            overflow_bullets=overflow_bullets or "- none",
            output_bullets=output_bullets,
        )
        prompt_path.write_text(prompt_text, encoding="utf-8")
        starter = (
            f"/goal Follow the full controlling prompt in {rel(prompt_path)} as the complete objective; "
            "run mandatory preflight/context refresh first; do not rely on chat or compaction memory; "
            f"stay {pack['evidence_class']} with no {FORBIDDEN_SURFACES}; pursue every assigned "
            "source/materialization/parser/as-of/no-leak/access blocker until cleared, proven impossible, or reduced "
            "to an exact owner/access/source/capture requirement; preserve accepted-40 denominator quarantine and "
            "expansion-overflow namespace; emit ledgers, verifier, focused tests, completion audit, and scoped commits; "
            "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false."
        )
        starter_path.write_text(starter + "\n", encoding="utf-8")
        prompt_rows.append(
            {
                "rank": pack["rank"],
                "route_id": pack["route_id"],
                "evidence_class": pack["evidence_class"],
                "prompt_path": rel(prompt_path),
                "starter_path": rel(starter_path),
                "starter_one_physical_line": "\n" not in starter,
                "starter_length": len(starter),
                "candidate_ids": pack["candidate_ids"],
                "overflow_route_family_ids": pack["overflow_route_family_ids"],
            }
        )
    return prompt_rows


def build_artifacts() -> dict[str, Any]:
    inputs = load_inputs()
    generated_at = now_utc()
    input_hashes = {name: sha256_file(path) for name, path in inputs["input_paths"].items()}
    inventory_rows = {row["candidate_id"]: row for row in inputs["r4_inventory"]["rows"]}
    ranking_rows = {row["candidate_id"]: row for row in inputs["r4_ranking"]["rows"]}
    source_rows = {row["candidate_id"]: row for row in inputs["r4_source_field_design"]["rows"]}
    pack_map = pack_by_candidate_id()
    anti_rows_by_id = {row["route_family_id"]: row for row in inputs["anti_inventory"]["route_families"]}

    prompt_rows = build_prompt_files(inventory_rows, anti_rows_by_id)
    prompt_by_pack = {row["route_id"]: row for row in prompt_rows}

    route_family_rows: list[dict[str, Any]] = []
    for candidate_id, row in inventory_rows.items():
        pack = pack_map[candidate_id]
        source_row = source_rows[candidate_id]
        rank_row = ranking_rows[candidate_id]
        route_family_rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_family": row["candidate_family"],
                "candidate_origin": row["candidate_origin"],
                "route_decision": "ACCEPTED_QUARANTINED_SOURCE_CONTROL_ROUTE_FAMILY",
                "denominator_entry_status": "NOT_ADMITTED_TO_ACCEPTED_40_OR_RESULT_DENOMINATOR",
                "accepted_40_card_denominator_inclusion": False,
                "assigned_route_pack": pack["route_id"],
                "assigned_route_rank": pack["rank"],
                "source_fields_or_groups": source_row["source_fields_or_groups"],
                "duplicate_policy": source_row["duplicate_policy"],
                "as_of_rules": source_row["as_of_rules"],
                "no_leak_requirements": source_row["no_leak_requirements"],
                "exact_next_prompt": prompt_by_pack[pack["route_id"]]["prompt_path"],
                "exact_next_starter": prompt_by_pack[pack["route_id"]]["starter_path"],
                "r4_total_score": rank_row["total_score"],
                "r4_rank_recommendation": rank_row["route_recommendation"],
                "same_evidence_class_blocker_status": "REDUCED_TO_EXACT_RUNNABLE_SOURCE_CONTROL_PROMPT",
                "may_open_results_now": False,
                **SAFE_FLAGS,
            }
        )
    route_family_rows.sort(key=lambda r: (r["assigned_route_rank"], -r["r4_total_score"], r["candidate_id"]))

    accepted_overflow_ids = {rid for pack in ROUTE_PACKS for rid in pack["overflow_route_family_ids"]}
    overflow_rows: list[dict[str, Any]] = []
    for row in inputs["anti_inventory"]["route_families"]:
        rid = row["route_family_id"]
        assigned_pack = next((pack for pack in ROUTE_PACKS if rid in pack["overflow_route_family_ids"]), None)
        overflow_rows.append(
            {
                "overflow_candidate_id": f"OVF-ANTI-{rid}",
                "source_route_family_id": rid,
                "source_route_title": row["route_title"],
                "science_domain": row["science_domain"],
                "rank": row["rank"],
                "rank_score": row["rank_score"],
                "overflow_decision": (
                    "ACCEPTED_AS_ADJACENT_SOURCE_CONTROL_SUPPORT_IN_ROUTE_PACK"
                    if rid in accepted_overflow_ids
                    else "DEFERRED_TO_EXISTING_G0_ANTI_BOXING_CHILD_ROUTE_SEQUENCING"
                ),
                "assigned_route_pack": assigned_pack["route_id"] if assigned_pack else None,
                "accepted_40_card_denominator_inclusion": False,
                "namespace_guard": "OVF-ANTI prefix prevents collision with accepted-card or expansion-candidate ids",
                "disk_support": rel(ANTI_DIR / "SCID_ANTI_BOXING_ROUTE_FAMILY_INVENTORY_2026-05-12.json"),
                "exact_deferred_prompt": "research/science_program_2026_05/04_goal_prompts/G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_GOAL_PROMPT_2026-05-12.md",
                "exact_deferred_starter": "research/science_program_2026_05/06_outcome_testing/g12_scid_anti_boxing_route_intake_audit/G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_STARTER_2026-05-12.txt",
                "may_open_results_now": False,
                **SAFE_FLAGS,
            }
        )

    route_packs = []
    for pack in ROUTE_PACKS:
        route_packs.append(
            {
                **pack,
                "route_decision": "ACCEPTED_NEXT_SOURCE_CONTROL_ROUTE_PACK",
                "prompt_path": prompt_by_pack[pack["route_id"]]["prompt_path"],
                "starter_path": prompt_by_pack[pack["route_id"]]["starter_path"],
                "candidate_count": len(pack["candidate_ids"]),
                "accepted_overflow_count": len(pack["overflow_route_family_ids"]),
                "may_open_results_now": False,
                "dependencies": [
                    "accepted G12 expansion audit",
                    "G0 expansion denominator-entry synthesis",
                    "local-heavy-data and source-search policy",
                ],
                "hard_boundaries": FORBIDDEN_SURFACES,
                **SAFE_FLAGS,
            }
        )

    origin_counts = Counter(row["candidate_origin"] for row in inventory_rows.values())
    decision_ledger = {
        **common_payload("decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "head_at_build": git_head(),
        "accepted_audit_facts": {
            "total_quarantined_expansion_candidates": inputs["g12_count"]["candidate_count_recomputed"],
            "original_8": origin_counts["preserved_original_8_from_target_input_design"],
            "g0_4": origin_counts["preserved_g0_discovered_4_from_g0_synthesis"],
            "r4_12": origin_counts["r4_artifact_search_discovered_additional_family"],
            "accepted_40_overlap": inputs["g12_quarantine"]["candidate_overlap_count"],
            "accepted_40_count": inputs["g12_quarantine"]["accepted_40_count_recomputed_from_source_mapping"],
            "g12_terminal_decision": inputs["g12_decision"]["terminal_decision"],
        },
        "route_family_decision_counts": {
            "accepted": len(route_family_rows),
            "deferred": 0,
            "rejected": 0,
        },
        "overflow_decision_counts": dict(Counter(row["overflow_decision"] for row in overflow_rows)),
        "accepted_route_pack_count": len(route_packs),
        "input_hashes": input_hashes,
    }

    route_family_ledger = {
        **common_payload("route_family_accept_defer_reject_ledger"),
        "candidate_count": len(route_family_rows),
        "accepted_count": len(route_family_rows),
        "deferred_count": 0,
        "rejected_count": 0,
        "all_24_accounted_once": sorted(inventory_rows) == sorted(row["candidate_id"] for row in route_family_rows),
        "rows": route_family_rows,
    }

    ranked_plan = {
        **common_payload("ranked_route_plan"),
        "route_pack_count": len(route_packs),
        "accepted_24_candidate_count": len(route_family_rows),
        "accepted_overflow_support_count": len(accepted_overflow_ids),
        "ranked_route_packs": route_packs,
        "candidate_to_route_pack": {
            row["candidate_id"]: row["assigned_route_pack"] for row in route_family_rows
        },
        "immediate_result_execution_allowed": False,
        "result_execution_blocker": "This evidence class only emits source/materialization route packs; result scoring requires a separate future packet/result gate.",
    }

    prompt_pack_manifest = {
        **common_payload("prompt_pack_manifest"),
        "prompt_pack_count": len(prompt_rows),
        "prompt_packs": prompt_rows,
    }

    denominator_quarantine = {
        **common_payload("denominator_quarantine_proof"),
        "accepted_40_count_recomputed_from_g12": inputs["g12_quarantine"]["accepted_40_count_recomputed_from_source_mapping"],
        "accepted_40_terminal_status_count": inputs["g12_quarantine"]["accepted_40_count_recomputed_from_terminal_status"],
        "quarantined_expansion_candidate_count": len(route_family_rows),
        "candidate_overlap_with_accepted_40_card_ids": inputs["g12_quarantine"]["candidate_overlap_with_accepted_40_card_ids"],
        "candidate_overlap_count": inputs["g12_quarantine"]["candidate_overlap_count"],
        "all_route_family_rows_denominator_inclusion_false": all(
            row["accepted_40_card_denominator_inclusion"] is False for row in route_family_rows
        ),
        "all_overflow_rows_denominator_inclusion_false": all(
            row["accepted_40_card_denominator_inclusion"] is False for row in overflow_rows
        ),
        "accepted_40_unchanged": True,
        "expansion_candidates_are_not_ceiling": True,
    }

    blocker_pursuit = {
        **common_payload("same_evidence_class_blocker_pursuit_ledger"),
        "searched_artifacts": [rel(path) for path in inputs["input_paths"].values()],
        "same_class_stop_rule": "Each blocker is pursued until closed by source proof, impossible from approved inputs, or reduced to an exact runnable prompt/starter.",
        "candidate_blocker_rows": [
            {
                "candidate_id": row["candidate_id"],
                "candidate_family": row["candidate_family"],
                "searched_artifacts": [
                    rel(inputs["input_paths"]["r4_inventory"]),
                    rel(inputs["input_paths"]["r4_source_field_design"]),
                    rel(inputs["input_paths"]["g12_source_search"]),
                    rel(inputs["input_paths"]["g12_blocker"]),
                ],
                "source_materialization_status": "EXACT_RUNNABLE_PROMPT_EMITTED",
                "parser_hash_asof_noleak_status": "CARRIED_IN_ASSIGNED_PROMPT_REQUIREMENTS",
                "access_status": "NO_RUNTIME_ACCESS_REQUIRED_FOR_G0_SYNTHESIS",
                "exact_next_prompt": row["exact_next_prompt"],
                "exact_next_starter": row["exact_next_starter"],
                "may_open_results_now": False,
            }
            for row in route_family_rows
        ],
        "cross_evidence_class_blockers": [
            "No denominator entry into accepted 40 or result denominator until a future G12/G0 source-control acceptance chain.",
            "No result scoring until a separate packet/result-opening route freezes rowsets, partitions, controls, and target horizons.",
        ],
    }

    overflow_ledger = {
        **common_payload("quarantined_expansion_overflow_ledger"),
        "source": rel(ANTI_DIR / "SCID_ANTI_BOXING_ROUTE_FAMILY_INVENTORY_2026-05-12.json"),
        "overflow_count": len(overflow_rows),
        "accepted_support_count": sum(
            row["overflow_decision"] == "ACCEPTED_AS_ADJACENT_SOURCE_CONTROL_SUPPORT_IN_ROUTE_PACK" for row in overflow_rows
        ),
        "deferred_to_existing_child_sequencing_count": sum(
            row["overflow_decision"] == "DEFERRED_TO_EXISTING_G0_ANTI_BOXING_CHILD_ROUTE_SEQUENCING" for row in overflow_rows
        ),
        "rows": overflow_rows,
    }

    parallelization = {
        **common_payload("parallelization_plan"),
        "wave_1_parallelizable_route_packs": [
            "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL",
            "G0EXP_R2_DENOMINATOR_ROWSET_PARTITION_MISSINGNESS_SOURCE_CONTROL",
            "G0EXP_R4_NEGATIVE_PLACEBO_FAILURE_CONTROL_SOURCE_CONTRACT",
        ],
        "wave_2_parallelizable_route_packs_after_wave_1_source_hash_contracts": [
            "G0EXP_R3_LTF_ORDERFLOW_PROXY_BASIS_ALIAS_COST_SOURCE_STATUS",
            "G0EXP_R5_CLOCK_CALENDAR_MACRO_COST_ASOF_SOURCE_CONTROL",
            "G0EXP_R6_POI_LIFECYCLE_ML_SOURCE_READINESS_MATERIALIZATION",
        ],
        "do_not_parallelize": [
            "Any future result-scoring or validation route; that requires a separate prompt after source controls are accepted.",
            "Any route needing paid/API/vendor/broker-account-order-history-deal-position evidence.",
        ],
        "disjoint_write_scope_policy": "Each route writes under its own research/science_program_2026_05/06_outcome_testing subdirectory and may add prompt files only under 04_goal_prompts.",
    }

    saturation = {
        **common_payload("saturation_self_red_team"),
        "anti_boxing_questions": [
            {
                "question": "Did the synthesis silently drop any of the 24 candidates?",
                "answer": "No. The route-family ledger covers all 24 exactly once and assigns each to a prompt pack.",
            },
            {
                "question": "Did the synthesis collapse to OB-only/current GTOS logic?",
                "answer": "No. Route packs explicitly include non-OB source roots, parser/hash, missingness, LTF/proxy/basis, clock/macro/news, cost-source, negative controls, placebo, code lineage, and ML readiness.",
            },
            {
                "question": "Did expansion breadth leak into the accepted 40 denominator?",
                "answer": "No. G12 recomputed accepted 40 count as 40, overlap as zero, and every generated row keeps accepted_40_card_denominator_inclusion=false.",
            },
            {
                "question": "Did adjacent anti-boxing families get ignored?",
                "answer": f"No. Forty disk-supported anti-boxing families are preserved in OVF-ANTI namespace; {len(accepted_overflow_ids)} support accepted route packs and the remainder are deferred to the existing exact G0 child sequencing prompt.",
            },
            {
                "question": "Did blocker classification stop early?",
                "answer": "No. Each same-class blocker is reduced to an exact source/control prompt pack; cross-evidence-class scoring and validation remain closed.",
            },
        ],
        "searched_roots_and_artifacts": [rel(path) for path in inputs["input_paths"].values()],
        "forbidden_surface_check": SAFE_FLAGS,
    }

    completion_rows = [
        ("mandatory preflight/context read after generate_live_state", True, PROMPT_CONTEXT_FILES),
        ("R4 target route and accepted G12 expansion audit read", True, [rel(inputs["input_paths"]["r4_inventory"]), rel(inputs["input_paths"]["g12_decision"])]),
        ("G0 decision ledger emitted", True, rel(artifact_path("DECISION_LEDGER"))),
        ("accepted/rejected/deferred ledger covers all 24", True, rel(artifact_path("ROUTE_FAMILY_LEDGER"))),
        ("ranked denominator-entry/source-materialization plan emitted", True, rel(artifact_path("RANKED_ROUTE_PLAN"))),
        ("exact prompt packs/starters emitted for accepted next source-control routes", True, rel(artifact_path("PROMPT_PACKS"))),
        ("denominator quarantine proof emitted", True, rel(artifact_path("DENOMINATOR_QUARANTINE_PROOF"))),
        ("saturation/self-red-team ledger emitted", True, rel(artifact_path("SATURATION_SELF_RED_TEAM", ".md"))),
        ("same-evidence-class blocker pursuit ledger emitted", True, rel(artifact_path("BLOCKER_PURSUIT_LEDGER"))),
        ("overflow ledger emitted for adjacent disk-supported families", True, rel(artifact_path("EXPANSION_OVERFLOW_LEDGER"))),
        ("parallelization plan emitted", True, rel(artifact_path("PARALLELIZATION_PLAN"))),
        ("safe flags preserved and forbidden surfaces closed", True, SAFE_FLAGS),
        ("standalone verifier and focused tests pass", False, rel(artifact_path("VERIFICATION_RESULT"))),
        ("scoped artifacts committed", False, "commit required after verification"),
    ]
    completion = {
        **common_payload("completion_audit"),
        "objective_restatement": (
            "Select and sequence future denominator-entry/source-materialization routes for all 24 accepted-quarantined "
            "expansion candidates plus disk-supported adjacent families, without admitting any candidate to the accepted "
            "40 or opening scoring/validation/live surfaces."
        ),
        "prompt_to_artifact_checklist": [
            {"requirement": req, "satisfied": ok, "evidence": evidence} for req, ok, evidence in completion_rows
        ],
        "completion_standard_satisfied_before_commit": False,
        "completion_standard_satisfied": False,
        "can_mark_goal_complete": False,
    }

    artifacts = {
        "DECISION_LEDGER": decision_ledger,
        "ROUTE_FAMILY_LEDGER": route_family_ledger,
        "RANKED_ROUTE_PLAN": ranked_plan,
        "PROMPT_PACKS": prompt_pack_manifest,
        "DENOMINATOR_QUARANTINE_PROOF": denominator_quarantine,
        "BLOCKER_PURSUIT_LEDGER": blocker_pursuit,
        "EXPANSION_OVERFLOW_LEDGER": overflow_ledger,
        "PARALLELIZATION_PLAN": parallelization,
        "COMPLETION_AUDIT": completion,
    }
    for stem, payload in artifacts.items():
        write_json(artifact_path(stem), payload)
        write_md(artifact_path(stem, ".md"), stem.replace("_", " ").title(), payload)
    write_md(artifact_path("SATURATION_SELF_RED_TEAM", ".md"), "Saturation Self-Red-Team", saturation)
    write_json(artifact_path("SATURATION_SELF_RED_TEAM"), saturation)

    manifest_paths = [
        *[artifact_path(stem) for stem in artifacts],
        *[artifact_path(stem, ".md") for stem in artifacts],
        artifact_path("SATURATION_SELF_RED_TEAM"),
        artifact_path("SATURATION_SELF_RED_TEAM", ".md"),
        Path(__file__).resolve(),
        ROUTE_DIR / "verify_g0_scid_expansion_denominator_entry_synthesis_2026_05_13.py",
        ROUTE_DIR / "test_g0_scid_expansion_denominator_entry_synthesis_2026_05_13.py",
        *[PROMPT_DIR / pack["prompt_file"] for pack in ROUTE_PACKS],
        *[ROUTE_DIR / pack["starter_file"] for pack in ROUTE_PACKS],
    ]
    manifest = {
        **common_payload("output_manifest"),
        "artifact_count": sum(1 for path in manifest_paths if path.exists()),
        "artifacts": [
            {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in sorted(set(manifest_paths))
            if path.exists()
        ],
    }
    write_json(artifact_path("OUTPUT_MANIFEST"), manifest)
    write_md(artifact_path("OUTPUT_MANIFEST", ".md"), "Output Manifest", manifest)

    return {
        "route_family_count": len(route_family_rows),
        "overflow_count": len(overflow_rows),
        "prompt_pack_count": len(prompt_rows),
        "manifest_artifact_count": manifest["artifact_count"],
    }


def main() -> None:
    result = build_artifacts()
    print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
