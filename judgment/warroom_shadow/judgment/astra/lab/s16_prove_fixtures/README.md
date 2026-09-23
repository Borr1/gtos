# S16 prove fixtures (local copy)

Authoritative Dig pack: `research/codila_absorb/war_room/s16_multi_stage_guard/prove_fixtures/`
plus `PROVE_FIXTURES.md` / `PROVE_PLAN.md`.

These eight JSON files are the offline Chair stub pack. They wrap Dig/Chair
tools only. Place is an infinity VETO. No host-mesh, no network, no broker.

```bash
python3 scripts/run_s16_prove.py --offline --jev-fixture-mode --shadow \
  --no-place --no-host-mesh --no-network \
  --fixtures judgment/astra/lab/s16_prove_fixtures \
  --score-out /tmp/s16-prove/scorecard.json
```
