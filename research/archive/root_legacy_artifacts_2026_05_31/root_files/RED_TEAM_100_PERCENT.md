# RED TEAM ESCALATION — Full System Audit

You are Zeta. Today you reviewed batch reports, pipeline outputs, and proposed
changes. You caught real mistakes. But you were reactive — you reviewed what
was handed to you. That stops now.

This is a full-system audit. Not a review of someone else's work. You are
going to find every vulnerability, every gap, every unasked question in the
Gold Traders Operating System. No document needs to be pasted. You already
have the project knowledge. Use it.

---

## PART 1: EXISTENTIAL RISKS NOBODY HAS MITIGATED

### 1.1 — Model Drift (no canary exists)
The entire system runs on Sonnet interpreting "at or near" an OB zone.
Anthropic can update Sonnet without notice. There is currently ZERO
detection for model behavior changes.

**Your task:** Design a canary test suite.
- Select 10 historical MSOs from the backtest data — 5 that should be
  CANDIDATE, 5 that should be NO_TRADE
- These must be clear-cut cases where the correct answer is obvious
- Specify the exact pass/fail criteria: if more than 1 out of 10 flips
  from the known-correct answer, HALT all live trading
- The suite runs before every trading session, takes <60 seconds
- Write the full specification. File path, MSO selection criteria,
  execution script outline, alert mechanism.
- This should have been built before the system went live. It wasn't.
  Fix that.

### 1.2 — No Drawdown Recovery Rule
The system trades 1% risk regardless of equity state. A 7-loss streak
at 1% on FTMO $100K = -$7,000. FTMO max daily loss is 5% ($5,000).
Three bad days could end the challenge.

**Your task:** Design a mechanical drawdown management rule.
- At what drawdown level does risk reduce? (suggest threshold)
- What does risk reduce to?
- At what recovery level does risk restore?
- Must be mechanical — no discretionary "I feel like reducing size"
- Must be coded into permissions.py, not just documented
- Check: does the current system have ANY drawdown-based risk adjustment?
  grep the codebase. If no: flag as CRITICAL.

### 1.3 — Challenge Failure Has No Playbook
$500 challenge fee. If the system fails Phase 1, what happens?
There is no decision tree for failure.

**Your task:** Write the failure playbook.
- Challenge fails in first week (system clearly not working) → action?
- Challenge fails in week 3-4 (close but didn't hit target) → action?
- Challenge fails due to single large loss (fat tail event) → action?
- How many consecutive challenge failures before reassessing the system?
- What's the maximum capital allocated to challenge attempts?

---

## PART 2: THE EXIT LEAK (biggest R-recovery opportunity)

33 timeout trades. Average MFE 1.54R. Average final R 0.90R.
That's 0.64R per trade left on the table. 33 × 0.64 = 21.1R total.

The entire 2026 decay from peak expectancy is roughly 27R.
The exit leak is 78% of the decay.

Nobody has written a single line of code to test a trailing stop.

**Your task:**
- Pressure-test this claim. Is the 0.64R exit leak real or is it
  survivorship bias? Would a trailing stop have also cut winners short
  on the non-timeout trades?
- Design the test: take ALL trades (not just timeouts), simulate a
  trailing stop that activates at 1R MFE with a 0.5R trail. Measure
  total R with vs without.
- Design a second test: fixed TP at 1.5R vs current session timeout.
- Specify which trades to include, what data is needed, what the
  decision gate is (minimum R improvement to justify implementation).
- Flag if anyone has tested this already (check test_results.json).

---

## PART 3: WHAT THE AI IS ACTUALLY DOING (black box risk)

The system treats the AI's CANDIDATE/NO_TRADE decision as a black box.
Nobody has studied what MSO features actually drive the decision.

The confidence score is proven noise (r=-0.02). The grade is inverted
(LOW=75% WR, HIGH=46% WR on n=13). The AI provides reasons in text
but nobody has systematically analyzed whether those reasons correlate
with outcomes.

**Your task:**
- Is there a way to extract the AI's stated reasoning from historical
  evaluations? Check the candle_evaluations JSON for a "reason" field.
- If reasons exist: categorize them. "Strong displacement" vs "clean
  structure" vs "session timing" — which reason categories correlate
  with wins?
- If reasons don't exist in structured form: flag this as a gap.
  The system should be logging WHY the AI takes each trade, not just
  that it did.
- This isn't about building a new feature. It's about understanding
  the one feature that IS the edge.

---

## PART 4: THINGS THAT WERE BUILT TODAY THAT SHOULDN'T HAVE BEEN

Be honest. Review everything built on 2026-04-06 and flag what was
premature, unnecessary, or misallocated effort:

- 13 agents in Claw Empire — how many will produce meaningful work
  in the next 30 days? Name each one and give honest yes/no.
- 4 custom skills — are they wired to anything that runs? Or do they
  sit in files waiting for an orchestrator that doesn't work yet?
- KAP pipeline improvements (Agent 0-4 prompt changes) — the pipeline
  produced 0 implementable changes. Are the improvements to a
  zero-output pipeline worth the effort?
- Shadow logging (orchestrator.py changes) — is this wired, tested,
  and confirmed to produce data? Or is it code that's been written
  but never executed against a live trade?
- The bash orchestrator (run_kap.sh) — it produced 0 bytes of output
  in testing. Is it actually broken? Has anyone fixed it?

For each item: JUSTIFIED / PREMATURE / BROKEN. Be specific.

---

## PART 5: THE FINANCIAL PLAN REALITY CHECK

Run the actual numbers. No optimism, no pessimism.

- Current system at 2026 rates: WR, expectancy, trades/month, R/month
- FTMO Phase 1 requirements vs what the system produces at 1%, 1.5%, 2%
- Probability of passing Phase 1 in 30 days (use the Monte Carlo data)
- Probability of passing Phase 2 in 60 days
- Expected time from today to first payout (realistic range, not best case)
- Monthly income once funded (after FTMO's 80% split)
- What WR does the system need to sustain to remain funded long-term?

If the numbers don't work at current rates, say so. Don't sugarcoat it.

---

## PART 6: WHAT'S ACTUALLY MISSING FROM THE SYSTEM

List every gap you can find. Not improvements — gaps. Things that
should exist but don't:

- Safety systems that are missing
- Monitoring that isn't happening
- Data that isn't being collected
- Tests that haven't been run
- Failure modes that have no response plan
- Dependencies that have no backup

---

## PART 7: PRIORITY STACK

After completing Parts 1-6, produce a single ranked priority list.
Not by "importance" — by expected R-impact per hour of work.

Format:
```
1. [Task] — [Expected R impact] — [Hours to build] — [R per hour]
2. ...
```

The CEO (Borhen) will use this list to decide what gets built tomorrow.
Nothing else matters except this ranked list being correct.

---

## RULES FOR THIS AUDIT

- Do NOT soften findings to be encouraging
- Do NOT skip a section because "it's probably fine"
- Do NOT assume something works because code exists — check if it's
  been tested against live data
- Do NOT recommend building new things before confirming existing
  things work
- If the system is more fragile than everyone thinks, say so
- If the financial plan doesn't work at current rates, say so
- If today's work was mostly misdirected, say so

You are the immune system. This is the full body scan.

Go.
