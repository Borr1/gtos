# Session Q — the survivor-book MC at each firm's measured rules

**OD-3 option D. Branch `phase3/mc-true-target` off `main` @ `9b9367e78`. Blocks B230–B249.**

Reproduce: `python3 scripts/mc_firm_rules.py && python3 scripts/report_mc_firm_true.py`
Artifacts: `research/operations/w7_recost_2026_07_27/{MC_FIRM_TRUE_V1.json,MC_FIRM_TRUE_V1.md}`
Tests: `pytest tests/test_mc_firm_rules.py -q` → **37 passed**. Full-suite A/B: `ab/SESSION_Q_AB.md`.

---

## 0. The answer

**The defect is real. The conclusion drawn from it is backwards.**

`TARGET = 0.08` is redacted_account's phase-1 target applied to FTMO, whose measured target is 10 %. That is
confirmed at three independent sources (§2). But the sealed engine gets **two other** firm rules wrong,
the commission named neither, and **the larger one runs the opposite way**:

| axis | sealed engine | measured firm rule | direction |
|---|---|---|---|
| profit target | 0.08 both accounts | FTMO **10 %** [MEASURED], redacted_account 8 % [TRANSFERRED] | legacy **optimistic** (FTMO only) |
| max overall loss | `(peak−eq)/peak ≥ 0.10` — **trailing** | FTMO *"establishes a static limit"*, floor **$90,000** [MEASURED] | legacy **pessimistic** (both) |
| max daily loss | `dp ≤ −0.05` — % of the day's **opening equity** | both firms: fixed cash, **5 % of the initial balance** | legacy **optimistic** (both) |

Net, at each firm's true rules, **every one of the ten `p_pass` figures in the OD-3 dossier moves *up*,
not down.** The headline — FTMO, survivors, forward window, worst carry — goes **0.99675 → 0.99918**.
The largest single move is redacted_account ALL-11 forward/worst, **0.31785 → 0.36005**, and it is *entirely*
the drawdown basis.

So the sentence in the dossier's §5.2 — *"Every FTMO P(pass) above is therefore optimistic"* — is true
of the target in isolation and **false of the corrected rule set**. Nothing Borhen has been shown is
too good on this axis.

**What actually moves is time, and it moves a lot.** The dossier quotes days-to-pass for phase 1 at an
8 % target. At FTMO's real 10 % target, and then across the second phase both firms require:

| FTMO, survivors, fwd 2025+, worst carry | calendar days |
|---|---:|
| dossier (phase 1 @ 8 %) | **52** |
| phase 1 @ the true 10 % | **66** |
| **the whole 2-step evaluation** | **110** |

and on the full window, 297 → 393 → **642 calendar days**. **Time-to-first-payout roughly doubles.**
That is the number in this session that changes a decision.

**Three further findings, all from checking the commission rather than executing it:**

1. **The two accounts do not select the same book** (§10.1). `SURVIVORS_ONLY` is `metals_core` on FTMO and
   `vp_euidx_pocgrav` on redacted_account. The dossier's §0 — *"the subset … that survives … on both
   accounts"* — describes a **three**-sleeve book that no published grid measures. It is measured here.
2. **The concentration doubt the dossier calls its worst is understated** (§10.2). B161's 46.9 % is a
   share of the **11-sleeve book of record**, not of the survivor book. On the books that could
   actually be armed it is **48.9 % to 74.2 %**.
3. **The daily-loss denominator is provably irrelevant for the survivor book and material for the book
   of record** (§6) — deterministically, not by simulation.

---

## 1. What licenses these numbers

Five links, each exact rather than approximate. The chain matters because every number below is a
*difference* between two runs, and a difference is only attributable to the rule change if nothing
else moved.

