# Symbol state schema draft — closed object for ANY Challenge primary

**Date:** 2026-09-18
**Status:** Draft + assembler. Shadow / research. Not a live client. Not a NEWS invent.
**Sibling of:** [`JEV_GOLD_STATE_SCHEMA_DRAFT.md`](JEV_GOLD_STATE_SCHEMA_DRAFT.md) (`gtos.judgment.gold_state.v0`).
**Chair land:** [`lab/wires/HOST_SYMBOL_STATE_V0.md`](lab/wires/HOST_SYMBOL_STATE_V0.md).
**Clock:** broker wall = `America/New_York + 7h`. Challenge `time_utc` is already −3h. Never April historical.
**Account surface:** login `0`, pass `$110k`, magic `0`, ns `operator`.

This is the object Jev sees when the primary is **not only XAUUSD**. Question IDs stay
the gold fan-out. Code fills facts. Jev answers Choice / Score / Noul. Chair
ENFORCE / VETO / LABEL. Jev never places, remints, or flattens.

```
schema: gtos.judgment.symbol_state.v0
sibling_of: gtos.judgment.gold_state.v0
```

Assembler: `src.judgment.symbol_state.assemble_symbol_state_v0`.
Asset-class map: `src.judgment.symbol_class.field_map()`.
A+ sleeve object: `src.judgment.a_plus_sleeve.attach_sleeve_object`.

---

## 0. Owner vision lock — A+ sleeve on gate flow

**A+ setups for literally every instrument become sleeves.** Those sleeves sit
on the **same gates + information flow** as live Challenge. They are **not**
a side catalog.

Named lock: **`a_plus_sleeve_on_gate_flow`**.

| Must | Must not |
|---|---|
| Per-symbol A+ library is a first-class `gtos.judgment.sleeve.v0` object | A parallel “setup catalog” that Jev scores off-pipe |
| Fluid / admit / selector / size-observe consume `symbol_state.v0` | A second inventory, a chat LLM, or a new NEWS protocol |
| CA labels may enrich **any** sleeve (`sleeve.ca_labels`) | Invent DXY / yields / order book |
| SHADOW / observe first | Place, remint, flatten, or silent APPLY |

Pipe (same functions live Challenge already uses):

```
assemble_symbol_state_v0
  → observe_fluid_inventory          # fluid
  → observe UB-AUTH-010 / FLUID-ADM-*  # admit
  → observe_sel_v4_002               # selector (research-only, unbound)
  → compose_shadow                   # size observe
```

Scout+Edge Chair wires (SHADOW) fold into peers / sessions / clock / sleeve
labels. They do not APPLY and they do not invent DXY or TIPS.

`identity.sleeve` is the tag. `state.sleeve` is the object. `state.gate_flow.name`
is always `a_plus_sleeve_on_gate_flow`. Existing Challenge tags
(`dsp_two_bar_t`, `vss_fxcross_*`) wrap as `library=challenge_live`.
A+ tags (`aplus_*`) wrap as `library=per_symbol_a_plus`, `family_class=a_plus_study`,
`observe_only=true`. Both ride the same pipe.

Library stubs live in `A_PLUS_LIBRARY_V0` (XAUUSD, EURUSD, USDJPY, GBPJPY, US30,
GBPUSD). A row names a sleeve slot. It is **not** a generator and it does **not**
fire. US30 house-off stays on `surface.us30_off` — an A+ US30 sleeve is observe
only and does not lift the cut.

Silent APPLY is forbidden: `aplus_*` on XAUUSD still has
`named_apply_symbol=false`. Owner names a wire; then prove; then APPLY.

---

## 0b. Closed-object rules (same as gold)

1. One JSON object per candidate. Missing stays visible (`completeness.missing_fields`).
2. No realized PnL on `live_intent`. `EXPOST_KEYS` raise.
3. Code fills family / geometry / cost / sessions. Jev does not reclassify a known sleeve.
4. News is fail-closed. Filter the **landed** spine by pair currencies. Do not invent HIGH rows. Do not invent `NEWS_PROTOCOL`.
5. Empty ≠ zero. Unassembled peer is `present=false` + `source=unassembled`, not a fake 0.0 comove.
6. Clock block is mandatory. Same `new_york_plus_7` rule.
7. Physical size APPLY is **XAU-only** until a named non-XAU wire is PROVED.
   A+ sleeves never silent-APPLY, including on XAUUSD.

Never invent: DXY, US10Y, TIPS, order book, NEWS_PROTOCOL.

---

## 1. Universal vs asset-class specific

### Universal (every primary — same blocks as gold_state)

`identity`, `clock`, `sessions`, `timeframes`, `levels`, `news`, `sleeve_features`,
`geometry`, `cost`, `occupancy`, `governor`, `surface`, `completeness`.

M15+H4 required for `state_sufficient_for_live`. D1 optional for non-XAU
(the multi drop has no D1). Missing D1 is listed; it does not TF-abstain.

