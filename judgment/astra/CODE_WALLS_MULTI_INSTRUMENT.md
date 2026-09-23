# Code walls — why Jev / EDGE is gold-first

**Date:** 2026-09-18  
**Seat:** diagnosis + surgical unlock design. **No broker place. No remint. No flatten. No APPLY expansion.**  
**Chair ultragoal:** owner wants **all instruments**. Gold was the first closed-object study, not the destination.  
**Owner vision (this continuation):** **A+ setups × all instruments as sleeves** on the same live gate / info flow as fluid gates + Jev observe.  
**Companions:** [`JEV_ALIVE_ORGANISM_20260917.md`](JEV_ALIVE_ORGANISM_20260917.md), [`JEV_GOLD_STATE_SCHEMA_DRAFT.md`](JEV_GOLD_STATE_SCHEMA_DRAFT.md), `src/judgment/symbol_state.py`, `src/judgment/aplus_pipe.py` (this PR).

This file is evidence, not a KEEP/OFF religion. Every choke is `file:symbol:line`. `XAU_PEER` is **not a symbol in the tree** — it is the documented “XAU parent D1” idea. Implementation already refuses the substitution; the wall is that non-XAU D1 was never landed.

---

## 0. Punchline

Selector V4 and Scheduler V4 do **not** hard-limit the universe to XAUUSD. A ripgrep of `selector_v4.py` and `*scheduler*` under `src/components` finds **zero** `XAUUSD` strings.

Jev / EDGE is gold-first because the **living tissue** that those gates would consume was built as one closed XAUUSD object:

| Layer | What it actually does |
|---|---|
| State | `assemble_gold_state_v0` / `intent_gold_state` default `symbol="XAUUSD"` |
| Questions | `gold_fanout_questions()` — IDs are instrument-neutral; the **name** and prove bars are not |
| APPLY wire | `f5_xau_flow_alignment_size_tilt` |
| Prove | `wire_prove.py` counts **only** rows with `_sym == "XAUUSD"` |
| Lab | `scripts/jev_gold_lab.py` + April historical `XAUUSD_*.csv` |
| Schema draft | `identity.symbol: "XAUUSD"` (literal) |

Wrong trade = missing state or wrong calculation (owner). A GBPUSD / US30 / BTCUSD fire cannot be judged if the assembler, D1, currency map, and prove bars only exist for gold.

**This PR does not APPLY a multi-instrument wire.** It names the walls, ranks the unlocks, ships a default-off `symbol_state.v0` stub, and (this continuation) names the **A+ catalog-vs-pipe** split with a default-off `APLU-OBS-001` observe stub. A+ is not a Jev type. It is Model A `setup_grade` + a framework. Those rows never become W7 `TradeIntent` sleeves, so they never hit fluid / Jev observe.

---

## 1. Three buckets

### (a) Intentional Challenge / prop safety — KEEP

These are writer physics. Do not convert them into Jev toys. Do not lift them to “unlock multi-instrument edge.”

| ID | Site | What it is | Why KEEP |
|---|---|---|---|
| A-1 | `src/judgment/process_lock.py:46-64` | Envelope walls: `$KILL`, 2-stop COUNT, token digest, H8 flatten, hard DD, `us30_off`, occupancy keep-one, dead-window writer clock | Challenge / prop integers. Chair lock. |
| A-2 | `src/judgment/gold_state.py:163` `surface.us30_off: True` | US30 stays off the Challenge fire surface | Named envelope `ENV-US30`. Index tape can still be **scored**; it must not silently become a KEEP fire. |
| A-3 | `src/judgment/family.py:10-11,27-40` | `HARD_OFF_FAMILIES = bleed / orb_crypto / idxrev / xa_huge / mx_us30`; `hard_off_family` keys `us30*` | Current Challenge book config (OWNER_BRIEF 2026-09-16), not W7 law. W7 `crypto` is exempted at `family.py:57-58`. |
| A-4 | `src/judgment/family.py:11,43-45` | `KEEP_FAMILIES = spring / vss` | Current Challenge keep tags. Re-evaluate with complete state; do not invent a new KEEP grid. |
| A-5 | `src/judgment/apply_size.py:34-36,57-81` | Physical haircut only on login `0` / ns `operator` + `GTOS_JEV_APPLY_LIVE=1` | Challenge-only APPLY. W7 armed books must not be resized. |
| A-6 | `src/judgment/process_lock.py:35,115-118` | Leave-orig ticket `293332188` | Already-open exception. Not a symbol wall. |
| A-7 | `src/judgment/compose.py` + `process_lock.py:109-112` | Tilts cannot go below 0.70; cost tilt cannot exceed 1.00; cannot zero / refuse / place | Size physics. Works for any symbol once state exists. |
| A-8 | `src/judgment/bars.py:388` | `books_for_symbol`: **never substitute XAU for another pair** | Correct safety. The missing piece is own-symbol D1, not a gold inject. |
| A-9 | News honesty | Empty spine ≠ no HIGH. Do not invent `NEWS_PROTOCOL` | V2 / organism law. |

