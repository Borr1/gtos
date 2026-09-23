# HIST-PROVE PLAN — A1 observe every candidate / writer place Choice

**session:** `12_writer_cycle_run_book_a1_observe`  
**as_of_ict:** `2026-09-21T06:05:50+07:00`  
**login / ns:** Challenge `0` / `operator`  
**never_broker_place this session:** true  
**APPLY:** Chair only after gates below. This document does not land APPLY.

Doctrine: hist / replay Challenge tape **before any APPLY that changes live fire rate**.  
Observe-every that only POSTs `evaluate()` and logs **does not change fire rate** — that splice can Chair-land as SHADOW after a latency/budget smoke, not an R prove.  
**Place Choice APPLY changes fire rate** — full Challenge replay required.

---

## 1. Module_ATR honesty (do not invent ATR / regime)

| claim | truth |
|---|---|
| Live writer ATR | `primitives.atr14` on **named closed bars** (`gold_state.geometry.atr14` from Challenge M15 or live books). Missing bars → field unassembled, not a guessed ATR. |
| Module_ATR research lens | Recovered file exit_shape **stop −0.75 ATR-R / tgt +6.0 ATR-R**. Geometry **proxy**. `research_armed.py`: overlay tags only; **not** `config/live_armed_set.json`; **not** W7 `armed_sleeves()`. |
| Honesty verdict (yearfold packs) | **APPROXIMATION** of Module_ATR fills — proxy ≠ live module `TradeIntent` path (no stay_timing / peer_panel / admission). |
| Merge law | **Never** sum Dig_3R + Edge_ATR + Module_ATR. Separate columns. |
| Regime | `regime_tag` PENDING / honest unknown until assembled features. Do not invent regime buckets for hist-prove. |
| Overlay tags | `dsp_three_fresh_lower_lows`, `dsp_spring_close_on_20low_through_the_box` — SCORE LANE research. Promote **NO**, place **NO** from Module_ATR yearfold alone. |

Cite, do not merge:

- `/workspace/gtos/_intel_capture_activate_20260920/overlays/THREE_FRESH_MODULE_ATR_YEARFOLD_20260920.md`
- `/workspace/gtos/_intel_capture_activate_20260920/overlays/SPRING_MODULE_ATR_YEARFOLD_20260920.md`
- blotters: `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`
- `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl`
- also GBPJPY / XAGUSD Module_ATR blotters in the same dir (affinity; session 13)

If a symbol/TF CSV is missing: **`challenge_tape_present=false` → STATE_MISSING**. Do not substitute April `data/historical`. Do not substitute XAU bars onto GBPJPY.

---

## 2. Challenge tape paths (landed on this box)

Search dirs (`src/judgment/bars.py:challenge_search_dirs`):

1. `$GTOS_CHALLENGE_BAR_MULTI` if set
2. `.../judgment/astra/lab/challenge_shadow_20260917/` (XAUUSD M15/H4/D1 **PRESENT**)
3. `.../judgment/astra/lab/challenge_shadow_20260917/multi/` (**PRESENT:** XAUUSD, USDJPY, EURUSD, GBPUSD, GBPJPY, EURGBP, BTCUSD, ETHUSD, US30*, UK100* M15+H4)
4. `.../pipeline_state/ultimate_book/operator/judgment/state/_fable_bar_pull_20260917/multi/` (check at prove time)
5. `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/multi/` (**PRESENT** subset)
6. `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars` (listed)

Peer admit: CSV **must** have `time_utc` (Challenge-true server−3h). April / broker-naive refused.

**MISSING on this clone (honest):**

- Live `shadow_logs/ultimate_book_launcher.jsonl` (host writer cycle tape). Needed to measure **actual** skip-reason frequencies vs generated intents.
- Live `judgment/astra/lab/a1/a1.jsonl` from Challenge pid (only `apply_receipt.jsonl` present in PR41 a1 dir).
- VPS Admin tree (host-mesh unreachable). Chair CopyFromBox / pull host jsonl when machineId `7cfa9657-...` is up.

Until launcher jsonl is pulled, replay uses **bar CSVs + generation/admit shadow** (`challenge_shadow.py`, `scripts/jev_host_systemone_shadow.py`), not live skip mix. Label that as **HIST_PARTIAL**.

---

## 3. Two-stage prove

### Stage A — Observe-every SHADOW (fire rate unchanged)

**Goal:** every generated candidate produces one `jev_client.evaluate(state)` receipt, including STAND/SKIP.

**Smoke (no R gate):**

| metric | gate |
|---|---|
| `n_candidates` | count generated intents + named generation_skips (exclude generator `None`) |
| `n_evaluate_ok + n_evaluate_skipped_honest` | ≥ `n_candidates` (deduped) |
| `n_evaluate_missing` | **0** on weekend/occupancy/kill-brake/authority-false/cost-skip |
| `n_posts / n_candidates` | ≤ 1.15 with `GTOS_JEV_A1_DEDUPE=1` (today ~4.0) |
| `calls_used` | < `GTOS_JEV_MAX_CALLS` (500000) |
| `broker_effect` | all false |
| `order_send` | 0 from this splice |
| writer `n_intents` / `placed` / skip-reason histogram | **identical** to pre-splice on same tape |
| p95 extra latency per cycle | record; Chair aborts if writer poll overrun |

**Pass → Chair may set `GTOS_JEV_A1_OBSERVE_EVERY=1` on Challenge only.** Not W7. Not APPLY place.

### Stage B — Place Choice hist-prove (fire rate **would** change)

**Goal:** typed Choice `PLACE|STAND|DELAY` over COMPLETE_STATE beats today's integer fire on Challenge tape **before** `GTOS_JEV_PLACE_CHOICE_APPLY=1`.

