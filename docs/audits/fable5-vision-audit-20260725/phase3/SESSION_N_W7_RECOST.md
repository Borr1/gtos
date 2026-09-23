# Session N — Re-cost the W7 validation

**Stage 1 item 1.2.** Worktree `worktrees/wave3-w7-recost-20260727`, branch `phase3/w7-recost`,
**from `phase3/broker-truth` @ `7e36ac9dc`** — not from `main`. You need Session J's cost layer, and it
is not merged yet. **Your block range is B150–B164.**

**Read `../WAVE_3_WORKING_AGREEMENT.md` first.**

---

## What this is

**You decide whether GTOS's one positive validation survives contact with what trading actually costs.**

That is not framing. The programme has exactly one positive full-window validation in the tree — the
W7 core book's 2015–2026 evidence, 1,679 days, trade rows from 2015-03-19, per-sleeve depth from 11
years down to 12 months. Everything else measured negative. And the third review's central strategic
finding (§1.2) is that this one positive result is **invalid rather than negative**:

> Negative evidence cannot be repaired. Invalid evidence can, and cheaply.

Two defects contaminate it:

- **F38 — the cost model charges zero commission.** `src/components/broker_net_cost_engine.py:577-583`
  computes `spread_r + slippage_r + swap_r`. There is no commission term, at five independent sites.
  The system knew: `KB7_tick_truth.py:61-63` sets `COMMISSION_R = {s: 0.0}` under the comment *"If a
  venue charges commission, this is optimistic by that amount."* Self-declared, never propagated.
  Realized commission+swap was **31.6 % of the live W7 loss** (−12.69 R of −25.32 R).
- **F39 — the authorizing MC credits tick erosion with the wrong sign.**
  `INTEG_W7_FINAL_RESULT.json`'s `tick_erosion_applied` grants **positive** credits where reality
  charges a cost: USDJPY **+0.0179**, XAUUSD +0.019, USOIL_cash +0.037, applied as `R + h`
  (`KB7_tick_mc.py:62`). USDJPY's true charge is ≈ **−0.195 R** — a ~0.2 R/trade optimistic error on
  the sleeve family that lost 9 of 9 live.

Your output is `SURVIVOR_BOOK_V1` — **or an honest kill.** Both are wins. A kill that is correct is
worth more to Borhen than a survivor book that is wishful, because the next stage spends real money
against it.

## Why it is cheap

**Re-costing is arithmetic over cached rows, not a re-backtest.** The validation's exact input rows
survive in-tree, 678 KB:

```
research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/
    INTEG_W3_streams_cache.pkl        464,923 B
    INTEG_W5_new_streams_cache.pkl    212,951 B
```

The third review's adversarial pass reconciled these to CYCLE62's 1,679-day core-8 series **to the
day** — all 8 sleeves, per-trade sym/date/R. The rerun chain is resolvable from git at HEAD:
`KB7_growth_kelly_sizing.py`, `INTEG_W7_final_book.py`, `KB7_tick_mc.py`,
`CYCLE62_core8_revalidation.py`.

**Do not use `D4_COMBINED_TRADE_LEDGER.jsonl` as the restatement base.** The third review's first
draft named it and was wrong: it covers **7 of 8 sleeves** (no `fx_jpy_ny`) and its metals rows are a
re-simulation diverging from the consumed series by a mean |Δ| of **0.60 R** [verifier-measured]. It
is the re-sim coordinate source only.

## What you build on

Session J (Stage 1.1) shipped the cost layer this depends on, on your parent branch:

- `research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json` — per-account
  records, `conventions`, and **coverage classes `MEASURED` / `MODELLED` / `TRANSFERRED`**.
- `src/costs/model.py` — `cost_r(...)`, `commission_usd_per_lot(...)`,
  `swap_price_drag_per_night(...)`, `rollover_nights(...)`, `legacy_class_cost_r(...)`.
- `FIRM_RULES_V1.json`, `COST_LAYER_RECONCILIATION.json`, `TICK_SPREAD_MEASUREMENT.json`.

**Nothing downstream computes a cost any other way.** If `cost_r` cannot answer for a symbol, that is
a coverage fact to publish, not a gap to fill with a plausible number.

## The work

1. **Per-row re-cost** over the two caches, at the live dial, per account. Every row carries its
   coverage class through to the output — a survivor whose margin rests on `TRANSFERRED` costs is a
   different claim from one resting on `MEASURED`, and the dossier must be able to tell them apart.
2. **Both F39 readings, published as a sensitivity band.** The erosion map may have been spread-only
   or commission-inclusive by intent — `wave7_pairs_statarb.py:206-210`, same route, charges the map
   on top of a real spread crossing and calls it a *"slippage/commission proxy."* **The record cannot
   settle which was meant, and it has no generator** (`450a275f8` is a JSON-only diff, searched in
   both repo copies). So compute both. Do not pick one and justify it.
