#!/usr/bin/env python3
"""Extract trades-level orderflow features for GTOS event windows.

Research/tooling only. Consumes the event manifest plus Databento fetch plan
and writes descriptive feature diagnostics. No live trading logic is changed.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.futures_cfd_mapping import load_databento_trades  # noqa: E402
from src.research_infra.orderflow_features import (  # noqa: E402
    compute_event_features,
    generated_at_utc,
    median_or_none,
)


DEFAULT_MANIFEST = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json"
)
DEFAULT_FETCH_PLAN = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_FETCH_PLAN_OF_DATA_2_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_FEATURE_DIAGNOSTIC_OF_DATA_3_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_FEATURE_DIAGNOSTIC_OF_DATA_3_2026-05-02.md"
)

SUMMARY_FEATURES = (
    "event15_signed_volume",
    "event15_buy_fraction",
    "event15_absorption_volume_per_tick",
    "profile_event_price_volume_percentile",
    "profile_nearest_lvn_distance_ticks",
    "post15_price_change_ticks",
)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [row for row in rows if row.get("is_primary_proxy") and row.get("data_status") == "ok"]
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in primary:
        by_class[row["event_class"]].append(row)
        by_symbol[row["symbol"]].append(row)

    def _summary(bucket: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, items in sorted(bucket.items()):
            out[key] = {"n": len(items)}
            for feature in SUMMARY_FEATURES:
                out[key][f"median_{feature}"] = median_or_none([item.get(feature) for item in items])
        return out

    status_counts = Counter(row.get("data_status") for row in rows)
    return {
        "feature_row_count": len(rows),
        "primary_ok_row_count": len(primary),
        "data_status_counts": dict(sorted(status_counts.items())),
        "primary_by_event_class": _summary(by_class),
        "primary_by_symbol": _summary(by_symbol),
    }


def build_payload(manifest: dict[str, Any], fetch_plan: dict[str, Any]) -> dict[str, Any]:
    events = {event["event_id"]: event for event in manifest["events"]}
    manifest_groups = {group["group_id"]: group for group in manifest.get("fetch_groups") or []}
    rows: list[dict[str, Any]] = []
    missing_outputs: list[str] = []
    for group in fetch_plan["groups"]:
        output_path = Path(group["output_path"])
        manifest_group = manifest_groups.get(group["group_id"], {})
        event_ids = group.get("event_ids") or manifest_group.get("event_ids") or []
        group_events = [events[event_id] for event_id in event_ids if event_id in events]
        if not output_path.exists():
            missing_outputs.append(str(output_path))
            for event in group_events:
                for futures_symbol in group["request"]["symbols"]:
                    rows.append(
                        {
                            "event_id": event["event_id"],
                            "symbol": event["symbol"],
                            "futures_symbol": futures_symbol,
                            "event_class": event["event_class"],
                            "data_status": "missing_raw",
                        }
                    )
            continue
        trades = load_databento_trades([output_path])
        for event in group_events:
            for futures_symbol in group["request"]["symbols"]:
                rows.append(compute_event_features(event, trades, futures_symbol))

    summary = summarize_rows(rows)
    return {
        "schema_version": "orderflow_event_feature_diagnostic_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "manifest_schema_version": manifest.get("schema_version"),
            "fetch_plan_schema_version": fetch_plan.get("schema_version"),
            "event_count": len(manifest.get("events") or []),
            "fetch_group_count": len(fetch_plan.get("groups") or []),
        },
        "feature_rows": rows,
        "missing_outputs": missing_outputs,
        "synthesis": {
            "summary": (
                "Trades-level orderflow features were extracted for fetched GTOS "
                "event windows. This is a diagnostic feature table, not a trading "
                "rule or promotion claim."
            ),
            **summary,
            "ambiguities": [
                "Trade side is Databento aggressor-side metadata; it is not identical to full footprint bid/ask-depth reconstruction.",
                "Zero-record weekend windows are retained as no_data and excluded from primary feature medians.",
                "Candidate-vs-context medians are descriptive only; no outcome edge or significance is claimed.",
                "Post-event features are for forensic diagnostics and must not be used in any future as-of decision rule.",
                "Depth/heatmap concepts such as resting liquidity and queue absorption remain untested by trades schema.",
            ],
            "open_questions": [
                "Do pre-event features alone separate candidates from structural context once outcomes are joined?",
                "Are LVN/POC proximity features stable across symbols or dominated by one instrument/session?",
                "Which candidate windows deserve mbp-1/mbp-10 depth pulls for true resting-liquidity validation?",
                "Do post-event diagnostics show trap/rejection patterns that can be re-expressed as pre-event hypotheses?",
            ],
            "next_steps": [
                "Join feature rows to synthetic/actual R outcomes and keep post-event fields out of as-of candidate hypotheses.",
                "Run candidate-versus-context and winner-versus-loser diagnostics on pre-event features only.",
                "Register a small number of structural orderflow hypotheses before any replay-style test.",
                "Spend depth credits only on the subset of windows where trades-level diagnostics show a coherent mechanism.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    lines = [
        "# Orderflow Event Feature Diagnostic",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Coverage",
        "",
        f"- Feature rows: {synth['feature_row_count']}",
        f"- Primary ok rows: {synth['primary_ok_row_count']}",
        f"- Data status counts: {synth['data_status_counts']}",
        "",
        "## Primary Proxy Medians By Event Class",
        "",
        "| Event class | n | event15 signed vol | event15 buy fraction | event15 absorption vol/tick | profile percentile | nearest LVN ticks | post15 change ticks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for klass, row in synth["primary_by_event_class"].items():
        lines.append(
            "| "
            f"{klass} | {row['n']} | "
            f"{_fmt(row.get('median_event15_signed_volume'))} | "
            f"{_fmt(row.get('median_event15_buy_fraction'))} | "
            f"{_fmt(row.get('median_event15_absorption_volume_per_tick'))} | "
            f"{_fmt(row.get('median_profile_event_price_volume_percentile'))} | "
            f"{_fmt(row.get('median_profile_nearest_lvn_distance_ticks'))} | "
            f"{_fmt(row.get('median_post15_price_change_ticks'))} |"
        )
    lines.extend(
        [
            "",
            "## Primary Proxy Medians By Symbol",
            "",
            "| Symbol | n | event15 signed vol | event15 buy fraction | event15 absorption vol/tick | profile percentile | nearest LVN ticks | post15 change ticks |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for symbol, row in synth["primary_by_symbol"].items():
        lines.append(
            "| "
            f"{symbol} | {row['n']} | "
            f"{_fmt(row.get('median_event15_signed_volume'))} | "
            f"{_fmt(row.get('median_event15_buy_fraction'))} | "
            f"{_fmt(row.get('median_event15_absorption_volume_per_tick'))} | "
            f"{_fmt(row.get('median_profile_event_price_volume_percentile'))} | "
            f"{_fmt(row.get('median_profile_nearest_lvn_distance_ticks'))} | "
            f"{_fmt(row.get('median_post15_price_change_ticks'))} |"
        )
    lines.extend(
        [
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguities"]],
            "",
            "## Open Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["open_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):.4f}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--fetch-plan", default=DEFAULT_FETCH_PLAN)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    fetch_plan_path = Path(args.fetch_plan)
    if not manifest_path.exists():
        parser.exit(2, f"manifest not found: {manifest_path}\n")
    if not fetch_plan_path.exists():
        parser.exit(2, f"fetch plan not found: {fetch_plan_path}\n")
    payload = build_payload(load_json(manifest_path), load_json(fetch_plan_path))
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"feature_rows={payload['synthesis']['feature_row_count']} "
        f"primary_ok={payload['synthesis']['primary_ok_row_count']} "
        f"statuses={payload['synthesis']['data_status_counts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
