#!/usr/bin/env python3
"""Build the vNext repo context cleanup inventory ledgers.

This script is intentionally metadata-first. It inventories the working tree,
Git/LFS footprint, runtime surfaces, credential/account-artifact patterns, and
active-context stale-current claims for the 2026-05-29 cleanup route.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = ROOT / "research" / "operations" / "vnext_repo_context_cleanup_deletion_2026_05_29"
INVENTORY_HASH_LIMIT_BYTES = 5 * 1024 * 1024
PROMPT_PATH = "research/science_program_2026_05/04_goal_prompts/VNEXT_REPO_CONTEXT_CLEANUP_DELETION_GOAL_PROMPT_2026-05-29.md"
STARTER_PATH = "research/science_program_2026_05/04_goal_prompts/VNEXT_REPO_CONTEXT_CLEANUP_DELETION_STARTER_2026-05-29.txt"
LIVE_ACTIVATION_DIR = "research/operations/vnext_live_activation_active_repair_companion_2026_05_28"
VNEXT_REPAIR_DIR = "research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"

ACTIVE_CONTEXT_PATHS = [
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".context/00_READING_ORDER.md",
    ".context/LIVE_STATE.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
]

CURRENT_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

TEXT_EXTENSIONS = {
    ".bat",
    ".cfg",
    ".csv",
    ".env",
    ".gitignore",
    ".gitattributes",
    ".html",
    ".ini",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".rst",
    ".sh",
    ".txt",
    ".yaml",
    ".yml",
}

RUNTIME_ROOTS = (
    "shadow_logs/",
    "pipeline_state/",
    "knowledge_base/trade_records/",
    "knowledge_base/index/",
    "data/ticks/",
    "data/m1/",
    "data/historical",
)

CACHE_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    ".ipynb_checkpoints",
}

STALE_PATTERNS = [
    {
        "id": "old_7_symbol_current",
        "regex": re.compile(r"\b7 instruments\b|\b7-symbol\b|7 orchestrators", re.IGNORECASE),
        "replacement": "24-symbol vNext production replacement surface",
    },
    {
        "id": "old_primary_l2_current",
        "regex": re.compile(r"PrimaryAnalyzer\s*(?:->|/|and)\s*L2|Component 3A.*Component 4", re.IGNORECASE),
        "replacement": "vNext runtime/pre-AI/post-L2 routing with old AI/L2 framed historical unless explicitly current",
    },
    {
        "id": "static_15r_current",
        "regex": re.compile(r"\b1\.5R\b|fixed[- ]?1\.5|static[- ]?1\.5", re.IGNORECASE),
        "replacement": "momentum_exhaustion primary with partial_be_runner exception; fixed 1.5R is comparator/fail-closed only",
    },
    {
        "id": "j46_j49_current",
        "regex": re.compile(r"\bJ46\b|\bJ49\b", re.IGNORECASE),
        "replacement": "J46/J49 are historical/comparator context unless labeled otherwise",
    },
    {
        "id": "april_live_current",
        "regex": re.compile(r"April\s+\d{1,2},\s+2026|2026-04|Apr\s+\d{1,2}", re.IGNORECASE),
        "replacement": "historical April state label or current 2026-05 vNext state",
    },
]

CREDENTIAL_PATTERNS = [
    ("api_key_name", re.compile(r"(?i)\b(api[_-]?key|anthropic_api_key|openai_api_key|telegram_bot_token|token)\b")),
    ("bearer_token_literal", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{12,}")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("broker_account_number", re.compile(r"\b(?:login|account|mt5_account|broker_account)\D{0,24}(\d{6,12})\b", re.IGNORECASE)),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=check,
    )


def run_cmd(args: list[str]) -> dict[str, Any]:
    started = utc_now()
    try:
        cp = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        return {
            "command": args,
            "started_at_utc": started,
            "ended_at_utc": utc_now(),
            "exit_code": cp.returncode,
            "stdout": cp.stdout,
            "stderr": cp.stderr,
        }
    except FileNotFoundError as exc:
        return {
            "command": args,
            "started_at_utc": started,
            "ended_at_utc": utc_now(),
            "exit_code": 127,
            "stdout": "",
            "stderr": str(exc),
        }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def sha256_file(path: Path) -> tuple[str | None, str | None]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest(), None
    except OSError as exc:
        return None, f"hash_failed:{type(exc).__name__}:{exc}"


def inventory_hash(path: Path, size: int | None, tracked_object_id: str | None) -> tuple[str | None, str]:
    if tracked_object_id:
        return None, "content_hash_deferred_tracked_git_object_id_recorded"
    if size is not None and size > INVENTORY_HASH_LIMIT_BYTES:
        return None, f"content_hash_deferred_size_gt_{INVENTORY_HASH_LIMIT_BYTES}_bytes_targeted_predelete_hash_required"
    sha, reason = sha256_file(path)
    return sha, "hashed" if sha else (reason or "hash_failed_unknown")


def content_hash_prefix(path: Path, limit: int = 4096) -> str | None:
    try:
        with path.open("rb") as handle:
            return hashlib.sha256(handle.read(limit)).hexdigest()
    except OSError:
        return None


def looks_text(path: Path, size: int | None = None) -> bool:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return True
    if path.name in {".gitignore", ".gitattributes", "AGENTS.md", "CLAUDE.md"}:
        return True
    if size is not None and size > 10 * 1024 * 1024:
        return False
    try:
        with path.open("rb") as handle:
            sample = handle.read(4096)
        if b"\x00" in sample:
            return False
        sample.decode("utf-8")
        return True
    except Exception:
        return False


def parse_status() -> dict[str, dict[str, str]]:
    cp = run_git(["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    raw = cp.stdout
    status: dict[str, dict[str, str]] = {}
    if not raw:
        return status
    entries = raw.split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        if not entry:
            i += 1
            continue
        code = entry[:2]
        path = entry[3:].replace("\\", "/")
        if code.startswith("R") or code.startswith("C"):
            i += 1
            old_path = entries[i].replace("\\", "/") if i < len(entries) else None
        else:
            old_path = None
        status[path] = {"xy": code, "old_path": old_path or ""}
        i += 1
    return status


def git_list_z(args: list[str]) -> set[str]:
    cp = run_git(args)
    if cp.returncode != 0 or not cp.stdout:
        return set()
    return {item.replace("\\", "/") for item in cp.stdout.split("\0") if item}


def parse_head_tree() -> dict[str, dict[str, Any]]:
    cp = run_git(["ls-tree", "-r", "-l", "HEAD"])
    rows: dict[str, dict[str, Any]] = {}
    for line in cp.stdout.splitlines():
        # 100644 blob <oid> <size-or->\t<path>
        if "\t" not in line:
            continue
        meta, path = line.split("\t", 1)
        parts = meta.split()
        if len(parts) < 4:
            continue
        rows[path.replace("\\", "/")] = {
            "mode": parts[0],
            "object_type": parts[1],
            "object_id": parts[2],
            "git_size_bytes": None if parts[3] == "-" else int(parts[3]),
        }
    return rows


def parse_lfs_current() -> set[str]:
    cp = run_cmd(["git", "lfs", "ls-files", "-n"])
    if cp["exit_code"] != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in cp["stdout"].splitlines() if line.strip()}


def parse_lfs_all() -> list[dict[str, Any]]:
    cp = run_cmd(["git", "lfs", "ls-files", "--all"])
    rows: list[dict[str, Any]] = []
    for line in cp["stdout"].splitlines():
        text = line.strip()
        if not text:
            continue
        parts = text.split()
        oid = parts[0] if parts else ""
        marker = parts[1] if len(parts) > 1 else ""
        path = " ".join(parts[2:]) if len(parts) > 2 else ""
        rows.append(
            {
                "surface": "git_lfs_all",
                "lfs_object_id_prefix": oid,
                "materialization_marker": marker,
                "path": path.replace("\\", "/"),
                "raw": text,
            }
        )
    if not rows and cp["exit_code"] != 0:
        rows.append(
            {
                "surface": "git_lfs_all",
                "status": "tool_failed",
                "exit_code": cp["exit_code"],
                "stderr": cp["stderr"][:2000],
            }
        )
    return rows


def lfs_materialization(path: Path, is_lfs: bool) -> str:
    if not is_lfs:
        return "not_lfs_tracked"
    try:
        with path.open("rb") as handle:
            sample = handle.read(128)
    except OSError as exc:
        return f"lfs_tracked_unreadable:{type(exc).__name__}"
    if sample.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return "lfs_pointer_file"
    return "lfs_materialized_content"


def directory_family(path: str) -> str:
    if path.startswith(".context/"):
        return ".context"
    if path.startswith("research/operations/"):
        return "research_operations"
    if path.startswith("research/science_program_2026_05/"):
        return "science_program_2026_05"
    if path.startswith("research/program_control/"):
        return "program_control"
    if path.startswith("research/"):
        return "research_other"
    if path.startswith("src/"):
        return "src"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("scripts/"):
        return "scripts"
    if path.startswith("config/"):
        return "config"
    if path.startswith("shadow_logs/"):
        return "shadow_logs"
    if path.startswith("pipeline_state/"):
        return "pipeline_state"
    if path.startswith("knowledge_base/"):
        return "knowledge_base"
    if path.startswith("data/"):
        return "data"
    return "repo_root"


def role_classification(path: str, status: str) -> str:
    suffix = Path(path).suffix.lower()
    parts = set(Path(path).parts)
    if ".git" in parts:
        return "git_internal"
    if any(part in CACHE_PARTS for part in parts):
        return "temp_cache"
    if path.endswith(".tmp") or ".tmp" in path or re.search(r"\.tmp\d+$", path):
        return "temp_cache"
    if path.startswith("src/"):
        return "active_code"
    if path.startswith("tests/"):
        return "active_test"
    if path.startswith("config/") or path in {".gitattributes", ".gitignore", "pyproject.toml", "pytest.ini"}:
        return "active_config"
    if path.startswith("scripts/"):
        return "active_or_support_script"
    if path in ACTIVE_CONTEXT_PATHS or path.startswith(".context/00_core/") or path == ".context/00_READING_ORDER.md":
        return "active_context"
    if path.startswith(LIVE_ACTIVATION_DIR):
        return "active_live_activation_route"
    if path.startswith(VNEXT_REPAIR_DIR):
        return "current_vnext_reproducibility_evidence"
    if path.startswith("research/science_program_2026_05/04_goal_prompts/"):
        if "VNEXT_REPO_CONTEXT_CLEANUP_DELETION" in path:
            return "active_route"
        return "stale_prompt_or_prior_route_prompt"
    if path.startswith(".context/02_session_handoffs/"):
        return "stale_handoff_or_historical_context"
    if path.startswith(RUNTIME_ROOTS):
        return "runtime_data"
    if path.startswith("research/archive/"):
        return "cold_archive_evidence"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".xlsx", ".mp4"}:
        return "image_media_or_binary_evidence"
    if path.startswith("research/"):
        return "historical_route_or_research_evidence"
    if status == "ignored":
        return "temp_cache_or_ignored_runtime"
    return "unknown"


def first_pass_decision(path: str, role: str, git_status: str, lfs_state: str) -> str:
    if role in {"active_code", "active_config", "active_test", "active_or_support_script", "active_context", "active_route"}:
        return "KEEP_CURRENT_AUTHORITY"
    if role == "active_live_activation_route":
        return "KEEP_CURRENT_AUTHORITY"
    if role == "current_vnext_reproducibility_evidence":
        return "KEEP_REPRODUCIBILITY_EVIDENCE"
    if role == "runtime_data":
        return "KEEP_REPRODUCIBILITY_EVIDENCE"
    if role == "cold_archive_evidence":
        return "COLD_EVIDENCE_ARCHIVE_WITH_POINTER"
    if role == "temp_cache" or role == "temp_cache_or_ignored_runtime":
        return "DELETE_CONTEXT_POLLUTION_UNTRACKED" if git_status != "tracked" else "DELETE_CONTEXT_POLLUTION_TRACKED"
    if role == "stale_prompt_or_prior_route_prompt":
        return "COMPRESS_TO_CURRENT_SUMMARY_THEN_DELETE"
    if role == "stale_handoff_or_historical_context":
        return "COLD_EVIDENCE_ARCHIVE_WITH_POINTER"
    if role == "historical_route_or_research_evidence":
        if lfs_state == "lfs_materialized_content":
            return "COLD_EVIDENCE_ARCHIVE_WITH_POINTER"
        return "COMPRESS_TO_CURRENT_SUMMARY_THEN_DELETE"
    if role == "image_media_or_binary_evidence":
        return "COLD_EVIDENCE_ARCHIVE_WITH_POINTER"
    return "KEEP_REPRODUCIBILITY_EVIDENCE"


def load_active_reference_text() -> str:
    chunks: list[str] = []
    roots = [ROOT / ".context", ROOT / "src", ROOT / "scripts", ROOT / "tests", ROOT / "config"]
    for special in ["README.md", "CLAUDE.md", "AGENTS.md"]:
        p = ROOT / special
        if p.exists() and p.is_file():
            try:
                chunks.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size > 1024 * 1024 or not looks_text(path, size):
                continue
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    return "\n".join(chunks)


def build_reference_counters(active_text: str) -> tuple[Counter[str], Counter[str]]:
    normalized = active_text.replace("\\", "/")
    token_re = re.compile(r"(?<![A-Za-z0-9_.\-/])(?:\.context|research|src|scripts|tests|config|shadow_logs|pipeline_state|knowledge_base|data|README|CLAUDE|AGENTS)[A-Za-z0-9_./\-]*")
    path_counter: Counter[str] = Counter()
    basename_counter: Counter[str] = Counter()
    for match in token_re.finditer(normalized):
        token = match.group(0).strip("`'\"),.;:")
        if not token:
            continue
        path_counter[token] += 1
        base = Path(token).name
        if base and len(base) > 6:
            basename_counter[base] += 1
    return path_counter, basename_counter


def scan_reference_count(path: str, reference_counters: tuple[Counter[str], Counter[str]]) -> dict[str, Any]:
    path_counter, basename_counter = reference_counters
    basename = Path(path).name
    direct = path_counter.get(path, 0)
    base = basename_counter.get(basename, 0) if basename and len(basename) > 6 else 0
    return {
        "active_reference_count": direct,
        "active_basename_reference_count": base,
        "reference_scan_scope": "single_pass_path_token_index_README_CLAUDE_AGENTS_context_src_scripts_tests_config_text_under_1MiB",
    }


def discover_files() -> tuple[set[str], set[str], set[str], set[str], set[str], dict[str, dict[str, str]]]:
    tracked = git_list_z(["ls-files", "-z"])
    others = git_list_z(["ls-files", "--others", "--exclude-standard", "-z"])
    ignored = git_list_z(["ls-files", "--others", "--ignored", "--exclude-standard", "-z"])
    deleted = set()
    status_map = parse_status()
    for path, info in status_map.items():
        if "D" in info["xy"]:
            deleted.add(path)
    disk_files: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = Path(dirpath).relative_to(ROOT).as_posix()
        if rel_dir == ".git" or rel_dir.startswith(".git/"):
            dirnames[:] = []
            continue
        for filename in filenames:
            p = Path(dirpath) / filename
            disk_files.add(rel(p))
    all_paths = set(tracked) | others | ignored | deleted | disk_files
    return all_paths, tracked, others, ignored, deleted, status_map


def build_inventory() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    all_paths, tracked, others, ignored, deleted, status_map = discover_files()
    head_tree = parse_head_tree()
    lfs_current = parse_lfs_current()
    reference_counters = build_reference_counters(load_active_reference_text())

    inventory: list[dict[str, Any]] = []
    credential_rows: list[dict[str, Any]] = []
    runtime_rows: list[dict[str, Any]] = []
    delete_breakage_rows: list[dict[str, Any]] = []
    mixed_rows: list[dict[str, Any]] = []
    consolidation_rows: list[dict[str, Any]] = []

    for path in sorted(all_paths):
        fs_path = ROOT / path
        exists = fs_path.exists()
        if path in tracked:
            git_status = "tracked"
        elif path in ignored:
            git_status = "ignored"
        elif path in others:
            git_status = "untracked"
        elif path in deleted:
            git_status = "deleted"
        else:
            git_status = "non_git_disk"
        stat = None
        size = None
        mtime = None
        if exists and fs_path.is_file():
            try:
                stat = fs_path.stat()
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
            except OSError:
                pass
        sha, hash_status = (None, "path_deleted_or_not_regular_file")
        if exists and fs_path.is_file():
            sha, hash_status = inventory_hash(fs_path, size, head_tree.get(path, {}).get("object_id"))
        is_lfs = path in lfs_current
        lfs_state = lfs_materialization(fs_path, is_lfs) if exists and fs_path.is_file() else ("lfs_tracked_deleted" if is_lfs else "not_lfs_tracked")
        role = role_classification(path, git_status)
        decision = first_pass_decision(path, role, git_status, lfs_state)
        ref_info = scan_reference_count(path, reference_counters)
        mixed_status = "not_mixed"
        if role == "active_context":
            mixed_status = "mixed_scan_pending"
        elif role in {"stale_handoff_or_historical_context", "historical_route_or_research_evidence", "stale_prompt_or_prior_route_prompt"}:
            mixed_status = "mixed_extract_then_delete_or_demote_pending"

        row = {
            "relative_path": path,
            "git_status": git_status,
            "git_xy": status_map.get(path, {}).get("xy", ""),
            "file_type": Path(path).suffix.lower() or "[no_extension]",
            "size_bytes": size,
            "last_modified_utc": mtime,
            "git_object_id_head": head_tree.get(path, {}).get("object_id"),
            "git_object_size_head": head_tree.get(path, {}).get("git_size_bytes"),
            "content_sha256": sha,
            "hash_status": hash_status,
            "lfs_status": lfs_state,
            "directory_family": directory_family(path),
            "role_classification": role,
            "reference_count_from_current_active_docs_code": ref_info["active_reference_count"],
            "basename_reference_count_from_current_active_docs_code": ref_info["active_basename_reference_count"],
            "reference_scan_scope": ref_info["reference_scan_scope"],
            "first_pass_classification": decision,
            "mixed_context_status": mixed_status,
            "useful_section_claim_table_refs": [],
            "stale_section_claim_table_refs": [],
            "merge_destination_or_rewrite_target": None,
            "evidence_used_for_classification": [
                "git_status",
                "git_ls_tree_head",
                "git_lfs_ls_files_current",
                "path_family_heuristic",
                "active_context_reference_scan",
            ],
        }
        inventory.append(row)

        if decision.startswith("DELETE_CONTEXT_POLLUTION"):
            delete_breakage_rows.append(
                {
                    "relative_path": path,
                    "candidate_decision": decision,
                    "active_reference_count": ref_info["active_reference_count"],
                    "basename_reference_count": ref_info["active_basename_reference_count"],
                    "breakage_status": "needs_manual_review_before_delete"
                    if ref_info["active_reference_count"] or git_status == "tracked"
                    else "no_active_direct_reference_detected",
                    "proof_scope": ref_info["reference_scan_scope"],
                }
            )

        if path.startswith(RUNTIME_ROOTS):
            runtime_rows.append(runtime_retention_row(row))

        credential_rows.extend(scan_credentials(row, fs_path))

        if mixed_status != "not_mixed":
            mixed_rows.append(
                {
                    "relative_path": path,
                    "mixed_context_status": mixed_status,
                    "role_classification": role,
                    "first_pass_classification": decision,
                    "useful_intelligence": "pending_section_level_extraction",
                    "stale_framing": "pending_section_level_extraction",
                    "target_current_summary_path": ".context/00_core/current_vnext_system_map.md",
                    "source_file_final_decision": decision,
                    "proof_status": "not_yet_executed",
                }
            )

    consolidation_rows.extend(build_consolidation_rows(inventory))
    summary = summarize_inventory(inventory)
    return inventory, summary, credential_rows, runtime_rows, delete_breakage_rows, mixed_rows, consolidation_rows


def runtime_retention_row(inventory_row: dict[str, Any]) -> dict[str, Any]:
    path = inventory_row["relative_path"]
    if path.startswith("data/m1/") or "m1_capture_state" in path:
        tier = "hot_current_forward_capture"
    elif path.startswith("data/ticks/") or "tick" in path:
        tier = "hot_current_forward_capture"
    elif path.startswith("shadow_logs/gtos_vnext") or path.startswith("shadow_logs/cross_instrument") or path.startswith("shadow_logs/ob_retest"):
        tier = "hot_current_runtime_decision_stream"
    elif path.startswith("pipeline_state/") and (path.endswith(".tmp") or ".tmp" in path):
        tier = "delete_now_temp_atomic_write_fragment"
    elif path.startswith("pipeline_state/"):
        tier = "hot_current_runtime_state"
    elif path.startswith("knowledge_base/trade_records/"):
        tier = "warm_reproducibility_trade_record_evidence"
    elif path.startswith("data/historical"):
        tier = "warm_reproducibility_market_data"
    else:
        tier = "warm_reproducibility_runtime_log"
    return {
        "relative_path": path,
        "git_status": inventory_row["git_status"],
        "size_bytes": inventory_row["size_bytes"],
        "last_modified_utc": inventory_row["last_modified_utc"],
        "runtime_retention_tier": tier,
        "decision_status": "initial_inventory_not_executed",
        "evidence": inventory_row["role_classification"],
    }


def scan_credentials(row: dict[str, Any], fs_path: Path) -> list[dict[str, Any]]:
    path = row["relative_path"]
    rows: list[dict[str, Any]] = []
    path_lower = path.lower()
    path_flag = any(token in path_lower for token in [".env", "credential", "token", "account", "login", "broker", "telegram"])
    if path_flag:
        rows.append(
            {
                "relative_path": path,
                "finding_type": "sensitive_path_name",
                "matched_value_redacted": "[path-name]",
                "line_number": None,
                "artifact_decision": "review_required_current_keep_or_delete",
                "git_status": row["git_status"],
            }
        )
    if not fs_path.exists() or not fs_path.is_file():
        return rows
    size = row["size_bytes"] or 0
    if size > 5 * 1024 * 1024 or not looks_text(fs_path, size):
        return rows
    try:
        text = fs_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return rows
    for idx, line in enumerate(text.splitlines(), 1):
        for finding_type, regex in CREDENTIAL_PATTERNS:
            match = regex.search(line)
            if not match:
                continue
            rows.append(
                {
                    "relative_path": path,
                    "finding_type": finding_type,
                    "matched_value_redacted": "[redacted]",
                    "line_number": idx,
                    "artifact_decision": classify_credential_decision(path, finding_type),
                    "git_status": row["git_status"],
                }
            )
            break
    return rows


def classify_credential_decision(path: str, finding_type: str) -> str:
    if path.startswith("research/operations/vnext_live_activation_active_repair_companion_2026_05_28/") and finding_type == "broker_account_number":
        return "KEEP_CURRENT_OPERATIONAL_EVIDENCE_NON_DEFAULT_READING"
    if path.startswith(".context/") or path in {"CLAUDE.md", "AGENTS.md"}:
        return "REWRITE_OR_REDACT_IF_STALE_ACCOUNT_MATERIAL"
    if path.startswith("shadow_logs/") or path.startswith("pipeline_state/"):
        return "RUNTIME_RETENTION_REVIEW"
    return "REVIEW_REQUIRED_CURRENT_KEEP_OR_DELETE"


def build_consolidation_rows(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    active_docs = [r for r in inventory if r["role_classification"] == "active_context"]
    for doc in active_docs:
        rows.append(
            {
                "relative_path": doc["relative_path"],
                "overlap_family": "active_entrypoint_current_truth",
                "current_authority_target": ".context/00_core/current_vnext_system_map.md",
                "duplicate_or_stale_context_risk": "old_live_system_claims_may_overlap_current_vnext_truth",
                "decision_status": "pending_section_level_rewrite",
            }
        )
    return rows


def summarize_inventory(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_bytes = sum(r["size_bytes"] or 0 for r in rows)
    return {
        "schema_version": "repo_file_inventory_summary_v1",
        "generated_at_utc": utc_now(),
        "route_id": "vnext_repo_context_cleanup_deletion_2026_05_29",
        "file_rows": len(rows),
        "total_size_bytes": total_bytes,
        "by_git_status": dict(Counter(r["git_status"] for r in rows)),
        "by_role_classification": dict(Counter(r["role_classification"] for r in rows)),
        "by_first_pass_classification": dict(Counter(r["first_pass_classification"] for r in rows)),
        "by_lfs_status": dict(Counter(r["lfs_status"] for r in rows)),
        "largest_file_bytes": max((r["size_bytes"] or 0 for r in rows), default=0),
        "hash_status_counts": dict(Counter(r["hash_status"] for r in rows)),
    }


def build_git_lfs_footprint() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    head_tree = parse_head_tree()
    lfs_current = parse_lfs_current()
    for path, meta in sorted(head_tree.items()):
        fs_path = ROOT / path
        is_lfs = path in lfs_current
        rows.append(
            {
                "surface": "current_head_tracked_file",
                "relative_path": path,
                "git_object_id": meta["object_id"],
                "git_size_bytes": meta["git_size_bytes"],
                "lfs_status": lfs_materialization(fs_path, is_lfs) if fs_path.exists() else ("lfs_tracked_deleted" if is_lfs else "not_lfs_tracked"),
                "github_size_class": github_size_class(meta["git_size_bytes"]),
                "decision_status": "pending_lfs_or_large_file_decision" if (meta["git_size_bytes"] or 0) >= 50_000_000 or is_lfs else "no_large_file_action_required_initial",
            }
        )
    rows.extend(parse_lfs_all())
    rows.extend(build_large_git_object_rows())
    rows.extend(build_ref_rows())
    rows.extend(build_remote_rows())
    summary = {
        "schema_version": "repo_git_lfs_github_footprint_summary_v1",
        "generated_at_utc": utc_now(),
        "route_id": "vnext_repo_context_cleanup_deletion_2026_05_29",
        "ledger_rows": len(rows),
        "current_head_tracked_files": len(head_tree),
        "current_lfs_files": len(lfs_current),
        "large_current_head_files_ge_50mb": sum(1 for r in rows if r.get("surface") == "current_head_tracked_file" and (r.get("git_size_bytes") or 0) >= 50_000_000),
        "github_hard_limit_current_head_files": sum(1 for r in rows if r.get("surface") == "current_head_tracked_file" and (r.get("git_size_bytes") or 0) >= 100_000_000),
        "surfaces": dict(Counter(r.get("surface", "unknown") for r in rows)),
    }
    return rows, summary


def github_size_class(size: int | None) -> str:
    if size is None:
        return "unknown"
    if size >= 100_000_000:
        return "github_hard_limit_ge_100mb"
    if size >= 50_000_000:
        return "github_warning_ge_50mb"
    return "below_github_warning"


def build_large_git_object_rows() -> list[dict[str, Any]]:
    rev = run_git(["rev-list", "--objects", "--all"])
    if rev.returncode != 0:
        return [
            {
                "surface": "reachable_git_object_large_scan",
                "status": "git_rev_list_failed",
                "stderr": rev.stderr[:2000],
            }
        ]
    object_paths: dict[str, str] = {}
    object_ids: list[str] = []
    for line in rev.stdout.splitlines():
        if not line.strip():
            continue
        oid, _, path = line.partition(" ")
        object_ids.append(oid)
        object_paths[oid] = path.replace("\\", "/")
    rows: list[dict[str, Any]] = []
    if not object_ids:
        return rows
    batch = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objecttype) %(objectname) %(objectsize)"],
        cwd=ROOT,
        input="\n".join(object_ids) + "\n",
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if batch.returncode != 0:
        return [
            {
                "surface": "reachable_git_object_large_scan",
                "status": "git_cat_file_failed",
                "stderr": batch.stderr[:2000],
            }
        ]
    head_paths = set(parse_head_tree())
    for line in batch.stdout.splitlines():
        parts = line.split()
        if len(parts) != 3 or parts[0] != "blob":
            continue
        oid = parts[1]
        try:
            size = int(parts[2])
        except ValueError:
            continue
        if size < 50_000_000:
            continue
        path = object_paths.get(oid, "")
        rows.append(
            {
                "surface": "reachable_git_object_ge_50mb",
                "git_object_id": oid,
                "relative_path": path,
                "git_object_size_bytes": size,
                "github_size_class": github_size_class(size),
                "current_head_presence": "present_in_head_path" if path in head_paths else "not_current_head_path",
                "history_cleanup_status": "history_rewrite_required_for_full_remote_size_cleanup",
            }
        )
    return rows


def build_ref_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    commands = {
        "local_branch": ["for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads"],
        "remote_tracking_branch": ["for-each-ref", "--format=%(refname:short) %(objectname)", "refs/remotes"],
        "tag": ["for-each-ref", "--format=%(refname:short) %(objectname)", "refs/tags"],
        "stash": ["stash", "list", "--format=%gd %H %gs"],
        "worktree": ["worktree", "list", "--porcelain"],
        "submodule": ["submodule", "status", "--recursive"],
    }
    for surface, args in commands.items():
        cp = run_git(args)
        if cp.returncode != 0:
            rows.append({"surface": surface, "status": "tool_failed", "stderr": cp.stderr[:1000]})
            continue
        for line in cp.stdout.splitlines():
            if line.strip():
                rows.append({"surface": surface, "raw": line.strip()})
    return rows


def build_remote_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cp = run_git(["remote", "-v"])
    for line in cp.stdout.splitlines():
        if line.strip():
            rows.append({"surface": "git_remote", "raw": line.strip()})
    ls_remote = run_git(["ls-remote", "--heads", "--tags", "origin"])
    if ls_remote.returncode == 0:
        for line in ls_remote.stdout.splitlines():
            rows.append({"surface": "origin_remote_ref", "raw": line.strip()})
    else:
        rows.append({"surface": "origin_remote_ref", "status": "tool_failed_or_network_blocked", "stderr": ls_remote.stderr[:1000]})
    gh = shutil.which("gh")
    if not gh:
        rows.append({"surface": "github_cli", "status": "gh_not_available"})
        return rows
    for surface, args in {
        "github_release": [gh, "release", "list", "--limit", "100"],
        "github_actions_run": [gh, "run", "list", "--limit", "100"],
    }.items():
        result = run_cmd(args)
        if result["exit_code"] != 0:
            rows.append({"surface": surface, "status": "tool_failed_or_auth_required", "stderr": result["stderr"][:1000]})
            continue
        for line in result["stdout"].splitlines():
            if line.strip():
                rows.append({"surface": surface, "raw": line.strip()})
    return rows


def build_active_context_staleness() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    mixed: list[dict[str, Any]] = []
    for rel_path in ACTIVE_CONTEXT_PATHS:
        path = ROOT / rel_path
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), 1):
            for pattern in STALE_PATTERNS:
                if not pattern["regex"].search(line):
                    continue
                historical_label = bool(re.search(r"historical|archive|old|prior|deprecated|not current", line, re.IGNORECASE))
                status = "allowed_historical_mention" if historical_label else "stale_current_claim_needs_repair_review"
                row = {
                    "relative_path": rel_path,
                    "line_number": line_no,
                    "pattern_id": pattern["id"],
                    "line_excerpt": line[:500],
                    "staleness_status": status,
                    "current_replacement": pattern["replacement"],
                    "decision": "KEEP_HISTORICAL_LABEL_REQUIRED" if historical_label else "REWRITE_ACTIVE_DOC_REMOVE_STALE_SECTIONS",
                }
                rows.append(row)
                if status != "allowed_historical_mention":
                    mixed.append(
                        {
                            "relative_path": rel_path,
                            "line_number": line_no,
                            "mixed_section_status": "stale_current_claim_in_active_doc",
                            "useful_context_to_keep": "active entrypoint role or historical caveat",
                            "stale_context_to_remove": line[:500],
                            "rewrite_target": rel_path,
                        }
                    )
    plan = {
        "schema_version": "active_context_repair_plan_v1",
        "generated_at_utc": utc_now(),
        "route_id": "vnext_repo_context_cleanup_deletion_2026_05_29",
        "stale_rows_needing_repair": sum(1 for r in rows if r["staleness_status"] == "stale_current_claim_needs_repair_review"),
        "allowed_historical_mentions": sum(1 for r in rows if r["staleness_status"] == "allowed_historical_mention"),
        "files_needing_repair": sorted({r["relative_path"] for r in rows if r["staleness_status"] == "stale_current_claim_needs_repair_review"}),
        "next_action": "rewrite_active_entrypoints_after current truth layer is written",
    }
    return rows, plan, mixed


def build_current_truth_anchor() -> str:
    return f"""# Repo Current Truth Anchor

