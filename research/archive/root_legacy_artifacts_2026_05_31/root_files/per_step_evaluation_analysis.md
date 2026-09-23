# Analysis 3: Per-Step Evaluation Analysis

Which steps in the AI's 7-step evaluation actually predict outcomes?

Extracted step-level data for **108** trades.

## Step 1: Daily Bias Confidence

| Confidence | Count | WR | Avg R |
|---|---|---|---|
| high | 108 | 68.5% | +0.222R |
## Step 2: H4 Alignment

| Aligned | Count | WR | Avg R |
|---|---|---|---|
| True | 108 | 68.5% | +0.222R |

(Insufficient variation to test)

## Step 3: H1 POI Type

| POI Type | Count | WR | Avg R |
|---|---|---|---|
| OB | 101 | 72.3% | +0.267R |
| none | 7 | 14.3% | -0.424R |

### Fibonacci Zone

| Zone | Count | WR | Avg R |
|---|---|---|---|
| discount | 96 | 70.8% | +0.188R |
| neutral | 7 | 14.3% | -0.424R |
| premium | 5 | 100.0% | +1.790R |

## Step 4: Liquidity Sweep

| Sweep Detected | Count | WR | Avg R |
|---|---|---|---|
| True | 41 | 63.4% | +0.217R |
| False | 67 | 71.6% | +0.225R |

Fisher p: 0.3993
**NOT PREDICTIVE**

### Sweep Quality

| Quality | Count | WR | Avg R |
|---|---|---|---|
| ambiguous | 21 | 61.9% | +0.297R |
| clean | 40 | 62.5% | +0.208R |
| none | 46 | 76.1% | +0.193R |

## Step 5: M15 Displacement Quality

| Quality | Count | WR | Avg R |
|---|---|---|---|
| medium | 3 | 100.0% | +1.487R |
| strong | 105 | 67.6% | +0.186R |

Displacement ratio ≥2.2: WR=63.8% (n=58)
Displacement ratio <2.2: WR=74.0% (n=50)
Fisher p: 0.3019
**NOT PREDICTIVE**

## Summary: Which Steps Predict Outcomes?

| Step | Feature | Predictive? | Delta | p-value |
|---|---|---|---|---|
| 4. Liq Sweep | detected vs not | NO | -8.2pp | 0.3993 |
| 5. M15 Displacement | high vs low ratio | NO | -10.2pp | 0.3019 |

## The Real Problem: Evaluation Steps Don't Vary

| Step | Variation | Testable? |
|---|---|---|
| 1. Daily Bias | 100% "high" confidence | NO — zero variation |
| 2. H4 Alignment | 100% "aligned=True" | NO — zero variation |
| 3. H1 POI Type | 93% OB, 7% none | YES — OB vastly outperforms (72% vs 14%) |
| 4. Liquidity Sweep | 38% detected | YES — sweep NOT predictive (p=0.40) |
| 5. M15 Displacement | 97% "strong" | NO — near-zero variation |

**Steps 1, 2, and 5 pass every single trade.** They're checkboxes, not filters. If every candidate gets "high daily bias, aligned H4, strong displacement," these steps add prompt tokens without adding signal.

The only step with real discriminative power is **Step 3: H1 POI Type** — OB setups (72.3% WR, +0.27R) massively outperform non-OB entries (14.3% WR, -0.42R). But this is just saying "the ob_retest framework works and session_sweep doesn't."

**Liquidity sweep detection is anti-predictive**: trades WITHOUT sweeps win more (71.6%) than with sweeps (63.4%). The sweep check may be adding noise.

## Fibonacci Zone Surprise

| Zone | Count | WR | Avg R |
|---|---|---|---|
| premium | 5 | 100% | +1.79R |
| discount | 96 | 70.8% | +0.19R |
| neutral | 7 | 14.3% | -0.42R |

The 5 premium-zone trades are 100% WR with +1.79R avg. Tiny sample but worth monitoring — these are counter-trend entries that may capture mean-reversion moves with large R.

## So What?

1. **Steps 1, 2, 5 are cargo cult.** They pass everything. Either make them genuinely discriminative (reject some candidates) or remove them to save tokens.
2. **Step 4 (sweep) may be counterproductive.** Sweep detection doesn't predict wins and may cause the AI to overvalue sweeps.
3. **Step 3 (H1 OB) is the only real filter.** The OB identification itself is what matters.
4. **The prompt needs to produce variance.** A 7-step evaluation that gives the same answer to every setup is wasted computation.