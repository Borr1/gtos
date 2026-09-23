# KB cycle 68 — ML trade-selection / reach-prediction on the deployed metals edge (the proven lever, deep attack)

**Setup.** Workflow wf_3e2a6d48-f27: one agent built a shared leak-free decision-bar feature+label store
(`SELECTION_FEATURE_STORE.jsonl`, 482 trades, 20 backward-only features, label reach_2R base rate 0.415);
5 modeling approaches (logistic, shallow tree, hand-rolled GBM, reach-regression, confluence-stack) each
fit on TRAIN(≤2021) and scored OOS+SEALED ONCE; adversarial verify deflated by the 73-trial budget;
principal independently re-derived with an explicit random-selection null.

## RESULT — a REAL but MODEST predictive signal; NOT deflation-certified → LEAD, not deployable.
- **The ML signal is genuine and the best the program has produced.** Logistic and reach-regression BOTH:
  sealed AUC ~0.64-0.65 with a TINY train→sealed gap (0.02-0.04 — NOT overfit, the AUC holds out of sample),
  sealed selected mean-R ~0.49-0.53 vs baseline 0.227 (~2.1-2.3×), R-per-bar ~0.058-0.060 vs 0.020 (~3×),
  win-rate ~0.51-0.53 vs 0.42. Two independent model families AGREE. (Prior program ML was AUC 0.53 ≈ random;
  this is a real step up.) Principal re-derivation: sealed AUC 0.642, selected n=71 mean-R 0.475.
- **But the dollar lift does NOT survive deflation.** Principal RANDOM-SELECTION null (does the model select
  better than picking n random sealed trades?): p = **0.038** — significant unadjusted, but the workflow tried
  73 variants → the deflated bar (Bonferroni ~0.0007; verifier block-perm/bootstrap) is far below 0.038. Both
  ML verdicts = MARGINAL / within-noise; confluence-stack = leak/overfit; **GBM correctly self-failed**
  (train AUC 0.985 vs sealed 0.514 — textbook overfit, not claimed). CONFIRMED_REAL = [].
- **Why marginal not real:** the selected sealed sample is small (n~71-80) and the metals R is fat-tailed
  (high variance) → the mean-R CI is wide; and 73 trials raise the deflation bar. The AUC signal is real; the
  *dollar* certification needs more sample or fewer trials.

## HONEST VERDICT + PATH (the one hard rule held — nothing thin shipped)
- ML trade-selection is a **promising real-but-marginal LEAD**, NOT a deployable gate. Do not hard-gate live
  trades on it. The machine refused to certify a fat-tail-noisy dollar lift even with a real AUC — correct.
- **Paths to certify (clear and live-aligned):** (1) LIVE-FORWARD — the live metals trades are virgin sealed
  data; evaluate the frozen reach-predictor's predictions on them (pre-register it now, no re-fit). (2) A
  SIMPLER model (2-4 features → far lower trial budget → easier deflation), built on the prior that vol-regime
  + persistence + trend carry the signal. (3) COMBINE with the c67 vol-cap (the one REAL/deflation-surviving
  selection filter) — the ML may add orthogonal lift on top of the regime filter.
- **Convergence:** c67 (vol-cap regime filter, REAL) + c68 (ML reach AUC 0.64, real-but-marginal) point the
  same way — **trade selection by regime/quality is the real per-trade-edge lever**, modest and partly
  certified. It improves the SHARPE axis on the EXISTING edge (no new breadth needed). The deployable piece
  today is the vol-cap; the ML is the live-confirm extension.

## INFRASTRUCTURE BUILT (reusable)
`SELECTION_FEATURE_STORE.jsonl` (leak-free decision-bar features + reach/MFE/MAE labels for all 482 trades)
+ `sel_{logistic,shallow_tree,gbm,reach_regression,confluence_stack}.py`. This is the substrate for the
live-confirm selection layer and any future modeling.

**Files.** `SELECTION_FEATURE_STORE.jsonl`, `sel_*.py`, Workflow wf_3e2a6d48-f27.
