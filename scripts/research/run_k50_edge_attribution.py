#!/usr/bin/env python3
"""Run K50 — Causal Edge Attribution (F16: proper SHAP + Bonferroni + bootstrap CI).

Pure-Python CLI that:
  1. Loads filled trades from canonical sources:
       - ``knowledge_base/index/_trade_index.json`` (legacy session-simulator
         batch, n=129 as of 2026-04-26).
       - Optional ``--unified-csv`` (e.g.
         ``research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv``)
         to widen the population to ~150 trades with extra columns.
       - Optional ``--symbols``: filter the loaded trades.
  2. Builds a feature matrix (8 features) and realised-R target.
  3. Trains a gradient-boosting regressor (LightGBM if installed, else
     sklearn).
  4. Computes **proper-SHAP** attribution with bootstrap 95% CI (under
     the F16 update). Falls back to permutation-importance when the
     SHAP path is unavailable, but ``--method shap`` forces SHAP and
     errors if it cannot run.
  5. Splits the trade set into H1 (chronological first half) and H2
     (chronological second half) and runs a **Bonferroni-corrected**
     one-sided Welch's t-test on the per-feature mean |SHAP| H1-vs-H2
     bootstrap distributions. ``family_size = len(FEATURE_NAMES) = 8``.
     Surface decayed features per the corrected p-values.
  6. Runs Bayesian linear regression as a sanity check.
  7. Writes ``shap_values.json`` (per-trade SHAP rows + per-feature
     bootstrap CI), ``ranking.json`` (rankings + CI + H1/H2 importance
     test results) and ``report.md`` (verdict block + comparison
     table). The default output directory is
     ``research/edge_decomposition/K50_attribution_proper_shap/``.
  8. If the sibling directory
     ``research/edge_decomposition/K50_attribution/ranking.json`` exists,
     auto-generates ``comparison.md`` (proper SHAP vs original
     permutation).

No AI calls. Read-only on the trade-index sources; writes only inside the
chosen ``--output-dir``.

Usage::

    python scripts/research/run_k50_edge_attribution.py \\
        --output-dir research/edge_decomposition/K50_attribution_proper_shap \\
        --method shap \\
        --alpha 0.05 \\
        --bootstrap-n-resamples 100 \\
        --symbols XAUUSD
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research_infra.edge_attribution import (  # noqa: E402
    AttributionReport,
    AttributionWithCI,
    FEATURE_NAMES,
    FeatureCI,
    FeatureImportanceTest,
    bayesian_linear_attribution,
    build_feature_matrix,
    compute_shap_attribution,
    compute_shap_attribution_with_ci,
    h1_h2_importance_test,
    spearman_rank_delta,
    train_gbm_regressor,
    _shap_available,
)


DEFAULT_OUTPUT_DIR = (
    ROOT / "research" / "edge_decomposition" / "K50_attribution_proper_shap"
)
DEFAULT_TRADE_INDEX = ROOT / "knowledge_base" / "index" / "_trade_index.json"
DEFAULT_UNIFIED_CSV = (
    ROOT / "research" / "b_deep_audit_2026-04-19" / "phase1"
    / "_delta_scratch" / "trades_unified.csv"
)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _load_trade_index(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    trades = data.get("trades", []) if isinstance(data, dict) else []
    return [t for t in trades if isinstance(t, dict)]


def _load_unified_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _filter_symbols(trades: list[dict], symbols: Iterable[str] | None) -> list[dict]:
    if not symbols:
        return trades
    requested = {s.strip().upper() for s in symbols if s.strip()}
    return [t for t in trades if str(t.get("symbol", "")).upper() in requested]


def _merge_unique(primary: list[dict], secondary: list[dict]) -> list[dict]:
    """Merge unique by ``trade_id`` (primary wins ties)."""
    seen: set[str] = set()
    out: list[dict] = []
    for t in primary:
        tid = str(t.get("trade_id", ""))
        if tid and tid in seen:
            continue
        if tid:
            seen.add(tid)
        out.append(t)
    for t in secondary:
        tid = str(t.get("trade_id", ""))
        if tid and tid in seen:
            continue
        if tid:
            seen.add(tid)
        out.append(t)
    return out


def _split_chronological_halves(trades: list[dict]) -> tuple[list[dict], list[dict]]:
    """Sort trades chronologically and split at the midpoint.

    Falls back to lexicographic sort on the date-like field if no
    parsing helper is available.
    """
    sortable = []
    for t in trades:
        date = (
            t.get("date")
            or t.get("candle_close_time")
            or t.get("entry_time")
            or ""
        )
        sortable.append((str(date), t))
    sortable.sort(key=lambda kv: kv[0])
    half = len(sortable) // 2
    h1 = [t for _, t in sortable[:half]]
    h2 = [t for _, t in sortable[half:]]
    return h1, h2


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _write_shap_values(
    out_dir: Path,
    report: AttributionReport,
    cis: tuple[FeatureCI, ...],
    trade_ids: list[str],
    *,
    bootstrap_n_resamples: int,
    ci_alpha: float,
    method_requested: str,
) -> Path:
    rows = []
    for i, tid in enumerate(trade_ids):
        row = {"trade_id": tid}
        for j, fn in enumerate(report.feature_names):
            row[fn] = float(report.shap_values[i, j])
        rows.append(row)
    ci_block = {
        fc.feature: {
            "point": fc.point,
            "ci_low": fc.ci_low,
            "ci_high": fc.ci_high,
            "n_resamples": fc.n_resamples,
        }
        for fc in cis
    }
    payload = {
        "method_requested": method_requested,
        "method_used": report.method,
        "shap_available": _shap_available(),
        "base_value": report.base_value,
        "feature_names": list(report.feature_names),
        "n_samples": report.n_samples,
        "bootstrap_n_resamples": bootstrap_n_resamples,
        "ci_alpha": ci_alpha,
        "feature_ci": ci_block,
        "rows": rows,
    }
    out = out_dir / "shap_values.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def _write_ranking(
    out_dir: Path,
    report: AttributionReport,
    cis: tuple[FeatureCI, ...],
    bayes: dict,
    delta: dict,
    h1_h2_tests: tuple[FeatureImportanceTest, ...] | None,
    *,
    bootstrap_n_resamples: int,
    ci_alpha: float,
    alpha: float,
    method_requested: str,
) -> Path:
    rankings = [
        {
            "feature": r.feature,
            "rank": r.rank,
            "mean_abs_shap": r.mean_abs_shap,
            "mean_shap": r.mean_shap,
            "relative_importance": r.relative_importance,
        }
        for r in report.rankings
    ]
    ci_by_feat = {
        fc.feature: {
            "point": fc.point,
            "ci_low": fc.ci_low,
            "ci_high": fc.ci_high,
            "n_resamples": fc.n_resamples,
        }
        for fc in cis
    }
    h1_h2_payload: list[dict] | None = None
    if h1_h2_tests is not None:
        h1_h2_payload = [
            {
                "feature": t.feature,
                "h1_importance": t.h1_importance,
                "h2_importance": t.h2_importance,
                "delta": t.delta,
                "raw_p": t.raw_p if math.isfinite(t.raw_p) else None,
                "bonferroni_p": (
                    t.bonferroni_p if math.isfinite(t.bonferroni_p) else None
                ),
                "survives_bonferroni": t.survives_bonferroni,
                "family_size": t.family_size,
            }
            for t in h1_h2_tests
        ]
    payload = {
        "method_requested": method_requested,
        "shap_method_used": report.method,
        "shap_available": _shap_available(),
        "alpha": alpha,
        "bootstrap_n_resamples": bootstrap_n_resamples,
        "ci_alpha": ci_alpha,
        "shap_rankings": rankings,
        "feature_ci": ci_by_feat,
        "h1_h2_importance_test": h1_h2_payload,
        "bayesian_posterior_mean": bayes["posterior_mean"],
        "bayesian_posterior_std": bayes["posterior_std"],
        "bayesian_raw_space_mean": bayes["raw_space_mean"],
        "bayesian_rank_by_abs_mean": bayes["rank_by_abs_mean"],
        "bayesian_intercept": bayes["intercept"],
        "bayesian_noise_variance_mode": bayes["noise_variance_mode"],
        "n_samples": bayes["n_samples"],
        "rank_correlation_shap_vs_bayesian": delta,
    }
    out = out_dir / "ranking.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def _format_p(p: float | None) -> str:
    if p is None or not isinstance(p, float) or not math.isfinite(p):
        return "—"
    if p < 1e-4:
        return f"{p:.2e}"
    return f"{p:.4f}"


def _format_pct(x: float | None) -> str:
    if x is None or not isinstance(x, float) or not math.isfinite(x):
        return "—"
    return f"{x * 100:+.1f}%"


def _format_imp(x: float) -> str:
    if not math.isfinite(x):
        return "—"
    return f"{x:.4f}"


def _format_ci(lo: float, hi: float) -> str:
    if not math.isfinite(lo) or not math.isfinite(hi):
        return "—"
    return f"[{lo:.4f}, {hi:.4f}]"


def _write_report_md(
    out_dir: Path,
    report: AttributionReport,
    cis: tuple[FeatureCI, ...],
    bayes: dict,
    delta: dict,
    h1_h2_tests: tuple[FeatureImportanceTest, ...] | None,
    *,
    n_input: int,
    n_filled: int,
    sources: list[str],
    symbols_filter: tuple[str, ...] | None,
    alpha: float,
    method_requested: str,
    bootstrap_n_resamples: int,
    ci_alpha: float,
    h1_n: int | None,
    h2_n: int | None,
) -> Path:
    lines: list[str] = []
    lines.append("# K50 — Causal Edge Attribution (F16: proper SHAP + Bonferroni + bootstrap CI)\n")
    lines.append(
        f"- **Method requested**: `{method_requested}`  \n"
        f"- **Method used**: `{report.method}`  \n"
        f"- **SHAP available**: `{_shap_available()}`  \n"
        f"- **Samples (filled trades)**: {report.n_samples}  \n"
        f"- **Sources**: {', '.join(sources) or 'none'}  \n"
        f"- **Symbol filter**: {','.join(symbols_filter) if symbols_filter else 'none (all)'}  \n"
        f"- **Input trades read**: {n_input} (filled = {n_filled})  \n"
        f"- **Bonferroni alpha**: {alpha:.3f} | family size: {len(report.feature_names)}  \n"
        f"- **Bootstrap resamples**: {bootstrap_n_resamples} | CI alpha: {ci_alpha:.3f}\n"
    )

    # Edge component ranking table — with bootstrap CI
    lines.append("\n## Edge Component Ranking (mean |SHAP| with bootstrap CI)\n")
    lines.append(
        "| Feature | mean \\|SHAP\\| | mean SHAP | relative importance | "
        "bootstrap CI | Bayesian rank |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|")
    bay_rank_map = {f: i + 1 for i, f in enumerate(bayes["rank_by_abs_mean"])}
    ci_by_feat = {fc.feature: fc for fc in cis}
    for r in report.rankings:
        bay_rank = bay_rank_map.get(r.feature, "-")
        fc = ci_by_feat.get(r.feature)
        ci_str = _format_ci(fc.ci_low, fc.ci_high) if fc else "—"
        lines.append(
            f"| {r.feature} | {r.mean_abs_shap:.4f} | {r.mean_shap:+.4f} | "
            f"{r.relative_importance * 100:.1f}% | {ci_str} | {bay_rank} |"
        )

    # H1 vs H2 importance-delta — Bonferroni
    if h1_h2_tests is not None:
        lines.append("\n## H1 vs H2 importance-delta test (Bonferroni-corrected)\n")
        lines.append(
            f"H1 / H2 sample sizes: **{h1_n} / {h2_n}** filled trades. "
            f"One-sided Welch's t-test on bootstrap distributions of mean |SHAP| "
            f"(H0: H1 ≤ H2). Bonferroni family size = {len(report.feature_names)}, "
            f"α = {alpha:.3f}. Bootstrap resamples per half: "
            f"{bootstrap_n_resamples}.\n"
        )
        lines.append("| Feature | H1 |SHAP| | H2 |SHAP| | delta | raw p | bonf p | status |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for t in h1_h2_tests:
            if t.survives_bonferroni and t.delta > 0:
                status = "DECAYED"
            elif (
                isinstance(t.bonferroni_p, float)
                and math.isfinite(t.bonferroni_p)
                and t.bonferroni_p < alpha
                and t.delta < 0
            ):
                status = "newly important"
            elif t.delta > 0 and (
                not isinstance(t.bonferroni_p, float)
                or not math.isfinite(t.bonferroni_p)
                or t.bonferroni_p >= alpha
            ):
                status = "suggestive"
            else:
                status = "stable"
            lines.append(
                f"| {t.feature} | {_format_imp(t.h1_importance)} | "
                f"{_format_imp(t.h2_importance)} | "
                f"{(t.delta):+.4f} | "
                f"{_format_p(t.raw_p)} | "
                f"{_format_p(t.bonferroni_p)} | {status} |"
            )
        lines.append("")

    # Bayesian table
    lines.append("\n## Bayesian Posterior (standardised coefficients)\n")
    lines.append("| Feature | posterior mean | posterior std | raw-space coef |")
    lines.append("|---|---:|---:|---:|")
    for f in bayes["rank_by_abs_mean"]:
        lines.append(
            f"| {f} | {bayes['posterior_mean'][f]:+.4f} | "
            f"{bayes['posterior_std'][f]:.4f} | "
            f"{bayes['raw_space_mean'][f]:+.4f} |"
        )

    # Strategic verdict
    lines.append("\n## Strategic verdict\n")
    if report.rankings:
        top = report.rankings[0]
        lines.append(
            f"- **Top R contributor (proper SHAP)**: `{top.feature}` "
            f"({top.relative_importance * 100:.1f}% of total |SHAP| mass)"
        )
        signed_sorted = sorted(report.rankings, key=lambda r: r.mean_shap)
        if signed_sorted and signed_sorted[0].mean_shap < 0:
            neg = signed_sorted[0]
            lines.append(
                f"- **Top negative contributor**: `{neg.feature}` "
                f"(mean SHAP {neg.mean_shap:+.4f})"
            )
        else:
            lines.append("- **Top negative contributor**: none (all features net non-negative on average)")

    # Decay verdict from Bonferroni-corrected H1/H2
    if h1_h2_tests is not None:
        decayed = [t for t in h1_h2_tests if t.survives_bonferroni and t.delta > 0]
        if decayed:
            decayed.sort(key=lambda t: -t.delta)
            most = decayed[0]
            lines.append(
                f"- **Most decayed H1→H2 (Bonferroni α={alpha:.3f})**: "
                f"`{most.feature}` (delta {most.delta:+.4f}, "
                f"bonf p = {_format_p(most.bonferroni_p)})"
            )
        else:
            lines.append(
                f"- **Most decayed H1→H2**: _(none survive Bonferroni at "
                f"α={alpha:.3f})_"
            )

    # Methodological caveats
    lines.append("\n## Caveats\n")
    lines.append(
        f"- SHAP rank vs Bayesian-magnitude rank Spearman r = "
        f"`{delta.get('spearman_r', float('nan')):.3f}` (n={delta.get('n', 0)})."
    )
    lines.append(
        "- Realised-R target only — no walk-level proxies "
        "(per `feedback_walk_level_evidence_not_predictive`)."
    )
    lines.append(
        "- Categorical features are integer-encoded "
        "(framework_id, session_id, regime_tag); the GBM tree splits handle "
        "them natively but the Bayesian linear model treats them as ordinal "
        "— interpret Bayesian coefficients on those columns with care."
    )
    lines.append(
        "- F16 update: SHAP is now the default attribution path when "
        "`shap` + a tree backend (`lightgbm` / `xgboost` / sklearn-GBM) "
        "are importable. The original K50 (commit `44d0644`) ran the "
        "permutation-importance fallback because the local environment "
        "lacked `shap` at the time. See `comparison.md` (when present) "
        "for proper-SHAP vs original-permutation deltas."
    )
    lines.append(
        "- Bonferroni correction is applied to the H1/H2 importance-"
        f"delta test family across the {len(report.feature_names)} canonical "
        "features. With small-n bootstrap distributions per half, the "
        f"corrected α={alpha:.3f} demands raw_p < {alpha / len(report.feature_names):.4f}, "
        "which is conservative."
    )
    lines.append(
        "- Bootstrap CIs are computed by resampling filled trades with "
        "replacement and re-fitting the regressor. Per-feature mean |SHAP| "
        "percentile bounds reflect sampling variability of the importance "
        "statistic, not model misspecification."
    )
    lines.append(
        "- Output feeds K54 ML classifier feature engineering. K50 does "
        "**not** propose system changes."
    )

    out = out_dir / "report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _write_comparison(
    out_dir: Path,
    proper_report: AttributionReport,
    proper_cis: tuple[FeatureCI, ...],
    h1_h2_tests: tuple[FeatureImportanceTest, ...] | None,
    *,
    original_ranking_path: Path,
    method_requested: str,
    alpha: float,
) -> Path | None:
    """Write `comparison.md` if the original K50 ranking JSON exists.

    Pure observational; never raises if the original file is malformed.
    """
    if not original_ranking_path.exists():
        return None
    try:
        original = json.loads(original_ranking_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    orig_rankings = original.get("shap_rankings", [])
    if not orig_rankings:
        return None

    orig_method = original.get("shap_method") or original.get("shap_method_used") or "unknown"
    orig_n = original.get("n_samples", "—")

    orig_by_feat = {r["feature"]: r for r in orig_rankings}
    proper_by_feat = {r.feature: r for r in proper_report.rankings}
    proper_ci_by_feat = {fc.feature: fc for fc in proper_cis}
    h1_h2_by_feat = (
        {t.feature: t for t in h1_h2_tests} if h1_h2_tests is not None else {}
    )

    fp = out_dir / "comparison.md"
    lines: list[str] = []
    lines.append(
        "# K50 — proper SHAP vs original permutation comparison\n"
    )
    lines.append(
        f"- **Original K50 method**: `{orig_method}` "
        f"(no Bonferroni, no bootstrap CI). n_samples = {orig_n}.\n"
        f"- **Proper-SHAP K50 method**: `{proper_report.method}` "
        f"(Bonferroni α = {alpha:.3f}, family_size = "
        f"{len(proper_report.feature_names)}). n_samples = "
        f"{proper_report.n_samples}.\n"
        f"- **Original ranking JSON**: `{original_ranking_path}`\n"
    )

    # Verdict-format table per the F16 brief
    lines.append("\n## K50 — proper SHAP vs original permutation\n")
    lines.append(
        "| Feature | original mean importance% | proper SHAP mean \\|SHAP\\| | "
        "proper rel imp% | rank delta | bonf p | status change |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---|")

    # Build aligned rows in proper-rank order
    feats = list(proper_report.feature_names)
    # rank delta = proper_rank - original_rank
    proper_rank_by_feat = {r.feature: r.rank for r in proper_report.rankings}
    orig_rank_by_feat = {
        r["feature"]: r["rank"] for r in orig_rankings if "rank" in r
    }

    for feat in feats:
        orig = orig_by_feat.get(feat, {})
        proper = proper_by_feat.get(feat)
        ci = proper_ci_by_feat.get(feat)
        h1h2 = h1_h2_by_feat.get(feat)

        orig_pct = orig.get("relative_importance", 0.0) * 100 if orig else 0.0
        if proper is None:
            continue
        proper_imp = proper.mean_abs_shap
        proper_pct = proper.relative_importance * 100
        rd = (
            proper_rank_by_feat.get(feat, 0) - orig_rank_by_feat.get(feat, 0)
            if feat in orig_rank_by_feat
            else 0
        )
        bonf_p = h1h2.bonferroni_p if h1h2 else float("nan")

        # Status change: a feature shifts categories under the strict regime if
        # it was a top-3 contributor in the original AND falls out of top-3
        # under proper SHAP (or vice versa).
        orig_rank = orig_rank_by_feat.get(feat, 99)
        proper_rank = proper_rank_by_feat.get(feat, 99)
        if orig_rank <= 3 and proper_rank > 3:
            status = "fell from top-3"
        elif orig_rank > 3 and proper_rank <= 3:
            status = "rose into top-3"
        elif orig_rank == 1 and proper_rank > 1:
            status = "lost #1 dominance"
        elif orig_rank > 1 and proper_rank == 1:
            status = "became #1"
        else:
            status = "—"

        lines.append(
            f"| {feat} | {orig_pct:.1f}% | {proper_imp:.4f} "
            + (f"({_format_ci(ci.ci_low, ci.ci_high)})" if ci else "")
            + f" | {proper_pct:.1f}% | "
            f"{rd:+d} | {_format_p(bonf_p)} | {status} |"
        )

    lines.append("")

    # Comparison verdict
    framework_proper = proper_by_feat.get("framework_id")
    framework_orig = orig_by_feat.get("framework_id")
    framework_remains_dominant = (
        framework_proper is not None
        and framework_proper.rank == 1
    )

    top_proper = proper_report.rankings[0] if proper_report.rankings else None
    top_orig = orig_rankings[0] if orig_rankings else {}

    # Sign flips: SHAP mean changes sign vs original
    sign_flips: list[str] = []
    for feat in feats:
        orig = orig_by_feat.get(feat, {})
        proper = proper_by_feat.get(feat)
        if proper is None:
            continue
        orig_signed = orig.get("mean_shap", 0.0)
        prop_signed = proper.mean_shap
        if orig_signed > 0 and prop_signed < 0:
            sign_flips.append(feat)
        elif orig_signed < 0 and prop_signed > 0:
            sign_flips.append(feat)

    lines.append("## Comparison verdict\n")
    if top_proper is not None:
        lines.append(
            f"- Top feature under proper SHAP: **{top_proper.feature}** "
            f"({top_proper.relative_importance * 100:.1f}% relative |SHAP|)."
        )
    if top_orig:
        lines.append(
            f"- Top feature under original permutation: "
            f"**{top_orig.get('feature', '—')}** "
            f"({top_orig.get('relative_importance', 0.0) * 100:.1f}% relative)."
        )
    lines.append(
        f"- Whether `framework_id` remains dominant under proper SHAP: "
        f"{'**yes**' if framework_remains_dominant else '**no**'}."
    )
    if sign_flips:
        lines.append(
            f"- Sign-flips between methods: {', '.join(sign_flips)}."
        )
    else:
        lines.append("- Sign-flips between methods: _(none)_.")

    # Reasoning (2-4 sentences)
    if framework_remains_dominant:
        reason = (
            "Proper SHAP confirms `framework_id` retains its #1 rank, but "
            f"the magnitude shifts ({_format_imp(framework_orig['mean_abs_shap']) if framework_orig else '—'} → "
            f"{_format_imp(framework_proper.mean_abs_shap)}) and the bootstrap CI "
            f"makes the variance of the estimate explicit. Other features' relative "
            f"shares may have shrunk because the GBM/SHAP path captures interaction "
            f"effects that the univariate permutation fallback overshoots."
        )
    else:
        reason = (
            f"Under proper SHAP, `framework_id` no longer ranks #1. "
            f"`{top_proper.feature if top_proper else 'unknown'}` is now the dominant "
            "edge component. The original permutation-importance estimate was "
            "likely inflated by univariate-mean shifts that don't survive a "
            "tree-model's joint attribution. K50's original verdict therefore "
            "does NOT replicate under proper SHAP — analogous to F5's K51 "
            "finding where 2/3 features sign-flipped."
        )
    lines.append(f"- Reasoning: {reason}")

    lines.append("")
    lines.append("## Strategic implication\n")
    lines.append(
        "- For K54 feature engineering: prioritise the proper-SHAP top "
        f"contributors (rank-1: `{top_proper.feature if top_proper else '—'}`)."
        " Treat the original K50 ranking as a screening hint, not a "
        "confirmed feature attribution."
    )
    lines.append(
        "- For Phase 2 prompt research: re-frame any prior framing that "
        "leant on `framework_id 81%` "
        "(the original 215-trade run shipped 75%). Where proper SHAP demotes "
        "or sign-flips a feature, the prompt research that followed that "
        "feature's trail should be re-evaluated."
    )
    lines.append(
        "- F16 + F5 confirm a methodology pattern: permutation importance "
        "without correction is a screening tool only. Confirmatory K-series "
        "research must use SHAP TreeExplainer plus Bonferroni and bootstrap "
        "CI before strategic conclusions are drawn."
    )

    fp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return fp


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="K50 edge attribution (F16: proper SHAP + Bonferroni + bootstrap CI)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Output directory. Default: "
            f"{DEFAULT_OUTPUT_DIR.relative_to(ROOT) if DEFAULT_OUTPUT_DIR.is_relative_to(ROOT) else DEFAULT_OUTPUT_DIR}"
        ),
    )
    parser.add_argument(
        "--trade-index",
        type=Path,
        default=DEFAULT_TRADE_INDEX,
        help="Path to _trade_index.json",
    )
    parser.add_argument(
        "--unified-csv",
        type=Path,
        default=DEFAULT_UNIFIED_CSV,
        help="Optional path to trades_unified.csv (auxiliary)",
    )
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=None,
        help="Optional symbol filter (e.g. XAUUSD GBPUSD)",
    )
    parser.add_argument(
        "--no-unified-csv",
        action="store_true",
        help="Skip the unified CSV merge (only use _trade_index.json)",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="auto",
        choices=("auto", "shap", "permutation"),
        help=(
            "Attribution method. 'auto' uses SHAP when available, "
            "permutation otherwise. 'shap' forces SHAP and errors out "
            "if it is unavailable. 'permutation' forces the original "
            "sklearn permutation-importance fallback."
        ),
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help=(
            "Bonferroni significance threshold for the H1/H2 mean |SHAP| "
            "importance-delta test family across the 8 canonical features. "
            "A feature must satisfy bonferroni_p < alpha to be classified "
            "as 'decayed'."
        ),
    )
    parser.add_argument(
        "--bootstrap-n-resamples",
        type=int,
        default=100,
        help=(
            "Number of bootstrap resamples per feature (and per H1 / H2 "
            "half). 0 disables bootstrap CIs (CI bounds = point estimate)."
        ),
    )
    parser.add_argument(
        "--bootstrap-seed",
        type=int,
        default=0,
        help="Seed for the bootstrap resampler.",
    )
    parser.add_argument(
        "--ci-alpha",
        type=float,
        default=0.05,
        help="Two-sided CI alpha. 0.05 → 2.5/97.5 percentiles (95%% CI).",
    )
    parser.add_argument(
        "--no-comparison",
        action="store_true",
        help=(
            "Skip the auto-generated comparison.md block even if the "
            "original K50_attribution/ranking.json exists."
        ),
    )
    parser.add_argument(
        "--original-ranking",
        type=Path,
        default=None,
        help=(
            "Optional explicit path to the original-K50 ranking.json. "
            "If omitted, defaults to the canonical "
            "research/edge_decomposition/K50_attribution/ranking.json "
            "sibling directory of --output-dir."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    sources: list[str] = []
    primary = _load_trade_index(args.trade_index)
    if primary:
        sources.append(f"trade_index:{args.trade_index.name}")
    secondary: list[dict] = []
    if not args.no_unified_csv:
        secondary = _load_unified_csv(args.unified_csv)
        if secondary:
            sources.append(f"unified_csv:{args.unified_csv.name}")

    trades = _merge_unique(primary, secondary)
    n_input = len(trades)
    trades = _filter_symbols(trades, args.symbols)

    # Filled count = trades with extractable realised R
    from src.research_infra.edge_attribution import _extract_realized_r  # noqa: WPS433

    n_filled = sum(1 for t in trades if _extract_realized_r(t) is not None)

    if n_filled < 4:
        print(
            f"[K50] only {n_filled} filled trades after filter — aborting.",
            file=sys.stderr,
        )
        return 2

    print(f"[K50] SHAP available: {_shap_available()} | requested method: {args.method}")
    print(f"[K50] Loading {n_filled} filled trades ...")

    X, y, names = build_feature_matrix(trades)
    if X.shape[0] < 4:
        print("[K50] feature matrix too small — aborting.", file=sys.stderr)
        return 3

    # Trade-id alignment for shap_values.json rows
    trade_ids: list[str] = []
    seen_idx = 0
    for t in trades:
        if not isinstance(t, dict):
            continue
        if _extract_realized_r(t) is None:
            continue
        trade_ids.append(str(t.get("trade_id", f"row_{seen_idx}")))
        seen_idx += 1

    # Full-population attribution + bootstrap CI
    print(
        f"[K50] Bootstrapping ({args.bootstrap_n_resamples} resamples, "
        f"seed={args.bootstrap_seed}, ci_alpha={args.ci_alpha}) ..."
    )
    full = compute_shap_attribution_with_ci(
        X, y, names,
        method=args.method,
        n_resamples=args.bootstrap_n_resamples,
        seed=args.bootstrap_seed,
        ci_alpha=args.ci_alpha,
    )
    report = full.base_report
    cis = full.cis

    # H1 / H2 split + bootstrap distributions for the importance-delta test
    h1, h2 = _split_chronological_halves(trades)
    h1_h2_tests: tuple[FeatureImportanceTest, ...] | None = None
    h1_n: int | None = None
    h2_n: int | None = None
    if len(h1) >= 4 and len(h2) >= 4:
        Xh1, yh1, _ = build_feature_matrix(h1)
        Xh2, yh2, _ = build_feature_matrix(h2)
        h1_n = int(Xh1.shape[0])
        h2_n = int(Xh2.shape[0])
        if h1_n >= 4 and h2_n >= 4:
            print(f"[K50] H1 / H2 split: {h1_n} / {h2_n} filled trades.")
            h1_full = compute_shap_attribution_with_ci(
                Xh1, yh1, names,
                method=args.method,
                n_resamples=args.bootstrap_n_resamples,
                seed=args.bootstrap_seed + 1,
                ci_alpha=args.ci_alpha,
            )
            h2_full = compute_shap_attribution_with_ci(
                Xh2, yh2, names,
                method=args.method,
                n_resamples=args.bootstrap_n_resamples,
                seed=args.bootstrap_seed + 2,
                ci_alpha=args.ci_alpha,
            )
            h1_h2_tests = h1_h2_importance_test(
                h1_full.bootstrap_distributions,
                h2_full.bootstrap_distributions,
                names,
                alpha=args.alpha,
                family_size=len(names),
            )
        else:
            print(
                "[K50] H1 / H2 halves too small for importance test "
                f"(h1={h1_n}, h2={h2_n}); skipping.",
                file=sys.stderr,
            )

    # Bayesian sanity check on the full population
    bayes = bayesian_linear_attribution(X, y, names)
    delta = spearman_rank_delta(report.rankings, bayes["rank_by_abs_mean"])

    # Write artefacts
    shap_path = _write_shap_values(
        out_dir, report, cis, trade_ids,
        bootstrap_n_resamples=args.bootstrap_n_resamples,
        ci_alpha=args.ci_alpha,
        method_requested=args.method,
    )
    rank_path = _write_ranking(
        out_dir, report, cis, bayes, delta, h1_h2_tests,
        bootstrap_n_resamples=args.bootstrap_n_resamples,
        ci_alpha=args.ci_alpha,
        alpha=args.alpha,
        method_requested=args.method,
    )
    report_path = _write_report_md(
        out_dir, report, cis, bayes, delta, h1_h2_tests,
        n_input=n_input,
        n_filled=n_filled,
        sources=sources,
        symbols_filter=tuple(args.symbols) if args.symbols else None,
        alpha=args.alpha,
        method_requested=args.method,
        bootstrap_n_resamples=args.bootstrap_n_resamples,
        ci_alpha=args.ci_alpha,
        h1_n=h1_n,
        h2_n=h2_n,
    )

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(ROOT))
        except ValueError:
            return str(p)

    print(f"[K50] {report.n_samples} filled trades | method={report.method}")
    print(f"[K50] wrote {_rel(shap_path)}")
    print(f"[K50] wrote {_rel(rank_path)}")
    print(f"[K50] wrote {_rel(report_path)}")
    print("[K50] Top 3 by mean |SHAP|:")
    for r in report.rankings[:3]:
        fc = next((c for c in cis if c.feature == r.feature), None)
        ci_str = f" CI=[{fc.ci_low:.4f}, {fc.ci_high:.4f}]" if fc else ""
        print(
            f"  {r.rank}. {r.feature}: |SHAP|={r.mean_abs_shap:.4f} "
            f"signed={r.mean_shap:+.4f} rel={r.relative_importance * 100:.1f}%{ci_str}"
        )

    # Comparison block
    if not args.no_comparison:
        if args.original_ranking is not None:
            original_ranking_path = args.original_ranking
        else:
            original_ranking_path = (
                out_dir.parent / "K50_attribution" / "ranking.json"
            )
        cmp_path = _write_comparison(
            out_dir, report, cis, h1_h2_tests,
            original_ranking_path=original_ranking_path,
            method_requested=args.method,
            alpha=args.alpha,
        )
        if cmp_path is not None:
            print(f"[K50] wrote {_rel(cmp_path)}")
        elif original_ranking_path.exists():
            print(
                f"[K50] original ranking found at {_rel(original_ranking_path)} "
                "but comparison.md was not produced (parser miss)."
            )
        else:
            print(
                f"[K50] no original-K50 ranking at {_rel(original_ranking_path)} "
                "— skipping comparison.md."
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
