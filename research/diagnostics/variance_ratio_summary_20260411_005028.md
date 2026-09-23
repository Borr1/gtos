# Variance Ratio Analysis — GTOS Instruments

**Generated:** 2026-04-11 00:50 UTC
**Method:** Lo-MacKinlay (1988) heteroskedasticity-robust VR test
**Joint test:** Chow-Denning (1993) with Bonferroni correction

**Classification thresholds (two-sided p-value):**
- p < 0.01 → STRONG
- p < 0.05 → MODERATE  
- p < 0.10 → SUGGESTIVE (flag, needs more data)
- p ≥ 0.10 → RANDOM WALK

**Bonferroni correction across full matrix** (5 instr × 4 TF × 6 q ≈ 120 tests): α_corrected ≈ 0.0004.  
Only STRONG results (p < 0.01) are robustly significant after correction.

---

## Summary Table — Overall classification at VR(q=8)

| Instrument | M1 | M5 | M15 | H1 | H4 | D1 | H1 stability |
|---|---|---|---|---|---|---|---|
| XAUUSD | RW | RW | RW | RW | RW | RW | STABLE |
| US30 | N/A | N/A | RW | RW | RW | RW | STABLE |
| USDJPY | N/A | N/A | RW | RW | RW | RW | STABLE |
| GBPJPY | N/A | N/A | REV? | RW | RW | RW | STABLE |
| GBPUSD | N/A | N/A | REV↓ | RW | RW | RW | STABLE |

*MOM=Momentum, REV=Mean-Reversion, RW=Random Walk, ↑↑=p<0.01, ↑=p<0.05, ?=suggestive (p<0.10)*

---

## Detailed Results

### XAUUSD

#### XAUUSD M1 (99,998 returns, 2025-12-18 – 2026-04-02)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0074 | 0.683 | 0.49467 | 2.333 | RANDOM_WALK |
| 4 | 0.9976 | -0.124 | 0.90109 | -0.407 | RANDOM_WALK |
| 8 | 0.9861 | -0.472 | 0.63677 | -1.488 | RANDOM_WALK |
| 16 | 0.9721 | -0.670 | 0.50295 | -2.006 | RANDOM_WALK |
| 32 | 0.9772 | -0.401 | 0.68869 | -1.131 | RANDOM_WALK |
| 64 | 0.9710 | -0.387 | 0.69870 | -1.004 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.683 (q=2), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2025 | 11,554 | 1.0256 | 0.566 | 0.57162 | RANDOM_WALK |
| 2026 | 88,444 | 0.9844 | -0.511 | 0.60908 | RANDOM_WALK |

#### XAUUSD M5 (99,998 returns, 2024-10-29 – 2026-04-02)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0129 | 1.154 | 0.24858 | 4.081 | RANDOM_WALK |
| 4 | 1.0216 | 1.046 | 0.29577 | 3.654 | RANDOM_WALK |
| 8 | 1.0304 | 0.967 | 0.33349 | 3.252 | RANDOM_WALK |
| 16 | 1.0174 | 0.396 | 0.69186 | 1.249 | RANDOM_WALK |
| 32 | 0.9859 | -0.238 | 0.81194 | -0.697 | RANDOM_WALK |
| 64 | 0.9913 | -0.111 | 0.91171 | -0.302 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 1.154 (q=2), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2024 | 12,167 | 1.0661 | 1.548 | 0.12160 | RANDOM_WALK |
| 2025 | 70,142 | 1.0122 | 0.602 | 0.54714 | RANDOM_WALK |
| 2026 | 17,689 | 1.0415 | 0.732 | 0.46434 | RANDOM_WALK |

#### XAUUSD M15 (47,141 returns, 2024-04-01 – 2026-03-30)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0006 | 0.036 | 0.97133 | 0.133 | RANDOM_WALK |
| 4 | 0.9999 | -0.003 | 0.99770 | -0.010 | RANDOM_WALK |
| 8 | 0.9593 | -0.880 | 0.37883 | -2.990 | RANDOM_WALK |
| 16 | 0.9369 | -0.971 | 0.33141 | -3.112 | RANDOM_WALK |
| 32 | 0.9402 | -0.680 | 0.49670 | -2.037 | RANDOM_WALK |
| 64 | 0.9878 | -0.103 | 0.91776 | -0.290 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.971 (q=16), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2024 | 17,960 | 0.9717 | -0.764 | 0.44492 | RANDOM_WALK |
| 2025 | 23,547 | 0.9698 | -0.895 | 0.37100 | RANDOM_WALK |
| 2026 | 5,634 | 0.9457 | -0.558 | 0.57691 | RANDOM_WALK |

