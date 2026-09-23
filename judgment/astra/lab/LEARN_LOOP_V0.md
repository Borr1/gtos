# LEARN_LOOP_V0 — Challenge-true close learning (all symbols)

**Account:** Challenge login `0` / ns `operator`  
**Status:** shadow / prove first. **Jev never places.**  
**Close contract:** `gtos.close_loop.v1` (locked; `orig_tp` is first-class). LEARN_LOOP_V0 binds it.  
**Chair tickets named this wave:** XAU `293611741` `orig_stop`; GBPJPY `293540988` `orig_tp`.

The organism improves *when to act* by labeling every Challenge close — not gold-only — and feeding typed conditions back into judgment research. V0 does not APPLY. V0 does not invent `NEWS_PROTOCOL`.

---

## 1. Existing paths this loop reuses

| Path | Role | V0 use |
|---|---|---|
| `score_position` / `score_deals` | Challenge-true shadow pack | Every close is scored here. Not a second scorer. |
| `assemble_gold_state_v0` (`assemble_symbol_state_v0` alias) | Closed symbol_state object | Snapshot keys. Already multi-symbol (M15+H4). |
| `classify_close` / `named_exit_class` | Inventory vs scoreboard | `broker_tp` stays the inventory word; scoreboard says `orig_tp`. |
| `closed_doc_from_deals` | LABEL-only `closed[]` | `orig_stop` rows only. Envelope 2-stop COUNT stays the live file. |
| `local_answers` admit / close_label | Fluid Choice/Noul | Shadow answers stamped on the learn row. |
| April `data/historical*` | Forbidden | `april_historical_used` fails the row visible. |

Replay (`score_replay_row`) is the older pack. Prefer Challenge deal history / `closed_doc` / `exit_class`.

---

## 2. Per close (the loop)

```
Challenge deal / chair-named close
    → normalize (do not invent prices)
    → score_position (symbol books; never wear XAU on GBPJPY)
    → symbol_state snapshot keys
    → named exit_class + R + regime tags
    → append-only JSONL research store
    → scoreboard + promotion proposal (SHADOW only)
```

### Snapshot keys

`identity.symbol / side / sleeve / family_class`  
`clock.weekday_name / is_friday`  
`sessions.named / utc_hour` (open as-of) plus `sessions.close_named` (close stamp; missing → `session:unassembled`)  
`flow.stance`  
`cost.spread_r_of_stop / hurtful`  
`geometry.plan_r / stop_dist`  
`occupancy.two_stop_exhausted / same_sleeve_orig_stops_utc_day`  
`news.spine_empty / high_in_f5_window` (empty spine ≠ no HIGH)  
`completeness.state_sufficient_for_live / timeframes_m15_h4 / missing_fields`

### Scoreboard language

`orig_stop` · `orig_tp` · `time_stop` · `breach_flatten` · `other`

Inventory `close_label` still maps TP → `broker_tp`. The scoreboard keeps Chair's `orig_tp`.

### R provenance

| `r_source` | Meaning |
|---|---|
| `sit_backstop` | Chair / Challenge close-loop seed. Preferred over geometry. |
| `broker_exit` | Deal row has an exit print |
| `geometry_implied_orig_sl` | Chair `orig_stop` + named SL; no close print in this workspace |
| `geometry_implied_orig_tp` | Chair `orig_tp` + named TP |
| `unassembled` | Geometry missing |

`geometry_R` stays on the row when sit_backstop R is used (XAU implied −1.00 vs sit_backstop −1.03). Do not invent GBPJPY prices to justify +2.96.

### `gtos.close_loop.v1` lock

File: `learn_loop_v0/CLOSE_LOOP_V1.json`.

- `exit_class` includes **`orig_tp`** (not only inventory `broker_tp`).
- `miss_type`: `event_gap` · `ok_win` · `false_structure` · `unlabeled`
- `asset_class`: `XAU` · `FX` · `INDEX` · `CRYPTO` · `OTHER` — FX never wears XAU tape.
- Seeded sit_backstop tickets:

| Ticket | Symbol | Class | R | miss | prove_next (LABEL only) |
|---|---|---|---:|---|---|
| 293611741 | XAUUSD | orig_stop | −1.03 | event_gap | gate/size-cut XAU `dsp_shakeout` inside BOJ T±60 |
| 293540988 | GBPJPY | orig_tp | +2.96 | ok_win | split FX-cross vs XAU R books in Warsh windows |

`prove_next` maps to an **existing** fluid question (`event_proximity` / `admit` / size_tilt). It does **not** invent `NEWS_PROTOCOL` or a BOJ calendar row. Empty spine ≠ no HIGH.

### Chair batch (Challenge `0`, n=48)

