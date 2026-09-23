# Lane H — configuration, gates, and owner decisions: what is OFF and why

**Read-only audit, 2026-08-11.** No config byte changed, nothing armed, no token minted, no VPS
contact. Commissioned by the owner: *"Everything in the configuration or the parameters or anything
that needs to be configured or activated or needs my decision — we need to look at them too. And we
see what kind of gates were maybe overprotective, what kind of features were maybe deactivated due to
conservatism and being extra safe and passive."*

Sources: `config/agent_config.yaml` + `config/profiles/*.yaml` in
`worktrees/wave21-full-system-coherence-20260809`; the 2026-07-25 VPS export at
`/Users/borr/GTOSActive/vps-export-20260725/`; **the host's own measured before-state at
2026-08-06 and 2026-08-10** (`phase19/receipts/vps_live_ops_2026080{6,10}/`, reachable on
`origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`); `run_book.py`; `src/`; every
`OD-*` artifact.

Everything below is `[MEASURED]` by direct read unless stamped otherwise. Where the estate never
measured a thing, this document says **unmeasured** and does not guess.

---

## 0. The decision queue — five decisions, ten minutes

Ranked by value × staleness. Each is one line, what it is worth, and what it costs to get wrong.

| # | Decision | Worth | Cost of getting it wrong | Open since |
|---|---|---|---|---|
| **H-1** | **The `significance` gate blocks every exit-geometry improvement the estate has ever measured.** 1,631 gated exit cells over 25 sleeves: **all 25 improve, none admits, and the failing gate at all 25 best cells is `significance`.** Adopt a lower evidentiary bar for **exit geometry on an already-armed sleeve** (where the entry edge is already accepted and the question is only where to take profit)? | Median **+0.249 R/day** per sleeve, range +0.015..+0.771. On **23 of 25** sleeves the best exit geometry is worth **more than eliminating carry entirely**. | Arming a fitted exit. Mitigation: restrict to armed sleeves, publish train/test both sides, keep the entry gate untouched. | 2026-07-30 (12 d) |
| **H-2** | **`sub_xvol_pullback` — armed on both accounts — has a train/test sign inversion nobody has ruled on.** Its train window is **−0.190 / −0.278 R**, its test window **+1.02 / +1.37**. Its frontier exit `target_4R` **REJECTS at all four cost bands** (p 0.0080 vs a 0.002083 rank-1 bar). Keep it armed, size it down, or pull it? | It is 1 of 4 armed sleeves and the highest per-trade gross R in the survivor book (1.30698 on n=90). | Pulling a real edge, or keeping a fitted one. Neither is measured; the inversion is. | 2026-07-30 (12 d) |
| **H-3** | **The live book runs outside the cluster envelope the 2.0 % dial was certified on.** `ultimate_book_one_unit_per_cluster_per_day` is **`false`** in config while `book_owner.py:270` defaults it **`True`** — the config is actively switching a safety envelope off. Restore it, or re-certify the dial without it? | **unmeasured.** Filed as **D-L** on 2026-07-27 with the observation that the book is "operating outside the envelope the 2.0 % dial was certified on"; never answered. | This is a *risk* decision and it is the owner's by definition. Getting it wrong in the loose direction concentrates same-cluster risk on one day at a 2.0 % nominal dial. | 2026-07-27 (15 d) |
| **H-4** | **OD-AI-7 — `--recover-pre-gap-bar` — the only formally-open item of the wave-8 eight.** Recommendation from this lane: **close it as NO.** | The recoverable population is **4.26 %** of 134,027 D1 trades and **6.4 %** of `sub_xvol_pullback` (armed) — but its measured D1 sign is **negative** (**−0.0771 R** against **+0.0117 R** for the reachable population). **The defect is currently saving money.** | Nearly nil to say no. It also was deliberately not carried to the host, so it is doubly inert. | 2026-07-30 (12 d) |
| **H-5** | **OD-BC-1 / OD-BC-2 — the only decisions racing a third party's clock.** Should AI-initiated trading be prohibited on both live terminals, and is a terminal auto-update acceptable on an armed funded host at all? **Live Update cannot be disabled.** | **unmeasured**, and that is the point: *"Deciding after arrival means the default decided it."* | An unattended MetaQuotes build landing on a host holding two funded accounts, with hazard H8 (flatten first, then gate) unrehearsed. | 2026-07-31 (11 d) |

