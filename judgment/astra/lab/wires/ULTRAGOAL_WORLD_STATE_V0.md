# ULTRAGOAL — WORLD_STATE_V0 → Jev

**Seat:** architecture / design pack. **No broker place. No remint. No flatten. No TypeSafe live wire.**
**Date:** 2026-09-18
**Schema:** `gtos.judgment.world_state.v0`
**Assembler:** `src/judgment/world_state.py` `assemble_world_state_v0`
**Questions:** `src/judgment/world_questions.py` (Noul-first pack)
**JSON Schema:** `judgment/astra/schemas/world_state_v0.json`
**Rates / DXY / funding extension:** [`RATES_DXY_FUNDING_V0.md`](RATES_DXY_FUNDING_V0.md) — typed `usd_impulse` / `rates_impulse` / `funding_stress` / `risk_on_off`. Missing Challenge-true feeds stay null. No APPLY size.
**Parent:** [`JEV_GOLD_STATE_SCHEMA_DRAFT.md`](../../JEV_GOLD_STATE_SCHEMA_DRAFT.md) + [`JEV_ALIVE_ORGANISM_20260917.md`](../../JEV_ALIVE_ORGANISM_20260917.md)
**Correctness that still binds:** [`JEV_INTEGRATION_V2_20260917.md`](../../JEV_INTEGRATION_V2_20260917.md) §8 — `NEWS_PROTOCOL` is **not in git**.

Owner ultragoal: compounding trading intelligence that reasons like a **world-aware desk** (cross-asset, rates/liquidity, named event proximity, gold sold under a *named* USD/funding/rates context) — **not** a chat LLM dumping raw X into orders.

Jev (TypeSafe System One) = typed Choice / Score / Noul over structured state. Intelligence only. **Chair ENFORCE / VETO / LABEL. Writer prints.**

---

## 0. Non-goals (explicit)

| Forbidden | Why |
|---|---|
| Raw X firehose as state | Not a typed field. `world.narrative.raw_x_forbidden = true`. Chat summaries are not news. |
| Inventing `NEWS_PROTOCOL` URLs / endpoints | V2 §8: the file is **not in this repository**. Event Nouls without a named spine **abstain**. Host `events.jsonl` is a writer tape, not a protocol client (`host_events.py`). |
| Broker send from Jev | No `order_send`, no remint, no flatten, no token mint. `never_place / never_remint / never_flatten` are schema constants. |
| Treating USD FX as a yield print | EURUSD/USDJPY snaps are a **USD proxy basket**. `rates.assembled` stays false until a named US10Y / TNX / ZN tape lands. |
| Inventing DXY / VIX / funding-AI prose | `data/DXY_D1.csv` exists but prints ~25 — rejected as not ICE DXY (`dxy_csv_present_but_not_ice_dxy`). Sierra VXM/ZN are `control_only` and **thin** (3 D1 days, April 15–17). Narrative stays `unassembled`. See [`RATES_DXY_FUNDING_V0.md`](RATES_DXY_FUNDING_V0.md). |
| Mutating the 48-fluid inventory in this pack | WORLD questions are a **new pack**, not a silent rewrite of `JEV_GATE_INVENTORY.json`. Chair lands gates later. |
| Same-pass APPLY | Process lock `shadow_score_then_wire`. Challenge-true prove first. |

---

## 1. Survey — what already exists (this branch)

Read from disk 2026-09-18 on `cursor/jev-alive-organism-72cf` plus this pack. Do not reconstruct from chat.

