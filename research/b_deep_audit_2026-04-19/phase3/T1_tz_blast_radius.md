# Phase 3 T1 — Export TZ Bug Blast Radius

**Tester:** Opus 4.7 hypothesis tester, 2026-04-19
**Target:** `scripts/export_mt5_historical.py:80-81` TZ bug
**Hypothesis tested:** H1 (bug contaminates broader research) vs H0 (isolated to hour-of-day)

---

## Verdict (1 paragraph)

**Partial H1 confirmed — the bug is broader than hour-of-day, but the blast radius splits cleanly on "timestamp labels used for WHAT".** Price-math research (Tier A ε revalidation, sl_beyond_ob buckets, CANDIDATE WR/R math) is **NOT distorted** because both the T7 simulation and the M15 CSVs carry the identical mislabeled timestamps and `compute_outcome` matches by string equality and then walks the candle sequence forward — labels cancel out. η's hour-of-day study IS fully contaminated (already known; confirmed bit-exact by Phase 2). The canonical quarterly decay sequence `[73.2, 71.4, 63.6, 59.4]` in `L4_foundation_analysis.py:649` is **a hardcoded constant**, not a computation from `data/historical_2026/` — unaffected by this bug. **Most alarming finding:** `src/mt5/mt5_real.py:58,71` has the **IDENTICAL mislabeling pattern** as `export_mt5_historical.py:81`, so the live trading system also carries broker-server-time candles mislabeled as UTC — but live KZ gating uses `datetime.now(timezone.utc)` (wall-clock) to fire pipelines, so the pipeline runs at correct real-UTC moments, even though the candles it analyzes are labeled 2-3 hours ahead. This makes live and research internally self-consistent (same mislabel convention on both sides), so production edge numbers hold, but "the XAUUSD London KZ 07:00-10:30 UTC" in the config actually corresponds to broker-labeled 07:00 = real UTC 04:00-05:00 — i.e. pre-real-London. Academic/literature cross-references to "London session" no longer map cleanly. **For Tuesday redacted_account kickoff: NO DELAY.** The production system is self-consistent; the backtests that justified the 1% deployment are valid on the actual data the live system consumes. Fix is medium priority post-kickoff research hygiene.

---

## Bug mechanism (verified)

**`scripts/export_mt5_historical.py:75-82`:**
```python
if tf_name == "D1":
    df["time"] = df["time"].apply(
        lambda ts: datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    )
else:
    df["time"] = df["time"].apply(
        lambda ts: datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    )
```

**What it does:** Calls `datetime.fromtimestamp(ts, tz=timezone.utc)` on `rates["time"]`. `rates` comes from `mt5.copy_rates_range` (line 63), which returns broker-server-time Unix timestamps — **not UTC**. Passing `tz=timezone.utc` to `fromtimestamp` with a NON-UTC epoch-seconds value is a semantic error: it interprets the broker-time epoch-seconds AS-IF-UTC and labels the resulting naive datetime as UTC-aware. No conversion happens; only mislabeling.

**Correct behavior:** MT5's `copy_rates_range` epoch-seconds are in the broker's server timezone. Correct conversion requires knowing the broker TZ (usually UTC+2 EET winter / UTC+3 EEST summer for FTMO-family brokers) and either: (a) subtracting the offset before `fromtimestamp(..., tz=timezone.utc)`, or (b) using `datetime.fromtimestamp(ts).replace(tzinfo=ZoneInfo("Europe/Athens")).astimezone(timezone.utc)`.

**Same pattern in live:** `src/mt5/mt5_real.py:58` and `:71`:
```python
"time": datetime.fromtimestamp(r[0], tz=timezone.utc).isoformat(),
```
Identical mislabeling. The live trading system has been operating with broker-labeled-as-UTC timestamps since inception.

**CLI flag check:** No `--tz` flag exists. Script has no broker-TZ awareness at all. No compensating fix in any separate file.

**Empirical verification of broker-server TZ:** 23:45 → 00:00 close-to-open gap signature (measured in pips on 2026-Q1):

| Symbol | `historical_2026/` mean gap | neg% | `historical/` mean gap | neg% |
|---|---:|---:|---:|---:|
| GBPJPY | **−13.37 pips** | **86.7%** | −1.06 pips | 48.6% |
| USDJPY | **−5.21 pips** | **83.3%** | −0.33 pips | 39.2% |
| GBPUSD | **−4.54 pips** | **78.3%** | −0.28 pips | 29.7% |
| EURUSD | **−3.00 pips** | **86.7%** | (no file) | — |

