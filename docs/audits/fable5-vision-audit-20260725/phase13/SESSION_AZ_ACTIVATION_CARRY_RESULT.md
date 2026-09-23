# Session AZ — the carry that makes the estate's one admission runnable, and the file that must not be in it

**Wave 13. Branch `phase13/activation-carry`, from `main` at `46a0d21be`. Blocks B1850–B1867.**

**Scoped A/B: `phase13/SESSION_AZ_AB.md` — 0 bad → 0 bad, 0 regressed** over the 17 shared
files, **+39 net new passing tests** in one new file.

Nothing touched the VPS, no broker-capable script ran (not even `--help`),
`config/agent_config.yaml` and `config/profiles/redacted_account.yaml` are byte-untouched, and **the
package arms nothing by itself**. H1/R2 drift is 2 `UNHYDRATED-LFS` at session start and 2 at
session end — unchanged.

**Deliverable:** `phase13/activation_carry_mx/` — MANIFEST.json, four payloads (plus three
`run_book.py` variants), diffs against the **host's** bytes, `build_carry.py`, `verify_carry.py`
(six gates), `receipts/az_carry_probe.py` + `AZ_CARRY_PROBE_V1.json`. Three documents:
`AZ_CARRY_ENUMERATION.md` (what is carried and why), `ORDERING_AND_PARTIAL_STATES.md` (what a
half-done ceremony leaves running), **`MX_ACTIVATION_CEREMONY.md`** (the handoff).

---

## 0. What was found, in order of how much it matters

**1. The commission's fifth file must not be carried, and carrying it would have moved armed
money for nothing.** The brief says the package *"must also carry AS's `execution.py`
adopt-path fix — it is a live-crash fix independent of the activation"*. Measured against the
host's own bytes: Session AS's `KeyError('trigger_r')` is **real on mainline and unreachable on
this host**. The host's `hydrate_vnext_dynamic_policy_from_record` carries an explicit
`if selected_policy == "time_stop":` branch from lineage commit **`b36d9ab92`** — an ancestor
of `redacted_host` and **not** of `main` — that sets `trigger_r = 0.0` and guards `final_target_r`.
Driving the host's own path returns `hydrated: True` today. Applying mainline's replacement as
a control moves **three of three** adopt probes, none of which raised first: on `crypto`, which
is ARMED on both accounts, `be_trigger_r 0.0 → 4.0` and **`take_profit_1 0.0 → 3040.0`**. The
carry is **four files**, and AS's fix is filed as *host-inapplicable* rather than closed.

**2. Six of the eight wired frontier sleeves killed `run_book.py` at launch, and the ceremony
would have shipped it.** The banner rendered `float(_o["final_target_r"])` unconditionally;
the six `time_stop_*` cells carry no such key. So `--frontier-exits vol_compression` raised
`KeyError` **after `parse_frontier_exits` had accepted the name** — the worker dies before
`BookLauncher`, the supervisor restarts a missing book forever, `manage_open_positions` never
runs on either namespace. `mx_btcusd` was never one of the six, which is why AU's 43 tests did
not see it and why this ceremony would have carried the landmine to a live host. Fixed on
mainline and in the payload; the invariant pinned is **what validation accepts, the next line
can render**.

**3. Nine of sixteen partial states are unsafe and a module-top import probe finds ZERO of
them.** Session AC's grid found *half* its fatal states by import. Here the `imports` column is
`ok` in all sixteen rows, because every failure in this carry is a **signature** mismatch, not a
missing module: 4 module-load deaths (`run_book` without `execution_packets` — a deferred import
inside `main()`, unconditional), 3 startup deaths, 2 **silent placement outages**.

