# p4 — CORRECT THE RECORD

**Lane:** p4 (wave 20 forward). **Nothing sampled, nothing deleted.** Every number below was
produced by execution against primary evidence in this repository; every superseded claim is
annotated at source and left intact (CLAUDE.md §10). No live-forward P&L was read, no broker-mutating
script was run, the VPS was not touched.

Register: `SUPERSEDED_CLAIMS_V1.json` (this directory) — machine-readable, and enforced by
`tests/research_infra/test_superseded_claims_register.py` so no annotation can silently rot.

---

## 0. HEADLINE

**The committed launcher armed a sleeve the owner had disarmed, and had done so for two days.**
`scripts/run_book_supervisor.ps1:86` still passed
`mx_btcusd_d1_donchian_20_breakout` in FTMO's `--tags` *and* `--frontier-exits`, against an owner
instruction executed on the host on 2026-08-05 (D-2 CLOSED, host commit `2fa77722d`). A book
restarted from the committed launcher would have re-armed it. **Repaired, and the class made
unrepeatable**: `config/live_armed_set.json` + `src/safety/armed_set.py` +
`tests/safety/test_armed_set_single_source.py`, of which **four tests fail against the pre-repair
launcher** — proved by physically reverting it, not by reading it.

Three further corrections, each measured:

| | |
|---|---|
| **A** | The wave's own armed set was wrong at both ends in **four** artifacts. Corrected, and r1's estate analysis re-run: `sub_mid_dn_revert`'s day-block **p goes 0.0410 → 0.0858 net** and its gross R/day **+0.6472 → +0.2614** — the fold and p-value that never existed. |
| **B** | STAGE13's founding numbers struck at source in **five** artifacts + the live allowlist. New measurement: **4 of the 7 activated families were NEGATIVE in their own activating evidence** (42.5 % of rows), the headline is a 68.7 % in-sample selection worth **+0.119273 R/trade**, and one GEOMETRY_WRONG family carries **70.9 %** of the case. |
| **C** | The cited sizing audit **has never existed on any of 9,004 commits**. The weights survive; the derivation does not, and is **not** reconstructible (Spearman −0.1111). But the risk framing was wrong: the armed set's intersection with the candidate book is **empty** — these weights size nothing live today. |

---

## 1. A — WHAT IS ARMED, ESTABLISHED FROM PRIMARY EVIDENCE

### 1.1 The armed set

Established from the owner-decision record and the host ceremony receipt, not from any summary:

```
FTMO        crypto, energy_agri, sub_mid_dn_revert, sub_xvol_pullback
redacted_account  crypto, energy_agri, sub_mid_dn_revert, sub_xvol_pullback
```

`mx_btcusd_d1_donchian_20_breakout` was disarmed on FTMO on 2026-08-05 by owner instruction
(verbatim *"disable the mx_btcusd"*). Primary evidence, read directly:
`git show edb240459:.../phase19/receipts/vps_live_ops_20260805/MX_DISABLE_RECEIPT.md` on branch
`ops/vps-live-mx-disable-20260805` — host file sha256 `63079cec…` → `ff9299bd…`, occurrences of the
tag in the host launcher **2 → 0**, live process command line re-read from `Win32_Process` after
restart showing four tags and no `--frontier-exits`, `config_digest=ffe16657feaf` unchanged.

### 1.2 The committed launcher was never updated — and it is not the host's file either

| | committed | host (2026-08-05 ceremony) |
|---|---:|---:|
| bytes | **7,828** (blob `357d01a26601`) | 19,575 before → **19,495** after |
| `$books` array at line | 86 | **140** |
| spread-floor key | `spreadFloor` | **`floor`** |
| `mx_btcusd…` occurrences | **1 (tags) + 1 (frontier)** | 0 |

That blob is **identical on all 40 local branches, including `main`** — measured by resolving
`scripts/run_book_supervisor.ps1` at every branch tip. So this was not a stale side branch: the
mainline launcher armed a disarmed sleeve.

**And the two files have diverged structurally.** The host's is ~2.5× the size with a different key
name. **The committed launcher must never be carried wholesale** — carry individual argument
changes. That warning is now written into the file itself.

### 1.3 The repair, and the proof that it is a repair

`scripts/run_book_supervisor.ps1` FTMO row: `mx_btcusd_d1_donchian_20_breakout` removed from `tags`,
`frontier` set to `$null` (the shape the FN row has always used; `:114` builds the argument only
`if ($b.frontier)`). redacted_account row byte-identical.

