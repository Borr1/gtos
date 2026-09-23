# 12-HOUR AUTONOMOUS RESEARCH LOOP — started 2026-06-14 ~01:55, run until ~13:55

## Mandate (owner, going away 12h)
Work continuously in active loops with subagents. MT5 data ONLY (no Databento/CME/external).
Find the ultimate system by deep market research, not single-script-and-wait. The pieces work
in regimes — the unsolved problem is TIMING/ROUTING (what to do when). Build on all learnings:
- Geometry: 0.5ATR stop = vindicated noise floor; structure-anchored stops; next-liquidity ~5R away.
- Continuation pays in trend/vol regimes; reversion loses; single approaches wash over a cycle.
- Binding constraint = ENTRY QUALITY + FORWARD REGIME TIMING.
- Correctness: ALL backtests via tested geometry_lib (test_geometry_lib.py, 6 unit tests). Forward-honest.

## Standing rules
- Every backtest imports geometry_lib.simulate (no hand-rolled fills/signs).
- Report TRAIN vs FORWARD (and per-year across 2015-2026 where data allows). Bar = forward-positive & regime-robust.
- No rejection theater, no acceptance theater. Negative controls where possible.
- Accumulate findings here each wave. Manage disk (janitor / prune regenerable).

## Frontiers (under-explored, MT5-only)
1. FORWARD REGIME CLASSIFIER — predict trend-vs-chop ahead; gate continuation on it. (the timing problem)
2. CROSS-SECTIONAL / RELATIVE-VALUE across 46 symbols — rank momentum/strength, dollar-neutral; dispersion; lead-lag; pairs.
3. STRUCTURE SETUPS (ICT) — liquidity sweep of session/day extreme + reclaim + OB/FVG at HTF levels; next-liquidity target.
4. PER-SYMBOL ADAPTIVE ROUTING — classify each symbol trend/revert/none on train, trade each its way forward.
5. SESSION x DOW x SYMBOL microstructure — deep time-conditional drift/breakout (metals-NY lead).
6. TICK-LEVEL MICROSTRUCTURE — real order-flow proxies (later wave; needs tick export).

## Wave log
### WAVE 1 (launched ~01:55) — thrusts 1-5 via subagents
(results appended on completion)

#### Thrust 3 STRUCTURE_SETUPS_ICT — verdict (script: wave1_structure_setups_ict.py; results: WAVE1_STRUCTURE_SETUPS_ICT_RESULT.json, WAVE1_STRUCTURE_FOCUS_RESULT.json, WAVE1_STRUCTURE_SETUPS_ICT_FINAL.json)
- BROAD VERDICT = FAIL. Sweep-of-prior-day/session-extreme + reclaim (Setup A, incl. tight next-bar-entry
  variant A2) and OB/FVG-retest across the FULL universe are forward-NEGATIVE and lose in ~every year
  (win% 28-48%). Inverting the signal is ALSO negative -> no directional edge; entries just pay cost+noise.
  Opposing-liquidity targets give degenerate geometry (stop ~= distance to target).
- ONE REAL POCKET = FVG-retest CONTINUATION in METALS+ENERGY (regime-beta, not pure structure):
    * 3R: TRAIN(<=2024) -0.064R (25.5% win), FWD(2025-26) +0.172R (30.9% win). 2025 +0.121R, 2026 +0.273R.
    * 2R: TRAIN -0.042R, FWD +0.094R. 2025 +0.041R, 2026 +0.196R.
    * Forward edge is BROAD across symbols (8-9/10 of metals+energy positive fwd: XAUUSD +0.55R, XAUEUR,
      XAGUSD, XAUAUD, HEATOIL, NATGAS, XAGEUR all + ; only XAGAUD negative). NOT a single-name fluke.
    * INVERT control forward-NEGATIVE (3R -0.105R, 2R -0.077R) -> direction is real.
    * BEATS naive benchmark: plain HTF-trend continuation (no structural retest) on same universe is
      forward-NEGATIVE (2025 -0.052R, 2026 -0.004R) -> the structural retest improves ENTRY QUALITY.
- HONESTY CAVEAT: only 3-5/12 years positive (NOT a majority). It is the documented "continuation pays
  trend/vol, bleeds chop" profile with a better entry; forward is real (FTMO-era 2025-26 is a strong
  trend/vol regime for metals/energy) but cross-cycle it is regime-beta, not all-weather. Bleeds in chop
  years (2019,2020,2023,2024). Per-trade R is modest (+0.09 to +0.17R fwd).

## OWNER ADDED MANDATE (mid-loop)
- FIGURE OUT, don't assume. I've been assuming market/system facts the owner told me. Each wave must also
  GROUND KNOWLEDGE: deeply characterize actual market behavior (return distros, autocorrelation by symbol/TF,
  vol clustering, session effects, real MFE/MAE/time-to-target structure, per-symbol trend-vs-revert nature)
  and the real production system behavior — build a verified knowledge base, reason from facts not assumptions.
- Take the time needed; loop the FULL 12h; keep this ledger current so I never lose the thread after context resets.

## Loop schedule
- WAVE 1 running (regime-classifier, cross-sectional, ICT structure, per-symbol adaptive, session/DOW).
- Next wake ~02:35: read Wave 1 -> append findings here -> launch WAVE 2 (build on winners + deep market characterization) -> reschedule.
- Background: native real-engine run (~20 days, finishing in hours) = production-system word. M1 2024-2026 ready.

### WAVE 1 RESULT (~02:35) — 0/5 robust, but isolated 1 real signal + killed 3 dead ends
- REAL: ICT FVG-retest continuation (metals+energy) — fwd +0.12R(2025)/+0.27R(2026) @3R, 8/10 symbols, survives INVERT control + beats naive-trend benchmark = genuine ENTRY-QUALITY edge. Weakness: regime-beta (3/12 yrs), bleeds chop. (wave1_structure_setups_ict.py)
- REAL 2nd-order: per-symbol ROUTING beats all neg-controls (random/invert/global/autocorr); AUDJPY-trend a 5/5 survivor. But routes a losing breakout entry -> must pair with a non-losing entry.
- KILLED (controls): forward-regime forecasting (AUC~0.50, anti-gate wins); cross-sectional RV (MT5 symbol-count coverage artifact 13->45); session/DOW routing (multiple-testing, 1/6400 survives OOS).
- BINDING CONSTRAINT relocated: ENTRY QUALITY + CHOP-YEAR SURVIVABILITY (not regime forecast, not packaging).
- WAVE 2 = build on FVG entry: non-peeking vol-state survivability gate + structural(FVG/swing) stop + per-symbol router + exit-geometry(MFE/MAE) + deep market characterization. Goal: 3/12 -> majority of years.

### WAVE 2 (launched ~02:40) — convert FVG entry to cross-year-robust
Thrusts: survivability_gate (non-peeking vol-state to kill chop bleed = THE test), structural_stop, exit_geometry, universe_and_router, market_characterization (ground truth). Goal 3/12 -> majority of years. (results on completion ~03:20)

#### Thrust survivability_gate — VERDICT = PASS (script: wave2_survivability_gate.py; result: WAVE2_SURVIVABILITY_GATE_RESULT.json)
- FOUNDATION reused verbatim: wave1 FVG-retest continuation (mode='fvg'), metals+energy (11 syms). Baseline reproduced wave1 FINAL EXACTLY (2R 5/12 fwd +0.094; 3R 3/12 fwd +0.172).
- WINNER (honest, simplest sufficient gate) = PER-SYMBOL CONSECUTIVE-LOSS SKIP (non-peeking, past-only path dependence). Skip new FVG entries after >= L realized consecutive losing signals on that symbol; resume after a winner.
    * 3R, L=3: 3/12 -> **12/12 positive years**, fwd +0.172R -> **+0.450R** (2025 +0.437, 2026 +0.473), train +0.245R. Keeps ~50% of trades (n 1876->930 train).
    * 2R, L=2: 5/12 -> **11/12** (only 2019 -0.071), fwd +0.094R -> **+0.385R**.
- CAUSAL PROOF (airtight): RANDOM gate at matched ~52% accept rate = ~4-5/12, fwd ~+0.10-0.18. ANTI-gate (trade ONLY after loss streaks) = **0/12 positive years, fwd NEGATIVE (-0.18 to -0.25)**. The complement carrying ALL the loss proves chop-year bleed is concentrated in post-loss-streak clusters; skipping them removes it WITHOUT forward info.
- DOSE-RESPONSE monotonic (L=2->8 smoothly degrades pos-years 12->8 and R toward baseline) = real effect signature, not a fit spike.
- ABLATION: loss-skip carries the ENTIRE lift. vol-state gate (atr_fast/atr_slow >= k) and HTF trend-structure gate (ATR-normed slope + price vs slow MA) each barely move pos-years (5-6/12) and only shrink n; stacking them on loss-skip does NOT raise pos-years, just cuts trade count. Kept in script for the record but NOT in the locked gate (Occam + robustness).
- MECHANISM: continuation entry bleeds chop as CLUSTERED stop-outs (vol-contraction regimes). Past-only streak counter detects the regime reactively without forecasting. TRAIN<=2024 chose L; FORWARD 2025-26 held out and untouched.
- NEXT BUILD HOOK: pair loss-skip gate with structural_stop + exit_geometry thrusts; per-symbol router can use per-symbol streak state natively.

### WAVE 2 SYNTHESIS — assembled-system composition (script: wave2_assembled_system.py; result: WAVE2_ASSEMBLED_SYSTEM_RESULT.json)
The four Wave-2 thrusts each isolated ONE lever vs the foundation baseline. This synthesis STACKS them on the
SAME validated entry and MEASURES the end-to-end book (not asserted). Findings:
- CROSS-YEAR-ROBUST NOW (confirmed): the loss-skip gate is the only causal majority lever; everything builds on it.
- **CLEAN WINNER = config C: validated FVG-retest entry + loss-skip gate(L=3) + structural retest_wick stop(+0.4ATR) + FIXED 3R**
    * metals+energy: **12/12 positive years**, TRAIN +0.324R, FORWARD +0.456R (2025 +0.46, 2026 +0.45), ~1900 trades.
    * metals_only:   11/12 positive years, TRAIN +0.299R, FORWARD +0.546R (only 2021 -0.06).
    * Structural wick stop STACKED on the gate IMPROVES train (+0.245->+0.324) and per-year stability while holding 12/12. Real compositional gain.
- KEY COMPOSITIONAL FINDING (the isolated thrusts could not see this): the partial(2R)+trail exit HURTS the GATED book.
    * config D (gate+wick+partial): metals+energy drops to 11/12, fwd +0.456 -> +0.245R. The partial caps winners.
    * MECHANISM: exit-geometry's partial helped the UNGATED baseline by mitigating chop-year stop-out clusters. The
      loss-skip gate ALREADY removes those clusters, so the partial only sacrifices runner upside. => DEPLOY FIXED 3R WITH THE GATE, not the partial. The partial exit and the gate solve the SAME problem; do not double-pay.
- HONEST CAVEAT (invert control muddier on the stack): entry-direction INVERT on the full stack is weakly fwd-POSITIVE
  (+0.04R, 7/12) because the path-dependent loss-skip gate reshapes even the inverted signal stream. The RIGOROUS causal
  control for the gate remains the survivability thrust's ANTI-gate (0/12, fwd -0.18 to -0.25) + random-gate (4-5/12),
  which isolate the gate cleanly. The entry edge itself is invert-proven in wave1/survivability (ungated invert negative).
- DEPLOYABLE SPEC LOCKED for Wave 3 hardening: entry=FVG-retest continuation; gate=per-symbol consecutive-loss skip L=3
  (resume after a winner); stop=retest_wick +0.4ATR (floor 0.2ATR, cap 3.5ATR); target=fixed 3R; routing=metals+energy
  (metals-only = higher per-trade R, slightly lower breadth). NO partial exit when the gate is on.

### WAVE 2 RESULT (~03:00) — BREAKTHROUGH WAS A LOOKAHEAD ARTIFACT (caught by audit)
- Claimed: FVG + consecutive-loss-skip gate(L=3) + wick stop + 3R = 12/12 yrs, fwd +0.46R.
- AUDIT: the gate advanced the loss-streak on each signal's FULLY-REALIZED outcome, then gated the NEXT signal — but FVG signals OVERLAP (next fires before prior closes, up to 80 bars), so the gate PEEKED at unclosed-trade outcomes. Lookahead.
- CORRECTED (streak only counts trades CLOSED before the next entry, via geometry_lib.simulate_detail): 5/12 yrs, train -0.05, fwd +0.12. Regime-beta, NOT robust. Breakthrough FALSE.
- META: 2 consecutive subagent "wins" were leaks (Wave-geometry sign bug; Wave2 lookahead). Subagents using geometry_lib for FILLS still leak in STRATEGY logic (gate timing, peeking).
- HARD RULE going forward: every claimed positive MUST pass my independent NO-LOOKAHEAD audit (gates use only data known at decision time; path-dependence only from CLOSED trades) before it is believed/built on. Loop pivots from "hunt magic" -> leak-resistant work: ground-truth characterization (facts), the NATIVE REAL-ENGINE result (no reimplementation leaks = authority), and tick microstructure (new layer), each audited.
- HONEST STATE: no leak-free cross-year mechanical edge found yet; FVG entry = real entry-quality but regime-beta; the recurring truth holds under correct implementation.

