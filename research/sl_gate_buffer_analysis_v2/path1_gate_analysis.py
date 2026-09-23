"""Path 1 — Gate Configuration × SL Policy Analysis.

Agent B (Opus 4.7), 2026-04-18.

Input
-----
``multi_sl_outcomes.csv`` from ``path1_multi_sl_replay.py``. One row per
(retest_event, SL_policy). Columns include outcome, r_multiple, buffer_atr
(M15), is_degenerate, side.

Computes for each cell (policy × gate_config), filtering degenerate rows:
  * admitted count
  * CONTINUED / REVERSED / UNRESOLVED counts
  * WR = CONT / (CONT + REV)    [UNRESOLVED excluded]
  * Expectancy (mean R across admitted rows, UNRESOLVED treated as 0R)
  * Expectancy excluding UNRESOLVED (mean R over resolved rows)
  * Risk-adjusted expectancy: mean (r_multiple * m15_atr / abs(entry - target))
    This accounts for the R-ratio artifact — tighter SL → bigger R but same
    price-distance-to-target.
  * Sweep-event count: REVERSED where buffer_atr < 0.3 (proxy for Apr-16-style
    sweep-past-edge pattern).

Gate configurations mirror replication_analysis.py:144-165:

  1. baseline         — no bypass (always rejects `sl_too_tight`).
  2. current_live     — framework==ob_retest AND sl_beyond_edge AND ratio >= 0.3.
  3. option_c         — framework==ob_retest AND sl_beyond_edge AND ratio <= 0.5.
  4. option_d         — framework==ob_retest AND sl_beyond_edge AND ratio <= 0.3.
  5. option_e (hybrid)— framework==ob_retest AND sl_beyond_edge AND
                        0.3 <= ratio <= 0.5.

For THIS study every admitted row is an ob_retest retest event with
`sl_beyond_edge = True` by construction (buffer positive). The
`sl_too_tight` base rule is triggered by `sl_distance < 1.5 * m15_atr`; we
evaluate this per row too, but at gate-admission time a row is counted as
"admitted" iff the gate would LET IT THROUGH, which depends on both the
tightness test and the bypass clause.

Outputs
-------
``path1_gate_cells.csv`` — one row per (policy_multiplier, gate_config).
``path1_buffer_distribution.csv`` — buffer_atr stats per policy.
``path1_per_symbol_0p5.csv`` — per-symbol breakdown at the 0.5 policy (the
   current-live equivalent).
``path1_r_distribution.csv`` — r_multiple distribution (p5/p25/p50/p75/p95,
   min/max) per policy, CONTINUED only.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "research" / "sl_gate_buffer_analysis_v2"
MULTI_PATH = OUT_DIR / "multi_sl_outcomes.csv"


CONFIGS: Tuple[str, ...] = (
    "1_baseline",
    "2_current_live",
    "3_option_c",
    "4_option_d",
    "5_option_e",
)

# 1.5 * M15 ATR is the production sl_too_tight threshold.
# If sl_distance < 1.5 * m15_atr, the base rule REJECTS unless bypass applies.
BASE_TIGHT_MULT = 1.5


def sl_distance_atr(row: dict) -> float:
    """|entry - sl| / m15_atr, used for sl_too_tight base rule evaluation."""
    d = abs(float(row["entry"]) - float(row["sl_price"]))
    if float(row["m15_atr"]) <= 0:
        return float("inf")
    return d / float(row["m15_atr"])


def gate_admits(row: dict, config: str) -> bool:
    """Return True if this configuration would admit this row at trade time.

    Matches replication_analysis.py:138-166.
    """
    # Degenerate rows never get here (pre-filtered upstream), but guard anyway.
    if bool(row.get("is_degenerate")):
        return False
    m15_atr = float(row["m15_atr"])
    if m15_atr <= 0:
        return False
    sl_dist = abs(float(row["entry"]) - float(row["sl_price"]))
    # Base rule: if not tight, admission is automatic regardless of bypass.
    if sl_dist >= BASE_TIGHT_MULT * m15_atr:
        return True
    # Tight — baseline rejects.
    if config == "1_baseline":
        return False
    # All other configs require sl_beyond_edge (True by construction in this
    # dataset — every row was built with SL on the far side of the OB edge).
    buffer_atr = float(row["buffer_atr"])
    if config == "2_current_live":
        return buffer_atr >= 0.3
    if config == "3_option_c":
        return buffer_atr <= 0.5
    if config == "4_option_d":
        return buffer_atr <= 0.3
    if config == "5_option_e":
        return 0.3 <= buffer_atr <= 0.5
    raise ValueError(f"unknown config {config}")


def r_to_numeric(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        f = float(v)
        if np.isnan(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def summarize_cell(rows: List[dict]) -> dict:
    """Compute admitted/WR/Exp/etc for a list of admitted rows."""
    n = len(rows)
    if n == 0:
        return {
            "admitted": 0,
            "continued": 0,
            "reversed": 0,
            "unresolved": 0,
            "win_rate": float("nan"),
            "expectancy_all": float("nan"),
            "expectancy_ex_unresolved": float("nan"),
            "sweep_events": 0,
            "max_R": float("nan"),
            "min_R": float("nan"),
            "price_distance_expectancy": float("nan"),
        }
    cont = sum(1 for r in rows if r["outcome"] == "CONTINUED")
    rev = sum(1 for r in rows if r["outcome"] == "REVERSED")
    unr = sum(1 for r in rows if r["outcome"] == "UNRESOLVED")
    resolved = cont + rev
    wr = cont / resolved if resolved else float("nan")
    # Expectancy_all: UNRESOLVED treated as 0R (time-stop equivalent)
    rs_all: List[float] = []
    rs_resolved: List[float] = []
    price_r_units: List[float] = []  # |target - entry| / m15_atr, for risk-adjusted accounting
    for r in rows:
        rn = r_to_numeric(r["r_multiple"])
        if rn is None:
            rs_all.append(0.0)
        else:
            rs_all.append(rn)
            rs_resolved.append(rn)
        # Price-distance-to-target in M15 ATR units (signed by outcome):
        # for CONTINUED we realize +|tgt - entry|; for REVERSED we realize
        # -|entry - sl|. Both normalized by m15_atr. This removes the
        # R-ratio artifact because we measure realized price-distance in
        # absolute (M15-ATR-normalized) terms rather than as a ratio to SL.
        m15a = float(r["m15_atr"])
        if m15a <= 0:
            continue
        if r["outcome"] == "CONTINUED":
            dist = abs(float(r["target_price"]) - float(r["entry"]))
            price_r_units.append(dist / m15a)
        elif r["outcome"] == "REVERSED":
            dist = abs(float(r["entry"]) - float(r["sl_price"]))
            price_r_units.append(-dist / m15a)
        else:
            price_r_units.append(0.0)
    exp_all = float(np.mean(rs_all)) if rs_all else float("nan")
    exp_res = float(np.mean(rs_resolved)) if rs_resolved else float("nan")
    price_exp = float(np.mean(price_r_units)) if price_r_units else float("nan")
    # Sweep events: REVERSED with tight buffer (< 0.3 × M15 ATR).
    sweeps = sum(
        1
        for r in rows
        if r["outcome"] == "REVERSED" and float(r["buffer_atr"]) < 0.3
    )
    max_r = max((r for r in rs_resolved), default=float("nan"))
    min_r = min((r for r in rs_resolved), default=float("nan"))
    return {
        "admitted": n,
        "continued": cont,
        "reversed": rev,
        "unresolved": unr,
        "win_rate": wr,
        "expectancy_all": exp_all,
        "expectancy_ex_unresolved": exp_res,
        "sweep_events": sweeps,
        "max_R": max_r,
        "min_R": min_r,
        "price_distance_expectancy": price_exp,
    }


def buffer_distribution(rows: List[dict]) -> dict:
    """Buffer/M15_ATR distribution for admitted rows."""
    vals = [float(r["buffer_atr"]) for r in rows]
    if not vals:
        return {}
    arr = np.array(vals)
    # Bins
    bins = [
        ("<0.3", np.sum(arr < 0.3)),
        ("[0.3,0.4)", np.sum((arr >= 0.3) & (arr < 0.4))),
        ("[0.4,0.5)", np.sum((arr >= 0.4) & (arr < 0.5))),
        ("[0.5,0.75)", np.sum((arr >= 0.5) & (arr < 0.75))),
        ("[0.75,1.0)", np.sum((arr >= 0.75) & (arr < 1.0))),
        ("[1.0,1.5)", np.sum((arr >= 1.0) & (arr < 1.5))),
        (">=1.5", np.sum(arr >= 1.5)),
    ]
    return {
        "n": len(vals),
        "p5": float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "bins": bins,
    }


def r_distribution(rows: List[dict]) -> dict:
    """R-multiple distribution on CONTINUED rows only."""
    vals = []
    for r in rows:
        if r["outcome"] != "CONTINUED":
            continue
        rn = r_to_numeric(r["r_multiple"])
        if rn is not None:
            vals.append(rn)
    if not vals:
        return {"n": 0}
    arr = np.array(vals)
    return {
        "n": len(vals),
        "p5": float(np.percentile(arr, 5)),
        "p25": float(np.percentile(arr, 25)),
        "p50": float(np.percentile(arr, 50)),
        "p75": float(np.percentile(arr, 75)),
        "p95": float(np.percentile(arr, 95)),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "mean": float(arr.mean()),
    }


def run() -> None:
    print(f"Loading {MULTI_PATH}")
    df = pd.read_csv(MULTI_PATH)
    print(f"  rows: {len(df)}")

    # Drop degenerate rows for all gate analysis.
    df["is_degenerate"] = df["is_degenerate"].astype(bool)
    clean = df[~df["is_degenerate"]].copy()
    print(f"  clean (non-degenerate): {len(clean)}")

    # Convert for per-row dicts
    clean_records = clean.to_dict(orient="records")

    # -------- Per-policy × gate cell analysis --------
    policies = sorted(clean["policy_multiplier"].unique())
    print(f"  policies: {policies}")

    cell_rows: List[dict] = []
    for pol in policies:
        pol_rows = [r for r in clean_records if r["policy_multiplier"] == pol]
        for config in CONFIGS:
            admitted = [r for r in pol_rows if gate_admits(r, config)]
            stats = summarize_cell(admitted)
            cell_rows.append(
                {
                    "policy_multiplier": pol,
                    "gate_config": config,
                    **stats,
                }
            )

    cell_path = OUT_DIR / "path1_gate_cells.csv"
    with cell_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "policy_multiplier",
                "gate_config",
                "admitted",
                "continued",
                "reversed",
                "unresolved",
                "win_rate",
                "expectancy_all",
                "expectancy_ex_unresolved",
                "sweep_events",
                "max_R",
                "min_R",
                "price_distance_expectancy",
            ],
        )
        w.writeheader()
        for rec in cell_rows:
            w.writerow(rec)
    print(f"Wrote {cell_path} ({len(cell_rows)} rows)")

    # -------- Buffer distribution per policy --------
    buf_rows: List[dict] = []
    for pol in policies:
        pol_rows = [r for r in clean_records if r["policy_multiplier"] == pol]
        stats = buffer_distribution(pol_rows)
        rec = {"policy_multiplier": pol, **{k: v for k, v in stats.items() if k != "bins"}}
        # Explode bins into columns
        for bname, bcount in stats.get("bins", []):
            rec[f"bin_{bname}"] = int(bcount)
        buf_rows.append(rec)
    # Consistent columns across rows
    all_cols = sorted({k for r in buf_rows for k in r.keys()})
    # Reorder: policy, n, percentiles, min, max, bins
    ordered = ["policy_multiplier", "n", "p5", "p25", "p50", "p75", "p95", "min", "max"]
    bin_cols = sorted([c for c in all_cols if c.startswith("bin_")])
    ordered += bin_cols
    buf_path = OUT_DIR / "path1_buffer_distribution.csv"
    with buf_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ordered)
        w.writeheader()
        for rec in buf_rows:
            w.writerow({k: rec.get(k, "") for k in ordered})
    print(f"Wrote {buf_path}")

    # -------- Per-symbol breakdown at 0.5 policy --------
    pol05 = [r for r in clean_records if float(r["policy_multiplier"]) == 0.5]
    per_symbol_rows: List[dict] = []
    symbols = sorted({r["symbol"] for r in pol05})
    for sym in symbols:
        sym_rows = [r for r in pol05 if r["symbol"] == sym]
        for config in CONFIGS:
            admitted = [r for r in sym_rows if gate_admits(r, config)]
            stats = summarize_cell(admitted)
            per_symbol_rows.append(
                {
                    "symbol": sym,
                    "gate_config": config,
                    **stats,
                }
            )
    per_sym_path = OUT_DIR / "path1_per_symbol_0p5.csv"
    with per_sym_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "symbol",
                "gate_config",
                "admitted",
                "continued",
                "reversed",
                "unresolved",
                "win_rate",
                "expectancy_all",
                "expectancy_ex_unresolved",
                "sweep_events",
                "max_R",
                "min_R",
                "price_distance_expectancy",
            ],
        )
        w.writeheader()
        for rec in per_symbol_rows:
            w.writerow(rec)
    print(f"Wrote {per_sym_path}")

    # -------- R-multiple distribution per policy --------
    r_rows: List[dict] = []
    for pol in policies:
        pol_rows = [r for r in clean_records if r["policy_multiplier"] == pol]
        stats = r_distribution(pol_rows)
        r_rows.append({"policy_multiplier": pol, **stats})
    r_path = OUT_DIR / "path1_r_distribution.csv"
    with r_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "policy_multiplier",
                "n",
                "p5",
                "p25",
                "p50",
                "p75",
                "p95",
                "min",
                "max",
                "mean",
            ],
        )
        w.writeheader()
        for rec in r_rows:
            w.writerow(rec)
    print(f"Wrote {r_path}")

    # -------- Pretty-print summary --------
    print("\n=== Gate × Policy cells (admitted, WR, Exp_ex_unresolved) ===")
    header = "policy " + " ".join(f"{c:>28}" for c in CONFIGS)
    print(header)
    for pol in policies:
        row_strs = [f"{pol:<5}"]
        for config in CONFIGS:
            cell = next(
                r
                for r in cell_rows
                if r["policy_multiplier"] == pol and r["gate_config"] == config
            )
            adm = cell["admitted"]
            wr = cell["win_rate"]
            exp = cell["expectancy_ex_unresolved"]
            wr_s = f"{wr:.1%}" if wr == wr else "nan"
            exp_s = f"{exp:+.3f}" if exp == exp else "nan"
            row_strs.append(f" {adm:>4} {wr_s:>7} {exp_s:>10}")
        print(" | ".join(row_strs))

    print("\nDone.")


if __name__ == "__main__":
    run()
