# GTOS Mismatch and Risk Register

**Audit:** independent architecture / correctness / simplification, `a3badc054`, 2026-07-25.
Ranked by *practical consequence*, not by how alarming the name sounds.

**Legend.** `Cat` = category (CORRECTNESS · AUTHORITY · REPLAY/LIVE · PERF · COMPLEXITY · DEAD · PROOF · OPS).
`Conf` = confidence: **[F]** fact I verified directly, **[V]** verified by a subagent with file:line I spot-checked, **[INF]** inference, **[HYP]** hypothesis.

---

## Tier 0 — invalidates conclusions currently being drawn

### R1 · REPLAY/LIVE · The replay measures a system the live path does not implement
**Conf [F]/[V].**

| Stage | Live | Replay |
|---|---|---|
| cross-candidate selection | `orchestrator.py:1322-1327` — first candidate that places wins; one symbol per OS process (`start_all.bat:121-167`) | `moonshot_scheduler_v4_best_trade_allocator.py:27866 allocate_decision_window` — ranks all 24 symbols in one window under cluster and portfolio caps |
| Selector V4 admission | `selector_v4.py:3543 evaluate_selector_v4_admission` — no production caller; the only bridge (`gtos_vnext_runtime.py:15194`) is itself uncalled | called at `v4_timewarp…:67522`, `:67580` |
| Scheduler V4 | telemetry: `orchestrator.py:3504` stamps `"runtime_effect_now": False`; `permissions.py:930 _reject_if_scheduler_v4_not_selected_authority` returns `None` because `_scheduler_v4_required` (`permissions.py:655-666`) needs `scheduler_v4_…_live_activation_allowed`, which is `false` at `config/agent_config.yaml:963` | the allocator is the decision authority |
| sizing | `execution.py:9080 _calculate_lots` → broker lot step (`:2323 _normalize_volume`) → **reject below min lot** (`:3396-3401`) | continuous `risk_cash / abs(entry-stop)` (`v4:6497`) |
| entry | market order at the tick *after* the M15 close confirms the touch (`execution.py:6040-6043` → `:6550` → `:3169`), then SL distance re-anchored to that price (`:3182`) | fill at the tick that touched the limit (`v4:63193`) |
| pending lifetime | 48 h wall clock (`execution.py:5975`) | `min(asof + 120 min, end of day)` (`v4:85864`, `PENDING_EXPIRY_REPAIRED=120` at `v4:377-378`) |
| exit management | real broker orders with retries, requotes, deal confirmation (`execution.py:7935, 8386, 7505, 7536, 8705`) | lossless R-space bar walk, instantaneous partial closes (`dynamic_execution_policy.py:335` via `v4:61216`) |

**Adversarial correction (accepted).** Two qualifications the first pass missed:
1. **`ultimate_book` *does* implement cross-candidate selection.** `src/components/ultimate_book/admission.py:1275-1295` sorts by descending conviction and sheds the lowest-conviction units against a gross-risk cap, reached via `admit_and_size` (`:1298`) ← `bridge.py:226` ← `book_engine.py:481` ← `book_owner.py:723`. **But it is unwired at HEAD**: `BookLauncher`/`UltimateBookOwner` have no instantiation outside `tests/`, and their entrypoint `run_book.py` is not tracked (R4). Worse, the book path does not call the selector or scheduler — it **fabricates their packets**: `ultimate_book/execution_packets.py:323-332` hardcodes `"gtos_vnext_selector_v4_action": "trade"` and `"gtos_vnext_scheduler_v4_selected_action_class": "execute_now"` so the execution-manager field check passes.
2. `orchestrator.py:3504` is the wrong line — it is `:3502`, and it sits in the `except` fail-closed branch. The always-`False` stamp that actually matters is `moonshot_scheduler_v4_best_trade_allocator.py:28022-28026`, applied at `:28117`. The conclusion is unchanged.

**Current behaviour vs intended.** The evidence tree treats replay R as a forecast of live R. It is not: it is the return of a portfolio-optimal, selector-filtered, scheduler-throttled, continuously-sized, perfectly-executed strategy.
**Root cause.** Two decision cores were built at different times against different constraints, sharing only candidate generation. Nothing enforces the equivalence the naming implies.
**Falsified if:** someone shows `evaluate_selector_v4_admission` or `allocate_decision_window` on a live call path, or shows `run_book.py` performing cross-symbol allocation.
**Smallest fix.** Publish the divergence matrix as a first-class artifact next to every arm receipt, and stop reporting replay R without it.
**Strongest fix.** One decision core with an injected `Broker` and `Clock` port (see `TARGET_ARCHITECTURE.md` §2). Replay and live differ only in the port implementations.
**Interaction with gates.** Directly qualifies the January four-arm result and the whole B7.5 programme. It does not invalidate the *arm contrast* (all four arms share the same replay semantics), but it does invalidate any absolute transfer to production.

---

### R2 · PROOF · No sealed Phase-D arm has a semantic parity proof
**Conf [V] — adversarially verified, claim narrowed.**

*Correction accepted:* the original phrasing ("only the June S1R1 single day has one") overstated the gap. A genuine legacy-vs-accelerated **January** comparison does exist at Task-2 scope — `.hermes/receipts/task2/task2-semantic-equivalence-20260722T113411Z/TASK2_SEMANTIC_EQUIVALENCE_VERIFICATION.json`, Jan 1–7 and Jan 1–2, arm **S0R0**, against `LEGACY_ROOT = .hermes/evidence/task2/latest-golden-20260721-r2/successor-namespace`. It is real evidence. It is **not** evidence about the sealed `PHASE_D_JANUARY_*` R3_CAP_R2 arms: different arm fingerprint (`2ece240b…`), different source authority, different contract.

