"""KB5 comparison: STATE_D re-score vs fixed-barrier substrate.
Compares on the (dir, state-coords) tuple since STATE_D drops target_R.
Reports: cells that STRENGTHEN, NEW cells crossing the trust bar under STATE_D,
and the per-year train+forward of the headline cells."""
import sys, json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent

fixed = json.load(open(HERE / "SUBSTRATE_TOP_EDGES.json"))["edges"]
sd = json.load(open(HERE / "KB5_STATE_D_RESCORE.json"))


def state_of_fixed(cell):
    """fixed cell 'g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|...' -> (dmode, frozenset(conds))"""
    parts = cell.split("|")
    dmode = parts[1].split("=")[1]
    conds = frozenset(parts[3:])
    return dmode, conds


def state_of_sd(cell):
    """sd cell 'sd1.0|dir=1|depth4|vol=xhi|...' -> (dmode, frozenset(conds))"""
    parts = cell.split("|")
    dmode = parts[1].split("=")[1]
    conds = frozenset(parts[3:])
    return dmode, conds


# index fixed edges by (dir,state) -> best (by min(tr,fw)) variant
fixed_by_state = {}
for e in fixed:
    k = state_of_fixed(e["cell"])
    score = min(e["meanR_train"], e["meanR_fwd"])
    if k not in fixed_by_state or score > min(fixed_by_state[k]["meanR_train"], fixed_by_state[k]["meanR_fwd"]):
        fixed_by_state[k] = e

# index STATE_D forward-validated edges (deployed stop_atr=1.0 only for fair apples-apples)
sd_edges_all = sd["edges"]
sd_dep = [e for e in sd_edges_all if e["stop_atr"] == 1.0]
sd_by_state = {}
for e in sd_dep:
    k = state_of_sd(e["cell"])
    score = min(e["meanR_train"], e["meanR_fwd"])
    if k not in sd_by_state or score > min(sd_by_state[k]["meanR_train"], sd_by_state[k]["meanR_fwd"]):
        sd_by_state[k] = e

print(f"fixed (dir,state) tuples that forward-validated: {len(fixed_by_state)}")
print(f"STATE_D deployed-stop (dir,state) tuples that forward-validated: {len(sd_by_state)}")
print(f"STATE_D forward-validated cells total (all stop_atrs): {len(sd_edges_all)}, deployed-stop only: {len(sd_dep)}")

both = set(fixed_by_state) & set(sd_by_state)
only_sd = set(sd_by_state) - set(fixed_by_state)
only_fixed = set(fixed_by_state) - set(sd_by_state)
print(f"\n(dir,state) in BOTH: {len(both)} | NEW under STATE_D only: {len(only_sd)} | "
      f"fixed-only (lost under STATE_D): {len(only_fixed)}")

# --- look up STATE_D rescore for EVERY fixed (dir,state), even if it didn't cross the bar ---
# need the full STATE_D cmap for that
sd_cells = sd["cells"]
def sd_lookup(dmode, conds):
    """find the deployed-stop STATE_D cell for this (dir,state) in the full cmap."""
    for ck, c in sd_cells.items():
        if not ck.startswith("sd1.0|"): continue
        p = ck.split("|")
        if p[1].split("=")[1] != dmode: continue
        if frozenset(p[3:]) == conds:
            return c
    return None

