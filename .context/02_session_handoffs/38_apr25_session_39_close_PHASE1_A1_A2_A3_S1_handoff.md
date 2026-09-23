# Session 39 close → fresh session — Phase 1 + A1 + A2 + A3 + S1 + pre-Monday-challenge

**Handoff from:** Session 39 close (2026-04-25 UTC, ~8 hours of work)
**Main HEAD at close:** `405a75d` (S1 monthly-decay monitor merged)
**Open decision gate:** CEO picks GO / STAY / Wait on v2-active detector flip for Monday 2026-04-27 paid FTMO $100K challenge.

---

## MANDATORY FIRST ACTIONS (do these before anything else)

1. Read `CLAUDE.md`.
2. Regenerate + read `.context/LIVE_STATE.md`.
3. Read this handoff.
4. Read `research/a2_v2_active_backtest/SYNTHESIS.md` — the Monday detector-flip decision brief.
5. Read `research/phase1_full_extraction/EXTRACTION.md` — why V4-A was DEFERRED + XAUUSD H1/H2 decay finding.
6. Read `research/monthly_decay_monitor/2026-04_report_including_a1.md` — first-run alert status.
7. Read latest memory: `feedback_walk_level_evidence_not_predictive.md` + `feedback_decay_is_ceo_number_one_concern.md`.

---

## What shipped in session 39 (11 merge commits on main)

### Phase 1 research (merged from worktrees)
- `fd50199` — Phase 1 Track A (XAUUSD reverse-engineering, 13,208 M15 walk rows)
- `23d6624` — Phase 1 Track C (sub-session edge map — NULL at n≥20)
- `570a194` — Phase 1 Track D (sniper subset — REJECT + INSUFFICIENT)
- `aa8bcf1` — `PHASE1_SYNTHESIS.md` (5 new findings, 0 new hard gates)

### Infrastructure (merged)
- `b1fcf5c` — A3 trade-record instrumentation v1.1 (`target_ob_touch_count`, `m5_refined`, `realized_R`, etc. on every filled CAND)
- `74f2fec` — MT5 historical data export expanded 7 → 24 instruments (96 CSVs)
- `49ff747` — A1 logger expansion (`h1_opp_ob_touch`, `detector_version_at_eval`, etc.) + 12-slice backtest artifacts
- `7928184` — Phase 1 comprehensive extraction (E1-E12, +7,071 lines)
- `405a75d` — S1 monthly-decay shadow monitor (live from day 1)

### Research artifacts (committed to main)
- `a4048c2` + `878aebc` — A2 v2-active backtest + SYNTHESIS (**HALT auto-verdict, lean-GO rec**)

### CLAUDE.md updates
- `b92703b` — Session 39 extended closure + unresolved items 8-10
- `d670d1d` — Prune sessions 33-36 to one-liner (size discipline)

**Pytest status:** 2043 passed / 5 skipped / 1 xfailed (up from 2042 pre-session-39). Zero regressions.

---

## Key findings (in priority order)

### 1. V4-A prompt nudge DEFERRED (would have hurt us)

Track A walk found touch=0 (fresh OB) primary rate 31.7% vs touch≥2's 2.1% — Bonferroni p ≈ 5e-16. ADR-005 drafted to nudge AI toward touch=0/1.

**BUT A1's comprehensive extraction (E1) joined `candidate_features_log.jsonl` × `all_results.json` for realized R per stratum:**

| Touch | Filled n | WR | Exp R |
|---|---:|---:|---:|
| 1 | 36 | 41.7% | +0.042R |
| 2 | 25 | 52.0% | **+0.300R** |
| ≥3 | 14 | 42.9% | +0.073R |

Point estimates REVERSE the walk prediction. CIs overlap (insufficient evidence), but there's zero evidence V4-A would help and non-trivial signal it would hurt.

**Memory saved:** `feedback_walk_level_evidence_not_predictive.md` — don't translate walk-level pre-trade probability into prompt/gate changes without realized-R validation.

### 2. XAUUSD H1 → H2 2026 WR decay (p=0.006) — highest actionable signal

A1 realized-R under v1 production:
- Jan 45.5% (n=11) / Feb 75.0% (n=20) / **Mar 33.3% (n=15) / Apr 10.0% (n=10)**
- H1 (Jan+Feb) 64.5% n=31 vs H2 (Mar+Apr) 24.0% n=25
- Chi-square p=0.006 (Bonferroni-surviving)

Consistent with CLAUDE.md quarterly decay trend (73→59%). Extends it through April. Drives urgency of the detector decision — **sitting on v1 production Monday = deploying into documented decay.**

### 3. A1 backtest ran v1-era data, not v2 (scope lesson)

A1's default config used `detector_version=v2_shadow` which per `structure_detector_shadow_logger.py:105` routes production through v1. 100% of A1's 1142 logger rows show `mso_h1_structure_direction='bullish'` — the v1 signature. F3 (session 38) used `--detector-version v2` CLI override → 22.8% SHORT CAND share + +0.407R fleet expectancy.

**A1 measures CURRENT production.** For v2 ACTIVE validation we ran A2.

### 4. Anti-pattern classifier does NOT replicate OOS

Track A AUC 0.65 train-test → 0.55 on A1 as held-out sample, Spearman(prob, R) = −0.09 p=0.43. No hard-gate candidate.

### 5. A2 v2-active verdict: HALT (3/4 PASS; LONG WR ambiguity)

Re-ran A1's 12-slice methodology with `--detector-version v2` CLI. **$37.59 of $40 budget.**