### (b) Accidental gold-only scaffolding — CUT candidates

These encode “the first study was gold” as if it were the type system. They starve multi-instrument intelligence without protecting the Challenge.

| ID | Site | Choke | Cut shape (later PR) |
|---|---|---|---|
| B-1 | `src/judgment/gold_state.py:66` | `symbol: str = "XAUUSD"` | Required argument, or default `""` and fail `state_sufficient`. Keep `assemble_gold_state_v0` as the XAU-named wrapper. |
| B-2 | `src/judgment/a1_log.py:212` | `symbol = str(_attr(intent, "symbol") or "XAUUSD")` | Missing symbol must stay missing. **This PR adds `intent_symbol_state` and leaves the live A1 default in place.** |
| B-3 | `src/judgment/bars.py:176` | `normalize_symbol(None)` → `"XAUUSD"` | Empty / None should not alias gold. |
| B-4 | `src/judgment/challenge_shadow.py:137` | `pos.get("symbol") or "XAUUSD"` | Same default on every unscored Challenge row. |
| B-5 | `src/judgment/apply_size.py:480-488` | Haircut assembles via `intent_gold_state` | After prove: call `intent_symbol_state` so a GBPUSD unit cannot be scored as gold. **Not this PR (APPLY path).** |
| B-6 | `src/judgment/process_lock.py:30` | `WIRE_FLOW = "f5_xau_flow_alignment_size_tilt"` | Rename / alias to a symbol-neutral wire id. Keep the string as a compat alias — it is already APPLIED_NAMED on Challenge XAU. |
| B-7 | `src/judgment/process_lock.py:81,88` | Prove bars `min_xau_sufficient` / `min_xau_cost_complete` | Add `min_symbol_sufficient` per landed Challenge symbol. Do not drop the XAU bar. |
| B-8 | `src/judgment/wire_prove.py:96,132` | `_sym(r) == "XAUUSD"` filters **all** prove counts | A EURUSD row that is sufficient and tilts **cannot prove**. That is a measurement wall, not a safety wall. |
| B-9 | `src/judgment/jev_questions.py:23` | Function name `gold_fanout_questions` | This PR adds `symbol_fanout_questions` as an identical alias. Questions themselves are already path-referenced, not XAU-hardcoded. |
| B-10 | `src/judgment/news_spine.py:160,171-172,197` | Default symbol XAUUSD; W7 window match is `currency in {USD, XAU}` | Key the W7 window to `currencies_for(symbol)`. Do not invent events. |
| B-11 | `scripts/jev_gold_lab.py:21-30` | Lab slices are XAU H4 only | Add `jev_symbol_lab.py` over landed Challenge multi CSVs. |
| B-12 | `src/components/primary_analyzer.py:305-316` | KB context assembled **only** when `symbol == "XAUUSD"` | Per-symbol KB or honest empty — already empty for non-gold; the wall is that gold stats must never leak into another symbol (already stripped). Unlock = *build* non-gold KB, do not copy gold. |
| B-13 | `src/components/orchestrator.py:9401-9404` | `_get_instrument_expertise` returns `_XAUUSD_EXPERTISE` or `""` | Same: add validated expertise per class, or leave empty. Do not paste gold W-shape onto FX. |
| B-14 | `src/components/market_state.py:1434` | Session ATR / `session_vol_ratio` only if `symbol == "XAUUSD"` | Ibikunle W-shape is a **gold** finding. Other symbols need their own session ATR or `unassembled`. |
| B-15 | `src/components/candidate_features_logger.py:653` | `m15_sess_vol_ratio` forced `None` unless XAUUSD | Follows B-14. |
| B-16 | `src/components/sprt_monitor.py:122` | Unknown instrument inherits `INSTRUMENT_PARAMS["XAUUSD"]` | Fail closed / `unassembled` params. Do not score NAS100 with gold p0=0.357 / p1=0.620. |
| B-17 | `src/components/permissions.py:2239` | `sl_absolute_min` default **5.0** (gold dollars) | Per-symbol floor from profile / tick size. $5 on EURUSD is a different contract. |
| B-18 | `src/components/permissions.py:101,837` | `symbol="XAUUSD"` defaults; `get_positions("XAUUSD")` | Defaults that silently gold-scope a call. |
| B-19 | `src/components/edge_monitor.py:392` | Default `p0=0.62` “XAUUSD batch WR” | Per-instrument monitor, same as B-16. |
| B-20 | `src/judgment/sleeve_from_tape.py:64-124` | A8 / `ac60` 0.10 / 0.04 from **metals.py** applied to every Challenge sleeve | Metals persistence on a VSS FX tag is a borrowed cliff. Per-class feature pack; metals A8 stays for `w7_metals`. |

