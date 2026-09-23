# Carry receipt — owner manual SL/TP moves are first-class

Session LM, 2026-08-05. Owner directive, verbatim: *"if i make a move on my ftmo account it should
reflect on the book, my manual moves should be allowed and 'normal' to have"* — which also settles
the policy fork the forensic refused to decide: **the book yields to the owner.**

Host commit **`f66da7664`** on `vps/ultimate-conditioned-expansion-minimal-2026-06-18`.

## 0. H1 — contract binding [ANSWERED: NOT BOUND, no seal break]

Checked against `B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json` (45 path rows
across `common_behavior_inputs` 41, `package_authority_inputs` 2, `verification_tooling` 2):

| file touched this session | R2 binding |
|---|---|
| `src/components/execution.py` | **NOT BOUND** |
| `tests/test_owner_manual_protective_moves.py` (new) | **NOT BOUND** |
| `scripts/run_book_supervisor.ps1` | **NOT BOUND** |
| `scripts/mt5_preflight.py` | **NOT BOUND** |

**No decision-contract seal is broken by anything this session did.** For the record, the bound
files under `src/components/` are `broker_net_cost_engine.py`, `execution_manager_v4.py`,
`exit_policy_v4.py`, `pending_nofill_lifecycle_v4.py`, `prop_firm_headroom_v4.py`,
`same_symbol_lifecycle_v4.py`, `selector_v4.py`, `workspace_paths.py` — **none of them was touched.**
CN's authorized forward break on `broker_net_cost_engine.py` remains unspent.

No `config/agent_config.yaml` byte moved; **no activation-token re-mint required**.

## 1. The lineage trap this nearly walked into

**Mainline's `execution.py` is a different file from the host's**, and patching the wrong one would
have shipped ~7 KB of untested drift onto two funded accounts:

| | bytes | sha256 |
|---|---:|---|
| host (live) | 454,116 | `d0d367877dfb6cde52f886a93623238dfaa788e5d7f14b8e19451e3c62938445` |
| mainline | 461,239 | `afb81e734e2d0b8a43585da0c35908d1bba0e4c4aab6755c22e5183506b9f913` |

`book_owner.py` differs by 31 KB, `book_engine.py` by 23 KB, `launcher.py` by 3 KB — this is Session
S's 25-of-519 divergence, seen from the inside.

