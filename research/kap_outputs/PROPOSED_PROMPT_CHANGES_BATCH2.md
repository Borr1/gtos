# PROPOSED PROMPT CHANGES — Batch 2 (2026-04-06)
# Source: Agent 0 Scout session — post-87-video collection review
# Status: PENDING REVIEW

---

## EXECUTIVE SUMMARY

After collecting 87 videos and reviewing all 5 agent prompts, here are the changes
that would extract the MOST additional value from the pipeline. Ordered by impact.

---

## 1. AGENT 2 (Comprehension) — HIGHEST IMPACT

### Problem
Agent 2 extracts individual claims but misses **relationships between variables**,
which is where the real tradeable edges live. "OBs work" is a claim. "OBs work
72% in London but only 55% in NY when H4 is aligned" is an edge.

### Change 1A: Add CORRELATION_CLAIM category

After the existing 6 categories, add:

```
**CORRELATION_CLAIM** — Relationships between two or more variables
- "When X happens, Y is more/less likely"
- Conditional performance: "Strategy X works better during Y conditions"
- Time correlations: "After event A, B tends to happen within N candles"
- Multi-factor: "Win rate improves from X% to Y% when filter Z is added"
- Cross-asset: "When DXY does X, gold tends to do Y"
- Example: "Silver Bullet win rate jumps from 60% to 78% when there's a prior HTF liquidity sweep"

THIS IS THE MOST VALUABLE CATEGORY. Every video has these buried in casual
remarks. When someone says "I noticed it works better in trending weeks" —
that's a CORRELATION_CLAIM. Extract it. Tag the two variables.
```

### Change 1B: Add "variables" field to claim JSON

```json
{
    "claim": "...",
    "category": "...",
    "variables": ["session_time", "ob_body_ratio"],  // NEW — what variables are involved
    "conditional_on": "H4 trend aligned",             // NEW — what condition makes it work
    ...
}
```

### Change 1C: Add explicit instruction to mine for conditionals

Add to section "5. WHAT TO EXTRACT":

```
- ANY conditional statement ("works better when", "only if", "except during",
  "higher probability after") → EXTRACT as CORRELATION_CLAIM. These are the
  highest-value extractions. A trader saying "this works better on Tuesday
  through Thursday" is giving you a testable edge filter for FREE.
- When a speaker compares two approaches and one wins → EXTRACT both the
  winner AND the comparison. "OTE beats Silver Bullet in ranging markets" tells
  us about BOTH strategies.
- When a speaker shows their journal/statistics breakdown by day, session, or
  condition → EXTRACT EVERY breakdown number, even if they mention it casually.
```

### Change 1D: Cross-video awareness

Add instruction:

```
If you process multiple videos in sequence, note when two different speakers
make the SAME claim independently. Add a field:
    "cross_video_corroboration": true/false
    "corroborating_videos": ["video_03", "video_07"]

Independent corroboration from different sources is the strongest signal
that something is real.
```

---

## 2. AGENT 3 (Filter) — HIGH IMPACT

### Problem
Agent 3 is too strict on filtering and misses the value of PATTERN DETECTION
across videos. If 4 out of 87 videos independently mention "Tuesday-Thursday
outperforms Monday/Friday", that's WAY more valuable than a single novel claim.

### Change 2A: Add CONVERGENT_EVIDENCE category

Currently novelty is: NOVEL, REDUNDANT, CONTRADICTORY, COMPLEMENTARY.

Add:

```
**CONVERGENT** — Multiple independent sources make similar claims
- 2+ videos from different channels making the same claim
- Higher confidence than any single NOVEL claim
- Assign priority boost: +1 for 2 sources, +2 for 3+ sources
- This is the closest thing to "peer review" in YouTube content
```

### Change 2B: Add cross-video pattern detection pass

After processing all individual videos, add:

```
## CROSS-VIDEO ANALYSIS PASS

After all videos are filtered individually, do ONE final pass:
1. Group all claims by topic/variable
2. Look for clusters where 2+ videos say the same thing
3. Look for CONTRADICTION clusters (most valuable — tells you the answer is nuanced)
4. For each cluster, create a META-FINDING with all sources listed
5. Rank meta-findings higher than individual findings

This is the highest-value output Agent 3 can produce. A single video saying
"London beats NY" is anecdotal. Three videos independently saying it is a
research lead. Two videos DISAGREEING about it is a confirmed research priority.
```

### Change 2C: Track "belief frequency" in the ecosystem

```
Count how many videos promote each SMC/ICT belief. If 10/87 videos claim
"bigger OBs are better" but our data says body size is NULL (p=0.97), that's
a HIGH-VALUE contradiction because it means most traders are using a broken filter.
The more popular a false belief, the more edge in knowing it's false.
```

---

