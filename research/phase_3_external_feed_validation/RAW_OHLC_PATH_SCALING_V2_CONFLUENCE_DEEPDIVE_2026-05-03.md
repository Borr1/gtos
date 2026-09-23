# Raw OHLC Path Scaling V2 Confluence Deep Dive

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Discovery label: `DISCOVERY_ONLY_NOT_REGISTERED`

## Registered Question Before Outputs

Are V2 FVG/OB/Swing/Composite agreement and disagreement pockets structurally coherent enough to generate forward-test hypotheses, or are the same-dataset lifts concentrated artifacts?

## Bottom Line

FVG-only rows are a real discovery pocket but are much larger than OB-only rows and must be treated as concentration-sensitive. OB-after-FVG behavior is the cleanest structural pattern: when both fire, FVG usually appears first and OB often preserves more right tail. Composite is not globally useful, but its positive rows are worth studying as arbitration examples rather than as a blind highest-floor rule.

No result in this report is a promotion, replay registration, or live-logic recommendation.

## Slice Summary

| slice | n | FVG mean delta vs J46 | OB mean delta vs J46 | Composite mean delta vs J46 | FVG-OB mean | Composite-best mean | entry violations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full_resolved | 4394 | 0.033292 | 0.024061 | -0.042453 | 0.009231 | -0.296092 | 0 |
| year_2026 | 474 | 0.365975 | 0.233839 | 0.339326 | 0.132135 | -0.234958 | 0 |

## Direct Answers

- FVG-only rescue pockets: Full FVG-only improves bucket n=743; 2026 FVG-only improves bucket n=86. Use the JSON concentration panels for symbol/session/side/regime/year caps.
- OB-after-FVG tail preservation: The both-fired sequence table is the strongest support for the tail-preservation hypothesis; same-dataset only, not registered validation.
- Composite: Composite minus best single is globally negative in full data (-0.296092) and 2026 (-0.234958), so Composite remains an overlock warning. Positive composite rows are arbitration case studies only.
- OB-only: OB-only improves bucket is small in full data (n=88) and very small in 2026 (n=6), so OB-only claims have high small-sample risk.

## Leave-One Stress

Full resolved stress:

| dimension | excluded | excluded n | kept n | FVG delta mean | OB delta mean | FVG-OB mean | FVG sign flip | OB sign flip | FVG-OB sign flip |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| symbol | GBPJPY | 455 | 3939 | 0.013077 | 0.013592 | -0.000515 | False | False | True |
| symbol | GBPUSD | 715 | 3679 | 0.027385 | 0.020134 | 0.007250 | False | False | False |
| symbol | NAS100 | 732 | 3662 | 0.010984 | 0.026712 | -0.015728 | False | False | True |
| symbol | US30_cash | 278 | 4116 | 0.018396 | 0.025203 | -0.006807 | False | False | True |
| symbol | USDJPY | 1428 | 2966 | 0.108662 | 0.044908 | 0.063754 | False | False | False |
| symbol | XAGUSD | 319 | 4075 | 0.036807 | 0.018213 | 0.018594 | False | False | False |
| symbol | XAUUSD | 467 | 3927 | 0.034945 | 0.024895 | 0.010050 | False | False | False |
| session | london | 1529 | 2865 | 0.075639 | 0.019281 | 0.056358 | False | False | False |
| session | ny | 1477 | 2917 | -0.013507 | 0.030122 | -0.043629 | True | False | True |
| session | tokyo | 1388 | 3006 | 0.038345 | 0.022735 | 0.015610 | False | False | False |
| side | LONG | 3054 | 1340 | -0.104167 | 0.004816 | -0.108983 | True | False | True |
| side | SHORT | 1340 | 3054 | 0.093605 | 0.032505 | 0.061100 | False | False | False |
| year | 2022 | 495 | 3899 | 0.055562 | 0.027848 | 0.027714 | False | False | False |
| year | 2023 | 1121 | 3273 | 0.034564 | 0.040785 | -0.006222 | False | False | True |
| year | 2024 | 765 | 3629 | 0.057429 | 0.035989 | 0.021440 | False | False | False |
| year | 2025 | 1539 | 2855 | 0.025974 | 0.019384 | 0.006590 | False | False | False |
| year | 2026 | 474 | 3920 | -0.006935 | -0.001305 | -0.005630 | True | True | True |

2026-only stress:

