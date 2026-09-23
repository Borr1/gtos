# Gate G0 receipt — Phase 0, reconcile the fork and unblock

**Assessed 2026-07-26** by the Opus implementation session, over commits `4d2407c77..HEAD` on `main`.
Evidence tags per `OPUS_IMPLEMENTATION_PROMPT.md` §4: **[MEASURED]** (ran/observed here),
**[VERIFIED]** (read directly in code or sealed artifacts), **[INFERRED]**, **[HYP]**.

`FULL_VISION_PLAN.md` states G0 as: *"`run_book.py` imports and its tests pass at HEAD; book +
companion test suites green; A/B against parent commit shows only intended deltas; the H1 contract
check passes under the new split; an activation-token dry-run shows every mutating entrypoint fail
closed without a token."*

---

## 0. The one criterion that had to be restated first, and why

**"Book + companion test suites green" is not a meaningful criterion at this baseline, and saying so
is the honest move rather than a concession.** The whole suite is **650 failed / 9,747 passed /
33 errors** [MEASURED]. `tests/ultimate_book` alone carries **60** pre-existing failures. Both prior
audits' "11 failures" was an ~885-test subset (B1).

Design rule 7 of the plan is explicit: *"Gates are evidence definitions, never waiting periods: where
a gate names a quantity, sufficiency is the implementing session's judgment, stated with its rationale
in the gate receipt."* So the quantity is restated, with the rationale here.

**Restated criterion, scoped to the live surface (B16):**

> **Zero new failures against the recorded baseline manifest, compared as failure SETS and not counts,
> plus every behaviour this phase changed pinned by a test that fails against the pre-change code.**

Three reasons this is the stronger criterion, not the weaker one:

1. **"Green" would be satisfiable by deleting tests.** "Zero regressions by set, plus a failing-first
   test per behaviour change" cannot be.
2. **~330 of the failures are research-evidence bookkeeping and ~56 are artifact-existence assertions
   against a sparse-masked tree** (B16). They are in the deletion tier and must leave *with the code
   they test*, as a reviewed pair (F23) — repairing them would be work spent to make a number look
   better while the deletion manifest later throws it away.
3. **Counts lie.** Session 1 published a "refuted" verdict from a count comparison that a set
   comparison overturned (B10 → B11). Every claim below is a set comparison.

**What this criterion does NOT establish, stated plainly:** the genuine-defect count inside the 650 is
still unmeasured (C10 killed the "153 genuine" figure; B10/B11 killed the sparse-masking explanation
for the dominant 299). G0 does not close that, and does not pretend to.

---

## 1. Criterion-by-criterion

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | `run_book.py` imports at HEAD and its tests pass | **MET** | `tests/test_run_book_importable.py`, 8 tests, green. Imports in a child process rooted at an empty cwd so `load_dotenv(override=True)` cannot reach a real `.env` [MEASURED] |
| 2 | Live-surface suites: zero new failures by SET | **MET** | `tests/ultimate_book`: 60 bad → 60 bad, **0 regressed, 0 fixed**, 378 → 402 passing. Whole suite diffed in §3 [MEASURED] |
| 3 | A/B shows only intended deltas | **MET** | §3 [MEASURED] |
| 4 | H1 contract check passes under the new split | **MET** | §2 [MEASURED] |
| 5 | Activation-token dry-run: every mutating entrypoint fails closed without a token | **MET** | §4 [MEASURED] |

---

## 2. H1 under the new split [MEASURED]

The `CLAUDE.md` §3 snippet, run verbatim as documented, against **R2** (the contract of record for any
new window):

```
DRIFTED: …/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl
DRIFTED: …/SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl
unbound verification tooling (free to edit):
  src/research_infra/b7_5_post_acceleration_semantic_verifier.py
  src/research_infra/replay_acceleration_task2_semantic_acceptance.py
```

**Zero code drift.** The two JSONL rows are B2/B3's known state, not a Phase-0 side effect: the
contract resolver searches three roots (`attempt5:1046-1051`) and both resolve against
`/Users/borr/GTOSActive/repo`. Proven by running the real enforcement entrypoint,
`selection_sizing_factorial_binding_from_args`, rather than by re-reading the resolver — **all four R2
arms bind** [MEASURED].

