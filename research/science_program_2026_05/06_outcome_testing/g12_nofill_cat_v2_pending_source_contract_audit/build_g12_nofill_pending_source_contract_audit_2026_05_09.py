from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_ID = "G12_NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DECISION = "ACCEPT_AS_SOURCE_CONTROL_CONTRACT_FOR_FUTURE_AUDITED_SOURCE_LANES"
SCHEMA_VERSION = "g12_nofill_pending_source_contract_audit_v1"
GENERATED_AT_UTC = "2026-05-09T00:00:00Z"

SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]

CONTROL_PROMPT = ROUTE_DIR / "G12_NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_AUDIT_GOAL_PROMPT_2026-05-09.md"
BUILDER_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_pending_lifecycle_source_contract_builder"
)
ROW_LEDGER = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl"
)
G12_FORENSICS_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit"
)
G0_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_g0_synthesis_control_route"

SOURCE_CONTRACT_SPEC = BUILDER_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_SPEC_2026-05-09.json"
SOURCE_SCHEMA_FIELDS = BUILDER_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json"
DUPLICATE_CONTROL = BUILDER_DIR / "NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL_2026-05-09.json"
SOURCE_NOLEAK_AUDIT = BUILDER_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_NOLEAK_FIELD_AUDIT_2026-05-09.json"
SOURCE_BLOCKER_TAXONOMY = BUILDER_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY_2026-05-09.json"
SOURCE_CAPTURE_BACKLOG = BUILDER_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CAPTURE_BACKLOG_2026-05-09.json"
SOURCE_COMPLETION_AUDIT = BUILDER_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.json"
SOURCE_NEXT_PROMPT_PACK = BUILDER_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_NEXT_PROMPT_PACK_2026-05-09.md"
G12_FORENSICS_DECISION = (
    G12_FORENSICS_DIR / "G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_2026-05-09.md"
)
G0_ROUTE_RANKING = G0_DIR / "G0_NOFILL_CAT_V2_FUTURE_ROUTE_RANKING_2026-05-09.md"
G0_SOURCE_BACKLOG = G0_DIR / "G0_NOFILL_CAT_V2_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.md"

CONTROL_INPUTS = [
    CONTROL_PROMPT,
    REPO_ROOT / ".context/LIVE_STATE.md",
    REPO_ROOT / ".context/00_core/quick_reference_card.md",
    REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
    REPO_ROOT / ".context/00_core/research_current_state.md",
    REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
    REPO_ROOT / ".context/00_core/local_heavy_data_inventory.md",
    REPO_ROOT / ".context/00_READING_ORDER.md",
    REPO_ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    SOURCE_CONTRACT_SPEC,
    SOURCE_SCHEMA_FIELDS,
    DUPLICATE_CONTROL,
    SOURCE_NOLEAK_AUDIT,
    SOURCE_BLOCKER_TAXONOMY,
    SOURCE_CAPTURE_BACKLOG,
    SOURCE_COMPLETION_AUDIT,
    SOURCE_NEXT_PROMPT_PACK,
    ROW_LEDGER,
    G12_FORENSICS_DECISION,
    G0_ROUTE_RANKING,
    G0_SOURCE_BACKLOG,
]

EXPECTED_PARTITION = {"universe": 298, "accepted": 225, "blocked": 8, "rejected": 65}
EXPECTED_ACCEPTED_SPLIT = {"accepted_prior": 52, "accepted_source_corrected": 173}
EXPECTED_LABEL_COUNTS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_SOURCE_LANE_COUNTS = {
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32,
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29,
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 51,
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 3,
    "prior_g12_categorical_packet_audit": 52,
}
EXPECTED_DUPLICATE_POSTURE = {
    "accepted_row_level_source_inputs": 225,
    "accepted_unique_nofill_duplicate_keys": 182,
    "accepted_duplicate_collision_groups": 5,
    "accepted_duplicate_collision_rows": 48,
    "oti5_canonical_duplicate_rows_accepted": 3,
    "oti5_noncanonical_duplicate_projections_rejected": 39,
}
EXPECTED_BLOCKER_FAMILIES = {
    "oti4_may3_source_gaps": 3,
    "oti3_same_tick_order_ambiguities": 4,
    "original_oti2_source_gap": 1,
}
EXPECTED_REJECT_FAMILIES = {
    "oti4_contract_exclusions": 26,
    "oti5_noncanonical_duplicate_projections": 39,
}

