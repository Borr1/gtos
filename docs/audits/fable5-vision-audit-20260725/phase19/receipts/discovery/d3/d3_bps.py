"""d3 A2 — THE INVARIANT COMPARISON.  R is a ratio; both the gross and the toll scale with
the stop.  Multiply back into price space (bps of the entry price) and the two systems
become directly comparable regardless of contract."""
import gzip,json
import numpy as np
from pathlib import Path
ROOT=Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
A=ROOT/"docs/audits/fable5-vision-audit-20260725"
est=json.load(gzip.open(A/"phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz","rt"))["trades"]
dos=json.load(open(A/"phase8/receipts/SLEEVE_DOSSIER_V1.json"))["sleeves"]
LIVE=["crypto","energy_agri","sub_xvol_pullback","sub_mid_dn_revert",
      "mx_btcusd_d1_donchian_20_breakout"]
rowsout={}
print("%-34s %5s %10s %10s %11s %11s %8s"%("system","n","stop_bps","gross_R","gross_bps","toll_bps","g/t"))
for sl in LIVE:
    rr=est[sl]
    bps=np.array([r["sl_distance_price"]/abs(r["entry_price"])*1e4 for r in rr
                  if r.get("entry_price") and r.get("sl_distance_price")])
    a=dos[sl]["archive"]; cd=a["cost_decomposition"]
    g=cd["mean_gross_r"]; c=cd["mean_total_cost_r"]
    med=float(np.median(bps))
    # gross in bps: R x stop distance, computed PER TRADE where possible
    per=[]
    for r in rr:
        if r.get("entry_price") and r.get("sl_distance_price") and r.get("r_gross") is not None:
            per.append(r["r_gross"]*r["sl_distance_price"]/abs(r["entry_price"])*1e4)
    gbps=float(np.mean(per)) if per else g*med
    tbps=c*med
    rowsout[sl]=dict(n=len(rr),stop_bps_median=med,gross_r=g,cost_r=c,
                     gross_bps_per_trade=gbps,toll_bps_per_trade=tbps,
                     gross_over_toll=gbps/tbps if tbps else None)
    print("%-34s %5d %10.1f %10.4f %11.2f %11.2f %8.2f"%(sl,len(rr),med,g,gbps,tbps,gbps/tbps))
json.dump(rowsout,open("/tmp/d3/D3_BPS_LIVE.json","w"),indent=1)
