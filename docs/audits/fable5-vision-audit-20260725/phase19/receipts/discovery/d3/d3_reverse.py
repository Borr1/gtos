"""d3 C — THE REVERSE TRANSPLANT: the live sleeves under the BROAD FAMILY's contract.

If the live sleeves' edge survives a 9.28 bps stop and a 2-hour horizon, then the broad
family's contract is not what is killing it.  If it does not, then 'signal' and 'contract'
are not separable quantities and the honest statement is about a signal AT A HORIZON.

Population: every AQ_ESTATE_TRADES_V2 trade of the four live sleeves + the standing
admission whose entry falls inside the M15 tape window and whose symbol the tape carries.
Each trade is re-walked on the same tape, from its own entry instant, in its own
direction, at a ladder of stop widths and horizons.  PLACEBO-SIDE on every cell.
"""
from __future__ import annotations
import gzip, json, sys, time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
sys.path.insert(0,"/tmp/d3")
import d3_walk as W, d3_tape as D, d3_tape2 as T2

ROOT=Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
EST=ROOT/"docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
LIVE=["crypto","energy_agri","sub_xvol_pullback","sub_mid_dn_revert",
      "mx_btcusd_d1_donchian_20_breakout"]
TAPE_SYMS=set("AUDJPY AUDUSD BTCUSD CHFJPY ETHUSD EURGBP EURJPY EURUSD GBPJPY GBPUSD GER40 "
              "JP225 NAS100 NZDUSD SPX500 UK100 UKOIL_cash US30_cash USDCAD USDCHF USDJPY "
              "USOIL_cash XAGUSD XAUUSD".split())
STOP_BPS=[None,9.28,25.0,50.0,100.0,200.0,400.0]   # 9.28 = the broad family's own median (f1)
HORIZ=[8,32,96,288,640,1280]
TARGETS=[2.0,3.0,4.0]

def load_rows():
    o=json.load(gzip.open(EST,"rt")); T=o["trades"]
    out=[]
    for sl in LIVE:
        for r in T[sl]:
            s=r.get("symbol_canonical") or r.get("symbol")
            eu=r.get("entry_utc")
            if not eu or s not in TAPE_SYMS: continue
            if not ("2025-06-01" <= eu[:10] <= "2026-05-20"): continue
            if not r.get("entry_price") or not r.get("sl_distance_price"): continue
            out.append(dict(sleeve=sl, s=s, t=eu.replace("Z","+00:00"),
                            e=float(r["entry_price"]), dnat=abs(float(r["sl_distance_price"])),
                            long=int(r["direction"])>0, r_gross=r.get("r_gross"),
                            hold=r.get("hold_hours"), mfe=r.get("mfe_r"), mae=r.get("mae_r")))
    return out

