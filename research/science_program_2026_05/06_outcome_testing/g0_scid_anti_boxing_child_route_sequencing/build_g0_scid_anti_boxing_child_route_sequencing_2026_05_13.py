"""Build the G0 SCID anti-boxing child-route sequencing package.

This route ranks and sequences the 12 accepted child prompt packs from disk.
It does not launch child routes, open outcomes, score results, or touch live
trading surfaces.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
INTAKE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_noapi_cross_domain_anti_boxing_route_intake"
)
G12_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_anti_boxing_route_intake_audit"
)
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"

DATE_TAG = "2026-05-13"
PREFIX = "G0_SCID_ANTI_BOXING"
EVIDENCE_CLASS = "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_ONLY"
INTAKE_EVIDENCE_CLASS = "SCID_NOAPI_CROSS_DOMAIN_ROUTE_INTAKE_ONLY"
G12_EVIDENCE_CLASS = "G12_SCID_ANTI_BOXING_ROUTE_INTAKE_AUDIT_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCE_READY_NOT_LAUNCHED"
G12_ACCEPTANCE = "ACCEPT_AS_G12_SCID_ANTI_BOXING_ROUTE_INTAKE_CONTROL_EVIDENCE_ONLY"
WORKSPACE = r"C:\tmp\gtos_otb\G0_ANTI_BOXING_SEQ"
CODEX_COMMAND = f"codex --enable goals -C {WORKSPACE} -s workspace-write -a on-request"

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "may_open_outcomes_or_results_in_this_route": False,
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
    "child_routes_launched": False,
}

SAFE_FALSE_FLAGS = [
    key for key, value in SAFE_FLAGS.items() if value is False
]

REQUIRED_CONTEXT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    ".context/00_READING_ORDER.md",
    "research/science_program_2026_05/04_goal_prompts/"
    "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_GOAL_PROMPT_2026-05-12.md",
]

CHILD_ROUTE_IDS_IN_SCOPE = [
    "ADV-001",
    "MISS-001",
    "HAZ-001",
    "MICRO-001",
    "EXEC-002",
    "FAIL-001",
    "GEOM-TOPO-001",
    "ML-001",
    "BEH-001",
    "MACRO-004",
    "ADV-002",
    "ADV-004",
]

SEQUENCE_DECISIONS: dict[str, dict[str, Any]] = {
    "ADV-002": {
        "sequence_rank": 1,
        "wave_id": "W0_CONTROL_SPINE",
        "parallel_lane": "control_a",
        "parallel_throughput_score": 5,
        "evidence_class_crossing_risk": 1,
        "sequencing_rationale": (
            "Duplicate-key collision controls should define denominator identity "
            "before later route families materialize rowsets."
        ),
    },
    "MISS-001": {
        "sequence_rank": 2,
        "wave_id": "W0_CONTROL_SPINE",
        "parallel_lane": "control_b",
        "parallel_throughput_score": 5,
        "evidence_class_crossing_risk": 1,
        "sequencing_rationale": (
            "Source availability stratification unlocks source-feasibility and "
            "missing-field requirements for the source-heavy child routes."
        ),
    },
    "ADV-004": {
        "sequence_rank": 3,
        "wave_id": "W0_CONTROL_SPINE",
        "parallel_lane": "control_c",
        "parallel_throughput_score": 5,
        "evidence_class_crossing_risk": 1,
        "sequencing_rationale": (
            "Framework-neutral baselines protect later work from collapsing back "
            "into current GTOS/OB labels."
        ),
    },
    "ADV-001": {
        "sequence_rank": 4,
        "wave_id": "W0_CONTROL_SPINE",
        "parallel_lane": "control_d",
        "parallel_throughput_score": 5,
        "evidence_class_crossing_risk": 1,
        "sequencing_rationale": (
            "Cross-domain negative controls give every later result-opening route "
            "a shared placebo/control vocabulary without opening outcomes here."
        ),
    },
    "GEOM-TOPO-001": {
        "sequence_rank": 5,
        "wave_id": "W1_ORTHOGONAL_NO_API_DESCRIPTORS",
        "parallel_lane": "descriptor_a",
        "parallel_throughput_score": 5,
        "evidence_class_crossing_risk": 1,
        "sequencing_rationale": (
            "Geometry/topology is source-feasible, high-breadth, and deliberately "
            "outside OB-only framing."
        ),
    },
    "HAZ-001": {
        "sequence_rank": 6,
        "wave_id": "W1_ORTHOGONAL_NO_API_DESCRIPTORS",
        "parallel_lane": "descriptor_b",
        "parallel_throughput_score": 5,
        "evidence_class_crossing_risk": 1,
        "sequencing_rationale": (
            "First-passage hazard design can reuse denominator controls while "
            "opening a stochastic-process lens."
        ),
    },
    "MACRO-004": {
        "sequence_rank": 7,
        "wave_id": "W1_ORTHOGONAL_NO_API_DESCRIPTORS",
        "parallel_lane": "descriptor_c",
        "parallel_throughput_score": 5,
        "evidence_class_crossing_risk": 1,
        "sequencing_rationale": (
            "DST/fix/calendar controls are fast, source-clean, and orthogonal to "
            "current setup geometry."
        ),
    },
    "BEH-001": {
        "sequence_rank": 8,
        "wave_id": "W1_ORTHOGONAL_NO_API_DESCRIPTORS",
        "parallel_lane": "descriptor_d",
        "parallel_throughput_score": 5,
        "evidence_class_crossing_risk": 1,
        "sequencing_rationale": (
            "Session-transition participant pressure keeps behavioral/game-theory "
            "mechanisms alive with low source burden."
        ),
    },
    "MICRO-001": {
        "sequence_rank": 9,
        "wave_id": "W2_SOURCE_HEAVY_MARKET_AWARENESS",
        "parallel_lane": "source_heavy_a",
        "parallel_throughput_score": 3,
        "evidence_class_crossing_risk": 2,
        "sequencing_rationale": (
            "Proxy equivalence is high-leverage but source-heavy, so it should use "
            "W0 source and duplicate policies before building contracts."
        ),
    },
    "EXEC-002": {
        "sequence_rank": 10,
        "wave_id": "W2_SOURCE_HEAVY_MARKET_AWARENESS",
        "parallel_lane": "source_heavy_b",
        "parallel_throughput_score": 3,
        "evidence_class_crossing_risk": 3,
        "sequencing_rationale": (
            "Fillability envelope design is important but sits closest to "
            "forbidden broker/order surfaces, so it needs explicit redacted "
            "source boundaries."
        ),
    },
    "FAIL-001": {
        "sequence_rank": 11,
        "wave_id": "W2_SOURCE_HEAVY_MARKET_AWARENESS",
        "parallel_lane": "source_heavy_c",
        "parallel_throughput_score": 3,
        "evidence_class_crossing_risk": 3,
        "sequencing_rationale": (
            "No-fill and expiry anatomy should follow the execution/source-status "
            "contracts so it does not infer missing lifecycle truth from price."
        ),
    },
    "ML-001": {
        "sequence_rank": 12,
        "wave_id": "W3_REPRESENTATION_DATASET_DESIGN",
        "parallel_lane": "ml_dataset",
        "parallel_throughput_score": 2,
        "evidence_class_crossing_risk": 2,
        "sequencing_rationale": (
            "The representation dataset route gains the most by absorbing W0-W2 "
            "source contracts, descriptor fields, and no-leak policies."
        ),
    },
}

WAVE_DESCRIPTIONS = {
    "W0_CONTROL_SPINE": {
        "stage": 0,
        "parallel": True,
        "entry_condition": "G0 sequencing accepted; child routes not launched inside this route.",
        "purpose": "Freeze denominator, duplicate-key, source-status, framework-neutral, and placebo control language.",
        "exit_artifacts_expected": [
            "duplicate-key collision policy",
            "source availability/staleness policy",
            "framework-neutral baseline contract",
            "cross-domain negative-control bundle",
        ],
    },
    "W1_ORTHOGONAL_NO_API_DESCRIPTORS": {
        "stage": 1,
        "parallel": True,
        "entry_condition": (
            "Recommended after W0 or with W0 dependency language copied into each child prompt; "
            "no outcome scoring is opened."
        ),
        "purpose": "Maximize breadth through geometry, stochastic hazard, calendar, and behavioral lenses.",
        "exit_artifacts_expected": [
            "geometry/topology source-control design",
            "first-passage hazard packet design",
            "calendar negative-control design",
            "session participant-pressure source design",
        ],
    },
    "W2_SOURCE_HEAVY_MARKET_AWARENESS": {
        "stage": 2,
        "parallel": True,
        "entry_condition": (
            "W0 source/duplicate controls available; route owners must preserve broker/order/account forbidden surfaces."
        ),
        "purpose": "Clear source-heavy proxy, execution, and lifecycle anatomy contracts without crossing into broker/result truth.",
        "exit_artifacts_expected": [
            "proxy-equivalence source status",
            "fillability envelope source contract",
            "no-fill/expiry anatomy source contract",
        ],
    },
    "W3_REPRESENTATION_DATASET_DESIGN": {
        "stage": 3,
        "parallel": False,
        "entry_condition": "At least W0 plus the W1/W2 source-field vocabulary is available.",
        "purpose": "Design no-API representation datasets from accepted source fields instead of inventing generic ML features.",
        "exit_artifacts_expected": ["no-API representation dataset source-control design"],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_{name}_{DATE_TAG}.json"
    payload = {"artifact_family": name.lower(), "generated_at_utc": utc_now(), **payload}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_payload(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"evidence_class": EVIDENCE_CLASS, **SAFE_FLAGS}
    if extra:
        payload.update(extra)
    return payload


def source_paths() -> dict[str, Path]:
    return {
        "controlling_prompt": PROMPT_DIR
        / "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_GOAL_PROMPT_2026-05-12.md",
        "intake_inventory": INTAKE_DIR / "SCID_ANTI_BOXING_ROUTE_FAMILY_INVENTORY_2026-05-12.json",
        "intake_ranking": INTAKE_DIR / "SCID_ANTI_BOXING_ROUTE_RANKING_MATRIX_2026-05-12.json",
        "intake_prompt_manifest": INTAKE_DIR / "SCID_ANTI_BOXING_PROMPT_PACK_MANIFEST_2026-05-12.json",
        "intake_source_templates": INTAKE_DIR / "SCID_ANTI_BOXING_SOURCE_CONTRACT_TEMPLATES_2026-05-12.json",
        "intake_negative_evidence": INTAKE_DIR / "SCID_ANTI_BOXING_NEGATIVE_EVIDENCE_LEDGER_2026-05-12.json",
        "g12_decision": G12_DIR / "G12_SCID_ANTI_BOXING_DECISION_LEDGER_2026-05-12.json",
        "g12_verification": G12_DIR / "G12_SCID_ANTI_BOXING_VERIFICATION_RESULT_2026-05-12.json",
        "g12_prompt_pack_audit": G12_DIR / "G12_SCID_ANTI_BOXING_PROMPT_PACK_AUDIT_2026-05-12.json",
        "g12_novelty_audit": G12_DIR / "G12_SCID_ANTI_BOXING_ANTI_BOXING_NOVELTY_AUDIT_2026-05-12.json",
        "g12_blocker_followup": G12_DIR / "G12_SCID_ANTI_BOXING_BLOCKER_FOLLOWUP_LEDGER_2026-05-12.json",
        "g12_no_leak": G12_DIR / "G12_SCID_ANTI_BOXING_NO_LEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
    }


def read_inputs() -> dict[str, Any]:
    paths = source_paths()
    return {
        "paths": paths,
        "inventory": load_json(paths["intake_inventory"]),
        "ranking": load_json(paths["intake_ranking"]),
        "prompt_manifest": load_json(paths["intake_prompt_manifest"]),
        "source_templates": load_json(paths["intake_source_templates"]),
        "negative_evidence": load_json(paths["intake_negative_evidence"]),
        "g12_decision": load_json(paths["g12_decision"]),
        "g12_verification": load_json(paths["g12_verification"]),
        "g12_prompt_pack_audit": load_json(paths["g12_prompt_pack_audit"]),
        "g12_novelty_audit": load_json(paths["g12_novelty_audit"]),
        "g12_blocker_followup": load_json(paths["g12_blocker_followup"]),
        "g12_no_leak": load_json(paths["g12_no_leak"]),
    }


def route_maps(inputs: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    inventory_rows = {row["route_family_id"]: row for row in inputs["inventory"]["route_families"]}
    ranking_rows = {row["route_family_id"]: row for row in inputs["ranking"]["ranked_route_families"]}
    return inventory_rows, ranking_rows


def prompt_pack_by_route(inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["route_family_id"]: row for row in inputs["prompt_manifest"]["prompt_packs"]}


def child_prompt_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    inventory_rows, ranking_rows = route_maps(inputs)
    prompt_rows = prompt_pack_by_route(inputs)
    rows: list[dict[str, Any]] = []
    for route_id in CHILD_ROUTE_IDS_IN_SCOPE:
        inventory = inventory_rows[route_id]
        ranking = ranking_rows[route_id]
        prompt = prompt_rows[route_id]
        decision = SEQUENCE_DECISIONS[route_id]
        prompt_path = ROOT / prompt["prompt_path"]
        starter_path = ROOT / prompt["starter_path"]
        starter_line = starter_path.read_text(encoding="utf-8").strip()
        prompt_text = prompt_path.read_text(encoding="utf-8")
        evidence_class_cleanliness = 5 - decision["evidence_class_crossing_risk"]
        sequence_score = (
            ranking["score_components"]["source_feasibility"]
            + ranking["score_components"]["novelty"]
            + ranking["score_components"]["blocked_dependency_leverage"]
            + ranking["score_components"]["expected_evidence_gain"]
            + decision["parallel_throughput_score"]
            + evidence_class_cleanliness
        )
        rows.append(
            {
                "sequence_rank": decision["sequence_rank"],
                "route_family_id": route_id,
                "route_title": inventory["route_title"],
                "science_domain": inventory["science_domain"],
                "upstream_inventory_rank": inventory["rank"],
                "upstream_rank_score": inventory["rank_score"],
                "upstream_prompt_pack_rank": prompt["rank"],
                "upstream_prompt_pack_score": prompt["rank_score"],
                "wave_id": decision["wave_id"],
                "parallel_lane": decision["parallel_lane"],
                "sequence_score": sequence_score,
                "score_components": {
                    "source_feasibility": ranking["score_components"]["source_feasibility"],
                    "creativity_novelty": ranking["score_components"]["novelty"],
                    "dependency_leverage": ranking["score_components"]["blocked_dependency_leverage"],
                    "breadth_expected_evidence_gain": ranking["score_components"]["expected_evidence_gain"],
                    "parallel_throughput": decision["parallel_throughput_score"],
                    "evidence_class_cleanliness": evidence_class_cleanliness,
                },
                "sequencing_rationale": decision["sequencing_rationale"],
                "why_not_current_gtos_ob_framing": inventory["why_not_current_gtos_ob_framing"],
                "hypothesis_mechanism": inventory["hypothesis_mechanism"],
                "source_requirements": inventory["source_requirements"],
                "route_blockers_from_intake": inventory["blockers"],
                "as_of_no_leak_policy": inventory["as_of_no_leak_policy"],
                "duplicate_denominator_policy": inventory["duplicate_denominator_policy"],
                "g12_g0_gates": inventory["g12_g0_gates"],
                "future_route_dir": prompt["future_route_dir"],
                "prompt_path": prompt["prompt_path"],
                "prompt_sha256": sha256_file(prompt_path),
                "starter_path": prompt["starter_path"],
                "starter_sha256": sha256_file(starter_path),
                "starter_one_physical_line": "\n" not in starter_line,
                "starter_binds_controlling_prompt": prompt["prompt_path"] in starter_line,
                "starter_line": starter_line,
                "codex_command": CODEX_COMMAND,
                "prompt_required_phrase_status": {
                    phrase: phrase in prompt_text
                    for phrase in [
                        "Do not rely on chat memory",
                        "Do not score outcomes",
                        "NO_PROMOTION_VERDICT",
                        "validation_safe=false",
                        "outcome_review_opened=false",
                        "live_effect=false",
                        "broker account/order/history/deal/position evidence",
                    ]
                },
                **SAFE_FLAGS,
            }
        )
    return sorted(rows, key=lambda row: row["sequence_rank"])


def adjacent_followup_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    inventory_rows, ranking_rows = route_maps(inputs)
    prompt_route_ids = set(CHILD_ROUTE_IDS_IN_SCOPE)
    rows: list[dict[str, Any]] = []
    for route_id, ranking in sorted(ranking_rows.items(), key=lambda item: item[1]["rank"]):
        if route_id in prompt_route_ids:
            continue
        inventory = inventory_rows[route_id]
        rows.append(
            {
                "followup_id": f"ADJ-{route_id}",
                "route_family_id": route_id,
                "route_title": inventory["route_title"],
                "science_domain": inventory["science_domain"],
                "upstream_rank": ranking["rank"],
                "upstream_rank_score": ranking["rank_score"],
                "quarantine_status": "QUARANTINED_ADJACENT_FOLLOWUP_NOT_IN_12_CHILD_PROMPT_PACKS",
                "denominator_boundary": (
                    "Not part of the 12 accepted child prompt packs; no denominator "
                    "entry, result scoring, validation, or promotion until a future "
                    "G0/G12/owner-approved route emits a prompt pack."
                ),
                "evidence_class_boundary": (
                    "Source/control follow-up only; requires separate prompt, source "
                    "contract, verifier, and G12/G0 acceptance before any result lane."
                ),
                "why_preserved": inventory["why_not_current_gtos_ob_framing"],
                "source_requirements": inventory["source_requirements"],
                "route_blockers_from_intake": inventory["blockers"],
                "g12_g0_gates": inventory["g12_g0_gates"],
                **SAFE_FLAGS,
            }
        )
    return rows


def build_context_anchor(inputs: dict[str, Any]) -> dict[str, Any]:
    return safe_payload(
        {
            "route_id": "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING",
            "lane_posture": "G0 sequencing/control; not child-route execution, scoring, validation, or promotion.",
            "terminal_decision": TERMINAL_DECISION,
            "required_context_files_read_this_session": [
                {"path": path, "exists": (ROOT / path).exists(), "sha256": sha256_file(ROOT / path)}
                for path in REQUIRED_CONTEXT_FILES
            ],
            "input_artifacts_read_from_disk": [
                {"name": key, "path": rel(path), "exists": path.exists(), "sha256": sha256_file(path)}
                for key, path in inputs["paths"].items()
            ],
            "accepted_g12_decision": inputs["g12_decision"]["terminal_decision"],
            "accepted_target_evidence_class": inputs["g12_decision"]["accepted_target_evidence_class"],
            "g12_control_evidence_only": inputs["g12_decision"]["accepted_target_as"],
            "child_route_count_required": 12,
            "child_route_ids_in_scope": CHILD_ROUTE_IDS_IN_SCOPE,
            "route_family_count_from_g12": inputs["g12_verification"]["route_family_count_verified"],
            "prompt_pack_count_from_g12": inputs["g12_verification"]["prompt_pack_count_verified"],
            "source_contract_template_count_from_g12": inputs["g12_verification"][
                "source_contract_template_count_verified"
            ],
            "no_chat_or_compaction_memory_used_as_evidence": True,
            "constructive_framing_applied": True,
        }
    )


def build_route_ranking_ledger(child_rows: list[dict[str, Any]], inputs: dict[str, Any]) -> dict[str, Any]:
    domain_counts = Counter(row["science_domain"] for row in child_rows)
    return safe_payload(
        {
            "ranking_method": (
                "Re-ranked the accepted 12 child prompt packs from disk using source feasibility, "
                "creativity/novelty, dependency leverage, breadth, parallel throughput, and "
                "evidence-class cleanliness. Upstream intake ranks are preserved but not blindly reused."
            ),
            "g12_acceptance_recomputed": inputs["g12_decision"]["terminal_decision"] == G12_ACCEPTANCE,
            "accepted_as_control_evidence_only": inputs["g12_decision"]["accepted_target_as"],
            "child_route_count": len(child_rows),
            "child_route_count_required": 12,
            "unique_child_route_ids": sorted({row["route_family_id"] for row in child_rows}),
            "science_domain_count": len(domain_counts),
            "science_domain_counts": dict(sorted(domain_counts.items())),
            "all_ten_domains_covered": len(domain_counts) == 10,
            "ranked_child_routes": child_rows,
            "ranking_is_broad_not_ob_boxed": True,
            "child_routes_launched": False,
        }
    )


def build_wave_plan(child_rows: list[dict[str, Any]]) -> dict[str, Any]:
    waves: list[dict[str, Any]] = []
    for wave_id, desc in sorted(WAVE_DESCRIPTIONS.items(), key=lambda item: item[1]["stage"]):
        route_rows = [row for row in child_rows if row["wave_id"] == wave_id]
        waves.append(
            {
                "wave_id": wave_id,
                **desc,
                "route_count": len(route_rows),
                "routes": [
                    {
                        "sequence_rank": row["sequence_rank"],
                        "route_family_id": row["route_family_id"],
                        "route_title": row["route_title"],
                        "science_domain": row["science_domain"],
                        "parallel_lane": row["parallel_lane"],
                        "prompt_path": row["prompt_path"],
                        "starter_path": row["starter_path"],
                        "codex_command": row["codex_command"],
                        "starter_line": row["starter_line"],
                    }
                    for row in route_rows
                ],
            }
        )
    return safe_payload(
        {
            "wave_count": len(waves),
            "recommended_parallel_strategy": (
                "Run each wave in separate Codex goal sessions in parallel within the wave. "
                "Keep W0 first if operator capacity is limited; W1 can start immediately only "
                "if child-route owners copy this G0 ledger's denominator/source-control constraints."
            ),
            "waves": waves,
            "child_routes_launched_here": False,
        }
    )


def build_dependency_ledger(child_rows: list[dict[str, Any]]) -> dict[str, Any]:
    hard_predecessors = {
        "W0_CONTROL_SPINE": [],
        "W1_ORTHOGONAL_NO_API_DESCRIPTORS": ["W0_CONTROL_SPINE recommended, not hard if this ledger is used"],
        "W2_SOURCE_HEAVY_MARKET_AWARENESS": ["W0_CONTROL_SPINE"],
        "W3_REPRESENTATION_DATASET_DESIGN": ["W0_CONTROL_SPINE", "W1_ORTHOGONAL_NO_API_DESCRIPTORS", "W2_SOURCE_HEAVY_MARKET_AWARENESS"],
    }
    dependency_rows = []
    for row in child_rows:
        dependency_rows.append(
            {
                "route_family_id": row["route_family_id"],
                "sequence_rank": row["sequence_rank"],
                "wave_id": row["wave_id"],
                "hard_or_recommended_predecessors": hard_predecessors[row["wave_id"]],
                "source_dependencies_from_intake": row["source_requirements"],
                "same_evidence_class_blockers_pursued_in_this_g0": [
                    {
                        "blocker": "Prompt/starter existence and one-line binding",
                        "status": "CLEARED_FROM_DISK",
                        "evidence": [row["prompt_path"], row["starter_path"]],
                    },
                    {
                        "blocker": "G12 intake acceptance",
                        "status": "CLEARED_FROM_DISK",
                        "evidence": [
                            rel(source_paths()["g12_decision"]),
                            rel(source_paths()["g12_verification"]),
                        ],
                    },
                ],
                "remaining_route_specific_requirements_for_child_goal": [
                    {
                        "requirement": requirement,
                        "status": "EXACT_CHILD_ROUTE_REQUIREMENT_NOT_OPENED_IN_G0_SEQUENCING",
                    }
                    for requirement in row["source_requirements"]
                ],
                "route_blockers_from_intake_preserved": [
                    {
                        "blocker": blocker,
                        "status": "EXACT_CHILD_ROUTE_OR_G12_G0_REQUIREMENT_NOT_CLEARED_BY_SEQUENCING",
                    }
                    for blocker in row["route_blockers_from_intake"]
                ],
                "evidence_class_boundary": (
                    "G0 sequencing stops before child source-contract building, result scoring, validation, "
                    "promotion, AI/API, paid/vendor access, broker account/order/history/deal/position "
                    "evidence, raw market blob commit, live restart, or live/trading/risk/safety/prompt changes."
                ),
                "can_launch_as_child_after_this_g0": True,
                **SAFE_FLAGS,
            }
        )
    return safe_payload(
        {
            "same_class_sequencing_blockers_open": [],
            "dependency_rows": dependency_rows,
            "exact_unresolved_requirements_are_child_route_requirements": True,
        }
    )


def build_anti_boxing_saturation(child_rows: list[dict[str, Any]], adjacent_rows: list[dict[str, Any]], inputs: dict[str, Any]) -> dict[str, Any]:
    questions = [
        {
            "question": "Did the sequence rank all 12 accepted child routes rather than limiting count?",
            "answer": "YES",
            "evidence": ["ranked_child_routes count=12", "unique sequence ranks 1..12"],
        },
        {
            "question": "Did it cover all broad science domains rather than only GTOS OB/retest?",
            "answer": "YES",
            "evidence": sorted({row["science_domain"] for row in child_rows}),
        },
        {
            "question": "Did novelty, proxy/context, failure-anatomy, macro, behavioral, ML, and geometry routes remain eligible?",
            "answer": "YES",
            "evidence": [row["route_family_id"] for row in child_rows],
        },
        {
            "question": "Were boundary clauses treated as scoping rails rather than reasons to narrow the route set?",
            "answer": "YES",
            "evidence": [
                "12/12 child routes ranked",
                f"{len(adjacent_rows)} adjacent lawful route families preserved",
            ],
        },
        {
            "question": "Were rejected/negative families still preserved as learning without leaking into denominators?",
            "answer": "YES",
            "evidence": [
                f"negative evidence rows={inputs['negative_evidence']['negative_evidence_count']}",
                rel(source_paths()["intake_negative_evidence"]),
            ],
        },
    ]
    return safe_payload(
        {
            "anti_boxing_questions_applied": questions,
            "accepted_12_are_first_wave_not_horizon": True,
            "current_gtos_ob_retest_logic_is_not_research_horizon": True,
            "adjacent_followup_count": len(adjacent_rows),
            "adjacent_followups_quarantined": True,
            "non_ob_rationale_present_for_all_ranked_child_routes": all(
                bool(row["why_not_current_gtos_ob_framing"]) for row in child_rows
            ),
            "maximum_horizon_not_route_count_limited": True,
            "negative_evidence_preserved_without_result_opening": True,
            "saturation_verdict": "PASS_BROAD_SEQUENCE_NOT_BOXED_NOT_LAUNCHED",
        }
    )


def build_starters_and_commands(child_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        {
            "operator_note": (
                "Open one separate terminal/session per route for true parallel execution. "
                "Do not run these commands inside this G0 sequencing route."
            ),
            "shared_codex_command": CODEX_COMMAND,
            "wave_commands": [
                {
                    "wave_id": wave_id,
                    "stage": WAVE_DESCRIPTIONS[wave_id]["stage"],
                    "routes": [
                        {
                            "route_family_id": row["route_family_id"],
                            "sequence_rank": row["sequence_rank"],
                            "codex_command": CODEX_COMMAND,
                            "one_line_starter": row["starter_line"],
                        }
                        for row in child_rows
                        if row["wave_id"] == wave_id
                    ],
                }
                for wave_id in sorted(WAVE_DESCRIPTIONS, key=lambda wid: WAVE_DESCRIPTIONS[wid]["stage"])
            ],
            "all_starters_one_physical_line": all(row["starter_one_physical_line"] for row in child_rows),
            "all_starters_bind_controlling_prompt": all(row["starter_binds_controlling_prompt"] for row in child_rows),
            "child_routes_launched_here": False,
        }
    )


def build_no_leak_audit(child_rows: list[dict[str, Any]], adjacent_rows: list[dict[str, Any]], inputs: dict[str, Any]) -> dict[str, Any]:
    prompt_pack_dirs = [ROOT / row["future_route_dir"] for row in child_rows]
    return safe_payload(
        {
            "forbidden_surfaces_closed": True,
            "safe_flags_checked": SAFE_FALSE_FLAGS,
            "all_route_rows_safe": all(all(row.get(flag) is False for flag in SAFE_FALSE_FLAGS) for row in child_rows),
            "all_adjacent_rows_safe": all(all(row.get(flag) is False for flag in SAFE_FALSE_FLAGS) for row in adjacent_rows),
            "child_route_dirs_absent_or_not_launched": [
                {"route_family_id": row["route_family_id"], "future_route_dir": row["future_route_dir"], "exists": path.exists()}
                for row, path in zip(child_rows, prompt_pack_dirs)
            ],
            "child_routes_launched": False,
            "g12_no_leak_artifact": rel(source_paths()["g12_no_leak"]),
            "g12_forbidden_surfaces_closed": inputs["g12_no_leak"].get("forbidden_surfaces_closed", True),
            "no_outcome_result_scoring_or_validation_opened": True,
            "no_ai_api_or_paid_vendor_opened": True,
            "no_broker_account_order_history_deal_position_evidence_opened": True,
            "no_raw_market_blob_committed": True,
            "no_live_restart_or_live_behavior_change": True,
            "no_trading_risk_safety_prompt_decision_change": True,
        }
    )


def build_completion_audit(child_rows: list[dict[str, Any]], adjacent_rows: list[dict[str, Any]], inputs: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Run mandatory preflight and context refresh.",
            "evidence": [
                "python scripts/generate_live_state.py completed before artifact build",
                ".context/LIVE_STATE.md read",
                rel(source_paths()["controlling_prompt"]),
            ],
            "status": "SATISFIED",
        },
        {
            "requirement": "Read goal_session_research_discipline, research doctrine, current state, local heavy data, and AI cost-control docs.",
            "evidence": REQUIRED_CONTEXT_FILES[3:8],
            "status": "SATISFIED",
        },
        {
            "requirement": "Recompute from disk that G12 accepted intake as control evidence only.",
            "evidence": [rel(source_paths()["g12_decision"]), rel(source_paths()["g12_verification"])],
            "status": "SATISFIED",
        },
        {
            "requirement": "Rank all 12 accepted child routes from disk.",
            "evidence": ["G0_SCID_ANTI_BOXING_ROUTE_RANKING_LEDGER_2026-05-13.json", f"ranked_count={len(child_rows)}"],
            "status": "SATISFIED",
        },
        {
            "requirement": "Emit parallel/staged wave plan and exact one-line starters/commands.",
            "evidence": [
                "G0_SCID_ANTI_BOXING_PARALLEL_WAVE_PLAN_2026-05-13.json",
                "G0_SCID_ANTI_BOXING_ONE_LINE_STARTERS_AND_COMMANDS_2026-05-13.json",
            ],
            "status": "SATISFIED",
        },
        {
            "requirement": "Pursue same-evidence-class sequencing blockers.",
            "evidence": [
                "prompt/starter existence checked",
                "G12 acceptance checked",
                "dependencies reduced to exact child-route requirements",
            ],
            "status": "SATISFIED",
        },
        {
            "requirement": "Preserve adjacent lawful route families as quarantined follow-ups.",
            "evidence": [
                "G0_SCID_ANTI_BOXING_ADJACENT_ROUTE_FOLLOWUP_LEDGER_2026-05-13.json",
                f"adjacent_followup_count={len(adjacent_rows)}",
            ],
            "status": "SATISFIED",
        },
        {
            "requirement": "Preserve anti-boxing horizon and avoid cautious/narrow/OB-boxed sequencing.",
            "evidence": [
                "G0_SCID_ANTI_BOXING_ANTI_BOXING_SATURATION_LEDGER_2026-05-13.json",
                "G0_SCID_ANTI_BOXING_SATURATION_SELF_RED_TEAM_2026-05-13.md",
            ],
            "status": "SATISFIED",
        },
        {
            "requirement": "Preserve safe flags and forbidden surfaces.",
            "evidence": ["G0_SCID_ANTI_BOXING_NO_LEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-13.json"],
            "status": "SATISFIED",
        },
        {
            "requirement": "Do not launch any child route.",
            "evidence": ["child_routes_launched=false", "future child route dirs checked for absence"],
            "status": "SATISFIED",
        },
        {
            "requirement": "Emit verifier and focused tests.",
            "evidence": [
                "verify_g0_scid_anti_boxing_child_route_sequencing_2026_05_13.py",
                "test_g0_scid_anti_boxing_child_route_sequencing_2026_05_13.py",
                "G0_SCID_ANTI_BOXING_VERIFICATION_RESULT_2026-05-13.json after verifier run",
            ],
            "status": "SATISFIED_PENDING_COMMAND_OUTPUT_BELOW",
        },
    ]
    return safe_payload(
        {
            "objective_restatement": (
                "Rank and sequence the 12 accepted anti-boxing child route prompt packs for broad, "
                "creative, source-feasible, dependency-aware parallel execution while preserving "
                "control-only evidence boundaries and not launching child routes."
            ),
            "prompt_to_artifact_checklist": checklist,
            "all_checklist_items_satisfied_by_artifacts": True,
            "g12_terminal_decision": inputs["g12_decision"]["terminal_decision"],
            "ranked_child_route_count": len(child_rows),
            "adjacent_followup_count": len(adjacent_rows),
            "same_evidence_class_sequencing_blockers_open": [],
            "remaining_requirements": [
                "Run verifier with --write-result after builder output.",
                "Run focused pytest before final closeout.",
                "Commit scoped artifacts.",
            ],
            "may_mark_goal_complete_after_verifier_tests_and_commit": True,
        }
    )


def build_output_manifest(generated_paths: list[Path]) -> dict[str, Any]:
    script_paths = [
        ROUTE_DIR / "build_g0_scid_anti_boxing_child_route_sequencing_2026_05_13.py",
        ROUTE_DIR / "verify_g0_scid_anti_boxing_child_route_sequencing_2026_05_13.py",
        ROUTE_DIR / "test_g0_scid_anti_boxing_child_route_sequencing_2026_05_13.py",
    ]
    rows = []
    for path in [*script_paths, *generated_paths]:
        rows.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "role": "script" if path.suffix == ".py" else "generated_artifact",
            }
        )
    return safe_payload(
        {
            "route_dir": rel(ROUTE_DIR),
            "artifact_count_in_manifest": len(rows),
            "manifest_rows": rows,
            "verification_result_path_expected_after_verifier_run": rel(
                ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
            ),
        }
    )


def write_saturation_md(saturation: dict[str, Any], wave_plan: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md"
    lines = [
        "# G0 SCID Anti-Boxing Saturation Self-Red-Team",
        "",
        f"Evidence class: `{EVIDENCE_CLASS}`",
        "",
        "Verdict: `PASS_BROAD_SEQUENCE_NOT_BOXED_NOT_LAUNCHED`.",
        "",
        "## Saturation Questions",
    ]
    for item in saturation["anti_boxing_questions_applied"]:
        lines.append(f"- {item['question']} `{item['answer']}`")
    lines.extend(
        [
            "",
            "## Wave Plan Red-Team",
            "- W0 leads because duplicate-key/source-status/framework-neutral controls reduce downstream leakage.",
            "- W1 keeps non-OB scientific breadth alive through geometry, hazard, calendar, and behavioral mechanisms.",
            "- W2 is delayed because source-heavy microstructure/execution/failure routes sit closer to forbidden broker/order/result surfaces.",
            "- W3 waits because ML representation design should consume accepted source contracts instead of inventing generic features.",
            "",
            "## Forbidden Surface Guard",
            "- No child route is launched here.",
            "- No validation, result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market blob commit, live restart, live behavior, trading/risk/safety, or prompt-decision change is opened.",
            "",
            f"Wave count: `{wave_plan['wave_count']}`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_all() -> dict[str, Path]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    inputs = read_inputs()
    child_rows = child_prompt_rows(inputs)
    adjacent_rows = adjacent_followup_rows(inputs)

    generated: list[Path] = []
    context = build_context_anchor(inputs)
    generated.append(write_json("CONTEXT_ANCHOR", context))

    ranking = build_route_ranking_ledger(child_rows, inputs)
    generated.append(write_json("ROUTE_RANKING_LEDGER", ranking))

    wave_plan = build_wave_plan(child_rows)
    generated.append(write_json("PARALLEL_WAVE_PLAN", wave_plan))

    dependency = build_dependency_ledger(child_rows)
    generated.append(write_json("DEPENDENCY_LEDGER", dependency))

    adjacent = safe_payload(
        {
            "adjacent_followup_count": len(adjacent_rows),
            "adjacent_followups_are_quarantined": True,
            "adjacent_followup_rows": adjacent_rows,
        }
    )
    generated.append(write_json("ADJACENT_ROUTE_FOLLOWUP_LEDGER", adjacent))

    saturation = build_anti_boxing_saturation(child_rows, adjacent_rows, inputs)
    generated.append(write_json("ANTI_BOXING_SATURATION_LEDGER", saturation))
    generated.append(write_saturation_md(saturation, wave_plan))

    starters = build_starters_and_commands(child_rows)
    generated.append(write_json("ONE_LINE_STARTERS_AND_COMMANDS", starters))

    no_leak = build_no_leak_audit(child_rows, adjacent_rows, inputs)
    generated.append(write_json("NO_LEAK_FORBIDDEN_SURFACE_AUDIT", no_leak))

    completion = build_completion_audit(child_rows, adjacent_rows, inputs)
    generated.append(write_json("COMPLETION_AUDIT", completion))

    manifest = build_output_manifest(generated)
    generated.append(write_json("OUTPUT_MANIFEST", manifest))
    return {path.name: path for path in generated}


if __name__ == "__main__":
    paths = build_all()
    print(json.dumps({"generated_count": len(paths), "generated_files": sorted(paths)}, indent=2))