`surface.us30_off` is always true. `surface.apply_named_wires` is true only
for XAUUSD. `surface.symbol_state_observe_only` is true for every other primary.

### Class-specific

| Class | Symbols (code facts) | Extra fields |
|---|---|---|
| **fx** | 6-letter pairs whose legs are in `{EUR,GBP,USD,JPY,AUD,NZD,CAD,CHF}` | `pair.{base,quote}`, `usd_leg` (`base` / `quote` / null), `usd_from_pair` (H4 trend mapped onto USD strength — **not DXY**), `session_bias`, `pip_scale` (0.01 JPY quote, else 0.0001), `relevant_news_ccys` |
| **metal** | XAUUSD, XAGUSD | `usd_sensitivity=usd_proxy_only`, `a8_source`, `ac60`, `vol_ratio`, `peer_usdjpy_present` |
| **index** | US30, UK100, NAS100, SPX500, GER40, JP225, EU50, FRA40 | `cash_alias` (`US30.cash` / `UK100.cash`), `house_us30_off=true`, `session_bias` |
| **crypto** | BTCUSD, ETHUSD | `trade_surface=house_hard_off_not_a_fire` |
| **energy** | USOIL, UKOIL | `weekend=energy` |

Crosses without a USD leg (GBPJPY, EURJPY) still see USD HIGH on the host
spine (risk-off). That is a filter on existing rows, not a new protocol.

USD proxy: `usd_from_pair_trend(EURUSD, +1) = −1` (EUR up → USD weaker);
`usd_from_pair_trend(USDJPY, +1) = +1`. No DXY series is read or invented.

---

## 2. Peers (rewrite of `not_xau_primary`)

PR #15 stamped `usdjpy.source=not_xau_primary` when the primary was not XAU.
That is a dead end. This assembler never emits that source.

Each primary has a named Challenge / 24-surface peer set
(`symbol_class.PEERS_BY_SYMBOL`). Missing tape →

```json
{ "present": false, "m15_atr14": null, "h4_trend": null, "comove_20": null, "atr_ratio": null, "source": "unassembled" }
```

Present tape (Challenge CSV only):

```json
{ "present": true, "m15_atr14": 0.12, "h4_trend": 1, "comove_20": 0.41, "atr_ratio": 1.02, "source": "challenge_csv" }
```

`comove_20` is Pearson of 20 aligned M15 simple returns. A single-tf primary
book dict is **never** reused as a peer cache (that would wear USDJPY bars as XAU).

XAUUSD + USDJPY still expose `xau_usdjpy_comove_20` when PR #15 `peers.py`
is on the tree and does not say `not_xau_primary`.

Peers never flip `state_sufficient_for_live`. Absence is `missing_fields: ["peers"]`.

---

## 3. News

`gold_state` already attaches the landed spine. `symbol_state` adds:

- `relevant_currencies` — pair / index / metal currencies already on the spine
- `pair_high_events` — spine events whose `currency` is in that set
- `pair_high_in_f5_window` — any pair HIGH in T−60..T+15
- `pair_high_n`

`spine_empty` still means “we do not have a calendar,” not “there is no HIGH.”
Do not overwrite June `data/news_calendar.json`. Do not invent endpoints.

---

## 4. Completeness

Gold flags are copied. Added:

| Flag | Meaning |
|---|---|
| `asset_class` | symbol mapped (not `unknown`) |
| `class_specific` | class block assembled |
| `peers` | at least one named peer `present` |
| `news_pair_ccy` | `relevant_currencies` non-empty |
| `world` | WORLD_STATE_V0 / CA attached (not `unassembled`) |
| `chair_wires` | Scout+Edge SHADOW block assembled (`apply` stays false) |
| `state_sufficient_for_live` | **gold predicate only** (identity + M15+H4 + geometry + family ≠ unknown) |
| `missing_fields` | gold list + `peers` / `class_specific` when those blocks are empty |

`expost_rejected` on `live_intent` raises `ValueError`.

---

## 5. World / CA (optional)