def main():
    rows=load_rows(); n=len(rows)
    syms=sorted({p.name[:-len("_M15.csv")] for p in D.M15_DIR.glob("*_M15.csv")})
    tape=T2.CTape(syms); C=W.Cost()
    rng=np.random.default_rng(20260806)
    entry=np.array([r["e"] for r in rows]); dnat=np.array([r["dnat"] for r in rows])
    long=np.array([r["long"] for r in rows]); plong=rng.random(n)<0.5
    sl_names=np.array([r["sleeve"] for r in rows])
    day=np.array([r["t"][:10] for r in rows])
    base=np.zeros(n); pnL=np.zeros(n); pnS=np.zeros(n); bd0=[]
    for a,r in enumerate(rows):
        b,_,_,_=C.base_px(r["s"],r["t"],r["e"]); base[a]=b
        pnL[a]=C.per_night_px(r["s"],True,r["e"]); pnS[a]=C.per_night_px(r["s"],False,r["e"])
        bd0.append(C.cm._to_broker(datetime.fromisoformat(r["t"]), C.cm.server))
    rr=[dict(s=r["s"],t=r["t"],f=r["sleeve"],d="L" if r["long"] else "S") for r in rows]
    pos,W_h,W_l,W_c,W_t,t_dec=W.build_frames(tape,rr,list(range(n)))
    acc=defaultdict(lambda: defaultdict(float)); daily=defaultdict(lambda: defaultdict(float))
    dailyg=defaultdict(lambda: defaultdict(float)); dailyn=defaultdict(lambda: defaultdict(int))
    fam=defaultdict(lambda: defaultdict(float))
    e=entry[:,None]
    for arm,side in (("REAL",long),("PLACEBO",plong)):
        sgn=np.where(side,1.0,-1.0)[:,None]; pn=np.where(side,pnL,pnS)
        for sb in STOP_BPS:
            d = dnat if sb is None else entry*sb/1e4
            dd=d[:,None]
            rc=(W_c-e)/dd*sgn; rh=(W_h-e)/dd*sgn; rl=(W_l-e)/dd*sgn
            rhi=np.maximum(rh,rl); rlo=np.minimum(rh,rl)
            for tr in TARGETS:
                res=W.cell_walk(rc,rhi,rlo,tr,HORIZ)
                for Hh,(r_,xb,code) in res.items():
                    W._accum(acc,daily,dailyg,dailyn,fam,arm,sb,tr,Hh,"fixed",
                             r_,xb,code,base,pn,d,day,sl_names,bd0,W_t,t_dec)
    out={"n":n,"cells":{}}
    for k,v in acc.items():
        out["cells"][k]=dict(v)
    out["families"]={k:dict(v) for k,v in fam.items()}
    out["rows_by_sleeve"]={s:int((sl_names==s).sum()) for s in LIVE}
    # native-geometry sanity: does the re-walk reproduce the estate's own r_gross sign/level?
    json.dump(out,open("/tmp/d3/D3_REVERSE.json","w"))
    print("n",n,out["rows_by_sleeve"])
    def show(sb,tr,Hh):
        kr="REAL|%s|%s|%d|fixed"%("native" if sb is None else "%gbps"%sb,tr,Hh)
        kp=kr.replace("REAL","PLACEBO")
        a=acc[kr]; b=acc[kp]
        if not a["n"]: return
        print("%-8s tgt %.1f H%5d  n %4d  gross %8.4f  placebo %8.4f  SIGNAL %8.4f  cost %7.4f  net %8.4f  hold_h %7.1f  %%stop %.3f %%tgt %.3f"%(
          "native" if sb is None else "%gbps"%sb,tr,Hh,a["n"],a["sum_gross"]/a["n"],b["sum_gross"]/b["n"],
          a["sum_gross"]/a["n"]-b["sum_gross"]/b["n"],a["sum_cost"]/a["n"],a["sum_net"]/a["n"],
          a["sum_hold_min"]/a["n"]/60,a["n_stop"]/a["n"],a["n_target"]/a["n"]))
    print("\nLIVE SLEEVES, re-walked.  Their OWN contract first, then the broad family's.")
    for sb in STOP_BPS:
        for Hh in (8,1280):
            show(sb,2.0,Hh)
    print("\nAt the sleeves' own 3R/4R:")
    for sb in (None,9.28):
        for tr in (3.0,4.0):
            show(sb,tr,1280); show(sb,tr,8)
    # per sleeve at the two extreme contracts
    print("\nPER SLEEVE (n, native-stop 320h 3R vs broad-contract 9.28bps 2h 2R), gross R/trade")
    for s in LIVE:
        k1="REAL|native|3.0|1280|fixed||%s"%s; k2="REAL|9.28bps|2.0|8|fixed||%s"%s
        a=fam.get(k1); b=fam.get(k2)
        if a and a["n"]:
            print("  %-34s n %3d   own-shape %8.4f   broad-shape %8.4f"%(s,int(a["n"]),a["sum_gross"]/a["n"],(b["sum_gross"]/b["n"]) if b and b["n"] else float("nan")))

if __name__=="__main__":
    main()
