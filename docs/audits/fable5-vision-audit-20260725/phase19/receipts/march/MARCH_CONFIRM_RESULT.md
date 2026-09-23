# MARCH_CONFIRM_RESULT — the March 2026 one-shot, executed

Session MARCH-EXEC, 2026-08-05/06. Executes `MARCH_PREREG_V1` under OD-FA2-1 on
Borhen's word of 2026-08-05. Branch `phase19/march-confirm`; `main` untouched.

**Evidence class.** March 2026 is the estate's only never-decoded month. It has now
been decoded ONCE, under a protocol frozen before any March byte existed. Every
number below is lane evidence, `billed:false`, C7-censored (all walked outcomes are
120-minute-wall MTM-censored, symmetrically across arms). **Nothing here is
admission-grade, and §6 of the prereg forbids reading any monthly delta as a powered
economic test — a restriction the results below make load-bearing rather than
theoretical.**

---

## 0. TL;DR — three findings

**1. The January mechanism story reproduces out-of-window. Five of five primary
endpoints PASS, both census bands PASS.** Cost truth widens the funnel (2.17×,
January 2.42×); belief honesty stands the system down (0.118×, January 0.105×); the
declared ceiling composes to near-silence (8 trades against an 11-trade bar); the
wrapper machinery is byte-exactly inert (0 set difference, 0 moved trades, book delta
0.0000); and the billed V27 candidate remains inexpressible through the R-denominated
cost gate (0 transformed admissions, 100 % cost-refusal). This is the strongest
result the confirm could have produced, and it was produced on a month that could not
have been fitted to.

**2. Not one economic number in March is distinguishable from zero — including the
baseline's.** March's frozen R0 book is **+7.32 R on 110 trades**, where January's
was −5.51 on 57. That looks like a sign flip and **it is not one**: the daily
bootstrap 90 % interval on March's R0 monthly total is **[−5.97, +20.60]**, and
January's was **[−17.98, +6.64]**. Both span zero, and they overlap each other
heavily. Every one of the six March arms spans zero on its own book. The prereg
predicted a monthly MDE of 20–26 R and said a single month cannot certify economic
magnitudes; that is now measured rather than asserted. **The mechanism confirms carry
this result. The economics carry nothing.**

**3. The transform is worse than useless on March — it costs a trade.** In January
arm (v) was byte-identical to arm (iii): the transform bought zero trades and changed
nothing. In March it buys zero trades **and deletes one**: the untransformed breaker
candidate at `2026-03-31 US30_cash SHORT` is admitted by arm (iii) and refused once
transformed. The entire (v) − (iii) book delta of **+1.0408 R is exactly that one
trade's net** (−1.04083, a loss — so removing it happens to help). P5 is confirmed in
a strictly stronger form than January stated it: the R-denominated gate does not
merely fail to admit high-RR geometry, it withdraws admission from geometry it would
otherwise have accepted.

---

## 1. The five PRIMARY endpoints (frozen thresholds, §4)

| # | claim | rule | March measured | Jan | verdict |
|---|---|---|---|---|---|
| **P1** | cost truth widens the funnel | trades(I) ≥ 1.5 × trades(R0) | **239 ≥ 165** (2.1727×) | 2.42× | **PASS** |
| **P2** | belief honesty stands down | trades(II) ≤ 0.25 × trades(R0) | **13 ≤ 27.5** (0.1182×) | 0.105× | **PASS** |
| **P3** | ceiling composes to near-silence | trades(III) ≤ max(3, 0.10 × trades(R0)) | **8 ≤ 11** | 1 | **PASS** |
| **P4** | machinery is inert | set(IV) == set(R0), per-trade ≤ 1e-9 | **0 / 0 set diff, 0 moved, Δ 0.0000** | exact | **PASS** |
| **P5** | the edge is inexpressible | transformed admissions == 0 **AND** refusal ≥ 99 % | **0 admissions, 100.0 % refused** | 0; 100 % | **PASS** |

R0 March = **110 trades**, so no count bar is degenerate: the scorer's power note
reads *"adequate: R0 book is thick enough for the count bar to discriminate"* on all
three count endpoints. January's R0 was 57 trades — March's baseline is nearly twice
as thick, which makes P1–P3 harder to pass by accident, not easier.

**P3 deserves one honest qualification.** It passes at 8 trades against an 11-trade
bar, where January passed at 1. The threshold is frozen and 8 ≤ 11, so the verdict is
PASS and stands. But "near-silence" is a weaker description of 8 trades than of 1,
and the margin is 3 trades. A reader entitled to the strongest version of this claim
should take January's, not March's.

