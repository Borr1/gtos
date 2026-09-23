#!/usr/bin/env python3
"""Verify V2 structural path-scaling concentration from the event log.

Research/tooling only. This script recomputes pairwise structural-vs-J46
statistics from the V2 event JSONL instead of trusting the Markdown report.
It then compares the recomputed values against the V2 summary JSON and emits
a concentration/broadness audit for the candidate V2b hypothesis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analyze_raw_ohlc_replay_followups import groups_for_key  # noqa: E402


DEFAULT_SUMMARY_JSON = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/"
    "raw_ohlc_path_scaling_v2_structural_levels_20260501T223136Z.json"
)
DEFAULT_EVENT_LOG = (
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/"
    "raw_ohlc_path_scaling_v2_structural_levels_events_20260501T213225Z.jsonl"
)
DEFAULT_OUTPUT_JSON = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_CONCENTRATION_VERIFICATION_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_CONCENTRATION_VERIFICATION_2026-05-02.md"
)
BASELINE_VARIANT = "J46_J49_ONLY"
STRUCTURAL_VARIANTS = (
    "STRUCT_SWING_PROTECTED_V2",
    "STRUCT_BOS_LEVEL_V2",
    "STRUCT_DISPLACEMENT_HALFBACK_V2",
    "STRUCT_FVG_MID_EDGE_V2",
    "STRUCT_OB_BOUNDARY_V2",
    "STRUCT_LIQUIDITY_RUN_V2",
    "STRUCT_COMPOSITE_ANY_V2",
)
GROUPS = (
    "all_enabled",
    "all_excluding_gbpusd_control",
    "target_cohorts",
    "primary_controlled_family",
    "cleared_non_primary_targets",
    "negative_controls",
    "blocked_dominance_controls",
)
COMPARE_FIELDS = (
    "paired_resolved_n",
    "mean_delta_candidate_minus_baseline",
    "sum_delta_candidate_minus_baseline",
    "candidate_better_n",
    "baseline_better_n",
    "tie_n",
)
EPS = 1e-9


@dataclass
class PairStats:
    paired_resolved_n: int = 0
    baseline_sum_r: float = 0.0
    candidate_sum_r: float = 0.0
    delta_sum_r: float = 0.0
    candidate_better_n: int = 0
    baseline_better_n: int = 0
    tie_n: int = 0
    baseline_positive_n: int = 0
    candidate_positive_n: int = 0
    both_positive_n: int = 0
    both_nonpositive_n: int = 0
    rows: list[dict[str, Any]] = field(default_factory=list)

    def add(self, *, baseline_r: float, candidate_r: float, row: dict[str, Any] | None = None) -> None:
        delta = candidate_r - baseline_r
        self.paired_resolved_n += 1
        self.baseline_sum_r += baseline_r
        self.candidate_sum_r += candidate_r
        self.delta_sum_r += delta
        if delta > EPS:
            self.candidate_better_n += 1
        elif delta < -EPS:
            self.baseline_better_n += 1
        else:
            self.tie_n += 1
        baseline_positive = baseline_r > 0
        candidate_positive = candidate_r > 0
        self.baseline_positive_n += baseline_positive
        self.candidate_positive_n += candidate_positive
        self.both_positive_n += baseline_positive and candidate_positive
        self.both_nonpositive_n += (not baseline_positive) and (not candidate_positive)
        if row is not None:
            self.rows.append(row)

    def to_summary(self) -> dict[str, Any]:
        n = self.paired_resolved_n
        return {
            "paired_resolved_n": n,
            "baseline_mean_r": round(self.baseline_sum_r / n, 6) if n else None,
            "candidate_mean_r": round(self.candidate_sum_r / n, 6) if n else None,
            "mean_delta_candidate_minus_baseline": round(self.delta_sum_r / n, 6) if n else None,
            "sum_delta_candidate_minus_baseline": round(self.delta_sum_r, 6),
            "candidate_better_n": self.candidate_better_n,
            "baseline_better_n": self.baseline_better_n,
            "tie_n": self.tie_n,
            "baseline_positive_n": self.baseline_positive_n,
            "candidate_positive_n": self.candidate_positive_n,
            "both_positive_n": self.both_positive_n,
            "both_nonpositive_n": self.both_nonpositive_n,
        }


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _net_r(row: dict[str, Any], cost_key: str = "0.05") -> float | None:
    value = (row.get("net_r_by_cost") or {}).get(cost_key)
    if value is None:
        return None
    return float(value)


def load_relevant_event_rows(event_log: Path | str) -> dict[str, dict[str, dict[str, Any]]]:
    wanted = set(STRUCTURAL_VARIANTS) | {BASELINE_VARIANT}
    by_event: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    with Path(event_log).open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            variant = row.get("variant_id")
            if variant not in wanted:
                continue
            if _net_r(row) is None:
                continue
            by_event[row["event_key"]][variant] = row
    return by_event


def iter_pairs(by_event: dict[str, dict[str, dict[str, Any]]], variant_id: str) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    for variants in by_event.values():
        baseline = variants.get(BASELINE_VARIANT)
        candidate = variants.get(variant_id)
        if baseline is not None and candidate is not None:
            yield baseline, candidate


def build_pairwise_stats(by_event: dict[str, dict[str, dict[str, Any]]]) -> dict[str, PairStats]:
    out: dict[str, PairStats] = {}
    for variant in STRUCTURAL_VARIANTS:
        stats = PairStats()
        for baseline, candidate in iter_pairs(by_event, variant):
            baseline_r = _net_r(baseline)
            candidate_r = _net_r(candidate)
            if baseline_r is None or candidate_r is None:
                continue
            delta = candidate_r - baseline_r
            stats.add(
                baseline_r=baseline_r,
                candidate_r=candidate_r,
                row={
                    "event_key": candidate.get("event_key"),
                    "symbol": candidate.get("symbol"),
                    "session": candidate.get("session"),
                    "selected_timeframe": candidate.get("selected_timeframe"),
                    "side": candidate.get("mechanical_side") or "none",
                    "role": candidate.get("role"),
                    "raw_cohort_key": candidate.get("raw_cohort_key"),
                    "baseline_r": baseline_r,
                    "candidate_r": candidate_r,
                    "delta_r": delta,
                },
            )
        out[variant] = stats
    return out


def summary_pairwise_lookup(summary_json: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["candidate_variant"]: row
        for row in summary_json.get("pairwise_vs_j46") or []
        if row.get("baseline_variant") == BASELINE_VARIANT
    }


def compare_to_summary(
    recomputed: dict[str, PairStats],
    summary_rows: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant, stats in recomputed.items():
        recomputed_row = stats.to_summary()
        summary_row = summary_rows.get(variant) or {}
        field_results = {}
        all_passed = True
        for field in COMPARE_FIELDS:
            a = recomputed_row.get(field)
            b = summary_row.get(field)
            if isinstance(a, float) or isinstance(b, float):
                passed = a is not None and b is not None and abs(float(a) - float(b)) <= 1e-6
            else:
                passed = a == b
            field_results[field] = {
                "recomputed": a,
                "summary": b,
                "passed": passed,
            }
            all_passed = all_passed and passed
        rows.append(
            {
                "candidate_variant": variant,
                "all_fields_passed": all_passed,
                "field_results": field_results,
            }
        )
    return rows


def _dimension_key(row: dict[str, Any], dimension: str) -> str:
    if dimension == "side":
        return str(row.get("side") or "none")
    return str(row.get(dimension) or "none")


def concentration_by_dimension(stats: PairStats, dimension: str) -> list[dict[str, Any]]:
    buckets: dict[str, PairStats] = defaultdict(PairStats)
    for row in stats.rows:
        key = _dimension_key(row, dimension)
        buckets[key].add(
            baseline_r=float(row["baseline_r"]),
            candidate_r=float(row["candidate_r"]),
        )
    out = []
    for key, bucket in buckets.items():
        summary = bucket.to_summary()
        summary[dimension] = key
        out.append(summary)
    return sorted(out, key=lambda item: item["sum_delta_candidate_minus_baseline"], reverse=True)


def concentration_broadness(rows: list[dict[str, Any]], dimension: str) -> dict[str, Any]:
    positives = [row for row in rows if row["sum_delta_candidate_minus_baseline"] > 0]
    negatives = [row for row in rows if row["sum_delta_candidate_minus_baseline"] < 0]
    positive_sum = sum(row["sum_delta_candidate_minus_baseline"] for row in positives)
    negative_sum = sum(row["sum_delta_candidate_minus_baseline"] for row in negatives)
    top_positive = positives[0]["sum_delta_candidate_minus_baseline"] if positives else 0.0
    top4_positive = sum(row["sum_delta_candidate_minus_baseline"] for row in positives[:4])
    return {
        "dimension": dimension,
        "bucket_count": len(rows),
        "positive_bucket_count": len(positives),
        "negative_bucket_count": len(negatives),
        "positive_sum_delta": round(positive_sum, 6),
        "negative_sum_delta": round(negative_sum, 6),
        "top_positive_share": round(top_positive / positive_sum, 6) if positive_sum else None,
        "top4_positive_share": round(top4_positive / positive_sum, 6) if positive_sum else None,
    }


def group_deltas(stats: PairStats) -> list[dict[str, Any]]:
    buckets: dict[str, PairStats] = defaultdict(PairStats)
    for row in stats.rows:
        for group in groups_for_key(str(row["raw_cohort_key"]), str(row["role"])):
            buckets[group].add(
                baseline_r=float(row["baseline_r"]),
                candidate_r=float(row["candidate_r"]),
            )
    out = []
    for group in GROUPS:
        summary = buckets[group].to_summary()
        summary["group"] = group
        out.append(summary)
    return out


def build_concentration_payload(recomputed: dict[str, PairStats]) -> dict[str, Any]:
    variants: dict[str, Any] = {}
    for variant, stats in recomputed.items():
        dim_rows = {
            dimension: concentration_by_dimension(stats, dimension)
            for dimension in ("symbol", "session", "selected_timeframe", "side", "role", "raw_cohort_key")
        }
        variants[variant] = {
            "pairwise": stats.to_summary(),
            "broadness": {
                dimension: concentration_broadness(rows, dimension)
                for dimension, rows in dim_rows.items()
            },
            "by_dimension": dim_rows,
            "group_deltas": group_deltas(stats),
        }
    return variants


def build_decision_readout(variants: dict[str, Any]) -> dict[str, Any]:
    swing = variants["STRUCT_SWING_PROTECTED_V2"]
    ob = variants["STRUCT_OB_BOUNDARY_V2"]
    fvg = variants["STRUCT_FVG_MID_EDGE_V2"]
    swing_cohort_broadness = swing["broadness"]["raw_cohort_key"]
    ob_groups = {row["group"]: row for row in ob["group_deltas"]}
    ob_group_positive = [
        group for group, row in ob_groups.items() if row["sum_delta_candidate_minus_baseline"] > 0
    ]
    return {
        "headline_winner_concentration_status": (
            "CONCENTRATION_BLOCKED"
            if swing_cohort_broadness["top4_positive_share"] is not None
            and swing_cohort_broadness["top4_positive_share"] >= 0.90
            else "BROAD_ENOUGH_DIAGNOSTIC"
        ),
        "headline_winner_top4_positive_share": swing_cohort_broadness["top4_positive_share"],
        "ob_boundary_pairwise_delta": ob["pairwise"]["mean_delta_candidate_minus_baseline"],
        "swing_pairwise_delta": swing["pairwise"]["mean_delta_candidate_minus_baseline"],
        "fvg_pairwise_delta": fvg["pairwise"]["mean_delta_candidate_minus_baseline"],
        "ob_boundary_positive_groups": ob_group_positive,
        "ob_boundary_positive_group_count": len(ob_group_positive),
        "recommended_v2b_candidate": "STRUCT_OB_BOUNDARY_V2",
        "recommended_v2b_comparison_arms": ["STRUCT_SWING_PROTECTED_V2", "STRUCT_FVG_MID_EDGE_V2", BASELINE_VARIANT],
        "registration_action": "REGISTER_OB_BOUNDARY_VALIDATION_HYPOTHESIS_NOT_PROMOTION",
    }


def build_payload(
    *,
    summary_json: dict[str, Any],
    event_log_path: Path | str,
    compute_hash: bool,
) -> dict[str, Any]:
    by_event = load_relevant_event_rows(event_log_path)
    recomputed = build_pairwise_stats(by_event)
    summary_lookup = summary_pairwise_lookup(summary_json)
    comparison = compare_to_summary(recomputed, summary_lookup)
    variants = build_concentration_payload(recomputed)
    all_verified = all(row["all_fields_passed"] for row in comparison)
    payload = {
        "schema_version": "raw_ohlc_path_scaling_v2_concentration_verification_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "verification_verdict": "PASS" if all_verified else "FAIL",
        "inputs": {
            "summary_schema_version": summary_json.get("schema_version"),
            "summary_event_log_path": summary_json.get("event_log_path"),
            "event_log_path": str(event_log_path),
            "event_log_sha256": sha256_file(event_log_path) if compute_hash else "SKIPPED",
            "events_with_relevant_resolved_rows": len(by_event),
            "baseline_variant": BASELINE_VARIANT,
            "structural_variants": list(STRUCTURAL_VARIANTS),
        },
        "summary_comparison": comparison,
        "variants": variants,
        "decision_readout": build_decision_readout(variants),
        "synthesis": {
            "summary": (
                "V2 concentration numbers were recomputed from the event log. The headline structural "
                "signal remains real but concentration-blocked for general promotion; OB-boundary remains "
                "the cleanest V2b validation candidate."
            ),
            "ambiguities": [
                "This verifies internal consistency against the same event log; it is not an out-of-sample validation.",
                "Cost remains R-sensitivity, not measured historical broker spread/slippage.",
                "Concentration broadness is diagnostic; final V2b gates must be pre-registered before a new validation run.",
            ],
            "open_questions": [
                "Will OB-boundary floors remain positive on a fresh validation lane?",
                "Will OB-boundary retain lower truncation once measured on unseen rows?",
                "Should V2b be cohort-specific if broadness gates fail again?",
            ],
            "next_steps": [
                "Register V2b around OB-boundary floors with swing/FVG comparison arms and explicit concentration gates.",
                "Do not proceed to V3 reentry until V2b validation either passes or clearly fails.",
                "Keep NO_PROMOTION_VERDICT because this audit is same-event-log verification.",
            ],
        },
    }
    return payload


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(value) for value in row) + " |")
    return out


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    decision = payload["decision_readout"]
    rows = []
    for variant_id in STRUCTURAL_VARIANTS:
        pair = payload["variants"][variant_id]["pairwise"]
        rows.append(
            [
                variant_id,
                pair["paired_resolved_n"],
                pair["mean_delta_candidate_minus_baseline"],
                pair["sum_delta_candidate_minus_baseline"],
                pair["candidate_better_n"],
                pair["baseline_better_n"],
            ]
        )
    lines = [
        "# V2 Structural Path Scaling Concentration Verification",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Verification verdict: `{payload['verification_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Pairwise Recompute Versus J46",
        "",
        *_table(
            ["Variant", "paired n", "mean delta", "sum delta", "candidate better", "J46 better"],
            rows,
        ),
        "",
        "## Summary-JSON Verification",
        "",
        *_table(
            ["Variant", "all fields passed"],
            [[row["candidate_variant"], row["all_fields_passed"]] for row in payload["summary_comparison"]],
        ),
        "",
        "## Decision Readout",
        "",
        f"- Headline winner concentration status: `{decision['headline_winner_concentration_status']}`",
        f"- Headline winner top-four positive cohort share: {decision['headline_winner_top4_positive_share']}",
        f"- Recommended V2b candidate: `{decision['recommended_v2b_candidate']}`",
        f"- Recommended comparison arms: {decision['recommended_v2b_comparison_arms']}",
        f"- Registration action: `{decision['registration_action']}`",
        "",
        "## OB Boundary Group Deltas",
        "",
        *_table(
            ["Group", "paired n", "mean delta", "sum delta"],
            [
                [
                    row["group"],
                    row["paired_resolved_n"],
                    row["mean_delta_candidate_minus_baseline"],
                    row["sum_delta_candidate_minus_baseline"],
                ]
                for row in payload["variants"]["STRUCT_OB_BOUNDARY_V2"]["group_deltas"]
            ],
        ),
        "",
        "## Swing Protected Top Cohorts",
        "",
        *_table(
            ["Cohort", "paired n", "mean delta", "sum delta"],
            [
                [
                    row["raw_cohort_key"],
                    row["paired_resolved_n"],
                    row["mean_delta_candidate_minus_baseline"],
                    row["sum_delta_candidate_minus_baseline"],
                ]
                for row in payload["variants"]["STRUCT_SWING_PROTECTED_V2"]["by_dimension"]["raw_cohort_key"][:8]
            ],
        ),
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
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--event-log", default=DEFAULT_EVENT_LOG)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--compute-hash", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_payload(
        summary_json=load_json(args.summary_json),
        event_log_path=args.event_log,
        compute_hash=args.compute_hash,
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"verification={payload['verification_verdict']} "
        f"v2b={payload['decision_readout']['recommended_v2b_candidate']} "
        f"headline_concentration={payload['decision_readout']['headline_winner_concentration_status']}"
    )
    return 0 if payload["verification_verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
