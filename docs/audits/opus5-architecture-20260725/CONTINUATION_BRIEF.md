# GTOS Continuation Brief

**Self-contained handoff. A session can start cold from this file.**
Written 2026-07-25 at the close of the Opus-5 independent architecture audit, branch
`audit/claude-opus5-architecture-20260725`.

---

## 0. Start here

0. Read `OWNER_SESSION_CONTEXT.md` — the owner's direction in his own words, including the central
   mandate: build the system, do not patch around it.
1. Read `CLAUDE.md` §1–3 (purpose, preflight, hazards). The hazards section will save you a day.
2. Read `FINAL_INDEPENDENT_AUDIT.md` in this directory (~20 min).
3. Do the falsification gate in §2 below. **Time-box it to one hour.**
4. Then build, per §4. Do not re-audit.

---

## 1. What is established

These are evidence-bound and reproducible. Treat them as given unless the gate in §2 breaks them.
Every one carries `file:line` or a re-runnable receipt in `MISMATCH_AND_RISK_REGISTER.md`.

| # | Established | Consequence |
|---|---|---|
| E1 | Replay implements a portfolio allocator, Selector V4 admission, and continuous sizing that the live path does not have | replay R does not transfer to production |
| E2 | `run_book.py`, the live entrypoint, is not in the repository | no live-behaviour claim is auditable |
| E3 | The proof layer verifies bytes, never economics (`parse_json=False` by design) | a wrong arm and a right arm are indistinguishable to it |
| E4 | No sealed Phase-D arm has a semantic parity proof; the only comparator is hardwired to the June fixture with no CLI | January/April parity is un-runnable without editing the verifier |
| E5 | Proof/attribution is 60.6 % of replay CPU; `evaluate_candidate_v4` is 8.3 % of wall | the replay is slow because of evidence, not economics |
| E6 | One arm emits 15.75 GB of JSON for 148 orders / 72 trades; an order row is 494 KB, 1,274 keys, 765 distinct values, 63.8 % key names | the row schema is the cost driver |
| E7 | The decision contract binds 42 source files by hash, 9 of them verifiers that never execute | proof-layer fixes cost a campaign re-run |
| E8 | Memory, not CPU, is the binding constraint: 15.3 GB peak on a 17.2 GB machine | parallel arms are impossible until this is fixed |
| E9 | 21.7 % of 1.33 M Python lines is reachable; 219,469 lines are LOW-risk deletable | — |
| E10 | The vision (feature store → label store → daily learning loop) needs ~30× throughput, not ~3× | this forces a rebuild rather than an optimisation |

Adversarially narrowed, so do not overstate these: the hindsight blocklists are **annotate-only**
(`exact_block_rules_mode: "diagnostic"`); the sleeve registry is an **unhydrated LFS pointer**; NAS100 has
**zero order rows** in any sealed arm; the acceptance gates are **not vacuous** — they establish that a
receipt is the honest output of pinned code over on-disk inputs.

---

## 2. Falsification gate — do this first, one hour

**E1 is load-bearing.** If it is wrong, most of the plan below is unnecessary and the right move is to
finish April/May/March on the current engine. Attack it before building on it.

Specifically, try to break:

- **E1a** — `evaluate_selector_v4_admission` (`src/components/selector_v4.py:3543`) has no production
  caller. Trace every caller of `gtos_vnext_runtime.evaluate_vnext_selector_v4_admission`. Check the
  `ultimate_book` path (`book_owner.py`, `admission.py`, `execution_packets.py`) — note it *fabricates*
  selector/scheduler packets rather than calling them.
- **E1b** — `orchestrator.py:1310-1328` is first-wins with no ranking before the loop.
- **E1c** — Scheduler V4 `runtime_effect` is always `False`
  (`moonshot_scheduler_v4_best_trade_allocator.py:28022-28026`) because
  `scheduler_v4_..._live_activation_allowed: false` at `config/agent_config.yaml:963`.
- **E1d** — live sizing quantises to broker lot step and rejects below minimum
  (`execution.py:9080`, `:2323`, `:3396-3401`); replay uses continuous `risk_cash / |entry−stop|`
  (`v4_timewarp_simulated_live_research_loop.py:6497`).

**If E1 holds:** record it and never revisit. Proceed to §4.
**If E1 breaks:** stop and tell Borhen. The plan changes.

E5 is independently re-checkable: `receipts/profile_jan01_02_sampled.json` plus
`receipts/wallsampler.py` and `receipts/profile_day_harness.py` reproduce the profile in ~10 minutes.

---

## 3. Queued behind a contract re-seal

Fixed, tested, and **not landed** because the files are contract-bound (E7). Each is pinned by a
characterisation test that fails when the contract is re-sealed — that failure is the signal to land it.

| Item | Where | Test that unblocks it |
|---|---|---|
| `allow_nan=True` NaN-equality hole in two of three parity comparators | `b7_5_post_acceleration_semantic_verifier.py`, `replay_acceleration_task2_semantic_acceptance.py` | `test_characterise_contract_bound_comparators_still_use_the_old_encoder` |
| Authority hash: `None`/`""` elision collides with absence; 12dp float rounding; set → `PYTHONHASHSEED`-dependent digest (incl. frozenset **dict keys**) | `moonshot_scheduler_v4_best_trade_allocator.py:_canonical_hash_payload` | `test_characterise_authority_hash_defects_remain_unfixed` |

**Owner decision D1:** re-seal forward-only (April/May/March on the new contract, January stays as-is,
costs nothing) or re-attest January too (~16.5 h). Recommend forward-only.

---

