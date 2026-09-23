# Data And Approval Gate Reclassification - 2026-05-03

Status: research/program-control clarification
Promotion posture: `NO_PROMOTION_VERDICT`

## Purpose

This note answers three owner questions:

1. Does Sierra Chart plus Databento solve the external data blockers?
2. Which approval-gated items actually create AI/API cost versus local compute/logging only?
3. How many open items are blocked by missing forward/live/unseen data versus how many can be pursued without that data?

Counts below are a primary-blocker classification of the current `research/program_control/MASTER_RESEARCH_QUEUE_STATE_2026-05-03.json`. Some items have mixed blockers; this note assigns each item to the dominant blocker that controls the next action.

## Queue Count Reclassification

Current non-terminal queue items:

| Scope | Count |
|---|---:|
| All non-terminal items (`BLOCKED`, `DEFERRED`, `FILED`, discovery candidates) | `112` |
| Strict `BLOCKED_WITH_REASON` + `DEFERRED_WITH_TRIGGER` only | `99` |

All non-terminal items by primary blocker:

| Primary blocker class | Count | Meaning |
|---|---:|---|
| `external_source_or_history` | `44` | Needs new historical/source/feed data or a better substrate. Sierra/Databento can help some, not all. |
| `forward_live_or_unseen_evidence` | `34` | Needs future/unseen GTOS rows, actual broker-R, live/shadow outcomes, larger cohort, or capacity/live-stream evidence. Historical data alone cannot settle it. |
| `approval_or_code_shadow` | `20` | Can be implemented or prototyped without forward/live data if CEO approves the code/behavior boundary. |
| `compute_research_no_forward` | `7` | Can be pursued with local compute, literature, harnesses, or current-web research; no live/forward data is the blocker. |
| `operator_admin` | `2` | Needs Windows/operator action, not research data. |
| `parked_low_value_or_ceo_request` | `5` | Technically researchable, but not currently useful unless CEO explicitly wants it. Includes owner-parked Component 3B debate because of extra AI/API cost. |

Strict blocked/deferred items only:

| Primary blocker class | Count |
|---|---:|
| `external_source_or_history` | `44` |
| `forward_live_or_unseen_evidence` | `31` |
| `approval_or_code_shadow` | `10` |
| `compute_research_no_forward` | `7` |
| `operator_admin` | `2` |
| `parked_low_value_or_ceo_request` | `5` |

Direct answer:

- `31` strict blocked/deferred items require forward/live/unseen evidence.
- `44` strict blocked/deferred items require external/historical/source data.
- `24` strict blocked/deferred items do not require forward/live data if we include approval/code-shadow work, compute/literature work, operator/admin work, and parked CEO-request work.
- If filed-for-approval items are included, `34` non-terminal items do not require forward/live data: `20` approval/code-shadow + `7` compute/literature + `2` operator/admin + `5` parked CEO-request.
- Practical near-term actionable count is lower: exclude the `5` parked items unless the CEO explicitly reopens them.

## Sierra Chart And Databento Do Not Solve Everything

Sierra Chart and Databento materially reduce the data problem, but they do not erase it.

They help most where the blocker is futures proxy microstructure:

| Blocker family | Sierra/Databento impact |
|---|---|
| `D-1`, `K-1`, `K-2`, `K-3` volume/dollar/imbalance bars | Materially helps for CME futures proxies; still not true CFD/spot FX volume. |
| `D-2` pre-2024 tick/depth history | Databento can help for CME futures proxies; Sierra historical tick categories help futures, but Sierra depth history is recent and forward capture is the main full-depth path. |
| `D-12` pre-2022/all-symbol history | Partially helps for CME futures proxies; does not solve all GTOS CFD/FX/broker-symbol history. |
| `X-1`, `X-2`, `X-3`, `E-3` trade/imbalance/meta-order proxies | Helps for futures proxy signed trades/depth; does not create true centralized spot FX or broker-CFD parent-order flow. |
| `E-2`, `P-7`, `P-9`, `X-4`, `U-6` depth/tick-count/Hawkes/trade-count substrate | Helps through forward depth capture and targeted historical futures pulls. |
| `P1-F` USDJPY/6J price-transfer follow-up | Databento/Sierra can help if the test is pre-registered and cost-capped. |

They do not solve these families:

| Blocker family | Why not solved by Sierra/Databento |
|---|---|
| `A-2` VIX1D/VIX9D and `A-3`/`V-2` VRP | Needs options/volatility-index/implied-variance sources and no-leak conventions, not just futures depth. |
| `D-4` FX COT, `D-5` KMW FX-fix, `D-7`/`U-8` H-K-M, `D-8` BIS, `D-9` Fed research feed | Macro/source/licensing problems, not tick/depth problems. |
| `A-8`/`U-12` real-gold percentile | Needs CPI/PCE deflator construction and publication-time metadata. |
| `E-4` retail-flow/crowding and `C-2` counterparty stop placement | Needs retail-flow, broker sentiment, or counterparty positioning. Futures depth is not the same object. |
| V2b/V3 promotion blockers | Need unseen GTOS rows and pending-limit lifecycle truth, not just more historical depth. |
| Account-dollar truth | Needs MT5 account-history/deal reconciliation, not Sierra/Databento. |

Practical conclusion:

- Sierra/Databento should be treated as the best path for orderflow, futures proxy, and microstructure substrate work.
- They are not a universal replacement for broker execution truth, live GTOS forward validation, macro/options sources, retail crowding data, or prop-account PnL truth.

