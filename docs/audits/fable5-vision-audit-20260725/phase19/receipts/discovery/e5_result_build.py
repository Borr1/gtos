"""Assemble e5_RESULT.json from the lane's measurement receipts, so the index carries every
headline number without re-deriving anything."""
import os, json
D = os.path.dirname(os.path.abspath(__file__))
M = ["january", "february", "march"]


def L(n):
    with open(os.path.join(D, n)) as f:
        return json.load(f)


tm = L("E5_THREE_MONTHS_V1.json"); dec = L("E5_DECOMPOSITION_V1.json")
tr = L("E5_TRAIL_V1.json"); sel = L("E5_SELECTION_V1.json"); sur = L("E5_SURVIVOR_V1.json")
st = L("E5_STACK_V1.json"); cell = L("E5_CELL_V1.json"); fb = L("E5_FILLBAR_V1.json")
hy = L("E5_HYBRID_V1.json"); tc = L("E5_TIME_CURVE_V1.json"); ce = L("E5_JAN_CEILING_V1.json")
val = L("E5_JAN_VALIDATION_V1.json"); pl = L("E5_PLACEBO_V1.json"); xr = L("E5_XAU_ROBUST_V1.json")

out = {
    "lane": "e5",
    "extends": "l2 / L2-F6 (spread-floored stop + 0.25R trail; ceiling asserted zero by algebra)",
    "schema": "gtos.e5.result.v1",
    "receipt": "e5_RESULT.md",
    "reproduction": {
        "l2_13_rerun_exact": True,
        "l2_published_S20_trail_net_frozen": -0.11481,
        "l2_published_recovery_frozen": 0.67407,
        "l2_published_recovery_sp73": 0.22430,
        "independent_library_S10_net_frozen": dec["january"]["S10_frozen"]["net_as_shipped"],
        "path_rebuild_vs_CQ_sidecar": val["path_comparison"],
    },
    "data_spend_register": {
        "january_2026": "already spent (CJ pool + CQ sidecar + bridge_ftmo_m1_202601)",
        "february_2026": "already read once (CP_FEBRUARY pool) + bridge_ftmo_m1_202602 -- paths BUILT by this lane",
        "march_2026": ("already read once (fa2 March confirm). ONLY the FA2_M_R0 MISSED_OPPORTUNITY "
                       "diagnostic pool was read -- same object class as January's CJ pool. No trade "
                       "ledger, no headline economics, no arm outcome."),
        "april_2026": "NOT SPENT -- M1 sources exist (bridge_ftmo_m1_202604), NO candidate pool exists",
        "may_2026": "NOT SPENT -- M1 sources exist (bridge_ftmo_m1_202605), NO candidate pool exists",
    },
    "months": {},
}
for m in M:
    out["months"][m] = {
        "n_pool_rows": tm[m]["n_pool_rows"], "n_entries": tm[m]["n_entries"],
        "build": tm[m]["build"],
        "rules": {k: {kk: v[kk] for kk in ("n_eval", "gross_newunit", "net_frozen", "net_sp73",
                                           "k_median", "win_pct")}
                  for k, v in tm[m]["rules"].items()},
        "recovery_frozen": tm[m]["recovery_frozen"], "recovery_sp73": tm[m]["recovery_sp73"],
        "k_invariance": tm[m]["k_invariance"],
        "decomposition": {k: dec[m][k] for k in dec[m] if k.startswith(("S", "k3"))},
        "trail": {"as_shipped_G": tr[m]["as_shipped_G"],
                  "best_fixed_time": tr[m]["best_fixed_time"],
                  "trail_ladder": tr[m]["trail_ladder"],
                  "be_ladder_vs_as_shipped": tr[m]["be_ladder_vs_as_shipped"],
                  "trail025_permutation_control": tr[m]["trail025"],
                  "C_frozen": tr[m]["C_frozen"], "C_sp73": tr[m]["C_sp73"]},
        "time_curve": {k: tc[m][k] for k in ("cost", "argmax", "C0_t120", "C1_t120", "C2_t120",
                                             "stop_cost_at_120", "contract_cost_at_120")},
        "boundary_by_symbol_R2": tm[m]["by_symbol"],
        "boundary_by_family_R2": tm[m]["by_family"],
        "boundary_by_session_R2": tm[m]["by_session"],
        "survivor_by_symbol_t025": {s: {"net_sp73": v[m]["all_t025"]["net_sp73"],
                                        "net_sp73_t010": v[m]["all_t010"]["net_sp73"],
                                        "n": v[m]["all_t025"]["n"]}
                                    for s, v in sur["by_symbol"].items() if m in v},
        "cell_XAUUSD_x_current_fvg_fill": cell[m]["XAUUSD_x_current_fvg_fill"],
        "cell_XAUUSD_other_families": cell[m]["XAUUSD_all_other_families"],
        "current_fvg_fill_by_symbol_setupday": {
            s: v["one_per_setup_day"]["net_sp73"] for s, v in cell[m]["current_fvg_fill_by_symbol"].items()},
        "fillbar_conventions": fb[m],
        "hybrid_convention": {k: hy[m][k] for k in hy[m] if k != "by_symbol_t010"},
        "hybrid_by_symbol_t010": hy[m]["by_symbol_t010"],
        "xau_robustness": xr[m],
        "stack": st[m],
        "placebo": pl[m],
    }
out["january_ceiling_ladders"] = {"ladder_A": ce["ladder_A"], "ladder_B": ce["ladder_B"]}
out["selection_out_of_sample"] = sel["partB_entry_selection_sp73"]
out["shrink_factorisation"] = sel["partA_shrink_factorisation"]
out["headline"] = {
    "WIDEN_range_over_15_cells": [min(dec[m][r]["part_WIDEN"] for m in M for r in
                                      ("S2_frozen", "S5_frozen", "S10_frozen", "S20_frozen", "k3_flat")),
                                  max(dec[m][r]["part_WIDEN"] for m in M for r in
                                      ("S2_frozen", "S5_frozen", "S10_frozen", "S20_frozen", "k3_flat"))],
    "TRAIL_positive_in_all_15_cells": all(dec[m][r]["part_TRAIL"] > 0 for m in M for r in
                                          ("S2_frozen", "S5_frozen", "S10_frozen", "S20_frozen", "k3_flat")),
    "ceiling_gap_sp73": {m: tm[m]["k_invariance"]["ceiling_gap_sp73"] for m in M},
    "survivor_cell": "XAUUSD x current_fvg_fill, tight trail",
    "survivor_cell_hybrid_setupday_t010": {
        m: {"n": hy[m]["XAU_x_fvg_setupday"]["t0.10"]["n"],
            "net_sp73": hy[m]["XAU_x_fvg_setupday"]["t0.10"]["net_sp73"],
            "ci95": hy[m]["XAU_x_fvg_setupday"]["t0.10"]["ci95"],
            "net_frozen": hy[m]["XAU_x_fvg_setupday"]["t0.10"]["net_frozen"]} for m in M},
    "full_stack_final_net_sp73": {m: st[m]["steps"][6]["net"] for m in M},
}
with open(os.path.join(D, "e5_RESULT.json"), "w") as f:
    json.dump(out, f, indent=1)
print("wrote e5_RESULT.json", os.path.getsize(os.path.join(D, "e5_RESULT.json")), "bytes")
print(json.dumps(out["headline"], indent=1)[:1400])
