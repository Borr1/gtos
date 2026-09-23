"""
C-1 Coval-Shumway second-half-of-session OB-retest audit.

Pre-registered hypothesis (see research/ml_program/experiments/c1_coval_shumway_second_half.md):

  OB-retest entries in the second half of a kill-zone (split at the kill-zone
  midpoint per CLAUDE.md kill-zone schedule) achieve realized-R mean >= +0.05R
  higher than first-half entries on the post-2022-2023-backfill cohort
  (n ~ 2,326), with stationary block bootstrap p < 0.05 (DSR-corrected for
  ~10 stratifications). Sign of the difference must be positive on >=3 of 4
  effective instrument groups.

Run:
    python scripts/research/c1_coval_shumway_audit.py

Outputs:
    research/ml_program/experiments/c1_coval_shumway_results.json

READ-ONLY against src/, config/, knowledge_base/,
pipeline_state/. Writes ONLY into research/ml_program/experiments/.
"""

from __future__ import annotations

import json
import math
import random
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Paths (absolute; matches dispatch brief).
# ----------------------------------------------------------------------------
REPO_ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
COHORT_2022_2023 = REPO_ROOT / "data" / "historical_2022_2023" / "trade_cohort.csv"
COHORT_K54_FULL = REPO_ROOT / "research" / "ml_program" / "models" / "k54_v1_features_full.csv"
OUT_JSON = REPO_ROOT / "research" / "ml_program" / "experiments" / "c1_coval_shumway_results.json"
OUT_MD = REPO_ROOT / "research" / "ml_program" / "experiments" / "c1_coval_shumway_second_half.md"

SEED = 42
B_BOOTSTRAP = 1000
DSR_TRIAL_COUNT = 10  # per dispatch brief

# ----------------------------------------------------------------------------
# Kill-zone schedule (UTC; from CLAUDE.md). Hours are integer UTC start hours.
# `first` is the set of `hour_utc` values landing in the first half of the KZ,
# `second` is the set in the second half (midpoint into the second half).
#
# All kill-zone widths are short enough that we map at integer-hour granularity;
# hour boundaries containing the midpoint are placed in second-half by convention
# when the midpoint is :00 (e.g. XAU NY mid 15:00), and in first-half when the
# midpoint is :15/:30/:45 inside the integer hour (conservative against the
# hypothesis).
# ----------------------------------------------------------------------------
KZ_SCHEDULE: Dict[str, Dict[str, Dict[str, set]]] = {
    "XAUUSD": {
        "london": {"first": {7, 8}, "second": {9, 10}},  # 07:00-10:30, mid 08:45
        "ny": {"first": {13, 14}, "second": {15, 16}},   # 13:00-17:00 (skip 13:00-13:15), mid 15:00
    },
    "XAGUSD": {  # proxy XAU
        "london": {"first": {7, 8}, "second": {9, 10}},
        "ny": {"first": {13, 14}, "second": {15, 16}},
    },
    "US30": {
        "london": {"first": {8, 9}, "second": {10}},      # 08:00-10:30, mid 09:15
        "ny": {"first": {13, 14}, "second": {15}},        # 13:30-16:00, mid 14:45
    },
    "US30_CASH": {  # alias for US30
        "london": {"first": {8, 9}, "second": {10}},
        "ny": {"first": {13, 14}, "second": {15}},
    },
    "NAS100": {  # proxy US30
        "london": {"first": {8, 9}, "second": {10}},
        "ny": {"first": {13, 14}, "second": {15}},
    },
    "USDJPY": {
        "london": {"first": {7, 8}, "second": {9}},       # 07:00-09:30, mid 08:15
        "ny": {"first": {13, 14}, "second": {15}},        # 13:00-15:30, mid 14:15
        "tokyo": {"first": {0, 1}, "second": {2}},        # 00:00-03:00, mid 01:30
    },
    "GBPJPY": {
        "london": {"first": {7, 8}, "second": {9}},
        "ny": {"first": {13, 14}, "second": {15}},
        "tokyo": {"first": {0, 1}, "second": {2}},
    },
    "GBPUSD": {
        "london": {"first": {7, 8, 9}, "second": {10, 11}},  # 07:00-12:00, mid 09:30
        "ny": {"first": {13, 14}, "second": {15}},           # 13:00-15:30, mid 14:15
    },
}