**A/B by execution, not by reading.** The launcher was physically reverted with `git stash`, the
suite re-run, and restored:

| | result |
|---|---|
| pre-repair launcher | **4 FAILED** — `test_launcher_and_declaration_agree`, `test_assert_consistent_…`, `test_no_owner_disarmed_sleeve_is_armed_by_the_committed_launcher`, `test_armed_sleeves_matches_what_the_committed_launcher_actually_arms`; message names the drift exactly (*"launcher arms undeclared ['mx_btcusd_d1_donchian_20_breakout']"*) |
| post-repair | **46 passed** across the three touched test files |
| restore | sha256 `2301200d…` **byte-identical** to the pre-revert snapshot |

### 1.4 The single source of truth

The failure had no cure because there was nowhere to look the answer up. Now there is:

* **`config/live_armed_set.json`** — the declaration. Per-account armed sleeves, frontier exits and
  spread-geometry floor, plus a `decision_log` in which **every row carries an authority and a
  receipt** (enforced by a test), and a stamped record of the committed-vs-host divergence.
* **`src/safety/armed_set.py`** — `armed_sleeves()` is what every artifact should call instead of
  writing a tuple down. `reconcile()` compares the declaration against the launcher and returns
  typed disagreements.
* **`tests/safety/test_armed_set_single_source.py`** — 13 tests.

Two safety properties are **modelled**, not commented:

1. **`--tags ""` is fail-open.** `run_book.py:383` reads `tuple(...) if args.tags else None`, so an
   empty string runs every BUILT sleeve. The parser returns `tags=None` (`is_fail_open`), never an
   empty tuple, so no caller can read the most dangerous configuration there is as "nothing armed".
   `reconcile()` reports it as `launcher_tags_fail_open`.
2. **A `--frontier-exits` naming a sleeve outside that worker's `--tags`** is reported
   (`frontier_exit_for_unarmed_sleeve`) — the exact shape the FTMO row had.

**Neither new file costs anything operationally**, and this is verified against the implementations
rather than asserted: `activation_token.config_digest_for` (`activation_token.py:1089-1116`) hashes
`config/agent_config.yaml` plus the active profile **file bytes** only, and `config_file_hashes`
(`replay_acceleration_attempt5_typed_sparse_runner.py:1502-1511`) is an explicit two-entry dict, not
a glob over `config/`. **No token re-mint is owed for `config/live_armed_set.json`.**

### 1.5 The four artifacts, corrected — and r1 re-run

| artifact | was | now |
|---|---|---|
| `receipts/r1/r1_estate_rewalk.py:75-81` | 4-tuple, wrong both ends | derives from `armed_set.armed_sleeves()` |
| `receipts/r2/R2_RESULT_V1.json → live_isolation` | same 4 | corrected + supersession record |
| `tests/test_broad_origin_emission_repairs.py:424` | 5-tuple (launcher's, one step behind the host) | derives from the SoT |
| `scripts/run_book_supervisor.ps1:86` | armed a disarmed sleeve | repaired |

One inference had to be withdrawn during this work: the first draft of the `R2_RESULT_V1.json`
annotation claimed the isolation proof was unaffected because the old set was "a superset plus one
extra". **It was not a superset** — it omitted `sub_mid_dn_revert` entirely, so one armed sleeve was
never covered by the published disjointness proof. The annotation now says so.

**r1's estate analysis re-run at the corrected set** —
`receipts/p4_rerun_r1_corrected_set.py`, which imports r1's own scripts unmodified (same bars, same
walker, same spread model, same controls) and only redirects outputs and widens the cell list:

* `R1_ESTATE_DELTA_V2.json` / `R1_ESTATE_ROWS_V2.json.gz`
* `R1_ADMISSION_STAT_V2.json` — **with `sub_mid_dn_revert @ as_walked` added**, the cell r1's V1 omitted

Day-block bootstrap, mid band, 20,000 draws, published walk → corrected walk:

| cell | n | days | GROSS R/day | p | NET R/day | p |
|---|---:|---:|---|---:|---|---:|
| **`sub_mid_dn_revert` @ as_walked** *(ARMED, and absent from V1)* | 533 | 394 | **+0.6472 → +0.2614** | 0.0000 → **0.0146** | **+0.2296 → +0.1696** | 0.0410 → **0.0858** |
| `crypto` @ as_walked *(ARMED)* | 181 | 131 | +0.7839 → +0.5995 | 0.0006 → 0.0057 | +0.5227 → +0.4186 | 0.0162 → 0.0345 |
| `energy_agri` @ as_walked *(ARMED)* | 67 | 39 | +1.3386 → +1.3374 | 0.0337 → 0.0340 | +1.1711 → +1.2079 | 0.0572 → 0.0526 |
| `sub_xvol_pullback` @ as_walked *(ARMED)* | 88 | 40 | +2.7907 → +2.7888 | 0.0001 | +2.5955 → +2.6635 | 0.0003 → 0.0002 |

**The omitted sleeve is the one the correction moves.** Its net day-block p more than doubles,
0.0410 → 0.0858, ending just inside a sealed α = 0.10 — and it was the only armed sleeve with no
p-value at the corrected walk anywhere in the wave. This is not a gate verdict (see r1's own note on
scope); it is the statistic the gate binds on.

---

## 2. B — THE STAGE13 FOUNDING NUMBERS, STRUCK AT SOURCE

Commit `69d000fb3` (2026-05-27) activated seven broad origin families and three POI frameworks
**one day** after they were born. Its evidence is
`research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/`.

**Annotated at source in five artifacts** with an additive top-level `_RETRACTED_2026_08_07` key —
**95 inserted lines, 0 deleted**, and every original document verified **identical** after removing
the annotation (parsed both sides, compared). Plus a sidecar `STAGE13_RETRACTION_2026-08-07.md` in
that directory and a comment on the live allowlist at `config/agent_config.yaml:1174-1181`.

### 2.1 Three things measured here for the first time

**(1) Four of the seven activated families were NEGATIVE in their own activating artifact.**

| family | expectancy_r | rows |
|---|---:|---:|
| `structural_distance_extreme` | **+1.196255** (win rate **0.8373**) | 53,415 |
| `cross_asset_lead_lag` | +0.324116 | 22,947 |
| `liquidity_sweep_reclaim` | +0.201752 | 100,326 |
| `displacement_continuation` | **−0.001394** | 93,918 |
| `regime_transition_break` | **−0.025308** | 5,537 |
| `session_open_range_break` | **−0.036532** | 17,666 |
| `volatility_compression_expansion` | **−0.037773** | 14,357 |

**130,354 of 307,042 rows — 42.5 % — sat in families the activating evidence itself scored
negative. All seven were switched on.**

**(2) The headline is the selection.** `+0.41278` is over **217,485 of 316,489** family rows
(68.7 %), retained by an in-sample positive-EV cell filter: `min_group_rows: 20`, one exit policy for
all 1,302 kept cells, no out-of-sample split, no multiplicity adjustment, and **zero** kept cells with
`expectancy_r <= 0` — positive by construction. Row-weighted over exactly the seven activated
families the same artifact gives **+0.293508**. **Selection premium +0.119273 R/trade, entirely
in-sample.**

**(3) One family is 70.9 % of the case.** `structural_distance_extreme` contributes **63,898 of
90,119** total R. The family the forensic judges GEOMETRY_WRONG — *"resolves at the median in
5 minutes; its 21-cell price grid is negative in 20 of 21"* — is more than two-thirds of the evidence
that turned on the other six.

### 2.2 What supersedes them

`−0.29226 R/trade`, the same machinery, out of sample (`phase19/SLEEVES_OR_USAGE_VERDICT.md` row R1).
**A 0.70504 gap and a sign flip.**

### 2.3 Scope, stated so it is not read as bigger than it is

`live_activation_allowed` is **false** for Selector V4 and Scheduler V4, so their permission gates
never fire (`permissions.py:930` returns `None` for every candidate). **No armed money is sized by
this allowlist.** The allowlist itself is left exactly as it stands: changing it is a strategy
decision and is Borhen's.

**One consequence to state plainly.** `config/agent_config.yaml` is one of R2's 43 bound paths, so
this comment breaks the execution seal via `config_file_hashes` → `shared_execution_contract_digest_sha256`.
That seal is **already broken forward** by CN's authorized `broker_net_cost_engine.py` edit — H1
drift reads **3 entries before and after this lane** (1 pre-existing + 2 unhydrated LFS pointers,
which are not drift) — so it costs **no new option**. See §5 for the carry warning.

---

