#!/usr/bin/env python3
"""l7_receipt — assemble L7_RESULT.md / L7_RESULT.json from every measured artifact."""
import json, os, gzip, collections
H = os.path.dirname(os.path.abspath(__file__))
L = lambda n: json.load(open(os.path.join(H, n)))
SW, CE, DE, CO, ME, NE, SC, W3, ZS, MG = (L("L7_SWEEP_V1.json"), L("L7_CELLS_V1.json"), L("L7_DECOMP_V1.json"),
    L("L7_CONTROLS_V1.json"), L("L7_MECH_V1.json"), L("L7_NET_V1.json"), L("L7_STAB_CQ_V1.json"),
    L("L7_WIDE3_V1.json"), L("L7_ZEROSPREAD_V1.json"), L("L7_MAGNET_V1.json"))
DL, SS, DR = L("L7_DELAY_V2.json"), L("L7_SCALE_V1.json"), L("L7_DELAYREPAIR_V1.json")
out = dict(lane="l7-inversions", month="January 2026 (true UTC, CJ re-clocked)",
    substrate=dict(base="l7_BASE.jsonl.gz", n=27658, n_with_anchor=27641),
    instruments=dict(
      pool_gross_r="the engine's own fill-BLIND realized gross (brief's basis)",
      orig_honest_r="+2R/-1R first touch, entry limit must be traded first",
      inv_honest_r="opposite side at the SAME level, stop/target reflected, mirror fill contract",
      orig_atm_r="signal's own side entered AT MARKET at the decision instant (prev_close anchor), same risk distance d, +2R/-1R",
      inv_atm_r="opposite side AT MARKET. EXACT MIRROR of orig_atm: fav_inv=-adv_atm, adv_inv=-fav_atm. Both fill at bar 1. No fill contract can bias the comparison.",
      info="(inv_atm_r - orig_atm_r)/2 = the whole directional content of the signal; positive => the sign is INVERTED"),
    headline_at_market=dict(pool=dict(n=27641, orig=-0.2257, inv=+0.2914, info=+0.2586),
      clean_at_limit=dict(n=14911, orig=-0.0596, inv=+0.0931, info=+0.0764,
        boot95=[0.0530, 0.1020], p_le0=0.0, days=21, info_first_emission=0.0746, info_lag1_1min=0.0438)),
    latency_decay=DL, physical_scale=SS, delayed_entry_repair=DR,
    born_state=DE["by_born_state"], mkt_r_buckets=DE["by_mkt_r_bucket"], controls=CO["controls"],
    mechanism=dict(risk_distance_quintiles=ME["M1_pooled"], per_family_quintiles=ME["M1_risk_distance_quintiles"],
      session=[x for x in ME["M2_session"] if x["scope"]=="session"],
      family_x_session_original_works=[x for x in ME["M2_session"] if x["scope"]=="family_x_session" and x["info"]<0],
      hour=ME["M2_hour"], net_by_quintile=NE["net_by_quintile"], zero_spread_limit=ZS),
    economics=dict(net_populations=ME["M3_net"], wide3=W3,
      zero_spread_note="CLEAN inverse gross +0.09312 R vs non-spread cost floor 0.10484 R -> UNREACHABLE at any spread divisor"),
    stability=SC["stability"], by_symbol=SC["by_symbol"], cq_crosscheck=SC["cq"],
    fill_conditioning=dict(source="src/research_infra/v4_timewarp_simulated_live_research_loop.py:60309-60310",
      rule="path_final_r returns (None,'not_filled_no_trade',None) when fill_status does not start with 'filled'; the pool filter requires opportunity_net_proxy_r is not None",
      magnet=MG["ALL_resting"], magnet_buckets=MG["buckets"],
      hazard_signature="touch hazard over resting mkt_r>2 rises 6.909% -> 100.000% in the final 10-bar block (140 at risk, 140 touched), 0 of 2171 never touched"),
    cells=dict(clean_top=CE["CLEAN_at_limit"]["cells"][:120], clean_negative=sorted([c for c in CE["CLEAN_at_limit"]["cells"] if c["n"]>=60], key=lambda c: c["info"])[:40],
      n_cells=CE["CLEAN_at_limit"]["n_cells"], pool_basis_top=SW["cells"]["ALL"][:40], tradeable_basis_top=sorted(SW["cells"]["TRADEABLE"], key=lambda c:-c["honest_score"])[:40],
      net_top=NE["net_cells"][:60]))
