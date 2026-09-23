from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
WORKTREE = Path(r"")

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    ".ipynb_checkpoints",
}

EXT_FAMILIES = {
    ".parquet": "columnar_market_or_feature_data",
    ".feather": "columnar_market_or_feature_data",
    ".csv": "csv_table_or_bar_data",
    ".tsv": "csv_table_or_bar_data",
    ".jsonl": "jsonl_logs_or_ledgers",
    ".json": "json_machine_artifact",
    ".ndjson": "jsonl_logs_or_ledgers",
    ".md": "markdown_human_artifact",
    ".txt": "text_human_or_raw_artifact",
    ".py": "python_code_or_tooling",
    ".ps1": "script_or_runtime_tooling",
    ".bat": "script_or_runtime_tooling",
    ".cmd": "script_or_runtime_tooling",
    ".sh": "script_or_runtime_tooling",
    ".yaml": "config_or_manifest",
    ".yml": "config_or_manifest",
    ".toml": "config_or_manifest",
    ".ini": "config_or_manifest",
    ".cfg": "config_or_manifest",
    ".db": "database_or_index",
    ".sqlite": "database_or_index",
    ".sqlite3": "database_or_index",
    ".lance": "database_or_index",
    ".scid": "sierra_scid_intraday_data",
    ".dly": "sierra_daily_data",
    ".depth": "sierra_depth_or_orderflow_data",
    ".depth2": "sierra_depth_or_orderflow_data",
    ".zip": "archive_or_download_cache",
    ".gz": "archive_or_download_cache",
    ".7z": "archive_or_download_cache",
    ".rar": "archive_or_download_cache",
    ".pkl": "serialized_model_or_cache",
    ".pickle": "serialized_model_or_cache",
    ".joblib": "serialized_model_or_cache",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def to_posix(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def rel_or_abs(path: Path) -> str:
    try:
        return to_posix(path.resolve().relative_to(WORKTREE.resolve()))
    except Exception:
        return str(path)


def path_contains(path: Path, fragment: str) -> bool:
    return fragment.lower() in str(path).lower().replace("/", "\\")


def family_for(path: Path) -> str:
    suffix = path.suffix.lower()
    lower = str(path).lower().replace("/", "\\")
    if suffix == ".parquet" and "\\data\\ticks\\" in lower:
        return "mt5_tick_parquet"
    if suffix == ".jsonl" and "\\shadow_logs\\" in lower:
        return "shadow_log_jsonl"
    if suffix == ".csv" and "\\data\\historical" in lower:
        return "historical_ohlc_csv"
    if suffix == ".json" and "\\pipeline_state\\" in lower:
        return "pipeline_state_json"
    if suffix in EXT_FAMILIES:
        return EXT_FAMILIES[suffix]
    if not suffix:
        return "extensionless_or_directory_marker"
    return "other"


def direct_children(path: Path, limit: int = 250) -> dict[str, Any]:
    result: dict[str, Any] = {
        "dirs": [],
        "files": [],
        "error": None,
        "truncated": False,
    }
    try:
        entries = sorted(path.iterdir(), key=lambda p: p.name.lower())
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    for entry in entries[:limit]:
        bucket = "dirs" if entry.is_dir() else "files"
        result[bucket].append(entry.name)
    result["truncated"] = len(entries) > limit
    result["total_entries"] = len(entries)
    return result


def scan_root(path: Path, max_depth: int | None = None, max_files: int = 500_000) -> dict[str, Any]:
    out: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir() if path.exists() else False,
        "status": "missing",
        "scan_mode": "recursive" if max_depth is None else f"recursive_max_depth_{max_depth}",
        "file_count": 0,
        "dir_count": 0,
        "total_bytes": 0,
        "family_counts": {},
        "extension_counts": {},
        "latest_mtime_utc": None,
        "largest_files": [],
        "sample_files_by_family": {},
        "errors": [],
        "truncated": False,
    }
    if not path.exists():
        return out
    if not path.is_dir():
        out["status"] = "not_directory"
        return out

    family_counts: Counter[str] = Counter()
    ext_counts: Counter[str] = Counter()
    samples: dict[str, list[str]] = defaultdict(list)
    largest: list[tuple[int, str]] = []
    latest_mtime: float | None = None
    root_depth = len(path.resolve().parts)
    out["status"] = "searched"

    for current, dirs, files in os.walk(path, followlinks=False):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        depth = len(current_path.resolve().parts) - root_depth
        if max_depth is not None and depth >= max_depth:
            dirs[:] = []
        out["dir_count"] += len(dirs)
        for name in files:
            file_path = current_path / name
            try:
                stat = file_path.stat()
            except Exception as exc:
                out["errors"].append(
                    {"path": str(file_path), "error": f"{type(exc).__name__}: {exc}"}
                )
                continue
            out["file_count"] += 1
            out["total_bytes"] += stat.st_size
            latest_mtime = stat.st_mtime if latest_mtime is None else max(latest_mtime, stat.st_mtime)
            suffix = file_path.suffix.lower() or "[none]"
            fam = family_for(file_path)
            family_counts[fam] += 1
            ext_counts[suffix] += 1
            if len(samples[fam]) < 8:
                samples[fam].append(rel_or_abs(file_path))
            largest.append((stat.st_size, rel_or_abs(file_path)))
            if len(largest) > 30:
                largest = sorted(largest, reverse=True)[:20]
            if out["file_count"] >= max_files:
                out["truncated"] = True
                dirs[:] = []
                break
        if out["truncated"]:
            break

    if latest_mtime is not None:
        out["latest_mtime_utc"] = (
            datetime.fromtimestamp(latest_mtime, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    out["family_counts"] = dict(sorted(family_counts.items()))
    out["extension_counts"] = dict(sorted(ext_counts.items()))
    out["sample_files_by_family"] = {k: v for k, v in sorted(samples.items())}
    out["largest_files"] = [
        {"bytes": size, "path": path_str} for size, path_str in sorted(largest, reverse=True)[:20]
    ]
    return out


def add_root(specs: list[dict[str, Any]], root_id: str, path: str, policy: str, max_depth: int | None) -> None:
    specs.append(
        {
            "root_id": root_id,
            "path": path,
            "policy": policy,
            "max_depth": max_depth,
        }
    )


def build_root_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    add_root(specs, "worktree_data", str(WORKTREE / "data"), "worktree local data", None)
    add_root(specs, "worktree_ticks", str(WORKTREE / "data" / "ticks"), "worktree local tick captures", None)
    add_root(specs, "worktree_historical_2026", str(WORKTREE / "data" / "historical_2026"), "worktree MT5 historical bars", None)
    add_root(specs, "worktree_shadow_logs", str(WORKTREE / "shadow_logs"), "worktree shadow/runtime logs", None)
    add_root(specs, "worktree_research", str(WORKTREE / "research"), "worktree research artifacts", None)
    add_root(specs, "worktree_knowledge_base", str(WORKTREE / "knowledge_base"), "worktree knowledge/trade records", None)
    add_root(specs, "worktree_pipeline_state", str(WORKTREE / "pipeline_state"), "worktree pipeline state", None)
    add_root(specs, "worktree_config", str(WORKTREE / "config"), "worktree config", None)
    add_root(specs, "worktree_scripts", str(WORKTREE / "scripts"), "worktree scripts/tooling", None)
    add_root(specs, "worktree_tests", str(WORKTREE / "tests"), "worktree tests", None)

    main = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
    add_root(specs, "absolute_main_data", str(main / "data"), "approved absolute main repo data root", None)
    add_root(specs, "absolute_main_ticks", str(main / "data" / "ticks"), "approved absolute main repo tick root", None)
    add_root(specs, "absolute_main_external", str(main / "data" / "external"), "approved absolute main repo external/cache root", None)
    add_root(specs, "absolute_main_shadow_logs", str(main / "shadow_logs"), "approved absolute main repo shadow logs", None)
    add_root(specs, "absolute_main_exports", str(main / "exports"), "approved absolute main repo exports", None)

    tmp = Path(r"C:\tmp")
    add_root(specs, "tmp_direct", str(tmp), "approved temp root direct inventory only", 1)
    add_root(specs, "tmp_gtos_otb", str(tmp / "gtos_otb"), "approved prior worktree/cache root", None)
    add_root(specs, "tmp_current_worktree", str(WORKTREE), "current sprint worktree root", 3)
    if tmp.exists():
        try:
            for child in sorted(tmp.iterdir(), key=lambda p: p.name.lower()):
                if not child.is_dir():
                    continue
                lower = child.name.lower()
                if lower.startswith("gtos") and child.resolve() != WORKTREE.resolve():
                    add_root(
                        specs,
                        f"tmp_gtos_candidate_{child.name}",
                        str(child),
                        "targeted prior GTOS temp candidate",
                        5,
                    )
        except Exception:
            pass

    sierra = Path(r"C:\SierraChart")
    add_root(specs, "sierra_root", str(sierra), "approved SierraChart root", 4)
    for child in ["Data", "MarketDepthData", "MarketDepthHistoricalData"]:
        add_root(specs, f"sierra_{child.lower()}", str(sierra / child), "targeted Sierra data subroot", None)

    docs = Path(r"C:\Users\MSI\Documents")
    add_root(specs, "documents_direct", str(docs), "approved owner documents root direct inventory only", 1)
    return specs


def build_candidate_root_matrix(root_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matrix = []
    for spec in root_specs:
        path = Path(spec["path"])
        entry = {
            "root_id": spec["root_id"],
            "path": spec["path"],
            "policy": spec["policy"],
            "exists": path.exists(),
            "is_dir": path.is_dir() if path.exists() else False,
            "status": "found" if path.is_dir() else ("exists_not_dir" if path.exists() else "missing"),
        }
        matrix.append(entry)
    return matrix


def build_blockers(candidate_matrix: list[dict[str, Any]], scans: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for row in candidate_matrix:
        if row["status"] == "missing":
            blockers.append(
                {
                    "blocker_type": "local_absence",
                    "root_id": row["root_id"],
                    "path": row["path"],
                    "access_need": "If this source is required, provide the local path/export or authorize a read-only extraction route. Do not infer absence beyond this root.",
                }
            )
    for root_id, scan in scans.items():
        for error in scan.get("errors", [])[:20]:
            blockers.append(
                {
                    "blocker_type": "filesystem_read_error",
                    "root_id": root_id,
                    "path": error["path"],
                    "access_need": error["error"],
                }
            )
        if scan.get("truncated"):
            blockers.append(
                {
                    "blocker_type": "scan_truncated",
                    "root_id": root_id,
                    "path": scan["path"],
                    "access_need": "Increase scan cap or narrow target patterns before claiming completeness.",
                }
            )
    blockers.append(
        {
            "blocker_type": "forbidden_surface_by_task",
            "root_id": "live_mt5_and_paid_vendor",
            "path": "MT5 live calls / paid API / vendor calls",
            "access_need": "Task explicitly forbids paid/API/vendor calls and live MT5 calls. A future extraction must include a pre-call manifest, owner approval where required, symbol/window/fields/cost/no-leak rules.",
        }
    )
    return blockers


def build_cautions() -> list[dict[str, str]]:
    return [
        {
            "source_family": "shadow_logs",
            "caution": "Use for provenance, candidates, diagnostics, and permitted non-result fields. Do not consume broker actual-R, live trade result, account/order/history/deal/position labels unless a lane explicitly permits that evidence class.",
        },
        {
            "source_family": "local_heavy_data_roots",
            "caution": "Discovery roots are not validation-safe by existence. Any consumed source needs hashes, source contract, as-of ordering, duplicate policy, and label separation.",
        },
        {
            "source_family": "prior_worktrees_and_tmp",
            "caution": "Use as leads/caches only. Treat stale worktree data as non-canonical until source hashes and commit context are verified.",
        },
        {
            "source_family": "Sierra SCID/depth",
            "caution": "SCID/depth files require parser proof, segment hashes, timezone/as-of rules, and source-contract review before outcome use.",
        },
        {
            "source_family": "tick_parquet",
            "caution": "Tick data can support packet/source coverage and path/fillability audits only when symbol/window/source hashes and no-leak rules are recorded.",
        },
        {
            "source_family": "generated_research_outputs",
            "caution": "Research ledgers can generate hypotheses and comparisons, but promotion requires a separate dossier with unseen/pre-registered validation and concentration/cost/no-leak controls.",
        },
    ]


def build_routes(scans: dict[str, Any]) -> list[dict[str, Any]]:
    def count(root_id: str, family: str) -> int:
        return scans.get(root_id, {}).get("family_counts", {}).get(family, 0)

    routes = [
        {
            "rank_hint": 1,
            "route": "Mine current shadow-log strategy/candidate ledgers for no-API mechanical hypotheses",
            "primary_roots": ["worktree_shadow_logs", "absolute_main_shadow_logs"],
            "why_high_value": "Fresh local logs include large candidate/path/strategy ledgers and can fuel immediate no-API descriptor mining without live calls.",
            "starting_files_or_families": [
                "live_mechanical_strategy_shadow_outcomes.jsonl",
                "candidate_ltf_path_order.jsonl",
                "candidate_path_follow.jsonl",
                "strategy_follow_evaluations.jsonl",
                "mechanical_context_diagnostics_join.jsonl",
            ],
            "cautions": "Keep broker/account/deal result fields out unless explicitly authorized; separate synthetic/path labels from broker-realized labels.",
            "observed_local_signal": {
                "worktree_shadow_log_jsonl_files": count("worktree_shadow_logs", "shadow_log_jsonl"),
            },
        },
        {
            "rank_hint": 2,
            "route": "Use data/historical_2026 CSV bars for broad mechanical replay and cross-symbol controls",
            "primary_roots": ["worktree_historical_2026", "absolute_main_data"],
            "why_high_value": "CSV bars are cheap, local, and appropriate for source-safe no-API hypothesis generation across symbols/timeframes.",
            "starting_files_or_families": ["historical_ohlc_csv"],
            "cautions": "Historical replay can generate/kill hypotheses; do not call tuned results validation unless split/pre-registration supports it.",
            "observed_local_signal": {
                "worktree_historical_csv_files": count("worktree_historical_2026", "historical_ohlc_csv"),
            },
        },
        {
            "rank_hint": 3,
            "route": "Search tick parquet roots for lower-timeframe path/fillability and packet-source repair",
            "primary_roots": ["worktree_ticks", "absolute_main_ticks"],
            "why_high_value": "Tick parquet is the highest-resolution local path source if present and can repair fill/no-fill/source coverage questions.",
            "starting_files_or_families": ["mt5_tick_parquet"],
            "cautions": "Hash per consumed file/window; no live MT5 extraction in this task.",
            "observed_local_signal": {
                "worktree_tick_parquet_files": count("worktree_ticks", "mt5_tick_parquet"),
                "absolute_tick_parquet_files": count("absolute_main_ticks", "mt5_tick_parquet"),
            },
        },
        {
            "rank_hint": 4,
            "route": "Inspect SierraChart SCID/depth roots for futures/orderflow proxies",
            "primary_roots": ["sierra_data", "sierra_marketdepthdata", "sierra_marketdepthhistoricaldata"],
            "why_high_value": "If present, Sierra files are the bridge to futures/orderflow/proxy research that current GTOS logs cannot synthesize.",
            "starting_files_or_families": ["sierra_scid_intraday_data", "sierra_depth_or_orderflow_data"],
            "cautions": "Parser and immutable segment hash proof required before any outcome use.",
            "observed_local_signal": {
                "sierra_scid_files_in_data_root": count("sierra_data", "sierra_scid_intraday_data"),
                "sierra_depth_files_in_data_root": count("sierra_data", "sierra_depth_or_orderflow_data"),
            },
        },
        {
            "rank_hint": 5,
            "route": "Use existing research packet/result ledgers as hypothesis inventory, not canonical source truth",
            "primary_roots": ["worktree_research", "tmp_gtos_otb"],
            "why_high_value": "Prior READY8/SCID and phase research already contain accepted controls, fail-closed rows, and candidate families to route into immediate mechanical tests.",
            "starting_files_or_families": ["jsonl_logs_or_ledgers", "json_machine_artifact", "markdown_human_artifact"],
            "cautions": "Re-verify source hashes/rowset hashes before using any prior result as evidence.",
            "observed_local_signal": {
                "worktree_research_jsonl_files": count("worktree_research", "jsonl_logs_or_ledgers"),
                "worktree_research_json_files": count("worktree_research", "json_machine_artifact"),
            },
        },
    ]
    return routes


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    started = utc_now()
    root_specs = build_root_specs()
    candidate_matrix = build_candidate_root_matrix(root_specs)
    scans: dict[str, Any] = {}
    for spec in root_specs:
        scans[spec["root_id"]] = scan_root(Path(spec["path"]), max_depth=spec["max_depth"])

    direct_indexes = {
        "documents_direct": direct_children(Path(r"C:\Users\MSI\Documents")),
        "tmp_direct": direct_children(Path(r"C:\tmp")),
        "sierra_root": direct_children(Path(r"C:\SierraChart")) if Path(r"C:\SierraChart").exists() else None,
    }

    blockers = build_blockers(candidate_matrix, scans)
    routes = build_routes(scans)
    finished = utc_now()
    inventory = {
        "schema": "gtos_weekend_mechanical_edge_factory_data_inventory_v1",
        "worker": "Worker A / local_data_source_inventory",
        "generated_at_utc": finished,
        "run_started_utc": started,
        "route_dir": rel_or_abs(OUT_DIR.parent.parent),
        "write_scope": rel_or_abs(OUT_DIR),
        "safe_flags": SAFE_FLAGS,
        "task_boundaries": {
            "non_destructive_filesystem_only": True,
            "paid_api_vendor_calls_run": False,
            "live_mt5_calls_run": False,
            "files_written_outside_write_scope": False,
            "validation_safe": False,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
        "context_files_read": [
            "AGENTS.md",
            ".context/LIVE_STATE.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/research_operating_doctrine.md",
            "research/science_program_2026_05/04_goal_prompts/WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H_GOAL_PROMPT_2026-05-15.md",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/",
            ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
        ],
        "source_roots_searched": root_specs,
        "candidate_heavy_data_roots": candidate_matrix,
        "root_scans": scans,
        "direct_indexes": direct_indexes,
        "source_use_cautions": build_cautions(),
        "blockers_and_access_needs": blockers,
        "highest_value_immediate_data_routes": routes,
    }

    json_path = OUT_DIR / "DATA_SOURCE_INVENTORY_2026-05-15.json"
    json_path.write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8", newline="\n")

    write_jsonl(
        OUT_DIR / "SOURCE_ROOT_SCAN_LEDGER_2026-05-15.jsonl",
        [
            {
                "root_id": root_id,
                "path": scan["path"],
                "status": scan["status"],
                "exists": scan["exists"],
                "file_count": scan["file_count"],
                "dir_count": scan["dir_count"],
                "total_bytes": scan["total_bytes"],
                "family_counts": scan["family_counts"],
                "latest_mtime_utc": scan["latest_mtime_utc"],
                "truncated": scan["truncated"],
                "safe_flags": SAFE_FLAGS,
            }
            for root_id, scan in sorted(scans.items())
        ],
    )
    write_jsonl(OUT_DIR / "CANDIDATE_HEAVY_DATA_ROOTS_2026-05-15.jsonl", candidate_matrix)
    write_jsonl(OUT_DIR / "BLOCKERS_AND_ACCESS_NEEDS_2026-05-15.jsonl", blockers)
    write_jsonl(OUT_DIR / "HIGHEST_VALUE_DATA_ROUTES_2026-05-15.jsonl", routes)

    found = [row for row in candidate_matrix if row["status"] == "found"]
    missing = [row for row in candidate_matrix if row["status"] == "missing"]
    family_totals: Counter[str] = Counter()
    for scan in scans.values():
        family_totals.update(scan.get("family_counts", {}))

    summary_lines = [
        "# Worker A Local Data Source Inventory",
        "",
        f"Generated: {finished}",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
        "",
        "## Scope",
        "",
        "- Non-destructive local filesystem inventory only.",
        "- No paid/API/vendor calls were run.",
        "- No live MT5 calls were run.",
        "- Files were written only under this subagent data-inventory scope.",
        "",
        "## Source Roots Searched",
        "",
        "| Root | Status | Files | Dirs | Latest mtime UTC | Policy |",
        "|---|---:|---:|---:|---|---|",
    ]
    for root_id, scan in sorted(scans.items()):
        policy = next((spec["policy"] for spec in root_specs if spec["root_id"] == root_id), "")
        summary_lines.append(
            f"| `{root_id}` | `{scan['status']}` | {scan['file_count']} | {scan['dir_count']} | {scan['latest_mtime_utc'] or ''} | {policy} |"
        )

    summary_lines.extend(
        [
            "",
            "## File Counts By Family",
            "",
            "Counts below are per-root aggregate counts and intentionally not deduplicated across nested roots. Use `root_scans` in the JSON artifact for exact per-root counts before consuming sources.",
            "",
            "| Family | Files |",
            "|---|---:|",
        ]
    )
    for family, count_value in sorted(family_totals.items(), key=lambda item: (-item[1], item[0])):
        summary_lines.append(f"| `{family}` | {count_value} |")

    summary_lines.extend(
        [
            "",
            "## Candidate Heavy Roots",
            "",
            f"- Found candidate roots: {len(found)}",
            f"- Missing candidate roots: {len(missing)}",
            "",
            "Found roots:",
        ]
    )
    for row in found:
        summary_lines.append(f"- `{row['root_id']}`: `{row['path']}`")
    summary_lines.append("")
    summary_lines.append("Missing roots:")
    for row in missing:
        summary_lines.append(f"- `{row['root_id']}`: `{row['path']}`")

    summary_lines.extend(
        [
            "",
            "## Exact Blockers / Access Needs",
            "",
        ]
    )
    local_absence = [b for b in blockers if b["blocker_type"] == "local_absence"]
    read_errors = [b for b in blockers if b["blocker_type"] == "filesystem_read_error"]
    other_blockers = [
        b
        for b in blockers
        if b["blocker_type"] not in {"local_absence", "filesystem_read_error"}
    ]
    for blocker in local_absence:
        summary_lines.append(
            f"- `{blocker['blocker_type']}` at `{blocker['root_id']}` (`{blocker['path']}`): {blocker['access_need']}"
        )
    if read_errors:
        by_root = Counter(b["root_id"] for b in read_errors)
        summary_lines.append(
            f"- `filesystem_read_error`: {len(read_errors)} exact rows captured in `BLOCKERS_AND_ACCESS_NEEDS_2026-05-15.jsonl`; likely transient/racy stale paths from parallel worktrees unless reproduced."
        )
        for root_id, count_value in sorted(by_root.items()):
            summary_lines.append(f"  - `{root_id}`: {count_value} read-error rows")
    for blocker in other_blockers:
        summary_lines.append(
            f"- `{blocker['blocker_type']}` at `{blocker['root_id']}` (`{blocker['path']}`): {blocker['access_need']}"
        )

    summary_lines.extend(
        [
            "",
            "## Source-Use Cautions",
            "",
        ]
    )
    for caution in build_cautions():
        summary_lines.append(f"- `{caution['source_family']}`: {caution['caution']}")

    summary_lines.extend(
        [
            "",
            "## Highest-Value Immediate Data Routes",
            "",
        ]
    )
    for route in routes:
        summary_lines.append(
            f"{route['rank_hint']}. {route['route']} - {route['why_high_value']} Caution: {route['cautions']}"
        )

    summary_lines.extend(
        [
            "",
            "## Machine-Readable Artifacts",
            "",
            "- `DATA_SOURCE_INVENTORY_2026-05-15.json`",
            "- `SOURCE_ROOT_SCAN_LEDGER_2026-05-15.jsonl`",
            "- `CANDIDATE_HEAVY_DATA_ROOTS_2026-05-15.jsonl`",
            "- `BLOCKERS_AND_ACCESS_NEEDS_2026-05-15.jsonl`",
            "- `HIGHEST_VALUE_DATA_ROUTES_2026-05-15.jsonl`",
        ]
    )
    (OUT_DIR / "DATA_SOURCE_INVENTORY_SUMMARY_2026-05-15.md").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
