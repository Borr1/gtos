# KB2 — Deeper history to validate forward-only sleeves (track: data_depth)

Builder pass 2026-06-15. Goal: convert forward-only sleeves to TRAIN-validated by sourcing
deeper history from the MT5 Docker bridge, then re-validate on a real TRAIN(<=2024)->FORWARD
(2025-26) split. Doctrine: build & improve, per-YEAR never averages-as-verdict, no lookahead,
forward holdout mandatory, distrust forward-only positives, delete nothing.

## (a) BRIDGE IS REACHABLE — deep history exported

- `siliconmetatrader5` installed; `localhost:8001` OPEN; `client.initialize()=True`, account trade_mode=2.
- Connection path: `scripts/export_mt5_research_ohlcv.py` -> `--prefer-silicon-bridge --bridge-port 8001`.
- CRITICAL: file labels != broker symbols. Correct broker names (from the existing deep-h4 manifest):
  indices use `.cash` and US tickers (SPX500=US500.cash, GER40=GER40.cash, UK100=UK100.cash,
  US30_cash=US30.cash, EU50_cash=EU50.cash, NAS100=US100.cash); energy/agri use `.cash`/`.c`
  (NATGAS.cash, UKOIL.cash, USOIL.cash, HEATOIL.c, CORN.c, COTTON.c). FX/crypto are plain.

### TRUE earliest broker history (probed directly), and what was exported

| symbol      | broker name | H4 earliest | M15 earliest | TRAIN(<=2024) now? |
|-------------|-------------|-------------|--------------|--------------------|
| GBPJPY/USDJPY/EURUSD/GBPUSD/AUDUSD | plain | 2014-01 | **2014-01** | YES (11.5 yr M15) |
| GER40       | GER40.cash  | 2018-03     | -            | YES (deep) |
| UK100       | UK100.cash  | 2017-12     | -            | YES (deep) |
| US30_cash   | US30.cash   | 2019-02     | -            | YES (deep) |
| SPX500      | US500.cash  | 2021-01     | 2021-01      | YES (3.9 yr) |
| EU50_cash   | EU50.cash   | 2021-01     | -            | YES (3.9 yr) |
| USOIL/UKOIL | .cash       | 2020-12     | 2020-12      | YES (deep) |
| CORN_c      | CORN.c      | 2023-03     | -            | YES (partial, 1.7 yr) |
| NATGAS_cash | NATGAS.cash | 2024-10     | -            | thin (Q4-24 only) |
| HEATOIL_c   | HEATOIL.c   | 2025-01     | -            | NO (forward-only) |
| COTTON_c    | COTTON.c    | 2025-03     | -            | NO (forward-only) |
| ETHUSD      | ETHUSD      | **2024-09** | 2024-09      | partial (Q4-24, n=13) |

### Exports written (manifest + sha256 + read_only, existing conventions)

1. `data/mt5_research_exports/bridge_ftmo_deep_h4_backfill_2014_2026/` — H4 for SPX500, GER40,
   UK100, US30_cash, EU50_cash, CORN_c, COTTON_c, NATGAS_cash, HEATOIL_c, UKOIL_cash, USOIL_cash,
   ETHUSD. 12 symbols, 2014-2026 request window (broker-capped per table above), 0 errors.
2. `data/mt5_research_exports/bridge_ftmo_fx_m15_backfill_2014_2025/` — M15 for GBPJPY, USDJPY,
   EURUSD, GBPUSD, AUDUSD, CHFJPY, EURJPY. 7 symbols, **2014-01..2025-05**, ~280k bars/symbol, 0 errors.
   Unions with existing `bridge_ftmo_m15_20250601_20260610/` to give 11.5 years of M15 FX.
