# The command center — one page, one command

**For Borhen. You are the monitor.** This page changes nothing and can change nothing: the tool
behind it imports no broker module, opens no socket, and writes no config. Every action it names is
a ceremony the orchestrator performs and you authorise.

It does not replace `phase4/CANARY_OPERATOR_PAGE.md` or `phase11/FIVE_SLEEVE_OPERATOR_PAGE.md` —
it is the union of what they see, plus the three reads neither could make without asking you to type
the answer.

---

## One command

```bash
python3 scripts/gtos_command_center.py --export-root <vps-export-dir>
```

Everything else is optional. Useful additions:

```bash
python3 scripts/gtos_command_center.py \
    --export-root /Users/borr/GTOSActive/vps-export-YYYYMMDD \
    --fills <dir>/LIVE_TRADE_ROWS.jsonl \
    --armed-utc 2026-07-30T11:52:00Z \
    --html /tmp/command_center.html \
    --day-start-equity FTMO=107872 --day-start-equity redacted_account=96229
```

`--html` writes a standalone page (no scripts, no external requests, light/dark aware) if you would
rather read it in a browser than a terminal.

**Exit codes**, so it can sit behind anything: `0` clean · `1` an ALERT or a STOP · `3` clean, but
something could not be checked. Three rather than two on purpose — "nothing is wrong" and "nothing
was checked" are different, and collapsing them is how `.tools/monitor_books.py` sat mute through the
window it was meant to be watching.

**A worked example is committed** at `phase13/receipts/COMMAND_CENTER_EXAMPLE.{md,html,json}`,
generated from the 2026-07-25 export. It exits **1**, and §1 below is why.

---

## Where the export comes from

There is no live feed. The tool reads a read-only VPS export — the orchestrator's ceremony — and
**every age, equity and gate on the page describes the host as of that export.** A stale export
makes a healthy book look dead and a changed gate look unchanged. The page prints the export's age
at the top, in days, and alerts above 24 h.

The fills file is separate and is built the usual way:

```bash
python3 scripts/w7_live_forensics.py --export-root <export> --out-dir <dir>
#   -> <dir>/LIVE_TRADE_ROWS.jsonl        <- the --fills file
```

---

## 1. Why this page exists: it stopped asking you for the answer

The two older operator pages both take their most important input as **a string you type**:

- `canary_watch.py --launch-tags` and `book_sleeve_telemetry.py --launch-tags-ftmo` take *the armed
  set* that way. The tool then checks your belief against the expectation. In the exact failure mode
  the check exists for — you misremember, or you read the `.ps1` on disk that a running worker was
  not launched from — **the check passes while the book trades a different set.**
- `canary_watch.py --account-state` takes equity, balance and the drawdown floor the same way.

Both are in the export as machine-readable facts, and this page reads them:

| what | where it actually lives |
|---|---|
| the book's `--tags` | the **running worker's command line**, `27_runtime_snapshot/processes_full.json` |
| the gates, as resolved | the **running worker's own launcher record**, `05_shadow_logs/ultimate_book_launcher.jsonl` |
| equity, balance, positions, terminal build | `09_mt5_api/*_{account,terminal}_info.json`, `*_positions_get.jsonl` |

So §1 of the page puts **three independent reads of the armed set** side by side. Agreement is the
signal; disagreement is the alarm.

**On the 2026-07-25 export both accounts read `--tags` ABSENT**, which is why the example exits 1.
That export predates the arming and no money was at risk — the gates were false — but it is the
mechanism demonstrated on real data: a worker launched with no `--tags` trades the whole registry,
and **every log reads perfectly healthy while it does.**

Two failure modes the page treats identically, because they are: `--tags` **absent**, and `--tags ""`
— which is falsy at `run_book.py:340` and also means every BUILT sleeve. The second is worse,
because it *looks* like a deliberate restriction.

---

## 2. The one number on this page you must not read off a single record

The launcher log looks like it answers "what is the book trading". It does not, quite.
`launcher.py:328` builds each cycle record's `tags` as the tags **whose decision timeframe advanced
on that tick** — so a tick that only advances H4 emits only the H4 sleeves.

Measured on the 2026-07-25 export, 5,237 cycle records over five weeks:

| | last record says | union over the log says |
|---|---:|---:|
| FTMO | 22 | **32** |
| redacted_account | **10** | **32** |

A page that read the last record and called it the armed set would under-report redacted_account by
**3.2×** — and under-reporting is the fail-open direction wearing a clean read's clothes, because a
smaller set looks safer.

