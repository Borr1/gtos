# AI, Orderflow, And Execution Context

Date: 2026-05-03
Status: discussion context
Promotion posture: NO_PROMOTION_VERDICT
Scope: research direction, system interpretation, execution-design context

## Purpose

This note preserves an important owner/Codex discussion that should not live only in chat memory. It is not a strict plan, timeline, rulebook, or promotion decision. Future sessions should treat it as context for how the owner is thinking about AI, mechanical structure, orderflow/depth, execution, data capture, and the balance between speed and proof.

The central theme is:

> Build and test aggressively, especially where the change is additive or shadow-only; promote live behavior only when the challenger is clearly better than the current live system under a fair comparison, with rollback controls.

## Owner Concerns Captured

The owner raised several connected concerns:

- GTOS now has a large amount of market data and live-system information that a normal retail trader does not have, including MT5 live data, internal market-state logs, candidate logs, tick capture, Sierra Chart Package 12 data/depth capture, Databento paths, canaries, shadow logs, and replay infrastructure.
- The question is whether this is becoming hedge-fund-like in process and whether the system is actually utilizing the data well enough.
- The owner is concerned that if mechanical structure, data capture, opportunity finding, execution, and risk management keep improving, the AI API call could become the weakest part of the system.
- The owner wants AI and canary/API calls understood clearly: which calls are safety checks, which are candidate-selection calls, and whether AI is adding value or suppressing good opportunities.
- The owner does not want the research program to become too conservative by waiting arbitrary long periods when obvious improvements are being logged.
- At the same time, the owner wants real proof, real numbers, and no artifacted claims.
- The owner specifically asked whether orderflow/depth features, if they help timing and quality, mean the system should stop thinking only in candle-close terms and start considering limit orders, market orders, event-driven triggers, entry aborts, and exits.

## Current System Interpretation

GTOS is not a full hedge-fund platform in the institutional sense. It does not have institutional capital, co-location, direct exchange execution infrastructure, a staffed risk committee, dedicated data-engineering teams, or a fully mature OMS/EMS stack.

However, relative to normal retail trading, the process is already far above ordinary discretionary retail:

- structured market-state extraction,
- deterministic pre-AI gates,
- AI candidate evaluation,
- deterministic L2 verification,
- canary drift checks,
- shadow logs,
- replay infrastructure,
- candidate-feature logs,
- tick capture,
- slippage logging,
- Sierra depth capture,
- targeted Databento orderflow work,
- explicit promotion gates and decay monitoring.

The important nuance is that the data stack is currently ahead of the live decision stack. The system is collecting and preparing data that is not yet fully promoted into live trading behavior. Sierra/depth/orderflow should be treated as a major research and forward-shadow opportunity, not as already-realized live edge.

## Mechanical Structure Versus AI

The mechanical system is not just a simple rules engine. It constructs the structured market-state object that the AI sees: bias, structure, order blocks, FVGs, breakers, liquidity, displacement, POIs, and framework-specific context.

The AI call is also not merely a passive confirmation layer in current live behavior. It is a selectivity layer:

- deterministic gates can skip impossible/no-bias/no-POI cases before the AI call,
- the AI receives the structured market state and emits CANDIDATE or NO_TRADE,
- if AI emits NO_TRADE, the live pipeline stops before L2/execution,
- if AI emits CANDIDATE, deterministic L2 then verifies the AI's claim against source market-state data,
- post-AI guards and L2 checks protect against malformed, degenerate, wrong-side, or inconsistent AI outputs.

This means AI can help by filtering weak mechanical opportunities, but it can also suppress opportunities that a stronger mechanical system might have taken. That concern is valid and should be measured directly rather than assumed away.

Canary calls are different. The canary is not a per-candidate trading decision. It is model/prompt drift protection using frozen fixtures. Its purpose is to detect whether the live model/prompt combination still behaves within expected bounds.

## Current Execution Reality

The live system does not simply enter every accepted setup by market order at candle close.

Current behavior is closer to:

1. M15 candle closes.
2. Market state is built.
3. Pre-AI gates run.
4. AI emits CANDIDATE or NO_TRADE.
5. L2 and safety gates verify the CANDIDATE.
6. The system places a local pending limit intent.
7. The orchestrator checks later candles to see whether the limit price was touched.
8. If triggered and still viable, the execution engine sends an MT5 market deal at current bid/ask.

Important nuance: the current pending-limit mechanism is local/polled, not a native MT5 pending order. It is candle-level polling, not true tick/depth-event execution.