| Metric | A2 | F3 | Read |
|---|---:|---:|---|
| Fleet Exp | **+0.333R** | +0.407R | Solid, positive |
| Fleet WR | 53.3% (30 filled) | 56.2% (32) | Comparable |
| XAUUSD SHORT share | **30.8%** | 22.8% | ✓ Better than F3 |
| XAUUSD SHORT WR | 100% (2/2) | 100% (2/2) | Identical |
| XAUUSD LONG WR | 33.3% (n=9) | 45.5% (n=11) | CIs overlap, can't reject F3 |
| **USDJPY fleet** | 57.9% / +0.447R / +8.5R | 57.9% / +0.447R / +8.5R | ✓ **Bit-exact** |
| Fleet MaxDD | 3.0R | n/a | Well below 8R cap |

Pre-registered criteria: 3/4 PASS (Exp, SHORT share, MaxDD). FAIL: Fleet LONG WR 50% < 55% (lands in halt window [45%, 55%]). **CEO decision required.**

---

## Decision gate CEO must resolve (pre-Monday)

From `research/a2_v2_active_backtest/SYNTHESIS.md`:

| Option | Rationale |
|---|---|
| **GO** (my rec) | Flip `detector_version: v2_shadow → v2` Sunday + rolling restart. Buy challenge Monday AM. LONG-WR-watch SPRT: halt if XAUUSD LONG WR drops below 40% on first 20 live trades. |
| STAY | Keep `v2_shadow` (v1 production) Monday. Another week of live v1 data, re-evaluate next weekend. Cost: another week of documented decay. |
| Wait longer | $40 additional backtest on Apr-May sliding window. Marginal value-add. |

**The question awaiting CEO answer:** GO, STAY, or Wait? My analysis says GO EV beats STAY EV because the LONG-WR-watch SPRT catches any real regression ~20 trades in at ~2.5% DD (recoverable). STAY locks in another week of observed 10% April WR. But this is a strategic call, not a math call.

---

## Non-decision items that can proceed in fresh session

### Immediately (no CEO approval needed)

- **Sunday pre-deploy checklist execution** (rolling restart dry-run, canary, E2E verifier)
- **Watchdog monthly-decay hook** — enable after ~1 month live data. Currently wrapped in `if ($false)` per S1 design.
- **Handoff read + verify main HEAD `405a75d` matches LIVE_STATE.md**

### If CEO chose GO

- Monday pre-deploy: change `config/agent_config.yaml` `detector_version: v2_shadow → v2`
- Rolling restart under `--profile ftmo` (new account credentials from CEO's paid challenge)
- Smoke trade via `scripts/fn_smoke_trade.py`
- Update CLAUDE.md unresolved item 4 to note v2 active promoted + LONG-WR-watch SPRT
- Document LONG-WR-watch SPRT as unresolved item 11

### If CEO chose STAY

- No config change Monday
- Collect another week of A3-instrumented v1-production data
- Next Saturday: re-run A2 methodology with post-A3-data for WR comparison
- Keep challenge purchase plan but on v2_shadow config

---

## Open unresolved items in CLAUDE.md

See `CLAUDE.md §What is unresolved`. Items 8, 9, 10 added session 39.
New items likely to add post-session-39:
- 11: A2 HALT verdict + CEO GO/STAY decision (resolve by Sunday evening)
- 12: LONG-WR-watch SPRT gate (if GO chosen)
- 13: Sunday pre-deploy dry-run checklist

---

## Things to NOT do

- Do NOT ship V4-A prompt nudge. Evidence reversed.
- Do NOT ship the anti-pattern classifier as gate. AUC 0.55 OOS.
- Do NOT expand beyond Tier-1 5 instruments Monday. Phase 2a (EURUSD, NAS100, SPX500, AUDUSD, etc.) batch-validates AFTER Monday stabilizes.
- Do NOT modify A1/A2 pre-registered analysis scripts post-hoc (SHA256 guard protects).
- Do NOT flip `detector_version: v2` without CEO explicit GO. Current state is `v2_shadow` = v1 production.

---

## Memory files updated/added session 39

- `feedback_decay_is_ceo_number_one_concern.md` (new)
- `feedback_walk_level_evidence_not_predictive.md` (new — important methodology lesson)

---

## Weekend budget summary

- Session 38 API: ~$45 (F3 backtest + prompt iterations)
- Session 39 API: A1 backtest $30 + A2 backtest $37.59 = ~$68
- Sub-agent dispatches: $0 (Claude Code subscription, not Anthropic API)
- Monthly cap status: ~$113 of $50/mo (CEO explicit authorization for validation sprint)

---

## Agent usage discipline (carried from session 38)

- CLAUDE.md ~34.4k chars (under 35k cut threshold post-prune).
- Sub-agent dispatches inherit CLAUDE.md. Keep briefs tight.
- Long-running Python via `run_in_background: true` Bash per `feedback_long_running_subprocess_pattern.md`.
- Pre-register analysis criteria + SHA256-log the script BEFORE running — A1 + A2 both use this pattern.
- Per `feedback_parallelize_aggressively_tier4.md`: aggressive parallelization for backtests.

---

## Communication pattern CEO prefers

- Brutally honest. No hedged confidence numbers.
- One-sentence plan before dispatch, one-paragraph status after.
- Show diffs before commit for any research-artifact commit.
- Flag discoveries that change the plan IMMEDIATELY.
- Date-stamp relative references (Sunday → 2026-04-26, Monday → 2026-04-27).

---

*Session 39 was the densest research session to date: 11 merges, 5 new memories, 2 backtests, 1 HALT verdict, 1 deferred prompt change, $68 API spend. The weekend work is done; the only remaining pre-Monday item is the CEO GO/STAY decision.*
