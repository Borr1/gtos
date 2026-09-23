# Astra V2 news and decision protocol — staged for implementation

This is a specification, not an existing endpoint or a live authorization. Preserve Nightly Decide's no-splice state until the supplied V2 is loaded through the owner ceremony. Keep the current timing policy and $150 unit during transport repair; measure economic policy changes separately.

## 1. Identity and immutable decision inputs

Every packet carries schema_version, packet_id, actor, account_login, namespace, magic, source_event_id, source_published_at_utc, first_received_at_utc, analyzed_at_utc, facts_hash, policy_version, scope and valid_until_utc. Times are timezone-aware UTC. Original source time is never replaced by receipt or resend time. A missing field is explicit unknown, not inferred "now". Windows-generated JSON uses canonical UTF-8 without BOM; readers accept UTF-8 BOM for compatibility, validate decoded JSON, and emit a parse-failure receipt rather than silently reporting empty data.

Use distinct types:

- **Event facts:** stable official release occurrence ID plus revision/source-post IDs; scheduled time, actual publication time, declared event class, affected instrument set and mapping version. Revisions supersede the same event, not create independent blackouts. A correction can extend a scheduled window only when the actual scheduled event changed, with provenance.
- **Candidate decision:** exact fire ID includes account, namespace, normalized broker symbol, sleeve, direction, decision-bar UTC and geometry hash. Event or book state relied upon is versioned. Legacy sleeve-day IDs remain search aliases only; they cannot carry a live veto to another fire.
- **Position action:** exact broker ticket plus original-contract hash, current broker position version, mechanism and expiry. Manage remains existing close/tighten authority with no widening or risk addition. A stale condition requires a new observation.
- **Close label:** append-only close/deal ID and policy epoch, exit cause, actor, authorization evidence and compliance classification. Labels are accepted even when no candidates/positions remain. They never become trading decisions.

Keep event facts independent of a slate. Keep candidate and position actions bound to the precise analyzed object. Include event_version, critical quote/spread state changes and contract/book version in the relevant judge fingerprint; do not wake on every unchanged quote.

## 2. Durable publication and receipts

Replace a single overwritable verdict.json with immutable packet files named by packet_id or a single transactional queue. Existing deployments can retain a compatibility adapter, but it must preserve analyzed state and expiry; it cannot rebind old reasoning to the latest fingerprint. Two producers never replace each other's packet. One resident desk consumer claims an immutable packet before parsing and records the exact bytes/hash parsed. Claim/replay is idempotent.

Receipts are separate states: RECEIVED → VALIDATED/REJECTED → COMMITTED → CONSUMED → broker ACK/FILL/CANCEL if applicable. Each has timestamp, packet_id, consumer_version, affected fire/order/ticket IDs and reason. "HTTP200", "wrote file", "applied" and "broker cancelled" are different claims. Failed flow/manage writes must not return applied=True; a partial write must be recorded as PARTIAL and reconciled before archiving as complete. Atomic replacement protects one file, not a multi-file transaction.

Critical event facts and current broker fills/contract defects have their own bounded queue; close labeling and historical harvest use a lower-priority queue. Dedupe duplicate current events; do not replay historical harvest into the live wake queue. Page one actionable delivery failure with backlog age, retry count and packet_id, and keep independent permitted writer flow alive.

## 3. Scope and expiry

| Decision | Identity and lifetime |
|---|---|
| Scheduled event exclusion | Exact event_id plus explicit affected symbols. Current strategy window is scheduled_utc−15min through scheduled_utc+60min. Its absolute end never moves because a headline is resent. |
| Unscheduled already-supported event class | Stable occurrence ID and accepted source time. Use the current +60min strategy policy from first accepted occurrence, never another 60 min from each application. A later duplicate is context only. |
| Microstructure15m re-entry restriction | Exact symbol/family rule and broker close time; absolute end close_time+15min. A retry doesn't restart the clock. New named fire after the restriction remains eligible. |
| Correlation judgment | Exact candidate fire and compared book/candidate-set versions. Default validity ends at the earliest of next book change, candidate invalidation, or analyzed_at+30s. Thirty seconds is an engineering freshness limit, not a new economic cooldown. The writer recomputes/revalidates before send. |
| Position manage | Exact ticket, contract and observed condition. Expiry appropriate to the condition; current execution code must revalidate the risk-reducing action and ownership immediately before broker request. No delayed automatic action based solely on an old red-P&L observation. |
| Macro picture | Context only; explicit as-of and invalidation. No trading HOLD without a currently authorized named mechanism. |

