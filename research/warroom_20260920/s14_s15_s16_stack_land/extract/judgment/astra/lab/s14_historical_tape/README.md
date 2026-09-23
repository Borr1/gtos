# S14 Challenge tape 0

Historical-first prove input. **No live bars.** No host-mesh.

Generate / refresh:

```bash
python3 scripts/run_s14_historical_prove.py --force \
  --write-tape judgment/astra/lab/s14_historical_tape/TAPE_0.jsonl \
  --log-dir /tmp/s14-prove \
  --score-out /tmp/s14-prove/scorecard.json
```

Rows are `gold_state.v0` + injected System One answers. Features are bucket sources (returns, vol_ratio, slope) — never raw OHLCV, ticks, or expost `broker_net` / `R`.
