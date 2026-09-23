# HIST-PROVE PLAN — TWO_STOP_REMINT_Choice

**session:** `08_two_stop_remint_choice`  
**as_of_ict:** `2026-09-21T06:05:25+07:00`  
**account:** Challenge login `0` · ns `operator` · magic `0` · pass line 110000  
**place=false · apply=false · order_send=0 this session**  
**lens law:** Challenge_book first. Module_ATR / Dig_3R / Edge_ATR are **separate** columns. Never merge R universes.

---

## 0. Why prove at all

Integer 2-stop is blunt. Owner remint/place/flatten is **OPEN after prove**, not eternal-off.

Two Challenge exhibits from Weekly Market Brief 2026-09-20 (same isolated-reentry law, opposite $):

| day | symbol | sleeve | n same-day | result | WMB family? |
|---|---|---|---:|---|---|
| 2026-09-15 | XAUUSD | `dsp_three_fresh_lower_lows` | 2 | ≈ **+$354** (orig_stop then time_stop winner) | **NO** — other-sleeve reprint must remain legal |
| 2026-09-17 | XAUUSD | `dsp_two_bar_thrust_into_20high_continues` | 2 | ≈ **−$300** (both orig_stop) | **YES** — WMB exhibit |

Global Sep 13 cap (`F5_SAME_SLEEVE_ORIG_STOP_DAY_CAP=2` on **all** sleeves) would have starved **both**. WMB scopes the starve to two_bar / rejection_wick / isolated_spike. Jev Choice is the hist-first overlay: STAND on spent bleed remints, not STAND on paying other-sleeve reprints, SWITCH_SLEEVE when alive_menu has a KEEP sleeve, FLATTEN_SIBLING only if a sibling is actually open (rare under keep-one).

**Gate:** no `GTOS_JEV_TWO_STOP_REMINT_APPLY=1` until this prove PASS. Integer WMB splice (scoped refuse) is fail-closed starve — still replay before land because it changes fire rate of those families.

---

## 1. Tape paths FOUND (box mirrors)

### 1.1 Challenge-true closes (use these)

| path | what | honesty |
|---|---|---|
| `/workspace/gtos/close_loop/war_room_20260920/learning_scoreboard_60.jsonl` | per-ticket Challenge rows login 0; `realised_r_unit150`, `exit_class`, `sleeve`, `miss_type`, geometry held | `regime_tag: null` on sampled two_bar / three_fresh rows → **PENDING, do not invent** |
| `/workspace/gtos/close_loop/war_room_20260920/vps_hydrate/challenge_0_closed.json` | MT5 closed positions n=60 from 2026-08-01; `comment_in` `F5:sleeve`; profit_net | broker $; not Module_ATR R |
| `/workspace/gtos/close_loop/war_room_20260920/YTD_2026_CHALLENGE_TRUE_SLICE_20260920.md` | Challenge_book n=38, sumR **−32.3981**, window through **2026-09-12** | Sep 15/17 remints **outside this window** |
| `/workspace/gtos/close_loop/war_room_20260920/loss_autopsy_summary.json` | sleeve n / sum_R / tickets | two_bar split across truncated `dsp_two_bar_t` and full name |
| `/workspace/gtos/close_loop/war_room_20260920/LOSE_NARRATIVE_20260920.json` | miss_type narratives | |
| `/workspace/gtos/briefs/WEEKLY_MARKET_BRIEF_20260920.md` | Sep 15/17 remint $ | weekly, not a blotter |
| `/workspace/gtos/CHALLENGE_ZERO_WIN_AUTOPSY_20260910.md` | `same_sleeve_remint_after_stop` n=5 −$762.10 | pre-cut first-22 |
| `/workspace/gtos/fable_joint_pull_20260917/just_closed_siblings.json` | live `closed[]` through 2026-09-17T09:48Z | **does not include** later Sep 17 two_bar remint close; `updated_ict` stale 09-08; 24h prune |
| `/workspace/gtos/close_loop/war_room_20260920/jev_everywhere_lessons_0.jsonl` | train lessons | |

### 1.2 Module_ATR — honesty (REQUIRED)

**FOUND Module_ATR blotters (NOT WMB families):**