#### XAUUSD H1 (14,715 returns, 2023-10-02 – 2026-03-30)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 0.9802 | -0.932 | 0.35119 | -2.404 | RANDOM_WALK |
| 4 | 0.9655 | -0.893 | 0.37173 | -2.239 | RANDOM_WALK |
| 8 | 0.9727 | -0.465 | 0.64224 | -1.119 | RANDOM_WALK |
| 16 | 1.0228 | 0.264 | 0.79196 | 0.628 | RANDOM_WALK |
| 32 | 1.0883 | 0.717 | 0.47321 | 1.679 | RANDOM_WALK |
| 64 | 0.9998 | -0.001 | 0.99900 | -0.003 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.932 (q=2), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2023 | 1,466 | 1.1098 | 0.799 | 0.42431 | RANDOM_WALK |
| 2024 | 5,938 | 1.0017 | 0.030 | 0.97566 | RANDOM_WALK |
| 2025 | 5,899 | 0.9738 | -0.484 | 0.62837 | RANDOM_WALK |
| 2026 | 1,412 | 0.9441 | -0.417 | 0.67648 | RANDOM_WALK |

#### XAUUSD H4 (4,628 returns, 2023-03-31 – 2026-03-30)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0096 | 0.307 | 0.75855 | 0.651 | RANDOM_WALK |
| 4 | 1.0470 | 0.810 | 0.41763 | 1.709 | RANDOM_WALK |
| 8 | 1.1319 | 1.431 | 0.15240 | 3.034 | RANDOM_WALK |
| 16 | 1.0552 | 0.409 | 0.68214 | 0.853 | RANDOM_WALK |
| 32 | 1.0110 | 0.059 | 0.95279 | 0.117 | RANDOM_WALK |
| 64 | 0.9070 | -0.385 | 0.70022 | -0.693 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 1.431 (q=8), p_Bonferroni = 0.9144*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2023 | 1,158 | 0.9244 | -0.839 | 0.40140 | RANDOM_WALK |
| 2024 | 1,554 | 1.0155 | 0.166 | 0.86829 | RANDOM_WALK |
| 2025 | 1,545 | 1.0646 | 0.644 | 0.51942 | RANDOM_WALK |
| 2026 | 371 | 1.3434 | 1.447 | 0.14779 | RANDOM_WALK |

#### XAUUSD D1 (771 returns, 2023-04-03 – 2026-03-30)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0146 | 0.216 | 0.82892 | 0.405 | RANDOM_WALK |
| 4 | 0.9311 | -0.529 | 0.59691 | -1.023 | RANDOM_WALK |
| 8 | 0.8939 | -0.536 | 0.59204 | -0.996 | RANDOM_WALK |
| 16 | 0.7710 | -0.853 | 0.39364 | -1.444 | RANDOM_WALK |
| 32 | 0.6758 | -0.928 | 0.35323 | -1.411 | RANDOM_WALK |
| 64 | 0.6085 | -0.866 | 0.38643 | -1.191 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.928 (q=32), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2024 | 259 | 0.8786 | -0.663 | 0.50701 | RANDOM_WALK |
| 2025 | 258 | 0.7734 | -0.998 | 0.31811 | RANDOM_WALK |

### US30

#### US30 M15 (99,998 returns, 2022-01-06 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 0.9870 | -1.142 | 0.25341 | -4.121 | RANDOM_WALK |
| 4 | 0.9755 | -1.183 | 0.23663 | -4.144 | RANDOM_WALK |
| 8 | 0.9782 | -0.703 | 0.48193 | -2.328 | RANDOM_WALK |
| 16 | 0.9690 | -0.730 | 0.46515 | -2.229 | RANDOM_WALK |
| 32 | 0.9639 | -0.661 | 0.50847 | -1.790 | RANDOM_WALK |
| 64 | 0.9627 | -0.552 | 0.58116 | -1.292 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 1.183 (q=4), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2022 | 23,254 | 1.0011 | 0.036 | 0.97158 | RANDOM_WALK |
| 2023 | 23,562 | 1.0090 | 0.241 | 0.80987 | RANDOM_WALK |
| 2024 | 23,668 | 1.0359 | 1.050 | 0.29364 | RANDOM_WALK |
| 2025 | 23,505 | 0.9291 | -0.765 | 0.44416 | RANDOM_WALK |
| 2026 | 6,009 | 0.9067 | -1.145 | 0.25202 | RANDOM_WALK |

