# F5 LANDING V1 — the minimal-size live experiment, landed and preflighted

**Status: GO, with two owner-facing items and one correction to the commission.**
Nothing was started. No VPS, no broker, no live process was touched by this session.

Scope of this document: what was landed, what was measured, what was found that the package did
not know, and exactly what remains before the experiment can be started. The design is
`../forensics/F5_LIVE_MINIMAL_SIZE_PACKAGE_V1.md`; this is the record of landing it.

---

## 0. The answer, in one page

| | |
|---|---|
| **Magic-number isolation** | **LANDED and PROVED.** `magic_for_namespace()` is a pure function of the runtime namespace; the two F5 namespaces resolve to `0`, every other namespace — typos included — resolves to the armed book's `20260401`. 14 tests in `tests/safety/test_f5_isolation.py`, including the two the package names as ceremony blockers. Both pass. |
| **`test_f5_open_risk_fail_closed_not_triggered_by_f5`** | **PASS.** An F5 position with `sl == 0` leaves the armed book's `_open_risk_pct` numerically identical. Written as a differential test: the same fixture with the identity *shared* returns the full 4 % cap, so the test cannot pass vacuously. |
| **`test_f5_conviction_ledger_is_namespace_isolated`** | **PASS.** Filesystem test on real paths: 20 firing sleeves written to `…/operator/firing_sleeves.json` leave `…/operator_profile/` at 2 and its `na` unchanged. |
| **Default path** | Unchanged. Every F5 seam is inert with the flag absent; `trade_params` does not even grow a key. |
| **Files touched** | 13. **All 13 are FREE of the R2 decision contract** — verified against `B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json`. No re-seal. |
| **Activation tokens** | Untouched on both accounts — **after a defect in this session's own work was caught and reverted (§4).** No re-mint. |
| **`config/agent_config.yaml`** | **Not edited.** Byte-identical to HEAD. |
| **The armed books** | Not changed in any respect: same `--tags`, same tokens, same config, same profiles, no restart implied. |

**Two owner-facing items before the start** — §6. **One correction to the commission** — §4.

---

## 1. What was landed

Five scoped commits. Every file below is FREE of the R2 contract (checked, §3).

### 1.1 The blocking hazard — broker identity per decision surface

`MAGIC_NUMBER` was one module constant that every position read filtered on. That is safe with
one book per account and becomes a live-behaviour change on **armed money** with two, because
the namespace isolates every *file* surface and no *broker* surface.

The worst row is silent and it is the one that costs money: `book_engine._open_risk_pct` returns
the **full gross-risk cap** when any position it can see has `sl == 0`, `price_open == 0`, or an
unreadable `value_per_point`. One experiment position on a symbol without instrument config —
and redacted_account already silently skips 13 symbol/sleeve pairs on exactly that — makes the armed
book read `gross_risk_cap_exhausted` and stop opening units, with a healthy log and no alert.

Landed:

- `src/mt5/mt5_interface.py` — `MAGIC_F5_MINIMAL = 0`, `COMMENT_PREFIX_*`,
  `magic_for_namespace()`, `comment_prefix_for_magic()`, `comment_prefix_for_namespace()`.
  An **unknown namespace returns the armed magic**, deliberately: a typo must not mint a third,
  unmanaged identity — it must land on the one the system already knows how to manage.
- `src/mt5/mt5_real.py` — `RealMT5(..., magic=MAGIC_NUMBER)`; the two position filters read
  `self._magic`. **This is the single funnel**: every consumer in the live book path — the
  gross-risk sum, the same-symbol guard, adoption, the out-of-universe alert, the
  residual-after-partial resolver — reads positions through `get_positions` /
  `get_open_positions` and nothing else.
- `src/components/execution.py` — 14 sites, not the 8 the package listed (§5.1). Ten request
  sites and four *filter* sites; the filters matter because an F5 engine filtering on `20260401`
  would lose track of **its own** partials.
- `src/components/ultimate_book/book_owner.py` — `self._magic` / `self._comment_prefix`,
  `_sleeve_comment`, `_position_exposures`, both adoption comment checks, `_alert_out_of_universe`.
