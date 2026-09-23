# KAP MASTER LAUNCHER — Start All 5 Agents Simultaneously
# Each agent sleeps until its input files appear, then processes and outputs
# You launch all 5, walk away, come back to BATCH_REPORT.md

---

## HOW IT WORKS

Each agent has a sleep/wake mechanism:
- Agent 0 (Scout): Starts immediately — finds videos
- Agent 1 (Extractor): Sleeps until urls.txt appears → extracts transcripts
- Agent 2 (Comprehension): Sleeps until transcripts appear → extracts claims
- Agent 3 (Filter): Sleeps until claims appear → filters against KB
- Agent 4 (Strategist): Sleeps until findings appear → produces report

They communicate through files:
```
Agent 0 writes urls.txt          → wakes Agent 1
Agent 1 writes transcripts/      → wakes Agent 2
Agent 2 writes claims/           → wakes Agent 3
Agent 3 writes filtered/         → wakes Agent 4
Agent 4 writes BATCH_REPORT.md   → YOU READ THIS
```

---

## LAUNCH SEQUENCE — 5 Terminals

### Terminal 1: Agent 0 (Scout)
```bash
claude --chrome
```
Then paste the ENTIRE contents of `KAP_AGENT_0_SCOUT.md`

### Terminal 2: Agent 1 (Extractor)
```bash
claude
```
Then paste the ENTIRE contents of `KAP_AGENT_1_EXTRACTOR.md`
(It will say "Waiting for Agent 0..." and sleep)

### Terminal 3: Agent 2 (Comprehension)
```bash
claude
```
Then paste the ENTIRE contents of `KAP_AGENT_2_COMPREHENSION.md`
(It will say "Waiting for Agent 1..." and sleep)

### Terminal 4: Agent 3 (Filter)
```bash
claude
```
Then paste the ENTIRE contents of `KAP_AGENT_3_FILTER.md`
(It will say "Waiting for Agent 2..." and sleep)

### Terminal 5: Agent 4 (Strategist)
```bash
claude
```
Then paste the ENTIRE contents of `KAP_AGENT_4_STRATEGIST.md`
(It will say "Waiting for Agent 3..." and sleep)

---

## WHAT HAPPENS NEXT

1. Agent 0 browses YouTube (10-20 min) → saves urls.txt
2. Agent 1 wakes up, extracts transcripts (5-10 min) → saves transcripts/
3. Agent 2 wakes up, reads transcripts, extracts claims (15-20 min) → saves claims/
4. Agent 3 wakes up, loads KB, filters claims (10-15 min) → saves filtered/
5. Agent 4 wakes up, ranks findings, designs tests (10-15 min) → saves BATCH_REPORT.md

**Total time: ~50-80 minutes for 10-15 videos**
**Your involvement: 5 paste operations at launch, 1 report review at end**

---

## IF YOU ALREADY HAVE TRANSCRIPTS (like tonight)

Skip Agents 0 and 1. Just launch Terminals 3, 4, 5:

### Terminal 1: Agent 2 (Comprehension)
It will find existing transcripts and start immediately.

### Terminal 2: Agent 3 (Filter)
It will sleep until Agent 2 produces claims.

### Terminal 3: Agent 4 (Strategist)
It will sleep until Agent 3 produces findings.

---

## WHEN IT'S DONE

```bash
# Check if pipeline completed
cat ~/Documents/trading/gold-agent/research/kap_outputs/BATCH_REPORT.md

# If test scripts were generated
ls ~/Documents/trading/gold-agent/research/kap_outputs/tests/
```

---

## WEEKLY CYCLE

| Step | When | What | Time |
|---|---|---|---|
| Launch all 5 agents | Saturday morning | Paste 5 prompts | 10 min |
| Walk away | — | Agents work autonomously | 60-80 min |
| Read report | Saturday afternoon | Review BATCH_REPORT.md | 10 min |
| Run tests | Sunday | Execute priority 5 test scripts | 1-2 hours |
| Update KB | Sunday | Add confirmed findings to KB | 15 min |

---

## TROUBLESHOOTING

### An agent seems stuck:
Check if the previous agent finished:
```bash
ls ~/Documents/trading/gold-agent/research/kap_outputs/.agent*_done
```
Each signal file tells you which agents completed.

### An agent errored:
Read its terminal output. Most likely cause:
- Agent 0: Chrome couldn't navigate (restart Chrome, try again)
- Agent 1: youtube-transcript-api failed (video has no captions)
- Agent 2: Transcript too long for context (will process what it can)
- Agent 3: KB files not found (check project directory path)
- Agent 4: No findings to report (happens if filter was very strict)

### Want to rerun on different videos:
```bash
# Clean previous outputs
rm -rf ~/Documents/trading/gold-agent/research/kap_outputs/
# Relaunch all 5 agents
```

### Context window exhaustion:
If an agent stops responding mid-process (especially Agent 2 on 10+ transcripts),
restart it in a new terminal. It will detect existing signal files from prior
agents and resume from where the previous agents left off. Partially completed
output files from the crashed agent should be checked — some claims/findings
may have been saved before the crash.

### Realistic time estimate:
For 10-15 videos, expect 90-120 minutes total, not 50-80. Agent 2
(comprehension) is the bottleneck at 30-45 minutes for thorough extraction.

---

## FILES TO UPLOAD TO PROJECT KNOWLEDGE

Upload all 5 agent prompts so any future session can find them:
- KAP_AGENT_0_SCOUT.md
- KAP_AGENT_1_EXTRACTOR.md
- KAP_AGENT_2_COMPREHENSION.md
- KAP_AGENT_3_FILTER.md
- KAP_AGENT_4_STRATEGIST.md
- KAP_MASTER_LAUNCHER.md (this file)
