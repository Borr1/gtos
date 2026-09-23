# Clock truth — what a sealed receipt means, and what it does not

**Phase 1 Session B, 2026-07-26.** One page for whoever reads a sealed B7.5 receipt next year and needs
to know which of its numbers survive finding F7.

---

## 1. The correction, in one line

Every "UTC" timestamp in the research bar and tick archive is the **FTMO server's wall clock**, which is
UTC+2 or UTC+3. That much both audits had right.

**What they had wrong is the calendar.** F7, `FULL_VISION_PLAN.md` item 5, this session's own brief, and
`scripts/session_volatility_monitor.py:39-44` all state EET/EEST — the *European* DST calendar, last
Sunday of March and October. Measured, it is the **US** calendar: second Sunday of March, first Sunday of
November. Equivalently and exactly:

> **broker server wall clock == `America/New_York` wall clock + 7 hours**

which is the standard MT5 prop-broker convention — it pins server midnight to the FX close at 17:00 New
York, so the daily bar boundary never drifts against the market.

The two calendars agree for ~48 weeks a year and disagree for **~3 weeks each spring** (the US springs
forward first) and **~1 week each autumn** (the EU falls back first). In those windows an EU-calendar
correction is wrong by exactly one hour. This is not hypothetical: `25_data/historical/US30_cash_M15.csv`
on the VPS **has already had an EU-calendar correction applied** and is an hour off in every disagreement
window while correct everywhere else.

### Evidence [MEASURED]

Five methods. They rest on **three independent exchange calendars** (NYSE, Europe, Tokyo) plus two
references outside the broker entirely. Note that only the ~20 trading days a year inside a
disagreement window are informative at all — everywhere else the two hypotheses predict the same thing,
so a measurement there is not evidence either way and is not counted as such below.

| # | Method | Result |
|---|---|---|
| 1 | **Exchange-anchored step probe**, `data/historical_2026/` — a cash open is an auction, so volume *steps* discontinuously at a fixed point in *its own* exchange's calendar | JP225 (Tokyo, **no DST**) steps at broker 02:00 through 2026-03-06 and 03:00 from 2026-03-09. GER40/UK100 step at broker 10:00 when the calendars agree and **11:00 in both disagreement windows**. NYSE-anchored SPX500/US30/NAS100 never move. The three-regime signature winter/disagree/summer is **02:00 / 03:00 / 03:00** and **10:00 / 11:00 / 10:00** — non-monotone, which refutes the EU calendar (predicts 02:00/02:00/03:00 and 10:00/10:00/10:00) and a broker-fixed artifact (predicts constancy) at the same time. |
| 2 | **Same probe on raw broker stamps, 4.25 years** (`24_exports/multi_instrument/US30_cash_M15.csv`, 99,999 bars, 2022-01→2026-04) | **Nine transitions, every one on the US date, none on an EU date**: 2022-03-14, 2022-11-11, 2023-03-13, 2023-11-15, 2024-03-13, 2024-11-04, 2025-03-13, 2025-11-03, 2026-03-09 (first trading day after each US switch). |
| 3 | **Sierra Chart CME/CBOT/COMEX futures**, decoded UTC-native from `.scid` (`scripts/inspect_sierra_scid.py:22,64`) and never touched by any broker-offset code — cross-correlation of M15 log-returns, no calendar assumed on either side | Broker lag **+3.00 h** inside 2026-03-09..27 on all five instrument pairs (r = 0.837–0.998) and inside 2025-10-27..11-01 (r = 0.999). US predicts +3; EU predicts +2. |
| 4 | **A second broker's archive** (the HuggingFace XAUUSD file) which *does* run the EU calendar | FTMO leads it by exactly 1 h in exactly the disagreement windows, across four of them (2024 autumn, 2025 spring, 2025 autumn, 2026 spring). |
| 5 | **CME daily maintenance break**, a structural hole rather than a statistical peak | Sits at broker 00:00–01:00 on 67/67 disagreement dates. |

