# Day keys in the live book — what they are, which one `SleeveBookPolicy` uses where

**Session H deliverable 4.** Written 2026-07-26. Every claim below is `[MEASURED]` from source at
HEAD or from the VPS runtime-learning packets unless tagged otherwise.

`SESSION_H` says the live book "currently uses **three different notions of 'day'**". It uses **nine
independently computed ones**, and the count matters, because two of them disagree *inside a single
decision cycle* and that disagreement moves real position size.

---

## 1. The nine

| # | notion | definition | `file:line` | what it decides |
|---|---|---|---|---|
| 1 | **Decision day** — signal bar's **UTC** date | `dt.astimezone(utc).strftime("%Y-%m-%d")` | `bar_provider.py:86-88` | `TradeIntent.decision_day`; the correlated-risk-unit bucket (`admission.py:1113`); the Kelly-lite per-day count (`:1105`); the running-conviction store key (`book_engine.py:779`); both placement caps (`book_owner.py:1602,1613`); every ledger day key |
| 2 | **Sleeve server-local day** | `to_server_local(t).date()`, offset `broker_clock.NEW_YORK_PLUS_7` | `sleeves/_server_clock.py:91-98` | prior-day highs/lows, Asian range, opening range, session grouping in the eight B29 sleeves |
| 3 | **Account daily-loss reset day** | `(now_utc + _effective_offset_h(now)).strftime("%Y-%m-%d")` | `governor_state.py:157-160`, offset `:73-124` | the start-of-day balance anchor → `realized_today_pct` → the soft daily stop and the joint gross-cap tightening; `reset_window_date()` |
| 4 | **`fx_jpy`/`metals` own server day** | `_to_server_local(bar_time).date()` — a second implementation of #2 | `sleeves/fx_jpy.py:124-131`, `metals.py:157-158` | `fx_jpy`/`fx_jpy_ny` session bucketing; the A8 `session_hour` feature |
| 5 | **Stress-derisk ladder day** | `today = (now_utc + offset_hours).date()`; deal day `datetime.fromtimestamp(t, utc).date()` | `admission.py:439,446` | `consecutive_loss_days`, `trailing_neg_frac` → the ladder/co-loss size multiplier |
| 6 | **Symbol-damage window day** | same shape as #5 plus `cutoff = today − 5d` | `symbol_damage_guard.py:69,76-77` | the S1 guard — **inert live**: `book_engine.py:741-746` never passes `symbol_damage_metrics` |
| 7 | **Market-expansion "next open" day** | `runtime_now.date()` if available, else `(bar_time + 1d).date()` | `sleeves/market_expansion_d1.py:147-175`, stamped `:217-221` | **overwrites** `TradeIntent.decision_day` for all 14 `mx_*` sleeves |
| 8 | **`vp_euidx` UTC bar date** | `(t.astimezone(utc)).date()` — a `date`, not a string | `sleeves/vp_euidx.py:53-57` | prior-day volume-profile window (clean_3, so not live) |
| 9 | **`vss_fxcross` day string** | `_daystr(t) = s[:10] if len(s) >= 10 else None` | `sleeves/vss_fxcross_london_up_low.py:64-70` | its D1-up-regime gate |

Plus **ten derived truncations of #1** (`str(day)[:10]`) at `placement_ledger.py:94,111,181,221`,
`book_owner.py:608,677,1601,3062`, `runtime_learning_packet.py:239`, `execution_packets.py:218`.
Those are the same notion, re-sliced; they are not separate day concepts.

#2 and #4 are semantically one intent implemented twice. Both now delegate to
`broker_clock.NEW_YORK_PLUS_7`, so they agree numerically today — but they are two code paths that can
drift, and `metals.py:157` imports the `fx_jpy` *private* helper.

---

## 2. Two of them collide inside one cycle, and same-bar units get sized 1.66× apart

**[MEASURED]** over the whole packet stream, keyed on distinct `bridge` states: **12** bridge states
carry two Kelly day-counts in their `would_units`, of which **4** carry two different *multipliers* —
i.e. actually size differently. The other 8 land both counts in the same half-Kelly bin and are
economically inert. Consequential rate: **4 of 884 unit-bearing states = 0.45 %**.

`admission.py:1101-1106` builds `n_active_by_day` from the intents' `decision_day` and `:1144-1148`
resolves the Kelly multiplier once per day key, so a cycle whose intents span two day keys applies two
multipliers to units decided from one `size_correlated_units` call.

