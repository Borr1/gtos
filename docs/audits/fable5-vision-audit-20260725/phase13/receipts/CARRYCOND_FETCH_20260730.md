# The carry-conditional data fetch — DONE 2026-07-30

**The three dead sleeves' data blockade is broken.** AV-2 priced the ask (four metals crosses
+ corn/cotton H4; a clock proof for the GER40/UK100 M1 already on disk); the orchestrator
executed it against the live FTMO terminal, read-only, same session as the run-all wave.

## What was exported (host `bridge_ftmo_carrycond_h4_m1_20260730`, mirrored locally)

| file | rows | span | note |
|---|---:|---|---|
| XAUEUR/XAGEUR/XAUAUD/XAGAUD `_H4` | 8,547 each | 2021-01-21 → 2026-07-30 | the broker's full H4 depth |
| CORN_c_H4 | 4,950 | 2023-03-30 → | broker depth; canonical-renamed from `CORN.c` |
| COTTON_c_H4 | 1,712 | 2025-03-17 → | broker depth |
| GER40/UK100 `_M1` | 90,000 each | 2026-04-27 → | terminal M1 depth does NOT reach the March DST window |

Transfer: zipped host-side (2.8 MB, sha256 `1fc0d90c…`), pulled over host-admin in 45 KB
read-chunks (the 8K limit binds command length, not stdout), **hash-verified end-to-end**,
extracted with backslash normalization, **8/8 files sha256-verified against the manifest.**

## The clock, declared honestly

Sidecars written with the SANCTIONED writer (`src/utils/research_timebase.write_sidecar`,
rule resolved from the registry: `new_york_plus_7`), evidence field explicit:
**PROVENANCE-DECLARED, not byte-proven** — same server/terminal/rule as every sibling FTMO
export, anchored to the standing 81-boundary measurement; byte-proof unavailable because the
M1 span contains no US/EU DST disagreement window. AV's harness still classifies the bytes
`CLOCK_UNPROVABLE` (correct — its probe reads bytes), while **the fail-closed loader
(`CsvBarSource`) ACCEPTS all files through the sidecars** — verified by direct load of
XAUEUR, CORN_c, GER40.

## Status after the fetch

`av_deep_h4_ingest.py` residual_ask: **`missing: []` on all three sleeves**
(`metals_softband`, `sub_mid_dn_revert`, `vp_euidx_pocgrav`). What remains is the revival
gates — generator re-runs + carry re-tiering at the ratified rule — which is the next
wave's estate work, now unblocked. One honest limit carried forward: CORN/COTTON depth is
2023/2025+, so `sub_mid_dn_revert`'s commodity members gate on shorter histories than its FX
members; say so in any pooled figure.