**P5's sub-question stays NOT_EVALUABLE, correctly.** The prereg makes the trade-TP
provenance question (candidate 5D vs policy 2R) conditional on at least one
transformed admission. There are zero, so it is `NOT_EVALUABLE_zero_transformed_
admissions` — the same terminal January reached, for the same reason.

## 2. The two CENSUS bands (§4, secondary)

| # | claim | band | March | Jan | verdict |
|---|---|---|---|---|---|
| **S1** | frozen / truthed spread ratio | [4, 16] | **7.3113** (73,631.07 R frozen vs 10,070.91 R truthed over 116,267 of 130,124 packets) | 8.48 | **PASS** |
| **S2** | transformed / untransformed median breaker `cost_r` | [2, 8] | **3.5858** (0.532573 vs 0.148522 over 9,847 breaker candidates; 9,847/9,847 refused transformed, 9,026/9,847 with 820 executable untransformed) | 3.67 | **PASS** |

Both land close to their January values on independent data. S1's overcharge is
**7.3× in March against 8.5× in January** — the same phenomenon, slightly smaller.

## 3. Economics — ESTIMATION ONLY (§5), and the intervals are the point

| arm | composition | trades | book net R | Δ vs R0 | seed band (0.751 R) | daily Δ sd | bootstrap 90 % on monthly Δ |
|---|---|---:|---:|---:|---|---:|---|
| r0 | CJ recipe (frozen costs) | 110 | **+7.3243** | — | — | — | — |
| (i) | + R-COST-TRUTH | 239 | +4.5240 | −2.8004 | outside | 3.3780 | [−27.70, +23.12] |
| (ii) | + R-BELIEF + R-SCHEMA | 13 | −4.3634 | −11.6877 | outside | 1.8997 | [−25.87, +2.57] |
| (iii) | + `cost_ceiling_0p05` | 8 | −1.9553 | −9.2796 | outside | 1.9771 | [−23.89, +5.23] |
| (iv) | CJ pair + 8 inert controls | 110 | +7.3243 | **+0.0000 exact** | INSIDE | 0.0000 | [0, 0] |
| (v) | (iii) + breaker transform | 7 | −0.9145 | −8.2388 | outside | 2.0144 | [−23.07, +6.55] |

**Every book, including the baseline's, spans zero:**

| arm | book | 90 % interval on its own monthly total | spans 0 |
|---|---:|---|---|
| r0 | +7.3243 | [−5.9730, +20.6023] | yes |
| (i) | +4.5240 | [−23.3452, +33.6655] | yes |
| (ii) | −4.3634 | [−10.7228, +2.0216] | yes |
| (iii) | −1.9553 | [−7.2922, +3.5079] | yes |
| (iv) | +7.3243 | [−5.9730, +20.6023] | yes |
| (v) | −0.9145 | [−6.2373, +4.4224] | yes |

Four deltas sit outside the 0.751 R seed band, so they are not seed noise — but
"larger than the seed band" is a far weaker statement than "distinguishable from
zero", and none of them clears the second bar. **No arm's economics may be quoted as
a direction.**

### 3.1 Contest sites separated from shared-trade economics (B2 rule 3)

| arm | shared | moved | mean Δ/trade | Σ shared Δ | only-arm (n, ΣR) | only-r0 (n, ΣR) | admission Δ |
|---|---:|---:|---:|---:|---|---|---:|
| (i) | 63 | 22 | +0.00654 | +0.386 | 176, +7.617 | 47, +10.804 | −3.186 |
| (ii) | 4 | 4 | +0.03261 | +0.130 | 9, −4.968 | 106, +6.850 | −11.818 |
| (iii) | 4 | 4 | +0.03261 | +0.130 | 4, −2.560 | 106, +6.850 | −9.410 |
| (iv) | 110 | 0 | 0.0 | 0.0000 | 0, 0.000 | 0, 0.000 | +0.000 |
| (v) | 3 | 3 | +0.02971 | +0.089 | 4, −2.560 | 107, +5.768 | −8.328 |

The January structural finding survives intact and is arguably clearer here:
**cost and belief repairs move the ADMISSION GATE, not booked fill economics.**
Shared-trade movement is ≤ +0.033 R/trade everywhere; every material delta is
admission-side. Note one March difference: on arms (ii)/(iii)/(v) *all* shared trades
moved (4/4, 4/4, 3/3), where January's arm (ii) moved 0 of 1 — the belief bundle
reprices what it keeps, it just keeps almost nothing.

### 3.2 Scoreability — a qualification on arm (i) in both months

