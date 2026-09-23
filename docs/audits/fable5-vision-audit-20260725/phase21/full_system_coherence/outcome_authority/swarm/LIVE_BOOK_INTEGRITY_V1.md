# Live-book integrity: the two accounts are not the same book, and the cluster envelope is back on

**Owner-approved 2026-08-12** ("proceed as proposed and recommended in everything").
Task 1 is measurement only. Task 2 ended in an **executed, verified live config change** —
`ultimate_book_one_unit_per_cluster_per_day` is `true` on the host as of
**2026-08-11T10:39:42Z**, both activation tokens re-minted, both books restarted and proven
through the engine's own authorization choke point.

Receipts: `live_book_integrity_receipts/`. Every broker read in this lane used only
`initialize / account_info / positions_get / symbols_get / symbol_info / terminal_info /
shutdown`. **No `order_send`, no `order_check`, no `order_calc_*` was called at any point.**
Account numbers are redacted as `redacted:<sha256[:12]>`, the estate's convention.

---

## 0. What changed, in one table

| | before | after |
|---|---|---|
| `config/agent_config.yaml` (host) | sha256 `a2d5c675…`, 266,147 B | sha256 `c3059d0a…`, 267,235 B |
| `ultimate_book_one_unit_per_cluster_per_day` | `false` (`:1303`) | **`true`** (`:1314`) |
| FTMO token → config digest | `ffe16657feaf…` | **`0b0dbe307379…`** |
| redacted_account token → config digest | `e184a81d3b1b…` | **`8540f9a9f302…`** |
| token expiries | 2026-09-09T13:02:25.644Z / :33.457Z | 2026-09-09T13:02:26.390Z / :34.899Z (**preserved**) |
| FTMO worker PIDs | 6208 / 5708 | 11056 / 10844 |
| redacted_account worker PIDs | 1172 / 3956 | 11256 / 11232 |

**Not touched, by design:** the halt/flatten ordering, the activation-token *layer* (only the
tokens themselves were re-minted to match the new digest — the mechanism is unchanged), the
blackout, `--tags` (`crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert` on **both**
accounts, before and after), `--spread-geometry-floor`, every sleeve's geometry, the risk
dial, the exempt-cluster list, and the three authority gates. **Mainline config was NOT
edited** — the host and mainline configs already differ (`include_clean3`), and editing
mainline would break this repository's R2 execution seal for nothing.

---

# TASK 1 — the two accounts are not running the same book

## 1.1 The gap is the BROKER, not the profile — and that is the load-bearing distinction

Lane F (`56a860709`) measured 13 unreachable symbol slots on redacted_account from the book's own
telemetry. The obvious follow-up is whether that is a **profile-config omission** (fixable by
adding instrument blocks) or a **broker limitation** (not fixable at all). It is the second.

`live_book_integrity_receipts/symbol_universe_probe.py`, run on the host against both live
terminals, reproduces the engine's own resolution (`apply_profile_overrides` →
`build_broker_symbol_resolver` → `active_specs`) and then asks each broker directly:

| | FTMO | redacted_account |
|---|---:|---:|
| active symbol slots (armed 4 sleeves) | 42 | 42 |
| profile-supported | **42** | **29** |
| unreachable | **0** | **13** |
| profile instrument blocks | 42 | 32 |
| **symbols the broker lists AT ALL** | **166** | **76** |

For each of the 7 unique missing canonicals the probe resolved the broker name, called
`symbol_info`, then tried a name-alias list, then swept **every one of the broker's 76 symbols
for a substring match**. Result for all seven:

```
DASHUSD   cause=BROKER_DOES_NOT_LIST_IT  alias_hits=[]  substring_matches=[]
XAUEUR    cause=BROKER_DOES_NOT_LIST_IT  alias_hits=[]  substring_matches=[]
XAGEUR    cause=BROKER_DOES_NOT_LIST_IT  alias_hits=[]  substring_matches=[]
XAUAUD    cause=BROKER_DOES_NOT_LIST_IT  alias_hits=[]  substring_matches=[]
XAGAUD    cause=BROKER_DOES_NOT_LIST_IT  alias_hits=[]  substring_matches=[]
CORN_c    cause=BROKER_DOES_NOT_LIST_IT  alias_hits=[]  substring_matches=[]
COTTON_c  cause=BROKER_DOES_NOT_LIST_IT  alias_hits=[]  substring_matches=[]
```