| dimension | excluded | excluded n | kept n | FVG delta mean | OB delta mean | FVG-OB mean | FVG sign flip | OB sign flip | FVG-OB sign flip |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| symbol | GBPJPY | 71 | 403 | 0.197727 | 0.153575 | 0.044151 | False | False | False |
| symbol | GBPUSD | 103 | 371 | 0.346284 | 0.198601 | 0.147683 | False | False | False |
| symbol | NAS100 | 17 | 457 | 0.377037 | 0.239988 | 0.137050 | False | False | False |
| symbol | US30_cash | 24 | 450 | 0.356452 | 0.238104 | 0.118348 | False | False | False |
| symbol | USDJPY | 155 | 319 | 0.552955 | 0.362093 | 0.190863 | False | False | False |
| symbol | XAGUSD | 20 | 454 | 0.318296 | 0.154733 | 0.163562 | False | False | False |
| symbol | XAUUSD | 84 | 390 | 0.459150 | 0.325357 | 0.133792 | False | False | False |
| session | london | 189 | 285 | 0.334850 | 0.123661 | 0.211189 | False | False | False |
| session | ny | 125 | 349 | 0.472303 | 0.349659 | 0.122644 | False | False | False |
| session | tokyo | 160 | 314 | 0.276045 | 0.205113 | 0.070932 | False | False | False |
| side | LONG | 370 | 104 | 0.442884 | 0.370852 | 0.072031 | False | False | False |
| side | SHORT | 104 | 370 | 0.344357 | 0.195328 | 0.149029 | False | False | False |

## FVG-Only Rescue Pocket

Full bucket n: `743`. This is discovery-only and concentration-sensitive.

| dimension | positive contribution | top share | cap | cap exceeded | top group | top n | top contribution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| symbol | 602.582073 | 0.246623 | 0.450000 | False | {'symbol': 'NAS100'} | 158 | 148.610366 |
| session | 602.582073 | 0.476930 | 0.450000 | True | {'session': 'ny'} | 281 | 287.389717 |
| side | 602.582073 | 0.773367 | 0.450000 | True | {'side': 'LONG'} | 559 | 466.017219 |
| regime | 602.582073 | 0.692260 | 0.450000 | True | {'regime': 'D1'} | 559 | 417.143579 |
| year | 602.582073 | 0.481723 | 0.450000 | True | {'year': 2025} | 309 | 290.277463 |
| quarter | 602.582073 | 0.175312 | 0.450000 | False | {'quarter': '2025Q4'} | 108 | 105.639661 |
| symbol+session+side | 602.582073 | 0.246623 | 0.450000 | False | {'symbol': 'NAS100', 'session': 'ny', 'side': 'LONG'} | 158 | 148.610366 |
| raw_cohort_key | 602.582073 | 0.246623 | 0.450000 | False | {'raw_cohort_key': 'NAS100\|ny\|bullish\|D1'} | 158 | 148.610366 |

Top full-data FVG-only groups by FVG advantage over J46/OB:

| group | n | share n | mean metric | sum metric | mean FVG delta | mean OB delta |
| --- | --- | --- | --- | --- | --- | --- |
| {'symbol': 'NAS100', 'session': 'ny', 'side': 'LONG', 'regime': 'D1'} | 158 | 0.212651 | 0.940572 | 148.610366 | 0.940572 | -0.024838 |
| {'symbol': 'GBPJPY', 'session': 'tokyo', 'side': 'LONG', 'regime': 'D1'} | 91 | 0.122476 | 0.947026 | 86.179337 | 0.947026 | -0.001255 |
| {'symbol': 'GBPUSD', 'session': 'london', 'side': 'SHORT', 'regime': 'H4+H1_consensus'} | 91 | 0.122476 | 0.829632 | 75.496512 | 0.829632 | -0.088846 |
| {'symbol': 'XAUUSD', 'session': 'ny', 'side': 'LONG', 'regime': 'D1'} | 78 | 0.104980 | 0.918742 | 71.661886 | 0.918742 | -0.000653 |
| {'symbol': 'US30_cash', 'session': 'ny', 'side': 'LONG', 'regime': 'H4+H1_consensus'} | 45 | 0.060565 | 1.491499 | 67.117465 | 1.491499 | -0.291428 |
| {'symbol': 'USDJPY', 'session': 'tokyo', 'side': 'LONG', 'regime': 'D1'} | 78 | 0.104980 | 0.604692 | 47.165989 | 0.604692 | 0.000000 |
| {'symbol': 'USDJPY', 'session': 'tokyo', 'side': 'SHORT', 'regime': 'H4+H1_consensus'} | 48 | 0.064603 | 0.892177 | 42.824517 | 0.892177 | 0.000000 |
| {'symbol': 'XAGUSD', 'session': 'london', 'side': 'LONG', 'regime': 'D1'} | 59 | 0.079408 | 0.559759 | 33.025776 | 0.559759 | 0.000000 |
| {'symbol': 'USDJPY', 'session': 'tokyo', 'side': 'SHORT', 'regime': 'D1'} | 40 | 0.053836 | 0.444947 | 17.797869 | 0.444947 | -0.006304 |
| {'symbol': 'USDJPY', 'session': 'london', 'side': 'LONG', 'regime': 'D1'} | 50 | 0.067295 | 0.245128 | 12.256400 | 0.245128 | -0.144635 |
| {'symbol': 'USDJPY', 'session': 'london', 'side': 'SHORT', 'regime': 'D1'} | 5 | 0.006729 | 0.089191 | 0.445956 | 0.089191 | 0.000000 |

