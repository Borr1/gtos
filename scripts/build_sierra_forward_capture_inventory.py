#!/usr/bin/env python3
"""Build Sierra forward-capture readiness inventory.

Research/tooling only. Scans local Sierra `.scid`, `.depth`, and exported
SCID CSV files, then reports freshness/coverage for first-wave source
symbols. It does not open Sierra Chart and does not fetch data.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "sierra_forward_capture_inventory_v1"

DEFAULT_ROOTS = (
    "C:/SierraChart/Data",
    "data/sierrachart_exports",
    "research/sierrachart_data_source_research_2026-05-02",
)

CORE_SYMBOLS = (
    "NQ",
    "MNQ",
    "YM",
    "MYM",
    "GC",
    "MGC",
    "SI",
    "SIL",
    "6J",
    "6B",
    "6E",
    "ES",
    "MES",
    "CL",
    "ZN",
    "VXM",
    "VXMM",
    "XAUUSD",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mtime_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def infer_symbol(path: Path) -> str:
    stem = path.name
    for marker in (".", "_"):
        if marker in stem:
            stem = stem.split(marker, 1)[0]
            break
    contract = stem.upper()
    for root in sorted(CORE_SYMBOLS, key=len, reverse=True):
        if contract.startswith(root):
            return root
    return contract


def _count_csv_rows(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            rows = sum(1 for _ in handle)
        return max(rows - 1, 0)
    except OSError:
        return None


def _record_count(path: Path) -> int | None:
    suffix = path.suffix.lower()
    try:
        if suffix == ".scid":
            from scripts.inspect_sierra_scid import parse_header

            return parse_header(path).record_count
        if suffix == ".depth":
            from scripts.extract_sierra_depth_features import read_header

            return read_header(path).record_count
        if path.name.lower().endswith("_scid.csv") or suffix == ".csv":
            return _count_csv_rows(path)
    except Exception:
        return None
    return None


def discover_files(roots: list[Path]) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    suffixes = {".scid", ".depth", ".csv"}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in suffixes:
                continue
            lower_name = path.name.lower()
            if path.suffix.lower() == ".csv" and "scid" not in lower_name:
                continue
            files.append(
                {
                    "path": str(path),
                    "name": path.name,
                    "symbol_root": infer_symbol(path),
                    "kind": "depth" if path.suffix.lower() == ".depth" else "scid",
                    "size_bytes": path.stat().st_size,
                    "last_modified_utc": _mtime_utc(path),
                    "record_count": _record_count(path),
                }
            )
    return sorted(files, key=lambda row: (row["symbol_root"], row["kind"], row["path"]))


def classify_symbol(files: list[dict[str, Any]]) -> str:
    has_scid = any(row["kind"] == "scid" and row["size_bytes"] > 0 for row in files)
    has_depth = any(row["kind"] == "depth" and row["size_bytes"] > 0 for row in files)
    if has_scid and has_depth:
        return "READY_SCID_AND_DEPTH_PRESENT"
    if has_scid:
        return "CAUTION_SCID_PRESENT_DEPTH_MISSING"
    if has_depth:
        return "CAUTION_DEPTH_PRESENT_SCID_MISSING"
    return "BLOCKED_MISSING_LOCAL_SIERRA_FILES"


def build_inventory(
    *,
    roots: list[Path],
    expected_symbols: list[str] | None = None,
) -> dict[str, Any]:
    symbols = expected_symbols or list(CORE_SYMBOLS)
    files = discover_files(roots)
    by_symbol: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in symbols}
    for row in files:
        symbol = row["symbol_root"]
        if symbol in by_symbol:
            by_symbol[symbol].append(row)
    symbol_rows = []
    for symbol in symbols:
        symbol_files = by_symbol[symbol]
        scid_files = [row for row in symbol_files if row["kind"] == "scid"]
        depth_files = [row for row in symbol_files if row["kind"] == "depth"]
        symbol_rows.append(
            {
                "symbol_root": symbol,
                "status": classify_symbol(symbol_files),
                "scid_file_count": len(scid_files),
                "depth_file_count": len(depth_files),
                "latest_scid_utc": max((row["last_modified_utc"] for row in scid_files), default=None),
                "latest_depth_utc": max((row["last_modified_utc"] for row in depth_files), default=None),
                "scid_record_count_total": sum(row["record_count"] or 0 for row in scid_files),
                "depth_record_count_total": sum(row["record_count"] or 0 for row in depth_files),
                "files": symbol_files,
            }
        )
    status_counts: dict[str, int] = {}
    for row in symbol_rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now_iso(),
        "scope": "research/tooling only",
        "promotion_verdict": PROMOTION_VERDICT,
        "roots": [str(root) for root in roots],
        "expected_symbols": symbols,
        "status_counts": dict(sorted(status_counts.items())),
        "files_discovered": len(files),
        "symbols": symbol_rows,
        "operator_boundary": (
            "Codex can inspect existing files only. Missing or stale symbols require "
            "Sierra Chart/chartbook/operator capture steps."
        ),
    }


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Sierra Forward Capture Readiness - 2026-05-04",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "**Scope:** research/tooling only; no live trading behavior changes.",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in payload["status_counts"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## Symbol Coverage",
            "",
            "| Symbol | Status | SCID files | Depth files | SCID rows | Depth records | Latest SCID | Latest depth |",
            "|---|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in payload["symbols"]:
        lines.append(
            "| {symbol} | `{status}` | {scid_files} | {depth_files} | {scid_rows} | {depth_rows} | {latest_scid} | {latest_depth} |".format(
                symbol=row["symbol_root"],
                status=row["status"],
                scid_files=row["scid_file_count"],
                depth_files=row["depth_file_count"],
                scid_rows=row["scid_record_count_total"],
                depth_rows=row["depth_record_count_total"],
                latest_scid=row["latest_scid_utc"] or "n/a",
                latest_depth=row["latest_depth_utc"] or "n/a",
            )
        )
    lines.extend(
        [
            "",
            "## Operator Boundary",
            "",
            payload["operator_boundary"],
        ]
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", dest="roots", default=None)
    parser.add_argument("--symbol", action="append", dest="symbols", default=None)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    roots = [Path(root) for root in (args.roots or DEFAULT_ROOTS)]
    payload = build_inventory(roots=roots, expected_symbols=args.symbols)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps({"output_json": str(output_json), "output_md": str(output_md), "status_counts": payload["status_counts"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
