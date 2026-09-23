# Sierra Depth File Probe Report

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

Tick size used for distance calculations: `0.25`.

## NQM26-CME.2026-05-02_delayed.depth

- Source path: `research\sierrachart_data_source_research_2026-05-02\samples\NQM26-CME.2026-05-02_delayed.depth`
- Size bytes: `16792`
- SHA256: `fab6ad51eb07b6d5b38b9c16941810702791fd230af7b47b70499cbd695a526c`
- Header magic: `0x44444353`
- Header size: `64`
- Record size: `24`
- Version: `1`
- Records: `697`
- Byte remainder after records: `0`
- First timestamp UTC: `2026-05-02T14:53:35.874042+00:00`
- Last timestamp UTC: `2026-05-02T14:55:00.057317+00:00`
- Batches ended by flag: `3`
- Non-empty batches: `1`

Command counts:

- `ADD_ASK`: `86`
- `ADD_BID`: `608`
- `CLEAR_BOOK`: `3`

Latest non-empty batch features:

- Batch records: `0..694`
- Batch timestamp UTC: `2026-05-02T14:53:35.874042+00:00`
- Bid levels: `608`
- Ask levels: `86`
- Best bid: `27781.5`
- Best ask: `27791.0`
- Spread ticks: `38.0`
- Top 1 bid/ask qty: `1` / `1`
- Top 5 bid/ask qty: `9` / `5`
- Top 10 bid/ask qty: `18` / `63`
- Top 20 bid/ask qty: `36` / `88`
- Top 10 imbalance: `-0.555556`
- Top 20 imbalance: `-0.419355`
- Max bid wall qty / distance ticks: `500` / `23926.0`
- Max ask wall qty / distance ticks: `65` / `836.0`
- Top 10 bid/ask num orders: `13` / `12`

## NQM26-CME.2026-05-01_delayed.depth

- Source path: `research\sierrachart_data_source_research_2026-05-02\samples\NQM26-CME.2026-05-01_delayed.depth`
- Size bytes: `160`
- SHA256: `5d42ee932243a5a8f19bf7fe08846071645a421c432f960dad00ed2c1af9154b`
- Header magic: `0x44444353`
- Header size: `64`
- Record size: `24`
- Version: `1`
- Records: `4`
- Byte remainder after records: `0`
- First timestamp UTC: `2026-05-01T21:39:42.798000+00:00`
- Last timestamp UTC: `2026-05-02T14:53:35.556750+00:00`
- Batches ended by flag: `2`
- Non-empty batches: `1`

Command counts:

- `ADD_ASK`: `1`
- `ADD_BID`: `1`
- `CLEAR_BOOK`: `2`

Latest non-empty batch features:

- Batch records: `0..2`
- Batch timestamp UTC: `2026-05-01T21:39:42.798000+00:00`
- Bid levels: `1`
- Ask levels: `1`
- Best bid: `27781.5`
- Best ask: `27791.0`
- Spread ticks: `38.0`
- Top 1 bid/ask qty: `1` / `1`
- Top 5 bid/ask qty: `1` / `1`
- Top 10 bid/ask qty: `1` / `1`
- Top 20 bid/ask qty: `1` / `1`
- Top 10 imbalance: `0.0`
- Top 20 imbalance: `0.0`
- Max bid wall qty / distance ticks: `1` / `0.0`
- Max ask wall qty / distance ticks: `1` / `0.0`
- Top 10 bid/ask num orders: `0` / `0`

## Interpretation

- The sample files pass the documented Sierra `.depth` binary header checks.
- This confirms Sierra delayed depth recording is producing parser-readable files for `NQM26-CME`.
- The current samples are tiny and weekend/market-closed constrained; they are enough for parser proof, not enough for market/orderflow research claims.
- A longer active-session sample is still required before Databento parity or lead/lag analysis.
