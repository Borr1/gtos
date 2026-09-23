# The challenge-account canary: what to run, and what it means

**Session AP (wave 10, B1350–B1399), for OD-AI-6. Modelled on `phase4/CANARY_OPERATOR_PAGE.md`,
which is the page for the FTMO funded canary and remains the authority for anything shared.**

This page is for a **challenge account carrying the candidate book** — `mx_btcusd` and
`sub_xvol_pullback`, two sleeves, registry weights. It does not exist yet. Nothing here arms
anything; the machine-readable package is
`phase10/receipts/CHALLENGE_ACCOUNT_PACKAGE_V1.json` and the ceremony checklist is at the end
of it.

---

## Read this first, because it changes how you read every number below

**This book is expected to be economically inert, and that is the point.** At the allocator's
own registry weights it earns **0.136 %/month** and needs **6.6 years** to a two-phase pass.
The control — the armed three on the same population — earns 0.313 %/month. You are not buying
return. You are buying the one thing no amount of archive work can produce: a **forward record
on real broker truth** for the estate's best new-edge candidate. `mx_btcusd` has **0 live
fills**; so does every armed sleeve.

**And the forward record will not be statistically decisive inside the challenge.** The
learning lane's own floor is 30 fills across 30 distinct days before it will re-rate anything.
At the book's measured ~7 book-days/month that is a multi-year wait, and the challenge phases
are measured in weeks. Expect long silences. Long silences are normal, not a fault.

**Three things bind what you may quote** (the ratified population rule's own conditions,
`phase10/receipts/POPULATION_RULE_V1.json` → `ratified_rule.conditions`):

1. **The band travels with the admission, always.** `mx_btcusd @ target_5R` is ADMIT at
   flat/low/mid and **REJECT at `band_high` (p 0.0051)**. Say "admits at two of three bands".
   Never a bare ADMIT.
2. **`target_5R` is the cell.** 5R's p 0.0011 clears both BH and Bonferroni; 4R fails
   Bonferroni.
3. **Size on the recent folds, not the pooled figure.** Folds 4–5 average **+0.198 R/day**
   against folds 1–3's **+1.504** — **13.2 %**. No gate can see chronological decay by
   construction. So the forward expectation for `mx_btcusd` is a fifth of what its ADMIT
   headline implies, and quoting +0.9817 R/day as a forward rate breaches the ratification.

---

## The five answers this page is for

| # | question | where it comes from |
|---|---|---|
| 1 | **Is the book the book?** Are both sleeves actually generating? | the launcher's `--tags` and the two include-flags |
| 2 | **Is anything reaching the broker?** | the activation token and the three gates |
| 3 | **Is the exit contract the one that was measured?** | `time_stop_bars` units and the target cell |
| 4 | **Has the admission moved under me?** | the ratchet and the band |
| 5 | **Should this stop?** | the stop conditions |

---

## 1. Is the book the book?

**Two sleeves, two different reasons they can silently vanish.** Check the command line, not
the heartbeat — a book that generates nothing looks perfectly healthy.

| check | command | wrong answer |
|---|---|---|
| the launcher passes both tags | `Select-String -Path scripts\run_book_supervisor.ps1 -Pattern '--tags'` | no `--tags` → **all BUILT sleeves trade** |
| `--tags` is not empty | read the resolved command line | `--tags ""` is **falsy** at `run_book.py:340` → fail-**open**, all sleeves |
| `--tags` has no typo | the book's own startup log lists its spec count | an all-typo tags list yields an empty spec list and the book stands down **silently every tick** (`registry.py:144` drops unknown tags with no fallback and no error) — fail-closed but **mute** |
| `sub_xvol_pullback` can generate | `Select-String -Path config\agent_config.yaml -Pattern 'ultimate_book_include_clean3'` | `false` → it is a clean_3 sleeve and `book_engine.py:452-453` drops it. This is exactly the step-ZERO read that `VPS_CEREMONY_PACKAGE_2.md` used for FTMO |
| `mx_btcusd` can generate | `Select-String -Path config\agent_config.yaml -Pattern 'include_market_expansion_book'` | `false` → it is one of the 12 resolved by `positive_weighted12_after_swap` and disappears |

`--tags` can only ever **subset**. `book_engine.py:452-453` intersects it with the include-flag
registry, so it can never add back a sleeve a flag removed. Two sleeves, two flags: a missing
flag reads as a healthy book with fewer trades.

**And arming mid-day is a size event.** `RunningConvictionLedger` persists a per-`decision_day`
**union** of firing sleeves and `admission.py:1188` takes `na = max(na, override)` — monotone
upward within the day. Restarting mid-day inherits that day's wider set, and under the
half-Kelly bins an `na` of 2 → 7 moves the multiplier 0.991 → 1.241: **+25.2 % on every unit
that day**. Arm at a decision-day boundary, or delete that namespace's
`pipeline_state/ultimate_book/<namespace>/firing_sleeves.json` first. Same-day hazard only.

---

## 2. Is anything reaching the broker?

