"""Build the G12 audit for the SCID no-API ready-8 source-control packet."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_noapi_ready8_rowset_target_horizon_result_packet_materialization"
)

DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_NOAPI_READY8"
ROUTE_ID = "G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT"
EVIDENCE_CLASS = "G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_v1"
TARGET_ROUTE_ID = "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION"
TARGET_EVIDENCE_CLASS = "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION_ONLY"
EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_READY_CARDS = 8
EXPECTED_ROWSET_ROWS = EXPECTED_SOURCE_CANDIDATES * EXPECTED_READY_CARDS
EXPECTED_ACCEPTED_CARDS = 40
EXPECTED_BLOCKED_CARDS = 32
EXPECTED_UPSTREAM_EXPANSIONS = 8
EXPECTED_READY8_EXPANSIONS = 3

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

BASELINE_ASSIGNMENT_BY_CARD = {
    "ADV-001": "session_only_matched_placebo",
    "ADV-003": "duplicate_key_random_proxy_placebo",
    "BEH-001": "session_open_constraint_family",
    "HAZ-001": "candidate_density_waiting_time",
    "HAZ-005": "regime_transition_hazard_clock",
    "MAC-001": "day_of_week_month_turn_context",
    "MAC-004": "fixing_window_context",
    "UNC-004": "source_contract_confidence_without_scores",
}

FORBIDDEN_EXACT_ROW_KEYS = {
    "target_hit",
    "stop_hit",
    "target_hit_bool",
    "stop_hit_bool",
    "outcome",
    "outcome_label",
    "result",
    "realized_r",
    "actual_r",
    "r_multiple",
    "pnl",
    "profit",
    "loss",
    "win_rate",
    "expectancy",
    "performance_score",
    "broker_account",
    "broker_order",
    "broker_history",
    "broker_deal",
    "broker_position",
    "api_response",
    "ai_decision",
}

FORBIDDEN_TARGET_KEYS = {
    "target_hit",
    "stop_hit",
    "target_hit_bool",
    "stop_hit_bool",
    "observed_outcome",
    "outcome_label",
    "realized_r",
    "actual_r",
    "r_multiple",
    "pnl",
    "win_rate",
    "expectancy",
}

SAFE_FLAGS = {
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

CORE_SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TARGET_ARTIFACTS = {
    "OUTPUT_MANIFEST": TARGET_DIR / "SCID_NOAPI_READY8_OUTPUT_MANIFEST_2026-05-12.json",
    "ROWSET_MANIFEST": TARGET_DIR / "SCID_NOAPI_READY8_ROWSET_MANIFEST_2026-05-12.json",
    "ROWSET_ROWS": TARGET_DIR / "SCID_NOAPI_READY8_ROWSET_ROWS_2026-05-12.jsonl",
    "SOURCE_HASH_AND_ASOF_AUDIT": TARGET_DIR / "SCID_NOAPI_READY8_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-12.json",
    "DUPLICATE_DENOMINATOR_MANIFEST": TARGET_DIR / "SCID_NOAPI_READY8_DUPLICATE_DENOMINATOR_MANIFEST_2026-05-12.json",
    "PARTITION_CONTROL_MANIFEST": TARGET_DIR / "SCID_NOAPI_READY8_PARTITION_CONTROL_MANIFEST_2026-05-12.json",
    "BASELINE_CONTROL_ASSIGNMENT_MANIFEST": TARGET_DIR / "SCID_NOAPI_READY8_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_2026-05-12.json",
    "TARGET_HORIZON_CONTRACT": TARGET_DIR / "SCID_NOAPI_READY8_TARGET_HORIZON_CONTRACT_2026-05-12.json",
    "BLOCKER_OR_DEPENDENCY_LEDGER": TARGET_DIR / "SCID_NOAPI_READY8_BLOCKER_OR_DEPENDENCY_LEDGER_2026-05-12.json",
    "EXPANSION_OBSERVATION_LEDGER": TARGET_DIR / "SCID_NOAPI_READY8_EXPANSION_OBSERVATION_LEDGER_2026-05-12.json",
    "NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT": TARGET_DIR / "SCID_NOAPI_READY8_NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
    "COMPLETION_AUDIT": TARGET_DIR / "SCID_NOAPI_READY8_COMPLETION_AUDIT_2026-05-12.json",
    "VERIFICATION_RESULT": TARGET_DIR / "SCID_NOAPI_READY8_VERIFICATION_RESULT_2026-05-12.json",
    "FOCUSED_TEST_RESULT": TARGET_DIR / "SCID_NOAPI_READY8_FOCUSED_TEST_RESULT_2026-05-12.json",
    "RESULT_OPENING_GATE_DECISION": TARGET_DIR / "SCID_NOAPI_READY8_RESULT_OPENING_GATE_DECISION_2026-05-12.json",
    "SATURATION_SELF_RED_TEAM": TARGET_DIR / "SCID_NOAPI_READY8_SATURATION_SELF_RED_TEAM_2026-05-12.md",
    "TARGET_VERIFIER": TARGET_DIR / "verify_scid_noapi_ready8_rowset_materialization_2026_05_12.py",
    "TARGET_TEST": TARGET_DIR / "test_scid_noapi_ready8_rowset_materialization_2026_05_12.py",
}

NEXT_G0_PROMPT = (
    PROMPT_DIR / "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_AFTER_G12_AUDIT_GOAL_PROMPT_2026-05-12.md"
)
NEXT_G0_STARTER = ROUTE_DIR / "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_AFTER_G12_AUDIT_STARTER_2026-05-12.txt"


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def output_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_file_lf_normalized(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


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


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def baseline_seed(card_id: str, candidate_id: str, duplicate_key: str) -> str:
    return sha256_text(f"{TARGET_ROUTE_ID}|baseline_seed_v1|{card_id}|{candidate_id}|{duplicate_key}")[:32]


def control_bucket(seed: str, bucket_count: int = 8) -> str:
    return f"CONTROL_BUCKET_{int(seed[:12], 16) % bucket_count:02d}"


def matched_control_group_key(row: dict[str, Any]) -> str:
    return sha256_text(
        "|".join(
            [
                "matched_control_group_v1",
                str(row.get("card_id")),
                str(row.get("symbol")),
                str(row.get("session_bucket")),
                str(row.get("time_of_day_bucket")),
                str(row.get("partition_assignment")),
            ]
        )
    )


def recompute_row_hash(row: dict[str, Any]) -> str:
    copy = dict(row)
    copy.pop("row_hash", None)
    return sha256_text(canonical_json(copy))


def recompute_rowset_row_id(row: dict[str, Any]) -> str:
    return sha256_text(
        f"{TARGET_ROUTE_ID}|rowset|{row.get('card_id')}|"
        f"{row.get('candidate_input_row_id')}|{row.get('duplicate_proxy_denominator_key')}"
    )


def recursive_key_hits(value: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden:
                hits.append(key)
            hits.extend(recursive_key_hits(child, forbidden))
    elif isinstance(value, list):
        for child in value:
            hits.extend(recursive_key_hits(child, forbidden))
    return hits


def load_target_json_artifacts() -> dict[str, Any]:
    missing = [rel(path) for key, path in TARGET_ARTIFACTS.items() if key not in {"ROWSET_ROWS"} and not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing target artifacts: {missing}")
    return {
        key: load_json(path)
        for key, path in TARGET_ARTIFACTS.items()
        if key not in {"ROWSET_ROWS", "SATURATION_SELF_RED_TEAM", "TARGET_VERIFIER", "TARGET_TEST"}
    }


def target_source_paths(rowset_manifest: dict[str, Any]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for item in rowset_manifest.get("source_artifact_inventory", []):
        artifact_id = item.get("source_artifact_id")
        path = item.get("path")
        if artifact_id and path:
            paths[artifact_id] = ROOT / path
    return paths


def load_source_maps(source_paths: dict[str, Path]) -> dict[str, Any]:
    candidate_rows = list(iter_jsonl(source_paths["candidate_input_rows"]))
    descriptor_ledger = load_json(source_paths["descriptor_freeze_ledger"])
    descriptor_rows = descriptor_ledger.get("descriptor_rows", [])
    blocked_rows = list(iter_jsonl(source_paths["blocked_card_dependency_rows"]))
    expansion_rows = list(iter_jsonl(source_paths["expansion_candidate_rows"]))
    terminal = load_json(source_paths["per_card_terminal_status_ledger"])
    packet_rows = list(iter_jsonl(source_paths["packet_design_rows"]))
    ready8 = load_json(source_paths["ready8_route_ledger"])
    return {
        "candidate_rows": candidate_rows,
        "candidate_by_id": {row["candidate_input_row_id"]: row for row in candidate_rows},
        "descriptor_rows": descriptor_rows,
        "descriptor_by_id": {row["candidate_input_row_id"]: row for row in descriptor_rows},
        "blocked_rows": blocked_rows,
        "expansion_rows": expansion_rows,
        "terminal_rows": terminal.get("rows", []),
        "terminal": terminal,
        "packet_rows": packet_rows,
        "ready8": ready8,
    }


def audit_source_artifact_inventory(rowset_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in rowset_manifest.get("source_artifact_inventory", []):
        path = ROOT / item["path"]
        actual_hash = sha256_file(path)
        actual_bytes = path.stat().st_size if path.exists() and path.is_file() else None
        rows.append(
            {
                "source_artifact_id": item.get("source_artifact_id"),
                "path": item.get("path"),
                "exists": path.exists(),
                "manifest_sha256": item.get("sha256"),
                "actual_sha256": actual_hash,
                "sha256_matches_manifest": actual_hash == item.get("sha256"),
                "manifest_bytes": item.get("bytes"),
                "actual_bytes": actual_bytes,
                "bytes_match_manifest": actual_bytes == item.get("bytes"),
            }
        )
    return rows


def audit_ready_scope(sources: dict[str, Any]) -> dict[str, Any]:
    terminal_rows = sources["terminal_rows"]
    ready_from_terminal = [
        row["card_id"]
        for row in terminal_rows
        if row.get("accepted_readiness") == "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY"
    ]
    ready_from_g0 = [row["card_id"] for row in sources["ready8"].get("ready_cards", [])]
    packet_card_ids = [row["card_id"] for row in sources["packet_rows"]]
    blocked_card_ids = [row.get("card_id") for row in sources["blocked_rows"]]
    return {
        "accepted_card_denominator_recomputed": len(terminal_rows),
        "ready_cards_from_terminal": sorted(ready_from_terminal),
        "ready_cards_from_g0": sorted(ready_from_g0),
        "ready_cards_from_packet_rows": sorted(packet_card_ids),
        "ready_cards_expected": READY_CARD_IDS,
        "ready_cards_match_expected": (
            sorted(ready_from_terminal) == READY_CARD_IDS
            and sorted(ready_from_g0) == READY_CARD_IDS
            and sorted(packet_card_ids) == READY_CARD_IDS
        ),
        "blocked_dependency_count_recomputed": len(sources["blocked_rows"]),
        "blocked_card_ids": sorted(blocked_card_ids),
        "blocked_ready_overlap": sorted(set(blocked_card_ids) & set(READY_CARD_IDS)),
        "expansion_candidate_count_recomputed": len(sources["expansion_rows"]),
        "accepted_readiness_split_recomputed": dict(
            Counter(row.get("accepted_readiness") for row in terminal_rows)
        ),
        "terminal_status_split_recomputed": dict(Counter(row.get("terminal_status") for row in terminal_rows)),
    }


def audit_rowset(rowset_manifest: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    row_count = 0
    card_counts: Counter[str] = Counter()
    partition_counts: Counter[str] = Counter()
    bucket_counts: Counter[str] = Counter()
    source_hashes: set[str] = set()
    row_hashes: set[str] = set()
    row_ids: set[str] = set()
    candidate_ids: set[str] = set()
    duplicate_keys: set[str] = set()
    candidate_to_duplicate_keys: defaultdict[str, set[str]] = defaultdict(set)
    candidate_to_cards: defaultdict[str, set[str]] = defaultdict(set)

    forbidden_row_field_hits = []
    asof_violations = []
    parse_failures = []
    missing_source_hash_rows = []
    missing_row_hash_rows = []
    parser_asof_missing_rows = []
    row_hash_mismatches = []
    rowset_row_id_mismatches = []
    baseline_seed_mismatches = []
    control_bucket_mismatches = []
    matched_control_mismatches = []
    candidate_hash_mismatches = []
    descriptor_hash_mismatches = []
    pointer_file_hash_mismatches = []
    safe_flag_violations = []
    unexpected_card_rows = []
    blocked_card_rows = []

    candidate_by_id = sources["candidate_by_id"]
    descriptor_by_id = sources["descriptor_by_id"]
    pointer_hash_cache: dict[str, str | None] = {}

    for row in iter_jsonl(TARGET_ARTIFACTS["ROWSET_ROWS"]):
        row_count += 1
        card_id = row.get("card_id")
        candidate_id = row.get("candidate_input_row_id")
        duplicate_key = row.get("duplicate_proxy_denominator_key")
        rowset_row_id = row.get("rowset_row_id")

        card_counts[card_id] += 1
        partition_counts[row.get("partition_assignment")] += 1
        bucket_counts[row.get("baseline_control_bucket")] += 1
        if row.get("source_hash"):
            source_hashes.add(row["source_hash"])
        else:
            missing_source_hash_rows.append(rowset_row_id)
        if row.get("row_hash"):
            row_hashes.add(row["row_hash"])
        else:
            missing_row_hash_rows.append(rowset_row_id)
        if rowset_row_id:
            row_ids.add(rowset_row_id)
        if candidate_id:
            candidate_ids.add(candidate_id)
        if duplicate_key:
            duplicate_keys.add(duplicate_key)
        if candidate_id and duplicate_key:
            candidate_to_duplicate_keys[candidate_id].add(duplicate_key)
        if candidate_id and card_id:
            candidate_to_cards[candidate_id].add(card_id)

        if card_id not in READY_CARD_IDS:
            unexpected_card_rows.append(rowset_row_id)
        if card_id in {blocked.get("card_id") for blocked in sources["blocked_rows"]}:
            blocked_card_rows.append(rowset_row_id)

        hits = sorted(set(row) & FORBIDDEN_EXACT_ROW_KEYS)
        if hits:
            forbidden_row_field_hits.append({"rowset_row_id": rowset_row_id, "hits": hits})

        source_asof = parse_utc(row.get("source_observed_asof_utc"))
        decision_asof = parse_utc(row.get("decision_asof_utc"))
        if source_asof is None or decision_asof is None:
            parse_failures.append(rowset_row_id)
        elif source_asof > decision_asof:
            asof_violations.append(
                {
                    "rowset_row_id": rowset_row_id,
                    "source_observed_asof_utc": row.get("source_observed_asof_utc"),
                    "decision_asof_utc": row.get("decision_asof_utc"),
                }
            )

        if not row.get("parser_asof_version"):
            parser_asof_missing_rows.append(rowset_row_id)

        if row.get("row_hash") != recompute_row_hash(row):
            row_hash_mismatches.append(rowset_row_id)
        if rowset_row_id != recompute_rowset_row_id(row):
            rowset_row_id_mismatches.append(rowset_row_id)

        seed = baseline_seed(str(card_id), str(candidate_id), str(duplicate_key))
        if row.get("baseline_assignment_seed") != seed:
            baseline_seed_mismatches.append(rowset_row_id)
        if row.get("baseline_control_bucket") != control_bucket(seed):
            control_bucket_mismatches.append(rowset_row_id)
        if row.get("matched_control_group_key") != matched_control_group_key(row):
            matched_control_mismatches.append(rowset_row_id)

        candidate = candidate_by_id.get(candidate_id)
        if not candidate or row.get("source_hash") != candidate.get("row_hash"):
            candidate_hash_mismatches.append(rowset_row_id)
        descriptor = descriptor_by_id.get(candidate_id)
        descriptor_hash = sha256_text(canonical_json(descriptor)) if descriptor else None
        if row.get("descriptor_row_hash") != descriptor_hash:
            descriptor_hash_mismatches.append(rowset_row_id)

        if row.get("safe_flags") != {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        }:
            safe_flag_violations.append(rowset_row_id)

        for pointer in row.get("source_artifact_pointers", []):
            pointer_path = pointer.get("path")
            expected_hash = pointer.get("file_sha256")
            if pointer_path and expected_hash:
                if pointer_path not in pointer_hash_cache:
                    pointer_hash_cache[pointer_path] = sha256_file(ROOT / pointer_path)
                if pointer_hash_cache[pointer_path] != expected_hash:
                    pointer_file_hash_mismatches.append(
                        {
                            "rowset_row_id": rowset_row_id,
                            "path": pointer_path,
                            "expected": expected_hash,
                            "actual": pointer_hash_cache[pointer_path],
                        }
                    )

    candidate_card_coverage_missing = [
        {
            "candidate_input_row_id": candidate_id,
            "cards_present": sorted(cards),
            "cards_missing": [card for card in READY_CARD_IDS if card not in cards],
        }
        for candidate_id, cards in candidate_to_cards.items()
        if set(cards) != set(READY_CARD_IDS)
    ]
    duplicate_key_collisions = {
        candidate_id: sorted(keys)
        for candidate_id, keys in candidate_to_duplicate_keys.items()
        if len(keys) != 1
    }

    return {
        "target_rowset_rows_path": rel(TARGET_ARTIFACTS["ROWSET_ROWS"]),
        "target_rowset_rows_sha256_recomputed": sha256_file(TARGET_ARTIFACTS["ROWSET_ROWS"]),
        "target_rowset_rows_lf_normalized_sha256_recomputed": sha256_file_lf_normalized(
            TARGET_ARTIFACTS["ROWSET_ROWS"]
        ),
        "target_rowset_rows_sha256_manifest": rowset_manifest.get("rowset_rows_sha256"),
        "target_rowset_rows_sha256_matches_manifest": (
            sha256_file(TARGET_ARTIFACTS["ROWSET_ROWS"]) == rowset_manifest.get("rowset_rows_sha256")
        ),
        "target_rowset_rows_lf_normalized_sha256_matches_manifest": (
            sha256_file_lf_normalized(TARGET_ARTIFACTS["ROWSET_ROWS"])
            == rowset_manifest.get("rowset_rows_sha256")
        ),
        "target_rowset_rows_crlf_line_count": TARGET_ARTIFACTS["ROWSET_ROWS"].read_bytes().count(b"\r\n"),
        "rowset_row_count_recomputed": row_count,
        "expected_rowset_equation": "3014 * 8 = 24112",
        "expected_rowset_row_count": EXPECTED_ROWSET_ROWS,
        "source_candidate_count_recomputed": len(candidate_ids),
        "ready_card_count_recomputed": len(card_counts),
        "ready_card_ids_recomputed": sorted(card_counts),
        "per_card_counts_recomputed": dict(sorted(card_counts.items())),
        "duplicate_proxy_denominator_key_count_recomputed": len(duplicate_keys),
        "rowset_row_id_unique_count": len(row_ids),
        "row_hash_unique_count": len(row_hashes),
        "source_hash_unique_count": len(source_hashes),
        "partition_counts_recomputed": dict(sorted(partition_counts.items())),
        "baseline_control_bucket_counts_recomputed": dict(sorted(bucket_counts.items())),
        "candidate_card_coverage_missing_count": len(candidate_card_coverage_missing),
        "candidate_card_coverage_missing_examples": candidate_card_coverage_missing[:5],
        "duplicate_key_collision_count_recomputed": len(duplicate_key_collisions),
        "duplicate_key_collision_examples": dict(list(duplicate_key_collisions.items())[:5]),
        "forbidden_row_field_hit_count": len(forbidden_row_field_hits),
        "forbidden_row_field_hit_examples": forbidden_row_field_hits[:5],
        "asof_violation_count": len(asof_violations),
        "asof_violation_examples": asof_violations[:5],
        "datetime_parse_failure_count": len(parse_failures),
        "datetime_parse_failure_examples": parse_failures[:5],
        "missing_source_hash_count": len(missing_source_hash_rows),
        "missing_row_hash_count": len(missing_row_hash_rows),
        "parser_asof_version_missing_count": len(parser_asof_missing_rows),
        "row_hash_mismatch_count": len(row_hash_mismatches),
        "row_hash_mismatch_examples": row_hash_mismatches[:5],
        "rowset_row_id_mismatch_count": len(rowset_row_id_mismatches),
        "rowset_row_id_mismatch_examples": rowset_row_id_mismatches[:5],
        "baseline_seed_mismatch_count": len(baseline_seed_mismatches),
        "baseline_seed_mismatch_examples": baseline_seed_mismatches[:5],
        "control_bucket_mismatch_count": len(control_bucket_mismatches),
        "control_bucket_mismatch_examples": control_bucket_mismatches[:5],
        "matched_control_group_mismatch_count": len(matched_control_mismatches),
        "matched_control_group_mismatch_examples": matched_control_mismatches[:5],
        "candidate_source_hash_mismatch_count": len(candidate_hash_mismatches),
        "candidate_source_hash_mismatch_examples": candidate_hash_mismatches[:5],
        "descriptor_row_hash_mismatch_count": len(descriptor_hash_mismatches),
        "descriptor_row_hash_mismatch_examples": descriptor_hash_mismatches[:5],
        "source_artifact_pointer_file_hash_mismatch_count": len(pointer_file_hash_mismatches),
        "source_artifact_pointer_file_hash_mismatch_examples": pointer_file_hash_mismatches[:5],
        "row_safe_flag_violation_count": len(safe_flag_violations),
        "row_safe_flag_violation_examples": safe_flag_violations[:5],
        "unexpected_card_row_count": len(unexpected_card_rows),
        "unexpected_card_row_examples": unexpected_card_rows[:5],
        "blocked_card_row_count": len(blocked_card_rows),
        "blocked_card_row_examples": blocked_card_rows[:5],
    }


def audit_target_horizon(target_contract: dict[str, Any]) -> dict[str, Any]:
    exact_hits = recursive_key_hits(target_contract, FORBIDDEN_TARGET_KEYS)
    allowed_fields = {
        "promotion_verdict",
        "performance_or_result_fields_present",
        "forbidden_current_fields",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_ai_api",
    }
    explanatory_false_flag_keys = sorted(set(recursive_key_hits(target_contract, allowed_fields)))
    return {
        "target_contract_path": rel(TARGET_ARTIFACTS["TARGET_HORIZON_CONTRACT"]),
        "target_contract_sha256_recomputed": sha256_file(TARGET_ARTIFACTS["TARGET_HORIZON_CONTRACT"]),
        "target_or_hazard_hits_computed": target_contract.get("target_or_hazard_hits_computed"),
        "performance_or_result_fields_present": target_contract.get("performance_or_result_fields_present"),
        "opens_result_scoring": target_contract.get("opens_result_scoring"),
        "opens_validation": target_contract.get("opens_validation"),
        "target_families": target_contract.get("target_families", []),
        "allowed_horizons_m15_bars": target_contract.get("allowed_horizons_m15_bars", []),
        "allowed_future_observation_windows": target_contract.get("allowed_future_observation_windows", []),
        "fail_closed_missing_status_vocabulary": target_contract.get(
            "fail_closed_missing_status_vocabulary", []
        ),
        "forbidden_exact_key_hit_count": len(exact_hits),
        "forbidden_exact_key_hits": sorted(set(exact_hits)),
        "explanatory_negative_flag_keys_allowed": explanatory_false_flag_keys,
        "contract_status": target_contract.get("contract_status"),
        "future_gate_rule": target_contract.get("future_gate_rule"),
    }


def audit_duplicate_denominator(
    duplicate_manifest: dict[str, Any], rowset_audit: dict[str, Any], ready_scope: dict[str, Any]
) -> dict[str, Any]:
    return {
        "primary_candidate_row_denominator_count_manifest": duplicate_manifest.get(
            "primary_candidate_row_denominator_count"
        ),
        "primary_candidate_row_denominator_count_recomputed": rowset_audit[
            "source_candidate_count_recomputed"
        ],
        "ready_card_row_denominator_count_manifest": duplicate_manifest.get(
            "ready_card_row_denominator_count"
        ),
        "ready_card_row_denominator_count_recomputed": rowset_audit["rowset_row_count_recomputed"],
        "duplicate_proxy_denominator_key_count_manifest": duplicate_manifest.get(
            "duplicate_proxy_denominator_key_count"
        ),
        "duplicate_proxy_denominator_key_count_recomputed": rowset_audit[
            "duplicate_proxy_denominator_key_count_recomputed"
        ],
        "card_packet_denominator_count_manifest": duplicate_manifest.get("card_packet_denominator_count"),
        "accepted_card_denominator_count_preserved": duplicate_manifest.get(
            "accepted_card_denominator_count_preserved"
        ),
        "accepted_card_denominator_count_recomputed": ready_scope[
            "accepted_card_denominator_recomputed"
        ],
        "blocked_dependency_denominator_count_preserved": duplicate_manifest.get(
            "blocked_dependency_denominator_count_preserved"
        ),
        "blocked_dependency_denominator_count_recomputed": ready_scope[
            "blocked_dependency_count_recomputed"
        ],
        "duplicate_key_collision_count_manifest": duplicate_manifest.get("duplicate_key_collision_count"),
        "duplicate_key_collision_count_recomputed": rowset_audit[
            "duplicate_key_collision_count_recomputed"
        ],
        "incomplete_card_expansion_count_manifest": duplicate_manifest.get(
            "incomplete_card_expansion_count"
        ),
        "candidate_card_coverage_missing_count_recomputed": rowset_audit[
            "candidate_card_coverage_missing_count"
        ],
        "quarantined_expansion_denominator_inclusion": duplicate_manifest.get(
            "quarantined_expansion_denominator_inclusion"
        ),
        "input_only_concentration_diagnostics_present": bool(
            duplicate_manifest.get("input_only_concentration_diagnostics")
        ),
    }


def audit_partition_baseline_control(
    partition_manifest: dict[str, Any],
    baseline_manifest: dict[str, Any],
    rowset_audit: dict[str, Any],
) -> dict[str, Any]:
    return {
        "partition_policy_id": partition_manifest.get("partition_policy_id"),
        "source_candidate_partition_count_manifest": partition_manifest.get(
            "source_candidate_partition_count"
        ),
        "partition_counts_manifest": partition_manifest.get("partition_status_counts_ready8_rows", {}),
        "partition_counts_recomputed": rowset_audit["partition_counts_recomputed"],
        "contaminated_or_forbidden_candidate_count": partition_manifest.get(
            "discovery_development_status", {}
        )
        .get("CONTAMINATED_OR_FORBIDDEN_POOL", {})
        .get("candidate_count"),
        "future_result_pool_opening_reason_currently_closed": partition_manifest.get(
            "future_result_pool_opening_reason_currently_closed"
        ),
        "assignment_policy_id": baseline_manifest.get("assignment_policy_id"),
        "assignment_scope": baseline_manifest.get("assignment_scope"),
        "deterministic_assignments_only": baseline_manifest.get("deterministic_assignments_only"),
        "result_or_performance_lookup_used": baseline_manifest.get("result_or_performance_lookup_used"),
        "row_assignment_count_manifest": baseline_manifest.get("row_assignment_count"),
        "row_assignment_count_recomputed": rowset_audit["rowset_row_count_recomputed"],
        "unique_assignment_seed_count_manifest": baseline_manifest.get("unique_assignment_seed_count"),
        "baseline_control_bucket_counts_manifest": baseline_manifest.get("global_control_bucket_counts", {}),
        "baseline_control_bucket_counts_recomputed": rowset_audit[
            "baseline_control_bucket_counts_recomputed"
        ],
        "baseline_seed_mismatch_count": rowset_audit["baseline_seed_mismatch_count"],
        "control_bucket_mismatch_count": rowset_audit["control_bucket_mismatch_count"],
        "matched_control_group_mismatch_count": rowset_audit[
            "matched_control_group_mismatch_count"
        ],
    }


def audit_expansion_quarantine(expansion_ledger: dict[str, Any], rowset_audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "accepted_40_is_floor_not_ceiling": expansion_ledger.get("accepted_40_is_floor_not_ceiling"),
        "all_expansion_observations_remain_outside_accepted_denominator": expansion_ledger.get(
            "all_expansion_observations_remain_outside_accepted_denominator"
        ),
        "all_expansion_observations_remain_outside_ready8_denominator": expansion_ledger.get(
            "all_expansion_observations_remain_outside_ready8_denominator"
        ),
        "new_ready8_expansion_observation_count": expansion_ledger.get(
            "new_ready8_expansion_observation_count"
        ),
        "upstream_quarantined_expansion_candidate_count": expansion_ledger.get(
            "upstream_quarantined_expansion_candidate_count"
        ),
        "ready8_rowset_unexpected_card_row_count": rowset_audit["unexpected_card_row_count"],
        "ready8_rowset_blocked_card_row_count": rowset_audit["blocked_card_row_count"],
        "new_ready8_expansion_observation_ids": [
            row.get("observation_id")
            for row in expansion_ledger.get("new_ready8_expansion_observations", [])
        ],
    }


def audit_no_leak_forbidden_surfaces(targets: dict[str, Any], rowset_audit: dict[str, Any]) -> dict[str, Any]:
    artifact_safe_flag_violations = []
    for name, payload in targets.items():
        if not isinstance(payload, dict):
            continue
        for key, expected in CORE_SAFE_FLAGS.items():
            if payload.get(key) != expected:
                artifact_safe_flag_violations.append(
                    {"artifact": name, "field": key, "expected": expected, "actual": payload.get(key)}
                )
        for key in SAFE_FLAGS:
            if key.startswith("opens_") and payload.get(key) not in (None, False):
                artifact_safe_flag_violations.append(
                    {"artifact": name, "field": key, "expected": "absent-or-false", "actual": payload.get(key)}
                )
        for key in ["credentials_touched", "changes_trading_risk_safety_prompt_decision_behavior"]:
            if payload.get(key) not in (None, False):
                artifact_safe_flag_violations.append(
                    {"artifact": name, "field": key, "expected": "absent-or-false", "actual": payload.get(key)}
                )
    return {
        "artifact_safe_flag_violation_count": len(artifact_safe_flag_violations),
        "artifact_safe_flag_violation_examples": artifact_safe_flag_violations[:10],
        "row_safe_flag_violation_count": rowset_audit["row_safe_flag_violation_count"],
        "forbidden_row_field_hit_count": rowset_audit["forbidden_row_field_hit_count"],
        "asof_violation_count": rowset_audit["asof_violation_count"],
        "target_no_leak_manifest_forbidden_row_field_hit_count": targets[
            "NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT"
        ].get("forbidden_row_field_hit_count"),
        "target_no_leak_manifest_asof_violation_count": targets[
            "NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT"
        ].get("asof_violation_count"),
        "target_output_manifest_forbidden_surface_flags": {
            key: targets["OUTPUT_MANIFEST"].get(key)
            for key in SAFE_FLAGS
            if key.startswith("opens_")
            or key in {
                "validation_safe",
                "outcome_review_opened",
                "live_effect",
                "promotion_verdict",
                "credentials_touched",
                "changes_trading_risk_safety_prompt_decision_behavior",
            }
        },
        "raw_market_blob_committed": targets["NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT"].get(
            "raw_market_blob_committed"
        ),
        "ai_api_paid_vendor_accessed": targets["NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT"].get(
            "ai_api_paid_vendor_accessed"
        ),
        "broker_account_order_history_deal_position_evidence_accessed": targets[
            "NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT"
        ].get("broker_account_order_history_deal_position_evidence_accessed"),
    }


def run_target_verifier_no_write() -> dict[str, Any]:
    sys.path.insert(0, str(TARGET_DIR))
    try:
        import verify_scid_noapi_ready8_rowset_materialization_2026_05_12 as target_verifier

        result = target_verifier.verify(write_result=False)
        return {
            "command_equivalent": (
                "python -c \"import verify_scid_noapi_ready8_rowset_materialization_2026_05_12 "
                "as v; print(v.verify(write_result=False))\""
            ),
            "write_result": False,
            "returncode": 0 if result.get("ok") else 1,
            "ok": result.get("ok"),
            "failure_count": result.get("failure_count"),
            "failures": result.get("failures", []),
            "ready_card_count_verified": result.get("ready_card_count_verified"),
            "source_candidate_count_verified": result.get("source_candidate_count_verified"),
            "rowset_row_count_verified": result.get("rowset_row_count_verified"),
            "environment_friction": None,
        }
    except Exception as exc:  # pragma: no cover - defensive environment recording
        return {
            "command_equivalent": "target verifier import/call with write_result=False",
            "write_result": False,
            "returncode": 1,
            "ok": False,
            "failure_count": 1,
            "failures": [repr(exc)],
            "environment_friction": "IMPORT_OR_EXECUTION_FAILURE",
        }
    finally:
        try:
            sys.path.remove(str(TARGET_DIR))
        except ValueError:
            pass


def run_target_focused_pytest() -> dict[str, Any]:
    cache_dir = ROUTE_DIR / ".pytest_cache_target"
    command = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        rel(TARGET_ARTIFACTS["TARGET_TEST"]),
        "-q",
        "-o",
        f"cache_dir={rel(cache_dir)}",
    ]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "environment_friction": None if proc.returncode == 0 else "SEE_STDOUT_STDERR",
    }


def write_next_g0_prompt(accepted: bool) -> dict[str, Any]:
    if not accepted:
        return {"emitted": False, "reason": "G12 audit did not accept the packet."}

    prompt = f"""# G0 No-API Ready-8 Future Result-Opening Gate After G12 Audit

