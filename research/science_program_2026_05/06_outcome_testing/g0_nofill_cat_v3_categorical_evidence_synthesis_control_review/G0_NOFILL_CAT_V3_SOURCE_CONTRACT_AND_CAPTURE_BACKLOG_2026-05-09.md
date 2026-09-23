# G0 NOFILL CAT V3 Source Contract And Capture Backlog

Promotion posture: `NO_PROMOTION_VERDICT`.

## Source Lessons

- Source-control rows can be useful without entering the accepted denominator. Evidence: `['NOFILL-CAT-ROW-0049', 'NOFILL-CAT-ROW-0050', 'NOFILL-CAT-ROW-0051', 'NOFILL-CAT-ROW-0241']`. Control: Keep source-control families excluded unless a separate rebuild/G12 evidence-class gate changes them.
- USDJPY exact event ordering is truly source-impossible under approved current sources. Evidence: `['NOFILL-CAT-ROW-0130', 'NOFILL-CAT-ROW-0143', 'NOFILL-CAT-ROW-0165', 'NOFILL-CAT-ROW-0178']`. Control: A broker-native USDJPY quote-event source with a sequence ID, exchange/broker quote-event sequence number, or sub-millisecond/sub-row timestamp for each quote update, source-hashed and without account/order/history labels.
- Reject overlaps must be filtered before duplicate collapse. Evidence: `47 reject overlaps with zero denominator effect.`. Control: Accepted-first filtering is mandatory for all future count/control views.
- Opening-drive source projections require duplicate discipline before interpretation. Evidence: `43 noncanonical accepted projections; 51 row-level projection labels collapse to 8 primary duplicate-key members.`. Control: Future opening-drive contract must freeze canonical projection and duplicate policies before any result lane.

## Capture Backlog

### 1. USDJPY_BROKER_NATIVE_QUOTE_EVENT_SEQUENCE_SOURCE

Purpose: Clear or preserve the four source-impossible USDJPY rows and future same-tick event-order blockers.

Required fields:
- `broker-native quote event sequence ID or sequence number`
- `sub-row or sub-millisecond timestamp`
- `bid/ask quote state`
- `source hash`
- `no account/order/history/live labels`

Opens result scoring: `false`.

### 2. NOFILL_FORWARD_LIFECYCLE_CAPTURE_CONTRACT

Purpose: Capture pending intent creation, terminal-area touch, side-aware entry absence, cancel/expiry reason, spread, and source coverage prospectively.

Required fields:
- `pending intent create time`
- `entry price and side-aware touch status`
- `terminal-area touch time or absence`
- `cancel/expiry timestamp and reason`
- `source coverage and same-tick ambiguity flags`

Opens result scoring: `false`.

### 3. OPENING_DRIVE_SOURCE_PROJECTION_CONTRACT_DESIGN

Purpose: Turn projection-ready rows into a frozen categorical contract before any future result lane.

Required fields:
- `range definition`
- `breakout/as-of state`
- `projection canonicalization`
- `duplicate policy`
- `label family boundaries`

Opens result scoring: `false`.

### 4. NOFILL_CAT_V3_SOURCE_SAFE_EXPANSION_PACKET

Purpose: Add source-hashed rows only through a separate packet/rebuild/G12 path.

Required fields:
- `row source contract`
- `as-of timestamp policy`
- `forbidden field scan`
- `duplicate-key policy`
- `exclusion ledger`

Opens result scoring: `false`.

### 5. FILL_PATH_EVENT_ORDER_VOCABULARY_CONTRACT

Purpose: Preserve event-order categories as vocabulary for a future frozen contract without current result interpretation.

Required fields:
- `entry event timestamp`
- `terminal-area event timestamp or absence`
- `protective-level event timestamp or absence`
- `quote side predicate`
- `same-tick/same-bar ambiguity flag`

Opens result scoring: `false`.