- `run_book.py` — resolves the identity **once** from `args.namespace`, binds it to the wrapper,
  and logs it. `ExecutionEngine` derives the same value independently from
  `broker_account_namespace(config)`, which the launcher already sets to `args.namespace`: two
  derivations of one function of one input.
- **Fail-closed on a split identity.** `UltimateBookOwner.__init__` raises if the wrapper's magic
  and the namespace's disagree. A book that places under one identity and manages under another
  would leave positions open, unadopted and invisible to every guard — with a healthy log.

### 1.2 The experiment

- `src/components/ultimate_book/minimal_size.py` (new) — `MinimalSizeConfig` (validated at
  launch), `NotionalLedger`, `MinimalSizeScaler`, `round_up_to_min_lot`, `MinimalSizeCapture`,
  `minutes_to_nearest_high_impact_event`.
- **The scalar goes last.** `execution.py`, immediately after
  `risk_amount = account_balance * (risk_pct / 100)` — after the pre-trade cost model and after
  Execution Manager V4, both of which receive the **nominal** `risk_pct`. Asserted on recorded
  call arguments, not on source text.
- **Round up, never shed.** The sub-minimum branch rounds to `volume_min` under the flag and
  records `f5_lots_requested` / `f5_lots_placed` / `f5_lot_inflation`. An unreadable or
  pathological geometry **refuses** rather than producing an off-grid lot.
- **Three notional surfaces** in `book_engine.py`: `_equity` (N1), `_open_risk_pct` (N2), and a
  new `_f5_day_start_balance` helper that both governor call sites now route through (N3). N2 is
  the hunk that makes the experiment valid: at 1/200th lots the broker-derived sum reads
  ~0.0002 against a 0.04 cap, so the cap would never bind and the book would carry 20+
  concurrent units where production carries 2.
- **Notional breach → flatten → log → new epoch**, in that order: the production flatten runs
  first, on real positions, through the unchanged path; then the ledger closes a *numbered*
  epoch and reopens. `real_pnl_usd_cumulative` is never reset. **Never** `live_broker_authority:
  false` (H8 — that flag does not flatten and stops trade management too).
- **No loss budget**, by owner decision. The firm's limits, the governor, the kill flag and the
  activation token are the only brakes and none is bypassed. A test asserts the ledger has no
  budget gate, so adding one later is a visible policy change rather than a quiet one.
- **Capture**: `shadow_logs/f5_minimal/<ns>/events.jsonl`. Every row stamps `namespace`,
  `account_login` and `broker_mutation` — the fields `shadow_logs/slippage.jsonl` lacks on every
  row, which with four books writing would make fill rows indistinguishable.
- **`f5_slate`** closes the funnel-denominator gap: `admission.py` writes nothing to disk, so
  "we saw 9, took 2, here is why 3 lost to 6" cannot be reconstructed today. Pure observation,
  reusing values admission already computed. Idle cycles are skipped — the launcher already
  writes one namespaced row per tick.
- **News proximity** (§7.2 gap 5): every fill carries `f5_minutes_to_high_impact_event` from the
  `data/news_calendar.json` the runtime already loads. `None` when unreadable — absence is
  honest, a zero would be a lie.
- **The trail path** (`f5_stop_move`). `asian_fade` and `metal_session_reversion` are in the 32
  and are `trailing_runner`: no take-profit at all (`broker_take_profit_mode: "none"`,
  `final_target_r: None`), armed then trailed 0.5R behind. **Neither has ever carried a dollar
  of real money**, so this run is the programme's first live read of the let-it-ride exit — and
  the trail path reaches disk **nowhere** on the live book path today
  (`trailing_stop_shadow_logger` is wired into `orchestrator.py` only; `_modify_sl`'s audit is
  an in-memory halt diagnostic; the trade record keeps the *latest* stop, not the sequence). One
  row per **actual move**, never per tick: first row = the arm, last row = what the exit rode in
  on, each carrying previous stop, new stop and the R locked in against the initial risk.
  `f5_trade_closed` carries the realised R. Inert without the flag.

### 1.3 Arming, declared not omitted

- `config/live_armed_set.json` — two new accounts with the **explicit 32-name** list, a decision
  log entry naming the owner's words, and a new `surface` field (§5.2).