When `src.judgment.cross_asset` (PR #13) or `src.judgment.world_state` (PR #12)
is importable, `_maybe_world` attaches it. Gold books are passed only for
XAUUSD (never substitute XAU tape as another pair).

Absent on this branch:

```json
{ "schema": "gtos.judgment.world_state.v0", "source": "unassembled", "dxy": null, "rates": null, "never_invent_dxy": true, "never_invent_yield": true }
```

---

## 6. Intent / shadow wiring

- `intent_symbol_state` — always `symbol_state.v0`.
- `intent_gold_state` — XAUUSD stays `gold_state.v0`; every other primary
  returns `symbol_state.v0` (no `not_xau_primary` dead end).
- `challenge_shadow.score_position` — XAU uses gold assembler; else symbol
  assembler + `load_peer_books_for`.
- `compose_shadow` — `named_apply_symbol` iff identity symbol is XAUUSD.
- `apply_named_tilts` / `maybe_haircut_unit` — refuse non-XAU physical scale.

XAU rows nest the gold object at `gold_state`. Non-XAU set that key `null`.

Every row also carries `sleeve` + `gate_flow`. A1 `observe` / `observe_fluid_inventory`
already consume that typed state — no second caller. `observe_a_plus_on_gate_flow`
is the named stub that runs the same pipe and stamps `never_place` /
`never_silent_apply`.

---

## 7. Scout+Edge Chair wires (SHADOW)

Assembler: `src.judgment.chair_wires.assemble_chair_wires`.
Schema: `gtos.judgment.chair_wires.v0`. `apply: false` always.

| Wire | Fold | Inputs | Labels |
|---|---|---|---|
| `usd_proxy_vs_xau` | `peers.usd_proxy_vs_xau`, `class_specific.metal` | EURUSD + USDJPY H4 mapped with `usd_from_pair_trend` (not DXY) vs XAU H4 | `agree` / `disagree` / `flat` / unassembled |
| `gbpjpy_dual_leg_agree` | `peers.gbpjpy_dual_leg_agree` | GBPUSD + USDJPY H4 vs GBPJPY H4 | `agree` / `disagree` / `legs_agree` / `legs_disagree` |
| `us30_rth_vs_eth` | `sessions.us30_rth_vs_eth`, index block | `sessions.named` (`ny` → rth, else eth) | house `us30_off` stays true |
| `usdjpy_tokyo_event_liquidity` | `class_specific.fx` | Tokyo/Asia clock + `pair_high_in_f5_window` on the landed spine | `tokyo_pair_high` / `tokyo_quiet` / `tokyo_clock_spine_empty` / `outside_tokyo` |
| `fx_session_london_fit` | `sessions` + fx block | `named==london` and asset is fx | `fit` / `outside` / `not_fx` |
| `sess.ldn_ny_overlap_vol` | `sessions.ldn_ny_overlap_vol` | M15 volume in 12–16Z vs last-20 mean | empty ≠ zero |
| `corr.eur_gbp_usd_co_move` | `peers.corr` | `comove_20(EURUSD, GBPUSD)` | float or null |
| `corr.xau_vs_eur_proxy_usd` | `peers.corr` | `comove_20(XAUUSD, EURUSD)` | float or null — EUR as USD proxy, not DXY |
| `tokyo_fix_window_label` | `clock.tokyo_fix_window_label` | 00:45–01:15 UTC (9:55 JST). Clock only. | `tokyo_fix` / `outside` — hour 0 is still `dead_21_00z` on `sessions.named` |

`sleeve.ca_labels.labels` copies the same labels so CA can enrich any sleeve.
`completeness.chair_wires` is true when the block assembled. It does **not**
flip `state_sufficient_for_live`. Missing peer tape stays `source=unassembled`.

PACK 4 paths stay SHADOW on **both** `symbol_state.v0` and `gold_state.v0`
(`apply_pack4_fold`): `session.in_ldn_ny_overlap`, `london_expand_*`,
`ny_rth_us30`, `cluster.eur_gbp`, `cross.gbpjpy`, `information.boj_bucket`.
USD proxy is **USDJPY-primary**; `xau_eur_proxy` aliases only when USDJPY is null.

**Chair FREEZE.** `sleeve.gbpjpy_a_plus_ready` / `sleeve.xau_dsp_shakeout_ready`
are Choice `{a_plus, almost, blocked, null_state}` on both assemblers.
**Never admit.** GBPJPY conjuncts: session_ok ∧ identity_ok(|resid|≤0.15) ∧
agree ∧ dual_same ∧ boj∉{print,guidance_live}. XAU shakeout uses the same
shape with event_gap fail-closed and `usd_proxy_vs_xau` via `peers.usdjpy`
primary. BOJ 1.25% effective 2026-09-24 is timing only unless a spine stamp
exists — no NEWS_PROTOCOL invent, no fake print/guidance. Edge t1–t4 pin it.

---

## 8. Fixtures the tests pin

XAUUSD (landed Challenge CSV), EURUSD, USDJPY, US30, GBPJPY (synthetic
M15+H4+D1). Each is sufficient when tape is present; each refuses EXPOST on
`live_intent`; none emit `not_xau_primary`; EURUSD cannot haircut size with
`GTOS_JEV_APPLY_LIVE=1`.

SHADOW unlock remasure: **`n_non_xau_sufficient=45`** on EURUSD / USDJPY /
GBPUSD / EURGBP + US30 hard-off (9 as_ofs). Those rows use
`symbol_state.v0` on the observe pipe — not gold-defaults. Landed XAU
`shadow.summary.json` stays `n_non_xau_sufficient=0`. US30 remains
house hard-off. No place. No named APPLY.
