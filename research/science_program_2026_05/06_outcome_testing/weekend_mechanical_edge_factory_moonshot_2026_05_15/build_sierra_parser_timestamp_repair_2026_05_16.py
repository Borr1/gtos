#!/usr/bin/env python3
"""Repair the Route C Sierra source-contract blocker with parser audits.

The initial Sierra source-contract ledger was metadata-only. This builder
reuses the branch's existing SCID and depth parsers to audit every Sierra file,
record immutable byte-range segment hashes, and bind timestamp/as-of policy
reuse without claiming validation, outcomes, R/PnL, live-readiness, or
promotion.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.extract_sierra_depth_features import (  # noqa: E402
    COMMANDS as DEPTH_COMMANDS,
    _unpack_record_at,
    read_header as read_depth_header,
    sierra_datetime as depth_datetime,
)
from scripts.inspect_sierra_scid import (  # noqa: E402
    parse_header as parse_scid_header,
    read_record as read_scid_record,
)


SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

SOURCE_LEDGER = ROUTE_DIR / f"SIERRA_SOURCE_CONTRACT_LEDGER_{SOURCE_STAMP}.jsonl"
SCID_TIMESTAMP_POLICY = (
    REPO
    / "research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/SCID_ASOF_TIMESTAMP_AND_INTERVAL_POLICY_2026-05-11.json"
)
G12_AUDIT = (
    REPO
    / "research/science_program_2026_05/06_outcome_testing/g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit/G12_SCID_ASOF_CONTRACT_AUDIT_PARSER_TIMESTAMP_REVIEW_2026-05-11.json"
)

RESULT_PATH = ROUTE_DIR / f"SIERRA_PARSER_TIMESTAMP_REPAIR_RESULT_{STAMP}.json"
PARSER_AUDIT_LEDGER = ROUTE_DIR / f"SIERRA_PARSER_AUDIT_LEDGER_{STAMP}.jsonl"
BYTE_RANGE_FREEZE_LEDGER = ROUTE_DIR / f"SIERRA_BYTE_RANGE_FREEZE_LEDGER_{STAMP}.jsonl"
TIMESTAMP_CONTRACT_REUSE_LEDGER = ROUTE_DIR / f"SIERRA_TIMESTAMP_CONTRACT_REUSE_LEDGER_{STAMP}.jsonl"
PARSER_REPAIR_BLOCKER_LEDGER = ROUTE_DIR / f"SIERRA_PARSER_REPAIR_BLOCKER_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_PARSER_TIMESTAMP_REPAIR_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra parser/timestamp/source-byte repair only; no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

SEGMENT_1MB = 1024 * 1024
SEGMENT_4KB = 4096


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def file_mtime_utc(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def hash_range(path: Path, offset: int, length: int) -> str | None:
    if length <= 0:
        return None
    digest = hashlib.sha256()
    remaining = length
    with path.open("rb") as handle:
        handle.seek(offset)
        while remaining > 0:
            chunk = handle.read(min(SEGMENT_1MB, remaining))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def build_segment_freeze(row: dict[str, Any]) -> dict[str, Any]:
    path = Path(row["path"])
    ledger_bytes = int(row.get("bytes") or 0)
    current_exists = path.exists()
    current_bytes = path.stat().st_size if current_exists else None
    frozen_bytes = min(ledger_bytes, current_bytes or 0) if current_exists else 0
    segments: list[dict[str, Any]] = []
    if current_exists and current_bytes is not None:
        specs = [
            ("header_4kb", 0, min(SEGMENT_4KB, frozen_bytes)),
            ("prefix_1mb", 0, min(SEGMENT_1MB, frozen_bytes)),
            ("ledger_tail_1mb", max(0, frozen_bytes - SEGMENT_1MB), frozen_bytes - max(0, frozen_bytes - SEGMENT_1MB)),
            ("current_tail_4kb", max(0, current_bytes - SEGMENT_4KB), current_bytes - max(0, current_bytes - SEGMENT_4KB)),
        ]
        for label, offset, length in specs:
            segments.append(
                {
                    "segment_label": label,
                    "offset": offset,
                    "length": length,
                    "sha256": hash_range(path, offset, length),
                }
            )
    combined = hashlib.sha256()
    for segment in segments:
        combined.update(
            f"{segment['segment_label']}|{segment['offset']}|{segment['length']}|{segment['sha256']}\n".encode(
                "utf-8"
            )
        )
    return {
        "route_id": ROUTE_ID,
        "path": str(path),
        "extension": row.get("extension"),
        "symbol_hint": row.get("symbol_hint"),
        "ledger_bytes": ledger_bytes,
        "current_exists": current_exists,
        "current_bytes": current_bytes,
        "frozen_prefix_bytes": frozen_bytes,
        "ledger_modified_utc": row.get("modified_utc"),
        "current_modified_utc": file_mtime_utc(path),
        "byte_delta_current_minus_ledger": None if current_bytes is None else current_bytes - ledger_bytes,
        "mutable_status": mutable_status(ledger_bytes, current_bytes),
        "segment_count": len(segments),
        "segment_hash_family": "header/prefix/ledger-tail/current-tail segment hashes; not a full-file hash",
        "combined_segment_sha256": combined.hexdigest() if segments else None,
        "segments": segments,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
    }


def mutable_status(ledger_bytes: int, current_bytes: int | None) -> str:
    if current_bytes is None:
        return "MISSING_ON_CURRENT_FILESYSTEM"
    if current_bytes == ledger_bytes:
        return "UNCHANGED_SIZE_FROM_SOURCE_LEDGER"
    if current_bytes > ledger_bytes:
        return "CURRENT_FILE_LONGER_MUTABLE_APPEND_OR_REWRITE"
    return "CURRENT_FILE_SHORTER_TRUNCATED_OR_REPLACED"


def sample_positions(record_count: int) -> list[int]:
    if record_count <= 0:
        return []
    candidates = {
        0,
        1,
        2,
        record_count // 4,
        record_count // 2,
        (record_count * 3) // 4,
        record_count - 3,
        record_count - 2,
        record_count - 1,
    }
    return [idx for idx in sorted(candidates) if 0 <= idx < record_count]


def read_depth_record_dict(path: Path, header: Any, index: int) -> dict[str, Any]:
    with path.open("rb") as handle:
        dt_us, command, flags, num_orders, price, quantity = _unpack_record_at(handle, header, index)
    return {
        "index": index,
        "timestamp_utc": iso_utc(depth_datetime(dt_us)),
        "timestamp_us": dt_us,
        "command": command,
        "command_name": DEPTH_COMMANDS.get(command, f"UNKNOWN_{command}"),
        "flags": flags,
        "num_orders": num_orders,
        "price": price,
        "quantity": quantity,
    }


def audit_scid(row: dict[str, Any], freeze: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = Path(row["path"])
    blockers: list[dict[str, Any]] = []
    base = base_audit_row(row, freeze)
    try:
        header = parse_scid_header(path)
        ledger_bytes = int(row.get("bytes") or 0)
        frozen_bytes = int(freeze["frozen_prefix_bytes"] or 0)
        ledger_body = max(0, frozen_bytes - header.header_size)
        ledger_record_count = ledger_body // header.record_size
        ledger_remainder = ledger_body % header.record_size
        first_record = None
        ledger_last_record = None
        current_last_record = None
        with path.open("rb") as handle:
            if header.record_count > 0:
                first_record = read_scid_record(handle, header, 0)
                current_last_record = read_scid_record(handle, header, header.record_count - 1)
            if ledger_record_count > 0:
                ledger_last_record = read_scid_record(handle, header, ledger_record_count - 1)
        status = "SCID_PARSER_OK"
        if freeze["mutable_status"] != "UNCHANGED_SIZE_FROM_SOURCE_LEDGER":
            status = "SCID_PARSER_OK_BYTE_RANGE_FREEZE_REPAIRED_MUTABLE_SIZE"
            blockers.append(blocker(row, "MUTABLE_SCID_SIZE_REPAIRED_WITH_LEDGER_PREFIX_SEGMENT_FREEZE", freeze))
        base.update(
            {
                "parser_status": status,
                "parser_family": "scripts.inspect_sierra_scid",
                "magic": header.magic,
                "header_size": header.header_size,
                "record_size": header.record_size,
                "version": header.version,
                "utc_start_index": header.utc_start_index,
                "current_record_count": header.record_count,
                "current_remainder_bytes": header.remainder_bytes,
                "ledger_record_count": ledger_record_count,
                "ledger_remainder_bytes": ledger_remainder,
                "first_timestamp_utc": iso_utc(first_record.timestamp if first_record else None),
                "ledger_last_timestamp_utc": iso_utc(ledger_last_record.timestamp if ledger_last_record else None),
                "current_last_timestamp_utc": iso_utc(current_last_record.timestamp if current_last_record else None),
                "first_close": first_record.close if first_record else None,
                "ledger_last_close": ledger_last_record.close if ledger_last_record else None,
                "current_last_close": current_last_record.close if current_last_record else None,
                "timestamp_contract_status": "SCID_ASOF_TIMESTAMP_POLICY_REUSED",
                "parser_repair_status": "REPAIRED_METADATA_ONLY_BINARY_PARSER_PENDING",
            }
        )
    except Exception as exc:  # noqa: BLE001 - audit must preserve file-level failures.
        base.update(
            {
                "parser_status": "SCID_PARSER_ERROR",
                "parser_family": "scripts.inspect_sierra_scid",
                "error": f"{type(exc).__name__}: {exc}",
                "parser_repair_status": "FAILED_CLOSED",
            }
        )
        blockers.append(blocker(row, "SCID_PARSE_ERROR_FAIL_CLOSED", freeze, error=str(exc)))
    return base, blockers


def audit_depth(row: dict[str, Any], freeze: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = Path(row["path"])
    blockers: list[dict[str, Any]] = []
    base = base_audit_row(row, freeze)
    try:
        header = read_depth_header(path)
        frozen_bytes = int(freeze["frozen_prefix_bytes"] or 0)
        ledger_body = max(0, frozen_bytes - header.header_size)
        ledger_record_count = ledger_body // header.record_size
        ledger_remainder = ledger_body % header.record_size
        sample_count_basis = min(ledger_record_count, header.record_count)
        samples = [read_depth_record_dict(path, header, idx) for idx in sample_positions(sample_count_basis)]
        command_counts = Counter(sample["command_name"] for sample in samples)
        first_record = read_depth_record_dict(path, header, 0) if header.record_count else None
        ledger_last_record = (
            read_depth_record_dict(path, header, ledger_record_count - 1) if ledger_record_count > 0 else None
        )
        current_last_record = (
            read_depth_record_dict(path, header, header.record_count - 1) if header.record_count > 0 else None
        )
        status = "DEPTH_PARSER_OK_SEGMENT_SAMPLE_AUDITED"
        if freeze["mutable_status"] != "UNCHANGED_SIZE_FROM_SOURCE_LEDGER":
            status = "DEPTH_PARSER_OK_BYTE_RANGE_FREEZE_REPAIRED_MUTABLE_SIZE"
            blockers.append(blocker(row, "MUTABLE_DEPTH_SIZE_REPAIRED_WITH_LEDGER_PREFIX_SEGMENT_FREEZE", freeze))
        blockers.append(
            blocker(
                row,
                "DEPTH_NOT_FULL_SCANNED_REQUIRES_WINDOW_REPLAY_FOR_FEATURE_USE",
                freeze,
                error="Header, first/last, and deterministic segment samples audited for all files; full depth command replay remains event-window scoped.",
            )
        )
        base.update(
            {
                "parser_status": status,
                "parser_family": "scripts.extract_sierra_depth_features",
                "magic": f"{header.magic:#x}",
                "header_size": header.header_size,
                "record_size": header.record_size,
                "version": header.version,
                "current_record_count": header.record_count,
                "current_remainder_bytes": header.remainder,
                "ledger_record_count": ledger_record_count,
                "ledger_remainder_bytes": ledger_remainder,
                "first_timestamp_utc": first_record.get("timestamp_utc") if first_record else None,
                "ledger_last_timestamp_utc": ledger_last_record.get("timestamp_utc") if ledger_last_record else None,
                "current_last_timestamp_utc": current_last_record.get("timestamp_utc") if current_last_record else None,
                "sample_record_count": len(samples),
                "sample_positions": [sample["index"] for sample in samples],
                "sample_command_counts": dict(sorted(command_counts.items())),
                "sample_has_clear_book": bool(command_counts.get("CLEAR_BOOK")),
                "sample_has_ladder_activity": any(
                    key in command_counts
                    for key in ("ADD_BID", "ADD_ASK", "MODIFY_BID", "MODIFY_ASK", "DELETE_BID", "DELETE_ASK")
                ),
                "sample_timestamp_non_decreasing": timestamps_non_decreasing(samples),
                "timestamp_contract_status": "DEPTH_SOURCE_US_EPOCH_PARSER_REUSED_EVENT_WINDOWS_STILL_REQUIRED",
                "parser_repair_status": "REPAIRED_METADATA_ONLY_BINARY_PARSER_PENDING_FOR_HEADER_AND_SEGMENTS",
            }
        )
    except Exception as exc:  # noqa: BLE001 - audit must preserve file-level failures.
        base.update(
            {
                "parser_status": "DEPTH_PARSER_ERROR",
                "parser_family": "scripts.extract_sierra_depth_features",
                "error": f"{type(exc).__name__}: {exc}",
                "parser_repair_status": "FAILED_CLOSED",
            }
        )
        blockers.append(blocker(row, "DEPTH_PARSE_ERROR_FAIL_CLOSED", freeze, error=str(exc)))
    return base, blockers


def timestamps_non_decreasing(samples: list[dict[str, Any]]) -> bool | None:
    if len(samples) < 2:
        return None
    values = [int(sample["timestamp_us"]) for sample in samples]
    return all(left <= right for left, right in zip(values, values[1:]))


def audit_unparsed(row: dict[str, Any], freeze: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    base = base_audit_row(row, freeze)
    base.update(
        {
            "parser_status": "DLY_PARSER_NOT_IMPLEMENTED_METADATA_AND_SEGMENT_HASH_ONLY",
            "parser_family": None,
            "timestamp_contract_status": "NO_DLY_TIMESTAMP_CONTRACT_REUSED",
            "parser_repair_status": "NOT_REPAIRED_DLY_FORMAT_REQUIRES_SEPARATE_PARSER_OR_PROXY",
        }
    )
    return base, [blocker(row, "DLY_PARSER_NOT_IMPLEMENTED", freeze)]


def base_audit_row(row: dict[str, Any], freeze: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "path": row.get("path"),
        "root_label": row.get("root_label"),
        "symbol_hint": row.get("symbol_hint"),
        "extension": row.get("extension"),
        "ledger_parser_status": row.get("parser_status"),
        "ledger_bytes": row.get("bytes"),
        "current_exists": freeze.get("current_exists"),
        "current_bytes": freeze.get("current_bytes"),
        "byte_delta_current_minus_ledger": freeze.get("byte_delta_current_minus_ledger"),
        "mutable_status": freeze.get("mutable_status"),
        "combined_segment_sha256": freeze.get("combined_segment_sha256"),
        "segment_hash_family": freeze.get("segment_hash_family"),
        "ledger_modified_utc": row.get("modified_utc"),
        "current_modified_utc": freeze.get("current_modified_utc"),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
    }


def blocker(row: dict[str, Any], blocker_type: str, freeze: dict[str, Any], *, error: str | None = None) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "path": row.get("path"),
        "extension": row.get("extension"),
        "symbol_hint": row.get("symbol_hint"),
        "blocker_type": blocker_type,
        "mutable_status": freeze.get("mutable_status"),
        "byte_delta_current_minus_ledger": freeze.get("byte_delta_current_minus_ledger"),
        "repair_or_next_action": repair_action(blocker_type),
        "error": error,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
    }


def repair_action(blocker_type: str) -> str:
    mapping = {
        "MUTABLE_SCID_SIZE_REPAIRED_WITH_LEDGER_PREFIX_SEGMENT_FREEZE": (
            "Use ledger prefix bytes plus recorded segment hashes for same-resource reproducibility; do not treat current tail as sealed."
        ),
        "MUTABLE_DEPTH_SIZE_REPAIRED_WITH_LEDGER_PREFIX_SEGMENT_FREEZE": (
            "Use ledger prefix bytes plus recorded segment hashes for same-resource reproducibility; event-window replay must bind to byte-range state."
        ),
        "DEPTH_NOT_FULL_SCANNED_REQUIRES_WINDOW_REPLAY_FOR_FEATURE_USE": (
            "For any feature claim, run event-window depth replay from prior CLEAR_BOOK using the audited parser."
        ),
        "DLY_PARSER_NOT_IMPLEMENTED": "Build a separate .dly parser or use .scid/.csv/MT5 proxy before using daily Sierra rows.",
        "SCID_PARSE_ERROR_FAIL_CLOSED": "Exclude or repair file parser before feature use.",
        "DEPTH_PARSE_ERROR_FAIL_CLOSED": "Exclude or repair file parser before feature use.",
        "SOURCE_FILE_MISSING_FAIL_CLOSED": "Reacquire or remove source from candidate denominator.",
    }
    return mapping.get(blocker_type, "Repair before feature or strategy use.")


def build_contract_rows(generated_utc: str) -> list[dict[str, Any]]:
    scid_policy = json.loads(SCID_TIMESTAMP_POLICY.read_text(encoding="utf-8"))
    g12_audit = json.loads(G12_AUDIT.read_text(encoding="utf-8"))
    return [
        {
            "route_id": ROUTE_ID,
            "generated_utc": generated_utc,
            "contract_family": "scid_timestamp_interval_policy",
            "source_path": relative(SCID_TIMESTAMP_POLICY),
            "contract_status": "REUSED",
            "policy_summary": scid_policy.get("summary"),
            "source_timestamp_unit": scid_policy.get("source_timestamp_unit"),
            "sierra_epoch_utc": scid_policy.get("sierra_epoch_utc"),
            "interval_policy": scid_policy.get("interval_policy"),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_id": ROUTE_ID,
            "generated_utc": generated_utc,
            "contract_family": "g12_parser_timestamp_audit",
            "source_path": relative(G12_AUDIT),
            "contract_status": "REUSED_PASS_SOURCE_CONTROL_PARSER_TIMESTAMP_CONTRACT",
            "decision": g12_audit.get("decision"),
            "summary": g12_audit.get("summary"),
            "warning_notes": g12_audit.get("warning_notes"),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_id": ROUTE_ID,
            "generated_utc": generated_utc,
            "contract_family": "sierra_depth_parser",
            "source_path": "scripts/extract_sierra_depth_features.py",
            "contract_status": "REUSED_FOR_HEADER_SEGMENT_AND_EVENT_WINDOW_REPLAY",
            "source_timestamp_unit": "microseconds since Sierra epoch",
            "remaining_requirement": "Full depth command replay remains event-window scoped; this packet does not full-scan every depth file.",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_id": ROUTE_ID,
            "generated_utc": generated_utc,
            "contract_family": "sierra_dly_parser",
            "source_path": None,
            "contract_status": "NOT_REUSED_OR_REPAIRED",
            "remaining_requirement": "Daily Sierra .dly format remains metadata/segment-hash only until a dedicated parser or proxy route is built.",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
    ]


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_parser_timestamp_repair_builder", "created"),
        (RESULT_PATH, "sierra_parser_timestamp_repair_result", "created"),
        (PARSER_AUDIT_LEDGER, "sierra_parser_audit_ledger", "created"),
        (BYTE_RANGE_FREEZE_LEDGER, "sierra_byte_range_freeze_ledger", "created"),
        (TIMESTAMP_CONTRACT_REUSE_LEDGER, "sierra_timestamp_contract_reuse_ledger", "created"),
        (PARSER_REPAIR_BLOCKER_LEDGER, "sierra_parser_repair_blocker_ledger", "created"),
        (SUMMARY_PATH, "sierra_parser_timestamp_repair_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], status_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_parser_timestamp_repair",
        "status": "done",
        "route": "sierra_source_contract_repair",
        "details": (
            "Repaired the metadata-only Sierra source-contract blocker by parsing every SCID/depth header, "
            "freezing ledger-prefix byte ranges for mutable files, reusing accepted timestamp/as-of contracts, "
            "and preserving DLY/full-depth-scan gaps as explicit blockers."
        ),
        "counts": counts,
        "parser_status_counts": status_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(PARSER_AUDIT_LEDGER),
            relative(BYTE_RANGE_FREEZE_LEDGER),
            relative(TIMESTAMP_CONTRACT_REUSE_LEDGER),
            relative(PARSER_REPAIR_BLOCKER_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(
    generated_utc: str,
    counts: dict[str, int],
    parser_status_counts: dict[str, int],
    mutable_status_counts: dict[str, int],
) -> None:
    lines = [
        "# Sierra Parser Timestamp Repair",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: Sierra parser/timestamp/source-byte repair only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Parser Status Counts", ""])
    for key, value in sorted(parser_status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Mutable Size Status Counts", ""])
    for key, value in sorted(mutable_status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Remaining Same-Resource Work",
            "",
            "- Run event-window depth replay for any specific feature claim instead of relying on sampled command counts.",
            "- Build or route around the `.dly` parser gap before using Sierra daily files.",
            "- Bind future Sierra-derived feature packets to the ledger-prefix byte range and segment hash family when files are mutable.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_rows = read_jsonl(SOURCE_LEDGER)
    freeze_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []

    for row in source_rows:
        freeze = build_segment_freeze(row)
        freeze_rows.append(freeze)
        if not freeze["current_exists"]:
            audit = base_audit_row(row, freeze)
            audit.update(
                {
                    "parser_status": "SOURCE_FILE_MISSING_FAIL_CLOSED",
                    "parser_repair_status": "FAILED_CLOSED",
                }
            )
            audit_rows.append(audit)
            blocker_rows.append(blocker(row, "SOURCE_FILE_MISSING_FAIL_CLOSED", freeze))
            continue
        extension = str(row.get("extension") or "").lower()
        if extension == ".scid":
            audit, blockers = audit_scid(row, freeze)
        elif extension == ".depth":
            audit, blockers = audit_depth(row, freeze)
        else:
            audit, blockers = audit_unparsed(row, freeze)
        audit_rows.append(audit)
        blocker_rows.extend(blockers)

    contract_rows = build_contract_rows(generated_utc)
    write_jsonl(PARSER_AUDIT_LEDGER, audit_rows)
    write_jsonl(BYTE_RANGE_FREEZE_LEDGER, freeze_rows)
    write_jsonl(TIMESTAMP_CONTRACT_REUSE_LEDGER, contract_rows)
    write_jsonl(PARSER_REPAIR_BLOCKER_LEDGER, blocker_rows)

    extension_counts = Counter(str(row.get("extension") or "missing") for row in source_rows)
    parser_status_counts = Counter(str(row.get("parser_status") or "missing") for row in audit_rows)
    mutable_status_counts = Counter(str(row.get("mutable_status") or "missing") for row in audit_rows)
    counts = {
        "input_sierra_rows": len(source_rows),
        "audit_rows": len(audit_rows),
        "byte_range_freeze_rows": len(freeze_rows),
        "timestamp_contract_reuse_rows": len(contract_rows),
        "blocker_rows": len(blocker_rows),
        "scid_rows": extension_counts.get(".scid", 0),
        "depth_rows": extension_counts.get(".depth", 0),
        "dly_rows": extension_counts.get(".dly", 0),
        "parser_error_rows": sum(1 for row in audit_rows if str(row.get("parser_status", "")).endswith("_ERROR")),
        "missing_file_rows": parser_status_counts.get("SOURCE_FILE_MISSING_FAIL_CLOSED", 0),
        "mutable_size_rows": sum(
            count
            for status, count in mutable_status_counts.items()
            if status != "UNCHANGED_SIZE_FROM_SOURCE_LEDGER"
        ),
    }
    result = {
        "schema": "sierra_parser_timestamp_repair_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_PARSER_TIMESTAMP_SOURCE_CONTRACT_REPAIR_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "extension_counts": dict(sorted(extension_counts.items())),
        "parser_status_counts": dict(sorted(parser_status_counts.items())),
        "mutable_status_counts": dict(sorted(mutable_status_counts.items())),
        "next_same_resource_work": [
            "use audited SCID parser and timestamp contract to build source-bound SCID primitive rows",
            "run event-window depth replay for specific feature candidates rather than claiming full-depth-file interpretation",
            "repair or proxy the .dly daily file format before using those rows",
            "bind every mutable Sierra-derived packet to ledger-prefix byte ranges and segment hashes",
        ],
        "not_completion": "This repairs a source/parser blocker and opens deeper Sierra extraction; it does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(generated_utc, counts, dict(parser_status_counts), dict(mutable_status_counts))
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(parser_status_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