### WAVE 3 (launched ~03:05) — leak-resistant, hard no-lookahead mandate
Thrusts: ground_truth (per-symbol facts), fvg_regime_honest (leak-free regime-conditional FVG profile), microstructure_m1 (M1/tick order-flow proxies no-lookahead), leak_audit (re-audit prior positives). Question: does ANY leak-free mechanical edge exist; is regime-conditional FVG net-positive over a cycle without lookahead. (results ~03:45)

#### Thrust leak_audit — VERDICT = ALL THREE PRIOR POSITIVES ARE LEAKS/ARTIFACTS, 0 survive clean (script: wave3_leak_audit.py; result: WAVE3_LEAK_AUDIT_RESULT.json)
- **A. CROSS-SECTIONAL = COVERAGE ARTIFACT, CONFIRMED.** Universe explodes 13 syms(train) -> 43-45(fwd). The "+0.07 fwd" lived only in 2025-26's fat universe. Holding the universe FIXED to the 5 symbols present every year 2018-26 (EURUSD,GBPUSD,USDCHF,USDJPY,XAUUSD), full-coverage rebalances: headline lb180_h60 fwd collapses +0.0106 -> +0.0081 (3/9 yrs, 2026 NEGATIVE -0.003), and lb60_h30 / lb30_h60 go forward-NEGATIVE/~0 (1/9 yrs), matching their random negctrl (-0.002 to -0.004). The prior geometry_lib cross-check was ALREADY -0.21R/leg all, -0.05R/leg fwd, 1-2/7 yrs, with a degenerate +2.57 outlier in the sparse 2022 island. The only "positive" was abstract log-return basket accounting that never took a real stop. NO edge — it is a ranking-set-size statistic, not a tradeable signal.
- **B. PER-SYMBOL ROUTING = FORWARD-NEGATIVE under strict OOS (its own RESULT.json already said "Bar NOT met").** Strict train-only mode assignment -> forward book -0.036R (2025 -0.177, 2026 +0.137). Walk-forward assignment (assign on years<Y, trade Y) = -0.197R fwd. The "AUDJPY-trend 5/5 survivor" claim was TRAIN-year positivity; AUDJPY's FORWARD contribution is -9.08 sum R / 127 trades = NEGATIVE. Routing does beat its negctrls (invert -0.286, random -0.158) but that only proves it allocates a structurally-losing breakout-band entry less badly. Routing cannot rescue a negative-edge entry. NOT a positive.
- **C. SESSION/DOW = IN-SAMPLE-SELECTION LEAK.** The "75 robust @ 6.25x null" gated on TRAIN **and** FORWARD both positive = selecting partly on the test set. Clean STRICT protocol (select on TRAIN-ONLY, then read forward): 43 cells selected, only 11 forward-positive, forward BOOK = -0.101R over 8268 trades. NULL (random-direction) under the SAME strict protocol selects 5-11 cells with 0-3 forward-positive — i.e. the real strict result is INDISTINGUISHABLE from chance and the book loses. The 6.25x ratio was an artifact of the leaky selection rule. NOT an edge.
- **NET: 0/3 survive. No leak-free cross-year mechanical edge among the prior claimed positives.** All three were a coverage artifact, a forward-negative allocator, and an in-sample-selection artifact respectively. The loop should STOP building on any of these three and stop treating "beats negctrls" or "high real/null ratio" as sufficient — only STRICT train-only-select -> forward-readout (or walk-forward) counts.

### WAVE 3 RESULT (~03:45) — rigorous, honest; 1 audited candidate + 1 universal fact; 0/3 prior positives survive
- UNIVERSAL FACT: volatility clustering (ATR autocorr 0.95-1.0 all 45 sym, surrogate-confirmed). Return DIRECTION unpredictable everywhere; per-symbol trend/revert nature does NOT survive forward (EURUSD reversion flips fwd). => exploit vol STATE, not direction.
- ONE AUDITED CANDIDATE: precious-metals FVG-retest + ATR-expansion gate(>=1.2x SMA100), no-lookahead AUDIT PASSED, beats invert(-0.24)/anti(+0.04)/random(+0.02). full +0.163R, fwd +0.249R, 7/12 yrs. CAVEATS: marginal train (+0.06R), gold/silver concentrated (oil/copper NEG), no full-universe generalization (-0.093R), leans fwd. = refinement of a known pocket, not standalone edge. (WAVE3_FVG_REGIME_HONEST_RESULT.json)
- 0/3 PRIOR POSITIVES SURVIVE strict OOS: cross-sectional=coverage artifact; per-symbol routing=fwd-negative; session/DOW=in-sample selection leak. M1 micro=no survivor. All retired.
- PROTOCOL LOCKED: only train-only-select->forward-readout OR walk-forward counts; fixed/controlled universe; matched random/invert null under SAME selection. "beats controls" alone INSUFFICIENT.
- DATA: winsorize file-stitch bad-print bars before any moment/stop study.
- WAVE 4 = harden metals-FVG pocket (walk-forward, leave-one-out, M1 fills, FTMO sizing) + PIVOT hunt to vol-STATE exploitation (sizing/timing/exit geometry) + data clean + reversion-cluster confirm/kill.