**The cause is the UTC midnight boundary meeting per-symbol bar recency.** All four consequential cycles
fire within minutes of 00:00 or 21:00 UTC, and their intents' last *closed* bars straddle a date
boundary:

```
redacted_account 2026-06-19T01:00  asia_pdl_fade M15 bar 06-19T00:45  na=1  x0.748
                            idxrev        H4  bar 06-18T21:00  na=3  x0.991
ftmo       2026-06-24T21:05  vol_compression D1 bar 06-22T21:00 na=1  x0.748   (bar 2 days stale)
                            idxrev          H4 bar 06-24T13:00  na=9  x1.241
                            mx_nzdjpy       D1 bar 06-22T21:00  na=9  x1.241   (re-stamped to 06-24)
redacted_account 2026-06-25T01:00  idxrev GER40    H4 bar 06-24T16:00 na=10 x1.241
                            idxrev UK100    H4 bar 06-25T00:00  na=1  x0.748   <- SAME SLEEVE
ftmo       2026-07-14T01:00  idxrev          H4 bar 07-13T21:00 na=7  x1.241
                            asia_pdl_fade   M15 bar 07-14T00:45 na=1 x0.748
```

The third case decides the diagnosis: **`idxrev` against `idxrev`** — one sleeve, one timeframe, two
symbols whose last closed H4 bars fall either side of midnight. No account of the collision in terms of
timeframes or of the `mx_*` re-stamp can explain it.

Worst observed effect: **×1.241 against ×0.748 on units from the same bar — 1.66×.** Kelly-lite exists
to "bet BIGGER on multi-edge-agreement days" (`admission.py:893-897`); split day keys make it tilt by
which symbols happened to close a bar before midnight.

Filed as **D2** in `SLEEVE_BOOK_DEFECT_REGISTER.md`.

## 3. Which day key `SleeveBookPolicy` uses, where

The policy delegates all sizing to the live path, so it inherits **#1** wherever live does, exactly:

| policy element | day key | note |
|---|---|---|
| `PolicyCandidate.decision_day` | **#1** as produced upstream, including #7's overwrite for `mx_*` | the port does not normalise it — normalising would change risk bucketing |
| correlated-unit bucket | **#1** | `admission.py:1113`, unmodified |
| Kelly-lite day count | **#1** | `admission.py:1105`; the validator supplies the *recorded* count, so the port never re-derives a day key the record disagrees with |
| reactive de-risk state | **#5** in live; **supplied** in the policy | `AccountDayState.cycle["stress_state"]`; the policy cannot recompute #5 because it has no broker deals |
| governor reset window | **#3** in live; **folded into `realized_today_pct`** in the policy | the caller supplies the anchored percentage; the policy never computes a reset date |
| placement caps | **#1** in live; **not applied** | placement, not decision — `sleeve_book.PLACEMENT_GATES` |
| sleeve session grouping | **#2/#4** in live; **not applied** | the policy does not generate candidates in the validated path |

**One notion is deliberately absent from the policy: none.** The policy computes no day key of its
own. Every day key reaching it comes from the candidate or from the caller, which is why the port
cannot silently introduce a tenth.

---

## 4. `bar_provider.decision_day_of` — not changed, and what the evidence says

`SESSION_H` instructs: do not change notion #1 this session. It is not changed. B54 Part 2 records why
it is an owner decision rather than a bug fix: `book_owner.py:1608-1610` calls the cap it drives "the
one-unit-per-cluster-per-day envelope **the dial was certified on**", so moving the boundary changes
which positions count as one correlated unit.

The evidence this session produced bears on that decision. Each candidate fix was **measured** against
the four consequential cycles by recomputing day keys from the recorded bar stamps, rather than argued:

| candidate fix | cycles unified | why |
|---|---:|---|
| make `vol_compression` re-stamp like the 14 `mx_*` sleeves | **1 of 4** | only touches the one D1 sleeve that does not re-stamp |
| key the day off the bar **close** instead of its open | **2 of 4** | fails where a bar is stale by more than one period, and on the same-sleeve case |
| move #1 from UTC to **server** midnight | **0 of 4** | server midnight is 21:00/22:00 UTC — it puts the boundary *through* the D1 close instead of away from it |
| key the day off the **cycle runtime** (what `mx_*` already does) | **4 of 4** | bar-independent, so one cycle has one day key by construction |

