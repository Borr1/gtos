# NEWS_PROTOCOL REPAIR MAP

Repair = ingest a real protocol file, or make the **existing** Challenge writer
**READ** the existing HIGH spine. Missing `NEWS_PROTOCOL` is a **gap**, not
invent-permission.

**Zero invented endpoints.** This map names only paths, schemas, and URLs
already on disk or already cited by committed code. If a feed is absent, the
repair is “open the real file / host writer” — not “guess a URL.”

Challenge surface: login `0` / ns `operator` only.
Wave M already **APPLIED** `calendar_honest` as the label of
writer-not-READ. **Do not invert `spine_empty`.** Host unread ≠ empty spine.

Receipt of measured counts:
`judgment/astra/lab/wires/NEWS_PROTOCOL_REPAIR_MAP_RECEIPT.json`.
Ranked work queue: `judgment/astra/lab/NEWS_PROTOCOL_REPAIR_BACKLOG.md`.

---

## 0. Lock

| Forbidden | Why |
|---|---|
| Invent a `NEWS_PROTOCOL` file or its endpoints | V2 §8 GAP. Closest on git is leftover-ship compose, not a protocol. |
| Invent FOMC / NFP / CPI / speaker rows | Empty spine ≠ no HIGH. Event questions abstain. |
| Overwrite `data/news_calendar.json` | June 2026-05-31 week of record. |
| Call W7 `src/components/news_calendar.py` `NEWS_PROTOCOL` | Different organism (15 / **2** post, USD-mapped). |
| Treat host `inventory_status != READ` as `spine_empty` | Wave M: JSON covering is not empty. Unread is `calendar_honest=false`. |
| Revive leftover-ship `news_tape` | Writer comment: occupancy+Walter, stale 2026-08-27, `result_count 0`. Intentionally absent. |
| Invent a DeItaone / headline-mill client | Two historical tweet-id **source stamps** only. No URL, no mill in git. |
| Recycle `official_high_spine.json` as an input to its own composer | Leftover-ship: that file is the **OUTPUT**. Recycling kept invented clocks. |

---

## 1. Inventory (this tree + leftover-ship + Challenge tape)

Searched this checkout, `origin/main`, and `origin/f5-leftover-ship` for a
file named `NEWS_PROTOCOL`. **Zero files.** Same GAP as
`JEV_INTEGRATION_V2_20260917.md` §8.1.

### 1.1 Files that exist here

