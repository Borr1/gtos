# 12-HOUR AUTONOMOUS LOOP — FINAL HANDOFF (2026-06-14, read this first)

## What I did (MT5 data only, no external APIs, full 12h)
8 rigorous research waves + the native real-engine validation, every backtest through a unit-tested
fill library (geometry_lib) with independent no-lookahead audits, random/invert nulls, strict OOS,
and per-year 2015-2026 checks. Full log: RESEARCH_LOOP_LEDGER.md. Decision doc: ULTIMATE_GO_LIVE_DOSSIER.md.

## The bottom line (honest)
ONE real, audited, FTMO-safe edge exists in free MT5 data on this universe — and it is small:
**Gold-anchored, volatility-gated FVG-retest 2R continuation** (precious metals only XAU/XAG USD/EUR/AUD,
~81% XAUUSD; gate ATR14>=1.2*SMA100; structural stop; correlated-risk-unit sizing).
- Reproduced independently: +0.22R/trade, n~480-570, 8/12 positive years, forward 2025 +0.32 / 2026 +0.33.
- FTMO-safe deployable return: ~0.02-0.06%/month at conservative fixed-gate sizing (0.25-0.5%/unit, maxDD<10%);
  up to ~0.22%/month only with the walk-forward gate (an extra moving part). Real, but a small sleeve.
- Artifact: gold_sleeve_strategy.py (+ test_gold_sleeve.py, 3 regression tests pass).

## The decisive go-live finding (native real-engine run)
The EXISTING production V4 selector, run through the REAL engine at native geometry, LOSES:
-0.290R/fill, -1.4R/day, ~21% positive days, NEGATIVE EVERY MONTH (FINAL: 160 days / 779 fills, -226R; 2026 forward -0.384R/fill on 28 days;
2026 forward CONFIRMS even worse: -0.468R/fill, 1/10 pos days). Loses in EVERY period. This matches the hard-halt history.
=> DO NOT go live on the existing selector. Deploy the gold sleeve as a STANDALONE REPLACEMENT RULE
(metals-only, vol-gated FVG, 2R, correlated-unit sizing); disable the broad incumbent selection.

## What is DEAD (8 waves, 6 leaks caught — do not revisit)
reversion (all), continuation-as-alpha (regime-beta wash), cross-sectional RV (coverage artifact),
per-symbol routing (fwd-negative), session/DOW (in-sample selection), M1/tick microstructure
(sign-bug + OOS-selection leak), vol-state sizing/timing/exits, pairs/stat-arb, carry, overnight,
aggregate-pockets, all gold enlargements (multi-TF/tick/sessions), the learned per-candidate model
(AUC 0.53), and the two earlier "breakthroughs" (geometry sign bug; 12/12 lookahead gate).
NO second engine, NO broadener, NO diversifier exists in this data.
Universal fact: volatility clustering (ATR autocorr ~0.95) — harvestable only at the entry gate.

## The honest verdict on "the ultimate system"
On FREE MT5 data, the ultimate achievable mechanical system is this one small gold sleeve. It will not
fund an account by itself (~0.02-0.22%/mo). A MATERIALLY bigger system requires DIFFERENT INFORMATION
(real order flow / fundamentals / cross-asset flows) — now proven necessary, not optional. The durable
asset built is the research+audit machine that reliably separates edge from noise (it killed 6 leaks,
including its own).

## Owner decisions needed
1. Deploy the gold sleeve (standalone replacement rule) on a challenge account at what size (0.25% conservative)?
2. Authorize the runtime/broker-authority work (hard-halt forensic join, dual-broker audit, production-return
   dossier) — the real engineering blocker to live, not edge discovery.
3. Greenlight acquiring different data (order flow/fundamentals) for a materially bigger system, post-payout?

## 2026-06-14 THE RIGHT QUESTION — CHALLENGE-PASS PROBABILITY (was sizing for the wrong objective)
I had sized the gold sleeve for perpetual survival (Sharpe/maxDD, ~0.22%/mo) — useless framing for the
actual goal (PASS the challenges / get payouts). Re-ran as P(reach +8% before -5% daily / -10% max,
no time limit), bootstrapping the real audited gold daily-R stream (267 signal-days, +0.051 unit-R/day):
  0.50%/unit: P(pass)=71.3%  fail_maxDD 28.7%  daily-breach 0.0%  median ~117 days
  1.00%/unit: P(pass)=60.3%  fail_maxDD 39.7%  daily-breach 0.0%  median ~33 days
  2.00%/unit: P(pass)=53.0%  fail_maxDD 47.0%  daily-breach 0.0%  median ~10 days
=> The gold sleeve has ~71% chance to PASS one FTMO challenge at 0.5%/unit (0% daily-breach risk).
   Two accounts: ~92% pass >=1, ~50% pass both. THIS is the deployable, account-relevant result.
CAVEATS: gold-concentrated, 4/12 years negative (the 29% failures are real max-DD blowups), ~71% != certainty,
assumes forward resembles the bootstrapped historical distribution. Script: challenge_montecarlo.py.
GO-LIVE PLAN: deploy the gold sleeve (standalone rule) on BOTH challenge accounts at ~0.5%/unit; it is +EV,
no-daily-breach, ~71%/account pass odds. This is the real shot at funding — not a perpetual-Sharpe machine.
