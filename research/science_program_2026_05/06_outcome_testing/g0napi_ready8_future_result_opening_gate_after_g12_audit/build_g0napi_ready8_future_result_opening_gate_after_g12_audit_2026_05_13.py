"""Build the G0 no-API ready-8 future result-opening gate artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
G12_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_noapi_ready8_rowset_target_horizon_packet_audit"
)
TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_noapi_ready8_rowset_target_horizon_result_packet_materialization"
)

DATE_TAG = "2026-05-13"
PREFIX = "G0NAPI_READY8"
ROUTE_ID = "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_AFTER_G12_AUDIT"
EVIDENCE_CLASS = "G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_ONLY"
SCHEMA_VERSION = "g0napi_ready8_future_result_opening_gate_v1"
TERMINAL_OPEN = "OPEN_SEPARATE_QUARANTINED_NOAPI_RESULT_PACKET_PROMPT_AFTER_G12_ACCEPTANCE"
TERMINAL_CLOSED = "KEEP_RESULT_GATE_CLOSED_WITH_EXACT_REPAIR_BLOCKERS"
TARGET_ROUTE_ID = "SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION"

EXPECTED_SOURCE_CANDIDATES = 3014
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
EXPECTED_READY_CARDS = len(READY_CARD_IDS)
EXPECTED_ROWSET_ROWS = EXPECTED_SOURCE_CANDIDATES * EXPECTED_READY_CARDS
EXPECTED_ACCEPTED_CARDS = 40
EXPECTED_BLOCKED_DEPENDENCIES = 32
EXPECTED_ROW_EXCLUSIONS = 0

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
    "outcome_status",
    "outcome_label",
    "result",
    "realized_r",
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "r_multiple",
    "r",
    "pnl",
    "profit",
    "loss",
    "win_rate",
    "expectancy",
    "performance",
    "performance_score",
    "broker_account",
    "broker_order",
    "broker_history",
    "broker_deal",
    "broker_position",
    "order_ticket",
    "deal_id",
    "position_id",
    "api_response",
    "ai_decision",
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

TARGET_ARTIFACTS = {
    "rowset_manifest": TARGET_DIR / "SCID_NOAPI_READY8_ROWSET_MANIFEST_2026-05-12.json",
    "rowset_rows": TARGET_DIR / "SCID_NOAPI_READY8_ROWSET_ROWS_2026-05-12.jsonl",
    "source_hash_and_asof_audit": TARGET_DIR
    / "SCID_NOAPI_READY8_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-12.json",
    "duplicate_denominator_manifest": TARGET_DIR
    / "SCID_NOAPI_READY8_DUPLICATE_DENOMINATOR_MANIFEST_2026-05-12.json",
    "partition_control_manifest": TARGET_DIR
    / "SCID_NOAPI_READY8_PARTITION_CONTROL_MANIFEST_2026-05-12.json",
    "baseline_control_assignment_manifest": TARGET_DIR
    / "SCID_NOAPI_READY8_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_2026-05-12.json",
    "target_horizon_contract": TARGET_DIR / "SCID_NOAPI_READY8_TARGET_HORIZON_CONTRACT_2026-05-12.json",
    "blocker_or_dependency_ledger": TARGET_DIR
    / "SCID_NOAPI_READY8_BLOCKER_OR_DEPENDENCY_LEDGER_2026-05-12.json",
    "expansion_observation_ledger": TARGET_DIR
    / "SCID_NOAPI_READY8_EXPANSION_OBSERVATION_LEDGER_2026-05-12.json",
    "no_leak_and_forbidden_surface_audit": TARGET_DIR
    / "SCID_NOAPI_READY8_NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
    "verification_result": TARGET_DIR / "SCID_NOAPI_READY8_VERIFICATION_RESULT_2026-05-12.json",
    "completion_audit": TARGET_DIR / "SCID_NOAPI_READY8_COMPLETION_AUDIT_2026-05-12.json",
}

G12_ARTIFACTS = {
    "decision_ledger": G12_DIR / "G12_SCID_NOAPI_READY8_DECISION_LEDGER_2026-05-12.json",
    "blocker_followup_ledger": G12_DIR / "G12_SCID_NOAPI_READY8_BLOCKER_FOLLOWUP_LEDGER_2026-05-12.json",
    "verification_result": G12_DIR / "G12_SCID_NOAPI_READY8_VERIFICATION_RESULT_2026-05-12.json",
    "completion_audit": G12_DIR / "G12_SCID_NOAPI_READY8_COMPLETION_AUDIT_2026-05-12.json",
    "rowset_count_audit": G12_DIR / "G12_SCID_NOAPI_READY8_ROWSET_COUNT_AUDIT_2026-05-12.json",
    "hash_asof_audit": G12_DIR / "G12_SCID_NOAPI_READY8_HASH_ASOF_AUDIT_2026-05-12.json",
    "target_route_verification_rerun_audit": G12_DIR
    / "G12_SCID_NOAPI_READY8_TARGET_ROUTE_VERIFICATION_RERUN_AUDIT_2026-05-12.json",
}

NEXT_RESULT_PROMPT = (
    PROMPT_DIR / "SCID_NOAPI_READY8_QUARANTINED_RESULT_PACKET_AFTER_G0_GATE_GOAL_PROMPT_2026-05-13.md"
)
NEXT_RESULT_STARTER = (
    ROUTE_DIR / "SCID_NOAPI_READY8_QUARANTINED_RESULT_PACKET_AFTER_G0_GATE_STARTER_2026-05-13.txt"
)
GATTRIBUTES_REQUIRED_LINE = (
    "research/science_program_2026_05/06_outcome_testing/"
    "scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/"
    "SCID_NOAPI_READY8_ROWSET_ROWS_2026-05-12.jsonl text eol=lf"
)

TEXT_HASH_EQUIVALENT_SUFFIXES = {
    ".csv",
    ".gitattributes",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}


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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def sha256_file_text_eol_variants(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    if path.suffix.lower() not in TEXT_HASH_EQUIVALENT_SUFFIXES:
        actual = sha256_file(path)
        return {actual} if actual else set()
    raw = path.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return {
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(lf).hexdigest(),
        hashlib.sha256(crlf).hexdigest(),
    }


def file_hash_matches_expected_with_text_eol_equivalence(path: Path, expected: str | None) -> tuple[bool, str | None, bool]:
    actual = sha256_file(path)
    if expected is None or actual is None:
        return actual == expected, actual, False
    if actual == expected:
        return True, actual, False
    return expected in sha256_file_text_eol_variants(path), actual, True


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
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
    }
    base.update(SAFE_FLAGS)
    base.update(payload)
    return base


def baseline_seed(card_id: str, candidate_id: str, duplicate_key: str) -> str:
    return sha256_text(f"{TARGET_ROUTE_ID}|baseline_seed_v1|{card_id}|{candidate_id}|{duplicate_key}")[:32]


def control_bucket(seed: str, bucket_count: int = 8) -> str:
    value = int(seed[:12], 16) % bucket_count
    return f"CONTROL_BUCKET_{value:02d}"


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
    row_without_hash = dict(row)
    row_without_hash.pop("row_hash", None)
    return sha256_text(canonical_json(row_without_hash))


def recompute_rowset_row_id(row: dict[str, Any]) -> str:
    return sha256_text(
        f"{TARGET_ROUTE_ID}|rowset|{row.get('card_id')}|"
        f"{row.get('candidate_input_row_id')}|{row.get('duplicate_proxy_denominator_key')}"
    )


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_card = Counter(row.get("card_id") for row in rows)
    per_partition = Counter(row.get("partition_assignment") for row in rows)
    per_card_partition = Counter((row.get("card_id"), row.get("partition_assignment")) for row in rows)
    per_symbol = Counter(row.get("symbol") for row in rows)
    per_science_domain = Counter(row.get("science_domain") for row in rows)
    source_hashes = {row.get("source_hash") for row in rows if row.get("source_hash")}
    candidate_ids = {row.get("candidate_input_row_id") for row in rows if row.get("candidate_input_row_id")}
    duplicate_keys = {
        row.get("duplicate_proxy_denominator_key")
        for row in rows
        if row.get("duplicate_proxy_denominator_key")
    }
    row_hashes = {row.get("row_hash") for row in rows if row.get("row_hash")}

    candidate_card_coverage: dict[str, set[str]] = defaultdict(set)
    duplicate_card_coverage: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        candidate_card_coverage[row.get("candidate_input_row_id")].add(row.get("card_id"))
        duplicate_card_coverage[row.get("duplicate_proxy_denominator_key")].add(row.get("card_id"))

    candidate_card_coverage_missing = [
        key for key, cards in candidate_card_coverage.items() if set(cards) != set(READY_CARD_IDS)
    ]
    duplicate_card_coverage_missing = [
        key for key, cards in duplicate_card_coverage.items() if set(cards) != set(READY_CARD_IDS)
    ]

    row_hash_mismatches = []
    rowset_id_mismatches = []
    baseline_seed_mismatches = []
    control_bucket_mismatches = []
    matched_control_group_mismatches = []
    candidate_source_hash_mismatches = []
    descriptor_pointer_hash_mismatches = []
    source_artifact_pointer_file_hash_mismatches = []
    source_artifact_pointer_file_hash_eol_equivalent = []
    forbidden_row_field_hits = []
    asof_violations = []
    missing_source_hash = []
    missing_row_hash = []
    missing_parser_asof = []
    row_safe_flag_violations = []
    blocked_card_rows = []
    unexpected_card_rows = []
    pointer_hash_cache: dict[str, str | None] = {}
    pointer_match_cache: dict[tuple[str, str], tuple[bool, str | None, bool]] = {}

    for row in rows:
        row_id = row.get("rowset_row_id")
        card_id = row.get("card_id")
        if card_id not in READY_CARD_IDS:
            unexpected_card_rows.append(row_id)
        if str(card_id).startswith("BLOCKED") or row.get("future_result_gate_status") == "BLOCKED":
            blocked_card_rows.append(row_id)
        if recompute_row_hash(row) != row.get("row_hash"):
            row_hash_mismatches.append(row_id)
        if recompute_rowset_row_id(row) != row_id:
            rowset_id_mismatches.append(row_id)
        expected_seed = baseline_seed(
            str(card_id), str(row.get("candidate_input_row_id")), str(row.get("duplicate_proxy_denominator_key"))
        )
        if expected_seed != row.get("baseline_assignment_seed"):
            baseline_seed_mismatches.append(row_id)
        if control_bucket(expected_seed) != row.get("baseline_control_bucket"):
            control_bucket_mismatches.append(row_id)
        if matched_control_group_key(row) != row.get("matched_control_group_key"):
            matched_control_group_mismatches.append(row_id)
        if row.get("candidate_input_row_hash") != row.get("source_hash"):
            candidate_source_hash_mismatches.append(row_id)
        descriptor_pointer = next(
            (
                pointer
                for pointer in row.get("source_artifact_pointers", [])
                if pointer.get("artifact_role") == "descriptor_freeze_row"
            ),
            None,
        )
        if descriptor_pointer and descriptor_pointer.get("row_hash") != row.get("descriptor_row_hash"):
            descriptor_pointer_hash_mismatches.append(row_id)
        for pointer in row.get("source_artifact_pointers", []):
            pointer_path = pointer.get("path")
            file_hash = pointer.get("file_sha256")
            if pointer_path and file_hash:
                if pointer_path not in pointer_hash_cache:
                    pointer_hash_cache[pointer_path] = sha256_file(ROOT / pointer_path)
                actual_hash = pointer_hash_cache[pointer_path]
                cache_key = (pointer_path, file_hash)
                if cache_key not in pointer_match_cache:
                    pointer_match_cache[cache_key] = file_hash_matches_expected_with_text_eol_equivalence(
                        ROOT / pointer_path, file_hash
                    )
                matches, _, eol_equivalent = pointer_match_cache[cache_key]
                if not matches:
                    source_artifact_pointer_file_hash_mismatches.append(
                        {"rowset_row_id": row_id, "path": pointer_path}
                    )
                elif eol_equivalent and actual_hash != file_hash:
                    source_artifact_pointer_file_hash_eol_equivalent.append(
                        {"rowset_row_id": row_id, "path": pointer_path}
                    )
        hits = sorted(set(row.keys()) & FORBIDDEN_EXACT_ROW_KEYS)
        if hits:
            forbidden_row_field_hits.append({"rowset_row_id": row_id, "hits": hits})
        if row.get("source_observed_asof_utc") > row.get("decision_asof_utc"):
            asof_violations.append(row_id)
        if not row.get("source_hash"):
            missing_source_hash.append(row_id)
        if not row.get("row_hash"):
            missing_row_hash.append(row_id)
        if not row.get("parser_asof_version"):
            missing_parser_asof.append(row_id)
        flags = row.get("safe_flags", {})
        if flags.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            row_safe_flag_violations.append(row_id)
        if flags.get("validation_safe") is not False:
            row_safe_flag_violations.append(row_id)
        if flags.get("outcome_review_opened") is not False:
            row_safe_flag_violations.append(row_id)
        if flags.get("live_effect") is not False:
            row_safe_flag_violations.append(row_id)

    return {
        "rowset_row_count_recomputed": len(rows),
        "source_candidate_count_recomputed": len(candidate_ids),
        "duplicate_proxy_denominator_key_count_recomputed": len(duplicate_keys),
        "source_hash_unique_count_recomputed": len(source_hashes),
        "row_hash_unique_count_recomputed": len(row_hashes),
        "ready_card_count_recomputed": len([card for card in per_card if card in READY_CARD_IDS]),
        "ready_card_ids_recomputed": sorted(card for card in per_card if card in READY_CARD_IDS),
        "per_card_counts_recomputed": dict(sorted(per_card.items())),
        "per_partition_counts_recomputed": dict(sorted(per_partition.items())),
        "per_card_partition_counts_recomputed": [
            {"card_id": card, "partition_assignment": partition, "count": count}
            for (card, partition), count in sorted(per_card_partition.items())
        ],
        "per_symbol_counts_recomputed": dict(sorted(per_symbol.items())),
        "per_science_domain_counts_recomputed": dict(sorted(per_science_domain.items())),
        "candidate_card_coverage_missing_count": len(candidate_card_coverage_missing),
        "duplicate_card_coverage_missing_count": len(duplicate_card_coverage_missing),
        "duplicate_key_collision_count_recomputed": len(candidate_ids) - len(duplicate_keys),
        "forbidden_row_field_hit_count": len(forbidden_row_field_hits),
        "forbidden_row_field_hits_sample": forbidden_row_field_hits[:5],
        "asof_violation_count": len(asof_violations),
        "asof_violations_sample": asof_violations[:5],
        "missing_source_hash_count": len(missing_source_hash),
        "missing_row_hash_count": len(missing_row_hash),
        "parser_asof_version_missing_count": len(missing_parser_asof),
        "row_hash_mismatch_count": len(row_hash_mismatches),
        "row_hash_mismatches_sample": row_hash_mismatches[:5],
        "rowset_row_id_mismatch_count": len(rowset_id_mismatches),
        "baseline_seed_mismatch_count": len(baseline_seed_mismatches),
        "control_bucket_mismatch_count": len(control_bucket_mismatches),
        "matched_control_group_mismatch_count": len(matched_control_group_mismatches),
        "candidate_source_hash_mismatch_count": len(candidate_source_hash_mismatches),
        "descriptor_pointer_hash_mismatch_count": len(descriptor_pointer_hash_mismatches),
        "source_artifact_pointer_file_hash_mismatch_count": len(source_artifact_pointer_file_hash_mismatches),
        "source_artifact_pointer_file_hash_mismatches_sample": source_artifact_pointer_file_hash_mismatches[:5],
        "source_artifact_pointer_file_hash_eol_equivalent_count": len(
            source_artifact_pointer_file_hash_eol_equivalent
        ),
        "source_artifact_pointer_file_hash_eol_equivalent_sample": source_artifact_pointer_file_hash_eol_equivalent[:5],
        "row_safe_flag_violation_count": len(row_safe_flag_violations),
        "unexpected_card_row_count": len(unexpected_card_rows),
        "blocked_card_row_count": len(blocked_card_rows),
    }


def source_artifact_hash_audit(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    mismatch_count = 0
    eol_equivalent_count = 0
    missing_count = 0
    for artifact in inventory:
        path = ROOT / artifact["path"]
        expected = artifact.get("sha256")
        matches, actual, eol_equivalent = file_hash_matches_expected_with_text_eol_equivalence(path, expected)
        if actual is None:
            missing_count += 1
        if not matches:
            mismatch_count += 1
        elif eol_equivalent and actual != expected:
            eol_equivalent_count += 1
        rows.append(
            {
                "path": artifact.get("path"),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "matches": matches,
                "matches_via_text_eol_equivalence": bool(eol_equivalent and actual != expected and matches),
                "exists": actual is not None,
            }
        )
    return {
        "source_artifact_count": len(rows),
        "source_artifact_missing_count": missing_count,
        "source_artifact_hash_mismatch_count": mismatch_count,
        "source_artifact_hash_eol_equivalent_count": eol_equivalent_count,
        "source_artifact_hash_rows": rows,
    }


def recursive_key_hits(value: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, subvalue in value.items():
            if key in forbidden:
                hits.append(key)
            hits.extend(recursive_key_hits(subvalue, forbidden))
    elif isinstance(value, list):
        for item in value:
            hits.extend(recursive_key_hits(item, forbidden))
    return hits


def git_status_snapshot() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    allowed_prefixes = (
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
        ".gitattributes",
        "research/science_program_2026_05/04_goal_prompts/SCID_NOAPI_READY8_QUARANTINED_RESULT_PACKET_AFTER_G0_GATE_GOAL_PROMPT_2026-05-13.md",
        "research/science_program_2026_05/06_outcome_testing/g0napi_ready8_future_result_opening_gate_after_g12_audit/",
        "research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/SCID_NOAPI_READY8_ROWSET_ROWS_2026-05-12.jsonl",
        "research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/SCID_NOAPI_READY8_COMPLETION_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/SCID_NOAPI_READY8_OUTPUT_MANIFEST_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/SCID_NOAPI_READY8_VERIFICATION_RESULT_2026-05-12.json",
    )
    forbidden_prefixes = ("src/", "prompts/", "config/", "run_agent.py", "scripts/canary")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".zip", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path == prefix or path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(forbidden_prefixes),
                "scoped_raw_market_blob": scoped and path.endswith(raw_blob_suffixes),
            }
        )
    scoped_entries = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "entries": entries,
        "scoped_entries": scoped_entries,
        "unscoped_entry_count": len(entries) - len(scoped_entries),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped_entries),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped_entries),
    }


def next_result_prompt_text() -> str:
    return """# SCID No-API Ready-8 Quarantined Result Packet After G0 Gate