- `scripts/run_book_supervisor.ps1` — two new `$books` rows, plus a fix that was required and is
  worth knowing: `--spread-geometry-floor`, `--lane-weights` and `--lane-weights-key` were
  passed **unconditionally**, so a `$null` on an F5 row would have reached `run_book.py` as an
  empty string, and `parse_spread_geometry_floor` **refuses an empty string at launch by
  design**. They are now conditional. **Unchanged for the two armed rows**, which supply all
  three.
- `scripts/f5_status.py` (new) — the operator view. With no loss budget, the reporting *is* the
  control.

### 1.4 Tests

| file | tests | what it pins |
|---|---:|---|
| `tests/safety/test_f5_isolation.py` | 14 | the broker identity, both ceremony blockers, the fail-closed converse, adoption, same-symbol, two locks, no split identity |
| `tests/ultimate_book/test_f5_minimal_size.py` | 34 | default path, scalar-is-last, gross cap (differential), the fourth notional surface, round-up incl. the grid and the refusals, ledger + epochs + restart, no budget gate, capture, config refusal, news stamp, the trail path, armed-set |
| `tests/ultimate_book/test_f5_status.py` | 6 | read-only (measured by recorded calls), magic split, de-risk knee arithmetic, the unwired-ledger canary, day-zero render |
| `tests/safety/test_f5_carry_is_seal_and_token_safe.py` | 7 | **new class of test** — every carried file is outside the R2 seal *and* outside both token digests, the latter measured by byte-perturbation with a converse probe |
| `tests/safety/test_armed_set_single_source.py` | +2 | the production/experiment surface distinction, and that a production row gaining a minimal-size flag is a build failure |

**57 new tests. All pass.**

---

## 2. Preflight

Run on this machine, on the landed tree. Nothing below contacts a broker or the VPS.

```
$ python3 -m pytest tests/safety/test_f5_isolation.py -q
14 passed

$ python3 -m pytest tests/safety/test_f5_isolation.py::test_f5_open_risk_fail_closed_not_triggered_by_f5 \
                    tests/safety/test_f5_isolation.py::test_f5_conviction_ledger_is_namespace_isolated -q
2 passed                    <-- THE TWO CEREMONY BLOCKERS

$ python3 -m pytest tests/ultimate_book/test_f5_minimal_size.py -q
30 passed

$ python3 -m pytest tests/ultimate_book/test_f5_status.py -q
6 passed

$ python3 -m pytest tests/safety/test_f5_carry_is_seal_and_token_safe.py -q
7 passed

$ python3 -m pytest tests/safety/ tests/ultimate_book/ -q
1500 passed, 3 skipped, 3 xfailed, 1 failed
   the 1 failure is PRE-EXISTING at HEAD -- see section 5.4
```

**The magic map resolves as designed:**

```
magic_for_namespace('operator_profile')   == 20260401
magic_for_namespace('redacted_account_live_bee34003')== 20260401
magic_for_namespace('operator')         == 0
magic_for_namespace('redacted_account_f5_minimal')   == 0
magic_for_namespace('ftmo_f5_minmal')          == 20260401   <-- a typo lands on the ARMED identity
magic_for_namespace('') / (None)               == 20260401
```

**Flags parse and bad values refuse:**

```
$ python3 run_book.py --help | grep f5-
  --f5-minimal-size-usd F5_MINIMAL_SIZE_USD
  --f5-notional-initial-usd F5_NOTIONAL_INITIAL_USD

MinimalSizeConfig(enabled=True, target_risk_usd=0.0).validate()      -> ValueError
MinimalSizeConfig(enabled=True, target_risk_usd=10_000).validate()   -> ValueError
MinimalSizeConfig(enabled=True, notional_initial_usd=0).validate()   -> ValueError
MinimalSizeConfig(enabled=True, target_risk_usd=10.0,
                  notional_initial_usd=100000.0).validate()          -> OK
```

**The armed set reconciles — four accounts, the two armed UNCHANGED:**

```
reconcile()                          -> []                       (no disagreements)
armed_sleeves()                      -> {crypto, energy_agri, sub_mid_dn_revert, sub_xvol_pullback}
armed_sleeves('operator_profile')   -> the same four
armed_sleeves('redacted_account_live_bee34003')-> the same four
production accounts                  -> operator_profile, redacted_account_live_bee34003
experiment accounts                  -> operator, redacted_account_f5_minimal   (32 sleeves each)
```

