# Domain 18 — Trader Psychology & Decision Under Uncertainty — Papers

**Owner:** Phase 1 Worker Agent #18
**Compiled:** 2026-04-28
**Paper count:** 38
**Subscription-bounded.** Sources: WebSearch + WebFetch across Google Scholar / SSRN / NBER / Wiley / Springer / Oxford Academic / arXiv / PMC / Stanford / Berkeley / MIT / Princeton.

---

## 1. Section overview

This domain catalogs the **individual decision-maker** literature that conditions market behavior: prospect theory, disposition effect, overconfidence, ambiguity aversion, expert intuition, emotion / physiology in trading, framing, mental accounting, time-pressure, and recent (2020-2025) prop-firm / LLM-trader / drawdown research. The **counterparty-flow lens** for GTOS: every trader who breaks a stop, doubles a loser, refuses to take a 1.5R loss, or trades during stress is creating the order-flow imbalance the OB-zone edge harvests on retest. The **CEO-discipline lens**: the same biases (loss aversion, drawdown stress, snake-bite, sunk cost, recency, FOMO) apply to the human running the autonomous system, which is why Gate 0 / hard rules / kill-switch architecture matter. The **AI-grounding lens**: HALLUC-1 distinguishing precision bug from genuine perception failure connects to the Lichtenstein-Fischhoff calibration literature; LLM behavioral-bias research (2024-2025) directly informs Sonnet-4.6 vs Opus selection.

## 2. Reading-order recommendation

**Tier 1 — must read for any GTOS strategic decision:**
1. Kahneman & Tversky 1979 (prospect theory)
2. Tversky & Kahneman 1992 (cumulative PT — operationally usable functional form)
3. Odean 1998 (disposition effect — single-most-actionable counterparty bias)
4. Coval & Shumway 2005 (afternoon risk-recovery — direct CEO-after-loss analog)
5. Lo, Repin & Steenbarger 2005 (Fear and Greed — emotional intensity ↔ trader performance)
6. Kahneman & Klein 2009 (intuitive expertise conditions — when AI 'intuition' should be trusted)
7. Daniel & Hirshleifer 2015 (overconfidence + predictable returns — framework for Sonnet vs Opus)
8. Locke & Mann 2005 (professional-trader discipline — empirical proof discipline beats raw skill)
9. Frydman et al. 2014 fMRI (realization utility — neural mechanism of disposition effect)
10. Cohn, Engelmann, Fehr & Maréchal 2015 (countercyclical risk aversion — drawdown psychology causal evidence)

**Tier 2 — implementation context:**
- Tversky & Kahneman 1981 (framing — how prompts/displays change AI selectivity)
- Heath & Tversky 1991 (competence ↔ ambiguity aversion — why AI overconfidence ≠ retail overconfidence)
- Frydman & Rangel 2014 (debiasing via saliency reduction — UI / display design lessons)
- Genesove & Mayer 2001 (loss aversion in seller behavior — out-of-domain replication of disposition effect)
- Kőszegi & Rabin 2006 (expectations-based reference points — model for changing CEO benchmark mid-challenge)

**Tier 3 — recent / contrarian / replication:**
- Walasek, Mullett, Stewart 2024 / Brown et al. 2024 / re-meta-analysis 2025 (loss aversion robustness debate)
- LLM-trader experimental finance 2024-2025 (LLMs are MORE textbook-rational than humans)
- Prop-firm 2024 industry data (~5-10% pass rate; 70% failures from loss limits)

## 3. Cross-domain handoffs claimed

- Aggregate-market behavior from individual biases → 17 (Behavioral & Adaptive Markets)
- Sentiment-as-data → 17
- Risk-management / Kelly under fat tails → 21
- LLM-as-agent end-to-end trading → 20
- ML asset-pricing → 19

## 4. Gaps and caveats

1. **Loss aversion replication crisis (2018-2025).** Gal-Rucker (2018) → Brown et al. meta-analysis (2024, mean λ ≈ 1.8-2.1) → Walasek-Mullett-Stewart re-meta-analysis (2025, λ ≈ 1.07 in symmetric/unordered conditions). Strong evidence that loss aversion is a real but **methodologically fragile** phenomenon. GTOS implication: the inverted-TP gate and `risk.sl_buffer_atr_multiplier` are well-justified for **asymmetric and ordered** trading contexts (which actual trading is), but blindly invoking λ=2 for academic rigor is no longer defensible.
2. **Few prop-firm / FTMO-style academic studies.** Most "prop-firm psychology" content is industry/blog. The 2024 industry shakeout (80-100 firms exited) is documented but academic replication is missing. Cross-link: Coval-Shumway 2005 + Locke-Mann 2005 + Cohn et al. 2015 are the closest professional-trader laboratory analogs.
3. **No academic Steenbarger replication.** Steenbarger's clinical-experience trading-psychology framework is widely cited in industry but has limited peer-reviewed empirical validation. Treat as practitioner ground-truth, not statistical evidence.
4. **LLM-trader behavioral-bias literature is brand-new (2024-2025).** Findings are converging but not yet replicated — initial result is that LLMs deviate from human heuristic-driven trading, but exhibit different biases (overconfidence in calibration, loss-chasing in risk-taking research). HALLUC-1 / A4-trending-bull GTOS findings should be re-checked against this literature.
5. **Damasio somatic-marker hypothesis remains contested.** Iowa Gambling Task interpretation has critics (Maia & McClelland; Dunn et al.). Useful as a frame for trader-physiology research, not as established mechanism.
6. **Hot-hand fallacy was a fallacy.** Miller & Sanjurjo (2015-2018) overturned the original Gilovich-Vallone-Tversky finding. GTOS implication: **streak-detection logic is statistically defensible**; pure-mean-reversion priors on series of identical outcomes are biased.

## 5. Per-paper entries

---

### Prospect Theory: An Analysis of Decision under Risk
- **id:** P01
- **authors:** Daniel Kahneman, Amos Tversky
- **year:** 1979
- **source:** Econometrica, 47(2), 263-291
- **url:** https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_Tversky_1979_Prospect_theory.pdf
- **subject_population:** experimental (human subjects, gain/loss gambles)
- **abstract:** Foundational descriptive theory of choice under risk. Critiques expected utility theory and develops prospect theory: value is assigned to gains/losses (not final wealth), probabilities replaced by decision weights, value function concave in gains, convex in losses, steeper in losses (loss aversion).
- **key findings:**
  - People underweight outcomes that are merely probable vs. certain (certainty effect → risk aversion in gains, risk-seeking in losses).
  - People discard components shared by all prospects (isolation effect).
  - Value function: concave gains, convex losses, kinked at reference point with loss-aversion slope ratio ~2:1.
  - Probability weighting overweights small probabilities, underweights moderate-high.
  - Predicts reflection effect, fourfold pattern, framing effects.