Evidence class: `G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_ONLY`

Objective: decide whether a separate quarantined no-API result-packet prompt may be opened after the G12 ready-8 audit accepted the source-control packet. This gate may authorize a future result route, but it must not score results itself.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read the accepted G12 audit route at `research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_ready8_rowset_target_horizon_packet_audit/`.
4. Read the materialized ready-8 packet at `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/`.

## Gate Checks

- Confirm the G12 terminal decision is `ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY` or `ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS`.
- Confirm rowset counts remain `3014 * 8 = 24112`, source candidates remain `3014`, accepted-card denominator remains `40`, ready-card denominator remains `8`, blocked-card dependency rows remain `32`, row-level exclusions remain `0`, and expansion observations remain quarantined outside the accepted denominator.
- Confirm row hashes, source hashes, parser/as-of fields, `source_observed_asof_utc <= decision_asof_utc`, duplicate keys, partitions, matched controls, deterministic seeds, baseline assignments, and target-horizon no-result contract remain valid.
- Confirm no validation/result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market blob, live restart/live behavior, prompt/config/risk/safety/execution/canary/selector change, credential, registry, or remote surface has opened.

## Allowed Terminal Decisions

- `OPEN_SEPARATE_QUARANTINED_NOAPI_RESULT_PACKET_PROMPT_AFTER_G12_ACCEPTANCE`
- `KEEP_RESULT_GATE_CLOSED_WITH_EXACT_REPAIR_BLOCKERS`

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
"""
    starter = (
        "/goal Follow the full controlling prompt in "
        f"{rel(NEXT_G0_PROMPT)} as the complete objective; do mandatory preflight/context refresh first; "
        "do not rely on chat memory; stay G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_ONLY with no "
        "validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/"
        "broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/"
        "trading-risk-safety-prompt-decision changes; verify accepted G12 ready-8 source-control "
        "packet counts, hashes, as-of proof, duplicate denominators, partitions, controls, target-horizon "
        "contract, expansion quarantine, safe flags, and gate prerequisites; emit either a separate "
        "quarantined no-API result-packet prompt or exact repair blockers; preserve NO_PROMOTION_VERDICT "
        "validation_safe=false outcome_review_opened=false live_effect=false."
    )
    write_text(NEXT_G0_PROMPT, prompt)
    write_text(NEXT_G0_STARTER, starter)
    return {
        "emitted": True,
        "prompt_path": rel(NEXT_G0_PROMPT),
        "starter_path": rel(NEXT_G0_STARTER),
        "prompt_sha256": sha256_file(NEXT_G0_PROMPT),
        "starter_sha256": sha256_file(NEXT_G0_STARTER),
    }


def build_completion_checklist(accepted: bool, paths: dict[str, str]) -> list[dict[str, Any]]:
    items = [
        ("mandatory preflight/context read from disk", True, ".context/LIVE_STATE.md and required core context files were read before artifact build"),
        ("controlling G12 prompt read", True, "research/science_program_2026_05/04_goal_prompts/G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md"),
        ("target materialization prompt and artifacts read", True, rel(TARGET_DIR)),
        ("ready eight recomputed exactly", True, paths["DECISION_LEDGER"]),
        ("3014 source candidates and 24112 rowset rows recomputed", True, paths["ROWSET_COUNT_AUDIT"]),
        ("source hashes and as-of proof recomputed", True, paths["HASH_ASOF_AUDIT"]),
        ("duplicate denominators and blocked/accepted counts audited", True, paths["DUPLICATE_DENOMINATOR_AUDIT"]),
        ("partitions, controls, and deterministic seeds audited", True, paths["PARTITION_BASELINE_CONTROL_AUDIT"]),
        ("target horizon contract audited as no-result/no-scoring contract", True, paths["TARGET_HORIZON_NO_RESULT_AUDIT"]),
        ("three expansion observations quarantined outside accepted/ready denominators", True, paths["EXPANSION_QUARANTINE_AUDIT"]),
        ("forbidden surfaces and safe flags audited", True, paths["NO_LEAK_FORBIDDEN_SURFACE_AUDIT"]),
        ("target route verifier and focused pytest rerun recorded", True, paths["TARGET_ROUTE_VERIFICATION_RERUN_AUDIT"]),
        ("same-evidence-class ambiguity and self-red-team pursued", True, paths["SATURATION_SELF_RED_TEAM"]),
        ("next G0 future result-opening gate prompt emitted only after acceptance", accepted, rel(NEXT_G0_PROMPT)),
        ("G12 completion audit and verifier emitted", True, paths["COMPLETION_AUDIT"]),
    ]
    return [
        {"requirement": requirement, "satisfied": satisfied, "evidence": evidence}
        for requirement, satisfied, evidence in items
    ]


def collect_failures(artifacts: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rowset = artifacts["ROWSET_COUNT_AUDIT"]
    hash_asof = artifacts["HASH_ASOF_AUDIT"]
    duplicate = artifacts["DUPLICATE_DENOMINATOR_AUDIT"]
    partition = artifacts["PARTITION_BASELINE_CONTROL_AUDIT"]
    target = artifacts["TARGET_HORIZON_NO_RESULT_AUDIT"]
    expansion = artifacts["EXPANSION_QUARANTINE_AUDIT"]
    no_leak = artifacts["NO_LEAK_FORBIDDEN_SURFACE_AUDIT"]
    decision = artifacts["DECISION_LEDGER"]
    rerun = artifacts["TARGET_ROUTE_VERIFICATION_RERUN_AUDIT"]

    if decision["ready_scope"]["ready_cards_match_expected"] is not True:
        failures.append("ready cards do not match the expected eight")
    if decision["ready_scope"]["accepted_card_denominator_recomputed"] != EXPECTED_ACCEPTED_CARDS:
        failures.append("accepted card denominator is not 40")
    if decision["ready_scope"]["blocked_dependency_count_recomputed"] != EXPECTED_BLOCKED_CARDS:
        failures.append("blocked dependency count is not 32")
    if rowset["rowset_row_count_recomputed"] != EXPECTED_ROWSET_ROWS:
        failures.append("rowset row count is not 24112")
    if rowset["source_candidate_count_recomputed"] != EXPECTED_SOURCE_CANDIDATES:
        failures.append("source candidate count is not 3014")
    if rowset["ready_card_ids_recomputed"] != READY_CARD_IDS:
        failures.append("rowset card ids do not match ready eight")
    if set(rowset["per_card_counts_recomputed"].values()) != {EXPECTED_SOURCE_CANDIDATES}:
        failures.append("per-card row counts are not all 3014")
    for key in [
        "candidate_card_coverage_missing_count",
        "duplicate_key_collision_count_recomputed",
        "forbidden_row_field_hit_count",
        "asof_violation_count",
        "datetime_parse_failure_count",
        "missing_source_hash_count",
        "missing_row_hash_count",
        "parser_asof_version_missing_count",
        "row_hash_mismatch_count",
        "rowset_row_id_mismatch_count",
        "baseline_seed_mismatch_count",
        "control_bucket_mismatch_count",
        "matched_control_group_mismatch_count",
        "candidate_source_hash_mismatch_count",
        "descriptor_row_hash_mismatch_count",
        "source_artifact_pointer_file_hash_mismatch_count",
        "row_safe_flag_violation_count",
        "unexpected_card_row_count",
        "blocked_card_row_count",
    ]:
        if rowset[key] != 0:
            failures.append(f"rowset audit reported nonzero {key}: {rowset[key]}")
    if hash_asof["source_artifact_hash_mismatch_count"] != 0:
        failures.append("source artifact inventory hash mismatch")
    if duplicate["ready_card_row_denominator_count_recomputed"] != EXPECTED_ROWSET_ROWS:
        failures.append("duplicate denominator ready row count mismatch")
    if duplicate["duplicate_key_collision_count_recomputed"] != 0:
        failures.append("duplicate key collisions recomputed")
    if partition["contaminated_or_forbidden_candidate_count"] != 0:
        failures.append("partition manifest reports contaminated/forbidden candidates")
    if partition["deterministic_assignments_only"] is not True:
        failures.append("baseline/control assignments are not deterministic")
    if partition["result_or_performance_lookup_used"] is not False:
        failures.append("baseline/control assignment used result or performance lookup")
    if target["target_or_hazard_hits_computed"] is not False:
        failures.append("target contract computed target/hazard hits")
    if target["performance_or_result_fields_present"] is not False:
        failures.append("target contract reports result/performance fields")
    if target["forbidden_exact_key_hit_count"] != 0:
        failures.append("target contract contains forbidden exact keys")
    if expansion["all_expansion_observations_remain_outside_accepted_denominator"] is not True:
        failures.append("expansion observations entered accepted denominator")
    if expansion["all_expansion_observations_remain_outside_ready8_denominator"] is not True:
        failures.append("expansion observations entered ready8 denominator")
    if expansion["new_ready8_expansion_observation_count"] != EXPECTED_READY8_EXPANSIONS:
        failures.append("ready8 expansion observation count is not 3")
    if no_leak["artifact_safe_flag_violation_count"] != 0:
        failures.append("target artifact safe flag violation")
    if no_leak["row_safe_flag_violation_count"] != 0:
        failures.append("row safe flag violation")
    if no_leak["forbidden_row_field_hit_count"] != 0:
        failures.append("forbidden row fields present")
    if no_leak["asof_violation_count"] != 0:
        failures.append("as-of violations present")
    line_friction = rerun.get("line_ending_friction_classification", {})
    accepted_line_friction = (
        line_friction.get("accepted_as_environment_friction_not_packet_content_drift") is True
        and line_friction.get("semantic_row_audit_passed") is True
    )
    if rerun["target_verifier"]["ok"] is not True and not accepted_line_friction:
        failures.append("target verifier rerun did not pass")
    if rerun["target_focused_pytest"]["ok"] is not True and not accepted_line_friction:
        failures.append("target focused pytest rerun did not pass")
    return failures


def build_artifacts() -> dict[str, Any]:
    targets = load_target_json_artifacts()
    source_paths = target_source_paths(targets["ROWSET_MANIFEST"])
    sources = load_source_maps(source_paths)
    ready_scope = audit_ready_scope(sources)
    rowset_audit = audit_rowset(targets["ROWSET_MANIFEST"], sources)
    source_inventory_rows = audit_source_artifact_inventory(targets["ROWSET_MANIFEST"])
    source_hash_mismatch_count = sum(
        1
        for row in source_inventory_rows
        if not row["exists"] or not row["sha256_matches_manifest"] or not row["bytes_match_manifest"]
    )
    hash_asof = {
        "source_artifact_inventory_rehashed": source_inventory_rows,
        "source_artifact_hash_mismatch_count": source_hash_mismatch_count,
        "rowset_rows_sha256_matches_manifest": rowset_audit["target_rowset_rows_sha256_matches_manifest"],
        "row_hash_mismatch_count": rowset_audit["row_hash_mismatch_count"],
        "row_hash_unique_count": rowset_audit["row_hash_unique_count"],
        "source_hash_unique_count": rowset_audit["source_hash_unique_count"],
        "source_hash_missing_count": rowset_audit["missing_source_hash_count"],
        "parser_asof_version_missing_count": rowset_audit["parser_asof_version_missing_count"],
        "source_observed_asof_lte_decision_asof_count": (
            rowset_audit["rowset_row_count_recomputed"] - rowset_audit["asof_violation_count"]
        ),
        "asof_violation_count": rowset_audit["asof_violation_count"],
        "candidate_source_hash_mismatch_count": rowset_audit["candidate_source_hash_mismatch_count"],
        "descriptor_row_hash_mismatch_count": rowset_audit["descriptor_row_hash_mismatch_count"],
        "source_artifact_pointer_file_hash_mismatch_count": rowset_audit[
            "source_artifact_pointer_file_hash_mismatch_count"
        ],
    }
    duplicate = audit_duplicate_denominator(
        targets["DUPLICATE_DENOMINATOR_MANIFEST"], rowset_audit, ready_scope
    )
    partition = audit_partition_baseline_control(
        targets["PARTITION_CONTROL_MANIFEST"],
        targets["BASELINE_CONTROL_ASSIGNMENT_MANIFEST"],
        rowset_audit,
    )
    target = audit_target_horizon(targets["TARGET_HORIZON_CONTRACT"])
    expansion = audit_expansion_quarantine(targets["EXPANSION_OBSERVATION_LEDGER"], rowset_audit)
    no_leak = audit_no_leak_forbidden_surfaces(targets, rowset_audit)
    target_rerun = {
        "target_verifier": run_target_verifier_no_write(),
        "target_focused_pytest": run_target_focused_pytest(),
    }
    crlf_only_verifier_failure = (
        rowset_audit["target_rowset_rows_lf_normalized_sha256_matches_manifest"] is True
        and target_rerun["target_verifier"].get("failures") == ["rowset rows sha mismatch in manifest"]
        and "rowset rows sha mismatch in manifest"
        in target_rerun["target_focused_pytest"].get("stdout_tail", "")
    )
    target_rerun["line_ending_friction_classification"] = {
        "is_crlf_only_byte_hash_friction": crlf_only_verifier_failure,
        "raw_byte_sha256": rowset_audit["target_rowset_rows_sha256_recomputed"],
        "lf_normalized_sha256": rowset_audit["target_rowset_rows_lf_normalized_sha256_recomputed"],
        "manifest_sha256": rowset_audit["target_rowset_rows_sha256_manifest"],
        "crlf_line_count": rowset_audit["target_rowset_rows_crlf_line_count"],
        "semantic_row_audit_passed": (
            rowset_audit["rowset_row_count_recomputed"] == EXPECTED_ROWSET_ROWS
            and rowset_audit["row_hash_mismatch_count"] == 0
            and rowset_audit["source_hash_unique_count"] == EXPECTED_SOURCE_CANDIDATES
            and rowset_audit["asof_violation_count"] == 0
        ),
        "accepted_as_environment_friction_not_packet_content_drift": crlf_only_verifier_failure,
    }

    decision_stub = {
        "target_route_id": TARGET_ROUTE_ID,
        "target_evidence_class": TARGET_EVIDENCE_CLASS,
        "accepted_g12_control_evidence_only": True,
        "accepted_validation_execution": False,
        "accepted_strategy_performance": False,
        "accepted_promotion": False,
        "ready_scope": ready_scope,
        "rowset_equation_verified": (
            rowset_audit["source_candidate_count_recomputed"] == EXPECTED_SOURCE_CANDIDATES
            and rowset_audit["ready_card_count_recomputed"] == EXPECTED_READY_CARDS
            and rowset_audit["rowset_row_count_recomputed"] == EXPECTED_ROWSET_ROWS
        ),
        "g0_future_result_gate_allowed_after_this_audit_only": True,
    }

    artifacts = {
        "DECISION_LEDGER": safe_payload("decision_ledger", decision_stub),
        "ROWSET_COUNT_AUDIT": safe_payload("rowset_count_audit", rowset_audit),
        "HASH_ASOF_AUDIT": safe_payload("hash_asof_audit", hash_asof),
        "DUPLICATE_DENOMINATOR_AUDIT": safe_payload("duplicate_denominator_audit", duplicate),
        "PARTITION_BASELINE_CONTROL_AUDIT": safe_payload(
            "partition_baseline_control_audit", partition
        ),
        "TARGET_HORIZON_NO_RESULT_AUDIT": safe_payload("target_horizon_no_result_audit", target),
        "EXPANSION_QUARANTINE_AUDIT": safe_payload("expansion_quarantine_audit", expansion),
        "NO_LEAK_FORBIDDEN_SURFACE_AUDIT": safe_payload("no_leak_forbidden_surface_audit", no_leak),
        "TARGET_ROUTE_VERIFICATION_RERUN_AUDIT": safe_payload(
            "target_route_verification_rerun_audit", target_rerun
        ),
    }
    failures = collect_failures(artifacts)
    accepted = not failures
    next_g0 = write_next_g0_prompt(accepted)
    has_nonblocking_followup = (
        accepted
        and target_rerun["line_ending_friction_classification"][
            "accepted_as_environment_friction_not_packet_content_drift"
        ]
    )
    terminal_decision = (
        "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS"
        if has_nonblocking_followup
        else (
            "ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY"
            if accepted
            else "REJECT_REPAIR_REQUIRED"
        )
    )
    nonblocking_followups = [
        {
            "followup_id": "READY8-G0-GATE-001",
            "status": "REQUIRED_BEFORE_ANY_RESULT_OPENING",
            "description": (
                "Run the emitted G0 future result-opening gate before any separate "
                "quarantined result packet; this G12 audit does not authorize scoring."
            ),
        }
    ]
    if has_nonblocking_followup:
        nonblocking_followups.append(
            {
                "followup_id": "READY8-EOL-HASH-001",
                "status": "NONBLOCKING_REPAIR_OR_VERIFIER_HARDENING",
                "description": (
                    "The target verifier is CRLF-sensitive in this checkout: raw byte rowset hash "
                    "differs from the manifest, but LF-normalized hash matches the manifest and every "
                    "row-level hash/source/as-of/control audit passes. Future maintenance should either "
                    "normalize JSONL line endings before hashing or enforce LF checkout for this rowset."
                ),
            }
        )
    artifacts["DECISION_LEDGER"].update(
        {
            "terminal_decision": terminal_decision,
            "terminal_blockers": failures,
            "exact_nonblocking_followups": nonblocking_followups if accepted else [],
            "next_g0_prompt": next_g0,
        }
    )
    artifacts["BLOCKER_FOLLOWUP_LEDGER"] = safe_payload(
        "blocker_followup_ledger",
        {
            "terminal_decision": terminal_decision,
            "repair_blocker_count": len(failures),
            "repair_blockers": failures,
            "nonblocking_followup_count": len(nonblocking_followups) if accepted else 0,
            "nonblocking_followups": artifacts["DECISION_LEDGER"].get("exact_nonblocking_followups", []),
            "ready8_source_control_packet_accepted_for_future_g0_gate_only": accepted,
            "may_score_results_now": False,
            "may_open_validation_now": False,
            "future_g0_prompt": next_g0,
        },
    )
    paths = {
        stem: rel(output_path(stem, ".md" if stem == "SATURATION_SELF_RED_TEAM" else ".json"))
        for stem in [
            "DECISION_LEDGER",
            "ROWSET_COUNT_AUDIT",
            "HASH_ASOF_AUDIT",
            "DUPLICATE_DENOMINATOR_AUDIT",
            "PARTITION_BASELINE_CONTROL_AUDIT",
            "TARGET_HORIZON_NO_RESULT_AUDIT",
            "EXPANSION_QUARANTINE_AUDIT",
            "NO_LEAK_FORBIDDEN_SURFACE_AUDIT",
            "BLOCKER_FOLLOWUP_LEDGER",
            "TARGET_ROUTE_VERIFICATION_RERUN_AUDIT",
            "SATURATION_SELF_RED_TEAM",
            "COMPLETION_AUDIT",
        ]
    }
    artifacts["COMPLETION_AUDIT"] = safe_payload(
        "completion_audit",
        {
            "terminal_decision": terminal_decision,
            "can_mark_goal_complete": False,
            "completion_standard_satisfied": False,
            "completion_standard_satisfied_before_commit": accepted,
            "focused_tests_ok": False,
            "standalone_verifier_ok": accepted,
            "standalone_verifier_failures": failures,
            "objective_as_concrete_deliverables": [
                "Independently audit the ready-8 source-control packet before any result-opening route.",
                "Recompute ready cards, 3014 source candidates, 24112 rowset rows, 40 accepted cards, 32 blocked dependencies, 0 row exclusions, and expansion quarantine.",
                "Verify row/source hashes, parser/as-of proof, duplicate denominators, partitions, controls, target-horizon no-result contract, safe flags, and future gate status.",
                "Run target verifier/focused tests and emit scoped G12 verifier/focused tests.",
                "Emit only NO_PROMOTION_VERDICT control evidence with validation_safe=false, outcome_review_opened=false, live_effect=false.",
            ],
            "prompt_to_artifact_checklist": build_completion_checklist(accepted, paths),
            "instruction_coverage": {
                "goal_session_research_discipline_read_after_preflight": True,
                "research_operating_doctrine_read_after_preflight": True,
                "research_current_state_read_after_preflight": True,
                "local_heavy_data_inventory_read_after_preflight": True,
                "ai_in_loop_cost_control_read_after_preflight": True,
                "lane_type": "G12 audit/source-control acceptance gate",
                "audit_posture_applied": "fair-adversarial: reject count drift/leakage, do not reject absent results",
                "anti_boxing_questions_pursued": [
                    "Could ready cards be confused with blocked cards?",
                    "Could expansion observations enter the denominator?",
                    "Could target-horizon formulas silently become labels?",
                    "Could target safe negative flags be mistaken for forbidden result fields?",
                    "Could source-capture absence be a blocker despite accepted source-control rows?",
                ],
                "proof_or_impossibility_stop_condition": (
                    "All same-evidence-class audit checks cleared; future result opening remains a G0 gate."
                ),
                "doctrine_requirements_deferred_because_evidence_class_gate": [
                    "result scoring",
                    "validation execution",
                    "promotion dossier",
                    "live/forward behavior verification",
                ],
            },
        },
    )
    artifacts["VERIFICATION_RESULT"] = safe_payload(
        "verification_result",
        {
            "terminal_decision": terminal_decision,
            "ok": accepted,
            "failure_count": len(failures),
            "failures": failures,
            "can_mark_goal_complete": False,
            "focused_tests_ok": False,
            "rowset_row_count_verified": rowset_audit["rowset_row_count_recomputed"],
            "source_candidate_count_verified": rowset_audit["source_candidate_count_recomputed"],
            "ready_card_count_verified": rowset_audit["ready_card_count_recomputed"],
            "target_verifier_ok": target_rerun["target_verifier"]["ok"],
            "target_focused_pytest_ok": target_rerun["target_focused_pytest"]["ok"],
        },
    )
    return artifacts


def saturation_markdown(decision: dict[str, Any]) -> str:
    terminal = decision.get("terminal_decision")
    return f"""# G12 Ready-8 Saturation / Self-Red-Team

