"""Storage-retention classification helpers for LTO-038.

Research/tooling only. This module audits repository storage pressure and
classifies files into retention classes. It never deletes files. Cleanup
allowance is limited to explicit temp/cache paths and remains a dry-run
recommendation unless a separate archival/deletion policy is approved.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "storage_retention_status_v1"
POLICY_VERSION = "storage_retention_policy_v1"

OK = "OK_STORAGE_RETENTION_DRY_RUN"
WARNING = "STORAGE_RETENTION_WARNING"
ACTION_REQUIRED = "STORAGE_RETENTION_ACTION_REQUIRED"

RAW_SOURCE = "RAW_SOURCE_PROTECTED"
EVIDENCE_LOG = "EVIDENCE_LOG_PROTECTED"
DERIVED_FEATURE = "DERIVED_FEATURE_PROTECTED"
REPORT = "REPORT_PROTECTED"
TEMP_CACHE = "TEMP_CACHE_DRY_RUN_DELETABLE"
LOG_ROTATABLE = "LOG_ROTATABLE_AFTER_ARCHIVE"
LOCK_FILE = "LOCK_FILE_RUNTIME_PROTECTED"
CODE_CONFIG = "CODE_CONFIG_PROTECTED"
OTHER_REVIEW = "OTHER_REVIEW_REQUIRED"

DEFAULT_WARNING_FREE_GB = 20.0
DEFAULT_WARNING_FREE_PCT = 10.0
DEFAULT_CRITICAL_FREE_GB = 5.0
DEFAULT_CRITICAL_FREE_PCT = 3.0

PROTECTED_ROOT_PREFIXES = (
    "data/raw",
    "data/ticks",
    "data/account_history",
    "data/historical",
    "data/historical_2022_2023",
    "data/historical_2026",
    "data/sierrachart_exports",
    "data/sierra_ohlcv_roots",
    "shadow_logs",
    "knowledge_base/trade_records",
    "research/program_control",
    "research/operations",
    ".context",
)

RAW_SOURCE_SUFFIXES = {".depth", ".scid", ".parquet", ".csv"}
REPORT_SUFFIXES = {".md", ".json", ".jsonl"}
CODE_CONFIG_SUFFIXES = {".py", ".ps1", ".bat", ".yaml", ".yml", ".toml", ".ini"}
TEMP_DIR_PREFIXES = (
    ".pytest",
    ".codex",
    "_codex",
    "_pytest",
    "pytest",
    "tmp",
    ".tmp",
    "codex_tmp",
    "tmp_pytest",
)
TEMP_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules"}


@dataclass(frozen=True)
class RetentionDecision:
    retention_class: str
    deletion_allowed: bool
    archive_required_before_delete: bool
    reason: str


def coerce_utc(value: datetime | None) -> datetime:
    now = value or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def is_within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _has_prefix(relative: str, prefixes: Iterable[str]) -> bool:
    normalized = relative.replace("\\", "/").strip("/")
    return any(normalized == prefix or normalized.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def _is_root_temp_dir(relative: str) -> bool:
    parts = relative.replace("\\", "/").strip("/").split("/")
    if not parts or not parts[0]:
        return False
    top = parts[0]
    if top in TEMP_DIR_NAMES:
        return True
    return any(top.startswith(prefix) for prefix in TEMP_DIR_PREFIXES)


def classify_path(path: Path, root: Path) -> RetentionDecision:
    if not is_within_root(path, root):
        return RetentionDecision(
            retention_class=OTHER_REVIEW,
            deletion_allowed=False,
            archive_required_before_delete=True,
            reason="outside workspace root",
        )
    relative = relpath(path, root)
    normalized = relative.replace("\\", "/").strip("/")
    name = path.name
    suffix = path.suffix.lower()

    if _is_root_temp_dir(normalized) or name in TEMP_DIR_NAMES or suffix in {".pyc", ".pyo", ".tmp"}:
        return RetentionDecision(
            retention_class=TEMP_CACHE,
            deletion_allowed=True,
            archive_required_before_delete=False,
            reason="explicit temp/cache allowlist",
        )
    if name.endswith(".lock") or "/.notification_queue_worker.lock" in normalized or "/.orchestrator_" in normalized:
        return RetentionDecision(
            retention_class=LOCK_FILE,
            deletion_allowed=False,
            archive_required_before_delete=False,
            reason="runtime lock file",
        )
    if normalized.startswith("shadow_logs/"):
        return RetentionDecision(
            retention_class=EVIDENCE_LOG,
            deletion_allowed=False,
            archive_required_before_delete=True,
            reason="append-only shadow evidence log",
        )
    if normalized.startswith("logs/") and suffix == ".log":
        return RetentionDecision(
            retention_class=LOG_ROTATABLE,
            deletion_allowed=False,
            archive_required_before_delete=True,
            reason="operator log; rotate/archive before removal",
        )
    if normalized.startswith("research/") or normalized.startswith(".context/") or suffix in REPORT_SUFFIXES:
        return RetentionDecision(
            retention_class=REPORT,
            deletion_allowed=False,
            archive_required_before_delete=True,
            reason="research/report artifact",
        )
    if _has_prefix(normalized, PROTECTED_ROOT_PREFIXES) or suffix in RAW_SOURCE_SUFFIXES:
        return RetentionDecision(
            retention_class=RAW_SOURCE,
            deletion_allowed=False,
            archive_required_before_delete=True,
            reason="raw source, market data, account history, or protected evidence root",
        )
    if normalized.startswith("src/") or normalized.startswith("scripts/") or normalized.startswith("tests/") or normalized.startswith("config/") or suffix in CODE_CONFIG_SUFFIXES:
        return RetentionDecision(
            retention_class=CODE_CONFIG,
            deletion_allowed=False,
            archive_required_before_delete=True,
            reason="code/config/test artifact",
        )
    return RetentionDecision(
        retention_class=OTHER_REVIEW,
        deletion_allowed=False,
        archive_required_before_delete=True,
        reason="not in deletion allowlist",
    )


def iter_files(root: Path, *, max_files: int = 100_000) -> Iterable[Path]:
    yielded = 0
    stack = [root]
    root_resolved = root.resolve()
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if entry.is_dir(follow_symlinks=False):
                        relative = relpath(path, root_resolved)
                        if path.name in EXCLUDED_DIRS:
                            continue
                        stack.append(path)
                    elif entry.is_file(follow_symlinks=False):
                        yield path
                        yielded += 1
                        if yielded >= max_files:
                            return
        except OSError:
            continue


def safe_file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def directory_size(path: Path, root: Path, *, max_files: int = 25_000) -> int:
    if not is_within_root(path, root):
        return 0
    total = 0
    count = 0
    for file_path in iter_files(path, max_files=max_files):
        total += safe_file_size(file_path)
        count += 1
        if count >= max_files:
            break
    return total


def bytes_to_mb(value: int) -> float:
    return round(value / (1024 * 1024), 4)


def bytes_to_gb(value: int) -> float:
    return round(value / (1024 * 1024 * 1024), 4)


def disk_pressure_status(
    root: Path,
    *,
    warning_free_gb: float = DEFAULT_WARNING_FREE_GB,
    warning_free_pct: float = DEFAULT_WARNING_FREE_PCT,
    critical_free_gb: float = DEFAULT_CRITICAL_FREE_GB,
    critical_free_pct: float = DEFAULT_CRITICAL_FREE_PCT,
) -> dict[str, Any]:
    usage = shutil.disk_usage(root)
    free_gb = usage.free / (1024 * 1024 * 1024)
    free_pct = (usage.free / usage.total) * 100 if usage.total else 0.0
    codes: list[str] = []
    if free_gb < critical_free_gb or free_pct < critical_free_pct:
        codes.append("DISK_FREE_CRITICAL")
        status = ACTION_REQUIRED
    elif free_gb < warning_free_gb or free_pct < warning_free_pct:
        codes.append("DISK_FREE_WARNING")
        status = WARNING
    else:
        status = OK
    return {
        "disk_status": status,
        "total_gb": bytes_to_gb(usage.total),
        "used_gb": bytes_to_gb(usage.used),
        "free_gb": round(free_gb, 4),
        "free_pct": round(free_pct, 4),
        "warning_free_gb": warning_free_gb,
        "warning_free_pct": warning_free_pct,
        "critical_free_gb": critical_free_gb,
        "critical_free_pct": critical_free_pct,
        "pressure_codes": codes,
    }


def build_storage_inventory(
    root: Path,
    *,
    max_files: int = 100_000,
    top_n: int = 25,
) -> dict[str, Any]:
    class_bytes: dict[str, int] = {}
    class_counts: dict[str, int] = {}
    top_files: list[dict[str, Any]] = []
    large_sierra_depth: list[dict[str, Any]] = []
    cleanup_candidates: list[dict[str, Any]] = []
    scanned_files = 0

    for path in iter_files(root, max_files=max_files):
        scanned_files += 1
        size = safe_file_size(path)
        decision = classify_path(path, root)
        class_bytes[decision.retention_class] = class_bytes.get(decision.retention_class, 0) + size
        class_counts[decision.retention_class] = class_counts.get(decision.retention_class, 0) + 1
        item = {
            "path": relpath(path, root),
            "size_mb": bytes_to_mb(size),
            "retention_class": decision.retention_class,
            "deletion_allowed": decision.deletion_allowed,
            "archive_required_before_delete": decision.archive_required_before_delete,
            "reason": decision.reason,
        }
        top_files.append(item)
        if path.suffix.lower() in {".depth", ".scid"} or "sierra" in relpath(path, root).lower():
            large_sierra_depth.append(item)
        if decision.deletion_allowed:
            cleanup_candidates.append(item)

    top_files = sorted(top_files, key=lambda item: item["size_mb"], reverse=True)[:top_n]
    large_sierra_depth = sorted(large_sierra_depth, key=lambda item: item["size_mb"], reverse=True)[:top_n]
    cleanup_candidates = sorted(cleanup_candidates, key=lambda item: item["size_mb"], reverse=True)[:top_n]

    temp_dirs: list[dict[str, Any]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        relative = relpath(child, root)
        if not _is_root_temp_dir(relative) and child.name not in TEMP_DIR_NAMES:
            continue
        decision = classify_path(child, root)
        size = directory_size(child, root)
        temp_dirs.append(
            {
                "path": relative,
                "size_mb": bytes_to_mb(size),
                "retention_class": decision.retention_class,
                "deletion_allowed": decision.deletion_allowed,
                "archive_required_before_delete": decision.archive_required_before_delete,
                "reason": decision.reason,
            }
        )
    temp_dirs = sorted(temp_dirs, key=lambda item: item["size_mb"], reverse=True)[:top_n]

    return {
        "scanned_files": scanned_files,
        "class_counts": dict(sorted(class_counts.items())),
        "class_size_mb": {key: bytes_to_mb(value) for key, value in sorted(class_bytes.items())},
        "top_files": top_files,
        "large_sierra_depth_files": large_sierra_depth,
        "dry_run_cleanup_candidates": cleanup_candidates,
        "temp_cache_directories": temp_dirs,
        "dry_run_cleanup_candidate_count": len(cleanup_candidates),
        "temp_cache_directory_count": len(temp_dirs),
    }


def build_status_row(
    *,
    root: Path,
    now_utc: datetime | None = None,
    target_date: date | None = None,
    max_files: int = 100_000,
    top_n: int = 25,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    now = coerce_utc(now_utc)
    target = target_date or now.date()
    generated = generated_at_utc or now.isoformat()
    disk = disk_pressure_status(root)
    inventory = build_storage_inventory(root, max_files=max_files, top_n=top_n)

    protected_delete_violations = [
        item
        for item in [*inventory["top_files"], *inventory["large_sierra_depth_files"]]
        if item["retention_class"] in {RAW_SOURCE, EVIDENCE_LOG, DERIVED_FEATURE, REPORT} and item["deletion_allowed"]
    ]
    action_required_codes = list(disk["pressure_codes"])
    if protected_delete_violations:
        action_required_codes.append("PROTECTED_PATH_MARKED_DELETABLE")

    if "DISK_FREE_CRITICAL" in action_required_codes or protected_delete_violations:
        status = ACTION_REQUIRED
    elif action_required_codes:
        status = WARNING
    else:
        status = OK

    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        POLICY_VERSION,
        target.isoformat(),
        status,
        disk["disk_status"],
        sorted(set(action_required_codes)),
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("storage_retention", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "policy_version": POLICY_VERSION,
        "lto_id": "LTO-038",
        "target_date": target.isoformat(),
        "checked_at_utc": now.isoformat(),
        "storage_status": status,
        "dry_run_only": True,
        "deletion_performed": False,
        "disk": disk,
        "inventory": inventory,
        "retention_classes": {
            RAW_SOURCE: "Raw market/account/source data. Never delete without archival policy.",
            EVIDENCE_LOG: "Append-only evidence logs. Never delete without archival policy.",
            DERIVED_FEATURE: "Derived research features. Preserve unless lineage-safe archive exists.",
            TEMP_CACHE: "Temp/cache allowlist. Dry-run deletion candidate only.",
            LOG_ROTATABLE: "Runtime logs. Rotate/archive before removal.",
            LOCK_FILE: "Runtime lock state. Do not delete from storage monitor.",
            REPORT: "Research/report artifact. Preserve unless archived.",
            CODE_CONFIG: "Code, tests, config, scripts. Not a cleanup target.",
            OTHER_REVIEW: "Manual review required.",
        },
        "deletion_allowlist_policy": {
            "allowed_classes": [TEMP_CACHE],
            "allowed_root_prefixes": list(TEMP_DIR_PREFIXES),
            "allowed_names": sorted(TEMP_DIR_NAMES),
            "raw_source_delete_allowed": False,
            "evidence_log_delete_allowed": False,
            "reports_delete_allowed": False,
            "apply_mode_available": False,
        },
        "action_required_codes": sorted(set(action_required_codes)),
        "claim_boundary": (
            "This row is a dry-run storage-retention classification only. It "
            "does not delete files and does not approve deletion of raw source "
            "data, Sierra/depth files, account history, shadow evidence logs, "
            "or research reports."
        ),
        "evidence_class": "CONTROL_ONLY",
        "promotion_verdict": PROMOTION_VERDICT,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }
