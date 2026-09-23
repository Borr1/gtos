# V127 Fable B7.3 Non-Hostile 5D Pre-Replay Brief

Generated: 2026-07-06T11:48:17Z

Status: control surface before the next replay. This is not final/live proof.

## 1. Latest Completed Replay

- Latest targeted B7 proof: `BROAD_LIVE_AS_IF_REPLAY_V125_FABLE_B7_1_SIGNED_AUTHORITY_ALIAS_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window: `2026-06-03`
- Result: `14` trades, `-1.82424590R` net, `-0.74330096R` gross/final, `-$1563.10136496` cash PnL, W/L/F `5/9/0`, full/reduced fills `3/11`.
- Transfer: `6603` candidates, `96` scorecard rows, `31` orders, `6589` missed rows, `1101` package axes, `843` candidate-generated axes, `12` scorecard/order axes, `12` filled axes, `219778.99743033803R` source-bound R in-window, `-1.97612654R` axis-attributed executable R.

- Latest broad B7 proof: `BROAD_LIVE_AS_IF_REPLAY_V126_FABLE_B7_2_HOSTILE_5D_SIGNED_AUTHORITY_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`
- Window: `2026-05-13..2026-05-17`
- Result: `55` trades, `-4.43962487R` net, `-0.23004143R` gross/final, `-$3004.85149455` cash PnL, W/L/F `30/25/0`, full/reduced fills `16/39`.
- Transfer: `24510` candidates, `288` scorecard rows, `129` orders, `24446` missed rows, `1101` package axes, `886` candidate-generated axes, `42` scorecard/order axes, `38` filled axes, `492961.6332259947R` source-bound R in-window, `-5.1146153R` axis-attributed executable R.
- Same-window V126 vs V122J: candidates `+935`, scorecard `0`, orders `+1`, trades `+1`, net R `-0.91168634`, gross/final R `-1.03435759`, cash PnL `-$139.94615129`. Added transfers were net negative: `2` added stop-loss losers for `-2.16054439R`, `1` removed loser for `-1.06208299R`.
- V126 verifier: `ok=true`, `issue_count=0`, verified `2026-07-06T11:38:23Z`.

Interpretation: V126 is verifier-green and truth-clean, but behavior-negative. It is a hostile five-day stress result, not a full-system verdict and not proof that the source-bound reservoir failed globally.

## 2. Running Process State

No broad replay, route builder, route verifier, flow analyzer, source-bound parity builder, pytest, py_compile, git add, or Hermes worker is currently running.

Tick hydration precondition:

- A first unchunked availability probe was intentionally terminated after it held an established 127.0.0.1:8001 bridge socket with no output or artifact; `inspect_mt5_tick_availability.py` uses one full-window `copy_ticks_range` call per symbol, which is too coarse for this five-day 24-symbol window.
- The required V127 tick hydration path is the chunked read-only exporter, not the unchunked availability probe.
- Active export command:

```bash
PYTHONUNBUFFERED=1 python3 scripts/export_mt5_research_ticks.py \
  --prefer-silicon-bridge --bridge-host 127.0.0.1 --bridge-port 8001 \
  --source-broker FTMO \
  --source-role owner_authorized_path_override \
  --replaces-missing-frozen-path-source \
  --not-redacted_account-native \
  --source-truth-scope ordered_price_path_only_not_broker_order_lifecycle_truth \
  --require-owner-authorized-path-override \
  --handoff-run-id V127_FABLE_B7_3_NON_HOSTILE_5D \
  --handoff-requirement-id B7_3_JUNE_01_05_ORDERED_TICK_HYDRATION \
  --window v127_b7_3_nonhostile5d:2026-06-01T00:00:00Z,2026-06-06T02:00:00Z \
  --label bridge_ftmo_ticks_v127_b7_3_20260601_20260605_full_plus_expiry \
  --chunk-minutes 15 \
  --yes-live-readonly
