# June 2026 D1 lead-in supplement — V1 (2026-08-11)

Supplementary deep-lead-in D1 family materialized into the
`LANE_INPUTS_TRUE_UTC_V1` hold and bound into the **june_2026 manifest only**,
repairing the June 01–05 reduced-surface finding of
`JUNE_JULY_LANE_MATERIALIZATION_V1.md` §6 (D1 `selected_source_below_floor`,
16 rows < the engine's 20-bar per-day lookback floor against the main export's
2026-05-15 lead-in). Additive conversion, one authorized manifest rebuild, one
authorized registry-entry field update, zero outcome reads, no packs, no
resolver smoke (the generation-tree `D1_ROOT_ORDER` append and smoke are the
orchestrator's, immediately downstream).

## 1. Identities

| item | value |
|---|---|
| supplement export commit | `3725c30a6aa2f3abf4ea23317a34d857fedcb797` — "Supplementary D1 lead-in: 2026-04-01..07-31, 24-symbol GTOS surface, FTMO", `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18` (`e38ace15c..3725c30a6`) |
| payload | `data/mt5_research_exports/junjul_2026_d1_leadin_20260811/` — 24 D1 CSVs + `manifest.json`; **24/24 sha256 re-verified twice** (at extraction and inside the materializer); every symbol's first bar broker `2026-04-01 00:00:00`, last `2026-07-31 00:00:00` (no late history, crypto included — as the VPS session stated) |
| producer | same as the main materialization: `src/research_infra/lane_rematerialization.py`, here at origin/main `eed6c496b` — `_transform_bar_file` / `_parse_broker_bar_time` for conversion, `_source_manifest` + `_stable_sha256` for the manifest and its root, `_registry_write_lock` for the registry transaction |
| new hold family | `sources/bars/junjul_2026_d1_leadin_20260811/` — 24 converted D1 files, `source_family = junjul_2026_d1_leadin_20260811`, true-UTC span `2026-03-31T21:00:00Z → 2026-07-30T21:00:00Z`, 2,169 rows total (1,387 overlap + 782 lead-in-only; 29–44 lead-in rows/symbol), `source_sha256` = raw export hashes |

## 2. Conversion cross-check (before any hold write) — PASS

All 24 lead-in files converted to scratch through the producer path and
compared row-for-row against the existing `junjul_2026_lane_source_20260811`
converted D1 files over the overlap (true-UTC ≥ `2026-05-14T21:00:00Z`, broker
2026-05-15 00:00):

- **1,387 overlap rows compared** — exactly the main family's total D1 row
  count, i.e. the overlap timestamp sets are identical for every symbol;
- **0 mismatches** on every column (time/open/high/low/close/volume, exact
  string equality — stronger than the float check used in the main T2);
- 782 lead-in-only rows (all strictly before the overlap; 29/symbol
  FX-and-index, up to 44 for crypto with weekend bars);
- converted first bar uniformly `2026-03-31T21:00:00Z` (broker 04-01 00:00,
  summer +3 h) — clock convention identical to the main export, confirmed at
  the converted level. This closes the VPS session's verification (byte
  identity on 4 symbols, row counts on 24) to full-row identity on all 24.

Detail: `junjul_receipts/D1_SUPP_XCHECK.json`.

## 3. June manifest rebuild (only june_2026 touched)

- Existing 96 `bar_sources` entries preserved **value-identical** (asserted
  keyed by symbol/timeframe/family) with 24 supplement D1 entries added:
  `bar_source_count 96 → 120`, `bar_symbol_count` 24, every symbol now carrying
  two D1 rows (main family + lead-in family).
- Every non-bar manifest field asserted identical to the pre-rebuild manifest
  (window `2026-06-01..06-30`, clock block, statuses, tick disclosure
  0 sources / 24 gaps `captured_tick_archive_ends_before_window`,
  `economic_outcomes_read: false`, `surface: VAL`).
- **`manifest_root_sha256`: `7498a9d5fe18435c352f6b64cdac1109a79ea875a415f274ff9964655fdf2248` → `68c4ce3f2fcda3a9216b87520a6970e2e6b8dd1e5a68a25b686f2e9259d9178c`** — recomputed by the producer's own hashing.
- `july_2026.json` untouched (root `a62964745ed1609b…` unchanged).

With the lead-in bound, June 1's D1 lookback rises from 16 rows to ≈ 40+
(29 lead-in trading bars + the main family's 11 + in-window), comfortably over
the 20-row floor; symbol selection between the two D1 candidates is the
engine's, by `D1_ROOT_ORDER` rank, once the orchestrator appends the family.

## 4. Registry

Locked transaction; the pre-run registry backed up to scratch first.

| item | value |
|---|---|
| file sha256 before | `0f1a0a4b4a5ca85bf2a357b8690628cdd8ef0f492f45b648233ebce573e53d55` (already carries the owner-scoped July rebind) |
| file sha256 after | `f74fbf1e07bca149e6af223caac663d1e030d987c154c9b54c78f35281d9f084` |
| `registry_root_sha256` after | `28c7acdb0a190e75a70e800d60071d93e17b3e328652d4b36e8fb48f420a32a8` |

Proven against the backup: the june_2026 entry differs in exactly one field
(`source_manifest_root_sha256`); **all 12 other window entries byte-identical**,
including july_2026 with its deliberately rebound window
`["2026-07-01","2026-07-28"]` preserved as-is; top-level changes exactly
`{windows, registry_root_sha256}` (status stays SOURCE_READY). Post-write, all
13 manifests recompute and bind, and the registry root recomputes clean.
The raw-campaign registry-hash constants (`lane_rematerialization.py:174/:177`)
remain stale, one hash further along — same repair owner as before.

Hold receipt: `receipts/SOURCES_june_2026_d1_supplement.json`.

## 5. Annex

`junjul_receipts/D1_SUPP_XCHECK.json` (cross-check detail),
`junjul_receipts/D1_SUPP_RESULT.json` (materialization summary + hold receipt
mirror), `junjul_receipts/junjul_d1_supplement_materialize.py` (driver).
