# GTOS Live System-of-Record (authoritative)

Created 2026-06-16 to resolve MACRO-A2 / MACRO-A3 / SYNTH-3 / OPS-07 — "multiple contradictory
architecture/config models with no single source of truth." This file is the SINGLE authoritative
statement of the FACTUAL live model, verified against the running system (not the stale design notes).
Where a config/doc disagrees with this file, THIS FILE is correct and the other is stale.

## 1. Dual-broker execution model — TWO INDEPENDENT BOOKS (not primary/follower)

The live system runs **two fully independent per-account book workers**, NOT a primary/follower projector:

- `run_book.py --namespace operator_profile` → connects ONLY to `C:\MT5\FTMO`, sizes from FTMO's own
  equity, has its own governor/day-anchor/high-water, its own PlacementLedger, its own kill/flatten flags.
- `run_book.py --namespace redacted_account_live_bee34003` → the same, fully independent, against `C:\MT5\redacted_account`.
- The `GTOS_W7_BookSupervisor` scheduled task is the SOLE starter; it keeps both alive + the monitor.

There is **no live projection** of one account's decisions onto the other. Each account independently
generates the same sleeve signals from its own broker feed and sizes from its own equity. They place the
same *kind* of trades because they run the same sleeves on the same symbols, not because one mirrors the other.

**STALE / NOT THE LIVE MODEL (do not trust):**
- `config/profiles/operator_profile.yaml: dual_broker.runtime_model =
  redacted_account_primary_full_ftmo_follower_projector` and `role: follower_projector_only`. This is a DESIGN
  that was **never the deployed runtime** — the live books are independent (above). The block is inert for
  execution (no projector process runs). Left in place as design history; it does NOT drive live sizing.
- Older "FTMO-primary, redacted_account-follower" phrasing in CLAUDE.md / memory: also not the live execution
  model (the books are independent). "Primary" only meant FTMO is the account the owner cares most about.

**OWNER STRATEGY DECISION (genuinely open — not mine to set):** do you WANT the independent-books model
(current), or a real primary/follower projector (size one account, mirror onto the other with the
contract-size rescale)? The independent model is what runs and is verified safe. If you want the projector,
that is a build, not a doc fix. Until you say otherwise, independent books is the system of record.

## 2. Risk dial — 2.0% ceiling, per account, smooth-defended

- Active allocation profile: **`clean3_w7_ceiling_nom2p00`** (2.0% nominal) on BOTH accounts, validated by
  CYCLE62 (p_pass 1.0, 0% daily breach, worst-day −4.695%, eff ~1.73% on the core-8). This is the OWNER's
  validated choice — do NOT change it without owner direction.
- Mandatory pairing: `ultimate_book_derisk_mode: smooth` (the admit_and_size interlock fails closed at
  >=2.0% without smooth). Now also config-declared (was env-only). This is the one ceiling-dial
  precondition that is **machine-enforced** — `admission.py:1366` emits
  `ceiling_profile_requires_smooth_ddefense` [VERIFIED 2026-07-25].
- Per-unit size = `2.0% × sleeve_confidence × half-Kelly × derisk_mult × stress_derisk_mult`, then the
  governor `size_cap_multiplier` (max-DD band + OPS-03 profit-target protect). Low-conviction sleeves
  (idxrev/fx_jpy conf 0.15) therefore size to ~0.1–0.2%/trade by design.
  **CORRECTED 2026-07-25 — that formula is incomplete and overstates per-trade risk.** Read directly
  from `src/components/ultimate_book/admission.py:1000-1176` [VERIFIED], the actual chain is:

  ```
  conf       = max over same-cluster members of
               ( sleeve_confidence × intra_size × min(overlay_su × kelly_mult, 1.75) × learning_tilt )   :1152-1168
  unit_risk  = base_risk_per_unit × conf × derisk_mult                                                   :1170
  per_trade  = unit_risk / n            # n = same-day, same-correlation-cluster intents               :1171
  ```

  **Anchors re-verified 2026-07-26** after the VPS book merge (`46c526bfe`) inserted 4 lines into
  `cluster_of`. The formula itself is unchanged — the sizing math is byte-identical across that
  commit — but every line number in this block had drifted by +4 and is corrected above.
  `OVERLAY_SIZEUP_MAX = 1.75` is now `admission.py:308`.

  Three factors the sentence above omitted: (1) **`÷ n`** — a correlated risk *unit* is sized once and
  split across its n same-day same-class members, so per-trade risk is a fraction of the unit;
  (2) **`min(…, OVERLAY_SIZEUP_MAX = 1.75)`** (`admission.py:308,1153`) — a hard cap on the *combined*
  confluence-overlay × Kelly-lite tilt. It binds even though `ultimate_book_overlays: false`
  (`agent_config.yaml:1289`), because `kelly_mult` routes through the same cap; (3) `intra_size` and the
  owner-armed `learning_actuator` confidence tilt. `stress_derisk_mult` is not a separate trailing
  factor — it is folded into `derisk_mult`. Net effect: the old formula was **conservative-wrong**
  (it implies more per-trade risk than the code takes), but it should not be used to reason about sizing.
