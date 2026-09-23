# v1 — verify the wave-20 repairs: is it safe, and is it real?

**Lane:** v1 (verification). **Under test:** commits `029b2fc1c`, `119cc40e3` (lane r1) and
`5f72e6772` (lane r2), against parent `8dd9b07c0`. Seven files: two modified, five new.

Nothing here was taken from either lane's own reasoning. Every claim below was re-derived by
execution against the primary data, and where the lanes published a number I reproduced it from
their inputs with my own code before believing it.

---

## 0. Headline

**The repairs are safe and they are real — and the wave's own armed-money analysis is wrong at both
ends of the armed set.** Three artifacts (`r1_estate_rewalk.py:75-81`,
`tests/test_broad_origin_emission_repairs.py:424`, `R2_RESULT_V1.json → live_isolation`) declare the
same four sleeves. That list **omits `sub_mid_dn_revert`, which is armed on both accounts**, and
**includes `mx_btcusd_d1_donchian_20_breakout`, which the owner disarmed on 2026-08-05** (D-2 CLOSED,
host `2fa77722d`, `phase19/SESSION_FA_CONTINUATION_RESULT.md` on the sibling branch; the committed
launcher was never updated and still lists it).

The omission is the expensive half. Under r1's own correction `sub_mid_dn_revert` loses **59.6 %** of
its published gross — `+0.47842 → +0.19325 R/trade` on 533 trades with 38 exit-reason changes — the
largest proportional hit of any armed sleeve, and it never entered r1's fold or p-value receipts.
The inclusion is free: `mx_btcusd`'s estate delta is exactly **0.00000** on 318 trades.

Everything else checks out, including the parts that could have been wrong:

| check | verdict |
|---|---|
| full-suite A/B vs parent, by failure set | **96 bad → 95, 0 regressed, +66 net new passing** |
| armed-sleeve behaviour, 556,251 generator calls | **byte-identical stream hash** |
| H1 drift at HEAD | 3 entries, **identical to before the wave** (1 pre-existing + 2 LFS pointers) |
| r1 uncorrected arm == published estate `r_gross` | **22,354/22,354 exact, worst diff 0.0** |
| r2 census, reproduced from the rosters by my own code | **25,243 / 11,880 / 897,501 exact** |
| r2 blast radius, reproduced independently | **90,216 + the 1 cross-asset leader = 90,217 exact** |
| do the two repairs compose? | **yes — 92 rows of 25,243 (0.36 %) disagree** |
| quote-side convention vs REAL BID/ASK TICKS | **right, and exact on longs; 31 % short-side residual** |

---

## 1. Full-suite A/B against the parent commit

**Method.** BEFORE was produced by physically reverting the tree, not by reasoning about it:
the two modified files restored with `git restore --source=8dd9b07c0 --worktree`, the five new
files moved out of the tree entirely (so they neither run nor error at collection), and
`git diff --stat 8dd9b07c0 -- src/ tests/` verified empty. Both arms ran the identical command
in the identical worktree; the restore afterwards was checked by sha256 against a snapshot taken
before the revert and came back **byte-identical on all seven files**.

```
NO_COLOR=1 python3 scripts/pytest_failset.py capture -o {before,after}.json
python3 scripts/pytest_failset.py diff before.json after.json
```

| | failed | errors | **bad** | passed | skipped | xfailed |
|---|---:|---:|---:|---:|---:|---:|
| **BEFORE** (parent source state) | 52 | 44 | **96** | 12,398 | 213 | 31 |
| **AFTER** (HEAD) | 51 | 44 | **95** | 12,464 | 213 | 31 |

**unchanged 95 · fixed 1 · REGRESSED 0 · net new passing +66** (65 new tests — 27 r1 + 38 r2 —
plus the one fixed row). `diff` exits 0.

The single "fixed" row is **an environment flake, not a repair, and I am not claiming it**:
`tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment`.
Its module's import closure is 51 modules and contains none of the four touched modules; its test
file imports nothing from them; it passes deterministically in isolation at HEAD (4 runs). It
asserts behaviour around a 28 GiB free-space hard floor while this volume sits at 92 % capacity
with 37 GiB free.

