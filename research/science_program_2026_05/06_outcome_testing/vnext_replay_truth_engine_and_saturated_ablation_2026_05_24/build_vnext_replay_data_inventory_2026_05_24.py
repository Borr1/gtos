"""Inventory local data/source roots for the vNext replay truth engine.

The output is source coverage, not replay performance. It records what can be
used later for event construction, path simulation, source repair, and exact
gap proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]

PREREG_PATH = ROUTE_DIR / "VNEXT_REPLAY_PREREGISTRATION_MANIFEST_2026-05-24.json"
DATA_COVERAGE_PATH = ROUTE_DIR / "VNEXT_REPLAY_DATA_COVERAGE_LEDGER_2026-05-24.jsonl"
DATA_SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_DATA_COVERAGE_SUMMARY_2026-05-24.json"
SOURCE_GAP_PATH = ROUTE_DIR / "VNEXT_REPLAY_SOURCE_GAP_LEDGER_2026-05-24.jsonl"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"

HASH_BYTES_LIMIT = 128 * 1024 * 1024
TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".ps1",
    ".py",
    ".bat",
    ".ini",
    ".log",
}
SESSION_TOKENS = {
    "london": "london",
    "london_core": "london_core",
    "ny": "ny",
    "ny_core": "ny_core",
    "tokyo": "tokyo",
    "tokyo_kz": "tokyo_kz",
    "off_core": "off_core_session",
    "off_kz": "off_kz",
}
TIMEFRAME_RE = re.compile(r"(?i)(?:^|[^A-Z0-9])(M1|M5|M15|H1|H4|D1)(?:$|[^A-Z0-9])")
DATE_RE = re.compile(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)")


def repo_path(path: Path | str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    if os.name == "nt":
        resolved = str(candidate.resolve(strict=False))
        if not resolved.startswith("\\\\?\\"):
            return Path("\\\\?\\" + resolved)
    return candidate


def display_path(path: Path) -> str:
    text = str(path)
    if text.startswith("\\\\?\\"):
        text = text[4:]
    try:
        rel = Path(text).resolve(strict=False).relative_to(REPO_ROOT)
        return rel.as_posix()
    except ValueError:
        return Path(text).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int | None:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return None
    count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def stable_hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


def root_specs() -> list[dict[str, Any]]:
    prereg = load_json(PREREG_PATH)
    roots = prereg["data_universe_roots_to_inventory_next"]
    specs: list[dict[str, Any]] = []
    for root in roots:
        root_path = Path(root)
        if not root_path.is_absolute():
            root_path = REPO_ROOT / root_path
        specs.append(
            {
                "root": str(root),
                "abs_path": root_path,
                "source": "preregistered_data_universe_root",
            }
        )
    return specs


def is_generated_route_output(path: Path) -> bool:
    text = display_path(path)
    return (
        "06_outcome_testing/vnext_replay_truth_engine_and_saturated_ablation_2026_05_24/"
        in text
        or "06_outcome_testing/gtos_vnext_replay_truth_engine/" in text
    )


def iter_files(root: Path) -> Iterable[Path]:
    root = repo_path(root)
    if not root.exists() or not root.is_dir():
        return
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if d not in {".git", ".mypy_cache", ".pytest_cache", "__pycache__"}]
        for name in files:
            candidate = current_path / name
            if is_generated_route_output(candidate):
                continue
            yield candidate


def source_family(path_display: str, suffix: str) -> str:
    lower = path_display.lower()
    if "/data/ticks/" in lower or "\\data\\ticks\\" in lower:
        return "tick_data"
    if "sierra" in lower or suffix in {".scid", ".dly"}:
        return "sierra_or_orderflow_data"
    if "/data/historical" in lower or "/data/mt5_research_exports" in lower:
        return "historical_ohlc"
    if lower.startswith("shadow_logs/") or "/shadow_logs/" in lower:
        return "shadow_log"
    if lower.startswith("knowledge_base/") or "/knowledge_base/" in lower:
        return "knowledge_base"
    if "science_program_2026_05" in lower:
        return "research_artifact"
    if "/data/" in lower or lower.startswith("data/"):
        return "data_artifact"
    if "c:/tmp" in lower:
        return "prior_worktree_or_temp_cache"
    return "local_source_file"


def infer_timeframes(text: str) -> list[str]:
    found = {match.group(1).upper() for match in TIMEFRAME_RE.finditer(text)}
    return sorted(found)


def infer_dates(text: str) -> list[str]:
    dates = []
    for year, month, day in DATE_RE.findall(text):
        dates.append(f"{year}-{month}-{day}")
    return sorted(set(dates))


def infer_sessions(text: str) -> list[str]:
    lower = text.lower()
    sessions = {value for token, value in SESSION_TOKENS.items() if token in lower}
    return sorted(sessions)


def infer_symbols(text: str, symbols: list[str]) -> list[str]:
    upper = text.upper()
    found = []
    for symbol in symbols:
        if symbol and symbol.upper() in upper:
            found.append(symbol)
    return found[:20]


def file_row(path: Path, roots: list[str], symbols: list[str]) -> dict[str, Any]:
    stat = path.stat()
    path_display = display_path(path)
    suffix = path.suffix.lower()
    should_hash = stat.st_size <= HASH_BYTES_LIMIT
    return {
        "schema_version": "vnext_replay_data_coverage_v1",
        "path": path_display,
        "matched_roots": sorted(roots),
        "source_family": source_family(path_display, suffix),
        "extension": suffix,
        "bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "sha256": sha256_file(path) if should_hash else None,
        "hash_status": "HASHED" if should_hash else "DEFERRED_LARGE_FILE_NOT_CONSUMED_YET",
        "line_count": line_count(path) if should_hash else None,
        "symbol_hints": infer_symbols(path_display, symbols),
        "timeframe_hints": infer_timeframes(path_display),
        "date_hints": infer_dates(path_display),
        "session_hints": infer_sessions(path_display),
        "source_use_status": "INVENTORIED_NOT_YET_CONSUMED_FOR_REPLAY",
    }


def build_inventory() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    prereg = load_json(PREREG_PATH)
    freeze_markets = prereg["freeze_facts"]["freeze_summary"]
    # The full symbol map lives in the freeze summary file. Fallback to an empty list if
    # an older manifest shape is ever supplied.
    freeze_summary_path = repo_path(
        "research/science_program_2026_05/06_outcome_testing/"
        "gtos_vnext_research_to_runtime_builder/"
        "GTOS_VNEXT_FINAL_CONVERSION_FREEZE_SUMMARY_2026-05-23.json"
    )
    freeze_summary = load_json(freeze_summary_path)
    symbols = sorted(
        (freeze_summary.get("markets_symbols_timeframes_sessions_sides", {}).get("symbols") or {}).keys(),
        key=len,
        reverse=True,
    )
    path_to_roots: dict[str, list[str]] = defaultdict(list)
    missing_roots = []
    root_status = []
    for spec in root_specs():
        root_abs = repo_path(spec["abs_path"])
        exists = root_abs.exists()
        root_status.append(
            {
                "root": spec["root"],
                "exists": exists,
                "is_dir": root_abs.is_dir() if exists else False,
                "source": spec["source"],
            }
        )
        if not exists or not root_abs.is_dir():
            missing_roots.append(spec["root"])
            continue
        for path in iter_files(root_abs):
            path_to_roots[display_path(path)].append(spec["root"])
    rows = []
    for path_display, roots in sorted(path_to_roots.items()):
        rows.append(file_row(repo_path(path_display), roots, symbols))
    gap_rows = []
    for root in missing_roots:
        gap_rows.append(
            {
                "schema_version": "vnext_replay_source_gap_v1",
                "stage_id": "STAGE_02_EXHAUSTIVE_DATA_INVENTORY_AND_SOURCE_ACQUISITION",
                "gap_type": "missing_preregistered_data_root",
                "source_path": root,
                "attempts_executed": [
                    "checked preregistered data root existence",
                    "recorded root for later source acquisition if a replay shard needs it",
                ],
                "terminal_status": "NOT_TERMINAL_UNTIL_REPLAY_NEED_AND_ALTERNATE_ROOTS_EXHAUSTED",
                "next_action": "Use alternate local roots, reconstruction, proxy, or read-only export route when a replay event requires this source class.",
            }
        )
    if not missing_roots:
        gap_rows.append(
            {
                "schema_version": "vnext_replay_source_gap_v1",
                "stage_id": "STAGE_02_EXHAUSTIVE_DATA_INVENTORY_AND_SOURCE_ACQUISITION",
                "gap_type": "preregistered_data_roots",
                "attempts_executed": ["checked every preregistered data root"],
                "terminal_status": "ALL_PREREGISTERED_DATA_ROOTS_PRESENT",
                "next_action": "Proceed to event construction and row-level source-needs checks.",
            }
        )
    family_counts = Counter(row["source_family"] for row in rows)
    extension_counts = Counter(row["extension"] or "<none>" for row in rows)
    hash_counts = Counter(row["hash_status"] for row in rows)
    summary = {
        "schema_version": "vnext_replay_data_coverage_summary_v1",
        "generated_utc": utc_now(),
        "stage_id": "STAGE_02_EXHAUSTIVE_DATA_INVENTORY_AND_SOURCE_ACQUISITION",
        "row_count": len(rows),
        "root_status": root_status,
        "missing_root_count": len(missing_roots),
        "missing_roots": missing_roots,
        "source_family_counts": dict(sorted(family_counts.items())),
        "extension_counts": dict(sorted(extension_counts.items())),
        "hash_status_counts": dict(sorted(hash_counts.items())),
        "total_bytes_inventoried": sum(row["bytes"] for row in rows),
        "hashed_bytes_inventoried": sum(row["bytes"] for row in rows if row["hash_status"] == "HASHED"),
        "symbol_hint_row_count": sum(1 for row in rows if row["symbol_hints"]),
        "timeframe_hint_row_count": sum(1 for row in rows if row["timeframe_hints"]),
        "date_hint_row_count": sum(1 for row in rows if row["date_hints"]),
        "session_hint_row_count": sum(1 for row in rows if row["session_hints"]),
        "freeze_summary_runtime_artifacts": freeze_markets.get("generated_runtime_artifact_count"),
        "inventory_policy": {
            "deduplicated_overlapping_roots": True,
            "generated_current_route_outputs_excluded": True,
            "hash_bytes_limit": HASH_BYTES_LIMIT,
            "large_files_not_consumed_for_replay_yet": True,
            "no_top_n_sampling": True,
        },
    }
    return rows, summary, gap_rows


def update_source_gap_ledger(stage2_gap_rows: list[dict[str, Any]]) -> None:
    existing = read_jsonl(SOURCE_GAP_PATH) if SOURCE_GAP_PATH.exists() else []
    existing = [
        row
        for row in existing
        if row.get("stage_id") != "STAGE_02_EXHAUSTIVE_DATA_INVENTORY_AND_SOURCE_ACQUISITION"
    ]
    write_jsonl(SOURCE_GAP_PATH, [*existing, *stage2_gap_rows])


def update_output_manifest() -> None:
    outputs = []
    for path in [PREREG_PATH, DATA_COVERAGE_PATH, DATA_SUMMARY_PATH, SOURCE_GAP_PATH]:
        stat = path.stat()
        outputs.append(
            {
                "path": display_path(path),
                "exists": True,
                "bytes": stat.st_size,
                "lines": line_count(path),
                "sha256": sha256_file(path),
                "source_kind": "generated_replay_output",
            }
        )
    manifest = {
        "schema_version": "vnext_replay_output_manifest_v1",
        "generated_utc": utc_now(),
        "route_id": "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24",
        "outputs": outputs,
        "next_stage": "STAGE_03_RUNTIME_TRUTH_HARNESS",
    }
    write_json(OUTPUT_MANIFEST_PATH, manifest)


def build_outputs() -> dict[str, Any]:
    rows, summary, gap_rows = build_inventory()
    write_jsonl(DATA_COVERAGE_PATH, rows)
    write_json(DATA_SUMMARY_PATH, summary)
    update_source_gap_ledger(gap_rows)
    update_output_manifest()
    return summary


def check_outputs() -> None:
    rows, summary, gap_rows = build_inventory()
    existing_rows = read_jsonl(DATA_COVERAGE_PATH)
    if existing_rows != rows:
        raise AssertionError("Data coverage ledger is stale; rerun inventory builder")
    existing_summary = load_json(DATA_SUMMARY_PATH)
    existing_summary_no_time = dict(existing_summary)
    expected_summary_no_time = dict(summary)
    existing_summary_no_time.pop("generated_utc", None)
    expected_summary_no_time.pop("generated_utc", None)
    if existing_summary_no_time != expected_summary_no_time:
        raise AssertionError("Data coverage summary is stale; rerun inventory builder")
    existing_gaps = [
        row
        for row in read_jsonl(SOURCE_GAP_PATH)
        if row.get("stage_id") == "STAGE_02_EXHAUSTIVE_DATA_INVENTORY_AND_SOURCE_ACQUISITION"
    ]
    if existing_gaps != gap_rows:
        raise AssertionError("Stage 02 source-gap rows are stale")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("vNext replay data inventory check passed")
        return
    summary = build_outputs()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