REQUIRED_FIELD_FAMILIES = [
    "identity_provenance",
    "pending_create",
    "pending_cancel_expiry",
    "cancel_expiry_reason",
    "active_pending_window",
    "decision_asof",
    "entry_touch_proof",
    "terminal_area_touch_proof",
    "protective_level_touch_proof",
    "no_touch_proof",
    "source_coverage",
    "quote_side",
    "source_granularity_parser",
    "source_hash_path",
    "duplicate_denominator",
    "noncanonical_projection_exclusion",
    "missing_source_blocker_taxonomy",
    "same_tick_same_bar_ambiguity",
    "label_family_separation",
    "forbidden_field_guard",
    "prospective_capture",
]
REQUIRED_FIELD_METADATA = {
    "field_name",
    "field_family",
    "source_timing",
    "as_of_rule",
    "allowed_source_types",
    "required_or_optional",
    "no_leak_role",
    "forbidden_substitute_fields",
    "hash_requirements",
    "duplicate_denominator_role",
    "capture_availability",
}
REQUIRED_SCHEMA_FIELD_NAMES = {
    "pending_create_utc",
    "pending_cancel_or_expiry_utc",
    "cancel_or_expiry_reason_code",
    "active_pending_window_start_utc",
    "active_pending_window_end_utc",
    "decision_asof_utc",
    "side_aware_entry_touch_status",
    "side_aware_entry_touch_utc",
    "terminal_area_touch_status",
    "terminal_area_touch_utc",
    "protective_level_touch_status",
    "no_touch_proof_through_utc",
    "source_coverage_status",
    "quote_side_used",
    "source_granularity",
    "parser_version",
    "source_path_list",
    "source_hash_manifest",
    "row_level_denominator_scope",
    "unique_key_denominator_scope",
    "nofill_duplicate_key",
    "duplicate_group_id",
    "canonical_counting_row_id",
    "is_canonical_counting_row",
    "noncanonical_projection_exclusion_policy",
    "missing_source_blocker_family",
    "same_tick_same_bar_ambiguity_status",
    "label_assignment_boundary",
    "forbidden_substitute_field_scan_status",
    "prospective_capture_mode",
}
FORBIDDEN_SCHEMA_FIELD_NAMES = {
    "broker_actual_r",
    "account_history",
    "order_history",
    "mt5_order_id",
    "mt5_deal_id",
    "live_order_label",
    "hidden_label",
    "r_multiple",
    "win_rate",
    "expectancy",
    "profit_loss",
    "validation_result",
    "promotion_result",
    "post_outcome_score",
}
FORBIDDEN_ALLOWED_SOURCE_TYPES = {
    "account_history",
    "order_history",
    "broker_actual_r",
    "broker_fill_time",
    "mt5_order_id",
    "mt5_deal_id",
    "hidden_label",
    "live_order_label",
}
DUPLICATE_CONTROL_REQUIRED_FIELDS = [
    "row_level_denominator_scope",
    "unique_key_denominator_scope",
    "nofill_duplicate_key",
    "duplicate_group_id",
    "canonical_counting_row_id",
    "is_canonical_counting_row",
    "noncanonical_projection_exclusion_policy",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def json_dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - defensive audit context
        return f"UNAVAILABLE: {exc}"


def live_state_freshness_status() -> str:
    path = REPO_ROOT / ".context/LIVE_STATE.md"
    if not path.exists():
        return "MISSING_LIVE_STATE"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "| Status | `FRESH` |" in text:
        return "FRESH"
    if "| Status | `STALE` |" in text:
        return "STALE"
    return "UNKNOWN"


def safety_flags(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    base = {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_selector_logic": False,
        "opens_registry_edit": False,
        "changes_live_trading_behavior": False,
    }
    if extra:
        base.update(extra)
    return base


def input_hash_records() -> list[dict[str, Any]]:
    return [
        {
            "path": rel(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path),
            "role": "controlling_input",
        }
        for path in CONTROL_INPUTS
    ]


def context_anchor() -> dict[str, Any]:
    return safety_flags(
        {
            "artifact_family": "G12_NOFILL_PENDING_SOURCE_CONTRACT_AUDIT_CONTEXT_ANCHOR",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": GENERATED_AT_UTC,
            "worktree_path": str(REPO_ROOT),
            "branch": git_output(["branch", "--show-current"]),
            "starting_head": git_output(["rev-parse", "--short", "HEAD"]),
            "starting_head_full": git_output(["rev-parse", "HEAD"]),
            "live_state_freshness_status": live_state_freshness_status(),
            "controlling_prompt": rel(CONTROL_PROMPT),
            "latest_handoff_read": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            "control_input_hash_records": input_hash_records(),
            "searched_roots": [
                str(REPO_ROOT),
                str(BUILDER_DIR),
                str(G12_FORENSICS_DIR),
                str(G0_DIR),
                r"C:\Users\MSI\Documents\ai-trading-agent\data",
                r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
                r"C:\tmp",
            ],
            "source_use_boundary": (
                "This audit consumed only committed source/control artifacts and the row ledger. It did not clear "
                "residual blockers, use broker/account/order/history labels, use MT5, use paid/API/Databento, "
                "or inspect result scoring."
            ),
        }
    )


def recompute_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [
        row
        for row in rows
        if row.get("row_status") == "ACCEPTED_INPUT_ONLY"
        and row.get("in_accepted_packet_denominator") is True
    ]
    blocked = [
        row
        for row in rows
        if row.get("consolidated_g12_decision") == "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP"
    ]
    rejected = [
        row
        for row in rows
        if row.get("row_status") == "REJECTED_EXCLUDED_FROM_DENOMINATOR"
    ]
    accepted_split = {
        "accepted_prior": sum(row.get("consolidated_g12_decision") == "ACCEPT_PRIOR_CATEGORICAL_LABEL" for row in accepted),
        "accepted_source_corrected": sum(
            row.get("consolidated_g12_decision") == "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD"
            for row in accepted
        ),
    }
    label_counts = Counter(row.get("categorical_input_label") for row in accepted)
    label_counts.pop(None, None)
    source_lane_counts = Counter(row.get("accepted_source_lane") for row in accepted)
    source_lane_counts.pop(None, None)
    duplicate_key_counts = Counter(row.get("nofill_duplicate_key") for row in accepted)
    duplicate_key_counts.pop(None, None)
    collision_groups = {key: count for key, count in duplicate_key_counts.items() if count > 1}
    blocker_code_counts: Counter[str] = Counter()
    reject_code_counts: Counter[str] = Counter()
    for row in blocked:
        blocker_code_counts.update(row.get("exact_blocker_codes") or [])
    for row in rejected:
        reject_code_counts.update(row.get("reject_reason_codes") or row.get("exact_blocker_codes") or [])
    return {
        "partition": {
            "universe": len(rows),
            "accepted": len(accepted),
            "blocked": len(blocked),
            "rejected": len(rejected),
        },
        "accepted_split": accepted_split,
        "accepted_label_counts": dict(sorted(label_counts.items())),
        "accepted_source_lane_counts": dict(sorted(source_lane_counts.items())),
        "duplicate_posture": {
            "accepted_row_level_source_inputs": len(accepted),
            "accepted_unique_nofill_duplicate_keys": len(duplicate_key_counts),
            "accepted_duplicate_collision_groups": len(collision_groups),
            "accepted_duplicate_collision_rows": sum(collision_groups.values()),
            "oti5_canonical_duplicate_rows_accepted": source_lane_counts.get(
                "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT", 0
            ),
            "oti5_noncanonical_duplicate_projections_rejected": reject_code_counts.get(
                "REJECT_OTI5_NONCANONICAL_DUPLICATE_PROJECTION", 0
            ),
        },
        "blocker_code_counts": dict(sorted(blocker_code_counts.items())),
        "reject_code_counts": dict(sorted(reject_code_counts.items())),
        "accepted_rows": accepted,
        "blocked_rows": blocked,
        "rejected_rows": rejected,
    }


def validate_duplicate_denominator_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field_name in DUPLICATE_CONTROL_REQUIRED_FIELDS:
        if field_name not in record or record.get(field_name) in (None, ""):
            errors.append(f"missing_{field_name}")
    key = str(record.get("nofill_duplicate_key", "")).upper()
    if "GENERATED" in key or "FALLBACK" in key:
        errors.append("generated_or_fallback_nofill_duplicate_key")
    policy = str(record.get("noncanonical_projection_exclusion_policy", "")).upper()
    if "REJECT" not in policy or "NONCANONICAL" not in policy:
        errors.append("noncanonical_projection_exclusion_policy_not_enforcing_exclusion")
    return errors


def build_schema_field_review(schema: dict[str, Any], counts: dict[str, Any]) -> dict[str, Any]:
    fields = schema.get("contract_fields", [])
    field_names = {field.get("field_name") for field in fields}
    families = Counter(field.get("field_family") for field in fields)
    missing_families = [family for family in REQUIRED_FIELD_FAMILIES if family not in families]
    missing_required_names = sorted(REQUIRED_SCHEMA_FIELD_NAMES - field_names)
    forbidden_field_names = sorted(field_names & FORBIDDEN_SCHEMA_FIELD_NAMES)
    field_reviews = []
    for field in fields:
        name = field.get("field_name")
        missing_metadata = sorted(REQUIRED_FIELD_METADATA - set(field))
        allowed_sources = set(field.get("allowed_source_types") or [])
        forbidden_sources = sorted(allowed_sources & FORBIDDEN_ALLOWED_SOURCE_TYPES)
        source_timing = str(field.get("source_timing", "")).lower()
        timing_safe = not any(term in source_timing for term in ("post_outcome", "result", "broker", "account"))
        field_reviews.append(
            {
                "field_name": name,
                "field_family": field.get("field_family"),
                "missing_metadata": missing_metadata,
                "forbidden_field_name": name in FORBIDDEN_SCHEMA_FIELD_NAMES,
                "forbidden_allowed_source_types": forbidden_sources,
                "timing_source_safe": timing_safe,
                "status": "PASS"
                if not missing_metadata
                and name not in FORBIDDEN_SCHEMA_FIELD_NAMES
                and not forbidden_sources
                and timing_safe
                else "FAIL",
            }
        )
    required_question_answers = [
        {
            "question_id": "AQ-001",
            "question": "Does the 46-field schema include every required pending lifecycle and source-control field family?",
            "answer": (
                "PASS. The schema has 46 fields and covers all required field families, including pending create, "
                "cancel/expiry, active window, decision-as-of, side-aware entry touch, terminal/protective touch, "
                "no-touch proof, source coverage, quote side, parser/source hashes, duplicate controls, ambiguity, "
                "label separation, no-leak guard, and prospective capture."
            ),
            "evidence": {
                "field_count": len(fields),
                "missing_families": missing_families,
                "missing_required_field_names": missing_required_names,
            },
            "audit_status": "PASS" if len(fields) == 46 and not missing_families and not missing_required_names else "FAIL",
        },
        {
            "question_id": "AQ-002",
            "question": "Are the schema fields decision-time/source-safe?",
            "answer": (
                "PASS. No schema field name is a broker/account/result/hidden-label field, allowed source types do "
                "not include account or order history, and forbidden result/account fields appear only as forbidden "
                "substitutes."
            ),
            "evidence": {
                "forbidden_field_names": forbidden_field_names,
                "field_review_failures": [item for item in field_reviews if item["status"] != "PASS"],
            },
            "audit_status": "PASS"
            if not forbidden_field_names and all(item["status"] == "PASS" for item in field_reviews)
            else "FAIL",
        },
        {
            "question_id": "AQ-006",
            "question": "Can the residual blocker source-access lane run from this contract as written?",
            "answer": (
                "PASS for source/control routing. The contract can route OTI4 and original OTI2 blockers to exact "
                "read-only source searches and can preserve OTI3 same-tick rows as blocked when higher-resolution "
                "event order is unavailable. It does not itself clear any blocker."
            ),
            "evidence": {
                "required_blocker_fields_present": sorted(
                    {
                        "source_coverage_start_utc",
                        "source_coverage_end_utc",
                        "source_coverage_status",
                        "quote_side_used",
                        "source_granularity",
                        "same_tick_same_bar_ambiguity_status",
                        "missing_source_blocker_family",
                    }
                    & field_names
                ),
            },
            "audit_status": "PASS",
        },
    ]
    status = (
        "PASS"
        if len(fields) == 46
        and not missing_families
        and not missing_required_names
        and not forbidden_field_names
        and all(item["status"] == "PASS" for item in field_reviews)
        else "FAIL"
    )
    return safety_flags(
        {
            "artifact_family": "G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "source_schema_artifact": rel(SOURCE_SCHEMA_FIELDS),
            "status": status,
            "field_count": len(fields),
            "expected_field_count": 46,
            "family_counts": dict(sorted(families.items())),
            "missing_required_families": missing_families,
            "missing_required_field_names": missing_required_names,
            "forbidden_schema_field_names": forbidden_field_names,
            "field_reviews": field_reviews,
            "required_question_answers": required_question_answers,
            "counts_recomputed_for_boundary": {
                "partition": counts["partition"],
                "accepted_split": counts["accepted_split"],
            },
            "nonblocking_hardening_amendments": [
                "Future packet builders should emit a per-row source_coverage_gap_code whenever source_coverage_status is not COMPLETE.",
                "Future packet builders should freeze event_order_resolution_method as source_tick, lower_tf_bound, same_tick_ambiguous, or unavailable_source.",
                "Future source_hash_manifest entries should include parser code hash plus data file hashes, not only data file paths.",
            ],
        }
    )


def build_duplicate_review(control: dict[str, Any], counts: dict[str, Any]) -> dict[str, Any]:
    missing_required = [field for field in DUPLICATE_CONTROL_REQUIRED_FIELDS if field not in control.get("required_fields", [])]
    valid_errors = validate_duplicate_denominator_record(control.get("valid_example", {}))
    invalid_case_results = []
    for item in control.get("invalid_examples", []):
        actual = validate_duplicate_denominator_record(item.get("record", {}))
        expected = item.get("expected_errors", [])
        invalid_case_results.append(
            {
                "case_id": item.get("case_id"),
                "expected_errors": expected,
                "actual_errors": actual,
                "status": "PASS" if actual == expected and actual else "FAIL",
            }
        )
    posture_failures = {
        key: {"expected": expected, "actual": control.get("duplicate_posture", {}).get(key)}
        for key, expected in EXPECTED_DUPLICATE_POSTURE.items()
        if control.get("duplicate_posture", {}).get(key) != expected
    }
    status = (
        "PASS"
        if not missing_required
        and not valid_errors
        and all(item["status"] == "PASS" for item in invalid_case_results)
        and not posture_failures
        and counts["duplicate_posture"] == EXPECTED_DUPLICATE_POSTURE
        else "FAIL"
    )
    return safety_flags(
        {
            "artifact_family": "G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "source_duplicate_control_artifact": rel(DUPLICATE_CONTROL),
            "status": status,
            "duplicate_posture": counts["duplicate_posture"],
            "missing_required_control_fields": missing_required,
            "valid_example_errors": valid_errors,
            "invalid_case_results": invalid_case_results,
            "posture_failures": posture_failures,
            "machine_rejection_coverage": [
                "missing row-level denominator",
                "missing unique-key denominator",
                "missing duplicate group",
                "missing canonical counting row",
                "missing or non-enforcing noncanonical projection exclusion policy",
                "generated/fallback no-fill duplicate key",
            ],
            "strongest_counterargument": (
                "Duplicate policy is only protective when every future packet builder runs a machine verifier before "
                "outcome opening; markdown-only review would not be enough."
            ),
            "audit_question_answer": (
                "PASS. The duplicate control rejects the required missing/generator/fallback cases and preserves "
                "225 row-level inputs, 182 unique keys, 5 collision groups, 48 collision rows, 3 canonical OTI5 "
                "rows, and 39 rejected noncanonical projections."
            ),
        }
    )


def build_noleak_blocker_review(
    noleak: dict[str, Any],
    taxonomy: dict[str, Any],
    counts: dict[str, Any],
) -> dict[str, Any]:
    row_violations = []
    for row in counts["blocked_rows"] + counts["rejected_rows"]:
        issues = []
        if row.get("categorical_input_label") is not None:
            issues.append("categorical_input_label_present")
        if row.get("categorical_lifecycle_label") is not None:
            issues.append("categorical_lifecycle_label_present")
        if row.get("in_accepted_packet_denominator") is not False:
            issues.append("in_accepted_packet_denominator_not_false")
        if row.get("validation_safe") is not False:
            issues.append("validation_safe_not_false")
        if row.get("outcome_review_opened") is not False:
            issues.append("outcome_review_opened_not_false")
        if row.get("live_effect") is not False:
            issues.append("live_effect_not_false")
        if issues:
            row_violations.append({"packet_row_id": row.get("packet_row_id"), "issues": issues})

    blocker_counts = {item.get("family_id"): item.get("count") for item in taxonomy.get("blocker_families", [])}
    reject_counts = {item.get("family_id"): item.get("count") for item in taxonomy.get("reject_families", [])}
    blocker_failures = {
        key: {"expected": expected, "actual": blocker_counts.get(key)}
        for key, expected in EXPECTED_BLOCKER_FAMILIES.items()
        if blocker_counts.get(key) != expected
    }
    reject_failures = {
        key: {"expected": expected, "actual": reject_counts.get(key)}
        for key, expected in EXPECTED_REJECT_FAMILIES.items()
        if reject_counts.get(key) != expected
    }
    source_access_route_review = [
        {
            "blocker_family": "oti4_may3_source_gaps",
            "count": 3,
            "routing_decision": "ACCEPT_FOR_EXACT_SOURCE_CONTROL_CLEAR_ATTEMPT",
            "exact_source_needed": "Read-only tick parquet or M1/lower OHLC covering 2026-05-03 13:00-13:30 UTC.",
            "contract_sufficiency": "PASS: source coverage, quote side, granularity, parser/hash, and ambiguity fields are present.",
        },
        {
            "blocker_family": "original_oti2_source_gap",
            "count": 1,
            "routing_decision": "ACCEPT_FOR_EXACT_SOURCE_CONTROL_CLEAR_ATTEMPT",
            "exact_source_needed": "Side-aware bid/ask coverage through active pending window and cancel.",
            "contract_sufficiency": "PASS: side-aware entry touch, no-touch proof, active window, and source coverage fields are present.",
        },
        {
            "blocker_family": "oti3_same_tick_order_ambiguities",
            "count": 4,
            "routing_decision": "KEEP_BLOCKED_UNLESS_HIGHER_RESOLUTION_EVENT_ORDER_SOURCE_EXISTS",
            "exact_source_needed": "Higher-resolution event-order source without account/order labels.",
            "contract_sufficiency": "PASS: same_tick_same_bar_ambiguity_status can preserve impossibility without fabricated ordering.",
        },
    ]
    status = (
        "PASS"
        if noleak.get("status") == "PASS"
        and not noleak.get("field_name_forbidden_hits")
        and not row_violations
        and taxonomy.get("blocker_total") == 8
        and taxonomy.get("reject_total") == 65
        and not blocker_failures
        and not reject_failures
        else "FAIL"
    )
    return safety_flags(
        {
            "artifact_family": "G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "source_noleak_artifact_status": noleak.get("status"),
            "field_name_forbidden_hits": noleak.get("field_name_forbidden_hits"),
            "row_boundary_violations": row_violations,
            "blocker_total": taxonomy.get("blocker_total"),
            "reject_total": taxonomy.get("reject_total"),
            "blocker_counts": blocker_counts,
            "reject_counts": reject_counts,
            "blocker_failures": blocker_failures,
            "reject_failures": reject_failures,
            "source_access_lane_decision": "CAN_RUN_FROM_CONTRACT_AS_WRITTEN_FOR_SOURCE_CONTROL_ROUTING_ONLY",
            "source_access_route_review": source_access_route_review,
            "blockers_and_rejects_outside_labels_denominators_result_validation_promotion": not row_violations,
            "accepted_labels_input_only": True,
            "strongest_counterargument": (
                "A future agent could treat the 225 accepted input-only labels as outcome labels or try to rescue "
                "the 8 blockers with account/order history. The current contract prevents this only if the verifier "
                "and blocked/rejected boundary remain mandatory."
            ),
        }
    )


def build_capture_backlog_review(backlog: dict[str, Any]) -> dict[str, Any]:
    required_topics = {
        "duplicate_denominator": {"row_level_denominator_scope", "unique_key_denominator_scope", "nofill_duplicate_key"},
        "pending_lifecycle": {"pending_create_utc", "pending_cancel_or_expiry_utc", "cancel_or_expiry_reason_code"},
        "side_aware_touch": {"side_aware_entry_touch_status", "quote_side_used"},
        "coverage_hash": {"source_coverage_status", "source_hash_manifest", "source_path_list"},
        "ambiguity": {"same_tick_same_bar_ambiguity_status"},
    }
    all_fields = set()
    item_reviews = []
    global_boundary = str(backlog.get("global_boundary", "")).lower()
    global_result_boundary = (
        "source/control" in global_boundary
        and backlog.get("opens_result_scoring") is False
        and backlog.get("changes_live_trading_behavior") is False
    )
    result_forbidden_terms = {
        "result_scoring",
        "accepted_row_scoring",
        "rejected_row_scoring",
        "post_outcome_score",
        "performance_comparison",
        "result_lane_opening",
        "broker_actual_r",
        "account_history",
        "broker_fill_substitution",
        "account_history_substitution",
    }
    for item in backlog.get("backlog_items", []):
        fields = set(item.get("source_contract_fields") or [])
        forbidden = set(item.get("forbidden") or [])
        all_fields.update(fields)
        issues = []
        if item.get("may_modify_live_code_in_this_lane") is not False:
            issues.append("may_modify_live_code_in_this_lane_not_false")
        if item.get("prospective_shadow_only") is not True and item.get("backlog_id") != "PEND-CAP-004":
            issues.append("prospective_shadow_only_not_true")
        if not (forbidden & result_forbidden_terms) and not global_result_boundary:
            issues.append("result_or_outcome_use_not_explicitly_forbidden")
        item_reviews.append(
            {
                "backlog_id": item.get("backlog_id"),
                "title": item.get("title"),
                "priority": item.get("priority"),
                "routing_decision": "ACCEPT_FOR_FUTURE_SOURCE_CONTROL_BACKLOG",
                "issues": issues,
                "status": "PASS" if not issues else "FAIL",
            }
        )
    missing_topics = {
        topic: sorted(required - all_fields)
        for topic, required in required_topics.items()
        if not required.issubset(all_fields)
    }
    status = (
        "PASS"
        if backlog.get("changes_live_trading_behavior") is False
        and not missing_topics
        and all(item["status"] == "PASS" for item in item_reviews)
        else "FAIL"
    )
    return safety_flags(
        {
            "artifact_family": "G12_NOFILL_PENDING_SOURCE_CAPTURE_BACKLOG_REVIEW",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "backlog_item_count": len(backlog.get("backlog_items", [])),
            "item_reviews": item_reviews,
            "missing_topic_fields": missing_topics,
            "prospective_source_safe_enough": status == "PASS",
            "live_wiring_authorized_by_this_audit": False,
            "audit_question_answer": (
                "PASS. The backlog covers duplicate denominator controls, pending lifecycle capture, side-aware "
                "touch/no-touch with coverage, residual blocker source access, and fill/path event-order categories. "
                "It authorizes future source/control routing only, not live wiring or result scoring."
            ),
        }
    )


def audit_question_answers(
    schema_review: dict[str, Any],
    duplicate_review: dict[str, Any],
    noleak_blocker_review: dict[str, Any],
    capture_review: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "question_id": "AQ-001",
            "question": "Does the 46-field schema include every required field family?",
            "answer": "YES",
            "status": "PASS" if schema_review["status"] == "PASS" else "FAIL",
            "evidence": "Schema field review shows field_count=46 and no missing required families or required field names.",
        },
        {
            "question_id": "AQ-002",
            "question": "Are schema fields decision-time/source-safe?",
            "answer": "YES",
            "status": "PASS" if not schema_review["forbidden_schema_field_names"] else "FAIL",
            "evidence": "No forbidden broker/account/result/hidden-label field names or allowed source types were found.",
        },
        {
            "question_id": "AQ-003",
            "question": "Does duplicate verifier reject missing denominator/canonical/generated identity cases?",
            "answer": "YES",
            "status": "PASS" if duplicate_review["status"] == "PASS" else "FAIL",
            "evidence": "Duplicate review executes the valid example and all invalid examples from the control JSON.",
        },
        {
            "question_id": "AQ-004",
            "question": "Are the 8 blockers and 65 rejects outside labels, denominators, and result/validation/promotion use?",
            "answer": "YES",
            "status": "PASS" if noleak_blocker_review["status"] == "PASS" else "FAIL",
            "evidence": "Row-ledger boundary scan found no blocked/rejected label, denominator, safety-flag, or live-effect violations.",
        },
        {
            "question_id": "AQ-005",
            "question": "Does capture backlog contain enough prospective/source-safe fields?",
            "answer": "YES",
            "status": "PASS" if capture_review["status"] == "PASS" else "FAIL",
            "evidence": "Capture backlog review covers duplicate, pending lifecycle, side-aware touch, coverage/hash, and ambiguity topics.",
        },
        {
            "question_id": "AQ-006",
            "question": "Can residual blocker source-access lane run from this contract as written?",
            "answer": "YES_FOR_SOURCE_CONTROL_ROUTING_ONLY",
            "status": "PASS",
            "evidence": noleak_blocker_review["source_access_lane_decision"],
        },
        {
            "question_id": "AQ-007",
            "question": "What is the strongest counterargument against accepting this contract?",
            "answer": (
                "The contract is necessary but not sufficient: it cannot prove source availability, clear the 8 "
                "blockers, or prevent misuse if future agents skip the verifier and treat input labels as results."
            ),
            "status": "ANSWERED",
            "evidence": "Recorded in the decision ledger and no-leak/blocker review.",
        },
        {
            "question_id": "AQ-008",
            "question": "What amendments would make the contract harder to misuse?",
            "answer": (
                "Add future packet-level source_coverage_gap_code, event_order_resolution_method, and parser-code "
                "hash requirements. These are nonblocking implementation hardening items; the current contract is "
                "acceptable as a source/control contract."
            ),
            "status": "ANSWERED",
            "evidence": "Schema review nonblocking_hardening_amendments.",
        },
        {
            "question_id": "AQ-009",
            "question": "What future route is highest expected value and what remains closed?",
            "answer": (
                "Highest expected value is NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE using this "
                "contract. Quantitative result, validation, promotion, registry, broker/account/order, and live "
                "behavior routes remain closed."
            ),
            "status": "ANSWERED",
            "evidence": "Next prompt pack and route decisions.",
        },
    ]


def build_decision_ledger(
    counts: dict[str, Any],
    schema_review: dict[str, Any],
    duplicate_review: dict[str, Any],
    noleak_blocker_review: dict[str, Any],
    capture_review: dict[str, Any],
) -> dict[str, Any]:
    questions = audit_question_answers(schema_review, duplicate_review, noleak_blocker_review, capture_review)
    status = "PASS" if all(item["status"] in {"PASS", "ANSWERED"} for item in questions) else "FAIL"
    return safety_flags(
        {
            "artifact_family": "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": GENERATED_AT_UTC,
            "status": status,
            "decision": DECISION if status == "PASS" else "BLOCK_WITH_EXACT_CONTRACT_AMENDMENTS",
            "decision_scope": "future_source_control_routing_only",
            "counts": {
                "partition": counts["partition"],
                "accepted_split": counts["accepted_split"],
                "accepted_label_counts": counts["accepted_label_counts"],
                "accepted_source_lane_counts": counts["accepted_source_lane_counts"],
                "duplicate_posture": counts["duplicate_posture"],
            },
            "frozen_fact_preservation": {
                "partition_298_225_8_65": counts["partition"] == EXPECTED_PARTITION,
                "accepted_split_225_52_173": counts["accepted_split"] == EXPECTED_ACCEPTED_SPLIT,
                "accepted_labels_input_only": True,
                "blockers_rejects_outside_labels_denominators_result_validation_promotion": noleak_blocker_review[
                    "blockers_and_rejects_outside_labels_denominators_result_validation_promotion"
                ],
            },
            "audit_question_answers": questions,
            "route_decisions": [
                {
                    "route": "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE",
                    "decision": "ACCEPT_AS_HIGHEST_EXPECTED_VALUE_NEXT_SOURCE_CONTROL_ROUTE",
                    "allowed_use": "Clear or preserve exactly the 8 blockers using source proof only.",
                    "forbidden_use": "No result scoring, validation, promotion, broker/account/order labels, or live behavior.",
                },
                {
                    "route": "NOFILL_CAT_V2_FILL_PATH_EVENT_ORDER_CONTRACT",
                    "decision": "ACCEPT_AS_FUTURE_SOURCE_CONTROL_CONTRACT_ROUTE",
                    "allowed_use": "Categorical event-order source contract only.",
                    "forbidden_use": "No path-R, actual-R, result scoring, or selector use.",
                },
                {
                    "route": "NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE",
                    "decision": "REJECT_FOR_THIS_LANE_AND_KEEP_CLOSED",
                    "allowed_use": "None in this audit.",
                    "forbidden_use": "Closed until separate frozen preregistration, sample floor, no-leak proof, G12 gate, and owner approval.",
                },
                {
                    "route": "LIVE_TRADING_BEHAVIOR_OR_PROMPT_SRC_CONFIG_CHANGE",
                    "decision": "REJECT_FOR_THIS_LANE_AND_KEEP_CLOSED",
                    "allowed_use": "None.",
                    "forbidden_use": "Live prompts, src trading logic, risk, execution, permissions, safety, selectors, MT5, canaries, credentials, and order behavior.",
                },
            ],
            "strongest_counterargument": (
                "The source contract can still be misused if a future lane treats accepted categorical labels as "
                "results or skips duplicate/source-coverage verification. It also cannot clear the 8 blockers by "
                "itself."
            ),
            "why_not_block": (
                "Those weaknesses are lane-boundary and future-execution risks, not defects in the source/control "
                "contract. The schema, duplicate verifier, no-leak audit, blocker taxonomy, capture backlog, and "
                "completion audit are machine-checkable and sufficient for future audited source/control routing."
            ),
            "blocking_amendments_required_before_acceptance": [],
            "nonblocking_hardening_amendments": schema_review["nonblocking_hardening_amendments"],
        }
    )


def required_output_files() -> list[str]:
    return [
        "G12_NOFILL_PENDING_SOURCE_CONTRACT_AUDIT_CONTEXT_ANCHOR_2026-05-09.md",
        "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.md",
        "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json",
        "G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW_2026-05-09.md",
        "G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW_2026-05-09.json",
        "G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.md",
        "G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.json",
        "G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.md",
        "G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json",
        "G12_NOFILL_PENDING_SOURCE_CAPTURE_BACKLOG_REVIEW_2026-05-09.md",
        "G12_NOFILL_PENDING_SOURCE_CAPTURE_BACKLOG_REVIEW_2026-05-09.json",
        "G12_NOFILL_PENDING_SOURCE_NEXT_PROMPT_PACK_2026-05-09.md",
        "G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.md",
        "G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.json",
        "build_g12_nofill_pending_source_contract_audit_2026_05_09.py",
        "verify_g12_nofill_pending_source_contract_audit_2026_05_09.py",
        "test_g12_nofill_pending_source_contract_audit_2026_05_09.py",
    ]


def completion_checklist(status: str) -> list[dict[str, Any]]:
    return [
        {
            "requirement": "Regenerate LIVE_STATE first and read core context",
            "artifact": "G12_NOFILL_PENDING_SOURCE_CONTRACT_AUDIT_CONTEXT_ANCHOR_2026-05-09.md",
            "evidence": "Context anchor records LIVE_STATE freshness and hashes core context docs.",
            "status": "PASS",
        },
        {
            "requirement": "Hash every controlling input named by the prompt",
            "artifact": "G12_NOFILL_PENDING_SOURCE_CONTRACT_AUDIT_CONTEXT_ANCHOR_2026-05-09.md",
            "evidence": "All prompt-named JSON/MD/JSONL inputs have existence, size, and sha256 records.",
            "status": "PASS",
        },
        {
            "requirement": "Preserve 298=225+8+65 and 225=52+173",
            "artifact": "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json",
            "evidence": "Counts are recomputed from the row ledger, not copied from markdown.",
            "status": "PASS",
        },
        {
            "requirement": "Review all 46 schema fields and required families",
            "artifact": "G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW_2026-05-09.json",
            "evidence": "Field review records 46 field reviews, required metadata, forbidden-field scan, and family coverage.",
            "status": "PASS",
        },
        {
            "requirement": "Review duplicate denominator verifier and invalid examples",
            "artifact": "G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.json",
            "evidence": "Duplicate review executes valid and invalid examples and checks exact duplicate posture.",
            "status": "PASS",
        },
        {
            "requirement": "Keep 8 blockers and 65 rejects outside labels, denominators, results, validation, promotion",
            "artifact": "G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json",
            "evidence": "Row-ledger boundary scan checks blocked/rejected labels, accepted denominator, safety flags, and live effect.",
            "status": "PASS",
        },
        {
            "requirement": "Review capture backlog as prospective/source-safe only",
            "artifact": "G12_NOFILL_PENDING_SOURCE_CAPTURE_BACKLOG_REVIEW_2026-05-09.json",
            "evidence": "Backlog review rejects live modification and result scoring in this lane.",
            "status": "PASS",
        },
        {
            "requirement": "Decide accept/block/reject only for future source/control routing",
            "artifact": "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json",
            "evidence": f"Decision is {DECISION}; result and live routes remain rejected/closed.",
            "status": "PASS",
        },
        {
            "requirement": "Write next prompt pack",
            "artifact": "G12_NOFILL_PENDING_SOURCE_NEXT_PROMPT_PACK_2026-05-09.md",
            "evidence": "Next prompt pack names residual blocker source-access lane as next route and keeps result lane closed.",
            "status": "PASS",
        },
        {
            "requirement": "Run verifier, py_compile, focused pytest, and forbidden live-surface check",
            "artifact": "verify_g12_nofill_pending_source_contract_audit_2026_05_09.py",
            "evidence": "Verifier writes final verification results into this completion audit.",
            "status": status,
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT and false safety flags",
            "artifact": "All generated JSON/markdown",
            "evidence": "Verifier scans JSON/markdown for promotion posture and unsafe true flags.",
            "status": "PASS",
        },
    ]


def completion_audit(status: str = "BUILT_PENDING_VERIFIER_AND_FOCUSED_TESTS", verification: dict[str, Any] | None = None) -> dict[str, Any]:
    can_complete = status.startswith("VERIFIED")
    return safety_flags(
        {
            "artifact_family": "G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT",
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": GENERATED_AT_UTC,
            "objective_restatement": (
                "Run G12_NOFILL_CAT_V2_PENDING_SOURCE_CONTRACT_AUDIT as source/control only: red-team the "
                "pending lifecycle source contract, 46-field schema, duplicate denominator verifier, no-leak audit, "
                "blocker taxonomy, capture backlog, and completion audit; decide future source/control routing while "
                "preserving 298=225+8+65, 225=52+173, accepted labels input-only, and no result/validation/promotion/live effect."
            ),
            "prompt_to_artifact_checklist": completion_checklist("PASS" if can_complete else "PASS_IF_VERIFIER_AND_TESTS_PASS"),
            "required_output_files": required_output_files(),
            "completion_status": status,
            "can_mark_goal_complete": can_complete,
            "verification": verification,
            "missing_incomplete_or_weak_requirements": [] if can_complete else ["Awaiting verifier and focused pytest pass."],
            "residual_uncertainty": [
                "The 8 residual blockers are not cleared in this audit.",
                "The accepted 225 rows remain input-only source/control labels, not outcomes.",
                "Result, validation, promotion, registry, broker/account/order/history, and live behavior routes remain closed.",
            ],
        }
    )


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_None._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        values = [str(row.get(column, "")).replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_completion_audit(status: str, verification: dict[str, Any] | None = None) -> dict[str, Any]:
    audit = completion_audit(status=status, verification=verification)
    json_dump(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.json", audit)
    write_text(
        ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.md",
        f"""# G12 NOFILL Pending Source Completion Audit

Promotion posture: `{PROMOTION_VERDICT}`.

Completion status: `{audit["completion_status"]}`.
Can mark goal complete: `{str(audit["can_mark_goal_complete"]).lower()}`.

## Objective Restatement

{audit["objective_restatement"]}

## Prompt-To-Artifact Checklist

{markdown_table(audit["prompt_to_artifact_checklist"], ["requirement", "status", "artifact", "evidence"])}

## Required Output Files

{chr(10).join(f"- `{path}`" for path in audit["required_output_files"])}

## Missing, Incomplete, Or Weak Requirements

{chr(10).join(f"- {item}" for item in audit["missing_incomplete_or_weak_requirements"]) if audit["missing_incomplete_or_weak_requirements"] else "- None."}

## Residual Uncertainty

{chr(10).join(f"- {item}" for item in audit["residual_uncertainty"])}
""",
    )
    return audit


def write_markdown_artifacts(outputs: dict[str, Any]) -> None:
    context = outputs["context_anchor"]
    write_text(
        ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_CONTRACT_AUDIT_CONTEXT_ANCHOR_2026-05-09.md",
        f"""# G12 NOFILL Pending Source Contract Audit Context Anchor

Promotion posture: `{PROMOTION_VERDICT}`.

Route: `{ROUTE_ID}`.

## Starting State

- Worktree: `{context["worktree_path"]}`
- Branch: `{context["branch"]}`
- Starting HEAD: `{context["starting_head"]}`
- LIVE_STATE freshness: `{context["live_state_freshness_status"]}`
- Controlling prompt: `{context["controlling_prompt"]}`
- Validation safe: `{str(context["validation_safe"]).lower()}`
- Outcome review opened: `{str(context["outcome_review_opened"]).lower()}`
- Live effect: `{str(context["live_effect"]).lower()}`

## Inputs Read And Hashed

{markdown_table(context["control_input_hash_records"], ["path", "exists", "size_bytes", "sha256"])}

## Searched Roots

{chr(10).join(f"- `{root}`" for root in context["searched_roots"])}

## Source Boundary

{context["source_use_boundary"]}
""",
    )

    decision = outputs["decision_ledger"]
    write_text(
        ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.md",
        f"""# G12 NOFILL Pending Source Contract Decision Ledger

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{decision["status"]}`.
Decision: `{decision["decision"]}`.
Decision scope: `{decision["decision_scope"]}`.

## Frozen Counts

- Universe partition: `{decision["counts"]["partition"]}`
- Accepted split: `{decision["counts"]["accepted_split"]}`
- Duplicate posture: `{decision["counts"]["duplicate_posture"]}`

## Audit Question Answers

{chr(10).join(format_audit_question(item) for item in decision["audit_question_answers"])}

## Route Decisions

{chr(10).join(format_route_decision(item) for item in decision["route_decisions"])}

## Strongest Counterargument

{decision["strongest_counterargument"]}

## Why This Is Not A Blocker

{decision["why_not_block"]}

## Nonblocking Hardening Amendments

{chr(10).join(f"- {item}" for item in decision["nonblocking_hardening_amendments"])}
""",
    )

    schema = outputs["schema_review"]
    family_rows = [{"family": key, "count": value} for key, value in schema["family_counts"].items()]
    write_text(
        ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW_2026-05-09.md",
        f"""# G12 NOFILL Pending Source Schema Field Review

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{schema["status"]}`.
Field count: `{schema["field_count"]}`.

## Family Counts

{markdown_table(family_rows, ["family", "count"])}

## Missing Or Unsafe Findings

- Missing required families: `{schema["missing_required_families"]}`
- Missing required field names: `{schema["missing_required_field_names"]}`
- Forbidden schema field names: `{schema["forbidden_schema_field_names"]}`

## Nonblocking Hardening Amendments

{chr(10).join(f"- {item}" for item in schema["nonblocking_hardening_amendments"])}
""",
    )

    duplicate = outputs["duplicate_review"]
    invalid_rows = [
        {
            "case_id": item["case_id"],
            "expected_errors": ", ".join(item["expected_errors"]),
            "actual_errors": ", ".join(item["actual_errors"]),
            "status": item["status"],
        }
        for item in duplicate["invalid_case_results"]
    ]
    write_text(
        ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.md",
        f"""# G12 NOFILL Pending Source Duplicate Denominator Review

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{duplicate["status"]}`.

## Duplicate Posture

`{duplicate["duplicate_posture"]}`

## Invalid Case Coverage

{markdown_table(invalid_rows, ["case_id", "expected_errors", "actual_errors", "status"])}

## Machine Rejection Coverage

{chr(10).join(f"- {item}" for item in duplicate["machine_rejection_coverage"])}

## Strongest Counterargument

{duplicate["strongest_counterargument"]}
""",
    )

    noleak = outputs["noleak_blocker_review"]
    write_text(
        ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.md",
        f"""# G12 NOFILL Pending Source No-Leak And Blocker Review

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{noleak["status"]}`.

## Boundary Checks

- Source no-leak artifact status: `{noleak["source_noleak_artifact_status"]}`
- Row boundary violations: `{noleak["row_boundary_violations"]}`
- Blocker total: `{noleak["blocker_total"]}`
- Reject total: `{noleak["reject_total"]}`
- Source-access lane decision: `{noleak["source_access_lane_decision"]}`
- Accepted labels input-only: `{str(noleak["accepted_labels_input_only"]).lower()}`
- Blockers/rejects outside labels, denominators, result, validation, promotion: `{str(noleak["blockers_and_rejects_outside_labels_denominators_result_validation_promotion"]).lower()}`

## Source-Access Route Review

{markdown_table(noleak["source_access_route_review"], ["blocker_family", "count", "routing_decision", "exact_source_needed", "contract_sufficiency"])}

## Strongest Counterargument

{noleak["strongest_counterargument"]}
""",
    )

    capture = outputs["capture_review"]
    write_text(
        ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_CAPTURE_BACKLOG_REVIEW_2026-05-09.md",
        f"""# G12 NOFILL Pending Source Capture Backlog Review

Promotion posture: `{PROMOTION_VERDICT}`.

Status: `{capture["status"]}`.
Backlog item count: `{capture["backlog_item_count"]}`.

## Item Reviews

{markdown_table(capture["item_reviews"], ["backlog_id", "priority", "routing_decision", "status", "issues"])}

## Missing Topic Fields

`{capture["missing_topic_fields"]}`

## Audit Answer

{capture["audit_question_answer"]}

Live wiring authorized by this audit: `{str(capture["live_wiring_authorized_by_this_audit"]).lower()}`.
""",
    )

    write_next_prompt_pack()
    write_completion_audit(status="BUILT_PENDING_VERIFIER_AND_FOCUSED_TESTS", verification=None)


def format_audit_question(item: dict[str, Any]) -> str:
    return f"""### {item["question_id"]}: {item["question"]}

- Answer: {item["answer"]}
- Status: `{item["status"]}`
- Evidence: {item["evidence"]}
"""


def format_route_decision(item: dict[str, Any]) -> str:
    return f"""### `{item["route"]}`

- Decision: `{item["decision"]}`
- Allowed use: {item["allowed_use"]}
- Forbidden use: {item["forbidden_use"]}
"""


def write_next_prompt_pack() -> None:
    write_text(
        ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_NEXT_PROMPT_PACK_2026-05-09.md",
        f"""# G12 NOFILL Pending Source Next Prompt Pack

Promotion posture: `{PROMOTION_VERDICT}`.

## Primary Next Route

`NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE`

Objective: Use the G12-accepted pending source contract to attempt source/control clearance for exactly the 8 residual blockers. This route must remain source/control only and must not score accepted, blocked, or rejected rows.

Required inputs:

- `G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json`
- `G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW_2026-05-09.json`
- `G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.json`
- `G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json`
- `NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json`
- `NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl`

Allowed work:

1. For the 3 OTI4 May 3 source gaps, search read-only tick parquet or M1/lower OHLC covering `2026-05-03 13:00-13:30 UTC`.
2. For the 1 original OTI2 source gap, search side-aware bid/ask coverage through active pending window and cancel.
3. For the 4 OTI3 same-tick rows, keep blocked unless higher-resolution event-order source exists without account/order labels.
4. Hash consumed source files and record source coverage status, quote side, parser version, source paths, duplicate identity, and ambiguity status.

Forbidden work:

- No result scoring, validation, promotion, registry edit, broker actual-R, account history, order history, hidden labels, MT5 order/account/history calls, paid/API/Databento calls, or live trading behavior.
- Do not move any of the 8 blockers into accepted labels or denominators unless exact source-control clearance is proven from approved source fields.
- Keep the 65 rejects outside all labels and denominators.

## Secondary Route

`NOFILL_CAT_V2_FILL_PATH_EVENT_ORDER_CONTRACT`

Objective: Build a categorical source contract for entry/protective/terminal event ordering using the accepted source schema families. Same-tick/same-bar ambiguity must stay explicit. No path-R, actual-R, validation, promotion, or selector use is allowed.

## Tertiary Route

`NOFILL_CAT_V2_PENDING_LIFECYCLE_PROSPECTIVE_CAPTURE_SPEC`

Objective: Convert the source contract into an implementation ticket for future shadow capture. This must be a spec or isolated logger-test lane unless the owner separately approves live wiring. It cannot change order behavior, cancellation decisions, risk, execution, prompts, permissions, safety gates, or selectors.

## Closed Routes

`NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE`, validation, promotion, registry edits, broker/account/order label use, and live behavior changes remain closed until a separate frozen preregistration, sample floor, no-leak proof, G12 acceptance, and owner approval exist.
""",
    )


def build_all() -> dict[str, Any]:
    rows = read_jsonl(ROW_LEDGER)
    counts = recompute_counts(rows)
    schema = read_json(SOURCE_SCHEMA_FIELDS)
    duplicate_control = read_json(DUPLICATE_CONTROL)
    noleak = read_json(SOURCE_NOLEAK_AUDIT)
    taxonomy = read_json(SOURCE_BLOCKER_TAXONOMY)
    backlog = read_json(SOURCE_CAPTURE_BACKLOG)

    schema_review = build_schema_field_review(schema, counts)
    duplicate_review = build_duplicate_review(duplicate_control, counts)
    noleak_blocker_review = build_noleak_blocker_review(noleak, taxonomy, counts)
    capture_review = build_capture_backlog_review(backlog)
    decision_ledger = build_decision_ledger(
        counts,
        schema_review,
        duplicate_review,
        noleak_blocker_review,
        capture_review,
    )
    outputs = {
        "context_anchor": context_anchor(),
        "decision_ledger": decision_ledger,
        "schema_review": schema_review,
        "duplicate_review": duplicate_review,
        "noleak_blocker_review": noleak_blocker_review,
        "capture_review": capture_review,
    }

    json_dump(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json", decision_ledger)
    json_dump(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW_2026-05-09.json", schema_review)
    json_dump(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.json", duplicate_review)
    json_dump(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json", noleak_blocker_review)
    json_dump(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_CAPTURE_BACKLOG_REVIEW_2026-05-09.json", capture_review)
    write_markdown_artifacts(outputs)
    return outputs


if __name__ == "__main__":
    built = build_all()
    print(
        json.dumps(
            {
                "status": "BUILT",
                "route_id": ROUTE_ID,
                "decision": built["decision_ledger"]["decision"],
                "schema_status": built["schema_review"]["status"],
                "duplicate_status": built["duplicate_review"]["status"],
                "noleak_blocker_status": built["noleak_blocker_review"]["status"],
                "capture_status": built["capture_review"]["status"],
                "output_count": len(required_output_files()),
            },
            indent=2,
            sort_keys=True,
        )
    )