# Effective instrument groups for sign-count promotion gate.
INSTR_GROUPS = OrderedDict([
    ("XAU_XAG", {"XAUUSD", "XAGUSD"}),
    ("INDEX", {"NAS100", "US30_CASH", "US30"}),
    ("GBPJPY", {"GBPJPY"}),
    ("USD_FX", {"GBPUSD", "USDJPY"}),
])


def label_half(row: pd.Series) -> str:
    """Return 'first', 'second', or '' if outside the KZ window."""
    sym = row["symbol"]
    kz = row["kill_zone"]
    hour = int(row["hour_utc"])
    if sym not in KZ_SCHEDULE:
        return ""
    if kz not in KZ_SCHEDULE[sym]:
        return ""
    table = KZ_SCHEDULE[sym][kz]
    if hour in table["first"]:
        return "first"
    if hour in table["second"]:
        return "second"
    return ""


def load_cohort() -> pd.DataFrame:
    """Load + dedupe both cohorts; return frame with `half` and `instr_group` columns set."""
    parts = []
    if COHORT_2022_2023.exists():
        d1 = pd.read_csv(COHORT_2022_2023)
        parts.append(d1)
    if COHORT_K54_FULL.exists():
        d2 = pd.read_csv(COHORT_K54_FULL)
        parts.append(d2)
    if not parts:
        raise FileNotFoundError("Neither cohort file found.")
    df = pd.concat(parts, ignore_index=True)
    df = df.drop_duplicates(subset="trade_id").reset_index(drop=True)

    # Filter to OB-retest framework; drop nulls / zero-r rows
    df = df[df["framework"] == "ob_retest"].copy()
    df = df.dropna(subset=["realized_r", "hour_utc", "kill_zone", "symbol"]).copy()
    df["hour_utc"] = df["hour_utc"].astype(int)

    # Map half
    df["half"] = df.apply(label_half, axis=1)
    df = df[df["half"] != ""].copy()

    # Map instrument group
    def _grp(sym: str) -> str:
        for g, members in INSTR_GROUPS.items():
            if sym in members:
                return g
        return "OTHER"
    df["instr_group"] = df["symbol"].apply(_grp)
    df = df[df["instr_group"] != "OTHER"].copy()

    # Sort by date_iso for AR1 / block bootstrap stationarity
    df["dt"] = pd.to_datetime(df["date_iso"], errors="coerce", utc=True)
    df = df.sort_values("dt").reset_index(drop=True)
    return df


def lag1_autocorr(x: np.ndarray) -> float:
    if len(x) < 3:
        return 0.0
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    num = np.sum(x[:-1] * x[1:])
    den = np.sum(x ** 2)
    if den == 0:
        return 0.0
    rho = num / den
    if not np.isfinite(rho):
        return 0.0
    return float(max(-0.99, min(0.99, rho)))


def block_size_for(rho: float, floor: int = 5) -> int:
    """Politis-Romano stationary-block size heuristic; for AR1 process,
    1 / (1 - rho) approximates the de-correlation lag. We floor at 5."""
    if rho <= 0:
        return floor
    return max(floor, int(math.ceil(1.0 / max(1e-6, 1.0 - rho))))


