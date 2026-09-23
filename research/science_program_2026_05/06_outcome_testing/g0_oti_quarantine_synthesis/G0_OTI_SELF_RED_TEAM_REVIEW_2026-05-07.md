# G0 OTI Self Red-Team Review - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Scope:** adversarial review of this G0 synthesis before finalization

## Attack 1: The synthesis might overclaim OTI2 because it reports a positive mean.

**Risk:** OTI2's non-ambiguous descriptive mean is `+0.147037R`, which can look like edge evidence.

**Check:** OTI2 also reports a conservative lower-bound mean of `-0.311778R`, 34 same-minute ambiguity flags, 1 unresolved row, no leg-level risk-bank state, and risk-bank primary effective-N 0.

**Correction:** The synthesis states that OTI2 describes initial synthetic path labels only and does not prove risk-bank edge. The next action is a leg-ledger packet, not promotion.

## Attack 2: OTI1's 54 packet-level groups may be counted as independent evidence.

**Risk:** The packet-level denominator can hide repeated source groups across many experiments.

**Check:** OTI1 duplicate report gives 54 packet/cross-packet groups but only 11 source duplicate-group units and 7 source opportunity IDs after prefix unwrap.

**Correction:** The synthesis treats OTI1 as lifecycle-truth-only descriptive evidence and explicitly blocks validation inference.

## Attack 3: OTL1/OTL2 all-blocked reports could conflict with OTI1/OTI2 acceptance.

**Risk:** A future reader may think OTI1/OTI2 violated the initial packet audits.

**Check:** The chronology is OTL1/OTL2 all blocked, then OTB1R/OTB2R rebuilt input-only packets, then G12 OTB rebuild reaudit accepted a narrow subset, then OTI1/OTI2 opened only that subset.

**Correction:** The synthesis uses the later G12 OTB accepted shortlist as controlling packet scope and labels OTL1/OTL2 as historical blocker baselines.

## Attack 4: The synthesis might silently bless `validation_safe=false` gaps.

**Risk:** Some OTI result ledgers do not repeat every guard flag at every top level, especially OTI2 result ledger lacking an explicit `validation_safe=false` key.

**Check:** Master source registry has 0 `validation_safe=true`; preregistry has 0 `outcome_review_opened=true`; OTI2 method freeze and G12 OTI wrapper carry false; scoped scan found no true flip.

**Correction:** This G0 artifact carries explicit `validation_safe=false` and records the formatting gap as a future builder hygiene item, not as a flag flip.

## Attack 5: The next-lane ranking might smuggle in outcome authorization.

**Risk:** Ranking lanes by expected edge value can be misread as permission to test or promote.

**Check:** Every ranked action is framed as packet/source/approval work first. Outcome opening remains blocked until packet readiness and G12 audit.

**Correction:** The prompt pack uses one-line starters that say input-only, source/as-of, no outcomes, no live changes, or approval-only.

## Attack 6: G4 orderflow and G8 options/vol source lanes may require web or paid access.

**Risk:** A future lane could use source recommendations as spending authorization.

**Check:** OTB0 owner approval ledger allows official webfetch/curl for source-contract evidence only; Databento is conditional future free-credit only; G8/Cboe source/legal timing remains blocked.

**Correction:** The owner-approval ledger repeats that no Databento/API/paid calls are authorized by this synthesis and that official webfetch requires raw cache/source index evidence.

## Attack 7: Blocked-packet outcomes might have been inspected indirectly.

**Risk:** Broad grep or packet scans might have touched blocked result artifacts.

**Check:** This pass read blocked packet metadata, next questions, and packet files with 0 records where applicable. It did not run outcome builders, inspect blocked-packet result rows, or open quarantine directories for blocked packets. The OTI2 row parse was limited to the accepted OTI2 result JSONL.

**Correction:** The evidence ledger distinguishes blocked packet metadata from blocked-packet outcomes.

## Attack 8: "Accepted as quarantined discovery" might still imply market truth.

**Risk:** G12 acceptance sounds positive.

**Check:** G12 accepted methodology and containment, not market edge. It explicitly accepted not-computable statistics because the lanes preserved quarantine and exact reasons.

**Correction:** The synthesis uses acceptance only to permit a discovery-only section and a blocker-driven next-lane queue.

## Final Red-Team Verdict

This synthesis is acceptable as a G0 research-control artifact if it remains limited to:

- evidence-chain reconstruction,
- exact proof/non-proof boundaries,
- blocker/action mapping,
- next packet/source/approval lanes,
- and explicit `NO_PROMOTION_VERDICT`.

It would become invalid if used to promote a rule, flip `validation_safe`, open registry outcome review, pool label families, count OTI1 packet units as independent validation trials, score OTI2 risk-bank without leg-level fields, or authorize paid/API/live trading changes.