- `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl`
- `blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl`
- GBPJPY sub_mid / vss; XAG metals_core / metal_session_reversion / sub_xvol_pullback
- CF C scoreboard: `CF_C_MODULE_ATR_XAU_THREE_FRESH_SPRING_SCOREBOARD_20260920.md`  
  three_fresh Module_ATR C vs A Δ **+146.53**; spring Δ **+20.73** — **KEEP-family research only**

**MISSING — do not invent:**

- No `blotter_Module_ATR_*two_bar*`
- No `blotter_Module_ATR_*rejection_wick*`
- No `blotter_Module_ATR_*isolated_spike*`
- No Module_ATR yearfold for WMB remint cells
- `regime_tag` null on Challenge scoreboard two_bar rows → **STATE_MISSING / PENDING**

**Forbidden:**

- Invent ATR-at-entry or Module_ATR R for two_bar / rejection / isolated
- Merge Dig_3R + Edge_ATR + Module_ATR into one sumR
- Use three_fresh/spring Module_ATR yearfold as a proxy for two_bar remint quality
- Treat geometry_proxy OHLC Module_ATR as live TradeIntent path

**Allowed ATR:** named `geometry.atr14` / `stop_atr` on gold_state **when M15 is assembled** — that is tape ATR on COMPLETE_STATE, not a Module_ATR lens scoreboard. If unassembled, field is null.

WMB remint prove metrics = **Challenge_book** `realised_r_unit150` and/or broker `profit_net` on login 0. Separate optional column: Module_ATR **only** if a real blotter appears later.

---

## 2. Universe construction (replay)

### 2.1 Same-day same-sleeve chains

From Challenge closed + scoreboard, group by `(symbol, sleeve_norm, session_day_utc[:10])` ordered by `close_utc`.

A **remint member** is any close after the first orig_stop of that group the same day (parent excluded from the remint-$ column, included in chain n).

Sleeve-norm: treat `dsp_two_bar_t` and `dsp_two_bar_thrust_into_20high_continues` as the **same WMB family token** `two_bar` (substring law). Same for `dsp_isolated_*` / `dsp_isolated_spike_high` and `dsp_rejection*` / `dsp_rejection_wick_then_through`.

### 2.2 Named cells already on tape (seed; expand on replay)

**WMB in-scope (bleed exhibit + cousins)**

| parent → member | symbol | sleeve family | day | exit | Challenge R / $ | notes |
|---|---|---|---|---|---|---|
| 291377397 → **291402598** | US30.cash | isolated_spike | 2026-09-10 | orig_stop / orig_stop | member −1.03R / −$163-class | ZERO_WIN remint; US30 now hard-off — **do not reopen** via Choice |
| 291210052 | XAUUSD | two_bar (`dsp_two_bar_t`) | 2026-09-09 | orig_stop | −1.0102R / −$151.53 | held 3m41s; NY; miss_type false_structure; **single**, not a 2-stop chain |
| 291383082 | XAUUSD | two_bar (full name) | 2026-09-10 | orig_stop | −1.0847R / −$162.70 | held **21s**; Asia; miss_type event_gap; BOJ T±60 LABEL not invented HIGH |
| **293437038** | XAUUSD | two_bar (`dsp_two_bar_t`) | 2026-09-17 | orig_stop | −0.98R / −$146.90 | fill 12:32Z close 14:08Z; NY; **WMB weekly exhibit member**. Parent of the n=2 chain is **MISSING from just_closed_siblings snapshot** (file cut at 09:48Z). Hydrate from scoreboard + MT5 closed. |
| 291426696 | US30.cash | rejection_wick | 2026-09-10 | orig_stop | −1.18R | INDEX bleed; US30 hard-off now |
| 293592749 | ? | rejection_wick | later | orig_stop | in loss_autopsy n=2 sum_R −2.22 | expand on replay |

**Out of WMB family (must NOT be starved by scoped circuit)**

| chain | symbol | sleeve | day | result |
|---|---|---|---|---|
| 292524534 → later time_stop winner (weekly +$354 n=2) | XAUUSD | three_fresh | 2026-09-15 | **paid**. 292524534 itself orig_stop −1.01R / −$150.93 London. Winner ticket **not fully identified in YTD slice** (window ends 09-12). Weekly brief is the $ source — replay must join closed.json for the time_stop child. |
| 293024386 | XAUUSD | three_fresh | 2026-09-16 | orig_stop −1.01R / −$150.94 — different day than 09-15 chain |
| 291072108 → **291096187** | XAUUSD | walked | 2026-09-09 | remint member −$143-class; **out of WMB family** — occupancy session 16 / starve-on-evidence, not this Choice |
| US30 bleed 291124471 → 291139109 → 291167802 → 291186653 | US30 | bleed | 2026-09-09 | n=4 orig_stops; **hard-off now**; global 2-stop would have cut at n=2 (−$600 → ~−$300 per Astra). Do not reopen. |

