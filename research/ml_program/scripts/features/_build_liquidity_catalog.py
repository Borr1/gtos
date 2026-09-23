"""Generate `liquidity.csv` (per-feature tabular catalog).

Reads `liquidity_stability_scores.json` and the canonical column list
from `liquidity.feature_names()`, and emits a CSV row per feature with
columns: family, feature_name, source, lookback, comment, n, rho,
abs_rho, tied_pct.

Idempotent. Run after `_score_liquidity_stability.py`.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "research" / "ml_program" / "scripts" / "features"))
import liquidity  # type: ignore  # noqa: E402

SCORES_PATH = REPO_ROOT / "research" / "ml_program" / "feature_catalogs" / "liquidity_stability_scores.json"
CSV_PATH = REPO_ROOT / "research" / "ml_program" / "feature_catalogs" / "liquidity.csv"


def categorize(name: str) -> tuple[str, str, str]:
    """Return (sub_family, source, lookback) tag for a feature name."""
    src_eq = "_detect_equal_levels (mirror data_ingestion.py:301-330)"
    src_sweep = "_detect_sweeps_against_swings + _detect_swings_local (mirror market_state.py:887-932 + 187-219)"
    src_round = "_round_number_features (Osler 2000-2005 round-number magnetism)"
    src_stop = "_stop_cluster_features (proxy from _detect_swings_local)"
    src_vol = "_volume_cluster_features"
    src_pool = "_liquidity_pool_density (combines swings + equal-levels)"
    src_prior = "_prior_period_features (PDH/PDL/PWH/PWL/PMH/PML)"
    src_retest = "_swept_retest_features"
    src_magnet = "_price_magnet_score (composite)"

    # Per-TF lookback labels
    lb_m15 = f"M15 {liquidity.LOOKBACK_BY_TF['M15']} bars"
    lb_h1 = f"H1 {liquidity.LOOKBACK_BY_TF['H1']} bars"
    lb_h4 = f"H4 {liquidity.LOOKBACK_BY_TF['H4']} bars"
    sweep_lb_m15 = f"M15 sweep_lb={liquidity.SWEEP_LOOKBACK_BY_TF['M15']} bars"
    sweep_lb_h1 = f"H1 sweep_lb={liquidity.SWEEP_LOOKBACK_BY_TF['H1']} bars"
    sweep_lb_h4 = f"H4 sweep_lb={liquidity.SWEEP_LOOKBACK_BY_TF['H4']} bars"

    if "_eqh_" in name or "_eql_" in name or "_dist_eqh" in name or "_dist_eql" in name:
        sub = "equal_levels"
        src = src_eq
        lb = lb_m15 if "_M15_" in name else lb_h1 if "_H1_" in name else lb_h4
    elif "_sweep_" in name or "_bars_since_sweep" in name:
        sub = "sweep"
        src = src_sweep
        lb = sweep_lb_m15 if "_M15_" in name else sweep_lb_h1 if "_H1_" in name else sweep_lb_h4
    elif "_swept_retest_" in name:
        sub = "swept_retest"
        src = src_retest
        lb = sweep_lb_m15 if "_M15_" in name else sweep_lb_h1 if "_H1_" in name else sweep_lb_h4
    elif "_stopcluster_" in name:
        sub = "stop_cluster"
        src = src_stop
        lb = lb_m15 if "_M15_" in name else lb_h1 if "_H1_" in name else lb_h4
    elif "_volcluster_" in name:
        sub = "volume_cluster"
        src = src_vol
        lb = lb_m15 if "_M15_" in name else lb_h1 if "_H1_" in name else lb_h4
    elif "_pooldensity_" in name:
        sub = "liquidity_pool_density"
        src = src_pool
        lb = lb_m15 if "_M15_" in name else lb_h1 if "_H1_" in name else lb_h4
    elif name.startswith("liq_round_"):
        sub = "round_number"
        src = src_round
        lb = "single (anchor only)"
    elif "liq_dist_pdh" in name or "liq_dist_pdl" in name:
        sub = "prior_day"
        src = src_prior
        lb = "H1 24-bar prior day"
    elif "liq_dist_pwh" in name or "liq_dist_pwl" in name:
        sub = "prior_week"
        src = src_prior
        lb = "H4 24-bar prior week"
    elif "liq_dist_pmh" in name or "liq_dist_pml" in name:
        sub = "prior_month"
        src = src_prior
        lb = "H4 120-bar prior month"
    elif name.startswith("liq_magnet_"):
        sub = "price_magnet"
        src = src_magnet
        lb = "composite (uses other liq_ features)"
    else:
        sub = "other"
        src = "?"
        lb = "?"
    return sub, src, lb


def comment_for(name: str, score: dict) -> str:
    rho = score.get("rho")
    n = score.get("n", 0)
    tied = score.get("tied_pct", 0.0)
    rho_str = f"rho={rho:+.4f}" if rho is not None else "rho=NaN"
    bits = [rho_str, f"n={n}", f"tied={tied:.0%}"]
    if rho is None:
        bits.append("UNDERPOWERED")
    if tied is not None and tied > 0.85:
        bits.append("WARN: near-constant")
    if "round_" in name:
        levels_match = name.split("_")[2] if len(name.split("_")) > 2 else "?"
        bits.append(f"applicable to instruments whose price-magnitude makes {levels_match.replace('p','.')} a meaningful rung")
    return ", ".join(bits)


def main():
    with open(SCORES_PATH) as f:
        scores_data = json.load(f)
    scores = scores_data["scores"]
    names = liquidity.feature_names()
    rows = []
    for name in names:
        sub, src, lb = categorize(name)
        score = scores.get(name, {})
        rows.append({
            "family": "liquidity",
            "sub_family": sub,
            "feature_name": name,
            "source": src,
            "lookback": lb,
            "n": score.get("n", 0),
            "spearman_rho": score.get("rho"),
            "abs_rho": score.get("abs_rho"),
            "tied_pct": round(score.get("tied_pct", 0.0), 4) if score.get("tied_pct") is not None else None,
            "comment": comment_for(name, score),
        })
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "family", "sub_family", "feature_name", "source", "lookback",
            "n", "spearman_rho", "abs_rho", "tied_pct", "comment",
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"Wrote {len(rows)} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
