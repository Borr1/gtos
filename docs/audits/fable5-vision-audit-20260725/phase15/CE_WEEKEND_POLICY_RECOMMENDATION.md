# Weekend policy — the activation recommendation, so it stops sleeping undecided

Session CE (B2320–B2323). One page, as commissioned. Full evidence:
`phase13/BA_WEEKEND_POLICY_OWNER_PACKAGE.md` and `phase13/SESSION_BA_WEEKEND_SOLUTION_RESULT.md`;
mechanism `src/components/ultimate_book/weekend_policy.py` + `run_book.py --weekend-flat`,
default-off, 80 tests.

---

## The recommendation, in one line

**DO NOT ARM — on either account, today. Arm option (a′) on redacted_account at the moment it
passes, and buy the two answers that decide (a′)-versus-(a) NOW rather than after the pass.**

---

## 1. Why "do not arm" is not conservatism here

OD-HISTORICAL-FIRST §3 says a measured, controls-clean improvement to an armed sleeve sleeping
behind a default-off flag is a **defect state**. The spread-geometry floor is exactly that. **The
weekend policy is not, and the difference is worth being precise about**, because reading them
the same way would cost 42.8 % of the four-sleeve daily mean for nothing:

- The floor is an *improvement* whose trigger is a measurement, and the measurement is in. Not
  arming it is a defect.
- The weekend policy is a **contingent obligation** whose trigger is an **account state
  change**. It is a compliance guard for a rule that binds *"the moment that account PASSES and
  binds on FTMO never"*. It is correctly unarmed because its precondition has not occurred —
  not because anybody is waiting for more evidence.

Arming a compliance guard before the rule binds is not caution, it is paying the bill early.
The bill is measured (§2) and it is large.

**On FTMO it is never right.** FTMO carries no weekend rule at all — BA §1 checked and found
none. Arming there is pure cost with no obligation behind it. **OD-BA-2 should be recorded as
redacted_account-only, permanently.**

---

## 2. What it costs, and which option to pre-select

The armed four at the ratified rule (`RECORDED`, `CANDIDATE_BOOK_V1` V9 = 53, `B_balanced`
α 0.10), book columns at redacted_account's measured **two-step** rules with the dial held at 2.0 %:

| option | R/day | vs base | FN `p_pass` (2 phases) | %/month | median days to pass |
|---|---:|---:|---:|---:|---:|
| do nothing — **not legal once funded** | +1.8098 | — | 0.7345 | 0.408 | 494 |
| **(a)** Friday flatten, calendar reading | +1.0345 | −0.7753 (**−42.8 %**) | 0.6282 (−10.6 pp) | 0.229 | 689 (+40 %) |
| **(a′)** Friday flatten, **`crypto` exempt** | **+1.2542** | −0.5555 (−30.7 %) | **0.7447 (+1.0 pp)** | **0.344** | **611 (+24 %)** |
| (b) (a) + 48 h entry embargo | +1.3950 | −0.4147 | 0.7363 | 0.236 | **832 (+68 %)** |

**(a′) is the option to pre-select**, and the gap between it and (a) is one support ticket:
**+0.2197 R/day, +11.7 pp of `p_pass`, 78 fewer days to a payout** — 28.3 % of the entire bill,
decided by whether redacted_account's prohibition reaches an instrument whose market never closes.
BTCUSD gapped the weekend in only **43.8 %** of archive weeks and quoted straight through the
rest, so "the weekend" is a property of *(symbol, week)* rather than of the calendar.

Note the shape of (a′): it gives up 30.7 % of the daily mean and lands **one point above doing
nothing** on `p_pass`, because the flatten is also a risk reduction (book daily sd 0.9620 →
0.8722, −9.3 %). **Read the %/month and days-to-pass columns for a payout decision** — they
fall in every row, and `p_pass` is blind to speed, which is exactly how (b) reads free while
being the slowest row in the table.

Do not take (b). Its apparent improvement comes from **halving the number of book days**.

---

## 3. Buy these two answers now, not after the pass

| # | question | worth | who |
|---|---|---|---|
| **OD-BA-0** | capture redacted_account help-centre **11982358 / 11641232**, or get the funded-account weekend rule in writing | the whole policy prices a rule no artifact in this repo contains | Borhen |
| **OD-BA-1** | does that rule reach a 24/7 instrument (`crypto`)? | **+0.2197 R/day, +11.7 pp `p_pass`, −78 days** | Borhen, one ticket |

Both are answerable today and neither depends on the account passing. Answering them *after*
the pass means arming under the conservative reading and paying the extra 28.3 % for however
long the ticket takes. **This is the cheapest item in the whole activation package.**

---

## 4. BA-H1 is RETIRED — `broker_clock.py` is already on the host [MEASURED]

