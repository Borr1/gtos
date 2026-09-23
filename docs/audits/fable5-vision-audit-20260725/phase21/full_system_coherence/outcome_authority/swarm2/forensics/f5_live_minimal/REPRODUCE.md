# Reproducing the F5 numbers

The four analysis scripts read from a working directory `T` that must first be populated from
in-repo artifacts. Nothing is fetched and no broker is contacted.

```bash
cd /Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725
T=/tmp/f5 && mkdir -p "$T/f5"

git show HEAD:docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz            > "$T/AA_ESTATE.json.gz"
git show HEAD:docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_INERT_PROFILE_SYMBOL_SNAPSHOT.json > "$T/P1_SPECS.json"
git show HEAD:research/operations/vps_broker_truth_2026_07_26/BROKER_SYMBOL_SPEC_COMPARISON.json           > "$T/BROKER_SPEC.json"
git show HEAD:research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json                > "$T/COSTS_V11.json"

# then set T at the top of each script (they hardcode the scratch path used at authoring time)
sed -i '' "s#/Users/borr/.claude/jobs/adb9e69b/tmp/#$T/#g" *.py
python3 estate_stats.py      # trade rate, gross R, per-symbol stop distribution
python3 floor_table.py       # the min-lot floor table + placeability  -> F5_MIN_LOT_FLOOR_V1.json
python3 net_expectancy.py    # four-component cost-true expectancy, both brokers
python3 mc_trajectory.py     # effective $/trade with round-up + the Monte Carlo grid
```

Seed is `20260812` throughout; the Monte Carlo is a block bootstrap (block = 5 trading days) over
the throttled population, which is also shipped directly as
`receipts/F5_THROTTLED_POPULATION_V1.json.gz` (9,083 rows: `sleeve, sym, sl, day, netF, netN`) so
the trajectory work can be redone without re-deriving the estate.

`f5_status.py.draft` and `minimal_size.py.draft` are **drafts, not applied** — they carry a
`.draft` suffix precisely so nothing imports them by accident. Their destinations are
`scripts/f5_status.py` and `src/components/ultimate_book/minimal_size.py`; see `PATCHES_V1.md`.
