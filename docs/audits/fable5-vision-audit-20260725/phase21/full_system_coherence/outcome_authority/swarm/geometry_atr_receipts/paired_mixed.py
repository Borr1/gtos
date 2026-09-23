import sys; from pathlib import Path
import numpy as np, pandas as pd, json
REPO=Path("/Users/borr/GTOSActive/worktrees/swarm-geom-20260811"); sys.path.insert(0,str(REPO))
from src.research_infra.wave21_forward_shadow.daily_refit import load_frozen_corpus, make_rule_pipeline
from src.research_infra.wave21_forward_shadow.feature_contract import CATEGORICAL_FEATURES, NUMERIC_FEATURES
CORPUS=REPO/"docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority/forward_shadow/FROZEN_TRAINING_CORPUS_V1.npz"
c=load_frozen_corpus(CORPUS); sd=c.columns["stop_distance_atr"]; td=c.columns["target_distance_atr"]
with np.load(CORPUS,allow_pickle=False) as b:
    v=np.asarray([str(t) for t in b["decision_window_vocab"]],dtype=object); wid=v[b["decision_window_codes"]]
day=np.asarray([s.split(":",1)[1][:10] for s in wid]); y=c.y
days=np.unique(day); cut=days[int(len(days)*0.7)]; tr=day<cut; te=day>=cut
_,inv,cnt=np.unique(wid,return_inverse=True,return_counts=True); w=1.0/cnt[inv]
def frame(t):
    d={n:c.columns[n] for n in CATEGORICAL_FEATURES}
    for n in NUMERIC_FEATURES: d[n]= t if n=="target_distance_atr" else c.columns[n]
    return pd.DataFrame(d)
picked={}
for arm,t in (("as_is",td),("repaired",2.0*sd)):
    m=make_rule_pipeline(); f=frame(t); m.fit(f[tr],y[tr],ridge__sample_weight=w[tr]); p=m.predict(f)
    o=np.lexsort((-p[te],wid[te])); ws=wid[te][o]; first=np.ones(len(ws),bool); first[1:]=ws[1:]!=ws[:-1]
    idx=np.flatnonzero(te)[o][first]; picked[arm]=(ws[first],idx,y[idx])
assert (picked["as_is"][0]==picked["repaired"][0]).all()
a,b_=picked["as_is"][2],picked["repaired"][2]; d=b_-a; n=len(d)
rng=np.random.default_rng(20260811); B=10000
bs=np.array([d[rng.integers(0,n,n)].mean() for _ in range(B)])
lo,hi=np.percentile(bs,[2.5,97.5])
diff_windows=int((picked["as_is"][1]!=picked["repaired"][1]).sum())
print(json.dumps({"n_windows":n,"selections_differing":diff_windows,
 "as_is_mean_net_r":float(a.mean()),"repaired_mean_net_r":float(b_.mean()),
 "paired_delta_mean":float(d.mean()),"paired_delta_ci95":[float(lo),float(hi)],
 "delta_over_ci_halfwidth":float(abs(d.mean())/((hi-lo)/2))},indent=2))
