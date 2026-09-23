# Merge Plan — Thursday 2026-04-23 Audit Response

**Author:** Claude Code (Opus 4.7, max effort) — consolidated from 8 code-agents (A1-A8) + 8 independent reviewers (V1-V8) + 1 ADR author (F1)
**Date:** 2026-04-24
**Status:** Awaiting CEO decision on each branch
**Branches produced:** 7 code-changing branches + 1 ADR (docs only) + 1 research audit (docs only)

---

## TL;DR

| Phase | Outcome |
|---|---|
| Thursday forensic audit | 2 fills (+$1,260.91), P0 bug + multiple latent bugs + **structural bullish-bias bug confirmed** |
| 8 fix/analysis agents | All delivered; 7 code branches ready for review |
| 8 cold reviewers | 7 APPROVE / APPROVE_WITH_CONCERNS, 1 APPROVE_WITH_CONDITIONS (A5 1 FP on unfilled trade). V1 independently **CONFIRMS** structural bullish bias. |
| ADR-004 | Written; 8 fix options enumerated for CEO decision on market_state bug |
| Independent validation | V1 independently reproduces A7's extraordinary claims (8,086/8,086 H1 windows bullish) |

**Recommendation: merge 6 of 7 branches now** (A1, A2, A3, A5, A6, A8). Hold A4 prompt v2 for CEO decision on 4 fixture flips (2 show model still gaming V2 prompt). Do not touch market_state.py until ADR-004 decision is made.

---

## Per-branch merge recommendation

### Branch A1 — Orchestrator bug bundle `worktree-agent-a08c4676`
- 5 commits (kz_trades, new_day persistence, api_calls_made, session summary, log_candidate_features)
- **V2 verdict: APPROVE_WITH_CONCERNS (merge as-is)**
- All 5 bugs reproduced via src-revert; tests fail pre-fix / pass post-fix
- 20 new tests, full suite 1852 pass (same pre-existing `test_pending_intent_stale_before_first_kz_discarded` flake noted by 5+ reviewers)
- **Minor follow-ups** (non-blocking):
  - Bootstrap tests for new_day persistence reimplement restore snippet instead of calling `_bootstrap()` directly (write-side covered, read-side integration gap)
  - `DAILY_LOSS_STOP` + `data_incomplete:` prefix are additional pre-API skip paths (pre-existing over-count, not introduced by A1)
  - Generic ERROR path at `orchestrator.py:1094` doesn't propagate `produced_candidate` flag
- **Recommendation: MERGE TO MAIN NOW** (pure bug fixes, no trading-logic change)

### Branch A2 — Execution + verification minor fixes `worktree-agent-aa7f6346`
- 2 commits (`1b6ac3b` close-price fallback + `d749035` L2 displacement reversed iteration)
- **V3 verdict: APPROVE**
- Close-price fallback correct semantics (LONG→bid, SHORT→ask); 3 tests fail pre-fix / pass post-fix
- L2 displacement change rigorously verified as non-material trading-logic change:
  - `market_state.py:320` hardcodes `disp_present = disp_ratio >= 1.5`
  - `config/agent_config.yaml:83` sets same threshold with no profile overrides
  - Threshold-equals-floor → PASS/FAIL deterministic regardless of event picked
  - Only diagnostic fields change; no downstream trading decision consumes them
- **Minor follow-ups** (non-blocking):
  - `tick.bid == 0` (market-closed) edge case still propagates 0.0 (worth 1-line guard)
  - Partial-close paths (TP1/TP2) retain original `result.price=0.0` vulnerability (correctly scoped out per commit)
- **Recommendation: MERGE TO MAIN NOW** (pure bug fixes, verified non-material)

