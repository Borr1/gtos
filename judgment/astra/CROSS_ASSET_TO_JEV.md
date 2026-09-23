# Cross-asset / liquidity narrative → Jev

**Date:** 2026-09-18  
**Schema:** `gtos.judgment.cross_asset.v0` / `gtos.judgment.world_state.v0`  
**Surface:** Challenge `0` / `$110k` / magic `0` / ns `operator`  
**Status:** stubs + offline prove harness. Jev never places.

Owner law this pack implements: *if a trade was wrong, a state was missing or a calculation was wrong.* Gold-vs-rates, risk-on funding, and occupancy-across-book must be **typed fields** on `world_state`, not prose in a prompt. Empty ≠ zero. Missing peer tape stays `unassembled`.

Physical size stays **flow × cost** until a *new* cross-asset wire is `PROVED_SHADOW` and then `APPLIED_NAMED`. Envelope walls stay integers.

---

## 0. Survey (this clone, 2026-09-18 — after chair zip)

### 0.1 Challenge-true bar drops

| Symbol | Challenge M15 | Challenge H4 | Challenge D1 | Notes |
|---|---|---|---|---|
| `XAUUSD` | **landed** (1597 parent) | **landed** (75) | **landed** (56) | parent `challenge_shadow_20260917/` is identity; zip XAU (2000 / last 09-18T01:30Z) is unused |
| `EURUSD` | **landed** (2000) | **landed** (500) | — | zip `multi/`; last **2026-09-18T03:00:00Z** |
| `GBPUSD` | **landed** (2000) | **landed** (500) | — | same |
| `USDJPY` | **landed** (2000) | **landed** (500) | — | same |
| `US30` | **landed** (2000) | **landed** (500) | — | aliases `US30_cash` / `US30.cash` / `US30`; harness prefers `US30_cash` |
| `UK100` | missing | missing | missing | stem `UK100_cash` |
| `EURGBP` | missing | missing | missing | |
| `BTCUSD` / `ETHUSD` | missing | missing | missing | house_hard_off as a **fire** surface; optional risk-on peer only if later landed |

`landed_challenge_symbols()` = `["XAUUSD", "EURUSD", "GBPUSD", "US30", "USDJPY"]` **on this Cloud VM after the chair zip**.  
Chair 2026-09-18 first pass: VPS multi paths for EURUSD / GBPUSD / USDJPY (`time_utc` = server−3h, through ~2026-09-18T03:00Z); US30 FTMO resolve failed. Chair then attached `_peer_multi_20260918.zip` (same VPS tree, plus US30 aliases). Unzipped into `judgment/astra/lab/challenge_shadow_20260917/multi/`. This VM still has no host-admin/host-mesh/`~/.gtos/vps.env`. `copy_multi_csvs_if_present()` copied **0**. Peer CSVs are **not committed**. April `exports/multi_instrument/*` last-print 2026-04-03 and fail the admit gate (no `time_utc`).

`books_for_symbol` will **not** substitute XAU for another pair. A GBPUSD row without a GBPUSD Challenge CSV gets no M15/H4. That is correct. XAU identity stays the parent drop even when zip XAU is present (`CHALLENGE_BAR_DIR` is searched first).

April `data/historical*` and `exports/multi_instrument/*` **exist** (EURUSD / GBPUSD / USDJPY / US30 M15 through 2026-04). They are **not** Challenge-true. The prove harness must not wear them. `data/DXY_D1.csv` exists (515 rows, 2024-02-29 → 2026-04-02) and is **not** a prove source — G7 already demoted official DXY to soft context and called this file stale.

### 0.2 Occupancy (already multi-symbol)

Deal tape `deals_since_20260909.jsonl` (47 positions / 46 closed / 1 open):

| Cluster | Symbols on tape | n |
|---|---|---|
| metals | XAUUSD | 22 |
| index | US30 (14), UK100 (2) | 16 |
| fx_major | EURUSD, GBPUSD, EURGBP | 6 |
| crypto | BTCUSD, ETHUSD | 3 |