| arm | January unscoreable | March unscoreable |
|---|---|---|
| r0 | 2/57 = 3.5 % | 10/110 = 9.1 % |
| **(i)** | **31/138 = 22.5 %** | **80/239 = 33.5 %** |
| (ii) | 1/6 = 16.7 % | 0/13 = 0 % |
| (iii) | 0/1 | 0/8 = 0 % |
| (iv) | 2/57 = 3.5 % | 10/110 = 9.1 % |
| (v) | 0/1 | 0/7 = 0 % |

Unscoreable rows contribute 0.0 to a book total. **A third of arm (i)'s March
admissions carry no scoreable outcome**, so its +4.52 describes 159 trades, not 239.
This does not touch P1, which is a count endpoint and counts admissions — but it is a
real limit on arm (i)'s economics that reproduces across both months and was not
stated in the January write-up.

## 4. What changed vs January

**Confirmed unchanged (the mechanism story):** all five primaries and both census
bands, with March's ratios landing near January's on every one (2.17 vs 2.42; 0.118
vs 0.105; inert vs inert; 0/100 % vs 0/100 %; 7.31 vs 8.48; 3.59 vs 3.67).

**Changed, and it matters:**

1. **The baseline's sign.** January R0 −5.51 / 57 trades; March R0 **+7.32 / 110
   trades**. Both indistinguishable from zero and mutually overlapping. **This is the
   single most misquotable number in the document.** "The broad pool is positive in
   March" is not a claim this evidence supports.
2. **The repaired books are negative in March where January's were slightly
   positive.** Arm (ii) +0.58 → **−4.36**; arm (iii) +0.15 → **−1.96**; arm (v)
   +0.15 → **−0.91**. All four are noise-level in their own month. What survives both
   months is the *structural* verdict, not the sign: the honest system stands down.
3. **Arm (v) now costs a trade** (§0 finding 3) instead of being byte-identical to
   arm (iii). A strictly stronger form of P5.
4. **P3's margin narrowed** from 1 trade to 8 against an 11-trade bar.
5. **Zero fragment rebinds** in March against January's three, and March's pack config
   authority is byte-identical to January's `runtime_v3` — so the substrate difference
   between the two months is market data and nothing else.

## 5. What I got wrong (register)

1. **My analyzer read `economics` where the runner writes `economics_counts`.** The
   January self-check could not catch it: it compares against FA's published JSONs,
   which a *different* extractor wrote, so the field simply came back `None` for all
   four counts and matched nothing that was being compared. Found by reading the March
   receipts directly. **Blast radius: none on any scored value** — every trade count
   the endpoints use comes from the analyzer's own ledger walk, and S1 reads
   `repair_report`, which was correct. It corrupted an informational echo only. But it
   is exactly the class of bug a self-check *looks* like it covers and does not.
2. **My first draft of `transformed_trades` counted arm-only breaker trades against
   r0** and reported 9 for arm (i) — an arm with no transform installed. Fixed to
   measure against the arm's own control before March ran; the March result depends on
   that fix.
3. **My first monitor tailed a log file that did not exist yet**, so it silently
   followed only the chain log and would never have reported an arm boundary. Caught
   because the R0 start line produced no notification.
4. **I let the fast-forward to `main` run without anticipating sparse-checkout**, which
   deleted 26,618 files including two prereg-FROZEN substrate JSONs. Caught only
   because I re-hashed the substrate after the merge instead of assuming it survived.
   Had I not, six arms would have run against a substrate the prereg does not
   describe and the whole confirm would have been silently invalid.
5. **I did not anticipate that the tick sources had been iCloud-evicted.** The first
   materialization blocked ten minutes at 0 % CPU with a 0-byte output — which reads
   exactly like a hung job — before `brctl status` named it as a download.
6. **My initial framing of the March R0 result was wrong in my own head.** On seeing
   +7.32 against January's −5.51 my first reading was "the sign flipped between
   months". Computing both bootstrap intervals refuted that: they overlap and both
   span zero. I would have published a sign flip if I had reported before measuring.
7. **I wrote the wrong S2 medians into the first draft of this report** — "0.6842 vs
   0.1908" — when the census says **0.532573 vs 0.148522**. The ratio 3.5858 was
   correct because it came from the artifact; the two numbers behind it did not, and I
   transcribed them from nothing. Caught by re-reading `MARCH_POOL_CENSUS.json`
   against my own prose before landing. Every other figure in this document has now
   been re-checked the same way.

## 6. What this confirm does and does not settle

**Settles:** the five mechanism claims derived on January hold on a month that could
not have been fitted to. The cost layer's overcharge, the belief stack's stand-down,
the ceiling's near-silence, the machinery's inertness, and the cost gate's structural
exclusion of high-RR geometry are properties of the ENGINE, not artifacts of January.

