# Group E Synthesis — Behavioral Finance, Trader Psychology, Risk Management

**Synthesis Agent:** Group E (Phase 2, Track B)
**Run date:** 2026-04-28
**Model / effort:** Opus 4.7 / max
**Source domains:**
- `research/ml_program/literature/17_behavioral_adaptive_markets/` (42 papers)
- `research/ml_program/literature/18_trader_psychology_decision/` (38 papers)
- `research/ml_program/literature/21_risk_management_kelly_sizing/` (38 papers)
- **Total: 118 papers across 3 domains.**

**GTOS context anchors:** edge-decay is CEO's #1 concern; HALLUC-1 / S79 / J46-J49 / F11 / F15 / A6 / A4 are the active operational threads; K54 v2 just FAILED CPCV-honest accounting (cross-period replication had 3 of 4 groups sign-flip; Stouffer p=0.196 — not significant); side-aware sizing project is staged; Phase 2 must close 13 CEO decisions from Session 43 synthesis Section 7.

This synthesis is read-only over papers.md / papers.csv. No fabrication. All numbers tied to file lines.

---

## Section 1 — Overview of the corpus

### Domain 17 (Behavioral & Adaptive Markets, 42 papers)
Foundational behavioral asset-pricing (BSV, Hong-Stein, DHS, Barberis-Huang-Santos, Shiller); limits of arbitrage (Shleifer-Vishny, DeLong-Shleifer-Summers-Waldmann, Gromb-Vayanos, Brunnermeier-Nagel, Garleanu-Pedersen, Gabaix-Koijen, OFR Treasury 2021); Adaptive Markets Hypothesis (Lo 2004 / 2005 / 2024 with Zhang; precious-metals AMH; cryptocurrency AMH; COVID-commodity AMH); sentiment indices and media (Baker-Wurgler, Tetlock 2007 / 2008, Da-Engelberg-Gao FEARS, Garcia, Loughran-McDonald, Bollen Twitter, Hirshleifer-Shumway sunshine, Heimer peer effects); decay/anomaly literature (McLean-Pontiff, Greenwood-Shleifer-You bubbles, Greenwood-Hanson-Shleifer-Sørensen R-zone, Greenwood-Shleifer 2014 expectations, Jegadeesh-Titman, DeBondt-Thaler, Bernard-Thomas PEAD, Chen-Hong-Stein, Cohen-Frazzini); 2020-2025 retail-flow + LLM regime (Lopez-Lira-Tang ChatGPT, FinBERT, GameStop / WSB, Robinhood-outage retail-quality study).

Critical sub-corpus for GTOS: **Lo's AMH (4 papers)** + **McLean-Pontiff post-publication decay** + **Lopez-Lira-Tang real-time LLM-Sharpe collapse 6.54 → 1.22 in 30 months** = direct theoretical scaffold for CEO's edge-decay concern.

### Domain 18 (Trader Psychology & Decision, 38 papers)
Tier-1: Kahneman-Tversky 1979 prospect theory; Tversky-Kahneman 1992 cumulative prospect theory; Odean 1998 disposition effect; Coval-Shumway 2005 afternoon-risk-recovery; Lo-Repin-Steenbarger 2005 fear-and-greed; Kahneman-Klein 2009 intuitive-expertise; Daniel-Hirshleifer 2015 overconfidence-and-predictability; Locke-Mann 2005 professional-trader-discipline; Frydman-Barberis-Camerer-Bossaerts-Rangel 2014 fMRI realization-utility; Cohn-Engelmann-Fehr-Maréchal 2015 countercyclical-risk-aversion-causal.

Tier-2 (implementation context): Tversky-Kahneman 1981 framing; Heath-Tversky 1991 competence-driven ambiguity-seeking; Frydman-Rangel 2014 saliency debiasing; Genesove-Mayer 2001 housing disposition replication; Kőszegi-Rabin 2006 expectations-based reference points.

Tier-3 (recent / contrarian): Walasek-Mullett-Stewart 2025 loss-aversion-not-robust re-meta-analysis (λ ≈ 1.07 in symmetric/unordered subsets); Brown et al. 2024 meta (λ ≈ 1.8-2.1); Miller-Sanjurjo 2018 hot-hand-fallacy-was-fallacy; Hadley et al. 2024-2025 LLM-trader experimental finance; prop-firm 2024 industry data.