R1 now reports **4** drifted (those two plus the two verifiers P1 fixed). That is the intended,
bounded cost of OD-2, and `test_r1_binds_again_the_moment_the_sealed_bytes_are_restored` measures that
R1 is superseded rather than broken by restoring the sealed bytes and re-binding [MEASURED].

---

## 3. Whole-suite A/B [MEASURED]

Baseline: `receipts/baseline_full_suite.json`, re-anchored post-merge. Compared with
`scripts/pytest_failset.py diff`, i.e. by **failure set**.

```
before 28ff23976 ('Vendor the protective AI companion and the book monitor'): 684 bad
after  212ad7e6d ('Stop my contract test from breaking three replay tests…'):  683 bad
unchanged: 683   fixed: 1   REGRESSED: 0
FIXED: + tests/test_end_to_end_integration.py::…::test_high_load_integration
No regressions.
```

The one "fixed" entry is the **known non-deterministic test**, not a repair — it is listed here
rather than claimed as a win.

**It took three captures to get there, and the two failed ones are the point.** The first reported
**9 regressions**, all mine, and the diff is what found them:

| Regressed | Cause | Resolution |
|---|---:|---|
| 6 × `tests/test_fn_smoke_trade.py` | gating the script changed its contract; its tests reached an order without authorizing | tests authorize; a new test pins the refusal path |
| 3 × replay sparse-tick suites | **my own R2 contract test** deleted the runner from `sys.modules` and re-imported it, creating a second module object that `multiprocessing` then refused to pickle a function from | import normally — the SHA cache it was defending against keys on `mtime_ns` and already misses |
| 1 × `tests/test_a1_analyze.py` | **my own fix to `pytest_failset.py`**: bracket-matching swallowed the message of a collection error containing brackets | bracket-match only when the bracket opens before the reason separator |

Two of those three are defects **in the verification machinery itself**, found only because the diff
was run over the whole suite rather than a scoped subset — the replay failures pass in isolation and
pass even alongside the file that looked like the contaminator.

