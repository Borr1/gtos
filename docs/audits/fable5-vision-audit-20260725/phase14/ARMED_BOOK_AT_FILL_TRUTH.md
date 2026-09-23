# The armed book at fill truth — one page, read against the monitor

**For Borhen. 2026-07-31, Session CA.** Nothing here arms, pulls, sizes or promotes anything.
Every number is measured; the receipts are `phase14/receipts/CA_FILL_TRUTH_RESTATE_V1.json`
and `CA_FIRST_WEEK_V1.json`.

---

## 1. What is armed right now, and it is not the same book on both accounts

| | FTMO | redacted_account |
|---|---|---|
| sleeves | `crypto`, `energy_agri`, `sub_xvol_pullback`, `sub_mid_dn_revert`, **`mx_btcusd` on `--frontier-exits` (target_5R)** | the same four, **no frontier** |
| since | 2026-07-31 ~01:26 UTC | 2026-07-30 ~14:57 UTC |
| receipt | `phase13/receipts/MX_ACTIVATION_20260731.md` (host `d6c9c4b19`) | `phase8/receipts/FXJPY_PULL_20260730.md` (host `7017c6745`) |

`fx_jpy` is out on both. Session BB's fill-truth numbers were measured on the four; the
five-sleeve FTMO book is measured here for the first time.

---

## 2. Cadence — what the book will actually do

