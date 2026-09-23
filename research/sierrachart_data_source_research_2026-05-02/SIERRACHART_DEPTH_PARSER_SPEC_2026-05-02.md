# Sierra Chart Depth Parser Spec

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Primary source: <https://www.sierrachart.com/index.php?page=doc/MarketDepthDataFileFormat.html>
Local raw source: `research/sierrachart_data_source_research_2026-05-02/raw/sierra_09_page_doc_MarketDepthDataFileFormat_html.html`

## Purpose

Build a GTOS parser for Sierra Chart `.depth` files so Sierra delayed or Denali depth capture can be converted into the same kind of feature rows we already compute from Databento MBP/MBO windows.

This parser is not a trading signal. It is measurement infrastructure.

## File Discovery

Expected Sierra path:

`[SierraChartInstall]/Data/MarketDepthData/[symbol].[UTC date].depth`

Documented file properties:

- File extension: `.depth`
- Date in filename: UTC date
- File coverage: UTC `00:00:00` to `23:59:59`

## Binary Layout

### Header

Header size: `64` bytes.

Documented header members:

| Field | Type | Meaning |
|---|---|---|
| `FileTypeUniqueHeaderID` | `uint32_t` | magic `0x44444353` (`SCDD`) |
| `HeaderSize` | `uint32_t` | header size |
| `RecordSize` | `uint32_t` | record size |
| `Version` | `uint32_t` | file version |
| `Reserve` | `char[48]` | reserved |

Parser requirements:

- Reject if header is shorter than `16` bytes.
- Reject if magic is not `0x44444353`.
- Reject if `HeaderSize < 16`.
- Warn if `HeaderSize != 64`.
- Reject if `RecordSize != 24` until proven otherwise by a real file.
- Preserve `Version` in metadata.

### Record

Record size: `24` bytes.

Documented record members:

| Field | Type | Meaning |
|---|---|---|
| `DateTime` | `SCDateTimeMS` | UTC timestamp |
| `Command` | `uint8_t` enum | book command |
| `Flags` | `uint8_t` | record flags |
| `NumOrders` | `uint16_t` | number of limit orders at price |
| `Price` | `float32` | price level |
| `Quantity` | `uint32_t` | total contracts at price |
| `Reserved` | `uint32_t` | padding/reserved |

Timestamp conversion:

- `DateTime` is a `uint64` count of microseconds since Sierra's epoch: `1899-12-30T00:00:00Z`.
- Convert to UTC timestamp by adding `DateTime` microseconds to `1899-12-30T00:00:00Z`.

Endian assumption:

- Windows/Sierra C++ structures imply little-endian. Treat little-endian as the initial parser assumption and verify against real files.

## Command Enum

| Value | Command |
|---:|---|
| `0` | `NO_COMMAND` |
| `1` | `COMMAND_CLEAR_BOOK` |
| `2` | `COMMAND_ADD_BID_LEVEL` |
| `3` | `COMMAND_ADD_ASK_LEVEL` |
| `4` | `COMMAND_MODIFY_BID_LEVEL` |
| `5` | `COMMAND_MODIFY_ASK_LEVEL` |
| `6` | `COMMAND_DELETE_BID_LEVEL` |
| `7` | `COMMAND_DELETE_ASK_LEVEL` |

Flag:

| Value | Flag |
|---:|---|
| `0x01` | `FLAG_END_OF_BATCH` |

## Book Replay Rules

Maintain two price-keyed maps:

- bid book: price -> `{quantity, num_orders}`
- ask book: price -> `{quantity, num_orders}`

Apply records:

- `CLEAR_BOOK`: clear both bid and ask books.
- `ADD_BID_LEVEL`: set bid price level to `quantity`, `num_orders`.
- `ADD_ASK_LEVEL`: set ask price level to `quantity`, `num_orders`.
- `MODIFY_BID_LEVEL`: set bid price level to `quantity`, `num_orders`.
- `MODIFY_ASK_LEVEL`: set ask price level to `quantity`, `num_orders`.
- `DELETE_BID_LEVEL`: remove bid price level.
- `DELETE_ASK_LEVEL`: remove ask price level.

Open ambiguity to verify with real files:

- Whether `ADD_*` should reject existing price levels or simply upsert.
- Whether `MODIFY_*` on absent levels appears in practice.
- Whether delete commands can include stale/nonzero quantity.

Initial robust behavior:

- Treat add/modify as upserts.
- Treat delete-missing as warning, not hard failure.
- Log unknown commands as parse errors.

## Snapshot Identification

The official file-format page says a full market-depth snapshot is written every `10` minutes.

Snapshot batch pattern:

1. `COMMAND_CLEAR_BOOK`
2. zero or more add bid/ask records
3. final record with `FLAG_END_OF_BATCH`

Parser should expose:

- `snapshot_id`
- `batch_id`
- `is_snapshot_batch`
- `end_of_batch`
- `records_in_batch`

## Feature Contract

The first extractor output should support the Databento parity contract:

- `top_1_bid_qty`, `top_1_ask_qty`
- `top_5_bid_qty`, `top_5_ask_qty`
- `top_10_bid_qty`, `top_10_ask_qty`
- `top_20_bid_qty`, `top_20_ask_qty`
- `top_10_imbalance`
- `top_20_imbalance`
- `max_bid_wall_qty`, `max_ask_wall_qty`
- `max_bid_wall_distance_ticks`, `max_ask_wall_distance_ticks`
- `near_touch_bid_add_qty`
- `near_touch_ask_add_qty`
- `near_touch_bid_delete_qty`
- `near_touch_ask_delete_qty`
- `top_10_num_orders_bid`
- `top_10_num_orders_ask`
- `book_levels_bid`
- `book_levels_ask`
- `snapshot_age_ms`

## Validation Requirements

Before any GTOS research result can rely on Sierra depth:

1. Parser reads at least one real `.depth` file.
2. Header magic, header size, record size, and version are reported.
3. UTC conversion is checked against Sierra chart display for at least three records.
4. Replayed bid prices are below or at best bid side and ask prices above or at best ask side after each batch.
5. No negative quantity can occur after replay.
6. Snapshot batches rebuild a non-empty book for active futures symbols.
7. Feature rows around at least one Databento-overlapping event window are compared against Databento MBP-10.
8. Report remains `NO_PROMOTION_VERDICT`.

## Test Fixtures

Synthetic tests are allowed for parser mechanics but not for market claims:

- valid header + empty file,
- invalid magic,
- record-size mismatch,
- clear/add/end snapshot batch,
- add/modify/delete sequence,
- unknown command,
- UTC timestamp conversion for known microsecond offsets.

Real-file tests are mandatory before any research interpretation.
