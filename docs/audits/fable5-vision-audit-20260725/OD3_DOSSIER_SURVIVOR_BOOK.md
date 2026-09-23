# OD-3 — the activation-candidate decision

**For Borhen. Prepared 2026-07-29, after wave 3 merged.**
Every number below is read from a committed artifact, with its file named. Nothing is transcribed
from prose.

> **AMENDED 2026-07-29 by Session Q (option D, executed). Read this box before the tables.**
> `phase3/SESSION_Q_MC_TRUE_TARGET_RESULT.md`, artifact
> `research/operations/w7_recost_2026_07_27/MC_FIRM_TRUE_V1.json`, blocks **B230–B244**.
> Four things below changed. Three of them make this document's numbers *better*; the fourth is
> worse and it is the one that should carry weight.
>
> 1. **§5 item 2 is struck.** The 8 % target defect is real, but the sealed MC gets **two other**
>    firm rules wrong, and the larger — a *trailing* drawdown where FTMO's is a **static $90,000
>    floor** [MEASURED] — runs the opposite way and is bigger. At each firm's true rules **every
>    `p_pass` in §2 moves up**, not down. The corrected column is in §2.
> 2. **§2 was missing phase 2 entirely**, and that is where the real cost is. FTMO survivors /
>    fwd / worst takes **110 calendar days** for the full 2-step evaluation, not the 52 in §2 —
>    and the 14-day payout clock starts only after both phases. Time-to-payout roughly doubles.
> 3. **§0 and §3 are wrong that the four sleeves survive "on both accounts."** They do not:
>    redacted_account kills `metals_core` and keeps `vp_euidx_pocgrav`. See the amendment at §0.
> 4. **§5 item 1 is understated.** B161's 46.9 % is a share of the *11-sleeve* book. On the books
>    that could actually be armed the two in-sample sleeves are **48.9 % to 74.2 %**. See §5.

---

## 0. The decision, in one paragraph

**Activate the four-sleeve survivor book, or don't.** The survivor book is
`metals_core`, `crypto`, `energy_agri`, `sub_xvol_pullback` — the subset of the W7 core-8 book that
survives re-costing at broker-true costs **under every carry assumption tested**, ~~on both
accounts~~. The sleeve composition and the risk dial are yours; this document is the measurement,
not a proposal to trade it (`SURVIVOR_BOOK_V1.json:boundary`).

> **Struck 2026-07-29 (B238): "on both accounts" is false, and the two accounts select different
> books.** Read directly from `SURVIVOR_BOOK_V1.json`: FTMO's survivors are the four named above;
> **redacted_account's are `crypto`, `energy_agri`, `sub_xvol_pullback`, `vp_euidx_pocgrav`.** Each
> account keeps one sleeve the other kills, decided by the per-account swap rate rather than by the
> strategy, and both swaps are marginal — `metals_core`'s break-even hold is **489 h** on FTMO
> (swap 0.0431 R/night) but **329 h** on redacted_account (0.0638), missing its own 320 h ceiling by
> 2.8 %; `vp_euidx_pocgrav` runs the other way, 251 h on FTMO against 355 h on redacted_account.
> So §3's per-sleeve table is the **FTMO** reading, and §2's redacted_account rows are a **different
> portfolio** from the FTMO rows above them.
>
> The book this sentence *meant* — surviving on both — is the three-sleeve intersection
> `crypto`, `energy_agri`, `sub_xvol_pullback`, which no published grid measured. Session Q
> measures it: FTMO fwd/worst **`p_pass` 0.99772** phase 1, **0.99577** across both phases, 81
> calendar days, **2.133 %/month** — against the four-sleeve book's 0.99918 / 0.99828 / 66 d /
> 2.617 %/mo. Dropping `metals_core` costs ~18 % of the forward rate and ~15 days, and *raises*
> `p_pass` at worst carry on the full window, because it is the highest-swap survivor.
> **Composition here is not a `p_pass` question — it is the concentration question in §5.**

**The thing that changed:** the holding-time uncertainty that has been described as OD-3's blocker
**does not bind this book.** It binds the 11-sleeve book. That distinction was in the artifact and
was not surfaced until now, and it is the reason this dossier exists rather than another measurement
session.