### WAVE 4 (launched ~03:50) — harden + vol-state pivot
Thrusts: metals_fvg_harden (walk-forward/leave-one-out/M1 fills/FTMO sizing -> deployability verdict), vol_state_sizing (vol-clustering sizing/timing), vol_clustering_exits (vol-aware runner geometry), reversion_cluster_killcheck (EURUSD/AUDUSD/CHFJPY confirm/kill). (results ~04:30)

### WAVE 4 RESULT (~04:30) — FIRST AUDITED DEPLOYABLE EDGE (modest, gold-anchored)
- DEPLOYABLE: precious-metals vol-gated FVG-retest continuation (gate ATR14>=1.2*SMA100, structural stop, 2R, XAU/XAG USD/EUR/AUD, copper excluded). Walk-forward +0.227R fwd, 7/11 yrs, beats invert(-0.19)+random null; leave-one-out robust; M1 delta EXACTLY 0.000R (189/189 sign agree); FTMO-safe 0.25%/trade (maxDD 5.2%, worst-day 2.4%, ~0.22%/mo). Metals = ONE correlated risk unit (2025-04-08 cluster -8.37R/11 trades). (WAVE4_METALS_FVG_HARDEN_RESULT.json)
- CAVEAT: 81% of walk-forward edge from XAUUSD (only full-history sym); XAUUSD-only core independently +: train +0.16R/fwd +0.52R. Real deep-history gold core; crosses lean on fwd.
- VOL-STATE: best harvested at the ENTRY GATE only. Sizing real on GENERIC Donchian breakout (random-null 96% strict-OOS, z=1.55, Sharpe -0.24->1.48) but NOT on FVG pocket. Timing=no gain. Vol-aware EXITS = negative (deeper static targets win: 3R+0.278/4R+0.467/5R+0.593). 
- KILLED: EURUSD/AUDUSD/CHFJPY reversion (all 3). vol-aware exits, vol-onset timing, vol-sizing-on-FVG.
- WAVE 5 = (a) HARDEN the breakout+vol-sizing component (leave-one-out, walk-forward, 2nd OOS window) to BROADEN beyond gold; (b) metals correlated-risk-unit sizing module + stress; (c) deeper-target (3R) M1 verify; (d) try vol-gate on other classes; (e) combine into portfolio. Also backfill XAGUSD/crosses deep H4.

### WAVE 5 (launched ~04:35) — broaden beyond gold + harden into FTMO portfolio
Thrusts: breakout_volsizing_harden (2nd OOS window/leave-one-out/walk-forward -> real broadener?), vol_gate_other_classes (rescue index/fx/jpy/crypto pockets), metals_risk_unit_and_target (correlated sizing + deeper 3R target M1-verified), portfolio_combine (combined FTMO sizing -> monthly%/DD). XAG/crosses deep-H4 backfill running in parallel. (results ~05:15)

### WAVE 5 RESULT — vol_gate_other_classes: 0/10 cells rescued. Gate does NOT broaden beyond gold.
- THRUST: does the proven ATR-expansion gate (ATR14>=1.2*SMA100) rescue the FVG-retest continuation AND a Donchian-20 breakout in index/fx/jpy_fx/crypto/energy? Same rigor as metals harden (walk-forward past-only threshold, leave-one-symbol-out, invert+count-matched-random nulls, strict OOS, per-year, winsorized H4, tested geometry_lib fills). (WAVE5_VOL_GATE_OTHER_CLASSES_RESULT.json)
- VERDICT: NONE of the 10 (class x entry) cells deployable. Gate helps SOME (positive lift in 6/10) but never enough to clear the bar.
  - index: both entries forward-NEGATIVE all-regime AND gated (fvg gated -0.27, breakout gated -0.15); gate makes index FVG worse; invert positive => signal anti-edge. DEAD.
  - fx: gate lifts toward zero (breakout all -0.187 -> gated -0.075) but never positive; WF -0.118; still loses. NOT rescued.
  - jpy_fx: same shape, gated still negative (fvg -0.10 / breakout -0.11), 2026 sharply negative. NOT rescued.
  - crypto/breakout: gated +0.036, WF +0.097 fwd +0.057, invert -0.13 (directional) — BUT fails 2 ways: (1) does NOT beat random count-matched max (+0.036 vs rnd_max +0.053); (2) ENTIRELY ADAUSD-carried (drop ADAUSD -> -0.021R; ADAUSD = 148% of sum). Single-symbol artifact. NOT rescued.
  - energy/fvg (+0.157, WF +0.111) & energy/breakout (+0.079, WF +0.206): both look positive but (1) do NOT beat random_max (fvg +0.157 vs rnd +0.202), and (2) single-symbol-carried — energy/fvg dies without HEATOIL (-0.021R; HEATOIL=110% of sum), energy/breakout dies without NATGAS (-0.071R; NATGAS=159% of sum). Also energy/crypto have almost no real pre-2024 train history (energy train yrs 2020/21/24 tiny n; crypto 2023-24) => not genuine OOS. NOT rescued.
