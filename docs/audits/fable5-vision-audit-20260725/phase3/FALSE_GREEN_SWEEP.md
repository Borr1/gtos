# Where false green accumulates in GTOS — the Session M sweep

**Session M (wave 3, Stage 1 item 1.5), 2026-07-27.** Worktree `wave3-hygiene-20260727`, baseline HEAD
`8ed443982`. Read-only measurement; every fix landed in this session is recorded separately in blocks
**B140–B149** of `IMPLEMENTATION_STATE.md`.

`SESSION_M_HYGIENE.md` set the real deliverable above its own backlog:

> **So the real deliverable is not ten fixes. It is: how much of what this repo asserts about itself is
> actually checked?** … If the sweep tells you something general about where false green accumulates
> here, that finding outranks every item on the list.

This is that answer. It is a measurement, not an impression: six independent probes, each with its own
denominator, each positively controlled against a known instance before its negative results were
believed.

---

## 1. The headline finding

False green does not accumulate uniformly here. It concentrates in three places, and all three share one
mechanism: **the asserted quantity cannot vary.**

1. **Evidence-shaped tests.** **42.6 %** of the test files filed under the live decision surface
   (`tests/ultimate_book/`, 29 of 68) execute **zero lines** of the subsystem they are filed under
   [MEASURED, dynamic `sys.monitoring` tracing]. They read frozen research JSON and assert it equals
   frozen constants. They cannot fail when the code changes — only when the document does — while
   counting as coverage of the book that trades.

2. **A refusal vocabulary nobody asserts.** **47 %** (41 of 87) of the distinct machine-readable refusal
   codes the live decision surface can emit are named by **no test anywhere**. That includes all three
   `runtime_halt_*` codes and the broad-selector mutual-exclusion guard. If two refusal codes were
   swapped, nothing would notice, and the operator's post-incident log vocabulary is unverified.

3. **An architecture that cannot fail loudly.** The live book carries **32** comments promising "NEVER
   raises" and delivers them with **190** `except` handlers that return `None` or `pass` **with no log at
   all**. For every one of those guards, "checked, all clear" and "the check itself broke" are the same
   return value, forever, silently.

**The third is the root, and it is why F38 and the phantom halt flags are the same defect as the B41
vacuous tests.** A system whose safety checks degrade to a silent `None`, whose refusal codes are
unasserted, and which `CLAUDE.md` §4 already records as having **no monitoring watching the gate**, is not
reporting safety it does not have by accident. It is *structurally unable to report the difference*.

**The single highest-value change is therefore not a test. It is making "unassessable" distinguishable
from "clear."** See M4 in §5.

---

## 2. The quantification

Six probes. Denominator and method stated for each, because a rate without them is the thing this
document is about.

| # | probe | denominator | finding | rate |
|---|---|---|---|---|
| 1a | test-shape census (AST) | 9,936 test fns / 595 files | no assertion at all: 34 · every assertion negative: 782 · every assertion inside `if`/`for`: 180 · body is `pass`/`assert True`: **0** · unconditional skip/xfail: **0** | 0.34 % / 7.9 % / 1.8 % |
| 1b | positive-control balance | 26,564 distinct (file, asserted-quantity) pairs | quantity asserted **absent**, with nothing in the same file ever asserting it **present** | **4,371 = 16.45 %** |
| 1c | red positive control | 1,235 pairs asserted both ways | every positive control RED ⇒ its green negative siblings are vacuous | **9 pairs / 9 tests** |
| 2 | source-text assertions | 10,481 test fns | assert on source **code** text (`CLAUDE.md` §6 bans these by name): 18 tests / 44 sites; on config text: 1 | 0.17 % |
| 3 | refusal-code discrimination | 87 distinct live-surface codes | named by **no** test anywhere | **41 = 47 %** |
| 5 | production-line execution (**dynamic**) | 68 files / 572 tests in `tests/ultimate_book/` | files executing **zero** lines of `src/components/ultimate_book/` | **29 = 42.6 %** |

Probe 5 also yields the only ground-truth coverage number the live book has ever had: its whole test
directory covers **79.6 %** of it (5,731 of 7,199 statement lines), and **123 of 572** individual tests
(21.5 %) touch none of it.

**What each method would have missed — stated, because a rate without its blind spot is another false
green.**

- **Probe 1a read files as UTF-8 and silently skipped 9 BOM-carrying files.** Found only by cross-check,
  fixed with `utf-8-sig` (hence 9,936 vs 10,481). **The verifier sweep independently hit the same trap and
  lost 14 functions to it.** Any static tool in this repo that does not read `utf-8-sig` silently drops
  ~12 files. That is a live blind spot in the repo's own tooling and it has now bitten twice in one day.
- **Probe 1b** keys on a normalised expression string, so it cannot match the same quantity written two
  ways, and it is per-file, so cross-file positive controls read as missing.
