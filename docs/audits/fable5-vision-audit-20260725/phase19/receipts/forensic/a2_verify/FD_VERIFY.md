# Lane FD verification — Session FA-continuation Phase A2

**Verifier:** Fable A2 verification agent. **Date:** 2026-08-03.
**Sol worktree verified:** `/Users/borr/GTOSActive/worktrees/wave19-sol-defects-20260801`
(branch `phase19/sol-defects`, closing commit `a7d9260ed`, verified commit `951d0002c`, base `f8c05d0ac`).

**Boundary held:** February reads are **attribution-only under `owner_mandate_20260801`** — stated
here per the commission. No March data, no `packs/` for March, no live-forward (2026-07-29+)
outcomes, no lane arms, no replays, no test-suite run, no source file edited. All heavy inputs
streamed line-by-line; peak RSS 32.9 MB (main pass) / 37.1 MB (parity pass) — far under the 1.5 GB
ceiling. Writes confined to this `a2_verify/` directory.

**Method:** Sol receipts are the CLAIMS; the pools and full missed-opportunity ledgers are the
EVIDENCE. Every number below was recomputed from raw jsonl(.gz); Sol's `REPRODUCTION_AND_BIAS.json`
was read only to state claims and locate raw sources. The re-decode RULE was read from Sol's
committed builder (`analyze_decision_defects.py:219-258`) as the commission instructs, then
implemented independently in `fd_recompute.py`.