def stationary_block_bootstrap(
    r_first: np.ndarray,
    r_second: np.ndarray,
    block: int,
    B: int,
    rng: random.Random,
) -> Tuple[float, float, np.ndarray]:
    """Politis-Romano stationary block bootstrap on the difference of means.

    Strategy: paired bootstrap by half — bootstrap each half from its own
    series with stationary blocks of mean length `block`.
    Returns (delta_obs, two_sided_p, replicate_array).
    """
    delta_obs = float(np.mean(r_second) - np.mean(r_first))

    n1 = len(r_first)
    n2 = len(r_second)
    if n1 == 0 or n2 == 0:
        return delta_obs, float("nan"), np.array([])

    p_geom = 1.0 / max(1, block)

    np_rng = np.random.default_rng(rng.randint(0, 2**31 - 1))

    def _resample(series: np.ndarray, n: int) -> np.ndarray:
        out = np.empty(n, dtype=float)
        i = 0
        while i < n:
            start = np_rng.integers(0, len(series))
            # geometric block length
            blen = np_rng.geometric(p_geom)
            for k in range(blen):
                if i >= n:
                    break
                out[i] = series[(start + k) % len(series)]
                i += 1
        return out

    deltas = np.empty(B, dtype=float)
    for b in range(B):
        s1 = _resample(r_first, n1)
        s2 = _resample(r_second, n2)
        deltas[b] = float(np.mean(s2) - np.mean(s1))

    # Center distribution under the null delta=0 (Romano paired-bootstrap centering)
    centered = deltas - float(np.mean(deltas))
    abs_obs = abs(delta_obs)
    p_two_sided = float(np.mean(np.abs(centered) >= abs_obs))
    # Avoid p=0 for finite B; floor at 1/(B+1)
    p_two_sided = max(p_two_sided, 1.0 / (B + 1))
    return delta_obs, p_two_sided, deltas


def deflated_p(p_raw: float, n_trials: int) -> float:
    """Bonferroni-style upper bound on family-wise error after `n_trials`
    independent comparisons. We use this as a conservative DSR proxy.
    DSR (Bailey-Lopez de Prado 2014) is Sharpe-ratio-based; for a difference-
    of-means test the analytic form simplifies to a multiple-comparison
    adjustment with effective trial count. We report Bonferroni for
    transparency; document this as a conservative substitute."""
    return float(min(1.0, p_raw * n_trials))


def stratum_test(
    df: pd.DataFrame,
    label: str,
    rng: random.Random,
) -> Dict:
    """Run stationary block bootstrap on a stratum's first vs second halves."""
    first = df[df["half"] == "first"]["realized_r"].to_numpy(dtype=float)
    second = df[df["half"] == "second"]["realized_r"].to_numpy(dtype=float)
    n1 = len(first)
    n2 = len(second)
    if n1 < 2 or n2 < 2:
        return {
            "stratum": label,
            "n_first_half": n1,
            "n_second_half": n2,
            "mean_R_first": float(np.mean(first)) if n1 else float("nan"),
            "mean_R_second": float(np.mean(second)) if n2 else float("nan"),
            "diff": (float(np.mean(second) - np.mean(first)) if (n1 and n2) else float("nan")),
            "wr_first": float(np.mean(first > 0)) if n1 else float("nan"),
            "wr_second": float(np.mean(second > 0)) if n2 else float("nan"),
            "block_size": None,
            "bootstrap_p": float("nan"),
            "DSR_p": float("nan"),
            "verdict": "FAIL",
            "note": "insufficient data (<2 in either half)",
        }
    # AR1 on combined sorted r series for block-size choice
    combined = np.concatenate([first, second])
    rho = lag1_autocorr(combined)
    block = block_size_for(rho)
    delta_obs, p_raw, _ = stationary_block_bootstrap(first, second, block, B_BOOTSTRAP, rng)
    p_dsr = deflated_p(p_raw, DSR_TRIAL_COUNT)
    pass_diff = delta_obs >= 0.05
    pass_p = (p_raw < 0.05)
    pass_dsr = (p_dsr < 0.05)
    if pass_diff and pass_p and pass_dsr:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    return {
        "stratum": label,
        "n_first_half": n1,
        "n_second_half": n2,
        "mean_R_first": float(np.mean(first)),
        "mean_R_second": float(np.mean(second)),
        "diff": float(delta_obs),
        "wr_first": float(np.mean(first > 0)),
        "wr_second": float(np.mean(second > 0)),
        "ar1": rho,
        "block_size": block,
        "bootstrap_p": float(p_raw),
        "DSR_p": float(p_dsr),
        "verdict": verdict,
    }


