# Activation dossier — the generation-side spread-geometry floor, for the armed four

Session AY (B1800–B1849). **Nothing here is armed by this session.** The orchestrator executes
the ceremony; the flag is default-off and every measurement below is reproducible from the
receipts named in §7.

---

## 0. Read this first, because it changes what the decision is about

**The spread-geometry floor is not a new rule. Both live books already refuse these trades**,
at the send layer, at the same limits, on every W7 placement:

| layer | file:line | limit |
|---|---|---|
| authoritative pre-trade gate | `broker_net_cost_engine.py:721-728`, `:772-776` | `selected_cell_pretrade_max_spread_r` = **0.10** (fx_jpy/fx_jpy_ny **0.35**), `…max_total_cost_r` = **0.15** (JPY **0.45**) |
| pre-send mirror (fail-OPEN, spread only) | `book_owner.py:4240-4280`, called at `:1876` | the same spread key |

Reached on every book placement because `execution_packets.build_book_trade_params` stamps
`gtos_vnext_production_execution_path: True` at **`:538`** — the exact predicate
`execution._is_vnext_production_execution_path:1902-1913` tests. A refusal returns `None` from
`open_trade` (`execution.py:3438-3444`). (`execution_packets.py:348` carries the same key but
is `native_policy_instrumentation`, the adopt-rehydration helper, **not** a placement path;
citing it was decoration that read as corroboration.)

**Three qualifications on "already enforced", all measured:**

1. **It is config-conditional, not a code invariant.** `is_vnext_broker_net_cost_required`
   (`broker_net_cost_engine.py:127-142`) needs `enabled` + `apply_to_execution` +
   `mode == production_replacement_vnext_moonshot`. If any flipped, `pretrade_cost_refusal_reasons`
   returns `[]` at `:709-710` while `_is_vnext_production_execution_path` still returns True —
   **the gate would vanish silently.** All three are true today in both live profiles and both
   VPS trees.
2. **The enforced predicate is `spread_r > max + tolerance`** (`:591-593`, tolerance 1e-6), not
   a strict `>`.
3. **At HEAD the refusal is delivered one branch earlier and the diagnostic is worse**: ExecMgr-V4
   blocks at `execution.py:3429-3437` with `exec_mgr_v4:missing_cost:pretrade_cost_model_status_passed`,
   so the specific `spread_r_exceeds_selected_cell_limit:…` string never reaches
   `_last_open_trade_block_reason`. The order still refuses; only the forensics are lost.

It fires. In the read-only 2026-07-25 VPS export's own launcher log: **136 legs refused with
`cost_screen_spread_r`**, 62 more on the authoritative gate, observed `spread_r` up to
**16.543** (`AY_LIVE_SCREEN_EVIDENCE_V1.json`).

**So the decision on the table is not "should the book refuse these trades" — it already does.
It is "should it refuse them EARLIER, at generation."** §1 is the reason that is worth
anything, and §2 is what it costs.

---

## 1. What arming the floor actually buys

### 1.1 The conviction-count contamination — the live-money half [MEASURED]

`book_engine._running_conviction_override:937-987` builds the day's distinct-firing-sleeve
count from **intents**, after `precount_intent_filter`'s five drop rules. The cost screen is
not one of them and cannot be: it needs a tick and runs later, in `book_owner` at `:1876`.
`admission.py:1210` then takes `na = max(na, override)` — **monotone upward**.

So a sleeve whose every leg the cost gate will refuse still raises the day's Kelly-lite
multiplier **for every sleeve that does place**. Under the live half-Kelly bins
`((1,1,0.748),(2,3,0.991),(4,99,1.241))`, with `kelly_lite` and `kelly_running_count` both
`true` live:

| | measured on the export |
|---|---:|
| account-days that counted a sleeve which never placed a leg | **16** |
| account-days where that moved the Kelly-lite multiplier | **3** |
| worst single day | `na 5 → 2`, multiplier **1.241 → 0.991** |
| **size inflation on every unit that day** | **+25.227 %** |