| # | control | result |
|---|---|---|
| 1 | `scripts/build_survivor_book.py` re-run at HEAD vs the committed artifact | **byte-identical** (sha256 over all 48,721 B) |
| 2 | this session's series reconstruction vs the published columns (`book_days`, `vol_scale`, `eff_risk_pct`, `mean_r_per_book_day`), 24 cells | **0 mismatches** |
| 3 | `mc(Rules.LEGACY)` vs `INTEG_portfolio_build_w2.mc_series`, 36 cells × 20,000 paths, all five returned fields | **0 disagreements** — bit-identical, not "close" |
| 4 | this engine + this reconstruction at the sealed 20,000 paths vs **all 96 published MC fields** | **0 mismatches** (`test_this_engine_reproduces_every_published_mc_field_exactly`) |
| 5 | the firm-rule branches — which have no sealed counterpart — vs a **second, independently written implementation** (closure predicates, flat day loop, explicit phase machine), 7 rule sets × 3 risk levels | **0 disagreements** |

Link 3 is the load-bearing one. `mc()` is not a reimplementation of the sealed engine; it is the sealed
engine with the constants lifted into parameters, and it reduces to it exactly. Link 5 exists because
link 3 proves nothing about the *new* branches, and those are what the corrected numbers rest on.

**Nothing in the sealed route is edited.** `INTEG_portfolio_build.py:298` still reads
`TARGET = 0.08; MAXDD = 0.10; DAILY = 0.05`, and `test_the_sealed_constants_are_still_the_sealed_constants`
fails if that changes. The commission's "the 8 % result must stay reproducible" is satisfied by
construction, not by care.

**Precision.** 200,000 paths per cell against the sealed engine's 20,000 — 10×, and nested, so the
20,000-path result is exactly the 200,000-path result's prefix. Standard error on a `p_pass` of 0.997
is 1.2 × 10⁻⁴. Rule variants within a cell share seeds, so differences are paired and far better
resolved than either level alone. The measured seed-to-seed spread at the sealed rules is **≤ 0.00463**
across all 36 cells (§8 of `MC_FIRM_TRUE_V1.md`).

---

## 2. The target defect — confirmed, at three independent sources

| source | FTMO phase 1 | phase 2 |
|---|---|---|
| `FIRM_RULES_V1.json:firms.FTMO.rules.profit_target_pct`, coverage `MEASURED`, `provenance_kind: captured_page` | **10.0** | 5.0 |
| `config/profiles/operator_profile.yaml:85,99` — the **live** profile the supervisor launches | **10.0** | 5.0 |
| `config/profiles/ftmo.yaml:83,97` | **10.0** | 5.0 |

against `config/profiles/redacted_account.yaml:14` — `ultimate_book_profit_target_pct: 0.08`. The constant is
redacted_account's, applied to both.

`TARGET` is imported by `INTEG_portfolio_build_w2.py:250`, `INTEG_portfolio_build_w5.py:150`,
`KB2_true_corr_mc.py:100` and `KB3_regime_scaling.py:42`, and reaches `SURVIVOR_BOOK_V1.json` through
`W2.mc_series`. The commission's list was right; nothing was edited in any of them.

**Not a live defect.** `src/components/ultimate_book/admission.py:52` also hardcodes
`FTMO_TARGET = 0.08` under a header reading "FTMO CONSTANTS", beside `FTMO_MAXDD`/`FTMO_DAILY` which
*are* the firm's numbers. Its only consumer is `:1547`, a `"ftmo_rules"` metadata dict in the live
package descriptor; no gate reads it, and the live target comes from the profile via
`scripts/build_firm_rules.py:301`. This is FR2 in `FIRM_RULES_V1.json`, already filed as an owner
question ("deliberate internal target, or stale transcription?"). Confirmed as filed; **not fixed
here**, because renaming a constant the owner may have set deliberately is his call, not mine.
`admission.py` is **unbound** by the R2 contract, so the fix is a one-line edit whenever he answers.

---

## 3. The rule the commission did not name, and it is the big one

`FIRM_RULES_V1.json:firms.FTMO.rules.max_overall_loss_pct`:

```json
{"value": 10.0, "kind": "static (not trailing) for 2-Step", "floor_usd": 90000.0,
 "coverage": "MEASURED", "provenance": "as above -- 'establishes a static limit'"}
```

