# KB4 — Cross-instrument lead-lag / intermarket graph (track: leadlag)

Builder pass 2026-06-15. LAYER, not a strategy: a queryable directed intermarket graph +
a leak-free leader-impulse → laggard forward-odds miner. Doctrine: build & improve, map
WHERE/WHEN; per-YEAR never averages-as-verdict; no lookahead; forward holdout mandatory;
high odds from confluence; always report sample size n.

Engine: `leadlag.py` (importable). Outputs: `LEADLAG_GRAPH.json` (directed pairs),
`LEADLAG_EDGES.json` (full mined catalog with TRAIN/FWD/per-year/fwd-halves split).

## How it differs from the prior `hunt_cross_asset_leadlag.py`
The earlier hunt read ONLY the shallow `bridge_ftmo_deep_h4_2022_2026` dir, so almost every
pair showed `trN=0` — i.e. forward-only, untestable on a real TRAIN. `leadlag.py` uses
`w1.load` (the deep 2014/2015-2026 union), giving genuine TRAIN(<=2024) for the deep majors
(indices 2017-2021+, EURUSD/XAUUSD/USDJPY/silver/JPY-crosses 2015-2020+). That is what lets
us separate "real cross-regime edge" from "2025-26 single-regime artifact".

## No-lookahead contract (the only thing that matters here)
- Leader signal at close of bar i = z-scored cumulative log return over `look` CLOSED bars,
  z'd vs a TRAILING window that ends at i-1.
- Entry = laggard.close at the bar whose timestamp == leader's signal timestamp (H4 bars are
  on a shared 0/4/8/12/16/20 UTC grid; both have already closed → same-close decision/entry).
- Outcome on laggard bars strictly after i, via TESTED `geometry_lib.simulate` (pessimistic,
  stop wins ties). Stop = 0.5*ATR14(laggard, closed≤i). Real `w1.cost_for(follower)`.

## A. THE GRAPH — finding (important, honest)
Lagged cross-correlation of aligned H4 log returns across the deep universe shows that **the
strong cross-asset relationships are almost entirely CONTEMPORANEOUS (lag-0 co-movement), not
genuinely LEADING at the H4 bar level.** Of all directed pairs scanned over the deep symbols,
only ~13 have a lag-1..3 correlation that *beats lag-0 in BOTH regimes with sign+lag stable*,
and those genuine-lead links have tiny correlations (lead_gain ≈ 0.01–0.06). The big-|corr|
entries (EURGBP cluster, index↔index) are simultaneous, driven by shared dollar/risk factors.

Implication: a naive "leader moved last bar → enter laggard now" lag trade has almost no linear
edge on H4. **The exploitable structure is not the lagged correlation — it is the CONDITIONAL
forward distribution after a LARGE leader impulse** (a state, not a continuous signal). That is
exactly what the miner targets, and it is where the edge lives. The graph's real value is as a
*confluence map* (which instruments share a risk factor) + a falsifier of the lag-trade myth.

(Transfer-entropy proxy = sign mutual information per pair, lag-1, forward: also tiny — confirms
no strong directional bit-level lead at H4. Stored as `mi_fw_lag1` in the graph json.)

## B. THE MINER — forward-validated tradeable lead-lag edges
Scanned ~50 economic relations × looks{3,6,12} × z{1.0,1.5,2.0} × {momentum,reversion} × 4
geometries + confluence variants (dual-leader confirmation, laggard-regime-align gate). Tiers:
- `fwd_stable` = fwd n≥40, fwd R>0, BOTH forward halves R>0  → 174 configs.
- `tr_fw_robust` = real TRAIN n≥40 R>0 AND forward n≥40 R>0  → 79 configs.
- GOLD = both of the above → **17 configs** (the trustworthy core).

### Family aggregate (the headline direction of the edge family)
Trade-weighted across ALL base configs, forward EV is NEGATIVE for both momentum (-0.134) and
reversion (-0.160). **The family is NOT broadly tradeable** — most leader→laggard cells are
junk. The edge is a small set of CONFLUENT cells, never the average. (Doctrine in action: the
map judges states, not the system; a negative family average hides high-odds cells.)

