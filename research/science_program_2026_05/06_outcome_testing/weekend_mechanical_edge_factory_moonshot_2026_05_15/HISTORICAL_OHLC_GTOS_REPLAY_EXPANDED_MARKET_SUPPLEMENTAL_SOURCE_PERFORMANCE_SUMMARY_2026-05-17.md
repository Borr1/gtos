# Expanded-Market Supplemental Source Performance

Generated: 2026-05-18T00:12:30Z

## Inputs

- CP216 seed-floor performance rows: `45220`
- Sierra source-bound M15 source rows: `30`

## Outputs

- Combined performance rows: `46120`
- Additional source performance rows: `900`
- Aggregate rows: `6885`
- Missing simulated-field rows: `0`
- Rows with simulated R: `46120`

## Decisions

- CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET: 10175
- IMPLEMENT_EXPANDED_MARKET_PROXY_R_SCORER: 6401
- KILL_EXPANDED_MARKET_BRANCH: 3754
- REDESIGN_EXPANDED_MARKET_CONCENTRATION: 1920
- REDESIGN_EXPANDED_MARKET_SIGNAL_GEOMETRY: 23626
- REDESIGN_EXPANDED_MARKET_UNDERPOWERED: 244

## Boundary

Branch-local research artifact only. The run wrote no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path.

## Result

- ok: `True`
- issues: `[]`
