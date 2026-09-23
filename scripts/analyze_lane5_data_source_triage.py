#!/usr/bin/env python3
"""Triage Lane 5 data-source backlog items D-1/D-4/D-5/D-12.

Research/tooling only. Uses local inventories and cached status files to avoid
network, broker, or live-trading changes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = "research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md"
GTOS_SYMBOLS = ("XAUUSD", "XAGUSD", "GBPJPY", "USDJPY", "GBPUSD", "NAS100", "US30_cash")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def tick_inventory(root: Path) -> dict[str, Any]:
    tick_dir = root / "data" / "ticks"
    by_symbol: dict[str, dict[str, Any]] = {}
    for symbol in GTOS_SYMBOLS:
        symbol_dir = tick_dir / symbol
        parquet_files = sorted(symbol_dir.glob("*.parquet"))
        dates = [path.stem for path in parquet_files]
        by_symbol[symbol] = {
            "parquet_files": len(parquet_files),
            "first_date": dates[0] if dates else None,
            "last_date": dates[-1] if dates else None,
            "state_exists": (symbol_dir / ".state.json").exists(),
            "bytes": sum(path.stat().st_size for path in parquet_files),
        }

    all_dates = sorted({date for info in by_symbol.values() for date in [info["first_date"], info["last_date"]] if date})
    return {
        "symbols": by_symbol,
        "symbols_with_ticks": sum(1 for info in by_symbol.values() if info["parquet_files"]),
        "max_symbol_days": max((info["parquet_files"] for info in by_symbol.values()), default=0),
        "first_date_any_symbol": all_dates[0] if all_dates else None,
        "last_date_any_symbol": all_dates[-1] if all_dates else None,
        "tick_features_helper_exists": (root / "src" / "components" / "tick_features.py").exists(),
        "tick_capture_daemon_exists": (root / "src" / "components" / "tick_capture.py").exists(),
    }


def source_text_contains(root: Path, terms: tuple[str, ...]) -> dict[str, bool]:
    scan_roots = [
        root / "src",
        root / "scripts",
        root / "tests",
        root / "research" / "ml_program" / "MASTER_BACKLOG.md",
        root / "research" / "ml_program" / "PRE_REGISTERED_HYPOTHESES.md",
    ]
    found = {term: False for term in terms}
    for scan_root in scan_roots:
        paths = [scan_root] if scan_root.is_file() else list(scan_root.rglob("*.py")) + list(scan_root.rglob("*.md"))
        for path in paths:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            for term in found:
                if term.lower() in text:
                    found[term] = True
    return found


def cftc_inventory(root: Path) -> dict[str, Any]:
    status_dir = root / "data" / "external" / "status"
    normalized_dir = root / "data" / "external" / "normalized" / "cftc_cot"
    statuses = []
    for path in sorted(status_dir.glob("cftc_cot*.json")):
        payload = _read_json(path)
        statuses.append(
            {
                "status_key": payload.get("status_key"),
                "status": payload.get("status"),
                "row_count": payload.get("row_count"),
                "latest_observation_utc": payload.get("latest_observation_utc"),
                "latest_publication_utc": payload.get("latest_publication_utc"),
                "extra": payload.get("extra") or {},
                "status_file": _safe_rel(path, root),
            }
        )

    rows = []
    files = []
    for path in sorted(normalized_dir.glob("*.jsonl")):
        files.append(_safe_rel(path, root))
        rows.extend(_iter_jsonl(path))
    symbols = sorted({str(row.get("gtos_symbol")) for row in rows if row.get("gtos_symbol")})
    report_types = sorted({str(row.get("report_type")) for row in rows if row.get("report_type")})
    return {
        "status_file_count": len(statuses),
        "statuses": statuses,
        "normalized_file_count": len(files),
        "normalized_row_count": len(rows),
        "gtos_symbols": symbols,
        "report_types": report_types,
        "files": files,
    }


def lbma_inventory(root: Path) -> dict[str, Any]:
    status_dir = root / "data" / "external" / "status"
    normalized_dir = root / "data" / "external" / "normalized" / "lbma_calendar"
    statuses = []
    for path in sorted(status_dir.glob("lbma_calendar*.json")):
        payload = _read_json(path)
        statuses.append(
            {
                "status_key": payload.get("status_key"),
                "status": payload.get("status"),
                "row_count": payload.get("row_count"),
                "latest_observation_utc": payload.get("latest_observation_utc"),
                "latest_publication_utc": payload.get("latest_publication_utc"),
                "status_file": _safe_rel(path, root),
            }
        )

    rows = []
    files = []
    for path in sorted(normalized_dir.glob("*.jsonl")):
        files.append(_safe_rel(path, root))
        rows.extend(_iter_jsonl(path))
    symbols = sorted({str(row.get("gtos_symbol")) for row in rows if row.get("gtos_symbol")})
    metals = sorted({str(row.get("metal")) for row in rows if row.get("metal")})
    term_presence = source_text_contains(root, ("Krohn", "Mueller", "Whelan", "FX-fix", "KMW"))
    return {
        "status_file_count": len(statuses),
        "statuses": statuses,
        "normalized_file_count": len(files),
        "normalized_row_count": len(rows),
        "gtos_symbols": symbols,
        "metals": metals,
        "kmw_fx_fix_source_present": any(term_presence.values()),
        "kmw_term_presence": term_presence,
        "files": files,
    }


def history_availability_inventory(root: Path) -> dict[str, Any]:
    probe_dir = root / "data" / "mt5_research_exports" / "history_availability"
    probes = sorted(probe_dir.glob("phase3_m15_probe_2021_calendar_year_v2_*.json"))
    latest_2021 = probes[-1] if probes else None
    files: dict[str, Any] = {}
    if latest_2021:
        payload = _read_json(latest_2021)
        files = payload.get("files") or {}

    per_symbol = {}
    for key, info in files.items():
        symbol = str(info.get("file_symbol") or key.split("_", 1)[0])
        per_symbol[symbol] = {
            "rows": info.get("rows"),
            "first": info.get("first"),
            "last": info.get("last"),
            "has_rows_in_requested_range": bool(info.get("has_rows_in_requested_range")),
            "covers_requested_start": bool(info.get("covers_requested_start")),
            "reaches_requested_end": bool(info.get("reaches_requested_end")),
        }

    return {
        "latest_2021_probe": _safe_rel(latest_2021, root) if latest_2021 else None,
        "symbols_with_2021_rows": sorted(
            symbol for symbol, info in per_symbol.items() if info["has_rows_in_requested_range"]
        ),
        "symbols_covering_2021_start": sorted(
            symbol for symbol, info in per_symbol.items() if info["covers_requested_start"]
        ),
        "symbols_reaching_2021_end": sorted(
            symbol for symbol, info in per_symbol.items() if info["reaches_requested_end"]
        ),
        "per_symbol": per_symbol,
    }


def classify_tasks(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ticks = payload["inventories"]["ticks"]
    cftc = payload["inventories"]["cftc"]
    lbma = payload["inventories"]["lbma"]
    hist = payload["inventories"]["history_availability"]

    fx_cftc_symbols = [symbol for symbol in cftc["gtos_symbols"] if symbol not in {"XAUUSD", "XAGUSD"}]
    d1_ready_days = ticks["max_symbol_days"]
    d12_has_full_2021 = bool(hist["symbols_covering_2021_start"] and hist["symbols_reaching_2021_end"])

    return {
        "D-1": {
            "status": "DEFERRED_WITH_TRIGGER",
            "backlog_item": "Tick re-bar-sampling infrastructure (volume / dollar / imbalance bars across all 7 instruments).",
            "blocked_by": f"Tick capture exists but local history is only {d1_ready_days} days at best; MT5 retail volume/last fields are not a real volume/dollar substrate.",
            "trigger": "Rerun after >=30 trading days of all-symbol tick captures or approved paid LOB/trade feed; use tick-count-time bars as the MT5-safe substitute if implemented.",
            "evidence": {
                "symbols_with_ticks": ticks["symbols_with_ticks"],
                "max_symbol_days": ticks["max_symbol_days"],
                "tick_features_helper_exists": ticks["tick_features_helper_exists"],
                "tick_capture_daemon_exists": ticks["tick_capture_daemon_exists"],
            },
            "candidate_strength_vs_j46_j49": "not_applicable_data_substrate",
        },
        "D-4": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "CFTC COT data fetcher (gold + FX positioning).",
            "blocked_by": "CFTC fetcher and gold XAUUSD cache exist, but no local FX COT contract mappings/rows are present.",
            "trigger": "Register official CFTC FX contract mappings, fetch/cache those rows with publication-time guards, then reclassify.",
            "evidence": {
                "status_file_count": cftc["status_file_count"],
                "normalized_row_count": cftc["normalized_row_count"],
                "gtos_symbols": cftc["gtos_symbols"],
                "fx_cftc_symbols": fx_cftc_symbols,
            },
            "candidate_strength_vs_j46_j49": "not_applicable_data_source",
        },
        "D-5": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "LBMA fix + Krohn-Mueller-Whelan FX-fix data sources.",
            "blocked_by": "LBMA gold/silver fix calendar exists, but no local Krohn-Mueller-Whelan FX-fix source/cache is present.",
            "trigger": "Confirm the KMW FX-fix source/licensing path or replace with a registered legal FX-fix proxy; keep LBMA calendar as done subcomponent.",
            "evidence": {
                "status_file_count": lbma["status_file_count"],
                "normalized_row_count": lbma["normalized_row_count"],
                "gtos_symbols": lbma["gtos_symbols"],
                "metals": lbma["metals"],
                "kmw_fx_fix_source_present": lbma["kmw_fx_fix_source_present"],
            },
            "candidate_strength_vs_j46_j49": "not_applicable_data_source",
        },
        "D-12": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "Pre-2022 OHLCV extension (where broker has depth).",
            "blocked_by": "Current MT5 history probes show no full 2021 all-symbol M15 coverage; only XAGUSD has a small late-2021 slice.",
            "trigger": "Use an alternate broker/provider/archive if pre-2022 OHLCV is needed; do not treat current redacted_account MT5 as providing usable pre-2022 GTOS coverage.",
            "evidence": {
                "latest_2021_probe": hist["latest_2021_probe"],
                "symbols_with_2021_rows": hist["symbols_with_2021_rows"],
                "symbols_covering_2021_start": hist["symbols_covering_2021_start"],
                "symbols_reaching_2021_end": hist["symbols_reaching_2021_end"],
                "full_2021_available": d12_has_full_2021,
            },
            "candidate_strength_vs_j46_j49": "not_applicable_data_availability",
        },
    }


def build_payload(root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root_path = Path(root)
    payload = {
        "schema_version": "lane5_data_source_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "research/tooling only",
        "question": "Classify Lane 5 D-1/D-4/D-5/D-12 against local data-source evidence.",
        "source_files": [
            "research/ml_program/MASTER_BACKLOG.md",
            "data/ticks/",
            "data/mt5_research_exports/history_availability/",
            "data/mt5_research_exports/tick_availability/",
            "data/external/status/",
            "data/external/normalized/",
            "src/components/external_feeds.py",
            "scripts/fetch_external_feeds.py",
        ],
        "inventories": {
            "ticks": tick_inventory(root_path),
            "cftc": cftc_inventory(root_path),
            "lbma": lbma_inventory(root_path),
            "history_availability": history_availability_inventory(root_path),
            "bar_resampling_terms": source_text_contains(
                root_path,
                ("volume-bar resampling", "dollar-bar resampling", "imbalance-bar resampling", "tick-count-time bars"),
            ),
        },
    }
    payload["task_classifications"] = classify_tasks(payload)
    payload["status_counts"] = dict(
        sorted(Counter(row["status"] for row in payload["task_classifications"].values()).items())
    )
    return payload


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    ticks = payload["inventories"]["ticks"]
    cftc = payload["inventories"]["cftc"]
    lbma = payload["inventories"]["lbma"]
    hist = payload["inventories"]["history_availability"]
    tasks = payload["task_classifications"]
    lines = [
        "# Lane 5 Data Source Triage",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Question",
        "",
        payload["question"],
        "",
        "## Local Inventory",
        "",
        f"- Tick capture symbols with parquet files: `{ticks['symbols_with_ticks']}/7`; max days for any symbol: `{ticks['max_symbol_days']}`.",
        f"- Tick helper files: capture daemon `{ticks['tick_capture_daemon_exists']}`, feature helper `{ticks['tick_features_helper_exists']}`.",
        f"- CFTC normalized rows: `{cftc['normalized_row_count']}` across GTOS symbols `{', '.join(cftc['gtos_symbols'])}`.",
        f"- LBMA normalized rows: `{lbma['normalized_row_count']}` for metals `{', '.join(lbma['metals'])}` and symbols `{', '.join(lbma['gtos_symbols'])}`.",
        f"- 2021 M15 probe symbols with any rows: `{', '.join(hist['symbols_with_2021_rows']) or 'none'}`.",
        "",
        "## Task Classifications",
        "",
        "| id | status | blocker / trigger | candidate strength |",
        "| --- | --- | --- | --- |",
    ]
    for item_id in ("D-1", "D-4", "D-5", "D-12"):
        row = tasks[item_id]
        lines.append(
            "| {id} | {status} | {blocker} | {strength} |".format(
                id=item_id,
                status=row["status"],
                blocker=(row["blocked_by"] or row["trigger"]).replace("|", r"\|"),
                strength=row["candidate_strength_vs_j46_j49"],
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `D-1` is deferred, not done: tick capture exists, but volume/dollar/imbalance bars are still blocked by MT5 retail substrate limits and short local tick history.",
            "- `D-4` is blocked as a full backlog item: the CFTC COT fetcher and XAUUSD gold cache exist, but the requested FX positioning side is not locally mapped/cached.",
            "- `D-5` is blocked as a full backlog item: LBMA gold/silver fix calendar exists, but the KMW FX-fix source is absent locally.",
            "- `D-12` is blocked by broker history availability: current 2021 probe does not provide full all-symbol pre-2022 M15 coverage.",
            "",
            "## Source Files",
            "",
        ]
    )
    for source in payload["source_files"]:
        lines.append(f"- `{source}`")
    lines.extend(
        [
            "",
            "## NO_PROMOTION_VERDICT",
            "",
            "This artifact classifies data-source readiness only. It does not validate, promote, or modify live trading behavior.",
            "",
        ]
    )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(args.root)
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        "task_statuses="
        + json.dumps({key: value["status"] for key, value in payload["task_classifications"].items()}, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
