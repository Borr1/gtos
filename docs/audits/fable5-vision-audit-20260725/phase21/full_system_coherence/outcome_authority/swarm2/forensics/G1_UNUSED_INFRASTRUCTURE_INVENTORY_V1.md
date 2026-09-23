# G1 — the unused-infrastructure inventory: what already exists and is not being used

**Commission:** owner swarm, discovery lane G1, 2026-08-12. *"A full sweep of this project for
capability that exists and is not being used."* The trigger was the owner noticing that a swarm
rebuilt trade forensics from scratch while forensic machinery already sat in the repo.

**Scope discipline.** Discovery, not judgement. No broker, no VPS, no config byte, no `src/` edit,
no decision-contract-bound file, no git write. Read-only throughout; the two working-tree mutations
that occurred were a sub-lane's accidental artifact and this lane's own scratch, both reverted (§8).

**Method.** Mechanical orphan index over all 1,146 `scripts/` + `src/` modules (name → set of
referencing files, orphan = referenced only by itself), plus five parallel territory sweeps
(`scripts/` a–m, `scripts/` n–z + `scripts/research/`, `research/` non-ops, `research/operations/` +
`science_program`, `docs/audits/**/receipts/`), plus direct execution of the top candidates.
**MEASURED** = I ran it or resolved and inspected the bytes. **INFERRED** = read from code + input
`ls` only.

---

## 0. The answer in five lines

| # | asset | what it tells the owner | state |
|---|---|---|---|
| 1 | `phase19/receipts/discovery/w0_ws.py` → `w0_WORKING_SET.jsonl.gz` | Every candidate's excursion **and** the reason the system refused it, in one table | **MEASURED: loads 27,658 rows × 128 cols in 0.56 s** |
| 2 | `LANE16_PATH_ANATOMY_LEDGER.jsonl.gz` | How far all **289,928** candidates went, how far against, and what shape the path was | **MEASURED: `mfe_r`/`mae_r` on 289,927 of 289,928** |
| 3 | `src/research_infra/b7_5_diagnostic_pool.py` | The 28,519 candidates the incumbent **rejected**, with why, and what they went on to do | **MEASURED: reads sealed cold shards, 95 fields/row, 0.3 s** |
| 4 | `scripts/analyze_missed_fill_opportunities.py` | How far price came to the limit that never filled, and what entry shift would have caught it | **MEASURED: I ran it — 8.75 % miss rate, median 1.12 R** |
| 5 | `scripts/w7_live_forensics.py` + `w7_packet_forensics.py` | What the book **thought** it was doing versus what the broker **did**, per live trade | MEASURED `--help`; inputs present (pre-arming only) |

> **One sentence for the owner: the forensics you asked for have been computed at least three times
> already — on 27,658 candidates, on 289,928 candidates, and on 28,519 rejected ones — and the
> reason nobody found them is that `shadow_logs/`, `knowledge_base/` and most of `research/` are
> excluded from this worktree's sparse-checkout cone, so they read as missing files rather than as
> data.**

---

## 1. THE UNBLOCK — this is bigger than any single item on the list

**The forensic estate is not gone. It is un-checked-out.** [MEASURED]

| fact | measurement |
|---|---|
| `core.sparseCheckout` | `true` in this worktree and in `/Users/borr/GTOSActive/repo` |
| `shadow_logs/` tracked in `origin/main` | **138 ledgers** |
| `shadow_logs/` present in the working tree | **5** |
| Git-LFS objects already on this disk | **42 GB / 1,246 objects** at `/Users/borr/GTOSActive/repo/.git/lfs/objects` |
| `research/` subdirs on disk | 8, against the full tracked set |

Every `FileNotFoundError` that made a forensic script look dead in this sweep resolved to this one
cause. The four inputs of item 4 below are 49 MB + 29 MB + 44 MB + 26 MB of LFS content **already
on the disk**, addressable but not materialised.

**The recommended unblock (a human should run this, not an agent — it mutates the working tree):**

```
git sparse-checkout add shadow_logs knowledge_base \
  research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04 \
  research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31 \
  research/operations/vnext_live_activation_active_repair_companion_2026_05_28
git lfs checkout
```

**Two hazards to respect before doing it**, both from `CLAUDE.md`:

- **H1 / B185** — the decision-contract drift count is a property of *LFS hydration state*, not of
  any commit. Hydrating is the fix, not the risk (`git lfs checkout <path>` **then** read the
  count). De-hydrating is the risk.
- **B905, standing** — never clean, stash, or re-checkout
  `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` **in the main repo**
  (`/Users/borr/GTOSActive/repo`). The R2 seal is satisfied only by the uncommitted working copy
  there. `git sparse-checkout add` in *this worktree* does not touch it, but confirm the cwd.

Two LFS objects are genuinely absent locally: `shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl`
(1.5 GB) and `shadow_logs/structure_detector_divergences.jsonl` (310 KB). The first is
**regenerable on this machine** by `scripts/backfill_live_mechanical_shadow_outcomes.py` from
inputs that are present.

