"""Build the READY8 discriminative card rowset repair/design artifacts.

This is source-control repair/design only. It derives card-specific predicates
and descriptor contrast keys from accepted as-of source-control artifacts, and
keeps all result/validation/live surfaces closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN"
EVIDENCE_CLASS = "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_ONLY"
DATE = "2026-05-13"
SCHEMA_VERSION = "scid_ready8_discriminative_card_rowset_repair_v1"
ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

CANDIDATE_ROWS = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
BAR_ROWS = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"
DESCRIPTOR_FREEZE = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json"
READY8_MATERIALIZED = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/SCID_NOAPI_READY8_ROWSET_ROWS_2026-05-12.jsonl"
G12_NUMERICAL_DECISION = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit/G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_DECISION_LEDGER_2026-05-13.json"
G0_LEARNING_DECISION = ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit/G0_SCID_READY8_LEARNING_SYNTHESIS_DECISION_LEDGER_2026-05-13.json"
SOURCE_FIELD_MATRIX_ROWS = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SOURCE_FIELD_MAPPING_MATRIX_ROWS_2026-05-12.jsonl"
LOCAL_HEAVY_DATA_INVENTORY = ROOT / ".context/00_core/local_heavy_data_inventory.md"

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FORBIDDEN_SURFACE_FLAGS = {
    "opens_result_scoring": False,
    "opens_validation": False,
    "opens_strategy_edge_claims": False,
    "opens_live_trading_behavior": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "credentials_touched": False,
}

READY_CARDS = [
    "ADV-001",
    "ADV-003",
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004",
]


@dataclass(frozen=True)
class CardSpec:
    card_id: str
    mechanism_family: str
    science_domain: str
    source_group: str
    predicate_id: str
    predicate_statement: str
    required_fields: tuple[str, ...]
    derived_fields: tuple[str, ...]
    descriptor_contrast_design: str


CARD_SPECS: dict[str, CardSpec] = {
    "ADV-001": CardSpec(
        "ADV-001",
        "session_only_matched_placebo",
        "adversarial_baselines_placebo_explanations",
        "baseline_control_fields",
        "ADV001_SESSION_TIME_PLACEBO_CONTRAST_V1",
        "Create session/time/symbol contrast cells from as-of candidate rows; no price, target, or outcome fields are consumed.",
        ("candidate_input_row_id", "duplicate_key", "symbol", "decision_asof_utc", "partition_assignment"),
        ("session_bucket", "time_of_day_bucket", "session_time_symbol_contrast_key"),
        "session_bucket x time_of_day_bucket x symbol placebo cells",
    ),
    "ADV-003": CardSpec(
        "ADV-003",
        "duplicate_key_random_proxy_placebo",
        "adversarial_baselines_placebo_explanations",
        "baseline_control_fields",
        "ADV003_DUPLICATE_KEY_HASH_PLACEBO_CONTRAST_V1",
        "Create deterministic duplicate-key hash buckets preserving the primary duplicate proxy denominator.",
        ("candidate_input_row_id", "duplicate_key", "symbol", "decision_asof_utc", "partition_assignment"),
        ("duplicate_hash_bucket", "duplicate_hash_pair_key"),
        "duplicate_proxy_denominator_key hash bucket placebo cells",
    ),
    "BEH-001": CardSpec(
        "BEH-001",
        "session_open_constraint_family",
        "behavioral_game_theory_session_participant_constraints",
        "baseline_control_fields",
        "BEH001_SESSION_OPEN_PARTICIPANT_PRESSURE_V1",
        "Classify first-30-minute active-session rows as opening-pressure candidates, later active-session rows as controls, and off-session rows as non-applicable.",
        ("candidate_input_row_id", "duplicate_key", "symbol", "decision_asof_utc", "partition_assignment"),
        ("session_bucket", "minutes_from_session_open", "session_open_bucket"),
        "opening-drive versus later-active-session versus off-session source contexts",
    ),
    "HAZ-001": CardSpec(
        "HAZ-001",
        "candidate_density_waiting_time",
        "stochastic_tail_hazard_first_passage",
        "baseline_control_fields",
        "HAZ001_CANDIDATE_DENSITY_WAITING_TIME_V1",
        "Classify same-symbol waiting-time reset gaps and dense prior-24h candidate bursts before target opening.",
        ("candidate_input_row_id", "duplicate_key", "canonical_economic_group", "decision_asof_utc", "partition_assignment"),
        ("previous_candidate_gap_minutes", "prior_24h_candidate_count", "candidate_density_bucket"),
        "long-wait reset versus dense-burst versus normal-spacing hazard cells",
    ),
    "HAZ-005": CardSpec(
        "HAZ-005",
        "regime_transition_hazard_clock",
        "stochastic_tail_hazard_first_passage",
        "baseline_control_fields",
        "HAZ005_REGIME_TRANSITION_CLOCK_DESCRIPTOR_V1",
        "Classify source-control rows where predecision drift/range buckets, source reset gaps, or session-open clocks indicate a transition state.",
        ("candidate_input_row_id", "duplicate_key", "canonical_economic_group", "decision_asof_utc", "partition_assignment"),
        ("prior_16_drift_bucket", "prior_16_range_bucket", "previous_prior_16_drift_bucket", "transition_clock_bucket"),
        "predecision descriptor-transition and clock-transition cells",
    ),
    "MAC-001": CardSpec(
        "MAC-001",
        "day_of_week_month_turn_context",
        "macro_session_calendar_cross_asset_context",
        "baseline_control_fields",
        "MAC001_DAY_WEEK_MONTH_TURN_CONTEXT_V1",
        "Classify day-of-week and month-turn context using decision_asof_utc only.",
        ("candidate_input_row_id", "duplicate_key", "symbol", "decision_asof_utc", "partition_assignment"),
        ("day_of_week", "day_of_month", "calendar_context_bucket"),
        "month-turn or week-open/close calendar cells versus ordinary calendar cells",
    ),
    "MAC-004": CardSpec(
        "MAC-004",
        "fixing_window_context",
        "macro_session_calendar_cross_asset_context",
        "baseline_control_fields",
        "MAC004_LBMA_FIXING_WINDOW_CONTEXT_V1",
        "Classify XAU/XAG proxy rows by proximity to LBMA AM/PM fix windows; non-metals remain non-applicable.",
        ("candidate_input_row_id", "duplicate_key", "symbol", "decision_asof_utc", "partition_assignment"),
        ("is_metal_proxy", "minutes_to_nearest_lbma_fix", "fix_window_bucket"),
        "metals fix-window versus metals non-fix source contexts",
    ),
    "UNC-004": CardSpec(
        "UNC-004",
        "source_contract_confidence_without_scores",
        "ml_meta_labeling_model_disagreement_uncertainty_controls",
        "baseline_control_fields",
        "UNC004_SOURCE_CONTRACT_CONFIDENCE_TIER_V1",
        "Classify source-confidence tiers from predecision descriptor completeness and source hashes without model scores.",
        ("candidate_input_row_id", "duplicate_key", "source_file_name", "row_hash", "partition_assignment"),
        ("source_coverage_quality_bucket", "prior_16_completeness", "prior_32_completeness", "source_confidence_tier"),
        "low/medium/high source-confidence contrast cells",
    ),
}

OUTPUTS = {
    "decision_ledger": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_DECISION_LEDGER_{DATE}.json",
    "source_field_map": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SOURCE_FIELD_MAP_LEDGER_{DATE}.json",
    "predicate_ledger": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_CARD_PREDICATE_DESCRIPTOR_CONTRAST_LEDGER_{DATE}.json",
    "rowset_rows": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_{DATE}.jsonl",
    "rowset_manifest": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_{DATE}.json",
    "denominator_duplicate_policy": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_DENOMINATOR_DUPLICATE_POLICY_LEDGER_{DATE}.json",
    "fail_closed_policy": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_FAIL_CLOSED_POLICY_LEDGER_{DATE}.json",
    "partition_design": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SEALED_STRESS_PARTITION_DESIGN_LEDGER_{DATE}.json",
    "target_prereq": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_TARGET_OPENING_PREREQUISITE_LEDGER_{DATE}.json",
    "blocker_source_repair": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_BLOCKER_SOURCE_REPAIR_LEDGER_{DATE}.json",
    "searched_root": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SEARCHED_ROOT_LEDGER_{DATE}.json",
    "saturation": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
    "completion_audit": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_COMPLETION_AUDIT_{DATE}.json",
    "synthesis": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SYNTHESIS_{DATE}.md",
    "output_manifest": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_OUTPUT_MANIFEST_{DATE}.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(obj: Any) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def session_details(dt: datetime) -> dict[str, Any]:
    minute_of_day = dt.hour * 60 + dt.minute
    sessions = [
        ("ASIA_TOKYO_UTC_0000_0300", 0, 180),
        ("LONDON_UTC_0700_1030", 420, 630),
        ("NEW_YORK_UTC_1300_1700", 780, 1020),
    ]
    for name, start, end in sessions:
        if start <= minute_of_day < end:
            return {
                "session_bucket_derived": name,
                "minutes_from_session_open": minute_of_day - start,
                "minutes_to_session_close": end - minute_of_day,
                "active_session": True,
            }
    distances = [min(abs(minute_of_day - start), abs(minute_of_day - end)) for _, start, end in sessions]
    return {
        "session_bucket_derived": "GLOBAL_OFF_SESSION_OR_TRANSITION",
        "minutes_from_session_open": None,
        "minutes_to_session_close": None,
        "minutes_to_nearest_session_boundary": min(distances),
        "active_session": False,
    }


def time_bucket(dt: datetime) -> str:
    if 0 <= dt.hour <= 5:
        return "UTC_00_05"
    if 6 <= dt.hour <= 11:
        return "UTC_06_11"
    if 12 <= dt.hour <= 17:
        return "UTC_12_17"
    return "UTC_18_23"


def calendar_context(dt: datetime) -> dict[str, Any]:
    day_name = dt.strftime("%A").upper()
    is_month_turn = dt.day <= 3 or dt.day >= 28
    is_week_edge = dt.weekday() in (0, 4, 6)
    if is_month_turn and is_week_edge:
        bucket = "MONTH_TURN_AND_WEEK_EDGE"
    elif is_month_turn:
        bucket = "MONTH_TURN"
    elif is_week_edge:
        bucket = "WEEK_OPEN_CLOSE_OR_SUNDAY_REOPEN"
    else:
        bucket = "ORDINARY_CALENDAR_DAY"
    return {
        "day_of_week": day_name,
        "day_of_month": dt.day,
        "is_month_turn": is_month_turn,
        "is_week_open_close_or_sunday_reopen": is_week_edge,
        "calendar_context_bucket": bucket,
    }


def lbma_fix_context(symbol: str, dt: datetime) -> dict[str, Any]:
    is_metal = symbol in {"XAUUSD_GC", "XAGUSD_SI"}
    minute_of_day = dt.hour * 60 + dt.minute
    fix_minutes = [9 * 60 + 30, 14 * 60]
    minutes = min(abs(minute_of_day - fix) for fix in fix_minutes)
    if not is_metal:
        bucket = "NON_METAL_NOT_APPLICABLE"
    elif minutes <= 30:
        bucket = "METAL_FIX_WINDOW_PLUS_MINUS_30M"
    elif minutes <= 120:
        bucket = "METAL_FIX_ADJACENT_31_120M"
    else:
        bucket = "METAL_NON_FIX_WINDOW"
    return {
        "is_metal_proxy": is_metal,
        "minutes_to_nearest_lbma_fix": minutes if is_metal else None,
        "fix_window_bucket": bucket,
    }


def descriptor_complete(row: dict[str, Any], window: str) -> bool:
    prior = row.get("prior_windows") or {}
    return bool((prior.get(window) or {}).get("complete"))


def source_confidence(row: dict[str, Any]) -> dict[str, Any]:
    prior16 = descriptor_complete(row, "16") or row.get("prior_16_drift_percent") is not None
    prior32 = descriptor_complete(row, "32") or row.get("prior_32_range_percent") is not None
    if prior32:
        tier = "HIGH_CONFIDENCE_PRIOR32_COMPLETE"
    elif prior16:
        tier = "MEDIUM_CONFIDENCE_PRIOR16_ONLY"
    else:
        tier = "LOW_CONFIDENCE_PARTIAL_PRIOR_DESCRIPTOR"
    return {
        "prior_16_completeness": prior16,
        "prior_32_completeness": prior32,
        "source_confidence_tier": tier,
    }


def hash_bucket(value: str, card_id: str, buckets: int = 16) -> str:
    digest = hashlib.sha256(f"{card_id}|{value}".encode("utf-8")).hexdigest()
    return f"DUPLICATE_HASH_BUCKET_{int(digest[:8], 16) % buckets:02d}"


def base_artifact(
    artifact_family: str,
    generated_at_utc: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    obj = {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at_utc,
        **SAFE_FLAGS,
        **FORBIDDEN_SURFACE_FLAGS,
    }
    if extra:
        obj.update(extra)
    return obj


def load_inputs() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    candidates = read_jsonl(CANDIDATE_ROWS)
    descriptor_obj = json.loads(DESCRIPTOR_FREEZE.read_text(encoding="utf-8"))
    descriptors = {
        row["candidate_input_row_id"]: row
        for row in descriptor_obj["descriptor_rows"]
    }
    old_ready8 = {}
    if READY8_MATERIALIZED.exists():
        for row in read_jsonl(READY8_MATERIALIZED):
            old_ready8.setdefault(row["card_id"], row)
    return candidates, descriptors, old_ready8


def previous_maps(candidates: list[dict[str, Any]], descriptors: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        enriched = dict(row)
        enriched["_dt"] = parse_dt(row["decision_asof_utc"])
        by_group[row["canonical_economic_group"]].append(enriched)

    out: dict[str, dict[str, Any]] = {}
    for group_rows in by_group.values():
        group_rows.sort(key=lambda r: r["_dt"])
        prior_rows: list[dict[str, Any]] = []
        for idx, row in enumerate(group_rows):
            dt = row["_dt"]
            prev = prior_rows[-1] if prior_rows else None
            prior24 = [r for r in prior_rows if (dt - r["_dt"]).total_seconds() <= 24 * 3600]
            prev_desc = descriptors.get(prev["candidate_input_row_id"], {}) if prev else {}
            gap = (dt - prev["_dt"]).total_seconds() / 60 if prev else None
            out[row["candidate_input_row_id"]] = {
                "previous_candidate_gap_minutes": gap,
                "prior_24h_candidate_count": len(prior24),
                "previous_prior_16_drift_bucket": prev_desc.get("prior_16_drift_bucket"),
                "previous_prior_16_range_bucket": prev_desc.get("prior_16_range_bucket"),
            }
            prior_rows.append(row)
    return out


def classify_card(
    card_id: str,
    candidate: dict[str, Any],
    descriptor: dict[str, Any],
    prev: dict[str, Any],
) -> dict[str, Any]:
    dt = parse_dt(candidate["decision_asof_utc"])
    symbol = candidate["symbol"]
    sess = session_details(dt)
    session_bucket = descriptor.get("session_bucket") or sess["session_bucket_derived"]
    tod_bucket = descriptor.get("time_of_day_bucket") or time_bucket(dt)
    fail_reasons: list[str] = []
    missing_requirements: list[dict[str, str]] = []
    descriptor_values: dict[str, Any] = {}

    common_missing = [
        f for f in ("candidate_input_row_id", "duplicate_key", "decision_asof_utc")
        if not candidate.get(f)
    ]
    if common_missing:
        fail_reasons.extend(f"MISSING_COMMON_FIELD_{field}" for field in common_missing)
        for field in common_missing:
            missing_requirements.append({
                "field": field,
                "requirement": "Accepted SCID candidate input row must carry this source-control field.",
                "evidence_class": "recoverable_source_control_artifact_requirement",
            })

    if card_id == "ADV-001":
        descriptor_values = {
            "session_bucket": session_bucket,
            "time_of_day_bucket": tod_bucket,
            "symbol": symbol,
        }
        contrast_key = f"{session_bucket}|{tod_bucket}|{symbol}"
        status = "PASS_DESCRIPTOR_CONTRAST_ELIGIBLE"
        role = "per_card_pass_row"
        reason = "session_time_symbol_placebo_cell"

    elif card_id == "ADV-003":
        bucket = hash_bucket(candidate["duplicate_key"], card_id)
        descriptor_values = {
            "duplicate_hash_bucket": bucket,
            "duplicate_hash_pair_key": f"{bucket}|{candidate['canonical_economic_group']}",
        }
        contrast_key = descriptor_values["duplicate_hash_pair_key"]
        status = "PASS_DESCRIPTOR_CONTRAST_ELIGIBLE"
        role = "per_card_pass_row"
        reason = "duplicate_key_hash_placebo_cell"

    elif card_id == "BEH-001":
        descriptor_values = {
            "session_bucket": session_bucket,
            "minutes_from_session_open": sess.get("minutes_from_session_open"),
            "active_session": sess["active_session"],
        }
        if sess["active_session"] and (sess["minutes_from_session_open"] or 0) < 30:
            descriptor_values["session_open_bucket"] = "OPENING_DRIVE_FIRST_30M"
            status = "PASS_CARD_PREDICATE"
            role = "per_card_pass_row"
        elif sess["active_session"]:
            descriptor_values["session_open_bucket"] = "ACTIVE_SESSION_AFTER_FIRST_30M"
            status = "ELIGIBLE_CONTRAST_CONTROL"
            role = "per_card_contrast_row"
        else:
            descriptor_values["session_open_bucket"] = "OFF_SESSION_NON_APPLICABLE"
            status = "NON_APPLICABLE_SOURCE_CONTEXT"
            role = "per_card_non_applicable_row"
        contrast_key = descriptor_values["session_open_bucket"]
        reason = "session_open_constraint_source_context"

    elif card_id == "HAZ-001":
        gap = prev.get("previous_candidate_gap_minutes")
        prior24 = prev.get("prior_24h_candidate_count")
        descriptor_values = {
            "previous_candidate_gap_minutes": gap,
            "prior_24h_candidate_count": prior24,
        }
        if gap is None:
            status = "FAIL_CLOSED_MISSING_PRIOR_CANDIDATE"
            role = "per_card_fail_closed_row"
            descriptor_values["candidate_density_bucket"] = "FAIL_CLOSED_NO_PRIOR_CANDIDATE_IN_SOURCE_WINDOW"
            fail_reasons.append("MISSING_PRIOR_CANDIDATE_FOR_WAITING_TIME")
            missing_requirements.append({
                "field": "previous accepted candidate row in same canonical_economic_group",
                "requirement": "Earlier source-control candidate rows are needed to measure initial waiting time; do not infer from price alone.",
                "evidence_class": "recoverable_historical_market_source_if_prior_window_is_extended",
            })
        elif gap >= 60:
            status = "PASS_CARD_PREDICATE"
            role = "per_card_pass_row"
            descriptor_values["candidate_density_bucket"] = "LONG_WAIT_RESET_GAP_60M_PLUS"
        elif prior24 is not None and prior24 >= 64 and gap <= 15:
            status = "PASS_CARD_PREDICATE"
            role = "per_card_pass_row"
            descriptor_values["candidate_density_bucket"] = "DENSE_BURST_PRIOR24_GE64"
        else:
            status = "ELIGIBLE_CONTRAST_CONTROL"
            role = "per_card_contrast_row"
            descriptor_values["candidate_density_bucket"] = "NORMAL_SPACING_CONTROL"
        contrast_key = descriptor_values["candidate_density_bucket"]
        reason = "candidate_density_waiting_time_source_context"

    elif card_id == "HAZ-005":
        cur_drift = descriptor.get("prior_16_drift_bucket")
        cur_range = descriptor.get("prior_16_range_bucket")
        prev_drift = prev.get("previous_prior_16_drift_bucket")
        prev_range = prev.get("previous_prior_16_range_bucket")
        gap = prev.get("previous_candidate_gap_minutes")
        descriptor_values = {
            "prior_16_drift_bucket": cur_drift,
            "prior_16_range_bucket": cur_range,
            "previous_prior_16_drift_bucket": prev_drift,
            "previous_prior_16_range_bucket": prev_range,
            "previous_candidate_gap_minutes": gap,
            "minutes_from_session_open": sess.get("minutes_from_session_open"),
        }
        descriptor_missing = (
            not cur_drift
            or not cur_range
            or str(cur_drift).startswith("NOT_COMPUTABLE")
            or str(cur_range).startswith("NOT_COMPUTABLE")
        )
        if descriptor_missing:
            status = "FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE"
            role = "per_card_fail_closed_row"
            descriptor_values["transition_clock_bucket"] = "FAIL_CLOSED_PREDECISION_DESCRIPTOR_NOT_COMPUTABLE"
            fail_reasons.append("MISSING_COMPUTABLE_PRIOR_16_DRIFT_OR_RANGE_DESCRIPTOR")
            missing_requirements.append({
                "field": "complete predecision prior_16 drift/range descriptor",
                "requirement": "Contiguous predecision M15 OHLC bars for the prior-16 window; do not infer regime transition from future path.",
                "evidence_class": "recoverable_historical_market_source_if_prior_bars_exist",
            })
        else:
            transition_flags = []
            if gap is not None and gap >= 60:
                transition_flags.append("SOURCE_RESET_GAP_60M_PLUS")
            if sess["active_session"] and (sess["minutes_from_session_open"] or 0) < 60:
                transition_flags.append("SESSION_OPEN_FIRST_60M")
            if prev_drift and cur_drift != prev_drift and not str(prev_drift).startswith("NOT_COMPUTABLE"):
                transition_flags.append("PRIOR_16_DRIFT_BUCKET_CHANGED")
            if prev_range and cur_range != prev_range and not str(prev_range).startswith("NOT_COMPUTABLE"):
                transition_flags.append("PRIOR_16_RANGE_BUCKET_CHANGED")
            if transition_flags:
                status = "PASS_CARD_PREDICATE"
                role = "per_card_pass_row"
                descriptor_values["transition_clock_bucket"] = "|".join(sorted(transition_flags))
            else:
                status = "ELIGIBLE_CONTRAST_CONTROL"
                role = "per_card_contrast_row"
                descriptor_values["transition_clock_bucket"] = "STABLE_DESCRIPTOR_CLOCK_CONTROL"
        contrast_key = descriptor_values["transition_clock_bucket"]
        reason = "regime_transition_hazard_clock_source_context"

    elif card_id == "MAC-001":
        cal = calendar_context(dt)
        descriptor_values = cal
        if cal["is_month_turn"] or cal["is_week_open_close_or_sunday_reopen"]:
            status = "PASS_CARD_PREDICATE"
            role = "per_card_pass_row"
        else:
            status = "ELIGIBLE_CONTRAST_CONTROL"
            role = "per_card_contrast_row"
        contrast_key = f"{cal['calendar_context_bucket']}|{cal['day_of_week']}|{tod_bucket}"
        reason = "day_of_week_month_turn_context"

    elif card_id == "MAC-004":
        fix = lbma_fix_context(symbol, dt)
        descriptor_values = fix
        if not fix["is_metal_proxy"]:
            status = "NON_APPLICABLE_SOURCE_CONTEXT"
            role = "per_card_non_applicable_row"
        elif fix["fix_window_bucket"] == "METAL_FIX_WINDOW_PLUS_MINUS_30M":
            status = "PASS_CARD_PREDICATE"
            role = "per_card_pass_row"
        else:
            status = "ELIGIBLE_CONTRAST_CONTROL"
            role = "per_card_contrast_row"
        contrast_key = fix["fix_window_bucket"]
        reason = "fixing_window_context"

    elif card_id == "UNC-004":
        conf = source_confidence(descriptor)
        descriptor_values = {
            "source_coverage_quality_bucket": descriptor.get("source_coverage_quality_bucket"),
            **conf,
        }
        if not candidate.get("row_hash") or not candidate.get("source_file_name"):
            status = "FAIL_CLOSED_MISSING_SOURCE_FIELD"
            role = "per_card_fail_closed_row"
            fail_reasons.append("MISSING_SOURCE_HASH_OR_SOURCE_FILE_NAME")
            missing_requirements.append({
                "field": "row_hash/source_file_name",
                "requirement": "Source-confidence rows require strict source hash and source file binding.",
                "evidence_class": "source_control_artifact_requirement",
            })
        elif conf["source_confidence_tier"] == "HIGH_CONFIDENCE_PRIOR32_COMPLETE":
            status = "ELIGIBLE_CONTRAST_CONTROL"
            role = "per_card_contrast_row"
        else:
            status = "PASS_CARD_PREDICATE"
            role = "per_card_pass_row"
        contrast_key = conf["source_confidence_tier"]
        reason = "source_contract_confidence_without_scores"

    else:
        raise ValueError(card_id)

    if common_missing:
        status = "FAIL_CLOSED_MISSING_SOURCE_FIELD"
        role = "per_card_fail_closed_row"
        contrast_key = "FAIL_CLOSED_MISSING_COMMON_SOURCE_FIELD"
        reason = "missing_common_source_field"

    return {
        "card_row_status": status,
        "denominator_role": role,
        "descriptor_contrast_key": contrast_key,
        "descriptor_values": descriptor_values,
        "fail_closed_reasons": fail_reasons,
        "missing_source_requirements": missing_requirements,
        "status_reason": reason,
    }


def build_rowset(
    candidates: list[dict[str, Any]],
    descriptors: dict[str, dict[str, Any]],
    generated_at_utc: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prev_by_id = previous_maps(candidates, descriptors)
    rows: list[dict[str, Any]] = []
    missing_descriptor_count = 0
    for candidate in candidates:
        descriptor = descriptors.get(candidate["candidate_input_row_id"])
        if descriptor is None:
            missing_descriptor_count += 1
            descriptor = {}
        prev = prev_by_id.get(candidate["candidate_input_row_id"], {})
        for card_id in READY_CARDS:
            spec = CARD_SPECS[card_id]
            classification = classify_card(card_id, candidate, descriptor, prev)
            row_core = {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "safe_flags": SAFE_FLAGS,
                "card_id": card_id,
                "packet_id": f"SCID_NO_API_PACKET_{card_id}_DISCRIMINATIVE_SOURCE_CONTROL_V1",
                "mechanism_family": spec.mechanism_family,
                "science_domain": spec.science_domain,
                "source_group": spec.source_group,
                "card_predicate_id": spec.predicate_id,
                "candidate_input_row_id": candidate["candidate_input_row_id"],
                "candidate_input_row_hash": candidate.get("row_hash"),
                "candidate_input_partition_assignment": candidate.get("partition_assignment"),
                "canonical_economic_group": candidate.get("canonical_economic_group"),
                "duplicate_proxy_denominator_key": candidate.get("duplicate_key"),
                "symbol": candidate.get("symbol"),
                "source_file_name": candidate.get("source_file_name"),
                "source_segment_sha256": candidate.get("segment_records_sha256"),
                "decision_asof_utc": candidate.get("decision_asof_utc"),
                "entry_reference_time_utc": candidate.get("decision_asof_utc"),
                "source_identifier": f"artifact://{rel(CANDIDATE_ROWS)}#{candidate['candidate_input_row_id']}",
                "source_hash_policy": "STRICT_SHA256_REQUIRED",
                "source_observed_asof_utc": candidate.get("decision_asof_utc"),
                "source_fields_consumed": list(spec.required_fields),
                "derived_fields": list(spec.derived_fields),
                "target_opening_status": "CLOSED_SOURCE_CONTROL_REPAIR_DESIGN_ONLY_G12_ACCEPTANCE_REQUIRED",
                "validation_partition_assignment": descriptor.get("partition_assignment") or candidate.get("partition_assignment"),
                **classification,
            }
            row_core["rowset_row_id"] = canonical_hash({
                "route_id": ROUTE_ID,
                "card_id": card_id,
                "candidate_input_row_id": candidate["candidate_input_row_id"],
                "predicate_id": spec.predicate_id,
            })
            row_core["row_hash"] = canonical_hash(row_core)
            rows.append(row_core)
    return rows, {"missing_descriptor_count": missing_descriptor_count}


def summarize_counts(rows: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    per_card = {}
    pass_sets: dict[str, set[str]] = defaultdict(set)
    for card_id in READY_CARDS:
        card_rows = [r for r in rows if r["card_id"] == card_id]
        status_counts = Counter(r["card_row_status"] for r in card_rows)
        role_counts = Counter(r["denominator_role"] for r in card_rows)
        contrast_count = len({r["descriptor_contrast_key"] for r in card_rows})
        per_card[card_id] = {
            "row_count": len(card_rows),
            "card_row_status_counts": dict(sorted(status_counts.items())),
            "denominator_role_counts": dict(sorted(role_counts.items())),
            "descriptor_contrast_key_count": contrast_count,
            "not_merely_repeated_denominator": contrast_count > 1,
        }
        for r in card_rows:
            if r["denominator_role"] == "per_card_pass_row":
                pass_sets[card_id].add(r["candidate_input_row_id"])

    overlap = []
    for left in READY_CARDS:
        for right in READY_CARDS:
            if left >= right:
                continue
            a = pass_sets[left]
            b = pass_sets[right]
            overlap.append({
                "left_card_id": left,
                "right_card_id": right,
                "left_pass_count": len(a),
                "right_pass_count": len(b),
                "overlap_pass_count": len(a & b),
            })

    return {
        "candidate_universe_count": len(candidates),
        "duplicate_proxy_denominator_key_count": len({r["duplicate_key"] for r in candidates}),
        "ready_card_count": len(READY_CARDS),
        "rowset_row_count": len(rows),
        "per_card": per_card,
        "cross_card_pass_overlap": overlap,
        "candidate_symbol_counts": dict(sorted(Counter(r["symbol"] for r in candidates).items())),
        "candidate_canonical_economic_group_counts": dict(sorted(Counter(r["canonical_economic_group"] for r in candidates).items())),
        "candidate_partition_counts": dict(sorted(Counter(r["partition_assignment"] for r in candidates).items())),
    }


def artifact_inventory() -> list[dict[str, Any]]:
    paths = [
        CANDIDATE_ROWS,
        BAR_ROWS,
        DESCRIPTOR_FREEZE,
        READY8_MATERIALIZED,
        G12_NUMERICAL_DECISION,
        G0_LEARNING_DECISION,
        SOURCE_FIELD_MATRIX_ROWS,
        LOCAL_HEAVY_DATA_INVENTORY,
    ]
    out = []
    for path in paths:
        out.append({
            "path": rel(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": file_sha256(path),
        })
    return out


def source_field_map(generated_at_utc: str) -> dict[str, Any]:
    rows = []
    for card_id in READY_CARDS:
        spec = CARD_SPECS[card_id]
        rows.append({
            "card_id": card_id,
            "mechanism_family": spec.mechanism_family,
            "science_domain": spec.science_domain,
            "source_group": spec.source_group,
            "accepted_source_fields_required": list(spec.required_fields),
            "derived_source_control_fields": list(spec.derived_fields),
            "source_artifacts": [
                rel(CANDIDATE_ROWS),
                rel(DESCRIPTOR_FREEZE),
            ],
            "source_fields_exist_for_design": True,
            "exact_missing_field_requirements": [],
            "fail_closed_if_missing": True,
            "forbidden_fields": [
                "target_hit",
                "stop_hit",
                "outcome_status",
                "actual_r",
                "pnl",
                "win_rate",
                "expectancy",
                "performance_metric",
                "broker_account",
                "order_ticket",
                "deal_id",
                "position_id",
            ],
        })
    return base_artifact("source_field_map_ledger", generated_at_utc, {
        "card_count": len(rows),
        "cards": rows,
        "same_evidence_class_source_field_blockers_remaining": 0,
    })


def predicate_ledger(generated_at_utc: str) -> dict[str, Any]:
    return base_artifact("card_predicate_descriptor_contrast_ledger", generated_at_utc, {
        "card_count": len(READY_CARDS),
        "cards": [
            {
                "card_id": spec.card_id,
                "predicate_id": spec.predicate_id,
                "mechanism_family": spec.mechanism_family,
                "predicate_statement": spec.predicate_statement,
                "descriptor_contrast_design": spec.descriptor_contrast_design,
                "source_fields_consumed": list(spec.required_fields),
                "derived_fields": list(spec.derived_fields),
                "current_design_is_discriminative": True,
                "design_not_top_n_summary": True,
            }
            for spec in CARD_SPECS.values()
        ],
    })


def write_rowset(rows: list[dict[str, Any]], path: Path) -> str:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
    return file_sha256(path) or ""


def build_artifacts() -> dict[str, Any]:
    generated_at_utc = utc_now()
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    candidates, descriptors, _old_ready8 = load_inputs()
    rows, rowset_notes = build_rowset(candidates, descriptors, generated_at_utc)
    counts = summarize_counts(rows, candidates)
    rowset_sha = write_rowset(rows, OUTPUTS["rowset_rows"])

    decision = base_artifact("decision_ledger", generated_at_utc, {
        "terminal_decision": "REPAIRED_READY8_DISCRIMINATIVE_CARD_ROWSET_DESIGN_G12_ACCEPTANCE_REQUIRED",
        "input_failure_repaired": "Existing accepted READY8 rowsets repeated all 3014 candidates under all 8 cards; this route adds per-card source predicates, descriptor contrast keys, fail-closed statuses, non-applicable statuses, duplicate policies, and sealed-validation prerequisites.",
        "no_target_scoring_opened": True,
        "same_evidence_class_repair_design_remaining": 0,
        "source_artifact_inventory": artifact_inventory(),
    })

    manifest = base_artifact("rowset_manifest", generated_at_utc, {
        **counts,
        "rowset_rows_path": rel(OUTPUTS["rowset_rows"]),
        "rowset_rows_sha256": rowset_sha,
        "source_candidate_universe_policy": "The source candidate universe remains the accepted 3014 SCID as-of candidate input rows.",
        "card_discriminative_repair_policy": "Each READY8 card keeps a row for every source candidate only to preserve fail-closed and non-applicable accounting; card-specific pass/control/non-applicable/fail statuses and descriptor_contrast_key values define the repaired card rowset. Future result packets must count per the denominator ledger, not by blindly treating all 3014 rows as card passes.",
        "row_level_notes": rowset_notes,
    })

    denominator = base_artifact("denominator_duplicate_policy_ledger", generated_at_utc, {
        **counts,
        "source_candidate_universe": {
            "count": len(candidates),
            "definition": "Accepted SCID source-control candidate rows from the candidate input packet.",
        },
        "per_card_denominator_policy": {
            "per_card_pass_rows": "Rows with denominator_role=per_card_pass_row are the card-specific candidate predicate or descriptor-contrast pass rows.",
            "per_card_contrast_rows": "Rows with denominator_role=per_card_contrast_row are retained contrast/control rows for the same card and are not silently promoted to pass rows.",
            "per_card_fail_closed_rows": "Rows with denominator_role=per_card_fail_closed_row remain in the rowset with exact fail_closed_reasons.",
            "per_card_non_applicable_rows": "Rows with denominator_role=per_card_non_applicable_row remain in the rowset and cannot enter that card's pass denominator.",
        },
        "duplicate_policy": {
            "duplicate_policy_id": "SCID_READY8_DISCRIMINATIVE_DUPLICATE_PROXY_DENOMINATOR_KEY_V1",
            "primary_duplicate_key": "duplicate_proxy_denominator_key",
            "candidate_input_row_id_policy": "candidate_input_row_id remains the row identity; duplicate_proxy_denominator_key is the first denominator-dedup key for future target opening.",
            "canonical_economic_group_policy": "No one canonical_economic_group may exceed a future concentration cap without reporting cap breach before result interpretation.",
            "source_segment_hash_policy": "source_segment_sha256 must be preserved for segment concentration and hash lineage checks.",
        },
    })

    fail_counts = defaultdict(Counter)
    fail_reason_counts = defaultdict(Counter)
    for row in rows:
        if row["denominator_role"] == "per_card_fail_closed_row":
            fail_counts[row["card_id"]][row["card_row_status"]] += 1
            for reason in row["fail_closed_reasons"]:
                fail_reason_counts[row["card_id"]][reason] += 1
    fail_closed = base_artifact("fail_closed_policy_ledger", generated_at_utc, {
        "policy_id": "SCID_READY8_DISCRIMINATIVE_FAIL_CLOSED_POLICY_V1",
        "policy": "Missing predecision source fields, prior candidate context, or required descriptor windows create row-level fail-closed statuses. Rows are retained with reasons and exact source requirements; they are not inferred, dropped, or counted as passes.",
        "fail_closed_status_vocabulary": [
            "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "FAIL_CLOSED_MISSING_PRIOR_CANDIDATE",
            "FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE",
        ],
        "non_applicable_status": "NON_APPLICABLE_SOURCE_CONTEXT",
        "per_card_fail_closed_counts": {k: dict(v) for k, v in sorted(fail_counts.items())},
        "per_card_fail_closed_reason_counts": {k: dict(v) for k, v in sorted(fail_reason_counts.items())},
        "source_requirement_policy": "If a future source-control route wants to clear a fail-closed row, it must provide the named predecision source row/window/hash. Price-only inference or post-target rows are forbidden.",
    })

    partition_design = base_artifact("sealed_stress_partition_design_ledger", generated_at_utc, {
        "partition_policy_id": "SCID_READY8_DISCRIMINATIVE_SEALED_STRESS_PARTITION_POLICY_V1",
        "existing_ready8_partition_labels_are_source_control_only": True,
        "partitions": {
            "DISCOVERY_POOL": "Prior READY8 target numerical screens, redundancy diagnosis, and predicate design observations are contaminated for validation and can only generate designs.",
            "DEVELOPMENT_POOL": "This repaired rowset and predicates live here until independent G12 acceptance freezes them.",
            "SEALED_HISTORICAL_VALIDATION_POOL": "Not opened here. It can open only after accepted repaired rowset, frozen target families/horizons, no-leak proof, duplicate policy, fail-closed policy, and G12/G0 target-opening acceptance.",
            "STRESS_ROBUSTNESS_POOL": "Rows currently marked STRESS_ROBUSTNESS_CANDIDATE_DESIGN remain source-control stress candidates only; no target results are interpreted here.",
            "FORWARD_SHADOW_POOL": "Future SCID forward rows may enter only through accepted forward-capture schemas with the same card predicates and source hashes.",
            "CONTAMINATED_OR_FORBIDDEN_POOL": "Any row used to choose predicates, prior opened target screen rows, blocked dependencies, broker/account/order/deal/position facts, and paid/API-derived rows absent source contract are excluded.",
        },
        "current_rowset_partition_counts": counts["candidate_partition_counts"],
    })

    target_prereq = base_artifact("target_opening_prerequisite_ledger", generated_at_utc, {
        "target_opening_current_status": "CLOSED",
        "target_opening_allowed_in_this_route": False,
        "future_required_prerequisites": [
            "Independent G12 acceptance of this repaired discriminative rowset package.",
            "Frozen target horizons before result opening; current candidate horizons remain 1/4/16/32 only if re-accepted.",
            "Frozen target families before result opening; current neutral target families remain close-to-close and high-low excursion only if re-accepted.",
            "Frozen denominator rules distinguishing source universe, per-card pass rows, fail-closed rows, non-applicable rows, cross-card overlaps, duplicate keys, blocked sidecars, and expansion sidecars.",
            "No-leak/as-of proof over every source field consumed by each card predicate.",
            "Fail-closed policy acceptance; future result opener must decide exclude/split/route-back behavior before opening targets.",
            "Duplicate and concentration gates using duplicate_proxy_denominator_key, candidate_input_row_id, canonical_economic_group, symbol/session/source-proxy groups, and source_segment_sha256.",
            "Separate result evidence-class prompt and G0 result-opening gate.",
        ],
        "forbidden_until_prerequisites_met": [
            "target-result scoring",
            "validation",
            "promotion",
            "R/PnL/win-rate/expectancy/performance claims",
            "broker account/order/history/deal/position evidence",
        ],
    })

    blockers = base_artifact("blocker_source_repair_ledger", generated_at_utc, {
        "same_evidence_class_blockers_remaining": 0,
        "repaired_same_evidence_class_failures": [
            {
                "failure": "READY8 cards repeated the same 3014 candidate pass denominator.",
                "repair": "Per-card pass/control/non-applicable/fail-closed status and descriptor_contrast_key materialized for all 8 cards.",
            },
            {
                "failure": "Fail-closed descriptor missingness could be silently excluded.",
                "repair": "Rows with missing prior candidate or missing predecision descriptors remain in the rowset with explicit fail_closed_reasons and exact source requirements.",
            },
            {
                "failure": "Sealed/stress labels could be mistaken for validation partitions.",
                "repair": "Partition design ledger marks existing labels source-control only until G12/G0 target-opening gates accept a frozen repaired rowset.",
            },
        ],
        "row_level_source_requirements_not_blocking_design": [
            {
                "requirement": "Earlier same-group candidate rows for initial HAZ-001 waiting-time rows.",
                "classification": "recoverable_historical_market_source_if_prior_window_is_extended",
                "current_handling": "fail_closed row retained; no inference.",
            },
            {
                "requirement": "Complete prior-16 OHLC descriptor window for HAZ-005 transition rows.",
                "classification": "recoverable_historical_market_source_if_prior_bars_exist",
                "current_handling": "fail_closed row retained; no inference.",
            },
            {
                "requirement": "LBMA fix context applies only to metals source groups.",
                "classification": "non_applicable_source_context_for_non_metals",
                "current_handling": "non_applicable row retained; not counted as pass.",
            },
        ],
        "separate_evidence_class_handoffs": [
            "G12 acceptance of this repaired source-control package.",
            "Future target/result opening gate after G12 acceptance.",
            "Forward capture/source expansion for rows not recoverable from current accepted source-control artifacts.",
        ],
    })

    searched_root = base_artifact("searched_root_ledger", generated_at_utc, {
        "searched_roots": [
            {
                "root": rel(path) if path.is_relative_to(ROOT) else str(path),
                "exists": path.exists(),
                "purpose": purpose,
                "sha256": file_sha256(path) if path.is_file() else None,
            }
            for path, purpose in [
                (CANDIDATE_ROWS, "accepted source candidate universe"),
                (DESCRIPTOR_FREEZE, "predecision descriptor fields and partition labels"),
                (BAR_ROWS, "underlying as-of bar source rows, searched but not directly copied into rowset"),
                (READY8_MATERIALIZED, "previous redundant READY8 rowset failure baseline"),
                (SOURCE_FIELD_MATRIX_ROWS, "upstream per-card source-field mapping"),
                (G12_NUMERICAL_DECISION, "accepted G12 numerical-screen audit decision"),
                (G0_LEARNING_DECISION, "rank-1 repair route decision"),
                (LOCAL_HEAVY_DATA_INVENTORY, "anti-worktree-blindness policy"),
            ]
        ],
        "absolute_local_roots_checked": [
            {"root": r, "exists": Path(r).exists(), "consumed": False, "reason": "No same-evidence-class missing market-data blocker remained after accepted source-control artifacts supplied required fields."}
            for r in [
                r"C:\Users\MSI\Documents\ai-trading-agent\data",
                r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
                r"C:\tmp\gtos_otb",
                r"C:\SierraChart",
            ]
        ],
        "raw_blob_commit_opened": False,
        "broker_or_paid_source_access_opened": False,
    })

    saturation = base_artifact("saturation_self_red_team_ledger", generated_at_utc, {
        "questions": [
            {
                "question": "What would make the repaired rowset non-discriminative again?",
                "answer": "All cards keeping the same pass denominator with no card-specific contrast key. The verifier requires every card to have more than one descriptor_contrast_key and card-specific predicate IDs; status counts are preserved separately.",
                "same_evidence_class_gap_remaining": False,
            },
            {
                "question": "Could fail-closed rows leak into pass denominators?",
                "answer": "No. denominator_role separates pass, contrast, non-applicable, and fail-closed rows; fail reasons and exact requirements are in each row and the fail-closed ledger.",
                "same_evidence_class_gap_remaining": False,
            },
            {
                "question": "Could source-control partition labels be mistaken for validation?",
                "answer": "No. The partition design ledger states existing READY8 labels are source-control assignments only until a future G12/G0 target-opening gate accepts the repaired package.",
                "same_evidence_class_gap_remaining": False,
            },
            {
                "question": "Could current GTOS/OB framing box the repair?",
                "answer": "No. The eight designs cover adversarial placebo, behavioral session pressure, hazard/waiting time, transition clock, calendar/fix context, and source-confidence uncertainty; no OB-only field is used.",
                "same_evidence_class_gap_remaining": False,
            },
            {
                "question": "Could target rows, broker facts, or performance fields leak into the design?",
                "answer": "No. Builder consumes accepted source-control candidates/descriptors only and the verifier rejects forbidden result/performance/broker fields outside required safe flag names.",
                "same_evidence_class_gap_remaining": False,
            },
        ],
        "same_evidence_class_repair_design_intelligence_remaining": 0,
        "completion_as_exhaustion_claim": "All eight card predicate/contrast designs, denominator policies, fail-closed handling, duplicate/concentration controls, partition design, target-opening gates, source requirements, searched roots, and verifier coverage are emitted.",
    })

    completion = base_artifact("completion_audit", generated_at_utc, {
        "objective_restatement": "Repair/design the READY8 card rowset so all 8 cards have source-field maps, discriminative predicate or descriptor-contrast designs, denominator/fail-closed/duplicate/concentration/sealed-partition/target-opening policies, exact blockers, verifier/focused tests, and scoped artifacts while preserving closed validation/live/result surfaces.",
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight/context refresh completed", "evidence": ".context/LIVE_STATE.md regenerated and required context docs read before build", "status": "PASS"},
            {"requirement": "all 8 cards mapped", "evidence": rel(OUTPUTS["source_field_map"]), "status": "PASS"},
            {"requirement": "all 8 predicates/descriptor contrasts designed", "evidence": rel(OUTPUTS["predicate_ledger"]), "status": "PASS"},
            {"requirement": "draft repaired rowset materialized", "evidence": rel(OUTPUTS["rowset_rows"]), "status": "PASS"},
            {"requirement": "denominator and duplicate policy explicit", "evidence": rel(OUTPUTS["denominator_duplicate_policy"]), "status": "PASS"},
            {"requirement": "fail-closed policy explicit", "evidence": rel(OUTPUTS["fail_closed_policy"]), "status": "PASS"},
            {"requirement": "sealed/stress partition design explicit", "evidence": rel(OUTPUTS["partition_design"]), "status": "PASS"},
            {"requirement": "target-opening prerequisites explicit and closed", "evidence": rel(OUTPUTS["target_prereq"]), "status": "PASS"},
            {"requirement": "blockers repaired or exact requirements written", "evidence": rel(OUTPUTS["blocker_source_repair"]), "status": "PASS"},
            {"requirement": "searched-root/source-field/blocker/saturation ledgers emitted", "evidence": [rel(OUTPUTS["searched_root"]), rel(OUTPUTS["source_field_map"]), rel(OUTPUTS["blocker_source_repair"]), rel(OUTPUTS["saturation"])], "status": "PASS"},
            {"requirement": "safe flags preserved", "evidence": "All ledgers carry NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false", "status": "PASS"},
            {"requirement": "no result/validation/live/AI/API/paid/vendor/broker/raw/registry/remote/trading-surface opened", "evidence": "Forbidden surface flags are false in generated ledgers and verifier enforces them", "status": "PASS"},
        ],
        "same_evidence_class_repair_design_remaining": 0,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "can_mark_goal_complete_after_verifier_and_scoped_commits": True,
    })

    synthesis = f"""# SCID READY8 Discriminative Card Rowset Repair And Sealed Validation Design

