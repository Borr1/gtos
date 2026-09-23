# IMMEDIATE IMPLEMENTATION PLAN — PRE-WF-1 PROMPT ENHANCEMENTS
**Date:** 2026-04-07  
**Author:** Yasmine (Intelligence)  
**Urgency:** CRITICAL — 24-48 hour implementation window  
**Purpose:** Actionable steps for specialized teams before WF-1 lockdown  

---

## IMPLEMENTATION SEQUENCE

### PHASE 1: CRITICAL SECURITY FIXES (0-8 HOURS) — RED TEAM
**Owner:** Rania  
**Deadline:** End of day April 7, 2026  
**Blocker:** WF-1 cannot proceed without security compliance

#### TASK 1A: Add Security Protocol to ALL Agents
**Files to modify:** All 10 agent prompt files in `/agents/`

**Add this section to each agent after the "WHO YOU ARE" section:**

```markdown
## SECURITY PROTOCOL — WF-1 COMPLIANCE

### Input Validation
- Validate ALL JSON inputs before parsing with try/catch blocks
- Sanitize file paths to prevent directory traversal
- Never log API keys, credentials, or sensitive data to files
- Use parameterized queries for any database operations

### WF-1 Trading Period Compliance
- NO PROMPT MODIFICATIONS during active trading (April 7 - July 7, 2026)
- Any operational issues must use existing prompts or halt operations
- Document issues for post-WF-1 enhancement only

### Data Security
- Never write credentials to research/kap_outputs/ files
- Redact sensitive information from logs and outputs
- Verify file permissions before writing (no world-readable)
```

#### TASK 1B: Agent-Specific Security Additions

**Python-based agents (1, 2, 3, 4):**
```python
# Add to all Python code blocks:
import json
def safe_json_parse(data):
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"JSON parsing error: {e}")
        return None
```

**Bash-based agents (0):**
```bash
# Add input validation:
validate_url() {
    if [[ ! "$1" =~ ^https://[a-zA-Z0-9.-]+/ ]]; then
        echo "Invalid URL format: $1"
        return 1
    fi
}
```

### PHASE 2: CORRELATION EXTRACTION ENHANCEMENT (8-24 HOURS) — INTELLIGENCE
**Owner:** Yasmine  
**Deadline:** April 8, 2026 8:00 AM  
**Blocker:** Must complete before Agent 2 redeployment

#### TASK 2A: Update Agent 2 (Comprehension) Prompt
**File:** `/agents/KAP_AGENT_2_COMPREHENSION.md`

**Add after existing categories in section 2:**

```markdown
**CORRELATION_CLAIM** — Relationships between two or more variables (HIGHEST VALUE)
- "When X happens, Y is more/less likely"
- Conditional performance: "Strategy X works better during Y conditions"  
- Time correlations: "After event A, B tends to happen within N candles"
- Multi-factor: "Win rate improves from X% to Y% when filter Z is added"
- Cross-asset: "When DXY does X, gold tends to do Y"
- Session-conditional: "This setup only works in London" or "Avoid Mondays"
- Example: "Silver Bullet win rate jumps from 60% to 78% when there's a prior HTF liquidity sweep"

THIS IS THE MOST VALUABLE CATEGORY. Every video has these buried in casual
remarks. When someone says "I noticed it works better in trending weeks" —
that's a CORRELATION_CLAIM. Extract it. These are the raw materials for new
edge filters.
```

**Update JSON schema in section 3:**

```json
{
    "claim": "The exact claim in one clear sentence",
    "category": "MARKET_MECHANICS | TRADING_RULES | STATISTICAL_CLAIMS | RISK_MANAGEMENT | BACKTESTING_METHODOLOGY | MARKET_MICROSTRUCTURE | CORRELATION_CLAIM",
    "variables": ["session_time", "ob_body_ratio"],
    "conditional_on": "H4 trend aligned", 
    "cross_video_corroboration": false,
    "corroborating_videos": []
}
```

#### TASK 2B: Extract Correlation Claims from Existing Transcripts
**Action:** Re-run Agent 2 on all 62 existing transcripts with CORRELATION_CLAIM focus

**Expected Output:**
- Additional 180-240 correlation claims from existing data
- Cross-video corroboration detection across 62 videos
- Identification of convergent evidence patterns

### PHASE 3: SEARCH OPTIMIZATION (8-24 HOURS) — SCALING
**Owner:** Nesrine  
**Deadline:** April 8, 2026 8:00 AM  
**Blocker:** Must complete before next Scout deployment

#### TASK 3A: Update Agent 0 (Scout) Search Topics
**File:** `/agents/KAP_AGENT_0_SCOUT.md`

