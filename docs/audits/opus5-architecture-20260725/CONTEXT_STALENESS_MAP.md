# `.context/00_core/` Staleness Map

**27 files. Classified by risk of being mistaken for current authority, not merely by age.**

Produced 2026-07-25 during the Opus-5 audit, after Borhen observed that *"older stale files kinda create
some conservatism due to hard constraints."* The problem turned out to be larger than conservatism: three
April-era files describe a **completely different system** and read as authoritative.

**This map adds information; it removes nothing.** No file was edited, moved, or deleted — the staleness
pattern is itself evidence and a successor auditor should see it raw. This is one auditor's
classification. Verify before relying on any single row.

Note on dates: many files show a git date of 2026-07-12 from a bulk move. **The self-declared content date
is the meaningful one** and is what this table sorts on.

---

## Tier A — describes a system that no longer exists. Highest risk.

| File | Content date | Lines | What it actually describes |
|---|---|---:|---|
| **`architecture.md`** | 2026-03-28 | **3,337** | *"XAUUSD Autonomous AI Trading Agent"*, *"Model A — London Open Liquidity Sweep"*, *"Market: XAUUSD Only"*, *"Status: Design Complete — Ready for Phase 1 Implementation"* |
| **`master_roadmap.md`** | 2026-04-02 | 286 | *"Phase 0: Validate & Go Live (THIS WEEK)"*, and stale edge claims presented as established: *"101 trades, 69.3% WR, +0.235R, p=0.014"* |
| **`pre_lock_final_review.md`** | 2026-04-05 | 216 | WF-1 walk-forward gate review; *"Lock prompt for 3 months or halt for fixes"* |

**Why `architecture.md` is the single most dangerous file in the context tree.** It is 3,337 lines, it is
named `architecture.md`, it sits in the core context directory, and its status line says *"Design
Complete."* Everything about its presentation says *this is the architecture.* It describes a
**single-symbol XAUUSD Model A system** — no vNext, no 24-symbol surface, no selector/scheduler V4, no
`ultimate_book`, no B7.5 factorial, written **two months before the hard halt**. An agent that reads it as
current does not become conservative; it builds the wrong system.

**Why `master_roadmap.md` is dangerous differently.** It states edge performance as settled fact
(69.3 % WR, +0.235R, p=0.014) from the April Model A era. The hard-halt reconciliation records the actual
live outcome: **77 trades, −$859.69, 31 wins / 46 losses**. A plan anchored on the April numbers is
anchored on a claim the live system falsified.

**Superseded by:** `GTOS_ULTRA_GOAL.md` (charter), `live_system_of_record.md` (live model),
`vnext_absolute_moonshot_vision_and_limitations.md` (capability map), and the hard-halt reconciliation
route under `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/`.

---

## Tier B — current authority

| File | Content date | Lines | Role |
|---|---|---:|---|
| `GTOS_ULTRA_GOAL.md` | **2026-07-16** | 241 | **the controlling charter** — mission, culmination standard, activation vocabulary |
| `research_current_state.md` | 2026-06-18 | 5,749 | curated research snapshot; `LIVE_STATE` currently flags it stale vs `a3badc054` |
| `live_system_of_record.md` | 2026-06-16 | 71 | **authoritative for the live model**; declares itself superseding on conflict |
| `vnext_absolute_moonshot_vision_and_limitations.md` | 2026-06-07 | 707 | full capability map + known-limitation register |
| `research_operating_doctrine.md` | 2026-06-07 | 380 | research method |
| `current_vnext_system_map.md` | 2026-06-05 | 66 | oldest of the "current" set; **predates `ultimate_book` and never mentions it** |
| `current_repo_reading_order.md` | 2026-06-04 | 28 | navigation; predates this audit and the ULTRA_GOAL |

---

## Tier C — post-halt operational, still broadly valid

| File | Content date | Lines |
|---|---|---:|
| `final_moonshot_goal_session_execution_architecture.md` | 2026-06-04 | 172 |
| `final_moonshot_post_hard_halt_research_plan.md` | 2026-06-04 | 133 |
| `final_moonshot_central_orchestrator_successor_brief.md` | 2026-06-04 | 91 |
| `mac_migration_package_evidence_index.md` | 2026-06-04 | 87 |
| `portable_path_authority.md` | 2026-06-04 | 49 |
| `repo_cleanup_and_staleness_policy.md` | 2026-05-31 | 38 |
| `quick_reference_card.md` | undated | 61 |

`quick_reference_card.md` is the model for how a pointer doc should behave — it opens by naming what *not*
to treat as current. Its V3 framing is now incomplete (V4 and `ultimate_book` exist), but it is
self-aware about its own scope.

