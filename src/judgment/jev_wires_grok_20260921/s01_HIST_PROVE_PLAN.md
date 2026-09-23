# HIST-PROVE PLAN — occupancy/place Choice (Challenge tape first)

**session:** `01_book_owner_lifecycle_place`  
**as_of_ict:** `2026-09-21T06:04:27+07:00`  
**status:** PLAN only. Not run this session. APPLY=0.  
**account:** FTMO Challenge login `0` / ns `operator`  
**affinity:** instrument × sleeve held. Scoped **XAUUSD** then **GBPJPY**.

Owner: hist/replay on Challenge tape **before any APPLY** that changes live fire rate (place, remint, flatten, occupancy exception).

## 1. Module_ATR honesty (non-negotiable)

Three R universes stay **separate columns**. Never sum. Never alias.

| lens | geometry | blotter (FOUND) |
|---|---|---|
| **Module_ATR** | file stop **0.75 ATR** / tgt **6.0 ATR** (`stop0.75_tgt6.0_ATR`) | `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` n=11239; `..._dsp_spring_close_on_20low_through_the_box.jsonl` n=5659; GBPJPY vss n=818; GBPJPY sub_mid_dn_re proxy SHORT n=2057 |
| Dig_3R | Dig 3R | **do not merge** |
| Edge_ATR | Edge ATR-R | **do not merge** |

Rules:

- Occupancy counterfactual R = **Module_ATR R only** (`R_Module_ATR` / blotter `R_ATR` when `lens=Module_ATR`).
- If a skip row has no Module_ATR blotter join → `R_Module_ATR=null` (honest missing). Do not fill from Dig/Edge.
- ATR itself comes from named Challenge M15 `atr14` (`primitives.atr14` on Challenge CSV). **Do not invent ATR. Do not invent regime_tag.** `regime_tag=PENDING` if unassembled.
- Geometry proxy ≠ live `TradeIntent` path (no stay_timing / peer_panel / admission). Yearfold overlays already stamp this honesty — keep it.
- Package B → `sub_mid_dn_revert` alias is **forbidden** (do-not list).

## 2. Challenge tape (FOUND — not MISSING)

Search dirs from `src/judgment/bars.py:challenge_search_dirs`:

| path | what |
|---|---|
| `_pr41_land/.../judgment/astra/lab/challenge_shadow_20260917/XAUUSD_{M15,H4,D1}.csv` | XAU parent |
| `.../challenge_shadow_20260917/multi/GBPJPY_{M15,H4}.csv` | GBPJPY **present** |
| `.../multi/{USDJPY,EURUSD,GBPUSD,EURGBP,BTCUSD,ETHUSD,US30*,UK100_cash}_{M15,H4}.csv` | peers |
| `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/` | XAU + subset multi; **GBPJPY missing on this copy** — use PR41 multi |

April `data/historical*` is **never** Challenge tape (`admit_challenge_peer_csv` refuses no-`time_utc` / last print before 2026-09-17).

**MISSING honestly:**

- Live VPS `ultimate_book_launcher.jsonl` occupancy-skip stream (Admin unreachable this seat).
- Per-skip Module_ATR joined counterfactual table (not yet built).
- Host leftover-ship F5 yield vs PR41 W7 hard-refuse paired tape after Sep 13 2-stop cut.

Nightly CF (`nightly/2026-09-16/DECISIONS.json`) is **WATCH**, not prove.

## 3. Replay recipe

### 3.1 Harvest occupancy-skip rows

Sources (in order):

1. Challenge launcher / runtime-learning packets with `skip_reason` in:
   - `already_placed_today`
   - `cluster_unit_already_placed_today:*`
   - `sleeve_already_holds_symbol` / `_broker`
   - `same_broker_symbol_open_position_lifecycle_guard`
   - `stale_late_entry_after_restart`
   - `cost_screen_spread_r:*` (inventory `pretrade_spread_r_refuse`)
2. If launcher JSONL MISSING on box: reconstruct from Challenge deals + `occupancy_at` as-of each Module_ATR blotter fire (honest reconstruction; stamp `occupancy_source=challenge_deals_reconstructed`).
3. Do **not** use Sep 1–12 290-count as the prove window (pre-2-stop cut). Prefer **post-2026-09-13** + multiyear Module_ATR blotter as-ofs.

### 3.2 For each skip row, build COMPLETE_STATE

Use `COMPLETE_STATE_PLACE_OCCUPANCY.schema.json`. Required:

- occupancy facts at as-of (not future)
- cost.spread_r from named tick **or** STATE_MISSING
- freshness vs named bar close
- `news_join=STATE_MISSING` unless host events join is real
- `module_atr.R_available` only when blotter joins

POST `jev_client.evaluate(state)` with `place_occupancy_questions` + existing fan-out. Budget `GTOS_JEV_MAX_CALLS=500000` on the prove process.

### 3.3 Counterfactuals (code-owned, not chat)

For each row, compare **static skip** vs **Jev-interpreted action**, using **Module_ATR R** of the *would-have-been* unit:

| static | Jev | credit |
|---|---|---|
| skip `already_placed_today` | HOLD/STAND | 0 (same) |
| skip `already_placed_today` | PLACE_ISOLATED and `isolated_reentry_legal` | + Module_ATR R of that blotter fire (or null) |
| skip `already_placed_today` | PLACE_ISOLATED and NOT isolated | illegal → treat as HOLD (code) |
| skip `lifecycle_guard` | HOLD | 0 |
| skip `lifecycle_guard` | FLATTEN_ADD | **do not credit** until flatten path is specified; v0 illegal |
| skip `stale_late_entry` | STAND | 0 |
| skip `stale_late_entry` | PLACE_FRESH | + Module_ATR R if a blotter fire exists at that bar, else null |
| skip `cost_screen_spread_r` | COST_DOMINATED | 0 |
| skip `cost_screen_spread_r` | COST_OK | + Module_ATR R **minus named spread_r** (cost honesty); if ATR missing → null not 0 |