Generated: {utc_now()}
Route id: `vnext_repo_context_cleanup_deletion_2026_05_29`
Evidence class: `REPO_CONTEXT_CLEANUP_DELETION_CURRENT_TRUTH_PACKAGING`

## Current Runtime Truth

- vNext/moonshot production replacement is the active system truth to preserve.
- Current live surface is 24 symbols: {", ".join(CURRENT_SYMBOLS)}.
- Dynamic execution policy is `momentum_exhaustion` primary with `partial_be_runner` exception rows.
- Fixed/static `1.5R`, J46/J49, BE-only, 7-symbol, and old PrimaryAnalyzer/L2 framing are historical or comparator-only unless an active current artifact explicitly says otherwise.
- Live activation companion status from `{LIVE_ACTIVATION_DIR}`: gate-stack repaired, committed, live-reloaded, 24-symbol fleet fresh, and first real vNext order/fill/close/cost/deal reconciliation still pending.
- Coordination boundary: the live repair/monitor companion route can run in parallel; its current checkpoint/state files are hot current evidence and not cleanup targets unless a current-head cleanup decision proves a specific artifact obsolete and not required as live evidence.
- Current repair-hardening source from `{VNEXT_REPAIR_DIR}`: replay-selected rows `289600`; replay included live gates; dynamic replay selected rows `289600`; replayable metric rows `289599`; dynamic replay expectancy R about `0.9883`; promoted total R about `286221.353599`; production policy distribution `momentum_exhaustion=121112`, `partial_be_runner=168487`, `non_replayable_no_policy=1`.

