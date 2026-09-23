# Orderflow Research Closure Synthesis

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Registration verdict: `DO_NOT_REGISTER_REPLAY_HYPOTHESIS_YET`

## Synthesis

Orderflow is worth keeping in the research program, but not as a promoted decision rule yet. The useful progress is that the broad "footprint / heatmap / orderflow inversion" idea has been converted into testable data constraints and symbol-specific hypotheses. The current evidence points most strongly to NAS100 adverse-selection forensics, not a universal orderflow edge.

This brought the system closer to the goal in one specific way: it improved market-state observability and exposed exactly what the system cannot know from MT5 CFD OHLCV alone. It did not yet produce a tradable filter, and it did not validate influencer-style claims that a permanent orderflow model can be inferred from screenshots or product descriptions.

The current truth is:

- Databento/CME data acquisition is workable for supported futures proxies.
- Trades data is useful, but it cannot reproduce heatmap/resting-liquidity behavior.
- MBP-10 is more relevant than MBP-1 for depth/ladder questions.
- NAS100 has a real loser-heavy cluster worth forward collection: 1 synthetic winner / 10 synthetic losers in current coverage.
- NAS100 is still not ready for replay registration: actual-R n=1, synthetic winner n=1, MBP-10 NAS100 candidate n=11.
- XAUUSD currently has no loser contrast and one LIMIT_PLACED telemetry anomaly; it cannot support an orderflow rule.
- MBO/order-identity data remains deferred; current MBP-10 evidence has not created a precise MBO-only question.
- Unsupported symbols are a real data constraint: the current candidate-feature log has 92 candidate rows on symbols without validated CME proxy mapping.

## Current Evidence Base

Primary current artifacts used:

| Artifact | What it answers |
|---|---|
| `ORDERFLOW_ACTUAL_OUTCOME_COVERAGE_AUDIT_OF_DATA_6_2026-05-02` | Separates synthetic/path labels from actual broker-R labels. |
| `ORDERFLOW_DEPTH_MBP1_FEATURE_DIAGNOSTIC_OF_DATA_8_2026-05-02` | Tests top-of-book depth diagnostics. |
| `ORDERFLOW_DEPTH_MBP10_FEATURE_DIAGNOSTIC_OF_DATA_10_2026-05-02` | Tests top-10 ladder-depth diagnostics. |
| `ORDERFLOW_LIMIT_INTENT_RECONCILIATION_AUDIT_OF_DATA_11_2026-05-02` | Resolves XAUUSD LIMIT_PLACED missing actual-R row as an internal intent telemetry gap. |
| `ORDERFLOW_NAS100_HYPOTHESIS_READINESS_AUDIT_OF_DATA_12_2026-05-02` | Corrected NAS100 registration gates and label accounting. |
| `ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_13_2026-05-02` | Converts open questions into disciplined collection priorities using the current shadow log. |
| `PENDING_LIMIT_INTENT_TELEMETRY_SPEC_V0_2026-05-02` | Defines the minimal forward telemetry needed to close future LIMIT_PLACED ambiguity. |

Staleness control:

- Handoffs were treated as history, not evidence.
- The forward collection plan read the current `shadow_logs/candidate_features_log.jsonl`: 518 rows.
- The existing event manifest was confirmed to have been built from 518 rows with available-end cap `2026-05-01T16:00:00+00:00`.
- Current rows after that cap: 6 total, 4 CANDIDATE rows.

## Answered Questions

| Question | Answer | Evidence |
|---|---|---|
| Are we still data-blocked at the vendor level? | Not for supported CME futures windows. We can pull trades, MBP-1, and targeted MBP-10 from Databento under cost caps. | Fetch plans show trades cached for 20 groups, MBP-1 fetched for 4 groups, MBP-10 fetched for 4 groups. |
| Do we have every bit of information needed now? | No. Vendor availability is not the same as usable labels, proxy mapping, and live execution telemetry. | Forward plan: 92 unsupported-symbol candidate rows; actual-R coverage 1/23 orderflow candidates. |
| Does trades data reproduce the footprint/heatmap idea? | No. Trades data gives aggressor flow, signed volume, profile/LVN proxies, and absorption proxies, but not resting liquidity. | Trades diagnostic ambiguity ledger. |
| Does MBP-1 solve the heatmap/depth problem? | Only partially. It gives top-of-book liquidity, not ladder pockets or walls away from touch. | MBP-1 diagnostic and schema ladder. |
| Does MBP-10 add value over MBP-1? | It is directionally more relevant for ladder-depth questions. NAS100 MBP-10 shows candidate/context total-depth delta `-28.0000` and winner/loser total-depth delta `34.0000`, but the winner side is n=1. | NAS100 readiness audit. |
| Can NAS100 be registered as a replay hypothesis now? | No. Failed gates: actual-R minimum, synthetic winner minimum, MBP-10 candidate minimum. | NAS100 readiness audit. |
| Did the XAUUSD LIMIT_PLACED row recover as actual R? | No. It was an internal pending intent with no broker fill evidence, later discarded. M1 path TP is counterfactual only. | Limit-intent reconciliation audit. |
| Should MBO be pulled now? | No. No registered MBP-10 question has failed in a way that requires order identity or queue position. | Forward collection plan and hypothesis registry. |
| Is the orderflow idea dead? | No. The broad version is not validated; the narrowed NAS100 failure-forensics and fill-quality branches remain useful. | Current label/depth diagnostics. |

