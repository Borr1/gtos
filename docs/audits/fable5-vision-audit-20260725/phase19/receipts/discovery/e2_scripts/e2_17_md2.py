import json,os,statistics as st
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
R=json.load(open(f'{D}/e2_RESULT.json')); MO=['JAN','FEB','MAR','APR','MAY']
o=[];A=o.append
A("\n---\n\n## 3. NEW FINDING E2-N1 — the frozen cost model is a RANKING error, not a scale error\n")
A("This is the most consequential thing this lane found and it is not in the original finding.\n")
A("If the frozen model were simply ~3.4x too large, the cost gate would still rank candidates correctly and")
A("its only defect would be tightness. It does not. Measured on every row of every month:\n")
A("| month | Spearman(frozen_total, real_total) | median row ratio | p10 | p90 | gate disagreement | frozen-only admits | real-only admits | per-SYMBOL ratio spread | per-FAMILY ratio spread |")
A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for m in MO:
    v=R['SCALE_VS_RANK'][m]
    A(f"| {m} | **{v['spearman_frozen_vs_real']:.4f}** | {v['row_ratio_median']:.2f}x | {v['row_ratio_p10']:.2f}x | {v['row_ratio_p90']:.2f}x | **{100*v['disagreement_rate']:.1f}%** | {v['gate_frozen_only']:,} | {v['gate_real_only']:,} | {v['symbol_ratio_spread']:.1f}x | {v['family_ratio_spread']:.2f}x |")
A("\n**Reading.** A pure scale error would give Spearman ~1.0 and a per-row ratio with no dispersion. Instead")
A("the correlation is 0.37-0.60, the p10-to-p90 row ratio spans roughly 1x to 12-16x, and the per-symbol")
A("mean ratio spreads **50x-152x** — the frozen model over-charges some symbols two orders of magnitude more")
A("than others *relative to truth*. So the frozen gate is not just refusing too much; on **34.9%-44.7% of")
A("every month's pool it refuses and admits the wrong rows.**\n")
A("### 3.1 What fixing the gate is worth, and where it fails\n")
A("Frozen-gate book vs real-gate book, both takeable, both scored at real cost:\n")
A("| month | frozen-gate n | frozen-gate net@real | real-gate n | real-gate net@real | delta | trade-count ratio |")
A("|---|---:|---:|---:|---:|---:|---:|")
for m in MO:
    v=R['GATE_FIX_VALUE'][m]
    A(f"| {m} | {v['frozen_gate_book']['n']:,} | {v['frozen_gate_book']['net_real']:.4f} | {v['real_gate_book']['n']:,} | {v['real_gate_book']['net_real']:.4f} | {v['delta_net_real']:+.4f} | {v['n_ratio']:.2f}x |")
d=[R['GATE_FIX_VALUE'][m]['delta_net_real'] for m in MO]; nr=[R['GATE_FIX_VALUE'][m]['n_ratio'] for m in MO]
A(f"| **mean** | | | | | **{st.mean(d):+.4f}** | **{st.mean(nr):.2f}x** |")
A("\n**Fixing the gate is worth about +0.037 R/trade AND roughly doubles the trade count** — but it is **not")
A("uniformly positive: April is -0.0027.** This is the direct, month-resolved version of the estate's")
A("standing result that cost truth widens the funnel ~2.2-2.4x and earns no more; here the widening is")
A("1.70x-2.13x and the earnings change is +0.0132 to +0.0787 with one negative month.\n")
A("### 3.2 Per-symbol frozen/real cost ratio, January (the shape of the mis-ranking)\n")
sr=R['SCALE_VS_RANK']['JAN']['symbol_ratio']
ks=list(sr.items())
A("| cheapest-relative (model closest to truth) | ratio | most over-charged | ratio |\n|---|---:|---|---:|")
for i in range(6):
    A(f"| {ks[i][0]} | {ks[i][1]:.2f}x | {ks[-(i+1)][0]} | {ks[-(i+1)][1]:.2f}x |")
A("\n---\n\n## 4. NEW FINDING E2-N2 — the 12.1x family dispersion travels, and here is its price\n")
A("### 4.1 The dispersion itself\n")
A("| month | cheapest family cost | most expensive | ratio |\n|---|---:|---:|---:|")
for m in MO:
    f=R['MONTHS'][m]['family_real_cost_dispersion']
    A(f"| {m} | {f['min']:.4f} | {f['max']:.4f} | **{f['ratio']:.2f}x** |")