The accurate statement is: **no sealed Phase-D arm — January or April — has a semantic parity proof.**

`git ls-files 'PHASE_D*'` plus a filesystem sweep of the active worktree finds `B7_5_POST_ACCELERATION_SEMANTIC_PARITY.json` **only** under `PHASE_C_JUNE4_S1R1_R5_20260723T095937Z` — one day (2026-06-04), one arm, 9,959 rows. Every January and April arm carries only `B7_5_POST_ACCELERATION_ARM_RECEIPT.json`, which is a self-hash inventory of that arm's *own* 11 artifacts (`artifact_inventory.inventory_root_sha256`), plus `*_ARM_INDEPENDENT_POST_COLD_VERIFICATION.json`, which re-hashes the same bytes after cold demotion.

Compounding: `b7_5_post_acceleration_semantic_verifier.py` — the only comparator capable of producing such a proof — hardcodes the June fixture (`PARENT_ROOT` at `:26-30` pointing at a different worktree, `JUNE_SOURCE_PLAN_SHA256` at `:34`, `_JUNE_EXPECTED_SYMBOL_COUNT = 24` asserted at `:1216`, per-arm audit-binding file hashes at `:124-141`). January parity is therefore not merely un-run — it is un-runnable without editing the verifier, which would in turn invalidate `fixed_verifier_authority`.

**Consequence.** `phase_d_january_*` factorial effects rest on a parity proof covering 0.4 % of the row volume they were derived from.
**Smallest fix.** Parameterise the verifier's fixture binding (window id, parent root, expected symbol count, audit bindings) and run it for one January arm against an independently produced reference.
**Strongest fix.** Replace the receipt-inventory model with a *reference-run* model: every accepted arm must diff against a second, independently produced execution of the same window.

---

### R3 · PROOF · Acceptance gates are determinism checks presented as correctness proofs
**Conf [V].**

Three gates compare a persisted receipt to a **fresh in-process re-run of the code that wrote it**:
- `task2_closure_gate.py:288-299` → `semantic_acceptance.run_acceptance(fresh_root)`; raises `semantic_receipt_recomputation_mismatch`
- `replay_acceleration_real_gate.py:2302-2325` → imports `replay_acceleration_real_parity_verifier` and calls `verify_real_parity`; raises `parity_verifier_recompute_mismatch`
- `replay_acceleration_task9_final_validation.py:3457-3467` → `_recompute_legacy_task9_rebind(...)` defined in the same file

Two more compare producer output to producer output: `task6_prepared_pack_acceptance.py:388-397`, `task8_profile_runner.py:404`.

Additionally, **every** semantic claim from Task 3 upward funnels through one comparator and one 38-entry allowlist (`task2_semantic_acceptance.compare_role_rows`, `VOLATILITY_ALLOWLIST:561`). There is no second, independently written comparator anywhere in the acceptance chain. Widening the allowlist silently and retroactively relaxes every downstream receipt including Task 9.

**Adversarial correction (accepted): "tautology" is too strong.** Each gate re-derives from *on-disk inputs*, so it does catch hand-edited receipts, input drift, and code drift. Task 9 additionally checks namespace-inventory drift and its own implementation hash; the real gate runs `validate_fixed_verifier_code_authority` before and after. Also, the module path in the first pass was wrong: it is `replay_acceleration_task2_closure_gate.py`, not `task2_closure_gate.py`.

**Precisely what they establish:** *this receipt is the honest, current output of this pinned code over these on-disk inputs.*
**Precisely what they do not establish:** that the comparison logic is correct; that the reference was produced independently of the code under test; that any of the 38 allowlisted normalisations is semantically safe.

**Consequence.** A systematic bug in the comparator reproduces identically on both sides and passes.
**Note.** Eight genuinely independent verifiers *do* exist (`isolated_reducers_verifier`, `typed_proofs_verifier`, `integrated_source_verifier`, `slice_verifier`, `normalized_verifier`, `streaming_archive_verifier`, `real_contract_verifier`, `partial_golden_verifier`) — and **all eight are in the 35,019-line set unreachable from the production entrypoint.**

---

### R4 · AUTHORITY · The live entrypoint is not in the repository
**Conf [F].** `run_book.py` is referenced by `scripts/run_book_supervisor.ps1:108`, `src/components/ultimate_book/launcher.py:17`, `run_agent.py:41-43`, and `tests/test_run_book_account_identity.py` — and `git ls-files` returns no such file. It exists only on `remotes/origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`, not an ancestor of HEAD.

**Consequence.** The file that wires config → MT5, asserts account identity, and chooses which halt flags are honoured is unversioned on the audited branch. Every statement about live halt coverage, namespace isolation, and account gating rests on a file this audit cannot read. The hard-halt forensic join is auditing code that was not running.
**Smallest fix.** Merge or vendor `run_book.py` into HEAD before any further live-behaviour claim.

---

## Tier 1 — economically material, fix before activation

### R5 · OPS · `_modify_tp` mutates the broker while halted with no audit record — **DOWNGRADED**
**Conf [F]. Originally filed as a correctness bug; the adversarial review refuted that framing and it is corrected here.**

`src/components/execution.py::_modify_tp` reaches `self.mt5.order_send(request)` with no `runtime_halt` reference at all, while the sibling `_modify_sl` takes a halt snapshot and refuses non-risk-reducing moves.

