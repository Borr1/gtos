import numpy as np, json
WINS=["202510","202511","202512","202601","202602","202603","202604","202605"]
CON=["EST","BC","REFUSE","MKT","SPRSYM","SPRMT5","TIETGT","MIRROR"]
acc={}
for w in WINS:
    z=np.load("/tmp/p3/P315_%s.npz"%w, allow_pickle=True)
    for c in CON:
        acc.setdefault("f_"+c,[]).append(z["f_"+c]); acc.setdefault("r_"+c,[]).append(z["r_"+c])
    acc.setdefault("cost",[]).append(z["cost_r"]); acc.setdefault("mkt",[]).append(z["mkt_r0"])
A={k:np.concatenate(v) for k,v in acc.items()}
N=len(A["cost"]); print("1.5R target — pooled rows",N)
print("%-8s %8s %11s %11s %11s"%("contract","fill","gross/opp","gross/fill","net/fill"))
out={}
for c in CON:
    f=A["f_"+c]>0; r=A["r_"+c]; net=r-A["cost"]*f
    out[c]={"fill":float(f.mean()),"gross_per_opp":float(r.mean()),
            "gross_per_fill":float(r[f].mean()),"net_per_fill":float(net[f].mean())}
    print("%-8s %8.4f %+11.5f %+11.5f %+11.5f"%(c,f.mean(),r.mean(),r[f].mean(),net[f].mean()))
json.dump(out,open("/tmp/p3/P3_TGT15.json","w"),indent=1)