## Cleanup Boundary

Git history is the deep archive. Current HEAD is the working surface. Keep decisions need current authority, active reproducibility value, or unique intelligence that has been demoted to cold evidence with a pointer.

## First Incomplete Invariant

`stage02_active_context_repair_and_stage04_deletion_execution_pending`
"""


def build_current_truth_docs() -> None:
    system_map = {
        "schema_version": "current_vnext_system_map_v1",
        "generated_at_utc": utc_now(),
        "route_id": "vnext_repo_context_cleanup_deletion_2026_05_29",
        "production_replacement": "vNext moonshot",
        "symbols": CURRENT_SYMBOLS,
        "execution_policy": {
            "primary": "momentum_exhaustion",
            "exception": "partial_be_runner",
            "fixed_1_5r_role": "baseline_comparator_and_fail_closed_refusal_only_not_live_default",
        },
        "live_activation": {
            "status": "gate_stack_repaired_committed_live_reloaded_awaiting_first_real_vnext_lifecycle",
            "route_dir": LIVE_ACTIVATION_DIR,
            "first_unresolved_lifecycle_evidence": "first real order/fill/close/cost/deal reconciliation",
        },
        "current_evidence_dirs": [
            LIVE_ACTIVATION_DIR,
            VNEXT_REPAIR_DIR,
            "research/operations/vnext_repo_context_cleanup_deletion_2026_05_29",
        ],
        "excluded_from_current_authority": [
            "old 7-symbol April live handoffs unless labeled historical",
            "old PrimaryAnalyzer/L2/static 1.5R/J46/J49 defaults unless comparator-only",
            "raw LFS/jsonl evidence ledgers before current summaries/manifests",
            "runtime temp/cache files",
        ],
    }
    write_json(ROOT / ".context/00_core/current_vnext_system_map.json", system_map)
    (ROOT / ".context/00_core/current_vnext_system_map.md").write_text(
        f"""# Current vNext System Map

