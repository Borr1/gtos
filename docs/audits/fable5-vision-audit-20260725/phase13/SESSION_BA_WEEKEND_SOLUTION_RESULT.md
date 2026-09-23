# Session BA — the redacted_account weekend-holding solution (wave 13, B1900–B1949)

Branch `phase13/weekend-solution`. Owner authority: Borhen 2026-07-30, *"run all… i do give
explicit approval."* Nothing armed; no config byte moved; no broker-capable script run; the
VPS untouched.

**Deliverables.** Owner package `phase13/BA_WEEKEND_POLICY_OWNER_PACKAGE.md` — read that one
if you read only one. Mechanism `src/components/ultimate_book/weekend_policy.py` +
`run_book.py --weekend-flat` (+3 dials), default-off. Evidence
`phase13/receipts/BA_WEEKEND_V1.json` (census / flat surface / embargo surface / identity /
book MC), the derived holiday list `phase13/receipts/BA_EARLY_CLOSE_DATES_V1.txt`, driver
`phase13/receipts/ba_weekend.py`, repair rows `phase13/receipts/REPAIR_QUEUE_BA.json`
(8 rows + 1 errata, appended to the shared sidecar), A/B `receipts/session_ba_ab/SESSION_BA_AB.md` — **0 bad → 0 bad, 0 regressed, 371 → 371 passing on a shared 15-file scope, +80 net new passing**, emitted via `pytest_failset.py receipt` (the tool fence) with the before side produced by copy-back.

---

## 1. Findings, in the order they matter

**1.1 The policy costs 42.8 % of the armed four, and two thirds of that is one sleeve.**
At the ratified rule (`RECORDED`, `CANDIDATE_BOOK_V1` V9 = 53, `B_balanced` α 0.10), the
Friday flatten under the conservative calendar reading is **−0.7753 R/day** against the four
sleeves' +1.8098. `sub_xvol_pullback` alone is **66.3 %** of the bill (+1.0215 → +0.5076) and
`crypto` is **28.3 %** (+0.2611 → +0.0419). At redacted_account's measured two-step rules the
four-sleeve book goes `p_pass` **0.7345 → 0.6282** and median calendar days to a payout
**494 → 689**. Flattening beats dropping at **three of the four cost bands** for every sleeve;
**the exception is `crypto` at the high band, where the flatten takes it to −0.0382** (+0.1815
under the market-close reading), which makes its funded-account membership a real question and
ties it to §1.2. No other sleeve turns negative at any band; `sub_xvol_pullback` loses half its
edge and still earns +0.4990 at the worst band.

**1.2 A quarter of the bill is decided by one support ticket, not by any code.** `BTCUSD`
gapped the weekend in **43.8 %** of its weeks in the archive and quoted straight through the
other 56.2 %, so "the weekend" is a property of *(symbol, week)* and not of the calendar. If
redacted_account's prohibition does not reach an instrument whose market never closes, the `crypto`
sleeve's bill goes from −0.2192 R/day to **−0.0005** — and the book's `p_pass` goes
**0.6282 → 0.7447**, one point ABOVE the do-nothing baseline, because the flatten also cuts
the book's daily sd by **9.3 %** on those same days (0.9620 → 0.8722). On the wider
`RECORDED` branch, which includes each fold's train days, it also removes the single worst
book day outright (−1.7799 → −1.4755, **17.1 %**); on the OOS-only days that worst day is the
same under both arms, so the sd is the whole of the effect there. Worth **+0.2197 R/day,
+11.7 pp of `p_pass`, 78 fewer days to a payout**. Filed as OD-BA-1 with the conservative
reading as the default until it is answered.

**1.3 My own mechanism had a compliance hole, and the identity check found it.** The claim
"every priced weekend-flat exit lands on the instant the live switch closes at" came back
**7 mismatched of 271 (2.6 %)** — all Christmas or New Year. The mechanism is general: **when
Friday is a market holiday the week's last close is Friday 00:00 broker, and a
Saturday-anchored deadline aims 20 hours into a market that already shut.** Under the
redacted_account rule that is a *breach*, not a cost: a position rides the weekend and every log
reads healthy. Two mitigations ship — a 13-date early-close list derived from the archive
(**residual 0 over all 271**) and a 24 h margin that needs no list and costs an extra
0.1167 R/day. Neither is durable; the durable fix is capturing the broker's own session
table, which this repo names as authority it does not have
(`broker_net_cost_engine.py:44-45`) and is now a queued row.