No wildcard ALL-scope from a model's generic "uncertain news" sentence. A global scope needs a reviewed policy mechanism and explicit instrument enumeration. Initially preserve the writer's current USD-risk mapping including its extra index set; its breadth is a research question, not an excuse to silently shrink or expand it.

## 4. Writer boundary

Before every main or frozen-intent broker send, read the local committed event/policy snapshot and the current time, validate account/namespace/magic, exact fire identity, original candidate level, expiry and geometry, and record event_version and checked_at. If the version changes before dispatch, reevaluate locally. There is no unbounded LLM wait and no automatic market chase.

At the known event boundary, the writer reconciles affected native pendings against broker state and requests cancellation where the current no-new-risk event policy applies. Persist order identity and response. Broker fills and cancels race: if the fill wins, emit RACE_FILL, attach the saved original contract, and continue the position's existing management law. Never call that position "cancelled" or retroactively close it solely because the veto arrived late.

Existing positions keep original SL, broker TP and the actually persisted sleeve time stop unless an authorized present container defect or owner ticket instruction applies. Red P&L plus event proximity is insufficient. Seats may alert; they do not trade directly.

At event expiry, automatically re-evaluate unexpired eligible candidates and their frozen levels under current cost/geometry constraints. No remint of spent tickets. This is the mechanism for preserving opportunity supply after a temporary exclusion.

## 5. Clocks and division of work

All execution event times are UTC. Display ICT separately. Broker price timestamps have verified broker-clock conversion. Account daily-loss accounting follows the configured FTMO account's Prague reset and initial-account rules; the strategy's internal buffer is separately named. Never use a fixed UTC reset as a year-round substitute for Prague time.

WATCH refreshes the next14-day official event spine before each trading day and on official revisions; it confirms coverage rather than retyping dates into multiple conflicting files. For each scheduled event, local code prepares T−45 context wake, T−15 exclusion/cancel, release observation, and T+60 current-policy expiry. Time-sensitive boundaries execute locally even if Grok is busy or unavailable. T−45 prompts do not themselves change positions.

CHAIR receives candidate context before send where available, fills, closes, contract differences, event changes and actual action failures. No generic six-minute intellectual work quota. An hourly health reconcile plus session-open context remains a backstop; health proof does not mean mandatory owner chatter. WATCH owns the single Walter ingress, with a checkpointed gap-recovery route if the existing connector supports it. No second filtered-stream socket or re-fetch of the same post on every sit.

## 6. Test and measure

Engineering targets: local event commit→admission visibility p99≤1s; ingress receipt→commit p99≤5s for already-supported event facts. These are proposed service objectives to test on captured peak load, not observed guarantees. Capture external source publication→ingress separately. Report percentiles and maxima, losses/retries, malformed messages, slate mismatch, expired decisions, overwrite prevention, broker cancel failures and race fills.

Economic scorecard per event/family: all eligible candidate fires; submitted, cancelled, filled and rejected subsets; slippage/spread; hold-to-original-contract result; avoided losers; forgone winners; opportunity cost; unknown tick coverage; overlapping-event clusters. Compare current T+60 against preregistered shorter/conditioned alternatives on identical evidence, with an untouched later slice and day/event-blocked uncertainty. Do not infer alpha from process latency improvement alone.

## 7. Capability activation

Release only after tests prove both protective behavior and allowed printing: unaffected symbols continue, valid 15m re-entry remains eligible, duplicate headlines do not extend exclusions, post-fill correlation cannot leak to another fire, close labels survive empty slate, partial-write failures cannot claim completion, and startup preserves each live ticket's entry/orig/TP/time contract without synthetic management.

No remint is needed for the protocol on existing tags. Writer-consumer changes need a writer restart; desk/watcher changes need only their own processes. Persist and verify original contracts before the owner-controlled load. CHAIR/WATCH prompts below become active only when their referenced local capability receipt exists.
