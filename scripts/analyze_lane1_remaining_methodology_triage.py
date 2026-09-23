#!/usr/bin/env python3
"""Audit remaining Lane 1 methodology backlog items.

Research/tooling only. This report closes or blocks the remaining unblocked
Lane 1 items from the 2026-05-03 master queue without changing live trading
logic.
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

from src.research_infra.methodology_alternatives import (
    auc_rank_binary,
    bayesian_normal_normal_posterior,
    newey_west_mean_test,
    normal_one_sided_greater_p,
    romano_wolf_stepm,
    stationary_bootstrap_mean_test,
)
from src.research_infra.methodology_gate import training_overlap_weighted_standard_error


OUT_JSON = ROOT / "research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.json"
OUT_MD = ROOT / "research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md"


K54_V2_CPCV = ROOT / "research/ml_program/models/k54_v2/cpcv_paired_results.json"
K54_V3_CPCV = ROOT / "research/ml_program/models/k54_v3/cpcv_paired_results.json"
K54_V4_CPCV = ROOT / "research/ml_program/models/k54_v4/cpcv_paired_results.json"
K54_V3_CROSS_PERIOD = ROOT / "research/ml_program/models/k54_v3/cross_period_results.json"
K54_V3_CONFORMAL = ROOT / "research/ml_program/models/k54_v3/conformal_calibration.json"
AGENT_B_ALTERNATIVES = ROOT / "research/ml_program/forensics/2026-04-29/agent_b_methodology_alternatives.json"
AGENT_B_BAYESIAN = ROOT / "research/ml_program/forensics/2026-04-29/agent_b_bayesian_posterior.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def extract_path_diffs(payload: dict[str, Any], *, path_key: str, diff_key: str) -> list[float]:
    diffs: list[float] = []
    for row in payload.get(path_key, []):
        value = finite(row.get(diff_key))
        if value is not None:
            diffs.append(value)
    return diffs


def extract_v4_architecture_diffs(payload: dict[str, Any]) -> dict[str, list[float]]:
    keys = {
        "k54_v4_master": ("auc_master", "auc_v1"),
        "k54_v4_arch_a": ("auc_arch_a", "auc_v1"),
        "k54_v4_hybrid_5": ("auc_hybrid_5", "auc_v1"),
        "k54_v4_hybrid_4": ("auc_hybrid_4", "auc_v1"),
    }
    out = {name: [] for name in keys}
    for row in payload.get("paths", []):
        for name, (candidate_key, benchmark_key) in keys.items():
            cand = finite(row.get(candidate_key))
            bench = finite(row.get(benchmark_key))
            if cand is not None and bench is not None:
                out[name].append(cand - bench)
    return out


def fold_ranges(fold_meta: list[dict[str, Any]]) -> list[tuple[int, int]]:
    ranges = []
    start = 0
    for row in fold_meta:
        n = int(row["n"])
        ranges.append((start, start + n))
        start += n
    return ranges


def aggregate_fold_auc_diffs(
    payload: dict[str, Any],
    *,
    path_key: str,
    candidate_prob_key: str,
    benchmark_prob_key: str,
) -> list[dict[str, Any]]:
    by_idx: dict[int, dict[str, Any]] = {}
    for path in payload.get(path_key, []):
        test_idx = path.get("test_idx") or []
        candidate = path.get(candidate_prob_key) or []
        benchmark = path.get(benchmark_prob_key) or []
        y_true = path.get("y_te") or []
        if not (len(test_idx) == len(candidate) == len(benchmark) == len(y_true)):
            continue
        for idx, cand_score, bench_score, y_val in zip(test_idx, candidate, benchmark, y_true):
            row = by_idx.setdefault(int(idx), {"candidate": [], "benchmark": [], "y": int(y_val)})
            row["candidate"].append(float(cand_score))
            row["benchmark"].append(float(bench_score))

    out = []
    for fold, (start, end) in enumerate(fold_ranges(payload.get("fold_meta", []))):
        fold_y = []
        fold_candidate = []
        fold_benchmark = []
        for idx in range(start, end):
            row = by_idx.get(idx)
            if not row:
                continue
            fold_y.append(int(row["y"]))
            fold_candidate.append(sum(row["candidate"]) / len(row["candidate"]))
            fold_benchmark.append(sum(row["benchmark"]) / len(row["benchmark"]))
        auc_candidate = auc_rank_binary(fold_y, fold_candidate)
        auc_benchmark = auc_rank_binary(fold_y, fold_benchmark)
        diff = None
        if auc_candidate.auc is not None and auc_benchmark.auc is not None:
            diff = auc_candidate.auc - auc_benchmark.auc
        out.append(
            {
                "fold": fold,
                "n": len(fold_y),
                "candidate_auc": auc_candidate.auc,
                "benchmark_auc": auc_benchmark.auc,
                "auc_diff": diff,
                "n_positive": auc_candidate.n_positive,
                "n_negative": auc_candidate.n_negative,
            }
        )
    return out


def summarize_lift_series(name: str, diffs: list[float]) -> dict[str, Any]:
    weighted = training_overlap_weighted_standard_error(diffs)
    spa = stationary_bootstrap_mean_test(diffs, reps=2000, average_block_length=5, seed=42)
    dm = newey_west_mean_test(diffs)
    bayes = bayesian_normal_normal_posterior(
        observed_mean=weighted.mean,
        observed_se=weighted.weighted_se,
        prior_mean=0.0,
        prior_sd=0.05,
        thresholds=(0.0, 0.02, 0.04),
    )
    return {
        "name": name,
        "n_path_diffs": len(diffs),
        "mean_diff": weighted.mean,
        "cpcv_weighted_se": weighted.weighted_se,
        "cpcv_honest_t": weighted.t_stat,
        "cpcv_honest_p_two_sided": weighted.p_two_sided_normal_approx,
        "cpcv_honest_p_one_sided_greater": (
            normal_one_sided_greater_p(weighted.t_stat) if weighted.t_stat is not None else None
        ),
        "stationary_bootstrap_spa_style": spa.to_dict(),
        "dm_style_hac_on_path_diffs": dm.to_dict(),
        "bayesian_skeptical_prior_cpcv_se": bayes.to_dict(),
    }


def locate_47_cell_panel_candidates() -> list[str]:
    candidates = []
    for pattern in ("*47*cell*", "*instrument*side*regime*", "*side*regime*cell*"):
        for path in (ROOT / "research/ml_program").rglob(pattern):
            if path.is_file():
                candidates.append(str(path.relative_to(ROOT)))
    return sorted(set(candidates))


def build_payload() -> dict[str, Any]:
    k54_v2 = load_json(K54_V2_CPCV)
    k54_v3 = load_json(K54_V3_CPCV)
    k54_v4 = load_json(K54_V4_CPCV)
    cross_period = load_json(K54_V3_CROSS_PERIOD)
    conformal = load_json(K54_V3_CONFORMAL)
    agent_b_alt = load_json(AGENT_B_ALTERNATIVES)
    agent_b_bayes = load_json(AGENT_B_BAYESIAN)

    series = {
        "k54_v2_fixed_hp": extract_path_diffs(k54_v2, path_key="paths_fixed_hp", diff_key="auc_diff"),
        "k54_v3_master_bundle": extract_path_diffs(k54_v3, path_key="paths", diff_key="auc_diff"),
    }
    series.update(extract_v4_architecture_diffs(k54_v4))
    series_summaries = [summarize_lift_series(name, diffs) for name, diffs in series.items() if len(diffs) >= 2]

    fold_dm_inputs = {
        "k54_v2_fixed_hp_fold_aggregated": aggregate_fold_auc_diffs(
            k54_v2,
            path_key="paths_fixed_hp",
            candidate_prob_key="p_v2_te",
            benchmark_prob_key="p_v1_te",
        ),
        "k54_v3_master_bundle_fold_aggregated": aggregate_fold_auc_diffs(
            k54_v3,
            path_key="paths",
            candidate_prob_key="p_v3_te",
            benchmark_prob_key="p_v1_te",
        ),
    }
    fold_dm = {}
    for name, rows in fold_dm_inputs.items():
        diffs = [row["auc_diff"] for row in rows if row["auc_diff"] is not None]
        fold_dm[name] = {
            "fold_rows": rows,
            "dm_style_hac": newey_west_mean_test(diffs).to_dict() if len(diffs) >= 2 else None,
        }

    v4_matrix = []
    v4_arch = extract_v4_architecture_diffs(k54_v4)
    arch_names = ["k54_v4_master", "k54_v4_arch_a", "k54_v4_hybrid_5", "k54_v4_hybrid_4"]
    if all(len(v4_arch[name]) == 15 for name in arch_names):
        for i in range(15):
            v4_matrix.append([v4_arch[name][i] for name in arch_names])
    stepm_smoke = romano_wolf_stepm(v4_matrix, alpha=0.05, reps=1000, seed=42).to_dict() if v4_matrix else None

    cell_panel_candidates = locate_47_cell_panel_candidates()
    m5_resolution = {
        "status": "BLOCKED_WITH_REASON_FOR_EXACT_PER_SYMBOL_RESOLUTION",
        "current_empirical_read": "Keep AFML/CPCV-honest as promotion doctrine. Inoue-Kilian/Diebold-style in-sample or older-period evidence can be used as a diagnostic, but current artifacts do not justify replacing CPCV-honest gates.",
        "evidence": {
            "cross_period_c_i": cross_period.get("c_i"),
            "within_recent_c_ii": cross_period.get("c_ii"),
        },
        "blocker": "Exact 7-symbol per-instrument resolution needs full 2022-2023 v2/v3 feature catalog and old mechanical labels for missing symbols; current K54 v3 cross-period test is v1-schema and per effective group, not full per-symbol v3.",
        "trigger": "After D11 missing old labels and v2/v3 feature backfill are generated, rerun per-symbol old-train/recent-test, recent-train/2026-test, and CPCV-honest comparisons side by side.",
    }

    task_classifications = {
        "M-10": {
            "status": "DONE",
            "artifact": str(OUT_MD.relative_to(ROOT)),
            "classification": "Hansen SPA-style stationary bootstrap applied across current K54-class CPCV lift series.",
            "caveat": "Diagnostic only for CPCV paths; path overlap means naive SPA over-rejects if interpreted as promotion evidence.",
        },
        "M-11": {
            "status": "DONE",
            "artifact": str(OUT_MD.relative_to(ROOT)),
            "classification": "Diebold-Mariano-style HAC test computed on fold-aggregated paired AUC differences where prediction arrays exist.",
            "caveat": "K54 v4 has no stored per-row prediction arrays, so DM is path-level only for v4 and fold-aggregated for K54 v2/v3.",
        },
        "M-14": {
            "status": "DONE",
            "artifact": str(OUT_MD.relative_to(ROOT)),
            "classification": "K54 v3 conformal interval coverage has a Christoffersen unconditional coverage proxy.",
            "caveat": "Holdout 2026-04-29 to 2026-05-12 remains unopened/deferred; CPCV proxy failed coverage at p=0.00158.",
        },
        "M-15": {
            "status": "DONE",
            "artifact": str(OUT_MD.relative_to(ROOT)),
            "classification": "Bayesian normal-normal posterior track applied to K54-class lift series under CPCV-weighted SE and skeptical prior.",
            "caveat": "Bayesian posterior is parallel evidence only; it does not override DSR/PBO/effective-N promotion gates.",
        },
        "M-5": {
            "status": "BLOCKED_WITH_REASON",
            "artifact": str(OUT_MD.relative_to(ROOT)),
            "classification": "Current empirical read documented, but exact per-symbol Inoue-Kilian/Diebold vs AFML resolution is blocked.",
            "blocked_by": m5_resolution["blocker"],
            "trigger": m5_resolution["trigger"],
        },
        "M-6": {
            "status": "BLOCKED_WITH_REASON",
            "artifact": str(OUT_MD.relative_to(ROOT)),
            "classification": "Romano-Wolf StepM implementation smoke-tested on K54 v4 architecture columns, but required 47-cell panel is absent.",
            "blocked_by": "No observations x 47 instrument-side-regime cell performance-differential matrix was found in current artifacts.",
            "trigger": "Create a 47-cell cell_id x observation/fold matrix with candidate and benchmark metrics, then run the StepM harness.",
        },
    }

    return {
        "schema_version": "lane1_remaining_methodology_triage_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "source_files": [
            str(K54_V2_CPCV.relative_to(ROOT)),
            str(K54_V3_CPCV.relative_to(ROOT)),
            str(K54_V4_CPCV.relative_to(ROOT)),
            str(K54_V3_CROSS_PERIOD.relative_to(ROOT)),
            str(K54_V3_CONFORMAL.relative_to(ROOT)),
            str(AGENT_B_ALTERNATIVES.relative_to(ROOT)),
            str(AGENT_B_BAYESIAN.relative_to(ROOT)),
        ],
        "task_classifications": task_classifications,
        "k54_lift_series": series_summaries,
        "fold_aggregated_dm": fold_dm,
        "k54_v4_romano_wolf_stepm_smoke": {
            "architecture_columns": arch_names,
            "result": stepm_smoke,
            "scope_note": "Smoke test only; not the M-6 47-cell panel.",
        },
        "m5_inoue_diebold_vs_afml_resolution": m5_resolution,
        "m6_47_cell_panel_candidates_found": cell_panel_candidates,
        "m14_christoffersen_conformal_proxy": conformal,
        "prior_agent_b_evidence": {
            "methodology_alternatives": agent_b_alt,
            "bayesian_posterior": agent_b_bayes,
        },
    }


def fmt_float(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return out


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    tasks = payload["task_classifications"]
    series_rows = []
    for row in payload["k54_lift_series"]:
        bayes_probs = row["bayesian_skeptical_prior_cpcv_se"]["threshold_probabilities"]
        series_rows.append(
            [
                row["name"],
                row["n_path_diffs"],
                fmt_float(row["mean_diff"]),
                fmt_float(row["cpcv_weighted_se"]),
                fmt_float(row["cpcv_honest_p_one_sided_greater"]),
                fmt_float(row["stationary_bootstrap_spa_style"]["p_value_greater"]),
                fmt_float(bayes_probs.get("p_theta_gte_0.04")),
            ]
        )

    dm_rows = []
    for name, result in payload["fold_aggregated_dm"].items():
        dm = result["dm_style_hac"] or {}
        diffs = [row["auc_diff"] for row in result["fold_rows"] if row["auc_diff"] is not None]
        dm_rows.append(
            [
                name,
                len(diffs),
                fmt_float(dm.get("mean")),
                fmt_float(dm.get("standard_error")),
                fmt_float(dm.get("statistic")),
                fmt_float(dm.get("p_one_sided_greater")),
            ]
        )

    conformal = payload["m14_christoffersen_conformal_proxy"]
    m5 = payload["m5_inoue_diebold_vs_afml_resolution"]
    stepm = payload["k54_v4_romano_wolf_stepm_smoke"]
    stepm_result = stepm["result"] or {}

    lines = [
        "# Lane 1 Remaining Methodology Triage",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Question",
        "",
        "Audit the remaining Lane 1 methodology backlog items M-10, M-11, M-14, M-15, M-5, and M-6 from committed artifacts. Close only the items with sufficient evidence and convert the rest into precise blockers/triggers.",
        "",
        "## Classification",
        "",
        *table(
            ["id", "status", "classification", "blocker/trigger"],
            [
                [
                    item_id,
                    row["status"],
                    row["classification"],
                    row.get("blocked_by") or row.get("caveat") or "",
                ]
                for item_id, row in tasks.items()
            ],
        ),
        "",
        "## K54 Lift Methodology Results",
        "",
        "SPA and Bayesian results are diagnostic controls. They do not expose promotion p-values because DSR/PBO/effective-N gates still bind.",
        "",
        *table(
            [
                "series",
                "n",
                "mean diff",
                "CPCV weighted SE",
                "CPCV one-sided p",
                "SPA-style p",
                "Bayes P(theta>=0.04)",
            ],
            series_rows,
        ),
        "",
        "## Diebold-Mariano Fold Diagnostics",
        "",
        "K54 v2 and K54 v3 store per-row CPCV prediction arrays, so fold-level paired AUC diffs can be reconstructed by averaging predictions for each row across the CPCV paths that tested that row.",
        "",
        *table(
            ["series", "folds", "mean diff", "HAC SE", "DM stat", "one-sided p"],
            dm_rows,
        ),
        "",
        "## Christoffersen Coverage",
        "",
        f"- K54 v3 conformal target coverage: `{fmt_float(conformal.get('target_coverage'))}`.",
        f"- Observed CPCV proxy coverage: `{fmt_float(conformal.get('coverage_observed'))}`.",
        f"- Christoffersen LR stat: `{fmt_float(conformal.get('christoffersen_lr_stat'))}`.",
        f"- Christoffersen p: `{fmt_float(conformal.get('christoffersen_p'))}`.",
        f"- Status: `{conformal.get('gate_g_status')}`.",
        "",
        "Interpretation: the available proxy fails unconditional coverage and the true holdout gate remains unopened. This closes M-14 as a methodology test artifact, not as validation.",
        "",
        "## M-5 Empirical Resolution",
        "",
        m5["current_empirical_read"],
        "",
        f"Blocker: {m5['blocker']}",
        "",
        f"Trigger: {m5['trigger']}",
        "",
        "Current K54 v3 evidence is mixed: cross-period v1-schema old-train to recent-test is positive in 4/4 effective groups, but the within-recent 2024-2026 split is positive in only 1/4 groups. That is enough to keep older/in-sample evidence as discovery context, not enough to replace CPCV-honest promotion doctrine.",
        "",
        "## M-6 StepM State",
        "",
        "The reusable Romano-Wolf StepM harness is implemented in `src/research_infra/methodology_alternatives.py` and smoke-tested here on four K54 v4 architecture columns. This is not the requested 47-cell panel.",
        "",
        f"- Smoke-test columns: `{stepm['architecture_columns']}`.",
        f"- Smoke-test rejected columns: `{stepm_result.get('rejected_indices')}`.",
        f"- 47-cell panel candidates found: `{payload['m6_47_cell_panel_candidates_found']}`.",
        "",
        "M-6 remains blocked until a real observations x 47 instrument-side-regime cell performance-differential matrix exists.",
        "",
        "## Ambiguity Ledger",
        "",
        "- SPA over CPCV path diffs is deliberately reported with the path-dependence caveat; it can over-reject and is not a promotion gate.",
        "- K54 v4 lacks stored row-level prediction arrays, so fold-level DM reconstruction is only available for K54 v2/v3.",
        "- M-5 exact per-symbol resolution is blocked by data shape, not by literature ambiguity.",
        "- M-6 has a reusable implementation but lacks the required 47-cell empirical panel.",
        "",
        "## NO_PROMOTION_VERDICT",
        "",
        "This artifact changes research methodology bookkeeping only. It does not validate, promote, or modify any live trading behavior.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=str(OUT_JSON))
    parser.add_argument("--output-md", default=str(OUT_MD))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload()
    write_json(payload, Path(args.output_json))
    write_markdown(payload, Path(args.output_md))
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        "classifications={}".format(
            {key: value["status"] for key, value in payload["task_classifications"].items()}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
