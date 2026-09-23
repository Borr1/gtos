#!/usr/bin/env python3
"""Build Route C full-control and concentration diagnostics.

This consumes the 18 Route C residual descriptor rows and reconstructs their
same-symbol/session/horizon denominators from the neutral target-movement
ledger. It is a development diagnostic only: no validation, trade outcome,
R/PnL, expectancy, live-readiness, or promotion claim is opened here.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

TARGET_EVENT_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_EVENT_LEDGER_{SOURCE_STAMP}.jsonl"
RESIDUAL_QUEUE = ROUTE_DIR / f"TICK_M15_ROUTE_C_RESIDUAL_DESCRIPTOR_QUEUE_{SOURCE_STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_FULL_PERMUTATION_CONCENTRATION_RESULT_{STAMP}.json"
CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_FULL_PERMUTATION_CONCENTRATION_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"TICK_M15_FULL_PERMUTATION_CONCENTRATION_BUCKET_LEDGER_{STAMP}.jsonl"
BLOCKER_LEDGER = ROUTE_DIR / f"TICK_M15_FULL_PERMUTATION_CONCENTRATION_BLOCKER_LEDGER_{STAMP}.jsonl"
SEALED_FORWARD_LEDGER = ROUTE_DIR / f"TICK_M15_SEALED_FORWARD_PACKET_DESIGN_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_FULL_PERMUTATION_CONCENTRATION_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C development full-control and concentration diagnostics only; "
    "not validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

CONTROL_BUCKETS = [
    "DESCRIPTIVE_RESIDUAL_AFTER_CIRCULAR_HASH_AND_CONCENTRATION_CONTROLS",
    "DESCRIPTIVE_RESIDUAL_WITH_CONCENTRATION_CAUTION",
    "MIXED_AFTER_CIRCULAR_OR_HASH_CONTROL",
    "WEAKENED_BY_CIRCULAR_AND_HASH_CONTROL",
    "UNDERPOWERED_OR_SCHEMA_MISMATCH",
]

REMAINING_BLOCKERS = [
    "sealed_or_future_holdout_required",
    "entry_geometry_and_fillability_not_defined",
    "spread_slippage_commission_not_applied",
    "mt5_aggressor_proxy_only_on_current_broker",
    "full_combinatorial_permutation_not_claimed_by_circular_or_hash_controls",
    "sierra_binary_parser_timestamp_contract_still_required_for_depth_scid_expansion",
]

CONTROL_STATUS_BLOCKERS = [
    "same_denominator_all_circular_shift_control_completed_for_development_diagnostic",
    "same_denominator_hash_shuffle_control_completed_for_development_diagnostic",
    "sample_concentration_audit_completed_for_development_diagnostic",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def safe_float(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def mean(values: list[float]) -> float | None:
    return safe_float(sum(values) / len(values)) if values else None


def rate(values: list[bool]) -> float | None:
    return safe_float(sum(1 for value in values if value) / len(values)) if values else None


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return safe_float(ordered[0])
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return safe_float(ordered[lower] * (1.0 - weight) + ordered[upper] * weight)


def stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    changes = [
        safe_float(row.get("future_change"))
        for row in rows
        if safe_float(row.get("future_change")) is not None
    ]
    abs_changes = [
        safe_float(row.get("future_abs_change"))
        for row in rows
        if safe_float(row.get("future_abs_change")) is not None
    ]
    align = [
        bool(row["delta_aligned_with_future"])
        for row in rows
        if row.get("delta_sign", 0) != 0 and row.get("future_sign", 0) != 0
    ]
    return {
        "n": len(rows),
        "mean_future_change": mean(changes),
        "mean_abs_future_change": mean(abs_changes),
        "delta_alignment_n": len(align),
        "delta_alignment_rate": rate(align),
    }


def tail_summary(observed: float | None, control_values: list[float]) -> dict[str, Any]:
    numeric = [value for value in control_values if safe_float(value) is not None]
    if observed is None or not numeric:
        return {
            "control_count": len(numeric),
            "tail_fraction_ge_observed": None,
            "rank_fraction_le_observed": None,
            "control_mean": mean(numeric),
            "control_p05": quantile(numeric, 0.05),
            "control_p50": quantile(numeric, 0.50),
            "control_p95": quantile(numeric, 0.95),
            "control_max": max(numeric) if numeric else None,
        }
    ge_count = sum(1 for value in numeric if value >= observed)
    le_count = sum(1 for value in numeric if value <= observed)
    return {
        "control_count": len(numeric),
        "tail_fraction_ge_observed": safe_float(ge_count / len(numeric)),
        "rank_fraction_le_observed": safe_float(le_count / len(numeric)),
        "control_mean": mean(numeric),
        "control_p05": quantile(numeric, 0.05),
        "control_p50": quantile(numeric, 0.50),
        "control_p95": quantile(numeric, 0.95),
        "control_max": max(numeric) if numeric else None,
    }


def longest_consecutive_run(indices: list[int]) -> int:
    if not indices:
        return 0
    ordered = sorted(indices)
    longest = 1
    current = 1
    for previous, value in zip(ordered, ordered[1:]):
        if value == previous + 1:
            current += 1
        else:
            longest = max(longest, current)
            current = 1
    return max(longest, current)


def concentration(rows: list[dict[str, Any]], indices: list[int]) -> dict[str, Any]:
    dates = [row["bar_open_utc"][:10] for row in rows]
    months = [row["bar_open_utc"][:7] for row in rows]
    date_counts = Counter(dates)
    month_counts = Counter(months)
    n = len(rows)

    def top(counter: Counter[str]) -> tuple[str | None, int, float | None]:
        if not counter or n == 0:
            return None, 0, None
        key, count = counter.most_common(1)[0]
        return key, count, safe_float(count / n)

    top_date, top_date_count, top_date_share = top(date_counts)
    top_month, top_month_count, top_month_share = top(month_counts)
    date_hhi = sum((count / n) ** 2 for count in date_counts.values()) if n else None
    month_hhi = sum((count / n) ** 2 for count in month_counts.values()) if n else None
    effective_date_n = safe_float(1 / date_hhi) if date_hhi else None
    effective_month_n = safe_float(1 / month_hhi) if month_hhi else None
    longest_run = longest_consecutive_run(indices)

    warnings: list[str] = []
    if n < 20:
        warnings.append("flagged_n_lt_20")
    if len(date_counts) < 5:
        warnings.append("unique_event_dates_lt_5")
    if top_date_share is not None and top_date_share >= 0.25:
        warnings.append("top_event_date_share_ge_25pct")
    if effective_date_n is not None and effective_date_n < 5:
        warnings.append("effective_date_n_lt_5")
    if top_month_share is not None and top_month_share >= 0.60:
        warnings.append("top_month_share_ge_60pct")
    if n and longest_run / n >= 0.20:
        warnings.append("longest_denominator_index_run_ge_20pct_of_flagged")

    return {
        "unique_event_dates": len(date_counts),
        "top_event_date": top_date,
        "top_event_date_count": top_date_count,
        "top_event_date_share": top_date_share,
        "date_hhi": safe_float(date_hhi) if date_hhi is not None else None,
        "effective_date_n": effective_date_n,
        "unique_event_months": len(month_counts),
        "top_event_month": top_month,
        "top_event_month_count": top_month_count,
        "top_event_month_share": top_month_share,
        "month_hhi": safe_float(month_hhi) if month_hhi is not None else None,
        "effective_month_n": effective_month_n,
        "longest_consecutive_denominator_index_run": longest_run,
        "concentration_warnings": warnings,
        "concentration_caution": bool(warnings),
    }


def deterministic_hash_score(seed: int, row: dict[str, Any]) -> str:
    text = f"{seed}|{row['symbol']}|{row['session_bucket']}|{row['horizon_id']}|{row['bar_open_utc']}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_control_distributions(
    denom_rows: list[dict[str, Any]],
    flagged_indices: list[int],
) -> dict[str, Any]:
    denom_n = len(denom_rows)
    flagged_n = len(flagged_indices)
    circular_stats: list[dict[str, Any]] = []
    hash_stats: list[dict[str, Any]] = []

    if denom_n > 1 and flagged_n > 0:
        for shift in range(1, denom_n):
            shifted_rows = [denom_rows[(idx + shift) % denom_n] for idx in flagged_indices]
            circular_stats.append(stats(shifted_rows))

            ordered = sorted(
                range(denom_n),
                key=lambda idx, seed=shift: deterministic_hash_score(seed, denom_rows[idx]),
            )
            shuffled_rows = [denom_rows[idx] for idx in ordered[:flagged_n]]
            hash_stats.append(stats(shuffled_rows))

    return {
        "circular": circular_stats,
        "hash_shuffle": hash_stats,
    }


def metric_list(control_stats: list[dict[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in control_stats:
        value = safe_float(row.get(key))
        if value is not None:
            values.append(value)
    return values


def classify_row(
    flagged_n: int,
    flagged_n_matches_source: bool,
    circular_abs: dict[str, Any],
    hash_abs: dict[str, Any],
    concentration_info: dict[str, Any],
) -> str:
    if flagged_n < 20 or not flagged_n_matches_source:
        return "UNDERPOWERED_OR_SCHEMA_MISMATCH"
    circular_tail = circular_abs.get("tail_fraction_ge_observed")
    hash_tail = hash_abs.get("tail_fraction_ge_observed")
    if circular_tail is None or hash_tail is None:
        return "UNDERPOWERED_OR_SCHEMA_MISMATCH"
    survives_circular = circular_tail <= 0.05
    survives_hash = hash_tail <= 0.05
    if survives_circular and survives_hash and not concentration_info["concentration_caution"]:
        return "DESCRIPTIVE_RESIDUAL_AFTER_CIRCULAR_HASH_AND_CONCENTRATION_CONTROLS"
    if survives_circular and survives_hash and concentration_info["concentration_caution"]:
        return "DESCRIPTIVE_RESIDUAL_WITH_CONCENTRATION_CAUTION"
    if survives_circular or survives_hash:
        return "MIXED_AFTER_CIRCULAR_OR_HASH_CONTROL"
    return "WEAKENED_BY_CIRCULAR_AND_HASH_CONTROL"


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "tick_m15_full_permutation_concentration_builder", "created"),
        (RESULT_PATH, "tick_m15_full_permutation_concentration_result", "created"),
        (CONTROL_LEDGER, "tick_m15_full_permutation_concentration_ledger", "created"),
        (BUCKET_LEDGER, "tick_m15_full_permutation_concentration_bucket_ledger", "created"),
        (BLOCKER_LEDGER, "tick_m15_full_permutation_concentration_blocker_ledger", "created"),
        (SEALED_FORWARD_LEDGER, "tick_m15_sealed_forward_packet_design", "created"),
        (SUMMARY_PATH, "tick_m15_full_permutation_concentration_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known_paths = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [
        item for item in manifest["artifacts"]
        if item.get("path") not in known_paths
    ]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({
            "path": relative(path),
            "type": artifact_type,
            "status": status,
        })
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, control_rows: int, bucket_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "tick_m15_full_permutation_concentration",
        "status": "done",
        "route": "tick_sierra_orderflow_route_c",
        "details": (
            "Built full same-denominator circular-shift and deterministic hash-shuffle diagnostics plus "
            f"date/month concentration audit for all {control_rows} Route C residual descriptors. "
            "This remains development control evidence only."
        ),
        "bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(CONTROL_LEDGER),
            relative(BUCKET_LEDGER),
            relative(BLOCKER_LEDGER),
            relative(SEALED_FORWARD_LEDGER),
        ],
        "commands": [
            f"py -3 {relative(Path(__file__).resolve())}",
        ],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    target_rows = read_jsonl(TARGET_EVENT_LEDGER)
    residual_rows = read_jsonl(RESIDUAL_QUEUE)

    denominator_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in target_rows:
        key = (row["symbol"], row["session_bucket"], row["horizon_id"])
        denominator_by_key.setdefault(key, []).append(row)
    for rows in denominator_by_key.values():
        rows.sort(key=lambda value: value["bar_open_utc"])

    control_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    sealed_rows: list[dict[str, Any]] = []

    for residual in residual_rows:
        key = (residual["symbol"], residual["session_bucket"], residual["horizon_id"])
        denom_rows = denominator_by_key.get(key, [])
        primitive_flag = residual["primitive_flag"]
        flagged_indices = [
            idx for idx, row in enumerate(denom_rows)
            if primitive_flag in row.get("primitive_flags", [])
        ]
        flagged_rows = [denom_rows[idx] for idx in flagged_indices]
        observed = stats(flagged_rows)
        control_distributions = build_control_distributions(denom_rows, flagged_indices)
        circular_stats = control_distributions["circular"]
        hash_stats = control_distributions["hash_shuffle"]

        circular_abs = tail_summary(
            observed["mean_abs_future_change"],
            metric_list(circular_stats, "mean_abs_future_change"),
        )
        hash_abs = tail_summary(
            observed["mean_abs_future_change"],
            metric_list(hash_stats, "mean_abs_future_change"),
        )
        circular_alignment = tail_summary(
            observed["delta_alignment_rate"],
            metric_list(circular_stats, "delta_alignment_rate"),
        )
        hash_alignment = tail_summary(
            observed["delta_alignment_rate"],
            metric_list(hash_stats, "delta_alignment_rate"),
        )
        concentration_info = concentration(flagged_rows, flagged_indices)
        flagged_n_matches_source = observed["n"] == residual["flagged_n"]
        bucket = classify_row(
            observed["n"],
            flagged_n_matches_source,
            circular_abs,
            hash_abs,
            concentration_info,
        )

        queue_id = residual["queue_id"]
        row_out = {
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "symbol": residual["symbol"],
            "session_bucket": residual["session_bucket"],
            "horizon_id": residual["horizon_id"],
            "primitive_flag": primitive_flag,
            "source_residual_placebo_bucket": residual["placebo_bucket"],
            "denominator_n": len(denom_rows),
            "flagged_n": observed["n"],
            "source_residual_flagged_n": residual["flagged_n"],
            "flagged_n_matches_source_residual": flagged_n_matches_source,
            "observed_mean_abs_future_change": observed["mean_abs_future_change"],
            "observed_mean_future_change": observed["mean_future_change"],
            "observed_delta_alignment_n": observed["delta_alignment_n"],
            "observed_delta_alignment_rate": observed["delta_alignment_rate"],
            "circular_shift_abs_change": circular_abs,
            "hash_shuffle_abs_change": hash_abs,
            "circular_shift_delta_alignment": circular_alignment,
            "hash_shuffle_delta_alignment": hash_alignment,
            "concentration": concentration_info,
            "control_bucket": bucket,
            "control_scope": "all_same_denominator_circular_shifts_plus_deterministic_hash_shuffles",
            "control_limit": "not full combinatorial permutation and not statistical validation",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
        control_rows.append(row_out)

        for blocker in CONTROL_STATUS_BLOCKERS:
            blocker_rows.append({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "blocker": blocker,
                "status": "closed_for_development_diagnostic_only",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })
        for blocker in REMAINING_BLOCKERS:
            blocker_rows.append({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "blocker": blocker,
                "status": "open",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })
        if concentration_info["concentration_caution"]:
            blocker_rows.append({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "blocker": "concentration_caution_requires_sealed_or_forward_deconcentration",
                "status": "open_for_rows_with_concentration_warning",
                "concentration_warnings": concentration_info["concentration_warnings"],
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })

        sealed_rows.append({
            "packet_design_id": f"{queue_id}-SEALED-FORWARD-DESIGN",
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "symbol": residual["symbol"],
            "session_bucket": residual["session_bucket"],
            "horizon_id": residual["horizon_id"],
            "primitive_flag": primitive_flag,
            "frozen_development_descriptor": {
                "denominator_key": {
                    "symbol": residual["symbol"],
                    "session_bucket": residual["session_bucket"],
                    "horizon_id": residual["horizon_id"],
                },
                "primitive_flag": primitive_flag,
                "control_bucket": bucket,
            },
            "sealed_forward_status": "DESIGN_ONLY_NOT_OPENED",
            "minimum_future_requirements": [
                "future_or_sealed_rows_not_seen_by_this_development_packet",
                "same tick primitive schema and source hashes",
                "same denominator construction",
                "entry geometry and fillability definition before trade language",
                "spread slippage commission assumptions before R/PnL language",
                "duplicate and concentration controls",
            ],
            "forbidden_until_separate_lane": [
                "no validation claim",
                "no R/PnL or expectancy claim",
                "no live-readiness or promotion claim",
                "no runtime AI trade-decision use",
            ],
            "evidence_boundary": "sealed/forward packet design only; future rows are not opened here",
            "safe_flags": SAFE_FLAGS,
        })

    bucket_counts = Counter(row["control_bucket"] for row in control_rows)
    bucket_rows = [
        {
            "route_id": ROUTE_ID,
            "control_bucket": bucket,
            "row_count": bucket_counts.get(bucket, 0),
            "evidence_boundary": "bucket count only; no validation or promotion",
            "safe_flags": SAFE_FLAGS,
        }
        for bucket in CONTROL_BUCKETS
        if bucket_counts.get(bucket, 0) or bucket == "UNDERPOWERED_OR_SCHEMA_MISMATCH"
    ]

    write_jsonl(CONTROL_LEDGER, control_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(BLOCKER_LEDGER, blocker_rows)
    write_jsonl(SEALED_FORWARD_LEDGER, sealed_rows)

    result = {
        "schema": "tick_m15_full_permutation_concentration_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "ROUTE_C_DEVELOPMENT_FULL_CONTROL_AND_CONCENTRATION_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "control_scope": "all same-denominator circular shifts plus deterministic hash shuffles; concentration by event date/month/index run",
        "control_limit": "This is not full combinatorial permutation, not sealed validation, and not a trade outcome study.",
        "counts": {
            "residual_input_rows": len(residual_rows),
            "permutation_concentration_rows": len(control_rows),
            "bucket_rows": len(bucket_rows),
            "blocker_rows": len(blocker_rows),
            "sealed_forward_design_rows": len(sealed_rows),
        },
        "bucket_counts": dict(bucket_counts),
        "remaining_blockers": REMAINING_BLOCKERS,
        "closed_for_development_diagnostic_only": CONTROL_STATUS_BLOCKERS,
        "next_required_gate": "sealed_or_forward_holdout_plus_entry_geometry_and_cost_packet_required",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Full-Control And Concentration Diagnostics",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: Route C development diagnostics only. No validation, R/PnL, expectancy, live-readiness, or promotion verdict.",
        "",
        "## Counts",
        "",
        f"- Residual input rows: `{len(residual_rows)}`",
        f"- Control/concentration rows: `{len(control_rows)}`",
        f"- Bucket rows: `{len(bucket_rows)}`",
        f"- Blocker rows: `{len(blocker_rows)}`",
        f"- Sealed-forward packet design rows: `{len(sealed_rows)}`",
        "",
        "## Buckets",
        "",
    ]
    for bucket, count in sorted(bucket_counts.items()):
        summary.append(f"- `{bucket}`: `{count}`")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- The control uses every same-denominator circular shift and deterministic hash shuffles for each residual descriptor.",
        "- It does not claim a full combinatorial permutation test or statistical validation.",
        "- Sealed/future holdout, entry geometry, fillability, spread, slippage, commission, and broker-proxy blockers remain open.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, len(control_rows), dict(bucket_counts))

    print(json.dumps({
        "ok": True,
        "result": str(RESULT_PATH),
        "control_rows": len(control_rows),
        "blocker_rows": len(blocker_rows),
        "sealed_forward_design_rows": len(sealed_rows),
        "bucket_counts": dict(bucket_counts),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
