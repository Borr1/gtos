"""d1_tables — emit every table in the receipt, from the artifacts, once."""
import json
import sys

import numpy as np

D = "/tmp/d1/"
Q = json.load(open(D + "D1_SIGNAL_QUALITY_T2.0.json"))
Q15 = json.load(open(D + "D1_SIGNAL_QUALITY_T1.5.json"))
_S = json.load(open(D + "D1_SIG_T2.0.json"))
S = _S["significance"]
SCH = _S["schedule_perm"]
AFF = _S["affordability_deciles"]
S15 = json.load(open(D + "D1_SIG_T1.5.json"))["significance"]
M = json.load(open(D + "D1_MOMENT_V1.json"))["decomposition"]
W8 = Q["windows"]
COH = ["__ALL__", "__ATMARKET__", "__POI__"]
FAM = sorted(Q["family"])
out = []
P = out.append

P("## T1 — family economics, CLEAN fills (born-past-stop excluded), 8 windows, 2R/-1R/120 M1 bars\n")
P("| family | emissions | fills | fill rate | gross R | toll R | net R | win rate | payoff | breakeven | gap | months gross+ | past-stop share of fills |")
P("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|---:|")
for f, v in sorted(Q["family"].items(), key=lambda x: -x[1]["clean_fills"]["gross"]):
    c = v["clean_fills"]
    P(f"| `{f}` | {c['n_emissions']:,} | {c['n']:,} | {c['n']/c['n_emissions']:.3f} | {c['gross']:+.5f} | "
      f"{c['cost']:.4f} | {c['net']:+.5f} | {c['wr']:.4f} | {c['payoff']:.4f} | {c['breakeven']:.4f} | "
      f"{c['gap']:+.4f} | **{v['months_gross_positive']}/8** | {v['born_past_stop_share_of_fills']:.3f} |")
for f in COH:
    v = S[f]
    P(f"| **{f}** | — | {v['n']:,} | — | {v['gross']['mean']:+.5f} | {v['toll']:.4f} | "
      f"{v['net']['mean']:+.5f} | — | — | — | — | **{v['months_positive']}/8** | 0 |")

P("\n## T2 — gross R/trade by month, clean fills\n")
P("| family | " + " | ".join(w[2:] for w in W8) + " | months+ | sign-test p |")
P("|---|" + "---:|" * 8 + ":---:|---:|")
for f, v in sorted(Q["family"].items(), key=lambda x: -x[1]["months_gross_positive"]):
    r = v["by_month_clean"]
    P(f"| `{f}` | " + " | ".join((f"{r[w]['gross']:+.4f}" if w in r else "—") for w in W8)
      + f" | **{v['months_gross_positive']}/8** | {S[f]['sign_test_p_one_sided']:.4f} |")
for f in COH:
    v = S[f]
    P(f"| **{f}** | " + " | ".join(f"{x:+.4f}" for x in v["monthly_gross"])
      + f" | **{v['months_positive']}/8** | {v['sign_test_p_one_sided']:.4f} |")

P("\n## T3 — significance of gross (day-block bootstrap, 4000 draws, 163 trading days)\n")
P("| cohort | n | gross R | CI95 | p(<=0) | net R | toll R | gross/toll | median risk dist (bps) |")
P("|---|---:|---:|---|---:|---:|---:|---:|---:|")
for f in sorted(S, key=lambda k: -S[k]["gross"]["mean"]):
    v = S[f]
    g = v["gross"]
    P(f"| {'**'+f+'**' if f.startswith('__') else '`'+f+'`'} | {v['n']:,} | {g['mean']:+.5f} | "
      f"[{g['ci95'][0]:+.5f}, {g['ci95'][1]:+.5f}] | {g['p_le_0']:.4f} | {v['net']['mean']:+.5f} | "
      f"{v['toll']:.4f} | {v['gross_over_toll']:+.3f} | {v['d_bps_median']:.2f} |")

P("\n## T4 — the three matched controls (clean fills, 2R). Every arm shares the SAME rows,\n"
  "instants, risk distances and fill events; only the side changes.\n")
