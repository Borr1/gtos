# GBPUSD Observer-Mode Promotion Review

**Date:** 2026-04-25
**Author:** Claude Code (Opus 4.7) — Tier 1 Agent #4 / instrument_expansion sprint
**Purpose:** End-of-April review per memory `project_gbpusd_observer_cost.md` (CEO 2026-04-18 deferred this decision to month-end)
**Verdict (TL;DR):** **EXTEND-OBSERVER (until prompt v2 + v2 detector accumulates ≥20 post-fix CANDIDATEs with <20% L2-reject rate)**

---

## Executive summary

GBPUSD has run as a paid observer (no live `mt5.order_send`) since at least 2026-04-18 — formalized by Gate 0.5 `trading_enabled: false` in `config/agent_config.yaml` on 2026-04-24 (`research/gbpusd_observer_mode_decision_2026-04-24.md`). The original promotion criteria (≥20 post-fix CANDIDATEs, <20% L2 reject, ≥30% sustained CR, CEO end-of-April review) are **NOT met**:

- **154 M15 evaluations / 29 CANDIDATEs over 10 trading days** → 18.8% CR rate (Wilson 95% CI [13.4, 25.7]). Above CR target ✓.
- **Trade_records n=28 with full SL/TP fields. L2-pass rate = 14/28 = 50%, L2-reject rate = 50%, far above the <20% target.** ✗
- **L2 rejection cause = `sl_beyond_ob` 12/14, `entry_in_ob` 3/14.** Post-FA-2 (Apr 20+) the rate WORSENED, not improved: pre-FA-2 L2 PASS 58.8%, post-FA-2 L2 PASS 36.4%. The FA-2 sl_buffer fix introduced inverted-TP geometries (54.5% of post-FA-2 records have SL above entry for LONG).
- **All 28 records are LONG.** v1 detector bullish-only bias (CLAUDE.md item 4) — would unlock SHORT under v2, but v2 isn't yet promoted to production for GBPUSD.
- **Forward-resolved trade outcomes give n=1 realized fill (1 TP, +1.5R) on the L2-pass subset.** Stale-OB anchoring on the 1.34616 entry (Apr 14-22, 16/28 records) blocks 13/14 L2-pass records from ever filling — the AI references an OB price that's now 50-100 pips below market and never returns.
- **Mechanical OB-retest backtest (n=287 across Jan-Apr 2026):** WR 57.1% [51.4, 62.7], Exp R +0.429R/trade, Total +123R. April-only WR drops to 48.6% (n=70), consistent with the same H1→H2 decay seen across XAUUSD/USDJPY in CLAUDE.md items 9 + 11.