`final_moonshot_post_hard_halt_research_plan.md` names the June work programme (hard-halt forensic join,
V3-vs-live authority audit, dual-broker audit). **The active programme is now the B7.5 factorial** per the
charter. Read it as history of intent, not as the current queue.

---

## Tier D — method and tooling, largely time-independent

| File | Content date | Lines |
|---|---|---:|
| `gtos_context_os.md` | undated | 661 |
| `research_operating_doctrine.md` *(also Tier B)* | 2026-06-07 | 380 |
| `goal_session_research_discipline.md` | 2026-05-10 | 300 |
| `orchestrator_successor_operating_brief.md` | 2026-05-15 | 292 |
| `gtos_second_brain.md` | undated | 163 |
| `llm_specialization_research_backlog.md` | 2026-05-10 | 141 |
| `ai_in_loop_cost_control_research_plan.md` | 2026-05-10 | 135 |
| `parallel_goal_merge_playbook.md` | 2026-05-15 | 108 |
| `orchestrator_methodology_hardening_controls.md` | 2026-05-15 | 100 |
| `local_heavy_data_inventory.md` | 2026-05-10 | 85 |
| `r7_failure_intelligence_doctrine_addendum.md` | 2026-05-15 | 42 |

Method docs age more slowly than state docs. Treat as advisory. `gtos_second_brain.md` points at an
external vault (`/Users/borr/Documents/gtos/second-brain`) outside this repo.

---

## How to use this

1. **Any constraint that seems to block work should be date-checked before it is obeyed.** If it predates
   `GTOS_ULTRA_GOAL.md` (2026-07-16) and conflicts with it, the charter wins.
2. **Tier A is not a source of truth about the system.** It is a source of truth about what the system
   used to be, which is occasionally useful and frequently misleading.
3. The owner's standing direction (`OWNER_SESSION_CONTEXT.md` §4) is to **build the system rather than
   patch around it**. A stale document is not a constraint on that.
4. ~~Nothing here was deleted.~~ **ACTED ON 2026-07-26 by the Phase-0 implementation session.**

---

## What was done, 2026-07-26

The owner asked for a context tree a fresh session can trust. The call this map left open is now made,
in two stages, because deleting Tier A today would corrupt an investigation that has not run yet.

**Stage 1 — done.** All three Tier A files now open with an unmissable `HISTORICAL — NOT CURRENT
AUTHORITY. Do not build from this file.` banner naming what they describe, why it is dead, and what to
read instead. This is `quick_reference_card.md`'s model, which this map already praised. It removes the
*danger* — an agent mistaking them for current — without changing the file set.

Also: `current_vnext_system_map.md` and this map were **removed from `CLAUDE.md`'s mandatory preflight**
and demoted to conditional reads. A superseded document does not belong in a required read order, and
with Tier A self-labelling, a session no longer needs this map to avoid the trap.

**Stage 2 — DONE, 2026-07-26.** Session C reported, and all three files are deleted.

The blocker was real and it was measured rather than assumed. All three are **hardcoded by path** in
`scripts/build_gtos_vnext_master_conversion_ledger.py` (`:31724`, `:31816`, `:31909`), and that builder
enumerates via `git ls-files` then skips paths that do not exist — so deleting them drops ledger rows.
It does: **1,354 → 1,351**. What it does *not* do is move any assertion. A/B by failure **set** over the
three test files that consume `build_rows()`: **193 bad → 193 bad, 0 fixed, 0 regressed** [MEASURED].
`git grep` over `tests/` for the three filenames returns **zero** hits.

Stamping had been verified inert first, by the same method: the builder branches on **filename**, not
content, and an A/B over `test_gtos_vnext_master_conversion_ledger.py` + `test_gtos_vnext_runtime.py`
gave **299 → 299, 0 regressed, 0 fixed** [MEASURED].

Intelligence was extracted before deletion, per `repo_cleanup_and_staleness_policy.md` §8, and the
HISTORICAL banners were themselves the extraction record: `pre_lock_final_review.md`'s one live finding
(**the AI adds ~0pp to entry win rate** — what drove the de-LLM-ing of GTOS) is in `SECOND_AUDIT.md`
§3.6; `master_roadmap.md`'s April edge claim survives as the falsified comparand against the hard-halt
reconciliation's 77 trades / −$859.69 / 31 W-46 L. Git history is the deep archive.

Full record: `docs/audits/fable5-vision-audit-20260725/phase1/DELETION_MANIFEST.md` §5.