- **Probe 3** measures *discrimination*, **not** behaviour coverage. The activation-token tests are
  genuinely strong and behavioural (40+ tests, 8 reason strings asserted). 47 % means a swapped code
  would go unnoticed, not that the behaviour is untested.
- **Probe 5** excludes import-time execution and ran against a working tree five agents were editing, so
  it is used for aggregates only; individual claims rest on line-number-independent textual evidence.

**Static proxy, validated against dynamic truth:** "imports no first-party module" predicts "executes zero
subsystem lines" at **precision 100 %, recall 93 %** (27 TP, 0 FP, 2 FN). Applied repo-wide it yields
42 files / 123 tests — therefore an **undercount**.

---

## 3. Instances not already on the backlog, ranked by consequence

Live-surface first. Everything is cited at baseline HEAD `8ed443982`.

| # | site | asserted | actually checked | live? |
|---|---|---|---|---|
| **1** | `src/components/ultimate_book/book_engine.py:690`, caller `book_owner.py:2347` | docstring: last-resort flatten of **open** positions at −4 % daily / 9 % maxDD. `ultimate_book_flatten_on_breach: true` (`agent_config.yaml:1353`) — **armed live** | whole body is `try: … except Exception: return None` **with no log**; the caller wraps it in a *second* silent `except`. A persistent fault in `compute_governor_state` is indistinguishable from "no breach", permanently | **YES** |
| **2** | `src/components/execution.py:555`, `:3122`, `src/safety/runtime_halt.py:181` | the three `runtime_halt_*` codes, incl. `runtime_halt_fail_closed_unreadable_flag_path` | **zero** tests name any of the three. No test ever makes a flag path unreadable | **YES** |
| **3** | `admission.py:1675`, `:1704`, `:1748` — `assert_confidence_parity`, `assert_clean3_parity`, `assert_w7_final_parity`. `VPS_OPERATOR_BUNDLE.md:148` presents these to the operator as "Parity asserts" with `parity_ok=True` | the live book's sleeve weights match their source of record | **zero callers** anywhere in `src/`, `tests/`, `scripts/`, `run_book.py`. Named `assert_*`, return a `dict`, never raise. `assert_confidence_parity` imports `INTEG_portfolio_build_w2`, which does not exist beside the live module. The only executing copies are the **duplicates in the retired research package** — the D6 two-stacks split again | **YES** |
| **4** | `bridge.py:554-555`, `:581` | `fail_closed_broad_selector_still_live` (the guard preventing broad selector **and** book both live) and `blocked_by_governor` | named by no test; never executed by the live-surface test directory | **YES** |
| **5** | `scripts/mt5_preflight.py:136,142,152,155` + `tests/safety/test_raw_broker_script_guards.py` | that file's docstring: "the **three** broker-capable scripts that do not go through `RealMT5.order_send`" | it names and tests **two**. `mt5_preflight.py` — `CLAUDE.md` H6's *last ungated mutating script* — is mentioned by **zero** tests, and its four raw `mt5.order_send` calls sit at **module scope**, structurally invisible to that file's `ast.FunctionDef`-walking probe | **YES** |
| **6** | `src/safety/activation_token.py:187-200` | `ensure_signing_key` mints the HMAC key for the primary broker brake | `path.chmod(0o600)` inside `try: … except OSError: pass`, unlogged. A chmod failure silently leaves the token secret at default umask → forgeable exposure-increasing tokens | **YES** |
| **7** | 27 `*_artifacts.py` files (54 tests) + 2 others under `tests/ultimate_book/` | read as live-book coverage, by location | execute zero lines of it (probe 5). **Remedy is relocation, not deletion** — move to `tests/evidence/` | **YES** (by location) |
| **8** | `tests/conftest.py:64`, gate at `:112-113` | — | autouse `_auto_inject_deployment_phase` shims production Gate 0 whenever `config` lacks a `"deployment"` key: **96 of 112 tests (85.7 %)** that call `check_permissions` run with the first fail-closed gate **disabled**. An opt-in `real_deployment_gate` exists at `:354` and 16 tests use it. *To the repo's credit, the fixture's own docstring says so* | **YES** |
| **9** | `tests/safety/test_raw_broker_script_guards.py:71-91`, `:111-127` | "authorizes before it opens a position" / "checks the halt before opening a trade" | both **filter** call sites to those already guarded, then assert the filtered list is non-empty — **existential where the safety property is universal**. A newly-added unguarded opener would pass | **YES** |
| **10–11** | `tests/ultimate_book/test_book_engine.py` (subject `runtime_effect_now`) and `test_market_expansion_runtime_generator.py` (subject `dec.runtime_effect_now`) | — | two further instances of the exact B41/L1 mechanism, one in a file B41 examined and one in a file nobody had looked at | **YES** |
| 12 | `src/research_infra/v4_timewarp_simulated_live_research_loop.py:94757` | `audit_route_artifacts` verifies `REQUIRED_ARTIFACTS`, emits `status: passed\|failed`, writes a result JSON | return discarded at both call sites (bare `ast.Expr`); **no Python anywhere reads the file it writes**. The route completes identically either way. The purest instance of the class — and it sits in the 60.6 %-CPU file | no |
| 13 | `validation_integrity/sealed_holdout.py:52`, `selection_stability.py:153,212` | docstring: "RAISES if any selection/tuning touched a …" | only the `test_vig_*` tests call them; `gauntlet.py`, which would wire them in, imports none. **The validation-integrity guards are on no validation path — at the exact moment OD-3 asks for a re-costed W7 validation** | no |
| 14 | `b7_5_post_acceleration_runner.py:817-825` | — | nine consecutive lines hardcode `parity_gate_*=None` / `stop_after_parity_gate=False`, making 10 check-named functions across 4 **contract-bound** verifier modules unreachable on the sealed path. **This is H1's mechanism, localised to nine lines** | no |
| 15 | `replay_acceleration_attempt5_typed_sparse_runner.py:18171` | `require_attempt5_execution_authority` binds golden-manifest / amendment / fixed-verifier identity before a sealed route runs | bypassed — every production runner calls `_run_typed_sparse_attempt5` directly. **The sealed January/April evidence was produced on a path that never ran its own execution-authority binding** | no |

