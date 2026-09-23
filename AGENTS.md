# Gold Traders Operating System (GTOS) — Agent Instructions

Owner/CEO: Borhen.

> **PARTIALLY STALE — READ `CLAUDE.md` FIRST. Banner added 2026-07-27 by the wave-3 hygiene session.**
>
> **`CLAUDE.md` is the authority. Where this file disagrees with it, this file is wrong.** They were
> one briefing; `CLAUDE.md` was rewritten on 2026-07-27 for wave 3 and this copy was not, so it is a
> stale fork that a non-Claude agent could act on. The specific divergences measured at that date:
>
> 1. **The program named in §4 below is PARKED.** This file says the program is "B7.5 cross-window
>    selection–sizing decomposition". It is not, as of 2026-07-27: the active program is the
>    **activation-candidate decision (OD-3)** — re-cost the W7 book's validation at broker-true costs,
>    port candidate generation, answer G4. The B7.5 campaign is banked and parked with a price.
>    `docs/audits/fable5-vision-audit-20260725/THIRD_REVIEW.md` §4 is the controlling plan, approved
>    in full by Borhen on 2026-07-27. **This file does not mention that document at all.**
> 2. **"The entire brake is one config line" (§4) is wrong — it is three.** `apply_to_execution`,
>    `live_activation_allowed` and `live_broker_authority`, at exported working-tree
>    `agent_config.yaml:1161-1163`. Corrected in `CLAUDE.md` on 2026-07-27.
> 3. **H3 was wrong in three ways** and is struck and corrected in place below.
> 4. **`scripts/mt5_preflight.py` no longer places orders at all.** Its order-placing arm was
>    **retired** by Session I on 2026-07-27 and merged in wave 3 (`mt5_preflight.py:48-50` refuses both
>    `--test-order` and `GTOS_MT5_PREFLIGHT_TEST_ORDER=1`; test 5 uses `mt5.order_check`). This item
>    previously read "it is default observation-only, and ungated when armed", which described the
>    state *before* the retirement; H6 in the body is corrected too. Updated 2026-07-28 (B180).
>    **Scoped 2026-07-29 at wave-4 integration (B361): that is true of THIS repository and false of
>    the VPS.** Both VPS repo trees still carry four raw `mt5.order_send` calls at
>    `mt5_preflight.py:136, 142, 152, 155` — verified in the read-only 2026-07-25 export and at the
>    live-lineage commit `redacted_host`. The retirement is on mainline only and has not been carried. A
>    non-Claude agent acting on the unscoped sentence would conclude the live host is safe from a
>    path that is still there, which is the exact reason this banner exists.
> 5. **Four figures were propagated from `CLAUDE.md` on 2026-07-28** at wave-3 integration, because a
>    second root briefing that disagrees with the first is worse than one that is merely old: the tick
>    row count (191.9 M → 263,894,769, B114), `run_book.py`'s size (18,032 → 19,886 bytes, B181),
>    the halt being three false booleans rather than one, and H6 above. **The rest of this file is
>    still un-reconciled** — the queued full pass is not done.
>
> Everything else here was last reconciled 2026-07-25 and has not been re-verified against the wave-3
> tree. A full reconciliation of this file against `CLAUDE.md` is queued, not done.

This file is a root briefing. Last reconciled 2026-07-25 against source, config, and the sealed
campaign evidence during the Opus-5 independent architecture audit; partially amended 2026-07-27.

---

## 1. What GTOS is for

**Read this before deciding what to work on.** GTOS is not a backtester. Per `.context/00_core/GTOS_ULTRA_GOAL.md`
(2026-07-16, the newest and controlling charter) it is a compounding trading-intelligence and execution
system whose destination is: replay at scale → feature store → label store → trained models → default-off
runtime intelligence → daily learning loop → command center → controlled broker-real activation → first
payout → repeatable payouts → scaling toward Borhen's financial independence.

Two lines from that charter govern prioritisation and are quoted here because the codebase has drifted
from them:

- **"Profitability is the mission. Truth is its measurement substrate."**
- **"Activation movement is prior to scaffolding. Infrastructure and checkpoints support the mission;
  they do not culminate it."**

Proof, verification, and evidence machinery earn priority only when they unlock a decision, expose an
economic defect, or move the system toward operation. They are not the product.