**All work was done against the host's exact bytes**, obtained without touching the host: the host's
blob `938779a5…` was already in the Mac's object store via `origin/vps/ultimate-conditioned-
expansion-minimal-2026-06-18`, and `git cat-file -p` reproduced it at sha256 `d0d36787…` — verified
equal to the live file before anything was written.

## 2. What changed, and why each piece exists

**(1) Broker truth + adoption.** New `ExecutionEngine._reconcile_broker_protective_levels(trade,
position)`, called from `check_and_manage_trade` **before any exit logic reads `trade.stop_loss`**.
It re-reads `position.sl` / `position.tp` every management tick, adopts them, and stamps provenance.
Previously the book re-synced from the broker in only two narrowly-gated partial-recovery paths
(`_sync_recovered_partial_state_from_broker`, and inside `_execute_tp1_partial` when broker volume
had already dropped), so on a normal position an external move was invisible for the whole life of
the trade.

> **`sl_distance` is deliberately NOT rewritten.** It is the *sizing* basis — the definition of 1R
> that every downstream R computation is anchored to. Holding it fixed is exactly what makes
> `owner_sl_implied_risk_ratio` a meaningful number rather than a tautology.

**(2) Never-worsen guard at the single choke point, `_modify_sl`.** The book may not write a stop
worse than the one live at the broker. One guard there covers every caller:

- `_move_sl_to_breakeven` had **no worsening check at all** — it called
  `_modify_sl(ticket, trade.entry_price)` unconditionally;
- `_move_sl_to_dynamic_r` had one, but compared against `trade.stop_loss` (the book's own memory),
  not the broker.

It reuses the codebase's **existing** predicate `_sl_modify_reduces_or_preserves_risk(position,
new_sl)`, which already reads broker truth and was previously wired only to the runtime-halt path.
Returning `False` is a well-handled outcome — `_move_sl_to_breakeven`'s BUG #28 contract explicitly
does *not* close the position on a modify failure.

This is a **safety** fix independent of who set the stop: the book widening its own protection on an
open position is never correct.

**(3) Yields in BOTH directions, with one honest exception.** A tightened stop is kept. A **widened**
stop is also adopted and never silently re-tightened — but a widened stop can push the position past
the cash risk it was sized for, and on a prop account an unbudgeted loss is the fatal kind. That case
emits an explicit `WARNING` and an `OWNER_PROTECTIVE_LEVEL_ADOPTED` packet event carrying
`owner_sl_implied_risk_ratio` and `owner_sl_risk_exceeds_sized`. **Never silently re-tightened**
(that would fight the owner), **never silently accepted unrecorded** (that would hide a real exposure
change). The governor's breach-flatten is untouched and remains the backstop.

> Risk is measured **signed**, not as a distance. For a LONG it is `entry − sl`; for a SHORT it is
> `sl − entry`. A stop moved *past* entry into profit therefore has a **negative** risk distance and
> can never trip the warning — which is precisely the 2026-08-04 case (SHORT, stop 80.511 below
> entry 83.233, ratio **−0.403**). A naive `abs(entry − sl)` would have paged the owner for locking
> in profit.

**(4) Exit provenance.** `_record_close` now stamps `exit_level_provenance`
(`owner_modified` | `book_set`), `exit_stop_matches_book_intent`, the book's intended SL/TP, the
broker's last-seen SL/TP, the owner's levels, the override counters, first-seen timestamp, and the
risk flags. MT5 reports `DEAL_REASON_SL` identically whether the stop was the book's or a human's, so
without this an owner-steered exit is credited to the sleeve as its own performance. **Additive
only** — the existing `broker_closed` reconciliation semantics are unchanged, and a test pins that.

**(5) Break-even skipped cleanly when the live stop is already better.** Without this, the guard
would refuse three times and then page the owner with *"broker rejection requires human
investigation"* — false, and it would page him **for moving his own stop**. Same outcome, no false
alarm.

## 3. Test evidence — behavioural, and they bite

`tests/test_owner_manual_protective_moves.py`, **24 tests**, asserting what reaches the broker and
what the engine's own state becomes — never source text. All 24 pass **on the host, against the
installed file, in the real environment with the real sibling modules** (and from the repo location:
`24 passed in 8.77s`).

| group | what is pinned |
|---|---|
| adoption | owner-tightened stop adopted and **reflected on the book**; event recorded once; `sl_distance` preserved; locked-profit stop **not** flagged as risk (ratio < 0) |
| widening | adopted, `owner_sl_risk_exceeds_sized` True, ratio 1.5, warning logged, **zero broker requests sent**; a widening still *within* sized risk does not warn |
| never-worsen | refused on SHORT and on LONG, **no `order_send` issued**, better stop stays live, refusal event recorded; stop **removal** refused; setting a stop where none exists still allowed |
| regression | ordinary book tightening still sends and updates `book_intended_sl`; break-even still works on an untouched book stop; a book move is **not** later misread as an owner override; reconcile is a no-op when broker agrees |
| the incident | **the 2026-08-04 scenario end-to-end** — owner stop adopted, 2R break-even fires, owner's 80.511 survives, zero requests sent |
| provenance | `owner_modified` vs `book_set` both correct; `exit_stop_matches_book_intent`; close-reason semantics unchanged |
| BE skip | skip event emitted, guard not even reached, **owner not paged** |
| armed sleeves | `crypto`, `energy_agri`, `sub_xvol_pullback`, `sub_mid_dn_revert` **pinned by name**: absent an owner move, state and broker traffic are byte-for-byte unchanged |
| tolerance | absorbs 1e-12 float noise, sees a 0.001 tick |

**A/B against the pre-patch file** — same scenario, same fake broker, only the module differs:

```
BASE    (host today) : sent 1 request, owner's stop 80.511 -> 83.233   [DESTROYED]
PATCHED              : sent 0 requests, owner's stop 80.511 -> 80.511  [PRESERVED]
```

The defect is **real on the host as it stood today**, and the patch fixes it. (A test that passes on
both versions proves nothing; this one does not.)

## 4. The carry, and the check that stopped a bad install

Rather than push 471 KB of base64 over host-admin, the **patch script** was shipped and run on the host so
the host transformed its own file — then the result was verified by hash against the Mac-tested bytes.

**That check earned its keep on the first attempt.** The host produced **481,837 B /
`8c3219a9…`** instead of 471,334 B / `91ed9873…`. Cause: Python's text-mode I/O on Windows translated
every `\n` to `\r\n` on write (+1 byte per line ≈ the 10,469-byte delta). **The script refused to
install and the live file was never touched.** Fixed by byte-exact I/O (`read_bytes().decode()` /
`write_bytes(...encode())`), re-run, and the host then produced a file **byte-identical to the
Mac-tested one**.

| | bytes | sha256 |
|---|---:|---|
| before | 454,116 | `d0d367877dfb6cde52f886a93623238dfaa788e5d7f14b8e19451e3c62938445` |
| after | **471,334** | **`91ed9873f1b87de9f340cb489f0f7e39570c3f51e13a33c9104f8270c3be1b7f`** |

Backup of the exact prior bytes: `C:\Users\trader\lm20260805\execution.py.before-LM`, sha256 verified
equal to the pre-edit file.

**`verify_carry.py --check all` was not run, and could not be** — that tool is not generic; it ships
inside each built ceremony package (`phase4/packet_carry/`, `phase5/`, `phase13/`, `phase15/`) with
its own payload and expected-hash set, and no package exists for this change. Substituted: exact
before/after hashes, `py_compile`, the 24 behavioural tests **on the host**, the A/B against the
pre-patch file, and a host-branch commit.

**Installing did not change running behaviour** — the books hold the old module in memory until
restart; their pids were unchanged across the install (verified).

## 5. Restart — both books, at a decision-boundary-safe moment

`execution.py` is shared by both books, so both had to restart to load it. The window was chosen
rather than taken: the **17:00Z H4 boundary was ~2 minutes away** at the time the carry finished, so
the restart waited for that cycle to complete on both books before touching anything.

| UTC | event |
|---|---|
| 16:52:12 | patched file installed (books keep running the old module in memory) |
| 17:00:01 / 17:00:57 | **17:00Z H4 cycle completes** — FN then FTMO, four tags, `killed=false halted=false` |
| 17:01:54 | guarded script: FTMO 0 pos / FN 0 pos; host-UTC today `2026-08-05` **absent** from both `firing_sleeves.json` → `PROCEED` |
| 17:01:55 | pids discovered dynamically (not from a stale list) and stopped: 4696, 4708, 7164, 8028, 10756 (7080/9808 had already exited with their parents) |
| 17:03:07 | FTMO relaunched |
| 17:03:15 | redacted_account relaunched |
| 17:03:27 | both heartbeats healthy |

**Downtime ≈ 1 m 33 s**, both accounts flat throughout, next boundary 21:00Z — four hours clear.

### Post-restart verification

| check | FTMO | redacted_account |
|---|---|---|
| gates | `authority_gates_ON=True halted=False killed=False` | same |
| **config digest** | **`ffe16657feaf` — unchanged** | **`e184a81d3b1b` — unchanged** |
| account identity | verified | verified |
| argv | 4 tags, **no `--frontier-exits`** | 4 tags, no frontier |
| spread-geometry floor | ON for both sleeves | ON for both sleeves |
| timeframes | `tfs=[16388]` | `tfs=[16388]` |
| kill flag | absent | absent |
| heartbeat | pid 9640 healthy | pid 9800 healthy |

**No activation-token re-mint was needed and none was performed** — both digests are byte-identical
to before, which is the direct evidence that no token-bound byte moved.

**Proof the running books actually loaded the patched module** (rather than a stale `__pycache__`):
the file was installed at **16:52:12Z** and all four book processes were created at
**17:03:07–17:03:15Z** — after it. The installed source carries `_reconcile_broker_protective_levels`
(3 references), `sl_modify_would_worsen_live_broker_stop`, `exit_level_provenance`,
`SL_TO_BREAKEVEN_SKIPPED_LIVE_STOP_ALREADY_BETTER`, and `owner_manual_override_provenance_v1`
(5 references).

## 6. Known limits — stated, not buried

- **TP provenance is weaker than SL provenance, by choice.** `book_intended_sl` seeds from the book's
  own state (set in the entry request, so it is authoritative and catches an owner move made before
  the first management tick). `book_intended_tp` seeds from the **broker** on first sight, because
  the book's own TP lives in `take_profit_1` or `take_profit_2` depending on policy and guessing
  wrong would manufacture a false override on the very first tick. **Consequence: a TP moved before
  the first management tick is not attributed.** SL — the safety-critical one — has no such gap.
- **Detection is per-tick (~60 s), so a move made and reverted inside one tick is invisible.** It
  cannot cause a wrong action (the guard always reads live broker state at write time); it can only
  cost a provenance record.
- **This does not retro-label the 2026-08-04 trade.** That record still says `broker_closed` with no
  provenance; the forensic receipt is its provenance. The fix is forward-looking.
- **`owner_sl_override_active` clears when the broker's stop matches the book's intent again.** If
  the owner moves a stop and the book later legitimately sets that same level, the exit is attributed
  to the book. This is deliberate — attribution follows *who set the level that is live* — but it
  means a coincidental match reattributes.