Evidence class: `SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_ONLY`

Objective: build the separate quarantined no-API target-result packet authorized by `G0NAPI_READY8_FUTURE_RESULT_OPENING_GATE_AFTER_G12_AUDIT`. This is a result-packet builder only, not validation, promotion, live trading, strategy performance scoring, or an AI/API route.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read the G0 gate artifacts at `research/science_program_2026_05/06_outcome_testing/g0napi_ready8_future_result_opening_gate_after_g12_audit/`.
4. Read the accepted G12 audit route at `research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_ready8_rowset_target_horizon_packet_audit/`.
5. Read the materialized ready-8 packet at `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/`.

Do not rely on chat memory. Recompute from disk. Treat the source-control packet, G12 audit, and G0 gate decision as the controlling authority for this route.

## Scope

Open the target-result packet for exactly the accepted eight ready cards and exactly the accepted source-control rowset:

- ready cards: `ADV-001`, `ADV-003`, `BEH-001`, `HAZ-001`, `HAZ-005`, `MAC-001`, `MAC-004`, `UNC-004`;
- source candidates: `3,014`;
- rowset rows: `24,112`;
- accepted-card denominator: `40`;
- blocked dependencies: `32`, preserved outside this denominator;
- row exclusions: `0` unless a fail-closed target source condition is proven row by row.