## OB-Only Pocket

Full bucket n: `88`. The 2026 OB-only bucket is especially small, so this is not a robust standalone branch.

| dimension | positive contribution | top share | cap | cap exceeded | top group | top n | top contribution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| symbol | 39.716532 | 0.326996 | 0.450000 | False | {'symbol': 'NAS100'} | 21 | 12.987136 |
| session | 39.716532 | 0.771660 | 0.450000 | True | {'session': 'ny'} | 55 | 30.647661 |
| side | 39.716532 | 0.950929 | 0.450000 | True | {'side': 'LONG'} | 80 | 37.767611 |
| regime | 39.716532 | 0.852965 | 0.450000 | True | {'regime': 'D1'} | 77 | 33.876822 |
| year | 39.716532 | 0.917592 | 0.450000 | True | {'year': 2025} | 74 | 36.443557 |
| quarter | 39.716532 | 0.519245 | 0.450000 | True | {'quarter': '2025Q2'} | 34 | 20.622597 |
| symbol+session+side | 39.716532 | 0.326996 | 0.450000 | False | {'symbol': 'NAS100', 'session': 'ny', 'side': 'LONG'} | 21 | 12.987136 |
| raw_cohort_key | 39.716532 | 0.326996 | 0.450000 | False | {'raw_cohort_key': 'NAS100\|ny\|bullish\|D1'} | 21 | 12.987136 |

## OB-After-FVG Tail Preservation

Sequence stats:

| slice | sequence | n | share | FVG mean | OB mean | OB-FVG mean | OB better share | OB floor-FVG floor | OB index-FVG index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_resolved | fvg_then_ob | 1075 | 0.855892 | 1.124681 | 1.427288 | 0.302607 | 0.640930 | 0.142855 | 11.861395 |
| full_resolved | ob_then_fvg | 130 | 0.103503 | 1.595068 | 1.663110 | 0.068043 | 0.338462 | -0.626425 | -2.846154 |
| full_resolved | same_time | 51 | 0.040605 | 1.868510 | 1.889935 | 0.021425 | 0.411765 | -0.628866 | 0.000000 |
| year_2026 | fvg_then_ob | 282 | 0.924590 | 0.520626 | 0.650964 | 0.130338 | 0.680851 | 0.100535 | 22.790780 |
| year_2026 | ob_then_fvg | 8 | 0.026230 | 0.554562 | 0.489936 | -0.064625 | 0.375000 | -0.157906 | -10.500000 |
| year_2026 | same_time | 15 | 0.049180 | 0.585828 | 0.712526 | 0.126698 | 1.000000 | -0.523884 | 0.000000 |

FVG-then-OB positive-contribution concentration:

| dimension | positive contribution | top share | cap | cap exceeded | top group | top n | top contribution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| symbol | 437.162802 | 0.333185 | 0.450000 | False | {'symbol': 'USDJPY'} | 294 | 145.656062 |
| session | 437.162802 | 0.379336 | 0.450000 | False | {'session': 'london'} | 376 | 165.831585 |
| side | 437.162802 | 0.669324 | 0.450000 | True | {'side': 'LONG'} | 798 | 292.603733 |
| regime | 437.162802 | 0.876239 | 0.450000 | True | {'regime': 'D1'} | 848 | 383.059007 |
| year | 437.162802 | 0.623062 | 0.450000 | True | {'year': 2025} | 555 | 272.379611 |
| quarter | 437.162802 | 0.315728 | 0.450000 | False | {'quarter': '2025Q1'} | 153 | 138.024480 |
| symbol+session+side | 437.162802 | 0.154478 | 0.450000 | False | {'symbol': 'NAS100', 'session': 'ny', 'side': 'LONG'} | 156 | 67.532006 |
| raw_cohort_key | 437.162802 | 0.154478 | 0.450000 | False | {'raw_cohort_key': 'NAS100\|ny\|bullish\|D1'} | 156 | 67.532006 |