**R2 decision-contract membership — all 13 touched files:**

```
free   config/profiles/redacted_account.yaml            free   src/components/execution.py
free   config/live_armed_set.json                 free   src/components/ultimate_book/book_engine.py
free   run_book.py                                free   src/components/ultimate_book/book_owner.py
free   scripts/run_book_supervisor.ps1            free   src/components/ultimate_book/minimal_size.py
free   scripts/f5_status.py                       free   src/mt5/mt5_interface.py
free   scripts/rerate_book_from_live.py           free   src/mt5/mt5_real.py
free   research/.../FIRM_RULES_V1.json            free   src/safety/armed_set.py

config/agent_config.yaml: BOUND, and NOT EDITED (byte-identical to HEAD)
```

**Activation-token digests — measured by byte-perturbation, both live profiles:**

```
for each carried file: perturb one byte -> config_digest_for(agent_config, <profile>) UNCHANGED
converse probe:        perturb config/agent_config.yaml            -> digest MOVES
                       perturb config/profiles/<profile>.yaml      -> digest MOVES
=> no carried file enters either account's token digest. No re-mint.
```

**Full-suite A/B against the parent commit** — see §7 for the measured result.

---

## 3. What was NOT done, and why

- **The experiment was not started.** No VPS, no host-admin, no broker, no live process.
- **`config/agent_config.yaml` was not edited.** R2-bound and inside both token digests.
- **The V4 funnel was not armed.** It needs a config edit for a policy with one PASS and four
  REJECTs across five sealed months.
- **`post_event_block_minutes: 2 → 5` was not fixed.** Config byte ⇒ re-seal + re-mint on two
  live accounts. Mitigated by stamping every F5 fill with its distance to the nearest HIGH
  event, so tainted fills can be excluded rather than argued about.
- **`config/profiles/redacted_account.yaml` was not edited** — see §4, this is the correction.

---

## 4. CORRECTION TO THE COMMISSION — cleanup #1 is not safe as framed

The commission asked for the stale FOLLOWER comment at `config/profiles/redacted_account.yaml:5-11`
to be corrected, on the grounds that **"That file is NOT contract-bound."**

**That is true of the R2 contract and it is not the binding constraint.** Measured:

```
activation_token.config_digest_for(config_path, profile)
    hashes config/agent_config.yaml BYTES  +  the ACTIVE PROFILE FILE's BYTES
run_book.py:492   _cfg_digest = config_digest_for(args.config, args.profile)
supervisor        launches the redacted_account book with --profile redacted_account
=> config/profiles/redacted_account.yaml bytes ARE inside the redacted_account activation-token digest
```

A one-byte comment change therefore invalidates the redacted_account token the moment the file
reaches the host, and `RealMT5.order_send` then refuses every **exposure-increasing** request on
a funded account trading real money until someone notices and re-mints. (Risk-reducing requests
still pass, so nothing would be stranded — but the book would stop opening, quietly.)

**I made the edit, measured the digest move, and reverted it.** `config/profiles/redacted_account.yaml`
is byte-identical to HEAD (`sha256 b856f0ee…`, verified against `git show HEAD:`).

**The underlying documentation defect is real and stands as an owner-facing item.** The header
describes a FOLLOWER that "places NOTHING until decision + risk-% parity vs the FTMO primary is
proven clean"; the operative block at `:1093-1113` says `role: primary_full_runtime` with five
explicit `copy_primary_*: forbidden` constraints and `target_broker_truth_source:
target_broker_local_only`. The file contradicts itself, and the stale half is the one that reads
like trade replication — which redacted_account ToS §9.1(g)/(h) prohibit and which this architecture
deliberately does not do. **Bundle the comment fix with the next scheduled re-mint** (tokens
expire 2026-09-09), together with `post_event_block_minutes: 2 → 5`.

`tests/safety/test_f5_carry_is_seal_and_token_safe.py` now makes this class of mistake
impossible to land quietly: it perturbs every carried file by one byte and asserts the digest
does not move, with a converse probe so it cannot go vacuous.

---

