# June 2026 M15 lead-in supplement — V1 (2026-08-11)

Second supplementary lead-in family, identical pattern to
`JUNJUL_D1_SUPPLEMENT_MATERIALIZATION_V1.md`, closing the last residual of the
June reduced-surface diagnosis: 2026-06-01's five index symbols' M15/H1 context
streams starving on ~11 pre-June days of main-export M15 (H1 is derived from
M15, so one M15 lead-in repairs both frames). June manifest only; no smoke, no
packs, zero outcome reads.

## 1. Identities

| item | value |
|---|---|
| supplement export commit | `e81a166e1433a0aea910752a3b000a5f15cb59a9` — "Supplementary M15 lead-in: 2026-04-01..07-31, 24-symbol GTOS surface, FTMO", `origin/vps/…-2026-06-18` (`3725c30a6..e81a166e1`) |
| payload | `data/mt5_research_exports/junjul_2026_m15_leadin_20260811/` — 24 M15 CSVs + `manifest.json`; **24/24 sha256 re-verified twice**; every symbol's first bar broker 2026-04-01 (session-open staggered 00:00/01:00/03:00), last broker 2026-07-31 (22:45/23:45); crypto deep at 11,349 rows each, EURUSD 8,448 — as VPS-stated |
| producer | `src/research_infra/lane_rematerialization.py` at origin/main `8afdfd849` — same functions as both prior passes (`_transform_bar_file`, `_source_manifest` + root hashing, `_registry_write_lock`) |
| new hold family | `sources/bars/junjul_2026_m15_leadin_20260811/` — 24 converted M15 files, true-UTC span `2026-03-31T21:00:00Z → 2026-07-31T20:45:00Z`, 202,648 rows total (129,512 overlap + 73,136 lead-in-only; 2,604–4,100 lead-in rows/symbol), `source_sha256` = raw export hashes |

## 2. Conversion cross-check (before any hold write) — PASS

All 24 lead-in files converted to scratch through the producer path and
compared against the existing `junjul_2026_lane_source_20260811` converted M15
over each symbol's overlap (rows at/after that symbol's own first main-family
bar — per-symbol bounds because M15 first bars stagger by session open):

- **129,512 overlap rows compared** — exactly the main family's total M15 row
  count, identical timestamp sets for every symbol;
- **0 mismatches**, exact-string equality on every column;
- 73,136 lead-in-only rows, all strictly before each overlap;
- converted lead-in first bars 2026-03-31T21:00/22:00Z etc. (broker 04-01
  session opens, summer +3 h) — clock convention identical.

Closes the VPS verification (bytes on EURUSD/NAS100/BTCUSD, row counts on 24)
to full-row identity on all 24. Detail: `junjul_receipts/M15_SUPP_XCHECK.json`.

## 3. June manifest rebuild (only june_2026 touched)

- Existing **120** `bar_sources` entries preserved value-identical (asserted
  keyed by symbol/timeframe/family); 24 supplement M15 entries added →
  **`bar_source_count` 120 → 144**. Composition now, per symbol: D1 ×2 (main +
  D1 lead-in), H4 ×1, M15 ×2 (main + M15 lead-in), M1 ×1 (`bridge_ftmo_m1_202606`).
- Every non-bar manifest field asserted identical (window 2026-06-01..06-30,
  clock block, tick disclosure 0/24 `captured_tick_archive_ends_before_window`,
  `economic_outcomes_read: false`, `surface: VAL`).
- **`manifest_root_sha256`: `68c4ce3f2fcda3a9216b87520a6970e2e6b8dd1e5a68a25b686f2e9259d9178c` → `3aa0a9ad3e88a8b457900b9a7451b1c757d2dd0e6c0560e6c38c4ee0f83d2bc7`**.
- `july_2026.json` untouched (root `a62964745e…`).

June 1's M15 lookback rises from ~11 pre-window trading days to ~40+ (the
lead-in's 04-01 onward), which also feeds the derived H1; family selection
between the two M15 candidates is the engine's by `M15_ROOT_ORDER` rank once
the orchestrator appends `junjul_2026_m15_leadin_20260811` (the lane
accelerator admits only manifest-bound files, so the append is the only
machinery step).

## 4. Registry

Locked transaction, pre-run backup to scratch first.

| item | value |
|---|---|
| file sha256 before | `f74fbf1e07bca149e6af223caac663d1e030d987c154c9b54c78f35281d9f084` |
| file sha256 after | `ef89af74b48b3cd7402fcb4175ad6f5495f965fd213c2047d7e236c0f22c1c7a` |
| `registry_root_sha256` after | `400bfe8218c9c24a4bde8eabbec7ac160c501d2aaf18b7bcc6e0e0efd4a2f101` |

Proven against the backup: june_2026 entry differs in exactly
`source_manifest_root_sha256`; **all 12 other window entries byte-identical**,
july_2026's owner-rebound window `["2026-07-01","2026-07-28"]` preserved;
top-level changes exactly `{windows, registry_root_sha256}`. Post-write, all 13
manifests recompute and bind; registry root recomputes clean. The raw-campaign
registry-hash constants (`lane_rematerialization.py:174/:177`) advance one more
hash stale — same repair owner.

Hold receipt: `receipts/SOURCES_june_2026_m15_supplement.json`.

## 5. Annex

`junjul_receipts/M15_SUPP_XCHECK.json`, `junjul_receipts/M15_SUPP_RESULT.json`,
`junjul_receipts/junjul_m15_supplement_materialize.py` (executed driver).
