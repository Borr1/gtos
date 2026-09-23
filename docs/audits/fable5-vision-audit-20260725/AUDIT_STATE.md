# Fable-5 Second Independent Audit — Live State

**Worktree:** `/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725`
**Branch:** `audit/claude-opus5-architecture-20260725` (continuing after the Opus-5 audit's five commits)
**Auditor:** Fable 5 (second independent auditor per `FABLE_SUCCESSOR_BRIEF.md`)
**Started:** 2026-07-25

---

## Status: IN PROGRESS — fleet running, own measurements landing

## Phase plan

1. ~~Preflight + full absorption of prior audit (all 12 deliverables read firsthand)~~ DONE
2. Adversarial verification of E1–E10 + five never-examined layers — **8 parallel agents running**:
   E1 keystone attack · learning stack · companion/command center · execution boundary + run_book ·
   data layer · context/git archaeology · test/proof quality · reachability + 30× re-derivation ·
   W7 ultimate_book live-surface truth
3. Own measurements (see below)
4. Deliverables: `SECOND_AUDIT.md` (verdicts + new findings), `FULL_VISION_PLAN.md` (sequenced,
   gated, executable by another agent), receipts
5. Scoped commits

## Measured results so far (Fable, this session)

| Thread | Result | Evidence |
|---|---|---|
| **U3 closed** | `scheduler_v4_best_trade_allocator_dynamic_daily_drawdown_budget_enabled: true` in contract-bound base config (`config/agent_config.yaml:982`); arm runner never overrides it (only the R0 branch disables the *quality-gate* sub-flag, `attempt5:11971-11982`). So R8's mechanism is **armed in all four sealed arms** — the register's "key not in config, runner-supplied" is wrong on that point. BUT: scanned all 662 order rows across the four sealed January arms — `requested_risk_pct == final_approved_risk_pct` on every row; min `daily_runtime_headroom_pct_before` = 1.555 (R1 arms) vs 4.0 cap. **R8/R9 never bound in sealed January evidence: zero size changes, zero trade changes.** | scan over `PHASE_D_JANUARY_*` order ledgers in owner worktree (read-only) |
| **U2 closed** | `duplicate_exact_candidate_instance` drops: **0** in all four sealed arms (summary counter `candidate_duplicate_profile_scoped_instance_rows = 0` ×4; 0 string matches in all four cold decision ledgers; 0 in the 2-day local run, 5,647/5,647 decision rows `materialized`). R17 severity drops accordingly. **Side-finding:** the sealed arm path never persists `ledgers["event"]` (the event ledger role exists only on the legacy `build_route` path, `v4:95046`), so duplicate-drop *events* would be invisible except via the summary counter. | same + `audit_runs/benchmark_output` |
| **E5 re-verified & sharpened** | Independent re-classification of the committed 86,945-sample profile with a stricter taxonomy: **proof-complex (evidence-field builders + canonicalise/hash + JSON/sink serialize + ABC type-dispatch) = 72.4 % of captured self-time**; prior audit's 60.6 % is a defensible lower bound. Pure decision self-time **0.2 %**, simulation **0.05 %**, hydration ~2 %, pool-wait 12.3 %. (The prior "8.3 %" was `evaluate_candidate_v4` *cumulative*, which itself contains evidence work.) | `receipts/profile_jan01_02_sampled.json` re-analysis |

## Load-bearing new insight (to be confirmed by W7 + E1 agents)

**GTOS contains two competing live-candidate decision stacks with disjoint evidence chains.**

- Stack A — broad V4 surface: 24-symbol candidate generators → Selector V4 → Scheduler V4 →
  continuous sizing; measured by the sealed replay campaign (B7.5). The go-live dossier
  (`git show 86cccd08d:research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_GO_LIVE_DOSSIER.md`)
  states its native live result: **−0.25R/fill, "must be DISABLED"** at go-live.
- Stack B — W7 `ultimate_book`: 11 statistical sleeves (crypto, metals_core, energy_agri,
  sub_xvol_pullback, fx_jpy, vp_euidx_pocgrav, …), TRAIN ≤2024 / FWD 2025-26 validated by its own
  locked engine (`INTEG_W7_FINAL_RESULT.json`), Kelly-lite conviction sizing, dial ladder
  1.25 % → 1.50 % → 2.00 %. Declared the live model by `live_system_of_record.md` (2026-06-16);
  shadow-gated at HEAD; entrypoint `run_book.py` absent from HEAD (host-local).
- `ultimate_book/bridge.py:28-33` encodes a **replacement invariant**: the bridge fails closed if the
  broad selector is still apply-to-execution when the book is live. The two stacks are mutually
  exclusive by design.
- The B7.5 charter (2026-07-16, newest authority) decomposes selection/sizing **on Stack A** and aims
  to "carry the strongest supported policy to controlled canary readiness" — i.e. the compute-heavy
  sealed campaign measures the stack the June dossier ordered off, while the declared live stack has
  no representation in the sealed replay at all (replay consumes sleeve-registry rows only as
  admission *evidence* via `ultimate_candidate_package`, not as the book engine).

Consequence if it survives verification: the rebuild's decision core must host **both** policy
families behind the same ports, so replay measures whichever policy is actually the activation
candidate — that closes E1 by construction for either owner choice, and turns the "which stack goes
live" question into an explicit owner decision instead of an implicit fork between two documents.

## January factorial economics (Fable direct read — nobody had read the sealed result)

From `B7_5_SELECTION_SIZING_DEVELOPMENT_JANUARY_SOURCE_REPAIRED_R3_CAP_R2_MATRIX_AUDIT.json`
(owner worktree, read-only):

| Arm | scoreable_net_cash | scoreable_accepted_risk_cash | q = net/risk |
|---|---:|---:|---:|
| S0R0 (neutral sel, fixed 0.1 %) | −201.31 | 8,800 | −0.0229 |
| S1R0 (quality sel, fixed) | −550.60 | 7,500 | −0.0734 |
| S0R1 (neutral sel, dynamic) | −5,432.33 | 39,881 | −0.1362 |
| S1R1 (incumbent) | −6,596.06 | 36,778 | −0.1793 |

Primary classification (sealed analyzer): **selection = inconclusive_inside_closed_symmetric_band
(−0.049), sizing = material_negative (−0.1105, crosses the −0.1 sealed threshold), interaction =
non_claimable_positive_with_execution_suppression (+0.007)**. Status:
`PASS_DEVELOPMENT_JANUARY_MATRIX_ADVERSE_DEVELOPMENT_APRIL_AUTHORIZED`.

**Read plainly: every arm lost money in the January development window, and the dynamic-runtime
sizing that mimics the incumbent live-shaped policy is the sealed campaign's own measured value
destroyer.** Combined with the W7 dossier's −0.25R/fill verdict on the broad selector, Stack A keeps
measuring weak-to-negative on its own evidence chain, while Stack B (the book) is the only surface
with positive forward-validated economics. This must shape the vision plan's recommendation.

## E1 keystone attack (agent DONE) — VERDICT: HOLDS, and understates the gap

- E1a HOLDS: no production caller of `evaluate_selector_v4_admission`; run_book.py (VPS, 324 L) imports
  only UltimateBookOwner/bridge/symbol_map/BookLauncher — no selector/scheduler anywhere.
- E1b NARROWED in wording: "unwired at HEAD" → *entrypoint un-vendored; the book package at HEAD is
  current and even 3 modules ahead of the deployed VPS copy*. Book's conviction sort is cap-shedding
  (inert until the 4 % gross cap binds), not best-trade selection. Packet "fabrication" is a
  deliberate post-admission compat shim satisfying `execution_manager_v4_selector_v4_packet_required:
  true` (config:1136) — formal V4 compliance while bypassing V4 authority.
- E1c HOLDS: actually a **quintuple** gate; zero env/profile escapes (no os.environ in selector/
  permissions/scheduler; profiles never touch V4 keys). VPS config is deeper off: SHADOW 2026-07-02,
  `apply_to_execution: false` **plus a 4th gate `ultimate_book_live_broker_authority: false` that
  does not exist at HEAD** — the two branches disagree about the gate set (new finding).
- E1d HOLDS understated: replay never computes a lot quantity at all (`order_size_units_proxy`,
  v4:6494-6499; zero matches for volume_step/min-lot in the replay loop). Contrary evidence noted:
  replay's R-unit cost model is real (tick spread floor, commission, swap).
- Reverse-divergence table delivered (halt semantics, retcodes/requotes, partial fills, margin, lot
  geometry, 48 h vs 120 min pending expiry). Two prior-audit corrections: execution.py:3169-3182
  *refuses* to re-anchor (mislabeled before); replay does model estimated costs.
- Q6 decider: **if the halt flags were removed tomorrow, nothing trades on either surface at HEAD
  config** — the book stops at GATE3 false; the fleet's candidates die at the emv4 packet wall
  (`missing_selector_v4` fatal) because no component on the fleet path produces selector/scheduler
  packets. The live fleet at HEAD is fail-closed end-to-end (new load-bearing finding).
- Two-stacks insight CONFIRMED: the book shares none of replay's four decision layers, not even
  candidate generation (per-(symbol,sleeve) W7 signals vs broader-origin generators; replay imports
  exactly two spread-floor constants from admission.py and never calls admit_and_size).

## Agent reports received

**Companion/Command-Center agent (DONE)** — highlights:
- A real, tested, deterministic AI-companion runtime (2,078 L, `src/components/ai_companion/` +
  supervisor script + PS1) exists **only on the VPS branch**, `enabled: true`, authority `protective`,
  controls bounded to {pause_new_entries, sleeve cooldown, risk_multiplier≤1.0}, TTL ≤120 min,
  fail-closed into pause. Main has neither the module nor the book gate hooks → **a canary launched
  from this repo silently lacks the protective layer the sealed docs describe** (Tier-1; extends E2).
- The vision's "Autonomous Repair Companion" shipped as *operator-launched agent sessions* that
  hot-patched live trading code between ticks (35-event repair ledger May 28; 55 repair rows Jun 2,
  fleet hot-reloaded with 13+9 open positions), gated only by py_compile+pytest. Post-mortem's own
  verdict: repairs real, trading quality not proven (77 trades, −$859.69, WR 40.26%).
- LLM-in-the-loop: exactly 3 call sites (primary_analyzer:667, m5_refinement:555, debate:319), all
  Model-A-era; `run_book.py` (VPS) has **zero** LLM references; debate never wired live despite
  `debate_round2_enabled: true` (dead config). Anthropic-only; $1,800 billing leak drove a
  subscription mode that strips API keys. Budget thresholds `cost_warning/critical_threshold_usd`
  have **zero consumers** — config fiction.
- Command center: `dashboard.py` (FastAPI, 503 L) is test-only; the real practice was a CLI +
  Telegram alerts (write-only, no inbound controls). ~70 % of the vision's dashboard list already has
  a ledger feed; right rebuild is a `gtos status` report-pack CLI, not a web app.
- Cross-check item: `pipeline_state/` **does not exist** in `/Users/borr/GTOSActive/repo` working
  tree per this agent — the halt flags cited in CLAUDE.md may live only on the VPS. Execution agent
  to confirm.

**Learning-stack agent (DONE)** — highlights:
- Two lineages, not one. The **learned-edge lane** (dataset builder 770 L → trainer 719 L → walkforward
  gate 570 L → frozen-artifact scorer 489 L → selector_v4 admission + sizing integration) is the
  best-engineered ML code in the repo: whitelist-only features + forbidden-token guard, day-blocked
  CV, a leakage canary that refuses to emit artifacts, frozen-coefficient JSON (no sklearn at
  runtime), fail-closed refusals everywhere, 772 L of dedicated tests the prior audit missed.
  **Dead at exactly one point: its input.** No producer emits its expected per-day ledger format; the
  B7.5 arms dropped the candidate-microscope ledger; `predecision_features` is computed by the
  generator (broader_origin_generators.py:1929) and discarded at emission. Labels are recoverable by
  an adapter; features need re-emission. Also missing: the partition registry file, without which the
  trainer raises.
- **Not a GBM**: three heads — P(fill), P(target|fill) (L2 logistic, C=0.5), E[netR|fill] (Ridge α=5),
  38 dims, OOF empirical-Bayes categorical encodings, beta calibration on OOF only.
- **Per-candidate counterfactual frame** (selected + risk-rejected + selector-missed all become rows,
  labeled via oracle/missed paths): one month ≈ thousands of rows, not 72 trades — everyone
  (including the prior audit) understated the data supply by ~2 orders of magnitude.
- **The walkforward gate's baseline is the exact production admission floors** (p≥0.58, EV≥0.10 =
  config:805-810) with an anti-mimicry overlap cap (<0.80) — a gate pass is directly a
  beats-production claim.
