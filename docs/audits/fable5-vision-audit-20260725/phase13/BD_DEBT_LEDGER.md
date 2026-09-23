# Session BD — the live-path debt ledger (wave 13, B2050–B2099)

Every filed-but-unbuilt improvement that touches the live path, with what happened to it.
**Built** = code + behavioural tests, inert. **Closed** = the filing was answered without a build.
**Deferred** = named reason, and the reason is not "ran out of time".

Nothing here arms anything. No config byte moved, no R2-bound path was touched, the VPS was not
contacted, and no broker-capable script ran.

---

## 1. The ledger

| # | item | filed by | disposition | where |
|---|---|---|---|---|
| 1 | **OD-P3** — `modelled_cost_r` has no producer | P §6.1 / B213 | **BUILT** | `book_owner._runtime_learning_modelled_cost`, `packet_economics.build_cost_block` |
| 2 | **OD-P2** — the unit join key degenerates | P §3 / OD-P2 | **BUILT** | `book_owner._runtime_learning_unit_join_fields` |
| 3 | **OD-P1** — emit-on-change for `position_managed` | P §7 | **BUILT, default OFF** | `packet_emit_on_change.py` |
| 4 | **AQ §6a** — `want = budget + 64` degrades the time stop to INERT | AQ §6a | **BUILT: detection on, behaviour behind a flag** | `execution._trading_m15_bars_since`, `get_time_stop_clock_diagnostic` |
| 5 | **`energy_agri`'s scale-out** — twice measured, never gated | AD §6.2, AU §2 | **GATED + wired as a priced inert option** | `BD_PARTIAL_EXIT_V1.json`, `FRONTIER_EXIT_OVERRIDES` |
| 6 | **AS 6** — the sparse gap that reads like a measurement | AS handoff 6 | **CLOSED at the message** | `src/costs/model.py` |
| 7 | **AS 5** — two published figures wrong at source | AS handoff 5 | **CORRECTED at source** | `CLAUDE.md` wave-8 bullet |
| 8 | **AS 7** — `execution.py`'s B1535 needs a deploy decision | AS handoff 7 | **CLOSED by AZ's measurement — do NOT carry** | §3 below |
| 9 | **AU §1.4** — two hardening builds AR filed | AR handoff 4, AU-4 | **ALREADY BUILT by AU** — verified present | `tests/ultimate_book/test_runtime_flag_defaults_complete.py` |
| 10 | **AR's cap-absorption split** | AR §8.6 | **ALREADY BUILT by AR** — LATENT, correctly | `admission.py`, pinned |

---

## 2. What each build actually settled

### 1. OD-P3 — and the filed one-line repair does not work

P called this *"the largest remaining gap and it is cheap"* and described the fix as *"a small
change to that allowlist"*. Both halves needed correcting.

**Measured over the 99,112-packet export: ZERO packets carry any modelled cost** — not
`pretrade_total_cost_r`, not `pretrade_spread_r`, not `gtos_vnext_pretrade_cost_model`, not
`economics.cost.modelled_cost_r`. Three `pretrade_*` keys have been in the allowlist all along with
no producer, which is why the allowlist framing looked cheap.

**The literal repair ships 6.21× the bytes and does it quietly.** Adding
`gtos_vnext_pretrade_cost_model` to the flat key list emits the whole 42-key model. My own first
draft asserted it would be *quarantined* — the model carries `profile.server` and `server` is in
`FORBIDDEN_RAW_KEYS` — and that is **wrong**: `_clean_mapping` redacts it to `server_hash_sha256`
before the scan runs, so it passes validation and ships a hash of the broker server name in every
packet as noise. 2,764 bytes against 445 derived; **217.5 MB against 35.0 MB per 37-day window**, on
the stream OD-P1 exists to shrink.

**And the part worth more than the wiring.** `total_cost_r` is `spread + slippage + swap` and
charges **no commission** — F38's exact shape, surviving in the *pretrade* model after being
repaired in the realized one. The realized block charges `broker_entry_commission` and
`broker_exit_commission`. So `modelled − realized` is biased by the whole commission bill, in a
known direction, and a reader would book that bias as slippage-model error.
`modelled_vs_realized_comparable` says so on the row, three-valued so an absent side reads as
unknown rather than as a green light.

### 2. OD-P2 — the framing it was filed under was wrong, and in the safe direction

D4's agreement rule was right and its **scope** was one field (`direction`). Applied to the whole
join key. Replayed through the production function over the real corpus:

| field | agree | disagree | rows newly filled |
|---|---:|---:|---:|
| `sleeve` | 681 | **1** | **276** |
| `timeframe` / `decision_bar_iso` / `decision_day` | 682 | 0 | 277 each |
| `direction` | 630 | 52 | 225 |
| `symbol` | 405 | **277** | **0** |

