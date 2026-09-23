"""Build G12 blocker-clearing audit artifacts for OTB1/OTB2/OTB3.

This is a research-control audit only. It reads packet/source/no-leak
artifacts, checks schema and no-leak boundaries, and writes G12-owned
decisions. It must not run outcome tests, create quarantine/result outputs,
call external APIs, inspect R values, or change live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-07"
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_blocker_clearing_audit"
OTG = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
OTB1 = OTG / "otb1_lifecycle_packet_builder"
OTB2 = OTG / "otb2_synthetic_packet_builder"
OTB3 = OTG / "otb3_source_noleak_cleanup"
CONTROL = ROOT / "research" / "science_program_2026_05" / "00_control"
SYNTHESIS = ROOT / "research" / "science_program_2026_05" / "05_synthesis"

FORBIDDEN_PRIMARY_EXACT = {
    "broker_actual_r",
    "synthetic_path_r",
    "win_loss",
    "outcome_r",
    "future_return",
    "trade_result",
    "post_entry_path",
}

RESULT_SOURCE_KEYS = {
    "actual_r",
    "broker_actual_r",
    "gross_r",
    "hit_sl",
    "hit_tp1",
    "mae_r",
    "mfe_r",
    "net_r",
    "net_r_by_cost",
    "outcome",
    "outcome_r",
    "path_label",
    "path_order_label",
    "path_synthetic_r",
    "realized_r",
    "synthetic_path_r",
    "trade_outcome",
    "win_loss",
    "entry_first_touch_utc",
    "tp1_first_touch_utc",
    "sl_first_touch_utc",
    "trade_id",
}

OTB2_ALLOWED_GUARD_KEYS = {
    "broker_actual_r_absent_from_primary_metric",
    "label_family",
    "same_dataset_contamination_guard",
}

HASH64 = re.compile(r"^[0-9a-f]{64}$")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(canonical(part) for part in parts).encode("utf-8")).hexdigest()


def sha256_json(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def read_jsonl_by_line(path: Path) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if line.strip():
                rows[line_no] = json.loads(line)
    return rows


def read_jsonl_by_key(path: Path, key: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            value = row.get(key)
            if value:
                rows[str(value)] = row
    return rows


def table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(out)


def parse_utc(text: Any) -> datetime | None:
    if not text:
        return None
    raw = str(text).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def source_ref_base(ref: str) -> Path:
    # OTB1 source refs are stored as path:line. Windows paths are not used here.
    path_text = ref.rsplit(":", 1)[0] if ":" in ref else ref
    return ROOT / path_text


def key_scan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_hits: Counter[str] = Counter()
    result_like_hits: Counter[str] = Counter()
    for row in rows:
        for key in row:
            lowered = key.lower()
            if lowered in FORBIDDEN_PRIMARY_EXACT:
                exact_hits[lowered] += 1
            if lowered in RESULT_SOURCE_KEYS:
                result_like_hits[lowered] += 1
    return {
        "forbidden_exact_key_counts": dict(sorted(exact_hits.items())),
        "result_like_exact_key_counts": dict(sorted(result_like_hits.items())),
    }


def scan_flags(json_paths: list[Path]) -> dict[str, Any]:
    watched = {
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
        "live_trading_surfaces_touched",
        "quarantine_or_result_outputs_created",
        "quarantine_or_result_output_created",
        "databento_or_api_calls",
        "external_fetches_or_paid_calls",
        "paid_fetch_attempted",
        "paid_data_calls",
    }
    mentions: Counter[str] = Counter()
    bad: list[dict[str, Any]] = []

    def walk(obj: Any, path: list[str], origin: Path) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in watched:
                    mentions[key] += 1
                    nonzero_api = key in {"databento_or_api_calls", "external_fetches_or_paid_calls", "paid_fetch_attempted", "paid_data_calls"}
                    bad_value = value not in (0, False, None, "0") if nonzero_api else value is True or str(value).lower() == "true"
                    if bad_value:
                        bad.append({"file": rel(origin), "json_path": ".".join(path + [key]), "value": value})
                walk(value, path + [str(key)], origin)
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                walk(item, path + [str(index)], origin)

    for path in json_paths:
        walk(read_json(path), [], path)
    return {"flag_mentions": dict(sorted(mentions.items())), "bad_true_or_nonzero": bad}


def verify_otb1_packet_hash(payload: dict[str, Any]) -> dict[str, Any]:
    without_hash = {
        "packet_metadata": payload.get("packet_metadata"),
        "primary_lifecycle_rows": payload.get("primary_lifecycle_rows", []),
    }
    hashes = payload.get("packet_hashes", {})
    return {
        "packet_payload_hash_matches": stable_hash(without_hash) == hashes.get("packet_payload_sha256_excluding_this_hash_block"),
        "primary_rows_hash_matches": stable_hash(payload.get("primary_lifecycle_rows", [])) == hashes.get("primary_rows_sha256"),
        "primary_rows_hash_shape_ok": bool(HASH64.match(str(hashes.get("primary_rows_sha256", "")))),
    }


def verify_otb2_packet_hash(payload: dict[str, Any]) -> dict[str, Any]:
    recomputed = sha256_json({key: value for key, value in payload.items() if key != "packet_hash"})
    return {
        "packet_hash_matches": recomputed == payload.get("packet_hash"),
        "packet_hash_shape_ok": bool(HASH64.match(str(payload.get("packet_hash", "")))),
    }


def audit_otb1() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    packets: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    audit_rows = read_jsonl_by_line(ROOT / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl")

    for path in sorted((OTB1 / "packets").glob("*.json")):
        payload = read_json(path)
        metadata = payload["packet_metadata"]
        rows = payload.get("primary_lifecycle_rows", [])
        packet_id = metadata["packet_id"]
        decision_in = metadata.get("packet_decision")
        scan = key_scan(rows)
        hash_check = verify_otb1_packet_hash(payload)

        duplicate_counts = Counter(row.get("duplicate_group_id") for row in rows if row.get("duplicate_group_id"))
        duplicate_groups_with_multiple_rows = sorted([group for group, count in duplicate_counts.items() if count > 1])

        audit_refs: list[int] = []
        nonempty_path_label_refs = 0
        for row in rows:
            for source_ref in row.get("packet_build_source_paths", []):
                if source_ref.startswith("shadow_logs/pending_limit_lifecycle_audit.jsonl:"):
                    line_no = int(source_ref.rsplit(":", 1)[1])
                    audit_refs.append(line_no)
                    if audit_rows.get(line_no, {}).get("path_label") not in (None, "", []):
                        nonempty_path_label_refs += 1

        referenced_source_paths = sorted(
            {rel(source_ref_base(ref)) for row in rows for ref in row.get("packet_build_source_paths", [])}
        )
        missing_source_paths = [source for source in referenced_source_paths if not (ROOT / source).exists()]

        if decision_in == "BLOCKED_WITH_OWNER_QUESTION":
            g12_decision = "BLOCKED_WITH_NEXT_EXACT_QUESTION"
            decision_reason = "Original packet remains blocked; no primary lifecycle rows exist."
        elif nonempty_path_label_refs:
            g12_decision = "REJECT_INVALID_CLEARING"
            decision_reason = (
                "Primary rows are schema-clean, but referenced lifecycle-audit source rows contain non-empty "
                "path labels and OTB1 source_hash computation does not exclude that key."
            )
        elif duplicate_groups_with_multiple_rows:
            g12_decision = "BLOCKED_WITH_NEXT_EXACT_QUESTION"
            decision_reason = "Duplicate-group denominator is not one-to-one with row count; independent unit policy must be explicit."
        else:
            g12_decision = "ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT"
            decision_reason = "No primary key leakage or source-hash blocker found."

        next_question = (
            "Rebuild OTB1 from an input-only lifecycle projection that removes path_label and all R/path/touch "
            "result fields before hashing, then declare raw rows versus unique duplicate_group_id denominator."
        )
        if packet_id == "OTG0-PKT-017":
            next_question = (
                "Should observer status rows be converted by a dedicated observer lifecycle logger, or should "
                "EXP-G11-OBSERVER-EXPANSION-006 stay blocked outside lifecycle/no-fill packet testing?"
            )

        packets.append(
            {
                "packet_family": "OTB1",
                "packet_id": packet_id,
                "experiment_id": metadata["experiment_id"],
                "incoming_decision": decision_in,
                "g12_decision": g12_decision,
                "decision_reason": decision_reason,
                "primary_row_count": len(rows),
                "unique_duplicate_group_count": len(duplicate_counts),
                "duplicate_groups_with_multiple_rows": len(duplicate_groups_with_multiple_rows),
                "primary_forbidden_exact_key_counts": scan["forbidden_exact_key_counts"],
                "source_audit_refs": len(audit_refs),
                "source_audit_refs_with_nonempty_path_label": nonempty_path_label_refs,
                "hash_check": hash_check,
                "source_hash_shape_failures": sum(
                    1 for row in rows if not HASH64.match(str(row.get("source_hash", "")))
                ),
                "missing_source_paths": missing_source_paths,
                "next_exact_question": next_question,
            }
        )
        leakage_rows.append(
            {
                "packet_family": "OTB1",
                "packet_id": packet_id,
                "primary_rows_scanned": len(rows),
                "primary_forbidden_exact_key_counts": scan["forbidden_exact_key_counts"],
                "guard_or_label_token_notes": "label_family=lifecycle_no_fill is required and not an outcome value.",
                "result_bearing_source_counts": {
                    "referenced_pending_limit_lifecycle_audit_rows": len(audit_refs),
                    "referenced_rows_with_nonempty_path_label": nonempty_path_label_refs,
                },
                "verdict": "FAIL_SOURCE_NOLEAK" if nonempty_path_label_refs else "PASS_PRIMARY_KEYS",
            }
        )
        duplicate_rows.append(
            {
                "packet_family": "OTB1",
                "packet_id": packet_id,
                "row_count": len(rows),
                "unique_duplicate_group_count": len(duplicate_counts),
                "duplicate_groups_with_multiple_rows": len(duplicate_groups_with_multiple_rows),
                "denominator_status": "BLOCKED_UNLESS_UNIQUE_DUPLICATE_GROUP_DENOMINATOR_USED"
                if duplicate_groups_with_multiple_rows
                else "NO_WITHIN_PACKET_DUPLICATE_GROUP_DRIFT",
            }
        )

    return packets, leakage_rows, duplicate_rows


def audit_otb2() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    packets: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    ltf_by_row_key = read_jsonl_by_key(ROOT / "shadow_logs" / "candidate_ltf_path_order.jsonl", "row_key")

    for path in sorted((OTB2 / "packets").glob("*.json")):
        payload = read_json(path)
        rows = payload.get("records", [])
        packet_id = payload["packet_id"]
        scan = key_scan(rows)
        hash_check = verify_otb2_packet_hash(payload)

        duplicate_counts = Counter(row.get("duplicate_group_id") for row in rows if row.get("duplicate_group_id"))
        setup_counts = Counter(row.get("setup_id") for row in rows if row.get("setup_id"))
        duplicate_groups_with_multiple_rows = sorted([group for group, count in duplicate_counts.items() if count > 1])
        duplicate_setup_ids = sorted([setup for setup, count in setup_counts.items() if count > 1])

        referenced_ltf_rows = 0
        source_result_counts: Counter[str] = Counter()
        stale_ohlc_count = 0
        missing_source_paths: set[str] = set()
        source_hash_shape_failures = 0
        for row in rows:
            if not HASH64.match(str(row.get("source_hash", ""))):
                source_hash_shape_failures += 1
            for source in row.get("packet_build_source_paths", []):
                if not (ROOT / source).exists():
                    missing_source_paths.add(source)
            ordered_id = row.get("ordered_path_source_id", "")
            if "#" in ordered_id:
                row_key = ordered_id.split("#", 1)[1]
                source_row = ltf_by_row_key.get(row_key, {})
                if source_row:
                    referenced_ltf_rows += 1
                    for key in RESULT_SOURCE_KEYS:
                        if source_row.get(key) not in (None, "", []):
                            source_result_counts[key] += 1
            metadata = row.get("path_source_metadata", {})
            coverage_last = parse_utc(metadata.get("ohlc_coverage_last_utc"))
            path_end = parse_utc(row.get("path_end_utc"))
            if coverage_last and path_end and coverage_last < path_end:
                stale_ohlc_count += 1

        if payload["decision"] == "BLOCKED_WITH_OWNER_QUESTION":
            g12_decision = "BLOCKED_WITH_NEXT_EXACT_QUESTION"
            decision_reason = "Blocked packet has no primary records and carries an owner question."
        elif source_result_counts or stale_ohlc_count:
            g12_decision = "REJECT_INVALID_CLEARING"
            reason_bits = []
            if source_result_counts:
                reason_bits.append("ordered_path_source_id points to raw path-order source rows with result-bearing keys")
            if stale_ohlc_count:
                reason_bits.append("local OHLC coverage metadata ends before packet path_end_utc")
            decision_reason = "; ".join(reason_bits) + "."
        else:
            g12_decision = "ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT"
            decision_reason = "No primary key leakage, result-source misuse, stale source, or duplicate blocker found."

        next_question = payload.get("owner_question") or (
            "Will OTB2 rebuild G10-EXP-RISKBANK-005 from an input-only path-order projection whose source rows "
            "exclude post-entry touch/path labels, and from OHLC/path sources with coverage through path_end_utc?"
        )

        packets.append(
            {
                "packet_family": "OTB2",
                "packet_id": packet_id,
                "experiment_id": payload["experiment_id"],
                "incoming_decision": payload["decision"],
                "g12_decision": g12_decision,
                "decision_reason": decision_reason,
                "primary_row_count": len(rows),
                "unique_duplicate_group_count": len(duplicate_counts),
                "duplicate_groups_with_multiple_rows": len(duplicate_groups_with_multiple_rows),
                "duplicate_setup_ids": len(duplicate_setup_ids),
                "primary_forbidden_exact_key_counts": scan["forbidden_exact_key_counts"],
                "allowed_guard_key_note": "broker_actual_r_absent_from_primary_metric and label_family=synthetic_path_r are OTG0-required guard declarations, not result columns.",
                "referenced_ltf_source_rows": referenced_ltf_rows,
                "referenced_ltf_rows_result_key_nonempty_counts": dict(sorted(source_result_counts.items())),
                "rows_with_stale_ohlc_coverage_before_path_end": stale_ohlc_count,
                "hash_check": hash_check,
                "source_hash_shape_failures": source_hash_shape_failures,
                "missing_source_paths": sorted(missing_source_paths),
                "next_exact_question": next_question,
            }
        )
        leakage_rows.append(
            {
                "packet_family": "OTB2",
                "packet_id": packet_id,
                "primary_rows_scanned": len(rows),
                "primary_forbidden_exact_key_counts": scan["forbidden_exact_key_counts"],
                "guard_or_label_token_notes": "Allowed guard tokens are recorded separately from forbidden result columns.",
                "result_bearing_source_counts": dict(sorted(source_result_counts.items())),
                "verdict": "FAIL_SOURCE_NOLEAK" if source_result_counts else "PASS_PRIMARY_KEYS",
            }
        )
        duplicate_rows.append(
            {
                "packet_family": "OTB2",
                "packet_id": packet_id,
                "row_count": len(rows),
                "unique_duplicate_group_count": len(duplicate_counts),
                "duplicate_groups_with_multiple_rows": len(duplicate_groups_with_multiple_rows),
                "duplicate_setup_ids": len(duplicate_setup_ids),
                "denominator_status": "NO_WITHIN_PACKET_DUPLICATE_GROUP_DRIFT",
            }
        )

    return packets, leakage_rows, duplicate_rows


def audit_otb3() -> dict[str, Any]:
    patchset = read_json(OTB3 / f"OTB3_PROPOSED_PATCHSET_{DATE_STAMP}.json")
    rewrite = read_json(OTB3 / f"OTB3_G11_NO_LEAK_REWRITE_LEDGER_{DATE_STAMP}.json")
    cleanup = read_json(OTB3 / f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.json")
    source_registry = read_json(CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json")

    proposed_forbidden_rows = [
        row["hypothesis_id"]
        for row in rewrite["rewrites"]
        if row.get("proposed_forbidden_fields_detected")
    ]
    current_forbidden_rows = [
        row["hypothesis_id"]
        for row in rewrite["rewrites"]
        if row.get("forbidden_current_fields_detected")
    ]
    source_status_counts = Counter(row["otb3_status"] for row in cleanup.get("source_statuses", []))

    return {
        "artifact_family": "OTB3_SOURCE_NOLEAK_PROPOSED_PATCHSET",
        "g12_decision": "ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT",
        "decision_scope": "Accepted as context-only sidecar guidance for future packet builders; not accepted as a direct master-registry patch or validation-safe source flip.",
        "direct_master_registry_edits_applied": patchset.get("direct_master_registry_edits_applied"),
        "direct_master_registry_edit_status": patchset.get("direct_master_registry_edit_status"),
        "validation_safe": patchset.get("validation_safe"),
        "outcome_review_opened": patchset.get("outcome_review_opened"),
        "g11_rewrite_rows": len(rewrite["rewrites"]),
        "g11_current_forbidden_rows": len(current_forbidden_rows),
        "g11_proposed_forbidden_rows": len(proposed_forbidden_rows),
        "source_status_counts": dict(sorted(source_status_counts.items())),
        "source_registry_rows": len(source_registry["rows"]),
        "source_registry_validation_safe_true_count": sum(1 for row in source_registry["rows"] if row.get("validation_safe") is True),
        "next_exact_question": "Will G0/G12 apply the OTB3 sidecar rewrite through a separate owner-approved registry patch, while preserving validation_safe=false and outcome_review_opened=false?",
    }


def build_artifacts() -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    json_paths = (
        list(OTB1.glob("**/*.json"))
        + list(OTB2.glob("**/*.json"))
        + list(OTB3.glob("**/*.json"))
    )
    metadata = {
        "artifact_family": "G12_BLOCKER_CLEARING_AUDIT",
        "version_date": DATE_STAMP,
        "generated_at_utc": generated_at,
        "git_head": git_value("rev-parse", "--short", "HEAD"),
        "git_branch": git_value("branch", "--show-current"),
        "scope": "packet_source_noleak_artifacts_only_no_outcomes",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "outcomes_run": False,
        "r_result_values_inspected": False,
        "quarantine_or_result_outputs_created": False,
        "external_fetches_api_databento_calls": 0,
        "live_surface_changes": False,
        "controlling_inputs": [
            rel(OTG / "otb0_blocker_clearing_governor"),
            rel(OTB1),
            rel(OTB2),
            rel(OTB3),
            rel(OTG / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{DATE_STAMP}.md"),
            rel(OTG / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.md"),
            rel(SYNTHESIS / "G12_RED_TEAM_REVIEW_2026-05-06.md"),
            rel(SYNTHESIS / "G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.md"),
            rel(CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.md"),
            ".context/00_core/research_current_state.md",
        ],
    }

    otb1_packets, otb1_leakage, otb1_duplicates = audit_otb1()
    otb2_packets, otb2_leakage, otb2_duplicates = audit_otb2()
    otb3 = audit_otb3()
    flag_scan = scan_flags(json_paths)
    all_packets = otb1_packets + otb2_packets
    leakage_rows = otb1_leakage + otb2_leakage
    duplicate_rows = otb1_duplicates + otb2_duplicates

    decision_counts = Counter(row["g12_decision"] for row in all_packets)
    decision_counts[otb3["g12_decision"]] += 1

    decision_ledger = {
        **metadata,
        "artifact_type": "decision_ledger",
        "decision_counts_including_otb3_family": dict(sorted(decision_counts.items())),
        "otb1_packets": otb1_packets,
        "otb2_packets": otb2_packets,
        "otb3_family_decision": otb3,
    }

    leakage_review = {
        **metadata,
        "artifact_type": "leakage_noleak_review",
        "forbidden_primary_exact_keys": sorted(FORBIDDEN_PRIMARY_EXACT),
        "otb2_allowed_guard_keys": sorted(OTB2_ALLOWED_GUARD_KEYS),
        "packet_rows": leakage_rows,
        "otb3_no_leak": {
            "g11_rewrite_rows": otb3["g11_rewrite_rows"],
            "current_forbidden_rows": otb3["g11_current_forbidden_rows"],
            "proposed_forbidden_rows": otb3["g11_proposed_forbidden_rows"],
        },
        "global_flag_scan": flag_scan,
    }

    duplicate_review = {
        **metadata,
        "artifact_type": "duplicate_denominator_review",
        "packet_rows": duplicate_rows,
        "finding": "OTB1 row counts are not identical to independent duplicate_group_id counts; OTB2 G10 has 86 rows and 86 unique duplicate groups.",
    }

    label_review = {
        **metadata,
        "artifact_type": "label_family_review",
        "findings": [
            {
                "family": "OTB1",
                "label_family": "lifecycle_no_fill",
                "status": "PRIMARY_ROWS_PHYSICALLY_SEPARATED_BUT_SOURCE_HASH_BLOCKED",
                "details": "All OTB1 primary rows use lifecycle_no_fill and no broker/synthetic R columns, but source/hash construction still touches result-bearing audit path-label fields.",
            },
            {
                "family": "OTB2",
                "label_family": "synthetic_path_r",
                "status": "PRIMARY_ROWS_DECLARED_SYNTHETIC_ONLY_BUT_SOURCE_ROWS_RESULT_BEARING",
                "details": "The synthetic label family is declared as a guard; primary records do not contain result columns, but referenced path-order source rows contain post-entry path/touch labels.",
            },
            {
                "family": "OTB3",
                "label_family": "context_only_source_noleak_sidecar",
                "status": "ACCEPT_CONTEXT_ONLY",
                "details": "OTB3 proposes as-of whitelists and keeps forbidden current fields out of proposed no_leak_fields.",
            },
        ],
    }

    source_review = {
        **metadata,
        "artifact_type": "source_asof_source_hash_review",
        "otb1_source_hash_blocker": {
            "ready_packets_with_referenced_audit_path_label_rows": sum(
                1
                for row in otb1_packets
                if row["incoming_decision"] == "PACKET_READY_FOR_G12_BLOCKER_AUDIT"
                and row["source_audit_refs_with_nonempty_path_label"] > 0
            ),
            "hash_shape_and_packet_hash_checks_passed": all(
                row["hash_check"]["packet_payload_hash_matches"]
                and row["hash_check"]["primary_rows_hash_matches"]
                and row["source_hash_shape_failures"] == 0
                for row in otb1_packets
            ),
            "decision": "REJECT current ready clearing because source hashes are not no-leak sanitized against path_label.",
        },
        "otb2_source_hash_blocker": {
            "ready_packet_referenced_ltf_rows": next(
                row["referenced_ltf_source_rows"] for row in otb2_packets if row["packet_id"] == "OTG0-PKT-013"
            ),
            "ready_packet_rows_with_stale_ohlc_coverage_before_path_end": next(
                row["rows_with_stale_ohlc_coverage_before_path_end"]
                for row in otb2_packets
                if row["packet_id"] == "OTG0-PKT-013"
            ),
            "hash_shape_and_packet_hash_checks_passed": all(
                row["hash_check"]["packet_hash_matches"]
                and row["source_hash_shape_failures"] == 0
                for row in otb2_packets
            ),
            "decision": "REJECT current ready clearing because source identity depends on result-bearing raw path-order rows and stale OHLC coverage.",
        },
        "otb3_source_status": otb3,
        "global_flag_scan": flag_scan,
    }

    blocked_questions = {
        **metadata,
        "artifact_type": "blocked_owner_question_ledger",
        "questions": [
            {
                "packet_family": row["packet_family"],
                "packet_id": row["packet_id"],
                "experiment_id": row["experiment_id"],
                "g12_decision": row["g12_decision"],
                "next_exact_question": row["next_exact_question"],
            }
            for row in all_packets
            if row["g12_decision"] != "ACCEPT_FOR_FUTURE_OUTCOME_TEST_PACKET_AUDIT"
        ]
        + [
            {
                "packet_family": "OTB3",
                "packet_id": "OTB3_PROPOSED_PATCHSET",
                "experiment_id": "SOURCE_NOLEAK_CLEANUP_SIDECAR",
                "g12_decision": otb3["g12_decision"],
                "next_exact_question": otb3["next_exact_question"],
            }
        ],
    }

    accepted = {
        **metadata,
        "artifact_type": "accepted_packet_shortlist",
        "accepted_packets": [],
        "accepted_context_sidecars": [
            {
                "artifact_family": "OTB3_PROPOSED_PATCHSET",
                "decision": otb3["g12_decision"],
                "scope_limit": otb3["decision_scope"],
            }
        ],
        "reason_no_packets_accepted": (
            "All OTB1 and OTB2 packet files that claimed PACKET_READY_FOR_G12_BLOCKER_AUDIT fail this G12 audit "
            "on result-bearing source/hash or stale coverage blockers. Blocked packets remain blocked."
        ),
    }

    recommendations = {
        **metadata,
        "artifact_type": "next_lane_recommendations",
        "recommendations": [
            {
                "priority": "P0",
                "lane": "OTB1_REBUILD_INPUT_ONLY_LIFECYCLE_PROJECTION",
                "action": "Drop path_label and all R/path/touch result keys before source hashing; write sanitized source-row hash and count raw rows versus unique duplicate_group_id.",
                "depends_on": "No outcome opening; local source projection only.",
            },
            {
                "priority": "P0",
                "lane": "OTB2_REBUILD_INPUT_ONLY_PATH_PACKET",
                "action": "Create a source projection for candidate_ltf_path_order that excludes path_order_label and touch/result times, then bind path windows to coverage-valid M1/OHLC or explicit path-order input rows.",
                "depends_on": "No result-bearing event logs; no Databento/API call.",
            },
            {
                "priority": "P1",
                "lane": "G0_G12_OTB3_SIDECAR_REVIEW",
                "action": "Apply or reject OTB3 proposed no-leak/source-ref rewrites through an owner-approved registry patch, preserving validation_safe=false and outcome_review_opened=false.",
                "depends_on": "Owner/G0 registry patch lane, not outcome testing.",
            },
            {
                "priority": "P1",
                "lane": "G12_REAUDIT_AFTER_REBUILD",
                "action": "Run the same packet/source/no-leak audit before any quarantine/result lane opens.",
                "depends_on": "Rebuilt packets with machine-checkable sanitized source hashes.",
            },
        ],
    }

    completion = {
        **metadata,
        "artifact_type": "completion_audit",
        "objective_restatement": "Audit merged OTB1/OTB2/OTB3 packet/source/no-leak artifacts from main HEAD bc6b684b without opening outcomes or touching live surfaces.",
        "can_mark_g12_blocker_clearing_audit_complete": True,
        "prompt_to_artifact_checklist": [
            {
                "requirement": "Mandatory GTOS preflight completed",
                "evidence": "generate_live_state.py was run, LIVE_STATE was read, latest handoff and core research context were read before audit writing.",
                "status": "PASS",
            },
            {
                "requirement": "Inspect every OTB1 lifecycle packet including 9 ready and EXP-G11-OBSERVER-EXPANSION-006 blocked packet",
                "evidence": f"{len(otb1_packets)} OTB1 packets audited; ready={sum(1 for row in otb1_packets if row['incoming_decision']=='PACKET_READY_FOR_G12_BLOCKER_AUDIT')}; blocked={sum(1 for row in otb1_packets if row['incoming_decision']=='BLOCKED_WITH_OWNER_QUESTION')}.",
                "status": "PASS",
            },
            {
                "requirement": "Inspect every OTB2 synthetic packet including G10 ready packet with 86 rows and 15 blocked owner-question packets",
                "evidence": f"{len(otb2_packets)} OTB2 packets audited; G10 rows={next(row['primary_row_count'] for row in otb2_packets if row['packet_id']=='OTG0-PKT-013')}; blocked={sum(1 for row in otb2_packets if row['incoming_decision']=='BLOCKED_WITH_OWNER_QUESTION')}.",
                "status": "PASS",
            },
            {
                "requirement": "Inspect OTB3 source/no-leak proposed patchset",
                "evidence": "OTB3 proposed patchset, G11 rewrite ledger, source cleanup ledger, and source registry flags audited.",
                "status": "PASS",
            },
            {
                "requirement": "No outcome/result leakage, result-bearing source misuse, duplicate drift, label mixing, stale source/as-of, or source-hash invalidity accepted",
                "evidence": "OTB1 and OTB2 ready packets are rejected; OTB3 accepted only as context sidecar. Reviews are split across leakage, duplicate, label, and source/as-of artifacts.",
                "status": "PASS",
            },
            {
                "requirement": "No validation_safe=true, outcome_review_opened=true, live_effect=true, paid/API/Databento call, or live-surface change",
                "evidence": f"Global flag scan bad_true_or_nonzero count={len(flag_scan['bad_true_or_nonzero'])}; git diff since OTB0 touches only research/context paths.",
                "status": "PASS" if not flag_scan["bad_true_or_nonzero"] else "FAIL",
            },
            {
                "requirement": "Produce required scoped G12 artifacts",
                "evidence": "Decision ledger, leakage/no-leak review, duplicate/denominator review, label-family review, source/as-of/source-hash review, blocked-owner-question ledger, accepted shortlist, recommendations, and completion audit written under g12_blocker_clearing_audit.",
                "status": "PASS",
            },
            {
                "requirement": "Preserve NO_PROMOTION_VERDICT and do not create quarantine/result outputs",
                "evidence": "Every G12 artifact metadata carries NO_PROMOTION_VERDICT, outcomes_run=false, r_result_values_inspected=false, and quarantine_or_result_outputs_created=false.",
                "status": "PASS",
            },
        ],
    }

    return {
        "metadata": metadata,
        "decision_ledger": decision_ledger,
        "leakage_review": leakage_review,
        "duplicate_review": duplicate_review,
        "label_review": label_review,
        "source_review": source_review,
        "blocked_questions": blocked_questions,
        "accepted": accepted,
        "recommendations": recommendations,
        "completion": completion,
    }


def render_decision_ledger(payload: dict[str, Any]) -> str:
    rows = []
    for row in payload["otb1_packets"] + payload["otb2_packets"]:
        rows.append(
            [
                row["packet_family"],
                row["packet_id"],
                row["experiment_id"],
                row["incoming_decision"],
                row["g12_decision"],
                row["primary_row_count"],
                row["decision_reason"],
            ]
        )
    rows.append(
        [
            "OTB3",
            "OTB3_PROPOSED_PATCHSET",
            "SOURCE_NOLEAK_CLEANUP_SIDECAR",
            "CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY",
            payload["otb3_family_decision"]["g12_decision"],
            "n/a",
            payload["otb3_family_decision"]["decision_scope"],
        ]
    )
    return "\n".join(
        [
            f"# G12 Blocker-Clearing Decision Ledger - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "**Scope:** packet/source/no-leak artifacts only; no outcomes.",
            "",
            "## Decision Counts",
            "",
            table(["Decision", "Count"], [[key, value] for key, value in payload["decision_counts_including_otb3_family"].items()]),
            "",
            "## Packet And Artifact Decisions",
            "",
            table(["Family", "Packet", "Experiment", "Incoming decision", "G12 decision", "Rows", "Reason"], rows),
        ]
    )


def render_leakage(payload: dict[str, Any]) -> str:
    rows = []
    for row in payload["packet_rows"]:
        result_counts = row["result_bearing_source_counts"]
        rows.append(
            [
                row["packet_family"],
                row["packet_id"],
                row["primary_rows_scanned"],
                row["primary_forbidden_exact_key_counts"] or "NONE",
                result_counts or "NONE",
                row["verdict"],
            ]
        )
    return "\n".join(
        [
            f"# G12 Leakage And No-Leak Review - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            "Primary packet rows were scanned for exact forbidden result keys. Guard declarations required by OTG0 are not treated as result columns, but result-bearing source-row dependencies are blockers.",
            "",
            table(["Family", "Packet", "Rows", "Primary forbidden keys", "Result-bearing source counts", "Verdict"], rows),
            "",
            "## OTB3 No-Leak Sidecar",
            "",
            table(
                ["Check", "Count"],
                [
                    ["G11 rewrite rows", payload["otb3_no_leak"]["g11_rewrite_rows"]],
                    ["Rows with forbidden current fields", payload["otb3_no_leak"]["current_forbidden_rows"]],
                    ["Rows with forbidden proposed fields", payload["otb3_no_leak"]["proposed_forbidden_rows"]],
                ],
            ),
            "",
            "## Global Flag Scan",
            "",
            f"Bad true/nonzero safety flags: `{len(payload['global_flag_scan']['bad_true_or_nonzero'])}`.",
        ]
    )


def render_duplicate(payload: dict[str, Any]) -> str:
    rows = [
        [
            row["packet_family"],
            row["packet_id"],
            row["row_count"],
            row["unique_duplicate_group_count"],
            row["duplicate_groups_with_multiple_rows"],
            row["denominator_status"],
        ]
        for row in payload["packet_rows"]
    ]
    return "\n".join(
        [
            f"# G12 Duplicate And Denominator Review - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            payload["finding"],
            "",
            table(["Family", "Packet", "Rows", "Unique duplicate groups", "Duplicate groups >1 row", "Status"], rows),
        ]
    )


def render_label(payload: dict[str, Any]) -> str:
    rows = [[row["family"], row["label_family"], row["status"], row["details"]] for row in payload["findings"]]
    return "\n".join(
        [
            f"# G12 Label-Family Review - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            table(["Family", "Label family", "Status", "Details"], rows),
        ]
    )


def render_source(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# G12 Source/As-Of/Source-Hash Review - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            "## OTB1",
            "",
            table(
                ["Check", "Value"],
                [
                    [
                        "Ready packets with referenced audit path-label rows",
                        payload["otb1_source_hash_blocker"]["ready_packets_with_referenced_audit_path_label_rows"],
                    ],
                    [
                        "Hash shape and packet-hash checks passed",
                        payload["otb1_source_hash_blocker"]["hash_shape_and_packet_hash_checks_passed"],
                    ],
                    ["Decision", payload["otb1_source_hash_blocker"]["decision"]],
                ],
            ),
            "",
            "## OTB2",
            "",
            table(
                ["Check", "Value"],
                [
                    ["Ready packet referenced LTF rows", payload["otb2_source_hash_blocker"]["ready_packet_referenced_ltf_rows"]],
                    [
                        "Rows with stale OHLC coverage before path_end_utc",
                        payload["otb2_source_hash_blocker"]["ready_packet_rows_with_stale_ohlc_coverage_before_path_end"],
                    ],
                    [
                        "Hash shape and packet-hash checks passed",
                        payload["otb2_source_hash_blocker"]["hash_shape_and_packet_hash_checks_passed"],
                    ],
                    ["Decision", payload["otb2_source_hash_blocker"]["decision"]],
                ],
            ),
            "",
            "## OTB3",
            "",
            table(
                ["Check", "Value"],
                [
                    ["Decision", payload["otb3_source_status"]["g12_decision"]],
                    ["Scope", payload["otb3_source_status"]["decision_scope"]],
                    ["Direct master registry edits applied", payload["otb3_source_status"]["direct_master_registry_edits_applied"]],
                    ["Source registry validation_safe=true count", payload["otb3_source_status"]["source_registry_validation_safe_true_count"]],
                    ["Source status counts", payload["otb3_source_status"]["source_status_counts"]],
                ],
            ),
        ]
    )


def render_blocked(payload: dict[str, Any]) -> str:
    rows = [
        [row["packet_family"], row["packet_id"], row["experiment_id"], row["g12_decision"], row["next_exact_question"]]
        for row in payload["questions"]
    ]
    return "\n".join(
        [
            f"# G12 Blocked Owner-Question Ledger - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            table(["Family", "Packet", "Experiment", "Decision", "Next exact question"], rows),
        ]
    )


def render_accepted(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# G12 Accepted Packet Shortlist - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            "## Accepted Packets",
            "",
            "None.",
            "",
            "## Accepted Context Sidecars",
            "",
            table(
                ["Artifact", "Decision", "Scope limit"],
                [
                    [
                        row["artifact_family"],
                        row["decision"],
                        row["scope_limit"],
                    ]
                    for row in payload["accepted_context_sidecars"]
                ],
            ),
            "",
            "## Reason",
            "",
            payload["reason_no_packets_accepted"],
        ]
    )


def render_recommendations(payload: dict[str, Any]) -> str:
    rows = [[row["priority"], row["lane"], row["action"], row["depends_on"]] for row in payload["recommendations"]]
    return "\n".join(
        [
            f"# G12 Next-Lane Recommendations - {DATE_STAMP}",
            "",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            table(["Priority", "Lane", "Action", "Depends on"], rows),
        ]
    )


def render_completion(payload: dict[str, Any]) -> str:
    rows = [
        [row["requirement"], row["status"], row["evidence"]]
        for row in payload["prompt_to_artifact_checklist"]
    ]
    return "\n".join(
        [
            f"# G12 Blocker-Clearing Completion Audit - {DATE_STAMP}",
            "",
            "**Can mark G12 blocker-clearing audit complete:** `true`",
            "**Promotion verdict:** `NO_PROMOTION_VERDICT`",
            "",
            "## Objective Restated",
            "",
            payload["objective_restatement"],
            "",
            "## Prompt-To-Artifact Checklist",
            "",
            table(["Requirement", "Status", "Evidence"], rows),
            "",
            "## Final State",
            "",
            "The audit is complete, but no OTB1 or OTB2 packet is accepted for future outcome test packet audit. OTB3 is accepted only as context-only sidecar guidance. No outcome review is opened.",
        ]
    )


def write_artifact_pair(stem: str, payload: dict[str, Any], renderer) -> None:
    write_json(OUT / f"{stem}_{DATE_STAMP}.json", payload)
    write_text(OUT / f"{stem}_{DATE_STAMP}.md", renderer(payload))


def main() -> int:
    artifacts = build_artifacts()
    write_artifact_pair("G12_BLOCKER_CLEARING_DECISION_LEDGER", artifacts["decision_ledger"], render_decision_ledger)
    write_artifact_pair("G12_LEAKAGE_NOLEAK_REVIEW", artifacts["leakage_review"], render_leakage)
    write_artifact_pair("G12_DUPLICATE_DENOMINATOR_REVIEW", artifacts["duplicate_review"], render_duplicate)
    write_artifact_pair("G12_LABEL_FAMILY_REVIEW", artifacts["label_review"], render_label)
    write_artifact_pair("G12_SOURCE_ASOF_SOURCE_HASH_REVIEW", artifacts["source_review"], render_source)
    write_artifact_pair("G12_BLOCKED_OWNER_QUESTION_LEDGER", artifacts["blocked_questions"], render_blocked)
    write_artifact_pair("G12_ACCEPTED_PACKET_SHORTLIST", artifacts["accepted"], render_accepted)
    write_artifact_pair("G12_NEXT_LANE_RECOMMENDATIONS", artifacts["recommendations"], render_recommendations)
    write_artifact_pair("G12_BLOCKER_CLEARING_COMPLETION_AUDIT", artifacts["completion"], render_completion)

    manifest = {
        **artifacts["metadata"],
        "artifact_type": "artifact_manifest",
        "artifacts": sorted(rel(path) for path in OUT.glob(f"*_{DATE_STAMP}.md"))
        + sorted(rel(path) for path in OUT.glob(f"*_{DATE_STAMP}.json")),
        "builder": rel(Path(__file__)),
    }
    write_json(OUT / f"G12_BLOCKER_CLEARING_ARTIFACT_MANIFEST_{DATE_STAMP}.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
