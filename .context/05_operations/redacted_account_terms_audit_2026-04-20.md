# redacted_account Stellar 2-Step $100K — Terms Audit (2026-04-20)

**Auditor:** Claude Code (Opus 4.7, max effort)
**Date of capture:** 2026-04-20
**Kickoff target:** 2026-04-21 (Tuesday)
**Product under audit:** redacted_account Stellar 2-Step, $100,000 size, CFD track (MT5)
**Methodology:** redacted_account primary sources (`redacted_account.com/stellar-model`, `redacted_account.com/plan`, `redacted_account.com/cfd-challenge-terms`) with cross-verification against redacted_account Help Center articles and 3rd-party reviews (PropTradingVibes, TradingFinder, PropFirmsFinder, Forex Prop Reviews). Where marketing page and T&C legal text disagreed, I note it.
**Scope:** 16 terms requested by CEO.

---

## TL;DR

1. **Phase 1 target is 8%, not 10%** — confirmed on both the marketing page (`/stellar-model`, `/plan`) AND the legal CFD Challenge Terms (`/cfd-challenge-terms`, Section 5.4). The Chairman audit was right, the verbal "10%" assumption is wrong. **This is the single biggest correction.** At 8%, our required net profit is $8,000 (not $10,000), so the challenge is 20% less hard than we were budgeting.
2. **XAUUSD leverage is 1:30 on the challenge, dropping to 1:5 on the funded account (HIGH risk to our sizing model).** FX (USDJPY, GBPJPY, GBPUSD) stays at 1:100. US30/indices is 1:30 on challenge, 1:5 on funded. Secondary sources all agree; the primary help-center page was not directly fetchable (WebFetch denied) but three independent reviews reporting April-2026 snapshots converge on the same numbers. Post-pass we will need ~6× more margin per ounce of gold — must validate our position-sizing code against this *before* we become funded, not after.
3. **News trading is ALLOWED but profit-split-penalised in a ±5 min window around listed high-impact news (40% of profit counts; 100% of loss).** Our GTOS currently has no blackout. This is a 10-min window per event — material for red-folder USD/EUR/GBP/JPY events. Decision needed: add blackout, or accept the 60% profit haircut on news-overlap trades.
4. **No consistency rule for CFD.** Confirmed explicitly by FN help center. Unlike FTMO-style firms, we can take uneven daily P&L distributions. Only Futures has a 40% consistency rule — irrelevant to us.
5. **EA/bots explicitly allowed**, with one important caveat: no duplicate strategies across accounts, no copy trading between accounts, max $300K allocation per single EA strategy. Single algo on single account is green-lit. Several secondary sources mention an "additional EA usage fee" — I could not verify this on primary source; **flag for manual check at purchase**.
6. **No time limit, no max trading days, weekend holding allowed during challenge** — all good. But **weekend holding is prohibited on the funded account** (post-pass). Another post-pass config change.
7. Daily loss is **full equity-basis including floating** (mid-session drawdown, not end-of-day). 00:00 server-time reset. Baseline is initial balance ($5,000), buffered upward by *today's* realized profit. Confirms our drawdown manager semantics.
8. Prohibited strategies list: **order-block retest / breakout is NOT on the prohibited list**. Our strategy is safe. But grid, martingale (EA-based martingale exempt, but human martingale not explicit), latency, arbitrage, tick scalping, HFT, copy trading across accounts, gambling, one-sided betting, hyperactivity are all prohibited.

**Bottom-line recommendation:** update `config/profiles/redacted_account.yaml` targets to 8% Phase 1, add leverage constraints per-symbol, decide on news-blackout policy, and mark weekend-holding as a post-pass rule to switch on. Confidence on every numeric claim in this doc is summarised in the Source Quality column of the audit table below.

---

## Per-term audit

