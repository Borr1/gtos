# NOFILL CAT V3 Result Contract Saturation Review - 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`

## Hard Questions

### What exact mistake would make source-control rows look like accepted result rows?

Failing to require `v3_terminal_family=accepted` and relying only on source/control evidence text would admit rows 0049/0050/0051/0241. The contract blocks this by row-id exclusions, `in_accepted_packet_denominator=false`, and verifier checks.

### What exact mistake would let source-impossible USDJPY rows leak back into denominators?

Treating same-tick quote-state ambiguity as resolved, or collapsing by duplicate key before applying row-id terminal-family exclusions. The contract applies row-level exclusions before duplicate collapse and keeps the exact unblocker as broker-native event sequence evidence.

### What exact mistake would let the 65 rejects influence sample size?

Counting the full 298-row universe as a denominator, or using reject sibling rows as duplicate projections. The future scorer must start from the 225-row eligibility ledger and may read rejects only from the exclusion ledger.

### Which fields look harmless but are actually dangerous?

`actual_r`, `synthetic_r`, `broker_actual_r`, `win_rate`, `expectancy`, `profit`, `account_history`, `live_order_state`, hidden labels, MT5 order/deal/position tickets, and any post-cancel/post-terminal field that modifies source geometry are forbidden.

### Which duplicate-key choice could double-count opportunity?

Accepted rows have `225` row-level entries but only `182` unique `nofill_duplicate_key` values. Row-level-only reporting would overstate sample size. The canonical projection rule prevents that.

### Which rows are eligible only under row-level counting?

All 225 accepted rows are row-level eligible. Only the canonical representative for each `nofill_duplicate_key` is duplicate-collapsed eligible. Source-control, source-impossible, and reject rows are eligible under neither denominator.

### Which label family is most likely to be over-interpreted?

`nofill_terminal_before_entry` looks like a meaningful lifecycle event because it has many rows, but it remains categorical input-only and cannot be described as edge, win/loss, R, or validation.

### Which roots could change the contract if discovered?

- `C:/tmp` exists=True: No root expands the denominator in this contract. Future scoring may add rows only through a separately source-hashed/G12-accepted packet.
- `C:/Users/MSI/Documents/ai-trading-agent/data` exists=True: No root expands the denominator in this contract. Future scoring may add rows only through a separately source-hashed/G12-accepted packet.
- `C:/Users/MSI/Documents/ai-trading-agent/data/ticks` exists=True: No root expands the denominator in this contract. Future scoring may add rows only through a separately source-hashed/G12-accepted packet.
- `C:/Users/MSI/Documents/ai-trading-agent/data/external` exists=True: No root expands the denominator in this contract. Future scoring may add rows only through a separately source-hashed/G12-accepted packet.
- `C:/Users/MSI/Documents/ai-trading-agent/shadow_logs` exists=True: No root expands the denominator in this contract. Future scoring may add rows only through a separately source-hashed/G12-accepted packet.
- `C:/SierraChart` exists=True: No root expands the denominator in this contract. Future scoring may add rows only through a separately source-hashed/G12-accepted packet.

No local heavy root is allowed to expand this contract's denominator. New source evidence can only feed a separate source packet, G12 audit, then a new or revised contract.

### What would a skeptical G12 audit reject?

It would reject hidden denominator movement, source-control rows in eligibility, USDJPY impossible rows inferred as resolved, reject rows in sample size, forbidden fields, missing source hashes, or row-level-only denominator claims. The verifier checks these exact failure modes.

### If the next scorer finds an ambiguity, should it score, exclude, split, or route back?

Score nothing by inference. If the row is accepted but duplicate/conflict/source/hash/field ambiguity appears, block that duplicate key and route back to source-control. If the row is source-control/source-impossible/reject, exclude. If the ambiguity requires R/broker/live/account evidence, split to a separate owner-approved contract.

### What did this contract deliberately not answer?

It does not answer whether any categorical family is profitable, predictive, validated, promotable, or live-actionable. It does not open R, win rate, expectancy, DSR/PBO, broker actual-R, account history, order/deal/position, or live execution evidence. Future G12 audit and separate scoring lanes own those gates.