---

## 2. Mandatory preflight

Run and read in this order. The ordering is by **authority recency** — later documents supersede earlier
ones where they conflict, and each says so itself.

1. `python3 scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md` — mechanical current state. Caveat: it renders **base config only**, with no
   profile or instrument overlay (`scripts/generate_live_state.py:394-399`), so its "Active config" table
   does not show the values any live process actually uses. Its enforcement-count column is a regex
   heuristic, not proof.
3. `.context/00_core/GTOS_ULTRA_GOAL.md` (2026-07-16) — **the controlling charter.** What the system is
   for, the culmination standard, and the activation vocabulary.
4. `.context/00_core/live_system_of_record.md` (2026-06-16) — **authoritative for the live model.** It
   states explicitly: "Where a config/doc disagrees with this file, THIS FILE is correct and the other is
   stale." It supersedes older primary/follower phrasing, including any that survives elsewhere.
5. `.context/00_core/research_current_state.md` (2026-06-18) — curated research snapshot. If `LIVE_STATE`
   flags it stale, read the newer route artifacts directly.
6. `.context/00_core/vnext_absolute_moonshot_vision_and_limitations.md` (2026-06-07) — the full capability
   map and the known-limitation register. Use it as the hypothesis space.
7. `docs/audits/opus5-architecture-20260725/OWNER_SESSION_CONTEXT.md` — the owner's direction in his own
   words: what GTOS is for, the sequencing decision, and the standing mandate to **build the system rather
   than patch around it**. Short, and it governs how you choose work.
8. `docs/audits/opus5-architecture-20260725/FINAL_INDEPENDENT_AUDIT.md` — independent architecture,
   correctness, and performance audit. Read before proposing architecture work; it will save you weeks.
9. `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md` — the **second independent audit
   (Fable 5)**: verdicts on the first audit's ten claims, corrections (H1-H3 above were amended from
   it), and the layers the first audit never examined — the two-stacks finding (the sealed replay
   measures a strategy family the go-live dossier ordered off; the declared live W7 book is
   unmeasured by any replay), the broker-time-labeled-as-UTC data defect, the live-lineage fork
   (entrypoint + safety companion + evidence of record on the VPS/deploy-live branches only), and the
   dormant-but-sound learning stack. Its `FULL_VISION_PLAN.md` is the sequenced path to activation
   and payout, with the two owner decisions (OD-1/OD-2) it starts from.
10. Latest numbered handoff in `.context/02_session_handoffs/` — **historical context only.**

**Not in the preflight, and deliberately so.** `.context/00_core/current_vnext_system_map.md`
(2026-06-05) predates the `ultimate_book` live surface and never mentions it — read it only if you need
the pre-book component inventory. `docs/audits/opus5-architecture-20260725/CONTEXT_STALENESS_MAP.md`
classifies all 27 core context files; its Tier A — `architecture.md`, `master_roadmap.md`,
`pre_lock_final_review.md` — was **deleted on 2026-07-26** once Session C measured that removing them
moves nothing (`DELETION_MANIFEST.md` §5.1: 193 bad → 193 bad, 0 regressed, by failure set). Git history
is the archive. Consult the map when a `.context/` file's authority is unclear.

For substantial coding, research, validation, or route work, after the reads above:

- rebuild the catalog: `python3 scripts/gtos_context.py build`
- generate and read a task pack: `python3 scripts/gtos_context.py pack --task "<active task>" --profile ultimate --include-memory`
- add `--route <route_name>` when the task is route-owned
- treat Context OS output as retrieval guidance, never as authority over current disk files

Also read before the corresponding work:

- research/validation: `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`
- orchestration / subagents / merges: `.context/00_core/orchestrator_successor_operating_brief.md`,
  `.context/00_core/orchestrator_methodology_hardening_controls.md`, `.context/00_core/parallel_goal_merge_playbook.md`
- cleanup / deletion: `.context/00_core/repo_cleanup_and_staleness_policy.md`

Never reconstruct state from chat memory. After compaction, interruption, long waits, or tool crashes,
repeat the relevant reads from disk. For subagents, pass a Context OS task pack or exact
`gtos_context.py search` / `route` commands rather than asking each agent to rediscover the repo.