| # | Term | GTOS-assumed (per CEO brief) | redacted_account-actual | Source(s) | Confidence | Match? |
|---|------|------------------------------|-------------------|-----------|------------|--------|
| 1 | Phase 1 profit target | 10% (per CEO verbal) / 8% (per Chairman audit) | **8%** ($8,000 on $100K) | `redacted_account.com/stellar-model` + `redacted_account.com/plan` + `redacted_account.com/cfd-challenge-terms` §5.4 + Help Center art. 8021071 | HIGH (primary + legal) | ✗ (if CEO's 10% was codified) / ✓ (if Chairman's 8% was codified) |
| 2 | Phase 2 profit target | 5% | **5%** ($5,000 on $100K) | Same as #1 | HIGH | ✓ |
| 3 | Max daily loss | 5% | **5%** of initial balance ($5,000 on $100K). Includes floating/open P&L + swaps + commissions (mid-session basis, NOT end-of-day). Daily limit increases by today's realized profit, but resets to 5%-of-initial at 00:00 server time. Breach = account paused until manual reset. | `redacted_account.com/stellar-model` + T&C §5.1 + Help Center art. 8019811, 8019914, 9941519 | HIGH | ✓ |
| 4 | Max total / overall loss | 10% | **10%** of initial balance ($10,000 on $100K). **Static**, not trailing. Calculated on initial balance; account must not drop below $90,000 at any point. Includes commissions/swaps/charges. | `redacted_account.com/stellar-model` + T&C §5.2 + Help Center art. 8019812, 8019915 | HIGH | ✓ (but confirm "static not trailing" in our config) |
| 5 | Minimum trading days | 5 | **5** separate trading days per phase, **1 trade minimum per day**. | `redacted_account.com/stellar-model` + T&C §5.3 + Help Center art. 8021076, 8021077 | HIGH | ✓ |
| 6 | Maximum trading days / time limit | None | **None** — unlimited time to complete both phases. | `redacted_account.com/stellar-model` ("No time limit in Challenge Phase") + Help Center art. 8021073 | HIGH | ✓ |
| 7 | Consistency rule | None (assumed) | **None for CFD.** Confirmed explicitly. (40% consistency rule exists only on Futures side, not applicable to us.) | Help Center art. 12673362 + PropTradingVibes 2026 review | HIGH | ✓ |
| 8 | Weekend holding | Allowed (assumed) | **Allowed during the Challenge phase.** PROHIBITED on funded account after passing. Marketing page explicitly: "Hold your trades as long as you want, even on weekends." | `redacted_account.com/stellar-model` + Help Center art. 11982358, 11641232 | HIGH | ✓ for challenge; flag for post-pass |
| 9 | News trading | Allowed, no blackout (assumed) | **Allowed**, but **News Profit-Split Rule** applies: 5 min before + 5 min after any listed high-impact news event (10-min total window), only **40% of profit** counts toward balance; **100% of losses** apply. Only when the news pair directly correlates with the traded instrument (e.g., USD news affects USDJPY/GBPUSD/XAUUSD; EUR news does not). Partial closes inside the window taint the entire trade. | Help Center art. 9430390, 10701447, 10701685 | HIGH (secondary aggregation of help-center) | ✗ (we have no news-window handling) |
| 10 | EA / bot / algo policy | Allowed (assumed) | **Allowed** for Stellar 2-Step on MT4/MT5. Constraints: (a) no duplicate strategies across accounts, (b) no copy trading between accounts not owned by same individual, (c) max $300K capital per single EA strategy. Some sources mention an "additional EA usage fee" — NOT FOUND on primary source, verify at account purchase. | Help Center art. 8020763, 8388896 + PropTradingVibes 2026 | HIGH on "allowed"; MEDIUM on "additional fee" claim (unverified primary) | ✓ with caveat |
| 11 | Challenge fee + refund | ~$549 (assumed) | **$549.99** for $100K Stellar 2-Step. Fully refundable ("Passing Reward") **with first payout** (requires completing both phases + KYC + first Performance Reward request). Note: T&C §10.3 also gives a 7-day purchase refund if NO trading occurred; once you trade, fee becomes tied to the Passing Reward pathway. | `redacted_account.com/stellar-model` + `redacted_account.com/plan` + T&C §10.3–10.4 + Help Center art. 8020087, 8020256, 9430506 | HIGH | ✓ |
| 12 | Profit split + payout cycle | 80% / 90% / unknown cadence | **Starts at 80%**, increasing to 90% over time with consistent payouts, max 95% with add-ons. First Performance Reward: **after 21 days** from receiving funded account. Then **bi-weekly (every 14 days)**. Minimum withdrawal $250 for Performance Reward; payouts processed within 24h. | `redacted_account.com/stellar-model` ("Up to 95%") + Help Center art. 8020768, 10701585 + QuantVPS payout rule breakdown | HIGH on 80%/95%; HIGH on 21d+14d cadence | ✓ (but confirm our cadence assumption) |
| 13 | Leverage — XAUUSD | Not specified in brief | **Challenge: 1:30.** **Funded: 1:5** (so-called "temporary" since months prior to April 2026, no announced end date). Applies to all commodities/metals/indices/oil. | Help Center art. 8019669 (indirect via search) + PropTradingVibes Apr 2026 + TradingFinder Apr 2026 | MEDIUM-HIGH (primary help-center not directly fetchable; three independent Apr-2026 sources converge) | ✗ (need per-symbol leverage overlay in our profile) |
| 13b | Leverage — FX (USDJPY, GBPJPY, GBPUSD) | Not specified in brief | **1:100** on both Challenge and Funded. | Same as above | HIGH | ✓ (standard FX leverage) |
| 13c | Leverage — US30 / indices | Not specified in brief | **Challenge: 1:30. Funded: 1:5.** Same as commodities. | Same as above | MEDIUM-HIGH | ✗ (same issue as XAUUSD) |
| 14 | Broker spread expectations | Not specified | Raw spreads from 0.0 pips + **$5 per lot commission** on Forex CFDs (MT5). **XAUUSD-specific spread NOT FOUND** in a numeric range on FN help center. Typical 3rd-party reports: 0.2-0.5 pip on major FX; XAUUSD tends to run 15-35 cents raw. Must confirm live at demo account setup. | Help Center art. 8224118 + MT5 live demo check required | LOW-MEDIUM (generic; no XAUUSD-specific) | Unknown |
| 15 | Prohibited strategies | (Implicit: our OB retest is fine) | Explicit prohibited list: **gambling, all-in-one, quick-strike, HFT, copy trading across accounts, group hedging, arbitrage, tick scalping, grid, latency, account rolling, one-sided betting, hyperactivity, exploiting demo server errors, low-liquidity guaranteed profit, account/device sharing.** Hedging **within the same account** is allowed. Martingale is explicitly carved out: "no limitations on trader's strategy, whether it involves discretionary trading or EAs that employ martingale" — so martingale is NOT prohibited. Order-block retest / breakout / trend-following are NOT on the list. | Help Center art. 8020351, 8388896 | HIGH | ✓ (our strategy is safe) |
| 16 | Payout / withdrawal minimums | Not specified | Performance Reward minimum: **$250** (required to accumulate $500 profit before first request). Smallest payout: US$20 (USDT TRC20) / US$50 (other methods). Max per single request: **US$4,999**. Payouts processed within 24h. | Help Center art. 10701585 (via search) + QuantVPS breakdown | MEDIUM-HIGH (consistent across 3+ 2026 sources) | Unknown |

