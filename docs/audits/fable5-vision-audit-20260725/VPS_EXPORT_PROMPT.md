# VPS export session — prompt to paste into a Claude session ON THE WINDOWS VPS

Written 2026-07-26. Copy from `--- BEGIN PROMPT ---` to `--- END PROMPT ---`.

The prompt is deliberately short. It states the goal, three prohibitions that exist because this
project already lived the incidents behind them, and a list of things previous sessions missed — as
hints, not instructions. Judgment about what is worth exporting belongs to the session on the machine;
it is the only one that can see the filesystem.

---

--- BEGIN PROMPT ---

You are on a **Windows VPS that is the live filesystem of record for a real-money trading system** —
three prop-firm accounts, their MetaTrader 5 terminals, and the runtime state of a book that traded
live 2026-06-18 → 07-02 and has been in shadow mode since.

**Your job: export everything of evidentiary value to the owner's Mac over host-mesh.** This is a
one-shot comprehensive pull that everything downstream depends on — live-vs-validation forensics,
execution-cost calibration, the learning loop, and the eventual canary package. **Err heavily toward
exporting more.** Filtering happens on the Mac, where it is cheap and reversible; a second trip here
is neither. If you are unsure whether something matters, take it.

## Three prohibitions

Not doubts about your judgment — each is an incident this project has already had.

1. **Change nothing about the running system.** Do not stop, start, restart, reconfigure or repair the
   `GTOS_W7_BookSupervisor` task, `run_book.py`, the MT5 terminals, any config, or any gate. Do not
   place, modify or cancel an order — read-only MT5 calls only.

   *Why:* in May and June, agent sessions hot-patched live trading code between ticks — 55 repair
   events in one day with 22 positions open. The repairs worked; the trading lost money and nobody
   could tell which changes caused what. The specific trap here: this book is deliberately braked at
   `ultimate_book_live_broker_authority: false`. It looks broken. It is not. Leave it.

2. **Do not delete, move or "clean up" anything — especially flags.** Files named `*HALT*`, `*KILL*`,
   `*FLATTEN*`, `*DISABLED*` are a safety mechanism, and their presence and contents are themselves
   evidence you are here to capture.

   *Why:* halt flags have already been deleted on this machine once, while the system was trading.

3. **No git writes.** No commit, checkout, stash, clean, pull or push. `git status` / `log` / `diff`
   are fine and useful.

   *Why:* the working tree almost certainly holds uncommitted live state that exists nowhere else.
   Tidying before exporting destroys the thing being exported.

If something looks wrong, **write it down and report it — do not fix it.** That report is valuable.

## Start by orienting, and show the owner before you pull

Find the GTOS checkout(s) (search for a directory holding both `run_book.py` and
`config/agent_config.yaml` — do not assume a path). Report branch, HEAD, dirty state, free disk space,
what is currently running, and the size of what you propose to export. Then go.

Write everything into one new directory, `C:\gtos_export_<UTC-timestamp>\`.

## Things previous sessions missed — hints, not a checklist

Export whatever you judge valuable. These are called out only because they have been overlooked
before, or because nobody on the Mac has ever had them:

- **The halt/kill flag contents, and a one-line verdict: is this machine halted, and by what.** These
  files exist in no working tree on the Mac, so the real safety state has never been verifiable from
  there. This closes a months-old hole.
- **MT5 terminal logs** (`Logs\`, `MQL5\Logs\` under each terminal). They record every order the
  terminal actually sent, independently of the system's own ledgers — a cross-check rather than more
  of the same.
- **`history_deals_get` from account inception to now, all three accounts** (including the untouched
  one), plus `history_orders_get`, `account_info`, `positions_get`, `symbols_get` and per-symbol specs
  for the traded symbols. This is the authoritative broker record of what happened to the money, and
  nobody has it. The two brokers' contract specs differ, which is an open question.
- **Runtime-learning packets, placement ledgers, trade records, `shadow_logs/`, `pipeline_state/`,
  `knowledge_base/`, `logs/` — for BOTH namespaces** (`operator_profile` and
  `redacted_account_live_bee34003`), across the whole period, not just the live fortnight.
- **Untracked files.** `git status --porcelain -uall` lists runtime artifacts that exist only here.
- **The config actually on disk**, the supervisor task definition, launch scripts, and relevant
  Windows event-log entries.
- **`broker_order_lifecycle_capture_v4.jsonl`** — believed to have never captured a single row
  anywhere. Confirming it either way ends a standing question.
- **Market data: inventory it, don't bulk-pull it.** Report per symbol and broker what depth
  `copy_rates_range` and `copy_ticks_range` actually return (earliest/latest, real vs synthesised
  ticks, rough rows/month). A full tick backfill is ~290 GB, so the owner sizes that from your numbers
  as a second pass — unless you judge a targeted subset is worth taking now, in which case take it and
  say why.

## Two things about the output

- **Hash it.** A `MANIFEST.jsonl` with `source_path`, `sha256`, `bytes`, `mtime_utc` per file, so the
  Mac can verify the transfer landed intact rather than assume it. Note anything unreadable (files
  locked by a running process are expected) instead of skipping silently.
- **Keep credentials separate.** Anything with a login, password, key or token goes in its own
  `SECRETS_DO_NOT_COMMIT\` directory, transferred separately. A file with plaintext account logins is
  already in this project's git history by accident; segregating them means the bulk export can be
  archived and processed without repeating that.

Send over **host-mesh**, not cloud storage — this carries account identity and is the only copy of the
live evidence. Leave the export directory in place until the Mac confirms the manifest verifies.

## Report back

Is the machine halted and by what; what is running and anything that looked wrong (stated, not fixed);
the three account balances and the deal-history range you got; total size transferred; and **anything
you found that this prompt did not anticipate and you think matters.** You are the only one who can
see this filesystem — that last item is the point.

--- END PROMPT ---

---

## Notes for the Mac side (not part of the prompt)

- Verify `MANIFEST.jsonl` before treating any of it as evidence.
- Land on local disk, never an iCloud path (`docs/STORAGE_AND_REMOTES.md:11-12`); archive a compressed
  copy to iCloud afterwards, write-once, manifest alongside.
- `SECRETS_DO_NOT_COMMIT/` never enters the repo or an iCloud archive that later gets unpacked.