P("| cohort | n | REAL gross | COIN gross | ANTI gross | direction value | CI95 | p(>=0) = evidence it is NEGATIVE | months dirval+ |")
P("|---|---:|---:|---:|---:|---:|---|---:|:---:|")
C = Q["controls"]
for f in COH + FAM:
    v = C.get(f)
    if not v:
        continue
    d = v["direction_value"]
    P(f"| {'**'+f+'**' if f.startswith('__') else '`'+f+'`'} | {v['n']:,} | {v['real_gross']:+.5f} | "
      f"{v['coin_gross']:+.5f} | {v['anti_gross']:+.5f} | **{d['mean']:+.5f}** | "
      f"[{d['ci95'][0]:+.5f}, {d['ci95'][1]:+.5f}] | {1-d['p_le_0']:.4f} | {v['months_direction_value_positive']}/8 |")

P("\n## T5 — shuffled-direction controls (side labels permuted inside cells; ambient drift preserved)\n")
P("| cohort | n | vs SHUF(w,sym,hour) | CI95 | p(<=0) | labels changed | vs SHUF(w,sym,hour,family) | CI95 | p(<=0) | labels changed |")
P("|---|---:|---:|---|---:|---:|---:|---|---:|---:|")
for f in COH + FAM:
    v = C.get(f)
    if not v:
        continue
    a, b = v["vs_shuf_symhour"], v["vs_shuf_symhourfam"]
    P(f"| {'**'+f+'**' if f.startswith('__') else '`'+f+'`'} | {v['n']:,} | {a['mean']:+.5f} | "
      f"[{a['ci95'][0]:+.5f}, {a['ci95'][1]:+.5f}] | {a['p_le_0']:.4f} | {v['shuf_symhour_label_change_rate']:.3f} | "
      f"{b['mean']:+.5f} | [{b['ci95'][0]:+.5f}, {b['ci95'][1]:+.5f}] | {b['p_le_0']:.4f} | "
      f"{v['shuf_symhourfam_label_change_rate']:.3f} |")

P("\n## T6 — MOMENT vs DIRECTION decomposition against a random moment on the same symbol+day\n")
P("| cohort | n | REAL | COIN(real rows) | COIN(random moment) | MOMENT value | p(<=0) | m+ | DIRECTION value | p(<=0) | m+ | TOTAL value | p(<=0) | toll | TOTAL/toll |")
P("|---|---:|---:|---:|---:|---:|---:|:---:|---:|---:|:---:|---:|---:|---:|---:|")
for f in COH + FAM:
    v = M.get(f)
    if not v:
        continue
    m, d, t = v["moment_value"], v["direction_value"], v["total_value"]
    P(f"| {'**'+f+'**' if f.startswith('__') else '`'+f+'`'} | {v['n']:,} | {v['real_gross']:+.5f} | "
      f"{v['coin_gross']:+.5f} | {v['random_moment_coin_gross']:+.5f} | {m['mean']:+.5f} | {m['p_le_0']:.4f} | "
      f"{v['months_moment_positive']}/8 | {d['mean']:+.5f} | {d['p_le_0']:.4f} | {v['months_direction_positive']}/8 | "
      f"**{t['mean']:+.5f}** | {t['p_le_0']:.4f} | {v['toll_real']:.4f} | {v['total_value_over_toll']:+.3f} |")

P("\n## T7 — schedule vs setup: eta^2 of gross R against the factor's OWN permutation null (200 perms)\n")
P("| family | factor | levels | eta2 | null mean | EXCESS | p(null>=obs) |")
P("|---|---|---:|---:|---:|---:|---:|")
for f, v in SCH.items():
    for fac, x in v.items():
        if x is None:
            continue
        P(f"| `{f}` | {fac} | {x['k_levels']:,} | {x['eta2']:.4f} | {x['eta2_null_mean']:.4f} | "
          f"{x['excess']:+.5f} | {x['p_ge_obs']:.3f} |")

