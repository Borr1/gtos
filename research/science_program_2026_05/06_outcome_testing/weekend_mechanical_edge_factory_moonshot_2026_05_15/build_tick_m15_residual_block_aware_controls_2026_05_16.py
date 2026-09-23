#!/usr/bin/env python3
"""Build row reconstruction and block-aware controls for Route C residuals.

This repairs the aggregate-only weakness in the first Route C residual packet.
It writes every residual-denominator row, joins source primitive metadata, audits
cross-descriptor duplicate event reuse, and runs block-preserving circular
controls by date, month, source file, and hour-of-day. It is still research
diagnostic work, not validation or promotion.
"""

from __future__ import annotations

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
PRIMITIVE_EVENT_LEDGER = ROUTE_DIR / f"TICK_M15_PRIMITIVE_EVENT_LEDGER_{SOURCE_STAMP}.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_FULL_PERMUTATION_CONCENTRATION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_RESIDUAL_BLOCK_AWARE_CONTROL_RESULT_{STAMP}.json"
ROW_RECONSTRUCTION_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_ROW_RECONSTRUCTION_LEDGER_{STAMP}.jsonl"
CROSS_DESCRIPTOR_DUPLICATE_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_CROSS_DESCRIPTOR_DUPLICATE_LEDGER_{STAMP}.jsonl"
BLOCK_CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_BLOCK_AWARE_CONTROL_LEDGER_{STAMP}.jsonl"
AXIS_STRESS_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_AXIS_STRESS_LEDGER_{STAMP}.jsonl"
AGGREGATE_CONCENTRATION_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_AGGREGATE_CONCENTRATION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_RESIDUAL_BLOCK_AWARE_CONTROL_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C row reconstruction and block-aware controls only; not validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