---

## Flags for CEO (delta from assumed / action-required)

1. **PHASE 1 TARGET = 8%, NOT 10%.** Update `config/profiles/redacted_account.yaml` if it currently encodes 10%. Do NOT trade to a 10% target and stop at 10% — that's 25% more drawdown exposure than needed. Exit Phase 1 at or near 8% ($8,000) to minimise variance risk.
2. **LEVERAGE ON XAUUSD + US30 IS 1:30 ON CHALLENGE, 1:5 POST-PASS.** This is a *hard* broker-side constraint. Implications:
   - Challenge phase: at 1:30 on gold at $3,300/oz, 1 lot (100 oz) = $330,000 notional → needs ~$11,000 margin. On $100K account with 5% daily-loss cap = $5,000, you cannot put on more than ~0.45 lots of gold at 1:30 before margin exceeds daily-loss headroom. Sanity check our typical position size against this; if we're routinely sizing <0.3 lots we are safe.
   - Post-pass: 1:5 means ~$66,000 margin for 1 lot of gold on a $100K account — impossible to run full size. Position sizing code needs a per-symbol leverage table and must NOT assume 1:100 on XAUUSD/US30 when we transition to funded.
   - FX (USDJPY, GBPJPY, GBPUSD) unaffected; stays 1:100 throughout.
3. **NEWS-WINDOW PROFIT HAIRCUT (5 min ± high-impact).** GTOS currently has no news blackout. Options: (a) add a ±5-min blackout around ForexFactory red-folder events, (b) accept the 40% profit retention during those windows. Given our ~17 trades/month expected frequency, collisions will be rare but not zero. Recommend a soft blackout (no new entries, existing positions unchanged) rather than forced flatten — lets live positions ride without a flatten-induced slippage penalty.
4. **WEEKEND HOLDING FLIPS POST-PASS.** Allowed during challenge, prohibited on funded account. Needs a profile-level `phase` flag and a Friday-close enforcer for the funded account phase.
5. **NO CONSISTENCY RULE.** Good. We can have a single big day account for 80% of total profit without penalty — unlike FTMO where some interpretations cap this. Exploit freely if the edge appears concentrated.
6. **"EA USAGE FEE" unverified.** Secondary sources claim redacted_account charges an additional fee for EA use; I could not confirm this on primary source (WebFetch denied to help.redacted_account.com). CEO should ask support directly at account purchase — a $30-50/month EA surcharge is common across prop firms, and if present affects our budget math.
7. **DAILY LOSS IS MID-SESSION (equity-basis with floating), not EOD.** Our current drawdown manager and H29 8%-DD reduction are both based on equity, so this matches — but double-check that `drawdown_manager.py` does NOT wait until candle-close or EOD to trigger. The break happens live on floating P&L, the second it crosses 5%.
8. **T&C §10.3 — 7-day non-trading refund window.** If we want to back out of the purchase decision after inspecting the live demo on 2026-04-21 but before placing any trade, we have 7 days. Useful escape hatch if live spreads / symbol availability look materially wrong.
9. **redacted_account "reserves the right to modify programme parameters" for future purchases (T&C §2+).** Since our challenge is purchased at the current terms, those lock for our account. But if we buy a second challenge later, re-audit. (The 2026 Legacy $50K profit-target bump from 2500→3000 is an example of them changing terms on new purchases only.)

