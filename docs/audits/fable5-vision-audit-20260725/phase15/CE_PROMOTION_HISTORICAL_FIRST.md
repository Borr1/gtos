# Promotion, restated historical-primary — the `mx_btcusd` amendment and the template

Session CE (B2330–B2339). Authority: `phase15/OD_HISTORICAL_FIRST_SCALING.md` §1, which names
this rule as the first instance to restate. **CA's sealed dossier is not edited.** The
amendment is `phase15/receipts/CE_MX_PROMOTION_AMENDMENT_V1.json`, the registry row is an
`incubation_rule_amendment` written through the API, and the agreement language for
`WAVE_11_WORKING_AGREEMENT.md` §6 is §5 below.

---

## 1. What was wrong, in one paragraph, and CA said it first

`mx_btcusd`'s promotion rule was: **cumulative net R ≥ +34 over 60 live fills**, measured
false-promotion probability **0.097**. At the sleeve's measured live-equivalent fill rate of
0.270 fills/week that is **about 51 calendar months**, and CA's own dossier says so:

> *"The promotion rule is therefore NOT a plan to promote — it is the honest price of promotion
> on evidence, and the estate should read it as an argument for a cheaper instrument rather
> than as a schedule."*

That is a correctly-derived rule under the old frame and a **mis-derived** one under
OD-HISTORICAL-FIRST §1, which says the live stream is a veto and never the clock. CA was right
about the arithmetic and right that it pointed somewhere else; the directive is what makes
"somewhere else" an obligation.

**It was amended at ZERO live fills.** The sleeve was armed 2026-07-31 ~01:26Z and
`CA_FIRST_WEEK_V1.json` puts the expected fills since at **0.105**. There is no live record
this restatement could have been fitted to, and that is the only clean moment a promotion rule
can ever be rewritten. The registry records it in a field nobody has to compute:
`amended_on_a_virgin_record: true`.

---

## 2. The restated rule — P1-HIST

Promotion off the 0.025 class toward the 0.05 incubation ceiling requires **all four
milestones AND the absence of the live veto**.

| # | milestone | threshold | data | looks |
|---|---|---|---|---:|
| **M1** | cross-**broker** replication: the same spec re-gated on the **redacted_account** BTCUSD D1 archive | ADMIT at ≥ 2 of 3 bands, same sign, recent-two-fold mean > 0 | `redacted_account_BTCUSD_D1.csv.gz`, 2,244 bars, 2017-06-12…2026-07-27, **on this machine now** | 1 |
| **M2** | cross-**instrument** mechanism replication: `d1_donchian_20_breakout @ target_5R` on `mx_ethusd` (311), `mx_avausd` (189), `mx_nzdjpy` (503) | pooled OOS mean R/day > 0 on **all three**, and ADMIT at ≥ 2 of 3 bands on **at least one** | `AQ_ESTATE_TRADES_V2.json.gz`, already captured at the repaired time-stop unit | 3 |
| **M3** | the two repairs the admission is contingent on still hold | `time_stop_bars == time_stop_m15(80,"D1")` **and** AU's frontier trade-identity at 318/318 | code | 0 |
| **M4** | no chronological decay | recent-two-fold mean R/day > 0 on the M1/M2 cut | a column of the same runs | 0 |
| **V** | **the live veto** | no stop rule fired **and** no live-vs-historical contradiction | the live stream | — |

**The calendar this implies is ZERO waiting.** Every input exists on this machine today. M1 and
M2 are gate walks. The restatement converts 51 months into an afternoon of compute — which is
the whole of what OD-HISTORICAL-FIRST asked for.

**The veto blocks only and can never accumulate toward a promotion.** That asymmetry *is* §1 of
the directive. The named contradictions to watch are in the artifact; the sharpest is **B1452**
— an open `mx_*` position requests 7,744 M15 bars per tick, and if the terminal returns fewer
than 7,680 closed M15 bars the time stop never fires **at all** (inert, not late; the wall-clock
fallback does not catch it). This sleeve is the first of its cohort ever armed.