PRIMITIVE_JOIN_FIELDS = [
    "source_file",
    "trade_date",
    "source_completeness",
    "n_ticks",
    "n_classified_ticks",
    "duplicate_ts_msc_rows",
    "spread_median",
    "spread_max",
    "spread_close",
    "tick_velocity_per_sec",
    "cumulative_delta",
    "abs_cumulative_delta",
    "buy_ticks",
    "sell_ticks",
    "neutral_ticks",
    "buy_pct",
    "price_change",
    "price_range",
    "cvd_divergence_flag",
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


def tail_fraction_ge(observed: float | None, values: list[float]) -> float | None:
    numeric = [value for value in values if safe_float(value) is not None]
    if observed is None or not numeric:
        return None
    return safe_float(sum(1 for value in numeric if value >= observed) / len(numeric))


def block_key(row: dict[str, Any], scheme: str, primitive: dict[str, Any] | None) -> str:
    if scheme == "event_date":
        return row["bar_open_utc"][:10]
    if scheme == "event_month":
        return row["bar_open_utc"][:7]
    if scheme == "hour_of_day_utc":
        return row["bar_open_utc"][11:13]
    if scheme == "source_file":
        return str((primitive or {}).get("source_file") or "SOURCE_FILE_MISSING")
    raise ValueError(f"unknown block scheme {scheme}")


def block_preserving_control(
    denom_rows: list[dict[str, Any]],
    primitives: dict[str, dict[str, Any]],
    primitive_flag: str,
    scheme: str,
) -> dict[str, Any]:
    observed_rows = [row for row in denom_rows if primitive_flag in row.get("primitive_flags", [])]
    observed = stats(observed_rows)
    grouped_indices: dict[str, list[int]] = {}
    flagged_indices_by_block: dict[str, list[int]] = {}
    for idx, row in enumerate(denom_rows):
        primitive = primitives.get(f"{row['symbol']}|{row['bar_open_utc']}")
        key = block_key(row, scheme, primitive)
        grouped_indices.setdefault(key, []).append(idx)
        if primitive_flag in row.get("primitive_flags", []):
            flagged_indices_by_block.setdefault(key, []).append(idx)

    control_values: list[float] = []
    control_alignment_values: list[float] = []
    max_shift = max((len(indices) for indices in grouped_indices.values()), default=0)
    for shift in range(1, max_shift):
        selected_indices: list[int] = []
        for key, flagged_indices in flagged_indices_by_block.items():
            block_indices = grouped_indices[key]
            position_by_index = {value: pos for pos, value in enumerate(block_indices)}
            block_n = len(block_indices)
            if block_n <= 1:
                selected_indices.extend(flagged_indices)
                continue
            for flagged_idx in flagged_indices:
                local_pos = position_by_index[flagged_idx]
                selected_indices.append(block_indices[(local_pos + shift) % block_n])
        selected_rows = [denom_rows[idx] for idx in selected_indices]
        selected_stats = stats(selected_rows)
        abs_value = safe_float(selected_stats["mean_abs_future_change"])
        align_value = safe_float(selected_stats["delta_alignment_rate"])
        if abs_value is not None:
            control_values.append(abs_value)
        if align_value is not None:
            control_alignment_values.append(align_value)

    block_counts = {key: len(value) for key, value in grouped_indices.items()}
    flagged_block_counts = {key: len(value) for key, value in flagged_indices_by_block.items()}
    top_block_key = None
    top_block_flagged_count = 0
    top_block_flagged_share = None
    if flagged_block_counts and observed["n"]:
        top_block_key, top_block_flagged_count = max(flagged_block_counts.items(), key=lambda item: item[1])
        top_block_flagged_share = safe_float(top_block_flagged_count / observed["n"])

    abs_tail = tail_fraction_ge(observed["mean_abs_future_change"], control_values)
    alignment_tail = tail_fraction_ge(observed["delta_alignment_rate"], control_alignment_values)
    if observed["n"] < 20 or abs_tail is None:
        bucket = "BLOCK_CONTROL_UNDERPOWERED"
    elif abs_tail <= 0.05:
        bucket = "BLOCK_CONTROL_RESIDUAL_LOW_TAIL"
    else:
        bucket = "BLOCK_CONTROL_WEAKENED"

    return {
        "block_scheme": scheme,
        "block_count": len(block_counts),
        "flagged_block_count": len(flagged_block_counts),
        "observed_flagged_n": observed["n"],
        "observed_mean_abs_future_change": observed["mean_abs_future_change"],
        "observed_delta_alignment_rate": observed["delta_alignment_rate"],
        "control_count": len(control_values),
        "tail_fraction_ge_observed_abs": abs_tail,
        "tail_fraction_ge_observed_alignment": alignment_tail,
        "control_mean_abs_future_change": mean(control_values),
        "control_mean_delta_alignment_rate": mean(control_alignment_values),
        "top_block_key": top_block_key,
        "top_block_flagged_count": top_block_flagged_count,
        "top_block_flagged_share": top_block_flagged_share,
        "block_control_bucket": bucket,
    }


def axis_leave_out_stress(
    denom_rows: list[dict[str, Any]],
    primitives: dict[str, dict[str, Any]],
    primitive_flag: str,
    scheme: str,
) -> list[dict[str, Any]]:
    flagged_rows = [row for row in denom_rows if primitive_flag in row.get("primitive_flags", [])]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in flagged_rows:
        primitive = primitives.get(f"{row['symbol']}|{row['bar_open_utc']}")
        grouped.setdefault(block_key(row, scheme, primitive), []).append(row)

    out: list[dict[str, Any]] = []
    for key, removed_rows in sorted(grouped.items()):
        removed_ids = {row["bar_open_utc"] for row in removed_rows}
        remaining = [row for row in flagged_rows if row["bar_open_utc"] not in removed_ids]
        remaining_stats = stats(remaining)
        out.append({
            "axis": scheme,
            "removed_key": key,
            "removed_n": len(removed_rows),
            "remaining_n": len(remaining),
            "remaining_stats": remaining_stats,
        })
    return out


def source_fields(primitive: dict[str, Any] | None) -> dict[str, Any]:
    primitive = primitive or {}
    return {field: primitive.get(field) for field in PRIMITIVE_JOIN_FIELDS}


def row_reconstruction(
    control_rows: list[dict[str, Any]],
    denominator_by_key: dict[tuple[str, str, str], list[dict[str, Any]]],
    primitive_by_symbol_bar: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    duplicate_refs: dict[str, list[dict[str, Any]]] = {}

    for control in control_rows:
        key = (control["symbol"], control["session_bucket"], control["horizon_id"])
        denom_rows = denominator_by_key[key]
        primitive_flag = control["primitive_flag"]
        flagged_n = control["flagged_n"]
        rotation = max(1, len(denom_rows) // 3) if denom_rows else 0
        flagged_indices = [
            idx for idx, row in enumerate(denom_rows)
            if primitive_flag in row.get("primitive_flags", [])
        ]
        single_rotation_indices = {
            (idx + rotation) % len(denom_rows)
            for idx in flagged_indices
        } if denom_rows else set()

        for idx, row in enumerate(denom_rows):
            primitive = primitive_by_symbol_bar.get(f"{row['symbol']}|{row['bar_open_utc']}")
            is_flagged = primitive_flag in row.get("primitive_flags", [])
            row_id = f"{row['symbol']}|{row['bar_open_utc']}"
            role = "flagged" if is_flagged else "denominator_control_pool"
            out = {
                "queue_id": control["queue_id"],
                "route_id": ROUTE_ID,
                "row_id": row_id,
                "row_role": role,
                "is_flagged": is_flagged,
                "single_rotation_member": idx in single_rotation_indices,
                "denominator_index": idx,
                "denominator_n": len(denom_rows),
                "flagged_n_for_descriptor": flagged_n,
                "symbol": row["symbol"],
                "session_bucket": row["session_bucket"],
                "horizon_id": row["horizon_id"],
                "primitive_flag": primitive_flag,
                "bar_open_utc": row["bar_open_utc"],
                "bar_close_utc": row["bar_close_utc"],
                "future_bar_open_utc": row["future_bar_open_utc"],
                "future_change": row.get("future_change"),
                "future_abs_change": row.get("future_abs_change"),
                "future_change_per_current_range": row.get("future_change_per_current_range"),
                "delta_sign": row.get("delta_sign"),
                "future_sign": row.get("future_sign"),
                "delta_aligned_with_future": row.get("delta_aligned_with_future"),
                "primitive_flags": row.get("primitive_flags", []),
                "source_join_found": primitive is not None,
                "source_fields": source_fields(primitive),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
            rows.append(out)
            if is_flagged:
                duplicate_refs.setdefault(row_id, []).append({
                    "queue_id": control["queue_id"],
                    "symbol": row["symbol"],
                    "session_bucket": row["session_bucket"],
                    "horizon_id": row["horizon_id"],
                    "primitive_flag": primitive_flag,
                    "bar_open_utc": row["bar_open_utc"],
                })

    duplicate_rows: list[dict[str, Any]] = []
    for row_id, refs in sorted(duplicate_refs.items()):
        descriptors = [
            f"{ref['queue_id']}|{ref['horizon_id']}|{ref['primitive_flag']}"
            for ref in refs
        ]
        first = refs[0]
        duplicate_rows.append({
            "row_id": row_id,
            "route_id": ROUTE_ID,
            "symbol": first["symbol"],
            "bar_open_utc": first["bar_open_utc"],
            "descriptor_reference_count": len(refs),
            "descriptor_references": descriptors,
            "sessions": sorted({ref["session_bucket"] for ref in refs}),
            "horizons": sorted({ref["horizon_id"] for ref in refs}),
            "primitive_flags": sorted({ref["primitive_flag"] for ref in refs}),
            "duplicate_effective_n_contribution": safe_float(1 / len(refs)) if refs else None,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })
    return rows, duplicate_rows


def concentration_rows(
    row_reconstruction_rows: list[dict[str, Any]],
    duplicate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    flagged = [row for row in row_reconstruction_rows if row["is_flagged"]]
    denom = row_reconstruction_rows
    out: list[dict[str, Any]] = []

    axes = {
        "symbol": lambda row: row["symbol"],
        "session_bucket": lambda row: row["session_bucket"],
        "horizon_id": lambda row: row["horizon_id"],
        "primitive_flag": lambda row: row["primitive_flag"],
        "event_date": lambda row: row["bar_open_utc"][:10],
        "event_hour_utc": lambda row: row["bar_open_utc"][11:13],
        "source_file": lambda row: row["source_fields"].get("source_file") or "SOURCE_FILE_MISSING",
    }
    for axis, getter in axes.items():
        for population_name, population in [("flagged_descriptor_references", flagged), ("denominator_references", denom)]:
            counts = Counter(getter(row) for row in population)
            total = len(population)
            for key, count in sorted(counts.items(), key=lambda item: str(item[0])):
                out.append({
                    "route_id": ROUTE_ID,
                    "axis": axis,
                    "axis_value": key,
                    "population": population_name,
                    "row_count": count,
                    "population_n": total,
                    "population_share": safe_float(count / total) if total else None,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                })

    duplicate_count_distribution = Counter(row["descriptor_reference_count"] for row in duplicate_rows)
    for reference_count, count in sorted(duplicate_count_distribution.items()):
        out.append({
            "route_id": ROUTE_ID,
            "axis": "cross_descriptor_duplicate_reference_count",
            "axis_value": reference_count,
            "population": "unique_flagged_bars",
            "row_count": count,
            "population_n": len(duplicate_rows),
            "population_share": safe_float(count / len(duplicate_rows)) if duplicate_rows else None,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })
    return out


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "tick_m15_residual_block_aware_control_builder", "created"),
        (RESULT_PATH, "tick_m15_residual_block_aware_control_result", "created"),
        (ROW_RECONSTRUCTION_LEDGER, "tick_m15_residual_row_reconstruction_ledger", "created"),
        (CROSS_DESCRIPTOR_DUPLICATE_LEDGER, "tick_m15_residual_cross_descriptor_duplicate_ledger", "created"),
        (BLOCK_CONTROL_LEDGER, "tick_m15_residual_block_aware_control_ledger", "created"),
        (AXIS_STRESS_LEDGER, "tick_m15_residual_axis_stress_ledger", "created"),
        (AGGREGATE_CONCENTRATION_LEDGER, "tick_m15_residual_aggregate_concentration_ledger", "created"),
        (SUMMARY_PATH, "tick_m15_residual_block_aware_control_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], block_bucket_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "tick_m15_residual_block_aware_controls",
        "status": "done",
        "route": "tick_sierra_orderflow_route_c",
        "details": (
            "Built full row reconstruction, cross-descriptor duplicate audit, source-joined concentration ledgers, "
            "and date/month/source/hour block-aware controls for all Route C residual descriptors."
        ),
        "counts": counts,
        "block_bucket_counts": block_bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(ROW_RECONSTRUCTION_LEDGER),
            relative(CROSS_DESCRIPTOR_DUPLICATE_LEDGER),
            relative(BLOCK_CONTROL_LEDGER),
            relative(AGGREGATE_CONCENTRATION_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    target_rows = read_jsonl(TARGET_EVENT_LEDGER)
    primitive_rows = read_jsonl(PRIMITIVE_EVENT_LEDGER)
    control_rows = read_jsonl(CONTROL_LEDGER)

    primitive_by_symbol_bar = {
        f"{row['symbol']}|{row['bar_open_utc']}": row
        for row in primitive_rows
    }
    denominator_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in target_rows:
        key = (row["symbol"], row["session_bucket"], row["horizon_id"])
        denominator_by_key.setdefault(key, []).append(row)
    for rows in denominator_by_key.values():
        rows.sort(key=lambda value: value["bar_open_utc"])

    reconstruction_rows, duplicate_rows = row_reconstruction(
        control_rows,
        denominator_by_key,
        primitive_by_symbol_bar,
    )

    block_control_rows: list[dict[str, Any]] = []
    axis_stress_rows: list[dict[str, Any]] = []
    for control in control_rows:
        key = (control["symbol"], control["session_bucket"], control["horizon_id"])
        denom_rows = denominator_by_key[key]
        primitive_flag = control["primitive_flag"]
        for scheme in ["event_date", "event_month", "source_file", "hour_of_day_utc"]:
            block_control = block_preserving_control(
                denom_rows,
                primitive_by_symbol_bar,
                primitive_flag,
                scheme,
            )
            block_control.update({
                "queue_id": control["queue_id"],
                "route_id": ROUTE_ID,
                "symbol": control["symbol"],
                "session_bucket": control["session_bucket"],
                "horizon_id": control["horizon_id"],
                "primitive_flag": primitive_flag,
                "source_control_bucket": control["control_bucket"],
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })
            block_control_rows.append(block_control)

            for stress in axis_leave_out_stress(
                denom_rows,
                primitive_by_symbol_bar,
                primitive_flag,
                scheme,
            ):
                stress.update({
                    "queue_id": control["queue_id"],
                    "route_id": ROUTE_ID,
                    "symbol": control["symbol"],
                    "session_bucket": control["session_bucket"],
                    "horizon_id": control["horizon_id"],
                    "primitive_flag": primitive_flag,
                    "source_control_bucket": control["control_bucket"],
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                })
                axis_stress_rows.append(stress)

    aggregate_rows = concentration_rows(reconstruction_rows, duplicate_rows)

    write_jsonl(ROW_RECONSTRUCTION_LEDGER, reconstruction_rows)
    write_jsonl(CROSS_DESCRIPTOR_DUPLICATE_LEDGER, duplicate_rows)
    write_jsonl(BLOCK_CONTROL_LEDGER, block_control_rows)
    write_jsonl(AXIS_STRESS_LEDGER, axis_stress_rows)
    write_jsonl(AGGREGATE_CONCENTRATION_LEDGER, aggregate_rows)

    block_bucket_counts = Counter(row["block_control_bucket"] for row in block_control_rows)
    source_join_missing = sum(1 for row in reconstruction_rows if not row["source_join_found"])
    flagged_reference_count = sum(1 for row in reconstruction_rows if row["is_flagged"])
    unique_flagged_bars = len(duplicate_rows)
    duplicate_references = flagged_reference_count - unique_flagged_bars

    counts = {
        "residual_input_rows": len(control_rows),
        "row_reconstruction_rows": len(reconstruction_rows),
        "flagged_descriptor_references": flagged_reference_count,
        "unique_flagged_bars": unique_flagged_bars,
        "duplicate_flagged_references": duplicate_references,
        "block_control_rows": len(block_control_rows),
        "axis_stress_rows": len(axis_stress_rows),
        "aggregate_concentration_rows": len(aggregate_rows),
        "source_join_missing_rows": source_join_missing,
    }
    result = {
        "schema": "tick_m15_residual_block_aware_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "ROUTE_C_ROW_RECONSTRUCTION_AND_BLOCK_AWARE_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "block_bucket_counts": dict(block_bucket_counts),
        "block_schemes": ["event_date", "event_month", "source_file", "hour_of_day_utc"],
        "source_join_fields": PRIMITIVE_JOIN_FIELDS,
        "duplicate_warning": "Flagged descriptor references are not independent bars; use cross-descriptor duplicate ledger before any challenger comparison.",
        "next_same_resource_work": [
            "cross_horizon_and_cross_session transfer matrix",
            "entry_geometry and cost packet",
            "Sierra SCID/depth parser timestamp contract for proxy repair",
            "broader symbol/timeframe acquisition if owned/free/current source exists",
        ],
        "not_completion": "This packet deepens Route C but does not complete the 60-hour moonshot objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Residual Block-Aware Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: row reconstruction and block-aware diagnostics only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        summary.append(f"- `{key}`: `{value}`")
    summary.extend(["", "## Block-Control Buckets", ""])
    for key, value in sorted(block_bucket_counts.items()):
        summary.append(f"- `{key}`: `{value}`")
    summary.extend([
        "",
        "## Boundary",
        "",
        "- Every residual-denominator row is reconstructed and source-joined where possible.",
        "- Block-aware controls preserve date, month, source-file, or UTC-hour flagged counts before rotating inside each block.",
        "- Cross-descriptor duplicate bars are explicit; descriptor references must not be treated as independent trade opportunities.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(block_bucket_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