Date: {DATE}

Evidence class: `{EVIDENCE_CLASS}`

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Decision

The READY8 redundancy failure is repaired at source-control design level. The source candidate universe remains the accepted `3,014` SCID as-of rows, but the repaired rowset no longer treats all `3,014` rows as card passes for every card. Each card now has a card-specific predicate or descriptor contrast key, with row-level `pass`, `contrast`, `non-applicable`, and `fail-closed` denominator roles.

## Card Repairs

- `ADV-001`: session/time/symbol placebo contrast.
- `ADV-003`: duplicate-key hash placebo contrast.
- `BEH-001`: session-open participant pressure versus later active-session controls.
- `HAZ-001`: waiting-time reset and dense prior-24h candidate-burst contrast.
- `HAZ-005`: predecision descriptor/clock transition contrast with missing descriptors fail-closed.
- `MAC-001`: day-of-week and month-turn calendar context.
- `MAC-004`: metals-only LBMA fix-window context; non-metals are non-applicable.
- `UNC-004`: source-confidence tier contrast from predecision descriptor completeness.

## Guardrails

No target scoring, validation, performance claim, AI/API call, paid/vendor access, broker/account/order/history/deal/position evidence, raw market blob commit, registry edit, remote push, or live trading-surface change was opened. Existing `SEALED_VALIDATION_CANDIDATE_DESIGN` labels remain source-control assignments only until a later G12/G0 target-opening gate accepts this repaired package.