#### US30 H1 (19,999 returns, 2022-11-10 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0061 | 0.340 | 0.73355 | 0.859 | RANDOM_WALK |
| 4 | 1.0024 | 0.068 | 0.94558 | 0.183 | RANDOM_WALK |
| 8 | 0.9933 | -0.120 | 0.90463 | -0.320 | RANDOM_WALK |
| 16 | 1.0037 | 0.049 | 0.96064 | 0.120 | RANDOM_WALK |
| 32 | 0.9327 | -0.673 | 0.50093 | -1.493 | RANDOM_WALK |
| 64 | 0.9252 | -0.556 | 0.57790 | -1.159 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.673 (q=32), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2022 | 802 | 0.9037 | -0.623 | 0.53333 | RANDOM_WALK |
| 2023 | 5,893 | 0.9076 | -1.510 | 0.13092 | RANDOM_WALK |
| 2024 | 5,920 | 0.9958 | -0.065 | 0.94795 | RANDOM_WALK |
| 2025 | 5,881 | 1.0531 | 0.449 | 0.65333 | RANDOM_WALK |
| 2026 | 1,503 | 0.9748 | -0.249 | 0.80298 | RANDOM_WALK |

#### US30 H4 (9,999 returns, 2019-10-15 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 0.9668 | -1.153 | 0.24884 | -3.317 | RANDOM_WALK |
| 4 | 0.9615 | -0.758 | 0.44860 | -2.060 | RANDOM_WALK |
| 8 | 0.9322 | -0.848 | 0.39638 | -2.293 | RANDOM_WALK |
| 16 | 0.9282 | -0.600 | 0.54880 | -1.630 | RANDOM_WALK |
| 32 | 0.9269 | -0.425 | 0.67111 | -1.146 | RANDOM_WALK |
| 64 | 0.9279 | -0.303 | 0.76153 | -0.790 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 1.153 (q=2), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2019 | 329 | 0.9120 | -0.487 | 0.62651 | RANDOM_WALK |
| 2020 | 1,560 | 0.9341 | -0.404 | 0.68626 | RANDOM_WALK |
| 2021 | 1,550 | 0.9101 | -0.969 | 0.33239 | RANDOM_WALK |
| 2022 | 1,540 | 0.9055 | -1.064 | 0.28748 | RANDOM_WALK |
| 2023 | 1,540 | 0.8949 | -1.271 | 0.20373 | RANDOM_WALK |
| 2024 | 1,548 | 1.0455 | 0.534 | 0.59313 | RANDOM_WALK |
| 2025 | 1,539 | 0.9727 | -0.143 | 0.88660 | RANDOM_WALK |
| 2026 | 393 | 0.8933 | -0.714 | 0.47524 | RANDOM_WALK |

#### US30 D1 (1,827 returns, 2019-02-07 – 2026-04-02)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 0.8694 | -1.760 | 0.07845 | -5.584 | MEAN_REVERSION_SUGGESTIVE |
| 4 | 0.9087 | -0.646 | 0.51844 | -2.087 | RANDOM_WALK |
| 8 | 0.8707 | -0.606 | 0.54436 | -1.868 | RANDOM_WALK |
| 16 | 0.8673 | -0.442 | 0.65869 | -1.289 | RANDOM_WALK |
| 32 | 0.7773 | -0.568 | 0.56978 | -1.492 | RANDOM_WALK |
| 64 | 0.5990 | -0.848 | 0.39660 | -1.878 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 1.760 (q=2), p_Bonferroni = 0.4707*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2019 | 209 | 0.7229 | -0.924 | 0.35570 | RANDOM_WALK |
| 2020 | 260 | 0.9098 | -0.217 | 0.82818 | RANDOM_WALK |
| 2021 | 259 | 0.6213 | -1.639 | 0.10124 | RANDOM_WALK |
| 2022 | 258 | 1.0239 | 0.129 | 0.89734 | RANDOM_WALK |
| 2023 | 258 | 1.0503 | 0.265 | 0.79081 | RANDOM_WALK |
| 2024 | 259 | 1.0551 | 0.284 | 0.77630 | RANDOM_WALK |
| 2025 | 258 | 0.6973 | -0.823 | 0.41057 | RANDOM_WALK |

