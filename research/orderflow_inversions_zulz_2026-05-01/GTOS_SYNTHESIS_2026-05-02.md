# GTOS Synthesis - Zulz Orderflow Inversions Research Pack

Date: 2026-05-02
Merge commit: `bcf1865 research: merge Zulz orderflow research pack`
Scope: Research only. No live trading logic, prompt, config, or execution changes.
Verdict: Research-worthy orderflow-awareness track. No production promotion.

## Evidence Reviewed

Sources reviewed in the merged pack:

- `README.md`, `MODEL_SPEC.md`, `CONSTRAINTS.md`, `KEY_QUOTES.md`
- 11 Whop product-description files under `product_descriptions/`
- Transcript index, aggregate transcript file, and individual transcript files under `transcripts/`
- 67 image assets under `images/`, including original-resolution representative full-layout, footprint, and VP/heatmap screenshots

The public pack is enough to reconstruct the model's conceptual logic. It is not enough to reproduce exact quantitative rules because the gated Discord/library and SierraChart chartbook parameters are missing.

## Core Synthesis

The Zulz model is not magic and not a new market law. It is a packaging of standard auction/orderflow primitives into one repeatable workflow:

1. Find a precise level using volume profile, most often a low-volume node inside or near a fair-value gap.
2. Wait for price to deliver to that level, often around the first VWAP standard deviation of the active session.
3. Confirm that the first side is trapped or absorbed on the footprint.
4. Enter when aggressive opposite-side flow appears and price reclaims/inverts the VWAP deviation.
5. Target visible resting liquidity / next heatmap level / next VWAP deviation / HTF volume-profile node.

His strongest technical claim is "LVN > FVG": the FVG is treated as a broad imbalance zone, while the LVN inside it is treated as the precise reaction level. That claim is plausible and directly testable.

The model does not publicly use GTOS-style order blocks or breakers. Across the pack, the repeated primitives are LVN, VWAP deviation, footprint absorption, delta shift, large trade bubbles, stacked imbalances, CVD, and heatmap resting liquidity. It is therefore best interpreted as a microstructure qualification layer, not a replacement for the existing structure engine.

## Honest Assessment

I agree with the user's instinct on one important point: orderflow can add real market-state awareness. If we can see where volume accepted, where it did not, where aggressive flow failed, where resting liquidity sits, and whether price is moving through a low-volume path, then entries, exits, and path-scaling decisions can become more informed than OHLC-only logic.

I disagree with the stronger marketing form: this does not let us "know exactly" what institutions or algorithms plan to do. Orderflow is still noisy, spoofable, venue-specific, and often ambiguous. It shows evidence of current auction behavior, not guaranteed intent. A large buyer can be initiating, hedging, absorbing, rebalancing, or spoofing. The chart can suggest who is trapped; it cannot prove motive.

The right framing for GTOS is:

- Good: orderflow may help identify whether a structural level is being defended, rejected, absorbed, or ignored.
- Good: it may improve target selection by locating liquidity pools and volume voids instead of relying only on fixed R paths.
- Good: it may reduce same-bar/path ambiguity by giving sequence inside the candle.
- Dangerous: using it as a story engine can create false confidence unless every rule is converted into measurable events and tested out of sample.

## What Is Likely Real

High-confidence useful primitives:

- LVN precision: a low-volume pocket inside a broad FVG/imbalance can be a better reaction coordinate than the whole zone.
- VWAP deviations: session VWAP bands are meaningful intraday auction references, especially around RTH/ETH session boundaries.
- Absorption: large aggressive volume that fails to move price is a real microstructure event.
- Delta shift: failed aggression followed by opposite aggressive flow is a plausible timing trigger.
- Volume voids: price can travel faster through low-volume areas because fewer prior participants are anchored there.
- Liquidity targets: resting depth / HVNs / POCs can act as magnets, though depth can be pulled.

Medium-confidence but unproven:

- "First VWAP deviation reclaim" is the correct universal trigger.
- 2000-trade footprint bars are optimal across NQ, ES, GC, CL, and YM.
- Heatmap targets improve realized R after fees/slippage.
- The same setup transfers cleanly from CME futures to MT5 CFDs via proxies.

Low-confidence / marketing:

- "Permanent" edge.
- Works the same on every market.
- "No subjectivity" in public form. The missing rules still leave substantial discretion.
- Public performance evidence. The pack has anecdotes, not an auditable track record.

## Translation To GTOS

Directly useful without paid futures depth:

- Session VWAP and standard deviations from local bars/ticks.
- Volume-profile LVN/HVN/POC from available volume or tick-volume data.
- FVG/LVN overlap tests.
- VWAP deviation reclaim tests.
- Tick-derived CVD proxy from bid/ask movement.
- Absorption proxy: high tick activity or volume near a level with low price progress.
- Volume void / low-volume path metrics for target selection.

Needs better data:

- True footprint bid/ask aggressive volume.
- True large-trade bubbles / print size.
- True depth heatmap and resting liquidity.
- Reliable 2000-trade bars.
- CME futures proxy alignment for XAUUSD/NAS100/US30.

The hard translation problem is that GTOS trades MT5 symbols, while the Zulz workflow depends on centralized CME futures data. For XAUUSD, the closest source is GC. For NAS100, NQ. For US30, YM or possibly ES as index proxy. FX pairs have no centralized futures-equivalent depth that maps cleanly to spot/CFD flow.

## Best Fit In The Program

The best use is not to replace V2/V3 structural research. The best use is to create an orderflow-awareness research track that can later condition structural events:

- Entry timing: do not enter just because price touches a level; require trap/absorption/reclaim evidence.
- Candidate filtering: reject structural signals where orderflow shows acceptance through the level instead of rejection.
- Path scaling: lock/release based on whether pullbacks show adverse absorption or supportive absorption.
- Targeting: use next liquidity/HVN/VWAP deviation rather than fixed R-only exits.
- Ambiguity resolution: use sub-M15 orderflow sequence to resolve same-bar wick/target/stop uncertainty.

This connects directly to what V0/V1/V2 taught us: OHLC structure alone can describe the level, but it often cannot describe the auction quality at the level.

## Structural Event Universe To Test

The following event families should be considered before narrowing the research:

- LVN inside FVG
- LVN at FVG boundary
- LVN at order block boundary
- LVN at breaker / mitigation level
- LVN at prior session high/low
- LVN at overnight high/low
- LVN at VWAP deviation
- LVN at composite/session volume-profile edge
- HVN/POC magnet into target
- Volume void between entry and target
- Failed auction high/low
- Poor high/poor low
- Single-print / low-participation zone
- VWAP reclaim after deviation sweep
- VWAP deviation rejection without reclaim
- VWAP hold continuation
- VWAP loss after reclaim as invalidation
- Absorption at high/low
- Absorption at LVN
- Absorption against existing GTOS direction
- Absorption supporting existing GTOS direction
- Delta divergence at level
- CVD divergence at level
- Stacked imbalance in entry direction
- Stacked imbalance exhaustion against entry direction
- Large trade bubble with no price progress
- Large trade bubble followed by continuation
- Large trade bubble followed by reversal
- Heatmap liquidity fill
- Heatmap liquidity pull
- Heatmap liquidity reload
- Sweep of resting liquidity followed by reclaim
- Depth imbalance near level
- Cross-market lead/lag: NQ vs ES, YM vs ES, GC vs DXY, CL vs ES, DXY vs ES
- News shock pullback to first VWAP deviation
- Post-open first 90-minute orderflow inversion
- Late-session random-volume failure mode

Not every family is likely to survive. The value of the broad list is to avoid prematurely reducing the problem to "LVN + VWAP" if a deeper interaction is the real signal.

## Registered Hypotheses For Next Research

These should be registered before testing:

1. LVN-inside-FVG reaction quality is better than broad FVG reaction quality.
   Metric: MFE/MAE, hit rate to next opposing level, time-to-reaction.

2. LVN touch plus VWAP-deviation reclaim outperforms LVN touch alone.
   Metric: forward 5/15/30-minute return and stop-before-target frequency.

3. Absorption plus delta shift improves entry timing versus price-only reclaim.
   Metric: adverse excursion after entry and target-before-stop sequence.

4. Heatmap/resting-liquidity targets outperform fixed-R targets when true depth is available.
   Metric: realized R, giveback, missed continuation, slippage.

5. Orderflow features improve GTOS structural candidate selection.
   Metric: conditional expectancy of existing OB/FVG/breaker candidates with and without orderflow confirmation.

6. Orderflow features improve path-scaling decisions.
   Metric: lock/release outcome versus V1/V2 path engines on the same full-corpus events.

7. Futures orderflow proxies transfer to GTOS CFD instruments only when basis/correlation is stable.
   Metric: proxy/CFD lead-lag correlation, level-touch timing delta, directional agreement at event time.

8. Trade-count bars outperform time bars for footprint triggers.
   Metric: trigger latency, false-trigger rate, and forward return stability across instruments.