Measured on the only window where every armed symbol exists (2024-10-29 … 2026-07-27, set by
DASHUSD's H4 start — availability, never results).

| | archive convention | **fill truth** | inflation |
|---|---:|---:|---:|
| **FTMO** fills / week | 3.25 | **1.67** | 1.94× |
| **FTMO** book-days / calendar month | 7.77 | **5.09** | 1.53× |
| **redacted_account** fills / week | 2.51 | **1.39** | 1.81× |
| **redacted_account** book-days / calendar month | 5.64 | **4.23** | 1.33× |

The gap is the live placement guard: **one open position per broker symbol across the whole
book**, plus a per-(sleeve, symbol, day) dedup. A blocked signal is dropped, never queued.

**FTMO's book suppresses 41.4 % of its decisions; redacted_account's 32.1 %.** The difference is
the fifth sleeve — see §4.

---

## 3. Per-sleeve, and this is where it bites

| sleeve | account | archive decisions | live fills | **suppressed** | live fills/week |
|---|---|---:|---:|---:|---:|
| `crypto` | FTMO | 181 | 71 | **60.8 %** | 0.30 |
| `crypto` | redacted_account | 181 | 94 | 48.1 % | 0.34 |
| `energy_agri` | both | 67 | 42 | 37.3 % | 0.14 |
| `sub_xvol_pullback` | both | 88 | 35 | **60.2 %** | 0.07 |
| `sub_mid_dn_revert` | FTMO | 533 | 414 | 22.3 % | 0.49 |
| `mx_btcusd` @ target_5R | FTMO | 318 | 134 | **57.9 %** | 0.27 |

**`crypto` lost 12.7 points of fill rate on FTMO the moment `mx_btcusd` was armed** (48.1 % →
60.8 % suppressed). Both trade BTCUSD, and the book holds one position per broker symbol.
That is not a fault; it is the price of the fifth sleeve, and it had not been measured.

**`sub_xvol_pullback` fires about 3.7 times a year live.** It has the highest per-trade gross
R in the book, and any figure quoted for it on an archive decision count is 2.5× the fills it
will produce.

---

## 4. The frontier contract costs the book fills — a number nobody had

`mx_btcusd` runs at `target_5R`, which holds trades longer than its committed 2R contract.
Longer holds occupy BTCUSD for longer:

| FTMO book with `mx_btcusd` at… | book fills | mx's own fills | `crypto` fills lost |
|---|---:|---:|---:|
| its committed **2R** | 747 | 180 (43.4 % suppressed) | 18 |
| the armed **target_5R** | **696** | **134 (57.9 %)** | **23** |

**The frontier costs the book 51 fills, 6.8 %.** It is still the right contract on the
economics — 2R rejects at all four bands and 5R is the estate's only admission — but the
cadence price is real and it is paid mostly by `mx_btcusd` blocking itself.

---

## 5. What this does to the published %/month — the honest answer is "less than you'd think"

Session BB warned that its 1.33× must **not** be applied to `BOOKS_MC_V1`'s rows, and it was
right. CA closed that question, and the answer is a proof rather than a correction:

- The only clause the W7 recost caches can express is the **day key**, and it **cannot move
  `book_days` at all** — it keeps the first row of every (sleeve, symbol, day), so no day can
  be emptied. Measured: 382 → 382, 173 → 173, 117 → 117.
- Clause isolation on the archive, where **both** clauses can run: day-key alone costs 164
  fills and **zero** book-days; symbol-occupancy alone costs **89** book-days.

**So the whole calendar-clock effect belongs to the clause the caches cannot express, and no
arithmetic on them can produce a corrected `%/month`.** The economic half is *bracketed*, not
corrected: keep-first gives 5.370 %/mo, keep-last 4.537, and the published 4.955 sits between
them — the sign is set by an intra-day ordering the cache does not record.

**Practical reading: keep using the published 4.955 %/month for the cache cell, and know it
is uncertain to about ±0.42 %/month for a reason that is not fixable from those files.** The
number to treat as the expected case remains the out-of-window one CLAUDE.md already gives
(+0.100 %/month over ten years), not either of these.

---

## 6. The stop conditions still hold — but their calendars are years

No threshold moved. Every one is denominated in R or in fills, and a fill is a fill. What
moved is **how long before any of them can say anything**, at the true fill rate:

| condition | needs | `crypto` | `energy_agri` | `sub_xvol_pullback` | `sub_mid_dn_revert` | `mx_btcusd` |
|---|---|---:|---:|---:|---:|---:|
| S1a risk floor | ~12 fills | 9.3 mo | 19.1 mo | 38.7 mo | 5.9 mo | — |
| S1b evidence floor | 60 fills | **46.7 mo** | **95.6 mo** | **193.5 mo** | 28.4 mo | **51.2 mo** |
| S2 gross negative | 20 fills | 15.6 mo | 31.9 mo | 64.5 mo | 9.5 mo | 17.1 mo |
| S5 stop-out run | 9 in a row | 7.0 mo | 14.3 mo | 29.0 mo | 4.3 mo | 7.7 mo |

(FTMO column; redacted_account is similar and slightly faster on `crypto`.)

**Only `sub_mid_dn_revert`'s risk floor can fire inside an evaluation window.** Everything
else is a multi-year instrument. That is not an argument to loosen them — it is the honest
statement that **the live stream cannot be the evidence base on this cadence**, and the
estate should stop expecting it to be.

---

## 7. What to do about the monitor, today

1. **`scripts/book_sleeve_telemetry.py` is now correct for two different books.** Its S6
   check took one flat list of expected `--tags`; it would have fired CRITICAL on both
   accounts against a correct host read, because the list still held `fx_jpy` and not
   `mx_btcusd`. Fixed, per account, with the ceremony receipt named for each.
2. **`mx_btcusd` now has stop rules and a promotion rule** (`phase14/receipts/CA_MX_INCUBATION_V1.json`).
   It had none — it went live with no risk floor, no evidence floor, no carry alert. Written
   after the arming, which is the wrong order and is recorded as such.
3. **The silence alarm's 15 / 22 sessions belong to BB's four-sleeve book.** FTMO's five fill
   1.67/week against the four's 1.39, so FTMO's true warn threshold is *tighter*. The tool
   correctly reads its thresholds from the receipt and refuses to invent one; re-deriving
   them for the current sets is a routed handoff, not something to eyeball.
4. **Do not read the first week.** Expected fills since each account's current set took
   effect: **0.105** (FTMO) and **0.174** (redacted_account). Zero fills is what a healthy book
   looks like right now, 90 % and 84 % of the time.
