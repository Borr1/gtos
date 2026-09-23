# Gold Traders Operating System (GTOS) — Agent Instructions

Owner/CEO: Borhen.
This file is the active root briefing. Last reconciled 2026-07-25 against source, config, and the sealed
campaign evidence during the Opus-5 independent architecture audit.

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
   and payout, with the two owner decisions (OD-1/OD-2) it starts from. **Both are now partly
   superseded — read item 10 before acting on either.**
10. `docs/audits/fable5-vision-audit-20260725/THIRD_REVIEW.md` (2026-07-27) — **the third
    independent review (Fable 5), and the controlling plan.** Approved in full by Borhen on
    2026-07-27. It reviews its own second audit and vision plan against the evidence eight
    implementation sessions produced, and it **changes the program**: Phase 2–3's sequencing is
    superseded by its §4 constrained plan (Stage 0 → Stage 1 → OD-3); OD-1 is reopened as OD-3;
    the ≤3 GB/arm gate is withdrawn; the campaign is parked. §1.2 is the strategic core (the
    negative-vs-invalid asymmetry), §A1 is the memory attribution that settles H3, §A2 records what
    its own adversarial pass refuted. **§4 is the work queue wave 3 is cut from.**
11. Latest numbered handoff in `.context/02_session_handoffs/` — **historical context only.**

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
        if not p.is_file(): continue
        b=p.read_bytes()
        if hashlib.sha256(b).hexdigest()!=r['sha256']:
            # An un-hydrated LFS pointer hashes differently from the content it points AT, so it
            # reads as drift when nothing has drifted. Distinguish the two before believing it.
            kind='UNHYDRATED-LFS' if b[:40].startswith(b'version https://git-lfs') else 'DRIFTED'
            print(kind+':',r['path'])
print('unbound verification tooling (free to edit):',
      [r['path'] for r in d['input_bindings']['verification_tooling']])