So the page takes the **union over a window** and refuses to call it complete unless every decision
timeframe present in the window actually advanced inside it. When one did not, the count is printed
as a **lower bound** and says so. Default window is 168 h — wide enough for D1 to advance across a
weekend.

**And the same union errs the other way too, which is stated rather than quietly reconciled:** the
launcher does not apply the DF-1 filter (`book_engine.py:452-453`), so its union is the *pre-DF-1*
candidate set — 32 where only 29 can generate under `include_clean3: false`. One read, two known
biases, both named. The worker `--tags` column is the one that actually bounds the book.

---

## 3. What each panel answers

| panel | question |
|---|---|
| **1 · armed set** | is the book trading what you think it is trading — read three ways |
| **2 · accounts** | equity, open P/L, positions, **distance to the phase target**, static drawdown headroom, today's daily allowance, minimum trading days |
| **3 · authority** | the gates **as the running worker resolved them**, the config on disk, disagreement between them, kill/halt flags, token expiries |
| **4 · alive vs quiet** | two different questions, never merged |
| **5 · sleeves** | per-sleeve R and the pre-registered stop conditions, delegated to `book_sleeve_telemetry.py` |

Three details worth knowing before you read a number off it:

**Distance to target uses each firm's own measured rules**, from
`research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json` — FTMO phase 1 is 10 %,
redacted_account's is 8 %, and both phase 2s are 5 %. The phase is read off the broker's own product
string and the page prints where it got it; `$100k FTMO Challenge 2-Step` does not name a phase, so
the page says it is **assuming** phase 1 rather than guessing silently. Override with `--phase`.

**redacted_account's max-drawdown basis is `TRANSFERRED`, not `MEASURED`** — a secondary audit, not a
captured page. The page prints its headroom and then says so, because if that floor is *trailing*
rather than static it rises with every equity peak and the headroom shown is an over-statement. One
captured page closes it.

**Minimum trading days is counted on each firm's own reset calendar** — FTMO 00:00 CE(S)T,
redacted_account 00:00 server time — and excludes balance operations. It is counted over the whole deal
history in the export, which carries no phase boundary, so read it as an upper bound on progress,
never as satisfaction of the requirement.

---

## 4. "Abnormally quiet" is deliberately not answered yet

The page computes days-since-last-placement, days-since-last-intent and the cycle/intent/placement
counts. It does **not** convert them into an alarm, because the threshold is Session BB's to
measure and an uncalibrated one would be worse than none: for this estate long silences are normal,
roughly seven book-days a month.

When BB's artifact exists, point at it:

```bash
python3 scripts/gtos_command_center.py --export-root <export> --quiet-basis <BB artifact>
```

The schema it must carry is printed on the page itself. One requirement is enforced rather than
requested: **a threshold with no measured `alarm_false_trip_probability` is refused, not adopted.**
`phase11/FIVE_SLEEVE_OPERATOR_PAGE.md` §S1 is why — a floor that fires 74 % of the time on a healthy
sleeve is a coin flip wearing a threshold's clothes, and the only way anyone found that out was by
computing a number that had already been claimed.

---

## 5. What the page will not do

It cannot arm, disarm, resize, flatten or restart anything, and it is not built so that it could.
Removing a sleeve, changing the dial, and shutting a gate are yours; the mechanics are printed on
the page itself, including the one that costs money if taken in the wrong order:

> **Flatten first, confirm flat, then shut the gate.** `live_broker_authority: false` does not
> flatten — it suppresses the flatten and degrades routine trade management to observe-only (H8).

---

## 6. Provenance

| claim | source |
|---|---|
| the tool | `scripts/gtos_command_center.py` |
| its behaviour | `tests/ultimate_book/test_gtos_command_center.py` (37 tests) |
| firm rules, targets, floors, reset calendars | `research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json` |
| the stop conditions and the armed set it checks against | `phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json` |
| per-sleeve economics | delegated to `scripts/book_sleeve_telemetry.py` — not restated, so there is one truth |
| the worked example | `phase13/receipts/COMMAND_CENTER_EXAMPLE.{md,html,json}` |
| the launcher single-record measurement | `phase13/SESSION_BC_COMMAND_CENTER_RESULT.md` §2 |

Nothing on the generated page is transcribed. Every figure is read from the artifacts above, and
anything that could not be read prints as `UNCHECKED` and exits 3.