Two alternative explanations were tested and are dead. The **broker's own tradable session** cannot
produce the shift: it is fixed at broker 01:00–23:45 in all three regimes for all four instruments and
never moves across any transition, while the anchor step does. And the **fold/ambiguity** concern is
empirically absent — 99,999 raw bars over 4.25 years contain zero weekend bars and zero bars in a skipped
or repeated New York hour, because both US transitions occur at 02:00 New York on a Sunday, inside the
FX weekend.

Reproduce methods 1–2 with `python3 scripts/measure_broker_clock_offset.py --data-dir <dir> --check
FTMO-Server3`: 99.3 % of 146 days on `data/historical_2026` (GER40 100 %), 94.4 % of 1,096 days on the
4.25-year file, where the residual is single-anchor estimator noise on individual news days rather than
any regime disagreement.

**No declaration exists anywhere**, in either direction — MT5 stores no server timezone on disk, and the
09_mt5_api pull used `symbol_info()`, which carries no session tables. Every EU/EET statement in the tree
is an internal assertion, and all trace back to one non-discriminating test that took the *median Friday
close hour* over a whole file and subtracted 21 — a statistic that cannot resolve a calendar, because the
Friday close is anchored to the broker's own clock. The repo had in fact already flagged the open
question in its own words at `src/components/ultimate_book/sleeves/fx_jpy.py:40-45`: *"if FTMO anchors to
the US calendar instead of the EU calendar, ~3 weeks in March and ~1 week around end-Oct/Nov could shift
the boundary by 1h."* It then guessed EU.

---

## 2. What a sealed receipt still means

**Unaffected — trust these as written.**

- **Every arm-vs-arm contrast inside the sealed campaign.** All four arms (S0R0/S1R0/S0R1/S1R1) consumed
  the same bars with the same shift, so the selection–sizing decomposition — which is what B7.5 exists to
  measure — is untouched. The shift is a common-mode term and it cancels.
- Total return, drawdown, trade count, win rate, R multiples, per-arm fingerprints, contract hashes.
- Anything indexed by *bar sequence* rather than by wall-clock hour.

**Caveated — do not quote these as real-world statements without re-deriving.**

- **Session-level attribution.** "This edge lives in the London session" means "in bars the config
  labelled london". That label was the broker window 07:00–13:00
  (`broader_origin_generators.py:66-110`), which in true UTC is **04:00–10:00Z in summer and
  05:00–11:00Z in winter** — against a real London cash session of 07:00–15:30Z (summer) / 08:00–16:30Z
  (winter). So the window opened about three hours before London and closed mid-morning: it is mostly
  the Asia tail plus the European open, not London. Every per-session P&L split, session heat-map and
  kill-zone attribution inherits this.
- **Session-conditioned learning features.** Anything with a session token, hour-of-day, or kill-zone flag
  in it. This is the reason the plan puts the repair *before* any learning-lane training run: a feature
  fitted on a mislabelled hour transfers into live — which runs a corrected clock — as a 2–3 h error.
- **The three hindsight session-level rejects (R14).** They rejected rules on the behaviour of the wrong
  hours. They are not wrong, but they are unproven.
- **Any live-transfer claim** that reasons from a replay hour to a real-world hour.
- **Day-boundary effects.** A broker day starts at 21:00/22:00 UTC the previous calendar day, so "daily"
  aggregates, daily-reset logic and D1 bars are shifted whole-day objects, not UTC days. **D1 bars are the
  worst case**: the date label itself moves.

**The rule for re-checking one conclusion.** Ask: *does this number change if every bar timestamp moves
back 2–3 hours?* If the quantity is a difference between arms, no — it survives. If it is indexed by
hour-of-day, session name, kill zone, or calendar date, yes — re-derive it by reading the inputs through
`src.utils.research_timebase.read_bars`, which returns true UTC without altering a byte on disk. Do not
audit the whole tree; re-check the specific conclusion you are about to rely on.

