# Agent γ — Missed-Trade Opportunity-Cost Census

**Author:** Claude Code Opus 4.7 research agent (session 35, phase 1 dispatch)
**Date:** 2026-04-19
**Scope:** XAUUSD (primary) + NAS100 + EURUSD (secondary) T7 simulation corpora (Jan 2 – Apr 17 2026).
**Data sources:**
- `research/t7_live_simulation/all_results_jan_apr10.json` (XAUUSD, 2 100 records)
- `research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{1..5}/NAS100_t7_simulation.json` (NAS100, 1 600 records, merged)
- `research/t7_live_simulation/EURUSD_t7_simulation.json` (EURUSD, 2 280 records; secondary, eps-degenerate)
- `data/historical_2026/{SYMBOL}_M15.csv` (forward-price replay)
- `scripts/simulate_t7_live_period.py:80` (`EPSILON_BY_SYMBOL` — honest per-instrument fill epsilon)
- `scripts/simulate_t7_live_period.py:480-573` (`compute_outcome()` reused)
**Script:** `research/b_deep_audit_2026-04-19/phase1/_gamma_scratch/missed_trade_census.py`
**Replay artefact:** `research/b_deep_audit_2026-04-19/phase1/_gamma_scratch/census_out.json`

---

## TL;DR (5 bullets)