**Bottom line:** the promotion gate is failing on the variable that matters most — L2-reject rate is 50% vs 20% target, and is regressing not improving post-FA-2. The headline "n=6, 83.3% WR" historical-batch number used to motivate observer mode in the first place is well below significance threshold and cannot resolve the question. The parallel structural-screen agent (Tier 1 #1, output `01_ranked_candidates.csv`) **rates GBPUSD as REJECT** (composite 52.4, bottom quartile) — its 4-month mechanical OB-WR of 47.6% is materially worse than 7+ other instruments (XAGUSD 59.6%, BTCUSD 61.7%, AUDJPY 54.4%, GBPJPY 55.3%, AUDUSD 53.5%, CHFJPY 53.5%) — which weakens GBPUSD's case as a tradeable instrument vs alternatives. KILL is still too aggressive (the prompt-v2 + v2-detector promotion path has identifiable next steps and ~$10/mo to keep observing is dirt cheap, and structural-screen mechanical WR is computed without AI filter; AI may add edge). PROMOTE-LIVE is reckless (50% L2-reject means 1 in 2 AI CANDs is geometrically broken). EXTEND is the only defensible path until prompt v2 + v2 detector accumulate fresh data.

---

## Section 1: Observer-mode CAND data (live, ~17 calendar days)

### 1A. Coverage

| Date | Total evals | CAND | NO_TRADE | CR % | Notes |
|------|-------------|------|----------|------|-------|
| 2026-04-06 | 30 | 0 | 30 | 0.0% | All `bias=ranging`, no consensus |
| 2026-04-10 | 23 | 0 | 23 | 0.0% | Same |
| 2026-04-13 | 24 | 6 | 18 | 25.0% | First active session |
| 2026-04-14 | 6 | 6 | 0 | 100.0% | All 6 evals were CAND (sparse log) |
| 2026-04-15 | 6 | 2 | 4 | 33.3% | |
| 2026-04-16 | 23 | 0 | 23 | 0.0% | Bias flipped back to ranging |
| 2026-04-17 | 16 | 4 | 12 | 25.0% | |
| 2026-04-20 | 4 | 4 | 0 | 100.0% | First post-FA-2 day; sparse log |
| 2026-04-21 | 17 | 6 | 11 | 35.3% | |
| 2026-04-22 | 5 | 1 | 4 | 20.0% | |
| **TOTAL** | **154** | **29** | **125** | **18.8%** | |

**CR rate: 29/154 = 18.8%, Wilson 95% CI [13.4%, 25.7%].** Comfortably above the 30%-CR-rate qualifier in the original observer-promotion criteria? **No** — that target is wrong on its face: 30% CR would imply ~30 trades/month/instrument which is far above CLAUDE.md's "~17/month across 5 instruments" baseline. The observed 18.8% is in line with the live fleet (XAUUSD baseline 10.3% per CLAUDE.md, but elevated post-Apr 13 setups). **CR is acceptable.**

**Note:** Apr 23 and Apr 24 daily JSONL files are MISSING despite session-summary files existing (`knowledge_base/live_sessions/GBPUSD/2026-04-23_*_summary.json`). The Apr 23 london summary records 20 evals all NO_TRADE (`top_reason: no_unmitigated_bullish_h1_pois`), so the orchestrator was running, but the per-evaluation JSONL writer didn't fire. This is a separate operational issue (likely a logger-init bug after the 2026-04-24 rolling restart for the v2_shadow promotion). It does not affect this analysis materially — the 17-day window through Apr 22 is sufficient.

### 1B. Decision distribution

| Decision | Count | % |
|----------|-------|---|
| NO_TRADE | 125 | 81.2% |
| CANDIDATE | 29 | 18.8% |
| WAIT / REJECTED_L2 | 0 | 0.0% (all L2 status is logged downstream as separate field on trade_record) |

All 29 CANDs were grade A+, framework `ob_retest`. No grade-B or grade-A CANDs. The AI is being binary about GBPUSD: either A+ with full conviction, or NO_TRADE. This matches CLAUDE.md "T7 prompt = max conviction or skip".

### 1C. Trade records — geometry + L2 + forward-resolution

`knowledge_base/trade_records/GBPUSD/` has 28 JSON files (one per CANDIDATE; 29 CANDs but 1 missing — likely a write race during boot). Each contains entry/SL/TP1, level2_verification result, sl_buffer_applied. I forward-resolved each against `data/historical_2026/GBPUSD_M15.csv` (M15 fill detection + max 96-bar/24h post-fill resolution; pessimistic same-bar SL+TP → SL):

**Geometry summary:**

| Metric | Value |
|--------|-------|
| Total records | 28 |
| Direction | 100% LONG (no SHORTs — v1 bullish-bias bug) |
| L2 PASS | 14 / 28 (50.0%, Wilson [32.6, 67.4]) |
| L2 FAIL | 14 / 28 (50.0%) |
| L2 fail by `sl_beyond_ob` | 12 (42.9% of all records) |
| L2 fail by `entry_in_ob` | 3 (one record fails on both) |
| Inverted TP geometry (SL ≥ entry on LONG) | 6 (21.4%) — all on Apr 20-21 post-FA-2 |
| `sl_buffer_applied = 0.0` | 17 (60.7%) — all pre-FA-2 (Apr 13-17) |
| `sl_buffer_applied > 0` | 11 (39.3%) — all post-FA-2 (Apr 20-22) |

**Pre-FA-2 vs post-FA-2 split:**

| Era | n | L2-PASS % | INV % | sl_buffer=0 % |
|-----|---|-----------|-------|---------------|
| pre-FA-2 (Apr 13-17) | 17 | **58.8%** | 0.0% | 100.0% |
| post-FA-2 / pre-prompt-v2 (Apr 20-22) | 11 | **36.4%** | **54.5%** | 0.0% |
| post-prompt-v2 (Apr 24+) | 0 | — | — | — |

**This is a regression.** FA-2 was supposed to fix `sl_beyond_ob` rejects by enforcing non-zero `sl_buffer_applied`. Per FN smoke + XAUUSD measurements it did. But for GBPUSD specifically, FA-2's introduction of the `sl_buffer` resulted in the buffer being applied in the WRONG DIRECTION on inverted-TP candidates (SL placed +5-7 pips ABOVE entry instead of below for LONG). The 6 inverted records on Apr 20-21 are not random AI errors — they are systematic. Example: GBPUSD_2026-04-20_london_0716 has entry 1.34616, SL 1.34687 (above), TP 1.34757; level2 fails on `sl_beyond_ob` (correctly) and the inverted-TP gate would auto-correct to mirror geometry — but trade_records show this never reached the auto-correction code path because L2 fail came first.

**Forward-resolution outcomes (96-bar/24h M15 walk):**

| Subset | n | TP | SL | TIMEOUT | NO_FILL |
|--------|---|----|----|---------|---------|
| All 28 records | 28 | 4 | 2 | 0 | 22 |
| L2 PASS only (n=14) | 14 | 1 | 0 | 0 | 13 |
| L2 PASS + realized | 1 | 1 | 0 | — | — |

**Realized stats:**

| Subset | n_realized | WR | Wilson 95% CI | Exp R |
|--------|-----------|------|----------------|-------|
| L2 PASS realized | 1 | 100.0% | [20.7, 100.0] | +1.50R |
| All 28 realized | 6 | 66.7% | [30.0, 90.3] | +0.667R |

**Why the 22 NO_FILL?** From Apr 14 through Apr 22, 16/28 records reference the SAME entry of 1.34616 — the AI keeps referencing a stale OB high while price ran 50-100 pips above (median 44.7 pips, max 108.8 pips) and never returned. This is the "stale-OB anchoring" pattern flagged in LIRA red-team but it's NOT LIRA-specific — it's prompt-side. Distance distribution:

| Stat | Value |
|------|-------|
| Min entry-vs-close gap | 1.7 pips |
| Q1 | 23.7 pips |
| Median | 44.7 pips |
| Q3 | 59.7 pips |
| Max | 108.8 pips |
| Records with entry >50 pips below close | 10/28 (35.7%) |

Conclusion: the **statistically-meaningful realized observer data is n=1** (1 win, 100% WR but useless n). The L2-fail subset gives n=5 realized (3 TP, 2 SL = 60% WR n=5) but those would never have traded. The Wilson CI on either is uselessly wide.

---

## Section 2: Backtest data

### 2A. A2 + F3 + Phase 1 — NOT AVAILABLE

I confirmed via `Glob` that the A2 v2-active backtest (`research/a2_v2_active_backtest/slices/`) and F3 backtest (`research/f3_backtest_2026-04-24/`) include only XAUUSD and USDJPY slices (8 + 4 = 12 slices each). **No GBPUSD slices exist.** Likewise for `research/touch_count_audit/_combined_dedup.jsonl` — the file does not exist on disk. The `data/gold_standard/setups_v1.jsonl` referenced in the task brief does not exist either (`data/gold_standard/` has only `__pycache__/`). The historical-batch n=6 from session 5 (Apr 7) is the only AI-evaluated GBPUSD population on record.

### 2B. Historical batch (Apr 7 batch test)

From `.context/02_session_handoffs/05_apr7_complete.md`:

| Symbol | n | WR | Exp R | Asymm | Status |
|--------|---|----|-------|-------|--------|
| GBPUSD | **6** | 83.3% | +1.03R | 1.43:1 | DEPLOYED (observer) |

Wilson 95% CI on 5/6 wins: **[43.6%, 97.0%]** — uselessly wide. n=6 is below the 20-trade significance threshold the system uses, below 30 (rule of thumb), below 100 (CLAUDE.md "Validated Numbers" threshold). This is the foundational "evidence" the system relied on to deploy GBPUSD observer in the first place, and per CLAUDE.md `pre_lock_final_review.md`: "GBPUSD has 6 trades. Only XAUUSD and USDJPY have batch evidence strong enough to trade with real confidence."

### 2C. Mechanical OB-retest backtest (this analysis)

I ran a fresh mechanical OB-retest scan over `data/historical_2026/GBPUSD_H1.csv` (1,940 H1 bars Jan 2 – Apr 24) + `data/historical_2026/GBPUSD_M15.csv` (7,760 M15 bars). Detected OBs via 3-bar fractal swing + BOS confirmation; entry at OB high/low (limit), SL 5 pips beyond OB, TP at 1.5R, 24h timeout. **No AI filter applied.** This is a structural baseline.

| Metric | Value |
|--------|-------|
| OBs detected | 144 bullish + 178 bearish = 322 total |
| Trades simulated | 302 |
| Realized (TP/SL) | 287 |
| Wins | 164 |
| Losses | 123 |
| **WR** | **57.1%** |
| Wilson 95% CI | **[51.4%, 62.7%]** |
| Exp R | +0.429R/trade |
| Total R | +123.0R |

**Per direction:**

| Dir | n | W | WR | Wilson 95% CI | Exp R |
|-----|---|---|----|----|-------|
| LONG | 135 | 80 | 59.3% | [50.8, 67.2] | +0.481R |
| SHORT | 152 | 84 | 55.3% | [47.3, 62.9] | +0.382R |

**Per-month decay (matches CLAUDE.md item 9 pattern):**

| Month | n | WR | Wilson 95% CI | Exp R |
|-------|---|------|---------------|-------|
| Jan | 76 | 59.2% | [48.0, 69.6] | +0.480R |
| Feb | 66 | 62.1% | [50.1, 72.9] | +0.553R |
| Mar | 75 | 58.7% | [47.4, 69.1] | +0.467R |
| Apr | 70 | **48.6%** | [37.2, 60.0] | **+0.214R** |

**H1 (Jan+Feb) WR = 60.6%, H2 (Mar+Apr) WR = 53.8%, decay = -6.8pp.** Smaller than XAUUSD's -40pp Apr decay (CLAUDE.md item 9) but consistent with the broader trend.

**Comparison to per-instrument validated baselines (CLAUDE.md):**

| Symbol | Mechanical OB cont. | AI-filtered batch WR | Source |
|--------|---------------------|----------------------|--------|
| XAUUSD | ~70% rolling-50 | 62.0% (n=129) | T7 + batch |
| USDJPY | — | 75.8% (n=33) | batch |
| US30 | — | 58.5% (n=41) | batch |
| GBPJPY | — | 57.1% (n=42) | batch |
| **GBPUSD mechanical** | **57.1% (n=287)** | 83.3% (n=6) | **this analysis + batch** |

The mechanical 57.1% on n=287 is in line with the AI-filtered batch numbers on US30/GBPJPY. The 83.3% n=6 number was a small-sample lucky spike. **A reasonable expected GBPUSD live WR is in the 55-65% band**, not 83%.

---

## Section 3: Cross-data consistency

### 3A. CR rate consistency

Observer 18.8% CR vs CLAUDE.md baseline 10.3%. The fleet-wide April CAND inflation is real (per `directional_concentration_audit_2026-04-24/report.md`: GBPUSD bias=bullish 74.7% of evals vs 50% baseline). This is the v1 detector locking the AI into bullish bias — and during a fundamentally bullish April, that aligns with the trend, inflating CR rate. Once v2 ships to production, expect CR to drop modestly + SHORT CANDs to begin appearing.

### 3B. WR consistency check

Observer realized n=1 → useless. Mechanical n=287 WR 57.1% → likely lower bound. Historical batch n=6 WR 83.3% → likely upper bound. **Best estimate of true GBPUSD AI-filtered WR: 60-70%, with ≥30 live trades needed to bound it.** No trade has actually been *placed* live in observer mode, so we have NO live-AI-filtered WR estimate that's worth a percentage point.

### 3C. Stale-OB anchoring

The 1.34616 anchor problem is not a GBPUSD-specific issue — LIRA red-team found it on USDJPY (CLAUDE.md item 13(e)). It's a prompt-architecture issue. V3 prompt closed `touches<2` gaming but doesn't address "AI references an OB X pips below current price for the Nth consecutive candle." A v3.5/v4 prompt that adds a `distance_to_entry_atr` veto would help — but is post-Monday work.

### 3D. Discrepancies

1. **L2 reject rate is 2.5x worse than promotion target** (50% vs 20%). Cannot promote on this metric.
2. **Stale-OB anchoring is amplified on GBPUSD** (16/28 records anchor at the same 1.34616 — 57% repeated identical entry). XAUUSD/USDJPY don't show this concentration in trade_records. May be partially because GBPUSD has fewer setups, so each H1 OB lasts longer in the unmitigated state.
3. **Apr 23-24 missing JSONL** despite live-session summaries existing. Operational, not strategic.

---

## Section 4: Decision criteria

### 4A. Promotion gates from observer-mode decision doc

| Gate | Target | Observed | PASS/FAIL |
|------|--------|----------|-----------|
| 1. FA-2 FX precision prompt fix landed | Yes | `fa35cc0` 2026-04-19 + `a9dc373` 2026-04-24 | ✓ Code shipped |
| 2. ≥20 post-fix CANDIDATEs with <20% L2 reject rate | n≥20, reject<20% | n=11 post-FA-2, **63.6% L2 reject rate** | ✗ FAIL on both |
| 3. Sustained ≥30% CAND rate over rolling window | ≥30% | 18.8% over 17 days (35.3% recent week) | ~ borderline |
| 4. CEO end-of-April review | scheduled | today (2026-04-25) | now |

**At least one critical gate is FAILED, not on a borderline.** L2 reject is 63.6% post-FA-2 vs <20% target. PROMOTE-LIVE is materially excluded by the system's own pre-registered criteria.

### 4B. Verdict

**EXTEND-OBSERVER.** Specifically:

1. **Hold `instruments.GBPUSD.trading_enabled: false` in `config/agent_config.yaml`** through next prompt iteration cycle (estimated 2 weeks).
2. **Re-run the observer-promotion gates after prompt v2 (`a9dc373`, landed Apr 24) accumulates ≥20 fresh CANDIDATEs** — the `M15-as-H1 substitution ban` in v2 should reduce the stale-OB anchoring problem materially. Initial v2-era data should land within 5-10 trading days given Apr's CR rate.
3. **Diagnose & fix the post-Apr-22 JSONL write outage** (separate from the observer decision but blocks future evidence collection). If `live_evaluations/GBPUSD/2026-04-2{3,4}.jsonl` aren't writing, the next 2 weeks of "EXTEND" yields no data.
4. **Promote v2 detector to production for GBPUSD** at the same time it's promoted on the other instruments (currently `v2_shadow`). Per CLAUDE.md item 4, v2 promotion needs ≥14 days shadow + ≥100 manually-classified divergences + ≥80% v2-correct + no production regression. Until then, GBPUSD will stay LONG-only and the observer data will be biased.
5. **At next review (estimated 2026-05-09 / 2 weeks):** re-run this report with the post-prompt-v2 + post-v2-detector data. If L2 reject is <20% AND the historical-batch n=6 has been augmented to n≥30 cumulative AI-evaluated CANDs (live observer + batch), promote at 0.5% risk + LONG-WR-watch SPRT.

### 4C. Why not KILL-OBSERVER

- Observer-mode cost (~$10/mo) is well within the $50/mo Anthropic balance and dwarfed by the cost of NOT having data when v2 ships.
- The observer infrastructure is a sunk cost (Gate 0.5 already shipped, JSONL writers in place except for the Apr 23-24 issue noted above).
- v1 detector has been shipping bullish-only labels for 100% of GBPUSD H1 windows — meaning the only data we have on the AI's actual GBPUSD discrimination ability is contaminated by detector bias. Observer needs to run through v2 promotion to provide a meaningful signal.
- KILL would lose the next 2 weeks of v2-era data; re-enabling later costs another orchestration setup + another bootstrapping period before the data is meaningful.

### 4D. Why not PROMOTE-LIVE

- 50% L2 reject rate vs 20% target — the AI's geometry is broken half the time.
- 21% inverted-TP geometry on post-FA-2 records — unsupervised live trading would have those geometries auto-corrected by the inverted-TP gate, but each correction is mirroring a structurally-bad setup, not creating a good one.
- Stale-OB anchoring amplified on GBPUSD (57% of post-Apr-14 records anchor identical entry) means actual live LONG fill rate would be ~30% of what AI proposes, even at 1% risk.
- Realized observer-mode WR signal is n=1. Cannot promote on n=1.
- v1 detector bias means we have ZERO observed GBPUSD SHORT data. Promoting LONG-only into a regime where v2 would shift SHORT exposes the system to one-sided risk.

---

## Section 5: Cost-benefit of observer mode

| Item | Value |
|------|-------|
| Current monthly API cost (CLAUDE.md memory) | ~$10/mo |
| Anthropic balance (CLAUDE.md) | $50/mo cap |
| Observer cost as % of cap | 20% |
| Information gained per dollar | 154 evals + 28 trade_records / 17 days = ~9 evals/day, ~1 record/day. At $10/mo, ~$0.05 per evaluation, ~$0.36 per trade record. Cheap. |
| Lost if we KILL: | ~7 days of v2-shadow GBPUSD CAND data, ~14 days of post-v2-prompt CAND data |
| Re-enable cost | One Gate 0.5 config flip (`trading_enabled: true` → start logging again) — basically zero |
| Re-enable lost time | New observer would need ~7-14 days of CANDIDATEs to rebuild the L2 baseline before promotion |

The cost-benefit is overwhelmingly in favor of EXTEND. Observer infra exists, costs $10/mo, and v2 + prompt-v2 changes coming up specifically address the patterns we're seeing fail.

---

## Section 6: Risk if PROMOTE-LIVE Monday

**Hypothetically**, if we did promote despite the failed gates:

| Scenario | Math |
|----------|------|
| Risk per trade | 0.5% of $100K = $500 |
| Estimated trades/month | ~5 (per CR rate × 20-day month, post-L2-filter) |
| Worst-case 5-loss streak | -2.5% account = -$2,500 |
| FTMO MaxDD limit | 10% / -$10,000 |
| Buffer | 7.5% absolute, 4× headroom |
| LONG-WR-watch SPRT halt | <40% WR after n=20 → halt |

The risk envelope at 0.5% IS contained (4× MaxDD headroom on a 5-loss streak). **But this is the wrong framing.** The question is not "can the account survive bad GBPUSD trades" — it can — the question is "is the AI's geometry good enough to deliver positive expected value." Currently, **n=1 realized live trade and 50% L2 rejects** says we don't know. SPRT halt at <40% WR n=20 is a fire-alarm, not a strategy. We don't promote instruments that fail pre-registered gates and rely on SPRT to catch the fall — we promote instruments that pass the gates first.

**Hypothetical capped-risk Promote v Extend trade-off:** at 0.5% risk × 5 trades/mo × +0.20R baseline expected (from mechanical 57.1% WR scaled by ~0.7 for AI filter overhead) = +0.1% account/mo from GBPUSD. That's ~$100/mo in expectancy on $100K. The $10/mo observer cost is 10% of that for what would still be valuable validation data. Extending observer for 2 weeks costs 0.5% of that expected gain in deferred upside.

---

## Section 7: Comparison to other instrument-expansion candidates

### 7A. Structural screen output (Tier 1 #1 result)

The parallel structural-screen agent's output (`01_ranked_candidates.csv` / `01_per_instrument_scorecard.csv`) **rates GBPUSD as REJECT** with composite_score 52.4 (bottom quartile, threshold 56.3). Key GBPUSD numbers from the structural screen (4-month Jan-Apr 2026 mechanical scan):

| Metric | GBPUSD value | Notes |
|--------|--------------|-------|
| OB-retest candidates | 66 | Comparable n |
| **OB-retest WR** | **47.62%** | **Below 55%, sub-breakeven for 1.5R RR** |
| FVG-fill candidates | 996 | Healthy n |
| FVG-fill WR | 34.35% | Comparable to peers (~33-35%) |
| Sweep-reversal candidates | 530 | |
| Sweep-reversal WR | 41.52% | Best of 4 framework triggers |
| Avg correlation to live | 0.189 | Independent (good) |
| Composite score | 52.4 | **REJECT** (bottom quartile) |

The structural-screen mechanical OB WR (47.6%) is materially below my own mechanical backtest (57.1%). The difference is methodology: my script used 5-pip SL buffer + entry at OB high (LONG); the structural screen likely uses different entry/SL/TP geometry. **Either way, neither number reaches the 70% mechanical-OB-continuation that CLAUDE.md cites for the validated instrument fleet.**

**Higher-ranked candidates from the structural screen (7+ above GBPUSD):**

| Rank | Symbol | Composite | Recommendation | Key strength |
|------|--------|-----------|---------------|--------------|
| 1 | XAGUSD | 67.7 | STRONG-CANDIDATE | OB WR 59.6% n=67 |
| 2 | AUDJPY | 64.9 | WORTH-VALIDATING | OB WR 54.4% n=74 |
| 3 | EURJPY | 63.7 | WORTH-VALIDATING | sweep n=436 WR 37.3% |
| 4 | BTCUSD | 62.9 | WORTH-VALIDATING | OB WR 61.7% n=89 |
| 5 | GBPJPY (live) | 62.0 | STRONG-CANDIDATE | OB WR 55.3% n=80 |
| 6 | AUDUSD | 61.3 | WORTH-VALIDATING | OB WR 53.5% n=75 |
| 7 | CHFJPY | 61.0 | WORTH-VALIDATING | OB WR 53.5% n=78 |
| ... | GBPUSD | 52.4 | **REJECT** | OB WR 47.6% n=66 |

**This materially strengthens the EXTEND-OBSERVER verdict, with one new wrinkle:** the structural-screen would have also REJECTED GBPUSD if it were a fresh candidate. The historical n=6 batch result (83.3% WR) drove the original observer-mode decision; with mechanical 4-month data now available, GBPUSD is a marginal candidate at best.

**However**, EXTEND-OBSERVER is still the right call vs KILL because:

- The 4-month mechanical scan covers an unusual fundamental regime (USD strength, GBP weakness, GBPUSD ranging to bearish at -1.3% on D1). Future regimes may differ.
- The observer cost is sunk + minimal ($10/mo).
- 17 days of live AI evaluation is uniquely positioned to test whether the AI can ADD edge over the structurally-marginal mechanical baseline. This question is unanswered (n=1 realized fill).
- KILL would foreclose the answer; EXTEND keeps it open at trivial cost.

### 7B. Place in the LIVE 5-instrument fleet

| Symbol | Batch n | Batch WR | Exp R | Wilson 95% CI on WR | Status |
|--------|---------|----------|-------|---------------------|--------|
| XAUUSD | 129 | 62.0% | +0.278 | [53.4, 69.9] | LIVE 0.5% risk (FN) |
| USDJPY | 33 | 75.8% | +0.530 | [59.0, 87.2] | LIVE 1% risk |
| US30 | 41 | 58.5% | +0.430 | [43.3, 72.2] | LIVE 1% risk |
| GBPJPY | 42 | 57.1% | +0.220 | [42.2, 70.8] | LIVE 1% risk (fragile) |
| **GBPUSD** | **6** | **83.3%** | **+1.030** | **[43.6, 97.0]** | **OBSERVER** |
| NZDUSD | 16 | 29.4% | -0.240 | [12.9, 53.8] | KILLED permanently |

**GBPUSD's evidence base is the WEAKEST of the 5 currently-trading instruments by far.** Its point WR is 1st (83.3%) but on n=6 with a CI that overlaps every other instrument's CI plus EVERY plausible decision threshold (50%, 60%, 70%). Its only credibility advantage over the structural-screen universe is "we already have 17 days of observer data on it" — but that data shows it's not ready.

**Relative ranking among instrument-expansion candidates (revised post structural-screen):**

1. **Infrastructure-first:** GBPUSD remains the practical "next promotion" despite a marginal structural-screen rank — orchestrator running, observer logger active, Gate 0.5 hook in place, FN profile tested, FX-precision prompt + sl_buffer fix in production. Switching cost from observer to live is one config flip. Switching cost from "fresh candidate" to live is many days of orchestrator setup + bootstrapping + cold-start canary fixtures.
2. **Stronger structural candidates:** XAGUSD (composite 67.7), BTCUSD (62.9), AUDJPY (64.9) all have BETTER mechanical OB-WR than GBPUSD. **If powerful-machine vision roadmap (CLAUDE.md last commit `260ea64`) supports adding 2-3 more parallel orchestrator processes**, those candidates should enter observer mode in parallel — they don't compete with GBPUSD, they augment it.
3. **GBPUSD is at risk of being deprioritized AS A LIVE PROMOTION** — but it should still finish its observer-mode cycle to validate or invalidate the AI-edge hypothesis. The cost is trivial.

**Recommendation:** treat GBPUSD as a separate decision from "instrument expansion universe N+1 selection." GBPUSD is a binary EXTEND/PROMOTE/KILL on its own merits — and the verdict here is EXTEND. The structural-screen universe (XAGUSD, AUDJPY, BTCUSD, etc.) should be evaluated independently for ADDITIONAL observer-mode rollouts, with each promotion needing the same gates as GBPUSD. If GBPUSD's gates ultimately don't clear after another 4-6 weeks of post-prompt-v2 + post-v2-detector data, the right call may be to KILL-OBSERVER GBPUSD AND launch XAGUSD/AUDJPY observers in its place. But that's a 2-month-out decision, not a today decision.

---

## Output: Specific config diffs

### EXTEND-OBSERVER (this verdict)

**No config changes.** Maintain existing:

```yaml
# config/agent_config.yaml — NO CHANGE
GBPUSD:
  trading_enabled: false       # Observer-only per CEO decision 2026-04-18.
                               # Promotion to live requires: (1) FA-2 FX-precision
                               # prompt fix landed, (2) ≥20 post-fix CANDIDATEs
                               # with <20% L2 reject + ≥30% CAND rate, (3) CEO
                               # end-of-April review. See decision doc at
                               # research/gbpusd_observer_mode_decision_2026-04-24.md.
```

Open work item separate from this decision: **diagnose the Apr 23+ live_evaluations JSONL write outage on GBPUSD.** Comparable instruments (USDJPY, GBPJPY, US30) have Apr 23 + Apr 24 files; GBPUSD does not. Suspect: per-symbol logger init crashed silently on the rolling restart, or the observer-mode flag inadvertently disabled an evaluator-side log write. Without this fix, "EXTEND-OBSERVER for 2 more weeks" yields no incremental data.

### If CEO overrides verdict to PROMOTE-LIVE (NOT recommended, listed for completeness)

```yaml
# config/agent_config.yaml diff (NOT recommended)
GBPUSD:
-    trading_enabled: false
+    trading_enabled: true        # PROMOTED 2026-04-25 — start at 0.5% risk
```

```yaml
# config/profiles/redacted_account.yaml — would also need to override risk for safety
# Reduce GBPUSD risk to 0.5% during initial promotion window
instruments:
  GBPUSD:
    risk_per_trade_pct: 0.5  # Reduced from default 1.0% for first 20 live trades
```

Plus add SPRT halt rule (which doesn't exist yet for new-instrument promotion) — this would require new code in `src/components/sprt_monitor.py`. The spec: halt all GBPUSD trades when LONG WR over rolling-20 window drops below 40%.

### If CEO overrides verdict to KILL-OBSERVER (NOT recommended)

```bash
# Stop the GBPUSD orchestrator process (no config change needed)
# The orchestrator command would simply not be re-launched after next restart
```

---

## Summary table

| Section | Finding | Verdict implication |
|---------|---------|---------------------|
| Live observer CR rate | 18.8% (n=154 evals, 29 CAND) | Acceptable |
| L2 reject rate | 50% (target <20%) | FAILS gate, blocks promotion |
| Post-FA-2 L2 reject rate | 63.6% (gets WORSE post-fix) | Confirms regression |
| Inverted-TP rate post-FA-2 | 54.5% | Systematic prompt issue |
| Realized observer WR | n=1 (1 win) | Useless signal |
| Historical batch | n=6, WR 83.3% | Useless signal |
| Mechanical OB-retest backtest | n=287, WR 57.1% [51.4, 62.7] | Healthy structural baseline |
| Per-month decay | Apr -10.6pp vs Jan-Feb | Consistent with fleet decay |
| Direction distribution | 100% LONG (v1 bug) | Can't evaluate SHORT |
| Q24 FVG behavior | 70.4% fill — fleet-uniform | Healthy structure |
| Q52 MAE characteristics | UNIFORM (no deviation) | Healthy structure |

**FINAL VERDICT: EXTEND-OBSERVER for 2 weeks (~2026-05-09).** Re-evaluate after (a) prompt v2 + v2 detector accumulate ≥20 fresh CANDIDATEs, (b) diagnose Apr 23+ JSONL outage, (c) inverted-TP rate drops below 10%, (d) L2 reject rate drops below 20%. Cost to keep observing: ~$5 over the 2-week window.

