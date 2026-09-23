# Session V — the MC for the book that is actually going to be armed

**Branch `phase4/armed-set-mc`, cut from `phase3/mc-true-target` @ `70d747e7e` (not from `main`).
Blocks B380–B409.**

Reproduce: `python3 scripts/armed_set_mc.py && python3 scripts/report_armed_set_mc.py`
Artifacts: `research/operations/w7_recost_2026_07_27/{ARMED_SET_MC_V1.json,ARMED_SET_MC_V1.md}`
Tests: `pytest tests/test_armed_set_mc.py tests/test_mc_firm_rules.py -q`
Full-suite A/B: `research/operations/w7_recost_2026_07_27/ab/SESSION_V_AB.md` — **662 bad → 662 bad by failure set, 0 regressed, +20 net new passing tests.** The first pass reported 6 regressions and they were real (§9 item 9).

---

## 0. The answer

**The commission asked what risk dial the `0.99675` assumes. It assumes 0.847 % per correlated
unit, and no governor at all. The profile Borhen approved runs 2.0 % per unit and a de-risk
ladder. Both halves are wrong, they run in opposite directions, and they very nearly cancel.**

FTMO, forward window, worst carry, at FTMO's measured rules, 200,000 paths:

| | `p_pass` phase 1 | `p_pass` 2-step | cal-days ph1 | %/month |
|---|---:|---:|---:|---:|
| **published** — 0.847 %/unit, no governor | 0.99918 | 0.99828 | 66 | 2.617 |
| live sizing — 2.0 %/unit, **no** governor | 0.96884 | 0.93876 | 30 | 5.460 |
| **live sizing + the live governor** | **0.99791** | **0.99591** | 33 | 5.460 |
| the same, from FTMO's actual $107,879.56 | **0.99987** | **0.99823** | 8 | 5.460 |

**I nearly published the middle row as the finding.** It is a real measurement and it is not what
will happen: the published MC omits the 4 % gross open-risk cap, the −9 % entry block, and
`derisk_mode: smooth` — and smooth alone is worth **+0.057 of `p_pass`** on the 2-step at worst
carry, which is almost exactly what the 2.09× of size costs. That is the same trap Session Q
documented: correct one thing, and check whether a neighbour was compensating. One was.

**So the honest headline is not that the owner's number is too good. It is that the number is
right for reasons nobody had measured, and that the reasons are not equally durable:**

- **The sizing gap is real and large.** Every published `p_pass` describes 0.847 %/unit; the
  configured profile applies **2.000 %** with no volatility term (§2). Measured multiple after the
  half-Kelly bins absorb part of it: **2.09×**. The dial at which the two conventions agree is
  **≈ 0.96 % nominal**, and nothing in `ALLOCATION_PROFILES` sits there.
- **What cancels it is one YAML value.** `ultimate_book_derisk_mode: "smooth"` — and
  `GovernorLimits.derisk_mode` defaults to **`"band"`** (`admission.py`, `DEFAULT_LIMITS` reads
  `GTOS_UB_DERISK_MODE` with a `"band"` fallback). The `admission.py:1432` interlock refuses the
  ≥ 2 % dial without smooth, so it will be on — but the published economics have never depended on
  a governor setting before, and now they do. **The number Borhen was shown is only true because of
  a guard that number does not model.**
- **And on the account being armed that guard is currently switched off.** Smooth measures drawdown
  from the **static** initial balance, so at $107,879.56 `evaluate_governor` returns
  `size_cap_multiplier` **1.0** (§3, measured by calling it). Its protection begins only after the
  account has given back all $7,879.56 it has made. From here it does not matter much — the target
  is 1.97 % away and most paths reach it before any drawdown — but the cancellation above is a
  fresh-challenge property, not a from-here one.

Three findings that stand independent of all that:

1. **The live 2.0 % dial's certification describes a different configuration** (§2a). Its
   `0.9553 / 0.9562 / 0.5021` match `two_account_final.staggered_2.00_1.50` uniquely — account A at
   **1.501 % effective**, account B at **1.50 % nominal** — while the profile sets both to 0.020.
2. **The concentration doubt is `crypto`, not `sub_xvol_pullback`** (§6). The sleeve the commission
   sent me to interrogate is ~11 % of the book; halving it costs 0.3 % of equity per month. Halving
   `crypto` costs **21 %** of the book and 4.8 points of `p_pass`. **And `p_pass` inverts the
   leave-one-out ranking**, so any composition argument made on it picks the wrong book — and the
   published survivor-book table is a `p_pass` table.
3. **The window every headline is computed on is the window that selected the sleeves** (§7).
   `build_survivor_book.py:60` and `KB7_growth_kelly_sizing.py:130` use the same `d.year >= 2025`
   predicate, the route's own adversarial audit says so in as many words
   (`AUDIT_exec_and_untouched.md` §(b)), and **`git grep` finds that file cited by nothing.**
   Outside the window the same four sleeves earn **+0.100 %/month** over ten years and
   **−0.220 %/month** before 2020, against the headline 2.617 %.

**§7 is the only one of these the governor cannot fix, and it is the largest.**

---

## 1. What licenses these numbers

Every figure below descends from `INTEG_portfolio_build_w2.mc_series` by a chain of steps each of
which is required to be **exact**, not close. The chain is longer than Q's because this session
re-expresses the day series as a per-sleeve matrix — the live sizer needs raw R, since it applies
confidence itself — so there is one more joint to prove.