## 3. AGENT 4 (Strategist) — MEDIUM-HIGH IMPACT

### Problem
Agent 4 designs tests but doesn't RUN them. And it doesn't combine findings
into composite strategies.

### Change 3A: Actually RUN the test scripts

Add instruction:

```
After writing each test script, ACTUALLY RUN IT if the data files exist locally.
Don't just design the test — execute it and report the results inline.
If the data doesn't exist, note what data is needed and where to get it.
A test that runs and gives a p-value is 100x more valuable than a test script
sitting in a file.
```

### Change 3B: Composite strategy synthesis

Add section:

```
## COMPOSITE STRATEGY SYNTHESIS

After ranking individual findings, look for COMBINATIONS that could create
a new strategy or improve the existing one:

1. Can any confirmed finding be used as a FILTER on existing trades?
   (e.g., if Tuesday-Thursday is confirmed, add day filter)
2. Can any two findings be COMBINED into a multi-condition entry?
   (e.g., OB retest + IFVG + session timing = higher probability)
3. Do any findings suggest a NEW strategy entirely?
   (e.g., ORB + volume profile on gold = different approach worth testing)

Output a "STRATEGY_SYNTHESIS" section in the batch report with:
- Proposed composite strategies
- Expected improvement (based on individual finding effect sizes)
- Test plan for the composite
```

### Change 3C: Expected value calculation

```
For each finding, calculate rough expected value impact:

EV_impact = (current_trades_per_month * improvement_in_WR * avg_R * risk_per_trade)

Even a rough estimate helps prioritize. A finding that could improve WR by 5%
on 20 trades/month at 1R average is worth: 20 * 0.05 * 1R = 1R/month.
A finding that adds a filter reducing trades from 20 to 12 but improving WR
from 65% to 80% might be: 12 * 0.80 * 2R - 12 * 0.20 * 1R = 16.8R vs
20 * 0.65 * 2R - 20 * 0.35 * 1R = 19R. The math matters.
```

---

## 4. AGENT 1 (Extractor) — MEDIUM IMPACT

### Problem
Agent 1 only gets transcripts. Video descriptions often contain key data
(backtest spreadsheets, specific numbers, strategy rules) NOT in the transcript.

### Change 4A: Extract video description too

```
For each video, also extract the video description using youtube-transcript-api
or yt-dlp metadata. Save it in the transcript file under:

## Description:
[full video description text]

## Transcript:
[transcript text]

Descriptions often contain:
- Links to backtest data/spreadsheets
- Summarized rules not mentioned in the video
- Key statistics highlighted
- Chapter timestamps with descriptive labels
```

### Change 4B: Extract chapter timestamps

```
If the video has chapters (most data-driven videos do), extract them.
Chapter titles like "Backtesting Results" or "Analytics / Stats" tell
Agent 2 exactly where to focus attention.

Save as:
## Chapters:
0:00 - Intro
3:13 - Backtesting Results
8:20 - Market Volatility & Spread
...
```

---

## 5. AGENT 0 (Scout) — ALREADY UPDATED, minor additions

### Change 5A: Browse promising channels

```
When you find a channel that produces multiple high-quality data-driven videos,
browse their CHANNEL PAGE and check their video list. Channels like:
- neurotrader (quantitative Python)
- TTrades (ICT with structure)
- The Soup Room (CRT backtests)
- Quantified Strategies (quant backtests)
- QuantCrawler (coded backtests)
- Mind Over Markets (mathematical analysis)

One great channel can yield 5-10 valuable videos faster than 5 new searches.
```

### Change 5B: Check playlists

```
If you find a playlist titled "Backtesting Results" or "Strategy Development",
check ALL videos in that playlist. Playlists are curated — the creator already
grouped their best content.
```

---

## PRIORITY ORDER FOR IMPLEMENTATION

1. **Agent 2 Changes (1A-1D)** — Highest ROI. Extracting correlations and
   conditionals from existing transcripts could 3-5x the value of findings.
2. **Agent 3 Changes (2A-2C)** — Cross-video pattern detection turns noise
   into signal. Especially valuable with 87 videos.
3. **Agent 4 Changes (3A-3C)** — Running tests and synthesizing composites
   turns findings into money.
4. **Agent 1 Changes (4A-4B)** — Video descriptions are low-hanging fruit.
5. **Agent 0 Changes (5A-5B)** — Channel browsing for future batches.

---

## ESTIMATED IMPACT

Current pipeline: 87 videos → ~400 claims → ~20 kept findings → ~5 tests designed

With these changes: 87 videos → ~600 claims (including correlations) →
~40 kept findings (including convergent evidence) → ~15 tests EXECUTED →
~3-5 confirmed new edge filters for the trading system

The difference between "we found 5 interesting things" and "we confirmed 3 new
filters that improve WR by 5-8%" is the difference between research and profit.
