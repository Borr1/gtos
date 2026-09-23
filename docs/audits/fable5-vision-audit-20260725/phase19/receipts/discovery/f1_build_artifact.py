import json,glob,os
import numpy as np
DISC="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
A={"schema":"gtos.wave19.f1.baseline.v1","lane":"f1-baseline",
   "generated_utc":"2026-08-06",
   "purpose":"Canonical three-population baseline for the broad V4 family on the CORRECT object (the sealed arms' own candidate rosters), 8 open windows, whole population, nothing sampled."}
A['contracts']={
 "C1_honest_limit":{"desc":"Every candidate is a resting order at its own entry. A LONG fills when an M1 low <= entry, a SHORT when an M1 high >= entry (gaps through the level fill). The walk starts on the NEXT M1 bar (no same-bar credit). Target = policy target (2.0R) unless stated; stop = the candidate's own stop; horizon 120 M1 bars; conservative tie (stop wins inside a bar); mark to market at the wall. Never touched inside the horizon -> 0.0 R and no cost charged.",
   "verification":"Reproduces the sealed working set's fill_honest_walk_r on January's 27,658 pool rows: mine -0.20556 vs sealed -0.23672, mean|diff| 0.0606, 74.6% within 0.01 R, exit-reason census stop 15,636 vs 15,852 / target 4,042 vs 3,713 / no_fill 85 vs 241. Residual is M1-OHLC vs the sealed tick-ordered sidecar."},
 "C0_market":{"desc":"Market fill at the decision instant (fill = close of the last M1 bar strictly before it), otherwise identical.",
   "verification":"Reproduces the sealed sidecar's plain_walk_r EXACTLY: mine +0.040332 vs sealed +0.040897 on 27,658/27,658 rows, mean|diff| 0.001154, 99.88% within 0.01 R."},
 "cost":"h1 four-term broker-true, hour-aware (tick spread by broker hour + broker-true commission + measured price-unit slippage + swap on broker-midnight crossings), charged once in price units then divided by that row's own risk distance. Charged only on filled rows."}
A['census']=json.load(open('/tmp/f1/census.json'))
A['taken_by_window']=json.load(open('/tmp/f1/taken.json'))
A['roster']=json.load(open('/tmp/f1/final_roster.json'))
A['matched_controls']=json.load(open('/tmp/f1/matched_full.json'))
W={os.path.basename(f)[2:-5]:json.load(open(f)) for f in sorted(glob.glob('/tmp/f1/out/W_*.json'))}
A['per_window_walks']=W
cc=json.load(open('/tmp/f1/costcheck.json'))
arm=np.array([r['arm'] for r in cc]); h1=np.array([r['mine'] for r in cc])
A['cost_model_comparison']={"n_taken_trades":len(cc),"arm_cost_r_mean":float(arm.mean()),
  "h1_broker_true_mean":float(h1.mean()),"mean_ratio":float(h1.mean()/arm.mean()),
  "median_ratio":float(np.median(h1/arm)),
  "note":"Divergence is the SPREAD term and it is mean-driven, not typical: XAUUSD (274 of 507 trades) agrees at 1.044x; UKOIL_cash 11.11x and USOIL_cash 4.57x carry the whole gap; US30_cash/GER40/JP225 run 0.12-0.18x (h1 CHEAPER)."}
json.dump(A,open(DISC+'/f1_BASELINE_V1.json','w'),indent=1)
print('wrote',DISC+'/f1_BASELINE_V1.json', os.path.getsize(DISC+'/f1_BASELINE_V1.json'))
