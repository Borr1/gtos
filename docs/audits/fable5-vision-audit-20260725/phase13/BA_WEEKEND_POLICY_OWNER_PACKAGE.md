# Owner package — the redacted_account weekend-holding solution

Session BA, blocks B1900–B1913 (allocation B1900–B1949). Receipts: `phase13/receipts/BA_WEEKEND_V1.json`,
`phase13/receipts/BA_EARLY_CLOSE_DATES_V1.txt`, `phase13/receipts/ba_weekend.py`.
Nothing is armed. Everything below is default-off and needs no config byte.

---

## 0. The one-paragraph version

redacted_account permits weekend holding in the **Challenge** and prohibits it on the **funded**
account. redacted_account is armed on a challenge today, so this blocker fires the moment that
account passes. The mechanism is built, tested and default-off: `run_book.py --weekend-flat
<sleeves>`. **Its measured price on the armed four is −0.7753 R/day, 42.8 % of their
+1.8098 R/day, and it costs the redacted_account funded book 10.6 pp of `p_pass` and 40 % more
calendar time to a payout.** 66 % of that bill is one sleeve (`sub_xvol_pullback`) and
28 % is another (`crypto`) — and **that 28 % is recoverable by one question to redacted_account**,
because BTCUSD quotes through 56 % of weekends and it is not established that the rule reaches an
instrument whose market never closes. **The decision you are being asked for is not whether to
comply. It is which reading of the rule to comply with, and whether to spend one support ticket
finding out which one is real.**

---

## 1. The rule, and how well it is sourced

`research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json` →
`firms.redacted_account.rules.weekend_holding`:

> "allowed in Challenge, PROHIBITED on the funded account. Requires a post-pass config change
> that does not exist."

Its own `absent` list states the same gap from the other side: *"Any weekend-flatten policy
for redacted_account's funded phase"* exists in no artifact. **FTMO carries no weekend rule at
all** — `firms.FTMO.rules` has no `weekend_holding` key, and FTMO's rules come from its own
byte-captured page. So this policy is per account, and arming it on FTMO would pay the whole
bill above for no rule.

**Provenance, stated plainly.** `coverage: MEASURED`, but `provenance_kind:
secondary_audit` — `.context/05_operations/redacted_account_terms_audit_2026-04-20.md:38`, which
grades itself HIGH and quotes redacted_account's own marketing page for the *challenge* half
("Hold your trades as long as you want, even on weekends") while the *funded* half rests on
two help-centre articles (11982358, 11641232) that are **not byte-captured in this
repository**. That is enough to build against. It is not enough to arm on. **Precondition
OD-BA-0: capture those two pages, or get the answer in writing from support.**

---

## 2. What the archive says before any policy exists

Measured over the four armed sleeves' 869 archive trades (`census` in the receipt):

| sleeve | n | crosses a weekend, **market-close** reading | crosses, **calendar** reading |
|---|---:|---:|---:|
| `sub_xvol_pullback` | 88 | **62.5 %** | 62.5 % |
| `energy_agri` | 67 | 41.8 % | 41.8 % |
| `sub_mid_dn_revert` | 533 | 29.5 % | 30.0 % |
| `crypto` | 181 | 15.5 % | **45.9 %** |

Two facts behind that table, both measured and both load-bearing:

- **The weekly close is broker-local Saturday 00:00.** On every one of the 18 non-crypto
  symbols these sleeves trade, 99.65–99.93 % of calendar weeks contain exactly one weekend
  gap, and the last H4 bar before it opens at broker **Friday 20:00** — closing exactly at
  Saturday 00:00. **Both live servers agree on that instant on all 365 days of 2026**, so a
  policy measured on the FTMO bar archive is a policy about the redacted_account account. (This had
  to be checked: `broker_clock.py` exists because a +3 h assumption was wrong for three weeks
  of the sealed March window.)
- **`BTCUSD` and `DASHUSD` trade through most weekends.** BTCUSD gapped the weekend in
  **43.8 %** of its weeks and quoted straight through the other 56.2 %. So "the weekend" is a
  property of *(symbol, week)*, not of the calendar — which is the whole of the crypto
  question in §4.

**Do NOT read the census's own R comparison as the cost.** Crossing trades average +1.04 to
+1.90 R gross against +0.21 to +0.48 for non-crossing ones on three of the four sleeves, and
that is almost entirely survivorship: a trade still open on Friday night is a trade that did
not stop out on Tuesday. Crossing is an *outcome*, not a treatment. The cost of the policy is
the counterfactual replay in §3 and nothing else.