The half bins are selected by **`ultimate_book_kelly_conservative: true`**
(`agent_config.yaml:1304`). **+25.227 % is the na 3→4 crossing, not the worst the bins allow —
na 1→2 is +32.487 %**, and on the non-conservative bins the 3→4 crossing is +45.5 %. Also:
only **3 of the 16** contaminated days moved the multiplier at all, and **all nine sleeves ever
observed hitting the screen are outside the armed four** — the defect is reachable on the armed
set and its incidence *there* is unmeasured. The contamination also exists **within a single
cycle** even with `kelly_running_count` off (`admission.py:1164-1169`); the ledger is what makes
it persist all day.

This is the same defect class the **D3** repair closed on 2026-07-27 for the metals confluence
gate, and `_running_conviction_override`'s own docstring calls that class
**CORRECTNESS-CRITICAL**. The floor closes it for this filter by construction: an intent
refused at generation never reaches the count. Pinned by
`tests/ultimate_book/test_spread_geometry_floor.py::test_a_refused_intent_does_not_enter_the_days_firing_sleeve_union`.

**Note what this half does NOT depend on.** It is true whether or not the filter improves any
sleeve's expectancy, because it is about the OTHER sleeves' size.

### 1.2 The per-sleeve economics — measured at the ratified rule

`RECORDED` population, `B_balanced`, α = 0.10, family `B7_5_SEPARABILITY_MINE_V1` (V10),
band published alongside, 20-seed random null + inverse-cheapest control, protocol declared
before any outcome was read (`AY_SPREAD_GEOMETRY_PROTOCOL_V1.json`).

| armed sleeve | verdict | over limit | Δ R/day (low / mid / high) | p raw (ctl → floor) | random max | inverse |
|---|---|---:|---|---|---:|---:|
| `sub_mid_dn_revert` | **REPAIR** | 46.9 % | **+0.270 / +0.426 / +0.430** | 0.163 → **0.023** (mid) | +0.120 | **−0.060** |
| `sub_xvol_pullback` | **REPAIR** | 7.7 % | +0.170 / **+0.264** / +0.266 | 0.012 → **0.0020** (mid) | +0.208 | **−0.079** |
| `energy_agri` | NEUTRAL | 3.8 % | 0.000 / +0.212 / +0.265 | 0.206 → 0.138 | +0.175 | −0.00004 |
| `crypto` | NEUTRAL | 11.0 % | +0.063 / +0.066 / +0.189 | 0.134 → 0.121 | +0.194 | +0.032 |

**REPAIR** = at ≥ 2 of 3 real bands the floor's Δ is positive, beats **every one** of the 20
random-drop seeds, and the inverse-cheapest control is negative. All three clauses, because
each kills a different wrong explanation: sign, sampling noise, and "any drop would have done".

**Two properties of that rule the reader needs.** The controls are matched on the **drop count
before the population rule runs**, not on the scored sample — at `mid`, live `n` 208 against a
random mean of 173.9 and inverse 137, from identical 284-row pre-population kept-lists. A
uniform subsample is unbiased for the mean, so the mismatch *widens* the null and makes "beats
every random" harder; but "same sample size" is the natural reading of a matched control and it
is not what is matched. And `empirical_p_vs_random = 0.0476` is the **resolution floor** of a
20-seed null (1/21), identical on all three bands because the seeds are shared — read
`beats_every_random` as the statement.

Estate-wide: **3 REPAIR, 2 HARMFUL, 12 NEUTRAL, 7 NO-OP, 5 NOT_EVALUABLE.** It is a per-sleeve
repair, exactly as AW concluded — not an estate-wide rule.

---

## 2. What it costs, stated honestly

1. **It refuses trades an armed book takes today** — at generation instead of at send. For
   `sub_mid_dn_revert` that is **46.9 % of its archive trades**, which is not a trim, it is a
   different sleeve. The send gate already refuses them, so the *placed* population should be
   unchanged; what changes is the count, the sizing slot and the operator card. **That
   equivalence is an inference, not a measurement** — see §4.
