# Pattern → Jev / Noul / Choice / state

**Date:** 2026-09-18  
**Seat:** judgment / research. **No place. No remint. No flatten. No invent NEWS.**  
**Authority:** [`JEV_ALIVE_ORGANISM_20260917.md`](../JEV_ALIVE_ORGANISM_20260917.md) outcome-loop; [`JEV_WHAT_IT_IS_RESEARCH.md`](../JEV_WHAT_IT_IS_RESEARCH.md) primitives; [`gold_state.v0`](../../../src/judgment/gold_state.py); inventory [`JEV_GATE_INVENTORY.json`](../JEV_GATE_INVENTORY.json).  
**Backlog:** [`ABSORB_BACKLOG.md`](ABSORB_BACKLOG.md). **Stubs:** `src/judgment/harvest_patterns.py`. **Typed maps:** [`TYPED_FIELD_MAPS.json`](TYPED_FIELD_MAPS.json) (Chair prove order P0-1 → P0-5). **Receipts:** [`P0_1_FEATURE_AS_OF_HONEST_PROVE.json`](P0_1_FEATURE_AS_OF_HONEST_PROVE.json), [`P0_2_TF_ROUTE_PROVE.json`](P0_2_TF_ROUTE_PROVE.json), [`P0_5_FILL_REALISM_PROVE.json`](P0_5_FILL_REALISM_PROVE.json). Multi books: [`MULTI_BOOKS_LANDING_20260918.json`](MULTI_BOOKS_LANDING_20260918.json).

**Chair NAME 2026-09-18 — schema lock:** keep null-visible `harvest.*` extras on `gold_state.v0`. **Do not cut `gold_state.v0.1`.** Research-only. Live multiplier `1.0`. No vendor. No place. Atom promotion still needs the §7 NAME template.

Each row is: OSS **pattern** (not their code) → **typed field on our object** → **Jev primitive** → **gate hook** → **prove path**. Code composes. Jev never becomes a second writer.

---

## 0. How to read a row

```
1. OUTCOME the pattern exists for     (one sentence, no boolean)
2. STATE field we already have or add (path on gold_state / harvest extra)
3. Assembled today?                   (file or GAP)
4. Jev primitive                      (Choice / Score / Noul / none — integer)
5. Compose                            (weights live in compose.py / harvest stub)
6. Jev down / low-conf                (never extra PASS)
7. Wire class                         (A0 integer | A1 log | A2 chair | W_named)
8. Prove path                         (Challenge-true pack + frozen bars)
```

**Integer vs judgment** does not move. Token, 2-stop *count*, `--tags`, US30, H8 flatten, governor walls, calendar window math stay code. Harvested patterns may *label* or *tilt size* after `PROVED_SHADOW` + owner NAME. They may not place.

---

## 1. P0 patterns (do these)

### P0-1 Point-in-time feature contract (Qlib DataHandler / Feast PIT join)

| Slot | Ours |
|---|---|
| Outcome | Was every feature knowable at `clock.as_of_utc`? |
| Field | `harvest.pit.feature_as_of` (map name → ISO), `harvest.pit.leakage_keys` |
| Today | `as_of_clock`, `reject_expost`, `completeness.expost_rejected`, `harvest.pit.feature_as_of` via `feature_as_of_from_books`. |
| Jev | Noul `feature_as_of_honest` — true = no named field is younger than the decision bar; false = leak or missing as-of. |
| Hook | Assembler + `FLUID-ADM-001` `state_sufficient`. Leak on `live_intent` is a **code raise**, not a Jev refuse. |
| Down | Missing as-of → `completeness.pit = false`; Noul abstains (~0.5). No extra PASS. |
| Wire | A1 log. Integer raise already exists for EXPOST keys. Live multiplier stays 1.0 until Chair NAMES this atom. |
| Prove | **PROVED_SHADOW** 2026-09-18 Challenge `0`: n=53, decidable 48 ≥ 20, moved 6 ≥ 5 (injected future `ac60`), invented_high 0, xau_substituted 0, live 1.0. Receipt [`P0_1_FEATURE_AS_OF_HONEST_PROVE.json`](P0_1_FEATURE_AS_OF_HONEST_PROVE.json). Not APPLY. |