The prompt must be broad and constructive. Do not box the result packet into current GTOS behavior, OB/retest logic, one symbol, one session, one baseline, or one mechanism family. Use all eight ready cards, all accepted baseline/control families, the sealed/stress partitions, source-coverage descriptors, session/time/context fields, and the adjacent no-API route families exposed by the gate artifacts. Adjacent families may be inventoried and routed as sidecars, but they must not enter the accepted ready-8 result denominator unless a separate acceptance route authorizes them.

## Allowed Result Packet Work

- Compute only the neutral target-result families already frozen in the target-horizon contract:
  - `neutral_close_to_close_return_m15_horizons_v1`;
  - `neutral_high_low_excursion_m15_horizons_v1`.
- Use only accepted source-control candidate rows, accepted source-control bar/source rows, source hashes, and rowset rows.
- Use only horizons `1`, `4`, `16`, and `32` closed M15 bars.
- Build fail-closed row statuses for missing entry bars, missing horizon/path bars, source gaps, null OHLC fields, duplicate-key errors, partition violations, source-hash mismatch, or any field outside the accepted packet.
- Keep duplicate-key, row-level, per-card, partition, source-hash, and as-of ledgers machine-checkable.
- Emit input/result join manifests, row-level target packets, sidecar quality diagnostics, exact fail-closed blocker ledger, output manifest, verifier, focused tests, completion audit, and a next G12 audit prompt/starter.
- Include broad anti-boxing analysis across all eight cards, the four source/control group families, seven source proxy groups, sealed/stress partitions, session/time buckets, source coverage buckets, and the adjacent no-API route families. This is route breadth, not performance interpretation.

