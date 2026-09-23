# THE BREAKTHROUGH FRAMEWORK — how to think / plan / find them (distilled from cycle 69)

## The principle
The deployed edge is a STATIC policy applied to a HETEROGENEOUS, PARTLY-PREDICTABLE population of trades.
Every trade gets the same stop / target / size, but trades differ enormously (a few run 4–14R, most don't)
AND that difference is forecastable from decision-bar information. c69's breakthrough: stop optimizing one
rule for the average trade — predict each trade's latent type ŝ(x) and use a CONDITIONAL policy a*(ŝ).

Formally: the static book maximizes E[R | take]. The real structure is R = f(latent state s, action a) with
s partly observable at the decision bar via features x. The win is the contextual policy a*(ŝ(x)). The static
book leaves money at EVERY static parameter, for EVERY predictable latent variable. c69 proved the tail
(reach) is predictable (sealed AUC 0.67) and conditioning the TARGET on it (ride-deep) ~2× sealed mean-R.

## The generative map: breakthroughs = {static parameter} × {predictable latent variable}
STATIC PARAMETERS (currently fixed, one-size-fits-all):
  target · stop · SIZE · entry-timing · hold/time-stop · whether-to-take · which-sleeve-weight
PREDICTABLE LATENT VARIABLES (forecastable at decision bar):
  reach/MFE-magnitude (c69: AUC 0.67) · adverse-path/MAE · time-to-target/speed · win-prob · regime ·
  the JOINT (reach, MAE, time) distribution
Each cell is a candidate. Prioritized by expected value:
  1. **SIZE ∝ predicted edge** (reach×win) — the biggest RETURN lever; turns c69's 4× oracle into a sizing
     multiplier; Kelly-by-predicted-edge, DD-governed. (Re-validate −5% daily on the sized distribution.)
  2. **Adaptive target = predicted MFE** — set each trade's target to its predicted reach (sharper than one
     fixed 6R ride; a predicted-8R trade gets 8R, a predicted-3R gets 3R).
  3. **Stop ∝ predicted MAE** — tighter where the predicted adverse path is small (c66: runner pre-peak MAE
     p90 ~0.9R), wider where choppy. Improves R:R without cutting runners.
  4. **us_equity tail-ride** — the c69 breakthrough on the Donchian sleeve (trends run far → likely bigger).
     Harness eq_stream() is built.
  5. **Joint path-outcome model** — predict (reach, MAE, time) jointly → analytically-optimal geometry+size
     per trade. The deepest version = "the ultimate system".
  6. **Velocity** — condition hold/time-stop on predicted speed → cut slow trades → R/hour up (compounding).
  7. **Mechanical follow/avoid/mixed** — reliability-weighted confluence veto (whether-to-take), the moonshot
     concept validated mechanically.
FORCE MULTIPLIERS: (a) STACK the validated conditional policies into one fully-adaptive book; (b) APPLY across
every sleeve; (c) the prediction layer itself goes deeper (richer quant features, better models, the joint).

## How to find them (the discipline — why c69 is trustworthy and most candidates won't be)
Each cell is a HYPOTHESIS. Most are mirages (the machine rejected 8/10 in c67/c68). The two-part test c69
passed, applied to every candidate:
  (1) Is the latent variable genuinely predictable OUT-OF-SAMPLE? (sealed AUC, small train→sealed gap.)
  (2) Does conditioning the policy on it BEAT the static policy on the SEALED slice — deflated by the trial
      budget, robust to drop-top, positive across sub-periods, beating the right null (random-action)?
Only survivors are breakthroughs. The ORACLE (perfect-prediction ceiling) is the scout: compute it first — if
even perfect knowledge barely helps, skip the cell; if the ceiling is large (c69 oracle = 4.2×), the cell is
worth a real predictor. Expect a MINORITY to survive — but several strong priors (size-by-edge, adaptive-
target) likely do.

## The search plan (Workflows, leak-disciplined, principal re-derives winners)
PHASE A — PERCEPTION: build one shared, rich, leak-free prediction layer that forecasts reach, MAE, time
  (and ideally the joint) from decision-bar quant features (vol-expansion, persistence, structure, regime,
  microstructure). This is the system's "perception"; every conditional policy consumes it.
PHASE B — CONDITIONAL POLICIES: for each high-ceiling cell, compute the oracle, then fit the conditional
  policy on TRAIN, validate on SEALED, deflate, robustness-check. Keep survivors.
PHASE C — STACK + SIZE + GOVERN: combine survivors into the adaptive book; re-validate sizing/DD on the new
  return distribution (DD-defense governor); confirm the −5% daily wall holds.
PHASE D — GENERALIZE: apply across sleeves (us_equity harness ready); live-confirm the predictors on virgin
  trades (frozen, pre-registered).
THE ONE HARD RULE throughout: train→sealed, trial-budget-deflated, principal re-derives every load-bearing
winner. Aggression in the SEARCH (many hypotheses, much compute); ruthlessness in the VALIDATION.

## Why this is the path to the ultimate system (Sharpe × breadth → safe dial)
Breadth on MT5 is cost-capped (closed). The OTHER axis — per-trade edge QUALITY — is wide open: every static
parameter made adaptive to a predicted latent variable raises Sharpe on the EXISTING edge, and size-by-
predicted-edge converts that Sharpe into return at controlled ruin (the safe dial). The ultimate system is the
fully-adaptive, prediction-conditioned, ruin-governed policy — found one validated cell at a time.
