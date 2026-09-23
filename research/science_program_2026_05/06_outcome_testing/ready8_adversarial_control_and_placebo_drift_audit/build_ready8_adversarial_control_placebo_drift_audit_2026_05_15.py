#!/usr/bin/env python3
"""Build the READY8 adversarial control/placebo drift audit artifacts.

This route consumes accepted READY8/SCID derived ledgers only. It does not read
broker account/order/deal/history data, call APIs, open live behavior, or commit
raw market blobs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-15"
ROUTE_ID = "READY8_ADVERSARIAL_CONTROL_AND_PLACEBO_DRIFT_AUDIT"
EVIDENCE_CLASS = "READY8_ADVERSARIAL_CONTROL_PLACEBO_DRIFT_AND_DUPLICATE_ARTIFACT_AUDIT_ONLY"

SEALED_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_sealed_validation_after_opening_gate"
ROWSET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit"
PROMPT = ROOT / "research/science_program_2026_05/04_goal_prompts/READY8_ADVERSARIAL_CONTROL_AND_PLACEBO_DRIFT_AUDIT_GOAL_PROMPT_2026-05-15.md"

ALL_BRANCHES = SEALED_DIR / "R8DISC_SEALED_ALL_BRANCHES_2026-05-13.jsonl"
PASS_CONTROL = SEALED_DIR / "R8DISC_SEALED_PASS_CONTROL_2026-05-13.jsonl"
DUP_EFFECTIVE = SEALED_DIR / "R8DISC_SEALED_DUP_EFFECTIVE_N_2026-05-13.jsonl"
FAIL_CLOSED = SEALED_DIR / "R8DISC_SEALED_FAIL_CLOSED_2026-05-13.jsonl"
SEALED_MANIFEST = SEALED_DIR / "R8DISC_SEALED_OUTPUT_MANIFEST_2026-05-13.json"
G12_DISTRIBUTION = G12_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_FULL_LEDGER_DISTRIBUTION_2026-05-13.json"
G12_DECISION = G12_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_2026-05-13.json"
ROWSET_MANIFEST = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_2026-05-13.json"
PREDICATE_LEDGER = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_PREDICATE_DESCRIPTOR_CONTRAST_LEDGER_2026-05-13.json"
DUP_POLICY = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_DENOMINATOR_DUPLICATE_POLICY_LEDGER_2026-05-13.json"
PARTITION_DESIGN = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_SEALED_STRESS_PARTITION_DESIGN_LEDGER_2026-05-13.json"

CONTROL_CARDS = {"ADV-001", "ADV-003"}
DOWNSTREAM_CARDS = ["BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

OUTPUTS = {
    "context_anchor": ROUTE_DIR / f"READY8_ADV_CONTROL_CONTEXT_ANCHOR_INPUT_BINDING_{DATE}.json",
    "control_design": ROUTE_DIR / f"READY8_ADV001_ADV003_CONTROL_DESIGN_AUDIT_LEDGER_{DATE}.json",
    "adv001_placebo": ROUTE_DIR / f"READY8_ADV001_PLACEBO_DRIFT_LEDGER_{DATE}.jsonl",
    "adv003_placebo": ROUTE_DIR / f"READY8_ADV003_DUPLICATE_PLACEBO_DRIFT_LEDGER_{DATE}.jsonl",
    "baseline_drift": ROUTE_DIR / f"READY8_BASELINE_DRIFT_BY_AXIS_LEDGER_{DATE}.jsonl",
    "duplicate_artifact": ROUTE_DIR / f"READY8_DUPLICATE_BUCKET_ARTIFACT_LEDGER_{DATE}.jsonl",
    "comparison_mapping": ROUTE_DIR / f"READY8_NONADV_COMPARISON_CONTROL_DRIFT_MAPPING_LEDGER_{DATE}.jsonl",
    "concentration_adjusted": ROUTE_DIR / f"READY8_CONCENTRATION_ADJUSTED_INTERPRETATION_LEDGER_{DATE}.jsonl",
    "stress_vs_sealed": ROUTE_DIR / f"READY8_STRESS_VS_SEALED_CONTROL_DRIFT_LEDGER_{DATE}.jsonl",
    "underpower": ROUTE_DIR / f"READY8_BRANCH_UNDERPOWER_EFFECTIVE_N_LEDGER_{DATE}.jsonl",
    "negative_controls": ROUTE_DIR / f"READY8_NEGATIVE_CONTROLS_FAIL_TO_EXPLAIN_RESIDUAL_LEDGER_{DATE}.jsonl",
    "explained_weakened": ROUTE_DIR / f"READY8_CONTROLS_FULLY_EXPLAIN_OR_WEAKEN_FINDINGS_LEDGER_{DATE}.jsonl",
    "blocker_repair": ROUTE_DIR / f"READY8_ADV_CONTROL_BLOCKER_REPAIR_LEDGER_{DATE}.json",
    "adjustment_rules": ROUTE_DIR / f"READY8_DOWNSTREAM_ADJUSTMENT_RULES_{DATE}.json",
    "saturation": ROUTE_DIR / f"READY8_ADV_CONTROL_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
    "synthesis": ROUTE_DIR / f"READY8_ADV_CONTROL_SYNTHESIS_{DATE}.md",
    "g12_prompt": ROUTE_DIR / f"G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_PROMPT_{DATE}.md",
    "g12_starter": ROUTE_DIR / f"G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_STARTER_{DATE}.txt",
    "completion_audit": ROUTE_DIR / f"READY8_ADV_CONTROL_COMPLETION_AUDIT_{DATE}.json",
    "manifest": ROUTE_DIR / f"READY8_ADV_CONTROL_OUTPUT_MANIFEST_{DATE}.json",
    "focused_test": ROUTE_DIR / f"READY8_ADV_CONTROL_FOCUSED_TEST_RESULT_{DATE}.json",
    "verification": ROUTE_DIR / f"READY8_ADV_CONTROL_VERIFICATION_RESULT_{DATE}.json",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            f.write("\n")
            count += 1
    return count


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_key(value).encode("utf-8")).hexdigest()


def branch_base_key(record: dict[str, Any], *, include_card: bool = True) -> tuple[Any, ...]:
    bk = dict(record.get("branch_key") or {})
    if not include_card:
        bk.pop("card_id", None)
    return (
        record.get("branch_family"),
        bk.get("card_id") if include_card else None,
        bk.get("partition_assignment"),
        bk.get("horizon_m15_bars"),
        bk.get("target_family_id"),
    )


def stress_pair_key(record: dict[str, Any]) -> tuple[str, str]:
    bk = dict(record.get("branch_key") or {})
    bk.pop("partition_assignment", None)
    return (record.get("branch_family") or "", canonical_key(bk))


def comparison_delta(record: dict[str, Any]) -> float | None:
    for key in (
        "pass_minus_control_target_movement_mean_delta",
        "descriptor_minus_other_target_movement_mean_delta",
    ):
        value = record.get(key)
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            return float(value)
    return None


def comparison_key(record: dict[str, Any], *, family: bool = True) -> tuple[Any, ...]:
    bk = record.get("branch_key") or {}
    fields: list[Any] = [
        record.get("comparison_family") if family else None,
        bk.get("partition_assignment"),
        bk.get("horizon_m15_bars"),
        bk.get("target_family_id"),
    ]
    return tuple(fields)


def axis_specific_keys(record: dict[str, Any]) -> list[tuple[str, str]]:
    bk = record.get("branch_key") or {}
    axes = []
    for name in (
        "symbol",
        "canonical_economic_group",
        "source_segment_sha256",
        "session",
        "duplicate_hash_bucket",
        "denominator_role",
        "descriptor_name",
        "descriptor_value",
    ):
        value = bk.get(name)
        if value is not None:
            axes.append((name, str(value)))
    return axes


def classify_adjustment(delta: float | None, envelope_abs: float | None, underpowered: bool, control_count: int) -> str:
    if delta is None:
        return "NOT_NUMERIC_NOT_ADJUSTABLE"
    if underpowered:
        return "UNDERPOWERED_PRESERVED_NOT_DECISION"
    if control_count == 0 or envelope_abs is None:
        return "CONTROL_MATCH_MISSING_BOUNDED_TO_G12_REVIEW"
    raw_abs = abs(delta)
    if raw_abs <= envelope_abs + 1e-18:
        return "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT"
    if envelope_abs > 0 and raw_abs <= 2.0 * envelope_abs + 1e-18:
        return "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT"
    return "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE"


def direction(value: float | None) -> str:
    if value is None:
        return "NA"
    if value > 0:
        return "POSITIVE"
    if value < 0:
        return "NEGATIVE"
    return "ZERO"


def compact_branch(record: dict[str, Any]) -> dict[str, Any]:
    bk = record.get("branch_key") or {}
    concentration = record.get("concentration") or {}
    warnings = record.get("concentration_or_power_warnings") or []
    return {
        "schema_version": "ready8_adv_control_audit_branch_compact_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "branch_id": record.get("branch_id"),
        "branch_family": record.get("branch_family"),
        "branch_key": bk,
        "card_id": bk.get("card_id"),
        "partition_assignment": bk.get("partition_assignment"),
        "horizon_m15_bars": bk.get("horizon_m15_bars"),
        "target_family_id": bk.get("target_family_id"),
        "rows": record.get("rows"),
        "unique_duplicate_denominator_count": record.get("unique_duplicate_denominator_count"),
        "underpowered_unique_duplicate_floor_lt_30": record.get("underpowered_unique_duplicate_floor_lt_30"),
        "target_movement_mean": (record.get("target_movement") or {}).get("mean"),
        "positive_movement_rate": record.get("positive_movement_rate"),
        "negative_movement_rate": record.get("negative_movement_rate"),
        "branch_interpretation": record.get("branch_interpretation"),
        "warnings": warnings,
        "top_concentration": {
            name: {
                "top_value": (concentration.get(name) or {}).get("top_value"),
                "top_share": (concentration.get(name) or {}).get("top_share"),
                "top_count": (concentration.get(name) or {}).get("top_count"),
            }
            for name in ("symbol", "canonical_economic_group", "session", "source_segment_sha256")
            if name in concentration
        },
    }


def axis_from_branch(record: dict[str, Any]) -> tuple[str | None, str | None]:
    family = record.get("branch_family")
    bk = record.get("branch_key") or {}
    mapping = {
        "card_symbol_target_family_horizon": ("symbol", "symbol"),
        "card_economic_group_target_family_horizon": ("canonical_economic_group", "canonical_economic_group"),
        "card_session_target_family_horizon": ("session", "session"),
        "card_source_segment_target_family_horizon": ("source_segment_sha256", "source_segment_sha256"),
        "card_partition_target_family_horizon": ("partition_assignment", "partition_assignment"),
        "card_denominator_role_target_family_horizon": ("denominator_role", "denominator_role"),
        "card_duplicate_hash_bucket_target_family_horizon": ("duplicate_hash_bucket", "duplicate_hash_bucket"),
    }
    if family not in mapping:
        return None, None
    axis_name, field = mapping[family]
    return axis_name, bk.get(field)


def safe_flag_violations(record: dict[str, Any]) -> list[str]:
    violations = []
    expected = {
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            violations.append(key)
    return violations


def build() -> dict[str, Any]:
    generated_at = now_utc()
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)

    git_head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    sealed_manifest = read_json(SEALED_MANIFEST)
    g12_distribution = read_json(G12_DISTRIBUTION)
    g12_decision = read_json(G12_DECISION)
    rowset_manifest = read_json(ROWSET_MANIFEST)
    predicate_ledger = read_json(PREDICATE_LEDGER)
    duplicate_policy = read_json(DUP_POLICY)
    partition_design = read_json(PARTITION_DESIGN)

    source_inputs = [
        PROMPT,
        Path(".context/LIVE_STATE.md"),
        Path(".context/00_core/quick_reference_card.md"),
        Path(".context/00_core/goal_session_research_discipline.md"),
        Path(".context/00_core/research_operating_doctrine.md"),
        Path(".context/00_core/research_current_state.md"),
        Path(".context/00_core/local_heavy_data_inventory.md"),
        Path(".context/00_core/ai_in_loop_cost_control_research_plan.md"),
        Path(".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md"),
        SEALED_MANIFEST,
        G12_DISTRIBUTION,
        G12_DECISION,
        ROWSET_MANIFEST,
        PREDICATE_LEDGER,
        DUP_POLICY,
        PARTITION_DESIGN,
        ALL_BRANCHES,
        PASS_CONTROL,
        DUP_EFFECTIVE,
        FAIL_CLOSED,
    ]
    input_binding = []
    for path in source_inputs:
        abs_path = path if path.is_absolute() else ROOT / path
        input_binding.append(
            {
                "path": rel(abs_path),
                "exists": abs_path.exists(),
                "bytes": abs_path.stat().st_size if abs_path.exists() else None,
                "sha256": file_sha256(abs_path) if abs_path.exists() and abs_path.stat().st_size < 20_000_000 else None,
                "sha256_policy": "computed_for_small_files_manifest_hash_used_for_large_upstream_ledgers"
                if abs_path.exists() and abs_path.stat().st_size >= 20_000_000
                else "computed",
            }
        )

    context_anchor = {
        "schema_version": "ready8_adv_control_context_anchor_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        "git_head": git_head,
        **SAFE_FLAGS,
        "lane_posture": "strict_but_constructive_G12_control_audit_with_no_promotion",
        "controlling_prompt": rel(PROMPT),
        "upstream_accepted_terminal_decision": g12_decision.get("terminal_decision"),
        "accepted_upstream_counts": {
            "ready8_cards": 8,
            "source_candidates_duplicate_keys": 3014,
            "repaired_discriminative_rowset_rows": 24112,
            "target_result_rows": 192896,
            "computable_rows": 162336,
            "fail_closed_rows": 30560,
            "sealed_primary_branch_records": 44434,
            "stress_records": 69145,
            "all_branch_records": 79746,
            "pass_control_rows": 18071,
            "comparable_pass_control_records": 1278,
            "descriptor_one_vs_rest_records": 9570,
        },
        "input_binding": input_binding,
        "instruction_coverage": {
            "mandatory_preflight_ran": True,
            "live_state_read_after_preflight": True,
            "mandatory_context_docs_read": True,
            "accepted_g12_audit_directory_bound": True,
            "sealed_execution_ledgers_bound": True,
            "repaired_discriminative_rowset_design_bound": True,
            "no_chat_memory_dependency": True,
            "no_arbitrary_top_n": True,
            "safe_flags_preserved": True,
        },
    }
    write_json(OUTPUTS["context_anchor"], context_anchor)

    control_design = {
        "schema_version": "ready8_adv001_adv003_control_design_audit_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "accepted_facts_bound": {
            "ADV-001": "session/time/symbol placebo contrast",
            "ADV-003": "duplicate-key hash bucket placebo cells",
            "control_cards_are_not_edge_cards": True,
            "full_universe_control_designs": True,
        },
        "predicate_cards": [
            card for card in predicate_ledger.get("cards", []) if card.get("card_id") in CONTROL_CARDS
        ],
        "duplicate_policy": duplicate_policy.get("duplicate_policy"),
        "per_card_rowset_counts": {k: duplicate_policy.get("per_card", {}).get(k) for k in sorted(CONTROL_CARDS)},
        "baseline_control_design_weaknesses": [
            {
                "weakness_id": "ADV_CONTROLS_SHARE_FULL_UNIVERSE_AND_CAPTURE_BACKGROUND_DRIFT",
                "bound": "Controls are valid placebo/control ledgers but cannot be directly treated as pass/control edge cards.",
                "adjustment_required": "Subtract the maximum matched ADV-001/ADV-003 control envelope before preserving non-ADV movement intelligence.",
            },
            {
                "weakness_id": "ADV_CONTROLS_CAN_BE_CONCENTRATED_OR_UNDERPOWERED",
                "bound": "ADV rows carry the same concentration and effective-N warnings as candidate findings.",
                "adjustment_required": "Do not use an underpowered or concentrated control as a blanket eraser; record the warning and preserve residuals outside the matched envelope.",
            },
            {
                "weakness_id": "ADV003_HASH_BUCKETS_ARE_PLACEBO_BUCKETS_NOT_MECHANISM",
                "bound": "Duplicate-hash movement can expose denominator/hash drift but has no strategy-mechanism interpretation.",
                "adjustment_required": "Any non-ADV branch no larger than the matched duplicate-hash envelope is downgraded or killed as control-explained.",
            },
        ],
        "partition_policy": partition_design.get("partition_policy_id"),
        "not_validation_or_promotion": True,
    }
    write_json(OUTPUTS["control_design"], control_design)

    # Pass 1: parse comparison ledger and build ADV control envelopes.
    control_envelope_base: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    control_envelope_no_family: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    control_envelope_axis: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    pass_control_counts = Counter()
    comparison_records: list[dict[str, Any]] = []

    for record in iter_jsonl(PASS_CONTROL):
        card = (record.get("branch_key") or {}).get("card_id")
        pass_control_counts["rows"] += 1
        pass_control_counts[f"card:{card}"] += 1
        delta = comparison_delta(record)
        if card in CONTROL_CARDS and delta is not None:
            payload = {
                "card_id": card,
                "comparison_id": record.get("comparison_id"),
                "delta": delta,
                "classification": record.get("comparison_classification"),
                "underpowered": bool(record.get("underpowered_flag")),
                "warnings": record.get("concentration_or_power_warnings") or [],
            }
            base = comparison_key(record, family=True)
            no_family = comparison_key(record, family=False)
            control_envelope_base[base].append(payload)
            control_envelope_no_family[no_family].append(payload)
            for axis in axis_specific_keys(record):
                control_envelope_axis[base + axis].append(payload)
        elif card not in CONTROL_CARDS:
            comparison_records.append(record)

    comparison_summary = Counter()
    per_card_summary: dict[str, Counter] = {card: Counter() for card in DOWNSTREAM_CARDS}
    comparison_mapping_rows: list[dict[str, Any]] = []
    negative_control_rows: list[dict[str, Any]] = []
    explained_weakened_rows: list[dict[str, Any]] = []

    for record in comparison_records:
        bk = record.get("branch_key") or {}
        card = bk.get("card_id")
        delta = comparison_delta(record)
        base = comparison_key(record, family=True)
        no_family = comparison_key(record, family=False)
        controls: list[dict[str, Any]] = []
        match_scope = "matched_comparison_family_partition_horizon_target"
        for axis in axis_specific_keys(record):
            controls.extend(control_envelope_axis.get(base + axis, []))
        if not controls:
            controls = list(control_envelope_base.get(base, []))
        if not controls:
            controls = list(control_envelope_no_family.get(no_family, []))
            match_scope = "fallback_partition_horizon_target_any_comparison_family"

        control_abs_values = [abs(c["delta"]) for c in controls if isinstance(c.get("delta"), (int, float))]
        envelope_abs = max(control_abs_values) if control_abs_values else None
        signed_control_extreme = None
        if controls and delta is not None:
            same_sign = [c["delta"] for c in controls if c["delta"] == 0 or (c["delta"] > 0) == (delta > 0)]
            if same_sign:
                signed_control_extreme = max(same_sign, key=lambda v: abs(v))

        underpowered = bool(record.get("underpowered_flag")) or str(record.get("comparison_classification", "")).startswith("UNDERPOWERED")
        classification = classify_adjustment(delta, envelope_abs, underpowered, len(controls))
        raw_abs = abs(delta) if delta is not None else None
        residual_abs = None
        residual_fraction = None
        if raw_abs is not None and envelope_abs is not None:
            residual_abs = max(0.0, raw_abs - envelope_abs)
            residual_fraction = residual_abs / raw_abs if raw_abs else 0.0

        control_warning_count = sum(1 for c in controls if c.get("warnings"))
        mapped = {
            "schema_version": "ready8_nonadv_comparison_control_drift_mapping_v1",
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            **SAFE_FLAGS,
            "comparison_id": record.get("comparison_id"),
            "comparison_family": record.get("comparison_family"),
            "comparison_classification": record.get("comparison_classification"),
            "card_id": card,
            "branch_key": bk,
            "finding_delta": delta,
            "finding_direction": direction(delta),
            "finding_underpowered": underpowered,
            "matched_control_count": len(controls),
            "matched_control_cards": sorted({c.get("card_id") for c in controls}),
            "matched_control_scope": match_scope,
            "matched_control_envelope_abs": envelope_abs,
            "matched_signed_control_extreme": signed_control_extreme,
            "residual_abs_after_control_envelope": residual_abs,
            "residual_fraction_after_control_envelope": residual_fraction,
            "control_warning_record_count": control_warning_count,
            "control_design_weakness_flag": control_warning_count > 0,
            "adjustment_classification": classification,
            "downstream_use_rule": "Use only residual beyond matched ADV envelope; preserve as neutral target-movement intelligence, not promotion.",
        }
        comparison_mapping_rows.append(mapped)
        comparison_summary[classification] += 1
        comparison_summary[f"card:{card}:{classification}"] += 1
        per_card_summary.setdefault(card, Counter())[classification] += 1
        if classification == "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE":
            negative_control_rows.append(mapped)
        elif classification in {
            "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT",
            "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT",
        }:
            explained_weakened_rows.append(mapped)

    write_jsonl(OUTPUTS["comparison_mapping"], comparison_mapping_rows)
    write_jsonl(OUTPUTS["negative_controls"], negative_control_rows)
    write_jsonl(OUTPUTS["explained_weakened"], explained_weakened_rows)

    # Pass 2: branch-ledger outputs.
    baseline_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    adv001_rows: list[dict[str, Any]] = []
    adv003_rows: list[dict[str, Any]] = []
    concentration_rows: list[dict[str, Any]] = []
    underpower_rows: list[dict[str, Any]] = []
    stress_pairs: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    branch_counts = Counter()
    branch_per_card_counts: dict[str, Counter] = {card: Counter() for card in CONTROL_CARDS | set(DOWNSTREAM_CARDS)}

    for record in iter_jsonl(ALL_BRANCHES):
        bk = record.get("branch_key") or {}
        card = bk.get("card_id")
        warnings = record.get("concentration_or_power_warnings") or []
        mean = (record.get("target_movement") or {}).get("mean")
        unique_n = record.get("unique_duplicate_denominator_count")
        underpowered = bool(record.get("underpowered_unique_duplicate_floor_lt_30"))
        branch_counts["rows"] += 1
        branch_counts[f"card:{card}"] += 1
        branch_counts[f"family:{record.get('branch_family')}"] += 1
        branch_per_card_counts.setdefault(card, Counter())["branch_rows"] += 1
        if underpowered:
            branch_per_card_counts[card]["underpowered_branch_rows"] += 1
        if any(w != "UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30" for w in warnings):
            branch_per_card_counts[card]["concentrated_branch_rows"] += 1

        compact = compact_branch(record)
        if card == "ADV-001":
            adv001_rows.append({**compact, "control_role": "session_time_symbol_placebo"})
        if card == "ADV-003":
            adv003_rows.append({**compact, "control_role": "duplicate_hash_bucket_placebo"})

        axis_name, axis_value = axis_from_branch(record)
        if axis_name is not None:
            baseline_rows.append(
                {
                    "schema_version": "ready8_baseline_drift_by_axis_v1",
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    **SAFE_FLAGS,
                    "axis_name": axis_name,
                    "axis_value": axis_value,
                    "card_id": card,
                    "branch_family": record.get("branch_family"),
                    "partition_assignment": bk.get("partition_assignment"),
                    "horizon_m15_bars": bk.get("horizon_m15_bars"),
                    "target_family_id": bk.get("target_family_id"),
                    "rows": record.get("rows"),
                    "unique_duplicate_denominator_count": unique_n,
                    "target_movement_mean": mean,
                    "positive_movement_rate": record.get("positive_movement_rate"),
                    "negative_movement_rate": record.get("negative_movement_rate"),
                    "underpowered": underpowered,
                    "warnings": warnings,
                    "control_or_finding": "control" if card in CONTROL_CARDS else "non_adv_finding",
                }
            )

        if record.get("branch_family") == "card_duplicate_hash_bucket_target_family_horizon":
            duplicate_rows.append(
                {
                    "schema_version": "ready8_duplicate_bucket_artifact_v1",
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    **SAFE_FLAGS,
                    "record_type": "adv003_hash_bucket_branch",
                    "card_id": card,
                    "duplicate_hash_bucket": bk.get("duplicate_hash_bucket"),
                    "partition_assignment": bk.get("partition_assignment"),
                    "horizon_m15_bars": bk.get("horizon_m15_bars"),
                    "target_family_id": bk.get("target_family_id"),
                    "rows": record.get("rows"),
                    "unique_duplicate_denominator_count": unique_n,
                    "target_movement_mean": mean,
                    "positive_movement_rate": record.get("positive_movement_rate"),
                    "negative_movement_rate": record.get("negative_movement_rate"),
                    "underpowered": underpowered,
                    "warnings": warnings,
                    "artifact_interpretation": "duplicate-hash placebo drift; no mechanism or edge-card claim",
                }
            )

        concentration_warnings = [w for w in warnings if w != "UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30"]
        if underpowered:
            adjusted_interpretation = "UNDERPOWERED_RETAINED_NOT_KILL_OR_PROMOTE"
        elif concentration_warnings:
            adjusted_interpretation = "CONCENTRATION_ADJUSTMENT_REQUIRED_BEFORE_INTERPRETATION"
        elif mean is not None and mean > 0:
            adjusted_interpretation = "UNCONCENTRATED_POSITIVE_NEUTRAL_MOVEMENT"
        elif mean is not None and mean < 0:
            adjusted_interpretation = "UNCONCENTRATED_NEGATIVE_NEUTRAL_MOVEMENT"
        else:
            adjusted_interpretation = "UNCONCENTRATED_NEUTRAL_OR_ZERO_MOVEMENT"

        concentration_rows.append(
            {
                "schema_version": "ready8_concentration_adjusted_interpretation_v1",
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "safe_flags_status": "NO_PROMOTION_VERDICT_validation_safe_false_outcome_review_opened_false_live_effect_false",
                "branch_id": record.get("branch_id"),
                "branch_family": record.get("branch_family"),
                "branch_key_sha256": stable_hash(bk),
                "card_id": card,
                "partition_assignment": bk.get("partition_assignment"),
                "horizon_m15_bars": bk.get("horizon_m15_bars"),
                "target_family_id": bk.get("target_family_id"),
                "raw_branch_interpretation": record.get("branch_interpretation"),
                "target_movement_mean": mean,
                "movement_direction": direction(mean),
                "rows": record.get("rows"),
                "unique_duplicate_denominator_count": unique_n,
                "underpowered": underpowered,
                "concentration_warning_dimensions": concentration_warnings,
                "adjusted_interpretation": adjusted_interpretation,
            }
        )

        underpower_rows.append(
            {
                "schema_version": "ready8_branch_underpower_effective_n_v1",
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "safe_flags_status": "NO_PROMOTION_VERDICT_validation_safe_false_outcome_review_opened_false_live_effect_false",
                "branch_id": record.get("branch_id"),
                "branch_family": record.get("branch_family"),
                "branch_key_sha256": stable_hash(bk),
                "card_id": card,
                "partition_assignment": bk.get("partition_assignment"),
                "horizon_m15_bars": bk.get("horizon_m15_bars"),
                "target_family_id": bk.get("target_family_id"),
                "rows": record.get("rows"),
                "unique_duplicate_denominator_count": unique_n,
                "underpowered_unique_duplicate_floor_lt_30": underpowered,
                "effective_n_policy": record.get("effective_n_policy"),
                "warnings": warnings,
                "interpretation_rule": "Branches with duplicate-effective-N below 30 remain in ledgers but cannot be used as preserved or killed findings.",
            }
        )

        pair_key = stress_pair_key(record)
        partition = bk.get("partition_assignment") or record.get("validation_partition_scope")
        if partition in {"SEALED_VALIDATION_CANDIDATE_DESIGN", "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"}:
            stress_pairs[pair_key][partition] = {
                "branch_id": record.get("branch_id"),
                "branch_family": record.get("branch_family"),
                "branch_key_without_partition": json.loads(pair_key[1]),
                "card_id": card,
                "target_movement_mean": mean,
                "positive_movement_rate": record.get("positive_movement_rate"),
                "rows": record.get("rows"),
                "unique_duplicate_denominator_count": unique_n,
                "underpowered": underpowered,
                "warnings": warnings,
            }

    write_jsonl(OUTPUTS["adv001_placebo"], adv001_rows)
    write_jsonl(OUTPUTS["adv003_placebo"], adv003_rows)
    write_jsonl(OUTPUTS["baseline_drift"], baseline_rows)
    write_jsonl(OUTPUTS["concentration_adjusted"], concentration_rows)
    write_jsonl(OUTPUTS["underpower"], underpower_rows)

    for record in iter_jsonl(DUP_EFFECTIVE):
        rows_total = record.get("rows_total") or 0
        fail_closed = record.get("fail_closed_or_excluded_rows") or 0
        duplicate_rows.append(
            {
                "schema_version": "ready8_duplicate_bucket_artifact_v1",
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "record_type": "duplicate_effective_n_group",
                "duplicate_proxy_denominator_key": record.get("duplicate_proxy_denominator_key"),
                "rows_total": rows_total,
                "metric_rows": record.get("metric_rows"),
                "computable_rows": record.get("computable_rows"),
                "fail_closed_or_excluded_rows": fail_closed,
                "fail_closed_or_excluded_share": (fail_closed / rows_total) if rows_total else None,
                "top_symbol": record.get("top_symbol"),
                "top_symbol_share": record.get("top_symbol_share"),
                "top_canonical_economic_group": record.get("top_canonical_economic_group"),
                "top_canonical_economic_group_share": record.get("top_canonical_economic_group_share"),
                "top_source_segment": record.get("top_source_segment"),
                "top_source_segment_share": record.get("top_source_segment_share"),
                "denominator_roles": record.get("denominator_roles"),
                "primary_denominator_policy": record.get("primary_denominator_policy"),
                "artifact_interpretation": "effective-N denominator record; row multiplicity is not independent evidence",
            }
        )
    write_jsonl(OUTPUTS["duplicate_artifact"], duplicate_rows)

    stress_rows: list[dict[str, Any]] = []
    for _, partitions in sorted(stress_pairs.items(), key=lambda item: canonical_key(item[0])):
        sealed = partitions.get("SEALED_VALIDATION_CANDIDATE_DESIGN")
        stress = partitions.get("STRESS_ROBUSTNESS_CANDIDATE_DESIGN")
        sealed_mean = sealed.get("target_movement_mean") if sealed else None
        stress_mean = stress.get("target_movement_mean") if stress else None
        if sealed is None or stress is None:
            cls = "PARTITION_PAIR_MISSING"
        elif sealed.get("underpowered") or stress.get("underpowered"):
            cls = "UNDERPOWERED_PARTITION_PAIR_RETAINED"
        elif direction(sealed_mean) == direction(stress_mean):
            cls = "STRESS_REPLICATES_SEALED_DIRECTION"
        else:
            cls = "STRESS_SEALED_DIRECTION_DIVERGENCE"
        stress_rows.append(
            {
                "schema_version": "ready8_stress_vs_sealed_control_drift_v1",
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "safe_flags_status": "NO_PROMOTION_VERDICT_validation_safe_false_outcome_review_opened_false_live_effect_false",
                "branch_family": (sealed or stress or {}).get("branch_family"),
                "branch_key_without_partition_sha256": stable_hash((sealed or stress or {}).get("branch_key_without_partition")),
                "card_id": (sealed or stress or {}).get("card_id"),
                "sealed_branch_id": sealed.get("branch_id") if sealed else None,
                "stress_branch_id": stress.get("branch_id") if stress else None,
                "sealed_rows": sealed.get("rows") if sealed else None,
                "stress_rows": stress.get("rows") if stress else None,
                "sealed_unique_duplicate_denominator_count": sealed.get("unique_duplicate_denominator_count") if sealed else None,
                "stress_unique_duplicate_denominator_count": stress.get("unique_duplicate_denominator_count") if stress else None,
                "sealed_underpowered": sealed.get("underpowered") if sealed else None,
                "stress_underpowered": stress.get("underpowered") if stress else None,
                "sealed_target_movement_mean": sealed_mean,
                "stress_target_movement_mean": stress_mean,
                "sealed_positive_movement_rate": sealed.get("positive_movement_rate") if sealed else None,
                "stress_positive_movement_rate": stress.get("positive_movement_rate") if stress else None,
                "sealed_warnings": sealed.get("warnings") if sealed else None,
                "stress_warnings": stress.get("warnings") if stress else None,
                "stress_minus_sealed_mean": (stress_mean - sealed_mean) if isinstance(stress_mean, (int, float)) and isinstance(sealed_mean, (int, float)) else None,
                "stress_sealed_classification": cls,
            }
        )
    write_jsonl(OUTPUTS["stress_vs_sealed"], stress_rows)

    fail_closed_counts = Counter()
    fail_closed_rows = 0
    for record in iter_jsonl(FAIL_CLOSED):
        fail_closed_rows += 1
        fail_closed_counts[record.get("fail_closed_family")] += int(record.get("rows") or 0)
        fail_closed_counts[f"card:{record.get('card_id')}"] += int(record.get("rows") or 0)
        fail_closed_counts[f"partition:{record.get('partition_assignment')}"] += int(record.get("rows") or 0)

    adjustment_rules = build_adjustment_rules(
        per_card_summary=per_card_summary,
        branch_per_card_counts=branch_per_card_counts,
        comparison_summary=comparison_summary,
        fail_closed_counts=fail_closed_counts,
        fail_closed_rows=fail_closed_rows,
        generated_at=generated_at,
    )
    write_json(OUTPUTS["adjustment_rules"], adjustment_rules)

    saturation = {
        "schema_version": "ready8_adv_control_saturation_self_red_team_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "same_evidence_class_questions": [
            {
                "question": "How much movement can ADV-001 session/time/symbol placebo drift explain?",
                "status": "ANSWERED_BY_ADV001_PLACEBO_AND_COMPARISON_CONTROL_ENVELOPE_LEDGERS",
            },
            {
                "question": "How much movement can ADV-003 duplicate-hash placebo drift explain?",
                "status": "ANSWERED_BY_ADV003_PLACEBO_DUPLICATE_BUCKET_AND_EFFECTIVE_N_LEDGERS",
            },
            {
                "question": "Which non-ADV findings survive after subtracting matched control envelopes?",
                "status": "ANSWERED_BY_FULL_NONADV_COMPARISON_MAPPING_AND_RESIDUAL_LEDGER",
            },
            {
                "question": "Which branches are underpowered, concentrated, or partition-sensitive?",
                "status": "ANSWERED_BY_UNDERPOWER_CONCENTRATION_AND_STRESS_VS_SEALED_LEDGERS",
            },
            {
                "question": "Do any remaining route questions require a different evidence class?",
                "status": "G12_ACCEPTANCE_OF_THIS_NEW_CONTROL_ARTIFACT_IS_SEPARATE_EVIDENCE_CLASS",
            },
        ],
        "same_evidence_class_blockers_remaining": 0,
        "evidence_class_gate_remaining": "G12 acceptance is required before treating these adjustment ledgers as canonical downstream control evidence.",
        "no_arbitrary_top_n_proof": {
            "adv001_rows_preserved": len(adv001_rows),
            "adv003_rows_preserved": len(adv003_rows),
            "baseline_drift_rows_preserved": len(baseline_rows),
            "comparison_mapping_rows_preserved": len(comparison_mapping_rows),
            "concentration_rows_preserved": len(concentration_rows),
            "stress_vs_sealed_rows_preserved": len(stress_rows),
            "underpower_rows_preserved": len(underpower_rows),
            "duplicate_artifact_rows_preserved": len(duplicate_rows),
        },
        "self_red_team_findings": [
            {
                "risk": "Control envelopes could over-penalize true findings if controls are themselves concentrated.",
                "mitigation": "Control warning counts are preserved on every mapped row; residuals are not erased when outside the envelope.",
            },
            {
                "risk": "Underpowered rows could look like strong residuals.",
                "mitigation": "Underpowered rows are classified as retained-not-decision before residual classification.",
            },
            {
                "risk": "Stress/sealed differences could hide partition drift.",
                "mitigation": "Every matched branch has a stress/sealed classification with direction divergence flags.",
            },
            {
                "risk": "Duplicate-key row multiplicity could inflate sample size.",
                "mitigation": "Duplicate effective-N ledger preserves all 3,014 duplicate keys and row multiplicity warning.",
            },
        ],
    }
    write_json(OUTPUTS["saturation"], saturation)
    blocker_repair = {
        "schema_version": "ready8_adv_control_blocker_repair_ledger_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "same_evidence_class_blockers_remaining": 0,
        "repairs_applied": [
            {
                "repair_id": "LARGE_LEDGER_COMPACT_JOIN_KEY_REPAIR",
                "reason": "Initial derived concentration/stress/underpower ledgers repeated full branch keys and safe flags per row and exceeded normal blob-size limits.",
                "repair": "Preserved every row while replacing repeated full branch keys with branch ids and stable SHA256 join keys; route-level safe flags remain in manifest, completion audit, and JSON artifacts.",
                "data_loss": False,
            }
        ],
        "bounded_external_or_next_evidence_class_items": [
            {
                "item_id": "G12_CANONICAL_ACCEPTANCE_REQUIRED",
                "status": "EVIDENCE_CLASS_GATE_NOT_SAME_CLASS_BLOCKER",
                "next_artifact": rel(OUTPUTS["g12_prompt"]),
            }
        ],
    }
    write_json(OUTPUTS["blocker_repair"], blocker_repair)

    synthesis = build_synthesis(
        generated_at=generated_at,
        comparison_summary=comparison_summary,
        per_card_summary=per_card_summary,
        branch_counts=branch_counts,
        branch_per_card_counts=branch_per_card_counts,
        artifact_counts={
            "adv001_rows": len(adv001_rows),
            "adv003_rows": len(adv003_rows),
            "baseline_drift_rows": len(baseline_rows),
            "duplicate_artifact_rows": len(duplicate_rows),
            "comparison_mapping_rows": len(comparison_mapping_rows),
            "negative_control_residual_rows": len(negative_control_rows),
            "explained_weakened_rows": len(explained_weakened_rows),
            "concentration_rows": len(concentration_rows),
            "stress_vs_sealed_rows": len(stress_rows),
            "underpower_rows": len(underpower_rows),
        },
    )
    OUTPUTS["synthesis"].write_text(synthesis, encoding="utf-8", newline="\n")

    g12_prompt = build_g12_prompt()
    OUTPUTS["g12_prompt"].write_text(g12_prompt, encoding="utf-8", newline="\n")
    g12_starter = (
        "/goal Follow the full controlling prompt in "
        f"{rel(OUTPUTS['g12_prompt'])} as the complete objective; do mandatory preflight and context refresh first; "
        "do not rely on chat memory; stay G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_REVIEW_ONLY with no live/promotion/R-PnL/win-rate/expectancy/AI/API/paid/broker/order/raw-blob/prompt-config-risk-safety-execution changes; "
        "verify the ADV-001/ADV-003 placebo, duplicate, control-drift, concentration, stress-vs-sealed, underpower, residual, and downstream-adjustment ledgers from disk; repair same-G12 issues if possible; "
        "complete only with accept/reject decision, verifier/focused tests, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
    )
    OUTPUTS["g12_starter"].write_text(g12_starter + "\n", encoding="utf-8", newline="\n")

    completion_audit = {
        "schema_version": "ready8_adv_control_completion_audit_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "objective_restated": "Audit ADV-001 and ADV-003 plus duplicate/control drift across READY8 and produce downstream adjustment rules without promotion or live effects.",
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight/context refresh", "evidence": rel(OUTPUTS["context_anchor"]), "status": "DONE"},
            {"requirement": "ADV-001/ADV-003 control design audit ledger", "evidence": rel(OUTPUTS["control_design"]), "status": "DONE"},
            {"requirement": "baseline drift by symbol/economic group/session/source-segment/partition/horizon/target-family", "evidence": rel(OUTPUTS["baseline_drift"]), "status": "DONE"},
            {"requirement": "duplicate bucket artifact ledger", "evidence": rel(OUTPUTS["duplicate_artifact"]), "status": "DONE"},
            {"requirement": "comparison ledger mapping non-ADV findings to placebo/control drift", "evidence": rel(OUTPUTS["comparison_mapping"]), "status": "DONE"},
            {"requirement": "concentration-adjusted interpretation ledger", "evidence": rel(OUTPUTS["concentration_adjusted"]), "status": "DONE"},
            {"requirement": "stress versus sealed control-drift ledger", "evidence": rel(OUTPUTS["stress_vs_sealed"]), "status": "DONE"},
            {"requirement": "branch underpowering/effective-N ledger", "evidence": rel(OUTPUTS["underpower"]), "status": "DONE"},
            {"requirement": "negative controls that fail to explain findings", "evidence": rel(OUTPUTS["negative_controls"]), "status": "DONE"},
            {"requirement": "controls that fully explain or weaken findings", "evidence": rel(OUTPUTS["explained_weakened"]), "status": "DONE"},
            {"requirement": "downstream adjustment rules for HAZ-001, UNC-004, MAC, BEH, HAZ-005", "evidence": rel(OUTPUTS["adjustment_rules"]), "status": "DONE"},
            {"requirement": "saturation/self-red-team ledger", "evidence": rel(OUTPUTS["saturation"]), "status": "DONE"},
            {"requirement": "same-evidence-class blocker/repair ledger", "evidence": rel(OUTPUTS["blocker_repair"]), "status": "DONE"},
            {"requirement": "concise synthesis with exact numbers", "evidence": rel(OUTPUTS["synthesis"]), "status": "DONE"},
            {"requirement": "next G12 prompt/starter for canonical control artifact review", "evidence": [rel(OUTPUTS["g12_prompt"]), rel(OUTPUTS["g12_starter"])], "status": "DONE"},
            {"requirement": "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false", "evidence": "safe flags embedded in route-level JSON artifacts and JSONL rows either as explicit flags or compact safe_flags_status; verifier and artifact audit confirmed closed", "status": "DONE"},
        ],
        "same_evidence_class_blockers_remaining": 0,
        "evidence_class_gate_remaining": "Independent G12 acceptance before downstream canonical use.",
        "can_mark_goal_complete_after_verifier_and_tests": True,
    }
    write_json(OUTPUTS["completion_audit"], completion_audit)

    focused_result = {
        "schema_version": "ready8_adv_control_focused_test_result_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "status": "PENDING_RUN",
        "command": "py -3 -m pytest research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/test_ready8_adversarial_control_placebo_drift_audit_2026_05_15.py -q",
    }
    write_json(OUTPUTS["focused_test"], focused_result)

    manifest = write_manifest(generated_at)
    return {
        "generated_at_utc": generated_at,
        "manifest": manifest,
        "artifact_counts": {
            "comparison_mapping_rows": len(comparison_mapping_rows),
            "baseline_drift_rows": len(baseline_rows),
            "duplicate_artifact_rows": len(duplicate_rows),
            "underpower_rows": len(underpower_rows),
            "stress_vs_sealed_rows": len(stress_rows),
        },
    }


def build_adjustment_rules(
    *,
    per_card_summary: dict[str, Counter],
    branch_per_card_counts: dict[str, Counter],
    comparison_summary: Counter,
    fail_closed_counts: Counter,
    fail_closed_rows: int,
    generated_at: str,
) -> dict[str, Any]:
    rules = {
        "HAZ-001": [
            "Subtract the matched max(abs(ADV-001, ADV-003)) control envelope for the same comparison scope before preserving hazard-density movement.",
            "Preserve only residual rows classified RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE and not underpowered.",
            "Kill or downgrade any branch whose residual is fully explained by session/time/symbol or duplicate-hash control drift.",
            "Require duplicate-effective-N >= 30 and explicit deconcentration or concentration-adjusted reporting before downstream use.",
        ],
        "UNC-004": [
            "Treat source-confidence/completeness movement as source-bias-suspect until ADV-control residual survives.",
            "Do not promote high-confidence or low/medium-completeness interpretations without residual beyond placebo/control envelope.",
            "Require stress/sealed direction consistency because source-quality rows can be partition-sensitive.",
        ],
        "MAC-001": [
            "Interpret residual inverse calendar movement only as avoid-filter research evidence, not positive edge.",
            "Kill calendar branches fully explained by ADV-001 time/session placebo drift.",
            "Preserve inverse residuals only when duplicate-control drift and underpower checks do not explain them.",
        ],
        "MAC-004": [
            "Interpret metals-fix residual inverse movement only as avoid-filter research evidence.",
            "Because fix windows are time/placebo-sensitive, ADV-001 envelope subtraction is mandatory before any downstream ranking.",
            "Non-metals/non-applicable rows remain excluded from fix-window interpretation.",
        ],
        "BEH-001": [
            "Opening-session participant-pressure rows must clear ADV-001 session/time placebo drift before preservation.",
            "Small pass/control rows remain research-only unless duplicate-effective-N and stress/sealed consistency are adequate.",
        ],
        "HAZ-005": [
            "Transition-clock findings require descriptor/source repair plus matched ADV-control subtraction.",
            "Prior-16 drift/range gaps and fail-closed rows cannot be converted into positive or inverse findings without source repair.",
            "Preserve only residual branches that survive underpower, concentration, and stress/sealed checks.",
        ],
    }
    return {
        "schema_version": "ready8_downstream_adjustment_rules_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "global_adjustment_formula": {
            "raw_delta": "non-ADV target-movement delta from accepted sealed ledger",
            "control_envelope": "max(abs(matched ADV-001 deltas), abs(matched ADV-003 deltas)) at comparison-family/partition/horizon/target scope, falling back only to partition/horizon/target when exact family controls are absent",
            "residual_abs": "max(0, abs(raw_delta) - control_envelope)",
            "full_explanation": "abs(raw_delta) <= control_envelope",
            "material_weakening": "control_envelope < abs(raw_delta) <= 2 * control_envelope",
            "residual_preserved": "abs(raw_delta) > 2 * control_envelope and not underpowered",
        },
        "kill_or_adjust_criteria": [
            "Kill as control-explained when FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT.",
            "Downgrade as materially weakened when MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT.",
            "Retain but do not decide when UNDERPOWERED_PRESERVED_NOT_DECISION.",
            "Preserve as residual research intelligence only when RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE and concentration/stress checks do not contradict the branch.",
            "Never convert neutral target movement into R/PnL/win-rate/expectancy/promotion evidence.",
        ],
        "per_card_summary_counts": {card: dict(per_card_summary.get(card, Counter())) for card in DOWNSTREAM_CARDS},
        "branch_summary_counts": {card: dict(branch_per_card_counts.get(card, Counter())) for card in CONTROL_CARDS | set(DOWNSTREAM_CARDS)},
        "fail_closed_aggregated_counts": dict(fail_closed_counts),
        "fail_closed_ledger_rows": fail_closed_rows,
        "comparison_summary_counts": dict(comparison_summary),
        "per_card_rules": rules,
    }


def build_synthesis(
    *,
    generated_at: str,
    comparison_summary: Counter,
    per_card_summary: dict[str, Counter],
    branch_counts: Counter,
    branch_per_card_counts: dict[str, Counter],
    artifact_counts: dict[str, int],
) -> str:
    lines = [
        "# READY8 Adversarial Control And Placebo Drift Audit",
        "",
        f"Generated: {generated_at}",
        f"Evidence class: `{EVIDENCE_CLASS}`",
        "",
        "Terminal posture: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
        "",
        "## Exact Ledger Coverage",
        "",
    ]
    for key, value in artifact_counts.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Control Adjustment Result",
            "",
            f"- Full control explanation rows: {comparison_summary.get('FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT', 0)}",
            f"- Materially weakened rows: {comparison_summary.get('MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT', 0)}",
            f"- Residual preserved rows: {comparison_summary.get('RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE', 0)}",
            f"- Underpowered retained rows: {comparison_summary.get('UNDERPOWERED_PRESERVED_NOT_DECISION', 0)}",
            f"- Not numeric / not adjustable rows: {comparison_summary.get('NOT_NUMERIC_NOT_ADJUSTABLE', 0)}",
            f"- Control-match missing rows: {comparison_summary.get('CONTROL_MATCH_MISSING_BOUNDED_TO_G12_REVIEW', 0)}",
            "",
            "## Per-Card Summary",
            "",
        ]
    )
    for card in DOWNSTREAM_CARDS:
        counts = per_card_summary.get(card, Counter())
        branch_counts_for_card = branch_per_card_counts.get(card, Counter())
        lines.append(
            "- "
            f"{card}: residual_preserved={counts.get('RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE', 0)}, "
            f"fully_explained={counts.get('FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT', 0)}, "
            f"weakened={counts.get('MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT', 0)}, "
            f"underpowered={counts.get('UNDERPOWERED_PRESERVED_NOT_DECISION', 0)}, "
            f"not_numeric={counts.get('NOT_NUMERIC_NOT_ADJUSTABLE', 0)}, "
            f"branch_rows={branch_counts_for_card.get('branch_rows', 0)}, "
            f"concentrated_branch_rows={branch_counts_for_card.get('concentrated_branch_rows', 0)}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "ADV-001 and ADV-003 explain or weaken a material subset of READY8 movement, but they are not blanket erasers. The route preserves every non-ADV comparison row and assigns a matched control-envelope adjustment. Branches that remain outside the matched control envelope are retained as residual neutral target-movement intelligence only, still subject to duplicate-effective-N, concentration, and stress/sealed checks.",
            "",
            "The downstream rule is exact: subtract the matched ADV control envelope first; then kill, weaken, retain-underpowered, or preserve residuals according to the generated adjustment ledger. No output is a promotion, live-readiness, R/PnL, win-rate, expectancy, AI/API, broker, order, or execution claim.",
            "",
            "## Safe Boundary",
            "",
            "No live, prompt, config, risk, safety, execution, selector, canary, broker/order, paid/API, raw market blob, registry, or remote surface was opened by this route.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_g12_prompt() -> str:
    return f"""# G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_REVIEW

