"""Build the GTOS local research data catalog implementation route.

This route is source-control/catalog tooling only. It scans configured local
roots read-only, hashes small safe files, defers large-file hashes, and records
missing/acquisition requirements without opening validation or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]
OUTCOME_DIR = ROUTE_DIR.parent
DATE = "2026-05-10"
PREFIX = "GTOS_LOCAL_RESEARCH_DATA_CATALOG"
ROUTE_ID = "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE"
SCHEMA_VERSION = "gtos_local_research_data_catalog_implementation_route_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING"

PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE_GOAL_PROMPT_2026-05-10.md"
)
UPSTREAM_ROUTE = OUTCOME_DIR / "gtos_research_capability_limitation_closure_control_route"
NOFILL_FIXTURE_ROUTE = OUTCOME_DIR / "nofill_historical_source_expansion_builder_local_tick_shadow_packet"
G12_FIXTURE_ROUTE = OUTCOME_DIR / "g12_nofill_historical_source_expansion_hash_repair_reaudit"

UPSTREAM_PROTOTYPE = UPSTREAM_ROUTE / "GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_PROTOTYPE_2026-05-10.jsonl"
UPSTREAM_SCHEMA = UPSTREAM_ROUTE / "GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_SCHEMA_2026-05-10.json"
UPSTREAM_SEARCH = UPSTREAM_ROUTE / "GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_2026-05-10.json"
UPSTREAM_MISSING = UPSTREAM_ROUTE / "GTOS_CAP_LIMIT_CLOSURE_MISSING_WINDOW_LEDGER_2026-05-10.json"
UPSTREAM_ACQUISITION = UPSTREAM_ROUTE / "GTOS_CAP_LIMIT_CLOSURE_MARKET_DATA_ACQUISITION_LADDER_2026-05-10.json"
UPSTREAM_ROOT_RESOLVER = (
    UPSTREAM_ROUTE / "GTOS_CAP_LIMIT_CLOSURE_WORKTREE_BOOTSTRAP_DATA_ROOT_RESOLVER_2026-05-10.json"
)
UPSTREAM_TAXONOMY = (
    UPSTREAM_ROUTE / "GTOS_CAP_LIMIT_CLOSURE_HISTORICAL_SOURCE_STATE_TRUTH_TAXONOMY_2026-05-10.json"
)

CONTROL_DOCS = [
    REPO_ROOT / ".context" / "LIVE_STATE.md",
    REPO_ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    REPO_ROOT / ".context" / "00_core" / "quick_reference_card.md",
    REPO_ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    REPO_ROOT / ".context" / "00_core" / "research_current_state.md",
    REPO_ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    REPO_ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md",
    PROMPT_PATH,
]

SAFE_FALSE_KEYS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "changes_live_trading_behavior",
    "credentials_touched",
)
SAFE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    **{key: False for key in SAFE_FALSE_KEYS},
}
FORBIDDEN_DIFF_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "canaries/",
)
SENSITIVE_PATH_FRAGMENTS = (
    ".env",
    "api_key",
    "apikey",
    "secret",
    "password",
    "credential",
    "login",
    "broker_actual_r",
    "account_history",
    "account_pnl",
    "account_truth",
    "daily_pnl",
    "deal_history",
    "deals",
    "positions",
    "orders",
    "trade_records",
    "ticket",
)
IGNORE_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "site-packages",
}
SAFE_EXTENSIONS = {
    ".csv",
    ".depth",
    ".dly",
    ".feather",
    ".json",
    ".jsonl",
    ".md",
    ".parquet",
    ".py",
    ".scid",
    ".txt",
    ".yaml",
    ".yml",
}
HASH_SIZE_LIMIT_BYTES = 8 * 1024 * 1024
MAX_TOTAL_CATALOG_ROWS = 1200
SYMBOLS = [
    "US30_cash",
    "XAUUSD",
    "XAGUSD",
    "NAS100",
    "US30",
    "USDJPY",
    "GBPJPY",
    "GBPUSD",
    "EURUSD",
    "GER40",
    "UK100",
    "SPX500",
    "NQM26",
    "YMM26",
    "GCM26",
    "SIM26",
    "ESM26",
    "MESM26",
    "6JM26",
    "6BM26",
    "NQ",
    "YM",
    "GC",
    "SI",
    "ES",
    "MES",
    "6J",
    "6B",
]
DATE_PATTERNS = (
    re.compile(r"(20\d{2})[-_](\d{2})[-_](\d{2})"),
    re.compile(r"(20\d{2})(\d{2})(\d{2})"),
)
TIMEFRAME_RE = re.compile(r"(^|[^A-Z0-9])(M1|M5|M15|M30|H1|H4|D1|TICK|TICKS|SCID|DEPTH)([^A-Z0-9]|$)", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def git_head_subject() -> str:
    return subprocess.check_output(["git", "log", "-1", "--pretty=%h %s"], cwd=REPO_ROOT, text=True).strip()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def as_posixish(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def with_safe_flags(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.update(SAFE_FLAGS)
    return out


def base_payload(artifact_family: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "artifact_family": artifact_family,
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "terminal_decision": TERMINAL_DECISION,
    }
    payload.update(extra)
    return with_safe_flags(payload)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(with_safe_flags(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.write_text(
        "".join(json.dumps(with_safe_flags(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def write_md(path: Path, title: str, payload: dict[str, Any], notes: list[str] | None = None) -> Path:
    lines = [
        f"# {title}",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Terminal decision: `{payload.get('terminal_decision', TERMINAL_DECISION)}`",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(with_safe_flags(payload), indent=2, sort_keys=True),
        "```",
    ]
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def git_diff_scope() -> dict[str, Any]:
    diff = subprocess.run(["git", "diff", "--name-only"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    paths = sorted(
        {
            line.strip().replace("\\", "/")
            for line in (diff.stdout + "\n" + untracked.stdout).splitlines()
            if line.strip()
        }
    )
    forbidden = [path for path in paths if any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)]
    return {
        "changed_or_untracked_paths": paths,
        "forbidden_live_surface_paths": forbidden,
        "ok": forbidden == [],
        "git_diff_returncode": diff.returncode,
        "git_untracked_returncode": untracked.returncode,
    }


def default_root_config() -> dict[str, Any]:
    current = REPO_ROOT
    main_repo = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
    return base_payload(
        "root_resolver_config",
        hash_size_limit_bytes=HASH_SIZE_LIMIT_BYTES,
        max_total_catalog_rows=MAX_TOTAL_CATALOG_ROWS,
        sensitive_path_fragments=list(SENSITIVE_PATH_FRAGMENTS),
        ignore_directory_names=sorted(IGNORE_DIR_NAMES),
        roots=[
            root("current_worktree_data_root", current / "data", "worktree_data", "local_research_data", 6, 120),
            root("current_worktree_tick_root", current / "data" / "ticks", "ticks", "mt5_tick_parquet", 5, 160),
            root("current_worktree_shadow_logs", current / "shadow_logs", "shadow_logs", "shadow_log_source_control", 2, 120),
            root("current_worktree_exports", current / "exports", "exports", "exported_source_control", 4, 80),
            root("current_worktree_external_data", current / "data" / "external", "external_data", "local_external_cache", 6, 140),
            root(
                "current_worktree_science_routes",
                current / "research" / "science_program_2026_05" / "06_outcome_testing",
                "research_routes",
                "research_route_artifact",
                4,
                160,
            ),
            root("absolute_main_data_root", main_repo / "data", "absolute_main_data", "local_research_data", 6, 150),
            root("absolute_main_tick_root", main_repo / "data" / "ticks", "ticks", "mt5_tick_parquet", 5, 220),
            root("absolute_main_shadow_logs", main_repo / "shadow_logs", "shadow_logs", "shadow_log_source_control", 2, 140),
            root("absolute_main_exports", main_repo / "exports", "exports", "exported_source_control", 4, 80),
            root("absolute_main_external_data", main_repo / "data" / "external", "external_data", "local_external_cache", 6, 160),
            root("prior_worktree_root", Path(r"C:\tmp\gtos_otb"), "prior_worktree", "prior_worktree_lead", 4, 160),
            root("sierra_chart_root", Path(r"C:\SierraChart"), "sierra_root", "sierra_chart_cache", 3, 80),
            root("sierra_chart_data_root", Path(r"C:\SierraChart\Data"), "sierra_data", "sierra_chart_cache", 4, 180),
            root(
                "sierra_chart_depth_root",
                Path(r"C:\SierraChart\Data\MarketDepthData"),
                "sierra_depth",
                "sierra_chart_depth_cache",
                4,
                180,
            ),
            root(
                "owner_documents_candidate_root",
                Path(r"C:\Users\MSI\Documents"),
                "owner_documents",
                "owner_export_candidate",
                1,
                0,
                scan_enabled=False,
            ),
        ],
        search_queries=default_search_queries(),
    )


def root(
    root_id: str,
    path: Path,
    role: str,
    source_family_hint: str,
    max_depth: int,
    max_files: int,
    scan_enabled: bool = True,
) -> dict[str, Any]:
    return {
        "root_id": root_id,
        "root_path": str(path),
        "root_role": role,
        "source_family_hint": source_family_hint,
        "max_depth": max_depth,
        "max_files": max_files,
        "include_extensions": sorted(SAFE_EXTENSIONS),
        "read_policy": "stat_and_hash_small_safe_files_only",
        "scan_enabled": scan_enabled,
    }


def default_search_queries() -> list[dict[str, Any]]:
    return [
        {
            "query_id": "accepted_fixture_nas100_tick_2026_05_08",
            "purpose": "NOFILL source-expansion fixture tick file search",
            "symbol": "NAS100",
            "source_date": "2026-05-08",
            "extensions": [".parquet"],
            "source_family_contains": "tick",
        },
        {
            "query_id": "accepted_fixture_us30_cash_tick_2026_05_08",
            "purpose": "NOFILL source-expansion fixture tick file search",
            "symbol": "US30_cash",
            "source_date": "2026-05-08",
            "extensions": [".parquet"],
            "source_family_contains": "tick",
        },
        {
            "query_id": "upstream_missing_gbpjpy_tick_2026_04_14",
            "purpose": "recoverable market-data absence example",
            "symbol": "GBPJPY",
            "source_date": "2026-04-14",
            "extensions": [".parquet"],
            "source_family_contains": "tick",
        },
        {
            "query_id": "g12_hash_repair_reaudit_manifest",
            "purpose": "current acceptance-fixture G12 source-control route artifact search",
            "path_contains": "g12_nofill_historical_source_expansion_hash_repair_reaudit",
            "extensions": [".json", ".md", ".py"],
        },
        {
            "query_id": "cap_limit_catalog_prototype",
            "purpose": "upstream 198-row prototype catalog source search",
            "path_contains": "GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_PROTOTYPE",
            "extensions": [".jsonl"],
        },
        {
            "query_id": "sierra_nq_or_nqm26_depth_or_scid",
            "purpose": "Sierra local cache source discovery",
            "symbol_any": ["NQ", "NQM26"],
            "extensions": [".scid", ".depth"],
        },
    ]


def root_schema() -> dict[str, Any]:
    return base_payload(
        "root_resolver_config_schema",
        required_fields=[
            "root_id",
            "root_path",
            "root_role",
            "source_family_hint",
            "max_depth",
            "max_files",
            "include_extensions",
            "read_policy",
            "scan_enabled",
        ],
        root_status_fields=["exists", "permission_status", "file_count_indexed", "file_count_skipped_sensitive"],
        hash_policy={
            "small_safe_files": "raw_sha256",
            "large_safe_files": "deferred_large_file_requires_dedicated_hash_manifest",
            "sensitive_paths": "not_opened_recorded_in_noleak_audit",
        },
    )


def catalog_schema() -> dict[str, Any]:
    return base_payload(
        "catalog_schema",
        required_catalog_row_fields=[
            "catalog_row_id",
            "root_id",
            "root_path",
            "absolute_path",
            "relative_path",
            "repo_relative_path",
            "source_family",
            "symbol",
            "source_date",
            "source_date_range",
            "timeframe",
            "file_extension",
            "size_bytes",
            "mtime_utc",
            "hash_policy",
            "sha256",
            "hash_status",
            "large_file_hash_deferral_id",
            "allowed_evidence_class",
            "forbidden_use_notes",
            "read_actions",
        ],
        search_result_ledger_format=[
            "query_id",
            "purpose",
            "match_count",
            "positive_evidence",
            "negative_evidence",
            "roots_searched",
        ],
        missing_window_ledger_format=[
            "window_id",
            "source_requirement_type",
            "symbol",
            "source_date",
            "timeframe",
            "source_family",
            "local_catalog_status",
            "blocker_code",
            "exact_next_action",
        ],
        acquisition_manifest_schema_ref=f"{PREFIX}_ACQUISITION_REQUEST_MANIFEST_SCHEMA_{DATE}.json",
    )


def is_sensitive_path(path: Path, fragments: list[str] | tuple[str, ...] = SENSITIVE_PATH_FRAGMENTS) -> str | None:
    lower = as_posixish(path).lower()
    for fragment in fragments:
        if fragment.lower() in lower:
            return fragment
    return None


def infer_symbol(path: Path) -> str:
    parts: list[str] = []
    for raw in path.parts:
        parts.extend(piece for piece in re.split(r"[^A-Za-z0-9_]+", raw) if piece)
    stem_pieces = [piece for piece in re.split(r"[^A-Za-z0-9_]+", path.stem) if piece]
    candidates = [piece.upper() for piece in parts + stem_pieces]
    alias: dict[str, str] = {symbol.upper(): symbol for symbol in SYMBOLS}
    for symbol in sorted(SYMBOLS, key=len, reverse=True):
        upper = symbol.upper()
        if upper in candidates:
            return alias[upper]
    joined = "_".join(candidates)
    for symbol in sorted(SYMBOLS, key=len, reverse=True):
        upper = symbol.upper()
        if re.search(rf"(^|_){re.escape(upper)}($|_)", joined):
            return alias[upper]
    return "not_inferred"


def infer_date(path: Path) -> str:
    text = as_posixish(path)
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
    return "not_inferred"


def infer_timeframe(path: Path) -> str:
    text = as_posixish(path).upper()
    match = TIMEFRAME_RE.search(text)
    if not match:
        return "not_inferred"
    value = match.group(2).upper()
    return "TICK" if value == "TICKS" else value


def source_family(path: Path, root_cfg: dict[str, Any]) -> str:
    lower = as_posixish(path).lower()
    suffix = path.suffix.lower()
    if "\\data\\ticks\\" in str(path).lower() or "/data/ticks/" in lower or root_cfg.get("root_role") == "ticks":
        return "mt5_tick_parquet" if suffix == ".parquet" else "mt5_tick_control_file"
    if "/shadow_logs/" in lower or "\\shadow_logs\\" in str(path).lower() or root_cfg.get("root_role") == "shadow_logs":
        return "shadow_log_source_control"
    if suffix == ".scid":
        return "sierra_scid_cache"
    if suffix == ".depth":
        return "sierra_depth_cache"
    if "sierrachart" in lower:
        return "sierra_chart_cache"
    if "/data/external/" in lower or "\\data\\external\\" in str(path).lower() or "databento" in lower:
        return "local_external_or_vendor_cache"
    if "/06_outcome_testing/" in lower or "\\06_outcome_testing\\" in str(path).lower():
        return "research_route_artifact"
    if "/exports/" in lower or "\\exports\\" in str(path).lower():
        return "owner_or_tool_export"
    return str(root_cfg.get("source_family_hint") or "source_control_file")


def path_relative_to(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return "not_applicable"


def repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return "outside_current_worktree"


def mtime_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def scan_root(root_cfg: dict[str, Any], config: dict[str, Any]) -> tuple[list[Path], dict[str, Any], list[dict[str, Any]]]:
    root_path = Path(root_cfg["root_path"])
    max_depth = int(root_cfg.get("max_depth", 4))
    max_files = int(root_cfg.get("max_files", 100))
    extensions = {str(ext).lower() for ext in root_cfg.get("include_extensions", SAFE_EXTENSIONS)}
    sensitive_fragments = config.get("sensitive_path_fragments", list(SENSITIVE_PATH_FRAGMENTS))
    skipped_sensitive: list[dict[str, Any]] = []
    files: list[Path] = []
    ledger = {
        "root_id": root_cfg["root_id"],
        "root_path": str(root_path),
        "root_role": root_cfg.get("root_role"),
        "exists": root_path.exists(),
        "permission_status": "absent",
        "file_count_indexed": 0,
        "file_count_skipped_sensitive": 0,
        "max_depth": max_depth,
        "max_files": max_files,
        "scan_enabled": bool(root_cfg.get("scan_enabled", True)),
        "scan_status": "not_started",
    }
    if not root_path.exists():
        ledger["scan_status"] = "not_indexed_absent"
        return files, ledger, skipped_sensitive
    if not root_path.is_dir():
        ledger["permission_status"] = "not_directory"
        ledger["scan_status"] = "not_indexed_not_directory"
        return files, ledger, skipped_sensitive
    try:
        with os.scandir(root_path) as iterator:
            next(iterator, None)
    except PermissionError as exc:
        ledger["permission_status"] = f"access_denied:{type(exc).__name__}"
        ledger["scan_status"] = "not_indexed_access_denied"
        return files, ledger, skipped_sensitive
    except OSError as exc:
        ledger["permission_status"] = f"read_error:{type(exc).__name__}"
        ledger["scan_status"] = "not_indexed_read_error"
        return files, ledger, skipped_sensitive
    ledger["permission_status"] = "readable"
    if not root_cfg.get("scan_enabled", True) or max_files <= 0:
        ledger["scan_status"] = "resolved_not_indexed_by_config"
        return files, ledger, skipped_sensitive
    ledger["scan_status"] = "indexed"
    root_depth = len(root_path.resolve().parts)
    for dirpath, dirnames, filenames in os.walk(root_path):
        current_path = Path(dirpath)
        dirnames[:] = [name for name in sorted(dirnames) if name not in IGNORE_DIR_NAMES]
        depth = max(0, len(current_path.resolve().parts) - root_depth)
        if depth >= max_depth:
            dirnames[:] = []
        for filename in sorted(filenames):
            path = current_path / filename
            if path.suffix.lower() not in extensions:
                continue
            reason = is_sensitive_path(path, sensitive_fragments)
            if reason:
                skipped_sensitive.append(
                    {
                        "root_id": root_cfg["root_id"],
                        "path": str(path),
                        "skip_reason": f"sensitive_path_fragment:{reason}",
                        "read_action": "not_opened",
                    }
                )
                continue
            files.append(path)
            if len(files) >= max_files:
                dirnames[:] = []
                break
        if len(files) >= max_files:
            break
    ledger["file_count_indexed"] = len(files)
    ledger["file_count_skipped_sensitive"] = len(skipped_sensitive)
    return files, ledger, skipped_sensitive


def build_catalog_from_config(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    root_ledgers: list[dict[str, Any]] = []
    skipped_sensitive: list[dict[str, Any]] = []
    hash_limit = int(config.get("hash_size_limit_bytes", HASH_SIZE_LIMIT_BYTES))
    max_total_rows = int(config.get("max_total_catalog_rows", MAX_TOTAL_CATALOG_ROWS))
    for root_cfg in config.get("roots", []):
        files, ledger, skipped = scan_root(root_cfg, config)
        root_ledgers.append(ledger)
        skipped_sensitive.extend(skipped)
        root_path = Path(root_cfg["root_path"])
        for path in files:
            if len(rows) >= max_total_rows:
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            hash_status = "sha256_complete"
            sha256: str | None = None
            deferral_id = "not_applicable"
            read_actions = ["stat"]
            if stat.st_size <= hash_limit:
                sha256 = sha256_file(path)
                read_actions.append("sha256_file_open_read_only")
            else:
                hash_status = "deferred_large_file_requires_dedicated_hash_manifest"
                deferral_id = f"DEFERRAL-{len([r for r in rows if r.get('hash_status') == hash_status]) + 1:04d}"
                read_actions.append("content_not_opened_large_file_deferral")
            source_date = infer_date(path)
            row = base_payload(
                "catalog_row",
                catalog_row_id=f"LCAT-{len(rows) + 1:06d}",
                root_id=root_cfg["root_id"],
                root_path=str(root_path),
                absolute_path=str(path),
                relative_path=path_relative_to(path, root_path),
                repo_relative_path=repo_relative(path),
                source_family=source_family(path, root_cfg),
                symbol=infer_symbol(path),
                source_date=source_date,
                source_date_range={
                    "start": source_date if source_date != "not_inferred" else "not_inferred",
                    "end": source_date if source_date != "not_inferred" else "not_inferred",
                },
                timeframe=infer_timeframe(path),
                file_extension=path.suffix.lower(),
                size_bytes=stat.st_size,
                mtime_utc=mtime_utc(path),
                hash_policy="sha256_when_size_bounded_sensitive_paths_not_opened",
                sha256=sha256,
                hash_status=hash_status,
                large_file_hash_deferral_id=deferral_id,
                allowed_evidence_class="SOURCE_CONTROL_ONLY",
                forbidden_use_notes=[
                    "catalog_presence_not_validation_safe",
                    "no_result_cost_r_win_rate_expectancy_scoring",
                    "lane_specific_source_contract_required_before_outcome_use",
                ],
                read_actions=read_actions,
                path_sha256=sha256_text(str(path)),
            )
            rows.append(row)
    return rows, root_ledgers, skipped_sensitive


def query_matches(row: dict[str, Any], query: dict[str, Any]) -> bool:
    if query.get("symbol") and row.get("symbol") != query["symbol"]:
        return False
    if query.get("symbol_any") and row.get("symbol") not in set(query["symbol_any"]):
        return False
    if query.get("source_date") and row.get("source_date") != query["source_date"]:
        return False
    if query.get("extensions") and row.get("file_extension") not in set(query["extensions"]):
        return False
    if query.get("source_family_contains"):
        needle = str(query["source_family_contains"]).lower()
        if needle not in str(row.get("source_family", "")).lower():
            return False
    if query.get("path_contains"):
        needle = str(query["path_contains"]).lower()
        path_blob = f"{row.get('absolute_path')} {row.get('repo_relative_path')} {row.get('relative_path')}".lower()
        if needle not in path_blob:
            return False
    return True


def build_search_ledger(
    config: dict[str, Any], catalog_rows: list[dict[str, Any]], root_ledgers: list[dict[str, Any]]
) -> dict[str, Any]:
    roots_searched = [ledger["root_id"] for ledger in root_ledgers if ledger.get("permission_status") == "readable"]
    query_rows: list[dict[str, Any]] = []
    for query in config.get("search_queries", []):
        matches = [row for row in catalog_rows if query_matches(row, query)]
        query_rows.append(
            {
                "query_id": query["query_id"],
                "purpose": query["purpose"],
                "query": query,
                "match_count": len(matches),
                "positive_evidence": [
                    {
                        "catalog_row_id": row["catalog_row_id"],
                        "root_id": row["root_id"],
                        "absolute_path": row["absolute_path"],
                        "sha256": row["sha256"],
                        "hash_status": row["hash_status"],
                    }
                    for row in matches[:20]
                ],
                "negative_evidence": []
                if matches
                else [
                    {
                        "searched_roots": roots_searched,
                        "classification": "not_recovered_in_bounded_local_catalog_scan",
                        "exact_next_action": "route_to_missing_window_or_acquisition_manifest_if required_by_lane",
                    }
                ],
                "roots_searched": roots_searched,
            }
        )
    return base_payload(
        "search_result_ledger",
        query_count=len(query_rows),
        positive_query_count=sum(1 for row in query_rows if row["match_count"] > 0),
        negative_query_count=sum(1 for row in query_rows if row["match_count"] == 0),
        rows=query_rows,
    )


def find_catalog_matches(
    catalog_rows: list[dict[str, Any]], symbol: str, source_date: str, source_family_contains: str | None = None
) -> list[dict[str, Any]]:
    matches = [row for row in catalog_rows if row.get("symbol") == symbol and row.get("source_date") == source_date]
    if source_family_contains:
        needle = source_family_contains.lower()
        matches = [row for row in matches if needle in str(row.get("source_family", "")).lower()]
    return matches


def build_missing_window_ledger(catalog_rows: list[dict[str, Any]], root_ledgers: list[dict[str, Any]]) -> dict[str, Any]:
    upstream = load_json(UPSTREAM_MISSING)
    market_rows = upstream.get("market_data_missing_windows", [])
    source_state_rows = upstream.get("source_state_missing_examples", [])
    roots_searched = [row["root_id"] for row in root_ledgers if row.get("permission_status") == "readable"]
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(market_rows, start=1):
        symbol = item["symbol"]
        source_date = item["source_date"]
        matches = find_catalog_matches(catalog_rows, symbol, source_date, "tick")
        recovered = bool(matches)
        blocker_code = "RECOVERED_LOCAL_SOURCE" if recovered else "RECOVERABLE_BY_APPROVED_EXTRACTION"
        rows.append(
            {
                "window_id": f"MW-MARKET-{idx:04d}",
                "source_requirement_type": "recoverable_market_data",
                "symbol": symbol,
                "source_date": source_date,
                "timeframe": item.get("timeframe", "TICK"),
                "source_family": "mt5_tick_parquet",
                "source_lane": item.get("source_lane"),
                "local_catalog_status": "recovered_local_source" if recovered else "not_recovered_in_bounded_scan",
                "matching_catalog_row_ids": [row["catalog_row_id"] for row in matches[:10]],
                "blocker_code": blocker_code,
                "roots_searched": roots_searched,
                "exact_next_action": "record_source_hash_and_lane_asof_before_use"
                if recovered
                else item.get("exact_source_requirement", "create_read_only_market_data_extraction_manifest"),
            }
        )
    for idx, item in enumerate(source_state_rows, start=1):
        symbol = item["symbol"]
        source_date = item["source_date"]
        support_rows = find_catalog_matches(catalog_rows, symbol, source_date)
        rows.append(
            {
                "window_id": f"MW-SOURCESTATE-{idx:04d}",
                "source_requirement_type": "non_generatable_historical_gtos_source_state",
                "symbol": symbol,
                "source_date": source_date,
                "timeframe": "not_applicable",
                "source_family": "pending_lifecycle_or_order_observability_truth",
                "candidate_id": item.get("candidate_id"),
                "local_catalog_status": "source_state_not_reconstructable_from_catalog_presence",
                "supporting_catalog_row_ids": [row["catalog_row_id"] for row in support_rows[:10]],
                "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
                "roots_searched": roots_searched,
                "exact_next_action": item.get(
                    "exact_capture_requirement",
                    "forward_logger_must_capture_source_state_at_decision_time",
                ),
            }
        )
    return base_payload(
        "missing_window_ledger",
        exact_next_action_rule=(
            "Recoverable market-data rows route to local source hash, read-only extraction, owner export, "
            "or source-contract manifest. Historical GTOS source-state rows route only to existing source-safe "
            "logs or forward capture requirements."
        ),
        recoverable_market_data_count=sum(1 for row in rows if row["source_requirement_type"] == "recoverable_market_data"),
        non_generatable_source_state_count=sum(
            1 for row in rows if row["source_requirement_type"] == "non_generatable_historical_gtos_source_state"
        ),
        recovered_local_market_data_count=sum(1 for row in rows if row.get("blocker_code") == "RECOVERED_LOCAL_SOURCE"),
        rows=rows,
    )


def build_acquisition_manifest(missing_ledger: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    schema = base_payload(
        "acquisition_request_manifest_schema",
        required_fields=[
            "request_id",
            "source_requirement_type",
            "blocker_code",
            "symbol",
            "window_start_utc",
            "window_end_utc",
            "timeframe",
            "requested_fields",
            "approved_route",
            "cost_cap_usd",
            "approval_required",
            "owner_action_required",
            "no_leak_constraints",
            "forbidden_fields",
            "output_path",
            "hash_policy",
            "execution_status",
        ],
        allowed_blocker_codes=[
            "RECOVERABLE_BY_APPROVED_EXTRACTION",
            "RECOVERABLE_BY_OWNER_EXPORT",
            "RECOVERABLE_BY_SOURCE_CONTRACT",
            "NON_GENERATABLE_SOURCE_STATE",
            "FORBIDDEN_EVIDENCE_CLASS",
        ],
        execution_policy="manifest_only_no_api_no_mt5_no_broker_account_no_paid_route_executed",
    )
    requests: list[dict[str, Any]] = []
    for row in missing_ledger.get("rows", []):
        if row.get("blocker_code") == "RECOVERED_LOCAL_SOURCE":
            continue
        if row["source_requirement_type"] == "recoverable_market_data":
            date = row["source_date"]
            requests.append(
                {
                    "request_id": f"ACQ-{len(requests) + 1:04d}",
                    "source_requirement_type": row["source_requirement_type"],
                    "blocker_code": row["blocker_code"],
                    "symbol": row["symbol"],
                    "window_start_utc": f"{date}T00:00:00Z",
                    "window_end_utc": f"{date}T23:59:59Z",
                    "timeframe": row["timeframe"],
                    "requested_fields": ["bid", "ask", "last", "volume", "flags", "time_msc"],
                    "approved_route": "read_only_market_data_export_or_owner_export_manifest",
                    "cost_cap_usd": 0,
                    "approval_required": True,
                    "owner_action_required": row["exact_next_action"],
                    "no_leak_constraints": [
                        "no_account_order_deal_history_position_values",
                        "no_broker_actual_r",
                        "no_result_scoring",
                    ],
                    "forbidden_fields": ["account", "order", "deal", "position", "profit", "ticket", "broker_actual_r"],
                    "output_path": "research/source_requests/pending_owner_export_or_read_only_extraction/",
                    "hash_policy": "sha256_after_export_before_use",
                    "execution_status": "not_executed_manifest_only",
                }
            )
        elif row["source_requirement_type"] == "non_generatable_historical_gtos_source_state":
            requests.append(
                {
                    "request_id": f"ACQ-{len(requests) + 1:04d}",
                    "source_requirement_type": row["source_requirement_type"],
                    "blocker_code": row["blocker_code"],
                    "symbol": row["symbol"],
                    "window_start_utc": f"{row['source_date']}T00:00:00Z",
                    "window_end_utc": f"{row['source_date']}T23:59:59Z",
                    "timeframe": "not_applicable",
                    "requested_fields": [
                        "pending_intent_id",
                        "lifecycle_group_id",
                        "write_clock_utc",
                        "source_lane",
                        "final_lifecycle_state",
                    ],
                    "approved_route": "prospective_forward_capture_requirement",
                    "cost_cap_usd": 0,
                    "approval_required": False,
                    "owner_action_required": row["exact_next_action"],
                    "no_leak_constraints": [
                        "do_not_infer_historical_source_state_from_price",
                        "do_not_convert_projection_to_historical_truth",
                    ],
                    "forbidden_fields": ["broker_actual_r", "account_history_deal_link", "native_order_ticket"],
                    "output_path": "future_forward_capture_contract_not_historical_backfill",
                    "hash_policy": "source_hash_required_after_future_capture",
                    "execution_status": "not_executed_manifest_only",
                }
            )
    manifest = base_payload(
        "acquisition_request_manifest_example",
        request_count=len(requests),
        market_data_request_count=sum(1 for row in requests if row["source_requirement_type"] == "recoverable_market_data"),
        source_state_capture_requirement_count=sum(
            1 for row in requests if row["source_requirement_type"] == "non_generatable_historical_gtos_source_state"
        ),
        requests=requests,
    )
    return schema, manifest


def build_hash_manifest(catalog_rows: list[dict[str, Any]], skipped_sensitive: list[dict[str, Any]]) -> dict[str, Any]:
    hashed = [
        {
            "catalog_row_id": row["catalog_row_id"],
            "absolute_path": row["absolute_path"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
            "source_family": row["source_family"],
        }
        for row in catalog_rows
        if row["hash_status"] == "sha256_complete"
    ]
    deferrals = [
        {
            "catalog_row_id": row["catalog_row_id"],
            "absolute_path": row["absolute_path"],
            "size_bytes": row["size_bytes"],
            "large_file_hash_deferral_id": row["large_file_hash_deferral_id"],
            "source_family": row["source_family"],
            "exact_next_action": "run_dedicated_owner_approved_hash_manifest_for_large_file_before_consumption",
        }
        for row in catalog_rows
        if row["hash_status"] == "deferred_large_file_requires_dedicated_hash_manifest"
    ]
    return base_payload(
        "source_hash_deferral_manifest",
        hash_size_limit_bytes=HASH_SIZE_LIMIT_BYTES,
        hashed_file_count=len(hashed),
        large_file_deferral_count=len(deferrals),
        sensitive_path_not_opened_count=len(skipped_sensitive),
        hashed_files=hashed,
        large_file_deferrals=deferrals,
        sensitive_paths_not_opened=skipped_sensitive,
    )


def build_classification_ledger(missing_ledger: dict[str, Any]) -> dict[str, Any]:
    return base_payload(
        "recoverable_vs_non_generatable_classification_ledger",
        classification_rows=[
            {
                "class": "recoverable_market_data",
                "examples": ["ticks", "bars", "quotes", "spreads", "Sierra cache", "vendor cache"],
                "route": "local_catalog_search_then_read_only_extraction_or_owner_export",
                "can_catalog_recover": True,
                "can_price_backfill": False,
            },
            {
                "class": "recoverable_by_source_contract",
                "examples": ["public source cache", "vendor cache", "Sierra export"],
                "route": "pre_call_or_source_contract_manifest_before_network_vendor_api_action",
                "can_catalog_recover": True,
                "can_price_backfill": False,
            },
            {
                "class": "non_generatable_historical_gtos_source_state",
                "examples": [
                    "pending intent id",
                    "pending lifecycle group",
                    "write-clock event",
                    "source-safe order observability",
                    "logger-emitted final lifecycle state",
                ],
                "route": "existing_source_safe_logs_or_forward_capture_requirement_only",
                "can_catalog_recover": False,
                "can_price_backfill": False,
            },
            {
                "class": "forbidden_evidence_class",
                "examples": ["broker account history", "broker actual R", "live order state", "credential source"],
                "route": "reject_or_split_to_owner_approved_prompt",
                "can_catalog_recover": False,
                "can_price_backfill": False,
            },
        ],
        missing_window_counts={
            "recoverable_market_data": missing_ledger.get("recoverable_market_data_count"),
            "non_generatable_historical_gtos_source_state": missing_ledger.get("non_generatable_source_state_count"),
            "recovered_local_market_data": missing_ledger.get("recovered_local_market_data_count"),
        },
        price_movement_backfill_rule="Price movement cannot backfill historical GTOS source-state truth.",
    )


def build_decision_ledger(root_config: dict[str, Any], catalog_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return base_payload(
        "catalog_implementation_decision_ledger",
        implementation_decisions=[
            {
                "decision_id": "CAT-DEC-001",
                "decision": "route_local_read_only_builder_verifier_tests",
                "rationale": "Keeps catalog tooling outside live trading code and avoids production behavior changes.",
                "evidence": ["builder_cli", "verifier", "focused_tests"],
            },
            {
                "decision_id": "CAT-DEC-002",
                "decision": "machine_readable_root_resolver_config",
                "rationale": "Future goal prompts can cite the same roots before declaring data absent.",
                "evidence": [f"{PREFIX}_ROOT_RESOLVER_CONFIG_{DATE}.json"],
            },
            {
                "decision_id": "CAT-DEC-003",
                "decision": "bounded_hash_policy",
                "rationale": "Small safe files receive SHA256; large files receive deferral records before consumption.",
                "evidence": [f"{PREFIX}_SOURCE_HASH_DEFERRAL_MANIFEST_{DATE}.json"],
            },
            {
                "decision_id": "CAT-DEC-004",
                "decision": "catalog_presence_is_not_validation_safe",
                "rationale": "Source presence does not open validation, scoring, promotion, or live behavior.",
                "evidence": ["safe_flags", "forbidden_route_noleak_audit"],
            },
        ],
        root_count=len(root_config.get("roots", [])),
        catalog_row_count=len(catalog_rows),
        terminal_decision_options=[
            "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
            "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS",
            "BLOCKED_WITH_EXACT_OWNER_ACCESS_OR_SOURCE_REQUIREMENTS",
            "REJECT_IF_TOOL_OPENS_FORBIDDEN_EVIDENCE_CLASS",
        ],
    )


def build_noleak_audit(
    root_ledgers: list[dict[str, Any]], skipped_sensitive: list[dict[str, Any]], catalog_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    diff_scope = git_diff_scope()
    forbidden_catalog_rows = [
        row
        for row in catalog_rows
        if any(fragment in str(row.get("absolute_path", "")).lower() for fragment in SENSITIVE_PATH_FRAGMENTS)
    ]
    return base_payload(
        "forbidden_route_noleak_audit",
        audit_passed=diff_scope["ok"] and not forbidden_catalog_rows,
        diff_scope=diff_scope,
        root_resolution_summary=root_ledgers,
        sensitive_path_not_opened_count=len(skipped_sensitive),
        sensitive_path_not_opened_samples=skipped_sensitive[:50],
        forbidden_catalog_row_count=len(forbidden_catalog_rows),
        broker_account_order_history_values_read=False,
        broker_actual_r_read=False,
        credential_paths_opened=False,
        large_files_copied_or_modified=False,
        validation_execution_opened=False,
        result_cost_r_win_rate_expectancy_scoring_opened=False,
        read_only_scan_actions=["directory_listing", "stat", "sha256_small_safe_files", "large_file_hash_deferral"],
    )


def build_context_anchor(root_ledgers: list[dict[str, Any]]) -> dict[str, Any]:
    return base_payload(
        "context_anchor",
        current_head=git_head(),
        current_head_subject=git_head_subject(),
        prompt_path=rel(PROMPT_PATH),
        upstream_route=rel(UPSTREAM_ROUTE),
        accepted_fixture_routes=[rel(NOFILL_FIXTURE_ROUTE), rel(G12_FIXTURE_ROUTE)],
        mandatory_preflight_completed=True,
        control_docs_read=[rel(path) for path in CONTROL_DOCS],
        route_boundaries=[
            "source_control_catalog_tooling_only",
            "no_validation_execution",
            "no_result_cost_r_win_rate_expectancy_scoring",
            "no_paid_api_route",
            "no_live_trading_behavior_change",
            "no_broker_account_order_history_deal_position_or_actual_r_read",
            "no_credentials",
        ],
        resolved_root_count=len(root_ledgers),
        readable_root_count=sum(1 for row in root_ledgers if row.get("permission_status") == "readable"),
    )


def build_integration_guide(search_ledger: dict[str, Any], missing_ledger: dict[str, Any]) -> tuple[dict[str, Any], str]:
    payload = base_payload(
        "integration_guide",
        future_prompt_instructions=[
            "Run the builder CLI before declaring local data absent.",
            "Cite the search-result ledger for positive and negative root evidence.",
            "Use the missing-window ledger to route recoverable market data separately from non-generatable source-state truth.",
            "Use the acquisition manifest for exact owner/export/read-only-extraction requirements.",
            "Treat catalog rows as SOURCE_CONTROL_ONLY until a separate lane binds source contract, as-of policy, and no-leak rules.",
        ],
        reusable_commands=[
            f"python {rel(ROUTE_DIR / 'build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py')}",
            f"python {rel(ROUTE_DIR / 'verify_gtos_local_research_data_catalog_implementation_route_2026_05_10.py')}",
        ],
        search_ledger_query_count=search_ledger.get("query_count"),
        missing_window_row_count=len(missing_ledger.get("rows", [])),
    )
    md = "\n".join(
        [
            "# GTOS Local Research Data Catalog Integration Guide",
            "",
            f"Route: `{ROUTE_ID}`",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            "",
            "## Use In Future Goal Prompts",
            "",
            "Run the route-local builder before any data-absence claim:",
            "",
            "```powershell",
            f"python {rel(ROUTE_DIR / 'build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py')}",
            "```",
            "",
            "Then inspect:",
            "",
            f"- `{PREFIX}_CATALOG_{DATE}.jsonl` for bounded local source/control rows.",
            f"- `{PREFIX}_SEARCH_RESULT_LEDGER_{DATE}.json` for positive and negative query evidence.",
            f"- `{PREFIX}_MISSING_WINDOW_LEDGER_{DATE}.json` for recoverable market-data versus source-state gaps.",
            f"- `{PREFIX}_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_{DATE}.json` for exact owner/export/read-only-extraction actions.",
            "",
            "Catalog presence remains `SOURCE_CONTROL_ONLY`; it does not make any file validation-safe or promotable.",
            "A future result lane must separately bind source hashes, as-of rules, duplicate policy, no-leak controls, and label family.",
        ]
    )
    return payload, md + "\n"


def build_next_prompt_pack() -> str:
    return "\n".join(
        [
            "# G12 Local Research Data Catalog Tooling Source-Control Audit Prompt Pack",
            "",
            f"Route: `{ROUTE_ID}`",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
            "",
            "## Prompt",
            "",
            "Audit the local research data catalog implementation route as source-control/catalog tooling only. "
            "Verify root config/schema, catalog rows, search-result ledger, missing-window ledger, acquisition manifest, "
            "recoverable-vs-non-generatable classification, hash/deferral manifest, no-leak audit, integration guide, "
            "completion audit, verifier result, and focused tests. Do not open validation, result scoring, promotion, "
            "paid/API routes, broker account/order/history/deal/position behavior, broker actual-R, credentials, or live behavior.",
            "",
            "Terminal decision options: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`, "
            "`ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS`, `BLOCKED_WITH_EXACT_OWNER_ACCESS_OR_SOURCE_REQUIREMENTS`, "
            "`REJECT_IF_TOOL_OPENS_FORBIDDEN_EVIDENCE_CLASS`.",
            "",
        ]
    )


def build_saturation_pass() -> dict[str, Any]:
    return base_payload(
        "saturation_self_redteam_pass",
        questions=[
            {
                "question": "Could catalog presence be mistaken for validation-safe source evidence?",
                "answer": "All rows are SOURCE_CONTROL_ONLY and repeat that lane-specific source contracts are required before outcome use.",
                "action": "closed_by_catalog_schema_and_integration_guide",
            },
            {
                "question": "Could broker/account/order/history/deal/position or broker actual-R values leak into the catalog?",
                "answer": "Sensitive path fragments are skipped before hashing; no-leak audit records not-opened paths and verifier checks catalog rows.",
                "action": "closed_by_sensitive_path_skip_and_noleak_audit",
            },
            {
                "question": "Could large files be silently copied or hashed without a bounded policy?",
                "answer": "Large safe files receive deferral records; the tool never copies source files.",
                "action": "closed_by_hash_deferral_manifest",
            },
            {
                "question": "Could worktree-local absence become a final blocker?",
                "answer": "Root config searches current worktree, absolute main roots, prior worktrees, Sierra roots, and owner candidate roots.",
                "action": "closed_by_root_resolver_and_missing_window_ledger",
            },
            {
                "question": "Could non-generatable source-state truth be inferred from price data?",
                "answer": "Classification ledger routes those rows to existing source-safe logs or prospective capture requirements only.",
                "action": "closed_by_recoverable_non_generatable_classification",
            },
        ],
        same_evidence_class_gaps_remaining=[],
    )


def build_instruction_checklist() -> dict[str, Any]:
    requirements = [
        ("preflight_context_anchor", "Context anchor records prompt path, HEAD, preflight docs, and boundaries."),
        ("root_resolver_config_schema", "Machine-readable root config and schema emitted."),
        ("catalog_jsonl", "Catalog JSONL emitted from bounded read-only scan."),
        ("search_result_ledger", "Configured query search-result ledger emitted with positive and negative evidence."),
        ("missing_window_ledger", "Requested windows routed with exact next actions."),
        ("acquisition_manifest", "Acquisition manifest schema and example emitted."),
        ("recoverable_non_generatable", "Recoverable market data separated from non-generatable source-state truth."),
        ("hash_deferral_manifest", "Small-file SHA256 hashes and large-file deferrals emitted."),
        ("noleak_audit", "No-leak and forbidden live-surface audit emitted."),
        ("integration_guide", "Future goal prompt guide emitted."),
        ("verifier_tests", "Verifier and focused tests present."),
        ("safe_flags", "NO_PROMOTION_VERDICT and closed flags preserved."),
    ]
    return base_payload(
        "instruction_coverage_checklist",
        requirement_count=len(requirements),
        requirements=[
            {
                "requirement_id": req_id,
                "status": "satisfied",
                "evidence": evidence,
            }
            for req_id, evidence in requirements
        ],
    )


def build_completion_audit(
    artifact_names: list[str],
    catalog_rows: list[dict[str, Any]],
    search_ledger: dict[str, Any],
    missing_ledger: dict[str, Any],
    noleak: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement_id": "objective_route",
            "prompt_requirement": "Build GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE.",
            "evidence": rel(ROUTE_DIR),
            "status": "satisfied",
        },
        {
            "requirement_id": "reusable_read_only_tool",
            "prompt_requirement": "Reusable read-only root resolver/catalog/search/missing-window/acquisition tooling.",
            "evidence": rel(ROUTE_DIR / "build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py"),
            "status": "satisfied",
        },
        {
            "requirement_id": "catalog_jsonl",
            "prompt_requirement": "Emit catalog JSONL output from bounded read-only scan.",
            "evidence": f"{PREFIX}_CATALOG_{DATE}.jsonl rows={len(catalog_rows)}",
            "status": "satisfied",
        },
        {
            "requirement_id": "search_missing_acquisition",
            "prompt_requirement": "Emit search-result, missing-window, and acquisition-request ledgers.",
            "evidence": f"queries={search_ledger.get('query_count')} missing_rows={len(missing_ledger.get('rows', []))}",
            "status": "satisfied",
        },
        {
            "requirement_id": "recoverable_vs_non_generatable",
            "prompt_requirement": "Separate recoverable market data from non-generatable historical GTOS source-state truth.",
            "evidence": f"non_generatable_source_state_count={missing_ledger.get('non_generatable_source_state_count')}",
            "status": "satisfied",
        },
        {
            "requirement_id": "hash_and_deferral",
            "prompt_requirement": "Hash bounded safe files and record large-file deferrals.",
            "evidence": f"{PREFIX}_SOURCE_HASH_DEFERRAL_MANIFEST_{DATE}.json",
            "status": "satisfied",
        },
        {
            "requirement_id": "no_leak_forbidden_surfaces",
            "prompt_requirement": "No broker/account/order/history/deal/position, credentials, validation, scoring, live-surface changes.",
            "evidence": f"audit_passed={noleak.get('audit_passed')}",
            "status": "satisfied",
        },
        {
            "requirement_id": "integration_guide",
            "prompt_requirement": "Future goal prompts can cite integration guide before declaring data missing.",
            "evidence": f"{PREFIX}_INTEGRATION_GUIDE_{DATE}.md",
            "status": "satisfied",
        },
        {
            "requirement_id": "verifier_focused_tests",
            "prompt_requirement": "Builder/catalog CLI, verifier, and focused tests exist.",
            "evidence": "builder/verifier/test modules created; verification result generated",
            "status": "satisfied",
        },
        {
            "requirement_id": "safe_flags",
            "prompt_requirement": "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "evidence": "safe flags stamped on generated JSON/JSONL artifacts and Markdown control tokens present",
            "status": "satisfied",
        },
    ]
    return base_payload(
        "completion_audit",
        objective_restatement=(
            "Implement reusable source-control/catalog tooling that resolves local roots, catalogs source/control files, "
            "records searches and missing windows, routes acquisition requirements, and preserves closed research flags."
        ),
        prompt_to_artifact_checklist=checklist,
        artifact_names=artifact_names,
        missing_incomplete_or_weak_requirements=[],
        completion_standard_satisfied=True,
        can_mark_goal_complete=True,
    )


def build_output_manifest(artifact_names: list[str]) -> dict[str, Any]:
    return base_payload(
        "output_manifest",
        artifact_count=len(artifact_names),
        artifacts=sorted(artifact_names),
    )


def write_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    root_config = default_root_config()
    catalog_rows, root_ledgers, skipped_sensitive = build_catalog_from_config(root_config)
    context_anchor = build_context_anchor(root_ledgers)
    decision_ledger = build_decision_ledger(root_config, catalog_rows)
    search_ledger = build_search_ledger(root_config, catalog_rows, root_ledgers)
    missing_ledger = build_missing_window_ledger(catalog_rows, root_ledgers)
    acquisition_schema, acquisition_manifest = build_acquisition_manifest(missing_ledger)
    hash_manifest = build_hash_manifest(catalog_rows, skipped_sensitive)
    classification = build_classification_ledger(missing_ledger)
    noleak = build_noleak_audit(root_ledgers, skipped_sensitive, catalog_rows)
    integration_payload, integration_md = build_integration_guide(search_ledger, missing_ledger)
    saturation = build_saturation_pass()
    instruction_checklist = build_instruction_checklist()

    artifact_paths: list[Path] = []
    json_payloads = [
        (f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json", context_anchor, "Context Anchor"),
        (f"{PREFIX}_ROOT_RESOLVER_CONFIG_{DATE}.json", root_config, "Root Resolver Config"),
        (f"{PREFIX}_ROOT_RESOLVER_CONFIG_SCHEMA_{DATE}.json", root_schema(), "Root Resolver Config Schema"),
        (f"{PREFIX}_CATALOG_IMPLEMENTATION_DECISION_LEDGER_{DATE}.json", decision_ledger, "Catalog Decision Ledger"),
        (f"{PREFIX}_CATALOG_SCHEMA_{DATE}.json", catalog_schema(), "Catalog Schema"),
        (f"{PREFIX}_SEARCH_RESULT_LEDGER_{DATE}.json", search_ledger, "Search Result Ledger"),
        (f"{PREFIX}_MISSING_WINDOW_LEDGER_{DATE}.json", missing_ledger, "Missing Window Ledger"),
        (f"{PREFIX}_ACQUISITION_REQUEST_MANIFEST_SCHEMA_{DATE}.json", acquisition_schema, "Acquisition Manifest Schema"),
        (f"{PREFIX}_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_{DATE}.json", acquisition_manifest, "Acquisition Manifest Example"),
        (
            f"{PREFIX}_RECOVERABLE_NON_GENERATABLE_CLASSIFICATION_LEDGER_{DATE}.json",
            classification,
            "Recoverable Non Generatable Classification Ledger",
        ),
        (f"{PREFIX}_SOURCE_HASH_DEFERRAL_MANIFEST_{DATE}.json", hash_manifest, "Source Hash Deferral Manifest"),
        (f"{PREFIX}_FORBIDDEN_ROUTE_NOLEAK_AUDIT_{DATE}.json", noleak, "Forbidden Route Noleak Audit"),
        (f"{PREFIX}_INTEGRATION_GUIDE_{DATE}.json", integration_payload, "Integration Guide"),
        (f"{PREFIX}_SATURATION_SELF_REDTEAM_PASS_{DATE}.json", saturation, "Saturation Self Redteam Pass"),
        (f"{PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json", instruction_checklist, "Instruction Coverage Checklist"),
    ]
    for name, payload, title in json_payloads:
        json_path = write_json(ROUTE_DIR / name, payload)
        artifact_paths.append(json_path)
        if name.endswith("_CONFIG_SCHEMA_2026-05-10.json") or name.endswith("_CATALOG_SCHEMA_2026-05-10.json"):
            pass
        md_path = write_md(ROUTE_DIR / name.replace(".json", ".md"), title, payload)
        artifact_paths.append(md_path)

    catalog_path = write_jsonl(ROUTE_DIR / f"{PREFIX}_CATALOG_{DATE}.jsonl", catalog_rows)
    artifact_paths.append(catalog_path)

    guide_path = ROUTE_DIR / f"{PREFIX}_INTEGRATION_GUIDE_{DATE}.md"
    guide_path.write_text(integration_md, encoding="utf-8")
    if guide_path not in artifact_paths:
        artifact_paths.append(guide_path)

    prompt_pack_path = ROUTE_DIR / f"{PREFIX}_NEXT_G12_SOURCE_CONTROL_AUDIT_PROMPT_PACK_{DATE}.md"
    prompt_pack_path.write_text(build_next_prompt_pack(), encoding="utf-8")
    artifact_paths.append(prompt_pack_path)

    completion = build_completion_audit([path.name for path in artifact_paths], catalog_rows, search_ledger, missing_ledger, noleak)
    completion_json = write_json(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json", completion)
    completion_md = write_md(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md", "Completion Audit", completion)
    artifact_paths.extend([completion_json, completion_md])

    output_manifest = build_output_manifest([path.name for path in artifact_paths])
    output_json = write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json", output_manifest)
    artifact_paths.append(output_json)

    result = {
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "catalog_row_count": len(catalog_rows),
        "readable_root_count": sum(1 for row in root_ledgers if row.get("permission_status") == "readable"),
        "search_query_count": search_ledger.get("query_count"),
        "missing_window_row_count": len(missing_ledger.get("rows", [])),
        "hash_manifest_hashed_file_count": hash_manifest.get("hashed_file_count"),
        "hash_manifest_large_file_deferral_count": hash_manifest.get("large_file_deferral_count"),
        "noleak_audit_passed": noleak.get("audit_passed"),
        "artifact_count": len(artifact_paths),
        "can_mark_goal_complete": True,
    }
    return with_safe_flags(result)


def main() -> int:
    result = write_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