**redacted_account's universe carries no metal cross, no softs and no DASH.** The profile is
*correct*; it declares what the broker offers. This cannot be repaired by config, by a
symbol-map alias, or by a watchdog. It is a property of the account. (This independently
confirms `phase19/.../T3_redacted_account_UNIVERSE_FINDING.md`, commit `f1c3b5a27`, which reached
the same 76-symbol conclusion by exhaustion on 2026-08-10.)

## 1.2 Which sleeve loses what

| sleeve | cluster | FTMO slots | FN slots | lost on FN |
|---|---|---:|---:|---|
| `crypto` | crypto | 2 | **1** | DASHUSD — **half its surface** |
| `energy_agri` | energy | 2 | 2 | — |
| `sub_xvol_pullback` | substrate | 18 | **12** | XAUEUR, XAGEUR, XAUAUD, XAGAUD, CORN_c, COTTON_c |
| `sub_mid_dn_revert` | substrate | 20 | **14** | the same six |

The live cycle log corroborates it exactly: redacted_account's own
`broker_profile_generation` block reports `profile_supported_symbol_slot_count: 29`,
`broker_unsupported_symbol_slot_count: 13`, and lists those 13 skips by
`(symbol, sleeve, cluster)` every cycle. FTMO's reports 42/42/0.

## 1.3 Restating redacted_account's economics over the book it can actually trade

**Method.** `live_book_integrity_receipts/restate_fn_universe.py` drives the published
machinery unmodified — `recost_w7_validation.build([])` for rows,
`mc_firm_rules.series` / `.mc` / `.rule_sets` / `._derived` for the grid — at the
**deployable** convention (`KELLY_HALF`, `RISK_LIVE_NOMINAL`, 2.0 % dial), which is the one
`BOOKS_MC_V1.json → cache_books.live_nominal_half_kelly` publishes and the live book
implements. The only change is a **row predicate on `sym`**, inserted at the single seam
where the symbol exists.

**Control, and an honest caveat.** `book_days` reproduces **exactly** (117 on both accounts,
the published value) — the convention-invariant control `verify_series` itself relies on, so
the trade set is the published one. `mean_r_per_book_day` does **not** reproduce
(FTMO 0.34623 → 0.38077, FN 0.37293 → 0.40802) and the reason is documented in
`mc_firm_rules.verify_series`: `BROKER_TRUE_COSTS_V1.json` gained coverage after Session Q
sealed its figures. So the `AS_PUBLISHED` row below is **the published book at today's cost
coverage**, not a byte reproduction of the 2026-07-30 artifact — and it is the correct
baseline here precisely because all four universes share one code path and one cost artifact.

### The published three-sleeve book, forward window, worst carry, P2 (both phases)

| universe | trades | book days | R/book-day | FTMO p_pass | FTMO %/mo | **FN p_pass** | **FN %/mo** |
|---|---:|---:|---:|---:|---:|---:|---:|
| **published artifact** (2026-07-30) | 356 | 117 | 0.373 | 0.9172 | 4.501 | **0.9331** | **4.848** |
| `AS_PUBLISHED` (today's costs) | 356 | 117 | 0.408 | 0.9341 | 4.950 | 0.9538 | 5.304 |
| `CURRENT_SURFACE` | 196 | 69 | 0.359 | 0.8864 | 2.528 | 0.9321 | 2.752 |
| **`FN_TRADEABLE`** | **142** | **47** | 0.403 | 0.9909 | 2.430 | **0.9897** | **2.365** |

### The four-sleeve book that is actually armed today

`src.safety.armed_set.declared_arming()` reports **both** accounts armed on
`crypto, energy_agri, sub_mid_dn_revert, sub_xvol_pullback` — so `FTMO_ARMED_TODAY_3` and
`redacted_account_RUNNABLE_3` are **stale on composition** as well as on universe.

| universe | trades | book days | FTMO p_pass | FTMO %/mo | **FN p_pass** | **FN %/mo** |
|---|---:|---:|---:|---:|---:|---:|
| `AS_PUBLISHED` | 754 | 173 | 0.9292 | 5.509 | 0.9509 | 5.928 |
| `CURRENT_SURFACE` | 391 | 105 | 0.9181 | 3.030 | 0.9553 | 3.274 |
| **`FN_TRADEABLE`** | **318** | **75** | 0.9807 | 2.344 | **0.9831** | **2.303** |

### The result is not "less safe" — it is **much slower**, and that is the surprise

Restricting to redacted_account's real universe moves `p_pass` **up** (0.9538 → 0.9897 on the
published book) while the monthly rate **halves** (5.304 → 2.365 %/mo) and the median
calendar time to target **more than doubles** (48 → 112 days). The mechanism is visible in
the series: dropping those symbols removes the tails at both ends — `sd_unit_r` 1.1826 →
0.9963, worst day −1.2452 → −0.8459 R — leaving a book with fewer, tamer days.

