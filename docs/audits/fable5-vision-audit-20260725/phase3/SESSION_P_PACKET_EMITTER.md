# Session P — Forward shadow that can bear weight

**Stage 3, brought forward.** Worktree `worktrees/wave3-packet-emitter-20260727`, branch
`phase3/packet-emitter`, from `main`. **Your block range is B200–B219.**

**Read `../WAVE_3_WORKING_AGREEMENT.md` first.**

---

## Why this is running now instead of after OD-3

The plan sequences Stage 3 after the OD-3 decision. It is being brought forward for one reason, and
you should know it because it tells you what matters:

**Session N re-costed the W7 validation and found that its dominant remaining uncertainty is holding
time.** Book of record, FTMO, 2.0 % dial: `P(pass)` **0.951** and 1.97 %/month at one night of
average carry, versus **0.450** and 0.13 %/month if every trade ran to its horizon. N's words: *"The
entire distance between those is holding time, and nothing in the tree records it — which makes exit
timestamps the cheapest thing that would sharpen OD-3."*

Every day the emitter is not hardened is a day of shadow data that cannot bear weight. Stage 3 is
where, in the third review's phrase, *calendar physics begins* — shadow scoring **starts earning only
once this lands**. Bringing it forward costs nothing that OD-3 needs and buys real calendar.

## What is measured about the current emitter — start here, then attack it

I probed the live export before commissioning you. **Re-derive all of this; do not inherit it.**

Source, **outside the repo** (which is why prior sessions did not find it):

```
/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/
    ultimate_book_runtime_learning_packets.jsonl.gz
```

**99,112 packets** from the live window:

| event_type | count |
|---|---:|
| `position_managed` | 78,687 |
| `unit_skipped` | 14,638 |
| `cycle_no_candidates` | 4,325 |
| `unit_shadow` | 545 |
| `unit_admitted` | 440 |
| `position_adopted` | 181 |
| `position_closed` | **151** |
| `unit_placed` | 145 |

What I found [MEASURED, re-verify]:

- **`spread_r` is absent from every one of the 99,112 packets.** Stage 3 names it first for a reason.
- **Holding time IS derivable, but only from `position_closed`** — its `outcome` block carries both
  `placement_observed_at_utc` and `closed_at_utc`. **148 of 151 derive**; the other 3 lack
  `placement_observed_at_utc`. Median 2.26 h, p75 9.40 h, max 90.00 h, and only **16 of 148** exceed
  24 h.
- **No other event type carries an entry timestamp at all.** So holding time exists for 151 closes
  out of 99,112 packets, and for nothing that did not close inside the window.
- `position_managed` — 79 % of all packets — carries an `outcome` of only
  `{action, placement_status, sleeve, source_completeness_status}`. It is the highest-volume event
  and it records almost nothing.

**Session N is auditing that same probe from the backward direction** — whether those 148 holds are
admissible as evidence for the re-cost. Yours is the forward mechanism: making holding time, cost,
and governor state first-class for every future packet. Do not duplicate N's analysis. **Do read what
N concludes** — if it finds `placement_observed_at_utc` is biased against fill time by a poll
interval, then fixing that is yours and it matters more than anything else on your list.

## What Stage 3 specifies

> VPS packet-emitter hardening in one carry (`spread_r`, direction on `unit_admitted`, A8 features,
> raw governor equity/open-risk — kills the self-fulfilling headroom recovery, makes the shed
> validatable; **one packet per intent**), emit-time schema validation, silence alarm,
> lifecycle-capture result side repaired (the named Phase-6 cost source currently records intent
> only).

Three of those deserve emphasis:

- **"Kills the self-fulfilling headroom recovery."** The governor's *raw* equity and open-risk are
  not emitted, so any headroom analysis reconstructs them from the same derived state it is trying to
  validate. Session L measured the consequence from the other side: the gross cap **never bound** —
  6,355 recorded units, zero shed, max utilization 0.4654. The shed cannot be validated on data that
  never exercised it, and it will stay unvalidatable until raw governor state is emitted.