### P0-2 Route identity (Jesse routes)

| Slot | Ours |
|---|---|
| Outcome | Which (sleeve × symbol × TF) is this fire, so all-instruments share one question set? |
| Field | `identity.tf_route` ∈ `{M15,H4,D1,multi_m15_h4}`, `identity.route_id` = `sleeve\|symbol\|tf_route` |
| Today | `identity.sleeve`, `identity.symbol`, Challenge multi-bar (M15+H4). **GAP:** no route id; gold_state still reads XAU-shaped. |
| Jev | Choice `route_class` ∈ `{metal, fx_major, fx_cross, index, unknown}`. No-match stays `unknown`. Do not dump 400 tags into one Choice — prefilter in code (≤255). |
| Hook | Assembler identity. Fan-out questions stay ID-stable across symbols. |
| Down | `route_class=unknown` → `state_sufficient` false. |
| Wire | A1. Extending `identity.symbol` off XAU is research-only until Chair names it. |
| Prove | **PROVED_SHADOW** 2026-09-18. Chair NAME of the table (SHADOW labels only): XAUUSD→`metal`; majors→`fx_major`; GBPJPY→`fx_cross`; US30*→`index` + house_hard_off honesty; UK100/BTC/ETH stay `unknown`. Do not invent a class outside that table. Receipt [`P0_2_TF_ROUTE_PROVE.json`](P0_2_TF_ROUTE_PROVE.json). Live 1.0. Not APPLY. D1 missing does **not** TF-abstain. |

### P0-3 Protection atoms (Freqtrade protections)

| Slot | Ours |
|---|---|
| Outcome | Is this named protection still earning the outcome it was written for? |
| Field | `harvest.protection.kind` ∈ `{cooldown, stoploss_guard, maxdd, occupancy, two_stop, cluster}` + `fired` bool + `remaining` int |
| Today | Integers: 2-stop count, occupancy keep-one, cluster cap, governor DD. **GAP:** no named “why this wall exists” atom for Jev. |
| Jev | Score `protection_still_earns` 0–2 (0 = wall is cutting A+ fire, 2 = wall is eating house-toxic). Noul `would_be_nth_stop` **label only**. |
| Hook | `F5-JEV-002` / `ENV-TWO-STOP` / `ENV-OCC` / `UB-PLC-011`. **Jev is not the counter.** |
| Down | Absent remaining count → do not label “safe.” Integer still blocks. |
| Wire | A1 label. Size tilt only after `PROVED_SHADOW` + preauth `size_tilt`. Never refuse a house-legal fire. |
| Prove | Challenge 2-stop tape: `would_be_nth_stop` true on would-be thirds; `live_multiplier` stays 1.0 while locked; invented HIGH forbidden. |

### P0-4 Challenge envelope snapshot (no OSS peer — compose Nautilus RiskEngine + Lean max-DD + our MC)

| Slot | Ours |
|---|---|
| Outcome | Are we judging the sleeve on the **firm’s** walls, not a generic 2%? |
| Field | `harvest.envelope.daily_loss_rule`, `maxdd_rule` ∈ `{static_floor, trailing}`, `reset_clock` ∈ `{cest_midnight, server_midnight}`, `phase` ∈ `{1,2,funded}` |
| Today | `governor.*` generic. Firm-true rules live in research MC, not on the live gold_state. **GAP:** Challenge-true snapshot not on every row. |
| Jev | **None on the walls.** Optional Score `wall_pressure` log-only (already in alive map UB-ADM-004). |
| Hook | A0 integers. Jev may see the snapshot as context for `admit` / size tilt; cannot lift a wall. |
| Down | Missing snapshot → `completeness.envelope = false`; fluid admit abstains. |
| Wire | A0 for walls. A1 for `wall_pressure`. |
| Prove | Snapshot fields match Challenge login `0` / `$110k` when `origin_organism=f5_challenge`. Verification login stays quarantined. |

### P0-5 Fill / cost realism (hftbacktest)