So the honest sentence for the owner is: **redacted_account is a smaller, calmer, slower book than
its published figures describe. It is more likely to pass eventually and takes roughly 2.3×
as long to get there.**

### Sample sizes and intervals, stated plainly

`se_p_pass` is **Monte-Carlo sampling error only** (≤ 0.0013 at 40,000 paths) and does not
carry the estimation error on the day series, which dominates. The honest sample statement is
the row count: the `FN_TRADEABLE` published-book cell rests on **142 trades over 47 book
days**, and the four-sleeve cell on **318 trades over 75 book days**. Two independent
priors on how much confidence that supports: 46.9 % of the survivor book's edge rests on 194
trades (Session N §8.2), and Lane F's power analysis shows the *live* record cannot
distinguish 4.501 %/mo from 0.100 %/mo for 2–6 months. Treat these as ordering, not precision.

## 1.4 There is a larger population defect underneath, affecting BOTH accounts

Census of the W7 cache — the population every published `p_pass` is computed on — against
each sleeve's **current** `on_surface`:

| sleeve | cache trades | on symbols NOT on the current surface | FN-unavailable |
|---|---:|---:|---:|
| `crypto` | 104 | **36 (34.6 %)** — ETHUSD | 37 (35.6 %) |
| `energy_agri` | 162 | **103 (63.6 %)** — CORN_c, COTTON_c, HEATOIL_c, NATGAS_cash | 78 (48.1 %) |
| `sub_xvol_pullback` | 90 | **21 (23.3 %)** — EURUSD, NAS100, USDCAD, USDCHF, N25_cash, SOYBEAN_c | 17 (18.9 %) |
| `sub_mid_dn_revert` | 398 | **203 (51.0 %)** — 28 symbols | 21 (5.3 %) |

**44.9 % of the published three-sleeve book, and 48.1 % of the armed four-sleeve book, is
trades on instruments NEITHER account's sleeves can generate today.** `energy_agri`'s
published economics are 63.6 % agricultural and refined-product trades against a live surface
of exactly `USOIL_cash` + `UKOIL_cash`. This is not a redacted_account problem; it is a
population-vs-surface problem, and the `CURRENT_SURFACE` rows above are the first restatement
of it for either account.

## 1.5 Should the accounts be expected to diverge? Yes — and the cause is the universe, not the costs

Comparing each account's own honest cell (four-sleeve book, forward, worst carry, P2):

| | FTMO `CURRENT_SURFACE` | redacted_account `FN_TRADEABLE` | divergence |
|---|---:|---:|---|
| %/month | 3.030 | 2.303 | **FN ≈ 24 % lower** |
| book days | 105 | 75 | **FN ≈ 29 % fewer** |
| p_pass (2-phase) | 0.9181 | 0.9831 | FN higher |

And the control that isolates the cause: run **FTMO's costs on FN's universe** and the
monthly rate is 2.344 vs redacted_account's 2.303 — a **1.7 %** difference. The whole of the
accounts' expected divergence is the **instrument universe**; the broker-cost difference is
a rounding error beside it.

**Practical consequence for the owner:** the two accounts must not be read as a controlled
A/B of the same book. Expect redacted_account to trade about **three-quarters as often** and earn
about **three-quarters as much per month** as FTMO, indefinitely, for structural reasons. A
redacted_account underperformance of that size is the *expected* outcome, not evidence of a defect.
(redacted_account also carries a live `size_cap_multiplier: 0.622928`,
`reason: derisking_into_maxdd_wall`, from its pre-arming −3.77 % — a further, separate,
37.7 % size reduction that no published figure prices.)

---

# TASK 2 — the cluster envelope

## 2.1 What the flag actually does, and what the code really is

`book_owner.py:269-276` reads `ultimate_book_one_unit_per_cluster_per_day` with an **inline
default of `True`**; the host config carried `false`. Lane H (`4eaa41f80`) is right that this
put the live book outside the envelope its 2.0 % dial was certified on.

The enforcement is `book_owner.py:2066`:

```python
if (self._cluster_cap_on and _cluster and _cluster not in self._cluster_cap_exempt
        and self._ledger.cluster_placed_today_other_bar(_cluster, _dday, dbar)):
```