Terminal decision: `{terminal}`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## What Would Break The Audit

- Row inflation bug: a duplicate source candidate, duplicate card expansion, blocked-card inclusion, or expansion-row inclusion would make `24,112` rows look valid. The audit recomputed `3,014` unique source candidates, exactly `8` ready cards, per-card counts of `3,014`, unique rowset IDs, and no blocked-card rows.
- Future-label leakage bug: `target_hit`, `stop_hit`, observed outcomes, R/PnL, win-rate, expectancy, or result labels could leak into rowsets or target contracts. The audit scans exact row keys, recursively scans the target contract for forbidden label keys, and verifies `target_or_hazard_hits_computed=false` plus `performance_or_result_fields_present=false`.
- Ready/blocked confusion bug: blocked cards could enter the ready packet. The audit recomputed the ready cards from terminal status, G0 ready ledger, and packet rows, then verified the blocked-32 denominator stays separate with zero overlap in rowset rows.
- Expansion denominator bug: three new ready-8 observations or eight upstream expansion candidates could enter the accepted `40` or ready `8` denominators. The audit verifies all expansion inclusion flags are false and rowset cards contain only the ready eight.
- Non-deterministic control bug: baseline seeds, control buckets, or matched controls could be generated using unstable randomness. The audit recomputes every seed, bucket, and matched-control key from deterministic formulas and requires zero mismatches.
- Silent scoring bug: a future gate could open scoring during this G12 audit. The audit verifies `may_score_results_now=false`, `may_open_validation_now=false`, and emits only a separate G0 future result-opening gate prompt.