## Composite Arbitration

| slice | positive n | negative n | match n | positive share | negative share | mean comp-best |
| --- | --- | --- | --- | --- | --- | --- |
| full_resolved | 590 | 1669 | 2135 | 0.134274 | 0.379836 | -0.296092 |
| year_2026 | 95 | 270 | 109 | 0.200422 | 0.569620 | -0.234958 |

Composite-positive full-data conditions with n>=10:

| group | n | share n | mean comp-best | sum comp-best | mean FVG-OB |
| --- | --- | --- | --- | --- | --- |
| {'symbol': 'NAS100', 'session': 'ny', 'side': 'LONG', 'regime': 'D1'} | 74 | 0.125424 | 0.685049 | 50.693637 | 0.167245 |
| {'symbol': 'GBPUSD', 'session': 'london', 'side': 'SHORT', 'regime': 'H4+H1_consensus'} | 73 | 0.123729 | 0.451246 | 32.940936 | 0.284947 |
| {'symbol': 'USDJPY', 'session': 'tokyo', 'side': 'SHORT', 'regime': 'H4+H1_consensus'} | 52 | 0.088136 | 0.513867 | 26.721062 | 0.507520 |
| {'symbol': 'GBPJPY', 'session': 'tokyo', 'side': 'LONG', 'regime': 'D1'} | 73 | 0.123729 | 0.339591 | 24.790111 | 0.502369 |
| {'symbol': 'XAGUSD', 'session': 'london', 'side': 'LONG', 'regime': 'D1'} | 48 | 0.081356 | 0.426384 | 20.466408 | 0.413031 |
| {'symbol': 'USDJPY', 'session': 'london', 'side': 'LONG', 'regime': 'D1'} | 49 | 0.083051 | 0.412652 | 20.219929 | 0.055870 |
| {'symbol': 'USDJPY', 'session': 'tokyo', 'side': 'LONG', 'regime': 'D1'} | 89 | 0.150847 | 0.223586 | 19.899188 | 0.128462 |
| {'symbol': 'USDJPY', 'session': 'tokyo', 'side': 'SHORT', 'regime': 'D1'} | 39 | 0.066102 | 0.394101 | 15.369939 | 0.182151 |
| {'symbol': 'US30_cash', 'session': 'ny', 'side': 'LONG', 'regime': 'H4+H1_consensus'} | 42 | 0.071186 | 0.273673 | 11.494272 | 0.653172 |
| {'symbol': 'XAUUSD', 'session': 'ny', 'side': 'LONG', 'regime': 'D1'} | 35 | 0.059322 | 0.311106 | 10.888695 | 0.320839 |
| {'symbol': 'USDJPY', 'session': 'london', 'side': 'SHORT', 'regime': 'D1'} | 16 | 0.027119 | 0.466067 | 7.457077 | 0.020648 |

## Representative 2026 Casebook

## Market-Structure Coherence Basis

Status: `LOG_METADATA_ONLY_NOT_CHART_REVIEW`

These flags show structure-sequence coherence in the replay log. They are not manual chart validation and do not prove a forward edge.

For OB-after-FVG examples, the coherent replay-log pattern requires:

- both FVG and OB structural variants fired
- FVG first lock confirmed before OB first lock
- OB first lock confirmed on a later selected-timeframe index
- OB lock floor is above the FVG lock floor for LONG-side R accounting, or otherwise preserves more realized R
- OB net R exceeds FVG net R on the same event key

FVG-only examples:

