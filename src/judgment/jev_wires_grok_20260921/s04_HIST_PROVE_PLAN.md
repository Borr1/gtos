# HIST-PROVE PLAN — place_fluid Choice PLACE|STAND|DELAY

**session:** `04_fluid_gates_place_fluid_family`  
**as_of_ict:** `2026-09-21T06:20:00+07:00`  
**status:** PLAN (not run this session)  
**queue:** `/workspace/gtos/close_loop/war_room_20260920/PLACE_FLUID_HIST_PROVE_QUEUE_20260921.md` was **QUEUED**; this is the executable recipe.  
**never_broker_place:** true  
**Module_ATR honesty:** named blotter ATR only; never invent ATR/regime; never merge Dig_3R / Edge_ATR R universes.

---

## 0. Why LABEL prove ≠ PLACE prove

Wave L applied `FLUID-PLC-001` as **label** (`n_decidable=97`, `n_moved=97`, `n_distinct=2`). Wave J applied PLC-002/003/005/006 as labels. PLC-004 was `constant_on_this_tape`; PLC-007 was `missing_named_state`; both later inherited `APPLIED_NAMED` with **n=0** on the inherit record.

Those bars (`min_decidable=20`, `min_non_default=5`, `min_distinct=2`, `invented_high_forbidden`) prove the **label moves**. They do **not** prove that a Choice `PLACE` improves Challenge **sumR / DD / fire rate** vs writer actuals.

Owner override: if hist shows Jev better at place → prove → APPLY. Shadow LABEL is not that hist.

---

## 1. Tapes (found)

### 1.1 Challenge file-exit (PRIMARY — required)

| artifact | path | n |
|---|---|---|
| Challenge shadow pack | `_pr41_land/ai-trading-agent/judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl` | **97** |
| kinds | open 1 / slate 40 / slate_skip 10 / deal_close 46 | WAVE_M |
| deals | `.../deals_since_20260909.jsonl` | 47 |
| events | `.../events_since_20260915.jsonl` | host news + stop_move |
| closes tape | `.../jev_everywhere_closes/TAPE_0.jsonl` | 63 |
| M15+H4 | `.../challenge_shadow_20260917/multi/` | XAUUSD, EURUSD, GBPUSD, EURGBP, USDJPY, GBPJPY, US30 |

Account surface: login **0**, ns `operator`, magic `0`. Verification 0 quarantined.

**MISSING (honest):**

- GBPJPY pack rows = **0** (tape landed, unused). Do not invent.
- BTC/ETH/UK100 M15+H4 **absent**. Do not pull as trade surface.
- Host news writer `READ` count on this tape = **0** (NOT_READ / UNKNOWN / None). Event Noul must abstain when spine honesty fails — do not invent HIGH.
- Live VPS Admin tree **UNREACHABLE** this seat. Re-run same recipe on host when machineId Shell is up.

### 1.2 Module_ATR blotters (SECONDARY lens — tagged, never merged)

| blotter | n | affinity |
|---|---|---|
| `blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` | 11239 | XAUUSD × three_fresh |
| `blotter_Module_ATR_XAUUSD_dsp_spring_close_on_20low_through_the_box.jsonl` | 5659 | XAUUSD × spring |
| GBPJPY vss / sub_mid proxies | present | **sub_mid_dn_re_proxy is NOT Package B merge** — do-not list |

Row contract (do not "fix"):

```
lens=Module_ATR
exit_shape=stop0.75_tgt6.0_ATR
fill_model=geometry_proxy_ohlc_touch_module_ATR_exit_NOT_broker_NOT_module_exact
R == R_ATR   # Module_ATR R only
atr          # named from blotter OHLC; if missing → drop row, do not invent
```

**Honesty rules:**

1. Geometry proxy OHLC-touch is **not** a broker fill. Score as `geometry_proxy`, never as Challenge file-exit.
2. Do **not** merge Dig_3R or Edge_ATR R into Module_ATR sumR (doctrine do-not: "Merge Dig3R Module_ATR lenses").
3. Do **not** invent `regime_tag` from Module_ATR year-fold. `regime_tag=PENDING` unless S14 features exist on that as-of.
4. Year-fold train rows (`sumR_year` 2014–2026) are **affinity context**, not place labels. Geometry print alone ≠ strike.
5. `research_armed_tags` may overlay three_fresh/spring on STATE; **never** splice into `live_armed_set`.
6. If a Challenge row lacks `geometry.atr14` and `timeframes.m15.atr14`, PLC-005 / geo_score are **undecidable**. DELAY. Do not copy blotter ATR onto a different clock.