Slate `bddc8ff9fad4a254` candidates: USDJPY 14 / EURUSD 9 / XAUUSD 9 / GBPUSD 7 / BTCUSD 1.

`occupancy_at` already varies by symbol. `corr_hold_named` already flags same-cluster siblings. `occupancy_book_at` (this pack) counts **clusters_open** / **book_open_n** across the book. KEEP-one and the 2-stop COUNT stay envelope integers.

### 0.3 What can be typed *today* vs what waits on a chair pull

| Narrative | Typed today? | Blocker |
|---|---|---|
| Occupancy across FX / metal / index | **yes** — deal tape | — |
| Session liquidity (overlap / thin) | **yes** — clock | — |
| Event-join USD/GBP/JPY/EUR HIGH | **yes** — host spine | empty spine ≠ no HIGH |
| Gold co-moves with USD | **yes on this VM (label)** | zip FX M15 landed; CA-USD/CORR `PROVED_SHADOW`, apply stays false |
| Risk-on funding | **yes on this VM (label)** | zip US30 + USDJPY; CA-RSK `PROVED_SHADOW`, apply stays false |
| Gold co-moves with US30 | **yes on this VM (label)** | zip US30; CA-IDX `PROVED_SHADOW`, apply stays false |
| Real rates / DXY official | **never on this tape** | no FRED; DXY file is not Challenge-true |

---

## 1. CROSS_ASSET_FEATURES_V0

Closed object. Path-reference in questions: `` `world.usd_proxy.named` ``, `` `world.gold_vs_usd.corr.w32` ``, `` `world.occupancy_book.n_clusters_open` ``.

```
schema: gtos.judgment.cross_asset.v0
```

Nested under `gold_state.world` (also `gtos.judgment.world_state.v0`). Missing blocks stay visible. `state_sufficient_for_live` does **not** require peers — a gold fire can still be judged on XAU M15+H4.

### 1.1 Peers

`world.peers.<SYMBOL>` = compact M15 snap (`present`, `last_close`, `last_utc`, `trend`, `close_vs_close_n_atr`, `source_path`). Priority: EURUSD, GBPUSD, USDJPY, US30, UK100, EURGBP. Absence is `present: false`, not a borrowed XAU close.

### 1.2 USD proxy (no paid DXY)

Equal-weight FX basket already MT5-exportable:

```
usd_ret = mean( -ret(EURUSD), -ret(GBPUSD), +ret(USDJPY) )
```

Need **≥ 2** members and ≥ 8 overlapping M15 log-returns. Otherwise `named = unassembled` (not `usd_flat`, not `0.0`).

| Field | Type |
|---|---|
| `usd_proxy.named` | `usd_up \| usd_down \| usd_flat \| unassembled` |
| `usd_proxy.ret` | mean log-return or null |
| `usd_proxy.members_present` | list |
| `usd_proxy.source` | `fx_majors_equal_weight \| unassembled` |
| `usd_proxy.dxy_used` | always `false` on Challenge prove |

### 1.3 Rates / funding stand-in

No FRED. `rates_proxy` is USDJPY trend: `yen_offered` / `yen_bid` / `flat` / `unassembled`. USDJPY **alone** is not risk-on.

### 1.4 Risk-on

Needs US30 **and** the yen label.

| US30 trend | USDJPY | `risk_on.named` |
|---|---|---|
| +1 | yen_offered | `risk_on` |
| −1 | yen_bid | `risk_off` |
| present, else | — | `mixed` |
| US30 missing | — | `unassembled` |

### 1.5 Correlation windows

Pearson on aligned M15 log-returns. Slack 15 minutes. Windows **16 / 32 / 96**. `n < 8` or zero variance → `null`, never `0.0`. Named from **return-space** Pearson (band ±0.25 on w32, else w16), not from both-up levels. A constant-dollar arithmetic ramp can invert the name (increment magnitudes decay as price rises); a constant log-return path is undefined (var = 0). Fixtures use a shared varying return series.

