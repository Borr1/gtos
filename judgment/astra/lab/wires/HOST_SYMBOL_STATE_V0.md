# HOST SYMBOL_STATE_V0 — Chair land (observe / SHADOW)

Tip on this branch after review: land **`src/judgment/`** onto Challenge f5-live
(`0` / `operator` only) so Jev can **score** any Challenge
primary, not only XAU. Do **not** wholesale-copy GitHub `book_owner.py` onto
the dirty host. Do **not** remint. Do **not** flatten. Do **not** place from Jev.

This wave is **typed state + observe**. Physical size APPLY on non-XAU stays
**off**. Named APPLY wires (`f5_xau_flow_alignment_size_tilt`, `F5-JEV-004`)
remain **XAUUSD-only** until a named non-XAU wire is PROVED.

## Owner vision lock — A+ sleeve on gate flow

A+ setups for **every** instrument become **sleeves** on the **same**
Challenge gate pipe. Not a side catalog.

1. Per-symbol A+ library → first-class `state.sleeve` (`gtos.judgment.sleeve.v0`).
2. Fluid / admit / selector / size-observe consume `symbol_state.v0` (same
   `observe_*` + `compose_shadow` as live).
3. CA labels enrich any sleeve (`sleeve.ca_labels`). Never invent DXY.
4. SHADOW / observe first. No place. No silent APPLY (`aplus_*` even on XAU).

Named: `gate_flow.name = a_plus_sleeve_on_gate_flow`.
Copy also `src/judgment/a_plus_sleeve.py`, `family.py`, and `chair_wires.py`.
Chair does **not** admit A+ tags onto `--tags` this land. Stubs only.

## Scout+Edge Chair wires — SHADOW only

Folded into `symbol_state.v0` / sleeve fields. **No APPLY. No DXY. No TIPS.**

| Wire | Natural home | What it is |
|---|---|---|
| `usd_proxy_vs_xau` | `peers` + metal | EURUSD+USDJPY H4 → USD proxy vs XAU H4. Not DXY. |
| `gbpjpy_dual_leg_agree` | `peers` (GBPUSD+USDJPY) | Both legs +1 → GBPJPY up. Missing tape = unassembled. |
| `us30_rth_vs_eth` | `sessions` | `ny` → rth, else eth. **House US30 off stays.** |
| `usdjpy_tokyo_event_liquidity` | `class_specific.fx` | Asia/Tokyo clock + pair HIGH on the **landed** spine. |
| `fx_session_london_fit` | `sessions` / fx | `named==london` on an FX primary. |
| `sess.ldn_ny_overlap_vol` | `sessions.ldn_ny_overlap_vol` | M15 volume in 12–16Z. Empty ≠ zero. |
| `corr.eur_gbp_usd_co_move` | `peers.corr` | `comove_20(EURUSD, GBPUSD)`. |
| `corr.xau_vs_eur_proxy_usd` | `peers.corr` | `comove_20(XAUUSD, EURUSD)`. EUR as USD proxy. |
| `tokyo_fix_window_label` | `clock` | 00:45–01:15 UTC (9:55 JST). Clock-only. Not NEWS. |

`state.chair_wires.apply` is always false. Labels also copy onto `sleeve.ca_labels`.
They never flip `state_sufficient_for_live`. They are not fluid inventory gates.

PACK 4 canonical paths (still SHADOW) fold onto **both** `symbol_state.v0`
and `gold_state.v0` via `apply_pack4_fold`: `session.in_ldn_ny_overlap`,
`london_expand_*`, `ny_rth_us30`, `cluster.eur_gbp`, `cross.gbpjpy`,
`information.boj_bucket`. `usd_proxy_vs_xau` uses **USDJPY primary**;
`xau_eur_proxy` is the alias only when USDJPY is null. XAU
`intent_gold_state` / Challenge shadow now carry the same extensions so
the gold path does not drop Chair wires.