- **relevance to GTOS:** The single most operative theoretical foundation. Loss-aversion asymmetry directly justifies the inverted-TP auto-correction gate in `permissions.py`; the kink at the reference point (entry price) directly maps to the disposition effect that the OB-retest-edge **harvests as counterparty flow**. Reference-point dependence informs why drawdown psychology dominates strategic CEO decisions (each session's P&L gets re-anchored).
- **potential hypothesis:** Order flow against an institutional OB-retest level should be **disproportionately** loss-averse-driven (concentrated late-stop-out flow) within the first 1-2 ATR adverse moves, consistent with retail/small-fund holders sitting on losing positions and capitulating only at a discrete "give up" threshold. Testable via skew-to-the-stop-side execution timing in OB-retest M5 microstructure.
- **cross-domain links:** 17 (aggregate-market behavior); 21 (Kelly with non-EU preferences)

---

### Advances in Prospect Theory: Cumulative Representation of Uncertainty
- **id:** P02
- **authors:** Amos Tversky, Daniel Kahneman
- **year:** 1992
- **source:** Journal of Risk and Uncertainty, 5, 297-323
- **url:** https://psych.fullerton.edu/mbirnbaum/psych466/articles/Tversky_Kahneman_JRU_92.pdf
- **subject_population:** experimental (human subjects, multi-outcome lotteries)
- **abstract:** Functional form upgrade of 1979 prospect theory: cumulative (rank-dependent) decision weights instead of separable; works for arbitrary outcome distributions including continuous; respects first-order stochastic dominance. Estimates loss-aversion coefficient λ ≈ 2.25 from experimental data.
- **key findings:**
  - Cumulative weighting transforms cumulative probabilities, not raw probabilities.
  - Different weighting functions for gains vs. losses.
  - Empirical estimates: loss aversion λ ≈ 2.25; value-function curvature α ≈ 0.88 (gains), β ≈ 0.88 (losses); probability-weighting parameter γ ≈ 0.61 (gains), δ ≈ 0.69 (losses).
  - Diminishing sensitivity + loss aversion together explain the fourfold pattern.
- **relevance to GTOS:** Provides the **operationally usable** form for any probability-weighting calculation. The estimated λ ≈ 2.25 was treated as a near-universal constant for 30 years and was the basis for the "1R loss = 2R gain to feel even" trader-psychology rule of thumb. K54 / S79 risk-policy work that touches sizing under non-normal returns should use a CPT functional form rather than mean-variance.
- **potential hypothesis:** A drawdown-conditioned reference shift (Kőszegi-Rabin style) reduces effective λ from ~2.25 toward ~1.5 inside drawdowns (as recovery-as-reference replaces breakeven), explaining the "house money / break-even" tendency in Coval-Shumway 2005. GTOS could test this on its own simulation by re-pricing position-sizing utility under drawdown.
- **cross-domain links:** 17, 21

---

### Are Investors Reluctant to Realize Their Losses?
- **id:** P03
- **authors:** Terrance Odean
- **year:** 1998
- **source:** Journal of Finance, 53(5), 1775-1798
- **url:** https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/areinvestorsreluctant.pdf
- **subject_population:** retail (10,000 discount brokerage accounts, US)
- **abstract:** Empirical demonstration of the disposition effect in real retail trading data. Investors are 1.5-2× more likely to sell winners than losers, controlling for taxes and rebalancing, and the behavior is *not* justified by subsequent portfolio performance.
- **key findings:**
  - Proportion of Gains Realized (PGR) > Proportion of Losses Realized (PLR), persistently.
  - Effect is NOT explained by tax-motivated trading (which would produce the opposite pattern, especially in December).
  - Effect is NOT justified by performance — losers continued to underperform.
  - Disposition effect is one direct empirical implication of extending Kahneman-Tversky 1979 to investments.
- **relevance to GTOS:** **Foundational to the OB-retest edge mechanism.** Disposition-effect-laden losers create persistent late stop-out flow when price retests prior structure (their entry zone). The 1.5-2× asymmetry is approximately the same magnitude observed in OB-retest continuation rate (70% mechanical baseline). The CEO's hard-rule "any single trade > 1.5R = emergency stop" is a direct mechanical defense against the same bias in human-supervisor mode.
- **potential hypothesis:** OB-retest continuation rate (currently ~70% rolling-50, decaying to ~60% per F11) tracks the population-average disposition-effect strength among recent counterparties. If retail-share of an instrument's traded volume drops (e.g., crypto-like algorithmic dominance), OB-retest edge should decay correspondingly. Suggests an empirical instrument: regress OB-retest WR on a retail-flow proxy.
- **cross-domain links:** 17 (aggregate market manifestation); 06 (microstructure of stop-out cascades)

---

### Boys Will Be Boys: Gender, Overconfidence, and Common Stock Investment
- **id:** P04
- **authors:** Brad M. Barber, Terrance Odean
- **year:** 2001
- **source:** Quarterly Journal of Economics, 116(1), 261-292
- **url:** https://faculty.haas.berkeley.edu/odean/papers/gender/boyswillbeboys.pdf
- **subject_population:** retail (35,000+ households, US discount brokerage 1991-1997)
- **abstract:** Tests the prediction that overconfident investors trade excessively. Uses gender (men known to be more overconfident in finance) as a predictor. Men trade 45% more than women; trading reduces men's net returns by 2.65pp/year vs 1.72pp for women.
- **key findings:**
  - Men trade 45% more than women.
  - Men's annual net returns 2.65pp below benchmark; women's 1.72pp below.
  - Single men trade 67% more than single women; net cost difference 1.44pp.
  - Trading-volume gap consistent with overconfidence-trading model (Odean 1998 theory paper).
  - Both genders lose to costs; the gap is purely about overconfidence-driven turnover.
- **relevance to GTOS:** Establishes that overconfidence → excessive trading → underperformance, with magnitude. Operationally relevant for the AI-prompt psychology question: Sonnet 4.6 has CR=38%, Opus 4.7 has CR=19%, but Sonnet has higher live WR (69.6% vs 60.9%) — superficially this looks like Opus is more "selective", but it could equivalently be that Opus is *miscalibrated overconfident* (refuses true CANDIDATEs at higher rate, like the Lichtenstein-Fischhoff overconfidence-under-difficulty pattern). Worth testing K54-style classifier output: which side over/underconfidence error mode matches.
- **potential hypothesis:** GTOS's H29 drawdown-position-reduction rule (DD≥8% → 0.5% risk) implicitly accepts that "discipline" requires structural intervention because, like Barber-Odean men, even disciplined traders trade through pain. The mechanical rule out-performs willpower because willpower exhibits Barber-Odean's overconfidence-driven excess trading.
- **cross-domain links:** 17, 19 (overconfidence as feature for ML models)

---

### The Disposition to Sell Winners Too Early and Ride Losers Too Long: Theory and Evidence
- **id:** P05
- **authors:** Hersh Shefrin, Meir Statman
- **year:** 1985
- **source:** Journal of Finance, 40(3), 777-790
- **url:** https://people.bath.ac.uk/mnsrf/Teaching%202011/Shefrin-Statman-85.pdf
- **subject_population:** general decision-maker (theoretical + early empirical)
- **abstract:** First formal theoretical treatment of the disposition effect. Combines mental accounting, regret aversion, self-control, and tax considerations into a unified framework. Argues tax considerations alone cannot explain observed patterns — psychological mechanisms dominate.
- **key findings:**
  - Disposition effect is overdetermined: prospect theory + mental accounting + regret-avoidance + self-control failures.
  - Tax considerations would predict the opposite seasonal pattern from what is observed.
  - Pre-Odean theoretical scaffolding for what would become the Odean 1998 empirical demonstration.
  - Introduced "mental account" concept to investor decision-making.
- **relevance to GTOS:** Mental-accounting framework directly maps to the per-instrument tracking GTOS already maintains (per-symbol heartbeat, per-symbol concurrent-tracker). Self-control framework supports the CEO mental model: don't ask the AI agent to be more disciplined than the human — *encode* discipline in unconditional gates (Gate 0, inverted-TP, kill-switch).
- **potential hypothesis:** Multi-instrument trading strategies with **shared** mental-account framing (e.g., "drawdown across all 7 GTOS instruments") will have lower disposition-driven counterparty flow than single-instrument strategies, because counterparties operate at single-position mental-account level. Tested by comparing OB-retest WR across instruments by retail-share.
- **cross-domain links:** 17

---

### Risk, Uncertainty, and Profit
- **id:** P06
- **authors:** Frank H. Knight
- **year:** 1921
- **source:** Hart, Schaffner & Marx / Houghton Mifflin (book)
- **url:** https://fraser.stlouisfed.org/files/docs/publications/books/risk/riskuncertaintyprofit.pdf
- **subject_population:** general (theoretical)
- **abstract:** Foundational distinction between **risk** (known probability distribution) and **uncertainty** (unknown distribution; "Knightian uncertainty"). Argues entrepreneurial profits are compensation for bearing genuine uncertainty, not measurable risk.
- **key findings:**
  - Risk vs. Knightian uncertainty distinction.
  - Profit from genuine uncertainty cannot be competed away by perfect competition.
  - Uncertainty resists probabilistic decomposition.
  - Conceptual root of subsequent ambiguity-aversion / robust-control literature.
- **relevance to GTOS:** Directly relevant to GTOS's edge-decay framing. The "risk-management" of MFE/risk-per-trade operates on **risk** (we have empirical distributions). But edge-decay (F11, F15, K52) is **Knightian** — the regime-conditioned LONG-side selectivity collapse cannot be probabilistically forecasted from in-sample. GTOS's monitoring infrastructure (rolling-50 OB-continuation, SPRT, kill-switch) is the engineering response to Knightian uncertainty about the edge itself.
- **potential hypothesis:** A pure-risk system (Kelly-optimal under empirical distributions) **systematically under-sizes** safety margin against Knightian regime change. GTOS's `risk_per_trade_pct: 2.0 → 0.5 when DD≥8%` and Phase-3 deployment caps embody an implicit Knightian premium that pure mean-variance optimization would set to zero. Worth quantifying ex post: what's the realized "Knightian premium" (gap between Kelly-optimal and shipped risk-per-trade)?
- **cross-domain links:** 21 (Kelly-with-uncertainty); 02 (out-of-distribution validation methodology)

---

### The Psychophysiology of Real-Time Financial Risk Processing
- **id:** P07
- **authors:** Andrew W. Lo, Dmitry V. Repin
- **year:** 2002
- **source:** Journal of Cognitive Neuroscience, 14(3), 323-339 (also NBER w8508)
- **url:** http://web.mit.edu/Alo/www/Papers/lo_repin2002.pdf
- **subject_population:** professional (10 FX/derivatives traders, Boston financial institution)
- **abstract:** Wired 10 professional traders with skin-conductance, blood-volume-pulse, heart-rate, respiration, EMG, and temperature sensors during live trading. Measured statistically significant autonomic responses correlated with trader-detected market events and volatility regimes.
- **key findings:**
  - Statistically significant electrodermal differences during transient market events vs. control.
  - Significant cardiovascular changes during high-volatility periods.
  - Even highly experienced traders showed strong physiological responses.
  - Suggests emotion is *intrinsic* to real-time financial-risk processing, not a debiasing target.
  - Differences across traders related to experience level.
- **relevance to GTOS:** Empirical support for the GTOS architectural principle that **emotion-in-the-loop is the failure mode**, hence the autonomous-system-with-hard-rules approach. The somatic markers Lo-Repin measure are precisely what lead the CEO (or any trader) to override Gate 0 / resize positions / pull stops in drawdown. The system's value is decoupling decisions from this somatic-marker loop.
- **potential hypothesis:** A trader's somatic-marker intensity (proxied by HRV, skin conductance variance) predicts disposition-effect strength. If true, the per-instrument retail-flow share that drives OB-retest WR could be re-modeled as expected somatic-marker intensity in the average counterparty population.
- **cross-domain links:** 17, 06 (microstructure of stress-driven flow)

---

### Conditions for Intuitive Expertise: A Failure to Disagree
- **id:** P08
- **authors:** Daniel Kahneman, Gary Klein
- **year:** 2009
- **source:** American Psychologist, 64(6), 515-526
- **url:** https://psycnet.apa.org/record/2009-13007-001
- **subject_population:** general decision-maker (review/dialogue)
- **abstract:** Joint statement reconciling heuristics-and-biases (Kahneman) with naturalistic decision-making (Klein). Identifies two **necessary** conditions for valid intuitive expertise: (1) high-validity (regular, predictable) environment, (2) sufficient feedback for the expert to learn the regularities.
- **key findings:**
  - Two-condition test: predictable environment + feedback-rich learning.
  - When both fail: intuition is overconfidence.
  - When both succeed: pattern-matching > deliberation.
  - "Subjective experience" of confident intuition is a poor signal of actual validity.
  - Most managerial / strategic / financial / political contexts FAIL the two-condition test.
- **relevance to GTOS:** Directly applicable to AI-vs-human-trader question. Markets are **medium-validity** environments with **delayed, sparse feedback** — the two-condition test is partially failed. This explains why even Sonnet 4.6 over-emits ob_retest in 100% of frameworks despite POI availability (per Multi-framework dispatch suppression memory) — pattern-strength signals aren't well-calibrated to outcome distributions in this validity regime. K54 ML classifier is structurally an attempt to bypass this calibration failure by training on outcome data directly.
- **potential hypothesis:** AI-prompt-driven trading systems will exhibit characteristic Kahneman-Klein "low-validity intuitive overconfidence" failure modes (high-confidence misclassification on out-of-sample regimes), which is precisely what F15 + A6 + A4 collectively show for XAUUSD H2-2026 LONG cohort. The K54-vs-AI shadow harness (K55) is the empirical comparison that maps directly to this two-condition framework.
- **cross-domain links:** 19, 20

---

### Judgment Under Uncertainty: Heuristics and Biases
- **id:** P09
- **authors:** Amos Tversky, Daniel Kahneman
- **year:** 1974
- **source:** Science, 185(4157), 1124-1131
- **url:** https://sites.socsci.uci.edu/~bskyrms/bio/readings/tversky_k_heuristics_biases.pdf
- **subject_population:** experimental (human subjects, judgment tasks)
- **abstract:** Foundational paper introducing the heuristics-and-biases program. Identifies three primary heuristics — representativeness, availability, anchoring-and-adjustment — and the systematic errors they produce.
- **key findings:**
  - Representativeness heuristic → base-rate neglect, conjunction fallacy, gambler's fallacy / hot-hand mistakes.
  - Availability heuristic → frequency judgment biased by retrievability / vividness.
  - Anchoring-and-adjustment → insufficient adjustment from arbitrary starting values.
  - Heuristics are economical and usually effective but lead to "systematic and predictable errors."
- **relevance to GTOS:** Anchoring is directly load-bearing for OB-retest mechanics — the entry price IS the anchor counterparties cannot adjust away from. Representativeness (recency / hot-hand) is the bias that the GTOS regime-classifier was built to expose: human traders incorrectly assume current regime continues; the K54 classifier gets to bypass this. Availability bias is precisely why CEO can over-weight last-month performance vs. baseline statistics — kill-switch + Gate 0 + quarterly-decay-monitor are debiasing infrastructure.
- **potential hypothesis:** OB-retest WR should be **higher** in instruments with stronger anchoring tendency (e.g., round-number-magnetism gold > index futures > FX-cross). Cross-domain link to 09 (round-number magnetism) tests this directly.
- **cross-domain links:** 09, 17

---

### Risk, Ambiguity, and the Savage Axioms (Ellsberg paradox)
- **id:** P10
- **authors:** Daniel Ellsberg
- **year:** 1961
- **source:** Quarterly Journal of Economics, 75(4), 643-669
- **url:** https://sites.socsci.uci.edu/~bskyrms/bio/readings/ellsberg.pdf
- **subject_population:** experimental (urn-gamble paradox)
- **abstract:** Demonstrates systematic preference violations of Savage's subjective expected utility axioms. Subjects prefer betting on known-distribution urns over unknown-distribution urns even when the expected payoffs are identical. Establishes ambiguity aversion as a distinct phenomenon from risk aversion.
- **key findings:**
  - Ellsberg paradox: two-color urn experiment systematically violates Savage axioms.
  - Distinguishes ambiguity from risk: people prefer measurable risk over Knightian uncertainty.
  - Foundational to the multi-prior / max-min EU literature.
- **relevance to GTOS:** Ambiguity aversion is the formal mechanism behind market-participation puzzles (Cao-Wang-Zhang) and is directly relevant to GTOS's design: the system is built to keep going through ambiguity (regime transitions, edge-decay periods) by mechanism, where a human would freeze. The CEO's pre-deployment-checklist culture is itself an ambiguity-aversion management technology.
- **potential hypothesis:** Counterparty trading volume should drop disproportionately during high-ambiguity regime transitions (proxied by realized-vs-implied volatility divergence). If GTOS continues trading through these (per its design), it should harvest a lower-competition window — an Ellsberg-premium edge. Testable by per-instrument WR conditional on regime-transition flag.
- **cross-domain links:** 21, 16, 11

---

### Do Behavioral Biases Affect Prices? (Coval-Shumway)
- **id:** P11
- **authors:** Joshua D. Coval, Tyler Shumway
- **year:** 2005
- **source:** Journal of Finance, 60(1), 1-34
- **url:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2005.00723.x
- **subject_population:** professional (Chicago Board of Trade proprietary traders)
- **abstract:** Loss-averse traders who suffer morning losses take on substantially more risk in the afternoon, with measurable price impact. The market efficiently distinguishes these distressed trades from informed flow, and prices set by loss-averse traders reverse faster.
- **key findings:**
  - Traders with morning losses are 16% more likely to take above-average afternoon risk.
  - Distressed traders place more trades, larger trades, accumulate more inventory.
  - Their buy-side prices average higher than market; sell-side lower.
  - Price reversal after distressed trades is significantly faster than after informed trades.
  - Direct evidence that emotion-driven flow is identifiable AND mean-reverting.
- **relevance to GTOS:** The empirical analog of the OB-retest edge mechanism, in a different market and at a different time-scale. Distressed counterparty flow is identifiable and mean-reverts; GTOS's edge is recognizing the structural pattern (OB) that signals where distressed flow concentrates. **Critical for CEO operating discipline:** if CEO is the "morning-loss trader" (had a losing session), the right move is reduced position sizing (H29 already implemented) — the literature directly supports the mechanism.
- **potential hypothesis:** OB-retest continuation rate (and WR) should be higher during the **second half** of intraday sessions, after distressed-flow has accumulated. Specifically: London-session morning-loss traders create harvested NY-session OB-retest opportunities. Testable by intraday-time-of-day stratification of GTOS realized R per OB-retest.
- **cross-domain links:** 17, 06 (microstructure of stress flow)

---

### Professional Trader Discipline and Trade Disposition
- **id:** P12
- **authors:** Peter R. Locke, Steven C. Mann
- **year:** 2005
- **source:** Journal of Financial Economics, 76(2), 401-444
- **url:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X0400203X
- **subject_population:** professional (full-time floor futures traders)
- **abstract:** Professional floor traders DO hold losers longer than winners, but do NOT incur measurable cost from the behavior. Discipline measures predict subsequent trading success. Distinguishes "disposition effect as cost" (retail) from "disposition effect as feature" (professional discipline).
- **key findings:**
  - Professional traders DO hold losers longer than winners (disposition effect present).
  - But NO performance cost detected for the behavior.
  - Discipline measures (low time-to-loss-realization, low time-to-gain-realization mismatch) predict survival.
  - Successful pros are characterized by relative — not absolute — discipline.
  - Trading discipline IS a measurable trait, predicts who keeps trading.
- **relevance to GTOS:** Critical empirical finding that professional success ≠ absence of disposition effect, but RELATIVE discipline. Directly maps to GTOS engineering: don't try to eliminate AI's emergent biases, **measure them and gate the worst ones with hard rules**. The 2026-04-27 KEPT touch_count_reject_threshold=2 decision (vs. LOOSEN_TO_3) is precisely a relative-discipline call: GTOS doesn't need to ELIMINATE all touch-2 trades, just stay on the disciplined side of the threshold.
- **potential hypothesis:** GTOS's emergent "AI selectivity collapse" in trending_bull (per F2/F15) is structurally the same phenomenon as Locke-Mann's undisciplined floor traders: the AI's pattern-matching is functioning, but its disposition-relative-to-baseline is degraded. Predicts that an "AI discipline score" (entry-vs-mean-position, exit-distance-from-OB, etc.) will predict realized R better than raw signal score. Maps directly to K54 baseline.
- **cross-domain links:** 17, 19 (discipline as ML feature)

---

### Experts, Amateurs, and Real Estate: An Anchoring-and-Adjustment Perspective
- **id:** P13
- **authors:** Gregory B. Northcraft, Margaret A. Neale
- **year:** 1987
- **source:** Organizational Behavior and Human Decision Processes, 39, 84-97
- **url:** https://www.smallprojectsbureau.com/wp-content/uploads/2020/01/northcraft_neale.pdf
- **subject_population:** professional + amateur (21 real estate agents, 7+ years average; plus undergraduate amateurs)
- **abstract:** Listing-price anchors significantly biased property valuations even among 7-year-experienced real-estate professionals. Effect was the same magnitude in experts as amateurs.
- **key findings:**
  - Listing-price anchor influenced ALL four estimate measures, in both experts and amateurs.
  - Experts denied being influenced when explicitly asked.
  - Real-world domain (not just lab) replication of anchoring.
  - Expertise is NOT a debiasing path against anchoring.
- **relevance to GTOS:** Critical evidence that expertise alone doesn't debias anchoring. Direct AI parallel: reasoning-heavy / max-effort prompting does not necessarily reduce anchoring on the visible MSO `current_price` value. The HALLUC-1 bug was precisely an anchoring failure on AI side (the displayed-value precision propagated into AI's stop_loss arithmetic). For the OB-retest mechanism, anchoring is the foundation: counterparties anchor on entry price; GTOS anchors on structural OB level — the anchor-mismatch is the edge.
- **potential hypothesis:** Reducing salience of `current_price` in AI prompts (replace decimal value with "current price NEAR upper edge of FVG zone") would reduce HALLUC-class precision-anchoring errors. Cross-link: Frydman-Rangel 2014 saliency-debiasing.
- **cross-domain links:** 09 (round-number anchors), 19

