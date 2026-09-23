# LANE F — Live book ground truth: what the two funded accounts have actually earned

**Read date: 2026-08-11T09:24:57Z.** Source of record: **the brokers' own deal history**, read
read-only from both live MT5 terminals over host-admin (`initialize(path=…, portable=True)` →
`account_info` / `positions_get` / `history_deals_get` → `shutdown`; the same short-lived read-only
session pattern `.tools/monitor_books.py` already runs every 300 s on that host). No order, modify,
cancel, token, config, gate, tag or process was touched. Book-side attribution comes from
`shadow_logs/ultimate_book_launcher.jsonl` and `shadow_logs/broker_order_lifecycle_capture_v4.jsonl`
on the live host; every such claim is labelled.

Receipts: `swarm/lane_f_receipts/`.

---

## 0. The answer in one paragraph

**In 12.9 days of live armed operation across $200,000 of prop capital, the armed book has placed
exactly one trade.** It was `energy_agri` short UKOIL.cash on FTMO, 2026-08-04, and it made
**+$493.20 (+0.382 R)**. redacted_account has placed **nothing** — not because it saw nothing, but because
the one signal it did see was refused **462 times** by its own activation-token layer over two hours,
a namespace defect that was only repaired on 2026-08-10. Account balances today are **FTMO
$108,342.47** and **redacted_account $96,229.28**, both flat, no open positions. Neither figure is
mostly the armed book's doing: FTMO's +$8,342 is 94 % pre-arming, and $13,166 of it came from **two
manual 1.00-lot XAUUSD trades on 2026-07-02** that the book never placed. **The live record is not
powered to say anything.** A single trade's 95 % interval on the monthly rate is
**[−5.6, +7.8] pp/month** — it contains the +4.5 %/month in-window expectation, the +0.100 %/month
out-of-window expectation, and zero. It cannot separate them, and will not be able to for months.

---

## 1. Realized P&L per account since arming [MEASURED — broker deal history]

| | **FTMO** | **redacted_account** |
|---|---:|---:|
| account (redacted) | `redacted:310fcf063aa8` | `redacted:bee340036194` |
| server | FTMO-Server3 | redacted_account-Server 2 |
| armed | 2026-07-29 12:55 UTC | 2026-07-30 05:18 UTC |
| days armed at read | **12.85** | **12.17** |
| balance at arming | $107,872.28 | $96,229.28 |
| **balance now** | **$108,342.47** | **$96,229.28** |
| equity now | $108,342.47 | $96,229.28 |
| open positions | **0** | **0** |
| **realized since arming — armed book** (`magic 20260401`) | **+$493.20** | **$0.00** |
| realized since arming — all sources | +$470.19 | $0.00 |
| positions since arming — book / all | **1 / 2** | **0 / 0** |
| book P&L as % of balance at arming | **+0.457 %** | **0.000 %** |

**Combined: the armed book has earned +$493.20 on $200,000 of funded capital in ~12.5 days
(+0.247 % of combined capital).** That is the whole live record.

### The deal history is complete — verified, not assumed
Both accounts reconcile **exactly** to their $100,000 opening balance:

- FTMO: `Initial account balance` +100,000.00 (2026-06-01T10:23:31Z) + Σ(all trading deals)
  +8,342.47 = **108,342.47** = broker balance, to the cent.
- redacted_account: `Initial+Deposit` +100,000.00 (2026-04-26T20:06:53Z) + Σ(all trading deals)
  −3,770.72 = **96,229.28** = broker balance, to the cent.

There are no hidden or undownloaded deals on either account. 275 deals / 134 positions on FTMO,
362 deals / 169 positions on redacted_account, lifetime.

### Do not read the account balances as book performance
FTMO's +$8,342.47 lifetime is **94.1 % pre-arming** (+$7,872.28 before 2026-07-29 12:55). And the
pre-arming figure is itself dominated by two positions the book never placed: **two manual
1.00-lot XAUUSD longs on 2026-07-02 (magic 0, empty comment) worth +$6,085.34 and +$7,081.35 —
+$13,166.69 combined.** Strip those and the pre-arming live W7 book was **losing** money. Symmetrically,
redacted_account's −$3,770.72 was all incurred before it was armed. **Arming did not cause either number.**