### USDJPY

#### USDJPY M15 (49,999 returns, 2024-03-31 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 0.9942 | -0.529 | 0.59690 | -1.290 | RANDOM_WALK |
| 4 | 1.0051 | 0.263 | 0.79254 | 0.609 | RANDOM_WALK |
| 8 | 0.9956 | -0.157 | 0.87510 | -0.332 | RANDOM_WALK |
| 16 | 0.9938 | -0.165 | 0.86885 | -0.314 | RANDOM_WALK |
| 32 | 1.0003 | 0.006 | 0.99501 | 0.011 | RANDOM_WALK |
| 64 | 1.0334 | 0.531 | 0.59571 | 0.817 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.531 (q=64), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2024 | 18,804 | 1.0011 | 0.023 | 0.98200 | RANDOM_WALK |
| 2025 | 24,859 | 1.0069 | 0.227 | 0.82039 | RANDOM_WALK |
| 2026 | 6,336 | 0.9131 | -1.168 | 0.24296 | RANDOM_WALK |

#### USDJPY H1 (19,999 returns, 2023-01-16 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0071 | 0.655 | 0.51266 | 1.001 | RANDOM_WALK |
| 4 | 1.0145 | 0.700 | 0.48366 | 1.097 | RANDOM_WALK |
| 8 | 1.0182 | 0.568 | 0.57036 | 0.869 | RANDOM_WALK |
| 16 | 1.0440 | 0.970 | 0.33225 | 1.414 | RANDOM_WALK |
| 32 | 1.0382 | 0.613 | 0.54020 | 0.848 | RANDOM_WALK |
| 64 | 1.0018 | 0.021 | 0.98344 | 0.027 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.970 (q=16), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2023 | 5,960 | 1.0310 | 0.536 | 0.59194 | RANDOM_WALK |
| 2024 | 6,239 | 0.9768 | -0.370 | 0.71143 | RANDOM_WALK |
| 2025 | 6,216 | 1.0516 | 1.064 | 0.28720 | RANDOM_WALK |
| 2026 | 1,584 | 1.0480 | 0.481 | 0.63035 | RANDOM_WALK |

#### USDJPY H4 (9,999 returns, 2019-10-30 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0216 | 1.349 | 0.17734 | 2.157 | RANDOM_WALK |
| 4 | 1.0373 | 1.278 | 0.20110 | 1.995 | RANDOM_WALK |
| 8 | 1.0514 | 1.163 | 0.24475 | 1.737 | RANDOM_WALK |
| 16 | 1.0226 | 0.361 | 0.71772 | 0.513 | RANDOM_WALK |
| 32 | 0.9787 | -0.244 | 0.80718 | -0.334 | RANDOM_WALK |
| 64 | 0.9747 | -0.210 | 0.83358 | -0.278 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 1.349 (q=2), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2019 | 258 | 1.0320 | 0.170 | 0.86527 | RANDOM_WALK |
| 2020 | 1,563 | 1.1517 | 1.085 | 0.27802 | RANDOM_WALK |
| 2021 | 1,560 | 0.9847 | -0.190 | 0.84969 | RANDOM_WALK |
| 2022 | 1,554 | 1.0545 | 0.508 | 0.61124 | RANDOM_WALK |
| 2023 | 1,554 | 1.0020 | 0.020 | 0.98430 | RANDOM_WALK |
| 2024 | 1,560 | 1.0564 | 0.572 | 0.56739 | RANDOM_WALK |
| 2025 | 1,554 | 1.0018 | 0.019 | 0.98452 | RANDOM_WALK |
| 2026 | 396 | 1.3302 | 1.633 | 0.10256 | RANDOM_WALK |

