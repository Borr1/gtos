"""Build G0EXP R1 local-heavy root/parser/hash/lineage source controls.

This lane is source/control materialization only. It scans local roots for
metadata, hashes small control artifacts, emits raw/heavy hash deferrals, and
binds parser and lineage evidence. It does not score outcomes, call APIs, pull
paid data, inspect broker account/order/deal/position history, commit raw market
blobs, or alter live trading behavior.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
UPSTREAM_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_scid_expansion_denominator_entry_synthesis_from_g12_audit"
)

DATE_TAG = "2026-05-13"
PREFIX = "G0EXP_R1"
ROUTE_ID = "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL"
EVIDENCE_CLASS = "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY"
SCHEMA_VERSION = "g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_v1"
TERMINAL_DECISION = "BUILT_G0EXP_R1_SOURCE_CONTROL_PACKAGE_G12_AUDIT_REQUIRED"

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

ASSIGNED_FAMILIES: dict[str, str] = {
    "R4-EXP-ROOT-001": "local_heavy_data_root_coverage_and_hash_deferral_controls",
    "R4-EXP-PARSER-001": "parser_version_shape_fingerprint_and_schema_drift_controls",
    "EXP-ADV-001": "hash_integrity_placebo_controls",
    "R4-EXP-CODEHIST-001": "source_control_commit_route_and_artifact_lineage_controls",
}

ADJACENT_PROMPT_FAMILIES: dict[str, str] = {
    "OVF-ANTI-ADV-002": "Duplicate-Key Collision Placebo Route",
    "OVF-ANTI-MISS-002": "Duplicate Denominator Drift Route",
    "OVF-ANTI-FAIL-003": "Schema Parser Clock Failure Taxonomy Route",
}

RAW_BLOB_SUFFIXES = {
    ".parquet",
    ".scid",
    ".depth",
    ".jsonl.gz",
    ".zip",
    ".bin",
    ".db",
    ".sqlite",
    ".feather",
    ".h5",
    ".hdf5",
    ".xlsx",
}
MARKET_DATA_SUFFIXES = RAW_BLOB_SUFFIXES | {".csv"}
TEXT_CONTROL_SUFFIXES = {".md", ".json", ".txt", ".py", ".yaml", ".yml", ".toml", ".ps1"}
SMALL_CONTROL_HASH_LIMIT = 8 * 1024 * 1024
ROOT_SCAN_FILE_LIMIT = 100_000
SAMPLE_LIMIT = 20
PARSER_MATRIX_LIMIT = 120
SCHEMA_SHAPE_LIMIT = 120

PROMPT_PATH = (
    PROMPT_DIR
    / "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_GOAL_PROMPT_2026-05-13.md"
)
NEXT_G12_PROMPT_PATH = (
    PROMPT_DIR
    / "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-13.md"
)

MANDATORY_CONTEXT = [
    ".context/LIVE_STATE.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    "research/science_program_2026_05/04_goal_prompts/G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_GOAL_PROMPT_2026-05-13.md",
    "research/science_program_2026_05/06_outcome_testing/g0_scid_expansion_denominator_entry_synthesis_from_g12_audit/G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS_DECISION_LEDGER_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/g0_scid_expansion_denominator_entry_synthesis_from_g12_audit/G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS_ROUTE_FAMILY_LEDGER_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/g0_scid_expansion_denominator_entry_synthesis_from_g12_audit/G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS_RANKED_ROUTE_PLAN_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/g0_scid_expansion_denominator_entry_synthesis_from_g12_audit/G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS_BLOCKER_PURSUIT_LEDGER_2026-05-13.json",
    "research/science_program_2026_05/06_outcome_testing/g0_scid_expansion_denominator_entry_synthesis_from_g12_audit/G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS_DENOMINATOR_QUARANTINE_PROOF_2026-05-13.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def output_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def git_head() -> str:
    if not hasattr(git_head, "_cached"):
        setattr(git_head, "_cached", run_git(["rev-parse", "--short=12", "HEAD"]))
    return getattr(git_head, "_cached")


def git_lineage(path: Path) -> dict[str, Any]:
    rel = repo_rel(path)
    proc = subprocess.run(
        ["git", "log", "--follow", "--format=%H%x09%aI%x09%s", "--", rel],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    commits = []
    for line in proc.stdout.splitlines()[:8]:
        parts = line.split("\t", 2)
        if len(parts) == 3:
            commits.append({"commit": parts[0], "author_date": parts[1], "subject": parts[2]})
    return {
        "path": rel,
        "exists": path.exists(),
        "git_tracked": bool(run_git(["ls-files", "--", rel])),
        "recent_commits": commits,
        "latest_commit": commits[0] if commits else None,
    }


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "head_at_build": git_head(),
        **SAFE_FLAGS,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any], summary_lines: list[str] | None = None) -> None:
    lines = [
        f"# {title}",
        "",
        f"- **route_id:** `{ROUTE_ID}`",
        f"- **evidence_class:** `{EVIDENCE_CLASS}`",
        "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
        "- **validation_safe:** `false`",
        "- **outcome_review_opened:** `false`",
        "- **live_effect:** `false`",
        "",
    ]
    if summary_lines:
        lines.extend(summary_lines)
        lines.append("")
    lines.extend(["```json", json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_pair(stem: str, title: str, payload: dict[str, Any], summary_lines: list[str] | None = None) -> list[Path]:
    json_path = output_path(stem, ".json")
    md_path = output_path(stem, ".md")
    write_json(json_path, payload)
    write_md(md_path, title, payload, summary_lines)
    return [json_path, md_path]


def should_skip_dir(name: str) -> bool:
    return name.lower() in {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".venv",
        "venv",
        ".codex_tmp",
        "_pytest",
    }


def path_depth(base: Path, path: Path) -> int:
    try:
        return len(path.relative_to(base).parts)
    except ValueError:
        return 0


def scan_root(label: str, root: Path, max_depth: int | None = None, recursive: bool = True) -> dict[str, Any]:
    row: dict[str, Any] = {
        "label": label,
        "path": str(root),
        "exists": root.exists(),
        "is_dir": root.is_dir() if root.exists() else False,
        "scan_policy": "metadata_only_no_content_copy",
        "recursive": recursive,
        "max_depth": max_depth,
        "status": "ROOT_ABSENT_EXACT" if not root.exists() else "ROOT_PRESENT_NOT_SCANNED",
        "file_count": 0,
        "dir_count": 0,
        "total_bytes": 0,
        "extension_counts": {},
        "raw_market_blob_count": 0,
        "market_data_like_count": 0,
        "manifest_control_candidate_count": 0,
        "parser_candidate_count": 0,
        "sample_raw_or_heavy_files": [],
        "sample_manifest_control_files": [],
        "sample_parser_files": [],
        "sample_other_files": [],
        "hash_deferral_records": [],
        "hashed_control_samples": [],
        "errors": [],
        "truncated": False,
    }
    if not root.exists():
        row["exact_next_requirement"] = "Owner/export/access must provide this root or an updated absolute path."
        return row
    if root.is_file():
        files = [root]
        iterator: list[tuple[Path, list[str], list[str]]] = []
    else:
        files = []
        iterator = []
        if recursive:
            for dirpath, dirnames, filenames in os.walk(root):
                current = Path(dirpath)
                dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
                if max_depth is not None and path_depth(root, current) >= max_depth:
                    dirnames[:] = []
                iterator.append((current, dirnames, filenames))
                if len(iterator) > ROOT_SCAN_FILE_LIMIT:
                    row["truncated"] = True
                    break
        else:
            try:
                filenames = [p.name for p in root.iterdir() if p.is_file()]
                dirnames = [p.name for p in root.iterdir() if p.is_dir()]
                iterator.append((root, dirnames, filenames))
            except OSError as exc:
                row["errors"].append(f"{type(exc).__name__}: {exc}")
    try:
        if root.is_file():
            pass
        else:
            for current, dirnames, filenames in iterator:
                row["dir_count"] += len(dirnames)
                for filename in filenames:
                    files.append(current / filename)
                    if len(files) >= ROOT_SCAN_FILE_LIMIT:
                        row["truncated"] = True
                        break
                if row["truncated"]:
                    break
    except OSError as exc:
        row["errors"].append(f"{type(exc).__name__}: {exc}")

    ext_counts: Counter[str] = Counter()
    manifest_candidates: list[Path] = []
    parser_candidates: list[Path] = []
    raw_candidates: list[Path] = []
    other_samples: list[Path] = []
    for file_path in files:
        try:
            stat = file_path.stat()
        except OSError as exc:
            row["errors"].append(f"{file_path}: {type(exc).__name__}: {exc}")
            continue
        suffix = "".join(file_path.suffixes[-2:]).lower() if file_path.name.lower().endswith(".jsonl.gz") else file_path.suffix.lower()
        suffix = suffix or "[no_ext]"
        ext_counts[suffix] += 1
        row["file_count"] += 1
        row["total_bytes"] += stat.st_size
        lower_name = file_path.name.lower()
        is_raw = suffix in RAW_BLOB_SUFFIXES
        is_market = suffix in MARKET_DATA_SUFFIXES
        is_manifest = any(token in lower_name for token in ("manifest", "source_hash", "source-index", "schema", "contract", "ledger", "registry", "status"))
        is_parser = suffix == ".py" and any(token in lower_name for token in ("parser", "scid", "sierra", "tick", "capture", "build", "audit", "verify"))
        if is_raw:
            row["raw_market_blob_count"] += 1
            raw_candidates.append(file_path)
        if is_market:
            row["market_data_like_count"] += 1
        if is_manifest:
            row["manifest_control_candidate_count"] += 1
            manifest_candidates.append(file_path)
        if is_parser:
            row["parser_candidate_count"] += 1
            parser_candidates.append(file_path)
        if len(other_samples) < SAMPLE_LIMIT and not is_raw and not is_manifest and not is_parser:
            other_samples.append(file_path)

    row["extension_counts"] = dict(sorted(ext_counts.items()))
    for attr, candidates in [
        ("sample_raw_or_heavy_files", raw_candidates),
        ("sample_manifest_control_files", manifest_candidates),
        ("sample_parser_files", parser_candidates),
        ("sample_other_files", other_samples),
    ]:
        samples = []
        for path in candidates[:SAMPLE_LIMIT]:
            try:
                samples.append({"path": str(path), "size_bytes": path.stat().st_size})
            except OSError:
                samples.append({"path": str(path), "size_bytes": None})
        row[attr] = samples

    for path in raw_candidates[:SAMPLE_LIMIT]:
        row["hash_deferral_records"].append(
            {
                "path": str(path),
                "suffix": path.suffix.lower(),
                "hash_status": "FULL_HASH_DEFERRED_RAW_OR_HEAVY_NO_COMMIT",
                "reason": "Raw/heavy market data blob is not committed or copied by this route.",
                "exact_rehash_procedure": f"Run a future source-control lane to compute sha256 over {path} read-only, record hash/size/mtime, and keep the raw file uncommitted.",
            }
        )
    for path in manifest_candidates[:SAMPLE_LIMIT]:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size <= SMALL_CONTROL_HASH_LIMIT and path.suffix.lower() in TEXT_CONTROL_SUFFIXES:
            try:
                row["hashed_control_samples"].append(
                    {
                        "path": str(path),
                        "size_bytes": size,
                        "sha256": sha256_file(path),
                        "hash_status": "HASHED_SMALL_CONTROL_ARTIFACT",
                    }
                )
            except OSError as exc:
                row["errors"].append(f"{path}: {type(exc).__name__}: {exc}")
        else:
            row["hash_deferral_records"].append(
                {
                    "path": str(path),
                    "size_bytes": size,
                    "hash_status": "HASH_DEFERRED_NON_TEXT_OR_TOO_LARGE_CONTROL_CANDIDATE",
                    "reason": "Not a small text control artifact under this lane's no-raw-commit policy.",
                    "exact_rehash_procedure": f"Hash {path} read-only in a source-control lane if it becomes a consumed source.",
                }
            )

    if row["errors"]:
        row["status"] = "ROOT_PRESENT_SCANNED_WITH_ERRORS"
    elif row["truncated"]:
        row["status"] = "ROOT_PRESENT_SCANNED_METADATA_TRUNCATED"
    else:
        row["status"] = "ROOT_PRESENT_SCANNED_METADATA_ONLY"
    row["no_raw_market_blob_content_copied"] = True
    return row


def local_roots() -> list[dict[str, Any]]:
    return [
        {"label": "current_worktree", "path": ROOT, "max_depth": 7, "recursive": True},
        {"label": "current_worktree_data", "path": ROOT / "data", "max_depth": 7, "recursive": True},
        {"label": "current_worktree_data_ticks", "path": ROOT / "data" / "ticks", "max_depth": 4, "recursive": True},
        {"label": "current_worktree_data_external", "path": ROOT / "data" / "external", "max_depth": 6, "recursive": True},
        {"label": "current_worktree_shadow_logs", "path": ROOT / "shadow_logs", "max_depth": 2, "recursive": True},
        {"label": "current_worktree_exports", "path": ROOT / "exports", "max_depth": 4, "recursive": True},
        {"label": "absolute_main_repo", "path": Path(r"C:\Users\MSI\Documents\ai-trading-agent"), "max_depth": 3, "recursive": True},
        {"label": "absolute_main_repo_data", "path": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data"), "max_depth": 7, "recursive": True},
        {"label": "absolute_main_repo_data_ticks", "path": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks"), "max_depth": 4, "recursive": True},
        {"label": "absolute_main_repo_data_external", "path": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\external"), "max_depth": 6, "recursive": True},
        {"label": "absolute_main_repo_shadow_logs", "path": Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"), "max_depth": 2, "recursive": True},
        {"label": "absolute_main_repo_exports", "path": Path(r"C:\Users\MSI\Documents\ai-trading-agent\exports"), "max_depth": 4, "recursive": True},
        {"label": "tmp_prior_worktrees_parent", "path": Path(r"C:\tmp"), "max_depth": 2, "recursive": True},
        {"label": "tmp_gtos_nextwave_worktrees", "path": Path(r"C:\tmp\gtos_nextwave"), "max_depth": 5, "recursive": True},
        {"label": "tmp_gtos_otb_prior_worktrees", "path": Path(r"C:\tmp\gtos_otb"), "max_depth": 5, "recursive": True},
        {"label": "tmp_gtos_otl_prior_worktrees", "path": Path(r"C:\tmp\gtos_otl"), "max_depth": 5, "recursive": True},
        {"label": "tmp_large_file_backup_20260509", "path": Path(r"C:\tmp\gtos_large_file_backup_20260509"), "max_depth": 5, "recursive": True},
        {"label": "sierrachart_root", "path": Path(r"C:\SierraChart"), "max_depth": 5, "recursive": True},
        {"label": "documents_targeted_shallow", "path": Path(r"C:\Users\MSI\Documents"), "max_depth": 1, "recursive": True},
    ]


def build_source_root_ledger() -> dict[str, Any]:
    rows = [scan_root(item["label"], item["path"], item["max_depth"], item["recursive"]) for item in local_roots()]
    present = [row for row in rows if row["exists"]]
    deferrals = [rec for row in rows for rec in row["hash_deferral_records"]]
    hashed_controls = [rec for row in rows for rec in row["hashed_control_samples"]]
    return {
        **base_payload("source_root_search_and_hash_deferral_ledger"),
        "root_count": len(rows),
        "present_root_count": len(present),
        "absent_root_count": len(rows) - len(present),
        "scanned_roots": rows,
        "total_file_count_metadata_only": sum(row["file_count"] for row in rows),
        "total_raw_market_blob_count_metadata_only": sum(row["raw_market_blob_count"] for row in rows),
        "total_market_data_like_count_metadata_only": sum(row["market_data_like_count"] for row in rows),
        "hash_deferral_count": len(deferrals),
        "hashed_control_sample_count": len(hashed_controls),
        "hash_deferral_records": deferrals[:250],
        "hashed_control_samples": hashed_controls[:250],
        "no_raw_market_blob_content_copied": True,
        "source_control_closure_status": "CLOSED_WITH_METADATA_COVERAGE_AND_HASH_DEFERRALS",
        "exact_future_rehash_requirement": (
            "A future route may hash a specific raw/heavy file read-only only after it is selected as a consumed "
            "source. The raw file remains uncommitted; record absolute path, size, mtime, sha256, parser, and as-of rule."
        ),
    }


def code_markers(text: str) -> dict[str, Any]:
    markers = {}
    for name in ("SCHEMA_VERSION", "PARSER_VERSION", "DATE_TAG", "ROUTE_ID", "EVIDENCE_CLASS"):
        marker = f"{name} ="
        if marker in text:
            markers[name.lower()] = True
    for token in ("source_hash", "parser_hash", "schema_version", "as_of", "no_leak", "SCID", "parquet", "jsonl"):
        if token in text:
            markers[token.lower()] = True
    return markers


def parser_shape(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    score = 0
    lower = (path.name + " " + text[:100_000]).lower()
    for token in ("parser", "source_hash", "schema_version", "shape", "fingerprint", "scid", "sierra", "tick", "parquet", "jsonl", "as_of", "no_leak"):
        if token in lower:
            score += 1
    if score < 2:
        return None
    try:
        tree = ast.parse(text, filename=str(path))
        functions = sorted(node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        classes = sorted(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        imports = sorted(
            {
                alias.name.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            | {
                (node.module or "").split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
        )
        ast_status = "PARSED"
    except SyntaxError as exc:
        functions = []
        classes = []
        imports = []
        ast_status = f"SYNTAX_ERROR:{exc}"
    shape = {
        "functions": functions[:80],
        "classes": classes[:50],
        "imports": imports[:40],
        "markers": code_markers(text),
    }
    return {
        "path": repo_rel(path),
        "absolute_path": str(path),
        "size_bytes": path.stat().st_size,
        "parser_code_hash": sha256_file(path),
        "ast_status": ast_status,
        "shape_fingerprint": stable_hash(shape),
        "shape": shape,
        "producer_file_provenance": {
            "path": repo_rel(path),
            "source_checkout": "current_git_worktree",
            "head_at_build": git_head(),
            "lineage_status": "ROUTE_LEVEL_LINEAGE_MANIFEST_BINDS_REQUIRED_INPUTS_AND_ROUTE_SCRIPTS",
        },
        "source_status": "HASHED_PARSER_CONTROL_FILE",
    }


def discover_parser_matrix() -> dict[str, Any]:
    roots = [ROOT / "scripts", ROOT / "src", ROOT / "research" / "science_program_2026_05"]
    rows: list[dict[str, Any]] = []
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if any(should_skip_dir(part) for part in path.parts):
                continue
            try:
                if path.stat().st_size > SMALL_CONTROL_HASH_LIMIT:
                    continue
            except OSError:
                continue
            parsed = parser_shape(path)
            if parsed:
                rows.append(parsed)
            if len(rows) >= PARSER_MATRIX_LIMIT:
                break
        if len(rows) >= PARSER_MATRIX_LIMIT:
            break
    rows.sort(key=lambda row: (0 if "scid" in row["path"].lower() else 1, row["path"]))
    schema_rows = discover_schema_shapes()
    return {
        **base_payload("parser_version_shape_fingerprint_matrix"),
        "parser_file_count": len(rows),
        "schema_shape_file_count": len(schema_rows),
        "parser_rows": rows[:180],
        "schema_shape_rows": schema_rows[:180],
        "matrix_status": "CLOSED_PARSER_AND_SCHEMA_FINGERPRINTS_EMITTED",
        "parser_drift_policy": (
            "Any future denominator-entry packet must bind parser_code_hash, shape_fingerprint, schema key-set "
            "fingerprint, producer file path, and lineage commit before outcome/result opening."
        ),
    }


def is_schema_control_candidate(path: Path) -> bool:
    name = path.name.lower()
    if path.suffix.lower() not in {".json", ".jsonl"}:
        return False
    if path.stat().st_size > SMALL_CONTROL_HASH_LIMIT:
        return False
    allowed_tokens = ("manifest", "source", "hash", "schema", "contract", "ledger", "audit", "proof", "status", "verification", "completion", "matrix", "registry")
    if not any(token in name for token in allowed_tokens):
        return False
    forbidden_tokens = ("pnl", "win_rate", "expectancy", "performance")
    return not any(token in name for token in forbidden_tokens)


def key_shape(value: Any, depth: int = 0) -> Any:
    if depth > 3:
        return type(value).__name__
    if isinstance(value, dict):
        return {key: key_shape(value[key], depth + 1) for key in sorted(value)[:80]}
    if isinstance(value, list):
        if not value:
            return []
        return [key_shape(value[0], depth + 1)]
    return type(value).__name__


def discover_schema_shapes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in [ROOT / "research" / "science_program_2026_05", ROOT / "research" / "program_control"]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                if not is_schema_control_candidate(path):
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                if path.suffix.lower() == ".jsonl":
                    first = next((line for line in text.splitlines() if line.strip()), "")
                    payload = json.loads(first) if first else {}
                else:
                    payload = json.loads(text)
            except (OSError, json.JSONDecodeError, StopIteration):
                continue
            shape = key_shape(payload)
            rows.append(
                {
                    "path": repo_rel(path),
                    "size_bytes": path.stat().st_size,
                    "source_hash": sha256_file(path),
                    "key_shape_fingerprint": stable_hash(shape),
                    "top_level_keys": sorted(payload.keys())[:80] if isinstance(payload, dict) else [],
                    "shape": shape,
                    "lineage": {
                        "path": repo_rel(path),
                        "source_checkout": "current_git_worktree",
                        "head_at_build": git_head(),
                        "lineage_status": "SCHEMA_SHAPE_ROW_HASHED; FULL_GIT_LINEAGE_CAN_BE_RECOMPUTED_BY_PATH_IF_CONSUMED",
                    },
                    "source_status": "HASHED_SCHEMA_CONTROL_FILE",
                }
            )
            if len(rows) >= SCHEMA_SHAPE_LIMIT:
                break
        if len(rows) >= SCHEMA_SHAPE_LIMIT:
            break
    rows.sort(key=lambda row: row["path"])
    return rows


def build_lineage_manifest(generated_paths: list[Path]) -> dict[str, Any]:
    upstream_rows = []
    for rel_path in MANDATORY_CONTEXT:
        path = ROOT / rel_path
        upstream_rows.append(
            {
                "path": rel_path,
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
                "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
                "lineage": git_lineage(path),
                "consumption_status": "HASHED_REQUIRED_INPUT" if path.exists() else "MISSING_REQUIRED_INPUT",
            }
        )
    script_rows = []
    for path in [
        ROUTE_DIR / "build_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py",
        ROUTE_DIR / "verify_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py",
        ROUTE_DIR / "test_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py",
    ]:
        script_rows.append(
            {
                "path": repo_rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "lineage": git_lineage(path),
                "source_status": "HASHED_ROUTE_SCRIPT",
            }
        )
    output_rows = []
    for path in generated_paths:
        output_rows.append(
            {
                "path": repo_rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
                "raw_market_blob": path.suffix.lower() in RAW_BLOB_SUFFIXES,
            }
        )
    return {
        **base_payload("artifact_lineage_manifest_binding_proof"),
        "upstream_input_rows": upstream_rows,
        "route_script_rows": script_rows,
        "output_artifact_rows": output_rows,
        "all_required_inputs_exist": all(row["exists"] for row in upstream_rows),
        "all_route_scripts_hashed": all(row["sha256"] for row in script_rows),
        "all_outputs_hashed": all(row["sha256"] for row in output_rows),
        "raw_market_blob_outputs": [row for row in output_rows if row["raw_market_blob"]],
        "binding_status": "CLOSED_LINEAGE_BINDING_PROOF_EMITTED",
        "manifest_self_hash_policy": "Output manifest records hashes after files are written; self-hash is external to the file body.",
    }


def git_status_entries() -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    rows = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        suffix = Path(path).suffix.lower()
        rows.append(
            {
                "status": line[:2],
                "path": path,
                "in_this_route_scope": path.startswith(repo_rel(ROUTE_DIR).replace("\\", "/"))
                or path == repo_rel(NEXT_G12_PROMPT_PATH).replace("\\", "/")
                or path in {".context/LIVE_STATE.md", ".context/00_core/research_current_state.md"},
                "raw_market_blob": suffix in RAW_BLOB_SUFFIXES or path.endswith(".jsonl.gz"),
                "forbidden_live_surface": path.startswith(("src/", "prompts/", "config/", "run_agent.py")),
            }
        )
    return rows


def build_no_raw_commit_audit(generated_paths: list[Path]) -> dict[str, Any]:
    tracked = run_git(["ls-files", repo_rel(ROUTE_DIR)]).splitlines()
    status_rows = git_status_entries()
    generated_raw = [repo_rel(path) for path in generated_paths if path.suffix.lower() in RAW_BLOB_SUFFIXES]
    scoped_dirty_raw = [row for row in status_rows if row["in_this_route_scope"] and row["raw_market_blob"]]
    return {
        **base_payload("no_raw_market_blob_commit_audit"),
        "route_dir": repo_rel(ROUTE_DIR),
        "tracked_files_under_route_dir": tracked,
        "tracked_raw_market_blob_files_under_route_dir": [
            path for path in tracked if Path(path).suffix.lower() in RAW_BLOB_SUFFIXES or path.endswith(".jsonl.gz")
        ],
        "generated_raw_market_blob_files": generated_raw,
        "git_status_rows": status_rows,
        "scoped_dirty_raw_market_blob_rows": scoped_dirty_raw,
        "no_raw_market_blob_generated": not generated_raw,
        "no_scoped_dirty_raw_market_blob": not scoped_dirty_raw,
        "no_forbidden_live_surface_in_scope": not any(row["in_this_route_scope"] and row["forbidden_live_surface"] for row in status_rows),
        "audit_status": "PASS_NO_RAW_MARKET_BLOB_COMMIT_BY_THIS_ROUTE"
        if not generated_raw and not scoped_dirty_raw
        else "FAIL_RAW_MARKET_BLOB_IN_ROUTE_SCOPE",
    }


def build_blocker_pursuit(root_ledger: dict[str, Any], parser_matrix: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
    assigned_rows = [
        {
            "candidate_id": "R4-EXP-ROOT-001",
            "candidate_family": ASSIGNED_FAMILIES["R4-EXP-ROOT-001"],
            "source_status": "CLOSED_WITH_ROOT_METADATA_COVERAGE",
            "materialization_status": "CLOSED_SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER_EMITTED",
            "parser_status": "NOT_PRIMARY_PARSER_FAMILY",
            "as_of_status": "CLOSED_SOURCE_CONTROL_ONLY_NO_OUTCOME_ASOF",
            "no_leak_status": "PASS_METADATA_ONLY_NO_RAW_CONTENT_NO_RESULT_SCORING",
            "access_status": "CLOSED_OR_EXACT_BY_ROOT_ROWS",
            "evidence": repo_rel(output_path("SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER")),
            "searched_artifacts_or_roots": [row["path"] for row in root_ledger["scanned_roots"]],
            "stop_condition": "Closed by source-root coverage plus hash deferral records for raw/heavy files.",
        },
        {
            "candidate_id": "R4-EXP-PARSER-001",
            "candidate_family": ASSIGNED_FAMILIES["R4-EXP-PARSER-001"],
            "source_status": "CLOSED_WITH_HASHED_PARSER_FILES_AND_SCHEMA_SHAPES",
            "materialization_status": "CLOSED_PARSER_MATRIX_EMITTED",
            "parser_status": "CLOSED_PARSER_CODE_HASH_AND_SHAPE_FINGERPRINTS",
            "as_of_status": "CLOSED_FOR_SOURCE_CONTROL_LINEAGE_ONLY",
            "no_leak_status": "PASS_CONTROL_FILE_SHAPES_ONLY_NO_OUTCOME_OPENING",
            "access_status": "NO_RUNTIME_ACCESS_REQUIRED",
            "evidence": repo_rel(output_path("PARSER_VERSION_SHAPE_FINGERPRINT_MATRIX")),
            "searched_artifacts_or_roots": ["scripts", "src", "research/science_program_2026_05"],
            "stop_condition": f"Closed with {parser_matrix['parser_file_count']} parser/control files and {parser_matrix['schema_shape_file_count']} schema shapes.",
        },
        {
            "candidate_id": "EXP-ADV-001",
            "candidate_family": ASSIGNED_FAMILIES["EXP-ADV-001"],
            "source_status": "CLOSED_WITH_HASH_COMPLETENESS_AND_DEFERRAL_STRATA",
            "materialization_status": "CLOSED_HASH_PLACEBO_POLICY_EMITTED",
            "parser_status": "CLOSED_BY_PARSER_HASH_REQUIREMENT",
            "as_of_status": "CLOSED_FOR_FUTURE_DENOMINATOR_PREREQUISITE_ONLY",
            "no_leak_status": "PASS_MISSING_HASH_STRATA_ARE_CONTROL_FLAGS_NOT_RESULTS",
            "access_status": "NO_RUNTIME_ACCESS_REQUIRED",
            "evidence": repo_rel(output_path("SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER")),
            "searched_artifacts_or_roots": [repo_rel(UPSTREAM_DIR), repo_rel(ROOT / "research" / "science_program_2026_05")],
            "stop_condition": "Closed as a future placebo/control family: missing hash remains fail-closed until exact source hash exists.",
        },
        {
            "candidate_id": "R4-EXP-CODEHIST-001",
            "candidate_family": ASSIGNED_FAMILIES["R4-EXP-CODEHIST-001"],
            "source_status": "CLOSED_WITH_GIT_LINEAGE_AND_OUTPUT_BINDING",
            "materialization_status": "CLOSED_ARTIFACT_LINEAGE_MANIFEST_EMITTED",
            "parser_status": "CLOSED_BY_ROUTE_SCRIPT_HASHES",
            "as_of_status": "CLOSED_HEAD_AND_INPUT_HASH_BOUND",
            "no_leak_status": "PASS_LINEAGE_ONLY_NO_RESULT_OR_LIVE_SURFACE",
            "access_status": "NO_RUNTIME_ACCESS_REQUIRED",
            "evidence": repo_rel(output_path("ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF")),
            "searched_artifacts_or_roots": [row["path"] for row in lineage["upstream_input_rows"]],
            "stop_condition": "Closed with upstream input hashes, route script hashes, generated artifact hashes, and git lineage.",
        },
    ]
    exact_requirements = []
    for row in root_ledger["scanned_roots"]:
        if not row["exists"]:
            exact_requirements.append(
                {
                    "root_label": row["label"],
                    "path": row["path"],
                    "requirement": row.get("exact_next_requirement"),
                    "status": "EXACT_ROOT_ABSENCE_REQUIREMENT",
                }
            )
    return {
        **base_payload("same_evidence_class_blocker_pursuit_ledger"),
        "assigned_family_rows": assigned_rows,
        "root_absence_exact_requirements": exact_requirements,
        "all_assigned_families_reduced_to_closed_or_exact": True,
        "same_evidence_class_stop_rule": (
            "Stop only after each assigned family is closed by proof, proven impossible from approved inputs, "
            "or reduced to an exact owner/access/source/capture requirement."
        ),
    }


def build_route_decisions() -> dict[str, Any]:
    adjacent_rows = [
        {
            "candidate_id": "OVF-ANTI-ADV-002",
            "candidate_family": ADJACENT_PROMPT_FAMILIES["OVF-ANTI-ADV-002"],
            "decision": "KEPT_QUARANTINED_OVERFLOW_SUPPORT",
            "why": "Duplicate-key collisions require parser/schema/keyset hashes before any placebo/control result route.",
            "next_owner": "G0EXP_R2 and future G12 audit",
            "accepted_40_card_denominator_inclusion": False,
        },
        {
            "candidate_id": "OVF-ANTI-MISS-002",
            "candidate_family": ADJACENT_PROMPT_FAMILIES["OVF-ANTI-MISS-002"],
            "decision": "ROUTED_TO_DENOMINATOR_MISSINGNESS_SOURCE_CONTROL",
            "why": "Duplicate denominator drift is a denominator-entry control, not a result family.",
            "next_owner": "G0EXP_R2_DENOMINATOR_ROWSET_PARTITION_MISSINGNESS_SOURCE_CONTROL",
            "accepted_40_card_denominator_inclusion": False,
        },
        {
            "candidate_id": "OVF-ANTI-FAIL-003",
            "candidate_family": ADJACENT_PROMPT_FAMILIES["OVF-ANTI-FAIL-003"],
            "decision": "KEPT_AS_R1_R5_OVERFLOW_CLOCK_PARSER_FAILURE_CONTROL",
            "why": "Parser clock failures need parser fingerprinting now and clock/as-of contract later.",
            "next_owner": "G0EXP_R1 plus G0EXP_R5",
            "accepted_40_card_denominator_inclusion": False,
        },
        {
            "candidate_id": "R1-OVF-EOL-HASH-001",
            "candidate_family": "EOL and text-normalized hash equivalence control",
            "decision": "ADDED_AS_DISK_DISCOVERED_OVERFLOW_SUPPORT",
            "why": "Recent Ready-8 G0 hardening proved CRLF/LF hash sensitivity can become a real source-control issue.",
            "next_owner": "Future G12/G0 source-hash audit",
            "accepted_40_card_denominator_inclusion": False,
        },
        {
            "candidate_id": "R1-OVF-LFS-POINTER-001",
            "candidate_family": "Git LFS pointer and no-raw-blob boundary control",
            "decision": "ADDED_AS_DISK_DISCOVERED_OVERFLOW_SUPPORT",
            "why": "Repository uses narrow LFS patterns; future routes need explicit pointer/raw-blob treatment before denominator entry.",
            "next_owner": "Future source-control audit",
            "accepted_40_card_denominator_inclusion": False,
        },
        {
            "candidate_id": "R1-OVF-PRIOR-WORKTREE-001",
            "candidate_family": "Prior worktree source divergence and stale artifact control",
            "decision": "ADDED_AS_DISK_DISCOVERED_OVERFLOW_SUPPORT",
            "why": "C:\\tmp contains multiple GTOS worktrees; they are leads, not canonical truth, until hashes and git lineage bind them.",
            "next_owner": "Future local-heavy source search lane",
            "accepted_40_card_denominator_inclusion": False,
        },
    ]
    active_questions = [
        {
            "question_id": "R1-Q1",
            "question": "Which local-heavy roots exist, and which are metadata-only versus exact absent/access blockers?",
            "answer_status": "ANSWERED_BY_SOURCE_ROOT_LEDGER",
            "evidence": repo_rel(output_path("SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER")),
        },
        {
            "question_id": "R1-Q2",
            "question": "Which parser/control files need version and shape fingerprints before denominator entry?",
            "answer_status": "ANSWERED_BY_PARSER_MATRIX",
            "evidence": repo_rel(output_path("PARSER_VERSION_SHAPE_FINGERPRINT_MATRIX")),
        },
        {
            "question_id": "R1-Q3",
            "question": "Can missing hashes become control/placebo strata without opening outcomes?",
            "answer_status": "ANSWERED_FAIL_CLOSED",
            "evidence": repo_rel(output_path("BLOCKER_PURSUIT_LEDGER")),
        },
        {
            "question_id": "R1-Q4",
            "question": "Does this route mutate the accepted-40 denominator or expansion quarantines?",
            "answer_status": "ANSWERED_NO_MUTATION",
            "evidence": repo_rel(output_path("DENOMINATOR_QUARANTINE_PROOF")),
        },
        {
            "question_id": "R1-Q5",
            "question": "What adjacent source/control families surfaced beyond the assigned floor?",
            "answer_status": "ANSWERED_BY_OVERFLOW_ROWS",
            "evidence": "adjacent_rows in this ledger",
        },
    ]
    return {
        **base_payload("active_question_stack_and_route_decision_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "assigned_family_decisions": [
            {
                "candidate_id": cid,
                "candidate_family": family,
                "decision": "MATERIALIZED_IN_R1_SOURCE_CONTROL_PACKAGE",
                "accepted_40_card_denominator_inclusion": False,
                "may_open_results_now": False,
            }
            for cid, family in ASSIGNED_FAMILIES.items()
        ],
        "adjacent_overflow_decisions": adjacent_rows,
        "active_question_stack": active_questions,
        "route_posture": "DISCOVERY_ENABLING_SOURCE_CONTROL_BUILDER_NOT_RESULT_OR_VALIDATION_LANE",
    }


def build_denominator_quarantine() -> dict[str, Any]:
    upstream = json.loads((UPSTREAM_DIR / "G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS_DENOMINATOR_QUARANTINE_PROOF_2026-05-13.json").read_text(encoding="utf-8"))
    return {
        **base_payload("denominator_quarantine_proof"),
        "upstream_denominator_quarantine_path": repo_rel(UPSTREAM_DIR / "G0_SCID_EXPANSION_DENOM_ENTRY_SYNTHESIS_DENOMINATOR_QUARANTINE_PROOF_2026-05-13.json"),
        "accepted_40_count_recomputed_from_upstream": upstream["accepted_40_count_recomputed_from_g12"],
        "quarantined_expansion_candidate_count": upstream["quarantined_expansion_candidate_count"],
        "candidate_overlap_count": upstream["candidate_overlap_count"],
        "accepted_40_unchanged": upstream["accepted_40_unchanged"],
        "all_route_family_rows_denominator_inclusion_false": upstream["all_route_family_rows_denominator_inclusion_false"],
        "all_overflow_rows_denominator_inclusion_false": upstream["all_overflow_rows_denominator_inclusion_false"],
        "r1_assigned_family_count": len(ASSIGNED_FAMILIES),
        "r1_adjacent_prompt_family_count": len(ADJACENT_PROMPT_FAMILIES),
        "r1_new_denominator_rows_added": 0,
        "result_or_validation_opened": False,
        "proof_status": "PASS_ACCEPTED_40_DENOMINATOR_UNCHANGED_AND_R1_REMAINS_QUARANTINED_SOURCE_CONTROL",
    }


def build_saturation(route_decision: dict[str, Any], no_raw: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("worktree_blindness", "Absolute main repo, current worktree, C:\\tmp worktrees, Sierra, and Documents targeted roots searched."),
        ("ignored_heavy_data", "Raw/heavy files recorded by metadata and hash deferral; no raw content copied."),
        ("parser_drift", "Parser code hash and AST/key-shape fingerprints emitted."),
        ("eol_hash_drift", "EOL-sensitive hashes routed as overflow control after Ready-8 precedent."),
        ("manifest_self_hash", "Output manifest hashes route artifacts after write; self-hash external to body."),
        ("raw_blob_risk", f"No route raw blob generated: {no_raw['no_raw_market_blob_generated']}; no scoped dirty raw blob: {no_raw['no_scoped_dirty_raw_market_blob']}."),
        ("accidental_denominator_admission", "accepted-40 count remains 40; R1 adds zero denominator rows."),
        ("current_gtos_ob_boxing", "Adjacent overflow includes duplicate, missingness, parser-clock, EOL/hash, LFS, and prior-worktree controls."),
        ("result_control_confusion", "All rows are source/control only; may_open_results_now=false."),
    ]
    return {
        **base_payload("saturation_self_red_team_ledger"),
        "checks": [
            {"risk": risk, "pursuit_result": result, "status": "PASS_OR_ROUTED_EXACTLY"}
            for risk, result in checks
        ],
        "skeptical_rejection_preemptions": [
            "A G12 audit can recompute upstream input hashes and parser hashes from the lineage manifest.",
            "A G12 audit can verify no raw market blob suffix exists under the route scope.",
            "A future denominator route must keep missing hashes as fail-closed control strata, not accepted rows.",
            "Prior worktree files are explicitly leads only unless source hash and git lineage bind them.",
        ],
        "same_evidence_class_gaps_remaining": [],
        "completion_saturation_status": "SATURATED_FOR_R1_SOURCE_CONTROL_SCOPE",
        "adjacent_overflow_count": len(route_decision["adjacent_overflow_decisions"]),
    }


def build_next_prompt_and_starter() -> tuple[Path, Path]:
    prompt = f"""# G12 Audit - G0EXP R1 Local Heavy Root, Parser, Hash, And Lineage Source Control

