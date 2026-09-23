# GTOS Second Independent Audit — Fable 5

**Scope:** independent verification of the Opus-5 architecture audit (`docs/audits/opus5-architecture-20260725/`),
plus the layers that audit never examined: the learning stack, the AI companion / command-center surface,
the execution boundary and `run_book.py`, the data layer, test/proof quality, and the full-vision gap.
**Branch:** `audit/claude-opus5-architecture-20260725`, continuing after the first audit's five commits.
**Method:** firsthand re-read of the entire authority chain and all twelve prior deliverables; nine parallel
investigation agents (one per unexamined layer, plus dedicated adversarial attacks on keystone claims E1,
E9, E10); direct measurement against the sealed evidence in the owner's read-only worktree; independent
re-classification of the committed 86,945-sample profile. Every claim is tagged
**[MEASURED]** (this audit ran/observed it), **[VERIFIED]** (read directly in code or sealed artifacts),
**[INFERRED]**, or **[HYP]**, with `file:line`.

**Posture:** I was instructed to attack the first audit, and did. Where it was wrong, that is stated
plainly; where it holds, that is stated plainly; where this audit's own findings could be wrong, the
falsification route is named.

---

## 1. Verdicts on the first audit's ten load-bearing claims

| # | Claim | Verdict | What changed |
|---|---|---|---|
| E1 | Replay implements allocator/selector/continuous sizing the live path doesn't → replay R doesn't transfer | **HOLDS — and understates the gap** | The live-designated system is a different *strategy family* entirely (§2.1). Wording corrections: book package at HEAD is current (entrypoint un-vendored, not "unwired"); packet fabrication is a deliberate post-admission compat shim; book conviction sort is cap-shedding, not selection |
| E2 | `run_book.py` is not in the repository | **HOLDS, sharpened** | It *is* locally readable (`git show remotes/origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18:run_book.py`, 324 lines) — but vendoring fails on ImportError, and the real gap is a **two-way fork of the whole live package** (§2.3) |
| E3 | Proof layer verifies bytes, never economics | **HOLDS at the per-trade level; strongest form refuted at aggregate level** | The route analyzer *does* independently re-sum economics from ledger rows with per-row identity checks (`pnl_cash == risk_cash × net_r` @1e-6; stress recompute @1e-8) — better than the first audit credited. But **nothing anywhere recomputes a trade's R from prices**: the analyzer contains zero `entry_price`/`exit_price`/`stop_loss` references, so an engine-side per-trade R defect is certified by the whole chain (§3.5) |
| E4 | No sealed Phase-D arm has a semantic parity proof | **HOLDS** | — |
| E5 | Proof/attribution is 60.6 % of replay CPU; decisions 8.3 % | **HOLDS — and 60.6 % is indeed a lower bound** | Independent re-classification with a stricter taxonomy: **proof-complex = 72.4 % of captured self-time; pure decide+simulate self-time = 0.3 %** [MEASURED, §5.1] |
| E6 | 15.75 GB / arm; 494 KB order rows, 63.8 % key names | **HOLDS** (re-read from arm receipts) | — |
| E7 | Contract binds 42 files incl. 9 never-executing verifiers; proof fixes cost a campaign | **HOLDS** | — |
| E8 | Memory binds before CPU; parallel arms impossible today | **CONFIRMED in precise form** | 2-way is measured ~1.1–1.3× net (the audit's own contended run is the experiment); ~~"15.32 GB footprint" is a unit echo of the verified 8.61 GB maxrss; fix target ≤3 GB/arm~~ *[both struck 2026-07-27 — two `/usr/bin/time -l` fields, not one converted (B81/B83); 8.61 GB is a 2-day fixture; the ≤3 GB target is withdrawn. See §5.3's banner]* (§5.3) |
| E9 | 21.7 % reachable; 219,469 lines LOW-risk deletable | **Reachability HOLDS and is understated (true denominator: ~15 % of 2.35 M tracked lines); the deletion plan is NOT executable as specified** | The un-materialized LOW tier would delete the live book surface and the ML pipeline; per-file sweeps + vendoring preconditions added (§5.4) |
| E10 | Vision needs ~30×, not ~3× → rebuild, not optimisation | **Number high by ~2× (no derivation existed); conclusion survives weakened** | Defensible band ~10–16×, reached by memory fix + projection + parallelism; "not by micro-optimisation" stands; the rebuild case rests on F1/F5/F7, not on throughput (§5.5) |

Corrections this audit forced on the first audit's register (beyond the verdict table):

- **R8/U3 — resolved, and the register was wrong on a premise.** The dynamic daily-drawdown budget is
  **enabled in the contract-bound base config** (`scheduler_v4_best_trade_allocator_dynamic_daily_drawdown_budget_enabled: true`,
  `config/agent_config.yaml:982` → mapped at `v4_timewarp:30083-30086`), not "runner-supplied"; the
  runner's R0 branch disables only the *quality-gate* sub-flag (`attempt5:11971-11982`). So the
  lexical-order materialisation mechanism was **armed in all four sealed arms** — and it **never
  bound**: across all 662 sealed January order rows plus the 88-row April partial,
  `requested_risk_pct == final_approved_risk_pct` on every row; minimum
  `daily_runtime_headroom_pct_before` is 1.555 % (January R1) / 1.610 % (April) against the 4.0 % cap
  [MEASURED]. R8/R9's realised effect on all sealed evidence to date: **zero orders, zero sizes.**
- **U2 — resolved.** `duplicate_exact_candidate_instance` drops: **zero** in all four sealed arms
  (summary counter `candidate_duplicate_profile_scoped_instance_rows = 0` ×4; zero matches streamed
  from all four cold decision ledgers; 5,647/5,647 local decision rows `materialized`) [MEASURED].
  R17's "silent loss of unknown rate" is now measured at zero on all sealed evidence. Side-finding:
  the sealed arm path never persists `ledgers["event"]` at all (the event-ledger role exists only on
  the legacy `build_route` path, `v4:393,95046`), so had drops occurred, the only surviving record
  would be that summary counter (F14).
- **R5 framing of `execution.py:3169-3182`** — those lines *refuse* to re-anchor ("do NOT
  re-anchor/chase", `:3174`); the prior audit's divergence table described them backwards [VERIFIED].
- **R1's "unwired at HEAD"** — restated: the `ultimate_book` package at HEAD is current and even
  three modules ahead of the deployed copy; only the entrypoint is un-vendored (§2.3).
- **Learning-stack inventory errors** — `model_pin.py` / `model_router.py` are Anthropic-LLM serving
  infrastructure, not ML-pipeline components; `learning_actuator.rerate_book`'s consumption path is
  **fully implemented and config-gated** (`bridge.py:283→:410`, `admission.py:1075-1076,:1162`), not
  "comments only"; and the learned-edge lane's dedicated tests (772 lines under
  `tests/research_infra/` + a 672-line selector-mode suite) exist and were missed (§3.1).
- **R35 nuance** — `dormant_state.json` is written/read on the *orchestrator* path only; the book
  never consults it, so the cross-account contamination it implies requires the retired fleet to be
  running. The genuine shared-state list for the two-books model is: the default kill flag (brakes
  both books), the shared flatten flag (deliberate), and two shared-append JSONL ledgers
  disambiguated only by an in-row namespace field [VERIFIED].