---

## 2. Counterfactual design

For each Challenge pack row with `kind in {open, slate, slate_skip, deal_close}`:

1. Rebuild gold_state as-of (already in pack `state`).
2. Attach COMPLETE_STATE extras when named (occupancy from deals, news inventory extra, last_refusal). Missing → null.
3. `evaluate(state)` with `GTOS_JEV_MAX_CALLS=500000` **or** offline local_answers if key/budget skip — **receipt must record source=`jev` vs `local`**. Local must not PLACE.
4. Read `place_action` (Jev) plus PLC-001..007.
5. Envelope integers as-of: hard_off, two_stop COUNT, occupancy keep-one, dead window, token. If hit → force STAND (code).
6. Map:

| writer actual | Choice | bucket |
|---|---|---|
| printed (deal_close or open) | PLACE | TP (true place) |
| printed | STAND or DELAY | FN (Jev would have held) → **saved R** = −realized if realized<0, **cost** = −realized if realized>0 |
| not printed (slate_skip / slate never filled) | STAND/DELAY | TN |
| not printed | PLACE | FP — **fill MISSING**. Do not invent a fill. Count as fire-rate pressure only; R=null |

**Do not** simulate fills for FP. Honest `STATE_MISSING` on counterfactual R.

S15 tape-authority already on sidecar (do not invent new numbers):

- false_abstain = 0
- false_admit_n = 29, false_admit_tape_R = −28.9172
- cost_avoided_by_reject_n = 23, cost_avoided_by_reject_tape_R = −24.6586
- `place: infinity_veto` is the **retired S15 cage**; recompute place Choice vs those 29 false-admits as a **named slice**, not a new HIGH.

FIRE 1201 KEEP wins that must not flip (p0_hist_prove): tickets `291816474` (+1.87R), `293540988` (+2.962R), `291794419` (+3.02R). Residuals `291087142` / `293128383` stay REVIEW/KEEP labels, not hard-off.

---

## 3. Metrics (required on receipt)

Compute **three** books, never mixed:

| book | R column | when |
|---|---|---|
| `Challenge_file_exit` | deal `R` / tape realized | PRIMARY gate |
| `Module_ATR_geometry_proxy` | blotter `R_ATR` | SECONDARY, tagged `lens=Module_ATR` |
| `Dig_3R` / `Edge_ATR` | — | **out of this prove** |

Per book:

```
n                  # rows considered
n_decidable        # place_action decidable (Jev ok or local DELAY)
n_jev_ok           # evaluate() ok
n_jev_dark         # skip/error → DELAY
n_PLACE / n_STAND / n_DELAY
fire_rate          # n_PLACE / n_decidable
n_writer_printed   # open+deal_close
sumR_writer        # sum realized on printed
sumR_jev_place     # sum realized on TP ∪ (FN excluded)
sumR_delta         # sumR_jev_place - sumR_writer   # FN-hold of losers is +delta
maxDD_writer
maxDD_jev
n_invented_high    # must be 0
n_invented_atr     # must be 0
n_FP_no_fill       # PLACE on unfilled; R null
keep_win_preserved # FIRE 1201 three tickets still PLACE or DELAY-not-STAND-against-keep
```

Also per symbol × sleeve (affinity). Do not pool US30/BTC hard-off into XAU sumR.

---

## 4. PASS bars (frozen before read)

**Primary (Challenge file-exit), scoped XAUUSD first:**

| bar | value | why |
|---|---|---|
| `n_decidable` | ≥ 20 | same as fluid label bars |
| `n_jev_ok` | ≥ 20 **or** explicit `jev_dark_fail` | local-only PLACE is illegal; if Jev dark, prove is BLOCKED not PASS |
| `n_invented_high` | 0 | empty spine claimed HIGH fails |
| `n_invented_atr` | 0 | missing ATR used as number fails |
| `n_refused_cost_skip` | 0 | PLC-003/UB-PLC-017 cannot_refuse |
| `sumR_delta` | > 0 | Jev PLACE/STAND/DELAY beats writer keep-all on printed set |
| `maxDD_jev` | ≤ `maxDD_writer` | do not buy R with worse DD |
| `fire_rate` | ≤ writer_print_rate × 1.15 | do not explode fire |
| `keep_win_preserved` | true | FIRE 1201 |
| `envelope_bypass` | 0 | Choice never prints through ENV-* |

**Secondary (Module_ATR geometry_proxy)** — **informational**, cannot alone PASS place APPLY:

- Report `sumR_Module_ATR` on the **same affinity cells** (XAU×three_fresh, XAU×spring) with year-fold honesty.
- If Module_ATR year ≤ 0 (e.g. three_fresh 2026 `sumR_Module_ATR=−53.8568` from train absorb), PLACE on that year-proxy is **not** a KEEP. Do not treat geometry_proxy winners as Challenge payout.

**GBPJPY scoped:** blocked until pack n_decidable≥20 on GBPJPY Challenge rows (currently 0). Tape exists; pack rows MISSING.

---

## 5. Procedure (executor)

```
export GTOS_JEV_FLUID_GATES_SHADOW=1
unset GTOS_JEV_PLACE_FLUID_APPLY   # must stay off
export GTOS_JEV_MAX_CALLS=500000
# GTOS_JEV_A1_CALL default-on if key present

# 1) Re-score pack with place_action in questions (shadow, --no-apply)
python3 scripts/jev_challenge_shadow.py   # or replay existing pack + local+jev merge

# 2) Prove PLACE vs writer actuals
python3 scripts/jev_place_fluid_hist_prove.py \
  --shadow judgment/astra/lab/challenge_shadow_20260917/shadow.jsonl \
  --deals  judgment/astra/lab/challenge_shadow_20260917/deals_since_20260909.jsonl \
  --out    judgment/astra/lab/wires/PLACE_FLUID_HIST_PROVE.json \
  --lens   Challenge_file_exit \
  --no-apply

# 3) Secondary Module_ATR report (tagged, not a PASS)
python3 scripts/jev_place_fluid_hist_prove.py \
  --blotter /workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl \
  --lens Module_ATR \
  --affinity XAUUSD,dsp_three_fresh_lower_lows \
  --no-apply
```

`scripts/jev_place_fluid_hist_prove.py` does **not exist yet** — sketch in `drafts/hist_prove_place_fluid.py`. This session does not run it against TypeSafe (design + plan only). Chair executor runs it.

Refuse exit 2 if `GTOS_JEV_PLACE_FLUID_APPLY` or `GTOS_JEV_FLUID_GATES_APPLY` used as place send, or if Dig_3R R is mixed in.

---

## 6. Gate to APPLY (Chair only)

PASS on Challenge_file_exit XAUUSD **and** owner/Chair NAME → then:

1. Write `judgment/live/prove/FLUID-PLC-PLACE.json` with `wire_class=W_named`, `proven=true`, `lens=Challenge_file_exit`, metrics above.
2. Scoped env: `GTOS_JEV_PLACE_FLUID_APPLY=1` + `GTOS_JEV_PLACE_FLUID_SCOPED_SYMBOLS=XAUUSD`.
3. Writer consume land (separate Chair). Fail-closed DELAY if Jev dark.
4. Do **not** flip `GTOS_JEV_SLEEVE_SELECT_APPLY`.
5. Do **not** treat `GTOS_JEV_FLUID_GATES_APPLY=1` as place.
6. GBPJPY second, after pack rows exist.

FAIL → remain SHADOW. Do not lower bars. Do not invent fills for FP.

---

## 7. Known S15 / Wave facts to beat (not to overwrite)

- Writer false-admits: n=29, tape R=−28.92. Place Choice should STAND/DELAY a **named subset** of these without killing FIRE 1201 KEEP wins.
- Cost-avoided-by-reject: n=23, R=−24.66. PLC-003 cannot become a new skip; size haircut stays F5-JEV-004.
- Ticket 293332188 leave-orig closed; live tilts 1.0; no remint.
- `n_xau_sufficient=28`, `n_cost_complete=47`, `n_news_empty=0` on pack n=97.

---

## 8. Blockers (honest)

| blocker | impact |
|---|---|
| VPS Admin unreachable | cannot re-rg live flags; box mirror used |
| GBPJPY pack n=0 | no scoped GBPJPY place prove this tape |
| Host news READ=0 | event questions abstain; PLC-002 weak |
| PLC-004 constant-then-inherited | occupancy label needs deals join; missing tape → None |
| PLC-007 missing last_refusal | need slate refusals named |
| `evaluate()` budget default 200 | hist must raise `GTOS_JEV_MAX_CALLS` |
| veto.py substring `place` | must land judgment fix **before** hist injects PLACE |
| Module_ATR is geometry_proxy | cannot PASS place APPLY alone |

---

## 9. Sibling session

`14_place_fluid_hist_prove_apply` owns the APPLY-wire land recipe after this family's map. Do not claim that session's APPLY. This plan is the shared hist bar.