EOF
```

**Read the count with the LFS caveat, added 2026-07-27 (B185).** The drift count is a property of
**your working tree's LFS hydration state**, not of any commit — so it is not portable between
worktrees and not stable across a checkout. Two bound paths are LFS-tracked
(`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`, `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`);
when either sits as a 131-byte pointer the check above reports it as drifted, and the original check
could not tell that apart from a genuine seal break. It happened in this worktree during wave-3
integration: a plain `git merge --ff-only` de-hydrated `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` and the
count went 1 → 2, which the working agreement defines as "the real signal". It was not.
**`git lfs checkout <path>` first, then read the count** — the object store is local, no network.
~~The pointer's own `oid sha256:` line is the contract's expected hash, so a pointer is positive
evidence the content is intact rather than a reason to worry.~~

> **Struck 2026-07-30 — that sentence is false for one of the two paths, and the truth is a
> standing hazard (Session AT, B905).** For `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`
> the pointer oid is `a5bcc0f8…` while R2 expects `19365f60…` — the contract's expected bytes match
> **no committed object in any git tree**. They match exactly one file on this machine: the
> UNCOMMITTED, `git status`-modified working copy in `/Users/borr/GTOSActive/repo` (same length,
> 205,754 bytes, which is why nothing noticed). The seal is satisfied only because the runner's
> `binding_roots` fallback ends at `MAIN_REPO_ROOT` and finds the dirty file there. **Never clean,
> stash, or re-checkout that path in the main repo** — the parked campaign's ~36 MH option dies with
> it. A verified copy is held at
> `/Users/borr/GTOSActive/hermes-evidence-hold-20260727/r2-contract-satisfying-bytes-20260730/`.
> For the *other* LFS-bound path (`SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`) the pointer-oid claim
> holds. Check per path; do not generalise it again.

Still true after OD-2: **seven other never-executing verifiers stay bound**, because
`code_authority_paths` (`replay_acceleration_attempt5_typed_sparse_runner.py:1405-1431`) binds them a
second time from inside an executing file. They are listed in R2's `verification_tooling_deferred` with
that reason. Landing a change to a genuinely bound file still requires regenerating the contract and
re-running the affected windows (~16.5 h per window).

**H2 — The test suite is not green at HEAD, and the standing explanation was wrong.** 10 tests fail
in `tests/test_selector_v4.py` on a clean checkout. The Fable audit hydrated the sleeve-registry LFS
pointer (that fixed exactly one other failure, in `test_permissions.py`); the remaining 10 are a
**real, pre-existing package-admission defect** — `package_execution_fill_probability` resolves
`None` — filed as F13 in `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md`.

**The mechanism this file used to state was also wrong, and the fix it implied would have cost a
re-seal.** Struck: *"`selector_v4.py:4004-4016` never consults `entry_quality_fill_probability`"*.
That description is accurate and the inference is not — `:3995-4001` **does** consult it, for
`package_quality_fill_probability`, a different quantity, and `:4004-4016` correctly declines to mix
an entry-quality heuristic into an execution-fillability slot. The real gate is upstream:
`_complete_execution_fillability_atom` (`selector_v4.py:453-537`) refuses to emit without a complete
value+provenance tuple and `continue`s at `:508` when `source_time`/`source_boundary` is missing. The
ten fixtures pass a bare `{"fill_probability": X}` with no provenance. **The defect is in the
fixtures, not the engine** — see `IMPLEMENTATION_STATE.md` **B8 [VERIFIED]** and `THIRD_REVIEW.md` §7
item 4. Editing `selector_v4.py` on the old story would have touched a **contract-bound** file for no
reason (H1: re-seal + ~16.5 h per window).

**Always A/B against the parent commit before claiming "no regressions."** Do not chase these as your
bug, do not repeat the LFS explanation, and do not repeat the `:4004-4016` one either.

**H3 — Memory is a constraint, and the ≤3 GB/arm target was aimed at the wrong subsystem.
Corrected 2026-07-27; the prior text was wrong in three ways and is struck.**

- The "15.3 GB is a GiB/GB echo of 8.61 GB" claim is **false**. `/usr/bin/time -l` emits both
  `maximum resident set size` *and* `peak memory footprint`; 15.32/8.61 = 1.779, not the 1.0737 a
  GiB→GB conversion gives. Two fields, two measurements. (The error was this file's and the second
  audit's — `SECOND_AUDIT.md:619-622`, struck by `THIRD_REVIEW.md` §7.1.)
- **8.61 GB is a 2-day fixture, not a month arm** (`day: 2026-01-01`, `end_day: 2026-01-02`,
  603.7 s). **No month-arm RSS measurement exists anywhere.** Do not quote it as one.
- **The ≤3 GB/arm target is withdrawn, not re-derived.** It came from a wrong causal story (the
  source layer's 5× materialisation). Session G killed every source-layer copy, proved output
  identity over 1.78 M rows, and the arm did not shrink (B84/B85).

**Where the memory actually is** [MEASURED, `THIRD_REVIEW.md` §A1 — `tracemalloc` at the Python-heap
high-water mark of the sealed 2-day S1R1 fixture; receipt
`docs/audits/fable5-vision-audit-20260725/third_review_receipts/memattrib_result.json`]:

| owner | MB at high-water | share |
|---|---:|---:|
| `v4_timewarp_simulated_live_research_loop.py` — per-day row/attribution accumulation | 3,866 | **60.6 %** |
| `moonshot_scheduler_v4_best_trade_allocator.py` | 614 | 9.6 % |
| stdlib `json/decoder` (retained day-pack JSON) | 401 | 6.3 % |
| **source layer** (`integrated_source` + `prepared_day_pack`) | **99** | **1.6 %** |

Traced heap grows **monotonically through each replay day** (0 → 5.5 GB day 1, → 6.38 GB day 2) and
collapses at day end; RSS spikes to its peak at the instant of that collapse, when day-end
serialisation forces the accumulation resident. **The evidence machinery is simultaneously the
memory (60.6 % of heap), the CPU (60.6 % self-time) and the bytes (>99.8 % never value-read) — one
redesign, three resource problems.** No source-layer work of any kind can move the arm peak.

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
`scripts/mt5_preflight.py` **no longer places orders at all — closed 2026-07-27 by Session I, merged
in wave 3.** Its order-placing arm is retired: `--test-order` and `GTOS_MT5_PREFLIGHT_TEST_ORDER=1`
both print `RETIRED_ARM_MESSAGE` and `raise SystemExit(2)` (`mt5_preflight.py:48-50`), and test 5 now
answers the same question with `mt5.order_check`, which validates a request without mutating anything
(`:147`, `:167`). The refusal covers the environment variable as well as the flag, so a stale
`GTOS_MT5_PREFLIGHT_TEST_ORDER=1` in a VPS environment cannot arm it. ~~**There is no longer a raw
`mt5.order_send` in the repository outside the gated engine path.**~~ (Struck: "It is the last ungated
mutating script; gate it or retire it" — it was retired. Struck earlier still: "still default-live".)
All of these stay on the never-execute list regardless.

> **Amended 2026-07-29 at wave-4 integration (B361). That last sentence is true of THIS repository
> and false of the VPS, and the difference is the whole point.** Session I's retirement is on
> mainline only; it has never been carried. Both VPS repo trees — Session S measured that there are
> **two** and that 25 of their 519 shared `src/` files differ by sha256 (B292) — still carry four
> raw `mt5.order_send` calls at `mt5_preflight.py:136, 142, 152, 155`. Verified two ways without
> touching the host: in the read-only 2026-07-25 export
> (`vps-export-20260725/extracted/21_scripts/mt5_preflight.py` **and**
> `.../13_packet_repo/scripts/mt5_preflight.py` — same four line numbers in both trees), and at
> `redacted_host`, the commit S verified as the live lineage — all three copies are **byte-identical**
> (sha256 `cff6a058…`). `[UNVERIFIED]` for today's host: this session does not touch the VPS, so the
> evidence is the 2026-07-25 snapshot plus the lineage commit.
>
> **And the MAINLINE half is wrong too, as literally worded.** Struck above; the correct sentence is
> **"there is no *ungated* raw `mt5.order_send` that can INCREASE exposure outside the gated engine
> path."** Five raw call sites exist here at HEAD outside `src/mt5/mt5_real.py`, and the repo already
> knew — `tests/safety/test_raw_broker_script_guards.py` exists for exactly three of them:
>
> | site | guard |
> |---|---|
> | `src/safety/heartbeat_monitor.py:739` | the **halt only**, no activation token — and §4 establishes the halt does not exist on the VPS, so it is inert there. Not in the `run_book.py` path (it is on the `run_agent.py` lineage). |
> | `scripts/flatten_all_positions.py:49` | **none** |
> | `scripts/emergency_close_and_stop_redacted_account.py:304, 360` | **none** |
> | `scripts/fn_smoke_trade.py:246` | deliberately exempt, documented at `:205-216` |
> | `scripts/fn_smoke_trade.py:389` | gated (`authorize_raw_broker_request`, `:381`) |
>
> All five are **risk-reducing** (close, cancel, flatten), which the token layer passes without a
> token anyway — that is the honest defence, and it is not what the original sentence said. All stay
> on the never-execute list regardless. Found by an adversarial pass on this very amendment (B366).

**H7 — Replay does not measure the live system.** Replay runs a portfolio allocator, Selector V4 admission,
and continuous sizing that the live path does not implement. Do not transfer replay R to a production claim
without the divergence matrix in the audit.

**H8 — Shutting the gate does not flatten. `live_broker_authority: false` leaves open positions open
*and* unmanaged.** [MEASURED 2026-07-29 at wave-4 integration by direct read, B362.] The instinctive
emergency sequence — "shut the gate, then work it out" — is backwards, and it is the one hazard here
that costs money the first time it is learned. With `ultimate_book_live_broker_authority` false
(`_live_broker_authority`, `:251-263`, reading `gtos_vnext_runtime.ultimate_book_live_broker_authority`,
default `False`), five paths in `book_owner.py` stop reaching the broker — four by returning, the
fifth by degrading:

| path | line | what happens instead |
|---|---|---|
| `_flatten_all_engines` | `:2364-2373` | records `{action}_suppressed_live_broker_authority_false` and returns without visiting a single engine |
| operator `FLATTEN.flag` | `:2423` | one warning, then `return` |
| governor breach flatten | `:2458` | one warning, then `return` |
| **routine per-tick trade management** | `:2526` | `live_broker_authority_false_observe_only` — TP/SL moves, scale-outs and time stops stop reaching the broker |
| exit-policy rehydration on adopt | `:2714-2718` | **does not return** — calls `hyd(rec, modify_broker_tp=False)` and continues; it returns early only on `TypeError` (`:2719-2723`) |

The flag that reads as the emergency brake is therefore *observed*, not obeyed
(`source_completeness_status: flatten_request_observed_broker_mutation_disabled`), and the fourth row
is the one nobody expects: the book stops managing as well as stops closing. **Flatten first, confirm
flat, then shut the gate.**

**A gated position is not naked, and that limit matters** [MEASURED by an adversarial pass, B366;
this line previously read `[UNVERIFIED]`]. The broker-side SL/TP are set **at entry**
(`execution.py:3488`, `"sl": sl, "tp": tp1`), so a hard server-side stop survives the gate — the
book's own `_alert_out_of_universe` docstring says an unmanaged position *"would silently ride the
broker SL/TP only"*. What is lost is the **time stop, scale-outs, trail/BE moves, TP edits, and the
governor breach-flatten.** Losing breach-flatten is the prop-fatal part, so the operating rule stands
unchanged; do not read it as "positions are unprotected". Independently confirmed by enumeration:
every `self._mt5` call in `book_owner` is a **read**, every mutation routes through an execution
engine, the only `ee.close_position(` is `:2392` inside the gated `_flatten_all_engines`, and both of
its callers are themselves gated. `run_book.py` performs no broker mutation of its own.

---

## 4. Current truth

> **Plan position, 2026-08-12 (addendum to the note below, same read) — the gate ledger in
> full, the five-month sealed record, and the analysis now running.** The note immediately
> below is the June/July narrative and still binds; this one carries what it does not.
> Blocks **B3414–B3421**.
>
> - **The four gates, from the sealed payload itself** (`JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json`
>   → `gates` / `gate_inputs` / `window_stats`, payload `13c92591…`, commit `1f7e21e44`):
>   discipline-beats-naive-mixed **+28.96 R PASS**; pooled worst-case > −2 R **−16.72 R FAIL**;
>   rule∘LSR positive in window **−7.00 R FAIL** — the in-window gate the note below does not
>   quote; rule∘LSR positive every scored month **June −3.16 / July −3.84 FAIL**. The scoped
>   replay is **23 selected / 21 resolved: 2 TARGET / 11 STOP / 8 TIME_STOP / 2 CENSORED**
>   (`primary_deployable_object_forward_record`), pooled actual −10.40 R, worst case −12.44 R.
>   BAR-1 and BAR-2 sit under `reported_not_used` and also REJECT (BAR-2 bootstrap p05 −35.76,
>   20,000 resamples, seed 20260811).
> - **The prereg ladder is four commits, each frozen before the outcome it governs**: V1
>   `52f3bd9c8` (BAR-3, r4 scorer) → V1_1 `8afdfd849` (D1 rebind, r4b) → V1_2 `71e42cc34`
>   (M15+H4 lead-ins, lead-in-first precedence, r4c) → V1_3 `241640fce` (registry re-pin for the
>   scorer's Oct/Nov bootstrap, r4d; payload `d92c80ea…`). The depth repairs carry their own
>   receipts — `JUNJUL_{D1,M15,H4}_SUPPLEMENT_MATERIALIZATION_V1.md` over
>   `JUNE_JULY_LANE_MATERIALIZATION_V1.md` — at **1,387 / 129,512 / 8,292 overlap rows compared,
>   0 mismatches**, exact string equality on every column.
> - **The sealed record is five months now: Feb PASS / Apr+May REJECT / Jun+Jul REJECT.** One
>   PASS in five, and the only positive stable across all three reads is a *relative* quantity
>   (+18.9 / +6.6 / +28.96 R discipline-vs-naive). Price any future funnel claim against that
>   ledger before calling it an edge.
> - **Lane surface**: the hold's registry carries `june_2026` (**168 `bar_sources`** after the
>   three supplements) and `july_2026`, whose read authority ends **2026-07-28** — not month-end,
>   because 07-29 is the first arming date and the TEST live-forward band stays unread; the
>   `WINDOWS` spec and the registry entry carry the same bound. `src/` on `main` carries
>   **neither** those two `WINDOWS` entries nor the re-pinned registry hashes: both live only in
>   the disclosed `JUNJUL_MACHINERY_PATCH_V1_3.diff` [VERIFIED by grep of `origin/main`].
> - **Shadow deploy, operational state**: the VPS deploy under
>   `host-local\gtos-shadow\` has **not** completed — two attempts died at a host
>   login outage and a third is running. Until its `SHADOW_START=…` banner is read, treat forward
>   coverage as *not yet started*, not as running-and-quiet.
> - **An owner-directed full-puzzle analysis of the five-month record is underway**
>   (orchestrator-run, no subagents); its plan lands as a separate `main` commit. Nothing in the
>   whole June/July program touched a live path — **the armed sleeve estate and every live-state
>   claim in this file are unaffected.**

> **Plan position, 2026-08-12 — the June/July BAR-3 confirm read is SEALED: REJECT, and the
> scoped-LSR deployable is dead on its own confirm.** Read this note first; the 2026-08-10 note
> below binds where not superseded. The full record: `phase21/full_system_coherence/
> outcome_authority/JUNJUL_READ_RESULT.md` + `JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json`
> (payload `13c92591…`), prereg ladder `JUNE_JULY_MARKET_TOP_CHOICE_PREREG_V1..V1_3` (owner-ratified
> BAR-3; three execution-layer amendments, each frozen pre-read).
>
> - **Verdict**: pooled worst-case **−16.72 R** over 42 days (June −0.12, July −16.61); rule∘LSR
>   negative in BOTH months (June −3.16 / July −3.84; scoped replay 23 trades, 2 TARGET / 11 STOP /
>   8 TIME_STOP, −12.44 wc). February was the outlier, not the norm. BAR-1/BAR-2 also reject.
>   **No incubation ceremony** — the prereg discipline killed the deployment before money did.
> - **What survives every sealed read**: discipline-vs-naive relative skill (+18.9 Feb, +6.6 AprMay,
>   **+28.96 JunJul**). The selection layer works; the candidate pool's absolute edge is
>   non-stationary (families flip sign month-to-month: `structural_distance_extreme` June +10.06 →
>   July −12.69, same shape as April's autopsy).
> - **The June read cost three measured source-depth repairs** (the engine's screens starve below
>   ~30 pre-day D1 / ~72 H4 / deep-M15 bars — invisible on the deep families every prior window
>   used): D1/M15/H4 lead-in supplements, all exact-string cross-checked, June manifest
>   `7498a9d5→f20fc7ae` (96→168 sources), July untouched. The stream-coverage invariant that
>   caught it fail-closed is why June is not a silently-dead month in the record.
> - **The surface map changed under owner word**: `gap_2026H1_tail_pre_arming` is replaced by TRAIN
>   band `train_2026_junjul_funnel_confirm` (2026-06-01..07-28, estate-consumed/funnel-virgin dual
>   disclosure, per the gap's own resolution_owner clause + BAR3_RATIFICATION_20260811.md). TEST
>   (2026-07-29+) untouched. The generation tree (coherence worktree) carries these as disclosed
>   uncommitted patches (`JUNJUL_MACHINERY_PATCH_V1..V1_3.diff` on main).
> - **Forward shadow is the instrument now**: dual-lane (general + scoped-LSR) read-only runner,
>   merged (`eed6c496b`), **daily prequential refit merged under owner word** (`1c9266850` —
>   day-zero bit-identical to the flat V1 artifact); VPS deploy in progress under
>   `host-local\gtos-shadow\`. Zero broker mutation by construction.
> - **Rule V2 is commissioned** (owner "proceed", 2026-08-12): postmortem §5 features (regime
>   interactions, completion-rate proxies, MFE-shape priors, SD5, calibration — V1's largest
>   measured defect), trained through July 2026, to be frozen-read on the **four never-funnel-read
>   2025 windows already materialized in the hold** (june/august/september/december 2025) under a
>   BAR-2-class bar (proposed; owner ratifies at freeze). Those four windows are the program's
>   validation currency — **spend nothing on them**.
> - The raw-campaign registry pins (`lane_rematerialization.py:172-186` at the generation tree)
>   were re-pinned to the post-materialization registry (V1_3); any registry change breaks them
>   again by construction. The armed sleeve estate is untouched by all of the above.

> **Plan position, 2026-08-10 — waves 19–21 have landed on main (`6f061af2d`), and the program
> has its first frozen-rule unseen-window PASS.** Read this note first; the 2026-08-01 note below
> binds where not superseded. The wave-by-wave record for 19/20 is in `WAVE_11_WORKING_AGREEMENT.md`
> §4; wave 21 is `phase21/WAVE21_INTEGRATION.md` + `IMPLEMENTATION_STATE.md` B3400–B3413.
>
> - **The probability question is settled by measurement, not argument** (`phase21/full_system_coherence/
>   probability_truth/PROBABILITY_EV_TRUTH_V1.json`): the debate-engine score is outcome-uninformative
>   (AUC 0.4960; predicted 0.783 vs observed 0.2503 target rate; Platt unrescuable). Truth mode
>   (`wave21_full_flow_truth_mode_enabled`, default-off) strips probability/EV authority fail-closed;
>   economic probability authority requires a geometry-bound outcome model that does not yet exist.
> - **FEBRUARY VALIDATION PASS (2026-08-10):** the frozen MARKET-top-choice rule — prequential ridge
>   over the full raw candidate population, complete four-component costs, trade only when the top
>   candidate is MARKET, abstain on LIMIT — made **+14.17 R on 106 trades (105 resolved), 13 pos / 6 neg
>   days, all three pre-registered gates green** on regenerated February 2026. Comparators on the same
>   universe: rerank-substitution +4.67, naive mixed −4.74 on 360. Rule of record:
>   `phase21/full_system_coherence/outcome_authority/MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json`
>   (V1 froze a base-config runtime that could not satisfy its own cost-completeness clause — run 1 is
>   NOT_EVALUABLE, receipt `FEBRUARY_RUN1_NOT_EVALUABLE.md`; V1.1 is the execution-layer amendment,
>   validated by exact January-05 reproduction). Caveats bound to the result: modelled M1 lifecycle
>   (not broker fills), n=106, ridge over-predicts ~1.5×, +13.6 of the +14.2 R sits in
>   `liquidity_sweep_reclaim` (24 trades), February was VAL-read once (wave 18, different pipeline).
>   `activation_or_live_authority: false` by the rule's own terms. Reserves still never-read:
>   2025-10-31, 2025-11-05.
> - **APRIL+MAY READ (2026-08-11): REJECT.** The February-PASS rule, verbatim on the next two
>   never-read months (frozen prereg V1.6 after six execution-layer calendar/guard amendments,
>   all receipted): pooled **−2.612 R on 67 trades** (April −7.742/50, May +5.130/17), gate 2
>   failed. The discipline still beat naive mixed by +6.6 R (−9.212 on 317) — ranking adds value
>   in every measured month; the rule as frozen is NOT deployable and no arming proposal exists.
>   Family robustness: FAMILY_SPECIFIC (liquidity_sweep_reclaim, the only positive family).
>   Standing: one PASS + one REJECT; 3-month pooled +11.556 R/63 days. April+May are now opened
>   development data. See `outcome_authority/APRMAY_READ_RESULT.md`.
> - **The inverted-breaker candidate's ADMIT is REJECT again** under the wave-21 slippage authority
>   (q 0.3169; 6 of 16 symbols lack reconciled price-domain slippage samples). Restoration is a
>   slippage capture (AUDJPY/CHFJPY/EURJPY/UKOIL.cash/USOIL.cash/XAGUSD), not a threshold change.
> - **Live (2026-08-10):** both tokens re-minted to **2026-09-09** (30-day cap; re-mint before then).
>   F1 (FN token namespace) was fixed 08-06; CN (broker-true commission) live on both books since
>   08-06; CO lapsed (owner-directed); **CM was armed 08-06 and ROLLED BACK 08-10 on the owner's
>   word** (host `4d28676f8`) — FTMO crypto is back on the shipped 4R contract, re-arm gated on
>   pricing `stop_1p5x_target_scale` on the corrected-quote walker. Armed set: four sleeves both
>   books (`crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert`), spread floor on the last
>   two, mx disarmed. Known live gap: redacted_account silently skips 13 symbol/sleeve pairs on missing
>   instrument config — fix bundles with the next re-mint + restart.
> - **March confirm + six 2025 lane windows are on main lean** (squash `04f314295`); the six giant
>   March arm receipts stay local-only (sha256s recorded; bundles in
>   `hermes-evidence-hold-20260727/branch-bundles-20260810/`). The three held-out 2025 windows were
>   SPENT 2026-08-06 (lane p2) — no held-out 2025 set remains; Oct/Nov/Dec are the open working set.
> - **Next queue (in order):** pre-register the next unseen read of the PASS rule (the two reserve
>   days + a 2025 window) with a concentration test on `liquidity_sweep_reclaim`; fresh full-flow
>   comparator + W7 recost rerun under integrated code (both PENDING in `ROUTE_STATUS.json` — retained
>   runs bind pre-integration code); the CS slippage capture; then the geometry-bound outcome model
>   (the Jeffreys/ridge estimator made result-bearing) toward an incubation-size live arm.

> **Plan position, 2026-08-01 — the CJ + wave-17 train has landed under OD-ALL-IN
> (`docs/audits/fable5-vision-audit-20260725/phase17/OD_ALL_IN_20260801.md`, the owner's
> direct-to-live directive). Waves 9–16 landed between the note below and this one; the
> working agreement (`WAVE_11_WORKING_AGREEMENT.md` §4) is the wave-by-wave record. What
> binds NOW:**
>
> - **The clock was wrong and is now measured**: sealed labels were true UTC + 2 h (CJ,
>   54/54 weekly opens). Re-clocked January moves the broad family +3.435 R (still negative,
>   −5.506). True-UTC lane packs exist for Jan/Feb/Apr/May 2026; **February 2026 is the first
>   never-read economic window** (Session CP owns its pre-declared first read).
> - **Widening the armed set was PRICED and the direct-addition set is EMPTY on both accounts**
>   (CL): both JPY sleeves −0.1121 ΔP2 on FTMO, `metals_core` ×0.50 −0.1198, softband
>   carry-conditional, FN-MX fails the historical-primary gate, VP unpriceable. Two incubation
>   proposals (ETH target-5R, Asia PDL) are filed at 0.025 pending exact live-contract parity.
> - **Three host ceremonies compose at the 2026-08-02 00:00 UTC boundary** (the orchestrator
>   executes): CM — FTMO `crypto@stop_1p5x_target_scale` via `--frontier-exits` (+0.03552 R/day
>   latest-fold planning basis); CN — broker-true commission as the default fourth cost term,
>   fail-closed, both books (7/174 same-input flips, all conservative, all FN oil); CO — the
>   learning lane's first live vector, FTMO `crypto` ×1.15 + `mx@target_5R` ×1.15, signed
>   all-or-neutral envelope, governor senior, declarations expire 2026-08-08. After execution
>   FTMO runs 5 tags + frontier `mx,crypto` + lane weights; redacted_account 4 tags + neutral lane.
> - **CN's `broker_net_cost_engine.py` edit is the authorized forward R2 seal break** (owner
>   word, recorded): any future sealed replay regenerates its decision contract first. The
>   parked campaign's resume option is already dead by CJ's seal break, as priced.
> - **Wave 18 landed same day: virgin February REJECTS broad V4 at true UTC** (0/20 positive
>   days, precision 0.309 vs 0.606 breakeven, committed pre-outcome rule — the S1R1
>   continuation probe is CLOSED; February is used-once VAL now). AW's B_TIME map is
>   superseded by `phase18/receipts/CP_TRUE_UTC_B_TIME_MAP_V1.json` (all 83 cells negative).
>   Two factory candidates stand billed at the **V27** family tip (59 declared / 57 looks,
>   `phase18/receipts/CANDIDATE_FAMILY_V27.json`): CP's NY-metals-LONG (TRAIN survivor,
>   gate NOT_EVALUABLE pending fill-classified capture + measured fidelity) and CQ's
>   inverted-breaker 5D/0.25D (+11.9 net R/trade on TRAIN and HOLDOUT January VAL, gate
>   NOT_EVALUABLE at one fold of three). Wave 19 (CR/CS) is running both gate-completing
>   captures; CS reads CJ's economics-unread April+May packs as the two missing folds.
>   CQ also retired CK's first-touch ambiguity bound (0/27,658 measured) and wired the
>   default-off breaker transform behind an absent-false key.
>
> The 2026-07-30 note below is retained: its wave-6/7/8 facts still bind where not superseded
> above.

> **Plan position, 2026-07-30 — waves 5, 6 and 7 have landed; `FOURTH_REVIEW.md` is the plan of
> record and Fable 5 orchestrates. Read this note first; the wave-3 note below it is retained
> because its corrections still bind, but its "what now decides OD-3" line is superseded.**
>
> Wave 6 built the fixing machine (AA: `run_gate(..., diagnose=True)`, 22,324 walked trades,
> the repair queue — now **134 rows + 49 in AD's sidecar** across 32+ members), the regime spine
> (AB), broker-true spread/era models (AG), and retired the noise in the test suite (AT: **639
> standing failures → 67**, per-test proof, all live coverage kept — the suite now reports code).
> Wave 7 executed the prescriptions. What it settled:
>
> - **"What now decides OD-3 is holding time" is superseded by measurement (AD, B750–B757).**
>   1,631 gated exit cells over 25 sleeves: every sleeve improves (median +0.249 R/day), on 23 of
>   25 the best exit geometry is worth MORE than eliminating carry entirely, and the failing gate
>   at all 25 best cells is `significance`. **Exit geometry and the multiplicity bill are the
>   binding constraints; carry was never the lever.** Carry tiers restated at measured holds:
>   `sub_mid_dn_revert` and `fx_jpy` are **UNCONDITIONAL on both accounts**; `metals_core`-on-
>   redacted_account flips at a 2.5 % time-stop tightening (not 10 %).
> - **`time_stop_bars` is M15 PRINTED bars for every sleeve** (`execution.py:8953-8958`). The
>   ~~twelve~~ **ten** generating `mx_*` D1 sleeves' live time stop is therefore 24–25 trading hours
>   against a 72–96 h realised median — **72–90 % of their trades truncated**; every published
>   economic number for those sleeves describes a contract the live book does not run. Four M15
>   sleeves also bind; all H4 sleeves and `vol_compression` are exactly the pre-scaled contract AA
>   walked.
>
>   > **REPAIRED 2026-07-30 (Session AQ, B1400–B1406), and the count above is corrected to three
>   > numbers because it was conflating them.** `SLEEVE_EXIT_PROFILES` declares **14** `mx_*`
>   > sleeves; **12** are in the active registry; **10** generate a trade (the archive has no
>   > `EU50.cash` or `FRA40.cash` series). The declared value was `96`, which is exactly
>   > `M15_BARS_PER["D1"]` — **the conversion ratio written into the field that wants the converted
>   > value**, so the live horizon was one D1 bar against eighty. `vol_compression`, declared four
>   > lines earlier in the same dict, had the identical D1 horizon right all along at `7680`. Fixed
>   > to `time_stop_m15(80, "D1")`; the two now share one expression. **Nothing armed moved** — the
>   > three live sleeves are H4 at 1280 = 80 × 16 — and 45 tests pin the unit behaviourally, the
>   > blast radius against a frozen pre-repair snapshot, and the armed three by name.
>   >
>   > **Two things the repair does NOT settle.** (1) Its value is **signed both ways**: at
>   > RECORDED/mid it is worth **+0.2722 R/day** on `mx_btcusd` and **−0.5913** on `mx_us100`, and
>   > **five of ten sleeves were BETTER under the accidental one-bar stop**. Those five want a short
>   > horizon *declared deliberately on the evidence*, which is an exit-frontier decision and is
>   > routed as one. ~~(2) For the ten unit-CORRECT sleeves the prescription is the opposite: the spec
>   > is right and the **published economics** are wrong. `asian_fade`'s published figure overstates
>   > its own live contract by **0.88 R/day** with a truncation fraction of **zero**, so that gap is
>   > the trailing-runner contract interacting with the time stop and nobody has walked it.~~
>   >
>   > > **(2) is STRUCK 2026-07-30 — Session AU walked it and the 0.88 is a construction artifact,
>   > > not a labelling error (B1561).** `asian_fade`'s true restamp error at RECORDED/mid is
>   > > **+0.0000 R/day**: its published economics already describe its live contract. AQ's
>   > > `LIVE_TRUE` arm is `AD.Variant(family="time_stop", target_mode="native")` and `Variant`
>   > > defaults `trail_arm_r`/`trail_gap_r`/`partial_at_r` to `None`, so for a `trailing_runner`
>   > > sleeve it **deletes the sleeve's own exit policy**. The zero truncation fraction was the
>   > > tell — a time stop that never fires cannot cost 0.88 R/day, and AQ said so. AA's own
>   > > metadata settles the published contract: `exit_contracts[sleeve].applied_here ==
>   > > "trail+stop+target+maxbars"`. `metal_session_reversion` is the same shape (+0.3054 artifact).
>   > > **The estate no longer has a "largest single labelling error".**
>   > >
>   > > **What it has instead, and the direction is worse on armed money.** For a
>   > > `partial_be_runner` sleeve the same time-stop-only arm accidentally REPRODUCES AA's plain
>   > > walk, so its error cancels to exactly zero and the sleeve never entered the ten restamp rows.
>   > > **`energy_agri` is ARMED and its true restamp error is +0.2302 R/day at every band** — the
>   > > live scale-out costs that much against the published plain-exit figure, corroborating AD
>   > > §6.2's −0.308 R/day through a second instrument. Across the four `partial_be_runner` sleeves
>   > > the sign runs BOTH ways (`metals_core`'s scale-out HELPS by 0.0777). And the real
>   > > qualification on `asian_fade` is a different one: at B613's honest trail bound it loses
>   > > **0.3365 R/day** (−0.1528 → −0.4893), which is AD's 95.8 %-intrabar finding priced at the
>   > > ratified rule. The eight other restamp rows reproduce AQ's figures exactly.
>   > > See `phase12/SESSION_AU_CONTRACT_WIRING_RESULT.md` §2.
>   >
>   > **One live-behaviour consequence, before any `mx_*` sleeve is ever armed (B1452).**
>   > `_trading_m15_bars_since` asks for `want = max(96, budget + 64)`, so an open `mx_*`
>   > position now requests **7,744** M15 bars per tick instead of 160. The fetch is not the
>   > hazard: **if the terminal returns fewer than 7,680 closed M15 bars the count can never
>   > reach the budget and the time stop never fires at all**, and the wall-clock fallback
>   > does not catch it (that path needs `None`, not a short count). The backstop degrades to
>   > INERT rather than late. Nothing armed is exposed — the three live sleeves are H4 at
>   > 1280, want 1344 — and it is filed rather than patched because the obvious mitigation
>   > moves armed sleeves onto the over-counting wall-clock path and would close them EARLIER.
>   > Measure the terminal's `copy_rates` ceiling before arming anything in this cohort.
>   >
>   > **And the part that reaches the challenge package**: `mx_btcusd @ target_5R` holds 82.3 % of
>   > its trades past 24 h and **REJECTS at all four bands** under the pre-repair contract
>   > (p 0.0011 → 0.0564, fold positivity 5/5 → 3/5, two most recent folds negative). The estate's
>   > one standing admission was contingent on this repair. Neither change alone admits: 2R at the
>   > repaired horizon p 0.0064, 5R under the old stop p 0.0564, both together p 0.0011. See
>   > `phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md`.
> - **Breadth is refuted as the estate's cure (AF).** 246 members × 30 families × 134,027 trades:
>   0 admit; 23 of 30 families are mixtures (dispersion ratio > 1) and their prescription is
>   `MEMBER_CONDITIONING_NOT_BREADTH`. The two-clause coherence test — ratio < 1 AND all members
>   positive — passes exactly 2 of 30, the same two with the grid's best p-values. The 9-symbol
>   crypto cluster is **refuted as diversification** (ratio 4.74, best-to-worst 1.80 R/trade).
> - **`mx_btcusd` is the estate's best new-edge candidate and is blocked ONLY by an owner
>   decision**: raw p 0.0064 (+0.389 R/day OOS on RECORDED eras), q 1.0 against the 276-look bill.
>   `declared_family_size` has no principled stopping rule; at ≤ 31 looks it admits under BH
>   α = 0.20, at ≤ 8 under Bonferroni α = 0.05. Its exit repair is a **wider target** (5R,
>   +0.309 R/day), not carry.
> - **The learning lane reads cost-true evidence and moves both ways (AE).** All seven
>   legacy-covered verdicts changed. **`metals_core` — armed, conf 1.00 — inverts to DOWN_WEIGHT
>   ×0.50** on a 232-trade/118-day OOS at −0.205 R broker-true. `crypto` is the only armed sleeve
>   the lane would size up (×1.08). Lane stays default-off, recommendation-only.
> - **Live-contract fidelity findings on armed money (AD §6.2):** `energy_agri`'s live
>   `partial_be_runner` scale-out measures **−0.308 R/day** against the plain exit (n=67, thin —
>   a question, not a recommendation); the armed `crypto` sleeve has its **first positive
>   out-of-window number** (+0.0869 R/day, n=182, 2017–2026, p 0.30).
> - **The suite baseline is committed** — see `docs/audits/fable5-vision-audit-20260725/receipts/`
>   for the wave-7 train capture; diff against it with `scripts/pytest_failset.py`, never
>   re-capture the before side. Full-suite A/B is the orchestrator's, once per merge train.
>
> **Wave 8 has landed (merged 2026-07-30).** What it settled, in one paragraph each:
>
> - **The multiplicity family is now a declared artifact** (`phase8/receipts/CANDIDATE_FAMILY_V1.json`,
>   ratchet enforced by `walkforward/candidate_family.py`): the family is `active_specs`' own 32,
>   enumerated from code that cannot see a return. The historical 69-look family **double-counted**
>   (W's and X's looks are subsets of AA's 32), so published q-values were over-corrected. At the
>   declared family `mx_btcusd` + `sub_xvol_pullback` flip to ADMIT **as a pair — but only at
>   α = 0.20, which `options.py:110` itself disqualifies for arming**. At the sealed α = 0.10 the
>   binding constraint is `sub_xvol_pullback`'s p on RECORDED eras (0.012 vs a 0.0034 rank-1 bar);
>   the two closers are banked prescriptions needing no new data (its `vr ≥ 1.4` variant n 88→420;
>   `mx_btcusd` `target_5R` on RECORDED) — wave 9 Session AL is running them.
> - **The entry hour is the FX D1 cohort's lever** (AH): 100 % of its fills land at broker hour 00,
>   the 13–38× hour; entering at the first H4 close is worth +0.063…+0.141 R/trade net, 38/42
>   members improve, `mx_cadjpy` crosses zero. Member conditioning is **refuted** as a lever (coin
>   flip OOS); the era×hour composition is repaired (damped b = 0.4947, 0 verdicts move); the bar
>   `spread` column is the within-bar MINIMUM — blind to the rollover at H4 by construction.
> - **Four registry-orphan generators judged for the first time** (AK, 7,919 trades) and AD's
>   exit-sweep gap closed: **`sub_xvol_pullback` (armed) had no exit frontier** — ~~`target_4R`
>   +1.157 R/day~~; `asia_pdl_fade` −0.069 → +0.085 with 5/5 folds on one stop cell.
>
>   > **Corrected at source 2026-07-30 by Session BD (AS handoff 5), because this line has been
>   > cited three times and is wrong in two independent ways.** (1) **+1.157 R/day is the LEVEL of
>   > the `target_4R` cell, not the improvement.** `as_walked` is 1.0264 and `target_4R` is 1.1565,
>   > so the change at AK's own standard is **+0.130 R/day** — reading the level as the delta
>   > overstates it **8.9×** (B1524). (2) **AK measured it at a standard that does not govern the
>   > estate**: `AK_EXIT_FRONTIER_V2.json` carries no population key and no `spread_band`, i.e.
>   > **ALL_ERAS at the flat 37-day snapshot at the historical 69-look family**, where the ratified
>   > rule is RECORDED, banded, at `CANDIDATE_BOOK_V1` (B1525). Re-gated at the ratified rule the
>   > delta is **+0.3435 R/day**, 2.6× the ALL_ERAS figure and identical across all four bands
>   > (B1526) — the magnitude is *larger*, which is why this correction is not a demotion.
>   >
>   > **And the verdict is the part that reaches armed money.** AU gated the same cell with the era
>   > population AK never set and it **REJECTS at all four bands**, p 0.0080 against a 0.002083
>   > rank-1 bar — on the one ARMED sleeve in the set — while its **train window is negative
>   > (−0.190 / −0.278 R) and its test window is +1.02 / +1.37**. A bigger delta and a failed
>   > admission are not in tension: one is magnitude, the other is evidence. The contract is wired
>   > and OFF (`--frontier-exits sub_xvol_pullback`); AS handoff 3 is *"do not propose it."*
>   `structural_retest`'s F7 clock repaired; a second raw-UTC site in `BUILT`
>   (`sub_mid_dn_revert`, 50.04 % of bars mis-bucketed) awaits wave 9's re-derivation. A
>   Kelly-lite `unknown_sleeve` sizing hazard (+32.5 %) is pinned by tests; registry-edit safe
>   order: **confidence weight first, spec second**.
> - **The books at firm-true rules** (AI): armed three P2 0.9172 FTMO / 0.9331 redacted_account (98 % of
>   the gap is the cost series; **inverts if redacted_account's max-DD is trailing — one captured page
>   decides redacted_account arming**). AD's tier restatement at measured carry is **+35 %/month for
>   1.3–2.6 pp of `p_pass`** — a real trade-off, Borhen's. At registry confidence 0.025,
>   admitting `mx_btcusd` is economically inert — re-weighting is a separate owner decision. The
>   pre-gap fix is **wired** behind `run_book.py --recover-pre-gap-bar` (no config byte moves),
>   default off. The sleeve dossier (`phase8/receipts/SLEEVE_DOSSIER_V1.json`, rules R0–R11) is
>   the one-truth-per-sleeve artifact; 30 population disagreements stamped.
> - **The owner queue is consolidated at `phase8/OWNER_DECISION_QUEUE.md`** with
>   `phase8/VPS_CEREMONY_PACKAGE_2.md` — whose **step ZERO is the `include_clean3` host read**
>   (see the armed-set bullet above). **The ceremony was EXECUTED 2026-07-30** directly on the
>   host over host-admin (owner-directed): all 9 carry files verified at after-bytes,
>   `verify_carry.py --check all` PASS, monitor daemon restarted on carried code, and the
>   arming + carry **committed on the host branch (`118071eaa`)** so no checkout can disarm
>   the book. Books were never restarted — they already ran the carried code. Receipt:
>   `phase8/receipts/VPS_CEREMONY_COMPLETED.md`. C5 stays OFF (OD-AI-7 open).
>
> Wave 9 landed 2026-07-30 (AL B1150–B1199: the first sealed-α ADMIT; AM B1200–B1241: the
> re-clock and the one-hour entry lever). **Wave 10 landed 2026-07-30**: AN (B1250–B1266)
> wired the population axis — 240 gated arms, exactly 9 ADMIT, **all** `mx_btcusd` on
> `RECORDED`; the coverage hole is closed and the **admission decays chronologically**
> (recent folds +0.198 R/day = 13.2 % of the early folds' +1.504 — size on the recent folds;
> no gate can see decay by construction). AO (B1300–B1349) measured that AB's regime dials
> ARE the substrate sleeves' own firing coordinates (identity filter — a bucket-level regime
> gate is a no-op there, pinned by 14 tests), killed its own would-be pair admission on the
> permutation test's resolution floor (2⁸ assignments at n=44; the BH rank-1 bar sits below
> the floor), and moved `vr` to the sizing lane (monotone: tertile net R/trade
> 0.512 → 1.111 → 2.124, perm p 0.00025). **The population rule is RATIFIED: `RECORDED`
> with AN's conditions** (Borhen 2026-07-30; `phase10/receipts/POPULATION_RULE_V1.json` →
> `ratified_rule`, pinned by `tests/research_infra/test_population_rule_ratified.py`) — so
> ~~the estate has ONE standing admission, `mx_btcusd @ target_5R`, published as "admits at
> two of three cost bands", challenge-account-bound at registry weight.~~
>
> > **STRUCK 2026-08-07 (wave-20 lane p4). THE ESTATE HAS NO STANDING ADMISSION.** That cell
> > flipped **ADMIT → REJECT** under A1b's corrected permutation null (q 0.129–0.135 against
> > α = 0.10; D-2 in `phase19/SESSION_FA_CONTINUATION_RESULT.md`), and wave 20's m3 composed the
> > two independent repairs and proved the quote-side walker adds nothing to the flip — corrected
> > p 0.002810 → **0.002843**, +1.2 %, no verdict moves (`phase20/SESSION_M3_ESTATE_RESTATED.md`
> > §2.3). **The sleeve was then DISARMED on FTMO on 2026-08-05 by owner instruction** (host
> > `2fa77722d`). The published "admits at two of three cost bands" is still literally true of the
> > *raw* p at the ratified rule and still false as a verdict — cite it only with the null named.
> > At the ratified rule every sleeve that has ever touched real money REJECTS
> > (`phase20/SLEEVE_FORENSIC_REPORT.md` §3). Register:
> > `phase20/forward/SUPERSEDED_CLAIMS_V1.json`. **Wave 11 landed 2026-07-30 (AP B1350–B1385, AQ B1400–B1453, AR B1450–B1499
> — AQ borrowed B1450–53, letter-disambiguation not needed, both sets written):** AP cleared
> the decision queue (the energy transfer bought coverage 100 % and robustness, NOT
> significance — the FVG residual is YEARS of sample; the pre-gap premise is CONFIRMED as an
> H4-index daily-close pattern, flag stays OFF on the economics). **AQ found the estate's one
> admission was contingent on a contract repair that had not landed, and landed it**: `mx_*`
> time stops carried `96` — the M15↔D1 conversion RATIO, not a horizon — now `7680` via
> `execution_packets.py` (R2-unbound; armed sleeves asserted unaffected by the driver). Under
> the live contract the admission REJECTS at all four bands (p 0.0564); under the repaired one
> it ADMITS at two of three (p 0.0011); five D1 sleeves were BETTER under the accidental 1-bar
> stop and get deliberate short-horizon decisions. Hour-01 confirmed (+0.11 R/trade) but 0/72
> admit — a cost repair, not an edge. **AR built the `vr` tilt (`run_book.py
> --vol-level-tilt`, default OFF) and recommends NOT arming** — its own control proved the
> +1.119 pp book headline was 85 % equity-path artifact; the clean instrument (risk-weighted
> efficiency vs blind constants) shows the ORDERING is real (125× separation on RECORDED) and
> the book payoff wins one band of four. **Compounded book return is not a valid instrument
> for a sizing change** — now a binding standard, with the maxbars-share rule (AL's published
> frontier carries 20.6 % unreported truncation at its own winner) and the two-layer
> identity-filter check. Family artifact: two parallel V4s merged as V4 (AQ) + **V5 = the
> union** (CANDIDATE_BOOK 48, MECHANISM_CROSS 321). **Wave 12 running: AU contract wiring +
> estate restamp B1550–B1599, AV the sample engine B1600–B1649; AS (B1500–B1549)
> live-activation dossiers launched alongside.**
>
> > **Session AU has landed (B1550–B1593, `phase12/SESSION_AU_CONTRACT_WIRING_RESULT.md`), and
> > the headline is about ARMED money.** `run_book.py --frontier-exits <sleeve>[,<sleeve>]` makes
> > `target_5R` and `target_4R` runnable — a per-sleeve selection, not a boolean, because the two
> > are in opposite live states, and default-off. The wired contract is proved **economically
> > identical trade by trade** to its research cell (318/318 and 88/88), and the standing admission
> > survives the round trip at a **tighter** bill (V5's 48, p 0.0011, admits at two of three bands).
> > **But `sub_xvol_pullback @ target_4R` — AK's frontier winner on the one ARMED sleeve — had
> > never been gated at the ratified rule** (`ak_supply_gate.py` sets no `spread_band` and no era
> > population: flat 37-day snapshot on ALL_ERAS), and it **REJECTS at all four bands**, p 0.0080
> > against a 0.002083 bar. Worse, publishing AR's two dropped gate fields for the first time shows
> > that sleeve's **train window is negative (−0.190 / −0.278 R) while its test window is +1.02 /
> > +1.37** — the same sign inversion AR found on a candidate, here on armed money. Neither is a
> > reason to disarm; both belong in front of Borhen before any sizing decision touches it. Also:
> > `regime_inflation`'s CLEAN verdict was printing *"haircut x0.050 (~1.0)"* on the standing
> > admission — wrong by 20× inside its own sentence, now fixed with the binding term and floor
> > flag published; six D1 sleeves get a **deliberate short horizon** declared at the ratified rule
> > (for four of them the value is `time_stop_m15(1, "D1")` = 96, the integer AQ removed — a
> > declaration now, not an accident, and every cell still REJECTS); `SLEEVE_DOSSIER_V1.json`'s
> > stale 96 is closed on 12 sleeves; and `sub_mid_dn_revert`'s exit frontier rebuilt on the
> > re-clocked population moves from **−0.106 R/day with `expectancy` failing** to **+0.092/+0.059/
> > +0.008 with it passing**, best cell `time_stop_20` → `time_stop_40`.
>
> **Session AQ has landed (B1400–B1447, `phase11/SESSION_AQ_CONTRACT_TRUTH_RESULT.md`), and
> the headline reaches that standing admission.** `mx_btcusd @ target_5R` holds 82.3 % of its
> trades past 24 h, and until 2026-07-30 the live engine would have closed all of them at ~24 h
> because the `mx_*` D1 cohort's `time_stop_bars` was the M15-per-D1 conversion ratio rather
> than a horizon. Under that contract the admission **REJECTS at all four bands**. The unit
> repair landed this session (see the `time_stop_bars` bullet above), moved nothing armed, and
> **the admission now describes a contract the book can run** — but any package citing it must
> name the repair as well as the exit cell. Also: AM's `sub_mid_dn_revert` re-clock finally has
> an artifact of record (`phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz`, 503 → 533; four
> downstream artifacts are still stale on the old clock); the ratified hour-01 entry convention
> is **confirmed on the third mechanism AM never covered** (+0.111 R/trade net vs hour 00,
> beating hour 04 by +0.037) and still admits nothing (0 of 72 arms, best p 0.380); and
> `GateResult.family["wipeout"]` now fires when a whole run of nulls would otherwise tabulate
> as a result.
>
> **RATIFIED 2026-07-30 by Borhen ("yes please proceed as proposed and recommended"): the
> admission rule is `CANDIDATE_BOOK_V1`, all-declared basis, at the sealed `B_balanced`
> α = 0.10** — recorded with provenance in `phase8/receipts/CANDIDATE_FAMILY_V1.json`
> (`ratified_rule`) and pinned by `tests/research_infra/test_candidate_family.py`. α = 0.20
> remains research triage only; no admission at 0.20 reaches a book. Sleeve composition, the
> dial, and arming remain separate owner decisions.

> **Plan position, 2026-07-28 — wave 3 has landed. Read this before picking up any stage item.**
>
> **`FULL_VISION_PLAN.md`'s Phase 2–3 sequencing is superseded** by the constrained plan in
> `docs/audits/fable5-vision-audit-20260725/THIRD_REVIEW.md` §4, **approved in full by Borhen on
> 2026-07-27**. The plan's own author (Fable 5) found that its middle phases inverted the charter:
> they schedule a monolith-scale rebuild *before* any activation-bearing decision, for a policy family
> whose measured economics are negative in every campaign-grade window ever run. `BroadV4Policy` is
> demoted from primary to optional; the ≤3 GB/arm gate is **withdrawn** (H3); the B7.5 campaign is
> **parked with a price**, banked first.
>
> **Stage 0 and Stage 1 are delivered.** Six sessions merged 2026-07-28 (Session O, blocks B180+):
> 0.1/0.2 safety spine (I), 1.1 broker-truth cost layer (J), 1.2 W7 re-cost (N), 1.3 generation port +
> K1 + G4 (K), 1.4 evidence packs (L), 1.5 hygiene (M). Wave 3 is `IMPLEMENTATION_STATE.md`
> **B100–B172** plus **B180–B199**. Integration receipt: `phase3/WAVE3_INTEGRATION.md`.
>
> **The two measurements that were supposed to reach OD-3 both came back, and they did not settle
> it — they relocated it.** Stage 1.2 expected commission to be the contamination and found it is
> **not**: commission is 0.0000 R on the index sleeve and material only on the two `conf 0.15` JPY
> sleeves. The legacy cost map was wrong in *direction* as often as magnitude, over-charging 6 of 11
> sleeves and under-charging 5. The book survives re-costing at **−12.3 %** on the daily mean, and
> **no sleeve is killed by commission**; two were negative before any cost was charged.
>
> **What now decides OD-3 is holding time.** Swap is the largest single broker cost for eight of
> eleven sleeves, **no exit index survives in any cache**, and the band that leaves open is not a
> rounding error: at one night of average carry the book is ~~`P(pass) 0.951`~~ and **1.97 %/month**;
> if every trade ran to its structural horizon it is ~~`P(pass) 0.450`~~ and **0.13 %/month**.
>
> > **Amended 2026-07-29 (B230–B244) — those two `P(pass)` values were computed at the wrong firm
> > rules, and the correction goes UP.** `INTEG_portfolio_build.py:298` hardcodes redacted_account's 8 %
> > target for both accounts (true), *and* a **trailing** drawdown where FTMO's is a **static
> > $90,000 floor** [MEASURED], *and* a daily loss on the day's opening equity where both firms use
> > a fixed 5 % of the **initial** balance. Net at each firm's measured rules the two figures are
> > **0.954** and **0.458**, and every `p_pass` in `SURVIVOR_BOOK_V1.json` moves up, not down.
> > **The number that actually moves is time.** Nothing published had ever modelled **phase 2**,
> > which both firms require at 5 %: across the whole 2-step evaluation the same two cells are
> > **0.931** and **0.300**, so the 11-sleeve book does *not* clear a two-phase evaluation at worst
> > carry — and the survivor book's calendar time to a payout roughly doubles (52 → 66 → **110**
> > days, FTMO fwd/worst). See `research/operations/w7_recost_2026_07_27/MC_FIRM_TRUE_V1.json` and
> > `docs/audits/fable5-vision-audit-20260725/phase3/SESSION_Q_MC_TRUE_TARGET_RESULT.md`. The
> > sealed constants are **untouched** and the 8 % result still reproduces byte-identically.
>
> > **Amended 2026-07-28 (B173–B177, B200–B201). Struck: "and nothing in the tree records it" and
> > "Five of eleven sleeves are CARRY-CONDITIONAL."** Both were written before Session N's live-carry
> > measurement merged, and the last edit to this section only filled in the A/B figure. The caches
> > record no exit index — that half stands. But the **live W7 window measured the carry of three of
> > the eleven sleeves directly**, from the packet export at
> > `/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/ultimate_book_runtime_learning_packets.jsonl.gz`
> > (outside the repo) plus Session J's deal-record extraction. **The broker charged swap on zero of
> > the 41 live JPY-sleeve positions** (`fx_jpy` 0/32, `fx_jpy_ny` 0/9) and on 39 of 59 `idxrev`. The
> > swap field validates against its own structure with no false positives: of 300 rows, 76 cross a
> > broker midnight and 74 carry nonzero swap; 224 do not cross and **all 224 are exactly 0.0**.
> >
> > **Use the live holds for sleeve-median comparison only — not as a bias-corrected series.**
> > Session P first concluded "the 148 holds are admissible" (B200) and then **refuted its own
> > conclusion** (B215): the +28 s correction is unmeasured on **39 %** of the corpus, and that gap is
> > a *calendar block*, not noise — of 57 rows closing before 2026-06-24 exactly **1** carries
> > `broker_exit_time_utc` (2 %), against **89 of 91** (98 %) after. The lag is three populations, not
> > one (`broker_closed` n=82 **+27.35 s**; `vnext_time_stop` n=6 **−0.03 s**;
> > `broker_closed_absent_on_reconcile` n=2 **+761.8 s**), so a uniform +28 s *adds* error to
> > book-initiated closes and is 27× too small for the reconcile rows. It also fails in the left tail
> > — the shortest broker-true hold of 35.0 s reads as 61.6 s (+76 %). **The anchor choice matters
> > 128× more than the bias term**: three medians exist and differ by **44 %** — 2.2565 h at packet
> > emission, 1.8783 h by `closed_at_utc`, **1.2603 h by broker truth. Use the broker figure.**
> > Against break-evens of 10–320 h none of this changes a sleeve verdict, which is exactly why the
> > weaker claim is the honest one.
> >
> > **Tiers now, from the artifact and not from prose** (`SURVIVOR_BOOK_V1.json`, verified by direct
> > read): UNCONDITIONAL `metals_core` / `crypto` / `energy_agri` / `sub_xvol_pullback` (4);
> > MEASURED_LIVE_CARRY `fx_jpy` (1); CARRY_CONDITIONAL_LIVE_SUPPORTED `fx_jpy_ny` (1);
> > **CARRY_CONDITIONAL `metals_softband` / `vp_euidx_pocgrav` / `sub_mid_dn_revert` (3)**;
> > DEAD_BEFORE_COST `idxrev` / `metals_ob_micro` (2). ~~So it is **three** sleeves fully open, not
> > five.~~ N's own adversarial pass refused to close the three by analogy and was right to: across
> > the twelve live sleeves the used-fraction of horizon runs **0.4 % to 105 %**, three exceeding
> > their nominal horizon, so it is not a constant and cannot be transferred.
> >
> > > **Amended 2026-07-29 at wave-4 integration (B358). The tier list above is FTMO's, and it was
> > > written as if it were the book's.** `survivor_tier` is stored **per account** —
> > > `accounts.<acct>.sleeves.<sleeve>.survivor_tier` — and the two accounts disagree on two
> > > sleeves. The error hid because the *counts* are identical:
> > >
> > > | tier | FTMO | redacted_account |
> > > |---|---|---|
> > > | UNCONDITIONAL (4 each) | `metals_core`, crypto, energy_agri, sub_xvol_pullback | crypto, energy_agri, sub_xvol_pullback, `vp_euidx_pocgrav` |
> > > | CARRY_CONDITIONAL (3 each) | metals_softband, `vp_euidx_pocgrav`, sub_mid_dn_revert | `metals_core`, metals_softband, sub_mid_dn_revert |
> > >
> > > `metals_core` and `vp_euidx_pocgrav` swap places, and Session Q measured why: the swap turns on
> > > the per-account swap rate, marginally — `metals_core` break-even **489 h** on FTMO against
> > > **329 h** on redacted_account, missing its own 320 h ceiling by 2.8 % (B238). The remaining four tiers
> > > (`fx_jpy`, `fx_jpy_ny`, `idxrev`, `metals_ob_micro`) are the same on both. So **"three sleeves
> > > fully open" was the count of the INTERSECTION**, not a property of either account: each account
> > > has four UNCONDITIONAL sleeves and they share three
> > > (`crypto, energy_agri, sub_xvol_pullback`).
>
> **Recovering the remaining three is a data fetch, not a sealed window** — a generator re-run against
> `data/mt5_research_exports/bridge_ftmo_deep_h4_*`, which is absent from this machine. It is the
> cheapest thing that would sharpen OD-3 and it is the next unit of work.
>
> **Do not read wave 3 as "the W7 book is validated."** It is *not killed by cost*, which is a
> weaker and different claim. Two independent reasons to stay sceptical, both from wave 3's own
> sessions: **46.9 % of the survivor book's edge rests on 194 trades** with in-sample selection
> concentrated in `crypto` and `sub_xvol_pullback` (N §8.2), and **88.5 % of core-8's confidence
> weight sits in sleeves statistically consistent with having generated nothing** across the entire
> 38-day live window (K's G4). The fortnight that triggered OD-1 never tested the book's core.
>
> Everything from wave 1, wave 2, wave 3, the third review **and wave 4** is merged to `main`.
> Wave-2 integration A/B'd at **695 bad → 695 bad by failure set, 0 regressed, +145 net new passing
> tests**; wave-3 integration at **673 bad → 650 bad, 0 stably regressed, 24 fixed, +234 net new
> passing**; wave-4 integration at **660 bad → 660 bad by failure set, 0 regressed, 0 fixed — the two sets
> byte-identical — and +163 net new passing tests**. All three receipts live under
> `docs/audits/fable5-vision-audit-20260725/receipts/` — corrected 2026-07-29, this line said
> `receipts/WAVE{2,3}_INTEGRATION_AB.md` and there is no `receipts/` directory at the repo root, so
> the citation cost every reader who followed it a failed `ls`.
> Full detail in `IMPLEMENTATION_STATE.md` blocks **B1–B99e** for waves 1–2; **wave 3 from B100**;
> **wave 4 is B230–B244 (Q), B260–B289 (R), B290–B319 (S), B320–B349 (T), B350–B379 (U)**.
>
> **Wave 4 delivered** (merged 2026-07-29, Session U): Q the MC at each firm's *measured* prop rules
> and phase 2 (`phase3/SESSION_Q_MC_TRUE_TARGET_RESULT.md`); R the learning lane closed, live-aware,
> default-off and brake-only (`phase4/SESSION_R_LEARNING_LANE_RESULT.md`); S the packet carry
> re-authored against the VPS lineage it will actually run on
> (`phase4/SESSION_S_PACKET_UNBLOCK_RESULT.md`, `phase4/PACKET_UNBLOCK_VPS_RUNBOOK.md`); T the eight
> token chaos drills, the owner-facing canary page, and **the strand fix** (`phase4/CANARY_OPERATOR_PAGE.md`).
> Integration receipt: `phase4/WAVE4_INTEGRATION.md`.

- **Program — restated 2026-07-28 after wave 3.** The active program is still the
  **activation-candidate decision (OD-3)**, but its blocking input changed. Stage 1.1–1.5 are
  delivered; what OD-3 now waits on is **holding time** (above), then a cost-true survivor book — or
  an honest kill — in front of Borhen. **B7.5 cross-window selection–sizing decomposition stays
  parked**, banked, and priced as an expiring option (§6.2 of the third review); it is not the
  program.

  **The asymmetry that drove wave 3 held, but not for the stated reason.** The broad V4 stack's
  evidence is **negative and unrepairable** (four negative January arms, sizing sealed
  `material_negative`, −0.25 R/fill native live, −1,683.5 R admitted on the June validation frame; the
  least-bad cell was the dumb neutral reference). **Precision added 2026-07-30, at the owner's
  challenge:** "unrepairable" is a claim about the incumbent POLICY LAYERS (the two tested
  switches + dynamic sizing), not about the underlying pool — `JANUARY_BANK.md` §3: the reference
  arm's diagnostic pool carries **±38,317 R of separable opportunity over 28,519 rows in one
  month**, and whether ANY rule separates it is *"open and unmeasured at any useful resolution"*
  (a two-bit experiment cannot test separability). Session AW (`phase12/SESSION_AW_SEPARABILITY_MINE.md`,
  B1650–B1699) measures it for the first time — mining the sealed diagnostic exhaust at modern
  multiplicity discipline, out-of-window tests on the fast machinery, March never read. The W7 book's evidence was **invalid and
  repairable** — a positive 1,679-day validation contaminated by a cost model charging **zero
  commission** (F38, `broker_net_cost_engine.py:577-583` sums `spread + slippage + swap`) and
  crediting tick erosion with the **wrong sign** (F39). That repair is now **done**, over the caches
  as predicted (`INTEG_W3_streams_cache.pkl` + `INTEG_W5_new_streams_cache.pkl`, 678 KB, arithmetic
  not a re-backtest) — and it changed the shape of the answer:

  > **Corrected by measurement, B150–B164.** The third review expected commission to be the
  > contamination. It is not. `THIRD_REVIEW.md` §1.2 cited "realized commission+swap was 31.6 % of
  > the live W7 loss" and read it as a commission problem; at the validation's own stop geometry
  > **commission is 0.0000 R on the index sleeve** and material only on the two `conf 0.15` JPY
  > sleeves. **The 31.6 % was mostly swap.** So the repairable defect was real and the repair
  > worked, but it left the book's fate resting on the one input the caches cannot supply.

  **Read `THIRD_REVIEW.md` §1.2 and §4, then `phase3/SESSION_N_W7_RECOST_RESULT.md` §0 and §8, before
  proposing any work.** OD-1 is reopened as OD-3.
- **The clock is now measured, and it is the US DST calendar, not EET/EEST.** Broker server wall clock =
  `America/New_York + 7 h` for **both** FTMO-Server3 and redacted_account-Server 2 (VPS-measured over 81 weekly
  session boundaries per broker; all transitions on US dates, none on EU dates). Use
  `src/utils/broker_clock.py`; it **fails closed** on an unregistered server. Never hardcode +3 — the two
  calendars disagree ~4 weeks a year, including **2026-03-08..03-28, inside the sealed March window**.
- **The daily-loss reset is per account, and the two firms differ.** FTMO resets at **00:00 CE(S)T**
  (its own captured page, and `config/profiles/operator_profile.yaml:104`); redacted_account at **00:00
  server time**. These are different clocks — a firm's reset rule is not its MT5 server clock. See B56.
- **Research tick data lives OUTSIDE the repo** at `/Users/borr/GTOSActive/vps-ticks-20260726/`
  (2.05 GB, 51 files, FTMO + redacted_account, 2026-06-18..07-24, **263,894,769 rows**, all sha256-verified —
  corrected 2026-07-27 by scanning every row, B114; the previous "191.9 M" was the subtotal of manifest
  **V2 only** (32 files), and `TICKS_MANIFEST.jsonl` (V1) covers the other 19 at 71,997,348). Its `time`
  and `time_msc` columns are **broker wall clock, not UTC** — every file carries a `.timebase.json`
  saying so. Convert with `broker_clock.broker_epoch_to_utc`; never trust a `_utc` field name.
- **Campaign state — PARKED 2026-07-27, with a price, and banked first.** January development is sealed
  and accepted (four arms S0R0/S1R0/S0R1/S1R1, all negative). **April is 15 sealed days** — not "16 of
  30", corrected per B36 — and it **carries no partial credit**: the runner refuses any non-fresh output
  namespace (`b7_5_post_acceleration_runner.py:292-315`) and hardcodes sub-window away on the sealed path
  (`:832`), so the stopped S1R1 cannot resume. Finishing the campaign under the frozen engine costs
  **~36 machine-hours serial** (April 16.5 + May ~2.7 — May is ~3 trading days — + March 16.5), and the
  option **expires at the first bound-file edit** (then +16.5 MH to re-run January for comparability).

  **Two hard conditions before any window ever runs again.** (1) The **pooled promote/reject/inconclusive
  evaluator does not exist anywhere** — verified: zero threshold keys in any Python; the only pooling
  artifact is `factor_or_policy_promotion_authorized: False` hardcoded in two analyzers. Reading April's
  outcomes without it would improvise the terminal decision post-hoc. It must be **written and sealed
  first**. (2) The protocol seals the thresholds but **not the pooling weights** (by-window vs by
  risk-cash), so even the pooling semantics would otherwise be chosen after seeing the data.
  Promotion is arithmetically near-foreclosed regardless: pooled must exceed +0.1 from a −0.152 start.

  **Keep March outcome-unread.** It is the only untouched month for any future broad-family treatment,
  and it is the scarcest resource in the programme. See `JANUARY_BANK.md` for what was banked before the
  park.
- **Runtime — CORRECTED 2026-07-26 by direct inspection of the VPS. The "hard halt" does not exist.**
  A read-only export session on the Windows VPS established [MEASURED]: **no `*.flag` file exists
  anywhere in either tree.** Not `GTOS_HARD_PRODUCTION_HALT.flag`, not `RESEARCH_RUNTIME_HALT.flag`, not
  `AUTOSTART_DISABLED.flag`, and neither of the two `ULTIMATE_BOOK_KILL_*.flag` paths `run_book.py` is
  actively watching. The only halt artifact is one **archived** file renamed on 2026-05-18. Meanwhile the
  supervisor task is **Running**, both books are healthy, both MT5 terminals are connected, and
  `trade_allowed` is **true** on both.

  **The entire brake is three false YAML booleans** — `apply_to_execution`, `live_activation_allowed`,
  `live_broker_authority`, at exported working-tree `agent_config.yaml:1161-1163`. (Corrected
  2026-07-27; this file previously said "one config line". Line-number caveat added 2026-07-30 from
  AT's B908: `:1161-1163` is the **exported VPS file's** numbering; in THIS repository the
  ultimate_book gates sit at `config/agent_config.yaml:1248-1250` and `:1161-1163` are
  `validation_anti_overfit_v4_*` keys. A committed test, `test_a8_live_activation_config.py:76`,
  asserts mainline is armed and fails — mainline is *not* armed; the arming lives in the VPS's own
  config. Use the right line numbers for the tree you are reading.) There is no second line of defence — no
  flag, no terminal block, no scheduler stop — and, the part that matters most, **no monitoring watching
  the gate.** Nothing on that host would detect a flip. `ultimate_book_live_broker_authority: true` has
  never existed in any committed config, so accidental single-line drift cannot fire it; the exposure is
  a deliberate or erroneous edit, unobserved. F2 predicted the flag mechanism could not protect a fresh
  clone; the truth is worse, because it is not protecting the **live machine** either. Every prior
  statement in this file and in both audits that GTOS is "hard-halted as broker/VPS state" was describing
  flags that do not exist.

  **The activation token is on mainline only** (`src/mt5/mt5_real.py:28` imports it here). The VPS copy's
  `RealMT5.order_send` calls the raw module with **no guard** (`git show redacted_host:src/mt5/mt5_real.py`).
  Carrying it across is **Stage 0 item 0.1 — the first work item of wave 3**, ~0.5–1 session plus an
  owner-executed VPS ceremony, and deployment-safe while the gates are false.

  Treat the halt as **three false YAML booleans on a running, funded, connected host** — corrected
  2026-07-27 at wave-3 integration; this sentence still said "a single YAML boolean" while the
  paragraph above it had already been corrected to three. Do not add a second
  flag to feel better; port the activation token (below) to the VPS, which is the mechanism that makes
  absence fail closed.
- **Activation tokens are now the primary brake (2026-07-26).** Absence-of-halt is fail-open on a fresh
  clone (F2); presence-of-authorization is not. `RealMT5.order_send` refuses any **exposure-increasing**
  request without a valid token for that account (`src/safety/activation_token.py`); risk-reducing
  requests — closes, partial closes, pending cancels, stop tightenings — pass **without** one, so an
  expired token can never strand a position. Tokens live in `$GTOS_ACTIVATION_TOKEN_DIR` or
  `~/.gtos/activation`, deliberately outside the repo. Mint/inspect/revoke with
  `scripts/gtos_activation_token.py`. **There is no config flag to disable this** — the token is the switch.
- **BOTH ACCOUNTS ARE ARMED AND TRADING REAL MONEY. FTMO armed 2026-07-29 12:55 UTC
  (three sleeves since 14:25); redacted_account armed 2026-07-30 ~05:18 UTC on the same three
  sleeves** (OD-AI-2, owner-ratified; receipt `phase8/receipts/FN_ARMING_20260730.md`, host
  commits `118071eaa` + `eb7c28516`). Every statement elsewhere in this file that GTOS — or
  redacted_account specifically — is halted, gated off, or in shadow is **false** as of those
  timestamps. Read this bullet before acting on any of them.

  | | FTMO | redacted_account |
  |---|---|---|
  | `authority_gates_ON` (the book's own log) | **True** | **True** (2026-07-30 05:15:18Z) |
  | three gates | VPS `agent_config.yaml` **all `true`** | **`true` at `config/profiles/redacted_account.yaml:11-13`** (was the shadow override) |
  | activation token | **valid to 2026-08-14**, binds `ffe16657feaf` (re-minted 2026-08-01 under OD-ALL-IN, digest unchanged, flat 0/0) | **valid to 2026-08-14**, binds `e184a81d3b1b` (same re-mint) |
  | `run_book.py --tags` | **FOUR sleeves since 2026-08-05 ~14:33Z** (`crypto`, `energy_agri`, `sub_mid_dn_revert`, `sub_xvol_pullback`; **no `--frontier-exits`**) — `mx_btcusd` DISARMED by owner instruction, host `2fa77722d`, D-2 CLOSED. Authority: `src.safety.armed_set.armed_sleeves()`, never this table. ~~FIVE sleeves since 2026-07-31 ~01:26Z~~: the four + **`mx_btcusd_d1_donchian_20_breakout` on `--frontier-exits` (target_5R)** — the estate's first sealed-standard admission, live (`phase13/receipts/MX_ACTIVATION_20260731.md`; host `d6c9c4b19`). History: 3→5 on 07-30 ~11:52Z, `fx_jpy` pulled ~14:57Z on AV's evidence (`phase8/receipts/FXJPY_PULL_20260730.md`) | the four core sleeves — no frontier, untouched |
  | kill flag | **released** | **released 2026-07-30** (held through each ceremony restart) |
  | decision timeframes | `[16388]` (H4-only again — M15 left with `fx_jpy`; derived from specs, `launcher.py:106-109`) | `[16388]` |

  **The 5-sleeve expansion** (owner-ratified twice, then clarified: "i accept activating the
  sleeves there" — the two live accounts ARE the proving ground; the third account, an inactive
  FTMO, is the RESERVE): receipt `phase8/receipts/FIVE_SLEEVE_EXPANSION_20260730.md`, host
  commit `f855250cd`. Priced at OD-AI-3 measured p99: P2 0.9172→0.8915 for 4.501→6.120 %/mo
  and 60→48 days (FTMO). Neither added sleeve passes an admission standard — armed on explicit
  owner risk acceptance, on the record. `mx_btcusd` is **LIVE on FTMO since 2026-07-31** at
  registry confidence 0.025 (economically small by design — the forward record is the point),
  sized on the recent folds (+0.198 R/day), via Session AZ's four-file carry (preflight PASS →
  all PASS → behaviour PASS; token digest unchanged).

  > **STOP — do not read the armed set out of this file. Corrected 2026-08-07 (wave-20 lane p4),
  > and this is now the third different set stated in this section.** Both statements around this
  > box are stale: the row above says FIVE on FTMO including `mx_btcusd_d1_donchian_20_breakout`
  > on `--frontier-exits`, and the paragraph below says "exactly three". **Neither is true.**
  >
  > **The armed set is FOUR on BOTH accounts: `crypto`, `energy_agri`, `sub_mid_dn_revert`,
  > `sub_xvol_pullback`.** `mx_btcusd_d1_donchian_20_breakout` was disarmed on FTMO on
  > **2026-08-05** by owner instruction (D-2 CLOSED, host commit `2fa77722d`; receipt
  > `phase19/receipts/vps_live_ops_20260805/MX_DISABLE_RECEIPT.md` on branch
  > `ops/vps-live-mx-disable-20260805`), and `--frontier-exits` went with it. The **committed**
  > launcher was not updated until 2026-08-07 and armed it for two days.
  >
  > **There is now a single source of truth and prose is not it.** Call
  > `src.safety.armed_set.armed_sleeves()`; it reconciles `config/live_armed_set.json` (the
  > owner-decision declaration, with a receipt per change) against
  > `scripts/run_book_supervisor.ps1` (the mechanism), and
  > `tests/safety/test_armed_set_single_source.py` fails the build if they drift.
  > **Do not write the set down again anywhere** — four artifacts did, and all four were wrong.
  > Receipt: `phase20/forward/P4_RECORD_CORRECTION.md`.

  ~~**The armed set is exactly three sleeves** — `crypto`, `energy_agri`, `sub_xvol_pullback`~~ — via
  `run_book.py --tags`, set at `scripts/run_book_supervisor.ps1:140` **(that is the HOST's line
  number; the committed file's `$books` array is at `:86` and the two files have diverged — 19,495 B
  on the host against 7,828 B here, and the spread-floor key is `floor` there and `spreadFloor`
  here. Never carry the committed launcher wholesale.)**. `metals_core` was in the
  12:55 set and was pulled at 14:25; AE's cost-true evidence (DOWN_WEIGHT ×0.50 on a
  232-trade/118-day OOS at −0.205 R) later landed on the same side as that pull. The registry
  itself resolves **32**; `--tags` is what bounds it, ~~and it is carried for FTMO only~~ **(both
  accounts carry `--tags` today — FN's four-tag row has been in the committed launcher since
  2026-07-31)**. A book
  restarted without `--tags` trades all 32 and its log looks perfectly healthy — check the command
  line, not the heartbeat.

  > **[VERIFIED 2026-07-30 — read directly on the host over host-admin/host-mesh, owner-directed]:
  > `ultimate_book_include_clean3: true` at host `:1200` ("ON 2026-07-29"), all three gates
  > armed, config written 12:54:30Z at the arming, FTMO workers carrying the three `--tags`.
  > The armed book IS the three-sleeve book and every published figure prices it. Receipt:
  > `phase8/receipts/VPS_STEP_ZERO_VERIFIED.md`.** The paragraph below is retained as the
  > history of why this had to be checked:
  > Three sleeves generate **only if** the host's `ultimate_book_include_clean3` is `true`. At
  > `false`, `effective_registry` is 29 and the `--tags` intersection resolves to **TWO** sleeves
  > (`crypto`, `energy_agri`) — `sub_xvol_pullback`, the survivor book's highest per-day R, would
  > be silently absent while every log reads healthy. Mainline carries `false` at `:1270`; the
  > read-only 2026-07-25 export carries `false` at its `:1200` — captured four days **before**
  > the 14:25 arming, so it cannot settle the question; this file's earlier "now true (:1200)"
  > claim describes the arming intent, not a verified host read. **One `Select-String` on the VPS
  > decides it, and it is step ZERO of `phase8/VPS_CEREMONY_PACKAGE_2.md`.** If false, every
  > published economic figure for the armed set (4.501 %/mo, P2 0.9172, the 0.313 %/mo archive
  > control, every redacted_account comparison) prices a book that is not running.

  **`ultimate_book_include_clean3` is now `true`** (`:1200`), which is what admits `sub_xvol_pullback`
  — the highest per-trade gross R in the survivor book (1.30698 on n=90) and structurally absent from
  the live path before this.

  **Do not edit `config/agent_config.yaml` without re-minting the token.** The token binds the config
  digest; a single byte changes it and the book refuses to place. Revoke with
  `python scripts/gtos_activation_token.py revoke --profile operator_profile` — instant, and it
  can never strand a position (risk-reducing requests never need a token). **To disarm with positions
  open, flatten FIRST**: setting `live_broker_authority: false` returns before flattening
  (`book_owner.py:2344-2353`) and strands them.

  **Expected economics, stated honestly:** the 5.46 %/month headline is measured on the window that
  *selected* these sleeves — `build_survivor_book.py:60` and `KB7_growth_kelly_sizing.py:130` share
  the `d.year >= 2025` predicate (Session V). Out of window the same four earn **+0.100 %/month over
  ten years** and **−0.220 % before 2020**. Treat the small number as the expected case. Expect
  **~7 book-days/month**; long silences are normal, not a fault.

- **Live decision surface:** the **`ultimate_book` W7 book**, not the broad selector.
  `config/agent_config.yaml:1246-1394`: `enabled: true`, `apply_to_execution: true`. Profile
  `clean3_w7_ceiling_nom2p00` (2.0 % nominal per account) with mandatory `derisk_mode: smooth` —
  and note that `GovernorLimits` defaults to `"band"`, with `smooth` held on **only** by the ≥2 %
  interlock, which a dial move below 2 % releases (Session V). Two fully independent per-account
  `run_book.py` workers — **not** primary/follower. See `live_system_of_record.md`.
- **What "the armed book" is, and the two things it needs — added 2026-07-29 at wave-4 integration
  (B359), because wave 4 used that phrase for three different sets.** Borhen has approved arming FTMO
  on its **four** survivors: **`metals_core`, `crypto`, `energy_agri`, `sub_xvol_pullback`**
  (`SURVIVOR_BOOK_V1.json` → `accounts.FTMO.survivors`). Read the *set*, never the count:
  - **No confidence floor can express it.** `sub_xvol_pullback` carries confidence **0.45** in the
    runtime's own table (`admission.py:218-219`) and `metals_softband` — killed on FTMO — carries
    **0.50**, so every floor low enough to admit the fourth survivor admits a killed sleeve. There is
    no `confidence_floor` key anywhere in the tree (B324; three code paths do filter on confidence,
    all hardcoded at zero). The mechanism is **`run_book.py --tags`** (`:100`, `:340-343`), which
    needs no source edit on a live host. `scripts/run_book_supervisor.ps1:108-109` passes **no**
    `--tags`, so the committed launcher runs the whole book (B327) — that is the one CRITICAL
    condition that can be wrong while every other indicator reads normal.
  - **Three of the four run today; the fourth cannot.** `sub_xvol_pullback` is a clean_3 sleeve, and
    `book_engine.py:425` + `:452-453` (the DF-1 filter) drop every spec outside
    `_active_sleeve_names()`, which reads `ultimate_book_include_clean3` — **`false`** at
    `agent_config.yaml:1270`. So the three-sleeve canary is not a set anyone selected on the
    evidence; it is the FTMO survivors minus the one the config cannot generate (T's B337).
  - **The live config resolves 29 generating sleeves, not 8.** Measured on `main` by calling the
    resolvers the engine calls: `active_specs` builds **32**, `book_engine.py:452-453` drops three
    (`sub_mid_dn_revert`, `sub_xvol_pullback`, `vp_euidx_pocgrav`), **29 can generate an order**, and
    `effective_registry` is the *same* 29 — generation and sizing agree exactly. Core-8 is the
    **minimum any of the 16 flag combinations can reach** (B325), not what is configured;
    `include_candidate_book: true` (`:1272`, 9 sleeves) and `include_market_expansion_book: true`
    (`:1284`, 12 resolved by the `positive_weighted12_after_swap` policy) are what make it 29.
  - **The key that admits the fourth sleeve is sealed — but not by the mechanism this bullet first
    named.** `config/agent_config.yaml` **is** one of R2's 43 bound paths (`common_behavior_inputs`).
    ~~so flipping `include_clean3` in this repository breaks the seal (H1)~~ — struck 2026-07-29 by
    an adversarial pass (B366). **H1's input-binding drift check does *not* catch a worktree-local
    flip**: the runner resolves each bound path against a fallback chain of `binding_roots` ending in
    `MAIN_REPO_ROOT = /Users/borr/GTOSActive/repo` and returns on the first root that matches
    (`replay_acceleration_attempt5_typed_sparse_runner.py:1046-1051`, `:1062-1072`). The seal still
    breaks — via `config_file_hashes` (`:1502-1511`) → `shared_execution_contract_digest_sha256` →
    `b7_5_post_acceleration_semantic_verifier.py:753-754`. **Cite the execution-seal digest, not the
    drift check.** Changing it on the live host's own config does not touch this repository's seal.
    Also worth knowing: `config/profiles/redacted_account.yaml` is bound by **neither** contract, while
    both FTMO profiles are. Measured consequence of the flip: the sizing registry goes 29 → 32 and
    total confidence weight 6.82 → 7.77 (**+13.9 %**); no sizing quantity reads registry size — the
    Kelly-lite conviction multiplier keys on sleeves *firing that day* (`admission.py:920-935`), and
    `GovernorLimits` has no count-scaled cap. It also happens to be what the
    active allocation profile already demands: `clean3_w7_ceiling_nom2p00` carries the note *"ONLY
    with include_clean3=True + kelly_lite=True + stress_derisk=True"*, and only the first is unmet.
  - **`--tags` bounds the conviction count PROSPECTIVELY ONLY, and arming mid-day is a +25 % size
    event.** [MEASURED by an adversarial pass, B365.] `RunningConvictionLedger`
    (`running_conviction_state.py:33-82`) **persists** a per-`decision_day` union of firing sleeves to
    `pipeline_state/ultimate_book/<namespace>/firing_sleeves.json`, and `admission.py:1188` takes
    `na = max(na, override)` — monotone upward within the day. It is armed live: `kelly_lite: true`
    (`agent_config.yaml:1303`), `kelly_conservative: true` (`:1304`), `kelly_running_count: true`
    (`:1305`). The exported VPS ledgers hold **6–7 distinct firing sleeves per day**. Restarting
    mid-day under a four-sleeve `--tags` inherits that day's wider set, and under the half-Kelly bins
    `((1,1,0.748),(2,3,0.991),(4,99,1.241))` an `na` of 2 → 7 moves the multiplier 0.991 → 1.241:
    **+25.2 % on every unit that day.** Mitigation: **arm at a decision-day boundary**, or delete
    that namespace's `firing_sleeves.json` first. `_KEEP_DAYS = 2` plus today-only keys mean prior
    days cannot contaminate a fresh day — the hazard is same-day only.
  - **Two `--tags` failure modes to know before the ceremony.** `--tags ""` is falsy at
    `run_book.py:340`, so an empty string silently means **all BUILT sleeves** — fail-open. An
    all-typo `--tags` yields an empty spec list and the book stands down silently every tick
    (`registry.py:144` drops unknown tags with no fallback and no error) — fail-closed, but mute.
    `--tags` can only ever *subset*: `book_engine.py:452-453` intersects it with the include-flag
    registry, so it can never add back a sleeve the config removed. And two `active_specs(None, …)`
    call sites are **not** intersected — `book_owner.py:489` (profile preflight) and `:2680`
    (`_manageable_pairs`) — so an already-open `sub_xvol_pullback` position would still be adopted
    and exit-managed even while it cannot be newly generated.
  - **[MEASURED: absence, by search of the recost route] no MC at 2.0 % exists for exactly the
    three-sleeve `metals_core, crypto, energy_agri` book** (T, B337; re-confirmed here against
    `MC_FIRM_TRUE_V1.json`, whose variants are `ALL_11_BOOK_OF_RECORD`, `SURVIVORS_ONLY` (4) and
    `SURVIVORS_BOTH_ACCOUNTS` (3 — but a *different* three: `crypto, energy_agri,
    sub_xvol_pullback`)). ~~**Do not adopt the `SURVIVORS_BOTH_ACCOUNTS` number for the canary**; it
    is the account-intersection book, not the config-runnable one.~~ **Struck 2026-07-30 (AI §3.1):
    the 14:25 arming adjustment INVERTED that warning — `SURVIVORS_BOTH_ACCOUNTS` is now exactly
    the armed set, and `metals_core, crypto, energy_agri` is the set that is no longer armed.**
    The armed three at firm-true rules, live sizing, fwd 2025+, worst carry: **P2 `p_pass` 0.9172
    FTMO / 0.9331 redacted_account** (`phase8/receipts/BOOKS_MC_V1.json`; the gap is 98 % the cost
    series, not the target, and inverts if redacted_account's max-DD is trailing — unestablished). The
    four-sleeve figures are FTMO `SURVIVORS_ONLY / fwd / worst-carry` **`p_pass` 0.99918 phase 1,
    0.99828 across both phases**, and the 2-step figure is the one that gates a payout.
- **`run_book.py`, the live entrypoint, IS in this repository** — corrected 2026-07-26. It was vendored
  by Phase 0 item 0.1b (`31cf05634`) and amended by `7c85c3105`; **19,886 bytes at HEAD** (18,032
  before wave 3 — Sessions I and M both amended it; see B181), alongside
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

  **Moved 2026-07-27.** The campaign's source-materialization evidence — 197 MB, January
  (`january-post-acceleration-source-20260723T225928Z`) and April
  (`april-post-acceleration-source-20260725T021800Z`), 290 sealed read-only files — lived only in the
  `phase2-columnar-source-20260726` worktree, which was retired after wave 2 merged. It is now held at
  **`/Users/borr/GTOSActive/hermes-evidence-hold-20260727/hermes/`**, seals intact. It was the **only**
  copy on this machine: the main repo has no `.hermes` at all. If the parked campaign is ever resumed
  (D-D), this is load-bearing — do not delete it with a worktree.
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

**CHECK WHETHER IT ALREADY EXISTS BEFORE YOU BUILD IT (owner instruction, 2026-08-12).** Only
**21.7 % of 1.33 M Python lines is reachable from a current entrypoint** — read the other way,
that is ~1 M lines of working, forgotten machinery, and the default behaviour is to rebuild it.
Four instances in a single day: a per-trade excursion census was built from scratch while
`AA_ESTATE_TRADES.json.gz` had held 22,324 MFE/MAE rows since wave 6; `LANE16_PATH_ANATOMY_LEDGER.jsonl.gz`
(**289,928 candidates × 78 fields**, 10-class path taxonomy) has never been read by anything; the
ATR two-estimator divergence was re-measured when `phase20/receipts/r2/R2_ATR_DEFS_V1.json`
already recorded it (1.0234, 48.30 % outside ±10 %) and nobody wired the consequence; and
`data/mt5_research_exports` (**18.88 GB, 23.5 M M15 rows, 166 symbols, from 2014**) is called
"absent from this machine" in §4 of this file and is present.

Before any new analysis, script, ledger or measurement: `rg` the concept **and its synonyms**
across `scripts/`, `src/`, `research/operations/`, `docs/audits/**/receipts/` and the `.hermes/`
trees; check `phase*/receipts/`, because this project's habit is to measure a thing, write a
receipt and never wire the consequence; and remember the repo uses **sparse checkout**, so a
`FileNotFoundError` usually means "not materialised", not "does not exist" (`shadow_logs/` showed
5 files on disk against 138 tracked). State what you reused and what you rebuilt, with the reason.
`…/swarm2/forensics/G1_UNUSED_INFRASTRUCTURE_INVENTORY_V1.md` is the standing index — add to it
rather than starting a new list. **Put this instruction in every subagent brief.**

**Name the price basis, and let an identity pick it.** Every drift/gross/net figure states its
basis (raw archive mid vs traded quotes) in the same breath as the number. That alone is not
enough — two agents got the same barrier figure wrong by 1.576 bp *and in sign* with both sides
already in bp and both labelled. So: **where a subset of the data makes two quantities equal by
construction, reconcile there first and let that identity choose the basis.** Worked example:
TIME_STOP trades exit *at* the 120-minute horizon, so "barriered" and "held to horizon" are the
same trade — they reconcile to 6e-07 on the traded basis and are off by 1.9786 bp on raw mid,
which settles the question in one command.

**Units come first, because getting them wrong has repeatedly misdirected this project (owner
instruction, 2026-08-12). Do not express everything in R.** R = quantity ÷ stop distance, and the
stop is *our own choice*, varying ~15× across the book (median 3.0 bp to 44.5 bp by quintile, F1
corpus, n=146,736). That denominator means two different things:

- **R is FAITHFUL for money.** Sizing is fixed-fractional (`execution.py:3445`,
  `risk_amount = account_balance * (risk_pct / 100)`), so 1 R is a constant dollar figure and
  `cost_r × $2,000 = cost_dollars` exactly at 2 % on $100k. Tight stops genuinely cost more
  dollars — you buy more lots to risk the same amount and commission/spread/swap are per-lot.
  That is a real economic effect, not an artifact.
- **R is TREACHEROUS for market movement.** A "+1 R move" is 3 pips on one trade and 219 index
  points on another. [MEASURED] the pool's edge reads **+0.0945 R on the tightest stop quintile
  and +0.0062 R on the widest — 15× — while in price it is flat at ~0.3 bp across all five.**
  The spread was our stop choice, not the market. Two independent confirmations: F2 measured
  ρ(predicted MFE, stop width) = **−0.787**, i.e. an R-denominated label taught the model our
  geometry instead of the market, which is why replacing the label achieved nothing; and the
  swap term appears to scale backwards with hold time partly for the same reason.
- **Never place a cost-in-R beside an edge-in-R.** "Cost 1.2 R against 0.04 R of profit" sets a
  faithful money ratio next to a movement ratio with a different denominator. They are not the
  same kind of number and must not be subtracted.

**How to report:** costs in **dollars** (plus pips/points where the mechanism is a price distance,
and lots where it is per-lot; state which components are deducted and which are already inside the
fill price) · movement, edge, drift, MFE/MAE in **pips / points / bp of price** · size in **lots** ·
R only for "how much of the risk taken did we get back", never across populations with different
stop distributions without naming both denominators.

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

**BOTH accounts are ARMED and trading real money — FTMO since 2026-07-29 12:55 UTC, redacted_account
since 2026-07-30 ~05:18 UTC — see the BOTH ACCOUNTS ARE ARMED bullet in §4 before you act on
anything below.** The rest of this section was written while both were gated and is retained
because it is still correct for the research surface; nothing in it is a reason to touch a live
book.

The system was **gated, not hard-halted** — corrected 2026-07-27 at wave-3 integration; this sentence
said "hard-halted as broker/runtime evidence," which is the exact claim §4 establishes is false (no
`*.flag` file exists on the VPS; the brake is three false config booleans plus the activation-token
layer). The gate is a restriction on *broker authority*, never on implementation. Do not use old
launcher snippets, live companion repair notes, process health, or first-fill framing as a reason to
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