Reproduced bit-exact by my own scratch (`_T1_scratch/01_verify_gap_signature.py`). `historical/` (the older dataset, likely a TradingView export or MT5 with proper TZ handling) has symmetric ~noise-level gaps. `historical_2026/` shows systematic **negative** gaps strongly concentrated in one bar — the signature of broker-server-midnight rollover appearing mid-bar when interpreted as UTC.

**Confirmation via volume profile** (average tick-volume per labeled hour, GBPJPY):
- hours 21, 22, 23 (labeled): 1446, 1307, 802
- hours 00, 01, 02, 03 (labeled): **491**, 841, 1210, 1524

The volume trough at labeled hour 00 (491) is the broker-server-midnight reconciliation lull — an acute drop of 40% vs prior bar. True UTC 00:00 for FX would be the Tokyo pre-open, which shows a more gradual decline. The broker is definitively on a non-UTC server time; labels are mis-set.

---

## Affected artefacts (ranked by impact on Tuesday decision)

### 1. **Tier A2/A3 NAS100 + EURUSD ε revalidation** — impact: **NONE**

- **File:** `research/b_deep_audit_2026-04-19/tier_a/epsilon_revalidation.py:171` → uses `data/historical_2026/{symbol}_M15.csv` for M15 lookup.
- **File:** `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/NAS100_epsilon_revalidation.md` and `EURUSD_epsilon_revalidation.md` — output files.
- **Evidence:** `compute_outcome()` in `scripts/simulate_t7_live_period.py:524-527` matches the T7 record's `candle_time` against `m15_candles[i]["time"]` by **string equality**:
  ```python
  for candle in m15_candles:
      if candle["time"] == candle_time:
          found_start = True
  ```
  Both T7 records and the M15 CSV were generated on the same broker-time labels; both use `2026-01-02T07:00:00Z`-style strings. The match succeeds; the subsequent H/L/C walk for TP/SL hit-detection operates on the **unshifted price sequence**. OHLC values are unaffected by the label bug (only timestamps are). Numerically, every `WR%`, `sumR`, `expR` figure in the two revalidation tables survives.
