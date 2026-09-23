# HIST-PROVE PLAN — admission governor Score / DERISK / BLOCK

**session:** `17_residual_static_admission_governor`  
**as_of_ict:** `2026-09-21T06:03:46+07:00`  
**account:** FTMO Challenge login `0` · ns `operator` · magic `0`  
**APPLY:** forbidden until this plan produces a PASS receipt and Chair ENFORCE.  
**place:** `false` on every replay. Writer is not invoked.

---

## 1. Module_ATR honesty (non-negotiable)

Three R universes exist for XAU `dsp_three_fresh_lower_lows`. **They must never be merged.**

| lens | path | use in this prove |
|---|---|---|
| **Challenge broker R** | deal tape / `challenge_replay_rows.jsonl` `R` / `broker_net` | **PRIMARY** metric for governor counterfactuals |
| **Dig_3R** | Dig blotter (3R geometry) | not a governor input; do not mix |
| **Edge_ATR** | Edge ATR-R | not a governor input; do not mix |
| **Module_ATR** | `/workspace/gtos/close_loop/war_room_20260920/blotter_Module_ATR_XAUUSD_dsp_three_fresh_lower_lows.jsonl` | **LABEL / third lens only**. Geometry proxy `stop0.75/tgt6.0` ATR. `R_Module_ATR` must not feed Dig or Edge. Must not be written into `admission_complete_state.atr`. |

**Do not invent ATR or regime.**

- Live `TradeIntent.atr_ratio` / `vr` are decision-bar facts (`index<=i`) from the metals/substrate generators.
- `gold_state.geometry.atr14` comes from Challenge M15 via `primitives.atr14` — named bars, not Module_ATR blotter.
- If `vr` / `atr_ratio` / `atr14` absent: `atr_basis=missing`, vol-level and A8 questions **ABSTAIN**. Fail-open-to-1.0 for vol tilt (already coded).
- `regime_tag` / `conf_band` stay `PENDING` unless a named assembler filled them (session 07/10). Do not cook a regime from Module_ATR yearfold.
- News: `news_join=STATE_MISSING` if spine empty. Do not invent NEWS_PROTOCOL.

If a replay row only has Module_ATR R and no Challenge broker R: **exclude from PRIMARY scoreboard**; may sit on a side table tagged `lens=Module_ATR`.

---

## 2. Challenge tape paths (present on box)

### Bars (Challenge-true; April `data/historical` is **not** a member)

Search order is `judgment/bars.py::challenge_search_dirs()`:

| path | present? |
|---|---|
| `_pr41_land/.../judgment/astra/lab/challenge_shadow_20260917/` | YES (`XAUUSD_M15.csv`) |
| `_pr41_land/.../judgment/astra/lab/challenge_shadow_20260917/multi/XAUUSD_M15.csv` | YES (157153 B) |
| `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_M15.csv` | YES (135118 B) |
| `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/multi/` | search dir listed |
| `pipeline_state/ultimate_book/operator/judgment/state/_fable_bar_pull_20260917/multi` | may be MISSING this seat — honest |
| env `GTOS_CHALLENGE_BAR_MULTI` | unset here |

Refuse April / broker-naive CSVs without `time_utc` (`admit_challenge_peer_csv`).

### Deal / replay tape

| path | what |
|---|---|
| `/workspace/gtos/research/jev/lab/challenge_replay_rows.jsonl` | 45 tickets, queried 2026-09-17. Wins 6 / losses 39. Actual PnL **−4295.92 USD**. |
| `/workspace/gtos/research/jev/lab/CHALLENGE_JEV_REPLAY_20260917.md` | admit_then / admit_now confusion vs profit. **This is sleeve-fire `admit` Choice, not governor Score.** Do not treat as governor prove. |
| `/workspace/gtos/research/jev/lab/mt5_challenge_positions_0.json` | snapshot |
| Live slates under `/workspace/gtos/live/` and `fable_joint_pull_20260917/` | `governor.reason=derisking_into_maxdd_wall`, `cap_mult≈0.42–0.71` — **observed live STATIC derisk**, the primary Score population |
| `/workspace/gtos/judgment/live/jev_sidecar/admit/2026-09-20/` | sidecar admit receipts (wrong question family for this prove) |

### Replay engine (no broker)

- `src/research_infra/replay_policy/sleeve_book.py` → same `evaluate_vnext_ultimate_book_admission`
- `src/research_infra/walkforward/book_replay.py`
- Draft SHADOW hook: `drafts/admission_jev.py` (APPLY hard-off)

VPS live tree `redacted_host` UNREACHABLE this seat. Host deal history beyond the 45-ticket snapshot is **MISSING** here. Chair CopyFromBox when online. Do not invent fills.

---

## 3. Counterfactual design

For each Challenge decision-day / bar where `admit_and_size` ran (or reconstructed from slates + intents):

1. **STATIC baseline** — current `evaluate_governor` + size path (APPLY=0). Record:
   - `reason`, `allow_new`, `size_cap_multiplier`
   - units kept, `sum unit_risk_pct`
   - would-fire? (allow_new ∧ sized units > 0)
2. **Jev SHADOW** — POST `admission_governor_questions` ∪ `symbol_fanout_questions` over `admission_complete_state`. Log only.
3. **Jev COUNTERFACTUAL (offline)** — apply Score **shrink-only** to `size_cap_multiplier`; apply soft-stop Choice only in a **named ablation** (default off).