- **H2's causal story is nine-tenths wrong.** [MEASURED] Hydrating the sleeve-registry LFS pointer
  (`git lfs pull`, succeeded, working tree stays git-clean) fixed **exactly one** of the 11 red
  tests. The 10 remaining `test_selector_v4.py` failures are a genuine behavior/expectation mismatch:
  `package_execution_fill_probability` resolves `None` because the lookup chain
  (`selector_v4.py:4004-4016`) consults only `execution_fill_probability` /
  `predecision_limit_fillability_probability` — never the `entry_quality_fill_probability=0.3` the
  fixtures provide — so `quality_allowed: false`. The mismatch predates visible history; the loader
  even contains purpose-built LFS-pointer fallback logic (`replay_lfs_pointer_fallback`,
  `ultimate_candidate_package.py:769-782`), i.e. someone engineered around the pointer problem while
  the standing explanation still blamed it. **A real red signal on the selector's package-admission
  path is being routinely ignored under a wrong diagnosis.** (New finding F13.)
- **H6 amendments** — the dual-broker follower's re-transmission additionally requires opt-in
  `--order-enabled` (`:2600`, dry-run path `:2205-2211`), and `engine.open_trade` does carry the
  config-armed halt guard; `mt5_preflight.py` has been partially repaired since the register (real
  order now behind opt-in `--test-order`/env). `fn_smoke_trade.py` is *worse* than recorded: it
  drives the **raw `MetaTrader5` module** (`:59`, order at `:347`), bypassing `create_mt5`, `RealMT5`
  and the entire engine guard stack [VERIFIED].

---

## 2. Tier-0 findings of this audit (new)

### F1 — GTOS contains two competing decision stacks with disjoint evidence chains, and the sealed campaign measures the one the go-live dossier ordered off

**[VERIFIED across four independent sources.]**

- **Stack A — the broad V4 surface** (what the sealed replay measures): 24-symbol
  `broader_origin_generators` candidates → Selector V4 admission → Scheduler V4 best-trade
  allocator → continuous cash sizing. The replay self-declares its generator
  (`v4_timewarp:59385`). The B7.5 incumbent arm is literally
  `selection_mode: "quality_ranked_current", sizing_mode: "dynamic_runtime"` (`v4:36199-36202`).
- **Stack B — the W7 `ultimate_book`** (what `live_system_of_record.md` declares live): 11+9+12
  statistical sleeves, stdlib-pure byte-faithful ports of the locked route
  `final_moonshot_v4_ultimate_mechanical_edge_2026_06_10`, TRAIN ≤2024 / FWD 2025-26 validated by its
  own locked engine, Kelly-lite conviction sizing under a fail-closed governor.
- **Zero shared signal code.** The replay imports exactly one thing from the book: the
  `TICK_SPREAD_FLOOR_R` cost table (`v4:105-108`). The book imports nothing from the generators.
  Name rhymes (`vol_compression` sleeve vs `volatility_compression_expansion` family) are independent
  implementations. The one decision-bearing coupling in the sealed arms is session-token
  reclassification: `selector_v4_package_session_token_authority_enabled: true`
  (`config:790` → `selector_v4.py:2126-2168`) lets package session tokens rescue off-session
  candidates into a configured session; the package softening overrides are config-off
  (`config:791,795`).
- **The stacks are mutually exclusive by design.** `bridge.py:28-33` encodes the replacement
  invariant — the bridge fails closed if the broad selector is still apply-to-execution when the book
  bears risk — quoting the go-live dossier: *"The losing broad V4 selector (−0.25R/fill native;
  ULTIMATE_GO_LIVE_DOSSIER.md) must be OFF when the book is live."*
  (dossier readable at `git show 86cccd08d:research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_GO_LIVE_DOSSIER.md`).
- **And the campaign's own midpoint economics corroborate the dossier.** From the sealed January
  matrix audit (`B7_5_SELECTION_SIZING_DEVELOPMENT_JANUARY_SOURCE_REPAIRED_R3_CAP_R2_MATRIX_AUDIT.json`):

  | Arm | scoreable_net_cash | scoreable risk cash | q = net/risk |
  |---|---:|---:|---:|
  | S0R0 neutral/fixed | −201.31 | 8,800 | −0.023 |
  | S1R0 quality/fixed | −550.60 | 7,500 | −0.073 |
  | S0R1 neutral/dynamic | −5,432.33 | 39,881 | −0.136 |
  | S1R1 incumbent | −6,596.06 | 36,778 | −0.179 |

  Sealed analyzer classification: **selection = inconclusive** (−0.049, inside the ±0.1 band),
  **sizing = material_negative** (−0.1105, crossing the sealed threshold), interaction =
  non-claimable positive with execution suppression. Every arm lost money in the January development
  window; the dynamic-runtime sizing that mimics the incumbent policy is the measured value destroyer.

**Consequence.** The compute-heavy sealed campaign (~16.5 h per window, three windows remaining)
decomposes selection-vs-sizing *inside Stack A*, whose native live measurement was −0.25R/fill and
whose January development economics are negative in all four cells — while Stack B, the only surface
with positive forward-validated economics and the declared live model, has **no representation in any
replay harness at all**. The B7.5 protocol's promote action would freeze a Stack-A arm and advance it
toward canary (`B7_5_SELECTION_SIZING_EXPERIMENT_PROTOCOL.json: actions.promote`), directly colliding
with the bridge's replacement invariant.

**This is not a claim that B7.5 is worthless** — its factorial isolates *mechanism* questions
(does quality selection add value at equal risk? is dynamic sizing worth its risk expansion?) whose
answers transfer as design knowledge. It is a claim that the **activation-bearing surface and the
measured surface have diverged**, that no document decides which stack is the activation candidate
(charter 2026-07-16 continues Stack-A research; system-of-record 2026-06-16 declares Stack B live),
and that the rebuild must close this by hosting both policy families behind one decision core so the
replay measures whatever would actually trade (§6, and `FULL_VISION_PLAN.md`).

**Falsified if:** someone shows a sealed replay arm whose executed trades are generated by the book's
sleeve registry, or an owner decision record designating the B7.5 winner rather than the book as the
activation policy. Neither exists in either checkout today [VERIFIED].

**OWNER DECISION UPDATE (2026-07-25, after this finding was reported).** Borhen supplied the missing
decision record in conversation: the W7 book **did go live** (2026-06-18 → 2026-07-02, both accounts),
underperformed, and he deactivated it (the "SHADOW 2026-07-02" switch) and went "full in" on the
current broad system — the plan is to build this system to quality and activate it, not W7. This
audit then read the live evidence from the VPS branch directly:

- Live window ≈ 10 trading days. Broker snapshots: 2026-06-23 FTMO `95,716.59` / FN `99,187.00`
  (flat); 2026-07-02 shadow switch FTMO `94,638.26` / FN `96,133.42` (one `W7:idxrev` short each,
  both closed at TP shortly after → ≈ `94,664` / `96,164`). Against a fresh 100 k FTMO challenge
  start: **FTMO ≈ −5.3 %**; FN's 06-18 start is not pinned in the branch (pre-halt fleet losses on
  the same account) → **FN book-era ≈ −3.0 to −3.9 %** [VERIFIED snapshots; starts part-inferred].
- **Attribution is confounded by three deployment choices**, all documented on the branch: (1) it
  went live at the **2.0 % ceiling dial** (`clean3_w7_ceiling_nom2p00` + smooth), not the dossier's
  recommended 1.25 % first-cycle — at 2.0 % the dossier's own table says stress maxDD-fail ~25 %;
  (2) what went live was **not the validated 11-sleeve clean_3** but core-8 + the 9-sleeve candidate
  book + the 12-sleeve conditioned market-expansion book, audited 06-17 and owner-approved/activated
  **same-day** 06-18; (3) the window carried ~20 live hardening commits with hot reloads — the
  accretion pattern, live. A ~10-day window at the ceiling dial cannot statistically separate "edge
  absent" from "aggressive dial + unlucky fortnight"; the FTMO-vs-FN damage asymmetry on identical
  signals additionally implicates execution/universe differences.
