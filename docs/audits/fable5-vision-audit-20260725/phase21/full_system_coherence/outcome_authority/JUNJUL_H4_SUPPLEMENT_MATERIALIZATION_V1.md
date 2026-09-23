# June 2026 H4 lead-in supplement — V1 (2026-08-11)

Third and final supplementary lead-in family, identical pattern to the D1 and
M15 passes (`JUNJUL_D1_SUPPLEMENT_MATERIALIZATION_V1.md`,
`JUNJUL_M15_SUPPLEMENT_MATERIALIZATION_V1.md`), closing the last measured
residual of the June reduced-surface diagnosis: 2026-06-01's five US/UK/JP
index symbols' M15/H1 streams gated by an ~72-pre-day-H4-bar depth threshold in
the index intraday families (06-01 had 66 pre-day H4 bars under the main junjul
family alone; 06-02's 72 consumed fully). June manifest only; no smoke, no
packs, zero outcome reads.

## 1. Identities

| item | value |
|---|---|
| supplement export commit | `bba5a38ae0eac8c1d762fe1f4918861826907755` — "Supplementary H4 lead-in: 2026-04-01..07-31, 24-symbol GTOS surface, FTMO", `origin/vps/…-2026-06-18` (`e81a166e1..bba5a38ae`) |
| payload | `data/mt5_research_exports/junjul_2026_h4_leadin_20260811/` — 24 H4 CSVs + `manifest.json`; **24/24 sha256 re-verified twice**; every symbol's first bar exactly broker `2026-04-01 00:00:00` (no late history), last broker `2026-07-31 20:00:00` |
| producer | `src/research_infra/lane_rematerialization.py` at origin/main `d211a39e6` — same functions as all prior passes |
| new hold family | `sources/bars/junjul_2026_h4_leadin_20260811/` — 24 converted H4 files, true-UTC span `2026-03-31T21:00:00Z → 2026-07-31T17:00:00Z`, 12,976 rows total (8,292 overlap + 4,684 lead-in-only; 174–262 lead-in rows/symbol), `source_sha256` = raw export hashes |

## 2. Conversion cross-check (before any hold write) — PASS

All 24 lead-in files converted to scratch through the producer path and
compared against the existing `junjul_2026_lane_source_20260811` converted H4
over each symbol's overlap (rows at/after that symbol's own first main-family
bar):

- **8,292 overlap rows compared** — exactly the main family's total H4 row
  count, identical timestamp sets for every symbol;
- **0 mismatches**, exact-string equality on every column;
- 4,684 lead-in-only rows, all strictly before each overlap (~29 pre-window
  trading days × 6 H4 bars for FX/indices; crypto deeper with weekends —
  raising 06-01's pre-day H4 depth from 66 well past the ~72 threshold);
- converted lead-in first bars `2026-03-31T21:00:00Z` (broker 04-01 00:00,
  summer +3 h) — clock convention identical.

Closes the VPS verification (bytes on EURUSD/NAS100/BTCUSD, row counts on 24)
to full-row identity on all 24. Detail: `junjul_receipts/H4_SUPP_XCHECK.json`.

## 3. June manifest rebuild (only june_2026 touched)

- Existing **144** `bar_sources` entries preserved value-identical (asserted
  keyed by symbol/timeframe/family); 24 supplement H4 entries added →
  **`bar_source_count` 144 → 168**. Composition per symbol now: D1 ×2, H4 ×2,
  M15 ×2 (each: main + lead-in family), M1 ×1 (`bridge_ftmo_m1_202606`).
- Every non-bar manifest field asserted identical (window 2026-06-01..06-30,
  clock block, tick disclosure 0/24 `captured_tick_archive_ends_before_window`,
  `economic_outcomes_read: false`, `surface: VAL`).
- **`manifest_root_sha256`: `3aa0a9ad3e88a8b457900b9a7451b1c757d2dd0e6c0560e6c38c4ee0f83d2bc7` → `f20fc7ae535c960bac86c7f5749e46cba2f588eca399e696a383fc4d2c355b90`**.
- `july_2026.json` untouched (root `a62964745e…`).

Family selection between the two H4 candidates is the engine's by
`H4_ROOT_ORDER` rank once the orchestrator appends
`junjul_2026_h4_leadin_20260811` — the only machinery step, as with the two
prior lead-ins (the lane accelerator admits only manifest-bound files).

## 4. Registry

Locked transaction, pre-run backup to scratch first.

| item | value |
|---|---|
| file sha256 before | `ef89af74b48b3cd7402fcb4175ad6f5495f965fd213c2047d7e236c0f22c1c7a` |
| file sha256 after | `da3641814ae75e0eab07eecc5df920fa386674379e466d8aeaedc3fd1398721d` |
| `registry_root_sha256` after | `96521cca70488fdc737bc38f71012fd9e7a3325b48ca030ea5776478a6216d49` |

Proven against the backup: june_2026 entry differs in exactly
`source_manifest_root_sha256`; **all 12 other window entries byte-identical**,
july_2026's owner-rebound window `["2026-07-01","2026-07-28"]` preserved;
top-level changes exactly `{windows, registry_root_sha256}`. Post-write, all 13
manifests recompute and bind; registry root recomputes clean. The raw-campaign
registry-hash constants (`lane_rematerialization.py:174/:177`) advance one more
hash stale — same repair owner.

Hold receipt: `receipts/SOURCES_june_2026_h4_supplement.json`.

## 5. Annex

`junjul_receipts/H4_SUPP_XCHECK.json`, `junjul_receipts/H4_SUPP_RESULT.json`,
`junjul_receipts/junjul_h4_supplement_materialize.py` (executed driver).