Generated: {utc_now()}

## Read First

This file is the current vNext truth entrypoint. Use it before old handoffs, old program-control reports, and raw route ledgers.

## Production Surface

- Active system: vNext moonshot production replacement.
- Live symbols: {", ".join(CURRENT_SYMBOLS)}.
- Live activation status: gate-stack repaired, committed, live-reloaded, and waiting for first real vNext order/fill/close/cost/deal reconciliation.
- Current execution policy: `momentum_exhaustion` primary with `partial_be_runner` exception selection.
- Static fixed `1.5R`, J46/J49, and BE-only logic are not current production defaults; they are comparator, historical, diagnostic, or fail-closed references unless an active vNext artifact says otherwise.

## Evidence Pointers

- Live activation companion: `{LIVE_ACTIVATION_DIR}`
- Activation repair-hardening route: `{VNEXT_REPAIR_DIR}`
- Cleanup route: `research/operations/vnext_repo_context_cleanup_deletion_2026_05_29`
- Live companion coordination: current checkpoint/state files in the live activation companion route are hot live evidence, not cleanup targets. Open live companion gaps are context only for cleanup: native live-writer packet, vNext order/fill/close packet, explicit old PA/L2 absence in native packets, and real broker lifecycle reconciliation.

## Data Surfaces

