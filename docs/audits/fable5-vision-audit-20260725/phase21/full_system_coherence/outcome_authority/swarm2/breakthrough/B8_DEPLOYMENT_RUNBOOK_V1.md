# B8 PAIRED SHADOW — DEPLOYMENT RUNBOOK (VPS)

**NOT DEPLOYED. This document is the instruction, not a record of one.** B8 was built and
measured on the research laptop; nothing in this lane has contacted the VPS.

Target host: the **existing** forward-shadow clone at `host-local\gtos-shadow\`
(`FORWARD_SHADOW_DEPLOYED_20260811.md`, `FORWARD_SHADOW_RUNBOOK.md`). B8 rides in that clone as a
**second, independent scheduled task**. It does not modify, restart, or share state with the
funnel-shadow task.

---

## 0. HARD SAFETY LINES — READ BEFORE ANYTHING

1. **Separate clone, already established.** `host-local\gtos-shadow\repo`. **Never**
   the live book's tree. B8 adds no new clone.
2. **Zero mutation surface.** B8's emitter drives `GenerationPort`, which is handed a bar source,
   not a broker. There is no `order_send` anywhere in the package — proved statically and
   dynamically by `controls.control_read_only` (C6), which scans **every** module including the
   emitter.
3. **The three live gates are forced false in memory** by `emit_decisions.runtime_config`
   (`ultimate_book_live_broker_authority`, `..._live_activation_allowed`, `..._apply_to_execution`),
   *after* the config is merged, so a config that had them on cannot arm this process. Pinned by
   `test_emitter_config_forces_the_three_live_gates_off`.
4. **No config writes.** The runtime config is built in a dict. `config/agent_config.yaml` is
   R2-bound **and** its digest is bound by the live activation token — B8 never touches it, and
   the `include_clean3` research override is applied in memory exactly as
   `AQ_ESTATE_TRADES_V2.research_overrides` did.
5. **`--tags` is deliberately absent.** Everywhere else in this estate an empty `--tags` is a
   fail-open hazard (B359). Here running the whole 29-sleeve registry **is the instrument** — it is
   Lane 4 rung 1 — and it is safe for exactly one reason: there is no order surface behind it.
   **Do not copy this pattern into anything that can place.**
6. **Own namespace.** B8 writes only under `shadow_logs/b8_paired_shadow/` in the shadow clone.
   It never writes to `pipeline_state/*`, `shadow_logs/gtos_vnext*`, or the funnel lane's
   `shadow_logs/funnel_shadow/`.
7. **This lane cannot disarm or arm anything.** If you find yourself editing a launcher, a profile,
   or a token to make B8 work, stop — B8 is wrong, not the live book.

---

## 1. SPARSE-CHECKOUT SET

The funnel lane's working set (`FORWARD_SHADOW_RUNBOOK.md` §1b) plus **two** additions B8 needs.
Applied as no-cone patterns:

```powershell
git -C host-local\gtos-shadow\repo sparse-checkout add `
  src config tests `
  docs/audits/fable5-vision-audit-20260725/phase21/cost `
  docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority `
  docs/audits/fable5-vision-audit-20260725/phase11/receipts `
  docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts `
  research/operations/broker_truth_layer_2026_07_27 `
  research/operations/spread_model_2026_07_29
```

| addition | why B8 needs it | what happens without it |
|---|---|---|
| `phase11/receipts/` | `AQ_ESTATE_TRADES_V2.json.gz` — the sealed decision store the forward stream is merged **into**, and C1's control input | **C1 and C2 cannot run.** The harness would start from an empty history, every sequential monitor would restart at information fraction 0, and no forward result would be comparable with any published estate number |
| `phase20/forward/receipts/` | `R1_ESTATE_ROWS_V2.json.gz` — C3's input | **C3 cannot run**; the statistics layer would be unverified on the host |

**LFS.** `AQ_ESTATE_TRADES_V2.json.gz` and `R1_ESTATE_ROWS_V2.json.gz` may arrive as 131-byte
pointers. Run `git lfs checkout <path>` (object store is local, no network) and confirm the byte
size before the preflight — an un-hydrated pointer parses as a JSON error, not as a missing file,
which is a slower failure to read.

---

## 2. PREFLIGHT — IT REFUSES TO START RATHER THAN MEASURING NOTHING

This is the whole lesson of `FORWARD_SHADOW_DEPLOYED_20260811.md`. Deploy 2 had a healthy feed, a
green log, and **88 candidates refused every cycle, forever**, because `BROKER_TRUE_COSTS_V1.json`
was absent and the commission path returned `None` by contract. B8's preflight converts that class
of failure into a startup refusal that **names the path**.

```powershell
cd host-local\gtos-shadow\repo
$env:PYTHONPATH = "$PWD;$PWD\docs\audits\fable5-vision-audit-20260725\phase21\full_system_coherence\outcome_authority\swarm2\breakthrough"

# (a) unit + adversarial pins — 28 tests, ~2 s, no data required
host-local\gtos-shadow\venv\Scripts\python -m pytest `
  docs\audits\fable5-vision-audit-20260725\phase21\full_system_coherence\outcome_authority\swarm2\breakthrough\b8_paired_shadow\test_b8_paired_shadow.py -q

# (b) artifact + cost-seam preflight — REFUSES on a missing path and names it
host-local\gtos-shadow\venv\Scripts\python -c `
  "from b8_paired_shadow.live_shadow import preflight; import json; print(json.dumps(preflight(strict=True), indent=1))"

# (c) the reproduction controls — C1-C7 must ALL pass before any number is read
host-local\gtos-shadow\venv\Scripts\python -m b8_paired_shadow.run_harness --controls
```

**Acceptance for (c), and it is not negotiable:**

| control | must read |
|---|---|
| C1 | `mismatches: 0`, `max_abs_error: 0.0` |
| C2 | `unaccounted: 0`; `lane8_named_controls` all `match: true` (crypto 181, energy_agri 67, sub_xvol_pullback 88) |
| C3 | all five checks `match: true` |
| C4 | `verdict: INERT`, `p_value_reported: null` |
| C6 | `static_mutation_call_sites_in_package: []`, `order_send_raised: true` |
| C7 | `sign_agrees: true` |

**If C1 fails on the host and passed on the laptop, the host's bar archive is not the estate's.**
That is the correct conclusion and it is a data problem, not a harness problem. Do not proceed.

> **Expect a small, benign C1/C3 divergence on Windows and do not chase it.** The funnel lane
> measured platform solver drift of 2.8e-3 (7.9e-4 with BLAS thread pinning) on this host
> (`SOLVER_PLATFORM_DRIFT_RECEIPT_V1.json`). B8 fits nothing and solves nothing — its labeller is
> pure arithmetic over bars — so **C1 should still be exactly 0.0**. C3 reads a stored artifact and
> should also match. If either drifts, that is a real difference, not the known one.

---

## 3. THE TWO PROCESSES

B8 is deliberately split so the slow part cannot delay the fast part and a failure in either is
visible on its own.

### 3.1 The emitter — the read-only 29-sleeve shadow book

Runs the full include-flag registry at bar closes and appends decisions. Idempotent: a restart
re-reads what it wrote and appends nothing (`_key` normalises the timeframe on both sides;
`test_emitter_dedupe_key_is_type_stable_across_a_restart` pins it). **Double-counted decisions
would inflate the sequential monitor's information fraction, which is the entire basis of its alpha
spending — a restart would buy an unearned early stop.**

```powershell
# host-local\gtos-shadow\run_b8_emit.ps1
$env:PYTHONPATH = "host-local\gtos-shadow\repo;host-local\gtos-shadow\repo\docs\audits\fable5-vision-audit-20260725\phase21\full_system_coherence\outcome_authority\swarm2\breakthrough"
$env:OMP_NUM_THREADS = "1"; $env:OPENBLAS_NUM_THREADS = "1"; $env:MKL_NUM_THREADS = "1"
cd host-local\gtos-shadow\repo
$today = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
$from  = (Get-Date).ToUniversalTime().AddDays(-3).ToString("yyyy-MM-dd")
host-local\gtos-shadow\venv\Scripts\python -m b8_paired_shadow.emit_decisions `
  --out shadow_logs\b8_paired_shadow\decisions.jsonl `
  --start $from --end $today --timeframes H4,D1,M15
```

A **3-day overlap window on every run** is intentional: the emitter is idempotent, so the overlap
costs only CPU and closes the gap a missed run would otherwise leave permanently. Schedule daily,
after the D1 close:

```powershell
schtasks /Create /TN "GTOS_B8_EMIT" /SC DAILY /ST 23:30 /RL LIMITED /IT `
  /TR "powershell -NoExit -ExecutionPolicy Bypass -File host-local\gtos-shadow\run_b8_emit.ps1"
```

**Cost.** H4-only over 20 days is ~28 s and ~115 cycles on the laptop; adding M15 multiplies cycles
by 16. Start H4+D1; add M15 only once the H4 questions are accumulating and you have measured the
host's cycle time.

### 3.2 The harness — controls, questions, receipts

```powershell
# host-local\gtos-shadow\run_b8_harness.ps1  (same PYTHONPATH + BLAS pinning block)
host-local\gtos-shadow\venv\Scripts\python -m b8_paired_shadow.run_harness `
  --out docs\audits\fable5-vision-audit-20260725\phase21\full_system_coherence\outcome_authority\swarm2\breakthrough\b8_paired_shadow\receipts
```

```powershell
schtasks /Create /TN "GTOS_B8_HARNESS" /SC DAILY /ST 23:50 /RL LIMITED /IT `
  /TR "powershell -NoExit -ExecutionPolicy Bypass -File host-local\gtos-shadow\run_b8_harness.ps1"
```

`run_harness` exits **2** when any control fails and still runs the questions so the failure can be
diagnosed — **but no number it prints is publishable until C1–C7 are green.** The banner says so.

### 3.3 Wiring the forward stream in (the one edit to make)

The harness currently loads sealed history only. To make the forward decisions count, the
`Substrate.load()` call in `run_harness.main` becomes:

```python
from b8_paired_shadow.live_shadow import intents_from_shadow_log, merge_forward

sub = Substrate.load()
fwd, drops = intents_from_shadow_log(Path("shadow_logs/b8_paired_shadow/decisions.jsonl"))
sub.intents = merge_forward(sub.intents, fwd)
```

`merge_forward` refuses duplicates on the pairing key. **Record `len(fwd)` and `drops` in the run's
receipt**: a sequential monitor that crosses its boundary on forward data is a different claim from
one that crosses on history, and the receipt must let a reader tell them apart.

---

## 4. THE DAILY READ

```powershell
host-local\gtos-shadow\venv\Scripts\python -c `
  "from pathlib import Path; from b8_paired_shadow.live_shadow import daily_read_summary; print(daily_read_summary(Path(r'...\b8_paired_shadow\receipts\B8_QUESTIONS_V1.json')))"
```

One screen, one line per question:

```
  Q7_ex_ante_cost_gate_0.2   n= 10180 mean=+0.0987 CI[+0.0817,+0.1151] disc=25.5% t=0.29 STOP_EFFECT_VS_ZERO -> PASS
```

**Read it in this order:**

1. **`disc`** — below 5 % the contrast is `NEAR_INERT` and rests on a handful of outcome flips,
   whatever `n` says. Do not act on it.
2. **`CI`** — the day-block interval. The i.i.d. one is in the receipt and is narrower; it is not
   the one to read.
3. **`t=`** — the information fraction, not a t-statistic. It is how far through its declared
   horizon the question is.
4. **the sequential decision** — `STOP_EFFECT_VS_ZERO` means the effect is real. It does **not**
   mean the effect clears the question's bar.
5. **`-> VERDICT`** — that is the pass-bar answer, and it is the one that changes a decision.

**Weekly, additionally:** open `B8_CAUSALITY_LEDGER_V1.json` and check
`arms_with_same_day_aggregates` is still `[]`. If a new arm appears there, its temporal companions
are mandatory before its number is quoted anywhere.

**Health, not results.** The emitter appending 0 rows for a week with markets open is a fault, not a
quiet market: the H4 estate emits ~1 decision/day. Check `shadow_logs\b8_paired_shadow\decisions.jsonl`
line count before concluding anything from an unmoving question.

---

## 5. WHAT TO DO WHEN A QUESTION ANSWERS

A `PASS` is **not** an instruction to change the live book. The sequence:

1. **Stop the question.** Its arms stay in the multiplicity ledger forever; the ledger is
   append-only and the family never shrinks.
2. **Check the causality companions** — lag retention and the within-day split — before quoting it.
3. **Take it to the estate's admission standard**, not this harness's pass bar: `CANDIDATE_BOOK_V1`,
   all-declared basis, sealed α = 0.10 (`phase8/receipts/CANDIDATE_FAMILY_V1.json → ratified_rule`).
   The harness's BH ledger gives the q-value; the ratified rule decides admission.
4. **If it touches an armed sleeve, it is an owner decision.** `--frontier-exits`,
   `--spread-geometry-floor` and `--entry-hour` are launcher flags that change which trades an armed
   book proposes. They need no config byte and no token re-mint — which makes them *easy*, not
   *safe*. Borhen's call, with the receipt.
5. **Never re-pose the same question after seeing the answer.** That is a second look and the ledger
   will count it.

---

## 6. STOPPING

`schtasks /End /TN GTOS_B8_EMIT` and `schtasks /End /TN GTOS_B8_HARNESS`. **There is never anything
to flatten** — B8 holds no position, has no token, and cannot reach a broker. Deleting
`shadow_logs\b8_paired_shadow\` loses accumulated forward decisions and nothing else; the emitter
will re-derive any window still covered by the host's bar archive.

---

## 7. KNOWN FAILURE MODES, IN THE ORDER THEY HAVE ACTUALLY HAPPENED

| symptom | cause | fix |
|---|---|---|
| preflight raises naming `spread_model_2026_07_29` | sparse set missing | §1 |
| preflight's `cost_seam_probe.ok: false` with the file present | the model loads and cannot price — **deploy 2's exact failure mode**, healthy feed, green log, zero measurement | check the era table `BAR_SPREAD_ERAS.json.gz` hydrated |
| C1 fails with a JSON parse error | `AQ_ESTATE_TRADES_V2.json.gz` is an un-hydrated LFS pointer | `git lfs checkout` |
| every question reports `n=0` | every decision dropped as `ArmUnavailable` — almost always the spread seam, since a cost band is charged on every arm | read `drops` in the receipt; it names the reason per arm |
| emitter appends 0 rows on a market day | bar source stale, or the window is shorter than one H4 close | check `cycles` in the emitter's stats block |
| a question's `n` jumps on a restart | the dedupe key broke | `test_emitter_dedupe_key_is_type_stable_across_a_restart` should have caught it — treat as a harness defect, not a data event |
| `git pull` fails with `could not read Username` | host-admin session is Administrator; the clone's credential belongs to `trader` | use task `GTOS_SHADOW_UPDATE` (run-as `trader`), per `FORWARD_SHADOW_DEPLOYED_20260811.md` |

---

## 8. WHAT THIS DEPLOYMENT DOES NOT DO

- It does **not** touch the funnel-shadow lane, its task, its namespace, or its model.
- It does **not** measure fill fidelity. Every outcome here is a **modelled** replay over bars.
  Lane 4 §7.1 names shadow-to-live fill fidelity as the gate on this whole recommendation, and
  Lane H records **6 of 16 symbols lacking reconciled price-domain slippage samples** (AUDJPY,
  CHFJPY, EURJPY, UKOIL.cash, USOIL.cash, XAGUSD). **Until that reconciliation exists, a B8 answer
  is an answer about a simulator**, and the honest framing of any result is "the contract measures
  X on the estate's own labeller", never "the book would have earned X".
- It does **not** produce economic levels. Only treatment differences, spread-only, with the
  residual-cost caveat in `B8_PAIRED_SHADOW_HARNESS_V1.md` §8.
