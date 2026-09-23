# V2 2025-window readiness — `june_2025`, `august_2025`, `september_2025`, `december_2025`

**READ-ONLY audit, 2026-08-12.** Zero economic-outcome reads were performed on these four windows by
this audit. Every number below comes from the lane registry, the source manifests, the bar files'
`time` column, the surface/guard code paths, and the spread model — never from a candidate, trade, or
outcome ledger.

Ground: `/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/`
Code truth: `/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809` (read-only; its
uncommitted machinery edits were neither touched nor reverted).

---

## 0. THE HEADLINE, AND IT OVERTURNS THE COMMISSION'S PREMISE

`CLAUDE.md` at `fc7aed442` commissions Rule V2 to be "frozen-read on the **four never-funnel-read
2025 windows** already materialized in the hold … Those four windows are the program's validation
currency — **spend nothing on them**."

**Three of the four were already spent, on the record, by wave 19 — and the fourth was never
restricted at all.** This was found by following the only repo-side references to these window ids,
which land entirely in `phase19`. No ledger was opened; the evidence is the estate's own status
markers, which say so in their first line.

`docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/READ_RESTRICTED_INDEX.md`
(Session LP, spend record appended 2026-08-06) opens:

> **THE RESTRICTION IS LIFTED AND THE WINDOWS ARE GONE.** Lane `p2` (wave 19) spent `june_2025`,
> `august_2025` and `september_2025` on 2026-08-06 against a written pre-declaration. **There is no
> held-out set left in this estate.** Any lane that now wants an out-of-sample read must capture a
> new window; do not treat these three as unseen, and do not treat the fact that the pool FILES were
> never opened as leaving them virgin — p2 read the same months through a regenerated roster, which
> is the same evidence and a better object.

and, on the fourth window, under "What is NOT restricted":

> `october_2025`, `november_2025`, `december_2025` — the working set, open to analysis now.

`december_2025` is consumed by name in committed wave-19 code:
`phase19/receipts/discovery/d2_rank.py:45` and `f1_walk.py:22` bind
`pools/LP_december_2025_S0R0_POOL_V1.jsonl.gz` as an input, and `discovery/D2_202512_V1.json` is that
lane's output. The per-pool marker for `june_2025` carries the same spend record next to the artifact
and ends: *"NOT VIRGIN. The economics of this month have been read … Treat this month as in-sample
from now on."*

Critically, **p2 read these months off the very inputs this audit is assessing.** Its
pre-declaration §1 names them: "Inputs: `LANE_INPUTS_TRUE_UTC_V1` bars (M15 bridge +
`deep_universe_h4d1_2014_2026` H4/D1 + the `bridge_ftmo_m1_{202506,202508,202509}` M1 tape)." It is
the same source surface, the same clock, the same hold.

### 0.1 The one distinction that survives, stated precisely

The commission's phrase is "never-**funnel**-read", and that narrower claim **holds by measurement**:

| axis | verdict | evidence |
|---|---|---|
| **funnel-virgin** | **YES** | No artifact under `phase21/` references any of the four window ids. The only `phase21` files touching these calendar months are `postmortem/pm_regime.py` and `PM_REGIME_MONTHS_V1.json`, which compute regime-spine dials over **bars only** — no candidate generation, no rule scoring, no outcome. |
| **estate-virgin** | **NO** | Wave 19: `p2` spent jun/aug/sep on seven pre-declared hypotheses (2026-08-06); `d2`/`f1` consumed dec from the unrestricted working set. |

So a V2 frozen read on these windows is a **funnel-first** read, not an **unseen-window** read. That
is exactly the `train_2026_junjul_funnel_confirm` precedent, whose band in
`trainer_partitions.DEFAULT_SURFACE_MAP` is labelled *"Estate-consumed, funnel-virgin"* with the
matching disclosure — and it is a materially weaker instrument than the commission assumes, because
the broad-family candidate population p2 measured is the same population the funnel ranks over.

**This is an owner-facing correction, not an engineering blocker.** The decision — whether a
funnel-virgin-but-estate-spent surface satisfies a BAR-2-class bar — is Borhen's, and it should be
made with the wave-19 spend in front of him rather than discovered afterwards.