Replay construction:

1. Rebuild candidates from Challenge M15/H4 (+ D1 XAU only) via `books_for_symbol` as-of each decision bar.
2. Attach occupancy from Challenge deals (`deals_since_20260909.jsonl` in the 20260917 drop) — not invented.
3. Attach cost from named spread if tick tape exists; else `cost.source=unassembled` (honest).
4. `news_join=STATE_MISSING` unless host events.jsonl is present. Empty spine ≠ no HIGH.
5. Run **counterfactual policies** on the **same** candidate set:

| policy | place rule |
|---|---|
| `P0_integers` | today's book_owner continues + cost_screen + router (baseline) |
| `P1_observe_only` | P0 send; Jev logged (Stage A) |
| `P2_choice_shadow` | log Choice; send still P0 |
| `P3_choice_apply_stand` | send only if integers pass **and** Choice ≠ STAND |
| `P4_choice_apply_place` | integers envelope still bind; Choice PLACE may **unblock** only the hist-approved skip classes (cost, occupancy remint) — **never** kill/token/weekend/hard-off |

Envelope classes **never** enter P3/P4 unblock list: `ENV-*`, weekend embargo, circuit_breaker, max_dd_limit, identity, already_placed_this_bar, profile_missing_instrument_config.

Candidate skip classes for P4 (hist-first, ranked):

1. `pretrade_spread_r_refuse` / `cost_screen_spread_r` (gap ranked #4)
2. occupancy `already_placed_today` / sleeve_holds / lifecycle_guard (ranked #9) — remint/flatten only, not stack
3. `stale_late_entry_after_restart` DELAY vs PLACE
4. FLUID-PLC-001..007 promote (session 14 owns APPLY recipe)

---

## 4. Replay metrics (required)

Report **all four** plus n:

| metric | definition |
|---|---|
| `n` | candidates (and separately n_placed, n_stand, n_skip_by_reason) |
| `sumR` | sum of realized R on Challenge closes that match candidate_id / (symbol,sleeve,decision_bar). Missing close → **not** imputed. |
| `DD` | max drawdown of the equity curve of those R (static initial-balance basis, same as governor) |
| `fire_rate` | `n_placed / n_candidates` |

Also: WR, avgR, n_conflicts with sleeve-select (do not flip global select APPLY), `n_jev_dark`, `invented_high==0`, `order_send==0` on shadow.

**Per-symbol affinity** (held): at least XAUUSD, GBPJPY; then XAGUSD, EURUSD, NZD if tape present. Do not pool into one R and hide a loser.

**Module_ATR lens (optional column, not the gate):** if overlay tag fires on XAU, cite Module_ATR blotter sumR **separately**. Gate to APPLY uses **Challenge writer R**, not Module_ATR proxy.

---

## 5. Gate to APPLY

### Stage A (observe-every SHADOW)

Chair ENFORCE `GTOS_JEV_A1_OBSERVE_EVERY=1` on Challenge when:

- [ ] `n_evaluate_missing == 0` on a pulled host launcher jsonl **or** a lab replay of ≥1 Challenge session-day
- [ ] fire rate / placed tickets unchanged vs control
- [ ] budget not exhausted
- [ ] no broker_effect

### Stage B (PLACE Choice APPLY) — **not this session**

Chair ENFORCE `GTOS_JEV_PLACE_CHOICE_APPLY=1` only when **all** hold:

- [ ] Stage A live on Challenge ≥ 1 full session-day
- [ ] P3 or P4 vs P0: `sumR` **strictly greater**, `DD` not worse beyond Chair-named band, `n` large enough to not be a 3-trade toy
- [ ] fire_rate change signed and explained per skip_reason
- [ ] envelope skips still 100% STAND
- [ ] Module_ATR / Dig / Edge not used as the sole promote reason
- [ ] scoped symbols only if global tape thin (XAU / GBPJPY first — same discipline as sleeve-select; **do not** flip `GTOS_JEV_SLEEVE_SELECT_APPLY`)
- [ ] prove receipt written under `judgment/live/prove/UB-OBS-EVERY.json` with `wire_class` in `{A1,A2,A3,W_named}` and `proven: true`

**Fail → stay SHADOW.** Integers keep sending as today.

---

## 6. Replay drivers (existing; do not invent new news)

```bash
# Challenge-true bars only
python3 scripts/jev_host_systemone_shadow.py   # evaluate() on host-shaped state
python3 scripts/run_jev_everywhere_historical_prove.py --force \
  --write-tape judgment/astra/lab/jev_everywhere_closes/TAPE_0.jsonl

python3 -m pytest -q tests/judgment/test_jev_client.py \
  tests/judgment/test_news_inventory_live.py \
  tests/judgment/test_fluid_inventory.py
```

New tests from `PATCH_SKETCH.md` §8 land with the splice, not before.

---

## 7. Host jsonl pull (blocker)

When VPS is up, Chair pull (no SSH from this session):

- `pipeline_state/ultimate_book/operator/` heartbeat + ledger
- `shadow_logs/ultimate_book_launcher.jsonl` (or host equivalent)
- `judgment/astra/lab/a1/a1.jsonl`
- writer `events.jsonl` for news inventory (honest empty OK)

Until then Stage A lab uses CSVs + skip-reason **synthetic** from this map; label **HIST_PARTIAL**.

---

## 8. What would be a false prove

- Using Module_ATR yearfold HOLD sumR as if it were writer R
- Imputing R for STAND candidates that never had a close
- Counting silent generator `None` as candidates
- Flipping place APPLY because Typesafe usage was “too cheap”
- Unblocking weekend embargo / kill / token / hard-off
- Substituting April historical bars