3. **MC re-run** with the erosion sign fixed and commission added, per account, at the live dial.
4. **Calendar-day restatement** — the original's day accounting is not the calendar's.
5. **`SURVIVOR_BOOK_V1`** — the cost-surviving sleeve subset, with per-sleeve margin, coverage class,
   and the band width — or the kill, stated as plainly.

## Known answers to check yourself against

From `GATE_G1B_RECEIPT.md` §5.2a, at the precision the third review's adversarial pass forced. If your
arithmetic disagrees with these, one of you is wrong and you must find out which **before** publishing:

- Commission is **zero on the six measured index CFDs**, near-zero on XAU/XAG (**0.0054 / 0.0013 R**),
  and **0.09–0.20 R** on the measured FX/JPY legs and BTC.
- **Commission alone kills USDJPY on the validation's own rows**: `fx_jpy` +0.116 gross − 0.195 → negative.
- **It dents but does not kill GBPJPY**: +0.219 gross − 0.093 survives. Its live death was *gross-edge*
  — which is exactly why the cost model never saw it coming.
- **BTC takes a ~13 % haircut.**
- Commission is **unmeasured** for energy/agri, DASHUSD, the four metal crosses, and ~24 % of
  `idxrev`'s index universe. Those carry as **`TRANSFERRED` bands**, never as zero.

**The tension you are being paid to resolve:** the surviving high-weight complex is metals+energy
(conf 1.00 / 0.80 / 0.50 / 0.30). The one fully commission-free sleeve, `idxrev`, is the registry's
lowest-weight, **train-falsified** sleeve — and the only live-profitable one. The status field did not
predict live sign (B63). Do not resolve that by preferring the tidy answer.

## Two corrections you must not inherit

1. **`metals_core` did NOT run a 2-of-6 symbol universe.** THIRD_REVIEW §1.2, B99b, D0 and Session K's
   own prompt all say it did. **Session K refuted it this week: `metals_core` ran 6-of-6 on FTMO and
   still produced nothing.** If you find yourself explaining a metals result by missing symbols, stop.
2. **88.5 % of the book's confidence weight is unmeasured by its own live window** (B63/B99b). The
   measured 11.5 % split JPY-negative, `idxrev`-positive. So the live fortnight cannot confirm *or*
   refute most of what you are about to re-cost — say so where it matters rather than borrowing
   confidence from it.

## Hazards specific to you

- **Your branch does not have the A/B tool's refusal guards.** Sessions L and M both hardened
  `scripts/pytest_failset.py` after a full-suite capture was SIGTERMed and the tool wrote a green
  baseline for a run that executed nothing — reporting *"694 fixed, 0 regressed, no regressions."*
  Those guards are on `phase3/evidence-packs` and `phase3/hygiene-batch`, **not on your parent**.
  Until integration, **check `pytest_returncode` and `totals` by hand on every capture before you
  trust it.** A capture with `totals: {}` is an absence of measurement, not an absence of failures.
- **Session K is running concurrently and the machine is memory-bound.** Five concurrent full suites
  last wave left 108 MB free of 16 GB and silently killed captures — that *is* the defect above.
  Stagger your full-suite captures; do not launch one while another is running.
- **H1: check decision-contract membership before editing anything under `src/`.** The R2 contract
  binds 43 paths by SHA-256 and a bound-file edit costs ~16.5 machine-hours per window to re-seal.
  `src/costs/` is new and unbound; `broker_net_cost_engine.py` may not be. Check, don't assume.
- **Derive, don't accumulate.** Two artifacts this week were false-green because they were built from
  a success log and so had no way to record what failed (Session M's whole thesis; K's D22; my own
  bars manifest, twice). If your output has a coverage or exclusion list, derive it by set-difference
  from the full expected set.
- **This repo uses sparse-checkout, and `git status` will lie to you about it.** Most of
  `research/operations/` is excluded (the tracked tree is 6.3 GB). A file can be committed on your
  branch, absent from your working tree, and **`git status` still clean** — the index carries the
  skip-worktree `S` bit. I already added `/research/operations/broker_truth_layer_2026_07_27/` for
  you, and both `INTEG_W*` caches were already in the set. If you need another research path:
  `git sparse-checkout add /research/operations/<dir>/`. Check `git ls-files -v <path>` for an `S`
  before concluding a file does not exist.

## Boundary

**You do not decide the dial, the sleeve composition, or the activation candidate.** Those are
Borhen's, made at OD-3 with your table in front of him. You produce the measurement and state its
uncertainty honestly — including what remains unproven: in-sample selection bias, and the book under
risk pressure (the gross-cap shed has zero live evidence).

Your table is **OD-3's first input.** Session K is producing the second.