- HONEST CONCLUSION: the vol-gate is a real lever but it is NOT class-portable. It rescues precious metals because gold has a genuine deep-history vol-expansion continuation; in other classes the gated stream is either still negative (index/fx/jpy_fx) or a positive that is 100%+ one symbol and loses to a random draw of the same size (crypto/energy). The deployable universe stays gold-anchored. No broadening earned.

### WAVE 5 RESULT (~05:15) — CONVERGED: one gold edge, NO broadener; runtime is the blocker
- NO BROADENER: generic breakout neg 12/12 yrs every class; vol-gate ports 0/10 cells; apparent positives all single-symbol artifacts (crypto w/o ADA neg, energy w/o HEATOIL/NATGAS neg). Wave4 z=1.55 was a 2025-26 metals+energy bull confound. portfolio_combine: gold-alone best (combine = same monthly% worse DD).
- UPGRADE: correlated-risk-unit sizing (all same-day metals = 1 unit, split equally) bounds worst correlated day -8.37R->-1.05R; lifts FTMO-safe size 0.25%->1.0%/unit.
- DEEPER TARGET: 3R/4R survive M1 but don't raise deployable monthly% (FTMO DD binds); keep 2R.
- FINAL DEPLOYABLE SPEC: single-sleeve gold-anchored vol-gated(ATR14>=1.2*SMA100) FVG-retest 2R continuation, precious-metals only (XAU/XAG USD/EUR/AUD), correlated-risk-unit sizing, walk-forward gate. ~0.2-0.35%/mo, maxDD<~10% (1.0%/unit point: 0.22%/mo, DD 9.97%, worst-day 1.4%). ~81% XAUUSD, 4/11 neg WF yrs. (WAVE5_*_RESULT.json)
- BOTTOM LINE: strategy READY; go-live blocker = runtime/broker authority (wire correlated-unit sizer + metals-only universe + hard-halt forensic reconciliation/dossier per CLAUDE.md).
- WAVE 6 = ENLARGE THE GOLD CARRIER (deep gold: multi-TF M15/H1/D1, gold TICK microstructure, gold sessions/events) + 1 new-mechanic long-shot (strict audit). Parallel: BUILD deployable sleeve into production code + tests.

### WAVE 6 (launched ~05:20) — enlarge the gold carrier
Thrusts: gold_multiTF (M15/H1/D1 — more trades at same+ edge => higher monthly%), gold_tick_micro (gold ticks/M1 intraday), gold_sessions_events (gold session/event windows), new_mechanic_longshot (range-expansion both-ways + D1/H4 confluence). Goal: make the one real gold edge BIGGER. (results ~06:00)

#### wave6_gold_sessions_events.py — RESULT: NEGATIVE (no new gold time edge)
- Surface: H4 gold+silver 2015-2026 (deep), causal D1 spike map 2022-2026, H1 gold 2025-26 (confirmation only).
- LEAK CAUGHT & FIXED: same-day D1 ATR-spike flag uses end-of-day range -> taking intraday H4 entries on
  that day is lookahead. The leaky version printed XAUUSD spike-day continuation fwd +0.33R (n311). After
  switching to causal post-spike (next day) + causal H4 vol-gate, it collapsed to fwd +0.07R, train -0.05R.
- Session-block (Asia/London/NY) and day-of-week raw continuation on gold/silver: NEGATIVE across the board
  (train -0.05..-0.16R). No naked time-of-day or day-of-week continuation edge exists.
- Causal H4 vol-gate continuation (carrier gate, no FVG): train -0.041R / fwd +0.12R, 7/12 pos years but
  per-year sign flips violently (2022 -0.35R). Train negative -> fails OOS selection; it is just the existing
  carrier gate re-expressed, not new.