**The six stop rules are carried across UNCHANGED.** They are the veto, they are
`RISK_BOUND_not_inference`, and they are supposed to be fast. Restating them would loosen the
only thing that can block, which is the opposite of what the directive says.

---

## 3. The false-promotion arithmetic, as honestly as CA stated its own

**CA's number: 0.097**, measured by bootstrap over the sleeve's own centred archive R
distribution — P(a zero-mean sleeve reaches +34 R within 60 fills). Cost: ~51 months.

**This rule's number: 0.13 to 0.35, and the upper end is the honest one.**

- **M3 contributes nothing.** It is deterministic; P = 1 under every hypothesis. It is in the
  rule because the admission **REJECTS at all four bands under the pre-repair contract**
  (p 0.0564), so promoting on a silently-regressed repair would be promoting a number that no
  longer describes anything.
- **M4 ≈ 0.5.** Exactly 0.5 for a symmetric centred distribution; slightly below for the
  right-skewed R distribution these sleeves actually have — so 0.5 is the conservative
  statement.
- **M1 is treated as ≈ 1.0 and credited with nothing.** Conditional on the FTMO admission being
  luck, the redacted_account archive captures the same market and is **likely to reproduce that
  luck**. It is declared a ROBUSTNESS milestone, not an independence test. A milestone that
  mostly cannot fail must not be allowed to look like evidence.
- **M2 ≈ 0.25–0.7.** Under independence, "all three positive" alone is 0.125 and the admission
  clause tightens it further. Crypto correlation between `mx_ethusd` and `mx_avausd` inflates
  it; **`mx_nzdjpy` being an FX cross deflates it** — a mechanism that replicates outside crypto
  is not a crypto artifact. AF's measured crypto-cluster dispersion ratio of **4.74**
  (best-to-worst 1.80 R/trade) is direct evidence these symbols do not share an edge by
  default, which is what makes replication informative rather than automatic.

**Bound: 0.5 × [0.25…0.7] × 1.0 = 0.13 … 0.35.**

**Stated as a trade, not as an improvement.** P1-HIST is **weaker per decision** than CA's rule
(0.13–0.35 against 0.097) and **available now** rather than in 51 months. That is exactly the
trade OD-HISTORICAL-FIRST asks for and calling it anything else would be dishonest. It is not a
free lunch.

**The tightening that closes the gap, and it is recommended.** Require M2 to ADMIT at ≥ 2 of 3
bands on **all three** members rather than one. P(M2 | no edge) then falls to ~0.10 even under
a generous correlation allowance, giving **P(false promotion) ≈ 0.05** — better than CA's 0.097
*and* still available this week. The cost is that it may not be reachable: `mx_avausd` has 189
trades and could fall below the option's sample floors. **If it returns NOT_EVALUABLE the
milestone must be declared UNREACHABLE and the looser form used with its 0.13–0.35 number
attached** — not quietly dropped to the looser form while quoting the tighter number.

**Three things not claimed.** That the milestones are independent (they are not, and the bound
says so in the direction that makes the rule look worse). That reaching P1-HIST establishes the
edge — significance is already established at the sealed α (p 0.0011); what promotion needed
was never *more* significance, it was evidence that the admission is not an artifact of one
venue, one instrument, or one repair. And that the 0.13–0.35 is a measurement: the honest
instrument is a bootstrap that re-runs M1 and M2 under a null centring each member's own
archive R distribution while preserving the cross-member correlation. **That is filed, not
done** — the analytic bound is published with its assumptions named rather than dressed as a
measurement.

---

## 4. The multiplicity bill, declared before any of it runs

**4 looks**: M1 = 1, M2 = 3, M3 = 0, M4 = 0. Billed through
`training_lane.graduation.graduate()`, one look each, with the provenance chain attached.

