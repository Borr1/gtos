# COMPLETE KNOWLEDGE WORKFLOW — Research + Implementation

## THE FULL CYCLE

```
RESEARCH PIPELINE (KAP)              IMPLEMENTATION PIPELINE
═══════════════════════              ═══════════════════════

Agent 0: Scout (Chrome)              
    ↓ urls.txt                       
Agent 1: Extractor (Python)          
    ↓ transcripts/                   
Agent 2: Comprehension (CC)          
    ↓ claims/                        
Agent 3: Filter (CC)                 
    ↓ findings_report.md             
Agent 4: Strategist (CC)             
    ↓ BATCH_REPORT.md                
                                     
    ↓ You paste findings into:       
                                     
STRATEGIC REVIEWER (claude.ai)───→ Approves tests
    ↓ Action report                  
                                         ↓
                                     IMPLEMENTATION AGENT (CC)
                                         ↓ Runs tests
                                         ↓ test_results.json
                                         ↓
                                     Back to STRATEGIC REVIEWER
                                         ↓ Confirms/Rejects
                                         ↓
                                     Update KB with confirmed findings
```

## 7 AGENTS, 3 PHASES

### Phase 1: DISCOVERY (5 agents, autonomous)
Agents 0-4 run the KAP pipeline. Output: BATCH_REPORT.md

### Phase 2: REVIEW (1 agent, you paste findings)
Strategic Reviewer evaluates findings, approves tests. Output: Action report

### Phase 3: IMPLEMENTATION (1 agent, runs tests)
Implementation Agent runs approved tests. Output: test_results.json
Back to Reviewer for final verdict.

## HOW TO RUN IT

### Saturday Morning — Research Pipeline
Open 5 terminals, paste Agent 0-4 prompts. Walk away.
Come back to BATCH_REPORT.md.

### Saturday Afternoon — Strategic Review  
Open Claude.ai in this project.
Paste KAP_STRATEGIC_REVIEWER.md as first message.
Then paste the BATCH_REPORT.md content.
Get back: action report with TEST NOW / DEFER / KILL decisions.

### Saturday Evening or Sunday — Implementation
Open Claude Code terminal.
Paste KAP_IMPLEMENTATION_AGENT.md.
Then paste the "TEST NOW" findings from the Reviewer.
Agent runs tests, produces test_results.json.

### Sunday — Final Review
Paste test_results.json back into the Strategic Reviewer session.
Get: CONFIRMED / REJECTED verdicts.
Update kb_research_findings.md with results.
Confirmed findings go into KB documents.

## ALL PROMPT FILES

| File | Agent | Phase | Tool |
|---|---|---|---|
| KAP_AGENT_0_SCOUT.md | Scout | Research | Claude Code + Chrome |
| KAP_AGENT_1_EXTRACTOR.md | Extractor | Research | Claude Code |
| KAP_AGENT_2_COMPREHENSION.md | Comprehension | Research | Claude Code |
| KAP_AGENT_3_FILTER.md | Filter | Research | Claude Code |
| KAP_AGENT_4_STRATEGIST.md | Strategist | Research | Claude Code |
| KAP_STRATEGIC_REVIEWER.md | Reviewer | Review | Claude.ai project chat |
| KAP_IMPLEMENTATION_AGENT.md | Implementer | Implementation | Claude Code |

Upload ALL 7 to project knowledge. Any future session can find them.

## WEEKLY TIME INVESTMENT

| Phase | Time | Your effort |
|---|---|---|
| Research pipeline (5 agents) | 90-120 min | 5 paste operations |
| Strategic review | 15-20 min | Read + paste findings |
| Implementation | 30-60 min | 1 paste operation |
| Final review + KB update | 10-15 min | Read + update files |
| **Total** | **~3 hours** | **~45 min active** |

## EXPECTED OUTPUT PER CYCLE

- Videos processed: 10-15
- Claims extracted: 50-100
- Claims kept: 5-15
- Tests run: 3-5
- Confirmed findings: 1-2

At 1-2 confirmed findings per week for 12 weeks:
**12-24 validated improvements by the WF-1 boundary review in July.**