---

## 3. The number per option

Every row is the armed four, gated at the **ratified rule** — `RECORDED` population,
`CANDIDATE_BOOK_V1` at the V9 declaration (53), `B_balanced` α 0.10 — with the band column
published and chronological folds in the receipt. R/day is the **sum** of the four sleeves'
`pooled_oos_mean_r` — an additive convenience, not the book's own R/day: the four sleeves trade
on different days and this sum applies no confidence weights. The book columns are the real
thing: the confidence-weighted four-sleeve book at Q's MC under **redacted_account's measured 2-step
rules**, on the gate's own OOS days, with the risk dial held at 2.0 % across every arm (so the
comparison is an exit change and not a sizing change — AR's standard that compounded book return
is not a valid instrument for a *sizing* decision is respected by holding size fixed, and the
risk-free R/day column is the headline regardless).

| # | option | R/day | vs base | FN `p_pass` (2 phases) | %/month | median days to pass |
|---|---|---:|---:|---:|---:|---:|
| 0 | **do nothing** — *not legal once funded* | +1.8098 | — | 0.7345 | 0.408 | 494 |
| a | **Friday flatten, calendar reading** ← the mechanism as built | **+1.0345** | **−0.7753 (−42.8 %)** | **0.6282 (−10.6 pp)** | 0.229 | 689 (+40 %) |
| a′ | Friday flatten, **`crypto` exempt** (market-close reading) | +1.2542 | −0.5555 (−30.7 %) | **0.7447 (+1.0 pp)** | 0.344 | 611 (+24 %) |
| b | (a) **+ 48 h entry embargo** | +1.3950 | −0.4147 (−22.9 %) | 0.7363 (+0.2 pp) | 0.236 | **832 (+68 %)** |
| b′ | (a) + 24 h entry embargo | +0.8844 | −0.9254 (−51.1 %) | not run | | |
| c | **per-sleeve hybrid** — best legal cell each | +1.6771 | −0.1327 (−7.3 %) | not run | | |
| d | flatten at **Friday 00:00** (holiday-robust, no list to maintain) | +0.9178 | −0.8920 (−49.3 %) | not run | | |

**Why a cost can raise `p_pass`.** Row (a′) gives up 30.7 % of the daily mean and comes out one
point *above* doing nothing, because the flatten is also a **risk reduction**: on the same days
it cuts the book's daily standard deviation from 0.9620 to 0.8722 (**−9.3 %**), and on the
wider `RECORDED` branch it removes the single worst book day outright (−1.7799 → −1.4755). A
prop challenge is a survival problem as much as a return problem, so a change that trades some
mean for less variance can move `p_pass` the other way from `%/month`. That is why both columns
are here and why **the %/month and days columns are the payout read** — they fall in every row.

`p_pass` MC standard error is ±0.0022–0.0024, so the (a) drop and the (a′) rise are both
real, not noise. **The %/month and days-to-pass columns are the ones to read for a payout
decision**; `p_pass` is a probability of *ever* clearing within the timeout and is blind to
speed, which is exactly how option (b) can look free and be the slowest row in the table.

### Where the bill is

| sleeve | share of the calendar bill | its own R/day, before → after |
|---|---:|---|
| `sub_xvol_pullback` | **66.3 %** | +1.0215 → +0.5076 |
| `crypto` | **28.3 %** | +0.2611 → +0.0419 |
| `energy_agri` | 3.1 % | +0.4065 → +0.3823 |
| `sub_mid_dn_revert` | 2.3 % | +0.1206 → +0.1026 |

**Flattening beats dropping for every sleeve at three of the four cost bands** — including
`sub_xvol_pullback`, which loses half its edge and still earns +0.5076 R/day, so it should not
be given up.

**The one exception, and it is the sleeve OD-BA-1 is about.** At the **high** spread band
`crypto` turns marginally negative under the calendar flatten: +0.1810 → **−0.0382**. So under
the conservative reading *and* a high-spread regime, `crypto`'s membership of the funded book is
a real question rather than a rhetorical one. Under the market-close reading it is **+0.1815 even
at the high band**. Post-flatten levels, all four bands:

| sleeve | flat 37-day | low | mid | high |
|---|---:|---:|---:|---:|
| `crypto` | +0.0737 | +0.0470 | +0.0419 | **−0.0382** |
| `energy_agri` | +0.3453 | +0.3949 | +0.3823 | +0.3611 |
| `sub_xvol_pullback` | +0.4897 | +0.5134 | +0.5076 | +0.4990 |
| `sub_mid_dn_revert` | +0.2128 | +0.1295 | +0.1026 | +0.0611 |
| **book sum** | +1.1214 | +1.0847 | +1.0345 | +0.8830 |

(The bill itself does not move with the band — §"What did NOT work" — but the *level* it leaves
behind does, and that is what a drop-or-keep decision reads.)

### What did NOT work, so you do not have to wonder

- **The entry embargo is not a repair.** On three of four sleeves it makes the flatten
  *worse*, and where it looks better (option b) it does so by halving the number of book
  days: same daily mean, 68 % more calendar time, a worse %/month. Default 0, recommend 0.
- **Zero margin is worse than one bar of margin on all four sleeves** (`m_inclusive` vs
  `m0`: −0.34 vs −0.22 on `crypto`, −0.59 vs −0.51 on `sub_xvol_pullback`). Holding the last
  four hours of the week costs more than it earns *and* is charged the weekend rollover. The
  default 4 h margin is the cheaper cell as well as the fillable one.
- **The cost band does not move the bill.** Option (a)'s delta is identical to eight decimal
  places at flat / low / mid / high, because the flatten changes gross R and swap and leaves
  the trade set (and therefore the spread charge) untouched. "Admits at N of 3 bands"
  phrasing does not apply to a cost delta, and this is why.

### The one caveat on option (c)

The per-sleeve hybrid is the **best of 17 legal cells per sleeve**, selected on the outcome.
It is published as an upper bound on what tuning could recover, not as a recommendation: at
that selection bill it would need its own out-of-sample confirmation before anything is armed
on it. Reporting it as *the* cost would repeat AO's undeclared-median-cut error with a
different variable.

---

## 4. The decision, and the cheapest thing that changes it

**OD-BA-1 — which reading of the rule applies to a 24/7 instrument?** Worth
**+0.2197 R/day** (28.3 % of the whole bill), **+11.7 pp of `p_pass`** and **78 fewer days
to a payout**. redacted_account's rule says "no weekend holding"; it does not say whether that
reaches BTCUSD, whose market does not close on 56.2 % of weekends. One support ticket
answers it. **Recommendation: ask, and default to the conservative reading until the answer
arrives** — `--weekend-flat` with no `--weekend-exempt`, which is option (a).

**OD-BA-2 — arm the policy on redacted_account only.** FTMO has no weekend rule. Arming it there
costs 42.8 % of the armed four for nothing.

**OD-BA-3 — the holiday list, or a wider margin.** See §5: without one of the two, the
policy has a compliance hole in ~2.6 % of weekend-crossing exits. The list costs nothing per
week and has to be maintained; the wider margin costs an extra **0.1167 R/day** every week
and maintains itself.

**OD-BA-0 (precondition, §1).** Capture the two redacted_account help-centre pages, or get the
funded-account weekend rule in writing. Everything above prices a rule this repository has
only at second hand.

---

## 5. The defect this session found in its own mechanism, and what it costs

The identity check — *every priced weekend-flat exit must land on the instant the live
switch would close at* — came back **7 mismatched out of 271** (2.6 %). All seven are
Christmas or New Year weeks, and the mechanism was the same every time: **when Friday is a
market holiday the week's last close is Friday 00:00 broker, and a Saturday-anchored deadline
aims 20 hours into a market that has already shut.** Under the redacted_account rule that is a
**breach, not a cost** — a position rides the weekend and every log reads healthy.

Two fixes, both built, and the choice is OD-BA-3:

1. **`--weekend-early-close <dates|file>`** — a list of non-trading days; a holiday at the end
   of a week pulls the whole deadline back a day. A 13-date list **derived from the archive**
   ships at `phase13/receipts/BA_EARLY_CLOSE_DATES_V1.txt` and closes the hole to **zero
   residual over all 271 exits**. Every date in it is a recognisable market holiday
   (Christmas Eve / Christmas / New Year / Good Friday), which is corroboration and not
   proof: bar absence cannot distinguish a market holiday from an archive coverage gap, and
   the derivation's own filters (a 52 h ceiling, a 60 % quorum over the symbols whose archive
   reaches that week) are what took 187 candidate dates down to 13. **The list is historical
   and contains no future date** — an operator arming the policy must extend it forward.