json.dump(out, open(os.path.join(H, "L7_RESULT.json"), "w"), indent=1)

def tb(hdr, rowsx):
    s = "| " + " | ".join(hdr) + " |\n|" + "|".join("---" for _ in hdr) + "|\n"
    for r in rowsx: s += "| " + " | ".join(str(x) for x in r) + " |\n"
    return s
M = []
A = M.append
A("# LANE l7 — WHAT ELSE IS BACKWARDS\n")
A("**Headline.** Over the 14,911 January candidates whose entry price IS the decision-instant market price "
  "(geometry-free and selection-free), taking the **opposite side at market** with the generator's own risk distance "
  "is worth **+0.0764 R/trade** of directional information (day-block bootstrap 95% [+0.0530, +0.1020], p(<=0)=0.0000, "
  "t=8.71, positive on **20 of 21 trading days** and **23 of 24 symbols**). The signal's direction is inverted across "
  "the whole book, not in one family. It is **not** the CQ breaker phenomenon — the two populations share **zero rows**.\n")
A("**And the qualifier that governs how to read every number below: it is a ONE-MINUTE effect.** Delay the entry by "
  "two minutes and the directional signal falls to **+0.0148 R/trade, p=0.157** — gone. At the median risk distance the "
  "whole signal is **0.783 bps of price** (1.566 bps between the two legs). This is not a directional forecast the book "
  "can trade; it is a measurement that **the generator's entry price is systematically on the wrong side of the very "
  "next minute**, by about one spread. Section 2.1 is the ladder.\n")
A("**Which turns the whole lane into a repair that requires no inversion at all.** Keep the signal's own direction, "
  "keep the risk distance, keep the target and stop — just stop entering at the trigger bar's close. Waiting "
  "**5 minutes** is worth **+0.0670 R/trade** (paired per row, day-block bootstrap 95% [+0.0550, +0.0786], "
  "p(<=0)=0.000, n=14,837) and moves the at-market book from **-0.0601 to +0.0069 — across zero**. "
  "`structural_distance_extreme` moves **-0.0825 -> +0.1083** and `off_configured_session` **-0.0996 -> +0.0111**. "
  "Section 3.4. **The direction is not backwards; the entry instant is, and the inversion at delay 0 is its shadow.**\n")
A("## 0. Instruments — read before any number below\n")
A("An 'inverse' at the same limit level is NOT a mirror: the fill contract differs (a buy limit below market becomes a "
  "sell order above it). Every directional claim here uses the **at-market pair**, which is an exact mirror:\n")
A("```\nfav_atm = fav - mkt_r     adv_atm = adv - mkt_r     (signal's own side, entered at market)\n"
  "fav_inv = -adv_atm        adv_inv = -fav_atm          (opposite side, same price, same d)\n"
  "info    = (inv_atm_r - orig_atm_r) / 2\n```\n")
A("Both legs fill at bar 1 by construction, carry the same risk distance `d`, the same +2R/-1R contract, the same "
  "conservative same-bar tie-to-stop rule, and mark to market at the same 120-bar wall. No fill contract, no geometry "
  "and no horizon can bias `info`. Anchor is `mkt_r_prev_close` — the close of the last M1 bar **strictly before** the "
  "decision minute, i.e. the w0-capture V2 no-look-ahead anchor. Reproduces w0-capture's born census exactly "
  "(at_limit 14,911 / resting 7,949 / past_stop 3,516 / marketable 1,265).\n")
A("**Integrity checks.** `orig_atm_r == orig_blind_r` on all 14,911 at-limit rows, max |diff| **0.00e+00** (the at-market "
  "entry IS the limit there). Engine `gross_r` vs path-derived blind walk: sign agreement **90.69%**, Pearson **+0.7503** "
  "— a flipped side convention in the sidecar would be strongly negative, so the convention is consistent. "
  "`which_came_first` reproduces the walk reason on 27,648 of 27,658 rows.\n")