| Tissue | Where | What it already does | What WORLD must not redo |
|---|---|---|---|
| **gold_state.v0** | `src/judgment/gold_state.py` | Closed **per-candidate** XAUUSD object: clock, sessions, M15/H4/D1, levels, news attach, sleeve A8, geometry, cost, occupancy, governor, completeness. EXPOST rejected on `live_intent`. | WORLD is the **desk**. Gold stays the **fire**. Attach via `attach_world(gold, world)`. |
| **compose** | `src/judgment/compose.py` | Maps `flow_alignment` Score → `[0.70, 1.15]`, `cost_hurtful` Noul → `[0.70, 1.00]`. Cannot zero a fire. Leave-orig ticket `293332188` stays 1.0. | WORLD compose (`compose_world_shadow`) **never resizes**. It drafts Chair nouns only. |
| **fluid_gates** | `src/judgment/fluid_gates.py` + `JEV_GATE_INVENTORY.json` | 48 fluid / 8 envelope. Envelope walls stay integers. `auto_apply_eligible` only `size_tilt` / `label`. | Do not add WORLD ids to the 48 without Chair. Envelope still not Jev toys. |
| **news_spine** | `src/judgment/news_spine.py` | Loads `data/news_calendar.json` + `data/news/*.json`. Fail-closed. Empty covering window = `spine_empty` (**not** “no HIGH”). W7 15/2, F5 15/60. Prefers host Challenge-axis rows on datetime+currency collision. | WORLD **reuses** `attach_news`. No new fetch. No invented HIGH. |
| **host_events** | `src/judgment/host_events.py` | Challenge `events_since_*.jsonl`: trail + `news_t15` / `news_t60` inventory. Unread stays named (`NOT_READ` / `UNKNOWN`). Explicitly **does not add a NEWS_PROTOCOL endpoint**. | WORLD copies `news_inventory_at` into `host_news`. |
| **a1_log** | `src/judgment/a1_log.py` | Default-off (`GTOS_JEV_A1_LOG` / `GTOS_JEV_ALIVE_SHADOW`). Assembles gold fan-out, optional TypeSafe POST, `compose_shadow`. SEL-V4-002 lives here — not in bound `selector_v4.py`. | Do not default-on WORLD POSTs. Chair land later may add `observe_world` behind the same env. |
| **occupancy** | `src/judgment/occupancy.py` | Challenge-true symbol open / isolated 15m / `CORR_CLUSTER` (metals, fx_major, index, crypto). Missing tape → all `None`. | WORLD lifts clusters to **desk occupancy** (`focus_cluster_crowded`). KEEP-one stays the envelope integer. |
| **jev_questions** | `src/judgment/jev_questions.py` | Per-fire A1 pack (`state_sufficient`, `flow_stance`, `event_proximity`, …). | WORLD pack is a **second fan-out** over `{gold, world}`. Same TypeSafe rules (IDs not sent; meaning in instructions). |
| **Wave M** | `WAVE_M_RECEIPT.json` | Proved `a8_agrees` + `calendar_honest` on Challenge tape. Host writer never `READ` on that tape. Remaining SHADOW: trail / friday_cutoff / spine_empty-constant. | WORLD `calendar_honest_world` **reuses** that honesty: JSON covering + host not-READ = false. |
| **Sierra proxies** | `src/research_infra/sierra_proxy_registry.py` | ZN = `rates_liquidity_control_only`, CL = `macro_liquidity_control_only`, VXM = vol control. **Not target confluence.** Not in this checkout’s bar dirs. | WORLD stamps `sierra_zn: control_only_absent`. Does not pretend ZN is a live rates path. |

**Landed news on this clone (do not invent more):**

- `data/news_calendar.json` — week of 2026-05-31 only
- `data/news/f5_high_calendar_host_20260916.json` — Challenge-axis (Wave M uses this)
- `data/news/high_spine_ff_thisweek_20260917.json` + raw FF this-week
- Host writer inventory on the 2026-09-17 Challenge tape: **never READ**

**Landed cross-asset bars:**

- Challenge-true XAU M15/H4/D1 under `judgment/astra/lab/challenge_shadow_20260917/`
- Multi-symbol Challenge landing slot (`bars.py` `MULTI_SYMBOL_PRIORITY`: EURUSD, GBPUSD, BTCUSD, EURGBP, US30, UK100, ETHUSD; USDJPY optional). **April `data/historical*` is never Challenge-true** (`test_bars_multi.py`).
- Repo historical CSVs exist for EURUSD / USDJPY / GBPUSD / NAS100 / US30_cash / XAGUSD — usable for **lab** world assembly, never as a Challenge score unless the Challenge path is landed.