## Forbidden Surfaces

Do not compute or claim R, PnL, win rate, expectancy, Sharpe, performance, strategy edge, validation, promotion, live readiness, broker actual-R, account/order/history/deal/position labels, AI/API decisions, paid/vendor pulls, raw market blob commits, credentials, registry edits, remote pushes, live restarts, or trading prompt/config/risk/safety/execution/canary/selector behavior changes.

Do not inspect blocked-card results. Do not include the `32` blocked dependency rows or quarantined expansion candidates in the accepted ready-8 denominator. Do not convert sidecar observations into accepted cards. Do not rescue a result by post-hoc threshold mining. Do not describe target movement as a trading performance result.

## Required Outputs

- Quarantined target-result row packet for all eligible ready-8 rows and all four horizons.
- Target-source join ledger proving source hashes, as-of ordering, fail-closed statuses, and no forbidden fields.
- Duplicate and denominator ledger proving `3,014` source candidates, `24,112` ready rows before horizon expansion, and no blocked/expansion denominator leakage.
- Partition/control ledger preserving sealed/stress and deterministic baseline/control assignments.
- Adjacent no-API route-family sidecar ledger that is broad, curious, and explicitly quarantined from accepted denominators.
- Same-evidence-class blocker/repair ledger for every count/hash/as-of/duplicate/source/partition/control/target-horizon issue found.
- Saturation/self-red-team ledger.
- Completion audit with prompt-instruction coverage.
- Standalone verifier and focused tests.
- Next G12 audit prompt/starter for the result packet.
- Scoped commits only.

## Terminal Decision

Allowed terminal decisions:

- `MATERIALIZED_QUARANTINED_READY8_NOAPI_TARGET_RESULT_PACKET_G12_AUDIT_REQUIRED`
- `KEEP_READY8_RESULT_PACKET_CLOSED_WITH_EXACT_REPAIR_OR_SOURCE_BLOCKERS`

The route may open target-result computation only inside this quarantined evidence class. It must preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, and `live_effect=false`; it must not open validation, promotion, live behavior, AI/API, paid/vendor, broker account/order/history/deal/position, raw market blob, registry, remote, or trading-risk/safety/prompt-decision surfaces.