---

## 2. Trade-by-trade record since arming

### FTMO — 2 positions, of which 1 is the book

| # | open (UTC) | close (UTC) | symbol | dir | vol | gross | comm | swap | **net** | magic | sleeve | exit |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| 1 | 2026-08-04 13:00:28 | 2026-08-05 04:56:43 | UKOIL.cash | SELL | 1.91 | +513.03 | 0.00 | −19.83 | **+493.20** | 20260401 | **`energy_agri`** | `[sl 80.511]` |
| 2 | 2026-08-10 01:06:38 | 2026-08-10 05:47:51 | XAUUSD | SELL | 0.01 | −22.95 | −0.06 | 0.00 | −23.01 | **0** | — (not the book) | `[sl 4345.10]` |

**Trade 1 — the only armed-book trade in existence.** From the book's own placement record
[MEASURED, `ultimate_book_launcher.jsonl` 2026-08-04T13:00:13.970243Z]:

- candidate `W7_BOOK::energy::UKOIL_cash::2026-08-04::SHORT::energy_agri`, decision bar
  2026-08-04T09:00:00Z, decision time 13:00:25.812Z
- `risk_pct_override: 1.1968` → **risk $1,291.02** on the balance at arming
- decision entry 83.208, **broker fill 83.233** (0.025 favourable for a short), SL 89.98367,
  TP1 56.105, final target 4.0 R