**Still missing (named, not filled):**

- `NEWS_PROTOCOL`, `MAC_INGEST`, `OWNER_LAW`, `ASTRA_ARCH` (V2 §8)
- DXY series
- US10Y / TNX / ZN OHLC in `data/historical*`
- Walter / desk_briefs
- Official F5 leftover-ship `official_high_spine` live freshness protocol

---

## 2. Two closed objects — do not collapse them

```
                    ┌─────────────────────────────────────┐
   as-of clock ───► │  world_state.v0   (desk)            │
                    │  usd / rates-proxy / risk / news    │
                    │  corr / occupancy / liquidity       │
                    └─────────────────┬───────────────────┘
                                      │ attach_world()
                    ┌─────────────────▼───────────────────┐
   candidate   ───► │  gold_state.v0   (fire)             │
                    │  geometry / A8 / cost / M15 H4 D1   │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                         Jev fan-out (gold pack + world pack)
                                      │
                                      ▼
                    code compose ──► Chair ENFORCE / VETO / LABEL
                                      │
                                      ▼
                                 Writer prints
```

| Rule | gold_state.v0 | world_state.v0 |
|---|---|---|
| Cardinality | One per candidate / bar-fire | One per as-of (desk) |
| Sufficient predicate | identity + M15+H4 + geometry + family ≠ unknown | clock + symbol + (**USD proxy OR news spine OR occupancy**) |
| May resize (after prove) | Yes — named flow/cost wires only | **No** |
| May draft Chair VETO | Event / cost (existing) | USD/rates-proxy, event, cluster |
| EXPOST on live_intent | Illegal | Illegal |