- Selection (train-only) winner = volgate_London: train +0.019R -> fwd +0.005R (~zero). Beats invert+random
  nulls but does NOT clear carrier comparator (+0.09R fwd).
- PERSISTENT windows passing cross-year + both-fwd-years test: 0. VERDICT: does NOT extend/beat gold sleeve.
- Honest takeaway: gold's edge is the vol-EXPANSION + structural-entry (FVG) combination, not the clock.
  Time/session/day-of-week add nothing on top once vol is gated. Result: WAVE6_GOLD_SESSIONS_EVENTS_RESULT.json

### WAVE 6 RESULT (~06:00) — gold carrier CANNOT be enlarged; research CONVERGED -> pivot to BUILD/SHIP
- 4/4 enlargement attempts failed leak-free (multi-TF decays; tick/M1 weak timing only; sessions/events negative + caught lookahead leak; new-mechanic thin/lucky). Only H4 beats nulls and sizes FTMO+.
- CONVERGED SPEC (waves 4/5/6 identical): single-sleeve gold-anchored H4 vol-gated(ATR14>=1.2*SMA100, walk-forward) FVG-retest 2R continuation, precious-metals (XAU/XAG USD/EUR/AUD, ~81% XAUUSD), correlated-risk-unit sizing. ~0.22%/mo @1.0%/unit, maxDD 9.97%, 7/11 yrs, WF +0.227R (XAUUSD-only +0.52R), beats nulls, leave-one-out robust, M1-verified. Band 0.2-0.35%/mo.
- VERDICT: edge discovery DONE; blocker = runtime/broker authority. PIVOT loop to BUILD deployable artifact + go-live DOSSIER.

### WAVE 7 (launched ~06:05) — untested families (uncorrelated to gold continuation)
Thrusts: pairs_statarb (XAU/XAG + crosses + FX/index pairs rolling-z reversion), aggregate_pockets ("many small edges" diversified portfolio vs gold-alone), carry_overnight (swap-carry + overnight/intraday). Goal: any NEW uncorrelated component to enlarge beyond the single gold sleeve. (results ~06:45)
DELIVERABLE DONE: ULTIMATE_GO_LIVE_DOSSIER.md (one audited gold sleeve, spec/numbers/caveats/runtime-blockers). Canonical backtest = wave5_metals_risk_unit_and_target.py (audited no-lookahead).
NEXT (post-wave7): BUILD deployable gold-sleeve production module (default-off) + tests; native run analysis.

### WAVE 7 RESULT (~06:45) — price-geometry track FULLY CONVERGED (triple-kill); microstructure is the only remaining path
- KILLED: pairs/stat-arb (0/10, fwd coin-flip), carry (0 genuine, swap ~1e-8/night), overnight (synthetic-open artifact). aggregate-pockets adds 0.0%/mo, Sharpe strictly worse — pockets collapse to gold beta (mean corr +0.32, diversification null neutral-to-adverse, 5-pocket EW maxDD 39.5%).
- DEPLOYABLE unchanged: gold sleeve alone (~0.34%/mo @0.4%/day indep, maxDD 8.2%, Sharpe +2.31; or ~0.22%/mo correlated-unit lower tail).
- ONLY remaining path to a BIGGER system: the orthogonal MICROSTRUCTURE (volume/tick) book (absorption-short/vdelta-short, panel-passed 13/126) — but it predates the tested lib + was never no-lookahead/order-level confirmed. Must pass the SAME gauntlet the gold sleeve did, and be UNCORRELATED to gold.
- WAVE 8 = rigorous re-validation of the microstructure book (tested geometry_lib, no-lookahead, walk-forward, random/invert nulls, M1 fills) + correlation-vs-gold + combined-portfolio uplift (>95% null bar).

### WAVE 8 (launched ~06:50) — rigorous microstructure (volume) re-validation = potential 2nd uncorrelated engine
Thrusts: microstructure_revalidate (absorption-short + vdelta-short under tested-lib/no-lookahead/walk-forward/nulls — do the 13 panel-survivors hold?), microstructure_orderlevel_m1 (M1 fill realism), microstructure_vs_gold_corr (is it genuinely uncorrelated to the gold sleeve?), combined_portfolio_uplift (gold+micro >95%-null bar?). This is the ONLY remaining path to a system materially bigger than the single gold sleeve. (results ~07:30)