### Three more, found by this session's own fix work rather than by the sweep

- **`SLEEVE_REGISTRY` genuinely diverges between the live authority and its route ancestor**, and the
  parity test misses it. `admission.SLEEVE_REGISTRY["crypto"].symbols` is `("BTCUSD", "DASHUSD")`; the
  route module's is `("BTCUSD", "DASHUSD", "ETHUSD")`. `test_vendor_parity.py::test_admission_parity`
  reports parity because its four-intent fixture uses BTCUSD for crypto and never touches the symbol they
  disagree about — **parity asserted over a universe on which parity is not in question.** D6 said parity
  holds "on the shared numeric core"; that understates it. Now enumerated so a *new* divergence turns red.
- **`AGENTS.md` is a stale fork of the root briefing.** At baseline it had **zero** mentions of
  `THIRD_REVIEW.md`, still named the **parked** B7.5 campaign as "the Program", still said the brake is
  "one config line" where the truth is three, and still carried the struck H3 GiB/GB claim. An agent
  reading it would have begun work on a parked program under a refuted memory model. The ghost-reference
  class at full scale.
- **`B58` is cited 34 times across 17 files** and has never existed in any revision. The prompt scoped
  this to two files.

---

## 4. Positive controls — why the negative results are believable

- **Probe 1c**, run blind against the tree, **independently rediscovered B41/L1 exactly**: the same file,
  the same subject (`res['n_intents']`), the same red control, and the same two vacuous green siblings
  B41 named. It then found 7 more relationships B41 did not. Corroborated twice over by
  `.pytest_cache/v/cache/lastfailed` and by the concurrent fix agent's independent description of the
  identical mechanism.