### (c) Missing `symbol_state` generality — BUILD

Not a wrong `if symbol == "XAUUSD"`. The object, the tape, and the feeds were never generalized.

| ID | Gap | Evidence | Do not invent |
|---|---|---|---|
| C-1 | No `symbol_state.v0` until this PR | Schema draft locks `identity.symbol: "XAUUSD"` (`JEV_GOLD_STATE_SCHEMA_DRAFT.md` ~line 42) | — |
| C-2 | **XAU_PEER / XAU parent D1** | `gold_state.py:138` comment: “D1 stays on the XAU parent tape.” `bars.py:164-165`: “XAU parent; … No D1 for non-XAU.” `bars.py:388` refuses substitution. | Do **not** inject XAU D1 into GBPUSD. Land own-symbol D1 or leave `timeframes.d1` missing (already visible). |
| C-3 | Challenge multi tape is M15+H4 only | `bars.py:166` `MULTI_SYMBOL_PRIORITY = EURUSD, GBPUSD, BTCUSD, EURGBP, US30, UK100, ETHUSD` | April `data/historical/*` is not Challenge-true (`test_bars_multi.py`). |
| C-4 | Currency map incomplete vs 24-symbol surface | `news_calendar.py:32-42` has 9 keys. `GTOS_24_SYMBOL_SURFACE` is 24 (`v4_timewarp_simulated_live_research_loop.py:293-318`). | Do not invent DXY as a currency. |
| C-5 | DXY feed | Zero committed DXY series used by Jev state | Flag `unassembled`. This PR does. |
| C-6 | Yield / UST feed | Zero committed yield series used by Jev state | Flag `unassembled`. This PR does. |
| C-7 | `NEWS_PROTOCOL` / F5 `official_high_spine` | Organism §4: leftover-ship, **not on this main** | Do not invent. Host `f5_high_calendar` JSON is the Challenge axis that exists. |
| C-8 | Selector / scheduler consume no per-symbol Jev body | `SEL-V4-002` is research-only (`jev_questions.py:13-20`); must not be imported from bound `selector_v4.py` (`a1_log.py:13-14`) | Observe via unbound wrapper + `intent_symbol_state`. No reseal this PR. |
| C-9 | Fluid axes are symbol-agnostic questions on a gold-named object | 48 fluid / 8 envelope (`JEV_GATE_INVENTORY.json`). Alias wire `f5_xau_flow_alignment_size_tilt` on `FLUID-ADM-003`. | Keep envelope integers. Re-prove fluid size tilts per symbol class before APPLY. |
| C-10 | Occupancy clusters already know more than gold | `occupancy.py:20-31` maps XAU/XAG, FX majors, US30/UK100, BTC/ETH | Reuse. Do not collapse everything to `metals`. |

---

## 2. Trace — each named surface

### 2.1 `gold_state` / `intent_gold_state`

```
intent  →  intent_gold_state (a1_log.py:192)
              default symbol XAUUSD          (a1_log.py:212)
              Challenge books_for_symbol     (a1_log.py:229)
              assemble_gold_state_v0         (gold_state.py:61)
                  default symbol XAUUSD      (gold_state.py:66)
                  attach_news(symbol=…)      (news_spine.py:160)
                  surface.us30_off = True    (gold_state.py:163)
                  D1 comment = XAU parent    (gold_state.py:138)
```