- `gold_vs_usd.named`: `gold_with_usd` / `gold_against_usd` / `mixed` / `unassembled`
- `gold_vs_index.named`: `gold_with_us30` / `gold_against_us30` / `mixed` / `unassembled`

### 1.6 Session liquidity flags

Clock only. Not invented volume.

| `utc_hour` | `named` | overlap | thin |
|---|---|---|---|
| Fri ≥ 16 | `friday_cutoff` | no | yes |
| ≥ 21 or 0 | `dead` | no | yes |
| 12–16 | `overlap_london_ny` | yes | no |
| 16–21 | `ny` | no | no |
| 7–12 | `london` | no | no |
| 0–7 | `asia` | no | yes |

### 1.7 Event-join

From the named news spine only. F5 window T−60 … T+15.

`usd_high_in_window` / `gbp_high_in_window` / `jpy_high_in_window` / `eur_high_in_window` / `minutes_to_nearest_usd` / `joined_currencies`.

`spine_empty: true` → all of those are **null**. Empty spine is not “no HIGH.”

### 1.8 Occupancy book

`clusters_open.{metals,fx_major,index,crypto}` + `book_open_n` + `n_clusters_open` + `symbols_open`. Source `challenge_deals` or `deal_tape_absent`.

This is a **label**. It does not KEEP, HOLD, remint, or flatten.

---

## 2. Jev questions (typed, research-only)

Added to the fan-out. **Not** in the 48-fluid inventory. They cannot APPLY size.

| ID | Primitive | State path | Ignore when |
|---|---|---|---|
| `gold_usd_comove` | Choice `with_usd \| against_usd \| no_clear` | `world.gold_vs_usd` | unassembled |
| `gold_index_comove` | Choice `with_us30 \| against_us30 \| no_clear` | `world.gold_vs_index` | unassembled |
| `risk_on_funding` | Choice `risk_on \| risk_off \| mixed` | `world.risk_on` | unassembled |
| `session_liquidity` | Score 0–2 | `world.session_liquidity` | clock missing |
| `occupancy_world` | Score 0–2 | `world.occupancy_book` | tape absent |

Local (no-Jev) instruments live in `src.judgment.cross_asset.local_cross_asset_answers`.

---

## 3. Prove → APPLY ladder

Same lock as Wave E/M: **shadow score first, then wire.** Frozen bars = fluid label (`min_decidable=20`, `min_non_default=5`, `min_distinct=2`). Invented HIGH forbidden. Cannot refuse. Cannot stack a new size axis on `live_flow × live_cost`.

```
NOT_PROVED
    → chair lands named Challenge M15 (if the target needs peers)
    → offline harness on Challenge shadow pack
    → PROVED_SHADOW (label only)
    → owner NAME / preauth (size_tilt or label; never place / remint / flatten)
    → APPLIED_NAMED
```

Envelope walls (`ENV-OCC`, `ENV-US30`, 2-stop COUNT, token, H8, dead-window writer clock) are **not** on this ladder.

### 3.1 Targets

| ID | Question | Needs | This pack (97 shadow rows, after chair zip) |
|---|---|---|---|
| **CA-OCC-001** | `occupancy_world` | deal tape | **PROVED_SHADOW** — 97 / 31 / vals 0,1,2 — apply false |
| **CA-LIQ-001** | `session_liquidity` | clock | **PROVED_SHADOW** — 97 / 30 / thin·ordinary·overlap — apply false |
| **CA-EVT-001** | event-join HIGH-by-currency | news spine | **PROVED_SHADOW** — 97 / 4 HIGH-in-window — apply false |
| **CA-USD-001** | `usd_proxy.named` | EURUSD+GBPUSD+USDJPY Challenge M15 | **PROVED_SHADOW** — 97 / 97 / usd_flat 35, usd_up 56, usd_down 6 — **apply false** |
| **CA-CORR-001** | `gold_usd_comove` | same FX M15 + XAU | **PROVED_SHADOW** — 97 / 32 / against_usd 32, no_clear 65 — **apply false** |
| **CA-RSK-001** | `risk_on_funding` | US30 + USDJPY Challenge M15 | **PROVED_SHADOW** — 97 / 97 / mixed 92, risk_off 2, risk_on 3 — **apply false** |
| **CA-IDX-001** | `gold_index_comove` | US30 Challenge M15 | **PROVED_SHADOW** — 97 / 87 / with_us30 87, no_clear 10 — **apply false** |

