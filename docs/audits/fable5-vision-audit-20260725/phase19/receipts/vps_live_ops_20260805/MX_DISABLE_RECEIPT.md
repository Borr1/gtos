# Receipt — `mx_btcusd_d1_donchian_20_breakout` disabled on FTMO

Session LM, 2026-08-05. Owner instruction (verbatim): *"disable the mx_btcusd"*.
Risk-reducing; executed. **No config byte touched, therefore no activation-token re-mint** — the
token digest binding is untouched and both books' tokens remain exactly as Borhen minted them.

## 0. Target file — identity confirmed before the edit

| | value |
|---|---|
| path | `C:\Users\MSI\Documents\ai-trading-agent\scripts\run_book_supervisor.ps1` |
| **root derivation** | from the **running process command line**, not from an assumed path. `C:\GTOS` is a *second, different* tree (Session S's B292 two-tree finding) holding only `archives/ exports/ installers/ logs/ tools/` — no `run_book.py`, no `scripts\`, no `pipeline_state\ultimate_book`. **An edit there would have been a silent no-op.** |
| length before | **19,575 B** |
| sha256 before | `63079CEC1CB927BD23DC3C9D5B3F4B58CD5130D0DBC85601326236A26D8A6E2E` |
| mtime before | 2026-07-31T10:46:55Z |
| encoding | UTF-8, **no BOM** (`23 20 57 37` = `# W7`), **LF** line endings (457 LF, 1 CRLF) — preserved |
| matches LH's recorded spread-floor hash | ✔ `63079cec1cb9` |
| backup | `C:\Users\trader\lm20260805\run_book_supervisor.ps1.before-LM-mxdisable`, sha256 verified identical to the pre-edit file |

## 1. The edit — one substring, one occurrence

Line **140**, the FTMO row of the `$books` array. Removed **both** the tag and the frontier-exits key
in a single replacement (target substring verified to occur exactly once in the file):

```
-  ... tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout"; frontier="mx_btcusd_d1_donchian_20_breakout"; floor="sub_mid_dn_revert,sub_xvol_pullback" },
+  ... tags="crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert"; floor="sub_mid_dn_revert,sub_xvol_pullback" },
```

**Removing the `frontier` key entirely is the correct shape, not a hack:** the launcher builds the
argument as `$frontArg = if ($b.frontier) { " --frontier-exits ..." } else { "" }` (`:435`), and the
redacted_account row has never carried a `frontier` key at all. The FTMO row is now structurally identical
to the FN row that has been launching cleanly since 2026-07-31.

`--spread-geometry-floor` untouched. redacted_account row **byte-identical** to before.

| | value |
|---|---|
| length after | **19,495 B** (Δ **−80** = 34 B tag + 46 B frontier key — arithmetically exact, no collateral change) |
| sha256 after | `FF9299BDF4F007030AC565F194EF5AF4730AF27A51D8C9535E586A95CFF85C91` |
| occurrences of `mx_btcusd_d1_donchian_20_breakout` in the file | **0** (was 2) |

## 2. Pre-flight checks that gated the edit and the restart

| check | why | result |
|---|---|---|
| **PowerShell parse** (`Parser::ParseFile`) | a broken launcher = FTMO down with no auto-restart | **0 errors** |
| **`$books` evaluated in isolation** (lines 139–142 in a scriptblock) | proves the *resulting argv*, not the source text | FTMO → `--tags "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert" --spread-geometry-floor "..."`, **no `--frontier-exits`**; FN unchanged |
| **`--tags ""` fail-OPEN trap** (falsy at `run_book.py:340` ⇒ *all* BUILT sleeves) | the dangerous failure mode | avoided — `tag_count = 4`, non-empty |
| **all-typo fail-closed trap** (silent stand-down every tick) | the mute failure mode | avoided — the four names are the exact strings the launcher log already resolves for both books |
| **open positions, both accounts** | H8 / orphaning | **FTMO 0, FN 0**; equity = balance on both |
| **B365 conviction-size hazard** | restart can inherit a wider same-day firing set ⇒ up to +25 % size | **not applicable** — `firing_sleeves.json` held only `{"days": {"2026-08-04": ["energy_agri"]}}` on both namespaces; **no `2026-08-05` key existed**, so there was nothing for today to inherit. File left untouched (deleting it was unnecessary). |
| **kill flags** | must stay released | absent before and after |

The flat-check, the B365 check and the process kill were executed **inside a single guarded script**
so no state could change between checking and acting; the script is written to abort with a distinct
exit code on `ABORT_NOT_FLAT` or `ABORT_B365_TODAY_KEY_PRESENT`. It reported
`PROCEED_FLAT_AND_NO_TODAY_KEY`.

## 3. Why a restart was required — and why killing the supervisor was part of it

The supervisor evaluates `$books` **once, at process start**, then loops forever
(`while ($true)`, `:429`). The incumbent supervisor (pid 2972, up since 2026-08-03T10:53Z) therefore
held the **old five-tag array in memory**: killing only the FTMO workers would have had it relaunch
them with `mx` still armed. The supervisor also *only ever starts* a missing book and never stops one
(`:432`), so it cannot restart a book on its own.

Sequence, chosen for the smallest possible exposure window:

1. Edit + parse-check + argv-evaluation **before** stopping anything (so a bad edit could never
   leave FTMO down).
2. Guarded flat-check, then `taskkill /F` on FTMO python `1172`, its parent `2380`, the wrapper
   `4836`, and the supervisor `2972`. (`2380` reported *"operation not supported"* — it had already
   exited when its child died; confirmed gone in the verification below.)
3. Let the **5-minute scheduled task** (`GTOS_W7_BookSupervisor`) fire and take over — the proven
   self-heal path LH watched work on 2026-08-03. No hand-launching.

**Window chosen deliberately:** ~14:30Z, both accounts flat, no open position to orphan, and the next
FTMO H4 decision boundary at 17:00Z — nearly 2.5 h away. redacted_account ran untouched throughout (its
processes were never signalled; `Test-BookRunning` kept returning true for it).

## 4. What happened, minute by minute

| UTC | event |
|---|---|
| 14:30:40 | guarded script: FTMO 0 pos / FN 0 pos, no `2026-08-05` firing key → `PROCEED` |
| 14:30:41 | `taskkill /F` on 1172 (FTMO python), 4836 (wrapper), 2972 (supervisor) |
| 14:33:01 | scheduled task fires → **new supervisor pid 8028** |
| 14:33:09 | `book supervisor starting (pid 8028; ns: operator_profile, redacted_account_live_bee34003)` |
| 14:33:10 | `(re)starting book ns=operator_profile` — FN correctly **not** restarted (still alive) |
| 14:33:13 | `started book ns=operator_profile wrapper pid=10756` |
| 14:33:17 | FTMO python 4696 → 9808 up **with the new argv** |
| 14:33:37 | book launcher declares itself armed and healthy |

**FTMO book downtime: 2 m 36 s**, flat throughout, ~2.5 h before the next H4 decision boundary
(17:00Z). redacted_account never signalled — pids 7164/4708/7080 unchanged from 2026-07-31T11:01Z.

## 5. Post-restart verification — every item checked

**Live process command line** (both new FTMO pids 4696 and 9808, read from `Win32_Process`):

```
run_book.py --terminal-path C:\MT5\FTMO\terminal64.exe --namespace operator_profile
  --profile operator_profile --kill-flag pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag
  --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert
  --spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback --poll-seconds 60
```

**No `--frontier-exits`. Four tags. `mx_btcusd_d1_donchian_20_breakout` absent.**

The book's own startup, `shadow_logs/run_book_console.log` 2026-08-05 14:33:34–37:

| line | reads |
|---|---|
| activation context | `namespace=operator_profile, config_digest=ffe16657feaf, token_dir=host-local\.gtos\activation` — **digest unchanged**, i.e. no config byte moved and the token still binds |
| account identity | `verified (namespace=operator_profile)` |
| notifier | `account=$108,365, risk=2.00%, $/R=$2,167, profile=clean3_w7_ceiling_nom2p00` |
| spread floor | **ON** for `sub_mid_dn_revert` **and** `sub_xvol_pullback` at `spread_r <= 0.1000` — preserved |
| gates | **`authority_gates_ON=True halted=False killed=False`** |
| launcher | `BookLauncher starting: tfs=[16388] poll=60s kill=…ULTIMATE_BOOK_KILL_ftmo.flag` |

**`tfs=[16388]` is H4-only, and that is independent confirmation the sleeve really is gone.** The
decision timeframes are derived from the resolved spec set; `mx_btcusd_d1_donchian_20_breakout` is a
**D1** sleeve, and while it was armed the book also ran a D1 boundary — visible in
`ultimate_book_launcher.jsonl` at **2026-08-04T21:05:33Z**, the one FTMO cycle in the record carrying
all five tags. There is no longer a D1 timeframe to run. This is a stronger check than reading the
tag string back: it proves the *resolver*, not just the argument, dropped the sleeve.

Runtime state after:

| check | value |
|---|---|
| `ultimate_book_launcher.jsonl` first post-restart cycle | 2026-08-05T14:33:37Z, ns `operator_profile`, `killed=false halted=false`, **`['crypto','energy_agri','sub_xvol_pullback','sub_mid_dn_revert']`** |
| FTMO heartbeat | pid **9808**, `healthy=true`, age 59 s |
| FN heartbeat | pid **7080** (unchanged), `healthy=true`, age 20 s |
| kill flags | both still **absent** |
| `firing_sleeves.json` | unchanged both namespaces, still only the `2026-08-04` key |
| `run_book_console.log.err` | no new bytes — last entry still 2026-06-29 |
| open positions | FTMO 0 / FN 0 |

## 6. Committed on the host branch

`git commit -F … -- scripts/run_book_supervisor.ps1` on
`vps/ultimate-conditioned-expansion-minimal-2026-06-18`:

```
2fa77722d  Disable mx_btcusd_d1_donchian_20_breakout on FTMO (owner instruction, 2026-08-05)
267cccc94  Spread-geometry floor ARMED on both books …
```

One file, one line changed, working tree clean for that path afterwards. **Committing matters here:**
the host is a lineage that exists nowhere else, and an uncommitted launcher edit is one `git checkout`
away from silently re-arming the sleeve. (Host git identity is the pre-existing `Codex GPT-5
<redacted@example.com>` used by every prior host ceremony; left as-is for consistency. Git emitted its
usual `CRLF will be replaced by LF` notice for the file's single CRLF — cosmetic, and the on-disk
bytes the supervisor actually reads were verified by parse, by argv evaluation, and by the live
relaunch.)

## 7. What was deliberately NOT done

- **No token minted, re-minted or revoked.** Not needed — and out of bounds regardless.
- **No `config/agent_config.yaml` edit**, no registry or confidence change. The `--tags` launcher
  argument is the designed mechanism and it leaves the token digest untouched (proved by the
  post-restart `config_digest=ffe16657feaf`).
- **No redacted_account change of any kind.**
- **`firing_sleeves.json` not deleted** — the B365 mitigation was unnecessary because no key for
  today existed. Deleting it would have been a harmless but unreceipted state change; leaving it
  keeps the record honest.
- **No broker-mutating call.** Every MT5 call this session was `positions_get`, `account_info`,
  `terminal_info`, `history_deals_get`, `history_orders_get`.
