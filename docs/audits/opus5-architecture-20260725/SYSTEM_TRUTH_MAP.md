# GTOS System Truth Map

**Reconstructed from source at `a3badc054` (audit branch `audit/claude-opus5-architecture-20260725`), 2026-07-25.**
Every claim carries a `file:line`. Where a claim is inference rather than direct observation it is labelled **[INF]**. Where it is a hypothesis awaiting proof it is labelled **[HYP]**.

---

## 0. Scale

| Surface | Files | Lines |
|---|---:|---:|
| `src/` | 590 | 502,487 |
| `scripts/` | 417 | 289,803 |
| `tests/` | 593 | 419,264 |
| `research/**/*.py` | 37 | 120,120 |
| **Total Python** | **1,637** | **1,331,674** |

Single largest module: `src/research_infra/v4_timewarp_simulated_live_research_loop.py` — **96,047 lines**, 595 top-level `def`, 16 classes, 144 nested `def`. Its test is 63,745 lines. The largest verifier, `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`, is 37,015 lines.

**Code lives in four places** — `src/`, `scripts/`, `tests/`, and inside evidence route directories under `research/operations/<route>/`. The fourth location holds 120k lines including the production parity builder and verifier.

---

## 1. The two systems

The single most important structural fact about GTOS is that **it is two different systems that share a candidate generator.**

```
                       ┌──────────────────────────────────────────┐
                       │  SHARED (genuinely common code)          │
                       │  • data_ingestion.ingest_live_data       │
                       │  • market_state.compute_market_state     │
                       │  • broader_origin_generators             │
                       │      .generate_live_broader_origin_…     │
                       │  • execution_manager_v4                  │
                       │  • same_symbol_lifecycle_v4              │
                       │  • dynamic_target_stop_geometry_v4       │
                       │  • exit_policy_v4                        │
                       │  • broker_net_cost_engine                │
                       └───────────────┬──────────────────────────┘
                                       │
        ┌──────────────────────────────┴───────────────────────────────┐
        │                                                              │
┌───────▼────────────────────────────┐        ┌─────────────────────────▼──────────────┐
│ LIVE                               │        │ REPLAY                                 │
│ run_book.py  ← NOT IN THIS REPO    │        │ b7_5_post_acceleration_runner.run-arm  │
│  → ultimate_book/launcher.py:199   │        │  → attempt5._run_typed_sparse_attempt5 │
│  → book_owner.py:712 run_cycle     │        │  → v4_timewarp…:90455 run_campaign     │
│  → order_router.py:75              │        │                                        │
│  → execution.py:3080 open_trade    │        │  per 24-symbol decision window:        │
│  → execution.py:6620 safe_place…   │        │   evaluate_candidate_v4      :67389    │
│  → mt5_real.py:362 order_send      │        │   materialize_scheduler_window:78014   │
│                                    │        │   allocate_decision_window  SCHED:27866│
│ SELECTION: first-wins per process  │        │   finalize_scheduler_risk_…  :44810    │
│   orchestrator.py:1322-1327        │        │   build_runtime_risk_authority:36568   │
│ SCHEDULER: telemetry only          │        │   simulate_order             :85822    │
│   orchestrator.py:3504             │        │                                        │
│   "runtime_effect_now": False      │        │ SELECTION: portfolio allocator over    │
│ SELECTOR V4: zero callers          │        │   all 24 symbols, cluster caps,        │
│ SIZING: execution.py:9080          │        │   pending replacement, re-ranking      │
│   _calculate_lots → broker lot     │        │ SIZING: continuous units               │
│   step, min-lot REJECT :3396       │        │   risk_cash / |entry−stop|  :6497      │
└────────────────────────────────────┘        └────────────────────────────────────────┘
```

**Consequence.** Replay measures the return of a portfolio-optimal, selector-filtered, scheduler-throttled strategy. The live system implements none of those three stages. Any R statistic transferred from replay to production carries that gap, and no receipt in the evidence tree measures it.

---

## 2. Live path — source to broker

