"""Generate the per-generator pages of SLEEVE_FORENSIC_REPORT.md directly from
SLEEVE_FORENSIC_V1.json, so the report and the machine-readable record cannot diverge."""
from __future__ import annotations
import json, os
P=os.path.dirname(os.path.abspath(__file__)); PH20=os.path.dirname(os.path.dirname(P))
D=json.load(open(f"{PH20}/SLEEVE_FORENSIC_V1.json"))
ORDER=[("core_w7_armed","Section A — the armed book (4 sleeves, Borhen's money today)"),
       ("core_w7_pulled","Section B — armed and pulled (2 sleeves)"),
       ("core_w7_never_armed","Section C — core W7, never armed (3 sleeves)"),
       ("core_w7_unmeasured","Section D — core W7, never measured (1 sleeve)"),
       ("candidate_book","Section E — the candidate book (9 live-registered sleeves)"),
       ("candidate_book_quarantined","Section F — the candidate book, quarantined (3 sleeves)"),
       ("market_expansion_mx","Section G — the market-expansion mx_* cohort (14 sleeves)"),
       ("registered_for_sizing_no_generator","Section H — registered for sizing, no generator (1)"),
       ("broad_origin_POI","Section I — the broad-V4 POI frameworks (3 families)"),
       ("broad_origin_production","Section J — the broad-V4 production origin families (10 families)")]
def fmt(x, n=4):
    if x is None: return "—"
    if isinstance(x,float): return f"{x:.{n}f}"
    return str(x)
L=[]
gens=D["generators"]; mach=D["shared_machinery"]
for klass,title in ORDER:
    members=[k for k,v in gens.items() if v["klass"]==klass]
    if not members: continue
    L.append(f"\n## {title}\n")
    for name in sorted(members, key=lambda n:(gens[n]["verdict"], n)):
        r=gens[name]
        L.append(f"### `{name}` — **{r['verdict']}**\n")
        L.append(f"**Premise.** {r['premise']}\n")
        L.append(f"**Origin.** {r['origin']}\n")
        L.append(f"**Claimed at birth vs known now.** {r['claimed_at_birth']}\n")
        L.append(f"**Parameters.** {r['parameters']}\n")
        L.append(f"**Geometry vs premise.** {r['geometry']}\n")
        L.append(f"**Life cycle.** {r['lifecycle']}\n")
        # numeric block
        num=[]
        if "s1" in r:
            s=r["s1"]; num.append(f"| walked trades | {s['n']} | timeframe | {s['timeframe']} |")
            num.append(f"| realised median hold | {s['hold_h_median']:.1f} h | stop | {s['stop_bps']:.2f} bps = {s['stop_over_atr']:.2f} x ATR |")
            num.append(f"| toll | {s['toll_bps']:.2f} bps (cost_r {s['cost_r']:.4f}) | **signal at own hold / toll** | **{s['signal_over_toll']:.2f}x** |")
            num.append(f"| excursion capture | {s['capture_frac']*100:.1f} % of mean MFE {s['mfe_r_mean']:.2f} R | exits | {s['exit_reasons']} |")
            num.append(f"| estate decision | {s['estate_decision']} | gate | {s['gate_verdict']} |")
        if "s2" in r:
            s=r["s2"]; num.append(f"| confidence | {s['confidence']:.2f} | corr-cluster | `{s['corr_cluster']}` |")
            if s["n_trades"] is not None and s["n_trades"]>0:
                num.append(f"| gated trades | {s['n_trades']} ({s['per_year']:.1f}/yr) | grid | {s['grid']} |")
                num.append(f"| declared horizon | {fmt(s['live_horizon_own_bars'],1)} own bars | realised median hold | {fmt(s['med_hold_own_bars'],1)} own bars (p90 {fmt(s['p90_hold_own_bars'],1)}) |")
                num.append(f"| resolved inside entry bar | {fmt(s['frac_resolved_in_entry_bar'])} | exceeding live horizon | {fmt(s['frac_over_live_horizon'])} |")
                num.append(f"| median MFE | {fmt(s['mfe_med_r'],3)} R | exit mix | {s['exit_mix']} |")
                num.append(f"| ratified gate (mid band) | {s['gate_verdict_mid']} | R/day | {fmt(s['gate_r_per_day_mid'])} |")
        if "x1" in r:
            x=r["x1"]; num.append(f"| **X1 mechanism** | **{', '.join(x['mechanism_tags'])}** | max signed t across the ladder | {x['max_signed_t']:.2f} |")
            num.append(f"| IR at own hold (the idea) | {x['IR_at_own_hold']:.4f} | cost_r (cost geometry) | {x['cost_r_toll_over_stop']:.3f} |")
            num.append(f"| TIGHT = stop/sigma (stop geometry) | {x['TIGHT_stop_over_sigma']:.3f} | RATIO signal/toll | {fmt(x['RATIO_signal_over_toll'],3)} |")
            num.append(f"| realised resolution T_res | {x['T_res_h']:.2f} h | drift argmax T_peak | {x['T_peak_h']:.1f} h |")
        if "ceiling" in r:
            c=r["ceiling"]; num.append(f"| **ceiling at h\\*={c['best_h']:.1f} h** | drift {c['drift_bps']:.2f} − toll {c['toll_bps']:.2f} = **{c['net_bps']:.2f} bps** | CI95 | [{c['ci95'][0]:.2f}, {c['ci95'][1]:.2f}] |")
            num.append(f"| ceiling verdict | {c['verdict']} | n | {c['n']} |")
        if "irrelevant_by_construction" in r:
            i=r["irrelevant_by_construction"]
            num.append(f"| emissions (8 windows) | {i['n_emissions']:,} | **irrelevant by construction** | **{i['union_share']*100:.2f} %** |")
            num.append(f"| off-session {i['off_configured_session']*100:.2f} % · born past stop {i['born_past_stop']*100:.2f} % | | target already behind {i['target_already_behind']*100:.2f} % · stale bar {i['stale_bar']*100:.2f} % | |")
        if num:
            L.append("| | | | |\n|---|---|---|---|")
            L.extend(num); L.append("")
        L.append(f"**Verdict — {r['verdict']}. Repair.** {r['repairable']}\n")
        L.append(f"*Evidence:* `{r['evidence']}`\n")
L.append("\n## Section K — shared machinery (not generators; both are code paths every family above rides)\n")
for name,r in mach.items():
    L.append(f"### `{name.lstrip('_')}` — **{r['verdict']}**\n")
    L.append(f"**Premise.** {r['premise']}\n\n**Origin.** {r['origin']}\n\n**Claimed at birth.** {r['claimed_at_birth']}\n")
    L.append(f"**Parameters.** {r['parameters']}\n\n**Geometry.** {r['geometry']}\n\n**Life cycle.** {r['lifecycle']}\n")
    L.append(f"**Verdict — {r['verdict']}. Repair.** {r['repairable']}\n\n*Evidence:* `{r['evidence']}`\n")
open(f"{P}/_pages.md","w").write("\n".join(L))
print("pages", len(L), "lines ->", f"{P}/_pages.md")