### GOLD-TIER edges (real TRAIN R>0 AND forward-stable both halves)
| edge | cfg | TRAIN R (n) | FWD R (n) | fwd win | per-year forward |
|------|-----|-------------|-----------|---------|------------------|
| **NAS100→SPX500** | L12 z2.0 mom T2.0 | +0.306 (219) | +0.101 (103) | 23% | 25:+0.34 26:-0.29 |
| **NAS100→SPX500** | L3 z1.5 mom T1.5 [regime_align] | +0.171 (298) | +0.176 (142) | 31% | 22:+0.27 23:+0.12 24:+0.13 25:+0.35 26:-0.19 |
| **SPX500→NAS100** | L3 z1.5 mom T2.0 [regime_align] | +0.233 (320) | +0.119 (131) | 24% | 22:+0.14 23:+0.40 24:+0.16 25:+0.28 26:-0.23 |
| **SPX500→GER40** | L6 z2.0 rev T2.0 | +0.122 (252) | +0.094 (108) | 23% | (rev) 21:+0.88 25:+0.22 |
| **XAGUSD→XAUUSD** | L6 z2.0 mom TRAIL | +0.250 (180) | +0.070 (82) | 33% | 20:+0.33 21:+0.53 26:+0.49 |
| **GER40→UK100** | L6 z2.0 rev T1.5 | +0.069 (233) | +0.219 (106) | 32% | 21:+0.42 25:+0.19 26:+0.27 |
| **US30→USDJPY** | L6 z2.0 mom T2.0 | +0.065 (407) | +0.161 (98) | 26% | 21:+0.55 24:+0.19 25:+0.10 26:+0.29 |
| **US30→GER40** | L6 z1.5 mom T1.5 [regime_align] | +0.054 (365) | +0.167 (130) | 31% | 25:+0.29 26:+0.04 |
| **USDJPY→AUDJPY** | L6 z2.0 rev T2.0 | +0.024 (316) | +0.171 (70) | 26% | (fade JPY spike) |
| **BTCUSD→ETHUSD** | L12 z1.0 mom TRAIL | +0.279 (89) | +0.111 (605) | 36% | 24:+0.28 25:+0.18 26:-0.02 |

### Forward-only stable edges (no deep TRAIN — driver starts 2025; lower confidence)
- **EURUSD→XAUUSD** [regime_align L3 z1.5 mom T2.0]: FWD +0.577 (n=114), but TRAIN -0.156 over
  10 deep years (2015-2024 all negative). The forward number is a 2025-26 weak-dollar/gold-bull
  regime artifact at this aggressive config — DO NOT size as a train-validated edge. (See note.)
- **DXY_cash→XAUUSD** [regime_align]: FWD +0.40..+0.52, but DXY H4 only exists 2025+ → no TRAIN
  at all. Pure forward-only; keep as breadth-only / forward-confirmation context.
- **ETHUSD→LTCUSD / BTCUSD→LTCUSD / →DOTUSD**: FWD +0.34..+0.47 but alts have no pre-2025 H4 →
  forward-only crypto-beta; lower confidence than BTC→ETH which has a (thin) 2024 TRAIN.

## C. FALSIFICATION — is it the LEADER, or the follower's own move?
Critical control: re-mine each headline edge gating on the FOLLOWER's OWN impulse (same
look/z/thesis) instead of the leader. Forward EV, leader-gated vs self-gated:
| edge | leader-gated FWD R(n) | follower-self FWD R(n) | Δ (leader adds) |
|------|----------------------|------------------------|-----------------|
| US30→USDJPY (L3 z2 TRAIL) | +0.309 (117) | +0.063 (83) | **+0.246** |
| US30→USDJPY (L6 z2 T2.0)  | +0.161 (98)  | -0.186 (70) | **+0.347** |
| EURUSD→XAUUSD (L12 z2 T2) | +0.273 (91)  | -0.313 (116)| **+0.586** |
| BTCUSD→ETHUSD (L12 z1 TR) | +0.111 (605) | -0.037 (595)| **+0.149** |
| GER40→UK100 (rev)         | +0.133 (107) | +0.021 (118)| **+0.112** |
| NAS100→SPX500 (L3 z1.5 T2)| +0.052 (217) | +0.018 (208)| +0.034 |
The leader contributes genuine cross-asset information (Δ>0 everywhere). Most striking:
gold's and yen's OWN momentum at these horizons is a LOSER, but conditioning on the
risk/dollar leader flips it positive. This is a real, distinct signal family — not repackaged
single-instrument momentum.