### Branch A3 — Pre-AI gate formalization `worktree-agent-a97f76b5`
- 2 commits (`a84abde` direction-aware gate + `3da685b` watchdog git-status warning)
- **V4 verdict: APPROVE**
- **Live-drift check PASSES**: byte-diff between committed blob and working-tree file is empty — code committed matches exactly what has been running live since 2026-04-22 watchdog restart
- Gate is strictly narrower than L2 (adds `ob.type == bias` + `bb.direction == bias` filters L2 lacks); cannot false-block in practice
- 19/19 gate tests pass; GBPJPY weekly eval decline (29→15→5→1) independently verified via `wc -l`
- Watchdog git-status check fires before orchestrator restart, targets main worktree correctly, non-fatal, filter regex correct
- **Minor follow-ups** (non-blocking):
  - `scripts/canary_fixtures/last_run.json` will trigger spurious watchdog warnings (tracked + updates every canary run). Narrow filter in follow-up.
  - `no_bias` early-returns at `orchestrator.py:576-585` BEFORE the gate → direction-agnostic fallback is dead code in current flow (not a bug)
  - Counter-bias edge case theoretical today; becomes relevant after market_state fix. Worth a test then.
  - `BreakerBlock.direction` is `str` not `Literal["bullish","bearish"]` — defensive typing opportunity
- **Recommendation: MERGE TO MAIN NOW** (formalizes live code, bit-exact, all tests pass)

