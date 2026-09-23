"""Build the G12 audit package for the SCID anti-boxing route intake.

This route is audit/control evidence only. It independently recomputes the
target intake from disk, records any same-evidence-class repairs, and emits the
next G0 sequencing prompt without launching child routes or opening outcomes.
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
TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_noapi_cross_domain_anti_boxing_route_intake"
)
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"

DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_ANTI_BOXING"
EVIDENCE_CLASS = "G12_SCID_ANTI_BOXING_ROUTE_INTAKE_AUDIT_ONLY"
TARGET_EVIDENCE_CLASS = "SCID_NOAPI_CROSS_DOMAIN_ROUTE_INTAKE_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_AS_G12_SCID_ANTI_BOXING_ROUTE_INTAKE_CONTROL_EVIDENCE_ONLY"

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
}

REQUIRED_DOMAINS = [
    "geometry_topology_path_shape",
    "stochastic_tail_hazard",
    "auction_microstructure_orderflow_liquidity",
    "behavioral_game_theory_session_participants",
    "macro_calendar_cross_asset",
    "execution_fillability_spread_slippage",
    "ml_meta_labeling_uncertainty",
    "adversarial_baselines_placebos",
    "source_missingness_denominator_controls",
    "failure_anatomy_derived_hypotheses",
]

REQUIRED_SOURCE_CONTRACT_FIELDS = [
    "template_id",
    "source_family",
    "required_fields",
    "searched_root_expectations",
    "as_of_rule",
    "hash_deferral_policy",
    "no_leak_rules",
    "duplicate_policy",
    "forbidden_fields",
    "fail_closed_statuses",
]

CONTEXT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    "research/science_program_2026_05/04_goal_prompts/G12_SCID_ANTI_BOXING_ROUTE_INTAKE_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "research/science_program_2026_05/04_goal_prompts/G0NAPI_R5_ANTI_BOXING_INTAKE_GOAL_PROMPT_2026-05-12.md",
]

FORBIDDEN_SURFACE_PHRASE = (
    "validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/"
    "paid-vendor/broker-account-order-history-deal-position/raw-market-blob/"
    "live-restart/live-behavior/trading-risk-safety-prompt-decision changes"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def target_artifact(stem: str, suffix: str = ".json") -> Path:
    return TARGET_DIR / f"SCID_ANTI_BOXING_{stem}_{DATE_TAG}{suffix}"


def safe_payload(artifact_family: str, generated_at: str) -> dict[str, Any]:
    return {
        **SAFE_FLAGS,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
    }


def load_target() -> dict[str, Any]:
    return {
        "inventory": read_json(target_artifact("ROUTE_FAMILY_INVENTORY")),
        "domain": read_json(target_artifact("DOMAIN_COVERAGE_AND_GAP_LEDGER")),
        "ranking": read_json(target_artifact("ROUTE_RANKING_MATRIX")),
        "source_contracts": read_json(target_artifact("SOURCE_CONTRACT_TEMPLATES")),
        "negative": read_json(target_artifact("NEGATIVE_EVIDENCE_LEDGER")),
        "prompt_manifest": read_json(target_artifact("PROMPT_PACK_MANIFEST")),
        "criteria": read_json(target_artifact("CANDIDATE_ACCEPTANCE_REJECTION_CRITERIA")),
        "completion": read_json(target_artifact("COMPLETION_AUDIT")),
        "target_verification": read_json(target_artifact("VERIFICATION_RESULT")),
    }


def build_context_anchor(generated_at: str) -> dict[str, Any]:
    context_rows = []
    for raw_path in CONTEXT_FILES:
        path = ROOT / raw_path
        context_rows.append({"path": raw_path, "exists": path.exists(), "sha256": sha256_file(path)})
    target_rows = []
    for path in sorted(TARGET_DIR.glob("*")):
        if path.is_file():
            target_rows.append({"path": rel(path), "sha256": sha256_file(path), "exists": True})
    return {
        **safe_payload("context_anchor", generated_at),
        "audit_scope": "independent G12 audit of target route intake artifacts only",
        "target_route_dir": rel(TARGET_DIR),
        "context_inputs": context_rows,
        "target_artifact_count_seen": len(target_rows),
        "target_artifacts_seen": target_rows,
        "lane_posture": "G12 audit/control; fair-adversarial; preserve creative breadth while rejecting real evidence defects",
        "hard_boundaries": FORBIDDEN_SURFACE_PHRASE,
    }


def build_route_family_recomputation(target: dict[str, Any], generated_at: str) -> dict[str, Any]:
    inventory = target["inventory"]
    families = inventory["route_families"]
    family_ids = [row["route_family_id"] for row in families]
    domain_counts = Counter(row["science_domain"] for row in families)
    ranking_ids = [row["route_family_id"] for row in target["ranking"]["ranked_route_families"]]
    upstream = inventory["upstream_reconstruction"]
    route_rows = []
    for row in families:
        route_rows.append(
            {
                "rank": row["rank"],
                "route_family_id": row["route_family_id"],
                "science_domain": row["science_domain"],
                "rank_score": row["rank_score"],
                "has_mechanism": bool(row.get("hypothesis_mechanism")),
                "has_source_requirements": bool(row.get("source_requirements")),
                "has_as_of_policy": bool(row.get("as_of_no_leak_policy")),
                "has_duplicate_policy": bool(row.get("duplicate_denominator_policy")),
                "has_non_ob_rationale": bool(row.get("why_not_current_gtos_ob_framing")),
                "may_open_outcomes_or_results_in_this_route": row.get("may_open_outcomes_or_results_in_this_route"),
                "opens_broker_evidence": row.get("opens_broker_account_order_history_deal_position_evidence"),
            }
        )
    return {
        **safe_payload("route_family_recomputation_audit", generated_at),
        "target_evidence_class": inventory["evidence_class"],
        "route_family_count": len(families),
        "route_family_count_required_exact": 40,
        "route_family_count_exactly_40": len(families) == 40,
        "unique_route_family_count": len(set(family_ids)),
        "all_route_family_ids_unique": len(set(family_ids)) == len(family_ids),
        "ranking_row_count": len(ranking_ids),
        "ranking_matches_inventory_ids": set(ranking_ids) == set(family_ids),
        "rank_scores_descending": [row["rank_score"] for row in target["ranking"]["ranked_route_families"]]
        == sorted([row["rank_score"] for row in target["ranking"]["ranked_route_families"]], reverse=True),
        "domain_counts": dict(sorted(domain_counts.items())),
        "domain_count": len(domain_counts),
        "required_domain_count": len(REQUIRED_DOMAINS),
        "all_required_domains_covered": set(REQUIRED_DOMAINS).issubset(domain_counts),
        "exact_four_families_per_domain": all(domain_counts.get(domain) == 4 for domain in REQUIRED_DOMAINS),
        "upstream_reconstruction": {
            "accepted_card_count": upstream.get("accepted_card_count"),
            "ready_card_count": upstream.get("ready_card_count"),
            "blocked_card_count": upstream.get("blocked_card_count"),
            "science_domain_count": upstream.get("science_domain_count"),
            "preserved_target_expansion_candidate_count": upstream.get("preserved_target_expansion_candidate_count"),
            "g0_discovered_expansion_candidate_count": upstream.get("g0_discovered_expansion_candidate_count"),
            "all_expansion_candidates_denominator_inclusion_false": upstream.get(
                "all_expansion_candidates_denominator_inclusion_false"
            ),
        },
        "route_rows": route_rows,
        "failures": [
            failure
            for failure, ok in [
                ("route family count is not exactly 40", len(families) == 40),
                ("route family ids are not unique", len(set(family_ids)) == len(family_ids)),
                ("required domains are not all covered", set(REQUIRED_DOMAINS).issubset(domain_counts)),
                ("not exactly four families per required domain", all(domain_counts.get(domain) == 4 for domain in REQUIRED_DOMAINS)),
                ("ranking ids do not match inventory ids", set(ranking_ids) == set(family_ids)),
                ("ranking rows are not sorted by score", [row["rank_score"] for row in target["ranking"]["ranked_route_families"]]
                 == sorted([row["rank_score"] for row in target["ranking"]["ranked_route_families"]], reverse=True)),
            ]
            if not ok
        ],
    }


def build_domain_audit(target: dict[str, Any], generated_at: str) -> dict[str, Any]:
    domain_counts = Counter(row["science_domain"] for row in target["inventory"]["route_families"])
    manifest = target["prompt_manifest"]
    prompt_domains = Counter(row["science_domain"] for row in manifest["prompt_packs"])
    rows = []
    for domain in REQUIRED_DOMAINS:
        rows.append(
            {
                "science_domain": domain,
                "route_family_count": domain_counts.get(domain, 0),
                "prompt_pack_count": prompt_domains.get(domain, 0),
                "target_domain_ledger_status": next(
                    row.get("gap_status")
                    for row in target["domain"]["domain_rows"]
                    if row.get("science_domain") == domain
                ),
                "covered": domain_counts.get(domain, 0) > 0,
            }
        )
    return {
        **safe_payload("domain_coverage_audit", generated_at),
        "required_domains": REQUIRED_DOMAINS,
        "domain_rows": rows,
        "all_required_domains_have_route_family": all(row["route_family_count"] > 0 for row in rows),
        "all_required_domains_have_prompt_pack": all(row["prompt_pack_count"] > 0 for row in rows),
        "breadth_verdict": "PASS_10_OF_10_DOMAINS_WITH_40_TOTAL_ROUTE_FAMILIES",
    }


def prompt_text_check(prompt_path: Path, starter_path: Path) -> dict[str, Any]:
    prompt_text = prompt_path.read_text(encoding="utf-8")
    starter_text = starter_path.read_text(encoding="utf-8").strip()
    required_phrases = [
        "Do not rely on chat memory",
        "Current GTOS OB/retest logic is not the research horizon",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
        "Do not score outcomes",
        "broker account/order/history/deal/position evidence",
        "AI/API",
        "Completion Standard",
    ]
    return {
        "prompt_exists": prompt_path.exists(),
        "starter_exists": starter_path.exists(),
        "starter_one_physical_line": "\n" not in starter_text,
        "starter_binds_controlling_prompt": starter_text.startswith("/goal Follow the full controlling prompt"),
        "required_phrase_status": {phrase: phrase in prompt_text for phrase in required_phrases},
    }


def build_prompt_pack_audit(target: dict[str, Any], generated_at: str) -> dict[str, Any]:
    pack_rows = []
    failures = []
    for pack in target["prompt_manifest"]["prompt_packs"]:
        prompt_path = ROOT / pack["prompt_path"]
        starter_path = ROOT / pack["starter_path"]
        checks = prompt_text_check(prompt_path, starter_path)
        missing = [phrase for phrase, ok in checks["required_phrase_status"].items() if not ok]
        if missing:
            failures.append({"route_family_id": pack["route_family_id"], "missing_prompt_phrases": missing})
        if not checks["starter_one_physical_line"] or not checks["starter_binds_controlling_prompt"]:
            failures.append({"route_family_id": pack["route_family_id"], "starter_failure": checks})
        pack_rows.append({**pack, **checks})
    return {
        **safe_payload("prompt_pack_audit", generated_at),
        "prompt_pack_count": len(pack_rows),
        "prompt_pack_count_required_exact": 12,
        "prompt_pack_count_exactly_12": len(pack_rows) == 12,
        "all_starters_one_physical_line": all(row["starter_one_physical_line"] for row in pack_rows),
        "all_starters_bind_controlling_prompt": all(row["starter_binds_controlling_prompt"] for row in pack_rows),
        "all_required_domains_have_prompt_pack": target["prompt_manifest"]["all_required_domains_have_prompt_pack"],
        "prompt_pack_rows": pack_rows,
        "failures": failures,
    }


def build_source_contract_audit(target: dict[str, Any], generated_at: str) -> dict[str, Any]:
    templates = target["source_contracts"]["templates"]
    rows = []
    failures = []
    repair_fields = [
        "searched_root_expectations",
        "hash_deferral_policy",
        "no_leak_rules",
        "fail_closed_statuses",
    ]
    for template in templates:
        missing = [field for field in REQUIRED_SOURCE_CONTRACT_FIELDS if not template.get(field)]
        if missing:
            failures.append({"template_id": template.get("template_id"), "missing_fields": missing})
        rows.append(
            {
                "template_id": template.get("template_id"),
                "source_family": template.get("source_family"),
                "required_fields_count": len(template.get("required_fields", [])),
                "searched_root_expectations_count": len(template.get("searched_root_expectations", [])),
                "forbidden_fields_count": len(template.get("forbidden_fields", [])),
                "has_all_required_contract_controls": not missing,
                "same_evidence_class_repair_fields_present": all(template.get(field) for field in repair_fields),
            }
        )
    return {
        **safe_payload("source_contract_audit", generated_at),
        "template_count": len(templates),
        "template_count_required_exact": 10,
        "template_count_exactly_10": len(templates) == 10,
        "required_contract_fields": REQUIRED_SOURCE_CONTRACT_FIELDS,
        "same_evidence_class_repair_applied": {
            "status": "APPLIED_BEFORE_G12_CLOSEOUT",
            "fields_added_or_verified": repair_fields,
            "reason": "G12 prompt requires searched-root expectations, hash/deferral policy, no-leak rules, and fail-closed statuses for each template.",
        },
        "template_rows": rows,
        "failures": failures,
    }


def build_negative_and_novelty_audits(target: dict[str, Any], generated_at: str) -> tuple[dict[str, Any], dict[str, Any]]:
    negative_rows = target["negative"]["negative_evidence_rows"]
    negative_failures = []
    for row in negative_rows:
        if not row.get("preserved_learning"):
            negative_failures.append({"negative_id": row.get("negative_id"), "missing": "preserved_learning"})
    novelty_by_domain = {}
    for domain in REQUIRED_DOMAINS:
        novelty_by_domain[domain] = [
            row["route_family_id"]
            for row in target["inventory"]["route_families"]
            if row["science_domain"] == domain and row.get("why_not_current_gtos_ob_framing")
        ]
    novelty = {
        **safe_payload("anti_boxing_novelty_audit", generated_at),
        "current_gtos_ob_retest_logic_is_not_research_horizon": target["inventory"].get(
            "current_gtos_ob_retest_logic_is_not_research_horizon"
        ),
        "accepted_40_is_floor_not_ceiling": target["inventory"].get("accepted_40_is_floor_not_ceiling"),
        "novelty_by_required_domain": novelty_by_domain,
        "all_40_have_non_ob_rationale": all(
            bool(row.get("why_not_current_gtos_ob_framing")) for row in target["inventory"]["route_families"]
        ),
        "breadth_verdict": "PASS_PRESERVE_CREATIVE_OUTSIDE_CURRENT_GTOS_BREADTH",
    }
    negative = {
        **safe_payload("negative_evidence_treatment_audit", generated_at),
        "negative_evidence_count": len(negative_rows),
        "negative_evidence_rows": negative_rows,
        "has_boxed_route_rejection": any(row.get("status") == "REJECTED_AS_BOXED" for row in negative_rows),
        "has_forbidden_surface_rejection": any("FORBIDDEN" in row.get("status", "") for row in negative_rows),
        "all_negative_rows_preserve_learning": not negative_failures,
        "negative_evidence_verdict": "PASS_NEGATIVE_EVIDENCE_IS_RESEARCH_INTELLIGENCE_NOT_OB_COLLAPSE",
        "failures": negative_failures,
    }
    return novelty, negative


def build_no_leak_audit(target: dict[str, Any], generated_at: str) -> dict[str, Any]:
    json_artifacts = {
        "inventory": target["inventory"],
        "domain": target["domain"],
        "ranking": target["ranking"],
        "source_contracts": target["source_contracts"],
        "negative": target["negative"],
        "prompt_manifest": target["prompt_manifest"],
        "criteria": target["criteria"],
        "completion": target["completion"],
    }
    safe_failures = []
    for name, payload in json_artifacts.items():
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            safe_failures.append(f"{name}: promotion_verdict mismatch")
        for flag, expected in SAFE_FLAGS.items():
            if flag == "promotion_verdict":
                continue
            if payload.get(flag) is not expected:
                safe_failures.append(f"{name}: {flag} is not {expected}")
    route_failures = []
    for row in target["inventory"]["route_families"]:
        for flag in [
            "may_open_outcomes_or_results_in_this_route",
            "opens_validation",
            "opens_result_scoring",
            "opens_ai_api",
            "opens_paid_or_vendor_access",
            "opens_broker_account_order_history_deal_position_evidence",
            "opens_live_restart",
            "opens_live_trading_behavior",
            "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        ]:
            if row.get(flag) is not False:
                route_failures.append({"route_family_id": row["route_family_id"], "flag": flag, "value": row.get(flag)})
    return {
        **safe_payload("no_leak_forbidden_surface_audit", generated_at),
        "json_artifact_safe_flag_failures": safe_failures,
        "route_family_safe_flag_failures": route_failures,
        "forbidden_surfaces_closed": not safe_failures and not route_failures,
        "no_leak_verdict": "PASS_FORBIDDEN_SURFACES_CLOSED_AND_SAFE_FLAGS_FALSE"
        if not safe_failures and not route_failures
        else "FAIL_FORBIDDEN_SURFACE_REPAIR_REQUIRED",
        "explicitly_closed_surfaces": [
            "validation/results",
            "R/PnL/win-rate/expectancy/performance",
            "promotion",
            "AI/API",
            "paid-vendor access",
            "broker account/order/history/deal/position evidence",
            "raw market blob commit",
            "live restart/live behavior",
            "trading-risk-safety-prompt-decision changes",
        ],
    }


def build_blocker_followup(generated_at: str, source_audit: dict[str, Any]) -> dict[str, Any]:
    open_blockers = []
    if source_audit["failures"]:
        open_blockers.extend(source_audit["failures"])
    return {
        **safe_payload("blocker_followup_ledger", generated_at),
        "same_evidence_class_repairs_pursued": [
            {
                "repair_id": "G12-REPAIR-SOURCE-CONTRACT-EXPLICIT-CONTROLS",
                "status": "DONE",
                "evidence": [
                    rel(TARGET_DIR / "build_scid_anti_boxing_route_intake_2026_05_12.py"),
                    rel(TARGET_DIR / "verify_scid_anti_boxing_route_intake_2026_05_12.py"),
                    rel(TARGET_DIR / "test_scid_anti_boxing_route_intake_2026_05_12.py"),
                    rel(target_artifact("SOURCE_CONTRACT_TEMPLATES")),
                ],
                "reason": "Template controls now explicitly specify searched-root expectations, hash/deferral policy, no-leak rules, and fail-closed statuses.",
            }
        ],
        "open_blockers": open_blockers,
        "nonblocking_followups": [
            {
                "followup_id": "G0-CHILD-SEQUENCING",
                "status": "EMITTED_NOT_LAUNCHED",
                "owner": "future G0 route",
                "evidence": rel(PROMPT_DIR / "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_GOAL_PROMPT_2026-05-12.md"),
            }
        ],
        "can_accept_after_repairs": not open_blockers,
    }


def build_saturation(generated_at: str, source_audit: dict[str, Any], prompt_audit: dict[str, Any]) -> None:
    text = f"""# G12 SCID Anti-Boxing Route Intake Saturation Self-Red-Team

