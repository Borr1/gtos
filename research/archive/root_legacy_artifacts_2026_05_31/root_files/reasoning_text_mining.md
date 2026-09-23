# Analysis 2: Reasoning Text Mining

Extracted features for **108** of 111 trades.

## Feature Distributions

| Feature | Median | Mean | Min | Max |
|---|---|---|---|---|
| word_count | 102 | 101.5 | 88 | 120 |
| price_count | 5 | 5.0 | 2 | 9 |
| hedging_count | 1 | 0.9 | 0 | 2 |
| confidence | 80 | 79.9 | 75 | 80 |

## Feature → WR Correlations

| Feature | Split | High n | High WR | Low n | Low WR | Delta | Fisher p |
|---|---|---|---|---|---|---|---|
| word_count | ≥102.5 vs <102.5 | 54 | 70.4% | 54 | 66.7% | +3.7pp | 0.8361 |
| price_count | ≥8 vs <8 | 7 | 71.4% | 101 | 68.3% | +3.1pp | 1.0000 |

## Replication of Claimed Predictors

### Claim: price_level_count ≥8 adds +17.4pp

- ≥8 levels: 7 trades, WR = 71.4%
- <8 levels: 101 trades, WR = 68.3%
- **Delta: +3.1pp** (claimed: +17.4pp)
- Fisher p = 1.0000
- **DOES NOT REPLICATE**

### Claim: hesitation_score ≤2 adds +13.3pp

### Setup Grade vs Outcome

| Grade | Count | WR | Avg R |
|---|---|---|---|
| A | 18 | 72.2% | +0.225R |
| A+ | 90 | 67.8% | +0.222R |

## Structural Problem: Near-Zero Feature Variance

The most important finding is what's **missing**: almost all features have near-zero variance.

| Feature | Problem |
|---|---|
| confidence_score | 106/108 trades are exactly 80. No meaningful split possible. |
| hedging_count | All ≤2. The AI never hedges. Cannot test hesitation claim. |
| word_count | Range 88-120 (very tight). All reasoning is template-length. |
| price_count | 93% have 2-7 levels. Only 7 trades have ≥8. Tiny sample. |
| setup_grade | 83% are A+, 17% are A. Grades don't differentiate. |

**The confidence scorer and text features cannot possibly predict outcomes because they don't vary.** The AI assigns the same confidence (80), same grade (A+), and same reasoning template to virtually every trade. This means:

1. **price_level_count ≥8 → +17.4pp**: DOES NOT REPLICATE. Only 7 trades qualify, delta is +3.1pp (p=1.0). The original claim was likely based on the screening population, not the batch trades.
2. **hesitation_score ≤2 → +13.3pp**: UNTESTABLE. All trades have ≤2 hedging phrases. There's no high-hesitation group to compare against.
3. **The confidence scorer is effectively a constant.** It adds no information because it assigns 80 to everything.

## So What?

The text mining reveals that **the AI's reasoning is performative, not discriminative.** It generates plausible-sounding analysis for every candidate but doesn't actually vary its assessment across setups of different quality. To add value, the confidence scorer needs to produce DIFFERENT scores for different setups — currently it's a rubber stamp.