---

### Investor Psychology and Security Market Under- and Overreactions
- **id:** P14
- **authors:** Kent D. Daniel, David Hirshleifer, Avanidhar Subrahmanyam
- **year:** 1998
- **source:** Journal of Finance, 53(6), 1839-1885
- **url:** https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00077
- **subject_population:** general (theoretical model + empirical test)
- **abstract:** Theory of market under- and overreactions based on two psychological biases: investor overconfidence about private-information precision, and biased self-attribution (asymmetric updating). Predicts negative long-lag autocorrelations (overreaction reversal), excess volatility, public-event return predictability, AND positive short-lag autocorrelations / momentum / earnings drift.
- **key findings:**
  - Overconfidence about private-information precision → excess volatility + overreaction.
  - Biased self-attribution → momentum, earnings drift.
  - Combined: negative long-lag autocorrelations, positive short-lag autocorrelations.
  - One of the two foundational models linking psychological bias to asset-pricing facts (other is Barberis-Shleifer-Vishny 1998).
- **relevance to GTOS:** Self-attribution-bias dynamics directly apply to the AI agent: the AI takes credit for winning regimes (regime-conditioned LONG-bull cohort 2026 H1) and externalizes losing regimes (H2 collapse) when extracting "learnings". Without explicit framework for this, AI evolution becomes self-reinforcing on profitable cohorts. **The shadow-logger architecture is the engineering response** — outcome data is collected unfiltered, not interpreted by the AI.
- **potential hypothesis:** Live AI rationale (when extracted from `shadow_logs/`) should exhibit measurable self-attribution asymmetry: more detail / certainty in winning-trade post-mortems than losing-trade ones. Testable via length / sentiment / explicit-statistic-citation analysis on existing rationale logs.
- **cross-domain links:** 17, 19, 20