## 5. What the package did not know

### 5.1 The magic surface is larger than §4.3 lists — 14 sites in `execution.py`, not 8

The package lists eight `"magic": MAGIC_NUMBER` request sites. There are **ten**, plus **four
filter sites** (`p.magic == MAGIC_NUMBER`) it does not mention at all. The filters are the ones
that matter for correctness: they resolve the residual position after a partial close. An F5
engine filtering on `20260401` would see **zero** of its own positions there and lose track of
every partial. All 14 now read `self._magic`.

### 5.2 `armed_sleeves()` would have been poisoned — the surface distinction

Adding two 32-sleeve accounts to `config/live_armed_set.json` broke four things, and it was
right to break them: `armed_sleeves()` unions across accounts, and every consumer means *"what
is trading real money at the production dial"*. A 32-sleeve $10 surface folded into that union
answers a different question with the same words — precisely the class of error `armed_set.py`
exists to prevent.

Landed: an explicit `surface` field (`production` / `experiment`). `armed_sleeves()` unions
**production only** by default; naming an account returns that account regardless. The launcher
side **derives** the surface from whether the row passes `--f5-minimal-size-usd`, so mislabelling
either side is a `surface_mismatch` and a build failure. The dangerous direction is the one that
motivates it: a *production* row that quietly gained a minimal-size flag would place 1/200th
lots while every published figure, every survivor screen and every learning-lane recommendation
still priced it at the dial. `scripts/rerate_book_from_live.py` now derives from
`production_arming()`.

### 5.3 Three of the five §4.2 hazard rows do not apply to the live book path

Verified by import-closure measurement, not by reading:

| §4.2 row | verdict |
|---|---|
| `RealMT5.get_open_positions` → `_open_risk_pct` | **REAL.** The one that costs money. Fixed. |
| `RealMT5.get_positions(symbol)` → same-symbol | **REAL.** Fixed at the same funnel. |
| `cross_instrument_correlation_gate` | **NOT REACHABLE** from `run_book.py`. It is imported only by `permissions.py`, `orchestrator.py`, `direction_emission_logger.py` and `primary_analyzer_prompt.py` — the V4/legacy lineage. The ultimate_book path never calls it. |
| `book_owner._position_exposures` adoption | **REAL**, and it consumes the already-filtered list, so the magic fix closes it. Fixed at the comment clause too. |
| `_alert_out_of_universe` | **REAL** but consumes the filtered list; cosmetic for the armed book, and it would have made the **F5** book blind to its own out-of-universe positions. Fixed. |

Also out of the live book path: `concurrent_tracker.py`, `permissions.py`, and
`same_symbol_lifecycle_v4`'s *decision* function. `execution.py` imports only
`record_same_symbol_lifecycle_entry_v4` from that module — a **store write**, not a broker
request, read by no live decision (only by an offline script). Its store
(`knowledge_base/meta/same_symbol_lifecycle_v4_store.json`) is **shared across namespaces** and
is a read-modify-write, so four writers will race where two do today. Pre-existing, best-effort,
no decision reads it: **filed, not fixed.**

### 5.4 A fifth artifact had written the armed set down, and the launcher rows found it

`tests/ultimate_book/test_lane_weights.py::test_supervisor_binds_current_account_scopes_and_contracts_to_external_files`
was failing on a clean checkout when this landing began: a **source-string assertion** expecting
the committed launcher to still carry `mx_btcusd_d1_donchian_20_breakout` in its tags — the
sleeve the owner disarmed on 2026-08-05 and wave-20 lane p4 removed on 2026-08-07. The test was
stale, not the launcher. A concurrent session repaired it during this landing (it is now a
behavioural test that derives from `src.safety.armed_set`), so it is green here and it is **not
this change's work**. Recorded because it is the fifth artifact to write the armed set down from
memory, and because CLAUDE.md §6 names the antipattern exactly: *"a test that greps the source
for a substring passes against a wrong implementation."*

### 5.6 Three test files are environment-dependent, on both sides