Raw inputs (sha256-verified, byte sizes matching Sol's source receipts — same evidence, my arithmetic):

| role | rows | sha256 (first 12) |
|---|---:|---|
| Feb compact pool `CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz` (wave18 copy; wave19 copy byte-identical) | 24,239 | `d89202c3b7a3` |
| Feb full ledger `CP_FEBRUARY_TRUE_UTC_S0R0_V1_MISSED_OPPORTUNITY_LEDGER.jsonl` | 129,165 | `db5a2ce8450a` |
| Jan compact pool `CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` | 27,658 | `ee920fb0e287` |
| Jan full ledger `CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl` | 153,425 | `9ac5b105c83c` |
| Feb arm receipt `CP_FEBRUARY_ARM_S0R0_V1.json` | — | `64343e7a9b3d` |

---

## FD1 — February cost_missing / flat-0.12 re-decode: **VERIFIED (exact)**

**Rule applied** (independent implementation): rows with `symbol ∈ {GER40, UKOIL_cash, USOIL_cash}`
and `|cost_r − 0.12| ≤ 1e-12`; `redecoded = spread_r + expected_slippage_r + swap_cost_r +
commission_r` (all four required); `delta = 0.12 − redecoded`; `corrected_net =
opportunity_net_proxy_r + delta` on scoreable rows; sign flip when `(net > 0) != (corrected > 0)`.

| quantity | claimed (Sol) | recomputed (ledger) | recomputed (pool, independent) |
|---|---:|---:|---:|
| physical flat-0.12 rows | 17,716 (13,196/2,532/1,988) | **identical** | 3,555 pool rows (pool = scoreable subset) |
| scoreable rows | 3,555 (1,635/1,203/717) | **identical** | **identical** |
| complete-component rows | = physical | 17,716/17,716 | 3,555/3,555 |
| recorded net sum | −872.58729156 | **−872.58729156** | **−872.58729156** |
| redecoded net sum | −1,051.176716241 | **−1,051.17671624** | **−1,051.17671624** |
| **delta after re-decode** | **−178.589424681** | **−178.58942468** | **−178.58942468** |
| **sign flips** | **67** (18/36/13) | **67** (18/36/13) | **67** (18/36/13) |
| redecoded mean cost (per physical row) | 0.333507473 / 0.067010369 / 0.077987289 | **identical** | (pool means differ by construction — scoreable-only denominators — 0.276/0.0718/0.0942; not a discrepancy) |
| physical recorded−redecoded | −2,599.753603163 (GER40 −2,817.444618024; oils +134.169745683 / +83.521269178) | **identical to the last digit** | — |

Zero scoreable rows sit on the sign boundary (`net == 0` or `corrected == 0`), so the flip count is
tolerance-robust. The two independent raw sources (full ledger vs compact pool) agree to the last
printed digit on every figure.

**FA Phase-1 anchor verified:** 5,876 Feb full-ledger rows carry a `cost_missing` miss_reason —
UKOIL_cash 2,532 / USOIL_cash 1,988 / GER40 1,356 — exactly as `FUNNEL_FEB.md:129-135` states, and
every scoreable row of those three symbols carries cost_r == exactly 0.12 (`cost_distinct == {0.12}`
per symbol in the pool). Note the tasking paraphrase merged two populations ("5,876 physical rows …
carrying constant cost_r=0.12"): 5,876 is the **miss_reason** count; the **flat-0.12** count is
17,716 physical / 3,555 scoreable. Both verify exactly; FA's original wording was precise.

**Arm-receipt binding verified** (`CP_FEBRUARY_ARM_S0R0_V1.json`, sha256 matches Sol's):
`commission_broker_true_gated` reports calls == applied == 129,231, unpriced == 0, and per-symbol
n == the flat-0.12 physical row counts **exactly** (13,196 / 2,532 / 1,988) with mean_r 0.0 — the
zero-commission premise of the re-decode is bound by the arm's own repair report.

**Scope completeness (my adversarial check, beyond the claim):** `cost_r == 0.12` occurs on **no
other symbol** in either window's full ledger, and January carries **zero** flat-0.12 and **zero**
cost_missing rows. Stronger than claimed: in February, **100 % of ALL physical rows** of the three
symbols carry the 0.12 fallback — whole symbols were unpriced, not just the scoreable subsets.

## FD2 — nine defect classes: registry **VERIFIED**; three classes verified in raw data

`DEFECT_REGISTER.json` enumerates **exactly 9 commissioned defects** (FD-01 flat-0.12 fallback;
FD-02 provenance/key-drift projection; FD-03 spread placeholder authority; FD-04 close_mark_source
overload; FD-05 binary-population ambiguity; FD-06 selector reject re-injection; FD-07 authority
failure plumbing; FD-08 unscoreable terminal / cost rebase / flat slippage; FD-09 EV & default
template authority) plus **1 ancillary** (FD-A1 memo key). The 21-path changed-file inventory
matches `git diff f8c05d0ac..a7d9260ed` exactly.

Three classes verified against raw data (commissioned examples):

1. **`pretrade_cost_packet_status` (FD-02): VERIFIED exact.** Jan full ledger: present AND non-null
   on **153,425/153,425**. Feb full ledger: present on **0/129,165**. (Pools: Jan 27,658/27,658
   non-null; the Feb pool carries the key on all 24,239 rows with null value — matching Sol's
   compact-scan split.) Same pass, same verdict class: `commission_r_repair_status` on 0/129,165;
   legacy blocker key `missed_package_replay_order_executable_final_blocker_class` on
   **129,165/129,165** with canonical `final_blocker_class` on **0** (ledger) and the inverse in the
   pool (24,239 canonical / 0 legacy). Full↔compact parity join at `candidate_id +
   decision_time_utc`: **24,239 common, 0 missing, 0 extra, 0 blocker-value mismatches, 0 duplicate
   keys on either side** — schema drift, not population drift, exactly as FD-02 concludes. (The FA
   Phase-1 join hazard does not bite on this subset: keys are unique without symbol/side extension.)
2. **BTCUSD `spread_r` 0.0001 (FD-03): VERIFIED at the claimed 1e-12 tolerance.** Pools:
   1,203/1,203 + 915/915 = **2,118/2,118**; ledgers: 8,388/8,388 + 4,669/4,669. Precision nuance
   worth keeping: the values are template-constant but **not bit-identical** — Jan ledger holds
   8,358 distinct floats inside a ~6.8e-13 band around 0.0001. That jitter pattern (a constant put
   through float arithmetic) independently corroborates "template, not measurement".
3. **UKOIL_cash 0.02580 / USOIL_cash 0.02700 constants (FD-03): VERIFIED.** 100 % of rows at
   template in both windows at both granularities (UKOIL 1,932 & 2,532 ledger, 790 & 1,203 pool;
   USOIL 1,595 & 1,988, 733 & 717); max deviation ≈ 5e-13. Contrast: GER40's real spread spans
   0.0197..1.55 with 12,195 distinct February values — the variation the placeholders lack.

**Ancillary FD-A1 verified without running the test suite** (standalone pure-function probe, one
subprocess per `PYTHONHASHSEED` 1..64, comparing `_exact_content_key({"a":1,"b":[2]})` against the
insertion-reversed mapping): the **base** function (extracted via `git show f8c05d0ac`) produces
unequal keys under **exactly** seeds **[22, 28, 29, 35, 50, 62]** — Sol's claimed failing-seed set,
reproduced independently — and the repaired HEAD function is equal under **all 64**.

## FD3 — default-off status: **VERIFIED as Sol claimed it, with one precision correction to the tasking paraphrase**

- **Economic semantic/authority repair** (the flat-0.12 healing + native re-gate,
  `repairs.py:277` `_apply_broker_true_commission_capture`): executes **only** inside patch ids
  **`commission_broker_true`** and **`commission_broker_true_gated`** (+ `commission_inert_control`),
  each constructed `accel.Patch(default_on=False)` (`repairs.py:525`; swap-horizon `:623`;
  cost-ceiling `:720`), registered by `register_repairs` (`repairs.py:832-834`), and reachable only
  through `runner.py --repairs` (default `None`, `runner.py:514-521`, consumed at `:579`) where
  `resolve_repairs(None) → []` = **the frozen economics** (`repairs.py:866-867`). **Default-off,
  verified in code.**
- **Deterministic memo key** (`cuts.py:253-264`, sort typed frozen mapping pairs by their
  protocol-5 pickle frame): the canonicalization itself is unconditional inside
  `_exact_content_key`, but **every patch that exercises it is default-off** —
  `selector/timewarp/probability_hash_content_memo_v2` (`default_on=False`, `cuts.py:702`) and
  `attribution_fields_content_memo_v2` (`default_on=False`, `cuts.py:820`) — and none is in
  `TRAIN_DEFAULT_PATCHES` (`cuts.py:1239-1249`); the one default-set memo patch
  (`ultimate_packet_hash_content_memo`) deliberately uses the non-exact key
  (`exact = patch_id != …`, `cuts.py:623`). Cache-key-only either way (a miss recomputes through
  the original function).
- **Precision correction — aimed at the tasking paraphrase, not at Sol:** the FD-02 **evidence
  projections** (`decision_semantics_projection`, `missed_pool_projection`,
  `cost_attribution_provenance`, `semantic_sidecar_projection`, `ledger_scalar_projection`) are
  **`default_on=True` + `sealed_compatible=False`** (`cuts.py:1042-1043`, `:1089`) and members of
  `TRAIN_DEFAULT_PATCHES` — i.e. **default-ON within the research train lane**, exactly as Sol's own
  register states ("default-on, evidence-only, explicitly sealed-incompatible"). They change
  evidence shape only. Reachability is bounded: `decision_semantics` is imported by nothing outside
  `train_engine/cuts.py`, `cd_pool.py` (receipt builder), and FD's census script; the changed `src/`
  files are train_engine-only; and my independent R2 check finds **none of FD's 4 changed code files
  among the contract's 45 bound paths**. So: "nothing FD landed changes any default economics, and
  the economic repairs are default-off" is TRUE; a blanket "everything FD landed is default-off"
  would be FALSE.

## New findings

1. **FD-A1 residual at HEAD (new defect, same class):** `_exact_content_key`'s set/frozenset branch
   (`cuts.py:315`) still returns `frozenset(items)`, so **equal set-valued payloads get unequal memo
   keys** under `PYTHONHASHSEED ∈ {8, 13, 14, 37, 41, 47, 59}` of 1..64 — measured with the same
   probe that reproduced the base failing seeds exactly (see `MEMO_KEY_PROBE.json`). Impact bounded:
   memo-key only (miss → recompute, correctness preserved; cost is cache misses and seed-flaky
   tests), and JSON-decoded payloads contain no sets — but any in-memory payload carrying a real
   set re-imports the defect FD-A1 closed for mappings.
2. **Whole-symbol February unpricing:** 100 % of ALL GER40/UKOIL_cash/USOIL_cash physical rows carry
   the 0.12 fallback (not only scoreable rows), and flat-0.12 touches no other symbol in either
   window; January has zero such rows. FD-01's three-symbol scope is the complete population.
3. **Spread placeholders are float-jittered constants** (thousands of distinct values inside a
   ≤ 7e-13 band) — an independent second corroboration of FD-03's "template, not measurement".
4. **The CP pool is an economically faithful projection:** pool-based and full-ledger-based FD1
   recomputes agree to the last printed digit on every figure.
5. **Tasking-paraphrase conflation** of the 5,876 (cost_missing miss_reason) and 17,716/3,555
   (flat-0.12 physical/scoreable) populations — both verified; keep FA's precise wording.

## Receipts in this directory

- `FD_VERIFY.json` — machine-readable verdict table (this document's numbers).
- `FD_RECOMPUTE_RAW.json` — the full main-pass recompute (both pools, both full ledgers, arm receipt).
- `FD02_PARITY_RAW.json` — blocker-key drift + full/compact parity join.
- `MEMO_KEY_PROBE.json` — 64-seed base-vs-HEAD probe, per-seed rows.
- `fd_recompute.py`, `fd02_parity_pass.py`, `memo_key_probe_child.py` — the exact helpers used.
