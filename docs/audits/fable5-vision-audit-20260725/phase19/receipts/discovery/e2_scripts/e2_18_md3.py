import json,os,statistics as st
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
R=json.load(open(f'{D}/e2_RESULT.json')); MO=['JAN','FEB','MAR','APR','MAY']
o=[];A=o.append
A("\n---\n\n## 5. BOUNDARY — where it holds and where l10's per-symbol claims do NOT\n")
A("### 5.1 The symbol claims are JANUARY-ONLY. This is the clearest localization in the lane.\n")
b=R['BOUNDARY_SYMBOL']['rows']
A("l10 X11: *\"USDCHF is the only symbol in the pool with positive takeable gross (+0.0117, n=774), and")
A("GER40 is the only other one at breakeven (-0.0030, n=1,400).\"* Extended:\n")
A("| symbol | JAN | FEB | MAR | APR | MAY | mean gross | mean real cost | mean net@real | months gross>0 | total n |")
A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for k,v in sorted(b.items(),key=lambda kv:-kv[1]['gross_mean']):
    g=v['gross_by_month']
    A(f"| {k} | {g['JAN']:.4f} | {g['FEB']:.4f} | {g['MAR']:.4f} | {g['APR']:.4f} | {g['MAY']:.4f} | **{v['gross_mean']:.4f}** | {v['real_cost_mean']:.4f} | {v['net_real_mean']:.4f} | {v['months_gross_positive']} | {v['n_total']:,} |")
usd=b['USDCHF']; ger=b['GER40']
A(f"\n**USDCHF's +0.0117 does not survive contact with any other month** — {usd['gross_by_month']['FEB']:.4f} / {usd['gross_by_month']['MAR']:.4f} / {usd['gross_by_month']['APR']:.4f} / {usd['gross_by_month']['MAY']:.4f}, mean **{usd['gross_mean']:.4f}** on n={usd['n_total']:,}.")
A(f"**GER40's -0.0030 becomes mean {ger['gross_mean']:.4f}.** Over five months **no symbol of 24 has positive mean gross**,")
A("and only three (EURJPY, AUDUSD, USDCHF) have even one positive month. Treat every single-month per-symbol")
A("gross number in this estate as noise until it is shown over four months.\n")
A("### 5.2 The SESSION axis replaces it — and it is much stronger\n")
s=R['BOUNDARY_SESSION']['rows']
A("| session bucket | JAN | FEB | MAR | APR | MAY | mean gross | mean real cost | mean net@real | total n |")
A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for k,v in sorted(s.items(),key=lambda kv:-kv[1]['gross_mean']):
    g=v['gross_by_month']
    A(f"| {k} | {g['JAN']:.4f} | {g['FEB']:.4f} | {g['MAR']:.4f} | {g['APR']:.4f} | {g['MAY']:.4f} | **{v['gross_mean']:.4f}** | {v['real_cost_mean']:.4f} | {v['net_real_mean']:.4f} | {v['n_total']:,} |")
A("\n**`london` is the best-gross session in 4 of 5 months** at mean -0.0251 on n=18,538; `ny` is second at")
A("-0.0694 on n=18,247 and carries the CHEAPEST real cost of any bucket (0.1158), giving it the best mean")
A("net@real of any large bucket (-0.1852). Every hour bucket outside the three named sessions is worse on")
A("gross than all three of them. Unlike the symbol axis this holds at n>5,000/bucket.\n")
A("\n---\n\n## 6. NEW FINDING E2-N3 — the estate's best conditioned cell, and its honest statistics\n")
sw=R['SWEEP']
A(f"A pre-enumerated sweep of **{sw['n_declared_cells']} declared cells**: 10 family depths (ordered by")
A("JANUARY real cost only) x 5 session sets x 2 gate choices, each read on all five months.")
A(f"**{sw['n_positive_mean_gross']} of {sw['n_declared_cells']} have positive mean gross; {sw['n_positive_mean_net_real']} have positive mean net@real** (and those two are")
A("the same cell with and without a gate that does not bind it).\n")
A("| cell | JAN | FEB | MAR | APR | MAY | mean gross | mean net@real | months gross>0 | min month n | total n |")
A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for k,v in list(sw['top10'].items()):
    g=v['per_month_gross']
    A(f"| `{k}` | "+" | ".join(f"{g[m]:.4f}" if v['per_month_n'][m]>=30 else "-" for m in MO)+f" | **{v['gross_mean']:.4f}** | {v['net_real_mean']:.4f} | {v['months_gross_positive']} | {v['n_min_month']} | {v['n_total']} |")
c=R['BEST_CELL_STAT']
A(f"\n### 6.1 The winner, stated honestly\n")
A(f"**Cell:** {c['cell']}\n")
A("| statistic | value |\n|---|---|")
A(f"| n | **{c['n']}** (JAN {c['n_by_month']['JAN']}, FEB {c['n_by_month']['FEB']}, MAR {c['n_by_month']['MAR']}, APR {c['n_by_month']['APR']}, MAY {c['n_by_month']['MAY']}) |")
A(f"| distinct decision days | {c['distinct_decision_days']} |")
A(f"| pooled gross mean | **+{c['gross_mean']:.6f}** |")
A(f"| bootstrap 90% CI on gross | [{c['gross_bootstrap_90CI'][0]:.4f}, {c['gross_bootstrap_90CI'][1]:.4f}] |")
A(f"| bootstrap 95% CI on gross | [{c['gross_bootstrap_95CI'][0]:.4f}, {c['gross_bootstrap_95CI'][1]:.4f}] |")
A(f"| real cost | {c['real_cost_mean']:.6f} |")
A(f"| pooled net@real | **+{c['net_real_mean']:.6f}** |")
A(f"| bootstrap 90% CI on net@real | [{c['net_real_bootstrap_90CI'][0]:.4f}, {c['net_real_bootstrap_90CI'][1]:.4f}] |")
A(f"| permutation p vs same-month NY peers (B={c['permutation_B']:,}) | **{c['permutation_p_vs_same_month_ny_peers']:.4f}** |")
A(f"| NY universe gross mean (the null it beats) | {c['ny_universe_gross_mean']:.6f} |")
A(f"| declared looks in this lane | {c['declared_looks_this_lane']} |")
A(f"\n**Symbol composition:** {json.dumps(c['symbols'])}\n")
A("**Read it exactly as it is.** The pooled gross mean is +0.0331; the +0.0408 in the sweep table is the")
A("mean of per-month means, which weights a 47-row April equally with a 117-row January. The 90% bootstrap")
A("interval spans zero. The permutation p of 0.0548 is against a same-month NY null, i.e. it already controls")
A("for session and month, but it does NOT control for the 100 declared looks. **This is a discovery-grade")
A("signal that survives five months and a session-matched permutation at n=390. It is not an admission and")
A("no gate in this estate would pass it.** What makes it interesting is not the p-value but that its two")
A("families are the two the January cost ranking picked FIRST, before any outcome was read.\n")
A("### 6.2 Named conditioned cells, for the record\n")
cc=R['CONDITIONED_CELLS']
A("| cell | JAN | FEB | MAR | APR | MAY | mean net@real | mean gross | total n |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for k,v in cc.items():
    A(f"| {k} | "+" | ".join(f"{v[m]['net_real']:.4f}" if v[m]['n'] else "-" for m in MO)+f" | **{v['SUMMARY']['net_real_mean']:.4f}** | {v['SUMMARY']['gross_mean']:.4f} | {v['SUMMARY']['n_total']:,} |")
open(f'{D}/e2_RESULT_part3.md','w').write("\n".join(o)); print('part3 lines',len(o))
