#!/usr/bin/env python3
"""ATTRITION RECOVERY target 1 — FB `current_ob_retest` 1.5D/0.25D, exact control + controls.

Reproduces the published cell byte-for-byte (tick override included), then runs the
controls FB never ran. Read-only; writes /private/tmp/FB_REWALK_V2.json.
"""
import gzip, json, datetime as dt
from pathlib import Path
import numpy as np

REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
POOL = REPO/"docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
SIDE = REPO/"docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
TICK = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/"
            "cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/ticks/202601")
TOL, HZ = 1e-9, 120
TD, SD = 1.5, 0.25
EPOCH = dt.datetime(1970,1,1,tzinfo=dt.timezone.utc)
def parse(s): return dt.datetime.fromisoformat(str(s).replace("Z","+00:00"))
def eus(d): return int((d-EPOCH).total_seconds()*1_000_000)

pool=[json.loads(l) for l in gzip.open(POOL,'rt')]
N=len(pool)
obset={i for i,r in enumerate(pool) if r.get('origin_family')=='current_ob_retest'}
dates=sorted({parse(r["decision_time_utc"]).date().isoformat() for r in pool})
TRAIN,HOLD=set(dates[:13]),set(dates[13:21])

# --- pass 1: sidecar in pool order (walker's contract), keep OB rows only
rec={}
i=-1
for line in gzip.open(SIDE,'rt'):
    if not line.strip(): continue
    i+=1
    if i not in obset: continue
    r=json.loads(line); p=pool[i]
    assert str(r["candidate_id"])==str(p["candidate_id"]), i
    obs=r["ordered_path_observations"]
    rec[i]=dict(
        hi=np.fromiter((float(o["high"]) for o in obs),np.float64),
        lo=np.fromiter((float(o["low"]) for o in obs),np.float64),
        op=float(obs[0]["open"]), close=float(obs[-1]["close"]),
        entry=float(p["entry_price"]), d=abs(float(p["entry_price"])-float(p["stop_loss"])),
        side=str(p["side"]).upper(), cost=float(p["cost_r"]), spread=float(p.get("spread_r") or 0.0),
        day=parse(p["decision_time_utc"]).date().isoformat(), sym=str(p["symbol"]),
        dec=parse(p["decision_time_utc"]), mode="M1_CONSERVATIVE", bid=None, ask=None)
assert i+1==N, (i+1,N)
print("OB rows walked:",len(rec))

# --- pass 2: tick override for the four tick symbols
for sym in sorted(["EURUSD","USDJPY","XAGUSD","XAUUSD"]):
    idx=[k for k,v in rec.items() if v["sym"]==sym]
    if not idx: continue
    t=[];b=[];a=[]
    with (TICK/sym/"microstructure_ticks.jsonl").open() as fh:
        for line in fh:
            if not line.strip(): continue
            r=json.loads(line); t.append(int(r["time_msc"])*1000); b.append(float(r["bid"])); a.append(float(r["ask"]))
    t=np.asarray(t,np.int64); b=np.asarray(b); a=np.asarray(a)
    ov=0
    for k in idx:
        v=rec[k]; s=int(np.searchsorted(t,eus(v["dec"]),side="right"))
        e=int(np.searchsorted(t,eus(v["dec"]+dt.timedelta(minutes=HZ)),side="right"))
        if s>=e: continue
        v["bid"]=b[s:e]; v["ask"]=a[s:e]; v["mode"]="ORDERED_TICK"; ov+=1
    print(f"  {sym}: {len(idx)} OB rows, {ov} tick-overridden")

keys=sorted(rec)
days=np.array([rec[k]["day"] for k in keys])
tr=np.array([d in TRAIN for d in days]); ho=np.array([d in HOLD for d in days])
cost4=np.array([rec[k]["cost"] for k in keys])/SD

def series(v, side, spread_px):
    """(fav, adv, terminal) in D units for `side`, charging `spread_px` of quote crossing.

    Tick rows already carry both sides of the book (LONG exits bid, SHORT exits ask), so the
    caller passes spread_px = 0.0 for them; only the M1 branch, which resolves both barriers
    against one BID series, needs the synthetic crossing.
    """
    if v["mode"] == "ORDERED_TICK":
        bid, ask, e, d = v["bid"], v["ask"], v["entry"], v["d"]
        sg = (bid - e) / d if side == "LONG" else (e - ask) / d
        return np.maximum.accumulate(sg), np.maximum.accumulate(-sg), float(sg[-1])
    hi, lo, e, d, c = v["hi"], v["lo"], v["entry"], v["d"], v["close"]
    if side == "LONG":
        # entry at ask = e + s ; exits on the bid archive
        fav = np.maximum.accumulate((hi - (e + spread_px)) / d)
        adv = np.maximum.accumulate(((e + spread_px) - lo) / d)
        term = (c - (e + spread_px)) / d
    else:
        # entry at bid = e ; exits on the ask = bid + s
        fav = np.maximum.accumulate((e - (lo + spread_px)) / d)
        adv = np.maximum.accumulate(((hi + spread_px) - e) / d)
        term = (e - (c + spread_px)) / d
    return fav, adv, term


def fillstart(v, side):
    """index of the first observation at which the resting LIMIT at `entry` is touched."""
    if v["mode"]=="ORDERED_TICK":
        px = v["ask"] if side=="LONG" else v["bid"]
        w=np.flatnonzero(px<=v["entry"]+TOL) if side=="LONG" else np.flatnonzero(px>=v["entry"]-TOL)
    else:
        w=np.flatnonzero(v["lo"]<=v["entry"]+TOL) if side=="LONG" else np.flatnonzero(v["hi"]>=v["entry"]-TOL)
    return int(w[0]) if len(w) else None