def _format_md_row(name: str, r: Dict) -> str:
    return (
        f"| {name} "
        f"| {r['n_first_half']} "
        f"| {r['n_second_half']} "
        f"| {r['mean_R_first']:+.4f} "
        f"| {r['mean_R_second']:+.4f} "
        f"| {r['diff']:+.4f} "
        f"| {r['wr_first']*100:.1f}% "
        f"| {r['wr_second']*100:.1f}% "
        f"| {r['bootstrap_p']:.4f} "
        f"| {r['DSR_p']:.4f} "
        f"| {r['verdict']} |"
    )


def main():
    random.seed(SEED)
    np.random.seed(SEED)
    rng = random.Random(SEED)

    df = load_cohort()
    print(f"[c1] cohort rows post-filter: {len(df)} "
          f"(within-KZ-window OB-retest, half-labeled, instr_group-mapped)")

    results: Dict[str, Dict] = OrderedDict()

    # Aggregate
    results["aggregate"] = stratum_test(df, "aggregate", rng)

    # Per instrument group (sign-count gate uses these 4)
    for grp in INSTR_GROUPS.keys():
        sub = df[df["instr_group"] == grp]
        results[f"group_{grp}"] = stratum_test(sub, f"group_{grp}", rng)

    # Per kill-zone
    for kz in ["london", "ny", "tokyo"]:
        sub = df[df["kill_zone"] == kz]
        results[f"kz_{kz}"] = stratum_test(sub, f"kz_{kz}", rng)

    # Per regime
    for regime in ["bullish", "bearish", "transitional"]:
        sub = df[df["regime_tag"] == regime]
        results[f"regime_{regime}"] = stratum_test(sub, f"regime_{regime}", rng)

    # Per side
    for side in ["LONG", "SHORT"]:
        sub = df[df["direction_long_short"] == side]
        results[f"side_{side}"] = stratum_test(sub, f"side_{side}", rng)

    # Sign-count gate: across the 4 instrument groups, count sign(diff) > 0
    sign_count_pos = 0
    sign_count_total = 0
    for grp in INSTR_GROUPS.keys():
        r = results[f"group_{grp}"]
        if r["n_first_half"] >= 2 and r["n_second_half"] >= 2 and not np.isnan(r["diff"]):
            sign_count_total += 1
            if r["diff"] > 0:
                sign_count_pos += 1

    agg = results["aggregate"]
    promotion_pass = (
        (agg["diff"] >= 0.05)
        and (agg["bootstrap_p"] < 0.05)
        and (agg["DSR_p"] < 0.05)
        and (sign_count_pos >= 3)
    )

    summary = {
        "metadata": {
            "experiment_id": "C-1",
            "hypothesis_id": "H-15",
            "bundle": "B-8 quick-win",
            "date": "2026-04-29",
            "seed": SEED,
            "B_bootstrap": B_BOOTSTRAP,
            "DSR_trial_count": DSR_TRIAL_COUNT,
            "cohort_files": [
                str(COHORT_2022_2023),
                str(COHORT_K54_FULL),
            ],
            "cohort_rows_post_filter": int(len(df)),
        },
        "results": results,
        "sign_count": {
            "positive_groups": int(sign_count_pos),
            "total_evaluable_groups": int(sign_count_total),
            "groups_required": 3,
        },
        "promotion": {
            "PASS": bool(promotion_pass),
            "criteria": [
                ("aggregate diff >= +0.05R", float(agg["diff"]), bool(agg["diff"] >= 0.05)),
                ("aggregate bootstrap_p < 0.05", float(agg["bootstrap_p"]), bool(agg["bootstrap_p"] < 0.05)),
                ("aggregate DSR_p < 0.05", float(agg["DSR_p"]), bool(agg["DSR_p"] < 0.05)),
                ("sign(diff) > 0 in >= 3/4 instrument groups", f"{sign_count_pos}/{sign_count_total}", bool(sign_count_pos >= 3)),
            ],
            "verdict": "PASS" if promotion_pass else "FAIL",
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"[c1] wrote {OUT_JSON}")

    # ------------------------------------------------------------------
    # Append rendered tables to the markdown deliverable.
    # ------------------------------------------------------------------
    md_table_header = (
        "| Stratum | n_first | n_second | mean_R_first | mean_R_second | "
        "diff | WR_first | WR_second | bootstrap_p | DSR_p | verdict |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n"
    )

    def _fmt_subset(keys: List[Tuple[str, str]]) -> str:
        rows = [md_table_header]
        for k, label in keys:
            r = results[k]
            rows.append(_format_md_row(label, r) + "\n")
        return "".join(rows)

    md_aggregate = _fmt_subset([("aggregate", "aggregate")])
    md_groups = _fmt_subset([(f"group_{g}", f"group_{g}") for g in INSTR_GROUPS.keys()])
    md_kz = _fmt_subset([(f"kz_{kz}", f"kz_{kz}") for kz in ["london", "ny", "tokyo"]])
    md_reg = _fmt_subset([(f"regime_{r}", f"regime_{r}") for r in ["bullish", "bearish", "transitional"]])
    md_side = _fmt_subset([(f"side_{s}", f"side_{s}") for s in ["LONG", "SHORT"]])

    pass_str = "PASS" if promotion_pass else "FAIL"
    sign_str = f"{sign_count_pos}/{sign_count_total}"

    verdict_block = (
        f"- **Aggregate delta (mean realized-R, second minus first):** {agg['diff']:+.4f}R\n"
        f"- **Aggregate stationary-bootstrap p:** {agg['bootstrap_p']:.4f}\n"
        f"- **Aggregate DSR-corrected p (Bonferroni proxy, n_trials=10):** {agg['DSR_p']:.4f}\n"
        f"- **Sign-count gate (sign(diff) positive across the 4 instrument groups):** {sign_str} (need >=3/4)\n"
        f"- **PROMOTION VERDICT:** **{pass_str}**\n"
    )

    md_text = OUT_MD.read_text(encoding="utf-8")
    if "(Auto-generated below.)" in md_text:
        # Replace the per-section placeholders.
        md_text = md_text.replace(
            "### 3.1 Aggregate\n\n(Auto-generated below.)",
            f"### 3.1 Aggregate\n\n{md_aggregate}",
        ).replace(
            "### 3.2 Per-instrument-group\n\n(Auto-generated below.)",
            f"### 3.2 Per-instrument-group\n\n{md_groups}",
        ).replace(
            "### 3.3 Per-kill-zone\n\n(Auto-generated below.)",
            f"### 3.3 Per-kill-zone\n\n{md_kz}",
        ).replace(
            "### 3.4 Per-regime\n\n(Auto-generated below.)",
            f"### 3.4 Per-regime\n\n{md_reg}",
        ).replace(
            "### 3.5 Per-side\n\n(Auto-generated below.)",
            f"### 3.5 Per-side\n\n{md_side}",
        ).replace(
            "### 3.6 Verdict\n\n(Auto-generated below.)",
            f"### 3.6 Verdict\n\n{verdict_block}",
        )
        OUT_MD.write_text(md_text, encoding="utf-8")
        print(f"[c1] updated {OUT_MD}")

    # Emit short stdout summary
    print()
    print("=" * 80)
    print("C-1 COVAL-SHUMWAY SECOND-HALF AUDIT - SUMMARY")
    print("=" * 80)
    print(verdict_block)
    print("Per-stratum:")
    for k, r in results.items():
        print(f"  {k:20s}  n=({r['n_first_half']:>3}, {r['n_second_half']:>3})  "
              f"diff={r['diff']:+.4f}R  p={r['bootstrap_p']:.4f}  DSR_p={r['DSR_p']:.4f}  {r['verdict']}")


if __name__ == "__main__":
    main()