A("## 1. THE INVERSION, by born state\n")
A(tb(["born state","n","orig at-market","inv at-market","INFO","INFO 95% lo","INFO 95% hi","INFO first-emission"],
   [[t["born_state"], t["n"], f"{t['orig_atm']:+.4f}", f"{t['inv_atm']:+.4f}", f"{t['info']:+.4f}",
     f"{(t['boot'] or {}).get('lo',float('nan')):+.4f}", f"{(t['boot'] or {}).get('hi',float('nan')):+.4f}",
     f"{t['info_first']:+.4f}"] for t in DE["by_born_state"]]))
A("`born_at_limit` is the clean cell: entry == market exactly (one distinct `mkt_r` value, 0.0), so the inverse target "
  "sits exactly 2R away just like the original's, and the fill is instantaneous so the pool's fill-conditioning "
  "(section 5) cannot have selected on the path.\n")
A("## 2. The two controls that decide it\n")
A(tb(["population","n","long share","long@mkt","short@mkt","INFO","95% lo","INFO lag-1","95% lo","INFO drift-free","95% lo","p(<=0)"],
   [[t["pop"], t["n"], f"{t['long_share']:.1%}", f"{t['long_atm']:+.4f}", f"{t['short_atm']:+.4f}", f"{t['info']:+.4f}",
     f"{t['boot_info']['lo']:+.4f}", f"{t['info_lag1']:+.4f}", f"{t['boot_info_lag1']['lo']:+.4f}",
     f"{t['info_clean']:+.4f}", f"{t['boot_info_clean']['lo']:+.4f}", f"{t['boot_info_clean']['p_le0']:.3f}"] for t in CO["controls"]]))
A("**C2 market drift is refuted.** `delta = (short@mkt - long@mkt)/2` knows nothing about the signal, so any common "
  "January drift sits in it identically for LONG- and SHORT-signalled rows. On the clean population "
  "`delta|LONG-signal = +0.0577` and `delta|SHORT-signal = -0.0920` — a **+0.1497 gap straddling zero** — while the "
  "unconditional drift is only **-0.0238**. The drift-free statistic `info_clean = +0.0749` is within 0.0015 of the raw "
  "`info`. The signal's own direction call is what is inverted.\n")
A("**C1 latency is the binding caveat, and it is severe.** Re-entering at the close of the decision-minute bar "
  "(a 1-minute delay) gives `info` **+0.0438** on the clean population and **+0.2287** pool-wide. Pushing it further "
  "kills it outright — see 2.1.\n")
A("### 2.1 Entry-latency ladder — enter at the close of path bar k, walk bars k+1..120\n")
A("Unambiguous construction: the entry price is fully known at the end of bar k and no bar before k+1 is scored, so "
  "orig and inv stay exact mirrors at every rung.\n")
A(tb(["delay (min)","n","orig@mkt","inv@mkt","INFO","boot 95% lo","boot 95% hi","p(<=0)","t"],
  [[t["delay_min"], t["n"], f"{t['orig']:+.4f}", f"{t['inv']:+.4f}", f"{t['info']:+.4f}", f"{t['boot_lo']:+.4f}",
    f"{t['boot_hi']:+.4f}", f"{t['p_le0']:.3f}", f"{t['t_naive']:.2f}"] for t in DL]))
A("**The signal is 81% gone after two minutes and is not statistically distinguishable from zero anywhere between "
  "2 and 15 minutes.** (The 30- and 60-minute rungs turn significant again at +0.0262 / +0.0221 — a separate, slower "
  "effect this lane does not characterise, and a real lead for a later wave.)\n")
A("This ladder was produced independently twice. A prior l7 attempt that did not survive to write a receipt left "
  "`L7_DELAY_LADDER_V1.json` and `L7_CRUX_V2.json` in this directory; its `dir_signal_mean` is "
  "**+0.0763844644893032** against this lane's **+0.0763844644893032**, and its delay rungs (0.07638 / 0.01482 / "
  "0.01189 / 0.00765 / 0.01407 at 0/1/2/5/15) reproduce the table above to 4 decimals from different code. "
  "**This lane's first latency estimate (`info_lag1 = +0.0438`) was measured at a 1-minute delay and is correct at "
  "that delay; it is not in conflict with the 2-minute rung, and the 2-minute rung is the one that matters.**\n")