TypeSafe state guidance ([docs](https://docs.typesafe.ai/concepts/state.md)): named JSON fields, questions independent, reference paths with backticks (`` `world.usd.stance` ``, `` `gold.geometry.stop_dist` ``).

---

## 3. WORLD_STATE_V0 fields (typed)

Full JSON Schema: `judgment/astra/schemas/world_state_v0.json`.
Assembler: `assemble_world_state_v0(...)`.

### 3.1 What V0 **can** support today (hedge-fund questions without lying)

The owner example — *gold sold under funding / AI / rates context* — is a **desk question**. V0 can ask it **only** against named fields:

| Question the desk wants | V0 named substrate | Honest refusal |
|---|---|---|
| Rates path | `rates.named_yield` | **Unassembled.** No US10Y/TNX/ZN tape. `rates_path_assembled` Noul target is **false** until a tape lands. |
| USD | `usd.stance` from EURUSD / GBPUSD / USDJPY `tf_snap` (EUR up = USD down; USDJPY up = USD up) | DXY file present but rejected (`usd.dxy.reason = dxy_csv_present_but_not_ice_dxy`). Series stays null. |
| Liquidity proxies | `liquidity.spread_r_of_stop`, `vol_ratio`, `session_named` from gold | Sierra ZN/CL / order book = `control_only_absent` / `unassembled` |
| Event proximity | `news.*` via `attach_news` + `host_news` via `news_inventory_at` | Empty spine ≠ no HIGH. Host unread ≠ honest. No NEWS_PROTOCOL URL. |
| Cross-asset occupancy | `occupancy.clusters` from `CORR_CLUSTER` + Challenge deals | Missing tape → `None`, never “crowded” |
| gold↔rates correlation | `corr.gold_vs_usd` = Pearson of overlapping D1 **gold vs USD-proxy** returns (inv EURUSD or USDJPY) | This is **gold↔USD**, not gold↔yield. `gold_rates_coherence` Score sits at mid while `rates.assembled` is false. |
| “Sold under funding/AI” | **Not a field.** `narrative.source = unassembled`. `narrative_state_absent` Noul should be **true**. | Do not fill from chat or X. |

Code fact the pack exists to confirm:

```
corr.code_gold_sold_into_usd_strength =
  (focus.side in {short,sell} and usd.stance == stronger)
  or (focus.side in {long,buy} and usd.stance == weaker)
```

That is the V0 stand-in for “gold sold under a strong-USD / tightening-proxy tape.” It is **not** a claim about the Fed path.

### 3.2 Completeness (code, before the call)

```
Desk is evaluable (state_sufficient_for_desk) only if:
  clock.as_of_utc and focus.symbol
  and (usd.proxy assembled OR news.spine_empty is false OR occupancy assembled)

LIVE / as_of_open_study additionally:
  no EXPOST keys
  news.spine_empty is a boolean (assembled), not omitted

If state_sufficient_for_desk is false:
  you MAY still call Jev with Noul world_state_sufficient (expect low)
  you may NOT use other WORLD answers for a Chair draft
```

`named_yield` and `dxy` are **always false** on this clone. That is a feature: the Score `gold_rates_coherence` is instructed to stay at 1 (proxy-only / mixed) until a yield tape exists.

---

## 4. Jev question pack — names + Noul targets

Pack id: `gtos.judgment.world_pack.v0`
One request. Independent questions. Challenge-true **code labels** are the first score — not live P&L, not a KEEP grid.

**Prove → APPLY path (frozen bars, same as Wave L/M):**

1. Assemble `world_state` at every Challenge shadow as-of (`challenge_shadow_20260917`, login `0`, ns `operator`).
2. Stamp **code twins** (`compose_world_shadow`) — no TypeSafe required for the first pass.
3. Optional: POST TypeSafe with `world_systemone_payload(attach_world(gold, world))`.
4. Score each Noul against the Challenge-true target in the table (agreement / Brier), **not** against broker_net.
5. Bars (do not lower): label `min_decidable=20`, `min_non_default=5`, `min_distinct=2`; invented HIGH forbidden.
6. Chair may **LABEL** as soon as the code twin is honest. **VETO / ENFORCE** only after PROVED_SHADOW + owner/Chair land. WORLD never resizes.

### 4.1 Nouls (yes-event = target)

| Name | Target (yes) | Challenge-true label | Chair |
|---|---|---|---|
| `world_state_sufficient` | Named desk blocks present | `completeness.state_sufficient_for_desk` | LABEL |
| `usd_strength_named` | Named USD FX stronger | `usd.stance == stronger` | LABEL |
| `gold_sold_into_usd_strength` | Short into USD strength or long into USD weakness | `corr.code_gold_sold_into_usd_strength` | VETO draft |
| `rates_path_assembled` | Named yield series present | `completeness.named_yield` — **expect false** | LABEL |
| `usd_proxy_only` | Rates block is FX basket, not yield | `rates.usd_proxy_only` | LABEL |
| `event_proximity_world` | Named HIGH in the **code** window | `news.high_in_f5_window` or `high_in_w7_window`; spine empty → ~0.5 | VETO draft |
| `calendar_honest_world` | Spine present and host READ or no host writer | Wave M rule: unread writer ⇒ false | LABEL |
| `corr_gold_vs_usd_against` | 20d gold D1 against USD proxy | `corr.gold_vs_usd.relation == against_usd` | LABEL |
| `corr_regime_broken` | 20d sign ≠ 60d sign | `corr.gold_vs_usd.regime_broken` | LABEL |
| `risk_on_named` | Named NAS100/US30/UK100 up | `risk.stance == risk_on` | LABEL |
| `gold_fights_risk` | Gold side fights named risk | short+risk_on or long+risk_off | LABEL |
| `liquidity_hurtful_world` | Named spread dominates | `spread_r_of_stop >= 0.10` when assembled | LABEL |
| `cluster_crowded` | Focus cluster has another open | `occupancy.focus_cluster_crowded` | VETO draft |
| `narrative_state_absent` | No desk-brief / no X | `narrative.source == unassembled` — **expect true** | LABEL |
| `world_veto_usd_rates` | Draft VETO: gold fights USD/rates-proxy | sold-into-strength **and** (against_usd or regime_broken) | VETO |
| `world_veto_event` | Draft VETO: named HIGH in window | same as `event_proximity_world`; empty spine ≠ veto | VETO |

### 4.2 Choice / Score (compose later)

| Name | Primitive | Job |
|---|---|---|
| `usd_stance` | Choice `stronger \| weaker \| mixed \| unassembled` | Confirm the named vote |
| `risk_stance` | Choice `risk_on \| risk_off \| mixed \| unassembled` | Confirm the named vote |
| `gold_macro_fit` | Choice `with_macro \| against_macro \| unclear` | Combine USD/risk/corr — **not** a yield story |
| `chair_draft` | Choice `enforce \| veto \| label \| abstain` | Draft only. Chair stamps. Writer ignored. |
| `usd_pressure` | Score 0–2 | USD pressure on gold |
| `risk_alignment` | Score 0–2 | Gold vs named risk |
| `liquidity_quality` | Score 0–2 | Named spread/session only |
| `gold_rates_coherence` | Score 0–2 | **Must sit at 1** while yield is unassembled |

Local compose (`compose_world_shadow`): `chair_draft = abstain` if desk insufficient; `veto` if usd-rates veto or named HIGH or cluster crowded; else `label`. **Never `enforce` from code.** Never `size_tilt`.

---

## 5. Chair land-later checklist

Copy this onto the host only after Challenge prove. Tip: land `src/judgment/` onto **Challenge f5-live** (`0` / `operator`) the same way as [`HOST_STATE_SUFFICIENT.md`](HOST_STATE_SUFFICIENT.md). Do **not** wholesale-copy `book_owner.py`.

### 5.1 Must already be true (do not regress)

- [ ] Envelope walls stay integers (`ENV-KILL`, 2-stop count, token digest, H8, DD, US30, occupancy keep-one, dead window).
- [ ] SEL-V4-002 stays in `a1_log.py`. Do not edit host `selector_v4.py` (R2 / H1).
- [ ] Physical lots stay **flow × cost** until Chair names another size axis.
- [ ] Leave-orig ticket `293332188` and already-open rows stay 1.0.
- [ ] `NEWS_CALENDAR_REPAIR.md`: do not overwrite June `data/news_calendar.json`.
- [ ] Host news writer must actually **READ** before `calendar_honest_world` can go true on Sep 15+ rows.
- [ ] Remaining SHADOW (do not invent to clear): `FLUID-HLD-005` trail, `FLUID-HLD-008` friday_cutoff, `FLUID-NWS-005` spine_empty-constant.

### 5.2 WORLD pack land order

1. **LABEL only** — ship `world_state.py` + `world_questions.py`. Assemble on Challenge as-ofs. Log `compose_world_shadow` next to A1 JSONL. No TypeSafe required.
2. **Prove code twins** against the Noul-target table (bars above). Receipt under `judgment/astra/lab/wires/`.
3. **Optional TypeSafe** — `GTOS_JEV_A1_CALL` already default-on when a key is present. Keep WORLD behind an explicit flag (`GTOS_JEV_WORLD_CALL=1`) so gold A1 budget (200) is not silently eaten.
4. **Chair LABEL** the honest Nouls (`usd_proxy_only`, `narrative_state_absent`, `rates_path_assembled=false`, `calendar_honest_world`).
5. **Chair VETO** (inbox draft, not writer refuse) only for `world_veto_event` / `world_veto_usd_rates` / `cluster_crowded` after PROVED_SHADOW. Occupancy KEEP-one remains the integer.
6. **Chair ENFORCE** — not in V0. No WORLD size wire. No W7 armed-book import. No token remint.

### 5.3 What Chair copies (when they say land)

1. `src/judgment/world_state.py`
2. `src/judgment/world_questions.py`
3. This file + `judgment/astra/schemas/world_state_v0.json`
4. Existing `news_spine.py`, `host_events.py`, `occupancy.py`, `bars.py` (already on the organism branch)
5. Env unchanged for gold wires. New: `GTOS_JEV_WORLD_CALL=0` default.
6. Restart **only** `GTOS_F5_FTMO` if a splice is added. No remint. No flatten. No place from Jev.

---

## 6. Repair vs build next

### Repair (do not skip — WORLD will lie if you do)

| Defect | Evidence | Repair |
|---|---|---|
| Host calendar unread | Wave M: writer `NOT_READ` / `UNKNOWN` / None, never `READ` | Host writer **reads** the spine. Do not invert `spine_empty`. Do not invent NEWS_PROTOCOL. |
| Live gold sufficient was false | Wave M: `intent_gold_state` lacked Challenge books | Already patched on the organism branch (`books_for_symbol`). Chair must land that splice **before** WORLD, or desk+fire will both be dark. |
| geometry ATR 1.5 vs 2.0 | CLAUDE / wave-21 | Keep `gold.completeness.geometry_atr_basis`. WORLD must not score “fit” across mixed bases. |
| Two calendars, no protocol | V2 §8 `NEWS_PROTOCOL` missing | Ingest the **real** Project file when it exists. Until then fail-closed. |
| Challenge multi symbols not all landed | `bars.py` slot exists; April historical is the wrong tape | Land Challenge EURUSD/USDJPY/US30 CSVs into `challenge_shadow_*/multi/`. Do not score WORLD USD/risk on April files and call it Challenge-true. |
| Trail / Friday / empty-spine constants | Wave M `not_proved` | Wait for named as-ofs. Do not rename questions to force two distinct values. |

### Build next (this pack starts 1–3)

1. **WORLD assembler + schema + question pack** — this PR (stubs + tests).
2. **Challenge world JSONL** — `assemble_world_state_v0` at each shadow as-of with landed multi books (when present) + host events + gold attach. No TypeSafe.
3. **Prove receipt** — code twins vs Noul targets; bars not lowered.
4. **Yield tape ingest** (separate owner decision) — a named US10Y or ZN control series with clock + source path. Only then may `rates.assembled` flip. Sierra ZN stays control-only, not target confluence.
5. **DXY optional** — same rule: named CSV or unassembled. Never inferred from chat.
6. **Chair VETO inbox** — reuse leftover-ship `write_inbox_verdict.py` if/when that file is ingested. This pack does not write inbox.
7. **Narrative tissue** — Walter / desk_briefs **if the Mac Project emits them** (V2 §8.2). Still not raw X.

---

## 7. TypeSafe fit (why this is Jev, not a chat seat)

From the TypeSafe skill + [state](https://docs.typesafe.ai/concepts/state.md) / [Noul](https://docs.typesafe.ai/primitives/noul.md) / [fan-out](https://docs.typesafe.ai/patterns/fan-out.md):

- Code owns workflow. Jev returns calibrated probabilities over **named** fields.
- One Noul per label (`usd_strength_named` ≠ `rates_path_assembled`).
- Speculative fan-out is legal: ask `world_veto_*` in the same call; compose ignores them when `world_state_sufficient` is low.
- Confidence on Choice/Score is not permission to send.
- A Noul near 0.5 is “don’t know” — the required answer when spine_empty or yield unassembled.

Chat seats (Grokbot, Project coordinator) stay **outside** the fire path.

---

## 8. Tests that pin honesty

`tests/judgment/test_world_state.py`:

- Unassembled world does not claim DXY, yield, or HIGH.
- USD stance from named EURUSD/USDJPY snaps (invert EUR).
- `gold_sold_into_usd_strength` is a code fact.
- Pearson / regime flags need overlapping D1; thin series stay unassembled.
- Occupancy missing tape ≠ crowded.
- Host unread ⇒ `calendar_honest_world` false.
- EXPOST rejected on `live_intent`.
- Compose never resizes; chair_draft never `enforce`.
- Question pack IDs match `WORLD_NOUL_TARGETS`.
- No `NEWS_PROTOCOL` URL string in assembler / questions / schema.

---

## 9. What this PR is not

It is not a live wire. It is not a rates model. It is not a news protocol. It is not an X ingest. It is the **typed desk object + Jev pack** the ultragoal asked for, so the next session can prove on Challenge tape and the Chair can land LABEL / VETO without anyone inventing a missing world.
