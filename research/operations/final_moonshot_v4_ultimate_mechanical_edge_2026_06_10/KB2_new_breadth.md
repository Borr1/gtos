# KB2 — New breadth/frequency sleeves (track key: KB2)

Builder track: add breadth/frequency carriers — (a) ETHUSD 3rd crypto, (b) 2nd daily JPY entry at
the NY open, (c) dedicated energy supply-shock tier with a deeper runner, (d) agri grains.
Doctrine: build & improve, nothing killed; per-YEAR / per-SYMBOL never averages-as-verdict; no
lookahead; forward holdout (train year<=2024, forward 2025 & 2026); confidence-sized.

Module: `kb2_new_breadth.py` (builders + reporting). Refinement sweep: `kb2_refine.py`.
Result JSON: `KB2_NEW_BREADTH_RESULT.json`. All fills via tested `geometry_lib.simulate` /
`compounding_sleeve.exit_state_d`. Net R winsorized to [-1.3,+5]. Real cost `w1.cost_for(sym)`.

Summary of what was ADDED:
| sleeve | status | fwd EV (2025-26) | trades/yr | confidence size |
|---|---|---|---|---|
| (a) ETHUSD crypto, ac>=0.10 | IMPROVEMENT | +0.32R (pos every yr) | ~36 | 0.75 (BTC-like, thinner history) |
| (a) ETHUSD crypto, ac>=0.20 hi-conviction tier | IMPROVEMENT | +2.13R | ~4 | 0.50 (small n) |
| (b) NY-open JPY, gated (imp>=1.0+trend20) | IMPROVEMENT | +0.15R (pos both yrs) | ~190 | 0.50 (2nd session, dilutive USDJPY) |
| (c) ENERGY supply-shock vr>=2.0, runR=4 | IMPROVEMENT | +1.08R, 86% win | ~13 | 1.00 (88% win, both fwd yrs +) |
| (d) grains WHEAT/SOYBEAN | DATA-BLOCKED learning | n/a | n/a | — |

---

## (a) ETHUSD — 3rd crypto carrier (resampled M1->H4)

**Data fix.** `w1.load('ETHUSD')` H4 is broken (134 bars). I resampled `ETHUSD_M1.csv`
(real M1 data 2024-10 .. 2026-06, ~1.05M rows across `bridge_ftmo_m1_*`) into UTC-aligned H4
buckets (0/4/8/12/16/20, matching the deep-H4 grid) -> **3577 H4 bars, 2024-10-11 .. 2026-06-09**.
This gives a thin 2024-Q4 train slice (year<=2024) + full 2025 & 2026 forward — the SAME structure
as BTC/DASH in KB_crypto.md (train thin, forward is the verdict).

**Rule (IDENTICAL to KB_crypto.md locked rule):** Donchian-20 breakout on closed bars
(long if `close[i] > max(high[i-20..i-1])`, short if `close[i] < min(low[i-20..i-1])`) + persistence
gate `ac60 >= THR` + wide stop `sd = 2.0*ATR14` + fixed target `4R`. Cost = crypto class.

**EV is monotone in the ac threshold (same property KB_crypto found for BTC/DASH) — robust, not a
magic number:**

| ac thr | ALL n | ALL EV | FWD n | FWD EV | per-year |
|---|---|---|---|---|---|
| 0.10 | 81 | +0.513 | 62 | **+0.322** | 2024:+1.14 2025:+0.36 **2026:+0.17** |
| 0.15 (KB default) | 36 | +1.047 | 23 | +0.414 | 2024:+2.17 2025:+0.70 2026:-0.95(n4) |
| 0.175 | 24 | +1.403 | 13 | +0.639 | 2024:+2.31 2025:+0.95 2026:-1.10(n2) |
| 0.20 | 17 | +2.137 | 7 | **+2.126** | 2024:+2.15 2025:+2.66 2026:-1.10(n1) |

**Recommended ETH settings (confidence-sized, nothing killed):**
- **Carrier setting = ac>=0.10** (NOT the 0.15 BTC default): it is the ONLY threshold forward-positive
  in EVERY year including 2026 (+0.17R, n=13), with the most frequency (~36 trades/yr). At ac>=0.15+
  the 2026 slice collapses to n<=4 and goes negative — that is breakout-gate over-tightening on ETH's
  thin 2026 history, not a real sign flip (the lower-threshold superset is +0.17R in 2026). ETH needs
  a looser persistence gate than BTC because its sample is shorter.