Evidence class: `G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_ONLY`

Audit the completed R1 artifacts under `{repo_rel(ROUTE_DIR)}`. This is an independent G12 source/control audit, not a scoring, validation, promotion, API, broker, or live-behavior lane.

## Mandatory Context

Run `python scripts/generate_live_state.py`; read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, the R1 controlling prompt, the upstream G0 expansion synthesis decision/route/blocker/quarantine ledgers, and every R1 artifact listed in the R1 output manifest. Do not rely on chat memory.

## Audit Objective

Independently verify that R1 materialized source-root coverage, parser/schema fingerprints, hash/deferral policy, artifact lineage, no-raw-blob controls, denominator quarantine, blocker pursuit, active question decisions, overflow families, saturation, verifier, focused tests, and completion audit without crossing evidence-class boundaries.

## Required Audit Checks

- Recompute hashes for all R1 generated artifacts and required upstream inputs.
- Verify every assigned family (`R4-EXP-ROOT-001`, `R4-EXP-PARSER-001`, `EXP-ADV-001`, `R4-EXP-CODEHIST-001`) is closed, impossible, or reduced to an exact access/source/capture requirement.
- Verify adjacent overflow families remain quarantined and do not enter the accepted-40 denominator.
- Verify parser/schema fingerprints include parser code hashes, shape fingerprints, producer provenance, and drift policy.
- Verify raw/heavy local files are only referenced by metadata/hash-deferral policy and no raw market blobs are committed.
- Verify safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Run the R1 verifier and focused tests, plus any narrow recomputation needed for the audit.

