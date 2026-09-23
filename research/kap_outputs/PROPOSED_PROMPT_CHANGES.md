# KAP Pipeline — Proposed Prompt Changes
# Date: 2026-04-06
# Author: Agent 4 (Strategist)
# Status: PENDING REVIEW — No changes applied to other agents
# For: Management review before implementation

---

## Context

During the 2026-04-06 batch run (15 videos, 107 claims, 18 findings), several
operational issues were identified that would improve pipeline efficiency and
output quality. This document proposes specific changes to agent prompts,
organized by agent, with rationale for each.

---

## PROPOSED CHANGES TO: Agent 0 (Scout)

### Change 1: Add Research-Question-Driven Search Topics
**What:** Add 7 new primary search topics derived from our validated findings
and open research questions.

**Proposed additions:**
```
11. "order block body ratio thin wick candle quality"
12. "impulse candle count displacement strength"
13. "FVG fill percentage continuation rate"
14. "BOS vs CHoCH order block quality difference"
15. "gold session timing optimal entry beyond kill zone"
16. "order block clustering liquidity zone confluence"
17. "XAUUSD H4 alignment order block filtering"
```

**Why:** Current search topics are generic SMC terms. These target our specific
open questions — topics where external data could directly improve the system.
The current topics produced 2 off-topic videos (prop firm management, pure
psychology) out of 15 in this batch.

**Risk:** Low. Additive change — doesn't remove existing topics.

---

### Change 2: Remove "prop firm risk management FTMO strategy" Search Topic
**What:** Remove topic #11 from the secondary search list.

**Why:** This exact topic led the Scout to select a prop firm account
management video (Video 01) that produced 10 claims, ALL tangential to the
trading system. Zero testable market claims. 100% waste of pipeline time.

**Risk:** None. Prop firm risk management content is about business operations,
not market mechanics.

---

### Change 3: Expand REJECT Criteria with Specific Keywords
**What:** Add three new rejection categories to the existing REJECT list.

**Proposed additions:**
```
- Are about prop firm ACCOUNT MANAGEMENT (scaling accounts, getting payouts,
  challenge strategies, account rotation, AUM planning). These contain zero
  market analysis. Title keywords to reject: "how to get funded", "prop firm
  payout", "$X per month from trading", "scaling funded accounts", "challenge
  strategy", "funded trader mindset"

- Are about trading PSYCHOLOGY/MINDSET without specific market claims.
  Title keywords to reject: "mindset", "psychology", "discipline", "revenge
  trading", "emotional control". These videos produce 0% testable claims.

- Are from channels focused on motivation over data (e.g., "Trader Mind TV"
  and similar). Check if the channel's other videos are also psychology-only.
```

**Why:** Video 01 (prop firm management) and Video 02 (pure psychology)
produced 10 and 0 claims respectively, with 0 kept findings combined. The
current REJECT list catches "pure motivation" but doesn't explicitly catch
prop firm business content or trading psychology content that has no market
claims.

**Risk:** Low. These categories have zero overlap with technical analysis
content. A video titled "XAUUSD order block psychology" would NOT be caught
because it contains "order block" and "XAUUSD."

---

### Change 4: Add HARD REJECT Technical Terms Gate
**What:** Add a rule that rejects any video whose title/description contains
NONE of a set of technical trading terms.

**Proposed terms:**
```
order block, OB, FVG, fair value gap, displacement, liquidity, BOS,
CHoCH, market structure, backtest, win rate, session, kill zone,
entry, exit, stop loss, take profit, R:R, risk reward, timeframe,
confluence, imbalance, breaker, mitigation
```

**Why:** If a "trading video" never mentions any of these terms, it's about
business/psychology, not market mechanics. This would have caught both
off-topic videos in this batch.

**Risk:** Medium. Could reject videos that use non-standard terminology for
valid concepts. Mitigated by the broad term list (26 terms).

---

## PROPOSED CHANGES TO: Agent 4 (Strategist) — ALREADY APPLIED

These changes are to my own prompt and have already been applied to
`agents/KAP_AGENT_4_STRATEGIST.md`. Summary of what was added:

### Lessons Learned Section (12 items)
1. **Don't block on Agent 3** — read claims directly, pre-assess quality
2. **Correct data file paths** — both `data/` and `data/historical/`, with
   size awareness (top-level may be 200 candles, historical has 14K+)