**One thing the tooling needed before this A/B was possible.** `scripts/pytest_failset.py`'s
summary-line regex is `^(FAILED|ERROR)\s+…`, and this shell exports **`FORCE_COLOR=3`**, so pytest
emits `\x1b[31mFAILED\x1b[0m …` and the parser recovers **zero** node ids. It fails loud
(`usable_as_baseline: false`, `diff` refuses) — which is the right design — but it is why lane r1
downgraded to a scoped A/B, citing an unparseable full-suite capture at this same parent commit.
`NO_COLOR=1` in the environment fixes it without changing a single pytest argument, so both arms
stay identical. Worth writing into the tool.

The committed baseline (`receipts/FAILSET_BASELINE_MAIN.json`, 2026-07-31, `bca8c4466`) is
**not usable as the before side here**: it records 1 failed / 0 errors / 12,705 passed / 120
skipped against this worktree's 52 / 44 / 12,398 / 213. It was captured in a fully materialised
tree; diffing against it would report ~95 false regressions. Hence the physical revert.

---

## 2. Armed-sleeve safety, by execution

### 2.1 The armed set is FIVE, from the repository's own launcher

`scripts/run_book_supervisor.ps1:86` (FTMO) and `:87` (redacted_account):

```
FTMO       tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout"
           frontier="mx_btcusd_d1_donchian_20_breakout"   spreadFloor="sub_mid_dn_revert,sub_xvol_pullback"
redacted_account tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert"
```

`tests/test_broad_origin_emission_repairs.py:424-429` declares `ARMED_SLEEVES` as four and the
docstring three lines below it says *"The five armed tags"*. `r1_estate_rewalk.py:75-81` declares the
same four. `R2_RESULT_V1.json → live_isolation.armed_sleeves` publishes the same four.

**And the launcher is itself one step behind the host.** `mx_btcusd_d1_donchian_20_breakout` was
**disarmed on FTMO on 2026-08-05 by owner instruction** (host commit `2fa77722d`, D-2 CLOSED in
`phase19/SESSION_FA_CONTINUATION_RESULT.md`, which lives on the sibling branch
`phase19/broad-forensic`); `scripts/run_book_supervisor.ps1` was never updated on either branch and
still carries it. So the truly-armed set today is **four on each account —
`crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert`** — and the lanes' four-sleeve list
manages to be wrong at both ends: it contains the one sleeve that is no longer armed and omits one
that is. Everything in §2.2 is measured over the **union** of both readings, so no conclusion here
depends on resolving it.

### 2.2 No armed decision moves — proved by running them

`receipts/v1/v1_armed_behaviour.py` drives each armed sleeve's **own generator callable**, resolved
from `sleeves/registry.active_specs`, over **every** decision instant in the FTMO M15/H4/D1 archive
(`vps-bars-20260727`), on a fixed 400-bar window, and hashes the emitted `TradeIntent` stream.

| | calls | emissions | stream sha256 |
|---|---:|---:|---|
| HEAD | 556,251 | 1,213 | `a89d5f5a15b48d08eb0796ecb8b8386dc8f08e0c0508249504f0afd1c6b0d06c` |
| parent (`8dd9b07c0`, tree physically reverted) | 556,251 | 1,213 | `a89d5f5a15b48d08eb0796ecb8b8386dc8f08e0c0508249504f0afd1c6b0d06c` |

**Identical.** Not "no diff found" — the same 64 hex characters over a stream that encodes every
field of every emitted intent, in order, at full float precision. If any armed sleeve had changed
one decision, one direction, one stop distance or one target on any bar of the archive, the hash
would differ.

Per sleeve at HEAD: `crypto` 21,442/180, `energy_agri` 16,248/68, `sub_xvol_pullback` 152,245/94,
`sub_mid_dn_revert` 363,608/577, `mx_btcusd_d1_donchian_20_breakout` 2,708/294.

### 2.3 And they cannot move, structurally

Measured in a clean interpreter (`receipts/v1/v1_live_closure.py`), not read off a grep:

* `run_book.py`'s module-level import closure is **240 modules (84 project)** and contains
  **none** of `broader_origin_generators`, `broad_origin_emission_contract`, `walkforward.exits`,
  `walkforward.quote_side`.
* Importing the live decision core — `book_owner`, `book_engine`, `admission`, `sleeves.registry`,
  `order_router`, `components.execution` — pulls **189 modules (94 project)**, again none of the four.
* All five armed generators resolve to
  `sleeves/{crypto,energy_agri,substrate,market_expansion_d1}.py`; the registry's whole closure is
  53 modules and contains none of the four.

---

## 3. H1 — the drift state after the edits

Re-read at HEAD with the LFS caveat applied:

```
DRIFTED:        src/components/broker_net_cost_engine.py          <- pre-existing, CN, owner-authorised
UNHYDRATED-LFS: …/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl   <- not drift
UNHYDRATED-LFS: …/SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl                     <- not drift
bound paths checked: 43
```

**Three entries, one real, unchanged from before the wave** — `broker_net_cost_engine.py` is not in
the wave's diff (`git diff --name-status 8dd9b07c0..HEAD` is seven files, none of them bound).
Neither contract mentions any of the four touched files: a recursive scan of every `path` key in R1
and R2 returns 46 and 48 paths and **zero** substring hits for `broader_origin_generators.py`,
`broad_origin_emission_contract.py`, `exits.py` or `quote_side.py`. None is in the runner's
`code_authority_paths` (`replay_acceleration_attempt5_typed_sparse_runner.py:1405-1431`). **No new
option spent.**

### 3.1 But "not bound" is a weaker claim than either lane made it

`src/research_infra/v4_timewarp_simulated_live_research_loop.py` **is** an R2-bound path *and* is in
`code_authority_paths`, and at `:56` it imports
`broader_origin_generators.generate_live_broader_origin_candidates` at module level — the exact
function r2 changed. `broader_origin_generators.py` is not sealed by anything.

Measured (`receipts/v1/v1_seal_hole.py`): **54 project modules are reachable by import from that
bound file; 10 are sealed; 44 are not.** So r2's default-ON change alters what a future sealed
replay would generate **while every drift check and the execution-seal digest report zero**. The hole
is pre-existing and structural — wave 20 is the first change to walk through it. The mitigation
already exists and works (`LEGACY_EMISSION_POLICY`, proven byte-exact on 174,497/174,497 rows), but
it only helps an operator who knows to reach for it.

---

## 4. Attacking r1 — the quote-side walker, against real ticks

`receipts/v1/v1_tick_truth.py`. Ground truth is a **tick-level round trip** on
`vps-ticks-20260726` (broker epoch → true UTC), transacting on the side the live engine transacts
on: LONG pays the ask at the decision bar's last tick and exits on the bid; SHORT hits the bid and
exits on the ask; stop wins ties. That is compared against both bar-walk conventions on the same
archive bars, target 2R, maxbars 80, M15, **61,106 round trips over 13 symbols, whole population of
the overlap window.**

### 4.1 The convention is right, and on longs it is essentially exact

| | uncorrected bias | corrected bias | removed |
|---|---:|---:|---:|
| **LONG** (n = 30,553) | +0.138168 | **−0.004600** | **96.7 %** |
| **SHORT** (n = 30,553) | +0.198961 | **+0.061750** | **69.0 %** |

(bias = bar walk − tick truth, in R; positive = the bar walk over-reports.)

Exit-reason agreement with tick truth improves on both sides: LONG 28,656 → 30,086 of 30,553;
SHORT 28,095 → 29,336.

### 4.2 The residual is direction-asymmetric, and the cause is measured

A LONG's stop and target are **bid**-quoted and the tape **is** the bid, so nothing about a long's
exits needs a spread at all — only its entry does, and the entry spread is known exactly at the
entry tick. That is why the long residual is −0.0046.