---

### CEO Overconfidence and Corporate Investment
- **id:** P15
- **authors:** Ulrike Malmendier, Geoffrey Tate
- **year:** 2005
- **source:** Journal of Finance, 60(6), 2661-2700
- **url:** https://eml.berkeley.edu/~ulrike/Papers/OCinvestment23november2004_full_jf.pdf
- **subject_population:** professional / executive (Forbes 500 CEOs, 1980-1994)
- **abstract:** Identifies overconfident CEOs via reluctance to reduce personal exposure to firm-specific risk. Overconfident CEOs overinvest when internal cash flow is abundant; underinvest when external financing required.
- **key findings:**
  - CEO overconfidence persistently fails to diversify against firm-specific risk.
  - Overconfident CEOs show stronger investment-cash-flow sensitivity.
  - Effect concentrated in equity-dependent firms.
  - Demonstrates that overconfidence affects high-stakes professional decisions, not just retail.
- **relevance to GTOS:** Direct CEO-operational-discipline relevance. The same overconfidence-driven over-/under-investment pattern applies to deployment-phase decisions: when GTOS is winning (H1 2026), there's a temptation to over-deploy (more instruments, larger size); when losing (H2), to underinvest in research / pivot. The structural responses — phased deployment, fixed-deployment-phase Gate 0, kill-switch — formally manage this.
- **potential hypothesis:** A measurable "GTOS deployment-overconfidence" signal: gap between proposed risk-per-trade in CEO ad-hoc-asks vs. shipped. If post-mortem data shows the gap correlates with subsequent realized DD, the hard rule "risk_per_trade_pct stays at 2.0" is empirically validated.
- **cross-domain links:** 17, 22 (hedge-fund alpha & CEO overconfidence in funds)

---

### Endogenous Steroids and Financial Risk-Taking on a London Trading Floor
- **id:** P16
- **authors:** John M. Coates, Joe Herbert
- **year:** 2008
- **source:** Proceedings of the National Academy of Sciences, 105(16), 6167-6172
- **url:** https://www.pnas.org/doi/10.1073/pnas.0704025105
- **subject_population:** professional (17 male London FX/derivatives traders, 8 days)
- **abstract:** Morning testosterone level predicts day's profitability (14/17 traders had higher P&L on high-T days). Cortisol rises with both intra-trader return variance AND market volatility. Endogenous steroids modulate trader risk preference in real time.
- **key findings:**
  - Higher morning testosterone → higher P&L that day.
  - Cortisol tracks both individual-trader and market-wide risk variance.
  - Acute steroid elevation could reinforce + amplify volatility-driven risk aversion / seeking.
  - Mechanism for "risk on / risk off" cycles linked to trader-population endocrinology.
- **relevance to GTOS:** Empirical evidence that human-trader risk preferences are endocrinologically modulated, hence inherently unstable across days/weeks. Strong argument for autonomous-system architecture: GTOS's kill-zone schedule operates with literally invariant risk preferences; counterparty population's risk preferences shift hour-to-hour with steroid cycles. The OB-retest edge is partly the difference between GTOS's invariant risk-rule and counterparties' steroid-modulated risk rule.
- **potential hypothesis:** OB-retest WR should be HIGHER during high-realized-volatility kill zones (where counterparty cortisol is elevated, distorting their risk-preferences). Testable by stratifying GTOS realized R per OB-retest by current-day VIX (or instrument-specific RV).
- **cross-domain links:** 17, 16

---

### The Neural Basis of Financial Risk Taking
- **id:** P17
- **authors:** Camelia M. Kuhnen, Brian Knutson
- **year:** 2005
- **source:** Neuron, 47(5), 763-770
- **url:** https://www.cell.com/neuron/fulltext/S0896-6273(05)00657-4
- **subject_population:** experimental (fMRI, healthy adults, financial choice task)
- **abstract:** Distinct neural circuits predict risk-seeking vs. risk-averse mistakes in financial decision-making. Nucleus accumbens activation precedes risk-seeking choices and risk-seeking errors; anterior insula activation precedes riskless choices and risk-aversion errors.
- **key findings:**
  - Two distinct neural circuits, each predicting a distinct error class.
  - Nucleus accumbens (reward circuit) → risk-seeking errors.
  - Anterior insula (aversion circuit) → risk-aversion errors.
  - Excessive activation of either → mistakes.
  - First neural-level evidence that financial risk-taking has dual mechanisms (not single risk-preference parameter).
- **relevance to GTOS:** Suggests that "risk preference" is not a single parameter but a dual-circuit balance. Operationally, this means GTOS's H29 drawdown-position-reduction (reducing risk in drawdown) addresses one circuit (insula-driven risk-aversion errors), while the kill-switch / Gate 0 architecture addresses the other (NAcc-driven risk-seeking errors). Both are needed.
- **potential hypothesis:** GTOS prompt design (Sonnet 4.6 effort=max) implicitly balances both circuits. A direct test: A/B prompts that emphasize "risk-control" framing (insula-priming) vs "edge-capture" framing (NAcc-priming) should produce systematically different CR rates and outcome distributions, even with identical pre-AI POI input.
- **cross-domain links:** 17, 19, 20

---

### Fear and Greed in Financial Markets: A Clinical Study of Day-Traders
- **id:** P18
- **authors:** Andrew W. Lo, Dmitry V. Repin, Brett N. Steenbarger
- **year:** 2005
- **source:** American Economic Review (P&P), 95(2), 352-359 (also NBER w11243)
- **url:** http://web.mit.edu/Alo/www/Papers/lorepsteen4.pdf
- **subject_population:** retail/active (80 day-traders, 5-week interval study)
- **abstract:** Day-traders with **more intense** emotional reactions (positive AND negative) to gains/losses had **significantly worse** trading performance. Standardized personality inventory failed to identify a "trader personality profile" — emotional regulation matters more than personality.
- **key findings:**
  - Intense emotional reactions on BOTH sides → worse performance.
  - No "trader personality profile" survives.
  - Emotion regulation, not absence of emotion, is the actionable variable.
  - Confirms Lo-Repin 2002 finding at scale (80 vs 10 subjects).
