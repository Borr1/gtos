import sys, json
from pathlib import Path
import numpy as np, pandas as pd
REPO=Path("/Users/borr/GTOSActive/worktrees/swarm-geom-20260811"); sys.path.insert(0,str(REPO))
from src.research_infra.wave21_forward_shadow.daily_refit import load_frozen_corpus, make_rule_pipeline
from src.research_infra.wave21_forward_shadow.feature_contract import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from sklearn.preprocessing import StandardScaler
CORPUS=REPO/"docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority/forward_shadow/FROZEN_TRAINING_CORPUS_V1.npz"
c=load_frozen_corpus(CORPUS); sd=c.columns["stop_distance_atr"]; td=c.columns["target_distance_atr"]
with np.load(CORPUS,allow_pickle=False) as b:
    v=np.asarray([str(t) for t in b["decision_window_vocab"]],dtype=object); wid=v[b["decision_window_codes"]]
day=np.asarray([s.split(":",1)[1][:10] for s in wid])
homo=np.round(td/sd,9)==1.5
# 1) standardized-column identity claim
for lab,x in (("as_is(1.5x)",td[homo]),("repaired(2.0x)",2.0*sd[homo])):
    z=StandardScaler().fit_transform(x.reshape(-1,1)).ravel()
    zs=StandardScaler().fit_transform(sd[homo].reshape(-1,1)).ravel()
    print(f"{lab}: max|z(target)-z(stop)| = {np.nanmax(np.abs(z-zs)):.3e}")
# 2) do the two arms pick the SAME candidate in each window?
def frame(t):
    d={n:c.columns[n] for n in CATEGORICAL_FEATURES}
    for n in NUMERIC_FEATURES: d[n]= t if n=="target_distance_atr" else c.columns[n]
    return pd.DataFrame(d).iloc[homo.nonzero()[0]].reset_index(drop=True)
y=c.y[homo]; w_ids=wid[homo]; d2=day[homo]
days=np.unique(d2); cut=days[int(len(days)*0.7)]
tr=d2<cut; te=d2>=cut
_,inv,cnt=np.unique(w_ids,return_inverse=True,return_counts=True); w=1.0/cnt[inv]
picks={}
for arm,t in (("as_is",td),("repaired",2.0*sd)):
    m=make_rule_pipeline(); f=frame(t); m.fit(f[tr],y[tr],ridge__sample_weight=w[tr]); p=m.predict(f)
    o=np.lexsort((-p[te],w_ids[te])); ws=w_ids[te][o]
    first=np.ones(len(ws),bool); first[1:]=ws[1:]!=ws[:-1]
    picks[arm]=(ws[first], np.flatnonzero(te)[o][first])
same=int((picks["as_is"][1]==picks["repaired"][1]).sum()); n=len(picks["as_is"][1])
print(f"\nHOMOGENEOUS top-1 selections identical in {same}/{n} windows ({100*same/n:.2f}%)")
