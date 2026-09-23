# Static-Limit Adaptive-Execution Gap - Live Intelligence

Date: 2026-05-13
Status: `URGENT_RESEARCH_EXECUTION_DESIGN_DOSSIER_OPENED`
Promotion verdict: `NO_PROMOTION_VERDICT`
Trading behavior impact: none

## Why This Exists

The operator flagged a recurring live failure mode: GTOS identifies a good structural level, price reacts from or near that level, and the system remains out because the execution path is a static exact internal limit touch. This is not isolated frustration. It is now recorded as a live-intelligence pattern family:

`STATIC_LIMIT_ADAPTIVE_EXECUTION_GAP`

No live trading behavior is changed by this note. It exists to force near-term research/design work instead of treating each missed move as a separate anecdote.

## 2026-05-13 XAGUSD Evidence

Active internal intent:

- Candidate: `XAGUSD_2026-05-13T10:30:00+00:00`
- Intent: `lim_XAGUSD_2026-05-13_103030`
- Side: `LONG`
- Entry: `86.571`
- Stop: `85.986`
- TP1: `87.449`
- Mode: `INTERNAL_CANDLE_POLLED_INTENT`
- Broker pending order created: `false`
- Order send attempted: `false`

Tick evidence from `data/ticks/XAGUSD/2026-05-13.parquet`, reviewed from `2026-05-13T10:30:31.060000+00:00` to `2026-05-13T11:13:45.962000+00:00`:

- Rows reviewed: `6212`
- Bid touched entry: `false`
- Ask touched entry: `false`
- Nearest bid: `86.584` at `2026-05-13T11:06:16.355000+00:00`
- Bid miss distance: `0.013`
- Nearest ask: `86.656` at same timestamp
- Ask miss distance: `0.085`
- Median spread: `0.056`
- Max bid after intent: `86.966`
- Max bid move from entry: `0.395`

Interpretation boundary: this is a bid-side near miss, not an ask-side fill. A broker buy limit at `86.571` would not have filled on this tick evidence. The issue is not that GTOS ignored a literal fill. The issue is that GTOS has no adaptive participation logic after a validated zone reaction.

## 2026-05-13 XAGUSD Post-Cancel Touch Evidence

Later review showed a second, distinct execution failure mode on the same intent.

GTOS cancelled `lim_XAGUSD_2026-05-13_103030` at `2026-05-13T11:45:31.312411+00:00` with:

- Lifecycle state: `cancelled_target_reached_without_fill`
- Reason: `target_reached_without_entry_touch`
- Checked candle: `2026-05-13T11:30:00+00:00`
- Candle high: `87.518`
- TP1: `87.449`
- Candle low: `86.987`
- Entry: `86.571`

So, by current code, the internal intent was cleared because the M15 candle reached TP1 before the exact entry level. There was no native broker pending order left behind.

Tick evidence after that cancellation:

- Pending intent file present after cancellation: `false`
- MT5 XAGUSD orders after review: `[]`
- MT5 XAGUSD positions after review: `[]`
- First post-cancel bid touch below entry: `86.542` at `2026-05-13T12:20:56.048000+00:00`
- First post-cancel ask touch below entry: `86.568` at `2026-05-13T12:21:21.134000+00:00`
- Post-cancel minimum bid: `86.295` at `2026-05-13T12:30:15.957000+00:00`
- Post-cancel minimum ask: `86.383` at `2026-05-13T12:30:15.959000+00:00`

Interpretation boundary: this was no longer just a near miss. The ask later traded below the original long entry, but the system had already cancelled the internal intent after a TP-first candle. This exposes a separate research question: whether TP-first cancellation should permanently retire a still-valid structural level, or whether it should move the setup into a monitored re-entry/second-touch state.

Counterfactual status as of the later operator review:

- Review timestamp: approximately `2026-05-13T12:36:51Z`
- Latest parquet tick: bid `86.079`, ask `86.159`
- MT5 live tick near review: bid `86.048`, ask `86.127`
- Original entry: `86.571`
- Original SL: `85.986`
- Original TP1: `87.449`
- Post-cancel SL touched by bid/ask in reviewed tick window: `false`
- Counterfactual interpretation: a later adaptive/re-entry long from the original level would currently be in drawdown, not stopped. This must not be scored as a missed winner; it is an unresolved/adverse counterfactual path until SL/TP/exit state resolves.

## Same-Family Prior Intelligence

Existing rows in `shadow_logs/operator_market_intelligence.jsonl` already show the same family:

- `GBPJPY_2026-05-11T07:30:00+00:00`: price moved up before the long limit was reached.
- `US30_cash_2026-05-11T08:15:00+00:00`: price continued to TP1 area without first touching the long limit.
- `US30_cash_2026-05-11T08:15:00+00:00`: later classified as already beyond TP1 at decision time.
- `NAS100_2026-05-11T09:15:00+00:00`: already far beyond TP1 at decision time while the deep limit was untouched.
- `GBPJPY` 2026-05-12: operator saw price back near a prior level, but execution was blocked by no current valid system path and outside-KZ status.

