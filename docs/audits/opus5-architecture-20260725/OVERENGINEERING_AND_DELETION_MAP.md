# Overengineering and Deletion Map

**Measured over `a3badc054`.** All counts come from an AST import graph over 1,638 `.py` files (1,331,833 lines) plus `git ls-tree` blob sizes — not from filesystem globbing, because this worktree is a sparse checkout (29,110 tracked files, 3,313 on disk).

---

## 1. The headline ratio

| Bucket | Files | Lines | % of Python |
|---|---:|---:|---:|
| **CORE** — reachable from a current entrypoint | **152** | **288,669** | **21.7 %** |
| CAMPAIGN-only — reachable only via `.hermes` receipts | 53 | 148,269 | 11.1 % |
| TOOLCHAIN_ONLY — imported only by `scripts/`/`research/` | 204 | 178,853 | 13.4 % |
| TEST_ONLY — imported only by `tests/` | 420 | 217,855 | 16.4 % |
| ROOT_ENTRYPOINT_UNIMPORTED — has `__main__`, nothing imports it | 246 | 216,827 | 16.3 % |
| TEST_ROOT_ORPHAN — test file nothing imports | 585 | 416,496 | 31.3 % |
| ORPHAN — zero inbound edges, no `__main__` | 31 | 13,133 | 1.0 % |

Per directory:

| Dir | Total | CORE | Neither CORE nor CAMPAIGN |
|---|---|---|---|
| `src/` | 590 f / 502,490 L | 147 f / 283,368 L | **417 f / 189,993 L** |
| `scripts/` | 417 f / 289,805 L | **4 f / 5,151 L** | **413 f / 284,654 L** |
| `tests/` | 593 f / 419,268 L | 0 | **566 f / 300,128 L** |

**Four of 417 scripts are on a live path.** 385 of 417 (93 % of `scripts/` lines) have not been touched since the hard halt on 2026-06-03.

---

## 2. Concepts with more than one implementation

Measured by AST clone detection (identifier/constant erasure, ≥40 nodes, ≥2 files): **436 clone groups, 12,742 duplicate lines** beyond one canonical copy each.

| Concept | Impls | Behaviour variants | Risk |
|---|---:|---|---|
| **canonical JSON→bytes for sealing** | **40 definitions, 6 distinct `json.dumps` signatures** | 28× `allow_nan=False, ensure_ascii=True`; **3× `allow_nan=True`** (the three semantic-parity comparators); 4× `ensure_ascii=False`; 1× `allow_nan=False, ensure_ascii=False`; 2× `indent=2`; 2× `default=<expr>` | **CRITICAL — verified.** Under `allow_nan=True`, NaN/Infinity serialise to bare tokens and compare byte-equal, so two runs both producing an undefined economic value passed parity while all 28 sealing encoders raised. Demonstrated and fixed — see `IMPLEMENTATION_LEDGER.md` P1 |
| **JSONL reader** | 203 | 94 raise on a malformed line, 84 silently `continue`, 25 other | **CRITICAL** — denominators in any evidence analysis depend on which reader the path used |
| **file SHA-256** | 119 | 6 chunk strategies (1 MiB ×88, 16 MiB ×4, whole-file ×5, …) | low correctness, high maintenance |
| **UTC timestamp parser** | 80 | 63 handle a trailing `Z`, **17 do not** | **HIGH** — the 17 throw on ISO-Z strings the other 63 accept |
| **R-multiple** | 57 | `orchestrator.py:10248` guards `not sl_distance or == 0` and so accepts a **negative** `sl_distance` (sign-flipped R); the three shadow loggers guard `<= 0` | **HIGH — on the live path** |
| **symbol normaliser** | 84 | 10 distinct in CORE alone; `gtos_vnext_runtime.py` has 4 by itself | **HIGH** — family disagreement between the permission gate and the same-symbol lifecycle gate is a double-position hazard |
| **JSONL appender** | 110 | 106 newline-terminate, 4 do not | medium |
| **"is trading allowed"** | 42 | 3 independent CORE predicates with no shared contract | medium-high |
| **cost/spread/slippage** | 356 sites / 118 files | 13 CORE | medium-high |
| **session classifier** | 325 sites / 143 files | 18 CORE | medium |
| exact-hash memo | 2 (`CampaignExactCache._exact_hash_cache`, `_PACKAGE_AUTHORITY_HASH_CACHE`) | same algorithm, different bounds, duplicated `_stable_sha256_material` | medium |

