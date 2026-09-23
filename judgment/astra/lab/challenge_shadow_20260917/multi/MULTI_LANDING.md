# Challenge multi landing — 2026-09-18

Chair attached two named zips. Unzipped here. Challenge-true
`time_utc` (−3h contract; broker `+3h` kept as `broker_time`). No April
historical. No invent. No APPLY.

| Zip | Files |
|---|---|
| `_peer_multi_20260918` / `_peer_multi_20260918_0c0a.zip` | EURUSD / GBPUSD / USDJPY / US30 (three stems) / XAUUSD M15+H4 (+ XAU D1) |
| `_gbpjpy_eurgbp_20260918` / `_gbpjpy_eurgbp_20260918_518a.zip` | GBPJPY + EURGBP M15+H4 |

Parent `../XAUUSD_*.csv` stays the Wave E XAU authority. The XAU copy here
does not replace it (`resolve_challenge_tf` prefers the parent dir).

US30 is landed because Chair included it. It stays `house_hard_off` /
`ENV-US30`. Do not lift that integer from this drop.

GBPJPY is landed and unused on the current pack (no GBPJPY rows).
BTCUSD / ETHUSD / UK100 / NAS100 were not in either zip.
No non-XAU D1. No US10Y/TNX. No TED/SOFR.

RDF last-bar impulse uses H4 (36h lag). EURGBP/GBPJPY are named landed
books and are **not** USD-impulse inputs.

Rates / funding stay unassembled. DXY reject stays. LABEL only.