3. MERGED the deep H4 backfill INTO `bridge_ftmo_deep_h4_2022_2026/` (the dir `w1.load` reads,
   alongside `..._2015_2022`). Union by timestamp, backfill wins on overlap. **Overlap OHLC verified
   identical (0 mismatches)** on GER40/SPX500/US30/CORN — strict superset, only earlier bars added.
   Originals preserved in `_pre_backfill_2014_orig/`; provenance in
   `DEEP_H4_BACKFILL_MERGE_PROVENANCE.json`. Net effect: `w1.load(sym)` now serves deep TRAIN history
   for indices/energy/agri AND ETHUSD (which was a broken 134-bar stub -> now 3774 bars).

## (b) Resampling not needed
The bridge was reachable, so no M1->M15/H4 resampling fallback was used. (M1 2024+ exists but bridge
H4/M15 history is deeper and cleaner.)

## (c) RE-VALIDATION VERDICTS (TRAIN<=2024 -> FORWARD 2025 & 2026, per-year, per-symbol)

Scripts: `KB2_revalidate_fxjpy.py`, `KB2_revalidate_idxrev.py`, `KB2_revalidate_crypto_eth.py`,
and the energy/agri re-run via `energy_agri_sleeve.build_candidates()` on deep w1.load.

### 1) fx_jpy London-open momentum (M15) -> STAYS FORWARD-ONLY (now revealed as a single-regime artifact)
Locked rule R1 (GBPJPY+USDJPY, impulse over first 4 London M15 bars, stop1.0/tgt2.5, maxbars48),
re-run on 11.5 yr M15:
- TRAIN<=2024: **-0.103R/trade** (n=5706), negative in **9 of 11 train years** (2014-2023 all neg
  except 2021 ~flat; only 2024 +0.042).
- FWD2025 +0.003, FWD2026 +0.152 (FWD25-26 +0.048) — the KB's published +0.168R was a 2025-26-only
  window pumped by trendy BoJ-divergence months; on the deduped deep set forward is much smaller.
- Per-symbol: GBPJPY FWD +0.146 but TRAIN -0.114; USDJPY TRAIN -0.093 / FWD -0.050.
- Pure-FX falsification control even worse (TRAIN -0.203, FWD -0.134) — JPY-specific bias confirmed,
  but the bias is NOT a TRAIN edge. NO conditional gate fixes it: impulse-strength and prior-day
  trend-alignment gates are all TRAIN-negative (best is align-gated TRAIN -0.08 / FWD +0.128).
- **VERDICT: forward-only, do NOT deploy as primary. The deep history FALSIFIES the train hypothesis.**
  Best surviving sub-pocket = trend-aligned, tiny size only. This corrects KB_fx_jpy R1's optimism.

### 2) Index failed-breakout fade (H4) -> STAYS FORWARD-ONLY (now falsified across 5 deep indices)
Locked rule (lb16, stop1.5, tgt0.75, maxbars60, no gate), re-run with real TRAIN on 5 indices:
- Full pocket TRAIN<=2024 **-0.065R** (n=4447), neg in **5 of 6 train years** (2019-2024; only 2021 ~+0.01).
- FWD2025 +0.002, FWD2026 +0.074 (FWD25-26 +0.025) — real but small, forward-only as KB suspected.
- Per deep-train symbol (TRAIN / FWD): SPX500 -0.107/+0.006, GER40 -0.053/-0.108, UK100 -0.008/+0.068,
  US30 -0.102/+0.001, EU50 -0.055/+0.103. **Every deep index is TRAIN-negative.**
- Geometry/lb robustness: 1.5/0.75 is the least-bad train config (consistent with KB), lb monotone, but
  all TRAIN-negative. **VERDICT: forward-only / small-size breadth, now with HARD evidence (5 deep
  indices) it is not a deployable primary. Confirms & hardens KB_index_reversion's honest stance.**

### 3) Energy + Agri continuation (H4) -> CONVERTS to TRAIN-validated  (the win of this track)
Locked gates (energy = vr>=2.0 OR |slope30|<0.05 ATR/bar; agri = ac60>=0.10), STATE_D exit, re-run
on deep w1.load (USOIL/UKOIL now 2020+, CORN 2023+):
- **ENERGY gate: TRAIN<=2024 +0.433R (n=35, 74% win) ; FWD25-26 +0.658R (n=70, 69% win).**
  Positive in train years 2021(+0.53), 2022(+0.71), 2024(+0.11) and forward 2025(+0.29), 2026(+0.94).
  USOIL TRAIN +0.50/FWD +0.49 and UKOIL TRAIN +0.37/FWD +0.22 are BOTH-SIDE positive on the deepest
  symbols. **CONVERTS — train-validated, not a 2026 confound.**