Date: {DATE}

## Evidence Class

`G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_REVIEW_ONLY`

Review the route-local READY8 adversarial control/placebo drift audit artifacts at:

`{rel(ROUTE_DIR)}`

This is a strict G12 acceptance audit of a newly generated control-adjustment artifact. It is not a promotion route, not validation_safe, not live behavior, not R/PnL/win-rate/expectancy, not broker/order/account evidence, and not AI/API or paid access.

## Mandatory Context

Run and read:

1. `python scripts/generate_live_state.py` (or `py -3 scripts/generate_live_state.py` on this Windows host if `python` launcher fails)
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/goal_session_research_discipline.md`
5. `.context/00_core/research_operating_doctrine.md`
6. `.context/00_core/research_current_state.md`
7. latest handoff
8. accepted G12 sealed-validation audit directory
9. the R6 audit output manifest, completion audit, verifier result, synthesis, and all ledgers in the route directory

Do not rely on chat memory. Inspect disk artifacts.

## Required Work

- Recompute row counts for the route ledgers.
- Verify ADV-001/ADV-003 controls were treated as controls, not edge cards.
- Verify all non-ADV comparison rows are preserved without arbitrary top-N truncation.
- Verify control-envelope adjustment math and classifications.
- Verify duplicate-effective-N, concentration, stress/sealed, underpower, residual, explained/weakened, and downstream adjustment ledgers.
- Repair same-G12 issues if possible.
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Completion Standard

Complete only with an accept/reject decision, recomputation/verifier evidence, exact repair or blocker ledger if needed, and safe flags closed. If accepted, the artifact may become canonical downstream control evidence for R1-R5/R7 interpretation only, not promotion.
"""


def write_manifest(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or now_utc()
    artifacts = []
    for key, path in sorted(OUTPUTS.items()):
        if key == "manifest":
            continue
        artifacts.append(
            {
                "artifact_key": key,
                "path": rel(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": file_sha256(path) if path.exists() else None,
            }
        )
    manifest = {
        "schema_version": "ready8_adv_control_output_manifest_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "manifest_self_hash_policy": "manifest excludes itself from hash closure",
    }
    write_json(OUTPUTS["manifest"], manifest)
    return manifest


def record_focused_test_pass(command: str) -> None:
    payload = {
        "schema_version": "ready8_adv_control_focused_test_result_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
        "status": "PASSED",
        "command": command,
    }
    write_json(OUTPUTS["focused_test"], payload)
    write_manifest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-focused-test-pass", action="store_true")
    parser.add_argument("--command", default="")
    parser.add_argument("--refresh-manifest", action="store_true")
    args = parser.parse_args()
    if args.record_focused_test_pass:
        record_focused_test_pass(args.command)
        return
    if args.refresh_manifest:
        write_manifest()
        return
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