---

## 2. The top five, in full

### 1. `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/w0_ws.py`

**What it tells him.** For every candidate in the wave-19 pool: how far it ran, how far it went
against, when it did each — *and* which gate refused it and why. Excursion and refusal in the same
row, which is the join every forensics lane has had to build by hand.

**MEASURED, executed 2026-08-12.** `w0_ws.load()` → **27,658 rows, 128 columns, 0.56 s.**

- Excursion family: `mfe_r`, `mae_r`, `bars_to_mfe`, `bars_to_mae`, `bars_to_mfe_after_stop`,
  `mae_r_before_target`, and the by-bar ladders `mfe_r_by_bar_{5,15,30,60,120}` /
  `mae_r_by_bar_{5,15,30,60,120}`.
- Decision family: `final_blocker_class`, `miss_reason`, `selector_action`, `selector_reason`,
  `effective_selector_action`, `effective_selector_reason`, `scheduler_selection_disposition`,
  `scheduler_materialization_status`, `risk_finalizer_reason`, `risk_finalizer_rank`.
- **`final_blocker_class` distribution, measured:** `cost_authority` **20,448**, `other` 2,684,
  `package_authority` 2,668, `scheduler_selection` 689, `execution_fillability` 449,
  `selector_materialization` 369. **73.9 % of candidates die at the cost gate.**

**Substrate.** `w0_WORKING_SET.jsonl.gz`, 10.3 MB, committed. Documented in
`w0_WORKING_SET_README.md`.

**Called by?** 142 files reference it — **all inside wave 19**. Nothing in the current swarm uses it.

**Redundancy.** Its excursion columns overlap F1's census. Its **decision/refusal columns exist
nowhere in the in-flight lanes** — that is the unique value. Defer to F1 for excursion on the
Feb–Jul corpus; use this for "why was it refused, and was the refusal right".

**Cost to revive: trivial** — a three-line import.

**Caveat.** `w0_ws.walk()` needs `w0_R_PATHS.jsonl.gz`, which is **absent** (never committed).
`load()` does not. Rebuildable from `phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz`
(34 MB, present).

---

### 2. `research/operations/vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01/LANE16_PATH_ANATOMY_LEDGER.jsonl.gz`

**What it tells him.** For every one of 289,928 candidates: the maximum it reached, the maximum it
gave up, and which of ten path shapes it traced.

**MEASURED, full scan 2026-08-12.** 38.6 MB gzip, **289,928 rows × 78 fields**;
`mfe_r` non-null **289,927**, `mae_r` non-null **289,927**.

`path_class` census, measured in full:

| path_class | rows |
|---|---:|
| `winner_reached_1r_or_better` | 142,820 |
| `positive_less_than_1r_policy_exit` | 56,734 |
| `breakeven_or_partial_be_return` | 53,055 |
| `loss_sl_or_stop_policy_exit` | 36,519 |
| `negative_policy_exit_before_1r` | 471 |
| `loss_sl_before_partial_trigger` | 200 |
| `winner_partial_then_be_return` | 73 |
| `winner_partial_then_dynamic_final` | 36 |
| `stuck_entry_no_sl_or_1r_before_friday_close` | 12 |
| `partial_trigger_then_open_at_friday_close` | 5 |

Also carries `origin_family`, `mechanism_family`, `regime_h4_state`, `session_bucket`,
`best_policy_id`, `current_policy_cost_adjusted_median_r`, `no_entry_touch`, `sl_before_1r`.

**Called by?** Nothing outside its own route plus `build_vnext_absolute_moonshot_scheduler_v3.py:55`.
Selector/Scheduler V3 are `false`/default-off (`CLAUDE.md` §4), so the whole estate was orphaned in
place when the route parked.

**Redundancy.** F1's census covers **146,736 filled trades** across five sealed 2026 months. This is
**289,928 candidates** — a different and larger population, including candidates that never filled.
F1 §1.2 inventories "fifteen places" of prior forensic machinery and **names none of this route**.
Not a duplicate; a complement at ~2× the population on the candidate rather than the fill axis.

**Correction to a sub-lane claim.** The fields `missed_opportunity` and `correct_rejection` exist
but are **effectively unpopulated**: measured `missed_opportunity == true` on **1** row and
`correct_rejection == true` on **3** rows of 289,928. Do not plan work that depends on them. The
MFE/MAE/`path_class` census is the real asset here.

**Cost to revive: trivial** — plain gzip + JSON, no seal, no contract, no LFS.

**Siblings in the same estate, same population, also unread** (INFERRED, sizes measured):
`SCHEDULER_V3_BLOCKED_EDGE_RECOVERY_LEDGER.jsonl.gz` (14.7 MB, 179,575 rows — what the scheduler
refused and what the refusal cost), `SCHEDULER_V3_ACCEPTED_REDUCED_REJECTED_DECISION_LEDGER.jsonl.gz`
(25.6 MB — accepted / size-reduced / rejected per rule),
`HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz` (18.2 MB — R left on the table vs the best
available policy; **zero `.md` in the repo references its route**).