File: `learn_loop_v0/CLOSE_LOOP_BATCH_V1.json`. Aggregates only. The 6-row fixture pack is a **sample**, not this batch. Do **not** invent the other 46 tickets, a CRYPTO `mean_R`, GBPJPY prices, close stamps, `NEWS_PROTOCOL`, or BOJ calendar rows.

| | |
|---|---|
| n | 48 |
| sum_R / mean_R | ≈ −28.43 / ≈ −0.59 (`approx: true`) |
| exit_class | `orig_stop` 42 · `time_stop` 4 · `orig_tp` 2 |
| miss_type | `false_structure` 39 · `ok_win` 6 · `event_gap` 3 |
| XAU | n=23 mean_R −0.37 |
| INDEX | n=16 mean_R −1.04, **0 wins** |
| FX | n=6 ≈flat (`mean_R` 0.0, `approx_flat`) |
| CRYPTO | n=3 all stops; `mean_R` is **null** (not invented) |

`scoreboard.sample_n` is the fixture count. `scoreboard.batch` is this sealed object. Identities: exits / misses / asset n all sum to 48; `tickets_invented: false`.

### Asset-class split prove

`prove_asset_class_split` — LABEL / prove, **never APPLY**. Maps to existing questions only.

| Pattern | n | status | question | Hint |
|---|---:|---|---|---|
| INDEX | 16 | SHADOW | `admit` | abstain / keep `house_hard_off` (`mx_us30`, `idxrev`) |
| CRYPTO | 3 | UNDERPOWERED_SHADOW | `admit` | keep `orb_crypto` hard-off |
| XAU | 23 | SHADOW | `event_proximity` | size-cut `dsp_shakeout` BOJ T±60 |
| FX | 6 | SHADOW | `admit` | split FX-cross vs XAU R books in Warsh windows |
| `false_structure` | 39 | SHADOW | `admit` | draft abstain; dominant miss |

Promotion `min_n=5` still applies to the **fixture** pack (UNDERPOWERED_SHADOW). Batch INDEX / XAU / FX / false_structure clear that floor as SHADOW. Chair ritual still required to APPLY. Envelope walls stay integers.

---

## 3. Shadow harness

```
GTOS_JEV_A1_CALL=0 python3 scripts/jev_learn_loop.py
```

Fixtures: `judgment/astra/lab/learn_loop_v0/fixtures/challenge_closes.jsonl`

| Ticket | Symbol | Class | Provenance |
|---|---|---|---|
| 293611741 | XAUUSD | orig_stop | sit_backstop −1.03R `event_gap` |
| 293540988 | GBPJPY | orig_tp | sit_backstop +2.96R `ok_win`. No invented prices. |
| 291076386 | EURUSD | orig_stop | `deals_since_20260909.jsonl` |
| 291113462 | US30.cash | orig_stop | same deals file |
| 291816474 | EURGBP | orig_tp | same deals file (broker TP print) |
| 291794419 | XAUUSD | time_stop | same deals file |

US30 stays `house_hard_off` / `mx_us30`. Envelope `us30_off` is not a Jev toy.

---

## 4. How a validated pattern becomes a Noul / Choice

**Never silent APPLY.**

```
cluster on Challenge-true closes (n, mean R, same exit_class + regime tags)
    → UNDERPOWERED_SHADOW if n < 5
    → SHADOW proposal naming an *existing* fluid question
         admit | close_label | hold_too_late | time_stop_vs_orig
    → prove on Challenge tape → PROVED_SHADOW
    → Chair ENFORCE / VETO / LABEL
    → APPLY only if auto_apply_eligible (size_tilt / label)
```

Forbidden auto effects stay `place` / `remint` / `flatten` / `envelope`.  
`SEL-V4-002` stays research-only.  
V0 does **not** write `JEV_GATE_INVENTORY.json`. A Chair ritual is required to add a gate.

This fixture pack is **underpowered by construction**. That is the honest scoreboard, not a reject.

---

## 5. Host land

See [`wires/HOST_LEARN_LOOP_LAND.md`](wires/HOST_LEARN_LOOP_LAND.md).

Default-off observer: `GTOS_JEV_LEARN_LOOP=1` → `maybe_learn_from_close`.  
Do not splice leftover-ship `book_owner.py`. Do not place from this seat.

The n=48 batch is Chair-sealed. Host store still writes one row per close. Do not invent the other 46 tickets. Asset-class split prove is LABEL only.

---

## 6. Done when

- [x] Design (this file)
- [x] Harness + fixtures (XAU + GBPJPY + FX + US30)
- [x] Tests (`tests/judgment/test_learn_loop.py`)
- [x] No broker place
- [x] Challenge-true scoreboard language
- [x] n=48 batch bound on scoreboard (`CLOSE_LOOP_BATCH_V1.json`)
- [x] Asset-class split prove (LABEL only; never APPLY)
