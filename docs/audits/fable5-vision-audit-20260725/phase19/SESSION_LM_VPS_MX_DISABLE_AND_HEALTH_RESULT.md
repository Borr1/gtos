# Session LM — VPS: mx_btcusd disabled, the owner-intervened trade reconstructed, live flow assured — RESULT

**2026-08-05, ~13:33–14:52 UTC, over host-admin/host-mesh as `trader` on `redacted_host`.**
Commission: `phase19/SESSION_LM_VPS_MX_DISABLE_AND_HEALTH.md`. Branch
`ops/vps-live-mx-disable-20260805`. Receipts: `phase19/receipts/vps_live_ops_20260805/`.

**No token was minted, re-minted or revoked. No config byte moved. No broker-mutating call was
made** — every MT5 call was `positions_get` / `account_info` / `terminal_info` /
`history_deals_get` / `history_orders_get`. redacted_account was not touched in any way.

---

## 0. Headline

**The money is safe.** Both accounts flat, both books armed and healthy, no orphaned state, no
broker/book divergence. FTMO **$108,365.48**, redacted_account **$96,229.28**.

**`mx_btcusd` is disabled on FTMO** and committed on the host branch so no checkout can re-arm it.

**Yesterday's trade was closed by Borhen, not by the book** — he moved the stop from a device of his
own and it filled for **+$493.20 net**. The book's state is fully coherent with the broker
afterwards. But the learning lane has recorded that owner-chosen exit as ordinary sleeve
performance, and it has no field that could say otherwise.

---

## 1. A root-path correction that could have made the whole session a no-op

The commission's first draft said the live tree was `C:\GTOS`. It is not. **The live tree is
`C:\Users\MSI\Documents\ai-trading-agent`**, derived from the running process's own command line.
`C:\GTOS` exists but holds only `archives/ exports/ installers/ logs/ tools/` — no `run_book.py`, no
`scripts\run_book_supervisor.ps1`, no `pipeline_state\ultimate_book`, and it is **not a git
repository at all** (`git rev-parse` there fails). Session S's two-tree finding (B292) is exactly
this hazard. Editing the launcher in the wrong root would have been a **silent no-op** — the
supervisor would have relaunched from the real file with `mx` still armed, and every verification
short of reading the live process command line would have looked fine.

The orchestrator caught and corrected this independently at commit `69f948b63`. **Always derive the
root from the running process, never from a directory listing.**

---

## 2. (A) `mx_btcusd` disabled — done

Full receipt: `receipts/vps_live_ops_20260805/MX_DISABLE_RECEIPT.md`.

`scripts/run_book_supervisor.ps1` line 140, one substring, one occurrence: removed
`mx_btcusd_d1_donchian_20_breakout` from the FTMO `--tags` **and** removed the whole
`frontier="mx_btcusd_d1_donchian_20_breakout";` key. 19,575 B `63079cec…` → 19,495 B `ff9299bd…`,
**Δ −80 B exactly**, zero occurrences of the sleeve name remaining. redacted_account row byte-identical.

Gated before touching anything: PowerShell **parse check** (0 errors) and the `$books` literal
**evaluated in isolation** to prove the resulting argv — because the two `--tags` traps are decided
by the argv, not the source text (`--tags ""` is falsy and fails **open** to all BUILT sleeves; an
all-typo list stands the book down **silently**). Result: 4 tags, non-empty, no `--frontier-exits`.

Then a **single guarded script** did the flat-check and the kill atomically: both accounts 0
positions, and `firing_sleeves.json` held only a `2026-08-04` key — **so the B365 +25 % conviction
hazard did not apply today** and the file was left untouched rather than deleted-for-show.

The restart had to include the supervisor: it reads `$books` **once at startup** and then loops
forever, so the incumbent (pid 2972, up 51 h) held the old five-tag array in memory and would have
relaunched `mx`. Killed FTMO workers + supervisor at 14:30:41; the 5-minute scheduled task took over
at 14:33:01 and relaunched from the edited file at 14:33:17. **FTMO downtime 2 m 36 s**, flat, ~2.5 h
before the next decision boundary. redacted_account ran untouched throughout.

