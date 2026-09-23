# Activation dossier — the ratified entry-hour convention

Session CE (B2310–B2318). **Nothing here is armed by this session.** The lever is built,
default-off, and the recommendation below is Borhen's to accept or refuse.

Authority: `phase9/OWNER_DECISION_ENTRY_HOUR.md` (ratified 2026-07-30) and OD-HISTORICAL-FIRST
§3. Receipts: `phase15/receipts/CE_ENTRY_HOUR_V1.json` (the measurement),
`phase15/receipts/CE_ENTRY_HOUR_IDENTITY.txt` (OFF == the base commit),
`tests/ultimate_book/test_ce_entry_hour_lever.py` (35 tests).

---

## 0. The decision's own scope note is now false, in two different ways

The ratified decision says:

> *Applies to the FX D1 generating sleeves (the `mx_*` D1 cohort and any future D1 FX sleeve
> whose generation clock fills at hour 00). … the armed three sleeves are not in this cohort,
> so nothing armed changes.*

Both halves were true on 2026-07-30. Both are false now, and the second one is the important
one because it was never about arming — it was about how the cohort was defined.

**0.1 An `mx_*` D1 sleeve IS armed.** `mx_btcusd_d1_donchian_20_breakout` went live on FTMO at
2026-07-31 ~01:26 UTC. It fills at broker hour 00 on **318 of 318** trades. The decision's own
scope line puts the `mx_*` D1 cohort in scope and simultaneously says the cohort is FX; BTCUSD
is in the first and not the second. **The decision is ambiguous exactly where it now bites**, so
this dossier records the ambiguity rather than resolving it — scope is an owner call.

**0.2 The cohort was scoped by TIMEFRAME and the phenomenon is a property of the BAR CLOSE
HOUR.** An H4 bar closes at broker 00:00 too. Measured across the armed set
(`CE_ENTRY_HOUR_V1.json` → `census`), on the FTMO-Server3 clock:

| armed sleeve | tf | fills at broker hour 00 | share |
|---|---|---:|---:|
| `mx_btcusd_d1_donchian_20_breakout` (FTMO only) | D1 | 318 of 318 | **100 %** |
| **`sub_mid_dn_revert`** (both accounts) | **H4** | **235 of 533** | **44.1 %** |
| `crypto` (both) | H4 | 35 of 181 | 19.3 % |
| `energy_agri` (both) | H4 | 9 of 67 | 13.4 % |
| `sub_xvol_pullback` (both) | H4 | 9 of 88 | 10.2 % |

**Scoping by D1 missed the only armed sleeve the lever can actually help.**

---

## 1. The measurement, and why it inverts the obvious reading

The rollover premium is a property of the **symbol**, not of the sleeve or the timeframe.
Median M15 spread at broker hour 00 against the median of every other hour, on the matched FTMO
feed (2024-01-01 … 2026-07-27):

| symbol | hour 00 | other hours | premium |
|---|---:|---:|---:|
| **CHFJPY** | 239 | 12 | **×19.9** |
| **USDJPY** | 64 | 4 | **×16.0** |
| **GBPJPY** | 174 | 14 | **×12.4** |
| **AUDJPY** | 90 | 8 | **×11.3** |
| **EURJPY** | 96 | 12 | **×8.0** |
| NZDJPY *(unarmed, FX D1 cohort)* | 95 | 9 | ×10.6 |
| CADJPY *(unarmed, FX D1 cohort)* | 86 | 11 | ×7.8 |
| **BTCUSD** | 2442 | 2442 | **×1.000** |
| DASHUSD | 20 | 20 | ×1.000 |
| XAU\*/XAG\*, oils, cash indices | *no quote at hour 00* | — | n/a |

Two consequences, and they point opposite ways:

**`mx_btcusd` — the armed sleeve the decision names — has nothing to gain.** BTCUSD quotes 24/7
with a flat spread schedule; there is no rollover on it at all. Measured directly on the 97 of
its 318 trades the M15 archive covers, the hour-01 entry displacement is **−0.0185 R/trade**
(median −0.0416, 37.1 % positive), and **zero** of those 97 trades touched their stop or their
target in the skipped hour — so that first-order figure is **exact**, not an approximation.
Arming the lever here costs about two hundredths of an R per trade and saves nothing.

**`sub_mid_dn_revert` — an H4 sleeve, outside the ratified cohort, armed on both accounts — is
where the exposure is.** 147 of its 533 trades (**27.6 % of the sleeve**) enter on one of the
five JPY crosses at broker hour 00, into a ×8–×20 spread.

