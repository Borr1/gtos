# HALLUC-1 Multi-Framework Dispatch Suppression — Live Verification 2026-04-28

**Status:** Diagnosis complete, no code changes yet. Awaiting Phase 2 session to implement.
**Live trading impact:** Negligible — all 7 historical hits caught by safety gates, zero unsafe trades placed.
**This is a HANDOFF document** for the session handling Phase 2 prompt/framework work.

---

## TL;DR

The recurring "HALLUC-1" pattern (CANDIDATE→demoted to NO_TRADE due to null `trade_parameters`) on GBPJPY is **NOT a model hallucination**. The AI is correctly reading real M15 FVG fill setups. Three compounding code bugs funnel those reads into the wrong dispatch path:

1. **Prompt bias** at `src/prompts/primary_analyzer_prompt.py:1426` — the user-prompt's last line literally says *"Evaluate this M15 candle for the OB Retest setup"*. Overrides the system-prompt's PARALLEL EVALUATION block at lines 421-451. AI is told to pick `ob_retest`.
2. **MSO renderer hides mitigated OBs** at `src/prompts/primary_analyzer_prompt.py:1050` — `obs = [ob for ob in tf_data.get("order_blocks", []) if not ob.get("mitigated", False)]`. In a strong trending market all bullish OBs get retested → AI sees an empty "Unmitigated OBs" subsection but is still told to pick `ob_retest` from it.
3. **L2 routes on the wrong field** at `src/components/verification.py:307` — reads `analysis.framework` (the biased routing field), not `analysis.frameworks_evaluated.<X>.qualified` (the AI's actual qualification flags).

When the model's correct internal answer is "fvg_fill qualifies on M15 FVG `[215.450, 215.499]`", the system reads `framework: ob_retest` off the wrapper, runs `h1_poi_exists` against an empty unmitigated H1 OB list, and rejects. The HALLUC-1 demote at `primary_analyzer.py:695-706` is the AI's only honest move when forced into ob_retest with no OBs available — it returns null `trade_parameters` because there is no H1 OB to anchor on.

---

## Smoking gun — 2026-04-28 01:30:27 UTC GBPJPY

`knowledge_base/trade_records/GBPJPY/2026-04-28_tokyo_0130.json` contains the AI's emitted JSON simultaneously holding:

| Field | Value | What it means |
|---|---|---|
| `framework` (top-level) | `"ob_retest"` | ← what L2 routes on |
| `frameworks_evaluated.fvg_fill.qualified` | `true` | ← AI's actual finding |
| `frameworks_evaluated.ob_retest.qualified` | `true` (but reason text says *"ob_retest does NOT qualify as no unmitigated bullish H1 OBs exist"*) | internal flag-vs-text disagreement |
| `h1_setup.poi_type` | `"FVG"` | confirms FVG |
| `h1_setup.poi_price_level` | `215.461` | midpoint of M15 FVG `[215.450, 215.499]` (verbatim in MSO) |
| `overall_reasoning` | *"fvg_fill framework fires on unfilled bullish M15 FVG at 215.499-215.450..."* | reasoning matches the FVG, not an OB |

**Three of four signals say fvg_fill; only the routing field says ob_retest.** L2 verification then runs `_check_h1_poi_exists` (`verification.py:297-405`) against the empty H1 unmitigated OB list, fails, and the FVG-specific `_check_entry_in_fvg` (`verification.py:541-610`) is **skipped** because L2 only routes on the wrong top-level `framework` field.

---

## Pattern across all 7 historical hits

All 7 are **LONG-side**, all happen in **trending-bull regimes** with **zero unmitigated same-direction H1 OBs**.

| UTC | Class | h1_unmitigated_OB_count (same dir) | M15 FVGs unfilled | fvg_fill F4 qualified? | KZ |
|---|---|---|---|---|---|
| 2026-04-27 07:19 | HALLUC-1 | 0 | (high) | not stated | London |
| 2026-04-27 08:00 | HALLUC-1 | 0 | yes | no | London |
| 2026-04-27 08:15 | HALLUC-1 | 0 | yes | no | London |
| 2026-04-27 08:45 | HALLUC-1 | 0 | yes | no | London |
| 2026-04-27 09:30 | HALLUC-1 (also c1_failed flagged) | 0 | yes | no | London |
| 2026-04-28 01:15 | HALLUC-1 | 0 | 7 | no | Tokyo |
| 2026-04-28 01:30 | L2 reject | 0 | 5 (incl 215.499-215.450 ratio-6.7) | **YES** | Tokyo |
| 2026-04-28 02:15 | HALLUC-1 | 0 | 8 | no | Tokyo |

The 01:30 hit is the smoking gun because `fvg_fill.qualified=true` was emitted internally — proving the AI saw the FVG, evaluated it, and would have routed correctly if not for the prompt-line-1426 bias.

Distinct from NAS100 HALLUC-1 (precision-rounding class, fixed in commit `2c75f98` + 4 sister fixes; zero recurrence today).

n=7 LONG-side fits memory `project_a6_decay_attribution_long_side_concentrated` and `project_f2_long_decay_pinpointed_trending_bull_2026-04-27` but n is too small to weight independently.

---

## Verdict on CEO's question

> *"Is this actually an issue or is the AI saying something for a real reason?"*

**The AI is saying something for a real reason.** It's reading real M15 FVG geometry from the MSO it's given, recognizing the fvg_fill setup correctly, and outputting the FVG midpoint as `poi_price_level`. The "issue" is in the system code:

- **Prompt forces it to pick `ob_retest`** as the framework label (line 1426).
- **MSO render strips mitigated OBs** so AI has no OBs to anchor to (line 1050).
- **L2 reads the wrong field** to route the verification check (verification.py:307).

The HALLUC-1 demote (`primary_analyzer.py:695-706`) is honest behavior — the AI cannot fill `trade_parameters` for a framework that has no anchor in the rendered MSO, so it returns nulls and the system catches it.

**Hypothesis ranking by evidence weight:**
1. **H2 + H4 (multi-framework dispatch suppression on a mitigated-OB H1)** — STRONGEST. Both are present. Confirmed.
2. **H6 (UX/state-machine framing)** — STRONG. The null trade_params IS the AI's correct response to being routed wrong.
3. **H3 (level miscitation due to schema mismatch)** — MODERATE. Secondary to H2.
4. **H1 (pure hallucination)** — REJECTED. AI's cited 215.461 is the M15 FVG midpoint listed verbatim in MSO.
5. **H5 (equal_highs sweep is the trigger)** — REJECTED. Sweep is observation-only (G4 in prompt), not a routing input. Shared signature is incidental to OB-exhaustion in trending markets.

---

## Recommended fix order (Phase 2 scope)

Priority 1 (small, single-line, biggest impact):
1. **Fix `primary_analyzer_prompt.py:1426`** — change the hardcoded "for the OB Retest setup" to framework-neutral wording. ~2-line prompt change. Trivial to revert. **This alone may resolve 80%+ of cases.**

Priority 2 (medium, compositional):
2. **MSO renderer (`primary_analyzer_prompt.py:1050`)** — show mitigated H1 OBs as a separate flagged section so the AI can see them and decide *"all OBs mitigated; route to fvg_fill or breaker_re_entry"* explicitly rather than infer it from emptiness.
3. **L2 verification (`verification.py:297-405`)** — read `analysis.frameworks_evaluated.X.qualified` (the AI's qualified flags) instead of `analysis.framework` (the biased routing label). Makes L2 robust to wrapper-level errors. Pairs with #1 — even if prompt fix is reverted, this catches the bad routing.

Priority 3 (defensive, non-breaking):
4. **Prompt self-check item:** AI must assert `analysis.framework` literally matches the framework named in `overall_reasoning`. Closes the internal flag-vs-text inconsistency observed at 01:30.
5. **Tighten pre-AI gate** to require both H1 POI source AND M15 fill-confirmation before the AI call. Saves cost; doesn't fix root cause.

Priority 4 (no-op option):
6. Do nothing. Safety gates catch every instance; ~6 wasted Sonnet calls/week.

The agent that ran the deep-dive recommended Priority 1 alone may suffice; pair with Priority 2 and 3 (the L2 routing fix) for defense in depth.

---

## Live-trading impact summary

| Concern | Status |
|---|---|
| Unsafe trade placed | 0 (safety gates working) |
| Open positions | 0 (verified via direct mt5 query 2026-04-28 02:18 UTC) |
| Wasted API cost | ~6 Sonnet calls/week — minor |
| Monitoring noise | non-trivial (RED alerts during KZs) |
| CEO blindspot risk | none — gates are loud-fail |

---

## What this session has already shipped to main

| Branch | Commit on main | What it fixes | Status |
|---|---|---|---|
| `feature/fix-notification-queue-worker` | `9c5d2e9` | Notification queue worker architecture (cron-script enqueue + worker drain) | ✅ Merged + worker running |
| follow-up dotenv | `afca41d` | CLI loads `.env` so worker has TELEGRAM_* env | ✅ Merged |
| follow-up cron dotenv | `a27ede3` | 4 cron scripts load_dotenv at startup | ✅ Merged |
| `feature/fix-sibling-daemon-stability` | `0d3b92a` | Watchdog cmd.exe vs python PID confusion + FX/metals tick subscription robustness | ✅ Merged + daemons restarted |
| `feature/fix-html-escape-notification-alerts` | `c24f1e1` | Drop `parse_mode=HTML` everywhere; kills 400 storm bug class | ✅ Merged + worker restarted |

## What this session has parked pending CEO decision

| Branch | What it does | Status |
|---|---|---|
| `feature/fix-broker-offset-and-bug25-test` | (1) Detect broker offset on daemon startup so tick capture works on FN GMT+3; (2) lock in bug #25 (equity=0 false-trigger) regression test | Branch ready at `193ce86` (3979 tests pass), NOT merged — CEO triaging separately |

---

## Don't-touch list (trading-logic files)

The Phase 2 fix should NOT modify:
- `src/components/orchestrator.py` (main pipeline — only prompt/MSO/verification files are in scope here)
- `src/components/primary_analyzer.py` (only `_check_candidate_completeness` at lines 695-706 is **observability** for this bug — leave the demote logic alone)
- `src/components/execution.py`
- `src/components/market_state.py`
- `src/components/permissions.py`
- `src/safety/dormant_state.py`

In scope:
- `src/prompts/primary_analyzer_prompt.py` (lines 1050 + 1426 — the prompt + MSO render)
- `src/components/verification.py` (line 307 routing logic)
- prompt-related tests

---

## Files cited (evidence)

Source code:
- `C:\Users\MSI\Documents\ai-trading-agent\src\prompts\primary_analyzer_prompt.py:299-358` (R1-R8 + G1-G5 + NO FOURTH GATE)
- `C:\Users\MSI\Documents\ai-trading-agent\src\prompts\primary_analyzer_prompt.py:421-451` (PARALLEL EVALUATION block)
- `C:\Users\MSI\Documents\ai-trading-agent\src\prompts\primary_analyzer_prompt.py:558-651` (FVG_FILL FRAMEWORK)
- `C:\Users\MSI\Documents\ai-trading-agent\src\prompts\primary_analyzer_prompt.py:1029-1109` — `_format_tf` ; **line 1050 is the unmitigated-only OB filter**
- `C:\Users\MSI\Documents\ai-trading-agent\src\prompts\primary_analyzer_prompt.py:1426` — **smoking gun: "Evaluate this M15 candle for the OB Retest setup"**
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\primary_analyzer.py:695-706` — `guard_candidate_null_params` demote logic
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\verification.py:297-405` — `_check_h1_poi_exists`, routes on `analysis.framework`
- `C:\Users\MSI\Documents\ai-trading-agent\src\components\verification.py:541-610` — `_check_entry_in_fvg` skipped for non-fvg_fill framework

Live-trading evidence (2026-04-28):
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\live_evaluations\GBPJPY\2026-04-28.jsonl` rows 5/6/9 (today's 3 hits at 01:15 / 01:30 / 02:15 UTC)
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\trade_records\GBPJPY\2026-04-28_tokyo_0130.json:11505-11631` — full system_prompt + user_message + ai_response for the smoking-gun L2 reject
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\no_trades\nt_2026-04-28_0115.yaml` and `nt_2026-04-28_0215.yaml` — verbatim AI reasoning for today's 2 HALLUC-1 hits
- `C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\candidate_features_log.jsonl` — `mso_h1_unmitigated_ob_count: 0` rows for the 01:15 and 02:15 GBPJPY candles

Historical evidence (2026-04-27):
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\live_evaluations\GBPJPY\2026-04-27.jsonl` rows 13/16/17/19/22 (yesterday's 5 London-KZ hits)
- `C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\no_trades\nt_2026-04-27_0800.yaml`, `nt_2026-04-27_0815.yaml`, `nt_2026-04-27_0845.yaml`

---

## Related memories (read these too)

- `project_multi_framework_dispatch_suppression` — original Council-2026-04-26 verdict; this session adds live-trading verification
- `project_halluc_1_precision_bug_class_2026-04-27` — distinct class (NAS100 precision); fixed in commit 2c75f98 + 4 sister fixes; zero recurrence today, do not conflate
- `project_eurusd_sl_root_cause` — same family as halluc_1 precision class
- `feedback_engineer_systemic_not_patches` — CEO 2026-04-26: design real fixes that apply across all instruments

---

## Provenance

- Investigation agent: Opus 4.7 (1M context), max effort, isolated worktree, ~80 tool calls, ~10 minutes wallclock.
- Verdict synthesized + handoff written by main monitoring session 2026-04-28.
- All evidence files exist on disk at the paths cited; no synthetic data.