> **Handling note.** The `.READ_RESTRICTED` markers and `READ_RESTRICTED_INDEX.md` were read on the
> strength of `p2_PREDECLARATION.md` §0, which describes them as carrying "window ids, capture
> windows, row counts, sha256 — **no economics**". That description is now stale: the 2026-08-06
> spend record appended headline economics to both. The figures are therefore not reproduced here.
> Anyone auditing this file should know those two paths now disclose outcomes.

---

## 1. Readiness matrix

| window | registry | code-`WINDOWS` | depth | surface/guard | spreads | M1 sanity | verdict |
|---|---|---|---|---|---|---|---|
| `june_2025` | PASS | **ABSENT** | **FAIL — M15** | AUTHORIZED (VAL) | PASS (3/3 decidable) | PASS | **NEEDS_M15_LEADIN + NOT_ESTATE_VIRGIN** |
| `august_2025` | PASS | **ABSENT** | PASS (thinnest) | AUTHORIZED (VAL) | PASS (1/3 decidable) | PASS | **NEEDS_OWNER_RERATIFICATION** (else READY_AFTER_WINDOWS_ENTRY) |
| `september_2025` | PASS | **ABSENT** | PASS | AUTHORIZED (VAL) | PASS (1/3 decidable) | PASS | **NEEDS_OWNER_RERATIFICATION** (else READY_AFTER_WINDOWS_ENTRY) |
| `december_2025` | PASS | **ABSENT** | PASS | AUTHORIZED (VAL) | PASS (1/3 decidable) | PASS | **NEEDS_OWNER_RERATIFICATION** (else READY_AFTER_WINDOWS_ENTRY) |

"else READY_AFTER_WINDOWS_ENTRY" means: **mechanically** the only code change needed is a `WindowSpec`
entry. Every other input-layer check passes. The verdict is gated on §0, not on the plumbing.

---

## 2. Registry and manifest (item 1)

`registry_root_sha256` recomputes: **PASS** (`96521cca70488fdc737bc38f71012fd9e7a3325b48ca030ea5776478a6216d49`,
which is also the value pinned at `lane_rematerialization.py` `RAW_CAMPAIGN_REGISTRY_ROOT_SHA256`).

| field | `june_2025` | `august_2025` | `september_2025` | `december_2025` |
|---|---|---|---|---|
| window span | 2025-06-03 .. 06-30 | 2025-08-01 .. 08-30 | 2025-09-01 .. 09-30 | 2025-12-01 .. 12-31 |
| `surface` | VAL | VAL | VAL | VAL |
| `split` | `lane_validation` | `lane_validation` | `lane_validation` | `lane_validation` |
| `pack_status` | BUILT_AND_VALIDATED | BUILT_AND_VALIDATED | BUILT_AND_VALIDATED | BUILT_AND_VALIDATED |
| `source_manifest_root_sha256` | `6cab71b7…2b7f` | `93c61b7b…44fa` | `cbd202b1…efc79` | `4d547da7…3ba5` |
| manifest root recomputes | PASS | PASS | PASS | PASS |
| root matches registry binding | PASS | PASS | PASS | PASS |
| `pack_roots` count | 28 | 30 | 30 | 31 |
| calendar days in span | 28 | 30 | 30 | 31 |
| `campaign_sealed` / `economic_outcomes_read` | false / false | false / false | false / false | false / false |

