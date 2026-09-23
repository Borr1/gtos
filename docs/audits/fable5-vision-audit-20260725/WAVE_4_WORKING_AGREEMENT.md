# Wave 4 — working agreement

Read this before your session prompt. It is short, and it is written from **what actually went wrong
in wave 3**, most of it caused by the orchestrator's own prompts rather than by the sessions.

---

## 1. Your authority

You have full control of repo changes on this laptop: production code, config, risk, execution,
safety, selector, scheduler, runtime, launchers, profiles, tests, verifiers, research artifacts.
Implement, verify, commit.

**Two things are not yours.** Strategic trading decisions — the risk dial, allocation profile, sleeve
composition, any change to the sealed economic contract — are Borhen's. And **nothing you do touches
the VPS.** A live funded FTMO account is being armed ~~on three sleeves~~ as you work; the VPS is
driven separately by the orchestrator through an owner-executed ceremony.

> **Corrected 2026-07-29 at wave-4 integration (B359). The approved book is FOUR sleeves** —
> `metals_core, crypto, energy_agri, sub_xvol_pullback`, FTMO's survivors in `SURVIVOR_BOOK_V1.json`.
> This line is the *fourth* place wave 4 says "three", and the three sets meant are not the same:
> R's is the cross-account intersection, T's is the config-runnable subset, and this one names no
> sleeves at all. **Read the set, never the count.** Corrected here because this document is the one
> every wave-4 session treats as authority.
the VPS.** A live funded FTMO account is being armed on three sleeves as you work; the VPS is driven
separately by the orchestrator through an owner-executed ceremony.