`state_sufficient_for_live` needs identity + M15 + H4 + geometry + known family (`gold_state.py:139-148`). D1 is **visible-missing**, not a TF-abstain. That part is already multi-symbol-safe — `test_bars_multi.py` proves GBPUSD M15+H4 without D1 is sufficient.

The accidental wall is the **default**, not the predicate.

### 2.2 `XAU_PEER`

There is **no** `XAU_PEER` identifier in the repository (ripgrep: zero hits). The peer idea is the comment pair:

- `src/judgment/gold_state.py:138` — “D1 stays on the XAU parent tape.”
- `src/judgment/bars.py:164-165` — “XAU parent; … No D1 for non-XAU.”

The **code** that loads books is the opposite:

- `src/judgment/bars.py:388` — “Never substitute XAU for another pair.”
- `books_for_symbol` returns that symbol’s CSVs or `None`. A single-TF cache is treated as XAU only when `sym == "XAUUSD"` (`bars.py:394-396`).

Classification: **(c)** missing own-symbol D1, plus a **stale comment** that could tempt a later session to inject gold D1. This PR names the policy `not_substituted` on `generality.xau_peer_d1`.

### 2.3 Sleeve gates

| Site | Symbol surface | Class |
|---|---|---|
| `sleeves/metals.py:31` `ON_SURFACE` | XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD | W7 metals sleeve — intentional generation surface, not a Jev wall |
| `admission.py` metals specs | same 6-tuple | W7 admission |
| `sleeve_from_tape.py` | A8 / ac60 metals cliffs on **any** Challenge tag | **(b) B-20** |
| `family.py` `dsp_spring_xau` → `house_keep` | name contains `xau` | KEEP tag, not a symbol filter |

W7 `--tags` / `include_clean3` / armed-set are **A0 integers** (organism UB-GEN-001/002). They bound live generation. They are not Jev intelligence walls. Do not expand `--tags` from this diagnosis.

### 2.4 Selector

- `selector_v4.py`: no `XAUUSD` / `gold_state` references. R2-bound — **do not edit**.
- Jev hook `SEL-V4-002` lives in `a1_log.observe_sel_v4_002` (`a1_log.py:340-344`) and assembles via `intent_gold_state(..., origin="historical_lab")`.
- Inventory: `sel_v4_002_research_only: true`, `do_not_edit_selector_v4: true`.

Wall: the **payload** is gold-defaulted. The selector engine is already multi-symbol.

### 2.5 Scheduler

- No `XAUUSD` hits under `src/components/*scheduler*`.
- Same-symbol lifecycle / whiteboard `symbol_state` strings are **position-health** enums (`hard_quarantine`, `same_symbol_same_side_active`), not Jev gold_state.

Wall: scheduler can already see many symbols. It has no Jev symbol body to ask `flow_alignment` on NAS100.

### 2.6 Fluid axes

48 fluid gates, 8 envelope walls (`fluid_gates.py:14-15`, `JEV_GATE_INVENTORY.json`).

- Questions (`jev_questions.py`) path-reference `timeframes.*`, `sessions.*`, `news.*`, `geometry.*` — symbol-agnostic.
- `FLUID-ADM-003` alias_wire = `f5_xau_flow_alignment_size_tilt`.
- Prove of that wire **drops non-XAU rows** (`wire_prove.py:96`).
- Envelope walls stay integers (`process_lock.py:46-64`).

Unlock: prove fluid size/label per **landed** Challenge symbol class (FX / index / crypto / metals). Do not APPLY a GBPUSD tilt from an XAU prove receipt.

---

## 3. Missing sources — flag only

| Source | Status on this tree | Jev rule |
|---|---|---|
| DXY / dollar index | **Absent** | `generality.macro.dxy.status = unassembled` |
| UST yields / real rates | **Absent** | `generality.macro.yields.status = unassembled` |
| `NEWS_PROTOCOL` / leftover-ship `official_high_spine` | **Not on this main** | `not_invented`. Use host `f5_high_calendar` when present; else `spine_empty`. |
| Non-XAU Challenge D1 | **Not landed** (M15+H4 only) | Missing field, not XAU peer. |
| Crypto-native calendar | **Absent** (BTC/ETH map to USD quote only) | USD HIGH is a quote-currency proxy, not a BTC event spine. |