- **relevance to GTOS:** Bridges Lo-Repin physiological work to performance. Empirically supports the GTOS architectural choice: NOT trying to make AI "less emotional" (which is mostly a moot question for an LLM anyway), but adding hard infrastructure to **decouple decisions from any emotional / state-dependent loop**. Maps directly to the operator playbook documents (`.context/05_operations/`) — the playbooks are emotion-regulation infrastructure for the human in the loop.
- **potential hypothesis:** Per Lo-Repin-Steenbarger, emotional intensity is the controllable variable. For human-in-the-loop systems like GTOS, the per-session journaling + checklist culture should produce measurable improvements in CEO discipline metrics over time (e.g., fewer override events). Already implicit in CLAUDE.md "10 reliability rules".
- **cross-domain links:** 17

---

### Investor Psychology and Asset Pricing (survey)
- **id:** P19
- **authors:** David Hirshleifer
- **year:** 2001
- **source:** Journal of Finance, 56(4), 1533-1597
- **url:** https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00379
- **subject_population:** general (review article)
- **abstract:** Comprehensive survey: behavioral finance has moved from purely-rational paradigm to one where security expected returns are determined by both risk AND mispricing. Catalogs decision biases and reviews how they propagate to prices.
- **key findings:**
  - Catalogs decision biases relevant to financial markets.
  - Frames behavioral finance as the "vibrant flux" successor to purely-rational asset pricing.
  - Single most-cited (2,000+ citations) survey of investor-psychology evidence.
- **relevance to GTOS:** Useful as a comprehensive cross-reference. For the GTOS edge mechanism, the relevant claim is: behavioral biases drive **systematic** mispricing patterns (not noise), which is the precondition for any pattern-based edge.
- **potential hypothesis:** Comprehensive scaffold; no single hypothesis but a meta-hypothesis: every persistent edge has a corresponding catalogued bias as its mechanism. For OB-retest, the bias is disposition + anchoring (P03 + P09 + P13).
- **cross-domain links:** 17

---

### Overconfident Investors, Predictable Returns, and Excessive Trading
- **id:** P20
- **authors:** Kent D. Daniel, David Hirshleifer
- **year:** 2015
- **source:** Journal of Economic Perspectives, 29(4), 61-88
- **url:** https://www.aeaweb.org/articles?id=10.1257/jep.29.4.61
- **subject_population:** general (review)
- **abstract:** Reviews evidence that psychological bias affects economic actors' behavior; high trading volume and price predictability are difficult to reconcile with rational models. Centers overconfidence as the unifying explanation.
- **key findings:**
  - Confirms 14-year evidence: overconfidence remains the most-evidenced psychological bias for asset markets.
  - Excessive trading is overconfidence's most robust empirical signature.
  - Predictable-return patterns (momentum, reversal, post-event drift) consistent with overconfidence-based models.
  - Updates Daniel-Hirshleifer-Subrahmanyam 1998 with 2000s evidence.
- **relevance to GTOS:** Directly relevant to AI prompt-design questions. If overconfidence is the unifying market bias, GTOS's edge-capture is partly counterparty-overconfidence-arbitrage. The MSO gate's CR rate (~10.3% baseline) is implicitly a selectivity reservation against overconfidence — accept only patterns clear enough to overcome counterparty-overconfidence-driven noise.
- **potential hypothesis:** Sonnet 4.6's higher CR (38%) vs Opus 4.7's (19%) on the MSO gate may reflect Sonnet being **less overconfident in its uncertainty** — i.e., more willing to call CANDIDATE on borderline patterns where Opus over-rejects. If true, the live WR comparison (69.6% vs 60.9%) is consistent with Sonnet being correctly-calibrated on a higher-recall point of the precision-recall curve.
- **cross-domain links:** 17

---

### Gambling with the House Money and Trying to Break Even
- **id:** P21
- **authors:** Richard H. Thaler, Eric J. Johnson
- **year:** 1990
- **source:** Management Science, 36(6), 643-660
- **url:** https://business.columbia.edu/sites/default/files-efs/pubfiles/1154/thaler_and_johnson.pdf
- **subject_population:** experimental (sequential-gamble subjects)
- **abstract:** Decision-makers' risk preferences depend on prior outcomes within a mental account. Prior gains increase willingness to take subsequent risk ("house money effect"); prior losses make break-even gambles disproportionately attractive ("break-even effect").
- **key findings:**
  - House money effect: prior gains → increased subsequent risk-taking.
  - Break-even effect: prior losses → preference for risky gambles offering chance to break even.
  - Both effects refute the "ignore prior outcomes" rationality requirement.
  - Mental-account framework formalized.
- **relevance to GTOS:** Direct foundation for the "GTOS-in-drawdown" risk paradox. Without H29 / Gate 0, an undisciplined system would EITHER raise risk during drawdown (break-even effect, classic "revenge trading") OR raise risk during winning streaks (house-money effect, classic "tilt"). The shipped GTOS architecture defends against BOTH (H29 lowers DD risk; deployment-phase locks in winning-streak risk).
- **potential hypothesis:** Counterparty break-even-effect flow concentrates near the prior local high after a 1-2 ATR drawdown — exactly the price level where OB-retest setups appear. Implies OB-retest entries should systematically encounter break-even-effect-driven counterparties just AFTER the structural OB level is reclaimed, not before.
- **cross-domain links:** 17, 21

---

### Evidence for Countercyclical Risk Aversion: An Experiment with Financial Professionals
- **id:** P22
- **authors:** Alain Cohn, Jan Engelmann, Ernst Fehr, Michel André Maréchal
- **year:** 2015
- **source:** American Economic Review, 105(2), 860-885
- **url:** https://www.aeaweb.org/articles?id=10.1257/aer.20131314
- **subject_population:** professional (financial professionals primed with bust/boom scenario)
- **abstract:** Financial professionals primed with a "bust" scenario showed substantially higher risk aversion than those primed with "boom", with measured fear-arousal mediating the effect. Demonstrates that risk aversion is **causally** modulated by macro-priming, not just correlated.
- **key findings:**
  - Bust-primed professionals were significantly more risk-averse.
  - Self-reported fear mediated the effect.
  - Direct causal evidence for countercyclical risk aversion in professionals (not just retail).
  - Major puzzle (high asset-price volatility) candidate-explained.
- **relevance to GTOS:** Empirical validation that even professional traders' risk preferences shift with macro framing. Justifies GTOS's quarterly-decay-monitor + S1 monthly-decay-monitor architecture: the **measurement** of decay must be mechanical, not narrative-dependent, because narrative ("the market is regime-shifting") biases the measurement.
- **potential hypothesis:** GTOS strategic decisions made during/right after drawdowns will tend toward **excess** safety (too-conservative position sizing, too-aggressive risk-reduction). This aligns with the empirical pattern observed in items #4 (XAUUSD H2 LONG decay): the impulse to halt LONG trading entirely is the classical countercyclical-risk-aversion response. The S79 risk-policy maintained 2.0% (didn't reduce) precisely against this bias.
- **cross-domain links:** 17, 21

---

### Loss Aversion and Seller Behavior: Evidence from the Housing Market
- **id:** P23
- **authors:** David Genesove, Christopher Mayer
- **year:** 2001
- **source:** Quarterly Journal of Economics, 116(4), 1233-1260
- **url:** https://academic.oup.com/qje/article/116/4/1233/1903212
- **subject_population:** retail (Boston condominium sellers, 1990s)
- **abstract:** Out-of-stocks replication of disposition / loss-aversion: condominium sellers facing nominal losses set higher list prices, achieve higher sale prices, but face MUCH lower sale hazard. Magnitude: 25-35% of expected-vs-purchase-price gap reflected in list prices; 3-18% in sale prices.
- **key findings:**
  - Loss-faced sellers list 25-35% of (expected - purchase) gap higher.
  - Realize 3-18% of the gap in sale price.
  - Sale hazard much lower for loss-faced sellers.
  - Disposition-effect generalizes beyond stocks.
- **relevance to GTOS:** Critical out-of-domain replication — disposition effect is asset-class general. Strengthens confidence that the OB-retest edge mechanism (counterparty-disposition-flow) generalizes across the 7 GTOS instruments, despite different microstructures.
- **potential hypothesis:** OB-retest edge magnitude should be similar (within constant-factor) across asset classes if disposition-effect intensity is similar. Cross-instrument WR variance at GTOS (XAUUSD 62%, US30 58.5%, USDJPY 75.8%, GBPJPY 57.1%) is consistent with this — bounded variance, all > 50% baseline.
- **cross-domain links:** 17, 11 (FX), 12 (equity indices)

---

### Using Neural Data to Test a Theory of Investor Behavior: An Application to Realization Utility
- **id:** P24
- **authors:** Cary Frydman, Nicholas Barberis, Colin Camerer, Peter Bossaerts, Antonio Rangel
- **year:** 2014
- **source:** Journal of Finance, 69(2), 907-946
- **url:** https://nicholasbarberis.github.io/neuro_jf.pdf
- **subject_population:** experimental (fMRI subjects, simulated stock market)
- **abstract:** Direct neural evidence for "realization utility" theory of investor behavior — utility derived from the ACT of realizing gains/losses (not just from final wealth). Subjects exhibit disposition effect; vmPFC activation tracks predictions of realization-utility model at moment of sell.
- **key findings:**
  - All subjects show disposition effect, even with information that makes selling losers optimal.
  - vmPFC activity at sell-decision tracks realization-utility model (not pure-EU model).
  - First neural test of an asset-pricing-theory mechanism.
  - Provides mechanistic underpinning for disposition effect.