| Artifact | Role | Status on Challenge path |
|---|---|---|
| `judgment/astra/lab/NEWS_CALENDAR_REPAIR.md` | Repair note: sync FROM spine; never overwrite June | LIVE instruction |
| `src/judgment/news_spine.py` | Load every JSON under `data/news/` + June operator file. `spine_empty` = no event inside 10d. Challenge axis = path contains `f5_high_calendar` | LIVE (this tree) |
| `src/judgment/news_calendar_sync.py` | Sync HIGH rows FROM `f5_high_calendar_host_20260916.json`. Ticket copy only on exact `scheduled_utc` + name | LIVE repair tool |
| `scripts/jev_news_calendar_sync_from_spine.py` | CLI for that sync | LIVE |
| `scripts/jev_news_calendar_repair.py` | Fetch **already-cited** ForexFactory this-week JSON. Writes dated snapshot under `data/news/`. Exit 2 on fetch fail. Does not overwrite June | LIVE tool; **not** `NEWS_PROTOCOL` |
| `data/news/f5_high_calendar_host_20260916.json` | Host HIGH spine copy. Schema `gtos.f5.high_calendar.v1`. 13 events. sha256 `5258c3bacc94c3fa21b1608d5be71d2357edddf8918f01e1a8366ad85408f7f4`. Updated `20260916T222519Z` | LIVE snapshot (ingested) |
| `data/news/news_calendar_f5_synced_from_spine.json` | Sync product of the host spine. `invented: false`. 13 events | LIVE snapshot, not a harvest |
| `data/news/high_spine_ff_thisweek_20260917.json` | FF this-week HIGH slice (16 rows). Schema `gtos.news.ff_thisweek_snapshot.v0` | W7-adjacent optional; not Warsh filter; not Challenge writer |
| `data/news/ff_thisweek_raw_20260917.json` | Raw FF list (105) | Same |
| `data/news_calendar.json` | June week of record (`week_of` 2026-05-31). Source comment already names `https://nfs.faireconomy.media/ff_calendar_thisweek.json` | W7 organism. Do not overwrite |
| `src/judgment/host_events.py` | Reads landed `events_since_*.jsonl`. Does **not** add a `NEWS_PROTOCOL` endpoint. `news_inventory_at` names `READ` / `NOT_READ` / `UNKNOWN` / `None` | LIVE reader |
| `src/judgment/fluid_local.py` `_calendar_honest` | Writer hit + `inventory_status != READ` → false. No writer row → JSON axis | LIVE (Wave M APPLIED) |
| `src/judgment/challenge_shadow.py` | `extra.update(news_inventory_at(...))` then compose | LIVE on shadow pack |
| `src/judgment/gold_state.py` / `a1_log.intent_gold_state` | Attaches JSON spine via `attach_news`. Does **not** attach host inventory | LIVE JSON, **gap** on live A1 |
| `src/judgment/compose.py` | `event_questions_abstain` keys **only** `news.spine_empty` | LIVE; correct — do not invert |
| `src/judgment/jev_questions.py` `calendar_honest` | Prompt still says “spine present + events non-empty” | **STALE** vs Wave M applied meaning |
| `src/components/news_calendar.py` + `config/agent_config.yaml` `news_filter` | W7 HIGH filter. 15 pre / **2** post. `json_calendar_file: data/news_calendar.json` | W7 LIVE; **not** Challenge |
| `scripts/refresh_economic_calendar.py` | Staleness monitor + Telegram. **Does not fetch** | W7 monitor |
| `src/utils/economic_calendar.py` | CSV 120 / 30 block | Legacy W7; not F5 |

This branch has **no** `scripts/f5_desk/` and **no**
`src/components/ultimate_book/minimal_size.py`. Those live on
`origin/f5-leftover-ship` only.

### 1.2 Leftover-ship (not this branch) — closest compose, still not NEWS_PROTOCOL

| Artifact | What it actually does |
|---|---|
| `scripts/f5_desk/composer.py` `_fold_calendar_docs` | Fold order: `f5_high_calendar` → `official_high_spine` → `news_brief` → `news_calendar` **only if dump is live**. Frozen June/August dump cannot be live HIGH. `news_tape` is not a source |
| `src/components/ultimate_book/minimal_size.py` `f5_compose_official_high_spine` | Writes schema `gtos.news.official_high_spine.v1` with `extracted_utc`. **Does not read** `official_high_spine.json` (that file is the output) |
| same file `f5_live_calendar_paths` | Intel dir `C:\Users\trader\intel-layer\calendar` + repo `data/official_high_spine.json` + `data/news_brief.json` + Challenge `…/operator/judgment/state/f5_high_calendar.json` + `data/news_calendar.json`. Comment: `news_tape` is occupancy+Walter, stale **2026-08-27 07:38 UTC**, `result_count 0` |
| `scripts/f5_desk/inbox_gates.py` | T−15 .. T+60 (`F5_HIGH_PRE_MIN` / `POST`). Mechanism `event_proximity` |
| leftover-ship grep for `news_t15_pending_cancel` / `inventory_status` on those files | **Empty.** The Challenge writer that emits `inventory_status` is **host f5-live**, not leftover-ship |

Intel-layer path is a **Mac leftover-ship machine**. Challenge VPS paths in the
landed slate are `host-local\redacted_host\repo\…`. Two hosts. Do not
assume intel-layer is mounted on Challenge.

### 1.3 Challenge host fold (landed slate, 2026-09-17T10:41:05Z)

From `judgment/astra/lab/challenge_shadow_20260917/slate_20260917T104105Z_bddc8ff9fad4a254.json`
`calendar_fold`:

| Name | Host path | Fold result |
|---|---|---|
| `f5_high_calendar` | `…\operator\judgment\state\f5_high_calendar.json` | **used**, `events_kept: 13` |
| `official_high_spine` | `…\redacted_host\repo\data\official_high_spine.json` | **used**, `events_kept: 0` |
| `news_brief` | `…\redacted_host\repo\data\news_brief.json` | **used**, `events_kept: 0` |
| `news_calendar` | `…\redacted_host\repo\data\news_calendar.json` | **skipped** `stamp_stale:2026-09-07T06:18:42+00:00:244.4h` |

Neither `official_high_spine.json` nor `news_brief.json` is in this git tree.

---

## 2. LIVE vs STUB vs MISSING on Challenge (`0` / `operator`)

| Surface | Class | Evidence |
|---|---|---|
| Host `f5_high_calendar.v1` (13 Warsh-class rows) | **LIVE** | Slate fold 13 kept. Repo copy sha256 `5258c3ba…`. `news_spine` marks `challenge_axis`. Wave F receipt same hash |
| Host writer `news_t15_pending_cancel` / `news_t60_expiry_reeval` | **LIVE** (emitting) | 3337 + 3337 rows on `events_since_20260915.jsonl` (`ts_utc` 2026-09-15T00:00:15Z → 2026-09-17T10:41:32Z). `event_version` `2026-09-14T06:18:09Z`. `account_login` 0 / `namespace` `operator` |
| Writer `inventory_status=READ` | **MISSING** (never on this tape) | 3244 `NOT_READ`, 93 `UNKNOWN`, 3337 `None` (all t60 rows lack the field). `READ` = **0** |
| `calendar_honest` Wave M label | **LIVE APPLIED** | Writer-not-READ is false (10) vs JSON-only true (87). `FLUID-ADM-009` `APPLIED_NAMED` |
| `news.spine_empty` on Challenge as-ofs | **LIVE false** | 0/97 empty. `FLUID-NWS-005` still SHADOW because the tape has no uncovered as-of. Do not invert |
| Host `official_high_spine.json` | **STUB** | Present, 0 events kept |
| Host `news_brief.json` | **STUB** | Present, 0 events kept |
| Host `data/news_calendar.json` | **STUB** (stale) | Skipped 244.4h after 2026-09-07. This tree’s June file is a different week-of-record |
| `NEWS_PROTOCOL` file + endpoint status | **MISSING** | Zero files this clone / `origin/main` / leftover-ship |
| leftover-ship `f5_compose_official_high_spine` | **MISSING on this branch** | Exists only on `origin/f5-leftover-ship` |
| leftover-ship `inbox_gates` T−15..T+60 | **MISSING on this branch** | Constants already copied into `news_spine.F5_PRE/F5_POST` (15 / 60) |
| Intel-layer `C:\Users\trader\intel-layer\calendar` | **MISSING on Challenge VPS** | Leftover-ship Mac path. Not in landed slate paths |
| DeItaone / headline mill client | **MISSING** | Two past `unscheduled_nfp` source stamps only |
| leftover-ship `news_tape` / Walter | **STALE / excluded** | Writer: not a source. Stale 2026-08-27 |
| Live A1 `intent_gold_state` host inventory extra | **MISSING** | Only `challenge_shadow` calls `news_inventory_at` |
| `observe_fluid_inventory` → `compose_shadow` | **STUB path** | Calls `compose_shadow(state, packed)` **without** `extra=` — live A1 drops writer inventory even if a caller passed it |
| `jev_questions.calendar_honest` prompt | **STALE** | Still “spine present”; Wave M meaning is writer-READ |
| W7 `news_filter` / June JSON | **LIVE on W7, MISSING as Challenge truth** | Do not substitute |
| FF this-week snapshot 2026-09-17 | **LIVE optional tool** | Existing URL in June source + `jev_news_calendar_repair.py`. Not Warsh-class. Not the writer |

---

## 3. Host writer inventory (measured)

Tape: `judgment/astra/lab/challenge_shadow_20260917/events_since_20260915.jsonl`
(7729 lines).