A("### 2.2 Physical scale — the signal is one spread wide\n")
A(tb(["quantity","value"],
  [["median risk distance `d` (clean population)", f"{SS['median_rd_pct']:.5f}% of price"],
   ["directional signal", f"{SS['info_r']:.4f} R = **{SS['info_bps']:.3f} bps** of price"],
   ["spread between the two legs (2 x info)", f"**{SS['two_leg_bps']:.3f} bps**"],
   ["pool FROZEN spread charge, median", f"{SS['frozen_spread_bps_median']:.3f} bps"],
   ["true spread at the measured 7.3x over-charge, median", f"{SS['corrected_spread_bps_median']:.3f} bps"]]))
A("The one-minute adverse move is **5.5x the corrected true spread** and **0.75x the frozen charge** — which is why "
  "the spread model is *not* what kills the inverse (section 4); the non-spread fixed costs are.\n")
A("## 3. MECHANISM\n")
A("### 3.1 It is monotone in stop tightness — measured WITHIN family so it is not a family proxy\n")
A(tb(["risk-distance quintile","n","median d (% of price)","orig@mkt","inv@mkt","INFO"],
   [[t["quintile"], t["n"], f"{ME['M1_risk_distance_quintiles'][0]['rd_pct_med']:.4f}" if False else f"{NE['net_by_quintile'][t['quintile']-1]['rd_pct_med']:.4f}",
     f"{t['orig']:+.4f}", f"{t['inv']:+.4f}", f"{t['info']:+.4f}"] for t in ME["M1_pooled"]]))
A("Tightest-stop quintile **+0.1138**, widest **+0.0429**, monotone. The tighter the generator's own stop, the more "
  "inverted its direction call.\n")
A("### 3.2 The generators, read at source\n")
A("Every one of the seven families in the clean population enters at `entry=bar.close` — that is *why* they are the "
  "at-limit population. Three read directly:\n")
A(tb(["family","source","rule","direction","INFO"],
  [["`structural_distance_extreme`","`src/components/broader_origin_generators.py:862-897`","`pos50>=0.97` -> SHORT at close, stop `bar.high+0.25*atr14`; `pos50<=0.03` -> LONG","**fades** a 50-bar (12.5 h) range extreme","**+0.1356**"],
   ["`cross_asset_lead_lag`","`broader_origin_generators.py:1023-1032`","`side = LONG if leader_move>0 else SHORT`, fired only when `lag_response<=0.5`","**follows** a 1-bar leader impulse into an unresponsive lag","**+0.1002**"],
   ["`displacement_continuation`","`broader_origin_generators.py:745-752`","`range/atr14>=1.5 and body/atr14>=0.75`; `side = LONG if close>open`, stop at the far end of the bar","**follows** a 1-bar (15 min) impulse","**+0.0818**"],
   ["`liquidity_sweep_reclaim`","`broader_origin_generators.py:708-742`","swept prior-20 high and closed back below -> SHORT at close","**fades** a 20-bar sweep","+0.0355 (95% lo -0.0111, not significant)"]]))
A("The pairing looks **backwards at both scales** — the family that *fades* a 12.5-hour extreme is the most inverted "
  "(continuation wins there) and the families that *follow* a 15-minute impulse are inverted too (reversion wins "
  "there) — but the latency ladder says the common cause is simpler and sits below both. **Entry is `entry=bar.close` "
  "in every one of the seven clean families**, i.e. at the extreme of the bar whose extremeness is the trigger "
  "condition, and the whole effect is spent in the next one to two minutes. The direction the rule chose barely "
  "matters; the *price* it chose does. The one family whose trigger does not require a directional close — "
  "`liquidity_sweep_reclaim`, which requires a **reclaim** (`bar.low < p_low20 and bar.close > p_low20`), so its close "
  "is back *inside* the range rather than at an extreme — is the one family that is **not** significantly inverted "
  "(+0.0355, 95% lo -0.0111). That is the mechanism, and it is a testable prediction the pool corroborates.\n")