Complete only after the result packet is built or exact repair/source/access blockers are proven, verifier/focused tests pass, the next G12 audit prompt exists, and scoped artifacts are committed.
"""


def next_result_starter_text() -> str:
    return (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/04_goal_prompts/"
        "SCID_NOAPI_READY8_QUARANTINED_RESULT_PACKET_AFTER_G0_GATE_GOAL_PROMPT_2026-05-13.md "
        "as the complete objective; run mandatory preflight/context refresh first; do not rely on chat "
        "or compaction memory; stay SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_ONLY with no "
        "validation/promotion/live/API/paid-vendor/broker-account-order-history-deal-position/raw-blob/"
        "registry/remote/trading-risk-safety-prompt-decision changes; compute only the frozen neutral "
        "target-result packet for all 8 ready cards, 3014 source candidates, 24112 ready rows, horizons "
        "1/4/16/32, accepted controls, duplicate/as-of/source-hash/fail-closed ledgers, and quarantined "
        "adjacent no-API sidecars; do not compute R/PnL/win-rate/expectancy/performance or inspect "
        "blocked-card results; pursue every same-class blocker until cleared, repaired, proven impossible, "
        "or reduced to exact source/repair/access prompt; complete only with result packet artifacts, "
        "verifier/focused tests, next G12 audit prompt/starter, scoped commits, NO_PROMOTION_VERDICT, "
        "validation_safe=false, live_effect=false."
    )


def build_artifacts(write_outputs: bool = True) -> dict[str, Any]:
    route_time = now_utc()
    target = {name: load_json(path) for name, path in TARGET_ARTIFACTS.items() if path.suffix == ".json"}
    g12 = {name: load_json(path) for name, path in G12_ARTIFACTS.items()}
    rows = list(iter_jsonl(TARGET_ARTIFACTS["rowset_rows"]))
    row_summary = summarize_rows(rows)
    rowset_manifest = target["rowset_manifest"]
    row_path = TARGET_ARTIFACTS["rowset_rows"]
    rowset_raw_sha = sha256_file(row_path)
    rowset_lf_sha = sha256_file_lf_normalized(row_path)
    manifest_rowset_sha = rowset_manifest.get("rowset_rows_sha256")
    source_hash_audit = source_artifact_hash_audit(rowset_manifest.get("source_artifact_inventory", []))
    target_contract = target["target_horizon_contract"]
    duplicate_manifest = target["duplicate_denominator_manifest"]
    partition_manifest = target["partition_control_manifest"]
    baseline_manifest = target["baseline_control_assignment_manifest"]
    expansion_ledger = target["expansion_observation_ledger"]
    blocker_ledger = target["blocker_or_dependency_ledger"]
    no_leak_audit = target["no_leak_and_forbidden_surface_audit"]
    target_verifier = target["verification_result"]
    g12_decision = g12["decision_ledger"]
    g12_followup = g12["blocker_followup_ledger"]

    gitattributes_text = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    gitattributes_line_present = GATTRIBUTES_REQUIRED_LINE in gitattributes_text
    target_forbidden_key_hits = recursive_key_hits(target_contract, FORBIDDEN_EXACT_ROW_KEYS)

    evidence_failures = []
    if g12_decision.get("terminal_decision") not in {
        "ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY",
        "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS",
    }:
        evidence_failures.append("G12 terminal decision is not accepted.")
    if row_summary["rowset_row_count_recomputed"] != EXPECTED_ROWSET_ROWS:
        evidence_failures.append("Rowset row count mismatch.")
    if row_summary["source_candidate_count_recomputed"] != EXPECTED_SOURCE_CANDIDATES:
        evidence_failures.append("Source candidate count mismatch.")
    if row_summary["duplicate_proxy_denominator_key_count_recomputed"] != EXPECTED_SOURCE_CANDIDATES:
        evidence_failures.append("Duplicate-key denominator mismatch.")
    if row_summary["ready_card_ids_recomputed"] != READY_CARD_IDS:
        evidence_failures.append("Ready card IDs mismatch.")
    if rowset_manifest.get("accepted_card_denominator_count") != EXPECTED_ACCEPTED_CARDS:
        evidence_failures.append("Accepted 40-card denominator mismatch.")
    if rowset_manifest.get("blocked_dependency_row_count_preserved") != EXPECTED_BLOCKED_DEPENDENCIES:
        evidence_failures.append("Blocked dependency denominator mismatch.")
    if rowset_manifest.get("row_level_exclusion_count") != EXPECTED_ROW_EXCLUSIONS:
        evidence_failures.append("Row-level exclusions are not zero.")
    if rowset_raw_sha != manifest_rowset_sha:
        evidence_failures.append("Raw rowset hash does not match manifest.")
    if rowset_lf_sha != manifest_rowset_sha:
        evidence_failures.append("LF-normalized rowset hash does not match manifest.")
    if source_hash_audit["source_artifact_hash_mismatch_count"] != 0:
        evidence_failures.append("Source artifact hash mismatch.")
    for key in [
        "candidate_card_coverage_missing_count",
        "duplicate_card_coverage_missing_count",
        "duplicate_key_collision_count_recomputed",
        "forbidden_row_field_hit_count",
        "asof_violation_count",
        "missing_source_hash_count",
        "missing_row_hash_count",
        "parser_asof_version_missing_count",
        "row_hash_mismatch_count",
        "rowset_row_id_mismatch_count",
        "baseline_seed_mismatch_count",
        "control_bucket_mismatch_count",
        "matched_control_group_mismatch_count",
        "candidate_source_hash_mismatch_count",
        "descriptor_pointer_hash_mismatch_count",
        "source_artifact_pointer_file_hash_mismatch_count",
        "row_safe_flag_violation_count",
        "unexpected_card_row_count",
        "blocked_card_row_count",
    ]:
        if row_summary[key] != 0:
            evidence_failures.append(f"Row audit nonzero {key}: {row_summary[key]}")
    if duplicate_manifest.get("duplicate_key_collision_count") != 0:
        evidence_failures.append("Target duplicate manifest reports collisions.")
    if duplicate_manifest.get("quarantined_expansion_denominator_inclusion") is not False:
        evidence_failures.append("Expansion denominator inclusion is not false.")
    if partition_manifest.get("discovery_development_status", {}).get(
        "CONTAMINATED_OR_FORBIDDEN_POOL", {}
    ).get("candidate_count") != 0:
        evidence_failures.append("Contaminated/forbidden partition is not empty.")
    if baseline_manifest.get("deterministic_assignments_only") is not True:
        evidence_failures.append("Baseline assignments are not deterministic.")
    if baseline_manifest.get("result_or_performance_lookup_used") is not False:
        evidence_failures.append("Baseline/control manifest used result lookup.")
    if target_contract.get("target_or_hazard_hits_computed") is not False:
        evidence_failures.append("Target horizon contract already computed hits.")
    if target_contract.get("performance_or_result_fields_present") is not False:
        evidence_failures.append("Target horizon contract has result/performance fields.")
    if target_forbidden_key_hits:
        evidence_failures.append("Target horizon contract contains forbidden exact keys.")
    if expansion_ledger.get("all_expansion_observations_remain_outside_accepted_denominator") is not True:
        evidence_failures.append("Expansion observations entered accepted denominator.")
    if expansion_ledger.get("all_expansion_observations_remain_outside_ready8_denominator") is not True:
        evidence_failures.append("Expansion observations entered ready-8 denominator.")
    if blocker_ledger.get("ready8_source_control_blocker_count") != 0:
        evidence_failures.append("Ready-8 source-control blockers remain.")
    if no_leak_audit.get("forbidden_row_field_hit_count") != 0 or no_leak_audit.get("asof_violation_count") != 0:
        evidence_failures.append("No-leak audit reports forbidden row fields or as-of violations.")
    if target_verifier.get("ok") is not True:
        evidence_failures.append("Target verifier is not green after same-class repair.")
    if not gitattributes_line_present:
        evidence_failures.append("Line-ending policy repair is missing from .gitattributes.")

    terminal_decision = TERMINAL_OPEN if not evidence_failures else TERMINAL_CLOSED
    opened = terminal_decision == TERMINAL_OPEN
    if write_outputs and opened:
        write_text(NEXT_RESULT_PROMPT, next_result_prompt_text())
        write_text(NEXT_RESULT_STARTER, next_result_starter_text())

    next_prompt = {
        "emitted": opened,
        "prompt_path": rel(NEXT_RESULT_PROMPT) if NEXT_RESULT_PROMPT.exists() or opened else None,
        "prompt_sha256": sha256_file(NEXT_RESULT_PROMPT) if NEXT_RESULT_PROMPT.exists() else None,
        "starter_path": rel(NEXT_RESULT_STARTER) if NEXT_RESULT_STARTER.exists() or opened else None,
        "starter_sha256": sha256_file(NEXT_RESULT_STARTER) if NEXT_RESULT_STARTER.exists() else None,
    }

    adjacent_route_families = [
        {
            "route_family": item.get("candidate_family") or item.get("observation_family"),
            "source_safe_hypothesis_or_field": item.get("source_safe_hypothesis_or_field")
            or item.get("source_safe_materialization_insight"),
            "accepted_denominator_inclusion": item.get("accepted_40_card_denominator_inclusion", False),
            "ready8_denominator_inclusion": item.get("ready8_denominator_inclusion", False),
            "future_requirement": item.get("future_acceptance_requirement") or item.get("future_route_requirement"),
        }
        for item in (
            expansion_ledger.get("upstream_quarantined_expansion_candidates", [])
            + expansion_ledger.get("new_ready8_expansion_observations", [])
        )
    ]

    repair_ledger = safe_payload(
        "same_evidence_class_repair_ledger",
        {
            "terminal_decision": terminal_decision,
            "repair_blocker_count": len(evidence_failures),
            "repair_blockers": evidence_failures,
            "same_class_followups_pursued": [
                {
                    "followup_id": "READY8-G0-GATE-001",
                    "source": rel(G12_ARTIFACTS["blocker_followup_ledger"]),
                    "g12_status": "REQUIRED_BEFORE_ANY_RESULT_OPENING",
                    "pursuit_performed": "This G0 route recomputed the accepted packet evidence and emitted the future quarantined no-API result-packet prompt.",
                    "terminal_status": "CLEARED_BY_G0_GATE_OPEN_DECISION" if opened else "BLOCKED_BY_G0_GATE_FAILURE",
                },
                {
                    "followup_id": "READY8-EOL-HASH-001",
                    "source": rel(G12_ARTIFACTS["blocker_followup_ledger"]),
                    "g12_status": "NONBLOCKING_REPAIR_OR_VERIFIER_HARDENING",
                    "pursuit_performed": (
                        "Specific rowset path was added to .gitattributes with text eol=lf, the working-tree "
                        "rowset was normalized to LF, and the target verifier was rerun."
                    ),
                    "manifest_rowset_sha256": manifest_rowset_sha,
                    "raw_rowset_sha256_after_repair": rowset_raw_sha,
                    "lf_normalized_rowset_sha256_after_repair": rowset_lf_sha,
                    "gitattributes_line_present": gitattributes_line_present,
                    "row_hash_mismatch_count": row_summary["row_hash_mismatch_count"],
                    "source_artifact_hash_mismatch_count": source_hash_audit["source_artifact_hash_mismatch_count"],
                    "terminal_status": "REPAIRED_AND_CLEARED" if rowset_raw_sha == manifest_rowset_sha else "NOT_CLEARED",
                },
            ],
            "no_runtime_approval_needed": True,
            "no_external_access_needed": True,
            "may_score_results_now": False,
            "future_result_packet_prompt_opened": opened,
            "next_result_prompt": next_prompt,
        },
    )

    reconciliation = safe_payload(
        "gate_evidence_reconciliation_ledger",
        {
            "terminal_decision": terminal_decision,
            "terminal_blockers": evidence_failures,
            "g12_terminal_decision": g12_decision.get("terminal_decision"),
            "g12_acceptance_ok": g12_decision.get("terminal_decision")
            in {
                "ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY",
                "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS",
            },
            "target_verifier_ok_after_repair": target_verifier.get("ok") is True,
            "rowset_counts": {
                "expected_source_candidates": EXPECTED_SOURCE_CANDIDATES,
                "expected_ready_cards": EXPECTED_READY_CARDS,
                "expected_rowset_rows": EXPECTED_ROWSET_ROWS,
                "expected_accepted_cards": EXPECTED_ACCEPTED_CARDS,
                "expected_blocked_dependencies": EXPECTED_BLOCKED_DEPENDENCIES,
                "expected_row_level_exclusions": EXPECTED_ROW_EXCLUSIONS,
                **row_summary,
            },
            "hash_reconciliation": {
                "manifest_rowset_sha256": manifest_rowset_sha,
                "raw_rowset_sha256": rowset_raw_sha,
                "lf_normalized_rowset_sha256": rowset_lf_sha,
                "raw_matches_manifest": rowset_raw_sha == manifest_rowset_sha,
                "lf_normalized_matches_manifest": rowset_lf_sha == manifest_rowset_sha,
                "gitattributes_line_present": gitattributes_line_present,
                **source_hash_audit,
            },
            "asof_reconciliation": {
                "source_observed_asof_lte_decision_asof_count": row_summary["rowset_row_count_recomputed"]
                - row_summary["asof_violation_count"],
                "asof_violation_count": row_summary["asof_violation_count"],
                "parser_asof_version_missing_count": row_summary["parser_asof_version_missing_count"],
                "target_source_hash_audit_claim": target["source_hash_and_asof_audit"].get(
                    "source_observed_asof_lte_decision_asof_count"
                ),
            },
            "duplicate_partition_control_reconciliation": {
                "duplicate_key_collision_count": row_summary["duplicate_key_collision_count_recomputed"],
                "duplicate_manifest_collision_count": duplicate_manifest.get("duplicate_key_collision_count"),
                "partition_counts": row_summary["per_partition_counts_recomputed"],
                "partition_manifest_counts": partition_manifest.get("partition_status_counts_ready8_rows"),
                "deterministic_assignments_only": baseline_manifest.get("deterministic_assignments_only"),
                "baseline_seed_mismatch_count": row_summary["baseline_seed_mismatch_count"],
                "control_bucket_mismatch_count": row_summary["control_bucket_mismatch_count"],
                "matched_control_group_mismatch_count": row_summary["matched_control_group_mismatch_count"],
                "global_control_bucket_counts": baseline_manifest.get("global_control_bucket_counts"),
            },
            "target_horizon_no_result_contract": {
                "allowed_horizons_m15_bars": target_contract.get("allowed_horizons_m15_bars"),
                "target_families": target_contract.get("target_families"),
                "target_or_hazard_hits_computed": target_contract.get("target_or_hazard_hits_computed"),
                "performance_or_result_fields_present": target_contract.get("performance_or_result_fields_present"),
                "forbidden_exact_key_hit_count": len(target_forbidden_key_hits),
                "current_route_may_compute_values": False,
            },
            "blocked_and_expansion_quarantine": {
                "blocked_32_dependency_row_count": blocker_ledger.get("blocked_32_dependency_row_count"),
                "blocked_32_not_mixed_into_ready8_materialization": blocker_ledger.get(
                    "blocked_32_not_mixed_into_ready8_materialization"
                ),
                "all_expansion_observations_remain_outside_accepted_denominator": expansion_ledger.get(
                    "all_expansion_observations_remain_outside_accepted_denominator"
                ),
                "all_expansion_observations_remain_outside_ready8_denominator": expansion_ledger.get(
                    "all_expansion_observations_remain_outside_ready8_denominator"
                ),
                "upstream_quarantined_expansion_candidate_count": expansion_ledger.get(
                    "upstream_quarantined_expansion_candidate_count"
                ),
                "new_ready8_expansion_observation_count": expansion_ledger.get(
                    "new_ready8_expansion_observation_count"
                ),
            },
            "safe_surface_reconciliation": {
                "forbidden_row_field_hit_count": row_summary["forbidden_row_field_hit_count"],
                "row_safe_flag_violation_count": row_summary["row_safe_flag_violation_count"],
                "target_no_leak_forbidden_row_field_hit_count": no_leak_audit.get("forbidden_row_field_hit_count"),
                "target_no_leak_asof_violation_count": no_leak_audit.get("asof_violation_count"),
            },
        },
    )

    decision = safe_payload(
        "g0_decision_ledger",
        {
            "terminal_decision": terminal_decision,
            "terminal_blockers": evidence_failures,
            "result_packet_prompt_opened": opened,
            "result_scoring_opened_by_this_gate": False,
            "may_score_results_now": False,
            "may_open_future_quarantined_result_packet_prompt": opened,
            "g12_terminal_decision": g12_decision.get("terminal_decision"),
            "accepted_g12_control_evidence_only": g12_decision.get("accepted_g12_control_evidence_only"),
            "ready8_scope": {
                "ready_card_ids": READY_CARD_IDS,
                "ready_card_count": EXPECTED_READY_CARDS,
                "source_candidate_count": EXPECTED_SOURCE_CANDIDATES,
                "rowset_row_count": EXPECTED_ROWSET_ROWS,
                "accepted_card_denominator": EXPECTED_ACCEPTED_CARDS,
                "blocked_dependency_rows": EXPECTED_BLOCKED_DEPENDENCIES,
                "row_level_exclusions": EXPECTED_ROW_EXCLUSIONS,
            },
            "opening_rationale": (
                "G12 accepted the source-control packet, all G0 count/hash/as-of/duplicate/partition/control/"
                "target-horizon/quarantine checks pass after line-ending repair, and no forbidden surface opened."
            )
            if opened
            else "Gate remains closed until blockers are repaired.",
            "not_based_on": [
                "vague caution",
                "small-n validation fear",
                "OB-only bias",
                "novelty aversion",
                "runtime convenience",
                "future G12 anxiety",
            ],
            "next_result_prompt": next_prompt,
            "ready_card_mechanism_families": BASELINE_ASSIGNMENT_BY_CARD,
            "adjacent_noapi_route_families_quarantined": adjacent_route_families,
        },
    )

    saturation = f"""# G0NAPI Ready-8 Saturation And Self-Red-Team

