# Session CE — the sleeping-improvements activation package (wave 15, B2300–B2340)

Commission `phase15/SESSION_CE_ACTIVATION_PACKAGE.md`. Charter
`phase15/OD_HISTORICAL_FIRST_SCALING.md` (Borhen, 2026-07-31). **Nothing armed. The VPS
untouched. No broker-capable script run. `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml` and every R2-bound path unwritten** — 43 bound paths checked
at session start and end: 2 UNHYDRATED-LFS, 0 drifted.

---

## 0. Findings first

1. **The host's `book_engine.py` is not the lineage's, and building the carry against the
   lineage would have failed preflight on a funded machine.** It reads like a path no ceremony
   has written — AZ's manifest does not mention it, S's does not carry it — but **Session AC's
   activation carry has it at `copy_order: 3`**, and that carry landed 2026-07-29, verified at
   after-bytes. The host is at `b6a9ef7d…` (37,838 B), not `187f35a4…` (36,498 B). My first
   build had it wrong. **"No manifest I read mentions this path" is not "no ceremony has
   written it"** — the carries compose, and the composition is the state.

2. **The spread floor's activation carry is built, and its verifier was exercised end to end
   *before* the ceremony** against a reconstructed host tree (lineage + the S, AC and AZ
   carries, 15 of 15 at their own manifests' after-hashes): **45 ok / 0 FAIL**, plus a
   deliberate order violation caught and a proven rollback. Session AC's verifier could never
   be run before it met a funded machine; this one has been.

3. **On the basis the estate ratified for anything that gets sized, AY's own recommendation
   inverts — and nobody had computed the delta.** Wave-11 §1 requires the recent-fold basis for
   a sized decision. AY published the recent-fold *levels* and the *pooled* delta, never the
   delta on that basis. Recomputed: `sub_mid_dn_revert` **+0.4260 pooled → +0.0410 recent
   (10 %)**; `sub_xvol_pullback` **+0.2644 → +0.2559 (97 %)**. Both true, answering different
   questions — the pooled delta is the evidence the effect is real, the recent-fold delta is
   the planning number. **Arm both; expect the economics from the second and the conviction
   repair from the first.**

4. **The ratified entry-hour decision's scope note is now false, and the larger of the two ways
   has nothing to do with arming.** It says *"the armed three sleeves are not in this cohort."*
   (a) An `mx_*` D1 sleeve **is** armed since 2026-07-31 and fills at broker hour 00 on **318 of
   318** trades. (b) **The cohort was scoped by TIMEFRAME and the phenomenon is a property of
   the BAR CLOSE HOUR.** An H4 bar closes at broker 00:00 too, and `sub_mid_dn_revert` — H4,
   outside the cohort, armed on **both** accounts — puts **235 of 533** fills there.

5. **The rollover premium belongs to the SYMBOL, and that decides the whole lever.** Median M15
   spread at broker hour 00 against every other hour: **CHFJPY ×19.9, USDJPY ×16.0, GBPJPY
   ×12.4, AUDJPY ×11.3, EURJPY ×8.0** — against **BTCUSD ×1.000** (24/7, no rollover) and no
   quote at all on metals/oils/indices. So `mx_btcusd`, the sleeve the decision names, has
   nothing to gain: measured **−0.0185 R/trade**, and **exactly**, since zero of the 97
   measurable trades touched a stop or target in the skipped hour. `sub_mid_dn_revert` puts
   **147 of its 533 trades (27.6 % of the sleeve)** on the five JPY crosses at hour 00.

6. **And the gross half on that sleeve is not decidable: the honest sample size is 7.** Only 7
   of those 147 fall inside the M15 archive's span. AH's cohort prior (cost dominating gross
   5:1 to 10:1) is **not transferred** — different sleeve, timeframe and symbols. Under
   OD-HISTORICAL-FIRST §2 that is a priced fetch, not a verdict: M15 for the five JPY crosses
   back to the sleeve's archive start, plus a cheap half that needs only a `.timebase.json`
   sidecar on four H1 files already in `data/`.

7. **BA-H1 is retired: `broker_clock.py` is already on the host, twice over.** Carried by
   Session S (`copy_order: 1`) and again by Session AC (`copy_order: 1`), verified at
   after-bytes, and **committed on the host branch at `118071eaa`** because a `git clean` would
   have deleted it. BA was reading a fact about the 2026-07-26 export; the carries landed
   2026-07-29/30.

8. **The weekend policy is NOT a sleeping improvement, and reading it as one costs 42.8 % of
   the four-sleeve daily mean.** The floor is an improvement whose trigger is a measurement
   that is in; the weekend policy is a **contingent obligation** whose trigger is an account
   state change — it binds when redacted_account passes and binds on FTMO never. Correctly unarmed,
   not defectively unarmed. Pre-select option (a′) and buy the two answers now: the gap between
   (a′) and (a) is **one support ticket worth 28.3 % of the whole bill**.

9. **`mx_btcusd`'s promotion rule is restated historical-primary — at ZERO live fills, the only
   clean moment it could ever be rewritten.** CA's rule needed 60 live fills ≈ **51 calendar
   months**. **P1-HIST** needs four historical milestones plus a live veto that only blocks, and
   **every input exists on this machine today**: cross-broker replication on the redacted_account
   BTCUSD archive, cross-instrument mechanism replication on `mx_ethusd`/`mx_avausd`/`mx_nzdjpy`
   (the last an **FX cross**, so replication there is not a crypto artifact), repair-interaction
   persistence, and no chronological decay. **51 months becomes an afternoon of compute.**

10. **Stated as a trade, not as an improvement: P1-HIST is WEAKER per decision** — false
    promotion **0.13–0.35** against CA's measured **0.097** — **and available now.** M1 is
    credited with nothing (conditional on the FTMO admission being luck, the redacted_account archive
    would likely reproduce it). The recommended tightening reaches **≈ 0.05**, better than CA's
    *and* still available this week.

11. **`book_owner.__init__` assigned two fields twice**, and two different kwargs were both
    called "the fourth" — wave-13 hand-merge residue. Behaviour was unchanged, which is why it
    survived; the commission's instruction to verify the composition **at the call sites**
    rather than by reading the signature is what found it.

---

## 1. What was built

| deliverable | where |
|---|---|
| **CE-1** the spread-floor activation carry | `phase15/activation_carry_spread_floor/` — MANIFEST, 4 payloads, diffs, `verify_carry.py`, `build_carry.py`, `SPREAD_FLOOR_CEREMONY.md`, dry-run + recent-fold receipts |
| **CE-2** the entry-hour lever, default-off | `src/components/ultimate_book/entry_hour.py`, `book_engine._entry_hour_deferral`, `run_book.py --entry-hour`, 35 tests, `CE_ENTRY_HOUR_ACTIVATION_DOSSIER.md`, `CE_ENTRY_HOUR_V1.json`, identity receipt |
| **CE-3** the weekend recommendation | `phase15/CE_WEEKEND_POLICY_RECOMMENDATION.md`, `CE_BA_H1_RETIREMENT_V1.json` |
| **CE-4** promotion restated + the amendment path | `phase15/CE_PROMOTION_HISTORICAL_FIRST.md`, `CE_MX_PROMOTION_AMENDMENT_V1.json`, `IncubationRegistry.amend_rules()`, 18 tests, agreement §6 language, one registry row |
| **CE-5** | skipped in one line — see §4 |

**Three flags now compose on one constructor** (`--frontier-exits`, `--spread-geometry-floor`,
`--weekend-flat`, `--entry-hour`), each default-off, none a config key, so no activation token's
digest can move.

**The one doctrine this session added.** The spread floor fails **closed**; the entry-hour lever
fails **open**. Both are right: **fail closed when the failure mode is a breach; fail open to
the committed contract when it is a missed improvement.** An unpriceable leg is the pathology
the floor exists to prevent; a dark clock on the entry lever means only that the improvement
did not apply, and deferring forever would silently disarm an armed sleeve. Every fail-open is
counted, never silent.

---

## 2. A/B

**0 bad → 0 bad, 0 regressed, 846 → 846 passing on a shared 37-file scope, +53 net new
passing.** Tool-emitted `gtos-ab-receipt-v1` fence at
`receipts/session_ce_ab/SESSION_CE_AB.md`, with `SCOPE_NOTE.md` beside it explaining why the
scope is 37 and the change touched 39 (the two new test files cannot exist on the before side;
`--scope-difference-justification` was available and deliberately not used — re-running the
after side on the shared scope is a *real* comparison, and a justification is a reason to
accept a weaker one).

The before side is a **full** copy-back: all 8 modified paths restored to `e19a2bb49`, all 26
added paths removed. It reproduces the ZERO baseline exactly.

---

## 3. What I got wrong

1. **I built the whole carry against the wrong host bytes and only caught it by reconstructing
   the host.** `book_engine.py` is in Session AC's manifest at `copy_order: 3`; I read AZ's and
   S's manifests, saw no mention, and concluded the host was at the lineage. The manifest would
   have shipped a `sha256_before_expected` that fails preflight on a funded machine — which is
   the *good* outcome; the bad one is a verifier reading "not carried yet" and an operator
   copying anyway. Found by building a reconstructed host tree from **all three** manifests
   before writing the verifier, not by reading more carefully.

2. **My first identity proof was vacuous and printed PASS.** It ran against a fake broker with
   no bars, generated zero intents on both sides, and compared two empty lists. The receipt
   script now asserts the fixture produced intents and **refuses to report PASS** if it did not.
   An identity proof that cannot fail is not evidence.

3. **My conviction-count gate compared a dict to an int and crashed.** `update_and_count`
   returns `{decision_day: count}`, not a count — the same shape that made one of Session AY's
   own fixtures vacuously true. Caught by running the gate rather than by reading the callee.
   It now asserts the shape first, so a future change of it fails loudly here.

4. **I dropped CD's in-flight block range as DEAD and the guard immediately proved it ACTIVE.**
   I reasoned that my ceiling move to B2340 put CD's `B2250–B2299` below the ceiling with
   nothing citing it. `B2250` is cited as an individual token in **six** files. The class of an
   in-flight entry is not something to derive from where the ceiling sits — the guard computes
   it, and I should have let it. Restored as ACTIVE; CD owns retiring it.

5. **My first copy-back restored only the changed source files and produced a phantom
   failure.** `IMPLEMENTATION_STATE.md` at HEAD against the base's block-guard test is a mixed
   state belonging to neither side; it reported 1 failed. The correct copy-back restores every
   path in `git diff --name-status`. This is B2231's landmine with a different trigger, and it
   would have read as "your change broke the block guard."

6. **My symbol loader silently mapped 39 of `sub_mid_dn_revert`'s hour-00 trades to "no
   feed".** The archive spells the cash indices and oils with an underscore (`UKOIL_cash`) and
   the trade rows with a dot (`UKOIL.cash`). An absence produced by a filename convention,
   reported as a data gap — the exact shape AQ's own "corrected 2026-07-30" note warns about.
   Fixed for re-punctuation only; a genuine rename (US500 → SPX500?) is left unmapped and
   counted honestly rather than guessed.

7. **I priced the skipped-hour target breach at 5R for every sleeve for one run.** That is
   `mx_btcusd @ target_5R`'s contract and nobody else's. It now reads each trade's own
   `target_dist` and skips the check where there is none.

8. **I wrote "249 of 457" into the ceremony page and 457 was invented.** The two arms score
   different denominators (325 control against 208 filtered, because `era_population.apply`
   runs per arm after the drop), so that row cannot be a fraction at all. Corrected to the bare
   count with the reason attached.

---

## 4. Handoff to the orchestrator

1. **`phase15/activation_carry_spread_floor/SPREAD_FLOOR_CEREMONY.md`** is the ceremony page.
   Preflight → backup → carry in `copy_order` → `--check all` → `--spread-geometry-floor
   sub_mid_dn_revert,sub_xvol_pullback` at a decision-day boundary. **Read §0.1 first** — the
   host's `book_engine.py` provenance is the thing this package corrects.
2. **`phase15/CE_ENTRY_HOUR_ACTIVATION_DOSSIER.md`** recommends arming the entry-hour lever on
   **nothing today**, and the reason is a fetch: `mx_btcusd` has no premium to save and
   `sub_mid_dn_revert` has seven measurable trades. **Price the M15 capture for the five JPY
   crosses** — it is the single measurement that would decide a 27.6 %-of-sleeve exposure on
   armed money. The cheap half (a `.timebase.json` sidecar on four existing H1 files) is a
   day's work and buys USDJPY and GBPJPY.
3. **`phase15/CE_WEEKEND_POLICY_RECOMMENDATION.md`** asks for four owner decisions and
   recommends arming nothing today. **OD-BA-0 and OD-BA-1 are answerable this week** and worth
   28.3 % of the policy's bill; answering them after the pass means paying the difference for
   however long the ticket takes.
4. **`phase15/CE_PROMOTION_HISTORICAL_FIRST.md`** — M1 and M2 are runnable now, four declared
   looks, and `mx_btcusd`'s promotion question is answered instead of scheduled. Take the
   tightening if `mx_avausd` is evaluable; if it is NOT_EVALUABLE, record the milestone
   UNREACHABLE rather than quietly using the looser form.
5. **CE-5 skipped.** `data/mt5_research_exports/bridge_ftmo_vp_m1_backfill_20260731/` does not
   exist at session end; the orchestrator owns the fetch and `vp_euidx_pocgrav` stays
   undecided. No gate was run for it and none is claimed.
6. **CD is still in flight and its `IN_FLIGHT_WAVE_RANGES` entry is ACTIVE**, restored by this
   session after it wrongly dropped it. CD owns retiring it. This session raised the ceiling to
   B2340, so a dangling citation inside `B2250–B2299` will now be named at CD's merge.
7. **Two things this session filed rather than fixed.** The exact bootstrap for P1-HIST's
   false-promotion number (a null preserving cross-member correlation), and the live/research
   divergence on metals at broker hour 00 — the research entry price is a bar close on an
   instrument that is not quoting, and the live book would fill at the session reopen.
