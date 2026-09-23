import sys, collections, statistics
sys.path.insert(0,"docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
import w0_ws
rows=w0_ws.load()
def q(v,p):
    v=sorted(v)
    if not v: return float('nan')
    i=(len(v)-1)*p; lo=int(i); hi=min(lo+1,len(v)-1)
    return v[lo] if lo==hi else v[lo]+(v[hi]-v[lo])*(i-lo)
print("path_bars: med %.0f  p90 %.0f  max %.0f"%(q([r['path_bars'] for r in rows],.5),q([r['path_bars'] for r in rows],.9),max(r['path_bars'] for r in rows)))
print("path_minutes: med %.0f p90 %.0f max %.0f"%(q([r['path_minutes'] for r in rows],.5),q([r['path_minutes'] for r in rows],.9),max(r['path_minutes'] for r in rows)))
print()
hdr=f"{'family':34s} {'n':>5s} {'res%':>5s} {'t_res_med':>9s} {'t_res_p75':>9s} {'t_res_p90':>9s} {'t_stop_med':>10s} {'t_tgt_med':>9s} {'t_mfe_med':>9s} {'MFE_med':>8s} {'MFE_p90':>8s} {'MAE_med':>8s}"
print(hdr); print("-"*len(hdr))
FAMS=collections.Counter(r['origin_family'] for r in rows)
out={}
for fam,_ in FAMS.most_common():
    sub=[r for r in rows if r['origin_family']==fam]
    res=[]; ts=[]; tt=[]
    for r in sub:
        w=r.get('which_came_first')
        if w=='stop' and r.get('bars_to_stop') is not None: res.append(r['bars_to_stop']); ts.append(r['bars_to_stop'])
        elif w=='target' and r.get('bars_to_target') is not None: res.append(r['bars_to_target']); tt.append(r['bars_to_target'])
    tmfe=[r['bars_to_mfe'] for r in sub if r.get('bars_to_mfe') is not None]
    mfe=[r['mfe_r'] for r in sub if r.get('mfe_r') is not None]
    mae=[r['mae_r'] for r in sub if r.get('mae_r') is not None]
    print(f"{fam:34s} {len(sub):5d} {100*len(res)/len(sub):5.1f} {q(res,.5):9.0f} {q(res,.75):9.0f} {q(res,.9):9.0f} {q(ts,.5):10.0f} {q(tt,.5):9.0f} {q(tmfe,.5):9.0f} {q(mfe,.5):8.3f} {q(mfe,.9):8.3f} {q(mae,.5):8.3f}")
    out[fam]=(q(res,.5),q(res,.75))
print()
print("(t_* are M1 bars == MINUTES of market time; res% = fraction resolved at stop-or-target inside the path horizon)")
