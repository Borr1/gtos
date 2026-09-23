#!/usr/bin/env python3
"""Cached NAS100 orderflow feature forensics.

Research/tooling only. This script reads existing MBO and MBP-10 diagnostic
JSON artifacts and performs leave-one-date/event stability checks. It never
fetches market data and never emits promotion language.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_MBO_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_MBO_FEATURE_DIAGNOSTIC_2026-05-02.json"
)
DEFAULT_MBP10_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_AGGRESSIVE_PROXY_EXPANDED_MBP10_FEATURES_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.md"
)

FEED_FEATURES = {
    "MBO_TOP20": {
        "event15_total_depth": "event15_median_total_depth20",
        "event15_thin_rate": "event15_thin_depth20_rate",
        "event15_imbalance": "event15_median_depth20_imbalance",
        "event15_wall_concentration": "event15_median_wall_concentration20",
        "event15_pull_pressure": "event15_near10_pull_pressure",
        "event15_net_liquidity": "event15_near10_net_liquidity",
        "pre60_total_depth": "pre60_median_total_depth20",
        "pre60_thin_rate": "pre60_thin_depth20_rate",
    },
    "MBP10_TOP10": {
        "event15_total_depth": "event15_median_total_depth10",
        "event15_thin_rate": "event15_thin_depth10_rate",
        "event15_imbalance": "event15_median_depth10_imbalance",
        "event15_near_far": "event15_median_near_far_ratio",
        "event15_max_bid_wall": "event15_median_max_bid_wall",
        "event15_max_ask_wall": "event15_median_max_ask_wall",
        "pre60_total_depth": "pre60_median_total_depth10",
        "pre60_thin_rate": "pre60_thin_depth10_rate",
    },
}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def median(values: Iterable[Any]) -> float | None:
    clean = [value for value in (safe_float(item) for item in values) if value is not None]
    return statistics.median(clean) if clean else None


def event_date(row: dict[str, Any]) -> str:
    return str(row.get("canonical_m15_close_utc") or "")[:10] or "UNKNOWN"


def event_hour(row: dict[str, Any]) -> str:
    text = str(row.get("canonical_m15_close_utc") or "")
    return text[:13] if len(text) >= 13 else "UNKNOWN"


def ok_nas100_rows(payload: dict[str, Any], *, feed: str) -> list[dict[str, Any]]:
    rows = payload.get("feature_rows") or []
    out = []
    for row in rows:
        if row.get("data_status") != "ok":
            continue
        if feed == "MBP10_TOP10" and row.get("symbol") != "NAS100":
            continue
        if feed == "MBO_TOP20" and row.get("symbol") not in {None, "NAS100"}:
            continue
        out.append(dict(row))
    return out


def candidate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("event_class") == "candidate"]


def context_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("event_class") != "candidate"]


def median_delta(rows: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    cand = candidate_rows(rows)
    ctx = context_rows(rows)
    cand_median = median(row.get(feature) for row in cand)
    ctx_median = median(row.get(feature) for row in ctx)
    delta = None if cand_median is None or ctx_median is None else cand_median - ctx_median
    return {
        "candidate_n": len(cand),
        "context_n": len(ctx),
        "candidate_median": cand_median,
        "context_median": ctx_median,
        "candidate_minus_context": delta,
    }


def outcome_delta(rows: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    labeled = [
        row
        for row in candidate_rows(rows)
        if safe_float(row.get("candidate__synthetic_realized_r")) is not None
    ]
    winners = [row for row in labeled if float(row["candidate__synthetic_realized_r"]) > 0]
    losers = [row for row in labeled if float(row["candidate__synthetic_realized_r"]) <= 0]
    winner_median = median(row.get(feature) for row in winners)
    loser_median = median(row.get(feature) for row in losers)
    delta = None if winner_median is None or loser_median is None else winner_median - loser_median
    return {
        "synthetic_winner_n": len(winners),
        "synthetic_loser_n": len(losers),
        "winner_median": winner_median,
        "loser_median": loser_median,
        "winner_minus_loser": delta,
    }


def sign(value: float | None) -> int | None:
    if value is None:
        return None
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def leave_one_date(rows: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    base = median_delta(rows, feature)["candidate_minus_context"]
    dates = sorted({event_date(row) for row in rows})
    checks = []
    for date in dates:
        subset = [row for row in rows if event_date(row) != date]
        row = median_delta(subset, feature)
        delta = row["candidate_minus_context"]
        checks.append(
            {
                "left_out_date": date,
                "candidate_n": row["candidate_n"],
                "context_n": row["context_n"],
                "delta": delta,
                "change_vs_full": None if base is None or delta is None else delta - base,
                "sign_flip_vs_full": sign(base) is not None and sign(delta) is not None and sign(base) != sign(delta),
            }
        )
    valid_changes = [abs(item["change_vs_full"]) for item in checks if item.get("change_vs_full") is not None]
    return {
        "full_delta": base,
        "full_sign": sign(base),
        "sign_flip_count": sum(1 for item in checks if item["sign_flip_vs_full"]),
        "max_abs_change_vs_full": max(valid_changes) if valid_changes else None,
        "checks": checks,
    }


def leave_one_candidate_event(rows: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    base = median_delta(rows, feature)["candidate_minus_context"]
    checks = []
    for candidate in candidate_rows(rows):
        event_id = candidate.get("event_id")
        subset = [row for row in rows if row.get("event_id") != event_id]
        row = median_delta(subset, feature)
        delta = row["candidate_minus_context"]
        checks.append(
            {
                "left_out_event_id": event_id,
                "left_out_date": event_date(candidate),
                "delta": delta,
                "change_vs_full": None if base is None or delta is None else delta - base,
                "sign_flip_vs_full": sign(base) is not None and sign(delta) is not None and sign(base) != sign(delta),
            }
        )
    valid_changes = [abs(item["change_vs_full"]) for item in checks if item.get("change_vs_full") is not None]
    max_item = None
    if valid_changes:
        max_item = max(
            (item for item in checks if item.get("change_vs_full") is not None),
            key=lambda item: abs(float(item["change_vs_full"])),
        )
    return {
        "full_delta": base,
        "sign_flip_count": sum(1 for item in checks if item["sign_flip_vs_full"]),
        "max_abs_change_vs_full": max(valid_changes) if valid_changes else None,
        "max_impact_event": max_item,
    }


def count_share(counter: Counter[str]) -> dict[str, Any]:
    total = sum(counter.values())
    if not total:
        return {"counts": {}, "top_key": None, "top_share": None}
    top_key, top_count = counter.most_common(1)[0]
    return {"counts": dict(sorted(counter.items())), "top_key": top_key, "top_share": round(top_count / total, 6)}


def concentration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cand = candidate_rows(rows)
    ctx = context_rows(rows)
    return {
        "candidate_by_date": count_share(Counter(event_date(row) for row in cand)),
        "context_by_date": count_share(Counter(event_date(row) for row in ctx)),
        "candidate_by_hour": count_share(Counter(event_hour(row) for row in cand)),
        "context_by_hour": count_share(Counter(event_hour(row) for row in ctx)),
    }


def label_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cand = candidate_rows(rows)
    synthetic = [
        row for row in cand if safe_float(row.get("candidate__synthetic_realized_r")) is not None
    ]
    actual = [
        row
        for row in cand
        if row.get("candidate__realized_r_available") and safe_float(row.get("candidate__realized_r")) is not None
    ]
    actual_winners = [row for row in actual if float(row["candidate__realized_r"]) > 0]
    actual_losers = [row for row in actual if float(row["candidate__realized_r"]) <= 0]
    synthetic_winners = [row for row in synthetic if float(row["candidate__synthetic_realized_r"]) > 0]
    synthetic_losers = [row for row in synthetic if float(row["candidate__synthetic_realized_r"]) <= 0]
    return {
        "candidate_n": len(cand),
        "synthetic_label_n": len(synthetic),
        "synthetic_winner_n": len(synthetic_winners),
        "synthetic_loser_n": len(synthetic_losers),
        "actual_r_n": len(actual),
        "actual_winner_n": len(actual_winners),
        "actual_loser_n": len(actual_losers),
        "actual_label_status": "BLOCKED_ACTUAL_R_SPARSE_OR_ONE_SIDED",
    }


def feature_forensics(feed: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    features = FEED_FEATURES[feed]
    candidate_context = {name: median_delta(rows, field) for name, field in features.items()}
    outcome = {name: outcome_delta(rows, field) for name, field in features.items()}
    stability = {
        name: {
            "leave_one_date": leave_one_date(rows, field),
            "leave_one_candidate_event": leave_one_candidate_event(rows, field),
        }
        for name, field in features.items()
    }
    return {
        "feed": feed,
        "coverage": {
            "ok_rows": len(rows),
            "candidate_rows": len(candidate_rows(rows)),
            "context_rows": len(context_rows(rows)),
        },
        "label_coverage": label_coverage(rows),
        "concentration": concentration(rows),
        "candidate_context": candidate_context,
        "synthetic_outcome": outcome,
        "stability": stability,
    }


def runtime_diagnostics(mbo_payload: dict[str, Any]) -> dict[str, Any]:
    groups = mbo_payload.get("group_diagnostics") or {}
    rows_by_group = {
        group_id: int(group.get("rows_processed") or 0)
        for group_id, group in groups.items()
        if group.get("status") == "ok"
    }
    total_rows = sum(rows_by_group.values())
    return {
        "mbo_rows_processed_total": total_rows,
        "mbo_rows_processed_by_group": rows_by_group,
        "largest_group_rows": max(rows_by_group.values()) if rows_by_group else 0,
        "scaling_readout": (
            "Before larger MBO runs, split by date/group, persist per-second book snapshots or "
            "window-level features, and reuse cached group diagnostics instead of rehydrating every DBN file."
        ),
    }


def forward_feature_families(forensics: dict[str, Any]) -> list[dict[str, Any]]:
    mbo = forensics["feeds"]["MBO_TOP20"]
    mbp = forensics["feeds"]["MBP10_TOP10"]
    return [
        {
            "family": "depth_availability_thinness",
            "priority": "KEEP_FORWARD_DEFAULT",
            "fields": [
                "event15_median_total_depth10",
                "event15_thin_depth10_rate",
                "event15_median_total_depth20",
                "event15_thin_depth20_rate",
                "pre60_median_total_depth10",
                "pre60_median_total_depth20",
            ],
            "reason": (
                f"Candidate/context total-depth deltas agree in direction across feeds "
                f"(MBP10={mbp['candidate_context']['event15_total_depth']['candidate_minus_context']}, "
                f"MBO={mbo['candidate_context']['event15_total_depth']['candidate_minus_context']})."
            ),
        },
        {
            "family": "depth_imbalance",
            "priority": "KEEP_AS_SECONDARY_DIAGNOSTIC",
            "fields": ["event15_median_depth10_imbalance", "event15_median_depth20_imbalance"],
            "reason": "Signs are mostly coherent but leave-one-date checks show fragility on sparse dates.",
        },
        {
            "family": "near_touch_pull_add_pressure",
            "priority": "MBO_ONLY_LOW_CONFIDENCE",
            "fields": [
                "event15_near10_pull_pressure",
                "event15_near10_net_liquidity",
                "event15_near10_add_size",
                "event15_near10_remove_size",
            ],
            "reason": "MBO queue-flow fields are useful for diagnostics but candidate/context pull-pressure sign flips under leave-one-date.",
        },
        {
            "family": "wall_concentration",
            "priority": "MONITOR_ONLY",
            "fields": [
                "event15_median_wall_concentration20",
                "event15_median_max_bid_wall",
                "event15_median_max_ask_wall",
            ],
            "reason": "No current evidence that wall concentration is cleaner than raw depth availability.",
        },
    ]


def build_payload(mbo_payload: dict[str, Any], mbp10_payload: dict[str, Any]) -> dict[str, Any]:
    feeds = {
        "MBO_TOP20": feature_forensics("MBO_TOP20", ok_nas100_rows(mbo_payload, feed="MBO_TOP20")),
        "MBP10_TOP10": feature_forensics("MBP10_TOP10", ok_nas100_rows(mbp10_payload, feed="MBP10_TOP10")),
    }
    payload = {
        "schema_version": "orderflow_nas100_cached_feature_forensics_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "mbo_json": DEFAULT_MBO_JSON,
            "mbp10_json": DEFAULT_MBP10_JSON,
            "data_policy": "cached_json_only_no_databento_fetch",
        },
        "feeds": feeds,
        "runtime_diagnostics": runtime_diagnostics(mbo_payload),
        "feature_family_forward_plan": [],
        "synthesis": {
            "status": "DIAGNOSTIC_ONLY_LABEL_LIMITED",
            "thin_depth_clue": (
                "Depth availability remains the strongest cached NAS100 clue: MBO top-20 and MBP-10 top-10 "
                "candidate windows both show lower event15 total depth than context, but leave-one-date checks "
                "show the sign depends heavily on 2026-04-28."
            ),
            "label_separation": (
                "Candidate/context depth is label-free and survives as a diagnostic. Outcome contrast remains "
                "synthetic-label dominated with one winner and one actual-R row, so it cannot validate a filter."
            ),
            "stability": (
                "Leave-one-date diagnostics show the headline depth delta flips sign when 2026-04-28 is removed "
                "for both MBO and MBP-10; this is not stable enough for a promotion dossier."
            ),
        },
    }
    payload["feature_family_forward_plan"] = forward_feature_families(payload)
    return payload


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return lines


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    feeds = payload["feeds"]
    lines = [
        "# NAS100 Cached Orderflow Feature Forensics",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only; cached JSON only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        f"- Status: `{payload['synthesis']['status']}`.",
        f"- Thin-depth clue: {payload['synthesis']['thin_depth_clue']}",
        f"- Label separation: {payload['synthesis']['label_separation']}",
        f"- Stability: {payload['synthesis']['stability']}",
        "",
        "## Coverage",
        "",
        *table(
            ["feed", "ok rows", "candidate", "context", "synthetic labels", "winner/loser", "actual R"],
            [
                [
                    feed,
                    row["coverage"]["ok_rows"],
                    row["coverage"]["candidate_rows"],
                    row["coverage"]["context_rows"],
                    row["label_coverage"]["synthetic_label_n"],
                    f"{row['label_coverage']['synthetic_winner_n']}/{row['label_coverage']['synthetic_loser_n']}",
                    row["label_coverage"]["actual_r_n"],
                ]
                for feed, row in feeds.items()
            ],
        ),
        "",
        "## Candidate Vs Context",
        "",
        *table(
            ["feed", "depth delta", "thin-rate delta", "imbalance delta", "top candidate date share", "top candidate hour share"],
            [
                [
                    feed,
                    row["candidate_context"]["event15_total_depth"]["candidate_minus_context"],
                    row["candidate_context"]["event15_thin_rate"]["candidate_minus_context"],
                    row["candidate_context"]["event15_imbalance"]["candidate_minus_context"],
                    row["concentration"]["candidate_by_date"]["top_share"],
                    row["concentration"]["candidate_by_hour"]["top_share"],
                ]
                for feed, row in feeds.items()
            ],
        ),
        "",
        "## Leave-One Stability",
        "",
        *table(
            ["feed", "feature", "full delta", "date sign flips", "max date change", "event sign flips", "max event change"],
            [
                [
                    feed,
                    feature,
                    checks["leave_one_date"]["full_delta"],
                    checks["leave_one_date"]["sign_flip_count"],
                    checks["leave_one_date"]["max_abs_change_vs_full"],
                    checks["leave_one_candidate_event"]["sign_flip_count"],
                    checks["leave_one_candidate_event"]["max_abs_change_vs_full"],
                ]
                for feed, row in feeds.items()
                for feature, checks in row["stability"].items()
                if feature in {"event15_total_depth", "event15_thin_rate", "event15_imbalance", "event15_pull_pressure"}
            ],
        ),
        "",
        "## Synthetic Outcome Contrast",
        "",
        *table(
            ["feed", "depth W-L", "thin-rate W-L", "imbalance W-L", "label status"],
            [
                [
                    feed,
                    row["synthetic_outcome"]["event15_total_depth"]["winner_minus_loser"],
                    row["synthetic_outcome"]["event15_thin_rate"]["winner_minus_loser"],
                    row["synthetic_outcome"]["event15_imbalance"]["winner_minus_loser"],
                    row["label_coverage"]["actual_label_status"],
                ]
                for feed, row in feeds.items()
            ],
        ),
        "",
        "## Forward Fields",
        "",
        *table(
            ["family", "priority", "fields", "reason"],
            [
                [item["family"], item["priority"], ", ".join(item["fields"]), item["reason"]]
                for item in payload["feature_family_forward_plan"]
            ],
        ),
        "",
        "## Runtime And Scaling",
        "",
        f"- MBO rows processed total in cached diagnostic: `{payload['runtime_diagnostics']['mbo_rows_processed_total']}`.",
        f"- Largest cached MBO group rows: `{payload['runtime_diagnostics']['largest_group_rows']}`.",
        f"- Scaling readout: {payload['runtime_diagnostics']['scaling_readout']}",
        "",
        "## Non-Claims",
        "",
        "- No new Databento data was fetched.",
        "- No threshold was optimized or selected.",
        "- Synthetic outcome contrast is not actual broker-R validation.",
        "- This report does not promote a live filter.",
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mbo-json", default=DEFAULT_MBO_JSON)
    parser.add_argument("--mbp10-json", default=DEFAULT_MBP10_JSON)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(load_json(args.mbo_json), load_json(args.mbp10_json))
    payload["inputs"]["mbo_json"] = args.mbo_json
    payload["inputs"]["mbp10_json"] = args.mbp10_json
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    for feed, row in payload["feeds"].items():
        depth_delta = row["candidate_context"]["event15_total_depth"]["candidate_minus_context"]
        flips = row["stability"]["event15_total_depth"]["leave_one_date"]["sign_flip_count"]
        print(f"{feed}: depth_delta={depth_delta} leave_one_date_flips={flips}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