- **Consequence for F1:** the fork is resolved by owner decision — the broad stack is the activation
  candidate (OD-1 answered). F1's architectural conclusion is unchanged (the policy-plural core makes
  the replay measure the activation candidate — which it now already does) and its evidentiary
  warning transfers: the current system must *earn* activation through the plan's gates, because its
  own current evidence (four negative January cells, sizing material_negative, KIAP holdout 1W/20L)
  is no better than what W7 died of.
- **One factual correction to the owner's stated premise, verified against the hydrated registry:**
  the belief "the current system has all the W7 sleeves, if not more" is **wrong at the signal
  level**. The current system's sleeve registry
  (`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`, 82 rows [MEASURED]) contains
  outcome-mined *groupings of the broad system's own 13 candidate families*
  (`fpsc_avoid_failure/redesign_repair/scheduler_lifecycle_merge__ob_retest/fvg_fill/…`) — **zero
  overlap** with the 32 W7 statistical sleeves (crypto, metals_core, energy_agri, sub_xvol_pullback,
  fx_jpy, vp_euidx_pocgrav, ny_crypto_momentum, …). Dropping W7 drops that signal family and its
  2014–2026 validation work entirely; keeping it as a benchmark/challenger inside the policy-plural
  core costs almost nothing. The W7 live fortnight is also the only live-execution evidence the
  modern stack has (fills, slippage, spread blocks, reconciliation) and is priority input to the
  Phase-6 cost calibration regardless of W7's fate as a strategy.

### F2 — The documented hard halt has no filesystem existence on this machine; the operative brakes are the platform boundary and committed config gates

**[MEASURED.]** All local checkouts — including `/Users/borr/GTOSActive/repo` — are sparse checkouts
that exclude `pipeline_state/` and `knowledge_base/meta/`. The three halt-flag files exist in **no
local working tree**; they are tracked in git (the blob records the CEO's 2026-06-03 halt order
verbatim) but skip-worktree masked. Halt-guard semantics are *missing-flag = clear* and CWD-relative
(`src/safety/runtime_halt.py:103-110,161-178`). Therefore any live-capable process launched from any
checkout on this Mac would report `runtime_halt_clear`.

What actually prevents trading from this machine, in order: (1) the `MetaTrader5` python package is
**Windows-only** — every broker-capable script, including the H6 hazards, dies at import on macOS;
(2) `ultimate_book_live_activation_allowed: false` at HEAD (`config:1250`) — committed, and sufficient
for the book path; (3) the legacy fleet is fail-closed end-to-end at HEAD config (F3); (4) whatever
flag files exist on the **VPS filesystem** — which is where the halt is real, and which is
unverifiable from here.

**Consequence.** "Hard-halted as broker/VPS state" in `CLAUDE.md` is accurate in substance but the
protective mechanism everyone cites (the flag files) is not what protects this build surface, and the
fail-open-on-missing semantics mean the flag mechanism *cannot* protect any fresh clone. The halt
design should be inverted for the rebuild: presence-of-authorization rather than absence-of-halt (an
activation token that must exist, bound to account + config digest), which also fixes R6 by
construction.

### F3 — At HEAD config, nothing can trade even if unhalted: the fleet dies at the packet wall, the book at its third gate

**[VERIFIED.]** If every halt flag were removed today: the book path stops at
`live_activation_allowed: false` → bridge shadow mode → `realized_units=[]`
(`bridge.py:421-436`, `book_owner.py:739-745`). The legacy fleet path stops at execution-manager
preflight: `execution_manager_v4_selector_v4_packet_required: true` (`config:1136`) makes selector/
scheduler packets mandatory, and **no component on the fleet path produces them** — the only
producers repo-wide are the replay (`v4:62803/62821`), a research gate, and the book's own shim
(`execution_packets.py:324/327`); the orchestrator only forwards packets if present
(`orchestrator.py:2590-2615`). Every fleet candidate dies `missing_selector_v4` → order refused
(`execution_manager_v4.py:1166-1176`, `execution.py:3336-3357`).

**Consequence.** Good news operationally (defense in depth is real at HEAD), but it also means the
"three challenge accounts ready" state is further from activation than the halt narrative implies:
activation is not "remove flags," it is "reconcile the fork (F4), vendor the entrypoint, flip two
config gates deliberately, on a Windows host with authenticated terminals."

### F4 — The live surface is a two-way fork: a month of live hardening exists only on the VPS branch, while HEAD evolved past the VPS in other modules

**[MEASURED.]** Merge-base `e0c2f8558` (2026-06-05); the VPS branch is 155 commits ahead, HEAD's
lineage 136; 1,715 files differ. On the live-critical package: `book_owner.py` **4,269 lines (VPS) vs
1,852 (HEAD)** — the VPS-only 2,561 lines are broker deal/exit reconciliation, position protection,
and realized-P&L joins from the live-operations month; `run_book.py` exists only there and imports
`bridge.config_bool_value`, which **has no definition anywhere at HEAD** (instant ImportError on
vendoring); the VPS tip adds a **fourth authority gate `ultimate_book_live_broker_authority: false`
("SHADOW 2026-07-02")** that HEAD code neither reads nor defines — the mechanism currently braking
the real VPS is one mainline does not implement. Conversely HEAD has three `convergence_*` modules
and the P4 `create_mt5` mode-validation fix that the VPS lacks (the VPS still opens a real connection
for any non-"mock" mode). An older, untracked third variant of `run_book.py` sits in
`/Users/borr/GTOSActive/repo` (15,216 bytes, mtime 2026-06-19).

And the fork is wider than code: **the book's entire evidence chain is off-mainline too.** The route
`research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/` — `geometry_lib.py` (the
locked validation engine), `INTEG_W7_FINAL_RESULT.json`, `ULTIMATE_GO_LIVE_DOSSIER.md`, the sleeve EV
tables and MC receipts, **661 files** — has zero files tracked at HEAD [MEASURED:
`git ls-files … | wc -l` = 0]; it lives on `origin/deploy-live` (86cccd08d) and the VPS branch
family. Mainline holds the book's *code* but neither its entrypoint, nor its protective companion
(F6), nor its *evidence of record*. No session working from this repo's HEAD has ever been able to
audit the evidence behind the declared live system — including both audits until this one read it
via `git show`.

**Consequence.** "Vendor `run_book.py`" (the first audit's step 1) is really **reconcile a
three-copy fork of the entire live lineage — code, safety layer, and evidence**, and any rebuild that
models "the live system" from HEAD's `ultimate_book/` alone models the wrong system in the opposite
direction from E1. This is the first concrete work item in the plan, and it adds a workstream neither
audit has done: **adversarially audit Stack B's evidence chain** (geometry_lib fill/exit semantics,
TRAIN/FWD split hygiene, MC assumptions) with the same rigor Stack A received — before it becomes the
activation candidate.

### F5 — The learning loop is one adapter away on the model side, and one emission away on the data side — and the blocker is the same schema problem the performance audit found

Full detail in §3.1. The short form: the learned-edge lane (770-line dataset builder → 719-line
trainer → 570-line walk-forward gate → 489-line frozen-artifact scorer → selector integration for
both admission *and* continuous sizing) is fail-closed, leakage-guarded, deterministic, tested, and
**dead at exactly one point: its input contract**. The replay's emission drifted (candidate-microscope
ledger dropped; `predecision_features` computed at `broader_origin_generators.py:1929` and discarded
at emission; filename scheme changed), orphaning four consumers. The 494 KB/1,274-key rows the
performance audit indicted are simultaneously **unusable as ML input** — the fix for both is the same
typed-event capture layer.

### F6 — A protective safety layer exists, enabled, only on the branch nobody audits

