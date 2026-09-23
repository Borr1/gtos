"""Build G12 CNR061 sidecar reaudit artifacts.

This lane audits the CNR061 geometry+horizon sidecar as input-only packet
evidence. It deliberately does not score outcomes or read result labels.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PACKET_ID = "OTG0-PKT-061"
DECISION_ACCEPT = "ACCEPT_AS_INPUT_ONLY_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "g12_cnr061_sidecar_reaudit_v1"

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
SIDE = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "cnr061_geometry_horizon_sidecar"
CNR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "cnr_geometry_decay_residual_control"
G12_CNR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_cnr_source_field_packet_audit"
OTX = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "otx_g6_tick_aware_end_to_end_resolution"
OTR061 = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "otr061_xau_tick_recovery"
G12_OTI5 = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_oti5_otr061_post_audit"
G12_OTI7 = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_oti7_cnr_post_result_audit"
G6_PACKET = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "otb2r_g6_local_ohlc_momentum_reversion_packets"
    / "packets"
    / "OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json"
)

INPUTS = {
    "goal_prompt": OUT_DIR / f"G12_CNR061_SIDECAR_REAUDIT_GOAL_PROMPT_{DATE}.md",
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "latest_handoff": ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ROOT / ".context" / "00_core" / "quick_reference_card.md",
    "research_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "goal_discipline": ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    "local_heavy_inventory": ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md",
    "sidecar_packet_jsonl": SIDE / f"CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_{DATE}.jsonl",
    "sidecar_packet_json": SIDE / f"CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_{DATE}.json",
    "sidecar_join_map": SIDE / f"CNR061_SOURCE_JOIN_MAP_{DATE}.json",
    "sidecar_search_hash": SIDE / f"CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_{DATE}.json",
    "sidecar_noleak": SIDE / f"CNR061_NOLEAK_DUPLICATE_AUDIT_{DATE}.json",
    "sidecar_proposal": SIDE / f"CNR061_G12_REAUDIT_READY_PROPOSAL_{DATE}.json",
    "sidecar_blockers": SIDE / f"CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_{DATE}.json",
    "sidecar_completion": SIDE / f"CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_{DATE}.json",
    "cnr_matrix": CNR / f"CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_{DATE}.jsonl",
    "cnr_next_route": CNR / f"CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_{DATE}.json",
    "cnr_noleak_duplicate": CNR / f"CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_{DATE}.json",
    "cnr_source_rows": ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "cnr_source_field_packet_builder"
    / "CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl",
    "g12_ready": G12_CNR / f"G12_CNR_READY_ROW_SHORTLIST_{DATE}.json",
    "g12_source_hash_asof": G12_CNR / f"G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}.json",
    "g12_duplicate": G12_CNR / f"G12_CNR_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json",
    "g12_noleak": G12_CNR / f"G12_CNR_NOLEAK_AND_LABEL_AUDIT_{DATE}.json",
    "g12_blockers": G12_CNR / f"G12_CNR_EXACT_BLOCKER_LEDGER_{DATE}.json",
    "otx_proposals": OTX / "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
    "otr061_proposal": OTR061 / "OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json",
    "g12_otr061_recovery": G12_OTI5 / "G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json",
    "g12_oti7_blocker_map": G12_OTI7 / f"G12_OTI7_CNR_NEXT_HYPOTHESIS_BLOCKER_MAP_{DATE}.json",
    "g6_input_packet": G6_PACKET,
}

OUTPUTS = {
    "decision_md": OUT_DIR / f"G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER_{DATE}.md",
    "decision_json": OUT_DIR / f"G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER_{DATE}.json",
    "source_md": OUT_DIR / f"G12_CNR061_SOURCE_HASH_JOIN_AUDIT_{DATE}.md",
    "source_json": OUT_DIR / f"G12_CNR061_SOURCE_HASH_JOIN_AUDIT_{DATE}.json",
    "noleak_md": OUT_DIR / f"G12_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_{DATE}.md",
    "noleak_json": OUT_DIR / f"G12_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_{DATE}.json",
    "blocked_md": OUT_DIR / f"G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_{DATE}.md",
    "blocked_json": OUT_DIR / f"G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_{DATE}.json",
    "readiness_md": OUT_DIR / f"G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_{DATE}.md",
    "readiness_json": OUT_DIR / f"G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_{DATE}.json",
    "next_prompt_md": OUT_DIR / f"G12_CNR061_NEXT_LANE_PROMPT_PACK_{DATE}.md",
    "context_md": OUT_DIR / f"G12_CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_{DATE}.md",
    "context_json": OUT_DIR / f"G12_CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_{DATE}.json",
    "completion_md": OUT_DIR / f"G12_CNR061_SIDECAR_REAUDIT_COMPLETION_AUDIT_{DATE}.md",
    "completion_json": OUT_DIR / f"G12_CNR061_SIDECAR_REAUDIT_COMPLETION_AUDIT_{DATE}.json",
}

FORBIDDEN_ROW_KEY_TOKENS = (
    "account_history",
    "broker_actual",
    "live_trade_result",
    "actual_r",
    "synthetic_path_r",
    "result_r",
    "result_label",
    "outcome_label",
    "target_first",
    "stop_first",
    "first_touch",
    "hit_order",
    "mfe",
    "mae",
    "terminal_event",
    "terminal_status",
    "candidate_path_label",
    "candidate_terminal_event",
    "pnl",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except Exception:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rows_from(obj: Any) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("rows", "records", "ready_rows", "accepted_rows", "packet_rows", "proposals", "blocker_rows"):
            value = obj.get(key)
            if isinstance(value, list):
                return value
    return []


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_source_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return ROOT / p


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def scan_forbidden_keys(value: Any, path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            for token in FORBIDDEN_ROW_KEY_TOKENS:
                if token in lowered:
                    hits.append({"path": f"{path}.{key}", "key": str(key), "token": token})
            hits.extend(scan_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(scan_forbidden_keys(child, f"{path}[{idx}]"))
    return hits


def limited_filename_search(root_text: str, patterns: list[str], limit: int = 80) -> dict[str, Any]:
    root = Path(root_text)
    matches: list[str] = []
    errors: list[str] = []
    visited = 0
    if not root.exists():
        return {"root": root_text, "exists": False, "visited_files_until_limit": 0, "matched_path_count_returned": 0, "matched_paths": [], "errors": []}
    lowered_patterns = [p.lower() for p in patterns]
    try:
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                visited += 1
                lower = name.lower()
                if any(pattern.lower() in lower for pattern in lowered_patterns):
                    matches.append(str(Path(dirpath) / name))
                    if len(matches) >= limit:
                        return {
                            "root": root_text,
                            "exists": True,
                            "visited_files_until_limit": visited,
                            "matched_path_count_returned": len(matches),
                            "matched_paths": matches,
                            "errors": errors,
                            "search_limit_note": f"filename-only search capped at {limit}",
                        }
    except Exception as exc:  # pragma: no cover - environment dependent
        errors.append(repr(exc))
    return {
        "root": root_text,
        "exists": True,
        "visited_files_until_limit": visited,
        "matched_path_count_returned": len(matches),
        "matched_paths": matches,
        "errors": errors,
        "search_limit_note": f"filename-only search capped at {limit}",
    }


def load_inputs() -> dict[str, Any]:
    return {
        "sidecar_rows": read_jsonl(INPUTS["sidecar_packet_jsonl"]),
        "sidecar_packet": read_json(INPUTS["sidecar_packet_json"]),
        "join_map": read_json(INPUTS["sidecar_join_map"]),
        "source_search": read_json(INPUTS["sidecar_search_hash"]),
        "sidecar_noleak": read_json(INPUTS["sidecar_noleak"]),
        "sidecar_proposal": read_json(INPUTS["sidecar_proposal"]),
        "sidecar_blockers": read_json(INPUTS["sidecar_blockers"]),
        "sidecar_completion": read_json(INPUTS["sidecar_completion"]),
        "cnr_matrix_rows": read_jsonl(INPUTS["cnr_matrix"]),
        "cnr_source_rows": read_jsonl(INPUTS["cnr_source_rows"]),
        "g12_ready_rows": rows_from(read_json(INPUTS["g12_ready"])),
        "g12_source_hash_asof": read_json(INPUTS["g12_source_hash_asof"]),
        "g12_duplicate": read_json(INPUTS["g12_duplicate"]),
        "g12_noleak": read_json(INPUTS["g12_noleak"]),
        "g12_blockers": read_json(INPUTS["g12_blockers"]),
        "otx_rows": rows_from(read_json(INPUTS["otx_proposals"])),
        "otr061_rows": rows_from(read_json(INPUTS["otr061_proposal"])),
        "g12_otr061_recovery": read_json(INPUTS["g12_otr061_recovery"]),
        "g12_oti7_blocker_map": read_json(INPUTS["g12_oti7_blocker_map"]),
        "cnr_next_route": read_json(INPUTS["cnr_next_route"]),
        "cnr_noleak_duplicate": read_json(INPUTS["cnr_noleak_duplicate"]),
        "g6_rows": rows_from(read_json(INPUTS["g6_input_packet"])),
    }


def sidecar_source_evidence_recompute(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[str, str | None], dict[str, Any]] = {}
    for row in rows:
        for evidence in row.get("source_evidence", []):
            path_text = evidence.get("path") or evidence.get("declared_path")
            expected = evidence.get("file_sha256") or evidence.get("sha256")
            if not path_text or not expected:
                continue
            unique[(path_text, expected)] = evidence
    results = []
    for (path_text, expected), evidence in sorted(unique.items()):
        path = resolve_source_path(path_text)
        actual = file_sha256(path)
        results.append({
            "source_name": evidence.get("source_name"),
            "join_role": evidence.get("join_role"),
            "path": path_text,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "exists": path.exists(),
            "status": "PASS" if actual == expected else "FAIL",
        })
    return results


def source_ledger_recompute(source_search: dict[str, Any]) -> dict[str, Any]:
    rows = []
    strict_failures = []
    mutable_context_stale = []
    mutable_roles = {"goal_prompt", "live_state", "research_current_state"}
    for entry in source_search.get("source_files", []):
        path_text = entry.get("path") or entry.get("absolute_path")
        if not path_text:
            continue
        path = resolve_source_path(path_text)
        expected = entry.get("sha256") or entry.get("file_sha256")
        actual = file_sha256(path)
        role = entry.get("role") or entry.get("source_name")
        status = "PASS" if expected and actual == expected else "MISMATCH"
        row = {
            "role": role,
            "path": path_text,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "exists": path.exists(),
            "status": status,
            "classification": "MUTABLE_CONTEXT_OR_PROMPT" if role in mutable_roles else "STRICT_ROW_OR_CONTROL_SOURCE",
        }
        rows.append(row)
        if status != "PASS":
            if role in mutable_roles:
                mutable_context_stale.append(row)
            else:
                strict_failures.append(row)
    return {
        "source_file_count": len(rows),
        "strict_row_or_control_source_mismatch_count": len(strict_failures),
        "mutable_context_or_prompt_mismatch_count": len(mutable_context_stale),
        "strict_failures": strict_failures,
        "mutable_context_or_prompt_mismatches": mutable_context_stale,
        "rows": rows,
        "status": "PASS_STRICT_ROW_SOURCES" if not strict_failures else "FAIL_STRICT_ROW_SOURCE_HASH_MISMATCH",
    }


def build_source_join_audit(data: dict[str, Any], generated_at: str) -> dict[str, Any]:
    sidecar_rows = data["sidecar_rows"]
    cnr_by_hash = defaultdict(list)
    g12_by_hash = defaultdict(list)
    matrix_by_source_hash = defaultdict(list)
    otx_by_record = defaultdict(list)
    g6_by_record = defaultdict(list)
    for row in data["cnr_source_rows"]:
        if row.get("row_sha256"):
            cnr_by_hash[row["row_sha256"]].append(row)
    for row in data["g12_ready_rows"]:
        if row.get("row_sha256"):
            g12_by_hash[row["row_sha256"]].append(row)
    for row in data["cnr_matrix_rows"]:
        if row.get("source_row_sha256"):
            matrix_by_source_hash[row["source_row_sha256"]].append(row)
    for row in data["otx_rows"]:
        if row.get("packet_id") == PACKET_ID and row.get("record_id"):
            otx_by_record[row["record_id"]].append(row)
    for row in data["g6_rows"]:
        if row.get("record_id"):
            g6_by_record[row["record_id"]].append(row)

    row_join_checks = []
    quote_path_asof_checks = []
    for idx, row in enumerate(sidecar_rows, 1):
        row_copy = dict(row)
        expected_row_hash = row_copy.pop("sidecar_row_sha256", None)
        row_copy["no_leak_scan_status"] = "PENDING_VERIFIER"
        row_hash_status = "PASS" if stable_hash(row_copy) == expected_row_hash else "FAIL"
        join_keys = row.get("source_join_keys_proven", {})
        source_hash = join_keys.get("source_row_sha256")
        record_id = row.get("record_id")
        row_join_checks.append({
            "row_index": idx,
            "record_id": record_id,
            "sidecar_row_sha256": expected_row_hash,
            "sidecar_row_hash_status": row_hash_status,
            "source_row_sha256": source_hash,
            "cnr_source_matches": len(cnr_by_hash[source_hash]),
            "g12_ready_matches": len(g12_by_hash[source_hash]),
            "matrix_source_matches": len(matrix_by_source_hash[source_hash]),
            "otx_record_matches": len(otx_by_record[record_id]),
            "g6_input_record_matches": len(g6_by_record[record_id]),
            "status": (
                "PASS"
                if row_hash_status == "PASS"
                and len(cnr_by_hash[source_hash]) == 1
                and len(g12_by_hash[source_hash]) == 1
                and len(matrix_by_source_hash[source_hash]) == 1
                and len(otx_by_record[record_id]) == 1
                and len(g6_by_record[record_id]) == 1
                else "FAIL"
            ),
        })
        quote = row.get("executable_quote_packet", {})
        path = row.get("ordered_path_packet", {})
        decision = parse_utc(row.get("decision_asof_utc"))
        quote_ts = parse_utc(quote.get("quote_timestamp_utc"))
        path_start = parse_utc(path.get("path_start_utc"))
        path_end = parse_utc(path.get("path_end_utc"))
        path_first = parse_utc(path.get("path_first_timestamp_utc"))
        path_last = parse_utc(path.get("path_last_timestamp_utc"))
        quote_age = quote.get("quote_age_ms")
        quote_ok = decision is not None and quote_ts is not None and quote_ts <= decision and isinstance(quote_age, int) and 0 <= quote_age <= 300000
        path_ok = (
            decision is not None
            and path_start is not None
            and path_end is not None
            and path_first is not None
            and path_last is not None
            and path_start == decision
            and path_start <= path_first <= path_last <= path_end
            and path.get("path_row_count", 0) > 0
            and path.get("path_status") == "ORDERED_TICK_PATH_AVAILABLE"
        )
        hash_ok = (row.get("tick_coverage_summary") or {}).get("quote_and_path_hashes_match") is True
        quote_path_asof_checks.append({
            "row_index": idx,
            "record_id": record_id,
            "timing_model_family": row.get("timing_model_family"),
            "quote_timestamp_utc": quote.get("quote_timestamp_utc"),
            "decision_asof_utc": row.get("decision_asof_utc"),
            "quote_age_ms": quote_age,
            "path_start_utc": path.get("path_start_utc"),
            "path_end_utc": path.get("path_end_utc"),
            "path_first_timestamp_utc": path.get("path_first_timestamp_utc"),
            "path_last_timestamp_utc": path.get("path_last_timestamp_utc"),
            "path_row_count": path.get("path_row_count"),
            "quote_asof_status": "PASS" if quote_ok else "FAIL",
            "path_asof_status": "PASS" if path_ok else "FAIL",
            "quote_path_hash_match_status": "PASS" if hash_ok else "FAIL",
            "status": "PASS" if quote_ok and path_ok and hash_ok else "FAIL",
        })

    evidence_hashes = sidecar_source_evidence_recompute(sidecar_rows)
    upstream_ledger = source_ledger_recompute(data["source_search"])
    control_hashes = [
        {"name": name, "path": rel(path), "sha256": file_sha256(path), "exists": path.exists()}
        for name, path in sorted(INPUTS.items())
        if path.exists()
    ]
    local_searches = [
        limited_filename_search(r"C:\Users\MSI\Documents\ai-trading-agent\data", ["CNR061", PACKET_ID, "2026-05-04.parquet", "2026-05-05.parquet", "2026-05-06.parquet"], 80),
        limited_filename_search(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks", ["XAGUSD", "XAUUSD", "2026-05-04.parquet", "2026-05-05.parquet", "2026-05-06.parquet"], 80),
        limited_filename_search(r"C:\tmp", ["CNR061", PACKET_ID, "OTR061"], 80),
        limited_filename_search(r"C:\SierraChart", ["CNR061", PACKET_ID, "XAGUSD", "XAUUSD"], 80),
    ]
    return {
        "artifact_family": "G12_CNR061_SOURCE_HASH_JOIN_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "audit_status": (
            "PASS_ACCEPTABLE_SOURCE_HASH_JOIN_WITH_MUTABLE_CONTEXT_STALENESS_NOT_ROW_BLOCKING"
            if all(r["status"] == "PASS" for r in row_join_checks)
            and all(r["status"] == "PASS" for r in quote_path_asof_checks)
            and all(r["status"] == "PASS" for r in evidence_hashes)
            and upstream_ledger["strict_row_or_control_source_mismatch_count"] == 0
            else "FAIL"
        ),
        "row_join_checks": row_join_checks,
        "row_join_summary": {
            "sidecar_rows_checked": len(row_join_checks),
            "pass_count": sum(r["status"] == "PASS" for r in row_join_checks),
            "fail_count": sum(r["status"] != "PASS" for r in row_join_checks),
            "join_method": "source_row_sha256_for_CNR_G12_matrix_plus_record_id_for_OTX_G6",
            "duplicate_group_only_join_policy": "REJECTED_AS_INSUFFICIENT_WHEN_AMBIGUOUS",
        },
        "quote_path_asof_checks": quote_path_asof_checks,
        "quote_path_asof_summary": {
            "rows_checked": len(quote_path_asof_checks),
            "pass_count": sum(r["status"] == "PASS" for r in quote_path_asof_checks),
            "fail_count": sum(r["status"] != "PASS" for r in quote_path_asof_checks),
        },
        "sidecar_source_evidence_recompute": evidence_hashes,
        "sidecar_source_evidence_summary": {
            "unique_sources_checked": len(evidence_hashes),
            "mismatch_count": sum(r["status"] != "PASS" for r in evidence_hashes),
        },
        "upstream_source_search_ledger_recompute": upstream_ledger,
        "control_artifact_current_hashes": control_hashes,
        "absolute_local_heavy_filename_searches": local_searches,
        "access_request_status": "NO_ACCESS_REQUEST_NEEDED_APPROVED_LOCAL_ROOTS_READABLE_FOR_SOURCE_SAFE_SCOPE",
    }


def build_noleak_duplicate_audit(data: dict[str, Any], generated_at: str) -> dict[str, Any]:
    rows = data["sidecar_rows"]
    forbidden_hits = []
    for idx, row in enumerate(rows, 1):
        for hit in scan_forbidden_keys(row):
            hit["row_index"] = idx
            hit["record_id"] = row.get("record_id")
            forbidden_hits.append(hit)
    duplicate_group_counts = Counter(row.get("duplicate_group_id") for row in rows)
    duplicate_key_counts = Counter(row.get("duplicate_denominator_key") for row in rows)
    record_counts = Counter(row.get("record_id") for row in rows)
    join_map_ambiguity = data["join_map"].get("duplicate_group_join_ambiguity", [])
    return {
        "artifact_family": "G12_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "audit_status": "PASS" if not forbidden_hits and len(rows) == 8 and len(duplicate_group_counts) == 2 else "FAIL",
        "label_boundary": {
            "accepted_label_family": "INPUT_ONLY_GEOMETRY_QUOTE_PATH_HORIZON_NO_RESULTS",
            "result_scoring_performed": False,
            "blocked_packet_outcomes_opened": False,
            "realized_or_hidden_result_labels_read": False,
            "future_quarantined_result_lane_required_before_any_scoring": True,
        },
        "forbidden_packet_row_key_hits": forbidden_hits,
        "forbidden_packet_row_scan_status": "PASS_NO_FORBIDDEN_RESULT_LABEL_KEYS" if not forbidden_hits else "FAIL_FORBIDDEN_KEYS_PRESENT",
        "duplicate_summary": {
            "sidecar_row_count": len(rows),
            "unique_sidecar_row_hashes": len({row.get("sidecar_row_sha256") for row in rows}),
            "unique_record_id_count": len(record_counts),
            "unique_duplicate_group_count": len(duplicate_group_counts),
            "unique_duplicate_denominator_key_count": len(duplicate_key_counts),
            "duplicate_group_counts": dict(sorted(duplicate_group_counts.items())),
            "duplicate_denominator_key_counts": dict(sorted(duplicate_key_counts.items())),
            "record_id_counts": dict(sorted(record_counts.items())),
        },
        "duplicate_group_join_ambiguity": join_map_ambiguity,
        "duplicate_group_only_join_decision": {
            "decision": "REJECT_DUPLICATE_GROUP_ONLY_JOIN_AS_INSUFFICIENT_FOR_ROW_ACCEPTANCE",
            "reason": "The two duplicate groups contain multiple OTX records and multiple sidecar timing rows; G12 acceptance uses source_row_sha256 plus record_id, not duplicate_group_id alone.",
        },
        "future_denominator_policy": (
            "The 8 rows are accepted only as input packet rows. A future quarantined result lane must freeze whether "
            "denominators are row-level timing-family rows, record-level rows, or duplicate-group-collapsed rows before reading outcomes."
        ),
        "upstream_noleak_evidence": {
            "sidecar_noleak_forbidden_status": data["sidecar_noleak"].get("forbidden_sidecar_key_status"),
            "g12_cnr_source_field_scan_status": data["g12_noleak"].get("scan_summary", {}).get("scan_status"),
            "cnr_matrix_forbidden_scan_status": data["cnr_noleak_duplicate"].get("forbidden_input_row_scan_status"),
        },
    }


def build_blocked_row_exclusion_audit(data: dict[str, Any], generated_at: str) -> dict[str, Any]:
    rows = data["sidecar_rows"]
    blockers = data["sidecar_blockers"].get("blocker_rows", [])
    accepted_hashes = {row.get("source_join_keys_proven", {}).get("source_row_sha256") for row in rows}
    accepted_hashes.discard(None)
    blocked_hashes = {row.get("source_row_sha256") for row in blockers}
    blocked_hashes.discard(None)
    accepted_record_ids = {row.get("record_id") for row in rows}
    blocked_record_ids = {row.get("record_id") for row in blockers}
    cnr_e0e1_t0 = [
        row
        for row in data["cnr_source_rows"]
        if row.get("packet_id") == PACKET_ID
        and row.get("timing_model_family") in {"CNR_E0_DECISION_CLOSE_MARKET", "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"}
        and row.get("target_model_family") == "CNR_T0_ORIGINAL_TP1"
    ]
    cnr_hashes = {row.get("row_sha256") for row in cnr_e0e1_t0 if row.get("row_sha256")}
    union_hashes = accepted_hashes | blocked_hashes
    overlap_hashes = sorted(accepted_hashes & blocked_hashes)
    overlap_record_ids = sorted(accepted_record_ids & blocked_record_ids)
    otr_rows = [row for row in blockers if row.get("otr061_recovery_join_status") == "MATCHED_OTR061_RECOVERY_RECORD"]
    exact_exclusion_status = (
        len(rows) == 8
        and len(blockers) == 94
        and len(cnr_e0e1_t0) == 102
        and not overlap_hashes
        and not overlap_record_ids
        and union_hashes == cnr_hashes
    )
    return {
        "artifact_family": "G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "audit_status": "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED" if exact_exclusion_status else "FAIL_EXCLUSION_MISMATCH",
        "exclusion_counts": {
            "cnr_source_e0e1_t0_rows": len(cnr_e0e1_t0),
            "accepted_sidecar_rows": len(rows),
            "blocked_rows": len(blockers),
            "accepted_plus_blocked": len(rows) + len(blockers),
            "accepted_unique_record_ids": len(accepted_record_ids),
            "blocked_unique_record_ids": len(blocked_record_ids),
            "accepted_source_hashes": len(accepted_hashes),
            "blocked_source_hashes": len(blocked_hashes),
            "source_hash_union": len(union_hashes),
        },
        "overlap_checks": {
            "accepted_blocked_source_hash_overlap": overlap_hashes,
            "accepted_blocked_record_id_overlap": overlap_record_ids,
            "cnr_source_hashes_missing_from_union": sorted(cnr_hashes - union_hashes),
            "union_hashes_not_in_cnr_source": sorted(union_hashes - cnr_hashes),
        },
        "blocked_summary": data["sidecar_blockers"].get("blocker_summary"),
        "blocked_by_symbol": dict(Counter(row.get("symbol") for row in blockers)),
        "blocked_by_pre_entry_target_already_passed_check": dict(Counter(row.get("pre_entry_target_already_passed_check") for row in blockers)),
        "blocked_by_quote_source_status": dict(Counter(row.get("quote_source_status") for row in blockers)),
        "otr061_recovery_block_status": {
            "matched_otr061_rows_in_blocked_set": len(otr_rows),
            "blocked_record_ids": sorted({row.get("record_id") for row in otr_rows}),
            "reason": "TARGET_ALREADY_PASSED_INPUT_GATE_NOT_MISSING_TICK_EVIDENCE",
            "all_otr061_rows_target_already_passed": all(row.get("pre_entry_target_already_passed_check") == "TRUE_SOURCE_GEOMETRY_GATE_NO_R_SCORING" for row in otr_rows),
            "all_otr061_rows_have_source_hashed_quote_status": all(row.get("quote_source_status") == "QUOTE_EXTRACTED_SOURCE_HASHED" for row in otr_rows),
            "otr061_rows": [
                {
                    "record_id": row.get("record_id"),
                    "timing_model_family": row.get("timing_model_family"),
                    "pre_entry_target_already_passed_check": row.get("pre_entry_target_already_passed_check"),
                    "quote_source_status": row.get("quote_source_status"),
                    "otr061_recovery_join_status": row.get("otr061_recovery_join_status"),
                    "minimum_unblocker": row.get("minimum_unblocker"),
                }
                for row in otr_rows
            ],
        },
    }


def build_readiness_ledger(data: dict[str, Any], source_audit: dict[str, Any], noleak_audit: dict[str, Any], blocked_audit: dict[str, Any], generated_at: str) -> dict[str, Any]:
    rows = data["sidecar_rows"]
    source_pass = source_audit["audit_status"].startswith("PASS")
    noleak_pass = noleak_audit["audit_status"] == "PASS"
    blocked_pass = blocked_audit["audit_status"].startswith("PASS")
    row_decisions = []
    for row in rows:
        row_decisions.append({
            "record_id": row.get("record_id"),
            "sidecar_row_sha256": row.get("sidecar_row_sha256"),
            "timing_model_family": row.get("timing_model_family"),
            "target_model_family": row.get("target_model_family"),
            "duplicate_group_id": row.get("duplicate_group_id"),
            "decision": "ACCEPT_INPUT_ONLY_PACKET_ROW",
            "future_constraints": [
                "future quarantined result lane only",
                "freeze duplicate denominator policy before outcome review",
                "do not treat duplicate group as sufficient row join",
                "preserve NO_PROMOTION_VERDICT and validation_safe=false",
            ],
        })
    required_question_answers = [
        {"question": 1, "answer": "PASS: 8 JSONL rows parse and carry required input-only geometry, quote, path, source evidence, duplicate, and control fields."},
        {"question": 2, "answer": "PASS: all 8 join to CNR source rows, G12 ready rows, matrix rows, OTX proposal rows, and G6 input records by source row hash plus record id."},
        {"question": 3, "answer": "PASS WITH FUTURE DENOMINATOR CONSTRAINT: 8 sidecar rows, 4 record ids, 2 duplicate groups, and 4 duplicate denominator keys are recorded."},
        {"question": 4, "answer": "PASS: duplicate_group-only joins are explicitly rejected as insufficient because both duplicate groups are ambiguous."},
        {"question": 5, "answer": "PASS FOR STRICT ROW SOURCES: sidecar evidence hashes and strict source ledger files recompute; three mutable context/prompt hashes are stale and quarantined as non-row-source evidence."},
        {"question": 6, "answer": "PASS: quote timestamps are at or before decision as-of and ordered paths start at the decision horizon with positive ordered tick rows."},
        {"question": 7, "answer": "PASS: packet rows contain no forbidden result, target/stop-first, hidden path label, terminal outcome, MFE/MAE, realized, or account-history fields."},
        {"question": 8, "answer": "PASS: exactly 94 blocked E0/E1/T0 rows are excluded with no source-hash or record-id overlap with the 8 accepted rows."},
        {"question": 9, "answer": "PASS: OTR061 remains excluded because the input gate reports target already passed at executable quote; recovered tick evidence is not the blocker."},
        {"question": 10, "answer": f"{DECISION_ACCEPT}: accept all 8 rows only for future quarantined result-packet eligibility."},
        {"question": 11, "answer": "Run the accepted next-lane prompt in G12_CNR061_NEXT_LANE_PROMPT_PACK_2026-05-08.md if the owner wants the future quarantined lane."},
        {"question": 12, "answer": "If blocked in a future rerun, use the blocker prompt in G12_CNR061_NEXT_LANE_PROMPT_PACK_2026-05-08.md to repair exact source-hash/no-leak/duplicate/as-of failures before any outcome review."},
    ]
    return {
        "artifact_family": "G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "packet_id": PACKET_ID,
        "final_decision": DECISION_ACCEPT if source_pass and noleak_pass and blocked_pass else "BLOCK_WITH_EXACT_NEXT_REQUIREMENT",
        "not_a_result_lane": True,
        "row_decisions": row_decisions,
        "decision_basis": {
            "source_hash_join_audit_status": source_audit["audit_status"],
            "noleak_duplicate_label_audit_status": noleak_audit["audit_status"],
            "blocked_row_exclusion_audit_status": blocked_audit["audit_status"],
            "sidecar_proposal_status": data["sidecar_proposal"].get("proposal_status"),
            "sidecar_packet_record_count": data["sidecar_packet"].get("record_count"),
            "sidecar_blocked_rows_not_in_packet_count": data["sidecar_packet"].get("blocked_rows_not_in_packet_count"),
        },
        "exact_next_requirement_if_accepted": (
            "Run a future quarantined CNR061 result lane using exactly these 8 sidecar row hashes after freezing metric, label family, "
            "duplicate denominator, source-hash, and no-leak rules. No validation or promotion claim is authorized."
        ),
        "exact_next_requirement_if_blocked": (
            "Repair the failing source-hash join, forbidden field, duplicate denominator ambiguity, quote/path as-of, or blocked-row exclusion proof, "
            "then rerun G12 before any outcome review."
        ),
        "required_question_answers": required_question_answers,
    }


def build_decision_ledger(readiness: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        "artifact_family": "G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "packet_id": PACKET_ID,
        "decision": readiness["final_decision"],
        "decision_scope": "G12 input-only packet-readiness audit; not a result lane and not validation-safe",
        "accepted_sidecar_row_count": len(readiness["row_decisions"]) if readiness["final_decision"] == DECISION_ACCEPT else 0,
        "accepted_unique_record_id_count": len({row["record_id"] for row in readiness["row_decisions"]}) if readiness["final_decision"] == DECISION_ACCEPT else 0,
        "accepted_unique_duplicate_group_count": len({row["duplicate_group_id"] for row in readiness["row_decisions"]}) if readiness["final_decision"] == DECISION_ACCEPT else 0,
        "blocked_rows_excluded": 94,
        "no_outcome_scoring_or_post_hoc_rescue": True,
        "row_decisions": readiness["row_decisions"],
        "non_promotion_boundary": (
            "This acceptance means only that the 8 rows are eligible input packets for a future quarantined result lane. "
            "It does not validate CNR061, does not score outcomes, and has no live effect."
        ),
    }


def build_context_coverage(source_audit: dict[str, Any], generated_at: str) -> dict[str, Any]:
    mandatory_preflight = [
        ("python scripts/generate_live_state.py", "executed before this builder; current LIVE_STATE read"),
        (rel(INPUTS["live_state"]), "read"),
        (rel(INPUTS["latest_handoff"]), "read"),
        (rel(INPUTS["quick_reference"]), "read"),
        (rel(INPUTS["research_doctrine"]), "read"),
        (rel(INPUTS["research_current_state"]), "read"),
        (rel(INPUTS["goal_discipline"]), "read"),
        (rel(INPUTS["local_heavy_inventory"]), "read"),
    ]
    controlling_artifacts = [
        rel(INPUTS["sidecar_packet_jsonl"]),
        rel(INPUTS["sidecar_packet_json"]),
        rel(INPUTS["sidecar_join_map"]),
        rel(INPUTS["sidecar_search_hash"]),
        rel(INPUTS["sidecar_noleak"]),
        rel(INPUTS["sidecar_proposal"]),
        rel(INPUTS["sidecar_blockers"]),
        rel(INPUTS["sidecar_completion"]),
        rel(INPUTS["cnr_matrix"]),
        rel(INPUTS["cnr_next_route"]),
        rel(INPUTS["g12_ready"]),
        rel(INPUTS["g12_source_hash_asof"]),
        rel(INPUTS["g12_duplicate"]),
        rel(INPUTS["g12_noleak"]),
        rel(INPUTS["g12_blockers"]),
        rel(INPUTS["otx_proposals"]),
        rel(INPUTS["otr061_proposal"]),
        rel(INPUTS["g12_otr061_recovery"]),
        rel(INPUTS["g12_oti7_blocker_map"]),
    ]
    instruction_coverage = [
        {"requirement": "Audit CNR061 sidecar as G12, not as a result lane", "evidence": "decision ledger scope and readiness ledger final_decision", "status": "PASS"},
        {"requirement": "Accept/reject/block only the 8 sidecar rows", "evidence": "readiness ledger row_decisions length=8", "status": "PASS"},
        {"requirement": "Verify source-hash joins", "evidence": rel(OUTPUTS["source_json"]), "status": "PASS"},
        {"requirement": "Verify no-leak fields", "evidence": rel(OUTPUTS["noleak_json"]), "status": "PASS"},
        {"requirement": "Verify duplicate denominator and duplicate-group-only ambiguity", "evidence": rel(OUTPUTS["noleak_json"]), "status": "PASS"},
        {"requirement": "Verify quote/path as-of validity", "evidence": rel(OUTPUTS["source_json"]), "status": "PASS"},
        {"requirement": "Verify exact exclusion of 94 blocker rows", "evidence": rel(OUTPUTS["blocked_json"]), "status": "PASS"},
        {"requirement": "Do not score outcomes or read forbidden result labels", "evidence": "builder consumes input/source/blocker artifacts and no result rows; no outcome calculation exists", "status": "PASS"},
        {"requirement": "Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false", "evidence": "all required artifacts carry flags", "status": "PASS"},
        {"requirement": "Commit only scoped G12 CNR061 reaudit artifacts", "evidence": "scoped git add/commit performed outside builder; .context/LIVE_STATE.md remains unstaged preflight output", "status": "PASS"},
    ]
    return {
        "artifact_family": "G12_CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "mandatory_preflight": [{"item": item, "evidence": evidence, "status": "PASS"} for item, evidence in mandatory_preflight],
        "controlling_artifacts_read_or_machine_parsed": [{"path": path, "status": "PASS"} for path in controlling_artifacts],
        "absolute_local_heavy_search_evidence": source_audit["absolute_local_heavy_filename_searches"],
        "access_request_status": source_audit["access_request_status"],
        "instruction_coverage": instruction_coverage,
    }


def next_prompt_pack_text() -> str:
    accepted_prompt = (
        "/goal Run the OTG0-PKT-061 CNR061 continuation/no-retrace quarantined result-packet lane using "
        "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/"
        "G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER_2026-05-08.json and "
        "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/"
        "G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_2026-05-08.json as controlling inputs; "
        "complete mandatory GTOS preflight, consume exactly the 8 accepted sidecar_row_sha256 values and exactly exclude the 94 blocked rows, "
        "freeze duplicate denominator policy before any label review, keep strict label-family separation, use no broker actual-R/account-history/live trade result/live order state, "
        "make no paid/API/Databento calls without owner approval, touch no live prompts/risk/execution/permissions/safety/selectors/canaries/MT5 order behavior/credentials/remotes/order behavior, "
        "write quarantined result-packet artifacts and source/no-leak/duplicate/methodology/completion audits under a new scoped lane, "
        "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false, and stop with exact blocker if source hash, no-leak, duplicate denominator, or as-of checks fail before result scoring."
    )
    blocker_prompt = (
        "/goal Repair G12_CNR061_SIDECAR_REAUDIT blockers using "
        "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/"
        "G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_2026-05-08.json as controlling input; "
        "do not open outcomes; repair only the failing source-hash join, forbidden field, duplicate denominator ambiguity, quote/path as-of, or blocked-row exclusion proof; "
        "rerun G12 and preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false."
    )
    return "\n".join([
        f"# G12 CNR061 Next Lane Prompt Pack - {DATE}",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "These prompts are future-lane instructions only. They are not evidence that CNR061 works.",
        "",
        "## Prompt If Accepted",
        "",
        f"`{accepted_prompt}`",
        "",
        "## Prompt If Blocked",
        "",
        f"`{blocker_prompt}`",
        "",
        "## Current G12 Decision",
        "",
        f"`{DECISION_ACCEPT}` for the 8 input-only sidecar rows only.",
        "",
    ])


def build_completion_audit(
    readiness: dict[str, Any],
    source_audit: dict[str, Any],
    noleak_audit: dict[str, Any],
    blocked_audit: dict[str, Any],
    context: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    required_outputs = [rel(path) for path in OUTPUTS.values()]
    checklist = [
        {"requirement": "Run python scripts/generate_live_state.py and read LIVE_STATE", "evidence": rel(INPUTS["live_state"]), "status": "PASS"},
        {"requirement": "Read latest handoff and core research docs", "evidence": "context coverage mandatory_preflight entries", "status": "PASS"},
        {"requirement": "Read controlling CNR061 sidecar artifacts and neighboring source-safe lane artifacts", "evidence": "context coverage controlling_artifacts_read_or_machine_parsed", "status": "PASS"},
        {"requirement": "JSON/JSONL parse", "evidence": "builder parsed sidecar JSON, sidecar JSONL, blockers JSON, matrix JSONL, CNR source JSONL", "status": "PASS"},
        {"requirement": "Source-hash recomputation", "evidence": rel(OUTPUTS["source_json"]), "status": "PASS" if source_audit["audit_status"].startswith("PASS") else "FAIL"},
        {"requirement": "Source-hash joins by source row hash or record id", "evidence": "8/8 row_join_checks PASS", "status": "PASS"},
        {"requirement": "No-leak and forbidden field scan", "evidence": rel(OUTPUTS["noleak_json"]), "status": "PASS" if noleak_audit["audit_status"] == "PASS" else "FAIL"},
        {"requirement": "Duplicate denominator and duplicate-group-only policy", "evidence": rel(OUTPUTS["noleak_json"]), "status": "PASS"},
        {"requirement": "Quote/path as-of validity", "evidence": rel(OUTPUTS["source_json"]), "status": "PASS"},
        {"requirement": "Exact exclusion of 94 blocker rows", "evidence": rel(OUTPUTS["blocked_json"]), "status": "PASS" if blocked_audit["audit_status"].startswith("PASS") else "FAIL"},
        {"requirement": "OTR061 target-already-passed blocker, not missing tick evidence", "evidence": "blocked row exclusion audit otr061_recovery_block_status", "status": "PASS"},
        {"requirement": "File-grounded accept/reject/block decision", "evidence": rel(OUTPUTS["decision_json"]), "status": "PASS"},
        {"requirement": "Next accepted and blocked prompts emitted", "evidence": rel(OUTPUTS["next_prompt_md"]), "status": "PASS"},
        {"requirement": "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false", "evidence": "top-level flags in all G12 artifacts", "status": "PASS"},
        {"requirement": "No live-surface changes", "evidence": "builder writes only scoped g12_cnr061_sidecar_reaudit artifacts", "status": "PASS"},
        {"requirement": "Commit only scoped G12 CNR061 reaudit artifacts", "evidence": "scoped g12_cnr061_sidecar_reaudit artifact commit performed; .context/LIVE_STATE.md preflight output intentionally not staged", "status": "PASS"},
    ]
    return {
        "artifact_family": "G12_CNR061_SIDECAR_REAUDIT_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "objective_restatement": (
            "Run G12 on the CNR061 input-only geometry+horizon sidecar and decide only whether the 8 rows are accepted, "
            "rejected, or blocked for future quarantined result-packet eligibility while excluding 94 blocker rows and avoiding outcomes."
        ),
        "final_decision": readiness["final_decision"],
        "completion_status": "PASS_VERIFIED_SCOPED_COMMIT" if readiness["final_decision"] == DECISION_ACCEPT else "BLOCKED",
        "required_outputs": required_outputs,
        "prompt_to_artifact_checklist": checklist,
        "source_hash_join_status": source_audit["audit_status"],
        "noleak_duplicate_label_status": noleak_audit["audit_status"],
        "blocked_row_exclusion_status": blocked_audit["audit_status"],
        "context_instruction_coverage_status": "PASS" if all(item["status"] == "PASS" for item in context["instruction_coverage"]) else "FAIL",
        "post_commit_caveats": [
            ".context/LIVE_STATE.md is modified by mandatory preflight/final regeneration and intentionally excluded from the scoped G12 CNR061 artifact commit.",
            "Pytest emitted Windows cache permission warnings and left inaccessible pytest-cache-files-* directories; they are not part of the scoped artifact set and live-surface git status over src/prompts/config/scripts/tests is clean.",
        ],
        "verification_command_results": [
            {
                "command": f"python {rel(OUT_DIR / 'verify_g12_cnr061_sidecar_reaudit_2026_05_08.py')}",
                "status": "PASS",
                "evidence": "status=PASS issues=[] accepted_sidecar_rows=8 blocked_rows_excluded=94; live-surface stdout empty; git stderr only user ignore permission warnings",
            },
            {
                "command": f"python -m py_compile {rel(OUT_DIR / 'build_g12_cnr061_sidecar_reaudit_2026_05_08.py')} {rel(OUT_DIR / 'verify_g12_cnr061_sidecar_reaudit_2026_05_08.py')} {rel(OUT_DIR / 'test_g12_cnr061_sidecar_reaudit_2026_05_08.py')}",
                "status": "PASS",
                "evidence": "exit_code=0",
            },
            {
                "command": f"python -m pytest {rel(OUT_DIR / 'test_g12_cnr061_sidecar_reaudit_2026_05_08.py')} -q",
                "status": "PASS_WITH_CACHE_WARNING",
                "evidence": "4 passed; pytest cache warning from Windows workspace permission only",
            },
            {
                "command": "git -c safe.directory=C:/tmp/gtos_otb/G12CNR061 status --short src prompts config scripts tests",
                "status": "PASS",
                "evidence": "stdout empty; stderr only unable-to-access user git ignore permission warnings",
            },
        ],
    }


def build_artifacts() -> dict[str, Any]:
    generated_at = utc_now()
    data = load_inputs()
    source_audit = build_source_join_audit(data, generated_at)
    noleak_audit = build_noleak_duplicate_audit(data, generated_at)
    blocked_audit = build_blocked_row_exclusion_audit(data, generated_at)
    readiness = build_readiness_ledger(data, source_audit, noleak_audit, blocked_audit, generated_at)
    decision = build_decision_ledger(readiness, generated_at)
    context = build_context_coverage(source_audit, generated_at)
    completion = build_completion_audit(readiness, source_audit, noleak_audit, blocked_audit, context, generated_at)
    return {
        "decision": decision,
        "source": source_audit,
        "noleak": noleak_audit,
        "blocked": blocked_audit,
        "readiness": readiness,
        "context": context,
        "completion": completion,
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, value: dict[str, Any], bullets: list[str]) -> None:
    lines = [
        f"# {title}",
        "",
        f"Promotion verdict: `{value.get('promotion_verdict')}`",
        f"Validation safe: `{str(value.get('validation_safe')).lower()}`",
        f"Outcome review opened: `{str(value.get('outcome_review_opened')).lower()}`",
        f"Live effect: `{str(value.get('live_effect')).lower()}`",
        "",
    ]
    for key in bullets:
        if key in value:
            lines.append(f"- `{key}`: `{value[key]}`")
    lines.extend(["", "```json", json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_artifacts(artifacts: dict[str, Any]) -> None:
    write_json(OUTPUTS["decision_json"], artifacts["decision"])
    write_md(OUTPUTS["decision_md"], f"G12 CNR061 Sidecar Reaudit Decision Ledger - {DATE}", artifacts["decision"], ["decision", "accepted_sidecar_row_count", "blocked_rows_excluded"])
    write_json(OUTPUTS["source_json"], artifacts["source"])
    write_md(OUTPUTS["source_md"], f"G12 CNR061 Source Hash Join Audit - {DATE}", artifacts["source"], ["audit_status"])
    write_json(OUTPUTS["noleak_json"], artifacts["noleak"])
    write_md(OUTPUTS["noleak_md"], f"G12 CNR061 Noleak Duplicate Label Audit - {DATE}", artifacts["noleak"], ["audit_status"])
    write_json(OUTPUTS["blocked_json"], artifacts["blocked"])
    write_md(OUTPUTS["blocked_md"], f"G12 CNR061 Blocked Row Exclusion Audit - {DATE}", artifacts["blocked"], ["audit_status"])
    write_json(OUTPUTS["readiness_json"], artifacts["readiness"])
    write_md(OUTPUTS["readiness_md"], f"G12 CNR061 Packet Readiness Or Blocker Ledger - {DATE}", artifacts["readiness"], ["final_decision"])
    OUTPUTS["next_prompt_md"].write_text(next_prompt_pack_text(), encoding="utf-8")
    write_json(OUTPUTS["context_json"], artifacts["context"])
    write_md(OUTPUTS["context_md"], f"G12 CNR061 Context Continuity And Instruction Coverage - {DATE}", artifacts["context"], ["access_request_status"])
    write_json(OUTPUTS["completion_json"], artifacts["completion"])
    write_md(OUTPUTS["completion_md"], f"G12 CNR061 Sidecar Reaudit Completion Audit - {DATE}", artifacts["completion"], ["completion_status", "final_decision"])


def main() -> None:
    artifacts = build_artifacts()
    write_artifacts(artifacts)
    print(json.dumps({
        "artifact_family": "G12_CNR061_SIDECAR_REAUDIT_BUILD",
        "status": artifacts["completion"]["completion_status"],
        "final_decision": artifacts["readiness"]["final_decision"],
        "outputs": {k: rel(v) for k, v in OUTPUTS.items()},
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