## D. NULL / multiple-testing reality check
~2000 configs scanned → some "stable" cells are luck. Random-entry null (k matched random
follower bars, leader's direction prior kept), forward EV vs 5 null reps:
| edge | real fwd R | null fwd R (mean±sd) | z-ish |
|------|-----------|----------------------|-------|
| BTCUSD→ETHUSD | +0.111 | -0.038 ± 0.034 | **+4.3** |
| NAS100→SPX500 | +0.073 | -0.123 ± 0.067 | **+2.9** |
| US30→USDJPY   | +0.161 | -0.212 ± 0.171 | **+2.2** |
| XAGUSD→XAUUSD | +0.070 | -0.058 ± 0.208 | +0.6 (weak — lower confidence) |
BTC→ETH and the index family clear the null convincingly; XAGUSD→XAUUSD does not → treat as
breadth/low-confidence despite passing the stable+robust filters (a sample-size warning, per
doctrine — never present a thin/noisy cell as a strong edge).

## E. Verdict & how to use
1. **The lag-correlation lead trade is a myth on H4** (graph proves co-movement, not lead).
2. **The real edge = conditional forward odds after a LARGE leader impulse**, in a few confluent
   cells. The defensible, null-clearing, train+forward-robust core:
   - **Index momentum spillover** (NAS100↔SPX500, SPX500↔NAS100, US30→GER40, GER40→UK100):
     when one index makes a 1.5-2σ impulse, the co-moving index continues. Deepest samples
     (n=200-480 train), positive across 2022-2025; weak/negative 2026 (note the regime caveat).
   - **US30→USDJPY** (risk-on Dow → yen-weak): train+forward positive, leader adds +0.25-0.35R.
   - **BTCUSD→ETHUSD** (BTC leads ETH): +4.3σ vs null, huge sample (n=605 fwd), train +0.28.
   - **USDJPY→{AUDJPY,GBPJPY} reversion**: fade a 2σ USDJPY spike on the cross — forward +0.17-0.22.
3. These followers (indices, USDJPY, ETH) are largely NOT carriers in the current
   metals/crypto-continuation/energy book (PORTFOLIO_BUILD_W2: metals_core, crypto BTC/DASH/ETH
   continuation, energy_agri, idxrev fade, fx_jpy session). Signal logic is cross-asset
   conditioning, not single-instrument continuation → **likely low-correlation, additive family.**
   ETHUSD overlap with the existing crypto-continuation sleeve is the one to watch (same symbol,
   different trigger); index momentum-spillover is opposite-sign to the existing idxrev FADE
   sleeve, so they are complementary regime coverage.
4. **Do NOT** deploy the forward-only gold cells (EURUSD/DXY→XAUUSD) as train-validated — the
   deep history falsifies them as 2025-26 regime artifacts at aggressive configs.

## Reusable API (import `leadlag` from the route dir)
- `build_graph(min_overlap, lags, candidates)` → directed lead-lag edges (corr/lead_gain/MI, TR vs FW).
- `lagged_corr(a,b,lag,year_lo,year_hi)`, `_sign_mi(...)` → graph primitives.
- `leader_signal(leader, look)` → leak-free z-impulse map.
- `mine_pair(leader,follower,relsign,look,z,thesis,geom, confirm=,confirm_sign=,regime=)` → trades.
- `mine_all(...)`, `split_stats`, `forward_stable`, `train_forward_robust` → catalog + tiers.
- `RELATIONS`, `GEOMS`, `CONFIRM_SETS` → editable catalogs.
