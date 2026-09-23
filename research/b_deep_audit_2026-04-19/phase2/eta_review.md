# Phase 2 Review — η (alternative edge discovery)

**Reviewer:** independent Opus 4.7 reviewer, 2026-04-19 (session 35 phase 2)
**Target deliverable:** `research/b_deep_audit_2026-04-19/phase1/eta_alternative_patterns.md`
**Scratch:** `research/b_deep_audit_2026-04-19/phase1/_eta_scratch/` (11 Python scripts + 6 JSON result files)
**Reviewer scratch:** `research/b_deep_audit_2026-04-19/phase2/_eta_review_scratch/` (this file summarizes; underlying python was run inline)
**Reproducibility rating:** **4 / 5** (every scratch-script output reproduces bit-exact including η's headline `239/296` and `p_bonf=2.6e-47`; the Bonferroni arithmetic is honest; data load + feature extraction is clean; **the headline is nonetheless wrong because the underlying input file has a data-pipeline defect** — an issue η's scratch cannot diagnose from within its own methodology)

---

## Final verdict (1 paragraph)

**η's top finding — GBPJPY hour-23 UTC SHORT at WR 80.7%, n=296, p_bonf=2.6e-47 — is almost entirely a data-pipeline artefact of `data/historical_2026/`, not a real market edge.** Running η's exact forward-replay logic on the independent `data/historical/` file (same 2026-Q1 window, clean MT5 export) yields **WR = 46.6%**, a 34-percentage-point reduction. On 2022-2025 OOS in the `historical/` file (n=3,095 — 10× η's in-sample), **GBPJPY-23 SHORT WR = 40.5%**, indistinguishable from η's own null baseline of 38.7% (p_bonf = 1.00). The same artefact inflates USDJPY-23 SHORT from 62.4% → 39.4% on clean data (OOS null ~42%) and GBPUSD-23 SHORT from 59.4% → 53.4% (OOS null ~45%). **The root cause is a 23:45→00:00 UTC systematic "gap" in `historical_2026/`** of −13.4 pips mean (GBPJPY), −5.2 (USDJPY), −4.5 (GBPUSD), −3.0 (EURUSD), with the negative sign hitting 78-87% of days. The same boundary on `historical/` shows mean −0.04 to −1.1 pips with 29-49% negative — i.e. noise. Mechanistically: `scripts/export_mt5_historical.py:81` labels MT5 broker-server timestamps as UTC with no TZ conversion, so broker server-midnight (typically 22:00 UTC on UTC+2 servers) cascades as an unaccounted rollover/reconciliation adjustment that appears in-file at the 23:45→00:00 boundary in the `historical_2026/` export. η's 4-hour forward replay of a 23:00-UTC SHORT crosses this artefact at bar-4 (00:00 UTC), which is where 44 of η's 239 wins resolve (18% of wins concentrated in one bar). Secondary findings that DO hold qualitatively: (a) the 3 CEO-specified candidate edges fail Bonferroni — this is correct (confirmed by my replication of `full_scan_output.json`); (b) the NO_TRADE winning-cluster hypothesis is falsified — matches γ and holds independently; (c) 22-23 UTC is outside current KZ coverage — confirmed against `quick_reference_card.md:31`. **Chairman action: discard all 22-23 UTC hour-of-day findings in η §4-6 and Rank-1/Rank-4/Rank-7/Rank-8 in §5 as data-artefact contamination. The XAUUSD h=11 edge also fails OOS (2024 WR=34.1%, 2025 WR=41.1%) and should be discarded separately. There is no actionable alternative edge in η's output. Fortunately the risk of mis-deployment is modest — η explicitly flagged OOS re-verification as the "critical next step" and did not recommend live enablement — but the report's R/month framing (28-33R marginal) must not propagate to the session 35 plan.**

## Concerns ranked by severity

1. **[CRITICAL — FATAL] GBPJPY-23 SHORT edge collapses on OOS clean data** — η claims WR 80.7% (n=296) on `data/historical_2026/GBPJPY_M15.csv`. Running the identical methodology on `data/historical/GBPJPY_M15.csv`:
   - 2026-Q1 (same window): WR = **46.6%** (n=251, W=117, L=134)
   - 2025 full year OOS: WR = **44.2%** (n=815)
   - 2024 full year OOS: WR = **41.4%** (n=823)
   - 2023 full year OOS: WR = **36.4%** (n=828)
   - 2022 since Mar OOS: WR = **40.1%** (n=629)
   - 2022-2025 pooled: WR = **40.5%** (n=3,095)
   
   η's own GBPJPY SHORT null baseline is 38.7% (`eta_alternative_patterns.md:44`). The 2022-2025 OOS WR is within 2pp of null. **p_bonf on 2022-2025 OOS data = 1.00** — this is NOT an edge on any time period except 2026-Q1-as-read-through-`historical_2026`. **Recommended action:** chairman reject §4 strong-edge table (10 edges) in full for the 22-23 UTC entries, and rank-ordered §5 candidates #1, #4, #5, #7, #8 must be struck. η's own §7 risk #1 ("edge discovered by ranking 330 tests — even at p=2.6e-47 should be re-verified on pre-2026 data") is correct foresight; the OOS verification now exists and the answer is "edge does not survive".

2. **[CRITICAL — FATAL] The inflation mechanism is a data-pipeline defect in `historical_2026/`, not a market phenomenon** — I measured the 23:45→00:00 UTC transition gap across four FX files in both `historical_2026/` and `historical/` folders, for 2026-Q1:
   | Symbol | `historical_2026/` mean gap | neg pct | `historical/` mean gap | neg pct |
   |---|---:|---:|---:|---:|
   | GBPJPY | **−13.37 pips** | **86.7%** | −1.06 pips | 48.6% |
   | USDJPY | **−5.21 pips** | **83.3%** | −0.33 pips | 39.2% |
   | GBPUSD | **−4.54 pips** | **78.3%** | −0.28 pips | 29.7% |
   | EURUSD | **−3.00 pips** | **86.7%** | (file not present) | — |
   
   These gaps are measured strictly between 15-minute-consecutive bars (`20 > dt_min > 10`), ruling out weekend-gap contamination. The `historical/` file — same MT5 account, same symbols — has **no such systematic bias**. The root cause sits in `scripts/export_mt5_historical.py:81`:
   ```
   df["time"] = df["time"].apply(
       lambda ts: datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
   )
   ```
   MT5's `copy_rates_range` returns broker-server-time Unix timestamps, NOT UTC timestamps. Most FTMO-like MT5 brokers run on UTC+2 (European winter) or UTC+3 (European summer) server time. Treating those timestamps as UTC mislabels every bar by 2-3 hours. The rollover/swap adjustment that brokers apply at broker-server-midnight (00:00 server = 22:00 UTC actual in winter) appears in the CSV at the 23:45 → 00:00 line because the label has been shifted. η's forward-replay through this boundary on a 23:00-UTC SHORT eats the rollover adjustment as free alpha. **Recommended action:** chairman note this as a **live code bug**: the `historical_2026/` dataset should be regenerated with proper TZ conversion, OR the MT5 broker's server TZ should be queried via `terminal_info()` and baked into the timestamp conversion. Both are in scope of the bug fix; neither changes prompts or trading logic so no CEO-approval is needed for the bug patch. Until fixed, **no FX T7 simulations or hour-of-day research should use `data/historical_2026/` for FX pairs**. Note that XAUUSD/NAS100/US30 appear less affected because those CSVs don't have h=00 bars (XAUUSD's earliest bar is h=01, confirmed at `historical_2026/XAUUSD_M15.csv`); the artefact is FX-specific.

3. **[CRITICAL] Intra-hour autocorrelation inflates apparent n from 74 independent days to 296 15-min observations** — η treats the 4 candles within each hour-23 UTC bucket (23:00, 23:15, 23:30, 23:45) as independent trials. They are not. Measuring the design effect on the 2026-Q1 GBPJPY-23 SHORT sample:
   - All 4 of a day's candles WIN: 45/74 days (60.8% observed) vs 42.4% under independence
   - All 4 LOSS: 4/74 (5.4%) vs 0.1% under independence (**54× over-concentrated in LOSS days**)
   - Per-day-sum variance = 1.275 vs Bernoulli-independence 0.622; design effect **DE = 2.05**
   - Effective independent n = 296 / DE = **144**, not 296
   
   Under proper daily-independence treatment on the `historical_2026/` data (accepting the artefact for argument's sake):
   - First-candle-only daily: n=74, W=53, **WR=0.716**, z=5.81, p_raw=6.1e-9, **p_bonf_330=2.0e-6** (still significant but **40+ orders of magnitude larger than η's 2.6e-47**)
   - Majority-vote daily: n=74, W=64, WR=0.865, **p_bonf_330=1.0e-14** (still significant but much weaker than claimed)
   
   **Recommended action:** chairman downgrade η's headline `p_bonf=2.6e-47` to the corrected `p_bonf ≈ 1e-6` to `1e-14` range, AND note that once the data-pipeline artefact is accounted for (concerns 1-2) the whole chain is moot. This concern is secondary to the data artefact but would stand independently even on clean data.

4. **[CRITICAL] The 44-win spike at bar-4 (00:00 UTC) reveals direct rollover-gap contamination of the expectancy figure** — Resolution-bar distribution for η's 239 wins on `historical_2026/` GBPJPY-23 SHORT:
   | Bar | UTC time | Wins resolved at this bar | Cumulative WR% |
   |---:|---:|---:|---:|
   | 1 | 23:15 | 54 | 22.6% |
   | 2 | 23:30 | 63 | 49.0% |
   | 3 | 23:45 | 62 | 74.9% |
   | **4** | **00:00** | **44** | **93.3%** |
   | 5-8 | 00:15 - 01:00 | 16 | 100% |
   
   The +18.4pp cumulative WR between bar-3 (74.9%) and bar-4 (93.3%) is concentrated in a single candle — the one containing the systematic −13.37 pip downward gap. **Forcing trade-close at 23:45** (bar-3, before the rollover) on `historical_2026/`:
   - Wins = 179, Losses = 31, Opens = 86 (n_resolved = 210)
   - WR on resolved = **85.2%** (still inflated, because the 3 bars pre-rollover on `historical_2026/` are *also* partly contaminated)
   - **Including unresolved as open-MTM at 23:45 close**: full-expectancy on 296 trades = **+0.112R/trade** (vs η's headline +1.019R/trade — a **9× reduction**)
   
   **Recommended action:** chairman note that η's +1.02R/trade expectancy is inflated by ~9× relative to the minimum defensible pre-rollover MTM-close interpretation, independent of the OOS null result. When chainable artefact + methodological choice compound, the total-R impact claim in §5 (+17.8R/month for GBPJPY-23 SHORT alone) is not recoverable.

5. **[CRITICAL] Same OOS collapse on USDJPY-23, XAUUSD-11, GBPUSD-23** — confirmed with same methodology on clean `historical/` data:
   - USDJPY-23 SHORT: η claim 62.4% / hist_2026 Q1 62.4% / hist_all Q1 **39.4%** / hist 2022-2025 OOS **41.7%** (vs null 40.7%) — **no edge**
   - GBPUSD-23 SHORT: η claim 59.4% / hist_2026 Q1 59.4% / hist_all Q1 **53.4%** / hist 2022-2025 OOS **45.0%** (vs null 41.2%) — marginal residual, not the claimed edge
   - XAUUSD-11 SHORT: η claim 51.9% / both files Q1 agree at 52% / hist 2025 OOS **41.1%** / hist 2024 OOS **34.1%** (vs null 40.0%) — **edge fails in 2024-2025**
   
   The XAUUSD h=11 finding is particularly instructive because the TWO CSV files AGREE on 2026-Q1 (52%), ruling out a data-artefact explanation for that specific edge. But it still fails OOS (34-41%), so this one is a different kind of failure: **regime-specific in-sample overfit**, not a data defect. Still fatal. **Recommended action:** chairman discard XAUUSD-11 SHORT as a separate (regime-overfit) rejection. Of the 10 "strong" edges in §4.1, zero survive a minimally-defensible OOS check.

6. **[MAJOR] The 330-test Bonferroni family is under-specified** — η declares the family size as "inst × hour × direction = 7 × 24 × 2 = 336, actually 330 after n>=20 filter" at `eta_alternative_patterns.md:60` and `hour_specific_edges.py:53-54`. The honest family is larger: η ALSO ran `edge_funcs` (8 pattern-edges × 7 instruments = 56 tests) AND the NO_TRADE-cluster sub-stratification (alignment × session × FVG × sweep × PDH/PDL ~ ≥30 tests, informal), AND conditional enhancement (WR × condition ~ 20+ tests in `conditional_enhancement.py`), AND monthly + subperiod stability tests (12 edges × 2-4 sub-periods ~ 24-48 stability tests that could elevate suggestive→strong). The TRUE family exercised by η is closer to 500-600 tests. At 500 tests, η's `p_bonf` figures scale up by ~1.5-1.8× — still leaves GBPJPY-23 SHORT's raw p=8.0e-50 far above any conceivable correction threshold, so the Bonferroni arithmetic does not independently kill the headline. BUT the XAUUSD-11 SHORT at `p_bonf=0.011` becomes `p_bonf≈0.018` at true family 500 — still strong, but the `EURUSD h=13 LONG` at `p_bonf=0.010` would tip to `p_bonf≈0.017` and the `USDJPY h=19 LONG` at `p_bonf=0.018` to `p_bonf≈0.030`. η also admits "If the true family is wider… some `p_bonf ~ 0.01` entries would fall below significance" at `eta_alternative_patterns.md:350` — this concern is acknowledged in writing, but the §4.1 table does not propagate it. **Recommended action:** chairman note the Bonferroni is conservative-enough for the strongest edges but marginal-enough to disqualify the weakest. Moot given concerns 1-5 but worth flagging for methodology quality.

7. **[MAJOR] Subperiod + monthly stability tables silently pass `historical_2026/`'s corrupt data through** — η's §4.4 H1/H2 stability tables (`eta_alternative_patterns.md:217-230`) and §4.5 monthly tables (line 234-245) are computed on the defective file. The "GBPJPY-23 SHORT growing Jan 81% → Apr 88%" narrative (line 246) is an artefact of the defect remaining CONSTANT across months (the broker TZ doesn't change mid-quarter). The apparent stability is therefore not "robust edge found" — it's "defect applied uniformly across quarter". This is slightly different from a normal overfit because the defect stability is itself artificial: if the broker changed TZ mid-quarter (e.g., for DST in March), the edge would have shifted, and η would have caught it. But DST happened on **Mar 29** (per `quick_reference_card.md:174`), which means there SHOULD be a ~1 hour shift in the defect pattern around that date — yet η's Mar monthly row shows WR 0.81 and Apr 0.88, both consistent. This suggests the broker is actually on a FIXED UTC+2 year-round (some MT5 brokers do this; others DST-shift). Either way, the stability tables in §4.4 / §4.5 do not independently corroborate the edge. **Recommended action:** chairman strike stability-based corroboration claims from §4.4 / §4.5.

8. **[MAJOR] The "terminal-hour liquidity sweep" mechanism narrative at §4.6 is post-hoc** — η explains the edge as "asymmetric excursion due to thin-book JPY pair winding down European flow before Tokyo open" (`eta_alternative_patterns.md:264`). This is *plausible literature-consistent* but is a post-hoc explanation picked AFTER the 80% WR was observed. On clean OOS data where WR is 40.5% instead of 80.7%, the same mechanism would predict a neutral or edge-negative outcome — so the mechanism is unfalsifiable, it explains any outcome. Further: η cites Osler (2000-2005) as academic support (line 264) — Osler's work is on order-flow imbalance at round-number stops, not end-of-day asymmetric vol. Mis-cited. **Recommended action:** chairman strike "terminal-hour liquidity sweep" mechanism claim. If the edge is real (which concerns 1-5 show it is not), the mechanism needs to be derived from first principles, not backfit.

9. **[MAJOR] No check for news-calendar seasonality** — η explicitly flags at `eta_alternative_patterns.md:352` that "If the mechanism is actually 'news-calendar artefact' (e.g., regular Japan data at 23:30 UTC), the edge could evaporate on any calendar change". This is correct self-flagging but NOT TESTED. Japan economic data (CPI, core CPI, Tankan, etc.) is routinely released at 23:30 or 23:50 UTC (corresponding to 08:30/08:50 JST). My per-DOW cut on `historical_2026/` shows Wednesday WR = 0.900 and Tuesday WR = 0.683 — that's a 22pp gap. If Japan data clusters on specific weekdays (e.g., Tankan is Monday morning JST), a plausible non-edge explanation is present. This doesn't change the OOS conclusion but it's another non-tested alternative hypothesis that η's TL;DR does not caveat. **Recommended action:** chairman do not pursue; moot given OOS null. Keep in backpocket if the data-artefact is ever cleared and real 2022-2025 edge is then considered.

10. **[MAJOR] γ agrees operationally — reconciliation partially holds, partially diverges** — η §2.2 reports NO_TRADE bias-forward-hit-rate of 36.6% / 38.0% / 39.2% (XAU / NAS / EUR) and cites these as matching γ. γ's independent numbers (`gamma_missed_trades.md:20`) are 36.6% / 38.0% / 39.2% — **exact bit-match**. The NO_TRADE null is independently confirmed by two agents with different code paths. This is a clean reconciliation. **BUT** — γ does NOT confirm the hour-of-day finding, because γ never ran that analysis. γ's Phase 1 scope was NO_TRADE census only. So "η agrees with γ" is true for the falsified-hypothesis half and NOT TESTED for the hour-of-day half. **Recommended action:** chairman accept γ/η reconciliation on NO_TRADE (rock-solid); disregard it on hour-of-day (not cross-checked by any agent in this phase).

11. **[MINOR] The 3 CEO-specified edges (FVG-only, Sweep+Displacement, Fib50) rejection IS correct** — I reproduced `full_scan_output.json` and verified η's headline numbers bit-exact:
    - FVG-only H1-aligned combined: n=4,248, WR=38.9%, Exp=−0.028 (η line 124)
    - Sweep+Displacement combined: n=1,277, WR=38.4%, Exp=−0.041 (η line 139)
    - Fib50 D1-aligned combined: n=1,754, WR=40.6%, Exp=+0.016 (η line 148)
    
    The EURUSD fib50 pocket (n=299, WR=49.2%, p_bonf=0.031) does survive Bonferroni and is NOT in the 22-23 UTC dead-zone, so it is NOT contaminated by the concern-2 defect. However, EURUSD FX-precision is flagged as a live blocker (`CLAUDE.md` unresolved #7), so this pocket cannot be operationalized as-is and is orthogonal to the Phase 1 η headline. **Recommended action:** chairman accept CEO-candidate rejection. Flag EURUSD fib50 pocket for Phase 3 FX-precision follow-on, not for this audit. Note that this pocket is STILL on the suspect `historical_2026/EURUSD_M15.csv` file — if EURUSD precision is fixed, this pocket must be re-run on clean data before trusting.

12. **[MINOR] "All edges outside current KZ coverage" claim verifies against KZ reference** — I checked `quick_reference_card.md:26-44`:
    - XAUUSD: 07:00-10:30 + 13:00-17:00 → 11:00-12:00 IS outside KZs (matches η)
    - USDJPY/GBPJPY: 00:00-03:00 + 07:00-09:30 + 13:00-15:30 → 22:00-23:59 IS outside (matches η). The 00 UTC Tokyo KZ bracket is 00:00-03:00 — η's JPY-0 LONG is actually INSIDE the Tokyo KZ (as η correctly annotates with "YES (Tokyo)" at line 183)
    - GBPUSD: 07-12 + 13-15:30 → 22-23 outside (matches η)
    
    The table at `eta_alternative_patterns.md:178-189` is accurate on KZ coverage. This part of the claim survives. **Recommended action:** chairman accept KZ-gap framing as factually correct, but moot given concern 1-5 invalidate the edges themselves.

13. **[MINOR] "Red-flag decaying edges" at §4.5 (USDJPY-0 LONG, USDJPY-19 LONG) are correctly NOT recommended** — η shows USDJPY-0 LONG April WR dropped to 33% (from 58-63%) and USDJPY-19 LONG H2 dropped to 44.9% (from 56.7%). η's §6 / §5 ranking explicitly excludes these. This is correct defensive filtering even on the defective dataset. **Recommended action:** none; minor credit to η for applying monthly-stability filtering even when the input is bad.

14. **[MINOR] Code quality is high; scratch is self-contained and reproducible** — `_eta_scratch/` scripts run clean; `full_scan_output.json` and `hour_edges.json` load and reproduce numbers to machine precision. The load_data.py path + ATR + forward-replay logic is all honest. The failure mode is upstream of η's code (the input data file), not within η's analytical layer. This matters for the chairman's R-deduction against η: **η's methodological quality is ≥4/5**; the failure is an input-data defect that requires a different agent (the one responsible for `export_mt5_historical.py` broker-TZ awareness) to fix. Not counting this against η's craft — counting it against the recommendation to act on the output.

## Spot-checks performed

Reproduced numbers from fresh runs of η's scratch scripts (all against `historical_2026/` as η did):
- **§4.1 GBPJPY-23 SHORT** n=296, W=239, WR=0.807, p_raw=8.01e-50, p_bonf=2.64e-47 — matches η line 179 bit-exact.
- **§4.1 USDJPY-23 SHORT** n=290, W=181, WR=0.624, p_bonf=1.64e-11 — matches η line 180 bit-exact.
- **§4.1 GBPUSD-23 SHORT** n=266, W=158, WR=0.594, p_bonf=5.95e-07 — matches line 181 bit-exact.
- **§4.1 XAUUSD-11 SHORT** n=289, W=150, WR=0.519, p_bonf=1.10e-02 — matches line 186 bit-exact.
- **§1.1 baseline directional nulls** (all 7 instruments) — match `full_scan_output.json["baselines"]` bit-exact.
- **§3.1 FVG-only combined** n=4,248, WR=0.389, Exp=−0.028 — matches line 124.
- **§3.2 sweep+displacement combined** n=1,277, WR=0.384 — matches line 139.
- **§3.3 fib50 D1-aligned combined** n=1,754, WR=0.406, Exp=+0.016 — matches line 148.
- **§2.2 NO_TRADE bias-forward-hit-rate** XAUUSD 36.6%, NAS100 38.0%, EURUSD 39.2% — matches line 96-98 AND γ's independent computation in `gamma_missed_trades.md:20`.
- **§4.1 Bonferroni arithmetic** `p_raw × 330 = p_bonf` verified for all 10 strong edges (e.g. 8.013e-50 × 330 = 2.644e-47 — matches).

Spot-checked and FOUND FATAL DISCREPANCIES:
- **GBPJPY-23 SHORT on clean `historical/` 2026-Q1**: n=251, W=117, WR=0.466 — **34 pp lower than η's 80.7%**.
- **GBPJPY-23 SHORT on clean `historical/` 2022-2025 OOS**: n=3,095, W=1,254, WR=0.405 — indistinguishable from null 0.387 (p_bonf_330=1.00).
- **USDJPY-23 SHORT on clean `historical/` 2026-Q1**: n=251, W=99, WR=0.394 — **23 pp lower than η's 62.4%**.
- **USDJPY-23 SHORT on clean `historical/` 2022-2025 OOS**: n=1,441, WR=0.417 — null.
- **GBPUSD-23 SHORT on clean `historical/` 2022-2025 OOS**: n=1,427, WR=0.450 — mild residual (null=0.412) but NOT η's 59.4%.
- **XAUUSD-11 SHORT on clean `historical/` 2024 OOS**: n=763, WR=0.341 — null.
- **XAUUSD-11 SHORT on clean `historical/` 2025 OOS**: n=993, WR=0.411 — null.
- **23:45 → 00:00 gap artefact verified** on all 4 FX pairs in `historical_2026/` vs clean `historical/` (see concern #2 table).

Augmented analyses performed:
- **Design effect / intra-day autocorrelation** for GBPJPY-23 SHORT: DE=2.05, effective n=144, so η's p_bonf is overstated by ~30-40 orders of magnitude (still strong on `historical_2026/`, but this correction stacks ON TOP OF the OOS null).
- **Resolution-bar distribution** (which candles the wins resolve on): 74.9% of wins resolve by bar-3 (23:45), then +18.4pp at bar-4 (00:00, THE ROLLOVER BAR). Confirms rollover contamination.
- **Force-close at 23:45 (pre-rollover) on `historical_2026/`**: n=210 resolved, WR=85.2%; n=296 inclusive-MTM, effective expectancy **+0.112R/trade** (vs η's +1.02R — 9× reduction).
- **Realistic 3-pip spread haircut on `historical_2026/` bars 1-3**: WR 0.792 (n=154), Exp +0.527R — still strong on `historical_2026/`, but the "still strong" is fighting the data defect.
- **Per-DOW cut of GBPJPY-23 SHORT on `historical_2026/`**: Mon 86.7%, Tue 68.3%, Wed 90.0%, Thu 85.0%, Fri 73.2% — 22 pp DOW gap implies day-specific news/structural variation AT the defect layer (not organic edge).
- **Per-week cut**: 3 of 15 weeks hit 100% WR (wk 03, 10, 16), which is too concentrated for independent daily events — further corroboration of within-day correlation.
- **Per-hour volume/range on GBPJPY h=23**: mean tick-volume=802 (lowest of day), mean bar-range=8.5 pips (lowest of day), mean ATR-14=10.1 pips (second-lowest). Confirms h=23 is thin-book; does NOT confirm the edge as real because the thin-book pattern is present every year including OOS.
- **Per-hour gap profile on XAUUSD**: no systematic gaps at any hour (mean gap ±0.05 to ±0.12), confirming XAUUSD data is clean and the artefact is FX-specific.

## Cross-agent conflict / triangulation notes

- **η vs γ (AGREEMENT on NO_TRADE, UNTESTED on hour-of-day):** γ and η both compute the NO_TRADE bias-forward-hit-rate census independently. Numbers match bit-exact (XAUUSD 36.6%, NAS100 38.0%, EURUSD 39.2%). Both falsify the "winning-NO_TRADE cluster" hypothesis. This is a clean cross-agent confirmation. However, γ did NOT run hour-of-day scans, so γ cannot corroborate η's §4 findings. The chairman should not read "η matches γ" as support for the hour-of-day edges — only for the NO_TRADE-cluster null.

- **η vs α / ε (PARTIAL CONFLICT):** α ranks XAUUSD entry-quality degradation as its top finding with R-impact −2 to −4R/quarter. η's 10 strong hour-of-day edges include XAUUSD-11 and XAUUSD-12 SHORT, which if real would represent "ADDITIVE alpha the current system misses". If α is right (XAUUSD entry execution is degrading), AND η is right (XAUUSD-11 is a +6R/month edge), then a straightforward chairman path is "the 2026-Q1 XAUUSD edge is shifting hours". BUT XAUUSD-11 fails OOS (concern 5), so α's entry-degradation story stands alone: it's real in the 2026 data but η's "successor edge" does not exist outside 2026-Q1. **Chairman action:** don't construct narrative coupling α + η hour-of-day. Treat them as independent findings.

- **η vs δ (AGREEMENT that 2026 is regime-anomalous):** δ's quarterly WR bootstrap shows 2026-Q1 is not distinguishable from noise. η's hour-of-day edges are overwhelmingly 2026-Q1 phenomena that fail OOS on 2022-2025 (my concern 1 and 5). δ's framing supports mine: **the entire hour-of-day layer η found in 2026-Q1 may be regime-specific noise**, not stable edges. This is a clean two-agent triangulation: η and δ together say "2026-Q1 is unusual, don't extrapolate from it". **Chairman action:** chairman use δ's "don't treat 2026 as training data for alternative-edge discovery" framing as meta-principle; η's output is a specific example of why.

- **η vs ε (NO CONFLICT, DIFFERENT DOMAINS):** ε covers XAUUSD fast-loss / MFE compression and liquidity-level distance metrics. η covers hour-of-day and pattern-based candidate edges. They don't overlap on any metric. No conflict or reconciliation required.

- **η vs ζ (NOT DIRECTLY TESTED):** ζ covers `market_state.py` pre-check correctness. η's "edges fire at 22-23 UTC" would require `market_state.py` to run at those hours, which it currently doesn't. If any of η's edges had held OOS, chairman would need ζ-confirmation that the structural features extracted at 22-23 UTC are reliable (liquidity levels computed with <300 M15 bars of context are suspect). Moot given concerns 1-5.

- **η vs θ (NO CONFLICT, DIFFERENT DOMAINS):** θ covers prompt integrity / AI layer. η's hour-of-day triggers are meant to be AI-free scheduled entries. No overlap, no reconciliation required.

## Chairman recommendations

1. **Reject η's headline + §4-5 R/month ranking in full.** The 22-23 UTC edges are data-pipeline artefacts; the XAUUSD-11 edge is a regime-specific in-sample overfit. No alternative edge in η's output survives a minimally-defensible OOS check.

2. **Accept η's falsification of the 3 CEO-specified candidate edges** (FVG-only, Sweep+Displacement, Fib50) as correct. This part of η is valuable — it retires 3 hypotheses with rigorous methodology.

3. **Accept η's NO_TRADE-cluster falsification** as independently confirmed by γ (bit-exact match on XAUUSD/NAS100/EURUSD).

4. **File a data-integrity ticket** for `scripts/export_mt5_historical.py:81` broker-TZ handling (use `terminal_info().timezone` or equivalent). Until patched, FX data in `data/historical_2026/` should be considered unreliable for hour-of-day research. Research-layer bug fix, no CEO approval needed. Moderate priority — T7 simulation results for FX are already flagged as blocked on the FX-precision issue (`CLAUDE.md` unresolved #7 + #8); this adds a second blocker on top.

5. **Do NOT operationalize any hour-of-day trigger pre-redacted_account.** The Tuesday 2026-04-21 kickoff at 1% risk on XAUUSD/US30/USDJPY/GBPJPY/GBPUSD should proceed ONLY on the existing OB-retest logic. η does not recommend operationalization either (`eta_alternative_patterns.md:319` "~2-4 weeks shadow log + 10-trade pilot at 0.25% risk"), so this is primarily a belt-and-suspenders note.

6. **Treat η's §3 EURUSD fib50 pocket (n=299, p_bonf=0.031) as a Phase-3 re-examination candidate AFTER the data-pipeline fix** (concern #4 above) and after the EURUSD FX-precision issue is resolved (`CLAUDE.md` unresolved #7). Neither should propagate to the session 35 plan.

## Reproducibility verdict

**4 / 5.**

- Every `full_scan_output.json` / `hour_edges.json` number reproduces bit-exact from the scratch scripts.
- The Bonferroni arithmetic is honest (p_raw × 330 = p_bonf, verified).
- The forward-replay logic is correctly symmetric and look-ahead-free.
- The feature computation is correct.
- **The one point that drops it from 5 to 4**: η did not independently cross-verify the `historical_2026/` file against `data/historical/` or against fresh MT5 pull before running Bonferroni on `historical_2026/`. A single sanity check (e.g., spot-check 2026 prices against `historical/GBPJPY_M15.csv`) would have surfaced the 23:45→00:00 gap discrepancy and saved the entire hour-of-day analysis. This is the exact "suspect environment state before code when external calls fail" principle from `CLAUDE.md` verification protocol, generalized to "suspect upstream data before downstream stats when extraordinary claims emerge".
- The `CLAUDE.md` discipline of `MT5 preflight + cache suspicion` (`verify against fresh mt5.copy_rates_* before assuming CSV/LanceDB is stale`) is exactly the missing control.

## Final position (single paragraph for the chairman)

η's methodology is high-quality and scratch-reproducible, but the input file `data/historical_2026/` contains a ~−13 pip systematic 23:45→00:00 UTC gap for FX pairs that is absent from the independent `data/historical/` file. That defect alone explains almost all of η's 22-23 UTC hour-of-day edges: GBPJPY-23 SHORT collapses from WR 80.7% to 46.6% on `historical/` 2026-Q1 and to 40.5% (null) on 2022-2025 OOS; USDJPY-23, GBPUSD-23, and XAUUSD-11 all fail OOS as well. η's p_bonf=2.6e-47 is further corrupted by intra-hour autocorrelation (design effect 2.05 on GBPJPY-23), and a full-MTM close at 23:45 pre-rollover reduces the claimed +1.02R/trade expectancy by 9× even on the defective input. **Chairman: discard η's §4-5 R/month ranking in full; keep §2 NO_TRADE-cluster falsification (confirmed by γ); keep §3 CEO-candidate rejection; file a data-pipeline ticket on `scripts/export_mt5_historical.py:81` broker-TZ handling; do not revise the session 35 kickoff plan based on η's output.** There is no actionable alternative edge surfacing from η. The specific failure mode — high-confidence edge from defective input data — is one the system's existing discipline (`CLAUDE.md` section "MT5 / DATA EXTRACTION PREFLIGHT") was designed to catch; recommend chairman add "always cross-verify primary data file against a second source before running Bonferroni-heavy search" to the research-agent brief template.