### 2.3 MISSING tape (state honestly)

- Full Sep 17 two_bar **parent ticket** of 293437038 not in `just_closed_siblings.json` snapshot (mtime/cutoff 09:48Z). **Must hydrate from** `challenge_0_closed.json` + scoreboard + any later closed_joined. If parent still missing after join: cell n is incomplete — **do not invent**.
- Sep 15 three_fresh **winner ticket** not in YTD 09-12 slice. Weekly +$354 is the cited $; replay must find the time_stop child or mark `$ source = weekly_brief_not_joined`.
- Live VPS `just_closed_siblings.json` post-09-17: **UNREACHABLE** this seat (host-mesh). Use box snapshots + Challenge hydrate.
- `closed_joined` refresh after Sep 13 (Astra P1.2) — **not found as a named file**. Closest: `challenge_0_closed.json` (n=60) + scoreboard_60.

---

## 3. Policies to score (counterfactual, same tape)

Replay each chain **as-of the member's fill**, never with future closes (two_stop.py already supports `as_of_utc`).

| id | policy | fire-rate effect |
|---|---|---|
| P0 | **keep_all isolated yield** (pre-WMB leftover) | 15m+flat yields already_placed_today for all sleeves |
| P1 | **global 2-stop** Sep 13 (`cap=2` all sleeves) | refuse remint for ANY sleeve at n>=2 |
| P2 | **WMB scoped integer** (Chair ENFORCE 2) | refuse remint only if family in {two_bar, rejection_wick, isolated_spike} AND n>=2; other sleeves keep P0 |
| P3 | **Jev Choice SHADOW** | evaluate() remint_action on every P0 candidate with n>=1 orig_stop same day; **does not change fills** (receipts only) |
| P4 | **Jev Choice APPLY (counterfactual)** | STAND → drop member; REMINT_OK → keep member; SWITCH_SLEEVE → drop this sleeve (do not credit a different sleeve's $ unless that sleeve actually fired — no invented fills); FLATTEN_SIBLING → drop member, do not credit flatten $ (no flatten tape) |

P4 SWITCH_SLEEVE / FLATTEN_SIBLING **must not invent trades**. Credit is only: avoided remint $ (member not taken). Switching is a LABEL until a real other-sleeve fill exists on that bar.

---

## 4. Metrics (required)

Per policy, per universe (WMB-family chains vs all-sleeve remint chains vs KEEP-family reprints):

| metric | definition |
|---|---|
| `n` | number of remint **members** (not parents) |
| `n_chains` | number of same-day groups with n_closes>=2 |
| `sumR` | sum of Challenge `realised_r_unit150` on members. **Separate** broker_usd column. **Never** add Module_ATR R into this. |
| `sum_usd` | sum of broker `profit_net` on members |
| `DD` | max running drawdown of concatenated member R in time order |
| `fire_rate` | members / (members + refused_by_policy) |
| `n_stand` / `n_remint_ok` / `n_switch` / `n_flatten` | Choice histogram (P3/P4) |
| `n_jev_dark` | evaluate skip/error |
| `n_count_unknown` | closed_absent / deals-label |

Report WMB-family slice and KEEP-family slice **as two tables**. A policy that improves two_bar by killing three_fresh is a **FAIL** even if sumR looks better on a merged table.

---

## 5. PASS / FAIL gate to Chair APPLY

All must hold on Challenge login 0 tape (not verification 0):

1. **WMB-family remint members:** P2 (scoped integer) sumR >= P0 sumR and sum_usd >= P0 (starve bleed remints). Seed: Sep 17 two_bar −$300 should be **cut at the second fill**. Isolated US30 remint is already dead via hard-off — do not count as a P2 win.
2. **KEEP / out-of-family reprints:** P2 fire_rate on three_fresh / spring / vss / expanding **equals P0** (scoped circuit must not touch them). Sep 15 three_fresh +$354 must **survive P2**.
3. **P1 global cap vs P2:** if P1 kills the three_fresh winner, that is evidence **against** applying global cap as the Jev-less default. P2 is the integer envelope to land.
4. **P4 vs P2:** APPLY only if  
   - WMB-family sumR(P4) >= sumR(P2)  (Choice does not re-open bled remints)  
   - KEEP-family sumR(P4) >= sumR(P2)  (Choice does not STAND a paying reprint)  
   - DD(P4) <= DD(P2) + 0.25R slack  
   - fire_rate(P4) on WMB family <= fire_rate(P2)  (no fire-rate explosion)  
   - `n_jev_dark == 0` on decidable cells OR dark cells fail-closed STAND (same as P2)
5. **n floor:** at least **n=8** remint members across families **or** honest BLOCKED with n found (do not pad with invented Module_ATR years).
6. **Affinity:** XAU×two_bar, XAU×three_fresh, US30×isolated (hard-off) scored separately. No cross-instrument R mix.
7. **FLATTEN_SIBLING:** if n_flatten>0 and no open sibling on tape, those answers are **wrong** — FAIL P4 until questions/state fixed. Do not APPLY flatten.
8. **SWITCH_SLEEVE:** LABEL accuracy vs alive_menu only; no $ credit for unfilled sleeves.
9. **Module_ATR:** WMB family Module_ATR column stays **MISSING**. Optional KEEP-family Module_ATR (three_fresh/spring CF C) may be cited as **why SWITCH_SLEEVE toward those sleeves is research-plausible** — not as remint sumR.

If n is too small for P4: **SHADOW continues**, integer P2 may still Chair-ENFORCE as fail-closed starve (proposal 2). Choice APPLY waits.

---

## 6. Replay procedure (no broker)

```
1. Load learning_scoreboard_60.jsonl ⋈ challenge_0_closed.json
   join key: ticket / position_id. Prefer Challenge realised_r_unit150.
2. Build occupancy as_of each candidate fill using two_stop.occupancy_from_closed
   with as_of_utc = fill_utc. Never leak later same-day stops.
3. Integer P0/P1/P2 from refuse_reason + cap. Writer 15m HOLD always first.
4. Assemble COMPLETE_STATE (session 10 composer). remint.news_join = STATE_MISSING
   unless official_high_spine is honestly joined. regime_tag stays PENDING if null.
5. P3: jev_client.evaluate(state) with symbol_fanout_questions ∪ remint_action.
   GTOS_JEV_TWO_STOP_REMINT_SHADOW=1 APPLY=0. Log jsonl under this OUT dir.
6. P4: counterfactual drop members where Choice STAND (and integer would have
   allowed). Do not simulate new SWITCH_SLEEVE fills.
7. Write PROVE receipt: n, sumR, sum_usd, DD, fire_rate, histograms, blockers.
8. Chair only: ENFORCE P2 integer splice; APPLY P4 flag iff PASS.
```

`GTOS_JEV_MAX_CALLS=500000`. One evaluate() per remint candidate (fan-out questions in the same POST).

---

## 7. Blockers (prove may be BLOCKED, design is not)

| blocker | effect |
|---|---|
| VPS Admin unreachable | cannot confirm host-dirty 2-stop bytes vs leftover mirror |
| Sep 17 two_bar parent ticket not in siblings snapshot | join closed.json; if still missing, n incomplete |
| Sep 15 three_fresh winner ticket not in YTD 09-12 | join closed.json; else cite weekly $ as unverified join |
| Module_ATR blotter MISSING for WMB families | **do not invent**; Challenge_book metrics only |
| `regime_tag` null | PENDING / STATE_MISSING |
| WMB `refuse_reason` not imported | integer P2 not live on leftover mirror |
| n remint members may be < 8 on Challenge-true | SHADOW-only; integer P2 still Chair-optional |

---

## 8. Next Chair actions (not this session)

1. LABEL this hist-prove plan.
2. ENFORCE WMB integer splice into isolated-yield (**scoped families only**) after a dry replay of P2 vs P0.
3. VETO any land that flips `GTOS_JEV_SLEEVE_SELECT_APPLY` or auto-flattens.
4. APPLY `GTOS_JEV_TWO_STOP_REMINT_APPLY=1` **only** after P4 PASS receipt exists.
5. Do not ENFORCE global cap as the Jev-less default if P1 kills three_fresh.

This session does not Chair-ENFORCE, does not APPLY, does not place.
