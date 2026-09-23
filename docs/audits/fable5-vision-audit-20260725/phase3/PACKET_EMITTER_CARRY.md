# Session P — the forward shadow, as a reviewable carry

**Stage 3, brought forward. Branch `phase3/packet-emitter` off `main` @ `df2baf060`. Blocks B200–B219.**

Reproduce the measurements: `python3 scripts/ultimate_book_packet_silence_alarm.py --packets <export> --expect-namespace operator_profile --expect-namespace redacted_account_live_bee34003`
Tests: `pytest tests/ultimate_book/test_packet_emitter_hardening.py tests/ultimate_book/test_packet_silence_alarm.py -q` → 46 passed.
A/B: `tests/ultimate_book` **60 bad → 60 bad by failure set, 0 regressed, 481 → 515 passing.**

---

## 0. The answer

**The emitter's problem was never that fields were missing. It was that the fields it already had
were unpopulated, unlabelled, or unjoinable — and that its highest-volume event type spends 79 % of
the stream re-emitting a timestamp.**

Three of the numbers I was commissioned with are wrong in ways that change the work, and one of
them closes the question Session N left open. All re-derived from the 99,112-packet live export
(`vps-export-20260725`, 2026-06-18T17:06:50Z … 2026-07-25T22:05:28Z, both namespaces).

**The headline for OD-3: `placement_observed_at_utc` is not biased against fill time.** The prompt
asked me to treat a poll-interval bias as outranking everything else on my list. Measured, the bias
runs the other way and is three orders of magnitude too small to matter:

| | measured | n |
|---|---:|---:|
| `placement_observed_at_utc` − `broker_fill_time_utc` | **−1.23 s** (median) | 93 closes, 132 placements |
| — sign | **earlier** than fill on 90/93 and 126/132 | |
| `created_at_utc` − `broker_exit_time_utc` | **+26.8 s** (median), p95 +60.4 s, max +24.1 min | 90 |
| **net bias of the 148-row estimator** | **≈ +28 s, over-stating** | |

The entry side is a local send instant ~1.2 s before the broker's fill. **The biased side is the
exit**, and it is one poll interval at the measured 60 s cadence.

### But "therefore admissible" does not follow, and an adversarial pass is what showed it

My first draft of this section concluded *"N can use the 148 holds."* A refuter tasked with
destroying that conclusion **refuted it**, and re-measuring independently confirmed all three of its
objections. The corrected statement:

> The 148 holds are usable **for sleeve-median comparisons against 10–320 h break-evens**, where a
> 28 s offset is 0.3 % of the median. They are **not** admissible as a uniform-bias-corrected
> series.

Three reasons, each measured here:

1. **The +28 s correction is unmeasured on 39 % of the corpus, and the gap is a calendar block, not
   a random half.** Of the 57 estimator rows closing before 2026-06-24, exactly **1** carries
   `broker_exit_time_utc` (2 %); from 06-24 onward it is **89 of 91** (98 %). The emitter changed
   what it wrote at that boundary. The exit-lag bias across the first 39 % of the corpus rests on
   **n = 1**.
2. **The lag is three populations, not one.** Stratified by `close_action`:

   | `close_action` | n | median lag | max |
   |---|---:|---:|---:|
   | `broker_closed` | 82 | **+27.35 s** | +62.2 s |
   | `vnext_time_stop` | 6 | **−0.03 s** | +0.5 s |
   | `broker_closed_absent_on_reconcile` | 2 | **+761.8 s** | +1,446.5 s |

   Applying +28 s uniformly *adds* error to book-initiated closes and is ~27× too small for the two
   reconcile rows. And the 1,446 s row is not a cadence failure — that ticket had 72
   `position_managed` packets spanning its exit with a max gap of 65 s. The loop polled ~24 times
   and did not detect the close. **There is a second failure mode unrelated to poll cadence.**
3. **It fails in the left tail.** The shortest broker-true hold in the corpus is **35.0 s**, recorded
   as 61.6 s — a **+76 % overstatement**. 8 of the 89 checkable rows carry >10 % relative error.
   `mx_nzdjpy_d1_donchian_20_breakout`, median hold 317 s, has **0 of 3** rows with any broker truth.