A("### 3.3 London is the exception — the original direction WORKS there\n")
A(tb(["route session","n","orig@mkt","inv@mkt","INFO","95% CI","p(<=0)"],
  [[t["key"], t["n"], f"{t['orig']:+.4f}", f"{t['inv']:+.4f}", f"{t['info']:+.4f}",
    f"[{t['boot']['lo']:+.4f}, {t['boot']['hi']:+.4f}]", f"{t['boot']['p_le0']:.3f}"] for t in [x for x in ME["M2_session"] if x["scope"]=="session"]]))
A("`london` is the **only** session with a positive at-market original (+0.0235) and its `info` is **-0.0079**, "
  "95% CI [-0.0454, +0.0362], p(<=0)=0.634 — indistinguishable from zero. Inside London the same families invert back:\n")
A(tb(["family x session","n","orig@mkt","inv@mkt","INFO"],
  [[t["key"], t["n"], f"{t['orig']:+.4f}", f"{t['inv']:+.4f}", f"{t['info']:+.4f}"]
   for t in sorted([x for x in ME["M2_session"] if x["scope"]=="family_x_session" and x["info"]<0], key=lambda x:x["info"])]))
A("This is the lane's partial-inversion finding: **the book is directionally correct in London and inverted "
  "everywhere else.** `off_configured_session` — 7,655 of the 14,911 clean rows (51.3%) — is the most inverted "
  "session at +0.1104, and w0-dictionary D12 measured that only 1,079 rows in the whole month are actually rejected "
  "for firing off-session.\n")
A("### 3.4 THE REPAIR — same direction, later entry\n")
A("If the mechanism is the entry price rather than the direction, then simply delaying the entry should repair the "
  "book without any inversion. It does. Paired per row against delay 0, same side, same `d`, same +2R/-1R, same wall:\n")
A(tb(["delay (min)","orig level","delta vs delay 0","95% lo","95% hi","p(<=0)","orig NET @spread/7.3","% rows whose outcome moved"],
  [[t["delay"], f"{t['orig_level']:+.4f}", f"**{t['delta_vs_d0']:+.4f}**", f"{t['delta_lo']:+.4f}", f"{t['delta_hi']:+.4f}",
    f"{t['p_le0']:.3f}", f"{t['orig_net73']:+.4f}", f"{t['pct_changed']:.1%}"] for t in DR["rungs"]]))
A("Every rung from 1 to 30 minutes is positive and significant; **5 minutes is the peak at +0.0670 R/trade** and is the "
  "only rung where the at-market book is positive (+0.0069). Only 45.0% of rows change outcome at all, so the gain is "
  "concentrated at roughly **+0.149 R on the rows that move**. It does **not** repair the net "
  "(-0.2261 -> -0.1591 at spread/7.3) — the fixed-cost problem in section 4 is untouched — but it is the only change in "
  "this receipt that takes a gross number across zero, and it needs no new signal, no direction flip and no new data.\n")
A(tb(["family","n","delay 0","delay 5","delta"],
  [[t["family"], t["n"], f"{t['d0']:+.4f}", f"{t['d5']:+.4f}", f"**{t['delta']:+.4f}**"] for t in DR["by_family_delay5"]]))
A(tb(["route session","n","delay 0","delay 5","delta"],
  [[t["session"], t["n"], f"{t['d0']:+.4f}", f"{t['d5']:+.4f}", f"**{t['delta']:+.4f}**"] for t in DR["by_session_delay5"]]))
A("`tokyo` is the one session the delay does not help (-0.0002) — consistent with it being the session whose inversion "
  "is largest at delay 0 for a different reason, and worth its own look.\n")
A("## 4. IS THE INVERSION HARVESTABLE? No — and the reason is exact\n")
A(tb(["quintile","n","median d %","INFO","inv gross","cost frozen","cost @spread/7.3","inv NET @7.3","95% lo","orig NET @7.3"],
  [[t["quintile"], t["n"], f"{t['rd_pct_med']:.4f}", f"{t['info']:+.4f}", f"{t['inv_gross']:+.4f}", f"{t['cost_frozen']:.4f}",
    f"{t['cost73']:.4f}", f"{t['inv_net73']:+.4f}", f"{t['boot']['lo']:+.4f}", f"{t['orig_net73']:+.4f}"] for t in NE["net_by_quintile"]]))
