#!/usr/bin/env python3
"""Diagnostic summaries for joined Phase 3 external-feed candidate rows.

This is intentionally not a promotion evaluator. It extracts coverage, target
availability, frozen-source strata, and simple numeric screens from a candidate
join artifact, then suppresses any alpha verdict until CPCV/PBO/DSR gates can
be run on a larger realized-outcome dataset.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
import sys
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Iterable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.components.external_feeds import (  # noqa: E402
    DEFAULT_EXTERNAL_DATA_ROOT,
    safe_slug,
    utc_now,
)


DEFAULT_BUNDLE_ID = "calendar_macro_bundle_v1"
DEFAULT_TARGET_FIELD = "candidate__synthetic_realized_r"
DIAGNOSTIC_SCHEMA_VERSION = "external_feed_candidate_diagnostics_v1"

SOURCE_AVAILABILITY_FIELDS = (
    "fred__available",
    "lbma_calendar__available",
    "cftc_cot__available",
    "wgc__available",
    "flashalpha_gex__available",
)

CATEGORICAL_STRATA_FIELDS = (
    "symbol",
    "candidate__symbol",
    "candidate__framework",
    "candidate__direction",
    "candidate__kill_zone",
    "candidate__final_outcome",
    "candidate__synthetic_outcome",
)

NUMERIC_DIAGNOSTIC_FIELDS = (
    "fred__DGS10__value",
    "fred__DGS2__value",
    "fred__DFII10__value",
    "fred__T10YIE__value",
    "fred__VIXCLS__value",
    "fred__GVZCLS__value",
    "fred__DTWEXBGS__value",
    "lbma_calendar__minutes_to_next_fix",
    "lbma_calendar__minutes_since_previous_fix",
    "cftc_cot__disagg_combined__managed_money_net",
    "cftc_cot__disagg_combined__managed_money_long",
    "cftc_cot__disagg_combined__managed_money_short",
    "cftc_cot__disagg_combined__open_interest",
)

METHODOLOGY_THRESHOLDS = {
    "dsr_corrected_p_lt": 0.01,
    "pbo_lt": 0.4,
    "effective_n_gte": 3,
    "cumulative_program_trial_count": 200,
    "sharpe_noise_ceiling": 3.078,
}


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load JSONL rows from a candidate join artifact."""

    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_diagnostic_source_line"] = line_number
            rows.append(row)
    return rows


def find_latest_candidate_join(
    root: str | Path = DEFAULT_EXTERNAL_DATA_ROOT,
    *,
    bundle_id: str = DEFAULT_BUNDLE_ID,
    label_contains: str | None = None,
) -> Path:
    """Return the newest candidate-join JSONL artifact for a bundle."""

    join_dir = Path(root) / "validation" / safe_slug(bundle_id) / "candidate_join"
    candidates: list[Path] = []
    for path in join_dir.glob("*.jsonl"):
        if not path.is_file():
            continue
        if label_contains and label_contains not in path.name:
            continue
        candidates.append(path)
    if not candidates:
        raise FileNotFoundError(f"no candidate join JSONL files found in {join_dir}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def build_candidate_diagnostics(
    rows: Iterable[Mapping[str, Any]],
    *,
    input_path: str | Path | None = None,
    bundle_id: str = DEFAULT_BUNDLE_ID,
    target_field: str = DEFAULT_TARGET_FIELD,
    min_numeric_n: int = 8,
) -> dict[str, Any]:
    """Build verdict-suppressed diagnostics for joined candidate rows."""

    materialized = [dict(row) for row in rows]
    target_rows = [row for row in materialized if _finite_number(row.get(target_field))]
    actual_realized_rows = [
        row for row in materialized if _finite_number(row.get("candidate__realized_r"))
    ]
    diagnostic = {
        "schema_version": DIAGNOSTIC_SCHEMA_VERSION,
        "created_at_utc": utc_now().isoformat(),
        "bundle_id": bundle_id,
        "input_path": str(input_path) if input_path else None,
        "target_field": target_field,
        "rows_read": len(materialized),
        "target_rows": len(target_rows),
        "actual_realized_r_rows": len(actual_realized_rows),
        "baseline": summarize_rows(materialized, target_field=target_field),
        "coverage": build_coverage(materialized, target_field=target_field),
        "diagnostic_fold_counts": build_fold_counts(target_rows),
        "categorical_strata": {
            field: summarize_by_field(materialized, target_field=target_field, field=field)
            for field in CATEGORICAL_STRATA_FIELDS
            if any(field in row for row in materialized)
        },
        "source_availability_strata": {
            field: summarize_by_field(materialized, target_field=target_field, field=field)
            for field in SOURCE_AVAILABILITY_FIELDS
            if any(field in row for row in materialized)
        },
        "numeric_diagnostics": {
            field: summarize_numeric_field(
                materialized,
                target_field=target_field,
                numeric_field=field,
                min_n=min_numeric_n,
            )
            for field in NUMERIC_DIAGNOSTIC_FIELDS
            if any(row.get(field) not in (None, "") for row in materialized)
        },
    }
    diagnostic["methodology_gate"] = build_methodology_gate(diagnostic)
    return diagnostic