2. **`--weekend-flatten-before-hours 24`** — flat by Friday 00:00 broker every week. Needs no
   list, is robust to any Friday holiday by construction, and costs an extra **0.1167 R/day**
   across the armed four (option d).

**The durable fix is neither.** It is the broker's own trading-session table:
`broker_net_cost_engine.py:44-45` names `symbol_info_session_trade` /
`symbol_info_session_quote` as source authority it does not have, and `src/mt5/mt5_real.py`
exposes no sessions API. Filed in the repair queue.

---

## 6. The switch

```
python run_book.py --profile redacted_account --namespace redacted_account \
    --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert \
    --weekend-flat crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert \
    --weekend-early-close docs/audits/fable5-vision-audit-20260725/phase13/receipts/BA_EARLY_CLOSE_DATES_V1.txt
```

Defaults, and why each one is where it is:

| flag | default | effect of the default |
|---|---|---|
| `--weekend-flat` | empty | **the whole policy is off.** No sleeve is governed; both decision functions return False for every name at every instant; the code path is the committed one. |
| `--weekend-flatten-before-hours` | `4.0` | one H4 bar — the flatten instant is the close of the last H4 bar of the week, which is the instant the priced cell exits at. That mapping is what makes §3's number the number for *this* setting. |
| `--weekend-entry-embargo-hours` | `0.0` | no embargo beyond the flatten window itself. An entry inside the flatten window is always refused — it would be closed on the tick that opened it. |
| `--weekend-exempt` | empty | the conservative reading. Exempting `crypto` is OD-BA-1 and needs the firm's written answer. |
| `--weekend-early-close` | empty | **the measured 2.6 % exposure of §5**, not a safe default. The launcher logs a warning naming it every time the policy is armed without one. |

**None of these is a config key.** `config/agent_config.yaml` and
`config/profiles/redacted_account.yaml` are both hashed into a live activation token's config
digest, so a key in either would stop the armed book placing until the token was re-minted.
A test asserts no weekend key reaches any of the three profile files.

**It refuses to start rather than degrade.** If the policy is armed and either the MT5 server
name or `src/utils/broker_clock.py` cannot be resolved, `run_book.py` returns 5, notifies
CRITICAL, and does not run. That matters here more than anywhere else in the book:
`broker_clock.py` was **absent from the live host** as of the 2026-07-26 VPS export
(`packet_economics.py:41-49`), and a compliance guard that silently degrades to "no weekend
is due" is a funded account holding through one while every indicator reads normal. **Carry
`src/utils/broker_clock.py` to the host before arming this** — it is not optional plumbing
here, it is the policy's only clock.

**Flip it at a flat book.** The policy closes positions on a schedule; arming it mid-week
with positions open is safe (they are simply closed at the next deadline), but arming it
*inside* the flatten window closes everything governed on the first tick.

**Shutting the gate also shuts this policy — and that is H8 again, one layer up.** The weekend
flat runs inside `_manage_engine`, which returns early with
`live_broker_authority_false_observe_only` when `ultimate_book_live_broker_authority` is false
(CLAUDE.md H8). So setting the gate false does not just leave positions open and unmanaged; on a
funded redacted_account account it also **stops the compliance close from firing**, and the account
holds through the weekend. The operating rule is unchanged and now has one more reason:
**flatten first, confirm flat, then shut the gate.**

---

## 7. Handoff

| # | item | owner |
|---|---|---|
| OD-BA-0 | capture redacted_account help-centre 11982358 / 11641232, or get the funded weekend rule in writing | Borhen |
| OD-BA-1 | does the weekend rule reach a 24/7 instrument? worth 0.2197 R/day and 11.7 pp of `p_pass` | Borhen (one support ticket) |
| OD-BA-2 | arm on redacted_account only, when it passes | Borhen |
| OD-BA-3 | maintain the early-close list, or take the 24 h margin | Borhen |
| BA-H1 | carry `src/utils/broker_clock.py` to the VPS before arming — the policy refuses to start without it | orchestrator |
| BA-H2 | capture the broker trading-session table (`symbol_info_session_trade`); it retires OD-BA-3 permanently | a later session |
| BA-H3 | the four-sleeve book has **no published cache-population MC**; §3's levels are archive-population and comparable to each other, not to `phase8/receipts/BOOKS_MC_V1.json`'s 0.9331 | a later session |
