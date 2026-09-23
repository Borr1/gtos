"""d3 B — THE CONTRACT TRANSPLANT.

Re-express the broad-family origin families under LIVE-SLEEVE-SHAPED contracts and
measure.  Three axes, priced on the SAME rows, with a matched PLACEBO-SIDE arm on every
cell (f2's standard: an exit/geometry change is worth a great deal to a coin flip too, so
a cell's level is uninterpretable without its placebo).

  stop width  native | 25 | 50 | 100 | 200 | 400 bps    (live sleeves sit at 44-436 bps;
                                                         the broad family's native median
                                                         is 9.28 bps -- f1)
  horizon     2h | 8h | 24h | 72h | 160h | 320h          (live sleeves: 320 h time stop)
  target      2R | 3R | 4R | 5R                          (live sleeves: 3R / 4R / 5R)

Toll is the h1 four-term broker-true basis, re-charged per cell: spread + commission +
slippage at the fill, plus SWAP on every broker midnight the cell's own realised hold
crosses -- so a longer horizon pays for itself in carry, exactly as the live sleeves do.
"""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
import numpy as np

sys.path.insert(0,"/tmp/d3")
RCPT = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
            "docs/audits/fable5-vision-audit-20260725/phase19/receipts")
sys.path.insert(0,str(RCPT/"pbg"))
sys.path.insert(0,str(RCPT.parents[4]))
import d3_tape as D
import pbg_econ as E

STOP_BPS   = [None, 25.0, 50.0, 100.0, 200.0, 400.0]
HORIZ_BARS = [8, 32, 96, 288, 640, 1280]        # M15 bars -> 2,8,24,72,160,320 hours
TARGETS    = [1.5, 2.0, 3.0, 4.0, 5.0]
MAXH       = 1280
SEED       = 20260806

# ---------------------------------------------------------------- swap night table
def build_night_cum():
    d0 = date(2025,5,1); d1 = date(2026,8,1)
    dates=[]; w=[]
    d=d0
    while d<=d1:
        dates.append(d); w.append(3.0 if d.weekday()==3 else 1.0); d+=timedelta(days=1)
    cum=np.cumsum(w)
    idx={dd:i for i,dd in enumerate(dates)}
    return idx, cum
NIGHT_IDX, NIGHT_CUM = build_night_cum()

def nights_between(bd0, minutes):
    """Vectorised night count: midnights in (w0, w0+minutes], triple on Thursday."""
    n=len(bd0)
    out=np.zeros(n)
    for a in range(n):
        w1 = bd0[a] + timedelta(minutes=float(minutes[a]))
        i0 = NIGHT_IDX[bd0[a].date()]; i1 = NIGHT_IDX[w1.date()]
        out[a] = NIGHT_CUM[i1]-NIGHT_CUM[i0]
    return out

# ---------------------------------------------------------------- walker
def first_true_idx(mask):
    any_=mask.any(axis=1); first=np.argmax(mask,axis=1)
    return np.where(any_, first, 10**9)

def cell_walk(rc, rh, rl, target_r, horizons):
    """Return {H: (r, exit_bar, code)} for every horizon, one first-touch pass."""
    is_ = first_true_idx(np.nan_to_num(rl, nan=np.inf) <= -1.0)
    it  = first_true_idx(np.nan_to_num(rh, nan=-np.inf) >= target_r)
    valid = ~np.isnan(rc)
    n,H = rc.shape
    ar = np.arange(n)
    out={}
    for Hh in horizons:
        v = valid[:,:Hh]
        has = v.any(axis=1)
        lastidx = Hh-1-np.argmax(v[:,::-1],axis=1)
        lastidx = np.clip(lastidx,0,Hh-1)
        lastr = rc[ar,lastidx]
        r = np.where(has,lastr,np.nan); code=np.where(has,2,3); xb=np.where(has,lastidx,0)
        st = is_<Hh; tg = it<Hh
        tw = tg & (~st | (it<is_))
        sw = st & (~tg | (is_<=it))
        r = np.where(tw, target_r, r); code=np.where(tw,1,code); xb=np.where(tw,it,xb)
        r = np.where(sw, -1.0, r);     code=np.where(sw,0,code); xb=np.where(sw,is_,xb)
        out[Hh]=(r,xb.astype(np.int64),code)
    return out