Even a `PROVED_SHADOW` occupancy/session/event label does **not** change lots. APPLY of a *size* effect requires a later named wire and still cannot zero a fire.

### 3.2 Harness

```bash
python3 scripts/jev_cross_asset_prove.py
```

Reads `judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl` + deals. Writes:

- `judgment/astra/lab/wires/CROSS_ASSET_SURVEY_V0.json`
- `judgment/astra/lab/wires/CROSS_ASSET_PROVE_V0.json`

`--no-write` prints the same payload without touching disk.

---

## 4. Code map

| Piece | Path |
|---|---|
| Feature math | `src/judgment/cross_asset.py` |
| World assembler | `src/judgment/world_state.py` |
| Occupancy book | `src/judgment/occupancy.py` `occupancy_book_at` |
| gold_state nest | `src/judgment/gold_state.py` `world` |
| Challenge attach | `src/judgment/challenge_shadow.py` via `load_peer_books` + `deal_tape` |
| Live A1 attach | `src/judgment/a1_log.py` `intent_gold_state` |
| Questions | `src/judgment/jev_questions.py` |
| Local answers | `src/judgment/fluid_local.py` |
| Harness | `src/judgment/cross_asset_prove.py` / `scripts/jev_cross_asset_prove.py` |
| Named CA size (shadow) | `src/judgment/ca_size.py` / `src/judgment/ca_size_prove.py` / `scripts/jev_ca_size_prove.py` |
| Tests | `tests/judgment/test_cross_asset.py`, `tests/judgment/test_ca_size.py` |

Loader already ready: `bars.books_for_symbol`, `copy_multi_csvs_if_present`, `scripts/jev_copy_challenge_multi_bars.py`. Chair pull list item 7 is still the land.

---

## 5. Next prove targets (ordered)

1. ~~Hydrate this VM from the VPS multi drop.~~ **Done 2026-09-18** via chair zip (`CHAIR_PEER_HYDRATE_20260918.md`). FX + US30 aliases admitted. April still refused.
2. ~~Re-run prove.~~ **Done.** Four flips to `PROVED_SHADOW`: CA-USD-001, CA-CORR-001, CA-RSK-001, CA-IDX-001. OCC/LIQ/EVT unchanged. **No CA-\* APPLY.**
3. Leave every CA-* target as **label**. A size tilt on gold-vs-USD / risk-on / US30 is a *new* wire — not pre-authorized by “apply everything yes” on flow/cost.
4. Optional later peers: UK100 / EURGBP (not required for the seven CA-* targets). Do not lower bars.
5. **Named size wire (this pack):** `ca_cross_asset_size_tilt` / `CA-SIZ-001`. Shadow scores the seven PROVED labels onto veto-class `[0.70, 1.00]`. Live stays 1.0. APPLY stays false. Physical lots stay flow × cost. Receipt `CA_SIZE_SHADOW_WIRE.md`. Chair zip re-run 2026-09-18T04:11:01Z: USD/CORR/RSK/IDX now assemble; USD/RSK/IDX move tilts; CORR is `against_usd` (tilt 1.0). Chair/owner later may NAME; this pack does not.
6. Only after Chair/owner NAME: compose may multiply flow × cost × *that* — never a fourth silent multiplier. Never place.

---

## 6. What this pack refuses to do

- Place, remint, flatten, move SL, write inbox.
- Invent HIGH / FOMC / NFP rows.
- Treat `data/DXY_D1.csv` or FRED as Challenge-true.
- Wear April historical as Challenge tape.
- Substitute XAU M15 for FX/index.
- Encode 0.0 correlation as “no co-move.”
- Let occupancy_world become KEEP-one or a third-stop counter.
- Change `us30_off` / hard-off families.
- Stack physical size before a named APPLY.