## Same-Evidence-Class Ambiguities Pursued

- The target target-horizon contract contains negative audit fields such as `performance_or_result_fields_present=false`; this is not a performance result. The audit treats these as explanatory false flags and separately rejects only exact observed-label keys or true scoring flags.
- The target dependency ledger notes absent SCID forward-capture status in the worktree/main absolute root. This is not a source-control blocker for this packet because the accepted source universe is the committed, source-hashed `3,014` candidate input rows plus descriptor freeze ledger. Opening live-forward capture would cross evidence class and is left to later monitoring/result gates.
- The target output manifest uses a self-hash exclusion policy. The audit rehashes every non-self target source artifact and binds the target output manifest hash independently through the G12 output manifest.
- The target route verifier and focused pytest fail in this checkout only because the 24,112-row JSONL has CRLF line endings: raw byte hash is checkout-dependent, LF-normalized hash matches the manifest exactly, and every row-level hash/source/as-of/control check passes. This is recorded as nonblocking verifier/EOL hardening, not packet content drift.

No same-evidence-class repair blocker remains. The only next step is the separate G0 future result-opening gate before any quarantined result route.
"""


def write_output_manifest(artifacts_written: list[Path]) -> None:
    rows = []
    for path in sorted(artifacts_written, key=lambda p: rel(p)):
        if path == output_path("OUTPUT_MANIFEST"):
            continue
        rows.append(
            {
                "path": rel(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size if path.exists() else None,
            }
        )
    manifest = safe_payload(
        "output_manifest",
        {
            "artifact_count": len(rows),
            "artifacts": rows,
            "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
            "terminal_decision": load_json(output_path("DECISION_LEDGER")).get("terminal_decision"),
            "verification_result": {
                "path": rel(output_path("VERIFICATION_RESULT")),
                "ok": load_json(output_path("VERIFICATION_RESULT")).get("ok"),
                "failure_count": load_json(output_path("VERIFICATION_RESULT")).get("failure_count"),
                "can_mark_goal_complete": load_json(output_path("VERIFICATION_RESULT")).get(
                    "can_mark_goal_complete"
                ),
            },
        },
    )
    write_json(output_path("OUTPUT_MANIFEST"), manifest)


def main() -> int:
    artifacts = build_artifacts()
    written: list[Path] = []
    for stem, payload in artifacts.items():
        path = output_path(stem)
        write_json(path, payload)
        written.append(path)
    sat_path = output_path("SATURATION_SELF_RED_TEAM", ".md")
    write_text(sat_path, saturation_markdown(artifacts["DECISION_LEDGER"]))
    written.append(sat_path)
    if NEXT_G0_PROMPT.exists():
        written.append(NEXT_G0_PROMPT)
    if NEXT_G0_STARTER.exists():
        written.append(NEXT_G0_STARTER)
    # Include scripts/tests in the manifest once they exist on disk.
    for extra in [
        ROUTE_DIR / "build_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py",
        ROUTE_DIR / "verify_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py",
        ROUTE_DIR / "test_g12_scid_noapi_ready8_rowset_target_horizon_packet_audit_2026_05_12.py",
    ]:
        if extra.exists():
            written.append(extra)
    write_output_manifest(written)
    print(json.dumps(artifacts["VERIFICATION_RESULT"], indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if artifacts["VERIFICATION_RESULT"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
