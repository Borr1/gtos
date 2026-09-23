# G12 Ready-8 Saturation / Self-Red-Team

Terminal decision: `ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## What Would Break The Audit

- Row inflation bug: a duplicate source candidate, duplicate card expansion, blocked-card inclusion, or expansion-row inclusion would make `24,112` rows look valid. The audit recomputed `3,014` unique source candidates, exactly `8` ready cards, per-card counts of `3,014`, unique rowset IDs, and no blocked-card rows.
- Future-label leakage bug: `target_hit`, `stop_hit`, observed outcomes, R/PnL, win-rate, expectancy, or result labels could leak into rowsets or target contracts. The audit scans exact row keys, recursively scans the target contract for forbidden label keys, and verifies `target_or_hazard_hits_computed=false` plus `performance_or_result_fields_present=false`.
- Ready/blocked confusion bug: blocked cards could enter the ready packet. The audit recomputed the ready cards from terminal status, G0 ready ledger, and packet rows, then verified the blocked-32 denominator stays separate with zero overlap in rowset rows.
- Expansion denominator bug: three new ready-8 observations or eight upstream expansion candidates could enter the accepted `40` or ready `8` denominators. The audit verifies all expansion inclusion flags are false and rowset cards contain only the ready eight.
- Non-deterministic control bug: baseline seeds, control buckets, or matched controls could be generated using unstable randomness. The audit recomputes every seed, bucket, and matched-control key from deterministic formulas and requires zero mismatches.
- Silent scoring bug: a future gate could open scoring during this G12 audit. The audit verifies `may_score_results_now=false`, `may_open_validation_now=false`, and emits only a separate G0 future result-opening gate prompt.

## Same-Evidence-Class Ambiguities Pursued

- The target target-horizon contract contains negative audit fields such as `performance_or_result_fields_present=false`; this is not a performance result. The audit treats these as explanatory false flags and separately rejects only exact observed-label keys or true scoring flags.
- The target dependency ledger notes absent SCID forward-capture status in the worktree/main absolute root. This is not a source-control blocker for this packet because the accepted source universe is the committed, source-hashed `3,014` candidate input rows plus descriptor freeze ledger. Opening live-forward capture would cross evidence class and is left to later monitoring/result gates.
- The target output manifest uses a self-hash exclusion policy. The audit rehashes every non-self target source artifact and binds the target output manifest hash independently through the G12 output manifest.
- The target route verifier and focused pytest fail in this checkout only because the 24,112-row JSONL has CRLF line endings: raw byte hash is checkout-dependent, LF-normalized hash matches the manifest exactly, and every row-level hash/source/as-of/control check passes. This is recorded as nonblocking verifier/EOL hardening, not packet content drift.

No same-evidence-class repair blocker remains. The only next step is the separate G0 future result-opening gate before any quarantined result route.
