"""K53 — Loser Anti-Pattern Classifier CLI runner.

Loads filled CANDIDATEs (with realized R) from the unified Phase 1 + Tier 2
jsonl, builds per-trade feature vectors, clusters losers, trains a binary
classifier, and writes ``clusters.json`` + ``classifier_metrics.json`` +
``anti_pattern_report.md``.

Usage
-----

    # Original mixed-source run (kept for parity with commit 2d3afa4 — but
    # known to be a confounded baseline; train AUC 0.996 → H2 0.598).
    python scripts/research/run_k53_loser_anti_pattern.py \\
        --output-dir research/edge_decomposition/K53_anti_pattern

    # Custom input
    python scripts/research/run_k53_loser_anti_pattern.py \\
        --output-dir <dir> \\
        --input research/accepted_candidates_loser_mining/unified_filled_cands.jsonl

    # Force in-house path (skip sklearn even when installed)
    python scripts/research/run_k53_loser_anti_pattern.py \\
        --output-dir <dir> --no-sklearn

    # Tune k search range
    python scripts/research/run_k53_loser_anti_pattern.py \\
        --output-dir <dir> --k-min 3 --k-max 7

    # F3 source-stratified — Phase-1 only honest baseline (75 filled CANDs)
    python scripts/research/run_k53_loser_anti_pattern.py \\
        --output-dir research/edge_decomposition/K53_anti_pattern_phase1 \\
        --source-filter phase1

    # F3 source-stratified — independent per-source clusters + classifiers
    python scripts/research/run_k53_loser_anti_pattern.py \\
        --output-dir research/edge_decomposition/K53_anti_pattern_per_source \\
        --per-source

Outputs
-------
``clusters.json``               - per-cluster size / mean R / centroid / top-3 features
``classifier_metrics.json``     - train AUC / test AUC / holdout AUC + feature importance
``anti_pattern_report.md``      - human-readable verdict
``feature_matrix.json``         - exported feature matrix (auditable)

When ``--per-source`` is passed, the same four files are written under each
source subdirectory (``<output-dir>/<source>/...``) plus a top-level
``per_source_summary.json`` aggregating the per-source AUCs.

Hard rules
----------
* Pure Python; sklearn optional.
* No AI / Anthropic API calls.
* Read-only: ``research/accepted_candidates_loser_mining/`` is read-only.
* Walk-level features are ignored — clustering is on REALIZED outcomes
  (loss = realized_r ≤ 0).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Allow running from anywhere — locate project root by walking up until we
# see ``pyproject.toml`` so the ``src/`` import works without PYTHONPATH.
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent
while _PROJECT_ROOT != _PROJECT_ROOT.parent:
    if (_PROJECT_ROOT / "pyproject.toml").exists():
        break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.loser_anti_pattern import (  # noqa: E402
    ClassifierReport,
    ClusterReport,
    cluster_frequency_in_window,
    cluster_losers,
    cluster_losers_by_source,
    describe_cluster,
    train_loss_classifier,
    train_loss_classifier_per_source,
)


logger = logging.getLogger(__name__)


DEFAULT_INPUT = (
    "research/accepted_candidates_loser_mining/unified_filled_cands.jsonl"
)


# ────────────────────────────────────────────────────────────────────────────
# Feature engineering
# ────────────────────────────────────────────────────────────────────────────

# K50 alignment: ob_retest_distance_atr, displacement_quality, fvg_present,
# touch_count, framework_id, session_id, hour_of_day, regime_tag.
#
# Our unified jsonl carries:
#   * mso_h1_nearest_ob_distance_atr → ob_retest_distance_atr
#   * displacement_quality / displacement_quality_ord (LOW=0, MEDIUM=1, HIGH=2)
#   * h1_fvg_unfilled_count / m15_fvg_unfilled_count → fvg_present (>0?)
#   * touch_count_at_eval                            → touch_count
#   * framework string                               → one-hot framework
#   * kill_zone string                               → one-hot session
#   * hour_utc                                       → cyclic hour encoding
#   * mso_h1_structure_direction                     → regime_tag proxy
#                                                      (bullish/bearish/range)
#
# Feature schema (deterministic order):
FRAMEWORK_VALUES = ["ob_retest", "fvg_fill", "breaker_re_entry"]
KILL_ZONE_VALUES = ["london", "ny", "tokyo", "off"]


FEATURE_NAMES: list[str] = [
    "ob_retest_distance_atr",     # mso_h1_nearest_ob_distance_atr
    "displacement_quality_ord",   # 0=LOW, 1=MEDIUM, 2=HIGH; missing → 1.0 (median)
    "fvg_h1_unfilled_count",      # h1_fvg_unfilled_count
    "fvg_m15_unfilled_count",     # m15_fvg_unfilled_count
    "fvg_present",                # 1 if any FVG unfilled, else 0
    "touch_count",                # touch_count_at_eval
    "ob_touch_max",               # max touch count across H1 OBs
    "direction_matches_h1",       # 1 if direction aligns with H1 structure
    "hour_sin",                   # sin(2π h / 24)
    "hour_cos",                   # cos(2π h / 24)
    "day_of_week",                # 0..6
    "framework_ob_retest",
    "framework_fvg_fill",
    "framework_breaker_re_entry",
    "session_london",
    "session_ny",
    "session_tokyo",
    "session_off",
    "regime_bullish",
    "regime_bearish",
    "sweep_quality_ord",          # 0/1/2 (LOW/MEDIUM/HIGH); missing → 1.0
    "bias_confidence_ord",        # 0/1/2 (LOW/MEDIUM/HIGH); missing → 1.0
    "fib_retracement_pct",        # 0..1 fractional retracement
    "risk_reward",                # tp_distance / sl_distance
]


def _ord_or(value: Any, default: float = 1.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _displacement_to_ord(value: Any) -> float:
    """LOW/MEDIUM/HIGH → 0/1/2; missing → 1.0 (median imputation)."""
    if value is None:
        return 1.0
    s = str(value).upper().strip()
    return {"LOW": 0.0, "MEDIUM": 1.0, "MODERATE": 1.0, "HIGH": 2.0}.get(s, 1.0)


def _quality_to_ord(value: Any) -> float:
    """Generic ordinal quality (sweep, bias confidence)."""
    if value is None:
        return 1.0
    s = str(value).upper().strip()
    return {"LOW": 0.0, "MEDIUM": 1.0, "MODERATE": 1.0, "HIGH": 2.0}.get(s, 1.0)


def _structure_direction_to_regime(value: Any) -> tuple[float, float]:
    """Returns (regime_bullish, regime_bearish). Range / unknown → (0, 0)."""
    if value is None:
        return (0.0, 0.0)
    s = str(value).lower().strip()
    if s == "bullish":
        return (1.0, 0.0)
    if s == "bearish":
        return (0.0, 1.0)
    return (0.0, 0.0)


def _hour_cyclic(h: Any) -> tuple[float, float]:
    if h is None:
        return (0.0, 0.0)
    try:
        hh = float(h) % 24.0
    except (TypeError, ValueError):
        return (0.0, 0.0)
    import math
    rad = 2.0 * math.pi * hh / 24.0
    return (math.sin(rad), math.cos(rad))


def _one_hot(value: Any, choices: list[str]) -> list[float]:
    if value is None:
        return [0.0] * len(choices)
    s = str(value).lower().strip()
    return [1.0 if s == c.lower() else 0.0 for c in choices]


def _row_to_features(r: dict[str, Any]) -> list[float]:
    """Project a unified jsonl row to the canonical FEATURE_NAMES order."""
    sin_h, cos_h = _hour_cyclic(r.get("hour_utc"))
    fw_oh = _one_hot(r.get("framework"), FRAMEWORK_VALUES)
    kz_oh = _one_hot(r.get("kill_zone"), KILL_ZONE_VALUES)
    regime_b, regime_be = _structure_direction_to_regime(
        r.get("mso_h1_structure_direction")
    )
    h1_fvg = _safe_float(r.get("h1_fvg_unfilled_count"), 0.0)
    m15_fvg = _safe_float(r.get("m15_fvg_unfilled_count"), 0.0)
    return [
        _safe_float(r.get("mso_h1_nearest_ob_distance_atr"), 2.0),
        _displacement_to_ord(r.get("displacement_quality")),
        h1_fvg,
        m15_fvg,
        1.0 if (h1_fvg + m15_fvg) > 0 else 0.0,
        _safe_float(r.get("touch_count_at_eval"), 1.0),
        _safe_float(r.get("ob_touch_max"), 1.0),
        _safe_float(r.get("direction_matches_h1"), 0.0),
        sin_h,
        cos_h,
        _safe_float(r.get("day_of_week"), 2.0),
        *fw_oh,
        *kz_oh,
        regime_b,
        regime_be,
        _quality_to_ord(r.get("sweep_quality")),
        _quality_to_ord(r.get("bias_confidence")),
        _safe_float(r.get("fib_retracement_pct"), 0.5),
        _safe_float(r.get("risk_reward"), 1.5),
    ]


# ────────────────────────────────────────────────────────────────────────────
# Loaders
# ────────────────────────────────────────────────────────────────────────────


def load_unified_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load the unified Phase 1 + Tier 2 filled-CAND jsonl.

    Skips rows that don't carry a realized R-multiple.
    """
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(f"input jsonl not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning("skip line %d: invalid json: %s", line_num, e)
                continue
            if r.get("r_multiple") is None:
                continue
            rows.append(r)
    return rows


def parse_iso_timestamp(s: Any) -> Optional[datetime]:
    if not isinstance(s, str):
        return None
    try:
        # Replace trailing Z so Python parses it.
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


# ────────────────────────────────────────────────────────────────────────────
# Reporting
# ────────────────────────────────────────────────────────────────────────────


def cluster_to_record(
    cid: int,
    report: ClusterReport,
    rows: list[dict[str, Any]],
    indices_in_cluster: list[int],
    h2_freq: dict[int, dict[str, float]],
    feature_matrix: list[list[float]],
) -> dict[str, Any]:
    """Assemble a JSON-serializable cluster record."""
    cluster_rows = [rows[i] for i in indices_in_cluster]
    instruments: dict[str, int] = {}
    for r in cluster_rows:
        instruments[r["symbol"]] = instruments.get(r["symbol"], 0) + 1
    halves: dict[str, int] = {}
    for r in cluster_rows:
        halves[r.get("half") or "unknown"] = halves.get(r.get("half") or "unknown", 0) + 1
    centroid = report.centroids[cid]
    description = describe_cluster(
        cid,
        centroid,
        report.feature_names,
        population_centroid=report.population_centroid,
        top_k=3,
    )
    # Top-3 features by deviation magnitude.
    deviations = sorted(
        [
            (name, val, val - pop)
            for name, val, pop in zip(
                report.feature_names, centroid, report.population_centroid
            )
        ],
        key=lambda t: abs(t[2]),
        reverse=True,
    )[:3]
    return {
        "cluster_id": cid,
        "n": report.cluster_sizes[cid],
        "mean_realized_r": round(report.cluster_means_r[cid], 4),
        "centroid": {
            name: round(v, 4) for name, v in zip(report.feature_names, centroid)
        },
        "top_3_distinguishing_features": [
            {
                "name": name,
                "centroid_value": round(val, 4),
                "deviation_from_population": round(dev, 4),
            }
            for name, val, dev in deviations
        ],
        "instruments": instruments,
        "half_split": halves,
        "h2_2026_n_in_window": h2_freq.get(cid, {}).get("n_in_window", 0),
        "h2_2026_frequency_within_cluster": round(
            h2_freq.get(cid, {}).get("frequency", 0.0), 4
        ),
        "description": description,
    }


def render_markdown_report(
    cluster_report: ClusterReport,
    cluster_records: list[dict[str, Any]],
    classifier_report: ClassifierReport,
    n_total: int,
    n_losers: int,
    n_h2: int,
    most_actionable_id: int,
    *,
    sklearn_used: bool,
    label: str = "all",
) -> str:
    lines: list[str] = []
    title_suffix = "" if label == "all" else f" ({label})"
    lines.append(f"# K53 Loser Anti-Pattern Report{title_suffix}")
    lines.append("")
    lines.append(
        f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}_"
    )
    lines.append("")
    if label != "all":
        lines.append(
            f"**Source-stratified pass:** rows restricted to "
            f"`source == {label!r}`. F3 mandate (post-K53 confound diagnosis): "
            "the original mixed-source K53 had train AUC 0.996 → H2 holdout "
            "0.598 because the joined matrix let Phase 1 vs Tier 2 schema "
            "differences leak into the labels. This pass clusters and trains "
            "WITHIN a single source so schema differences cannot drive the "
            "result."
        )
        lines.append("")
    lines.append("## Population")
    lines.append("")
    lines.append(f"- Pass label: **{label}**")
    lines.append(f"- Total filled CANDIDATEs: **{n_total}**")
    lines.append(f"- Losers (realized R ≤ 0): **{n_losers}**")
    lines.append(f"- H2-2026 losers in window: **{n_h2}**")
    lines.append(f"- sklearn used: **{sklearn_used}**")
    lines.append("")
    lines.append(
        f"## Loser anti-pattern clusters (k={cluster_report.k}, "
        f"silhouette={cluster_report.silhouette:.3f})"
    )
    lines.append("")
    lines.append(
        "| Cluster | n | Top 3 features (centroid, deviation vs population) | "
        "Mean R | WR within | H2-2026 frequency in cluster |"
    )
    lines.append("|--------:|--:|---|--:|--:|--:|")
    for rec in cluster_records:
        feat_str = "<br>".join(
            [
                f"{f['name']}: {f['centroid_value']:+.3f} "
                f"(Δ={f['deviation_from_population']:+.3f})"
                for f in rec["top_3_distinguishing_features"]
            ]
        )
        lines.append(
            f"| {rec['cluster_id']} | {rec['n']} | {feat_str} | "
            f"{rec['mean_realized_r']:+.3f} | 0.000 | "
            f"{rec['h2_2026_frequency_within_cluster']:.3f} |"
        )
    lines.append("")
    lines.append("### Silhouette by k")
    lines.append("")
    lines.append("| k | silhouette |")
    lines.append("|--:|--:|")
    for k in sorted(cluster_report.silhouette_by_k):
        lines.append(f"| {k} | {cluster_report.silhouette_by_k[k]:.3f} |")
    lines.append("")
    lines.append("## Loss classifier")
    lines.append("")
    lines.append(f"- Classifier type: `{classifier_report.classifier_type}`")
    lines.append(f"- Train AUC: **{classifier_report.train_auc:.3f}**")
    lines.append(
        f"- Held-out (random split, n={classifier_report.n_test}) "
        f"AUC: **{classifier_report.test_auc:.3f}**"
    )
    lines.append(
        f"- Held-out (H2-2026 time slice, n={classifier_report.holdout_n}) "
        f"AUC: **{classifier_report.holdout_auc:.3f}**"
    )
    lines.append(
        f"- Regime-stationarity ratio (holdout / random-test): "
        f"**{classifier_report.regime_stationarity_ratio:.3f}**"
    )
    lines.append("")
    lines.append("### Top 5 features by importance")
    lines.append("")
    lines.append("| # | feature | importance |")
    lines.append("|--:|---|--:|")
    for i, (name, w) in enumerate(classifier_report.feature_importance[:5], 1):
        lines.append(f"| {i} | {name} | {w:.4f} |")
    lines.append("")

    # Strategic verdict.
    lines.append("## Strategic verdict")
    lines.append("")
    silh = cluster_report.silhouette
    if silh >= 0.5:
        verdict = "yes (strong cluster structure)"
    elif silh >= 0.25:
        verdict = "partial (moderate cluster structure)"
    else:
        verdict = "no (weak cluster structure — losses do not separate cleanly)"
    lines.append(f"- Distinct anti-patterns identified: **{verdict}**")
    most_actionable = next(
        (c for c in cluster_records if c["cluster_id"] == most_actionable_id),
        cluster_records[0] if cluster_records else None,
    )
    if most_actionable is not None:
        feat_summary = ", ".join(
            f"{f['name']} {f['deviation_from_population']:+.2f}"
            for f in most_actionable["top_3_distinguishing_features"]
        )
        lines.append(
            f"- Most actionable cluster (highest H2-2026 frequency): "
            f"**Cluster {most_actionable['cluster_id']}** "
            f"(n={most_actionable['n']}, "
            f"H2 freq={most_actionable['h2_2026_frequency_within_cluster']:.2f}) "
            f"— {feat_summary}"
        )
    if classifier_report.regime_stationarity_ratio < 0.85:
        decay_note = (
            " The held-out time-slice AUC dropped substantially below "
            "the random-split AUC — this is the SYSTEM_DECAY signature: "
            "anti-patterns from H1 do not generalize to H2."
        )
    else:
        decay_note = (
            " Held-out time-slice AUC is comparable to random-split AUC, "
            "suggesting anti-patterns are stable across H1 / H2."
        )
    lines.append(f"- Reasoning:{decay_note}")
    lines.append("")
    lines.append(
        "## Handoff to K54\n\n"
        "The clusters above become K54's feature-engineering hints — the "
        "trained ML classifier should attend to the highest-importance "
        "features surfaced here AND the per-cluster centroid signatures."
    )
    return "\n".join(lines) + "\n"


# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="K53 — Loser Anti-Pattern Classifier"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory (e.g. research/edge_decomposition/K53_anti_pattern)",
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help=(
            "Input jsonl path (default: "
            "research/accepted_candidates_loser_mining/unified_filled_cands.jsonl)"
        ),
    )
    parser.add_argument(
        "--k-min",
        type=int,
        default=3,
        help="Minimum k to search (default: 3)",
    )
    parser.add_argument(
        "--k-max",
        type=int,
        default=7,
        help="Maximum k to search (default: 7)",
    )
    parser.add_argument(
        "--no-sklearn",
        action="store_true",
        help="Force in-house numerical path even when sklearn is installed.",
    )
    parser.add_argument(
        "--time-slice",
        default="2026-03-01T00:00:00+00:00",
        help=(
            "ISO timestamp marking the start of the held-out test slice. "
            "Rows with timestamp >= this value go to holdout. "
            "Default: 2026-03-01 (= start of H2-2026)."
        ),
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--source-filter",
        choices=["phase1", "tier2", "all"],
        default="all",
        help=(
            "F3 source-stratified mode: restrict the analysis to rows whose "
            "``source`` tag matches the filter. ``phase1`` = full-MSO XAUUSD/"
            "USDJPY rows (75 filled CANDs). ``tier2`` = parsed AI-response only "
            "(142 rows). ``all`` (default) = original mixed-source K53 run "
            "kept for parity with commit 2d3afa4 — known confound."
        ),
    )
    parser.add_argument(
        "--per-source",
        action="store_true",
        help=(
            "F3 per-source mode: run K53 independently for each source tag "
            "encountered in the data. Writes <output-dir>/<source>/{clusters."
            "json, classifier_metrics.json, anti_pattern_report.md, "
            "feature_matrix.json} plus a top-level per_source_summary.json. "
            "Mutually exclusive with --source-filter (use that flag for a "
            "single-source pass). Sources with < 8 losers / < 20 total are "
            "skipped to keep AUCs honest."
        ),
    )
    parser.add_argument(
        "--min-losers-per-source",
        type=int,
        default=8,
        help=(
            "Minimum losers needed to attempt clustering within a source "
            "during --per-source mode (default 8)."
        ),
    )
    parser.add_argument(
        "--min-rows-per-source",
        type=int,
        default=20,
        help=(
            "Minimum total rows needed to attempt classifier training within "
            "a source during --per-source mode (default 20)."
        ),
    )
    return parser