- Stale references to "1.25%/1.50% dials" in older comments are superseded by the 2.0% ceiling.

## 2b. Live book composition — AMENDED 2026-07-25 (was absent from this file)

**This file was written 2026-06-16 and describes the core-8 book. Two additional books were switched on
2026-06-18 and were never recorded here.** Recording them now, because everything downstream — the W7
live-drawdown forensics, the Phase-6 cost calibration, and any claim about what was validated — depends
on knowing what actually ran. Verified identical on HEAD and on the live VPS branch
(`remotes/origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`) [VERIFIED 2026-07-25]:

| Component | Key (HEAD line / VPS line) | Value | Validation cited in config |
|---|---|---|---|
| clean_3 (3 sleeves) | `ultimate_book_include_clean3` (1270 / 1200) | `false` — dropped 2026-06-15 as selection-glow | — |
| core-8 | (implied by the above) | **live** | CYCLE62_CORE8_REVALIDATION: p_pass 1.0, daily_breach 0 %, worst_day −4.695 %, eff ~1.73 % after half-Kelly (`agent_config.yaml:1297-1299`) |
| candidate book (**9** sleeves) | `ultimate_book_include_candidate_book` (1272 / 1202) | `true` — "ON 2026-06-18" | **none cited** |
| market-expansion book (**12** sleeves) | `ultimate_book_include_market_expansion_book` (1284 / 1214) | `true` — "ON 2026-06-18 owner-approved all-in activation package", policy `positive_weighted12_after_swap` | **none cited** |

So the live book on 2026-06-18 was **core-8 + 9 + 12 = 29 sleeves**, not the 8 this file implies.
The 9-sleeve allowlist is explicit at `agent_config.yaml:1274-1283`; the 12 are resolved by the named
policy (`ultimate_book_market_expansion_sleeves: []` at `:1288` — the policy name, not an allowlist,
selects them).

**Two consequences, stated plainly:**

1. **The dial's validation covers core-8 only.** `agent_config.yaml:1294-1301` is explicit that CYCLE62
   re-proved the 2.0 % ceiling "on the actually-DEPLOYED core-8 book WITH smooth DD-defense". That
   comment was written when core-8 *was* the whole deployed book. Three days later 21 sleeves were added
   and the validation citation was never revisited.

   The config cites the artifact with an elided path (`research/.../KNOWLEDGE_BASE/validation/
   CYCLE62_CORE8_REVALIDATION.json`), which resolves nowhere. **Located and read 2026-07-25** [MEASURED]:
   it is on `origin/live-handoff-2026-06-15` at commit `98da29d2a`, path
   `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/KNOWLEDGE_BASE/validation/CYCLE62_CORE8_REVALIDATION.json`
   (2,554 B), alongside its generator `CYCLE62_core8_revalidation.py`. It is **not** on HEAD and **not**
   on `origin/deploy-live`.

   Its scope, read in full [VERIFIED]: `base: 0.02`; two series (`core8` n=1679, vs 0.8647;
   `elevensleeve` vs 0.7504); two accounts (`FN_fresh_tgt108`, `FTMO_97p2k_tgt110`); two book variants
   (`11sleeve_control` eff 1.501 %, `CORE8_DEPLOYED` eff 1.729 %); three de-risk modes. The quoted live
   numbers are the `CORE8_DEPLOYED` + `smooth` cell: `p_pass 1.0`, `daily_breach_pct 0.0`,
   `worst_day_pct −4.695`. **The file contains zero occurrences of "candidate", "expansion" or
   "weighted12"** [MEASURED]. So no joint validation of the 29-sleeve book at the 2.0 % ceiling exists
   in the cited artifact, and none is referenced anywhere else on the live surface. This is a fourth
   confounder on the W7 live drawdown, alongside the three in `SECOND_AUDIT.md` F1's owner-decision update.

   **One number from CYCLE62 bears directly on reading the W7 live fortnight:** under
   `CORE8_DEPLOYED` + `smooth`, the MC's own **median days-to-target is 64 (redacted_account) and 110 (FTMO)**.
   The live window was ~10 trading days — roughly 9–16 % of the median horizon the locked MC itself
   projects. Whatever the W7 drawdown was, this dial's own validation says a 10-day window is far too
   short to falsify it. That arithmetic belongs in the Phase-1 G1b forensics.