A("\n### 4.2 Family real cost R/trade, takeable, four months side by side\n")
bf=R['BOUNDARY_FAMILY']
A(f"**Mean Spearman across the six month-pairs = {bf['mean_spearman']}** — the ordering is near-invariant.\n")
A("| family | JAN | FEB | APR | MAY | mean |\n|---|---:|---:|---:|---:|---:|")
for k,v in sorted(bf['rows'].items(),key=lambda kv:kv[1]['mean']):
    A(f"| {k} | {v['JAN']:.4f} | {v['FEB']:.4f} | {v['APR']:.4f} | {v['MAY']:.4f} | **{v['mean']:.4f}** |")
A("\n(The four-month table is the one with a directly comparable pool construction. March's own dispersion")
A(f"is {R['MONTHS']['MAR']['family_real_cost_dispersion']['ratio']:.2f}x with the same ordering.)\n")
A("### 4.3 Family net@real — the ordering is also stable\n")
bn=R['BOUNDARY_FAMILY_NET']
A(f"Mean Spearman = {bn['mean_spearman']}.\n")
A("| family | JAN | FEB | APR | MAY | mean |\n|---|---:|---:|---:|---:|---:|")
for k,v in sorted(bn['rows'].items(),key=lambda kv:kv[1]['mean']):
    A(f"| {k} | {v['JAN']:.4f} | {v['FEB']:.4f} | {v['APR']:.4f} | {v['MAY']:.4f} | **{v['mean']:.4f}** |")
A("\n### 4.4 THE PRICE — January-chosen cheapest-K families, evaluated on every month\n")
A("The family ORDER is fixed by January real cost alone; no outcome was read to choose it. Net@real:\n")
lad=R['LEVER_LADDER_JAN_SELECTED']
A("| K (cheapest families) | JAN | FEB | APR | MAY | n JAN |\n|---|---:|---:|---:|---:|---:|")
for K in range(1,11):
    r=lad[str(K)]
    A(f"| {K} | {r['JAN']['net_real']:.4f} | {r['FEB']['net_real']:.4f} | {r['APR']['net_real']:.4f} | {r['MAY']['net_real']:.4f} | {r['JAN']['n']:,} |")
A("\n**The ladder is monotone-degrading in every month.** K=1 is the best cell in 4 of 5 months and the only")
A("positive one anywhere on the ladder is FEB K=1 (+0.0040). A January-only cost ranking predicts the")
A("out-of-sample net ordering in four independent months — that is what makes this a lever rather than a")
A("January artifact.\n")
A("### 4.5 Staged decomposition — how much is cheaper cost and how much is better trades\n")
st_=R['LEVER_STAGES']
A("| stage | JAN | FEB | MAR | APR | MAY |\n|---|---|---|---|---|---|")
for s,lbl in [('S0_all','S0 all rows'),('S1_takeable','S1 + drop born_past_stop'),
              ('S2_takeable_4fam','S2 + 4 cheapest families (JAN-chosen)'),
              ('S3_takeable_4fam_12sym','S3 + 12 cheapest symbols (JAN-chosen)'),
              ('S4_plus_realgate','S4 + real-cost gate')]:
    A(f"| {lbl} | "+" | ".join(f"{st_[m][s]['net_real']:.4f} (n={st_[m][s]['n']:,})" for m in MO)+" |")
A("| **of which GROSS at S4** | "+" | ".join(f"{st_[m]['S4_plus_realgate']['gross']:.4f}" for m in MO)+" |")
A("| **of which REAL COST at S4** | "+" | ".join(f"{st_[m]['S4_plus_realgate']['real_cost']:.4f}" for m in MO)+" |")
tot=[st_[m]['S0_all']['net_real']-st_[m]['S4_plus_realgate']['net_real'] for m in MO]
A(f"\n**Total lever value S0 -> S4: "+", ".join(f"{m} +{v:.4f}" for m,v in zip(MO,[-x for x in [st_[m]['S0_all']['net_real']-st_[m]['S4_plus_realgate']['net_real'] for m in MO]]))+"**")
A(f"— i.e. "+", ".join(f"{m} +{(st_[m]['S4_plus_realgate']['net_real']-st_[m]['S0_all']['net_real']):.4f}" for m in MO)+f", mean **+{st.mean([(st_[m]['S4_plus_realgate']['net_real']-st_[m]['S0_all']['net_real']) for m in MO]):.4f} R/trade**.")
A(f"After the takeability repair alone (S1 -> S4) the lever is still worth mean **+{st.mean([(st_[m]['S4_plus_realgate']['net_real']-st_[m]['S1_takeable']['net_real']) for m in MO]):.4f} R/trade** on ~2,400-3,300 rows/month.\n")
A(f"Families used: `{', '.join(R['JAN_SELECTED_4_FAMILIES'])}`.\n")
A(f"Symbols used: `{', '.join(R['JAN_SELECTED_12_SYMBOLS'])}`.\n")
open(f'{D}/e2_RESULT_part2.md','w').write("\n".join(o)); print('part2 lines',len(o))
