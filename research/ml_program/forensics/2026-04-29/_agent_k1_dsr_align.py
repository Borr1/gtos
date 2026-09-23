"""K1 add-on: align DSR computation with Agent E's framing for direct comparability.

Agent E uses base_SR=1.2748 at lift=0.0484, n=528, T=15.
The implied formula is: projected_SR = (lift / 0.0484) * 1.2748 * sqrt(n / 528).

Equivalent: SR per unit lift at base = 26.34. So projected_SR = lift * 26.34 * sqrt(n / 528)
= lift * (1.2748 / 0.0484) * sqrt(n / 528).

DSR-p computed via Bailey-Lopez de Prado eq 11.5 with skew=0, kurt=3.

We compute this projection for our 3 paired-tested claims at:
  T_paths in [15, 20, 50]
  n_cohort in [528 (current), 2326 (Phase 2 minimum), 3132 (Phase 2 aggressive_a),
               4892 (Phase 2 aggressive_b)]
  N_trials in [50 (ONC), 200 (current trial budget)]
"""
import json, math
from pathlib import Path
from scipy import stats

EULER = 0.5772156649015329
F = Path("C:/Users/MSI/Documents/ai-trading-agent/research/ml_program/forensics/2026-04-29")


def expected_max_sharpe(N: int) -> float:
    if N <= 1:
        return 0.0
    a = math.sqrt(2.0 * math.log(N))
    return a - EULER / a


def dsr_p_value(sr_obs: float, n_obs: int, N_trials: int,
                skew: float = 0.0, kurt: float = 3.0) -> float:
    """Agent E's formulation: variance scales as 1/(n_obs-1)."""
    if n_obs <= 1:
        return 1.0
    var_inner = 1.0 - skew * sr_obs + (kurt - 1.0) / 4.0 * sr_obs * sr_obs
    var_inner = max(var_inner, 1e-12)
    sigma_sr = math.sqrt(var_inner / (n_obs - 1))
    if sigma_sr <= 0:
        return 1.0
    e_max_z = expected_max_sharpe(N_trials)
    e_max_sr = sigma_sr * e_max_z
    z = (sr_obs - e_max_sr) / sigma_sr
    return 1.0 - float(stats.norm.cdf(z))


# Agent E's projection coefficient
BASE_LIFT = 0.0484
BASE_SR = 1.2748
BASE_N = 528
SR_PER_UNIT_LIFT = BASE_SR / BASE_LIFT  # 26.34

CLAIMS = [
    # (name, observed_lift_paired, type)
    ("K54 v3 vs canonical v1", 0.0484, "global_paired"),
    ("Q1.3 ArchA vs canonical v1", 0.0339, "global_paired"),
    ("T7 NAS_US30 specialist vs v3 global (Agent C K=4 paired proxy)", -0.0068, "specialist_paired"),
    ("T7 NAS_US30 specialist vs v3 global (Agent I unpaired UPPER BOUND)", 0.2144, "specialist_unpaired"),
    ("T7 NAS_US30 specialist vs v3 specialist (Agent I unpaired vs Q1.4)", 0.1114, "specialist_unpaired"),
]

T_RANGE = [15, 20, 50]
N_TRIALS_RANGE = [50, 200]
COHORT_RANGE = [
    ("current_528", 528),
    ("phase2_min_2326", 2326),
    ("phase2_a_3132", 3132),
    ("phase2_b_4892", 4892),
]

results = {"projection_basis": {
    "base_lift": BASE_LIFT,
    "base_SR": BASE_SR,
    "base_n": BASE_N,
    "sr_per_unit_lift": SR_PER_UNIT_LIFT,
    "formula": "projected_SR = lift * SR_PER_UNIT_LIFT * sqrt(n / 528)",
    "DSR_formula": "Bailey-Lopez de Prado AFML eq 11.5 (skew=0, kurt=3)",
    "alignment_note": "Per Agent E base SR convention (matches "
                       "agent_e_dsr_threshold_scan.json + Agent B forensic).",
}, "scans": []}

print(f"Projection basis: SR = lift * {SR_PER_UNIT_LIFT:.3f} * sqrt(n/528)")
print(f"Expected-max SR @ N=200 trials = {expected_max_sharpe(200):.4f}")
print(f"Expected-max SR @ N=50 trials = {expected_max_sharpe(50):.4f}")
print()
for cname, lift, ctype in CLAIMS:
    print(f"\n=== {cname} (lift={lift:+.4f}) ===")
    if lift <= 0:
        print(f"  Lift is non-positive; DSR-p = 1.0 (no edge to defend)")
        for cohort_label, n in COHORT_RANGE:
            for T in T_RANGE:
                for N in N_TRIALS_RANGE:
                    results["scans"].append({
                        "claim": cname,
                        "lift": lift,
                        "type": ctype,
                        "cohort_n": n,
                        "cohort_label": cohort_label,
                        "T_paths": T,
                        "N_trials": N,
                        "projected_SR": 0.0,
                        "DSR_p": 1.0,
                        "verdict": "NO_EDGE",
                    })
        continue
    for cohort_label, n in COHORT_RANGE:
        sr_proj = lift * SR_PER_UNIT_LIFT * math.sqrt(n / BASE_N)
        for T in T_RANGE:
            for N in N_TRIALS_RANGE:
                p = dsr_p_value(sr_proj, T, N)
                verdict = ("SURVIVES" if p < 0.01 else
                           "BORDERLINE" if p < 0.05 else
                           "FAILS")
                results["scans"].append({
                    "claim": cname,
                    "lift": lift,
                    "type": ctype,
                    "cohort_n": n,
                    "cohort_label": cohort_label,
                    "T_paths": T,
                    "N_trials": N,
                    "projected_SR": round(sr_proj, 4),
                    "DSR_p": round(p, 4),
                    "verdict": verdict,
                })
                print(f"  n={n} T={T} N={N}: SR={sr_proj:.3f} DSR-p={p:.4f} {verdict}")

# Summarize key cells
print("\n=== Phase 2 readiness summary at N=200 ===")
for cname, lift, ctype in CLAIMS:
    print(f"\n  {cname} (lift={lift:+.4f})")
    for cohort_label, n in COHORT_RANGE:
        for T in T_RANGE:
            cell = next(s for s in results["scans"]
                        if s["claim"] == cname and s["cohort_n"] == n
                        and s["T_paths"] == T and s["N_trials"] == 200)
            print(f"    n={n} T={T} N=200: DSR-p={cell['DSR_p']:.4f} {cell['verdict']}")

with (F / "agent_k1_dsr_aligned_scan.json").open("w") as fh:
    json.dump(results, fh, indent=2)
print(f"\nSaved: {F / 'agent_k1_dsr_aligned_scan.json'}")
