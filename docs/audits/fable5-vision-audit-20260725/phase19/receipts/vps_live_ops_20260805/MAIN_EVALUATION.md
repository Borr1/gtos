# GitHub `main` — evaluated, one file carried, everything else refused

Session LM, 2026-08-05. Owner's words: *"have the changes from github main pulled too **if they add
value**"*. That is a judgment, and for almost all of `main` the answer is **no**.

## 1. What is on `main` right now

`main` HEAD `2ecea327b` (2026-08-05). The twelve most recent commits are, without exception,
**research-lane**: Session FA continuation receipts, `MARCH_PREREG_V1`, T2/T3 arm analyses, the
March-executor commission, lane iteration ledgers, LAND A/B supplements. Not one of them touches a
file the live books load.

**Nothing of it was taken.**

## 2. Why `main` is never merged onto this host — measured, not assumed

- The host runs branch **`vps/ultimate-conditioned-expansion-minimal-2026-06-18`**, a different
  lineage. `git branch -a --contains HEAD` returns that branch **only**.
- The host's history carries `118071eaa`, `eb7c28516`, `f855250cd`, `7017c6745`, `d6c9c4b19`,
  `267cccc94` — **arming and carry commits that exist nowhere else**. A merge or pull of `main`
  could revert the arming, disarm carried safety code, or move token-digest-bound config bytes.
- The host's own `origin/main` ref is `33e05e832` with `FETCH_HEAD` dated **2026-07-31 12:06** — it
  is 5 days stale, which is *correct* for this host and was left alone. No fetch, no pull, no merge
  was performed.

## 3. The one thing worth carrying — and it was carried

**`scripts/mt5_preflight.py` — Session I's 2026-07-27 retirement of the order-placing arm.**

The host was still running the **pre-retirement** copy. Measured on the host:

| | before | after |
|---|---|---|
| length | 9,025 B | 10,082 B |
| sha256 | `cff6a058354104ab3542dd180288fb81782850363f5223f751042e035ba32b42` | `6e92932d9d51bb40ecf2129ee06dda01f7bd1dd29c3a46537d988aec111d5ee2` |
| mtime | 2026-05-31T21:35:46Z | (carried 2026-08-05) |
| raw `mt5.order_send` **call sites** | **4** — lines 136, 142, 152, 155 | **0** |

The before-hash `cff6a058…` is **exactly** the value `CLAUDE.md` §H6 records for the un-retired
file, and the four line numbers match its register entry. That is independent corroboration that
this host carried the defect the audit documented — on a machine with two funded accounts and
`trade_allowed: true`, with no runtime-halt check and no activation token on those calls.

The after-bytes are **byte-identical to mainline's** (hash verified against `git show
main:scripts/mt5_preflight.py` computed on the Mac before upload, and again on the host after
writing).

### Why this one was safe to carry when a merge is not

- **Self-contained.** Imports only `argparse, sys, os, dotenv, MetaTrader5, yaml, time, datetime`.
  **Zero `from src` / `import src`.** The host's 25 divergent `src/` files therefore cannot break
  it — the usual lineage hazard does not apply.
- **No caller.** No `.ps1`, no `.py`, and no scheduled task invokes it. The only textual reference
  anywhere is a *comment* in `fn_smoke_trade.py:75` (`# FN min (verified by mt5_preflight)`).
  Carrying it therefore changed **nothing that runs**.
- **Books untouched across the carry** — FTMO pids 4696/9808, FN pids 4708/7080, unchanged.

### Verification substituted for `verify_carry.py --check all`, and why

The commission's ceremony names `verify_carry.py --check all`. **That tool is not generic** — it
ships *inside* each built ceremony package (`phase4/packet_carry/`, `phase5/activation_carry/`,
`phase13/activation_carry_mx/`, `phase15/activation_carry_spread_floor/`), each with its own payload
and expected-hash set. There is no ceremony package for this file, so there was nothing for it to
check. Equivalent verification was performed instead, and **the script was never executed** — it
stays on the never-execute list, including its retired arm:

1. `py_compile` → exit 0.
2. **0** `mt5.order_send` call sites (the single textual match is line 15, *inside the refusal
   message*: ``It was the last path in the repository that called a raw `mt5.order_send` ``);
   6 `order_check` references.
3. **Static ordering proof** that the retired arm cannot reach the broker:
   `if args.test_order or os.getenv("GTOS_MT5_PREFLIGHT_TEST_ORDER"…)` at **line 48** →
   `raise SystemExit(2)` at **line 50**, while `import MetaTrader5 as mt5` is **line 58**. The
   refusal fires before the module is even imported, so neither the flag nor a stale environment
   variable can place anything.
4. No `src` import (point above).
5. No caller (point above).

**Committed on the host branch** as `38e935065`, so no checkout can silently restore the
order-placing version.

## 4. Bookkeeping defect this session introduced — declared, not hidden

`CARRIED_STATE.json` (repo root, stamp `2026-07-31T01:27:23Z`, ceremony `mx_btcusd activation
2026-07-31`) records

```
"scripts/run_book_supervisor.ps1": "63079cec1cb9…"
```

which is the **pre-edit** hash. After the mx disable the file is `ff9299bdf4f0…`, so that entry is
now stale. It was **deliberately not edited**, for two reasons:

- **Nothing running reads it.** A recursive search of `scripts/`, `.tools/`, `src/` and `run_book.py`
  for `CARRIED_STATE` returns **zero** hits. It is a ceremony record, not a runtime check.
- **It is already internally inconsistent**, and guessing at a repair could manufacture a false
  seal-break for the next ceremony: its top-level key says `63079cec…` (the spread-floor version)
  while its own `files` sub-map says `e46fe321…` (the older mx-ceremony version) for the *same path*.
  Two different hashes for one file already coexist in it.

**For the next ceremony to consume:** `scripts/run_book_supervisor.ps1` is now
`ff9299bdf4f007030ac565f194ef5af4730af27a51d8c9535e586a95cff85c91` (19,495 B) and
`scripts/mt5_preflight.py` is now
`6e92932d9d51bb40ecf2129ee06dda01f7bd1dd29c3a46537d988aec111d5ee2` (10,082 B).

## 5. Net

| item | verdict |
|---|---|
| merge/pull `main` onto the host | **refused, and not attempted** |
| Session FA research lane (`train_engine`, receipts, prereg) | **no live value — not carried** |
| `scripts/mt5_preflight.py` retirement | **carried**, host commit `38e935065` |
| host `origin/main` ref / `FETCH_HEAD` | left stale on purpose; no fetch performed |
