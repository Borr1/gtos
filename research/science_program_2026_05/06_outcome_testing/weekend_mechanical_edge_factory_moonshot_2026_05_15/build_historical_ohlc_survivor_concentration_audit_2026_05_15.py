#!/usr/bin/env python3
"""Audit concentration and event clustering for OHLC placebo survivors."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
SURVIVOR_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_NEIGHBOR_PLACEBO_SURVIVOR_QUEUE_2026-05-15.jsonl"
EVENTS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_PRIMITIVE_EVENT_LEDGER_2026-05-15.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_SURVIVOR_CONCENTRATION_AUDIT_RESULT_2026-05-15.json"
AUDIT_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_SURVIVOR_CONCENTRATION_AUDIT_LEDGER_2026-05-15.jsonl"
CLUSTER_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_SURVIVOR_EVENT_CLUSTER_LEDGER_2026-05-15.jsonl"
ROUTE_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_SURVIVOR_CLUSTER_ROUTE_QUEUE_2026-05-15.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_SURVIVOR_CONCENTRATION_AUDIT_SUMMARY_2026-05-15.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Survivor concentration and event-clustering audit only. This is not "
    "sealed validation, R/PnL, expectancy, fillability, live-readiness, or a "
    "promotion verdict."
)

MIN_CLUSTERS = 40
MIN_DATES = 20
MAX_DATE_SHARE = 0.10
MAX_MONTH_SHARE = 0.45
MIN_CLUSTER_EFFECTIVE_RATIO = 0.35


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def parse_ts(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def r6(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def safe_div(num: float | int | None, den: float | int | None) -> float | None:
    if den in (0, 0.0, None):
        return None
    if num is None:
        return None
    return float(num) / float(den)


def key_for(row: dict[str, Any]) -> tuple[str, str, str, int]:
    return (row["symbol"], row["session"], row["primitive_id"], int(row["horizon_bars"]))


def route_id_for(key: tuple[str, str, str, int]) -> str:
    symbol, session, primitive_id, horizon = key
    return f"{symbol}|{session}|{primitive_id}|h{horizon}"


def load_survivors() -> dict[tuple[str, str, str, int], dict[str, Any]]:
    return {key_for(row): row for row in read_jsonl(SURVIVOR_QUEUE_PATH)}


def load_survivor_events(keys: set[tuple[str, str, str, int]]) -> dict[tuple[str, str, str, int], list[dict[str, Any]]]:
    groups: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(EVENTS_PATH):
        key = (row["symbol"], row["session"], row["primitive_id"], int(row["horizon_bars"]))
        if key in keys:
            groups[key].append(row)
    for rows in groups.values():
        rows.sort(key=lambda item: item["time_utc"])
    return groups


def cluster_events(
    key: tuple[str, str, str, int],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    _, _, _, horizon = key
    gap = timedelta(minutes=15 * horizon)
    clusters: list[list[dict[str, Any]]] = []
    for row in rows:
        if not clusters:
            clusters.append([row])
            continue
        previous_ts = parse_ts(clusters[-1][-1]["time_utc"])
        current_ts = parse_ts(row["time_utc"])
        if current_ts - previous_ts <= gap:
            clusters[-1].append(row)
        else:
            clusters.append([row])

    rendered: list[dict[str, Any]] = []
    for idx, cluster in enumerate(clusters, 1):
        directional_values = [
            float(item["directional_close_units"])
            for item in cluster
            if item.get("directional_close_units") is not None
        ]
        positive_values = [1.0 if value > 0 else 0.0 for value in directional_values]
        rendered.append(
            {
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "HISTORICAL_OHLC_SURVIVOR_EVENT_CLUSTER",
                "route_candidate_id": route_id_for(key),
                "cluster_id": f"{route_id_for(key)}|cluster_{idx:04d}",
                "symbol": key[0],
                "session": key[1],
                "primitive_id": key[2],
                "horizon_bars": key[3],
                "event_count": len(cluster),
                "start_time_utc": cluster[0]["time_utc"],
                "end_time_utc": cluster[-1]["time_utc"],
                "start_date": cluster[0]["date"],
                "end_date": cluster[-1]["date"],
                "mean_directional_close_units": r6(
                    sum(directional_values) / len(directional_values) if directional_values else None
                ),
                "directional_positive_share": r6(
                    sum(positive_values) / len(positive_values) if positive_values else None
                ),
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rendered


def summarize_survivor(
    key: tuple[str, str, str, int],
    survivor: dict[str, Any],
    events: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
) -> dict[str, Any]:
    event_count = len(events)
    date_counts = Counter(row["date"] for row in events)
    month_counts = Counter(row["date"][:7] for row in events)
    directional_values = [
        float(row["directional_close_units"])
        for row in events
        if row.get("directional_close_units") is not None
    ]
    raw_mean = sum(directional_values) / len(directional_values) if directional_values else None
    raw_positive = (
        sum(1.0 if value > 0 else 0.0 for value in directional_values) / len(directional_values)
        if directional_values
        else None
    )
    cluster_directional = [
        row["mean_directional_close_units"]
        for row in clusters
        if row.get("mean_directional_close_units") is not None
    ]
    cluster_positive = [
        row["directional_positive_share"]
        for row in clusters
        if row.get("directional_positive_share") is not None
    ]
    cluster_mean = sum(cluster_directional) / len(cluster_directional) if cluster_directional else None
    cluster_positive_mean = sum(cluster_positive) / len(cluster_positive) if cluster_positive else None

    midpoint = event_count // 2
    first_half = events[:midpoint]
    second_half = events[midpoint:]

    def half_mean(rows: list[dict[str, Any]]) -> float | None:
        vals = [
            float(row["directional_close_units"])
            for row in rows
            if row.get("directional_close_units") is not None
        ]
        return sum(vals) / len(vals) if vals else None

    first_half_mean = half_mean(first_half)
    second_half_mean = half_mean(second_half)

    max_date_count = max(date_counts.values()) if date_counts else 0
    max_month_count = max(month_counts.values()) if month_counts else 0
    max_cluster_count = max((row["event_count"] for row in clusters), default=0)
    cluster_count = len(clusters)
    cluster_effective_ratio = safe_div(cluster_count, event_count)
    max_date_share = safe_div(max_date_count, event_count)
    max_month_share = safe_div(max_month_count, event_count)
    max_cluster_event_share = safe_div(max_cluster_count, event_count)

    if not events:
        audit_bucket = "NO_EVENT_ROWS"
    elif cluster_count < MIN_CLUSTERS:
        audit_bucket = "LOW_EFFECTIVE_CLUSTER_COUNT"
    elif len(date_counts) < MIN_DATES:
        audit_bucket = "LOW_UNIQUE_DATE_COUNT"
    elif (max_date_share or 1.0) > MAX_DATE_SHARE:
        audit_bucket = "DATE_CONCENTRATED"
    elif (max_month_share or 1.0) > MAX_MONTH_SHARE:
        audit_bucket = "MONTH_CONCENTRATED"
    elif (cluster_effective_ratio or 0.0) < MIN_CLUSTER_EFFECTIVE_RATIO:
        audit_bucket = "CLUSTER_DUPLICATE_HEAVY"
    elif raw_mean is None or cluster_mean is None or raw_mean <= 0 or cluster_mean <= 0:
        audit_bucket = "CLUSTER_WEIGHTED_SIGN_FRAGILE"
    elif first_half_mean is None or second_half_mean is None or first_half_mean <= 0 or second_half_mean <= 0:
        audit_bucket = "TIME_SPLIT_SIGN_FRAGILE"
    else:
        audit_bucket = "DESCRIPTIVE_CLUSTER_AND_CONCENTRATION_RESILIENT"

    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "evidence_class": "HISTORICAL_OHLC_SURVIVOR_CONCENTRATION_AUDIT",
        "route_candidate_id": route_id_for(key),
        "symbol": key[0],
        "session": key[1],
        "primitive_family": survivor["primitive_family"],
        "primitive_id": key[2],
        "horizon_bars": key[3],
        "event_count": event_count,
        "unique_dates": len(date_counts),
        "unique_months": len(month_counts),
        "cluster_count": cluster_count,
        "cluster_effective_ratio": r6(cluster_effective_ratio),
        "max_single_date_share": r6(max_date_share),
        "max_single_month_share": r6(max_month_share),
        "max_cluster_event_share": r6(max_cluster_event_share),
        "raw_mean_directional_close_units": r6(raw_mean),
        "raw_directional_positive_share": r6(raw_positive),
        "cluster_weighted_mean_directional_close_units": r6(cluster_mean),
        "cluster_weighted_directional_positive_share": r6(cluster_positive_mean),
        "first_half_mean_directional_close_units": r6(first_half_mean),
        "second_half_mean_directional_close_units": r6(second_half_mean),
        "top_date": date_counts.most_common(1)[0][0] if date_counts else None,
        "top_month": month_counts.most_common(1)[0][0] if month_counts else None,
        "audit_bucket": audit_bucket,
        "input_placebo_status": survivor["placebo_status"],
        "input_control_coverage": survivor["control_coverage"],
        "required_next_controls": [
            "purged train/test or frozen forward route",
            "cost/fill model before any strategy projection",
            "same-source cross-period replay",
            "instrument eligibility review",
        ],
        "safe_flags": SAFE_FLAGS,
    }


def write_summary(result: dict[str, Any], bucket_counts: Counter[str]) -> None:
    lines = [
        "# Historical OHLC Survivor Concentration Audit",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, "
        "`outcome_review_opened=false`, `live_effect=false`",
        "",
        f"Evidence class: `{result['evidence_class']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Audit Buckets", ""])
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Cluster-resilient rows remain research candidates, not trade rules.",
            "- Cluster weighting removes adjacent-event inflation but does not provide sealed validation.",
            "- No row includes spread, fillability, slippage, commission, or lifecycle truth.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    survivors = load_survivors()
    events_by_key = load_survivor_events(set(survivors.keys()))

    audit_rows: list[dict[str, Any]] = []
    cluster_rows: list[dict[str, Any]] = []
    for key, survivor in sorted(survivors.items()):
        events = events_by_key.get(key, [])
        clusters = cluster_events(key, events)
        cluster_rows.extend(clusters)
        audit_rows.append(summarize_survivor(key, survivor, events, clusters))

    route_rows = [
        row
        for row in audit_rows
        if row["audit_bucket"] == "DESCRIPTIVE_CLUSTER_AND_CONCENTRATION_RESILIENT"
    ]
    bucket_counts = Counter(row["audit_bucket"] for row in audit_rows)

    write_jsonl(AUDIT_LEDGER_PATH, audit_rows)
    write_jsonl(CLUSTER_LEDGER_PATH, cluster_rows)
    write_jsonl(ROUTE_QUEUE_PATH, route_rows)

    result = {
        "schema": "historical_ohlc_survivor_concentration_audit_result_v1",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "HISTORICAL_OHLC_SURVIVOR_CONCENTRATION_AUDIT",
        "claim_boundary": CLAIM_BOUNDARY,
        "parameters": {
            "input": "all rows from HISTORICAL_OHLC_NEIGHBOR_PLACEBO_SURVIVOR_QUEUE; no top-N cap",
            "cluster_gap": "same route candidate events separated by <= horizon_bars * 15 minutes",
            "minimum_clusters": MIN_CLUSTERS,
            "minimum_unique_dates": MIN_DATES,
            "maximum_single_date_share": MAX_DATE_SHARE,
            "maximum_single_month_share": MAX_MONTH_SHARE,
            "minimum_cluster_effective_ratio": MIN_CLUSTER_EFFECTIVE_RATIO,
        },
        "counts": {
            "input_survivor_rows": len(survivors),
            "audit_rows": len(audit_rows),
            "event_cluster_rows": len(cluster_rows),
            "cluster_resilient_route_rows": len(route_rows),
        },
        "audit_bucket_counts": dict(sorted(bucket_counts.items())),
        "required_next_controls": [
            "purged train/test or frozen forward route",
            "cost/fill model before any strategy projection",
            "same-source cross-period replay",
            "instrument eligibility review",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result, bucket_counts)
    print(json.dumps({"ok": True, "counts": result["counts"], "generated_utc": generated_utc}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
