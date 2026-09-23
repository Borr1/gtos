# Orderflow Research Synthesis And Next Hypotheses

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Executive Synthesis

The orderflow work moved us closer to the long-term goal by removing the largest data-access ambiguity, but it did not produce a promotable trading rule. We now have a working Databento futures pipeline, a tested futures-to-CFD timestamp policy for the 2026 sample, trades-level footprint proxies, MBP-1 top-of-book depth, and sampled MBP-10 ladder-depth diagnostics.

The core finding is not "orderflow works" or "orderflow failed." The truth is narrower: CME futures data can be aligned to the CFD symbols well enough for research signals, but the current candidate sample is too small, too NAS100-dominated, and too sparse in broker-realized outcomes to promote anything. Orderflow remains a promising awareness layer, especially for forensics and hypothesis generation, but not yet a decision layer.

## What Was Answered

1. Futures-to-CFD divergence:
   - Directional futures-to-CFD mapping is viable for research. Tested windows show high M1 return alignment when MT5 timestamps are shifted by `-120` minutes before the March 2026 US DST weekend and `-180` minutes after.
   - This means CME futures can propagate useful directional/orderflow information into CFD research.
   - It does not mean futures prices equal CFD execution prices. Basis, spread, broker candles, contract rolls, and holiday/session differences still matter.

2. Timestamp policy:
   - The 2026 tested transition is pinned between Friday 2026-03-06 and Monday 2026-03-09.
   - Future joins must use the date-aware offset policy, not a per-event best-fit shift.
   - Remaining caveat: November DST fallback and roll-week behavior are not yet tested.

3. Actual realized-R coverage:
   - Current orderflow feature candidate rows: 23.
   - Synthetic/path target coverage: 13/23.
   - Broker actual realized-R coverage: 1/23.
   - The blocker is mostly structural: 12 rows were rejected before execution, so broker realized R cannot exist for them.
   - One XAUUSD row (`2026-04-17T13:30:00+00:00`) is `LIMIT_PLACED` but has no execution/exit payload in the trade record, so it needs broker-history reconciliation before it can become an actual-R label.

4. Trades-level orderflow:
   - The descriptive separation is mostly a NAS100 failure cluster, not a universal orderflow edge.
   - NAS100 outcome rows are `1` winner / `10` losers in the current synthetic-target subset.
   - XAUUSD has `2` winners / `0` losers, which is not enough to validate a gold orderflow rule.

5. MBP-1 top-of-book depth:
   - MBP-1 was fetched for four scoped groups at estimated cost `$2.279908`.
   - It did not show a strong top-of-book signal. NAS100 candidate/context event15 imbalance delta was `0.0000`; thin-rate delta was `0.0093`.
   - MBP-1 is useful for cheap monitoring, but it cannot validate full footprint/heatmap/LVN claims.

6. MBP-10 ladder depth:
   - MBP-10 was fetched for the same four scoped groups at estimated cost `$4.672899`.
   - One request triggered a Databento warning for streaming size greater than 5 GB, proving broad ladder-depth pulls can become expensive/heavy quickly.
   - Sampled MBP-10 gives more ladder context than MBP-1:
     - NAS100 candidate/context event15 depth10 imbalance delta: `0.0225`.
     - NAS100 candidate/context event15 total-depth delta: `-28.0000`.
     - NAS100 winner-minus-loser total-depth delta: `34.0000`, but winner n is only `1`.
   - This is hypothesis-generating only. It is not promotion-grade.

## Cost And Data Spend

Known Databento research spend/estimates used in this phase:

| Purpose | Approx cost USD |
|---|---:|
| Trades event-window fetch plan from prior artifact | 2.866733 |
| Timestamp transition audit 2026-03-06 | 0.260023 |
| Timestamp transition audit 2026-03-09 | 0.254289 |
| MBP-1 scoped depth pilot | 2.279908 |
| MBP-10 scoped ladder pilot | 4.672899 |
| Approx subtotal | 10.333852 |

Final vendor billing may differ from estimates. Raw data is intentionally kept out of git.

## Doors Opened