**Never run a broker-capable script**: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`,
`mt5_preflight.py`, `dual_broker_execution_follower.py`, `start_all.bat`, `.tools/monitor_books.py`,
`flatten_all_positions.py`, `emergency_close_and_stop_redacted_account.py`. `create_mt5("live")` *succeeds*
on macOS — the ImportError only surfaces on `.connect()` — so construction is **not** a safety
boundary.

## 2. Authority order, stated explicitly

This bit an entire class of work in wave 3. When two documents disagree, this is the order:

1. **Your session prompt** — most specific, most recent, wins.
2. This agreement.
3. `THIRD_REVIEW.md` §4 (the approved plan) and the root `CLAUDE.md`.
4. Everything else in `.context/` and `docs/` — **historical unless a current artifact labels it
   active.**

If your prompt and a repo document conflict, follow the prompt and **say so in your report**. Two VPS
worker runs in wave 3 were captured by a stale root briefing and spent their whole turn on its
preflight instead of the job. That was the orchestrator's fault for not stating this order.

## 3. What the orchestrator got wrong last wave — so you can catch it faster

These are evidenced, not impressions. Assume the same failure modes are present in *your* prompt.

| # | what happened | what it means for you |
|---|---|---|
| 1 | **Block ranges were too tight.** K got 10 blocks, overflowed into L's range, and the *fix* caused a second collision with N. O cleaned up both. | Your range is **30 blocks**, and §4 lists every allocation. Check the table before numbering. |
| 2 | **Inherited claims were stated as facts, and sessions believed them.** The prompts asserted `metals_core` ran a "2-of-6 symbol universe" — K measured 6-of-6, still zero fires. Session N's prompt listed six "known answers"; N refuted three. | Anything the orchestrator hands you is a **claim to test**, not a fact to build on. Where a prompt states a number, it also owes you its source — if it doesn't, distrust it. |
| 3 | **The environment traps weren't in the prompts until they bit.** Sparse-checkout hid J's cost layer from N's worktree with `git status` clean. | §5 below. Read it before you conclude a file doesn't exist. |
| 4 | **An instrument defect wasn't propagated.** L and M *independently* discovered that `pytest_failset.py` wrote a green baseline for a SIGTERM-killed run. Two sessions, same discovery, duplicated effort. | If you find a defect in a shared instrument, **say so in your first commit message**, not in your final report. |
| 5 | **"Done" was under-specified**, so sessions varied on whether to merge or push. | §6. |
| 6 | **The orchestrator asserted where it should have measured.** The OD-3 dossier claimed four sleeves survive "on both accounts". Session Q measured it: they don't — only three are common, and the difference turns on per-account swap. | If a claim is cheaply measurable, **measure it** rather than inheriting it. Q's whole value came from checking the commission instead of executing it. |

## 4. Block allocation — the full table

Consult this before numbering anything. Wave 3: I `B100–109`, J `B110–119`, K `B120–129` **+ B165–172**,
L `B130–139`, M `B140–149`, N `B150–164` **+ B173–177**, O `B180–188`, P `B200–221`, Q **`B230–249`,
of which B230–B244 are used** — merged at wave-4 integration as `30bf067fb`.

> Two corrections here, 2026-07-29 (B367). ~~"(on `phase3/mc-true-target`, not yet merged)"~~ — it
> merged. And Q's range was tabled two ways: `B230–B244` here and in `CLAUDE.md`, but `B230–B249`
> in `WAVE_3_WORKING_AGREEMENT.md:206` (Q's own edit) and in Q's session doc. A session reading this
> file would have concluded *(245–249)* were free while the wave-3 table said Q owns them — failure
> mode #1 in §3, exactly. Resolved to the wider form, which is what Q allocated.

**Wave 4: R `B260–289` · S `B290–319` · T `B320–349` · U `B350–379` · V `B380–409`.** 30 each,
deliberately generous. If you need more, take the next free 10 **above 410** and record it.

> **U and V were added to this table 2026-07-29 at wave-4 integration (Session U, B352).** They were
> allocated in the session prompts and nowhere else, and `tests/test_implementation_state_block_citations.py`
> requires an in-flight range to be declared in *this* file — an exemption traceable only to a
> prompt is not traceable. The gap `B410+` is deliberate slack, not an allocation. Struck: *"take
> the next free 10 above 350"*, which was true when only R/S/T existed and would now collide with U.
L `B130–139`, M `B140–149`, N `B150–164` **+ B173–177**, O `B180–188`, P `B200–221`, Q `B230–244`
(on `phase3/mc-true-target`, not yet merged).

**Wave 4: R `B260–289` · S `B290–319` · T `B320–349`.** 30 each, deliberately generous. If you need
more, take the next free 10 **above 350** and record it.

## 5. Environment traps — all four bit someone in wave 3

- **Sparse-checkout lies to you.** Most of `research/operations/` is excluded. A file can be committed
  on your branch, absent from your working tree, and **`git status` still clean** — the index carries
  the skip-worktree `S` bit. `git ls-files -v <path>` shows it;
  `git sparse-checkout add /research/operations/<dir>/` hydrates it.
- **LFS pointers read as corruption, and as H1 drift.** 4,151 files are LFS-tracked and **their
  content is not on this machine**. A 131-byte pointer parses as `Expecting value: line 1 column 1`.
  Two contract-bound paths are LFS-tracked, so an un-hydrated pointer reports as **drift when nothing
  drifted** — `git lfs checkout <path>` first, then read the count. This also means a large share of
  the ~650 standing test failures is **data absence, not broken code**.
- **Memory is the binding constraint, not CPU.** Five concurrent full suites in wave 3 left 108 MB
  free of 16 GB and *silently killed captures* — which is the defect in the next bullet. Stagger
  full-suite runs; check free memory first.
- **The A/B tool now refuses bad captures, but check anyway.** L and M both hardened
  `scripts/pytest_failset.py` after it wrote `totals: {}` / `failed: []` for a SIGTERMed run and
  `diff` reported *"694 fixed, 0 REGRESSED, No regressions."* Both guards are on `main` now. Still
  read `pytest_returncode` and `totals` by hand before trusting a capture.

## 6. What "done" means

1. **Committed on your branch.** Do not merge to `main` — integration is a separate session.
2. **A/B by failure set, full-suite, committed, with captures embedded** —
   `python3 scripts/pytest_failset.py receipt <before> <after> -o <receipt.md>`. Counts are **not**
   portable between worktrees; only sets are. A receipt pointing at a scratchpad path is as
   unverifiable as no receipt: `tests/scripts/test_ab_receipts_are_self_contained.py` enforces this
   and it will go red on you if you skip it.
3. **A scoped A/B is acceptable when justified** — Session P scoped to one directory and said so
   honestly — but a scoped A/B leaves the branch **uncertified for merge**, and someone else pays
   that cost later. Prefer full-suite; if you scope, say what it does not cover.
4. **H1: check decision-contract membership before editing under `src/`** (`CLAUDE.md` §3). The R2
   contract binds 43 paths; a bound-file edit costs a re-seal plus ~16.5 machine-hours per window.
   `config/agent_config.yaml` **is** bound. `src/components/ultimate_book/admission.py` is **not**.
5. **Blocks appended to `IMPLEMENTATION_STATE.md`** in your range, each tagged `[MEASURED]`,
   `[VERIFIED]` or `[UNVERIFIED]`.

## 7. Method — what actually worked last wave

Spend the agent-hours. They are not the scarce resource; this machine's replay hours and the VPS
ceremonies are.

**Adversarial verification earned its cost every single time it was run.** Every wave-3 session that
commissioned refuters had real errors found:

- P built the exact false-evidence defect it was sent to prevent — publishing **71,969 still-open
  positions as completed holds**, a 2.49× overstatement of the one number OD-3 turns on — and its own
  refuter caught it.
- K's refuter refuted or partly refuted **all five** of its G4 claims, and ran the measurement the
  receipts should have opened with.
- N's refuter took back three findings, including one where N had claimed a result held "under either
  reading" of a timebase without measuring which reading was true.
- Q found the defect it was sent for was real but that **correcting only it would have reported a
  five-point deterioration that does not exist**, because two *other* rules were wrong in the
  opposite direction.

So: **commission refuters, tell them to default to "refuted", and give them distinct lenses** rather
than N identical ones. Then publish what they overturned — every wave-3 session recorded its
withdrawals rather than quietly amending, and that is why the evidence is trustworthy.

**When a quantity is directly measurable, measure it.** K's lesson, stated in B171 after three
confident wrong answers about `energy_agri`: *"do not transfer a rate and defend the transfer."*

**A clean negative beats a rescued pass.** K1 is not passed and saying so plainly was worth more than
a number that looked better. If your honest end state is "this does not work", that is a result.

## 8. Reporting

State what you measured, what you refuted, and **what you got wrong and withdrew**. Cite `file:line`
for production-state claims. Do not fabricate a number; if something is unmeasured, say `[UNVERIFIED]`
and say what would measure it.

Finish the whole task. If part is genuinely blocked, complete everything else and say precisely what
you left and why — the way Session P held three coupled files rather than land two and break the
third.