The token is the switch and there is no config flag to disable it.

- `RealMT5.order_send` refuses any **exposure-increasing** request without a valid token for
  that account (`src/safety/activation_token.py`).
- **Risk-reducing requests pass without one** — closes, partial closes, pending cancels, stop
  tightenings. So an expired token can never strand a position.
- Revoke with `python scripts/gtos_activation_token.py revoke --profile <challenge_profile>`.
  Instant.

**Before minting, verify the host is running a tree where the token exists.** Session S
measured that the VPS's own `src/mt5/mt5_real.py` at `redacted_host` calls the raw module with **no
guard**. A new host provisioned from the VPS lineage inherits that, and the token layer becomes
decorative. Provision from **mainline**, or carry the guard as part of the ceremony. Same for
`mt5_preflight.py`: Session I's retirement of its order-placing arm is on mainline only, and
both VPS trees still carry four raw `mt5.order_send` calls at `:136, :142, :152, :155`.

**To disarm with positions open, flatten FIRST.** Setting `live_broker_authority: false`
returns before flattening (`book_owner.py:2364-2373`) and leaves positions open **and
unmanaged** — TP/SL moves, scale-outs, time stops and the governor breach-flatten all stop
reaching the broker (`:2526`). The broker-side SL/TP set at entry survive, so a gated position
is not naked; what is lost is everything else, and losing breach-flatten is the prop-fatal
part.

---

## 3. Is the exit contract the one that was measured?

**This is the check most likely to be quietly wrong, and it is why the package names the exit.**

`time_stop_bars` is **M15 printed bars for every sleeve** (`execution.py:8953-8958`). For a D1
sleeve like `mx_btcusd` that makes the live time stop **24–25 trading hours** against a 72–96 h
realised median — **72–90 % of its trades truncated**. Armed as configured, `mx_btcusd` earns
**−0.141 R/day**. On `target_5R` it earns **+0.309 R/day** on the as-walked eras and **+0.9817
R/day** on RECORDED at band_mid.

So: **if the book is running and the exit is not `target_5R`, you are running a sleeve nobody
measured, with a negative expected rate.** Check it before you look at the P&L.

The same applies to `sub_xvol_pullback` at `target_4R` (+1.157 R/day against +1.026 as-walked,
`AK_EXIT_FRONTIER_V2.json`). Wiring either is a registry/spec edit and **AK's measured safe
order is confidence weight FIRST, spec SECOND** — a Kelly-lite `unknown_sleeve` sizing hazard
of +32.5 % is pinned by tests.

---

## 4. Has the admission moved under me?

Two ways it can, both silent:

- **The ratchet.** Additions raise the bill and withdrawals never lower it. Any new look on
  either member restates their q. At `m = 35` and α = 0.10, BH rank 1 needs **p ≤ 0.002857**;
  `mx_btcusd @ target_5R` sits at **0.0011**, so there is headroom — AL measured the largest
  admitting family as **90** at α = 0.10 but only **45** at α = 0.05. The Bonferroni half has
  1.29× headroom and dies at m ≥ 46.
- **The band.** An AG-lane cost repair that reclassifies these eras moves the stamp, and the
  ADMIT rejects at `band_high`. A band change is a stop event, not a footnote.

`sub_xvol_pullback` is the fragile one and it is **already trading Borhen's FTMO money**. Its n
across the four populations is **88 / 85 / 56 / —**; at 56 it is NOT_EVALUABLE under
`B_balanced`, and it is NOT_EVALUABLE under `A_strict` on RECORDED. Its evidence disappears
under an option change *and* under a population change, independently. Putting it in this book
too **doubles** an FTMO leg rather than diversifying it.

---

## 5. Should this stop?

**Any one of these ends the run:**

1. the account breaches — the run has answered its question at the cost of the fee;
2. the ratified population rule is amended off `RECORDED` → the ADMIT falls and the book has no
   admitted member (`sub_xvol_pullback` is NOT_EVALUABLE on `decidable`);
3. the ratchet moves and a recomputed q crosses α = 0.10;
4. a cost-band restatement moves the arm's stamp.

**Do not rely on the learning lane's brake as the stop condition.** AE §3.1, in its own words:
*"this brake is weak and the correction made it weaker."* At the shipped `armed` scope a
genuinely dead `metals_core` has a **4.6 %** chance of being gated within its first 60 live
fills and `energy_agri` **14.5 %**. It is also **recommendation-only** — the lane never
actuates. A brake that needs a human is a report.

---

## What this page cannot tell you

- **Whether the candidate book is diversified.** It is not, on the evidence: AF refuted a
  crypto cluster as diversification (−0.1849 R/day, dispersion ratio 4.74, 1.80 R best-to-worst
  across nine symbols). Do not price a crypto cluster cap as diversification.
- **Whether `mx_btcusd` works.** It has no live fills at all. That is what this account is for.
- **Whether the exit is wired.** It is not. That is step 5 of the package's checklist and the
  largest unpriced item in it.