```

- Expected manifest: `data/mt5_research_exports/bridge_ftmo_ticks_v127_b7_3_20260601_20260605_full_plus_expiry/manifest.json`.
- V127 broad replay must not start until this manifest is complete or until a source-gap diagnostic run is explicitly labeled as such.

Hydration completed:

- Manifest exists and validates as JSON.
- `created_at_utc=2026-07-06T12:34:10.088220+00:00`.
- `files=24`, `symbols=24`, `errors=[]`, total rows `15847737`, zero-row files `[]`.
- Earliest tick in manifest: `2026-06-01T00:05:00.073000+00:00`; latest tick in manifest: `2026-06-06T01:59:59.863000+00:00`.
- Artifact size: about `3.2G`.

## 3. Baseline Comparison

Fable/current-stack anchors:

- V122J hostile B4 truth baseline, `2026-05-13..2026-05-17`: `54` trades, `-3.52793853R` net, `+0.80431616R` gross/final, `-$2864.90534326` cash PnL, W/L/F `30/24/0`, `23575` candidates, `288` scorecard rows, `127` orders, `23512` missed rows, `37` filled axes, `475938.7001370051R` source-bound R in-window, `-4.0917195R` axis-attributed executable R.
- V126 hostile B7.2 truth result, same window: `55` trades, `-4.43962487R` net. This worsened V122J by `-0.91168634R` and added net-negative transfers.

Older comparator anchors:

- V89D hostile `2026-05-13..17`: `56` trades, `+34.84520454R` net, `+39.93441037R` gross/final, cash `+$8178.90660707`, W/L/F `41/15/0`.
- V90 hostile `2026-05-13..17`: `51` trades, `+28.84201157R` net, `+33.36349114R` gross/final, cash `+$6371.80465431`, W/L/F `37/14/0`.
- V92 hostile `2026-05-13..17`: `51` trades, `+29.35570236R` net, W/L/F `37/14/0`.
- V121AG hostile `2026-05-13..17`: `45` trades, `+21.82482975R` net, `+25.17869106R` gross/final, cash `+$12465.17720161`, W/L/F `27/18/0`.

Non-hostile objective comparator:

- V104 non-May objective `2026-06-01..2026-06-05`: `46` trades, `+14.73101491R` net, `+18.36174510R` gross/final, cash `+$2850.02330565`, W/L/F `26/20/0`, `35191` candidates, `480` scorecard rows, `111` order events, `35135` missed rows, `894/1101` candidate-generated axes, `33` scorecard/order axes, `27` filled axes, `426601.3938625386R` source-bound R in-window, `+13.36917856R` axis-attributed executable R.

V104 is not a current-code proof; it is the closest same-window non-May comparator for V127.

## 4. Dirty Files And Active Code Changes

Current HEAD includes:

- `1ff228058 Materialize Fable B7 authority proof`
- `4152368dc Record Fable B7.2 hostile proof`

Unstaged unrelated dirty files remain in the worktree, including Context OS docs/code, older V95 artifacts, config/code/test files, and deleted stale science-program JSONL files. They are not part of this B7.3 replay unless explicitly patched later.

Active intended change before V127 replay: this pre-replay brief only. No production code change is being introduced before B7.3.

## 5. Subagent Findings

- Cicero / B6 read-only pass: incorporated. Findings are reflected in B6 matrix closure and V123 audit/repair: broker-calibrated cost is authority, REFUSED/source-gap rows remain non-executable, USDJPY stale/mapping producer proof was repaired, and current V126 verifier has zero executed REFUSED/source-gap rows.
- Copernicus / V122J read-only pass: incorporated. Findings are reflected in B4/B5 matrix closure, V122J parity/comparison rebuild, V126 B7.2 comparison, and the current need to separate hostile-regime behavior from systemic transfer failure.
- No active subagent result is pending before V127.

## 6. Known Mismatch Classes

- Source-bound -> candidate: partially healthy but still low conversion quality. V126 has `886/1101` candidate-generated axes; V104 had `894/1101`. Candidate generation itself is not the current choke, but generated candidates still carry weak scorecard/order transfer.
- Candidate -> selector: truth surfaces are repaired for raw/effective action and broker-cost authority. Remaining risk is whether signed authority admits stop-loss-prone transfers without enough causal quality.
- Selector -> scheduler: open B7 transfer quality risk. V126 added signed-authority transfers but they were net negative. V104 non-May had `480` scorecard rows and `33` scorecard/order axes; V126 hostile had `288` scorecard rows and `42` scorecard/order axes.
- Scheduler -> risk: risk provenance is preserved. Remaining risk is risk-expression quality, especially full/reduced distribution and whether reallocation selects strong candidates or just makes more weak candidates executable.
- Risk -> order: broker-cost REFUSED/source-gap execution is closed by verifier. Remaining risk is order materialization quality, stop geometry, guarded fallback drift, and marketable/limit decision quality.
- Order -> lifecycle/fill: fill realism is clean on V126, but conversion is behavior-negative. Remaining risk is pending/expiry/replacement/same-symbol handling in non-hostile windows.
- Fill -> exit: current highest likely root leak after V126. Added B7.2 transfers became stop-loss losers; exit/stop geometry and profit-harvest preservation must be audited after non-hostile proof.
- Ledger/verifier: current route verifier is green. Remaining risk is comparison precision after V127 and route manifest binding to the new prefix.

## 7. Fixed / Partial / Open

- Fixed: B0 instrumentation, B1 provenance truth, B2 fillability/reallocation truth chain, B3 risk-expression provenance, B4 fill realism, B5 verifier/comparison precision, B6 broker-cost calibration audit.
- Partial: B7 proof ladder. B7.1 one-day targeted proof and B7.2 hostile five-day proof are complete; B7.2 is behavior-negative.
- Open: B7.3 non-hostile objective five-day proof, B7.4 broader holdout proof, B7.5 final proof-ladder synthesis.
- Open after proof if systemic: selected-transfer quality, stop/exit/profit-harvest damage, scheduler/reallocation value model, risk-expression distribution, and non-hostile source/fill availability.

## 8. Next Batch

Next dependency batch: B7.3 non-hostile objective five-day proof.

Selected window: `2026-06-01..2026-06-05`.

Reason:

- It is outside the hostile May 13-17 stress bucket.
- It has a prior V104 same-window comparator with positive executable behavior.
- It exercises the full 24-symbol surface and five trading days.
- It tests whether V126 behavior is hostile-regime-specific or systemic under the current B0-B6/B7.1/B7.2 code.

## 9. Exact Files / Components Affected

No code patch before V127. Replay will exercise:

- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/analyze_broad_live_as_if_replay_flow.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/compare_broad_live_as_if_replay_runs.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_denominator_to_deployment_execution.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/components/selector_v4.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/components/broker_net_cost_engine.py`