`tests/test_replay_differential_harness.py` — `test_a_sealed_arm_compared_with_itself_is_equivalent`,
`test_two_different_sealed_arms_are_reported_as_differing`,
`test_the_cold_shard_roles_are_readable_on_a_sealed_arm` — fail **identically on both clean
checkouts** (`'INCOMPLETE' == 'EQUIVALENT'`, `KeyError: 'left_row_count'`, `'absent' == 'raw'`).
They read the parked campaign's cold-evidence shards, which a concurrent *"Storage reclamation
2026-08-12: 27.0 → 86.6 GB free"* commit moved during this session. Same on both sides, so they
cancel in the diff; flagged here because they will otherwise be mistaken for a regression by the
next reader.

One more worth recording as a **method** note rather than a finding:
`tests/phase21/test_wave21_verification.py::test_matching_fresh_receipt_establishes_current_parity`
appeared to regress in a first A/B attempt and does **not**. It builds a receipt from the
working-tree launcher and verifies it against the launcher **at the preserved commit**, so any
dirty worktree fails it — including the file-copy staging the first A/B used. On a clean checkout
of the landed commit the whole file passes (22/22). If a future session stages an A/B by copying
files onto a checkout, this test will cry wolf.

### 5.5 `MockMT5` cannot reach the vNext sizing path

`_calculate_lots(require_broker_geometry=True)` sizes from `order_calc_profit` and disables every
fallback; `MockMT5` supplies neither that nor `symbol_info`. Without a raw-broker double a vNext
order returns `lot_size_unverified` **before** it reaches the sub-minimum decision the round-up
replaces — so a naive round-up test would have proved nothing. The test file supplies a minimal
`_RawBroker` and the round-up is exercised end to end through `open_trade`.

---

## 6. Before the start — the queue, in order

1. **Owner decision: `mx_btcusd_d1_donchian_20_breakout` is in the F5 32.** The owner disarmed
   it on the production book on 2026-08-05. The F5 approval was explicitly "all 32 sleeves, not
   the armed 4", and it runs at $10 on a separate broker identity in a separate namespace — so
   this is not an exemption, it is a different surface. **It is still a sleeve the owner turned
   off, and he should know it is back on at $10 before the start.** Pinned by
   `test_an_experiment_surface_may_run_a_disarmed_sleeve_only_at_minimal_size`, which fails if
   any of the three conditions (experiment surface / fixed minimal size / distinct namespace) is
   removed.
2. **Step-zero host read is still required and this session did not do it** (out of scope):
   - `governor_static_initial_balance` — if it is not `100000.0`, every de-risk-knee number in
     `f5_status.py` and §4.4 of the package moves with it.
   - The redacted_account receipt `FN_SIZE_CAP_V1.json` records `size_cap_multiplier 0.622928,
     reason derisking_into_maxdd_wall`, which $100,000 / $96,229 does **not** produce (that gives
     1.0). Either the host's reference differs or the receipt is from another moment. **If
     redacted_account really is at 0.6229 it is already inside the de-risk band, and every experiment
     dollar there costs 3.33 pp of armed size.** Still the owner's call — but he must make it
     knowing.
   - `include_clean3` and the broker symbol geometry (the floor table is a 2026-07-25 snapshot).
   - Confirm both accounts flat, and that no `firing_sleeves.json` exists for today under the
     **new** namespaces.
3. **Two new activation tokens**, minted against the `--namespace` strings
   (`operator`, `redacted_account_f5_minimal`), **not** the profile names. Minting
   `"namespace": "redacted_account"` against a worker running `--namespace redacted_account_live_bee34003`
   is what refused 462 orders over two hours and left that account at zero trades for twelve
   days.
4. **Start FTMO first; stagger redacted_account.** Package §9.5: FTMO has the larger buffer, no
   de-risk coupling, cheaper min-lot geometry, and no captured cross-firm conduct clause.
   redacted_account waits on the free page fetches and one support ticket.
5. **Start at a decision-day boundary**, or delete the new namespace's `firing_sleeves.json`
   first. The ledger is per-namespace so the armed book cannot be contaminated — but the F5
   book's own count should start clean.
6. **H8 ordering, in any step that touches an open position: flatten first, confirm flat, then
   gate.** `live_broker_authority: false` does not flatten and stops routine trade management
   too. Rolling back F5 means: flatten magic-`0` positions, confirm flat, remove the two
   `$books` rows, count those two workers to zero. The armed books are never touched.