| Field | Count |
|---|---:|
| `news_t15_pending_cancel` | 3337 |
| `news_t60_expiry_reeval` | 3337 |
| `inventory_status=NOT_READ` | 3244 |
| `inventory_status=UNKNOWN` | 93 |
| `inventory_status=None` | 3337 (every t60 row) |
| `inventory_status=READ` | **0** |
| `n_events_in_window=0` | 3244 |
| `n_events_in_window=1` | 54 |
| `n_events_in_window=2` | 39 |
| `n_events_in_window=None` | 3337 |
| note `no_active_window_or_unresolved_order` | 3244 |
| note `inventory_unknown_unresolved_retained` | 93 |

The writer is **alive** and stamping unread. 93 rows saw a window
(`n_events_in_window` 1 or 2) and still did not `READ`. Repair is the host
writer opening the existing spine, not a new feed.

`host_events.news_inventory_at` prefers a named status within 6h of as-of.
Sep 9–14 Challenge as-ofs have **no** writer row → extra stays
`host_news_source=unassembled` → `calendar_honest` falls back to JSON
(Wave M: 87 true). Sep 15+ writer hit → false (10).

---

## 4. `calendar_honest` already APPLIED — do not invert `spine_empty`

Wave M (`WAVE_M_RECEIPT.json`, code `54be26d79`):

- `FLUID-ADM-009` `calendar_honest`: JSON covering is **not** enough when
  host `news_t15` / `news_t60` is present and `inventory_status != READ`.
  This tape: never `READ`. APPLIED_NAMED **label only** — does not stack size.
- `FLUID-NWS-005` `spine_empty_honesty`: false on 97/97 because
  `f5_high_calendar` covers every Challenge as-of. Host unread is **not**
  empty spine. Still SHADOW until a real as-of sits outside the 10-day
  cover after calendar repair. **Do not invent that empty.**

`compose.event_questions_abstain` stays keyed on `spine_empty` only.
Event Nouls stay decidable from named JSON HIGH. Honesty of the **writer**
is the separate label.

`jev_questions.py` still tells Jev the old sentence (“spine present”).
That is a prompt repair (R1), not a reason to flip `spine_empty`.

---

## 5. DeItaone / headline mill — external transmission, may be down

**What exists (no more):**

- Two **past** host-spine rows, both `event_type: unscheduled_nfp`,
  `scheduled_utc` 2026-09-04T12:30:21Z / 12:31:34Z:
  - `source: DeItaone/2095851961547395244`
  - `source: DeItaone/2095852269971321307`
- Leftover-ship comment: `news_tape` is occupancy+Walter and went stale
  2026-08-27 07:38 UTC with `result_count 0`. Writer does **not** read it.
- Host `news_brief.json` folded with **0** events kept.
- **No** in-repo client, URL, mill name, or `NEWS_PROTOCOL` endpoint for
  DeItaone or a headline mill. Do not add one from chat.

**Honest degrade when unread / down (already the Wave M contract):**

1. Do not invent prints, tweet fetches, or mill URLs.
2. Keep the two DeItaone rows as **historical stamps** on the ingested spine.
   They do not become live truth.
3. Scheduled official_high rows stay the Warsh-class axis
   (`federalreserve.gov`, `bls.gov`, `ecb.europa.eu`, `bankofengland.co.uk`,
   `boj.or.jp` — already on the 13-event file).
4. If the host writer is present and `inventory_status != READ`:
   `calendar_honest = false`. Typed state still carries `news.events` from
   JSON. Jev may see HIGH names; the honesty bit says the writer has not
   read them.
5. If there is **no** writer row: do **not** pretend the mill is up.
   `host_news_source=unassembled`. `calendar_honest` may be JSON-true.
   That is “no writer stamp,” not “mill confirmed READ.”
6. Never set `spine_empty=true` because the mill is down.
7. Unscheduled class (`unscheduled_nfp`) without a live transmission:
   do not synthesize a new print. `past_flag` / `warsh_class` use the
   **named** nearest HIGH only.

---

## 6. Gaps → repair (file, owner, dependency)

Ordered here by **leverage for feeding typed state into Jev**. Same IDs as
the backlog. No new endpoints.

### G1 — Live A1 drops host inventory extra