## Sierra Historical Data Boundary

Based on the current Sierra research artifact:

- The owner has Service Package 12, so the near-term blocker is not the Sierra package tier.
- Sierra is useful for forward/recent depth capture and parser-readable `.depth` files.
- Sierra delayed `NQM26-CME` depth is already proven parser-readable from weekend samples, but the weekend sample is market-closed constrained.
- Sierra full-depth conclusions need active-session capture and Databento parity.
- Sierra is not a long-horizon historical MBO replacement. The current research record says MBO requires Package 12, only orders with quantity `>=3` are transmitted/displayed, and there is no support for recording MBO data or downloading historical MBO data.
- Sierra Forex/CFD historical data is indicative quote data; it does not provide centralized true volume or depth.
- Sierra CME historical categories help futures proxy research, but depth retention is recent, and forward capture is the cleaner full-depth path.

## Approval Items And API Cost

| Item | Main change | New AI/API cost? | Primary risk | Recommended posture |
|---|---|---:|---|---|
| `L-6` / `O-6` token-usage logger | Logs existing API calls with cost/latency/call id. | `No new calls`; tiny local write/compute. | Touches `primary_analyzer.py`; must fail open. | Approve first. Low risk, high observability value. |
| `P2-I` pending-limit lifecycle telemetry | Logs pending-intent checks and outcomes. | `No`. Local JSONL only. | Touches `execution.py` / `orchestrator.py`; must not alter trade branch. | Approve early. It unlocks V2b/V3/orderflow label truth. |
| `S-1` K55 shadow harness | Local ML inference/logging parallel to AI. | Usually `No AI API`; local compute only unless design adds AI calls. | Touches orchestrator/config live path; could add latency if badly wired. | Approve after target refresh as shadow-only/off-by-default/fail-open. |
| `A-16` DCC/cDCC/Block-DECO | Research prototype or risk-model replacement. | `No`. Local compute. | Live replacement changes risk behavior. | Approve research prototype only; no live replacement. |
| `B-5` AI grounding bundle | Bundle around L-1/L-2/L-8 while L-4 is parked. | `Possibly yes`; depends on tool-use design. | Alters Component 3A behavior if wired. | Approve only as cost-capped shadow harness after L-6 telemetry. |
| `X-7` cascade prompt rebuild | Rebuild/test prompt cascade. | `Yes` if batch A/B uses AI calls; can be expensive. | Prompt behavior change; V4/cascade was shelved. | Defer or run tiny shadow A/B only with explicit budget. |
| `L-1` tool-use grounding | Wire AI tools into PrimaryAnalyzer. | `Low to medium`; local tools are free, but extra AI tool rounds can add calls/tokens. | Alters Component 3A behavior. | Shadow-only, capped, after L-6 logger. |
| `L-2` market-state tool inventory | Recent outcome/session-vol tool lookup. | `Low`; mostly local lookup, possible extra tokens. | Alters context given to AI. | Shadow-only, no decision impact. |
| `L-4` Component 3B debate | Bull/Bear/Judge AI flow. | `Yes, high relative`; likely multiple AI calls per candidate. | More token spend and AI-flow change. | Owner-parked 2026-05-03. Keep dormant; no near-term API spend. |
| `L-3` Reflexion/adaptive loop | Post-trade feedback/adaptation. | `Maybe`; LLM reflections cost per closed trade unless local-only. | Live adaptation can create drift. | Shadow-only; no live learning. |

## If It Is Additive And Low Harm, Why Not Do It?

The correct answer is: we should usually do it, but with a hard contract.

Additive telemetry/shadow work is worth approving when it is:

1. fail-open,
2. append-only,
3. no decision impact,
4. no prompt/risk/execution behavior change,
5. bounded latency,
6. bounded disk growth,
7. tested against write failure,
8. disabled or shadow-only by config,
9. cost-capped if it calls an AI API.

Under that rule, the best "why not do it now?" approvals are:

1. `L-6/O-6` token-usage logging.
2. `P2-I` pending-limit lifecycle telemetry.
3. MT5 account-history reconciliation / PnL truth verifier.
4. Sierra active-session depth capture and Databento parity.
5. `S-1` K55 shadow scaffold after target refresh.
6. Research-only risk prototypes (`A-16`, `R-1`, `R-3`, `R-4`) with no live risk hook.

The items that should still be cost-gated are:

1. `X-7` prompt/cascade A/B, because batch testing can burn API budget.
2. `L-1`/`L-2`/`B-5` grounding, because tool-use may add tokens/calls unless carefully shadowed.
3. `L-3` Reflexion, because adaptive AI loops can create drift even if per-trade cost is small.
4. `L-4` debate is not just cost-gated; it is parked by owner decision until explicitly reopened.

## Bottom Line

Sierra plus Databento opens a lot of room, especially for CME futures proxy microstructure and forward/recent depth capture. It does not eliminate the need for:

- live GTOS forward rows,
- broker/account-history reconciliation,
- pending-limit lifecycle telemetry,
- macro/options/retail-flow sources,
- explicit approval for behavior-changing AI/risk paths.

The strongest immediate approval path is not a risky live change. It is additive observability:

1. token usage,
2. pending-limit lifecycle,
3. account-history truth,
4. Sierra/Databento parity,
5. K55 shadow-only logging.

Those are the highest-value no-promotion/no-decision-impact items because they make future ideas easier to accept or reject with real evidence.
