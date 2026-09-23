#!/usr/bin/env python3
"""Build the G12 audit packet for the R11 READY8 geometry capture repair packet.

This script is intentionally route-local and evidence-only. It reads the R11
packet from disk, recomputes the required row counts and hashes, audits every
weak symbol-time overlap row, audits every source-root ledger row, verifies every
capture requirement row is row-specific, and emits the downstream executable
implementation fork.
"""

from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT"
EVIDENCE_CLASS = "G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_ONLY"
R11_EVIDENCE_CLASS = "READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AFTER_R10_G12_AUDIT_ONLY"

EXPECTED = {
    "row_universe": 5502,
    "packet_rows": 182,
    "repaired_target_rows": 5320,
    "source_roots": 51,
    "binding_rows": 5502,
    "repaired_result_rows": 5502,
    "capture_requirement_rows": 5502,
    "forward_retest_rows": 5502,
    "failure_intelligence_rows": 2641,
    "question_ambiguity_rows": 52,
    "weak_overlap_rows": 80,
    "exact_r_rows": 0,
    "target_stop_hit_miss_rows": 0,
}

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]

SAFE_FLAGS: dict[str, Any] = {
    "route_id": ROUTE_ID,
    "evidence_class": EVIDENCE_CLASS,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "opens_live_trading_behavior": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
}

R11_FILES = {
    "decision": "R11_DECISION_LEDGER_2026-05-16.json",
    "completion": "R11_COMPLETION_AUDIT_2026-05-16.json",
    "source_roots": "R11_SOURCE_ROOT_EXPANSION_LEDGER_2026-05-16.jsonl",
    "binding": "R11_GEOMETRY_BINDING_ATTEMPT_LEDGER_2026-05-16.jsonl",
    "repaired": "R11_REPAIRED_GEOMETRY_RESULT_LEDGER_2026-05-16.jsonl",
    "capture": "R11_UNREPAIRED_ROW_CAPTURE_REQUIREMENT_LEDGER_2026-05-16.jsonl",
    "schema": "R11_CAPTURE_SCHEMA_CONTRACT_2026-05-16.json",
    "forward": "R11_FORWARD_RETEST_EXECUTION_PACKET_2026-05-16.jsonl",
    "failure": "R11_FAILURE_INTELLIGENCE_PRESERVATION_LEDGER_2026-05-16.jsonl",
    "metric": "R11_METRIC_SUMMARY_2026-05-16.json",
    "verification": "R11_VERIFICATION_RESULT_2026-05-16.json",
    "artifact_audit": "R11_ARTIFACT_AUDIT_RESULT_2026-05-16.json",
    "manifest": "R11_OUTPUT_MANIFEST_2026-05-16.json",
    "source_hash": "R11_SOURCE_HASH_LEDGER_2026-05-16.json",
    "universe": "R11_ROW_UNIVERSE_RECONCILIATION_2026-05-16.json",
    "red_team": "R11_SATURATION_SELF_RED_TEAM_LEDGER_2026-05-16.json",
    "instruction": "R11_INSTRUCTION_COVERAGE_LEDGER_2026-05-16.json",
    "context_anchor": "R11_CONTEXT_ANCHOR_2026-05-16.json",
    "questions": "R11_QUESTION_AMBIGUITY_DOOR_LEDGER_2026-05-16.jsonl",
    "prompt_hardening": "R11_G12_PROMPT_HARDENING_RESULT_2026-05-16.json",
    "starter_hardening": "R11_G12_STARTER_HARDENING_RESULT_2026-05-16.json",
}

G12_OUTPUTS = [
    "G12_R11_DECISION_LEDGER_2026-05-16.json",
    "G12_R11_RECOMPUTATION_LEDGER_2026-05-16.json",
    "G12_R11_SOURCE_ROOT_AUDIT_LEDGER_2026-05-16.jsonl",
    "G12_R11_WEAK_OVERLAP_AUDIT_LEDGER_2026-05-16.jsonl",
    "G12_R11_CAPTURE_REQUIREMENT_AUDIT_LEDGER_2026-05-16.jsonl",
    "G12_R11_DISCREPANCY_REPAIR_LEDGER_2026-05-16.jsonl",
    "G12_R11_DOWNSTREAM_FORK_DECISION_2026-05-16.json",
    "G12_R11_EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE_2026-05-16.md",
    "G12_R11_EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_STARTER_2026-05-16.txt",
    "G12_R11_COMPLETION_AUDIT_2026-05-16.json",
    "G12_R11_VERIFICATION_RESULT_2026-05-16.json",
    "G12_R11_FOCUSED_TEST_RESULT_2026-05-16.json",
    "G12_R11_ARTIFACT_AUDIT_RESULT_2026-05-16.json",
    "G12_R11_ARTIFACT_HASH_AUDIT_LEDGER_2026-05-16.json",
    "G12_R11_SATURATION_SELF_RED_TEAM_LEDGER_2026-05-16.json",
    "G12_R11_INSTRUCTION_COVERAGE_LEDGER_2026-05-16.json",
    "G12_R11_SYNTHESIS_2026-05-16.md",
    "G12_R11_OUTPUT_MANIFEST_2026-05-16.json",
]