The engine tests `(peak - eq) / peak >= 0.10` (`INTEG_portfolio_build_w2.py:263`). That is a **trailing**
stop measured from the running high-water mark. Since `peak ≥ 1` always, `peak × 0.90 ≥ 0.90`, so the
trailing rule fires at a **higher** equity than the firm's fixed $90,000 floor, always — it is strictly
harder to survive, and the gap widens exactly as a path approaches its target.

This is not a small correction. Isolated (`L3`), it is worth up to **+0.0764** of `p_pass` across the
36 cells (0 to +0.0521 across the ten the dossier quotes), and it is the reason every corrected figure
moves up:

| account | book / window / carry | target 8→firm | daily %→cash | maxDD trail→static | **net** |
|---|---|---:|---:|---:|---:|
| FTMO | SURVIVORS / fwd / WORST | −0.00062 | +0.00000 | **+0.00219** | **+0.00219** |
| FTMO | SURVIVORS / 2015-26 / WORST | −0.00769 | +0.00000 | **+0.02152** | **+0.02120** |
| FTMO | ALL 11 / 2015-26 / 1 night | −0.00794 | −0.01395 | **+0.02477** | **+0.00173** |
| FTMO | ALL 11 / 2015-26 / WORST | **−0.05305** | −0.00263 | **+0.05210** | **+0.00488** |
| redacted_account | SURVIVORS / fwd / WORST | 0 | +0.00000 | **+0.00754** | **+0.00754** |
| redacted_account | ALL 11 / fwd / WORST | 0 | +0.00000 | **+0.03961** | **+0.03961** |

Read the FTMO ALL-11 worst-carry row: the target error was worth −0.053 and the drawdown error +0.052.
**They nearly cancel.** A session that had corrected only the target — which is exactly what the
commission asked for — would have reported a 5-point deterioration that does not exist.

**One caveat, stated because it is the weaker leg.** redacted_account's `max_overall_loss_pct` is
`TRANSFERRED`, value 10.0, with **no `kind` field** — it is inherited from an assertion that the two
firms' 100k challenge limits are identical. If FTMO's is static, the transfer says redacted_account's is
too, and that is how it is modelled. `L5`/`P4` re-run everything with the trailing rule retained, so
the redacted_account figures can be read either way:
redacted_account survivors fwd/worst is **0.99625** static, **0.98871** trailing.

---

## 4. The corrected table — the ten figures in front of the owner

`published` is `SURVIVOR_BOOK_V1.json` at 20,000 paths. `L0` is this engine at the **same** rules and
200,000 paths, so `L0 − published` is Monte-Carlo noise and `firm-true − L0` is the whole rule effect.

| account | book / window / carry | published (8 %) | L0 same rules | **firm-true ph1** | Δ vs L0 | **firm-true 2-step** |
|---|---|---:|---:|---:|---:|---:|
| FTMO | **SURVIVORS / fwd 2025+ / WORST** | 0.99675 | 0.99699 | **0.99918** | +0.00219 | **0.99828** |
| FTMO | SURVIVORS / fwd 2025+ / 1 night | 1.00000 | 1.00000 | **1.00000** | +0.00000 | 1.00000 |
| FTMO | SURVIVORS / 2015-26 / WORST | 0.96055 | 0.96245 | **0.98365** | +0.02120 | 0.97055 |
| FTMO | SURVIVORS / 2015-26 / 1 night | 0.99995 | 0.99991 | **0.99999** | +0.00008 | 0.99996 |
| FTMO | ALL 11 / 2015-26 / 1 night | 0.95045 | 0.95244 | **0.95417** | +0.00173 | 0.93054 |
| FTMO | ALL 11 / 2015-26 / WORST | 0.44950 | 0.45297 | **0.45785** | +0.00488 | **0.29952** |
| redacted_account | **SURVIVORS / fwd 2025+ / WORST** | 0.98910 | 0.98871 | **0.99625** | +0.00754 | **0.99232** |
| redacted_account | SURVIVORS / 2015-26 / WORST | 0.98295 | 0.98045 | **0.99285** | +0.01240 | 0.98634 |
| redacted_account | ALL 11 / 2015-26 / WORST | 0.23000 | 0.23172 | **0.24747** | +0.01575 | **0.11299** |
| redacted_account | ALL 11 / fwd 2025+ / WORST | 0.31785 | 0.32044 | **0.36005** | +0.03961 | **0.18016** |