## 10. Patch Type

This checkpoint is diagnostic/proof, not a code patch. It is required by Fable B7 before tuning more policy from the hostile slice.

## 11. Expected Measurable Effect Before Replay

Because no code changes are introduced after V126:

- Candidate -> scorecard transfer should be comparable to V104 non-May order of magnitude, not necessarily identical because B7 code differs.
- Scorecard -> order transfer should reveal whether signed authority improves or worsens same-window order conversion versus V104.
- Order -> fill transfer must remain truth-clean: no executed broker-cost REFUSED rows, no source-gap executable fills, no broker/live/final true rows.
- Missed positive R should remain separated from missed negative R and classified by broker-cost/source/fillability/order/lifecycle reason.
- Trade count should be interpreted against V104 same-window `46` trades, not against V126 hostile `55` trades.
- Net/gross/final R should be interpreted against V104 same-window `+14.73101491R` net and V126 hostile `-4.43962487R` only as regime context.
- W/L/F should be compared to V104 `26/20/0`.
- Cost-refused/source-gap execution must stay `0`.
- Risk-reduced/full-risk distribution must be reported separately. V104 had all terminal orders reduced-risk; V126 hostile had `16` full-risk and `39` reduced fills. V127 must show whether full-risk expression transfers edge or damage outside the hostile bucket.

## 12. Proof / Failure Criteria

Helped:

- V127 is truth-clean and materially closer to or better than V104 same-window behavior while preserving B7 authority/provenance repairs.
- Improvement is explained by better conversion/selection/scheduler/risk/order/lifecycle/exit, not by suppressing all opportunity.

Failed:

- V127 is truth-clean but materially worse than V104 on the same `2026-06-01..2026-06-05` window.
- Added signed-authority transfers are net negative again, especially through stop-loss/exit geometry.

Exposes next root issue:

- Candidate axes remain high but scorecard/order/fill axes remain weak: patch scheduler/reallocation/value-model transfer next.
- Scorecard/order axes rise but filled trades lose: patch selected-policy stop/exit/profit-harvest geometry next.
- Full-risk rows lose disproportionately: patch signed risk-expression ladder and risk budget/headroom/reallocation quality next.
- Reduced-risk rows still dominate and suppress winners: patch causal risk-expression promotion conditions next.
- Refused/source-gap rows execute: stop immediately and patch verifier/code authority leak before more replay.

Broker/live/final remain false. Local replay/package authority remains full. This replay proves the B7.3 non-hostile slice only; it does not prove total source-bound reservoir conversion.