Do not fetch or fabricate any of the above in this PR.

---

## 4. Ranked unlock backlog

Priority = what unblocks **all-instrument** Jev state without touching send / APPLY / envelope.

| Rank | Unlock | Class | Touches | This PR |
|---|---|---|---|---|
| 1 | `assemble_symbol_state_v0` — same body, no XAU default, named absences | (c) | `src/judgment/symbol_state.py` | **Shipped (stub)** |
| 2 | `intent_symbol_state` — missing symbol stays missing | (b) B-2 | same | **Shipped (stub, not wired into A1/APPLY)** |
| 3 | Stop `normalize_symbol(None) → XAUUSD` | (b) B-3 | `bars.py` | Next — needs caller audit |
| 4 | Own-symbol Challenge D1 (or honest missing) for the seven multi names | (c) C-2/C-3 | tape land + `bars.py` comment strike | Tape; no XAU inject |
| 5 | `attach_news` W7 window keyed by `currencies_for(symbol)` | (b) B-10 | `news_spine.py` only (not live `news_calendar.py` this wave) | Design in stub map |
| 6 | Per-class sleeve features (do not run metals A8 on VSS FX as if it were `metals_core`) | (b) B-20 | `sleeve_from_tape.py` | Later |
| 7 | Symbol-neutral prove bars + wire alias | (b) B-6/B-7/B-8 | `process_lock.py`, `wire_prove.py` | Later; keep XAU receipt |
| 8 | `jev_symbol_lab` over landed multi CSVs | (b) B-11 | scripts | Later |
| 9 | Unbound SEL-V4-002 / UB-AUTH-010 observe via `intent_symbol_state` | (c) C-8 | `a1_log.py` | Later; still default-off |
| 10 | Fluid re-prove per symbol class before any non-XAU APPLY | (c) C-9 | prove ledger | Later |
| 11 | Session ATR / expertise / SPRT / SL floor per class | (b) B-13–B-19 | live components | Later; not Jev send |
| 12 | DXY / yield feeds **if** a real source is committed | (c) C-5/C-6 | new data + assembler | **Blocked on source.** Do not invent. |
| 13 | Name A+ frameworks as catalog-only / not-on-pipe | §8 D-1…D-8 | `aplus_pipe.py` | **Shipped (catalog + tests)** |
| 14 | Observe A+ packets via `symbol_state` (not gold default) | §8 U-1…U-3 | `assemble_aplus_observe_state` | **Shipped (stub, not wired)** |
| 15 | HOST land note: env-gated `book_owner` call of `maybe_observe_aplus_at_place` | §8 U-4 | `HOST_APLU_OBS_LAND.md` — **not** spliced; **not** wholesale `book_owner` | **Shipped (note + helper)** |
| 16 | Observe body carries `setup_grade` / `framework` / `kill_zone` / POI | §8 U-5 | additive `aplus` block; `levels.poi` untouched | **Shipped (shadow)** |
| 17 | Sleeve adapter A+ × symbol → pipe-shaped packet, then owner `--tags` | §8 U-8 | registry only after owner word | Later; **not** this diagnosis |

**Never in this backlog:** `ExecutionEngine.open_trade`, `RealMT5.order_send`, remint, flatten, token remint, invented HIGH, Challenge KEEP-grid rewrite, W7 `--tags` expansion from diagnosis.

---

## 5. What this PR ships

1. **This document** — walls, buckets, backlog, and **§8 A+ off the pipe**.
2. **`src/judgment/symbol_state.py`** (default-off research):
   - `assemble_symbol_state_v0` wraps `assemble_gold_state_v0`
   - XAUUSD keeps `schema = gtos.judgment.gold_state.v0` (gold lab comparable)
   - other symbols use `gtos.judgment.symbol_state.v0` with the same body keys
   - `generality.xau_peer_d1.policy = not_substituted`
   - `generality.macro.{dxy,yields,news_protocol}` named absences
   - `intent_symbol_state` does not default to XAUUSD