| | |
|---|---|
| Class | MISSING wire (code exists) |
| File | `src/judgment/a1_log.py` `intent_gold_state` / `observe` / `observe_fluid_inventory`; `src/judgment/apply_size.py` haircut path |
| Owner | Judgment / Chair land on Challenge only |
| Dependency | `host_events.news_inventory_at` already exists. Landed `events_since_*.jsonl` or host `shadow_logs/f5_minimal/operator/events.jsonl` |
| Action | Pass `news_inventory_at(host_events, as_of)` into compose `extra` the same way `challenge_shadow` already does. `observe_fluid_inventory` must call `compose_shadow(..., extra=extra)`. Do not invent a feed |
| Jev effect | `calendar_honest` and host unread become visible on the live observe path, not only the 97-row shadow pack |

### G2 — Host writer never READS the spine

| | |
|---|---|
| Class | LIVE emitter, MISSING read |
| File | Host f5-live writer (not leftover-ship; leftover-ship has no `inventory_status`). Chair copies `src/judgment/` per `HOST_STATE_SUFFICIENT.md`; the **read** lives in the host writer that emits `news_t15` / `news_t60` |
| Owner | Chair / host f5-live. Not this Cloud seat |
| Dependency | Existing `f5_high_calendar.json` (13 events). **Not** a new endpoint |
| Action | Writer opens that file (mtime reload already specified on leftover-ship). Stamp `inventory_status=READ` when bytes are actually parsed. Keep `NOT_READ` / `UNKNOWN` when they are not. Do not invent HIGH to get a READ |
| Jev effect | `calendar_honest` can become true on Sep 15+ as-ofs without flipping `spine_empty` |

### G3 — `jev_questions.calendar_honest` prompt is stale

| | |
|---|---|
| Class | STALE prompt |
| File | `src/judgment/jev_questions.py` |
| Owner | Judgment |
| Dependency | Wave M `_calendar_honest` (already APPLIED) |
| Action | Tell Jev: JSON covering + writer `READ` (or no writer row). Writer-not-READ is false. Empty spine ≠ no HIGH. Do not ask Jev to invent HIGH |
| Jev effect | System One answers match the APPLIED label |

### G4 — `NEWS_PROTOCOL` file absent

| | |
|---|---|
| Class | MISSING Project file |
| File | Not in git. V2 expected name `NEWS_PROTOCOL`. If the Project stores another basename, ingest the real file and rename the pointer in `JEV_INTEGRATION_V2` §8.1 |
| Owner | Owner / Mac Project / VPS — ingest onto disk |
| Dependency | None that this agent may invent |
| Action | Copy the real file into the tree **when it exists**. Record endpoint names **from that file**. Until then, event Noul without protocol = abstain on **freshness**, not on named JSON HIGH |
| Jev effect | Endpoint status / freshness become typed fields. **Do not draft the protocol** |

### G5 — Host `official_high_spine` / `news_brief` are empty stubs

| | |
|---|---|
| Class | STUB |
| File | Host `data/official_high_spine.json`, `data/news_brief.json`. Leftover-ship composer: `f5_compose_official_high_spine` **writes** the spine from `news_brief` + live `news_calendar` |
| Owner | Host composer / intel-layer on the machine that actually writes those files |
| Dependency | Live `news_brief` or a **live** (not stale) calendar dump. Leftover-ship forbids recycling the spine as input |
| Action | If host files later hold events, ingest a dated copy under `data/news/` (same pattern as `f5_high_calendar_host_20260916.json`). Fold under `news.source` only when `extracted_utc` covers the as-of. Do not invent rows to fill 0-kept |
| Jev effect | Second axis besides `f5_high_calendar`. Today 0+0 means JSON Challenge axis is the 13-event host calendar only |

### G6 — Leftover-ship compose / inbox_gates not on this branch

| | |
|---|---|
| Class | MISSING on this branch |
| File | `origin/f5-leftover-ship` `scripts/f5_desk/composer.py`, `inbox_gates.py`, `src/components/ultimate_book/minimal_size.py` |
| Owner | Chair — copy **named** files onto Challenge f5-live, not wholesale `book_owner.py` (`HOST_STATE_SUFFICIENT.md`) |
| Dependency | Host already folds `f5_high_calendar`. This tree already has F5 15/60 in `news_spine.py` |
| Action | Do not vendor leftover-ship into W7 `book_owner`. If Chair needs compose on this branch, copy the calendar-fold + compose functions only. Do not carry leftover-ship `JUDGE-CHARTER` 0 / $150 |
| Jev effect | Slate `calendar[]` + `calendar_fold` become reproducible here. Not required for JSON `attach_news` |

