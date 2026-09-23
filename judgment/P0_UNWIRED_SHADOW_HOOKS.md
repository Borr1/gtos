# P0 unwired SHADOW hooks (FIRE 1404)

Challenge **0** only. Verification 0 quarantined.

Same `jev_fluid_gate_v1` admit sidecar as PR29 / S14 / S15 / S16 / Jev-everywhere.
**Not** a parallel place path. `apply=false` always on this pack.

## Fields stamped on `warroom_shadow`

| Field | Role | Values |
|---|---|---|
| `conf_gate_band_disposition` | sidecar | `STRICT` / `SESSION` / `EVENT` / `REVIEW` / `KEEP` |
| `P0_KEEP_REVIEW_WIN_VS_FAMILY_LOSER` | Choice | `REVIEW_KEEP` / `FAMILY_LOSER` / `UNSURE` |
| `P0_CFD_MISS_FALSE_STRUCTURE` | Choice | `STAND_DOWN` / `KEEP_EXEMPT` / `NOT_FS` |
| `P0_CFD_SIZE_INTENT` | Choice | `STAND_DOWN` / `HALF` / `TRIM` / `FULL` / `KEEP_CAP` |
| `P0_CFD_SLEEVE_FAMILY_KEEP_SIG` | Noul | `0.0`–`1.0` from STATE keep signature |

FIRE 1201 floors (`judgment/astra/conf_gate_band_weights_shadow.json`) are
SHADOW labels only. Historical labels still lack numeric confidence —
**do not flip APPLY**.

## Laws

- Jev never places / remints / flattens / `order_send`.
- Do not invent `NEWS_PROTOCOL`.
- Cost is disclosure, never a kill-gate (PR35).
- KEEP signature from **STATE**, not a sleeve-name allowlist.
- Affinity is instrument × sleeve on the row. No global rule.
- Expanding harden / V3 stays PARKED (no third feature).
- Read `GTOS_JEV_FLUID_GATES_SHADOW` (or `--force`). Never set
  `GTOS_JEV_FLUID_GATES_APPLY` or `GTOS_DIG_MULTI_STAGE_GUARD_APPLY`.

## Prove (historical — no live bars)

Chair enable is `GTOS_JEV_FLUID_GATES_SHADOW=1` only. Never flip APPLY.

```bash
GTOS_JEV_FLUID_GATES_SHADOW=1 python3 scripts/run_p0_shadow_hooks_historical_prove.py \
  --log-dir /tmp/p0-shadow \
  --score-out /tmp/p0-shadow/scorecard.json \
  --receipt-out /tmp/p0-shadow/fire1201.json
```

`--force` is the CI dry-run analog. The prove refuses if
`GTOS_JEV_FLUID_GATES_APPLY` or `GTOS_DIG_MULTI_STAGE_GUARD_APPLY` is set.

Bars: every row `apply=false`, `broker_effect=false`, `order_send=0`,
`invented_high=0`, KEEP noul does not fire from sleeve name alone,
FIRE 1201 KEEP wins preserved (3/3 `KEEP`), residuals PARKED
(`291087142` / `293128383` `REVIEW` + `KEEP_EXEMPT`), research
candidate **EMPTY**.

See [`CHAIR_P0_SHADOW_ENABLE_HIST_PROVE.md`](CHAIR_P0_SHADOW_ENABLE_HIST_PROVE.md).