#### USDJPY D1 (2,999 returns, 2014-09-09 – 2026-04-02)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 0.9870 | -0.513 | 0.60814 | -0.711 | RANDOM_WALK |
| 4 | 0.9779 | -0.480 | 0.63121 | -0.646 | RANDOM_WALK |
| 8 | 0.9652 | -0.487 | 0.62636 | -0.644 | RANDOM_WALK |
| 16 | 0.9811 | -0.183 | 0.85510 | -0.235 | RANDOM_WALK |
| 32 | 1.0042 | 0.029 | 0.97710 | 0.036 | RANDOM_WALK |
| 64 | 1.0321 | 0.161 | 0.87193 | 0.193 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.513 (q=2), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **UNSTABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2015 | 259 | 0.6992 | -1.362 | 0.17307 | RANDOM_WALK |
| 2016 | 260 | 1.1701 | 0.892 | 0.37211 | RANDOM_WALK |
| 2017 | 259 | 0.8594 | -0.691 | 0.48931 | RANDOM_WALK |
| 2018 | 259 | 0.9164 | -0.451 | 0.65189 | RANDOM_WALK |
| 2019 | 259 | 0.7868 | -1.081 | 0.27956 | RANDOM_WALK |
| 2020 | 261 | 0.8518 | -0.363 | 0.71628 | RANDOM_WALK |
| 2021 | 260 | 0.8565 | -0.819 | 0.41292 | RANDOM_WALK |
| 2022 | 259 | 1.0029 | 0.014 | 0.98859 | RANDOM_WALK |
| 2023 | 259 | 0.9066 | -0.485 | 0.62756 | RANDOM_WALK |
| 2024 | 260 | 1.1642 | 0.762 | 0.44626 | RANDOM_WALK |
| 2025 | 259 | 0.6552 | -1.701 | 0.08903 | MEAN_REVERSION_SUGGESTIVE |

### GBPJPY

#### GBPJPY M15 (99,998 returns, 2022-03-28 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 0.9715 | -2.411 | *0.01590* | -9.018 | MEAN_REVERSION_MODERATE |
| 4 | 0.9617 | -1.974 | *0.04843* | -6.474 | MEAN_REVERSION_MODERATE |
| 8 | 0.9524 | -1.825 | 0.06799 | -5.090 | MEAN_REVERSION_SUGGESTIVE |
| 16 | 0.9428 | -1.708 | 0.08771 | -4.108 | MEAN_REVERSION_SUGGESTIVE |
| 32 | 0.9255 | -1.726 | 0.08437 | -3.693 | MEAN_REVERSION_SUGGESTIVE |
| 64 | 0.9200 | -1.430 | 0.15275 | -2.772 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 2.411 (q=2), p_Bonferroni = 0.0954*

*Temporal stability (H0=stable): **UNSTABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2022 | 18,987 | 0.8993 | -1.585 | 0.11306 | RANDOM_WALK |
| 2023 | 24,864 | 0.9962 | -0.121 | 0.90397 | RANDOM_WALK |
| 2024 | 24,954 | 1.0280 | 0.635 | 0.52557 | RANDOM_WALK |
| 2025 | 24,860 | 0.9180 | -2.414 | *0.01576* | MEAN_REVERSION_MODERATE |
| 2026 | 6,333 | 0.9075 | -1.297 | 0.19470 | RANDOM_WALK |

#### GBPJPY H1 (19,999 returns, 2023-01-16 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0124 | 1.061 | 0.28860 | 1.751 | RANDOM_WALK |
| 4 | 1.0129 | 0.585 | 0.55827 | 0.972 | RANDOM_WALK |
| 8 | 0.9978 | -0.066 | 0.94760 | -0.106 | RANDOM_WALK |
| 16 | 0.9888 | -0.235 | 0.81435 | -0.360 | RANDOM_WALK |
| 32 | 0.9341 | -1.009 | 0.31279 | -1.461 | RANDOM_WALK |
| 64 | 0.8767 | -1.396 | 0.16269 | -1.910 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 1.396 (q=64), p_Bonferroni = 0.9761*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2023 | 5,960 | 1.0738 | 1.300 | 0.19345 | RANDOM_WALK |
| 2024 | 6,239 | 1.0045 | 0.068 | 0.94604 | RANDOM_WALK |
| 2025 | 6,216 | 0.9297 | -1.309 | 0.19058 | RANDOM_WALK |
| 2026 | 1,584 | 0.8905 | -1.212 | 0.22548 | RANDOM_WALK |