This creates a clear research opening: orderflow/depth can potentially improve not only signal selection, but also execution quality.

## What Orderflow/Depth Could Enable

Orderflow/depth should not be framed only as another yes/no signal. It may be most valuable as an execution-quality layer after a structural opportunity exists.

Potential execution modes to compare:

- Market on confirmation: use when momentum/displacement and liquidity conditions imply waiting for a pullback is more harmful than paying spread/slippage.
- Native broker limit: use when the setup's edge depends on price revisiting a specific OB/FVG/breaker zone and broker handling is acceptable.
- Local event-driven trigger: arm a structural setup, then enter only after tick/depth behavior confirms absorption, failed continuation, stack/pull change, aggressive-flow exhaustion, or liquidity reaction.
- No-fill/abort: skip a structurally valid opportunity when the tape shows bad fill quality, spread widening, adverse absorption, or liquidity vacuum.
- Exit management: use orderflow/depth to study whether to hold to J46-J49 targets, reduce, scratch, trail, or avoid holding through adverse liquidity behavior.

These are research candidates, not approved live behavior changes.

## Promotion Philosophy From The Discussion

This discussion should not be converted into a rigid timeline such as "two days" or "seven calendar days." The better framing is evidence maturity.

The posture should be:

- aggressive for data capture,
- aggressive for shadow logging,
- aggressive for replay and challenger generation,
- careful but not frozen for live execution changes,
- strict about numbers and attribution,
- willing to promote controlled changes when a challenger is clearly better than the current live system under fair forward/shadow comparison.

The owner does not want arbitrary multi-month waiting if a challenger is obviously outperforming in the right logs. At the same time, execution changes can damage live trading through missed fills, worse slippage, accidental outside-window fills, broker quirks, bad local polling, or spread behavior. Therefore promotion should scale with behavioral risk.

Suggested evidence tiers:

- Data/logging only: can be added aggressively if storage/compute are acceptable and there is no decision impact.
- Shadow challenger: can run aggressively beside live with no behavior impact.
- Risk-reducing filter: lower bar than trade-adding logic, but still needs forward/shadow proof and rollback.
- Entry-mode change: needs current-live baseline comparison, slippage/fill-quality telemetry, and limited rollout.
- Trade-adding logic: highest bar because it changes frequency and risk exposure.
- AI replacement or AI bypass: requires explicit AI-gated versus mechanical-only comparison, including missed winners, avoided losers, post-L2 rejects, malformed/guarded outputs, and execution quality.

No tier above is a hard rule. The point is to preserve the reasoning: promotion burden should match risk and reversibility.

## Specific Questions Future Research Should Answer

Future goal sessions should explicitly test these questions where data permits:

- Is AI adding expectancy versus the best mechanical-only challenger, or mainly reducing frequency?
- Are AI NO_TRADE decisions suppressing mechanical opportunities that later perform well?
- Are post-AI L2 rejects mostly catching true AI errors, or are they rejecting opportunities because of overly tight deterministic geometry?
- Which instruments benefit from orderflow/depth timing, and which do not?
- Does depth improve entry price, win rate, R multiple, drawdown, or only explain winners after the fact?
- Should entry mode vary by framework: OB retest, FVG fill, breaker re-entry?
- Should entry mode vary by instrument: NQ/MNQ, ES/MES, GC/MGC, SI, 6B, 6J, CL, ZN, etc.?
- Are native broker pending orders safer/better than current local pending intents for specific symbols?
- Does event-driven execution beat candle-level polling?
- Can orderflow identify when to cancel an armed setup before it fills?
- Can orderflow improve exits or J46-J49 target handling without reducing the strategy's right-tail value?
- How much of the apparent orderflow edge survives out-of-sample, forward shadow, and source/proxy transfer checks?

## Fresh Goal Session Instruction

Fresh research sessions should read this note with:

- `research/program_control/EXPANDED_OOS_DATA_RESEARCH_PROGRAM_AND_GOAL_PROMPT_2026-05-03.md`
- `research/program_control/SIERRA_CHARTBOOK_PREP_PLAN_2026-05-03.md`
- `research/program_control/SIERRA_DOWNLOAD_STATUS_AND_GOAL_SESSION_NOTES_2026-05-03.md`
- `.context/00_core/research_current_state.md`

This note should influence the questions asked and comparisons run. It should not be treated as prior proof that orderflow, mechanical-only trading, or AI bypass is better.

The practical goal is:

> Keep the current live system as the baseline, log challengers against it, and promote only when the challenger is demonstrably better in the right evidence class.