| Slot | Ours |
|---|---|
| Outcome | Is cost the whole trade, and is the fill model honest enough to say so? |
| Field | existing `cost.*` + `harvest.fill.model` ∈ `{bar_close, next_open, tick, unknown}`, `harvest.fill.latency_ms` |
| Today | `cost.spread_r_of_stop`, `F5-JEV-004` tilt `[0.70, 1.00]`. **GAP:** no fill-model noun; missing cost looks like “cheap.” |
| Jev | Noul `cost_complete` (named spread/slip/commission present). Score `fill_realism` 0–2. Existing Noul `cost_hurtful` unchanged. |
| Hook | `UB-PLC-017` / `F5-JEV-004`. Cost tilt cannot refuse / zero. |
| Down | `fill.model=unknown` → `fill_realism` ignored in compose (weight 0). |
| Wire | A1; APPLY cost tilt already owner-named on Challenge. |
| Prove | **PROVED_SHADOW** 2026-09-18. 47/47 honest rows decidable tick Score 2.0; unknown abstains. Live 1.0. Receipt [`P0_5_FILL_REALISM_PROVE.json`](P0_5_FILL_REALISM_PROVE.json). Not APPLY. |

---

## 2. P1 patterns

### P1-1 Event-sourced clock (Nautilus)

| Slot | Ours |
|---|---|
| Outcome | Is this bar/tick the event we think it is, on the clock we pinned? |
| Field | existing `clock.rule=new_york_plus_7`, `clock.as_of_utc`, `sessions.source` |
| Jev | Noul `tape_fresh` (alive map UB-GEN-004 / UB-PLC-013). Score `session_fitness` (exists). |
| Hook | Do **not** replace `broker_clock.py`. Do not invent EET+3. |
| Prove | Friday cutoff / dead_21_00z rows score 0 session_fitness; writer clock still blocks. |

### P1-2 Incremental labels (River)

| Slot | Ours |
|---|---|
| Outcome | Did this close change the sleeve’s learn-loop evidence, at day-block grain? |
| Field | `harvest.learn.label` ∈ `{target, stop, time_stop, manual_other, unknown}`, `harvest.learn.R`, `harvest.learn.day` |
| Today | `learning_actuator` every-split + day-blocks; close-label Choice must include `time_stop` (V1 miss). |
| Jev | Choice `exit_class` (exists, CLOSE hook). **EXPOST only on `as_of_close_illegal_for_live`.** |
| Hook | Never attach `R` / `exit_class` to `live_intent`. Actuator stays default-off. |
| Prove | 5/5 Challenge paying time_stops label `time_stop`, not `manual_other`. |

### P1-3 Hypothesis → evidence loop (RD-Agent process)

| Slot | Ours |
|---|---|
| Outcome | One harvest hypothesis, one frozen metric, one receipt — no tune-after-see. |
| Field | `harvest.hypothesis.id`, `metric`, `frozen_before` |
| Jev | None. This is Chair / prove machinery. |
| Hook | `fluid_prove.prove_gate` + `PROVE_BARS_*`. |
| Prove | Ledger row exists before the Jev call that it governs. |

### P1-4 Evaluator vs trader (OctoBot / vnpy apps)

| Slot | Ours |
|---|---|
| Outcome | Intelligence can score without being able to send. |
| Field | none new — process law |
| Jev | All A1 questions. |
| Hook | `src/judgment/__init__.py` already forbids place/remint/flatten. Harvest stubs must not import `mt5` / `execution`. |
| Prove | `test_harvest_patterns.py` import graph. |

### P1-5 Walk-forward ranking (PyBroker / Zipline Pipeline)

| Slot | Ours |
|---|---|
| Outcome | Is this sleeve A+ **out of the fold that selected it**? |
| Field | `harvest.wf.fold_id`, `harvest.wf.role` ∈ `{train, oos, sealed}` |
| Jev | Score `lesson` for Nightly body — **not** KEEP/OFF (F5-JEV-010). |
| Hook | Gold lab G-2W→G-10M; `learning_actuator` every-split. |
| Prove | Pre-register fold roles before reading R. |

---

## 3. P2 patterns (short)