---

## 3. The DST seams — and the one the plan got wrong

| Campaign window | Seam inside it | Offset |
|---|---|---|
| **January 2026** development | none | uniform **+2** |
| **March 2026** sealed challenge | **2026-03-08** | +2 for 1–7 March, **+3** from 8 March |
| **April 2026** adverse-development | none | uniform **+3** |
| **May 2026** development | none | uniform **+3** |

The plan and the brief both name **2026-03-29** as the seam inside the sealed March challenge. That date is
inert for this broker. The real seam is **2026-03-08**, three weeks earlier, which puts the split at
1 week / 3 weeks rather than 4 weeks / 2 days. Anyone applying the F7 repair with the EU calendar would
leave **2026-03-09 through 2026-03-28 wrong by one hour** — 15 trading days inside the most decision-bearing
window in the programme, and wrong in a way no existing test detects.

Autumn is the same trap in miniature: the tick window's seam is **2025-11-02**, not 2025-10-26. (The brief's
"2025-10-25" is a third date; the EU transition that year was 2025-10-26, and the broker moved on 11-02.)

---

## 4. The forward-vs-replay join

Forward logs (slippage, pending-lifecycle, runtime-learning packets) are true UTC from 2026-04-28, when the
live path gained `_broker_epoch_to_utc`. Replay data is broker time. A naive timestamp join misaligns by
**8–12 M15 bars**. Phase 6's cost calibration depends on that join being exact, so it must read the replay
side through the view layer rather than parsing the CSV `time` column directly.

One such join already exists and is already wrong:
`scripts/audit_orderflow_limit_intent_reconciliation.py:259,314,431` joins a live `placed_time_utc` against
`data/historical_2026` M1 bars parsed as UTC. Its output artifact is dated 2026-05-02 — after the live path
started emitting true UTC — so it has been joining across the two clocks.

---

## 5. What changed, and what deliberately did not

**Changed.** The three exporters that produce research data now correct broker epochs *and* translate the
request window, and declare the offset per file
(`export_mt5_research_ohlcv.py`, `export_mt5_historical.py`, `export_mt5_research_ticks.py`). The existing
archive is declared rather than rewritten: 96 `.timebase.json` sidecars under `data/historical_2026`, each
carrying the rule and the verification that backs it. `fx_jpy._ftmo_server_offset_hours` — used by the live
`fx_jpy` and `metals` sleeves — moved off the EU calendar onto the measured one.

**Deliberately not changed.**

- **No sealed artifact was rewritten.** Repairing timestamps inside sealed evidence would destroy arm
  comparability and break contract bindings, to fix a defect that cancels between arms anyway. The
  deliverable is a correct going-forward path plus this note.
- **No SHA-contract-bound file was touched**, so no re-seal and no ~16.5 h/window re-run.
  `config/agent_config.yaml`'s kill-zone constants keep their numbers and become *more* correct, not less:
  once replay reads true UTC, `london: 07:00` finally means 07:00 UTC on both sides. The replay parser
  (`wave4r_replay_microstructure.py`) was **not** patched either — correcting the data rather than the
  parser avoids the parser's AST hash feeding `source_batch.py`'s `implementation_root`, which would have
  forced a bundle re-materialisation and a tick-cache wipe.
- **The eight deployed `ultimate_book` sleeves that read a raw UTC hour against a constant commented
  "server hour" were left alone.** They fire **2–3 h late** against the session they were fitted on, two
  of them on an exact `(hour, minute)` match so they hit the wrong bar every day; and each carries a
  second shift in its per-day key (PDH/PDL, Asian range, opening range, daily caps). Full table and
  severity split in `IMPLEMENTATION_STATE.md` B29. Changing which hour a deployed sleeve fires at is a
  trading decision, not a bug fix, and it belongs to the owner. The book holds no broker authority today,
  so the exposure is to the shadow evidence the strategy is being judged on, not to live orders.