- **Learned sizing is a continuous third sizing-policy family** (`selector_v4_learned_risk_sizing_enabled`,
  selector_v4.py:4936-4967) — directly relevant to B7.5's binary S/R question.
- Corrections to the prior audit: `learning_actuator.rerate_book` consumption path is **fully
  implemented and config-gated** (bridge.py:283→:410, admission.py:1075-1076,:1162), not "comments
  only"; runtime packet capture is config-ENABLED (agent_config.yaml:1253-1255) — armed, inert only
  because run_book.py/halt; model_pin/model_router are LLM-call infra, misfiled in the ML inventory;
  wave4b/wave4c are one-shot June-5 forensic materializations hardcoded to a 15,679-row universe —
  **dead end as store foundation**, keep as evidence.
- Real statistical flaws: numeric specs computed on the full frame (minor OOF optimism); no
  purge/embargo for the ~48 h label horizon (acknowledged in-code, unenforced).
- Verdict: **(b) repair-then-connect** — rebuild only the capture/adapter layer on typed events
  (exactly the prior TARGET_ARCHITECTURE direction); keep trainer/gate/scorer/integration as-is.
  Gap list of 6 items received (feature re-emission is contract-bound → next contract generation).
- Emission drift orphaned four consumers, not one (three other research modules import the same
  discovery function).

