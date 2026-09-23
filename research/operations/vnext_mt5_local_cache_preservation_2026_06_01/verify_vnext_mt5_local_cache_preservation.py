"""Verify local MT5 cache preservation route artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

import build_vnext_mt5_local_cache_preservation as builder


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]

REQUIRED_FILES = [
    "ROUTE_CONTEXT_ANCHOR.json",
    "MT5_LOCAL_CACHE_INVENTORY.jsonl",
    "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json",
    "MT5_SENSITIVE_EXCLUSION_LEDGER.jsonl",
    "MT5_ARCHIVE_INCLUDE_LEDGER.jsonl",
    "MT5_ARCHIVE_MANIFEST.json",
    "MT5_ARCHIVE_LISTING.jsonl",
    "MT5_REPO_COVERAGE_COMPARISON.json",
    "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl",
    "MT5_UNREADABLE_OR_BLOCKED_LEDGER.jsonl",
    "MT5_MISSING_ROOT_LEDGER.jsonl",
    "OUTPUT_MANIFEST.json",
    "COMPLETION_AUDIT.json",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_no}: {exc}") from exc
    return rows


def run_py_compile() -> dict[str, Any]:
    files = [
        ROUTE_DIR / "build_vnext_mt5_local_cache_preservation.py",
        ROUTE_DIR / "verify_vnext_mt5_local_cache_preservation.py",
        ROUTE_DIR / "test_vnext_mt5_local_cache_preservation.py",
    ]
    command = [sys.executable, "-m", "py_compile", *[str(path) for path in files if path.exists()]]
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def verify_manifest_hashes(issues: list[str]) -> None:
    manifest = read_json(ROUTE_DIR / "OUTPUT_MANIFEST.json")
    for row in manifest.get("files", []):
        if row.get("hash_status") != "sha256":
            continue
        path = REPO_ROOT / row["path"]
        if not path.exists():
            issues.append(f"output_manifest_missing_path:{row['path']}")
            continue
        if path.stat().st_size != row.get("bytes"):
            issues.append(f"output_manifest_byte_mismatch:{row['path']}")
        if builder.sha256_file(path) != row.get("sha256"):
            issues.append(f"output_manifest_sha256_mismatch:{row['path']}")


def verify_archive(issues: list[str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = read_json(ROUTE_DIR / "MT5_ARCHIVE_MANIFEST.json")
    listing = read_jsonl(ROUTE_DIR / "MT5_ARCHIVE_LISTING.jsonl")
    archive_path = Path(manifest.get("archive_path", ""))
    if not archive_path.exists():
        issues.append("archive_missing_on_disk")
        return manifest, listing
    archive_bytes = archive_path.stat().st_size
    if archive_bytes != manifest.get("archive_bytes"):
        issues.append("archive_byte_count_mismatch")
    if builder.sha256_file(archive_path) != manifest.get("archive_sha256"):
        issues.append("archive_sha256_mismatch")
    if not listing:
        issues.append("archive_listing_missing_or_empty")
    if len(listing) != manifest.get("archived_file_count"):
        issues.append("archive_listing_count_mismatch")
    if sum(int(row["size_bytes"]) for row in listing) != manifest.get("archived_uncompressed_bytes"):
        issues.append("archive_listing_uncompressed_bytes_mismatch")
    try:
        with tarfile.open(archive_path, mode="r:gz") as archive:
            first = next((member for member in archive.getmembers() if member.isfile()), None)
            if first is None:
                issues.append("archive_has_no_file_members")
    except tarfile.TarError as exc:
        issues.append(f"archive_not_readable:{exc}")
    return manifest, listing


def verify_current_disk_counts(summary: dict[str, Any], issues: list[str]) -> None:
    rows, blocked, missing = builder.enumerate_local_mt5_files()
    if len(rows) != summary.get("source_file_count"):
        issues.append(f"current_disk_source_file_count_changed:{len(rows)}!={summary.get('source_file_count')}")
    current_bytes = sum(int(row["size_bytes"]) for row in rows)
    if current_bytes != summary.get("source_bytes"):
        issues.append(f"current_disk_source_bytes_changed:{current_bytes}!={summary.get('source_bytes')}")
    if len(blocked) != summary.get("unreadable_row_count"):
        issues.append("current_disk_unreadable_count_changed")
    if len(missing) != summary.get("missing_root_count"):
        issues.append("current_disk_missing_root_count_changed")


def verify(check: bool = False) -> dict[str, Any]:
    issues: list[str] = []
    for name in REQUIRED_FILES:
        if not (ROUTE_DIR / name).exists():
            issues.append(f"missing_required_file:{name}")
    if issues:
        payload = {
            "schema_version": "mt5_local_cache_verification_result_v1",
            "route_id": builder.ROUTE_ID,
            "generated_at_utc": builder.utc_now(),
            "ok": False,
            "issues": issues,
        }
        builder.json_dump(ROUTE_DIR / "VERIFICATION_RESULT.json", payload)
        return payload

    inventory = read_jsonl(ROUTE_DIR / "MT5_LOCAL_CACHE_INVENTORY.jsonl")
    include_rows = read_jsonl(ROUTE_DIR / "MT5_ARCHIVE_INCLUDE_LEDGER.jsonl")
    sensitive_rows = read_jsonl(ROUTE_DIR / "MT5_SENSITIVE_EXCLUSION_LEDGER.jsonl")
    blocked_rows = read_jsonl(ROUTE_DIR / "MT5_UNREADABLE_OR_BLOCKED_LEDGER.jsonl")
    missing_rows = read_jsonl(ROUTE_DIR / "MT5_MISSING_ROOT_LEDGER.jsonl")
    summary = read_json(ROUTE_DIR / "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json")
    comparison = read_json(ROUTE_DIR / "MT5_REPO_COVERAGE_COMPARISON.json")

    if len(inventory) <= 100:
        issues.append("external_mt5_cache_only_presence_inventoried_or_too_few_rows")
    if summary.get("source_file_count") != len(inventory):
        issues.append("summary_inventory_count_mismatch")
    if summary.get("source_bytes") != sum(int(row["size_bytes"]) for row in inventory):
        issues.append("summary_inventory_bytes_mismatch")
    if blocked_rows:
        issues.append(f"unreadable_or_archive_blocker_rows_present:{len(blocked_rows)}")
    if missing_rows:
        issues.append(f"missing_source_root_rows_present:{len(missing_rows)}")

    bases_rows = [
        row
        for row in inventory
        if row.get("path") and ("\\bases\\" in row["path"].lower() or "/bases/" in row["path"].lower())
    ]
    if not bases_rows:
        issues.append("bases_not_classified")
    for ext in [".hcc", ".hc", ".tkc", ".dat", ".welcome"]:
        if summary.get("bases_required_extension_classification", {}).get(ext, 0) <= 0:
            issues.append(f"bases_extension_not_classified:{ext}")

    include_names = {row.get("archive_member_path") for row in include_rows}
    manifest, listing = verify_archive(issues)
    listing_names = {row.get("archive_member_path") for row in listing}
    missing_from_archive = sorted(name for name in include_names if name not in listing_names)
    extra_in_archive = sorted(name for name in listing_names if name not in include_names)
    if missing_from_archive:
        issues.append(f"archive_missing_included_members:{len(missing_from_archive)}")
    if extra_in_archive:
        issues.append(f"archive_has_unplanned_members:{len(extra_in_archive)}")

    nonsecret_evidence_unarchived = [
        row
        for row in inventory
        if row.get("evidence_role") in builder.EVIDENCE_ROLES_ARCHIVED
        and row.get("archive_decision") != "include_archive"
    ]
    if nonsecret_evidence_unarchived:
        issues.append(f"nonsecret_evidence_not_archived_or_blocked:{len(nonsecret_evidence_unarchived)}")

    if sensitive_rows and not all(row.get("path_sha256") and row.get("exclusion_reason") for row in sensitive_rows):
        issues.append("sensitive_exclusions_missing_path_hash_or_reason")
    if any(row.get("path") for row in sensitive_rows):
        issues.append("sensitive_exclusion_contains_clear_path")
    if summary.get("sensitive_excluded_file_count") != len(sensitive_rows):
        issues.append("sensitive_exclusion_count_mismatch")

    if not comparison.get("external_mt5_adds_broker_server_cache"):
        issues.append("coverage_comparison_missing_broker_server_cache_increment")
    if not comparison.get("external_mt5_adds_terminal_or_ea_runtime_logs"):
        issues.append("coverage_comparison_missing_runtime_log_increment")
    if comparison.get("previous_external_mt5_status") != "presence_only_inventory_closed_by_this_followup_route":
        issues.append("previous_presence_only_gap_not_closed")

    if manifest.get("archive_path", "").startswith(str(REPO_ROOT)):
        issues.append("archive_is_inside_git_repo")
    if manifest.get("archive_candidate_file_count") != len(include_rows):
        issues.append("archive_manifest_candidate_count_mismatch")
    if manifest.get("archive_candidate_bytes") != sum(int(row["size_bytes"]) for row in include_rows):
        issues.append("archive_manifest_candidate_bytes_mismatch")
    if manifest.get("archive_blocker_count", 0) != 0:
        issues.append("archive_manifest_reports_blockers")

    builder.output_manifest()
    verify_manifest_hashes(issues)
    verify_current_disk_counts(summary, issues)
    compile_result = run_py_compile()
    if compile_result["returncode"] != 0:
        issues.append("py_compile_failed")

    ok = not issues
    payload = {
        "schema_version": "mt5_local_cache_verification_result_v1",
        "route_id": builder.ROUTE_ID,
        "generated_at_utc": builder.utc_now(),
        "ok": ok,
        "issues": issues,
        "counts": {
            "inventory_rows": len(inventory),
            "bases_rows": len(bases_rows),
            "archive_include_rows": len(include_rows),
            "archive_listing_rows": len(listing),
            "sensitive_exclusion_rows": len(sensitive_rows),
            "blocked_rows": len(blocked_rows),
            "missing_root_rows": len(missing_rows),
            "archive_bytes": manifest.get("archive_bytes"),
        },
        "checks": [compile_result],
    }
    builder.json_dump(ROUTE_DIR / "VERIFICATION_RESULT.json", payload)
    builder.completion_audit(ok, issues)
    builder.output_manifest()
    if check and not ok:
        raise SystemExit(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = verify(check=args.check)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
