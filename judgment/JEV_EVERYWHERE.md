# Jev everywhere — Challenge 0 sidecar fan-out

**Owner NAME:** JEV EVERYWHERE POSSIBLE on Challenge GTOS (login **0**).  
**Compose with:** PR29 / S14 / S15 on `jev_fluid_gate_v1` — **not** a parallel place path.  
**Flags (default unset):** `GTOS_JEV_EVERYWHERE_SHADOW` *or* `GTOS_JEV_FLUID_GATES_SHADOW`  
**Dig E 2026-09-21:** `EVERYWHERE_SHADOW` is an **alias** of `FLUID_GATES_SHADOW` — **APPLY_CANDIDATE ALREADY_LIVE**, **not** an open `IN_PROVE` dual-flag pair.  
**Never:** place / `order_send` / remint / flatten / invent `NEWS_PROTOCOL` / new hard-off cages

## What it does

Inventory every decision site under `src/judgment` + the fluid-gate sidecar. Sit System One **Choice / Score / Noul** on every **safe** site. Emit one structured shadow row per site on the **same** admit sidecar.

Unsafe sites stay vetoed (place, remint, flatten, order_send, NEWS_PROTOCOL invent). S16 Dig/Chair stays on its own flags (observe-only here).

Writer house locks (`bleed`, `orb_crypto`, `idxrev`, `xa_huge`, `mx_us30`) are **not** deleted. No new hard-off family is added. Panic hard-offs are not research-path religion.

**Chair CF D is the primary soft policy (2026-09-20, Challenge 60, +11.17R):**

`stand_down` when `miss=false_structure` and not KEEP; KEEP exempt (house spring/vss **or** family `sub_mid`; expand is allow, not KEEP). Ablation order: **miss › size › family › session › conf**. Shadow compose on this sidecar — not asset-zero religion.

Still sitting, now behind CF D:

1. `sleeve_family` — allow spring / vss / sub / expand (CF **+8.70R**)
2. `size_x_conf` — size × conf_shadow compose
3. `cost_band` / `conf_gate` SHADOW labels (`COST_*`, `CONF_GATE_*` including ALLOW/KEEP)

Question bank: [`astra/lab/jev_cf_d_bank/QUESTION_BANK_0.json`](astra/lab/jev_cf_d_bank/QUESTION_BANK_0.json) (n=10).

`LEGACY_religion_index_crypto_xa_0` is **revoked**. Do not encode INDEX / CRYPTO / xa size0 as religion. `regime_unknown` stays honest until assembled regime features exist — do not invent.

## Surface (pre → post)

| site | pre | Jev sits |
|---|---|---|
| alive_menu / conf_gate / s14 / s15 / done_outside | wired | yes (wrap + questions) |
| fanout_book | IDs only | yes — typed pack |
| admit | schema only | Choice + Noul + Score |
| close_label | schema only | Choice + Noul + Score |
| corr_hold | schema only | Noul + Score + Choice (no flatten) |
| usage_router | gap | Choice |
| size_tilt | gap | Score **label** (APPLY still veto) |
| event_stamp | gap | Noul; empty spine abstains |
| score_then_choice / queue_handoff / state_shape | gap | Noul / Choice / Noul |
| **sleeve_family** (CF #1) | gap | code — spring/vss/sub/expand allow |
| **size_x_conf** (CF #2) | gap | code compose; never size0 religion |
| **cost_band** + conf_gate SHADOW (CF #3) | gap | `COST_*` / `CONF_GATE_*` labels |
| **cf_d** (primary soft policy) | gap | Choice + Score + Noul — FS stand_down, KEEP exempt |

Map artifact: [`astra/jev_everywhere_sites.json`](astra/jev_everywhere_sites.json).

## Prove (historical closes — no live bars)

```bash
python3 scripts/run_jev_everywhere_historical_prove.py --force \
  --log-dir /tmp/jev-everywhere \
  --write-tape judgment/astra/lab/jev_everywhere_closes/TAPE_0.jsonl \
  --write-map judgment/astra/jev_everywhere_sites.json \
  --score-out /tmp/jev-everywhere/scorecard.json
```

```bash
python3 -m pytest -q tests/judgment/test_jev_everywhere.py tests/judgment/test_fluid_gates.py
```

Bars: decidable ≥ 20, moved ≥ 5, sites ≥ 10, invented_high == 0, order_send == 0,
flatten in action_scope == 0, hard-off families untouched, broker_effect all false,
place ∞ VETO.

Unset flags write nothing. `--force` is still shadow-only.