- **relevance to GTOS:** Confirms disposition effect is neurologically grounded — meaning it CANNOT be eliminated by retail education / experience / discipline alone (Locke-Mann shows pros only relatively manage it). The OB-retest edge should remain robust as long as retail / undisciplined-pro counterparty flow exists. **Decay risk:** if retail share of an instrument's flow drops dramatically (algorithmic / passive), the OB-retest edge should compress — matches the F11 finding that OB-zone-advantage degraded from +16.8pp pre-2026 to +4.6pp H2-2026.
- **potential hypothesis:** Per-instrument OB-retest decay velocity correlates with growth in algorithmic / index / passive share of that instrument's flow. The fact that XAUUSD shows the strongest decay is consistent with growing CTA / algorithmic gold flow (precious-metals quants).
- **cross-domain links:** 17, 10 (gold)

---

### Debiasing the Disposition Effect by Reducing the Saliency of Information about a Stock's Purchase Price
- **id:** P25
- **authors:** Cary Frydman, Antonio Rangel
- **year:** 2014
- **source:** Journal of Economic Behavior and Organization, 107B, 541-552
- **url:** https://www.rnl.caltech.edu/publications/pdf/frydman2014a.pdf
- **subject_population:** experimental (Caltech students, simulated stock-trading)
- **abstract:** Reducing the visual prominence of a stock's purchase price reduced the disposition effect by 25%. Suggests purchase-price salience is causally upstream of the bias, not just correlated.
- **key findings:**
  - Disposition effect 25% smaller when purchase price is not displayed.
  - Effect was still present (not eliminated), but reduced.
  - Demonstrates UI-design has measurable behavioral consequences.
  - Implies trading platforms can be designed to debias.
- **relevance to GTOS:** Direct guidance for AI-prompt design. The MSO format / order-block representation in GTOS prompts is the AI's UI; salience choices in that representation matter for AI behavior. The HALLUC-1 bug provides a concrete example: the displayed `current_price` decimal precision drove downstream AI rounding errors. Reducing decimal salience (as discussed in P13 hypothesis) is the Frydman-Rangel-style intervention.
- **potential hypothesis:** A/B testing prompt versions with different OB / FVG / current-price salience SHOULD measurably affect AI selectivity (CR rate), inverted-TP rate, and L2 rejection rate. The intervention is essentially zero-cost (just prompt edit).
- **cross-domain links:** 19, 20

---

### A Survey of Behavioral Finance
- **id:** P26
- **authors:** Nicholas Barberis, Richard H. Thaler
- **year:** 2003
- **source:** Handbook of the Economics of Finance, Ch. 18, 1053-1128
- **url:** https://nicholasbarberis.github.io/ch18_6.pdf
- **subject_population:** general (handbook chapter)
- **abstract:** Comprehensive handbook chapter. Behavioral finance has two pillars: (1) limits to arbitrage (why mispricings persist), (2) psychology (which biases produce mispricings). Reviews evidence at aggregate-market, cross-sectional, individual-trading, and corporate-finance levels.
- **key findings:**
  - Two-pillar structure: limits-to-arbitrage + psychology.
  - Reviews disposition, overconfidence, framing, mental accounting, conservatism.
  - Catalogs behavioral asset-pricing models.
  - Sets standards for what counts as a "behavioral" explanation.
- **relevance to GTOS:** Foundational reference. Critical concept for GTOS: **limits to arbitrage** explains why the OB-retest edge can persist even though it's "obvious". Capacity-constraint, capital-constraint, position-management-constraint, and time-horizon-constraint all limit how much a smart counterparty can correct the disposition-driven mispricing. GTOS's small size + autonomous execution means it operates within those limits, harvests the residual.
- **potential hypothesis:** GTOS edge magnitude should DECAY as it scales — when GTOS turnover crosses some fraction of the disposition-counterparty-flow, its own flow erodes the mispricing. This is structurally consistent with edge-decay (F11 / F15) but the alternative explanation (regime change) is more likely at GTOS's current scale.
- **cross-domain links:** 17, 22

---

### The Framing of Decisions and the Psychology of Choice
- **id:** P27
- **authors:** Amos Tversky, Daniel Kahneman
- **year:** 1981
- **source:** Science, 211(4481), 453-458
- **url:** https://sites.stat.columbia.edu/gelman/surveys.course/TverskyKahneman1981.pdf
- **subject_population:** experimental (Asian disease problem, etc.)
- **abstract:** Same options framed as gains vs. losses produce systematically different choices ("Asian disease problem"). Establishes framing as a fundamental violation of descriptive invariance — a cornerstone of rational choice.
- **key findings:**
  - "Asian disease": survival framing → 72% choose risk-averse Program A; mortality framing → majority choose risk-seeking equivalent.
  - Framing effects are robust across stakes and replicated thousands of times.
  - Violation of descriptive invariance → rational-choice theory descriptively wrong.
  - Risk-averse over gains; risk-seeking over losses (consistent with prospect theory).
- **relevance to GTOS:** Direct AI prompt-design implications. The same MSO can be framed as "high-quality entry opportunity" vs "moderate-risk entry with downside" — these will produce different CR rates from the AI gate. The GTOS prompt's explicit framing in `prompts/` requires CEO approval *precisely* because framing has measurable behavioral consequences. ADR-006 parallel-evaluation dispatch (vs. ob_retest-first cascade) is a framing change documented as an architectural decision.
- **potential hypothesis:** The Multi-framework dispatch suppression finding (36.77% fvg-only POI but 100% ob_retest emission, per project memory) is a classic framing effect: the prompt's order-of-mention frames ob_retest as the default. ADR-006 parallel-evaluation should partially correct this. Testable: post-ADR-006 framework-distribution should align with pre-AI POI availability ratios.
- **cross-domain links:** 19, 17

---

### Preference and Belief: Ambiguity and Competence in Choice under Uncertainty
- **id:** P28
- **authors:** Chip Heath, Amos Tversky
- **year:** 1991
- **source:** Journal of Risk and Uncertainty, 4, 5-28
- **url:** https://courses.washington.edu/pbafhall/514/514%20Readings/ambiguity%20and%20competence.pdf
- **subject_population:** experimental
- **abstract:** Competence hypothesis: people prefer betting on their own (ambiguous) judgment over equiprobable chance bets when they consider themselves knowledgeable, even paying a premium. Refutes pure ambiguity-aversion explanation.
- **key findings:**
  - Self-perceived competence reverses ambiguity preferences.
  - In their domain of expertise, people SEEK ambiguity.
  - Effect is about credit/blame attribution, not pure information.
  - Refines Ellsberg paradox: ambiguity attitude is domain-specific, competence-modulated.