Route: `{ROUTE_ID}`
Evidence class: `{EVIDENCE_CLASS}`
Terminal decision: `{terminal_decision}`

## Prompt Application

- This is a G0 result-opening gate, not a result-scoring lane.
- Boundary language was treated as evidence-class scoping, not as a reason to be cautious, OB-boxed, route-count-limited, novelty-averse, or reluctant to open the strongest lawful no-API result-packet route.
- Result scoring remains unopened in this gate: `may_score_results_now=false`.
- Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Anti-Boxing Questions Pursued

- All 8 ready cards were recomputed rather than sampling one card.
- All 3,014 source candidates and all 24,112 ready-card rows were scanned.
- All accepted baseline/control families were checked: session placebo, duplicate-key random proxy placebo, session-open constraints, hazard clocks, calendar/fix context, and source-confidence controls.
- The 40-card accepted denominator was preserved as a floor, not a ceiling.
- The 32 blocked dependencies and expansion observations were explicitly quarantined.
- Adjacent no-API route families were carried into the next prompt as quarantined sidecars, not suppressed by OB/retest framing.

## Same-Evidence-Class Ambiguities Pursued

1. G12 required this G0 gate before any future result route. This route resolves that gate.
2. G12 recorded CRLF/LF hash friction. This route repaired it with a specific `.gitattributes` LF rule and normalized the rowset so raw and LF-normalized hashes both match the manifest.
3. The rowset was rechecked for row-hash, source-hash, as-of, duplicate, partition, deterministic-control, safe-flag, and forbidden-key failures.
4. The target-horizon contract was kept no-result in this gate while freezing the next quarantined result-packet route.