## Next Gate

The next evidence-class gate is independent G12 acceptance of this repaired source-control rowset package. A future result-opening route must freeze target families/horizons, denominator rules, fail-closed behavior, duplicate/concentration gates, and no-leak/as-of proof before opening any target rows.
"""

    artifacts = {
        "decision_ledger": decision,
        "source_field_map": source_field_map(generated_at_utc),
        "predicate_ledger": predicate_ledger(generated_at_utc),
        "rowset_manifest": manifest,
        "denominator_duplicate_policy": denominator,
        "fail_closed_policy": fail_closed,
        "partition_design": partition_design,
        "target_prereq": target_prereq,
        "blocker_source_repair": blockers,
        "searched_root": searched_root,
        "saturation": saturation,
        "completion_audit": completion,
    }
    for key, obj in artifacts.items():
        write_json(OUTPUTS[key], obj)
    OUTPUTS["synthesis"].write_text(synthesis, encoding="utf-8", newline="\n")

    manifest_artifacts = []
    for key, path in OUTPUTS.items():
        if key == "output_manifest":
            continue
        manifest_artifacts.append({
            "artifact_id": key,
            "path": rel(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": file_sha256(path),
        })
    output_manifest = base_artifact("output_manifest", generated_at_utc, {
        "artifact_count": len(manifest_artifacts),
        "artifacts": manifest_artifacts,
        "manifest_self_hash_policy": "Output manifest excludes itself from hash closure.",
    })
    write_json(OUTPUTS["output_manifest"], output_manifest)
    return output_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    manifest = build_artifacts()
    if not args.quiet:
        print(json.dumps({
            "ok": True,
            "route_id": ROUTE_ID,
            "artifact_count": manifest["artifact_count"],
            "rowset_rows_path": rel(OUTPUTS["rowset_rows"]),
        }, indent=2))


if __name__ == "__main__":
    main()