- **relevance to GTOS:** Critical for understanding AI behavior on specialty trading patterns. AI may exhibit *competence-driven over-acceptance* on patterns that were heavily represented in training (vs. *ambiguity-driven over-rejection* on patterns that weren't). Maps to the framework-distribution problem: AI heavily prefers ob_retest because its prompt + training represents this pattern most concretely.
- **potential hypothesis:** AI's framework-distribution skew (per Multi-framework dispatch suppression) is structurally a Heath-Tversky competence preference: AI emits the framework where it feels most "competent" (ob_retest), even when other frameworks have higher POI availability. Predicts: explicit prompt language asserting framework-equivalence will only partially correct this, because the underlying competence-based preference is robust.
- **cross-domain links:** 17, 19, 20

---

### Loss aversion is not robust: A re-meta-analysis (contrarian)
- **id:** P29
- **authors:** Lukasz Walasek, Timothy Mullett, Neil Stewart (and prior work by Gal & Rucker)
- **year:** 2025 (with 2018, 2024 antecedents)
- **source:** Journal of Economic Psychology (Feb 2025) + Gal & Rucker 2018 + Brown et al. 2024
- **url:** https://www.sciencedirect.com/science/article/abs/pii/S0167487025000133
- **subject_population:** experimental (re-meta-analysis of 607 estimates, 150 articles)
- **abstract:** Re-meta-analysis of Brown et al. 2024 dataset: when studies are stratified by methodological choice (asymmetric vs symmetric gains/losses, ordered vs unordered), the symmetric-unordered subset has loss-aversion coefficient λ ≈ 1.07 (not significantly above 1.0). Suggests apparent λ ≈ 2 was an artifact of methodology.
- **key findings:**
  - Brown et al. 2024 meta-analysis: λ ≈ 1.8-2.1 across 607 estimates.
  - Walasek-Mullett-Stewart 2025: λ ≈ 1.07 in symmetric-unordered subset.
  - Loss aversion as a **universal** constant is no longer empirically supported.
  - Loss aversion as a **context-dependent** phenomenon (asymmetric framing, ordered presentation, real-money stakes) survives.
  - Major contrarian finding for canonical behavioral-finance literature.
- **relevance to GTOS:** Forces honesty about how strong the loss-aversion claim is. **Trading is asymmetric and ordered by nature** (trader has a chosen entry, watches direction-by-direction movement) — so the stronger λ ≈ 2 estimate likely DOES apply to trading. But the claim "humans always lose-averse 2:1" is no longer valid; treat as a context-dependent operating constant.
- **potential hypothesis:** GTOS-relevant loss-aversion intensity is closer to λ ≈ 2 (asymmetric, ordered context) but should be re-estimated empirically from per-instrument behavioral data rather than borrowed from cross-domain meta-analysis. K54 features could include an instrument-specific loss-aversion-proxy derived from order-flow asymmetry around stop-out clusters.
- **cross-domain links:** 17, 21, 02 (replication crisis methodology)

---

### Surprised by the Gambler's and Hot Hand Fallacies? A Truth in the Law of Small Numbers
- **id:** P30
- **authors:** Joshua B. Miller, Adam Sanjurjo
- **year:** 2018 (Econometrica) / 2015 SSRN
- **source:** Econometrica, 86(6), 2019-2047 / SSRN 2627354
- **url:** https://papers.ssrn.com/abstract=2627354
- **subject_population:** experimental + statistical re-analysis (basketball shooting + theoretical)
- **abstract:** Demonstrates a **statistical bias** in the original Gilovich-Vallone-Tversky 1985 hot-hand finding. When hits/misses are counted starting after a streak, finite-sample selection produces a downward bias in continuation-rate estimates. Correctly analyzed, the original data DO show a hot hand. Reverses the canonical "hot hand is fallacy" claim.
- **key findings:**
  - Selection-conditional finite-sample bias was missed in original GVT 1985 work.
  - Correctly analyzed, hot hand IS real (effect size meaningful in basketball data).
  - Implications: gambler's fallacy may be a **rational** response to the same statistical structure.
  - Major reversal for canonical behavioral-finance teaching.
- **relevance to GTOS:** Streak-based decision rules are NOT automatically irrational. Statistical orthodoxy "do not chase streaks, mean-reversion always" is empirically wrong in many contexts. This validates GTOS's "consecutive losses on a single instrument > 5 = emergency stop" rule — it accepts that streaks are real, plans for them.
- **potential hypothesis:** GTOS realized R per OB-retest should exhibit positive autocorrelation conditional on regime stability (per instrument). The 5-consecutive-loss kill-rule implicitly assumes streaks happen — Miller-Sanjurjo says this assumption is empirically validated. Testable: WR conditional on previous-trade-outcome should not equal unconditional WR.
- **cross-domain links:** 17, 02 (statistical methodology)

---

### Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective
- **id:** P31
- **authors:** Andrew W. Lo
- **year:** 2004
- **source:** Journal of Portfolio Management, 30(5), 15-29
- **url:** https://web.mit.edu/Alo/www/Papers/JPM2004_Pub.pdf
- **subject_population:** general (theoretical synthesis)
- **abstract:** Reconciles efficient markets with behavioral finance via evolutionary framework: behavioral biases stem from heuristics adapted to non-financial contexts, and market efficiency depends on the population mix of heuristic-using vs. rational agents. Edge persistence is determined by adaptation rate vs. environment change rate.
- **key findings:**
  - Evolutionary framework reconciles EMH with behavioral finance.
  - Edges persist when their counterparty heuristic is widespread + costly to debias.
  - Edge decay is structural — populations adapt.
  - Provides theoretical scaffolding for empirical edge-decay observations.
- **relevance to GTOS:** **The single most-relevant theoretical framework for GTOS edge-decay management.** F11 (OB-zone advantage decay velocity), F15 (regime-conditioned LONG-side selectivity collapse), K52 (FVG-in-impulse signal reversal) are all examples of Lo's "adaptation rate vs. environment change rate" framework playing out empirically. The shipped monitoring infrastructure (rolling-50, S1 monthly-decay) is engineered specifically against this dynamic.
- **potential hypothesis:** Per the AMH framing, GTOS should expect ALL its empirical edges to decay on a timescale set by counterparty-population adaptation. The key uncertainty is the half-life: months (fast) or years (slow). Continuous re-validation (rolling-50 OB-continuation, K52-style Validated Numbers re-test) is the essential operating discipline.
- **cross-domain links:** 17, 22

---

### Why Do (Some) Households Trade So Much?
- **id:** P32
- **authors:** Juhani T. Linnainmaa
- **year:** 2011
- **source:** Review of Financial Studies, 24(5), 1630-1666
- **url:** https://academic.oup.com/rfs/article-abstract/24/5/1630/1614746
- **subject_population:** retail (Finnish household trading data, large structural model)
- **abstract:** Households trade actively to *learn* about their own ability, even when they expect to lose from active investing. Reconciles excessive-trading puzzle with optimization: rational learning + ability uncertainty produces the observed pattern.
- **key findings:**
  - Households' returns from active investing are downward-biased estimates of true ability.
  - Trading intensity declines with experience (consistent with learning).
  - Households start small.
  - Provides rational micro-foundation for excessive-trading observations.
- **relevance to GTOS:** Suggests that a substantial portion of GTOS's counterparty flow comes from "learners" — retail traders trading partly to discover their own ability. This flow is structurally inefficient (they trade through losses to learn) and is a stable source of OB-retest counterparty volume. Decay risk: if learner-flow declines (e.g., gamification UI removed), OB-retest edge decays.
- **potential hypothesis:** Per-instrument retail-learner flow (proxied by retail account-opening rate per instrument) predicts that instrument's OB-retest edge intensity. Crypto-trader migration to gold (anecdotal post-FTX) could be a temporary tailwind to XAUUSD edge; a learner-burnout cycle would be the structural headwind.
- **cross-domain links:** 17, 22

---

### Do Individual Day Traders Make Money? Evidence from Taiwan
- **id:** P33
- **authors:** Brad M. Barber, Yi-Tsung Lee, Yu-Jane Liu, Terrance Odean
- **year:** 2014
- **source:** Working paper / Review of Financial Studies (2014/2017+)
- **url:** http://www.econ.yale.edu/~shiller/behfin/2004-04-10/barber-lee-liu-odean.pdf
- **subject_population:** retail (entire Taiwan stock market day-traders, 1992-2006)
- **abstract:** Comprehensive empirical assessment of retail day-trading profitability. <1% of day-traders are predictably profitable; ~20% positive net of fees over the studied period. Survival rate at 3 years: 15%.
- **key findings:**
  - <1% of day-traders predictably profitable.
  - ~20% positive net of fees.
  - 15% three-year survival.
  - Even heavy traders (>$20k/day) have ~19% positive abnormal returns.
- **relevance to GTOS:** Quantifies the failure rate of disciplined retail trading (the alternative to the autonomous-system approach). Empirical justification for the GTOS architectural choice: the failure mode for unaided humans is NOT marginal underperformance, it's catastrophic survival rates.
- **potential hypothesis:** GTOS's expected success rate (over a multi-year horizon, conditional on the system surviving methodology / decay management) should be benchmarked against the <1% / 15% Barber-Lee-Liu-Odean baseline. If GTOS sustains >0% expected R after 3 years live (with rigorous monitoring), it has materially beaten the empirical retail counterfactual.
- **cross-domain links:** 17, 22

---

### LLM Trading: Analysis of LLM Agent Behavior in Experimental Asset Markets / LLM Agents Do Not Replicate Human Market Traders
- **id:** P34
- **authors:** [arXiv 2502.15800 — Hadley et al. / multi-author 2024-2025]
- **year:** 2024-2025
- **source:** arXiv:2502.15800 (multiple versions)
- **url:** https://arxiv.org/html/2502.15800v3
- **subject_population:** AI agents (Claude-3.5-Sonnet, GPT-3.5, GPT-4o, Grok-2, Mistral-Large, Gemini-1.5)
- **abstract:** Tests 6 commercial LLMs in experimental asset-market environments designed to replicate canonical human-trader bubble experiments. LLMs trade much closer to fundamental value, exhibit substantially less bubble-formation behavior, and rely more on fundamentals than heuristics. Important contrarian: do NOT replicate human behavioral biases as expected.
- **key findings:**
  - LLM markets exhibit muted bubble-formation vs. human markets.
  - LLM strategies show lower variance, reduced bias, more fundamentals-anchored.
  - Exception: overconfidence — LLMs rate their own coverage rates higher than actual.
  - Different bias profile, not absence of bias.
  - First-generation evidence on LLM-as-trader behavior in finance.
- **relevance to GTOS:** Critical recent literature. Confirms what the GTOS team has empirically observed: AI agents are not human-trader-style irrational, but they ARE specifically miscalibrated (overconfidence in coverage). HALLUC-1 / B7-v2 / A4 GTOS findings should be re-checked against this literature: the "AI hallucination" pattern is different from "human heuristic-driven bias", which validates the engineering response (precision-bug fixes) over the prompt-engineering response.
- **potential hypothesis:** GTOS's AI selectivity collapse in trending_bull (per F2 / F15) is fundamentally an LLM-overconfidence phenomenon, not a heuristic-driven bias. Predicts that K54 ML classifier (trained on outcomes, no LLM in the inference loop) will systematically out-perform the AI gate in regime-extremum cohorts where the LLM is most-overconfident.
- **cross-domain links:** 19, 20, 17

---

### Sleep Deprivation Biases the Neural Mechanisms Underlying Economic Preferences (and meta-analyses)
- **id:** P35
- **authors:** Vinod Venkatraman et al. 2011 + meta-analyses
- **year:** 2011 (foundational) + 2024-2025 reviews
- **source:** Journal of Neuroscience (foundational); MDPI 2025 scoping review
- **url:** https://www.jneurosci.org/content/31/10/3712
- **subject_population:** experimental (sleep-deprived adults, fMRI + behavioral tasks)
- **abstract:** Single-night sleep deprivation shifts decision-making strategy from defending against losses to seeking gains, with corresponding ventromedial prefrontal cortex activation increase. Meta-analytic evidence: sleep deprivation impairs decision-making, increases risky choices, with magnitude that varies by task type and deprivation duration.
- **key findings:**
  - Sleep-deprived subjects shift from loss-defense to gain-seeking.
  - vmPFC activation increases (correlate of shift).
  - Mood is more affected than cognitive/motor performance.
  - Direct evidence for state-dependence of risk-preferences.
- **relevance to GTOS:** Direct CEO-operational-discipline relevance. The autonomous system architecture allows GTOS to operate during periods (overnight, weekend) when human-supervised trading would be sleep-deprivation-biased. The kill-zone schedule + autonomous execution + monitoring-only-supervision mode is engineered precisely to operate continuously without human-state-dependence. Also relevant for CEO meta-decisions (when to ship, when to halt) — AVOID making strategic GTOS calls under sleep deprivation.
- **potential hypothesis:** Counterparty trading flow during sleep-deprived hours of the dominant trading population (e.g., Asian session for European retail, end-of-NY-session for US retail) should exhibit different disposition / loss-aversion profile. Could partially explain Tokyo session's behavior characteristics for JPY pairs.
- **cross-domain links:** 17, 11

---

### A Model of Reference-Dependent Preferences (Kőszegi-Rabin)
- **id:** P36
- **authors:** Botond Kőszegi, Matthew Rabin
- **year:** 2006
- **source:** Quarterly Journal of Economics, 121(4), 1133-1165
- **url:** https://academic.oup.com/qje/article-abstract/121/4/1133/1855210
- **subject_population:** general (theoretical model)
- **abstract:** Reference points are determined by recent (rational) expectations, not the status quo. Provides equilibrium framework where the reference point is endogenous. Captures loss aversion, first-order risk aversion, and diminishing sensitivity simultaneously.
- **key findings:**
  - Endogenous, expectations-based reference points.
  - Personal-equilibrium concept (rational expectations + reference dependence).
  - Captures loss aversion AND first-order risk aversion AND diminishing sensitivity.
  - Asset-pricing implication: equity premium is high because expectations-based loss aversion makes consumption-fluctuations more painful.
- **relevance to GTOS:** Critical for modeling drawdown psychology. As GTOS proceeds through a challenge, the CEO's reference point ISN'T static at $100k — it shifts with rational expectations (recent equity peak, projected peak, social comparisons). This explains why mid-challenge drawdowns feel disproportionately painful even if mathematically equivalent to early-challenge drawdowns. The H29 drawdown rule + Gate 0 deployment-phase locks operate against the resulting biased CEO judgment.
- **potential hypothesis:** CEO override-rate of GTOS hard rules should spike NEAR (but not AT) recent equity peaks — when expectations-based reference is at its most-elevated and any retracement triggers loss-aversion. The hard rule "no overrides without WF approval" is the operational defense.
- **cross-domain links:** 17, 21

---

### Dark Triad Personality Traits and Selective Hedging (and risk-taking literature)
- **id:** P37
- **authors:** various (Beth Kewell et al. on Dark Triad + Hedging; Joinson et al. on Dark Triad + financial risk)
- **year:** 2021-2025
- **source:** Journal of Business Ethics + Personality and Individual Differences
- **url:** https://link.springer.com/article/10.1007/s10551-021-04985-z
- **subject_population:** professional (corporate risk managers) + experimental (working adults)
- **abstract:** Narcissism + psychopathy + Machiavellianism (Dark Triad) predict propensity for financial risk-taking. Risk-managers with high Dark Triad scores engage in selective hedging more than peers. Dark Triad explains gambling-style risk-taking + investment risk-taking.
- **key findings:**
  - Narcissism explains general financial-risk propensity.
  - Psychopathy explains gambling-style risk-taking.
  - Effect concentrated in older, male, less-experienced managers.
  - Dark-Triad signals in corporate risk-management have ethical implications.
- **relevance to GTOS:** Adds dimension to "counterparty psychology": some sub-population of counterparties is structurally more risk-seeking (Dark Triad-driven). For GTOS edge stability, this sub-population's flow is reliably present in retail / less-disciplined-pro contexts. For CEO operational discipline: be aware of own Dark-Triad-flavored impulses ("I have an edge that the market doesn't know about" → narcissistic-overconfidence flag). The audit-driven cleanup pattern + mandatory CEO approval-for-trading-logic gate is implicitly a check against this.
- **potential hypothesis:** Strategy-development teams with structurally over-represented Dark-Triad characteristics (high-risk, under-discipline, dismissive-of-risk-management) systematically underperform. The empirical record of failed prop-firm participants (5-10% pass rate, with most failures from loss-limit violations) is consistent.
- **cross-domain links:** 17, 22

---

### Affect Heuristic in Judgments of Risks and Benefits (Slovic / Finucane et al.)
- **id:** P38
- **authors:** Melissa Finucane, Ali Alhakami, Paul Slovic, Stephen M. Johnson
- **year:** 2000
- **source:** Journal of Behavioral Decision Making, 13(1), 1-17
- **url:** https://www.anderson.ucla.edu/faculty/keith.chen/negot.%20papers/FinAlhSlovicJohn_AffectHeur00.pdf
- **subject_population:** experimental (general adults, risk-benefit judgment tasks)
- **abstract:** Risk-benefit judgments exhibit a robust *inverse* relationship — items judged high-benefit are also judged low-risk and vice versa, even when the underlying truth has zero or positive correlation. Time pressure strengthens the effect. Affect, not analysis, is doing the work.
- **key findings:**
  - Risk-benefit inverse relationship is heuristic-driven, not data-driven.
  - Time pressure strengthens the effect.
  - Distinct from cognitive heuristics (representativeness, availability) — affect is the input.
  - Foundational paper for "affect-as-information" view of decision-making.
- **relevance to GTOS:** Direct relevance to AI prompt design. If a setup is described with positive valence ("strong displacement", "clean OB"), the AI may underweight risk; with negative valence ("weak conviction", "marginal momentum"), overweight risk. This is implicit in the MSO's structural layout. The K54 classifier's outcome-based training fundamentally bypasses this — it ignores affect and looks only at realized R.
- **potential hypothesis:** AI gate emissions are systematically biased by the affect-loading of language used to describe market state in the MSO. A neutral-language MSO (compared to current rich-language version) should produce different CR rates. Testable in shadow mode with negligible cost.
- **cross-domain links:** 19, 17

---

## 6. Validated-numbers cross-references for synthesis

For Phase 2 synthesis: where this domain's findings update or contextualize GTOS's Validated Numbers (per CLAUDE.md):

- **XAUUSD WR 62%** (P03 + P11 + P21 + P31): the empirical claim is robust *for a population with disposition + loss-aversion + countercyclical-risk-aversion counterparties*; decay (per F11, F15) is consistent with population shift (P31 AMH framing).
- **OB zone advantage +17pp pre-2026 → +4.6pp H2-2026** (F11): consistent with P31 Adaptive Markets edge-decay; counterparty-flow saturation OR retail-share decline OR algorithmic-CTA-share rise.
- **Loss aversion = inverted TP gate justification:** P01 + P02 establish the mechanism; P29 says context-dependence is real but **trading IS asymmetric and ordered**, so λ ≈ 2 still applies operationally.
- **Disposition effect = OB-retest counterparty mechanism:** P03 + P05 + P12 + P23 + P24 are the chain of evidence.
- **CEO operational discipline:** P11 + P22 + P36 establish that even professionals exhibit countercyclical risk aversion + reference-point shifts; the gate-and-rule architecture is the engineering response.
- **AI overconfidence:** P14 + P15 + P20 + P34 establish overconfidence as the unifying bias; P34 (LLM behavioral) shows AI agents have **different** but still-present overconfidence patterns.

## 7. Hypothesis backlog (preview for Phase 3)

These will be re-examined in Phase 3 hypothesis-generation; logged here for handoff:

1. **OB-retest WR vs. retail-flow share** (from P03 + P32 + P33). Per-instrument retail-share proxy → OB-retest edge intensity. Strong prediction; data-available test.
2. **Per-instrument loss-aversion estimation** (from P29 + P02). Replace single λ ≈ 2 with per-instrument λ derived from order-flow asymmetry. Feeds K54 features.
3. **Saliency-based prompt debiasing** (from P13 + P25 + P27 + P38). A/B test prompt variants to measurably affect CR / inverted-TP / L2 rates. Zero-cost intervention.
4. **AI competence-driven framework over-emission** (from P28). Explicit prompt language asserting framework-equivalence will only partially correct the ob_retest skew. Tests post-ADR-006 distribution.
5. **Streak-conditioned OB-retest WR** (from P30). Hot-hand fallacy reversal implies streaks may be real; conditional WR ≠ unconditional WR.
6. **Drawdown reference-shift effect** (from P36). CEO override-rate spikes near recent equity peaks; H29 + Gate 0 are the operational defense.
7. **Sleep-deprivation in counterparty population** (from P35). Per-session WR variation could reflect counterparty population sleep-state.
8. **K54 / K55 (regime-aware ML classifier vs AI shadow harness)** is the cleanest empirical test of the LLM-overconfidence-vs-outcome-data tradeoff (P34 + P14 + P20).