| Pattern | Field | Jev | Hook | Prove |
|---|---|---|---|---|
| Lean universe / spec | `surface.instrument_spec` | Noul `instrument_known` | UB-GEN-003 integer already drops unknown; Noul is consistency | redacted_account missing-config pairs stay dropped |
| Hummingbot paper/live | existing shadow flags | Score `paper_live_parity` | A1 on shadow vs Challenge fill | n≥20 paired fills or abstain |
| FinRL closed obs | `gold_state.v0` itself | — | Assembler | No gym `step` in judgment |
| vnpy / aiomql typed MT5 | research ledger only | — | **Forbidden** on send | Import test |
| gym-mtsim account | `harvest.envelope.*` study | — | Default-off script | No live terminal |

---

## 4. Proposed questions (IDs for *our* code — not sent to the model)

Add to a future fan-out only when the field is assembled. Do not ask Jev to invent missing state.

| Question id | Primitive | Instructions gist | Ignore if |
|---|---|---|---|
| `feature_as_of_honest` | noul | Completeness of per-field as-of vs `clock.as_of_utc` | — (always ask; empty → false/0.5) |
| `route_class` | choice | `metal` / `fx_major` / `fx_cross` / `index` / `unknown` | — |
| `protection_still_earns` | score | 0 wall cutting A+; 2 wall eating house-toxic | `remaining` missing |
| `would_be_nth_stop` | noul | Label only | not same sleeve / UTC day |
| `cost_complete` | noul | Named cost terms present | — |
| `fill_realism` | score | 0 bar-fantasy; 2 tick-true | `fill.model=unknown` |
| `wall_pressure` | score | Near prop wall? | envelope unassembled |
| `instrument_known` | noul | Spec present for this symbol | — |
| `paper_live_parity` | score | Shadow fill ≈ Challenge fill | no pair |
| `exit_class` | choice | **must include `time_stop`** | not a close row |

Existing questions (`state_sufficient`, `flow_stance`, `flow_alignment`, `session_fitness`, `geometry_vs_tape`, `level_respect`, `cost_hurtful`, `event_proximity`, `calendar_honest`, `admit`, …) do **not** get renamed. Harvest adds; it does not fork the inventory.

---

## 5. Compose with harvest atoms

Weights stay in code (`compose.py`). Harvest atoms are extra inputs, same law:

```
house_block = token | hard_off | us30 | two_stop_exhausted
            | cost_screen_refuse | dead_window | occupancy | governor | halt

if house_block:
    disposition = writer_blocked          # harvest logs only
elif not state_sufficient or not feature_as_of_honest:
    disposition = assemble_or_escalate
else:
    composite = w_flow*flow + w_sess*sess + w_geo*geo + w_lvl*lvl
                - w_cost*cost_hurtful - w_event*event
    # harvest (ignore-if-unused):
    #   - fill_realism unknown → weight 0
    #   - protection_still_earns is LABEL, not a new refuse
    #   - wall_pressure is LABEL
    disposition = log_only until a W_named sentence exists
```

Jev down / schema-break / low-conf: **no extra PASS.** Alive ≠ fail-open. Size tilts stay inside `[0.70, 1.15]` / cost `[0.70, 1.00]`. Cannot zero. Cannot remint.

---

## 6. Schema discipline

- **LOCKED (Chair 2026-09-18):** null-visible extras on `gold_state.v0` (`harvest.*`). **No `gold_state.v0.1` cut.** Assembler schema string stays `gtos.judgment.gold_state.v0`.
- Do not put EXPOST keys on `live_intent`.
- Do not invent `news.events[]`.
- Do not put `flatten` in any Choice (`jev_corr_hold_v1` law).
- Do not put 400 sleeve tags in one Choice.
- Route / feature / envelope extras must be JSON-serialisable named fields — Jev is text-only; charts become ATR / hour / distance.

---

## 7. Chair NAME template (copy when promoting a harvest atom)

```
I NAME harvest.<atom> on <wire_id>.
Effect: label | size_tilt.
Not: place, remint, flatten, envelope.
Prove receipt: <path>.
Challenge login/ns only until I say otherwise.
```

The 2026-09-18 NAME locked the *schema seat* only. Until a sentence in this template exists for a named atom, stubs attach and tests pass; live multiplier stays 1.0.
