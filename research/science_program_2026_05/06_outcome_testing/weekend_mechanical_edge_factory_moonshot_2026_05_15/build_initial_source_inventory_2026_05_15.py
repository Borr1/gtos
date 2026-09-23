#!/usr/bin/env python3
"""Build the parent-side initial source inventory for the 60h moonshot route.

This is read-only. It inventories metadata, line counts, and selected hashes for
reachable local sources without opening paid/vendor/live surfaces.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
UTC_NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

WORKTREE_ROOTS = [
    "data",
    "shadow_logs",
    "research",
    "knowledge_base",
    "src",
    "scripts",
    "config",
    "tests",
    "pipeline_state",
]

ABSOLUTE_ROOTS = [
    Path(r"C:\Users\MSI\Documents\ai-trading-agent\data"),
    Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks"),
    Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\external"),
    Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"),
    Path(r"C:\Users\MSI\Documents\ai-trading-agent\exports"),
    Path(r"C:\tmp\gtos_otb"),
    Path(r"C:\SierraChart"),
]

SOURCE_FAMILY_RULES = [
    ("tick_data", ("tick", "ticks", ".parquet")),
    ("sierra_scid", (".scid", "sierra")),
    ("sierra_depth", (".depth", "marketdepth", "depth")),
    ("shadow_log", ("shadow_logs", ".jsonl")),
    ("research_artifact", ("research", ".md", ".json", ".jsonl", ".csv")),
    ("source_code", ("src", "scripts", ".py")),
    ("config", ("config", ".yaml", ".yml", ".toml")),
    ("test", ("tests", "test_", ".pytest")),
    ("knowledge_base", ("knowledge_base", "trade_records")),
    ("pipeline_state", ("pipeline_state", "heartbeat")),
    ("market_csv", (".csv", "historical")),
]

TEXT_EXTS = {".md", ".txt", ".json", ".jsonl", ".csv", ".yaml", ".yml", ".py", ".toml", ".ps1"}
HASH_EXTS = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".toml"}
MAX_FILES_PER_ROOT = 50000
MAX_HASH_BYTES = 2_000_000
MAX_LINE_BYTES = 10_000_000


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def classify(path: Path) -> str:
    text = str(path).lower()
    ext = path.suffix.lower()
    for family, needles in SOURCE_FAMILY_RULES:
        for needle in needles:
            if needle.startswith("."):
                if ext == needle:
                    return family
            elif needle in text:
                return family
    return "other"


def sha256_file(path: Path) -> str | None:
    try:
        size = path.stat().st_size
        if size > MAX_HASH_BYTES or path.suffix.lower() not in HASH_EXTS:
            return None
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def line_count(path: Path) -> int | None:
    try:
        size = path.stat().st_size
        if size > MAX_LINE_BYTES or path.suffix.lower() not in TEXT_EXTS:
            return None
        count = 0
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                count += chunk.count(b"\n")
        return count
    except OSError:
        return None


def iter_files(root: Path) -> Iterable[Path]:
    seen = 0
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules"}
        ]
        for filename in filenames:
            seen += 1
            if seen > MAX_FILES_PER_ROOT:
                return
            yield Path(dirpath) / filename


def inspect_root(root: Path, label: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    root_record: dict[str, object] = {
        "label": label,
        "path": str(root),
        "exists": root.exists(),
        "is_dir": root.is_dir() if root.exists() else False,
        "status": "missing",
        "file_count": 0,
        "total_bytes": 0,
        "family_counts": {},
        "extension_counts": {},
        "newest_file_utc": None,
        "errors": [],
    }
    rows: list[dict[str, object]] = []
    if not root.exists():
        return root_record, rows
    if not root.is_dir():
        root_record["status"] = "not_directory"
        return root_record, rows

    families: Counter[str] = Counter()
    extensions: Counter[str] = Counter()
    newest_ts = 0.0
    status = "ok"

    for path in iter_files(root):
        try:
            stat = path.stat()
        except OSError as exc:
            root_record["errors"].append({"path": str(path), "error": str(exc)})
            continue
        family = classify(path)
        ext = path.suffix.lower() or "<no_ext>"
        families[family] += 1
        extensions[ext] += 1
        root_record["file_count"] = int(root_record["file_count"]) + 1
        root_record["total_bytes"] = int(root_record["total_bytes"]) + stat.st_size
        newest_ts = max(newest_ts, stat.st_mtime)
        rows.append(
            {
                "root_label": label,
                "path": rel(path),
                "family": family,
                "extension": ext,
                "bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "line_count": line_count(path),
                "sha256": sha256_file(path),
            }
        )

    if int(root_record["file_count"]) >= MAX_FILES_PER_ROOT:
        status = "truncated_at_file_cap"
    root_record["status"] = status
    root_record["family_counts"] = dict(sorted(families.items()))
    root_record["extension_counts"] = dict(sorted(extensions.items()))
    if newest_ts:
        root_record["newest_file_utc"] = (
            datetime.fromtimestamp(newest_ts, timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    return root_record, rows


def summarize_shadow_logs(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    shadow_rows = [row for row in rows if row["family"] == "shadow_log"]
    return sorted(
        [
            {
                "path": row["path"],
                "bytes": row["bytes"],
                "modified_utc": row["modified_utc"],
                "line_count": row["line_count"],
            }
            for row in shadow_rows
        ],
        key=lambda item: (item["line_count"] or 0, item["bytes"]),
        reverse=True,
    )


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    columns = [
        "root_label",
        "path",
        "family",
        "extension",
        "bytes",
        "modified_utc",
        "line_count",
        "sha256",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    roots: list[tuple[str, Path]] = [(name, REPO / name) for name in WORKTREE_ROOTS]
    roots.extend((f"absolute::{path.name or str(path)}", path) for path in ABSOLUTE_ROOTS)

    root_records: list[dict[str, object]] = []
    file_rows: list[dict[str, object]] = []
    for label, root in roots:
        root_record, rows = inspect_root(root, label)
        root_records.append(root_record)
        file_rows.extend(rows)

    family_totals: dict[str, int] = defaultdict(int)
    family_bytes: dict[str, int] = defaultdict(int)
    for row in file_rows:
        family = str(row["family"])
        family_totals[family] += 1
        family_bytes[family] += int(row["bytes"])

    payload = {
        "schema": "weekend_mechanical_edge_factory_initial_source_inventory_v1",
        "generated_utc": UTC_NOW,
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "policy": {
            "read_only": True,
            "no_paid_api_vendor_calls": True,
            "no_live_mt5_calls": True,
            "hash_policy": "Small text/control files are SHA256 hashed; large/binary market data is inventoried by metadata pending route-specific source contracts.",
            "file_cap_per_root": MAX_FILES_PER_ROOT,
        },
        "root_records": root_records,
        "family_totals": dict(sorted(family_totals.items())),
        "family_bytes": dict(sorted(family_bytes.items())),
        "shadow_log_line_leaders": summarize_shadow_logs(file_rows)[:100],
        "immediate_data_routes": [
            {
                "route": "shadow_log_market_behavior_mining",
                "source_families": ["shadow_log"],
                "reason": "Fresh large candidate/path/shadow logs are present in LIVE_STATE and source inventory; can drive first no-API descriptor mining.",
            },
            {
                "route": "research_artifact_reuse",
                "source_families": ["research_artifact"],
                "reason": "READY8/SCID/no-API route artifacts preserve candidate universes, controls, and mechanism ledgers for comparison and challenger design.",
            },
            {
                "route": "tick_and_sierra_targeted_contracts",
                "source_families": ["tick_data", "sierra_scid", "sierra_depth"],
                "reason": "Large binary data should be consumed only through route-specific parsers/hashes/as-of contracts; inventory identifies availability without over-claiming validation safety.",
            },
        ],
    }

    write_json(ROUTE_DIR / "DATA_SOURCE_INVENTORY_PARENT_2026-05-15.json", payload)
    write_jsonl(ROUTE_DIR / "DATA_SOURCE_FILE_LEDGER_PARENT_2026-05-15.jsonl", file_rows)
    write_csv(ROUTE_DIR / "DATA_SOURCE_FILE_LEDGER_PARENT_2026-05-15.csv", file_rows)

    md_lines = [
        "# Parent Initial Source Inventory",
        "",
        f"Generated UTC: `{UTC_NOW}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "## Root Summary",
        "",
        "| Root | Status | Files | Bytes | Newest UTC | Families |",
        "|---|---:|---:|---:|---|---|",
    ]
    for root in root_records:
        md_lines.append(
            "| {label} | {status} | {file_count} | {total_bytes} | {newest} | {families} |".format(
                label=root["label"],
                status=root["status"],
                file_count=root["file_count"],
                total_bytes=root["total_bytes"],
                newest=root["newest_file_utc"] or "",
                families=json.dumps(root["family_counts"], sort_keys=True),
            )
        )
    md_lines.extend(
        [
            "",
            "## Family Totals",
            "",
            "| Family | Files | Bytes |",
            "|---|---:|---:|",
        ]
    )
    for family in sorted(family_totals):
        md_lines.append(f"| {family} | {family_totals[family]} | {family_bytes[family]} |")
    md_lines.extend(
        [
            "",
            "## Immediate Data Routes",
            "",
            "- `shadow_log_market_behavior_mining`: use fresh candidate/path/shadow logs for first no-API descriptor mining.",
            "- `research_artifact_reuse`: reuse accepted READY8/SCID/no-API artifacts before inventing new denominators.",
            "- `tick_and_sierra_targeted_contracts`: consume binary tick/SCID/depth data only through route-specific source contracts.",
            "",
            "## Cautions",
            "",
            "- This inventory is source discovery, not validation approval.",
            "- Large/binary files are not fully hashed here; route-specific source contracts must hash and parse them before outcome use.",
            "- Worktree absence remains nonterminal; blocked roots should become access/search tasks, not final data absence claims.",
        ]
    )
    (ROUTE_DIR / "DATA_SOURCE_INVENTORY_PARENT_2026-05-15.md").write_text(
        "\n".join(md_lines) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "ok": True,
                "generated_utc": UTC_NOW,
                "roots": len(root_records),
                "files": len(file_rows),
                "outputs": [
                    "DATA_SOURCE_INVENTORY_PARENT_2026-05-15.json",
                    "DATA_SOURCE_FILE_LEDGER_PARENT_2026-05-15.jsonl",
                    "DATA_SOURCE_FILE_LEDGER_PARENT_2026-05-15.csv",
                    "DATA_SOURCE_INVENTORY_PARENT_2026-05-15.md",
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