All 36 cells, including the six the dossier does not quote, are in `MC_FIRM_TRUE_V1.md` §3.

**What to change in the dossier.** §2's two tables should carry the `firm-true ph1` column and, more
importantly, the 2-step column — see §5. §5.2 ("*The MC target is 8 %, but FTMO requires 10 %… Every
FTMO P(pass) above is therefore optimistic*") should be **struck and replaced**: the target is wrong,
two other rules are also wrong, and the net moves the other way. `CLAUDE.md` §4's `P(pass) 0.951` and
`P(pass) 0.450` become **0.954** and **0.458**.

---

## 5. Phase 2 — the correction that actually changes the decision

Both firms require a second phase at 5 %. A book that clears phase 1 and stalls in phase 2 has passed
nothing, and no published figure has ever modelled it. Modelled here as one continuous bootstrap path:
phase 1, account reset to the initial balance, phase 2, same loss limits throughout.

| account | book / window / carry | ph1 | ph2 alone | **2-step** | ph1 × ph2 | cal-days ph1 | **cal-days 2-step** |
|---|---|---:|---:|---:|---:|---:|---:|
| FTMO | **SURVIVORS / fwd / WORST** | 0.99918 | 0.99921 | **0.99828** | 0.99839 | 66 | **110** |
| FTMO | SURVIVORS / 2015-26 / WORST | 0.98365 | 0.98513 | **0.97055** | 0.96902 | 393 | **642** |
| FTMO | ALL 11 / 2015-26 / 1 night | 0.95417 | 0.97099 | **0.93054** | 0.92649 | 109 | **177** |
| FTMO | ALL 11 / 2015-26 / WORST | 0.45785 | 0.57907 | **0.29952** | 0.26512 | 104 | **167** |
| redacted_account | **SURVIVORS / fwd / WORST** | 0.99625 | 0.99642 | **0.99232** | 0.99267 | 57 | **105** |
| redacted_account | ALL 11 / fwd / WORST | 0.36005 | 0.46907 | **0.18016** | 0.16889 | 35 | **64** |

Two readings.

**For the survivor book, phase 2 costs almost no probability and roughly doubles the clock.** FTMO
forward/worst: 0.99918 → 0.99828, but 66 → 110 calendar days. That is the number that belongs beside
"first payout on the 14th day after the first trade" — the 14-day clock starts *after* both phases.

**For the 11-sleeve book of record, phase 2 is close to decisive.** FTMO worst carry 0.458 → **0.300**;
redacted_account forward/worst 0.360 → **0.180**. The book of record does not clear a two-phase evaluation at
worst carry on either account, and that was invisible in every prior number.

`ph1 × ph2` is within 0.004 of the joint MC everywhere except the two weakest cells, where the joint is
*higher* (0.2995 vs 0.2651) — passing phase 1 selects bootstrap positions that favour phase 2. The
joint figure is the one to use; the product is shown only to demonstrate the phases are near-independent
in this model.

---

## 6. The daily-loss denominator — answered deterministically, not by simulation

The commission asked whether the MC models one denominator for both firms, and to quantify it. **It
models one, and it is neither firm's.**

- **FTMO** [MEASURED, captured page]: *"the difference between the account balance recorded at 00:00
  CE(S)T of the current day and the Maximum Daily Loss Amount, which is **5 % of the Initial Simulated
  Capital**"* — a fixed cash amount, measured on equity.
- **redacted_account** [MEASURED, captured page], worked example verbatim: *"if you start a new day with
  $110,000 and lose $5,000 … since your daily loss limit is calculated based on the initial balance
  ($100,000 × 5 % = $5,000), losing $5,000 breaches the limit … **even though your equity has not
  dropped to $95,000**."*
- **The engine** tests `dp <= -0.05` where `dp` is a return on the day's opening equity. At $110,000 it
  permits **$5,500**. redacted_account's own example breaches; the engine does not.
  (`test_redacted_account_worked_example_breaches_under_firm_basis_and_not_under_legacy`.)

The denominators differ by exactly the factor `eq`, so the legacy rule is **lenient in profit** — which
is where a passing path spends most of its life — and strict in drawdown.

**Whether that matters is decidable without simulating.** The bootstrap only ever draws days present in
the series, so the worst single-day loss any path can take is `min(series) × risk`, at a day-start
equity of at most `1 + target`:

| book | window / carry | worst day, % of equity | legacy can fire | firm can fire | % of the 5 % allowance |
|---|---|---:|---|---|---:|
| FTMO SURVIVORS | fwd / WORST | −1.541 | no | no | **33.9 %** |
| FTMO SURVIVORS | 2015-26 / WORST | −1.946 | no | no | 42.8 % |
| redacted_account SURVIVORS | fwd / WORST | −1.505 | no | no | 33.1 % |
| FTMO ALL 11 | 2015-26 / 0 nights | −4.747 | **no** | **YES** | 104.4 % |
| FTMO ALL 11 | 2015-26 / 1 night | −4.984 | **no** | **YES** | 109.6 % |
| redacted_account ALL 11 | 2015-26 / 0 nights | −4.816 | **no** | **YES** | 106.0 % |
| redacted_account ALL 11 | 2015-26 / WORST | −7.822 | YES | YES | 172.1 % |

**For the survivor book on either account, no path can breach the daily rule under either denominator.**
The worst day in the whole series uses a third of the allowance. That is a proof, not a `p_fail_daily`
of 0.0 that might be a sampling artefact.

**For the 11-sleeve book of record it is material, and the legacy denominator was hiding breaches
entirely.** `p_fail_daily` moves from a published **0.0** to **0.0068** (FTMO, 0 nights), **0.0233**
(FTMO, 1 night) and **0.0055** (redacted_account, 0 nights) — three cells where the correct rule fires and the
sealed one cannot. Isolated, the daily correction costs FTMO ALL-11 at 1 night **−0.01395** of `p_pass`.

**Reset clocks.** FTMO resets at 00:00 CE(S)T, redacted_account at 00:00 server time (= `America/New_York + 7 h`);
they are different calendars ~4 weeks a year. The MC has no clock at all — its "day" is a row in the
series — so the reset rule cannot be modelled here and is not. It matters for the live governor, where
FR1 already records the same denominator error at `governor_state.py:271`, severity high.

---

## 7. Minimum trading days — modelled, and inert

FTMO requires 4 trading days per phase, redacted_account 5 [both MEASURED]; the engine models neither, and
only FTMO's is configured anywhere in the repo (FR4). Modelled two ways — `latch` (stop risking on
reaching target, wait out the minimum, which is what `derisk_mode: smooth` would do) and `at_risk`
(keep trading at full size, a bound rather than an expectation):