Verified after: live argv on both new pids carries 4 tags and no frontier flag; the book's own
startup reads **`authority_gates_ON=True halted=False killed=False`** with
**`config_digest=ffe16657feaf` unchanged** (proof no token-bound byte moved); spread-geometry floor
still ON for both sleeves; first post-restart launcher cycle at 14:33:37Z lists exactly the four
sleeves; kill flags absent; heartbeats fresh.

**One independent confirmation worth naming:** the launcher now reports **`tfs=[16388]`** — H4 only.
`mx_btcusd` is a **D1** sleeve, and the D1 timeframe left with it. That proves the *resolver* dropped
the sleeve, not merely that the argument string changed.

Host commit **`2fa77722d`**.

**What Borhen will see tonight:** the ~21:00 UTC cycle will list **four** sleeves instead of five.
The daily cycle count stays at **6**. That is the change, not a fault.

---

## 3. (B) The trade, and what Borhen actually did

Full receipt: `receipts/vps_live_ops_20260805/TRADE_FORENSIC_20260804_UKOIL.md`.

**What fired.** FTMO `energy_agri`, **SHORT 1.91 lots UKOIL.cash @ 83.233**, decision bar
2026-08-04T09:00Z, filled 13:00:28Z, position `172916305`, `reason=EXPERT` (book-placed),
**SL 89.984 / TP 56.230 both server-side at entry**. Sized at 1.20 % risk = $1,289.44 — and the stop
distance × lots × contract value reproduces that to the dollar, so the position was sized exactly as
declared.

**What the book intended.** `partial_be_runner`: broker TP at **4 R**, and a **software trigger at
2.00 R** for the scale-out and break-even move.

**What happened.** Closed 2026-08-05T04:56:43Z at 80.547 on **`reason = DEAL_REASON_SL`**, comment
`[sl 80.511]`. **+513.03 gross, −19.83 swap, 0.00 commission → +493.20 net.** Realised **0.398 R**;
peak floating was 0.504 R.

**Who moved the stop — measured two independent ways:**

1. **The VPS terminal never sent a modify.** MT5 journals every request sent through a terminal.
   `20260804.log` has exactly five `Trades` lines, all five the entry; `20260805.log` has exactly one,
   the closing deal notification. Across **ten days** of FTMO journals there is no `modify` line at
   all. The book acts only through this terminal.
2. **An external device was logged into the FTMO account — and only FTMO.** The VPS's own public IP is
   `0.0.0.0`: it is the *sole* IP in the redacted_account journal every day for four weeks, and that
   terminal is never touched by hand. From **2026-08-02 onward the FTMO journal shows only
   `0.0.0.0`** — including an authorization at 2026-08-04 19:29:55 UTC, during the life of this
   position. Two terminals on one host cannot have two public IPs.

**So: Borhen moved the stop from 89.984 to 80.511 himself, from his own device, locking ≈$520 gross.
The stop then filled. The book neither placed nor requested that exit** — which matches his account
exactly.

**Is the book's state coherent? Yes, completely.** 0 positions both accounts; equity = balance;
107,872.28 + 493.20 = 108,365.48 ✔; `edge_state.json` recorded the win and the deal ticket;
`daily_pnl.json` reconciled from account history 43 s after the fill; **no orphaned managed state**.
Nothing needed repairing.

**And one guard deserves credit.** At 21:01:32 on 08-04 the terminal lost its broker link and
`positions_get` returned empty **while the position was still open**. The book logged
`… HISTORY_UNAVAILABLE; deferring broker_closed` and refused to declare a close it could not confirm;
the terminal resynced at 21:02:08 reporting 1 position. **It did not fabricate a close from an
absence** — seven hours before the real one.

### The finding that matters most