**Why the original framing was wrong.** A take-profit move does **not** increase risk: the stop is untouched, so maximum loss is unchanged. And the TP1→TP2→TP3 partial ladder (`execution.py:8081`, `:8290`, `:8687`) moves TP *further* from entry by construction, so refusing "exposure-extending" TP moves would strand a residual at an already-hit TP1. The halt contract's own boundary token is `allows_risk_reducing_management`, and `tests/test_runtime_control_atomic_halt.py:238` explicitly asserts `_modify_tp(ticket, 2680.0) is True` on a long whose TP is 2670.0 **while the hard-halt flag is set**. TP modification under halt is intended and codified.

**What is genuinely missing** is the audit trail: `_modify_sl` records a halt diagnostic for every mutation it performs while halted; `_modify_tp` recorded nothing, so a broker mutation during a declared hard halt left no trace in the halt diagnostic stream.

**Fix as landed:** take the halt snapshot for the record, then proceed. See `IMPLEMENTATION_LEDGER.md` P3.

**Lesson recorded.** I shipped a change that broke a test codifying the intended behaviour, and claimed "zero regressions" from a partial test run. The A/B against the parent commit that would have caught it is now part of the ledger's verification step.

### R6 · OPS · The halt guard is config-gated, CWD-relative, and fails open on both
**Conf [V].** `src/safety/runtime_halt.py:100` returns the `default` (`False`) when `runtime_control.enabled` is absent; `permissions.py:148` passes `default=False`. `runtime_halt.py:103-110 _repo_root` falls back to `Path.cwd()`, and `ExecutionEngine._enforce_runtime_halt_clear` (`execution.py:487-495`) passes no `repo_root`. A missing flag file is classified `missing_paths`, not `unreadable`, so it resolves to `active=False` (`:174-178`) — `fail_closed_on_unreadable_flag_path` only fires on `OSError`.

**Consequence.** The hard halt is one dropped config key or one `cd` away from being inert. `heartbeat_monitor.py:704` already passes `repo_root=PROJECT_ROOT` explicitly, which shows the correct pattern exists and was not applied to the execution engine.

### R7 · CORRECTNESS · `create_mt5` returns a real broker connection for any unrecognised mode
**Conf [F].** `src/mt5/__init__.py:14-18`:
```python
if mode == "mock":
    return MockMT5(**kwargs)
else:
    from .mt5_real import RealMT5
    return RealMT5(**kwargs)
```
`create_mt5("mok")`, `create_mt5("simulate")`, `create_mt5("")` all connect to a real terminal.
**Fix implemented in this audit** — see `IMPLEMENTATION_LEDGER.md` R7.

### R8 · CORRECTNESS · Order materialisation is alphabetical, silently overriding the finalizer rank
**Conf [V] — adversarially verified, scope narrowed.** `v4_timewarp…:93202 for selected_instance_key in sorted(selected_instance_key_set)`. Inside the loop, `simulate_order` → `build_runtime_risk_authority` reads the *live, mutating* `account.accepted_risk_pct(day)` (`:36939`) and writes it back via `record_accepted_risk_order` (`:88708`).

**Corrections accepted:**
- Rank is real and *is* destroyed — but by `set()` at `:91706` (`selected_instance_key_set = set(final_selected_candidate_instance_keys)`), one step **before** the `sorted()`. The finalizer does emit rank order at `:52723` under `"status": "risk_admitted_selected_by_finalizer_rank"`.
- **Ordering can only change position *size*, never which orders exist.** `:88649 order_intent_materialized = bool(not fallback_contract_unmet)` has no headroom term.
- The mechanism is inert unless `scheduler_dynamic_daily_drawdown_budget_enabled` is true (`:33570`); that key is not in `config/agent_config.yaml` and is supplied by the runner. **Magnitude unresolved** — see U3.

**Consequence.** When a window is headroom-constrained *and* the dynamic budget is enabled, the trade that gets the remaining headroom is the one whose `candidate_id` SHA-256 prefix sorts first — not the one the 8,750-line finalizer ranked best. Deterministic and reproducible, therefore invisible to every determinism gate in R3.
**Deliberately not "fixed" here.** Changing the iteration order changes every sealed result. This audit adds a characterising test that documents the behaviour and fails if it is ever changed accidentally. The decision to re-order is the owner's.

### R9 · CORRECTNESS · The finalizer's shadow account is stale and the proof field asserts the opposite
**Conf [V].** `v4:47178 shadow_account = copy.deepcopy(account)` is never updated with tentative admissions, yet `:51600` emits `"risk_finalizer_shadow_account_records_prior_tentative_admissions"`.

**Consequence.** Every ranked option is sized against the same pre-window budget, so the finalizer systematically over-approves and `simulate_order` silently truncates — which is exactly the mechanism R8 then resolves alphabetically. A ledger field states a property the code does not implement.

### R10 · REPLAY/LIVE · Replay-arm sizing uses a profile production does not use
**Conf [F].** `config/agent_config.yaml:3160 timewarp_replay_risk_profile_path: "config/profiles/ftmo.yaml"`. Live sizing uses `config/profiles/redacted_account.yaml`. Measured over the 24-symbol replay surface: **NAS100 0.25 % live vs 0.50 % replay (2×)**, **US30_cash 2.0 % live vs 1.0 % replay (0.5×)**. The R0 arms pin a fixed unit (`v4:6141-6177`, `executable_risk_cash_detail`); the **R1 arms take the `balance * final_risk_pct / 100` branch at `v4:6144`**, so the divergence lands squarely on the "dynamic runtime sizing" arm.