A("Cost is R-denominated, so the same tiny risk distance that maximises the inversion maximises the bill. The ratio "
  "`inv_gross / cost@7.3` is **0.51, 0.64, 0.49, 0.66, 0.53** across the five quintiles — the inversion is worth about "
  "**half the corrected cost at every geometry**.\n")
A("**The zero-spread limit settles it.** On the clean population the inverse's gross edge is **+0.09312 R** and the "
  "**non-spread** cost floor (commission + the flat 0.02 slippage + swap) is **0.10484 R**. The edge does not clear the "
  "cost floor *even if the spread model is corrected to zero*. Per quintile, `edge - fixed cost`:\n")
A(tb(["quintile","n","inv gross","fixed (non-spread) cost R","edge - fixed","fixed/edge"],
  [[t["quintile"], t["n"], f"{t['inv_gross']:+.4f}", f"{t['fixed_cost_r']:.4f}", f"{t['edge_minus_fixed']:+.4f}",
    f"{t['fixed_cost_r']/t['inv_gross']:.2f}"] for t in ZS]))
A("Three families do clear the zero-spread floor — the wide-geometry ones: `displacement_continuation` (+0.0185), "
  "`session_open_range_break` (+0.0359), `volatility_compression_expansion` (+0.0408). Taken together (n=6,057) the "
  "inverted book lands at **exactly break-even**: NET @spread/7.3 **-0.0028** [-0.0341, +0.0278], NET @8.5 **+0.0009**, "
  "against the same population's original at **-0.1662**. **Inverting recovers +0.1634 R/trade and lands on zero.**\n")
A("## 5. THE POOL IS FILL-CONDITIONED — a substrate defect this lane had to find to avoid reporting a fake inversion\n")
A("`path_final_r` (`src/research_infra/v4_timewarp_simulated_live_research_loop.py:60309-60310`):\n")
A("```python\nfill_status = str(oracle.get(\"fill_status\") or \"\")\nif not fill_status.startswith(\"filled\"):\n    return None, \"not_filled_no_trade\", None\n```\n")
A("`opportunity_net_proxy_r` is therefore `None` for any candidate whose entry was never traded, and the pool filter "
  "(w0-dictionary D3) requires `opportunity_net_proxy_r is not None`. **Every row in the 27,658-row pool is a row whose "
  "limit filled.** Empirical signature on the 7,949 resting rows: P(price reaches the level) = **99.9623%** against a "
  "distance-matched symmetric control of **36.82%**, and the touch hazard over `mkt_r>2` rises **6.909% -> 100.000%** in "
  "the final 10-bar block (140 at risk, **140** touched, **0 of 2,171 never touched**). A hazard cannot be 100%; a "
  "filter can.\n")
A(tb(["mkt_r bucket","n","P(reach level)","P(symmetric control)","magnet ratio","median bars to level","R after the fill","inv at-market"],
  [[b["label"], b["n"], f"{b['p_reach_level']:.2%}", f"{b['p_symmetric_control']:.2%}", f"{b['magnet_ratio']:.2f}x",
    b["median_bars_to_level"], f"{b['orig_after_fill']:+.4f}", f"{b['inv_atm']:+.4f}"] for b in MG["buckets"]]))
A("Consequence: **the resting-limit inversion (+0.7546 info, born_resting) is NOT bankable** — it is measured on a "
  "sample selected on the very price move it claims to predict. It is reported here so no later lane rediscovers it "
  "and believes it. The clean at-limit cell is unaffected: those fills are instantaneous.\n")
A("## 6. CQ / current_breaker_re_entry — INDEPENDENT, zero overlap\n")
A(f"CQ's 4,263 inverted-breaker trades join this lane's base on `source_candidate_id` with **0 unmatched**. Their born "
  f"mix is `{SC['cq']['born_mix']}` — **{SC['cq']['cq_rows_in_clean_population']} rows** ({SC['cq']['at_limit_share']:.2%}) "
  f"sit in this lane's clean population, and `current_breaker_re_entry` contributes **{SC['breaker_in_clean']}** rows to it. "
  f"On CQ's own past-stop rows the inverse is **+{SC['cq']['inv_blind_on_cq_past_stop']:.4f} R blind**, "
  f"**{SC['cq']['inv_honest_on_cq_past_stop']:+.4f} R** with the fill required, and "
  f"**{SC['cq']['inv_atm_on_cq_past_stop']:+.4f} R** at market. CQ's +11.9 R/trade is the fill-blind convention; at "
  f"market or with an honest fill it is zero. **Two different phenomena, no shared rows.**\n")