## Ambiguity Ledger

Blocking ambiguities:

- Exact stop placement is not disclosed.
- Exact invalidation rule is only partially public: one clip says reclaim-level break means "I'm done."
- Exact VWAP deviation multiplier is unknown.
- Exact session VWAP split rules are unknown beyond ETH/RTH wording.
- Exact large-volume bubble threshold is unknown.
- Exact heatmap threshold settings are unknown.
- Exact footprint tick/trade compression per instrument is unknown. The pack mentions 2000-trade bars, but a reviewed ES image shows 3000 trades, so the rule is instrument/template dependent.
- Exact LVN source is ambiguous: session VP, composite VP, HTF VP, overnight profile, or local profile.
- Exact definition of "reclaim" is unknown: intrabar cross, bar close, footprint bar close, or sustained hold.
- Exact definition of "aggressive buyers/sellers show up" is unknown.
- Exact target-ranking logic is unknown when multiple liquidity/VWAP/profile targets exist.
- Exact rule for when a heatmap level is valid versus spoofed/pulled is unknown.
- Exact cross-correlation lookback and threshold are unknown.
- Exact news-day size and target rules are discretionary in public clips.

Non-blocking but important:

- Product descriptions have copy-paste artifacts across NQ/ES/GC. That weakens trust in marketing precision, not necessarily in the underlying concepts.
- Public clips show selected examples, not a statistically representative sample.
- Public evidence does not prove profitability.
- The Discord/library may contain stronger rules, but it is gated.

## Threats And Failure Modes

- Venue mismatch: CME futures flow may not translate to MT5 CFDs cleanly.
- Depth spoofing: resting liquidity can be pulled; heatmap targets can be deceptive.
- Classification error: without aggressor flags, tick-derived delta can be wrong.
- Lookahead risk: volume profile and heatmap levels must be computed only from information available at event time.
- Parameter mining: thresholds for absorption, LVN width, VWAP bands, and heatmap strength are easy to overfit.
- Story bias: "trapped buyers/sellers" is a useful label but must become an objective event definition.
- Cost sensitivity: better timing can disappear after spread/slippage if entries are late.
- Sample-size trap: orderflow events are narrower than OHLC events; significance will take time.

## Data Path Options

No-paid path:

- Use existing MT5 tick capture and historical OHLC.
- Build degraded VWAP/LVN/volume-void/absorption proxies.
- Treat results as feasibility only, not proof of true orderflow edge.

Best research path:

- Capture CME futures data for GC/NQ/ES/YM/CL with tick, bid/ask, volume, and depth.
- Export from SierraChart or use a broker/feed API if available.
- Build an event-level dataset with strict timestamping and no lookahead.
- Map futures events to GTOS CFD symbols and measure transfer quality.

Cheapest ambiguity-closing path:

- Use the free Premium Discord code if still active to inspect setup-library/live breakdowns.
- Do not treat Discord claims as performance evidence.
- Extract only rule definitions, not proprietary redistribution.

Paid parameter path:

- Buy the smallest relevant chartbook only if exact SierraChart settings are needed.
- The chartbook would likely reveal indicator settings but not performance truth.

## Recommended Next Steps

1. Register an `OF-0` research spec defining the event taxonomy and no-leak rules before looking at outcomes.
2. Build a no-paid prototype over existing MT5 ticks: VWAP deviations, local VP/LVN proxy, volume voids, reclaim events, and absorption proxy.
3. Run a small feasibility audit: do the features generate stable, timestampable events at all?
4. If feasible, run an event study on full available captured corpus with cost sensitivity and same-bar/path diagnostics.
5. In parallel, decide whether to use the free Discord route to close missing rule definitions.
6. Do not buy chartbooks or subscriptions until the no-paid prototype proves the concepts are measurable in our environment.
7. If true depth becomes available, create `OF-1` using CME futures data and repeat the event study with proper footprint/depth features.
8. Only after `OF-1` evidence exists, test integration against GTOS candidates and V2/V3 path-scaling logic.

## Bottom Line

This is worth pursuing, but only as a measured orderflow-awareness research track. The correct thesis is not "Zulz has a permanent model." The correct thesis is:

> Microstructure features may improve GTOS by telling us whether a structural level is being accepted, rejected, absorbed, or targeted in real time.

That thesis is coherent, testable, and aligned with the current research direction. It also has serious data and methodology constraints. The next move should be a registered, no-promotion, no-leak feasibility study, not a live-system change.