2. **`admission.py`'s own profile registry contradicts the deployed config, and nothing reconciles them.**
   `admission.py:774-779` documents `clean3_w7_ceiling_nom2p00` as usable **"ONLY with
   include_clean3=True + kelly_lite=True + stress_derisk=True"**, and `bridge.py:71` defaults
   `ultimate_book_include_clean3: True` with the comment "W7 final book = clean_3 (11 sleeves)". Live ran
   it with `include_clean3: false`. Of the three stated preconditions, `kelly_lite` and `stress_derisk`
   hold (`agent_config.yaml:1303,1309`); the composition one does not, and **no code enforces or
   annotates it** [MEASURED — no raise/assert/require guard exists on `include_clean3` anywhere in
   `src/`]. Per CYCLE62 the deployed core-8 configuration is nonetheless the validated one, so the
   docstring is *stale*, not the config wrong — but a reader of `admission.py:777` is currently told
   the live configuration is forbidden. The docstring is queued for correction under the Phase-0
   fork reconciliation (`admission.py` is **not** contract-bound, so the edit is free).

## 3. Account identity authority — per-profile `expected_account` assert (fail-closed)

- Each profile carries `broker_profile.expected_account` (login compared as a salted-free SHA-256 — no raw
  login/credential in code/config), plus server/company/currency/terminal paths.
- `run_book.py` calls `assert_mt5_account_matches_profile(mt5, merged)` after connect; ANY mismatch or
  inability to verify → refuse to start (exit 5). This is the single identity gate (MACRO-A4). A
  namespace can therefore never trade the wrong real-money account.

## 4. Daily-loss / max-DD governor — per account, broker-correct, DST-aware

- Daily-loss baseline = day-start BALANCE reconstructed from realized closed deals since the **server-local**
  reset boundary (excludes floating P&L; survives mid-day restart); fail-closed if unreadable.
- Reset-window offset now tracks the **live-measured** broker offset (DST-correct, self-re-detecting every
  6h), config `governor_daily_reset_offset_hours` as fallback.
- Static max-DD wall = `governor_static_initial_balance × (1 − max_dd)` (a fixed 90k for a 100k account;
  does NOT trail). Soft daily stop −3%, hard −5% enforced via the joint gross-cap collapse + breach-flatten.

## 5. Single-instance / no-double-book

- `run_book.py` holds an ATOMIC named kernel mutex (`Local\GTOS_W7_run_book_<namespace>`) + a pid-file
  guard. The supervisor never stops a book (only starts a missing one), so it can never orphan a position.

## 6. Mainline-ahead carry-back — what the VPS lineage does NOT have (recorded 2026-07-26)

Phase 0 merged the VPS live package into mainline. Three things travel the **other** way and are
recorded here because nobody can push to the VPS from this build surface: whoever next redeploys
`remotes/origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18` (`redacted_host`, 2026-07-02) must
carry them, or the deployed copy silently loses them.

| Mainline-only | Why it matters on the VPS |
|---|---|
| **P4 — `create_mt5` mode validation** (`src/mt5/__init__.py:20-27`) | The VPS copy still falls through to `RealMT5` for any non-`"mock"` mode, so a typo (`"mok"`, `"simulate"`, `""`) opens a **real broker connection**. Mainline raises `ValueError` on an unknown mode. |
| **The three `convergence_*` modules** (`convergence_advisory.py`, `convergence_replay_matcher.py`, `convergence_replay_record.py`) plus their integration in `book_owner.py` (the import, two `__init__` flags, two status fields, `_runtime_learning_convergence_advisory`, and 7 emission call sites) and `runtime_learning_packet`'s `convergence_advisory=` parameter | The VPS `runtime_learning_packet` has **no** `convergence_advisory` kwarg. Deploying mainline's `book_owner.py` against the VPS's packet module is a `TypeError` on **every book cycle**. The two must move together. |
| **The activation token** (`src/safety/activation_token.py`, the guard inside `RealMT5.order_send`, and `run_book.py`'s `set_activation_context` call) | Without it a VPS worker is back to absence-of-halt semantics. With it, the VPS needs a minted token in `$GTOS_ACTIVATION_TOKEN_DIR` (or `~/.gtos/activation`) per account **before it can open any position** — see `scripts/gtos_activation_token.py`. Risk-reducing requests still pass without one, so this can never strand a position. |

**Contract of record for any new replay window: R2, not R1.** OD-2 landed 2026-07-26 as
`B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json`. Pass it to
`--decision-contract`; R1 now reports two drifted paths because P1's fix landed in the two verifiers
the split freed. R1 and January's acceptance are untouched.

## What to read for ground truth
- Live state (mechanical): `.context/LIVE_STATE.md` (regenerate via `scripts/generate_live_state.py`).
- This file: the authoritative architecture/config/identity model.
- Audit resolution: `research/operations/live_ops_intelligence_2026_06_15/AUDIT_RESOLUTION_LEDGER.json`.