- **Probe 1b was controlled against itself.** Its first, stricter form ("all assertions in the test are
  negative") **failed** to flag the two known-vacuous B41 tests, because each also carries unrelated
  positive assertions. That failure produced the correct per-file formulation. Shipping the first
  version's output would have been a clean instance of the sweep becoming its own finding.
- **Probe 2** first returned 426 tests; sampling showed it was propagating "read a JSON file" through any
  variable. Rebuilt with path-literal typing: 426 → 18, and the rebuilt probe still surfaces the known
  instances.
- **Probe 5** first reported "0 tests execute zero `src/` lines" — wrong, because every test executes ~17
  lines of the conftest's own notification machinery. Re-scoped to the subsystem under test.
- **Probe 3** first reported the activation-token codes as untested, which would have been a false alarm;
  direct reading found 8 codes asserted across `test_activation_token.py`. That forced the honest framing.
- **The verifier probe rediscovered 9 of H1's 9 never-executing verifiers, plus the audit's tenth — but
  only after two corrections, and the naive form finds ZERO of them.** Every one of the nine *has* call
  sites, several 9–31 of them. "No caller anywhere" is the wrong question; **reachability from the
  producing entrypoint** is the right one.

**B41/L2 is already repaired at this HEAD** — the probe confirms all three `TestGate3Integration` tests
now reach their intended assertions. Recorded so nobody re-fixes it.

---

## 5. Mechanisms

**Hard constraint, measured:** there is **no CI, no `.github/`, no git hooks, no pre-commit config, no
lint config**, and `coverage`/`pytest-cov` are not installed. The only enforcement surface that actually
runs is the pytest suite plus `scripts/pytest_failset.py`. Every mechanism must therefore ship **as a test
in `tests/`** — which is a feature, because it then fails inside the A/B the working agreement already
requires.

| id | mechanism | cost | expected FP rate |
|---|---|---|---|
| **M1** | **Red-control meta-test.** For each (file, quantity) pair asserted both ways: if every positive-asserting test is in the current failure set and ≥1 negative sibling is green, fail. **This is the only class that appears with no commit** — B41/L1 was created by the calendar. | ~120 lines, built and validated | **0 %** (9 findings from 1,235 pairs, all genuine) |
| **M2** | **Subsystem-execution meta-test.** `sys.monitoring` LINE events per test; a file under `tests/<subsystem>/` must execute ≥1 line of the corresponding `src/**/<subsystem>/`. | ~40-line plugin; **+4.6 s on an 18 s run (~25 %)** | 0–7 % |
| **M3** | **Refusal-code assertion ratchet.** Fail on an *increase* in codes emitted by production and named by no test. A wall would land 41 red at once; a ratchet defers the judgement call about which codes are worth asserting. | ~30 lines | ~0 % |
| **M4** | **The root fix, and it is not a lint.** Make the two `None`s different: each live-surface guard returns its *unassessable* state as a distinct sentinel rather than sharing the "all clear" return, and a test forces a fault and asserts the sentinel. **Start with item 1** — armed live, and the only open-position safety tier. | ~1 session | n/a |
| **M5** | **Scoped mutation testing.** `admission.py` + `book_engine.py` + `bridge.py` + `governor_state.py` + all of `src/safety/` = 2,529 statement lines; those tests run in ~18 s. ~500 mutants ≈ **2.5 machine-hours** — one-seventh of a replay arm, against the surface that actually trades. | 2.5 MH | n/a |

**Landed this session:** `tests/test_implementation_state_block_citations.py`, the ghost-reference
mechanism (§3's third bullet), which is M-shaped and sabotage-verified. **M1–M5 are specified, not built.**

**On M4 and F38.** M1–M3 catch instances; only M4 addresses the root. It is also **the only item here that
would have caught F38**, whose defect is a *missing term in a sum* — structurally invisible to any comment-
or name-based probe. For F38's class specifically the real mechanism is a reconciliation test asserting
modelled cost equals realized broker cost on sampled real fills. That data exists (the 31.6 % figure), so
it is feasible, but it is not cheap and it is not hygiene.

---

## 6. What was looked for and NOT found

Negative results, each with the control proving the probe could see the thing.

- **Test bodies that are `pass` or only `assert True`: zero.** Genuinely absent.
- **Unconditional `@pytest.mark.skip` / non-strict `xfail`: zero true instances.** The one flagged is a
  `strict=True` xfail with a named-bug reason — the correct pattern. All three textual
  `@pytest.mark.skip` matches are **comments** in the wave4 test files explaining why their authors chose
  a *conditional* skip instead, one of which says outright that an unconditional skip "would report 'not
  applicable' forever — the same false-green shape this guard exists to avoid." **The repo actively
  resists this failure mode.**
- **Always-true check functions on the live surface: zero.** The 15 candidates are accumulator-style
  validators that report by mutating a parameter. Control: the probe found 8 elsewhere.
- **Verdict-computed-then-discarded on the live surface: zero**, across all 78 files in `run_book.py`'s
  import closure. The bare-expression check calls there all **raise**, so a bare call is correct idiom.
  Control: the probe found 7 in research code, including item 12.
- **`if False:` or commented-out check dispatch in production: zero.** **`globals()`/`eval`/`exec`
  dispatch of a check: zero.** **Assertions swallowed by `try/except`: 3 repo-wide, none live-surface.**
- **`assert` statements in the live book: zero, and only 4 `raise` sites in 7,199 statement lines.** This
  is a structural finding rather than a null: **the live book refuses by returning a reason, never by
  raising** — which is exactly why exception coverage is the wrong instrument here and refusal-code
  coverage is the right one.

---

## 7. Coverage this sweep does NOT have

Stated plainly, because a sweep that hides its gaps is the thing it is measuring.

- **Two of the six planned modalities did not return**: comment-vs-code contradiction, and config-key
  deadness. They are only partially covered by items 3, 5 and 8 above and by the "NEVER raises" census.
  **No result is claimed for either.** They are the obvious next pass, and D1/D6/D7 — three defects in one
  register, all of that exact shape — suggest the yield would be high.
- Probe 5 ran against a mutating working tree.
- Nothing here measures the **research** surface systematically; items 12–15 are incidental catches.
- The 79.6 % live-book line coverage is a *union over the whole test directory*, which is the most
  favourable possible framing. Per-test it is far lower, and 42.6 % of the files contribute zero.