**Also true and worth thirty seconds:** the learning lane (**CO**) never ran — it lapsed unexecuted
by owner direction, its declarations then expired 2026-08-08, and redacted_account's carried vector was
**all ×1.00 anyway**. Either re-commission it or retire it formally; today it is neither armed nor
retired. And **OD-3 — "the activation candidate: composition and dial" — was never answered as OD-3**;
real money was armed under a blanket approval instead, taking OD-4 (the dial) and OD-5 (canary /
account / date) down with it.

---

## 1. What is actually running — the state of record

`[MEASURED]` on the host: gate/config state and argv from `PRESTATE_20260806.txt`; token and
ceremony state from `RESULT_20260810.md`; the CM rollback from commit `4d28676f8` (2026-08-10
13:32Z). This lane made no host contact of its own.

**Live argv, both workers, after the 2026-08-10 CM rollback:**

```
run_book.py --terminal-path <term> --namespace <ns> --profile <p>
            --kill-flag pipeline_state/ULTIMATE_BOOK_KILL_<x>.flag
            --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert
            --spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback
            --poll-seconds 60
```

| | FTMO | redacted_account |
|---|---|---|
| three authority gates | **all `true`** (host `agent_config.yaml:1161-1163`) | **all `true`** |
| `ultimate_book_include_clean3` | **`true`** (host `:1200`) | same file |
| armed sleeves (`--tags`) | 4: `crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert` | the same 4 |
| `--spread-geometry-floor` | **ARMED** on 2 sleeves | **ARMED** on 2 sleeves |
| `--frontier-exits` | **none** — armed as `crypto` by LN on 2026-08-06, **rolled back 2026-08-10** on owner order *"roll it back"* | none, by design |
| `--lane-weights` | **absent from the live argv** — CO lapsed unexecuted | absent |
| activation token | re-minted 2026-08-10 13:02:25Z, **valid to 2026-09-09T13:02Z**, digest `ffe16657feaf` unchanged | re-minted 13:02:33Z, **valid to 2026-09-09**, digest `e184a81d3b1b` unchanged |
| equity at 2026-08-10 12:5xZ | 108,342.47 | 96,229.28 |
| open positions | **0** | **0** |

**Two corrections to the record this lane had to make.** (1) The 2026-08-14 token cliff is
**removed** — Session LR re-minted both on 2026-08-10 and proved them through the engine's own
`order_send` choke point (`534dcf6aa`: live namespace ALLOWED, wrong and undeclared namespaces
both REFUSED, broker `order_check` retcode 0 on both). Capped at `MAX_TOKEN_LIFETIME_HOURS = 720`
(`activation_token.py:85`) — the safety cap was **not** edited to reach the requested date, which
is the right call. **Next re-mint due before 2026-09-09.** (2) The three "composing" ceremonies of
2026-08-02 are **not** the state: **CN executed** (2026-08-06), **CM executed then rolled back**,
**CO lapsed unexecuted**.

**Mainline is not the live tree, and cannot be.** In this repository `agent_config.yaml:1268` is
`live_activation_allowed: false`, `:1288` is `include_clean3: false`, and
`ultimate_book_live_broker_authority` **does not exist as a key at all** (it defaults `False` in
`book_owner.py`). `config/profiles/redacted_account.yaml:11` carries only `apply_to_execution: true` —
mainline has no way to arm redacted_account. The arming lives exclusively in the host's own config bytes.
That is a sound design and should not be "fixed".

---

## 2. The owner-decision surface: `run_book.py`'s eleven switches

This is the honest map of the estate's activation surface. Every one of these is **default-off by
construction and deliberately outside `agent_config.yaml`**, because that file's bytes are hashed
into the activation token's config digest — flipping a feature there would invalidate the token.
The design is good. What follows is which ones are exercised.