#### GBPJPY H4 (9,999 returns, 2019-10-30 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0003 | 0.016 | 0.98745 | 0.029 | RANDOM_WALK |
| 4 | 0.9849 | -0.435 | 0.66379 | -0.807 | RANDOM_WALK |
| 8 | 0.9645 | -0.677 | 0.49833 | -1.200 | RANDOM_WALK |
| 16 | 0.9499 | -0.693 | 0.48839 | -1.139 | RANDOM_WALK |
| 32 | 0.9200 | -0.815 | 0.41486 | -1.254 | RANDOM_WALK |
| 64 | 0.8718 | -0.979 | 0.32776 | -1.405 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.979 (q=64), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2019 | 258 | 0.8792 | -0.464 | 0.64249 | RANDOM_WALK |
| 2020 | 1,563 | 1.0198 | 0.180 | 0.85719 | RANDOM_WALK |
| 2021 | 1,560 | 1.0921 | 1.154 | 0.24859 | RANDOM_WALK |
| 2022 | 1,554 | 0.9565 | -0.292 | 0.76991 | RANDOM_WALK |
| 2023 | 1,554 | 0.9655 | -0.352 | 0.72450 | RANDOM_WALK |
| 2024 | 1,560 | 0.8799 | -1.111 | 0.26644 | RANDOM_WALK |
| 2025 | 1,554 | 0.9116 | -0.933 | 0.35092 | RANDOM_WALK |
| 2026 | 396 | 1.1210 | 0.781 | 0.43504 | RANDOM_WALK |

#### GBPJPY D1 (2,999 returns, 2014-09-10 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0331 | 0.777 | 0.43694 | 1.810 | RANDOM_WALK |
| 4 | 1.0551 | 0.790 | 0.42945 | 1.612 | RANDOM_WALK |
| 8 | 1.0535 | 0.559 | 0.57638 | 0.991 | RANDOM_WALK |
| 16 | 1.0349 | 0.268 | 0.78866 | 0.435 | RANDOM_WALK |
| 32 | 0.9361 | -0.357 | 0.72112 | -0.548 | RANDOM_WALK |
| 64 | 0.8805 | -0.506 | 0.61260 | -0.717 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.790 (q=4), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **UNSTABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2015 | 259 | 1.0823 | 0.383 | 0.70142 | RANDOM_WALK |
| 2016 | 260 | 1.0216 | 0.074 | 0.94066 | RANDOM_WALK |
| 2017 | 259 | 1.1212 | 0.634 | 0.52593 | RANDOM_WALK |
| 2018 | 259 | 1.0067 | 0.038 | 0.96956 | RANDOM_WALK |
| 2019 | 259 | 1.2546 | 1.142 | 0.25358 | RANDOM_WALK |
| 2020 | 261 | 1.1688 | 0.649 | 0.51654 | RANDOM_WALK |
| 2021 | 260 | 1.0677 | 0.372 | 0.70989 | RANDOM_WALK |
| 2022 | 259 | 0.9780 | -0.108 | 0.91367 | RANDOM_WALK |
| 2023 | 259 | 0.6719 | -1.742 | 0.08142 | MEAN_REVERSION_SUGGESTIVE |
| 2024 | 260 | 1.2793 | 1.204 | 0.22848 | RANDOM_WALK |
| 2025 | 259 | 0.6874 | -1.584 | 0.11312 | RANDOM_WALK |

### GBPUSD

#### GBPUSD M15 (49,999 returns, 2024-03-31 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 0.9851 | -2.063 | *0.03913* | -3.326 | MEAN_REVERSION_MODERATE |
| 4 | 0.9784 | -1.634 | 0.10228 | -2.581 | RANDOM_WALK |
| 8 | 0.9560 | -2.167 | *0.03024* | -3.329 | MEAN_REVERSION_MODERATE |
| 16 | 0.9292 | -2.445 | *0.01449* | -3.595 | MEAN_REVERSION_MODERATE |
| 32 | 0.9064 | -2.362 | *0.01816* | -3.281 | MEAN_REVERSION_MODERATE |
| 64 | 0.8960 | -1.976 | *0.04817* | -2.546 | MEAN_REVERSION_MODERATE |

*Chow-Denning joint test: max|z*| = 2.445 (q=16), p_Bonferroni = 0.0870*

*Temporal stability (H0=stable): **UNSTABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2024 | 18,804 | 0.9835 | -0.480 | 0.63107 | RANDOM_WALK |
| 2025 | 24,859 | 0.9452 | -1.903 | 0.05705 | MEAN_REVERSION_SUGGESTIVE |
| 2026 | 6,336 | 0.9381 | -1.223 | 0.22136 | RANDOM_WALK |