def be_runner_walk(rc, rh, rl, arm_r, final_r, horizons, partial_frac=0.5):
    """energy_agri's shape: take `partial_frac` off at +arm_r and move the stop to
    breakeven; the runner goes to +final_r or the time stop.  Arming is shifted one bar
    so no intrabar credit is taken (AA/AD convention)."""
    n,H = rc.shape; ar=np.arange(n)
    hit = np.nan_to_num(rh,nan=-np.inf) >= arm_r
    armed = np.zeros((n,H),dtype=bool)
    armed[:,1:] = np.maximum.accumulate(hit,axis=1)[:,:-1]
    level = np.where(armed,0.0,-1.0)
    stopped = np.nan_to_num(rl,nan=np.inf) <= level
    is_ = first_true_idx(stopped)
    ia  = first_true_idx(hit)
    it  = first_true_idx(np.nan_to_num(rh,nan=-np.inf) >= final_r)
    valid=~np.isnan(rc)
    out={}
    for Hh in horizons:
        v=valid[:,:Hh]; has=v.any(axis=1)
        lastidx=np.clip(Hh-1-np.argmax(v[:,::-1],axis=1),0,Hh-1)
        lastr=rc[ar,lastidx]
        armed_in = (ia<Hh) & (ia<is_)
        st = is_<Hh; tg = it<Hh
        # runner leg outcome
        run = np.where(has,lastr,np.nan); xb=np.where(has,lastidx,0)
        tw = tg & (~st | (it<is_)); sw = st & (~tg | (is_<=it))
        run=np.where(tw,final_r,run); xb=np.where(tw,it,xb)
        stop_lvl = np.where(ia<is_, 0.0, -1.0)
        run=np.where(sw,stop_lvl,run); xb=np.where(sw,is_,xb)
        r = np.where(armed_in, partial_frac*arm_r + (1-partial_frac)*run, run)
        r = np.where(has, r, np.nan)
        out[Hh]=(r,xb.astype(np.int64),np.where(tw,1,np.where(sw,0,2)))
    return out

# ---------------------------------------------------------------- frames
def build_frames(tape, rows, chunk_ix, extra=MAXH+2):
    """PRINTED-bar frames.  Column j is the j-th printed M15 bar stamped at or after the
    decision instant, which is the unit the live engine's time stop counts."""
    n=len(chunk_ix)
    W_h=np.full((n,extra),np.nan); W_l=np.full((n,extra),np.nan); W_c=np.full((n,extra),np.nan)
    W_t=np.zeros((n,extra),dtype=np.int64)
    t_dec=np.zeros(n,dtype=np.int64)
    by=defaultdict(list); pos=np.zeros(n,dtype=np.int64)
    for a,ri in enumerate(chunk_ix):
        r=rows[ri]
        pos[a]=tape.pos(r["s"], r["t"]); t_dec[a]=tape.minutes(r["t"])
        by[r["s"]].append(a)
    ar=np.arange(extra)
    for sym,aa in by.items():
        h,l,c,tm = tape.h[sym],tape.l[sym],tape.c[sym],tape.tmin[sym]
        m=len(c)
        aa=np.asarray(aa)
        cols=pos[aa][:,None]+ar[None,:]
        good=(cols>=0)&(cols<m); cl=np.clip(cols,0,max(m-1,0))
        if m==0: continue
        W_h[aa]=np.where(good,h[cl],np.nan); W_l[aa]=np.where(good,l[cl],np.nan)
        W_c[aa]=np.where(good,c[cl],np.nan); W_t[aa]=np.where(good,tm[cl],-1)
    return pos,W_h,W_l,W_c,W_t,t_dec