## Existing Quant Anchor

`research/program_control/MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.md` already registered the broader missed-fill problem:

- Countable missed-fill-to-TP-area: `7 / 24 = 29.1667%`
- XAGUSD: `2 / 5 = 40%`
- US30_cash: `2 / 3 = 66.6667%`
- NAS100: `1 / 3 = 33.3333%`

That study correctly preserves `NO_PROMOTION_VERDICT`, but the live operator evidence says this must move from passive monitoring to an urgent execution-design dossier.

## Weekend Context: Data Gathered vs Live Utilization

The broader issue is not lack of raw intelligence. GTOS is already gathering multiple live/shadow streams that are directly relevant to missed static-limit entries. The gap is that most of this context is not consumed by the live decision/execution path.

Live path currently uses:

- OHLC candles converted into the MSO.
- Basic spread/data-quality fields.
- Deterministic pre-screen gates.
- Primary Analyzer output.
- L2 verification, permissions, correlation, and safety gates.
- Static internal pending-limit polling by exact entry touch.

Relevant intelligence gathered but not live-consumed for adaptive entry:

- `shadow_logs/operator_market_intelligence.jsonl` - operator-observed missed-entry / execution-context incidents.
- `shadow_logs/pending_limit_lifecycle.jsonl` - internal limit lifecycle, checked candle range, tick bid/ask when available, trigger state, and cancel/fill state.
- `shadow_logs/candidate_path_follow.jsonl` - whether price reached TP/SL areas without entry touch.
- `shadow_logs/candidate_ltf_path_order.jsonl` - lower-timeframe path ordering when available.
- `shadow_logs/missed_opportunity_shadow.jsonl` - near-miss and 0.25R-inside-limit observation-only comparators.
- `shadow_logs/prefill_delivery_path.jsonl` and `shadow_logs/prefill_delivery_path_audit.jsonl` - pre-fill delivery/reversal context, currently not scoreable enough for execution.
- `shadow_logs/shadow_observer_tick_enrichment.jsonl` and `data/ticks/{SYMBOL}/` - tick/bid/ask/spread/microstructure evidence.
- `research/program_control/MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.md` - aggregate missed-fill geometry.

Code/context anchors:

- `src/components/data_ingestion.py` attaches `raw_data["tick_features"]` fail-open, but this is additive and not part of the live entry/execution rule.
- `src/components/market_state.py` constructs the production MSO from OHLC/session/spread fields and does not carry `tick_features` into the decision object.
- `src/research_infra/missed_fill_opportunity_study.py` explicitly says it does not infer broker fills, call MT5, or change live behavior.
- `src/research_infra/live_shadow_gap_closure.py` records the 0.25R inside-limit comparator as observation-only and states it does not change execution.
- `src/research_infra/prefill_delivery_path_audit.py` currently emits `PREFILL_DELIVERY_REVERSAL_SCORER_NOT_IMPLEMENTED`.
- `src/components/pending_limit_lifecycle_logger.py` is observation-only; its rows do not influence trading code.

Weekend work should treat this as a closed-loop intelligence-utilization problem, not a request for more passive logging. The required output is a design/test path for converting the already-collected evidence into a shadow adaptive-entry scorer first, then an explicitly approved execution rule only if evidence supports it.

## Open Research/Design Questions

1. Should GTOS evaluate zone reaction instead of exact limit touch only?
2. Should near-miss distance be normalized by spread, tick size, ATR, and R distance?
3. Should a long internal intent have a secondary trigger when price comes within a configured band, rejects, and resumes in the trade direction?
4. Should the system distinguish bid-near-miss from ask-near-miss for buy entries?
5. Should stale/deep limits be suppressed earlier when the current market is already beyond TP1?
6. Should Telegram say `INTERNAL INTENT` instead of `LIMIT ORDER` until a broker order is actually sent?
7. What is the worst-case adverse selection if adaptive entry chases a reaction that is actually only a spread/quote artifact?
8. Should `target_reached_without_entry_touch` cancellation permanently kill the setup, or should it create a separate monitored re-entry state when price later returns to the original entry/zone?
9. Should later bid/ask-fillable retraces after a TP-first cancellation be scored as a distinct missed-execution class?

## Required Next Dossier

Create an urgent research/execution dossier for:

- adaptive entry after validated zone reaction,
- bid/ask-aware near-miss telemetry,
- proximity bands in R, spread, ATR, and tick units,
- live-vs-counterfactual separation,
- cost/slippage-aware entry if a reaction trigger fires,
- TP-first cancellation followed by later entry-touch handling,
- explicit rejection of any rule that merely chases price without structural confirmation.

No live execution, prompt, risk, or order-flow change should be made from this file alone. Any adaptive execution behavior requires explicit CEO approval and focused tests.

## NO_PROMOTION_VERDICT

This note is live intelligence and operations triage only. It does not validate a new entry model, does not prove profitability of adaptive entries, and does not authorize live behavior changes.
