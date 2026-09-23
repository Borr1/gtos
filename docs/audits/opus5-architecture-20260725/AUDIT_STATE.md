# GTOS Independent Architecture Audit — Live State

**Worktree:** `/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725`
**Branch:** `audit/claude-opus5-architecture-20260725` (from `a3badc054`)
**Started / last updated:** 2026-07-25

---

## Status: COMPLETE — all deliverables written, fixes landed, adversarially reviewed

Reading order: `FINAL_INDEPENDENT_AUDIT.md` → `MISMATCH_AND_RISK_REGISTER.md` → `REPLAY_TRUTH_AND_PERFORMANCE_AUDIT.md` → `TARGET_ARCHITECTURE.md`.

---

## Deliverables

| File | State |
|---|---|
| `AUDIT_STATE.md` | this file |
| `SYSTEM_TRUTH_MAP.md` | done — components, call chains, boundaries, authority/lineage graph, measured scale |
| `MISMATCH_AND_RISK_REGISTER.md` | done — 37 findings in 4 tiers, adversarial corrections folded in and marked |
| `OVERENGINEERING_AND_DELETION_MAP.md` | done — reachability buckets, duplicate concepts, 3-tier deletion plan |
| `REPLAY_TRUTH_AND_PERFORMANCE_AUDIT.md` | done — sampled profile, row anatomy, lower bound, optimisation experiments |
| `TARGET_ARCHITECTURE.md` | done — minimal core, ports, 4-stage migration with a falsification gate |
| `IMPLEMENTATION_LEDGER.md` | done — 5 fixes, 5 characterisations, measurements, blocker, owner decisions |
| `FINAL_INDEPENDENT_AUDIT.md` | done — executive conclusion and activation path |
| `receipts/` | sampled profile, uncontended baseline, micro-parity benchmark, harness source |

## Method

- 7 parallel investigation agents (monolith anatomy, acceleration stack, decision chain, config authority, proof machinery, live/replay parity, dead paths).
- 2 adversarial verifier agents instructed to **refute** 12 highest-stakes claims, defaulting to REFUTED. Result: 3 confirmed, 7 narrowed, 1 refuted as stated, 1 severity-reduced. All corrections folded in and marked.
- Direct measurement: 4 ms sampled profile of a real sealed replay (86,945 samples), uncontended end-to-end benchmark, row-level ledger anatomy, exact-parity micro-benchmarks.

## Key measured facts

| Fact | Value |
|---|---|
| Python in repo | 1,331,674 lines / 1,637 files |
| Reachable from a current entrypoint | **21.7 %** (152 files, 288,669 lines) |
| Largest module | `v4_timewarp_simulated_live_research_loop.py` — 96,047 lines |
| Proof/evidence/type-check share of replay CPU | **60.6 %** (lower bound) |
| `evaluate_candidate_v4` share of wall | **8.3 %** |
| Evidence per arm | **15.75 GB** for 148 orders / 72 trades |
| Order row | 494,196 B, 1,274 keys, 8,091 leaves → **765 distinct values**, 63.8 % key names |
| Uncontended Jan 1–2 baseline | **603.678 s** wall; dense economic path **507.638 s**; peak RSS 8.61 GB |
| No-event economic path | **1.7 s** (5 s target passes; reported 52.5 s "miss" is startup) |
| Fixed per-process startup | **63.03 s** wall / 108.98 s CPU |
| Exact-parity optimisation | **2.19×** canonicalisation, 0 mismatches over 296 real payloads |
| Four-arm parallelism (already built, unused) | **3.7×** campaign speedup, zero semantic change |

## Changes landed

Fixes P1–P5 with tests: parity `NaN` hole, authority-hash set non-determinism, `_modify_tp` halt gap, `create_mt5` unknown-mode fallthrough, `max_gap_pct` truthiness. 101 tests pass; **zero regressions** (11 failures in `test_selector_v4.py`/`test_permissions.py` are pre-existing on clean HEAD — unhydrated LFS sleeve registry).

New: `src/research_infra/replay_canonical_bytes.py`, `tests/test_opus5_architecture_audit_hardening.py`.

## Blocker recorded (finding R37)

The decision contract binds 42 source files by SHA-256, feeding all four arm fingerprints — including nine verifiers that never execute. Editing a verifier makes the next replay fail closed with `selection_sizing_decision_contract_input_drift`. **P1 and P2 cannot ship into the campaign without regenerating the contract and re-running every arm.**

## Open threads for a successor

| # | Thread |
|---|---|
| U1 | Vendor `run_book.py` — blocks every live-behaviour claim |
| U2 | Count `duplicate_exact_candidate_instance` drops in the existing decision ledgers |
| U3 | Is `scheduler_dynamic_daily_drawdown_budget_enabled` on in the sealed arms? Decides R8's magnitude |
| U4 | One measured `derived_cold` end-to-end run — never done; all published numbers assume warm caches |
| U5 | Hydrate the sleeve registry LFS object and re-run `tests/test_selector_v4.py` |

## Artifacts created outside `docs/`

- `audit_runs/` — local copies of sealed January inputs and the contended reference run. Not for commit; delete when finished.
- `.hermes/evidence/phase-d/january-post-acceleration-source-…/` — local copy of sealed evidence used to demonstrate the absolute-path binding failure. Not for commit.
