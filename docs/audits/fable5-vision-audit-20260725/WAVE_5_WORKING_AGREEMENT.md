# Wave 5 — working agreement

Read this before your session prompt. It is short, and it is written from **what actually went wrong
in waves 3 and 4**, most of it caused by the orchestrator's own prompts rather than by the sessions.

---

## 1. Your authority

You have full control of repo changes on this laptop: production code, config, risk, execution,
safety, selector, scheduler, runtime, launchers, profiles, tests, verifiers, research artifacts.
Implement, verify, commit.

**Two things are not yours.** Strategic trading decisions — the risk dial, allocation profile, sleeve
composition, admission standards, any change to the sealed economic contract — are Borhen's. And
**nothing you do touches the VPS.** A live funded FTMO account is being armed on four sleeves; the VPS
is driven separately by the orchestrator through an owner-executed ceremony.

**Never run a broker-capable script**: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`,
`mt5_preflight.py`, `dual_broker_execution_follower.py`, `start_all.bat`, `.tools/monitor_books.py`,
`flatten_all_positions.py`, `emergency_close_and_stop_redacted_account.py`. `create_mt5("live")` *succeeds*
on macOS — the ImportError only surfaces on `.connect()` — so construction is **not** a safety
boundary.

## 2. Authority order, stated explicitly

1. **Your session prompt** — most specific, most recent, wins.
2. This agreement.
3. `WAVE_5_PLAN.md`, then `THIRD_REVIEW.md` §4 (the approved plan) and the root `CLAUDE.md`.
4. Everything else in `.context/` and `docs/` — **historical unless a current artifact labels it
   active.**

If your prompt and a repo document conflict, follow the prompt and **say so in your report.**

## 3. What the orchestrator got wrong — evidenced, and still recurring

Assume the same failure modes are present in *your* prompt.

| # | what happened | what it means for you |
|---|---|---|
| 1 | **Inherited claims stated as facts.** Wave 3: "`metals_core` runs a 2-of-6 universe" — K measured 6-of-6. N's prompt listed six "known answers"; N refuted three. Wave 4: T's prompt asserted "the book is three sleeves" and "a confidence floor exists" — **both false**; the config resolves 29 and no floor exists anywhere. | Anything the orchestrator hands you is a **claim to test**. Where a prompt states a number, it owes you its source — if it doesn't, distrust it. |
| 2 | **Reimplementing resolution the engine already does.** T recomputed the sleeve set and reported 20 instead of 29. The orchestrator then probed symbol availability with raw `mt5.symbol_info` on *canonical* names, bypassing `symbol_map.py` — and reported `energy_agri` at **0/2** and `sub_xvol_pullback` at **6/18**. Through the engine's own resolver both are **full surface**. The wrong numbers nearly killed two sleeves of a funded book. | **Call the production resolver.** If a module exists to cross a boundary, crossing it yourself is a bug, not a shortcut. |
| 3 | **Block ranges too tight** (wave 3): K overflowed into L; the fix collided with N. | Your range is **30 blocks**; §4 lists every allocation. Check before numbering. |
| 4 | **Shared-instrument defects not propagated.** L and M independently found the same `pytest_failset` false-green. S found `test_implementation_state_block_citations.py` matched heading-form blocks only, capping the ceiling at B200. | If you find a defect in a shared instrument, **say so in your first commit message**, not your final report. |
| 5 | **Environment traps absent until they bit.** | §5. Read it before concluding a file doesn't exist. |
| 6 | **The orchestrator asserting where it should have measured.** The OD-3 dossier claimed four sleeves survive "on both accounts" — Q measured only three are common. | If a claim is cheaply measurable, **measure it**. |

**R's example is the one to copy.** Its prompt instructed it to price realized outcomes through the
cost model. R refused, correctly — for *realized* fills the broker reports what it charged, and a
model of that is weaker evidence than the number. It used the model for reconciliation instead, and
published the disagreement. **Disagreeing with your prompt, in writing, with a reason, is the highest
form of compliance with it.**

## 4. Block allocation — the full table

Wave 3: I `B100–109`, J `B110–119`, K `B120–129` **+ B165–172**, L `B130–139`, M `B140–149`,
N `B150–164` **+ B173–177**, O `B180–188`, P `B200–221`, Q `B230–244`.
Wave 4: R `B260–289` · S `B290–319` · T `B320–349` · U `B350–379` · V `B380–409`.

**Wave 5: W `B420–449` · X `B450–479` · Y `B480–509` · Z `B510–539`.**
If you need more, take the next free 10 **above 550** and record it.

## 5. Environment traps — all bit someone

- **Sparse-checkout lies to you.** Most of `research/operations/` is excluded. A file can be committed
  on your branch, absent from your working tree, and **`git status` still clean** — the index carries
  the skip-worktree `S` bit. `git ls-files -v <path>` shows it;
  `git sparse-checkout add /research/operations/<dir>/` hydrates it.
- **LFS pointers read as corruption, and as H1 drift.** 4,151 files are LFS-tracked and their content
  is not all on this machine. A 131-byte pointer parses as `Expecting value: line 1 column 1`.
  `git lfs checkout <path>` first. A large share of the ~650 standing test failures is **data
  absence, not broken code.**
- **Memory is the binding constraint, not CPU.** Five concurrent full suites in wave 3 left 108 MB
  free of 16 GB and *silently killed captures*. Stagger full-suite runs; check free memory first.
- **Never wait on a machine-wide condition.** Session T left two shells polling
  `until [ -f $AB/after.json ] && [ $(pgrep -f pytest | wc -l) -eq 0 ]`. That is correct on a
  one-session machine and **unsatisfiable here** — four to six sessions run pytest continuously, so
  the loop slept for **5.5 hours** and never exited. Scope every wait to your own worktree, e.g.
  `pgrep -f "pytest.*<your-worktree-name>"`. The inverse also bit: Session S declared a `nohup`
  capture dead that was still running against its tree, and discarded three A/B attempts. **You
  cannot see the other sessions' processes as yours — check the path, not the process name.**
- **The A/B tool refuses bad captures now, but check anyway.** Read `pytest_returncode` and `totals`
  by hand. And before starting a capture, confirm **no other pytest is writing into your tree** —
  Session S discarded three attempts, one because a `nohup` run it had declared dead was still going.

## 6. What "done" means

1. **Committed on your branch.** Do not merge to `main` — integration is a separate session.
2. **A/B by failure set, full-suite, committed, with captures embedded** —
   `python3 scripts/pytest_failset.py receipt <before> <after> -o <receipt.md>`. Counts are **not**
   portable between worktrees; only sets are. A receipt pointing at a scratchpad path is unverifiable
   and `tests/scripts/test_ab_receipts_are_self_contained.py` enforces it.
3. **A scoped A/B is acceptable when justified**, but it leaves the branch **uncertified for merge**
   and someone else pays that later. Say what it does not cover.
4. **H1: check decision-contract membership before editing under `src/`** (`CLAUDE.md` §3). R2 binds
   43 paths; a bound-file edit costs a re-seal plus ~16.5 machine-hours per window.
   `config/agent_config.yaml` **is** bound. Most of `src/components/ultimate_book/` is **not** — check.
5. **Blocks appended to `IMPLEMENTATION_STATE.md`** in your range, tagged `[MEASURED]`, `[VERIFIED]`
   or `[UNVERIFIED]`.

## 7. Method — what has worked every single time

Spend the agent-hours. They are not the scarce resource; this machine's replay hours and the VPS
ceremonies are.

**Adversarial verification has earned its cost in every session that ran it.** P published 71,969
still-open positions as completed holds — a 2.49× overstatement of the one number OD-3 turns on — and
its own refuter caught it. K's refuter refuted or partly refuted **all five** G4 claims. N's took back
three findings. Q found the defect it was sent for was real but that correcting only it would have
reported a five-point deterioration that does not exist. T's caught its own book-composition numbers
being wrong in both directions *after* they had shipped as a CRITICAL alert. R's found ten defects,
two severe enough to invert its headline.

So: **commission refuters, tell them to default to "refuted", give them distinct lenses** rather than
N identical ones. Then publish what they overturned.

**When a quantity is directly measurable, measure it.** K's B171, after three confident wrong answers:
*"do not transfer a rate and defend the transfer."*

**A clean negative beats a rescued pass.** K1 is not passed, and saying so plainly was worth more than
a number that looked better.

## 8. Reporting

State what you measured, what you refuted, and **what you got wrong and withdrew**. Cite `file:line`
for production-state claims. Do not fabricate a number; if something is unmeasured, say `[UNVERIFIED]`
and say what would measure it.

Finish the whole task. If part is genuinely blocked, complete everything else and say precisely what
you left and why — the way Session P held three coupled files rather than land two and break the third.