Boilerplate with no shared scaffold: `main()` in **457 files** (416 distinct bodies), `build_parser()` in 109, `write_markdown()` in 79.

---

## 3. Version ladders

Filename-based cleanup finds almost nothing — exactly **one** literal `_v2` sibling pair exists. The ladders are concept-level:

| Family | Members | Lines | Current | Older rungs still present |
|---|---:|---:|---|---|
| `replay_acceleration_*` | 53 | 68,202 | `attempt5_typed_sparse_runner.py` | 14 CORE, 23 CAMPAIGN-only, **16 TEST_ONLY** |
| — `task2…task9` | 13 | 16,763 | task9 | all 13 CAMPAIGN-only, alive only via receipts + mirror tests |
| — `partial_golden` chain | 6 src + 3 tests | 7,730 | `_successor_authority.py` | 2 middle rungs TEST_ONLY |
| **`moonshot_*`** | **179** | **63,646** | **none — 0 CORE, 0 CAMPAIGN** | 162 TEST_ONLY, 17 TOOLCHAIN_ONLY; **178/179 frozen at 2026-05** |
| — `moonshot_expanded_market_*` | 64 | 26,373 | — | `boundary_row()` byte-identical in **56 files**; `as_float()` in 24 |
| `waveN*` | 9 | 17,745 | `wave4r_replay_microstructure.py` | `wave4r_v4_vs_v3_frozen_replay_results_gate.py` (7,189 L) TEST_ONLY |
| legacy/old/frozen-marked | 29 | 30,058 | — | 24/29 have zero non-test importers |

Nothing in the source tree marks which rung is current — only `.hermes` receipts do.

**Frozen single-run route.** `attempt5:15180 require_attempt5_execution_authority` — docstring *"Reject every route except the fresh S0R0 Jan 1-7 parity run"* — hard-pins `arm_id == "S0R0"`, a literal arm fingerprint, a fixed output prefix and date range. The 19,500-line module's nominal public entry (`run_typed_sparse_attempt5`) is therefore dead for every real arm; production enters at `run_replay_engine` (`attempt5:18157`).

---

## 4. The circular proof/execution binding

Discovered by this audit while trying to benchmark: `B7_5_POST_ACCELERATION_DECISION_CONTRACT.json` → `input_bindings.common_behavior_inputs` binds **42 files by SHA-256**, and those hashes feed `common_execution_input_digest_sha256` → `arm_fingerprint_projection` → `arm_fingerprint_sha256` for all four arms.

Nine of the 42 are **verifiers, gates, and acceptance modules that never execute during a replay**:

```
src/research_infra/b7_5_post_acceleration_semantic_verifier.py
src/research_infra/replay_acceleration_task2_semantic_acceptance.py
src/research_infra/replay_acceleration_integrated_source_verifier.py
src/research_infra/replay_acceleration_real_gate.py
src/research_infra/replay_acceleration_real_parity_verifier.py
src/research_infra/replay_acceleration_streaming_archive_verifier.py
src/research_infra/replay_acceleration_task9_final_validation.py
src/research_infra/replay_semantic_diagnostic.py
research/operations/…/verify_denominator_to_deployment_execution.py
```

plus two one-shot builders and `replay_acceleration_task7_isolated_runner.py`.

**Demonstrated:** editing `b7_5_post_acceleration_semantic_verifier.py` — a file that does not run during a replay — caused the next replay to fail closed with
`selection_sizing_decision_contract_input_drift:src/research_infra/b7_5_post_acceleration_semantic_verifier.py`.

> **You cannot repair a bug in a verifier without invalidating the execution contract, regenerating all four arm fingerprints, and re-running every arm.**