**And the error term I certified as harmless is 128× smaller than the one still open.** The three
anchors give medians 2.2563 h / 1.8783 h / 1.2583 h — the *estimator choice* moves the central
estimate by **0.998 h = 44.2 %**, against the 28 s (0.0078 h) bias. Proving the small term small
says nothing about admissibility while the large term is unresolved. **Which anchor N uses is the
question that should be settled first.**

Two corrections to how those 148 were derived, which N should carry:

- **`closed_at_utc` is not a broker fact — it is the packet's own emission instant.** My first draft
  said "byte-identical to `created_at_utc` on all 98 rows (max difference −0.0 s)". **That was
  wrong, and it was a formatting artifact of my own probe** (`.1f` on a sub-second value). Measured
  properly: `closed_at_utc` − `created_at_utc` is **strictly later on 98 of 98**, median
  **+0.0457 s**, max **+1.306 s**. Exactly zero on **0** rows. The conclusion is unchanged — it is a
  poll observation, not a broker timestamp — but the specific was false.
- **The 148 figure uses the packet emission time as the exit.** Only **98** of 151 closes carry
  `closed_at_utc` and only **90** carry `broker_exit_time_utc`. Medians differ accordingly: 2.2565 h
  (emission), 1.8783 h (`closed_at_utc`), **1.2603 h (broker truth)**. The broker-truth median is
  **44 % lower** than the number in my prompt. If holding time is going to decide five sleeves,
  which of those three medians is used is not a rounding question.

**And there is no censoring.** All 150 distinct ticket hashes in the window have a `position_closed`.
Max observed hold is 90 h against a 37-day window, so the distribution is not truncated — a small
piece of good news for anyone using it as evidence.

---

## 1. Three claims in my prompt that are wrong

Kept per `WAVE_3_WORKING_AGREEMENT` §2: a prompt that turns out to be wrong is a finding.

### 1.1 "`spread_r` is absent from every one of the 99,112 packets"

**It is not absent. It is present on all 99,112 and null on all 99,112.** The distinction is the
whole job. `runtime_learning_packet.py:411` has always written
`"spread_r": outcome_clean.get("spread_r")` — the field was reserved and nobody ever populated it.

Worse, the number already existed. `_spread_cost_screen` (`book_owner.py:4083`) computes
`spread_r = (ask - bid) / rd` for **every** leg it evaluates, and then — on the failing legs only —
formats it into a refusal **string**:

```
cost_screen_spread_r:0.142>0.100 (spread 0.0043 vs fx_jpy stop 0.0303)
```

So the only quantitative spread evidence in the entire live corpus is a regex-parseable substring
inside `skip_reason`, present exclusively on the legs that failed. That is a spread record built
from a refusal log — the passing legs are most of the distribution and their absence reads as "no
spread" rather than "spread was fine". Stage 3 named `spread_r` first and it was right to, but the
work is *populate*, not *add*.

### 1.2 "No other event type carries an entry timestamp at all"

`position_managed` carries `broker_fill_time_utc` on **40,948 of 78,687** packets,
`placement_observed_at_utc` on 71,969, and `policy_clock_entry_time_utc` on 44,399.
`position_adopted` carries fill time on 129 of 181. Entry time is one of the better-covered fields
in the stream.

### 1.3 "`position_managed` … records almost nothing"

True of its nested `outcome` block, false of the packet. At top level `position_managed` carries
`broker_entry_commission`/`broker_entry_swap` on 27,739 rows and the entry timestamps above. The
event's problem is not that it records little — it is that it records the *same thing* 91 times per
position, which is §2.

---

## 1b. The `_utc` hazard, in its most dangerous form: the agreement is manufactured

**`broker_fill_time_utc` can be silently moved by up to ±6 whole hours, and no packet has ever said
so.**

`book_owner._iso_from_deal_time_near_reference` (`:2818-2852`) takes the broker deal time and
searches ±6 hours in whole-hour steps for the shift that minimises distance to a **local** reference
instant, accepting it if the result lands within 10 minutes:

```python
for hours in range(-int(max_shift_hours), int(max_shift_hours) + 1):
    candidate = dt - timedelta(hours=hours)
    ...
if best_shift and best_distance <= int(tolerance_minutes) * 60:
    return best.isoformat(), best_shift * 3600
```

The offset **is** computed and **is** stored — `execution["broker_fill_time_alignment_offset_seconds"]`
at `:3055-3056`. It is then read by nobody. Repo-wide it has exactly one writer and zero readers,
and it appears in **0 of the 99,112 live packets**.

