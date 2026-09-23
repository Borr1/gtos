# S16 MULTI_STAGE_GUARD — Dig/Chair MCP screens (judgment stub)

**Compose with:** PR #29 `DONE_OUTSIDE` + `CONF_GATE` law only (confidence ≠ permission).  
**Not** the Challenge admit sidecar (S14 / S15 / `jev_fluid_gate_v1`).  
**Flags (default unset):** `GTOS_DIG_MULTI_STAGE_GUARD_SHADOW` · `GTOS_DIG_MULTI_STAGE_GUARD_APPLY`  
**Never:** place / `order_send` / remint / flatten / invent `NEWS_PROTOCOL` / host-mesh

## What it does

Five CODE-owned screens around Dig/Chair tool calls:

| Stage | API | CODE maps to |
|---|---|---|
| 1 input | `screenInput` | `allow \| review \| block` (+ `support` escalate) |
| 2 tool-pre | `assessAction` | heuristics first; Jev block stands; write/send failMode `closed\|review` |
| 3 observation | `screenObservation` | injection → data-only; never invent NEWS |
| 4 response | `screenOutput` | hold send on block |
| 5 claim-verify | `verifyClaim` | DONE_OUTSIDE twin |

Wire order: inventory deny → S11 hard DENY → local heuristics → Jev `assessAction` → CODE disposition → ASK Chair. On a "done" claim, code verifies the artifact; Jev `DONE` is advisory only (`NOT_DONE_JEV_ADVISORY_ONLY` when the artifact is missing).

## Laws

- Place ∞ VETO. Off Challenge place scoreboard.
- Confidence ≠ permission. HIGH claim conf never grants write/send/place.
- Heuristics never override a Jev `block` / `deny`.
- Write/send failMode is never `open`.
- Observation path never invents `NEWS_PROTOCOL`.
- APPLY (owner NAME later) still never maps to place.
- Dig E KILL (S20): Challenge place path dual-flag is hard-off.
  `maybe_write_shadow_row` is observe-only and must not raise / block place.
  `book_owner` never imports this module.

## Prove (offline)

```bash
python3 scripts/run_s16_prove.py --offline --jev-fixture-mode --shadow \
  --no-place --no-host-mesh --no-network \
  --fixtures judgment/astra/lab/s16_prove_fixtures \
  --log-dir /tmp/s16-prove --score-out /tmp/s16-prove/scorecard.json
```

```bash
python3 -m pytest -q tests/judgment/test_s16_multi_stage_guard.py
```

Bars: decidable ≥ 20, moved ≥ 5, dig_broker_tools = 0, failMode_open_on_write = 0,
heuristics_clears_jev_block = 0, confidence_as_permission = 0, invented_high_forbidden,
place_path_untouched, shadow rows `broker_effect=false` `never_place=true`.

Dig pack authority:

- `research/codila_absorb/war_room/s16_multi_stage_guard/SHADOW_WIRE_SPEC.md`
- `research/codila_absorb/war_room/s16_multi_stage_guard/guard_map.json`
- `research/codila_absorb/war_room/s16_multi_stage_guard/compose_pseudocode.md`
- `research/codila_absorb/war_room/s16_multi_stage_guard/PROVE_PLAN.md`
- `research/codila_absorb/war_room/s16_multi_stage_guard/PROVE_FIXTURES.md`
- `research/codila_absorb/war_room/s16_multi_stage_guard/PR29_S16_COMPOSE.md`
- `research/codila_absorb/war_room/s16_multi_stage_guard/prove_fixtures/`

Local copies: [`astra/s16_guard_map.json`](astra/s16_guard_map.json), [`astra/lab/s16_prove_fixtures/`](astra/lab/s16_prove_fixtures/).

Unset flags write nothing. `--shadow` / `--force` on the prove script is still shadow-only.