**Adversarial correction (accepted) — realised impact is much smaller than the config gap.** Every order row in all four sealed January arms and April S1R1 was enumerated:
- **NAS100 has zero order rows in any sealed arm** (Jan S0R0 182, S0R1 176, S1R0 156, S1R1 148, Apr S1R1 88 — none NAS100). The 2× divergence is real in config but **has produced no divergent sizing in the sealed evidence.**
- **US30_cash appears only in April S1R1, 2 rows**, at `('US30_cash', 1.0, 'config/profiles/ftmo.yaml:instruments.US30_cash.risk.risk_per_trade_pct', 'R1')` against redacted_account's `2.0` — a genuine **0.5× under-sizing versus production in a sealed R1 arm**.

The wiring defect is confirmed and the ledgers prove R1 consults `risk_pct_for_symbol` (every order row carries a `config/profiles/ftmo.yaml:instruments.<SYM>.risk.risk_per_trade_pct` provenance string). The *realised* effect to date is two April rows. It becomes material the moment NAS100 trades.

NAS100 is one of three symbols named as dominating hard-halt damage (`.context/00_core/current_vnext_system_map.md:32`).

### R11 · CORRECTNESS · Config priority inversion disarms the profile-level kill switch
**Conf [V].** `src/utils/config.py:123` deep-merges `instruments.<symbol>` over the **config root**. Every symbol in `config/agent_config.yaml:4313+` carries `trading_enabled: true`, so a profile that sets root-level `trading_enabled: false` (e.g. `config/profiles/denominator_capture_research.yaml:11`) is overwritten to `True`. Gate 0.5 (`permissions.py:230-232`) therefore never fires for that profile.

**Consequence.** An "observer-only" profile is silently trade-enabled; defence-in-depth for research profiles drops from two layers to one (`deployment.phase`).

### R12 · REPLAY/LIVE · Replay's cost model is an uncalibrated constant
**Conf [V].** Spread falls through four tiers to a hard default (`v4:58839-58850`, `quote_source="conservative_default_spread_r_no_tick_or_symbol_spec"`); commission status is hardcoded `"COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK"` (`v4:58897`); slippage is the config constant `gtos_vnext_expected_slippage_r` (`broker_net_cost_engine.py:544-554`).

Live *does* capture the truth — `shadow_logs/slippage.jsonl`, `broker_order_lifecycle_capture_v4.jsonl`, per-deal commission/swap at `execution.py:2131/2225`. Offline reconcilers exist (`scripts/backfill_broker_actual_r_audit.py`, `src/research_infra/account_pnl_truth_reconciler.py`) but **nothing feeds measured slippage/spread back into the replay constants.**
**Consequence.** Replay cost is a human-maintained guess; live cost widens exactly when the strategy trades.

---

## Tier 2 — research validity

### R13 · CORRECTNESS · The B7.5 2×2 factorial is confounded
**Conf [V] — adversarially CONFIRMED.** The verifier traced the flag through to admission: `dynamic_budget_quality_gate_enabled` feeds `scheduler_quality_failures`, which at `SCHED:23758-23762` appends `"dynamic_allocator_quality_floor_not_met:…"` to `vetoes`, and `SCHED:23863` requires `status == "candidate_ranked" and not vetoes`. **The effect is real, not cosmetic: R0 arms admit candidates R1 arms reject.**

Three couplings:
1. `replay_acceleration_attempt5_typed_sparse_runner.py:11978-11983` sets `scheduler_v4_best_trade_allocator_dynamic_budget_quality_gate_enabled = False` **inside the `sizing_factor == "R0"` branch**; that flag gates hard admission floors on `expected_net_r`, `probability`, `fill_probability`, `source_completeness` (`SCHED:19542-19563`). R0 arms therefore admit a strictly larger candidate pool than R1 arms.
2. `risk_pct` is a multiplicative term in the finalizer selection score (`v4:44059-44065`) and sits at position 6 of the sort key (`:44084`). Under R0 it collapses to a constant; under R1 it reorders the ranking.
3. S0 switches to hard-only quality-failure lists (`v4:51953-51961`), so S0 ranks neutrally *on a different eligibility pool*.

**Consequence.** S0R0 / S1R0 / S0R1 / S1R1 differ in both factors simultaneously. The 2×2 cannot be read as a clean main-effects decomposition, and the "arm-neutral" claim does not hold at code level. *(Note: the mission defers optimising the economic criteria themselves. This finding is about whether the criteria are wired orthogonally, which is in scope.)*

### R14 · CORRECTNESS · In-sample priors near the admission path — **largely REFUTED as originally stated**
**Conf [V] — adversarially verified; the strong form does not hold.**

- **Blocklists — REFUTED.** `config/agent_config.yaml:813` sets `selector_v4_admission_quality_exact_block_rules_mode: "diagnostic"`. `selector_v4.py:2505-2516` routes every (symbol, side, family) and hour-bucket hit through `add_exact_rule_reason`, which under diagnostic/observe/shadow appends to `diagnostic_reasons` — and `diagnostic_reasons` is **never** merged into `hard_reject` (the reject path is `hard_reject.extend(admission_quality_hard_reject)` at `:4410`, sourced from `hard_reject_reasons` at `:3962`). The ~54 hindsight-derived rules are **annotate-only**. The first pass also cited the wrong config lines (guard flag is 780; blocklists are 818, 825, 950).
  *What does survive:* three **unconditional** hard rejects in the same guard — `selector_v4_block_partial_be_runner` (`:2536-2542`), the off-session `partial_be_runner` block (`:2543-2552`), and off-session entries with `action: "reject"` (`:2553-2570`). Their reason strings (`…after_kiap_weak_accepted_drag`) are hindsight-motivated, but they are session/policy-level, not the per-symbol loss lists.