**Largest effect anywhere in the grid: −0.0022** (redacted_account ALL-11 full/worst, `at_risk`). Every
survivor-book cell is unchanged to five decimals under both models. The rule is real, unconfigured,
and does not reach any number. Closed.

---

## 8. The risk dial — pricing the dossier's option A

The dossier's option A is "canary at a reduced dial" and nothing in the record priced it. First, a
reading correction that applies to every table including this one:

**"the 2.0 % dial" is not 2.0 % of risk per unit.** `build_survivor_book.econ` vol-matches each variant
to the reference book (`vs = sd_book / sd`), so the survivor book at the nominal 2.0 % dial actually
risks **0.85 %** (FTMO forward) to **1.06 %** (redacted_account full window) per correlated unit — the
`eff_risk_pct` column, published but not mentioned in the dossier. A reader who takes "2.0 % nominal"
at face value is over-estimating the sizing by ~2.4×.

FTMO, survivors, forward window, worst carry (the decision cell), at the corrected rules:

| dial | eff risk % | p_pass ph1 | p_pass 2-step | cal-days ph1 | %/mo calendar |
|---|---:|---:|---:|---:|---:|
| 0.50 % | 0.212 | 1.00000 | 1.00000 | 280 | 0.654 |
| 0.75 % | 0.318 | 1.00000 | 1.00000 | 184 | 0.981 |
| 1.00 % | 0.423 | 1.00000 | 1.00000 | 137 | 1.308 |
| 1.50 % | 0.635 | 0.99994 | 0.99988 | 90 | 1.963 |
| 2.00 % | 0.847 | 0.99918 | 0.99828 | 66 | 2.617 |