Never send orders. Never mutate live `pipeline_state/ultimate_book/*/high_water.json`.

### Ablations (run separately; do not mix)

| id | what | default |
|---|---|---|
| A0 | SHADOW log only (byte-identical fire) | **required first** |
| A1 | Score shrink on `derisking_into_maxdd_wall` only | primary APPLY candidate |
| A2 | Score shrink on profit-target / stress ladder / coloss / kelly / vol | after A1 PASS |
| A3 | Soft-stop Choice BLOCK_KEEP vs DERISK_TRIM | **off** until A1 PASS + daily-breach 0 |
| A4 | Shed Score vs FFD | off (cap never bound in W7 fortnight) |
| A5 | A8 Choice ADMIT_TRIM vs DROP | off; live DROP stays until hist |
| A6 | Overlay Scores | off; live overlays=false |

A3 that **increases fire rate** on days with `realized_today_pct <= -0.03` must show **zero** extra daily-breach vs −5% and non-worse maxDD.

---

## 4. Metrics (must report)

Per ablation vs STATIC:

| metric | definition |
|---|---|
| `n` | decision rows with named governor state |
| `n_derisk` | rows with reason `derisking_into_maxdd_wall` |
| `n_soft_stop` | rows with `soft_daily_stop_reached` |
| `n_block` | `allow_new=false` |
| `fire_rate` | fraction would-fire |
| `sumR` | **Challenge broker R** (PRIMARY). Separate `sumR_Module_ATR` if a side table exists — never add them. |
| `sum_usd` | broker_net |
| `maxDD` | peak-to-trough on the **static initial-balance** basis (90k wall), not trailing high-water |
| `worst_day_pct` | min realized_today_pct |
| `n_daily_breach` | days with realized+open ≤ −5% |
| `n_maxdd_breach` | equity ≤ 90k |
| `mean_cap_mult` | among allow_new rows |
| `n_jev_dark` | skipped POSTs |

**PASS gate for A1 (Score shrink on maxDD derisk):**

- `n_daily_breach` ≤ STATIC (prefer 0)
- `n_maxdd_breach` ≤ STATIC (prefer 0)
- `maxDD` no worse than STATIC by more than 0.2 pp (noise band — declare if tape n is small)
- `sumR` ≥ STATIC **or** fire_rate ↓ with sumR per fire ≥ STATIC (do not buy fewer fires that are worse)
- `n_jev_dark / n` < 0.05 on the prove window (else FAIL — starved/dark)
- Module_ATR side table not used in the PASS inequality
- No PLACE occurred (`never_broker_place: true` in receipt)

**FAIL / no APPLY if:** Score widens cap_mult vs static on any row; soft-stop Choice reopens into joint-room violation; any invented ATR/news.

Small-n honesty: the 45-ticket 2026-09-17 replay is **sleeve-admit** labeled, not a full governor day series. If `n_derisk` on a true Challenge governor reconstruction is **MISSING** (no persisted `GovernorState` jsonl this seat), **do not fake n**. Use live slates as a **presence** sample (`derisking_into_maxdd_wall` is live) and mark `governor_day_series: STATE_MISSING` until Chair lands host `high_water.json` + day anchors + intent logs.

---

## 5. Reconstruction recipe when day series is MISSING

1. Collect slate `governor` blocks (`reason`, `cap_mult`, `open_risk_pct`) from `/workspace/gtos/live/_slate_*.json` and `fable_joint_pull_20260917/`.
2. Pair with Challenge M15 as-of (time_utc).
3. If equity/high_water/day_anchor absent: **cannot** replay `evaluate_governor` leak-free. Stop and report MISSING. Do not backfill equity from Module_ATR.
4. When host `pipeline_state/ultimate_book/operator/{high_water,day_anchor}.json` is copied: rebuild `GovernorState` and run `SleeveBookPolicy` with SHADOW=1.

---

## 6. Affinity

Instrument × sleeve held. A1 Score is **account-level** (same cap_mult on all units that day) — affinity does not split the cap. Shed Score (A4) may prefer XAU / GBPJPY keep **without** flipping `GTOS_JEV_SLEEVE_SELECT_APPLY`. Scoped sleeve-select APPLY remains sessions 03 / Chair receipts.

---

## 7. Gate to APPLY (Chair only)

```
SHADOW A0 byte-identical  →  A1 hist PASS  →  Chair ENFORCE
  GTOS_JEV_ADMISSION_SHADOW=1
  GTOS_JEV_ADMISSION_SIZE_SCORE=1
  GTOS_JEV_ADMISSION_APPLY=1          # Score shrink on derisking_into_maxdd_wall only
  GTOS_JEV_ADMISSION_SOFT_STOP_CHOICE=0
  GTOS_JEV_ADMISSION_FAIL_CLOSED=1
  GTOS_JEV_SLEEVE_SELECT_APPLY remains 0
```

Prove artifact path (when written):  
`judgment/live/prove/UB-GOV-001.json`  
wire_class `A1` or `W_named`, `proven: true`, `stake: admission_governor_size`.

This session writes **the plan**, not UB-GOV-001. Do not claim Chair APPLY landed.

---

## 8. Existing Jev replay that is **not** this prove

`CHALLENGE_JEV_REPLAY_20260917.md` admit_then/admit_now vs profit is the **sleeve-fire** `admit` Choice (hard_refuse on toxic US30 families). Governor Score must not be calibrated on that confusion matrix. Hard-off families stay integer (session 09).
