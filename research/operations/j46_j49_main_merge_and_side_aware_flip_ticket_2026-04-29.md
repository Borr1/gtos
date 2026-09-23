# Production Integration Ticket — J46-J49 Main-Merge + side_aware_sizing.enabled Flip

**Filed:** 2026-04-29 (Phase 2 master synthesis CEO-approved decisions #1 + #2)
**Source:** `research/ml_program/phase_2/MASTER_SYNTHESIS_PHASE_2.md` + memories `project_h_pm04_combined_mc_PASS_j46_clear_to_merge_2026-04-29` + `project_h_pm03_side_aware_everywhere_PARETO_winner_2026-04-29`.
**Status:** AWAITING MAIN-THREAD INTEGRATION
**CEO approval:** 2026-04-29 ("let's go as proposed and recommended, i approve")
**Owner:** Main-thread engineer (next session OR explicit confirmation in this session)

## TL;DR

Two production changes locked by CEO approval:

1. **J46-J49 main-merge from branch `be33522`** at base S79 risk_per_trade_pct=2.0%. H-PM04 cleared (combined P(pass FN) 99.7%/91.7%, P(bust HARD) 0.26-0.54%, p99 MTM-DD 7.12-7.31%, all gates PASS). 
2. **`config/agent_config.yaml` side_aware_sizing.enabled: false → true** (1-line change; profile already correct LONG=0.5x SHORT=1.0x per CEO standardization). H-PM03 cleared (full P(pass) 0.83→0.94, P(bust HARD) 0.150→0.022 PASSES gate, p95 MaxDD 8.91%).

Both at base S79 risk_per_trade_pct=2.0%. Live A/B 30d shadow data accumulation post-flip.

## ⚠️ Why this is filed as a ticket (not auto-executed)

These are PRODUCTION STATE changes affecting live trading on 7 orchestrators. The CEO directionally approved Phase 2 ship sequence, but per CLAUDE.md "Executing actions with care" guidance:
- Git merge to main affects shared system + hard to reverse.
- Config flip affects live trading decisions on 7 instruments × 7 orchestrators.

Filing as a ticket lets the main-thread engineer execute with proper smoke-test discipline. If CEO confirms in this session that I should auto-execute, I will (single confirmation = green-light).

## Pre-flight state check (2026-04-29)

**Git state:**
- Branch `be33522` exists locally: "feat(research): J46-J49 joint position-management policy sweep v2"
- Working tree has 9 modified tracked files + 3 untracked (research artifacts + state files).
- main HEAD recent commits include `310c68c` (news_filter), `67a25e7` (TickSymbolMap), `65ea7dc` (FN paid-challenge).

**Config state:**
- `config/agent_config.yaml` line 84-89 already has `side_aware_sizing` block with correct profile:
  ```yaml
  side_aware_sizing:
    enabled: false             # master flag — default OFF; CEO flips after 30d shadow
    long_multiplier: 0.5       # halve LONG sizing (validated edge driver)
    short_multiplier: 1.0      # SHORT unchanged (no statistical edge to reduce)
    sprt_window_size: 20       # rolling LONG-outcome window (portfolio-level)
    sprt_wr_threshold: 0.50    # auto-disable when LONG WR < this in window
  ```
- Only change needed: `enabled: false` → `enabled: true`.
- Comment text "default OFF; CEO flips after 30d shadow" — comment can be updated to reflect H-PM03 backtest validation, OR left as-is (the H-PM03 backtest is the validation that allows skipping the 30d shadow phase).
- SPRT auto-disable at LONG WR < 0.50 over rolling 20-trade window provides safety net.

## Step 1 — J46-J49 main-merge

### Pre-merge check
```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git log --oneline be33522..main  # should be empty if be33522 is up-to-date with main
git log --oneline main..be33522  # show commits that will be merged
git diff main..be33522 --stat    # show files changed
```

### Recommended merge approach
```bash
# Merge with merge commit (preserves history)
git merge --no-ff be33522 -m "merge: J46-J49 portfolio policy (H-PM04 PASS, base=2.0%)

H-PM04 combined MC verdict (2026-04-29):
- P(pass FN Phase 1): 99.7% (S79-density) / 91.7% (Realistic-density). Both clear >0.90.
- P(bust HARD): 0.26% / 0.54%. Below 2.5pp ceiling.
- p99 MTM-DD: 7.12-7.31%. Below 8% internal cap.
- Combined gives +27pp realistic-density P(pass) lift over S79-only baseline (64.6→91.7%).
- All pre-registered gates PASS at base S79 risk_per_trade_pct=2.0%.

Components per Agent F Shapley decomposition:
- J49 TP1=3.0R: +0.270R [36.4%]
- J46 partial=0%: +0.245R [33.0%]
- J47 immediate-on-TP1 BE: +0.217R [29.3%]
- J48 12-bar time-stop: +0.010R [1.3%] (droppable but kept)

CEO approval: 2026-04-29 (Phase 2 master synthesis decision #1).
Ticket: research/operations/j46_j49_main_merge_and_side_aware_flip_ticket_2026-04-29.md
Authors: H-PM04 (Phase 2 dispatch) + Agent F (mechanism decomposition).

Co-Authored-By: Claude Opus 4.7 (1M context) <redacted@example.com>
"
```

### Post-merge smoke test
```bash
# 1. Verify merge clean
git status
git log --oneline -3

# 2. Run unit tests on J46-J49 trade-management code
pytest tests/ -k "j46 or j47 or j48 or j49 or trade_management or position" -v

# 3. Run canary fixtures
python scripts/canary_test.py --max-fixtures 10

# 4. Restart orchestrators (one at a time)
# Use start_all.bat or restart per-instrument
```

### Rollback procedure (if issue found)
```bash
git revert -m 1 HEAD  # creates a revert commit
# Then restart orchestrators
```

## Step 2 — side_aware_sizing flag flip

### Single-line edit
File: `config/agent_config.yaml`
Line: 85
Change: `enabled: false` → `enabled: true`

Optionally update the comment block (lines 71-83) to reflect H-PM03 backtest verdict:
```yaml
  # ----- Side-aware position sizing (H38 + side_aware_a + H-PM03 PARETO winner) ---------
  # Originally validated H38 + side_aware_a (commit 124de56). Re-validated H-PM03
  # (Phase 2 dispatch 2026-04-29): full P(pass FN) 0.830→0.937 (+10.7pp);
  # P(bust HARD) 0.150→0.022 (PASSES 0.025 gate); H2 XAU P(pass) +18.7pp;
  # p95 MaxDD 8.91%. Pareto-clean winner over alternative variants.
  # ENABLED 2026-04-29 (post H-PM03 PASS + CEO approval) — config-only ship.
  # Live A/B 30d shadow data accumulation continues; SPRT auto-disable still active.
```

### Smoke test
```bash
# 1. Validate yaml parses
python -c "import yaml; yaml.safe_load(open('config/agent_config.yaml'))"

# 2. Validate config load + side_aware effect on a synthetic CANDIDATE
pytest tests/ -k "side_aware or risk_resolution or sprt" -v

# 3. Restart orchestrators
```

### Live monitoring after flip
- Watch `pipeline_state/side_aware_sprt_state.json` for SPRT status.
- Watch `shadow_logs/live_monitor.jsonl` for per-trade sizing decisions (LONG should be 0.5x, SHORT 1.0x).
- If SPRT auto-disables (LONG WR < 0.50 over 20-trade window) → manual reset required.

## Order of operations (recommended)

1. **First:** flip side_aware flag (smaller, lower-risk, tests in 10 min).
2. **Verify:** orchestrator restarts cleanly + first 5-10 trades show correct sizing.
3. **Then:** merge J46-J49 from `be33522` (larger code change, needs full smoke test).
4. **Verify:** orchestrator restarts cleanly + canary fixtures all pass.
5. **Document:** commit messages reference this ticket + CEO approval date.

## Risk controls in place

For J46-J49:
- Existing safety gates (Gate 0 deployment.phase, inverted TP correction, between-KZ pending limit checker, ADR-006 sl_beyond_ob, etc.) all stay active.
- H-PM04's combined-MC validated P(bust HARD) at 0.26-0.54% across 5,000 paths.
- Live A/B 30d shadow standard before full activation.

For side_aware:
- SPRT auto-disable at LONG WR < 0.50 over rolling 20-trade window.
- SPRT state persisted in `pipeline_state/side_aware_sprt_state.json`.
- Manual reset required after auto-disable.
- H-PM03's MC validated P(bust HARD) 0.022 < 0.025 gate.

## CEO confirmation required

Per WF-1 + "Executing actions with care": these production changes need explicit confirmation before execution. CEO has approved DIRECTIONALLY ("let's go as proposed and recommended, i approve"). Two paths:

**Path A — auto-execute now:** if CEO confirms in this session "yes, execute the J46 merge + side_aware flip now," orchestrator will run the bash commands above + edit config + smoke test + commit. (~30 min wallclock.)

**Path B — main-thread next session:** if CEO prefers to handle in a clean session with full attention, this ticket stays as the handoff doc. Main-thread engineer claims at next session start.

Path A is faster and the changes are well-scoped. Path B is safer if there's any concern about live trading impact during the change window.

## CEO-approval status
- 2026-04-29: CEO approved Phase 2 ship sequence (decisions #1 + #2 from Phase 2 MASTER_SYNTHESIS).
- Per WF-1 discipline: production code modification requires CEO approval; this ticket records that approval.

---

*Ticket end. Awaiting CEO confirmation on execution path (auto-execute now OR defer to main-thread next session).*