# ---------------------------------------------------------------- cost helpers
class Cost:
    def __init__(self):
        self.cm = E.CostModel()
    def per_night_px(self, sym, long, price):
        rec = self.cm.bt.get(self.cm.bmap.get(sym,sym))
        if rec is None: return 0.0
        spec = rec.get("spec") or {}
        raw = spec.get("swap_long" if long else "swap_short"); mode=spec.get("swap_mode")
        if raw is None or mode is None or float(raw)>=0: return 0.0
        adv=abs(float(raw))
        if int(mode)==1:
            pt=spec.get("point"); return adv*float(pt) if pt else 0.0
        if int(mode) in (5,6):
            return float(price)*(adv/100.0)/360.0
        return 0.0
    def base_px(self, sym, iso, price):
        h=self.cm.broker_hour(iso)
        sp=self.cm.spread_bps(sym,h)/1e4*price
        cmm=self.cm.comm_px(sym,price)
        sl=self.cm.slip_bps.get(sym,("MODELLED",0.0))[1]/1e4*price
        return sp+cmm+sl, sp, cmm, sl

def load_window(win, indir):
    rows = D.load_close_rows(indir, D.AT_MARKET)
    rows = [r for r in rows if abs(float(r["e"])-float(r["sl"]))>0 and float(r["e"])>0]
    rows.sort(key=lambda r:(r["t"],r["s"],r["f"]))
    return rows

def run_window(win, indir, tape, C, out_path, chunk=6000):
    rows = load_window(win, indir)
    n=len(rows)
    rng = np.random.default_rng(SEED + int(win.replace("-","")))
    # ---- per-row constants
    entry=np.array([float(r["e"]) for r in rows])
    slp  =np.array([float(r["sl"]) for r in rows])
    dnat =np.abs(entry-slp)
    long =np.array([r["d"]=="L" for r in rows])
    plong=rng.random(n)<0.5
    sym  =[r["s"] for r in rows]
    inst =[r["t"] for r in rows]
    day  =np.array([r["t"][:10] for r in rows])
    fam  =np.array([r["f"] for r in rows])
    base=np.zeros(n); spread_px=np.zeros(n); pn_L=np.zeros(n); pn_S=np.zeros(n)
    bd0=[]
    for a in range(n):
        b,sp,cm_,sl_ = C.base_px(sym[a], inst[a], entry[a])
        base[a]=b; spread_px[a]=sp
        pn_L[a]=C.per_night_px(sym[a],True,entry[a]); pn_S[a]=C.per_night_px(sym[a],False,entry[a])
        u=datetime.fromisoformat(inst[a])
        bd0.append(C.cm._to_broker(u, C.cm.server))
    acc = defaultdict(lambda: defaultdict(float))   # cell -> stats
    daily = defaultdict(lambda: defaultdict(float)) # cell -> day -> net sum
    dailyg= defaultdict(lambda: defaultdict(float)) # cell -> day -> gross sum
    dailyn= defaultdict(lambda: defaultdict(int))
    famacc= defaultdict(lambda: defaultdict(float))
    for c0 in range(0,n,chunk):
        ix=list(range(c0,min(c0+chunk,n)))
        pos,W_h,W_l,W_c,W_t,t_dec = build_frames(tape, rows, ix)
        sl_ = np.array(ix)
        e=entry[sl_][:,None]
        for arm,side in (("REAL",long[sl_]),("PLACEBO",plong[sl_])):
            sgn=np.where(side,1.0,-1.0)[:,None]
            pn = np.where(side, pn_L[sl_], pn_S[sl_])
            for sb in STOP_BPS:
                d = dnat[sl_] if sb is None else entry[sl_]*sb/1e4
                dd=d[:,None]
                rc=(W_c-e)/dd*sgn; rh_=(W_h-e)/dd*sgn; rl_=(W_l-e)/dd*sgn
                rhi=np.maximum(rh_,rl_); rlo=np.minimum(rh_,rl_)
                for tr in TARGETS:
                    res=cell_walk(rc,rhi,rlo,tr,HORIZ_BARS)
                    for Hh,(r,xb,code) in res.items():
                        _accum(acc,daily,dailyg,dailyn,famacc,arm,sb,tr,Hh,"fixed",
                               r,xb,code,base[sl_],pn,d,day[sl_],fam[sl_],
                               [bd0[i] for i in ix],W_t,t_dec)
                # energy_agri shape: partial 50% at 2R -> BE, runner 4R
                res=be_runner_walk(rc,rhi,rlo,2.0,4.0,HORIZ_BARS)
                for Hh,(r,xb,code) in res.items():
                    _accum(acc,daily,dailyg,dailyn,famacc,arm,sb,"be2_4",Hh,"be_runner",
                           r,xb,code,base[sl_],pn,d,day[sl_],fam[sl_],
                           [bd0[i] for i in ix],W_t,t_dec)
        del W_h,W_l,W_c,W_t
    out={"window":win,"n_rows":n,"cells":{}}
    for k,v in acc.items():
        days=daily[k]
        out["cells"][k]=dict(v)
        out["cells"][k]["n_days"]=len(days)
        out["cells"][k]["days_net_positive"]=int(sum(1 for d in days if days[d]>0))
        out["cells"][k]["day_net"]={d:days[d] for d in sorted(days)}
        out["cells"][k]["day_gross"]={d:dailyg[k][d] for d in sorted(dailyg[k])}
        out["cells"][k]["day_n"]={d:dailyn[k][d] for d in sorted(dailyn[k])}
    out["families"]={k:dict(v) for k,v in famacc.items()}
    json.dump(out, open(out_path,"w"))
    return out