- **Sleeve registry — PARTLY.** `_match_sleeve` is at `ultimate_candidate_package.py:1451`; the match key is **coarse and future-free** (symbol / side / framework / origin_family / session bucket, `:1462-1490`). The override does **not** flip a hard reject by itself — it is an AND-precondition on softening paths that are each separately default-off (`…_off_session_softening_enabled` false at config:791; `…_soften_selector_fill_floor_enabled` false at config:795). `selector_v4.py:3714` is **dead code**, unconditionally shadowed by `:4115`. And the registry file is an **unmaterialised 131-byte Git-LFS pointer** on this checkout, so the channel is inert here and its rows could not be sampled.

**Revised consequence.** The in-sample-contamination risk is **structural, not currently active**: the mechanism, the registry schema (which does carry `selector_lift_sum` / `scheduler_result_r_sum`, `:955-956`), and the config keys all exist, and three unconditional session-level hindsight rejects do fire. Flipping `exact_block_rules_mode` to enforcing, or materialising the registry, would activate a genuine in-sample channel with no gate in between. Because Selector V4 is not on the live path (R1), none of this exists in production either way.

### R15 · PROOF · The no-leak boundary is a string denylist and `no_leak_status` is a constant
**Conf [V].** `SCHED:6864-6926 execution_fillability_source_is_authoritative` and `selector_v4.py:1344-1355 _source_contract_violation` reject sources whose **name** contains `"postdecision"`, `"realized"`, `"outcome"`, `"future"`. Provenance timestamps are not consulted. Every `no_leak_status` in the repo is the literal `"pass"` (`v4:81413`, `permissions.py:826/889`, `live_decision_packet_v4.py:940`, `execution_manager_v4.py:373`). The only real check, `verify_no_future_leakage` (`v4:95332-95360`), inspects **five** packet fields and never touches the scheduler option record, the risk-authority packet, or the ultimate-package block — i.e. exactly where R14 lives.

Time-slicing itself is clean: `PRIMARY_DECISION_TIMEFRAMES` excludes M1/TICK (`v4:315-317`, asserted `"m1_or_tick_attached_to_decision": False` at `:59556`), and the pre-decision cost tick is hard-bounded at `asof` (`v4:58763-58766`).

### R16 · CORRECTNESS · A within-replay outcome feedback loop has no live counterpart
**Conf [V].** `build_adaptive_replay_memory_guard` (`v4:34895-35024`) reads realized `net_r` from `account.closed_trades` back into admission (`:40433-40438`), on by default in every factorial arm (`v4:31310-31312`). Causality is correctly enforced (`if close_time is None or close_time > decision_time: continue`, `:34978-34980`, 30-day lookback), so this is **not** future leakage. But there is no adaptive memory guard anywhere in `orchestrator.py` or `permissions.py`, and it couples R→S: sizing changes which trades close, which changes future eligibility.

### R17 · CORRECTNESS · Candidate identity is not unique and collisions are resolved by silent dropping
**Conf [V].** POI-anchored candidate ids omit time from the hash payload (`broader_origin_generators.py:1860-1866`); only the no-POI branch includes `candle_open_utc` (`:1869`). The composite `f"{candidate_id}@@{decision_time_utc}"` is re-derived at five independent sites. Collisions are handled by dropping the candidate (`v4:91427-91435`, `:93231-93243`).
**Consequence.** Silent candidate loss at an unmeasured rate, and five places that must be changed together.

---

## Tier 3 — performance and complexity

### R18 · PERF · Evidence representation, not economics, sets the cost floor
**Conf [F].** One January arm emits **15.75 GB** of logical JSON to produce 148 orders and 72 trades (`B7_5_POST_ACCELERATION_ARM_RECEIPT.json` → `artifact_inventory.artifacts`). Measured directly on the real ledgers:

- order row: **494,196 bytes**, 1,274 top-level keys, 8,091 scalar leaves, **765 distinct values**, **63.8 % of the row is key names** (315,449 bytes over 8,501 key occurrences, 2,860 distinct names averaging 37 characters).
- trade row: 508,394 bytes, 1,428 top-level keys, 8,297 leaves, 638 distinct values, 64.8 % key names.
- scorecard row: **1.94 MB each**.
- the same subtrees appear at several paths — `predecision_stop_hazard_guard` / `scheduler_option_predecision_stop_hazard_guard` (2,652 B twice), `package_displacement_quality` / `selected_scheduler_package_displacement_quality` (2,205 B twice, written to two dicts at `SCHED:14693-14694`), `risk_authority.package_marketable_entry_guard_replay_route` also present as a top-level key (32,263 B).

Serialization is **not** the bottleneck: measured `json.dumps` 190–250 MB/s and `sha256` 2,300 MB/s on these exact rows, so ~855 MB/dense-day costs ≈4 s of ~570 s. The cost is **computing** 1,274 fields per row.

### R19 · PERF · The heaviest function runs twice per order; the hot tick lookup is uncached
**Conf [V].**
- `build_runtime_risk_authority` (5,065 lines) at `v4:49568` (per ranked option) **and again** at `v4:85868` (per selected order), with `"runtime_risk_authority_recomputed_for_order_materialization": True` at `:85879`. The finalizer result *is* passed in (`:93316`) but only reconciled (`:85927-86160`), not reused.
- `path_source_and_oracle` (415 lines) is called up to 3× per selected order at `:86721`, `:87104`, `:87516` with **no `query_cache`**, so each constructs a fresh `PathTruthIndex`, re-parses the tick file, and re-derives per-day source authority. The two *diagnostic* sites (`:92464`, `:92880`) do pass a cache.

