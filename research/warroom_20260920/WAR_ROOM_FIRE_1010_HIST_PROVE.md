# WAR ROOM FIRE 1010 — Historical Prove (S14 / S15 / S16)

**Owner:** Chair war-room hist-prove executor  
**When:** 2026-09-20 10:11 ICT (UTC+7)  
**Seat:** Chair box extract (no VPS machineId / no host-mesh)

## Laws observed

- Never host-mesh
- Never set `GTOS_JEV_FLUID_GATES_APPLY` or `GTOS_DIG_MULTI_STAGE_GUARD_APPLY` (confirmed unset after runs)
- Never place / `order_send` (`n_order_send == 0` all three)
- No NEWS invent (`n_invented_high == 0`; S16 fixture `08_empty_news_no_invent` passed)
- Worked on Chair extract only: `/workspace/gtos/research/warroom_20260920/s14_s15_s16_stack/extract/`

## Environment

| Item | Value |
|------|-------|
| CWD / PYTHONPATH | extract root |
| Python | 3.13.5 system (`/usr/bin/python3`) |
| Venv | **not needed** — judgment imports resolved from extract `src/` with stdlib only |
| APPLY flags | unset before/after |
| VPS machineId `7cfa9657-805b-4e9c-9fbb-886c500f997b` | **unavailable this seat** (no CopyFromBox / local-exec) |

## Commands run

```bash
cd /workspace/gtos/research/warroom_20260920/s14_s15_s16_stack/extract
unset GTOS_JEV_FLUID_GATES_APPLY GTOS_DIG_MULTI_STAGE_GUARD_APPLY
export PYTHONPATH="$PWD"

python3 scripts/run_s14_historical_prove.py --force \
  --log-dir /workspace/gtos/research/warroom_20260920/hist_prove_1008 \
  --score-out /workspace/gtos/research/warroom_20260920/hist_prove_1008/s14_scorecard.json

python3 scripts/run_s15_historical_prove.py --force \
  --log-dir /workspace/gtos/research/warroom_20260920/hist_prove_1008 \
  --score-out /workspace/gtos/research/warroom_20260920/hist_prove_1008/s15_scorecard.json

python3 scripts/run_s16_prove.py --offline --jev-fixture-mode --shadow \
  --no-place --no-host-mesh --no-network \
  --fixtures judgment/astra/lab/s16_prove_fixtures \
  --log-dir /workspace/gtos/research/warroom_20260920/hist_prove_1008/s16 \
  --score-out /workspace/gtos/research/warroom_20260920/hist_prove_1008/s16_scorecard.json
```

## Results (pass/fail)

| Lane | Exit | pass | n_decidable | n_moved | n_order_send | broker_effect_all_false | n_invented_high | Notes |
|------|------|------|-------------|---------|--------------|-------------------------|-----------------|-------|
| **S14** | 0 | **PASS** | 28 (≥20) | 17 (≥5) | **0** | true | 0 | gates: admit_ok_label=11, half_size=6, stand_down=11; n_distinct_gate=3 |
| **S15** | 0 | **PASS** | 38 (≥20) | 31 (≥5) | **0** | true | 0 | pick_counts NO=38 VETO=1; place_infinity_veto=true; false_abstain=0 |
| **S16** | 0 | **PASS** | 31 (≥20) | 24 (≥5) | **0** | true | 0 | allow=7 blocked=15 review=8 support=1; failed=0; never_place_all=true |

**Overall:** **ALL PASS** — decidable/moved bars met; `order_send=0` on every lane.

## Artifact paths (Chair box)

| Artifact | Path |
|----------|------|
| S14 scorecard | `/workspace/gtos/research/warroom_20260920/hist_prove_1008/s14_scorecard.json` |
| S15 scorecard | `/workspace/gtos/research/warroom_20260920/hist_prove_1008/s15_scorecard.json` |
| S16 scorecard | `/workspace/gtos/research/warroom_20260920/hist_prove_1008/s16_scorecard.json` |
| S14/S15 shadow logs | `/workspace/gtos/research/warroom_20260920/hist_prove_1008/admit/2026-09-20/` |
| S16 shadow logs | `/workspace/gtos/research/warroom_20260920/hist_prove_1008/s16/2026-09-20/` |
| This report | `/workspace/gtos/research/warroom_20260920/WAR_ROOM_FIRE_1010_HIST_PROVE.md` |

## VPS copy status

**NOT DONE this seat.** `CopyFromBox` / Shell `machineId 7cfa9657-805b-4e9c-9fbb-886c500f997b` unavailable to this executor (Linux Chair box only; standing note matches `PR29_VPS_SHADOW_LAND.md` / `hydrate_fx_receipt.md`).

**Chair must copy** scorecards + this report to VPS:

```
research\warroom_20260920\
  s14_scorecard.json
  s15_scorecard.json
  s16_scorecard.json
  WAR_ROOM_FIRE_1010_HIST_PROVE.md
```

Suggested source dir on Chair: `hist_prove_1008\` + report at warroom root.

## Blockers

1. **VPS land:** machineId/CopyFromBox not available — Chair one-shot copy required.
2. **Deps:** none — no venv created; extract imports clean.
3. **APPLY:** intentionally never flipped.

## Schema stamps

- S14: `gtos.s14.prove_scorecard.v1`
- S15: `gtos.s15.prove_scorecard.v1`
- S16: `gtos.chair.s16.prove_scorecard.v1`