### Branch A5 — POI/entry/SL consistency validator `worktree-agent-a432468d`
- 1 commit (`385055b` `guard_candidate_inconsistent_pois`)
- **V5 verdict: APPROVE_WITH_CONDITIONS**
- 10 new tests, all 28 primary_analyzer tests pass; full suite 1799 pass; canary 11/12 baseline + 3/4 borderline PASS
- Counterfactual test verified against production data (Thursday US30 NY 16:00) — POI/entry/OB values all authentic
- **1 historical false-positive found** by V5's simulation against 147+ trade records: **USDJPY 2026-04-22 ny_1515** (POI in touches=2 OB via 0.2% L2 tolerance but entry in a different touches=1 OB). Trade never filled. **Across whole history, FP rate on actually-filled trades = 0.**
- **CEO decision needed**: accept the 1 FP (trade didn't fill; stricter-than-L2 is safer) OR harmonize to 0.2% tolerance
- **Additional non-blockers**:
  - Test fixture's touches=2 OB range approximated (`[48590.30, 48645.71]` vs real `[48629.71, 48645.71]`); test also omits a touches=29 mitigated OB that contains POI in production. Test exercises single-match branch but not the 2+ match branch that real data hits. Recommend expanding fixture.
  - Mitigated OB filtering gap: guard doesn't filter mitigated OBs; L2's `_find_matching_ob` does. Creates rationale mismatch in telemetry (guard says `inconsistent_pois`, L2 says `h1_poi_exists` phantom). Both reject; telemetry differs.
  - Canary doesn't route through `PrimaryAnalyzer.analyze()` → new guard not exercised in canary path. Unit tests cover.
- **Recommendation: MERGE after CEO decides on the tolerance harmonization** (1 FP on unfilled trade is acceptable to me; strict is safer)

### Branch A6 — M5 SL clamp `worktree-agent-aa6fc1ba`
- 1 commit (`c3002fa` clamp + wiring + 20 tests)
- **V6 verdict: APPROVE**
- **Agent correctly overrode my H1_ATR suggestion to use M15_ATR** — V6 confirms this was the right call. Using H1_ATR would over-buffer (ratio ≈1.79×) and SHRINK the set of rescuable CANDIDATEs. My H1_ATR suggestion would have been a silent design bug. Agent saved me from it.
- Clamp logic hand-traced through all branches (LONG, SHORT, passthrough, feasibility rails)
- Thursday US30 NY 13:46 counterfactual figures (OB_LOW=49155.31, AI_SL=49046.27, M5_SL=49219.75) verified against production record `knowledge_base/trade_records/US30_cash/2026-04-23_ny_1346.json` + `logs/us30.log:2557`
- "Skip refinement, keep original" semantic verified at `orchestrator.py:824` — NO NO_TRADE demotion on infeasible clamp
- 40/40 m5 tests pass; 1852 full suite (same flake); canary 11/12 baseline + 3/4 borderline PASS
- **Minor follow-ups** (non-blocking):
  - buffer=0 edge case: if `_compute_ob_buffer` returns 0, LONG clamp produces `clamped_sl == ob.low` exactly, which fails strict-`<` L2 re-check. Not production-relevant (live config=0.5, orchestrator always attaches `_full_config`) but worth 1-line guard
  - `_find_matching_h1_ob` docstring says "mirrors" `verification._find_matching_ob` but actually mirrors `permissions._ob_retest_sl_exception_applies` (type-filter version). Only docstring misleading; filter is semantically correct.
- **Recommendation: MERGE TO MAIN NOW** (correct design, verified counterfactual, comprehensive tests)

### Branch A8 — GBPUSD trading_enabled Gate 0.5 `worktree-agent-ad0a9ebd`
- 2 commits (`32fbe58` gate + `4369214` decision doc)
- **V7 verdict: APPROVE**
- Gate ordering verified (0 → 0.5 → 1/3); 5 config-loading red-team scenarios verified correct
- Default `True` means missing key = fail-OPEN (safe for existing instruments)
- 60/60 permissions tests pass; full suite 1838 pass
- Live config smoke test reproduced by V7 — GBPUSD A+ CANDIDATE denied at `gate=gate0_5_trading_enabled`; XAUUSD passes under same config
- **Bonus finding CONFIRMED as real latent bug (pre-existing, not introduced by A8)**: `orchestrator.py:1999` `_should_skip_first_ny_candle` uses `self.config.get("instruments", {}).get(self._symbol, {})` but `instruments` is popped during merge → always returns `{}`. **XAUUSD's `skip_first_ny_candle: true` flag has been silently ignored** — NY 13:00-13:15 candles have been evaluating even though CLAUDE.md states "skip 13:00-13:15". Worth a follow-up patch (restores trading logic → CEO approval).
- V7 non-blocking recommendations:
  1. Fix `skip_first_ny_candle` dead code
  2. Add profile-overrides-`trading_enabled` test (gap)
  3. `isinstance(trading_enabled, bool)` check with warning (YAML quoted-string footgun)
  4. Echo actual value in `details` dict rather than hard-coded False
  5. Audit scripts/tests for similar dead `config.get("instruments", ...)` lookups
- **Recommendation: MERGE TO MAIN NOW** (GBPUSD hard-block is strict improvement over label-only; skip_first_ny_candle dead-code finding is a SEPARATE follow-up)

### Branch A4 — Prompt v2 `prompt-hardening-fx-m15-ceo-review` (custom branch name)
- 2 commits (`ed28316` FX precision + self-check + `guard_candidate_wrong_side_sl` + `19852ff` M15-as-H1 STRICT RULE)
- **V8 verdict: APPROVE_WITH_CONCERNS**
- 120 tests pass (13 new); full suite 1818 pass; fixture regeneration script correctly updates only `system_prompt` (not `expected_decision`), so no test circularity
- PRECISION examples geometrically correct for all 4 decimal variants (5dp/3dp/2dp/1dp)
- `guard_candidate_wrong_side_sl` correct logic + ordering (degenerate guard first, strict `>` / `<` with `math.isclose` deferral on SL==entry)
- STRICT RULE unambiguous; breaker-zone rename safe (framework reintroduction risk low — config still restricts to `ob_retest`)
- Deviation 1 (narrower Issue 2 rule) SAFE under current config: `permissions.py:333` cutoff is `touches >= 2`, so touches=2 CANDIDATEs get rejected downstream. Brittle to threshold change; should be documented in primary_analyzer.
- **4 fixture flips vs human-annotated `expected_decision`; agent only flagged 1**:
  1. `ny_candidate_2026mar24_win` CAND→NO_TRADE (flagged, justified ✓)
  2. **`borderline_xauusd_20260115T1315_candidate` CAND→NO_TRADE (NOT flagged)** — model emits `"C1=PASS C2=PASS C3=PASS but no_qualifying_h1_poi in correct direction with touches<2"`. This is the EXACT pattern V2 prompt forbids. Model invented a `touches<2` criterion that V2 says downstream gates handle.
  3. `london_no_trade_no_active_retest_2026jan19` NO_TRADE→CAND (NOT flagged) — material behavioral change, new class of CANDIDATEs
  4. **`borderline_gbpusd_20260128T0700_fx_wrong_side_sl` CAND→NO_TRADE (NOT flagged)** — model says "all H1 bullish OBs are far below current price" — reachable-distance rejection, which V2 also explicitly forbids
- **V8 critical finding: V2 prompt is PARTIAL MITIGATION, not full fix.** The model is still gaming the prompt with reasons V2 explicitly forbids.
- **Behavioral flag**: `permissions.py:630-641` has pre-existing auto-correct for inverted TP/SL. A4's `guard_candidate_wrong_side_sl` runs BEFORE permissions.py → previously-auto-corrected wrong-side CANDIDATEs are now NO_TRADE. Deliberate change, but worth CEO awareness.
- **Interaction with A5**: wire A5 AFTER A4 to preserve distinct `wrong_side_sl` reason code (otherwise A5's `inconsistent_pois` swallows them)
- **No independent canary run against V2 baseline yet** — only `--baseline` self-established; recommend one validation run (no `--baseline` flag) before merge
- **Recommendation: HOLD for CEO decision.** V2 is real improvement on FX 5dp precision + wrong-side-SL detection, but 2 of the 4 fixture flips prove V2 does NOT fully close the over-rejection loophole. CEO should either (a) accept V2 as partial mitigation with another round to close remaining loopholes, or (b) decline and keep the current prompt until fuller fix

### F1 — ADR-004 (not a merge item; decision document)
- Two files in working tree: `.context/06_decisions/ADR-004-market-state-structural-bullish-bias.md` + `ADR-004-SUMMARY.md`
- **Filename conflict**: existing `004_sl_gate_reconciliation_2026-04-18.md` — functionally this is ADR-005. Rename before committing.
- 8 fix options enumerated (A-H); agent recommends **Option D (net-score classifier)** with `dead_zone_threshold = max(2, min_swings // 4)` as the first-principles default
- Backtest cost tiers: Min $54 / Mid $162 / Full $270. Full exceeds $50/month API cap.
- **Major escalation from ADR**: because `identify_structure` gates `detect_structure_breaks` at `market_state.py:323-350`, bullish-only labels → bullish-only BOS events → **bullish-only OBs in the entire downstream supply**. The edge metric (70% OB continuation) was measured on bullish-only OBs.
- **Important nuance for validated numbers**: batch dataset (n=367) DID include 29 SHORT trades (blocked at `permissions.py:609-614 direction_mismatch`) per `knowledge_base_backtest/analysis/data_exploitation_20260405.md:210-219`. So the batch WR is NOT strictly on LONG-only sample — the batch AI emitted SHORTs. Needs pre-validation grep to confirm.
- **Recommendation: CEO reviews ADR + SUMMARY, picks fix option, then we dispatch F2 (prototype) + F3 (backtest) + review**

### V1 — Independent validation (not a merge item; research)
- `research/directional_concentration_audit_2026-04-24/V1_INDEPENDENT_VALIDATION.md` + V1_SUMMARY.md
- **CONFIRMED (98% confidence)** — 141/141 LONG CANDIDATEs, 8,086/8,086 H1 windows bullish, root cause at `market_state.py:239-247`, bug since initial commit `436c16b`
- V1 confirmed live proof in current pipeline_state: H1 `hh=11, hl=9, lh=11, ll=9` (both branches qualify, bullish wins); M15 `ll=50 > hh=43` (bearish numerically stronger, bullish label wins)
- V1 minor refinements: "pure downtrend" bullish only in saturated windows (realistic production, not tiny synthetic); `recent_pairs` variable name is misleading

---

## Proposed merge order

Assuming CEO approves 6 of 7 branches for merge:

```
Step 1 — Research commit (clean up documentation debt)
  git add research/thursday_2026-04-23_analysis/ \
          research/directional_concentration_audit_2026-04-24/ \
          research/reviews_2026-04-24/ \
          .context/06_decisions/005_market_state_structural_bullish_bias_2026-04-24.md \
          .context/06_decisions/005_market_state_structural_bullish_bias_2026-04-24_SUMMARY.md
  git commit -m "research(audit): Thursday 2026-04-23 forensic + reviews + structural bias ADR"

Step 2 — A3 first (formalizes live code; no behavioral change)
  git merge --no-ff worktree-agent-a97f76b5

Step 3 — A1 (orchestrator bugs; unblocks limit-fill lifecycle)
  git merge --no-ff worktree-agent-a08c4676

Step 4 — A2 (execution + verification fixes)
  git merge --no-ff worktree-agent-aa7f6346

Step 5 — A6 (M5 SL clamp)
  git merge --no-ff worktree-agent-aa6fc1ba

Step 6 — A5 (POI/entry/SL validator; after CEO decides on tolerance)
  git merge --no-ff worktree-agent-a432468d

Step 7 — A8 (GBPUSD trading_enabled flag)
  git merge --no-ff worktree-agent-ad0a9ebd

Step 8 — Integration test on main
  pytest tests/ -v
  (expect 1852+ pass, same pre-existing flake)

Step 9 — Canary on main (one validation run, ~$1-2)
  python scripts/canary_test.py

Step 10 — Rolling restart live (picks up all 7 merged commits)
  Per the pattern in handoff 36 §2.1 — SIGTERM fleet, respawn with --profile redacted_account

Step 11 — HOLD A4 (prompt v2) pending CEO decision
Step 12 — HOLD market_state fix pending CEO decision on ADR-004
```

---

## What I recommend you review first

In priority order:

1. **V1_SUMMARY.md + ADR-004-SUMMARY.md** (5 min) — understand the structural bullish-bias bug and the fix options
2. **SYNTHESIS.md** (from Thursday audit) — what happened Thursday, what bugs surfaced
3. **V8 review of A4 prompt v2** (the 4-flip finding — especially the 2 unflagged flips showing V2 is still being gamed)
4. **V5 review of A5** — the 1 FP (USDJPY 2026-04-22 ny_1515) — decide on tolerance harmonization

Everything else is straightforward APPROVE.

---

## Outstanding items summary

| Item | Status | Action |
|---|---|---|
| 6 code branches ready to merge | APPROVED by reviewers | CEO sign-off, then merge |
| A4 prompt v2 | 4 fixture flips, 2 unflagged, V2 partial mitigation | **CEO decision** |
| A5 tolerance | 1 FP on unfilled trade | **CEO decision** on strict vs 0.2% harmonization |
| Uncommitted research (Thursday analysis + reviews + directional audit) | Ready to commit | Bundle into research commit |
| ADR-004 filename | Conflict with existing 004_* | Rename to 005_* before commit |
| ADR-004 fix option | 8 enumerated; agent recommends Option D | **CEO decision** |
| F2 prototype fix for market_state | Not started | Dispatch after CEO picks option |
| Full-2026 backtest | Not started | Dispatch after F2 with CEO-approved scope |
| `skip_first_ny_candle` dead code bug (V7 finding) | Pre-existing latent bug | Follow-up PR, CEO approval (restores trading logic) |
| `kz_trades` NameError pre-existing flake | V2-V8 all noted | Separate small PR |

---

## Open questions for CEO

1. **A4 prompt v2 merge or hold?** V2 is real improvement but still being gamed on 2 of 4 flipped fixtures. Options:
   - (a) Merge A4 as partial mitigation; plan V3 to close remaining loopholes
   - (b) Hold A4; prompt another round to plug `touches<2` + `reachable-distance` rejection patterns before merging

2. **A5 tolerance harmonization?** New guard uses strict bounds; L2 uses 0.2% tolerance. 1 FP (on unfilled trade) results. Options:
   - (a) Accept strict (safer, catches 1 extra case per ~30 limits placed)
   - (b) Harmonize to 0.2%

3. **ADR-004 fix option?** Agent recommends Option D (net-score classifier). Alternatives enumerated. Backtest cost scales with ambition.

4. **market_state fix timeline?** Until it lands + backtests validate, every new CANDIDATE the system produces inherits the bullish bias. Do we pause live trading, keep trading, or something in between?

5. **Rolling restart timing?** Live processes need restart to pick up merged commits. Coordinate with kill-zone windows.