| event | symbol | session | side | regime | J46 | FVG | OB | Composite | FVG-OB | fire bucket | sequence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|2026-01-13T15:15:00+00:00 | XAUUSD | ny | LONG | D1 | -1.050000 | 1.314986 | -1.050000 | 0.681998 | 2.364986 | fvg_only_fired | n/a |
| XAUUSD\|2026-01-13T15:30:00+00:00 | XAUUSD | ny | LONG | D1 | -1.050000 | 1.314162 | -1.050000 | 0.681556 | 2.364162 | fvg_only_fired | n/a |
| XAUUSD\|2026-01-13T16:15:00+00:00 | XAUUSD | ny | LONG | D1 | -1.050000 | 1.297409 | -1.050000 | 1.041794 | 2.347409 | fvg_only_fired | n/a |
| XAUUSD\|2026-01-13T16:30:00+00:00 | XAUUSD | ny | LONG | D1 | -1.050000 | 1.288524 | -1.050000 | 1.034594 | 2.338524 | fvg_only_fired | n/a |
| XAUUSD\|2026-01-13T15:45:00+00:00 | XAUUSD | ny | LONG | D1 | -1.050000 | 1.286134 | -1.050000 | 0.666525 | 2.336134 | fvg_only_fired | n/a |
| XAUUSD\|2026-01-13T16:00:00+00:00 | XAUUSD | ny | LONG | D1 | -1.050000 | 1.285067 | -1.050000 | 1.031793 | 2.335067 | fvg_only_fired | n/a |
| XAUUSD\|2026-01-13T16:45:00+00:00 | XAUUSD | ny | LONG | D1 | -1.050000 | 1.283761 | -1.050000 | 1.030735 | 2.333761 | fvg_only_fired | n/a |
| XAUUSD\|2026-01-13T17:00:00+00:00 | XAUUSD | ny | LONG | D1 | -1.050000 | 1.267286 | -1.050000 | 0.656418 | 2.317286 | fvg_only_fired | n/a |

OB-only examples:

| event | symbol | session | side | regime | J46 | FVG | OB | Composite | FVG-OB | fire bucket | sequence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|2026-03-04T16:00:00+00:00 | XAUUSD | ny | LONG | D1 | 0.377054 | 0.326478 | 0.609705 | 0.160998 | -0.283227 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-12T15:15:00+00:00 | XAUUSD | ny | LONG | D1 | 1.531889 | 0.567306 | 1.759844 | -0.030316 | -1.192538 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-12T15:30:00+00:00 | XAUUSD | ny | LONG | D1 | 1.528837 | 0.566115 | 1.756353 | -0.030354 | -1.190238 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-12T15:45:00+00:00 | XAUUSD | ny | LONG | D1 | 1.524585 | 0.564456 | 1.751488 | -0.030407 | -1.187032 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-12T16:00:00+00:00 | XAUUSD | ny | LONG | D1 | 1.511369 | 0.559298 | 1.736368 | -0.030571 | -1.177070 | both_fired | fvg_then_ob |
| XAUUSD\|2026-03-04T16:30:00+00:00 | XAUUSD | ny | LONG | D1 | 0.432759 | 0.330520 | 0.616789 | 0.163264 | -0.286269 | both_fired | fvg_then_ob |

OB-after-FVG tail-preservation examples:

| event | symbol | session | side | regime | J46 | FVG | OB | Composite | FVG-OB | fire bucket | sequence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|2026-01-22T16:45:00+00:00 | XAUUSD | ny | LONG | D1 | 4.329986 | 0.217985 | 2.584211 | 0.240155 | -2.366226 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-12T15:15:00+00:00 | XAUUSD | ny | LONG | D1 | 1.531889 | 0.567306 | 1.759844 | -0.030316 | -1.192538 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-12T15:30:00+00:00 | XAUUSD | ny | LONG | D1 | 1.528837 | 0.566115 | 1.756353 | -0.030354 | -1.190238 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-12T15:45:00+00:00 | XAUUSD | ny | LONG | D1 | 1.524585 | 0.564456 | 1.751488 | -0.030407 | -1.187032 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-12T16:00:00+00:00 | XAUUSD | ny | LONG | D1 | 1.511369 | 0.559298 | 1.736368 | -0.030571 | -1.177070 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-20T16:15:00+00:00 | XAUUSD | ny | LONG | D1 | 2.035141 | 0.273434 | 1.083383 | 0.289797 | -0.809949 | both_fired | fvg_then_ob |
| XAUUSD\|2026-01-20T16:30:00+00:00 | XAUUSD | ny | LONG | D1 | 2.027754 | 0.272288 | 1.079368 | 0.272288 | -0.807080 | both_fired | fvg_then_ob |
| XAGUSD\|2026-02-03T10:15:00+00:00 | XAGUSD | london | LONG | D1 | 0.822860 | -0.026804 | 0.660104 | 0.077321 | -0.686908 | both_fired | fvg_then_ob |

Composite-positive examples:

| event | symbol | session | side | regime | J46 | FVG | OB | Composite | FVG-OB | fire bucket | sequence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAS100\|2026-02-03T16:15:00+00:00 | NAS100 | ny | LONG | D1 | -1.050000 | -1.050000 | -1.050000 | 0.004458 | 0.000000 | neither_fired | n/a |
| NAS100\|2026-02-03T16:30:00+00:00 | NAS100 | ny | LONG | D1 | -1.050000 | -1.050000 | -1.050000 | 0.004148 | 0.000000 | neither_fired | n/a |
| NAS100\|2026-02-03T15:15:00+00:00 | NAS100 | ny | LONG | D1 | -1.050000 | -1.050000 | -1.050000 | 0.004072 | 0.000000 | neither_fired | n/a |
| NAS100\|2026-02-03T15:30:00+00:00 | NAS100 | ny | LONG | D1 | -1.050000 | -1.050000 | -1.050000 | 0.004057 | 0.000000 | neither_fired | n/a |
| NAS100\|2026-02-03T15:45:00+00:00 | NAS100 | ny | LONG | D1 | -1.050000 | -1.050000 | -1.050000 | 0.004019 | 0.000000 | neither_fired | n/a |
| NAS100\|2026-02-03T16:00:00+00:00 | NAS100 | ny | LONG | D1 | -1.050000 | -1.050000 | -1.050000 | 0.003895 | 0.000000 | neither_fired | n/a |
| NAS100\|2026-02-03T14:15:00+00:00 | NAS100 | ny | LONG | D1 | -1.050000 | -1.050000 | -1.050000 | 0.003852 | 0.000000 | neither_fired | n/a |
| NAS100\|2026-02-03T14:30:00+00:00 | NAS100 | ny | LONG | D1 | -1.050000 | -1.050000 | -1.050000 | 0.003625 | 0.000000 | neither_fired | n/a |

## Missing Fields And Blockers

- `pre_fill_delivery_path_rows`: Cannot test delivery-leg plus reversal-leg structure from current post-fill event log.
- `pending_limit_lifecycle_state`: Cannot distinguish broker fill/expiry/cancel/no-trigger states for pre-fill hypotheses.
- `data_source`: Event rows do not expose an immutable data-source label beyond event-log path and cohort metadata.

## Forward-Only Fields V2b Should Collect

- `event_key`
- `symbol`
- `session`
- `side`
- `raw_cohort_key`
- `regime`
- `setup_decision_close_utc`
- `pending_limit_created_utc`
- `original_poi_type_and_bounds`
- `fill_or_expiry_state`
- `selected_path_timeframe`
- `lower_tf_available`
- `fvg_fired`
- `ob_fired`
- `swing_fired`
- `composite_fired`
- `fvg_first_lock_time_and_floor_r`
- `ob_first_lock_time_and_floor_r`
- `sequence_bucket`
- `j46_net_r_by_cost`
- `fvg_net_r_by_cost`
- `ob_net_r_by_cost`
- `swing_net_r_by_cost`
- `composite_net_r_by_cost`
- `same_bar_ambiguity_state`
- `actual_broker_r_if_available`
- `synthetic_path_r_if_available`
- `fill_no_fill_label`
- `cost_model_version`

## Opened Hypotheses

- `V2DD-H1-FVG-ONLY-RESCUE-POCKET` (DISCOVERY_ONLY_NOT_REGISTERED): FVG floors may rescue post-entry failures when no qualifying OB floor forms. Risk: May be concentrated in a few symbol/session/regime/year pockets.
- `V2DD-H2-FVG-THEN-OB-TAIL-PRESERVATION` (DISCOVERY_ONLY_NOT_REGISTERED): FVG appears first as delivery continuation, then OB acts as later protective floor. Risk: Current event log is post-fill only and cannot prove pre-fill delivery-leg structure.
- `V2DD-H3-COMPOSITE-ARBITRATION-NOT-BLIND-COMPOSITE` (DISCOVERY_ONLY_NOT_REGISTERED): Composite may help only under arbitration conditions where it avoids both single-selector failure modes. Risk: Global mean is negative and same-dataset positive cases may be selected artifacts.

## Next Steps

1. Build a forward-only confluence ledger once V2b has resolved post-cutoff pairs.
2. Use pre-fill delivery-path capture before scoring the two-leg delivery/reversal hypothesis.
3. Do not promote FVG-only, OB-after-FVG, or Composite arbitration without pre-registered unseen validation.