---

## 3. Hazards — read before editing anything under `src/`

These are operating traps that have already cost real time. Each is evidence-bound; see the audit's
`MISMATCH_AND_RISK_REGISTER.md` for the full entry.

**H1 — The decision contract binds paths by SHA-256, and those hashes feed all four arm fingerprints.**
Editing **any** bound file makes the next replay fail closed with
`selection_sizing_decision_contract_input_drift`.

**Two generations exist. Use R2 for anything forward.** OD-2 landed 2026-07-26:

- **R2 — `…/B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json`** — **43 bound paths**.
  The contract of record for April/May/March and every learned-arm campaign. Pass it to
  `--decision-contract`. It moved two never-executing verifiers into `input_bindings.verification_tooling`,
  which the enforcement loop does not read, so **verifier fixes are now free**.
- **R1 — `…/B7_5_POST_ACCELERATION_DECISION_CONTRACT.json`** — 44 bound paths. January's contract of
  record; sealed, accepted, and deliberately untouched. It now reports **4 drifted** here (the two
  verifiers P1 fixed, plus the two JSONL ledgers that resolve against `/Users/borr/GTOSActive/repo` —
  see B2/B3). Re-running a January arm under R1 means restoring the two verifiers' sealed bytes first.

Check membership before editing anything under `src/` (defaults to R2):

```bash
python3 - <<'EOF'
import json,hashlib,pathlib
R2='research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json'
d=json.load(open(R2))
for g in ('common_behavior_inputs','package_authority_inputs'):
    for r in d['input_bindings'][g]:
        p=pathlib.Path(r['path'])
        if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:
            print('DRIFTED:',r['path'])
print('unbound verification tooling (free to edit):',
      [r['path'] for r in d['input_bindings']['verification_tooling']])
EOF
```

Still true after OD-2: **seven other never-executing verifiers stay bound**, because
`code_authority_paths` (`replay_acceleration_attempt5_typed_sparse_runner.py:1405-1431`) binds them a
second time from inside an executing file. They are listed in R2's `verification_tooling_deferred` with
that reason. Landing a change to a genuinely bound file still requires regenerating the contract and
re-running the affected windows (~16.5 h per window).

**H2 — The test suite is not green at HEAD, and the standing explanation was wrong.** 10 tests fail
in `tests/test_selector_v4.py` on a clean checkout. The Fable audit hydrated the sleeve-registry LFS
pointer (that fixed exactly one other failure, in `test_permissions.py`); the remaining 10 are a
**real, pre-existing package-admission defect** — `package_execution_fill_probability` resolves
`None` (`selector_v4.py:4004-4016` never consults `entry_quality_fill_probability`) — filed as F13
in `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md` and queued for a decided fix.
**Always A/B against the parent commit before claiming "no regressions."** Do not chase these as your
bug, but do not repeat the LFS explanation either.

**H3 — Memory is a constraint, and the ≤3 GB/arm target was aimed at the wrong subsystem.
Corrected 2026-07-27; the prior text of this hazard was wrong in three ways and is struck.** This
file lagged `CLAUDE.md` §3, which is the authority; the two now agree.

- ~~"the oft-quoted '15.3 GB footprint' is a GiB/GB unit echo of the same measurement"~~ — **false.**
  `/usr/bin/time -l` emits both `maximum resident set size` *and* `peak memory footprint`;
  15.32/8.61 = **1.779**, not the 1.0737 a GiB→GB conversion gives. Two fields, two measurements.
  (B81/B83; struck by `THIRD_REVIEW.md` §7.1.)
- ~~"One replay arm peaks at 8.61 GB maxrss"~~ — **mis-scoped.** 8.61 GB is a **2-day fixture**
  (`day: 2026-01-01`, `end_day: 2026-01-02`, 603.7 s), not a month arm. **No month-arm RSS
  measurement exists anywhere.** Do not quote it as one.
- ~~"until the 5×-materialisation finding is fixed (target ≤3 GB/arm)"~~ — **the target is withdrawn,
  not re-derived.** It came from a wrong causal story. Session G killed every source-layer copy,
  proved output identity over 1.78 M rows, and the arm did not shrink (B84/B85).

