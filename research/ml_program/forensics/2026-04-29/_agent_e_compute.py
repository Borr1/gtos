"""Agent E forensic computation: 2022-2023 v2-feature backfill feasibility,
non-XAU fillback inventory, pre-2022 extension probe, DSR projection.

Subscription-only. Read-only on production.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from scipy import stats

OUT = Path("C:/Users/MSI/Documents/ai-trading-agent/research/ml_program/forensics/2026-04-29")
OUT.mkdir(parents=True, exist_ok=True)

EULER = 0.5772156649015329


def expected_max_sharpe(N: int) -> float:
    if N <= 1:
        return 0.0
    a = math.sqrt(2.0 * math.log(N))
    return a - EULER / a


def dsr_p_value(sr_obs: float, n_obs: int, N_trials: int, skew: float = 0.0,
                kurtosis: float = 3.0) -> float:
    if n_obs <= 1:
        return 1.0
    var_inner = 1.0 - skew * sr_obs + (kurtosis - 1.0) / 4.0 * sr_obs * sr_obs
    var_inner = max(var_inner, 1e-12)
    sigma_sr = math.sqrt(var_inner / (n_obs - 1))
    if sigma_sr <= 0:
        return 1.0
    e_max_z = expected_max_sharpe(N_trials)
    e_max_sr = sigma_sr * e_max_z
    z = (sr_obs - e_max_sr) / sigma_sr
    return 1.0 - float(stats.norm.cdf(z))


# ---------------------------------------------------------------------------
# 1) Non-XAU 2024-2025 fillback inventory
# ---------------------------------------------------------------------------
fillback = {
    "scope": "Available 2024-2025 non-XAU trade cohort sources for K54 fillback",
    "data_sources": {
        "knowledge_base_backtest_sessions": "AI-graded historical sessions per (symbol, year)",
        "trades_unified_csv": "K54 v1 unified trade ledger (151 rows)",
        "f11_mechanical_2024_2025": "Mechanical OB-retest extraction on data/historical/{SYMBOL}_M15.csv",
    },
    "kb_backtest_per_instrument_year": {
        "XAUUSD": {
            "sessions_2024": 96, "candidates_2024": 30, "trades_2024": 24,
            "sessions_2025": 183, "candidates_2025": 85, "trades_2025": 64,
            "sessions_2026": 39, "candidates_2026": 48, "trades_2026": 33,
        },
        "GBPJPY": {
            "sessions_2025": 57, "candidates_2025": 29, "trades_2025": 20,
            "sessions_2026": 57, "candidates_2026": 27, "trades_2026": 22,
        },
        "USDJPY": {
            "sessions_2025": 57, "candidates_2025": 16, "trades_2025": 15,
            "sessions_2026": 57, "candidates_2026": 22, "trades_2026": 18,
        },
        "GBPUSD": {
            "sessions_2024": 60, "candidates_2024": 10, "trades_2024": 3,
            "sessions_2025": 107, "candidates_2025": 22, "trades_2025": 18,
            "sessions_2026": 34, "candidates_2026": 4, "trades_2026": 4,
        },
        "US30_cash": {
            "sessions_2025": 63, "candidates_2025": 25, "trades_2025": 23,
            "sessions_2026": 58, "candidates_2026": 23, "trades_2026": 18,
        },
        "NZDUSD": {
            "sessions_2025": 46, "candidates_2025": 8, "trades_2025": 6,
            "sessions_2026": 57, "candidates_2026": 12, "trades_2026": 11,
        },
    },
    "kb_backtest_summary": {
        "total_executed_trades_2024": 27,
        "total_executed_trades_2025": 146,
        "total_candidates_2024": 40,
        "total_candidates_2025": 185,
        "note": (
            "AI-graded; would dilute the K54 mechanical-only cohort. "
            "Useful as supplemental validation, not primary training cohort."
        ),
    },
    "trades_unified_per_instrument_year": {
        "XAUUSD": {"2024": 14, "2025": 85, "2026": 32},
        "GBPUSD": {"2024": 3, "2025": 17},
    },
    "f11_mechanical_2024_2025_projection": {
        "method": (
            "Run extract_bos_events + find_ob_retest_outcome on "
            "data/historical/{SYMBOL}_M15.csv covering the 2024-2026 window. "
            "Schema mirrors data/historical_2022_2023/trade_cohort.csv."
        ),
        "non_xau_panel_2024_2025": {
            "GBPUSD": {"m15_first": "2024-03-31", "m15_last": "2026-04-17",
                       "span_months": 24, "trades_per_month_2022_2023": 17.0,
                       "projected_trades_2024_2025": 326},
            "USDJPY": {"m15_first": "2024-03-31", "m15_last": "2026-04-17",
                       "span_months": 24, "trades_per_month_2022_2023": 16.6,
                       "projected_trades_2024_2025": 318},
            "GBPJPY": {"m15_first": "2022-03-28", "m15_last": "2026-04-17",
                       "_note": "already covered for 2022-2023; 2024-2025 partition",
                       "span_months_2024_2025": 24,
                       "projected_trades_2024_2025": 408},
            "US30_cash": {"m15_first": "2022-01-06", "m15_last": "2026-04-17",
                          "_note": "already covered 2022-2023; 2024-2025 partition",
                          "span_months_2024_2025": 24,
                          "projected_trades_2024_2025": 384},
            "XAGUSD": {"m15_first": "2024-01-02", "m15_last": "2026-04-02",
                       "span_months": 27, "projected_trades_2024_2025": 320},
            "NAS100": {"m15_first": "2024-01-02", "m15_last": "2026-04-02",
                       "span_months": 27, "projected_trades_2024_2025": 354},
        },
        "panel_total_projected": 2110,
        "method_caveats": (
            "Assumes 2024-2025 trading-rate matches 2022-2023 panel "
            "(~16-17 trades/month). Actual yield could be plus/minus 20 percent "
            "based on regime activity. XAUUSD 2024-2025 has 108 in K54 v1 already."
        ),
    },
    "fillback_recommendation": {
        "primary": (
            "Run F11 mechanical OB-retest extraction on 2024-2025 OHLCV for "
            "6 non-XAU symbols (~1760-2110 additional mechanical trades)."
        ),
        "secondary": (
            "Defer kb_backtest sessions integration; AI-graded contamination "
            "risk on a mechanical-only research substrate."
        ),
        "wallclock_estimate": (
            "1-2 hours for BOS extraction on all 6 instruments; +2-3 hours for "
            "v2-feature compute (parallel)."
        ),
    },
}

with (OUT / "agent_e_non_xau_fillback_inventory.json").open(
    "w", encoding="utf-8"
) as fh:
    json.dump(fillback, fh, indent=2)


# ---------------------------------------------------------------------------
# 2) Pre-2022 broker depth probe results
# ---------------------------------------------------------------------------
pre_2022 = {
    "probe_date": "2026-04-29",
    "method": "MT5.copy_rates_from_pos(symbol, tf, 0, 99999) on FN-Server 2 LIVE",
    "broker": "redacted_account-Server 2 (live 100k 2-Step, account 0)",
    "_caveat": (
        "Read-only probe; no order_send paths invoked; live orchestrators "
        "uninterrupted."
    ),
    "per_instrument_max_depth": {
        "XAUUSD": {
            "M15": {"oldest": "2022-01-31T01:45", "newest": "2026-04-28T23:45",
                    "n": 99999, "span_days": 1548,
                    "_cap_reason": "broker M15 limit (99999 bars ~2.85 yr)"},
            "H1": {"oldest": "2019-12-23T02:00", "newest": "2026-04-28T23:00",
                   "n": 37491, "span_days": 2318,
                   "_cap_reason": "broker history end (~6.4 yr)"},
            "H4": {"oldest": "2019-12-23T00:00", "newest": "2026-04-28T20:00",
                   "n": 9811, "span_days": 2318},
            "D1": {"oldest": "2019-12-23T00:00", "newest": "2026-04-28T00:00",
                   "n": 1637, "span_days": 2318},
        },
        "XAGUSD": {
            "M15": {"oldest": "2021-12-15T17:30", "newest": "2026-04-28T23:45",
                    "n": 99999, "span_days": 1595},
            "H1": {"oldest": "2019-12-23T01:00", "newest": "2026-04-28T23:00",
                   "n": 36258, "span_days": 2318},
            "H4": {"oldest": "2019-12-23T00:00", "newest": "2026-04-28T20:00",
                   "n": 9783, "span_days": 2318},
            "D1": {"oldest": "2019-12-23T00:00", "newest": "2026-04-28T00:00",
                   "n": 1634, "span_days": 2318},
        },
        "USDJPY": {
            "M15": {"oldest": "2022-04-12T22:45", "newest": "2026-04-29T00:15",
                    "n": 99999, "span_days": 1477},
            "H1": {"oldest": "2008-09-04T23:00", "newest": "2026-04-29T00:00",
                   "n": 41419, "span_days": 6445,
                   "_note": "17.6 years H1 history"},
            "H4": {"oldest": "2008-09-04T20:00", "newest": "2026-04-29T00:00",
                   "n": 12182, "span_days": 6445},
            "D1": {"oldest": "2008-09-04T00:00", "newest": "2026-04-29T00:00",
                   "n": 3992, "span_days": 6446},
        },
        "GBPUSD": {
            "M15": {"oldest": "2022-04-12T22:45", "newest": "2026-04-29T00:15",
                    "n": 99999, "span_days": 1477},
            "H1": {"oldest": "2010-02-03T10:00", "newest": "2026-04-29T00:00",
                   "n": 99999, "span_days": 5928,
                   "_note": "16+ years H1 history"},
            "H4": {"oldest": "2008-09-04T20:00", "newest": "2026-04-29T00:00",
                   "n": 26934, "span_days": 6445},
            "D1": {"oldest": "2008-09-04T00:00", "newest": "2026-04-29T00:00",
                   "n": 4563, "span_days": 6446},
        },
        "GBPJPY": {
            "M15": {"oldest": "2022-04-12T15:00", "newest": "2026-04-29T00:15",
                    "n": 99999, "span_days": 1477},
            "H1": {"oldest": "2010-02-02T15:00", "newest": "2026-04-29T00:00",
                   "n": 99999, "span_days": 5929, "_note": "16+ years"},
            "H4": {"oldest": "1993-04-19T20:00", "newest": "2026-04-29T00:00",
                   "n": 43711, "span_days": 12062,
                   "_note": "33 years (longest H4 of any pair on this broker)"},
            "D1": {"oldest": "1993-04-19T00:00", "newest": "2026-04-29T00:00",
                   "n": 8293, "span_days": 12063,
                   "_note": "33 years D1"},
        },
        "US30": {
            "M15": {"oldest": "2022-10-20T11:00", "newest": "2026-04-28T23:45",
                    "n": 72663, "span_days": 1286,
                    "_note": "broker started carrying US30 at 2022-10-20"},
            "H1": {"oldest": "2022-10-20T11:00", "newest": "2026-04-28T23:00",
                   "n": 20258, "span_days": 1286},
            "H4": {"oldest": "2022-10-20T08:00", "newest": "2026-04-28T20:00",
                   "n": 5419, "span_days": 1286},
            "D1": {"oldest": "2022-10-20T00:00", "newest": "2026-04-28T00:00",
                   "n": 908, "span_days": 1286},
        },
        "US30_cash": {
            "_note": (
                "FN broker uses 'US30' not 'US30_cash'; canonical fleet symbol "
                "is US30_cash but broker matching = US30"
            ),
            "extension_path": (
                "Re-symbol-map US30 -> US30_cash in extract_ohlcv pipeline; "
                "same broker depth as US30"
            ),
        },
        "NDX100": {
            "M15": {"oldest": "2022-10-20T11:00", "newest": "2026-04-28T23:45",
                    "n": 72678, "span_days": 1286},
            "H1": {"oldest": "2022-10-20T11:00", "newest": "2026-04-28T23:00",
                   "n": 20264, "span_days": 1286},
            "H4": {"oldest": "2022-10-20T08:00", "newest": "2026-04-28T20:00",
                   "n": 5417, "span_days": 1286},
            "D1": {"oldest": "2022-10-20T00:00", "newest": "2026-04-28T00:00",
                   "n": 908, "span_days": 1286},
        },
    },
    "M1_depth_probe": {
        "_purpose": (
            "Determine M1 OHLCV availability for the 14 catalog M1-required "
            "features"
        ),
        "XAUUSD": {"M1_oldest": "2026-01-15", "M1_newest": "2026-04-28",
                   "span_days": 103,
                   "_cap": "99999-bar broker limit at M1 frequency"},
        "GBPJPY": {"M1_oldest": "2026-01-21", "M1_newest": "2026-04-29",
                   "span_days": 97},
        "USDJPY": {"M1_oldest": "2026-01-21", "M1_newest": "2026-04-29",
                   "span_days": 97},
        "verdict": (
            "M1 OHLCV is CAPPED at ~3.3 months from MT5; pre-2026 M1 backfill "
            "is not feasible from broker; would require M15->M1 reconstruction "
            "(synthetic) or third-party data source (Dukascopy / Histdata)."
        ),
    },
    "max_feasible_extension_per_instrument": {
        "XAUUSD": {"M15_back_to": "2022-01-31",
                   "H1+_back_to": "2019-12-23",
                   "comment": "Cannot reach pre-2022 M15; H1+ to 2019"},
        "XAGUSD": {"M15_back_to": "2021-12-15",
                   "H1+_back_to": "2019-12-23",
                   "comment": "Same as XAU; ~2 months earlier M15"},
        "USDJPY": {"M15_back_to": "2022-04-12",
                   "H1+_back_to": "2008-09-04",
                   "comment": "M15 capped 2022; H1+ 17 years history"},
        "GBPUSD": {"M15_back_to": "2022-04-12",
                   "H1+_back_to": "2008-09-04",
                   "comment": "Same; H1+ to 2008"},
        "GBPJPY": {"M15_back_to": "2022-04-12",
                   "H1+_back_to": "2010-02-02",
                   "H4+_back_to": "1993-04-19",
                   "comment": "Longest H4/D1 history (33 years from 1993)"},
        "US30 (US30_cash)": {"M15_back_to": "2022-10-20",
                             "H1+_back_to": "2022-10-20",
                             "comment": "Broker only carries US30 from 2022-10-20"},
        "NAS100 (NDX100)": {"M15_back_to": "2022-10-20",
                            "H1+_back_to": "2022-10-20",
                            "comment": "Same broker-side cutoff as US30"},
    },
    "pre_2022_extension_strategy": {
        "M15_only_features": (
            "NOT FEASIBLE pre-2022 - broker M15 depth caps at 2022-01 across "
            "the fleet (XAU/XAG: Jan 2022; FX: Apr 2022; indices: Oct 2022)."
        ),
        "H1+_features_subset": {
            "feasible": True,
            "scope": (
                "~300 of 1219 catalog features depend only on H1/H4/D1 OHLCV"
            ),
            "extension_window": (
                "USDJPY/GBPUSD/GBPJPY: 2008-09 onward (17.5 years available); "
                "XAU/XAG: 2019-12 onward (6.4 years)"
            ),
            "trade_cohort_yield_pre_2022": {
                "USDJPY_2010_2021": ("~12 years x 12 mo x ~14 trades/mo "
                                     "(H1 BOS rate) = ~2016 trades"),
                "GBPUSD_2010_2021": "~12 years x ~14 trades/mo = ~2016 trades",
                "GBPJPY_2010_2021": "~12 years x ~14 trades/mo = ~2016 trades",
                "XAUUSD_2020_2021": "~2 years x ~14 trades/mo = ~336 trades",
                "panel_total": "~6384 H1-only mechanical trades pre-2022",
            },
            "tradeoff": (
                "Drop ~75 percent of catalog (M15+M1 features). The H1+ "
                "feature subset can still inform K54 architecture B but with "
                "less precision. Recommend as Phase 3 stretch, not Phase 2."
            ),
        },
        "third_party_extension": {
            "options": [
                "Dukascopy historical-tick API: M1 OHLCV from 2008+ for FX",
                "Histdata.com: FX M1 OHLCV from 2000+ for major pairs, free",
                "MetaQuotes broker history: requires DLL hook, complex",
            ],
            "feasibility": (
                "MEDIUM - would require careful schema reconciliation with "
                "FN-broker M15 used in 2022-2023 backfill; risk of micro-bias "
                "due to alternate broker spreads"
            ),
            "recommended": (
                "Defer to Q3 if Phase 2 cohort proves insufficient; Phase 2 "
                "priority is NOT pre-2022 extension"
            ),
        },
    },
}

with (OUT / "agent_e_pre_2022_extension.json").open("w", encoding="utf-8") as fh:
    json.dump(pre_2022, fh, indent=2)


# ---------------------------------------------------------------------------
# 3) DSR projection: scenario x lift -> DSR-p (CSV)
# ---------------------------------------------------------------------------
import csv

base_n = 528
base_SR = 1.2748
T_paths = 15

scenarios = [
    ("status_quo", 528,
     "Q1.3 cohort (528 v2-feature substrate)"),
    ("phase2_minimum", 2326,
     "+ 2022-2023 5-symbol v2-feature backfill (1798)"),
    ("phase2_aggressive_a", 3132,
     "+ GBPJPY+US30 2022-2023 v2 (390+416)"),
    ("phase2_aggressive_b", 4892,
     "+ non-XAU 2024-2025 mechanical fillback (~1760)"),
    ("phase2_maximum", 9892,
     "+ pre-2022 FX H1 history (~5000)"),
    ("theoretical_max", 14892,
     "+ synthetic GARCH-EVT augmentation (~5000)"),
]

trial_budgets = [50, 100, 200, 500, 1000]
lifts = [0.030, 0.040, 0.0484, 0.060, 0.080, 0.100, 0.150, 0.200]

with (OUT / "agent_e_dsr_projection.csv").open("w", encoding="utf-8",
                                               newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["scenario", "scenario_n", "scenario_description",
                "lift_paired_AUC", "trial_budget_N", "T_paths",
                "projected_paired_SR", "DSR_p", "verdict"])
    for sname, sn, sdesc in scenarios:
        for lift in lifts:
            sr_per_lift = base_SR / 0.0484
            base_lift_SR = lift * sr_per_lift
            sr_proj = base_lift_SR * math.sqrt(sn / base_n)
            for N in trial_budgets:
                p = dsr_p_value(sr_proj, T_paths, N)
                verdict = ("SURVIVES" if p < 0.01 else
                           "BORDERLINE" if p < 0.05 else "FAILS")
                w.writerow([sname, sn, sdesc, f"{lift:.4f}", N, T_paths,
                            f"{sr_proj:.4f}", f"{p:.4f}", verdict])

# ---------------------------------------------------------------------------
# 4) DSR threshold scan: at observed lift 0.0484, what (n, T) jointly survive?
# ---------------------------------------------------------------------------
threshold_scan = {
    "methodology": "AFML eq 11.5 with skew=0, kurt=3 (matches Agent B forensic)",
    "fixed": {"lift_paired_AUC": 0.0484, "T_paths": 15},
    "verdicts": [],
}
for N in [50, 100, 200, 500, 1000]:
    for n_tgt in range(528, 30000, 100):
        sr_proj = base_SR * math.sqrt(n_tgt / base_n)
        p = dsr_p_value(sr_proj, T_paths, N)
        if p < 0.01:
            threshold_scan["verdicts"].append({
                "trial_budget_N": N,
                "n_threshold_DSR_lt_0_01": n_tgt,
                "projected_paired_SR": round(sr_proj, 3),
                "DSR_p_at_threshold": round(p, 4),
            })
            break
    else:
        threshold_scan["verdicts"].append({
            "trial_budget_N": N,
            "n_threshold_DSR_lt_0_01": "infeasible_under_30000",
            "comment": (
                "At observed lift 0.0484, sqrt-n SR scaling never delivers "
                "DSR<0.01 within reasonable cohort size at this N; reduce N "
                "via ONC clustering, increase T_paths, or shift methodology."
            ),
        })

# Joint T x n exploration
joint = []
for T in [15, 20, 25, 30, 40, 50]:
    for n_tgt in [528, 2326, 3132, 4892, 9892, 14892]:
        sr_proj = base_SR * math.sqrt(n_tgt / base_n)
        p = dsr_p_value(sr_proj, T, 200)
        joint.append({
            "T_paths": T,
            "cohort_n": n_tgt,
            "projected_SR": round(sr_proj, 3),
            "DSR_p_N200": round(p, 4),
            "verdict": ("SURVIVES" if p < 0.01 else
                        "BORDERLINE" if p < 0.05 else "FAILS"),
        })
threshold_scan["joint_T_n_at_N200_lift_0_0484"] = joint

# Required T at each n for DSR<0.01 at N=200
req_T = []
for n_tgt in [2326, 3132, 4892, 9892, 14892]:
    sr_proj = base_SR * math.sqrt(n_tgt / base_n)
    for T in range(15, 1000):
        p = dsr_p_value(sr_proj, T, 200)
        if p < 0.01:
            req_T.append({"cohort_n": n_tgt, "T_paths_required": T,
                          "projected_SR": round(sr_proj, 3)})
            break
threshold_scan["required_T_paths_at_N200_lift_0_0484"] = req_T

# Max trial-budget N for DSR<0.01 at observed SR
max_N = []
for n_tgt in [528, 2326, 3132, 4892, 9892]:
    sr_proj = base_SR * math.sqrt(n_tgt / base_n)
    survives_until = None
    for N in [10, 20, 30, 50, 75, 100, 150, 200, 300, 500, 1000]:
        p = dsr_p_value(sr_proj, T_paths, N)
        if p < 0.01:
            survives_until = N
        else:
            break
    max_N.append({"cohort_n": n_tgt,
                  "max_N_DSR_lt_0_01_T15": survives_until or "<10"})
threshold_scan["max_trial_budget_N_at_T15_lift_0_0484"] = max_N

with (OUT / "agent_e_dsr_threshold_scan.json").open("w",
                                                    encoding="utf-8") as fh:
    json.dump(threshold_scan, fh, indent=2)

print("DSR threshold scan results:")
for v in threshold_scan["verdicts"]:
    print(" ", v)
print("Joint T x n at N=200 (sample):")
for v in joint[:6]:
    print(" ", v)

print("\nWrote:")
print(" -", OUT / "agent_e_non_xau_fillback_inventory.json")
print(" -", OUT / "agent_e_pre_2022_extension.json")
print(" -", OUT / "agent_e_dsr_projection.csv")
print(" -", OUT / "agent_e_dsr_threshold_scan.json")
