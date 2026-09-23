---
title: Q4.6 — T7 sim vs session-KB CANDIDATE-rate discrepancy
author: Claude Code (main thread, data archaeology session)
date: 2026-04-20
parent: research/b_deep_audit_2026-04-19/phase4_chairman_synthesis.md
status: resolved — pipeline-version + stage-mismatch artifact, not a bug
---

# Q4.6 — Sim vs KB CANDIDATE-rate discrepancy

## 1. The question (from Phase-4 chairman synthesis)

> Phase-2 γ reports **10 XAUUSD CANDIDATEs / 2100 records (0.48%)** on the sim's Jan 2 – Apr 10 run.
> Phase-2 δ reports **48 XAUUSD CANDIDATEs / 828 records (5.80%)** on the "same period" from the session-KB.
>
> 5.80 / 0.48 ≈ **12× difference**. Bug or artifact?

**Answer up-front: artifact.** Two independent effects are compounded — a pipeline-version mismatch (γ's sim runs the current Sonnet-4.6 + L2 pipeline; δ's KB was produced by the older debate-era pipeline) and a stage-mismatch (γ counts at the **post-L2** stage; δ counts at the **raw AI-emitted** stage). When reconciled at the same stage, the sim's raw-AI CAND rate (~36%) is actually **higher** than the backtest KB's raw-AI CAND rate (~6%), and the sim's post-L2 rate (0.48%) is comparable to the backtest KB's post-debate pass rate (33/828 = 4.0%). γ reviewer already diagnosed this in `research/b_deep_audit_2026-04-19/phase2/gamma_review.md:24`; this document confirms it by re-deriving every number.

## 2. Reproducing both cited figures

### 2a. γ's "10 / 2100" — sim `all_results_jan_apr10.json`

File: `.claude/worktrees/agent-a092f636/research/t7_live_simulation/all_results_jan_apr10.json`
Metadata: `symbol=XAUUSD, start=2026-01-02, end=2026-04-10, period='Jan 2 – Apr 10, 2026 (combined: Jan-Mar11 + Mar11-Apr10, 24 duplicate Mar-11 records removed)'`
Total records: **2100**

Decision distribution:

| decision | count | % |
|---|---:|---:|
| NO_TRADE | 1034 | 49.24% |
| REJECTED_L2 | 741 | 35.29% |
| NO_TRADE_PARSE_FAIL | 289 | 13.76% |
| BLOCKED_LIMIT | 13 | 0.62% |
| PARSE_ERROR | 13 | 0.62% |
| **CANDIDATE** | **10** | **0.48%** |
| TOTAL | 2100 | 100.00% |

γ's 0.48% is the **post-L2** CANDIDATE rate (AI emitted a direction AND the L2 verifier passed AND the sim's fill rules let it through).

The 10 records (chronological):

| # | candle_time | kill_zone |
|---:|---|---|
| 1 | 2026-01-15T13:15:00Z | ny |
| 2 | 2026-01-20T16:00:00Z | ny |
| 3 | 2026-01-21T15:00:00Z | ny |
| 4 | 2026-01-27T07:00:00Z | london |
| 5 | 2026-02-06T07:00:00Z | london |
| 6 | 2026-02-20T15:00:00Z | ny |
| 7 | 2026-03-10T16:00:00Z | ny |
| 8 | 2026-03-24T13:15:00Z | ny |
| 9 | 2026-03-31T14:00:00Z | ny |
| 10 | 2026-04-06T10:00:00Z | london |

### 2b. δ's "48 / 828" — backtest KB `knowledge_base_backtest/sessions/XAUUSD/2026-*.json`

39 files found: 2026-01-05 → 2026-03-25 (Q1 2026 + Mar 25).
Total `candle_evaluations` entries across files: **828**

Decision distribution (field: `decision`):