3. **`symbol_fanout_questions()`** — identical alias of `gold_fanout_questions()`.
4. **`src/judgment/aplus_pipe.py`** (default-off research):
   - catalog of Model A frameworks, each `catalog_only_not_on_w7_gate`
   - `assemble_aplus_observe_state` — XAU keeps gold schema; other symbols stay themselves
   - `observe_aplus_candidate` (`APLU-OBS-001`) + fluid inventory stamp; **not** imported from bridge / book_owner / selector
   - observe body carries `setup_grade` / `framework` / `kill_zone` / `poi` (additive; gold `levels.poi` untouched)
   - `maybe_observe_aplus_at_place` — SHADOW helper the host would call after `cost_skip`; default-off; does not mutate `cost_skip`
5. **`judgment/astra/lab/wires/HOST_APLU_OBS_LAND.md`** — how dirty `book_owner` would env-gate + call; do **not** wholesale-copy the host file.
6. **Tests** — gold body keys equal; missing symbol ≠ XAU; GBPUSD A+ stays GBPUSD with all four observe fields; live `intent_gold_state` still defaults; A+ frameworks absent from `BUILT` / `CANDIDATE_BUILT`; helper not imported from book_owner / selector.

**Not shipped:** APPLY on non-XAU, A1 rewire, `bars.normalize_symbol` change, news_spine W7 filter change, selector/scheduler edits, broker path, `--tags` expansion, a W7 generator for `ob_retest` / `fvg_fill`.

---

## 6. Gold path still works (contract)

| Call | Must remain |
|---|---|
| `assemble_gold_state_v0(...)` | Same schema, same sufficiency rules, same EXPOST reject |
| `intent_gold_state` with `symbol=XAUUSD` | Same completeness / geometry as before |
| `intent_gold_state` with **no** symbol | Still defaults XAUUSD (B-2, live A1 unchanged) |
| `compose_shadow` / named wires | Still XAU Challenge APPLY only when existing env+account gates say so |
| `surface.us30_off` | Still `True` on the gold body |

`assemble_symbol_state_v0(symbol="XAUUSD")` must equal the gold object on every gold key (`gold_keys_equal`). Extra keys (`generality`, `schema_symbol`) are additive.

---

## 7. Why gold-first happened (so we do not moralize it)

Owner 2026-09-17: *“we can have it for gold… study all the market of gold from start to finish.”* That is a **lab order**, not a universe cap.

The organism doc made `gold_state.v0` the closed object. Fable implemented that object. Prove bars then counted XAU. The wire was named `f5_xau_…`. Defaults filled in the rest.

Chair ultragoal is all instruments. The cut is: **keep Challenge integers; stop treating XAUUSD as the type of intelligence.**

---

## 8. A+ setups × instruments — off the gate pipe

**Vision:** every A+ setup, on every instrument, rides as a **sleeve** on the same live info flow as fluid gates + Jev observe.

**What “A+” is (and is not).** A+ is Model A `setup_grade` (`Literal["A+","A","B+","B","C"]` at `src/models/analysis_models.py:84`) plus a `framework` (`ob_retest` / `breaker_retest` / `breaker_re_entry` / `fvg_fill` / `session_sweep` / `equal_sweep` at `:99-114`). It is **not** a Jev type, not a KEEP family, and not a W7 `TradeIntent.sleeve`.

Two stacks never meet:

```
CATALOG (A+ lives here)                         PIPE (Jev / fluid live here)
Primary Analyzer  →  Gate1 (A+/A)  →  Selector V4
  prompt setup_grade "A+" for CANDIDATE           W7 generator → TradeIntent
  enabled_frameworks catalog                      → bridge.admit_and_size (UB-AUTH-010)
  live_activation_allowed: false                  → book_owner._spread_cost_screen (UB-PLC-017)
  SEL-V4-002 research-only, R2-bound              → observe_fluid_inventory (48 fluid)
                                                  assembler: intent_gold_state → default XAUUSD
```

`TradeIntent` (`admission.py:832-867`) has `sleeve`, `symbol`, A8 metals fields, `vr`. It has **no** `setup_grade`, **no** `framework`, **no** `kill_zone`. A PA CANDIDATE cannot enter `admit_and_size` without a sleeve adapter that does not exist.

### 8.1 Gold-only walls (A+ can exist, but intelligence is XAU-shaped)

These starve non-gold A+ even if a later adapter put the packet on the pipe.