- **"One packet per intent."** Establish what the current cardinality actually is before changing it.
  440 `unit_admitted` against 145 `unit_placed` and 151 `position_closed` is worth understanding.
- **"Result side repaired."** The named Phase-6 cost source records **intent only** — it never
  records what the trade actually cost. With Session J's `src/costs/` now landed, a packet can carry
  both the modelled and realized cost and let the difference be measured instead of assumed.

## Constraints that are not negotiable

- **This is a carry, not a deployment.** You produce a reviewable diff plus an owner-executed runbook,
  exactly as Session I did for the token carry — see `phase3/TOKEN_CARRY.md` and
  `phase3/STAGE0_VPS_RUNBOOK.md` on `phase3/safety-spine` and follow that shape. **Borhen executes
  anything that touches the VPS.** You never do.
- **The VPS is a live, funded, connected host** with `trade_allowed: true` on both terminals and two
  healthy books running. Placement gates are false and stay false. **Never run any broker-capable
  script**: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`, `mt5_preflight.py`,
  `dual_broker_execution_follower.py`, `start_all.bat`, `.tools/monitor_books.py`,
  `flatten_all_positions.py`, `emergency_close_and_stop_redacted_account.py`. Note that
  `create_mt5("live")` *succeeds* on macOS — the ImportError only surfaces on `.connect()` — so
  construction is **not** a safety boundary.
- **Emit-time schema validation must fail closed and must not be able to stop a live book.** Those
  two pull against each other and resolving that tension is the actual engineering. A validator that
  can crash the emitter is worse than no validator; a validator that silently drops malformed packets
  recreates the false-green class this wave has already been burned by four separate times.
- **Deployment-safe while the gates are false** is the bar, and you must *demonstrate* it, not assert
  it. Session I's proof shape: show the carry imports nothing from the coupling trap, that it is a
  no-op at every call site under current config, and that the failure mode is refusal rather than
  exception.
- **Backward compatibility is a hard requirement.** 99,112 existing packets are the only live
  evidence the programme has. A schema change that makes them unreadable destroys it. Version the
  schema; never rewrite the history.

## Hazards

- **H1 — check decision-contract membership before editing anything under `src/`.** R2 binds 43
  paths by SHA-256; a bound-file edit costs ~16.5 machine-hours per window to re-seal. Run the check
  in `CLAUDE.md` §3 *before* your first edit, not after.
- **`src/components/ultimate_book/book_owner.py` is touched by `phase3/hygiene-batch`** (Session M,
  D3 — a live-active defect where A8-rejected metals intents entered the persisted running Kelly
  count). Integration is merging that concurrently. Read M's change before you touch that file, and
  keep your diff off the same lines if you can.
- **Two sessions are running:** integration (merging six branches) and N (the re-cost A/B).
  **Memory, not CPU, is the binding constraint** — five concurrent full suites last wave left 108 MB
  free of 16 GB and silently killed captures. Keep your test scope tight, stagger any full-suite run,
  and check `pytest_returncode` and `totals` before trusting any capture.
- **Never trust a field name containing `_utc`.** Broker-time-labelled-as-UTC is a real data defect
  in this codebase and it has already cost the programme real time. Broker server wall clock =
  `America/New_York + 7 h` on the **US** DST calendar for both servers; use
  `src/utils/broker_clock.py`, which fails closed on an unregistered server. Never hardcode +3.
- **Derive, don't accumulate.** Four artifacts this wave were false-green because they were built
  from a success log and had no way to record what failed. If your emitter has a coverage or
  exclusion list, derive it by set-difference from the full expected set.

## What good looks like

The measurement that decides whether you succeeded is not "the code is written". It is: **could a
future session compute a cost-true, holding-time-aware P&L for every intent from packets alone, and
know which numbers are measured versus modelled?** Everything else is in service of that.

State plainly what your change would have made recoverable in the existing 99,112 packets and could
not, because that gap is what the shadow window will still be missing on day one.

Use your own judgment on scope, sequencing, method, and how much adversarial verification to spend —
including on whether any of the above is wrong.
