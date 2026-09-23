"""Build local-only MT5 cache preservation artifacts.

This route reads local MT5 filesystem evidence only. It does not import MT5,
connect to a broker, call paid APIs, print credentials, or start runtime code.
The large archive is written outside the repository.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "vnext_mt5_local_cache_preservation_2026_06_01"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
PREVIOUS_ROUTE_DIR = REPO_ROOT / "research" / "operations" / "vnext_compliant_vps_data_preservation_broker_portability_2026_06_01"

ACTIVE_TERMINAL_ID = "D0E8209F77C8CF37AD8BF550E51FF075"
TERMINAL_ROOT = Path(r"C:\Users\MSI\AppData\Roaming\MetaQuotes\Terminal")
ACTIVE_TERMINAL_ROOT = TERMINAL_ROOT / ACTIVE_TERMINAL_ID
PROGRAM_FILES_ROOT = Path(r"C:\Program Files\MetaTrader 5")
ARCHIVE_DIR = Path(r"C:\Users\MSI\Documents\GTOS_MT5_LOCAL_PRESERVATION_2026_06_01")
ARCHIVE_PATH = ARCHIVE_DIR / "GTOS_MT5_LOCAL_PRESERVATION_2026_06_01.tar.gz"

LIVE_CONTEXT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/repo_cleanup_and_staleness_policy.md",
    ".context/00_core/vnext_absolute_moonshot_vision_and_limitations.md",
]

PREVIOUS_ROUTE_FILES = [
    "OFFICIAL_redacted_account_SOURCE_INDEX.json",
    "LOCAL_EVIDENCE_COVERAGE_SUMMARY.json",
    "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl",
    "BROKER_PORTABILITY_MAP.json",
    "BROKER_PORTABILITY_GAP_LEDGER.jsonl",
    "COMPLETION_AUDIT.json",
    "VERIFICATION_RESULT.json",
]

MARKET_HISTORY_EXTENSIONS = {".hcc"}
BAR_CACHE_EXTENSIONS = {".hc"}
TICK_CACHE_EXTENSIONS = {".tkc"}
TEXT_EXTENSIONS = {".log", ".jsonl", ".json", ".txt", ".csv", ".ini", ".set", ".mq5", ".mqh", ".mqproj"}
SOURCE_CODE_EXTENSIONS = {".mq5", ".mqh", ".mqproj", ".ex5", ".dll", ".hlsl", ".cl", ".js", ".bmp", ".ico"}
PROGRAM_INSTALL_EXTENSIONS = {".exe", ".dll", ".dat", ".ini", ".ico", ".bmp", ".txt", ".mqh", ".mq5", ".ex5", ".json"}
TIMEFRAME_NAMES = {
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "M10",
    "M12",
    "M15",
    "M20",
    "M30",
    "H1",
    "H2",
    "H3",
    "H4",
    "H6",
    "H8",
    "H12",
    "D1",
    "DAILY",
    "W1",
    "MN1",
}
EVIDENCE_ROLES_ARCHIVED = {
    "market_history",
    "tick_cache",
    "bar_cache",
    "broker_server_metadata",
    "terminal_logs",
    "ea_runtime_logs",
    "mql5_files_evidence",
    "source_runtime_code",
    "program_install_reproducibility",
    "broker_lifecycle_local_cache",
    "common_files_evidence",
}
SENSITIVE_NAME_PARTS = {
    "account",
    "accounts",
    "auth",
    "community",
    "credential",
    "credentials",
    "key",
    "login",
    "password",
    "secret",
    "token",
}
CONFIG_SENSITIVE_DIRS = {"config", "profiles", "presets"}
TEMP_CACHE_DIRS = {"temp", "cache"}


@dataclass(frozen=True)
class SourceRoot:
    tag: str
    path: Path
    purpose: str


SOURCE_ROOTS = [
    SourceRoot("terminal_roaming", TERMINAL_ROOT, "complete MetaQuotes roaming terminal root"),
    SourceRoot("active_terminal", ACTIVE_TERMINAL_ROOT, "active MT5 terminal instance cache"),
    SourceRoot("program_files_mt5", PROGRAM_FILES_ROOT, "MT5 install evidence for reproducibility"),
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="microseconds") + "Z"


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def jsonl_write(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path, chunk_size: int = 1024 * 1024 * 8) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()


def git_head() -> dict[str, str]:
    try:
        full = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
        subject = subprocess.check_output(["git", "log", "-1", "--format=%s"], cwd=REPO_ROOT, text=True).strip()
    except Exception as exc:  # pragma: no cover - defensive path
        return {"head": "unavailable", "head_short": "unavailable", "head_subject": f"git_error:{exc}"}
    return {"head": full, "head_short": full[:9], "head_subject": subject}


def get_c_drive_free_bytes() -> int | None:
    try:
        usage = shutil.disk_usage("C:\\")
        return int(usage.free)
    except OSError:
        return None


def normalize_parts(path: Path) -> list[str]:
    return [part.lower() for part in path.parts]


def matched_roots(path: Path, roots: Iterable[SourceRoot] = SOURCE_ROOTS) -> list[SourceRoot]:
    matches = []
    path_s = str(path).lower()
    for root in roots:
        root_s = str(root.path).lower()
        if path_s == root_s or path_s.startswith(root_s.rstrip("\\/") + os.sep.lower()):
            matches.append(root)
    return sorted(matches, key=lambda item: len(str(item.path)), reverse=True)


def best_root(path: Path, roots: Iterable[SourceRoot] = SOURCE_ROOTS) -> SourceRoot | None:
    matches = matched_roots(path, roots)
    return matches[0] if matches else None


def root_relative(path: Path, root: SourceRoot) -> str:
    try:
        rel = path.relative_to(root.path)
    except ValueError:
        rel = Path(path.name)
    return rel.as_posix()


def archive_member_path(path: Path) -> str:
    root = best_root(path)
    if root is None:
        return "unmatched/" + path.name
    return f"{root.tag}/{root_relative(path, root)}"


def is_sensitive_by_name(path: Path) -> bool:
    name = path.name.lower()
    stem = path.stem.lower()
    parts = set(normalize_parts(path))
    if parts & CONFIG_SENSITIVE_DIRS:
        return True
    if stem in {"accounts", "community", "terminal", "settings", "common", "servers"} and path.suffix.lower() in {".dat", ".ini"}:
        return True
    return any(part in name for part in SENSITIVE_NAME_PARTS)


def infer_server_symbol(path: Path) -> tuple[str | None, str | None]:
    parts = list(path.parts)
    lower = [part.lower() for part in parts]
    if "bases" in lower:
        bases_idx = lower.index("bases")
        server = parts[bases_idx + 1] if bases_idx + 2 < len(parts) else None
        for family in ("history", "ticks"):
            if family in lower:
                idx = lower.index(family)
                symbol = parts[idx + 1] if idx + 1 < len(parts) else None
                return server, symbol
        return server, None
    if "mql5" in lower and "files" in lower:
        stem = path.stem
        if stem.startswith("agent_signals_"):
            return None, stem.replace("agent_signals_", "", 1)
    return None, None


def infer_timeframe(path: Path) -> str | None:
    ext = path.suffix.lower()
    stem = path.stem.upper()
    if ext == ".tkc":
        return "TICK_MONTH"
    if path.name.lower() == "ticks.dat":
        return "TICK_METADATA"
    if ext == ".hcc":
        return "M1_PACKED_YEAR"
    if ext == ".hc":
        if stem == "DAILY":
            return "D1"
        if stem in TIMEFRAME_NAMES:
            return stem
    return None


def infer_date_window(path: Path) -> tuple[str | None, str | None, str]:
    """Infer dates from names/paths only; never reads binary cache content."""
    ext = path.suffix.lower()
    stem = path.stem
    if ext == ".hcc" and stem.isdigit() and len(stem) == 4:
        year = int(stem)
        return f"{year:04d}-01-01", f"{year:04d}-12-31", "filename_year"
    if ext == ".tkc" and stem.isdigit() and len(stem) == 6:
        year = int(stem[:4])
        month = int(stem[4:])
        if 1 <= month <= 12:
            last_day = calendar.monthrange(year, month)[1]
            return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}", "filename_year_month"
    if path.suffix.lower() in TEXT_EXTENSIONS:
        digits = "".join(ch if ch.isdigit() else " " for ch in path.stem).split()
        for item in digits:
            if len(item) == 8:
                try:
                    parsed = dt.datetime.strptime(item, "%Y%m%d").date().isoformat()
                    return parsed, parsed, "filename_yyyymmdd"
                except ValueError:
                    continue
    return None, None, "not_inferable_without_parsing_binary_or_file_content"


def classify_path(path: Path) -> dict[str, Any]:
    parts = set(normalize_parts(path))
    ext = path.suffix.lower()
    name = path.name.lower()
    server, symbol = infer_server_symbol(path)
    timeframe = infer_timeframe(path)
    first_date, last_date, date_source = infer_date_window(path)
    sensitive = is_sensitive_by_name(path)
    role = "irrelevant"
    archive_decision = "exclude_non_evidence"
    exclusion_reason = "not_a_required_mt5_market_history_runtime_or_reproducibility_surface"

    if sensitive:
        role = "credential_sensitive" if any(part in name for part in SENSITIVE_NAME_PARTS) else "config_sensitive"
        archive_decision = "exclude_sensitive"
        exclusion_reason = "credential_or_config_sensitive_file_excluded_without_content_capture"
    elif "program files" in str(path).lower() and best_root(path) and best_root(path).tag == "program_files_mt5":
        role = "program_install_reproducibility" if ext in PROGRAM_INSTALL_EXTENSIONS or not ext else "program_install_reproducibility"
        archive_decision = "include_archive"
        exclusion_reason = None
    elif "temp" in parts:
        role = "temp_cache"
        archive_decision = "exclude_non_evidence"
        exclusion_reason = "temporary_cache_not_required_for_market_history_runtime_preservation"
    elif "bases" in parts:
        if ext in MARKET_HISTORY_EXTENSIONS:
            role = "market_history"
        elif ext in BAR_CACHE_EXTENSIONS:
            role = "bar_cache"
        elif ext in TICK_CACHE_EXTENSIONS or name == "ticks.dat":
            role = "tick_cache"
        elif "trades" in parts:
            role = "broker_lifecycle_local_cache"
        elif ext == ".welcome" or "symbols" in parts or "news" in parts or "mail" in parts or "subscriptions" in parts or ext in {".hyb", ".baf", ".baj"}:
            role = "broker_server_metadata"
        elif ext == ".dat":
            role = "config_sensitive"
            archive_decision = "exclude_sensitive"
            exclusion_reason = "terminal_chart_or_ui_config_dat_under_bases_excluded"
        else:
            role = "broker_server_metadata"
        if role in EVIDENCE_ROLES_ARCHIVED:
            archive_decision = "include_archive"
            exclusion_reason = None
    elif "logs" in parts and "mql5" in parts:
        role = "ea_runtime_logs"
        archive_decision = "include_archive"
        exclusion_reason = None
    elif "logs" in parts:
        role = "terminal_logs"
        archive_decision = "include_archive"
        exclusion_reason = None
    elif "mql5" in parts and "files" in parts:
        role = "mql5_files_evidence"
        archive_decision = "include_archive"
        exclusion_reason = None
    elif "mql5" in parts and ext in SOURCE_CODE_EXTENSIONS:
        role = "source_runtime_code"
        archive_decision = "include_archive"
        exclusion_reason = None
    elif "common" in parts and "files" in parts:
        role = "common_files_evidence"
        archive_decision = "include_archive"
        exclusion_reason = None
    elif ext in {".set", ".ini"}:
        role = "config_sensitive"
        archive_decision = "exclude_sensitive"
        exclusion_reason = "parameter_or_ini_config_excluded_without_content_capture"
    elif "tester" in parts:
        role = "temp_cache"
        archive_decision = "exclude_non_evidence"
        exclusion_reason = "strategy_tester_cache_not_required_for_live_market_history_runtime_preservation"

    return {
        "evidence_role": role,
        "archive_decision": archive_decision,
        "exclusion_reason": exclusion_reason,
        "server_or_broker_folder": server,
        "symbol": symbol,
        "timeframe": timeframe,
        "first_date": first_date,
        "last_date": last_date,
        "date_inference_source": date_source,
        "extension": ext or "<none>",
        "sensitive": archive_decision == "exclude_sensitive",
    }


def file_row(path: Path, stat_result: os.stat_result, scan_roots: list[SourceRoot]) -> dict[str, Any]:
    classification = classify_path(path)
    path_s = str(path)
    row: dict[str, Any] = {
        "schema_version": "mt5_local_cache_inventory_v1",
        "route_id": ROUTE_ID,
        "file_name": path.name,
        "extension": classification["extension"],
        "size_bytes": int(stat_result.st_size),
        "modified_time_utc": dt.datetime.fromtimestamp(stat_result.st_mtime, tz=dt.timezone.utc)
        .replace(tzinfo=None)
        .isoformat(timespec="microseconds")
        + "Z",
        "scan_root_tags": [root.tag for root in scan_roots],
        "scan_root_paths": [str(root.path) for root in scan_roots],
        "path_sha256": sha256_text(path_s.lower()),
        **classification,
    }
    if classification["sensitive"]:
        row["path"] = None
        row["redacted_path"] = f"REDACTED_PATH_SHA256:{row['path_sha256']}"
        row["archive_member_path"] = None
    else:
        row["path"] = path_s
        row["redacted_path"] = None
        row["archive_member_path"] = archive_member_path(path) if classification["archive_decision"] == "include_archive" else None
    return row


def enumerate_local_mt5_files(roots: Iterable[SourceRoot] = SOURCE_ROOTS) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_key: dict[str, dict[str, Any]] = {}
    blocked: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    roots = list(roots)
    for root in roots:
        if not root.path.exists():
            missing.append(
                {
                    "schema_version": "mt5_missing_root_v1",
                    "route_id": ROUTE_ID,
                    "root_tag": root.tag,
                    "path": str(root.path),
                    "purpose": root.purpose,
                    "status": "missing",
                }
            )
            continue
        for dirpath, dirnames, filenames in os.walk(root.path, topdown=True, followlinks=False):
            dirnames[:] = [name for name in dirnames if not (Path(dirpath) / name).is_symlink()]
            for filename in filenames:
                path = Path(dirpath) / filename
                key = str(path).lower()
                if key in rows_by_key:
                    matched = matched_roots(path, roots)
                    rows_by_key[key]["scan_root_tags"] = sorted(set(rows_by_key[key]["scan_root_tags"]) | {r.tag for r in matched})
                    rows_by_key[key]["scan_root_paths"] = sorted(set(rows_by_key[key]["scan_root_paths"]) | {str(r.path) for r in matched})
                    continue
                try:
                    stat_result = path.stat()
                except OSError as exc:
                    blocked.append(
                        {
                            "schema_version": "mt5_unreadable_file_v1",
                            "route_id": ROUTE_ID,
                            "path_sha256": sha256_text(str(path).lower()),
                            "path": str(path),
                            "error": repr(exc),
                            "status": "unreadable_stat",
                        }
                    )
                    continue
                rows_by_key[key] = file_row(path, stat_result, matched_roots(path, roots))
    return list(rows_by_key.values()), blocked, missing


def read_previous_route_summary() -> dict[str, Any]:
    coverage = read_json(PREVIOUS_ROUTE_DIR / "LOCAL_EVIDENCE_COVERAGE_SUMMARY.json", {})
    official = read_json(PREVIOUS_ROUTE_DIR / "OFFICIAL_redacted_account_SOURCE_INDEX.json", {})
    missing_rows = list(iter_jsonl(PREVIOUS_ROUTE_DIR / "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl"))
    return {
        "previous_route_dir": str(PREVIOUS_ROUTE_DIR.relative_to(REPO_ROOT)),
        "previous_route_exists": PREVIOUS_ROUTE_DIR.exists(),
        "official_source_count": len(official.get("entries", [])) if isinstance(official, dict) else 0,
        "previous_external_mt5_presence_rows": len(coverage.get("external_mt5_presence_rows", [])) if isinstance(coverage, dict) else 0,
        "previous_inventory_rows": coverage.get("inventory_rows") if isinstance(coverage, dict) else None,
        "previous_required_roots": coverage.get("required_root_summaries", []) if isinstance(coverage, dict) else [],
        "previous_timeframe_coverage_by_symbol": coverage.get("timeframe_coverage_by_symbol", {}) if isinstance(coverage, dict) else {},
        "previous_missing_export_requirement_rows": len(missing_rows),
    }


def summarize_inventory(rows: list[dict[str, Any]], blocked: list[dict[str, Any]], missing: list[dict[str, Any]]) -> dict[str, Any]:
    role_counts: dict[str, int] = {}
    role_bytes: dict[str, int] = {}
    ext_counts: dict[str, int] = {}
    server_counts: dict[str, int] = {}
    symbol_counts: dict[str, int] = {}
    timeframe_by_symbol: dict[str, set[str]] = {}
    bases_ext_counts: dict[str, int] = {}
    for row in rows:
        role = row["evidence_role"]
        role_counts[role] = role_counts.get(role, 0) + 1
        role_bytes[role] = role_bytes.get(role, 0) + int(row["size_bytes"])
        ext = row["extension"]
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
        if "\\bases\\" in (row.get("path") or "").lower() or "/bases/" in (row.get("path") or "").lower():
            bases_ext_counts[ext] = bases_ext_counts.get(ext, 0) + 1
        server = row.get("server_or_broker_folder")
        symbol = row.get("symbol")
        timeframe = row.get("timeframe")
        if server:
            server_counts[server] = server_counts.get(server, 0) + 1
        if symbol:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            if timeframe:
                timeframe_by_symbol.setdefault(symbol, set()).add(timeframe)
    include_rows = [row for row in rows if row["archive_decision"] == "include_archive"]
    sensitive_rows = [row for row in rows if row["archive_decision"] == "exclude_sensitive"]
    non_evidence_rows = [row for row in rows if row["archive_decision"] == "exclude_non_evidence"]
    return {
        "schema_version": "mt5_local_cache_coverage_summary_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "source_roots": [
            {"tag": root.tag, "path": str(root.path), "exists": root.path.exists(), "purpose": root.purpose}
            for root in SOURCE_ROOTS
        ],
        "source_file_count": len(rows),
        "source_bytes": sum(int(row["size_bytes"]) for row in rows),
        "archive_candidate_file_count": len(include_rows),
        "archive_candidate_bytes": sum(int(row["size_bytes"]) for row in include_rows),
        "sensitive_excluded_file_count": len(sensitive_rows),
        "sensitive_excluded_bytes": sum(int(row["size_bytes"]) for row in sensitive_rows),
        "non_evidence_excluded_file_count": len(non_evidence_rows),
        "non_evidence_excluded_bytes": sum(int(row["size_bytes"]) for row in non_evidence_rows),
        "unreadable_row_count": len(blocked),
        "missing_root_count": len(missing),
        "evidence_role_counts": dict(sorted(role_counts.items())),
        "evidence_role_bytes": dict(sorted(role_bytes.items())),
        "extension_counts": dict(sorted(ext_counts.items())),
        "bases_extension_counts": dict(sorted(bases_ext_counts.items())),
        "server_or_broker_folder_counts": dict(sorted(server_counts.items())),
        "symbol_file_counts": dict(sorted(symbol_counts.items())),
        "timeframe_coverage_by_symbol": {symbol: sorted(values) for symbol, values in sorted(timeframe_by_symbol.items())},
        "bases_required_extension_classification": {
            ext: bases_ext_counts.get(ext, 0) for ext in [".hcc", ".hc", ".tkc", ".dat", ".welcome"]
        },
    }


def make_archive(rows: list[dict[str, Any]], *, force: bool, compresslevel: int, progress_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    include_rows = [row for row in rows if row["archive_decision"] == "include_archive"]
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    if ARCHIVE_PATH.exists() and not force:
        raise SystemExit(f"Archive already exists; use --force-archive to replace: {ARCHIVE_PATH}")
    temp_path = ARCHIVE_PATH.with_name(ARCHIVE_PATH.name + ".tmp")
    if temp_path.exists():
        temp_path.unlink()
    blocked: list[dict[str, Any]] = []
    started = time.time()
    written_files = 0
    written_uncompressed_bytes = 0
    with tarfile.open(temp_path, mode="w:gz", compresslevel=compresslevel, dereference=False) as archive:
        for index, row in enumerate(include_rows, start=1):
            source = Path(row["path"])
            try:
                stat_before = source.stat()
                archive.add(source, arcname=row["archive_member_path"], recursive=False)
                written_files += 1
                written_uncompressed_bytes += int(stat_before.st_size)
            except OSError as exc:
                blocked.append(
                    {
                        "schema_version": "mt5_archive_blocker_v1",
                        "route_id": ROUTE_ID,
                        "path": str(source),
                        "path_sha256": row["path_sha256"],
                        "archive_member_path": row["archive_member_path"],
                        "evidence_role": row["evidence_role"],
                        "error": repr(exc),
                        "status": "archive_read_failed",
                    }
                )
            if index == 1 or index == len(include_rows) or index % 25 == 0:
                json_dump(
                    progress_path,
                    {
                        "archive_path": str(ARCHIVE_PATH),
                        "archive_temp_path": str(temp_path),
                        "candidate_files": len(include_rows),
                        "processed_candidates": index,
                        "written_files": written_files,
                        "written_uncompressed_bytes": written_uncompressed_bytes,
                        "blocked_files": len(blocked),
                        "elapsed_seconds": round(time.time() - started, 1),
                        "updated_at_utc": utc_now(),
                    },
                )
    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()
    temp_path.replace(ARCHIVE_PATH)
    archive_sha = sha256_file(ARCHIVE_PATH)
    archive_stat = ARCHIVE_PATH.stat()
    manifest = {
        "schema_version": "mt5_archive_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "archive_path": str(ARCHIVE_PATH),
        "archive_storage": "outside_git_streaming_tar_gzip",
        "archive_compression": "gzip_tar_stream",
        "archive_compresslevel": compresslevel,
        "archive_bytes": int(archive_stat.st_size),
        "archive_sha256": archive_sha,
        "archive_created_at_utc": dt.datetime.fromtimestamp(archive_stat.st_mtime, tz=dt.timezone.utc)
        .replace(tzinfo=None)
        .isoformat(timespec="microseconds")
        + "Z",
        "archive_candidate_file_count": len(include_rows),
        "archive_candidate_bytes": sum(int(row["size_bytes"]) for row in include_rows),
        "archived_file_count_from_write": written_files,
        "archived_uncompressed_bytes_from_write": written_uncompressed_bytes,
        "archive_blocker_count": len(blocked),
    }
    return manifest, blocked


def list_archive(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with tarfile.open(path, mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            rows.append(
                {
                    "schema_version": "mt5_archive_listing_v1",
                    "route_id": ROUTE_ID,
                    "archive_member_path": member.name,
                    "size_bytes": int(member.size),
                    "modified_time_utc": dt.datetime.fromtimestamp(member.mtime, tz=dt.timezone.utc)
                    .replace(tzinfo=None)
                    .isoformat(timespec="microseconds")
                    + "Z",
                    "mode": oct(member.mode),
                }
            )
    return rows


def compare_repo_coverage(summary: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    repo_symbols = set((previous.get("previous_timeframe_coverage_by_symbol") or {}).keys())
    mt5_symbols = set(summary.get("symbol_file_counts", {}).keys())
    repo_timeframes = previous.get("previous_timeframe_coverage_by_symbol") or {}
    mt5_timeframes = summary.get("timeframe_coverage_by_symbol") or {}
    mt5_all_timeframes = sorted({tf for values in mt5_timeframes.values() for tf in values})
    repo_all_timeframes = sorted({tf for values in repo_timeframes.values() for tf in values})
    return {
        "schema_version": "mt5_repo_coverage_comparison_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "previous_route_dir": previous["previous_route_dir"],
        "previous_external_mt5_status": "presence_only_inventory_closed_by_this_followup_route",
        "repo_local_symbol_count": len(repo_symbols),
        "external_mt5_symbol_count": len(mt5_symbols),
        "symbols_added_by_external_mt5_cache": sorted(mt5_symbols - repo_symbols),
        "symbols_in_repo_not_in_external_mt5_cache": sorted(repo_symbols - mt5_symbols),
        "repo_local_timeframe_classes": repo_all_timeframes,
        "external_mt5_timeframe_classes": mt5_all_timeframes,
        "external_mt5_adds_broker_server_cache": summary["evidence_role_counts"].get("broker_server_metadata", 0) > 0,
        "external_mt5_adds_broker_lifecycle_local_cache": summary["evidence_role_counts"].get("broker_lifecycle_local_cache", 0) > 0,
        "external_mt5_adds_terminal_or_ea_runtime_logs": (
            summary["evidence_role_counts"].get("terminal_logs", 0)
            + summary["evidence_role_counts"].get("ea_runtime_logs", 0)
        )
        > 0,
        "external_mt5_adds_program_install_reproducibility": summary["evidence_role_counts"].get("program_install_reproducibility", 0) > 0,
        "interpretation": {
            "repo_local_data_state": "previous_route_already_preserved_repo_local_data_ticks_m1_and_research_outputs",
            "external_cache_increment": "external_mt5_cache_preserves_terminal_native_bases_ticks_history_broker_metadata_local_trades_cache_logs_mql5_files_and_install_evidence",
            "server_export_still_required": "full_current_account_history_symbol_specs_sessions_commissions_swaps_margin_tick_value_stop_freeze_spread_samples_and_any_server_history_not_cached_locally",
        },
    }


def remaining_export_requirements() -> list[dict[str, Any]]:
    requirements = [
        {
            "schema_version": "mt5_remaining_export_requirement_v1",
            "route_id": ROUTE_ID,
            "state": "unavailable_until_compliant_vps_read_only_export",
            "source_family": "broker_lifecycle_truth",
            "required_action": "export full account orders deals positions history from compliant non-restricted non-US MT5/VPS origin without order_send",
            "proof_required": "orders_deals_positions_jsonl_hash_manifest_and_read_only_export_log",
            "fields": ["orders", "deals", "positions", "commissions", "swaps", "close_reasons", "partial_close_lifecycle"],
        },
        {
            "schema_version": "mt5_remaining_export_requirement_v1",
            "route_id": ROUTE_ID,
            "state": "unavailable_until_compliant_vps_read_only_export",
            "source_family": "broker_symbol_geometry",
            "required_action": "export symbol_info and symbol_info_tick/session metadata for all 24 vNext symbols from compliant VPS",
            "proof_required": "per_symbol_symbol_info_jsonl_hash_manifest",
            "fields": [
                "contract_size",
                "tick_size",
                "tick_value",
                "point_value",
                "min_lot",
                "max_lot",
                "lot_step",
                "stop_level",
                "freeze_level",
                "sessions",
                "commissions",
                "swaps",
                "margin",
                "spread_samples",
            ],
        },
        {
            "schema_version": "mt5_remaining_export_requirement_v1",
            "route_id": ROUTE_ID,
            "state": "unavailable_until_compliant_vps_read_only_export",
            "source_family": "server_only_market_history",
            "required_action": "from compliant VPS, export any server-side history windows not present in local bases cache",
            "proof_required": "missing_window_report_plus_read_only_export_hash_manifest",
            "fields": ["server_history_gap_windows", "server_ticks_gap_windows", "symbol_alias_map"],
        },
    ]
    return requirements


def output_manifest() -> dict[str, Any]:
    rows = []
    for path in sorted(ROUTE_DIR.glob("*")):
        if path.is_dir():
            continue
        if path.name.startswith("archive_") and path.suffix == ".log":
            continue
        if path.name == "MT5_ARCHIVE_PROGRESS.json":
            continue
        if path.name in {"OUTPUT_MANIFEST.json", "VERIFICATION_RESULT.json", "COMPLETION_AUDIT.json"}:
            rows.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "bytes": path.stat().st_size,
                    "sha256": None,
                    "hash_status": "volatile_route_artifact_verified_by_parse_and_presence",
                }
            )
        else:
            rows.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "hash_status": "sha256",
                }
            )
    payload = {
        "schema_version": "mt5_local_cache_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "route_dir": str(ROUTE_DIR.relative_to(REPO_ROOT)),
        "files": rows,
        "large_archive_policy": "archive_outside_git_recorded_in_MT5_ARCHIVE_MANIFEST_json",
    }
    json_dump(ROUTE_DIR / "OUTPUT_MANIFEST.json", payload)
    return payload


def completion_audit(verification_ok: bool = False, issues: list[str] | None = None) -> dict[str, Any]:
    issues = issues or []
    payload = {
        "schema_version": "mt5_local_cache_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "git": git_head(),
        "evidence_class": "local_only_mt5_cache_inventory_archive_preservation",
        "forbidden_surface_attestation": {
            "broker_changing_action_by_this_route": False,
            "mt5_server_export_by_this_route": False,
            "live_runtime_started_by_this_route": False,
            "paid_api_or_vendor_call_by_this_route": False,
            "credential_print_or_change_by_this_route": False,
            "remote_push_by_this_route": False,
        },
        "context_files_read_after_preflight": LIVE_CONTEXT_FILES,
        "previous_route_read": str(PREVIOUS_ROUTE_DIR.relative_to(REPO_ROOT)),
        "archive_outside_git": str(ARCHIVE_PATH),
        "verification_ok": verification_ok,
        "verification_issue_count": len(issues),
        "can_mark_goal_complete": verification_ok and not issues,
        "requirements": [
            {"requirement": "external_mt5_cache_full_inventory", "status": "see_MT5_LOCAL_CACHE_INVENTORY"},
            {"requirement": "bases_full_classification", "status": "see_MT5_LOCAL_CACHE_COVERAGE_SUMMARY"},
            {"requirement": "one_archive_outside_git", "status": "see_MT5_ARCHIVE_MANIFEST"},
            {"requirement": "sensitive_exclusions_recorded", "status": "see_MT5_SENSITIVE_EXCLUSION_LEDGER"},
            {"requirement": "repo_vs_external_coverage_compared", "status": "see_MT5_REPO_COVERAGE_COMPARISON"},
            {"requirement": "remaining_vps_export_requirements_exact", "status": "see_MT5_REMAINING_VPS_EXPORT_REQUIREMENTS"},
            {"requirement": "route_verifier_ok_true", "status": "passed" if verification_ok else "pending"},
            {
                "requirement": "scoped_commit_with_codex_coauthor",
                "status": "verified_ready_for_final_scoped_commit",
                "note": "final commit hash is proven by git history outside this self-referential route artifact",
            },
        ],
        "issues": issues,
    }
    json_dump(ROUTE_DIR / "COMPLETION_AUDIT.json", payload)
    return payload


def build(args: argparse.Namespace) -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    previous = read_previous_route_summary()
    free_bytes = get_c_drive_free_bytes()
    rows, blocked, missing = enumerate_local_mt5_files()
    summary = summarize_inventory(rows, blocked, missing)
    summary["c_drive_free_bytes_before_archive"] = free_bytes
    summary["c_drive_free_gib_before_archive"] = round(free_bytes / (1024**3), 2) if free_bytes is not None else None
    summary["known_storage_facts_confirmation"] = {
        "terminal_root_gib": round(sum(int(row["size_bytes"]) for row in rows if "terminal_roaming" in row["scan_root_tags"]) / (1024**3), 2),
        "active_terminal_gib": round(sum(int(row["size_bytes"]) for row in rows if "active_terminal" in row["scan_root_tags"]) / (1024**3), 2),
        "program_files_mt5_gib": round(sum(int(row["size_bytes"]) for row in rows if "program_files_mt5" in row["scan_root_tags"]) / (1024**3), 2),
    }
    json_dump(
        ROUTE_DIR / "ROUTE_CONTEXT_ANCHOR.json",
        {
            "schema_version": "mt5_local_cache_route_context_anchor_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "git": git_head(),
            "context_files_read_after_preflight": LIVE_CONTEXT_FILES,
            "previous_route_dir": str(PREVIOUS_ROUTE_DIR.relative_to(REPO_ROOT)),
            "previous_route_files_read": PREVIOUS_ROUTE_FILES,
            "source_roots": [
                {"tag": root.tag, "path": str(root.path), "exists": root.path.exists(), "purpose": root.purpose}
                for root in SOURCE_ROOTS
            ],
            "archive_path": str(ARCHIVE_PATH),
            "forbidden_surfaces": {
                "live_broker_order_deal_position_action": False,
                "mt5_server_export_from_current_local_environment": False,
                "paid_api_vendor_call": False,
                "credential_printing_or_change": False,
                "remote_push": False,
            },
        },
    )
    jsonl_write(ROUTE_DIR / "MT5_LOCAL_CACHE_INVENTORY.jsonl", rows)
    jsonl_write(ROUTE_DIR / "MT5_UNREADABLE_OR_BLOCKED_LEDGER.jsonl", blocked)
    jsonl_write(ROUTE_DIR / "MT5_MISSING_ROOT_LEDGER.jsonl", missing)
    jsonl_write(ROUTE_DIR / "MT5_SENSITIVE_EXCLUSION_LEDGER.jsonl", [row for row in rows if row["archive_decision"] == "exclude_sensitive"])
    jsonl_write(ROUTE_DIR / "MT5_ARCHIVE_INCLUDE_LEDGER.jsonl", [row for row in rows if row["archive_decision"] == "include_archive"])
    json_dump(ROUTE_DIR / "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json", summary)
    comparison = compare_repo_coverage(summary, previous)
    json_dump(ROUTE_DIR / "MT5_REPO_COVERAGE_COMPARISON.json", comparison)
    jsonl_write(ROUTE_DIR / "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl", remaining_export_requirements())

    archive_manifest: dict[str, Any] | None = None
    archive_blockers: list[dict[str, Any]] = []
    if args.create_archive:
        archive_manifest, archive_blockers = make_archive(
            rows,
            force=args.force_archive,
            compresslevel=args.compresslevel,
            progress_path=ROUTE_DIR / "MT5_ARCHIVE_PROGRESS.json",
        )
        listing = list_archive(ARCHIVE_PATH)
        archive_manifest.update(
            {
                "archived_file_count": len(listing),
                "archived_uncompressed_bytes": sum(int(row["size_bytes"]) for row in listing),
                "archive_listing_path": str((ROUTE_DIR / "MT5_ARCHIVE_LISTING.jsonl").relative_to(REPO_ROOT)),
            }
        )
        json_dump(ROUTE_DIR / "MT5_ARCHIVE_MANIFEST.json", archive_manifest)
        jsonl_write(ROUTE_DIR / "MT5_ARCHIVE_LISTING.jsonl", listing)
        if archive_blockers:
            blocked.extend(archive_blockers)
            jsonl_write(ROUTE_DIR / "MT5_UNREADABLE_OR_BLOCKED_LEDGER.jsonl", blocked)
    elif (ROUTE_DIR / "MT5_ARCHIVE_MANIFEST.json").exists():
        archive_manifest = read_json(ROUTE_DIR / "MT5_ARCHIVE_MANIFEST.json")
    else:
        json_dump(
            ROUTE_DIR / "MT5_ARCHIVE_MANIFEST.json",
            {
                "schema_version": "mt5_archive_manifest_v1",
                "route_id": ROUTE_ID,
                "generated_at_utc": utc_now(),
                "archive_path": str(ARCHIVE_PATH),
                "status": "pending_create_archive",
            },
        )
        jsonl_write(ROUTE_DIR / "MT5_ARCHIVE_LISTING.jsonl", [])

    manifest = output_manifest()
    completion_audit(False, ["verification_not_run_yet"])
    result = {
        "route_dir": str(ROUTE_DIR.relative_to(REPO_ROOT)),
        "source_file_count": len(rows),
        "source_bytes": summary["source_bytes"],
        "archive_candidate_file_count": summary["archive_candidate_file_count"],
        "archive_candidate_bytes": summary["archive_candidate_bytes"],
        "sensitive_excluded_file_count": summary["sensitive_excluded_file_count"],
        "non_evidence_excluded_file_count": summary["non_evidence_excluded_file_count"],
        "unreadable_or_blocked_count": len(blocked),
        "missing_root_count": len(missing),
        "archive_path": str(ARCHIVE_PATH),
        "archive_bytes": archive_manifest.get("archive_bytes") if archive_manifest else None,
        "archive_sha256": archive_manifest.get("archive_sha256") if archive_manifest else None,
        "output_manifest_files": len(manifest["files"]),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-archive", action="store_true", help="Create the outside-git tar.gz archive.")
    parser.add_argument("--force-archive", action="store_true", help="Replace an existing route-named archive.")
    parser.add_argument("--compresslevel", type=int, default=1, choices=range(1, 10), help="gzip compression level for tar.gz.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    build(parse_args(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