| ID | Site | Choke |
|---|---|---|
| D-1 | `src/judgment/a1_log.py:212,286,310,323,343` | Every live observe (`maybe_observe_ub_auth_010`, `maybe_observe_ub_plc_017`, `maybe_observe_fluid_at_place`, `observe_sel_v4_002`) assembles via **`intent_gold_state`**. Missing symbol → `"XAUUSD"`. A GBPUSD A+ observed on this path is judged as gold. |
| D-2 | `src/components/primary_analyzer.py:305-316` | KB context assembled **only** when `symbol == "XAUUSD"`. Non-gold A+ prompts are empty-KB by construction. |
| D-3 | `src/components/orchestrator.py:9401-9404` | `_get_instrument_expertise` returns `_XAUUSD_EXPERTISE` or `""`. Gold W-shape must not be pasted onto FX. |
| D-4 | `src/components/market_state.py:1434` | Session ATR / Ibikunle W-shape only if `symbol == "XAUUSD"`. |
| D-5 | `src/components/permissions.py:101` | `check_permissions(..., symbol="XAUUSD")` default. Gate1 on a omitted symbol is a gold-scoped call. |
| D-6 | `src/components/ultimate_book/sleeves/metals.py:31` | Closest *mechanical* cousin of A+ geometry (H4 FVG-retest) is `ON_SURFACE` = six metals. Not Model A grade; not 24-symbol. |
| D-7 | `src/judgment/sleeve_from_tape.py:64-152` | Observe features on the pipe are metals A8 / `ac60`, applied to **every** Challenge tag. An A+ `ob_retest` packet that fell onto today’s assembler would wear metals cliffs, not framework/POI/grade. |
| D-8 | `src/judgment/wire_prove.py:96,132` | Prove counts `_sym == "XAUUSD"` only. A non-gold A+ tilt cannot prove. |

### 8.2 Catalog-only walls (A+ never becomes a sleeve on the pipe)

These keep A+ off `admit_and_size` / cost-screen / fluid / Jev even on gold.

| ID | Site | Choke |
|---|---|---|
| E-1 | `src/models/analysis_models.py:84,99-114` | Grade + framework live on `PrimaryAnalysisOutput`, not on `TradeIntent`. |
| E-2 | `config/agent_config.yaml:434` | `enabled_frameworks: ["ob_retest", "fvg_fill", "breaker_re_entry"]` — catalog, not a registry. |
| E-3 | `src/prompts/primary_analyzer_prompt.py:713,770` | Prompt law: `setup_grade` is always `"A+"` for CANDIDATE (C-gate **is** the quality gate). Grade is a prompt token, not a sleeve admission bit. |
| E-4 | `src/components/permissions.py:2071-2074` | Gate1 `below_grade_threshold` if grade not in `(A+, A)`. This is the **PA path**. W7 intents never carry a grade, so they never pass through this gate. |
| E-5 | `config/agent_config.yaml:762-764` | `selector_v4_enabled: true` but `apply_to_execution: false` and `live_activation_allowed: false`. V4 packets compute; they do not fire. |
| E-6 | `src/judgment/host_sites.py:52-61` + `a1_log.py:13-14,340-344` | `SEL-V4-002` is research-only. **Do not import from `selector_v4.py`** (R2 / H1). The selector engine is multi-symbol; the Jev hook is unbound and gold-defaulted. |
| E-7 | `src/components/ultimate_book/sleeves/registry.py:47-96,119-127` | `BUILT` = 11 mechanical W7 sleeves. `CANDIDATE_BUILT` is **explicit opt-in** (`include_candidate_book`). Neither table contains `ob_retest`, `fvg_fill`, `breaker_re_entry`, or `aplus_*`. `active_specs` cannot yield an A+ framework. |
| E-8 | `config/live_armed_set.json:21-25,34-38` | Armed `--tags` = `crypto`, `energy_agri`, `sub_xvol_pullback`. Owner integer. `--tags` can only **subset** BUILT (`registry.py:144`). It cannot add a catalog framework. |
| E-9 | `src/judgment/family.py:11,43-45` | `KEEP_FAMILIES = spring / vss`. A+ is not a keep tag. `family_class_for("aplus_ob_retest")` is `other_tagged`. |
| E-10 | `src/components/ultimate_book/bridge.py:612-613` + `book_owner.py:2202-2204` | Jev observe is spliced **only** after W7 admit and after W7 cost_skip. No PA / Gate1 observer exists. |
| E-11 | `src/components/pre_ai_gates.py:244-258` | Framework POI / proximity helpers exist for the AI call. They do not emit a sleeve. |

### 8.3 Ranked unlocks — put multi-instrument A+ onto fluid + Jev observe