**The learning lane cannot tell a human exit from a book exit.** Every field says `broker_closed`,
and `deal.reason == SL` is identically true either way. The book knows both numbers — the stop it set
(89.984) and the stop that fired (80.511, sitting in the close order's `price_open` and its
`[sl 80.511]` comment) — and **compares neither**. So `edge_state.json` now credits `energy_agri`
with `n=1, wins=1, sum_profit=+493.2` for a price Borhen chose, and the advisory's 151-trade closed
set draws from the same stream.

To be fair to the system: it **refuses to claim an R** for the trade (`result_r 0.0`,
`actual_r_claim_allowed: false`) and the dollars are broker-reconciled, not projected. The
evidence-class discipline is real. But the *provenance of the exit decision* is not captured at all,
and since the whole point of the forward record is honesty about what the sleeves do, this is a
genuine contamination channel — one trade of 151 today, and a general mechanism.

### Would the book have fought him?

**Not on this trade — and only because it stayed small.** Peak 0.504 R never reached the 2.00 R
trigger, so the book had no reason to act and did not.

**Had it reached 2 R, yes — and it would have made things worse.** `_move_sl_to_breakeven`
(`execution.py:9419-9452`) has **no monotonicity guard whatsoever**: it calls
`_modify_sl(ticket, trade.entry_price)` unconditionally. It would have moved the stop from Borhen's
**+0.40 R** back to **0 R**. The trailing path `_move_sl_to_dynamic_r` (`:7324`) *does* ratchet, but
compares against `trade.stop_loss` — the book's **own memory** (89.984), never resynced from the
broker on a normal position — so its guard would have passed too. And the asymmetry gives it away:
`_modify_sl` reads the broker to preserve the **TP** but overwrites the SL, while `_modify_tp` reads
the broker to preserve the **SL**. The SL path is the only one of the four that silently discards
owner input.

Details and the suggested fix order: `receipts/vps_live_ops_20260805/LIVE_BEHAVIOUR_FINDINGS.md`
(LB1–LB6). **Nothing was changed** — these are execution-behaviour changes on armed money.

---

## 4. (C) Health, forward data, intelligence gathering

Full receipt: `receipts/vps_live_ops_20260805/HEALTH_SWEEP.md` (LH's 10 rows re-run, plus continuity
and integrity).