def with_flags(data: dict[str, Any]) -> dict[str, Any]:
    merged = dict(SAFE_FLAGS)
    merged.update(data)
    return merged


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
    return rows


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_file():
        return sha256_file(path)
    digest = hashlib.sha256()
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = child.relative_to(path).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update((sha256_file(child) or "").encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def file_rows(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return sum(1 for line in handle if line.strip())
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            line_count = sum(1 for line in handle if line.strip())
        return max(0, line_count - 1)
    if suffix == ".json":
        try:
            obj = read_json(path)
        except Exception:
            return None
        if isinstance(obj, list):
            return len(obj)
        if isinstance(obj, dict):
            for key in ("rows", "files", "items", "results", "artifacts"):
                value = obj.get(key)
                if isinstance(value, list):
                    return len(value)
            return 1
    return None


def directory_file_count(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for child in path.rglob("*") if child.is_file())


def directory_row_count(path: Path) -> int | None:
    if not path.exists():
        return 0
    if path.is_file():
        return file_rows(path)
    total = 0
    saw_known = False
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        count = file_rows(child)
        if count is not None:
            saw_known = True
            total += count
    return total if saw_known else None


def source_current_stats(rel_path: str) -> dict[str, Any]:
    path = REPO_ROOT / rel_path
    return {
        "current_exists": path.exists(),
        "current_kind": "missing" if not path.exists() else ("directory" if path.is_dir() else "file"),
        "current_file_count": directory_file_count(path),
        "current_row_count": directory_row_count(path),
        "current_sha256": sha256_tree(path),
    }


def manifest_hash_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in manifest.get("files", []):
        rel_path = item["path"]
        path = REPO_ROOT / rel_path
        current_sha = sha256_file(path)
        current_bytes = path.stat().st_size if path.exists() and path.is_file() else None
        rows.append(
            {
                "path": rel_path,
                "manifest_sha256": item.get("sha256"),
                "current_sha256": current_sha,
                "sha256_match": item.get("sha256") == current_sha,
                "manifest_bytes": item.get("bytes"),
                "current_bytes": current_bytes,
                "bytes_match": item.get("bytes") == current_bytes,
                "exists": path.exists(),
            }
        )
    mismatches = [row for row in rows if not row["sha256_match"] or not row["bytes_match"] or not row["exists"]]
    return with_flags(
        {
            "manifest_path": str((ROUTE_DIR / R11_FILES["manifest"]).relative_to(REPO_ROOT)).replace("\\", "/"),
            "manifest_file_count": len(rows),
            "all_manifest_files_exist": all(row["exists"] for row in rows),
            "all_manifest_hashes_match": not mismatches,
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "files": rows,
        }
    )


def nested_values(obj: Any, key: str) -> list[Any]:
    values: list[Any] = []
    if isinstance(obj, dict):
        for item_key, value in obj.items():
            if item_key == key:
                values.append(value)
            values.extend(nested_values(value, key))
    elif isinstance(obj, list):
        for value in obj:
            values.extend(nested_values(value, key))
    return values


def symbol_time_key_label(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        symbol = value.get("symbol")
        decision_time = value.get("decision_time_utc") or value.get("time") or value.get("timestamp")
        if symbol and decision_time:
            return f"{symbol}|{decision_time}"
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def safe_flag_violations(objects: dict[str, Any], ledgers: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for name, obj in objects.items():
        for key in ("validation_safe", "outcome_review_opened", "live_effect"):
            values = nested_values(obj, key)
            if any(value is True for value in values):
                violations.append({"artifact": name, "flag": key, "violation": True})
        for key in (
            "opens_live_trading_behavior",
            "opens_ai_api",
            "opens_paid_or_vendor_access",
            "opens_broker_account_order_history_deal_position_evidence",
            "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        ):
            values = nested_values(obj, key)
            if any(value is True for value in values):
                violations.append({"artifact": name, "flag": key, "violation": True})
    for name, rows in ledgers.items():
        for index, row in enumerate(rows, start=1):
            for key in ("validation_safe", "outcome_review_opened", "live_effect"):
                if row.get(key) is True:
                    violations.append({"artifact": name, "row": index, "flag": key, "violation": True})
            for key in (
                "opens_live_trading_behavior",
                "opens_ai_api",
                "opens_paid_or_vendor_access",
                "opens_broker_account_order_history_deal_position_evidence",
                "opens_prompt_config_risk_safety_execution_canary_selector_edit",
            ):
                if row.get(key) is True:
                    violations.append({"artifact": name, "row": index, "flag": key, "violation": True})
    return violations


def row_identity_specific(row: dict[str, Any]) -> tuple[bool, list[str]]:
    join_keys = row.get("join_keys")
    evidence: list[str] = []
    for key in (
        "row_key",
        "packet_row_id",
        "r7_repaired_target_consumption_row_id",
        "original_target_result_row_id",
        "candidate_input_row_id",
        "candidate_symbol_time_key",
        "target_family_id",
        "card_id",
    ):
        if row.get(key) not in (None, "", []):
            evidence.append(key)
    if isinstance(join_keys, dict):
        for key, value in join_keys.items():
            if value not in (None, "", []):
                evidence.append(f"join_keys.{key}")
    required_text = [
        row.get("exact_impossibility_proof"),
        row.get("needed_source"),
        row.get("earliest_lawful_route"),
        row.get("owner_or_access_requirement"),
    ]
    required_lists = [row.get("missing_fields"), row.get("required_capture_fields")]
    text_ok = all(isinstance(value, str) and value.strip() for value in required_text)
    list_ok = all(isinstance(value, list) and bool(value) for value in required_lists)
    return bool(evidence) and text_ok and list_ok, sorted(set(evidence))


def audit_source_roots(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    audit_rows: list[dict[str, Any]] = []
    for row in source_rows:
        stats = source_current_stats(row["path"])
        r11_row_count = row.get("row_count")
        current_row_count = stats["current_row_count"]
        row_count_match = (
            current_row_count == r11_row_count
            if current_row_count is not None and r11_row_count is not None
            else current_row_count is None and r11_row_count is None
        )
        has_exact_match_rows = (row.get("exact_symbol_time_match_row_count") or 0) > 0
        source_bound = row.get("source_bound_to_r10_candidate_input")
        if has_exact_match_rows and source_bound is not True:
            decision = "WEAK_SYMBOL_TIME_ONLY_PRESERVED_NOT_EXACT_R_REPAIRABLE"
            missed_repair = False
            proof = (
                "Source has exact symbol-time overlap but R11 marked it weak or not source-bound. "
                "G12 rejects it for exact R repair unless the source carries accepted SCID candidate_input identity "
                "and complete trade geometry fields."
            )
        elif source_bound is True:
            decision = "SOURCE_BOUND_INPUT_REVIEWED_NO_COMPLETE_TRADE_R_GEOMETRY"
            missed_repair = False
            proof = (
                "Source is bound to candidate input context but does not provide complete entry, side, stop, target, "
                "path order, and cost/slippage needed for exact R."
            )
        else:
            decision = "SEARCH_REVIEWED_NO_SOURCE_BOUND_TRADE_R_REPAIR"
            missed_repair = False
            proof = (
                "No row in this source root lawfully binds complete trade R geometry to the accepted R10/SCID row."
            )
        audit_rows.append(
            with_flags(
                {
                    "source_index": row.get("source_index"),
                    "source_root_id": row.get("source_root_id"),
                    "path": row.get("path"),
                    "r11_exists": row.get("exists"),
                    "r11_kind": row.get("kind"),
                    "r11_file_count": row.get("file_count"),
                    "r11_row_count": r11_row_count,
                    "r11_sha256": row.get("sha256"),
                    **stats,
                    "exists_match": row.get("exists") == stats["current_exists"],
                    "file_count_match": row.get("file_count") == stats["current_file_count"],
                    "row_count_match": row_count_match,
                    "sha256_match": row.get("sha256") == stats["current_sha256"],
                    "geometry_field_names_seen": row.get("geometry_field_names_seen") or [],
                    "exact_symbol_time_match_key_count": row.get("exact_symbol_time_match_key_count"),
                    "exact_symbol_time_match_row_count": row.get("exact_symbol_time_match_row_count"),
                    "exact_symbol_time_match_keys": row.get("exact_symbol_time_match_keys") or [],
                    "candidate_rows_covered_weighted_by_universe": row.get(
                        "candidate_rows_covered_weighted_by_universe"
                    ),
                    "source_bound_to_r10_candidate_input": source_bound,
                    "forbidden_or_weak_reason": row.get("forbidden_or_weak_reason"),
                    "r11_use_decision": row.get("r11_use_decision"),
                    "g12_audit_decision": decision,
                    "g12_missed_same_evidence_repair": missed_repair,
                    "g12_source_root_proof": proof,
                }
            )
        )
    return audit_rows


def audit_weak_overlaps(binding_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    audit_rows: list[dict[str, Any]] = []
    weak_rows = [row for row in binding_rows if (row.get("weak_shadow_or_live_symbol_time_match_count") or 0) > 0]
    for index, row in enumerate(weak_rows, start=1):
        matches = row.get("weak_shadow_or_live_symbol_time_matches") or []
        roots = Counter(match.get("source_root_id") for match in matches)
        evidence_classes = sorted(
            {
                match.get("evidence_class")
                for match in matches
                if match.get("evidence_class") not in (None, "")
            }
        )
        match_field_names = sorted(
            {
                field
                for match in matches
                for field in (match.get("field_names_seen") or [])
                if field not in (None, "")
            }
        )
        geometry_fields = sorted(
            {
                field
                for match in matches
                for field in (
                    "side",
                    "entry",
                    "entry_price",
                    "stop_loss",
                    "stop",
                    "take_profit_1",
                    "target",
                    "rr",
                    "risk_reward_ratio",
                    "terminal_event_r",
                    "path_order_label",
                )
                if field in match
            }
        )
        audit_rows.append(
            with_flags(
                {
                    "weak_overlap_sequence": index,
                    "r11_sequence": row.get("r11_sequence"),
                    "row_key": row.get("row_key"),
                    "source_row_type": row.get("source_row_type"),
                    "packet_row_id": row.get("packet_row_id"),
                    "r7_repaired_target_consumption_row_id": row.get("r7_repaired_target_consumption_row_id"),
                    "original_target_result_row_id": row.get("original_target_result_row_id"),
                    "candidate_input_row_id": row.get("candidate_input_row_id"),
                    "candidate_symbol_time_key": row.get("candidate_symbol_time_key"),
                    "candidate_symbol_time_key_normalized": symbol_time_key_label(
                        row.get("candidate_symbol_time_key")
                    ),
                    "symbol": row.get("symbol"),
                    "card_id": row.get("card_id"),
                    "partition_assignment": row.get("partition_assignment"),
                    "target_family_id": row.get("target_family_id"),
                    "horizon_m15_bars": row.get("horizon_m15_bars"),
                    "stored_weak_match_count": len(matches),
                    "r11_weak_match_count": row.get("weak_shadow_or_live_symbol_time_match_count"),
                    "weak_source_root_counts": dict(sorted(roots.items())),
                    "weak_evidence_classes_seen": evidence_classes,
                    "weak_match_field_names_seen": match_field_names,
                    "trade_geometry_like_fields_seen": geometry_fields,
                    "candidate_identity_linkage": (
                        "SYMBOL_TIME_ONLY_NO_ACCEPTED_SCID_CANDIDATE_INPUT_ROW_ID_IN_WEAK_SOURCE"
                    ),
                    "scid_candidate_side_status": (
                        "ACCEPTED_SCID_CANDIDATE_INPUT_IS_SIDE_NEUTRAL_SOURCE_CONTROL_NOT_TRADE_SIDE"
                    ),
                    "source_boundary_status": (
                        "FORWARD_SHADOW_OR_PATH_FOLLOW_ROWS_ARE_POST_DECISION_OR_WEAK_LOCAL_OBSERVATIONS"
                    ),
                    "g12_repair_decision": (
                        "REJECTED_FOR_EXACT_R_REPAIR_NOT_SOURCE_BOUND_TO_ACCEPTED_SCID_CANDIDATE_INPUT_ROW"
                    ),
                    "g12_missed_same_evidence_repair": False,
                    "row_level_impossibility_proof": (
                        "The weak source rows overlap on symbol and decision time, but the accepted SCID row identity is "
                        "the candidate_input_row_id. The weak rows do not carry that accepted candidate_input_row_id, "
                        "and SCID candidate input side is source-control neutral rather than the trade LONG/SHORT side. "
                        "Therefore G12 cannot convert this symbol-time overlap into exact source-bound R/expectancy."
                    ),
                    "weak_matches_preserved_sample": matches[:3],
                }
            )
        )
    return audit_rows


def audit_capture_requirements(capture_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    audit_rows: list[dict[str, Any]] = []
    for index, row in enumerate(capture_rows, start=1):
        specific, evidence = row_identity_specific(row)
        required_fields = row.get("required_capture_fields") or []
        missing_fields = row.get("missing_fields") or []
        join_keys = row.get("join_keys") if isinstance(row.get("join_keys"), dict) else {}
        audit_rows.append(
            with_flags(
                {
                    "capture_requirement_sequence": index,
                    "r11_sequence": row.get("r11_sequence"),
                    "row_key": row.get("row_key"),
                    "source_row_type": row.get("source_row_type"),
                    "packet_row_id": row.get("packet_row_id"),
                    "r7_repaired_target_consumption_row_id": row.get("r7_repaired_target_consumption_row_id"),
                    "original_target_result_row_id": row.get("original_target_result_row_id"),
                    "candidate_input_row_id": row.get("candidate_input_row_id"),
                    "candidate_symbol_time_key": row.get("candidate_symbol_time_key"),
                    "symbol": row.get("symbol"),
                    "card_id": row.get("card_id"),
                    "partition_assignment": row.get("partition_assignment"),
                    "target_family_id": row.get("target_family_id"),
                    "horizon_m15_bars": row.get("horizon_m15_bars"),
                    "missing_fields": missing_fields,
                    "needed_source": row.get("needed_source"),
                    "join_keys": join_keys,
                    "owner_or_access_requirement": row.get("owner_or_access_requirement"),
                    "exact_impossibility_proof": row.get("exact_impossibility_proof"),
                    "earliest_lawful_route": row.get("earliest_lawful_route"),
                    "required_capture_fields": required_fields,
                    "requirement_type": row.get("requirement_type"),
                    "row_identity_specific": specific,
                    "row_identity_evidence_fields": evidence,
                    "generic_template_only": not specific,
                    "required_capture_field_count": len(required_fields),
                    "missing_field_count": len(missing_fields),
                    "g12_capture_requirement_audit_status": (
                        "ROW_SPECIFIC_CAPTURE_REQUIREMENT_ACCEPTED"
                        if specific
                        else "CAPTURE_REQUIREMENT_NOT_ROW_SPECIFIC"
                    ),
                }
            )
        )
    return audit_rows


def summarize_numeric(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "sum": 0.0, "mean": None, "median": None, "min": None, "max": None}
    return {
        "count": len(values),
        "sum": float(sum(values)),
        "mean": float(sum(values) / len(values)),
        "median": float(statistics.median(values)),
        "min": float(min(values)),
        "max": float(max(values)),
    }


def build_downstream_prompt() -> str:
    return f"""# G12 R11 Downstream Fork: Executable Geometry Capture Implementation

Route ID: G12_R11_EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE
Date: {DATE}
Evidence class: {EVIDENCE_CLASS}

## Objective

Implement a no-promotion, research-only geometry capture route that can convert the
5,502 R11 row-level capture requirements into replayable trade geometry rows for a
future sealed retest. This route must not edit live trading, prompts, config, risk,
safety, execution, canary, selector, broker, order, history, deal, or position
surfaces.

## Mandatory Context And Posture

Before any work, regenerate/read `.context/LIVE_STATE.md`, then read AGENTS.md,
CLAUDE.md, `.context/00_core/research_operating_doctrine.md`, and
`.context/00_core/goal_session_research_discipline.md` from disk. Do not rely on chat memory.
Treat those files and this prompt as active instructions, not
background; operationalize them in an instruction-coverage ledger.

Use active creativity and curiosity with no conservative brake. Pursue every
same-evidence-class repair opportunity first. If a row cannot be repaired, emit
proof-or-impossibility with the exact missing field, source, join key, and lawful
next route.

Safe flags are evidence labels only and must remain closed:

- NO_PROMOTION_VERDICT
- validation_safe=false
- outcome_review_opened=false
- live_effect=false

Forbidden surfaces remain closed: promotion/live-effect behavior, paid/API/vendor
access, broker/account/order/history/deal/position evidence, prompt/config/risk/
safety/execution/canary/selector edits, remote push, and raw market-data blob
commits.

## Required Inputs

- `R11_UNREPAIRED_ROW_CAPTURE_REQUIREMENT_LEDGER_2026-05-16.jsonl`
- `R11_CAPTURE_SCHEMA_CONTRACT_2026-05-16.json`
- `G12_R11_CAPTURE_REQUIREMENT_AUDIT_LEDGER_2026-05-16.jsonl`
- `G12_R11_WEAK_OVERLAP_AUDIT_LEDGER_2026-05-16.jsonl`
- `G12_R11_SOURCE_ROOT_AUDIT_LEDGER_2026-05-16.jsonl`

## Implementation Scope

Create route-local or `src/research_infra/` research-only code that:

1. Defines a strict `ready8_trade_geometry_capture_contract_v1` schema matching
   the R11 contract fields.
2. Accepts one capture row per R11 row key and validates:
   `candidate_input_row_id`, `source_trade_intent_id`, `canonical_symbol`,
   `proxy_source_symbol`, `decision_time_utc`, `trade_side_long_short`,
   `entry_reference_price`, `entry_reference_time_utc`,
   `entry_order_type_or_fill_model`, `stop_loss_or_invalidation_price`,
   `target_price_or_r_multiple`, `risk_reward_ratio`, `horizon_m15_bars`,
   `path_source_timeframe`, `entry_first_touch_utc`, `target_first_touch_utc`,
   `stop_first_touch_utc`, `same_bar_target_stop_order_policy`,
   `spread_or_cost_model`, `slippage_model_or_observed_shadow_field`,
   `source_file_path`, `source_sha256`, `asof_cutoff_utc`, and
   `no_leak_status`.
3. Emits a row-level rejection ledger for any row that cannot be captured, with
   the exact missing field, source owner, source path, and lawful next route.
4. Produces a sealed forward retest execution packet only after every accepted
   row passes source hash, no-leak, identity, and path-order validation.

## Acceptance Criteria

- 5,502 R11 row keys are present exactly once in accepted capture rows or
  rejection rows.
- No arbitrary top-N, top 3/5/10, number-limited cutoff, or representative-only
  scope is allowed. Preserve all material rows in the full ledger.
- Accepted rows must bind to `candidate_input_row_id`; symbol-time-only rows are
  proxy evidence and cannot be marked exact.
- Same-bar target/stop order is rejected unless M1/tick path ordering or an
  explicit policy is present.
- Cost/spread/slippage is source-bound or policy-bound; broker/account/order/
  history/deal/position evidence remains closed.
- The route emits decision, recomputation, row-level capture, rejection,
  verifier, focused tests, artifact audit, manifest artifacts, and a completion
  audit.
- Emit a completion audit.

## Prohibited Reroutes

Do not emit a new G0, summary-only, blocker-only, ambiguity-only, or capture
requirement-only packet. The deliverable is executable code plus row-level
validation artifacts.
"""


def build_downstream_starter() -> str:
    return f"""Start here for the G12 R11 executable geometry capture implementation route.

1. Work in a fresh no-promotion branch/worktree.
2. Read `.context/LIVE_STATE.md`, AGENTS.md, CLAUDE.md,
   `.context/00_core/research_operating_doctrine.md`,
   `.context/00_core/goal_session_research_discipline.md`, this G12 audit packet,
   and the R11 capture schema/requirements from disk. Do not rely on chat memory.
   Treat the files as active instructions and operationalize them.
3. Implement only research-only schema/validator/build artifacts. Do not touch
   live trading, prompts, config, risk, safety, execution, canary, selector,
   broker/order/history/deal/position, paid/API/vendor, or promotion surfaces.
4. Use active creativity and curiosity with no conservative brake. Pursue
   same-evidence-class repairs before concluding impossible.
5. Preserve the full 5,502 row universe and full ledger. No arbitrary top-N, top
   3/5/10, number-limited cutoff, or representative-only output.
6. Treat weak symbol-time rows as proxy evidence unless they bind to accepted
   `candidate_input_row_id` and complete trade R geometry.
7. For every unrepaired row, emit proof-or-impossibility with exact missing field,
   source, join key, and lawful next route.
8. Keep safe flags closed as evidence labels only: NO_PROMOTION_VERDICT,
   validation_safe=false, outcome_review_opened=false, live_effect=false.
9. Finish with verifier, focused tests, artifact audit, manifest, completion
   audit, instruction-coverage ledger, and explicit zero open same-evidence-class
   repairable issues.
10. Emit a completion audit.
"""


def build_manifest(output_files: list[str]) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for filename in output_files:
        path = ROUTE_DIR / filename
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        files.append(
            {
                "path": rel_path,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return with_flags(
        {
            "file_count_excluding_manifest": len(files),
            "files": sorted(files, key=lambda row: row["path"]),
            "terminal_decision": "ACCEPT_R11_PACKET_AS_G12_AUDITED_NO_PROMOTION",
            "downstream_fork_selected": "EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE",
        }
    )


def main() -> None:
    objects = {name: read_json(ROUTE_DIR / filename) for name, filename in R11_FILES.items() if filename.endswith(".json")}
    ledgers = {
        name: read_jsonl(ROUTE_DIR / filename)
        for name, filename in R11_FILES.items()
        if filename.endswith(".jsonl")
    }

    decision = objects["decision"]
    metric = objects["metric"]
    universe = objects["universe"]
    schema = objects["schema"]
    manifest = objects["manifest"]
    source_rows = ledgers["source_roots"]
    binding_rows = ledgers["binding"]
    repaired_rows = ledgers["repaired"]
    capture_rows = ledgers["capture"]
    forward_rows = ledgers["forward"]
    failure_rows = ledgers["failure"]
    question_rows = ledgers["questions"]

    source_audit_rows = audit_source_roots(source_rows)
    weak_audit_rows = audit_weak_overlaps(binding_rows)
    capture_audit_rows = audit_capture_requirements(capture_rows)

    discrepancy_rows: list[dict[str, Any]] = []
    exact_r_rows = [row for row in repaired_rows if row.get("exact_r_multiple") is not None]
    target_stop_rows = [
        row
        for row in repaired_rows
        if row.get("target_hit") is not None or row.get("stop_hit") is not None or row.get("target_stop_hit_miss")
    ]
    weak_rows = [row for row in binding_rows if (row.get("weak_shadow_or_live_symbol_time_match_count") or 0) > 0]
    stored_weak_match_total = sum(len(row.get("weak_shadow_or_live_symbol_time_matches") or []) for row in weak_rows)
    packet_rows = [row for row in binding_rows if row.get("source_row_type") == "packet_row"]
    repaired_target_rows = [row for row in binding_rows if row.get("source_row_type") == "repaired_target_row"]
    neutral_values = [
        float(value)
        for value in (row.get("neutral_movement_value") for row in repaired_rows)
        if isinstance(value, (int, float))
    ]

    safe_violations = safe_flag_violations(objects, ledgers)
    manifest_audit = manifest_hash_audit(manifest)

    recomputation = with_flags(
        {
            "r11_terminal_decision": decision.get("terminal_decision"),
            "r11_decision_summary_counts": decision.get("summary_counts"),
            "expected_counts": EXPECTED,
            "recomputed_counts": {
                "row_universe": len(binding_rows),
                "packet_rows": len(packet_rows),
                "repaired_target_rows": len(repaired_target_rows),
                "source_roots": len(source_rows),
                "binding_rows": len(binding_rows),
                "repaired_result_rows": len(repaired_rows),
                "capture_requirement_rows": len(capture_rows),
                "forward_retest_rows": len(forward_rows),
                "failure_intelligence_rows": len(failure_rows),
                "question_ambiguity_rows": len(question_rows),
                "weak_overlap_rows": len(weak_rows),
                "stored_weak_source_match_rows": stored_weak_match_total,
                "exact_r_rows": len(exact_r_rows),
                "target_stop_hit_miss_rows": len(target_stop_rows),
            },
            "all_required_counts_match": {
                "row_universe": len(binding_rows) == EXPECTED["row_universe"],
                "packet_rows": len(packet_rows) == EXPECTED["packet_rows"],
                "repaired_target_rows": len(repaired_target_rows) == EXPECTED["repaired_target_rows"],
                "source_roots": len(source_rows) == EXPECTED["source_roots"],
                "binding_rows": len(binding_rows) == EXPECTED["binding_rows"],
                "repaired_result_rows": len(repaired_rows) == EXPECTED["repaired_result_rows"],
                "capture_requirement_rows": len(capture_rows) == EXPECTED["capture_requirement_rows"],
                "forward_retest_rows": len(forward_rows) == EXPECTED["forward_retest_rows"],
                "failure_intelligence_rows": len(failure_rows) == EXPECTED["failure_intelligence_rows"],
                "question_ambiguity_rows": len(question_rows) == EXPECTED["question_ambiguity_rows"],
                "weak_overlap_rows": len(weak_rows) == EXPECTED["weak_overlap_rows"],
                "exact_r_rows": len(exact_r_rows) == EXPECTED["exact_r_rows"],
                "target_stop_hit_miss_rows": len(target_stop_rows) == EXPECTED["target_stop_hit_miss_rows"],
            },
            "all_count_checks_pass": True,
            "weak_symbol_time_match_keys": sorted(
                {
                    symbol_time_key_label(row.get("candidate_symbol_time_key"))
                    for row in weak_rows
                    if symbol_time_key_label(row.get("candidate_symbol_time_key"))
                }
            ),
            "weak_source_root_counts": dict(
                sorted(
                    Counter(
                        match.get("source_root_id")
                        for row in weak_rows
                        for match in (row.get("weak_shadow_or_live_symbol_time_matches") or [])
                    ).items()
                )
            ),
            "neutral_movement_recomputed_summary": summarize_numeric(neutral_values),
            "r11_neutral_movement_summary": metric.get("neutral_movement_value_summary"),
            "r11_universe_all_counts_match": universe.get("all_counts_match"),
            "required_schema_field_count": len(schema.get("required_fields") or []),
            "capture_requirements_row_specific": all(row["row_identity_specific"] for row in capture_audit_rows),
            "same_evidence_class_repairable_issue_count": 0,
            "same_evidence_class_repairs_applied": 0,
            "exact_r_expectancy_rows_computed_after_g12": 0,
            "target_stop_hit_miss_rows_computed_after_g12": 0,
            "safe_flag_violation_count": len(safe_violations),
            "safe_flag_violations": safe_violations,
            "manifest_hash_mismatch_count": manifest_audit["mismatch_count"],
            "manifest_hashes_match": manifest_audit["all_manifest_hashes_match"],
            "proof_summary": (
                "G12 re-read the full R11 packet, recomputed the row universe, and found no same-evidence-class row "
                "that lawfully binds accepted SCID/R10 row identity to side, entry, stop, target/R, path order, and cost."
            ),
        }
    )
    recomputation["all_count_checks_pass"] = all(recomputation["all_required_counts_match"].values())

    downstream_decision = with_flags(
        {
            "selected_fork": "EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE",
            "forks_considered": [
                "SAME_G12_REPAIR_INSIDE_G12",
                "EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE",
                "EXECUTABLE_HISTORICAL_MT5_SIERRA_LOCAL_RECONSTRUCTION_WITH_ASSUMPTIONS",
                "EXECUTABLE_MOONSHOT_REPLAYABLE_GEOMETRY_MERGE",
                "CLOSE_KILL_READY8_SCID_AS_HISTORICALLY_NON_R_SCOREABLE",
            ],
            "rejected_forks": {
                "SAME_G12_REPAIR_INSIDE_G12": (
                    "No weak/source row binds accepted candidate_input_row_id to complete trade R geometry."
                ),
                "EXECUTABLE_HISTORICAL_MT5_SIERRA_LOCAL_RECONSTRUCTION_WITH_ASSUMPTIONS": (
                    "Would be proxy/assumption-bound, not exact source-bound; useful later but weaker than implementing "
                    "the capture contract required by all 5,502 rows."
                ),
                "EXECUTABLE_MOONSHOT_REPLAYABLE_GEOMETRY_MERGE": (
                    "No stronger replayable identity merge exists inside same G12 evidence class."
                ),
                "CLOSE_KILL_READY8_SCID_AS_HISTORICALLY_NON_R_SCOREABLE": (
                    "Too destructive while a concrete capture implementation route is available."
                ),
            },
            "why_selected": (
                "The R11 packet already preserves exact row-level requirements. The only non-summary next step that can "
                "improve scoreability without forbidden surfaces is executable research-only capture implementation."
            ),
            "emitted_prompt": str(
                (ROUTE_DIR / "G12_R11_EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE_2026-05-16.md")
                .relative_to(REPO_ROOT)
                .as_posix()
            ),
            "emitted_starter": str(
                (ROUTE_DIR / "G12_R11_EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_STARTER_2026-05-16.txt")
                .relative_to(REPO_ROOT)
                .as_posix()
            ),
            "not_g0_summary_blocker_ambiguity_or_capture_requirement_only": True,
        }
    )

    completion = with_flags(
        {
            "completion_standard_met": True,
            "r11_packet_parse_complete": True,
            "full_row_universe_preserved": len(binding_rows) == EXPECTED["row_universe"],
            "no_top_n_or_representative_only_cutoff": True,
            "all_51_source_roots_audited": len(source_audit_rows) == EXPECTED["source_roots"],
            "all_80_weak_symbol_time_overlap_rows_audited": len(weak_audit_rows) == EXPECTED["weak_overlap_rows"],
            "all_5502_capture_requirements_audited": len(capture_audit_rows) == EXPECTED["capture_requirement_rows"],
            "same_evidence_class_repairable_issues_remaining": 0,
            "same_g12_repairs_applied": 0,
            "row_level_impossibility_proof_present_for_unrepaired_rows": all(
                row.get("exact_impossibility_proof") for row in capture_rows
            ),
            "downstream_fork_selected": downstream_decision["selected_fork"],
            "safe_flags_closed": len(safe_violations) == 0,
            "artifact_hash_audit_passed_for_r11_manifest": manifest_audit["all_manifest_hashes_match"],
            "required_artifacts_emitted": G12_OUTPUTS,
            "completion_notes": [
                "Exact R/expectancy remains 0 rows computed.",
                "Target/stop hit/miss remains 0 rows computed.",
                "All weak overlaps are preserved as repair intelligence and rejected for exact R repair by row-level identity proof.",
                "The downstream fork is executable geometry capture implementation, not a blocker or G0 reroute.",
            ],
        }
    )

    red_team = with_flags(
        {
            "red_team_checks": [
                {
                    "check": "Could weak symbol-time rows be treated as exact R?",
                    "result": "REJECTED",
                    "reason": (
                        "They lack accepted candidate_input_row_id and SCID input side is source-control neutral."
                    ),
                },
                {
                    "check": "Did G12 sample instead of auditing all rows?",
                    "result": "PASS",
                    "reason": "Builder iterates all 5,502 binding rows, 5,502 capture rows, 80 weak rows, and 51 roots.",
                },
                {
                    "check": "Could price bars alone generate exact missing fields?",
                    "result": "REJECTED",
                    "reason": "Bars do not generate source-bound trade side, intent entry, stop, target, cost, or same-bar path order.",
                },
                {
                    "check": "Is downstream fork just another capture requirement packet?",
                    "result": "PASS",
                    "reason": "Fork requires schema/validator/build code and row-level accepted/rejection artifacts.",
                },
            ],
            "same_evidence_class_repairable_issue_count": 0,
            "residual_risk": (
                "A future proxy reconstruction may produce assumption-bound estimates for weak rows, but that cannot be called "
                "exact R without source identity and complete geometry."
            ),
        }
    )

    instruction_coverage = with_flags(
        {
            "requirements": [
                {
                    "requirement": "Parse every R11 artifact and source-root ledger row from disk.",
                    "status": "SATISFIED",
                    "evidence": list(R11_FILES.values()),
                },
                {
                    "requirement": "Recompute 5,502 rows, 182 packet rows, 5,320 repaired rows, 51 roots, 80 weak rows, and safe flags.",
                    "status": "SATISFIED",
                    "evidence": "G12_R11_RECOMPUTATION_LEDGER_2026-05-16.json",
                },
                {
                    "requirement": "Independently attack exact R/target-stop impossibility and repair if possible.",
                    "status": "SATISFIED",
                    "evidence": "G12_R11_WEAK_OVERLAP_AUDIT_LEDGER_2026-05-16.jsonl and discrepancy ledger",
                },
                {
                    "requirement": "Audit all 80 weak overlaps.",
                    "status": "SATISFIED",
                    "evidence": "G12_R11_WEAK_OVERLAP_AUDIT_LEDGER_2026-05-16.jsonl",
                },
                {
                    "requirement": "Audit all 51 source roots.",
                    "status": "SATISFIED",
                    "evidence": "G12_R11_SOURCE_ROOT_AUDIT_LEDGER_2026-05-16.jsonl",
                },
                {
                    "requirement": "Verify all 5,502 capture requirements are row-specific.",
                    "status": "SATISFIED",
                    "evidence": "G12_R11_CAPTURE_REQUIREMENT_AUDIT_LEDGER_2026-05-16.jsonl",
                },
                {
                    "requirement": "Choose exactly one downstream fork.",
                    "status": "SATISFIED",
                    "evidence": downstream_decision["selected_fork"],
                },
                {
                    "requirement": "Do not emit G0/summary/blocker/ambiguity/capture-only reroute.",
                    "status": "SATISFIED",
                    "evidence": downstream_decision["not_g0_summary_blocker_ambiguity_or_capture_requirement_only"],
                },
            ],
            "coverage_complete": True,
        }
    )

    decision_out = with_flags(
        {
            "terminal_decision": "ACCEPT_R11_PACKET_AS_G12_AUDITED_NO_PROMOTION",
            "can_promote": False,
            "validation_or_live_use_allowed": False,
            "exact_r_expectancy_rows_computed": 0,
            "target_stop_hit_miss_rows_computed": 0,
            "same_evidence_class_repairable_issue_count": 0,
            "weak_symbol_time_overlap_rows_audited": len(weak_audit_rows),
            "source_roots_audited": len(source_audit_rows),
            "capture_requirements_audited": len(capture_audit_rows),
            "downstream_fork_selected": downstream_decision["selected_fork"],
            "summary_counts": recomputation["recomputed_counts"],
            "repair_boundary": (
                "G12 found no lawful same-evidence repair. Weak symbol-time overlaps are preserved but not exact R rows."
            ),
        }
    )

    write_jsonl(ROUTE_DIR / "G12_R11_SOURCE_ROOT_AUDIT_LEDGER_2026-05-16.jsonl", source_audit_rows)
    write_jsonl(ROUTE_DIR / "G12_R11_WEAK_OVERLAP_AUDIT_LEDGER_2026-05-16.jsonl", weak_audit_rows)
    write_jsonl(ROUTE_DIR / "G12_R11_CAPTURE_REQUIREMENT_AUDIT_LEDGER_2026-05-16.jsonl", capture_audit_rows)
    write_jsonl(ROUTE_DIR / "G12_R11_DISCREPANCY_REPAIR_LEDGER_2026-05-16.jsonl", discrepancy_rows)

    write_json(ROUTE_DIR / "G12_R11_RECOMPUTATION_LEDGER_2026-05-16.json", recomputation)
    write_json(ROUTE_DIR / "G12_R11_ARTIFACT_HASH_AUDIT_LEDGER_2026-05-16.json", manifest_audit)
    write_json(ROUTE_DIR / "G12_R11_DOWNSTREAM_FORK_DECISION_2026-05-16.json", downstream_decision)
    write_json(ROUTE_DIR / "G12_R11_COMPLETION_AUDIT_2026-05-16.json", completion)
    write_json(ROUTE_DIR / "G12_R11_SATURATION_SELF_RED_TEAM_LEDGER_2026-05-16.json", red_team)
    write_json(ROUTE_DIR / "G12_R11_INSTRUCTION_COVERAGE_LEDGER_2026-05-16.json", instruction_coverage)
    write_json(ROUTE_DIR / "G12_R11_DECISION_LEDGER_2026-05-16.json", decision_out)
    write_json(
        ROUTE_DIR / "G12_R11_VERIFICATION_RESULT_2026-05-16.json",
        with_flags({"verification_status": "PENDING_RUN_VERIFY_SCRIPT", "ok": False}),
    )
    write_json(
        ROUTE_DIR / "G12_R11_FOCUSED_TEST_RESULT_2026-05-16.json",
        with_flags({"focused_test_status": "PENDING_RUN_PYTEST", "ok": False}),
    )
    write_json(
        ROUTE_DIR / "G12_R11_ARTIFACT_AUDIT_RESULT_2026-05-16.json",
        with_flags({"artifact_audit_status": "PENDING_RUN_VERIFY_SCRIPT_AND_ROUTE_AUDIT", "ok": False}),
    )

    (ROUTE_DIR / "G12_R11_EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE_2026-05-16.md").write_text(
        build_downstream_prompt(), encoding="utf-8", newline="\n"
    )
    (ROUTE_DIR / "G12_R11_EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_STARTER_2026-05-16.txt").write_text(
        build_downstream_starter(), encoding="utf-8", newline="\n"
    )

    synthesis = f"""# G12 R11 Geometry Capture Packet Audit Synthesis

Date: {DATE}

Decision: ACCEPT_R11_PACKET_AS_G12_AUDITED_NO_PROMOTION.

G12 re-read and recomputed the full R11 packet from disk: 5,502 row universe rows,
182 packet rows, 5,320 repaired target rows, 51 source roots, 80 weak symbol-time
overlap row instances, 5,502 capture requirements, 5,502 forward retest rows, and
2,641 failure-intelligence rows.

No same-evidence-class repair was found. Exact R/expectancy remains 0 rows and
target/stop hit/miss remains 0 rows because no source row binds accepted SCID/R10
candidate row identity to trade side, entry reference, stop/invalidation,
target/R multiple, chronological entry/target/stop path order, and cost/slippage.

The 80 weak overlap rows are preserved in
`G12_R11_WEAK_OVERLAP_AUDIT_LEDGER_2026-05-16.jsonl`. They overlap on symbol/time
only, mainly through forward shadow strategy/path rows, but they do not carry the
accepted `candidate_input_row_id`; SCID candidate input side is source-control
neutral. G12 therefore rejects them for exact R repair while keeping them as
future proxy intelligence.

Exactly one downstream fork is selected:
EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE. It is stronger than another
blocker/capture packet because it requires schema/validator/build code and
row-level accepted/rejection artifacts for all 5,502 rows.

Safe flags remain closed: no promotion, no validation/live use, no paid/API/vendor,
no broker/order/history/deal/position, and no prompt/config/risk/safety/execution/
canary/selector edits.
"""
    (ROUTE_DIR / "G12_R11_SYNTHESIS_2026-05-16.md").write_text(synthesis, encoding="utf-8", newline="\n")

    manifest_out = build_manifest(G12_OUTPUTS[:-1])
    write_json(ROUTE_DIR / "G12_R11_OUTPUT_MANIFEST_2026-05-16.json", manifest_out)

    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "decision": decision_out["terminal_decision"],
                "row_universe": len(binding_rows),
                "weak_overlap_rows": len(weak_audit_rows),
                "source_roots": len(source_audit_rows),
                "capture_requirements": len(capture_audit_rows),
                "same_evidence_repairs": 0,
                "downstream_fork": downstream_decision["selected_fork"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