---

## 2. What is NOT decidable from the data on this machine, stated plainly

**The cost half is measured and large. The gross half is not decidable, and the honest sample
size is 7.** Of `sub_mid_dn_revert`'s 147 premium-symbol hour-00 trades, only **7** fall inside
the M15 archive's span (it starts 2024-01-01; 182 of the sleeve's hour-00 trades predate it).
On those 7 the mean displacement is −0.0598 R — a number with no standing at n=7 and it is not
offered as one.

AH's end-to-end simulation of the FX D1 cohort found cost dominating gross **5:1 to 10:1**
(gross −0.0154 R/trade against a cost saving of +0.0788…+0.1567), which is a prior that the net
is positive wherever the premium is real. **That prior is not transferred here** — different
sleeve, different timeframe, different symbol set — and quoting AH's +0.063…+0.141 for
`sub_mid_dn_revert` would be exactly the transfer this estate keeps having to correct.

Under OD-HISTORICAL-FIRST §2 a sample gap is an action item, not a verdict. The specific,
priced fetch that would decide it:

> **M15 (or H1 with a verified `.timebase.json`) for GBPJPY, CHFJPY, AUDJPY, USDJPY and EURJPY
> on the matched FTMO feed, back to the start of `sub_mid_dn_revert`'s archive.** That converts
> 7 measurable trades into ~147 and makes the gate walk possible. It is a capture, not an
> analysis, and it is the orchestrator's to price.

A second, cheaper half exists and is worth naming: four pre-2024 H1 files already sit in
`data/` (GBPUSD, USDJPY from 2022-01-03; GBPJPY, NZDUSD from 2023-01-16) and are unusable only
because they carry **no `.timebase.json` sidecar**, so `CsvBarSource` refuses them under the F7
fail-closed rule. AQ costed that at *"a day's work, not a capture."* It buys USDJPY and GBPJPY —
two of the five — over two extra years.

---

## 3. What was built

| file | what |
|---|---|
| `src/components/ultimate_book/entry_hour.py` | new. `parse_entry_hour`, `deferral_reason`, `EntryHourSelectionError`. Imports `typing` only. |
| `src/components/ultimate_book/book_engine.py` | `entry_hour=` + `broker_server=` kwargs; `_entry_hour_deferral` applied at generation, after the spread floor |
| `src/components/ultimate_book/book_owner.py` | kwarg passthrough; resolves the broker server as a **callable** so a reconnect to a differently-named server cannot leave a stale name |
| `run_book.py` | `--entry-hour`, validated at launch |
| `tests/ultimate_book/test_ce_entry_hour_lever.py` | 35 behavioural tests |

**It is a DEFERRAL at generation, not a new decision timeframe, and that is forced by the
data.** An hour-01 fill needs a bar closing at broker 01:00; on the matched feed the D1 grid
closes at 00:00 and H4 at 00/04/08/12/16/20, and neither contains one at any date. Only M15
does. So the book generates on the same decision bar it uses today and declines to *emit* the
intent until the broker clock reaches the target. The launcher already polls every 60 s, the
decision bar does not change between rollovers, and the idempotency key (`decision_bar_iso`)
makes it place exactly once.

**It FAILS OPEN, which is the opposite of the spread floor and is deliberate.** An unresolvable
server, an unregistered clock rule, an unknown timeframe or a bug in the method all emit the
intent unchanged — today's behaviour. Deferring forever on a dark clock would be a silent
disarm of an armed sleeve, and what cannot be evaluated here is an *improvement*, not a *rule*.
Every fail-open increments `generation.entry_hour.fail_open` and the first eight distinct
exceptions are named in `generation.entry_hour.errors`. The rule, stated so it can be argued
with: **fail closed when the failure mode is a breach; fail open to the committed contract when
it is a missed improvement.**

**The launch refusal that matters.** `book_owner._entry_too_late` shadows any entry more than
`ultimate_book_max_entry_lateness_frac` (0.5) of a bar period past the close — **12 h on D1,
2 h on H4, 7.5 min on M15**. A target past that window is accepted by every other check and
then silently dropped at placement as `stale_late_entry_after_restart`: the sleeve stops
trading while every log reads healthy. `parse_entry_hour` refuses it at launch. Measured
against this repo's registry: `sub_mid_dn_revert:1` and `mx_btcusd…:1` are legal; `crypto:5`,
`sub_mid_dn_revert:3` and any M15 sleeve at hour 1 are refused.

