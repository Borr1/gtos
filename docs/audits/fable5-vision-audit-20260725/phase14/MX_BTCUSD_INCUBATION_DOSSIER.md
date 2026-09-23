# `mx_btcusd` — the incubation dossier that should have existed before the ceremony

**For Borhen. 2026-07-31, Session CA.** Nothing here arms, promotes or re-weights anything.
Receipt: `phase14/receipts/CA_MX_INCUBATION_V1.json`; the rules are wired into
`phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json` as ADDED rows.

---

## The uncomfortable part first

`mx_btcusd_d1_donchian_20_breakout` has been trading real money on FTMO since **2026-07-31
~01:26 UTC**, and until this session `FIVE_SLEEVE_STOP_CONDITIONS_V1.json` carried **no row
for it at all** — no risk floor, no evidence floor, no carry alert, no hold-time alert, no
promotion rule.

The Training Lane you ratified the same day says, in §4: *"Each incubant carries pre-registered
stop AND promotion rules, written before arming."* The arming came first. The rules below are
written after, and nothing about them was fitted to a live fill — **there are none yet**, and
there is not expected to be one for about four days. But the order was wrong, and the record
says so rather than quietly reading as if it were not.

---

## What it is and why it is armed

The estate's **only** admission at the sealed α: RECORDED population, `B_balanced` α 0.10,
corrected against `CANDIDATE_BOOK_V1`, **admits at two of three cost bands**. Contingent on two
repairs, both now on the host — AQ's time-stop unit (96 was the M15-per-D1 *ratio*, not a
horizon) and AU's `--frontier-exits` wiring, proved trade-by-trade identical to the research
cell.

Registry confidence **0.025** — 0.32 % of book weight, economically small **by design**. AI
measured that admitting it at this weight is inert. The forward record is the point.

**Planning number: +0.198 R/day** — the *recent* folds, per the ratified rule's sizing clause.
Never the +0.982 full-window mean: AN measured a 7.6× chronological decay on this admission,
and no gate can see decay by construction.

---

## The rules, derived rather than chosen

Every input comes from **one** object — the gate's own `diagnose=True` cost decomposition at
the ratified rule on the `target_5R` contract the book actually runs, which reproduces the
standing admission exactly (n 232, +0.982 R/day, p 0.0011). The formulas are Session AS's,
imported rather than retyped.

Measured basis: gross **+1.0241 R/trade**, cost ex-swap 0.0439, swap 0.2228 (11.94 nights
mean), **net +0.7574 R/trade**; dispersion sd 2.700 over 232 trades; median hold 120 h,
82.3 % of trades over 24 h.

| rule | threshold | what a trip means | measured false-alarm rate |
|---|---:|---|---:|
| **S1a** risk floor | cumulative net **−9.089 R** | you have paid what you pre-registered. Says nothing about the sleeve. | 0.070 |
| **S1b** evidence floor | cumulative net **−9.09 R** | the sleeve is *not* running at its archive expectancy | 0.070 |
| **S2** gross negative | 20 fills, ≥8 day blocks, both weightings | losing before cost — no cost model can rescue it | — |
| **S3** carry surprise | alert **34.0** nights / stop **40.6** | the tier restatement is void | — |
| **S4** hold surprise | alert above **360 h** (3× the 120 h median) | the published economics describe a different contract | — |
| **S5** stop-out run | alert 6, stop 9 in a row | — | — |
| **P1 promotion** | cumulative net **+34.0 R** | luck alone is an unlikely explanation | 0.097 |

Action on any stop: **remove from `--tags` on FTMO** — the orchestrator's ceremony, and it
never needs a flatten (a de-tagged sleeve's open position stays adopted and exit-managed).
Never reach for `live_broker_authority: false` (H8).

**P1 is the mirror of S1b**: the shallowest 0.5 R step a sleeve with true mean *zero* reaches
within 60 fills with probability ≤ 0.10. Reaching it authorises a request to you to move the
sleeve off 0.025 toward the 0.05 incubation ceiling. Nothing automatic.

---

## The two numbers that should shape your expectations

**1. It fills about once every 3.7 weeks.** 318 archive decisions become **134** live fills —
**57.9 % suppressed**, because the book holds one open position per broker symbol and this
sleeve trades BTCUSD, which `crypto` also trades. At its committed 2R contract the suppression
would be 43.4 %; the frontier's longer holds cost it 46 of its own fills and cost `crypto` 5
more. Long silences are the design, not a fault.

**2. The promotion rule is ~51 months away at that rate**, and the evidence floor ~51 months
too. That is the honest price of promotion on live evidence for a sleeve this quiet. It is an
argument for finding a cheaper instrument — not for loosening the threshold, which would just
make the answer wrong faster.

---

## One hazard to clear before this sleeve holds a position for long

`mx_*` sleeves now ask the terminal for **7,744 M15 bars per tick**. If the terminal returns
fewer than 7,680 *closed* M15 bars, the count can never reach the budget and **the time stop
never fires at all** — inert, not late, and the wall-clock fallback does not catch it (that
path needs `None`, not a short count). This is the first sleeve of its cohort ever armed.
**Measure the terminal's `copy_rates` ceiling.** The broker-side SL/TP set at entry survive
regardless, so a position is not naked; what would be lost is the horizon.