**Baseline re-anchored** at `212ad7e6d` with the fixed parser: **650 failed / 9,747 passed /
27 skipped / 33 errors**, `parse_complete: true` (the ids recovered account for pytest's own totals).
The previous receipt was labelled `28ff23976, dirty=true` — its contents were the post-merge tree, so
it was a valid comparand, but the SHA it carried was not the tree it measured.

**Known noise source, carried:** `test_end_to_end_integration.py::TestCrossComponentIntegration::test_high_load_integration`
is non-deterministic (pass/pass/fail over three identical runs) and can appear on either side of a
single-run diff without meaning anything.

---

## 4. Activation-token dry-run [MEASURED]

`tests/safety/test_activation_token.py` (51 tests) and `tests/safety/test_raw_broker_script_guards.py`
(8 tests) are the dry-run, and they run on macOS with no broker and no MetaTrader5.

**Fails closed without a token** — the fake MT5 module records every `order_send` it is asked to
perform, and the assertion is that it recorded **nothing**:

| Entrypoint | Covered by | Result |
|---|---|---|
| `RealMT5.order_send` | direct | refuses, `activation_token_absent`, broker never reached |
| `execution.py:9744 / 9785 / 9894 / 9935` | route through `self.mt5.order_send` → the adapter | covered |
| `execution.py:6710` (`executor.submit(self.mt5.order_send, request)`) | the check is inside the **callee**, so a bare-attribute reference is covered automatically — this is exactly C2's blind spot | covered |
| `scripts/dual_broker_execution_follower.py` | builds its engine on `create_mt5` → the adapter, **plus** its own armed halt check | covered |
| `scripts/fn_smoke_trade.py` (raw module) | `authorize_raw_broker_request` before the entry order | covered |
| `src/safety/heartbeat_monitor.py:727` (raw module) | flatten path — risk-reducing **by policy**, exempt by design | exempt, stated |
| `scripts/mt5_preflight.py`, `emergency_close_and_stop_redacted_account.py`, `flatten_all_positions.py`, `.tools/monitor_books.py` | **not covered** — see declared gaps | open |

**Denials measured**: absent · expired · signature-invalid (hand-edited expiry) · wrong account ·
signing key removed · namespace unsatisfied · namespace mismatch · config digest mismatch · unknown
action. Each raises `ActivationTokenError` with a named reason and the fake broker records zero sends.

**The non-negotiable, measured**: with an expired token *and* with no token at all, a close, a partial
close, a pending cancel and a stop tightening all reach the broker. Removing the risk-reducing
exemption fails 7 tests, verified by mutation [MEASURED] — the tests are not decorative.

`test_the_mutating_surface_has_not_widened` is a source census (deliberately, and the docstring says
why): it fails if a new `.order_send(` appears under `src/` outside the named exemption list.

---

## 5. Verdict

**G0 MET, on the restated criterion, with the gaps below declared.**

Phase 0 items 1–6 are complete: fork reconciled (`46c526bfe`, `9495752c2`, `28ff23976`, `31cf05634`),
evidence route vendored (`41425481e`), F13 fixed (`44f9a02c6`), activation token landed (`7c85c3105`),
OD-2 executed and P1 landed (`4a11faa78`, `e5c7ce30a`), history-graft doc recorded (`a258ad6dc`).

---

## 6. Declared gaps — required output, not an admission

- **The genuine-defect count inside the 650 is still unmeasured** (C10, and B10/B11 killed both cheap
  explanations). The largest open question in the programme's measurement layer.
- **The 33 collection errors are not classified.** ~23 are attributable to the missing
  `pytest-asyncio` plugin, which cannot be installed here (C11: Homebrew Python 3.14.4 is PEP-668
  externally-managed and a venv would invalidate other assumptions).
- **`scripts/mt5_preflight.py` is still default-live with no halt check** and is not routed through the
  activation guard. It was left because its order path is already behind an opt-in
  `--test-order`/env gate, but that is a weaker guarantee than every other entrypoint now has. Named
  in H6.
- **`emergency_close_and_stop_redacted_account.py` and `flatten_all_positions.py` are deliberately
  ungated.** Per B21 they are the operator's only gate-independent exit, and the owner's 2026-07-26
  decision makes that load-bearing. Ungating them is the correct behaviour, not an oversight — but it
  means those two paths are outside every mechanism in this receipt.
- **The activation token has never run against a real broker.** Every test uses a fake module. The
  first live exercise is a canary-day step, and `create_mt5("live")` succeeding on macOS (C1) means
  construction proves nothing.
- **The token's HMAC does not defend against an adversary with write access to the token directory** —
  the key lives beside the tokens. It is tamper-evidence against a hand-edited expiry. The module
  docstring states this rather than overclaiming.
- **R2 has never been used to run an arm.** It binds through the real enforcement entrypoint for all
  four arms [MEASURED], but no window has been launched under it. The pack-build-seal and prepared-pack
  steps (C8) take `--decision-contract` as an argument and therefore need no code change, which is
  verified by reading the argument parser — **not** by running them.
- **Three review findings are recorded and not fixed** (see `IMPLEMENTATION_STATE.md`): the
  daily-P&L `$0.00` reporting defect, the `consecutive_losses` `losses_today` `TypeError` on a `None`
  fetch, and `pytest_failset.py`'s truncation of parametrized ids containing spaces. The first two sit
  on the legacy fleet/notification path; the third weakens the A/B tool this receipt depends on and is
  the highest-priority of the three.

---

## 7. Open question for the owner (one, batched as promised)

**Q3 — graft the legacy June history, or leave it referenced?** The engine's formative 1,006 June
commits exist only in the iCloud legacy repo (F28). Option 1 (reference, via
`.context/00_core/repository_history_graft.md`) has landed and is sufficient for reading. Grafting
would make `git blame`/`bisect` work on the engine's core, and costs an iCloud re-materialisation plus
a mutation of a store the migration record treats as read-only (C12). **No urgency; it blocks nothing
in Phase 1.**
