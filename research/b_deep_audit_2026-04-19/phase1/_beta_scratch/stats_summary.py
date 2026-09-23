"""Statistical summary for beta report."""
from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(r"C:\Users\MSI\Documents\ai-trading-agent/research/b_deep_audit_2026-04-19/phase1/_beta_scratch")


def binomial_p_exact(k, n, p=0.5, direction="two-sided"):
    """Exact binomial test p-value (returns the one-tailed or two-tailed)."""
    if n == 0:
        return None
    from math import comb
    pmf_k = comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    if direction == "two-sided":
        # sum tail masses with pmf <= pmf_k
        total = 0.0
        for i in range(n + 1):
            pmf_i = comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
            if pmf_i <= pmf_k + 1e-12:
                total += pmf_i
        return total
    elif direction == "less":
        return sum(
            comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
            for i in range(k + 1)
        )
    else:  # greater
        return sum(
            comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
            for i in range(k, n + 1)
        )


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)) / denom
    return (centre - half, centre + half)


def bonferroni(p, n_tests=8):
    if p is None:
        return None
    return min(p * n_tests, 1.0)


def main():
    # Test 1: sl_buffer_applied = 0.0 universality (each instrument vs alternative hypothesis != 1.0)
    # Not meaningful to p-test; rate is 100% with n=1053/300/202 — report as descriptive.
    # Test 2: Degenerate EURUSD rate vs 0
    # 179/300 vs null-hypothesis 0% → p ≈ 0 (obviously)
    # But for inter-instrument comparison: Fisher's exact
    # XAUUSD 0/1053 vs EURUSD 179/300 → p essentially 0
    # Test 3: Model_used bogus rate (is it ≥95%?)
    # XAUUSD 1452/1455, NAS100 759/759, EURUSD 1106/1106 — descriptive.
    # Test 4: EURUSD direction skew LONG (not primary in this audit — delta)
    # Test 5: h1_poi_hallucination proportion per instrument

    # Headline: EURUSD degenerate rate CI
    k_eur, n_eur = 179, 300
    lo, hi = wilson_ci(k_eur, n_eur)
    p_eur = k_eur / n_eur

    # Hallucinated model_used rate per instrument
    cases = {
        "XAUUSD": (1452, 1455),
        "NAS100": (759, 759),
        "EURUSD": (1106, 1106),
    }
    out = {
        "degenerate_EURUSD": {
            "k": k_eur, "n": n_eur, "rate": p_eur,
            "wilson_95_ci": [lo, hi],
            "raw_p_vs_null_0pct": "<1e-300 (descriptive)",
            "bonferroni_corrected_p": "<1e-300",
        },
        "model_used_bogus_rate": {},
    }
    for inst, (k, n) in cases.items():
        lo, hi = wilson_ci(k, n)
        out["model_used_bogus_rate"][inst] = {
            "k": k, "n": n, "rate": k / n,
            "wilson_95_ci": [lo, hi],
        }

    # sl_buffer_applied=0 rate
    sl = {
        "XAUUSD": (1053, 1053),
        "NAS100": (202, 202),
        "EURUSD": (300, 300),
    }
    out["sl_buffer_zero_rate"] = {}
    for inst, (k, n) in sl.items():
        lo, hi = wilson_ci(k, n)
        out["sl_buffer_zero_rate"][inst] = {
            "k": k, "n": n, "rate": k / n,
            "wilson_95_ci": [lo, hi],
        }

    # AI/pipeline bias mismatch (exploratory; n>20 on XAUUSD/EURUSD)
    out["ai_bias_disagreement"] = {
        "XAUUSD": {"mismatch": 58, "agree": 1397, "rate_pct": 58 / 1455 * 100},
        "EURUSD": {"mismatch": 248, "agree": 858, "rate_pct": 248 / 1106 * 100},
        "NAS100": {"mismatch": 27, "agree": 732, "rate_pct": 27 / 759 * 100},
    }

    # poi citation hallucinations (L2 h1_poi_exists family)
    out["poi_hallucination_prevalence"] = {
        "XAUUSD": {"poi_cited_no_match_in_MSO": 90, "poi_identified_false_but_MSO_has_one": 69, "total_h1_poi_rejects": 159},
        "EURUSD": {"poi_cited_no_match_in_MSO": 112, "poi_identified_false_but_MSO_has_one": 43, "total_h1_poi_rejects": 155},
        "NAS100": {"poi_cited_no_match_in_MSO": 13, "poi_identified_false_but_MSO_has_one": 19, "total_h1_poi_rejects": 32},
    }

    # entry_in_ob magnitude (XAUUSD's top L2 reason)
    out["entry_in_ob_magnitude"] = {
        "XAUUSD": {"n": 557, "mean_dist_zone_widths": 4.55, "median_dist_zone_widths": 3.45, "max_dist_zone_widths": 24.99},
        "EURUSD": {"n": 13, "mean_dist_zone_widths": 0.0, "median_dist_zone_widths": 0.0, "note": "2-dp degenerate rounding hides distance"},
        "NAS100": {"n": 5, "mean_dist_zone_widths": 8.34, "median_dist_zone_widths": 8.23, "max_dist_zone_widths": 11.49},
    }

    with open(OUT / "stats_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