def summarize_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    target_field: str,
) -> dict[str, Any]:
    """Summarize target values across rows."""

    materialized = list(rows)
    values = [_as_float(row.get(target_field)) for row in materialized]
    finite_values = [value for value in values if value is not None]
    stats = summarize_values(finite_values)
    stats.update(
        {
            "row_count": len(materialized),
            "target_available": len(finite_values),
            "target_missing": len(materialized) - len(finite_values),
        }
    )
    return stats


def summarize_values(values: Iterable[float]) -> dict[str, Any]:
    """Summarize a numeric target without p-values or verdicts."""

    vals = [float(value) for value in values if _finite_number(value)]
    if not vals:
        return {
            "n": 0,
            "sum_r": None,
            "mean_r": None,
            "median_r": None,
            "stdev_r": None,
            "win_count": 0,
            "loss_count": 0,
            "flat_count": 0,
            "win_rate": None,
            "loss_rate": None,
            "min_r": None,
            "max_r": None,
        }
    n = len(vals)
    win_count = sum(1 for value in vals if value > 0)
    loss_count = sum(1 for value in vals if value < 0)
    flat_count = sum(1 for value in vals if value == 0)
    return {
        "n": n,
        "sum_r": sum(vals),
        "mean_r": mean(vals),
        "median_r": median(vals),
        "stdev_r": stdev(vals) if n >= 2 else 0.0,
        "win_count": win_count,
        "loss_count": loss_count,
        "flat_count": flat_count,
        "win_rate": win_count / n,
        "loss_rate": loss_count / n,
        "min_r": min(vals),
        "max_r": max(vals),
    }


def build_coverage(
    rows: Sequence[Mapping[str, Any]],
    *,
    target_field: str,
) -> dict[str, Any]:
    """Build high-level row, target, and source availability coverage."""

    target_rows = [row for row in rows if _finite_number(row.get(target_field))]
    output: dict[str, Any] = {
        "rows_read": len(rows),
        "target_field": target_field,
        "target_available": len(target_rows),
        "target_missing": len(rows) - len(target_rows),
        "actual_realized_r_available": sum(
            1 for row in rows if _finite_number(row.get("candidate__realized_r"))
        ),
        "external_validation_matched": sum(
            1 for row in rows if row.get("external_validation_matched") is True
        ),
        "external_validation_missing": sum(
            1 for row in rows if row.get("external_validation_matched") is False
        ),
        "source_availability": {},
    }
    for field in SOURCE_AVAILABILITY_FIELDS:
        if not any(field in row for row in rows):
            continue
        output["source_availability"][field] = {
            "all_rows_available": sum(1 for row in rows if row.get(field) is True),
            "target_rows_available": sum(1 for row in target_rows if row.get(field) is True),
        }
    return output


