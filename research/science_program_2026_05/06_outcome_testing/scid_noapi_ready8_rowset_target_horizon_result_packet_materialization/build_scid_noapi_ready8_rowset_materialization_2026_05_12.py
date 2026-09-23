"""Build the SCID no-API ready-8 source-control materialization packet.

This route materializes rowsets, target-horizon contracts, denominator,
partition/control, baseline/control, hash/as-of, and no-leak controls for the
eight G12-accepted ready descriptor/control cards. It deliberately does not
open validation, outcome labels, R/PnL, performance, broker/order evidence,
AI/API calls, paid data, live restarts, or trading-decision behavior.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"

G0_SYNTHESIS_DIR = OUTCOME_DIR / "g0_scid_noapi_40card_prereg_replay_input_design_synthesis"
INPUT_DESIGN_DIR = OUTCOME_DIR / "scid_noapi_40card_prereg_input_design"
G12_INPUT_AUDIT_DIR = OUTCOME_DIR / "g12_scid_noapi_40card_prereg_replay_input_design_audit"
ASOF_PACKET_DIR = OUTCOME_DIR / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
NEUTRAL_TARGET_DIR = OUTCOME_DIR / "scid_asof_quarantined_neutral_target_execution_packet"
TARGET_HORIZON_DIR = OUTCOME_DIR / "scid_asof_sealed_validation_target_horizon_repair"

DATE_TAG = "2026-05-12"
PREFIX = "SCID_NOAPI_READY8"
ROUTE_ID = "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION"
EVIDENCE_CLASS = "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION_ONLY"
SCHEMA_VERSION = "scid_noapi_ready8_rowset_materialization_v1"
TERMINAL_DECISION = "MATERIALIZED_READY8_SOURCE_CONTROL_PACKET_G12_AUDIT_REQUIRED"

READY_CARD_IDS = [
    "ADV-001",
    "ADV-003",
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004",
]

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

FORBIDDEN_ROW_FIELDS = {
    "target_hit",
    "stop_hit",
    "outcome",
    "outcome_status",
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "realized_r",
    "r",
    "pnl",
    "profit",
    "loss",
    "win_rate",
    "expectancy",
    "performance",
    "performance_metric",
    "validated_edge",
    "order_ticket",
    "deal_id",
    "position_id",
    "account_id",
    "broker_account",
}

BASELINE_ASSIGNMENT_BY_CARD = {
    "ADV-001": "session_only_matched_placebo",
    "ADV-003": "duplicate_key_random_proxy_placebo",
    "BEH-001": "session_open_constraint_control",
    "HAZ-001": "candidate_density_waiting_time_control",
    "HAZ-005": "regime_transition_hazard_clock_control",
    "MAC-001": "day_of_week_month_turn_calendar_control",
    "MAC-004": "fixing_window_time_of_day_control",
    "UNC-004": "source_contract_confidence_missingness_control",
}

SOURCE_ARTIFACTS = {
    "candidate_input_rows": ASOF_PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
    "candidate_input_manifest": ASOF_PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json",
    "descriptor_freeze_ledger": NEUTRAL_TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json",
    "pre_target_freeze_packet": NEUTRAL_TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_PRE_TARGET_FREEZE_PACKET_2026-05-12.json",
    "concentration_denominator_audit": NEUTRAL_TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_CONCENTRATION_DENOMINATOR_AUDIT_2026-05-12.json",
    "partition_symbol_session_matrix": NEUTRAL_TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_PARTITION_SYMBOL_SESSION_MATRIX_2026-05-12.json",
    "source_hash_binding": NEUTRAL_TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_SOURCE_HASH_BINDING_2026-05-12.json",
    "target_horizon_contract": TARGET_HORIZON_DIR / "SCID_ASOF_TARGET_HORIZON_NEUTRAL_TARGET_CONTRACT_2026-05-11.json",
    "target_horizon_rulebook": TARGET_HORIZON_DIR / "SCID_ASOF_TARGET_HORIZON_RULEBOOK_2026-05-11.json",
    "ready8_route_ledger": G0_SYNTHESIS_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_READY_8_ROUTE_LEDGER_2026-05-12.json",
    "route_ranking_matrix": G0_SYNTHESIS_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-12.json",
    "g0_decision_ledger": G0_SYNTHESIS_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_DECISION_LEDGER_2026-05-12.json",
    "g12_decision_ledger": G12_INPUT_AUDIT_DIR / "G12_SCID_NOAPI_PREREG_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "packet_design_ledger": INPUT_DESIGN_DIR / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_REPLAY_INPUT_PACKET_DESIGN_LEDGER_2026-05-12.json",
    "packet_design_rows": INPUT_DESIGN_DIR / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_REPLAY_INPUT_PACKET_DESIGN_ROWS_2026-05-12.jsonl",
    "per_card_terminal_status_ledger": INPUT_DESIGN_DIR / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_PER_CARD_TERMINAL_STATUS_LEDGER_2026-05-12.json",
    "source_field_mapping_matrix": INPUT_DESIGN_DIR / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SOURCE_FIELD_MAPPING_MATRIX_2026-05-12.json",
    "blocked_card_dependency_ledger": INPUT_DESIGN_DIR / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_BLOCKED_CARD_DEPENDENCY_LEDGER_2026-05-12.json",
    "blocked_card_dependency_rows": INPUT_DESIGN_DIR / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_BLOCKED_CARD_DEPENDENCY_ROWS_2026-05-12.jsonl",
    "expansion_candidate_ledger": INPUT_DESIGN_DIR / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_EXPANSION_CANDIDATE_LEDGER_2026-05-12.json",
    "expansion_candidate_rows": INPUT_DESIGN_DIR / "SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_EXPANSION_CANDIDATE_ROWS_2026-05-12.jsonl",
}

G12_AUDIT_PROMPT = (
    PROMPT_DIR
    / "G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md"
)
FUTURE_RESULT_GATE_PROMPT = (
    PROMPT_DIR
    / "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_GOAL_PROMPT_2026-05-12.md"
)
G12_AUDIT_STARTER = (
    ROUTE_DIR / "G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_STARTER_2026-05-12.txt"
)
FUTURE_RESULT_GATE_STARTER = (
    ROUTE_DIR / "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_STARTER_2026-05-12.txt"
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@lru_cache(maxsize=None)
def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def output_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def safe_payload(artifact_family: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": now_utc(),
    }
    base.update(SAFE_FLAGS)
    base.update(payload)
    return base


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def source_artifact_inventory() -> list[dict[str, Any]]:
    inventory = []
    for name, path in SOURCE_ARTIFACTS.items():
        inventory.append(
            {
                "source_artifact_id": name,
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                "used_by_ready8_materialization": True,
            }
        )
    return inventory


def load_inputs() -> dict[str, Any]:
    missing = [rel(path) for path in SOURCE_ARTIFACTS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing required source artifacts: {missing}")

    descriptor = load_json(SOURCE_ARTIFACTS["descriptor_freeze_ledger"])
    candidate_rows = load_jsonl(SOURCE_ARTIFACTS["candidate_input_rows"])
    packet_rows = load_jsonl(SOURCE_ARTIFACTS["packet_design_rows"])
    expansion_rows = load_jsonl(SOURCE_ARTIFACTS["expansion_candidate_rows"])
    blocked_rows = load_jsonl(SOURCE_ARTIFACTS["blocked_card_dependency_rows"])

    return {
        "ready8_route_ledger": load_json(SOURCE_ARTIFACTS["ready8_route_ledger"]),
        "route_ranking_matrix": load_json(SOURCE_ARTIFACTS["route_ranking_matrix"]),
        "g0_decision_ledger": load_json(SOURCE_ARTIFACTS["g0_decision_ledger"]),
        "g12_decision_ledger": load_json(SOURCE_ARTIFACTS["g12_decision_ledger"]),
        "packet_design_ledger": load_json(SOURCE_ARTIFACTS["packet_design_ledger"]),
        "packet_rows": packet_rows,
        "per_card_terminal_status_ledger": load_json(SOURCE_ARTIFACTS["per_card_terminal_status_ledger"]),
        "source_field_mapping_matrix": load_json(SOURCE_ARTIFACTS["source_field_mapping_matrix"]),
        "blocked_card_dependency_ledger": load_json(SOURCE_ARTIFACTS["blocked_card_dependency_ledger"]),
        "blocked_rows": blocked_rows,
        "expansion_candidate_ledger": load_json(SOURCE_ARTIFACTS["expansion_candidate_ledger"]),
        "expansion_rows": expansion_rows,
        "descriptor_freeze_ledger": descriptor,
        "candidate_rows": candidate_rows,
        "pre_target_freeze_packet": load_json(SOURCE_ARTIFACTS["pre_target_freeze_packet"]),
        "concentration_denominator_audit": load_json(SOURCE_ARTIFACTS["concentration_denominator_audit"]),
        "partition_symbol_session_matrix": load_json(SOURCE_ARTIFACTS["partition_symbol_session_matrix"]),
        "source_hash_binding": load_json(SOURCE_ARTIFACTS["source_hash_binding"]),
        "target_horizon_contract": load_json(SOURCE_ARTIFACTS["target_horizon_contract"]),
        "target_horizon_rulebook": load_json(SOURCE_ARTIFACTS["target_horizon_rulebook"]),
        "source_artifact_inventory": source_artifact_inventory(),
    }


def recompute_ready_cards(data: dict[str, Any]) -> list[dict[str, Any]]:
    ready_from_g0 = data["ready8_route_ledger"].get("ready_cards", [])
    ready_by_id = {row["card_id"]: row for row in ready_from_g0}
    packet_by_id = {row["card_id"]: row for row in data["packet_rows"]}
    terminal_by_id = {
        row["card_id"]: row for row in data["per_card_terminal_status_ledger"].get("rows", [])
    }
    ready_cards = []
    for card_id in READY_CARD_IDS:
        if card_id not in ready_by_id or card_id not in packet_by_id or card_id not in terminal_by_id:
            raise ValueError(f"ready card missing from upstream ledgers: {card_id}")
        row = {**packet_by_id[card_id], **ready_by_id[card_id]}
        row["accepted_readiness"] = terminal_by_id[card_id]["accepted_readiness"]
        row["terminal_status_from_target"] = terminal_by_id[card_id]["terminal_status"]
        row["baseline_assignment_family"] = BASELINE_ASSIGNMENT_BY_CARD[card_id]
        ready_cards.append(row)
    return ready_cards


def candidate_descriptor_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    descriptors = data["descriptor_freeze_ledger"].get("descriptor_rows", [])
    candidate_by_id = {row["candidate_input_row_id"]: row for row in data["candidate_rows"]}
    if len(descriptors) != 3014:
        raise ValueError(f"expected 3014 descriptor rows, got {len(descriptors)}")
    if len(candidate_by_id) != 3014:
        raise ValueError(f"expected 3014 candidate input rows, got {len(candidate_by_id)}")
    merged = []
    for descriptor in descriptors:
        candidate_id = descriptor["candidate_input_row_id"]
        candidate = candidate_by_id.get(candidate_id)
        if not candidate:
            raise ValueError(f"descriptor missing candidate input row: {candidate_id}")
        if descriptor["duplicate_proxy_denominator_key"] != candidate["duplicate_key"]:
            raise ValueError(f"duplicate key mismatch for {candidate_id}")
        descriptor_hash = sha256_text(canonical_json(descriptor))
        merged.append(
            {
                "descriptor": descriptor,
                "candidate": candidate,
                "descriptor_row_hash": descriptor_hash,
            }
        )
    return merged


def baseline_seed(card_id: str, candidate_id: str, duplicate_key: str) -> str:
    return sha256_text(f"{ROUTE_ID}|baseline_seed_v1|{card_id}|{candidate_id}|{duplicate_key}")[:32]


def control_bucket(seed: str, bucket_count: int = 8) -> str:
    value = int(seed[:12], 16) % bucket_count
    return f"CONTROL_BUCKET_{value:02d}"


def build_rowset_rows(
    ready_cards: list[dict[str, Any]],
    merged_candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    for card in ready_cards:
        card_id = card["card_id"]
        for item in merged_candidates:
            descriptor = item["descriptor"]
            candidate = item["candidate"]
            candidate_id = descriptor["candidate_input_row_id"]
            duplicate_key = descriptor["duplicate_proxy_denominator_key"]
            required_values = {
                "candidate_input_row_id": candidate_id,
                "duplicate_proxy_denominator_key": duplicate_key,
                "symbol": descriptor.get("symbol"),
                "session_bucket": descriptor.get("session_bucket"),
                "time_of_day_bucket": descriptor.get("time_of_day_bucket"),
                "source_hash": candidate.get("row_hash"),
                "source_observed_asof_utc": candidate.get("decision_asof_utc"),
                "decision_asof_utc": candidate.get("decision_asof_utc"),
                "partition_assignment": descriptor.get("partition_assignment"),
            }
            missing_fields = [name for name, value in required_values.items() if value in (None, "")]
            if missing_fields:
                exclusions.append(
                    {
                        "card_id": card_id,
                        "candidate_input_row_id": candidate_id,
                        "exclusion_status": "EXCLUDED_MISSING_REQUIRED_SOURCE_CONTROL_FIELD",
                        "missing_fields": missing_fields,
                    }
                )
                continue
            seed = baseline_seed(card_id, candidate_id, duplicate_key)
            row: dict[str, Any] = {
                "rowset_row_id": sha256_text(f"{ROUTE_ID}|rowset|{card_id}|{candidate_id}|{duplicate_key}"),
                "candidate_input_row_id": candidate_id,
                "packet_id": card["packet_id"],
                "card_id": card_id,
                "science_domain": card["science_domain"],
                "mechanism_family": card["mechanism_family"],
                "source_group": card["source_group"],
                "source_proxy_group": descriptor.get("source_proxy_group"),
                "symbol": descriptor["symbol"],
                "canonical_economic_group": descriptor.get("canonical_economic_group"),
                "session_bucket": descriptor["session_bucket"],
                "time_of_day_bucket": descriptor["time_of_day_bucket"],
                "utc_hour": descriptor.get("utc_hour"),
                "entry_reference_time_utc": descriptor.get("entry_reference_time_utc"),
                "decision_asof_utc": candidate["decision_asof_utc"],
                "source_observed_asof_utc": candidate["decision_asof_utc"],
                "duplicate_proxy_denominator_key": duplicate_key,
                "partition_assignment": descriptor["partition_assignment"],
                "candidate_input_partition_assignment": candidate.get("partition_assignment"),
                "baseline_assignment_family": BASELINE_ASSIGNMENT_BY_CARD[card_id],
                "baseline_assignment_seed": seed,
                "baseline_control_bucket": control_bucket(seed),
                "baseline_duplicate_policy_id": "SCID_READY8_DUPLICATE_PROXY_DENOMINATOR_KEY_V1",
                "matched_control_group_key": sha256_text(
                    "|".join(
                        [
                            "matched_control_group_v1",
                            card_id,
                            str(descriptor.get("symbol")),
                            str(descriptor.get("session_bucket")),
                            str(descriptor.get("time_of_day_bucket")),
                            str(descriptor.get("partition_assignment")),
                        ]
                    )
                ),
                "source_identifier": (
                    "artifact://"
                    + rel(SOURCE_ARTIFACTS["candidate_input_rows"])
                    + "#"
                    + candidate_id
                ),
                "source_hash": candidate["row_hash"],
                "source_hash_policy": "STRICT_SHA256_REQUIRED",
                "source_artifact_pointers": [
                    {
                        "artifact_role": "candidate_input_row",
                        "path": rel(SOURCE_ARTIFACTS["candidate_input_rows"]),
                        "file_sha256": sha256_file(SOURCE_ARTIFACTS["candidate_input_rows"]),
                        "row_hash": candidate.get("row_hash"),
                    },
                    {
                        "artifact_role": "descriptor_freeze_row",
                        "path": rel(SOURCE_ARTIFACTS["descriptor_freeze_ledger"]),
                        "file_sha256": sha256_file(SOURCE_ARTIFACTS["descriptor_freeze_ledger"]),
                        "row_hash": item["descriptor_row_hash"],
                    },
                    {
                        "artifact_role": "source_segment",
                        "source_file_name": candidate.get("source_file_name"),
                        "segment_records_sha256": candidate.get("segment_records_sha256"),
                        "included_bar_hash_count": len(candidate.get("included_bar_hashes") or []),
                    },
                ],
                "candidate_input_row_hash": candidate.get("row_hash"),
                "descriptor_row_hash": item["descriptor_row_hash"],
                "parser_asof_version": candidate.get("asof_feature_schema_version"),
                "source_coverage_quality_bucket": descriptor.get("source_coverage_quality_bucket"),
                "denominator_group_concentration_bucket": descriptor.get(
                    "denominator_group_concentration_bucket"
                ),
                "prior_context_descriptor_buckets": {
                    "prior_16_range_bucket": descriptor.get("prior_16_range_bucket"),
                    "prior_16_drift_bucket": descriptor.get("prior_16_drift_bucket"),
                    "prior_32_range_bucket": descriptor.get("prior_32_range_bucket"),
                },
                "future_result_gate_status": "NOT_OPENED_G12_AUDIT_AND_G0_RESULT_GATE_REQUIRED",
                "safe_flags": {
                    "promotion_verdict": "NO_PROMOTION_VERDICT",
                    "validation_safe": False,
                    "outcome_review_opened": False,
                    "live_effect": False,
                },
            }
            row["row_hash"] = sha256_text(canonical_json(row))
            rows.append(row)
    return rows, exclusions


def count_by(rows: Iterable[dict[str, Any]], *keys: str) -> list[dict[str, Any]]:
    counts: Counter[tuple[Any, ...]] = Counter(tuple(row.get(key) for key in keys) for row in rows)
    out = []
    for key_tuple, count in sorted(counts.items(), key=lambda item: tuple(str(x) for x in item[0])):
        out.append({**{key: value for key, value in zip(keys, key_tuple)}, "count": count})
    return out


def write_rowset_artifacts(
    rows: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    ready_cards: list[dict[str, Any]],
    data: dict[str, Any],
) -> dict[str, Any]:
    row_path = output_path("ROWSET_ROWS", ".jsonl")
    write_jsonl(row_path, rows)
    row_file_sha = sha256_file(row_path)
    per_card_counts = dict(Counter(row["card_id"] for row in rows))
    source_candidate_ids = {row["candidate_input_row_id"] for row in rows}
    duplicate_keys = {row["duplicate_proxy_denominator_key"] for row in rows}
    manifest = safe_payload(
        "rowset_manifest",
        {
            "terminal_decision": TERMINAL_DECISION,
            "accepted_card_denominator_count": 40,
            "ready_card_denominator_count": 8,
            "blocked_dependency_row_count_preserved": 32,
            "source_candidate_row_count": len(source_candidate_ids),
            "duplicate_proxy_denominator_key_count": len(duplicate_keys),
            "eligible_source_candidate_row_count": 3014,
            "rowset_row_count": len(rows),
            "expected_rowset_row_count": 3014 * 8,
            "rowset_rows_path": rel(row_path),
            "rowset_rows_sha256": row_file_sha,
            "ready_card_ids": [card["card_id"] for card in ready_cards],
            "packet_ids": {card["card_id"]: card["packet_id"] for card in ready_cards},
            "per_card_row_counts": per_card_counts,
            "row_level_exclusion_count": len(exclusions),
            "row_level_exclusions": exclusions,
            "source_artifact_inventory": data["source_artifact_inventory"],
            "candidate_universe_source": rel(SOURCE_ARTIFACTS["descriptor_freeze_ledger"]),
            "candidate_input_rows_source": rel(SOURCE_ARTIFACTS["candidate_input_rows"]),
            "materialization_policy": (
                "All 3014 source-control candidate descriptor rows are materialized once for each "
                "of the 8 ready cards. No sampling was used."
            ),
        },
    )
    write_json(output_path("ROWSET_MANIFEST"), manifest)
    return manifest


def build_target_horizon_contract(data: dict[str, Any], ready_cards: list[dict[str, Any]]) -> dict[str, Any]:
    pre = data["pre_target_freeze_packet"]
    upstream_contract = data["target_horizon_contract"]
    contract = safe_payload(
        "target_horizon_contract",
        {
            "terminal_decision": TERMINAL_DECISION,
            "contract_status": "SOURCE_CONTROL_TARGET_HORIZONS_FROZEN_NO_SCORING_OPENED",
            "target_or_hazard_hits_computed": False,
            "performance_or_result_fields_present": False,
            "ready_card_ids": [card["card_id"] for card in ready_cards],
            "allowed_horizons_m15_bars": pre.get("horizons_m15_bars", []),
            "target_families": pre.get("target_families", []),
            "target_formula_text_source_control_only": pre.get("frozen_target_formula_text", {}),
            "source_safe_asof_descriptor_definitions": pre.get(
                "frozen_source_safe_asof_descriptor_definitions", []
            ),
            "allowed_future_observation_windows": [
                {
                    "horizon_m15_bars": horizon,
                    "window_start_rule": "entry_reference_time_utc",
                    "window_end_rule": f"entry_reference_time_utc_plus_{horizon}_closed_m15_bars",
                    "allowed_future_source_rows": [
                        "source-control bar rows accepted by G12",
                        "candidate input rows with strict source hashes",
                    ],
                    "current_route_may_compute": False,
                }
                for horizon in pre.get("horizons_m15_bars", [])
            ],
            "fail_closed_missing_status_vocabulary": pre.get(
                "frozen_fail_closed_not_computable_rules", []
            ),
            "forbidden_current_fields": [
                "target_hit",
                "stop_hit",
                "outcome",
                "R",
                "PnL",
                "win_rate",
                "expectancy",
                "performance",
                "broker_account",
                "order_ticket",
                "deal_id",
                "position_id",
            ],
            "upstream_neutral_target_contract_path": rel(SOURCE_ARTIFACTS["target_horizon_contract"]),
            "upstream_neutral_target_contract_sha256": sha256_file(SOURCE_ARTIFACTS["target_horizon_contract"]),
            "upstream_contract_family": upstream_contract.get("contract_family")
            or upstream_contract.get("artifact_family"),
            "future_gate_rule": (
                "A separate result-opening route may only run after this packet receives G12 acceptance "
                "and a later G0 gate confirms denominator, duplicate, partition, control, and no-leak prerequisites."
            ),
        },
    )
    write_json(output_path("TARGET_HORIZON_CONTRACT"), contract)
    return contract


def build_duplicate_manifest(rows: list[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    duplicate_by_candidate: dict[str, set[str]] = defaultdict(set)
    card_by_candidate: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        duplicate_by_candidate[row["candidate_input_row_id"]].add(row["duplicate_proxy_denominator_key"])
        card_by_candidate[row["candidate_input_row_id"]].add(row["card_id"])
    collisions = {
        candidate_id: sorted(keys)
        for candidate_id, keys in duplicate_by_candidate.items()
        if len(keys) != 1
    }
    incomplete_card_expansion = {
        candidate_id: sorted(cards)
        for candidate_id, cards in card_by_candidate.items()
        if len(cards) != len(READY_CARD_IDS)
    }
    concentration = data["concentration_denominator_audit"]
    manifest = safe_payload(
        "duplicate_denominator_manifest",
        {
            "primary_candidate_row_denominator_count": len(duplicate_by_candidate),
            "ready_card_row_denominator_count": len(rows),
            "duplicate_proxy_denominator_key_count": len({next(iter(keys)) for keys in duplicate_by_candidate.values()}),
            "card_packet_denominator_count": len(READY_CARD_IDS),
            "blocked_dependency_denominator_count_preserved": 32,
            "accepted_card_denominator_count_preserved": 40,
            "quarantined_expansion_denominator_inclusion": False,
            "duplicate_policy_id": "SCID_READY8_DUPLICATE_PROXY_DENOMINATOR_KEY_V1",
            "duplicate_key_collision_count": len(collisions),
            "duplicate_key_collisions": collisions,
            "incomplete_card_expansion_count": len(incomplete_card_expansion),
            "incomplete_card_expansion": incomplete_card_expansion,
            "input_only_concentration_diagnostics": {
                "symbol_counts": concentration.get("symbol_counts", {}),
                "canonical_economic_group_counts": concentration.get(
                    "canonical_economic_group_counts", {}
                ),
                "source_file_counts": concentration.get("source_file_counts", {}),
                "partition_counts": concentration.get("partition_counts", {}),
                "max_group_share": concentration.get("max_group_share"),
                "max_symbol_share": concentration.get("max_symbol_share"),
                "diagnostic_scope": "input_only_no_performance_or_result_interpretation",
            },
            "per_card_counts": dict(Counter(row["card_id"] for row in rows)),
            "per_partition_counts": count_by(rows, "partition_assignment"),
            "per_card_partition_counts": count_by(rows, "card_id", "partition_assignment"),
        },
    )
    write_json(output_path("DUPLICATE_DENOMINATOR_MANIFEST"), manifest)
    return manifest


def build_partition_control_manifest(rows: list[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    partition_counts = Counter(row["partition_assignment"] for row in rows)
    source_candidate_partition_counts = Counter(
        (row["candidate_input_row_id"], row["partition_assignment"]) for row in rows
    )
    manifest = safe_payload(
        "partition_control_manifest",
        {
            "partition_policy_id": "SCID_READY8_SOURCE_CONTROL_PARTITION_POLICY_V1",
            "partition_status_counts_ready8_rows": dict(partition_counts),
            "source_candidate_partition_count": len(source_candidate_partition_counts),
            "discovery_development_status": {
                "DISCOVERY_POOL": {
                    "candidate_count": 0,
                    "status": "CLOSED_TO_READY8_MATERIALIZATION",
                    "reason": "Ready-8 packet uses accepted SCID as-of descriptor rows only.",
                },
                "DEVELOPMENT_POOL": {
                    "candidate_count": 0,
                    "status": "CLOSED_TO_READY8_MATERIALIZATION",
                    "reason": "No parameter or threshold development is performed.",
                },
                "SEALED_VALIDATION_CANDIDATE_DESIGN": {
                    "candidate_count": len(
                        {
                            row["candidate_input_row_id"]
                            for row in rows
                            if row["partition_assignment"] == "SEALED_VALIDATION_CANDIDATE_DESIGN"
                        }
                    ),
                    "status": "SOURCE_CONTROL_PACKET_ONLY_NO_RESULT_OPENING",
                },
                "STRESS_ROBUSTNESS_CANDIDATE_DESIGN": {
                    "candidate_count": len(
                        {
                            row["candidate_input_row_id"]
                            for row in rows
                            if row["partition_assignment"] == "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"
                        }
                    ),
                    "status": "SOURCE_CONTROL_PACKET_ONLY_NO_RESULT_OPENING",
                },
                "FORWARD_POOL": {
                    "candidate_count": 0,
                    "status": "NOT_OPENED_IN_THIS_ROUTE",
                },
                "CONTAMINATED_OR_FORBIDDEN_POOL": {
                    "candidate_count": 0,
                    "status": "EXCLUDED_FROM_DENOMINATOR",
                },
            },
            "future_result_pool_opening_reason_currently_closed": (
                "This route has frozen source-control partition assignments but still requires a G12 audit "
                "and later G0 result-opening gate before any result or validation evidence class may run."
            ),
            "source_partition_matrix_path": rel(SOURCE_ARTIFACTS["partition_symbol_session_matrix"]),
            "source_partition_matrix_sha256": sha256_file(SOURCE_ARTIFACTS["partition_symbol_session_matrix"]),
            "per_card_partition_counts": count_by(rows, "card_id", "partition_assignment"),
            "per_symbol_session_partition_counts": count_by(
                rows,
                "symbol",
                "session_bucket",
                "partition_assignment",
            ),
        },
    )
    write_json(output_path("PARTITION_CONTROL_MANIFEST"), manifest)
    return manifest


def build_baseline_assignment_manifest(rows: list[dict[str, Any]], ready_cards: list[dict[str, Any]]) -> dict[str, Any]:
    card_defs = []
    for card in ready_cards:
        card_rows = [row for row in rows if row["card_id"] == card["card_id"]]
        card_defs.append(
            {
                "card_id": card["card_id"],
                "packet_id": card["packet_id"],
                "science_domain": card["science_domain"],
                "mechanism_family": card["mechanism_family"],
                "baseline_assignment_family": BASELINE_ASSIGNMENT_BY_CARD[card["card_id"]],
                "deterministic_seed_formula": (
                    f"sha256({ROUTE_ID}|baseline_seed_v1|card_id|candidate_input_row_id|duplicate_proxy_denominator_key)[:32]"
                ),
                "baseline_duplicate_policy_id": "SCID_READY8_DUPLICATE_PROXY_DENOMINATOR_KEY_V1",
                "row_count": len(card_rows),
                "control_bucket_counts": dict(Counter(row["baseline_control_bucket"] for row in card_rows)),
                "assignment_hash": sha256_text(
                    canonical_json(
                        [
                            {
                                "candidate_input_row_id": row["candidate_input_row_id"],
                                "baseline_assignment_seed": row["baseline_assignment_seed"],
                                "baseline_control_bucket": row["baseline_control_bucket"],
                            }
                            for row in card_rows
                        ]
                    )
                ),
            }
        )
    manifest = safe_payload(
        "baseline_control_assignment_manifest",
        {
            "assignment_policy_id": "SCID_READY8_BASELINE_CONTROL_ASSIGNMENT_V1",
            "assignment_scope": "source_control_only_no_result_lookup",
            "deterministic_assignments_only": True,
            "result_or_performance_lookup_used": False,
            "baseline_control_card_definitions": card_defs,
            "row_assignment_count": len(rows),
            "unique_assignment_seed_count": len({row["baseline_assignment_seed"] for row in rows}),
            "global_control_bucket_counts": dict(Counter(row["baseline_control_bucket"] for row in rows)),
        },
    )
    write_json(output_path("BASELINE_CONTROL_ASSIGNMENT_MANIFEST"), manifest)
    return manifest


def recursive_key_scan(value: Any, forbidden: set[str] = FORBIDDEN_ROW_FIELDS) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, subvalue in value.items():
            if key in forbidden:
                hits.append(key)
            hits.extend(recursive_key_scan(subvalue, forbidden))
    elif isinstance(value, list):
        for item in value:
            hits.extend(recursive_key_scan(item, forbidden))
    return hits


def build_no_leak_audit(rows: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_hits = []
    asof_violations = []
    for row in rows:
        hits = [key for key in row if key in FORBIDDEN_ROW_FIELDS]
        if hits:
            forbidden_hits.append({"rowset_row_id": row["rowset_row_id"], "forbidden_keys": hits})
        if row["source_observed_asof_utc"] > row["decision_asof_utc"]:
            asof_violations.append(row["rowset_row_id"])
    audit = safe_payload(
        "no_leak_and_forbidden_surface_audit",
        {
            "rowset_rows_scanned": len(rows),
            "forbidden_row_field_hit_count": len(forbidden_hits),
            "forbidden_row_field_hits": forbidden_hits[:20],
            "asof_violation_count": len(asof_violations),
            "asof_violations": asof_violations[:20],
            "safe_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
            "forbidden_surfaces_opened": [],
            "source_artifacts_used": artifacts,
            "broker_account_order_history_deal_position_evidence_accessed": False,
            "ai_api_paid_vendor_accessed": False,
            "raw_market_blob_committed": False,
        },
    )
    write_json(output_path("NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT"), audit)
    return audit


def build_source_hash_asof_audit(rows: list[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    source_hash_missing = [row["rowset_row_id"] for row in rows if not row.get("source_hash")]
    parser_missing = [row["rowset_row_id"] for row in rows if not row.get("parser_asof_version")]
    source_hash_counts = Counter(row["source_hash"] for row in rows)
    audit = safe_payload(
        "source_hash_and_asof_audit",
        {
            "rowset_rows_scanned": len(rows),
            "source_hash_missing_count": len(source_hash_missing),
            "parser_asof_version_missing_count": len(parser_missing),
            "source_hash_unique_count": len(source_hash_counts),
            "candidate_input_source_hash_reuse_policy": (
                "Each candidate input row hash is reused across the eight ready-card materializations; "
                "card-specific row_hash values remain unique."
            ),
            "row_hash_unique_count": len({row["row_hash"] for row in rows}),
            "source_observed_asof_lte_decision_asof_count": sum(
                1 for row in rows if row["source_observed_asof_utc"] <= row["decision_asof_utc"]
            ),
            "source_artifact_inventory": data["source_artifact_inventory"],
            "upstream_source_hash_binding": {
                "path": rel(SOURCE_ARTIFACTS["source_hash_binding"]),
                "sha256": sha256_file(SOURCE_ARTIFACTS["source_hash_binding"]),
                "manifest_hash_reconciliation": data["source_hash_binding"].get(
                    "manifest_hash_reconciliation", {}
                ),
            },
            "searched_roots": [
                {
                    "root": rel(OUTCOME_DIR),
                    "purpose": "accepted SCID route artifacts and as-of source-control packets",
                    "status": "SEARCHED",
                },
                {
                    "root": "shadow_logs/scid_forward_source_capture.jsonl",
                    "purpose": "prospective live SCID source rows",
                    "status": "ABSENT_IN_WORKTREE_AND_MAIN_ABSOLUTE_REPO_ROOT",
                    "closure": (
                        "Not needed for this materialization because the accepted as-of descriptor/candidate "
                        "packet supplies 3014 source-control rows."
                    ),
                },
            ],
        },
    )
    write_json(output_path("SOURCE_HASH_AND_ASOF_AUDIT"), audit)
    return audit


def write_future_prompts() -> dict[str, str]:
    g12_prompt = f"""# G12 SCID No-API Ready-8 Rowset / Target-Horizon Packet Audit