---

## 1. Recommendation

**Take the survivor book to a controlled canary at a dial you would be relaxed to lose, and let the
forward shadow accumulate.** Not because the evidence is strong enough to bet the account — §5 says
plainly where it is thin — but because:

- Its economics are **robust to the worst carry case**, which is the only open measurement question.
- The remaining doubts (§5) are **overfitting doubts**, and no amount of further re-costing can touch
  them. `B161`: *"Re-costing cannot detect overfitting, only mispricing. Nothing in this session
  speaks to whether those two edges are real, and they are half the survivor book."*
- **Only forward out-of-sample data can settle them**, and that clock does not start until something
  trades. Session P's carry (merged) is what makes the next window self-measuring.

The three `CARRY_CONDITIONAL` sleeves are **V2 candidates**, added when the data fetch happens. They
are not a precondition.

---

## 2. The economics

`research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json`, dial 2.0 % nominal
(`clean3_w7_ceiling_nom2p00`, `config/agent_config.yaml:1246-1394`).

**"WORST carry" = every trade charged the maximum swap nights its horizon allows.** It is the
pessimistic bound, not an expectation.

**Amended 2026-07-29 (B232–B234).** The `P(pass)` and `cal. days` columns as originally published
are the sealed MC's, at an 8 % target for both firms, phase 1 only. The two columns after them are
`MC_FIRM_TRUE_V1.json` at each firm's **measured** rules (FTMO 10 %, both accounts' static $90,000
overall floor and fixed-cash daily allowance) — first for phase 1, then for the **whole 2-step
evaluation**, which is what actually has to happen before a payout clock starts.

### FTMO

| book / window / carry | P(pass) as published | **P(pass) firm-true ph1** | **P(pass) 2-step** | %/mo calendar | cal. days ph1 (pub → true) | **cal. days 2-step** | book-days/mo |
|---|---:|---:|---:|---:|---:|---:|---:|
| **SURVIVORS / fwd 2025+ / WORST** | 0.99675 | **0.99918** | **0.99828** | 2.617 | 52 → 66 | **110** | 7.11 |
| SURVIVORS / fwd 2025+ / 1 night | 1.0 | 1.00000 | 1.00000 | 3.717 | 41 → 49 | 80 | 7.11 |
| **SURVIVORS / 2015-26 / WORST** | 0.96055 | **0.98365** | **0.97055** | 0.463 | 297 → 393 | **642** | 1.81 |
| SURVIVORS / 2015-26 / 1 night | 0.99995 | 0.99999 | 0.99996 | 0.841 | 202 → 250 | 393 | 1.81 |
| ALL 11 / 2015-26 / 1 night | 0.95045 | 0.95417 | **0.93054** | 1.973 | 88 → 109 | 177 | 12.26 |
| ALL 11 / 2015-26 / **WORST** | 0.4495 | 0.45785 | **0.29952** | 0.134 | 74 → 104 | 167 | 12.26 |

### redacted_account

| book / window / carry | P(pass) as published | **P(pass) firm-true ph1** | **P(pass) 2-step** | %/mo calendar | cal. days ph1 | **cal. days 2-step** |
|---|---:|---:|---:|---:|---:|---:|
| **SURVIVORS / fwd 2025+ / WORST** | 0.9891 | **0.99625** | **0.99232** | 2.551 | 57 | **105** |
| SURVIVORS / 2015-26 / WORST | 0.98295 | **0.99285** | 0.98634 | 0.583 | 260 | 481 |
| ALL 11 / 2015-26 / WORST | 0.23 | 0.24747 | **0.11299** | **−1.023** | 56 | 91 |
| ALL 11 / fwd 2025+ / WORST | 0.31785 | 0.36005 | **0.18016** | **−1.183** | 35 | 64 |

redacted_account's phase-1 target is 8 %, so its `P(pass)` moves purely on the drawdown and daily bases.
Its overall-loss rule is `TRANSFERRED` with no `kind` recorded; on the sealed trailing reading the
survivors/fwd/worst figure is 0.98871 rather than 0.99625.