2. **`sub_mid_dn_revert`'s fold calendar moves by about four years** when the floor is applied
   (`fold_calendar_identical: false`), because the filter removes its earliest trades and
   `build_fold_calendar` derives boundaries from the data's span. The pooled comparison is
   valid; **a fold-by-fold one is not**, so "5 of 5 folds positive vs 2 of 5" is not a claim
   this dossier makes. `sub_xvol_pullback` and `energy_agri` keep an identical calendar.
3. **Neither REPAIR admits.** Both still REJECT at the ratified family. `sub_xvol_pullback`'s
   raw p reaches **0.0020**, which would admit at a declared family of ≤ 50 — the estate's
   ratified `CANDIDATE_BOOK_V1` is **53** and this session's own bill is far larger. It misses
   at every defensible bill. **This is a fidelity repair, not an admission.**
4. **`sub_xvol_pullback`'s gain rests on 6 dropped trades of 85.** It beats all 20 random
   seeds, which is the strongest statement 20 seeds can make, and it is still six trades.
5. **ON, the floor adds one `RealMT5.get_tick` per candidate intent per tick** on the
   generation path (`book_engine.py`), a broker interaction that does not exist today. Zero
   when OFF.
6. **Naming a sleeve refuses more than "over the limit", by fail-closed design.** An
   unreadable, crossed or absent quote, a non-positive `stop_dist`, or any exception inside the
   floor all refuse that intent (`spread_geometry.py`, `book_engine._spread_geometry_refusal`).
   On a symbol whose quote cannot be read, an opted-in sleeve proposes nothing that tick. That
   is deliberate — it matches the authoritative gate's own
   `missing_current_quote_spread_or_sl_distance` — and it is a real behaviour change to accept,
   not a footnote. §4.1 is the stop condition that watches it.
7. **The fix is prospective within a decision day.** `RunningConvictionLedger` persists the
   day's union, so arming mid-day cannot un-count what is already counted — the same hazard
   `--tags` carries (B365), and the reason §3 says to restart at a day boundary.
5. **The floor reads the live tick spread; AY-1 measured a modelled era-banded spread.** Same
   ratio, two sources. The bands are published for exactly this reason and the sign is stable
   across all three.

---

## 3. The exact ceremony

**Flag** (no config byte moves; no activation token is disturbed; both `agent_config.yaml` and
`profiles/redacted_account.yaml` are untouched, which is why it is a launcher argument):

```
--spread-geometry-floor sub_mid_dn_revert
```

`scripts/run_book_supervisor.ps1:140` is where `--tags` is set; this goes beside it, per
account. A sleeve named without a limit **inherits the limit the send gate will apply to it**
(`selected_cell_pretrade_max_spread_r[_by_sleeve]`), so the two layers cannot drift apart. An
explicit form is available (`sub_mid_dn_revert:0.075`) and is **not recommended** — a
generation floor stricter than the send gate refuses trades the book would otherwise take, and
nothing in §1 supports that.

**Recommended scope, and the reasoning:**

| sleeve | recommend | why |
|---|---|---|
| `sub_mid_dn_revert` | **ARM** | the only armed sleeve where the floor is a REPAIR at ≥2 bands **and** materially engaged (46.9 % over limit), so §1.1's contamination and §1.2's economics point the same way |
| `sub_xvol_pullback` | **owner's call** | REPAIR, but it engages 6 trades of 85; the conviction benefit is real and the expectancy claim is thin |
| `energy_agri`, `crypto` | **do not arm** | NEUTRAL — inside the random envelope at every band. Arming them buys only §1.1, at the cost of a live-behaviour change with no economic support |

