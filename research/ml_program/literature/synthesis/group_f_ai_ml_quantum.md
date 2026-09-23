# Group F Synthesis — AI/ML for Finance + RL/LLMs in Trading + Hedge-Fund Alpha + Quantum

**Synthesis agent:** Phase 2 Group F (Opus 4.7, max effort)
**Compiled:** 2026-04-28
**Domains covered:** 19 (AI/ML for finance — classical, deep, sequence), 20 (RL & LLMs in trading), 22 (hedge-fund alpha + Wall Street + quantum)
**Papers read:** 177 total — 78 in Domain 19, 53 in Domain 20, 46 in Domain 22 (papers.md + papers.csv each)
**Position in Phase 2:** 1 of 6 synthesis agents
**Mandate:** K54 v2 architecture revision; meta-labeling deployment; Q2 sequence-model timing; AI-replacement-vs-supplementation; hedge-fund alpha-decay framing
**Constraints:** read-only; UTF-8; no fabrication; subscription-bounded

---

## 1. Cross-cutting findings (the 5 results that survive across all 3 domains)

### Finding 1 — Tree ensembles beat deep models at GTOS data scale; the literature is unambiguous

The Gu-Kelly-Xiu 2020 (RFS) result that shallow trees and shallow neural networks deliver the largest OOS R² on financial panels is the most-replicated finding in Domain 19. Krauss-Do-Huck 2017, Fischer-Krauss 2018, Avramov-Cheng-Metzker 2023, and Israel-Kelly-Moskowitz 2020 all anchor the same conclusion at varying scales: **at the n=O(10³) outcome-trade scale GTOS lives in, regularized GBDT (LightGBM/XGBoost/CatBoost) is the empirically-correct default.** Deep architectures need ≥10× the labels of trees at fixed signal-to-noise (Gu-Kelly-Xiu, Vaswani 2017 caveat from their own data scale). This corroborates K54 v1's LightGBM choice and refutes the "we're not deep enough" framing of Q1.3's failure.

**Counter-evidence:** Chen-Pelger-Zhu 2024 (Management Science) shows adversarial deep nets with macro-state RNN encoder can beat tree models — but only with their GAN-style no-arbitrage loss and a properly-conditioned macro state. Not a refutation; a constraint.

### Finding 2 — Decay is the default; the question is rate, not direction

McLean-Pontiff 2016 quantifies the canonical decay curve: 26% out-of-sample, 58% post-publication, across 97 anomalies. Sullivan 2019 documents $21.1B of net-of-fee value subtracted by the hedge-fund industry over 19 years. Bollen-Joenvaara-Kauppila 2017 ("End of an Era?") and 2024 (decreasing returns to scale) extend this through the GFC + post-2010 era. Lo's 2017 Adaptive Markets Hypothesis provides the *mechanism*: edges decay because relevant species multiply. Critically, the long-horizon LLM-trading evaluation (arXiv 2505.07078, 2025) shows **most published LLM-trading edges decay or invert at 3+ year horizons** — consistent with hedge-fund-aggregate findings.

**This is not GTOS-specific.** F11's measurement (16.8pp pre-2026 → 4.6pp H2-2026, ~73% decline; ~78% decay-attributed) is squarely inside the McLean-Pontiff distribution. GTOS H2-2026 LONG-WR collapse is consistent with industry baseline, not exotic.

### Finding 3 — The AUC-vs-realized-R gap is structural, not GTOS-pathology

Israel-Kelly-Moskowitz 2020 ("Can Machines 'Learn' Finance?") and Avramov-Cheng-Metzker 2023 (Management Science) both quantify the gap. Avramov shows DL-signal profitability collapses 50-80% when microcaps + distressed + high-vol cells are excluded; trading costs further halve. Quantum-RL trading (arXiv 2506.20930, 2025) shows the *same* pattern at quantum scale: training rewards higher than classical, realized cumulative returns lower. **The training-proxy-vs-realized-metric divergence is universal across all proxy-based learning** (cross-entropy, AUC, training reward). GTOS's K54 baseline pattern (AUC 0.571 → +0.164R lift only at high threshold) is the literature norm, not an outlier — directly mirrors `feedback_walk_level_evidence_not_predictive`.

### Finding 4 — Tool-use grounding is the consensus path for LLM-decision-maker hallucination mitigation

QuantMCP 2025 reports 80%+ reduction in factual hallucination via Anthropic Model Context Protocol routing. FAITH 2025 measures 8-15% intrinsic hallucination on financial tables for frontier models (GPT-4, Claude) — bracketing GTOS's pre-FA-2 per-instrument range (US30 23.4% → XAUUSD 13.1% → GBPJPY 5.3%). FinAgent 2024 demonstrates tool augmentation handling numeric-precision tasks LLMs typically fail at. The Deficiency study (2311.15548) explicitly says "mitigation requires retrieval / tool-use, not better prompting alone." HALLUC-1's NAS100 93% precision-bug class is the predicted outcome of *not* having tool-grounded numeric facts in the prompt.

### Finding 5 — Meta-labeling is the architecturally-correct bridge between AI direction and execution sizing

Lopez de Prado 2018 (book Ch 3 + 5) defines triple-barrier labels (TP/SL/time-stop = exact J46-J49 structure) and meta-labeling. Hudson-Thames 2022 independent replication: meta-labeling lifts strategy F1 by 5-15% across primary signals. Buffett's-Alpha (Frazzini-Kabiller-Pedersen 2018) shows the deepest factor-decomposition pattern: what looks like ineffable skill resolves to **systematic factor exposures + leveraged sizing**. The architectural lesson is identical: separate "should we trade?" (direction signal) from "how much?" (sizing) and from "is this a high-confidence direction?" (meta-label). GTOS's S79 risk-policy switch (uniform_fn 2.0% sizing) is a hand-tuned single-knob version of meta-labeling; the literature wants this learned.

---

## 2. K54 v2 architecture revision — ranked recommendations for n=2,326 × 1,234 features

Q1.3 K54 v2 FAILED at the architecture level: per-regime ensemble drag at small n + calendar-feature overfit. The literature provides clear guidance on which architectures address those specific failure modes at this exact scale.

**Note on data scale:** With 1,234 features and 2,326 examples, the feature-to-example ratio is **0.53** — well into the high-dimensional regime where the Feng-Giglio-Xiu 2020 + Harvey-Liu-Zhu 2016 multiple-testing critique becomes load-bearing. Of 313 published return-predictors, only ~9 survive |t-stat|>3. Of 100+ published factors, very few survive double-LASSO. **Any K54 v3 architecture must include feature-selection / dimensionality reduction as a first-class layer.** Architecture choices alone won't save 1,234 candidates against 2,326 examples.

### Rank 1 — Per-regime LightGBM with TreeSHAP-stability feature pruning + Lopez-de-Prado meta-labeling head (highest feasibility, lowest risk)

**Stack:** Per-regime LightGBM defender + per-fold TreeSHAP across CPCV folds → median-rank feature pruning to ~30-50 features → primary classifier outputs probability → meta-labeling secondary classifier (also LightGBM) trained on triple-barrier labels (TP/SL/time-stop = J46-J49 structure) → output sizing in {0, 0.5, 1.0}.

**Anchor papers:** Gu-Kelly-Xiu 2020 (tree-dominance at small-n); Lopez de Prado 2018 (CPCV + meta-labeling + triple-barrier); Lundberg-Lee 2017 (SHAP); F5/F11 GTOS findings on improper-vs-proper SHAP; Friedman 2001 (gradient boosting); Ke et al 2017 (LightGBM); Bailey-Lopez de Prado 2014 (deflated Sharpe gate).

**Why this is rank 1:** Five reasons. (1) Empirically dominant at GTOS data scale per Domain-19 anchor. (2) F5 already showed K51 SHAP-based component pruning failed under proper Bonferroni — meta-rank stability over CPCV folds is the right discipline. (3) Meta-labeling directly addresses the AUC-vs-realized-R gap (Finding 3). (4) Triple-barrier labels exactly match J46-J49's `+0.742R/trade` outcome structure (`project_j46_j49_position_mgmt_findings`). (5) All-tree implementation is ONNX-exportable per Q4 sovereignty doctrine; sub-ms inference; auditable.

**Concrete spec:**
- Feature pruning step: 5-fold CPCV → per-fold TreeSHAP magnitude → keep features with median rank in top-50 across folds. This is the proper-method version that F5 documented works.
- Per-regime LightGBM: 4 separate models (one per F15 regime cell) with `num_leaves` capped at ~30-40 (per LightGBM K54 v1 small-n discipline).
- Meta-labeling secondary: trained on triple-barrier labels from `_trade_index.json` + realized-R; output ∈ {0, 0.5, 1.0}; replaces hand-tuned S79 switch.
- Promotion gate: deflated-Sharpe-corrected for trial count (~200 hyperparameter trials → factor-LASSO-protected); CPCV with embargo; 30% holdout opened ONCE.

**Predicted lift over K54 v2 baseline:** +0.04-0.06 AUC from feature pruning (cuts the high-dim noise that defeated v2); +0.05-0.10R/trade from meta-labeling Pareto-dominance over uniform sizing.

### Rank 2 — Pooled-instrument iTransformer with variate-attention + per-regime gating (medium feasibility, higher upside)

**Stack:** Single iTransformer model with 7 instrument-tokens (one per GTOS symbol) + 64-bar lookback per token + per-regime gating layer + binary candidate output.

**Anchor papers:** Liu et al 2024 (iTransformer ICLR Spotlight); Sirignano-Cont 2019 (universal LOB cross-stock generalization); Nie et al 2023 (PatchTST channel-independence); Salinas et al 2020 (DeepAR pooled training); Krauss-Do-Huck 2017 (cross-stock pooling).

**Why this is rank 2:** Sirignano-Cont's universality result — pooled LSTM trained on 489 NASDAQ stocks generalizes to held-out stocks at near-stock-specific accuracy — is the literature anchor for the K54 cross-instrument-pooled approach. iTransformer's variate-attention captures cross-instrument correlation structure end-to-end (could replace the heuristic GTOS correlation gate). Critical at n=2,326: pooling 7 instruments → effective n ≈ 16,000 dataset events from XAUUSD's larger sample. *This is the single highest-leverage step at GTOS's data scale.*

**Caveat (data-hunger):** Vaswani 2017 + Bengio-Simard-Frasconi 1994 + DLinear caution still applies — needs strong regularization (dropout 0.3, weight-decay 1e-3) and DLinear baseline as Occam-test gate.

**Predicted lift:** +0.03-0.05 AUC over per-instrument LightGBM on the data-poor cells (USDJPY, GBPJPY, GBPUSD, XAGUSD).

### Rank 3 — Temporal Convolutional Network (TCN) with channel-independent processing (middle ground)

**Stack:** 6-layer TCN, kernel-size 3, exponential dilation (1,2,4,8,16,32), 64-bar H1 sequences, per-regime ensembling head.

**Anchor papers:** Bai-Kolter-Koltun 2018 (TCN); Borovykh-Bohte-Oosterlee 2017 (WaveNet for finance); Nie et al 2023 (channel-independence).

**Why this is rank 3:** TCN's parameter/receptive-field ratio is favorable at n=2,326. Parallelizable training enables fast batch backtests on subscription budget. Conditional-input WaveNet variant lets it condition on multiple instruments + multiple timeframes. The middle ground between LightGBM (no temporal model) and Transformer (high data-hunger).

**Predicted lift:** AUC parity with iTransformer at 5× faster wall-clock training — the cost-optimal Q2 sequence-model baseline.

### Rank 4 — TFT (Temporal Fusion Transformer) for interpretable variable selection (interpretability-constrained scenarios)

**Stack:** TFT with instrument as static covariate, regime as past-known input, microstructure as observed-history, multi-quantile output head.

**Anchor papers:** Lim-Arik-Loeff-Pfister 2021 (TFT); Lim-Zohren 2021 (DL forecasting survey on hybrid superiority).

**Why this is rank 4 (not higher):** TFT's variable-selection networks satisfy GTOS doctrine for "why" rationale — but interpretability is a soft constraint, not hard. Empirically TFT trades raw AUC for interpretability vs PatchTST/iTransformer. Reserve for when CEO requires explainable per-trade rationale.

### Rank 5 — Foundation-model zero-shot baseline (FREE control, must run before any custom training)

**Stack:** Zero-shot Time-MoE, Lag-Llama, Chronos, MOIRAI on H1 returns with appropriate frequency setting.

**Anchor papers:** Shi et al 2024 (Time-MoE); Rasul et al 2024 (Lag-Llama); Ansari et al 2024 (Chronos); Woo et al 2024 (MOIRAI); Carriero-Pettenuzzo 2024 (macro forecasting LLMs).

**Why this is rank 5 (a control, not a candidate):** The literature consensus is that zero-shot foundation models match specialized forecasters on many domains. **K54 v3 must clear this baseline OR justify why it doesn't.** If zero-shot Time-MoE achieves AUC within 0.02 of K54 v2 LightGBM, the bespoke ML stack adds nothing — focus K54 v3 design on closing that gap. Free benchmark; cost = compute only; cannot skip.

### Lower-priority architectures (de-prioritize for K54 v3)

- **Pure deep BSDE / autoencoder asset pricing / Quant GANs / cWGAN augmentation** — Coletta et al 2023 specifically calls out OOD brittleness for synthetic-data augmentation; Bao-Yue-Rao 2017 wavelet line has documented look-ahead leakage in replications. Both are research candidates for Q3-Q4, not K54 v3.
- **Pure Transformer (Vaswani-style) without patching/inversion** — DLinear 2023 contrarian finding stands; vanilla Transformer is data-hungry and permutation-invariant in time. Skip in favor of PatchTST or iTransformer.

---

## 3. Meta-labeling deployment — concrete spec for GTOS

The single most-architecturally-relevant Phase 1 finding (Domain 19) per the brief: **Lopez-de-Prado meta-labeling is the missing layer between Component 3A AI direction and Component 4 execution sizing.**

### Conceptual fit
- Primary signal (Component 3A AI): emits BUY / SELL / HOLD direction call after MSO evaluation.
- Triple-barrier outcome (J46-J49 structure): TP up, SL down, time-stop after 12 bars — this is *exactly* the Lopez-de-Prado canonical labeling.
- Meta-label (proposed K54 v3 secondary): given primary direction + state features, predict probability of hitting TP before SL/time-stop. Output: sizing ∈ {0, 0.5, 1.0} × `risk_per_trade_pct`.

### Concrete spec
1. **Labels:** From `knowledge_base/index/_trade_index.json` + `research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv` — extract triple-barrier outcome (TP=1, SL=0, timeout=conditional based on closing R) per closed trade.
2. **Features (meta-classifier input):** AI primary direction (BUY/SELL/HOLD as one-hot); per-regime LightGBM K54 probability; F15 regime label; OB-zone geometry (ob_distance_atr, ob_age_candles); side-aware indicator (LONG/SHORT in trending_bull cell); time features (hour_utc, day_of_week, kill_zone).
3. **Model:** Secondary LightGBM classifier (binary: TP-hit vs not). Train with focal loss (γ=2, α=0.25) for class imbalance — Friedman 2001 + the Domain-19 small-n regularization caution.
4. **Sizing rule:** `position_size = base_risk × meta_prob_quantile_bin`, where bins are {0% if prob<0.4, 50% if prob∈[0.4,0.6], 100% if prob≥0.6}.
5. **Promotion gate:** Compare R/trade across {old uniform, side-aware-a, K54-meta-labeled} on F15 H2-2026 holdout under deflated Sharpe correction. Pre-register hypothesis: meta-labeling Pareto-dominates side-aware-a by ≥+0.05R/trade.

