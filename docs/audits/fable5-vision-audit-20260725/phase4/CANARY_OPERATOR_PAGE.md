# The canary: what to run, and what it means

For Borhen. You are the monitor — you accepted that explicitly, and nothing below
changes it. Every check here is a **message to you**. None of them stops trading,
changes size, or touches a gate.

> **Read this first — added 2026-07-29 at wave-4 integration (Session U, B359). The approved
> armed set is FOUR sleeves, and the example below runs three.**
>
> Borhen approved arming FTMO on its four survivors — `metals_core, crypto, energy_agri,
> **sub_xvol_pullback**`. This page was written when only three were reachable, and that part
> was correct: `sub_xvol_pullback` is a clean_3 sleeve, `ultimate_book_include_clean3` is
> `false` at `agent_config.yaml:1270`, and `book_engine.py:452-453` drops it before it can
> generate (T's B337). **The `--launch-tags` example below is therefore right for the config as
> committed and wrong for the approved book.**
>
> Arming four needs BOTH: `include_clean3: true` **on the live host's config**, and
> `--tags metals_core,crypto,energy_agri,sub_xvol_pullback` on the launch line. Making that flip
> in *this repository* instead breaks the R2 decision contract (`config/agent_config.yaml` is
> bound; H1). The flip moves the sizing registry 29 → 32 and total confidence weight 6.82 → 7.77,
> but the Kelly-lite conviction multiplier keys on sleeves *firing that day*, so `--tags` bounds
> it. The example is left at three deliberately: it matches what the committed config can
> actually run, and the sequencing is the orchestrator's ceremony, not this page's.
>
> One thing that does NOT transfer: the `P(pass)` figures behind the stop conditions are for the
> four-sleeve book. **No MC at 2.0 % exists for exactly these three** — Session V is measuring
> the armed set directly.

---

## One command

```bash
python3 scripts/canary_watch.py \
    --launch-tags metals_core,crypto,energy_agri \
    --armed-utc 2026-07-29T00:00:00Z \
    --account-state ~/canary_account_state.json \
    --fills shadow_logs/canary_fills.jsonl \
    --packets shadow_logs/ultimate_book_runtime_learning_packets.jsonl \
    --expect-namespace operator_profile
```

Everything after the first line is optional. With nothing at all it still answers
questions 1 and 5, which are the two that can go wrong while everything else looks
normal. Add `-o page.txt` to keep a copy.

**Where `--fills` comes from, because without it C1, C2 and C3 never evaluate —
and a check that never evaluates is the failure this whole page exists to
prevent.** There is no live feed. The file is built from a VPS export:

```bash
# 1. export the VPS's MT5 API state (read-only; the orchestrator's ceremony)
#    -> <export>/09_mt5_api/{ftmo,redacted_account}_history_{deals,orders}_get.jsonl
# 2. turn it into priced trade rows
python3 scripts/w7_live_forensics.py --export-root <export> --out-dir <dir>
#    -> <dir>/LIVE_TRADE_ROWS.jsonl          <- this is the --fills file
```

So the cost tripwires are only as fresh as the last export. Until one exists with
canary fills in it, the page will say `no fills yet — nothing to price` and exit
**3**, not 0. That is deliberate: it is telling you those three conditions are
**unchecked**, not that they are clear.

**Exit codes**, so you can put it behind anything: `0` clean · `1` an alert at
MEDIUM or above · `3` clean, but something could not be checked. Three rather than
two on purpose — "nothing is wrong" and "nothing was checked" are different, and
collapsing them is exactly how `.tools/monitor_books.py` sat mute through the
window it was meant to be watching.

Run it **when you look**, not on a timer. There is nothing here that degrades if
you check twice a day instead of every hour — the book is expected to trade about
seven days a month.

---

## Read this before the first run: the book is not three sleeves

**Measured 2026-07-29, and it is the reason question 5 is on the page.**

`config/agent_config.yaml` cannot express a three-sleeve book. Not "is not
currently set to" — *cannot*. All 16 combinations of the four include-flags were
enumerated and the smallest resolvable book is **core-8**, which contains
`idxrev`, `fx_jpy` and `fx_jpy_ny` — the three sleeves measured as dead.

The live chain is three steps, and it lands on **29**:

| step | count | where |
|---|---:|---|
| specs built | 32 | `sleeves/registry.py:active_specs` |
| dropped — not in the active book | −3 | `book_engine.py:452-453` (DF-1) |
| **can generate an order** | **29** | of which 12 are `mx_*` market-expansion sleeves |

Those 29 are exactly the sleeves that carry a sizing weight — after the engine
filter the two resolvers agree. Three sleeves (`sub_mid_dn_revert`,
`sub_xvol_pullback`, `vp_euidx_pocgrav`) are built but dropped before they can fire.

**The three-sleeve book is expressed by `run_book.py --tags`, and the committed
`scripts/run_book_supervisor.ps1:108-109` passes none.** So:

> **Before arming, confirm the live supervisor passes
> `--tags metals_core,crypto,energy_agri`.** If it does not, the book is 29
> sleeves — the three measured as dead, plus twelve market-expansion sleeves at
> confidence 0.025 — and it will look like normal trading.

This session could not check the VPS and does not claim to have. What it can say
is that nothing in this repository restricts the book to three, so the restriction
has to be in the launch command, and it is worth reading with your own eyes.

Then pass the same tags to `canary_watch.py --launch-tags`, and question 5 checks
that the two agree.

### And one thing about the three sleeves themselves

The armed book is **exactly the FTMO survivor book minus `sub_xvol_pullback`** —
and `sub_xvol_pullback` is one of the three sleeves the engine drops because
`include_clean3: false`. So the canary book is not a set someone picked on the
evidence; it is *the survivors the config can currently generate*.

That matters for one number you may be carrying: ~~the 2.0 % dial's `P(pass) 0.99675`~~
(FTMO, forward window, worst carry) was computed on the **four**-sleeve survivor
book. Dropping a low-correlation sleeve drops diversification, and P(pass) does not
transfer downward. **No Monte Carlo at 2.0 % exists for exactly these three.**
Separately, the active profile's own note says it is for use *"ONLY with
include_clean3=True"*, which the config does not satisfy.

> **Corrected 2026-07-29 at wave-4 integration. `0.99675` is the pre-Session-Q number.**
> It was computed at the *sealed* firm rules, which hardcoded redacted_account's trailing
> drawdown and 8 % target for both accounts. At each firm's **measured** rules the same
> cell is **`0.99918`** for phase 1 and **`0.99828`** across both phases
> (`MC_FIRM_TRUE_V1.json` → `accounts.FTMO.variants.SURVIVORS_ONLY.fwd_nights_max.rules`,
> `L4_FIRM_TRUE_PH1` / `P2_BOTH_PHASES`). **The two-phase figure is the one that gates a
> payout**, and phase 2 had never been modelled before Q. Both are still four-sleeve
> numbers, so the paragraph's point is unchanged — only the figure it is about.
>
> Also do not substitute the three-sleeve number that *does* exist:
> `SURVIVORS_BOTH_ACCOUNTS` (`p_pass` 0.99772 / 0.99577) is `crypto, energy_agri,
> sub_xvol_pullback` — the account-intersection book, a **different** three from the
> canary's.

None of that is a reason not to arm — it is your call and you have made it. It is a
reason not to read a four-sleeve `P(pass)` as the canary's number.

---

## The five answers

**1 — Is it armed?** The four authority gates, read from the config on disk right
now, plus whether a valid activation token exists for the account. `ABSENT` is
printed as `ABSENT`, never as `false`: `ultimate_book_live_broker_authority` is
absent from mainline and explicitly false in the VPS export, and rendering those
the same way would make a fresh clone look like the live host.

**2 — Did it trade?** Two separate questions that must never be merged. *Alive* is
the packet stream (a gap over 30 minutes is an alert; the live export's p99 idle is
15 minutes, so this will not cry wolf). *Quiet* is fills, and quiet is normal — the
three armed sleeves fired **zero** times across the entire 38-day live window and
that was consistent with their natural frequency. The page prints the calibrated
probability of the silence you are looking at, every time, so you know what normal
looks like before something is wrong.

**3 — What did it cost versus what we predicted?** Every fill priced against
`BROKER_TRUE_COSTS_V1.json` and compared to what the broker actually charged. The
baseline to beat is a mean absolute error of **0.000535 R** over 175 fills; the
model this replaced was wrong by **0.0591 R** because it charges zero commission.
The alert sits at 0.01 R — about 19× the baseline, above the worst single fill ever
measured, and far below the point where the re-cost has bought nothing. This is
measurable from the first handful of fills, which is why it is condition one.

Swap and holding time get their own tripwire. Commission turned out **not** to be
the contamination — it is 0.0000 R on the index sleeve — and swap is the largest
single broker cost for eight of eleven sleeves. Carry is what OD-3 now waits on.

**4 — How much drawdown headroom?** Distance to the static floor and to today's
daily allowance, on each firm's **own** reset calendar. FTMO resets at 00:00
CE(S)T; redacted_account at 00:00 server time; the MT5 server clock is
`America/New_York + 7 h` on the **US** DST calendar. Three different clocks, and
`src/utils/broker_clock.py` fails closed rather than guessing.

Balance and equity are **inputs** — this tool holds no broker connection and says
so on the page. Supply them in a small JSON:

```json
{"FTMO": {"balance": 107872, "equity": 107872, "day_start_equity": 107872,
          "static_dd_floor": 90000, "initial_capital": 100000,
          "daily_loss_basis": "initial_capital", "daily_reset_rule": "CE(S)T",
          "broker_server": "FTMO-Server3",
          "provenance": "[input] read off the terminal at 08:00 UTC"}}
```

**5 — Still exactly three sleeves?** Above.

---

## What each alert is telling you to do

| condition | if it fires |
|---|---|
| **C4** book composition | Stop and read the launch command. Nothing else on the page means anything if this is red. |
| **C5** gates / token | If it was not you, treat it as an incident. |
| **C1** cost deviation | The cost table is wrong, and the cost table is the activation case. Worth pausing new entries by hand while you look. |
| **C2** swap / holding | Carry is running longer than the live corpus did. Every carry-conditional sleeve moves toward break-even. |
| **C3** sleeve tripwire | A sleeve is losing *before* costs. That is what the two dead JPY sleeves looked like, and it took a fortnight to see. Not statistically conclusive at six fills, and not meant to be. |
| **C6** book silent | The process stopped emitting. Check the supervisor. |
| **C7** no fills past 42 days | Informational. Genuinely might be nothing. |
| **C8** headroom | The only one where the number matters more than the trend. |

Removing a sleeve, changing the dial, or shutting a gate are yours. The tool will
not do any of them, and it is not built so that it could.

---

## The drills

```bash
python3 scripts/token_chaos_drills.py --receipts-dir <dir>
```

Eight specified drills plus one added by this session. Six pass locally. Two —
D-7 and D-8 — **cannot** run without a demo MT5 terminal, because they ask what
the *broker* does, and a fake module can only replay whichever answer was encoded.

The one to know about: **D-8's dangerous branch is the only path inside the token
layer that can refuse a close.** If `MetaTrader5.positions_get` can return a stale
non-empty tuple that omits a live ticket, the gate reads that as authoritative
absence, the close classifies as new exposure, and with no token it is refused.
Everything else — a `None` return, an exception, a broken token directory, a
revoked token, a deleted signing key — lets the close through, verified end to end.

D-8 is cheap and needs only a demo account. It should be run before the funded
book carries a position through a terminal restart.

---

## Three ways a close could be refused ABOVE the token layer

The drills tested the activation layer. An adversarial pass found that the layer
above it is where the real risk was.

**1 — A float bug made ~11 % of position sizes un-closable. Fixed 2026-07-29.**
`_normalize_volume` truncated a binary quotient that is mathematically an exact
integer, so 0.03 lots normalized to 0.02 — and the close gate demands they match.
Nine close producers routed through it, the live book always takes that branch, and
no retry could ever succeed. **44 of 327 real broker close deals** in the VPS export
carried an affected volume. Fixed in `execution.py` with an exhaustive test; the
same fix means an entry asking for 0.03 now places 0.03 rather than 0.02, which is
a one-step size increase in those cases and is **worth your explicit blessing**.

**2 — Setting `live_broker_authority: false` strands open positions.**
`book_owner.py:2364-2373` returns before flattening anything, and `:2526`
skips routine exit management as observe-only. The natural "stop it now" reflex —
shutting the brake — leaves every open position with no exit management at all.
**Flatten first, then shut the gate**, not the other way round.
*(Line numbers repointed 2026-07-29 at wave-4 integration — Session S's change to
`book_owner.py` shifted them by 20, and the old `:2344-2353` now lands on an unrelated
function. What a gated position DOES keep is the broker-side SL/TP set at entry
(`execution.py:3488`), so it is not naked; what it loses is the time stop, scale-outs,
trail/BE moves, TP edits and — the part that ends an evaluation — the governor
breach-flatten.)*

**3 — A runtime halt refuses closes, and its risk-reducing carve-out uses the
lossy reader.** `execution.py:530` calls `self.mt5.get_positions(...)`, which masks
a failed broker read as `[]` and filters by magic — the exact defect the token
layer was repaired for in B101, still live one layer up. Under an active halt, a
close of an adopted or foreign-magic position, or one attempted during a transient
read failure, gets `runtime_halt_active_no_order_send`. Recorded, not fixed: it
only bites while a halt is active, and a halt is a deliberate operator act.

`scripts/flatten_all_positions.py` is ungated by design and is the manual escape
hatch from all three.
