"""Compute fresh correlation matrix from data/historical_2026/ M15 closes.

For staleness audit. Uses log returns, common-timestamp intersection.
$0 API.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
DATA = ROOT / "data" / "historical_2026"
OUT = ROOT / "research" / "staleness_audit"
OUT.mkdir(parents=True, exist_ok=True)

INSTRUMENTS = [
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD",
    "EURGBP", "EURJPY", "EURUSD", "GBPJPY", "GBPUSD",
    "GER40", "JP225", "NAS100", "NZDUSD", "SPX500",
    "UK100", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF",
    "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD",
]


def load_m15_returns(symbol: str) -> dict[str, float]:
    path = DATA / f"{symbol}_M15.csv"
    if not path.exists():
        return {}
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                rows.append((r["time"], float(r["close"])))
            except (KeyError, ValueError):
                continue
    out: dict[str, float] = {}
    for i in range(1, len(rows)):
        prev_t, prev_c = rows[i - 1]
        curr_t, curr_c = rows[i]
        if prev_c > 0 and curr_c > 0:
            out[curr_t] = math.log(curr_c / prev_c)
    return out


def pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 2:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if sx == 0 or sy == 0:
        return 0.0
    return num / (sx * sy)


def main():
    print("Loading log-returns for", len(INSTRUMENTS), "instruments...")
    returns = {}
    date_ranges = {}
    for s in INSTRUMENTS:
        r = load_m15_returns(s)
        if r:
            returns[s] = r
            ks = sorted(r.keys())
            date_ranges[s] = (ks[0], ks[-1], len(ks))
        else:
            print(f"  WARN: no data for {s}")

    print("\nDate ranges (per instrument):")
    for s, (start, end, n) in date_ranges.items():
        print(f"  {s:14s} {start} -> {end}  n={n}")

    print("\nComputing pairwise Pearson correlations on common timestamps...")
    matrix: dict[str, dict[str, float]] = {}
    n_obs: dict[str, dict[str, int]] = {}
    for a in INSTRUMENTS:
        if a not in returns:
            continue
        matrix[a] = {}
        n_obs[a] = {}
        for b in INSTRUMENTS:
            if b not in returns:
                continue
            if a == b:
                matrix[a][b] = 1.0
                n_obs[a][b] = len(returns[a])
                continue
            common = sorted(set(returns[a].keys()) & set(returns[b].keys()))
            if len(common) < 30:
                matrix[a][b] = 0.0
                n_obs[a][b] = len(common)
                continue
            x = [returns[a][t] for t in common]
            y = [returns[b][t] for t in common]
            matrix[a][b] = round(pearson(x, y), 4)
            n_obs[a][b] = len(common)

    out_json = OUT / "fresh_correlation_matrix_2026-04-25.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"matrix": matrix, "n_obs": n_obs, "date_ranges": date_ranges},
                  f, indent=2)
    print(f"\nWrote {out_json}")

    # Print key pairs
    print("\n=== KEY PAIRS (fresh 2026 data) ===")
    pairs_of_interest = [
        ("XAUUSD", "GBPUSD"),
        ("XAUUSD", "US30_cash"),
        ("XAUUSD", "USDJPY"),
        ("XAUUSD", "XAGUSD"),
        ("XAUUSD", "EURUSD"),
        ("XAUUSD", "AUDUSD"),
        ("XAUUSD", "NZDUSD"),
        ("XAUUSD", "USDCAD"),
        ("USDJPY", "GBPJPY"),
        ("USDJPY", "EURJPY"),
        ("US30_cash", "NAS100"),
        ("US30_cash", "SPX500"),
        ("GBPUSD", "GBPJPY"),
        ("GBPUSD", "EURUSD"),
        ("GBPUSD", "AUDUSD"),
        ("GBPUSD", "NZDUSD"),
        ("GBPUSD", "US30_cash"),
        ("GBPJPY", "EURJPY"),
        ("AUDUSD", "NZDUSD"),
        ("AUDUSD", "USDCAD"),
        ("EURUSD", "USDCHF"),
        ("EURUSD", "USDCAD"),
        ("USDJPY", "USDCAD"),
    ]
    for a, b in pairs_of_interest:
        if a in matrix and b in matrix[a]:
            r = matrix[a][b]
            n = n_obs[a].get(b, 0)
            print(f"  {a:12s} <-> {b:12s} r={r:+.4f}  n={n}")


if __name__ == "__main__":
    main()