### R20 · PERF · Bar data is materialised five times and tick data four times
**Conf [V].** Raw bytes (`ImmutableSourceBatchCache` `payload.bin`) → fixed-width binary rows (`TypedNormalizedPartitionCache` `rows.bin`) → Python dicts (`BroadSourceResolver._file_cache`) → day-grouped copies (`_day_file_cache`, re-copied at `integrated_source.py:1082-1105`) → prepared-pack `mso_payload`. `integrated_source.py:432-443` materialises fresh dicts on every load and `:1026-1028` then calls `legacy.rows_by_day` for another full copy.
**Consequence.** Peak RSS 8.66 GB (`TASK9_FINAL_ACCELERATOR_ACCEPTANCE.json.measurements.warm_filesystem.peak_rss_bytes_median`) on a 16 GB machine, and a typed-cache "hit" still pays 2–3× row-copy cost — which is why 23 cache layers delivered 1.37×.

### R21 · PERF/OPS · Fixed per-process overhead is 63 s before the first decision
**Conf [F], measured in this audit.** A run that reached the day loop and stopped consumed **63.03 s wall / 108.98 s CPU** in source-authority validation, typed-cache bind, 4-worker sparse-tick prewarm, and resolver construction. This is the real content of the "no-event day 52.5 s vs 5 s target" miss; the economic path on a no-event day is **1.7 s** (measured across all four sealed January arms).

### R22 · OPS · No sub-window replay is possible
**Conf [F], demonstrated three times in this audit.**
1. `b7_5_post_acceleration_runner.py:1399-1400` requires `window.start == args.start and window.end == args.end` against the sealed calendar month.
2. `attempt5:16228-16231` requires exact set equality between the declared pack roots and the chunk plan.
3. `attempt5:16476-16487` recomputes the canonical source-plan digest **over the selected day set** and requires it to equal the sealed month digest.

**Consequence.** Investigating one anomalous day of a 3.5-hour arm requires re-running the arm. The engine does contain a bounded mode (`engineering_stop_after_day`, `attempt5:16122-16145`) but `b7_5_post_acceleration_runner.py:832` hardcodes it to `None` on the sealed path.

### R23 · OPS · Sealed authority binds absolute filesystem paths
**Conf [F], demonstrated empirically.** Byte-identical copies of the January evidence placed in a second worktree are rejected: `FreshSourceAuthorityError: fresh_source_authority_path_binding_mismatch` (`replay_acceleration_fresh_source_authority.py:309`, comparing `Path(bundle_binding["directory"]).resolve()` to the argument). `b7_5_post_acceleration_runner.py:1431-1434` does the same for the prepared-pack root. Two module constants pin machine-specific locations:
```python
# src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py:186-190
ATTEMPT5_RUNTIME_EVIDENCE_ROOT = Path("/Users/borr/GTOSActive/repo").resolve()
ATTEMPT5_TICK_SOURCE_MANIFEST = Path(
    "/Users/borr/Documents/gtos/repo/ai-trading-agent/"
    "data/mt5_research_exports/bridge_ftmo_ticks_micro_2025_2026/manifest.json"
).resolve()
```
and `attempt5:15241-15244` fails closed if the runtime evidence root differs.
**Consequence.** No accepted arm is reproducible on another machine, from another checkout, or after a directory rename. Four decision inputs (sleeve registry, member-axis join, reconstructed selection, fillability labels) are read from `/Users/borr/GTOSActive/repo` — outside the audited checkout and unversioned on this branch.

### R24 · PROOF/OPS · Task 9's accepted evidence namespace is gone, and the gate can no longer pass
**Conf [F] — adversarially verified and sharpened.** `TASK9_FINAL_ACCELERATOR_ACCEPTANCE.json` binds `final_validation.source_namespace = research/operations/…/attempt_5_typed_sparse/TASK9_FINAL_VALIDATION_R2_20260723T031200Z` with `complete_namespace_file_count: 437`. That directory is **absent from all five worktrees and from `/Users/borr/GTOSActive/repo`**, was never committed (`git log --all --diff-filter=A` is empty for it), and has **no cold-demotion receipt** — the only demotion receipts are the January arm ones. `.context/LIVE_STATE.md` at acceptance time listed it as untracked-and-present.

**Concrete consequence:** `validate_review_rebind` computes `current_inventory = inventory_tree(output_root)`; over a nonexistent root that cannot equal the 437-file inventory, so **re-running the Task 9 gate today raises `task9_review_rebind_namespace_inventory_drift`**. The Task 9 acceptance is unreproducible.

*Correction accepted:* the separate dangling `accepted_evidence` entry (index 19) is a **Task 2** artifact, not Task 9's, and unlike the namespace it **is** recoverable — `git ls-files -v` shows flag `S` (skip-worktree) and `git cat-file -e HEAD:…` succeeds. Task 9's own listed entry (the receipt) exists.

### R25 · DEAD · 45 % of the acceleration stack cannot run
**Conf [V].** Transitive closure from `b7_5_post_acceleration_runner` reaches 20 of 59 acceleration modules — **43,312 reachable, 35,019 unreachable** lines. `replay_acceleration_real_gate.py` + `replay_acceleration_real_parity_verifier.py` (5,096 lines) are *imported* but inert because `b7_5_post_acceleration_runner.py:820-826` hardcodes `parity_gate_after_day = None`, `streaming_proof_archive_root = None`, `max_streaming_proof_archive_bytes = 0`.

Separately, `attempt5:15180 require_attempt5_execution_authority` — docstring *"Reject every route except the fresh S0R0 Jan 1-7 parity run"* — hard-pins `arm_id == "S0R0"`, a literal arm fingerprint, a fixed output prefix, and a fixed date range. `run_typed_sparse_attempt5` is therefore a frozen single-run route; production goes through `run_replay_engine` (`attempt5:18157`).

