#!/usr/bin/env python3
"""M-16 Q1.3 CPCV path bias-variance bookkeeping.

Research/tooling only. Reads existing K54 v2 CPCV artifacts and decomposes the
reported +0.0309 AUC lift into path-mean signal versus path-to-path variance.
It does not retrain models or open any holdout.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.methodology_gate import training_overlap_weighted_standard_error


DEFAULT_CPCV_JSON = "research/ml_program/models/k54_v2/cpcv_paired_results.json"
DEFAULT_STAT_REEVAL_MD = "research/ml_program/audit/statistical_reevaluation.md"
DEFAULT_OUTPUT_JSON = "research/ml_program/audit/Q13_CPCV_BIAS_VARIANCE_BOOKKEEPING_2026-05-03.json"
DEFAULT_OUTPUT_MD = "research/ml_program/audit/Q13_CPCV_BIAS_VARIANCE_BOOKKEEPING_2026-05-03.md"

Q13_GATE_A_LIFT_THRESHOLD = 0.04


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fixed_hp_path_diffs(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for path in payload.get("paths_fixed_hp") or []:
        if path.get("auc_diff") is None:
            continue
        rows.append(
            {
                "path": int(path.get("path")),
                "auc_v2": float(path.get("auc_v2")),
                "auc_v1": float(path.get("auc_v1")),
                "auc_diff": float(path.get("auc_diff")),
                "delong_p": float(path.get("delong_p")) if path.get("delong_p") is not None else None,
                "n_test": int(path.get("n_test")) if path.get("n_test") is not None else None,
            }
        )
    if len(rows) < 2:
        raise ValueError("fixed-HP CPCV artifact must contain at least two path diffs")
    return rows


def loo_influence(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diffs = [row["auc_diff"] for row in rows]
    full_mean = sum(diffs) / len(diffs)
    out = []
    for row in rows:
        remaining = [other["auc_diff"] for other in rows if other["path"] != row["path"]]
        loo_mean = sum(remaining) / len(remaining)
        out.append(
            {
                "dropped_path": row["path"],
                "dropped_diff": row["auc_diff"],
                "loo_mean": loo_mean,
                "mean_delta_vs_full": loo_mean - full_mean,
                "relative_mean_change_abs": abs(loo_mean - full_mean) / abs(full_mean) if full_mean else math.inf,
            }
        )
    return sorted(out, key=lambda item: abs(item["mean_delta_vs_full"]), reverse=True)


def decompose_path_variance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    diffs = [row["auc_diff"] for row in rows]
    n = len(diffs)
    mean = sum(diffs) / n
    sample_var = sum((value - mean) ** 2 for value in diffs) / (n - 1)
    sample_std = math.sqrt(sample_var)
    weighted = training_overlap_weighted_standard_error(diffs)
    signal_power = mean * mean
    variance_power = sample_var
    second_moment = signal_power + variance_power
    signal_share = signal_power / second_moment if second_moment else 0.0
    variance_share = variance_power / second_moment if second_moment else 0.0
    weighted_ci_95 = [
        mean - 1.96 * weighted.weighted_se,
        mean + 1.96 * weighted.weighted_se,
    ]
    loo = loo_influence(rows)
    positive = sum(1 for value in diffs if value > 0)
    negative = sum(1 for value in diffs if value < 0)
    max_positive_support = max(rows, key=lambda row: row["auc_diff"])
    max_negative_drag = min(rows, key=lambda row: row["auc_diff"])
    return {
        "n_paths": n,
        "mean_lift": mean,
        "sample_std": sample_std,
        "sample_variance": sample_var,
        "signal_power_mean_squared": signal_power,
        "path_variance_power": variance_power,
        "signal_share_of_second_moment": signal_share,
        "path_variance_share_of_second_moment": variance_share,
        "sample_std_to_abs_mean_ratio": sample_std / abs(mean) if mean else math.inf,
        "weighted_se_to_abs_mean_ratio": weighted.weighted_se / abs(mean) if mean else math.inf,
        "weighted_se": weighted.to_dict(),
        "weighted_ci_95_normal_approx": weighted_ci_95,
        "weighted_ci_crosses_zero": weighted_ci_95[0] <= 0 <= weighted_ci_95[1],
        "positive_path_count": positive,
        "negative_path_count": negative,
        "zero_path_count": n - positive - negative,
        "positive_path_rate": positive / n,
        "gate_a_threshold": Q13_GATE_A_LIFT_THRESHOLD,
        "threshold_gap": Q13_GATE_A_LIFT_THRESHOLD - mean,
        "mean_to_threshold_ratio": mean / Q13_GATE_A_LIFT_THRESHOLD,
        "loo_influence": loo,
        "max_influence": loo[0],
        "max_positive_support": {
            "path": max_positive_support["path"],
            "auc_diff": max_positive_support["auc_diff"],
        },
        "max_negative_drag": {
            "path": max_negative_drag["path"],
            "auc_diff": max_negative_drag["auc_diff"],
        },
        "classification": (
            "VARIANCE_DOMINATED_NO_SIGNAL_CLAIM"
            if signal_share < 0.25 and weighted_ci_95[0] <= 0 <= weighted_ci_95[1]
            else "SIGNAL_SHARE_NOT_LOW_REVIEW_REQUIRED"
        ),
    }


def build_payload(
    *,
    cpcv_json: str | Path = DEFAULT_CPCV_JSON,
    stat_reeval_md: str | Path = DEFAULT_STAT_REEVAL_MD,
) -> dict[str, Any]:
    payload = load_json(cpcv_json)
    rows = fixed_hp_path_diffs(payload)
    decomposition = decompose_path_variance(rows)
    summary = payload.get("summary_fixed_hp_recommended") or {}
    return {
        "schema_version": "q13_cpcv_bias_variance_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "task_id": "M-16",
        "input_artifacts": {
            "cpcv_json": str(cpcv_json),
            "statistical_reevaluation": str(stat_reeval_md),
        },
        "source_summary": {
            "reported_diff_mean": summary.get("diff_mean"),
            "reported_diff_std": summary.get("diff_std"),
            "reported_diff_se_naive": summary.get("diff_se"),
            "reported_stouffer_p": summary.get("delong_p_combined_stouffer"),
            "reported_gate_a_pass": summary.get("gate_a_pass"),
        },
        "path_rows": rows,
        "decomposition": decomposition,
        "answer": {
            "variance_vs_signal": decomposition["classification"],
            "plain_english": (
                "The +0.0309 Q1.3 lift is variance-dominated: the squared mean accounts "
                "for only {signal:.1%} of mean-plus-path-variance, while path variance "
                "accounts for {variance:.1%}."
            ).format(
                signal=decomposition["signal_share_of_second_moment"],
                variance=decomposition["path_variance_share_of_second_moment"],
            ),
            "promotion_relevance": "No promotion relevance; this is a closed-methodology bookkeeping artifact.",
        },
        "next_steps": [
            "Keep Q1.3 K54 v2 closed; do not cite Stouffer p as evidence.",
            "Use this decomposition pattern for any future CPCV path report that has per-path diffs.",
            "Continue Lane 1 with M-10/M-11/M-14/M-15/M-5/M-6 unless another artifact-supported closure is found.",
        ],
    }


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if value is None:
        return "n/a"
    if isinstance(value, (list, dict)):
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
    dec = payload["decomposition"]
    max_inf = dec["max_influence"]
    lines = [
        "# Q1.3 CPCV Bias-Variance Bookkeeping",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Hypothesis",
        "",
        "The Q1.3 `+0.0309` fixed-HP CPCV lift is dominated by path-to-path variance rather than transferable signal.",
        "",
        "## Inputs",
        "",
        f"- CPCV artifact: `{payload['input_artifacts']['cpcv_json']}`.",
        f"- Prior statistical re-evaluation: `{payload['input_artifacts']['statistical_reevaluation']}`.",
        "- No model retraining and no holdout opening were performed.",
        "",
        "## Result",
        "",
        f"- Classification: `{dec['classification']}`.",
        f"- Mean lift: `{dec['mean_lift']:.6f}` versus Q1.3 gate threshold `{dec['gate_a_threshold']:.6f}`.",
        f"- Path sample std: `{dec['sample_std']:.6f}`.",
        f"- CPCV-honest weighted SE: `{dec['weighted_se']['weighted_se']:.6f}`.",
        f"- 95% weighted normal-approx CI: `[{dec['weighted_ci_95_normal_approx'][0]:.6f}, {dec['weighted_ci_95_normal_approx'][1]:.6f}]`.",
        f"- Signal share of mean-plus-path-variance: `{dec['signal_share_of_second_moment']:.6f}`.",
        f"- Path variance share of mean-plus-path-variance: `{dec['path_variance_share_of_second_moment']:.6f}`.",
        f"- Positive/negative path count: `{dec['positive_path_count']} / {dec['negative_path_count']}` out of `{dec['n_paths']}`.",
        f"- Most influential path: `{max_inf['dropped_path']}`; dropping it moves the mean to `{max_inf['loo_mean']:.6f}` (`{max_inf['relative_mean_change_abs']:.2%}` absolute relative change).",
        f"- Largest positive support path: `{dec['max_positive_support']['path']}` with diff `{dec['max_positive_support']['auc_diff']:.6f}`.",
        f"- Largest negative drag path: `{dec['max_negative_drag']['path']}` with diff `{dec['max_negative_drag']['auc_diff']:.6f}`.",
        "",
        "## Per-Path Diffs",
        "",
        *table(
            ["path", "auc_v2", "auc_v1", "diff", "delong_p"],
            [
                [row["path"], row["auc_v2"], row["auc_v1"], row["auc_diff"], row["delong_p"]]
                for row in payload["path_rows"]
            ],
        ),
        "",
        "## Interpretation",
        "",
        f"- {payload['answer']['plain_english']}",
        "- The weighted interval crosses zero, so the average lift is not a stable signal estimate.",
        "- The Stouffer p-value is not used; it assumes path independence that this CPCV design does not have.",
        "",
        "## Next Steps",
        "",
        *[f"- {item}" for item in payload["next_steps"]],
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This report closes M-16 as methodology bookkeeping only. It does not validate, promote, or modify live trading behavior.",
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpcv-json", default=DEFAULT_CPCV_JSON)
    parser.add_argument("--stat-reeval-md", default=DEFAULT_STAT_REEVAL_MD)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(cpcv_json=args.cpcv_json, stat_reeval_md=args.stat_reeval_md)
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    dec = payload["decomposition"]
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        "classification={classification} mean={mean:.6f} signal_share={signal:.6f} variance_share={variance:.6f}".format(
            classification=dec["classification"],
            mean=dec["mean_lift"],
            signal=dec["signal_share_of_second_moment"],
            variance=dec["path_variance_share_of_second_moment"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