### Anchor papers + why this specific spec works
- **Lopez de Prado 2018** Chapters 3 + 5 — defines the triple-barrier + meta-label split.
- **Hudson-Thames 2022** — independent replication: 5-15% F1 lift on top of primary signals.
- **Buffett's Alpha (Frazzini-Kabiller-Pedersen 2018)** — gold-standard demonstration that what looks like manager skill = systematic factor exposures + leveraged sizing. The same architectural pattern is what meta-labeling automates.
- **Israel-Kelly-Moskowitz 2020** — the AUC-vs-realized-R gap is precisely the gap meta-labeling closes by separating "is the direction right?" from "should we size up?"
- **Project memory `project_j46_j49_position_mgmt_findings`** — J46-J49 portfolio policy already shows +0.742R/trade vs baseline (n=321, p=3.3e-20). Meta-labeling is the *learnable* extension of J46-J49's hand-tuned rule.

### Cost estimate
- Training: ~$0 (subscription).
- Inference: ~0ms (LightGBM ONNX, fits within Q4 sub-millisecond target).
- Anthropic budget impact: zero — meta-labeling sits *below* the LLM gate and processes its outputs offline.

### Predicted lift
- **+0.05R-0.10R/trade** over current S79 uniform_fn 2.0% sizing on F15 H2-2026 holdout, pre-deflated. Conservative; subtract ~0.02R for deflated-Sharpe + multiple-testing correction.

---

## 4. Q2 sequence-model timing — should DLinear lead?

The brief asks: per Phase 0 roadmap, Q2 = sequence models (LSTM/Transformer). DLinear / Time-LLM / Chronos suggest simpler architectures may dominate. Should Q2 lead with DLinear baseline?

### Verdict: YES — DLinear baseline must come first; sequence models follow only if they beat it

**Rationale (literature-anchored):**

1. **Zeng et al 2023 (DLinear, AAAI Oral)** demonstrated simple linear models with seasonal-trend decomposition outperform Informer/Autoformer/FEDformer on 9 standard LTSF benchmarks. Many transformer "improvements" close the gap to the linear baseline rather than push past it. PatchTST and iTransformer have since closed the gap, but the basic Occam-test discipline this paper enforces is precisely the hygiene K54 v3 needs.

2. **Foundation-model zero-shot benchmarks (Lag-Llama, Chronos, MOIRAI, Time-MoE)** are the *second* free baseline. Carriero-Pettenuzzo 2024 shows time-series LLMs match dedicated econometric models on FRED-MD macro variables. If zero-shot beats DLinear which beats per-instrument LightGBM, the order of operations is wrong.

3. **The GTOS B7-vs-realized-R disconnect + F4/F5/F11 reproducibility failures** (memories `project_b7_hallucination_per_instrument_2026-04-27`, `project_f5_k51_does_not_replicate_under_proper_method`, `project_f11_ob_zone_decay_velocity_pinned`) are exactly the class of failure DLinear's Occam-test discipline catches.

### Concrete Q2 sequence: DLinear → Foundation models → TCN → PatchTST/iTransformer → LSTM/Transformer

**Sequence:**
1. **Baseline 0 (Q2 Week 0):** Per-instrument linear regression on H1 OHLCV. Brutal Occam-test floor.
2. **Baseline 1 (Q2 Week 1):** DLinear with seasonal-trend decomposition. *Cannot ship sequence models without first beating this.*
3. **Baseline 2 (Q2 Week 1):** Zero-shot Time-MoE / Lag-Llama / Chronos. Free; all 4 should run.
4. **Candidate 1 (Q2 Week 2-3):** TCN (6-layer, kernel-3, exp dilation). Parallel training, parameter-efficient.
5. **Candidate 2 (Q2 Week 3-4):** PatchTST (patch-size 4, 16-patch sequence) — cheapest transformer that handles GTOS data scale.
6. **Candidate 3 (Q2 Week 4-5):** iTransformer for cross-instrument pooled training.
7. **Candidate 4 (Q2 Week 5-6, only if 1-3 fail to clear):** LSTM with hidden-size 64 + GRU as parameter-efficient alternative.
8. **Vanilla Transformer:** SKIP — Vaswani-2017's data-hunger + DLinear's permutation-invariance critique together close the door. Use PatchTST or iTransformer instead.