## What Worked

1. Futures/CFD mapping became operational for XAUUSD, NAS100, and US30/US30_cash.
2. Timestamp alignment is good enough for tested 2026 windows when using the date-aware shift policy.
3. Trades features can be extracted and joined to GTOS event windows.
4. MBP-1 and MBP-10 can be fetched and sampled into repeatable depth features.
5. NAS100 failure forensics produced a coherent candidate direction: thin/depth conditions around failed CANDIDATE rows.
6. The methodology caught a label trap: `LIMIT_PLACED` is not the same thing as broker execution.
7. The current pipeline now separates synthetic/path labels, actual broker R, and fill/no-fill labels.

## What Did Not Work

1. No broad orderflow edge was validated.
2. No orderflow rule is promotion-ready.
3. No threshold can be frozen without threshold-mining risk.
4. Actual-R coverage is too sparse for execution-P&L claims.
5. XAUUSD is not analyzable as a continuation-quality hypothesis yet because current joined labels are 2 winners / 0 losers.
6. NAS100 has too few winners for stable winner-minus-loser feature direction.
7. Unsupported symbols cannot be safely pulled from futures feeds until proxy mapping is validated.
8. Historical live logs cannot fully explain the XAUUSD pending-intent no-trigger anomaly.

## Doors Opened

1. NAS100 adverse-selection filter research:
   - Scope: NAS100 CANDIDATE rows only.
   - Label policy: synthetic/path labels separated from actual broker R.
   - Data: trades + MBP-1 forward, MBP-10 targeted.
   - Status: `CANDIDATE_NOT_REGISTERED`.

2. Execution/fill-quality research:
   - Scope: LIMIT_PLACED rows.
   - Label policy: fill/no-fill, order-send success/failure, actual broker R.
   - Data need: pending-intent telemetry, not more historical Databento data.
   - Status: blocked until telemetry exists.

3. Proxy-mapping expansion:
   - Current unsupported candidate symbols: GBPJPY 23, GBPUSD 21, USDJPY 34, XAGUSD 14.
   - XAGUSD likely deserves first review because a futures proxy may be conceptually closer than FX-cross proxies, but it still requires a registered mapping/timestamp audit.

4. Depth-feature validation:
   - MBP-10 is the right next depth level for targeted questions.
   - MBO remains a later option only if a precise queue/order-identity question survives MBP-10.

## Doors Closed

1. Do not treat influencer product descriptions or screenshots as executable strategy rules.
2. Do not use MT5 CFD tick/volume alone as a substitute for CME footprint/depth.
3. Do not score `LIMIT_PLACED` as actual R without broker execution evidence.
4. Do not register a NAS100 replay hypothesis from the current selected failure cluster.
5. Do not pull broad MBO data now.
6. Do not collect futures orderflow for unsupported GTOS symbols before proxy validation.

## Ambiguity Ledger

- NAS100: current loser-side evidence is adequate for a clue, but winner-side evidence is too sparse.
- Actual R: many orderflow candidates are pre-execution rejects, so actual broker-R coverage will stay sparse unless the research question explicitly targets filled rows.
- Timestamp policy: tested windows support date-aware shifts, but November fallback and contract-roll behavior remain unvalidated.
- Futures/CFD basis: CME futures data improves market awareness, but it will never be identical to broker CFD prints, spreads, or fill path.
- LIMIT_PLACED telemetry: future rows need no-trigger check logs; the historical XAUUSD anomaly cannot be fully reconstructed.
- Unsupported symbols: proxy mapping can likely be expanded, but each symbol needs its own validation instead of assuming propagation.

## Open Questions

1. Does the NAS100 thin-depth failure signature persist in future, pre-declared candidate windows?
2. Can NAS100 collect enough winner labels without changing strategy parameters or mining thresholds?
3. Do actual broker fills eventually agree with synthetic/path labels, or does execution dominate the label difference?
4. Which unsupported symbol should be mapped next, and does its futures proxy actually track the broker CFD well enough?
5. Does MBP-10 add incremental signal after controlling by symbol, session, label type, and timestamp policy?
6. What is the minimum pending-intent telemetry needed to prevent future LIMIT_PLACED ambiguity?

## Next Steps

1. Follow `ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_13_2026-05-02`: NAS100 gets the next disciplined collection priority.
2. Do not register or replay NAS100 until the readiness gates are cleared or revised before looking at new data.
3. Keep XAUUSD continuation on watch only; wait for both winner and loser labels.
4. Draft and later seek explicit approval for fail-open pending-limit telemetry if live observability changes become allowed.
5. Choose one unsupported symbol for proxy-mapping validation before spending data credits on it.
6. Keep `NO_PROMOTION_VERDICT` until a registered, as-of, symbol-specific hypothesis passes sample-size and methodology gates.