## 4. Build order

Each phase has a gate. Do not start the next until the gate passes.

### P0 — Unblock (days, no replay cost)
- Vendor `run_book.py` into HEAD from the VPS branch.
- Split the contract's `input_bindings` into `executing_closure` (bound) and `verification_tooling`
  (versioned). One regeneration; every future proof fix becomes free.
- Land the §3 queue under the new contract.
- **Gate:** a contract-bound-file check passes, and `run_book.py` is readable in HEAD.

### P1 — Independent economics check (3–5 days, no replay cost)
Build the **shadow reducer**: ~400 lines, zero shared imports with the engine, recomputing
`scoreable_net_cash`, `total_accepted_risk_cash`, `physical_net_r`, `trade_count`,
`scoreable_risk_coverage` directly from the trade and order ledgers.
- **Run it against the sealed January arms you already have.** Highest value per hour in the plan: the
  first independent check that the numbers are right, against evidence that already exists.
- **Gate:** it agrees with the analyzer on all four January arms, or it does not and you have found a real
  economic defect. Either outcome is a win.

### P2 — Divergence matrix (2–3 days, no replay cost)
Publish replay-vs-live divergence as a first-class artifact beside every arm receipt.
- **Gate:** no arm receipt ships without it.

### P3 — Memory (1–2 weeks)
Collapse the 5× bar / 4× tick materialisation (`OVERENGINEERING_AND_DELETION_MAP.md` §2, audit R20).
Target: peak footprint 15.3 GB → under 4 GB.
- **Gate:** exact ledger SHA-256 parity on the Jan 1–2 fixture, plus 4 concurrent arms without swap.
- **Payoff:** month-window 16.5 h → ~4.5 h.

### P4 — One decision core + differential harness (3–4 weeks)
Pure core, three ports (`Clock`, `Broker`, `Sink`), attached at the existing injection seam
(`run_campaign:90494-90499`) so the old engine keeps running throughout. Build the differential harness
alongside: every commit runs both engines over every sealed window and diffs canonical outputs.
- **Falsification gate:** the slice must reproduce one symbol, one day exactly. If it cannot, the
  decomposition is wrong — stop and report. Two weeks to an answer otherwise worth months of argument.

### P5 — Evidence as projection (4–6 weeks, only after P4)
Typed fixed-width events from the loop; ledgers, scorecards, and authority blobs become derived views.
- **Gate:** the offline projection reproduces today's ledgers byte-for-byte.
- **Payoff:** dense day ~507 s → ~80–150 s; the 180 s target becomes arithmetic.

### P6 — Feature and label stores, then the daily loop
Columnar, content-addressed, immutable; labels joined by **one carried identity**, never reconstructed.
Both fall out of P5 rather than being new systems.
- **Gate:** a 2-year 4-arm sweep completes in hours, not weeks.

### P7 — Continuous forward shadow → canary readiness
The charter's `FORWARD_SHADOW_ACTIVE` rung, always on, same core, real data, simulated lifecycle. Becomes
the permanent source of execution truth that calibrates replay costs — closing the loop where replay
slippage is currently a hand-maintained config constant.

---

## 5. Working rules for whoever continues

- **A/B against the parent commit before claiming no regressions.** 11 tests already fail at HEAD from an
  unhydrated LFS pointer; a subset run will mislead you. This audit made exactly that mistake.
- **Check contract-bound membership before editing `src/`.** The check script is in `CLAUDE.md` §3 H1.
  This audit documented that trap and then walked into it.
- **Prefer behavioural tests.** Four tests written during this audit asserted on source strings and one
  used a list where it claimed to test set handling — it passed identically before the fix.
- **Adversarial review is a whetstone, not a hammer.** Two verifier passes changed four severity ratings
  here and a third caught two real regressions. Brief them to *refute with `file:line`*, not to improve.
- **State which decision a new verifier changes** before adding it. That is the charter's own test.

---

## 6. Measured reference numbers

| Quantity | Value | Source |
|---|---|---|
| dense day, economic path, uncontended | 507.6 s | `receipts/bench_baseline_uncontended.json` |
| no-event day, economic path | 1.7 s | four sealed January arm summaries |
| fixed per-process startup | 63.0 s wall / 109.0 s CPU | measured directly |
| one month, four arms, chunk time | 14.10 h | sealed January `progress_rows` |
| one month, four arms, full wall | 16.45 h | arm receipts |
| peak memory, one arm | 15.32 GB footprint / 8.61 GB RSS | `/usr/bin/time -l` |
| proof share of replay CPU | 60.6 % (lower bound) | `receipts/profile_jan01_02_sampled.json` |
| `evaluate_candidate_v4` share of wall | 8.3 % | same |
| exact-parity optimisation available | 2.19× on canonicalisation, 0 mismatches / 296 real payloads | `receipts/micro_parity.txt` |
| machine | 10 cores, 17.2 GB RAM, Python 3.14.4 | — |

---

## 7. Open threads

| # | Question | Why it matters |
|---|---|---|
| U1 | What does `run_book.py` actually do? | blocks every live-behaviour claim |
| U2 | Rate of `duplicate_exact_candidate_instance` drops | silent candidate loss of unknown size |
| U3 | Is `scheduler_dynamic_daily_drawdown_budget_enabled` on in the sealed arms? | decides whether lexical order materialisation (R8) ever binds |
| U4 | True cold end-to-end cost of one arm, including `build-pack` | every published number assumes warm derived caches |
| U5 | Hydrate the sleeve registry LFS object and re-run `tests/test_selector_v4.py` | 10 of the 11 pre-existing failures |