**Does not settle:** anything economic. Six arms, six intervals, six spanning zero.
The one-shot was designed to test mechanism, and §6 said so before the data existed;
the data agreed.

**Does not settle, and is now a live question:** whether the broad pool's frozen book
is negative at all. January said −5.51, March says +7.32, and neither is
distinguishable from zero. The honest statement is **"the frozen broad book is
indistinguishable from zero in both months measured"** — which is a different claim
from the one the estate has been carrying.

## 7. Receipts

All under `docs/audits/fable5-vision-audit-20260725/phase19/receipts/march/`, branch
`phase19/march-confirm`.

| artifact | sha256 (first 16) |
|---|---|
| `MARCH_PREFLIGHT_METADATA_V1.json` | `2b2d590ea0b0aa29` |
| `MARCH_SOURCES_RECEIPT_V1.json` | `f429474d19d34b43` |
| `MARCH_PACKS_RECEIPT_V1.json` | `c54b267619d8a776` |
| `MARCH_SOURCE_PLAN_RECEIPT_V1.json` | `2e98fea658dfab72` |
| `MARCH_ANALYZER_SELFCHECK_V1.json` | `e923f8f6e365111b` |
| `MARCH_SCORER_DRYRUN_V1.json` | `d89f28aff3bd7e74` |
| `MARCH_ENDPOINT_SCORES_V1.json` | `69ac07a5847f2005` |
| `analysis/MARCH_ARM_R0_ANALYSIS.json` | `908da9d49a818efa` |
| `analysis/MARCH_ARM_I_ANALYSIS.json` | `99d8fe8d210090f8` |
| `analysis/MARCH_ARM_II_ANALYSIS.json` | `cde93da23942bbc9` |
| `analysis/MARCH_ARM_III_ANALYSIS.json` | `e3cd15e8738c43b0` |
| `analysis/MARCH_ARM_IV_ANALYSIS.json` | `b37e652eb1cea6e9` |
| `analysis/MARCH_ARM_V_ANALYSIS.json` | `e0edb76e3239b643` |
| `analysis/MARCH_POOL_CENSUS.json` | `5b65dbd9e13fc931` |
| `arm_receipts/FA2_M_R0_RECEIPT.json` | `cedce7334871d6bc` |
| `arm_receipts/FA2_M_ARM_I_RECEIPT.json` | `3adf78c1e846dc75` |
| `arm_receipts/FA2_M_ARM_II_RECEIPT.json` | `82fa93422f2b3317` |
| `arm_receipts/FA2_M_ARM_III_RECEIPT.json` | `f88ea16523b3cb4b` |
| `arm_receipts/FA2_M_ARM_IV_RECEIPT.json` | `5c1b6bad1689b3f2` |
| `arm_receipts/FA2_M_ARM_V_RECEIPT.json` | `04f2d6a5d533100d` |

March lane window: source manifest `f74b7f95cae570c9…`, canonical source-plan digest
`8163172cbae28ae943ae940f3293bb2272671114e9e9bc0de3a7e04f79ffdf8e`, 31/31 packs,
2,880 records. The four CJ windows are byte-identical before and after, and January's
plan digest is still `b44b433039bf7f53…`.

Six arms, six `error: None`, all `resolved_window_id: march_2026`. **Zero
NOT_EVALUABLE terminals were reached.** Wall 9,751.7 / 14,471.8 / 6,630.6 / 6,198.1 /
9,619.9 / 6,154.0 s; peak RSS 3.59–4.35 GB.

## 8. The decision is Borhen's

The prereg reserves kill / park / iterate on the broad family to the owner, and this
session does not make it. What the evidence supports, stated neutrally:

- **Kill** is now better-evidenced than it was: the mechanism story is complete,
  internally consistent, and confirmed out-of-window on the last virgin month. The
  repaired system's verdict on this pool is stand down, in both months measured.
- **Park** costs nothing further and loses nothing. The repairs are landed and reusable;
  the lane packs for Jan/Feb/Mar/Apr/May exist; nothing decays.
- **Iterate** has one honest new argument and one honest new caution. The argument:
  arm (v)'s March behaviour sharpens the case for the licensed-not-built
  price/notional-denominated cost gate, because the R-denominated gate now demonstrably
  *withdraws* admission rather than merely failing to extend it — and that defect is a
  SYSTEM capability limit that would bind any future high-RR candidate, not a
  broad-family problem. The caution: nothing in March suggests the broad pool itself
  is worth more work.
- **One thing worth knowing before any of the three:** March is now used. It was the
  only never-decoded month, and it has been decoded once, exactly as specified. There
  is no second virgin month behind it.

**March is spent. What it bought is a confirmed mechanism and an explicitly
unpowered economics. The next move is yours.**