---

### 3. `src/research_infra/b7_5_diagnostic_pool.py`

**What it tells him.** The candidates the incumbent policy **turned down**, with the reason it
turned them down and the counterfactual outcome they went on to produce. This is the owner's
standing question pointed at rejections rather than fills.

**MEASURED, executed 2026-08-12.**

- `sealed_arm_counts()` → four January arms. S0R0: **154,299 rows**, **28,519 scoreable diagnostic
  rows**, **+6,916.95 R** across 8,006 positive rows against **−31,400.82 R** across 20,513 negative.
  S0R1/S1R0/S1R1 within a few rows of that.
- `iter_arm_rows(ARMS["S0R0"])` read rows off the **`.cold` zstd shards in 0.3 s**. **95 fields per
  row**, including `miss_reason`, `selector_reason`, `effective_selector_reason`,
  `risk_finalizer_reason`, `outcome_close_reason`, `outcome_net_proxy_r`, `expected_net_r`,
  `entry_quality_fill_probability`, `entry_fill_executable`, `same_symbol_lifecycle_action`.
- `DEFAULT_LEDGER_ROOT` → `/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`
  — **exists, 6.2 GB.** Overridable with `GTOS_B7_5_LEDGER_ROOT`.

**Called by?** `train_engine/cuts.py`, `train_engine/footprint.py`, and session AW's separability
mine — **and all of them read January only**.

**The unused half.** `ARMS["APR_S1R1_PARTIAL"]` is already wired and has never been read. April's
15 sealed days sit at `.../attempt_5_typed_sparse/PHASE_D_APRIL_S1R1_R1_20260725T070249Z/`,
**501 MB across 8 ledgers** (MISSED_OPPORTUNITY 84.8 MB, DECISION 79.2 MB, SCORECARD 60.2 MB,
ORDERED_PATH_ORACLE 11.8 MB raw). The campaign's "no partial credit / no resume path" is a statement
about **economics**; the **forensics are readable today** without running a single replay hour.

**Cost to revive: trivial** to re-point at April or at the other three arms.

**Honest priors the module already carries and any caller must quote:** these are **proxy** outcomes,
not realised trades; 64 % precision is needed to break even against a 28.1 % base rate; the F31
gap-through charge is −0.038186 R per level-exit row.

---

### 4. `scripts/analyze_missed_fill_opportunities.py` → `src/research_infra/missed_fill_opportunity_study.py`

**What it tells him.** Of the candidates whose limit never filled, how many went on to reach the TP
area anyway, how much *further inside* the entry would have had to be to get filled, and what a
0.25 / 0.50 / 0.75 / 1.00 R entry shift would have caught. This is the generation-quality axis the
owner says is still open — accuracy at entry, not re-ranking a fixed pool.

**MEASURED — I executed it end to end on 2026-08-12** against the live shadow corpus staged from
`vps-export-20260725/extracted/05_shadow_logs/`:

| measurement | value |
|---|---:|
| raw candidates with a latest cluster | 404 |
| countable primary opportunities | 80 |
| **countable missed-fill-to-TP-area** | **7 (8.75 %)** |
| of those, needing > 1 R further inside | 4 |
| median inside-R required (countable) | **1.1236** |
| max / min inside-R required | 4.2577 / 0.2291 |
| TP1 first touch on the same decision candle | 5 |
| shifted-entry ladder (share of computable misses caught) | 0.25 R → 14.3 %, 0.50 R → 28.6 %, 0.75 R → 28.6 %, **1.00 R → 42.9 %** |

**Called by?** **Nothing. Zero external references** — one of only 138 fully orphaned modules of
1,146, and by a distance the highest value-to-effort ratio in that set.

**Inputs** (`missed_fill_opportunity_study.py:161-164`): `shadow_logs/strategy_follow_candidates.jsonl`,
`live_candidate_opportunity_clusters.jsonl`, `candidate_path_follow.jsonl`,
`candidate_ltf_path_order.jsonl`. All four are LFS objects **present on this disk** (49 / 29 / 44 /
26 MB) and also decompressible from the VPS export.

**How to run it** (exactly what I did):

```
mkdir -p /tmp/mfroot/shadow_logs && cd /tmp/mfroot/shadow_logs
SRC=/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs
for n in strategy_follow_candidates live_candidate_opportunity_clusters \
         candidate_path_follow candidate_ltf_path_order; do
  gzip -dc "$SRC/$n.jsonl.gz" > "$n.jsonl"; done
cd <repo> && python3 -c "
import sys; sys.path.insert(0,'.')
from src.research_infra.missed_fill_opportunity_study import build_study
import json; print(json.dumps(build_study('/tmp/mfroot'), indent=2))"
```

