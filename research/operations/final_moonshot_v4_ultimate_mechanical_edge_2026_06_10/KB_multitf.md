# KB — Multi-timeframe entry refinement (track: mtf_refine)

Goal: use H1/M15 to refine ENTRY timing on the commodity persistence setups. H4 sets
regime+setup; lower-TF times the entry. Better entries AND more frequency. Forward-validate
vs H4-only.

Owner of confirmed baseline: 6-metals (XAU/XAG x USD/EUR/AUD) FVG-retest continuation +
persistence gate ac60>=0.10 + ATR14>=1.2*SMA100 vol gate + STATE_D scale-out exit.
Reproduced exactly: **TRAIN<=2024 +0.298R (n=82), FORWARD 2025-26 +0.865R (n=49, 78% win)**.

## DATA AVAILABILITY (checked)
- XAUUSD: deep H1 (67k bars) + M15 (269k bars), **2015-2026** — `gold_multitf_d1h1_2015_2026/`, `gold_multitf_m15_2015_2026/`. Full-history holdout possible.
- XAGUSD: H1 forward-only 2025-06+ (`bridge_ftmo_htf_20250601_20260610/`).
- XAUEUR/XAGEUR/XAUAUD/XAGAUD: H1+M15 forward-only 2025-06+ (`bridge_ftmo_ext_htf_*`, `bridge_ftmo_ext_m15_*`).
- All metals: deep H4 2015-2026 (the baseline grid).
- Alignment gotcha: deep-H4 bars open at hours {0,4,8,12,16,20}; H1 export opens at hours 1-23. Do NOT assume index alignment — map by TIMESTAMP RANGE. H4 signal at bar open `t` is only actionable from `t+4h` (signal bar must close). `multitf_lib.first_ltf_index_after` does the leak-free binary search.

## WHAT WORKS — IMPROVEMENT #1 (promote): H1 better-fill, H4-width protective stop
(Now superseded by the H1->M15 CASCADE below, which beats it on both train and forward. Keep
this section for the mechanism + per-symbol + horizon evidence; deploy the cascade.)
**H1 better-fill, H4-width protective stop.**
Rule (LOCKED, chosen on TRAIN): after an audited H4 metals signal bar closes, wait up to
**12 H1 bars** for a pullback that improves the fill by **>= 1.0 * ATR_h1** vs the signal-bar
close (long: H1 low <= signal_close - 1.0*ATR_h1; short mirror). Enter at that pullback price
with the **SAME H4-width structural stop** (same risk unit). STATE_D scale-out exit on the H1
stream. If no qualifying pullback within 12 H1 bars, or no H1 coverage, **fall back to the
baseline H4 entry** (never skip a signal -> frequency preserved).

Result (same 49 forward trades, identical entry universe):
| metric | baseline H4 | mtf locked |
|---|---|---|
| TRAIN<=2024 R/t (n=82) | +0.298 | **+0.465** |
| FWD 2025-26 R/t (n=49) | +0.865 | **+1.129** |
| FWD win% | 77.6 | **85.7** |
| trades/yr (fwd) | ~33 | ~33 (unchanged) |

Per-year (mtf): 2018 +0.62, 2019 +0.24, 2021 +1.07, 2022 +1.45, 2024 +0.91, 2025 +1.25, 2026 +1.01.
Only 2016 (n=7) regressed (+0.13->-0.17). Both forward years improve.

### Why it works (mechanism, evidence-backed)
- The persistence regime (ac60>=0.10) = continuation with shallow pullbacks that resolve in
  your favor. Buying the dip inside the H4 window gets a better entry on the SAME move => more R.
- The H4-width stop is PROTECTIVE: it survives intrabar noise that tight stops do not (see
  failed variants). Keeping H4 width while lowering the long entry = same risk unit, more upside.
- Causal proof (apples-to-apples paired diff on rows that actually got the better fill):
  - FORWARD better-filled rows (n=24): base +0.403 -> mtf +0.940  = **+0.537R lift**.
  - TRAIN better-filled rows (n=33, deep-H1 XAUUSD/XAGUSD = true OOS pre-2025):
    base +0.126 -> mtf +0.542 = **+0.416R lift**. The lift is NOT forward-only.