Only the last works, and it works because it is the only bar-independent option: no key derived from bar
stamps can unify the `idxrev`-vs-`idxrev` case, where two symbols genuinely have last-closed bars on
different UTC days. The live book already contains this convention — the 14 `mx_*` sleeves use it.

**Risk-envelope consequence of the runtime key, quantified as far as this evidence allows.** It merges
intents that currently split across two `(decision_day, cluster)` buckets into one, so on the affected
cycles it *reduces* the count of independent correlated units — tightening the envelope, the safe
direction. It simultaneously raises the Kelly count for the previously-under-binned unit, raising that
unit's size by up to 1.66×. The net is not one-signed and would need an MC pass on the real book before
it could be called safe. **Not applied here**: it is a sizing change on a funded account and squarely
B54 Part 2.

**Correction recorded.** An earlier version of this note proposed the bar-close key as the fix that
"makes every timeframe agree and removes the special case". Measured, it repairs 2 of 4 and fails on this
note's own headline cycle, because `vol_compression`'s last closed D1 bar was two days stale at that
runtime. Adversarial review caught it.

## 6. Session K — which day key the *generation* port uses, where

**Added 2026-07-27 (Session K, Stage 1.3a).** Session K's deliverable 5 is "a note on which day-key
you used where". The answer is short, because the port's whole design is to not choose: it calls the
production generator loop, so every day key is whichever one live computes.

| where | key | source |
|---|---|---|
| `PolicyCandidate.decision_day` | **notion #1 — the signal bar's UTC date** for 17 of 29 sleeves | `bar_provider.decision_day_of` (`:86-88`), set at `book_engine.py:518`, passed to every generator at `:523` |
| `PolicyCandidate.decision_day` | **the runtime wall-clock date** for the 12 market-expansion sleeves | `market_expansion_d1.next_open_decision_day` (`:147-161`), overriding the bar day at `:217-221` |
| `PolicyCandidate.features["bar_decision_day"]` | notion #1, always | the port preserves the bar-derived day even when the generator overrode it, so the two are separable downstream |
| `PolicyCandidate.decision_bar_iso` | the bar's UTC timestamp | `book_engine.py:535` |
| inside sleeves (prior-day highs, Asian ranges, opening ranges) | **notion #2 — FTMO server-local date, NY+7** | `sleeves/_server_clock.py:91-98`; `fx_jpy.py:157` carries its own copy |
| the replay clock driving each cycle | true UTC, supplied by the caller | `GenerationPort.generate(now_utc)` |

**Three things worth stating explicitly, because they cost time to establish:**

1. **`decision_day_of` was not changed**, per the standing instruction and B54 Part 2. The port
   consumes it as-is.
2. **The market-expansion override is the one that breaks replay**, and it is recorded as **D13** in
   `phase3/GENERATION_PORT_DEFECT_REGISTER.md` rather than fixed. It is a *different* decision from
   B54 Part 2 — that one is about re-keying notion #1 globally; D13 is about 12 sleeves taking a key
   from the wall clock instead of from any bar at all. Both are owner decisions; neither is settled
   by the other.
3. **The bar-close grid is broker-aligned, not UTC-aligned**, and this is a day-key-adjacent trap
   that bit this session twice. FTMO H4 bars close at UTC 21/01/05/09/13/17 (NY+7), so a bar
   "on 2026-06-18" by broker reckoning can carry a UTC `decision_day` of 2026-06-17. That is not a
   tenth notion — it is notion #1 observed on a grid that is not aligned to it — but it produces the
   same class of off-by-one, and it is why `CsvBarSource` converts broker-local → UTC at load and
   refuses any file without a declared timebase.

## 5. Cross-references

- `SLEEVE_BOOK_DEFECT_REGISTER.md` — D2 (this collision), D7 (`derisk_start_dd_pct` inert), and the
  rest.
- `SLEEVE_BOOK_POLICY_VALIDATION_RECEIPT.md` — the 12 cycles are the `MULTI_DAY_KELLY_IN_ONE_CYCLE`
  and two-date `decision_day_not_unique` classes.
- `IMPLEMENTATION_STATE.md` **B94**.
- B54 Part 2 (`IMPLEMENTATION_STATE.md:1623-1652`) — the standing owner decision on notion #1.