**[VERIFIED.]** A deterministic AI-companion runtime (`src/components/ai_companion/` — supervisor
1,013 L + control-state 523 L + launch script + supervisor PS1, tests included) exists **only on the
VPS branch**, `enabled: true`, authority `protective`, and it ran in shadow (8 proposals, 220 packet
rows in the absorption route). Its control surface is genuinely bounded: {pause_new_entries,
sleeve cooldown, risk_multiplier ≤ 1.0}, TTL ≤ 120 min, malformed state fails closed *into* pause.
Main has neither the module nor the book's gate hooks. A canary relaunched from this repo would run
without the protective layer its own sealed documentation describes. (The vision's "autonomous repair
companion," by contrast, was operator-driven agent sessions that hot-patched live code between ticks
— §3.2 — and should not be revived in that form.)

### F7 — The research data layer labels broker time as UTC; replay and live disagree about what hour it is

> **AMENDED 2026-07-26 by Phase 1 Session B — the defect is real, the calendar named below is wrong.**
> FTMO-Server3 is UTC+2/UTC+3, but it switches on the **US** DST calendar (2nd Sunday of March, 1st
> Sunday of November), not the EET/EEST one. Equivalently: broker wall clock = `America/New_York` + 7 h.
> The two calendars disagree for ~3 weeks each spring and ~1 week each autumn, and an EU-calendar
> correction is wrong by exactly one hour in every one of those windows. **The seam inside the sealed
> March challenge is therefore 2026-03-08, not 2026-03-29**, and it splits that window 1 week / 3 weeks.
> Measured over 2022-2026 on three independent exchange calendars plus UTC-native Sierra Chart CME
> futures; nine transitions, all on US dates, none on an EU date. See
> `CLOCK_TRUTH_IMPACT_NOTE.md` and `src/utils/broker_clock.py`. Every "EET/EEST" statement below and in
> `FULL_VISION_PLAN.md` item 5 should be read as "UTC+2/UTC+3 on the US calendar".

**[MEASURED + VERIFIED — data-layer agent; the single largest new defect of this audit.]**

- The MT5 export path converts broker-server epochs with `datetime.fromtimestamp(ts, tz=timezone.utc)`
  (`scripts/export_mt5_research_ohlcv.py:541`) — no server-offset correction anywhere. FTMO server
  time is EET/EEST (**UTC+2 winter / UTC+3 summer**). *[Amended: UTC+2/+3 is right; EET/EEST is not —
  see the banner above.]*
- Empirical proof from the data itself: bars end Friday **23:45 "UTC"** and resume Monday 00:00
  (`historical_2026/EURUSD_M15.csv`); ticks end Friday 23:54:59. True-UTC FX weeks end ~22:00Z. Every
  "UTC" timestamp in the research bar and tick exports is broker time, 2–3 h ahead of real UTC.
- The **live** path corrects: `mt5_real.py:212-244` (`_broker_epoch_to_utc`, self-detected offset,
  added 2026-04-28). The **replay** path parses the mislabeled stamps as UTC
  (`wave4r_replay_microstructure.py:130-142`).
- Session and kill-zone windows are shared wall-clock tables
  (`broader_origin_generators.py:66-110`, e.g. london 07:00–13:00; `data_ingestion.py:606-608`).
  **The same config therefore gates real-world market hours 2–3 h earlier in replay than in live.**
  "Asia range," London open, day boundaries, and every session-conditioned rule shift. The EU DST
  transition **2026-03-29 falls inside the sealed March challenge month**, adding a 1 h semantic seam
  mid-window; 2025-10-25 sits inside the tick window.
- Exactly one script in the repo documents the truth (`scripts/session_volatility_monitor.py`:
  "CRITICAL: MT5 M15 data is EET…" with a converter) — unused by the replay stack.
- Corollary for any forward/replay join: forward logs (slippage, pending-lifecycle) are true UTC
  (post-2026-04-28), replay data is broker time — a naive timestamp join misaligns by 8–12 M15 bars.

**What survives and what doesn't:** arm-vs-arm contrasts inside the sealed campaign are unaffected
(all arms share the shift). **Live-transfer claims, session-level attribution, session-conditioned
learning features, and the three hindsight session-level rejects (R14) are all built on a mislabeled
clock.** This adds a mandatory row to the divergence matrix, a repair item ahead of any learning
training run, and a re-check of every session-attribution conclusion in the evidence tree.

---

## 2b. Lesser findings register (F8–F22)

Numbered for reconciliation with the prior audit's R-register; each carries its evidence in §1/§3 or
the agent reports preserved via `AUDIT_STATE.md`.

| # | Finding | Class | Where |
|---|---|---|---|
| F8 | Same flag name, opposite semantics: `live_activation_allowed=false` *disables a rejection gate* on the V4 path (`permissions.py:930` returns None) but *suppresses placement* on the book path (bridge shadow). One vocabulary, two contradictory meanings | AUTHORITY | §2 F1/F3 |
| F9 | The VPS's current live brake (`ultimate_book_live_broker_authority`) is a mechanism HEAD neither reads nor defines | AUTHORITY | F4 |
| F10 | HEAD book composition (`include_clean3: false`, candidate-book 9 + market-expansion 12) no longer matches `live_system_of_record.md`'s 11-sleeve description; the sizing sentence there also omits three risk-shrinking factors | AUTHORITY/DOC | §3.3, W7 agent |
| F11 | Sealed-arm coupling channel: package session tokens can rescue off-session candidates (`selector_v4.py:2126-2168`, enabled at `config:790`) — the only sleeve-data path into sealed admission | REPLAY | F1 |
| F12 | SHORT-side live R computation has zero test coverage (`orchestrator.py:10254-10255`); all `actual_r` assertions are LONG | TEST GAP | §3.5 |
| F13 | The 10 red selector tests are a real package-admission defect (`package_execution_fill_probability` → None, `selector_v4.py:4004-4016`) misdiagnosed as LFS damage; hydration fixed only the 11th | CORRECTNESS/PROCESS | §1 |
| F14 | The sealed arm path never persists `ledgers["event"]` — duplicate-drop and kindred diagnostics survive only as summary counters | OBSERVABILITY | §1 U2 |
| F15 | `budget.cost_warning/critical_threshold_usd` have zero consumers — no cumulative-spend kill switch exists despite the $1,800 lesson | OPS | §3.2 |
| F16 | `LIVE_HANDOFF.md` (tracked) carries plaintext account logins against the profiles' own redaction policy | SECURITY | §3.3 |
| F17 | Replay `normalize_row` silently coerces unparseable OHLCV to 0.0 and drops bad-time rows (`v4:4640-4667`); live ingestion has the checks replay lacks | CORRECTNESS | §3.4 |
| F18 | `BookLauncher`'s per-tick brake watches only `RESEARCH_RUNTIME_HALT.flag` + kill flag; the hard-production flag binds one layer deeper | OPS | §3.3 |
| F19 | `fn_smoke_trade.py` bypasses the entire guard stack via raw `MetaTrader5` import; delete or gate it | OPS | §1 H6 |
| F20 | The canonical export archive is iCloud-evicted (53/96 April-bound files dataless); sealed bundles are insulated by their byte copies, new pack builds are not | DATA/OPS | §3.4 |
| F21 | `broker_order_lifecycle_capture_v4` — named by R28 as the natural broker-truth source — has never captured a row anywhere | DATA | §3.4 |
| F22 | Typed source cache duplicates ×2 by bundle-identity keying (192 = 96×2 entries); tick shards duplicate per overlapping window | PERF | §3.4 |
| F23 | The LOW deletion tier, as constructed, would delete `book_owner.py`/`launcher.py`/`learning_actuator.py`/`learned_edge_walkforward_gate.py` — the live surface and the vision's gate — because their only in-repo consumers are tests the tier also deletes | CLEANUP HAZARD | §5.4 |
| F24 | The prior audit's Python universe excluded 1.01 M tracked lines (43 %) — sparse-checkout blindness; all "% of repo" figures were computed against the working set | METHOD | §5.4 |
| F25 | 12 files carry UTF-8 BOMs that silently break `ast.parse` tooling, incl. two live-path modules | TOOLING | §5.4 |
| F26 | The sealed engine imports research-route modules at module level via `sys.path.insert` (`attempt5:47-57`) — CORE reaches outside `src/`+`scripts/`, and research-tree reorganisation can break the replay entrypoint | ARCH | §5.4 |
| F27 | The decision contract binds 44 paths (33 py + 3 YAML + 6 JSON + 2 JSONL), not 42; H1 guidance should say 44 | DOC | §5.4 |
| F28 | HEAD is a history graft: the engine's formative 1,006 June commits live only in the iCloud legacy repo (cutover 2026-07-12, `migration/atomic-cutover-20260712T192309Z.json` + 339 MB dirty patch); blame/bisect on HEAD is blind for the core and no context doc says so | AUTHORITY/METHOD | §3.6 |