| # | Stage | Site |
|---|---|---|
| 1 | supervisor launches one book per account | `scripts/run_book_supervisor.ps1:86-108` |
| 2 | **entrypoint** | `run_book.py` — **absent from HEAD**; `git ls-files` returns only `scripts/run_book_supervisor.ps1` and `tests/test_run_book_account_identity.py` |
| 3 | loop | `src/components/ultimate_book/launcher.py:199 BookLauncher.tick()` |
| 4 | cycle | `src/components/ultimate_book/book_owner.py:712 run_cycle(place=…)` |
| 5 | route | `src/components/ultimate_book/order_router.py:75-82` |
| 6 | open | `src/components/execution.py:3080 open_trade` → halt guard `:3109` → entry price from live tick `:3169` → request `:3455-3468` |
| 7 | send | `src/components/execution.py:6620 safe_place_order` → `:6710 executor.submit(self.mt5.order_send, request)` |
| 8 | **transmit** | `src/mt5/mt5_real.py:362 self._mt5.order_send(request)` |

A parallel legacy fleet exists: `start_all.bat:121-167` launches 24 `run_agent.py --symbol X` processes → `src/components/orchestrator.py:811 run`. `run_agent.py:37-48` refuses to start when a `run_book.py` process is alive — but the guard is wrapped in `except Exception: pass`.

**Single transmission chokepoint:** `src/mt5/mt5_real.py:362`. Reachable from `execution.py:6710` (guarded) and from `execution.py:9744, 9785, 9863, 9904` (SL/TP modify, which bypass `safe_place_order`).

---

## 3. Replay path — sealed arm, end to end

```
b7_5_post_acceleration_runner.py:2359 main
 └ :2375 run_sealed_arm
    ├ :2217 validate_execution_seal          ← decision contract + arm fingerprint
    ├ :2222 validate_args_against_execution_seal
    │        requires window.start/end == sealed month            :1399-1400
    │        requires resolve(pack.authority_path) == arg path    :1431-1434
    ├ :2224 replay.configure_runtime_evidence_root(/Users/borr/GTOSActive/repo)
    ├ :2227 bind_fresh_source                ← absolute-path binding, :863-890
    ├ :2240 replay.run_replay_engine(args)
    │   └ attempt5:18162 own_campaign_exact_caches()
    │      └ attempt5:15455 _run_typed_sparse_attempt5   (2,700 lines)
    │         ├ :15680 RealReplaySourceAccelerator.from_accepted_bundle   (typed cache)
    │         ├ :16056 prewarm_sparse_tick_sources        (4 workers)
    │         ├ :16096 BroadSourceResolver                (1,422 lines, 4 caches)
    │         ├ :16654 CampaignExactCache.from_config
    │         ├ :16772 PreparedDayPackReader              (sealed per-day pack)
    │         ├ :16794 ReplayCompactEventSink             (proof spill)
    │         └ :16842 run_campaign(...)                  ← ECONOMIC HOT PATH
    └ :2290 write B7_5_POST_ACCELERATION_ARM_RECEIPT.json
```

### 3.1 The chronological reducer

`v4_timewarp_simulated_live_research_loop.py:90455 run_campaign`, 3,644 lines.

```
for day in campaign.days                                     :90524
  account.ensure_day(day)                                    :90537
  for asof in clock.decision_times_for_day(day)              :90550   ← THE REDUCER
    account.process_events_until(until=asof)                 :90558 → :2536 (996 lines)
    open_snapshot(asof) / pending_snapshot(asof)             :90611-90612
    for symbol in INCLUDED_SYMBOLS (24)                      :90626   hydration
      live_replay.snapshot(symbol, asof)                     :90696 → compute_market_state
    for symbol in INCLUDED_SYMBOLS (24)                      :90776   generation + evaluation
      decision_core.generate_candidates(...)                 :90812
      evaluate_symbol_candidates_with_batched_proof_hashes    :90952 → :67852
        └ evaluate_candidate_v4                              :67389 (446 lines)
    decision_core.schedule_window(...)                       :91438 → materialize_scheduler_window :78014
    finalize_scheduler_risk_admitted_selection(...)          :91641 → :44810 (8,750 lines)
        └ per ranked option: build_runtime_risk_authority    :49568 → :36568 (5,065 lines)
    for candidate in all_candidates (missed-opportunity)     :92410 / :92811
    for selected_instance_key in sorted(selected_key_set)    :93202   ← ALPHABETICAL, not by rank
      simulate_order(...)                                    :93306 → :85822 (4,286 lines)
        └ build_runtime_risk_authority  RECOMPUTED           :85868   (flag set :85879)
        └ path_source_and_oracle × up to 3, NO query_cache   :86721, :87104, :87516
```