| decision | count | % |
|---|---:|---:|
| NO_TRADE | 605 | 73.07% |
| SKIP | 175 | 21.14% |
| **CANDIDATE** | **48** | **5.80%** |
| TOTAL | 828 | 100.00% |

δ's 5.80% is the **raw AI-emitted** CANDIDATE rate, *before* the debate / L2 / sim-fill stages.

What happens to those 48 after the next stage (`debate_verdict` field, older pipeline's equivalent of L2):

| debate_verdict | count | trade_executed |
|---|---:|:---:|
| AUTO_APPROVED | 33 | True |
| SAFETY_REJECT | 15 | None |

So 33 / 828 = **3.99%** post-debate trade-execution rate in the backtest KB. This is the stage-apples-to-apples comparison to γ's 0.48% post-L2 figure.

Setup-grade mix (field: `setup_grade`): 38× A+, 10× A. Kill-zone mix: 28× NY, 20× London. No Tokyo (XAUUSD has no Tokyo kill zone).

## 3. Root cause: pipeline-version mismatch

γ reviewer already stated this at `research/b_deep_audit_2026-04-19/phase2/gamma_review.md:24`:

> "I verified (b): γ's T7 sim runs the current Sonnet 4.6 L2 pipeline; δ's 48-CAND figure is older pipeline per session file `knowledge_base_backtest/sessions/XAUUSD/2024-04-01_session.json:54` fields (`debate_triggered`, `debate_verdict`). This is a **pipeline-version mismatch**, not a bug."

Independent confirmation:

- **δ's KB schema** contains `debate_triggered: bool` and `debate_verdict: AUTO_APPROVED|SAFETY_REJECT` on every CAND record (verified on all 48 CAND rows). This schema corresponds to the Component-3B **bull/bear debate** framework, which CLAUDE.md `## SYSTEM ARCHITECTURE` describes as "PAUSED (code exists, not wired)". It was the pre-Sonnet-4.6 production pipeline.
- **γ's sim schema** contains `decision ∈ {CANDIDATE, REJECTED_L2, NO_TRADE, NO_TRADE_PARSE_FAIL, BLOCKED_LIMIT, PARSE_ERROR}`. The `REJECTED_L2` bucket is the current Sonnet-4.6 + L2-verifier pipeline's output from `primary_analyzer.py` → L2 verification in `verification.py`.
- The two schemas are mutually exclusive: no record in δ's KB has a `REJECTED_L2` decision; no record in γ's sim has a `debate_verdict` field.
- Different generation tools produced different evaluation densities on overlapping calendar windows: δ's KB has 828 rows over Jan 5 – Mar 25 (avg ~21/day); γ's sim has 2100 rows over Jan 2 – Apr 10 (avg ~30/day). The older pipeline appears to have gated some candles out before reaching an AI call (e.g. no-setup pre-filter), so its denominator is smaller.

## 4. Stage-mismatch (secondary effect)

Even at the same pipeline version, the two cited numbers are at different funnel stages. Stage-adjusted, the sim's **raw-AI CAND rate** is *higher* than the backtest KB's raw-AI rate:

| pipeline funnel stage | γ sim (current) | δ backtest KB (older) |
|---|---:|---:|
| raw records | 2100 | 828 |
| raw AI-emitted CAND | 764 (36.4%) † | 48 (5.80%) |
| post-gate CAND | 10 (0.48%) ‡ | 33 (3.99%) § |

† sim raw AI-emitted = CANDIDATE (10) + REJECTED_L2 (741) + BLOCKED_LIMIT (13) = 764. Excludes NO_TRADE (1034) and NO_TRADE_PARSE_FAIL (289, which is a degraded read of an AI response that failed to parse as either direction or NO_TRADE). PARSE_ERROR (13) is ambiguous — treated here as not-AI-CAND since direction is unknown; including it changes the rate only marginally (777/2100 = 37.0%).
‡ post-L2 CANDIDATE only.
§ post-debate AUTO_APPROVED only.

**Direction of the effect**: the current Sonnet 4.6 pipeline is **more trigger-happy at the AI stage** (~36% vs ~6% raw CAND rate) and **more aggressively filtered at the post-AI stage** (L2 kills 741/764 = 97% of raw CANDs; debate killed only 15/48 = 31%). Net result: the current pipeline places **fewer** trades per 1000 candles (10/2100 ≈ 4.8 trades/kcandle) than the older pipeline would have (33/828 ≈ 40 trades/kcandle), but those trades are more curated.

This finding is consistent with the known 10.3% CANDIDATE-rate baseline cited in CLAUDE.md (`## CURRENT PROJECT STATE → Canonical numbers`) — 10.3% lands between the two (and is an overall average, not XAUUSD-specific or current-period).

## 5. 10-record trace (backtest KB, chronological)

The original brief asked for "10 XAUUSD session-KB records → trace into old T7 sim, categorize drop-stage". The requested methodology (live-KB records → T7 sim) is **infeasible** this session because:

1. The `knowledge_base/live_evaluations/XAUUSD/` directory has only 9 files dated 2026-04-06 through 2026-04-19 (Explore agent enumerated the directory). No Jan 2 – Apr 5 live records exist to map back to the sim's Jan-Mar window.
2. The T7 sim was run against the older pipeline's output (γ's `all_results_jan_apr10.json`); there is no "old T7 sim" co-extensive with δ's backtest KB to trace into.