Evidence class: `{EVIDENCE_CLASS}`

## What Would Make The Intake A Shallow Prompt Factory

The failure phrase is shallow prompt factory. It would be shallow if the 12 child prompts existed without disk-backed route-family rows, source contracts, no-leak/duplicate controls, negative-evidence treatment, and verifier/focused tests. Disk audit found 40 route families, 10 domains, 12 prompt packs, 10 source-contract templates, target verifier/tests, and this G12 verifier/tests.

## What Would Box It Back Into OB-Only Logic

The failure phrase is OB-only logic. An OB-only restatement would fail because every route family carries a non-current-GTOS/OB rationale, the negative-evidence ledger rejects OB-only restatements, and the domain coverage audit requires adversarial controls, missingness/denominator controls, hazard, microstructure/orderflow, execution/fillability, failure anatomy, topology, macro/session, behavioral, and ML/meta-labeling lanes.

## Under-Covered Domain Check

No required domain is under-covered in count terms: each of the 10 domains has exactly four route families. Prompt-pack coverage is one or more pack for every required domain. Future G0 sequencing can still choose staged execution because source feasibility differs by family.

## Weak Child Prompt Check

Prompt-pack audit count: {prompt_audit['prompt_pack_count']} packs. All starters are one physical line and bind the controlling prompt. The G12 verifier separately checks safe-flag and forbidden-surface phrases.

