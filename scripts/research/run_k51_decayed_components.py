#!/usr/bin/env python3
"""Run K51 — Decayed-Component Identification (proper SHAP + Bonferroni).

Pure-Python CLI that:
  1. Loads filled trades from ``knowledge_base/trade_records/{SYMBOL}/*.json``
     and ``knowledge_base/index/_trade_index.json`` (legacy batch trades).
  2. Computes rolling per-feature mean(|SHAP|) trajectories with bootstrap
     95% CI per window. Falls back to permutation importance when SHAP /
     LightGBM is unavailable.
  3. Identifies features that have decayed ≥ ``--threshold-pct`` (default
     0.40) from H1 to H2 AND survive Bonferroni correction at
     ``--alpha`` (default 0.05) across the canonical-feature family.
  4. Writes ``trajectories.json`` (per-feature per-window importance +
     CI series) and ``decay_report.md`` (verdict block + comparison
     tables + reasoning).

No AI calls. No production-config touched. Read-only on
``knowledge_base/``; writes only inside the chosen ``--output-dir``.

Usage::

    python scripts/research/run_k51_decayed_components.py \
        --output-dir research/edge_decomposition/K51_decayed_proper_shap \
        --window 30 --alpha 0.05

    # Restrict to specific symbols
    python scripts/research/run_k51_decayed_components.py \
        --output-dir research/edge_decomposition/K51_decayed_proper_shap \
        --window 30 \
        --symbols XAUUSD US30_cash USDJPY
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research_infra.decayed_component_identifier import (  # noqa: E402
    CANONICAL_FEATURES,
    DecayReport,
    FeatureDecay,
    TrajectoryPoint,
    _shap_available,
    identify_decay,
    load_trades_from_disk,
    rolling_attribution,
)


DEFAULT_TRADE_RECORDS_DIR = ROOT / "knowledge_base" / "trade_records"
DEFAULT_AUX_INDEX = ROOT / "knowledge_base" / "index" / "_trade_index.json"


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="K51 — Decayed-Component Identification (SHAP + Bonferroni)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help=(
            "Directory to write trajectories.json + decay_report.md. "
            "Created if it does not exist."
        ),
    )
    p.add_argument(
        "--window",
        type=int,
        default=50,
        help="Non-overlapping rolling window size (number of trades).",
    )
    p.add_argument(
        "--threshold-pct",
        type=float,
        default=0.40,
        help="Fractional drop threshold for 'decayed' classification.",
    )
    p.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help=(
            "Bonferroni significance threshold for the H1/H2 importance-"
            "delta hypothesis test family. A feature must satisfy "
            "bonferroni_p < alpha to be classified as 'decayed'."
        ),
    )
    p.add_argument(
        "--method",
        type=str,
        default="auto",
        choices=("auto", "shap", "permutation"),
        help=(
            "Importance method. 'auto' uses SHAP when available, "
            "permutation otherwise. 'shap' forces SHAP and errors out "
            "if it is unavailable. 'permutation' forces the original "
            "stratum-mean fallback."
        ),
    )
    p.add_argument(
        "--bootstrap-n-resamples",
        type=int,
        default=100,
        help="Bootstrap resamples per window for the 95%% CI. 0 disables.",
    )
    p.add_argument(
        "--bootstrap-seed",
        type=int,
        default=0,
        help="Seed for the per-window bootstrap resampler.",
    )
    p.add_argument(
        "--ci-alpha",
        type=float,
        default=0.05,
        help=(
            "Two-sided CI alpha for the bootstrap percentile bands. "
            "0.05 → 95%% CI."
        ),
    )
    p.add_argument(
        "--trade-records-dir",
        type=Path,
        default=DEFAULT_TRADE_RECORDS_DIR,
        help="Override trade-records directory.",
    )
    p.add_argument(
        "--aux-index",
        type=Path,
        default=DEFAULT_AUX_INDEX,
        help=(
            "Legacy _trade_index.json with a top-level 'trades' array. "
            "Use the literal value 'none' to skip."
        ),
    )
    p.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help=(
            "Restrict to these instruments (case-insensitive). Default: "
            "use everything found on disk."
        ),
    )
    return p


def _trajectories_to_jsonable(
    series: dict[str, list[TrajectoryPoint]],
) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for feature, points in series.items():
        out[feature] = [asdict(p) for p in points]
    return out


def _round(x: float, digits: int = 6) -> float:
    if not math.isfinite(x):
        return 0.0
    return round(float(x), digits)


def _format_imp(x: float) -> str:
    if not math.isfinite(x):
        return "—"
    return f"{x:.4f}"


def _format_pct(x: float) -> str:
    if not math.isfinite(x):
        return "—"
    return f"{x * 100:+.1f}%"


def _format_p(p: float) -> str:
    if not isinstance(p, float) or not math.isfinite(p):
        return "—"
    if p < 1e-4:
        return f"{p:.2e}"
    return f"{p:.4f}"


def _format_ci(lo: float, hi: float) -> str:
    if not math.isfinite(lo) or not math.isfinite(hi):
        return "—"
    return f"[{lo:.4f}, {hi:.4f}]"


def _h1_h2_ci_for_feature(series, feature: str) -> tuple[str, str]:
    """Aggregate the per-window CIs for a feature into H1 / H2 mean-CI strings."""
    points = series.get(feature, [])
    n = len(points)
    if n == 0:
        return "—", "—"
    mid = n // 2
    h1 = points[:mid]
    h2 = points[mid:]
    if h1:
        lo_h1 = sum(p.ci_low for p in h1) / len(h1)
        hi_h1 = sum(p.ci_high for p in h1) / len(h1)
        h1_str = _format_ci(lo_h1, hi_h1)
    else:
        h1_str = "—"
    if h2:
        lo_h2 = sum(p.ci_low for p in h2) / len(h2)
        hi_h2 = sum(p.ci_high for p in h2) / len(h2)
        h2_str = _format_ci(lo_h2, hi_h2)
    else:
        h2_str = "—"
    return h1_str, h2_str


def _write_trajectories(
    out_dir: Path,
    series: dict[str, list[TrajectoryPoint]],
    *,
    window: int,
    threshold_pct: float,
    alpha: float,
    method: str,
    n_trades_total: int,
    bootstrap_n_resamples: int,
    ci_alpha: float,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / "trajectories.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window": window,
        "threshold_pct": threshold_pct,
        "alpha": alpha,
        "method_requested": method,
        "shap_available": _shap_available(),
        "bootstrap_n_resamples": bootstrap_n_resamples,
        "ci_alpha": ci_alpha,
        "n_trades_total": n_trades_total,
        "features": list(CANONICAL_FEATURES),
        "trajectories": _trajectories_to_jsonable(series),
    }
    fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return fp


def _write_report(
    out_dir: Path,
    report: DecayReport,
    series: dict[str, list[TrajectoryPoint]],
    *,
    window: int,
    n_trades_total: int,
    trade_records_dir: Path,
    aux_index_path: Path | None,
    symbols: list[str] | None,
    method_requested: str,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / "decay_report.md"
    lines: list[str] = []
    lines.append("# K51 — Decayed-Component Identification (proper SHAP + Bonferroni)")
    lines.append("")
    lines.append(f"_Generated: {datetime.now(timezone.utc).isoformat()}_")
    lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        f"For each non-overlapping rolling window of **{window} trades**, "
        f"compute per-feature **{report.method}** importance (mean |SHAP| "
        "under the SHAP path; baseline-MSE − stratum-mean-MSE under the "
        "permutation fallback). Track per-feature trajectories across "
        f"windows. A **decayed component** has its mean importance drop ≥ "
        f"**{report.threshold_pct * 100:.0f}%** from H1 (first half of "
        f"windows) to H2 (second half) **AND** the H1/H2 importance-delta "
        f"one-sided Welch's t-test survives Bonferroni correction "
        f"(family_size = {report.family_size}, α = {report.alpha:.3f})."
    )
    lines.append("")
    lines.append("Data sources:")
    lines.append(f"- Trade records dir: `{trade_records_dir.resolve()}`")
    if aux_index_path is not None:
        lines.append(f"- Aux index: `{aux_index_path.resolve()}`")
    else:
        lines.append("- Aux index: (none)")
    if symbols:
        lines.append(f"- Symbol filter: {', '.join(sorted(symbols))}")
    else:
        lines.append("- Symbol filter: (all)")
    lines.append(f"- Method requested: `{method_requested}` → actually used: `{report.method}`")
    lines.append(f"- SHAP available: `{_shap_available()}`")
    lines.append("")
    lines.append(
        f"Sample: **{n_trades_total} filled trades**, "
        f"**{report.n_total_windows} windows** of {window}."
    )
    if report.h1_period and report.h2_period:
        lines.append(
            f"H1 period: `{report.h1_period[0]}` → `{report.h1_period[1]}`. "
            f"H2 period: `{report.h2_period[0]}` → `{report.h2_period[1]}`."
        )
    lines.append("")
    if report.n_total_windows < 2:
        lines.append("## Insufficient data")
        lines.append("")
        lines.append(
            f"Only {report.n_total_windows} window(s) of {window} trades were "
            "produced. Need at least 2 windows to split into H1/H2 — "
            "no decay verdict possible. Increase trade history or shrink "
            "``--window``."
        )
        fp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return fp

    # ─────────────────────────────────────────────────────────────────
    # Verdict block — required schema:
    #
    # ## Components decayed >=N% H1->H2 (mean SHAP, Bonferroni-corrected)
    # | Feature | H1 mean |SHAP| | H2 mean |SHAP| | drop % | bootstrap 95% CI | bonf p | status |
    # ─────────────────────────────────────────────────────────────────
    lines.append(
        f"## Components decayed >={report.threshold_pct * 100:.0f}% H1->H2 "
        f"(mean {('|SHAP|' if report.method == 'shap_treeexplainer' else 'permutation')}, Bonferroni-corrected)"
    )
    lines.append("")
    if report.method == "shap_treeexplainer":
        magnitude_label = "|SHAP|"
    else:
        magnitude_label = "importance"
    lines.append(
        f"| Feature | H1 mean {magnitude_label} | H2 mean {magnitude_label} | "
        "drop % | bootstrap 95% CI (H1, H2) | bonf p | status |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    if not report.decayed:
        lines.append("| _(none)_ | — | — | — | — | — | — |")
    else:
        for d in report.decayed:
            h1_ci, h2_ci = _h1_h2_ci_for_feature(series, d.feature)
            lines.append(
                f"| {d.feature} | {_format_imp(d.h1_mean)} | "
                f"{_format_imp(d.h2_mean)} | {_format_pct(d.drop_pct)} | "
                f"H1 {h1_ci} / H2 {h2_ci} | {_format_p(d.bonferroni_p)} | "
                f"{'DECAYED' if d.survives_bonferroni else 'suggestive'} |"
            )
    lines.append("")

    # All-feature table (informational; shows everything including
    # large-drop-but-fail-Bonferroni features).
    lines.append("## All canonical features (regardless of decay verdict)")
    lines.append("")
    lines.append(
        f"| Feature | H1 mean {magnitude_label} | H2 mean {magnitude_label} | "
        "drop % | bootstrap 95% CI (H1, H2) | raw p | bonf p | status |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for d in report.all_features:
        h1_ci, h2_ci = _h1_h2_ci_for_feature(series, d.feature)
        if d.survives_bonferroni and d.drop_pct >= report.threshold_pct:
            status = "DECAYED"
        elif d.h1_mean == 0 and d.h2_mean > 0:
            status = "newly important"
        elif math.isfinite(d.bonferroni_p) and d.bonferroni_p < report.alpha and d.drop_pct < report.threshold_pct:
            status = "sig but <threshold"
        elif d.drop_pct >= report.threshold_pct and not d.survives_bonferroni:
            status = "suggestive"
        else:
            status = "stable"
        lines.append(
            f"| {d.feature} | {_format_imp(d.h1_mean)} | "
            f"{_format_imp(d.h2_mean)} | {_format_pct(d.drop_pct)} | "
            f"H1 {h1_ci} / H2 {h2_ci} | {_format_p(d.raw_p)} | "
            f"{_format_p(d.bonferroni_p)} | {status} |"
        )
    lines.append("")

    # Newly important
    lines.append("## Newly important features (H1 mass == 0, H2 mass > 0)")
    lines.append("")
    lines.append(
        f"| Feature | H1 mean {magnitude_label} | H2 mean {magnitude_label} | "
        "gain | bonf p | n_h1 | n_h2 |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    if not report.newly_important:
        lines.append("| _(none)_ | — | — | — | — | — | — |")
    else:
        for d in report.newly_important:
            gain = d.h2_mean - d.h1_mean
            lines.append(
                f"| {d.feature} | {_format_imp(d.h1_mean)} | "
                f"{_format_imp(d.h2_mean)} | {_format_imp(gain)} | "
                f"{_format_p(d.bonferroni_p)} | "
                f"{d.n_h1_windows} | {d.n_h2_windows} |"
            )
    lines.append("")

    # Stable
    lines.append("## Stable features (or large-drop-but-not-significant)")
    lines.append("")
    lines.append(
        f"| Feature | H1 mean {magnitude_label} | H2 mean {magnitude_label} | "
        "drop % | bonf p | n_h1 | n_h2 |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    if not report.stable:
        lines.append("| _(none)_ | — | — | — | — | — | — |")
    else:
        for d in report.stable:
            lines.append(
                f"| {d.feature} | {_format_imp(d.h1_mean)} | "
                f"{_format_imp(d.h2_mean)} | {_format_pct(d.drop_pct)} | "
                f"{_format_p(d.bonferroni_p)} | "
                f"{d.n_h1_windows} | {d.n_h2_windows} |"
            )
    lines.append("")

    # Strategic verdict
    lines.append("## Strategic verdict")
    lines.append("")
    if report.decayed:
        most = report.decayed[0]
        lines.append(
            f"- Most decayed (proper-method): **{most.feature}** "
            f"({_format_pct(most.drop_pct)}, "
            f"bonf p = {_format_p(most.bonferroni_p)})."
        )
    else:
        lines.append(
            "- Most decayed (proper-method): _(none survive Bonferroni at "
            f"α={report.alpha:.3f})_."
        )

    if report.newly_important:
        newest = report.newly_important[0]
        lines.append(
            f"- Newly important (proper-method): **{newest.feature}** "
            f"(H2 importance {_format_imp(newest.h2_mean)})."
        )
    else:
        lines.append("- Newly important (proper-method): _(none)_.")

    # Sign-flips between methods are computed externally if a comparison
    # JSON is supplied; here we only state the raw verdict.
    lines.append("")
    lines.append("Reasoning:")
    if report.decayed:
        decayed_names = ", ".join(d.feature for d in report.decayed[:3])
        lines.append(
            f"- Features {decayed_names} carried meaningful R-variance "
            f"explanation in H1 but lost it in H2 with bonf p < {report.alpha:.3f}. "
            "Either the AI's selection criteria along these axes have "
            "weakened (system decay) or the underlying market relationship "
            "between these features and outcome has dissolved (regime decay)."
        )
    else:
        lines.append(
            "- No feature dropped past the threshold AND survived Bonferroni "
            "correction. The H1/H2 split with this many windows is "
            "underpowered for a Bonferroni-corrected family-of-"
            f"{report.family_size} test — large raw drops can fail "
            "Bonferroni when n_h1_windows + n_h2_windows is small. The "
            "permutation-method (no Bonferroni) results in the original "
            "K51 are screening hints, not significant signals."
        )
    if report.newly_important:
        lines.append(
            "- Newly important features in H2 indicate that the active edge "
            "axis has shifted; investigate these strata in K54+ for ML-classifier "
            "feature selection."
        )
    lines.append(
        "- Cross-reference with K50 (population-level attribution) before "
        "drawing strategic conclusions: if K50 ranks a feature low and K51 "
        "shows it decaying, the feature was never load-bearing."
    )
    lines.append(
        "- Walk-level evidence is not predictive of realized R "
        "(`feedback_walk_level_evidence_not_predictive`) — these importances "
        "are computed against realized R per filled trade."
    )

    fp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return fp


def _maybe_write_comparison(
    out_dir: Path,
    report: DecayReport,
    series: dict[str, list[TrajectoryPoint]],
    *,
    original_trajectories_path: Path | None,
) -> Path | None:
    """If an original (permutation-only, no-Bonferroni) trajectories
    JSON is supplied, write a comparison block to ``comparison.md``.

    Pure observational; never errors if the original is unavailable.
    """
    if original_trajectories_path is None or not original_trajectories_path.exists():
        return None
    try:
        original = json.loads(original_trajectories_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    orig_trajs = original.get("trajectories", {})
    # Compute original drops per feature (no Bonferroni)
    orig_drops: dict[str, tuple[float, float, float]] = {}
    for feat, points in orig_trajs.items():
        if not points:
            continue
        n = len(points)
        mid = n // 2
        h1 = [p["importance"] for p in points[:mid]]
        h2 = [p["importance"] for p in points[mid:]]
        h1_m = sum(h1) / len(h1) if h1 else 0.0
        h2_m = sum(h2) / len(h2) if h2 else 0.0
        if h1_m > 0:
            drop = (h1_m - h2_m) / h1_m
        elif h2_m > 0:
            drop = -1.0
        else:
            drop = 0.0
        orig_drops[feat] = (h1_m, h2_m, drop)

    # Map proper-method records by feature
    proper_by_feat: dict[str, FeatureDecay] = {fd.feature: fd for fd in report.all_features}

    fp = out_dir / "comparison.md"
    lines: list[str] = []
    lines.append("# K51 comparison — proper SHAP + Bonferroni vs original (permutation, no Bonferroni)")
    lines.append("")
    lines.append(f"_Generated: {datetime.now(timezone.utc).isoformat()}_")
    lines.append("")
    lines.append(
        f"Original trajectories: `{original_trajectories_path.resolve()}`"
    )
    lines.append(
        f"Original method: `permutation_importance` (no Bonferroni). "
        f"Proper method: `{report.method}` (Bonferroni at α={report.alpha:.3f}, "
        f"family_size={report.family_size})."
    )
    lines.append("")
    lines.append("## Comparison vs original K51 (permutation, no Bonferroni)")
    lines.append("")
    lines.append(
        "| Feature | original drop% | proper drop% | delta | bonf p | original status | proper status | status change |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    threshold = report.threshold_pct
    alpha = report.alpha
    for feat in sorted(set(orig_drops) | set(proper_by_feat)):
        orig = orig_drops.get(feat)
        proper = proper_by_feat.get(feat)
        orig_drop = orig[2] if orig else float("nan")
        proper_drop = proper.drop_pct if proper else float("nan")
        if math.isfinite(orig_drop) and math.isfinite(proper_drop):
            delta = proper_drop - orig_drop
        else:
            delta = float("nan")
        # Original status: only threshold matters (no Bonferroni in original).
        if not orig:
            orig_status = "n/a"
        elif orig[0] == 0 and orig[1] > 0:
            orig_status = "newly important"
        elif math.isfinite(orig_drop) and orig_drop >= threshold:
            orig_status = "decayed"
        else:
            orig_status = "stable"
        # Proper status
        if not proper:
            proper_status = "n/a"
        elif proper.h1_mean == 0 and proper.h2_mean > 0:
            proper_status = "newly important"
        elif proper.drop_pct >= threshold and proper.survives_bonferroni:
            proper_status = "DECAYED"
        elif proper.drop_pct >= threshold and not proper.survives_bonferroni:
            proper_status = "suggestive"
        else:
            proper_status = "stable"
        change = "—" if orig_status == proper_status else f"{orig_status} → {proper_status}"
        bonf_p = proper.bonferroni_p if proper else float("nan")
        lines.append(
            f"| {feat} | {_format_pct(orig_drop)} | {_format_pct(proper_drop)} | "
            f"{_format_pct(delta)} | {_format_p(bonf_p)} | "
            f"{orig_status} | {proper_status} | {change} |"
        )
    lines.append("")
    lines.append("## Reasoning")
    lines.append("")
    lines.append(
        "The proper method (SHAP / mean(|SHAP|) when available, plus a "
        "one-sided Welch's t-test on the H1/H2 importance series Bonferroni-"
        f"corrected over family_size={report.family_size}, α={report.alpha:.3f}) "
        "is a stricter test than the original screening rule. With only a "
        "handful of windows per half, Bonferroni at α=0.05 is hard to "
        "satisfy; large raw drops can drop to 'suggestive' status. The "
        "comparison block makes this dynamic transparent and is the right "
        "lens for ranking K54 ML-classifier feature inclusion."
    )

    fp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return fp


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    aux_index_path: Path | None = args.aux_index
    if aux_index_path is not None:
        aux_str = str(aux_index_path).strip().lower()
        if aux_str in ("none", "null", "off", ""):
            aux_index_path = None

    trade_records_dir: Path = args.trade_records_dir

    print(f"[K51] SHAP available: {_shap_available()}")
    print(f"[K51] Loading trades from {trade_records_dir} (aux: {aux_index_path}) ...")
    trades = load_trades_from_disk(
        trade_records_dir=trade_records_dir,
        aux_index_path=aux_index_path,
        symbols=args.symbols,
    )
    print(f"[K51] Loaded {len(trades)} filled trades.")

    series = rolling_attribution(
        trades,
        window=args.window,
        method=args.method,
        bootstrap_n_resamples=args.bootstrap_n_resamples,
        bootstrap_seed=args.bootstrap_seed,
        ci_alpha=args.ci_alpha,
    )
    n_windows = (
        len(next(iter(series.values()))) if series and next(iter(series.values())) else 0
    )
    print(f"[K51] Built {n_windows} non-overlapping windows of {args.window} trades.")

    report = identify_decay(series, threshold_pct=args.threshold_pct, alpha=args.alpha)
    print(
        f"[K51] Decay verdict (alpha={args.alpha:.3f}, Bonferroni family={report.family_size}): "
        f"{len(report.decayed)} decayed, "
        f"{len(report.newly_important)} newly important, "
        f"{len(report.stable)} stable."
    )

    out_dir: Path = args.output_dir
    traj_path = _write_trajectories(
        out_dir,
        series,
        window=args.window,
        threshold_pct=args.threshold_pct,
        alpha=args.alpha,
        method=args.method,
        n_trades_total=len(trades),
        bootstrap_n_resamples=args.bootstrap_n_resamples,
        ci_alpha=args.ci_alpha,
    )
    report_path = _write_report(
        out_dir,
        report,
        series,
        window=args.window,
        n_trades_total=len(trades),
        trade_records_dir=trade_records_dir,
        aux_index_path=aux_index_path,
        symbols=args.symbols,
        method_requested=args.method,
    )
    print(f"[K51] Wrote {traj_path}")
    print(f"[K51] Wrote {report_path}")

    # Comparison block — auto-detect the original K51 output if it lives
    # at the canonical "K51_decayed_original" sibling directory.
    comparison_candidate = out_dir.parent / "K51_decayed_original" / "trajectories.json"
    if comparison_candidate.exists():
        cmp_path = _maybe_write_comparison(
            out_dir,
            report,
            series,
            original_trajectories_path=comparison_candidate,
        )
        if cmp_path is not None:
            print(f"[K51] Wrote {cmp_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