def walk(flip=False, fillgate=False, spread=False):
    g=np.empty(len(keys)); o={"TARGET":0,"STOP":0,"HORIZON":0,"AMBIG":0}
    t0=0; unfilled=0
    for j,k in enumerate(keys):
        v=rec[k]; side=v["side"]
        if flip: side="SHORT" if side=="LONG" else "LONG"
        sp = v["spread"]*v["d"] if (spread and v["mode"]!="ORDERED_TICK") else 0.0
        fav,adv,term=series(v,side,sp)
        st=0
        if fillgate:
            f=fillstart(v,side)
            if f is None: unfilled+=1; g[j]=0.0; continue
            st = f
            if v["mode"] == "ORDERED_TICK":
                vv = dict(v, bid=v["bid"][st:], ask=v["ask"][st:])
            else:
                vv = dict(v, hi=v["hi"][st:], lo=v["lo"][st:])
            fav, adv, term = series(vv, side, sp)
        n=len(fav)
        if not fillgate and fav[0]>=TD-TOL: t0+=1
        ti=int(np.searchsorted(fav,TD-TOL,side="left")); si=int(np.searchsorted(adv,SD-TOL,side="left"))
        if ti>=n and si>=n: g[j]=term/SD; o["HORIZON"]+=1
        elif ti<si: g[j]=TD/SD; o["TARGET"]+=1
        elif si<ti: g[j]=-1.0; o["STOP"]+=1
        else: g[j]=-1.0; o["AMBIG"]+=1
    o["target_at_first_observation"]=t0; o["limit_never_touched"]=unfilled
    return g, g-cost4, o

def boot(net):
    uniq=sorted(set(days.tolist())); rng=np.random.default_rng(20260812)
    byday={u:net[days==u] for u in uniq}; out=[]
    for _ in range(5000):
        pick=rng.choice(len(uniq),len(uniq),replace=True)
        out.append(np.concatenate([byday[uniq[i]] for i in pick]).mean())
    out=np.sort(np.asarray(out))
    return [float(out[124]),float(out[4875])], float((out<=0).mean())

res={}
for name,kw in [("CONTROL",{}),("MIRROR",dict(flip=True)),
                ("FILL_GATED",dict(fillgate=True)),("FILL_GATED_MIRROR",dict(fillgate=True,flip=True)),
                ("SPREAD_CORRECTED",dict(spread=True)),
                ("FILL_GATED_SPREAD_CORRECTED",dict(fillgate=True,spread=True))]:
    g,net,o=walk(**kw); ci,p=boot(net)
    res[name]=dict(n=len(g),FULL=dict(gross=float(g.mean()),net=float(net.mean())),
        TRAIN=dict(n=int(tr.sum()),gross=float(g[tr].mean()),net=float(net[tr].mean())),
        HOLDOUT=dict(n=int(ho.sum()),gross=float(g[ho].mean()),net=float(net[ho].mean())),
        outcomes=o, net_day_block_ci95=ci, net_day_block_p_le_0=p,
        net_se_iid=float(net.std(ddof=1)/np.sqrt(len(net))))
    print(f"{name:30s} gross {g.mean():+9.6f} net {net.mean():+9.6f} CI95 [{ci[0]:+.4f},{ci[1]:+.4f}] p(<=0) {p:.4f} {o}")

# displacement diagnostics on the CONTROL arm
disp=[]; fav0=[]; adv0=[]
for k in keys:
    v=rec[k]; fav,adv,_=series(v,v["side"],0.0)
    fav0.append(float(fav[0])); adv0.append(float(adv[0]))
    e=v["entry"]; o0=v["op"] if v["mode"]!="ORDERED_TICK" else float(v["bid"][0])
    disp.append(((o0-e)/v["d"]) * (1 if v["side"]=="LONG" else -1))
disp=np.asarray(disp); fav0=np.asarray(fav0); adv0=np.asarray(adv0)
res["_diagnostics"]=dict(
  signed_displacement_at_decision_in_D=dict(mean=float(disp.mean()),median=float(np.median(disp)),
     p10=float(np.percentile(disp,10)),p90=float(np.percentile(disp,90)),
     frac_already_favourable=float((disp>0).mean())),
  first_observation_already_past_target_1p5D=int((fav0>=TD-TOL).sum()),
  first_observation_already_past_stop_0p25D=int((adv0>=SD-TOL).sum()),
  n=len(keys))
res["_meta"]=dict(pool=str(POOL),sidecar=str(SIDE),n_rows=len(keys),target_d=TD,stop_d=SD,
  mode_counts={m:sum(1 for k in keys if rec[k]["mode"]==m) for m in ("ORDERED_TICK","M1_CONSERVATIVE")},
  published=dict(FULL_gross=2.862376572451229,FULL_net=1.6467194254150541,
                 TRAIN_net=1.6308229668744396,HOLDOUT_net=1.6701968198216184,
                 outcomes=dict(TARGET=707,STOP=549,HORIZON=84)),
  mean_cost_r_original_R=float(np.mean([rec[k]["cost"] for k in keys])),
  mean_spread_r_original_R=float(np.mean([rec[k]["spread"] for k in keys])))
print(json.dumps(res["_diagnostics"],indent=1))
json.dump(res,open("/private/tmp/FB_REWALK_V2.json","w"),indent=1)