#### GBPUSD H1 (19,999 returns, 2023-01-16 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 0.9859 | -1.402 | 0.16101 | -1.996 | RANDOM_WALK |
| 4 | 0.9804 | -1.077 | 0.28165 | -1.479 | RANDOM_WALK |
| 8 | 0.9725 | -0.995 | 0.31966 | -1.314 | RANDOM_WALK |
| 16 | 0.9565 | -1.135 | 0.25643 | -1.398 | RANDOM_WALK |
| 32 | 0.9503 | -0.960 | 0.33708 | -1.103 | RANDOM_WALK |
| 64 | 0.9143 | -1.193 | 0.23280 | -1.327 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 1.402 (q=2), p_Bonferroni = 0.9661*

*Temporal stability (H0=stable): **STABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2023 | 5,960 | 1.0281 | 0.564 | 0.57289 | RANDOM_WALK |
| 2024 | 6,239 | 0.9425 | -1.155 | 0.24824 | RANDOM_WALK |
| 2025 | 6,216 | 0.9562 | -0.924 | 0.35560 | RANDOM_WALK |
| 2026 | 1,584 | 0.8880 | -1.111 | 0.26663 | RANDOM_WALK |

#### GBPUSD H4 (9,999 returns, 2019-10-30 – 2026-04-03)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0070 | 0.333 | 0.73898 | 0.699 | RANDOM_WALK |
| 4 | 0.9814 | -0.448 | 0.65387 | -0.993 | RANDOM_WALK |
| 8 | 0.9821 | -0.284 | 0.77612 | -0.605 | RANDOM_WALK |
| 16 | 0.9910 | -0.106 | 0.91586 | -0.205 | RANDOM_WALK |
| 32 | 0.9906 | -0.083 | 0.93390 | -0.148 | RANDOM_WALK |
| 64 | 0.8918 | -0.720 | 0.47148 | -1.185 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 0.720 (q=64), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **UNSTABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2019 | 258 | 0.8605 | -0.478 | 0.63293 | RANDOM_WALK |
| 2020 | 1,563 | 1.1035 | 0.814 | 0.41546 | RANDOM_WALK |
| 2021 | 1,560 | 0.9828 | -0.231 | 0.81756 | RANDOM_WALK |
| 2022 | 1,554 | 0.9429 | -0.347 | 0.72869 | RANDOM_WALK |
| 2023 | 1,554 | 0.9922 | -0.099 | 0.92138 | RANDOM_WALK |
| 2024 | 1,560 | 0.8240 | -2.119 | *0.03413* | MEAN_REVERSION_MODERATE |
| 2025 | 1,554 | 0.9928 | -0.084 | 0.93295 | RANDOM_WALK |
| 2026 | 396 | 0.9096 | -0.590 | 0.55541 | RANDOM_WALK |

#### GBPUSD D1 (2,999 returns, 2014-09-09 – 2026-04-02)

| q | VR(q) | z* (robust) | p-value | z (homo) | Classification |
|---|---|---|---|---|---|
| 2 | 1.0230 | 0.628 | 0.53016 | 1.260 | RANDOM_WALK |
| 4 | 1.0271 | 0.447 | 0.65474 | 0.793 | RANDOM_WALK |
| 8 | 0.9666 | -0.385 | 0.70051 | -0.619 | RANDOM_WALK |
| 16 | 0.8704 | -1.080 | 0.28006 | -1.612 | RANDOM_WALK |
| 32 | 0.8114 | -1.172 | 0.24116 | -1.619 | RANDOM_WALK |
| 64 | 0.7919 | -0.981 | 0.32669 | -1.248 | RANDOM_WALK |

*Chow-Denning joint test: max|z*| = 1.172 (q=32), p_Bonferroni = 1.0000*

*Temporal stability (H0=stable): **UNSTABLE***

**Year-by-year at q=8:**

| Year | n | VR(8) | z* | p | Classification |
|---|---|---|---|---|---|
| 2015 | 259 | 0.9734 | -0.139 | 0.88927 | RANDOM_WALK |
| 2016 | 260 | 0.9023 | -0.321 | 0.74794 | RANDOM_WALK |
| 2017 | 259 | 0.7879 | -1.007 | 0.31384 | RANDOM_WALK |
| 2018 | 259 | 1.0261 | 0.142 | 0.88701 | RANDOM_WALK |
| 2019 | 259 | 1.0524 | 0.227 | 0.82084 | RANDOM_WALK |
| 2020 | 261 | 1.4610 | 1.655 | 0.09792 | MOMENTUM_SUGGESTIVE |
| 2021 | 260 | 0.7642 | -1.265 | 0.20592 | RANDOM_WALK |
| 2022 | 259 | 0.8555 | -0.609 | 0.54241 | RANDOM_WALK |
| 2023 | 259 | 0.7930 | -1.089 | 0.27601 | RANDOM_WALK |
| 2024 | 260 | 1.0264 | 0.138 | 0.89009 | RANDOM_WALK |
| 2025 | 259 | 0.8599 | -0.702 | 0.48298 | RANDOM_WALK |

