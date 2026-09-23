"""K1 finalize: write a comprehensive decision matrix CSV using Agent E DSR
framing for direct comparability with Agent E's threshold scan."""
import csv, json, math
from pathlib import Path
from scipy import stats

F = Path("C:/Users/MSI/Documents/ai-trading-agent/research/ml_program/forensics/2026-04-29")
EULER = 0.5772156649015329


def expected_max_sharpe(N: int) -> float:
    if N <= 1:
        return 0.0
    a = math.sqrt(2.0 * math.log(N))
    return a - EULER / a


def dsr_p_value(sr_obs, n_obs, N_trials, skew=0.0, kurt=3.0):
    if n_obs <= 1:
        return 1.0
    var_inner = max(1e-12, 1.0 - skew * sr_obs + (kurt - 1.0) / 4.0 * sr_obs ** 2)
    sigma_sr = math.sqrt(var_inner / (n_obs - 1))
    if sigma_sr <= 0:
        return 1.0
    e_max_sr = sigma_sr * expected_max_sharpe(N_trials)
    z = (sr_obs - e_max_sr) / sigma_sr
    return 1.0 - float(stats.norm.cdf(z))


# Agent E projection coefficients
BASE_LIFT = 0.0484
BASE_SR = 1.2748
BASE_N = 528
SR_PER_LIFT = BASE_SR / BASE_LIFT


def project_sr(lift, n):
    return lift * SR_PER_LIFT * math.sqrt(n / BASE_N)


# K1's three claims
claims = [
    {
        "claim": "K54 v3 vs canonical K54 v1",
        "original_lift": 0.0484,
        "apples_to_apples_lift": 0.04841,
        "threshold": 0.04,
    },
    {
        "claim": "Q1.3 Arch A vs canonical K54 v1",
        "original_lift": 0.0492,
        "apples_to_apples_lift": 0.03392,
        "threshold": 0.04,
    },
    {
        "claim": "T7 NAS_US30 specialist vs K54 v3 global on NAS+US30 (Agent C K=4 paired)",
        "original_lift": 0.111,
        "apples_to_apples_lift": -0.00685,
        "threshold": 0.05,
    },
    {
        "claim": "T7 NAS_US30 specialist vs K54 v3 global on NAS+US30 (Agent I unpaired UPPER BOUND)",
        "original_lift": 0.111,
        "apples_to_apples_lift": 0.111,  # this is the un-fold-aligned upper bound
        "threshold": 0.05,
    },
]

# Compute DSR cells under Agent E framing
# DSR cells: T_paths in {15, 20}, N_trials=200, cohort_n in {528 (current), 2326 (Phase2 minimum)}
# + DSR T=20 N=50 (ONC) at n=2326
csv_rows = []
for c in claims:
    lift = c["apples_to_apples_lift"]
    survives = "YES" if lift >= c["threshold"] else "NO"
    if lift > 0:
        sr_528 = project_sr(lift, 528)
        sr_2326 = project_sr(lift, 2326)
        dsr_T15_N200_528 = dsr_p_value(sr_528, 15, 200)
        dsr_T20_N200_528 = dsr_p_value(sr_528, 20, 200)
        dsr_T15_N200_2326 = dsr_p_value(sr_2326, 15, 200)
        dsr_T20_N200_2326 = dsr_p_value(sr_2326, 20, 200)
        dsr_T20_N50_ONC_2326 = dsr_p_value(sr_2326, 20, 50)
    else:
        dsr_T15_N200_528 = dsr_T20_N200_528 = dsr_T15_N200_2326 = 1.0
        dsr_T20_N200_2326 = dsr_T20_N50_ONC_2326 = 1.0

    if c["claim"] == "K54 v3 vs canonical K54 v1":
        impl = "K54 v4 dispatch lift-PASSED at +0.04; survives DSR at T=20 + n=2,326 (0.0088)"
    elif "Arch A" in c["claim"]:
        impl = "Q1.3 gate (a) verdict INVALIDATED; lift 0.0339 below 0.04 threshold"
    elif "Agent C K=4" in c["claim"]:
        impl = "T7 K55-shadow target NOT supported by fold-aligned paired evidence"
    else:
        impl = "T7 K55-shadow target SUGGESTIVE under unpaired UPPER BOUND; needs fold-aligned re-train"

    csv_rows.append({
        "claim": c["claim"],
        "original_lift": c["original_lift"],
        "apples_to_apples_lift": round(lift, 5),
        "threshold": c["threshold"],
        "survives": survives,
        "DSR_p_T15_N200_n528": round(dsr_T15_N200_528, 4),
        "DSR_p_T20_N200_n528": round(dsr_T20_N200_528, 4),
        "DSR_p_T15_N200_n2326": round(dsr_T15_N200_2326, 4),
        "DSR_p_T20_N200_n2326": round(dsr_T20_N200_2326, 4),
        "DSR_p_T20_N50_ONC_n2326": round(dsr_T20_N50_ONC_2326, 4),
        "phase_2_implication": impl,
    })

with (F / "agent_k1_decision_matrix.csv").open("w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
    writer.writeheader()
    for row in csv_rows:
        writer.writerow(row)

# Print
for row in csv_rows:
    print(f"\n{row['claim']}")
    print(f"  original_lift     = {row['original_lift']:+.4f}")
    print(f"  apples_to_apples  = {row['apples_to_apples_lift']:+.4f}")
    print(f"  survives ≥{row['threshold']}: {row['survives']}")
    print(f"  DSR-p T15 N200 n528:   {row['DSR_p_T15_N200_n528']}")
    print(f"  DSR-p T20 N200 n528:   {row['DSR_p_T20_N200_n528']}")
    print(f"  DSR-p T15 N200 n2326:  {row['DSR_p_T15_N200_n2326']}")
    print(f"  DSR-p T20 N200 n2326:  {row['DSR_p_T20_N200_n2326']}")
    print(f"  DSR-p T20 N50 n2326:   {row['DSR_p_T20_N50_ONC_n2326']}")
    print(f"  Phase 2: {row['phase_2_implication']}")

print(f"\nFinal CSV saved: {F / 'agent_k1_decision_matrix.csv'}")
