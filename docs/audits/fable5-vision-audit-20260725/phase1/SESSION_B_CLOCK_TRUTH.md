# GTOS Phase 1, Session B — clock truth: the research layer labels broker time as UTC

You are an implementation session for GTOS. Phase 0 is complete and Gate G0 is met. Work on branch
`phase1/clock-truth` in **`/Users/borr/GTOSActive/worktrees/phase1-clock-truth-20260726`** — your own worktree, already
created and sparse-configured. Push with `GIT_LFS_SKIP_PUSH=1 git push -u origin phase1/clock-truth`.

**Do not work in `worktrees/claude-opus5-architecture-audit-20260725` and do not commit to `main`.**
Two sibling sessions are running concurrently in their own worktrees; sharing one would collide on the
git index and on the `shadow_logs/` and `pipeline_state/` trees the suite writes into. Merge to `main`
per `.context/00_core/parallel_goal_merge_playbook.md` when your gate is met.

Two other sessions may be running in parallel on the shadow reducer and the red suite. Your work
touches neither, but **you are the one they are both downstream of** — see §5.

---

## 1. Read order

1. `CLAUDE.md` — root briefing, hazards H1–H7. **H1 was rewritten**: the contract of record is now
   **R2**, 43 bound paths, and the drift check in §3 is the current one.
2. `docs/audits/fable5-vision-audit-20260725/IMPLEMENTATION_STATE.md` — B1–B25 supersede numbers both
   audits carry.
3. `docs/audits/fable5-vision-audit-20260725/SECOND_AUDIT.md` **F7** — your finding, in full. Also
   §3.4 (data layer) for the coverage and eviction context.
4. `docs/audits/fable5-vision-audit-20260725/FULL_VISION_PLAN.md` — Phase 1 item 5, and Phase 5 item 3
   for what depends on you.
5. `docs/STORAGE_AND_REMOTES.md` — before any decision about re-exporting or archiving data.
6. Preflight per `CLAUDE.md` §2.

---

## 2. The defect

**The single largest new defect either audit found.** [MEASURED + VERIFIED]

The MT5 export path converts broker-server epochs with
`datetime.fromtimestamp(ts, tz=timezone.utc)` — `scripts/export_mt5_research_ohlcv.py:541` — with no
server-offset correction anywhere. FTMO server time is EET/EEST: **UTC+2 winter, UTC+3 summer**.

Proof from the data itself, not from reading code: bars end Friday **23:45 "UTC"** and resume Monday
00:00 (`historical_2026/EURUSD_M15.csv`); ticks end Friday 23:54:59. True-UTC FX weeks end ~22:00Z.
Every "UTC" timestamp in the research bar and tick exports is broker time, 2–3 hours ahead of real UTC.

The **live** path corrects this and has since 2026-04-28 — `mt5_real.py:212-244`, `_broker_epoch_to_utc`,
with self-detected offset. The **replay** path parses the mislabelled stamps as UTC
(`wave4r_replay_microstructure.py:130-142`). Session and kill-zone windows are shared wall-clock
tables (`broader_origin_generators.py:66-110`, e.g. london 07:00–13:00; `data_ingestion.py:606-608`).

**So the same config gates real-world market hours 2–3 hours earlier in replay than in live.** "Asia
range", London open, day boundaries, and every session-conditioned rule shift.

Exactly one file in the repo documents the truth — `scripts/session_volatility_monitor.py`
("CRITICAL: MT5 M15 data is EET…", with a converter) — and the replay stack does not use it.

**What survives and what does not.** Arm-vs-arm contrasts inside the sealed campaign are unaffected —
all four arms share the same shift. **Live-transfer claims, session-level attribution,
session-conditioned learning features, and the three hindsight session-level rejects (R14) are all
built on a mislabelled clock.**

---

## 3. What to build

Per the plan: **make true-UTC the only time base.**

1. **The export path gains broker-offset correction with per-file offset provenance.** The logic is
   already written and live-proven — port `_broker_epoch_to_utc`'s approach rather than inventing one.
   Every exported file should carry, in its own metadata, which offset was applied and how it was
   determined. An export whose offset is undeclared is the same defect wearing a correction.