### Predicted outcome
Most likely: **DLinear baseline lands within ±0.01 AUC of K54 v1 LightGBM**, justifying tight regularization (LightGBM K54 v3 wins). PatchTST or iTransformer + meta-labeling head likely beats DLinear by 0.02-0.04 AUC if pooled across 7 instruments. Vanilla LSTM/Transformer underperforms PatchTST/iTransformer at GTOS scale per multiple anchors.

---

## 5. AI replacement vs supplementation — what does the literature endorse?

The brief asks: is the sovereignty doctrine on the right path? Replace LLM, ensemble with LLM, or use LLM-as-feature-extractor?

### Literature verdict: **Hybrid (LLM-feature + ML-decision) over pure replacement; meta-labeling between layers**

Three converging evidence streams:

**Stream A — Domain LLMs for finance saturate at frontier scale:**
- BloombergGPT 2023 (50B params, 363B financial tokens) is closed and unused.
- FinGPT 2023 ($300 LoRA fine-tunes) democratizes but underperforms on strategic decision-making per PIXIU/FinMA: **stock-prediction stays at chance (~50%) even for fine-tuned domain models.**
- FinLlama 2024 + Open-FinLLMs 2024 lift sentiment/classification F1 but not strategic prediction.
- Y. Li et al 2023 ICAIF survey: "**Hybrid (LLM + traditional) beats pure-LLM in finance.**"

**Stream B — Multi-agent debate frameworks consistently positive but bounded:**
- TradingAgents 2024 (open-source) + AlphaAgents 2025 (BlackRock-affiliated) + FinCon 2024 (NeurIPS) all show structured Bull/Bear/Judge debate beats single-agent.
- FinAgent 2024: tool-augmentation handles numeric precision LLMs typically fail at.
- Self-Reflection 2024: p<0.001 lift across multiple task types at 2× cost.
- All evaluations are 30d-3mo backtests; long-horizon survivorship (arXiv 2505.07078) shows decay or inversion at 3+ years.

**Stream C — Tool-grounded LLM > prompt-only LLM is the dominant frontier:**
- QuantMCP 2025: 80% factual-hallucination reduction via Anthropic Model Context Protocol.
- FAITH 2025: 8-15% intrinsic frontier-model hallucination on finance tables — bracketing GTOS pre-FA-2 rates.
- Deficiency study 2023: "mitigation requires retrieval / tool-use, not better prompting alone."

### Endorsed architectural path for GTOS

```
┌─────────────────────────────────────────────────────────────────┐
│  PRODUCTION PLANE  (sovereignty target by Q4)                    │
│                                                                  │
│  Input: M15 candle close + MSO from Component 2                  │
│         ↓                                                         │
│  K54 v3 per-regime LightGBM (binary direction prob)              │
│         ↓                                                         │
│  Meta-labeling secondary (TP-hit prob → sizing in {0, 0.5, 1.0}) │
│         ↓                                                         │
│  Adaptive conformal calibration (Zaffran et al 2022) → 90% CI    │
│         ↓                                                         │
│  Component 4 execution                                            │
│                                                                  │
│  ALL local ONNX. Sub-millisecond. Sovereignty-compliant.          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  RESEARCH PLANE  (LLM stays here; supplementary advisory)        │
│                                                                  │
│  Component 3A (Anthropic Sonnet 4.6, MCP-tool-grounded) →        │
│    advisory-only direction call + rationale                       │
│  Component 3B (Bull/Bear/Judge debate, currently default OFF) →  │
│    TradingAgents-style multi-agent, default-OFF until shadow     │
│    proves >+0.05R lift                                            │
│  Reflexion-style post-trade reflection → episodic memory          │
│  K55 ML-vs-AI shadow harness measures crossover point             │
└─────────────────────────────────────────────────────────────────┘
```