**Read the two bold columns together.** The 11-sleeve book collapses from 0.95 to 0.46 (FTMO) and
goes *negative* on redacted_account under worst-case carry. The survivor book moves from 1.000 to 0.999.
**That is the whole argument**: the carry question is decisive for one book and irrelevant for the
other, and the three sleeves that need the missing data are not in the survivor set.

**And now read the 2-step column, which is new.** The survivor book pays almost nothing for phase 2
(0.99918 → 0.99828) but takes **twice as long**. The 11-sleeve book of record does *not* clear a
two-phase evaluation at worst carry on either account — FTMO 0.300, redacted_account 0.180 — and that was
invisible in every number published before today.

**One reading correction that applies to every row (B237).** "At the 2.0 % dial" is not 2.0 % of
risk per unit: `build_survivor_book.econ` vol-matches each variant, so the survivor book actually
risks **0.85 %** (FTMO forward) to **1.06 %** (redacted_account full window) per correlated unit — the
`eff_risk_pct` column in the artifact. Taking "2.0 % nominal" at face value over-reads the sizing by
about **2.4×**.

---

## 3. The four sleeves

| sleeve | conf | n | first → last | gross R | break-even hold | horizon | headroom |
|---|---:|---:|---|---:|---:|---:|---:|
| `metals_core` | 1.00 | 131 | 2015-03-19 → 2026-05-19 | 0.910 | 489 h | 320 h | 1.52× |
| `crypto` | 0.85 | 104 | **2024-09-19** → 2026-06-04 | 1.212 | 975 h | 320 h | 3.04× |
| `energy_agri` | 0.80 | 162 | 2021-02-01 → 2026-05-12 | 0.539 | 1383 h | 320 h | 4.31× |
| `sub_xvol_pullback` | 0.45 | 90 | 2016-06-03 → 2026-03-12 | 1.307 | never reached | 320 h | 9.62× |

"Break-even hold" is the holding time at which carry eats the edge. Every sleeve's break-even is
**1.5×–9.6× its own structural horizon** — which is why the carry question does not bind them.

---

## 4. Firm rules — the two accounts are not the same instrument

`research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json`

| | FTMO | redacted_account |
|---|---|---|
| profit target ph1 / ph2 | **10 %** / 5 % [MEASURED] | **8 %** / 5 % [TRANSFERRED] |
| max daily loss | 5 % of **Initial Capital**, reset **00:00 CE(S)T** | 5 % of **Initial Balance + today's realized profit**, reset **00:00 server time** |
| max overall loss | 10 %, **static** (2-Step) [MEASURED] | 10 % [TRANSFERRED — asserted equal to FTMO, not independently captured] |
| first payout | 14th day after first trade | 21 days after funding, then bi-weekly |
| profit split | 80 % → 90 % | 80 % → 90 % (95 % with add-ons) |
| payout cap | — | **$4,999 per request**, min $250 |

**The daily-loss clocks are different, and the denominators are different.** A dial safe under one is
not automatically safe under the other. Set the dial **per account** and state it with its reset rule.

---

## 5. What is unproven — read this before deciding

Ordered by how much it should worry you.

1. **Half the survivor book has no out-of-sample window at all — and it is worse than half.**
   `B161` [MEASURED]: `crypto` is **37.7 %** of contribution on 104 trades with **no history before
   2024-09-19**; `sub_xvol_pullback` is 9.2 % on 90 trades and is *"a cell selected from a substrate
   scan."* **46.9 % of the edge sits on 194 trades.** Mean gross 1.2–1.3 R on a 3R-target geometry
   implies a ~55 % target-hit rate — high, and exactly what an overfit cell looks like.

   > **Amended 2026-07-29 (B240): 46.9 % is a share of the ELEVEN-sleeve book of record, not of the
   > survivor book.** On B161's own stated basis (Kelly columns, signed denominator) the 11-sleeve
   > book brackets 37.7 / 9.2 on both components at intermediate carry — 37.4 / 8.8 at 0.25 nights,
   > 39.0 / 9.2 at 0.75 — and no survivor-book basis tried (6 window×carry combinations, Kelly and
   > flat) comes close on both at once. On the books that could actually be armed,
   > `crypto + sub_xvol_pullback` is:
   >
   > | book | FTMO fwd/WORST | FTMO 2015-26/WORST | redacted_account fwd/WORST | redacted_account 2015-26/WORST |
   > |---|---:|---:|---:|---:|
   > | SURVIVORS-4 | **48.9 %** | **62.9 %** | **68.5 %** | **74.2 %** |
   > | BOTH-3 | **62.0 %** | **69.9 %** | **66.8 %** | **73.1 %** |
   >
   > redacted_account is worst because its re-cost drops `metals_core` — the only sleeve with 131 trades
   > and history back to 2015-03-19. **The doubt ranked first here is larger than stated, for every
   > candidate book, on both accounts.** Nothing in Session Q or Session N can shrink it; only
   > forward out-of-sample data can, which is the argument in §1.