**Order of operations** (the estate's own hazard, B365): `--tags` bounds the conviction count
**prospectively only**, and `RunningConvictionLedger` persists a per-day union that
`na = max(na, override)` carries upward. So **restart at a decision-day boundary**, or delete
that namespace's `pipeline_state/ultimate_book/<ns>/firing_sleeves.json` first. Restarting
mid-day inherits the day's wider set and the floor's whole §1.1 benefit is deferred to
tomorrow.

**Verify after restart** — three reads, all in the launcher's own output:

1. `SPREAD-GEOMETRY FLOOR IS ON for sub_mid_dn_revert at spread_r <= 0.1000 (inherited from
   the send gate's own limit)` — a WARNING line at startup. **Absent ⇒ the flag did not take.**
2. `generation.spread_geometry_floor` in the cycle telemetry: `{evaluated, refused, sleeves}`.
   `evaluated == 0` on a day the sleeve fired means the floor is not seeing intents.
3. `generation_skips` rows with `reason` starting `spread_geometry_floor:`, each carrying its
   own `spread_r`, `spread_price`, `stop_dist` and `limit`.

---

## 4. Stop conditions

Stop and roll back if **any** of these is observed:

1. **`spread_geometry_floor_quote_unavailable` on more than ~5 % of evaluated legs over a
   week.** The floor fails CLOSED on an unreadable quote (matching the authoritative gate's
   `missing_current_quote_spread_or_sl_distance`). A persistent quote-read fault would
   therefore silently thin the sleeve. This is the flag's most likely failure mode and it is
   the reason the telemetry counts *evaluated* as well as *refused*.
2. **Any `spread_geometry_floor_error:` row.** An internal fault refuses the intent and names
   the exception. One is a bug report; a stream of them is a disarm.
3. **The refused-leg count does not roughly match the `cost_screen_spread_r` skips the same
   sleeve produced before the change.** §2.1's equivalence is an inference: the floor reads
   the tick at GENERATION and the screen reads it at SEND, seconds apart, and a systematic gap
   between the two counts means one of them is not measuring what this dossier assumes.
   **This is the single most useful thing to watch in week one.**
4. `sub_mid_dn_revert`'s realised R/day over the next 30 book-days falls below its
   pre-change trailing figure by more than its own random-control envelope (±0.12 R/day at
   mid). Thirty book-days is roughly a month at ~7 book-days/month, so this is a slow check,
   not a trigger.

## 5. Rollback

Remove the flag and restart. **There is no state to unwind** — the floor writes nothing, holds
nothing, and touches no position; it only declines to emit an intent. A position already open
is unaffected: the floor runs in `_generate_intents` and every exit path reads the trade
record. Rollback is therefore strictly safer than the arming, and the same decision-day
boundary advice applies for the same reason (the day's persisted union).

## 6. What this dossier does not claim

- It does not claim the floor makes any sleeve admissible. Nothing admits.
- It does not claim the *placed* population is unchanged. It should be, and §4.3 is how that
  gets measured rather than assumed.
- It does not recommend touching the send-layer limits. `selected_cell_pretrade_max_spread_r`
  lives in an R2-bound file whose bytes are hashed into both activation tokens; this session
  reads it and never writes it.
- It does not recommend a generator constant change. `AY_GENERATOR_STOP_SURVEY_V1.json`
  measures why: `metals_core` carries the estate's strongest ATR stop floor (`0.25*ATR`,
  `metals.py:81`) and still reaches `spread_r` **1.14**. **An ATR floor is not a spread floor.**

## 7. Receipts

| artifact | what |
|---|---|
| `phase13/receipts/AY_SPREAD_GEOMETRY_PROTOCOL_V1.json` | the declaration, `cells_sha256`, before any outcome |
| `phase13/receipts/AY_LIVE_SCREEN_EVIDENCE_V1.json` | the live gate measured on the VPS export + the conviction contamination |
| `phase13/receipts/AY_LIVE_CONTRACT_CENSUS_V1.json` | the estate against each sleeve's own live limit, four bands |
| `phase13/receipts/AY_SLEEVE_GATE_V1.json` | 27 arms × 4 bands, every verdict, every fold |
| `phase13/receipts/AY_SLEEVE_VERDICT_V1.json` | the REPAIR / NEUTRAL / HARMFUL table |
| `phase13/receipts/AY_GENERATOR_STOP_SURVEY_V1.json` | each sleeve's stop expression vs its measured spread geometry |
| `phase13/receipts/CANDIDATE_FAMILY_V10.json` | the ratchet step |
| `src/components/ultimate_book/spread_geometry.py` | the floor |
| `tests/ultimate_book/test_spread_geometry_floor.py` | 33 tests: default-inert, fail-closed, and §1.1 pinned |