So for every packet in the corpus, **it is impossible to distinguish a raw broker timestamp from one
that was moved six hours to agree with our clock.** This matters more than an ordinary missing field
because of what it does to the evidence in §0: the argument that `broker_fill_time_utc` is genuinely
UTC rests on it agreeing with a true-UTC local instant to 1.2 s. If this function fired, **that
agreement is partly manufactured by the field's own producer.**

The bias conclusion in §0 survives — the snap moves whole hours and cannot touch a 1.2 s
sub-second residual, so the *magnitude* is unaffected. What does not survive is the provenance
label. A snapped fill time is not a measurement; it is a measurement transferred onto our clock.

**Fixed in this carry.** `broker_fill_time_alignment_offset_seconds` is added to the packet
allowlist, and `packet_economics` downgrades `entry_provenance` from `measured` to `transferred`
whenever it fired, publishing the offset alongside. That converts an invisible adjustment into a
labelled one. *Found by a refuter attacking this session's own bias claim, not by me.*

---

## 2. The finding that reframes Stage 3's "one packet per intent"

**78,687 `position_managed` packets describe 148 positions.** Median 91 packets per position;
**maximum 5,339 for a single position.**

Diffing consecutive packets for that busiest position, across all 5,338 transitions:

| field | transitions on which it changed |
|---|---:|
| `management_checked_at_utc`, `policy_clock_checked_at_utc`, `policy_clock_diagnostic`, `created_at_utc`, `packet_hash_sha256`, `outcome` | **5,338 / 5,338** |
| `policy_clock_bars_until_due`, `policy_clock_elapsed_m15_bars` | 161 |
| `policy_clock_entry_time_utc` | 5 |
| everything economically meaningful (`broker_position_sl/tp`, commission, swap, realized P&L) | **1** |

**5,339 packets to record 161 state changes.** Emit-on-change would drop **75,372 packets, 76.05 %
of the entire stream**. The corpus is **826 MB uncompressed over 37 days**.

**Corrected from 76.9 % / "no information loss", and the error is instructive.** My first count was
the number of *globally distinct* states (2,467 of 78,687 = 3.14 %). Emit-on-change is a
**run-length** operation, not a set operation: a state that recurs after changing away (A→B→A) must
be re-emitted. Counting the actual emissions per ticket in time order gives **3,315**, not 2,467 —
the set count swallowed **848 state re-visits**. Those re-visits are not noise; they are protection
and target *oscillations*, which is exactly what a reader would want to see. So "no information
loss" was false as stated, and the honest figure is **76.05 %**. Found by a refuter; the attack it
was pointed at (that the excluded nested `outcome` block hid information) **failed** — restoring all
27 substantive outcome-only fields moves the count by 2 packets.

I have **not** landed emit-on-change. It changes what the live book records, and the right form of
it needs a forced heartbeat so that "nothing changed" stays distinguishable from "the book died" —
which is what the silence alarm now provides the calibration for. It is written up as **OD-P1**
below because it is Borhen's call, not mine: it is cheap, it is large, and it is irreversible for
the window in which it runs.

Related cardinality, for the record: `unit_admitted` is 440 rows over **65** distinct
`ultimate_book_intent_id`. That collapse is not duplication — it is §3.

---

## 3. The join key degenerates, and there is a booby trap under it

**`unit_admitted` carries `symbol`, `sleeve`, `direction` and `candidate_id` on exactly 83 of 440
rows** — precisely the rows where the admission unit resolved to a single member:

| `admission_unit_member_count` | rows | join key present |
|---|---:|---|
| 1 | 83 | **yes** |
| 2 / 3 / 4 | 50 / 5 / 1 | no |
| `None` | 301 | no |

The cause is `book_owner.py:1324`:

```python
single_member = admission_members[0] if len(admission_members) == 1 else {}
```

Units bucket by `(decision_day, cluster)`, so anything spanning two sleeves of a cluster — `metals`,
`jpy`, `index` — or one sleeve on two symbols yields `{}`. That is the common case, not the edge
case. `unit_skipped` is worse: 14,627 of 14,638 rows carry `symbol`, but only **306** carry
`direction`.