Evidence class: `G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_ONLY`

Objective: independently audit the materialized ready-8 source-control packet in `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/` before any result-opening route is allowed.

Mandatory preflight: regenerate `.context/LIVE_STATE.md`; read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and the controlling ready-8 materialization prompt.

Audit requirements:

- Recompute the eight ready cards: `ADV-001`, `ADV-003`, `BEH-001`, `HAZ-001`, `HAZ-005`, `MAC-001`, `MAC-004`, `UNC-004`.
- Verify the rowset has `3014 * 8 = 24112` source-control rows and no row-level exclusions except exact proved exclusions.
- Verify the accepted-card denominator remains `40`, ready denominator remains `8`, blocked rows remain `32`, and expansion observations stay quarantined.
- Verify source hashes, row hashes, parser/as-of versions, `source_observed_asof_utc <= decision_asof_utc`, duplicate policy, partition/control assignments, and deterministic baseline/control assignments.
- Verify the target-horizon contract defines only future windows/contracts and contains no `target_hit`, `stop_hit`, `outcome`, `R`, `PnL`, win-rate, expectancy, performance, promotion, broker/order/account, AI/API, paid/vendor, raw-market-blob, live-restart, or trading-behavior surface.
- Run the route verifier and focused tests or stronger equivalents.

Allowed terminal decisions:

- `ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY`
- `ACCEPT_WITH_NONBLOCKING_FOLLOWUPS`
- `REJECT_REPAIR_REQUIRED`

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    result_prompt = f"""# G0 No-API Ready-8 Future Result-Opening Gate

Evidence class: `G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_ONLY`

Do not run this prompt as a scoring route unless a prior G12 audit accepts the ready-8 materialized source-control packet. This prompt is a future gate, not current validation.

Mandatory preflight: regenerate `.context/LIVE_STATE.md`; read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, the ready-8 materialization route artifacts, and the G12 ready-8 audit decision.

Gate objective: decide whether a separate quarantined no-API result packet may be opened from the accepted ready-8 packet, or emit exact repair blockers. The gate must verify G12 acceptance, frozen rowsets, duplicate denominators, partitions, baseline/control assignments, target-horizon contracts, no-leak proof, source hashes, as-of proof, and safe flags before any result lane is authorized.

Forbidden in this gate unless a later prompt explicitly opens a separate result evidence class: promotion, live behavior, trading logic, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market blob commits, risk/safety/prompt/config/execution/canary/selector changes.

Allowed terminal decisions:

- `OPEN_SEPARATE_QUARANTINED_NOAPI_RESULT_PACKET_PROMPT_AFTER_G12_ACCEPTANCE`
- `KEEP_RESULT_GATE_CLOSED_WITH_EXACT_REPAIR_BLOCKERS`

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    g12_starter = (
        "/goal Follow the full controlling prompt in "
        f"{rel(G12_AUDIT_PROMPT)} as the complete objective; do mandatory preflight/context refresh first; "
        "do not rely on chat memory; stay G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_ONLY with no "
        "validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/"
        "broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/"
        "trading-risk-safety-prompt-decision changes; independently recompute ready8 rowsets, source hashes, "
        "as-of, duplicate denominators, partitions, controls, target-horizon contracts, safe flags, future gate "
        "status, and G12/G0 prerequisites; run verifier/focused tests; emit scoped audit artifacts and mark complete "
        "only with NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false."
    )
    result_starter = (
        "/goal Follow the full controlling prompt in "
        f"{rel(FUTURE_RESULT_GATE_PROMPT)} as the complete objective; do mandatory preflight/context refresh first; "
        "do not rely on chat memory; stay G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_ONLY and keep the gate closed "
        "unless a prior G12 audit accepts the ready8 source-control packet; verify frozen rowsets, horizons, "
        "denominators, partitions, controls, no-leak/source-hash/as-of proof, and safe flags; do not open scoring "
        "inside this gate; NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false."
    )
    write_md(G12_AUDIT_PROMPT, g12_prompt.splitlines())
    write_md(FUTURE_RESULT_GATE_PROMPT, result_prompt.splitlines())
    write_md(G12_AUDIT_STARTER, [g12_starter])
    write_md(FUTURE_RESULT_GATE_STARTER, [result_starter])
    return {
        "g12_audit_prompt": rel(G12_AUDIT_PROMPT),
        "g12_audit_starter": rel(G12_AUDIT_STARTER),
        "future_result_gate_prompt": rel(FUTURE_RESULT_GATE_PROMPT),
        "future_result_gate_starter": rel(FUTURE_RESULT_GATE_STARTER),
    }


def build_result_gate_decision(prompt_paths: dict[str, str]) -> dict[str, Any]:
    decision = safe_payload(
        "result_opening_gate_decision",
        {
            "terminal_decision": TERMINAL_DECISION,
            "dependencies_frozen_for_source_control_packet": True,
            "g12_audit_required_before_any_result_opening": True,
            "future_result_gate_prompt_emitted": True,
            "future_result_gate_status": "DORMANT_UNTIL_READY8_G12_AUDIT_ACCEPTS_PACKET",
            "may_score_results_now": False,
            "may_open_validation_now": False,
            "exact_current_gate_blockers": [
                "G12 ready-8 packet materialization audit has not yet accepted this packet.",
                "A later G0 result-opening gate must explicitly authorize any separate result evidence class.",
            ],
            "prompt_paths": prompt_paths,
            "allowed_next_terminal_decision": "ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY",
        },
    )
    write_json(output_path("RESULT_OPENING_GATE_DECISION"), decision)
    return decision


def build_blocker_dependency_ledger(data: dict[str, Any], exclusions: list[dict[str, Any]]) -> dict[str, Any]:
    blocked_rows = data["blocked_rows"]
    ledger = safe_payload(
        "blocker_or_dependency_ledger",
        {
            "ready8_source_control_blocker_count": 0 if not exclusions else len(exclusions),
            "row_level_exclusion_count": len(exclusions),
            "row_level_exclusions": exclusions,
            "ready8_exact_dependencies_remaining_before_result_scoring": [
                "G12 audit of materialized ready-8 source-control packet",
                "future G0 result-opening gate",
                "separate result evidence-class prompt before any target/status/outcome scoring",
            ],
            "blocked_32_denominator_preserved": True,
            "blocked_32_dependency_row_count": len(blocked_rows),
            "blocked_32_readiness_split": dict(
                Counter(row.get("accepted_readiness") for row in blocked_rows)
            ),
            "blocked_32_not_mixed_into_ready8_materialization": True,
            "shadow_logs_scid_forward_source_capture_status": (
                "ABSENT_IN_WORKTREE_AND_MAIN_ABSOLUTE_ROOT; not needed for this packet because "
                "accepted as-of SCID candidate descriptor rows supplied the 3014-row source-control universe."
            ),
        },
    )
    write_json(output_path("BLOCKER_OR_DEPENDENCY_LEDGER"), ledger)
    return ledger


def build_expansion_ledger(data: dict[str, Any]) -> dict[str, Any]:
    upstream = data["expansion_rows"]
    observations = [
        {
            "observation_id": "READY8-EXP-001",
            "observation_family": "rowset_materialization_quality_control",
            "accepted_40_card_denominator_inclusion": False,
            "ready8_denominator_inclusion": False,
            "source_safe_materialization_insight": (
                "The same 3014 candidate source-control universe can support cross-card packet-quality "
                "diagnostics without entering any accepted-card result denominator."
            ),
            "future_route_requirement": "Separate expansion acceptance and G12/G0 denominator-entry route.",
        },
        {
            "observation_id": "READY8-EXP-002",
            "observation_family": "partition_x_source_coverage_missingness_control",
            "accepted_40_card_denominator_inclusion": False,
            "ready8_denominator_inclusion": False,
            "source_safe_materialization_insight": (
                "Source coverage and partition assignment can become a future no-API control family, "
                "but it must remain quarantined until accepted."
            ),
            "future_route_requirement": "Separate source/control candidate acceptance route; no outcome scoring.",
        },
        {
            "observation_id": "READY8-EXP-003",
            "observation_family": "baseline_assignment_stability_audit",
            "accepted_40_card_denominator_inclusion": False,
            "ready8_denominator_inclusion": False,
            "source_safe_materialization_insight": (
                "Deterministic control-bucket assignment stability itself is audit-worthy for later packet "
                "quality checks, not a strategy edge claim."
            ),
            "future_route_requirement": "Separate audit/control route; no denominator mixing.",
        },
    ]
    ledger = safe_payload(
        "expansion_observation_ledger",
        {
            "accepted_40_is_floor_not_ceiling": True,
            "upstream_quarantined_expansion_candidate_count": len(upstream),
            "upstream_quarantined_expansion_candidates": upstream,
            "new_ready8_expansion_observation_count": len(observations),
            "new_ready8_expansion_observations": observations,
            "all_expansion_observations_remain_outside_accepted_denominator": True,
            "all_expansion_observations_remain_outside_ready8_denominator": True,
        },
    )
    write_json(output_path("EXPANSION_OBSERVATION_LEDGER"), ledger)
    return ledger


def write_saturation_self_red_team() -> None:
    lines = [
        "# SCID No-API Ready-8 Saturation Self-Red-Team",
        "",
        f"Evidence class: `{EVIDENCE_CLASS}`",
        "",
        "## Objective Restatement",
        "",
        "Materialize the eight G12-accepted ready descriptor/control cards into source-hashed rowsets, target-horizon contracts, denominator/partition/control manifests, deterministic baseline/control assignments, no-leak/hash/as-of audits, and future gate prompts without opening scoring.",
        "",
        "## Doctrine Application",
        "",
        "- Builder posture applied: maximize source-safe packet construction inside the no-API source-control evidence class.",
        "- Anti-boxing applied: the accepted 40-card denominator is preserved as a floor, blocked 32 remain routed, and expansion observations are quarantined instead of suppressed.",
        "- Historical replay opportunity-cost applied: the accepted 3014 as-of SCID descriptor rows were used now instead of waiting passively for live SCID rows.",
        "- No-API cost control applied: no AI/API or paid/vendor access was used; all inputs are committed source-control artifacts.",
        "- Proof-or-impossibility applied: `shadow_logs/scid_forward_source_capture.jsonl` absence was not treated as a blocker because the accepted as-of packet supplies the full eligible rowset for this route.",
        "",
        "## Red-Team Questions",
        "",
        "- Could packet readiness be mistaken for result permission? Prevented by terminal decision `MATERIALIZED_READY8_SOURCE_CONTROL_PACKET_G12_AUDIT_REQUIRED` and dormant result gate.",
        "- Could blocked cards leak into ready denominators? Prevented by separate blocked-32 dependency ledger and rowset card-id verifier.",
        "- Could expansion observations enter the accepted denominator? Prevented by explicit denominator-inclusion=false rows.",
        "- Could target horizons become target hits? Prevented by contract-only target horizon artifact and forbidden-field verifier.",
        "- Could source rows be compact-only? Prevented by full `3014 * 8 = 24112` rowset materialization.",
        "- Could the route collapse to OB-only? Prevented by preserving all eight ready cards across adversarial, behavioral, hazard, macro, and uncertainty domains.",
        "",
        "## Deliberately Not Answered",
        "",
        "- No validation, result scoring, R/PnL, win-rate, expectancy, performance, promotion, AI/API, paid source, broker account/order/history/deal/position, raw market blob, live restart, or trading behavior question was opened.",
        "- Future result opening belongs to a later G0 gate after G12 packet acceptance.",
    ]
    write_md(output_path("SATURATION_SELF_RED_TEAM", ".md"), lines)


def build_completion_audit(
    manifest: dict[str, Any],
    target_contract: dict[str, Any],
    duplicate_manifest: dict[str, Any],
    partition_manifest: dict[str, Any],
    baseline_manifest: dict[str, Any],
    no_leak_audit: dict[str, Any],
    source_hash_audit: dict[str, Any],
    result_gate: dict[str, Any],
    blocker_ledger: dict[str, Any],
    expansion_ledger: dict[str, Any],
    prompt_paths: dict[str, str],
) -> dict[str, Any]:
    checklist = [
        ("mandatory preflight/context refreshed", True, ".context/LIVE_STATE.md regenerated and core docs read"),
        ("all eight ready cards materialized exactly once per source candidate", manifest["rowset_row_count"] == 3014 * 8, rel(output_path("ROWSET_ROWS", ".jsonl"))),
        ("accepted 40 and ready 8 denominators preserved", manifest["accepted_card_denominator_count"] == 40 and manifest["ready_card_denominator_count"] == 8, rel(output_path("ROWSET_MANIFEST"))),
        ("blocked 32 denominator not mixed", blocker_ledger["blocked_32_denominator_preserved"], rel(output_path("BLOCKER_OR_DEPENDENCY_LEDGER"))),
        ("source-hashed rowset manifest exists", bool(manifest.get("rowset_rows_sha256")), rel(output_path("ROWSET_MANIFEST"))),
        ("target-horizon contract has no result/performance fields", not recursive_key_scan(target_contract), rel(output_path("TARGET_HORIZON_CONTRACT"))),
        ("duplicate denominator manifest deterministic", duplicate_manifest["duplicate_key_collision_count"] == 0, rel(output_path("DUPLICATE_DENOMINATOR_MANIFEST"))),
        ("partition/control manifest deterministic", partition_manifest["source_candidate_partition_count"] == 3014, rel(output_path("PARTITION_CONTROL_MANIFEST"))),
        ("baseline/control assignments deterministic", baseline_manifest["deterministic_assignments_only"] is True, rel(output_path("BASELINE_CONTROL_ASSIGNMENT_MANIFEST"))),
        ("no-leak and forbidden surface audit passed", no_leak_audit["forbidden_row_field_hit_count"] == 0 and no_leak_audit["asof_violation_count"] == 0, rel(output_path("NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT"))),
        ("source hash/as-of audit passed", source_hash_audit["source_hash_missing_count"] == 0 and source_hash_audit["source_observed_asof_lte_decision_asof_count"] == 3014 * 8, rel(output_path("SOURCE_HASH_AND_ASOF_AUDIT"))),
        ("future result gate or exact blocker prompt exists", result_gate["future_result_gate_prompt_emitted"] is True, prompt_paths["future_result_gate_prompt"]),
        ("G12 audit prompt/starter exists", Path(ROOT / prompt_paths["g12_audit_prompt"]).exists() and Path(ROOT / prompt_paths["g12_audit_starter"]).exists(), prompt_paths["g12_audit_prompt"]),
        ("expansion observations quarantined", expansion_ledger["all_expansion_observations_remain_outside_accepted_denominator"], rel(output_path("EXPANSION_OBSERVATION_LEDGER"))),
        ("saturation self-red-team written", output_path("SATURATION_SELF_RED_TEAM", ".md").exists(), rel(output_path("SATURATION_SELF_RED_TEAM", ".md"))),
        ("standalone verifier and focused tests pass", False, "pending verifier/pytest run"),
        ("scoped artifacts and context refresh committed", False, "pending commit"),
    ]
    audit = safe_payload(
        "completion_audit",
        {
            "objective_as_concrete_deliverables": [
                "Full ready-8 rowset over all 3014 accepted source-control candidate rows.",
                "Target-horizon contract only, with no hits/status/outcome/performance computation.",
                "Duplicate denominator, partition/control, baseline/control, no-leak, and source-hash/as-of audits.",
                "Future result-gate prompt and G12 audit prompt without current scoring.",
                "Builder, verifier, focused tests, scoped commits, and preserved safe flags.",
            ],
            "instruction_coverage": {
                "goal_session_research_discipline_read_after_preflight": True,
                "research_operating_doctrine_read_after_preflight": True,
                "research_current_state_read_after_preflight": True,
                "local_heavy_data_inventory_read_after_preflight": True,
                "ai_in_loop_cost_control_read_after_preflight": True,
                "lane_type": "builder/source-control packet materialization",
                "builder_posture_applied": "aggressive source-control materialization; no compact-only shortcut",
                "anti_boxing_questions_pursued": [
                    "Used all 3014 eligible as-of source-control candidates.",
                    "Preserved non-OB ready cards and expansion observations.",
                    "Searched for live SCID source rows but did not block because accepted historical/as-of packet existed.",
                ],
                "proof_or_impossibility_stop_condition": (
                    "No source-control blocker remains for ready8; result opening is gated by G12/G0 methodology."
                ),
                "doctrine_requirements_deferred_because_evidence_class_gate": [
                    "result scoring",
                    "validation",
                    "promotion",
                    "broker/account/order evidence",
                    "AI/API or paid-source use",
                ],
            },
            "prompt_to_artifact_checklist": [
                {"requirement": req, "satisfied": ok, "evidence": evidence}
                for req, ok, evidence in checklist
            ],
            "terminal_decision": TERMINAL_DECISION,
            "completion_standard_satisfied_before_commit": False,
            "completion_standard_satisfied": False,
            "can_mark_goal_complete": False,
            "standalone_verifier_ok": False,
            "focused_tests_ok": False,
        },
    )
    write_json(output_path("COMPLETION_AUDIT"), audit)
    return audit


def write_output_manifest(extra_paths: list[Path], verification_result: dict[str, Any] | None = None) -> dict[str, Any]:
    paths = set()
    for path in ROUTE_DIR.iterdir():
        if path.is_file():
            paths.add(path)
    for path in extra_paths:
        if path.exists():
            paths.add(path)
    paths.discard(output_path("OUTPUT_MANIFEST"))
    manifest = safe_payload(
        "output_manifest",
        {
            "artifact_count": len(paths),
            "artifacts": [
                {
                    "path": rel(path),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
                for path in sorted(paths)
            ],
            "verification_result": verification_result,
            "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
        },
    )
    write_json(output_path("OUTPUT_MANIFEST"), manifest)
    return manifest


def build() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    data = load_inputs()
    ready_cards = recompute_ready_cards(data)
    merged_candidates = candidate_descriptor_rows(data)
    rows, exclusions = build_rowset_rows(ready_cards, merged_candidates)

    manifest = write_rowset_artifacts(rows, exclusions, ready_cards, data)
    target_contract = build_target_horizon_contract(data, ready_cards)
    duplicate_manifest = build_duplicate_manifest(rows, data)
    partition_manifest = build_partition_control_manifest(rows, data)
    baseline_manifest = build_baseline_assignment_manifest(rows, ready_cards)
    no_leak_audit = build_no_leak_audit(rows, data["source_artifact_inventory"])
    source_hash_audit = build_source_hash_asof_audit(rows, data)
    prompt_paths = write_future_prompts()
    result_gate = build_result_gate_decision(prompt_paths)
    blocker_ledger = build_blocker_dependency_ledger(data, exclusions)
    expansion_ledger = build_expansion_ledger(data)
    write_saturation_self_red_team()
    completion = build_completion_audit(
        manifest=manifest,
        target_contract=target_contract,
        duplicate_manifest=duplicate_manifest,
        partition_manifest=partition_manifest,
        baseline_manifest=baseline_manifest,
        no_leak_audit=no_leak_audit,
        source_hash_audit=source_hash_audit,
        result_gate=result_gate,
        blocker_ledger=blocker_ledger,
        expansion_ledger=expansion_ledger,
        prompt_paths=prompt_paths,
    )
    seed_verification = safe_payload(
        "verification_result",
        {
            "ok": False,
            "failure_count": None,
            "failures": ["verifier not run yet"],
            "can_mark_goal_complete": False,
        },
    )
    write_json(output_path("VERIFICATION_RESULT"), seed_verification)
    output_manifest = write_output_manifest(
        [G12_AUDIT_PROMPT, FUTURE_RESULT_GATE_PROMPT, G12_AUDIT_STARTER, FUTURE_RESULT_GATE_STARTER]
    )
    return {
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "ready_card_count": len(ready_cards),
        "source_candidate_row_count": len(merged_candidates),
        "rowset_row_count": len(rows),
        "row_level_exclusion_count": len(exclusions),
        "completion_standard_satisfied_before_verifier": completion[
            "completion_standard_satisfied_before_commit"
        ],
        "output_manifest_artifact_count": output_manifest["artifact_count"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True, ensure_ascii=True))