2. **Existing research data gets either a re-export or a declared-offset view layer.** The offset is
   deterministic — it is the EET/EEST calendar — so a view layer is legitimate and much cheaper than
   re-exporting terabytes. Your call; state the reasoning. See the eviction constraint in §4.
3. **Replay session tables then gate the same real-world hours as live.** This is the point of the
   whole exercise: same config, same hours, both sides.
4. **A regression test that fails if any ingest path ever emits a Friday bar after 22:05Z again.** The
   defect is invisible to every existing test, which is why it survived this long.
5. **A one-page impact note on the sealed evidence**: arm-vs-arm contrasts unaffected; session-level
   attributions carry a caveat. State it precisely enough that someone reading a sealed receipt next
   year knows what to trust.

**Two DST seams to handle explicitly, not discover later:** the EU transition **2026-03-29 falls inside
the sealed March challenge window**, adding a one-hour semantic seam mid-window; and 2025-10-25 sits
inside the tick window.

**One corollary worth building for:** forward logs (slippage, pending-lifecycle) are true UTC
(post-2026-04-28) while replay data is broker time, so a naive timestamp join between them misaligns
by **8–12 M15 bars**. Phase 6's cost calibration depends on that join being exact.

---

## 4. Constraints you must know before you plan

**The contract binding is the thing that decides your design.** Run the `CLAUDE.md` §3 check first.
As of 2026-07-26, against R2:

- `scripts/export_mt5_research_ohlcv.py` — **free**
- `src/research_infra/wave4r_replay_microstructure.py` — **free**
- `src/components/broader_origin_generators.py` — **free**
- `src/components/data_ingestion.py` — **free**
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py` — **BOUND, and bound twice**
  (also in `code_authority_paths`, `attempt5:1405-1431`)
- `config/agent_config.yaml` — **BOUND**

So the export path, the replay microstructure parser, the session tables and live ingestion are all
free to edit. **If your fix needs to change time handling inside `v4_timewarp…` or a session constant
in `agent_config.yaml`, it costs a new contract generation** — and because that file is *doubly* bound
the OD-2 split cannot free it. Do not discover this at the end. If you land in that position, batch
the bound edits and generate an R3 the way
`build_b7_5_post_acceleration_contract_r2_verification_split.py` generates R2 — read that builder, it
is short and documents the three fields that must stay byte-identical (`schema`, `status`,
`predecessor_contract_binding`) because `attempt5:929-990` pins them to hardcoded constants.

**Data availability (F20).** The canonical export archive lives on **iCloud Drive and is mostly
evicted** to dataless placeholders, including **53 of the 96 files bound by the current April bundle**.
Sealed months are insulated — bundles carry their own byte copies — but *re-exporting* depends on
re-materialisation. The owner has given standing approval to re-materialise from iCloud without asking.
Per `STORAGE_AND_REMOTES.md`, no live or replay code path may read an iCloud path; copy to local disk
first.

**Ordered tick truth covers 4 of 24 symbols × 7 months.** Do not design a repair that assumes tick
coverage the data does not have.

---

## 4b. New since this prompt was written: you now have ground truth

A read-only export off the operator's server landed 2026-07-26 and is on local disk at
`/Users/borr/GTOSActive/vps-export-20260725/extracted/` (manifest-verified, 29,784/29,784 rows).
Findings in `docs/audits/fable5-vision-audit-20260725/VPS_EXPORT_FINDINGS.md`. Two parts of it bear
directly on you, and they turn your hardest open question from a reasoning problem into a measurement:

- **`09_mt5_api/{ftmo,redacted_account}_history_deals_get.jsonl`** — 631 real broker deals spanning
  2026-04-26 → 07-03, pulled through the **live** path, which applies `_broker_epoch_to_utc`. Set
  against the research exports' broker-time stamps for the same window, this is a direct empirical
  read on the offset rather than an inference from the EET/EEST calendar.
- **`08_mt5_terminal/{FTMO,redacted_account}/logs/` and `MQL5/Logs/`** — 89 terminal log files. The terminal
  timestamps its own entries in **server time**, so these independently pin what the broker clock
  actually was on given dates, including across the DST seams.

**Use this to settle §7's falsification early.** If the offset turns out not to be deterministic from
the calendar — a broker changing server time mid-history, or the two brokers disagreeing — the view
layer dies and re-export becomes mandatory. You can now test that instead of assuming it.

One caution: the export's `25_data/` bar CSVs came off the same export path this session is repairing,
so they carry the defect. They are useful as *evidence of* the mislabelling, not as a corrected source.

---

## 5. Why this session is load-bearing

The plan says **"do this before any learning-lane training run"** — session features trained on a
mislabelled clock transfer wrong into live, and the learning lane is the charter's stated destination.
Phase 4 waits on you. So does Phase 6's forward-vs-replay join.

That is also the argument for not gold-plating it: the repair needs to be correct and *landed*, not
comprehensive. A view layer that is right beats a re-export that is still running.

---

## Method — use the orchestration

The owner has explicitly authorised multi-agent workflows. Use them. This programme's two live-risk
defects were found by a 28-agent adversarial pass, not by careful reading, and its worst wrong answers
came from one mind checking its own work.

Where a workflow earns its place here:

- **The five independent traces.** Export path, replay parse, session/kill-zone tables, live correction
  path, and the DST seams are five separate reads of the same defect. Fan them out; each returns where
  the clock is assumed versus corrected, with `file:line`.
- **The falsification probe.** Whether the offset is deterministic from the EET/EEST calendar decides
  your whole design. Test it against the 631 real broker deals and the terminal logs **in parallel with
  the tracing**, not after — the answer changes what you build.
- **Impact assessment across the sealed evidence.** Which conclusions survive a 2–3 h shift and which do
  not is a per-artifact question across many artifacts. Fan out.

Before you claim your gate is met, run agents briefed to **refute with `file:line`**. Every review pass
in this programme has overturned something the session was confident about.

## Anti-drift — this task has a characteristic way of going wrong

**Sliding into a full re-export.** It is the expensive branch and it is only correct if the offset
turns out to be non-deterministic. Settle that first, with evidence.

**Repairing timestamps in sealed evidence.** Arm-vs-arm contrasts are unaffected — all arms share the
shift. Rewriting sealed artifacts to "fix" them destroys comparability and breaks contract bindings.
The deliverable is a correct *going-forward* path plus an honest impact note.

**Chasing every session-conditioned conclusion in the tree.** Name the class and give the rule for
re-checking one. Do not audit them all; that is not this session.

## 6. Working rules

- **A/B every change** with `scripts/pytest_failset.py capture` + `diff` against
  `receipts/baseline_full_suite.json` (650 failed / 9,747 passed / 33 errors at `212ad7e6d`). Compare
  failure **sets**, never counts.
- **Run the whole suite for the A/B**, not a scoped subset. Phase 0 had three regressions that passed
  in isolation and only appeared in a full run.
- Always `--continue-on-collection-errors`; without it the suite executes **zero** tests and still
  exits like a completed run.
- **Never execute broker-capable scripts.** C1: `create_mt5("live")` succeeds on macOS; the
  ImportError only surfaces on `.connect()`.
- **H1 before editing anything under `src/`.**
- Prefer behavioural tests over source-string assertions. A test that greps for a substring passes
  against a wrong implementation — and this defect is exactly the kind a string test would miss.
- Before declaring the gate passed, run an adversarial subagent briefed to **refute with `file:line`**.
- Report faithfully.

**Traps already paid for here:** `zsh` eats `git show $V:path` (use `git cat-file -p "${V}:path"`);
`rg -r` is `--replace`; do not delete modules from `sys.modules` and re-import (it creates a second
module object and breaks `multiprocessing` pickling in unrelated tests);
`test_end_to_end_integration.py::…::test_high_load_integration` is non-deterministic.

**Scope discipline.** ~330 research-bookkeeping and ~56 artifact-existence failures are stale and in
the deletion tier — Session C owns them. Do not repair them because they look time-related.

---

## 7. Deliverables

The corrected export path with offset provenance; the view layer or re-export, with the reasoning
stated; the replay/live session-gating parity; the Friday-22:05Z regression test; the one-page impact
note on sealed evidence; an `IMPLEMENTATION_STATE.md` update with evidence tags and a declared-gaps
section.

**Falsification to watch for:** if the offset turns out **not** to be deterministic from the EET/EEST
calendar — a broker changing server time mid-history, or two brokers disagreeing — the view-layer
approach dies and re-export becomes mandatory. Check that early; it changes the whole design.
