# Session BD — the live-path debt sweep (wave 13, B2050–B2099)

**Branch `phase13/live-debt-sweep`. Ten filed items: six built, two closed by measurement, two
verified already-built. Nothing armed; no config byte moved; no R2-bound path touched; the VPS was
not contacted; no broker-capable script ran.**

Reproduce: `python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/bd_partial_exit.py`
A/B: `phase13/SESSION_BD_AB.md` — **0 bad → 0 bad, 0 regressed**, 2118 → 2121 over 80 shared files
by sha-verified copy-back, +79 in 5 new files.
Ledger: `phase13/BD_DEBT_LEDGER.md` · Manifest: `phase13/BD_CARRY_MANIFEST.json`

---

## 0. The answer

**Four of the six things I was asked to build turned out to have a defect in the filing, not just an
absence of code — and in three of those the filed repair, implemented literally, would have been
wrong.** That is the through-line of this session, and it is not a criticism of the filings: each
was written by a session that had measured something real and handed off before it could measure the
next thing.

The four, in descending order of what they cost if taken at face value:

1. **OD-P1's 76.05 % is a property of a state contract nobody wrote down**, and the obvious
   implementation delivers **40.14 %** instead of **96.72 %** — 2.4× less — while looking deployed.
   The entire gap is one nested `checked_at_utc` inside `policy_clock_diagnostic`. For an
   **irreversible** change, shipping the contract matters more than shipping the number.
2. **OD-P3's "small change to that allowlist" ships 6.21× the bytes and fails quietly.** The
   forbidden-key scan does not catch it — `_clean_mapping` redacts `profile.server` first — so it
   validates and ships 217.5 MB per window where 35.0 MB would do.
3. **OD-P2's booby trap is narrower than filed and its cure recovers more.** Exactly **1 of 277**
   multi-member units spans two sleeves; the common case is one sleeve on several symbols. So the
   field the trap would corrupt (`sleeve`) is the one an agreement rule recovers on 276 of 277 rows,
   and the field that genuinely cannot be resolved (`symbol`) is refused by the same test.
4. **AQ §6a's missing piece was not the fix.** AQ was right not to patch it. What was missing is
   that the inertness is **invisible**: `book_owner.py:2768` has asked the engine for a time-stop
   clock diagnostic since the packet carry landed, and **no engine in this repository defines it**.

And the fifth item came back with a number that is better and still not admissible:

> **`energy_agri`'s scale-out costs +0.2302 R/day on armed money, gated at the ratified rule for
> the first time — and both arms REJECT at all four bands.** Third instrument, agreeing with AD and
> AU, reproducing AU to four decimals through an independent driver. p 0.321 → 0.206 against
> α 0.10, n = 64, and the chronological folds decay under *both* contracts with the most recent
> negative either way. Wired as a priced, inert option. **The recommendation is not to arm it.**

---

## 1. The three packet decisions (OD-P3, OD-P2, OD-P1)

### 1.1 OD-P3 — the gap is total, and the filed repair is the wrong shape

Measured over the 99,112-packet export: **zero** packets carry any modelled cost. Not
`pretrade_total_cost_r`, not `pretrade_spread_r`, not `gtos_vnext_pretrade_cost_model`, not
`economics.cost.modelled_cost_r`. Three `pretrade_*` keys have sat in the allowlist all along with
no producer, which is exactly why the allowlist framing looked cheap.

**The counterfactual, run rather than asserted.** My first draft of the test asserted the naive
repair would be *quarantined*: the model carries `profile.server`, `server` is in
`FORBIDDEN_RAW_KEYS`, and `_contains_forbidden_raw_key` scans recursively. It is not quarantined.
`_clean_mapping` redacts the value to `server_hash_sha256` **before** the scan ever runs, so the
naive repair passes validation and ships a hash of the broker server name in every packet as noise.
The loud failure I predicted is a quiet one, which is the worse of the two. What it actually costs:
**2,764 bytes against 445** — 6.21× — and at `position_managed` volume **217.5 MB against 35.0 MB
per 37-day window**, on the stream OD-P1 exists to shrink by three quarters.