- **AGRI persistence (ac60>=0.10): TRAIN<=2024 +0.138R (n=15, all 2023) ; FWD +0.98R (n=5).**
  Positive both sides but thin -> CONVERTS (low-confidence, keep conf 0.5).
- AGRI seasonal breadth (not Dec-Feb): TRAIN -0.254 / FWD +0.348 -> stays forward-only breadth (small).
- HEATOIL/COTTON still forward-only (no pre-2025 broker history) -> keep 0.5 sym haircut as KB does.

### 4) Crypto ETH carrier (H4) -> CONVERTS; ETH added as 3rd carrier
ETH H4 was a broken 134-bar stub; rebuilt to 3774 bars (2024-09+). Locked crypto rule
(lb20 Donchian + ac60>=0.15 + sd2 + tgt4):
- **ETHUSD: TRAIN<=2024 +2.17R (n=13, 85% win) ; FWD2025 +0.70R (n=19) ; FWD2026 -0.95 (n=4, tiny
  adverse-regime sample matching the 2026 BTC-decline caveat).** ac-gate monotone (ac>=0.20 ->
  TRAIN +2.15 / FWD +2.13). ETH CONVERTS as a carrier.
- **3-carrier BTC+DASH+ETH: TRAIN +1.77R (n=21, was n=8) ; FWD25-26 +0.66R (n=83, ~55 trades/yr).**
  Adding ETH ~triples train n (more robust train) and raises forward frequency while staying strongly
  positive. (BTC+DASH reproduction matched KB exactly: TRAIN +1.138 n8, FWD +0.751 n60 — harness faithful.)
- **VERDICT: ETH CONVERTS and IMPROVES the crypto sleeve (breadth + train robustness).** Add ETH at
  full carrier weight with the same ac>=0.15 gate; size 2026 cautiously given the thin adverse sample.

## SUMMARY TABLE — conversion outcomes

| forward-only sleeve            | deep data now available        | verdict after real TRAIN split |
|--------------------------------|--------------------------------|--------------------------------|
| fx_jpy London-open (M15)       | M15 2014-2025 (11.5 yr)        | **STAYS forward-only — FALSIFIED as train edge** (TRAIN -0.103R) |
| index failed-breakout (H4)     | 5 indices deep (2017-2021+)    | **STAYS forward-only — falsified across 5 deep indices** (TRAIN -0.065R) |
| energy continuation (H4)       | USOIL/UKOIL 2020+, CORN 2023+  | **CONVERTS — train-validated** (TRAIN +0.433R, FWD +0.658R) |
| agri persistence (H4)          | CORN 2023+                     | **CONVERTS (thin)** (TRAIN +0.138R, FWD +0.98R) |
| crypto ETH (H4)                | ETH H4 rebuilt 2024-09+        | **CONVERTS + improves sleeve** (TRAIN +2.17R, 3-carrier FWD +0.66R) |

Net: 3 of the 4 forward-only sleeves convert (energy, agri, crypto-ETH); fx_jpy and index reversion
do NOT convert and are now demonstrably single-regime forward artifacts — kept as tiny-size breadth,
not deleted, with the train evidence that they must not be sized like the convertible sleeves.

## Data now in repo (exact)
- `bridge_ftmo_deep_h4_backfill_2014_2026/` (12 H4 symbols, manifest+sha)
- `bridge_ftmo_fx_m15_backfill_2014_2025/` (7 M15 FX symbols 2014-2025, manifest+sha)
- `bridge_ftmo_deep_h4_2022_2026/` now contains the unioned deep rows (provenance JSON inside);
  `w1.load` automatically serves deep TRAIN history for the converted sleeves.