**Five functions hold 27,700 lines (28.8% of the module):** `finalize_scheduler_risk_admitted_selection` (8,750), `build_runtime_risk_authority` (5,065), `simulate_order` (4,286), `materialize_scheduler_window` (3,958), `run_campaign` (3,644).

`evaluate_candidate_v4` and `materialize_scheduler_window` (4,404 lines of the most important domain code) have **no direct call site** — they are injected as function references at `:90494-90499`. Every static call-graph tool reports them dead.

### 3.2 Boundaries and identity

| Boundary | Producer | Consumer | Identity | Carried? |
|---|---|---|---|---|
| bars → candidate | `broader_origin_generators.py:251`, id at `:1889` | `v4_live_replay_decision_core.py:136` | `broadorigin_<sha256[:24]>` | carried, **not unique** — POI-anchored ids omit time (`:1860-1866`) |
| candidate → V4 packets | `selector_v4.py:3543` → `:3409 to_record()` | `v4_timewarp…:78014` | side-dict lookup `:28453` | reconstructed |
| candidate → allocation | `SCHED:27866 allocate_decision_window` | `v4_live_replay_decision_core.py:205` | `f"{candidate_id}@@{decision_time_utc}"` | reconstructed at 5 independent sites (`SCHED:27896`, `SCHED:6290`, `ultimate_candidate_package.py:1946`, `v4:28343`, `SCHED:10976`) |
| allocation → finalizer selection | `v4:44810` | `v4:91664` | same `@@` concat | reconstructed; **the scheduler's own selection is discarded** (`pre_risk_finalizer_scheduler_packet` `:91610`) |
| selection → sized order | `v4:36568` (again at `:85866`) | `v4:85822` | probe by `risk_finalizer_probe_by_id[key]` `:93280` | reconstructed; missing probe → hard reject `:93289` |
| order → pending | `v4:86514` mints `order_id` | `v4:2536` | `simulated_order_id` | **carried** |
| pending → position | `v4:2638-2755` | `v4:1726 open_snapshot` | `simulated_trade_id` | carried |
| position → resolution | `v4:2900-3040` | `v4:34975` reads `closed_trades` back into the decision path | `simulated_trade_id` | carried, **closes a feedback loop** |

No object is carried end-to-end. Identity collisions are handled by **dropping the candidate** (`:91427-91435`, `:93231-93243`).

---

## 4. Authority and data lineage

```
config/agent_config.yaml
   └ apply_profile_overrides(profile)        src/utils/config.py:158-180
        └ apply_instrument_overrides(symbol)  src/utils/config.py:92-142
             └ merges instruments.<sym> over the CONFIG ROOT   :123   ← priority inversion
   ├ LIVE  risk: config/profiles/redacted_account.yaml
   │        …but the live book actually sizes from a Python constant:
   │        ultimate_book/admission.py:775 ALLOCATION_PROFILES[…].risk_per_unit = 0.020
   └ REPLAY risk: config/agent_config.yaml:3160
             timewarp_replay_risk_profile_path: "config/profiles/ftmo.yaml"

env (never sealed):  GTOS_PROFILE · GTOS_UB_DERISK_MODE · GTOS_DUAL_BROKER_INTENT_ENABLED
                     — each overrides YAML and changes economics

outside the checkout (read-only, unversioned in this branch):
  /Users/borr/GTOSActive/repo/research/operations/…/SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl
  …/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl
  …/RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json
  …/WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl
       bound at replay_acceleration_attempt5_typed_sparse_runner.py:351-450
       root pinned at :186  ATTEMPT5_RUNTIME_EVIDENCE_ROOT = /Users/borr/GTOSActive/repo
```