Declaring the whole ladder up front is what stops it becoming *"re-run the gate whenever data
accrues"* — an unbounded number of looks nobody counts. The estate has been bitten by exactly
that shape twice: AO's undeclared median cut, and the nine-version-stale `DECLARATION_CHAIN`
whose default resolved a **51 % under-bill** in the permissive direction (B2204).

---

## 5. The template, and the agreement language

**Proposed for `WAVE_11_WORKING_AGREEMENT.md` §6, under Incubation:**

> **Promotion rules are historical-primary (OD-HISTORICAL-FIRST §1).** A promotion rule must
> pass three tests before an incubant is armed:
>
> 1. **Can it fire without waiting for the live stream?** If no, it is mis-derived and gets
>    restated before arming. A rule whose binding clock is a live fill count measured in months
>    is the named failure.
> 2. **Is every milestone reachable with data that exists?** A milestone needing a capture is
>    legitimate only if the capture is priced and scheduled (§2: *missing data is an action
>    item, never a verdict*). A milestone needing data nobody can get is a 51-month rule with
>    better prose.
> 3. **Is the false-promotion probability stated?** CA stated its own; that is the standard. A
>    promotion rule without one is a threshold somebody liked. When it is an analytic bound
>    rather than a bootstrap, say so and name the assumptions.
>
> The **live stream is a veto**: it blocks a promotion and it can stop a sleeve, and it never
> accumulates toward one. **Stop rules are unchanged by any restatement** — they are the veto,
> they are `RISK_BOUND_not_inference`, and they stay fast.
>
> The **look budget for the whole promotion ladder is declared before any of it runs** and
> billed through `graduate()`. "Re-gate as the archive grows" is an undeclared
> group-sequential design and is refused.
>
> Rules are amended through `IncubationRegistry.amend_rules()`, never by editing a sealed
> dossier. An amendment requires an owner ceremony, a stated reason, the superseded rule ids,
> **both directions together**, and the **live record at the moment of amendment** — the field
> that tells the next reader whether the rule could have been fitted to the stream. Amendments
> at zero live fills are marked `amended_on_a_virgin_record`; ones after fills are not refused,
> only made impossible to miss.

---

## 6. What was built

| artifact | what |
|---|---|
| `phase15/receipts/CE_MX_PROMOTION_AMENDMENT_V1.json` | the amendment, beside CA's untouched dossier |
| `phase15/receipts/ce_promotion_amendment.py` | the driver; writes the artifact and the registry row |
| `src/research_infra/training_lane/incubation.py` → `amend_rules()` | the re-registration path, CC's shapes |
| `tests/research_infra/test_ce_rule_amendment.py` | 17 tests, mostly about the price the path charges |
| `phase14/receipts/TRAINING_LANE_INCUBATION_REGISTRY.jsonl` | + one `incubation_rule_amendment` row (`ARMED->ARMED`) |

`amend_rules()` is deliberately a **hole in the wall that pre-registration is**, so it is made
expensive and visible rather than closed: both directions together, an owner ceremony, a stated
reason, named `supersedes` ids, a required `live_record`, and a refusal once the lane is over
(a promoted or stopped incubant's thresholds **are** the record of why it moved). The registry
stays append-only, so the original rule remains readable in the file forever — which is the
point of amending rather than editing.

---

## 7. Handoff

1. **M1 and M2 are runnable now and nothing blocks them.** One session of gate walks, four
   declared looks, and `mx_btcusd`'s promotion question is answered instead of scheduled.
2. **Take the tightening if `mx_avausd` is evaluable.** Decide that by running it, and if it is
   NOT_EVALUABLE record the milestone as UNREACHABLE rather than silently using the looser form.
3. **The exact bootstrap is filed.** The 0.13–0.35 is a bound with named assumptions; the
   measurement that would replace it is a null preserving cross-member correlation.
4. **The template applies to every future incubant**, including CA's revival candidates and
   anything the training lane graduates. The three tests in §5 are the whole of it.