**Where the memory actually is** [MEASURED, `THIRD_REVIEW.md` §A1 — `tracemalloc` at the Python-heap
high-water mark of the sealed 2-day S1R1 fixture]: `v4_timewarp_simulated_live_research_loop.py`
per-day row/attribution accumulation **3,866 MB (60.6 %)**;
`moonshot_scheduler_v4_best_trade_allocator.py` 614 MB (9.6 %); retained day-pack JSON 401 MB (6.3 %);
**source layer 99 MB (1.6 %)**. The evidence machinery is simultaneously the memory, the CPU and the
bytes — one redesign, three resource problems. No source-layer work can move the arm peak.

Two concurrent arms are measured ~1.1–1.3× net. Still do not launch parallel replays here — but the
reason is the 6.4 GB of evidence accumulation, not the source layer.

**H4 — Sealed authority binds absolute paths.** Byte-identical evidence copied to another worktree is
rejected (`fresh_source_authority_path_binding_mismatch`). `replay_acceleration_attempt5_typed_sparse_runner.py:186-190`
hardcodes `/Users/borr/GTOSActive/repo` and a `~/Documents/...` tick manifest. Replays only run from the
producing worktree, on this machine.

**H5 — No sub-window replay exists.** Three independent assertions force a full sealed month. Debugging one
day costs a full arm. The engine's own `engineering_stop_after_day` bounded mode is hardcoded to `None` on
the sealed path (`b7_5_post_acceleration_runner.py:832`).

**H6 — "Replay" means two opposite things.** `scripts/dual_broker_execution_follower.py --replay-existing`
**re-transmits historical intents to a live broker account**. Amended 2026-07-26: it now checks the halt
itself with the guard armed (`enabled_default=True`) immediately before its only `open_trade` call, so
coverage no longer depends on a config key that defaults False in two places (C3). `fn_smoke_trade.py`
drives the raw `MetaTrader5` module and is now gated on the same authorization the engine uses.
`scripts/mt5_preflight.py` **no longer places orders at all — retired 2026-07-27 by Session I, merged
in wave 3.** `--test-order` and `GTOS_MT5_PREFLIGHT_TEST_ORDER=1` both print `RETIRED_ARM_MESSAGE` and
`raise SystemExit(2)` (`mt5_preflight.py:48-50`); test 5 now uses `mt5.order_check`, which validates
without mutating (`:147`, `:167`). The refusal covers the env var as well as the flag. (Struck: "is
**still** default-live with no halt check — it is the remaining hazard in this family." That phrasing
was already stale before it was overtaken by the retirement — see the amendment note at the head of
this file.) All of them stay on the never-execute list regardless.

**H7 — Replay does not measure the live system.** Replay runs a portfolio allocator, Selector V4 admission,
and continuous sizing that the live path does not implement. Do not transfer replay R to a production claim
without the divergence matrix in the audit.

---

## 4. Current truth

> **Plan position, 2026-07-26 (evening).** Phase 0 complete. **Phase 1 is 3 of 5** — item 1 (shadow
> reducer, gate G1a, filed defect **F31**), item 3 (live-path tests) and item 5 (clock truth) are done;
> **items 2 (W7 forensics, gate G1b) and 4 (divergence matrix v2) are outstanding.** **Phase 2 is 1 of 6**
> — the differential harness is revived; `BroadV4Policy`, `SleeveBookPolicy`, sub-window replay and the
> columnar layer are not. **Gate G2 is not met.** Everything from the four Phase-1/2 sessions plus the
> integration review is merged to `main` (`ba6164e9c`), A/B'd at **507 bad → 507 bad, zero regressions**.
> Full detail in `docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` blocks **B1–B99e**. (This said `B1–B58`; no B58 block has ever existed — see the numbering note at the head of that file.)

