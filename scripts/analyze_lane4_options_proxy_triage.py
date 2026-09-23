#!/usr/bin/env python3
"""Triage Lane 4 options/gamma proxy feed tasks.

Research/tooling only. The script reads local feed-status and normalized-feed
files, then classifies the master-backlog options proxy items without making any
live trading changes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_JSON = (
    "research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.json"
)
DEFAULT_OUTPUT_MD = "research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md"

VOL_SERIES_NEEDED_FOR_A2 = ("VIX1D", "VIX9D")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _series_tokens_from_status(path: Path, payload: dict[str, Any]) -> set[str]:
    tokens = {path.stem.upper(), path.name.upper()}
    for key in ("status_key", "status_id", "source"):
        value = payload.get(key)
        if value is not None:
            tokens.add(str(value).upper())
    extra = payload.get("extra") or {}
    if isinstance(extra, dict):
        for key, value in extra.items():
            tokens.add(str(key).upper())
            tokens.add(str(value).upper())
    return tokens


def detect_external_data_terms(root: Path, terms: tuple[str, ...]) -> dict[str, bool]:
    """Return whether each term appears in local feed filenames or status metadata."""

    status_dir = root / "data" / "external" / "status"
    normalized_dir = root / "data" / "external" / "normalized"
    found = {term.upper(): False for term in terms}

    for path in status_dir.glob("*.json"):
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            payload = {}
        tokens = _series_tokens_from_status(path, payload)
        for term in found:
            if any(term in token for token in tokens):
                found[term] = True

    for path in normalized_dir.rglob("*"):
        if not path.is_file():
            continue
        upper = path.as_posix().upper()
        for term in found:
            if term in upper:
                found[term] = True
    return found


def load_fred_inventory(root: Path) -> dict[str, Any]:
    status_dir = root / "data" / "external" / "status"
    normalized_dir = root / "data" / "external" / "normalized" / "fred"
    series: dict[str, dict[str, Any]] = {}

    for path in sorted(status_dir.glob("fred__*.json")):
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        status_key = str(payload.get("status_key") or path.stem.replace("fred__", ""))
        series[status_key] = {
            "status": payload.get("status"),
            "row_count": payload.get("row_count"),
            "latest_observation_utc": payload.get("latest_observation_utc"),
            "latest_publication_utc": payload.get("latest_publication_utc"),
            "status_file": _safe_rel(path, root),
        }

    latest_observation_files: dict[str, str] = {}
    for path in sorted(normalized_dir.glob("*_observations_*.jsonl")):
        prefix = path.name.split("_observations_", 1)[0]
        latest_observation_files[prefix] = _safe_rel(path, root)

    return {
        "series": series,
        "normalized_observation_files": latest_observation_files,
        "available_vol_terms": detect_external_data_terms(
            root, ("VIXCLS", "VIX1D", "VIX9D", "GVZCLS", "VVIX", "VRP")
        ),
    }


def load_flashalpha_inventory(root: Path) -> dict[str, Any]:
    status_dir = root / "data" / "external" / "status"
    normalized_dir = root / "data" / "external" / "normalized" / "flashalpha_gex"

    statuses: list[dict[str, Any]] = []
    for path in sorted(status_dir.glob("flashalpha_gex__*.json")):
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        extra = payload.get("extra") or {}
        statuses.append(
            {
                "status_key": payload.get("status_key"),
                "status": payload.get("status"),
                "row_count": payload.get("row_count"),
                "proxy_symbol": extra.get("proxy_symbol"),
                "gtos_symbol": extra.get("gtos_symbol"),
                "expiration": extra.get("expiration"),
                "latest_publication_utc": payload.get("latest_publication_utc"),
                "status_file": _safe_rel(path, root),
            }
        )

    rows: list[dict[str, Any]] = []
    files: list[str] = []
    for path in sorted(normalized_dir.glob("*_gex_*.jsonl")):
        files.append(_safe_rel(path, root))
        rows.extend(_iter_jsonl(path))

    latest_by_proxy: dict[str, dict[str, Any]] = {}
    for row in rows:
        proxy = str(row.get("proxy_symbol") or "")
        if not proxy:
            continue
        current = latest_by_proxy.get(proxy)
        if current is None or str(row.get("as_of_utc") or "") > str(current.get("as_of_utc") or ""):
            latest_by_proxy[proxy] = {
                "proxy_symbol": proxy,
                "gtos_symbol": row.get("gtos_symbol"),
                "expiration": row.get("expiration"),
                "as_of_utc": row.get("as_of_utc"),
                "net_gex": row.get("net_gex"),
                "net_gex_label": row.get("net_gex_label"),
                "gamma_flip": row.get("gamma_flip"),
                "underlying_price": row.get("underlying_price"),
            }

    proxy_counts = Counter(str(row.get("proxy_symbol") or "") for row in rows)
    proxy_counts.pop("", None)

    return {
        "status_file_count": len(statuses),
        "normalized_file_count": len(files),
        "normalized_row_count": len(rows),
        "statuses": statuses,
        "normalized_files": files,
        "proxy_counts": dict(sorted(proxy_counts.items())),
        "latest_by_proxy": dict(sorted(latest_by_proxy.items())),
    }


def classify_tasks(fred: dict[str, Any], flashalpha: dict[str, Any]) -> dict[str, dict[str, Any]]:
    vol_terms = fred["available_vol_terms"]
    missing_a2 = [term for term in VOL_SERIES_NEEDED_FOR_A2 if not vol_terms.get(term)]
    flashalpha_ready = (
        flashalpha["status_file_count"] >= 5
        and flashalpha["normalized_row_count"] >= 5
        and {"QQQ", "DIA", "SPY"}.issubset(set(flashalpha["proxy_counts"]))
    )

    return {
        "A-2": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "VIX1D-VIX9D spread feature (gamma-sign proxy from MT5 + supplement).",
            "blocked_by": (
                "Local feed inventory does not contain "
                + ", ".join(missing_a2)
                + "; current normalized volatility feed has VIXCLS/GVZ-class data only."
            ),
            "trigger": "Confirm legal/free VIX1D and VIX9D sources, fetch/cache them as as-of daily series, then construct the spread with publication-time guards.",
            "evidence": {
                "available_vol_terms": vol_terms,
                "missing_required_terms": missing_a2,
            },
            "candidate_strength_vs_j46_j49": "not_applicable_feature_feasibility",
        },
        "A-3": {
            "status": "BLOCKED_WITH_REASON",
            "backlog_item": "VRP delta feature (term-structure-based gamma proxy).",
            "blocked_by": "No local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists in data/external.",
            "trigger": "Create a no-leak VRP construction spec with an as-of implied-vol/variance source and a realized-vol estimator, then build a point-in-time cache.",
            "evidence": {
                "vrp_term_present_in_external_data": fred["available_vol_terms"].get("VRP", False),
                "vix1d_present": vol_terms.get("VIX1D", False),
                "vix9d_present": vol_terms.get("VIX9D", False),
            },
            "candidate_strength_vs_j46_j49": "not_applicable_feature_feasibility",
        },
        "D-3": {
            "status": "DONE",
            "backlog_item": "CBOE GEX feed integration (or proxy via VIX term-structure).",
            "blocked_by": "",
            "trigger": "No repo integration blocker remains for the FlashAlpha Basic proxy path; official CBOE aggregate/historical GEX remains separate blocked validation/source work.",
            "evidence": {
                "flashalpha_basic_proxy_ready": flashalpha_ready,
                "status_file_count": flashalpha["status_file_count"],
                "normalized_file_count": flashalpha["normalized_file_count"],
                "normalized_row_count": flashalpha["normalized_row_count"],
                "proxy_counts": flashalpha["proxy_counts"],
                "latest_by_proxy": flashalpha["latest_by_proxy"],
            },
            "candidate_strength_vs_j46_j49": "not_strategy_comparable_feed_integration_only",
        },
    }


def build_payload(root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root_path = Path(root)
    fred = load_fred_inventory(root_path)
    flashalpha = load_flashalpha_inventory(root_path)
    task_classifications = classify_tasks(fred, flashalpha)
    return {
        "schema_version": "lane4_options_gamma_proxy_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "scope": "research/tooling only",
        "source_files": [
            ".context/04_agents/PHASE_3_FREE_FEED_SPRINT_PLAN.md",
            ".context/04_agents/PHASE_3_EXTERNAL_FEED_VALIDATION_REVIEW.md",
            "src/components/external_feeds.py",
            "scripts/fetch_external_feeds.py",
            "data/external/status/",
            "data/external/normalized/",
        ],
        "question": "Classify Lane 4 A-2/A-3/D-3 using local options/gamma proxy feed evidence.",
        "feed_inventory": {
            "fred": fred,
            "flashalpha_gex": flashalpha,
        },
        "task_classifications": task_classifications,
        "ambiguity_ledger": [
            {
                "ambiguity": "FlashAlpha Basic is single-expiry and forward-point-in-time only.",
                "handling": "Treat D-3 as proxy integration complete, not historical validation or official CBOE GEX coverage.",
            },
            {
                "ambiguity": "VIX1D/VIX9D source legality and fetch path are not represented locally.",
                "handling": "Block A-2 until both series have a confirmed legal/free source and no-leak cache.",
            },
            {
                "ambiguity": "VRP delta can be defined multiple ways.",
                "handling": "Block A-3 until the implied-vol source, realized-vol lookback, and publication-time convention are pre-registered.",
            },
        ],
    }


def _fmt(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    flash = payload["feed_inventory"]["flashalpha_gex"]
    fred = payload["feed_inventory"]["fred"]
    tasks = payload["task_classifications"]
    lines = [
        "# Lane 4 Options/Gamma Proxy Triage",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Question",
        "",
        payload["question"],
        "",
        "## Local Feed Inventory",
        "",
        f"- FlashAlpha GEX specific status files: `{flash['status_file_count']}`.",
        f"- FlashAlpha GEX normalized snapshot files: `{flash['normalized_file_count']}`.",
        f"- FlashAlpha GEX normalized rows: `{flash['normalized_row_count']}`.",
        f"- FlashAlpha proxy row counts: `{json.dumps(flash['proxy_counts'], sort_keys=True)}`.",
        f"- FRED status series: `{', '.join(sorted(fred['series']))}`.",
        f"- Vol/gamma terms found in local external data: `{json.dumps(fred['available_vol_terms'], sort_keys=True)}`.",
        "",
        "## Task Classifications",
        "",
        "| id | status | blocker / trigger | candidate strength |",
        "| --- | --- | --- | --- |",
    ]
    for item_id in ("A-2", "A-3", "D-3"):
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
            "## Evidence Details",
            "",
            "D-3 is complete only for the accepted proxy-integration path: FlashAlpha Basic single-expiry GEX snapshots are parsed, cached, and status-tracked for QQQ, DIA, SPY, GLD, and SLV. This is not official CBOE aggregate GEX and it is not a historical alpha verdict.",
            "",
            "A-2 is blocked because the local feed inventory has VIXCLS but does not have both VIX1D and VIX9D. The existing free-feed plan already restricts the spread to cases where the VIX1D source is confirmed legal/free.",
            "",
            "A-3 is blocked because VRP delta needs a pre-registered construction, including an implied-vol or variance term-structure source and a realized-vol estimator. VIXCLS alone is not enough to define VRP delta.",
            "",
            "## Ambiguity Ledger",
            "",
        ]
    )
    for row in payload["ambiguity_ledger"]:
        lines.append(f"- {row['ambiguity']} Handling: {row['handling']}")

    lines.extend(
        [
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
            "This artifact classifies feed feasibility and integration state only. It does not validate, promote, or modify live trading behavior.",
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
    status_summary = {key: value["status"] for key, value in payload["task_classifications"].items()}
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"task_statuses={_fmt(status_summary)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