(The `scripts/` CLI works too but defaults its outputs into
`research/program_control/MISSED_FILL_ENTRY_GEOMETRY_STUDY_2026-05-12.{json,md}` — pass
`--output-json` / `--output-md` to a scratch dir so it leaves no repo dirt.)

**Cost to revive: trivial.** **Caveat: n = 80 countable opportunities.** The measurement is a
demonstration that the instrument works, not a result to size on.

---

### 5. `scripts/w7_live_forensics.py` + `scripts/w7_packet_forensics.py`

**What they tell him.** The pair answers the live/replay reconciliation question from both ends:
`w7_live_forensics` reconstructs, per live trade, **which sleeve placed it, at what true R, and
which trades made the drawdown** — from **broker deal/order truth**, attributing the sleeve from the
`W7:<sleeve>` deal comment and self-calibrating $/price-unit from realised P&L, which matters
because the GTOS-side ledgers stop on 2026-07-02. `w7_packet_forensics` answers the same window from
`ultimate_book_runtime_learning_packets.jsonl.gz` — what the book *thought*. Run together they are
"intent versus fill" on real money.

**MEASURED** `--help` clean on both; both hardcoded roots exist; `w7_live_forensics` outputs already
sit in `docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/`. refs 35 and 11.

**Cost to revive: trivial** — pass `--out-dir` to a scratch path.

**Adjacent and also cheap, same axis, both MEASURED-RUN by a sub-lane:**

- `scripts/reconcile_cost_layer_to_broker_truth.py` — *does `src.costs.cost_r` predict what the
  broker actually charged?* Ran in full: **175 rows, 130 used, max |err| 0.001 R**, coverage measured
  on every row. Needs `PYTHONPATH=.`.
- `scripts/ultimate_book_packet_silence_alarm.py` — *did the live book stop thinking, and for how
  long?* Ran in full: **FTMO 43 gaps > 1800 s, longest 417.6 min; redacted_account 5 gaps, longest
  2,895.6 min**, against its own measured baseline (p99 909.6 s). That is a live-health finding
  sitting in a tool nobody runs.

---

## 3. The blocker that gates the whole live-forensics axis

**No post-arming live data exists on this machine.** [MEASURED]

The only live corpus is `vps-export-20260725/`, frozen **2026-07-25**. FTMO armed **2026-07-29**,
redacted_account **2026-07-30**. The `ultimate_book` packet stream in that export spans
**2026-06-18T17:06 → 2026-07-25T22:05, 99,112 rows** — entirely the *pre-arming* shadow period.

Every tool in §2 item 5 and every live/replay instrument below can therefore only describe the book
before it traded real money. **A fresh VPS pull of `shadow_logs/` + `09_mt5_api/` is the single
highest-leverage dispatch in this report**, and it is a transport task, not a research task. This
lane did not perform it (no VPS contact).

---

## 4. Capability that exists but is disconnected

### 4.1 The observation estate went dark at the architecture change

**[MEASURED]** Roughly twenty shadow loggers in `src/components/` are wired to
`src/components/orchestrator.py` — the legacy AI path. The live decision surface is now the
`ultimate_book` W7 book via `run_book.py`. The loggers stopped when the path changed:

| logger output | last row |
|---|---|
| `candidate_features_log.jsonl` | **2026-05-13** |
| `missed_opportunity_shadow.jsonl` | **2026-06-01** |
| `live_mechanical_strategy_shadow_outcomes.jsonl.gz` | **2026-06-01** |
| `slippage_runtime.jsonl` | 2026-07-02 |
| `broker_order_lifecycle_capture_v4.jsonl` | 2026-07-02 |

The family: `be_shadow_logger`, `candidate_features_logger`, `d1_bias_lag_logger`,
`direction_emission_logger`, `dumb_baseline_shadow_logger`, `evaluation_logger`,
`j46_j49_shadow_logger`, `partial_close_shadow_logger`, `pending_limit_lifecycle_logger`,
`proximity_shadow_logger`, `regime_shadow_logger`, `sl_beyond_ob_shadow_logger`,
`slippage_shadow_logger`, `structure_detector_shadow_logger`, `time_in_trade_shadow_logger`,
`touch_count_gate_logger`, `trailing_stop_shadow_logger`, `ai_decision_trace_logger`,
`cross_instrument_correlation_gate_logger`.

**The consequence, which is the point.** The current live packet carries **46 fields** [MEASURED] —
`event_type`, `skip_reason`, `outcome`, `spread_r`, `placement_status`, and so on. It records the
**decision** and never the **path**: no MFE, no MAE, no excursion, no entry-geometry, no
path-follow. So the armed book has *less* introspection than the shadow-era system it replaced.
Measured event mix over 99,112 packets: `position_managed` 78,687 / `unit_skipped` 14,638 /
`cycle_no_candidates` 4,325 / `unit_shadow` 545 / `unit_admitted` 440 / `position_adopted` 181 /
`position_closed` 151 / `unit_placed` 145. Top `skip_reason`: **`profile_missing_instrument_config`
13,254** — which is the "redacted_account silently skips 13 symbol/sleeve pairs" gap `CLAUDE.md` §4 already
names, visible in the packet stream and quantified here for the first time. `reject_reason` is
**empty on every row**.