2. ~~**The MC target is 8 %, but FTMO requires 10 %.**~~ **Struck 2026-07-29 (B230–B232) — the
   defect is real and the inference from it was backwards.** `INTEG_portfolio_build.py:298` does
   read `TARGET = 0.08; MAXDD = 0.10; DAILY = 0.05; N = 20000`, and 0.08 is redacted_account's target
   applied to both. But the same line gets **two other** firm rules wrong, and they were not noticed
   when this item was written:

   | axis | sealed engine | measured firm rule | direction |
   |---|---|---|---|
   | profit target | 0.08 both | FTMO **10 %** [MEASURED] | legacy optimistic |
   | max overall loss | `(peak−eq)/peak ≥ 0.10` — **trailing** | *"static limit"*, floor **$90,000** [MEASURED] | legacy **pessimistic** |
   | max daily loss | 5 % of the day's **opening equity** | fixed cash, 5 % of **initial** balance | legacy optimistic |

   The drawdown error is the larger one and it runs the other way. On FTMO ALL-11 / 2015-26 / worst
   the target error is worth **−0.053** and the drawdown error **+0.052**; they nearly cancel.
   **Re-run at each firm's true rules, every P(pass) in §2 moves up, not down** — so nothing you
   have been shown is too good on this axis. What is missing instead is **phase 2**, now in §2, and
   it roughly doubles the calendar time to a payout.
3. **Cost coverage is thin on two sleeves.** From `SURVIVOR_BOOK_V1.json`:
   `energy_agri` **103 of 162 rows ABSENT** (no cost data at all), `crypto` **69 of 104 TRANSFERRED**
   (borrowed from a comparable instrument). Only `metals_core` is majority-MEASURED (97/131).
4. **Direction is unknown on `sub_xvol_pullback` for 100 % of rows** and `crypto` for 34.6 %. Swap
   sign depends on direction, so those carry figures rest on an assumption.
5. **The book is low-frequency, and the headline rate hides it.** 1.81 book-days/month on the full
   window; 7.11 forward. The `monthly_pct_headline_x21` figures (5.4–11 %) assume 21 trading days a
   month that **do not exist**. The calendar figures in §2 are the real ones.
