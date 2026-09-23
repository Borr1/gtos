#!/usr/bin/env python3
"""Target 4a — the abstain discipline: put the three published margins on ONE basis,
then test them paired by day."""
import json, math
from pathlib import Path
import numpy as np
D = Path("docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority")
FILES = [("February 2026","FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json","+18.9"),
         ("April+May 2026","APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json","+6.6"),
         ("June+July 2026","JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json","+28.9583")]
out={"windows":[]}
for name,f,pub in FILES:
    d=json.load(open(D/f)); p=d["pooled"]
    a,m=p["market_top_abstain"],p["mixed"]
    act=a["actual_net_r"]-m["actual_net_r"]; wc=a["worst_case_net_r"]-m["worst_case_net_r"]
    # per-day paired series
    days=sorted(d["days"])
    da=[];dm=[];wa=[];wm=[]
    for k in days:
        pol=d["days"][k]["policies"]
        pa=pol["market_top_abstain"]["portfolio"]; pm=pol["mixed"]["portfolio"]
        da.append(pa["actual_net_r"]); dm.append(pm["actual_net_r"])
        wa.append(pa["worst_case_net_r"]); wm.append(pm["worst_case_net_r"])
    da,dm,wa,wm=map(np.array,(da,dm,wa,wm))
    def paired(x,y):
        dd=x-y; n=len(dd); se=dd.std(ddof=1)/math.sqrt(n); t=dd.mean()/se if se else float('nan')
        from math import erf,sqrt
        pv=2*(1-0.5*(1+erf(abs(t)/sqrt(2)))) if se else float('nan')
        return dict(n_days=n,total=float(dd.sum()),mean_per_day=float(dd.mean()),se=float(se),t=float(t),p=float(pv),
                    ci95_total=[float(dd.sum()-1.96*se*n),float(dd.sum()+1.96*se*n)],
                    positive_days=int((dd>0).sum()),negative_days=int((dd<0).sum()),zero_days=int((dd==0).sum()))
    row=dict(window=name,published_margin=pub,
        abstain=dict(selected=a["selected"],resolved=a["resolved"],censored=a["censored"],
                     actual=a["actual_net_r"],worst=a["worst_case_net_r"]),
        mixed=dict(selected=m["selected"],resolved=m["resolved"],censored=m["censored"],
                   actual=m["actual_net_r"],worst=m["worst_case_net_r"],
                   no_fill=m["outcomes"].get("NO_FILL")),
        margin_actual=act, margin_worst_case=wc,
        censoring_charge_abstain=a["actual_net_r"]-a["worst_case_net_r"],
        censoring_charge_mixed=m["actual_net_r"]-m["worst_case_net_r"],
        paired_actual=paired(da,dm), paired_worst=paired(wa,wm),
        limit_family_net_in_mixed={k:v for k,v in m["net_by_family"].items()
            if k in ("current_breaker_re_entry","current_fvg_fill","current_ob_retest")},
        limit_family_count_in_mixed={k:v for k,v in m["families"].items()
            if k in ("current_breaker_re_entry","current_fvg_fill","current_ob_retest")})
    out["windows"].append(row)
    print(f"\n=== {name}  (published margin {pub} R)")
    print(f"  abstain  sel {a['selected']:4d} res {a['resolved']:4d} cens {a['censored']:3d}  actual {a['actual_net_r']:+9.4f}  worst {a['worst_case_net_r']:+9.4f}")
    print(f"  mixed    sel {m['selected']:4d} res {m['resolved']:4d} cens {m['censored']:3d}  actual {m['actual_net_r']:+9.4f}  worst {m['worst_case_net_r']:+9.4f}  NO_FILL {m['outcomes'].get('NO_FILL')}")
    print(f"  MARGIN   actual {act:+9.4f}   worst-case {wc:+9.4f}")
    print(f"  censoring charge: abstain {a['actual_net_r']-a['worst_case_net_r']:+8.4f}  mixed {m['actual_net_r']-m['worst_case_net_r']:+8.4f}")
    pa=row["paired_actual"]; pw=row["paired_worst"]
    print(f"  paired by day, ACTUAL : total {pa['total']:+8.4f} t {pa['t']:+.3f} p {pa['p']:.4f}  (+{pa['positive_days']}/-{pa['negative_days']}/0:{pa['zero_days']} of {pa['n_days']})")
    print(f"  paired by day, WORST  : total {pw['total']:+8.4f} t {pw['t']:+.3f} p {pw['p']:.4f}  (+{pw['positive_days']}/-{pw['negative_days']}/0:{pw['zero_days']})")
    print(f"  LIMIT families inside `mixed`: {row['limit_family_count_in_mixed']} -> net {row['limit_family_net_in_mixed']}")
tot_a=sum(w["margin_actual"] for w in out["windows"]); tot_w=sum(w["margin_worst_case"] for w in out["windows"])
print(f"\nFIVE-MONTH TOTAL: actual basis {tot_a:+.4f} R ; worst-case basis {tot_w:+.4f} R")
out["five_month_total_actual"]=tot_a; out["five_month_total_worst"]=tot_w
json.dump(out,open("/private/tmp/FUNNEL_BASIS.json","w"),indent=1)