- exit policy `emv4_partial_be_runner_v1` (`partial_be_runner`), BE trigger 2.0 R, partial 0.5,
  `time_stop_bars: 1280` (= 80 × 16, the H4 contract — AQ's repaired unit, correct here)
- broker `retcode 10009 "Request executed"`, order ticket 172916305, entry deal 162262885,
  `RECONCILED_FROM_ACCOUNT_HISTORY`
- **R multiple = 493.20 / 1,291.02 = +0.382 R.** It exited on a stop trailed to 80.511 — locked-in
  profit, well short of the 2.0 R BE trigger and the 4.0 R target. Commission was **$0.00** and swap
  **−$19.83** for one overnight hold, so carry was 4.0 % of the gross.

**Trade 2 is not the armed book and did not pass through GTOS at all.** `magic 0`, empty comment,
no placement record in `ultimate_book_launcher.jsonl`, and — decisively — **no entry in
`activation_audit.jsonl` at that timestamp** [MEASURED]. Every exposure-increasing request that
crosses `RealMT5.order_send` is audited; the only 2026-08-10 audit rows are the deliberate
token drills at 13:23 and 13:28, hours after this trade closed. It was therefore placed **outside
the GTOS process**, i.e. by hand at the terminal. The same is true of the 0.01-lot XAUUSD on
2026-07-29 00:47 (−$7.28). They are the owner's, not the system's, and are excluded from all book
figures above.

### redacted_account — zero positions since arming

The last redacted_account position of any kind opened **2026-07-02T00:15:04Z**, 28 days before arming.
Nothing since. See §3 for why.

### Sleeves that were armed and then pulled — what they did while armed
`metals_core` was in the FTMO set from 12:55 to 14:25 on 2026-07-29 (90 minutes) and `fx_jpy` from
2026-07-30 ~11:52 to ~14:57 (~3 hours). **Neither generated a candidate, an intent or a fill in its
armed window** [MEASURED — no `magic 20260401` position exists on either account between arming and
2026-08-04, and the launcher records `no_candidates_this_bar` throughout]. `mx_btcusd_d1_donchian_20_breakout`
was live on FTMO via `--frontier-exits` from 2026-07-31 to its removal on 2026-08-05 and likewise
**never traded** — it appears in 7 launcher cycles, all with zero candidates. The armed set is now
**four sleeves on both accounts** — `crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert` with
`--spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback` and **no** `--frontier-exits`
[VERIFIED 2026-08-11 by reading both `run_book.py` command lines on the host].

---

## 3. Why redacted_account traded nothing — three causes, one of them now fixed

Both books are alive and evaluating. Neither is halted, killed or gated off: at the last cycle
(2026-08-11T09:00Z) both report `place: true`, `killed: false`, `halted: false`,
`live_broker_authority: true`, `include_clean3: true`, `apply_to_execution: true`, and the monitor
daemon reports `alert_count: 0`, `monitoring_degraded: false`, nothing down, nothing hung, and **no
`*.flag` kill file present**.

**Cause 1 — the activation-token namespace mismatch. This is the expensive one.**
On 2026-08-04 the redacted_account book generated the same `energy_agri` oil signal FTMO took, sized it,
and tried to place it **once per ~60 s tick from 13:00:32Z to 14:59:07Z — 231 launcher-recorded
rejections across USOIL_cash (116) and UKOIL_cash (115), 462 `order_send` attempts in the lifecycle
capture** [MEASURED]. Every one returned **no result object at all**
(`result: {present: false, success: false, missing_fields: ["order_result"]}`), which surfaces as
`order_rejected:timeout_no_fill` — a message that points at broker connectivity. It was not
connectivity. Session LM diagnosed it on 2026-08-05: the token was minted with
`"namespace": "redacted_account"` while the book runs `--namespace redacted_account_live_bee34003`, so
`activation_token_namespace_mismatch` refused every exposure-increasing request
(`HEALTH_SWEEP.md`, and the refusal is logged verbatim in `run_book_fn_console.log.err` at
14:58:06). The same signal on FTMO returned `retcode 10009` and made +$493.20.

**It is now repaired.** Both tokens were re-minted **2026-08-10 ~13:02Z** with correct namespaces
(`redacted_account_live_bee34003`, `operator_profile`), valid to **2026-09-09**, and the audit log
records a positive drill (`allowed: true`, `activation_token_valid`) plus deliberate negative
controls at 13:23 and 13:28 [VERIFIED 2026-08-11 by direct read of the token directory and audit
trail; only `namespace`/`expires` were read, no key material]. **So redacted_account was structurally
incapable of opening a position for 11 of its 12 armed days, and has been capable for one.**

**Cause 2 — 31 % of redacted_account's armed universe is unreachable, and still is** [MEASURED, current].
The book's own `broker_profile_generation` reports, on every FN cycle:

| | FTMO | redacted_account |
|---|---:|---:|
| active symbol slots | 42 | 42 |
| profile-supported | **42** | **29** |
| broker-unsupported | **0** | **13** |

The 7 unique missing symbols are `XAUEUR, XAGEUR, XAUAUD, XAGAUD, CORN_c, COTTON_c, DASHUSD`,
skipped `profile_missing_instrument_config` — 2,230 skip events since arming, hitting
`sub_xvol_pullback`, `sub_mid_dn_revert` and `crypto`. redacted_account is therefore running a
**materially different book from FTMO**, and every redacted_account economic figure published against the
42-slot universe overstates what that account can actually reach. This is open.

**Cause 3 — the book genuinely saw almost nothing.** Since arming, **exactly one decision bar on
each account produced a candidate**: 2026-08-04T09:00:00Z, `energy_agri`, UKOIL_cash + USOIL_cash.
Every other cycle is `no_candidates_this_bar` with `n_candidates_in: 0`. FTMO ran 103 cycles over
14 calendar days; redacted_account 183 over 11. Cadence is ~6 cycles/day since `fx_jpy` was pulled took
decision timeframes to H4-only (`advanced_tf: [16388]`); it was ~96/day when M15 was in the set.

One further FTMO note: the USOIL leg of that same 2026-08-04 signal was **skipped as
`stale_late_entry_after_restart`** at 17:00Z, so FTMO took one of two available legs.

**The redacted_account governor was never the blocker.** It has run
`allow_new_entries: true, size_cap_multiplier: 0.622928, reason: derisking_into_maxdd_wall` on all
183 cycles — a 37.7 % size reduction driven by the account's pre-arming −3.77 %, not a veto. FTMO's
governor is `allow_new_entries: true, cap 1.0, reason: ok`.

---

## 4. Account state now, against each firm's measured rules

Firm rules per Session Q [FTMO target and drawdown **MEASURED** from FTMO's own captured page;
redacted_account's 8 % **TRANSFERRED**, and whether its max-DD is static or trailing remains
**unestablished** — the estate has flagged that one captured page inverts the FN-vs-FTMO
comparison].

| | **FTMO** | **redacted_account** |
|---|---:|---:|
| balance / equity | $108,342.47 | $96,229.28 |
| open positions | 0 | 0 |
| vs $100,000 start | **+8.34 %** | **−3.77 %** |
| phase-1 profit target | 10 % → **$110,000** | 8 % → **$108,000** |
| **distance to target** | **$1,657.53 (+1.53 % needed)** | **$11,770.72 (+12.23 % needed)** |
| max-DD floor (static $90,000) | $90,000 | $90,000 |
| **drawdown headroom** | **$18,342.47** | **$6,229.28** |
| daily loss limit (5 % of initial) | $5,000 | $5,000 |
| days armed | 12.85 | 12.17 |

FTMO is **1.53 % from its phase-1 target** — but essentially all of that progress predates arming
and $13,167 of it is two manual gold trades. redacted_account needs **+12.23 %** and has 34 % less
drawdown headroom than FTMO. At the armed book's realized rate of +$493 per 12.9 days, FTMO would
reach $110,000 in **~43 days** and redacted_account would reach $108,000 in **~10 months** — and both of
those extrapolations rest on a single trade, which is the point of §5.

---

## 5. Expectation vs reality

| basis | monthly | over FTMO's 12.85 armed days (0.4223 mo) |
|---|---:|---:|
| in-window expectation (armed three, OD-AI-3 p99) | **+4.501 %** | +1.90 % → **+$2,050** |
| out-of-window honest estimate (same four sleeves, 10 y) | **+0.100 %** | +0.042 % → **+$45** |
| **FTMO realized, armed book** | **+1.083 %** (rate) | **+0.457 % → +$493.20** |
| **redacted_account realized, armed book** | **0.000 %** | **$0.00** |

**Which is the live record closer to?** On FTMO, the realized +$493 sits between the two, about
**4× the out-of-window expectation and 24 % of the in-window one**. On redacted_account it is below both.
Pooled across the two funded accounts — which is the honest denominator, since both were armed and
both were expected to earn — the realized **+0.247 % of combined capital over ~12.5 days ≈
+0.60 %/month**, i.e. **~13 % of the in-window expectation and ~6× the out-of-window one.**

**None of these comparisons is statistically meaningful.** See §6. What *is* meaningful:

- **Trade frequency.** Expected ~7 book-days/month; observed **one signal day in 12.85 days
  (~2.4/month)** on each account. That shortfall is itself not significant — Poisson, λ = 2.96
  expected trades, observed 1, **P(X ≤ 1) = 0.206**. Long silences are normal, exactly as documented.
- **Execution reality diverged from the model in a way no replay can see.** The model assumes both
  accounts take the signal. In the one instance the book fired, **one account filled and the other
  was refused 462 times.** A 50 % execution failure rate across armed accounts on the only live
  signal is not in any published P(pass).
- **The one realized trade was +0.382 R against a 4.0 R target**, exited by a trailed stop before
  the 2.0 R BE trigger. n = 1; it means nothing on its own, but it is the only live datapoint the
  repaired exit contract has produced.

### A relevant measured comparator: the live book's own longer record
Joining every book placement to its broker fill gives **142 live, broker-true, `magic 20260401`
trades** across both accounts (2026-06-19 → 2026-07-02, the pre-arming W7 window, at ~0.11 %
risk/trade rather than today's 1.20 %):

**mean −0.068 R, SD 1.210 R, median −0.254 R, win rate 45.8 %, min −1.99 R, max +4.26 R.**

That is the live W7 book's realized expectancy over its longest continuous run, and it is
**negative**. It is not a verdict on the armed four — that set is a different, later composition,
and this window is the one wave 3 already established was thin — but it is the only multi-trade
live evidence that exists, it is broker-true, and it does not support the in-window expectation.
It is also the honest σ for §6.

---

## 6. Is the live record powered to say anything? **No — and here is the number.**

Using the **measured** live per-trade dispersion (SD **1.210 R**, n = 142 above) and the armed
book's **measured** risk fraction (1.1968 % of equity per trade), one trade has a standard deviation
of **1.448 pp of account equity**.

**FTMO's observed record: 1 trade, +0.457 % over 0.4223 months → +1.083 pp/month, 95 % CI
[−5.64, +7.80] pp/month.**

That interval **contains the +4.501 %/month in-window expectation, contains the +0.100 %/month
out-of-window expectation, and contains zero.** It also contains −5 %/month. The live record is
consistent with every hypothesis anyone has proposed, including ruin. **Two weeks of trading cannot
distinguish +4.5 %/month from 0 %/month — this lane's answer to that question is an unambiguous no.**

How long until it could:

| trade rate | σ per month | to separate 4.501 vs 0.100 %/mo | to separate 4.501 vs 0 | to separate 0.100 vs 0 |
|---|---:|---:|---:|---:|
| 7/month (published cadence) | 3.83 pp | **5.9 months** | 5.7 months | 959 years |
| 2.37/month (observed cadence) | 2.23 pp | **2.0 months** | 1.9 months | 325 years |

(80 % power, α = 0.05, two-sided, one-sample against a point null.)

Read that table carefully. **The in-window claim is falsifiable in roughly 2–6 months of live
running** — that is genuinely useful, and it means the forward record will start to carry
information by roughly October 2026 *if the cadence holds and both accounts can actually execute*.
**The out-of-window claim is not falsifiable at all**: separating +0.100 %/month from zero needs
centuries. If the true edge is the out-of-window number, **the live book can never prove it, and
prop-account survival, not measurement, becomes the binding constraint.** That asymmetry is the
most decision-relevant thing in this document.

Two caveats on the power table, both making it optimistic: it assumes independent trades at constant
risk, and it assumes both accounts execute. Neither held in the one instance we have.

---

## 7. What this lane hands the other lanes

1. **The live book has produced one trade.** Any lane arguing from replay evidence should know the
   live record is n = 1 and cannot arbitrate between models. It is not a tiebreaker yet.
2. **+$493.20 is the entire realized output of the armed system.** Every other dollar in either
   account predates arming, and $13,167 of FTMO's is manual gold trades.
3. **redacted_account lost its only signal to a token-namespace defect and 31 % of its universe is still
   unreachable.** The first is fixed (2026-08-10); the second is open and means FN's published
   economics do not describe the account.
4. **The live W7 book's only multi-trade record is −0.068 R/trade over 142 broker-true trades.**
5. **The out-of-window hypothesis is unfalsifiable on live accounts.** Deciding between +4.5 %/month
   and +0.100 %/month by watching the books requires ~2–6 months at best and is impossible at worst.

---

## 8. Method, and what was not touched

**Read-only, verified:** the extraction script (`swarm/lane_f_receipts/lane_f_broker_truth.py`, run
on the host from `host-local\lane_f_20260811\`, outside the live tree, with
`PYTHONDONTWRITEBYTECODE=1`) calls only `initialize` / `terminal_info` / `account_info` /
`positions_get` / `symbol_info` / `history_deals_get` / `shutdown`. There is no `order_send`,
`order_check` or `order_calc` anywhere in it. No config byte, token, gate, tag, flag, process or
git state on the host was modified; nothing was checked out, cleaned or stashed. Account logins and
names appear nowhere in this document or its receipts — only `redacted:<sha256[:12]>`.

**Evidence classes.** Balances, equity, positions, deals, fills, commissions and swaps are
**[MEASURED]** from the broker. Sleeve attribution, risk fractions, candidate counts, skip reasons,
governor state and rejection counts are **[MEASURED]** from the live host's own logs. Firm rules
carry Session Q's classes (FTMO target/DD **MEASURED**; redacted_account 8 % **TRANSFERRED**; FN
static-vs-trailing max-DD **unestablished**). The 12.85-day arming interval uses the arming
timestamps recorded in `CLAUDE.md` §4; they agree with the first post-arming launcher cycles to
within seconds.

**Receipts** (`swarm/lane_f_receipts/`):

| file | contents |
|---|---|
| `LANE_F_RECEIPT_V1.json` | per-account ledger, firm distances, power analysis, the one book trade |
| `LANE_F_ACCOUNT_STATE_V1.json` | broker account + terminal state at read, redacted |
| `LANE_F_POSITIONS_ALL_V1.json` | all 303 lifetime positions, both accounts, broker-truth |
| `LANE_F_EMPIRICAL_R_V1.json` | the 142-trade live per-trade R distribution |
| `lane_f_broker_truth.py` | the read-only extractor, exactly as run |
