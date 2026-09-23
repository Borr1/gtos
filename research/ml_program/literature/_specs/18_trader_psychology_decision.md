# Domain 18 — Trader Psychology & Decision Under Uncertainty

**Slug:** `18_trader_psychology_decision`
**Owner:** Phase 1 Worker Agent #18
**Target paper count:** 25-40

---

## 1. Domain scope statement

This domain owns research at the **individual decision-maker level**: prospect theory, heuristics-and-biases, overconfidence, disposition effect, gambler's fallacy / hot-hand, anchoring, framing, regret, loss aversion, decision under ambiguity (Knightian uncertainty), expert-vs-novice trader cognition, time-pressure trading errors, emotion / affect in financial decisions (Lo neuroscience papers), professional-trader interview studies, prop-firm / risk-rule psychology, gamification effects (Robinhood), expert intuition (Klein, Kahneman dialogue).

**IN scope:** Kahneman-Tversky 1979 prospect theory, Tversky-Kahneman 1992 cumulative prospect theory, Odean disposition effect, Barber-Odean overconfidence, Lo Repin physiology of trader, Kahneman Lovallo planning fallacy, Camerer behavioral game theory, Knight 1921 risk-vs-uncertainty, Ellsberg paradox, ambiguity aversion, framing effects in trading, prop-firm psychology empirical work.

**OUT of scope:** **Aggregate market behavior** from individual biases → 17; **individual-trader algorithm-design biases** (model overfit) → 02; **risk management per-trade rules** under fat tails → 21; **AI-prompt psychology** of GTOS's own AI agent → engineering/research, NOT this domain.

---

## 2. Search strategy

### Keywords
- "prospect theory" decision under risk Kahneman Tversky
- "cumulative prospect theory" 1992
- "disposition effect" Odean Shefrin Statman
- "overconfidence" trading Barber Odean
- "gamblers fallacy" "hot hand" empirical
- "anchoring" trading exchange rate Northcraft
- "framing effect" trader decision
- "loss aversion" trading
- "expert intuition" Klein Kahneman
- "ambiguity aversion" Ellsberg trader
- "Knightian uncertainty" decision
- "trading psychology" stress
- "Lo Repin" physiology trader
- "professional trader" expertise study
- "prop firm" psychology evaluation
- "Robinhood" gamification trading

### Key journals
- *Journal of Finance*
- *Quarterly Journal of Economics*
- *Journal of Risk and Uncertainty*
- *Cognitive Psychology*
- *Journal of Behavioral Decision Making*
- *Journal of Financial Markets*
- *Management Science*
- *Journal of Behavioral and Experimental Finance*

### Repositories
- arXiv `q-fin.GN`, `econ.GN`
- SSRN Behavioral Finance
- NBER Behavioral Economics
- Robert Shiller Yale page
- Andrew Lo MIT Lab
- Daniel Kahneman / Amos Tversky archive (Princeton)

### Key authors
- Daniel Kahneman, Amos Tversky (foundational)
- Terrance Odean, Brad Barber (retail / disposition)
- Hersh Shefrin, Meir Statman (behavioral finance)
- Andrew Lo, Dmitry Repin (trader physiology)
- Colin Camerer (behavioral game theory)
- Frank Knight (uncertainty vs risk — historical)
- Richard Thaler (behavioral economics)
- Gary Klein (naturalistic decision)
- Ulrike Malmendier (overconfidence)

---

## 3. Seed papers — foundational

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 1 | Prospect Theory: An Analysis of Decision under Risk | Kahneman, Tversky | 1979 | https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_Tversky_1979_Prospect_theory.pdf |
| 2 | Advances in Prospect Theory: Cumulative Representation of Uncertainty | Tversky, Kahneman | 1992 | search Journal of Risk and Uncertainty 1992 — verify |
| 3 | Are Investors Reluctant to Realize Their Losses? (disposition) | Odean | 1998 | https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/areinvestorsreluctant.pdf |
| 4 | Boys Will Be Boys: Gender, Overconfidence, and Common Stock Investment | Barber, Odean | 2001 | search Quarterly Journal of Economics — verify |
| 5 | The Disposition to Sell Winners Too Early and Ride Losers Too Long | Shefrin, Statman | 1985 | search Journal of Finance — verify |
| 6 | Risk, Uncertainty and Profit (book) | Knight | 1921 | classic — public domain |
| 7 | Psychophysiology of Real-World Trading | Lo, Repin | 2002 | search Journal of Cognitive Neuroscience — verify |
| 8 | Conditions for Intuitive Expertise: A Failure to Disagree | Kahneman, Klein | 2009 | search American Psychologist — verify |
| 9 | Judgment Under Uncertainty: Heuristics and Biases | Tversky, Kahneman | 1974 | search Science Vol 185 — verify |

### Recent advances 2020-2025

| # | Title | Authors | Year | URL |
|---|-------|---------|------|-----|
| 10 | Robinhood and gamification | various | 2021-23 | search SSRN Robinhood |
| 11 | Overconfidence in algorithmic trading 2020-24 | various | 2022-25 | search SSRN |
| 12 | Stress / decision quality in market crash regimes | various | 2021-24 | search SSRN |
| 13 | LLM as decision aid for traders | various | 2023-25 | search arXiv |
| 14 | Disposition effect under prop-firm rules | various | 2022-25 | search SSRN |
| 15 | Disposition effect and reference points: An experimental study | recent | 2023 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10096489/ |

---

## 5. GTOS subsystem connections

- **CEO operating discipline** — directly informs WF-1 decision rules and post-loss-restraint patterns.
- **Disposition effect** maps to GTOS's hard rules ("any single trade > 1.5R" emergency stop) — literature on why human traders break this rule informs why an automated system enforcing it is the edge.
- **Loss aversion / asymmetric SL placement** — `risk.sl_buffer_atr_multiplier` and inverted-TP auto-correction are direct mitigations of human biases the literature documents.
- **AI prompt psychology** — Sonnet-4.6 vs Opus 4.7 for MSO gate (CR 38% vs 19%); literature on overconfidence in expert decision-making is directly relevant for understanding the AI's behavior.
- **HALLUC-1 NAS100 deterministic precision bug** — distinguishing AI hallucination (perception bias) vs precision bug (deterministic) maps to expert-error-classification literature.
- **A4 trending_bull replay** — AI did not change selectivity post-fix; literature on expert-confidence-when-confronted-with-evidence informs this finding.
- **Council workflow** (3-stage, on-demand) — anonymized ranking is a direct application of debiasing literature.

---

## 6. Cross-domain handoff rules

- **Aggregate-market noise-trader behavior** → 17.
- **Sentiment-as-data** → 17.
- **Risk-management rules under fat tails (Kelly etc.)** → 21.
- **LLM-extracted trader-emotion at scale** → 20.
- **Risk-aversion in factor pricing** → 13 / 17 split.

---

## 7. Output spec

Files:
- `research/ml_program/literature/18_trader_psychology_decision/papers.md`
- `research/ml_program/literature/18_trader_psychology_decision/papers.csv`

Same schema. Special field: `subject_population` (retail / professional / experimental / general decision-maker).

---

## 8. Quality bar / target

25-40 papers. Lower bound because this is concentrated literature with limited GTOS-system-actionable findings; quality > quantity. Aim for at least 5 papers that explicitly connect to algorithmic / AI trading systems vs purely human behavioral findings.