---

## 3. The layers the first audit never examined

### 3.1 The learning stack — repair-then-connect, not rebuild

*(Learning-stack agent, full evidence in `AUDIT_STATE.md`; spot-checks by the lead.)*

What exists and its quality:

- **Dataset builder** (`learned_edge_dataset_builder.py`, 770 L): one row per **candidate** (not per
  trade) — selected, risk-rejected, and selector-missed candidates all become labeled rows via the
  oracle/missed counterfactual paths. This directly attacks selection bias, and it means one
  arm-month supplies **thousands** of training rows, not 72 — every prior discussion (including the
  successor brief) understated the data supply by ~2 orders of magnitude. 43-name feature whitelist +
  forbidden-token guard; truth-tier × duplicate-group weighting; sealed-partition refusal.
- **Trainer** (719 L): three heads — P(fill) and P(target|fill) as L2 logistic (C=0.5), E[netR|fill]
  as Ridge (α=5) on winsorized labels; day-blocked CV; OOF empirical-Bayes categorical encodings;
  beta calibration on OOF only; a **leakage canary that refuses to emit an artifact** if shuffled
  labels stay predictable; frozen-coefficient JSON artifacts (runtime needs no sklearn), 14-day
  expiry, generator-code SHA pin, scorer round-trip parity check.
- **Walk-forward gate** (570 L): seven mechanical gates, of which the decisive one compares
  learned-admitted net-R against **the exact production admission floors** (p ≥ 0.58, EV ≥ 0.10 =
  `config:805-810`) with an anti-mimicry overlap cap (< 0.80) — a pass is directly a
  beats-production claim. Fails closed on degenerate inputs.
- **Runtime scorer + selector integration**: fail-closed refusals (schema/SHA/staleness/missing
  features); learned p/E[netR]/p_fill replace the heuristic floors inside the already-live
  calibrated-admission guard (`selector_v4.py:2662-2681`); **learned sizing**
  (`selector_v4.py:4936-4967`) is a continuous risk multiplier — a third, continuous sizing-policy
  family for exactly the question B7.5 answers with binary arms.
- **Book lane**: `runtime_learning_packet` capture is config-**enabled** (`config:1253-1255`) and
  waiting on the live cycle; `learning_actuator.rerate_book` → owner-armed confidence-tilt map is
  fully implemented with a 1.25 tilt bound and 0.0-drop semantics; only the evidence *producer* for
  the map is missing (~1 day of work against the B7.5 per-sleeve splits).

What is broken, precisely: (1) no producer emits the builder's expected per-day ledger naming; (2)
the B7.5 arms dropped the candidate-microscope anchor ledger entirely; (3) `predecision_features` and
five sibling fields are computed in-process and **not emitted** — labels are recoverable from current
ledgers by an adapter, features are not; (4) the partition-registry file
(`ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl`) exists nowhere, and without it the trainer raises; (5) two
real statistical flaws — numeric preprocessing specs computed on the full frame (OOF optimism), and
no purge/embargo for the ~48 h label horizon (acknowledged in-code, unenforced); (6) one train/serve
skew — `n_competing_in_group` trained on true counts but never populated at runtime.

**Assessment.** Keep the trainer/gate/scorer/integration as-is; rebuild only the capture/adapter
layer on typed events — which is the same work the performance problem demands (F5). wave4b/wave4c
"stores" are one-shot June-5 forensic materializations hardcoded to a 15,679-row universe: keep as
sealed evidence, do not extend. The prior `TARGET_ARCHITECTURE.md` proposal to "build feature and
label stores" stands, amended: the stores' *contract* should be the learned-edge lane's whitelist +
label vocabulary, and the lane above the builder should be reused, not rebuilt.

### 3.2 AI companion / repair / command center

*(Companion agent.)* Three truths: (1) the deterministic protective companion exists and is good —
on the wrong branch (F6); (2) the "autonomous repair companion" of the vision was **operator-launched
agent sessions hot-patching live trading code between ticks** (35-event repair ledger May 28; 55
repair rows June 2, fleet hot-reloaded with 22 open positions), and the post-mortem's own conclusion
is that this polished infrastructure while the economics failed — do not revive in that form; (3) the
command center never existed as a product: `dashboard.py` (FastAPI, 503 L) has only a test consumer;
what ran was a CLI + write-only Telegram. ~70 % of the vision's dashboard items already have a ledger
feed. The right build is a `gtos status` report-pack CLI over existing JSONL, not a web app.
LLM-in-the-loop: three call sites, all Model-A era, triple-neutralized; `run_book.py` has zero LLM
references; the $1,800 billing-leak lesson produced real cost-control rails
(`ai_call_policy`, purpose gating, $5 caps) — but the `budget.cost_*_threshold_usd` keys have **zero
consumers** (config fiction, F15).

### 3.3 Execution boundary

*(Execution agent; §2's F2-F4 carry the headlines.)* The definitive halt-surface table is in the
agent report (preserved in `AUDIT_STATE.md`); the residual facts worth stating: `RealMT5.order_send`
is a pure pass-through; the SL/TP modify paths bypass `safe_place_order` by design with their own
conditional guards (current line anchors `:9744/:9785/:9894/:9935`); `BookLauncher`'s per-tick brake
watches only `RESEARCH_RUNTIME_HALT.flag` + kill flag (`launcher.py:36-37`) — the hard-production
flag binds one layer deeper at `open_trade`; the identity assert is fail-closed on mismatch and
fail-open only when a profile carries no contract (all three live profiles carry contracts);
single-instance guards are Windows-only with a psutil-or-allow POSIX fallback; `mt5_ea/` is a
display-only chart EA (zero order calls) — the EA channel is eliminated as an execution concern.
Security note: `/repo`'s tracked `LIVE_HANDOFF.md` carries **plaintext account logins** despite the
profiles' redaction policy.

### 3.4 Data layer

*(Data-layer agent; F7 above carries the headline. Full inventory preserved in the agent report.)*

- **Coverage vs the vision's "years × 24 symbols":** bars are nominally sufficient (D1/H4 2014→2026;
  M15 2014→2026; M1 monthly 2024-01→2026-06 for the 24-symbol surface, crypto M1 starting later) —
  but the canonical export archive lives on **iCloud Drive and is mostly evicted** to dataless
  placeholders [MEASURED via `stat` flags], including **53 of the 96 files bound by the current April
  bundle**. Sealed months are immune (bundles carry their own 98 MB byte copies — a design decision
  that accidentally insulated the campaign), but building new packs or re-sealing depends on iCloud
  re-materialisation. **Ordered tick truth exists for 4 of 24 symbols × 7 months** (XAUUSD, XAGUSD,
  USDJPY, EURUSD, 2025-10→2026-04, 11.8 GB, self-declared `ordered_price_path_only`,
  FTMO-not-redacted_account); the other 20 symbols have **12 days** of ticks. Any fill/microstructure model
  today trains on ~17 % of the surface. Full 2-year tick backfill ≈ 290 GB raw; whether FTMO serves
  ticks deeper than 2025-10 is unknown (the availability probes are evicted).