**The part with more value than the wiring.** `total_cost_r` is `spread + slippage + swap`
(`broker_net_cost_engine.py:578-583`) and charges **no commission** — F38's exact shape, surviving
in the *pretrade* model after being repaired in the realized one. `build_cost_block`'s realized side
charges `broker_entry_commission` and `broker_exit_commission`. So `modelled − realized` is biased
by the entire commission bill in a known direction, and a reader who did not know would book the
bias as slippage-model error. The block now publishes `modelled_cost_excludes: ["commission"]`
unconditionally and a three-valued `modelled_vs_realized_comparable` — `False` when the realized
side charged commission, `None` when either side is absent, `True` only when subtraction is
actually safe. A bare boolean would have let absent evidence read as a green light.

### 1.2 OD-P2 — the agreement rule, and what the corpus says about the trap

D4's rule was right and its **scope** was one field. Applied to the whole join key and replayed
through the production function over the real corpus:

| field | agree | disagree | rows newly filled |
|---|---:|---:|---:|
| `sleeve` | 681 | **1** | **276** |
| `timeframe` / `decision_bar_iso` / `decision_day` | 682 | 0 | 277 each |
| `direction` | 630 | 52 | 225 |
| `symbol` | 405 | **277** | **0** |

P expected multi-sleeve units to be the common case — *"anything spanning two sleeves of a cluster
… yields `{}`"*. Measured, **1 of 277**. The common multi-member unit is one sleeve on several
symbols, which is why `symbol` disagrees on all 277 and the rule correctly declines to emit it on
every one.

The `_first_unit_sleeve` representative-guess would fire on 277 rows and be **wrong on 1**. That is
a narrower blast radius than P feared, and it is not a bound on tomorrow's — it scales with sleeves
per cluster and the registry resolves 32. The trap is **pinned inert**, not widened: a test fails if
`SizedUnit.sleeve_members` ever stops being a tuple, and a second test feeds the join rule a
JSON-round-tripped unit (the shape that arms the trap) and requires the same answer.

`admission_unit_join_status` is three-valued for a reason found while writing it: a two-valued
version reports `members_disagree` on the majority case, where the *sleeve* is clean and only the
symbol is mixed — telling a reader the attribution is untrustworthy on 277 of 277 rows where it is
sound on 276.

**Still open and filed, not fixed:** **303 of 985** unit rows (30.8 %) carry no member roster at
all, so no rule recovers a join key for them. Whether that is empty `sleeve_members` or a
`skip_context` miss is unmeasured, and the two have different repairs.

### 1.3 OD-P1 — the dial, and why the contract is the deliverable

| state contract | drop % of `position_managed` | of whole stream |
|---|---:|---:|
| none (every field is state) | 0.94 % | 0.74 % |
| top-level `*_checked_at_utc` excluded | 40.14 % | 31.87 % |
| **recursive `*_checked_at_utc` excluded** | **96.72 %** | **76.79 %** |

The third line reproduces P's 76.05 % to within 0.7 pp. The second is what you get if you write the
obvious exclusion list, because `policy_clock_diagnostic` is a nested dict embedding its own
`checked_at_utc` on 59.7 % of rows at 100 % churn. **A top-level implementation under-delivers by
2.4× while looking deployed** — and this change is irreversible for the window in which it runs, so
"looks deployed" is the expensive failure.

The rule is named rather than hand-picked (`checked_at_utc` or `*_checked_at_utc`, any depth) and it
lands in a real gap: on `position_managed` the churn is bimodal — four fields at 100 %, two at
4.86 % (`policy_clock_bars_until_due`, `policy_clock_elapsed_m15_bars`: the bar clock advancing,
which must survive and does), and every one of the other 98 at ≤ 0.46 %.

**The recommended configuration is not the headline.** 76.79 % is the no-heartbeat figure; with the
15-minute heartbeat P recommends in the same paragraph it is **73.70 % of stream** — the heartbeat
costs 3,069 packets, 2.35 pp.

**What is lost is now countable.** A suppressed packet is unrecoverable, but by construction it is
identical to one that was kept, so what a reader loses is the *run length*, not the state. Every
emitted packet carries `emit_on_change_suppressed_before` and `emit_on_change_unchanged_seconds`.
Fails open on every path (unidentifiable position, unserialisable outcome, filter exception); only
ever touches `position_managed`, with eleven other event types parametrised as never-suppressed; and
the cycle summary carries the count **without** touching `packet_write_error_count`, because feeding
it there reaches `ai_companion/supervisor.py:517` and issues `pause_new_entries` on both accounts
for a working compression.

---

## 2. AQ §6a — detection built, behaviour deliberately not

AQ filed `want = budget + 64` and declined to patch it: the obvious mitigation moves armed sleeves
onto the over-counting wall-clock path and closes them **earlier**. That judgement stands and is
respected. Two things were missing that are not the fix:

1. **`len(candles) < want` is not the test.** A broker legitimately returns fewer bars than asked —
   a young symbol, a long holiday. The only question is whether the returned window reaches back
   **past the fill**: if the oldest closed bar printed after `entry_dt`, the count is a lower bound
   and not a count. Free, from timestamps the function already parses.
2. **The inertness was invisible.** `book_owner.py:2768-2772` asks the engine for
   `get_time_stop_clock_diagnostic`, then for `_last_time_stop_clock_diagnostic`, and **no engine in
   this repository defined either name**. `policy_clock` was `None` on every tick of this lineage. A
   time stop that cannot fire produced no signal anywhere. This engine is now that producer.

Detection is always on and changes no returned value (pinned). The behaviour change sits behind
`ultimate_book_time_stop_wallclock_on_truncated_window`, default OFF, set by no committed config;
arming it trades an inert backstop for an early one, which is per-sleeve and Borhen's.

**Why it ships now:** F15 measured 7,800 bars available against an `mx_*` request of 7,744 — **56
bars, 0.72 % of headroom** — on a terminal setting a future session can change without knowing this
code exists. Nothing armed is exposed (H4 at 1280 wants 1344).

---

## 3. `energy_agri` — the third instrument, and it still rejects

Gated at the ratified rule with the cut rule declared before any gate ran: two arms per sleeve
(committed profile verbatim; the same target and horizon with the scale-out and BE move removed),
no grid, nothing fitted.

| sleeve | live | plain | plain − live | verdict L/P | p L/P |
|---|---:|---:|---:|---|---|
| **`energy_agri`** (ARMED) | +0.1763 | +0.4065 | **+0.2302** | REJECT / REJECT | 0.321 / 0.206 |
| `metals_softband` | +0.0530 | +0.0902 | +0.0372 | REJECT / REJECT | 0.329 / 0.283 |
| `metals_core` | −0.1300 | −0.2077 | **−0.0777** | REJECT / REJECT | 0.871 / 0.952 |
| `metals_ob_micro` | −0.1207 | −0.1606 | **−0.0399** | REJECT / REJECT | 0.732 / 0.651 |

R/day, mid band. **The control does its job — the sign runs both ways, 2 of 4 each.** A harness that
preferred plain everywhere would be measuring itself rather than the contract. And it reproduces
AU's two published figures (+0.2302 on `energy_agri`, −0.0777 on `metals_core`) to four decimals
through an independent driver.

**It is not an admission.** n = 64. `maxbars_share` 0.0 on both arms, so it is a contract difference
and not a ceiling artifact. `p_min` over the two arms is 0.2005 against 0.3608 expected under the
global null. And the mandatory fold table is the part to read before anyone sizes anything:

    LIVE   [+0.533, +0.282, −0.287]
    PLAIN  [+0.933, +0.351, −0.064]

Both decay hard; the most recent fold is **negative under either contract**; most of the improvement
sits in the earliest fold. Wired as `plain_exit_no_partial`, default OFF, ceremony selects by name.

**One structural nuance, which corrects how AU §2's phrasing will be read.** The delta is
*identical* at all four bands (0.230213 everywhere) because a cost band shifts both arms equally.
"At every band" is therefore a property of the comparison, **not four independent confirmations** —
of AU's figure as much as mine.

---

## 4. The carry, and the hazard this session created and then removed

`BD_CARRY_MANIFEST.json` is generated (AZ's shape; AZ's manifest read out of git by commit, because
wave-13 siblings are parallel branches and it is not an ancestor of my HEAD).

| file | disposition |
|---|---|
| `book_owner.py`, `execution_packets.py` | **AZ-PAYLOAD-STALE** — AZ's snapshots predate these changes. Rebuild from the merged tree; never apply two snapshots of one path. |
| `packet_emit_on_change.py` | NEW |
| `packet_economics.py`, `src/costs/model.py` | BD-only (`src/costs/` does not exist on the host — research surface) |
| `execution.py` | **DO-NOT-CARRY-WHOLE** |