A("Corroborating: the honest inverse of the whole `current_breaker_re_entry` family is **-0.1106 R/trade**, not positive "
  "(`L7_SWEEP_V1.json` population ALL, `dims=family`).\n")
A("## 7. Stability within January\n")
A(tb(["split","n","orig@mkt","inv@mkt","INFO"],
  [[t["split"], t["n"], f"{t['orig']:+.4f}", f"{t['inv']:+.4f}", f"{t['info']:+.4f}"] for t in SC["stability"]["splits"]]))
A(f"Daily `info` is positive on **{SC['stability']['days_positive']} of {SC['stability']['days_total']}** trading days.\n")
A("## 8. Per family and per symbol (clean population)\n")
A(tb(["family","n","orig@mkt","orig win","inv@mkt","inv win","INFO","95% lo","BH q"],
  [[c["key"], c["n"], f"{c['orig_atm']:+.4f}", f"{c['orig_win']:.1%}", f"{c['inv_atm']:+.4f}", f"{c['inv_win']:.1%}",
    f"{c['info']:+.4f}", f"{(c.get('boot') or {}).get('lo',float('nan')):+.4f}", f"{c.get('bh_q',float('nan')):.3f}"]
   for c in sorted([x for x in CE["CLEAN_at_limit"]["cells"] if x["dims"]=="family"], key=lambda x:-x["info"])]))
A(tb(["symbol","n","median d %","orig@mkt","orig win","inv@mkt","INFO"],
  [[t["symbol"], t["n"], f"{t['rd_pct_med']:.4f}", f"{t['orig']:+.4f}", f"{t['orig_win']:.1%}", f"{t['inv']:+.4f}", f"{t['info']:+.4f}"]
   for t in SC["by_symbol"]]))
A("**23 of 24 symbols are inverted.** Only `XAGUSD` is not (-0.0414, and its at-market original is the book's best at "
  "+0.0877). `USDCHF` (+0.0229) and `USDJPY` (+0.0165) are the only other positive originals.\n")
A("## 9. The ranked inversion table (lane item 1)\n")
A("Cells whose win rate sits below breakeven, ranked by `(breakeven - actual) * n`, on the honest at-market basis over "
  f"the clean population. Full list of **{CE['CLEAN_at_limit']['n_cells']}** cells in `L7_CELLS_V1.json`; "
  f"**{sum(1 for c in CE['CLEAN_at_limit']['cells'] if c['info']>0)}** of them ({sum(1 for c in CE['CLEAN_at_limit']['cells'] if c['info']>0)/CE['CLEAN_at_limit']['n_cells']:.1%}) have positive `info`, "
  "rising to **85.7%** among cells with n>=500 — the inversion is a property of the book, not of a cell selection.\n")
A(tb(["dims","key","n","orig@mkt","orig win","inv@mkt","inv win","INFO","95% lo","total R","BH q"],
  [[c["dims"], c["key"], c["n"], f"{c['orig_atm']:+.3f}", f"{c['orig_win']:.1%}", f"{c['inv_atm']:+.3f}", f"{c['inv_win']:.1%}",
    f"{c['info']:+.4f}", f"{(c.get('boot') or {}).get('lo',float('nan')):+.4f}", f"{c['info_total_R']:+.1f}", f"{c.get('bh_q',float('nan')):.3f}"]
   for c in CE["CLEAN_at_limit"]["cells"][:30]]))
A("### Cells where the ORIGINAL direction is right (n>=60)\n")
A(tb(["dims","key","n","orig@mkt","inv@mkt","INFO","orig win"],
  [[c["dims"], c["key"], c["n"], f"{c['orig_atm']:+.3f}", f"{c['inv_atm']:+.3f}", f"{c['info']:+.4f}", f"{c['orig_win']:.1%}"]
   for c in sorted([x for x in CE["CLEAN_at_limit"]["cells"] if x["n"]>=60], key=lambda x:x["info"])[:20]]))