- **R20 confirmed line-by-line and sharpened:** five bar materialisations / four tick
  materialisations verified at their exact sites; warm typed-cache hits still pay per-row dict
  construction *plus a canonical-JSON re-hash of every row on every load*
  (`integrated_source.py:432-445`); the typed cache is duplicated exactly ×2 by bundle-identity
  keying (192 = 96 × 2 entries [MEASURED]); tick shards duplicate per overlapping window variant
  (2.9 GB). Measured object sizes: bar dict 873 B vs 48 B fixed-width (18×); tick dict 1,075 B.
  A per-(symbol,day) mmapped columnar layer with the existing payload-SHA integrity keeps every
  guarantee the copies protect and cuts the data-layer resident set **~10× (≈3–4 GB → ≈300 MB)**
  [INFERRED, arithmetic in the agent report] — ~~the enabling step for four-arm parallelism (E8)~~.

  > **AMENDED 2026-07-27 by the §6.3 correction sweep — the description is right, the inference is
  > refuted.** R20's five-bar/four-tick materialisations are real; the "≈3–4 GB of data-layer resident
  > set, whose removal enables four-arm parallelism" inference is not. Session G built the layer, killed
  > the copies (8.4× at the partition boundary, output identity proven over 1.78 M rows) and **arm peak
  > RSS did not fall** — 7.716 → 7.986 GB, +3.5 % (B84). `THIRD_REVIEW.md` §A1 then measured the arm's
  > heap directly: the **source layer is 99 MB, 1.6 % of the high-water heap**, not 3–4 GB; 60.6 %
  > (3,866 MB) is the monolith's per-day row/attribution accumulation. **No source-layer work of any
  > kind can move the arm peak**, so this is not the enabling step for anything. See §5.3's banner.
- **Forward truth is thin and one channel is empty:** `slippage.jsonl` = 192 fills
  (2026-04-28→06-03, adverse-positive convention); `pending_limit_lifecycle.jsonl` = 877 rows with
  fill/no-fill labels and checked-candle OHLC — a genuine limit-fill calibration set;
  `broker_order_lifecycle_capture_v4.jsonl` — the channel R28 named as the natural broker-truth
  source — **has no data anywhere; it never captured** [MEASURED via direct `.git/lfs/objects`
  reads; `shadow_logs/` is dematerialised from every working tree]. Enough for a first global
  slippage distribution + asset-class buckets replacing the flat `0.02 R` constant
  (`config:740`); not enough for per-symbol × session cells. redacted_account-native tick capture ran for
  exactly **2 days** before the halt.
- **Replay-side silent coercion:** `normalize_row` coerces unparseable OHLCV to `0.0` and drops
  bad-time rows silently (`v4:4640-4667`); the live ingestion layer has the sanity checks the replay
  layer lacks (`data_ingestion.py:436-446`). Same fail-open class as R33, on the data path.
- **Quarantine machinery works** — and has only ever caught the 2026-06-02 halt-morning OOM
  artifacts ("Unable to allocate…" parquets), which ties the data layer back to H3: the memory
  ceiling corrupted capture before it ever hit a replay.

### 3.5 Test and proof quality