This single fact explains why the proof-layer defects found in this audit — the `allow_nan` hole, the `None`-elision hash collision, the hardcoded independence literals — have persisted. The architecture makes fixing them maximally expensive.

Note also which config files are bound: `config/agent_config.yaml`, `config/profiles/ftmo.yaml`, `config/profiles/operator_profile.yaml`. **`config/profiles/redacted_account.yaml` — the live profile — is not bound**, confirming the replay never sees production's risk surface.

---

## 5. Generated evidence in Git

Tracked tree: **29,110 files, 6.3 GB**.

| Class | Files | Size | % |
|---|---:|---:|---:|
| **GENERATED** (json/jsonl/csv/gz/png/log) | 19,069 | **6.1 GB** | **97.0 %** |
| CODE | 4,254 | 100.0 MB | 1.5 % |
| DOC | 5,707 | 91.2 MB | 1.4 % |

- `research/` alone: 20,695 files / 5.1 GB. `research/science_program_2026_05/06_outcome_testing/`: **12,387 files / 3.9 GB (62 % of the repo)**, a May-2026 programme `CLAUDE.md` classes as historical.
- **LFS covers almost none of it.** 4,186 files are LFS pointers; **24,924 files / 6.3 GB are stored inline**, including **280 blobs > 5 MB totalling 4.8 GB** (largest 87.6 MB). The 48 `.gitattributes` LFS globs do not match them.
- **3,821 artifacts / 527.5 MB are referenced by no tracked `.py`/`.md`/`.yaml`** — neither the file nor its containing directory.

---

## 6. Tests

593 files / 419,268 lines / 10,021 test functions — 83 % the size of `src/`.

| Health | Files | Lines |
|---|---:|---:|
| TARGET_CORE | 268 | 325,426 |
| TARGET_TOOLCHAIN | 127 | 57,188 |
| **TARGET_TEST_ONLY_DEAD** | **127** | **24,456** |
| **NO_TARGET** (imports no repo module) | **68** | **11,466** |

**195 files / 35,922 lines / 1,222 test functions exercise modules nothing else uses, or nothing at all.**

By kind (literal-container density + hex-digest count):

| Kind | Files | Lines | Literal-fixture lines |
|---|---:|---:|---:|
| GOLDEN_FIXTURE | 80 | 216,377 | 81,644 |
| MIXED | 182 | 100,844 | 15,535 |
| INVARIANT | 311 | 99,209 | 3,660 |

**100,902 lines (24.1 % of all test code) are literal fixture data.** Golden-fixture files are 13.5 % of test files but **51.6 % of test lines**. Every large test is a 1:1 module mirror, so the 96,047-line replay engine drags a 63,745-line test with it — neither can be refactored independently.

---

## 7. Reachable-but-dangerous routes

| Entrypoint | What it does | Why it matters |
|---|---|---|
| **`start_all.bat`** | 24 × `run_agent.py --symbol X`; lines 62-63 default `GTOS_MODE=live`, `GTOS_PROFILE=redacted_account` | one double-click relaunches the legacy fleet on the broker profile that produced the hard halt |
| **`run_agent.py --mode live`** | real MT5 order flow | its double-book guard scans for a `run_book.py` **process**; `run_book.py` is not tracked in this repo, and the guard is wrapped in `except Exception: pass` |
| **halt check** | the only remaining start block | presence-of-flag-file, CWD-relative (`runtime_halt.py:110`), `default=False` (`:100`); all three flags are sparse-excluded from this worktree, so it reports `runtime_halt_clear` |
| **`scripts/dual_broker_execution_follower.py --replay-existing`** | resets `offset=0` and **re-transmits historical intents to a live account**; zero `runtime_halt` references in 2,832 lines | "replay" means two opposite things in this repo |
| **`scripts/fn_smoke_trade.py`** | real `order_send` at `:347`; `--dry-run` is **opt-in** (`:511`) | default-live smoke trader, no halt check |
| **`scripts/mt5_preflight.py`** | real pending order behind an `input()` prompt; prints "cancel it manually" on failure | no halt check |
| **90 DEAD/ONE_SHOT scripts (97,606 L)** | reference `pipeline_state/`/`shadow_logs/`/`knowledge_base/` **and** open files for write | any accidental run mutates the surface hard-halt forensics treat as evidence |
| `create_mt5` | returned `RealMT5` for any mode ≠ `"mock"` | **fixed in this audit** — see ledger R7 |