**OFF is byte-identical**, proven non-vacuously against this session's base commit
(`e19a2bb49`): the same fixture generates 2 intents on both sides and the intents, meta,
generation telemetry and generation-skips all match. The proof **refuses to report PASS** if
the fixture generates nothing — an identity proof that cannot fail is not evidence.

**No config key.** The lever is a launcher argument, so AR's `DEFAULT_CONFIG` AST hardening
(`test_runtime_flag_defaults_complete.py`) is satisfied by construction — asserted directly
rather than assumed. Neither `agent_config.yaml` nor `profiles/redacted_account.yaml` moves, so
neither activation token's digest moves. **No R2-bound path was touched** (43 bound, 2
UNHYDRATED-LFS, 0 drifted, at session start and end).

---

## 4. Recommendation

| sleeve | recommend | why |
|---|---|---|
| `mx_btcusd_d1_donchian_20_breakout` | **DO NOT ARM** | 100 % of fills at hour 00 and a ×1.000 premium. Measured cost −0.019 R/trade, exact on all 97 measurable trades. The lever is a cost repair and there is no cost to repair |
| `sub_mid_dn_revert` | **HOLD — fetch first** | 27.6 % of the sleeve enters into a ×8–×20 spread, on armed money, on both accounts. The cost saving is real and the gross half rests on **n=7**. Under OD-HISTORICAL-FIRST the correct move is the priced fetch in §2, not an arming on a prior borrowed from a different cohort |
| `crypto`, `energy_agri`, `sub_xvol_pullback` | **do not arm** | 10–19 % hour-00 share, and their hour-00 symbols are BTCUSD/DASHUSD (×1.000) or instruments that do not quote at hour 00 at all |
| the unarmed FX D1 cohort (`mx_nzdjpy`, `mx_cadjpy`, …) | **the lever's real home** | ×7.8–×10.6 premium, AH's +0.063…+0.141 R/trade measured end to end on exactly these members, 38 of 42 improving. They are the natural next incubants and the mechanism is now ready for them |

**The one-line version:** the ratified convention was implemented, and the measurement says arm
it on nothing today — because the sleeve the decision named has no premium to save and the
sleeve with the premium has seven measurable trades. That is a fetch, not a verdict.

---

## 5. The ceremony, when the owner says go

**Flag** (no config byte; no token disturbed):

```
--entry-hour sub_mid_dn_revert
```

beside `--tags` at `scripts\run_book_supervisor.ps1:140`, per account. Bare means the ratified
hour 01; `sub_mid_dn_revert:2` is available and would need the §3 lateness check re-read (2 h on
H4 is exactly the window — it is refused).

**Carry first.** `entry_hour.py` is a new module and `book_engine.py` / `book_owner.py` /
`run_book.py` need the anchored edits. Build it the way
`phase15/activation_carry_spread_floor/` is built: **the host's `book_engine.py` is Session AC's
after-bytes (`b6a9ef7d…`, 37,838 B), not the lineage's** — see that package's §0.1. This carry
should be composed **on top of** the spread-floor carry, since both edit the same three files at
adjacent anchors.

**Restart at a decision-day boundary** for the same reason the floor does (B365): the day's
persisted firing-sleeve union is monotone upward, so a mid-day restart inherits the wider set.

**The line that proves it armed:**

```
ENTRY-HOUR CONVENTION IS ON for sub_mid_dn_revert: enter at broker hour 01 instead of the
decision bar's own close. The intent is DEFERRED at generation and re-proposed each tick until
the broker clock reaches it, so this book PLACES LATER and at a different price.
```

**Absent ⇒ the flag did not take.** Then watch `generation.entry_hour` →
`{evaluated, deferred, fail_open, sleeves}` in the cycle telemetry.

**Stop conditions.** (1) **`fail_open > 0` on any cycle** — the lever is not applying and the
book is running the committed contract while the operator believes otherwise. This is the most
likely failure mode and it is why the counter exists. (2) Any `generation.entry_hour.errors`
row. (3) A `stale_late_entry_after_restart` skip on a sleeve named in `--entry-hour` — the
launch check should make this impossible, and if it happens the check has a hole. (4) The
deferred count is zero over a week in which the sleeve fired at hour 00 — the deferral is not
reaching the intents.

**Rollback:** remove the flag and restart. Nothing is written, held, or opened; the lever only
declines to emit an intent for up to one hour.