**Chair FREEZE** readiness Choice `{a_plus, almost, blocked, null_state}` on
`sleeve.gbpjpy_a_plus_ready` and `sleeve.xau_dsp_shakeout_ready` (both
`symbol_state.v0` and `gold_state.v0`). GBPJPY = session_ok ∧
identity_ok(|resid|≤0.15) ∧ agree ∧ dual_same ∧ boj∉{print,guidance_live}.
XAU shakeout uses the same Choice; event_gap fail-closed; USD proxy via
`peers.usdjpy` primary. **Never emit admit Choice.** Do not soften
`us30_off`. BOJ 1.25% effective 2026-09-24 is bucket timing only — no
NEWS_PROTOCOL invent; no fake print/guidance without a spine stamp.
Edge fixtures t1–t4 pin both assemblers.

## SHADOW unlock remasure — `n_non_xau_sufficient=45`

Fixture grid, not the landed XAU pack. 9 `as_of` × EURUSD / USDJPY /
GBPUSD / EURGBP + US30 hard-off. Each sufficient row travels the
Challenge observe pipe (`assemble_symbol_state_v0` → `score_position` →
`compose_shadow`) as `symbol_state.v0`.

Gold-default leaks that reject a row: schema `gold_state.v0`, nested
`gold_state`, metal/XAU identity, peer `not_xau_primary`, missing
`class_specific`, news without pair-ccy filter, `named_apply_symbol`,
live tilt ≠ 1.0, `apply_this_row`, admit Choice.

US30's 9 rows stay `house_hard_off` + `surface.us30_off`. Live tilts
stay 1.0. `never_place`. Helper:
`src/judgment/non_xau_remeasure.py`. Receipt:
`judgment/astra/lab/wires/NON_XAU_REMEASURE_V0.json`.

The landed Challenge tape is still XAUUSD-only
(`shadow.summary.json` `n_non_xau_sufficient=0`). Do **not** overwrite
that pack with this fixture remasure.

## Why non-XAU died as `not_xau_primary`

`gold_state.v0` already accepted a `symbol=` argument, but the **shape** was
XAU (USD news, `us30_off`, XAU flow wire). PR #15 peers stamped
`usdjpy.source = not_xau_primary` on every non-XAU primary. Intent / shadow
then looked assembled and was a dead end.

`assemble_symbol_state_v0` is the sibling. Same completeness + `missing_fields`
contract. Class-aware peers. Pair-ccy filter on the **existing** news spine.
No invented `NEWS_PROTOCOL`. No DXY. No yields.

## What Chair copies

1. Copy `src/judgment/` (especially `symbol_class.py`, `symbol_state.py`,
   `a1_log.py`, `compose.py`, `apply_size.py`, `challenge_shadow.py`,
   `occupancy.py`, `gold_state.py`, `bars.py`).
2. Keep the existing XAU splice. `haircut_challenge_unit` still runs. Non-XAU
   units return **unchanged** (`named_apply_symbol=false` + symbol gate).
3. Env unchanged: `GTOS_JEV_ALIVE_SHADOW=1` `GTOS_JEV_A1_LOG=1`.
   `GTOS_JEV_APPLY_LIVE=1` still means **XAU named wires only**.
4. Restart **only** `GTOS_F5_FTMO` if you land code. No remint. No flatten.
   No place from Jev.

## Intent path

| Primary | `intent_gold_state` | `intent_symbol_state` | APPLY |
|---|---|---|---|
| `XAUUSD` | `gold_state.v0` **+ PACK 4 SHADOW extensions** | wraps `symbol_state.v0` + nested `gold_state` | named wires may apply |
| EURUSD / USDJPY / GBPJPY / US30 / other | **`symbol_state.v0`** | same | observe only (`live_*_tilt = 1.0`) |

`not_xau_primary` is not a source value this assembler emits. Missing peer
tape is `source=unassembled` and sits in `completeness.missing_fields`.

Challenge-true books only. April `data/historical*` is never a member.
Landed tape on this tree is **XAUUSD**. Other symbols assemble from host
live books or fixtures; empty M15/H4 stays visible (`state_sufficient=false`).

## Universal vs class-specific

