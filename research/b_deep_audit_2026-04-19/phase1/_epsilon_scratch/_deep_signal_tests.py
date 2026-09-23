"""Deeper statistical follow-up on the strongest signals.

- Sig 3: Fisher exact for XAUUSD 4/4 vs 175/395 null
- Sig 7: Mann-Whitney on winner MFE 2024 vs 2026; loss MAE; compression test
- Combined verdict with Bonferroni 6 tests
- XAUUSD historical MFE compression is the strongest signal — needs specific workup
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from _loader import load_all_backtest, load_m15, median, percentile, _parse_iso


# -----------------------------------------------------------------------------
# Fisher exact two-sided p-value for 2x2 contingency
# -----------------------------------------------------------------------------
def fisher_exact_2sided(a: int, b: int, c: int, d: int) -> float:
    """Return 2-sided Fisher exact p-value.

    2x2:  | a  b |
          | c  d |

    Null: rows and columns independent. Good for small n.
    """
    from math import comb

    def p_of_table(a, b, c, d):
        n = a + b + c + d
        r1 = a + b
        r2 = c + d
        c1 = a + c
        return comb(r1, a) * comb(r2, c) / comb(n, c1)

    total_prob = p_of_table(a, b, c, d)
    n = a + b + c + d
    r1 = a + b
    c1 = a + c
    p_target = total_prob
    p_sum = 0.0
    for x in range(max(0, r1 + c1 - n), min(r1, c1) + 1):
        y = r1 - x
        u = c1 - x
        v = (c + d) - u
        p = p_of_table(x, y, u, v)
        if p <= p_target + 1e-12:
            p_sum += p
    return min(1.0, p_sum)


def mann_whitney_u_p(a, b):
    if len(a) < 3 or len(b) < 3:
        return None
    combined = [(v, 0) for v in a] + [(v, 1) for v in b]
    combined.sort(key=lambda x: x[0])
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    r_a = sum(ranks[i] for i, (_, g) in enumerate(combined) if g == 0)
    n1, n2 = len(a), len(b)
    u_a = r_a - n1 * (n1 + 1) / 2
    u = min(u_a, n1 * n2 - u_a)
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if sigma == 0:
        return None
    z = (u - mu) / sigma
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return p


# -----------------------------------------------------------------------------
# Chi-square for proportion difference (2-sample)
# -----------------------------------------------------------------------------
def two_prop_z_p(succ1, n1, succ2, n2):
    """2-sided z-test for two proportions."""
    if n1 < 5 or n2 < 5:
        return None
    p1 = succ1 / n1
    p2 = succ2 / n2
    p = (succ1 + succ2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return None
    z = (p1 - p2) / se
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


# -----------------------------------------------------------------------------
# Sig 3 XAUUSD bootstrap
# -----------------------------------------------------------------------------
def sig3_xauusd_test():
    # 4/4 observed vs 175/395 null
    p_fisher = fisher_exact_2sided(4, 0, 175, 220)  # 4 rev / 0 no-rev vs 175 rev / 220 no-rev
    return {
        "test": "Fisher 2-sided",
        "observed": "4/4 XAUUSD candidate losses reversed ≥1R within 4h",
        "null_baseline": "175/395 random XAUUSD entries at same R size (44.3%)",
        "p_value": p_fisher,
        "effect_size_pp": (1.0 - 175/395) * 100,
        "note": "n=4 observed is small, but 100% vs 44% is extreme. Fisher handles small n correctly.",
    }


# -----------------------------------------------------------------------------
# Sig 7: MFE/MAE compression 2024 vs 2026 by symbol
# -----------------------------------------------------------------------------
def sig7_compression_tests():
    bt = load_all_backtest()
    out = {}
    for sym, trades in bt.items():
        by_year = defaultdict(list)
        for t in trades:
            y = t.get("date", "?")[:4]
            by_year[y].append(t)
        # Need 2024/2025 early vs 2026 late
        years = sorted(by_year.keys())
        if len(years) < 2:
            continue
        early_years = years[:-1]
        late_year = years[-1]

        early_trades = [t for y in early_years for t in by_year[y]]
        late_trades = by_year[late_year]
        if len(late_trades) < 5:
            continue

        # Winner MFE
        e_w_mfe = [t["mfe_r"] for t in early_trades if t.get("outcome") == "WIN" and t.get("mfe_r") is not None]
        l_w_mfe = [t["mfe_r"] for t in late_trades if t.get("outcome") == "WIN" and t.get("mfe_r") is not None]
        # Loss MFE
        e_l_mfe = [t["mfe_r"] for t in early_trades if t.get("outcome") == "LOSS" and t.get("mfe_r") is not None]
        l_l_mfe = [t["mfe_r"] for t in late_trades if t.get("outcome") == "LOSS" and t.get("mfe_r") is not None]
        # Winner MAE
        e_w_mae = [t["mae_r"] for t in early_trades if t.get("outcome") == "WIN" and t.get("mae_r") is not None]
        l_w_mae = [t["mae_r"] for t in late_trades if t.get("outcome") == "WIN" and t.get("mae_r") is not None]

        # Hold time
        e_hold = [t["hold_time_candles"] for t in early_trades if t.get("hold_time_candles") is not None]
        l_hold = [t["hold_time_candles"] for t in late_trades if t.get("hold_time_candles") is not None]

        out[sym] = {
            "early_years": early_years,
            "late_year": late_year,
            "n_early_trades": len(early_trades),
            "n_late_trades": len(late_trades),
            "winner_mfe": {
                "n_early": len(e_w_mfe), "n_late": len(l_w_mfe),
                "median_early": median(e_w_mfe) if e_w_mfe else None,
                "median_late": median(l_w_mfe) if l_w_mfe else None,
                "mean_early": statistics.mean(e_w_mfe) if e_w_mfe else None,
                "mean_late": statistics.mean(l_w_mfe) if l_w_mfe else None,
                "mw_u_p_2sided": mann_whitney_u_p(e_w_mfe, l_w_mfe),
                "compression_pct": (1 - median(l_w_mfe)/median(e_w_mfe))*100 if (e_w_mfe and l_w_mfe and median(e_w_mfe) > 0) else None,
            },
            "loss_mfe": {
                "n_early": len(e_l_mfe), "n_late": len(l_l_mfe),
                "median_early": median(e_l_mfe) if e_l_mfe else None,
                "median_late": median(l_l_mfe) if l_l_mfe else None,
                "mw_u_p_2sided": mann_whitney_u_p(e_l_mfe, l_l_mfe),
            },
            "winner_mae": {
                "n_early": len(e_w_mae), "n_late": len(l_w_mae),
                "median_early": median(e_w_mae) if e_w_mae else None,
                "median_late": median(l_w_mae) if l_w_mae else None,
                "mw_u_p_2sided": mann_whitney_u_p(e_w_mae, l_w_mae),
            },
            "hold_time_candles": {
                "n_early": len(e_hold), "n_late": len(l_hold),
                "median_early": median(e_hold) if e_hold else None,
                "median_late": median(l_hold) if l_hold else None,
            },
        }
    return out


# -----------------------------------------------------------------------------
# Overall Bonferroni verdict
# -----------------------------------------------------------------------------
def bonferroni_verdict(tests: dict, n_tests: int = 6):
    alpha_fwer = 0.05
    threshold = alpha_fwer / n_tests
    # Collect p-values
    all_p = []
    for k, t in tests.items():
        if isinstance(t, dict) and "p_value" in t and t["p_value"] is not None:
            all_p.append((k, t["p_value"]))
    all_p.sort(key=lambda x: x[1])
    return {
        "n_tests_bonferroni": n_tests,
        "threshold": threshold,
        "test_p_values": all_p,
        "survivors": [k for k, p in all_p if p <= threshold],
    }


if __name__ == "__main__":
    sig3 = sig3_xauusd_test()
    sig7 = sig7_compression_tests()
    # Also: proportions test for sig3 (treat as validation)
    prop3 = two_prop_z_p(4, 4, 175, 395)

    out = {
        "sig3_xauusd_reversal_fisher": sig3,
        "sig3_xauusd_reversal_z_prop": prop3,
        "sig7_compression_tests": sig7,
    }
    with open(HERE / "deep_signal_tests.json", "w", encoding="utf-8") as f:
        json.dump(out, f, default=str, indent=2)
    print(json.dumps(out, default=str, indent=2))