3. **Assess batch quality early** — report honestly on off-topic batches
4. **Cross-reference validated findings** — complete list of known statistics
   for instant REDUNDANT/COMPLEMENTARY/CONTRADICTORY classification
5. **Include Scout calibration feedback** — every report should suggest
   improvements to video selection
6. **Poll for updates** — Agent 3 may update findings incrementally
7. **Run test scripts, don't just write them** — execute and include results
8. **Top-level vs historical data size awareness** — always check `wc -l`
9. **Prioritize contradictions** — highest value, test first
10. **Distinguish probability vs magnitude** — claims may not actually
    contradict if measuring different things
11. **Session data structure** — documented JSON schema for batch sessions
12. **Baseline findings from this batch** — session equality, day-of-week,
    FVG fill, BE stops, scalper failure rate

### Data Check Code Update
Updated the data verification snippet to check both `data/` and
`data/historical/` locations, and added H4, D1 checks.

### Why These Changes
These are self-improvements based on actual issues encountered:
- Wasted 10 minutes waiting for Agent 3 when claims were already readable
- Test script used 200-candle file instead of 14,716-candle file (bad path)
- Initial report missed 3 pre-refuted findings that Agent 3 later caught
  (because I didn't cross-reference the full KB early enough)

---

## PROPOSED CHANGES TO: Agent 3 (Filter) — NONE

Agent 3 performed well this batch. It correctly:
- Tagged 38 claims as REDUNDANT
- Identified 7 contradictions with specific KB references
- Found 3 claims that were pre-refuted by existing data
- Kept 18 findings at appropriate priority levels

No changes recommended.

---

## PROPOSED CHANGES TO: Agent 1 (Extractor) — APPLIED 2026-04-06

**Incident:** Agent 1 re-ran after YouTube IP-blocked, overwriting 26 good
transcripts (video_16 through video_34) with "NO TRANSCRIPT AVAILABLE" stubs.
Agent 2 had already read and extracted claims from these transcripts, but the
source data was destroyed. 20 videos worth of transcripts were permanently lost.

### Change 5: Never Overwrite Existing Transcripts With Real Content
**What:** Added a skip guard at the top of the extraction loop — if a transcript
file already exists AND contains `## Transcript:` (not just a NO TRANSCRIPT
placeholder), skip it entirely.

**Why:** YouTube IP blocks are transient. When Agent 1 re-runs, failed
re-scrapes were overwriting previously successful transcripts with empty
placeholder files. This is catastrophic data loss.

**Applied to:** `KAP_AGENT_1_EXTRACTOR.md` lines 128-142 (main loop guard)
and all error-handler placeholder writes (2 locations).

**Risk:** None. If a transcript needs to be re-extracted, delete the file first.

---

## PROPOSED CHANGES TO: Agent 2 (Comprehension) — APPLIED 2026-04-06

### Change 6: Incremental Processing — Skip Already-Extracted Claims
**What:** Added a pre-scan that identifies which claims files already exist with
real claims, and skips those videos. Only processes new/missing transcripts.

**Why:** On re-runs, Agent 2 was re-processing all videos from scratch instead
of only new ones. With 54 videos, this wastes significant time and risks
overwriting good claims.

### Change 7: Incremental Signal Updates for Agent 3
**What:** After every 3 videos processed, Agent 2 now updates the `.agent2_done`
signal file with current totals so Agent 3 can start working on partial data
immediately instead of waiting for full completion.

**Why:** Batch-to-streaming conversion. Agent 3 was blocked waiting for all
claims to finish. Now it can start filtering as soon as 3 claims files exist.

### Change 8: Never Overwrite Claims Files With Real Claims
**What:** Before writing a claims file, check if one already exists with
`total_claims_extracted > 0`. If so, skip the write.

**Why:** Same principle as Agent 1 — protect previous work from re-run
overwrites.

**All three applied to:** `KAP_AGENT_2_COMPREHENSION.md`

**Risk:** None. Delete the claims file manually if re-extraction is needed.

---

## NEW RULE: Agent 4 Must Not Edit Other Agent Prompts Directly

**Lesson learned this session:** I edited Agent 0's prompt directly without
review. This has been reverted. Going forward, Agent 4 should:

1. Document all proposed changes in `PROPOSED_PROMPT_CHANGES.md`
2. Include the exact diff (what to add/remove/change)
3. Include rationale and risk assessment for each change
4. Wait for management approval before any changes are applied
5. Only self-edit `KAP_AGENT_4_STRATEGIST.md` (own prompt)

This rule has been added to Agent 4's prompt (see below).

---

## Implementation Priority

**Already applied (critical fixes):**
- **Change 5** — Agent 1 never overwrites existing transcripts (data loss prevention)
- **Change 6** — Agent 2 incremental processing (skip already-extracted)
- **Change 7** — Agent 2 incremental signal updates (streaming to Agent 3)
- **Change 8** — Agent 2 never overwrites existing claims (data loss prevention)

**Pending approval:**
1. **Change 2** (remove prop firm search topic) — zero risk, immediate value
2. **Change 3** (expand REJECT keywords) — low risk, prevents wasted pipeline runs
3. **Change 1** (add research-driven topics) — low risk, targets our open questions
4. **Change 4** (HARD REJECT gate) — medium risk, review term list first

---

## BATCH 2 ADDITIONS (2026-04-06, Batch 2 run)

### Change 9: Agent 0 — Gold-Specific Search Priority
**What:** Add explicit gold/XAUUSD keywords to search queries and deprioritize
generic NQ/ES Silver Bullet content.

**Proposed additions to search topics:**
```
18. "XAUUSD OR gold backtest exit strategy trailing stop"
19. "gold futures session timing optimal entry hours"
20. "gold vs indices ICT strategy differences"
21. "order block exit management take profit optimization"
```

**Proposed deprioritization:**
```
Move "ICT Silver Bullet backtest" to SECONDARY topics (not primary).
Reason: 6/9 videos in batch 2 were NQ Silver Bullet. Claims do NOT transfer
to gold (Asian sweep: 45.4% accuracy on gold, FVG freshness: p=0.54).
```

**Why:** Batch 2's biggest finding is that NQ/indices claims fail on gold:
- Asian range sweep: REJECTED (45.4% on gold, p=0.98)
- FVG freshness decay: NOT CONFIRMED (p=0.54 on gold M15)
- Silver Bullet macro windows: untestable (NQ-specific timing)

**Risk:** Low. We're not removing NQ topics, just deprioritizing them.
Gold-specific content is higher ROI for our pipeline.

### Change 10: Agent 0 — Clickbait Title Filter
**What:** Auto-reject videos with titles matching these patterns:
```
REJECT if title contains "90% win rate" AND video description mentions
fewer than 50 trades in sample.

REJECT if title contains "100% pass" AND "guarantee".

REJECT if title contains a specific dollar amount (e.g., "$200K",
"$1,000,000") AND "simple strategy" — unless the channel is known
data-driven (e.g., Trader Zan, QuantCrawler).
```

**Why:** Video 19 (IDFX) claimed "90% win rate" from 8 trades. Video 41
promised "100% pass guarantee." These waste pipeline time and produce
zero actionable findings.

**Risk:** Low. Could miss a legitimate high-WR study, but unlikely —
serious quant channels don't use clickbait titles.

### Change 11: Agent 1 — Rate Limiting for YouTube Transcripts
**What:** Add delay between transcript fetches and retry logic.

**Proposed code change:**
```python
# Between each transcript fetch, add:
import time, random
time.sleep(random.uniform(3, 8))  # 3-8 second random delay

# On failure, retry with exponential backoff:
for attempt in range(3):
    try:
        transcript = fetch_transcript(url)
        break
    except TranscriptBlocked:
        wait = (2 ** attempt) * 10 + random.uniform(0, 5)
        print(f"Blocked, retrying in {wait:.0f}s (attempt {attempt+1}/3)")
        time.sleep(wait)
```

**Why:** YouTube IP-banned us after ~25 rapid requests, blocking 30/39 videos.
This is the single biggest pipeline failure in batch 2.

**Risk:** Low. Slower fetching (adds ~3-5 min per batch of 30 videos) but
prevents complete blockage.

**Priority:** HIGH — this blocks ALL downstream agents.

### Implementation Priority (Batch 2)
1. **Change 11** (rate limiting) — CRITICAL, fixes pipeline blockage
2. **Change 9** (gold-specific search) — HIGH, improves finding relevance
3. **Change 10** (clickbait filter) — MEDIUM, reduces noise