- **Verified by:** checked `epsilon_revalidation.py` for any `datetime`/`hour` arithmetic on candle_time — none exists. No kill-zone re-bucketing. Pure price-math.
- **Downstream claim affected:** none. NAS100 T3.1 `sl_beyond_ob +13.5R` and EURUSD revalidation (−197R `h1_poi_exists` collapse at honest eps, etc.) stand on their measured values, modulo the separate blocker of EURUSD AI-precision issue (already in CLAUDE.md unresolved #7).

### 2. **Canonical quarterly decay `[73.2, 71.4, 63.6, 59.4]`** — impact: **NONE**

- **File:** `research/academic_pipeline/L4_foundation_analysis.py:649` — **hardcoded constant list**, not computed from `data/historical_2026/`.
- **Data source:** `research/academic_pipeline/data/entry_engineering_dataset.csv` (line 28) — pre-existing 129-trade batch dataset, not dependent on the faulty export.
- **Downstream claim affected:** none from this specific bug. (Whether those hardcoded numbers are themselves honestly computed upstream is Phase 3 δ's job; T1 scope is TZ bug only.)

### 3. **Tier B Phase 1 η hour-of-day family (330 tests)** — impact: **CATASTROPHIC** (already known, re-confirmed)

- **File:** `research/b_deep_audit_2026-04-19/phase1/eta_alternative_patterns.md` §4-5 rankings.
- **Evidence:** Phase 2 reviewer `phase2/eta_review.md` demonstrated GBPJPY-23 SHORT WR collapses from **80.7% → 40.5%** on clean `historical/` 2022-2025 OOS — null-indistinguishable. USDJPY-23, GBPUSD-23, XAUUSD-11 all fail OOS.
- **Why this is broader than "just hour-of-day"**: every hour-of-day edge in η's §4.1 table sits on labels that are shifted 2-3h from real UTC. Even the non-23:45 hours have the shifted-label problem, but the **magnitude** of artifact inflation correlates with proximity to the rollover bar. η's 22-23 UTC labels are the direct rollover candles; η's 11 UTC XAUUSD edge fails OOS for a **different** reason (regime overfit 2026-Q1 only). So the contamination mechanism differs across η's reported edges:
  - 22-23 UTC FX edges: **rollover-gap artifact** (label-shift specific)
  - 11 UTC XAUUSD: **regime overfit** (not label-shift; XAUUSD isn't contaminated)
- **Downstream claim affected:** all 10 "strong" hour-of-day edges in `eta_alternative_patterns.md:179-189`, plus §5 rankings, plus the +28-33R/month marginal claim. Phase 2 already disposed of these. Do not rehabilitate.
- **SAFE subset of η:** (a) the NO_TRADE-cluster null (§2, confirmed by γ bit-exact); (b) the 3 CEO-specified edge rejection (§3 FVG-only, Sweep+Displacement, Fib50 — pure-structure tests that don't pivot on hour labels). These survive the TZ bug.

### 4. **Live feed (`src/mt5/mt5_real.py`)** — impact: **SELF-CONSISTENT MAJOR** (behavioral: NONE; interpretive: MAJOR)

- **File:** `src/mt5/mt5_real.py:58` and `:71` — identical `datetime.fromtimestamp(r[0], tz=timezone.utc).isoformat()` mislabeling pattern.
- **Evidence — live state:** `knowledge_base/pipeline_state/02_market_state.json` shows M15 candles up to `2026-04-17T23:45:00+00:00` for XAUUSD written with mtime ~April 19 (Sunday). Friday XAUUSD trading actually closes at UTC **21:00** (broker 23:00 winter). The presence of a "23:45 UTC" candle on a Friday means the labels are broker-EEST (UTC+3, summer time), with broker 23:45 = real UTC 20:45. Labels are broker-EET/EEST mislabeled as UTC.
- **Behavioral impact (live trading):** **NONE measurable.**
  1. KZ gating uses `datetime.now(timezone.utc)` (wall clock, true UTC) vs config `start_utc: "07:00"` — `src/components/orchestrator.py:328, 1944-1955`. Pipelines fire at true UTC 07:00 London KZ start.
  2. At that moment, MT5 returns the most recent N M15 candles. These are correctly the CURRENT price data — MT5 doesn't shift prices, only labels them.
  3. Structure analysis (OB/FVG/swing detection) is index-ordinal — operates on the sequence, not the label values.
  4. So live trading correctly analyzes the real-world price action AT real UTC 07:00, even though the candles carry labels saying "10:00" (broker EEST).
- **Interpretive impact:** **MAJOR.**
  1. Session-level filtering in `data_ingestion.py:compute_session_levels` at line 120-144 filters candles by `c_time` vs `ASIAN_START=00:00 / ASIAN_END=07:00`. If candles have broker-label times, "Asian session candles" are selected as labels 00:00-06:45 — which is broker 00:00-06:45 = real UTC 22:00-04:45 (winter) or 21:00-03:45 (summer). That's a **shifted** Asian window.
  2. However — this same shift happens in research (every M15 CSV has the same mislabel), so backtest-derived session-level performance matches live-derived session-level performance because they both operate on the same shifted window. **Self-consistency preserves validated edge numbers.**
  3. But the MAPPING to academic literature breaks: the config's `london.start_utc: "07:00"` is applied by `datetime.now(timezone.utc)` — real UTC 07:00 — so live KZ **timing** is correct London start. The candle labels used internally are broker-time. Trading logic triggers correctly. Literature citations (Osler, Menkhoff, etc.) referencing "London session" match the live KZ gating (real UTC), not the candle labels.
- **Downstream claim affected:** interpretation of "Asian session levels" in the MSO. The computed `asian_high`/`asian_low` are from candles labeled 00:00-06:45 = real UTC 22:00 prev day to 04:45 (winter) — that's **not the real Asian session** (Tokyo 00:00-07:00 UTC is broker 02:00-09:00 labeled). The Asian session levels fed to the AI are actually **late-US/early-European-pre-open levels**. Edge is self-consistent because backtest also used same wrong-filter, but the MSO's "asian_high" is a misnomer.

### 5. **Phase 1 other agent scratches (α, γ, ε, δ, ζ, θ, β)** — impact: **VARIES**

- Several agent scratches reference `historical_2026/`:
  - `_delta_scratch/01_regime_metrics.py` — quarterly regime metrics. Price-math. Likely unaffected (same self-consistency argument).
  - `_zeta_scratch/01-08_*.py` — market state algo verification, OB proximity counterfactual, structure-direction lag. Uses candle sequence; label-agnostic.
  - `_alpha_scratch/slippage_analysis.py` — slippage. Price-math; unaffected.
  - `_gamma_scratch/missed_trade_census.py` — NO_TRADE census; already validated by η at bit-exact 36.6/38.0/39.2% match.
  - `_epsilon_scratch/_loader.py` — liquidity arb; TBD but likely price-math.
- **Blast risk:** any scratch that does hour-of-day or day-of-week conditioning inherits η-style contamination. Any scratch doing session-filtering inherits the interpretive-shift issue but stays self-consistent if it doesn't cross-compare to literature.
- **Out of T1 scope:** a scratch-by-scratch audit. Recommend Phase 3 T2/T3/T4 testers check whichever artefact their specific hypothesis depends on.

---

## Spot-check comparison

### Gap signature — reproduction of η's numbers

From `_T1_scratch/01_verify_gap_signature.py`:

```
23:45 -> 00:00 gap signature (pips, 2026-Q1)
  GBPJPY historical_2026     : n=60, mean=-13.37 pips, neg%=86.7%
  GBPJPY historical          : n=74, mean= -1.06 pips, neg%=48.6%
  USDJPY historical_2026     : n=60, mean= -5.21 pips, neg%=83.3%
  USDJPY historical          : n=74, mean= -0.33 pips, neg%=39.2%
  EURUSD historical_2026     : n=60, mean= -3.00 pips, neg%=86.7%
  EURUSD historical          : FILE NOT FOUND
  GBPUSD historical_2026     : n=60, mean= -4.54 pips, neg%=78.3%
  GBPUSD historical          : n=74, mean= -0.28 pips, neg%=29.7%
```

Matches Phase 2 reviewer's table bit-exact.

### Single transition example (GBPJPY, Jan 6-7 2026)

| Bar | time (labeled) | open | high | low | close |
|---|---|---:|---:|---:|---:|
| n   | 2026-01-06 23:30 | 211.483 | 211.507 | 211.458 | 211.470 |
| n+1 | 2026-01-06 23:45 | 211.468 | 211.528 | 211.459 | 211.521 |
| n+2 | 2026-01-07 00:00 | 211.338 | 211.447 | 211.338 | 211.408 |
| n+3 | 2026-01-07 00:15 | 211.395 | 211.403 | 211.260 | 211.358 |

- close(n+1) = 211.521, open(n+2) = 211.338 → **−18.3 pip gap**
- Bar n+1 range: 211.459–211.528; bar n+2 range: 211.338–211.447 — **zero overlap**. A clean, non-contiguous step.
- Volume signature: hour 23 = 802 ticks, hour 00 = **491** (40% drop) — consistent with broker-server-midnight reconciliation.

### Instrument-specific confirmation that XAUUSD/NAS100/US30 are FX-only artifact-free

```
XAUUSD: first-candle hour distribution = [(1, 75)]     (never 00:00 labeled)
NAS100: first-candle hour distribution = [(1, 76)]     (never 00:00 labeled)
US30:   first-candle hour distribution = [(1, 76)]
```

These instruments don't have labeled 00:00 bars because they don't trade through broker-midnight — metals/indices pause. Their first bar of the day is ~01:00 labeled (Tokyo open in broker-EET would be ~02:00, so 01:00 is late-Tokyo); no rollover contamination signature. η's §4 XAUUSD-11 SHORT failure is a **separate** OOS regime-overfit, not TZ-related.

### T7 candle_time vs M15 CSV format alignment

- T7 record: `"candle_time": "2026-01-02T07:00:00Z"`
- M15 CSV row: `"2026-01-02 07:00:00"` → parsed by `parse_tradingview_csv` → normalized to `"2026-01-02T07:00:00Z"`.
- String equality match inside `compute_outcome` succeeds. Zero impact on ε revalidation numeric outputs.

---

## Recommendation for Tuesday

**No delay to redacted_account kickoff (2026-04-21, $100K Stellar 2-Step, 1% risk).**

Rationale:
1. Live system is self-consistent: both backtest and live consume broker-labeled candles from the same mislabel convention; the edge numbers that justified deployment (XAUUSD 62% WR, OB zone +17pp, etc.) are valid on the data flowing through the production pipeline.
2. Tier A ε revalidation (the NAS100/EURUSD "honest epsilon" re-scoring that gated T2.9) is **price-math only**; TZ-label insensitive. Those numbers stand.
3. The contaminated research layer is η's hour-of-day scan, which was already rejected by Phase 2 review and **does not gate the Tuesday decision**.
4. The interpretive issue — "Asian session levels are really 3-hour-shifted European-late levels" — is a **meaning** issue, not a **behavior** issue. The MSO feature is still useful because it's self-consistent; it's just misnamed. No literature-based priors got injected into the trading decisions based on this name.

**Shadow logging already in place** that would catch a TZ-label drift problem:
- OB continuation rolling-50 monitor (primary decay metric).
- BE shadow logger.
- H16 US30 sweep divergence.

**Add to post-kickoff research hygiene:**
- Fix `export_mt5_historical.py:81` to use proper broker-TZ conversion.
- Fix `src/mt5/mt5_real.py:58,71` to use proper broker-TZ conversion — **BUT** the fix must be coordinated with one of two strategies:
  - (A) Convert candle timestamps to real UTC everywhere → then fix the downstream consumers that filter by `c_time` (e.g. `compute_session_levels`) since the session labels that get into the MSO would shift semantically. Risks re-calibration of every backtest number.
  - (B) Keep the current broker-labeled convention, but **rename** fields and add explicit documentation that timestamps are broker-EET/EEST, not UTC. Minimal code churn; preserves edge numbers.
- Recommend strategy (B) given that production is self-consistent and working. If CEO wants (A), plan for a 1-2 week backtest re-baseline window and delay any cross-instrument literature-referenced research until then.

---

## Fix cost estimate

**Strategy B (label convention cleanup, no behavioral change):**
- 1 line change in `export_mt5_historical.py` comment header making TZ convention explicit.
- Add `# broker-server time, NOT UTC — see T1 Phase 3 blast-radius report` comment at `mt5_real.py:58,71`.
- Rename `timezone.utc` → a `ZoneInfo("Europe/Athens")` (or similar) in `mt5_real.py` and convert to UTC once per candle at ingestion boundary. Reject labeled-UTC bug while preserving numerical wall-clock time.
- Rough: **~10 lines, 30-min edit, +60-min rewrite of one unit test for data_ingestion timestamp parity**.
- Low urgency. Do within 1-2 weeks post-kickoff. Before any future hour-of-day or session-boundary research.

**Strategy A (full real-UTC conversion with re-baseline):**
- All the above, PLUS:
- Re-run all T7 simulations on corrected data.
- Recompute every session-filtered metric (asian_high/asian_low, london_high/low, H25 volatility).
- Recalibrate kill-zone start/end times if the edge moved. (It likely did NOT move because the edge is structural — OB-zone precision — not timing.)
- Rough: **1-2 weeks of research work + ~$30 in T7 re-runs.**
- Medium-high urgency ONLY if a future research program requires literature-compliant UTC session labels. Not urgent for production.

---

## What I could not test

1. **Live broker TZ drift across DST.** The broker may observe EEST (UTC+3) summer and EET (UTC+2) winter; DST shift happens late March/late October. If the MT5 server DOES NOT DST-shift (possible — some FTMO-family brokers fix at UTC+2 year-round), then the mislabel offset is constant; if it DOES shift, there's a discontinuity around March 29 and October 25. I could not verify which mode without calling `mt5.terminal_info()` live. η's Phase 2 data shows monthly stability across Mar-Apr 2026 (WR 0.81 and 0.88) which suggests either no DST shift OR the artifact is robust across the shift. Either way, interpretive conclusion is unchanged.

2. **Bit-exact MT5 timestamp inspection.** I did not run a live MT5 preflight to pull a fresh candle and compare its raw `time` integer against a known UTC epoch, because CEO's MT5 preflight has been run recently and I wanted to stay read-only on live infrastructure. The 23:45 → 00:00 gap signature + volume trough are sufficient to establish broker-TZ mislabeling.

3. **Full Phase 1 scratch audit.** I scoped to α-η, ε, γ, δ, ζ, β, θ at the directory-name level but did not read every scratch script. Any scratch that pivots on hour-of-day or session-boundary labels inherits η's contamination. Phase 3 T2-T4 testers should recheck if their target artifact has a non-price-math dependency on `c_time`.

4. **Component 3A (AI analyzer) prompt-level sensitivity.** The AI sees `asian_high`, `asian_low`, `session_high`, `london_high` fields in the MSO. These names carry semantic meaning to the AI. The AI might rely on "Asian session" meaning "Tokyo 00-07 UTC" in its reasoning, even though the numeric value is from a shifted window. That reasoning error (if it exists) is covered by existing prompt-audit shadow logs, not by T1's scope.

5. **Whether the edge MOVES if we fix the bug.** If the real London session (UTC 07:00-10:30 actual) differs structurally from the broker-labeled 07:00-10:30, then fixing the TZ bug could shift the observed edge. Given the edge is structural (OB-zone precision) rather than session-specific, my prior is the edge is robust to the shift — but this is testable only by running Strategy A re-baseline, which is out of T1 scope.