**All ten rows pass except row 3 (the redacted_account token) and row 6 (the unexecuted ceremony) — both
inherited, both owner-word items.** Terminals connected, `trade_allowed` at terminal and account
level, correct logins, clock drift **+2 ms**, disk **75.80 GB free** (better than LH's 42.69),
**0 Application errors in 72 h**, no pending reboot, both books flat.

**Forward data: continuous, no gaps.** Every scheduled boundary is present on both books for the five
days since LH. Two apparent anomalies were chased down and both are expected behaviour:

- The **~52-hour redacted_account gap** (07-31 17:00Z → 08-02 21:00Z) is **the weekend**. Four consecutive
  weekends show the identical signature: FN 0 cycles on Saturday, ~12 on Sunday, while FTMO keeps 6.
  A freshness check cannot tell that from an outage; four weeks of continuity can.
- The **96 → 6 cycles/day collapse** after 07-30 is the **`fx_jpy` pull** — 96/day was the M15
  cadence, `fx_jpy` was the only M15 sleeve, and its removal left H4-only. Exactly as `CLAUDE.md`
  documents.

**Intelligence gathering is working**: monitor daemon on its 5-min loop (`monitoring_degraded:
false`), advisory current (`packet_row_count` 104,926 and rising), packets emitted every cycle, error
channels quiet since June, and **no duplicate daemons** — the restart's sweep left exactly one of
each.

**Method note that nearly produced a false finding:** Windows directory entries are **stale for open
files**. `Get-ChildItem` reported `monitor_daemon.log`, `run_book_console.log` and
`runtime_learning_advisory.log` as 2–3 days old; `os.stat` through a handle showed all three current
to the minute. Read open logs by handle.

### F1 is no longer latent — redacted_account missed a real trade

LH recorded the FN activation-token namespace mismatch as latent, *"zero FN intents have fired."*
**That stopped being true on 2026-08-04.** The FN book prepared **two** `energy_agri` candidates at
0.37 % risk and retried once a minute **from 13:00:41Z to 14:59:08Z — about two hours** — every
attempt refused:

```
broker mutation refused: activation_token_namespace_mismatch
    [exposure_increasing_new_deal] (redacted_account_live_bee34003 != redacted_account)
```

That is the source of the 122 FN launcher rows that day, and the token audit file's mtime is exactly
`2026-08-04T14:59:08Z`. **FTMO took the UKOIL leg of that same signal for +$493.20; redacted_account could
not take anything.** The token file still reads `"namespace": "redacted_account"` today.

It is **fail-closed** — no exposure was created and nothing could be stranded. But two things are
worth knowing: it has now **cost an actual trade**, and **the visible error is misleading** — the
refusal is logged, but what surfaces is `Order failed: timeout_no_fill`, which points at broker
connectivity rather than the token.

---

## 5. (D) GitHub `main` — one file carried, everything else refused

Full receipt: `receipts/vps_live_ops_20260805/MAIN_EVALUATION.md`.

**No fetch, no pull, no merge.** The host's twelve most recent `main` commits are, without exception,
research-lane (Session FA receipts, `MARCH_PREREG_V1`, T2/T3 analyses, lane ledgers) with zero live
value, and the host branch carries arming commits that exist nowhere else.

**Carried, single file: `scripts/mt5_preflight.py`** — Session I's 2026-07-27 retirement. The host was
still running the pre-retirement copy: 9,025 B, sha256 `cff6a058…`, with **four raw
`mt5.order_send` calls at lines 136/142/152/155** — exactly the hash and line numbers `CLAUDE.md` §H6
records, on a machine with two funded accounts and `trade_allowed: true`. Now 10,082 B, `6e92932d…`,
byte-identical to mainline.

Safe to carry when a merge is not, for measured reasons: it imports **nothing from `src/`** (so the
25 divergent files cannot break it), and **nothing calls it** — no script, no scheduled task; the
only reference anywhere is a comment in `fn_smoke_trade.py:75`. Carrying it changed nothing that
runs, and the books' pids were unchanged across it.

`verify_carry.py --check all` could not be used: **that tool is not generic** — it ships inside each
built ceremony package and there is none for this file. Equivalent verification was done instead, and
**the script was never executed in any form**, including its retired arm: `py_compile` exit 0; zero
`order_send` **call sites** (the one textual match is inside the refusal message); and a **static
ordering proof** that the retired arm cannot reach the broker — the refusal `raise SystemExit(2)` is
line 50, `import MetaTrader5` is line 58.

Host commit **`38e935065`**.

---

## 5b. (E) Owner manual moves are now first-class — built, tested, carried, live

**Authorised mid-session by Borhen, verbatim:** *"yes proceed with everything and for the book and
the manual move, if i make a move on my ftmo account it should reflect on the book, my manual moves
should be allowed and 'normal' to have."* That also settles the policy fork §3 refused to decide:
**the book yields to the owner.**

Full receipt: `receipts/vps_live_ops_20260805/OWNER_MANUAL_MOVES_CARRY.md`. Host commit
**`f66da7664`**.

**H1 [ANSWERED]: `src/components/execution.py` is NOT one of R2's 43 bound paths** — nor are the
test file, the supervisor `.ps1`, or `mt5_preflight.py`. **No decision-contract seal was broken by
anything this session did**, and CN's authorised forward break on `broker_net_cost_engine.py`
remains unspent.

**The lineage trap, avoided by measurement.** Mainline's `execution.py` is a *different file* from
the host's — 461,239 B vs 454,116 B — so patching the wrong one would have shipped ~7 KB of untested
drift onto two funded accounts. All work was done against the host's exact bytes, obtained without
touching the host (its blob was already in the Mac's object store via the remote branch; verified to
sha256 `d0d36787…` before anything was written).

What changed, in `execution.py` only:

1. **Broker truth + adoption** — new `_reconcile_broker_protective_levels`, called every management
   tick *before* any exit logic reads `trade.stop_loss`. The book now adopts whatever SL/TP is live
   at the broker. `sl_distance` is deliberately **not** rewritten: it is the sizing basis (1R) that
   every downstream R computation is anchored to.
2. **Never-worsen guard at the single choke point `_modify_sl`** — the book may not write a stop
   worse than the live one. It reuses the codebase's existing `_sl_modify_reduces_or_preserves_risk`
   predicate, which already read broker truth but was wired only to the halt path.
3. **Yields both ways.** Tightened stops are kept. Widened stops are *also* adopted and never
   silently re-tightened — but they emit a **warning** and a packet event carrying
   `owner_sl_implied_risk_ratio` / `owner_sl_risk_exceeds_sized` when they push risk past what the
   position was sized for. Risk is measured **signed**, so a stop moved past entry into profit — the
   2026-08-04 case, ratio **−0.403** — never warns. Governor breach-flatten untouched.
4. **Exit provenance** — `_record_close` stamps `exit_level_provenance` (`owner_modified` |
   `book_set`), `exit_stop_matches_book_intent`, both sides' levels, and the override counters.
   Additive; `broker_closed` semantics unchanged and pinned by a test.
5. **Break-even is skipped cleanly** when the live stop is already better, instead of burning three
   refusals and then paging Borhen with *"broker rejection requires human investigation"* — which
   would be false, and would page him for moving his own stop.

**Test evidence: 24 behavioural tests, all passing on the host against the installed file** in the
real environment (`tests/test_owner_manual_protective_moves.py`, committed to the host branch). They
assert what reaches the broker and what engine state becomes — never source text. The four armed
sleeves are pinned by name as completely unaffected absent an owner move.

**A/B against the pre-patch file, same scenario:** BASE sends 1 request and the owner's 80.511 stop
becomes 83.233; PATCHED sends **0** and it stays 80.511. The defect was real on the host as it stood
this morning.

**The verification caught a bad install before it happened.** Shipping the patch *script* (not
471 KB of base64), the host first produced 481,837 B / `8c3219a9…` instead of the Mac-tested
471,334 B / `91ed9873…` — Python's text-mode I/O on Windows had translated every `\n` to `\r\n`
(+1 byte/line). **The script refused to install; the live file was never touched.** After byte-exact
I/O it produced a file byte-identical to the tested one.

**Restart:** both books, at a chosen moment — the 17:00Z H4 boundary was two minutes away, so the
restart waited for it to complete on both books first. Downtime **1 m 33 s**, both accounts flat,
next boundary four hours clear. Post-restart both books read `authority_gates_ON=True halted=False
killed=False` with **config digests unchanged** (`ffe16657feaf` / `e184a81d3b1b`) — direct evidence
no token-bound byte moved and **no re-mint was needed or done**. Process creation times (17:03:07–15Z)
post-date the file install (16:52:12Z), which is the proof the running books actually loaded it.

**Known limits, stated not buried:** TP provenance is weaker than SL provenance by choice (SL seeds
from the book's authoritative entry-request value; TP seeds from the broker on first sight, because
the book's TP lives in one of two fields depending on policy). Detection is per-tick (~60 s), so a
move made and reverted inside one tick is invisible — it can cost a provenance record, never a wrong
action, because the guard reads live broker state at write time. And this does not retro-label the
2026-08-04 trade; the forensic receipt is that trade's provenance.

## 6. What needs Borhen's word

1. **redacted_account token re-mint (F1) — the only item with a live cost.** Until it is done redacted_account
   cannot open a position, and on 2026-08-04 that already cost it a trade FTMO took for +$493.20.
   **State plainly: fixing it is exposure-INCREASING**, and today's instruction was risk-reducing in
   posture — so it is deliberately left for a knowing decision, not folded in.
   `& .\.venv-gtos\Scripts\python.exe scripts\gtos_activation_token.py mint --profile redacted_account --namespace redacted_account_live_bee34003 …`
   (mirror the 07-30 mint; the 07-31 re-mint's `redacted_account` namespace is the defect). No restart
   needed — the token is read per request.
2. **CM/CN/CO composed ceremony (F2) — still unexecuted, and the clock is short.** Host is a coherent
   07-31 contract (no partial-carry hazard). **The CO declarations expire 2026-08-08 — three days.**
   After that they need freshly signed files, never date edits.
3. ~~**LB6 — the exit-provenance label.**~~ **DONE** — authorised mid-session and shipped
   (`f66da7664`). See §5b.
4. ~~**LB1/LB2 — should the book yield to a stop you moved?**~~ **DECIDED AND DONE** — Borhen:
   *"my manual moves should be allowed and 'normal' to have."* The book now yields in both
   directions, with a warning (never an override) when a widened stop exceeds the sized risk.
   See §5b.
5. **I2 — unbuffered book logging** (`-u` / `PYTHONUNBUFFERED=1` on the launcher line) so a dying
   book's last words reach disk. Diagnostic only; needs a restart, so best folded into the next
   ceremony.
6. **Pagefile 15.19 → 6–8 GB fixed** (LH's item, still open; needs a reboot).

---

## 7. What I changed autonomously

| change | why it was inside the boundary |
|---|---|
| FTMO `--tags` / `--frontier-exits` (host `2fa77722d`) | the owner's explicit instruction; risk-reducing; launcher argument, no config byte, no token |
| `scripts/mt5_preflight.py` retirement carried (host `38e935065`) | risk-reducing (4 raw `order_send` → 0); the commission's own named candidate; self-contained; no caller |
| FTMO worker + supervisor restart | required for the argv to take effect; both accounts flat, no decision boundary within 2.5 h |
| `src/components/execution.py` owner-manual-move support (host `f66da7664`) | **explicitly authorised by Borhen mid-session**; 24 behavioural tests on the host; H1 clean; no config byte |
| both books + supervisor restart (17:03Z) | required to load the patched module; waited for the 17:00Z boundary to complete first; 1 m 33 s, both flat |

Nothing else. Notably **not** done: no token action, no ceremony execution, no config edit, no
sizing/registry/risk change, no redacted_account change, no broker-mutating script, no `firing_sleeves.json`
deletion (it was unnecessary — recording that is more honest than a cosmetic cleanup).

---

## 8. What I got wrong

- **I assumed the commission's `C:\GTOS` root.** My first sweep ran `git` there and got *"not a git
  repository"*, which is what exposed it. Had that command not been in the batch I might have edited
  a file in the wrong tree and "verified" it by re-reading the same wrong file. The fix that actually
  protects against this is deriving the root from the running process — which is now in the receipt.
- **I twice believed a stale directory listing.** I nearly filed "the console logs have been dead for
  3 days" and "the monitor daemon has not written since 08-03" as findings. Both were artifacts of
  `Get-ChildItem` on open files. Corrected by `os.stat`, and called out in the receipt so the next
  session does not repeat it.
- **My first pass at the FN gap was "a 52-hour outage."** It is the weekend. I only found that by
  going back four weeks instead of five days; the five-day window the commission asked for would have
  left it looking like a defect.
- **Three analysis scripts returned empty results because I got the encoding wrong** — the MT5
  journals and the book console logs are **UTF-16LE**. The first run reported "0 auth IPs, 0 trade
  lines" and looked like clean evidence of absence. An empty result from a filter is not a
  measurement until the decode is proven; I added a decode probe before trusting any of them.
- **I initially wrote that "the book would fight a manual SL change" as a single mechanism.** It is
  two, and the more dangerous one is the one *without* a guard (`_move_sl_to_breakeven`), not the one
  with a mis-pointed guard. I had the weaker version in the first draft of the forensic receipt and
  corrected it after reading the actual break-even function rather than inferring from the trailing
  path.
- **I let a commit fail silently.** `git commit -m <heredoc>` returned nothing and I read HEAD before
  assuming success — which is the only reason I noticed. Switched to `-F <file>` with stderr captured.