`dbar` identifies **this** bar, so **same-bar members of one unit always place** — the cap can
only block a *later-bar* re-fire. That matters because `admission.size_correlated_units`
buckets by `(decision_day, cluster)` and splits `unit_risk / n` across members
(`admission.py:1171-1177`, `:1253`), i.e. same-bar diversification is already handled by
splitting one unit. Across bars there is no such memory: a later bar creates a **fresh full
unit**, which is 2× the certified envelope.

The armed book makes this sharp — `sub_xvol_pullback` and `sub_mid_dn_revert` are **both**
`substrate`, so **38 of 42 armed slots sit in one cluster**, all on H4 (6 bars/day).

## 2.2 The owner's 2026-06-16 relaxation was right then and does not describe this book

The config comment records the reason: the cap *"was blocking a 2nd same-cluster SYMBOL per
day (e.g. GER40 idxrev when JP225 idxrev already fired), which is stricter than the validated
model… The cap killed that diversifying trade."*

Measured on the armed four sleeves over the archive corpus (869 trades, 603 cluster-days):

| | count | share |
|---|---:|---:|
| `(cluster, day)` buckets | 603 | |
| buckets whose **first bar is multi-symbol** — the cap **never** blocks these | 56 | |
| buckets where the cap would bind | **146** | **24.2 %** |
| correlated units blocked | **168** | **21.8 %** |
| … blocked unit is a **repeat of a symbol the cluster already has on** | **150** | **89.3 %** |
| … blocked unit is a **genuinely new symbol** (the 06-16 case) | **18** | **10.7 %** |
| median gap first bar → blocked bar | **4.0 h** | one H4 bar |

So on today's armed book, **89.3 % of what the cap blocks is the same instrument re-firing
one bar later** — a second correlated unit, not diversification. Same-bar multi-symbol units
are untouched. And the note's own example, `idxrev`, is an **unarmed** sleeve
(`DEAD_BEFORE_COST`). The 2026-06-16 reasoning was sound for the book of that date and does
not transfer.

## 2.3 The price, and what it buys

