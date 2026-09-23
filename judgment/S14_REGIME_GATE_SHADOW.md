# S14 REGIME_GATE_SHADOW — judgment stub

**Account:** Challenge `0` / `$110k` / magic `0` / ns `operator`  
**Compose with:** PR #29 `ALIVE_MENU` + `CONF_GATE` + `DONE_OUTSIDE` (same admit sidecar)  
**Flags (default unset):** `GTOS_JEV_FLUID_GATES_SHADOW` · `GTOS_JEV_FLUID_GATES_APPLY`  
**Never:** place / `order_send` / remint / flatten / invent `NEWS_PROTOCOL`

## What it does

1. Emit bucket enums only from `gold_state.v0` + optional `harvest.*` (`omit_if_missing`).
2. One System One pack: `regime_type` (Choice, fixed 5) + `regime_change_likely` (Noul) + `strategy_viable` (Noul). No live TypeSafe client in this stub — inject or cache.
3. Code compose → `stand_down | half_size | admit_ok_label` + `size_factor` ∈ `{0, 0.5, 1.0}` **logged**.
4. Cache key `sha256(canonical_bucket_state_json)` for Challenge tape replay.
5. DONE_OUTSIDE verifies the same `jev_fluid_gate_v1` admit artifact.

`admit_ok_label` / Matchstick `trade` **never** maps to `order_send`. APPLY of `size_tilt` is refused (`s15_shadow_only_no_size_tilt_apply`) until Chair NAME after the S15 calibration sheet. S15 logs tape costs + CONF_GATE SHADOW bands on this same sidecar — see [`S15_COST_OF_ERROR.md`](S15_COST_OF_ERROR.md).

## Chair G1–G8 (do not weaken)

| Surface | S14 behavior |
|---|---|
| INDEX / `idxrev` / US30 | hard-off → `stand_down` |
| `xa_huge*` / `orb_crypto*` / `orb_*` / `bleed*` / `mx_us30` | hard-off → `stand_down` |
| KEEP `spring` / `vss` (G7 `ALLOW_NO_BOOST`) | size_factor never > 1.0 |
| G6 session 0.75 | Chair ceiling on cut sessions (KEEP exempt; `Asia_London_pre` / `Off_hours` left alone). Emitted `size_factor` stays in `{0, 0.5, 1.0}` — 0.75 snaps **down** to `half_size` 0.5 (never emit 0.75, never round up) |
| G8 `BLOCK_REENTRY_SAME_SLEEVE` | `already_placed_today` / same-sleeve <15m → `stand_down` unless new named fire |
| G5 `CONFIRM_SHADOW` | stay shadow; `broker_effect=false` |

## Historical prove (no live bars)

```bash
python3 scripts/run_s14_historical_prove.py --force \
  --log-dir /tmp/s14-prove \
  --score-out /tmp/s14-prove/scorecard.json \
  --write-tape judgment/astra/lab/s14_historical_tape/TAPE_0.jsonl
```

Bars: `n_decidable ≥ 20`, `n_moved ≥ 5`, `n_distinct_gate ≥ 2`, `n_invented_high == 0`, `n_order_send == 0`.  
`--force` writes shadow logs without exporting `GTOS_JEV_FLUID_GATES_SHADOW`. Unset flags still write nothing.

Tape identities come from Challenge `0` (including replay tickets such as `291072108` / `291076386`). Features are already-bucketable harvest fields, not raw OHLCV. System One answers are injected/cached — no live Jev call, no host-mesh.

Negative tape ⇒ adjust research thresholds / `judgment/astra/s14_favored_regimes.json` / bucket maps and re-run the **same** tape. Idle is forbidden.

## Tests

```bash
python3 -m pytest -q tests/judgment
```