Universal (same blocks as `gold_state`): identity, clock, sessions,
timeframes, levels, news, sleeve_features, geometry, cost, occupancy,
governor, surface, completeness.

| Class | Extra block | Code facts |
|---|---|---|
| FX | `class_specific.fx` | pair, `usd_leg`, `usd_from_pair` (H4 trend mapped; **not DXY**), session_bias, pip_scale, pair-ccy news |
| metal | `class_specific.metal` | `usd_sensitivity=usd_proxy_only`, A8 source, USDJPY peer |
| index | `class_specific.index` | cash alias (`US30.cash`), **`house_us30_off=true`**, session_bias |
| crypto / energy | label only | house hard-off / weekend — not a fire |

Peers (named, never invent):

- XAUUSD → USDJPY, EURUSD, XAGUSD
- EURUSD → GBPUSD, USDJPY, XAUUSD
- USDJPY → XAUUSD, EURUSD, US30
- GBPJPY → GBPUSD, USDJPY, XAUUSD
- US30 → USDJPY, XAUUSD, UK100

WORLD_STATE_V0 / CA features attach when those modules exist on the tree
(PRs #12 / #13). Absent → `world.source=unassembled`. Never invent DXY/US10Y.

Occupancy cluster names GBPJPY / EURJPY / AUDJPY / CHFJPY as `fx_major`
(CORR_CLUSTER). Occupancy KEEP-one stays the envelope integer.

## Sufficient predicate — do not relax

`state_sufficient_for_live` is still the **gold** predicate: identity +
M15+H4 + geometry + family ≠ unknown. Peers / world / D1 / news spine
never flip it. Missing those stay in `missing_fields`.

D1 is optional for non-XAU (multi drop has no D1). Visible, not abstaining.

## APPLY stays off on non-XAU

Three independent gates, all required:

1. `compose_shadow` sets `named_apply_symbol` only when identity is XAUUSD.
   Flow/cost **live** tilts stay 1.0 otherwise. Shadow tilts still compute
   for the log.
2. `apply_named_tilts` refuses when `named_apply_symbol is False`.
3. `maybe_haircut_unit` returns the unit unchanged when `symbol ≠ XAUUSD`.

A sufficient EURUSD row with `GTOS_JEV_APPLY_LIVE=1` on Challenge login/ns
**cannot** change `risk_pct_per_trade` or lots.

## Remaining — do not invent

| Item | Status | Chair |
|---|---|---|
| Non-XAU Challenge CSVs | Not landed here (XAU only). | Pull M15+H4 for EURUSD / USDJPY / US30 / GBPJPY into `challenge_shadow_20260917/multi/`. `time_utc` already −3h. Never April historical. |
| WORLD_STATE_V0 / CA | Optional import. Absent on this branch. | Land PRs #12 / #13 if Chair wants world attached. |
| Scout+Edge Chair wires | SHADOW labels folded (this wave). | Observe only. Do not APPLY. Do not invent DXY/TIPS. |
| Named non-XAU APPLY wire | Not proposed. | Shadow score first. Owner names a wire. Then prove. Then APPLY commit. |
| A+ sleeve generators | Stubs only (`aplus_*` library). | Do not `--tags` admit. Do not place. Fill primitives from Challenge tape later. |
| NEWS_PROTOCOL | Must not exist. | Pair-ccy filter on the landed spine only. Host writer READ is the calendar repair. |
| US30 | House off. | `surface.us30_off` and `class_specific.index.house_us30_off` stay true. Do not lift. |

## Applied this wave (observe only)

- `assemble_symbol_state_v0` — sibling schema `gtos.judgment.symbol_state.v0`.
- `state.sleeve` + `state.gate_flow` — **A+ sleeve on gate flow** (not a catalog).
- Intent / Challenge shadow score non-XAU primaries as real state.
- Peers never emit `not_xau_primary`.
- Physical lots stay **XAU flow × cost**. Non-XAU lots stay writer size.
- `aplus_*` cannot silent-APPLY.

Envelope walls stay integers. SEL-V4-002 stays research-only.
Chair speaks ENFORCE / VETO / LABEL. Jev is intelligence only.
