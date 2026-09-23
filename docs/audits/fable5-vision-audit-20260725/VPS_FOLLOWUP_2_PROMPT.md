# VPS follow-up #2 — what the tick pull missed, plus the daily-reset rule

Copy between the markers into the VPS session.

---

--- BEGIN ---

The tick pull landed and verified clean on the Mac: **19/19 files, all sha256 match.** Thank you.

Four things, all read-only. **Change nothing, restart nothing, don't touch flags or git.**

## 1. Your timestamps are broker time, labelled UTC — please confirm and re-label

`TICKS_MANIFEST.jsonl` calls its fields `first_tick_utc` / `last_tick_utc`, and the CSV `time` column
is epoch seconds decoded as UTC. **They are not UTC — they are FTMO server wall clock (UTC+3 in that
window).** Measured on the Mac two independent ways:

- the FX week boundary across 9 pairs sits at **Fri 23:54 → Mon 00:05 as stamped**, whereas the true-UTC
  FX week is Fri 21:00 → Sun 21:00. Implied offset **+2.85 to +2.92 h** (median +2.91 — that is +3 h
  less the few minutes between the last tick and the 17:00 New York close);
- EURUSD tick density peaks at stamped hour 17, which is 14:00 true UTC.

This is finding F7 and it is not your mistake — `datetime.fromtimestamp(rec["time"], tz=utc)` is what
the whole repo did until last week. MT5 hands back the broker's wall clock and decoding it *as* UTC
produces a stamp that claims UTC and is not.

**What I need:** confirm from your side (`mt5.symbol_info_tick()` vs `datetime.utcnow()` gives the live
offset directly), then re-emit the manifest with the fields renamed `first_tick_broker` /
`last_tick_broker`, plus a `broker_clock` block naming the server and offset. Do **not** rewrite the
CSVs — the raw broker epochs are the honest record and the Mac corrects on read. I only need the
labels to stop asserting UTC.

## 2. Seven surface symbols did not arrive

Present: AUDJPY AUDUSD AVAUSD BTCUSD ETHUSD EURUSD GBPJPY GBPUSD GER40.cash JP225.cash NZDJPY NZDUSD
UK100.cash US100.cash US30.cash US500.cash USDCAD USDJPY XAUUSD.

**Missing, and these are disproportionately what the metals and FX-cross sleeves trade:**
XAGUSD, EURJPY, CHFJPY, EURGBP, USDCHF, and both oils (USOIL/UKOIL — whatever they are called on the
terminal). Same window, same format. If a symbol genuinely does not exist on the terminal, say so
rather than substituting a near-match — a silent substitution is worse than a gap.

## 3. Same window from **redacted_account** as well

The export is FTMO-only. redacted_account ticks matter for a specific open question: redacted_account's DST
calendar is unmeasured, so `src/utils/broker_clock.py` **refuses to resolve it** rather than assume it
matches FTMO. Any window spanning a DST transition settles it; the shadow window alone still helps.

## 4. NEW, and the most valuable item — the daily-reset rule for both accounts

This drives the daily-loss guard on a funded account, and the repo currently disagrees with itself
(one component resets on MT5 server midnight, another on Prague midnight — 1–2 h apart).

For **each** terminal, report:

- `account_info()` in full — especially `server`, `company`, `currency`, `leverage`, `margin_mode`;
- the **server's own current time** vs UTC, from a fresh tick: `symbol_info_tick("EURUSD").time` (and
  `time_msc`) alongside `datetime.utcnow()`. This is the live offset, measured not inferred;
- whatever the terminal or the firm's own materials state about **when the daily loss limit resets** —
  server midnight, 00:00 CE(S)T, 00:00 GMT, something else. FTMO's rule is recorded here as
  `00:00 CE(S)T`; **redacted_account's is documented nowhere**, which is the actual gap.
- if there is any per-day equity/balance snapshot the terminal keeps (daily summary, statement rows),
  the timestamps of the last ~10 day boundaries would let me *measure* the reset instant rather than
  take it on documentation.

## 5. The depth probe — still not done, third time asking

Metadata only, **no bulk export**. Per symbol, per broker: earliest and latest timestamp
`copy_rates_range` actually returns for M1/M15/H4/D1, and the same for `copy_ticks_range`, plus whether
ticks are real `COPY_TICKS_ALL` or synthesised from bars, and approximate tick rows per month from one
or two sampled months.

**The question: does FTMO serve ticks deeper than 2025-10?** It has been unknown twice because earlier
probes were lost. One JSON is the whole deliverable. Use small windows.

Send over host-mesh as before.

--- END ---

---

## Context for the Mac side, not part of the prompt

- Item 4 is new and outranks the rest. `governor_state.py:60-76` resets the book's daily-loss window on
  the **MT5 server** clock; `dual_broker_execution_follower.py:919-932` resets on **Europe/Prague**.
  Measured gap: 1 h normally, **2 h across 2026-03-10..03-28** — inside the sealed March window. FTMO's
  documented rule (`config/profiles/ftmo.yaml:102`) is `00:00 CE(S)T`, so the governor is the wrong one
  and it resets **early**, which is the dangerous direction.
- Item 1 costs the VPS nothing and stops the next reader trusting an `_utc` suffix. Gap #9 of the
  clock-truth note is the same trap in `25_data/raw/XAUUSD_M15.csv`, which carries `Z`-suffixed
  broker stamps.
- Item 5 is a Phase-5 concern; nothing before it needs ticks. Sizing, measured: ordered tick truth is
  ~0.42 GB per symbol-month in export format, so a full 2-year × 24-symbol pull is ≈242 GB. The Mac now
  has **93 GiB free** after the D1 demotion (was 29 GiB), so a targeted pull is finally feasible —
  but only once the probe says what exists.