### R26 · COMPLEXITY · A function is defined twice; the first definition is unreachable by construction
**Conf [V].** `package_or_replay_row_requires_explicit_action_intent` is defined at `v4:71321` (54 lines, `(candidate, packets)`) and **redefined** at `v4:72711` (110 lines, `(row, packets=None)`, different precedence via `first_present`). Python binds the second. Anyone reading the first is reading semantics that never execute.

### R27 · COMPLEXITY · ~30 % of the replay engine is attribution machinery
**Conf [V].** 87 `*_fields` builders = 16,412 lines; 21 `*_detail` = 6,235; 11 `*_authority` = 6,425 — ≈29,000 of 96,047 lines. Inside the hot loops: 87 `*_fields(` call sites in `run_campaign`, 44 in `simulate_order`, 24 in the finalizer.
Plus: 27 in-module-unreachable top-level defs (972 lines), 13 of them with zero callers repo-wide; four independent tick loaders; six row-window slicers of which three are unreachable; 18 copies of `canonical_bytes`; ~20 copies of `file_sha256`; 9 copies of `_canonical`.

### R28 · OPS · Four V4 evidence logs have no consumer; a retired policy still logs
**Conf [V].** `live_decision_packets_v4.jsonl`, `execution_manager_v4_decisions.jsonl`, `probability_debate_team_engine_v4.jsonl`, and `broker_order_lifecycle_capture_v4.jsonl` have no reader outside tests. The last is written twice per order (`execution.py:3471`, `:3988`) and is the natural broker-truth source for closing the R12 cost-calibration gap. Meanwhile `j46_j49_shadow_logger` still writes for a policy disabled at `execution.py:3200-3215`. Only 2 of ~133 shadow writers rotate (`structure_detector_shadow_logger.py`, `equity_guard.py`); the rest grow unbounded on the VPS.

### R29 · OPS · `--replay-existing` re-transmits historical intents to a live broker
**Conf [V].** `scripts/dual_broker_execution_follower.py:2697` resets `offset = 0` and `:2247` calls `engine.open_trade`. The file contains **zero** `runtime_halt` references in 2,832 lines; `start_all.bat:196` passes `%FOLLOWER_REPLAY_ARG%`. In this repository "replay" means both "historical simulation" and "re-send to a live account".
**Recommendation.** Rename to `--resend-intent-log` and add an explicit halt check at follower startup and per intent.

### R30 · OPS · Default-live operational scripts with no halt check
**Conf [V].** `scripts/fn_smoke_trade.py` — `--dry-run` is opt-in (`:511`), real `order_send` at `:347`. `scripts/mt5_preflight.py:136-155` places a real pending order behind only an `input()` prompt (`:54`) and prints "cancel it manually" if cancellation fails (`:147`). Neither checks the halt flags.

### R31 · AUTHORITY · The mandatory reading path routes to superseded documents
**Conf [V].** `.context/00_core/live_system_of_record.md` (2026-06-16) states at `:1-6` that it supersedes conflicting docs, and describes the live model as two independent per-account `run_book.py` workers. It appears in **neither** `CLAUDE.md`'s Mandatory Preflight (steps 1–5) **nor** its Active Context Files list. `current_vnext_system_map.md` (2026-06-05) predates the `ultimate_book` block (`config/agent_config.yaml:1246-1394`) and never mentions it. `.context/LIVE_STATE.md` — designated "the single source of truth" — renders base config without profile or instrument overlay (`scripts/generate_live_state.py:394-399`), and its enforcement heuristic reports 359 matches for `budget.monthly_cap_usd` because the regex is `monthly_cap_usd|budget` (`:173`); the real count is 2, both of which document that it is *not* enforced.

### R32 · CORRECTNESS · Latent wall-clock leaks in replay
**Conf [V].** `SimulatedBroker.get_positions` (`v4:3552`) and `get_pending_orders` (`v4:3559`) compute ages against `datetime.now()`, not the replay clock. Dormant today (the main loop uses `account.open_snapshot(asof)` at `:90611`) but live if anyone wires `V4DecisionCycleCore` to the `SimulatedBroker` adapter, which `v4_live_replay_decision_core.py:113` invites. `build_simulated_prop_headroom` (`v4:34658`) defaults evaluation time to wall clock when `captured_at_utc` is `None`. `broader_origin_generators.py:277` silently substitutes wall clock when `now_utc` fails to parse — in the *shared* generator, so it affects replay and live alike. That should raise, not fall back.

### R33 · CORRECTNESS · Small fail-open defects with economic effect
**Conf [V].**
- `src/components/verification.py:1106` — `.get("max_gap_pct") or 1.5`: setting the strictest value `0` silently becomes the loosest `1.5`.
- `src/components/permissions.py:1718, 1787` default `gate1.ob_retest_sl_min_buffer_atr` to `0.3` while `src/components/m5_refinement.py:287` defaults it to `0.5` and config sets `0.5`. Deleting the key loosens the permissions gate by 40 % while the M5 clamp stays tight.
- `src/components/orchestrator.py:7652` defaults `session_memory_enabled` to `True` while config sets `False` — inverted fail direction.
- `src/components/news_calendar.py:54` defaults `enabled` to `False`; `:84-88` logs "all trades will proceed" when enabled but empty.
- `src/components/permissions.py:1371-1373`, `:1418-1423` — `except Exception: return None` fails the concurrent cap and the cross-instrument correlation gate open.
- `run_agent.py:37-47` wraps the double-book guard in `except Exception: pass`.