That last row closes **AS handoff 7 and inverts it**. AS asked for a deploy decision on B1535,
noting the books run the pre-fix code. AZ measured the answer against the host's own bytes: the host
diverged at lineage `b36d9ab92`, the `KeyError` is **unreachable there**, and mainline's hunk would
move `be_trigger_r` 0.0 → the record's value and `take_profit_1` 0.0 → `be_trigger_price` on adopted
time-stop positions across **all four armed sleeves** (3 of 3 adopt probes). My AQ §6a diagnostic
lives in that same file, so it inherits the restriction: a whole-file carry of mainline would ship
B1535 silently. Deferred with that reason. The diagnostic is worth having on the host; it is worth
less than an unintended exit-behaviour change on armed money.

**And the hazard I introduced.** `book_owner.py` is on the host; `packet_emit_on_change.py` is not.
A module-top import of a file that has not landed raises `ImportError` at load, propagates out of
`run_book.py` startup, and stops **both funded accounts** — the worst outcome a carry can have, and
a partial state AZ's 16-state probe could not have covered because the file did not exist when it
ran. The import is now optional by construction, with `except Exception` rather than
`except ImportError` so a half-transferred **corrupt** module degrades identically to an absent one
— the same guard `packet_economics.py:50-66` applies to `broker_clock`, for the same reason.
Verified by blocking the import through `sys.meta_path` and importing `book_owner` for real, not by
asserting the `try`/`except` exists. Carry order is therefore unconstrained.

---

## 5. Claims I made during this session and then withdrew

1. **"The naive OD-P3 repair would be quarantined."** False, and I had written it into a test
   docstring and a test body before running it. `_clean_mapping` redacts `profile.server` to
   `server_hash_sha256` before `_contains_forbidden_raw_key` ever sees it, so the naive repair
   *passes* validation. The loud failure I predicted is a quiet 6.21× size cost. The corrected test
   runs the counterfactual instead of asserting about it.
2. **I nearly published a units correction to a figure that was correct — on armed money.**
   `pooled_oos_mean_r` is a mean over the pooled OOS series, and I read the series as per-trade,
   which would have made AU's `r_per_day` key a mislabel of the same class as AQ's `time_stop_bars`.
   `folds.py:262-267` builds `test_r` from `daily.items()` — it is a **per-day** series, `_pooled_oos`
   says so in its own docstring, and the variable is named `n_days`. AU is right; **my** label was
   wrong, and it was in the driver and its output before I checked. Corrected before the artifact
   was committed. The near-miss is the point: a correction to a published figure needs the same
   verification as the figure.
3. **A test that passed through the wrong code path.**
   `test_the_flag_does_nothing_when_the_window_covers_the_fill` asserted the right outcome for the
   *"lower bound exceeds budget"* reason rather than the *"covers entry"* reason in its own title —
   my fixture's entry date was outside a 7,744-bar window on a fake whose bars are
   calendar-contiguous (real M15 bars print only in market hours, so 7,744 of them span ~112
   calendar days, not 80.7). Green, and vacuous. Now anchored to the bar grid with an assertion on
   the branch actually taken.
4. **My first `_is_committed_but_unhydrated` returned False for the exact artifact it was written to
   recognise.** It ran `git ls-files` with `cwd=path.parent` — which is usually the very directory
   sparse-checkout left out — against a repo-relative path. It answered "cannot tell" and fell
   through to the wrong message, i.e. it reproduced the bug it was fixing. Also renamed to
   `_is_tracked_by_git`, because that is what it checks; the original name over-promised.
5. **I used `isinstance(model, Mapping)` in `book_owner.py`.** That module imports only
   `Any/Callable/Optional` from typing, so a bare `Mapping` at runtime is a `NameError` no syntax
   check catches — and `_broker_server_name` documents this trap in a comment at `:1369` that I had
   already read. Caught before running, rewritten to the module's duck-typed convention.
6. **My first A/B base capture was unusable and the tool caught it, not me.** I passed the full
   85-file scope to both sides; five of those files do not exist at BASE, pytest aborted at
   collection with no counts line, and `pytest_failset.py` marked it `usable_as_baseline=false` and
   refused to diff it. Had it not, I would have compared against an empty failure set and called it
   clean.
7. **I attributed 18 test failures to my own changes for several minutes.** They were an unhydrated
   LFS pointer (`SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` read as JSON), present at session start —
   my own first H1 check had reported it and I did not connect the two until I read the traceback.
   This is the trap CLAUDE.md H1 documents and the working agreement pre-fixed twice, firing a
   third time.
8. **I hit AS handoff 6 before reading AS handoff 6.** The misleading exception cost me a 25-second
   substrate build and a wrong first hypothesis, exactly as AS predicted it would for the next
   session. That is what moved the fix from "the hydrator carries the path" to "the message says the
   true thing".