| # | control | result |
|---|---|---|
| 0 | `scripts/build_survivor_book.py` re-run at this session's HEAD vs the committed `SURVIVOR_BOOK_V1.json` | **byte-identical** (sha256 `29858ef1…`) |
| 1 | `scripts/mc_firm_rules.py` 200,000-path run at HEAD vs the committed `MC_FIRM_TRUE_V1.json`, semantically | **0 differences** over every scalar, list and key |
| 2 | the same, byte-for-byte, through the two-command sequence that produced it | sha256 `886dcf69…f4301d` — **byte-identical** |
| 3 | pre-patch vs post-patch full 200,000-path runs, same command | **byte-identical to each other** |
| 4 | raw per-sleeve matrix → `comb_from` rebuilds `mc_firm_rules.series`'s own output, 24 cells | **0 mismatches, exact equality** |
| 5 | `mc_governed` ungoverned vs `mc_firm_rules.mc`, both sizing conventions, all five fields | **0 disagreements** |
| 6 | `mc_firm_rules.mc(LEGACY)` vs `INTEG_portfolio_build_w2.mc_series`, 24 cells × 20,000 paths | **0 disagreements** |
| 7 | this session's independent path reproducing Q's published `p_pass` at 200,000 paths | 0.99699 / 0.99918 / 0.99828 — **exact** |

Control 7 is worth stating separately: `armed_set_mc.py` reaches the four-sleeve forward/worst cell
through a completely different construction (matrix → divide out confidence → re-apply → fold
Kelly) and lands on Q's `L0 0.99699`, `L4 0.99918`, `P2 0.99828` to five decimals. The two code
paths agree, so a bug would have to be in both.

**Controls 1–3 are what the commission asked for by name, and the answer is not the one-line yes it
expected.** A single `python3 scripts/mc_firm_rules.py` does **not** write the committed file
byte-identically — and did not at HEAD either, before I touched anything. The whole difference is
the position of one top-level key: `contribution_shares` sits **last** in the committed document
and before `accounts` in any default run, because Q added it to `main()` after generating the
artifact and merged it in through `--shares-only`, which appends. 226,931 byte positions differ;
**0 values do.** The exact reproducing sequence is now in `mc_firm_rules.py`'s docstring. This is
precisely why the commission said to prove it by re-running rather than by reading the patch.

---

## 2. The sizing gap, and the number that fixes it

### What each convention does

**Published.** `scripts/build_survivor_book.py:64` sets `vs = sd_book / sd` and
`scripts/mc_firm_rules.py` inherits it: `risk = dial × vs`. `sd_book` is the **core-8, flat,
legacy-R** reference book's daily σ (0.56859); `sd` is the variant's own Kelly-folded σ over its own
book-days. For the four armed sleeves on the forward window that ratio is **0.4234**, so
`eff_risk_pct` is 0.847 — published in every cell of `SURVIVOR_BOOK_V1.json`, and not mentioned in
the OD-3 dossier.

**Live.** The chain is four lines and none of them is a volatility ratio:

- `config/agent_config.yaml` → `ultimate_book_profile: "clean3_w7_ceiling_nom2p00"`
- `src/components/ultimate_book/admission.py:1424` → `base_risk = prof.risk_per_unit_A` = **0.020**
- `:1473` → `effective_base = base_risk × gov.size_cap_multiplier` (the governor's de-risk, ≤ 1.0)
- `size_correlated_units` → `unit_risk = base_risk_per_unit × conf × derisk_mult`

`ultimate_book_kelly_conservative: true` selects `KELLY_LITE_BINS_HALF`
`((1,1,0.748),(2,3,0.991),(4,99,1.241))` where the sealed grid uses `(0.85, 1.10, 1.60)`.

Verified end to end by construction, not by reading: sizing one `metals_core` intent at the live
profile returns `unit_risk_pct` **0.020** exactly
(`test_live_sizing_chain_has_no_volatility_term`). Not 0.020 × 0.4234.

### Why the naive multiple is wrong

`1 / 0.4234 = 2.36×` is the obvious answer and it over-states the gap, because **half-Kelly is
itself a volatility reshape**. Measured on the four-sleeve forward series, `sd(half) / sd(full)` =
**0.8854**. So the live convention delivers `0.020 × 0.8854 = 1.771 %` in full-Kelly units against
the published `0.847 %` — a multiple of **2.09×**, not 2.36×.

That correction matters and it is exactly the pattern Q's session was built on: fix one thing, then
check whether a neighbour was compensating. Here one was, partially.

**A second divergence runs the same way and is larger than I first measured.** `intra_size` is a
research-side intra-sleeve confidence ramp: the generator sized a marginal setup down, and
`recost_w7_validation.build_matrix_from:897` folds it into the **return**, so every published figure
for these sleeves is conditioned on down-sizing weak setups. **The live generators for all four
armed sleeves never set it.** `TradeIntent.intra_size` defaults to 1.0 (`admission.py:849`) and the
only generator in the tree that passes a value is `generate_metals_softband`
(`sleeves/metals.py:218`) — not `generate_metals` (`:203`), not `crypto.py:65`, not
`energy_agri.py:62`, not `substrate.py:113`. The research rows carry mean `intra_size` **0.6698**
(`metals_core`), **0.6489** (`energy_agri`), **1.0817** (`crypto`), 1.0 (`sub_xvol_pullback`).

Measured both ways on the armed book, forward window, worst carry [MEASURED]:

| | window total R | daily σ | worst day | L4 `p_pass` |
|---|---:|---:|---:|---:|
| research convention (`R × intra_size`) | 49.14 | 1.1889 | −3.28 % | 0.96884 |
| **live convention (`intra_size` ≡ 1.0)** | **53.76** | 1.1913 | **−4.12 %** | 0.97789 |

The live convention is **better on edge (+9.4 %) and worse on the tail**. The worst day in the armed
book's forward history moves from −3.28 % to **−4.12 %** of equity — past
`ultimate_book_flatten_daily_loss_pct: 0.04`, so the **last-resort flatten tier would fire on it**.
The headline in §0 is computed at the *research* convention and is therefore ~0.9 pp conservative on
`p_pass` and understates the worst day by 26 %. I found the smaller version of this myself (+2.9 %,
from a wrong model of how live handles `intra_size`); the sizing refuter found the real one.

### The actionable number

The last column of `ARMED_SET_MC_V1.md` §1 is the nominal at which the live sizing chain delivers
exactly the risk every published figure assumes: `dial × reshape = 0.020 × vol_scale`, i.e.
**≈ 0.956 % nominal** for the armed book at worst carry. **If Borhen wants the `p_pass 0.99918` he
was shown, that is the dial it describes.** Nothing in `ALLOCATION_PROFILES` sits there — the
nearest lower W7 dial is `clean3_w7_measured_nom1p25` at 1.25 %, and the W5 `clean3_balanced_eff0p71`
is a *different convention again* (it pre-multiplies its own vol scale into the constant, which the
W7 dials deliberately do not).

### 2a. The live dial's own certification describes a different configuration

`ALLOCATION_PROFILES["clean3_w7_ceiling_nom2p00"]` carries `base_p_both 0.9553`, `fwd_p_both
0.9562`, `stress15_p_both 0.5021`. Searching `INTEG_W7_FINAL_RESULT.json` for those three values
returns exactly one row — **`two_account_final.staggered_2.00_1.50`**:

| | account A | account B |
|---|---:|---:|
| certifying row, nominal | 0.02 | **0.015** |
| certifying row, **effective** | **0.01501** | 0.01126 |
| the live profile | 0.020 | **0.020** |

Two things follow. The certifying run was **staggered**, so the "P(both)" the profile advertises
describes account A at 2.0 % and account B at 1.5 %, not both at 2.0 %. And account A's certified
risk was **1.501 % effective** — `0.020 × VS_final 0.7504` — because the locked W7 MC vol-matched.

The live package is aware of this and justifies it (`ultimate_book_live_package.py:561-567`): *"the
volatility reshape is the KELLY-LITE conviction multiplier … matching the locked W7 MC where the
Kelly-folded series was vol-matched at VS_final=0.7504."* **Measured on that same basis — 11
sleeves, legacy R, full window — half-Kelly's reshape is 0.8216, not 0.7504.** So the live dial runs
`0.020 × 0.8216 = 1.643 %` in full-Kelly units against a certified 1.501 %: **1.095×**, a 9.5 %
overshoot on the book of record.

That is a small number and it is the *right* small number. The claim in the live package is
approximately true for the 11-sleeve book it was written about — half-Kelly really does absorb most
of the vol match there. It fails badly for the **four-sleeve** book, where the required reshape is
0.4234 and half-Kelly can only deliver 0.885. **The justification does not transfer to a sparser
book, and the survivor book is much sparser.**

---

## 3. The live governor, modelled inside the bootstrap

The published MC applies a constant risk to a scalar daily series. The live path does four more
things, and `mc_governed` models three of them (the fourth cannot be modelled and is stated in §7):

**The 4 % gross open-risk ceiling** (`admission.py:1294`, shed by
`_enforce_gross_open_risk_cap:1321`). It binds when the day's total `base × conf × kelly` exceeds
4 %. For the armed four that needs three sleeves firing together: at `n_active` 3 the day wants
`1.982 + 1.685 + 1.586 = 5.25 %`; at 4 it wants **7.69 %**. **On the forward window that happens on
1 of 128 book-days (0.78 %)** — the armed book is `n_active` 1 on **85.9 %** of its days, 2 on
13.3 %, 3 on 0.8 %, and never 4. The MC's own count of cap-bound draws agrees at 0.74–0.78 %.

So the cap is **almost inert for the armed book**, which is worth saying plainly because I expected
the opposite before measuring it. It is emphatically *not* inert for the currently-configured live
book, which generates from 11 + 9 candidate + 14 market-expansion sleeves.

Two further live facts about the shed, both from production code, neither of which changes the
armed book's numbers but both of which change how a reader should think about it: the shed is
**first-fit-descending, not lowest-conviction-first** (`admission.py:1331-1341`, the docstring D1
corrected in wave 3), so on the one 3-active day it drops the *third*-strongest sleeve while keeping
a weaker one that fits; and the cap counts risk still open from **prior** days, which this model does
not — with 320-hour horizons that means the live cap binds at least as often as measured here.

**`derisk_mode: smooth` is what makes the published number true, and it is not in the published
model.** From a fresh $100,000 challenge, adding the 4 % cap and smooth to the live sizing moves the
armed book at worst carry from **0.96884 → 0.99791** on phase 1 and **0.93876 → 0.99591** across the
2-step — recovering essentially the whole 2.09× sizing cost, at 10 % more calendar time (30 → 33
days). The cap contributes ~nothing (it binds on 0.78 % of days); **the recovery is smooth.** So the
published `0.99828`, computed at a sizing no live path uses and with no governor at all, lands
within 0.0024 of the live configuration's 0.99591 — by the cancellation of two errors of opposite
sign, neither of which had been measured.

**And the guard is currently switched off on the account being armed.** `admission.py:1286-1303`
measures drawdown from the **static** initial balance, so `cap_mult = 1 − dd/0.10` only when
`dd > 0`. Called directly at the two accounts' actual equities:

| account | equity | `size_cap_multiplier` | reason |
|---|---:|---:|---|
| redacted_account | $96,229.28 | **0.622928** | `derisking_into_maxdd_wall` |
| FTMO | $107,879.56 | **1.0** | `ok` |

The redacted_account value reproduces the commission's `0.622928` exactly, which is a useful check on both.
The FTMO value is the finding: **the interlock at `admission.py:1432` refuses the ≥2 % dial unless
`derisk_mode == "smooth"`, and smooth provides zero size reduction until the account is back below
$100,000.** The guard the ceiling dial is conditioned on starts working at the point where the
account has already lost everything it has made. That is correct behaviour for a drawdown defender
and it is not a reason to be comfortable at 2.0 % today.

From FTMO's actual equity the distinction matters less than it looks, because the target is 1.97 %
away and most paths reach it before any drawdown: with the whole governor, from here, the armed book
is `p_pass` **0.99987** on phase 1 in a median 8 calendar days and **0.99823** across the 2-step in
27. But that is the *distance to target* doing the work, not the guard. §3 and §4a of
`ARMED_SET_MC_V1.md` have the full grid, including `p_fail_entry_block` — the −9 % block is
absorbing in this model and is counted against the book, at 0.0021 (from $100,000) and 0.0001 (from
here) at worst carry.

**The −9 % entry block.** `max_dd_entry_block_pct: 0.09` stops new entries before the −10 % wall. In
this model that is **absorbing** — no open positions, no further entries, equity can never move
again — so it is recorded as its own outcome `fail_entry_block` and counted against the book rather
than allowed to hide inside `p_timeout`. (First version let it fall through to `timeout`; corrected
before the artifact was generated.)

---

## 4. The arming mechanism, verified rather than assumed

The commission's trap is right and it is worth pinning down exactly, because the mechanism decides
whether the measured book is the armed book.

- `sub_xvol_pullback`'s registry confidence is **0.45** (`admission.CLEAN3_REGISTRY`), below
  `metals_softband`'s 0.50. **No confidence floor selects it**, so `--tags` is the only mechanism.
- All eleven sleeves are in `BUILT` (`src/components/ultimate_book/sleeves/registry.py`), so
  `--tags metals_core,crypto,energy_agri,sub_xvol_pullback` selects exactly those four and drops
  nothing silently — `active_specs` returns all four [MEASURED].
- `--tags` restricts **generation**; `include_clean3` gates **admission**. With
  `ultimate_book_include_clean3: false` and `sub_xvol_pullback` in `--tags`, its intents are
  generated and then its whole cluster-day unit sizes to **0** with reason
  `fail_closed:unknown_sleeve:sub_xvol_pullback` [MEASURED, by calling `size_correlated_units`]. The
  failure is loud, not silent — but it silently produces a *three*-sleeve book if nobody reads the
  reason field.
- **`scripts/run_book_supervisor.ps1:108-109` does not pass `--tags`.** It passes
  `--terminal-path`, `--namespace`, `--profile`, `--kill-flag`, `--poll-seconds`. Arming the
  four-sleeve book therefore requires an edit to the supervisor as well as the two config flips.
  That is a VPS/orchestrator matter and is out of this session's scope; it is recorded because a
  plan that assumes `--tags` is already wired would be wrong.

---

## 5. The three sets, at the dial that will run

FTMO, forward window, at FTMO's measured rules. `published` is the vol-matched convention,
`live` is the 2.0 %-nominal half-Kelly one. Full grid, all six window × carry cells and all
four books, in `ARMED_SET_MC_V1.md` §2.

| book / carry | eff risk | worst day | **L4 p_pass** | cal-d | %/mo | **P2 p_pass** | P2 cal-d |
|---|---:|---:|---:|---:|---:|---:|---:|
| ARMED-4 / 0 nights | 0.835 % | −1.19 % | 1.00000 | 49 | 3.798 | 1.00000 | 80 |
| ARMED-4 / 0 nights *live* | 2.000 % | −2.58 % | 0.99846 | 22 | 8.042 | 0.99645 | 38 |
| ARMED-4 / 1 night | 0.836 % | −1.22 % | 1.00000 | 49 | 3.717 | 1.00000 | 80 |
| ARMED-4 / 1 night *live* | 2.000 % | −2.63 % | 0.99789 | 25 | 7.858 | 0.99528 | 41 |
| **ARMED-4 / WORST** | **0.847 %** | **−1.54 %** | **0.99918** | **66** | **2.617** | **0.99828** | **110** |
| **ARMED-4 / WORST *live*** | **2.000 %** | **−3.28 %** | **0.96884** | **30** | **5.460** | **0.93876** | **52** |
| FLOOR-3 / WORST | 0.825 % | −1.50 % | 0.99886 | 76 | 2.273 | 0.99767 | 126 |
| FLOOR-3 / WORST *live* | 2.000 % | −3.28 % | 0.96005 | 32 | 4.862 | 0.92339 | 58 |
| BOTH-3 / WORST | 0.856 % | −1.36 % | 0.99772 | 81 | 2.133 | 0.99577 | 132 |
| BOTH-3 / WORST *live* | 2.000 % | −2.86 % | 0.95210 | 36 | 4.402 | 0.91016 | 63 |
| ALL-11 / WORST | 0.861 % | −3.80 % | 0.83283 | 54 | 2.261 | 0.73344 | 91 |
| ALL-11 / WORST *live* | 2.000 % | **−6.84 %** | 0.63416 | 19 | 3.995 | **0.48423** | 32 |

**The 11-sleeve book of record does not survive its own historical worst day at live sizing.** At 0
nights it is −5.08 % and at worst carry −6.84 % of equity, against a 5 % hard daily wall — so the
book of record has days in its own record that breach outright at the dial the profile is set to.
That is a property of the dial, not of the carry assumption; at the published sizing the same days
are −2.67 % and −3.80 %.

At the published sizing the three candidate books are indistinguishable on `p_pass` at worst
carry — 0.9977 to 0.9992, all of them — and separated only by rate and time. **At ungoverned live
sizing they separate**: 0.969 / 0.960 / 0.952 on phase 1 and 0.939 / 0.923 / 0.910 across both
phases. **With the live governor they close again**: 0.99791 / 0.99621 / 0.99479 on phase 1 and
0.99591 / 0.99289 / 0.98998 across both, from a fresh challenge (§3). The ordering never changes;
the separation is a property of how much unmodelled risk each model leaves in, not of the books.
Whatever the sizing, the composition question is small next to what §7 does to all three.

**Carry becomes visible only at live sizing.** The published spread from 0 nights to worst carry is
1.00000 → 0.99918, a change of 0.0008. At live sizing it is 0.99846 → 0.96884, a change of 0.030.
So the carry band OD-3 has been waiting on is worth **37× more at the real dial than at the modelled
one** — which cuts both ways: it says the carry work mattered, and it says the sizing question
dominates it, because the *same* 2.09× is what made carry visible in the first place.

## 6. Concentration — and the answer is not the one the commission expected

**The question: how much of the four-sleeve advantage survives if `sub_xvol_pullback` is
half as good as it looks? Answer: half of it, and half of it was never much.**

The advantage of ARMED-4 over FLOOR-3 at worst carry is **+5.38 R** over 128 forward
book-days, on a FLOOR-3 base of 43.76 R — **+12.3 %** of monthly rate (5.460 % against
4.862 %). Halve `sub_xvol_pullback` and the advantage is +2.75 R, **+6.3 %**. Zero it
entirely and the advantage is +0.12 R, **+0.3 %**. It scales linearly, because it *is* that
sleeve's edge.

**So the four-sleeve book does not collapse to the three-sleeve book — but the two were
never far apart.** The premium for adding a sleeve the live config calls a selection
artifact is one third of one percent of equity per month at full strength.

Four corrections my own first version needed, all from the concentration refuter, all
published rather than quietly amended:

**6.1 — A shared sleeve must be haircut in BOTH books.** My first version cut `crypto` in
ARMED-4 only and differenced against an uncut FLOOR-3, publishing `beats_conf_floor3:
false` at λ ≤ 0.5. `crypto` is in both books, so that is a category error and the flag was
wrong in sign on 8 of 10 λ values per cell. Haircut both and the ARMED-4-vs-FLOOR-3 gap
moves from +5.380 to +5.270 as crypto goes from full strength to zero edge — **a 2 %
move.** The composition decision is very nearly invariant to `crypto`, which is exactly
what it should be, because `crypto` cancels. **A reader of my first artifact would have
concluded that half of Session N's concentration doubt kills the armed set. It does not
touch it.**

**6.2 — The break-even λ of 0.0 was a bisection failure, not a measurement.** `lo, hi =
0.0, 1.0` with the advantage positive everywhere halves `hi` to 2⁻³⁰ and reports 0.0 with
no failure signal — indistinguishable from a genuine root at zero. The advantage is exactly
linear in λ, so it is now solved: the true break-even is **λ = −0.023** at worst carry
(−0.058 at 0 nights).

**6.3 — A zero-edge fourth sleeve is not neutral, and the binary test is nearly
worthless.** Adding any sleeve raises `n_active` on the days it fires, which raises the
Kelly multiplier for the other three. Measured by substituting a sleeve with the identical
13-day firing pattern, the same dispersion and zero edge: **a worthless fourth sleeve beats
FLOOR-3 59.8 % of the time** (i.i.d. bootstrap of the demeaned values; 91.8 % under a
permutation, which pins the sample mean at exactly zero). The pure Kelly/day-axis artifact
is worth **+0.47 R in expectation**, ~9 % of the observed advantage. So `beats_conf_floor3`
carries almost no information. **The magnitude does survive**: P(null advantage ≥ observed)
= **0.006**.

**6.4 — The paired bootstrap advertised 128 days for a test whose effective sample is 13.**
The two books differ by one sleeve, so the difference series is exactly 0.0 on every day
that sleeve did not fire — 115 of 128. The right instrument at n = 13 is the exact
sign-flip test over all 8,192 patterns: **p = 0.0106**, against the block bootstrap's
0.0073 at block 5 (and 0.0048 at block 1, 0.0002 at block 20 — non-monotone, which is the
tell). And block 5 is not supported by the data: the daily series' ρ₁ is **0.062** against a
±0.177 band, every lag to 10 sits inside it, and the variance inflation factor is
**0.924 — below 1**. Session R's ρ₁ 0.441 is a property of
*when* `crypto` trades, not of the book's daily returns, and the bootstrap resamples
returns. Block sensitivity is now published beside the headline.

**What the concentration numbers actually say.** By leave-one-out at worst carry, live
sizing:

| dropped | book-days | total R | sd | L4 p_pass | cal-d | %/mo | **passes/yr** |
|---|---:|---:|---:|---:|---:|---:|---:|
| *(none — ARMED-4)* | 128 | 49.14 | 1.189 | 0.96884 | 30 | 5.460 | **11.79** |
| `sub_xvol_pullback` | 120 | 43.76 | 1.220 | 0.96005 | 32 | 4.862 | 10.95 |
| `metals_core` | 117 | 39.62 | 1.174 | 0.95210 | 36 | 4.402 | 9.65 |
| `energy_agri` | 82 | 32.68 | 1.293 | 0.94700 | 43 | 3.631 | 8.04 |
| **`crypto`** | 83 | 29.53 | **0.778** | **0.99986** | **57** | 3.692 | **6.40** |

**`p_pass` inverts the ranking and `passes/yr` does not.** Dropping `crypto` cuts the
book's daily σ by 35 % and its mean by 7 %, so the drawdown barrier becomes almost
unreachable — `p_pass` **0.99986**, the best of any variant — while the book loses a third of
its trading days and takes nearly twice as long. `crypto` is simultaneously the largest
edge (≈ 40 % of the book), the largest risk, and the worst thing to keep by `p_pass`. **Any
composition argument made on `p_pass` alone will pick the wrong book**, and the published
survivor-book table is a `p_pass` table.

**The concentration doubt is `crypto`, not `sub_xvol_pullback`.** The commission's framing —
*"`sub_xvol_pullback` is therefore both the reason the four-sleeve book outperforms the
three and the sleeve most likely to be a selection artifact"* — is right on the first half
and misdirects on the second. `sub_xvol_pullback` is ~11 % of the book and halving it is
worth 0.3 % of equity per month. Halving `crypto` costs **10.1 R of 49.1 (21 %)** and drops
`p_pass` from 0.969 to 0.921. Session N's 46.9 % names both sleeves; only one of them is
load-bearing, and it is the one nobody proposed dropping.

## 7. The thing that is bigger than everything above

**The window every headline is computed on is the window that selected the sleeves.**

`scripts/build_survivor_book.py:60` filters the "forward" window with `d.year >= 2025`.
That predicate is character-for-character the one the original sleeve selection used as its
verdict gate — `KB7_growth_kelly_sizing.py:130` and `INTEG_portfolio_build_w2.py:331`, both
`d.year >= 2025`.

The route's own adversarial audit says so, in as many words
(`AUDIT_exec_and_untouched.md` §(b), committed, 9,014 bytes):

> **"Finding: NO clean out-of-sample slice exists.** The entire **2025-26 forward window …
> was the FORWARD HOLDOUT that served as the verdict gate** for sleeve selection, conf
> weights, the HEATOIL/NATGAS drop, and the aggression dial. … They are a forward *holdout
> vs training*, but they are **not OOS vs model selection** — the sleeves and dial were
> chosen to look good on exactly this window."

**`git grep -l AUDIT_exec_and_untouched` returns nothing.** Not the dossier, not
`SURVIVOR_BOOK_V1.md`, not Session N's or Session Q's reports, not `CLAUDE.md`. The one
document in the repository that names the defect is cited by nothing that depends on it.

Measured — the armed four-sleeve book, FTMO, worst carry, at both sizings:

| window | book-days | bd/month | mean R/day | **%/mo published** | L4 published | **%/mo live** | L4 live |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2015–2019 | 27 | 0.49 | **−0.323** | **−0.220** | 0.00003 | −0.279 | 0.00060 |
| pre-2025 (2015–2024) | 118 | 1.00 | 0.083 | **0.100** | 0.76760 | 0.148 | 0.68779 |
| **2025+ — the selection window** | 128 | **7.11** | 0.435 | **2.617** | 0.99918 | 5.460 | 0.96884 |
| all 2015–2026 | 246 | 1.81 | 0.266 | 0.463 | 0.98365 | 0.851 | 0.90573 |

**26× the monthly rate inside the selection window, and negative outside it before 2020.**
Both terms move: the edge per book-day is 5.3× higher and the firing frequency is 7.1×
higher. The frequency ramp is monotone — the book's density of weekday sessions runs 0.4 %
(2015) to 28.7 % (2025), and **52 % of all 246 book-days fall in the last 18 of 136
months.**

`monthly_pct_calendar` is *linear* in `book_days_per_calendar_month`, and 7.11 is the
selection window's value. On the full window it is 1.81, and the median calendar month has
**one** book-day.

That is not a reason to disbelieve the recent regime. It is a reason not to treat
`2.617 %/month` as an out-of-sample expectation, which is how it reads in the dossier and
in `CLAUDE.md` §4.

**What the live window says about the frequency assumption.** Across the whole 38-day live
W7 window the three live-eligible armed sleeves fired **zero** times. Under the forward
window's own day pattern, resampled to preserve clustering, P(zero book-days in 38 days) is
**≈ 0.010** — about 1 in 96. One observation is not proof and I will not present it as one.
But the OD-3 dossier uses **7.11** book-days/month for the economics and, on a facing page,
a much lower implied rate to excuse the silent live window. Those two rates differ by ~3×
and cannot both be right.

**One commission claim refuted.** The prompt states that `crypto` "emitted 219 packets in
that window with 216 skipped for a **missing instrument config**". Measured over all 99,112
packets: `crypto` has 219, and **216 are `(crypto, DASHUSD, redacted_account_live_bee34003)` —
redacted_account only.** On the account being armed, `DASHUSD` **is** configured
(`config/profiles/operator_profile.yaml:1021`) and is one of `crypto.py:24`'s two
on-surface symbols. **FTMO ran `crypto` 2-of-2 and got nothing.** The missing-instrument
story explains the redacted_account half of that number and none of the FTMO half — which is the
half that matters, because FTMO is the account being armed.

## 8. What I would arm

Not a recommendation on the dial — that is Borhen's. A plain statement of what the
measurement supports.

**1. The composition choice does not matter much, and it is not where the risk is.** Four
sleeves versus three is worth **+12.3 % of monthly rate** at full strength and **+6.3 %**
under an honest halving of the marginal sleeve, with `p_pass` differing by under a
percentage point at either sizing. The advantage is statistically distinguishable from zero
(exact p = 0.0106 on an effective sample of 13 days) but it is in-sample to the selection
window, so that p-value is worth much less than it looks. **If the four-sleeve book is
armed, `sub_xvol_pullback` is not the reason it will work or fail.**

**2. The 2.0 % dial is defensible, and it is defensible for a reason that is not in the
document that justified it.** At the profile as configured the armed book runs at **2.09×
the risk every published figure describes** — and the live governor, which the published
model omits entirely, gives essentially all of it back: 2-step `p_pass` **0.99591** from a
fresh challenge against the published 0.99828, at **roughly twice the speed** (33 calendar
days against 66, 5.460 %/month against 2.617 %). **On that comparison the dial is not the
problem I expected it to be.**

What I would say to Borhen about it is narrower and, I think, more useful: **the published
economics now depend on `ultimate_book_derisk_mode: "smooth"`, and they never used to.**
`GovernorLimits.derisk_mode` defaults to `"band"`; only the `admission.py:1432` interlock
keeps smooth on at ≥ 2 %. A dial move below 2 % releases that interlock, and at 1.25 % or
1.5 % nominal the book would run with a weaker guard and the same unmodelled sizing
convention. **The step-up path in the config comment — 1.50 % after the first account clears
— is the configuration this measurement does not cover.** If the dial moves, the governor
should be pinned explicitly, not left to an interlock that no longer applies.

**3. From here, phase 1 is close to a formality and phase 2 is the whole question.** FTMO
needs **$2,120.44** — 1.97 % of current equity — against **$17,879.56** of room to a static
$90,000 floor, with its 4-day minimum already served. From that start, at live sizing,
phase 1 is `p_pass` **0.998** in a median **8 calendar days**. The two-step from here is
**0.973** in 27 days. **Everything that can go wrong goes wrong in phase 2**, which starts
fresh at $100,000 with none of the head start — and the head start was made by the live
core-8 book, not by these four sleeves.

**4. The measurement does not support the four-sleeve book as an out-of-sample
proposition, and it never could have.** §7 is not a refinement; it is the finding. On the
only slices that are not the selection window the same book earns **0.100 %/month** over ten
years and is **negative** before 2020. The published 2.617 % is an in-sample-to-selection
number, the repo's own audit says so, and nothing downstream cites it.

**So, plainly.** If the purpose of arming is to start a forward out-of-sample record, arm
it — that is the only thing that can settle §7, and it is exactly the OD-3 dossier's own
argument. **The four-sleeve set at 2.0 % with `smooth` is what the measurement supports**, and
the composition question inside it is small enough that I would not spend another session on
it. What I would not do is carry the `2.617 %/month` forward as an expectation: the honest
expected rate for a book whose edge is measured only inside its own selection window is
somewhere between **0.1 % and 5.5 % per month**, and nothing in this repository can narrow
that. Size the position to the fact that the range is that wide, not to the `p_pass` at the
top of it.

**A clean negative where one exists:** the eleven-sleeve book of record does **not** clear a
two-phase evaluation at live sizing on the forward window — `p_pass` **0.48423** — and its
worst historical day at that dial is **−6.84 %** of equity against a 5 % hard wall. That is
not a marginal call.

## 9. What I got wrong, and withdrew

Four refuters, four lenses, and every one of them overturned something. The largest
withdrawal is my own and no refuter caught it. Published rather than amended:

0. **"The armed book is 36× more likely to fail than the owner has been told."** I had that
   written as the session headline, from a correctly measured comparison of the published
   sizing against the live sizing. It is wrong because the comparison is not the right one:
   the published model omits the live governor as well as the live sizing, and
   `derisk_mode: smooth` is worth **+0.057 of `p_pass`** on the 2-step at worst carry —
   almost exactly what the 2.09× of size costs. At the live sizing **with** the live
   governor the armed book is `p_pass` **0.99591** across the evaluation against a published
   0.99828, at twice the speed. I found this by running the governed MC I had already
   written, after the headline was drafted. **It is the exact trap this session's commission
   named** — Q's "correcting only one thing would have reported a deterioration that does
   not exist" — and I walked into it.
1. **"The live path applies no volatility term at all."** False of the module. `admission.py`
   pre-multiplies `CLEAN3_VOL_SCALE = 0.9481` into every W5 `clean3_*` profile (`:686-731`).
   The W7 dials dropped it deliberately (`:752-760`). The correct claim is "**the configured
   profile** carries no vol term". Withdrawn and restated everywhere.
2. **"Half-Kelly is 9.5 % short of the vol match."** True arithmetic, wrong diagnosis.
   `INTEG_W7_final_book.py:171` — `VS_final = round(sd_book / sd_final, 4)  # Kelly runs
   hotter -> smaller vol_scale` — shows the vol match exists **to undo Kelly's inflation**.
   Kelly folding *raises* the series σ from 0.5997 to 0.7837. So the live package's claim
   that the Kelly multiplier *is* the reshape inverts cause and effect, and a milder Kelly
   can only ever stand in for part of it. And the certification the live config actually
   cites, `CYCLE62_CORE8_REVALIDATION.json`, is **not on HEAD** (recovered from `5d6dde09b`)
   and declares `core8.vs 0.8647`, `eff_pct 1.729` = `0.02 × 0.8647` — so
   `agent_config.yaml:1304`'s "half-Kelly … -> eff ~1.73 % on core-8" also mis-attributes a
   vol-scale product to the Kelly multiplier. Against that certification the overshoot is
   **1.157×**, not 1.095×.
3. **"The 4 % gross cap will bite hard at 2.0 %."** I expected it to be the dominant
   governor term. Measured: it binds on **1 of 128** forward book-days (0.78 %), because the
   armed book is single-sleeve on 85.9 % of its days. `admission.py:1340-1341` already
   records that the cap never bound once in the live W7 fortnight, across 668 units. Retracted
   before it reached the artifact.
4. **The crypto haircut rows, the break-even λ, the paired bootstrap's effective sample, the
   LOO `p_pass` ranking** — all four wrong in my first artifact, all four fixed in §6, all
   four found by a refuter rather than by me.
5. **Byte-identity of `MC_FIRM_TRUE_V1.json` from one command.** I claimed the commission's
   check would be a single re-run. It is not, and was not at HEAD either — see §1 and the
   note now in `mc_firm_rules.py`'s docstring.
6. **`--shares-only` was a live foot-gun I introduced.** Under `--kelly live_half_bins` it
   would have silently rewritten every published share in the committed artifact on a
   different basis, injected rows for an ad-hoc book, and written **no marker**, because the
   `sizing_convention` block sits on a path that branch returns before reaching. Now refuses,
   with a test. I had also written in a code comment that `sealed_shape` was "asserted by
   tests" when no such test existed; both the claim and the gap are closed.
7. **`mc_governed` "reduces exactly" to the sealed engine.** It reduces exactly *on this
   data*, not by construction: `(Σⱼ mⱼ·k)·risk` and `Σⱼ risk·confⱼ·k·rawⱼ` are different
   floating-point expressions and **50.26 % of the 18,480 real day-values differ bitwise**,
   by ≤ 3 ulp. A constructed series where `dp` lands on exactly −0.05 flips `p_fail_daily`
   from 1.0 to 0.0. It cannot happen here — the tightest barrier approach in the whole grid
   is 2.8 × 10⁻⁹ against a perturbation bounded by ~10⁻¹⁵ — but the docstring claimed a
   theorem and now states the measurement. The control was also only ever run at the sealed
   convention, never at the half-Kelly one every headline uses; it now runs both.
8. **`frequency_profile`'s "median" was the upper median** — 7 book-days/month where the
   true median is 6.5, printed beside the 7.11 mean that multiplies every monthly figure.
9. **My new test file broke six unrelated tests, and only the full-suite A/B could have
   found it.** `scripts/research/` is a **regular** package (it has an `__init__.py`), and a
   regular package beats a namespace portion at any `sys.path` position — so the moment
   `scripts/` becomes searchable, `import research` resolves there and `research.operations.*`
   stops resolving **for the rest of the process**. Every one of these scripts puts
   `scripts/` on the path to reach `recost_w7_validation`, and
   `tests/test_audit_b6_broker_cost_calibration.py` and
   `tests/test_b7_5_post_acceleration_contract.py` both import through `research.operations`.
   `tests/test_armed_set_mc.py` sorts alphabetically **ahead of both**, which took a latent
   hazard load-bearing: **6 tests moved from passing to failing, with nothing in the diff
   that could explain them.** Q's `tests/test_mc_firm_rules.py` carries the identical line and
   never triggered it, because `test_mc_*` sorts after `test_b7_5_*`. Fixed at the source in
   all six files that do it (`scripts/mc_firm_rules.py`, `armed_set_mc.py`,
   `build_survivor_book.py`, `tests/test_mc_firm_rules.py`, `test_armed_set_mc.py`,
   `test_w7_recost.py`) by pinning the repo-root package in `sys.modules` before extending
   the path, and pinned by
   `test_importing_this_module_does_not_break_the_research_namespace_package`, which asserts
   the property rather than the fix. **A scoped A/B would have missed this entirely**, which
   is the argument for the working agreement's full-suite rule stated as a measurement rather
   than a preference.

## 10. What this does not fix

Everything here runs in the optimistic direction, so the live-sizing `p_pass` figures remain an
upper bound in the same way Q's did.

**10.1 — Every item in Q's §9 survives unchanged.** Trade-entry-day accounting rather than an equity
curve; both firms measuring equity continuously including open P/L, which this model cannot express
because no exit index survives in any cache; redacted_account's weekend-holding prohibition on the funded
account; and overfitting, which no amount of re-sizing touches any more than re-costing did.

**10.2 — The soft daily stop is not modelled and cannot be.** `ultimate_book_soft_daily_stop_pct:
0.03` blocks new entries once realized intraday P&L reaches −3 %. At live sizing the armed book's
worst historical day is **−3.28 %**, so the soft stop is inside the observed range — but the MC has
one P&L value per day and no intraday sequence, so the stop has nothing to fire on. Its effect would
be to truncate the worst days, which runs *for* the book, and to cut short some good ones.

**10.3 — The gross cap is modelled per book-day only.** Live it counts risk open from prior days, and
the armed sleeves carry 320-hour horizons. The 0.78 % measured here is a floor.

**10.4 — The `intra_size` convention divergence (+2.9 %) is measured but not folded in.** It runs
against the book.

**10.5 — Phase 2 is modelled as a fresh account at the initial balance**, per Q. The OPS-03
profit-target protect (`ultimate_book_profit_target_pct: 0.10`, `derisk_mult 0.25`) cuts new-entry
size to a quarter once equity reaches $110,000 and stays there until the account is reset, which the
model does not represent. It runs *for* the book (it locks in the pass) and it is why the config
comment instructs the owner to move the key to 0.05 at the phase transition.

---

---

## 11. What is left, and what I did not do

- **I did not decide anything.** The dial, the sleeve composition and whether to arm are
  Borhen's at OD-3. §8 is what the measurement supports, not a proposal.
- **I did not touch the VPS, arm anything, mint a token, flip a gate, or run a
  broker-capable script.** `run_book_supervisor.ps1`'s missing `--tags` (§4) is recorded, not
  changed.
- **I did not edit the sealed route.** `INTEG_portfolio_build.py:298` is untouched;
  `MC_FIRM_TRUE_V1.json` still reproduces (§1) and pre-patch and post-patch runs are
  byte-identical to each other.
- **I did not fix `agent_config.yaml:1304`'s mis-attributed `eff ~1.73 %` comment**, or the
  `clean3_w7_ceiling_nom2p00` docstring that quotes a `staggered_2.00_1.50` row (§2a).
  `config/agent_config.yaml` is **decision-contract-bound** (H1), and the live package's
  profile statistics are the owner's economic contract, not a hygiene fix. Both are prepared,
  neither is landed.
- **I did not measure redacted_account.** `armed_set_mc.py --account redacted_account` runs, and the
  grid is symmetric, but only FTMO is being armed and redacted_account's survivor set is a
  different four sleeves (Q §10.1). Its governor is already at `size_cap_multiplier`
  **0.622928**.
- **The one thing that would settle §7 is forward out-of-sample data**, and nothing in this
  repository can produce it. That is the OD-3 dossier's own argument for arming, and this
  session does not weaken it — it only says what size the argument supports.
- **The next unit of work I would pick** is not another MC. It is to put §7 in front of
  Borhen beside the dossier's §2 table, because the dossier presents a
  selection-window number as an expectation and the repository's own audit already said
  not to.
