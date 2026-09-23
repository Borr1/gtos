# AI-In-The-Loop Cost Control Research Plan

Date: 2026-05-10
Status: active research plan
Scope: historical replay, AI decision-layer evaluation, API spend control, surrogate/model-specialization backlog
Promotion posture: `NO_PROMOTION_VERDICT`

## Purpose

This document preserves the owner's strategic concern that brute-forcing paid AI API calls across every historical test would be wasteful and could damage runway before the system is profitable. It defines how GTOS should separate market-edge validation from AI decision-layer validation.

The core principle:

Do not use expensive API calls as the brute-force historical backtest engine. Use broad no-API historical replay for market learning, then use targeted, cached, budgeted AI calls only where the question is specifically about the AI layer's incremental value or production reliability.

## Evidence Classes

Separate these questions:

1. Market edge question:
   Does a mechanical candidate, level, path, lifecycle state, or hypothesis show source-safe positive expectancy or useful filtering behavior across historical regimes?

2. AI decision-value question:
   Does the production AI prompt/model improve selection versus the mechanical baseline?

3. AI reliability question:
   Does the AI return valid schema, stable reasoning, no hallucinated fields, consistent decisions, and acceptable behavior under prompt/model changes?

4. Execution realism question:
   Do live broker spreads, slippage, latency, order observability, fills, rejects, and operational errors match the assumptions?

Only questions 2 and 3 require paid AI calls by default. Question 1 should usually be answered with no-API historical replay first. Question 4 requires forward/live shadow or micro-live observability, not broad historical API spending.

## What Should Usually Be No-API

Run these at historical scale without paid AI calls unless a specific AI-layer question is being tested:

- mechanical candidate generation,
- OB/FVG/breaker/CNR/NOFILL/lifecycle studies,
- replay-as-of candidate and path testing,
- regime/session/kill-zone/symbol/timeframe sweeps,
- bull/bear/range and volatility-state splits,
- missed-opportunity inventories,
- first-passage/path outcome tests,
- duplicate and concentration diagnostics,
- source-control, no-leak, purge/embargo, and validation-partition work,
- baseline comparisons and adversarial placebo tests,
- failure forensics and negative-result anatomy.

Goal sessions and local tools should be used heavily here. This is where historical replay compresses time and reduces opportunity cost.

## When API Calls Are Worth Paying For

Use paid AI calls only when the target claim depends on the production AI decision layer:

- whether the production prompt says `CANDIDATE`, `REJECT`, or another schema decision,
- whether the AI accepts bad mechanical setups or rejects good mechanical setups,
- whether the AI adds incremental value after deterministic filters,
- whether the AI handles borderline, contradictory, or high-context setups better than rules,
- whether a prompt/model/config change improves or degrades decisions,
- whether output schema reliability, refusal rate, hallucination rate, or prompt stability is acceptable.

Never describe a no-API replay or goal-session judgment as original production AI intent unless it used the same source-safe prompt/input/model/config path or is explicitly labeled as replay/projection.

## Recommended Architecture

1. No-API broad replay engine.
   Build large historical candidate/path/result/control universes mechanically, source-hashed and as-of.

2. Stratified AI sample.
   Select a limited, representative API sample from the no-API universe: regimes, symbols, sessions, sides, winners, losers, no-fills, borderline cases, high-disagreement cases, high-R opportunities, and failure clusters.

3. AI delta audit.
   Compare mechanical baseline, mechanical plus deterministic filters, mechanical plus AI gate, AI false positives, AI false negatives, AI rejects that later worked, and AI accepts that later failed. The question is incremental value, not whether the AI sounds convincing.

4. Response cache.
   Every paid API response must be content-addressed by model, prompt hash, input hash, config hash, system/version metadata, and source data hash. Never pay twice for the same input/prompt/model/config tuple unless explicitly testing model drift.

5. Canary/regression suite.
   Keep a small fixed API canary set for prompt/model/schema reliability. This is separate from broad historical replay and should be cheap.

6. Surrogate/distillation path.
   If enough AI-labeled examples exist, research cheaper deterministic or local-model surrogates that approximate the AI gate. Use the API for audits, hard cases, and periodic calibration rather than brute-force evaluation.

7. Role decision.
   After the AI delta audit, decide whether AI should remain the primary decision gate, become a secondary reviewer, become a safety veto, become an explanation/monitoring layer, or be removed from trade selection.

## Budget And Sampling Rules

Future AI-in-loop prompts should define:

- maximum API budget before the run starts,
- target sample size and sample-selection rules,
- source universe from which rows are sampled,
- strata and minimum per-stratum counts,
- cache path and cache-hit policy,
- model/prompt/config/input hash binding,
- stop conditions if API failures, schema drift, or costs exceed limits,
- output artifacts separating API-derived decisions from no-API replay/projection labels.

Small samples are acceptable for reliability smoke tests and canary checks, but not for final edge claims. Large historical universes should be narrowed with source-safe sampling before API evaluation.

## Goal Session Role

Goal sessions may:

- build historical replay universes,
- inspect and audit mechanical candidates,
- create stratified sampling plans,
- analyze cached AI responses,
- compare AI decisions versus mechanical outcomes,
- produce failure forensics,
- monitor live/shadow logs,
- design surrogate datasets.

Goal sessions must not:

- impersonate production AI API results unless explicitly labeled as researcher annotation or replay/projection,
- use their own judgment as a drop-in replacement for the production prompt/model path,
- spend broad API budget without a pre-call manifest and owner-approved budget,
- convert API sample results into promotion claims without sealed validation, cost/slippage controls, duplicate controls, and a separate promotion dossier.

## Research Backlog Routes

Future route candidates:

- `AI_DECISION_VALUE_STRATIFIED_SAMPLE_DESIGN`
- `AI_RESPONSE_CACHE_AND_PROMPT_HASH_CONTROL_ROUTE`
- `NO_API_HISTORICAL_REPLAY_ENGINE_AND_MISSED_OPPORTUNITY_INVENTORY`
- `AI_DELTA_AUDIT_MECHANICAL_BASELINE_VS_PRODUCTION_PROMPT`
- `AI_SURROGATE_MODEL_FEASIBILITY_AND_LABEL_DATASET_DESIGN`
- `AI_CANARY_SCHEMA_STABILITY_AND_MODEL_DRIFT_MONITOR`

These are research/control routes only until a separate owner-approved prompt opens a validation or promotion dossier.

