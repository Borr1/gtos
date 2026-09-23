# LLM Specialization Research Backlog

Date: 2026-05-10
Status: future research lane
Scope: GTOS model-specialization, fine-tuning, distillation, and eval design
Promotion posture: `NO_PROMOTION_VERDICT`

## Purpose

The owner raised a strategic question: instead of relying only on broad general-purpose frontier models for GTOS trade-decision analysis, should GTOS train, fine-tune, distill, or adapt a model specifically for its own trading decision use case?

This file preserves the idea as durable context so future agents do not rely on chat memory, and so the research does not stay boxed inside only the current NOFILL/CNR source-control lane.

## Honest Current View

LLM specialization is possible and worth researching, but it is not automatically a shortcut to a better trading agent.

The core bottleneck is not that a frontier model "knows useless things" such as web development. Broad model knowledge also provides reasoning, abstraction, instruction-following, language robustness, and anomaly detection. Fine-tuning usually changes behavior and task conditioning; it does not safely delete irrelevant knowledge.

The real bottleneck is whether GTOS has:

- clean source-safe input examples,
- non-leaky labels,
- audited decision traces,
- explicit no-trade / blocked / reject labels,
- sealed evaluation partitions,
- adversarial baselines,
- calibration and confidence checks,
- cost/latency/execution-readiness metrics,
- enough examples per class without duplicate denominator inflation.

Without those, a fine-tuned model can become faster and more confident at repeating historical mistakes.

## What Specialization Could Help

Useful possible roles:

- schema-valid, GTOS-native decision formatting;
- no-leak and source/as-of obedience;
- consistent blocker classification and exact next-question generation;
- cheap first-pass triage before frontier-model review;
- imitation of audited G12/G0 reasoning style;
- rejection filter or meta-labeling assistant;
- candidate explanation compression for downstream statistical models;
- synthetic training data reviewer, not synthetic truth generator;
- ensemble disagreement signal between frontier model, specialized LLM, and deterministic/ML baselines.

## What It Should Not Be Trusted To Do By Default

Do not assume specialization will:

- discover real price alpha from noisy labels by itself;
- replace sealed validation, robustness testing, or forward realism;
- make contaminated historical results valid;
- remove need for deterministic safety gates;
- produce broker-realized performance claims;
- outperform frontier models on deep reasoning without proof;
- improve live decisions before a separate promotion dossier exists.

## Candidate Routes

Future research may compare several routes:

1. Frontier-model prompt/tooling baseline.
   Keep current Sonnet/OpenAI-style model usage, but improve prompts, context retrieval, source contracts, and deterministic validators.

2. Closed-source supervised fine-tuning.
   Train a task-specific model on audited GTOS examples for formatting, decision consistency, blocker classification, and source-safe reasoning. Must check current vendor capabilities and costs at execution time.

3. Closed-source reinforcement fine-tuning or grader-based tuning.
   Use a programmable grader only after GTOS has a reliable eval harness. Useful for exact schema/no-leak/decision-policy adherence; dangerous if the grader encodes weak trading truth.

4. Open-source LoRA/QLoRA fine-tuning.
   Fine-tune a Qwen/Llama/DeepSeek-class model for local/private GTOS behavior. Useful for cost and privacy. Requires serving, GPU/CPU latency analysis, eval discipline, and comparison against frontier baselines.

5. Distillation.
   Use frontier-model G12/G0 reasoning as teacher traces for a smaller local model, but only when traces are audited and separated from validation labels.

6. Hybrid architecture.
   Use deterministic parsers and statistical/ML models for predictive signals, while a specialized LLM handles source-safe reasoning, explanation, triage, and exact blocker routing.

## Required Prerequisites Before Any Fine-Tune

A future `LLM_SPECIALIZATION_FEASIBILITY` route must first build:

- dataset inventory separating training, development, sealed evaluation, stress, forward, and contaminated examples;
- input/output schema with explicit allowed fields and forbidden fields;
- label provenance ledger showing whether labels came from G12/G0 audits, deterministic source-control rules, quarantined results, broker actuals, synthetic path labels, or human decisions;
- duplicate-key and duplicate-group policy;
- class balance report, including no-trade, blocked, reject, accepted, wrong-side, no-fill, and source-impossible cases;
- no-leak scan that proves no post-outcome or hidden path labels enter inputs;
- baseline eval harness against current frontier model prompting, deterministic validators, and simple statistical/ML baselines;
- sealed evaluation slices never used for training or prompt/model selection;
- cost/latency/reliability budget;
- failure taxonomy for hallucination, overconfidence, schema drift, leakage, false positives, and missed valid trades.

## Minimum Evaluation Standard

Any specialized model must beat or complement the baseline on sealed data, not just in-sample examples.

Metrics should include:

- schema validity;
- no-leak compliance;
- exact blocker classification accuracy;
- accepted/rejected decision agreement with audited labels;
- false accept rate on forbidden/leaky examples;
- false reject rate on valid examples;
- calibration and uncertainty quality;
- stability under prompt/input perturbation;
- robustness across symbol/session/regime/time splits;
- latency and cost;
- degradation on forward shadow rows.

The model may be useful even if it does not directly predict R, but the role must be explicit.

## Stop Conditions

Stop or downgrade the route if:

- labels are too contaminated for training;
- sealed eval cannot be built;
- model gains are only formatting gains and not worth operational complexity;
- specialized model overfits, becomes overconfident, or misses no-leak rules;
- serving complexity or latency is worse than the API baseline;
- performance disappears under symbol/session/regime holdouts.

## Future Prompt Name

Suggested future route:

`LLM_SPECIALIZATION_FEASIBILITY_AND_EVAL_DATASET_DESIGN`

This route should run only after the current source/control and sealed-partition foundations are strong enough to provide audited examples and clean eval splits. It should remain research-only and preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

No specialized model may affect live trading decisions without a separate promotion dossier and owner approval.