**Revival cost: a session** — adapt `live_mechanical_shadow.py` / `missed_fill_opportunity_study.py`
from the orchestrator's candidate schema to the book's packet schema. That would give the owner his
standing forensics request **on the live armed book**.

### 4.2 The K55 ML shadow substrate is running with the model slot empty

`src/research_infra/k55_ml_shadow.py:37` sets
`DEFAULT_MODEL_REGISTRY_PATH = research/ml_program/shadow/k55_shadow_registry_2026-05-05.json`.
**That file does not exist in `origin/main`** [MEASURED] — the directory holds only a different
artifact (`K55_TARGET_FEATURE_REGISTRY_2026-05-05.json`). Meanwhile
`shadow_logs/ml_shadow_predictions.jsonl` is **77.4 MB** and the substrate has been running inside
`scripts/run_live_monitoring_maintenance.py:176,273` for months emitting
`MODEL_ARTIFACT_PENDING` feature bundles with **inference permanently disabled**. One JSON in the
`k55_shadow_linear_json_model_v1` schema turns a 77 MB feature ledger into a live scorer.
**Revival: ~1 hour.**

### 4.3 The learning stack: a feature store, 14 trained models, and no reader

- `research/ml_program/scout/feature_matrix.parquet` — **528 rows × 1,260 columns**, cutoff
  2026-04-28, 7 symbols. The feature store `CLAUDE.md` calls dormant-but-sound. Read by one script.
- `research/ml_program/scripts/features/{structure,volatility,microstructure,time_session,liquidity,regime}.py`
  — **1,247 features** across six families, catalogued in `feature_catalogs/CATALOG_v2.csv`. Only
  third-party dep is pandas. This is the "what is measurable about a candidate at the entry candle"
  library — axis (b), directly.
- `research/ml_program/models/**/*.lgb` — **14 trained LightGBM models**. **Nothing reads any of
  them**, and `lightgbm` is not installed. Caveat that matters: `k54_v4/final_verdicts.json` records
  **FAIL on all three architectures, 3/7 gates, `ship_arch: null`**. Dead as a primary classifier;
  **unevaluated as a shadow scorer** — which is what §4.2 needs.

### 4.4 "What did we turn down" — already answered, never written up

`research/rejected_candidates_value_mining/` (13 scripts). **From its own committed
`bucket_metrics.json`** [MEASURED]: 3,120 rejections forward-resolved;
`m15_choch_exists` n=125, WR **57.6 %**, E[R] **+0.44**, **+55 R left on the table**;
`blocked_limit` n=1,397, E[R] +0.053, **+74 R**; `no_qualifying_h1_poi` n=196, E[R] −0.324
(correctly rejected). `forward_resolution.jsonl` is **7,649 rows** with
`fwd_outcome/fwd_r/fwd_entry/fwd_sl/fwd_tp`. **There is no `.md` in the directory** — only JSON and
CSV, which is why it has never been read. Blocker on re-running the backtest arm is a one-line
Windows `ROOT` path. The live arm needs re-pointing at the current KB layout
(`knowledge_base/redacted_account_live_bee34003/trade_records/…`). **Revival: trivial to read the answer;
a session to re-point at the live book** — and that last version is the one the owner actually wants.

### 4.5 Live-vs-replay instruments that exist and are idle

- `docs/audits/.../outcome_authority/forward_shadow/shadow_parity_harness.py` — three modes, of
  which `--mode shadow-packets` **re-scores logged live packets through the committed research
  pipeline** and fails on any divergence. This is the mechanised form of hazard H7. Fixtures
  present. INFERRED runnable; note the forward-shadow lane is currently active, so check for overlap.
- `src/research_infra/divergence_matrix.py` — per-row replay-R vs live-R with a `transfer_verdict`;
  `verify_b7_5_post_acceleration_arm.py:1127` makes it a **required** input, so no arm can be
  accepted without a live-transfer statement. **Revival: trivial.**
- `src/research_infra/replay_differential_harness.py` (1,259 lines) — *where exactly, at row and
  field, do two sealed arms differ?* Discovers arm prefixes from disk rather than a module constant.
  Turns "S1R1 was negative" into "here are the rows where it diverged". Has tests. **Trivial.**
- `research/b_deep_audit_2026-04-19/phase3/_T3_scratch/simulate_live_gate.py` + `live_gate_sim.parquet`
  (**106,147 rows × 8 cols**) — does the live gate see the same OB the research event says exists?
  Pure numpy/pandas, root-clean. **Trivial.**
- `scripts/build_vnext_live_replay_gate_stack_audit.py` — gate-by-gate live/replay disagreement,
  plus `LIVE_OLD_SYSTEM_LEAKAGE_AUDIT.json`. Directly on the SECOND_AUDIT two-stacks finding.

