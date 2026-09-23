"""Validation: does the d3 re-walk reproduce the estate's OWN recorded r_gross for the
same trade under the same contract?  If it does not, the reverse transplant is measuring
my walker, not the sleeves."""
import gzip,json,sys
from datetime import datetime
import numpy as np
sys.path.insert(0,"/tmp/d3")
import d3_walk as W, d3_tape as D, d3_tape2 as T2, d3_reverse as R

EXITP={"crypto":(4.0,1280),"energy_agri":(4.0,1280),"sub_xvol_pullback":(3.0,1280),
       "sub_mid_dn_revert":(3.0,1280),"mx_btcusd_d1_donchian_20_breakout":(2.0,7680)}
rows=R.load_rows(); n=len(rows)
syms=sorted({p.name[:-len("_M15.csv")] for p in D.M15_DIR.glob("*_M15.csv")})
tape=T2.CTape(syms)
rr=[dict(s=r["s"],t=r["t"],f=r["sleeve"],d="L" if r["long"] else "S") for r in rows]
pos,W_h,W_l,W_c,W_t,t_dec=W.build_frames(tape,rr,list(range(n)),extra=W.MAXH+2)
entry=np.array([r["e"] for r in rows]); dnat=np.array([r["dnat"] for r in rows])
long=np.array([r["long"] for r in rows])
e=entry[:,None]; dd=dnat[:,None]; sgn=np.where(long,1.0,-1.0)[:,None]
rc=(W_c-e)/dd*sgn; rh=(W_h-e)/dd*sgn; rl=(W_l-e)/dd*sgn
rhi=np.maximum(rh,rl); rlo=np.minimum(rh,rl)
out={}
print("sleeve                              n   walked_gross  estate_gross   corr   mean|diff|  sign_agree  walked_hold_h estate_hold_h")
allw=[];alle=[]
for sl,(tr,ts) in EXITP.items():
    m=np.array([r["sleeve"]==sl for r in rows])
    if m.sum()==0: continue
    res=W.cell_walk(rc[m],rhi[m],rlo[m],tr,[min(ts,W.MAXH)])
    r_,xb,code=res[min(ts,W.MAXH)]
    est=np.array([rows[i]["r_gross"] for i in range(n) if m[i]],dtype=float)
    eh=np.array([rows[i]["hold"] for i in range(n) if m[i]],dtype=float)
    tex=W_t[np.where(m)[0],np.clip(xb,0,W_t.shape[1]-1)]
    hold=(tex+15-t_dec[m])/60.0
    ok=np.isfinite(r_)&np.isfinite(est)
    allw+=list(r_[ok]); alle+=list(est[ok])
    print("%-34s %3d  %12.4f %13.4f %6.3f %11.4f %11.3f %13.1f %13.1f"%(
      sl,int(ok.sum()),r_[ok].mean(),est[ok].mean(),
      float(np.corrcoef(r_[ok],est[ok])[0,1]),float(np.abs(r_[ok]-est[ok]).mean()),
      float((np.sign(r_[ok])==np.sign(est[ok])).mean()),float(np.nanmean(hold[ok])),float(np.nanmean(eh[ok]))))
allw=np.array(allw);alle=np.array(alle)
print("\nPOOLED n=%d  walked %.4f  estate %.4f  corr %.3f  sign agreement %.3f"%(
  len(allw),allw.mean(),alle.mean(),float(np.corrcoef(allw,alle)[0,1]),float((np.sign(allw)==np.sign(alle)).mean())))
json.dump(dict(n=len(allw),walked=float(allw.mean()),estate=float(alle.mean()),
               corr=float(np.corrcoef(allw,alle)[0,1]),
               sign_agree=float((np.sign(allw)==np.sign(alle)).mean())),
          open("/tmp/d3/D3_REV_VALIDATE.json","w"),indent=1)
