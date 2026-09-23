#!/usr/bin/env python3
"""Audit a GTOS goal-route directory for required artifact classes.

The orchestrator should still read the artifacts. This script is a guardrail:
it makes missing completion audits, decision ledgers, verifiers, manifests,
next prompts, and large-ledger inventories visible before the next route is
prepared or merged.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import signal
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Any


TRANSIENT_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    "tmp_pytest",
    "pytest_cache",
}


REQUIRED_BY_PROFILE: dict[str, tuple[str, ...]] = {
    "standard": (
        "completion_audit",
        "decision_or_terminal_ledger",
        "verification_result",
        "output_manifest",
        "verifier_script",
        "focused_test",
    ),
    "launch-pack": (
        "completion_audit",
        "decision_or_terminal_ledger",
        "next_prompt_or_starter",
    ),
    "terminal": (
        "completion_audit",
        "decision_or_terminal_ledger",
        "verification_result",
    ),
}

WARNING_BY_PROFILE: dict[str, tuple[str, ...]] = {
    "standard": (
        "next_prompt_or_starter",
        "blocker_or_repair_ledger",
        "saturation_or_self_red_team",
    ),
    "launch-pack": ("output_manifest", "verification_result"),
    "terminal": ("next_prompt_or_starter",),
}


STATUS_KEYS = (
    "status",
    "terminal_status",
    "decision",
    "terminal_decision",
    "row_status",
    "missing_status",
    "result_status",
    "role",
)

READ_CHUNK_TIMEOUT_SECONDS = 30
READ_CHUNK_TIMEOUT_RETRIES = 5
BROAD_REPLAY_ARTIFACT_PREFIX = "BROAD_LIVE_AS_IF_REPLAY_"
GENERATED_REPLAY_ARTIFACT_PREFIXES = (
    BROAD_REPLAY_ARTIFACT_PREFIX,
    "BROAD_REPLAY_",
    "REPLAY_EXTENSION_",
    "PHASE2_",
    "SOURCE_BOUND_TO_EXECUTED_PARITY_",
    "EXECUTION_LEAKAGE_",
    "BIG_R_PROVENANCE_",
)
GENERATED_REPLAY_ARTIFACT_MARKERS = (
    "_SMOKE",
    "_PARTIAL",
    "_ABORTED",
)


@contextmanager
def read_deadline(seconds: int = READ_CHUNK_TIMEOUT_SECONDS):
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, 0)

    def _timeout_handler(signum, frame):  # noqa: ARG001
        raise TimeoutError(f"timed out reading file chunk after {seconds}s")

    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])


def iter_files(route_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in route_dir.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = {part.lower() for part in path.relative_to(route_dir).parts}
        if rel_parts & TRANSIENT_DIR_NAMES:
            continue
        files.append(path)
    return files


def _is_gzip_file(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            with read_deadline():
                return handle.read(2) == b"\x1f\x8b"
    except OSError:
        return False


def _open_jsonl_text(path: Path):
    if _is_gzip_file(path):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def iter_text_lines_with_retries(path: Path, *, chunk_size: int = 4 * 1024 * 1024):
    if _is_gzip_file(path):
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
            while True:
                try:
                    with read_deadline():
                        line = handle.readline()
                except TimeoutError:
                    raise OSError(f"timed out reading gzip text from {path}")
                if not line:
                    break
                yield line
        return
    pending = b""
    timeout_retries = 0
    with path.open("rb") as handle:
        while True:
            try:
                with read_deadline():
                    chunk = handle.read(chunk_size)
            except TimeoutError:
                timeout_retries += 1
                if timeout_retries > READ_CHUNK_TIMEOUT_RETRIES:
                    raise OSError(
                        f"timed out reading {path} after "
                        f"{READ_CHUNK_TIMEOUT_RETRIES} retries"
                    )
                time.sleep(0.5)
                continue
            timeout_retries = 0
            if not chunk:
                if pending:
                    yield pending.decode("utf-8", errors="replace")
                break
            parts = chunk.splitlines(keepends=True)
            if pending:
                parts[0] = pending + parts[0]
                pending = b""
            if parts and not parts[-1].endswith((b"\n", b"\r")):
                pending = parts.pop()
            for raw_line in parts:
                yield raw_line.decode("utf-8", errors="replace")


def read_text_with_retries(path: Path) -> str:
    return "".join(iter_text_lines_with_retries(path))


def _manifest_string_values(value: Any) -> set[str]:
    strings: set[str] = set()
    if isinstance(value, str):
        strings.add(value)
    elif isinstance(value, list):
        for item in value:
            strings.update(_manifest_string_values(item))
    elif isinstance(value, dict):
        for item in value.values():
            strings.update(_manifest_string_values(item))
    return strings


def _load_manifest_authority(route_dir: Path) -> tuple[set[str], str | None, str | None]:
    manifest_path = route_dir / "OUTPUT_MANIFEST.json"
    if not manifest_path.exists():
        return set(), None, None
    try:
        manifest = json.loads(read_text_with_retries(manifest_path))
    except (OSError, json.JSONDecodeError):
        return set(), None, None
    if not isinstance(manifest, dict):
        return set(), None, None
    manifest_strings = _manifest_string_values(manifest)
    manifest_names = {Path(value).name for value in manifest_strings}
    prefix = manifest.get("broad_quality_parity_prefix")
    tag = manifest.get("broad_quality_parity_tag")
    return manifest_names | manifest_strings, prefix if isinstance(prefix, str) else None, tag if isinstance(tag, str) else None


def _is_superseded_broad_replay_artifact(
    path: Path,
    route_dir: Path,
    *,
    manifest_authority: set[str],
    active_broad_prefix: str | None,
) -> bool:
    name = path.name
    if not name.startswith(BROAD_REPLAY_ARTIFACT_PREFIX):
        return False
    rel = path.relative_to(route_dir).as_posix()
    if name in manifest_authority or rel in manifest_authority:
        return False
    if active_broad_prefix and name.startswith(active_broad_prefix):
        return False
    return True


def _is_superseded_generated_replay_artifact(
    path: Path,
    route_dir: Path,
    *,
    manifest_authority: set[str],
    active_broad_prefix: str | None,
) -> bool:
    rel = path.relative_to(route_dir).as_posix()
    name = path.name
    if rel in manifest_authority or name in manifest_authority:
        return False
    if active_broad_prefix and name.startswith(active_broad_prefix):
        return False
    if name.startswith(GENERATED_REPLAY_ARTIFACT_PREFIXES):
        return True
    return any(marker in name for marker in GENERATED_REPLAY_ARTIFACT_MARKERS)


def classify_files(files: list[Path], route_dir: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {
        "completion_audit": [],
        "decision_or_terminal_ledger": [],
        "verification_result": [],
        "output_manifest": [],
        "builder_script": [],
        "verifier_script": [],
        "focused_test": [],
        "next_prompt_or_starter": [],
        "blocker_or_repair_ledger": [],
        "saturation_or_self_red_team": [],
    }
    for path in files:
        rel = path.relative_to(route_dir).as_posix().lower()
        name = path.name.lower()
        suffix = path.suffix.lower()

        def add(category: str) -> None:
            found[category].append(path.relative_to(route_dir).as_posix())

        if "completion_audit" in rel or "completion-audit" in rel:
            add("completion_audit")
        if any(token in rel for token in ("decision_ledger", "terminal_decision", "synthesis")):
            add("decision_or_terminal_ledger")
        if "verification_result" in rel or "verifier_result" in rel:
            add("verification_result")
        if "output_manifest" in rel or name == "manifest.json" or "_manifest_" in name:
            add("output_manifest")
        if suffix == ".py" and (name.startswith("build_") or "builder" in name):
            add("builder_script")
        if suffix == ".py" and not name.startswith("test_") and (
            name.startswith("verify_") or "verifier" in name
        ):
            add("verifier_script")
        if (suffix == ".py" and name.startswith("test_")) or any(
            token in rel for token in ("focused_test_result", "pytest_result")
        ):
            add("focused_test")
        if any(token in rel for token in ("prompt", "starter")):
            add("next_prompt_or_starter")
        if any(token in rel for token in ("blocker", "repair", "fail_closed", "fail-closed")):
            add("blocker_or_repair_ledger")
        if any(token in rel for token in ("saturation", "self_red_team", "self-red-team")):
            add("saturation_or_self_red_team")
    for category, matches in found.items():
        found[category] = sorted(set(matches))
    return found


def scan_jsonl(path: Path, max_rows: int | None) -> dict[str, Any]:
    rows = 0
    parse_errors = 0
    read_errors: list[str] = []
    keys: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    first_row_keys: list[str] | None = None
    try:
        for line in iter_text_lines_with_retries(path):
            if max_rows is not None and rows >= max_rows:
                break
            if not line.strip():
                continue
            rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if isinstance(row, dict):
                if first_row_keys is None:
                    first_row_keys = sorted(row.keys())
                keys.update(row.keys())
                for key in STATUS_KEYS:
                    value = row.get(key)
                    if isinstance(value, str):
                        statuses[f"{key}={value}"] += 1
    except OSError as exc:
        read_errors.append(f"{type(exc).__name__}: {exc}")
    return {
        "path": str(path),
        "rows_scanned": rows,
        "parse_errors": parse_errors,
        "read_errors": read_errors,
        "first_row_keys": first_row_keys or [],
        "top_keys": keys.most_common(30),
        "top_statuses": statuses.most_common(50),
        "scan_truncated": max_rows is not None and rows >= max_rows,
    }


def _retired_label_status(
    files: list[Path],
    route_dir: Path,
    *,
    manifest_authority: set[str],
    active_broad_prefix: str | None,
    max_file_bytes: int = 1_000_000,
    max_total_bytes: int = 5_000_000,
    scan_large_files: bool = False,
) -> dict[str, Any]:
    retired_markers = {
        "legacy_result_label": "NO_" "PROMOTION" "_VERDICT",
        "legacy_source_flag": "validation" "_safe",
        "legacy_outcome_flag": "outcome" "_review" "_opened",
        "legacy_runtime_flag": "live" "_effect",
    }
    found_markers: set[str] = set()
    scanned_bytes = 0
    skipped_large = 0
    skipped_after_cap = 0
    skipped_superseded_generated = 0
    for path in files:
        if path.suffix.lower() not in {".md", ".txt", ".py"}:
            continue
        if _is_superseded_generated_replay_artifact(
            path,
            route_dir,
            manifest_authority=manifest_authority,
            active_broad_prefix=active_broad_prefix,
        ):
            skipped_superseded_generated += 1
            continue
        size = path.stat().st_size
        if not scan_large_files and size > max_file_bytes:
            skipped_large += 1
            continue
        if not scan_large_files and scanned_bytes + size > max_total_bytes:
            skipped_after_cap += 1
            continue
        try:
            for line in iter_text_lines_with_retries(path):
                for name, marker in retired_markers.items():
                    if marker in line:
                        found_markers.add(name)
        except OSError:
            continue
        scanned_bytes += size
    checks = {name: name not in found_markers for name in retired_markers}
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "present": [name for name, passed in checks.items() if not passed],
        "scanned_bytes": scanned_bytes,
        "skipped_large_file_count": skipped_large,
        "skipped_after_total_cap_count": skipped_after_cap,
        "skipped_superseded_generated_count": skipped_superseded_generated,
    }


def audit_route(
    route_dir: Path,
    max_jsonl_rows: int | None,
    *,
    max_json_bytes: int = 1_000_000,
    max_jsonl_file_bytes: int = 10_000_000,
    allow_giant_jsonl: bool = False,
    profile: str = "standard",
    require_next_prompt: bool = False,
    require_saturation: bool = False,
) -> dict[str, Any]:
    if profile not in REQUIRED_BY_PROFILE:
        raise ValueError(f"unknown profile: {profile}")
    files = iter_files(route_dir)
    categories = classify_files(files, route_dir)
    manifest_authority, active_broad_prefix, active_broad_tag = _load_manifest_authority(route_dir)
    required_categories = list(REQUIRED_BY_PROFILE[profile])
    if require_next_prompt and "next_prompt_or_starter" not in required_categories:
        required_categories.append("next_prompt_or_starter")
    if require_saturation and "saturation_or_self_red_team" not in required_categories:
        required_categories.append("saturation_or_self_red_team")
    missing_required = [
        category
        for category in required_categories
        if not categories.get(category)
    ]
    missing_warnings = [
        category
        for category in WARNING_BY_PROFILE.get(profile, ())
        if not categories.get(category)
    ]
    jsonl_files = sorted(path for path in files if path.suffix.lower() == ".jsonl")
    json_files = sorted(path for path in files if path.suffix.lower() == ".json")
    json_parse_errors: list[dict[str, str]] = []
    json_zero_byte_errors: list[dict[str, str]] = []
    json_files_skipped_large: list[dict[str, Any]] = []
    json_files_skipped_superseded_broad: list[dict[str, Any]] = []
    json_files_skipped_superseded_generated: list[dict[str, Any]] = []
    for path in json_files:
        if _is_superseded_broad_replay_artifact(
            path,
            route_dir,
            manifest_authority=manifest_authority,
            active_broad_prefix=active_broad_prefix,
        ):
            json_files_skipped_superseded_broad.append(
                {
                    "path": path.relative_to(route_dir).as_posix(),
                    "reason": "superseded broad replay artifact not pinned by OUTPUT_MANIFEST.json",
                }
            )
            continue
        if _is_superseded_generated_replay_artifact(
            path,
            route_dir,
            manifest_authority=manifest_authority,
            active_broad_prefix=active_broad_prefix,
        ):
            json_files_skipped_superseded_generated.append(
                {
                    "path": path.relative_to(route_dir).as_posix(),
                    "reason": "superseded generated replay artifact not pinned by OUTPUT_MANIFEST.json",
                }
            )
            continue
        size = path.stat().st_size
        if size == 0:
            json_zero_byte_errors.append(
                {
                    "path": path.relative_to(route_dir).as_posix(),
                    "error": "zero-byte JSON artifact",
                }
            )
            continue
        if size > max_json_bytes:
            json_files_skipped_large.append(
                {
                    "path": path.relative_to(route_dir).as_posix(),
                    "bytes": size,
                    "reason": f"exceeds max_json_bytes={max_json_bytes}",
                }
            )
            continue
        try:
            json.loads(read_text_with_retries(path))
        except json.JSONDecodeError as exc:
            json_parse_errors.append(
                {
                    "path": path.relative_to(route_dir).as_posix(),
                    "error": str(exc),
                }
            )
    jsonl_files_to_scan = []
    jsonl_files_skipped_large: list[dict[str, Any]] = []
    jsonl_files_skipped_superseded_broad: list[dict[str, Any]] = []
    jsonl_files_skipped_superseded_generated: list[dict[str, Any]] = []
    for path in jsonl_files:
        if _is_superseded_broad_replay_artifact(
            path,
            route_dir,
            manifest_authority=manifest_authority,
            active_broad_prefix=active_broad_prefix,
        ):
            jsonl_files_skipped_superseded_broad.append(
                {
                    "path": path.relative_to(route_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "reason": "superseded broad replay artifact not pinned by OUTPUT_MANIFEST.json",
                }
            )
            continue
        if _is_superseded_generated_replay_artifact(
            path,
            route_dir,
            manifest_authority=manifest_authority,
            active_broad_prefix=active_broad_prefix,
        ):
            jsonl_files_skipped_superseded_generated.append(
                {
                    "path": path.relative_to(route_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "reason": "superseded generated replay artifact not pinned by OUTPUT_MANIFEST.json",
                }
            )
            continue
        size = path.stat().st_size
        if size > max_jsonl_file_bytes and not allow_giant_jsonl:
            jsonl_files_skipped_large.append(
                {
                    "path": path.relative_to(route_dir).as_posix(),
                    "bytes": size,
                    "reason": f"exceeds max_jsonl_file_bytes={max_jsonl_file_bytes}",
                }
            )
            continue
        jsonl_files_to_scan.append(path)
        if max_jsonl_rows is not None and len(jsonl_files_to_scan) >= 20:
            break
    jsonl_scans = [scan_jsonl(path, max_jsonl_rows) for path in jsonl_files_to_scan]
    jsonl_parse_error_count = sum(int(scan["parse_errors"]) for scan in jsonl_scans)
    jsonl_read_errors = [
        {
            "path": Path(scan["path"]).relative_to(route_dir).as_posix(),
            "errors": scan.get("read_errors", []),
            "rows_scanned_before_error": scan.get("rows_scanned", 0),
        }
        for scan in jsonl_scans
        if scan.get("read_errors")
    ]
    jsonl_full_scan_incomplete = bool(
        max_jsonl_rows is None and jsonl_files_skipped_large and not allow_giant_jsonl
    )
    large_files = [
        {
            "path": path.relative_to(route_dir).as_posix(),
            "bytes": path.stat().st_size,
        }
        for path in files
        if path.stat().st_size >= 10 * 1024 * 1024
    ]
    retired_labels = _retired_label_status(
        files,
        route_dir,
        manifest_authority=manifest_authority,
        active_broad_prefix=active_broad_prefix,
        scan_large_files=allow_giant_jsonl and max_jsonl_rows is None,
    )
    hard_failures = bool(
        missing_required
        or json_zero_byte_errors
        or json_parse_errors
        or jsonl_parse_error_count
        or jsonl_read_errors
        or jsonl_full_scan_incomplete
        or not retired_labels["ok"]
    )
    return {
        "route_dir": str(route_dir),
        "profile": profile,
        "ok": not hard_failures,
        "missing_required": missing_required,
        "missing_warnings": missing_warnings,
        "file_count": len(files),
        "json_count": len(json_files),
        "json_zero_byte_error_count": len(json_zero_byte_errors),
        "json_zero_byte_errors": json_zero_byte_errors,
        "json_parse_error_count": len(json_parse_errors),
        "json_parse_errors": json_parse_errors,
        "json_files_skipped_large_count": len(json_files_skipped_large),
        "json_files_skipped_large": json_files_skipped_large[:50],
        "json_files_skipped_superseded_broad_count": len(json_files_skipped_superseded_broad),
        "json_files_skipped_superseded_broad": json_files_skipped_superseded_broad[:50],
        "json_files_skipped_superseded_generated_count": len(json_files_skipped_superseded_generated),
        "json_files_skipped_superseded_generated": json_files_skipped_superseded_generated[:50],
        "json_parse_note": (
            "large JSON files are inventoried but not parsed by this lightweight guardrail; "
            "raise --max-json-bytes for a full parse audit"
            if json_files_skipped_large
            else "all current-authority JSON files were within the parse byte cap"
        ),
        "active_broad_quality_parity_prefix": active_broad_prefix,
        "active_broad_quality_parity_tag": active_broad_tag,
        "jsonl_count": len(jsonl_files),
        "jsonl_files_scanned": len(jsonl_files_to_scan),
        "jsonl_files_unscanned": len(jsonl_files) - len(jsonl_files_to_scan),
        "jsonl_files_skipped_large_count": len(jsonl_files_skipped_large),
        "jsonl_files_skipped_large": jsonl_files_skipped_large[:50],
        "jsonl_files_skipped_superseded_broad_count": len(jsonl_files_skipped_superseded_broad),
        "jsonl_files_skipped_superseded_broad": jsonl_files_skipped_superseded_broad[:50],
        "jsonl_files_skipped_superseded_generated_count": len(jsonl_files_skipped_superseded_generated),
        "jsonl_files_skipped_superseded_generated": jsonl_files_skipped_superseded_generated[:50],
        "jsonl_full_scan_incomplete": jsonl_full_scan_incomplete,
        "jsonl_parse_error_count": jsonl_parse_error_count,
        "jsonl_read_error_count": len(jsonl_read_errors),
        "jsonl_read_errors": jsonl_read_errors,
        "large_files": large_files,
        "retired_label_status": retired_labels,
        "artifact_categories": categories,
        "jsonl_scans": jsonl_scans,
        "jsonl_scan_note": (
            "all jsonl files under the byte cap scanned"
            if max_jsonl_rows is None and not jsonl_files_skipped_large
            else (
                "JSONL scan respects the row and byte caps; use --allow-giant-jsonl "
                "with --full-jsonl to read ledgers above the byte cap"
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route_dir", help="Route directory to audit")
    parser.add_argument(
        "--full-jsonl",
        action="store_true",
        help="Scan complete JSONL files instead of the default row cap.",
    )
    parser.add_argument(
        "--max-jsonl-rows",
        type=int,
        default=20000,
        help="Rows to scan per JSONL file unless --full-jsonl is set.",
    )
    parser.add_argument(
        "--max-json-bytes",
        type=int,
        default=1_000_000,
        help="Maximum JSON file size to fully parse in the lightweight guardrail.",
    )
    parser.add_argument(
        "--max-jsonl-file-bytes",
        type=int,
        default=10_000_000,
        help="Maximum JSONL file size to open in the lightweight guardrail.",
    )
    parser.add_argument(
        "--allow-giant-jsonl",
        action="store_true",
        help=(
            "Allow JSONL files above --max-jsonl-file-bytes to be opened. "
            "Use only for intentionally bounded giant-ledger audits."
        ),
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Return exit code 0 even if required artifact classes are missing.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(REQUIRED_BY_PROFILE),
        default="standard",
        help="Route artifact profile to apply.",
    )
    parser.add_argument(
        "--require-next-prompt",
        action="store_true",
        help="Require a next prompt/starter artifact even if the selected profile only warns.",
    )
    parser.add_argument(
        "--require-saturation",
        action="store_true",
        help="Require saturation/self-red-team artifacts.",
    )
    args = parser.parse_args()

    route_dir = Path(args.route_dir)
    if not route_dir.exists() or not route_dir.is_dir():
        raise SystemExit(f"route_dir does not exist or is not a directory: {route_dir}")

    max_rows = None if args.full_jsonl else args.max_jsonl_rows
    report = audit_route(
        route_dir,
        max_rows,
        max_json_bytes=args.max_json_bytes,
        max_jsonl_file_bytes=args.max_jsonl_file_bytes,
        allow_giant_jsonl=args.allow_giant_jsonl,
        profile=args.profile,
        require_next_prompt=args.require_next_prompt,
        require_saturation=args.require_saturation,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] or args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