P expected multi-sleeve units to be the common case (*"anything spanning two sleeves of a cluster
... yields `{}`"*). **Exactly 1 of 277 multi-member units spans two sleeves.** The common
multi-member unit is ONE sleeve on SEVERAL SYMBOLS — which is why `symbol` disagrees on all 277 and
the rule declines to emit it on every one. So the field the `_first_unit_sleeve` trap would corrupt
is the field the rule recovers almost completely, and the field that genuinely cannot be resolved is
refused by the same test. The trap is **pinned inert**, not widened; a test fails if
`SizedUnit.sleeve_members` ever stops being a tuple.

The representative-guess would fire on 277 rows and be **wrong on 1**. That is a narrower blast
radius than P feared and it is not a bound on tomorrow's: it scales with sleeves per cluster, and
the registry resolves 32.

**Still open, and not mine to fix blind:** **303 of 985** unit rows (30.8 %) carry no member roster
at all, so no rule can recover a join key for them. That is a `skip_context` population question
upstream of the emitter.

### 3. OD-P1 — the compression is a property of the contract, and the contract was never written down

P quotes one figure (76.05 %) for a change that is **irreversible for the window in which it runs**.
The same stream compresses by anything from 0.94 % to 96.72 % depending only on which fields count
as state:

| state contract | drop % of `position_managed` | of whole stream |
|---|---:|---:|
| none (every field is state) | 0.94 % | 0.74 % |
| top-level `*_checked_at_utc` excluded | 40.14 % | 31.87 % |
| **recursive `*_checked_at_utc` excluded** | **96.72 %** | **76.79 %** |

The third line reproduces P's 76.05 % to within 0.7 pp, so P's contract was the recursive one — and
the obvious implementation is the second. **A top-level exclusion list under-delivers by 2.4× while
looking deployed**, because `policy_clock_diagnostic` embeds its own `checked_at_utc` one level
down (59.7 % of rows, 100 % churn). That one nested key is the entire gap.

The contract is declared, named (`position_managed_emit_on_change_v1_recursive_checked_at`), and
falls in a real gap in the data: four fields at 100 % churn (all `*_checked_at_utc`, one nested),
two at 4.86 % (the bar clock advancing — real signal, preserved), and all 98 others at ≤ 0.46 %.

**The recommended configuration is not the headline.** 76.79 % is the NO-heartbeat figure. With the
15-minute heartbeat P recommends in the same paragraph it is **73.70 % of stream** — the heartbeat
costs 3,069 packets, 2.35 pp. Quote what you ship.

**What is lost is now countable.** A suppressed packet is unrecoverable, but it is by construction
identical to one that was kept, so what a reader loses is the *run length*. Every emitted packet
carries `emit_on_change_suppressed_before` and `emit_on_change_unchanged_seconds`. Fails open
everywhere; only ever touches `position_managed`; the cycle summary carries the count without
touching `packet_write_error_count` (feeding it there would raise an integrity issue and
`pause_new_entries` on both accounts for a working compression).

### 4. AQ §6a — the fix was not the missing thing

AQ filed and deliberately did not patch, because the obvious mitigation moves armed sleeves onto the
over-counting wall-clock path and closes them **earlier**. That judgement is respected. Two things
were missing that are not the fix:

1. **`len(candles) < want` is not the test.** A broker legitimately returns fewer bars than asked.
   The only question is whether the window reaches back **past the fill** — if the oldest closed bar
   printed after `entry_dt` the count is a LOWER BOUND, not a count. Free from timestamps already
   parsed.
2. **The inertness was invisible.** `book_owner.py:2768-2772` has asked the engine for
   `get_time_stop_clock_diagnostic`, then `_last_time_stop_clock_diagnostic`, since the packet carry
   landed — and **no engine in this repository defined either name**. `policy_clock` was `None` on
   every tick of this lineage. A time stop that cannot fire produced no signal anywhere. This engine
   is now that missing producer.

Detection always on and inert. Behaviour behind
`ultimate_book_time_stop_wallclock_on_truncated_window`, default OFF, no committed config sets it;
arming trades an inert backstop for an early one, which is per-sleeve and Borhen's.

**Headroom, which is why it ships now:** F15 measured 7,800 available against an `mx_*` request of
7,744 — **56 bars, 0.72 %** — on a terminal setting a future session can change without knowing this
code exists. Nothing armed is exposed (H4 at 1280 wants 1344).

### 5. `energy_agri` — better, and still not admissible

Gated at the ratified rule (RECORDED, `B_balanced` α 0.10, family V5, four bands), cut rule declared
before any gate ran: two arms per sleeve, nothing fitted.

| sleeve | live | plain | plain − live | verdicts |
|---|---:|---:|---:|---|
| **`energy_agri`** (ARMED) | +0.1763 | +0.4065 | **+0.2302** | REJECT / REJECT |
| `metals_softband` | +0.0530 | +0.0902 | +0.0372 | REJECT / REJECT |
| `metals_core` | −0.1300 | −0.2077 | **−0.0777** | REJECT / REJECT |
| `metals_ob_micro` | −0.1207 | −0.1606 | **−0.0399** | REJECT / REJECT |

R/day at the mid band. **The control does its job: the sign runs both ways, 2 of 4 each.** A harness
that preferred plain everywhere would be measuring itself. Reproduces AU's two published figures to
four decimals through an independent driver.

**It is not an admission.** Both arms REJECT at all four bands; `p_raw` 0.321 → 0.206 against
α 0.10; n = 64; and the chronological fold table decays under **both** contracts — LIVE
`[+0.533, +0.282, −0.287]`, PLAIN `[+0.933, +0.351, −0.064]` — the most recent fold negative either
way, most of the improvement in the earliest. `maxbars_share` 0.0 on both, so it is a contract
difference and not a ceiling artifact. `p_min` over the two arms 0.2005 against 0.3608 expected
under the global null.

**One structural nuance to carry forward:** the delta is *identical* at all four bands because a
cost band shifts both arms equally. "At every band" is a property of the comparison, **not four
independent confirmations**. AU's §2 phrasing should be read that way too.

Wired as `FRONTIER_EXIT_OVERRIDES["energy_agri"]`, cell `plain_exit_no_partial`, default OFF,
ceremony selects by name. **The recommendation is not to arm it on this evidence.**

### 6–7. AS handoffs 6 and 5

**6.** AS filed *"one line in the profile"*; that line landed in `scripts/gtos_hydrate_test_data.py`
in AU. **The message never did** — and the message is what a session reads at the moment it is
stuck. The artifact is committed, so on a fresh worktree *"not found ... Build it with
`build_broker_true_costs.py`"* sent three sessions in a row (AR B1473, AS, BD) to re-run a
broker-truth capture when the answer was one `git sparse-checkout add`, each after a ~25 s substrate
build. That is AS's *"failed run that reads like an expensive measurement"*, and it fired on me
before I had read AS's note about it. The two cases are now distinguished with `git ls-files`.

**7.** Corrected in `CLAUDE.md` at source: `+1.157 R/day` is the **level** of the `target_4R` cell,
not the improvement (`as_walked` 1.0264 → 1.1565, so **+0.130**, an 8.9× overstatement), and AK's
frontier is ALL_ERAS at the flat band at family 69 — not the ratified rule. Re-gated the delta is
**+0.3435 R/day**, *larger*; the verdict is still REJECT at all four bands with a negative train
window on armed money.

### 9–10. Two items that were already built

**AU §1.4** — both hardening builds AR filed exist and are green:
`tests/ultimate_book/test_runtime_flag_defaults_complete.py` (the AST walk that discovers resolvers)
and the learning lane's raise guard as a property over every branch. Verified present, not rebuilt.
My own new runtime keys are read through `rt.get(key, default)` with inline defaults, which is the
fail-safe shape, not the `DEFAULT_CONFIG[key]` resolver that raises.

**AR §8.6** — the size-up/shrink split is in `admission.py` and pinned. AR's own third pass
established it is **latent, not active** (`ultimate_book_overlays: false` *and* the only live
`sub_xvol_pullback` generator populates neither field either overlay needs, so `su` is 1.0
structurally). Nothing to add; re-deriving it would have cost a session.

---

## 3. AS handoff 7 — closed by AZ, and it inverts the filing

AS asked for a deploy decision on `execution.py`'s B1535 fix, noting *"the books currently run the
pre-fix code."* **Session AZ measured the answer against the host's own bytes and it is: do not
carry it.** The host's `execution.py` carries an explicit `if selected_policy == "time_stop":`
branch from lineage commit `b36d9ab92` — an ancestor of `redacted_host` and **not** of `main` — so the
`KeyError('trigger_r')` is real on mainline and **unreachable on the host**. Applying mainline's
hunk fixes nothing there and moves two live behaviours on adopted time-stop positions across all
four armed sleeves (`be_trigger_r` 0.0 → the record's value; `take_profit_1` 0.0 → `be_trigger_price`
— measured 3 of 3 adopt probes).

**This has a direct consequence for my own work, and it is the most important line in this
document.** My AQ §6a change is in `execution.py`. **It therefore cannot be carried as a whole
file**, because a whole-file copy would silently ship the B1535 fix AZ measured must not go. See
`BD_CARRY_MANIFEST.json` → `not_carryable_as_whole_file`.

---

## 4. What this session did not do

- **It did not deploy, arm, or recommend arming anything.** Two default-off runtime keys and one
  default-off frontier contract; no committed config sets any of them, asserted by tests.
- **It did not touch the VPS**, any config, or any R2-bound path. H1 drift read `2 UNHYDRATED-LFS`
  at start and `1` at end — the reduction is one `git lfs checkout` of a bound ledger that arrived
  as a pointer, per CLAUDE.md H1, not a change to any bound file.
- **It did not run a broker-capable script.**
- **It did not fix the 303 rosterless unit rows** (§2.2) — that is upstream of the emitter.
- **It made no repo-wide "no regressions" claim.** The A/B is by failure set over an 85-file blast
  radius: `phase13/SESSION_BD_AB.md`.