BA's handoff item 2 says *"carry `src/utils/broker_clock.py` to the VPS before this policy is
ever armed"*, and calls it *"a precondition of arming"*. **It has already been carried, twice,
and it is committed on the host branch.** BA was reading `packet_economics.py:41-49`, which
describes the **2026-07-26 VPS export** — and both carries landed after it:

| carry | position | destination | after-sha256 |
|---|---|---|---|
| Session S packet carry (`phase4/packet_carry`) | `copy_order: 1` | `src\utils\broker_clock.py` | `0f97bbb64bc55b02…` |
| Session AC activation carry (`phase5/activation_carry`) | `copy_order: 1` | same | same |

`phase8/receipts/VPS_CEREMONY_COMPLETED.md` records both applied (8 of 9 AC files at
after-hashes on 2026-07-29 12:37–12:39Z, the ninth completed 2026-07-30), `verify_carry.py
--check all` **PASS** over the composed set, and — line 49 — `src/utils/broker_clock.py`
explicitly committed at host `118071eaa` *"because a `git clean` would have deleted the module
`governor_state` imports."* The host's bytes are **byte-identical to mainline HEAD** (23,842 B,
`0f97bbb64bc55b0213e47a018c2e884d83b2059b61de7941a171fd3cf2fef552`).

So the launcher's fail-closed refusal (`run_book.py` returns 5 when the policy is armed and the
clock cannot be resolved) will **not** fire for a missing module. That is one less thing between
the pass and the guard.

**What is still NOT on the host, and would need carrying before arming:**
`src/components/ultimate_book/weekend_policy.py` (a new module) plus the anchored
`book_owner.py` / `run_book.py` edits. Build it the way
`phase15/activation_carry_spread_floor/` is built, and compose it **on top of** that carry —
they touch the same two files at adjacent anchors. Note also that the host's `book_owner.py` is
Session AZ's after-bytes and its `book_engine.py` is Session **AC's**, not the lineage's; that
correction is §0.1 of the spread-floor ceremony page and it applies here identically.

---

## 5. Two things that must be settled in the same ceremony

**OD-BA-3 — the holiday list, or the 24 h margin.** BA measured its own mechanism failing on
**7 of 271** priced weekend exits (2.6 %), all Christmas or New Year: when Friday is a market
holiday the week's last close is Friday 00:00 broker and a Saturday-anchored deadline aims 20
hours into a market that already shut. Under the funded rule that is a **breach, not a cost** —
a position rides the weekend and every log reads healthy. Two fixes exist and one must be
chosen: the derived 13-date list (`phase13/receipts/BA_EARLY_CLOSE_DATES_V1.txt`, residual 0
over all 271) or `--weekend-flatten-before-hours 24` (needs no list, costs an extra
0.1167 R/day). **The shipped list is historical and needs extending forward**; the durable fix
is BA-H2, capturing the broker's own `symbol_info_session_trade` table.

**H8, one layer up, and it is the sentence to remember.** The weekend flat runs inside
`_manage_engine`, which returns early with `live_broker_authority_false_observe_only` when
`ultimate_book_live_broker_authority` is false. So on a funded redacted_account account, shutting the
gate does not only leave positions open and unmanaged — **it also stops the compliance close
from firing, and the account holds through the weekend.** Flatten first, confirm flat, then
shut the gate.

---

## 6. The ceremony, when redacted_account passes

```
python run_book.py --profile redacted_account --namespace redacted_account \
    --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert \
    --weekend-flat crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert \
    --weekend-exempt crypto \
    --weekend-early-close docs/audits/fable5-vision-audit-20260725/phase13/receipts/BA_EARLY_CLOSE_DATES_V1.txt
```

`--weekend-exempt crypto` is option (a′) and is **conditional on OD-BA-1 coming back "the rule
does not reach a 24/7 instrument."** Without that answer, drop the line and take (a).

No config byte moves; neither token is disturbed. **Flip it at a flat book**, and never inside
the flatten window (it would close everything governed on the first tick). FTMO's worker is
untouched, now and permanently.

**Verify:** the launcher's startup line naming the flatten instant and the next weekend
boundary, plus `weekend_policy_preflight` returning `status: armed` with a resolved server. A
`governs_sleeves_this_worker_does_not_trade` list that is non-empty means the guard is governing
names the worker never trades — legal, and it reads exactly like one that works, so check it.

---

## 7. Owner decisions this page asks for

| # | ask | recommendation |
|---|---|---|
| OD-BA-2 | arm on redacted_account only, at the pass | **accept, and record FTMO as never** |
| OD-BA-0 | capture the two help-centre pages | **do it this week**, not at the pass |
| OD-BA-1 | does the rule reach a 24/7 instrument? | **one ticket, worth 28.3 % of the bill** |
| OD-BA-3 | holiday list or 24 h margin | **the list**, extended forward, until BA-H2 lands |
| — | arm anything today | **no** |