### 4.6 Sealed-evidence machinery that needs no replay hour

- `research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/b7_5_cold_evidence.py`
  — streams any of the sealed ledgers in place; **298 `.jsonl.cold` shard dirs, 2.3 GB**, under
  `/Users/borr/GTOSActive/repo/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/`.
  Already imported by items 3 and by `replay_differential_harness`. **Trivial.**
- `verify_b7_5_post_acceleration_arm.py` — under R2 it sits in `verification_tooling`, which the
  enforcement loop does not read, so **extending it is free of the ~16.5 h re-seal** (H1). The
  cheapest place in the repo to add a new sealed-evidence question.
- `compare_broad_live_as_if_replay_runs.py` (1,970 lines) — compares two completed replay runs from
  artifacts on disk, no replay. **~1 hour.**

### 4.7 Instruments in `docs/audits/**/receipts/` worth reusing rather than rebuilding

- `phase7/receipts/ad_exit_sweep.py` — re-simulates exit variants from AA's **stored intents**, so
  minutes rather than a regeneration; `AD_ONLY=<sleeve>` supported; `AA_ESTATE_TRADES.json.gz`
  (1.26 MB) present. Population is the **sleeve estate**, so not redundant with F1.
- `phase6/receipts/aa_estate_walk.py` — the fixing machine, `run_gate(..., diagnose=True)`. Its
  output `REPAIR_QUEUE_V1.json` (747 KB) + `REPAIR_QUEUE_APPEND.jsonl` (476 KB) is the 134+49-row
  queue `CLAUDE.md` names — and **no script reads it as input**. It is a document where it should be
  a work list.
- `phase19/receipts/discovery/l1_lib.py` + `l1_build_touch_index.py` — recompute **any**
  (target, stop) exit cell in O(1) under three fill conventions, an 18 × 10 first-touch surface.
  **BROKEN**: `l1_TOUCH_INDEX_V1.jsonl.gz` and its input `w0cap2_DECISION_ANCHOR_V1.jsonl.gz` were
  never committed, which kills all 15 `l1_*` consumers. **Fix: ~1 hour** — rebuild the anchor from
  the live CQ sidecar, then re-run the index builder. Worth it: F1's ladder is 9 fixed take-profits;
  this is the full 2-D surface.
- `professional_review/build_outcome_diagnostic_census.py` — *of the candidates we rejected, which
  were right?* **Zero references**; emits `OUTCOME_DIAGNOSTIC_PROMISING_REJECTS_540.jsonl`
  (present); all sha-pinned inputs present. **Trivial**, and 540 promising rejects is a population
  nobody is walking.
- `professional_review/build_far_side_unchosen_reference_downstream_census.py` — for the 1.5 R
  reference we did **not** choose, did price close through its far side anyway? **Zero references.**
- `postmortem/pm_lifecycle_shape.py` — when the system refused the top candidate because the symbol
  was already occupied, what did the refused candidate do and how did the occupier die?
  Opportunity-cost of the system's own occupancy rule; cache alive. **~1 hour.**
- `postmortem/pm_ranking_health.py` — realised mean net by decile of the model's own prediction, per
  month; the only decile-calibration instrument in the estate, and a **monitorable** quantity.
- `phase8/receipts/ah_entry_attribution.py` — separates a genuine entry-timing saving from the cost
  model charging the exit leg at the entry instant. A correction the in-flight lanes will need.
- `phase6/receipts/ag_mx_pilot_banded.py` — re-runs a verdict at the spread its own quarter actually
  had rather than a 37-day 2026 snapshot. The standing repair for AA's acknowledged cost
  look-ahead; nothing in flight applies it.
- `swarm/lane_i_receipts/scripts/part1_information.py` (read via `git show origin/main:`) — the
  capacity ladder: do the 43 predecision features contain **any** out-of-sample information about
  terminal net R? Inputs alive (`/tmp/lane_i/pop.parquet`, 125 MB). Bounds what is knowable at entry
  — axis (b) at its most fundamental.
- `opus5-architecture-20260725/receipts/wallsampler.py` — a general 151-line statistical profiler
  (~1–2 % overhead, no cProfile distortion). Not forensics; the throughput instrument for "replay at
  scale".

### 4.8 Two more that run today with no unblock at all

- **`scripts/intra_candle_missed_setups.py`** — *how many setups form and resolve inside a single
  M15 candle, i.e. the population the M15 cadence structurally cannot see.* **MEASURED: I ran it end
  to end, exit 0**, on `data/historical/XAUUSD_{M1,M5,M15,H1}.csv` which are present. Result over
  2025-12-18 → 2026-04-02 (99,999 M1 candles, 9,337/9,532 M5 swings, 628 H1 OB zones):
  **OB touch + rejection 535 total / 155.1 per month; sweep + displacement + pullback 124 / 35.9 per
  month; flash displacement 1.** Note it has **no argparse — it executes on import/`--help`** and
  writes to a stale path under `research/archive/root_legacy_artifacts_2026_05_29/generated/`;
  redirect it. **Trivial.**
