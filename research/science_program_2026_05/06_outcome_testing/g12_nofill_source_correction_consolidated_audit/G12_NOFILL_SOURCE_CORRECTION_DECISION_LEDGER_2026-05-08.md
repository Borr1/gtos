# G12 No-Fill Source-Correction Decision Ledger

Promotion posture: `NO_PROMOTION_VERDICT`.

Decision: `ACCEPT_CORRECTED_SOURCE_WAVE_FOR_FUTURE_INPUT_ONLY_CATEGORICAL_REBUILD_WITH_8_EXACT_BLOCKERS_AND_65_REJECTIONS`.

## Counts

| Key | Count |
|---|---:|
| `ACCEPT_PRIOR_CATEGORICAL_LABEL` | 52 |
| `ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD` | 173 |
| `BLOCK_EXACT_SOURCE_OR_ORDERING_GAP` | 8 |
| `REJECT_FROM_REBUILD_CONTRACT_EXCLUDED` | 26 |
| `REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE` | 39 |

## Interpretation

- `ACCEPT_*` means source-safe input-only evidence may be consumed by a future categorical rebuild.
- `BLOCK_*` means exact source/order evidence is still missing or unresolvable.
- `REJECT_*` means the row must not be counted or labeled in the rebuild because source proof or canonical duplicate policy excludes it.
- OTI2 fill/path labels are categorical event-order labels only.