P("\n## T8 — concentration: is a family really one instrument at one hour?\n")
P("| family | n symbols | top symbol | its row share | n hours | top hour | its row share | top-3 (sym,hour) cells' share of |gross| | raw mean gross | ambient-adjusted mean gross |")
P("|---|---:|---|---:|---:|---:|---:|---:|---:|---:|")
for f, v in Q["schedule_vs_setup"].items():
    P(f"| `{f}` | {v['n_symbols']} | {v['top_symbol']} | {v['top_symbol_row_share']:.3f} | {v['n_hours']} | "
      f"{v['top_hour']} | {v['top_hour_row_share']:.3f} | {v['top3_cells_share_of_abs_gross']:.4f} | "
      f"{v['raw_mean_gross']:+.5f} | {v['ambient_adjusted_mean_gross']:+.5f} |")

P("\n## T9 — target-geometry robustness: 2.0R (downstream contract) vs 1.5R (`risk.min_rr`, the emitted contract)\n")
P("| cohort | gross @2R | months+ @2R | gross @1.5R | months+ @1.5R | dirval @2R | dirval @1.5R |")
P("|---|---:|:---:|---:|:---:|---:|---:|")
for f in sorted(S, key=lambda k: -S[k]["gross"]["mean"]):
    a, b = S[f], S15.get(f)
    ca, cb = Q["controls"].get(f), Q15["controls"].get(f)
    if not b:
        continue
    P(f"| {'**'+f+'**' if f.startswith('__') else '`'+f+'`'} | {a['gross']['mean']:+.5f} | {a['months_positive']}/8 | "
      f"{b['gross']['mean']:+.5f} | {b['months_positive']}/8 | "
      f"{ca['direction_value']['mean']:+.5f} | {cb['direction_value']['mean']:+.5f} |")

P("\n## T10 — what would have to be true: win rate needed to pay the family's own toll\n")
W = json.load(open(D + "D1_WRNEED.json"))
P("| cohort | n | gross R | toll R | win rate now | avg win | avg loss | breakeven wr | wr that pays the toll | pp needed |")
P("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for r in W:
    P(f"| {'**'+r['c']+'**' if r['c'].startswith('__') else '`'+r['c']+'`'} | {r['n']:,} | {r['gross']:+.5f} | "
      f"{r['toll']:.4f} | {r['wr']:.4f} | {r['aw']:.4f} | {r['al']:.4f} | {r['be']:.4f} | {r['need']:.4f} | "
      f"**{r['pp']:+.2f}** |")

P("\n## T11 — affordability: risk-distance deciles (clean fills). No slice pays.\n")
for f in ["__ATMARKET__", "structural_distance_extreme", "liquidity_sweep_reclaim", "cross_asset_lead_lag"]:
    P(f"\n**{f}**\n")
    P("| decile | d_lo bps | d_hi bps | n | gross R | toll R | net R | gross/toll |")
    P("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in AFF[f]:
        P(f"| {r['decile']} | {r['d_lo']:.2f} | {r['d_hi']:.2f} | {r['n']:,} | {r['gross']:+.5f} | "
          f"{r['cost']:.4f} | {r['net']:+.5f} | {r['gross']/r['cost']:+.3f} |")

P("\n## T12 — family x side (clean fills)\n")
P("| family | n LONG | gross LONG | coin LONG | dirval LONG | n SHORT | gross SHORT | coin SHORT | dirval SHORT |")
P("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for f, v in Q["family_by_side"].items():
    L, Sd = v.get("L"), v.get("S")
    if not L or not Sd:
        continue
    P(f"| `{f}` | {L['n']:,} | {L['gross']:+.5f} | {L['coin_gross']:+.5f} | {L['gross']-L['coin_gross']:+.5f} | "
      f"{Sd['n']:,} | {Sd['gross']:+.5f} | {Sd['coin_gross']:+.5f} | {Sd['gross']-Sd['coin_gross']:+.5f} |")

open(D + "D1_TABLES.md", "w").write("\n".join(out) + "\n")
print("wrote /tmp/d1/D1_TABLES.md", len(out), "lines")