def _accum(acc,daily,dailyg,dailyn,famacc,arm,sb,tr,Hh,pol,r,xb,code,base,pn,d,day,fam,bd0,W_t,t_dec):
    nrow=len(r); arr=np.arange(nrow)
    tex=W_t[arr,np.clip(xb,0,W_t.shape[1]-1)]
    hold_min=np.where(tex>=0,(tex+15).astype(float)-t_dec.astype(float),np.nan)
    hold_min=np.clip(np.nan_to_num(hold_min,nan=15.0),15.0,None)
    nights=nights_between(bd0,hold_min)
    cost_px = base + pn*nights
    cost_r = cost_px/d
    m=np.isfinite(r)&np.isfinite(cost_r)
    lbl = "native" if sb is None else (sb if isinstance(sb,str) else ("%gbps"%sb))
    key="%s|%s|%s|%d|%s"%(arm, lbl, tr, Hh, pol)
    a=acc[key]
    rr=r[m]; cc=cost_r[m]; net=rr-cc
    a["n"]+=len(rr); a["sum_gross"]+=float(rr.sum()); a["sum_cost"]+=float(cc.sum())
    a["sum_net"]+=float(net.sum()); a["n_win_gross"]+=int((rr>0).sum())
    a["n_win_net"]+=int((net>0).sum())
    a["sum_hold_min"]+=float(hold_min[m].sum()); a["sum_nights"]+=float(nights[m].sum())
    a["n_stop"]+=int((code[m]==0).sum()); a["n_target"]+=int((code[m]==1).sum())
    a["n_horizon"]+=int((code[m]==2).sum())
    a["sum_win_r"]+=float(rr[rr>0].sum()); a["n_pos"]+=int((rr>0).sum())
    a["sum_loss_r"]+=float(rr[rr<=0].sum()); a["n_neg"]+=int((rr<=0).sum())
    dnet=net; dday=day[m]
    for dd_,x,gx in zip(dday,dnet,rr):
        daily[key][dd_]+=float(x); dailyg[key][dd_]+=float(gx); dailyn[key][dd_]+=1
    if Hh in (8,1280):
        for f_ in np.unique(fam[m]):
            fm=fam[m]==f_
            fk=key+"||"+str(f_)
            famacc[fk]["n"]+=int(fm.sum()); famacc[fk]["sum_gross"]+=float(rr[fm].sum())
            famacc[fk]["sum_cost"]+=float(cc[fm].sum()); famacc[fk]["sum_net"]+=float(net[fm].sum())

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--window",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    syms=sorted({p.name[:-len("_M15.csv")] for p in D.M15_DIR.glob("*_M15.csv")})
    print("loading tape...",flush=True)
    tape=D.M15Tape(syms)
    C=Cost()
    print("tape ok; walking",a.window,flush=True)
    o=run_window(a.window, D.WINDOWS[a.window], tape, C, a.out)
    print("done", a.window, o["n_rows"], len(o["cells"]),flush=True)