**Execution-boundary agent (DONE)** — highlights:
- **The hard halt has no filesystem existence on this Mac.** `/Users/borr/GTOSActive/repo` is itself a
  sparse checkout; `pipeline_state/` exists in NO local checkout; flags are tracked in git (blob
  records the CEO's 2026-06-03 halt order verbatim) but skip-worktree masked. Halt semantics:
  missing = clear (fail-open), CWD-relative. **Any live-capable process launched from any checkout
  here would report halt CLEAR.** Real brakes: MetaTrader5 python pkg is Windows-only (cannot trade
  from this Mac at all), `live_activation_allowed: false` (HEAD), `live_broker_authority: false`
  (host-local), and whatever flags exist on the VPS filesystem — unverifiable here.
- **run_book.py cannot be vendored as-is**: ImportError (`bridge.config_bool_value` undefined at
  HEAD) + book_owner.py fork: VPS 4,269 L vs HEAD 1,852 L (VPS-only: broker deal/exit reconciliation,
  position protection, realized-P&L joins); HEAD-only: 3 convergence modules + fix P4 (host-local). Vendor task = **two-way package reconciliation**.
- run_book itself checks NO halt flag; BookLauncher's per-tick brake watches only
  RESEARCH_RUNTIME_HALT + kill flag (launcher.py:36-37); GTOS_HARD_PRODUCTION_HALT binds only at the
  inner open_trade guard. Identity assert fail-closed on mismatch, fail-open when profile carries no
  contract (all 3 live profiles do carry contracts). Isolation guards are Windows-only (mutex+msvcrt);
  POSIX fallback degrades to psutil-or-allow.
- fn_smoke_trade.py is WORSE than the register: raw `import MetaTrader5`, bypasses create_mt5/
  RealMT5/every engine guard. mt5_preflight partially repaired since the audit (order now opt-in).
  Follower amendments: transmission also needs `--order-enabled`; open_trade's config-armed guard
  applies — but its flag files are the nonexistent-on-disk ones.
- mt5_ea/ is a display-only chart EA (zero order calls) — eliminated as an execution channel.
- LIVE_HANDOFF.md (tracked, /repo) carries **plaintext account logins** despite the profiles'
  redaction policy — security note for the report.
- Activation truth: execution host is the Windows VPS with pre-logged-in portable terminals
  (connect() passes no credentials). Minimal trustworthy package exists only on the VPS branch
  family; HEAD alone cannot produce one.

**W7 live-surface agent (DONE)** — highlights:
- **HEADLINE: zero shared signal code between the live book and the replay.** Book sleeves are
  stdlib-pure byte-faithful ports of the locked June-10 route (registry of 11 W7 + 9 candidate + 12
  market-expansion sleeves); replay generates via `broader_origin_generators` (10 origin families +
  3 framework families) through V4DecisionCycleCore. Only shared code: the TICK_SPREAD_FLOOR_R
  constants. Name rhymes (vol_compression vs volatility_compression_expansion) are independent
  implementations. **Replay R is evidence about the retired broad-selector system, not about a single
  trade the live book would take. No existing replay harness exercises the book.**
- Same-flag-opposite-semantics finding: `live_activation_allowed=false` DISABLES a rejection gate on
  the V4 path (permissions.py:930 returns None) but SUPPRESSES placement on the book path (bridge
  shadow mode, realized_units=[]). One flag name, two contradictory meanings.
- HEAD config composition differs from live_system_of_record's "clean3 11-sleeve" description:
  `include_clean3: false` (core-8) + candidate book (9 allowlisted) + market-expansion 12 under
  `positive_weighted12_after_swap`. The live doc's sizing sentence omits the ×≤1.75 overlay/Kelly
  cap, ÷n cluster split, and joint daily-limit gross-cap tightening (all risk-shrinking).
- Sizing chains are structurally incompatible in both directions (worked example: fx_jpy ≈0.22 %,
  metals_core ≈1.50 % vs replay's per-candidate dynamic cell risk on a balance basis).
- Book risk machinery: sound, predominantly fail-closed (atomic per-namespace governor state,
  DST-correct day baseline from broker deals, smooth-derisk interlock fails closed, breach-flatten
  2-tick confirm, cap shedding preserves metals_core). Holes are one layer deep, not order-bearing
  today.
- Packet fabrication verified as the finished design (satisfies emv4 field-completeness gates);
  no adapter seam toward the real selector exists or was started.
- R35 re-verified but nuanced: dormant_state.json is orchestrator-path-only → inert for the book;
  the real shared-state list is the default kill flag (brakes BOTH books), the shared flatten flag
  (deliberate), and two shared-append JSONL ledgers disambiguated only by an in-row namespace field.

**Test/proof-quality agent (DONE)** — folded into `SECOND_AUDIT.md` §3.5 + corrections (H2 overturned:
LFS fixed 1/11, the 10 selector failures are a real pre-existing defect `package_execution_fill_probability=None`,
selector_v4.py:4004-4016; E3 nuanced: analyzer re-aggregates but nothing recomputes R from prices;
SHORT-side R untested = F12; sizing genuinely well-tested; parity-harness revival ranking:
partial_golden > streaming_archive > task2_semantic_acceptance). U5 CLOSED (hydration done, 1 test fixed).

**Data-layer agent (DONE after resume)** — folded into `SECOND_AUDIT.md` F7 + §3.4. Headline: the
entire research data layer labels broker time (EET/EEST) as UTC — export writes broker epochs as UTC
(`export_mt5_research_ohlcv.py:541`), replay believes them, live corrects since 2026-04-28
(`mt5_real.py:212-244`); session tables gate hours 2–3 h apart between replay and live; DST seam
inside sealed March. Plus: iCloud eviction of the canonical archive (53/96 April-bound files
dataless); tick truth = 4 symbols × 7 months + 12 days for the rest; broker_order_lifecycle channel
never captured; R20 confirmed line-by-line with a measured ×2 typed-cache duplication; columnar
single-materialisation ⇒ ~10× data-layer memory cut. Plan updated (clock repair, acquisition
workstream, calibration joins).

**Reachability/E10 agent (DONE)** — folded into `SECOND_AUDIT.md` §5.3-5.5 + F23-F27. Headlines:
prior audit's Python denominator missed 1.01 M tracked lines (sparse blindness) — true reachability
~15 % of the full repo (dead-mass case stronger); CORE∪CAMPAIGN unions of two independent toolchains
agree within 1.8 %; the LOW deletion tier was never materialized and would delete book_owner/
launcher/learning_actuator/walkforward_gate (live surface + vision gate); ~30× has no derivation —
honest band ~10–16×, reached by memory fix (≤3 GB/arm) + projection + 3.7× parallelism; E8 confirmed
precisely (2-way measured ~1.2× net from the audit's own contended run; 15.32 GB was a unit echo of
8.61 GB maxrss); contract binds 44 paths not 42; sealed engine imports research-route modules at
module level (attempt5:47-57); 12 BOM files break ast tooling.

**Archaeology agent (DONE)** — folded into `SECOND_AUDIT.md` §3.6 + F28. Headlines: HEAD is a
history graft (1,006 June commits only in the iCloud legacy repo; cutover 2026-07-12); the monolith
grew ~92 K lines in 47 days with every growth commit labeled repair/fix/certify; three decision
generations in six weeks each beside its predecessor, the diagnosed default-off-successor failure
mode rebuilt twice after its own diagnosis; moonshot layer = 192 modules in 3 days, frozen in 2
weeks; learning stack built in one week, zero commits since; April red-team had measured "AI adds
~0pp" before the roadmap projected revenue from AI reasoning; capability map is 11 layers (not ~9),
replay the only heavily-built one; Wave plan stalled at 3–4, Waves 5–6 never reached. Declared gaps:
research_current_state.md unread; enable-revert search incomplete.

## ALL NINE AGENT WORKSTREAMS COMPLETE. Deliverables final.

## Open threads

| # | Thread | State |
|---|---|---|
| U1 | run_book.py audit from VPS branch | agent running |
| U4 | true cold end-to-end cost (derived_cold + build-pack) | still unmeasured; likely stays open (hours of compute) — will state as such |
| F-new | April S1R1 partial (16 days) R8/U2 scan | **DONE: 88 order rows, 0 truncated, min headroom 1.610** — R8 never bound in April partial either |
| F-halt | Where do the halt flags actually exist? | pending execution-boundary agent |

## Artifacts

- This directory: `docs/audits/fable5-vision-audit-20260725/`
- Working scratch under `/private/tmp/...scratchpad` (not committed)