Never invent a fill. If Module_ATR blotter has no row at that as-of/sleeve/symbol → `n_null_R` increment, do not impute.

### 3.4 Metrics (gate inputs)

Per cell `{symbol × sleeve × reason}` and overall scoped XAU / scoped GBPJPY:

| metric | definition |
|---|---|
| `n` | skip rows with complete occupancy facts |
| `n_decidable` | Jev ok + not dark |
| `n_illegal_label` | PLACE_ISOLATED without isolated_legal, FLATTEN_ADD, REMINT send |
| `fire_rate_static` | 0 on skip rows (by construction) vs live writer fire rate on Challenge |
| `fire_rate_jev` | fraction PLACE / PLACE_ISOLATED / PLACE_FRESH / COST_OK that code would allow |
| `sumR_Module_ATR_static` | 0 on skip (didn't take) |
| `sumR_Module_ATR_jev` | sum of credited Module_ATR R |
| `meanR` | sumR / n_credited |
| `DD_proxy` | running Module_ATR equity curve of credited takes (file-exit, not live SL) |
| `n_two_stop_override_attempts` | must be 0 allowed |

Report Dig_3R / Edge_ATR **side columns** if joined, labeled `NOT_GATE`.

## 4. PASS / FAIL gate to APPLY

Chair APPLY is **not** this session. Gate for a later Chair receipt:

**PASS (scoped occupancy PLACE_ISOLATED on one symbol×sleeve):**

1. `n_decidable >= 20` (process_lock fluid-label bar)
2. `n_illegal_label / n_decidable <= 0.05`
3. `sumR_Module_ATR_jev > sumR_Module_ATR_static` (static is 0 on skips) **and** `sumR_Module_ATR_jev > 0`
4. Module_ATR DD_proxy **not worse** than taking-all-skips DD (if taking-all is computable; else vs 0)
5. Fire-rate increase bounded: no more than **one** extra unit per (sleeve,symbol,UTC day) and **never** when `two_stop_exhausted`
6. Affinity held (XAU three_fresh/spring; GBPJPY vss — **not** Package B alias)
7. Time-split anti-oracle: last 30% of blotter as-ofs held (sign of sumR)
8. `news_join` never invented

**FAIL / stay SHADOW:**

- n too small (nightly lifecycle_guard METAL n=10 is WATCH, not PASS)
- only Dig_3R R available
- Jev wants FLATTEN_ADD / REMINT send
- would place on `already_placed_this_bar` or same-cycle dupe
- scoped symbol not XAUUSD/GBPJPY

**Cost Score APPLY (separate receipt):**

- COST_OK must not increase DD vs static skip on Challenge cost_screen rows
- TRIM may land through existing `GTOS_JEV_APPLY_LIVE` size path (already judged) — **not** a place-rate change
- COST_DOMINATED == static skip → no fire-rate change, no APPLY needed

**Freshness APPLY:** only if PLACE_FRESH sumR_Module_ATR > 0 on restart-late rows **and** n_decidable>=20. Else keep STAND.

## 5. Nightly CF (cite, do not treat as PASS)

From `nightly/2026-09-16/DECISIONS.json` (repeated 09-14..09-20 markdown):

| cell | n | sum_R | reading |
|---|---:|---:|---|
| METAL/INDEX `already_placed_today` | 48 | **+21.6** | refusing left +EV on table? WATCH. Strongest occupancy hist hint. |
| FX `already_placed_today_fx8` | 32 | +1.54 | weak |
| FX `already_placed_today` | 5 | +0.34 | n too small |
| METAL/INDEX `lifecycle_guard` | 10 | **+13.0** | missed +EV candidate; n=10 **not** PASS |
| FX `lifecycle_guard` | 3 | +0.54 | n too small |
| `already_placed_this_cycle` FX/METAL | 4 / 4 | −2.36 / −4.0 | refusing was better → **ENVELOPE_KEEP** |

Sep 1–12: `already_placed_today` 137 + `lifecycle_guard` 153 = 290 (pre-cut). Re-measure **after Sep 13**.

## 6. Run order (Chair executor)

1. Join Module_ATR blotters to Challenge M15 as-ofs for XAU `dsp_three_fresh` + `dsp_spring` (affinity).
2. Reconstruct occupancy_at from Challenge deals (FOUND occupancy.py).
3. Shadow POST place_action / occupancy_action / cost_action (no APPLY).
4. Scoreboard Module_ATR-only.
5. If PASS: draft **scoped** `GTOS_JEV_OCCUPANCY_CHOICE_APPLY=1` receipt for XAU three_fresh/spring **isolated re-entry only**.
6. Widen GBPJPY vss (conflict with sub_mid is session 03; occupancy prove still GBPJPY-scoped).
7. Cost Score hist (ranked #4) as a **separate** receipt.
8. Do **not** flip global sleeve-select APPLY.
9. Do **not** land FLATTEN_ADD / REMINT send from this family.

## 7. Script sketch (not executed)

`scripts/jev_occupancy_hist_prove.py` (Chair later):

- `--lens Module_ATR` required
- `--symbols XAUUSD,GBPJPY`
- `--apply false` hard-coded
- writes `judgment/astra/lab/wires/OCCUPANCY_PLACE_HIST_PROVE.json`

This session does **not** run it (design-only; Typesafe usage ramp is session 19).