Because `ultimate_book_intent_id` is a hash over `(namespace, event_type, sleeve, symbol,
direction, decision_bar_iso, decision_day)`, nulling four of those seven collapses 440 rows onto 65
ids. **The directions are not lost** — they survive in `admission_unit_members[].direction` — but
nothing at top level can be joined on.

**The booby trap.** `build_runtime_learning_packet:227` falls back to
`_first_unit_sleeve(unit)`, which would attribute a multi-sleeve unit wholesale to
`sleeve_members[0]` — the *alphabetically first* member. That fallback is currently **inert**, and
for an accidental reason:

```python
members = unit.get("sleeve_members")
if isinstance(members, list) and members:   # asdict(SizedUnit) yields a TUPLE
```

`SizedUnit.sleeve_members` is a tuple (`admission.py:1117`), `dataclasses.asdict` preserves tuples,
and `isinstance(tuple, list)` is False. So the fallback silently returns `None` — which is why
`sleeve` is null on all 357 multi/unknown-member rows rather than wrong.

**Widening that `isinstance` to `(list, tuple)` — the obvious "fix" — would silently begin
attributing every multi-sleeve metals unit to `metals_core`**, skewing every per-sleeve rollup
keyed on `packet["sleeve"]`, which is exactly what `scripts/w7_packet_forensics.py:100` does. I
have deliberately **not** touched it. The correct repair is to emit the members, not to guess a
representative, and it is written up as **OD-P2**.

*(I initially read this as a mainline-vs-VPS divergence, because the mainline builder returns
`asia_pdl_fade` for the same input. It does not diverge — I had round-tripped the unit through JSON,
which turns the tuple into a list. Recorded in §8.)*

---

## 4. What the carry contains

Five files. **Order matters**, and the first three are inert until the fourth lands.