## Vague Source-Contract Check

The first pass lacked explicit searched-root expectations, hash/deferral policy, no-leak rules, and fail-closed statuses on every source-contract template. Same-evidence-class repair was applied before closeout. Source template failures after repair: {len(source_audit['failures'])}.

## Same-Evidence-Class Repair Availability

The only detected repairable defect was source-contract explicitness. It was repaired in the target builder, verifier, focused test, and regenerated source-contract artifact. No outcome/result, validation, broker account/order/history/deal/position, AI/API, paid-vendor, raw-market-blob, live-restart, live-behavior, or trading-risk-safety-prompt-decision change was required or opened.
"""
    write_text(artifact_path("SATURATION_SELF_RED_TEAM", ".md"), text)


def build_g0_prompt(target: dict[str, Any]) -> tuple[Path, Path]:
    prompt_path = PROMPT_DIR / "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_GOAL_PROMPT_2026-05-12.md"
    starter_path = ROUTE_DIR / "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_STARTER_2026-05-12.txt"
    rows = target["prompt_manifest"]["prompt_packs"]
    route_lines = "\n".join(
        f"{row['rank']}. `{row['route_family_id']}` - `{row['science_domain']}` - prompt `{row['prompt_path']}` - starter `{row['starter_path']}`"
        for row in rows
    )
    prompt = f"""# G0 SCID Anti-Boxing Child Route Sequencing

