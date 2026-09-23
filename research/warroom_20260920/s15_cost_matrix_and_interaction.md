# S15 cost matrix + G4×G6 interaction — 2026-09-20 08:48 ICT

## S15 cost classes (tape R only)
### false_admit n=29 sum_tape_R=-28.9172 sum_shadow_R=-13.5428
- `fs_half_still_losing` n=21 tape=-21.4804 shadow=-8.7127
- `event_gap_shadow` n=3 tape=-3.1387 shadow=-1.3063
- `session_cut_loss` n=4 tape=-3.0974 shadow=-2.3231
- `full_size_loss` n=1 tape=-1.2007 shadow=-1.2007
### false_abstain n=0 missed_tape_R=0
- none — no REJECT blocked a tape winner
### review n=2
- {'ticket': 293128383, 'asset': 'XAU', 'sleeve': 'sub_mid_dn_re', 'session': 'Off_hours', 'exit': 'orig_stop', 'miss': 'false_structure', 'tape_R': -0.94, 'shadow_R': -0.94, 'size_mult': 1.0, 'admission': 'ADMIT', 'rules': ['G7_KEEP_NO_BOOST_MAX1', 'G8_ORIG_STOP_NO_SILENT_REENTRY']}
### cost_avoided_by_reject n=23 sum_tape_blocked=-24.6586
- by_asset {'CRYPTO': {'n': 3, 'sum_tape_R_blocked': -3.28}, 'FX': {'n': 4, 'sum_tape_R_blocked': -4.74}, 'INDEX': {'n': 16, 'sum_tape_R_blocked': -16.6386}}

## G4×G6 overshrink check
Q: Does G6+G4 double-cut overshrink XAU almost-wins?
Verdict: overshrink=False — Only G6 session cut on nonkeep wins (e.g. 292667008) — acceptable per Chair; no G4+G6 double-cut on wins
double_cut_wins=[]
g6_only_wins=[{'ticket': 292667008, 'sleeve': 'dsp_three_fresh', 'session': 'NY', 'tape_R': 3.41, 'shadow_R': 2.5575, 'size_mult': 0.75, 'shrink': 0.8525}]
g4_only_wins=[]