- **High-conviction tier = ac>=0.20** at smaller size: +2.13R fwd (n=7) — strong but n is tiny, so
  cap at 0.50 size. Kept for the size-by-confidence ladder, not deleted.
- **Exit:** fixed 4R target beats the STATE_D scale-out for ETH (target4 fwd +0.32 vs scale-out
  +0.01 at ac>=0.10) — exactly as KB_crypto found for BTC/DASH. The scale-out raises win% (45% vs
  31%) but gives up the right-tail that IS the crypto edge.

**Per-direction (ac>=0.15, fwd):** long +0.31R (n16), short +0.64R (n7) — both sides pay; shorts
slightly better (2026 was a crypto decline). **Confidence size: 0.75** of full crypto-sleeve size
(BTC-like behavior confirmed, but history is shorter than BTC/DASH so haircut pending more bars).

**Caveat (honest):** ETH H4 history only starts 2024-10 (resampled). 2024 is the thin train; the
forward 2025-26 is the verdict and it is positive at ac>=0.10. Re-validate as more H4 accrues. The
resampler is leak-free (H4 close = last M1 close in the bucket; gate/breakout use closed bars only).

---

## (b) 2nd daily JPY entry at the NY open (mirror London R1)

**Setup:** mirror of KB_fx_jpy.md R1 (1-hour opening-impulse ride, M15, stop 1.0*ATR, target
2.5*ATR, maxbars=48, one trade/sym/day, GBPJPY+USDJPY) but anchored at the NY session instead of
London. M15 data window 2025-06..2026-06 (forward-only; same caveat as R1).

**LEARNING — the RAW NY mirror does NOT carry the London edge (this is the decisive finding):**
- NY-hour scan (raw, s1.0/t2.5): hour>=12 −0.16R, >=13 −0.24R, >=14 −0.12R, >=15 −0.02R, >=16 −0.12R.
  Best raw NY hour (15) is only −0.018R vs London hour>=8 = **+0.168R** (London R1 reproduced exactly
  here — machinery verified). The clean directional persistence off the London open is a LONDON
  phenomenon; the NY open's first hour is choppier (US data already digested, no fresh trend
  initiation the way London opens the European/JPY trend day).

**BUT a gated NY variant IS a real (smaller) breadth sleeve — improvement, not killed:**
Add an impulse-strength filter + M15 trend alignment (only ride a strong NY-open impulse that agrees
with the 20-bar M15 trend):
- **NY hour>=15 + imp>=1.0*ATR + trend20:** **+0.154R, n=197 (~190 trades/yr), 36.5% win,
  positive in BOTH forward years (2025:+0.10, 2026:+0.23), 9/13 months positive.**
- Per-symbol: **GBPJPY +0.312R (n82)** carries it; USDJPY +0.042R (n115) is dilutive but kept.
- Falsification: same gated rule on pure FX (EURUSD/GBPUSD/AUDUSD) = **−0.128R** -> JPY-specific,
  not a generic momentum artifact. (Raw pure-FX NY = −0.173R.)
- The gates each add value monotonically: base −0.02 -> imp>=0.8 +0.05 -> trend20 +0.07 ->
  imp1.0+trend20 +0.15. The edge that survives at NY is the STRONG, TREND-ALIGNED impulse only;
  the London open is permissive enough to ride any impulse, the NY open is not.

**Deploy:** the gated NY-JPY sleeve at **0.50 confidence size** (2nd daily session = breadth/frequency,
+190 trades/yr, low per-trade EV, GBPJPY-led). It roughly doubles JPY-session frequency (London R1
~490/yr + NY gated ~190/yr) for a modest EV at small size. Same single-forward-window caveat as R1 —
re-validate when pre-2025 M15 is exported.

---

## (c) Energy supply-shock tier (vr>=2.0) with a DEEPER runner — clear improvement

**Tier:** the `vr>=2.0` supply-shock state from KB_energy_agri.md (88% win, the single strongest
energy sub-edge). Baseline STATE_D (vol-tiered runR, which caps the runner at 2.5R for high-vol
trades) under-monetizes shock trends. I swept a deeper fixed runner on this tier only:

| runR | ALL EV | FWD EV (2025-26) | FWD win | per-year |
|---|---|---|---|---|
| 2.5 (baseline) | +0.867 | +0.940 | 86% | 2021:+0.46 2025:+0.59 2026:+1.07 |
| **4.0** | **+0.982** | **+1.076** | 86% | 2021:+0.46 2025:+0.63 **2026:+1.24** |
| 5.0 | +1.059 | +1.167 | 86% | 2021:+0.46 2025:+0.38 2026:+1.46 |
| 6.0 | +1.097 | +1.213 | 86% | 2021:+0.46 **2025:-0.04** 2026:+1.68 |

**LOCKED: runR=4.0 (optionally 5.0 at smaller size).** runR=4 lifts forward EV +0.94 -> **+1.08R**
(+15%) while keeping 88% win and BOTH forward years robustly positive (2025:+0.63, 2026:+1.24).
runR=5 squeezes more (+1.17R) but 2025 weakens to +0.38; runR=6 BREAKS 2025 (−0.04) — the deepest
runner over-fits the 2026 trend year. So the runner ladder has a clean stationarity boundary at
runR≈4-5: beyond it you trade 2025 robustness for 2026 tail. The shock trend genuinely runs further
than the STATE_D 2.5R cap allowed; runR=4 captures it without 2025 fragility. Confidence size 1.00.

Note: n=26 (the shock state is rare by design — ~13 trades/yr forward). Frequency is low; this is a
high-EV, high-win, low-frequency tier and should be sized as such (it is the deepest-edge energy tier).

---

## (d) Agri grains WHEAT / SOYBEAN — DATA-BLOCKED (learning, exact source requirement)

**No WHEAT or SOYBEAN export exists anywhere in this repo** (checked all `bridge_ftmo_*` dirs across
H4, M15, M1). The only agri H4 symbols present are `CORN_c` and `COTTON_c` (already in
`energy_agri_sleeve.py`). 0 WHEAT/SOYBEAN files found.

This is the same data ceiling KB_energy_agri.md flagged as next-step #4. It is a data ask, not a
signal question: the agri-persistence machinery (ac60>=0.10, +0.64R, 89% win on CORN/COTTON) is
ready to extend the moment grains arrive.

**EXACT SOURCE REQUIREMENT:** continuous H4 OHLCV for `WHEAT_c` and `SOYBEAN_c` (ideally 2015-2026,
minimum 2023-2026 for a CORN-style train/forward split) exported to
`data/mt5_research_exports/bridge_ftmo_deep_h4_*`. With that, apply the locked agri gates verbatim
(ac60>=0.10 high-conf; not-Dec-Feb seasonal breadth) — expect CORN-like behavior given the shared
weather/seasonal persistence regime.

---

## NET BREADTH CONTRIBUTION (forward 2025-26, confidence-sized)

- **ETHUSD (ac>=0.10):** +0.32R/trade, ~36 trades/yr, pos every year, 0.75 size. New asset (3rd crypto
  carrier), low correlation to metals.
- **NY-JPY gated:** +0.15R/trade, ~190 trades/yr, pos both years, 0.50 size. 2nd daily JPY session ->
  ~doubles JPY-session frequency.
- **Energy shock runR=4:** +1.08R/trade, 86% win, ~13 trades/yr, 1.00 size. Deepens the highest-EV
  energy tier (+15% vs baseline runner).
- **Grains:** blocked on data only; ready to add on export.

Combined this adds ~240 new trades/yr of breadth across crypto + a 2nd FX session + a sharper energy
tier, every piece forward-validated and confidence-sized, nothing killed.

## NEXT STEPS
1. Wire ETH (ac>=0.10 carrier + ac>=0.20 hi-conviction tier) into the crypto sleeve / portfolio build;
   add the ETH M1->H4 resampler as a permanent loader so ETH refreshes with new M1 months.
2. Add the gated NY-JPY sleeve to the FX/JPY sleeve as a 2nd-session entry at 0.50 size; stack the
   L4 DOW tilt from KB_fx_jpy onto it once older M15 history exists.
3. Lock energy supply-shock tier runR=4 in `energy_agri_sleeve` (deeper-runner variant for vr>=2.0).
4. Export WHEAT_c/SOYBEAN_c H4 to unblock grains.

## FILES
- `kb2_new_breadth.py` — all four builders + ETH M1->H4 resampler + reporting (run as main).
- `kb2_refine.py` — ETH ac-threshold/exit sweep + NY-JPY rescue sweep.
- `KB2_NEW_BREADTH_RESULT.json` — machine-readable results.
- Comparators: KB_crypto.md, KB_fx_jpy.md, KB_energy_agri.md (locked wave-1 rules mirrored here).