**The dial is not buying safety on this book; it is buying time.** `p_pass` is ≥ 0.9999 at every dial
tested, and halving the dial halves the monthly rate and roughly doubles the days-to-pass. The reason
is §6: the failure modes this MC can express — daily breach and overall drawdown — are already
essentially closed on a four-sleeve book risking under 1 % per unit.

That is an argument *for* option A being cheap, and a warning that this table is not where the risk of
option A lives. What a reduced dial buys is protection against the things the MC does not model (§9),
and against §10.

---

## 9. What this correction does **not** fix

Every item here runs in the **optimistic** direction, so the corrected `p_pass` figures remain an upper
bound. None is introduced by this session; all survive it.

**9.1 — The MC's "day" is a trade-entry day, not a calendar equity day.** Every generator books a
trade's entire realized R on its **entry** date (`INTEG_portfolio_build.py:90,163,198` — `date=T[i].date()`
where `i` is the entry bar). The survivor sleeves have 320-hour horizons and are charged up to 13.4
nights of carry, so a trade can close ~13 calendar days after the row it lives in. The bootstrap series
is therefore a per-entry-day realized-R series, not an equity curve.

**9.2 — Both firms measure on equity, continuously, including open P/L.** FTMO's `measured_on` is
*"equity (balance + open P/L ± swaps − commissions)"*; redacted_account's is *"closed results for the day +
open position results"*. A day that nets −3 % but dips to −6 % intraday breaches in reality and not
here; so does an equity path that touches $90,000 with positions open. The modelled path is strictly
smoother than the measured one, so **`p_fail_dd` and `p_fail_daily` are both understated, on the
corrected rules as much as the sealed ones.**

The size of that gap is not recoverable from the caches, and the reason is the same missing datum that
leaves the carry band open: **no exit index survives anywhere** (`geometry_lib.simulate` returns realized
R and nothing else; Session N §8.1). Without exit times there is no position overlap, so there is no
mark-to-market path to measure. The missing exit index does not only leave carry unresolved — it leaves
the drawdown path unmodelled. Session P's packet carry is what closes this going forward.

**9.3 — redacted_account prohibits weekend holding on the funded account** [`FIRM_RULES_V1.json`, coverage
`MEASURED`, `provenance_kind: secondary_audit`] — *"allowed in Challenge, PROHIBITED on the funded
account. Requires a post-pass config change that does not exist."* All four survivor sleeves carry a
**320-hour (13.3-day) horizon**, which cannot avoid a weekend. **Every redacted_account number in this
document and in the dossier describes the challenge phases only.** What the book does on a redacted_account
funded account is unmeasured, and the config to make it legal does not exist.

**9.4 — Overfitting is untouched, and this session cannot touch it.** B161's rule stands: re-costing
detects mispricing, not overfitting; the same is true of re-ruling. See §10 — the exposure is larger
than recorded.

**9.5 — `PATHCAP` truncation.** A path that neither passes nor fails within 2,000 blocks (10,000
book-days) is `timeout`. `p_timeout` is **0.00000 in all 36 cells** at the 2.0 % dial and is now
published per cell, so this is confirmed inert rather than assumed. It is *not* inert at low dials on
near-zero-drift books, which is why the dial sweep is run only on the survivor variants.