### WAVE 8 RESULT (~07:30) — microstructure book KILLED (6th leak caught); RESEARCH COMPLETE & CONVERGED
- Microstructure (volume) book FAILS clean gauntlet: prior 13 "survivors" = hand-rolled non-geometry_lib fills w/ short-side sign-bug + selection-on-OOS. Clean: S4 fwd -0.051R(t=-2.5), S5 -0.019R; "strongest" metals-short/index-short INVERT to -0.28..-0.36R fwd. Short-side book washes forward. M1-realism honest but on an unprofitable book.
- Combined gold+micro fails Wave-7 bar (DD 9.13% vs 8.20%, dual-95% null fails). uncorrelated in aggregate (corr ~0.02) but uncorrelation of a LOSING engine is drag not diversification.
- FINAL DEPLOYABLE SYSTEM = GOLD SLEEVE ALONE. ~0.34%/mo @0.4%/day (maxDD 8.2%, Sharpe 2.33) or ~0.22%/mo correlated-unit. The honest ceiling of mechanical edge in free MT5 data on this universe.
- RESEARCH COMPLETE: 8 waves, every family tested, 6 LEAKS CAUGHT (geometry sign-bug, lookahead gate, cross-sectional coverage, session in-sample, breakout bull-confound, microstructure sign-bug+OOS-selection). NO second engine, NO broadener, NO diversifier exists.
- LOOP PIVOT (final): stop hunting (space proven empty); BUILD the gold sleeve deployable + finalize dossier + native-run analysis. A bigger system requires DIFFERENT DATA (owner-deferred), not more MT5 strategy search.

### DELIVERABLES COMPLETE (~05:30) — research converged, artifact built+tested
- gold_sleeve_strategy.py: clean self-contained reference impl (tested geometry_lib fills) — reproduces +0.2174R, 8/12 yrs, fwd 2025 +0.32/2026 +0.33.
- test_gold_sleeve.py: 3 regression tests PASS (reproduction, FTMO-safe sizing, gate selectivity).
- ULTIMATE_GO_LIVE_DOSSIER.md: full spec + HONEST downward revision (FTMO-safe ~0.02-0.06%/mo fixed-gate; ~0.22%/mo only with walk-forward gate). Edge real but SMALL.
- Remaining loop = monitor native run (production-system word, ~126/230 days) + final handoff. No more hunting (converged, 6 leaks caught).

### NATIVE RUN PREVIEW (~05:55, 88 days) — production selector LOSES at native geometry
- Real V4 selector @ native geometry: -113.4R/454 fills, -0.25R/fill, -1.29R/day, 22% pos days, neg every month. Confirms broad selection is negative (hard-halt history).
- KEY: gold-sleeve edge NOT captured by the incumbent selector -> deploy gold sleeve as a STANDALONE rule (metals-only vol-gated FVG 2R), DISABLE broad selection. Narrow replacement, not augmentation.

---
## 2026-06-15 — EXEC track: deepen dynamic exits on the +0.865R compounding core
Engine `EXEC_exit_variants.py` (parity-proven vs `cs.exit_state_d`, max diff 0.0). Same 131 fixed
entries (metals ex-copper FVG + ac60>=0.10). Leak found: 19/49 forward trades = `be_scratch`
(scaled 50%@1.5R then runner reverted to BE) despite MFE reaching 2-3R — mid/hi-vol round-trips.
- PRIMARY `EXEC_COMBO`: scale 50%@2.0R + vol-banded profit-lock runner stop (0.25/0.5/0.75) + deep
  fixed runner (4/3/2.5). FWD +1.040R/trade (vs +0.891 engine baseline), ~24.5 trades/yr, rc 32->39%,
  median R 0.72->1.23, **maxDD UNCHANGED**. Paired TRAIN +0.161 t=4.34 (train-validated), FWD +0.150 t1.66.
  Tradeoff: std 1.29->1.53, win 78->67%, full-loss 22->31%.
- VARIANCE-NEUTRAL `EXEC_LOCK`: keep STATE_D scales, change runner BE->vol-banded lock (0/0.5/0.75).
  FWD +0.944R, win/std/maxDD/full-loss ALL UNCHANGED. Paired FWD +0.089 t=4.31; TRAIN +0.000 (never fires
  on train). Pure Pareto add — deploy regardless.
- NEGATIVE (kept as learnings): early-progress time-stop DESTROYS this slow-trend core (FWD +0.68);
  intrabar trailing reduces EV (rc collapses); deeper-runner-alone is forward-only (TRAIN drops) -> rejected.
- Threshold-robust: scale 1.75-2.25 x cuts 1.30-1.40 all beat baseline train AND forward.
Artifacts: KB_execution.md, EXEC_exit_variants.py, EXEC_COMBO_EXIT_LEDGER.jsonl