---

## 6. Ledger, repairs, blocks

* **Trial ledger** — **32 rows** (`research/operations/trial_budget/TRIAL_LEDGER.jsonl`, session
  `BD`, mechanism `partial_exit_arms`): 4 sleeves × 2 arms × 4 bands, every arm ledgered including
  all 32 REJECTs. It deflates this session's statistics along with everyone else's; that is the
  design.
* **Repair queue** — **6 rows appended** (`phase6/receipts/REPAIR_QUEUE_APPEND.jsonl`, 224 → 230),
  3 primary. No row edited in place.
* **Multiplicity** — **no new looks.** Both `partial_exit` arms are exit-cell re-measurements of
  sleeves already declared in `CANDIDATE_BOOK_V1`; family V5 is read, never written.
* **A/B** — `phase13/SESSION_BD_AB.md`, emitted by `pytest_failset.py receipt`. 0 bad → 0 bad,
  0 regressed, 2118 → 2121 over 80 shared files; +79 in 5 new files. Copy-back in Python,
  sha-verified 12/12.
* **H1/R2** — checked before every `src/` edit. **Nothing this session touched is bound.** Drift
  read `2 UNHYDRATED-LFS` at start and `1` at end; the reduction is one `git lfs checkout` of a
  bound ledger that arrived as a pointer, per CLAUDE.md H1 — no bound file was edited.
* **Blocks** — **B2050–B2075** in `IMPLEMENTATION_STATE.md` (26 blocks). The commissioned range
  B2050–B2099 is not exhausted.

  > **One citation that does not resolve, and it is mine.** Three of this session's five commit
  > messages name block ranges written *before* the blocks were — `B2050-B2085`, `B2086-B2093`,
  > `B2094-B2095`. The authoritative numbering is the one in `IMPLEMENTATION_STATE.md`, **B2050 to
  > B2075 contiguous**, and a reader following those commit-message ranges will find nothing above
  > B2075. Git history is immutable so the wrong strings stay; this line is the correction, and the
  > lesson is the obvious one — do not cite a block number until the block exists.

---

## 7. Handoff — for the orchestrator

1. **Rebuild AZ's payloads from the merged tree.** `book_owner.py` and `execution_packets.py` are
   payloads in AZ's carry package and BD changed both. AZ's `build_carry.py` reads the working tree,
   so the fix is to re-run it post-merge and re-verify `sha256_after_carry` — but a ceremony that
   applies AZ's committed snapshot would silently drop BD's work, and a later BD carry would then
   fail AZ's own `sha256_before_expected`.
2. **`execution.py` must not be carried whole, and that now applies to two sessions.** AZ measured
   it for B1535; BD's time-stop diagnostic inherits the restriction. If the orchestrator opens that
   file on the host for any other reason, BD's three hunks are listed by name in the manifest and
   are safe to port individually — the returned count is unchanged with the flag off.
3. **`energy_agri` is in front of Borhen, not in front of a session.** +0.2302 R/day on armed money,
   third instrument agreeing, REJECT at all four bands, most recent fold negative under both
   contracts, n=64. The contract is wired and off. My recommendation is **do not arm**; the decision
   is his and the option now costs nothing to keep.
4. **OD-P1 is an owner decision with a number that moved.** P recommended yes-with-a-heartbeat at
   76.05 %; the shipped configuration is **73.70 %**, and the state contract — not the percentage —
   is what should be reviewed, because the change cannot be undone for the window it runs in.
5. **The 303 rosterless unit rows are the next packet-joinability unit of work** (30.8 % of the unit
   stream), and the first step is one measurement: empty `sleeve_members` vs `skip_context` miss.
   They have different repairs and only one is in the emitter.
6. **Re-run F15 before arming any `mx_*` sleeve, every time — not once.** 56 bars of headroom on a
   terminal setting. The live book can now answer it continuously: `time_stop_unreachable` is on the
   packet.
7. **A general form worth keeping.** Three of this session's items were "the fix landed, the error
   path still points the wrong way" (AS 6), "the fix landed, its scope was one field" (D4 → OD-P2),
   and "the number landed, the contract behind it did not" (OD-P1). When a session hands off a
   partial repair, the cheapest next question is not *what is left to build* but *what does the
   system still tell the next reader*.

**Not mine and untouched:** the VPS, arming, tokens, gates, α, sleeve composition, the population
rule, ratifying the family, merging to `main`, `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml`.
