# Session J — The broker-truth layer

**Stage 1 item 1.1.** Worktree `worktrees/wave3-broker-truth-20260727`, branch `phase3/broker-truth`,
from `main` @ `1e95fe7fa`. **Your block range is B110–B119.**

**Read `../WAVE_3_WORKING_AGREEMENT.md` first.**

---

## What this is, and why it comes before everything economic

**One function owns every cost number in GTOS.**

```
cost_r(symbol, account, holding_hours) -> {commission_r, swap_r, spread_r, slippage_r}
```

backed by a versioned `BROKER_TRUE_COSTS_V1.json`. Nothing downstream computes a cost any other way.

The reason this is Stage 1's first item is F38, and it is the largest economic finding in the
programme's history. **The validation and the live pre-trade engine charge zero commission at five
independent sites.** Verify the core of it yourself in one read:
`src/components/broker_net_cost_engine.py:577-583` computes `spread_r + slippage_r + swap_r`. There is
no commission term. Meanwhile realized commission+swap was **31.6 % of the live W7 loss** (−12.69 R of
−25.32 R).

The system knew. `KB7_tick_truth.py:61-63` sets `COMMISSION_R = {s: 0.0}` under a comment that reads
*"If a venue charges commission, this is optimistic by that amount."* Self-declared, never propagated,
and the whole 2015–2026 validation rests on it.

**Your layer is what makes Session-after-next's re-cost possible.** The re-cost (Stage 1.2) is
arithmetic over cached rows — but only once there is a trustworthy `cost_r` to apply. You are building
the thing that decides whether GTOS's one positive validation survives.

## What it owns

**Costs.** Session E measured the substrate: commission by instrument from broker truth; slippage
**+0.013 R** measured (half the modelled figure); stops fill clean at **−1.0036 R gross**. Vendored
spec comparison at `research/operations/vps_broker_truth_2026_07_26/BROKER_SYMBOL_SPEC_COMPARISON.json`
— note **18 of 19 shared symbols carry differing `trade_contract_size` between the two brokers**, and
JP225 differs in `digits`/`point`/`trade_tick_size` too. Spread comes from the tick archive at
`/Users/borr/GTOSActive/vps-ticks-20260726/` (1.9 GB, 191.9 M rows, 2026-06-18..07-24) — whose `time`
columns are **broker wall clock, not UTC**; convert with `broker_clock.broker_epoch_to_utc` and never
trust a `_utc` field name.

**Firm rules.** Same layer, because they are the same class of fact and have been asserted from memory
before. The two daily-reset clocks (**FTMO 00:00 CE(S)T; redacted_account 00:00 server time** — different
calendars, B56/B58), max-DD and daily-loss rules, and **a payout-rules capture per firm, done the way
the reset clocks were captured** — from the firm's own page, not from recollection. Broker truth exists
in the export for **all three accounts** (`VPS_EXPORT_FINDINGS.md` V5), which is what will let the
dossier's MC be per-account rather than generic.

## The design rule that makes this trustworthy

**Every number carries a coverage class, and the class travels into every result computed from it.**

- **[MEASURED]** — observed on this account, this instrument.
- **[TRANSFERRED]** — inferred from a comparable instrument; the band is wider and says from what.
- **[MODELLED]** — no observation; a stated assumption with an owner and a date.

Plus **×0.5 / ×1 / ×2 sensitivity bands** on anything not [MEASURED].

This matters because the coverage is genuinely uneven, and the unevenness is economically decisive.
Per `GATE_G1B_RECEIPT.md` §5.2a: commission is **zero on the six measured index CFDs**, near-zero on
XAU/XAG (0.0054 / 0.0013 R), and **0.09–0.20 R on the measured FX/JPY legs and BTC**. It is
**unmeasured** for energy/agri, DASHUSD, the four metal crosses, and ~24 % of `idxrev`'s index universe.
A re-cost that silently modelled those as zero would repeat F38 with better manners.

**A number without a coverage class is not a number this layer emits.** Make that structural — schema,
not convention.

## What it replaces

Name each site and route it through the new layer, or state why it cannot be:

1. The **five zero-commission sites** (F38). Find all five; the review names the engine, do not assume
   it named them all.
2. The **wrong-sign erosion application** (F39) — the MC credited tick erosion with the wrong sign, e.g.
   USDJPY **+0.0179 R credited where reality charges ~−0.195 R**. Note the record is genuinely ambiguous
   about intent (spread-only vs commission-inclusive map); the re-cost will publish **both readings as a
   band**, so your layer must be able to express both.
3. The **unenforced spread floors** (F40).

## Two things to check rather than assume

1. **`broker_net_cost_engine.py` already has commission *machinery*** — `commission_model_status`,
   `commission_model_required`, `DEFAULT_ALLOWED_COMMISSION_STATUSES` including one literally named
   `..._NO_EXECUTION_CRITICAL_COMMISSION_GAP`. So there is a gate that asserts commission is handled
   while the arithmetic omits it. Understand that mechanism before replacing it; it may be the cleanest
   seam, or it may be the trap.
2. **H1.** `broker_net_cost_engine.py` is under `src/components/`. **Run the membership check before
   editing it.** `config/agent_config.yaml` and both FTMO profiles are bound. If the correct wiring
   needs a bound file, deliver the layer plus the exact prepared change and surface the re-seal cost to
   Borhen — do not absorb that decision.

## Deliverables — the floor

1. `src/costs/` (or your better location, argued) with `cost_r`, behavioural tests, and the coverage
   class as a first-class typed field.
2. `BROKER_TRUE_COSTS_V1.json` — versioned, per account, per instrument, with provenance per number.
3. The firm-rule capture: two reset clocks, DD/daily-loss rules, **payout rules per firm from source**.
4. A site-by-site map of the five F38 sites, F39 and F40: routed, or stated why not with the cost.
5. A statement of coverage: which instruments are [MEASURED], which [TRANSFERRED], which [MODELLED] —
   because Stage 1.2 will publish exactly that as its band.
6. `IMPLEMENTATION_STATE.md` blocks **B110–B119**, and a full-suite A/B by failure set, committed.

Commit scoped work as you go, push your branch, do not merge to `main`.