### G7 — Intel-layer / Walter / news_tape

| | |
|---|---|
| Class | MISSING on Challenge VPS / STALE |
| File | Leftover-ship `F5_INTEL_CALENDAR_DIR = C:\Users\trader\intel-layer\calendar`. V2 Walter fields. `news_tape` excluded |
| Owner | Mac Project (intel-layer) vs Challenge VPS (Administrator) — **name the host** |
| Dependency | Real files on that host. Do not invent Walter cards |
| Action | If Challenge needs intel-layer, the repair is a **path on the VPS**, taken from `NEWS_PROTOCOL` or a measured host listing — not the leftover-ship Mac constant. Until then `walter.present=false` |
| Jev effect | Information tissue stays `unassembled`. Abstain, do not chat-summarize |

### G8 — ForexFactory this-week is optional W7-adjacent, not NEWS_PROTOCOL

| | |
|---|---|
| Class | LIVE tool, wrong organism if used as F5 protocol |
| File | `scripts/jev_news_calendar_repair.py` — URL already in June `data/news_calendar.json` source: `https://nfs.faireconomy.media/ff_calendar_thisweek.json` |
| Owner | Operator / W7 calendar hygiene |
| Dependency | That URL succeeding. Fetch fail → exit 2, `spine_empty` honesty, **no hand-written HIGH** |
| Action | May refresh dated `data/news/high_spine_ff_thisweek_YYYYMMDD.json`. Must not overwrite June. Must not replace Warsh-class `f5_high_calendar`. ISM/PMI/retail/claims are **excluded** on the host spine note |
| Jev effect | Broader HIGH names are not Challenge law. Do not retune `warsh_class` from FF |

### G9 — W7 `news_filter` fail-open if JSON empty

| | |
|---|---|
| Class | W7 hazard (not Challenge) |
| File | `src/components/news_calendar.py` — “NO events loaded — all trades will proceed without event awareness” |
| Owner | W7 book, not Jev |
| Dependency | Operator June/weekly JSON. `refresh_economic_calendar.py` alerts only |
| Action | Out of Challenge scope. Do not point `operator` at this component |
| Jev effect | None if Challenge stays on `news_spine` + host calendar |

### G10 — `FLUID-NWS-005` uncovered as-of does not exist on this tape

| | |
|---|---|
| Class | SHADOW, correctly |
| File | `HOST_STATE_SUFFICIENT.md` remaining-3 table |
| Owner | Time + calendar repair (G2/G5), not a fixture |
| Dependency | An as-of **outside** 10d of any real spine event |
| Action | Wait. Do not invent an empty. Do not flip `spine_empty` on unread |
| Jev effect | `spine_empty_honesty` stays constant-false until a real gap |

---

## 7. What Jev should consume today (typed, no invent)

On Challenge as-ofs in the landed pack:

```
news.spine_empty              false          # JSON cover; do not invert
news.challenge_axis_covering  true           # f5_high_calendar in 10d
news.high_in_f5_window        named bool     # T-15..T+60 from JSON
news.events[]                 named HIGH     # 13-event host spine
host_news_source              challenge_host_news_writer | unassembled
host_news_inventory_status    NOT_READ | UNKNOWN | None | (READ never seen)
calendar_honest               false if writer present and != READ
                              true if no writer row and JSON events exist
event_questions_abstain       news.spine_empty only
```

Physical lots stay **flow × cost**. These news bits are labels.

---

## 8. Explicit non-repairs

- Do not draft `NEWS_PROTOCOL` contents.
- Do not add an X/Twitter/DeItaone API.
- Do not merge `news_calendar.json.frozen-20260821` (6239 events, other schema).
- Do not use April historical M15 as Challenge tape.
- Do not treat leftover-ship `official_high_spine` clocks as authority without
  `extracted_utc` covering the as-of.
- Do not land leftover-ship `book_owner.py` onto the dirty host.
- Do not place, remint, flatten, or write chair inbox from this map.