---

## 10. Two things the dossier gets wrong, found on the way

### 10.1 The two accounts do not select the same book

`OD3_DOSSIER_SURVIVOR_BOOK.md` §0: *"The survivor book is `metals_core`, `crypto`, `energy_agri`,
`sub_xvol_pullback` — the subset … that survives re-costing at broker-true costs under every carry
assumption tested, **on both accounts**."* Read directly from `SURVIVOR_BOOK_V1.json`:

| | FTMO | redacted_account |
|---|---|---|
| survivors | `crypto`, `energy_agri`, **`metals_core`**, `sub_xvol_pullback` | `crypto`, `energy_agri`, `sub_xvol_pullback`, **`vp_euidx_pocgrav`** |

Each account keeps one sleeve the other kills, and both swaps are marginal — decided by the per-account
swap rate, not by the strategy:

| sleeve | account | swap R/night | break-even hold | ceiling | tier |
|---|---|---:|---:|---:|---|
| `metals_core` | FTMO | 0.0431 | 489 h | 320 h | UNCONDITIONAL |
| `metals_core` | **redacted_account** | **0.0638** | **329 h** | 320 h | **CARRY_CONDITIONAL** (misses by 2.8 % of its own horizon) |
| `vp_euidx_pocgrav` | FTMO | 0.0260 | 251 h | 320 h | CARRY_CONDITIONAL |
| `vp_euidx_pocgrav` | **redacted_account** | **0.0175** | **355 h** | 320 h | **UNCONDITIONAL** |

So the dossier's §3 per-sleeve table (`metals_core`, break-even 489 h, headroom 1.52×) is the **FTMO**
figure; on redacted_account it is 329 h and headroom **1.03×**. And the redacted_account rows of §2 are a
**different portfolio** from the FTMO rows above them.

**The book the §0 sentence actually describes** — surviving on both — is the three-sleeve intersection
`crypto`, `energy_agri`, `sub_xvol_pullback`. It is measured here as `SURVIVORS_BOTH_ACCOUNTS`
(`MC_FIRM_TRUE_V1.md` §7b), and it holds up:

| account | window / carry | book | book-days | p_pass ph1 | p_pass 2-step | cal-d ph1 | %/mo cal |
|---|---|---|---:|---:|---:|---:|---:|
| FTMO | fwd / WORST | SURVIVORS-4 | 128 | 0.99918 | 0.99828 | 66 | 2.617 |
| FTMO | fwd / WORST | **BOTH-3** | 117 | **0.99772** | **0.99577** | **81** | **2.133** |
| FTMO | 2015-26 / WORST | SURVIVORS-4 | 246 | 0.98365 | 0.97055 | 393 | 0.463 |
| FTMO | 2015-26 / WORST | **BOTH-3** | 190 | **0.99512** | **0.99023** | 398 | 0.473 |
| redacted_account | fwd / WORST | SURVIVORS-4 | 164 | 0.99625 | 0.99232 | 57 | 2.551 |
| redacted_account | fwd / WORST | **BOTH-3** | 117 | **0.99887** | **0.99779** | 60 | **2.331** |

Dropping `metals_core` costs ~18 % of the forward monthly rate and ~15 calendar days, and *raises*
`p_pass` at worst carry on the full window — because `metals_core` carries the highest swap of the FTMO
survivors, so it is the sleeve worst-carry punishes most. **The composition question is not a `p_pass`
question.** It is a concentration question, which is §10.2.

### 10.2 The concentration doubt is understated, and it is the doubt the dossier calls its worst

Dossier §5.1, from B161: *"46.9 % of the survivor book's edge sits on 194 trades"* — `crypto` 37.7 % and
`sub_xvol_pullback` 9.2 %, neither with an out-of-sample window.

**That figure is a share of the 11-sleeve book of record, not of the survivor book.** On B161's own
stated basis (Kelly columns, signed denominator), the 11-sleeve book brackets it on *both* components at
an intermediate carry — 37.4 / 8.8 at 0.25 nights, 39.0 / 9.2 at 0.75 nights — and no survivor-book
basis I tried comes close on both at once (6 window×carry combinations × Kelly and flat columns).