---

## Items flagged NOT FOUND / unverified

- **XAUUSD-specific spread range.** FN help center discusses generic "raw spreads from 0.0 pips + $5/lot commission" but does not publish a per-symbol spread table. Will be visible on the demo MT5 terminal immediately on 2026-04-21.
- **"EA usage fee"** claim (Myfxbook / PropTradingVibes secondary). Not confirmed on any FN primary URL I could reach. Ask FN support at account purchase.
- **Primary-source leverage help-center page** (help.redacted_account.com/.../8019669) was not directly fetchable via WebFetch (permission denied to subdomain); leverage numbers rely on WebSearch extraction + 3rd-party April-2026 reviews. Three independent sources converge so confidence is MEDIUM-HIGH, but CEO should sanity-check in the FN dashboard after login.
- **CFD Challenge Terms §5.6 consistency clause** mentions "Express Model consistency requirements" — I could not verify whether this inadvertently drags the Stellar 2-Step into any residual consistency check. Help center unambiguously says no consistency rule for Stellar 2-Step CFD; treat §5.6 as applying only to Express. If FN dashboard shows any "consistency" warning on our account, raise a support ticket immediately.

---

## Sources (fetched 2026-04-20)

Primary (redacted_account domain):
- https://redacted_account.com/ — homepage, general navigation
- https://redacted_account.com/stellar-model — Stellar Challenge product page, numeric summary table (WebFetch: SUCCESS, clean extract)
- https://redacted_account.com/plan — pricing/plans page (WebFetch: SUCCESS)
- https://redacted_account.com/cfd-challenge-terms — legal CFD Challenge Terms (WebFetch: SUCCESS, structured extract confirmed §5.4 profit targets, §5.1–5.2 loss limits, §5.3 trading days, §10.3–10.4 refund policy)

Secondary (redacted_account help center — accessed via WebSearch because WebFetch was denied for the `help.redacted_account.com` subdomain):
- Art. 8021071 — profit target Stellar 2-Step
- Art. 8021076 — Stellar 2-Step rules summary
- Art. 8021073 — Phase 1+2 time allowance
- Art. 8021077 — 5-day minimum
- Art. 8019811 / 8019812 — DLL / MLL calculation
- Art. 8019914 / 8019915 — DLL / MLL definitions
- Art. 9941519 — DLL vs MLL comparison
- Art. 12673362 — Stellar 2-Step CFD rules (includes consistency clarification)
- Art. 11982358 — overnight holding
- Art. 11641232 — Stellar Instant overnight/weekend (used for comparison)
- Art. 8020763 — EA allowed
- Art. 8388896 — strategy restrictions
- Art. 8020351 — prohibited strategies list
- Art. 9430390 / 10701447 / 10701685 — news trading Stellar 2-Step
- Art. 8019669 — leverage (indirect, via search excerpts)
- Art. 8020768 — profit split
- Art. 10701585 — Performance Reward cadence
- Art. 8020087 / 8020256 — fee refund policy
- Art. 9430506 — Passing Reward cadence

Third-party 2026 reviews (cross-verification only, not as primary source for numerical claims):
- https://proptradingvibes.com/blog/redacted_account-rules (April 2026)
- https://proptradingvibes.com/blog/redacted_account-stellar-1-step (April 2026)
- https://proptradingvibes.com/blog/redacted_account-account-types (April 2026)
- https://proptradingvibes.com/prop-firms/redacted_account (April 2026)
- https://www.proptradingvibes.com/blog/redacted_account-evaluation-mistakes (April 2026)
- https://www.proptradingvibes.com/blog/redacted_account-risk-management (April 2026)
- https://tradingfinder.com/props/redacted_account/ (March 2026)
- https://tradingfinder.com/props/redacted_account/rules/ (2026)
- https://propfirmsfinder.com/prop-firm/redacted_account/ (2026)
- https://forexpropreviews.com/redacted_account-stellar-challenges-overview/ (2026)
- https://www.quantvps.com/blog/funded-next-forex-payout-rules (2026)
- https://www.quantvps.com/blog/funded-next-payout-rules (2026)

**Point-in-time caveat:** redacted_account has documented their right to change terms for future purchases. The numbers above reflect the public-facing terms as of 2026-04-20. Before the 2026-04-21 kickoff purchase, do a final dashboard sanity-check after login — the account's displayed parameters are the binding ones per T&C §5.