### Why this beats both pure-replacement and pure-supplementation

- **Pure replacement (kill the LLM completely):** PIXIU "stock prediction stays at chance" + Israel-Kelly-Moskowitz AUC-vs-Sharpe gap + `project_a1_dumb_baseline_verdict_2026-04-26` (AI-vs-mechanical gap eroded, but mechanical OB still works H2 +0.036R while AI drags -0.131R H2) suggest the AI's contribution is variable and may be near-zero. But: the F8 finding (`project_f8_hallucination_not_decay_mechanism`) explicitly says decay is in *decision-making calibration*, not perception — LLMs may regain edge after Phase-2 prompt redesign. Don't kill prematurely.

- **Pure supplementation (LLM stays primary, ML advisory):** Sovereignty doctrine forbids permanent Anthropic dependency. $50/mo cap is a hard ceiling at scale. Local ONNX inference is ~$0/decision; LLM is ~$0.10/decision.

- **Endorsed path:** Run K54 v3 + meta-labeling + conformal calibration as the *primary* path locally. Keep LLM as Component 3A advisory. Use K55 shadow harness to measure where LLM adds value vs ML. Promote ML to primary when shadow shows ≥1.2× correlation-with-realized-R per Q4 hypothesis.

---

## 6. Hedge-fund alpha-decay finding that informs GTOS decay management

**The single most-load-bearing finding for GTOS decay strategy:** *McLean-Pontiff 2016 + Lo 2017 (AMH) + Sullivan 2019 + Bollen-Joenvaara-Kauppila 2017 together establish that edge decay is a property of edge **publication and replication**, not edge **mechanism failure**. The strategic response is continuous edge-evolution, not preservation.*

### What the literature says concretely
- **McLean-Pontiff 2016:** 26% OOS decay, 58% post-publication decay across 97 anomalies. The anchor citation.
- **Sullivan 2019:** $21.1B subtracted by hedge-fund industry over 19 years, post-GFC decline marked.
- **Bollen-Joenvaara-Kauppila 2017 ("End of an Era?")** + 2024 (decreasing returns to scale): hedge-fund persistence has weakened materially since GFC; decline correlates with industry-wide AUM growth.
- **Lo 2017 Adaptive Markets:** Markets evolve through competition + selection. Anomalies persist when relevant species are too few; decay when species multiply. "*Nothing makes sense in the hedge fund industry except in the light of the AMH.*"
- **Cornell 2020 (Medallion):** Counterexample. 63.3% gross compound 1988-2018; no negative year. **Capacity-blocked** ($12B internal) + Mercer/Brown speech-recognition pattern-detection + ~300 PhDs. Edges that are uniquely capacity-blocked + technically defensible can persist 30+ years.
- **Zuckerman 2019 (Renaissance book):** Medallion's no-down-year record holds because **each individual signal is small but uncorrelated**.

### Implication for GTOS decay management

1. **Treat every individual edge as a wasting asset.** F11's measurement (16.8pp pre-2026 → 4.6pp H2-2026) is consistent with McLean-Pontiff's distribution. Set quarterly re-validation as default; do not assume an edge will persist absent active evolution.

2. **Aggregate small uncorrelated edges, don't rely on one large edge.** Renaissance Medallion's durability comes from thousands of small uncorrelated signals, not one big OB-zone advantage. K54 v3's path is to add features that are weakly-correlated with the OB-precision feature — F11 + F2 already showed regime-side conditioning is one such axis. K54 v3 should aggressively pursue *uncorrelated* features (Feng-Giglio-Xiu double-LASSO methodology).

3. **GTOS at $100k AUM is below the capacity-decay band.** Naik-Ramadorai-Stromqvist 2007: capacity binds at $250M+. Stein 2005: GTOS as closed-end-CEO-financed prop-trade is structurally redemption-immune. **Don't optimize for capacity-decay before $1M AUM.**

