"""d3 A: structural geometry of the LIVE sleeves, measured from AQ_ESTATE_TRADES_V2."""
import gzip, json, statistics as st
from pathlib import Path
import numpy as np

ROOT = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
P = ROOT/"docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
o = json.load(gzip.open(P, "rt"))
T = o["trades"]
tfby = o.get("timeframe_by_sleeve", {})
exc  = o.get("exit_contracts", {})

LIVE = ["crypto","energy_agri","sub_xvol_pullback","sub_mid_dn_revert",
        "mx_btcusd_d1_donchian_20_breakout"]
out = {}
for sl, rows in T.items():
    if not rows: continue
    bps=[]; tgt=[]; hold=[]; mfe=[]; mae=[]; rg=[]; b2m=[]; syms={}
    days=set(); reasons={}
    for r in rows:
        e = r.get("entry_price"); d = r.get("sl_distance_price")
        if e and d and e>0: bps.append(d/abs(e)*1e4)
        td = r.get("target_dist")
        if td and d: tgt.append(td/d)
        if r.get("hold_hours") is not None: hold.append(r["hold_hours"])
        if r.get("mfe_r") is not None: mfe.append(r["mfe_r"])
        if r.get("mae_r") is not None: mae.append(r["mae_r"])
        if r.get("r_gross") is not None: rg.append(r["r_gross"])
        if r.get("bars_to_mfe") is not None: b2m.append(r["bars_to_mfe"])
        syms[r.get("symbol_canonical") or r.get("symbol")] = 1
        days.add(r.get("decision_day"))
        reasons[r.get("exit_reason")] = reasons.get(r.get("exit_reason"),0)+1
    def q(a,p):
        return float(np.percentile(a,p)) if a else None
    tf = tfby.get(sl)
    tf_min = tf if isinstance(tf,(int,float)) else None
    # hours from mfe bar
    mfeh = [b*(tf_min/60.0) for b in b2m] if (b2m and tf_min) else []
    out[sl] = dict(
        n=len(rows), timeframe_min=tf_min, exit_contract=exc.get(sl),
        risk_bps_median=q(bps,50), risk_bps_p10=q(bps,10), risk_bps_p90=q(bps,90),
        risk_bps_mean=float(np.mean(bps)) if bps else None,
        target_mult_median=q(tgt,50), target_mult_mean=float(np.mean(tgt)) if tgt else None,
        hold_h_median=q(hold,50), hold_h_mean=float(np.mean(hold)) if hold else None,
        hold_h_p90=q(hold,90),
        mfe_r_mean=float(np.mean(mfe)) if mfe else None, mae_r_mean=float(np.mean(mae)) if mae else None,
        r_gross_mean=float(np.mean(rg)) if rg else None,
        win_rate=float(np.mean([x>0 for x in rg])) if rg else None,
        n_symbols=len(syms), symbols=sorted(syms)[:8], n_days=len(days),
        trades_per_day=len(rows)/max(len(days),1),
        bars_to_mfe_median=q(b2m,50), mfe_hours_median=q(mfeh,50) if mfeh else None,
        frac_mfe_within_2h=float(np.mean([h<=2.0 for h in mfeh])) if mfeh else None,
        frac_hold_within_2h=float(np.mean([h<=2.0 for h in hold])) if hold else None,
        exit_reasons=reasons,
    )
json.dump(out, open("/tmp/d3/D3_SLEEVE_GEOM.json","w"), indent=1)
print("sleeve | n | tf_min | risk_bps_med | tgt_mult | hold_h_med | mfe_r | mae_r | gross_r | wr | nsym | tr/day | mfe_h_med | %mfe<=2h | %hold<=2h")
for sl in LIVE + [s for s in sorted(out) if s not in LIVE]:
    r = out.get(sl)
    if not r: continue
    f=lambda x,n=2: ("%."+str(n)+"f")%x if x is not None else "-"
    print(f"{sl[:34]:34s} {r['n']:5d} {str(r['timeframe_min']):>5s} {f(r['risk_bps_median'],1):>8s} {f(r['target_mult_median']):>6s} {f(r['hold_h_median'],1):>8s} {f(r['mfe_r_mean']):>6s} {f(r['mae_r_mean']):>6s} {f(r['r_gross_mean'],4):>8s} {f(r['win_rate'],3):>6s} {r['n_symbols']:4d} {f(r['trades_per_day'],3):>7s} {f(r['mfe_hours_median'],1):>7s} {f(r['frac_mfe_within_2h'],3):>7s} {f(r['frac_hold_within_2h'],3):>7s}")
