#!/usr/bin/env python3
"""Build a Route C Sierra exact .depth source-date acquisition manifest.

This packet is intentionally narrow: it consolidates existing Route C Sierra
source-date/depth requirements, scans approved local roots for exact and
near/delayed ``.depth`` files, hashes exact matches, and records acquisition
states. It does not update shared moonshot ledgers/manifests/verifiers.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime, date
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
STAMP = "2026-05-16"
PREFIX = f"SIERRA_DEPTH_EXACT_SOURCE_DATE_ACQUISITION_MANIFEST_{STAMP}"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C Sierra exact .depth source-date acquisition/file-discovery packet only; "
    "no strategy validation, trade outcome, R/PnL, expectancy, live-readiness, "
    "promotion, vendor call, or paid data call"
)

SEARCH_ROOTS = [
    Path(r"C:\SierraChart"),
    Path(r"C:\tmp"),
    REPO_ROOT,
    Path(r"C:\Users\MSI\Documents"),
]

SOURCE_ARTIFACTS = [
    {
        "path": ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_SOURCE_GAP_LEDGER_{STAMP}.jsonl",
        "source_artifact_role": "event_window_source_gap",
        "row_extractor": "direct_depth_path",
    },
    {
        "path": ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_GAP_LEDGER_{STAMP}.jsonl",
        "source_artifact_role": "alt_root_gap_search",
        "row_extractor": "expected_depth_path",
    },
    {
        "path": ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_AFTER_FALLBACK_LEDGER_{STAMP}.jsonl",
        "source_artifact_role": "route_c_ladder_requirement_after_fallback",
        "row_extractor": "direct_depth_path",
    },
    {
        "path": ROUTE_DIR / f"SIERRA_DEPTH_NEAR_MATCH_REQUIREMENT_IMPACT_LEDGER_{STAMP}.jsonl",
        "source_artifact_role": "near_match_requirement_impact",
        "row_extractor": "expected_depth_path",
    },
    {
        "path": ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_REQUIREMENT_LEDGER_{STAMP}.jsonl",
        "source_artifact_role": "source_silence_microcluster_source_requirement",
        "row_extractor": "direct_depth_path",
    },
    {
        "path": ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_ACQUISITION_LEDGER_{STAMP}.jsonl",
        "source_artifact_role": "source_silence_no_api_acquisition",
        "row_extractor": "direct_depth_path",
    },
    {
        "path": ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_ACQUISITION_LEDGER_{STAMP}.jsonl",
        "source_artifact_role": "source_silence_microcluster_fragile_stress_acquisition",
        "row_extractor": "target_depth_paths_context",
    },
]

MANIFEST_PATH = ROUTE_DIR / f"{PREFIX}.json"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY.md"
SOURCE_ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ARTIFACT_LEDGER.jsonl"
REQUIREMENT_ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_REQUIREMENT_ROW_LEDGER.jsonl"
UNIQUE_SOURCE_DATE_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIQUE_SOURCE_DATE_LEDGER.jsonl"
ROOT_SCAN_LEDGER = ROUTE_DIR / f"{PREFIX}_ROOT_SCAN_LEDGER.jsonl"
PERMISSION_LEDGER = ROUTE_DIR / f"{PREFIX}_PERMISSION_LEDGER.jsonl"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_LEDGER.jsonl"
CLASSIFICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CLASSIFICATION_LEDGER.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER.jsonl"

DEPTH_NAME_RE = re.compile(
    r"^(?P<source_symbol>.+?)\.(?P<source_date>\d{4}-\d{2}-\d{2})(?P<suffix>.*)\.depth$",
    re.IGNORECASE,
)
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def parse_depth_filename(filename: str) -> dict[str, Any]:
    match = DEPTH_NAME_RE.match(filename)
    if not match:
        return {
            "source_symbol": None,
            "source_date": None,
            "source_suffix": None,
            "filename_parse_status": "UNPARSED_DEPTH_FILENAME",
            "is_delayed_depth_file": False,
        }
    suffix = match.group("suffix") or ""
    return {
        "source_symbol": match.group("source_symbol"),
        "source_date": match.group("source_date"),
        "source_suffix": suffix,
        "filename_parse_status": "PARSED_EXACT_STYLE" if suffix == "" else "PARSED_WITH_SUFFIX",
        "is_delayed_depth_file": "delayed" in suffix.lower(),
    }


def expected_filename(source_symbol: str, source_date: str) -> str:
    return f"{source_symbol}.{source_date}.depth"


def expected_path_from_row(row: dict[str, Any]) -> str | None:
    for key in ("depth_path", "expected_depth_path", "candidate_path"):
        value = row.get(key)
        if value:
            return str(value)
    source_symbol = row.get("source_symbol")
    source_date = row.get("source_date")
    if source_symbol and source_date:
        return str(Path(r"C:\SierraChart\Data\MarketDepthData") / expected_filename(str(source_symbol), str(source_date)))
    return None


def normalize_symbol_date(row: dict[str, Any], depth_path: str | None) -> tuple[str | None, str | None]:
    source_symbol = row.get("source_symbol")
    source_date = row.get("source_date")
    if source_symbol and source_date:
        return str(source_symbol), str(source_date)
    if depth_path:
        parsed = parse_depth_filename(Path(depth_path).name)
        if parsed["source_symbol"] and parsed["source_date"]:
            return str(parsed["source_symbol"]), str(parsed["source_date"])
    return None, None


def row_identity(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "gap_id",
        "alt_search_gap_id",
        "requirement_id",
        "post_fallback_requirement_status",
        "source_requirement_id",
        "acquisition_id",
        "acquisition_requirement_id",
        "near_match_impact_id",
        "request_id",
        "request_ids",
        "route_c_queue_id",
        "route_c_symbol",
        "source_silence_status",
        "requirement_type",
        "requirement_status",
        "status",
    ]
    return {key: row.get(key) for key in keys if key in row}


def extract_requirement_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_rows: list[dict[str, Any]] = []
    requirement_rows: list[dict[str, Any]] = []
    ordinal = 0
    for artifact in SOURCE_ARTIFACTS:
        path = artifact["path"]
        rows = read_jsonl(path)
        extracted_count = 0
        skipped_count = 0
        extractor = artifact["row_extractor"]
        for row_index, row in enumerate(rows, 1):
            if extractor == "target_depth_paths_context":
                context = row.get("target_source_context") or {}
                depth_paths = context.get("target_depth_paths") or []
                request_ids = context.get("target_request_ids") or row.get("request_ids") or []
                target_source_symbols = context.get("target_source_symbols") or {}
                target_source_dates = context.get("target_source_dates") or {}
                if not depth_paths:
                    skipped_count += 1
                    continue
                for depth_path in depth_paths:
                    source_symbol, source_date = normalize_symbol_date(row, str(depth_path))
                    if not source_symbol or not source_date:
                        skipped_count += 1
                        continue
                    ordinal += 1
                    extracted_count += 1
                    requirement_rows.append(
                        {
                            "route_id": ROUTE_ID,
                            "source_requirement_row_id": f"SIERRA-DEPTH-EXACT-SOURCE-REQ-ROW-{ordinal:06d}",
                            "source_artifact": rel(path),
                            "source_artifact_role": artifact["source_artifact_role"],
                            "source_row_number": row_index,
                            "source_row_identity": row_identity(row),
                            "source_symbol": source_symbol,
                            "source_date": source_date,
                            "expected_filename": expected_filename(source_symbol, source_date),
                            "expected_depth_path": str(depth_path),
                            "requirement_extraction_kind": "nested_target_depth_path_context",
                            "request_ids": request_ids,
                            "target_source_symbol_counts": target_source_symbols,
                            "target_source_date_counts": target_source_dates,
                            "original_next_same_resource_action": row.get("next_same_resource_action"),
                            "evidence_boundary": EVIDENCE_BOUNDARY,
                            "safe_flags": SAFE_FLAGS,
                        }
                    )
                continue

            depth_path = expected_path_from_row(row)
            source_symbol, source_date = normalize_symbol_date(row, depth_path)
            if not depth_path or not source_symbol or not source_date:
                skipped_count += 1
                continue
            ordinal += 1
            extracted_count += 1
            requirement_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "source_requirement_row_id": f"SIERRA-DEPTH-EXACT-SOURCE-REQ-ROW-{ordinal:06d}",
                    "source_artifact": rel(path),
                    "source_artifact_role": artifact["source_artifact_role"],
                    "source_row_number": row_index,
                    "source_row_identity": row_identity(row),
                    "source_symbol": source_symbol,
                    "source_date": source_date,
                    "expected_filename": expected_filename(source_symbol, source_date),
                    "expected_depth_path": str(depth_path),
                    "requirement_extraction_kind": extractor,
                    "request_id": row.get("request_id"),
                    "request_ids": row.get("request_ids"),
                    "requirement_type": row.get("requirement_type"),
                    "requirement_status": row.get("post_fallback_requirement_status") or row.get("requirement_status") or row.get("status"),
                    "depth_file_exists_claim": row.get("depth_file_exists"),
                    "original_recovery_bucket": row.get("recovery_bucket") or row.get("alt_recovery_bucket"),
                    "original_near_candidate_count": row.get("near_candidate_count"),
                    "original_next_same_resource_action": row.get("post_fallback_next_same_resource_action") or row.get("next_same_resource_action") or row.get("exact_acquisition_action"),
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
        source_rows.append(
            {
                "route_id": ROUTE_ID,
                "source_artifact": rel(path),
                "source_artifact_role": artifact["source_artifact_role"],
                "row_extractor": extractor,
                "source_exists": path.exists(),
                "source_input_rows": len(rows),
                "extracted_requirement_rows": extracted_count,
                "skipped_rows_without_exact_file_identity": skipped_count,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return source_rows, requirement_rows


def build_unique_requirements(requirement_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in requirement_rows:
        grouped[(row["source_symbol"], row["source_date"])].append(row)
    out: list[dict[str, Any]] = []
    for index, ((source_symbol, source_date), rows) in enumerate(
        sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])),
        1,
    ):
        paths = sorted({row["expected_depth_path"] for row in rows if row.get("expected_depth_path")})
        out.append(
            {
                "route_id": ROUTE_ID,
                "unique_source_date_requirement_id": f"SIERRA-DEPTH-EXACT-SOURCE-DATE-{index:05d}",
                "source_symbol": source_symbol,
                "source_date": source_date,
                "expected_filename": expected_filename(source_symbol, source_date),
                "expected_depth_paths": paths,
                "expected_depth_path_count": len(paths),
                "contributing_requirement_row_count": len(rows),
                "contributing_source_artifacts": sorted({row["source_artifact"] for row in rows}),
                "contributing_source_artifact_roles": dict(sorted(Counter(row["source_artifact_role"] for row in rows).items())),
                "contributing_requirement_status_counts": dict(sorted(Counter(str(row.get("requirement_status")) for row in rows).items())),
                "contributing_row_ids": [row["source_requirement_row_id"] for row in rows],
                "requirement_boundary": "exact source-symbol/source-date .depth filename identity; source rows preserved separately",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return out


def scan_roots() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    root_rows: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []
    permission_rows: list[dict[str, Any]] = []
    seen_files: set[str] = set()
    permission_ordinal = 0

    for root in SEARCH_ROOTS:
        root_depth_seen = 0
        root_parsed_seen = 0
        root_permission_count = 0
        root_error_count = 0
        root_exists = root.exists()

        def on_error(error: OSError) -> None:
            nonlocal permission_ordinal, root_permission_count, root_error_count
            root_error_count += 1
            path = getattr(error, "filename", None) or str(root)
            is_permission = isinstance(error, PermissionError) or "Access" in str(error) or "Permission" in str(error)
            if is_permission:
                root_permission_count += 1
            permission_ordinal += 1
            permission_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "permission_event_id": f"SIERRA-DEPTH-EXACT-SOURCE-PERM-{permission_ordinal:05d}",
                    "root": str(root),
                    "path": str(path),
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "permission_state": "PERMISSION_DENIED" if is_permission else "WALK_ERROR_NON_PERMISSION",
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )

        if root_exists:
            for dirpath, _dirnames, filenames in os.walk(root, onerror=on_error):
                for filename in filenames:
                    if not filename.lower().endswith(".depth"):
                        continue
                    root_depth_seen += 1
                    path = Path(dirpath) / filename
                    parsed = parse_depth_filename(filename)
                    if parsed["filename_parse_status"] != "UNPARSED_DEPTH_FILENAME":
                        root_parsed_seen += 1
                    resolved_key = str(path).lower()
                    if resolved_key in seen_files:
                        continue
                    seen_files.add(resolved_key)
                    try:
                        stat = path.stat()
                        size = stat.st_size
                        modified = datetime.fromtimestamp(stat.st_mtime, UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
                        stat_status = "stat_ok"
                    except OSError as exc:
                        size = None
                        modified = None
                        stat_status = f"stat_failed:{type(exc).__name__}:{exc}"
                    file_rows.append(
                        {
                            "route_id": ROUTE_ID,
                            "root": str(root),
                            "path": str(path),
                            "filename": filename,
                            "size_bytes": size,
                            "modified_utc": modified,
                            "stat_status": stat_status,
                            **parsed,
                            "evidence_boundary": EVIDENCE_BOUNDARY,
                            "safe_flags": SAFE_FLAGS,
                        }
                    )
        root_rows.append(
            {
                "route_id": ROUTE_ID,
                "root": str(root),
                "root_exists": root_exists,
                "depth_files_seen_under_root": root_depth_seen,
                "parsed_depth_files_seen_under_root": root_parsed_seen,
                "walk_error_count": root_error_count,
                "permission_denied_count": root_permission_count,
                "root_permission_state": (
                    "ROOT_ACCESSIBLE_NO_PERMISSION_ERRORS"
                    if root_exists and root_permission_count == 0
                    else "ROOT_ACCESSIBLE_WITH_PERMISSION_ERRORS"
                    if root_exists
                    else "ROOT_NOT_FOUND"
                ),
                "search_method": "python_os_walk_depth_suffix",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return root_rows, file_rows, permission_rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_date(value: str | None) -> date | None:
    if not value or not ISO_DATE_RE.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def days_apart(left: str | None, right: str | None) -> int | None:
    left_date = parse_date(left)
    right_date = parse_date(right)
    if left_date is None or right_date is None:
        return None
    return abs((left_date - right_date).days)


def build_candidates(
    unique_requirements: list[dict[str, Any]],
    file_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_filename: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_symbol_date: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for file_row in file_rows:
        filename = str(file_row["filename"])
        by_filename[filename].append(file_row)
        source_symbol = file_row.get("source_symbol")
        source_date = file_row.get("source_date")
        if source_symbol and source_date:
            by_symbol_date[(str(source_symbol), str(source_date))].append(file_row)
        if source_symbol:
            by_symbol[str(source_symbol)].append(file_row)

    candidate_rows: list[dict[str, Any]] = []
    classification_rows: list[dict[str, Any]] = []
    hash_cache: dict[str, tuple[str | None, str]] = {}
    candidate_ordinal = 0

    for requirement in unique_requirements:
        source_symbol = str(requirement["source_symbol"])
        source_date = str(requirement["source_date"])
        expected = str(requirement["expected_filename"])
        exact_files = by_filename.get(expected, [])
        suffix_files = [
            row
            for row in by_symbol_date.get((source_symbol, source_date), [])
            if row["filename"] != expected
        ]
        near_files = []
        for row in by_symbol.get(source_symbol, []):
            if row["filename"] == expected:
                continue
            delta = days_apart(source_date, row.get("source_date"))
            if delta is not None and 0 < delta <= 3:
                near_files.append(row)

        seen_candidate_paths: set[str] = set()
        candidate_ids: list[str] = []
        exact_count = 0
        delayed_count = 0
        suffix_count = 0
        near_count = 0
        exact_hash_ok = 0
        exact_hash_failed = 0

        def add_candidate(relation: str, row: dict[str, Any]) -> None:
            nonlocal candidate_ordinal, exact_count, delayed_count, suffix_count, near_count, exact_hash_ok, exact_hash_failed
            path = str(row["path"])
            relation_key = f"{relation}:{path}".lower()
            if relation_key in seen_candidate_paths:
                return
            seen_candidate_paths.add(relation_key)
            candidate_ordinal += 1
            candidate_id = f"SIERRA-DEPTH-EXACT-SOURCE-CAND-{candidate_ordinal:06d}"
            candidate_ids.append(candidate_id)
            is_exact = relation == "exact_filename_match"
            is_delayed = bool(row.get("is_delayed_depth_file")) or "delayed" in str(row.get("filename", "")).lower()
            if is_exact:
                exact_count += 1
            elif is_delayed:
                delayed_count += 1
            elif relation == "same_symbol_date_suffix_match":
                suffix_count += 1
            else:
                near_count += 1

            sha256 = None
            hash_status = "not_hashed_non_exact_candidate"
            if is_exact:
                if path not in hash_cache:
                    try:
                        hash_cache[path] = (sha256_file(Path(path)), "sha256_computed")
                    except OSError as exc:
                        hash_cache[path] = (None, f"sha256_failed:{type(exc).__name__}:{exc}")
                sha256, hash_status = hash_cache[path]
                if sha256:
                    exact_hash_ok += 1
                else:
                    exact_hash_failed += 1
            candidate_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "candidate_id": candidate_id,
                    "unique_source_date_requirement_id": requirement["unique_source_date_requirement_id"],
                    "candidate_relation": relation,
                    "classification_use_boundary": (
                        "exact candidates are local file proof only after hash; near/delayed candidates are not substitutions"
                    ),
                    "expected_filename": expected,
                    "candidate_filename": row.get("filename"),
                    "candidate_path": path,
                    "candidate_root": row.get("root"),
                    "candidate_source_symbol": row.get("source_symbol"),
                    "candidate_source_date": row.get("source_date"),
                    "candidate_suffix": row.get("source_suffix"),
                    "candidate_is_delayed_depth_file": is_delayed,
                    "candidate_size_bytes": row.get("size_bytes"),
                    "candidate_modified_utc": row.get("modified_utc"),
                    "candidate_stat_status": row.get("stat_status"),
                    "source_symbol": source_symbol,
                    "source_date": source_date,
                    "date_distance_days": days_apart(source_date, row.get("source_date")),
                    "sha256": sha256,
                    "hash_status": hash_status,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )

        for row in exact_files:
            add_candidate("exact_filename_match", row)
        for row in suffix_files:
            relation = "same_symbol_date_delayed_suffix_match" if row.get("is_delayed_depth_file") else "same_symbol_date_suffix_match"
            add_candidate(relation, row)
        for row in near_files:
            add_candidate("same_symbol_near_date_match_plusminus_3d", row)

        if exact_count and exact_hash_failed == 0:
            local_classification = "EXACT_LOCAL_PROOF_HASHED"
            next_action = "use hashed exact local file as source-date proof for parser/replay work; still respect original blocker semantics"
        elif exact_count:
            local_classification = "EXACT_LOCAL_MATCH_HASH_FAILED_PERMISSION_OR_IO"
            next_action = "repair file read permission or IO before using exact match"
        elif delayed_count:
            local_classification = "DELAYED_NEAR_MATCH_ONLY_NOT_SUBSTITUTABLE"
            next_action = "audit delayed-source semantics; do not substitute for exact source-date truth"
        elif suffix_count:
            local_classification = "NEAR_SUFFIX_MATCH_ONLY_NOT_SUBSTITUTABLE"
            next_action = "audit suffix/provenance semantics; do not substitute for exact source-date truth"
        elif near_count:
            local_classification = "NEAR_DATE_MATCH_ONLY_NOT_SUBSTITUTABLE"
            next_action = "use only as same-symbol adjacent-date context/proxy after exact-source proof remains unavailable"
        else:
            local_classification = "NO_LOCAL_PROOF"
            next_action = "preserve exact source-date acquisition requirement; no local exact/near proof found in reachable roots"

        classification_rows.append(
            {
                "route_id": ROUTE_ID,
                "classification_id": f"SIERRA-DEPTH-EXACT-SOURCE-CLASS-{len(classification_rows) + 1:05d}",
                "unique_source_date_requirement_id": requirement["unique_source_date_requirement_id"],
                "source_symbol": source_symbol,
                "source_date": source_date,
                "expected_filename": expected,
                "expected_depth_paths": requirement["expected_depth_paths"],
                "contributing_requirement_row_count": requirement["contributing_requirement_row_count"],
                "contributing_source_artifact_roles": requirement["contributing_source_artifact_roles"],
                "candidate_ids": candidate_ids,
                "exact_candidate_count": exact_count,
                "exact_hash_ok_count": exact_hash_ok,
                "exact_hash_failed_count": exact_hash_failed,
                "delayed_candidate_count": delayed_count,
                "same_date_suffix_candidate_count": suffix_count,
                "near_date_candidate_count": near_count,
                "local_acquisition_classification": local_classification,
                "next_same_resource_action": next_action,
                "permission_state": "SEE_ROOT_AND_PERMISSION_LEDGERS_FOR_UNTARGETED_ACCESS_ERRORS",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return candidate_rows, classification_rows


def build_questions(
    classification_rows: list[dict[str, Any]],
    permission_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    class_counts = Counter(row["local_acquisition_classification"] for row in classification_rows)
    for classification, count in sorted(class_counts.items()):
        rows.append(
            {
                "route_id": ROUTE_ID,
                "question_id": f"SIERRA-DEPTH-EXACT-SOURCE-Q-{len(rows) + 1:03d}",
                "question_family": "local_acquisition_classification",
                "bucket": classification,
                "row_count": count,
                "question": f"What exact source, parser, replay, or proxy route follows for all {count} source-date files in {classification}?",
                "next_same_resource_action": "follow classification ledger actions without using near/delayed rows as exact substitutes",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    if permission_rows:
        rows.append(
            {
                "route_id": ROUTE_ID,
                "question_id": f"SIERRA-DEPTH-EXACT-SOURCE-Q-{len(rows) + 1:03d}",
                "question_family": "permission_state",
                "bucket": "PERMISSION_DENIED_PATHS_PRESENT",
                "row_count": len(permission_rows),
                "question": "Do any permission-denied roots plausibly contain Sierra .depth caches, or are they test/system folders outside this exact source-date acquisition lane?",
                "next_same_resource_action": "review full permission ledger; request elevated access only for paths that plausibly contain Sierra depth data",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def write_summary(path: Path, result: dict[str, Any]) -> None:
    counts = result["counts"]
    lines = [
        "# Sierra Depth Exact Source-Date Acquisition Manifest",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: exact local `.depth` source-date file discovery/acquisition routing only. No paid/vendor calls were made.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Classifications", ""])
    for key, value in result["local_acquisition_classification_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Candidate Relations", ""])
    for key, value in result["candidate_relation_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Exact matches were SHA-256 hashed and recorded as local source-date proof only.",
            "- Near, suffix, and delayed files were preserved as leads/proxies only and are not substitutions.",
            "- Permission errors are preserved in the permission ledger and not hidden.",
            "- Shared `OUTPUT_MANIFEST`, `SPRINT_OPERATING_LEDGER`, verifier files, and `.context` were not edited.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_rows, requirement_rows = extract_requirement_rows()
    unique_requirements = build_unique_requirements(requirement_rows)
    root_rows, file_rows, permission_rows = scan_roots()
    candidate_rows, classification_rows = build_candidates(unique_requirements, file_rows)
    question_rows = build_questions(classification_rows, permission_rows)

    write_jsonl(SOURCE_ARTIFACT_LEDGER, source_rows)
    write_jsonl(REQUIREMENT_ROW_LEDGER, requirement_rows)
    write_jsonl(UNIQUE_SOURCE_DATE_LEDGER, unique_requirements)
    write_jsonl(ROOT_SCAN_LEDGER, root_rows)
    write_jsonl(PERMISSION_LEDGER, permission_rows)
    write_jsonl(CANDIDATE_LEDGER, candidate_rows)
    write_jsonl(CLASSIFICATION_LEDGER, classification_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)

    candidate_relation_counts = Counter(row["candidate_relation"] for row in candidate_rows)
    classification_counts = Counter(row["local_acquisition_classification"] for row in classification_rows)
    root_permission_counts = Counter(row["root_permission_state"] for row in root_rows)
    counts = {
        "source_artifacts_considered": len(source_rows),
        "source_artifacts_existing": sum(1 for row in source_rows if row["source_exists"]),
        "source_input_rows_total": sum(int(row["source_input_rows"]) for row in source_rows),
        "extracted_requirement_rows": len(requirement_rows),
        "unique_source_date_requirements": len(unique_requirements),
        "search_root_rows": len(root_rows),
        "unique_depth_files_seen": len(file_rows),
        "permission_denied_or_walk_error_rows": len(permission_rows),
        "candidate_rows": len(candidate_rows),
        "exact_candidate_rows": candidate_relation_counts["exact_filename_match"],
        "exact_candidate_rows_sha256_hashed": sum(1 for row in candidate_rows if row["candidate_relation"] == "exact_filename_match" and row.get("sha256")),
        "delayed_candidate_rows": sum(1 for row in candidate_rows if row.get("candidate_is_delayed_depth_file")),
        "same_date_suffix_candidate_rows": candidate_relation_counts["same_symbol_date_suffix_match"],
        "near_date_candidate_rows": candidate_relation_counts["same_symbol_near_date_match_plusminus_3d"],
        "classification_rows": len(classification_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_exact_source_date_acquisition_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": EVIDENCE_BOUNDARY,
        "search_roots": [str(root) for root in SEARCH_ROOTS],
        "source_artifacts": [row["source_artifact"] for row in source_rows],
        "counts": counts,
        "local_acquisition_classification_counts": dict(sorted(classification_counts.items())),
        "candidate_relation_counts": dict(sorted(candidate_relation_counts.items())),
        "root_permission_state_counts": dict(sorted(root_permission_counts.items())),
        "artifacts": {
            "builder": rel(Path(__file__).resolve()),
            "manifest": rel(MANIFEST_PATH),
            "summary": rel(SUMMARY_PATH),
            "source_artifact_ledger": rel(SOURCE_ARTIFACT_LEDGER),
            "requirement_row_ledger": rel(REQUIREMENT_ROW_LEDGER),
            "unique_source_date_ledger": rel(UNIQUE_SOURCE_DATE_LEDGER),
            "root_scan_ledger": rel(ROOT_SCAN_LEDGER),
            "permission_ledger": rel(PERMISSION_LEDGER),
            "candidate_ledger": rel(CANDIDATE_LEDGER),
            "classification_ledger": rel(CLASSIFICATION_LEDGER),
            "question_ledger": rel(QUESTION_LEDGER),
        },
        "explicit_non_edits": [
            "OUTPUT_MANIFEST_2026-05-15.json",
            "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl",
            "verify_weekend_moonshot_initial_artifacts_2026_05_15.py",
            ".context/*",
        ],
        "no_paid_vendor_calls": True,
        "not_completion": "This is only the Route C exact Sierra .depth source-date acquisition packet requested by the owner.",
    }
    MANIFEST_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(SUMMARY_PATH, result)
    print(json.dumps({"ok": True, "counts": counts, "manifest": str(MANIFEST_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
