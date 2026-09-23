import sys, collections, statistics
sys.path.insert(0,"docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
import w0_ws
rows=w0_ws.load()
MINE=("liquidity_sweep_reclaim","structural_distance_extreme")
for fam in MINE+("__POOL__",):
    sub=rows if fam=="__POOL__" else [r for r in rows if r['origin_family']==fam]
    n=len(sub)
    print("="*72); print(fam, "n=",n)
    for col in ('selector_action','effective_selector_action','effective_selector_reason','scheduler_selection_disposition','candidate_lifecycle_action','final_blocker_class','miss_reason','effective_order_type','fill_realism_class','entry_touched','fill_realism_executable','entry_fill_executable','limit_marketable_at_decision','which_came_first','fill_honest_which_came_first','outcome_band'):
        c=collections.Counter(r.get(col) for r in sub)
        top=", ".join(f"{k}={v} ({100*v/n:.1f}%)" for k,v in c.most_common(6))
        print(f"  {col:34s} {top}")
    dup=sum(1 for r in sub if r.get('setup_dup_count',1) and float(r.get('setup_dup_count') or 1)>1)
    print(f"  duplicate-setup rows: {dup} ({100*dup/n:.2f}%)   first_emission={sum(1 for r in sub if r.get('is_first_emission'))}")