## 3. C — THE PHANTOM SIZING PROVENANCE

Every confidence weight in the nine-sleeve candidate book cites
`research/operations/final_moonshot_principal_full_system_audit_2026_06_17/CORRECTED_UNIFIED_BOOK_MC_AUDIT.json`
(`candidate_registry.py:157`, `test_candidate_book_consistency.py:86`,
`research_current_state.md:1042`, and `UNIFIED_BOOK_MC_RESULT.json → source_audit.mc`).

**Measured over all 9,004 commits reachable from every ref:**
`git log --all --diff-filter=A --name-only` records **zero** additions of that file, **zero** of its
sibling `CORRECTED_CANDIDATE_DAILY_SERIES_AUDIT.json`, and **zero of any path under that directory**.
The entire referenced directory is phantom.

### 3.1 What is reconstructible, and what is not

**The values are safe.** `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/UNIFIED_BOOK_MC_RESULT.json`
is real and tracked; its `conf` is byte-equal to `CANDIDATE_CONFIDENCE` and is pinned by
`test_candidate_book_consistency.py:73`. It also carries `loo_sharpe`, `new_sleeve_firedays`,
eleven ranked MC scenarios, and per-sleeve `matched_days` / `total_weighted_R`.

**The derivation is not.** That artifact restates the weights as **inputs** to all eleven scenarios
and never derives them, and they are not a function of anything it publishes:

| relation | Spearman (n=9) |
|---|---:|
| confidence vs R/day per fireday | **−0.1111** |
| confidence vs matched_days | +0.2992 |
| confidence vs firedays | +0.2821 |

`kz_london_crypto_low` has the **second-highest** per-day expectancy (0.337) and the **lowest**
nonzero weight (0.10); `metal_session_reversion` has the **lowest** (0.073) and the **highest**
weight (0.40). **No published statistic orders them.** Recorded as an owner-facing risk.

### 3.2 The risk framing needed correcting too

The concern as posed was *"those weights feed sizing on live accounts."* **Measured: they do not.**

```
armed set               crypto, energy_agri, sub_mid_dn_revert, sub_xvol_pullback
candidate-book names    asia_pdl_fade, asian_fade, kz_london_crypto_low, liq_asia_up_low_metal,
                        metal_session_reversion, ny_crypto_momentum, ny_index_momentum,
                        orb_crypto_london, structural_retest, vol_compression, vol_squeeze,
                        vss_fxcross_london_up_low
INTERSECTION            [] (empty)
```

All four armed sleeves take their confidence from `admission.SLEEVE_REGISTRY` (`crypto` 0.85,
`energy_agri` 0.80) and `admission.CLEAN3_REGISTRY` (`sub_xvol_pullback` 0.45, `sub_mid_dn_revert`
0.20) — whose own provenance artifacts **do** exist and are tracked (`INTEG_portfolio_build_w2.py`,
`INTEG_W5_CLEAN3_DEPLOY.json`, `PORTFOLIO_BUILD_W5.md`).

So this is a **debt, not an emergency** — and it becomes an emergency the moment any candidate-book
name enters `run_book.py --tags`. Both halves are pinned:
`test_the_cited_principal_audit_has_never_existed` (an assertion of absence, which fails the day
someone recovers *or fabricates* the audit) and `test_the_candidate_weights_size_nothing_that_is_armed`
(which fails the moment the intersection stops being empty, and says why in its message).

---

## 4. D — THE SWEEP

`SUPERSEDED_CLAIMS_V1.json` carries seven ranked rows. Ranked by whether anything still depends on
them:

| id | severity | still depends on it |
|---|---|---|
| `WAVE20-ARMED-SET` | **CRITICAL_WHEN_LIVE** | the launcher did, until this lane. **REPAIRED.** |
| `STAGE13-POOLED` | HIGH | the live allowlist authorised by it; no armed money (V4 gates never fire) |
| `STAGE13-NEGATIVE-AT-BIRTH` | HIGH | same allowlist; **first measured 2026-08-07** |
| `STAGE13-SDX` | HIGH | 70.9 % of the activation case |
| `CANDIDATE-BOOK-WEIGHT-PROVENANCE` | MEDIUM today, **HIGH on any candidate-book arming** | nothing armed; pinned both ways |
| `STAGE13-LSR` | MEDIUM | allowlist rows |
| `STAGE13-OLD3` | MEDIUM | allowlist rows |