**False positive to protect:** `scripts/emergency_close_and_stop_redacted_account.py` scores DEAD on every heuristic but is a deliberate safety tool. Exempt from any bulk deletion.

---

## 8. Deletion plan

Cumulative tiers; each includes the one below plus modules that become import-orphans once that tier is removed.

| Tier | Files | Lines | % of Python | Contents | Precondition |
|---|---:|---:|---:|---|---|
| **LOW** | 607 | **219,469** | 16.5 % | 114 never-referenced scripts (62,713 L) · 31 zero-edge orphans · 195 tests on dead/no targets (35,922 L) · the 283 `src/` modules that lose their last consumer (111,223 L) | none — nothing here is reachable from any entrypoint, receipt, or surviving test |
| **MEDIUM** | 719 | **318,098** | 23.9 % | LOW + all 218 DEAD scripts + the 179-module `moonshot_*` layer (63,646 L) + mirror tests | confirm the May-era moonshot evidence is reproducible from git history |
| **HIGH** | 1,029 | **549,842** | 41.3 % | MEDIUM + 127 ONE_SHOT builders (132,403 L) + 25 unimported `research/operations/*.py` runners (49,523 L, incl. the 26,738-line `build_denominator_to_deployment_execution.py`) + sealed CAMPAIGN ladder rungs | explicit decision that sealed receipts are the authority and their producers are archival |

Independent of Python:
- **527.5 MB** of tracked generated artifacts with no consumer reference — deletable now.
- **4.8 GB** in 280 inline non-LFS blobs > 5 MB — migrate to LFS or drop.
- **100,902 lines** of literal fixture data inside `tests/` — externalisable without losing a single assertion.

### Collapse, not just delete

| Collapse | From | To | Invariant protected today | Is that protection real? | Replacement |
|---|---|---|---|---|---|
| canonical JSON encoder | 40 defs / 6 signatures | 1 module | "evidence bytes are canonical" | **No** — the three parity encoders diverged and created a NaN hole | `src/research_infra/replay_canonical_bytes.py` (**done**, see ledger P1) |
| JSONL reader | 203 | 1 strict + 1 explicitly-lenient | "ledgers parse" | **No** — 84 readers silently skip malformed rows, changing denominators | one reader, `on_error` an explicit argument |
| file SHA-256 | 119 | 1 | none | — | one helper |
| UTC parse | 80 | 1 | "timestamps parse" | **No** — 17 reject the `Z` suffix the rest accept | one parser, fail-closed |
| R-multiple | 57 | 1 | "R is computed consistently" | **No** — the orchestrator's guard admits negative `sl_distance` | one function, `sl_distance > 0` asserted |
| symbol normaliser | 84 | 1 | "symbol families agree across gates" | **No** — 10 CORE variants | one registry |
| receipt schemas | 386 schema names, 1,411 hash-field names, 14 producerless | ~4 primitives: `MANIFEST`, `SEAL`, `COLD_ARCHIVE`, `OWNER_DECISION` | "evidence is bound" | **Partially** — byte binding is real; the input-set closure is chosen by the producer | see `TARGET_ARCHITECTURE.md` §5 |
| verifier/producer binding | 42 files in the contract, 9 of them verifiers | bind only what executes | "the run used sealed code" | **Overreaching** — it also freezes code that cannot affect the run | bind the executing closure; version verifiers separately |

**Estimated concept reduction:** 386 receipt schemas → ~4; 40 canonicalisers → 1; 203 JSONL readers → 2; 119 file-hashers → 1; 80 time parsers → 1; 179 `moonshot_*` modules → 0; 53 `replay_acceleration_*` modules → ~12.
