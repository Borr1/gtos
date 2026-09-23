# V120B B1/B3 Order-Executable Proof Contract Pre-Replay Brief

Generated: 2026-07-04T14:58:00Z

Broker/live/final remain closed. Local replay/package authority remains full for the 82-sleeve surface. This brief is the checkpoint before a targeted replay, not a live claim.

## Current Latest Completed Replay

Latest completed replay on disk is `BROAD_LIVE_AS_IF_REPLAY_V119C_PASSIVE_DISTANCE_QUEUE_RELEASE_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`.

Window: `2026-05-13..2026-05-17`.

Numbers: 288 scorecards, 16 order ledger rows, 5 trades, 2761 missed rows, net R `-5.50984356`, gross/final `-5.0/-5.0`, cash PnL `-550.50060863`, W/L/F `0/5/0`, missed `+224.65585079R / -1847.06522503R / -1622.40937424R`.

Behavior: all 5 trades are BTCUSD LONG reduced-risk stop losses. V119C is a worse hostile 5-day behavior artifact than V119, and it exposes missing order-executable transfer status on scorecard/order/trade/missed rows.

## Same-Window Baselines

| Run | Trades | Orders | Scorecards | Missed | Net R | W/L/F |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| V89D | 56 | 243 | 288 | 24885 | 34.84520454 | 41/15/0 |
| V90 | 51 | 233 | 288 | 24890 | 28.84201157 | 37/14/0 |
| V92 | 51 | 239 | 288 | 24887 | 29.35570236 | 37/14/0 |
| V119C | 5 | 16 | 288 | 2761 | -5.50984356 | 0/5/0 |

V90 artifact risk: its summary says scorecard ledger was materialized, but the scorecard ledger is absent on disk.

## Comparator Evidence

`/tmp/gtos_v119c_v92_compare_order_exec_transfer_smoke.json` compares V119C to V92 over the same window.

Key deltas: trades `-46`, net R `-34.86554592`, 4 added trades `-4.41387337R`, 50 removed trades `+30.45167255R`.

V119C order-executable missing transfer status:

- scorecard: 97
- order: 16
- trade: 5
- missed: 92

The patched comparator now treats order/trade order-executable rows without transfer status as failures, not as a hidden detail.

## Current Patch Batch

Implemented before replay:

- Saved Fable implementation sequence and audit plan under `.context/context_os/ultimate_system_plan/`.
- Added order-executable transfer/blocker rollups to the comparison parser across scorecard/order/trade/missed.
- Made comparison parser retry transient JSONL read timeouts.
- Made comparison parser hard-fail mismatched summary windows and report missing expected ledgers.
- Added comparator failures for order/trade order-executable rows without transfer status.
- Imported selector open-reduced reasons from the shared replay contract.
- Added a separate off-session reduce-risk reason so open-reduced authority is not counted when not granted.
- Synced shared reduce-risk reason contract.
- Added scorecard-reported order-executable aliases to verifier flag/reason/source tuples.
- Added verifier fatal scan for selector materialization without original selector action and for R identity drift.
- Treated simulated trade id as trade-bound unless fill status explicitly says non-filled.

## Subagents

Kierkegaard: incorporated. B1 provenance mostly exists but needed contract drift tests, broad materialization/R identity fatal checks, and replay interpretation guardrails.

Ramanujan: incorporated. V119C is the latest completed artifact; comparator needed exact-window hard failure, ledger missing reports, explicit profiles, and order/trade transfer failures.

Kant: incorporated. B3 off-session reason/action semantics were still wrong; V120 transfer could still emit unbound rows; trade-bound status could fall through if fill status was absent.

## Mismatch Map

Source-bound -> candidate: partially fixed. Claims must stay exact-window normalized.

Candidate -> selector: partially fixed. B3 off-session reason/action mismatch is fixed in this patch; full selector regression suite still pending.

Selector -> scheduler: partially fixed. V120 scheduler transfer fields exist; replay must prove status emission in scorecard/order/missed/trade ledgers.

Scheduler -> risk: open. V119C remains all reduced-risk; risk-expression distribution must be measured after V120B.

Risk -> order: open. V119C had missing transfer status on 16 order rows and 5 trade rows.

Order -> lifecycle/fill: partially fixed. Trade-bound ID detection is fixed; canonical fallback-window expiry disposition remains open.

Fill -> exit: deferred until enough clean transfer rows exist.

Ledger/verifier: improved. Order-executable transfer, selector materialization, and R identity are now first-class verifier/comparator surfaces.

## Replay Criteria

Run targeted proof before broad replay. The next replay should be a 2026-05-13 V120B repaired-package smoke if it exercises order-executable transfer rows; then rerun the 2026-05-13..17 hostile bucket only after targeted proof is green.

Success:

- every order-executable true row has transfer status: `order_bound`, `trade_bound`, `final_blocked`, or `not_order_executable`;
- zero order/trade rows with missing transfer status;
- no cost-refused/source-gap/false-order-executable executed rows;
- selector materialization rows preserve original selector action;
- R identity drift is zero where gross/cost/net proxy fields exist;
- trade count and R are reported as bounded local proof, not full reservoir transfer.

Failure:

- order-executable rows still disappear as missing transfer status;
- positivity comes from suppressing opportunities;
- added trades are net negative without a new causal blocker explanation;
- materialized raw/effective selector action lacks original provenance.
