# Pre-Replay Brief - V122I Fable B4 Hostile Fill Realism

Generated: `2026-07-06T05:37:55Z`

This is the control brief for the next Fable dependency step. It is not a broad-reservoir proof and must not be interpreted against the global million-R denominator.

## Current State

- Latest completed replay: `BROAD_LIVE_AS_IF_REPLAY_V122H_FABLE_B4_TICK_ENABLED_SOURCE_REALISM_20260610_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`
- Scope: bounded one-day `2026-06-10`, full configured candidate surface, 9-symbol ordered tick export available, repaired package profile, compact missed ledger.
- Active replay process: none.
- Existing V122I artifacts: none.
- Broker/live/final: closed.
- Local replay/package authority: full.
- Working tree: still contains unrelated older dirty files and deletions. Do not stage or revert them for this checkpoint.

## Fable Batch Matrix

- B0: DONE.
- B1: DONE.
- B2: DONE.
- B3: DONE WITH LABEL.
- B4: PARTIAL.
- B5: DONE WITH LABEL.
- B6: OPEN after B4 hostile fill-realism proof.
- B7: OPEN after B1-B6 closure.
- B8: OPEN after B7 pass.

## Baselines

Same-window hostile comparators for `2026-05-13..2026-05-17`:

| Run | Trades | Net R | Gross/Final R | Cash PnL | W/L/F |
| --- | ---: | ---: | ---: | ---: | --- |
| V89D | 56 | 34.84520454 | 39.93441037 / 39.93441037 | 8178.90660707 | 41/15/0 |
| V90 | 51 | 28.84201157 | 33.36349114 / 33.36349114 | 6371.80465431 | 37/14/0 |
| V92 | 51 | 29.35570236 | not reloaded here | not reloaded here | 37/14/0 |
| V121AG | 45 | 21.82482975 | 25.17869106 / 25.17869106 | 12465.17720161 | 27/18/0 |

V121AG same-window transfer context: source-bound R `407295.6072920759`, package axes `1101`, generated candidate axes `886`, scorecard/order axes `33`, filled trade axes `29`, actual executable R `21.29589138`.

Latest local B4 proof, V122H `2026-06-10`:

- candidates `6369`, scorecard `96`, top-level orders `29`, terminal/simulated orders `13`, trades `10`, missed `6356`, oracle rows `16`.
- net R `0.07137833`, gross/final R `0.86997526 / 0.86997526`, cash PnL `158.91066658`, risk cash `4006.86646365`, risk pct total `4.0`, W/L/F `7/3/0`.
- stress: +0.05R/trade `-0.42862167`, +0.10R/trade `-0.92862167`, +0.20R/trade `-1.92862167`.
- Monte Carlo: total R `0.07137833`, max DD p50 `-1.74320136`, p05 `-2.72456294`, worst `-2.74456294`.
- truth checks: executed REFUSED cost `0`, executed source-gap `0`, live mutation `0`, final true `0`, missing risk ladder `0`, executable M15 proxy `0`, executable first-touch optimistic `0`.

V122H was useful because it converted the V122E skip-tick no-fill slice into `10` realism-passing fills without changing candidate or scorecard transfer. That improvement came from ordered tick source conversion, not from suppressing opportunity.

## Current Root-Cause Map

- `source-bound -> candidate`: partially fixed. Same-window axes are tracked; V122H candidate count stayed stable versus V122E.
- `candidate -> selector -> scheduler`: fixed for the current dependency. Raw/effective selector, scheduler provenance, and risk-ladder projection have focused tests and verifier coverage.
- `scheduler -> risk -> order`: partially fixed. V122H has zero executed REFUSED/source-gap rows, but B6 cost-cell calibration remains open.
- `order -> lifecycle -> fill`: active B4 issue. V122H proves ordered tick conversion, but hostile five-day fill-realism proof is still required.
- `fill -> exit -> ledger`: fixed for current dependency. R identity and bridge/verifier proof surfaces are green on executable rows.

V122H blocker classification:

- B6 cost refusal/cost authority: `4870` rows, `423` scoreable, opportunity net `-264.70564042R`, positive `+62.42658513R`, negative `-327.13222555R`.
- B2/B3 scheduler-risk/admission: `133` rows, `133` scoreable, opportunity net `-26.27521669R`.
- B4 order geometry guard: `106` rows, `106` scoreable, opportunity net `-17.82874179R`.
- B4 source realism/missing ordered source: `696` rows, `0` scoreable, diagnostic proxy mark net `-0.0166692602R`.
- Fill-realism missed classes: ordered tick `525` scoreable rows, source-safe immediate `150` scoreable rows, M15 proxy `4502` unscoreable rows, not-filled `1077`, source-gap `94`.

Interpretation: remaining missed rows are not all B4 source leaks. Do not make proxy rows executable. Do not loosen broker-cost REFUSED rows. The next correct dependency step is the hostile five-day fill-realism proof; if it passes, move to B6 cost calibration.

## Subagent Findings

- Huygens: incorporated. MT5 bridge is live; raw RPyC and `terminal_info()` succeeded. Broker trading remains disabled.
- Rawls: incorporated. V122H command semantics are V122E one-day repaired profile without `--skip-tick-source`; use same semantics for the hostile proof.
- Avicenna: incorporated. Lazy tick hash validation and actual manifest `first/last` coverage are required; V122H proves ordered-price-path truth, not broker lifecycle truth.

## Next Action

Run the smallest replay that proves the next Fable dependency:

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-13 \
  --end 2026-05-17 \
  --chunk-size 1 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V122I_FABLE_B4_HOSTILE_5D_FILL_REALISM_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH \
  --omit-packet-sidecar-ledger \
  --compact-missed-ledger
```

This is a five-day hostile/stress B4 proof, not a global-reservoir proof.

## Success Criteria

- Completed final summary, not interrupted partial.
- Broker/live/final remain false.
- Executed REFUSED cost rows remain `0`.
- Executed source-gap rows remain `0`.
- Executable M15 proxy and first-touch optimistic rows remain `0`.
- Ordered tick rows include lazy hash validation where overlapping tick files are used.
- Report same-window candidate -> scorecard/order -> fill transfer.
- Report headline behavior separately from diagnostic missed/proxy rows.
- Report full-risk vs reduced-risk distribution.
- Report missed positive and negative R by reason.

## Failure Or Next-Flaw Criteria

- If diagnostic/proxy rows execute, B4 truth is broken and code must be patched before broader replay.
- If the May hostile window lacks ordered tick source but MT5 can hydrate it, hydrate exact symbol/window tick data instead of accepting source absence.
- If ordered source exists but fill-source routing remains diagnostic-only, patch fill-source routing/order-path binding.
- If B4 truth holds and the dominant remaining scoreable blocker is cost refusal, proceed to B6 broker-cost calibration rather than retuning selector from one symptom.