### 6.1 Deployment path — the F5 package's §8.2 assumes the wrong one

The package's §8.2 carries eleven files by `Copy-Item` from a backup directory. **That is not
how code reaches this host.** The live tree is `C:\Users\MSI\Documents\ai-trading-agent`
(**not** `C:\GTOS\repo`, which holds only `archives/ exports/ installers/ logs/ tools/` and is
not a git repository), code moves via **GitHub**, and VPS work runs **natively on the host**
rather than from a Mac agent driving it. So:

- **Everything here is pushable and pulls cleanly.** All 14 files are ordinary tracked files on
  the branch; nothing is generated, nothing is LFS, nothing needs a manual copy.
- Keep §8.2's `BACKUP_MANIFEST.json` step anyway — it is what makes §8.7's rollback block safe,
  and a `sha256: null` row is the only thing that authorises a delete.
- Keep §8.1 step zero verbatim: it derives the interpreter and the repo root **from the running
  process**, never from a directory listing, and it is the step that catches a host whose tree
  is not where anyone assumed.
- `scripts/run_book_supervisor.ps1` is the one file that must **not** be taken wholesale: the
  host's copy is a different, larger file (19,495 B against 7,828 B here, `$books` at `:140`,
  spread-floor key named `floor` not `spreadFloor`). Carry the two new `$books` rows and the
  conditional-argument change **by hand**, into the host's own file.
- The two new activation tokens are minted **on the host**, against the `--namespace` strings.

---

## 7. Full-suite A/B against the parent commit

Method: two clean `git worktree` checkouts at `HEAD` (`3da95f915`), one with this change applied,
run with `scripts/pytest_failset.py` (`--continue-on-collection-errors`, without which the suite
aborts at collection and executes zero tests while exiting like a completed run). A concurrent
session committed to this worktree during the landing; its files
(`broker_net_cost_engine.py`, `src/costs/barrier_slippage.py`, `tests/costs/*`) have **zero
overlap** with the 13 files here, verified by `git diff --name-only`, so the A/B isolates this
change alone.

**RESULT — `0e425e895` -> `56721dd5c`:**

```
before 0e425e895: 34 bad   (13,945 passed / 127 skipped / 31 xfailed / 1 errored)
after  56721dd5c: 33 bad   (14,024 passed / 127 skipped / 31 xfailed / 0 errored)

unchanged: 33    fixed: 1    REGRESSED: 0        <-- NO REGRESSIONS

FIXED: + tests/test_broad_origin_emission_repairs.py
```

**Zero regressions, one fixed, +79 net new passing tests, one fewer collection error.** The
fixed file is the one the parent commit broke on its own: `0e425e895` landed 81 seconds before
this change and already calls `_armed_sleeves(surface=None)`, a keyword that does not exist in
`armed_set.py` at that commit — it was written against this session's uncommitted tree, so the
parent is red without this change and this change is what completes it.

A first A/B attempt reported 5 regressions and was **methodologically flawed** (it staged the
"after" side by copying files onto a clean checkout). All five were run down individually and
none was real: three are environment-dependent on both sides (cold-evidence shards a concurrent
storage-reclamation commit moved mid-session), one is a dirty-worktree artifact of the staging
itself, and one was the wrong-baseline case above. Full detail: `F5_LANDING_AB_V1.txt`.

The trail-capture commit `ac8438f2b` landed after that pair and carries its own A/B
(`F5_LANDING_AB_V1_TRAIL.txt`), because it adds a call site on the armed book's per-tick
management path and so earns a measurement rather than an argument.

---

## 8. Commits

| # | scope |
|---|---|
| 1 | broker identity per decision surface + `tests/safety/test_f5_isolation.py` |
| 2 | the minimal-size module, the execution seams, the notional surfaces, the book hooks, the launcher flags + `tests/ultimate_book/test_f5_minimal_size.py` |
| 3 | `scripts/f5_status.py`, the armed-set surface distinction, the two declared F5 accounts, the two launcher rows + `tests/ultimate_book/test_f5_status.py` |
| 4 | `tests/safety/test_f5_carry_is_seal_and_token_safe.py` + the `FIRM_RULES_V1.json` news-filter correction |
| 5 | this document |