**1.4 The entry embargo is refuted as a repair.** The commission asked for it priced; it does
not pay. On three of four sleeves it makes the flatten worse. Where the combination looks
better (48 h: −0.4147 R/day against the flatten's −0.7753) it gets there by **halving the
number of book days**, so the daily mean is restored while median days-to-payout goes
689 → **832** and %/month falls to 0.236. `p_pass` is blind to speed, which is exactly how
that option reads free. Default 0, recommend 0. The `embargo_only` arms are published as
information and are **not legal** — an embargo without a flatten does not make an account
compliant.

**1.5 Zero margin is worse than one bar of margin on all four sleeves.** `m_inclusive`
(exit exactly at the weekly close) is dominated by `m0` everywhere: −0.34 vs −0.22 on
`crypto`, −0.59 vs −0.51 on `sub_xvol_pullback`. Holding the last four hours of the week
costs more than it earns *and* is charged the weekend rollover. The a-priori default (4 h,
one H4 bar) is therefore the cheaper cell as well as the only fillable one — chosen before
any result was read, which is what lets it be the headline.

**1.6 A cost delta is not a band quantity, and that is now measurable doctrine.** Option (a)'s
delta is identical to **eight decimal places** at flat / low / mid / high, because the flatten
changes gross R and swap while leaving the trade set — and therefore the spread charge —
untouched. Cells that drop trades (embargoes, wide margins) *do* vary by band. So the
ratified "admits at N of 3 bands" phrasing describes a LEVEL; publishing the band column for
a same-population delta is still right, and reading a spread across it as evidence would be
wrong.

**1.7 The two live servers agree on the weekend instant on every day of 2026.** Both resolve
to `America/New_York + 7 h`, so a policy measured on the FTMO bar archive is a policy about
the redacted_account account. Checked rather than assumed — `broker_clock.py` exists because a +3 h
assumption was wrong for three weeks of the sealed March window — and pinned by a test that
walks all 365 days.

**1.8 The weekly close is measured, not assumed.** Across the 18 non-crypto symbols the armed
four trade, **99.65–99.93 %** of calendar weeks contain exactly one weekend gap and the last
H4 bar before it opens at broker **Friday 20:00**, closing exactly at Saturday 00:00. That is
what makes the live `flatten_before_hours=4.0` default *identical* to the research `m0` cell
rather than merely analogous to it.

---

## 2. What was built

| file | what |
|---|---|
| `src/components/ultimate_book/weekend_policy.py` | new, pure (stdlib + `broker_clock`). `WeekendPolicy`, `OFF`, `next_weekend_boundary_utc`, `parse_weekend_flat`, `parse_early_close_dates`, `policy_from_args`. No MT5, no config read, no order. |
| `src/components/ultimate_book/book_owner.py` | `weekend_policy=` ctor arg (default `OFF` == byte-identical); `weekend_policy_preflight()`; `_weekend_flat_close()` in `_manage_engine` **before** the time stop, reusing the existing close-recording branch; `_weekend_entry_block()` in the intent loop as one more `skipped` reason. |
| `run_book.py` | `--weekend-flat`, `--weekend-flatten-before-hours`, `--weekend-entry-embargo-hours`, `--weekend-exempt`, `--weekend-early-close`. Parse refusal → exit 5; preflight failure → exit 5 + CRITICAL. |
| `tests/ultimate_book/test_ba_weekend_policy.py` | **80 tests**, all behavioural — including the entry side driven END TO END through the real `run_cycle` (reusing `test_book_owner.py`'s fake broker + recording engine), and a pin on the H8 interaction below. |

**R2 (H1) membership checked before editing**: every file touched is unbound. Working-tree
drift count is 2, both the known LFS pointers (CLAUDE.md §3's caveat); `git lfs checkout` was
not run on `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` and must not be.

**The policy cannot survive the gate being shut, and that is H8 one layer up.** The flatten runs
inside `_manage_engine`, which returns early with `live_broker_authority_false_observe_only` when
`ultimate_book_live_broker_authority` is false. So on a funded redacted_account account, shutting the
gate does not only leave positions open and unmanaged (H8) — it also stops the compliance close
from firing and the account holds through the weekend. Nothing inside the gate can fix that;
**flatten first, confirm flat, then shut the gate** now has one more reason behind it. Stated in
the module docstring and in the owner package.

**Degradation is deliberately asymmetric, and it is the most important design decision here.**
A dark clock makes `_weekend_entry_block` **refuse** (add no exposure you may not be able to
manage) and makes `_weekend_flat_close` **do nothing** (never invent a close on a guess). And
because a compliance guard that silently degrades to "no weekend is due" is a funded account
holding through one while every indicator reads normal, the failure is moved to **launch**:
armed policy + unresolvable server or missing `broker_clock` → `run_book.py` returns 5 and
notifies CRITICAL. `broker_clock.py` was absent from the live host at the 2026-07-26 export,
so this is not hypothetical; carrying it is a precondition of arming and a queued row.

---

## 3. Method notes a sceptic should check first

- **The baseline control runs before any cell is gated and FAILS the run if it breaks.** My
  re-simulator with no flat and no embargo must reproduce AD's `as_walked` row by row:
  181/181, 67/67, 88/88, 533/533, 0 mismatched. Every number in this session is a difference
  against that, so without the control the differences would be about my reimplementation.
- **Full-family gating, AD's convention.** Each arm gates the whole 32-sleeve family with only
  the target sleeve's records swapped, because gating one sleeve alone changes its BH rank and
  makes the q-value incomparable to the baseline it is measured against.
- **Multiplicity: no new declared looks.** Every arm is an exit-contract re-measurement of a
  sleeve already in `CANDIDATE_BOOK_V1`. The claim is a **cost** (an A/B of one sleeve against
  its own labelling), not an edge. **No cell admits anywhere in the surface** — 208 flat cells
  + 160 embargo cells, all REJECT. Every arm is ledgered.
- **The headline was chosen a priori.** `m0` is the headline for the stated reason (the
  tightest fillable cell on an H4 grid), not because it won. Reporting the surface's best cell
  as the cost would be AO's undeclared-median-cut error with a different variable — which is
  why option (c) in the package is labelled a 17-cell-per-sleeve selection and an upper bound.
- **The book MC's basis is published four ways** because the estate's MC convention (AI's
  `archive_daily`, Q's machinery) consumes the FULL day series including train days, and on
  `energy_agri` that convention and the gate **disagree on the sign** of the flatten's effect
  (gate OOS −0.024 R/day, full-series panel +0.397). `RECORDED_oos_only` restricts to the
  gate's own fold test days and is the branch quoted in the package; `ALL_ERAS`,
  `RECORDED` and `RECORDED_fwd_2025plus` are published beside it. `fwd_2025plus` is there for
  an arithmetic reason: `p_pass` is concave in the daily mean, so a delta measured at p 0.70
  is not the delta at AI's 0.93, and quoting only the full archive would overstate what
  compliance buys back.
- **Levels are archive-population.** They are comparable to each other and **not** to
  `phase8/receipts/BOOKS_MC_V1.json`'s cache-population 0.9331. Stamped everywhere.

---

## 4. What I got wrong

**4.1 The grid reading was wrong on the first run, and its own impossibility caught it.**
My first "market-close" deadline took *the next weekend close anywhere in the series*, which
for a continuously-quoted crypto week resolved to a gap years later and silently collapsed the
grid reading onto the calendar one. It printed as a result — `crypto`'s grid cell came out
**worse** than its calendar cell, which cannot happen when one rule is strictly weaker than
the other. That impossibility is what I noticed; the fix keys gapped weekends by the
Saturday's ISO week so the question becomes a lookup ("did THIS weekend gap?"). I killed the
in-flight sweep and re-ran it. Had the sign gone the other way I might not have looked.

**4.2 The early-close derivation's first version returned 497 dates including whole months.**
Bar absence cannot distinguish a market holiday from an archive coverage gap and my first
derivation did not try to: it emitted every date in every gap. Two filters fixed it (a 52 h
ceiling on the gap, and a 60 % quorum across the symbols that never print a weekend bar) —
187 candidates → 13 dates, all recognisable market holidays.

**4.3 And the quorum's denominator was wrong, which the residual check caught.** I first took
the quorum over *all* voting symbols; half the metals cross-pairs' archives begin in late
2020, so 2020-12-25 — one of the seven exits the whole derivation exists to catch — failed
quorum and the residual went 0 → 7. The denominator has to be the symbols whose archive
reaches that week. **The check that caught both 4.2 and 4.3 is the same one: "with the list,
how many exits would the live rule close LATER than the replay did?" It must be zero, and it
was the only thing that noticed.**

**4.4 A pathological holiday list could walk the boundary into the past.** My guard tested the
*current* candidate rather than the *result* of the step, so a list naming three weeks of
consecutive holidays returned a boundary before `now` — breaking the function's one invariant
and making `flatten_due` compare against a window that had already closed. A parametrised test
found it, and the invariant is now asserted at seven offsets across four lists.

**4.5 A swapped argument pair would have been silent.** `_weekend_flat_close(ee, sym, sleeve)`
takes two interchangeable strings, and I wrote the call site with them reversed. A swap does
not raise: the policy would govern the *symbol* name, which is in no selection, so the guard
would never fire. There is now a test that passes a symbol which is also a valid sleeve name
and asserts nothing closes.

**4.6 The artifact briefly claimed a 208-cell gate sweep took 1.4 seconds**, because a single
`seconds_total` key was overwritten by whichever stage ran last. Per-stage now.

**4.7 My first end-to-end entry test passed for the wrong reason and its control caught it.**
`_FakeMT5` anchors its forming bar on the real `now`, so handing `run_cycle` an arbitrary
simulated `now_utc` put the decision bar weeks in the past and the **entry-lateness** guard
dropped it — which looks exactly like the weekend guard working. The control ("with the policy
OFF, does this same cycle still place?") failed, which is how I found it; the fix moves the
feed's anchor with the clock. It also produced a real improvement: `_weekend_entry_block` now
takes the **cycle's** `now` rather than reading the wall clock inside the loop, so the entry
decision is made on the same clock as the decision bar it is about.

**4.8 One claim in the module docstring was wrong and is corrected.** I first wrote that
`m_inclusive` bounds "what the policy could be worth to an executor who cannot exist". A live
book *can* close at 23:55 with a market order; what it cannot do is exit at a bar close on a
grid. The right statement — and it is stronger — is that `m_inclusive` is dominated by `m0` on
all four sleeves anyway (§1.5), so the unfillable question never arises.

---

## 5. Handoff to the orchestrator

1. **Nothing to arm.** The switch is off and the package is Borhen's. OD-BA-0 (capture the two
   redacted_account help-centre pages) is a precondition of arming anything here; OD-BA-1 (does the
   rule reach a 24/7 instrument?) is worth 28 % of the bill for one support ticket.
2. **BA-H1 — carry `src/utils/broker_clock.py` to the VPS before this policy is ever armed.**
   The worker refuses to start without it, by design. With the policy off, nothing reads it, so
   the carry is not a landing blocker.
3. **BA-H2 — the broker session table.** `symbol_info_session_trade` capture retires the
   operator-maintained holiday list permanently and would also let the session-anchored
   sleeves stop inferring their own boundaries.
4. **BA-H3 — the armed FOUR still has no cache-population MC.** `BOOKS_MC_V1.json` covers the
   armed three on the recost caches; `sub_mid_dn_revert` was added 2026-07-30 and every
   four-sleeve figure in this session is archive-population. Someone should close that.
5. **The shared sidecar got 8 rows** (`REPAIR_QUEUE_BA.json` is the authoritative copy) and the
   trial ledger got every gated arm, including the REJECTs. Union-merge as usual.
6. **`--weekend-early-close` accepts a file path**, so the list can live in the repo and be
   diffed rather than hidden in a supervisor command line. The shipped one is historical; an
   armed policy needs it extended forward or the 24 h margin instead.