| flag | `run_book.py` | live state | classification | what it is worth |
|---|---|---|---|---|
| `--tags` | `:100` | **ARMED**, 4 sleeves | — | the arming mechanism itself |
| `--spread-geometry-floor` | `:157` | **ARMED**, 2 sleeves both accounts | — | REPAIR: `sub_mid_dn_revert` **+0.426 R/day** at mid (p 0.163 → 0.023, beats all 20 random controls); `sub_xvol_pullback` **+0.264** (p 0.012 → 0.0020). Also removes a measured Kelly contamination: 16 account-days, 3 moving the multiplier, worst **+25.2 %** |
| `--frontier-exits` | `:139` | **OFF** (armed 08-06, rolled back 08-10) | **(b) measured ambiguous** | CM's basis **+0.03552 R/day** predates the wave-20 corrected-quote exit re-walk; under the corrected tape the shipped 4R contract is the measured best cell and CM's cell is **unpriced** there. Re-arm gate is explicit: price `stop_1p5x_target_scale` on the corrected-quote walker first. **This rollback is correct.** |
| `--vol-level-tilt` | `:123` | **OFF, never armed** | **(b) measured ambiguous — see §3** | ordering is real (Spearman +0.4073, perm **p 0.00025**, tertile net R/trade **0.512 → 1.111 → 2.124**); the book payoff is **not** (85 % of the +1.119 pp headline was equity-path artifact, by AR's own control; wins 1 band of 4). Net multiplier over the archive is **0.925** — it is a de-risk on average |
| `--recover-pre-gap-bar` | `:112` | **OFF** | **(b) measured negative** | recoverable population is **negative**: −0.0771 R vs +0.0117 R at D1 (OD-AI-7, H-4 above) |
| `--entry-hour` | `:180` | **OFF, never armed** | **(c) unfinished — but inert today** | **RATIFIED 2026-07-30** at broker hour 01; captures 94–98 % of the rollover saving (16.67× spread at hour 00 → 1.33× at hour 01). **Scope is the FX D1 cohort, and none of it is armed**, so the live value today is **zero**. The ratification itself says implementation "rides the next generation re-derivation wave". Correctly parked |
| `--weekend-flat` (+ `--weekend-flatten-before-hours`, `--weekend-entry-embargo-hours`, `--weekend-exempt`, `--weekend-early-close`) | `:204`–`:249` | **OFF** | **(a) not yet due — a compliance interlock, not conservatism** | redacted_account prohibits weekend holding **once funded**; FTMO's captured rules carry no weekend clause. OD-BA-1 resolved by owner word: the rule does not reach 24/7 instruments, so the pre-selected policy is `--weekend-flat` with `crypto` exempt, worth **+0.2197 R/day, +11.7 pp `p_pass`, −78 days**. **It binds the moment redacted_account passes** — and FN sits at 96,229 today, so it is not imminent. **OD-BA-3 (the holiday list) is unanswered**, and its empty case is a measured **2.6 %** of weekend exits aiming at an already-shut market, which under the redacted_account rule is a **breach, not a cost** |
| `--lane-weights` / `--lane-weights-key` | `:101`, `:105` | **OFF on the host** | **(e) lapsed — see §5** | FTMO vector was `crypto` ×1.15 + `mx_btcusd` ×1.15; FN's was **all ×1.00** |
| `--once`, `--kill-flag`, `--poll-seconds` | `:111`, `:108`, `:99` | operational | — | — |

**The launcher divergence is real and is filed as OPEN.** `config/live_armed_set.json`
(`known_divergence_committed_launcher_vs_host`) records it: the committed
`scripts/run_book_supervisor.ps1` is **7,828 B**; the host file is **19,495 B**, with the books
array at `:140` not `:86` and the spread-floor key named `floor` not `spreadFloor`. The committed
launcher also passes `--lane-weights` and `--lane-weights-key`, which the host does not.
`tests/safety/test_armed_set_single_source.py` reconciles the **declaration** against the
**committed** launcher — it cannot see the host. That gap is why FTMO ran `--frontier-exits crypto`
from 08-06 to 08-10 while `live_armed_set.json` declared `frontier_exits: []`. **Do not carry the
committed launcher wholesale to the host; carry individual arguments.**

---

## 3. The conservatism list — off for reasons in category (d) or (e)

These are the free options, and the list is **shorter and more honest than the brief expected**.
Three of the named starting points turned out not to be free options at all, and saying so is the
point of the lane.

### 3.1 Genuine candidates

| item | location | why it is here | worth |
|---|---|---|---|
| **The `significance` gate on exit geometry** | `walkforward/gate.py:1124-1166`, α at `walkforward/options.py:96` | **(d) conservatism with a measurement behind the *other* side.** The gate is one instrument answering a per-day OOS stability question, applied to a per-trade cost-geometry question. All 25 sleeves improve; all 25 fail on this one gate. The estate never asked whether an *exit* change on an *already-armed* sleeve should face the same bar as a new entry edge | **median +0.249 R/day/sleeve**, and on 23 of 25 worth more than zero carry |
| **`ultimate_book_one_unit_per_cluster_per_day: false`** | `agent_config.yaml:1391`; code default is **`True`** at `book_owner.py:270` | **(e) lapsed.** Filed as D-L 2026-07-27, never answered. The config is actively overriding a safe code default | **unmeasured** — ~0.5 session to measure |
| **`gate1.sl_liquidity_cluster_enabled: false`** | `agent_config.yaml:376`, read at `permissions.py:1961` | **(e) forgotten.** The comment is literally *"Ship DISABLED. CEO flips to true after shadow-log review."* The shadow-log review has no artifact anywhere. Its founding evidence is one trade (Apr 16 NY −1R, SL 0.05 pts below an equal_lows pool) | **unmeasured, and n=1.** This is a *research* rejection filter on the legacy `run_agent.py` lineage, **not** the armed `run_book.py` path — so its live value today is **zero**. Listed for completeness, not for action |
| **The `--entry-hour` ratification never reached an implementation wave** | `phase9/OWNER_DECISION_ENTRY_HOUR.md` | **(c)/(e) boundary.** Ratified 2026-07-30; the cohort it governs is still unarmed | **zero today**, real if the FX D1 cohort is ever armed |

### 3.2 Three that look like free options and are not — corrections to the brief

1. **`broad_origin_target_policy_enabled` (default OFF) buys nothing today.** The per-family
   target-RR table at `broader_origin_generators.py:3242-3285` is real, every one of its 13 rows is
   honestly marked `UNCHOSEN`, and the enable key is `:3290`. **But the code's own measurement says
   the decoupling is structural, not yet effective**: every declared target is 1.5, `min_rr` is 1.5
   on mainline and 2.0 in sealed replay, so `min_rr >= declared` **everywhere the estate runs**, the
   floor binds on **100 % of 471,269 emissions**, and arms C and D of the inertness run are the same
   count. Turning it on changes **no number**. It is a governance repair — a risk-dial change can no
   longer silently move eleven exit contracts — and lane p2 separately took the underlying prize
   apart: deleting the fixed target shrinks 23–43 % on the quote-repaired walker, shrinks again at
   M1 resolution, and a **coin-flipped-direction placebo reproduces 71–180 % of what is left**.
   **Classification: (c) unfinished, correctly default-off. Not a free option.**

2. **`ultimate_book_sqrt_n_pooling: false` is advertised as a *"free +6-7pp stress lift"* and the
   live key cannot deliver it.** `[MEASURED by call-graph]`: `pool_same_day_sleeve_R`
   (`admission.py:114`) has **zero production callers** — the only other reference in `src/` is its
   own docstring at `:1120`. In the live sizing path, `sqrt_n_pooling=True` with n>1 does exactly
   one thing: append the string `f"sqrtN_pool_n{n}"` to a reason tuple (`admission.py:1259-1262`).
   `unit_risk` and `per_trade` are untouched — the code comment says so explicitly ("worst-case-stop
   risk is UNCHANGED... we only RECORD the active EV-credit pooling convention"). The +6–7 pp is a
   claim about a **research MC pooling convention**, not about live sizing.
   **Classification: (e) stale comment on (c) unfinished wiring. Flipping it changes no size.**
   The config comment should be corrected before it costs someone an afternoon.

3. **`wave21_full_flow_truth_mode_enabled` (default OFF) is an *honesty* guard, and off is the
   looser state.** `research_infra/wave21_full_flow_truth.py:64` requires an explicit `True`; when
   on, it **strips** probability/EV authority fail-closed. The measurement behind it is decisive —
   the debate-engine score is outcome-uninformative (**AUC 0.496**, predicted 0.783 vs observed
   0.250 target rate, Platt unrescuable). **Off means the offline full-flow path still permits
   probability claims the estate has measured to be worthless.** This is the one flag in the
   inventory whose *default should arguably flip*, and flipping it makes the system **more**
   conservative, not less. It touches no live book.

---

## 4. The overprotective-gate list

Distinguishing overprotective from protective, ruthlessly.

| gate | verdict | evidence |
|---|---|---|
| **`significance` at α = 0.10 applied uniformly to entry edges and exit geometry** | **OVERPROTECTIVE for exits on armed sleeves.** It is the correct bar for admitting a new edge; it is the wrong instrument for choosing where an already-accepted edge takes profit | 25/25 best exit cells fail on this and only this. `SESSION_AD_EXIT_REPAIR_RESULT.md:11` |
| **α = 0.20 disqualified for arming** | **CORRECT, keep.** `options.py:112-115` says it in its own author note: *"A pass here means 'worth spending more data on', never 'worth arming'. Do not let a C-pass reach a book."* The ratified rule is α = 0.10 (`options.py:96`, `BALANCED`) on `CANDIDATE_BOOK_V1` | ratified 2026-07-30, pinned by `tests/research_infra/test_candidate_family.py` |
| **`declared_family_size` multiplicity bill** | **PARTLY OVERPROTECTIVE, already half-repaired.** The historical 69-look family **double-counted** — W's and X's looks are subsets of AA's 32 — so published q-values were over-corrected. The declared family (`CANDIDATE_FAMILY_V1.json`) fixed that. What remains has no principled stopping rule | at ≤31 looks `mx_btcusd` admits under BH α=0.20; at ≤8 under Bonferroni α=0.05 |
| **Activation token** | **PROTECTIVE — do not touch.** Presence-of-authorization, not absence-of-halt. Risk-reducing requests (closes, partial closes, pending cancels, stop tightenings) pass **without** a token, so it can never strand a position. `MAX_TOKEN_LIFETIME_HOURS = 720` correctly refused an 840 h request on 2026-08-10 | `activation_token.py:85`, `:408-411` |
| **Lane-weights all-or-neutral fail-closed** | **PROTECTIVE — do not touch.** Any missing/stale/malformed/mis-scoped/badly-signed file yields a complete ×1.00 vector, never a partial one; non-neutral vectors admit only in the first 5 minutes of their effective day, then latch. That is the B365-class guard against an intraday sizing jump | `lane_weights.py:1-17`, `:372-374`, `:423-427` |
| **`--tags` / `--frontier-exits` / `--spread-geometry-floor` refusing an empty string** | **PROTECTIVE — do not touch.** `--tags ""` is falsy at `run_book.py:383` and silently means **all BUILT sleeves** (fail-open). The three newer flags each **refuse** an empty string rather than repeat that bug, and refuse an unknown sleeve rather than dropping it | `run_book.py:139-179` |
| **`--weekend-flat` refusing to start when the broker clock cannot resolve** | **PROTECTIVE — do not touch.** `broker_clock.py` was **absent** from the live host at the 2026-07-26 export; a compliance guard that degrades to "no weekend is due" is a funded account holding through one while every log reads healthy | `run_book.py:204-224` |
| **`heartbeat.flatten_enabled: false`** | **LEAVE OFF.** `(e)` by label — the comment reads *"RESEARCH_RUNTIME_HALT 2026-05-18"*, an event 12 weeks stale — but this is an **auto-flatten on missed heartbeats** on the `run_agent.py` lineage, not the `run_book.py` path, and `heartbeat_monitor.py:739` is a raw `order_send` gated by the halt only. Arming an unrehearsed auto-flatten on a funded host is not a conservatism repair | `agent_config.yaml:4317`, `heartbeat_monitor.py:944`, `:1016` |

---

## 5. The expired / stale list

| item | expiry | status today (2026-08-11) |
|---|---|---|
| **CO learning-lane declarations** — FTMO `crypto` ×1.15 + `mx_btcusd` ×1.15; FN **all ×1.00** | `expires_after_decision_day: 2026-08-08` | **EXPIRED — and never armed in the first place.** The ceremony **lapsed unexecuted by owner direction** (`ops/vps-ceremony-cm-cn-20260806`, commit `530b08b21`: *"the only record anywhere that CO must lapse unexecuted"*). The 2026-08-06 live argv carries no `--lane-weights`. Even had it run, it would have gone neutral on **2026-08-05**, three days before its own expiry: `mx_btcusd` was disarmed that day, `--tags` dropped to 4, and the envelope declares **5** `scope_sleeves` — `lane_weights.py:153-155` requires exact set equality, so the mismatch fail-closes the whole vector. **The learning lane has never influenced a live order.** |
| **Activation tokens** | was 2026-08-14 | **RESOLVED 2026-08-10** → **2026-09-09T13:02Z** both accounts, digests unchanged, proved through the engine's own authorization path. **Next re-mint due before 2026-09-09.** Several committed documents (`CLAUDE.md:858`, `phase17/OD_ALL_IN_20260801.md:34`, `phase8/OWNER_DECISION_QUEUE.md:37`) still state 08-14 |
| **B7.5 campaign resume option** (~36 MH) | "at the first bound-file edit" | **DEAD, twice** — the 2026-07-31 seal break, then CN's authorized `broker_net_cost_engine.py` edit. Priced and accepted at the time |
| **The 2026-08-02 "three composing ceremonies"** as described in `CLAUDE.md` §4 | — | **STALE.** CN executed 08-06; CM executed 08-06 then **rolled back 08-10**; CO lapsed. `CLAUDE.md`'s "After execution FTMO runs 5 tags + frontier `mx,crypto` + lane weights" describes a state that has never existed |
| **`ultimate_book_sqrt_n_pooling`'s *"free +6-7pp stress lift"* comment** | — | **STALE and actively misleading** — §3.2 item 2 |
| **`gate1.sl_liquidity_cluster_enabled`'s "CEO flips to true after shadow-log review"** | — | **STALE** — no shadow-log review artifact exists |
| **`ultimate_book_account_A_enabled` / `_B_enabled`** (`:1345-1346`) | — | **VESTIGIAL.** Both `false`; `two_account_balanced: true` is the live model. Harmless, but they read as unexercised capability and are not |
| **The 2026-07-25 VPS export as a statement of live gates** | — | **STALE by design.** It shows `apply_to_execution: false` / `live_activation_allowed: false` / `live_broker_authority: false` at `:1161-1163` — captured **four days before** the 2026-07-29 arming. Use the 08-06/08-10 prestates instead |

---

## 6. Full owner-decision inventory

36 distinct `OD-*` identifiers exist, plus two parallel letter series (`D-A…D-M` from 2026-07-27,
`D-1…D-5` from phase 19). Consolidated status:

**DECIDED and executed (11):** OD-2 (contract split, zero re-seals owed) · OD-AI-1 (`CANDIDATE_BOOK_V1`,
all-declared, α 0.10) · OD-AI-2 (redacted_account armed) · OD-AI-4 (recost V2 beside V1) · OD-AI-5 (registry
weight stays 0.025) · OD-AI-6 (no separate challenge track) · OD-AI-8 (signed peer transfer, coverage
85.5 % → 100 %) · OD-BA-0 / OD-BA-1 (owner word, crypto exempt) · OD-ALL-IN · OD-HISTORICAL-FIRST ·
the training-lane ratification · the H-CD-1 seal break · OD-BROAD-FORENSIC 1 & 2.

**OPEN (9):** **OD-AI-7** (pre-gap bar — H-4) · **OD-BA-3** (holiday list; empty case is a measured
2.6 % breach exposure) · **OD-BC-1 / OD-BC-2** (MT5 terminal — H-5) · **OD-J2** (`execution.py:7613-7645`
fallback key names silently return slippage+swap when quote spread is missing — cost quoted as
**"Free — unbound, no re-seal"**, one mention in the entire repo) · **OD-J3** (daily-loss denominator
vs both firms' fixed-cash rule — *"changes live risk gating, so it is yours"*, noted as *"currently
loose in profit"*) · **D-4** (kill/park/iterate the broad family) · **D-1 / OD-FA2-2** (LAND gate, green,
13,304/2/0 vs sealed 12,809/2/0, zero regressions — *"say the word and it lands"*) · **D-5 / OD-FA2-4**
(worktree cleanup, blocked on a 17 GB relocation).

**LAPSED SILENTLY (12+):** OD-3 (**the biggest one — never answered as OD-3**; real money armed under a
blanket approval) · OD-4 (the dial) · OD-5 (canary/account/date) · OD-R1 · D-B (candidate book on/off —
**76.4 %** of the live fortnight's net loss, placebo-failed at p 0.59) · D-C · D-G · D-I (the two accounts
still trade **different books**: 4 metal crosses + DASHUSD/XPD/XTZ/AVA absent from redacted_account, and
**62.4 %** of `metals_core` intents sit outside the W7 validation) · D-J (12 of 29 sleeves take their
risk-bucket day key from the **wall clock, not a bar** — live magnitude unmeasured, ~0.5 session) ·
D-K (the dial) · **D-L** (cluster envelope — H-3) · D-M.

**BUILT, ACCEPTED, NEVER ARMED (3):** OD-P1 / OD-P2 / OD-P3 — packet emit-on-change, the unit join key,
and `modelled_cost_r`. Under OD-ALL-IN's own words, built-but-unarmed is a **defect state**, and these
are the clearest instances. All three were re-priced **downward** after acceptance (OD-P1 76.9 % →
76.05 % → **73.70 %**; OD-P3's filed one-line repair **fails quietly at 6.21× the bytes**, inflating the
very stream OD-P1 exists to shrink). Worth re-reading before arming any of them.

**Two contradictions in the record**, both in `phase8/OWNER_DECISION_QUEUE.md`: OD-AI-3 is recorded as
both **NOT ADDED** (`:81`, `:584`) and **EXECUTED on the live accounts** (`:139`); and OD-AI-1's ratified
basis (`all_declared`, `:104`) contradicts its own recommendation (`looks_taken`, `:270`). Neither
changes what is armed today, but both will mislead the next reader.

**Three owner-grade items from Session LM (2026-08-05) that were never assigned OD identifiers** — the
redacted_account token defect (F1: the token bound the **profile name** instead of the namespace, and the
layer's own audit log records **231 refusals** between 13:00:42Z and 14:59:08Z on 2026-08-04, one
carrying `UKOUSD SELL 0.52`, while FTMO booked **+$493.20** on the sister trade; **repaired 2026-08-06
by Session LO**), exit-provenance mislabelling, and the break-even routine's missing worsening-guard.

---

## 7. Safety interlocks — do not weaken, and this lane does not propose to

Recorded so the conservatism list cannot be misread as a licence: the **activation token** layer
(presence-of-authorization, risk-reducing always passes, 720 h cap), **flatten-before-disarm ordering**
(hazard H8 — `live_broker_authority: false` returns before flattening at `book_owner.py:2364-2373` and
stops routine trade management at `:2526`), the **kill flags** (per-account, `--kill-flag`), the
**all-or-neutral lane-weights envelope** and its 5-minute activation window, the **empty-string refusal**
on the three newer sleeve flags, the **broker-clock refusal-to-start** under `--weekend-flat`, and the
**never-execute list** for every raw `order_send` script. None of these is conservatism. Every one of
them is the thing standing between a bad afternoon and a blown account.

---

## 8. Method and limits

Every live-state claim is sourced to the host's own captured before-state
(`phase19/receipts/vps_live_ops_20260806/PRESTATE_20260806.txt` and
`.../vps_live_ops_20260810/RESULT_20260810.md`), the argv in those captures, or a commit on the host
lineage `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`. **This lane made no VPS
contact**, so the host state is `[MEASURED as of 2026-08-10 13:32Z]`, not as of this minute. Anything
that changed on the host after that commit is outside this document.

Code claims are `file:line` against
`/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809`, which carries uncommitted
wave-21 machinery edits; none of the files cited here is among them.

**What this lane could not settle:** the value of H-1 (the significance question is a standard, not a
measurement — someone has to choose the bar), H-3 (the cluster-envelope magnitude is genuinely
unmeasured, ~0.5 session), D-J (wall-clock day keys, unmeasured, ~0.5 session), and OD-BC-1/2 (a
policy question about a vendor's release schedule).