def _build_features(
    rows: list[dict[str, Any]],
) -> tuple[
    list[list[float]],
    list[int],
    list[Optional[datetime]],
    list[float],
    list[dict[str, Any]],
    list[str],
]:
    """Project loaded rows to (X, y, ts, realized_r, kept_rows, sources).

    Skips rows where feature extraction throws (with a logger warning).
    Returns parallel lists ready for downstream clustering / classification.
    """
    X: list[list[float]] = []
    y: list[int] = []
    ts: list[Optional[datetime]] = []
    realized_r: list[float] = []
    kept_rows: list[dict[str, Any]] = []
    sources: list[str] = []
    for r in rows:
        try:
            feat = _row_to_features(r)
        except Exception as e:
            logger.warning("skip row: feature extraction failed: %s", e)
            continue
        rmult = float(r["r_multiple"])
        is_loss = 1 if rmult <= 0 else 0
        X.append(feat)
        y.append(is_loss)
        realized_r.append(rmult)
        ts.append(parse_iso_timestamp(r.get("timestamp")))
        kept_rows.append(r)
        sources.append(str(r.get("source") or "unknown"))
    return X, y, ts, realized_r, kept_rows, sources


def _run_single_pass(
    *,
    out_dir: Path,
    in_path: Path,
    label: str,
    X: list[list[float]],
    y: list[int],
    ts: list[Optional[datetime]],
    realized_r: list[float],
    kept_rows: list[dict[str, Any]],
    cutoff: datetime,
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Run cluster + classifier pipeline on a fully-prepared subset.

    Writes ``clusters.json`` + ``classifier_metrics.json`` +
    ``feature_matrix.json`` + ``anti_pattern_report.md`` under ``out_dir``.

    Parameters
    ----------
    out_dir : Path
        Output directory (created if missing).
    in_path : Path
        Source jsonl path (recorded in metadata only).
    label : str
        Pass label (e.g. ``"all"``, ``"phase1"``, ``"tier2"``) — surfaces
        in the report header so multi-pass runs are self-describing.
    X, y, ts, realized_r, kept_rows :
        Already-extracted parallel rows.
    cutoff : datetime
        Time-slice cutoff (typically 2026-03-01 H2 boundary).
    args : argparse.Namespace
        CLI arguments (k_min, k_max, no_sklearn, seed, time_slice).

    Returns
    -------
    dict[str, Any]
        Summary dict suitable for aggregation in --per-source mode.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    n_total = len(X)
    n_losers = sum(y)
    n_wins = n_total - n_losers

    if n_total == 0:
        logger.warning("[%s] empty pass — writing empty marker", label)
        (out_dir / "clusters.json").write_text(
            json.dumps(
                {
                    "metadata": {
                        "label": label,
                        "input_path": str(in_path),
                        "n_total": 0,
                        "skipped": True,
                        "reason": "no rows after filtering",
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return {
            "label": label,
            "n_total": 0,
            "skipped": True,
            "reason": "no rows after filtering",
        }

    n_h2 = sum(
        1 for i, t in enumerate(ts) if t is not None and t >= cutoff and y[i] == 1
    )

    loser_X = [X[i] for i in range(n_total) if y[i] == 1]
    loser_r = [realized_r[i] for i in range(n_total) if y[i] == 1]
    loser_ts = [ts[i] for i in range(n_total) if y[i] == 1]

    if len(loser_X) < args.k_min:
        logger.warning(
            "[%s] not enough losers (%d) for k_min=%d — skipping cluster step",
            label, len(loser_X), args.k_min,
        )
        cluster_report = None
        cluster_records: list[dict[str, Any]] = []
        most_actionable_id = -1
    else:
        # Clamp k_max for tiny populations so cluster_losers does not raise.
        k_max_eff = min(args.k_max, max(args.k_min, len(loser_X) - 1))
        cluster_report = cluster_losers(
            loser_X,
            k_range=(args.k_min, k_max_eff),
            feature_names=FEATURE_NAMES,
            realized_r=loser_r,
            seed=args.seed,
            prefer_sklearn=not args.no_sklearn,
        )
        h2_freq = cluster_frequency_in_window(
            cluster_report.labels,
            loser_ts,
            window_start=cutoff,
            n_clusters=cluster_report.k,
        )
        loser_indices_in_full = [i for i in range(n_total) if y[i] == 1]
        cluster_indices: dict[int, list[int]] = {
            c: [] for c in range(cluster_report.k)
        }
        for j, c in enumerate(cluster_report.labels):
            cluster_indices[c].append(loser_indices_in_full[j])
        cluster_records = []
        for cid in range(cluster_report.k):
            cluster_records.append(
                cluster_to_record(
                    cid,
                    cluster_report,
                    kept_rows,
                    cluster_indices[cid],
                    h2_freq,
                    X,
                )
            )
        most_actionable_id = (
            max(
                cluster_records,
                key=lambda r: (r["h2_2026_frequency_within_cluster"], r["n"]),
            )["cluster_id"]
            if cluster_records
            else -1
        )

    # Classifier
    classifier_report: Optional[ClassifierReport] = None
    if len(set(y)) >= 2:
        try:
            classifier_report = train_loss_classifier(
                X,
                y,
                feature_names=FEATURE_NAMES,
                timestamps=ts,
                time_slice_split=cutoff,
                classifier=(
                    "gradient_boosting"
                    if not args.no_sklearn
                    else "logistic_regression"
                ),
                seed=args.seed,
                prefer_sklearn=not args.no_sklearn,
            )
        except ValueError as e:
            logger.warning("[%s] classifier training failed: %s", label, e)
    else:
        logger.warning(
            "[%s] cannot train classifier — only one class present", label
        )

    clusters_doc: dict[str, Any] = {
        "metadata": {
            "label": label,
            "input_path": str(in_path),
            "n_total": n_total,
            "n_wins": n_wins,
            "n_losers": n_losers,
            "n_h2_losers": n_h2,
            "time_slice_cutoff": args.time_slice,
            "seed": args.seed,
        },
    }
    if cluster_report is not None:
        clusters_doc["metadata"].update(
            {
                "k": cluster_report.k,
                "silhouette": round(cluster_report.silhouette, 4),
                "silhouette_by_k": {
                    str(k): round(v, 4)
                    for k, v in cluster_report.silhouette_by_k.items()
                },
                "feature_names": cluster_report.feature_names,
                "sklearn_used": cluster_report.sklearn_used,
                "converged": cluster_report.converged,
                "n_init": cluster_report.n_init,
                "most_actionable_cluster_id": most_actionable_id,
            }
        )
        clusters_doc["clusters"] = cluster_records
        clusters_doc["population_centroid"] = {
            n: round(v, 4)
            for n, v in zip(
                cluster_report.feature_names, cluster_report.population_centroid
            )
        }
    else:
        clusters_doc["metadata"]["skipped_clustering"] = True

    classifier_doc: dict[str, Any] = {
        "metadata": {
            "label": label,
            "input_path": str(in_path),
            "n_total": n_total,
            "n_wins": n_wins,
            "n_losers": n_losers,
            "time_slice_cutoff": args.time_slice,
            "seed": args.seed,
        }
    }
    if classifier_report is not None:
        classifier_doc["metadata"].update(
            {
                "feature_names": classifier_report.feature_names,
                "classifier_type": classifier_report.classifier_type,
                "n_train": classifier_report.n_train,
                "n_test": classifier_report.n_test,
                "n_holdout": classifier_report.holdout_n,
                "sklearn_used": classifier_report.sklearn_used,
                "converged": classifier_report.converged,
            }
        )
        classifier_doc["metrics"] = {
            "train_auc": round(classifier_report.train_auc, 4),
            "test_auc": round(classifier_report.test_auc, 4),
            "holdout_auc": round(classifier_report.holdout_auc, 4),
            "regime_stationarity_ratio": round(
                classifier_report.regime_stationarity_ratio, 4
            ),
        }
        classifier_doc["feature_importance"] = [
            {"feature": name, "importance": round(w, 6)}
            for name, w in classifier_report.feature_importance
        ]
    else:
        classifier_doc["metadata"]["skipped_classifier"] = True

    feature_matrix_doc = {
        "metadata": {
            "label": label,
            "input_path": str(in_path),
            "n_total": n_total,
            "feature_names": FEATURE_NAMES,
        },
        "rows": [
            {
                "symbol": kept_rows[i]["symbol"],
                "source": kept_rows[i].get("source", "unknown"),
                "timestamp": kept_rows[i].get("timestamp"),
                "is_loss": y[i],
                "realized_r": realized_r[i],
                "features": X[i],
            }
            for i in range(n_total)
        ],
    }

    (out_dir / "clusters.json").write_text(
        json.dumps(clusters_doc, indent=2, sort_keys=False), encoding="utf-8"
    )
    (out_dir / "classifier_metrics.json").write_text(
        json.dumps(classifier_doc, indent=2, sort_keys=False), encoding="utf-8"
    )
    (out_dir / "feature_matrix.json").write_text(
        json.dumps(feature_matrix_doc, indent=2, sort_keys=False), encoding="utf-8"
    )
    if cluster_report is not None and classifier_report is not None:
        (out_dir / "anti_pattern_report.md").write_text(
            render_markdown_report(
                cluster_report,
                cluster_records,
                classifier_report,
                n_total,
                n_losers,
                n_h2,
                most_actionable_id,
                sklearn_used=cluster_report.sklearn_used,
                label=label,
            ),
            encoding="utf-8",
        )
    else:
        (out_dir / "anti_pattern_report.md").write_text(
            f"# K53 Loser Anti-Pattern Report ({label})\n\n"
            f"**Skipped** — n_total={n_total}, n_losers={n_losers}, "
            f"cluster_report={'present' if cluster_report else 'missing'}, "
            f"classifier_report="
            f"{'present' if classifier_report else 'missing'}.\n",
            encoding="utf-8",
        )

    logger.info("[%s] wrote outputs to %s", label, out_dir)

    summary = {
        "label": label,
        "n_total": n_total,
        "n_wins": n_wins,
        "n_losers": n_losers,
        "n_h2_losers": n_h2,
        "skipped": False,
    }
    if cluster_report is not None:
        summary["cluster_k"] = cluster_report.k
        summary["cluster_silhouette"] = round(cluster_report.silhouette, 4)
    if classifier_report is not None:
        summary["train_auc"] = round(classifier_report.train_auc, 4)
        summary["test_auc"] = round(classifier_report.test_auc, 4)
        summary["holdout_auc"] = round(classifier_report.holdout_auc, 4)
        summary["regime_stationarity_ratio"] = round(
            classifier_report.regime_stationarity_ratio, 4
        )
        summary["classifier_type"] = classifier_report.classifier_type
        summary["n_train"] = classifier_report.n_train
        summary["n_test"] = classifier_report.n_test
        summary["n_holdout"] = classifier_report.holdout_n
    return summary


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.per_source and args.source_filter != "all":
        logger.error(
            "--per-source and --source-filter are mutually exclusive "
            "(use --source-filter for a single-source pass; --per-source "
            "for independent runs across all sources)"
        )
        return 4

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    in_path = Path(args.input)
    if not in_path.is_absolute():
        in_path = _PROJECT_ROOT / in_path

    rows = load_unified_jsonl(in_path)
    if not rows:
        logger.error("no rows loaded — aborting")
        return 1

    cutoff = parse_iso_timestamp(args.time_slice)
    if cutoff is None:
        logger.error("invalid --time-slice: %r", args.time_slice)
        return 2

    X, y, ts, realized_r, kept_rows, sources = _build_features(rows)
    n_total = len(X)
    n_losers = sum(y)
    n_wins = n_total - n_losers
    logger.info(
        "loaded n=%d (wins=%d, losses=%d) from %s",
        n_total, n_wins, n_losers, in_path,
    )

    # Source distribution log line — surfaces the schema split for the operator.
    src_counts: dict[str, int] = {}
    for s in sources:
        src_counts[s] = src_counts.get(s, 0) + 1
    logger.info("source distribution: %s", src_counts)

    # ── Mode 1: --per-source (independent runs per source tag) ────────────────
    if args.per_source:
        per_source_summary: list[dict[str, Any]] = []
        # Deterministic ordering for reproducible aggregate JSON.
        for src in sorted(src_counts.keys()):
            sub_idx = [i for i in range(n_total) if sources[i] == src]
            sub_X = [X[i] for i in sub_idx]
            sub_y = [y[i] for i in sub_idx]
            sub_ts = [ts[i] for i in sub_idx]
            sub_r = [realized_r[i] for i in sub_idx]
            sub_rows = [kept_rows[i] for i in sub_idx]
            n_sub_losers = sum(sub_y)
            if (
                len(sub_idx) < args.min_rows_per_source
                or n_sub_losers < args.min_losers_per_source
            ):
                logger.info(
                    "skip source=%s (n=%d, losers=%d) below thresholds "
                    "(min_rows=%d, min_losers=%d)",
                    src, len(sub_idx), n_sub_losers,
                    args.min_rows_per_source, args.min_losers_per_source,
                )
                per_source_summary.append({
                    "label": src,
                    "n_total": len(sub_idx),
                    "n_losers": n_sub_losers,
                    "skipped": True,
                    "reason": "below min_rows or min_losers threshold",
                })
                continue
            sub_dir = out_dir / src
            summary = _run_single_pass(
                out_dir=sub_dir,
                in_path=in_path,
                label=src,
                X=sub_X,
                y=sub_y,
                ts=sub_ts,
                realized_r=sub_r,
                kept_rows=sub_rows,
                cutoff=cutoff,
                args=args,
            )
            per_source_summary.append(summary)

        agg_doc = {
            "metadata": {
                "input_path": str(in_path),
                "mode": "per_source",
                "n_total": n_total,
                "n_losers": n_losers,
                "n_sources": len(src_counts),
                "source_distribution": src_counts,
                "time_slice_cutoff": args.time_slice,
                "seed": args.seed,
                "min_rows_per_source": args.min_rows_per_source,
                "min_losers_per_source": args.min_losers_per_source,
            },
            "per_source": per_source_summary,
        }
        (out_dir / "per_source_summary.json").write_text(
            json.dumps(agg_doc, indent=2, sort_keys=False), encoding="utf-8"
        )
        logger.info("wrote per-source aggregate to %s", out_dir / "per_source_summary.json")
        for s in per_source_summary:
            if s.get("skipped"):
                logger.info(
                    "  source=%s SKIPPED (%s)", s["label"], s.get("reason")
                )
            else:
                logger.info(
                    "  source=%s n=%d losers=%d test_auc=%.3f holdout_auc=%.3f",
                    s["label"],
                    s["n_total"],
                    s["n_losers"],
                    s.get("test_auc", float("nan")),
                    s.get("holdout_auc", float("nan")),
                )
        return 0

    # ── Mode 2: --source-filter (single pass on filtered subset) ──────────────
    if args.source_filter != "all":
        keep = [i for i in range(n_total) if sources[i] == args.source_filter]
        if not keep:
            logger.error(
                "no rows match --source-filter=%s (sources present: %s)",
                args.source_filter, sorted(src_counts.keys()),
            )
            return 5
        X = [X[i] for i in keep]
        y = [y[i] for i in keep]
        ts = [ts[i] for i in keep]
        realized_r = [realized_r[i] for i in keep]
        kept_rows = [kept_rows[i] for i in keep]
        logger.info(
            "applied --source-filter=%s → kept n=%d (losers=%d)",
            args.source_filter, len(X), sum(y),
        )

    label = (
        args.source_filter
        if args.source_filter != "all"
        else "all"
    )
    summary = _run_single_pass(
        out_dir=out_dir,
        in_path=in_path,
        label=label,
        X=X,
        y=y,
        ts=ts,
        realized_r=realized_r,
        kept_rows=kept_rows,
        cutoff=cutoff,
        args=args,
    )
    if summary.get("skipped"):
        return 3
    logger.info(
        "label=%s k=%s silhouette=%s train_auc=%s test_auc=%s holdout_auc=%s",
        summary.get("label"),
        summary.get("cluster_k"),
        summary.get("cluster_silhouette"),
        summary.get("train_auc"),
        summary.get("test_auc"),
        summary.get("holdout_auc"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