Substituting the available source — **backtest KB → forward-fill table** — for the first 10 CANDs:

| # | candle_time | KZ | grade | framework | debate_verdict | trade_executed | trade_id | drop stage |
|---:|---|---|---|---|---|:---:|---|---|
| 1 | 2026-01-05T09:00:00Z | london | A | ob_retest | AUTO_APPROVED | True | bt_2026-01-05_london_001 | **executed** |
| 2 | 2026-01-05T13:15:00Z | ny | A | ob_retest | SAFETY_REJECT | — | — | dropped @ debate |
| 3 | 2026-01-06T07:30:00Z | london | A+ | ob_retest | AUTO_APPROVED | True | bt_2026-01-06_london_001 | **executed** |
| 4 | 2026-01-06T14:00:00Z | ny | A+ | ob_retest | AUTO_APPROVED | True | bt_2026-01-06_ny_002 | **executed** |
| 5 | 2026-01-07T14:30:00Z | ny | A+ | ob_retest | SAFETY_REJECT | — | — | dropped @ debate |
| 6 | 2026-01-09T08:30:00Z | london | A+ | ob_retest | AUTO_APPROVED | True | bt_2026-01-09_london_001 | **executed** |
| 7 | 2026-01-09T14:00:00Z | ny | A+ | session_sweep | SAFETY_REJECT | — | — | dropped @ debate |
| 8 | 2026-01-09T14:15:00Z | ny | A+ | session_sweep | AUTO_APPROVED | True | bt_2026-01-09_ny_002 | **executed** |
| 9 | 2026-01-12T07:30:00Z | london | A+ | ob_retest | AUTO_APPROVED | True | bt_2026-01-12_london_001 | **executed** |
| 10 | 2026-01-12T15:00:00Z | ny | A+ | ob_retest | AUTO_APPROVED | True | bt_2026-01-12_ny_002 | **executed** |

7/10 AUTO_APPROVED → executed; 3/10 SAFETY_REJECT at debate (all NY kill-zone 14:00-14:30 rejections, all `ob_retest` or `session_sweep`). Population stats across all 48: 33/48 = 69% executed, 15/48 = 31% SAFETY_REJECT.

None of these 10 backtest-KB records can be cross-matched to the sim's 10 CANDIDATEs at the same candle_time (sim's 10 CANDs are dated 2026-01-15, 01-20, 01-21, 01-27, 02-06, 02-20, 03-10, 03-24, 03-31, 04-06; backtest KB's first 10 CANDs are 01-05 through 01-12). This divergence is expected given the pipeline-version mismatch (different models, different prompts, different gating rules produce CANDs at different candles).