- **`scripts/analyze_prescreen_kills.py`** — *on every day the D1/H4 pre-screen killed before the AI
  ran, did a valid `ob_retest` actually exist in the kill zone?* One of very few items needing no
  sparse-add; all six `data/historical/XAUUSD_*.csv` present. **Trivial.**

---

## 5. Results already computed that nobody has read

Cheaper than re-running anything. All tracked in `origin/main`, most un-checked-out.

- `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/` (151 files):
  `WAVE2_ENTRY_PATH_MAE_MFE_TTD_CAUSAL_LEDGER.jsonl`,
  `WAVE2_EXECUTION_ENTRY_PATH_MAE_MFE_TIME_LEDGER.jsonl`,
  `WAVE2_BAD_MARKET_VS_BAD_SYSTEM_LEDGER.jsonl`,
  `WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl`,
  `WAVE2_COUNTERFACTUAL_DECISION_LEDGER.jsonl`, `WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl`,
  `WAVE2_CANDIDATE_FUNNEL_QUALITY_METRICS.json`.
- `research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_CANDIDATE_REJECTION_VALIDITY_LEDGER.jsonl`
  — "was the rejection right", already computed.
- `research/operations/final_moonshot_wave1a_hard_halt_forensic_matrix_2026_06_04/MFE_MAE_TIME_IN_TRADE_LEDGER.jsonl`.
- `research/operations/vnext_lane07_market_coverage_source_starvation_repair_2026_05_31/LANE07_24_SYMBOL_OPPORTUNITY_FUNNEL_LEDGER.jsonl`.
- `research/science_program_2026_05/.../weekend_mechanical_edge_factory_moonshot_2026_05_15/…LOCAL_BROKER_SOURCE_REPAIR_EXPECTANCY_REPAIR_RESULT_LEDGER_2026-05-17.jsonl`
  — **17,753 rows × 48 cols, 67 MB** of row-level claimed-R vs broker-exact-R reconciliation with
  `exact_missing_field_proof`. Axis (c) at row granularity; only two `.py` survive in-route and
  neither reads it.
- Present on disk here already:
  `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl`
  (77 rows) — and note its `mfe_r`/`mae_r` are **null** with `missing_fields` naming them. The
  excursion layer was scaffolded and never filled, by
  `scripts/build_wave3_profit_harvest_mfe_capture_v4.py`, whose one missing input
  (`WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl`) is in `origin/main` and un-checked-out. That is
  a **trivial** fix to a visibly half-finished job.

---

## 6. Orphaned data assets (exist on disk; nothing reads them)

| asset | size | note |
|---|---|---|
| `/Users/borr/GTOSActive/repo/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/*.jsonl.cold/` | **2.3 GB**, 298 shard dirs | 29 ORDERED_PATH_ORACLE, 29 MISSED_OPPORTUNITY, 32 DECISION, 29 SCORECARD, 28 TRADE, 28 ORDER … |
| `/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/…/` (same route) | **6.2 GB** | the *producing* worktree — the only place all four January arms live; every B7.5 default path resolves here |
| `…/attempt_5_typed_sparse/PHASE_D_APRIL_S1R1_R1_20260725T070249Z/` | **501 MB** | April's 15 sealed days, economically uncreditable, forensically intact |
| `LANE16_SOURCE_GAP_LEDGER.jsonl.gz` | **195.1 MB** | why each candidate's truth could not be reconstructed, by gap family |
| `LANE16_MICROSCOPE_EVENT_LEDGER.jsonl.gz` | **49.0 MB** | per-event microscope over the 289,928 population |
| `vnext_absolute_moonshot_scheduler_v3_2026_06_01/*.jsonl.gz` (7 files) | **178.1 MB** | FULL_EVIDENCE 36.5, SOURCE_GAP 29.4, ACCEPTED_REDUCED_REJECTED 25.6, MONEY_RISK 25.0, CONFLICT_ANATOMY 23.8, CORRELATION_CLUSTER 23.1, BLOCKED_EDGE 14.7 |
| `shadow_logs/ml_shadow_predictions.jsonl` | **77.4 MB** | every row inference-disabled — see §4.2 |
| `research/ml_program/models/**/*.lgb` | 14 models | nothing reads them; lightgbm not installed |
| `research/diagnostics/zone_age_analysis/ob_zone_age_events_v1.json` | **40.0 MB** | regenerable only after an `exports/` re-export |
| `research/rejected_candidates_value_mining/{rejected_rows_bucketed,forward_resolution,rejected_rows}.jsonl` | 28.1 MB | see §4.4 |
| `research/ml_program/audit/q2_correlation_matrix.csv` | **12.75 MB** | cross-family feature correlation |
| `knowledge_base_backtest/analysis/*displacement_database*.csv` | ~65 MB | 5 instruments × 3 runs, ~90 features + outcomes |
| `phase16/receipts/CK_D2_SERIAL_CANDIDATE_V1_ECONOMICS.json` | **9.6 MB** | exactly 1 reference — itself |
| `phase19/receipts/pools/LP_{june,august,september,october,november,december}_2025_S0R0_POOL_V1.jsonl.gz` | ~50 MB | **three carry `.READ_RESTRICTED` sidecars (june, august, september) — held-out; do not spend** |