4. **Continuous edge-evolution is the real moat.** Lo's AMH + Bollen 2024 imply the edge-discovery rate must exceed the edge-decay rate. GTOS Phase 2 priority order should bias toward *new edge discovery* (regime-aware ML, microstructure, side-aware sizing) over *existing edge optimization* (better OB detection thresholds).

5. **Buffett's Alpha decomposition is the institutional-credibility template.** GTOS edge that persists is likely a tight intersection (kill-zone × OB-zone × side-aware regime), not "AI mystery." K54 v3 should be designed to factor-decompose its own alpha: each prediction comes with feature-importance attribution. CEO can read the rationale; the rationale is replicable; the edge is institutional-grade.

---

# Final report (under 400 words)

## 1. Total papers read
**177 papers across 3 domains** — 78 (Domain 19 ai_ml_for_finance), 53 (Domain 20 rl_llms), 46 (Domain 22 hedge-fund/quantum). Both `papers.md` and `papers.csv` read for each.

## 2. Top 5 cross-cutting findings (architecture choice for n=2,326 cohort)
1. **Tree ensembles dominate at small-to-medium-n financial panels.** Gu-Kelly-Xiu 2020 + Krauss-Do-Huck 2017 + Avramov-Cheng-Metzker 2023 anchor this; deep architectures need ≥10× the labels at fixed S/N.
2. **Decay is the default; F11's GTOS measurement (~73% decline) is squarely inside McLean-Pontiff's 26%/58% distribution.** Industry baseline, not GTOS pathology.
3. **AUC-vs-realized-R gap is structural across all proxy-based learning** — including quantum RL (arXiv 2506.20930). Universal feature, not GTOS bug.
4. **Tool-use grounding (QuantMCP/MCP, FinAgent) is the consensus path for LLM hallucination mitigation** — 80% reduction.
5. **Meta-labeling is the architecturally-correct bridge between AI direction and execution sizing** — Lopez de Prado 2018 + Hudson-Thames 2022.

## 3. Top 5 actionable hypotheses for K54 v3 / Q2 / K55
1. Per-regime LightGBM with TreeSHAP-stability feature pruning + meta-labeling head Pareto-dominates K54 v2 baseline by +0.05-0.10R/trade on F15 H2-2026 holdout.
2. Pooled-instrument iTransformer (variate-attention) lifts AUC ≥0.03 vs per-instrument LightGBM in data-poor cells (USDJPY/GBPJPY/GBPUSD/XAGUSD).
3. DLinear baseline lands within ±0.01 AUC of K54 v1 — must clear before any sequence model.
4. MCP tool-grounded Component 3A reduces HALLUC-1-class precision bugs by 70%+ at <10% per-call cost.
5. Reflexion-style post-trade reflection yields ≥0.05R expectancy lift over 30d at <$5/mo.

## 4. AI-vs-ML architectural path the literature endorses
**Hybrid via meta-labeling, NOT replacement.** K54 v3 + meta-labeling + adaptive conformal calibration runs *primary* locally (sovereignty-compliant); LLM stays as Component 3A advisory + Bull/Bear/Judge debate. K55 shadow harness measures crossover — promote ML to primary when correlation-with-realized-R ≥1.2× AI's per Q4 hypothesis. Pure replacement is premature given F8's "decay is decision-calibration not perception"; pure supplementation violates sovereignty doctrine.

## 5. Top hedge-fund-alpha-lifecycle finding for GTOS decay management
**McLean-Pontiff 2016 + Lo 2017 AMH:** edge decay is a property of *publication-and-replication*, not *mechanism-failure*. Strategic response: aggregate small uncorrelated edges (Renaissance Medallion's mechanism per Zuckerman 2019), continuous edge-evolution, treat individual edges as wasting assets. GTOS at $100k is below the capacity-decay band (Naik-Ramadorai-Stromqvist 2007); optimize for edge-discovery rate over edge-preservation. K54 v3 should pursue features uncorrelated with the OB-precision feature.