## 6. Infeasibility of live-KB trace (original methodology)

Original brief: "Walk 10 XAUUSD session-KB records, trace into old T7 sim, categorize drop-stage."

Explore agent confirmed: `knowledge_base/live_evaluations/XAUUSD/` contains only 2026-04-06 through 2026-04-19 (9 files). 11 total CAND records, all on 2026-04-15/16/17, all `L2_REJECTED` (reason: `sl_beyond_ob`). No Jan-Mar live records exist.

Substituted methodology: backtest KB → forward-fill table (above). For the forward path from backtest KB CAND → actual trade outcome, `knowledge_base_backtest/trade_records/XAUUSD/` would be the source. That was not within the Q4.6 scope (which is about CAND-rate reconciliation, not outcome tracing); noted for future audits.

## 7. Conclusion

- **The 12× discrepancy is an artifact.** Two pipeline versions (debate-era vs Sonnet-4.6+L2-era) counting at two different funnel stages (raw AI-emitted vs post-gate).
- **Stage-adjusted**, the current pipeline is ~6× *more* CAND-prone at the AI stage (36.4% vs 5.80%), and its L2 gate is ~3× stricter than the old debate gate (kills 97% vs 31% of raw CANDs). Net trades placed per 1000 candles is ~8× lower under the current pipeline.
- γ reviewer already reached this conclusion independently (`phase2/gamma_review.md:24`). This document adds (a) the stage-adjusted reconciliation with explicit funnel math, (b) reproductions of both citations bit-exact, and (c) the 10-record backtest KB trace table.
- **Recommendation**: close Q4.6 as resolved; no bug, no code change required. If future audits want to compare rate metrics across pipeline generations, report both the raw-AI rate AND the post-gate rate, and state which pipeline generation produced the KB.
- **Follow-up observation worth flagging** (not required by Q4.6, surfaced incidentally): 97% L2-rejection of raw AI CANDs under the current pipeline is high. Cross-reference with FA-2's findings (FA-2 shipped `fa35cc0`: post-AI degenerate-params validator + non-zero `sl_buffer_applied`). Worth confirming whether the 741 REJECTED_L2 sim records are dominated by `sl_beyond_ob` (pre-FA-2 behavior) or by legitimate geometry violations. The `post_fa2/xauusd_*` sims (FA-3, verified in `fa3_verification.md`) show 184 raw CAND across 2130 evals = 8.6% — higher than γ's pre-FA-2 rate — suggesting FA-2 loosened the rejection floor. Not a Q4.6 concern.

## Reproduction snippets

```python
import json, glob, os
from collections import Counter

# gamma's 10/2100
d = json.load(open('.claude/worktrees/agent-a092f636/research/t7_live_simulation/all_results_jan_apr10.json', encoding='utf-8'))
print(len(d['results']), Counter(x['decision'] for x in d['results']))
# 2100 Counter({'NO_TRADE': 1034, 'REJECTED_L2': 741, 'NO_TRADE_PARSE_FAIL': 289, 'BLOCKED_LIMIT': 13, 'PARSE_ERROR': 13, 'CANDIDATE': 10})

# delta's 48/828
total, cands = 0, 0
files = sorted(glob.glob('knowledge_base_backtest/sessions/XAUUSD/2026-*.json'))
verdicts = Counter()
for f in files:
    for ev in json.load(open(f, encoding='utf-8')).get('candle_evaluations', []):
        total += 1
        if ev.get('decision') == 'CANDIDATE':
            cands += 1
            verdicts[ev.get('debate_verdict')] += 1
print(f'{cands}/{total}', verdicts)
# 48/828 Counter({'AUTO_APPROVED': 33, 'SAFETY_REJECT': 15})
```

Both reproduce bit-exact.