A("## 10. Worked candidate ids\n")
A("Most-inverted clean cell `structural_distance_extreme|off_configured_session` (orig -0.189 / inv +0.261, n=1,225): "
  "`broadorigin_fcdaf6daac7daeed7249b9c4` (2026-01-02T01:30:00Z GBPUSD SHORT, orig -1.00 / inv +2.00), "
  "`broadorigin_d61846c1cd1b2dc31f3c4f07` (01-02T01:45Z GBPUSD SHORT), "
  "`broadorigin_52b8434e5a016a2f34fad03a` (01-02T02:00Z GBPUSD SHORT), "
  "`broadorigin_caaef4d7a6d8f633fb753399` (01-02T03:00Z XAUUSD SHORT).\n\n"
  "London cell where the ORIGINAL works `liquidity_sweep_reclaim|london` (orig +0.077, n=913): "
  "`broadorigin_006787a804b98cca4e56a79b` (01-02T07:00Z GBPJPY SHORT, orig +2.00 / inv -1.00), "
  "`broadorigin_b20fb9fff0ebd3efc2a061d0` (01-02T07:15Z NZDUSD LONG), "
  "`broadorigin_71bf45689cc0b8082a9cb594` (01-02T07:45Z AUDUSD LONG).\n")
A("## 11. Caveats, stated plainly\n")
A("- **One month.** January 2026 only. March has no diagnostic pool with an M1 path sidecar in any worktree, and "
  "February's pool ships no path sidecar and no market anchor, so neither can test travel from here. That is the "
  "single highest-value next test.\n"
  "- **Multiplicity.** 2,640 clean cells were enumerated. BH q is reported for the 140 bootstrapped ones. The "
  "**population-level** claim (info +0.0764 on all 14,911 clean rows) is a single pre-specified test, not a cell pick.\n"
  "- **Pseudo-replication.** First-emission-only gives info +0.0746 [+0.0522, +0.0990] — the finding does not depend on "
  "the 24.39% repeats.\n"
  "- **2-hour horizon.** Every number is capped at 120 M1 bars. A directional edge that needs longer is invisible here.\n"
  "- **The inversion is not a trade, and the latency ladder is the reason.** It is spent in one to two minutes, it is "
  "one spread wide, and it lands at break-even net of even an 8.5x-corrected spread. It is a diagnosis of where the "
  "sign and the entry price are wrong, not a strategy.\n"
  "- **Not tested here:** whether entering these seven families one to two minutes after the trigger bar's close "
  "recovers the 0.0764 R directly (the latency ladder measures the *signal decaying*, not a *delayed-entry policy* — "
  "at delay 2 the original's own at-market return is -0.0085 vs -0.0596 at delay 0, which is +0.0511 R/trade and is "
  "the single cheapest thing in this receipt to test next). The 30-60 minute rungs turning significant again is "
  "unexplained and worth a lane.\n")
A("## 12. Artifacts\n")
for f in ["l7_BASE.jsonl.gz","L7_SWEEP_V1.json","L7_CELLS_V1.json","L7_DECOMP_V1.json","L7_CONTROLS_V1.json",
          "L7_MECH_V1.json","L7_NET_V1.json","L7_STAB_CQ_V1.json","L7_WIDE3_V1.json","L7_ZEROSPREAD_V1.json",
          "L7_MAGNET_V1.json","L7_DELAY_V2.json","L7_SCALE_V1.json","L7_DELAYREPAIR_V1.json","L7_RESULT.json",
          "l7_build_base.py","l7_sweep.py","l7_decomp.py","l7_controls.py","l7_magnet.py","l7_mech.py","l7_net.py",
          "l7_stability_cq.py","l7_delay.py","l7_delayrepair.py","l7_receipt.py"]:
    A(f"- `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/{f}`")
open(os.path.join(H, "L7_RESULT.md"), "w").write("\n".join(M))
print("wrote L7_RESULT.md", os.path.getsize(os.path.join(H,"L7_RESULT.md")), "bytes")
print("wrote L7_RESULT.json", os.path.getsize(os.path.join(H,"L7_RESULT.json")), "bytes")