**Effective replay-vs-live per-symbol risk, measured over the 24-symbol replay surface** (`GTOS_24_SYMBOL_SURFACE`, `v4:251-278`):

| Symbol | live (redacted_account) | replay (ftmo) | replay/live |
|---|---|---|---|
| NAS100 | 0.25 % | 0.50 % | **2.00×** |
| US30_cash | 2.00 % | 1.00 % | **0.50×** |

(22 of 24 agree. Seven replay-surface symbols are absent from `ftmo.yaml` and fall back to the 2.0 % base, which happens to equal the live value.)

---

## 5. Proof and evidence lineage

One accepted arm (Phase D January S1R1) produces:

| Ledger | Rows | Logical bytes | Bytes/row |
|---|---:|---:|---:|
| missed opportunity | 154,316 | 7,595,615,841 | 49,222 |
| decision | 69,888 | 4,062,951,201 | 58,135 |
| scorecard | 2,016 | 3,914,869,623 | **1,941,900** |
| order | 148 | 77,535,353 | 523,887 |
| trade | 72 | 38,347,402 | 532,603 |
| ordered path oracle | 74 | 18,966,280 | 256,301 |
| bucket | 8,492 | 35,173,588 | 4,142 |
| source universe | 867 | 3,068,029 | 3,539 |
| **total** | | **≈ 15.75 GB** | |

Source: `PHASE_D_JANUARY_S1R1_R1_20260724T195321Z/B7_5_POST_ACCELERATION_ARM_RECEIPT.json` → `artifact_inventory.artifacts`.

**15.75 GB of JSON to produce 148 orders and 72 trades — 218 MB of evidence per trade.**

Chain of custody for that arm:

```
FRESH_CURRENT_BUNDLE_AUTHORITY.json ─(sha + ABSOLUTE PATH)→ JANUARY_EXECUTION_SEAL_R3.json
                                                              │
       PHASE_D_JANUARY_ARM_NEUTRAL_PACK_R4/prepared-day-packs │ (31 pack roots, sha-bound)
                                                              ▼
                                            B7_5_POST_ACCELERATION_ARM_RECEIPT.json
                                              (self-hash over its OWN 11 artifacts)
                                                              ▼
                          JANUARY_S1R1_ARM_INDEPENDENT_POST_COLD_VERIFICATION.json
                                              (same root, after cold demotion)
                                                              ▼
                                   JANUARY_FOUR_ARM_MATRIX_ACCEPTANCE.json
```

Every link above is cryptographic **except** the one that matters most for scientific validity: there is no link binding a January arm's economic rows to an independently produced reference. The only semantic-parity artifact in the campaign is for **one day (2026-06-04), one arm (S1R1), 9,959 rows** — `PHASE_C_JUNE4_S1R1_R5_20260723T095937Z/B7_5_POST_ACCELERATION_SEMANTIC_PARITY.json`.

### What the parity comparator actually does

`b7_5_post_acceleration_semantic_verifier.py:1689-1761`, tolerance **zero** (byte equality of canonical JSON), with a **38-entry allowlist** (`allowlist_root_sha256 = b75bf513…`) covering only wall-clock timestamps and derived hashes. On the one real parity run:

| role | rows | rows with allowlisted differences |
|---|---:|---:|
| decision | 2,304 | 0 |
| bucket | 416 | 0 |
| scorecard | 96 | **96 (100 %)** |
| order | 10 | **10 (100 %)** |
| trade | 5 | **5 (100 %)** |
| oracle | 5 | **5 (100 %)** |
| missed | 6,976 | **6,976 (100 %)** |