print("\n" + "="*120)
print("EVERY fixed forward-validated (dir,state) — its FIXED best meanR vs its STATE_D meanR (deployed stop_atr=1.0)")
print("="*120)
print(f"{'dir':>4}{'fixTgt':>7}{'fixRtr':>8}{'fixRfw':>8}|{'sdRtr':>8}{'sdRfw':>8}{'sdWfw':>7}{'sdNtr':>6}{'sdNfw':>6}  {'VAL':>4}  state")
rows = []
for k in sorted(fixed_by_state, key=lambda kk: -min(fixed_by_state[kk]["meanR_train"], fixed_by_state[kk]["meanR_fwd"])):
    fe = fixed_by_state[k]
    dmode, conds = k
    c = sd_lookup(dmode, conds)
    state_str = "|".join(sorted(conds))
    if c and c["train"] and c["fwd"]:
        sdtr = c["train"]["mean_R"]; sdfw = c["fwd"]["mean_R"]
        sdwfw = c["fwd"]["win_pct"]; sdntr = c["train"]["n"]; sdnfw = c["fwd"]["n"]
        val = "YES" if k in sd_by_state else "no"
    else:
        sdtr = sdfw = sdwfw = sdntr = sdnfw = None; val = "n/a"
    rows.append(dict(dir=dmode, conds=state_str, fixTgt=fe["target_R"],
                     fixRtr=fe["meanR_train"], fixRfw=fe["meanR_fwd"],
                     sdRtr=sdtr, sdRfw=sdfw, sdWfw=sdwfw, sdNtr=sdntr, sdNfw=sdnfw, val=val))
    ds = "L" if dmode=="1" else "S"
    fmt=lambda v: f"{v:>+8.3f}" if isinstance(v,(int,float)) else f"{'--':>8}"
    print(f"{ds:>4}{fe['target_R']:>7.1f}{fe['meanR_train']:>+8.3f}{fe['meanR_fwd']:>+8.3f}|"
          f"{fmt(sdtr)}{fmt(sdfw)}{(str(sdwfw)+'%').rjust(7) if sdwfw is not None else '--'.rjust(7)}"
          f"{(sdntr if sdntr else '--'):>6}{(sdnfw if sdnfw else '--'):>6}  {val:>4}  {state_str}")

# strengthen = STATE_D fwd meanR > fixed best fwd meanR AND still validates
strengthen = [r for r in rows if r["val"]=="YES" and r["sdRfw"] is not None and r["sdRfw"] > r["fixRfw"]]
weaken = [r for r in rows if r["sdRfw"] is not None and r["sdRfw"] < r["fixRfw"]]
print(f"\nfixed cells whose FWD meanR STRENGTHENS under STATE_D (and still validates): {len(strengthen)}")
print(f"fixed cells whose FWD meanR is lower under STATE_D: {len(weaken)}")

print("\n" + "="*120)
print(f"NEW (dir,state) cells crossing the trust bar under STATE_D that were NOT in the fixed set ({len(only_sd)})")
print("="*120)
print(f"{'dir':>4}{'sdRtr':>8}{'sdRfw':>8}{'sdWfw':>7}{'Ntr':>6}{'Nfw':>6}{'Tyr':>6}{'Fyr':>6}  state")
new_sorted = sorted(only_sd, key=lambda kk: -min(sd_by_state[kk]["meanR_train"], sd_by_state[kk]["meanR_fwd"]))
for k in new_sorted:
    e = sd_by_state[k]
    ds = "L" if k[0]=="1" else "S"
    state_str = "|".join(sorted(k[1]))
    print(f"{ds:>4}{e['meanR_train']:>+8.3f}{e['meanR_fwd']:>+8.3f}{str(e['win_fwd'])+'%':>7}"
          f"{e['n_train']:>6}{e['n_fwd']:>6}{e['pos_train_years']:>3}/{e['total_train_years']:<2}"
          f"{e['pos_fwd_years']:>3}/{e['total_fwd_years']:<2}  {state_str}")

# dump structured comparison
out = {
    "n_fixed_states": len(fixed_by_state),
    "n_sd_states_deployed": len(sd_by_state),
    "n_both": len(both), "n_new_under_sd": len(only_sd), "n_lost_under_sd": len(only_fixed),
    "n_strengthen": len(strengthen), "n_weaken": len(weaken),
    "fixed_vs_sd_rows": rows,
    "new_under_sd": [dict(dir=("L" if k[0]=="1" else "S"), state="|".join(sorted(k[1])),
                          meanR_train=sd_by_state[k]["meanR_train"], meanR_fwd=sd_by_state[k]["meanR_fwd"],
                          win_fwd=sd_by_state[k]["win_fwd"], n_train=sd_by_state[k]["n_train"],
                          n_fwd=sd_by_state[k]["n_fwd"],
                          pos_train_years=sd_by_state[k]["pos_train_years"], total_train_years=sd_by_state[k]["total_train_years"],
                          pos_fwd_years=sd_by_state[k]["pos_fwd_years"], total_fwd_years=sd_by_state[k]["total_fwd_years"],
                          per_year=sd_by_state[k]["per_year"], per_class_fwd=sd_by_state[k]["per_class_fwd"])
                     for k in new_sorted],
}
(HERE / "KB5_COMPARE_RESULT.json").write_text(json.dumps(out, indent=1, default=str))
print("\nwrote KB5_COMPARE_RESULT.json")