---

## XAUUSD Kill Zone vs All-Hours Analysis (M15)

| Kill Zone | n returns | q | VR(q) | z* | p-value | Classification |
|---|---|---|---|---|---|---|
| London | 6682 | 2 | 1.0288 | 0.739 | 0.45974 | RANDOM_WALK |
| London | 6682 | 4 | 1.0962 | 1.111 | 0.26645 | RANDOM_WALK |
| London | 6682 | 8 | 1.1230 | 0.885 | 0.37617 | RANDOM_WALK |
| London | 6682 | 16 | 1.0604 | 0.320 | 0.74872 | RANDOM_WALK |
| NewYork | 7736 | 2 | 0.9854 | -0.689 | 0.49114 | RANDOM_WALK |
| NewYork | 7736 | 4 | 0.9843 | -0.390 | 0.69672 | RANDOM_WALK |
| NewYork | 7736 | 8 | 0.9848 | -0.239 | 0.81086 | RANDOM_WALK |
| NewYork | 7736 | 16 | 0.9555 | -0.490 | 0.62381 | RANDOM_WALK |
| All | 46626 | 2 | 0.9983 | -0.096 | 0.92338 | RANDOM_WALK |
| All | 46626 | 4 | 0.9954 | -0.148 | 0.88239 | RANDOM_WALK |
| All | 46626 | 8 | 0.9533 | -1.002 | 0.31614 | RANDOM_WALK |
| All | 46626 | 16 | 0.9245 | -1.174 | 0.24039 | RANDOM_WALK |

---

## GTOS Implications

### Q1 — XAUUSD H1 momentum vs mean-reversion?
VR(8) = **0.9727**, z* = -0.465, p = 0.64224 → **RANDOM_WALK**
(The OB-retest strategy trades on H1 structure; this classification is the relevant baseline autocorrelation regime.)

### Q2 — Strongest XAUUSD timescale signal?
Strongest: **H4 at q=8**, VR=1.1319, p=0.152403 → RANDOM_WALK

### Q3 — Kill zone vs all-hours (XAUUSD M15)?
All-hours  VR(8)=0.9533 → RANDOM_WALK
London KZ  VR(8)=1.1230 → RANDOM_WALK
NY KZ      VR(8)=0.9848 → RANDOM_WALK
If KZ classification differs from all-hours, kill zone selection is capturing a real structural difference.

### Q4 — Temporal stability (edge decay risk)?
- XAUUSD H1: STABLE
- US30 H1: STABLE
- USDJPY H1: STABLE
- GBPJPY H1: STABLE
- GBPUSD H1: STABLE

### Q5 — Cross-instrument differences at H1?
- XAUUSD H1: VR(8)=0.9727 p=0.64224 → RANDOM_WALK
- US30 H1: VR(8)=0.9933 p=0.90463 → RANDOM_WALK
- USDJPY H1: VR(8)=1.0182 p=0.57036 → RANDOM_WALK
- GBPJPY H1: VR(8)=0.9978 p=0.94760 → RANDOM_WALK
- GBPUSD H1: VR(8)=0.9725 p=0.31966 → RANDOM_WALK

---

## Statistical Caveats

- Bonferroni threshold for 120 simultaneous tests: α/120 ≈ 0.0004.  
  Only **STRONG** results (p < 0.01) are robustly significant after correction.
- D1 data: n < 2000, q=64 gives T/q < 30 — treat D1 q=64 as exploratory.
- XAUUSD M1: only ~4 months of data — results are exploratory only.
- Weekend/overnight gap returns are excluded from intraday VR (gaps > 3× expected bar).
- Kill zone VR: consecutive within-session returns concatenated across all dates;
  captures within-kill-zone autocorrelation structure, not cross-session momentum.
- Rolling VR(8) uses a 6-month window rolled monthly; short windows amplify noise.