### R34 · AUTHORITY · Environment variables override YAML for economic settings and appear in no seal
**Conf [V].** `GTOS_PROFILE` (`src/utils/config.py:154`) selects the entire risk/instrument/broker profile. `GTOS_UB_DERISK_MODE` (`ultimate_book/book_engine.py:325`, `admission.py:819`) is read **before** YAML and decides whether the 2.0 % ceiling profile trades at all. `GTOS_DUAL_BROKER_INTENT_ENABLED` (`dual_broker_intent_bus.py:722-724`) decides whether the second account receives orders. Seals bind code and two YAML files (`attempt5:1502-1511`) and capture **no environment at all**.
**Consequence.** Two runs with identical seal digests can size differently, trade a different symbol universe, and route orders to a different broker.

### R35 · OPS · Cross-account state is global, not per-broker
**Conf [V].** `config/profiles/*.yaml` declare 21 `runtime_paths.*` keys promising per-account isolation of `pipeline_state`, `shadow_logs`, `knowledge_base`, `logs`, `m1`, `ticks` — with **zero production readers**. `src/safety/dormant_state.py:50 DORMANT_STATE_PATH = Path("pipeline_state/dormant_state.json")` is relative and unnamespaced.
**Consequence.** A redacted_account daily-loss stop dormants the FTMO book and vice versa — the opposite of the two-independent-books model in `live_system_of_record.md:9-18`.

### R36 · COMPLEXITY · Silent-stale cache keys
**Conf [V].** `BroadSourceResolver.load_file` (`attempt5:8390`) keys on `str(path)` alone, stores the sha in the *value*, and never re-checks it (`:8402`); `release_completed_chunk_caches` (`:8645-8654`) drops only day-suffixed keys, so full-file entries survive all 31 days. `_cached_ftmo_manifest_payloads` (`v4:6905`) keys all source manifests on the repo root alone. `file_sha256_cached` (`v4:6889`) trusts `(mtime_ns, size)`.
**Consequence.** A source file changed between the pack build and the arm run is silently reused with old content, and the exact-hash contract still passes because it hashes the cached value.

---

### R37 · COMPLEXITY/OPS · The proof layer is sealed into the execution contract, so it cannot be repaired
**Conf [F] — discovered by this audit while attempting a benchmark, and demonstrated.**

`B7_5_POST_ACCELERATION_DECISION_CONTRACT.json` → `input_bindings.common_behavior_inputs` binds **42 files by SHA-256**. Those hashes feed `common_execution_input_digest_sha256` → `arm_fingerprint_projection` → `arm_fingerprint_sha256` for all four arms (`attempt5:1078-1133`).

Nine of the 42 are verifiers, gates, or acceptance modules that **never execute during a replay**: `b7_5_post_acceleration_semantic_verifier.py`, `replay_acceleration_task2_semantic_acceptance.py`, `replay_acceleration_integrated_source_verifier.py`, `replay_acceleration_real_gate.py`, `replay_acceleration_real_parity_verifier.py`, `replay_acceleration_streaming_archive_verifier.py`, `replay_acceleration_task9_final_validation.py`, `replay_semantic_diagnostic.py`, `verify_denominator_to_deployment_execution.py`. Two more are one-shot builders.

**Demonstrated:** applying the R-P1 fix to `b7_5_post_acceleration_semantic_verifier.py` — a file that does not run during a replay — caused the next replay to fail closed with
`ValueError: selection_sizing_decision_contract_input_drift:src/research_infra/b7_5_post_acceleration_semantic_verifier.py`.

**Consequence.** Repairing a verifier bug requires regenerating the decision contract, all four arm fingerprints, and re-running every arm — roughly 16 hours of compute per window. This is the mechanism by which every proof-layer defect in this register has survived: the architecture prices correctness fixes at a full campaign.

**Also confirmed here:** the bound config set is `agent_config.yaml`, `profiles/ftmo.yaml`, `profiles/operator_profile.yaml`. **`profiles/redacted_account.yaml` — the live profile — is not bound**, independently corroborating R10.

**Smallest fix.** Split `input_bindings` into `executing_closure` (bound) and `verification_tooling` (versioned, not bound).

---

## Adversarial review

Two independent verifier agents were tasked with **refuting** the twelve highest-stakes claims, defaulting to REFUTED where they could not confirm from code. Outcome: 3 CONFIRMED, 7 PARTLY_CONFIRMED with material narrowing, 1 REFUTED as stated (R14 blocklists), 1 confirmed with a symbol-level correction that substantially reduced its realised severity (R10). Every correction is folded into the entries above and marked. Findings that survived unchanged: R5, R7, R13, R23, R37.

---

## Unknowns worth closing

| # | Question | Why it matters | How to close |
|---|---|---|---|
| U1 | What does `run_book.py` actually do? | R4 blocks every live-behaviour claim | vendor the file from the VPS branch |
| U2 | Rate of `duplicate_exact_candidate_instance` drops | R17 — silent candidate loss of unknown size | count the event in the existing decision ledgers |
| U3 | Does the finalizer ever over-approve past headroom in practice? | decides whether R8+R9 change any real trade | count windows where `sum(approved) > headroom` in the January ledgers |
| U4 | True cold end-to-end cost of one arm | every published number assumes warm derived caches (`progressive_benchmark.py:136-145`) and excludes the separate `build-pack` process | one measured `derived_cold` run |
| U5 | How much of the 570 s/day is `build_runtime_risk_authority` | sets the ceiling on any optimisation | the sampled profile in `REPLAY_TRUTH_AND_PERFORMANCE_AUDIT.md` |