- Lift concentrates in LOW vol (vr<1.35): fwd +1.80R, 96% win — exactly where shallow
  persistence pullbacks are cleanest.
- No single-symbol confound: ALL 6 symbols improve forward; the worst baseline symbol
  XAUAUD goes -0.004 -> +1.704R. The rule rescues the loser.
- Robustness: forward stays +1.11..+1.17R for H1_MAXBARS in {160,240,320,480} (insensitive).
  EVERY (W,mi) combo in {6,12,24} x {0.25,0.5,1.0} beat baseline on both train and forward
  (fwd +1.13..+1.19). mi monotonically lifts train; W barely matters above 6.
- Leak check: 0/66 entries before the H4 signal-bar close.
- Cost: metals 0.0459R applied via STATE_D (w1.cost_for).

Files: `mtf_refine_exp3.py` (param sweep), `mtf_refine_exp4.py` (forward dissection),
`MTF_REFINE_LOCKED_RESULT.json` (locked numbers), `multitf_lib.py` (leak-free primitives).

## WHAT WORKS — SECOND IMPROVEMENT (promote on top of the H1 rule): H1->M15 CASCADE FILL
The H1 better-fill above sometimes finds no qualifying pullback in its 12-bar window and falls
back to the worse H4 entry (20/49 forward signals fell back). Adding an M15 fallback LEG
recovers some of those: after the H1 window finds nothing, scan up to **48 M15 bars** for a
pullback **>=1.0*ATR_m15** better than the signal close; enter there with the SAME H4-width
stop, STATE_D exit on M15 (maxbars=1280 = 320h, wall-clock matched). Only THEN fall back to H4.

Cascade order: **H1 fill -> (if none) M15 fill -> (if none) H4 fallback.** Never skip a signal.

| metric | baseline H4 | H1-only locked | **H1->M15 cascade** |
|---|---|---|---|
| TRAIN<=2024 R/t (n=82) | +0.298 | +0.465 | **+0.482** |
| FWD 2025-26 R/t (n=49) | +0.865 | +1.129 | **+1.164** |
| FWD win% | 77.6 | 85.7 | **87.8** |
| trades/yr (fwd) | ~33 | ~33 | ~33 (unchanged) |

The cascade beats the H1-only rule on BOTH train and forward and lifts win 85.7->87.8. It fills
5 more forward signals via the M15 leg (fwd fill src: 20 H4, 24 H1, **5 M15**), all positive
contributions. Per-year: it improves 2024 (+0.91->+1.02), 2025 (+1.25->+1.32), 2020 (+0.005->
+0.025), and NEVER regresses vs H1-only. XAGEUR forward goes +1.05->+1.23.