*(Test-quality agent; 97/97 of the first audit's own hardening tests pass at HEAD [MEASURED].)*

**Economic mutation sensitivity — the question that matters, answered concretely:**

- **Sign flip in live R computation** (`orchestrator.py:10248-10255 _compute_r`): **caught for LONG**
  — `tests/test_exit_wiring.py:405,:238,:475` carry hand-computed `actual_r` assertions (+0.75,
  +1.6429, −1.0) through the real `_finalize_exit` chain. **Escapes for SHORT** — every `actual_r`
  test is `direction="LONG"`; a SHORT-branch flip (`:10254-10255`) flips no assertion in the repo.
  (New finding F12.)
- **2× sizing error** (`execution.py:9080 _calculate_lots`): **caught on both branches** with
  hand-computed numeric volumes (broker-geometry path asserts 0.39 lots and the 636.0 cash-risk
  intermediate, `tests/test_limit_order_flow.py:1357-1434`; tick-value fallback asserts 0.24; a
  fail-closed test pins `broker_order_calc_profit_required_unavailable`). Sizing is genuinely
  well-tested — a positive surprise contradicting the golden-mirror reputation. Unprotected: profile
  overlay multipliers (the NAS100/US30 divergence) and account-currency conversion.
- **Admit-everything selector**: caught at unit level (86 `decision.action` assertions, 34 reject
  scenarios) — **invisible at live level**, because `permissions.py:655-661/930-937` makes selector
  authority a live no-op regardless (E1c), and no test exercises the gate against live config truth.

**Taxonomy over a 12-file sample:** the "1:1 golden mirror" pattern holds for every large file
sampled (the 63,745-line replay test is ~25k lines of fixture dicts asserting the implementation's
own status-string vocabulary); `inspect.getsource` source-string assertions exist in 3 files and
guard the acceleration runner's internals — the exact antipattern `CLAUDE.md` §6 warns about, sitting
on the crown jewels. Genuine invariants exist and are listed per-file in the agent report
(preserved via `AUDIT_STATE.md`).

**Proof layer:** `verify_b7_5_post_acceleration_arm.py:2-8,:831` confirms by-design byte-only arm
verification ("economic JSON objects are never decoded", `parse_json=False`). The route analyzer
(`analyze_b7_5_selection_sizing_matrix.py`, 3,336 L, zero `src/` imports for its summation) re-sums
economics from ledger rows with identity enforcement — real, and stronger than the first audit
credited — but **no code in the repository recomputes any trade's R from prices**, and the frozen
"independent" denominator verifier it leans on imports ten production modules including the
allocator it checks. The differential-parity harness a rebuild needs is already ~80 % present in
three dead modules: `partial_golden_verifier` (2,008 L, successor-acceptance framing),
`streaming_archive_verifier` (1,353 L, day-shard granularity), and — outside the eight —
`replay_acceleration_task2_semantic_acceptance.py` (row-level, fails closed on unknown differences).
Revival ranking is in the agent report.

### 3.6 Context archaeology and how the complexity accumulated

*(Archaeology agent; all hashes verified against local git including the legacy repository.)*

**The repository's own history is a graft (F28).** HEAD's lineage runs 2026-03-29 → 2026-06-05 →
one bulk snapshot commit `954f5a157` (2026-07-12, 2,845 files) → July. **The entire construction of
the current replay engine — 1,006 June commits — exists only in the iCloud legacy repo**
(`/Users/borr/Documents/gtos/repo/ai-trading-agent-ultimate-convergence-20260619.legacy-v238-…`,
4,621 commits; cutover record `/Users/borr/GTOSActive/migration/atomic-cutover-20260712T192309Z.json`,
plus a 339 MB dirty patch of 30 uncommitted files). `git blame`/`bisect` on HEAD is blind for the
system's core, and no context document mentions this.

**The owner's "patching like crazy" is now quantified.** The 96,047-line monolith was born at 3,718
lines on 2026-06-07 and grew ~92 K lines in 47 days across ~84 commits — **every growth commit
labeled "repair", "fix", or "certify"**; the two largest single commits (+10.5 K, +15.5 K lines) are
both "parity repair" commits. The engine was not designed; it was repaired into existence.

**Three decision-system generations in six weeks, each added beside its predecessor.** V3 was built
default-off (2026-06-02) → hard halt (06-03) → the post-halt forensics *named the failure mode*
("Full V3 was not true live authority… default-off/partially wired surfaces while live diverged") →
V4 was born **two days later, also default-off** (06-05) → the W7 book was vendored beside both ten
days after that (06-14/15), with the packet-fabrication shim introduced in the same wave
(`755f8ebf8`, "Stage 3b — full V4 order route"). The diagnosed failure mode was rebuilt twice within
two weeks of its diagnosis. The default-off gates (`apply_to_execution` 05-18,
`live_activation_allowed` 06-01) were born *with* their components — a deferred decision encoded as
config from day one, never a later safety retrofit; 197 and 40 commits then churned around them.

**Where the effort went.** April = code + tests (829 commits). May = the research/context explosion
(2,708 commits; `.context/` touched in 44 % of them; the 192-module `moonshot_*` layer created in
**three days**, 05-16→05-18, frozen within two weeks). June onward = 76 % of commits touch
`research/operations/` evidence machinery. Meanwhile the learning stack — the charter's stated
destination — was built in **one week** (feature store and label store: one commit each, 06-05;
trainer/gate: 06-10/11) and has zero commits since. The effort distribution mirrors the CPU profile
exactly: the measurement substrate absorbed the system's energy while the destination starved.
vNext was activated as production replacement on 2026-05-27 — one week before the hard halt.

**From the never-read documents, three things that matter:**
1. `pre_lock_final_review.md` (2026-04-05) had already measured that **"the AI adds ~0pp to entry
   WR… the system is profitable because of zone detection and execution rules, not Claude's
   reasoning"** — the de-LLM-ing of GTOS was evidence-driven and pre-dated by a month the
   architecture that removed it; `architecture.md`'s "NO AI — pure Python" Component 2 became the
   whole system while every AI component in that 3,337-line design went extinct.
2. `ai_in_loop_cost_control_research_plan.md` (2026-05-10) is the pivot document — its four separated
   evidence questions and "do not use API calls as the brute-force backtest engine" are the
   intellectual ancestor of the charter's evidence-class ladder, and its AI-delta-audit design
   remains the right experiment if an LLM ever re-enters the loop.
3. The post-halt Wave plan (2026-06-04) scheduled Wave 5 = ML and Wave 6 = learning companion +
   command center. The programme executed Waves 3–4 and stalled; seven weeks later the system is
   still in replay-substrate territory. The capability map (11 layers, not the ~9 the successor
   brief estimated) has exactly one heavily-built layer — the replay/digital twin — and the
   layer-by-layer status table is in the agent report.

Declared gaps of this workstream: `research_current_state.md` (5,749 L) was not read;
`architecture.md` internals were sampled, not exhausted; the learning-stack "enabled then reverted"
search was not run to completion (no such commit was encountered; absence unproven).

---

## 4. Proof-layer verdict

E3/E4/E7 hold as written (§1). The deeper statement stands and is now measured twice: the evidence
machinery attests byte custody, not economic correctness, and its own binding prices any repair at a
campaign re-run. The two questions that decide whether GTOS makes money — *does the measured system
predict the trading system?* and *are the numbers right?* — remain unanswered by ~54,000 lines of
proof code, and this audit adds a third: *is the measured system even the one intended to trade?*
(F1 says no.) The shadow-reducer recommendation from the first audit survives intact and is
scheduled first in the plan; the divergence-matrix recommendation is upgraded — it must state not
just execution-model divergence but **strategy-family divergence**.

## 5. Measurements

### 5.1 Profile re-classification (E5)

Independent taxonomy over the committed 86,945-sample profile
(`opus5-architecture-20260725/receipts/profile_jan01_02_sampled.json`), 95.5 % of wall captured
[MEASURED]:

| Category | share of captured self-time |
|---|---:|
| Serialize (JSON encode/decode, sink, zstd, timestamps) | 26.8 % |
| Canonicalise + hash | 24.5 % |
| Evidence/attribution field builders | 13.9 % |
| ABC `isinstance` dispatch | 7.2 % |
| **Proof-complex total** | **72.4 %** |
| Worker-pool wait (prewarm) | 12.3 % |
| Hydration | ~2 % |
| Residual unclassified | ~12.9 % → mostly evidence-support helpers on inspection |
| **Decision functions (self)** | **0.2 %** |
| **Simulation (self)** | **0.05 %** |

Caveat stated honestly: frame-level self-time attributes helper cost to the helper, not its caller,
so "decision" cumulative cost is higher (the first audit's 8.3 % cumulative for
`evaluate_candidate_v4` is the right number for that framing). Both framings agree on the
conclusion: the replay is an evidence factory containing a small trading simulator.

### 5.2 R8/R9 and U2 closure — see §1 corrections. Zero realised effect on all sealed evidence.

### 5.3 Memory / parallelism ladder (E8)

> **AMENDED 2026-07-27 by the §6.3 correction sweep — E8's parallelism verdict stands, the unit-echo
> sentence below is struck, and the ≤3 GB/arm target is withdrawn rather than re-derived.**
> The claim that the quoted "15.32 GB footprint" is a unit-conversion echo of the 8.61 GB maxrss is
> **wrong**, and it is refuted twice over.
>
> **Arithmetically** (B81): 15.32 / 8.61 = **1.779**, while a GiB→GB conversion is **1.0737** —
> 8.61 GB is 8.019 GiB and 15.32 GB is 14.268 GiB, so neither number is the other restated.
> `/usr/bin/time -l` prints **two different fields**, `maximum resident set size` *and* `peak memory
> footprint`; `CONTINUATION_BRIEF.md:164` records them side by side, and `phys_footprint` counts the
> compressed anonymous pages that have left RSS.
>
> **By measurement** (B83): one `/usr/bin/time -l` invocation on the same fixture emitted **both** —
> maxrss 7,716,159,488 B (7.716 GB) and peak footprint 14,838,312,240 B (14.838 GB), **1.92× apart** —
> with the fixture reproducing exactly (8,812 candidates / 10 orders / 5 trades / 96 scorecard /
> 8,807 missed). One run, two numbers; not one number twice.
>
> **The 8.61 GB is also mis-scoped: it is a two-day fixture, not a month arm.**
> `receipts/bench_baseline_uncontended.json:829` — `maxrss_bytes: 8610004992`, `day: 2026-01-01`,
> `end_day: 2026-01-02`, `arm: S1R1`, `wall_seconds: 603.678`. **No peak-RSS measurement of a full
> month arm exists anywhere on disk**; the month figures quoted around it are wall-clock
> extrapolations.
>
> **The ≤3 GB/arm target in the ladder is withdrawn** (`THIRD_REVIEW.md` §7.2), not re-derived. It
> rested on a causal story — the source layer's 5×-bar / 4×-tick materialisation — that Session G
> refuted by measurement: the copies were killed (8.4× at the partition boundary, arm output proven
> identical over 1.78 M rows) and arm peak RSS **did not fall** (7.716 → 7.986 GB, **+3.5 %**). The
> only banked win was **−9.0 % wall**, free (B84/B85).
>
> **Where the arm's memory actually is** — `THIRD_REVIEW.md` §A1, `tracemalloc` at the Python-heap
> high-water mark of the same sealed 2-day fixture: `v4_timewarp_simulated_live_research_loop.py`'s
> per-day row/attribution accumulation holds **3,866 MB = 60.6 %** of the heap; the **source layer is
> 99 MB = 1.6 %**. The evidence machinery is simultaneously the memory, the CPU and the bytes.
>
> **What survives unchanged:** E8's own verdict — 2-way parallelism is measured to be nearly worthless
> — which §A1's 6.38 GB of live per-day accumulation independently explains.

**E8 CONFIRMED, in precise form: 2-way parallelism is not impossible — it is measured to be nearly
worthless.** The first audit's own contended profile run doubles as the missing two-arm contention
experiment: 1,102.3 s vs 603.7 s uncontended on the same fixture (1.53–1.83× degradation), i.e. net
~1.1–1.3× from a second arm, at swap-thrash risk. Verified: 8.61 GB maxrss from the committed
receipt *[amended: that receipt is a **two-day fixture**, not a month arm — banner above]*;
~~the oft-quoted "15.32 GB footprint" is a **unit-conversion echo of the same measurement**
(14.27 GiB)~~ *[struck — two `/usr/bin/time -l` fields, not one converted; B81/B83]*, and the raw
`/usr/bin/time -l` output behind it was never committed — the one E8 number that could not be
independently re-verified *[amended: B83 re-took both fields from a single invocation, 1.92× apart]*.
Ladder: serial today (16.45 h/window) → contended 2-way
~1.2× (don't) → 48–64 GB RAM ~3.7× with no code change → memory fix (target ~~**≤3 GB/arm**~~
*[withdrawn 2026-07-27 — banner above]*, not the
<4 GB previously stated — 4×4 GB on a 16 GiB machine has no headroom) → 3.7× measured-basis, composing
with the Phase-3 projection work.

### 5.4 Reachability (E9)

Independent re-derivation (own entrypoint enumeration, own AST import graph with CPython-faithful
resolution, git-blob census) [MEASURED]:

- **The denominator was wrong.** Git tracks **3,814 `.py` / 2,347,200 lines**; the prior audit
  counted only the sparse on-disk subset (1,638 / 1,331,833). Against the full repo, operational
  reachability is **~14.8 %**; against the sparse set, **26.1 %** (its numerator missed ~59 K
  reachable lines: the sealed engine `sys.path.insert`s a research route and imports two route
  modules — `attempt5:47-57`, pulling in 47,820 lines — and 12 files carry UTF-8 BOMs that break
  naive `ast.parse`, including two live-path modules). The dead-mass conclusion gets **stronger**:
  ~85 % of tracked Python is operationally unreachable.
- **The robust part:** two independent toolchains' CORE∪CAMPAIGN unions agree within 1.8 %
  (429,205 vs 436,938 lines). The 179-module zero-reachability `moonshot_*` count reproduces
  **exactly**. The boundary between CORE and CAMPAIGN is method-sensitive; the two-thirds-dark
  conclusion is not.
- **The dangerous part: the LOW deletion tier was never materialized as a reviewable list, and as
  constructed it would delete the live trading surface and the ML pipeline.** Hidden-consumer hunt
  over a 12-file sample: 3–4 SAFE outright, 3 SAFE only with coupled test deletion, 3 UNCERTAIN,
  2–3 UNSAFE — including `book_owner.py` (in-repo consumers are 4 tests; its real consumer is
  `run_book.py`, out of repo) and `learned_edge_walkforward_gate.py` (0 non-test importers; its
  accepted evidence sits on the VPS branch and the charter's destination requires it). One
  `moonshot_*` module is one subprocess hop from the live monitoring-maintenance chain and named in
  active config (`agent_config.yaml:2716`).

**E9 verdict: HOLDS qualitatively and is understated against the true denominator; the deletion plan
is NOT executable as specified.** Preconditions added to the plan: vendor `run_book.py` first, exempt
the `ultimate_book` + learning families, materialize each tier as a reviewed manifest, and run the
hidden-consumer sweep (string/subprocess/config/receipt references + VPS-branch consumers) per file.
Also corrected: the decision contract binds **44 paths (33 `.py` + 3 YAML + 6 JSON + 2 JSONL)**, not
"42 source files."

### 5.5 Throughput requirement (E10)

**The "~30×" number has no derivation anywhere in the prior audit** — it reconstructs only as
"re-replay two full years overnight" (32.9×), a scenario the charter itself argues against
(`GTOS_ULTRA_GOAL.md:33`: one finite historical challenge, then **forward shadow**, not rolling
retrospective holdouts). Re-derived from verified baselines (dense day 507.6 s; 4.11 h/arm-month;
16.45 h/window; single-threaded confirmed):

| Scenario | Today | Needed | Composed levers reach? |
|---|---:|---:|---|
| Finish B7.5 (12 arm-months) | 49.3 h ≈ 2.05 days | 1× | already affordable; 13.4 h at 3.7× |
| 2-yr × 24-sym × 4-arm sweep | 16.5 days | 8–16× (in 1–2 days) / 32.9× (overnight) | **yes** for 1–2 days; no overnight |
| Nightly loop, incremental day | ~0.7 h | 1× | **fits today** |
| Nightly loop, 6-mo re-replay on policy change | 98.7 h | ~10× | **yes** (4–7.8 h composed) |
| 20-variant × 6-mo search | 20.5 days | 10.3× (weekend) / 49× (overnight) | weekend **yes** |

**E10 verdict: the number is high by ~2×; the conclusion survives in weakened form.** The defensible
requirement band is **~10–16×**. Micro-optimisation (~1.2–1.3×) reaches none of it — that half of
E10 stands. But the band is reached by the two structural fixes already scoped (memory/materialisation
+ evidence-as-projection) plus arm parallelism — so the honest framing is **"two targeted structural
fixes vs micro-optimisation,"** not "total rebuild vs optimisation." The rebuild case in this audit
rests on F1 (policy-plural core so replay measures what trades) and F5/F7 (capture layer and clock),
with throughput as a co-benefit — not on a 30× wall. Caveats carried: the separate `build-pack`
process has still never been timed (U4 stays open), and 2-year *tick-realistic* sweeps also gate on
data coverage (§3.4).

---

## 6. What this means — the strategic read

1. **The owner's instinct was right twice over.** The system is a museum of default-off capability
   (first audit's finding, confirmed everywhere this audit looked), *and* the deepest instance is not
   a patch but a fork: the live system and the measured system separated in June and nobody chose.
2. **The single highest-value decision available is not code.** It is the owner explicitly choosing
   the activation-bearing policy surface (the W7 book, on current evidence) and the role of the broad
   stack (research incubator feeding challengers through the learned-edge gate). Every subsequent
   build step gets simpler once that is chosen. The plan (`FULL_VISION_PLAN.md`) is written to make
   both choices executable, with the book as the default recommendation *because the evidence says
   so*: forward-validated positive sleeves vs −0.25R/fill native plus four negative January cells.
3. **The rebuild's decision core must be policy-plural.** One core, three ports (Clock/Broker/Sink),
   *N* policy modules (sleeve book, broad V4, learned-edge-augmented variants) — so that "replay
   measures the thing that trades" becomes true by construction for any owner choice, and E1 can
   never reopen.
4. **The learning loop is closer than anyone recorded** — but it points at the broad stack today.
   Its first production use should be the cheap one: the book-lane rerate producer (evidence →
   sleeve-confidence tilts, owner-armed), then the full candidate-level lane on the new capture
   layer.
5. **Proof spending gets a budget.** The charter's own rule — a verifier earns its place by naming
   the decision it changes — becomes a gate in the plan: every retained receipt/verifier names its
   decision or is deleted with the LOW tier.
6. **On the mission's one deferral** (whether the economic weights and selection criteria are
   themselves optimal): the deferral still makes sense, with one amendment. Hand-optimising criteria
   from outcomes remains out of scope and correctly so. But F1 shows the urgent question was never
   *tuning* criteria — it is *which criteria family* is the activation candidate, and that is OD-1
   in the plan. Once the walk-forward gate is live (Phase 4), criteria stop being hand-argued at
   all: challengers beat the incumbent through a sealed gate or they don't ship. That mechanism, not
   an optimisation pass, is the honest resolution of the deferred question.

*(Sections marked PENDING will be completed in this session as the remaining agent reports land;
the plan document is written against the completed picture.)*
