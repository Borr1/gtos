# Forward Orderflow Collection Spec V0

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Purpose

This spec defines how to collect orderflow data going forward without turning the research program into uncontrolled data spend or post-hoc feature mining. It does not change live trading logic, prompts, parameters, or execution behavior.

## Instruments

| GTOS symbol | Primary futures proxy | Secondary proxy | Notes |
|---|---|---|---|
| XAUUSD | GC.v.0 | none | Best conceptual match: gold CFD derives from COMEX gold futures plus broker basis/spread. |
| NAS100 | NQ.v.0 | none | Best index-futures proxy for NAS100 CFD. |
| US30 / US30_cash | YM.v.0 | ES.v.0 | YM is primary; ES can be comparator for broad index-flow context. |

## Timestamp Policy

For the current 2026 MT5 export behavior:

- Before the March 2026 US DST transition weekend: shift MT5 timestamps by `-120` minutes to align to Databento UTC.
- From Monday 2026-03-09 onward in the tested sample: shift MT5 timestamps by `-180` minutes.
- Never choose the best timestamp shift per event in alpha testing.
- Every joined row must record the shift policy used.

Open validation still required:

- November DST fallback.
- Contract roll windows.
- Broker holiday/session anomalies.

## Collection Windows

For every CANDIDATE event selected for orderflow research:

| Window | Use |
|---|---|
| `pre60`: event close minus 60 minutes through event close | As-of market-state features only. |
| `event15`: event close minus 15 minutes through event close | As-of near-trigger features only. |
| `post15`: event close through event close plus 15 minutes | For forensics only; never as decision input. |
| `post60`: event close through event close plus 60 minutes | For forensics only; never as decision input. |

For structural context rows:

- Use the same windows.
- Context rows must be selected before outcome analysis whenever they are used for hypothesis testing.
- Context rows should be stratified by symbol, session, and date where possible.

## Schema Ladder

1. `trades`
   - Default required feed for candidate/orderflow research.
   - Answers: aggressor-side volume, signed volume, absorption proxy, event-price volume profile, LVN/HVN proximity.
   - Cannot answer: resting liquidity, full heatmap, queue churn.

2. `mbp-1`
   - Default cheap depth feed when depth is needed.
   - Answers: best bid/ask spread, top-of-book imbalance, top-of-book thinness.
   - Cannot answer: ladder pockets beyond best level, volume walls away from touch.

3. `mbp-10`
   - Targeted forensic feed only.
   - Answers: top-10 ladder depth, total-depth thinness, near/far liquidity ratio, bid/ask wall asymmetry.
   - Cannot answer: order identity, queue position, iceberg behavior, full MBO reconstruction.

4. `mbo`
   - Do not pull broadly.
   - Only consider after a registered hypothesis explicitly requires queue/order-level behavior that MBP-10 cannot test.

## Escalation Rules

Default collection:

- Pull `trades` for selected windows.
- Pull `mbp-1` if the question includes depth, liquidity, spread, or top-book imbalance.

Escalate to `mbp-10` only when at least one is true:

- The row is a NAS100 failure-cluster forensic row.
- The row has actual broker R available.
- The row is `LIMIT_PLACED` and needs execution/fill-quality forensics.
- The row is a deliberately selected matched comparator for one of the above.

Do not escalate to `mbo` until:

- There is a written registered hypothesis.
- MBP-10 has already failed to answer the question.
- Expected storage/cost is estimated before execution.

## Outcome Buckets

Keep these buckets separate:

1. Pre-execution rejects:
   - Use synthetic/path labels only.
   - Do not claim broker execution edge.

2. Limit placed, no actual R:
   - Reconcile from broker history if possible.
   - If no execution payload exists, classify as limit-intent until proven filled.

3. Executed/actual-R rows:
   - Use broker actual R as primary outcome.
   - Compare synthetic versus actual R as a separate diagnostic.

## Data Artifacts

Commit:

- Manifests.
- Fetch plans.
- Metadata.
- Feature diagnostics.
- Synthesis reports.

Do not commit:

- Raw DBN/ZST files.
- Large extracted parquet/csv intermediates unless explicitly needed and reviewed.

## Guardrails

- No live trading behavior changes.
- No prompt edits.
- No threshold optimization.
- No alpha claim without pre-registration, actual methodology, sample-size checks, and DSR/PBO discipline where applicable.
- Every report must include synthesis, ambiguity ledger, open questions, next steps, and `NO_PROMOTION_VERDICT`.

## Immediate Next Use

The next valid research use of this spec is a NAS100 failure-forensics hypothesis candidate, not a broad orderflow promotion attempt. The current evidence suggests NAS100 is the only symbol with enough rows to ask a useful orderflow question, but still not enough to answer it decisively.
