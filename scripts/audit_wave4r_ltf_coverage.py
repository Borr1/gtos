#!/usr/bin/env python3
"""Audit lower-timeframe/tick coverage for Wave4R ordered-path gaps.

This is a read-only source-coverage tool. It does not infer fills or change
replay outcomes; it only proves whether local M1/tick evidence exists for the
symbol/date rows whose ordered touch times are still missing.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


DATE_RE = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})")
GZIP_MAGIC = b"\x1f\x8b"
MISSING_STATUS = "ordered_touch_times_missing"


def _is_gzip(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(2) == GZIP_MAGIC
    except OSError:
        return False


def _open_jsonl(path: Path):
    if _is_gzip(path):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def canonical_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def date_from_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    match = DATE_RE.search(str(value))
    return match.group("date") if match else None


def _source_type(path: Path) -> str | None:
    parts = {part.lower() for part in path.parts}
    if "ticks" in parts:
        return "tick"
    if "m1" in parts:
        return "m1"
    if "mt5_research_exports" in parts:
        return "mt5_research_export"
    return None


def _candidate_symbol_from_path(path: Path) -> str | None:
    parent = path.parent.name
    if not parent or parent.startswith(".") or parent.startswith("_"):
        return None
    if DATE_RE.fullmatch(parent):
        return None
    if parent.lower() in {"m1", "ticks", "mt5_research_exports"}:
        return None
    return canonical_symbol(parent)


def iter_ltf_files(source_roots: Iterable[Path]) -> Iterable[Path]:
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "_corrupt_quarantine" in {part.lower() for part in path.parts}:
                continue
            if path.name.startswith(".") or path.suffix.lower() not in {".csv", ".parquet"}:
                continue
            yield path


def index_ltf_files(source_roots: Iterable[Path]) -> dict[str, Any]:
    files_by_key: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    files_by_type: Counter[str] = Counter()
    symbol_dates_by_type: dict[str, set[tuple[str, str]]] = defaultdict(set)
    missing_date_or_symbol: list[str] = []
    for path in iter_ltf_files(source_roots):
        date = date_from_value(path.name)
        symbol = _candidate_symbol_from_path(path)
        source_type = _source_type(path)
        if not date or not symbol or not source_type:
            missing_date_or_symbol.append(str(path))
            continue
        key = (source_type, symbol, date)
        files_by_key[key].append(str(path))
        files_by_type[source_type] += 1
        symbol_dates_by_type[source_type].add((symbol, date))

    inventory_by_type: dict[str, Any] = {}
    for source_type, symbol_dates in sorted(symbol_dates_by_type.items()):
        dates = sorted({date for _, date in symbol_dates})
        symbols = sorted({symbol for symbol, _ in symbol_dates})
        inventory_by_type[source_type] = {
            "file_count": int(files_by_type[source_type]),
            "symbol_count": len(symbols),
            "symbols": symbols,
            "date_count": len(dates),
            "date_min": dates[0] if dates else None,
            "date_max": dates[-1] if dates else None,
            "symbol_date_count": len(symbol_dates),
        }
    return {
        "files_by_key": files_by_key,
        "inventory_by_type": inventory_by_type,
        "files_missing_date_or_symbol": missing_date_or_symbol,
    }


def scan_ordered_path_coverage(
    ordered_path_ledger: Path,
    files_by_key: Mapping[tuple[str, str, str], list[str]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = 0
    missing_rows = 0
    matched_m1_rows = 0
    matched_tick_rows = 0
    matched_any_rows = 0
    missing_date_rows = 0
    by_symbol: Counter[str] = Counter()
    by_year: Counter[str] = Counter()
    by_recovery_status: Counter[str] = Counter()
    by_source_status: Counter[str] = Counter()
    requirement_rows: dict[tuple[str, str], dict[str, Any]] = {}
    dates: list[str] = []

    with _open_jsonl(ordered_path_ledger) as handle:
        for line in handle:
            if not line.strip():
                continue
            rows += 1
            row = json.loads(line)
            status = row.get("ordered_path_source_status") or row.get("source_status")
            if status != MISSING_STATUS:
                continue
            missing_rows += 1
            symbol = canonical_symbol(row.get("symbol"))
            date = date_from_value(row.get("asof_utc"))
            if not date:
                missing_date_rows += 1
                date = "DATE_MISSING"
            else:
                dates.append(date)
            year = date[:4] if date != "DATE_MISSING" else "DATE_MISSING"
            by_symbol[symbol] += 1
            by_year[year] += 1
            by_recovery_status[str(row.get("recovery_status") or "")] += 1
            by_source_status[str(status)] += 1

            m1_paths = files_by_key.get(("m1", symbol, date), [])
            tick_paths = files_by_key.get(("tick", symbol, date), [])
            matched_m1 = bool(m1_paths)
            matched_tick = bool(tick_paths)
            if matched_m1:
                matched_m1_rows += 1
            if matched_tick:
                matched_tick_rows += 1
            if matched_m1 or matched_tick:
                matched_any_rows += 1

            key = (symbol, date)
            req = requirement_rows.setdefault(
                key,
                {
                    "symbol": symbol,
                    "date": date,
                    "missing_ordered_touch_rows": 0,
                    "matched_local_m1_file_count": len(m1_paths),
                    "matched_local_tick_file_count": len(tick_paths),
                    "matched_local_m1_paths": sorted(m1_paths),
                    "matched_local_tick_paths": sorted(tick_paths),
                    "coverage_status": (
                        "local_ltf_match_available"
                        if matched_m1 or matched_tick
                        else "local_ltf_missing"
                    ),
                    "sample_candidate_ids": [],
                    "sample_asof_utc": [],
                },
            )
            req["missing_ordered_touch_rows"] += 1
            if len(req["sample_candidate_ids"]) < 5:
                req["sample_candidate_ids"].append(row.get("candidate_id"))
            if len(req["sample_asof_utc"]) < 5:
                req["sample_asof_utc"].append(row.get("asof_utc"))

    date_min = min(dates) if dates else None
    date_max = max(dates) if dates else None
    requirements = sorted(
        requirement_rows.values(),
        key=lambda item: (item["coverage_status"], item["symbol"], item["date"]),
    )
    summary = {
        "ordered_path_ledger": str(ordered_path_ledger),
        "rows_scanned": rows,
        "missing_ordered_touch_rows": missing_rows,
        "missing_date_rows": missing_date_rows,
        "missing_symbol_date_pairs": len(requirements),
        "missing_date_min": date_min,
        "missing_date_max": date_max,
        "matched_local_m1_rows": matched_m1_rows,
        "matched_local_tick_rows": matched_tick_rows,
        "matched_any_local_ltf_rows": matched_any_rows,
        "unmatched_local_ltf_rows": missing_rows - matched_any_rows,
        "by_symbol": dict(sorted(by_symbol.items())),
        "by_year": dict(sorted(by_year.items())),
        "by_recovery_status": dict(sorted(by_recovery_status.items())),
        "by_source_status": dict(sorted(by_source_status.items())),
    }
    return summary, requirements


def build_report(
    *,
    ordered_path_ledger: Path,
    source_roots: Iterable[Path],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    roots = tuple(source_roots)
    index = index_ltf_files(roots)
    summary, requirements = scan_ordered_path_coverage(
        ordered_path_ledger,
        index["files_by_key"],
    )
    report = {
        "schema_version": "wave4r_ltf_coverage_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "source_boundary": (
            "read_only_local_file_coverage_audit_no_fill_inference_no_replay_mutation"
        ),
        "source_roots_checked": [str(root) for root in roots],
        "local_ltf_inventory": index["inventory_by_type"],
        "files_missing_date_or_symbol": index["files_missing_date_or_symbol"],
        "coverage_summary": summary,
        "verdict": {
            "local_ltf_can_repair_current_missing_rows": summary[
                "matched_any_local_ltf_rows"
            ]
            > 0,
            "rows_with_local_ltf_match": summary["matched_any_local_ltf_rows"],
            "rows_still_requiring_external_ltf_or_tick_source": summary[
                "unmatched_local_ltf_rows"
            ],
            "required_evidence": (
                "broker-native M1/tick files matching each missing symbol/date, "
                "or an owner-approved read-only MT5 export for those windows"
            ),
        },
    }
    return report, requirements


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ordered-path-ledger", required=True, type=Path)
    parser.add_argument("--source-root", action="append", type=Path, default=[])
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-jsonl", required=True, type=Path)
    args = parser.parse_args()

    report, requirements = build_report(
        ordered_path_ledger=args.ordered_path_ledger,
        source_roots=args.source_root,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_jsonl(args.output_jsonl, requirements)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