`pack_roots` is complete against `LaneInputRegistry.resolve`'s own rule (`{(split, day, day) for day
in window.days}`, all calendar days) for all four — so none would trip
`lane_pack_root_set_incomplete`. Packs are on disk: 839 MB / 1.1 GB / 1.2 GB / 1.0 GB.

**Note the two non-month spans.** `june_2025` starts **06-03**, not 06-01, and `august_2025` ends
**08-30**, not 08-31. Any `WindowSpec` added must copy these bounds verbatim; `resolve()` refuses on
`lane_window_binding_mismatch` if `WindowSpec` and the registry entry disagree by even one day.

### 2.1 Sources

Identical shape on all four: **96 bar sources = 24 symbols × {D1, H4, M15, M1}**, `bar_symbol_count`
24, and **0 missing files** on disk (all 384 `lane_relpath` values resolve).

| timeframe | family | in code root order? |
|---|---|---|
| D1 | `deep_universe_h4d1_2014_2026` | yes — `D1_ROOT_ORDER[0]` |
| H4 | `deep_universe_h4d1_2014_2026` | yes — `H4_ROOT_ORDER[0]` |
| M15 | `bridge_ftmo_m15_20250601_20260610` | yes — `M15_ROOT_ORDER[0]` |
| M1 | `bridge_ftmo_m1_{202506,202508,202509,202512}` | yes — matches `M1_MONTH_PREFIX` + month |

**M1 family present for every month: yes, all four.** No H1 sources exist in any manifest; that is
correct and unchanged — `_resolver_for` sets `use_native_h1=False`, so H1 is derived.

**This is a materially easier integration than June/July 2026.** Those windows needed four brand-new
families appended to the root orders (`junjul_2026_*`). These four bind only families **already
registered**, so **no `*_ROOT_ORDER` edit is required for any of them.**

### 2.2 Ticks

| window | `tick_sources` | gap status |
|---|---|---|
| `june_2025` | **0** | `captured_tick_archive_begins_after_window` × 24 |
| `august_2025` | **0** | `captured_tick_archive_begins_after_window` × 24 |
| `september_2025` | **0** | `captured_tick_archive_begins_after_window` × 24 |
| `december_2025` | **4** (EURUSD, USDJPY, XAGUSD, XAUUSD) | `no_captured_tick_source_for_symbol` × 20 |

Zero tick sources is **precedented and non-blocking**: `may_2026`, `june_2026` and `july_2026` are all
at 0 and are all in `WINDOWS`. `_tick_authority` iterates `tick_sources` and simply produces an empty
spec map; the gaps are carried structurally by `_tick_gaps`. December's 4 match the tick-bearing
windows (jan/feb/mar/apr, oct/nov).

---

## 3. Code `WINDOWS` membership (item 2) — CONFIRMED ABSENT, all four

`lane_rematerialization.WINDOWS` at the generation tree holds exactly eight ids:
`october_2025, november_2025, january_2026, february_2026, april_2026, may_2026, june_2026,
july_2026`. None of the four is present. Measured failure mode, run read-only:

```
resolve(february_2026): OK  window=2026-02-01..2026-02-28 packs=28
resolve(june_2025):     LaneRematerializationError: lane_window_unknown:june_2025
resolve(december_2025): LaneRematerializationError: lane_window_unknown:december_2025
```

`resolve()` checks `window_id not in WINDOWS` **first**, before the guard and before the manifest — so
this is the single first-failing gate, and it fails closed and loudly.

**Second, less obvious prerequisite, measured.** The held registry carries
`march_window_registered: true`, so a plain `LaneInputRegistry(path)` raises
`lane_input_registry_invalid`. Construction **must** pass
`allow_registered_march_metadata=True` (as `resolve_registered_raw_campaign_window` already does).
Any V2 driver that constructs the registry the plain way will fail before it reaches the window id.

**Third: adding a `WindowSpec` re-breaks the raw-campaign pins.** `RAW_CAMPAIGN_REGISTRY_FILE_SHA256`
/ `_ROOT_SHA256` pin the registry FILE and ROOT. A `WINDOWS` entry alone does not touch them — but any
registry mutation does, "which is that pin's intended behavior" per its own comment. Adding these four
windows needs **no registry change**: the entries are already there.

---

## 4. Source depth (item 3)

Lead-in = bars strictly before the window's first day, counted from each file's own `time` column.
Sample = NAS100 (index), EURUSD (FX), BTCUSD (crypto). min/med/max are across all 24 symbols.

| window | D1 (≥30) | H4 (≥72) | M15 | M1 |
|---|---|---|---|---|
| `june_2025` | **1129** / 2962 / 2963 PASS | **6520** / 17751 / 17756 PASS | **84** / 108 / 200 **FAIL** | 1242 / 1605 / 2975 |
| `august_2025` | **1172** / 3005 / 3006 PASS | **6778** / 18009 / 18014 PASS | **3668** / 4236 / 5533 PASS | 0 / 175 / 175 |
| `september_2025` | **1193** / 3026 / 3027 PASS | **6904** / 18135 / 18140 PASS | **5432** / 6252 / 8235 PASS | 0 / 175 / 175 |
| `december_2025` | **1258** / 3091 / 3092 PASS | **7294** / 18525 / 18530 PASS | **10855** / 12486 / 16597 PASS | 0 / 110 / 115 |

Per-sample-symbol M15 lead-in: `june_2025` EURUSD 108, NAS100 100, BTCUSD 200 · `august_2025` 4236 /
4009 / 5533 · `september_2025` 6252 / 5941 / 8235 · `december_2025` 12488 / 11833 / 16597.

**D1 and H4 are healthy everywhere, by a wide margin**, exactly as the DEEP-archive provenance
predicts — the worst D1 case is 1,129 rows against a 30-row bar and the worst H4 is 6,520 against 72.
Crypto late-history is visible but harmless (BTCUSD D1 begins 2017-01-15, ETHUSD 2017-02-19; the
index symbols — NAS100 and SPX500, both 2021-01-20 — are the true floor, and even they clear both
bars by 37.6× and 90.6×).

M1 lead-in near zero is **structural and normal**: the M1 families are per-month files, so lead-in is
only the prior evening's broker session. `january_2026`/`february_2026` — both already read — have the
same shape. `UKOIL_cash` shows exactly 0 M1 lead-in in three windows; unremarkable for the same reason.

### 4.1 `june_2025` M15 starvation — the one hard input defect, and it is independently corroborated

`june_2025`'s M15 lead-in is **84–200 bars, i.e. about one trading day.** The cause is arithmetic: the
M15 bridge family begins **2025-06-01T22:00Z** and the window opens **2025-06-03**.

Calibration against every other window on the same family, and against the June-2026 repair:

| window | M15 lead-in (min across 24 symbols) |
|---|---|
| **`june_2025`** | **84** |
| `august_2025` | 3,668 |
| `october_2025` | 7,265 |
| `november_2025` | 9,197 |
| `january_2026` | 12,683 |
| `february_2026` | 14,447 |
| `june_2026` **after** its starving repair (`junjul_2026_m15_leadin_20260811`) | 3,514 |

So `june_2025` sits **42× below the floor the June-2026 repair was built to reach**, and is the only
window on this family below it. `august_2025` at 3,668 is the thinnest passing window — it clears the
repaired June-2026 floor by 4 %, which is worth knowing but is not a defect.

**Wave 19 measured the same thing independently and to the day.** `p2_PREDECLARATION.md` §1.1
declares: *"The M15 bridge archive begins 2025-06-01T22:00Z. A decision instant needs 672 closed M15
bars for the generator's window; that is first satisfied on 2025-06-12."* Re-measured here from the
bar files:

| as-of date | min M15 bars | symbols with ≥ 672 |
|---|---|---|
| 2025-06-03 (window start) | 84 | **0 / 24** |
| 2025-06-09 | 420 | 2 / 24 |
| 2025-06-11 | 588 | 14 / 24 |
| **2025-06-12** | **672** | **24 / 24** |

The minimum crosses 672 **exactly** on 2025-06-12 and all 24 symbols clear it that day — an exact,
independent reproduction of p2's declared rule.

**Consequence.** `june_2025` is unusable as a full-month surface without one of:

1. an **M15 lead-in family** for late May 2025, appended to `M15_ROOT_ORDER` and bound in the
   `june_2025` manifest — the exact repair already performed for June 2026; or
2. a **declared truncation to 2025-06-12 .. 06-30** (13 of 20 weekdays), which is precisely what
   p2 adopted as its primary rule.

Option 2 needs no new capture but shrinks the window by a third and **re-uses p2's own declared
rule**, which sharpens rather than softens the §0 provenance problem. Option 1 costs a capture. Note
also that a truncated `WindowSpec` would then disagree with the registry entry's `[2025-06-03,
2025-06-30]` span and trip `lane_window_binding_mismatch` — truncation must happen **inside** the
driver, not by narrowing the `WindowSpec`.

---

## 5. Surface map and guard (item 4)

All four fall inside `val_selection_surface_2025_2026H1` (2025-01-01 .. 2026-05-31) on the surface
axis, and inside `train_backfill_2025H2` (2025-06-02 .. 2025-12-31) on the fitting axis.

`guard.authorize_window(purpose=PURPOSE_LANE_ITERATION)`, run read-only:

| window | outcome | days | surfaces | roles | dominant |
|---|---|---|---|---|---|
| `june_2025` | **AUTHORIZED** | 28 | `{VAL: 28}` | `{TRAIN: 28}` | VAL |
| `august_2025` | **AUTHORIZED** | 30 | `{VAL: 30}` | `{TRAIN: 30}` | VAL |
| `september_2025` | **AUTHORIZED** | 30 | `{VAL: 30}` | `{TRAIN: 30}` | VAL |
| `december_2025` | **AUTHORIZED** | 31 | `{VAL: 31}` | `{TRAIN: 31}` | VAL |

`surface_map_id` `gtos_training_lane_surface_map_v1_2026_07_31`, digest
`6aa3e3864fefd1721450bfe060bb4abdc0781dc484670138f3fc230ee9ab36bd`; `registry_id`
`gtos_trainer_partition_registry_v2_2026_07_29`. VAL ∈ `LANE_ITERABLE_SURFACES`, so the unconditional
surface gate passes; no day is in the March blackout.

Disclosure attached to every one of the 119 days:

> VAL is the survivor book's own selection surface (`d.year >= 2025`, `build_survivor_book.py:74` /
> `KB7_growth_kelly_sizing.py:130`). Ranking and gradient checks only; headline expectancy is never
> quoted from VAL alone.

**Two things follow, and the second is easy to miss.**

1. That disclosure is a **second, independent** reason these windows are weak validation currency —
   they sit inside the range that *selected* the armed sleeve book. It is orthogonal to §0 and
   predates it.
2. These four are **also `TRAINING`-authorized** — unlike `january_2026`, which is `SEALED` on the
   fitting axis. A probe confirms `authorize_window(..., purpose=PURPOSE_TRAINING)` returns
   AUTHORIZED for `june_2025`. **The guard will not stop V2 from *fitting* on a window it intends to
   *validate* on.** Nothing in the guard distinguishes the two; only the driver's declaration does. If
   V2 trains "through July 2026" as commissioned, that training range overlaps these windows entirely,
   and the separation must be enforced by the V2 driver explicitly.

---

## 6. Spread coverage (item 5)

`walkforward.quote_side.spread_for(sym, t, account="FTMO", band="mid")`, 3 symbols × 3 in-window
timestamps × 4 windows = **36 calls, 36 successes, 0 exceptions.** Every value > 0, so the
fail-closed zero-spread guard never fires. **The frozen cost machinery covers 2025.**

| window | NAS100 | EURUSD | BTCUSD |
|---|---|---|---|
| `june_2025` (2025Q2) | 1.67734 | 2.00769e-05 | 31.8435 |
| `august_2025` (2025Q3) | 1.49867 | 2e-05 | 8.60276 |
| `september_2025` (2025Q3) | 1.49867 | 2e-05 | 8.60276 |
| `december_2025` (2025Q4) | 1.41064 | 2e-05 | 1 |

Values are constant across the three timestamps within a window, as the model's construction requires
(era ratio × intraweek multiplier; all three probes are weekdays at the same UTC hour).

**The stricter probe is where the four differ.** With `require_decidable=True`:

| window | NAS100 | EURUSD | BTCUSD |
|---|---|---|---|
| `june_2025` | DECIDABLE (era `2025Q2`, RECORDED) | **DECIDABLE** (QUANTIZED) | **DECIDABLE** (RECORDED) |
| `august_2025` | DECIDABLE (`2025Q3`, RECORDED) | **not decidable** | **not decidable** (band spans 6.7×) |
| `september_2025` | DECIDABLE (`2025Q3`, RECORDED) | **not decidable** | **not decidable** |
| `december_2025` | DECIDABLE (`2025Q4`, RECORDED) | **not decidable** | **not decidable** |

with the model's own reason: *"the band spans more than the threshold, so it is a capture requirement
rather than a spread."*

So **`june_2025` is the only one of the four with a fully decidable cost basis on all three sampled
instrument classes** — a genuine and counterintuitive quality inversion against its M15 defect. For
the other three, any FX- or crypto-sensitive V2 figure carries a spread **capture requirement**, and
should be published banded rather than at `mid` alone. Index instruments are decidable everywhere.

One observation recorded without over-reading it: the December EURUSD refusal names era **`2025Q3`**
for a 2025-12-11 timestamp, i.e. the FX era resolution does not land on Q4. Reported verbatim; not
diagnosed here.

---

## 7. M1 chronology (item 6)

EURUSD, one file per window, hash-verified against the manifest rather than trusting it:

| window | family | rows (file / manifest) | sha256 | strictly increasing | dup ts | bounds match |
|---|---|---|---|---|---|---|
| `june_2025` | `bridge_ftmo_m1_202506` | 30,030 / 30,030 ✓ | **MATCH** | **yes** | 0 | ✓ |
| `august_2025` | `bridge_ftmo_m1_202508` | 30,030 / 30,030 ✓ | **MATCH** | **yes** | 0 | ✓ |
| `september_2025` | `bridge_ftmo_m1_202509` | 31,341 / 31,341 ✓ | **MATCH** | **yes** | 0 | ✓ |
| `december_2025` | `bridge_ftmo_m1_202512` | 31,283 / 31,283 ✓ | **MATCH** | **yes** | 0 | ✓ |

All four PASS on every axis, including `first_utc`/`last_utc` agreeing with the manifest exactly. Row
counts across all 384 bar files match their manifest `row_count` (96/96 per window).

---

## 8. What each window needs

**All four, in common — one code change:**

```python
"june_2025":      WindowSpec("june_2025",      "2025-06-03", "2025-06-30", "lane_validation", "202506"),
"august_2025":    WindowSpec("august_2025",    "2025-08-01", "2025-08-30", "lane_validation", "202508"),
"september_2025": WindowSpec("september_2025", "2025-09-01", "2025-09-30", "lane_validation", "202509"),
"december_2025":  WindowSpec("december_2025",  "2025-12-01", "2025-12-31", "lane_validation", "202512"),
```

No `*_ROOT_ORDER` edit, no manifest edit, no registry edit, no new capture. Construct the registry
with `allow_registered_march_metadata=True`.

**Per window, beyond that:**

- `june_2025` — **an M15 lead-in family, or a declared 06-12 start.** Not optional; at 84 bars the
  M15/H1-derived screens will starve exactly as June 2026's did.
- `august_2025`, `september_2025`, `december_2025` — nothing at the input layer.
- **All four — an owner decision on §0** before any read is framed as validation.

**Soft gap, recorded, not blocking:** only `december_2025` carries a pack SMOKE receipt
(`SMOKE_december_2025_b2760cdefa8786cb.json`, `runtime_binding_compatible: true`, `economics_run:
false`). The other three have `PACKS_*` + `SOURCES_*` + `SOURCE_PLAN_*` but no smoke. This matches
`october_2025` and `november_2025`, which are in `WINDOWS` and also lack smokes — so it is precedented.
A smoke is cheap and would confirm runtime binding before a long run.

**Stale-pin note:** `PACKS_june_2025.json` records `registry_root_sha256: bd36e731…`, superseded by
today's `96521cca…` (the junjul materialization passes moved the registry). The binding that matters —
`source_manifest_root_sha256` — matches current on all four. Not a defect; do not "repair" it.

---

## 9. Method and honesty

- Read: `LANE_INPUT_REGISTRY.json`, the four manifests, `PACKS_*`/`SMOKE_*` receipt **schemas**, the
  `time` column of bar files, `p2_PREDECLARATION.md`, `READ_RESTRICTED_INDEX.md`, the
  `.READ_RESTRICTED` markers, and code.
- **Not read:** any row of `LP_*_S0R0_POOL_V1.jsonl.gz`, any `*_S0R0_POOL_V1.json` receipt, any
  `p2_RESULT` / `P2_SEALED_*` / `D2_*` outcome artifact, any pack payload. Prices were never read from
  any bar file — only timestamps.
- Executed read-only from the wave-21 worktree with `PYTHONDONTWRITEBYTECODE=1`; its uncommitted
  machinery edits were not touched. `guard.authorize_window` and `LaneInputRegistry.resolve` are pure
  and write nothing.
- The §0 finding was **not** part of the commission; it surfaced from following window-id references
  and is reported because it changes what the commissioned read means.