On the books that could actually be armed, `crypto + sub_xvol_pullback` is:

| book | FTMO fwd/WORST | FTMO 2015-26/WORST | redacted_account fwd/WORST | redacted_account 2015-26/WORST |
|---|---:|---:|---:|---:|
| ALL 11 | *degenerate*¹ | *degenerate*¹ | *degenerate*¹ | *degenerate*¹ |
| SURVIVORS-4 | **48.9 %** | **62.9 %** | **68.5 %** | **74.2 %** |
| BOTH-3 | **62.0 %** | **69.9 %** | **66.8 %** | **73.1 %** |

¹ at worst carry the 11-sleeve book's winners and losers cancel (FTMO nets +11.86 of 197.91 gross), so a
share of the net is arithmetic rather than information; those rows are suppressed with their reason
rather than printed as 379 %.

So on redacted_account the two in-sample sleeves are **two-thirds to three-quarters** of the book, not 46.9 %,
because redacted_account's re-cost drops `metals_core` — the only sleeve with 131 trades and history back to
2015-03-19. **The doubt the dossier ranks first is bigger than the dossier states, for every candidate
book, on both accounts.** Nothing in this session or the last can shrink it; only forward out-of-sample
data can.

---

## 11. Claims I made during this session and then withdrew

1. **"Correcting the target will lower FTMO's `p_pass`."** I carried the commission's framing into the
   design and expected to publish a deterioration. The first 2,000-path smoke run showed `L4` *above*
   `L0` and I assumed a sign error in my own daily-basis branch. It was not: the drawdown basis is a
   second, larger, opposite-signed defect. **Correcting one rule of three would have produced a
   confidently wrong answer**, and it is the answer the commission asked for.
2. **`(1.0 - eq) >= maxdd_limit` as the static rule.** Correct as algebra, wrong at the boundary —
   `1.0 - 0.9` is `0.09999999999999998`, so a path sitting exactly on the $90,000 floor does not
   breach. Caught by a unit test written before the grid ran, not by inspection. Replaced with
   `eq <= 1.0 - maxdd_limit`, which is also the firm's own wording (a cash floor, not a fraction).
3. **A signed denominator for contribution shares.** It is the route's convention
   (`INTEG_portfolio_build.py:385`) and it degenerates silently: the 11-sleeve book at worst carry nets
   to ~6 % of its gross, and shares against it read 379 % and −358 %. Published for the first draft.
   Now suppressed with the net and gross both shown, on a stated threshold.
4. **A dial sweep across all variants.** Ran for ~7 minutes before I understood why: at a 0.5 % dial on
   a near-zero-drift series the barrier problem stops being drift-dominated and paths random-walk to
   the 10,000-day `PATHCAP`. The result would have been a `p_timeout` artefact presented as a `p_pass`.
   Restricted to the survivor variants, with the reason recorded in the code rather than in a commit
   message.

---

## 12. What this session did not do

- **It did not decide anything.** The dial, the sleeve composition, and whether to arm an account are
  Borhen's at OD-3. This is a measurement of rules that were mis-modelled; it is not a recommendation
  to trade, and §9 and §10 both run against the book.
- **It did not edit the sealed route.** `INTEG_portfolio_build.py:298` is untouched and
  `SURVIVOR_BOOK_V1.json` still reproduces byte-identically.
- **It did not fix `admission.py:52`** (FR2) — an owner question, one unbound line, prepared not landed.
- **It did not restate `W7_RECOST_V1.json`'s own MC grid** (nights 0–3 × flat/kelly × 3 dials, 11-sleeve
  book only). It carries the identical defect. It is not restated because no dossier or `CLAUDE.md`
  figure derives from it and the survivor decision does not use those cells — but a reader should not
  take its `p_pass` values as corrected.
- **It did not read a sealed window.** March remains outcome-unread.