---

## 7. Dead — do not dispatch work at these

- **`scripts/build_gtos_vnext_*_runtime_rows.py`, ~70 files** — closed 2026-05 conversion
  bookkeeping. *Exception:* `build_gtos_vnext_rejected_candidate_l2_value_mining_runtime_rows.py`
  (595 lines) is real analysis.
- **`scripts/analyze_lane{1..7}_*_triage.py`, 12 files** — a backlog superseded by `THIRD_REVIEW.md` §4.
- **`scripts/analyze_orderflow_*` (7), `audit_orderflow_*` (7), `audit_sierra_*` (4),
  `build_orderflow_*` (4)** — all `NO_PROMOTION_VERDICT`, blocked on Databento/Sierra data never
  purchased. Blocked at source, not code.
- **`scripts/analyze_raw_ohlc_path_scaling_v*` (6), `analyze_truth_layer_*` (4)** — re-ranking a
  fixed frozen pool, the closed dead end.
- **`analyze_b7_5_selection_sizing_matrix.py`** — a depth-6 find over all of `/Users/borr/GTOSActive`
  returns **zero** matching June artifacts. Inputs gone; its output audit is banked.
- **Hardcoded foreign roots:** `scripts/research/{dsr_audit,q1_dlinear_baseline,c1_coval_shumway_audit}.py`
  point at `C:/Users/MSI/Documents/ai-trading-agent`; `scripts/smc_a{1,2,3,5}_*.py` point at
  `/Users/borr/Documents/trading/gold-agent`, which does not exist. **`dsr_audit.py`,
  `q1_dlinear_baseline.py` and `c1_coval_shumway_audit.py` have no argparse and execute on
  `--help`** — see §8.
- **Model-bakeoff era, superseded:** `opus_regular_full_86.py`, `test_opus_*`, `test_sonnet_*`,
  `vision_comparison.py`, `reprocess_batch.py`, `full_86_model_comparison.py`,
  `comprehensive_analysis.py`, `confidence_decomposition_test.py`.
- **`scripts/session9_task{1..5}*.py`** — no `__main__` guard, one-shot yfinance/CFTC pulls.
- **Not trading:** `scripts/quantlabs_*.py`.

---

## 8. Method notes, corrections, and two incidents

**Corrections to sub-lane claims, made after direct measurement:**

1. `LANE16_PATH_ANATOMY_LEDGER`'s `missed_opportunity` and `correct_rejection` fields were reported
   as usable. Measured over all 289,928 rows they are true on **1** and **3** rows respectively.
   The MFE/MAE/`path_class` census is sound; those two fields are not.
2. The `ORDERED_PATH_ORACLE` ledger was reported to carry a
   `high_fill_unfilled_probe_counterfactual_*` field family. Measured on the January S0R0 raw
   ledger: that family **does not exist**. What is there is `mfe_r`, `mae_r`, `mfe_time_utc`,
   `mae_time_utc`, an `exit_composition_profit_harvest_counterfactual_*` pair, and a rich
   `limit_first_*` fill-realism family (`limit_first_entry_fill_executable`,
   `limit_first_entry_first_touch_utc`, `limit_first_fill_realism_class`, …) which **is** the
   "would the limit have filled" question. Also: that raw file is **91 rows / 1,189 fields**, not a
   large population — the large populations are in the `.cold` shards.
3. `w0_ws.load()` returns **128** columns, not 130.

**Two working-tree incidents, both reverted by this lane:**

- A sub-lane ran `scripts/research/dsr_audit.py --help`; the script has no argparse and executed,
  creating a literal `C:/` directory at the repo root from its hardcoded Windows path. Verified
  untracked, contents were a single `dsr_diagnostics.json`, **removed**.
- This lane's own run of `scripts/intra_candle_missed_setups.py` created
  `research/archive/root_legacy_artifacts_2026_05_29/`. Output copied to scratch, directory
  **removed**. `git status --porcelain` is clean of both.

**Sampling disclosure.** The mechanical orphan index is exhaustive over `scripts/` + `src/`
(1,146 modules; 138 with zero external references). `research/operations/` (488 py) and
`research/science_program_2026_05/` (1,629 py) were triaged at directory level with 2–3 artifacts
named per interesting route — not file-by-file. `docs/audits/` (1,180 py) was triaged by phase and
filename against the four value axes. Execution was attempted on the top candidates only; every
other runnability judgement is input-resolution plus `ls` and is labelled INFERRED.

**Machine-readable index:** `g1_inventory/G1_INVENTORY_V1.json`.
