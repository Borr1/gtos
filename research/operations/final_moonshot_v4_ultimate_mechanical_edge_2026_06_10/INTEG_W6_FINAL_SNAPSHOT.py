"""INTEG_W6_FINAL_SNAPSHOT.py — FINAL Wave-6 consolidation snapshot (the deploy book of record).

Assembles the FINAL deploy book numbers by reading the LOCKED Wave-5/6 artifacts (no re-mining;
the binding vol-matched MC was already run by the integrators and the KB6 builder tracks). This
script CITES those locked results into one machine-readable snapshot that PORTFOLIO_BUILD_W6.md +
ULTIMATE_GO_LIVE_DOSSIER.md reference, and re-asserts module<->artifact parity so the dossier numbers
are reproducible. It performs NO heavy compute and pulls ZERO data loaders.

Sources of truth (all locked, reproduced byte-identically by their integrators / KB6 builders):
  INTEG_W5_CLEAN3_DEPLOY.json        clean_3 deploy book (MC grids, 2-account, daily-breach)
  INTEG_GOLIVE_SNAPSHOT_RESULT.json  net-of-fills erosion per sleeve (W3 exec-realism)
  KB6_SESSION_STACKS_RESULT.json     clean_4 additive (session_leadlag_genuine) folded numbers
  KB6_COMBINE_RESULT.json            stress-hardening overlay grids (reactive / full stack)
  KB6_OVERLAY_PASSRATE_RESULT.json   VP-acceptance exit-honest stress numbers
  KB6_ROUTER_RESULT.json             confluence-score router (documented-disabled)
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
import sys
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
import ultimate_book_live_package as P


def load(name: str) -> dict:
    return json.loads((HERE / name).read_text())


def main() -> dict:
    c3 = load("INTEG_W5_CLEAN3_DEPLOY.json")
    golive = load("INTEG_GOLIVE_SNAPSHOT_RESULT.json")
    sess = load("KB6_SESSION_STACKS_RESULT.json")
    comb = load("KB6_COMBINE_RESULT.json")
    overlay = load("KB6_OVERLAY_PASSRATE_RESULT.json")
    router = load("KB6_ROUTER_RESULT.json")

    # parity gate — the snapshot is only valid if the module matches the locked artifacts.
    parity = {
        "clean3": P.assert_clean3_parity(),
        "confidence": P.assert_confidence_parity(),
    }
    parity_ok = parity["clean3"]["parity_ok"] and parity["confidence"]["parity_ok"]

    fold = sess["folded_additive"]              # clean_4 = clean_3 + session_leadlag_genuine
    slg = sess["sleeve_stats"]["session_leadlag_genuine"]
    # tier-1 reactive = ladder x coloss COMBINED (KB6_stress_hardening.md Section 3: 87.48%@1% /
    # 77.60%@1.5%, forward +2.0@1%, Sharpe 0.1564). The cached COMBINE JSON carries the individual
    # ladder3 (83.87) and coloss (84.78) legs + the regime stacks; the combined reactive figure is the
    # builder's documented Section-3 result. We cite both: the JSON-reproducible legs and the doc combo.
    ladder_only = comb["combos"]["ladder3"]
    coloss_only = comb["combos"]["coloss"]
    REACTIVE_COMBINED = {  # KB6_stress_hardening.md Section 3 (ladder+coloss reactive-only)
        "stress_1pct": 0.8748, "stress_1p5pct": 0.7760, "fwd_delta_1pct": 0.020, "sharpe": 0.1564,
    }
    full = comb["combos"]["regime+ladder+coloss"]
    base = comb["baseline"]

    snap = {
        "wave": "6-FINAL",
        "book_of_record": "clean_4 (clean_3 + session_leadlag_genuine) + W6 overlays (default-off)",
        "parity_ok": parity_ok,
        "parity": parity,
        # ---- FINAL deploy book: 12 sleeves (8 core + 3 clean_3 + 1 clean_4) ----
        "final_book": {
            "n_sleeves_clean3": 11,
            "n_sleeves_clean4": 12,
            "clean3_sleeves": c3["sleeves"],
            "clean4_added": list(P.CLEAN4_REGISTRY.keys()),
            "avg_off_diag_corr_clean3": c3["avg_off_diag_corr"],
            "sharpe_book_only": 0.1396,
            "sharpe_clean3": c3["sharpe"],
            "sharpe_clean4": fold["sharpe"],
            "vol_scale_clean3": c3["vol_scale"],
            "vol_scale_clean4": fold["vol_scale"],
        },
        # ---- trades/yr (net-of-fills via pessimistic geometry_lib labeler) ----
        "trades_per_year_fwd": {
            "book_core_approx": 1512,
            "clean3_additives": {"sub_xvol_pullback": 26, "vp_euidx_pocgrav": 115, "sub_mid_dn_revert": 64},
            "clean4_session_leadlag_genuine": round(slg["fwd_per_year"]),
            "clean3_total": 1717,
            "clean4_total": 1717 + round(slg["fwd_per_year"]),
            "note": "all R net of real cost via geometry_lib.simulate; no extra slippage haircut",
        },
        # ---- net-of-fills book contribution (W3 exec-realism erosion) ----
        "net_of_fills": {
            "book_conf_wtd_unitR_per_yr_modeled": golive["book_conf_wtd_unitR_per_yr_modeled"],
            "book_conf_wtd_unitR_per_yr_net": golive["book_conf_wtd_unitR_per_yr_net"],
            "book_erosion_pct": golive["book_erosion_pct"],
        },
        # ---- P(pass) challenge-pass MC, vol-matched (the fair test) ----
        "mc_volmatched_all": c3["mc_volmatched_all"],
        "mc_volmatched_stress": c3["mc_volmatched_stress"],
        "mc_fwd": c3["mc_fwd"],
        # ---- the BINDING constraint: 1.5x left-tail stress, vol-matched ----
        "binding_stress_1pct": {
            "clean3_baseline": base["stress"]["1.00%"],
            "clean4_folded": fold["stress_1pct_vm"],
            "ladder_only": ladder_only["stress"]["1.00%"],
            "coloss_only": coloss_only["stress"]["1.00%"],
            "with_reactive_overlay_combined": REACTIVE_COMBINED["stress_1pct"],
            "with_full_stack": full["stress"]["1.00%"],
        },
        "binding_stress_1p5pct": {
            "clean3_baseline": base["stress"]["1.50%"],
            "clean4_folded": fold["stress_1p5pct_vm"],
            "ladder_only": ladder_only["stress"]["1.50%"],
            "coloss_only": coloss_only["stress"]["1.50%"],
            "with_reactive_overlay_combined": REACTIVE_COMBINED["stress_1p5pct"],
            "with_full_stack": full["stress"]["1.50%"],
            "vp_acceptance_exit_honest_from": overlay["books"]["deploy_sd"]["stress_1p5pct_vm"],
            "vp_acceptance_exit_honest_to": overlay["books"]["vpacc_replace"]["stress_1p5pct_vm"],
        },
        # ---- per-sleeve contribution + confidence (from the clean_3 deploy artifact) ----
        "sleeve_contribution": c3["sleeve_contribution"],
        # ---- daily-breach + 2-account allocation ----
        "daily_breach": c3["daily_breach"],
        "two_account": c3["two_account"],
        "two_account_stress_with_reactive": {
            "balanced_0p71": comb["two_account"]["balanced"]["base_stress_p_both"],
            "balanced_0p71_with_regime": comb["two_account"]["balanced"]["regime_stress_p_both"],
            "conservative_0p47": comb["two_account"]["conservative"]["base_stress_p_both"],
            "conservative_0p47_with_regime": comb["two_account"]["conservative"]["regime_stress_p_both"],
        },
        # ---- W6 verdicts (what folded vs what stayed overlay/intel) ----
        "w6_verdicts": {
            "session_leadlag_genuine": "FOLDED sleeve (clean_4): Sharpe 0.1522->0.1586, stress@1% "
                                       "+2.51 / @1.5% +2.03, corr +0.053, ~195 tr/yr forward-only",
            "reactive_ladder_coloss": "FOLDED overlay default-on: stress@1% 80.86->87.48 (+6.6), "
                                      "forward-positive (+2.0), Sharpe 0.1564",
            "full_stack_regime": "OPT-IN tier-2: stress@1% ->91.86 (+11.0) but regime component "
                                 "forward-flat alone -> deploy after reactive proven live",
            "vp_acceptance": "ADOPT as sub_mid_dn_revert exit-honest definition (STATE_D): stress@1.5% "
                             "69.6->74.8 (+5.2), the only confluence overlay that lifts the stress tail",
            "leader_impulse_veto": "OVERLAY only (already wired): +1.17R/trade but BOOK-pass NEGATIVE if "
                                   "folded as a sleeve (61% freq retention shrinks diversification)",
            "confluence_router": "REJECTED as sizer: +0.20R mean but ZERO stress lift (concentrates "
                                 "size into high-variance pockets); kept as live-monitoring intel",
            "metals_sess_stack": "OVERLAY only: 90%-same-trade double-count of metals_core (corr +0.65)",
            "dxy_bias": "FILTER only: n=12 fwd, no train window -> confidence-nudge not a sleeve",
        },
        "module_schema_version": P.describe_book()["schema_version"],
    }
    return snap


if __name__ == "__main__":
    snap = main()
    (HERE / "INTEG_W6_FINAL_SNAPSHOT.json").write_text(json.dumps(snap, indent=1, default=str))
    print(json.dumps({
        "parity_ok": snap["parity_ok"],
        "clean4_total_tr_yr": snap["trades_per_year_fwd"]["clean4_total"],
        "stress_1pct": snap["binding_stress_1pct"],
        "schema": snap["module_schema_version"],
    }, indent=1))
