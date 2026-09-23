# Session BC — the command center (wave 13, B2000–B2049)

Findings first. Nothing here touched the VPS, ran a broker-capable script, or edited a config or an
R2-bound path. Every artifact is new; no existing file was modified.

---

## 0. The four findings, in the order they matter

**F-BC-1 — The two existing operator pages take their two most important inputs as strings the
operator types, and in the failure mode they exist for, the check is a tautology.** `canary_watch.py
--launch-tags` / `book_sleeve_telemetry.py --launch-tags-ftmo` compare the armed set *the operator
believes* against the expectation; `--account-state` takes equity and the drawdown floor the same
way. If the operator misremembers, or reads a `.ps1` on disk that a running worker was not launched
from, **the check passes while the book trades a different set.** Both facts are in the export as
machine-readable state, and `scripts/gtos_command_center.py` now reads them: `--tags` from the
running worker's own command line, equity from the broker's own `account_info`. That is the reason
this page is worth a third tool. [MEASURED — the mechanism is demonstrated on the 2026-07-25 export;
see F-BC-2.]

**F-BC-2 — On the 2026-07-25 export, both `run_book.py` workers were running with NO `--tags` at
all.** Read off `27_runtime_snapshot/processes_full.json`; the command lines are complete (266 and
262 chars, ending naturally at `--poll-seconds 60`), not truncated. That export **predates the
2026-07-29 arming and the gates were false, so no money was exposed** — the value is that it
confirms B327's warning at the *process* level rather than the committed-launcher level, and proves
the check is now a measurement. A worker with no `--tags` trades the whole include-flag registry and
every log reads perfectly healthy while it does.

**F-BC-3 — The launcher log's `tags` field is a per-tick subset, and reading it as the armed set
under-reports in the fail-open direction.** `launcher.py:328` builds each cycle record's `tags` as
`tuple(t for tf in advanced for t in self._tf_tags[tf])` — only the tags whose *decision timeframe
advanced on that tick*. Measured over 5,237 cycle records, 2026-06-18..07-25:

| | last cycle record | union over the log |
|---|---:|---:|
| FTMO | 22 | **32** |
| redacted_account | **10** | **32** |