**REMOVE from search topics:**
```
11. "prop firm risk management FTMO strategy"
```

**ADD new research-driven topics:**
```
11. "order block body ratio thin wick candle quality"
12. "impulse candle count displacement strength"  
13. "FVG fill percentage continuation rate"
14. "BOS vs CHoCH order block quality difference"
15. "gold session timing optimal entry beyond kill zone"
16. "order block clustering liquidity zone confluence"  
17. "XAUUSD H4 alignment order block filtering"
18. "XAUUSD OR gold backtest exit strategy trailing stop"
19. "gold futures session timing optimal entry hours"
20. "order block exit management take profit optimization"
```

#### TASK 3B: Add HARD REJECT Technical Terms Filter
**Add to REJECT criteria section:**

```markdown
HARD REJECT: If video title/description contains NONE of these technical terms:
order block, OB, FVG, fair value gap, displacement, liquidity, BOS,
CHoCH, market structure, backtest, win rate, session, kill zone,
entry, exit, stop loss, take profit, R:R, risk reward, timeframe,
confluence, imbalance, breaker, mitigation

If a "trading video" never mentions any of these terms, it's about
business/psychology, not market mechanics.
```

---

## VERIFICATION CHECKLIST

### Red Team Security Implementation
- [ ] Security protocol added to all 10 agent files
- [ ] WF-1 compliance reminders added  
- [ ] Input validation code added to Python agents
- [ ] URL validation added to Scout agent
- [ ] Test: attempt to trigger validation errors (should be caught)

### Intelligence Correlation Enhancement  
- [ ] CORRELATION_CLAIM category added to Agent 2
- [ ] JSON schema updated with variables/conditional fields
- [ ] Cross-video corroboration logic implemented
- [ ] Test: re-extract claims from 3 sample transcripts
- [ ] Verify: increased correlation claim detection rate

### Scaling Search Optimization
- [ ] Wasteful search topic removed from Agent 0
- [ ] 10 research-driven topics added
- [ ] HARD REJECT technical terms filter implemented  
- [ ] Test: verify topic filtering on sample video list
- [ ] Estimate: expected reduction in off-topic content

---

## SUCCESS METRICS

### Phase 1 Success Criteria
- **Security coverage:** 100% across all agents (up from 0%)
- **WF-1 compliance:** All agents have lockdown awareness
- **Validation:** No security vulnerabilities in test scenarios

### Phase 2 Success Criteria  
- **Correlation claims:** 3-5x increase from existing transcripts
- **Cross-video patterns:** Convergent evidence detection active
- **Edge filter candidates:** 10-15 new testable relationships identified

### Phase 3 Success Criteria
- **Topic relevance:** 95%+ (up from 87%)  
- **Waste reduction:** <5% off-topic content (down from 13%)
- **Research alignment:** All topics target validated knowledge gaps

---

## RISK MITIGATION

### Implementation Risks
1. **Time pressure:** Staggered deployment allows testing between phases
2. **Breaking changes:** All enhancements are additive (no removal of working features)
3. **WF-1 conflicts:** Changes enhance research capabilities without affecting trading logic

### Contingency Plans
1. **If Phase 1 delayed:** WF-1 CANNOT proceed - this is blocking
2. **If Phase 2 delayed:** Can proceed with existing claims, enhance post-WF-1
3. **If Phase 3 delayed:** Acceptable - affects future batches, not current system

---

## POST-IMPLEMENTATION ACTIONS

### Immediate Validation (April 8)
1. **Run test batch:** 5 new videos through enhanced pipeline
2. **Compare results:** Before/after enhancement metrics
3. **Document improvements:** Quantified efficiency gains

### WF-1 Monitoring (April 7 - July 7)  
1. **Security monitoring:** Track compliance across all operations
2. **Performance tracking:** Monitor enhanced correlation discovery rate
3. **Error logging:** Document any issues for post-WF-1 fixes

### Post-WF-1 Enhancements (July 8+)
1. **Content deduplication:** Implement shared prompt libraries  
2. **Context handoff improvements:** Standardize agent coordination
3. **Advanced pattern detection:** Cross-agent knowledge sharing

---

## CONCLUSION

**CRITICAL PATH:** Security → Correlation → Search optimization must complete in sequence within 24 hours.

**OWNER RESPONSIBILITIES:**
- **Rania (Red Team):** Security implementation - MUST COMPLETE TODAY
- **Yasmine (Intelligence):** Correlation enhancement - 24 hour window  
- **Nesrine (Scaling):** Search optimization - 24 hour window

**SUCCESS DEFINITION:** All three phases complete before April 8 EOD, enabling enhanced research capabilities during WF-1 without trading system disruption.

**STATUS:** Implementation begins immediately upon approval.