A SHORT's exits are **ask**-quoted, and the walk approximates the ask as `tape + spread at entry`.
The ask's own excursion is not the bid's plus a constant: measured on the resolving tick, the spread
at exit is **1.02–1.99×** the spread at entry, symbol by symbol. Regressing the short residual on
`(exit/entry spread ratio − 1) × spread/stop` across the 12 symbols with a resolving population gives
**Pearson r = 0.954**; the same regression on longs gives **r = −0.357** with a mean residual of
−0.0045. The mechanism is not inferred, it is the fit.

Consequence, stated as a bound rather than a restatement: **the estate's corrected gross of
−0.027726 R/trade is itself still optimistic on its short leg.** 9,571 of the estate's 22,354 trades
are short (42.8 %). At the pooled short residual that is roughly +0.026 R/trade still unpriced — but
it is **per symbol**, and the armed sleeves are the good case: BTCUSD's short residual is −0.0098,
ETHUSD −0.0162, USOIL +0.0132, UKOIL −0.0074. The two armed substrate sleeves are **100 % long**
(0/533 and 0/88 short), so they carry no residual at all. `crypto` (39.8 % short on BTC/DASH) and
`mx_btcusd` (32.7 % short) sit on the smallest-spread symbols in the book. **No armed conclusion
moves.**

### 4.3 The archive-is-BID identity, re-settled a third time

Independently, on a third tick read and a different join (last tick of each M15 bar vs that bar's
close): **30,601 of 30,603 exact, rate 0.999935, worst mismatch 0.045 spreads.** r1 published
1.000000 on its own M15 join; mine finds two exceptions, both sub-1/20-of-a-spread. The claim stands;
the exact rate does not.

### 4.4 One sentence in the shipped module is wrong, in the direction that flatters

`quote_side.py:216-224` (`entry_trigger_level_on_tape`) says a long's level "is reached one spread
EARLY in tape terms … it is the reason a limit book fills more often than an unshifted walk
believes." The **function** is correct — its own test pins `T(100, +1, 1, BID) == 99.0` — but 99 is
*below* 100, so which side of "early" you land on depends on the approach:

| order | tape trigger | approach | vs the unshifted walk |
|---|---:|---|---|
| BUY LIMIT (POI demand zone) | 99.0 | falling into it | **LATER — fills LESS often** |
| BUY STOP (breakout) | 99.0 | rising into it | EARLIER — fills more often |
| SELL LIMIT / SELL STOP | 100.0 | either | unchanged |

The broad V4 POI families — `current_fvg_fill`, `current_ob_retest`, `current_breaker_re_entry` —
are exactly the limit case, so the generalisation is wrong for the family it was written about, and
wrong in the optimistic direction. `r1_broad_rewalk.py:184-190` states the same limit honestly and
does not model it, so **no published number moves**. Docstring corrected in this lane; demonstration
at `receipts/v1/v1_limit_fill.py`.

---

## 5. Attacking r2 — the emission contract

### 5.1 Its census reproduces exactly, from the rosters, with my code

`receipts/v1/v1_r2_compose.py` re-derives the bins from the same eight rosters:

| bin | mine | `R2_CENSUS_V1.json` |
|---|---:|---:|
| `past_stop` | 25,243 | 25,243 |
| `marketable` | 11,880 | 11,880 |
| `target_through` | 897,501 | 897,501 |
| `resting` (POI only) | 131,728 | 276,453 − 144,725 at-market = 131,728 |

### 5.2 Its blast radius reproduces exactly, including the one exotic row

`receipts/v1/v1_union.py`, all 1,211,077 rows: `past_stop` 25,243, stale (age ≥ one period) 66,383,
intersection 1,410, **union 90,216**. r2 published **90,217** removed. The difference is exactly the
single cross-asset-leader refusal r2 itself named and measured (USOIL_cash, 2025-12-31 20:15 UTC),
which is not visible to a per-row test on the emitting symbol. 90,216 + 1 = 90,217.

### 5.3 Do r1 and r2 compose? Measured, and yes

r2 asks "is the market beyond the stop" using `current_price = the selected bar's close` — which r1
settled is the **bid**. A long buy limit transacts on the **ask**, so the strictly-malformed test for
a long is `gap < −1 − spread/risk`, not `gap < −1`. r2 therefore over-refuses a thin band of longs
and is **exact for shorts** (a sell limit transacts on the bid, which is the close).