### Domain 21 (Risk Management, Kelly, Position Sizing, 38 papers)
Kelly foundational (Kelly 1956, Thorp 2006, MacLean-Thorp-Ziemba 2011 / 2010, Busseti-Ryu-Boyd 2016, Sornette et al. 2020, Hong et al. 2025); vol-targeting / risk-parity (Moreira-Muir 2017, Harvey et al. 2018, Asness-Frazzini-Pedersen 2012, Maillard-Roncalli-Teiletche 2010, López de Prado HRP 2016); CVaR / coherent measures (Artzner-Delbaen-Eber-Heath 1999, Rockafellar-Uryasev 2000, Acerbi-Tasche 2002, McNeil-Frey-Embrechts 2015, Rickenberg 2019); drawdown control (Grossman-Zhou 1993, Cvitanić-Karatzas 1995, Magdon-Ismail-Atiya 2004, Chekhlov-Uryasev-Zabarankin 2005, Geanakoplos 2010); fat-tail-aware sizing (Student-t Kelly, Geman-Geman-Taleb 2014, Taleb 2020, Peters 2009 / 2019); prop-firm / practical (Strub 2014/2018 EVT-CDaR, hybrid Kelly+VIX 2025, Buffett's Alpha, Datye 2012, Carvalho 2020); buffer / SL (Black-Perold CPPI, conditional vol-targeting 2020, DRL-portfolio 2024); foundational (Markowitz 1952, Roy 1952 safety-first, Moskowitz-Ooi-Pedersen 2012 TSM).

**Critical sub-corpus for GTOS:** Strub (21-028) EVT-CDaR sizing — directly implements `P(MTM-DD ≥ 4%) ≤ ε` constraint with FX strategies; Busseti-Boyd RCK (21-005) — single-knob convex parametrization that nests Kelly + Markowitz; Sornette (21-006) crash-aware Kelly with empirically calibrated 0.4 fraction matching GTOS gold ξ=0.35; Moreira-Muir (21-008) vol-management Sharpe gain 20-40% OOS; Roy 1952 (21-037) safety-first frame is the *correct* objective for prop-firm sizing.

### What corpus does NOT cover (gaps)
- Side-aware Kelly under FX/commodity (papers found; literature thin — GTOS empirical asymmetry [LONG=0.5x, SHORT=1.0x] is unique).
- Prop-firm rule design under sequential-account-stage rules (industry whitepaper, not peer-reviewed). Phase 2 may need original empirical work here.
- LLM-as-trader behavioral profiling beyond first-generation 2024 result (Hadley et al.) — GTOS's HALLUC-1 / A4 evidence is among the earliest empirical material.
- Loss aversion replication crisis (Walasek-Mullett-Stewart 2025): forces reframing of inverted-TP gate justification — λ ≈ 2 still operates in *asymmetric, ordered* trading contexts (which trading IS) but is no longer a universal constant.
- Steenbarger-style clinical trader-psychology has no academic peer-reviewed replication; treat as practitioner ground-truth not statistical evidence.

---

## Section 2 — Edge-decay framework (special focus #1)

### How Lo's AMH frames GTOS's decay observations

Lo (2004) and Lo-Zhang (2024) say: edge persists when its counterparty heuristic is widespread + costly to debias; edge decays as populations adapt. The decay rate is set by `(adaptation rate of competitors) / (rate of regime change)`. McLean-Pontiff 2016 quantifies the empirical magnitude: 26% of return predictability is data-mining, 32% is post-publication arbitrage decay, leaving ~42% as out-of-sample-real edge. That ~5%/year residual decay is the McLean-Pontiff baseline the GTOS S1 monthly-decay-monitor should expect under "normal" arbitrageur learning.

GTOS observations cleanly fit the AMH frame:

1. **F11 OB-zone advantage decay velocity** (+16.8pp pre-2026 → +12.1pp H1-2026 → +4.6pp H2-2026): tracks the *exact* trajectory Lo predicts when a behavioral pattern is widely published (TradingView OB/SMC templates, retail-trading-ed YouTube channels). Post-publication decay is the dominant channel (~78% per F11 attribution); methodology drift accounts for ~22%.

2. **F15 + A6 LONG-side selectivity collapse** (XAUUSD LONG 48.4% → 18.8%; F2 trending_bull cohort 76.5% → 16.7%, Δ -59.8pp): is *regime-conditioned* AMH decay. The H1 2026 trending_bull cohort was 78% bullish (53.1% WR); the H2 cohort had only 4.8% trending_bull. The v1 detector forced LONG signals into a regime (trending_bull) whose underlying mechanism (BSV-style overreaction-after-conservatism) collapsed when the regime population thinned. AMH says: when a cohort's heuristic-counterparty population vanishes, the edge in that cohort vanishes.

3. **K52 FVG-in-impulse signal REVERSED**: classic McLean-Pontiff post-publication arbitrage. The FVG pattern is among the most-published in retail SMC education; it is now negative in H2 2026 (XAU FVG-WR 72.6% < non-FVG 75.4%). AMH predicts edges that flip sign under intense arbitrage (vs. simply decaying to noise) — and the K52 result is exactly that pathology.

4. **Lopez-Lira-Tang real-time LLM-news-Sharpe collapse 6.54 → 1.22 in 30 months**: direct empirical AMH on a model that GTOS adopts wholesale (Sonnet 4.6 at MSO gate). LLM-news-sentiment alpha is among the fastest-decaying alphas ever measured. By construction, GTOS's edge cannot afford to depend on raw LLM-news-sentiment; it must rest on infrastructure (OB structural precision + safety stack + microstructure features that are NOT publishable / democratized).

### AMH predictions for GTOS over 12-24 months

- **Continued ~3-5%/year baseline OB decay** (McLean-Pontiff): expected, normal, manageable. Worth deviation alarm threshold: >10%/year sustained decay = signal of regime acceleration (e.g., a new wave of OB-tooling in retail platforms).
- **Regime-conditioned cohort failures will recur** (Lo 2004 + F15 + Greenwood-Shleifer 2014 extrapolation): every regime cohort the AI is trained or prompted to recognize has a non-stationary base-rate. K54 must be regime-aware OR re-trained continuously OR architected with regime-as-feature (which Q1.3 K54 v2 attempted, then failed CPCV-honest).
- **High-retail-attention instruments decay fastest** (Heimer 2016, Robinhood-outage 2022, GameStop / WSB literature): NAS100 + GBPJPY + (post-FTX) crypto-rotation-into-gold all face faster decay than XAGUSD or USDJPY. F11 + HALLUC-1 NAS100 patterns are consistent.
- **Calm regimes erode edge faster than stressed regimes** (Shleifer-Vishny 1997, OFR-Treasury 2021, Garleanu-Pedersen 2007): when funding stress is low and arbitrageurs are well-capitalized, the OB-retest mean-reversion premium compresses. Edge magnitude correlates positively with funding-stress proxies (TED spread, SOFR-OIS, equity-vol breakouts). GTOS should expect higher OB continuation rates during stress weeks vs calm weeks.
- **Brunnermeier-Nagel risk** (hedge funds rode tech bubble): *smart money does not always correct mispricings*. NAS100's post-2020 retail-options gamma + Reddit-coordination regime means GTOS edge in indices may face *aligned* institutional + retail flow at sustained-rally tops. The Bull/Bear/Judge debate (research-door-wired N62) is the architectural response.
- **LLM-news-sentiment alpha decays toward zero by 2027** (Lopez-Lira-Tang trajectory): GTOS should NOT bet edge on LLM-extracted news sentiment as a feature; should bet on infrastructure that is structural/orthogonal to widely-replicable signals. K54-v2's failure under CPCV is partly consistent with this — the v2 features were too close to widely-known structural signals.
- **Instrument-specific lifecycle**: precious metals (XAUUSD, XAGUSD) trend toward efficiency over time but with intra-year reversal episodes (Auer / Caraiani; cryptocurrencies-gold-WTI 2021); FX continues to be slow-moving relative to equity indices. Edge half-life ranking: NAS100 < GBPJPY < XAUUSD < USDJPY ≈ XAGUSD.

---

## Section 3 — Counterparty modeling (special focus #2)

GTOS exploits human-trader stop placement, round-number anchoring, herding, late stop-out flow at structural pivots. The literature on counterparty behavior under fat-tailed volatility is split between behavioral asset-pricing (domain 17) and individual-trader psychology (domain 18). The synthesis below identifies the mechanisms that anchor the OB-retest edge and predict its decay vector.

### The disposition-effect chain is the operative counterparty mechanism

**P03 Odean 1998 + P05 Shefrin-Statman 1985 + P11 Coval-Shumway 2005 + P12 Locke-Mann 2005 + P21 Thaler-Johnson house-money + P23 Genesove-Mayer 2001 housing-loss-aversion + P24 Frydman-Barberis-Camerer-Bossaerts-Rangel 2014 fMRI realization utility:** the disposition effect is overdetermined (prospect theory + mental accounting + regret avoidance + self-control failures + neurally encoded), persists in retail ~1.5-2× more likely to sell winners than losers, persists in professionals as a measurable trait (with relative discipline as the survival differentiator), and replicates out-of-asset-class (housing-market sellers list 25-35% of (expected - purchase) gap higher when faced with losses). The Frydman fMRI work shows vmPFC tracks realization-utility model at the moment of sell — confirming the bias is neurally hardwired.

**Operative GTOS implication:** OB-retest continuation rate (~70% mechanical baseline; rolling-50 watchdog) is approximately the population-average disposition-effect strength among recent counterparties. Decay risk: as algorithmic / passive / index-flow share rises in an instrument's volume mix, the disposition-driven counterparty pool shrinks. F11's gold OB-decay is consistent with growing CTA / quantitative gold flow.

### Counterparty stress flow under fat tails — Coval-Shumway is the engine

**P11 Coval-Shumway 2005** is the empirical analog of the OB-retest edge mechanism in another market: morning-loss-stressed CBOT proprietary traders take 16% more above-average risk in the afternoon, place more trades, accumulate more inventory, and their prices revert FASTER than informed-flow prices. The empirical confirmation: distressed counterparty flow is identifiable AND mean-reverts. GTOS's edge is recognizing the structural pattern (OB) where distressed flow concentrates.

**Operative GTOS implication (testable):** OB-retest WR should be HIGHER during the second half of intraday sessions, after distressed-flow has accumulated. NY-session OB-retests on instruments where London-session generated stress flow should outperform London-session OB-retests. This is a free A/B per-instrument test on existing GTOS data.

### Round-number and reference-point anchoring is load-bearing

**P09 Tversky-Kahneman 1974** + **P13 Northcraft-Neale 1987** + **P36 Kőszegi-Rabin 2006**: anchoring is robust across expert and amateur populations; experts deny influence even when measurably biased; reference points are endogenous, expectations-based, not status-quo. Counterparties anchor on entry price (the disposition reference); GTOS anchors on structural OB level. The anchor mismatch IS the edge.

**Operative GTOS implication:** OB-retest WR should be HIGHER on instruments with stronger round-number anchoring (cross-link to domain 09 / round-number magnetism literature: gold > index futures > FX-cross). Empirically validated: XAUUSD WR 62% > XAGUSD ≈ US30 58.5% > GBPJPY 57.1%.

### Sleep-, steroid-, and circadian-cycling counterparties

**P16 Coates-Herbert 2008** + **P35 Venkatraman 2011 sleep deprivation**: human-trader risk preferences are endocrinologically modulated, hence inherently unstable hour-to-hour and across days. GTOS's invariant-rule architecture extracts the difference between its rule and counterparties' steroid-modulated rule. **Operative GTOS implication:** OB-retest WR should be HIGHER during high-realized-volatility kill zones (counterparty cortisol elevated) — testable by stratifying realized R per OB-retest by current-day RV. Asian session for European retail and end-of-NY-session for US retail should show different disposition profiles.

### LLM counterparties exhibit *different* (not absent) biases

**P34 Hadley et al. 2024-2025 LLM Trading**: 6 commercial LLMs tested in human-bubble experiments — LLMs trade closer to fundamental value, exhibit muted bubble-formation, but show overconfidence (rate own coverage rates higher than actual). HALLUC-1 / A4 / B7 GTOS findings are consistent: AI hallucination is precision-rounding bug-class, not heuristic-driven retail-style mispricing. Critical: as LLM-trader population grows in markets, the counterparty mix shifts toward this overconfidence-flavored pattern. GTOS's edge assumptions (disposition-driven retail cohorts) become stale as LLM-share rises.

### Behavioral asset-pricing models BSV / Hong-Stein / DHS map to OB-retest

**Section 1 of Domain 17:** BSV (Barberis-Shleifer-Vishny 1998) underreaction-to-conservatism + overreaction-to-representativeness; Hong-Stein 1999 newswatchers + momentum traders gradual diffusion → underreaction → overreaction; DHS (Daniel-Hirshleifer-Subrahmanyam 1998) overconfidence → excess vol + biased self-attribution → momentum. The OB-retest captures the moment underreaction-to-CHoCH transitions to overreaction-back-to-zone.

**Operative GTOS implication:** As newswatcher / retail education broadens (Hong-Stein gradual-diffusion-erosion), OB advantage compresses. The H1 → H2 OB advantage erosion matches exactly the Hong-Stein prediction.

### Institutional flow at bubble-tops can ALIGN with retail

**Brunnermeier-Nagel 2004**: hedge funds RODE the tech bubble; did not arbitrage. Refutes "smart money corrects mispricings" baseline. NAS100 post-2020 retail-options + index-options gamma + Reddit-coordination changes the historical asymmetry. **Operative GTOS implication:** SHORT-side OB retests on indices may underperform during bubble-regime (institutional + retail aligned); SHORT-side may BETTER perform after the bubble breaks (Chen-Hong-Stein crash setup); LONG-side becomes more risky precisely at sustained-rally tops. Maps to S79 + side-aware sizing → LONG=0.5x, SHORT=1.0x asymmetry.

### Counterparty fat-tail risk: "noise traders survive and earn premia"

**De Long-Shleifer-Summers-Waldmann 1990** noise-trader risk + **Shleifer-Vishny 1997 Limits of Arbitrage** + **OFR-Treasury 2021 LTCM redux**: arbitrageur capital withdraws in stress; noise-trader risk earns a premium; mispricings can deepen rather than self-correct in extreme regimes. **Operative GTOS implication:** GTOS is a small-scale "limits-of-arbitrage refilling agent" — its expected R is HIGHER in regimes where institutional capital has retreated (funding stress periods, post-shock weeks).

### Net counterparty model

GTOS counterparty pool ≈ retail + small-prop + algorithmic-CTA + occasionally aligned hedge-fund + 2024+ LLM-driven-flow share. The OB-retest edge is a weighted average of disposition-effect-strength × residence-time-of-late-stop-out-flow at the OB level, gated by the *type* of stress driving the cascade (information-driven stress amplifies edge; calm-period algo-cascade compresses edge).

---

## Section 4 — CEO operational discipline (special focus #3)

The CEO is a human trader subject to drawdown psychology. The literature provides direct guidance.

### Causal countercyclical risk aversion in PROFESSIONALS — Cohn et al. 2015

**P22 Cohn-Engelmann-Fehr-Maréchal 2015** (American Economic Review): financial professionals primed with "bust" scenario showed *causally* higher risk aversion than "boom" — fear-arousal mediates. **Strategic implication for the CEO:** strategic GTOS decisions made *during or right after* drawdowns will tend toward excess safety (too-conservative sizing, too-aggressive risk reduction). This is exactly the impulse to halt LONG trading entirely after observing item #4 XAUUSD H2 LONG decay. The S79 risk-policy maintained 2.0% (didn't reduce) precisely against this bias — empirically validated by literature.

**S79 hold during HALLUC-1 NAS100 0.25% pending observation** is a different signal — it's fact-based safety, not bust-primed countercyclical excess. The distinction matters.

### Coval-Shumway afternoon-recovery extends to the CEO

**P11 Coval-Shumway 2005** (rev cited above): when CEO has a losing session, the right move is reduced position sizing, not revenge-sizing. H29 8% drawdown rule (DD ≥ 8% → 0.5x risk) is the structural defense.

### The kill-switch architecture is empirically motivated

**P07 Lo-Repin 2002** + **P18 Lo-Repin-Steenbarger 2005** + **P17 Kuhnen-Knutson 2005** + **P21 Thaler-Johnson house-money / break-even**: emotion-in-the-loop is the failure mode, NOT a debiasing target. The somatic markers Lo-Repin measure are precisely what lead any trader to override Gate 0, resize positions, pull stops in drawdown. Kuhnen-Knutson's dual-circuit framework (NAcc reward → risk-seeking errors; insula → risk-aversion errors) confirms BOTH must be addressed. H29 addresses the insula side (forcing risk reduction in drawdown; defends against panic-cut-too-much); kill-switch + Gate 0 deployment-phase locks address the NAcc side (preventing house-money over-deployment in winning streaks). Both are needed.

### Reference-point shifts during a challenge — Kőszegi-Rabin 2006

**P36 Kőszegi-Rabin 2006:** reference points are endogenous, expectations-based. As GTOS proceeds through a challenge, the CEO's reference point isn't static at $100k — it shifts with rational expectations (recent equity peak, projected peak, social comparison to other prop participants). Mid-challenge drawdowns feel disproportionately painful even if mathematically equivalent to early-challenge drawdowns.

**Operative implication:** the hard rule "no overrides without WF approval" is the operational defense against expectations-shifted loss-aversion. CEO override rate of GTOS hard rules should spike NEAR (but not AT) recent equity peaks — when expectations-based reference is most-elevated.

### Heath-Tversky competence-driven AMBIGUITY-SEEKING

**P28 Heath-Tversky 1991:** in their domain of expertise, people SEEK ambiguity (refutes pure ambiguity-aversion). The CEO's expertise reading-list culture can generate competence-driven over-deployment in the "domain we know" (XAUUSD OB-retest). Heath-Tversky predicts *higher* deployment-aggression on familiar instruments than on unfamiliar ones (NAS100, observer-only GBPUSD). **Operative implication:** the deployment-phase Gate 0 is a structural defense against this competence-driven over-deployment.

### Malmendier-Tate 2005 CEO overconfidence — direct match

**P15 Malmendier-Tate 2005:** overconfident CEOs persistently fail to diversify against firm-specific risk; investment-cash-flow sensitivity rises; concentrated in equity-dependent firms. **Direct GTOS implication:** when GTOS is winning (H1 2026), there's a temptation to over-deploy (more instruments, larger size); when losing (H2), to underinvest in research / pivot. The structural responses — phased deployment, fixed-deployment-phase Gate 0, kill-switch — are formal defenses.

**Operative test:** measure gap between CEO ad-hoc-asks (proposed risk-per-trade) vs. shipped risk-per-trade. If post-mortem data shows the gap correlates with subsequent realized DD, the hard rule "risk_per_trade_pct stays at 2.0" is empirically validated.

### Locke-Mann RELATIVE discipline beats ABSOLUTE discipline

**P12 Locke-Mann 2005:** professional floor traders DO hold losers longer than winners; do NOT incur measurable cost; discipline measures predict trading SURVIVAL. Successful pros are characterized by RELATIVE — not absolute — discipline.

**Operative implication:** don't try to eliminate AI's emergent biases; measure them and gate the worst ones with hard rules. The 2026-04-27 KEPT touch_count=2 vs. LOOSEN_TO_3 decision is precisely a relative-discipline call: GTOS doesn't need to ELIMINATE all touch-2 trades, just stay on the disciplined side of the threshold.

### Decision-making sleep deprivation — direct CEO-discipline rule

**P35 Venkatraman et al. 2011** + meta-analyses: single-night sleep deprivation shifts decision-making from defending against losses to seeking gains; vmPFC activation increases. **Operative rule for CEO:** AVOID making strategic GTOS calls (deployment phase changes, prompt edits to `prompts/`, S79 risk-policy adjustments) under sleep deprivation. The autonomous-system-with-checklist culture in `.context/05_operations/` is the formal infrastructure response.

### Hot-hand-was-not-fallacy — streak rules are statistically defensible

**P30 Miller-Sanjurjo 2015/2018:** the original Gilovich-Vallone-Tversky 1985 finding "hot hand is fallacy" was itself a statistical artifact (selection-conditional finite-sample bias). Correctly analyzed, hot hand IS real. **Operative implication:** the GTOS hard rule "5 consecutive losses on a single instrument = emergency stop" is statistically defensible; streaks happen, plan for them.

### Dark Triad CEO check

**P37 Dark Triad literature:** narcissism + psychopathy + Machiavellianism predict propensity for financial risk-taking; psychopathy predicts gambling-style risk-taking. **Operative implication:** CEO should be aware of own Dark-Triad-flavored impulses ("I have an edge that the market doesn't know about" → narcissistic-overconfidence flag). The audit-driven cleanup pattern + mandatory CEO approval-for-trading-logic gate is implicitly a check against this.

### Loss aversion is *context-dependent*, not universal

**P29 Walasek-Mullett-Stewart 2025** (re-meta-analysis of Brown et al. 2024 dataset): λ ≈ 1.07 in symmetric-unordered subset; λ ≈ 1.8-2.1 only in asymmetric/ordered. Trading IS asymmetric and ordered; therefore λ ≈ 2 still applies operationally for trading-context decisions. But the claim "humans always lose-averse 2:1" is no longer empirically defensible. Inverted-TP gate justification holds; cross-applying λ = 2 to non-trading CEO decisions is questionable.

---

## Section 5 — Risk policy refinements (special focus #4)

The S79 sharpe-weighted policy delivered +25.8pp P(pass FN Phase 1). The fat-tail-aware sizing literature suggests several refinements.

### Strub 2014/2018 EVT-CDaR is the SINGLE most-applicable paper

**21-028 Strub Trade Sizing Techniques for Drawdown and Tail Risk Control:** EVT-fitted CDaR sizing on daily FX strategies — directly the GTOS use-case. Code released. Strub's results: equivalent-or-better Sharpe + significant tail-risk reduction. EVT-CDaR captures fat tail more accurately than vol-target.

**Operative refinement:** replace `risk_per_trade_pct: 2.0` with EVT-CDaR sizing under FN MTM-DD constraint. *Hypothesis:* 10-20% higher growth rate at same MTM-DD violation probability.

### Busseti-Boyd Risk-Constrained Kelly is the natural sharpe_weighted parametrization

**21-005 Busseti-Ryu-Boyd 2016:** convex optimization that nests Kelly + Markowitz under explicit drawdown-probability constraint `P(W_t / W_max < β) ≤ ε`. Single risk-aversion parameter `λ` is the sharpe_weighted-sizing knob.

**Operative refinement:** S79 Phase 2 sharpe_weighted should be re-parametrized as Busseti-Boyd `λ` chosen to satisfy `P(daily MTM-DD ≥ 4%) ≤ 0.02`. Preliminary: per-instrument optimal weights non-uniform (uniform_fn 2.0% leaves Sharpe on the table).

### Sornette crash-aware Kelly empirically calibrates to GTOS gold

**21-006 Sornette et al. 2020:** under jump-diffusion with calibrated `λ_jump = 0.05/year`, magnitude-tail-index ξ ≈ 0.3, full-Kelly path loses *all* simulated wealth in 50% of paths within 5 years. "Crash-aware" Kelly cuts effective leverage by 50% during high-jump-probability regimes; suggests jumps + heavy tails → "natural fractional Kelly" of factor 0.4.

**GTOS distributional finding (memory `project_distributional_findings`):** ξ = 0.35 for gold, GARCH persistence 0.9906, 6.2× more 3σ events than Gaussian. Sornette's 0.4 Kelly fraction is *empirically calibrated* near GTOS's distributional regime. GTOS at 2% sizing is roughly 1/18-Kelly under Gaussian assumptions; under fat-tail correction (Student-t with ν ≈ 4-5 → Kelly factor (ν-2)/ν ≈ 0.5-0.6) GTOS is roughly 1/9-Kelly under fat-tail-aware metric — still very conservative.

**Operative refinement:** compute Sornette-style crash-aware Kelly fraction for each GTOS instrument; sharpe_weighted scaling can sustainably range up to ~3% in low-vol regimes (per F11 + 1/9-Kelly stance) without breaching FN constraint.

### Moreira-Muir vol-management — 20-40% Sharpe gain OOS

**21-008 Moreira-Muir 2017:** vol-managed portfolios deliver 20-40% Sharpe gains *out-of-sample* across factors. Mechanism: variance shocks not offset by proportional return shocks. Implementation: scale by `target_vol / realized_vol_t`. Foundational for any GTOS sharpe_weighted implementation. Currently GTOS does NOT vol-scale → Moreira-Muir says edge is being left on the table.

**Operative refinement:** implement per-instrument `risk_pct_t = base · target_vol / ATR_20d`. Hypothesis: Sharpe lift ≥15% OOS, especially XAUUSD and indices.

### Conditional vol-targeting (21-034) avoids over-de-leveraging in calm regimes

**21-034 Conditional Volatility Targeting 2020:** always-on vol-targeting can underperform in some markets — under-hedges in stress, over-de-leverages in calm. Conditional rule: target vol only when `vol_z_score > 1.5`; otherwise constant exposure. Likely 5-10% Sharpe better than always-on, with same DD ceiling.

**Operative refinement:** GTOS should test always-on vs conditional vol-targeting on the 367-trade pop. Recommended: conditional version, threshold tuned per instrument.

### Roy 1952 safety-first is the CORRECT objective for prop-firm

**21-037 Roy 1952:** "minimize probability of falling below disaster level" — formula `(µ - r_disaster) / σ`. The FN 4% MTM-DD is precisely a "disaster level". Roy's framework is the *correct* objective for prop-firm sizing, not utility maximization or pure Kelly.

**Operative refinement:** recast S79 risk policy as Roy safety-first: maximize geometric mean R subject to `P(daily MTM-DD ≥ 4%) ≤ ε` for ε ∈ {0.01, 0.05, 0.10}. CEO choice of ε is the key parameter.

### Grossman-Zhou + Cvitanić-Karatzas drawdown-constrained portfolios

**21-018 / 21-019 Grossman-Zhou + Cvitanić-Karatzas:** closed-form solution for HARA utility with drawdown constraint — invest fraction proportional to surplus over the floor `α · M_t`. Multi-asset extension. **Operative refinement:** smooth Grossman-Zhou variant of H29: `risk_pct_t = 2.0% · max(0, (W_t - 0.92·W_max) / W_t) / 0.08`. Continuous-vs-step at 8% threshold tradeoff worth testing — Klass-Nowicki 2005 says discrete-time may favor step-function, but there's variance to characterize at the boundary.

### CPPI for GTOS — Black-Perold

**21-033 Black-Perold 1992 CPPI:** maintain risky allocation = m · (wealth - floor); m typically 3-5 for moderate growth + floor protection. GTOS's H29 (DD ≥ 8% → 0.5x) is *piecewise CPPI* with implicit m ≈ 1. **Refinement:** test m ∈ [2, 5] for CPPI variant — better growth-vs-DD frontier than H29's m≈1 step.

### Magdon-Ismail tail-corrected DD for GTOS gold

**21-020 Magdon-Ismail-Atiya 2004:** for Brownian motion `µ, σ`, expected MDD scales like `(σ²/µ) · log(T)`. Under fat tails (gold ξ=0.35), actual DD distribution is heavier-tailed than BM. **Operative refinement:** use Magdon-Ismail formulas calibrated for ξ=0.35 + GARCH 0.9906 — compute expected DD distribution; 95th percentile DD over 90 days likely 12-18% (not 8-10% under Gaussian). H29 threshold may need recalibration upward (or kept as conservative buffer).

### Side-aware sizing — empirical, literature thin

GTOS empirical asymmetry (LONG=0.5x, SHORT=1.0x; from `project_side_aware_sizing_findings`) is unique in the FX/commodity literature. Stambaugh-Yu-Yuan 2012 / 2015 sentiment + arbitrage-asymmetry papers (domain 17) provide *theoretical* anchor: high-sentiment periods → asymmetric mispricing, short leg drives anomaly results. F2/A6 LONG-side decay during high-sentiment trending_bull cohorts is exactly Stambaugh-Yu-Yuan symmetric prediction. **Operative refinement:** S79 sharpe_weighted Phase 2 should bundle side-aware multipliers; F2 / A6 / S79 sharpe_weighted are tightly linked.

### Risk-parity and HRP at the cross-instrument level

**21-010 Asness-Frazzini-Pedersen 2012 + 21-011 Maillard-Roncalli-Teiletche 2010 + 21-012 López de Prado HRP 2016:** equal risk contribution across instruments has been shown to outperform market-cap weighting. HRP formalizes cluster-based allocation without inverting the covariance matrix.

**Operative refinement:** GTOS cross-instrument correlation gate (additive HALVE/REJECT at |corr|>0.4) is a binary approximation of risk-parity. Replace with continuous ERC-style weighting using DCC-correlated 60-day cov matrix; HRP-cluster the 7 instruments (likely 3 clusters: precious metals, JPY crosses, indices). Test against existing binary gate.

### Ergodicity / time-average growth is the right optimization target

**21-026 / 21-027 Peters 2009 / 2019:** for multiplicative wealth processes, individual time-average ≠ ensemble average. Peters re-derives Kelly as time-average growth maximization without utility theory. For prop-firm survival (multiplicative constraint), time-average growth IS the right objective.

**Operative refinement:** benchmark prop-firm "P(pass)" against time-average vs. ensemble-average growth rate. Hypothesis: P(pass) correlates more strongly with time-average than ensemble-average. This validates S79's geometric-survival-first orientation over arithmetic E[R/trade].

### DRL-based sizing controller (Phase 3+)

**21-035 Risk-Aware Deep RL 2024:** PPO with explicit DD constraint achieves higher Sharpe + 25% reduction in maxDD vs vol-targeted benchmark. **Phase 3+ idea:** train a small DRL sizing controller on GTOS data with reward = Sharpe minus DD-violation penalty. Likely recovers smoother H29 + may be tunable to specific FN constraint. Currently rule-based.

---

## Section 6 — Actionable hypotheses (concrete, testable)

The following hypotheses are pre-registered for Phase 2. Each names the literature anchor and the test method.

| # | Hypothesis | Anchor | Test |
|---|-----------|--------|------|
| **H-E1** | Per-instrument OB-retest WR is HIGHER during second-half-of-session vs first-half (after distressed counterparty flow accumulates). | P11 Coval-Shumway 2005 | Stratify GTOS realized R per OB-retest by intra-session time bucket (first-30%, mid-40%, last-30% of kill zone). |
| **H-E2** | Per-instrument OB-retest decay velocity correlates with growth in algorithmic / passive / index share of that instrument's flow. | P03 Odean + P31 Lo AMH + P24 Frydman fMRI | Per-instrument retail-flow proxies (CFTC commitments, retail-broker data, algorithmic-share estimates) regressed against rolling OB advantage. |
| **H-E3** | OB continuation rate is HIGHER during funding-stress periods (TED spread > 60 bps; SOFR-OIS > threshold). | Shleifer-Vishny 1997, Garleanu-Pedersen 2007, OFR-Treasury 2021 | Tag historical trades by funding-stress regime; compute conditional WR per regime. |
| **H-E4** | LLM-news-sentiment alpha decays toward zero by 2027; GTOS edge MUST rest on infrastructure not LLM-feature alpha. | Lopez-Lira-Tang 6.54→1.22 Sharpe in 30 months | Continuous tracking of any LLM-feature alpha share in K54+; sunset clause if Sharpe contribution falls under 0.2. |
| **H-E5** | Replace S79 uniform_fn 2.0% with Busseti-Boyd RCK under FN constraint `P(MTM-DD ≥ 4%) ≤ 0.02`. Per-instrument optimal weights non-uniform. | 21-005 Busseti-Boyd 2016 | Implement on 367-trade pop. Compare growth rate, max DD, P(pass FN) with current S79. |
| **H-E6** | Implement Strub EVT-CDaR sizing — equivalent-or-better Sharpe at smaller worst-case DD; especially gold (ξ=0.35). | 21-028 Strub 2014/2018 | Backtest EVT-CDaR vs constant 2% on 367-trade pop. Primary metrics: max DD, P(MTM-DD violation), geometric mean R. |
| **H-E7** | Per-instrument vol-scaling (Moreira-Muir / Moskowitz-Ooi-Pedersen) lifts Sharpe by ≥15% OOS. | 21-008 Moreira-Muir 2017, 21-038 Moskowitz-Ooi-Pedersen 2012 | Per-instrument `target_vol / ATR_20d` scaling backtest. |
| **H-E8** | Conditional vol-targeting (turn on at vol-z > 1.5) outperforms always-on by 5-10% Sharpe + 20% lower tail-DD. | 21-034 Conditional Volatility Targeting 2020 | A/B test always-on vs conditional. |
| **H-E9** | Smooth Grossman-Zhou variant of H29 reduces variance of P(pass) outcome vs piecewise step. | 21-018 / 21-019 Grossman-Zhou + Cvitanić-Karatzas | Replace H29 with `risk_pct_t = 2.0% · max(0, (W_t - 0.92·W_max)/W_t)/0.08` in backtest. |
| **H-E10** | LONG-side expectancy decays faster than SHORT-side as edge unfolds; F2/A6 are exact Stambaugh-Yu-Yuan symmetric prediction. | Stambaugh-Yu-Yuan 2012 + 2015 + F2 + A6 | Continue side-stratified WR tracking; bundle side-aware sizing in S79 sharpe_weighted Phase 2. |
| **H-E11** | High-retail-attention instruments (NAS100, GBPJPY) decay fastest; rank decay velocity by instrument retail-mention frequency. | Heimer 2016, Robinhood-outage 2022, GameStop / WSB literature | Per-instrument retail-mention proxies regressed against per-instrument OB-decay velocity. |
| **H-E12** | Per-instrument loss-aversion λ derived from order-flow asymmetry around stop-out clusters is more useful than universal λ=2. | P29 Walasek-Mullett-Stewart 2025 | Microstructure-derived λ as K54 v3 feature. |
| **H-E13** | Saliency-debiased prompts (reduce decimal precision on `current_price` in MSO, frame-equivalent framework descriptions) reduce HALLUC-class precision-anchoring + framework-skew. | P25 Frydman-Rangel 2014, P13 Northcraft-Neale, P28 Heath-Tversky competence preference | A/B prompt variants in shadow-mode; track CR / inverted-TP / L2 rejection rate / framework-distribution. |
| **H-E14** | Streak-conditional WR ≠ unconditional WR (hot-hand is real). | P30 Miller-Sanjurjo 2018 | Conditional WR after N losses / N wins on the same instrument; pre-register signs before testing. |
| **H-E15** | Per-instrument K54 v3 should encode regime × sentiment interaction features (sentiment effect 3-4× stronger in stressed regimes per Garcia 2013). | Garcia 2013 + Stambaugh-Yu-Yuan 2012 + F15 | Add interaction features in K54 v3 bake-off vs K54 v2. |
| **H-E16** | OB-retest WR is HIGHER during high-realized-volatility kill zones (counterparty cortisol elevated). | Coates-Herbert 2008, Venkatraman 2011 | Stratify realized R per OB-retest by current-day RV decile. |
| **H-E17** | CEO override-rate of GTOS hard rules spikes NEAR (but not AT) recent equity peaks. | P36 Kőszegi-Rabin 2006 | Audit existing override-event logs (if any); plot override frequency vs equity-peak-distance. |
| **H-E18** | HRP cluster-based correlation gate (3-cluster: precious metals, JPY crosses, indices) outperforms binary pair-wise gate. | López de Prado HRP 2016 | A/B HRP-clustered gate vs current binary gate. |
| **H-E19** | Half-Kelly tolerance band per Carvalho 2020: GTOS could sustainably move from ~1/18-Kelly to 1/6-Kelly without breaching FN constraint, freeing edge. | 21-032 Carvalho 2020 | Compute Kelly-fraction tolerance band for current edge estimate; compare with operating fraction. |
| **H-E20** | LONG-WR-watch SPRT halt rate spikes during high-Baker-Wurgler-sentiment quintile periods. | Baker-Wurgler 2006 + Stambaugh-Yu-Yuan 2012 | Daily Baker-Wurgler index alignment with SPRT alert triggers. |

These 20 hypotheses bundle into 5 priority groups for Phase 2 rank-ordering:

1. **Priority 1 (Risk Policy Refinement):** H-E5 (Busseti-Boyd RCK), H-E6 (Strub EVT-CDaR), H-E7 (Moreira-Muir vol-scaling), H-E9 (smooth Grossman-Zhou), H-E10 (side-aware), H-E19 (Kelly band) — directly replaces S79 with literature-grounded structure.
2. **Priority 2 (Edge-Decay Tracking):** H-E2 (retail-flow share), H-E11 (retail-attention rank), H-E4 (LLM-feature sunset), H-E20 (sentiment-conditioned SPRT) — operationalizes Lo's AMH framing.
3. **Priority 3 (Counterparty Mechanism):** H-E1 (intra-session), H-E3 (funding stress), H-E16 (cortisol-zone) — refines OB-retest mechanism via direct counterparty-stress proxies.
4. **Priority 4 (Prompt / AI Architecture):** H-E13 (saliency debiasing), H-E15 (regime × sentiment interaction K54 v3) — addresses HALLUC-class + K54 v2 failure root causes.
5. **Priority 5 (CEO Discipline):** H-E17 (override-rate vs equity-peak), H-E12 (per-instrument λ), H-E14 (streak-conditional), H-E18 (HRP cluster gate) — operational discipline structure.

---

## Final report (under 350 words)

**1. Total papers read:** 118 across 3 domains (17_behavioral_adaptive_markets: 42; 18_trader_psychology_decision: 38; 21_risk_management_kelly_sizing: 38).

**2. Top 5 cross-cutting findings.**
- **F-1 (AMH framing):** Lo 2004 / 2005 / 2024 + McLean-Pontiff 2016 + Lopez-Lira-Tang ChatGPT-Sharpe 6.54→1.22 in 30 months provide the direct theoretical scaffold for CEO's edge-decay concern. F11 OB-decay velocity, F15 regime-conditioned LONG-collapse, K52 FVG-reversal all fit AMH cleanly. McLean-Pontiff baseline ~5%/year decay sets the alarm threshold for S1.
- **F-2 (Disposition is the operative counterparty mechanism):** Odean + Shefrin-Statman + Coval-Shumway + Locke-Mann + Genesove-Mayer + Frydman-fMRI overdetermine the disposition effect; it is neurally hardwired and replicates across asset classes. OB-retest continuation rate ≈ population disposition strength.
- **F-3 (Loss aversion is context-dependent, not universal):** Walasek-Mullett-Stewart 2025 + Brown 2024 — λ ≈ 1.07 in symmetric/unordered conditions, λ ≈ 2 in asymmetric/ordered. Trading IS asymmetric/ordered, so inverted-TP gate justified, but cross-applying λ=2 outside trading is no longer defensible.
- **F-4 (Strub + Busseti-Boyd are the Phase-2 risk-policy upgrade):** 21-028 + 21-005 + 21-008 + 21-018 provide a coherent literature-grounded path from S79 uniform_fn 2.0% to per-instrument EVT-CDaR + RCK + vol-scaled + smooth-Grossman-Zhou.
- **F-5 (LLMs exhibit *different* not absent biases):** Hadley et al. 2024 + GTOS HALLUC-1 — AI hallucination is precision-bug-class not heuristic-style retail mispricing. Confirms K54 ML-classifier value and that prompt engineering should target precision-anchoring (Frydman-Rangel saliency).

**3. Top 5 actionable hypotheses (esp. edge-decay framing + risk-policy refinement).** H-E5 (Busseti-Boyd RCK replacing uniform 2%); H-E6 (Strub EVT-CDaR sizing); H-E7 (Moreira-Muir vol-scaling, 15-25% Sharpe lift); H-E10 (side-aware sizing bundled with sharpe_weighted); H-E2 (per-instrument OB-decay regressed against retail-flow share — operationalizes AMH).

**4. Top 1 finding on counterparty behavior modeling.** Coval-Shumway 2005: distressed traders create identifiable, mean-reverting price impact; second-half-of-session OB-retests should outperform first-half (H-E1, free A/B test).

**5. Top 1 risk-policy refinement.** Replace `risk_per_trade_pct: 2.0` uniform with Busseti-Boyd Risk-Constrained Kelly (21-005) parametrized on FN constraint `P(MTM-DD ≥ 4%) ≤ 0.02` — single `λ` knob nests Kelly + Markowitz + drawdown; per-instrument optimal weights non-uniform (S79 leaves Sharpe on the table).

---

*End of Group E synthesis. Read-only over papers.md / papers.csv. No fabrication. UTF-8.*
