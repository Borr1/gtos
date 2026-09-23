# Dispatch + API Ledger

This program runs on TWO billing tracks (per CEO clarification 2026-04-28; memory `feedback_billing_tracks_distinction`):

- **Claude Code subscription** — flat monthly fee paid by CEO. Pays for ALL agent dispatches (audit, feature engineering, modeling, stats, adversarial, productionization). **No per-task variable cost; no $-budget gate.** Dispatches are bounded only by wallclock and reasonable subscription throughput.
- **Anthropic API ($50/mo cap; auto-reload DISABLED)** — only hit by code that calls the Anthropic SDK directly. In this program that means prompt-replay research only: K55-style ML-vs-AI head-to-heads, HALLUC-style A/Bs, prompt-variant backtests. Calibration: A4 cost $1.05 for n=11 replays = ~$0.10/setup at Sonnet-4.6 max effort.

**Tracking convention:** dispatches counted by event + outcome, not dollars. API spend tracked per-event; alarm at $30 cumulative across the program (60% of cap).

---

## Q1 — subscription-only by design

K54 v2 trains on local features extracted from local OHLCV + shadow logs + knowledge_base. No prompt replays needed. **API forecast: $0.**

| Date | Phase | Tier | Task | Status | API $ | Deliverable |
|---|---|---|---|---|---:|---|
| 2026-04-28 | Q1 | T2 | K54 v1 audit | DONE | $0 | `k54_v1_audit.md` (351 lines) + `k54_v1_features.csv` (20 lines) |

**Q1 API cumulative:** $0 / $50.

---

## Q2 — first phase that MAY hit API cap

K55 ML-vs-AI shadow harness, if it replays the live prompt against historical CANDIDATEs for a head-to-head benchmark, will be the first API-billed work in this program. Forecast TBD when K55 design lands; calibrate against A4's ~$0.10/setup. A 200-setup head-to-head ≈ $20.

| Date | Phase | Tier | Task | Status | API $ | Deliverable |
|---|---|---|---|---|---:|---|

**Q2 API cumulative:** $0 / $50 (open).

---

## Q3 — subscription-only by design

Tick-feature engineering is local Python. No prompt replays. **API forecast: $0.**

---

## Q4 — subscription-only by design

Live shadow worker calls only the local ONNX model. The production AI continues to bill against the live trading $-cap, NOT against this program. **API forecast: $0.**

---

## API-spend alarm thresholds (program-wide)

- **$30 cumulative** → re-baseline check with CEO; pause API-billed dispatches.
- **$45 cumulative** → halt all API-billed dispatches; subscription-only until topup.

---

*Maintained by the ML Program Orchestrator. Updated on every dispatch close + on every API-spend event.*
