"""Claim 2: the pool scan's null (vectorised)."""
import numpy as np, json, math
rng=np.random.default_rng(20260812)
d=np.load("/private/tmp/laneG-walk/pool_table.npz", allow_pickle=True)
MONTHS=["feb","apr","may","jun","jul"]
status=d["status"].astype(str); net=d["net"]
sel=np.char.startswith(status,"RESOLVED") & np.isfinite(net)
print("rows total",len(net),"resolved-with-net",int(sel.sum()))
y=net[sel]; m2i={m:i for i,m in enumerate(MONTHS)}
mo_idx=np.array([m2i[x] for x in d["month"][sel].astype(str)])
fam=d["family"][sel].astype(str); sym=d["symbol"][sel].astype(str)
ses=d["session"][sel].astype(str); side=d["side"][sel].astype(str)
keys={"family":(fam,300),
      "family_x_symbol":(np.char.add(np.char.add(fam,"|"),sym),30),
      "family_x_session":(np.char.add(np.char.add(fam,"|"),ses),30),
      "family_x_side":(np.char.add(np.char.add(fam,"|"),side),100),
      "symbol":(sym,200)}

def tab(codes, moi, nC):
    c=np.zeros((nC,5)); t=np.zeros((nC,5))
    np.add.at(c,(codes,moi),1.0); np.add.at(t,(codes,moi),y)
    sz=(c.min(axis=1)>=0)  # caller filters
    return c,t

def counts(codes,moi,nC,minn):
    c=np.zeros((nC,5)); t=np.zeros((nC,5))
    np.add.at(c,(codes,moi),1.0); np.add.at(t,(codes,moi),y)
    sz=c.min(axis=1)>=minn
    mm=np.divide(t,c,out=np.zeros_like(t),where=c>0)
    return int(((mm>0).all(axis=1)&sz).sum()), int(((mm<0).all(axis=1)&sz).sum()), sz, mm, c

B=500
report={}; tot_sized=tot_surv=0; tot_coin=0.0; agg={}
print(f"\n{'scan':20s} {'cells':>6s} {'surv+':>6s} {'all5-':>6s} {'coinE':>7s} | "
      f"{'N2 E[+]':>8s} {'N2 p95':>7s} {'N2 E[-]':>8s} | {'N3 E[+]':>8s} {'N3 p95':>7s}")
for name,(labels,minn) in keys.items():
    uniq,codes=np.unique(labels,return_inverse=True); nC=len(uniq)
    pos,neg,sz,mm,c=counts(codes,mo_idx,nC,minn)
    tot_sized+=int(sz.sum()); tot_surv+=pos; tot_coin+=sz.sum()*0.5**5
    ordm=np.argsort(mo_idx,kind="stable"); ordc=np.argsort(codes,kind="stable")
    n2=np.empty(B,int); n2n=np.empty(B,int); n3=np.empty(B,int)
    for b in range(B):
        rnd=rng.random(len(y))
        perm=np.lexsort((rnd,mo_idx));  lc=np.empty_like(codes);  lc[perm]=codes[ordm]
        n2[b],n2n[b],_,_,_=counts(lc,mo_idx,nC,minn)
        perm=np.lexsort((rnd,codes));   mi=np.empty_like(mo_idx); mi[perm]=mo_idx[ordc]
        n3[b],_,_,_,_=counts(codes,mi,nC,minn)
    print(f"{name:20s} {int(sz.sum()):6d} {pos:6d} {neg:6d} {sz.sum()*0.5**5:7.2f} | "
          f"{n2.mean():8.2f} {np.percentile(n2,95):7.0f} {n2n.mean():8.2f} | {n3.mean():8.2f} {np.percentile(n3,95):7.0f}")
    report[name]={"cells_meeting_size":int(sz.sum()),"survivors_all5_positive":pos,"cells_all5_negative":neg,
        "coinflip_E":float(sz.sum()*0.5**5),"N2_cell_label_perm_E_pos":float(n2.mean()),
        "N2_p95":float(np.percentile(n2,95)),"N2_E_all5_negative":float(n2n.mean()),
        "N3_month_perm_E_pos":float(n3.mean()),"N3_p95":float(np.percentile(n3,95)),
        "survivor_names":[str(u) for u,p in zip(uniq,(mm>0).all(axis=1)&sz) if p]}
    agg[name]=(n2.mean(),n3.mean(),n2n.mean(),neg)
tN2=sum(v[0] for v in agg.values()); tN3=sum(v[1] for v in agg.values())
tN2n=sum(v[2] for v in agg.values()); obsneg=sum(v[3] for v in agg.values())
print(f"\nTOTAL cells {tot_sized}; observed all-5-POSITIVE {tot_surv}; coin-flip E {tot_coin:.2f}; "
      f"N2 E {tN2:.2f}; N3 E {tN3:.2f}")
print(f"TOTAL observed all-5-NEGATIVE {obsneg}; N2 E {tN2n:.2f}")
report["_TOTAL"]={"cells":tot_sized,"observed_all5_positive":tot_surv,"coinflip_E":tot_coin,"N2_E":tN2,
                  "N3_E":tN3,"observed_all5_negative":obsneg,"N2_E_all5_negative":tN2n}
json.dump(report,open("/tmp/laneG/pool_null.json","w"),indent=1)
