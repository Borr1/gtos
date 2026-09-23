# TWO_STOP_PATH

Live 2-stop **COUNT** is an envelope integer. Jev may LABEL a would-be third fire. Jev is not the counter.

- Cap: `F5_SAME_SLEEVE_ORIG_STOP_DAY_CAP = 2`
- Source: `doc["closed"]` only
- Path: `pipeline_state/ultimate_book/{ns}/judgment/state/just_closed_siblings.json`
- Top-level symbol keys (`XAUUSD`, `US30.cash`, …) frozen at 09-08 are **legacy leftovers**. Ignored.
- `updated_ict` is stale leftover.
- Abandoned twin `judgment/live/just_closed_siblings.json` is never loaded.
- `closed[]` is pruned ~24h — older same-day stops that aged out under-count.

Code: `src/judgment/two_stop.py`.
