# RED TEAM CONTRADICTION DETECTION FRAMEWORK
**Established:** 2026-04-07  
**Required by:** Intelligence Lead conditional approval  
**Validated by:** Red Team Lead (Rania)

## Severity Classification System

### CRITICAL CONTRADICTIONS (immediate flag)
- **Definition:** New finding directly opposes existing KB fact with statistical significance (p<0.05)
- **Action:** Block KB update until resolved
- **Example:** New claim "M15 is trap" vs KB "M15 is optimal" (p<0.001)

### EXTENDS (nuanced addition)  
- **Definition:** New finding adds depth/context to existing KB without contradicting core fact
- **Action:** Add as supplementary context with reference to base finding
- **Example:** "OB freshness matters" extends but doesn't contradict "OB zone adds +17pp"

### CONFIRMS (validation)
- **Definition:** New finding validates existing KB fact through independent data/methodology
- **Action:** Mark as CONVERGENT evidence, strengthen confidence rating
- **Example:** Trader Zan 10yr backtest confirms our sweep anti-prediction finding

### NOVEL (new territory)
- **Definition:** New finding introduces completely new concept not covered in KB
- **Action:** Add to research queue with priority rating based on potential impact
- **Example:** "Forward liquidity targets" - completely new filter concept

## Data Quality Flags (Pre-Cross-Reference)

### BATCH_REPORT Quality Issues Identified:

#### HIGH RISK (invalidate cross-references)
1. **F07 Simulation Bias:** BE stop analysis admits "optimistic assumptions" - simulation assumes all 1R-reaching trades still reach TP with BE active. Real impact "between 0R and +0.060R"
2. **F15 Data Gap:** ICT regime dependency cannot be verified because "our data starts Oct 2024" - temporal coverage insufficient

#### MEDIUM RISK (flag with caveats) 
3. **Small Sample Bias:** Some findings based on n=23 trades (insufficient for statistical validity)
4. **F11 Untestable:** OB freshness marked UNTESTED due to missing OB age tracking in pipeline

#### LOW RISK (acceptable with notation)
5. **External Data Dependency:** F24 (70% prop failures are scalpers) relies on PipBack external data - single-source risk

## Cross-Validation Protocol

### Step 1: Pre-Screen Data Quality
- Flag simulation bias, data gaps, small samples before analysis
- Reject findings with obvious methodological flaws

### Step 2: Statistical Threshold Validation  
- Contradictions require p<0.05 OR large effect size (>10pp WR difference)
- Confirmations require independent data source OR different methodology

### Step 3: KB Impact Assessment
- CRITICAL: Affects live trading decisions → immediate investigation
- MEDIUM: Research queue addition → WF-2 testing  
- LOW: Archive as context → no action needed

## Approved Framework Status
✅ **Red Team Lead:** Framework established and operational  
⏳ **Intelligence Lead:** Pending framework review  
⏳ **Validation Lead:** Pending documentation approval