Instrument: the correlated **unit** (mean member R × the unit's max member confidence),
day-summed, both regimes, `jpy` exempt as configured. Population: `R1_ESTATE_ROWS_V2`
(archive) — **a within-corpus A/B**, not comparable to any published `p_pass`.

**The price is real and it is not small:**

| | cap OFF | cap ON |
|---|---:|---:|
| R/day (all years, conf-weighted) | +0.2538 | **+0.1625 (−36.0 %)** |
| R/day (forward 2025+) | +0.8139 | **+0.4868 (−40.2 %)** |
| paired delta, unweighted mid band | | **−0.154 R/day, 95 % CI [−0.262, −0.056]** |

Sign is stable across all four cost bands (`r_new_low/mid/high`, `r_old`), both weightings,
and a ±2 h day-boundary shift (a clock-sensitivity control, because CJ established the sealed
labels were UTC + 2 h).

**What it buys, at the objective that actually governs a prop account:**

| window · account · risk | p_pass OFF → ON | Δ | p_fail_daily OFF → ON | p_fail_dd OFF → ON |
|---|---|---:|---|---|
| all-years · FTMO · 2.000 % | 0.6955 → **0.7859** | **+0.0904** | 0.0185 → **0.0000** | 0.2860 → 0.2141 |
| all-years · FTMO · 1.1968 % | 0.8830 → **0.9323** | +0.0493 | 0.0000 → 0.0000 | 0.1170 → 0.0677 |
| all-years · FN · 2.000 % | 0.7046 → **0.7902** | +0.0856 | 0.0150 → **0.0000** | 0.2803 → 0.2098 |
| all-years · FN · 1.1968 % | 0.8849 → **0.9315** | +0.0466 | 0.0000 → 0.0000 | 0.1151 → 0.0685 |
| fwd-2025+ · FTMO · 2.000 % | 0.8050 → **0.9121** | **+0.1071** | 0.0538 → **0.0000** | 0.1412 → 0.0879 |
| fwd-2025+ · FTMO · 1.1968 % | 0.9706 → **0.9873** | +0.0167 | 0.0000 → 0.0000 | 0.0294 → 0.0127 |
| fwd-2025+ · FN · 2.000 % | 0.8126 → **0.9114** | +0.0988 | 0.0479 → **0.0000** | 0.1395 → 0.0886 |
| fwd-2025+ · FN · 1.1968 % | 0.9692 → **0.9866** | +0.0174 | 0.0000 → 0.0000 | 0.0308 → 0.0135 |

**Twelve of twelve cells favour ON** (the four unweighted cells at 2.000/1.1968/0.500 % agree:
+0.0798 / +0.0669 / +0.0421). The mechanism is the worst day: **−2.550 R → −1.650 R**
conf-weighted, **−4.00 R → −2.00 R** unweighted. At the 2.0 % dial a −4 R day is −8 % of
equity — past the −5 % firm wall *and* past the −4 % flatten trigger. **`p_fail_daily` goes
to exactly 0.0000 in every cell where it was non-zero**, and that failure mode is account
death, not a drawdown you trade out of.

## 2.4 The recommendation, and why it is not the one the brief anticipated

The brief allowed for "if the measured impact is negligible… leave live config alone and
correct the certification record." **It is not negligible — it is materially decision-bearing,
in both directions**, and the two directions do not point the same way:

- on **expectancy** the cap costs 36 %, which is why the 2026-06-16 relaxation happened;
- on **p_pass** — the objective a challenge account is actually optimising — it gains
  +4.7 to +10.7 pp and removes the daily-breach mode entirely.

A prop challenge is a path constraint, not a rate maximisation. **Recommendation: turn it on.
Executed.**

Blast radius today is ~nil, which is the right condition for a ceremony: the live book has
taken **one trade in 12.5 days**, `cluster_unit_already_placed_today` has been emitted
**0 times** in the entire launcher log (the path was unreachable), and both accounts held
**0 open positions** throughout. The change is prospective insurance, not a P&L event.

---

# 3. The ceremony, as executed

All times UTC, 2026-08-11. Host `C:\Users\MSI\Documents\ai-trading-agent`, HEAD `bba5a38ae`.
No `git checkout / pull / clean / stash` was run in the live tree at any point.

| # | step | result |
|---|---|---|
| 0 | pre-state capture (read-only) | config `a2d5c675…`; tokens valid, digests `ffe16657feaf` / `e184a81d3b1b`, expiry 2026-09-09; both books healthy; kill flags absent; supervisor PID 7316 alive; 0 open positions |
| 1 | backup | `host-local\lbi_20260811\agent_config.yaml.before`, sha256 verified equal to live |
| 2 | edit, 10:39 | uniqueness asserted (`occurrences of the exact key line: 1`), **one hunk**, +1,088 B, `a2d5c675…` → `c3059d0a…` |
| 3 | re-mint both, 10:39:42 | FTMO → `0b0dbe307379…`, FN → `8540f9a9f302…`; **expiries preserved to within 1.5 s** |
| 4 | verify tokens | both `"valid": true, "reason": "activation_token_valid"` |
| 5 | restart, 10:40:06 | 4 workers stopped; **supervisor relaunched both within 36 s** with byte-identical command lines |
| 6 | digest match in the RUNNING processes | FTMO log: `config_digest=0b0dbe307379`; FN log: `config_digest=8540f9a9f302` — **equal to the tokens** |
| 7 | placement drill | see below |
| 8 | rollback shape | proven arithmetically |

## 3.1 The byte diff

```diff
@@ -1301,5 +1301,16 @@
   # slightly above the certified one-unit-per-cluster-per-day envelope -- accepted for trade frequency +
   # the validated diversification. Set back to true to re-impose the strict envelope.
-  ultimate_book_one_unit_per_cluster_per_day: false
+  # OWNER 2026-08-12 (live-book integrity swarm): RE-IMPOSED (true). [11 comment lines recording
+  #  the measurement, the 89.3 %-repeat finding, the price and what it buys]
+  ultimate_book_one_unit_per_cluster_per_day: true
   ultimate_book_cluster_cap_exempt_clusters: ["jpy"]
```

The historical 2026-06-16 note is left intact above it; the new note is added, not
substituted, so the record reads as a sequence of decisions.

## 3.2 The placement proof — through the engine's own gate, transmitting nothing

`live_book_integrity_receipts/post_ceremony_verify.py` calls
`activation_token.authorize_broker_mutation`, the pure decision function behind
`RealMT5.order_send`'s choke point. It classifies and answers allow/deny; it does not
transmit. Three probes per account:

| probe | FTMO | redacted_account |
|---|---|---|
| **exposure-INCREASING** (`TRADE_ACTION_DEAL`, `ORDER_TYPE_BUY`, no `position`) | **allowed** · `activation_token_valid` · `increasing` | **allowed** · `activation_token_valid` · `increasing` |
| risk-REDUCING control | allowed | allowed |
| **stale-digest negative control** (digest `0×64`) | **REFUSED** · `activation_token_config_digest_mismatch` | **REFUSED** · same |

The negative control is the one that matters: it demonstrates the digest binding is **live**,
i.e. that Lane F's exact failure mode — 462 refusals over two hours on redacted_account,
surfacing misleadingly as `order_rejected:timeout_no_fill` — is what *would* have happened
had the tokens not been re-minted, and does not happen now.

Also confirmed in the same pass, resolved through the exact expression
`book_owner.py:269-276` uses:

| | FTMO | redacted_account |
|---|---|---|
| `cluster_cap_on_resolved` | **True** | **True** |
| `apply_to_execution` / `live_activation_allowed` / `live_broker_authority` / `include_clean3` | True ×4 | True ×4 |
| broker `trade_allowed` / terminal connected | True / True | True / True |
| balance / equity | $108,342.47 | $96,229.28 |
| open positions | **0** | **0** |

## 3.3 Rollback — tested in shape, not merely written down

Restoring `agent_config.yaml.before` reproduces the pre-ceremony digests **exactly**:

```
operator_profile:  AFTER ROLLBACK would be ffe16657feaf…  == pre-ceremony digest  -> True
redacted_account:             AFTER ROLLBACK would be e184a81d3b1b…  == pre-ceremony digest  -> True
```

Verified arithmetically from the two file byte-hashes without performing the rollback. The
procedure is therefore: **copy the backup over `config/agent_config.yaml` → re-mint both
tokens (they will bind `ffe16657feaf…` / `e184a81d3b1b…`) → stop the four `run_book.py`
workers and let the supervisor relaunch.** Same five minutes, same order, no other step.

**No stop condition fired.** Both token re-mints verified; both books' placement paths
confirmed; the estate is not in a half-applied state.

---

# 4. Post-state health check

Captured 2026-08-11T10:44Z, after the restart:

| | FTMO | redacted_account |
|---|---|---|
| workers | 11056 / 10844, launched 10:40:37 | 11256 / 11232, launched 10:40:40 |
| command line | unchanged — 4 tags + spread floor + `--poll-seconds 60` | unchanged — same 4 tags, no frontier |
| heartbeat | fresh, `"healthy": true` | fresh, `"healthy": true` |
| `authority_gates_ON` | **True**, `halted=False killed=False` | **True**, `halted=False killed=False` |
| account identity | verified (6 fields) | verified (6 fields) |
| decision timeframes | `tfs=[16388]` (H4) | `tfs=[16388]` (H4) |
| spread-geometry floor | ON for both substrate sleeves | ON for both |
| kill flag | absent | absent |
| supervisor | PID 7316, heartbeat current | — |
| open positions | 0 | 0 |

The first post-ceremony **decision cycle** lands at the next H4 close, **13:00 UTC** — the
books poll every 60 s and only evaluate at bar boundaries, which is why the heartbeat (not a
`cycle` row) is the liveness proof immediately after a restart.

---

# 5. What this leaves open

1. **`redacted_account_RUNNABLE_3` and `FTMO_ARMED_TODAY_3` are stale twice over** — three sleeves
   against four armed, and a full universe against two restricted ones. §1.3's grid is the
   restatement; it has not been folded into `BOOKS_MC_V1.json`, which still publishes 0.9331.
2. **Neither account's published economics describe its own surface** (§1.4). The
   `CURRENT_SURFACE` rows are the honest baseline and the `AS_PUBLISHED` rows are not.
   `energy_agri` is the extreme case at 63.6 %.
3. **`sub_xvol_pullback` and `sub_mid_dn_revert` share the `substrate` cluster**, so 38 of 42
   armed slots are one correlated unit per day under the restored envelope. That is the
   intended behaviour, but it means the armed book's realised breadth is `crypto` + `energy`
   + one substrate unit — narrower than a four-sleeve book sounds. Worth the owner knowing
   before any composition decision.
4. **The −36 % expectancy price is real.** If the owner would rather have the frequency than
   the pass probability, the rollback in §3.3 is five minutes. The recommendation rests
   entirely on the claim that a challenge account optimises `p_pass`, not R/day.
5. **`confidence_for(sleeve)` with no registry argument returns 0.0 for both clean_3 sleeves.**
   The live path passes `effective_registry` and is unaffected — but a research caller that
   forgets it silently prices two armed sleeves at zero weight. Not a live defect; a sharp
   edge worth a default.