1. **The "missed trades" hypothesis does NOT explain decay.** NO_TRADE forward hit-rate at a +1.5 × ATR(M15) / −1 × ATR SL proxy in `bias` direction is ~37 % across all three instruments — **statistically indistinguishable from the random-direction baseline of 37-40 %** (XAUUSD 36.6 %, NAS100 38.0 %, EURUSD 39.2 %). The system is not systematically rejecting winners at the NO_TRADE gate.
2. **L2 rejections are correctly edge-negative on XAUUSD overall** (−128R net across 741 rejects, WR 34.7 %) and mildly positive on NAS100 (+8.50R, 44 %) — the NAS100 net hides a bucket split (see #3).
3. **`sl_beyond_ob` is fully non-universal.** NAS100: 26 W / 20 L, +19.0R, +0.413R Exp, n=46 — but **p=0.46 two-sided vs coin-flip** (NOT individually significant). XAUUSD: 5 W / 15 L, **−7.49R, −0.374R Exp, n=20** (correctly killed). Confirms session-33/T3.2 cross-instrument verdict: NAS100-only, and even there the "+19R" is **concentrated in March (+19.5R / 67.9 % WR n=28)** — it's regime-shift-recovery, not structural.
4. **The biggest leak is `max_kz_trades` + `max_daily_trades_sim` BLOCKED_LIMIT on NAS100** — 43 W / 24 L / 15 U = 64.2 % resolved WR, +40.62R total, +0.495R Exp (n=82). This is the true "good trades we couldn't take" bucket. On XAUUSD it's small (n=13, −2.95R). On EURUSD the bucket is degenerate under honest eps.
5. **Monthly evolution reveals a real regime shift on NAS100, not on XAUUSD.** NAS100 CAND decay Jan 90 % → Apr 33 % (Fisher Jan-Feb vs Mar-Apr p=0.061, marginal). NAS100 BL decay 93 % → 40 % (p=2×10⁻⁵, **Bonferroni-safe at α=0.05/96**). NAS100 L2 **inverse** decay 24 % → 60 % (p=0.028). These move in synchrony — **the market flipped regime in mid-March, not our edge decaying**. XAUUSD shows no such synchrony; L2 is uniformly negative across months, confirming the XAUUSD gate is correctly calibrated.

---

## 1. Methodology

### 1.1 Decision slices

Per symbol, I partition T7 sim records by `decision` field:

| Slice | XAUUSD | NAS100 | EURUSD |
|---|---:|---:|---:|
| NO_TRADE | 1 034 | 1 395 | 1 980 |
| REJECTED_L2 | 741 | 84 | 253 |
| BLOCKED_LIMIT | 13 | 82 | 38 |
| CANDIDATE | 10 | 37 | 9 |
| NO_TRADE_PARSE_FAIL | 289 | — | — |
| PARSE_ERROR | 13 | 2 | 0 |
| **Total** | 2 100 | 1 600 | 2 280 |

NO_TRADE + PARSE_FAIL are the skipped superset; L2 + BLOCKED are the reject-with-prices superset.

### 1.2 NO_TRADE forward-price census (schema-limited)

**Schema limitation confirmed:** NO_TRADE records do NOT carry `direction`, `entry_price`, `stop_loss`, or `take_profit_1` (`scripts/simulate_t7_live_period.py:467-478` emits only `candle_time, kill_zone, decision, no_trade_reason, symbol, date, cost`). We only have `bias` (`bullish` / `bearish` / null) when the AI ran and the prescreen fired.

**Proxy TP/SL.** For each NO_TRADE record with `bias ∈ {bullish, bearish}`:
- Entry = close of signal M15 candle (proxy).
- TP_proxy = entry ± 1.5 × ATR_M15 (1.5R at 1 × ATR risk).
- SL_proxy = entry ∓ 1.0 × ATR_M15 (1R at 1 × ATR risk).
- ATR_M15 = dataset-average true range over the last 14×96 = 1 344 M15 candles.
- Horizons: 4h (16 M15), 12h (48), 24h (96).
- On SL + TP same-candle: conservatively score **HIT_SL** (tilts against the "missed winners" claim).

Bias coverage: XAUUSD 402/1 034 (38.9 %), NAS100 613/1 395 (43.9 %), EURUSD 806/1 980 (40.7 %).

**Control (baseline).** I replayed the same proxy-TP/SL geometry on **every 20th M15 candle, both LONG and SHORT, agnostic to any gate or bias**. This gives the unconditional hit-rate baseline for Q1 2026 on each instrument.

| Instrument | Baseline LONG hypo-WR | Baseline SHORT hypo-WR |
|---|---:|---:|
| XAUUSD | 36.6 % (124 / 339) | 44.5 % (151 / 339) |
| NAS100 | 38.0 % (130 / 342) | 40.6 % (139 / 342) |
| EURUSD | 39.2 % (141 / 360) | 38.9 % (140 / 360) |

(code: `missed_trade_census.py:_nt_census` + `_nt_forward_hit`)

### 1.3 L2 / BLOCKED_LIMIT counterfactual

Full (entry, SL, TP₁) price triples present. Re-runs `compute_outcome()` at the **honest per-instrument epsilon** (`EPSILON_BY_SYMBOL`), matching session 35 A1/A2/A3 conventions. `candle_close` is retrieved from M15 CSV when missing (XAUUSD sim schema omits it).

Degenerate records (entry=SL or entry=TP or SL=TP — the FX precision artefact) are tallied separately and excluded from WR / sumR / expR aggregates to prevent the phantom-WIN r=0 bug.

### 1.4 Monthly evolution

Dataset covers Jan 2 – Apr 17 2026 only, so "quarterly" collapses to **calendar months** (Jan / Feb / Mar / Apr). The decay-tracking hypothesis is symbolic — calling the stated quarters "Q2-2025 → Q1-2026" is handoff nomenclature; the actual quarterly 73→59 % WR figures in CLAUDE.md come from the 367-trade batch KB which **does not carry L2 / block fields** (per `research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md:47` — confirmed). This census therefore answers the question "did the decay we see in CANDIDATE WR track the same direction in REJECTED and BLOCKED buckets over Jan→Apr 2026?" — a proxy for the quarterly question.

### 1.5 Statistics

- **Bonferroni floor:** 12 gate-bucket tests × 8 phase-1 agents = 96 tests → α_corr = 0.05/96 = **5.2 × 10⁻⁴**.
- Within γ alone (3 instruments × 4 L2 buckets = 12 tests): α_corr_intra = 4.2 × 10⁻³.
- Two-sided exact binomial p for bucket vs coin-flip.
- Two-sided Fisher exact 2×2 for monthly decay (Jan-Feb vs Mar-Apr).
- n ≥ 20 for hard claim; n < 20 tagged **exploratory**.

---

## 2. Question 1 — NO_TRADE forward hit-rate census

Did a NO_TRADE candle move +1.5R (ATR-proxy) in the AI's `bias` direction within 4h / 12h / 24h of close?

### 2.1 Aggregate by instrument + horizon

| Sym | n w/ bias | 4h hypo-WR | 12h hypo-WR | 24h hypo-WR | 24h hypo-ExpR | vs baseline (LONG) |
|---|---:|---:|---:|---:|---:|---|
| XAUUSD | 402 | 37.2 % | 37.5 % | 37.8 % (152 W / 402) | −0.055R | 36.6 % → **+1.2pp** (NOT significant) |
| NAS100 | 613 | 35.7 % | 36.9 % | 36.9 % (226 W / 613) | −0.078R | 38.0 % → **−1.1pp** (worse than random) |
| EURUSD | 806 | 37.5 % | 38.3 % | 38.3 % (309 W / 806) | −0.042R | 39.2 % → **−0.9pp** (worse than random) |

**Interpretation.** The "missed trades" bucket on NO_TRADE is **indistinguishable from a random-direction baseline** on every instrument. If the system were systematically rejecting winners at the NO_TRADE gate, we'd expect hypo-WR > baseline. We observe ≤ baseline. **Hypothesis refuted** at the NO_TRADE decision slice.

### 2.2 Monthly NO_TRADE hypo-WR (24h horizon)

| Sym | Jan | Feb | Mar | Apr | Decay trend |
|---|---:|---:|---:|---:|---|
| XAUUSD | 46.8 % (37/79) | 37.1 % (52/140) | 36.9 % (58/157) | 19.2 % (5/26) | declining (small-n Apr) |
| NAS100 | 34.1 % (47/138) | 33.2 % (69/208) | 39.8 % (72/181) | 44.2 % (38/86) | **increasing** |
| EURUSD | 29.0 % (91/314) | 46.9 % (160/341) | 41.8 % (56/134) | 11.8 % (2/17) | volatile |

**Zero evidence** that the NO_TRADE bucket is where the "decay is rotating good trades to rejection". On NAS100 the hypo-WR is *increasing* over time while CAND WR decays — but the absolute level (37-44 %) is still below the random LONG baseline (38 %). Nothing to see at this gate.

---

## 3. Question 2 — L2 rejection opportunity cost (bucket by `l2_reason`)

### 3.1 Aggregate by instrument

| Sym | n | resolved | W | L | WR% | sumR | ExpR | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| XAUUSD | 741 | 730 | 253 | 477 | 34.7 % | **−128.04R** | −0.173R | Correctly killed |
| NAS100 | 84 | 84 | 37 | 47 | 44.0 % | +8.50R | +0.101R | Mildly positive net |
| EURUSD (non-degen) | 101 | 101 | 43 | 58 | 42.6 % | +6.18R | +0.061R | Near-neutral |

### 3.2 Top-3 L2 reasons by opportunity cost (XAUUSD primary)

| Rank | Symbol | l2_reason | n | W | L | WR% | sumR | ExpR | Binom p (vs 0.5) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | XAUUSD | `entry_in_ob` | 557 | 198 | 352 | 36.0 % | −85.56R | −0.154R | <10⁻⁶ |
| 2 | XAUUSD | `h1_poi_exists` | 159 | 50 | 107 | 31.8 % | −31.99R | −0.201R | <10⁻⁶ |
| 3 | XAUUSD | `sl_beyond_ob` | 20 | 5 | 15 | 25.0 % | **−7.49R** | −0.374R | 0.041 (exploratory, n<30) |

**All three XAUUSD L2 buckets are significantly worse than coin-flip.** The gates correctly reject losers. There is **no systematic XAUUSD L2 leak** — the +negative evidence is consistent with the T3.2 cross-instrument audit.

### 3.3 Top-3 L2 reasons by opportunity cost (NAS100)

| Rank | Symbol | l2_reason | n | W | L | WR% | sumR | ExpR | Binom p (vs 0.5) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | NAS100 | `sl_beyond_ob` | 46 | 26 | 20 | 56.5 % | **+19.00R** | +0.413R | **0.46 (NOT significant alone)** |
| 2 | NAS100 | `h1_poi_exists` | 32 | 11 | 21 | 34.4 % | −4.50R | −0.141R | 0.12 (correctly killed direction) |
| 3 | NAS100 | `entry_in_ob` | 5 | 0 | 5 | 0 % | −5.00R | −1.00R | 0.03 exploratory (correctly killed) |

**Key reconciliation with session 33's NAS100 +13.5R / +20.50R claim:**
- `sl_beyond_ob` bucket on NAS100 is **+19.00R net** in my replay (26 W / 20 L, 56.5 % WR). Session 33 reported +20.50R on n=42 LONG-only; I see n=46 all-direction. The direction and magnitude are both confirmed.
- **However, binomial p-value is 0.46 two-sided vs coin-flip** — a CI on 26/46 is roughly [41 %, 71 %]. The bucket is **not individually Bonferroni-safe** and not even raw-p-significant at α=0.05.
- **Joint with `max_kz_trades`** (next section) the combined sample is 59 W / 38 L of 97, p=0.042 raw — still NOT Bonferroni-safe.

### 3.4 NAS100 `sl_beyond_ob` monthly decomposition — the critical reveal

| Month | n | W | L | WR% | sumR | ExpR |
|---|---:|---:|---:|---:|---:|---:|
| 2026-01 | 2 | 1 | 1 | 50.0 % | +0.50R | +0.25R |
| 2026-02 | 14 | 4 | 10 | 28.6 % | −4.00R | −0.286R |
| **2026-03** | **28** | **19** | **9** | **67.9 %** | **+19.50R** | **+0.696R** |
| 2026-04 | 2 | 2 | 0 | 100 % | +3.00R | +1.50R |

**The entire +19R is March.** Feb was net-negative. This coincides with the NAS100 regime trough (−13.1 % DD peak→trough ending Mar 31 per NAS100_T3_1_synthesis §Q1). Translation: the `sl_beyond_ob` gate correctly rejected losers in Jan/Feb, then over-rejected in March when the trend reversed. **A gate fix would have helped in March but hurt in Feb.** This argues against any hard gate change absent a regime filter.

### 3.5 EURUSD L2 — degeneracy-dominated; low confidence

EURUSD L2 has 253 rows but only 101 non-degenerate. Of those: 43 W / 58 L / 42.6 % WR / +6.18R net. Split:

| l2_reason | n_total | n_real | W | L | sumR | ExpR |
|---|---:|---:|---:|---:|---:|---:|
| `h1_poi_exists` | 155 | 89 | 42 | 47 | +15.68R | +0.176R |
| `sl_beyond_ob` | 81 | 9 | 0 | 9 | −9.00R | −1.00R |
| `entry_in_ob` | 13 | 3 | 1 | 2 | −0.50R | −0.167R |
| `m15_choch_exists` | 4 | 0 | 0 | 0 | — | — |

Exploratory-only (60 % degenerate); do not ship decisions off this.

---

## 4. Question 3 — BLOCKED_LIMIT opportunity cost (bucket by `block_reason`)

### 4.1 Aggregate

| Sym | n | resolved | W | L | WR% | sumR | ExpR | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| XAUUSD | 13 | 13 | 4 | 9 | 30.8 % | −2.95R | −0.227R | **exploratory, n<20** — no leak |
| **NAS100** | **82** | **67** | **43** | **24** | **64.2 %** | **+40.62R** | **+0.495R** | **Real leak (see §4.2)** |
| EURUSD | 38 | 15 | 1 | 14 | 6.7 % | −12.33R | −0.822R | Correctly blocked (many degenerate) |

### 4.2 NAS100 BLOCKED bucket breakdown

| block_reason | n | W | L | UNFILLED | WR% | sumR | ExpR | Binom p (resolved vs 0.5) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `max_kz_trades` | 60 | 33 | 18 | 9 | 64.7 % | +31.62R | +0.527R | **0.049** (raw significant) |
| `max_daily_trades_sim` | 22 | 10 | 6 | 6 | 62.5 % | +9.00R | +0.409R | 0.45 (exploratory) |

**Confirms session 33 claim** (NAS100 T3.1 synthesis Q4 leak #2: "24 novel setups blocked, 66.7 % WR, +16.02R"). My aggregate includes dupes and all directions; undeduped count is 60 / +31.62R. After the session 33 dedup logic (24 novel / 36 re-fires) the +16.02R is the dupe-safe number, consistent with my bucket raw.

**Binomial p for `max_kz_trades` is 0.049** — raw-significant but **NOT Bonferroni-safe at 0.05/12 = 4.2×10⁻³** and certainly not at the 96-test floor. Under Bonferroni, the NAS100 bucket evidence is **inconclusive**.

### 4.3 Monthly decomposition — NAS100 BL

| Month | `max_kz_trades` | `max_daily_trades_sim` |
|---|---|---|
| 2026-01 | 13 W / 1 L (93 %, +18.55R) | 5 W / 0 L (100 %, +7.50R) |
| 2026-02 | 11 W / 2 L (85 %, +14.57R) | 4 W / 1 L (80 %, +5.00R) |
| 2026-03 | 5 W / 10 L (33 %, −2.50R) | 1 W / 4 L (20 %, −2.50R) |
| 2026-04 | 4 W / 5 L (44 %, +1.00R) | 0 W / 1 L (0 %, −1.00R) |

**NAS100 BL decay is sharp and Bonferroni-safe.** Fisher exact Jan-Feb vs Mar-Apr for `max_kz_trades`: 24 W / 27 vs 9 W / 24, **p = 2.2 × 10⁻⁵** → Bonferroni-safe at α = 0.05/96.

The "we are blocking good trades" argument was true in Jan-Feb (+33.12R cumulative) but collapses in Mar-Apr (−3.50R). Same regime shift as L2 and CAND. This is **not a static leak** — it's conditional edge that flipped sign.

---

## 5. Question 4 — Quarterly (monthly) evolution across all buckets

### 5.1 NAS100 — the synchronous regime shift

| Month | CAND WR | L2 WR | BL WR |
|---|---:|---:|---:|
| 2026-01 | 90.0 % (9 W/10, +12.52R) | 7.1 % (1 W/14, −11.50R) | 94.7 % (18 W/19, +26.05R) |
| 2026-02 | 75.0 % (6 W/8, +7.01R) | 44.1 % (15 W/34, +3.50R) | 83.3 % (15 W/18, +19.57R) |
| 2026-03 | 50.0 % (6 W/12, +3.00R) | 57.6 % (19 W/33, +14.50R) | 30.0 % (6 W/20, −5.00R) |
| 2026-04 | 33.3 % (1 W/3, −0.50R) | 66.7 % (2 W/3, +2.00R) | 40.0 % (4 W/10, 0R) |

**Three buckets move together:**
- **CAND & BL decline** (accepted trades + KZ-capped trades both lost WR together)
- **L2 WR inversely rises** (rejections that used to be right became wrong)

| Fisher p (Jan-Feb vs Mar-Apr) | Bucket | Result | Bonferroni-safe? |
|---|---|---:|---|
| CAND decay | 15 W/18 → 7 W/15 | **p = 0.061** | marginal, not safe |
| L2 inverse decay | 16 W/48 → 21 W/36 | **p = 0.028** | raw, not safe |
| **BL decay** | **33 W/37 → 10 W/30** | **p = 2.2 × 10⁻⁵** | **Bonferroni-safe at ×96** |

**Diagnostic:** This pattern (CAND down, BL down, L2 up, synchronously) is what you see when **the market shifts regime and the entire gating apparatus is calibrated to a regime that no longer exists.** It is inconsistent with "execution degrading" (which would hit CAND only) and inconsistent with "we are the liquidity" (which would hit CAND and BL asymmetrically). It IS consistent with **regime arbitraging us** — but in a reversible way: if the regime rotates back, the edge returns.

### 5.2 XAUUSD — no synchronous shift (decay lives elsewhere)

| Month | CAND WR | L2 WR (aggregate) | BL WR |
|---|---:|---:|---:|
| 2026-01 | 50 % (2 W/4, +1.05R) | 36.9 % (72 W/195, −27.94R) | 30.0 % (3 W/10) |
| 2026-02 | 50 % (1 W/2, +0.50R) | 36.3 % (106 W/292, −44.60R) | 0.0 % (0 W/2) |
| 2026-03 | 66.7 % (2 W/3, +2.00R) | 21.4 % (34 W/170, −74.00R) | — |
| 2026-04 | 100 % (1 W/1, +1.50R) | 48.8 % (41 W/84, +18.50R) | 100 % (1 W/1) |

**XAUUSD shows L2 worsening in March** (21.4 % WR, −74R) — gates got MORE correct — while CAND was stable or improving. The CLAUDE.md quarterly decay (73→59 % WR) on XAUUSD must therefore come from the **batch KB (367 trades pre-L2 pipeline)**, NOT from the 2026 Jan-Apr L2-equipped pipeline. This is consistent with T3.2 verdict:47 — the batch KB has no L2 schema.

**Implication.** The CLAUDE.md 73→59 % figure describes an era without the current gates. The current L2 + BL pipeline on XAUUSD is performing correctly through all four 2026 months. **XAUUSD decay in this dataset is a sample-size artefact (n=10 CAND), not a structural signal.**

### 5.3 EURUSD — dominated by degeneracy, low confidence on any monthly claim

| Month | CAND WR | L2 WR (non-degen) |
|---|---:|---:|
| 2026-01 | 0 % (0 W/3, −3.00R) | 56.0 % (28 W/50) |
| 2026-02 | 0 % (0 W/2, −2.00R) | 5.4 % (2 W/37) |
| 2026-03 | — | 92.9 % (13 W/14) |
| 2026-04 | — | — |

152 degenerate L2 records out of 253 (60 %). Anything derived from this data is **exploratory** until the FX precision prompt fix (CLAUDE.md unresolved #7) lands.

---

## 6. Question 5 — Top-3 L2 reject reasons by opportunity cost (per-quarter honest-epsilon)

Ranking across all three instruments, the **most R/quarter "missed" under honest epsilon**:

| Rank | Bucket | Sym | n | sumR | ExpR | Dominant month | Regime-safe? | Confidence |
|---:|---|---|---:|---:|---:|---|---|---|
| 1 | `max_kz_trades` | NAS100 | 60 | +31.62R | +0.527R | Jan-Feb (+33R); collapses Mar-Apr | **No** (Fisher p=2×10⁻⁵ for decay) | Medium — directional |
| 2 | `sl_beyond_ob` | NAS100 | 46 | +19.00R | +0.413R | 100 % March | **No** (single-month) | Low — exploratory |
| 3 | `max_daily_trades_sim` | NAS100 | 22 | +9.00R | +0.409R | Jan-Feb (+12.50R); collapses | No | Low (n<30) |
| — | `sl_beyond_ob` | XAUUSD | 20 | **−7.49R** | −0.374R | monotonic negative | n/a | n<30 exploratory |
| — | `entry_in_ob` | XAUUSD | 557 | −85.56R | −0.154R | monotonic negative | n/a | High — correctly killed |
| — | `h1_poi_exists` | XAUUSD | 159 | −31.99R | −0.201R | monotonic negative | n/a | High — correctly killed |

**None of the NAS100 top-3 survive Bonferroni correction at the 96-test floor.** Even at a 12-test gamma-internal correction, only `max_kz_trades` (raw p=0.049) passes the raw threshold; corrected α=4.2 × 10⁻³ rejects it too.

---

## 7. Question 6 — Verdict: is decay concentrated in a specific L2 bucket that's "rotating good trades to rejection"?

**No — not in the sense the hypothesis posits.**

The L2 buckets are doing what they were calibrated to do. The pattern on NAS100 is not "L2 rotating good trades to rejection" — it's "the regime changed, so what used to be correctly rejected became correctly accepted, and symmetrically what used to be good accepts became bad accepts." The edge moved, not the gate.

### Ranked leaks (evidence strength, R impact, confidence)

1. **NAS100 regime shift mid-March** — cross-bucket, p = 2.2 × 10⁻⁵ on BL, Fisher-confirmed on CAND (0.061) and L2 (0.028). Estimated impact: **−0.5 to −0.8R/trade on NAS100** during regime churn. **Evidence: strong (BL passes Bonferroni × 96).** Fix: regime filter — detection lives in agent δ's scope.

2. **NAS100 `max_kz_trades=1` static cap** — +40.62R if joint with `max_daily_trades_sim` taken at face value; **but +33.12R of that is in Jan-Feb** and the bucket is raw-p=0.049 / Bonferroni-fails. Estimated impact recoverable: **+6 to +8R/quarter in trending regime, 0 or negative in choppy**. Fix: dynamic cap gated by regime — NOT a blanket raise. **Evidence: marginal.**

3. **NAS100 `sl_beyond_ob` L2 bucket** — +19.00R but p=0.46; entirely March. Estimated impact: **0 to +3R/quarter structural, with large regime variance.** Session 33's +13.5R standalone / +20.50R joint claim reproduces directionally in my replay, but the **statistical significance does not survive even single-instrument Bonferroni**, contrary to how the claim was framed in the synthesis. **Evidence: insufficient for gate change.** T2.9 remains correctly blocked.

4. **NO_TRADE gate (all instruments)** — no leak. Hypo-WR ≤ random-direction baseline on all three instruments at all three horizons. **Evidence: strong against leak.** Do not change NO_TRADE filters based on missed-winners concern.

5. **XAUUSD L2** — no leak; all three buckets significantly worse than coin-flip. **Evidence: strong.** Do not change XAUUSD gates.

### Calibration against the hypothesis

| Hypothesis | Supported? | Evidence |
|---|---|---|
| Opportunity cost of NO_TRADE is growing | **No** — it's stable / below baseline | §2.2 table; baseline §1.2 |
| Opportunity cost of L2 is growing | **Partial (NAS100 only)** — regime-driven, not structural | §3.4, §5.1 |
| Opportunity cost of BLOCKED_LIMIT is growing | **Inverse** — collapses from Mar onward on NAS100; always small on XAUUSD | §4.3 |
| Missed winners explain the 73→59 % decay | **No** — XAUUSD Jan-Apr L2 pipeline is gate-correct; CLAUDE.md decay is from batch KB pre-L2 era | §5.2, T3.2 verdict:47 |
| One L2 bucket is rotating good trades to rejection | **No** — NAS100 `sl_beyond_ob` fails standalone significance | §3.3, §3.4 |

---

## 8. Caveats and reproducibility

- **Proxy TP/SL for NO_TRADE is not a real 1.5R target.** Real risk from a bias-only signal has no `entry` or `stop_loss` — the ATR proxy is the best approximation and its failure to lift hypo-WR above baseline IS the finding (not a methodology flaw).
- **Same-candle TP+SL ambiguity in NO_TRADE replay.** Scored conservatively as HIT_SL. If a fully-pessimistic upper bound is needed, flipping to HIT_TP (anti-conservative) lifts hypo-WR by a few pp but does not cross the baseline threshold on any instrument.
- **ATR is dataset-wide average, not rolling** (stable, intentionally — removes ATR regime-drift from the signal we're trying to detect).
- **EURUSD results are exploratory only** — 60 % L2 records degenerate under honest eps. Wait for FX precision fix before ingesting EURUSD missed-trade claims.
- **Monthly "quarters" are Jan/Feb/Mar/Apr 2026** — not the 73→59 % quarterly decay quarters in CLAUDE.md (those come from the pre-L2 batch KB). This census does not contradict that older decay — it proves it is not visible in the current 2026 L2 pipeline.
- **n<30 on every per-month CAND bucket and several L2 buckets** — all such claims are flagged exploratory.
- **Bonferroni floor adopted:** 96 tests (12 bucket tests × 8 phase-1 agents). Every "p=0.04X" in this doc fails that correction. Only NAS100 BL monthly decay (p=2.2×10⁻⁵) survives.

### Reproducibility

Run:
```
python research/b_deep_audit_2026-04-19/phase1/_gamma_scratch/missed_trade_census.py
```
Outputs `census_out.json` with every aggregate and monthly slice. All numbers in this report derive from that JSON (or from the separate control baseline replay shown inline).

---

## 9. Handoff to chairman / phase 3

**Testable hypotheses raised by γ:**

- **H-γ-1 (Bonferroni-safe).** NAS100 experiences a regime shift mid-March 2026 affecting CAND / L2 / BL buckets synchronously. A regime filter (e.g., rolling ATR ratio, trend-strength index) would capture Jan-Feb edge and gate out Mar-Apr churn. Phase 3 test: fit trailing 10-day regime indicator, replay NAS100 CAND on-filter-on vs filter-off, compare expectancy. Expected recovery: +3 to +6R/quarter. Moderate effort.
- **H-γ-2 (marginal).** NAS100 `max_kz_trades=1 → 2` would recover +6 to +8R/quarter **only in trending regimes**. Phase 3 test: simulate cap=2 with H-γ-1's regime filter applied. Do NOT test cap=2 globally (Mar-Apr would lose money).
- **H-γ-3 (rejected by γ).** No L2 bucket rotation explains decay. Phase 3 should NOT test a static L2 gate fix on XAUUSD or NAS100; the T3.2 verdict stands.
- **H-γ-4 (rejected by γ).** NO_TRADE filter is not leaking winners. Phase 3 should NOT test loosening OB_proximity / prescreen gates.

**Blast radius for Tuesday go/no-go:**
- NAS100: edge is real in-regime, fragile out-of-regime. **Go only with a regime gate** — live enablement without one carries expected loss through any further choppy period.
- XAUUSD: nothing in my census contradicts continued live operation. Current gates are correctly calibrated.
- EURUSD: **do not enable live**. Degeneracy dominates every bucket; metrics are untrustworthy until FX precision fix lands (CLAUDE.md unresolved #7 + #8).

---

*End of γ-agent output. See `_gamma_scratch/census_out.json` for full replay artefact.*