| # | file | new? | why this position |
|---|---|---|---|
| 1 | `src/utils/broker_clock.py` | **absent on VPS** | Needed for broker-clock night counts. Optional — see below. |
| 2 | `src/components/ultimate_book/runtime_learning_packet.py` | modified | Adds the `economics` passthrough, `packet_rejected`, and the marker builder. No new imports. |
| 3 | `src/components/ultimate_book/packet_economics.py` | **new** | Imports only `broker_clock`, optionally. |
| 4 | `src/components/ultimate_book/packet_guard.py` | **new** | Imports `runtime_learning_packet` (#2). |
| 5 | `src/components/ultimate_book/book_owner.py` | modified | Imports #3 and #4. **Nothing changes until this lands.** |

Plus `scripts/ultimate_book_packet_silence_alarm.py` — standalone, read-only, no live coupling,
can land any time or never.

### The dependency that would have broken the live book

**`src/utils/broker_clock.py` does not exist on the VPS.** `20_src/utils/` has no such file and the
VPS `governor_state.py` predates the clock work entirely. A top-level
`from ...utils.broker_clock import ...` in `packet_economics.py` would raise at module load,
propagate through `book_owner.py`, and **break the live book's import** — the worst outcome this
carry could have had.

The import is therefore optional by construction (`packet_economics.py:41-68`). Without it, the
night count degrades to `rollover_nights: None` with `error: broker_clock_module_unavailable`, and
every other field still works. That makes the carry **order-independent**: file 1 can land after
file 5, or never, and nothing breaks — it only postpones the night count. Guarded by
`test_the_carry_survives_a_host_with_no_broker_clock_module`.

---

## 5. Deployment safety — demonstrated, not asserted

Session I's proof shape, re-derived. All four are tests, not claims.

### A — the carry imports nothing that can reach a broker. **PROVEN.**

`test_carry_modules_import_nothing_that_can_reach_a_broker` walks the transitive import graph of
both new modules and asserts none of `MetaTrader5`, `src.mt5`, `src.components.execution`,
`src.components.orchestrator`, `order_router`, `book_engine`, `broker_net_cost_engine` is reachable.
This matters because `create_mt5("live")` **succeeds** on macOS — the ImportError only surfaces on
`.connect()` — so an import graph is the only construction-time evidence worth anything.

### B — inert on 79 % of the stream under current config. **PROVEN.**

`test_economics_is_a_noop_for_every_event_type_that_carries_no_position`: the economics block
returns `None`, not an empty shell, for every cycle/skip/shadow outcome. `cycle_no_candidates`,
`unit_skipped`, `unit_shadow` and `unit_admitted` packets do not grow a byte. Placement gates are
false and stay false; nothing here reads or writes one.

### C — the failure mode is refusal, not exception. **PROVEN.**

`test_the_failure_mode_is_refusal_not_exception` and `test_guard_never_raises_on_any_input`
(9 parametrised hostile inputs including `None`, non-mappings, and un-JSON-able objects). An
unresolvable broker clock yields a labelled refusal and **never a guessed offset**.

### D — backward compatibility. **MEASURED.**

**All 99,112 existing packets validate unchanged against the modified validator.** This is the
regression floor and it is checked directly against the export, not inferred.

`SCHEMA_VERSION` is deliberately **not** bumped. Bumping it would make every one of those 99,112
packets fail `schema_version_mismatch` on read — destroying the only live evidence the programme
has in order to record an addition. The packet shape has not changed; it has grown an optional key.
So the `economics` block carries **its own** `contract_version`, and a reader keys on that.

---

## 6. What the carry makes recoverable — and what it does not

The bar I was given: *could a future session compute a cost-true, holding-time-aware P&L for every
intent from packets alone, and know which numbers are measured versus modelled?*

**Not yet, and here is precisely the gap.**

### Now recoverable, that was not

| | before | after |
|---|---|---|
| holding time | derivable on 98/151 closes, silently mixing broker and poll instants | `economics.holding` with `entry_provenance`/`exit_provenance`/`holding_provenance` per row, and the entry and exit observation lags **published** rather than hidden |
| carry nights | nowhere | `rollover_nights` on the **broker** wall clock, with the individual `crossings` emitted alongside the total |
| spread | a regex substring inside `skip_reason`, failing legs only | `spread_r` populated on every evaluated leg, pass or fail, labelled `measured` |
| realized cost | five raw broker fields, no completeness signal | `economics.cost` with `realized_components_missing` derived **by set-difference**, and no total at all unless every component is present |
| governor | only `available_gross_risk_pct` (= cap − open_risk) | raw `equity`, `open_risk_pct`, `gross_open_risk_cap_pct`, `day_anchor_equity`, `high_water`, plus the derived verdict for A/B against a recomputation |
| a refused packet | vanished from the log; recorded only in the cycle summary | `packet_rejected` marker **in the main log** + full body in a quarantine sidecar |

**Why the governor block is the one that kills a self-fulfilling result.** Today the packet carries
the *difference* `cap − open_risk` and neither operand. And the cap is not a constant you could look
up: `book_engine.py:587-605` tightens it dynamically against the daily-loss room. So
`available_gross_risk_pct` alone is uninterpretable and utilization is unrecoverable — which is
exactly why Session L's finding (6,355 units, **zero shed**, max utilization 0.4654) could not be
validated against anything. Emitting the operands is what makes the shed checkable. Likewise
`day_anchor_equity`: `GovernorState` consumes it to compute `realized_today_pct` and then discards
it, so checking the daily-loss band today means re-deriving it from the number under test.

### Still NOT recoverable — the honest list

1. **Modelled cost is a passthrough with no producer.** `economics.cost.modelled_cost_r` reads
   `outcome["modelled_cost_r"]`, and **nothing writes that key.** The authoritative pretrade model
   lives in `broker_net_cost_engine.py:287-308` and reaches `trade_params` as
   `gtos_vnext_pretrade_cost_model`, but `_runtime_learning_trade_context` copies a fixed 25-key
   allowlist that does not include it. Wiring it is a small change to that allowlist — **which I did
   not make**, because `broker_net_cost_engine.py` is R2-bound (H1) and I wanted the boundary of
   this carry to be unambiguous. Until it is wired, the modelled-vs-realized *difference* — the
   thing Stage 3's "result side repaired" is actually about — is still not computable from packets.
   **This is the largest remaining gap and it is cheap.**
2. **A8 features cannot be emitted, and the emitter is not why.** `ConfluenceResult` — score, four
   booleans, and a reason string — is discarded at `admission.py:1084`, and intents dropped by the
   gate leave *no skip row at all*. But the gate is also unarmed (config default `False`,
   `bridge.py:98`) **and the five features are never populated by the metals generators**, so
   `_metals_confluence_pass` returns `None` → admit-as-today. Emitting them today would emit five
   nulls. The block accepts a `features` dict and is ready; the upstream is the blocker.
3. **Nothing retrofits the 99,112.** Every field above starts at the first packet after deployment.
   The existing corpus keeps exactly the holding times §0 describes, and no spread, no governor
   state, and no carry nights — ever. **That is the cost of every day this is not deployed**, and it
   is why Stage 3 was worth bringing forward.
4. **`_history_time_to_iso` assumes UTC for a naive broker timestamp** (`execution.py:2027-2039`).
   It happens to be correct for this data — `broker_fill_time_utc` agrees with a true-UTC local
   instant to 1.2 s, which is positive evidence the conversion is right *on this path* — but the
   function would silently mislabel a naive broker-epoch datetime, and it is one caller away from
   the H-hazard. I did not touch it; it is outside this carry and it deserves its own look.

---

## 7. Owner decisions

**OD-P1 — emit-on-change for `position_managed`?** Drops **76.05 %** of the stream (75,372 of
99,112 packets, ~630 MB per 37 days). Not lossless: it collapses 848 state oscillations, which are
themselves signal. Needs a forced heartbeat so "unchanged" stays distinguishable from "dead"; the
silence alarm supplies the calibration. Irreversible for the window in which it runs — packets not
emitted are not recoverable. My recommendation: **yes, with a 15-minute heartbeat**, matched to the
measured M15 idle pattern — but re-costed at 76.05 %, and it is a compression, not a free lunch.

**OD-P2 — repair the join key on multi-member units?** Requires touching `book_owner.py:1324` to
emit per-member rows or a member-derived key instead of `{}`. Not bound by R2. The risk is the
booby trap in §3: the naive version of this change starts mis-attributing multi-sleeve units to the
alphabetically-first sleeve. My recommendation: **yes, but as its own scoped change with its own
A/B**, not folded into this carry.

**OD-P3 — wire `modelled_cost_r`?** §6 item 1. Small, and it is what makes modelled-vs-realized
computable. Touches only `_runtime_learning_trade_context`'s allowlist in `book_owner.py`, which is
**not** R2-bound — I flagged `broker_net_cost_engine.py` above only as the *source* of the value,
which does not need editing. My recommendation: **yes**, and it should go before OD-P1.

---

## 8. Claims I made during this session and then withdrew

1. **"Mainline and the VPS emitter diverge on sleeve attribution."** They do not. Mainline's builder
   returns `asia_pdl_fade` where the live packet has `None`, which looked like a fork — but I had
   fed it a `unit` round-tripped through JSON, which converts the tuple to a list and flips the
   `isinstance` check. The VPS and mainline emitters differ **only** by the convergence-advisory
   additions. The real finding underneath was better than the false one: §3's inert booby trap.
2. **"The H1 check reports a second drifted path — the real signal."** It did, on arrival: both
   contract-bound sleeve ledgers were 131/132-byte LFS pointers, re-pointerised at 21:30 on
   2026-07-28. Not drift. `git lfs checkout` restored both and the check returned to the known
   `drifted=1` false alarm. Worth recording because the working agreement pre-fixed this trap on
   2026-07-27 and **it re-fired the next day**, so it is recurrent, not one-off.
3. **The first silence alarm assumed a 60 s grid and excused weekends on the broker clock.** Both
   wrong. It reported 46 % coverage and **1,633 breaches** — a tool that cries wolf 1,633 times is
   worse than no tool. The book emits on all seven broker weekdays (Sat 7,193 packets, Sun 5,900),
   so there is no weekend to excuse, and the gap distribution is not a grid (p50 0.0 s, p90 60.4 s,
   p99 909.6 s — a normal M15 idle). Rebuilt against the measured distribution at a 1800 s
   threshold: **48 alerts across the live window instead of 3,187.** The set-difference framing was
   kept only where it genuinely applies — the namespace roster, where a dead book emits nothing and
   therefore cannot appear in any observed set.
4. **"The guard never raises."** It could, at construction: `Path(writer.path)` on a duck-typed
   writer without `.path`. Caught by an existing test, not by me. "Never raises" is not a property
   of `append_many` alone.
5. **`test_nights_are_counted_on_the_broker_clock_not_utc` was wrong on first write.** I picked a
   22:00→23:00 UTC window believing it straddled the broker midnight; in summer that instant is
   21:00 UTC, so the whole window sat *after* it. The code was right and my arithmetic was not.
6. **"`closed_at_utc` is byte-identical to `created_at_utc`, max difference −0.0 s."** False, and it
   was my own probe's `.1f` format string hiding a sub-second value. It is strictly *later* on
   **98 of 98** rows, median +0.0457 s, max +1.306 s; exactly zero on none of them. The conclusion
   the claim supported — that it is a poll observation rather than a broker fact — is unaffected,
   which is precisely why the false specific survived my own reading of it. Caught by a refuter.
7. **"The 148 holds are admissible."** Refuted, by a refuter I commissioned to destroy it, and
   confirmed refuted by my own re-measurement. Corrected in §0: usable for sleeve-median
   comparisons, not as a uniform-bias-corrected series. I had proved the *small* error term small
   (28 s) while the *large* one — a 44.2 % swing between three defensible anchors, 128× larger —
   sat unresolved two paragraphs below in the same document. **The strongest form of this failure is
   that I had already written the 44 % finding down myself and still drew the wrong conclusion from
   it.**
8. **I built the false-evidence class this carry exists to prevent, and shipped it for four
   commits.** `management_checked_at_utc` was in the exit-source fallback list. `book_owner` sets
   that field unconditionally immediately before the economics block is built, and it is on 77,942
   of 78,687 `position_managed` rows — so `exit_at` was non-None for **every** management event.
   Replayed over the live corpus: **71,969 still-open positions published as completed holds**,
   each with a `holding_seconds` of elapsed-so-far and `rollover_nights` counted to a fabricated
   exit. `position_open_at_emit` was `false` **by construction** — it was `true` **0 times in
   72,117 blocks**. Mean holding time over the block read **20.85 h against a true 8.37 h: a 2.49×
   overstatement**, at a 476:1 ratio of fabricated to real samples, feeding the single number OD-3
   turns on. Fixed: `management_checked_at_utc` is no longer an exit source, open positions report
   `position_open_at_emit: true` with a **right-censored** `elapsed_seconds_at_emit` under its own
   key, and the 88 genuine mid-management closes are preserved. After the fix: **293 completed
   holds, mean 8.27 h.** Found by a refuter. I wrote three separate warnings about absence-vs-zero
   into this module's own docstrings while this sat in it.
9. **"Deployment-safe" — I introduced a live regression that a logging switch could trigger.**
   Moving the guard construction inline dropped the `writer is None` early return.
   `packet_enabled: true` + `packet_log_enabled: false` is a supported config that leaves the writer
   `None`; the guard then failed every packet as `unrecorded`, feeding `packet_write_error_count`
   into `ai_companion/supervisor.py:517 → :734-741`, which raises an integrity issue and issues
   **`pause_new_entries` for every namespace**. A logging switch would have stopped both books.
   Restored, and guarded by `test_a_logging_switch_cannot_stop_the_books`.
10. **"76.9 % of the stream, with no information loss."** Both halves wrong. I counted *globally
   distinct* states; emit-on-change is **run-length**, so a state recurring after changing away
   must be re-emitted. Real figure **76.05 %**, and the 848 swallowed re-visits are protection and
   target *oscillations* — signal, not noise. The attack aimed at the nested `outcome` block failed
   (restoring all 27 substantive fields moves it by 2 packets); the flaw was methodological.
11. **"Nothing in this carry needed to touch the entry-timestamp path."** False: §1b. The most
   consequential single change in this session — publishing the hour-snap offset — exists only
   because a refuter went looking for a way the timebase agreement could be circular.

---

## 9. What this session did **not** do

- **It did not deploy anything.** This is a carry: a reviewable diff plus
  `PACKET_EMITTER_VPS_RUNBOOK.md`. Borhen executes anything touching the VPS.
- **It did not land emit-on-change, the join-key repair, or the `modelled_cost_r` wiring.** All
  three are OD-P1/P2/P3, with recommendations and consequences quantified.
- **It did not run the full suite.** Scoped to `tests/ultimate_book` (575 tests) because two other
  sessions were live and memory is the binding constraint on this machine. The A/B is by failure
  set over that scope and it is committed. **No repo-wide "no regressions" claim is made here.**
- **It did not read a sealed window.** March remains outcome-unread.
- **It did not touch `_first_unit_sleeve`,** deliberately. See §3.