A page reading the last record would under-report redacted_account by **3.2×**, and a smaller set *looks
safer*. The modal record carries 10 tags (2,362 of FTMO's 2,654 **cycle** records; the file also holds 128 `manage` records, which carry no `tags` field at all). The tool therefore takes the
**union over a window** and checks the completeness condition — every decision timeframe present must
have advanced *inside* the window — publishing a **lower bound** when it fails. The same union errs
the other way too and that is stated rather than reconciled: the launcher does not apply DF-1
(`book_engine.py:452-453`), so its union is the pre-DF-1 candidate set (32 where 29 can generate
under `include_clean3: false`). One read, two known biases, both named on the page.

**F-BC-4 — MT5 build 6060 adds a terminal-side AI order path, MT5's Live Update cannot be disabled,
and GTOS's activation token is structurally incapable of seeing it.** Verified at source:
`enforce_broker_mutation_authorized` runs **inside the GTOS Python process**, immediately before
`self._mt5.order_send(request)` (`src/mt5/mt5_real.py:490-497`). Its own comment is precise — *"every
broker mutation **the engine performs** arrives here."* An order originating inside `terminal64.exe`
(native MCP) or inside a third-party Python MCP server never enters that function. Neither do the
three YAML gates help: `live_broker_authority: false` suppresses mutation inside `book_owner.py`,
which a terminal-side order does not traverse.

So the question is not *should GTOS adopt MT5's MCP*. It is: **a new order path is arriving on an
armed, funded host on MetaQuotes' schedule, and the only controls that bind it are the terminal's own
AI-trading permission and the broker's `trade_allowed`.** Both VPS terminals read **build 5836** at
the export (2026-07-25); 6060 released 2026-07-23/24. Full design, provenance and the two owner
decisions: **`phase13/MT5_MCP_INTEGRATION_DESIGN.md`**.

---

## 1. Delivered

| artifact | what it is |
|---|---|
| `scripts/gtos_command_center.py` | the read-only dashboard generator — markdown, standalone HTML, and JSON |
| `docs/.../phase13/COMMAND_CENTER_OPERATOR_PAGE.md` | how to run it and how to read it, for Borhen |
| `docs/.../phase13/receipts/COMMAND_CENTER_EXAMPLE.{md,html,json}` | a worked page generated from the 2026-07-25 export (exits **1**, for F-BC-2) |
| `docs/.../phase13/MT5_MCP_INTEGRATION_DESIGN.md` | the MCP design: what it exposes, what it replaces, the security core, the wiring plan, OD-BC-1/2 and HR-BC-1/2 |
| `scripts/gtos_mt5_mcp_readonly.py` | the read-only MT5 tool contract, prototyped against exported state; seven tools, every mutating name enumerated and refused |
| `tests/ultimate_book/test_gtos_command_center.py` | 39 tests |
| `tests/ultimate_book/test_gtos_mt5_mcp_readonly.py` | 24 tests |
| `docs/.../phase13/receipts/SESSION_BC_AB_RECEIPT.md` | the A/B, emitted via `pytest_failset.py receipt` |

### The page, panel by panel

1. **the armed set** — three independent reads (worker command line · launcher union · config
   include flags), cross-checked; agreement is the signal, disagreement the alarm
2. **the accounts** — equity, balance, open P/L, positions with SL/TP, pending orders, **distance to
   the phase target**, static drawdown headroom, today's daily allowance, minimum trading days
3. **authority** — the gates *as the running worker resolved them*, the config on disk, the
   disagreement between them, kill/halt flags, token expiries
4. **alive vs quiet** — never merged
5. **per-sleeve economics** — delegated to `book_sleeve_telemetry.py`, not restated

Exit codes match the sibling tools: `0` clean · `1` ALERT or STOP · `3` clean but something could not
be checked.

### Three things built deliberately rather than conveniently

- **Composition, not duplication.** Panel 5 calls `book_sleeve_telemetry.build_page` rather than
  re-implementing the stop conditions, the two floors, or the day-blocked sign-flip. It also
  **drops that delegate's S6 findings**, because panel 1 answers the same question from strictly
  better evidence and two answers to one question on one page is how a page loses its authority.
- **Firm rules are bound, not transcribed.** Targets, floors, reset calendars and minimum trading
  days come from `research/operations/broker_truth_layer_2026_07_27/FIRM_RULES_V1.json`, with its
  own `coverage` field carried onto the page: redacted_account's max-DD basis is `TRANSFERRED`, so the
  page prints its headroom and then says the number assumes a static floor and would be an
  over-statement if the floor trails.
- **The quiet alarm is a slot, and it refuses an uncalibrated threshold.** BB owns the number. The
  page computes days-since-placement/intent now, publishes the `gtos.live.quiet_basis.v1` schema it
  will adopt, and **refuses any threshold that carries no measured
  `alarm_false_trip_probability`** — `FIVE_SLEEVE_OPERATOR_PAGE.md` §S1 is the precedent: a floor
  that fires 74 % of the time on a healthy sleeve is a coin flip wearing a threshold's clothes.

### The MCP prototype's one structural property

`call_tool` dispatches through an allow-list, and every known mutating name — `create_order`,
`order_send`, `modify_order`, `close_position`, `cancel_order`, `modify_position`, `order_check` —
is enumerated and refused **with a reason that names the activation token it is protecting**, so a
caller gets a refusal that ends the conversation rather than a lookup failure it retries under
another spelling. The argument is in the design doc §5 and is one sentence: *a model instructed not
to trade is a policy; a server with no order code is a mechanism, and only the second survives a
prompt injection carried in a symbol comment.*

---

## 2. The A/B

**0 bad → 0 bad · 0 regressed · +63 passing**, scope `tests/ultimate_book` (896 → 959 passed,
skipped 3 → 3). Receipt: `phase13/receipts/SESSION_BC_AB_RECEIPT.md`, emitted by
`pytest_failset.py receipt` with both captures embedded.

**A cross-directory check was run separately**, because every file here is new and the only
breakage class outside `tests/ultimate_book` is import-level — which is exactly what §3(b) was:
my two files + `test_defect_register_repairs.py` + the three `tests/test_*.py` that put `scripts/`
on `sys.path` themselves → **170 passed, 0 failed, 0 skipped**. That combination failed once, on an
**over-strict assertion of mine** rather than a real defect (see §3(f)).

**The scope is wider than the tool selected, deliberately.** `pytest_failset.py scope` resolved the
blast radius to exactly my two new test files with zero escapes — correct, and a degenerate A/B,
because the BEFORE side would have collected nothing. I ran the whole directory my tests live in
instead, by copy-back (never `git checkout`). That decision is what caught the defect in §3.

---

## 3. What I got wrong

**(a) I counted trading days by slicing an epoch integer as a string, and the page reported 240
trading days over a 33-day deal history.** `str(deal["time"])[:10]` on a 10-digit epoch returns the
whole number, so every deal at a distinct second became a distinct day. The figure was wrong by
~12× and looked entirely plausible in the table. Three things were wrong at once and all three are
now fixed and pinned: `time` is a **broker-clock** epoch (converted with
`broker_clock.broker_epoch_to_utc`, which fails closed on an unregistered server); balance
operations are not trading days (`type: 2`, empty symbol); and the day boundary is each **firm's own
reset calendar**, not UTC. Corrected: FTMO 19, redacted_account 26 (28 on UTC — the calendars genuinely
differ, which is why doing it properly mattered). Also a dead filter, `if d.get("entry") in (0, None)
or True`, which read like a filter and was a no-op.

**(b) I put `scripts/` on `sys.path` and silently turned two passing tests into skips — and the
estate had already found and documented this hazard.** `scripts/research/` is a REGULAR package and
the repo root's `research/` is a NAMESPACE package, so it wins **regardless of sys.path position**;
`research.operations` then stops resolving process-wide, and
`test_defect_register_repairs.py`'s two `pytest.importorskip` tests skip instead of running. My first
fix — append instead of insert — **did not work**, for exactly that reason. The final fix is
`_load_sibling`: load sibling modules by file path, never put `scripts/` on the path at all.

The honest part: **`tests/test_mc_firm_rules.py:20-37` already documents this precisely**, including
that appending is not enough, and cites Session V's full-suite A/B measuring 6 unexplained
regressions from the alternative. I rediscovered it the expensive way. I should have grepped for
prior art on `scripts/research` before writing an import. My mitigation is stricter than the existing
workaround (no global side effect, no dependence on import order) and is pinned by two tests, but the
finding was not mine.

I also nearly filed a wrong handoff off the back of it — that the three other files inserting
`scripts/` at position 0 carry the same latent contamination. **I tested it and they do not**, because
they pre-warm `sys.modules` with the correct `research` package first. Checking took thirty seconds
and the claim would have sent someone after a non-problem.

**(c) A test of mine asserted the code was wrong when the test was.** I built a broker-epoch fixture
from a UTC timestamp, which is the exact trap CLAUDE.md warns about, and the reset-calendar test
failed. The code was right. The fixture is now `_broker_epoch()`, which constructs the epoch through
`offset_seconds_at_utc`, and a second test pins the convention so a "simplification" to
`utcfromtimestamp` fails loudly.

**(d) I read MQL5 article 21905's 14-tool surface as a description of the terminal's native MCP.**
It is a **third-party Python server** with opposite security properties (trading on by default, no
documented disable, plaintext credentials in `config.json`). The conflation nearly reached the design
doc's recommendations, where it would have understated the native path's controls and overstated the
third-party path's. §2 of the design doc exists to keep the two apart.

**(f) My own regression test asserted an invariant I do not own, and it went red on innocent
files.** It checked the process-wide property *"`scripts/` is never on `sys.path`"* — which
`tests/test_mc_firm_rules.py`, `test_armed_set_mc.py` and `test_w7_recost.py` legitimately violate,
because they need it and pre-warm `sys.modules` with the correct `research` package first. The
invariant this session actually owns is narrower: *importing `gtos_command_center` must not put it
there, and must not break `research.operations`.* That is now asserted in a clean **subprocess**, so
it cannot depend on collection order. I then verified the test can still fail: reintroducing the
defect in its subtler **append** form turns it red, and removing it turns it green.

**(e) The HTML page was not visually verified.** The Chrome extension is not connected in this
session. It is validated structurally instead — well-formed (parser check, no unclosed tags), 5/5
tables and 2/2 `<details>` closed, no `<script>`, no external references, tables in `overflow-x`
containers, light/dark aware — but nobody has looked at it. Worth one glance before it goes in front
of Borhen.

---

## 4. Unverified, and deliberately left so

- **Whether the VPS terminals have taken build 6060.** The export is from 2026-07-25 and reads 5836.
  This session does not touch the VPS. HR-BC-1, one command.
- **The default of 6060's AI-trading permission.** Not disclosed by the release notes, the forum
  thread, or the trade press. Every recommendation in the design doc is written not to depend on it;
  HR-BC-2 is the read.
- **"Live Update cannot be disabled" is [TRANSFERRED]**, from MQL5 forum consensus across several
  threads, not tested against a terminal here.
- **`mqid: true` on both terminals is [MEASURED]**; the inference that it satisfies 6060's AI sign-in
  prerequisite is **not**, and is stated as a reason to check rather than a conclusion.
- **Token expiries are UNCHECKED on this laptop.** The live tokens are on the VPS, outside every
  export by design. `--token-dir` is supported; the panel reports UNCHECKED rather than alerting, so
  it cannot cry wolf on a laptop run. It also does **not** verify the HMAC — a hand-edited expiry
  would read as valid here and be refused by the engine, and the page says so.
- **The example page's `--armed-utc` is 2026-06-18, chosen to exercise panel 5 against the only
  fills corpus that exists.** It is a demonstration of the tool, not a statement about the armed
  book.

---

## 5. Handoff to the orchestrator

1. **OD-BC-1 / OD-BC-2 are owner decisions with an external clock.** Should AI-initiated trading be
   *prohibited* on both terminals (recommended — an unattended VPS cannot man a confirmation
   prompt), and is a terminal upgrade acceptable on an armed funded host at all? The build is
   arriving whether or not anyone decides; deciding late means the default decided.
2. **HR-BC-1 / HR-BC-2 are two `Select-String`-scale host reads** for the next ceremony:
   `terminal_info.build` on both terminals, and — if either is on 6060+ — the current AI-trading,
   network and command-line permission values.
3. **Run the command center at the next export** and read panel 1 first. It is the check that says
   whether every other number on the page is about the book you think is running:
   `python3 scripts/gtos_command_center.py --export-root <export> --fills <LIVE_TRADE_ROWS.jsonl>`
4. **BB's quiet basis drops straight in** via `--quiet-basis`; the schema is printed on the page and
   an uncalibrated threshold is refused rather than adopted.
5. **A future session adding a `scripts/`-importing module should use `_load_sibling`**, not a
   `sys.path` edit — §3(b), and `tests/test_mc_firm_rules.py:20-37` for the prior art.
6. **The full-suite A/B is yours, once per train.** Mine is scoped to `tests/ultimate_book` and every
   file I added is new, so the blast radius outside that directory is import-level only — which is
   precisely the class of breakage §3(b) was, so it is worth a look rather than an assumption.