Measured on the whole POI population with the era-aware spread model:

* long past-stop refusals **9,450**, short **15,793**
* **92** of the 25,243 refusals are over-refusals — **0.36 %**
* whole-population bins move `past_stop` 25,243 → 25,151

**The composition holds.** And the 92 are not free money either: `gap < −1` on the bid means the
stop was breached on the quote the stop is watched on, so those orders would have been stopped
immediately anyway.

### 5.4 Where r2's pricing is convention-dependent, and it does not say so

r2 prices the past-stop rows at **−1.30135 R/row net** by walking them from the **limit price**. In
MT5 a buy limit above the market is not placeable, and a marketable one fills at the market, not at
the limit. So the −1.30 is a property of the estate's own walker; the real-money counterfactual sits
somewhere between "the order is rejected and there is no trade" (0 R) and that figure. r2 states this
caveat for the near-side radius dial (`R2_RESULT_V1` narrative) and does **not** carry it to defect
A's headline. **The repair is still right** — refusing to emit a malformed order needs no economic
argument — but "removes 26.54 % of the roster's net loss" is a statement about the measured roster,
not about money.

Two smaller ones, both filed rather than changed:

* `fill_gap_r` (`broad_origin_emission_contract.py:175`) resolves the side as
  `"LONG" if side.upper() == "LONG" else SHORT` — anything unrecognised silently becomes a short and
  flips the sign. Every call site passes the literal `"LONG"`/`"SHORT"`, and
  `broader_origin_generators.py:482` already used the same idiom before this wave, so there is no
  live exposure; it is a latent fail-open.
* the same docstring calls the marketable bin "fills now, **worse** than limit". For a buyer filling
  below their limit, and a seller filling above theirs, it is **better**. Corrected here.

---

## 6. What I changed

1. `src/research_infra/walkforward/quote_side.py:219` — `entry_trigger_level_on_tape`'s "fills more
   often" generalisation replaced with the per-order-type table it is actually true of (§4.4).
2. `src/components/broad_origin_emission_contract.py:185` — the marketable bin's "worse than limit"
   corrected; the walker-convention caveat r2 applied only to the near-side dial carried to the bin
   description; and the bid/ask boundary of §5.3 recorded where the predicate lives (§5.4).
3. `tests/test_broad_origin_emission_repairs.py:424` — `ARMED_SLEEVES` extended from four to the
   **five** the launcher actually carries, plus
   `test_armed_sleeves_matches_what_the_committed_launcher_actually_arms`, which parses the tag
   lists out of `scripts/run_book_supervisor.ps1` so the constant is derived rather than
   remembered. Arming a sixth sleeve now fails a test instead of silently invalidating an
   isolation proof.

**Edits 1 and 2 are provably inert.** `receipts/v1/v1_docstring_inert.py` parses each file at
`5f72e6772` and at HEAD, strips every module/class/function docstring, and compares
`ast.dump`: **identical** for both production modules. No executable statement changed, so no
number can move. (The test file's AST does change — it gained a test.)

Targeted re-run after these edits: `test_broad_origin_emission_repairs` +
`test_broad_origin_emission_contract` + `test_quote_side` + `test_wf_exits_parity` = **98 passed**
(97 before, +1 for the new launcher test).

---

## 7. Open, for the owner and the next lane

1. **`sub_mid_dn_revert` needs the treatment r1 gave the other four.** Armed on both accounts,
   −0.2852 R/trade gross under the correction (−59.6 %), 38 exit-reason changes in 533 trades, and no
   fold/p-value receipt exists for it at the corrected numbers.
2. **The short-side residual is unpriced.** ~31 % of the quote-side bias survives r1's correction on
   short trades because the walk uses one entry-instant spread for ask-quoted exits. Fixing it needs
   a per-bar spread series, not a per-trade scalar.
3. **44 unsealed modules are reachable from a sealed one.** Either bind the reachable set or publish
   the transitive closure alongside the contract, because "not in the bound list" is currently read
   as "cannot change a sealed result" and it is not the same statement.