- CME futures data is now usable as a research signal source for XAUUSD/NAS100/US30-style CFD questions.
- The timestamp problem is mostly solved for the current 2026 research window.
- We can reproduce several "footprint-like" families from real data: aggressor trade imbalance, absorption-style volume per range, volume profile/LVN/POC proximity, top-of-book depth, and top-10 ladder depth.
- MBP-10 provides enough ladder information to test liquidity-pocket hypotheses without immediately jumping to full MBO.
- The strongest near-term research path is symbol-specific NAS100 failure forensics, not a broad universal orderflow model.

## Doors Closed

- No broad orderflow rule is justified from the current data.
- MBP-1 alone is too shallow to support the influencer-style heatmap/footprint claim.
- Actual-R scoring is not viable yet for orderflow filters because broker realized-R coverage is only 1/23 in the current orderflow candidate subset.
- Broad MBP-10 or MBO history pulls are not smart yet. The sampled MBP-10 fetch already showed large-stream warnings.
- XAUUSD cannot be judged from the current orderflow subset because it has only two synthetic winner rows and no loser contrast.

## Ambiguity Ledger

- November DST fallback remains untested.
- Contract roll behavior remains untested.
- Futures basis and CFD broker spread can distort exact price-level joins even when returns align.
- Synthetic/path labels are useful for rejected-candidate diagnostics but are not broker realized R.
- MBP-10 sampling uses one-second last quotes; it misses intra-second queue churn and spoof/cancel behavior.
- MBP-10 is not MBO. It does not reveal order identity, queue position, iceberg behavior, or participant intent.
- The selected depth windows are not random; they were chosen because the trades diagnostics already made them interesting.
- The language of "manipulation" is not directly observable from these feeds. We can observe flow, liquidity, imbalance, and response; intent remains inference.

## Open Questions

1. Does the NAS100 failure-cluster orderflow signature persist as more candidate windows accrue?
2. Can the XAUUSD `2026-04-17T13:30:00+00:00` limit row be reconciled from broker history, or was it only a limit intent with no fill?
3. Does the date-aware timestamp policy hold across November 2026 DST fallback and contract roll windows?
4. Does MBP-10 add enough over trades + MBP-1 to justify targeted future pulls?
5. Would MBO materially change the conclusion, or would it mostly add cost/storage without a cleaner signal?
6. Can a single NAS100 failure-filter hypothesis be registered without threshold mining?
7. Are volume-profile/LVN features more stable than ladder-depth features, or are both regime/session artifacts?
8. Should forward collection default to trades + MBP-1 and reserve MBP-10 only for candidate windows flagged as high-value forensics?

## Next Hypotheses

These are not promoted rules. They are candidate hypotheses that would need frozen definitions before replay.

1. NAS100 failure-filter hypothesis:
   - Scope: NAS100 CANDIDATE rows only.
   - Family: pre-event volume-profile location + MBP-10 ladder thinness/total-depth.
   - Rationale: Current failures cluster around NAS100; MBP-10 suggests candidate rows had lower total ladder depth than context, but current n is too small.
   - Requirement before test: freeze windows, features, and threshold derivation method without looking at the replay labels.

2. XAUUSD continuation-quality hypothesis:
   - Scope: XAUUSD CANDIDATE rows only.
   - Family: futures trade imbalance + volume-profile/LVN location around the intended OB entry.
   - Rationale: Two XAUUSD synthetic winners are not enough, but gold is the symbol where CME futures likely maps most naturally to the CFD.
   - Requirement before test: collect loser/non-winner contrast first.

3. Execution-awareness hypothesis:
   - Scope: LIMIT_PLACED rows only.
   - Family: depth/flow state at placement versus fill/no-fill and later broker R.
   - Rationale: Orderflow may help more with whether a limit is likely to fill cleanly than with the CANDIDATE/NO_TRADE decision itself.
   - Requirement before test: broker-history reconciliation and forward actual-R collection.

## Recommended Next Steps

1. Backfill or verify the XAUUSD `2026-04-17T13:30` limit-intent row from broker history if available.
2. Do not spend on broad MBO history yet.
3. Add a forward research collector spec for candidate windows: trades by default, MBP-1 by default if affordable, MBP-10 only for targeted forensic buckets.
4. Register one NAS100 failure-forensics hypothesis after reviewing these artifacts, not before.
5. Expand timestamp validation later to November fallback and contract-roll windows.
6. Keep all orderflow outputs under `NO_PROMOTION_VERDICT` until sample size, actual-R coverage, and pre-registration discipline improve.
