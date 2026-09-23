# June + July 2026 true-UTC lane materialization — V1 (2026-08-11)

`june_2026` and `july_2026` bar-source windows materialized into the machine-local
`LANE_INPUTS_TRUE_UTC_V1` hold
(`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/`)
from the new VPS bar export. Additive-only, fail-closed, **zero economic-outcome
reads** — bars only; no candidate, no campaign, no ledger, no outcome object was
constructed or read. This unblocks the input side of the frozen June/July BAR-3
confirm read (`BAR3_RATIFICATION_20260811.md`); the read itself stays blocked on
the machinery items in §7, which are deliberately not this session's to land.

## 1. Identities

| item | value |
|---|---|
| export commit | `e38ace15c1de5844c28da44b06ec3f45008458aa` — "Jun+Jul 2026 lane-source export: 24-symbol GTOS surface, M1/M15/H4/D1 from FTMO", `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18` (commissioning note's 39-char sha lacked one `a`) |
| export payload | `data/mt5_research_exports/junjul_2026_lane_source_20260811/` — 96 CSVs + `manifest.json`; **96/96 sha256 re-verified against the manifest twice** (once at extraction, once inside the materializer); CRLF preserved via `-text`; broker wall clock (`time_column_convention: broker_wall_clock_not_utc_normalized`); coverage broker 2026-05-15 00:00 → 2026-08-01 00:00 exclusive |
| producer | `src/research_infra/lane_rematerialization.py` at origin/main `550aa72d7` — module content sha256 `137258dcad39bd4abf7be7c5a65e0a212d088cf94d65aa0ed1a9269271c15762`. The additive-window flow reused is Session LM-MAT's `materialize_lane_window_sources` (the producer of the seven 2025 extension windows), with its conversion `_transform_bar_file` / `_parse_broker_bar_time` (`broker_epoch_to_utc`, `NEW_YORK_PLUS_7`), `_find_bar_source`, `_tick_capture_span`, `_source_manifest` + `manifest_root_sha256` assembly (`_stable_sha256` over the payload minus the root field), `_registry_write_lock` transaction shape, pre-existing-window invariance assertion, and `SOURCES_*.json` receipt shape all invoked from the module itself |
| driver (annex) | `junjul_receipts/junjul_materialize.py` sha256 `f9391ad830e0c2b9e570dbafafc67848cb962652a01d6ea316685ccadc76fdc1` — parameterization wrapper only; every hash and schema comes from the module |
| smoke (annex) | `junjul_receipts/t5_resolver_smoke.py` sha256 `1d48dc457cc2237b8c421da4cc896c817c13532dbee7d85c4be399d3c7f0858d` |
| cross-check (annex) | `junjul_receipts/t2_golden_crosscheck.py` sha256 `2860070252688fd4594dc7ae551030a9090ffe6135aa51b7d3eaded3843d2f25` |
| runtime | producer imported from a sparse detached worktree of origin/main `550aa72d7`; the hold's logical repo root resolved by the producer's own `_logical_repo_root_for_registry` to `/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805` — no runtime-worktree path is bound anywhere in the hold |

## 2. Golden conversion cross-check (T2) — PASS on the declared region

Export rows converted through the producer's clock path and compared row-for-row
(open/high/low/close/volume, float equality) against the existing `may_2026`
lane files at the same true-UTC timestamps.

Declared overlap region (broker 2026-05-15 00:00 → 2026-05-30 00:00, i.e. UTC
`[2026-05-14T21:00Z, 2026-05-29T21:00Z)`), all 24 symbols:

| TF | compared rows | value mismatches | missing in export | missing in lane |
|---|---:|---:|---:|---:|
| D1 | 271 | 0 | 0 | 0 |
| H4 | 1,622 | 0 | 0 | 0 |
| M15 | 25,299 | 0 | 0 | 0 |
| M1 | 333,448 | 0 | 41,496* | 0 |
| **total** | **360,640 shared rows** | **0** | | |

\* All 41,496 are BTCUSD (21,081) + ETHUSD (20,415) M1 rows before their
disclosed export-M1 starts (BTC broker 2026-05-31 04:06 = UTC 05-31T01:06;
ETH broker 05-29 15:06 = UTC 05-29T12:06) — the commissioning note's known
genuine late history, zero rows missing for the other 22 symbols. Both series
begin **before 2026-06-01**, and producer semantics window-bound at resolve
time (`build_sources_for_days` per day; manifests bind full source files, e.g.
may_2026's D1 entries span 2013→2026), so the late start is **irrelevant to
both windows**, as the commission predicted.

Full-mutual-span diagnostic (beyond the declared region): every difference of
any kind across all four timeframes is confined to **2026-06-14..2026-06-17** —
the `deep_universe_h4d1_2014_2026` capture live-edge (captured 2026-06-16/17:
partial final bars, e.g. AUDJPY D1 2026-06-16T21:00Z lane volume 13,305 vs
completed 92,635, and a missing broker-06-16 bar on some symbols). Terminal
history revision is therefore **excluded** on 05-15..05-29 and the deep
archive's June tail is measured **unusable** for June windows — which this
materialization already guarantees by binding all four timeframes to the new
export (§3).

Clock spot-checks through the producer function: broker `2026-06-01 00:00` →
`2026-05-31T21:00Z` (summer, UTC+3), broker `2026-01-15 00:00` →
`2026-01-14T22:00Z` (winter, UTC+2), broker `2026-03-09 00:00` →
`2026-03-08T21:00Z` (US spring-forward date, not EU) — the measured
`America/New_York + 7 h` rule.

## 3. What was materialized (T3)

Structure per manifest: 24 symbols × D1/H4/M15/M1 = **96 `bar_sources`**, zero
`tick_sources`, all-24 `tick_gaps` (the May precedent), `surface: VAL`,
`economic_outcomes_read: false`, `status: LANE_TRUE_UTC_SOURCE_AUTHORITY_VALID`,
same `clock` block, H1 absent by design (the resolver derives it from M15,
`use_native_h1=False`; smoke-verified present on every resolved symbol).

New source families under `sources/bars/`:

| family | content | files | rows |
|---|---|---:|---:|
| `junjul_2026_lane_source_20260811` | D1+H4+M15, full export span (true-UTC first/last ≈ 2026-05-14T21:00Z → 2026-07-30T21:00Z D1 / 07-31T17:00Z H4 / 07-31T20:45Z M15) | 72 | D1 1,387 · H4 8,292 · M15 129,512 (per window manifest) |
| `bridge_ftmo_m1_202606` | M1 cut at broker June bounds (rows with broker time in `[2026-06-01, 2026-07-01)`) | 24 | 753,469 |
| `bridge_ftmo_m1_202607` | M1 cut at broker July bounds | 24 | 787,168 |

The M1 family names are forced by the engine (`attempt5` derives
`bridge_ftmo_m1_{YYYYMM}` from each day's month); the cut reproduces the
broker-month capture convention every existing `bridge_ftmo_m1_*` family
embodies (e.g. `bridge_ftmo_m1_202605` spans UTC 2026-04-30T21:05 →
05-29T20:54). Conversion is the module's, verbatim, over the full export file;
`source_sha256` on every row (M1 included) is the **raw export file hash**, so
provenance binds directly to the VPS manifest.

**Manifest roots (the two values the future prereg binds):**

| window | `manifest_root_sha256` | window span | split | tick disclosure |
|---|---|---|---|---|
| `june_2026` | `7498a9d5fe18435c352f6b64cdac1109a79ea875a415f274ff9964655fdf2248` | 2026-06-01..2026-06-30 | `lane_validation` | 0 tick sources, 24 gaps, `captured_tick_archive_ends_before_window` |
| `july_2026` | `a62964745ed1609bfe268f1b41996aa161c4fb500f49c2ffef9ee1c6a1e4b9a4` | 2026-07-01..2026-07-31 | `lane_validation` | 0 tick sources, 24 gaps, `captured_tick_archive_ends_before_window` |

Tick status measured from the capture archive's own metadata
(`_tick_capture_span` → 2025-10-01T00:05Z .. 2026-04-29T23:54Z; both window
starts sit after the span end). Same basis on which May generated and scored.

Hold receipts: `receipts/SOURCES_june_2026.json`, `receipts/SOURCES_july_2026.json`.

## 4. Registry (T4) — additive, proven

Both entries are schema-matched to the producer's fresh-window shape (the exact
key set of `april_2026`/`may_2026`: `window, split, surface, source_manifest,
source_manifest_root_sha256, pack_root, pack_roots, pack_status,
campaign_sealed`), with the values the producer writes for a source-only window:
`pack_roots: {}`, `pack_status: "NOT_BUILT"`, `campaign_sealed: false`.

Invariance, asserted twice (inside each locked transaction against the
in-lock `before` snapshot, and at the end against the pre-run byte backup):
**all 11 pre-existing window entries byte-identical**, top-level changes exactly
`{windows, status, registry_root_sha256}`. `status` moved
`LANE_TRUE_UTC_INPUT_REGISTRY_COMPLETE → LANE_TRUE_UTC_INPUT_REGISTRY_SOURCE_READY`,
which is the producer's own semantic (`_register_pack_roots` restores COMPLETE
only when every window is BUILT_AND_VALIDATED). Post-edit, every one of the 13
windows' manifest roots recomputes and matches its registry binding, including
the prereg-bound `february_2026` (`955937e4f0c4…`) and `may_2026`
(`7e0864b2c2ca…`), and the registry root recomputes clean.

| registry | sha256 |
|---|---|
| file, before | `fc505c32344247ad76790b92281bc3d9ff65d6e6d85c5a3843ce07f5e2a0b797` |
| file, after | `77caced170da362a9d3e4855aa8f830b13fd78293d56fbd955ae49b609ca0b2a` |
| `registry_root_sha256`, after | `8e7ade3620e420404335967e109e10f514d753313a3d3f53c3e05527e2e5fe2f` |

## 5. Day lists

Three conventions exist and they are not the same list; the commissioning
expectation ("trading weekdays — June 22, July 23") matches the **prereg**
convention, not the registry's.

1. **Registry / guard calendar convention** (what `WindowSpec.days` enumerates,
   what `guard.authorize_window` audits, and what `pack_roots` keys if packs are
   ever built — every existing window's `pack_roots` carries **all calendar
   days**, weekends included): June = 30 days `2026-06-01..2026-06-30`,
   July = 31 days `2026-07-01..2026-07-31`.
2. **Prereg day-list convention** (pure Mon–Fri, holidays included and left to
   stand down inside the engine — the February and April+May preregs' own
   convention, e.g. April lists Good Friday 2026-04-10):
   - June (22): 01, 02, 03, 04, 05, 08, 09, 10, 11, 12, 15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 29, 30
   - July (23): 01, 02, 03, 06, 07, 08, 09, 10, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 27, 28, 29, 30, 31
3. **Measured full-surface-resolvable days under this export** (§6): June
   06-08..06-30 (17 weekdays) at 24 symbols, June 06-01..06-05 (5 weekdays) at
   2 symbols (BTCUSD, ETHUSD); July 07-01..07-30 (22 weekdays) at 24 symbols,
   **07-31 resolves zero symbols**.

## 6. Resolver smoke (T5) — sources only

**Phase 1 — machinery as committed (expected refusals, captured verbatim).**
`LaneInputRegistry(REGISTRY, allow_registered_march_metadata=True).resolve(...,
purpose=PURPOSE_LANE_ITERATION)` refuses both windows at origin/main HEAD:

- `june_2026`: `WindowRefused: … refuses 30 day(s): day_outside_every_surface`
  (the ratified surface map's declared `gap_2026H1_tail_pre_arming`,
  2026-06-01..07-28).
- `july_2026`: `WindowRefused: … refuses 31 day(s): day_outside_every_surface
  (28 days …); surface_not_iterable:TEST (3 days: 2026-07-29, 2026-07-30,
  2026-07-31)` — the last three July days are on the ratified live-forward TEST
  band (both accounts armed from 07-29).

This is the measured proof that the confirm read still needs its own committed
authorization (§7), exactly as the March one-shot needed
`march_one_shot.py` + `MARCH_PREREG_V1`.

**Phase 2 — source-integrity smoke under process-local disclosed overrides**
(`WINDOWS` naming-table entries; `guard.authorize_window` wrapped with a
smoke-only SurfaceMap adding a TRAIN band 2026-06-01..07-31 — TRAIN being the
gap's own "honest label if it is ever opened"; `attempt5.{D1,H4,M15}_ROOT_ORDER`
extended with the new family name; all overrides die with the process). Then,
inside `inputs.runtime_bindings()`,
`lane._resolver_for(inputs).build_sources_for_days((day,), symbols=GTOS_24,
source_authority_days=(day,))` — the exact call `w21_generate_day_r2b.py` makes.

| window | day | resolved symbols | frames per resolved symbol |
|---|---|---:|---|
| june_2026 | 2026-06-01 | 2 (BTCUSD, ETHUSD) | all five D1/H4/H1/M15/M1 |
| june_2026 | 2026-06-30 | **24** | all five |
| july_2026 | 2026-07-01 | **24** | all five |
| july_2026 | 2026-07-31 | **0** | — |

Boundary probes: 06-02/03/04/05 → 2 symbols each; 06-08 → 24; 07-30 → 24.

Both partial days are **export-boundary facts, measured from the resolver's own
refusal rows**, not code defects:

- **June 01–05 (22 non-crypto symbols dropped):** D1
  `selected_source_below_floor` — 16 rows against the engine's
  `HTF_MIN_TOTAL_ROWS["D1"] = 20` per-day lookback floor. The export's
  2026-05-15 lead-in gives only 11 pre-window trading-day D1 bars; crypto
  passes on weekend bars. First 24-symbol day: **2026-06-08**.
- **July 31 (all 24 dropped):** D1
  `selected_source_missing_requested_replay_range` — `source_covers_requested_range`
  requires the last row's UTC **date** ≥ the requested day, and the final D1 bar
  (covering broker Friday 07-31) opens `2026-07-30T21:00Z`. Only the export's
  final trading day can trip this; the bar itself is present and complete.

Under the committed generator (`w21_generate_day_r2b`) June 01–05 would run as
legal partial days (`missing_symbols: 22` in `run_summary`), and 07-31 would
fail closed (`no symbols resolved`). If the prereg wants those days at full
surface, the repair is a wider re-export: **start ≤ 2026-05-06** (≥ 16 pre-June
trading days for the D1 floor) and **end ≥ 2026-08-04** (includes broker Monday
08-03's D1 bar, UTC date 08-02 ≥ 07-31). Note 07-29..31 are TEST-band days
(Phase 1), so a July list ending 07-28 — which the ratified surface map implies
absent a new owner word — makes the 07-31 limitation moot.

No sink, no campaign, no candidate, no outcome objects at any point.

## 7. What the confirm read still needs (machinery queue, none of it mine to land)

1. **Surface authorization for 2026-06-01..2026-07-xx** — an owner/orchestrator
   decision by the gap's own `resolution_owner` note (honest label TRAIN), with
   the March one-shot as the committed pattern; 07-29+ additionally sits on the
   ratified TEST band.
2. **`lane_rematerialization.WINDOWS` entries** for `june_2026` / `july_2026`
   (naming table; one dict entry each).
3. **`attempt5` family registration**: append `junjul_2026_lane_source_20260811`
   to `D1_ROOT_ORDER` (:2224), `H4_ROOT_ORDER` (:2231), `M15_ROOT_ORDER`
   (:2246) — the lane accelerator serves only families named in those tuples.
4. **Stale registry-hash constants** (consequence of any additive registration,
   priced into this commission): `RAW_CAMPAIGN_REGISTRY_FILE_SHA256`
   (`lane_rematerialization.py:174`, binds `fc505c32…`; file is now
   `77caced1…`) and `RAW_CAMPAIGN_REGISTRY_ROOT_SHA256` (:177, binds
   `b2760cde…`; root is now `8e7ade36…`) — until updated,
   `resolve_registered_raw_campaign_window` (Oct/Nov raw-campaign resolutions)
   refuses with `raw_campaign_registry_authority_mismatch`. The frozen
   February / April+May prereg artifacts are untouched history: they bind the
   registry **as of their freeze** and their manifests by `manifest_root_sha256`,
   all of which still verify (§4).

## 8. Deviations from precedent, complete list

1. **Static D1/H4/M15 from a new family instead of catalog reuse** — forced:
   the catalog's static families end 2026-06-10 (M15) / 2026-06-16 (D1/H4), and
   T2 measured the deep archive's June tail as partial/corrupt at its capture
   live-edge. First window pair to need this; `SOURCE_CATALOG.json` untouched
   (it is not consulted for these rows and its `catalog_root_sha256` binding is
   unchanged).
2. **D1 tail coverage threshold** — the producer's static check demands a bar
   *opening* on the window's final calendar day (`end_exclusive − 1 day`); for
   D1 that bar cannot exist at a summer month-final Friday (it opens at
   `−1 day − 3 h`). D1 checked at `end_exclusive − 1 day − 3 h`; all other
   timeframes verbatim. (The resolver-level twin of this proxy is §6's 07-31
   finding.)
3. **No M1 start-side coverage check** — the producer has none, and its
   accepted estate contains the same shape (may_2026 GER40 M1 first
   2026-05-04T00:16Z; october_2025 UKOIL_cash 2025-10-01T00:05Z; our
   UKOIL_cash 2026-06-01T00:05Z). Session-scaled per-day floors govern M1 at
   resolve time.
4. **M1 month-cut from a wider export** — pure row filter at broker-month
   bounds on module-converted rows; reproduces the capture convention;
   `source_sha256` stays the raw export hash.
5. **Registry `status` transition** COMPLETE → SOURCE_READY — producer
   semantics for a registry holding NOT_BUILT windows (§4).
6. **Prepared packs not built** (`pack_status: NOT_BUILT`) — the BAR-3 read
   consumes lane *sources* via the committed generator (measured: the
   February/April+May pipeline binds `w21_generate_day_r2b.py`, which calls
   `build_sources_for_days`; prepared packs appear nowhere in it). Pack builds
   remain available via the producer's `build_packs` if a future consumer needs
   them.

## 9. Annex

`junjul_receipts/`: `junjul_materialize.py` (driver), `t2_golden_crosscheck.py`
+ `T2_SCOPED.json` (cross-check + scoped result), `t5_resolver_smoke.py` +
`T5_RESULT.json` (smoke phases), `T3_T4_RESULT.json` (materialization summary).
The hold-side receipts are `receipts/SOURCES_{june,july}_2026.json` in the hold.
