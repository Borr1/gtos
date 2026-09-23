# NOFILL USDJPY Sequence Target Row Reconstruction

Promotion verdict: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

| Row | Side | Decision as-of UTC | Entry | Protective | Terminal | First ambiguous timestamp | Exact rows | Predicates on first row |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NOFILL-CAT-ROW-0130 | LONG | 2026-04-20T00:15:00Z | 159.037 | 158.879 | 159.274 | 2026-04-20T00:15:04.153000Z | 1 | entry_touch,protective_level |
| NOFILL-CAT-ROW-0143 | SHORT | 2026-05-01T00:30:00Z | 156.628 | 156.822 | 156.337 | 2026-05-01T00:30:00.083000Z | 1 | entry_touch,protective_level |
| NOFILL-CAT-ROW-0165 | LONG | 2026-04-20T00:15:00Z | 159.037 | 158.879 | 159.274 | 2026-04-20T00:15:04.153000Z | 1 | entry_touch,protective_level |
| NOFILL-CAT-ROW-0178 | SHORT | 2026-05-01T00:30:00Z | 156.628 | 156.822 | 156.337 | 2026-05-01T00:30:00.083000Z | 1 | entry_touch,protective_level |

Every target row is reconstructed from the upstream OTI3 source-control ledger. The reconstruction does not assign R, win/loss, broker actual-R, account/order/history/deal/position labels, or hidden labels.