- Hot runtime: `shadow_logs/gtos_vnext_*`, `shadow_logs/*runtime*`, `pipeline_state/`, `data/m1/`, `data/ticks/`
- Warm reproducibility: current vNext route summaries, manifests, selected trade shards, candidate records, and trade records
- Cold evidence: old route ledgers, old handoffs, LFS/raw JSONL shards, generated reports, and archived runtime streams reachable by manifest pointer

## First Unresolved Live Lifecycle Evidence

The next active live proof is the first real vNext order/fill/close/cost/deal reconciliation. Synthetic notification parity and live gate-stack parity are already recorded; broker lifecycle truth still needs a real event.
""",
        encoding="utf-8",
        newline="\n",
    )
    (ROOT / ".context/00_core/current_repo_reading_order.md").write_text(
        f"""# Current Repo Reading Order

Generated: {utc_now()}

1. Regenerate and read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/current_vnext_system_map.md`.
3. Read `.context/00_core/repo_cleanup_and_staleness_policy.md` when deciding keep/delete/compress status.
4. Read `{LIVE_ACTIVATION_DIR}/ACTIVE_REPAIR_STATE.json` for current live activation status.
5. Read `{LIVE_ACTIVATION_DIR}/LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json` for live/replay gate-stack parity.
6. Read `{VNEXT_REPAIR_DIR}/VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json` for vNext repair-hardening route state.
7. Read `.context/00_core/research_operating_doctrine.md`, `.context/00_core/goal_session_research_discipline.md`, and `.context/00_core/research_current_state.md` for research/doctrine controls. If `LIVE_STATE` marks `research_current_state.md` stale, inspect newer artifacts directly before relying on it.
8. Treat older handoffs, old program-control reports, raw JSONL/LFS ledgers, and April-era docs as historical or cold evidence unless a current truth file links them as active.
""",
        encoding="utf-8",
        newline="\n",
    )
    (ROOT / ".context/00_core/repo_cleanup_and_staleness_policy.md").write_text(
        f"""# Repo Cleanup And Staleness Policy

Generated: {utc_now()}

## Policy

Current HEAD is the working surface. Git history is the deep archive. Keep a file in current HEAD only when it is current authority, active code/config/test, active route state, active reproducibility evidence, or unique intelligence demoted through a cold-evidence pointer.

## Forbidden Active-Current Drift

Active docs must not present these historical or comparator-only patterns as current production truth:

- historical 7-symbol or April-era live surface;
- old PrimaryAnalyzer/L2 as the vNext production path;
- historical fixed/static `1.5R`, J46/J49, or BE-only as current vNext default execution;
- stale replay failures that current repair artifacts supersede;
- raw evidence ledgers as default reading context when summaries/manifests exist.

Historical mentions are allowed only when plainly labeled historical, archived, comparator-only, or superseded.

## Runtime Retention

Hot runtime surfaces include current vNext decision streams, M1/tick capture state, fresh pipeline state, current trade records, and live activation ledgers. Temp atomic-write fragments, cache directories, pycache, stale generated previews, and abandoned run scratch should be deleted after path-bounded proof.

## Large Evidence

Large JSONL/LFS/raw evidence should be outside default reading context. Keep summaries/manifests in current context and demote raw shards to cold reproducibility evidence when still needed.
""",
        encoding="utf-8",
        newline="\n",
    )


def build_stage00_state(summary: dict[str, Any], git_summary: dict[str, Any]) -> dict[str, Any]:
    head = run_git(["rev-parse", "HEAD"]).stdout.strip()
    head_subject = run_git(["log", "-1", "--oneline"]).stdout.strip()
    disk = shutil.disk_usage(ROOT)
    return {
        "schema_version": "repo_cleanup_state_v1",
        "route_id": "vnext_repo_context_cleanup_deletion_2026_05_29",
        "updated_at_utc": utc_now(),
        "status": "stage00_stage01_inventory_materialized_stage02_repair_pending",
        "head": head,
        "head_subject": head_subject,
        "live_state_path": ".context/LIVE_STATE.md",
        "controlling_prompt": PROMPT_PATH,
        "starter": STARTER_PATH,
        "current_vnext_route_anchors": [VNEXT_REPAIR_DIR],
        "current_live_activation_route_anchors": [LIVE_ACTIVATION_DIR],
        "disk_free_bytes": disk.free,
        "disk_total_bytes": disk.total,
        "tracked_untracked_summary": summary.get("by_git_status", {}),
        "lfs_status_summary": git_summary,
        "first_incomplete_cleanup_invariant": "stage02_active_context_repair_and_stage04_deletion_execution_pending",
        "coordination_boundary": {
            "live_companion_route_running_in_parallel": True,
            "live_companion_artifact_decision": "KEEP_CURRENT_AUTHORITY_HOT_LIVE_EVIDENCE",
            "cleanup_scope_guard": "Do not delete or rewrite active live companion artifacts unless a current-head cleanup decision proves they are obsolete and not required as live evidence.",
            "live_companion_open_evidence_gaps_context_only": [
                "native_live_writer_packet_pending",
                "vnext_order_fill_close_packet_pending",
                "explicit_old_pa_l2_absence_in_native_packets_pending",
                "real_broker_lifecycle_reconciliation_pending",
            ],
        },
        "forbidden_surfaces": [
            "no broker/order/deal/position operation",
            "no paid API/vendor call",
            "no prompt/config/risk/execution/safety/canary/selector behavior change outside cleanup docs/guardrails",
            "no remote push",
        ],
    }


def build_control_rows(command_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "timestamp_utc": utc_now(),
            "route_id": "vnext_repo_context_cleanup_deletion_2026_05_29",
            "action": "mandatory_preflight_completed_before_script",
            "evidence": ".context/LIVE_STATE.md regenerated and controlling prompt/doctrine/current artifacts read in-session",
            "result": "recorded",
        },
        {
            "timestamp_utc": utc_now(),
            "route_id": "vnext_repo_context_cleanup_deletion_2026_05_29",
            "action": "stage00_stage01_inventory_builder_executed",
            "evidence": "scripts/build_repo_context_cleanup_inventory.py",
            "result": "artifacts_written",
        },
    ]
    for result in command_results:
        rows.append(
            {
                "timestamp_utc": utc_now(),
                "route_id": "vnext_repo_context_cleanup_deletion_2026_05_29",
                "action": "plumbing_command",
                "command": result["command"],
                "exit_code": result["exit_code"],
                "stderr_excerpt": result["stderr"][:500],
                "stdout_bytes": len(result["stdout"].encode("utf-8", errors="replace")),
            }
        )
    return rows


def output_manifest(paths: list[Path]) -> dict[str, Any]:
    outputs = []
    for path in paths:
        p = path if path.is_absolute() else ROOT / path
        if not p.exists():
            continue
        sha, reason = sha256_file(p)
        outputs.append(
            {
                "relative_path": rel(p),
                "size_bytes": p.stat().st_size,
                "sha256": sha,
                "hash_status": "hashed" if sha else reason,
            }
        )
    return {
        "schema_version": "repo_cleanup_output_manifest_v1",
        "generated_at_utc": utc_now(),
        "route_id": "vnext_repo_context_cleanup_deletion_2026_05_29",
        "outputs": outputs,
        "output_count": len(outputs),
    }


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    print("stage=command_snapshots", flush=True)
    command_results = [
        run_cmd(["git", "status", "--short", "--branch"]),
        run_cmd(["git", "lfs", "ls-files", "--all"]),
        run_cmd(["git", "remote", "-v"]),
    ]

    print("stage=current_truth_docs", flush=True)
    build_current_truth_docs()
    (ROUTE_DIR / "REPO_CURRENT_TRUTH_ANCHOR.md").write_text(build_current_truth_anchor(), encoding="utf-8", newline="\n")

    print("stage=file_inventory", flush=True)
    inventory, inventory_summary, credential_rows, runtime_rows, delete_breakage_rows, mixed_rows, consolidation_rows = build_inventory()
    print("stage=git_lfs_footprint", flush=True)
    git_lfs_rows, git_lfs_summary = build_git_lfs_footprint()
    print("stage=active_context_staleness", flush=True)
    active_stale_rows, active_repair_plan, active_mixed_rows = build_active_context_staleness()
    mixed_rows.extend(active_mixed_rows)

    outputs: list[Path] = []
    artifacts: list[tuple[str, Any, str]] = [
        ("REPO_FILE_INVENTORY_LEDGER.jsonl", inventory, "jsonl"),
        ("REPO_FILE_INVENTORY_SUMMARY.json", inventory_summary, "json"),
        ("REPO_GIT_LFS_GITHUB_FOOTPRINT_LEDGER.jsonl", git_lfs_rows, "jsonl"),
        ("REPO_GIT_LFS_GITHUB_FOOTPRINT_SUMMARY.json", git_lfs_summary, "json"),
        ("REPO_CREDENTIAL_ACCOUNT_ARTIFACT_FOOTPRINT_LEDGER.jsonl", credential_rows, "jsonl"),
        ("REPO_RUNTIME_RETENTION_LEDGER.jsonl", runtime_rows, "jsonl"),
        ("REPO_DELETE_BREAKAGE_PROOF_LEDGER.jsonl", delete_breakage_rows, "jsonl"),
        ("REPO_MIXED_CONTEXT_EXTRACTION_LEDGER.jsonl", mixed_rows, "jsonl"),
        ("REPO_CONTEXT_CONSOLIDATION_LEDGER.jsonl", consolidation_rows, "jsonl"),
        ("ACTIVE_CONTEXT_STALENESS_LEDGER.jsonl", active_stale_rows, "jsonl"),
        ("ACTIVE_CONTEXT_REPAIR_PLAN.json", active_repair_plan, "json"),
        ("ACTIVE_CONTEXT_MIXED_SECTION_LEDGER.jsonl", active_mixed_rows, "jsonl"),
    ]
    for name, payload, kind in artifacts:
        path = ROUTE_DIR / name
        if kind == "jsonl":
            write_jsonl(path, payload)
        else:
            write_json(path, payload)
        outputs.append(path)

    state = build_stage00_state(inventory_summary, git_lfs_summary)
    write_json(ROUTE_DIR / "REPO_CLEANUP_STATE.json", state)
    outputs.append(ROUTE_DIR / "REPO_CLEANUP_STATE.json")

    control_rows = build_control_rows(command_results)
    write_jsonl(ROUTE_DIR / "REPO_CLEANUP_CONTROL_LEDGER.jsonl", control_rows)
    outputs.append(ROUTE_DIR / "REPO_CLEANUP_CONTROL_LEDGER.jsonl")
    outputs.append(ROUTE_DIR / "REPO_CURRENT_TRUTH_ANCHOR.md")
    outputs.extend(
        [
            ROOT / ".context/00_core/current_vnext_system_map.md",
            ROOT / ".context/00_core/current_vnext_system_map.json",
            ROOT / ".context/00_core/current_repo_reading_order.md",
            ROOT / ".context/00_core/repo_cleanup_and_staleness_policy.md",
        ]
    )
    manifest = output_manifest(outputs)
    write_json(ROUTE_DIR / "REPO_CLEANUP_OUTPUT_MANIFEST.json", manifest)

    print(json.dumps({"status": "ok", "route_dir": rel(ROUTE_DIR), "inventory_rows": len(inventory), "git_lfs_rows": len(git_lfs_rows), "active_stale_rows": len(active_stale_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