Two claims examined and **not** filed, because they turned out to be right: `energy_agri` and
`sub_xvol_pullback`'s published economics reproduce unmoved under the corrected walk (§1.5), and
`UNIFIED_BOOK_MC_RESULT.json`'s `conf` is exactly `CANDIDATE_CONFIDENCE`.

---

## 5. SAFETY, AND WHAT THE OWNER MUST KNOW BEFORE A CARRY

* **No broker-mutating script was run. The VPS was not touched. No live-forward P&L was read.**
* **H1 drift: 3 entries before this lane and 3 after — identical** (`broker_net_cost_engine.py`, the
  pre-existing owner-authorised CN break, plus the two unhydrated LFS pointers, which are not drift).
* **`config/agent_config.yaml` was edited** (a comment on the retracted allowlist). Two consequences,
  in the words they need to be said in:
  * it **breaks the R2 execution seal** via `config_file_hashes`. Already broken forward by CN, so no
    new option is lost — but any future sealed replay must regenerate its decision contract first.
  * **the activation token binds the config digest.** If this config byte is carried to the host, the
    token must be re-minted or the book refuses to place orders. Both tokens currently expire
    **2026-08-14**. *This lane's recommendation is NOT to carry it*: the mainline and host configs
    already differ (`include_clean3` is `true` on the host at `:1200`, `false` here at `:1270`), the
    comment is documentation for readers of this repository, and it buys the host nothing.
* **`scripts/run_book_supervisor.ps1` was edited and this one DOES matter on carry** — see §6.

---

## 6. WHAT THE HOST NEEDS — for the operator, not for an agent

**The host is already correct.** Session LM executed the disarm on 2026-08-05 and committed it on the
host branch as `2fa77722d` so no checkout can re-arm it. **Nothing needs to be done on the VPS as a
result of this lane.**

What changed here is that the *committed* launcher no longer disagrees with the host. The reason that
matters is a specific, recoverable accident: had anyone deployed `scripts/run_book_supervisor.ps1`
from this repository to the host, the FTMO worker would have come back up with five tags and
`--frontier-exits mx_btcusd_d1_donchian_20_breakout`, re-arming a sleeve the owner turned off, and
**every log would have read healthy** — the heartbeat, the gates and the account identity are all
indifferent to `--tags`. The check is the command line, not the heartbeat.

Three standing facts for whoever runs the next ceremony, all measured:

1. **Do not carry this file wholesale.** The host's launcher is a different, larger file (19,495 B vs
   7,828 B; `$books` at `:140` not `:86`; spread-floor key `floor` not `spreadFloor`). Carry
   individual argument changes.
2. **`--tags ""` is fail-open**, not empty — an empty string runs every BUILT sleeve
   (`run_book.py:383`). An all-typo `--tags` is fail-closed but **mute** (`registry.py:144`).
3. **Arming mid-day is a size event.** `RunningConvictionLedger` persists a per-day union of firing
   sleeves and `admission.py:1188` takes `na = max(na, override)`; a restart can inherit a wider
   same-day set and move the half-Kelly multiplier 0.991 → 1.241 (**+25.2 %**). Arm at a decision-day
   boundary or delete that namespace's `firing_sleeves.json` first. (LM checked this on 2026-08-05
   and it was not applicable — no `2026-08-05` key existed.)

---

## 7. WHAT THIS LANE DOES NOT SETTLE

1. **The armed-set declaration is only as good as its decision log.** The log is populated from the
   receipts that exist; if an arming decision was ever taken without a receipt, this lane cannot know
   it. The test enforces that every *recorded* row has an authority and a receipt, not that every
   decision was recorded.
2. **The candidate-book weight derivation is gone, not recovered.** §3 establishes it is not
   reconstructible from the surviving artifact. Rebuilding it is a real piece of work and it is owed
   before any candidate-book sleeve is armed.
3. **The STAGE13 allowlist is annotated, not changed.** Whether to prune the four negative-at-birth
   families from `moonshot_dynamic_execution_router_activated_origin_families` is a strategy
   decision. It costs nothing today (the gates never fire) and it is Borhen's call.
4. **`sub_mid_dn_revert`'s p = 0.0858 is a statistic, not a verdict.** Re-running the ratified gate
   needs AN's sealed population spec and `CANDIDATE_BOOK_V1`'s family, which belongs to whoever owns
   the admission. What is now true is that the number exists.
