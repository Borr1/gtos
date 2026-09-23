"""Compute DSR-p at alternative trial-budget anchors (per Agent B) for A2 top-K bands.

Tests whether top-K signal can survive DSR under the eff_N=11 (ONC empirical) anchor
that Agent B identified as the methodologically-defensible alternative to N=200.
"""
import json
import math
from pathlib import Path
import numpy as np
from scipy import stats

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
F = ROOT / "research/ml_program/forensics/2026-04-29"

with open(F / "agent_a2_extended_top_k_sweep.json") as fh:
    top_k_data = json.load(fh)

with open(F / "agent_a2_extended_threshold_sweep.json") as fh:
    thr_data = json.load(fh)

with open(F / "agent_a2_bottom_k_inversion.json") as fh:
    bot_data = json.load(fh)


def dsr_p(SR, T, N_trials):
    if T < 2:
        return float("nan")
    EM = 0.5772156649
    inv_phi_1 = stats.norm.ppf(1 - 1.0 / N_trials)
    inv_phi_2 = stats.norm.ppf(1 - 1.0 / (N_trials * math.e))
    e_max_z = (1 - EM) * inv_phi_1 + EM * inv_phi_2
    sigma_sr = math.sqrt((1 + 0.5 * SR**2) / (T - 1))
    sr_max_null = sigma_sr * e_max_z
    z = (SR - sr_max_null) / sigma_sr
    return float(1 - stats.norm.cdf(z))


def add_alt_n_dsr(rows, T_field="n", lift_key="lift_vs_uniform"):
    """For each row, compute DSR-p at N=200, 50, 11, 3 (Agent B's eff_N candidates)."""
    out = []
    for r in rows:
        T = r.get(T_field) if T_field in r else r.get("n_taken")
        SR = r.get("sr_per_trade")
        if SR is None or T is None or T < 2:
            out.append({**r, "dsr_p_N200": None, "dsr_p_N50": None, "dsr_p_N11": None, "dsr_p_N3": None,
                        "rg_pass_N50": False, "rg_pass_N11": False, "rg_pass_N3": False})
            continue
        d200 = dsr_p(SR, T, 200)
        d50 = dsr_p(SR, T, 50)
        d11 = dsr_p(SR, T, 11)
        d3 = dsr_p(SR, T, 3)
        ci = r.get("bootstrap_95ci", [None, None])
        ci_excl = ci[0] is not None and ci[0] > 0
        out.append({
            **r,
            "dsr_p_N200": round(d200, 4),
            "dsr_p_N50": round(d50, 4),
            "dsr_p_N11": round(d11, 4),
            "dsr_p_N3": round(d3, 4),
            "rg_pass_N200_p010": bool(ci_excl and d200 < 0.10),
            "rg_pass_N50_p010": bool(ci_excl and d50 < 0.10),
            "rg_pass_N11_p010": bool(ci_excl and d11 < 0.10),
            "rg_pass_N3_p010": bool(ci_excl and d3 < 0.10),
        })
    return out


print("=== Top-K with alt trial-budget DSR ===")
top_k_alt = add_alt_n_dsr(top_k_data["top_k_results"], T_field="n")
print(f"{'pct':>4} {'n':>4} {'lift':>7} {'CI_lo':>7} {'DSR_N200':>9} {'DSR_N50':>9} {'DSR_N11':>9} {'DSR_N3':>9} {'RG_N50':>7} {'RG_N11':>7} {'RG_N3':>7}")
for r in top_k_alt:
    print(f"{r['top_pct']:>4} {r['n']:>4} {r['lift_vs_uniform']:>+7.3f} {r['bootstrap_95ci'][0]:>+7.3f} "
          f"{r['dsr_p_N200']!s:>9} {r['dsr_p_N50']!s:>9} {r['dsr_p_N11']!s:>9} {r['dsr_p_N3']!s:>9} "
          f"{str(r['rg_pass_N50_p010']):>7} {str(r['rg_pass_N11_p010']):>7} {str(r['rg_pass_N3_p010']):>7}")

print("\n=== Threshold with alt trial-budget DSR ===")
thr_alt = add_alt_n_dsr(thr_data["thresholds"], T_field="n_taken", lift_key="lift_vs_uniform_R")
print(f"{'thr':>5} {'n':>4} {'lift':>7} {'CI_lo':>7} {'DSR_N200':>9} {'DSR_N50':>9} {'DSR_N11':>9} {'DSR_N3':>9} {'RG_N50':>7} {'RG_N11':>7} {'RG_N3':>7}")
for r in thr_alt:
    print(f"{r['threshold']:>5} {r['n_taken']:>4} {r['lift_vs_uniform_R']:>+7.3f} {r['bootstrap_95ci'][0]:>+7.3f} "
          f"{r['dsr_p_N200']!s:>9} {r['dsr_p_N50']!s:>9} {r['dsr_p_N11']!s:>9} {r['dsr_p_N3']!s:>9} "
          f"{str(r['rg_pass_N50_p010']):>7} {str(r['rg_pass_N11_p010']):>7} {str(r['rg_pass_N3_p010']):>7}")

# Save the alt-N comparison
with open(F / "agent_a2_dsr_alt_eff_n.json", "w") as fh:
    json.dump({
        "anchor_explanation": "Agent B's empirical eff_N estimates: N=200 (CEO conservative), N=50 (per-program-track aggregation), N=11 (ONC cluster-scaled, methodologically-defensible), N=3 (max ONC discount)",
        "top_k_with_alt_dsr": top_k_alt,
        "thresholds_with_alt_dsr": thr_alt,
        "research_grade_PASS_at_N200_p010": [r for r in top_k_alt if r["rg_pass_N200_p010"]],
        "research_grade_PASS_at_N50_p010": [r for r in top_k_alt if r["rg_pass_N50_p010"]],
        "research_grade_PASS_at_N11_p010": [r for r in top_k_alt if r["rg_pass_N11_p010"]],
        "research_grade_PASS_at_N3_p010": [r for r in top_k_alt if r["rg_pass_N3_p010"]],
        "verdict": (
            "If N=200 trial budget: NO top-K passes DSR-p<0.10. "
            "If N=50: see RG_N50 column. "
            "If N=11 (Agent B ONC empirical): see RG_N11 column. "
            "If N=3 (max ONC discount): see RG_N3 column."
        ),
    }, fh, indent=2, default=lambda x: float(x) if hasattr(x, "item") else str(x))
print(f"\nWROTE: {F}/agent_a2_dsr_alt_eff_n.json")