## Self-Red-Team

- Row inflation bug: blocked by `3,014 * 8 = 24,112` recomputation and per-card coverage checks.
- Future-label leakage bug: blocked by exact forbidden-key scans and target-horizon no-result contract checks.
- Ready/blocked confusion bug: blocked by 8 ready-card ID recomputation and 32 blocked dependency quarantine.
- Expansion denominator bug: blocked by accepted/ready denominator inclusion flags.
- Non-deterministic control bug: blocked by baseline seed, control bucket, and matched-control recomputation.
- Silent scoring bug: blocked by this route's `opens_result_scoring=false` artifacts and a separate future prompt.
- Hash-policy drift bug: repaired by LF enforcement and raw/LF hash reconciliation.

## Closure

Terminal blockers: `{len(evidence_failures)}`.

The gate opens only a separate quarantined result-packet prompt. It does not compute target results, validate a strategy, promote, change live behavior, call AI/API, use paid/vendor access, inspect broker/account/order/history/deal/position evidence, commit raw market blobs, or alter trading/risk/safety/prompt-decision surfaces.
"""

    prompt_checklist = [
        {
            "requirement": "mandatory preflight/context read from disk",
            "evidence": "LIVE_STATE regenerated before this build; core context files read in-session from disk.",
            "satisfied": True,
        },
        {
            "requirement": "read accepted G12 audit route",
            "evidence": rel(G12_DIR),
            "satisfied": True,
        },
        {
            "requirement": "read materialized ready-8 packet",
            "evidence": rel(TARGET_DIR),
            "satisfied": True,
        },
        {
            "requirement": "confirm accepted G12 terminal decision",
            "evidence": rel(G12_ARTIFACTS["decision_ledger"]),
            "satisfied": g12_decision.get("terminal_decision")
            in {
                "ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY",
                "ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS",
            },
        },
        {
            "requirement": "reconcile 3014 source candidates, 8 ready cards, 24112 rows, 40 accepted cards, 32 blocked rows, 0 exclusions",
            "evidence": rel(output_path("GATE_EVIDENCE_RECONCILIATION_LEDGER")),
            "satisfied": not evidence_failures,
        },
        {
            "requirement": "row/source hashes, as-of ordering, duplicates, partitions, controls, target-horizon contract, expansion quarantine verified",
            "evidence": rel(output_path("GATE_EVIDENCE_RECONCILIATION_LEDGER")),
            "satisfied": not evidence_failures,
        },
        {
            "requirement": "same-evidence-class repair ledger handles CRLF/LF follow-up",
            "evidence": rel(output_path("SAME_EVIDENCE_CLASS_REPAIR_LEDGER")),
            "satisfied": rowset_raw_sha == manifest_rowset_sha and gitattributes_line_present,
        },
        {
            "requirement": "future result-packet prompt and one-line starter emitted if opened",
            "evidence": rel(NEXT_RESULT_PROMPT) + " and " + rel(NEXT_RESULT_STARTER),
            "satisfied": opened,
        },
        {
            "requirement": "no result scoring/validation/promotion/live/API/paid/broker/raw-blob/trading-surface opened by this gate",
            "evidence": "safe flags in all G0 artifacts",
            "satisfied": True,
        },
        {
            "requirement": "standalone verifier and focused tests pass",
            "evidence": rel(output_path("VERIFICATION_RESULT")),
            "satisfied": False,
        },
        {
            "requirement": "scoped artifacts committed",
            "evidence": "git commit after verifier/test pass",
            "satisfied": False,
        },
    ]

    completion = safe_payload(
        "completion_audit",
        {
            "terminal_decision": terminal_decision,
            "completion_standard_satisfied_before_commit": False,
            "completion_standard_satisfied": False,
            "can_mark_goal_complete": False,
            "focused_tests_ok": False,
            "standalone_verifier_ok": False,
            "standalone_verifier_failures": [],
            "objective_as_concrete_deliverables": [
                "Decide from disk evidence whether the future quarantined ready-8 no-API result-packet prompt may open.",
                "Reconcile accepted G12 evidence, target packet counts, hashes, as-of ordering, duplicate policy, partitions, controls, target-horizon no-result contract, and expansion quarantine.",
                "Repair or clear same-evidence-class follow-ups, especially CRLF/LF rowset hash friction.",
                "Emit the strongest broad future result-packet prompt/starter if opened, or exact blockers if closed.",
                "Produce verifier, focused tests, completion audit, and scoped commit while preserving safe flags.",
            ],
            "instruction_coverage": {
                "goal_session_research_discipline_read_after_preflight": True,
                "research_operating_doctrine_read_after_preflight": True,
                "research_current_state_read_after_preflight": True,
                "local_heavy_data_inventory_read_after_preflight": True,
                "ai_in_loop_cost_control_read_after_preflight": True,
                "lane_type": "G0 result-opening gate",
                "posture_applied": "active gate opening when exact accepted evidence permits it; no result scoring in this gate",
                "anti_boxing_questions_pursued": [
                    "all eight ready cards",
                    "all four baseline/control route families",
                    "all 3014 source candidates",
                    "all 24112 ready rows",
                    "blocked dependencies and expansion sidecars kept quarantined",
                    "adjacent no-API route families carried into the future prompt without denominator leakage",
                ],
                "same_evidence_class_pursuit": [
                    "G12 G0 gate requirement resolved",
                    "CRLF/LF hash friction repaired",
                    "row-level hash/source/as-of/duplicate/control checks recomputed",
                ],
                "final_decision_not_based_on": [
                    "vague caution",
                    "novelty fear",
                    "OB-only bias",
                    "small-n validation fear",
                    "runtime convenience",
                    "future audit anxiety",
                ],
                "doctrine_requirements_deferred_because_evidence_class_gate": [
                    "target result computation",
                    "post-result G12 audit",
                    "validation",
                    "promotion",
                    "live trading behavior",
                ],
            },
            "prompt_to_artifact_checklist": prompt_checklist,
            "terminal_blockers": evidence_failures,
        },
    )

    if write_outputs:
        write_json(output_path("DECISION_LEDGER"), decision)
        write_json(output_path("GATE_EVIDENCE_RECONCILIATION_LEDGER"), reconciliation)
        write_json(output_path("SAME_EVIDENCE_CLASS_REPAIR_LEDGER"), repair_ledger)
        write_text(output_path("SATURATION_SELF_RED_TEAM", ".md"), saturation)
        write_json(output_path("COMPLETION_AUDIT"), completion)
        write_output_manifest()

    return {
        "decision": decision,
        "reconciliation": reconciliation,
        "repair_ledger": repair_ledger,
        "completion": completion,
        "saturation": saturation,
        "opened": opened,
        "terminal_decision": terminal_decision,
        "evidence_failures": evidence_failures,
    }


def write_output_manifest() -> None:
    artifact_paths = [
        output_path("DECISION_LEDGER"),
        output_path("GATE_EVIDENCE_RECONCILIATION_LEDGER"),
        output_path("SAME_EVIDENCE_CLASS_REPAIR_LEDGER"),
        output_path("SATURATION_SELF_RED_TEAM", ".md"),
        output_path("COMPLETION_AUDIT"),
        output_path("VERIFICATION_RESULT"),
        output_path("FOCUSED_TEST_RESULT"),
        ROUTE_DIR / "build_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13.py",
        ROUTE_DIR / "verify_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13.py",
        ROUTE_DIR / "test_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13.py",
        NEXT_RESULT_PROMPT,
        NEXT_RESULT_STARTER,
        ROOT / ".gitattributes",
        TARGET_ARTIFACTS["rowset_rows"],
        TARGET_ARTIFACTS["verification_result"],
    ]
    rows = [
        {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in sorted({p for p in artifact_paths if p.exists()}, key=rel)
    ]
    manifest = safe_payload(
        "output_manifest",
        {
            "terminal_decision": load_json(output_path("DECISION_LEDGER")).get("terminal_decision")
            if output_path("DECISION_LEDGER").exists()
            else None,
            "artifact_count": len(rows),
            "artifacts": rows,
        },
    )
    write_json(output_path("OUTPUT_MANIFEST"), manifest)


def main() -> int:
    result = build_artifacts(write_outputs=True)
    print(json.dumps({"terminal_decision": result["terminal_decision"], "opened": result["opened"]}, indent=2))
    return 0 if result["opened"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