6. **Three of the four survivors fired zero times in the 38-day live window** (K's G4). This is
   *consistent with* low frequency — empirical P(zero in 38 days) is 0.369 `metals_core`, 0.284
   `crypto`, 0.638 `energy_agri`, and **0.075 for all five silent together** over 1,934 rolling
   windows. It is not evidence of breakage: the same generators fired **289 times** over
   2024-01-02…2026-07-24. But it does mean **the live window offers no forward confirmation.**
7. **K1 is not passed.** Generation parity reached 86.59 % count agreement, not zero disagreements.
   K localised the residual to path-dependent sleeves and filed **D21**: undecidable until the book
   records which bar series it read. **Session P's carry fixes that** — from the next window on.
8. **The script behind the empirical P(0) figures in item 6 is not committed** — only its outputs
   are. Under this programme's own rule, that receipt is incomplete.

---

## 6. What it costs to be wrong

The failure mode is **not** a blown account — `p_fail_daily` is **0.0** across every survivor variant,
and `p_fail_dd` is 0.039 at worst (FTMO, full window, worst carry). The realistic failure mode is
**a book that does not trade enough to matter**: 7.11 book-days a month, and 52 calendar days to a
target under the pessimistic carry.

So the cost of being wrong is mostly **time and opportunity**, not capital. That asymmetry is the
argument for starting rather than waiting.

---

## 7. The options in front of you

| | option | what it buys | what it costs |
|---|---|---|---|
| **A** | Canary the survivor book at a reduced dial | Starts the only clock that can settle §5.1 | Small capital at risk; 3 sleeves left out |
| **B** | Canary at the full 2.0 % dial | Faster to a payout | §5.1 and §5.2 unhedged |
| **C** | Fetch `bridge_ftmo_deep_h4_*`, resolve the 3 sleeves, then decide | An 11-sleeve book | Another session; and §5.1 remains untouched either way |
| **D** | ~~Re-run the MC at FTMO's true 10 % target first~~ **DONE 2026-07-29** | Removed §5.2, and found three more things | 1 session, no new data |

**A + D was the recommendation.** ~~D is cheap and removes the one caveat found today~~; A starts
the out-of-sample clock that nothing else can.

> **D is executed (B230–B244).** It did not lower the numbers — it raised them, for the reason in
> §5.2 — but it changed three things that bear on A: the **2-step calendar time roughly doubles**
> (§2), the **survivor set is account-specific** (§0), and the **concentration doubt is larger than
> §5.1 states** (§5.1). None of that argues against A; the first two argue for setting expectations
> on time-to-payout, and the third argues for the *reduced* dial in A rather than the full dial in
> B. Session Q also priced the dial for the first time (B237): on this book `P(pass)` is ≥ 0.9999 at
> every dial from 0.5 % to 2.0 %, so **a reduced dial costs time and buys essentially no `P(pass)`**
> — what it buys is protection against the things the MC cannot model, which is §9 of
> `phase3/SESSION_Q_MC_TRUE_TARGET_RESULT.md`.

**Not recommended: waiting for C.** It does not touch the dominant doubt, and it holds the forward
clock at zero while it runs.

**One thing to settle before any redacted_account decision, added 2026-07-29 (B241).** redacted_account
**prohibits weekend holding on the funded account** [MEASURED, secondary_audit] and all four
survivor sleeves carry a **320-hour (13.3-day)** horizon, which cannot avoid a weekend. Every
redacted_account figure in this document therefore describes the **challenge phases only**, and the config
change that would make the funded phase legal does not exist. FTMO carries no such rule.

---

## 8. Prerequisites before anything trades

These are engineering, not decisions, and none is done by this document.

1. **The activation-token carry must land on the VPS** — Session I prepared it as a reviewable diff
   plus an owner-executed runbook (`phase3/TOKEN_CARRY.md`, `phase3/STAGE0_VPS_RUNBOOK.md`). **Only
   you execute it.** Today the entire brake is `ultimate_book_live_activation_allowed: false` at
   `config/agent_config.yaml:1250` on a running, funded, connected host **with nothing monitoring
   the gate.**
2. **Session P's packet carry should deploy before, not after** — it is what records holding time and
   cost going forward, and what makes K1 decidable.
3. **Chaos drills are written but not run** (`phase3/TOKEN_CHAOS_DRILLS.md`, 8 specs).
4. **Pre-registered stop conditions** — evidence-based, not only loss-based: measured-cost deviation
   from `BROKER_TRUE_COSTS_V1.json` over n fills, and sleeve-level tripwires of the JPY kind.

---

## 9. Provenance

| claim | source |
|---|---|
| economics, tiers, per-sleeve | `research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json` |
| firm rules, reset clocks | `research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json` |
| cost model | `research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json`, `src/costs/` |
| MC constants | `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/INTEG_portfolio_build.py:298` |
| **corrected MC at each firm's measured rules, phase 2, dial sweep, BOTH-3** | `research/operations/w7_recost_2026_07_27/MC_FIRM_TRUE_V1.json` + `.md`; **B230–B244**; `phase3/SESSION_Q_MC_TRUE_TARGET_RESULT.md` |
| in-sample concentration | `IMPLEMENTATION_STATE.md` **B161** |
| G4 / zero fires / P(0) | **B171**, `phase3/receipts/G4_GENERATION_RATE.json` |
| K1 verdict, D21 | **B170–B172**, `phase3/K1_GATE_RECEIPT.md` |
| holding-time evidence | **B173–B177**, **B200–B201**, **B215** |
| the dial | `config/agent_config.yaml:1246-1394` |