### Why M15 is a FALLBACK leg, not the primary timer (key mechanism)
- M15 as the PRIMARY fill (EXP7) beats baseline forward (+1.02..+1.08R) and train (+0.27..
  +0.46) on every (W,mi) combo with 0 leaks, BUT it does NOT beat the H1-only rule (best M15
  primary fwd +1.072 vs H1 +1.129). M15 fills MORE signals/earlier (fewer fallbacks: 18 vs 52)
  but those earlier/shallower M15-timed fills convert to slightly LOWER EV.
  **Learning: H1 is the sweet spot for the better-fill timer — wait for the H1-resolution
  pullback. M15 only earns its keep on signals where H1 found nothing (it catches a finer
  pullback that H1's coarser bars stepped over).**

### Causal proof the better-fill lift is NOT forward-only (rules out single-regime confound)
Paired diff on rows that actually got the H1 better fill:
- TRAIN deep-H1 PRE-2025 (XAUUSD/XAGUSD, genuine OOS, n=33): base +0.126 -> +0.542 = **+0.416R lift**.
- FWD all (n=24): base +0.403 -> +0.940 = **+0.537R lift**.
The lift exists in real pre-2025 out-of-sample data. The doctrine's forward-only confound risk
is addressed: the mechanic is causal (same move, better entry, same stop), not a regime artifact.

### Robustness + leak (cascade)
- M15-leg insensitive: every (W,mi) in {24,48,96}x{0.5,1.0} beats H1-only fwd (+1.137..+1.174)
  and train (+0.466..+0.521). Horizon-flat: fwd +1.164 across M15 maxbars {640,960,1280,1920}.
- Leak: **0** entries before the H4 signal-bar close (explicit per-bar audit on both LTF legs).

Files: `mtf_refine_exp7_m15fill.py` (M15 primary-fill sweep), `mtf_refine_exp8_combine_and_causal.py`
(cascade + causal paired proof), `mtf_refine_exp9_cascade_robust.py` (robustness + leak audit),
`MTF_REFINE_CASCADE_LOCKED_RESULT.json` (locked numbers), `multitf_lib.py` (M15 paths added).

## WHAT FAILED — LEARNINGS (keep, do not promote)
1. **Tighter lower-TF stop (VAR_A trigger / VAR_B immediate, EXP1).** Entering on an H1
   retest trigger with an H1-STRUCTURAL (tight) stop: TRAIN +0.13 / +(-0.06) vs base +0.26;
   FWD worse. Tight stops get shaken out by noise that the wide H4 stop survives. **Learning:
   in the persistence regime, stop WIDTH is the protective ingredient — do not tighten it.**
   This is what flipped the design to "better fill, same width."
2. **H1-native breadth sleeve (EXP5).** Scan H1 for NEW FVG-retest continuations under the
   H4 GO-state (trend+ac60+vol), dedup vs core H4 grid. Adds ~52 NEW trades/yr forward.
   But: **TRAIN -0.135R, FWD +0.184R (62% win)** = forward-only positive = single-regime
   confound; not promotable. No vol-tier rescues it (LOW: +0.35 fwd but -0.15 train; HI:
   +0.28 train but -0.38 fwd = sign flip). Pockets that ARE good: XAUEUR +0.66R/92% win fwd.
   **Learning: lower-TF DOES surface more setups, but H1-native FVG quality is too low without
   a grade filter; the breadth is real, the edge is not yet.** Tested next (EXP6) and resolved.
3. **GRADE-FILTERED H1-native breadth sleeve (EXP6) — grade filters do NOT rescue it.** Swept
   gap-depth G in {0.10..0.80}*ATR, displacement-velocity V (impulse-bar range) in {1.0..2.0}*
   ATR, and H4-FVG-zone confluence C, choosing on TRAIN. **NONE turns train positive while
   keeping forward positive:**
   - gap-depth: G=0.40 -> train -0.035/fwd +0.054 (n drops 122->73); G=0.60 -> train -0.086/
     fwd +0.287 (n->48). Train stays negative at every depth.
   - displacement: V=1.0 -> train -0.106/fwd +0.226; tighter V makes train WORSE (V=1.6 train
     -0.352). Impulse filtering cuts freq without fixing the ~25-36% win rate.
   - confluence C: the ONLY filter that flips train positive (+0.097) but it collapses to 28
     train / 11 fwd trades and fwd goes NEGATIVE (-0.023). Not promotable.
   **Decisive learning: the win rate of H1-native FVGs in this regime stays ~25-36% regardless
   of grade — the STATE_D scale-out needs the continuation to actually RUN, and H1 FVG
   direction-picks don't run reliably. The edge is NOT in lower-TF picking new directions; it
   is in BETTER FILLS on the already-validated H4 signal direction (the cascade above). Park the
   H1-native breadth sleeve at zero size; its breadth is real but its directional edge is not.**

## NEXT STEPS
- Promote the H1->M15 CASCADE better-fill into the deployable metals sleeve (supersedes the
  H1-only rule; drop-in: same signal set, same risk unit, same STATE_D exit; only the fill price
  + exit stream change, with an M15 fallback leg). FWD +1.164R/87.8% win, ~33 trades/yr.
- DONE: M15 full-basket (EXP7), H1->M15 cascade (EXP8), causal pre-2025 OOS proof (EXP8),
  cascade robustness + leak audit (EXP9), grade-filtered breadth resolved as not-promotable (EXP6).
- Test the same better-fill mechanic on the OTHER persistence-positive classes (crypto momentum,
  energy in persistence) — the doctrine notes commodity-continuation pays in persistence; the
  cascade is class-agnostic geometry, so it should transfer where deep H1/M15 exist.
- Optional: widen the M15 fallback window/threshold per vol-tier (lift concentrates in LOW vol).