"Zero meaningful differences" is entirely a statement that the 38-entry allowlist is correct and complete.

---

## 6. Where the time goes

Measured from the four sealed January arm summaries (`progress_rows`, 31 days each):

| Arm | economic hot path | proof finalization | total | active days (≥10 s) | mean active day |
|---|---:|---:|---:|---:|---:|
| S0R0 | 11,232.1 s | 462.8 s | 3.25 h | 21 | 534.1 s |
| S1R0 | 12,967.4 s | 597.7 s | 3.77 h | 21 | 616.6 s |
| S0R1 | 12,336.7 s | 676.5 s | 3.61 h | 21 | 586.6 s |
| S1R1 | 11,929.1 s | 547.2 s | 3.47 h | 21 | 567.2 s |

The 10 non-trading days cost **1.7 s each** in the economic path. The "no-event day ≤ 5 s target missed at 52.5 s" recorded in `TASK9_FINAL_ACCELERATOR_ACCEPTANCE.json` is an *allocated envelope*, not economic work: measured directly in this audit, fixed per-process startup (source authority validation + typed-cache bind + 4-worker sparse-tick prewarm + resolver construction) is **63.0 s wall / 109.0 s CPU** before the first decision.

Per active day: ~7,350 candidates evaluated in ~570 s = **77 ms per candidate**, producing ~855 MB of JSON. Measured `json.dumps` throughput on the real rows is 190–250 MB/s and `sha256` 2,300 MB/s, so **serialization accounts for ~0.7 % of the day**. The cost is the computation that fills 1,274-key rows, not the writing of them.

---

## 7. Structural facts that shape everything else

1. **An order row is 494,196 bytes with 1,274 top-level keys and 8,091 scalar leaves — of which only 765 are distinct values. 63.8 % of the row (315,449 bytes) is JSON key names.** The row is a flattened union of every intermediate structure, with the same subtrees emitted at several paths (`risk_authority.package_marketable_entry_guard_replay_route` is also a top-level key; `package_displacement_quality` is written into two dicts at `SCHED:14693-14694`).
2. **`build_runtime_risk_authority` (5,065 lines) runs twice per selected order** — once per ranked option in the finalizer (`:49568`) and again in `simulate_order` (`:85868`). The code records this: `"runtime_risk_authority_recomputed_for_order_materialization": True` (`:85879`).
3. **The execution-critical tick lookup is uncached; the diagnostic one is cached.** `path_source_and_oracle` at `:86721`, `:87104`, `:87516` passes no `query_cache`; the missed-opportunity sites at `:92464`, `:92880` do.
4. **`verify_route` (`:95970`) re-reads from disk everything `build_route` just wrote** — 44 `load_json`/`load_jsonl` calls at `:95205-95961`; the order ledger is parsed 5 times.
5. **No sub-window replay is possible.** Three independent assertions force a full sealed month: window equality (`b7_5_post_acceleration_runner.py:1399-1400`), pack-root set equality (`attempt5:16228-16231`), and source-plan digest equality over the selected day set (`attempt5:16476-16487`). Debugging one day of a 3.5-hour arm requires re-running the arm.
6. **Sealed authority binds absolute filesystem paths.** Demonstrated empirically in this audit: byte-identical copies of the January evidence in a second worktree are rejected with `fresh_source_authority_path_binding_mismatch` (`replay_acceleration_fresh_source_authority.py:309`). Two module constants pin machine-specific paths: `attempt5:186` `/Users/borr/GTOSActive/repo` and `attempt5:187-190` `/Users/borr/Documents/gtos/repo/ai-trading-agent/…`.
7. **45 % of the acceleration stack is unreachable from the production entrypoint** — 35,019 of 78,331 lines, including all eight genuinely independent verifiers.
8. **`.hermes/replay-accel-status.json` — the accepted-evidence index — has a dangling entry**, and Task 9's bound validation namespace (`TASK9_FINAL_VALIDATION_R2_20260723T031200Z`, 437 files) is absent from disk. Nothing detects either.