Priority = what lands A+ × symbol on the **same observe flow** as UB-AUTH-010 / UB-PLC-017 / 48 fluid, without APPLY, without reseal, without inventing feeds, without expanding `--tags`.

| Rank | Unlock | Class | Why this rank | This PR |
|---|---|---|---|---|
| U-1 | Catalog the frameworks as `catalog_only_not_on_w7_gate` | E-1/E-2/E-7 | Stops the next session from treating `ob_retest` as if it were already a sleeve. | **Shipped** `aplus_catalog()` |
| U-2 | Assemble A+ packets with `assemble_symbol_state_v0` (no XAU default; no metals A8) | D-1/D-7 | A GBPUSD A+ must be judged as GBPUSD. Metals A8 must not wear the A+ feature slot. | **Shipped** `assemble_aplus_observe_state` |
| U-3 | Default-off `observe_aplus_candidate` (`APLU-OBS-001`) + `observe_fluid_inventory` | E-10 | Same 48 fluid questions, same never-place stamp, **not** wired to host. Proves the info shape. | **Shipped** stub |
| U-4 | HOST land note: `book_owner` would call `maybe_observe_aplus_at_place` after `cost_skip`, env-gated **before** import | E-10 | Same site as UB-PLC-017. Must **not** wholesale-copy host `book_owner`. Must **not** touch `selector_v4.py`. Not spliced on this tree. | **Shipped note + helper** |
| U-5 | Carry `setup_grade` / `framework` / `kill_zone` / POI on the observe body (additive `aplus` block; gold keys stay comparable) | E-1/D-7 | Fluid questions already path-reference `sleeve_features.*`. Give them A+ names without rewriting `levels.poi`. | **Shipped (shadow)** |
| U-6 | Own-symbol Challenge tape (M15+H4, honest missing D1) for A+ symbols beyond metals | C-2/C-3/D-4 | Observe without tape is insufficient. Do not inject XAU D1. | Tape; later |
| U-7 | Per-class KB / expertise / session ATR — or honest empty | D-2/D-3/D-4 | Gold findings stay gold. Empty ≠ copy XAU. | Later |
| U-8 | Sleeve **adapter** (research): PA CANDIDATE A+/A × symbol → pipe-shaped packet with tag `aplus_<framework>` | E-7/E-8 | Lets `admit_and_size` *see* the row so UB-AUTH-010 / UB-PLC-017 fire without a BUILT generator. Default-off. **No `--tags` change.** | Later; owner word to register |
| U-9 | Fluid re-prove per symbol class before any non-XAU A+ size tilt | D-8/C-9 | Do not APPLY a GBPUSD A+ tilt from an XAU prove receipt. | Later |
| U-10 | Owner decision only: CANDIDATE_BUILT or `--tags` membership | E-8 | Arming is an A0 integer. Diagnosis must not expand the armed set. | **Never this PR** |

**Still KEEP (do not “unlock” A+ by lifting these):** envelope walls (A-1), `us30_off` fire surface (A-2), Challenge APPLY login/ns (A-5), `books_for_symbol` no-XAU-substitute (A-8), R2 bind on `selector_v4.py` (E-6), armed-set single source (`live_armed_set.json` + launcher).

**Still do not invent:** DXY, yields, `NEWS_PROTOCOL`. Flag `unassembled` / `not_invented` (already on `symbol_state.generality.macro`).

### 8.4 Gold A+ contract (so the first study does not regress)

| Call | Must remain |
|---|---|
| Gold A+ `ob_retest` observe | `schema = gold_state.v0`, `identity.symbol = XAUUSD`, `surface.us30_off = True`, gold body keys equal a gold assemble with the same sleeve/geometry |
| `aplus.setup_grade` / `framework` / `kill_zone` / `poi` | Additive block. Must not mutate gold keys. `levels.poi` stays the gold None. |
| `intent_gold_state` missing symbol | Still defaults XAUUSD (D-1 / B-2). Live A1 unchanged. |
| `observe_aplus_candidate` / `maybe_observe_aplus_at_place` | Default-off; `never_place`; **not** imported from bridge / book_owner / selector |
| Gate1 A+/A | Still the PA safety gate. Stub does not bypass it and does not fire W7. |
| Envelope / `--tags` | Unchanged. Land note forbids soft-open and arm expansion. |
