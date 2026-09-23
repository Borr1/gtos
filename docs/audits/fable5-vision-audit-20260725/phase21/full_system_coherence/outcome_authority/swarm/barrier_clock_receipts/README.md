# barrier_clock_receipts

Receipts for `../BARRIER_CLOCK_DEFECT_V1.md`. Every script is **read-only** — it opens sealed
pools, committed artifacts and the `src/` tree, and writes exactly one JSON next to itself.
Nothing here touches a live path, a config, a broker or the VPS.

| script | writes | answers |
|---|---|---|
| `bcd_sleeve_immunity.py` | `BCD_SLEEVE_IMMUNITY.json` | Does the defect reach the armed live book or the sleeve estate? Scans the live order-request construction, the sleeve entry convention and walk-start indices, and the `AA_ESTATE_TRADES` schema. |
| `bcd_wave21_census.py` | `BCD_WAVE21_CENSUS.json` | The 550,966 / 632,934 reach, the LIMIT/MARKET family split tested against `distance_to_limit_risk`, and the Lane G reconciliation via `lifecycle_label_status`. |
| `bcd_sealed_label.py` | `BCD_SEALED_LABEL.json` | Is the sealed January pool label fill-aware or decision-anchored? Compares `opportunity_net_proxy_r + cost_r` against both arms. |
| `bcd_jan_decomposition.py` | `BCD_DECOMP_JAN.json` | The three-arm decomposition (A decision-anchored / B causal-market / C fill-anchored) with day-block intervals, per family and per measured order type. **This is the detection test.** |
| `bcd_training_corpus.py` | `BCD_TRAINING_CORPUS.json` | What share of the frozen ridge's training target carries the defect. |

## Inputs that live outside this repository

`bcd_sleeve_immunity.py`, `bcd_sealed_label.py` and `bcd_jan_decomposition.py` read sealed pools
from the wave-21 worktree
`/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725`:

* `docs/.../phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz`
* `docs/.../phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz`
* `docs/.../phase6/receipts/AA_ESTATE_TRADES.json.gz`

`bcd_wave21_census.py` reads `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` —
the rows Lane G's `extract.py` turned into `pool_table.npz`. That cache is machine-local and
regenerable from the sealed compact-event roots; the census will refuse rather than guess if it is
absent.

`bcd_sleeve_immunity.py` and `bcd_training_corpus.py` resolve everything else relative to this
worktree, so they reproduce anywhere `origin/main` is checked out with `src/` present.

## Reproduce

```bash
cd <worktree-at-origin-main>/docs/audits/fable5-vision-audit-20260725/phase21/\
full_system_coherence/outcome_authority/swarm/barrier_clock_receipts
python3 bcd_sleeve_immunity.py
python3 bcd_wave21_census.py
python3 bcd_sealed_label.py
python3 bcd_jan_decomposition.py
python3 bcd_training_corpus.py
```

## The control that must stay at zero

`bcd_jan_decomposition.py` reports `MARKETABLE_limit_measured` — limits priced through the market,
which have no decision→fill gap by construction. Its A−C inflation is **+0.0031 R/trade
[−0.0023, +0.0078]** on 13,572 rows. If a future run moves that number, the harness is wrong, not
the estate.
