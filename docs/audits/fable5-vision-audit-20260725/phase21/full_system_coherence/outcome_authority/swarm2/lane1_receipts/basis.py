import json, os
B="/Users/borr/GTOSActive/worktrees/three-sleeve-restatement-20260811/docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
F={'feb':'FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json',
   'aprmay':'APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json',
   'junjul':'JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json'}
print("=== The 'discipline beats naive mixed' series, on BOTH bases ===")
print(f"{'window':9}{'disc_actual':>12}{'mix_actual':>12}{'D_ACTUAL':>10}{'disc_worst':>12}{'mix_worst':>12}{'D_WORST':>10}"
      f"{'disc_cens':>10}{'mix_cens':>9}{'mix_sel':>8}{'cens%':>7}")
out={}
for k,f in F.items():
    d=json.load(open(os.path.join(B,f)))['pooled']
    a=d['market_top_abstain']; m=d['mixed']
    da=a['actual_net_r']-m['actual_net_r']; dw=a['worst_case_net_r']-m['worst_case_net_r']
    out[k]=dict(actual=da,worst=dw,disc_cens=a['censored'],mix_cens=m['censored'],
                mix_sel=m['selected'],mix_actual=m['actual_net_r'],mix_worst=m['worst_case_net_r'],
                disc_actual=a['actual_net_r'],disc_worst=a['worst_case_net_r'],disc_sel=a['selected'])
    print(f"{k:9}{a['actual_net_r']:+12.3f}{m['actual_net_r']:+12.3f}{da:+10.3f}"
          f"{a['worst_case_net_r']:+12.3f}{m['worst_case_net_r']:+12.3f}{dw:+10.3f}"
          f"{a['censored']:10d}{m['censored']:9d}{m['selected']:8d}{100*m['censored']/m['selected']:6.1f}%")
print("\n  PUBLISHED SERIES (CLAUDE.md / read results): +18.9 (feb) / +6.6 (aprmay) / +28.96 (junjul)")
print(f"  matches ACTUAL basis for feb ({out['feb']['actual']:+.2f}) and aprmay ({out['aprmay']['actual']:+.2f});")
print(f"  matches WORST  basis for junjul ({out['junjul']['worst']:+.2f}), NOT its actual ({out['junjul']['actual']:+.2f}).")
print(f"\n  CONSISTENT ACTUAL-basis series: {out['feb']['actual']:+.2f} -> {out['aprmay']['actual']:+.2f} -> {out['junjul']['actual']:+.2f}   (monotone decay)")
print(f"  CONSISTENT WORST -basis series: {out['feb']['worst']:+.2f} -> {out['aprmay']['worst']:+.2f} -> {out['junjul']['worst']:+.2f}")
print("\n=== how much of each WORST case is the -1R censored fiat charge? ===")
for k,v in out.items():
    dc=v['disc_worst']-v['disc_actual']; mc=v['mix_worst']-v['mix_actual']
    print(f"  {k:8} discipline: {dc:+8.3f} R over {v['disc_cens']:2d} censors ({100*abs(dc)/max(abs(v['disc_worst']),1e-9):5.1f}% of its worst case)"
          f" | mixed: {mc:+9.3f} R over {v['mix_cens']:2d} censors ({100*abs(mc)/max(abs(v['mix_worst']),1e-9):5.1f}% of its worst case)")
print("\n=== JunJul primary gate, censored repriced at fair value (-E[cost_r] = -0.263) ===")
d=json.load(open(os.path.join(B,F['junjul'])))['pooled']['market_top_abstain']
for fv,lab in [(-1.02,'as booked (-1.0 - deductible)'),(-0.263,'fair value -E[cost_r]'),(0.0,'excluded')]:
    w=d['actual_net_r']+d['censored']*fv
    print(f"  {lab:32s} pooled = {w:+8.3f}   gate(> -2R) = {'PASS' if w>-2 else 'FAIL'}")
json.dump(out,open('lane1_receipts_basis.json','w'),indent=2)