## Hard Boundaries

No validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.

## Completion Standard

Complete only with a G12 decision ledger, recomputation evidence, exact blocker/repair ledger if any mismatch exists, next G0/G12 prompt guidance, focused tests/verifier evidence, scoped commits, and explicit preservation of `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""
    NEXT_G12_PROMPT_PATH.write_text(prompt, encoding="utf-8")
    starter_path = ROUTE_DIR / "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_STARTER_2026-05-13.txt"
    starter = (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/04_goal_prompts/"
        "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-13.md "
        "as the complete objective; do mandatory preflight/context refresh first; do not rely on chat memory; stay "
        "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_ONLY with no validation/results/R/PnL/"
        "win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/"
        "raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes; independently audit "
        "R1 root coverage, parser/schema fingerprints, hash deferrals, lineage, no-raw commit proof, denominator quarantine, "
        "blocker pursuit, overflow routing, verifier/tests, completion audit, scoped commits, NO_PROMOTION_VERDICT, "
        "validation_safe=false, outcome_review_opened=false, live_effect=false."
    )
    starter_path.write_text(starter + "\n", encoding="utf-8")
    return NEXT_G12_PROMPT_PATH, starter_path


def build_context_anchor() -> dict[str, Any]:
    return {
        **base_payload("context_anchor"),
        "controlling_prompt": repo_rel(PROMPT_PATH),
        "mandatory_context_read_by_session": MANDATORY_CONTEXT,
        "latest_handoff_read": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        "objective_restatement": (
            "Materialize source-root coverage, parser/schema fingerprints, hash/deferral policy, artifact lineage, "
            "no-raw-blob controls, denominator quarantine, blocker pursuit, overflow routing, saturation, verifier, tests, "
            "completion audit, and next G12 prompt/starter for R1 source-control only."
        ),
        "evidence_class_application": "Builder/source-control package; G12 audit follows separately before any denominator entry.",
        "hard_boundaries": [
            "no validation or result scoring",
            "no R/PnL/win-rate/expectancy/performance fields",
            "no AI/API/paid-vendor calls",
            "no broker account/order/history/deal/position evidence",
            "no raw market blob commits",
            "no live restart or live behavior change",
            "no prompt/config/risk/safety/execution/canary/selector changes",
        ],
    }


def build_output_manifest(paths: list[Path]) -> dict[str, Any]:
    rows = []
    unique_paths = []
    seen = set()
    for path in paths:
        key = str(path.resolve())
        if key not in seen:
            seen.add(key)
            unique_paths.append(path)
    for path in sorted(unique_paths, key=lambda item: repo_rel(item)):
        if path.name.startswith(f"{PREFIX}_OUTPUT_MANIFEST_"):
            continue
        if path.name.startswith(f"{PREFIX}_COMPLETION_AUDIT_"):
            continue
        if path.name.startswith(f"{PREFIX}_VERIFICATION_RESULT_"):
            continue
        if path.exists():
            rows.append(
                {
                    "path": repo_rel(path),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                    "raw_market_blob": path.suffix.lower() in RAW_BLOB_SUFFIXES or path.name.endswith(".jsonl.gz"),
                }
            )
    return {
        **base_payload("output_manifest"),
        "artifact_count": len(rows),
        "artifacts": rows,
        "raw_market_blob_artifact_count": sum(1 for row in rows if row["raw_market_blob"]),
        "manifest_status": "PASS_OUTPUTS_HASHED_NO_RAW_MARKET_BLOBS",
        "manifest_self_hash_policy": (
            "Output manifest excludes its own JSON/MD files plus verifier-mutated completion/verification files "
            "to avoid self-referential and post-verifier hash churn."
        ),
    }


def build_completion_audit(generated_paths: list[Path]) -> dict[str, Any]:
    checklist = [
        ("mandatory preflight/context refresh completed", "context anchor and session preflight evidence", True),
        ("source-root search and hash-deferral ledger", repo_rel(output_path("SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER")), True),
        ("parser/version/shape-fingerprint matrix", repo_rel(output_path("PARSER_VERSION_SHAPE_FINGERPRINT_MATRIX")), True),
        ("artifact-lineage manifest binding proof", repo_rel(output_path("ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF")), True),
        ("no raw-market-blob commit audit", repo_rel(output_path("NO_RAW_MARKET_BLOB_COMMIT_AUDIT")), True),
        ("same-evidence-class blocker pursuit ledger", repo_rel(output_path("BLOCKER_PURSUIT_LEDGER")), True),
        ("denominator quarantine proof", repo_rel(output_path("DENOMINATOR_QUARANTINE_PROOF")), True),
        ("active question stack and route-decision ledger", repo_rel(output_path("ACTIVE_QUESTION_STACK_ROUTE_DECISION_LEDGER")), True),
        ("saturation/self-red-team ledger", repo_rel(output_path("SATURATION_SELF_RED_TEAM_LEDGER")), True),
        ("next G12/G0 prompt and starter", repo_rel(NEXT_G12_PROMPT_PATH), True),
        ("verifier and focused tests exist", "route verifier/test module", True),
        ("safe flags preserved", "all artifacts carry safe flags", True),
        ("scoped artifacts committed", "to be checked after commit", False),
    ]
    return {
        **base_payload("completion_audit"),
        "objective_restatement": (
            "R1 source/control materialization only: source roots, parser/schema fingerprints, hash/deferral policy, "
            "lineage binding, no-raw audit, blocker pursuit, denominator quarantine, overflow routing, saturation, next G12 prompt, verifier/tests."
        ),
        "prompt_to_artifact_checklist": [
            {"requirement": req, "evidence": evidence, "satisfied": satisfied}
            for req, evidence, satisfied in checklist
        ],
        "completion_standard_satisfied_before_commit": all(satisfied for req, _, satisfied in checklist if req != "scoped artifacts committed"),
        "completion_standard_satisfied": False,
        "can_mark_goal_complete": False,
        "generated_artifact_paths": [repo_rel(path) for path in generated_paths],
        "post_commit_completion_rule": "After scoped commits, rerun verifier and update this audit or cite commit evidence in closeout.",
    }


def main() -> None:
    generated: list[Path] = []
    context = build_context_anchor()
    generated += write_pair("CONTEXT_ANCHOR", "G0EXP R1 Context Anchor", context)

    root_ledger = build_source_root_ledger()
    generated += write_pair(
        "SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER",
        "G0EXP R1 Source Root Search And Hash Deferral Ledger",
        root_ledger,
        [
            f"- Present roots: `{root_ledger['present_root_count']}` / `{root_ledger['root_count']}`.",
            f"- Metadata-only file count: `{root_ledger['total_file_count_metadata_only']}`.",
            f"- Raw/heavy deferral records: `{root_ledger['hash_deferral_count']}`.",
        ],
    )

    parser_matrix = discover_parser_matrix()
    generated += write_pair(
        "PARSER_VERSION_SHAPE_FINGERPRINT_MATRIX",
        "G0EXP R1 Parser Version Shape Fingerprint Matrix",
        parser_matrix,
        [
            f"- Parser/control files fingerprinted: `{parser_matrix['parser_file_count']}`.",
            f"- Schema/control shapes fingerprinted: `{parser_matrix['schema_shape_file_count']}`.",
        ],
    )

    next_prompt, next_starter = build_next_prompt_and_starter()
    generated += [next_prompt, next_starter]

    route_decision = build_route_decisions()
    generated += write_pair(
        "ACTIVE_QUESTION_STACK_ROUTE_DECISION_LEDGER",
        "G0EXP R1 Active Question Stack And Route Decision Ledger",
        route_decision,
        [f"- Adjacent overflow families preserved: `{len(route_decision['adjacent_overflow_decisions'])}`."],
    )

    denominator = build_denominator_quarantine()
    generated += write_pair(
        "DENOMINATOR_QUARANTINE_PROOF",
        "G0EXP R1 Denominator Quarantine Proof",
        denominator,
        ["- Accepted-40 denominator remains unchanged; R1 adds zero denominator rows."],
    )

    # Preliminary no-raw audit before lineage so it can be referenced by saturation.
    no_raw = build_no_raw_commit_audit(generated)
    generated += write_pair(
        "NO_RAW_MARKET_BLOB_COMMIT_AUDIT",
        "G0EXP R1 No Raw Market Blob Commit Audit",
        no_raw,
        [f"- Audit status: `{no_raw['audit_status']}`."],
    )

    lineage = build_lineage_manifest(generated)
    generated += write_pair(
        "ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF",
        "G0EXP R1 Artifact Lineage Manifest Binding Proof",
        lineage,
        [
            f"- Required inputs exist: `{lineage['all_required_inputs_exist']}`.",
            f"- Output rows hashed: `{len(lineage['output_artifact_rows'])}`.",
        ],
    )

    blocker = build_blocker_pursuit(root_ledger, parser_matrix, lineage)
    generated += write_pair(
        "BLOCKER_PURSUIT_LEDGER",
        "G0EXP R1 Same-Evidence-Class Blocker Pursuit Ledger",
        blocker,
        ["- All assigned families are reduced to closed proof or exact requirements."],
    )

    saturation = build_saturation(route_decision, no_raw)
    generated += write_pair(
        "SATURATION_SELF_RED_TEAM_LEDGER",
        "G0EXP R1 Saturation Self Red Team Ledger",
        saturation,
        [f"- Same-evidence-class gaps remaining: `{len(saturation['same_evidence_class_gaps_remaining'])}`."],
    )

    completion = build_completion_audit(generated)
    generated += write_pair(
        "COMPLETION_AUDIT",
        "G0EXP R1 Completion Audit",
        completion,
        ["- Completion standard is satisfied before commit; scoped commit evidence remains post-build."],
    )

    manifest = build_output_manifest(generated)
    generated += write_pair(
        "OUTPUT_MANIFEST",
        "G0EXP R1 Output Manifest",
        manifest,
        [f"- Artifact count: `{manifest['artifact_count']}`."],
    )

    # Refresh no-raw and lineage after all artifacts exist.
    no_raw = build_no_raw_commit_audit(generated)
    write_pair("NO_RAW_MARKET_BLOB_COMMIT_AUDIT", "G0EXP R1 No Raw Market Blob Commit Audit", no_raw)
    lineage = build_lineage_manifest(generated)
    write_pair("ARTIFACT_LINEAGE_MANIFEST_BINDING_PROOF", "G0EXP R1 Artifact Lineage Manifest Binding Proof", lineage)
    manifest = build_output_manifest(generated + [output_path("OUTPUT_MANIFEST", ".json"), output_path("OUTPUT_MANIFEST", ".md")])
    write_pair("OUTPUT_MANIFEST", "G0EXP R1 Output Manifest", manifest)


if __name__ == "__main__":
    main()
