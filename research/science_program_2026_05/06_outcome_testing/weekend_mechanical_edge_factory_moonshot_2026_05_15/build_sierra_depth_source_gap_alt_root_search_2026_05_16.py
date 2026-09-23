#!/usr/bin/env python3
"""Search approved local roots for missing Sierra .depth source-date gaps."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

SOURCE_GAP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_SOURCE_GAP_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_SEARCH_RESULT_{STAMP}.json"
ROOT_SCAN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_SCAN_LEDGER_{STAMP}.jsonl"
GAP_SEARCH_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_GAP_LEDGER_{STAMP}.jsonl"
CANDIDATE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_CANDIDATE_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_SEARCH_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SEARCH_ROOTS = [
    Path(r"C:\SierraChart"),
    Path(r"C:\tmp"),
    Path(r"C:\Users\MSI\Documents\ai-trading-agent"),
    Path(r"C:\Users\MSI\Documents"),
]

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Local alternate-root search for missing Sierra .depth files only; no strategy "
    "validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

DEPTH_NAME_RE = re.compile(r"^(?P<source_symbol>.+?)\.(?P<source_date>\d{4}-\d{2}-\d{2})(?P<suffix>.*)\.depth$")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_depth_name(path: Path) -> dict[str, Any]:
    match = DEPTH_NAME_RE.match(path.name)
    if not match:
        return {
            "source_symbol": None,
            "source_date": None,
            "suffix": None,
            "depth_filename_parse_status": "UNPARSED_DEPTH_FILENAME",
        }
    suffix = match.group("suffix") or ""
    return {
        "source_symbol": match.group("source_symbol"),
        "source_date": match.group("source_date"),
        "suffix": suffix,
        "depth_filename_parse_status": "PARSED_EXACT_STYLE" if not suffix else "PARSED_WITH_SUFFIX",
    }


def gap_filename(row: dict[str, Any]) -> str:
    path = str(row.get("depth_path") or "")
    return Path(path).name


def scan_depth_roots() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root_rows: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for root in SEARCH_ROOTS:
        root_errors: list[dict[str, str]] = []
        depth_files = 0
        parsed_files = 0
        exists = root.exists()

        def on_error(error: OSError) -> None:
            root_errors.append(
                {
                    "path": getattr(error, "filename", None) or str(root),
                    "error": f"{type(error).__name__}: {error}",
                }
            )

        if exists:
            for dirpath, _dirnames, filenames in os.walk(root, onerror=on_error):
                for filename in filenames:
                    if not filename.lower().endswith(".depth"):
                        continue
                    depth_files += 1
                    path = Path(dirpath) / filename
                    resolved_key = str(path).lower()
                    if resolved_key in seen_paths:
                        continue
                    seen_paths.add(resolved_key)
                    parsed = parse_depth_name(path)
                    if parsed["depth_filename_parse_status"] != "UNPARSED_DEPTH_FILENAME":
                        parsed_files += 1
                    try:
                        stat = path.stat()
                        size = stat.st_size
                        modified_utc = datetime.fromtimestamp(stat.st_mtime, UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
                    except OSError as exc:
                        size = None
                        modified_utc = None
                        root_errors.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
                    file_rows.append(
                        {
                            "route_id": ROUTE_ID,
                            "root": str(root),
                            "path": str(path),
                            "filename": path.name,
                            "size_bytes": size,
                            "modified_utc": modified_utc,
                            **parsed,
                            "evidence_boundary": EVIDENCE_BOUNDARY,
                            "safe_flags": SAFE_FLAGS,
                        }
                    )
        root_rows.append(
            {
                "route_id": ROUTE_ID,
                "root": str(root),
                "root_exists": exists,
                "depth_files_seen_under_root": depth_files,
                "parsed_depth_files_seen_under_root": parsed_files,
                "error_count": len(root_errors),
                "errors": root_errors,
                "search_method": "python_os_walk_depth_suffix",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return root_rows, file_rows


def recovery_bucket(exact: list[dict[str, Any]], near: list[dict[str, Any]]) -> str:
    if exact:
        return "EXACT_ALTERNATE_DEPTH_FILE_FOUND"
    if near:
        return "NEAR_MATCH_SUFFIX_OR_DELAYED_FILE_ONLY"
    return "NO_ALTERNATE_DEPTH_FILE_FOUND"


def next_action(bucket: str) -> str:
    if bucket == "EXACT_ALTERNATE_DEPTH_FILE_FOUND":
        return "hash and parser-audit exact alternate files before rerunning affected depth windows"
    if bucket == "NEAR_MATCH_SUFFIX_OR_DELAYED_FILE_ONLY":
        return "inspect source semantics of delayed/suffixed file before any use; do not substitute silently"
    return "preserve exact source-date capture requirement or search vendor/current-source routes if allowed"


def build_search_rows(
    gap_rows: list[dict[str, Any]],
    file_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    files_by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    files_by_symbol_date: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for file_row in file_rows:
        files_by_name[str(file_row["filename"])].append(file_row)
        source_symbol = file_row.get("source_symbol")
        source_date = file_row.get("source_date")
        if source_symbol and source_date:
            files_by_symbol_date[(str(source_symbol), str(source_date))].append(file_row)

    search_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    candidate_ordinal = 0
    for index, gap in enumerate(gap_rows, 1):
        filename = gap_filename(gap)
        source_symbol = str(gap.get("source_symbol"))
        source_date = str(gap.get("source_date"))
        exact = files_by_name.get(filename, [])
        near = [
            row for row in files_by_symbol_date.get((source_symbol, source_date), [])
            if row["filename"] != filename
        ]
        bucket = recovery_bucket(exact, near)
        bucket_counts[bucket] += 1
        candidate_refs: list[str] = []
        for relation, candidates in [("exact_filename_match", exact), ("same_symbol_date_suffix_match", near)]:
            for candidate in candidates:
                candidate_ordinal += 1
                candidate_id = f"SIERRA-DEPTH-ALT-CAND-{candidate_ordinal:05d}"
                candidate_refs.append(candidate_id)
                candidate_path = Path(str(candidate["path"]))
                try:
                    digest = sha256_file(candidate_path)
                    hash_status = "sha256_computed"
                except OSError as exc:
                    digest = None
                    hash_status = f"sha256_failed:{type(exc).__name__}:{exc}"
                candidate_rows.append(
                    {
                        "route_id": ROUTE_ID,
                        "candidate_id": candidate_id,
                        "gap_id": gap.get("gap_id"),
                        "candidate_relation": relation,
                        "expected_filename": filename,
                        "candidate_filename": candidate.get("filename"),
                        "candidate_path": candidate.get("path"),
                        "candidate_root": candidate.get("root"),
                        "source_symbol": source_symbol,
                        "source_date": source_date,
                        "candidate_suffix": candidate.get("suffix"),
                        "candidate_size_bytes": candidate.get("size_bytes"),
                        "candidate_modified_utc": candidate.get("modified_utc"),
                        "sha256": digest,
                        "hash_status": hash_status,
                        "use_status": (
                            "EXACT_FILE_REQUIRES_PARSER_AUDIT_BEFORE_USE"
                            if relation == "exact_filename_match"
                            else "NEAR_MATCH_NOT_SUBSTITUTABLE_WITHOUT_SOURCE_SEMANTICS_AUDIT"
                        ),
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "safe_flags": SAFE_FLAGS,
                    }
                )
        search_rows.append(
            {
                "route_id": ROUTE_ID,
                "alt_search_gap_id": f"SIERRA-DEPTH-ALT-GAP-{index:05d}",
                "gap_id": gap.get("gap_id"),
                "source_symbol": source_symbol,
                "source_date": source_date,
                "expected_depth_path": gap.get("depth_path"),
                "expected_filename": filename,
                "request_rows": gap.get("request_rows"),
                "request_family_counts": gap.get("request_family_counts"),
                "exact_candidate_count": len(exact),
                "near_symbol_date_candidate_count": len(near),
                "candidate_ids": candidate_refs,
                "recovery_bucket": bucket,
                "next_same_resource_action": next_action(bucket),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return search_rows, candidate_rows, bucket_counts


def build_questions(bucket_counts: Counter[str], root_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ordinal = 0
    for bucket, count in sorted(bucket_counts.items()):
        ordinal += 1
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-ALT-Q-{ordinal:03d}",
                "question_family": "recovery_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"What exact extraction, parser-audit, or capture route follows for all {count} gaps in {bucket}?",
                "next_same_resource_action": next_action(bucket),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    access_denied_roots = [
        root for root in root_rows
        if any("Access" in error.get("error", "") or "Permission" in error.get("error", "") for error in root.get("errors", []))
    ]
    if access_denied_roots:
        ordinal += 1
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-ALT-Q-{ordinal:03d}",
                "question_family": "search_access_error",
                "bucket": "LOCAL_ROOT_ACCESS_ERRORS_PRESENT",
                "row_count": sum(root.get("error_count", 0) for root in access_denied_roots),
                "question": "Do any access-denied temp roots contain depth caches that require owner/admin read access, or are they pytest temp directories irrelevant to Sierra depth recovery?",
                "next_same_resource_action": "record exact denied roots and continue with accessible roots; request access only if path names suggest market data caches",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    delayed_candidates = [row for row in candidate_rows if row.get("candidate_suffix")]
    if delayed_candidates:
        ordinal += 1
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-ALT-Q-{ordinal:03d}",
                "question_family": "delayed_suffix_candidate",
                "bucket": "NEAR_MATCH_DELAYED_OR_SUFFIXED_DEPTH_FILES",
                "row_count": len(delayed_candidates),
                "question": "Can delayed/suffixed Sierra sample files be used only as parser fixtures or source-semantics leads, not substitutes for exact source-date truth?",
                "next_same_resource_action": "audit delayed/suffix provenance before any parser-fixture reuse; do not fill missing depth windows from delayed samples",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_source_gap_alt_root_search_builder", "created"),
        (RESULT_PATH, "sierra_depth_source_gap_alt_root_search_result", "created"),
        (ROOT_SCAN_LEDGER, "sierra_depth_source_gap_alt_root_scan_ledger", "created"),
        (GAP_SEARCH_LEDGER, "sierra_depth_source_gap_alt_root_gap_ledger", "created"),
        (CANDIDATE_LEDGER, "sierra_depth_source_gap_alt_root_candidate_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_source_gap_alt_root_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_source_gap_alt_root_search_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_source_gap_alt_root_search",
        "status": "done",
        "route": "sierra_depth_source_gap_repair",
        "details": "Searched approved local roots for every missing Sierra .depth source-date gap and preserved exact/near/no-recovery status.",
        "counts": counts,
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(ROOT_SCAN_LEDGER),
            relative(GAP_SEARCH_LEDGER),
            relative(CANDIDATE_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], bucket_counts: Counter[str]) -> None:
    lines = [
        "# Sierra Depth Source-Gap Alternate-Root Search",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: local file discovery and exact source-gap repair routing only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Recovery Buckets", ""])
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Every missing depth source-date gap was searched against the accessible approved roots.",
            "- Exact alternate files, if any, still require parser/source audit before use.",
            "- Near delayed/suffix files are not substitutions for exact source-date truth.",
            "- Access-denied roots are preserved in the root scan ledger.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Convert unrecovered gaps into exact forward-capture/source-acquisition requirements.",
            "- Use delayed/suffix files only for parser-fixture or provenance analysis after audit.",
            "- Continue the independent ladder-snapshotter route for the locally available depth files.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    gap_rows = read_jsonl(SOURCE_GAP_LEDGER)
    root_rows, file_rows = scan_depth_roots()
    search_rows, candidate_rows, bucket_counts = build_search_rows(gap_rows, file_rows)
    question_rows = build_questions(bucket_counts, root_rows, candidate_rows)
    write_jsonl(ROOT_SCAN_LEDGER, root_rows)
    write_jsonl(GAP_SEARCH_LEDGER, search_rows)
    write_jsonl(CANDIDATE_LEDGER, candidate_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    counts = {
        "searched_root_rows": len(root_rows),
        "unique_depth_files_seen": len(file_rows),
        "missing_source_gap_rows": len(gap_rows),
        "gap_search_rows": len(search_rows),
        "candidate_rows": len(candidate_rows),
        "exact_candidate_rows": sum(1 for row in candidate_rows if row["candidate_relation"] == "exact_filename_match"),
        "near_candidate_rows": sum(1 for row in candidate_rows if row["candidate_relation"] != "exact_filename_match"),
        "root_error_count": sum(int(row.get("error_count") or 0) for row in root_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_source_gap_alt_root_search_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_SEARCH_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "recovery_bucket_counts": dict(sorted(bucket_counts.items())),
        "search_roots": [str(root) for root in SEARCH_ROOTS],
        "next_same_resource_work": [
            "convert unrecovered exact gaps into source-capture requirements",
            "audit any exact alternate file candidates before rerun",
            "treat delayed/suffixed near candidates as parser/source-semantics leads only",
        ],
        "not_completion": "This source-gap search repairs the local discovery layer but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(sorted(bucket_counts.items())))
    write_summary(generated_utc, counts, bucket_counts)
    print(json.dumps({"ok": True, "counts": counts, "bucket_counts": dict(bucket_counts), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