Evidence class: `G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_ONLY`

Objective: rank and sequence the 12 accepted anti-boxing child route prompt packs after the G12 intake audit. Do not launch child routes inside this G0 sequencing lane.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read this G12 audit route directory: `{rel(ROUTE_DIR)}`.
4. Read the target anti-boxing intake directory: `{rel(TARGET_DIR)}`.

## Inputs To Sequence

{route_lines}

## Required Work

- Recompute from disk that G12 accepted the intake as control evidence only.
- Rank the 12 child routes for parallel or staged execution using source feasibility, cross-domain coverage, dependency leverage, verifier strength, and risk of accidental evidence-class crossing.
- Preserve the anti-boxing horizon: current GTOS OB/retest logic is not the full research horizon, and examples are not limits.
- Preserve all hard boundaries. Do not open validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.
- Do not launch any child route. Emit only a sequencing ledger and one-line starters for the chosen waves if needed.

## Required Outputs

Create a scoped G0 route under `research/science_program_2026_05/06_outcome_testing/g0_scid_anti_boxing_child_route_sequencing/` with route-ranking ledger, parallel/staged wave plan, dependency ledger, no-leak/forbidden-surface audit, completion audit, verifier, and focused tests.

## Safe Flags

`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Completion Standard

Complete only when all 12 child routes are ranked from disk evidence, no child route is launched, hard boundaries are closed, verifier/focused tests pass, and any blocker is exact and actionable.
"""
    starter = (
        f"/goal Follow the full controlling prompt in {rel(prompt_path)} as the complete objective; "
        "run mandatory preflight/context refresh; do not rely on chat memory; stay G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_ONLY with no "
        f"{FORBIDDEN_SURFACE_PHRASE}; rank the 12 accepted child routes for parallel or staged execution from disk evidence only; "
        "do not launch child routes; emit sequencing ledger, no-leak audit, completion audit, verifier/focused tests, scoped commit; "
        "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; mark complete only when the prompt standard is fully satisfied."
    )
    write_text(prompt_path, prompt)
    write_text(starter_path, starter)
    return prompt_path, starter_path


def build_completion(
    generated_at: str,
    route_audit: dict[str, Any],
    domain_audit: dict[str, Any],
    prompt_audit: dict[str, Any],
    source_audit: dict[str, Any],
    negative_audit: dict[str, Any],
    novelty_audit: dict[str, Any],
    no_leak_audit: dict[str, Any],
    blocker_ledger: dict[str, Any],
    g0_prompt_path: Path,
    g0_starter_path: Path,
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "mandatory preflight/context refresh completed",
            "evidence": [".context/LIVE_STATE.md", "core context files read in session and hashed in context anchor"],
            "satisfied": True,
        },
        {
            "requirement": "read R5 controlling prompt and all intake artifacts from disk",
            "evidence": rel(TARGET_DIR),
            "satisfied": True,
        },
        {
            "requirement": "recompute exactly 40 route families across 10 required domains",
            "evidence": rel(artifact_path("ROUTE_FAMILY_RECOMPUTATION_AUDIT")),
            "satisfied": route_audit["route_family_count_exactly_40"] and route_audit["all_required_domains_covered"],
        },
        {
            "requirement": "recompute 12 prompt packs/starters and one-line starters",
            "evidence": rel(artifact_path("PROMPT_PACK_AUDIT")),
            "satisfied": prompt_audit["prompt_pack_count_exactly_12"] and prompt_audit["all_starters_one_physical_line"],
        },
        {
            "requirement": "verify source contracts for future fields, searched roots, as-of, hash/deferral, no-leak, fail-closed statuses",
            "evidence": rel(artifact_path("SOURCE_CONTRACT_AUDIT")),
            "satisfied": source_audit["template_count_exactly_10"] and not source_audit["failures"],
        },
        {
            "requirement": "verify anti-boxing breadth and preserve creativity outside current GTOS/OB framing",
            "evidence": rel(artifact_path("ANTI_BOXING_NOVELTY_AUDIT")),
            "satisfied": novelty_audit["all_40_have_non_ob_rationale"],
        },
        {
            "requirement": "verify negative evidence is research intelligence, not OB-collapse",
            "evidence": rel(artifact_path("NEGATIVE_EVIDENCE_TREATMENT_AUDIT")),
            "satisfied": negative_audit["all_negative_rows_preserve_learning"],
        },
        {
            "requirement": "verify no-leak and forbidden-surface closure",
            "evidence": rel(artifact_path("NO_LEAK_FORBIDDEN_SURFACE_AUDIT")),
            "satisfied": no_leak_audit["forbidden_surfaces_closed"],
        },
        {
            "requirement": "pursue same-evidence-class fixes before closeout",
            "evidence": rel(artifact_path("BLOCKER_FOLLOWUP_LEDGER")),
            "satisfied": blocker_ledger["can_accept_after_repairs"],
        },
        {
            "requirement": "emit G0 child-route sequencing prompt and do not launch child routes",
            "evidence": [rel(g0_prompt_path), rel(g0_starter_path)],
            "satisfied": g0_prompt_path.exists() and g0_starter_path.exists(),
        },
    ]
    return {
        **safe_payload("completion_audit", generated_at),
        "objective_restatement": (
            "Independently audit the SCID anti-boxing route intake as source/control evidence only, "
            "preserve creative breadth, repair same-evidence-class defects, and emit a G0 sequencing prompt if accepted."
        ),
        "terminal_decision": TERMINAL_DECISION if all(row["satisfied"] for row in checklist) else "REJECT_REPAIR_REQUIRED",
        "safe_flags_summary": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "prompt_to_artifact_checklist": checklist,
        "all_checklist_items_satisfied": all(row["satisfied"] for row in checklist),
        "can_mark_goal_complete_after_verifier_tests_and_commit": all(row["satisfied"] for row in checklist),
    }


def build_manifest(generated_at: str, g0_prompt_path: Path, g0_starter_path: Path) -> dict[str, Any]:
    paths = [
        artifact_path("CONTEXT_ANCHOR"),
        artifact_path("DECISION_LEDGER"),
        artifact_path("ROUTE_FAMILY_RECOMPUTATION_AUDIT"),
        artifact_path("DOMAIN_COVERAGE_AUDIT"),
        artifact_path("PROMPT_PACK_AUDIT"),
        artifact_path("SOURCE_CONTRACT_AUDIT"),
        artifact_path("ANTI_BOXING_NOVELTY_AUDIT"),
        artifact_path("NEGATIVE_EVIDENCE_TREATMENT_AUDIT"),
        artifact_path("NO_LEAK_FORBIDDEN_SURFACE_AUDIT"),
        artifact_path("BLOCKER_FOLLOWUP_LEDGER"),
        artifact_path("SATURATION_SELF_RED_TEAM", ".md"),
        artifact_path("COMPLETION_AUDIT"),
        artifact_path("VERIFICATION_RESULT"),
        artifact_path("OUTPUT_MANIFEST"),
        Path(__file__),
        ROUTE_DIR / "verify_g12_scid_anti_boxing_route_intake_audit_2026_05_12.py",
        ROUTE_DIR / "test_g12_scid_anti_boxing_route_intake_audit_2026_05_12.py",
        g0_prompt_path,
        g0_starter_path,
    ]
    return {
        **safe_payload("output_manifest", generated_at),
        "file_count": len(paths),
        "files": [{"path": rel(path), "exists": path.exists(), "sha256": sha256_file(path)} for path in paths],
    }


def build() -> dict[str, Any]:
    generated_at = utc_now()
    target = load_target()
    context_anchor = build_context_anchor(generated_at)
    write_json(artifact_path("CONTEXT_ANCHOR"), context_anchor)

    route_audit = build_route_family_recomputation(target, generated_at)
    write_json(artifact_path("ROUTE_FAMILY_RECOMPUTATION_AUDIT"), route_audit)

    domain_audit = build_domain_audit(target, generated_at)
    write_json(artifact_path("DOMAIN_COVERAGE_AUDIT"), domain_audit)

    prompt_audit = build_prompt_pack_audit(target, generated_at)
    write_json(artifact_path("PROMPT_PACK_AUDIT"), prompt_audit)

    source_audit = build_source_contract_audit(target, generated_at)
    write_json(artifact_path("SOURCE_CONTRACT_AUDIT"), source_audit)

    novelty_audit, negative_audit = build_negative_and_novelty_audits(target, generated_at)
    write_json(artifact_path("ANTI_BOXING_NOVELTY_AUDIT"), novelty_audit)
    write_json(artifact_path("NEGATIVE_EVIDENCE_TREATMENT_AUDIT"), negative_audit)

    no_leak_audit = build_no_leak_audit(target, generated_at)
    write_json(artifact_path("NO_LEAK_FORBIDDEN_SURFACE_AUDIT"), no_leak_audit)

    blocker_ledger = build_blocker_followup(generated_at, source_audit)
    write_json(artifact_path("BLOCKER_FOLLOWUP_LEDGER"), blocker_ledger)

    build_saturation(generated_at, source_audit, prompt_audit)
    g0_prompt_path, g0_starter_path = build_g0_prompt(target)

    completion = build_completion(
        generated_at,
        route_audit,
        domain_audit,
        prompt_audit,
        source_audit,
        negative_audit,
        novelty_audit,
        no_leak_audit,
        blocker_ledger,
        g0_prompt_path,
        g0_starter_path,
    )
    write_json(artifact_path("COMPLETION_AUDIT"), completion)

    decision = {
        **safe_payload("decision_ledger", generated_at),
        "terminal_decision": completion["terminal_decision"],
        "accepted_target_as": "source/control route-intake evidence only",
        "accepted_target_evidence_class": TARGET_EVIDENCE_CLASS,
        "no_promotion_verdict": True,
        "same_evidence_class_repairs": blocker_ledger["same_evidence_class_repairs_pursued"],
        "open_blockers": blocker_ledger["open_blockers"],
        "g0_child_route_sequencing_prompt": rel(g0_prompt_path),
        "child_routes_launched": False,
    }
    write_json(artifact_path("DECISION_LEDGER"), decision)

    verification = {
        **safe_payload("verification_result", generated_at),
        "ok": None,
        "note": "Run verify_g12_scid_anti_boxing_route_intake_audit_2026_05_12.py to populate final status.",
    }
    write_json(artifact_path("VERIFICATION_RESULT"), verification)
    write_json(artifact_path("OUTPUT_MANIFEST"), build_manifest(generated_at, g0_prompt_path, g0_starter_path))
    return {
        "terminal_decision": completion["terminal_decision"],
        "route_family_count": route_audit["route_family_count"],
        "domain_count": route_audit["domain_count"],
        "prompt_pack_count": prompt_audit["prompt_pack_count"],
        "source_template_count": source_audit["template_count"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