- **Program — SUPERSEDED 2026-07-27. Do not pick up work from this bullet.** ~~B7.5 cross-window
  selection–sizing decomposition (`GTOS_ULTRA_GOAL.md`). Resolve whether economic gain comes from
  portfolio selection at equal risk, from dynamic risk/cash expression, or their interaction — then
  carry the strongest supported policy to controlled canary readiness.~~
  **The B7.5 campaign is PARKED**, banked, and priced as an expiring option. The active program is the
  **activation-candidate decision (OD-3)**: re-cost the W7 book's 2015–2026 validation at broker-true
  costs, port candidate generation and answer G4, then put a cost-true survivor book — or an honest
  kill — in front of Borhen. The asymmetry driving it: the broad V4 stack's evidence is **negative and
  unrepairable**; the W7 book's is **invalid and repairable** (F38 charges zero commission, F39 credits
  tick erosion with the wrong sign). See `CLAUDE.md` §4 and `THIRD_REVIEW.md` §1.2/§4.
- **The clock is now measured, and it is the US DST calendar, not EET/EEST.** Broker server wall clock =
  `America/New_York + 7 h` for **both** FTMO-Server3 and redacted_account-Server 2 (VPS-measured over 81 weekly
  session boundaries per broker; all transitions on US dates, none on EU dates). Use
  `src/utils/broker_clock.py`; it **fails closed** on an unregistered server. Never hardcode +3 — the two
  calendars disagree ~4 weeks a year, including **2026-03-08..03-28, inside the sealed March window**.
- **The daily-loss reset is per account, and the two firms differ.** FTMO resets at **00:00 CE(S)T**
  (its own captured page, and `config/profiles/operator_profile.yaml:104`); redacted_account at **00:00
  server time**. These are different clocks — a firm's reset rule is not its MT5 server clock. See B56.
- **Research tick data lives OUTSIDE the repo** at `/Users/borr/GTOSActive/vps-ticks-20260726/`
  (1.9 GiB on disk, 51 files, FTMO + redacted_account, 2026-06-18..07-24, **263,894,769 rows**, all
  sha256-verified — corrected 2026-07-27 by scanning every row, B114; the previous "191.9 M" was the
  subtotal of manifest **V2 only** (32 files), and `TICKS_MANIFEST.jsonl` (V1) covers the other 19 at
  71,997,348). Its `time`
  and `time_msc` columns are **broker wall clock, not UTC** — every file carries a `.timebase.json`
  saying so. Convert with `broker_clock.broker_epoch_to_utc`; never trust a `_utc` field name.
- **Campaign state:** January development sealed and accepted (four arms S0R0/S1R0/S0R1/S1R1). **April
  adverse-development is INCOMPLETE** — pack R2 built, S1R1 reached 16 of 30 sealed days and was stopped
  on 2026-07-25 with no arm receipt. Remaining: finish April S1R1, run April S0R0/S1R0/S0R1, then May
  development, development freeze, and the sealed March challenge.
