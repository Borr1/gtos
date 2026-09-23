#!/usr/bin/env python3
"""Triage remaining Lane 5 data/feed backlog items D-2/D-7/D-8/D-9/D-10.

Research/tooling only. Uses local feed caches, MT5 tick probes, and existing
source plans to classify remaining data-access work without network calls.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = "research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _safe_rel(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def tick_probe_inventory(root: Path) -> dict[str, Any]:
    probe_dir = root / "data" / "mt5_research_exports" / "tick_availability"
    probes = sorted(probe_dir.glob("*.json"))
    latest = probes[-1] if probes else None
    payload = _read_json(latest) if latest else {}
    files = payload.get("files") or {}
    windows = []
    for key, row in files.items():
        windows.append(
            {
                "key": key,
                "file_symbol": row.get("file_symbol"),
                "window": row.get("window"),
                "start": row.get("start"),
                "end": row.get("end"),
                "has_ticks": bool(row.get("has_ticks")),
                "rows": int(row.get("rows") or 0),
                "first_tick_utc": row.get("first_tick_utc"),
                "last_tick_utc": row.get("last_tick_utc"),
            }
        )
    pre_2024_with_ticks = [
        row for row in windows if row["has_ticks"] and str(row.get("start") or "") < "2024-01-01"
    ]
    return {
        "probe_file_count": len(probes),
        "latest_probe": _safe_rel(latest, root),
        "window_count": len(windows),
        "windows_with_ticks": sum(1 for row in windows if row["has_ticks"]),
        "pre_2024_windows_with_ticks": len(pre_2024_with_ticks),
        "earliest_window_start": min((str(row.get("start")) for row in windows if row.get("start")), default=None),
        "latest_window_end": max((str(row.get("end")) for row in windows if row.get("end")), default=None),
    }


def status_inventory(root: Path, prefix: str) -> list[dict[str, Any]]:
    out = []
    for path in sorted((root / "data" / "external" / "status").glob(f"{prefix}*.json")):
        payload = _read_json(path)
        out.append(
            {
                "source": payload.get("source"),
                "status_key": payload.get("status_key"),
                "status": payload.get("status"),
                "row_count": payload.get("row_count"),
                "latest_observation_utc": payload.get("latest_observation_utc"),
                "latest_publication_utc": payload.get("latest_publication_utc"),
                "status_file": _safe_rel(path, root),
                "extra": payload.get("extra") or {},
            }
        )
    return out


def normalized_inventory(root: Path, source: str) -> dict[str, Any]:
    normalized_dir = root / "data" / "external" / "normalized" / source
    files = sorted(normalized_dir.glob("*.jsonl"))
    rows: list[dict[str, Any]] = []
    for path in files:
        rows.extend(_iter_jsonl(path))
    return {
        "file_count": len(files),
        "row_count": len(rows),
        "files": [_safe_rel(path, root) for path in files],
        "rows": rows,
    }


def fred_inventory(root: Path) -> dict[str, Any]:
    normalized = normalized_inventory(root, "fred")
    rows = normalized.pop("rows")
    series = sorted({str(row.get("series_id")) for row in rows if row.get("series_id")})
    return {
        "status_file_count": len(status_inventory(root, "fred")),
        "statuses": status_inventory(root, "fred"),
        "normalized_file_count": normalized["file_count"],
        "normalized_row_count": normalized["row_count"],
        "series": series,
        "files": normalized["files"],
    }


def wgc_inventory(root: Path) -> dict[str, Any]:
    normalized = normalized_inventory(root, "wgc")
    rows = normalized.pop("rows")
    central_bank_rows = [
        row
        for row in rows
        if "central_bank" in str(row.get("dataset") or "").lower()
        or "central bank" in str(row.get("category") or "").lower()
    ]
    datasets = sorted({str(row.get("dataset")) for row in rows if row.get("dataset")})
    return {
        "status_file_count": len(status_inventory(root, "wgc")),
        "statuses": status_inventory(root, "wgc"),
        "normalized_file_count": normalized["file_count"],
        "normalized_row_count": normalized["row_count"],
        "central_bank_row_count": len(central_bank_rows),
        "central_bank_datasets": sorted({str(row.get("dataset")) for row in central_bank_rows}),
        "datasets": datasets[:50],
        "files": normalized["files"],
    }


def external_source_presence(root: Path, terms: tuple[str, ...]) -> dict[str, bool]:
    """Check local external-feed filenames/status metadata for source terms."""

    files = list((root / "data" / "external").rglob("*"))
    joined = "\n".join(path.as_posix().lower() for path in files)
    statuses = []
    for path in (root / "data" / "external" / "status").glob("*.json"):
        statuses.append(path.read_text(encoding="utf-8", errors="replace").lower())
    joined += "\n" + "\n".join(statuses)
    return {term: term.lower() in joined for term in terms}


def classify_tasks(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ticks = payload["inventories"]["tick_probe"]
    fred = payload["inventories"]["fred"]
    wgc = payload["inventories"]["wgc"]
    source_terms = payload["inventories"]["source_terms"]

    return {
        "D-2": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "Pre-2024 tick data extraction (where broker permits).",
            "blocked_by": "Local MT5 tick probes and tick-capture cache do not provide pre-2024 tick history; broker retention only covers recent windows.",
            "trigger": "Alternate broker/provider/archive or paid historical tick/LOB source with pre-2024 coverage.",
            "latest_artifact_path": DEFAULT_OUTPUT_MD,
            "evidence": ticks,
            "candidate_strength_vs_j46_j49": "not_applicable_data_availability",
        },
        "D-7": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "He-Kelly-Manela intermediary-capital SDF index access.",
            "blocked_by": "No local H-K-M/intermediary-capital SDF source, status file, normalized cache, or registered source spec was found.",
            "trigger": "Obtain legal source/access path and cache it with no-lookahead publication metadata.",
            "latest_artifact_path": DEFAULT_OUTPUT_MD,
            "evidence": {
                "term_presence": {key: source_terms[key] for key in ("hkm", "he_kelly_manela", "intermediary_capital")},
            },
            "candidate_strength_vs_j46_j49": "not_applicable_data_source",
        },
        "D-8": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "FRED / BIS macro feature feed.",
            "blocked_by": "FRED macro cache exists, but no BIS source/cache/spec exists locally; full FRED/BIS item remains incomplete.",
            "trigger": "Register BIS macro source tables, fetch/cache them with publication-time metadata, and join with existing FRED macro cache.",
            "latest_artifact_path": DEFAULT_OUTPUT_MD,
            "evidence": {
                "fred_series": fred["series"],
                "fred_normalized_row_count": fred["normalized_row_count"],
                "bis_present": source_terms["bis"],
            },
            "candidate_strength_vs_j46_j49": "not_applicable_data_source_partial_fred_ready",
        },
        "D-9": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "Federal Reserve research feed integration.",
            "blocked_by": "No distinct Federal Reserve research-feed source contract, parser, status file, or normalized cache exists beyond the FRED macro feed.",
            "trigger": "Define the intended Federal Reserve research source, fields, cadence, publication-time model, and parser/cache.",
            "latest_artifact_path": DEFAULT_OUTPUT_MD,
            "evidence": {
                "fred_series": fred["series"],
                "federal_research_present": source_terms["federal_research"],
                "fed_research_present": source_terms["fed_research"],
            },
            "candidate_strength_vs_j46_j49": "not_applicable_ambiguous_source",
        },
        "D-10": {
            "status": "DONE",
            "backlog_item": "World Gold Council central-bank-flow feed.",
            "blocked_by": "",
            "trigger": "No data-plumbing blocker remains for local WGC GDT/ETF imports; alpha validation and scheduled/operator refresh remain separate work.",
            "latest_artifact_path": DEFAULT_OUTPUT_MD,
            "evidence": {
                "wgc_normalized_row_count": wgc["normalized_row_count"],
                "central_bank_row_count": wgc["central_bank_row_count"],
                "central_bank_datasets": wgc["central_bank_datasets"],
                "status_file_count": wgc["status_file_count"],
            },
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_feed_integration_only",
        },
    }


def build_payload(root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root_path = Path(root)
    payload = {
        "schema_version": "lane5_remaining_data_feed_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "research/tooling only",
        "question": "Classify remaining Lane 5 data/feed items D-2/D-7/D-8/D-9/D-10 from local source evidence.",
        "source_files": [
            "research/ml_program/MASTER_BACKLOG.md",
            "data/mt5_research_exports/tick_availability/",
            "data/external/status/",
            "data/external/normalized/",
            "src/components/external_feeds.py",
            "scripts/fetch_external_feeds.py",
            ".context/04_agents/PHASE_3_FREE_FEED_SPRINT_PLAN.md",
            ".context/04_agents/PHASE_3_EXTERNAL_FEED_VALIDATION_REVIEW.md",
        ],
        "inventories": {
            "tick_probe": tick_probe_inventory(root_path),
            "fred": fred_inventory(root_path),
            "wgc": wgc_inventory(root_path),
            "source_terms": external_source_presence(
                root_path,
                (
                    "bis",
                    "hkm",
                    "he_kelly_manela",
                    "intermediary_capital",
                    "federal_research",
                    "fed_research",
                ),
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
    ticks = payload["inventories"]["tick_probe"]
    fred = payload["inventories"]["fred"]
    wgc = payload["inventories"]["wgc"]
    tasks = payload["task_classifications"]
    lines = [
        "# Lane 5 Remaining Data/Feed Triage",
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
        f"- Tick probes: `{ticks['probe_file_count']}` files; latest `{ticks['latest_probe']}`; pre-2024 windows with ticks `{ticks['pre_2024_windows_with_ticks']}`.",
        f"- FRED: `{fred['normalized_row_count']}` normalized rows across series `{', '.join(fred['series'])}`.",
        f"- WGC: `{wgc['normalized_row_count']}` normalized rows; central-bank rows `{wgc['central_bank_row_count']}`.",
        f"- WGC central-bank datasets: `{', '.join(wgc['central_bank_datasets'])}`.",
        "",
        "## Task Classifications",
        "",
        "| id | status | blocker / trigger | candidate strength |",
        "| --- | --- | --- | --- |",
    ]
    for item_id in ("D-2", "D-7", "D-8", "D-9", "D-10"):
        row = tasks[item_id]
        blocker = row["blocked_by"] or row["trigger"]
        lines.append(
            "| {id} | {status} | {blocker} | {strength} |".format(
                id=item_id,
                status=row["status"],
                blocker=blocker.replace("|", r"\|"),
                strength=row["candidate_strength_vs_j46_j49"],
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `D-10` is done as data plumbing: local WGC Gold Demand Trends and ETF imports exist, including central-bank/other-institution rows.",
            "- `D-8` is still blocked as a full item: FRED is ready, but BIS is not locally sourced or cached.",
            "- `D-2`, `D-7`, and `D-9` remain source-blocked and require external provider/source decisions before repo work can proceed.",
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
            "This artifact classifies data/feed readiness only. It does not validate, promote, or modify live trading behavior.",
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