---

## 6. Declared gaps

1. **redacted_account's DST calendar is unmeasured.** Its offset is pinned at exactly +3 h for
   2026-06-14..2026-07-25 (72/73 log pairs), a window where both calendars agree. No redacted_account-attributed
   data anywhere spans a disagreement window. `src/utils/broker_clock.py` therefore **refuses to resolve**
   redacted_account rather than assuming it matches FTMO. The research archive appears to be FTMO-sourced, so
   this probably does not touch F7's blast radius — but that was not proven from a receipt. **Cheap close:**
   one read-only `symbol_info_session_quote()` pull for JP225 on both terminals would be a *declaration*
   rather than an inference, and would settle FTMO and redacted_account together.
2. **The rule is verified 2022-01 → 2026-04.** Outside that band it is extrapolated. A broker can change its
   server clock; nothing here would notice except the regression suite, which is why the suite checks the
   archive rather than only the code.
3. **Nine ingest sites still carry the defect** — the probe/inspection scripts
   (`inspect_mt5_history_availability.py:240`, `inspect_mt5_tick_availability.py:285-302`,
   `export_mt5_from_cache.py:74,185`, `research/extract_ohlcv_2022_2023.py:102`,
   `export_mt5_account_history_readonly.py:56`, `mt5_preflight.py:99`,
   `shadow_observer_tick_enrichment.py:146`). They are diagnostics rather than campaign data producers, and
   were left for scope. Any of them feeding a decision should be corrected first.
4. **`scripts/session_volatility_monitor.py` is wrong twice** — it hardcodes the EU DST table
   (`:39-44`) *and* its call site double-corrects. Its published session-volatility conclusions
   ("London unanimously shows W1 > W2 > W3") are unproven. Not repaired: it is a logging-only script and
   repairing it without re-running it would only move the error.
5. **The live sleeve half of F7 is scoped but unrepaired** (§5). Census, deployment status and severity are
   in `IMPLEMENTATION_STATE.md` B29; the decision is the owner's. One sub-gap inside it: the miners that
   produced those constants are not vendored at HEAD, so "the constants are broker hours" rests on the
   measured archive clock plus each sleeve's own comment rather than on the miner itself.
6. **Timezone config is internally inconsistent, independently of this finding.**
   `prop_safe_selector_daily_reset_timezone: Europe/Prague` (`config/profiles/ftmo.yaml:85`) is consumed by
   live code at `scripts/dual_broker_execution_follower.py:919-932` and wins over the numeric offset beside
   it. Europe/Prague is CET/CEST — a third calendar, agreeing with neither. Not touched here; flagged.
7. **`data/historical/` is deliberately left undeclared**, so reading it raises. Copies of that tree
   disagree: this repo's is already corrected, the VPS copy carries an EU-calendar correction. Verify a
   specific copy with `measure_broker_clock_offset.py` and write it a sidecar before using it.
8. **Crypto crosses the DST seam.** BTCUSD/ETHUSD trade through the weekend the transition falls in, so
   the repeated broker hour is reachable for them and MT5 returns the same epoch twice. The conversion is
   defined there (`fold=0`), but an exporter's raw-epoch dedup keeps one of the two bars. Nothing depends
   on it today; it matters for tick-level crypto work.
9. **A third mislabelled data file, outside F7's register.**
   `25_data/raw/XAUUSD_M15.csv` and `25_data/old_huggingface_backup/XAUUSD_M15.csv` (byte-identical,
   `sha256 e730cea3…`) carry **`Z`-suffixed** timestamps that are not UTC — they match FTMO broker stamps
   at lag 0 in every aligned window. A `Z` suffix is a stronger claim than a bare `time` column, so any
   consumer would reasonably have trusted them. Not in scope here; flagged.