- **Runtime — CORRECTED 2026-07-26 by direct inspection of the VPS. The "hard halt" does not exist.**
  A read-only export session on the Windows VPS established [MEASURED]: **no `*.flag` file exists
  anywhere in either tree.** Not `GTOS_HARD_PRODUCTION_HALT.flag`, not `RESEARCH_RUNTIME_HALT.flag`, not
  `AUTOSTART_DISABLED.flag`, and neither of the two `ULTIMATE_BOOK_KILL_*.flag` paths `run_book.py` is
  actively watching. The only halt artifact is one **archived** file renamed on 2026-05-18. Meanwhile the
  supervisor task is **Running**, both books are healthy, both MT5 terminals are connected, and
  `trade_allowed` is **true** on both.

  **The entire brake is THREE false YAML booleans** — `apply_to_execution`,
  `live_activation_allowed`, `live_broker_authority`, at exported working-tree
  `agent_config.yaml:1161-1163`. (Corrected 2026-07-27; this said "one config line:
  `ultimate_book_live_broker_authority: false`".) There is no
  second line of defence — no flag, no terminal block, no scheduler stop. F2 predicted the flag mechanism
  could not protect a fresh clone; the truth is worse, because it is not protecting the **live machine**
  either. Every prior statement in this file and in both audits that GTOS is "hard-halted as broker/VPS
  state" was describing flags that do not exist.

  Treat the halt as **three false YAML booleans on a running, funded, connected host** — corrected
  2026-07-28 at wave-3 integration (B180); this sentence contradicted its own paragraph, which had
  already been corrected to three. Do not add a second
  flag to feel better; port the activation token (below) to the VPS, which is the mechanism that makes
  absence fail closed.
- **Activation tokens are now the primary brake (2026-07-26).** Absence-of-halt is fail-open on a fresh
  clone (F2); presence-of-authorization is not. `RealMT5.order_send` refuses any **exposure-increasing**
  request without a valid token for that account (`src/safety/activation_token.py`); risk-reducing
  requests — closes, partial closes, pending cancels, stop tightenings — pass **without** one, so an
  expired token can never strand a position. Tokens live in `$GTOS_ACTIVATION_TOKEN_DIR` or
  `~/.gtos/activation`, deliberately outside the repo. Mint/inspect/revoke with
  `scripts/gtos_activation_token.py`. **There is no config flag to disable this** — the token is the switch.
- **Live decision surface (when unhalted):** the **`ultimate_book` W7 book**, not the broad selector.
  `config/agent_config.yaml:1246-1394`: `enabled: true`, `apply_to_execution: true`,
  `live_activation_allowed: false`. Profile `clean3_w7_ceiling_nom2p00` (2.0 % nominal per account) with
  mandatory `derisk_mode: smooth`. Two fully independent per-account `run_book.py` workers — **not**
  primary/follower. See `live_system_of_record.md`.
- **`run_book.py`, the live entrypoint, IS in this repository** — corrected 2026-07-26. It was vendored
  by Phase 0 item 0.1b (`31cf05634`) and amended by `7c85c3105`; **19,886 bytes at HEAD** (18,032 before wave 3 — Sessions I and M both amended it,
  B181), alongside
  `scripts/run_book_supervisor.ps1`, `tests/test_run_book_importable.py` and
  `tests/test_run_book_account_identity.py`. Live halt coverage, account identity and namespace
  isolation are now inspectable locally — the "unverifiable until vendored" caveat is retired.
- **V3/V4 status:** Selector V3 and Scheduler V3 are `false`/default-off. Selector V4 and Scheduler V4 are
  `enabled: true` but `live_activation_allowed: false`, so their permission gates never fire —
  `permissions.py:930` returns `None` for every candidate. V4 exists and is exercised in replay; it holds
  no live authority.
- **Symbol surface:** 24 symbols (`GTOS_24_SYMBOL_SURFACE`, `v4_timewarp_simulated_live_research_loop.py:251-278`).
  Replay sizes from `config/profiles/ftmo.yaml` (`agent_config.yaml:3160`); live sizes from
  `config/profiles/redacted_account.yaml`. They disagree on NAS100 (2×) and US30_cash (0.5×) — and so do the
  **brokers**: 18 of 19 shared symbols carry differing `trade_contract_size`, JP225 also differs in
  `digits`/`point`/`trade_tick_size`. Vendored at
  `research/operations/vps_broker_truth_2026_07_26/BROKER_SYMBOL_SPEC_COMPARISON.json`.
- **The live profile is `operator_profile`, not `ftmo`.** `scripts/run_book_supervisor.ps1:86-87`
  launches `run_book.py` with `profile=operator_profile` and `profile=redacted_account`. Both FTMO profiles
  exist and both are **decision-contract-bound** — check membership (H1) before editing either. A change
  tested only against `ftmo.yaml` has not been tested against the live account.
- **The 69 GB denominator-to-deployment route is cold-demoted** (2026-07-26, B53): 284 ledgers are now
  `*.jsonl.cold/` zstd shards read in place by
  `research/operations/…_2026_07_16/b7_5_cold_evidence.py`; 69.204 GiB → 2.5 GB with zero irreversible
  loss. Holds and a third copy: `~/gtos-d1-hold-20260726/` and
  `iCloud/GTOS-Cold-Archive/2026-07-26 D1 …/`. **Do not `git clean`/`git checkout` inside that route** —
  two `REPLAY_EXTENSION_*` paths are load-bearing *by their absence*.
- **Evidence lives in two places.** Committed route artifacts under `research/operations/`, and the
  **untracked `.hermes/` tree** (`plans/`, `receipts/`, `evidence/`, `replay-accel-status.json`) which
  holds the current campaign's accepted-evidence index. `.hermes/` is not in git — treat it as machine-local
  state and never assume a fresh clone has it.
- Historical: April/WF-1, XAUUSD-only, 7-symbol, Model A, PrimaryAnalyzer/L2, static `1.5R`, J46/J49, and
  BE-only material is historical unless a current artifact explicitly labels it active.

---

## 5. Full repo control

Goal sessions have full control over repo changes on this research laptop. Change production code, config,
prompts, risk, execution, safety, canary, selector, scheduler, runtime, live-behavior code, launchers,
profiles, tests, verifiers, research artifacts, manifests, and integration packages to build the strongest
final system. Implement, verify, and commit scoped changes.

Do not make strategic trading decisions for the owner. Risk dial, allocation profile, and any change to
the sealed economic contract are Borhen's calls.

---

## 6. Engineering rules

- Read current code before claiming behavior. Cite `file:line` for production-state claims.
- Do not fabricate data or statistics.
- Preserve user and other-agent changes. Do not reset or revert unrelated work.
- Use `rg` first for searches.
- Use the Edit/Write tools for edits. (`apply_patch` in older instructions was a Codex-tool artifact and
  does not apply here.)
- **Before claiming "no regressions," A/B against the parent commit** — run the suite at `HEAD~` and at
  your change and diff the failure sets. See H2.
- Prefer behavioural tests over source-string assertions. A test that greps the source for a substring
  passes against a wrong implementation.
- Keep commits scoped. Do not stage broad runtime dirt with cleanup or research commits.

---

## 7. Research rules

Research posture is aggressive, source-bound, and result-first. Same-evidence-class blockers must be
pursued until repaired, proven impossible from available inputs, or reduced to an exact source/capture
requirement.

Posture is build-and-ship, not theory-only. Evidence classes preserve claim quality; they do not limit
implementation. Ship the strongest final live system package.

Weigh proof work against the charter: it earns priority when it unlocks a decision, exposes an economic
defect, supports a causal repair, or moves the system toward operation. The audit found that
**60.6 % of replay CPU is proof/attribution machinery while 8.3 % decides trades** — when adding a new
verifier, receipt, or ledger field, state which decision it changes.

Read `.context/00_core/goal_session_research_discipline.md` and
`.context/00_core/research_operating_doctrine.md` before substantial research.

---

## 8. Cleanup rules

Current HEAD is the working surface. Git history is the deep archive.

Keep a file in current HEAD only when it is current authority, active code/config/test, active route state,
active reproducibility evidence, or unique intelligence demoted through a cold-evidence pointer. Delete,
compress, rewrite, or demote stale context pollution after proof.

The repo root stays lean: active entrypoints, current docs/config/runners, and local `.env*` only.

The audit's `OVERENGINEERING_AND_DELETION_MAP.md` quantifies the surface: **21.7 % of 1.33 M Python lines
is reachable from a current entrypoint**; 219,469 lines are deletable at LOW risk with no reachable
consumer and no surviving test. 97 % of the 6.3 GB tracked tree is generated evidence, of which 4.8 GB
sits in 280 inline non-LFS blobs over 5 MB.

Historical mentions are allowed only when clearly labeled historical, archived, comparator-only, or
superseded.

---

## 9. Running the system

The system is hard-halted as broker/runtime evidence, not as a restriction on implementation. Do not use
old launcher snippets, live companion repair notes, process health, or first-fill framing as a reason to
reuse weak behavior.

A sealed replay arm is launched through `src.research_infra.b7_5_post_acceleration_runner run-arm` with
the sealed contract, execution seal, source bundle, typed and tick-sparse caches, and prepared-day-pack
root. See `docs/audits/opus5-architecture-20260725/receipts/profile_day_harness.py` for a working,
annotated invocation. One month-window of four arms is **~16.5 h** on this machine.

Pre-halt live process evidence:

- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/`
- `research/operations/final_moonshot_live_failure_intelligence_2026_06_04/`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/`
- `pipeline_state/`, `shadow_logs/gtos_vnext_runtime_decisions.jsonl`,
  `shadow_logs/gtos_vnext_replacement_monitoring.jsonl`

The research laptop is the build surface.

---

## 10. Historical material

Old handoffs, old `.context` docs, old program-control reports, raw LFS JSONL ledgers, and April-era
runbooks can contain useful intelligence, but they are not current authority. Extract useful intelligence
into current summaries before deleting, rewriting, or demoting polluted sources.
