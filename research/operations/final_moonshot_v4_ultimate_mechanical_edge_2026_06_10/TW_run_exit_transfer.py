"""Driver: run the EXEC_COMBO / EXEC_LOCK exit transfer on crypto + energy sleeves."""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import TW_exit_transfer as T

OUT = {}

print("="*100)
print("CRYPTO SLEEVE — exit transfer (entries FIXED: BTC+DASH lb20 breakout + ac60>=0.15 + sd=2a)")
print("  baseline exit = target4 (KB_crypto locked). also compare vs STATE_D scale-out.")
print("="*100)
cents = T.build_crypto_entries()
print(f"crypto entries: {len(cents)} (BTC {sum(1 for e in cents if e['sym']=='BTCUSD')}, "
      f"DASH {sum(1 for e in cents if e['sym']=='DASHUSD')})\n")
c_base = T.run_policy(cents, T.exit_target4)
c_sd   = T.run_policy(cents, T.exit_state_d_via_sim)
c_comb = T.run_policy(cents, T.exit_combo)
c_lock = T.run_policy(cents, T.exit_lock)
r_cbase = T.report("target4 (BASELINE)", c_base)
r_csd   = T.report("STATE_D", c_sd)
r_ccomb = T.report("EXEC_COMBO", c_comb)
r_clock = T.report("EXEC_LOCK", c_lock)
print()
T.paired(c_base, c_comb, "COMBO-target4 (ALL)")
T.paired(c_base, c_lock, "LOCK-target4 (ALL)")
T.paired(c_sd,   c_comb, "COMBO-STATE_D (ALL)")
# forward-only paired
cb_f = [r for r in c_base if r['year']>=2025]; cc_f=[r for r in c_comb if r['year']>=2025]
cl_f = [r for r in c_lock if r['year']>=2025]
T.paired(cb_f, cc_f, "COMBO-target4 (FWD)")
T.paired(cb_f, cl_f, "LOCK-target4 (FWD)")
T.per_regime(c_base, "target4")
T.per_regime(c_comb, "EXEC_COMBO")
OUT['crypto'] = dict(target4=r_cbase, state_d=r_csd, exec_combo=r_ccomb, exec_lock=r_clock,
                     n=len(cents))

print("\n"+"="*100)
print("ENERGY SLEEVE — exit transfer (entries FIXED: ENERGY FVG + A/B gate vr>=2 OR |slope|<.05)")
print("  baseline exit = STATE_D scale-out (KB_energy locked).")
print("="*100)
eents = T.build_energy_entries()
bysym = {}
for e in eents: bysym[e['sym']] = bysym.get(e['sym'], 0)+1
print(f"energy entries: {len(eents)} ({bysym})\n")
e_sd   = T.run_policy(eents, T.exit_state_d_via_sim)
e_comb = T.run_policy(eents, T.exit_combo)
e_lock = T.run_policy(eents, T.exit_lock)
r_esd   = T.report("STATE_D (BASELINE)", e_sd)
r_ecomb = T.report("EXEC_COMBO", e_comb)
r_elock = T.report("EXEC_LOCK", e_lock)
print()
T.paired(e_sd, e_comb, "COMBO-STATE_D (ALL)")
T.paired(e_sd, e_lock, "LOCK-STATE_D (ALL)")
esd_f=[r for r in e_sd if r['year']>=2025]; ec_f=[r for r in e_comb if r['year']>=2025]
el_f=[r for r in e_lock if r['year']>=2025]
T.paired(esd_f, ec_f, "COMBO-STATE_D (FWD)")
T.paired(esd_f, el_f, "LOCK-STATE_D (FWD)")
# train paired (energy has real pre-2025: USOIL 2021, NATGAS 2024H2)
esd_t=[r for r in e_sd if r['year']<=2024]; ec_t=[r for r in e_comb if r['year']<=2024]
el_t=[r for r in e_lock if r['year']<=2024]
T.paired(esd_t, ec_t, "COMBO-STATE_D (TRAIN<=2024)")
T.paired(esd_t, el_t, "LOCK-STATE_D (TRAIN<=2024)")
T.per_regime(e_sd, "STATE_D")
T.per_regime(e_comb, "EXEC_COMBO")
# per-tag (supply_shock vs flat_breakout) forward
print("   per-tag (FWD 2025-26): STATE_D vs COMBO")
for tag in ('energy_supply_shock','energy_flat_breakout'):
    idxs=[k for k,e in enumerate(eents) if e['tag']==tag and e['year']>=2025]
    sd_t=T.stats([e_sd[k] for k in idxs]); cm_t=T.stats([e_comb[k] for k in idxs])
    if sd_t['n']: print(f"      {tag:<22} n{sd_t['n']:>3} STATE_D ev{sd_t['ev']:+.3f} -> COMBO ev{cm_t['ev']:+.3f}")
OUT['energy'] = dict(state_d=r_esd, exec_combo=r_ecomb, exec_lock=r_elock, n=len(eents))

(HERE/'TW_EXIT_TRANSFER_RESULT.json').write_text(json.dumps(OUT, indent=1, default=str))
print("\nwrote TW_EXIT_TRANSFER_RESULT.json")