**4. And the third class is not a crash — I published it as one first.**
`UltimateBookOrderRouter.place` wraps its body in `except Exception` (*"the book NEVER breaks
the live path"*), so `order_router` without `execution_packets` returns
`placed: False, reason: "router_exception:TypeError(…'frontier_exits')"` on **every unit,
forever**, while the process stays up, the heartbeat stays healthy and exit management keeps
running. Worse than "fatal" in one way and less in another. It is the state most likely to go
unnoticed, and it is now what the docs, the gate message and a test all say.

**5. `run_book.py`'s host bytes are pinned by no artifact, so the package ships a variant
table.** The Stage-0 token ceremony recorded line counts and no sha256. The state is bounded
anyway: the host's `book_owner.__init__` accepts neither `recover_pre_gap_bar` nor
`vol_level_tilt`, so any `run_book` from Session AI onward is a startup `TypeError` on both
namespaces — and both books are alive. Exactly **four** committed versions survive that filter;
each gets its own pre-built payload and exact after-sha256, `--check preflight` names the one to
copy, and an unrecognised sha256 is a **STOP with the bytes printed**, not a default.

**6. A fourth ordering invariant lives outside the file grid and is the most expensive one.**
`--frontier-exits` on the supervisor line with an uncarried `run_book.py` is `argparse` exiting
on an unrecognised argument at every respawn of every namespace. Reachable on the way **in**
(step 8 before step 6) and on the way **out** (restoring `run_book.py` before the `.ps1`), which
is why the rollback order puts the supervisor line first. `--check deps` reads the `.ps1`.

**7. The blast radius of the whole carry is one field on fourteen sleeves, and nothing armed.**
34 sleeves compared before/after over exit profile, adopt instrumentation and the full placement
dict: 14 move, all `mx_*`, all on `time_stop_bars` (96 → 7680) and its two derived copies. The
four ARMED sleeves are **byte-unchanged in all three sections**, with and without the selection.
Registry size 32 → 32. No config byte is needed — the host's own DF-1 filter already resolves
`mx_btcusd`.

---

## 1. AZ-1 — the carry set, by diff

Full detail: `AZ_CARRY_ENUMERATION.md`. In one table, with the host's bytes taken from
committed artifacts (the Session S and AC payloads, both verified at after-hashes on the running
host 2026-07-30) rather than from mainline:

| # | destination | host today | shape | why |
|---|---|---|---|---|
| 1 | `execution_packets.py` | lineage `e533f162d` | **mainline whole** | diff vs lineage is **exactly** AQ's unit repair + AU's registry + AZ's renderer; import header **byte-identical** |
| 2 | `order_router.py` | lineage `af2e696c1` | **mainline whole** | 14 lines, both hunks AU's, same import header |
| 3 | `book_owner.py` | Session S payload `2b9aab7b…` | **host + 4 anchored edits** | mainline is ~330 lines of diff and 4,100 lines longer, with wave 5–12 closure this host lacks |
| 4 | `run_book.py` | one of four (§0.5) | **host + 2 anchored edits** | no artifact pins it; the two mainline kwargs the host's owner rejects are deliberately absent |
| — | `execution.py` | AC payload `d0d36787…` | **NOT CARRIED** | §0.1 |
| — | both config files | — | **NOT CARRIED** | hashed into the live tokens' config digests |

**Every mainline change riding along is named and classified** in `AZ_CARRY_ENUMERATION.md`
§2.2, with its measured blast radius. The one that matters: `sub_xvol_pullback @ target_4R` is
wired in the carried file and **must not be selected** — the sleeve is armed at 3R and its 4R
cell REJECTS at all four cost bands at the ratified rule (AU §1.3, p 0.0080 against a 0.002083
bar). The committed 3R is untouched and asserted so.

**Seal exposure: none.** All four carried paths are unbound by R2, R1, `code_authority_paths`
and `config_file_hashes`, re-checked this session.

---

## 2. AZ-2 — the package, in Session T/AC's shape

`build_carry.py` derives every payload from its declared source and `--check` re-derives and
compares byte for byte, so a later edit to `execution_packets.py` cannot leave a stale payload
that the manifest still vouches for. `MANIFEST.json` carries copy order, per-file before/after
sha256, the `composes_with` declaration for the two prior carries (including that this carry
**supersedes** Session S's `book_owner.py`), and a `not_carried` block that gives the reason for
each omission rather than leaving it to be inferred.

**`verify_carry.py`, six gates**, exercised in both directions against materialised host trees
before shipping:

| gate | asserts | tested |
|---|---|---|
| `preflight` | the host is in a state this carry was built for; **names** the `run_book.py` payload | passes on the pre-carry tree; FAILs with the bytes printed on an unrecognised `run_book.py` |
| `postflight` | every destination at its after-bytes — **by sha, not behaviour**, because a truncated file imports, constructs and ticks | passes carried, FAILs uncarried |
| `deps` | the four ordering invariants, on disk, before any import | scored correctly on 14 synthetic states incl. all four `.ps1` cases |
| `imports` | every `src.` import `run_book.py` performs — derived from the host's OWN file by AST, **deferred imports included** — then both constructions | passes carried |
| `behaviour` | the activation resolves `target_5R`; the four armed sleeves are identical; the adopt path rehydrates; the banner renders for all eight; no frontier config key | 27 scored assertions, all pass |
| `rollback` | back at the bytes `BACKUP_MANIFEST.json` recorded — **not** the lineage's — and the tree still starts | passes reverted, FAILs carried |

Two deliberate improvements on AC's version. `check_interpreter` refuses the wrong interpreter
only when `.venv-gtos` **exists**, so the gates can be exercised off the host — AC's
unconditional refusal meant its verifier's first real execution was on a live funded machine.
And `--check imports` derives its import list from the host's own `run_book.py` rather than from
a hardcoded list, so a carry that adds an import cannot outrun its own probe.

---

## 3. AZ-3 — the ceremony page

`MX_ACTIVATION_CEREMONY.md`. Twelve steps, every one a safe place to stop except the restart,
with the **carry (3–7) separated from the activation (8–12)**: after step 7 the host can run the
admission's contract and is not running it, every default byte-identical to today. That seam is
what lets the code land and be lived with independently of the owner decision to arm.

It carries: the six preconditions with their evidence (the F15 `copy_rates` probe at 7,800 ≥
7,680 on both terminals; the sleeve already in the host's effective registry, **measured on the
host's own DF-1 filter**; `include_clean3` verified; the identity proof; the seal answers); the
host-admin ≤2,800-char base64 chunk mechanics; the exact five-sleeve tag string; the supervisor edit
with its guards (and why the per-book form is preferred over the one-line form that is
*measurably inert* on redacted_account but would advertise a contract FN does not run); the
`firing_sleeves.json` step and the one case where it is a +25.2 % sizing event; the flat-check
requirement **with its real reason**; the two log lines that prove it took; and a rollback whose
order is the reverse of the ceremony's, with the supervisor line first.

**The sizing statement, stated so nobody reads the headline as the plan.** Registry confidence
**0.025** of a total **7.77** — **0.32 %**, the pre-existing default-off weight and not a choice
this ceremony makes; re-weighting is OD-AI-5 and separate. The planning number is **+0.198
R/day** (AN's measured chronological decay: the two most recent folds), **not** the full-window
+0.982. `maxbars` share 1.89 %. And any package citing the admission must name **both** repairs
it is contingent on — at the old `96` the same cell rejects at all four bands (p 0.0564), at the
spec's 2R it rejects (p 0.0064); neither alone admits.

---

## 4. What I got wrong

**I published a failure class as "FATAL at PLACEMENT" and it is not fatal.** The probe called
`build_book_trade_params` directly, so it measured the raw `TypeError` rather than the outcome.
`UltimateBookOrderRouter.place` catches it. The real consequence — every unit refusing to place,
forever, behind a healthy heartbeat — is a *different* failure and arguably a worse one to be
in, and the word "fatal" would have sent an operator looking for a dead process. Found by
reading the carried `order_router.py`'s own body to check an unrelated claim. Now measured by
driving the real `place()` on every tree, and pinned.

**My rollback gate failed a correct rollback — Session S's own published defect, reproduced
inside the package written to avoid it.** `--check rollback` called `check_imports`, which
demanded the frontier selection construct; after a correct rollback it cannot. An operator who
had just reverted correctly would have been told the tree was broken and not to restart, at
2 a.m., on a funded account. S found this in its own carry, AC quoted it back, and I did it
anyway through the behaviour half instead of the byte half. Caught by **running** the gate on a
reverted tree rather than by reading it.

**My state grid reported every state safe on its first run, because the probe was narrower than
the claim.** It probed module-top imports only, and this carry's characteristic failure is a
*deferred* import inside `main()`. Then, having fixed that, the same probe reported every state
**fatal** — because I checked imported names with `hasattr`, and `from src.utils import
notification_queue` binds a submodule, not an attribute. Both are the wipeout shape AU filed:
a whole column of uniform verdicts is the instrument, not the subject. What caught both was
reading the table rather than the exit code.

**My adopt probe used a stub too thin to answer the question it was asked.** A hand-rolled `_T`
class raised `AttributeError: 'trade_id'` in all sixteen states, which hid whether the host's
rehydration reaches its end. Replaced with the real `TradeState` — and only then did the
`KeyError`-cannot-happen claim become a measurement instead of a reading.

**A partial probe run published an artifact that read as a complete one.** `--stage states`
overwrote the receipt with a file containing only `states`, silently deleting `blast_radius` and
`as_fix_control`; two tests then failed for reasons unrelated to what they assert. The driver
now merges. Same class as AU's null block, AN's verdict-inverting null and AQ's 72 clean-looking
`NOT_EVALUABLE` arms — the defect is not the missing data, it is that the artifact still looks
finished.

**My first regression guard for B1852 was a source-string test and it tripped on the comment
explaining the defect.** `'["final_target_r"]' not in block` matched the prose. Rewritten over
the AST — no `Subscript` on that constant inside the banner loop, and
`describe_frontier_contract` called in it. Exactly what the engineering rules say about
source-string assertions, learned the cheap way.

**And one inference a reader should check rather than take.** The claim that the host's
`run_book.py` is one of four rests on the host's `book_owner.py` being the Session S payload. It
was verified on the running host on 2026-07-30 and `--check preflight` re-verifies it before
anything is copied — but if that gate FAILs on `book_owner.py`, the variant table's derivation
is void along with it, and the right response is to stop rather than to reach for the primary
payload.

---

## 5. Ledger, repairs, blocks

* **Blocks** — B1850–B1867 in `IMPLEMENTATION_STATE.md`. The commissioned range B1850–B1899 is
  not exhausted.
* **Multiplicity** — **no new looks.** Nothing in this session gates an arm; every economic
  number quoted is a re-citation of AQ's, AU's, AN's or AI's already-ledgered work. No
  declaration file is touched.
* **H1/R2** — checked before every `src/` edit. `run_book.py`, `execution_packets.py`,
  `order_router.py`, `book_owner.py` and `execution.py` are unbound by all three mechanisms.
  Drift 2 `UNHYDRATED-LFS` at start and end.
* **Tests** — `tests/ultimate_book/test_az_activation_carry_mx.py`, **39 tests**: package
  reproducibility, the manifest's before-hashes against the prior carries' after-hashes, the
  whole-file payloads' import closure, the variant table re-derived **from git** in both
  directions, the B1852 invariant behaviourally and over the AST, the not-carried decision (both
  files' contents *and* the control's continuing demonstration), the blast radius, the state
  grid, the verifier's byte gates over 14 synthetic states, and that the carry arms nothing.
* **A/B** — `phase13/SESSION_AZ_AB.md`. 0 bad → 0 bad, 0 regressed; +39 in one new file. The
  new file is outside the shared scope and reported separately, because an A/B across different
  scopes is not a comparison.

---

## 6. Handoff — for the orchestrator

1. **`MX_ACTIVATION_CEREMONY.md` is the page.** Preconditions are all met; the package is
   verified in both directions against a reconstruction of the host's tree; the first thing to
   run on the host is `--check preflight`, and the first thing to read in its output is which
   `run_book.py` payload it names.
2. **Do not carry `execution.py`.** §0.1. If a future session wants AS's fix on the host,
   re-run `az_carry_probe.py --stage as-control` first and put the three moved probes in front
   of Borhen — it is a broker-TP change on adopted positions of armed sleeves, not a bug fix.
3. **Do not select `sub_xvol_pullback`.** Its `target_4R` cell is wired in the same file and
   REJECTS at all four cost bands at the ratified rule, on a sleeve trading real money on two
   accounts. AU and AS agree independently. The ceremony's tag string and flag name one sleeve.
4. **The sizing question is live and is not this ceremony's.** At registry confidence 0.025 the
   admission is economically inert by design (0.32 % of book weight). Whether to re-weight it is
   OD-AI-5, and the number to re-weight *on* is +0.198 R/day, not +0.982.
5. **The `mx_*` cohort's `want = budget + 64` exposure is cleared for BTCUSD only.** The F15
   probe measured 7,800 bars on both terminals against the 7,744 an open `mx_btcusd` position
   requests. Any *other* `mx_*` sleeve armed later needs its own probe on its own symbol — a
   short feed makes the time stop **inert**, not late, and the wall-clock fallback does not catch
   it.
6. **One thing this package does not do and the next carry should.** It verifies the host's
   bytes for three of four files against committed artifacts, and for `run_book.py` against a
   derived table. The reason a table was needed is that Stage 0 recorded line counts instead of
   hashes. **Every future ceremony should write a `CARRIED_STATE.json` on the host** — path →
   after-sha256 — so the next session reads the host's state instead of reconstructing it. The
   ceremony's `BACKUP_MANIFEST.json` is half of that already.

**Not mine and untouched:** the VPS, arming, tokens, gates, α, sleeve composition, the
population rule, registry weights, `config/agent_config.yaml`, `config/profiles/redacted_account.yaml`,
merging to `main`.