def build_fold_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Count fold diversity without pretending to compute effective N."""

    fields = ("symbol", "candidate__symbol", "fold_month", "fold_iso_week", "fold_quarter")
    output: dict[str, Any] = {}
    for field in fields:
        values = sorted({str(row.get(field)) for row in rows if row.get(field) not in (None, "")})
        output[field] = {"distinct": len(values), "values": values}
    return output


def summarize_by_field(
    rows: Sequence[Mapping[str, Any]],
    *,
    target_field: str,
    field: str,
) -> dict[str, Any]:
    """Summarize target values for a categorical or boolean field."""

    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[_label(row.get(field))].append(row)
    rendered: dict[str, Any] = {}
    for label, group_rows in sorted(groups.items(), key=lambda item: item[0]):
        rendered[label] = summarize_rows(group_rows, target_field=target_field)
    return {
        "field": field,
        "groups": rendered,
    }


def summarize_numeric_field(
    rows: Sequence[Mapping[str, Any]],
    *,
    target_field: str,
    numeric_field: str,
    min_n: int = 8,
) -> dict[str, Any]:
    """Report simple median-split and rank-correlation diagnostics."""

    pairs: list[tuple[float, float]] = []
    for row in rows:
        x = _as_float(row.get(numeric_field))
        y = _as_float(row.get(target_field))
        if x is None or y is None:
            continue
        pairs.append((x, y))
    base = {
        "field": numeric_field,
        "n": len(pairs),
        "min_required_n": min_n,
        "eligible": len(pairs) >= min_n,
    }
    if not pairs:
        base["reason"] = "no_rows_with_numeric_field_and_target"
        return base
    xs = [pair[0] for pair in pairs]
    ys = [pair[1] for pair in pairs]
    x_median = median(xs)
    lower_targets = [y for x, y in pairs if x <= x_median]
    upper_targets = [y for x, y in pairs if x > x_median]
    upper_stats = summarize_values(upper_targets)
    lower_stats = summarize_values(lower_targets)
    base.update(
        {
            "x_min": min(xs),
            "x_max": max(xs),
            "x_median": x_median,
            "x_distinct": len(set(xs)),
            "spearman_r": _spearman(xs, ys),
            "lower_or_equal_median": lower_stats,
            "upper_median": upper_stats,
            "upper_minus_lower_mean_r": _mean_diff(
                upper_stats.get("mean_r"),
                lower_stats.get("mean_r"),
            ),
        }
    )
    if len(pairs) < min_n:
        base["reason"] = "below_min_numeric_n"
    elif len(set(xs)) < 2:
        base["reason"] = "numeric_field_constant"
    else:
        base["reason"] = None
    return base


def build_methodology_gate(diagnostic: Mapping[str, Any]) -> dict[str, Any]:
    """Return a hard suppression block aligned to the Phase 3 protocol."""

    coverage = diagnostic.get("coverage", {})
    target_rows = int(coverage.get("target_available") or 0)
    actual_rows = int(coverage.get("actual_realized_r_available") or 0)
    reasons = [
        "diagnostic_only_not_promotion_evaluation",
        "cpcv_pbo_not_computed",
        "dsr_corrected_p_not_computed",
        "effective_n_not_computed",
        "trial_budget_protected_bundle_level_only",
    ]
    if actual_rows == 0:
        reasons.append("actual_candidate_realized_r_absent")
    if target_rows < 30:
        reasons.append("resolved_target_rows_below_30")
    return {
        "verdict": "SUPPRESSED_DIAGNOSTIC_ONLY",
        "promotion_allowed": False,
        "thresholds": dict(METHODOLOGY_THRESHOLDS),
        "actual_realized_r_rows": actual_rows,
        "target_rows": target_rows,
        "computed": {
            "effective_n": None,
            "pbo": None,
            "dsr_corrected_p": None,
        },
        "reasons": reasons,
    }


def write_diagnostic_json(
    *,
    diagnostic: Mapping[str, Any],
    root: str | Path,
    bundle_id: str,
    label: str,
) -> Path:
    """Write the diagnostic JSON under the ignored external validation tree."""

    stamp = utc_now()
    output_dir = (
        Path(root)
        / "validation"
        / safe_slug(bundle_id)
        / "candidate_join"
        / "diagnostics"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{safe_slug(label)}_{stamp:%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(diagnostic, indent=2, sort_keys=True), encoding="utf-8")
    return path


def render_markdown(diagnostic: Mapping[str, Any]) -> str:
    """Render a compact research note from the diagnostic payload."""

    coverage = diagnostic["coverage"]
    baseline = diagnostic["baseline"]
    gate = diagnostic["methodology_gate"]
    lines = [
        "# Phase 3 Candidate External-Feed Diagnostic",
        "",
        "**Status:** diagnostic only; promotion verdict suppressed.",
        f"**Created UTC:** {diagnostic['created_at_utc']}",
        f"**Input:** `{diagnostic.get('input_path')}`",
        f"**Bundle:** `{diagnostic.get('bundle_id')}`",
        f"**Target:** `{diagnostic.get('target_field')}`",
        "",
        "## Methodology Gate",
        "",
        f"- Verdict: `{gate['verdict']}`",
        f"- Promotion allowed: `{gate['promotion_allowed']}`",
        f"- Actual realized-R rows: {gate['actual_realized_r_rows']}",
        f"- Diagnostic target rows: {gate['target_rows']}",
        "- Required before any alpha claim: DSR-corrected p < 0.01, PBO < 0.4, effective_N >= 3, cumulative trial budget N = 200.",
        f"- Suppression reasons: {', '.join(gate['reasons'])}",
        "",
        "## Coverage",
        "",
        f"- Rows read: {coverage['rows_read']}",
        f"- Target available: {coverage['target_available']}",
        f"- Target missing: {coverage['target_missing']}",
        f"- External validation matched: {coverage['external_validation_matched']}",
        f"- External validation missing: {coverage['external_validation_missing']}",
        "",
        "## Baseline Diagnostic Target",
        "",
        "| n | sum R | mean R | median R | win rate | min R | max R |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        (
            f"| {baseline['n']} | {_fmt(baseline['sum_r'])} | {_fmt(baseline['mean_r'])} "
            f"| {_fmt(baseline['median_r'])} | {_pct(baseline['win_rate'])} "
            f"| {_fmt(baseline['min_r'])} | {_fmt(baseline['max_r'])} |"
        ),
        "",
        "## Source Availability",
        "",
        "| source field | all rows available | target rows available |",
        "|---|---:|---:|",
    ]
    for field, counts in coverage.get("source_availability", {}).items():
        lines.append(
            f"| `{field}` | {counts['all_rows_available']} | {counts['target_rows_available']} |"
        )
    lines.extend(
        [
            "",
            "## Target By Symbol",
            "",
            "| symbol | rows | target n | mean R | win rate |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    symbol_strata = diagnostic.get("categorical_strata", {}).get("symbol", {}).get("groups", {})
    for label, stats in _sorted_groups(symbol_strata):
        lines.append(
            f"| `{label}` | {stats['row_count']} | {stats['n']} | "
            f"{_fmt(stats['mean_r'])} | {_pct(stats['win_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Frozen Numeric Screens",
            "",
            "These are lead-generation diagnostics only. They do not create per-feature alpha claims.",
            "",
            "| field | n | distinct | Spearman r | upper-lower mean R | note |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for field, stats in diagnostic.get("numeric_diagnostics", {}).items():
        lines.append(
            f"| `{field}` | {stats['n']} | {stats.get('x_distinct', 0)} | "
            f"{_fmt(stats.get('spearman_r'))} | {_fmt(stats.get('upper_minus_lower_mean_r'))} "
            f"| {stats.get('reason') or 'eligible'} |"
        )
    lines.extend(
        [
            "",
            "## Readout",
            "",
            "This artifact moves Phase 3 forward by making the candidate-level join evaluable without relaxing the methodology gate. The useful information is coverage, target availability, fold diversity, and frozen-source diagnostic leads. The current artifact is not enough for promotion because actual realized-R is absent and PBO/DSR/effective_N are not computed.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown(path: str | Path, diagnostic: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(diagnostic), encoding="utf-8")
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        help="Candidate join JSONL path. Default: latest candidate join for bundle.",
    )
    parser.add_argument(
        "--root",
        default=str(DEFAULT_EXTERNAL_DATA_ROOT),
        help="External feed cache root (default: data/external).",
    )
    parser.add_argument("--bundle-id", default=DEFAULT_BUNDLE_ID)
    parser.add_argument(
        "--label-contains",
        help="Substring filter when auto-selecting the latest candidate join.",
    )
    parser.add_argument("--target-field", default=DEFAULT_TARGET_FIELD)
    parser.add_argument("--min-numeric-n", type=int, default=8)
    parser.add_argument("--label", default="phase3_candidate_diagnostics_v1")
    parser.add_argument(
        "--write-json",
        action="store_true",
        help="Write JSON diagnostics under data/external/validation.",
    )
    parser.add_argument(
        "--markdown",
        help="Optional committed markdown output path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = (
        Path(args.input)
        if args.input
        else find_latest_candidate_join(
            args.root,
            bundle_id=args.bundle_id,
            label_contains=args.label_contains,
        )
    )
    rows = load_jsonl(input_path)
    diagnostic = build_candidate_diagnostics(
        rows,
        input_path=input_path,
        bundle_id=args.bundle_id,
        target_field=args.target_field,
        min_numeric_n=args.min_numeric_n,
    )
    if args.write_json:
        diagnostic["json_output_path"] = str(
            write_diagnostic_json(
                diagnostic=diagnostic,
                root=args.root,
                bundle_id=args.bundle_id,
                label=args.label,
            )
        )
    if args.markdown:
        diagnostic["markdown_output_path"] = str(write_markdown(args.markdown, diagnostic))
    print(json.dumps(diagnostic, indent=2, sort_keys=True))
    return 0


def _finite_number(value: Any) -> bool:
    number = _as_float(value)
    return number is not None


def _as_float(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _label(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value in (None, ""):
        return "MISSING"
    return str(value)


def _rank(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0 for _ in values]
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    return _pearson(_rank(xs), _rank(ys))


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean = mean(xs)
    y_mean = mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_den = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_den = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    if x_den == 0 or y_den == 0:
        return None
    return numerator / (x_den * y_den)


def _mean_diff(upper: Any, lower: Any) -> float | None:
    upper_value = _as_float(upper)
    lower_value = _as_float(lower)
    if upper_value is None or lower_value is None:
        return None
    return upper_value - lower_value


def _fmt(value: Any) -> str:
    number = _as_float(value)
    if number is None:
        return "n/a"
    return f"{number:.4f}"


def _pct(value: Any) -> str:
    number = _as_float(value)
    if number is None:
        return "n/a"
    return f"{number * 100:.1f}%"


def _sorted_groups(groups: Mapping[str, Mapping[str, Any]]) -> list[tuple[str, Mapping[str, Any]]]:
    return sorted(
        groups.items(),
        key=lambda item: (-(int(item[1].get("n") or 0)), item[0]),
    )


if __name__ == "__main__":
    raise SystemExit(main())
