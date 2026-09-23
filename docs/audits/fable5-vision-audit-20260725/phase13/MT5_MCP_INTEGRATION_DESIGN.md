# The MT5 MCP integration — design, security posture, and the decision that is already running

Session BC, wave 13, 2026-07-30. Blocks B2000–B2049.

**For Borhen and the orchestrator.** Nothing in this document was executed against the VPS. The
prototype it describes reads a read-only export and contains no order-sending code.

---

## 0. The finding that changes the shape of this question

The commission asked for a design: *build 6060+ has native MCP; what does it expose, what oversight
does it replace, what is the security posture, what is the wiring plan.* Answering it turned up
something that reorders the question.

> **MetaTrader 5 build 6060 adds a terminal-side AI order path, MT5's Live Update cannot be
> disabled, and GTOS's primary brake — the activation token — is structurally incapable of seeing
> that path.**

So the honest framing is not *should GTOS adopt MT5's MCP?* It is: **a new order path is arriving on
an armed, funded host on MetaQuotes' schedule, and the question is whether anyone has decided the
terminal's AI-trading permission before it lands.** That is a step-zero host read and an owner
decision, and it is independent of whether GTOS ever builds an MCP integration at all.

The rest of this document supports that claim, then gives the design.

---

## 1. What is measured, and what is not

| fact | value | status |
|---|---|---|
| both VPS terminals' build at the 2026-07-25 export | **5836** | **[MEASURED]** `09_mt5_api/{ftmo,redacted_account}_terminal_info.json`, `"build": 5836`, both files |
| MT5 build 6060 release | **2026-07-23/24** | **[MEASURED, sources disagree by a day]** the release-notes page reads 23 July; the forum/search summary reads Friday 24 July. Either way it is **before** the export and the terminals had not taken it. |
| 6060 ships native MCP + AI agents | yes | **[MEASURED]** MetaQuotes release notes for build 6060 |
| AI-initiated trading is configurable: allow / prohibit / require manual confirmation | yes | **[MEASURED]** release notes |
| **the default of that setting** | — | **[UNVERIFIED — explicitly not disclosed]** by the release notes, the forum thread, or the trade press. This is the single most important unknown in the document. |
| Live Update can be disabled | **no** | **[TRANSFERRED]** MQL5 forum consensus across several threads: the built-in updater cannot be turned off; the workarounds are UAC prompts, avoiding MetaQuotes demo servers, or portable mode. Not verified by this session against a terminal. |
| both terminals have MetaQuotes ID data set | `"mqid": true` | **[MEASURED]** both `terminal_info` files. `TERMINAL_MQID` is the push-notification identity tied to an MQL5.community account. **[UNVERIFIED as an inference]** that this alone satisfies 6060's AI sign-in prerequisite — it is a reason to check, not a conclusion. |
| whether the terminals have updated since 2026-07-25 | — | **[UNVERIFIED]** this session does not touch the VPS. The export is five days old. |
| `dlls_allowed` | `false`, both | **[MEASURED]** — worth noting because it is the one adjacent permission that IS locked down. |

**The three numbers that matter together:** 6060 released 07-23/24 · the terminals read 5836 on
07-25 · the update cannot be refused. Brokers control which build their server offers, so
FTMO-Server3 and redacted_account-Server 2 may lag by weeks. But the arrival is a *when*, not an *if*.

---

## 2. Two different things are called "the MT5 MCP", and they have opposite security properties

Conflating these would be the central error available here, so they are separated first.

### 2a. The terminal's NATIVE MCP (build 6060+)

The terminal itself becomes an MCP source. An external agent — the release notes name OpenAI Codex
and Claude Code — connects to the platform, reads market and account state, and can "perform
required operations". Setup is a sign-in with an MQL5.community account; the platform then
self-configures a provider and key. There are separate permission settings for AI-initiated
**trading**, for **network requests**, and for **command-line operations**, and the AI settings
synchronise between the terminal and MetaEditor.

- **Security property:** there IS a permission for trading, with a middle setting (manual
  confirmation). The default is undisclosed.
- **Where the order originates:** inside `terminal64.exe`.

### 2b. A THIRD-PARTY Python MCP server

Several exist (`Qoyyuum/mcp-metatrader5-server`, `ariadng/metatrader-mcp-server`, and the pattern
written up in MQL5 article 21905). They are ordinary Python processes that `import MetaTrader5`,
attach to a running terminal, and re-export its API as MCP tools over stdio. The article's server
exposes 14 tools across account/market data and trading; **trading is enabled by default and the
article documents no mechanism to disable it.** Its `config.json` carries `login`, `password` and
`server` in plaintext.

- **Security property:** none beyond "do not install it". A `destructiveHint: True` annotation is a
  hint to a model, not a gate.
- **Where the order originates:** a separate Python process holding the same terminal.

**Neither is a variant of the other, and the estate must never treat a claim about one as evidence
about the other.**

---

## 3. What oversight this would actually replace — stated honestly

The temptation is to say MCP replaces the export ceremony. It does not, and overselling it here
would be the same error the estate keeps finding in its own artifacts.

| today | with a read-only MCP | genuinely replaced? |
|---|---|---|
| account equity / positions / terminal state, via a full VPS export ceremony | one tool call | **latency only.** The export ceremony also captures config, logs, process list, git state — none of which an MT5 MCP can see. |
| `--tags` truth (what the book is actually trading) | **not available** — this lives in a Windows *process command line*, not in MT5 | **no.** The command center reads it from the export's process snapshot; MT5 has no idea. |
| the authority gates | **not available from MT5** | **no.** They are GTOS config resolved inside the GTOS process. |
| heartbeat / launcher cycle stream | **not available from MT5** | **no.** |
| per-sleeve R and the stop conditions | **not available from MT5** | **no** — MT5 has deals, not sleeve attribution. |

**So the honest scope is narrow: MCP shortens the latency on the MT5-shaped slice of the picture
(equity, positions, terminal health, symbol specs) and nothing else.** That is a real improvement —
`gtos_command_center.py`'s account panel is exactly as fresh as the last export, and today that is
five days — but it is a fraction of the page. Anyone proposing MCP as a replacement for the export
ceremony has not read the table above.

There is one thing it adds that is not a replacement at all: **`terminal_info.build` becomes
watchable.** Nothing in the estate monitors it today, and §1 is the reason it should be.

---

## 4. The security core: both MCP paths are outside GTOS's primary brake

**[VERIFIED at source, this session.]**

Since 2026-07-26 the estate's primary brake is presence-of-authorization, not absence-of-halt:
`RealMT5.order_send` refuses any exposure-increasing request without a valid activation token for
that account. The choke point is `src/mt5/mt5_real.py:475-497`:

```python
def order_send(self, request: dict) -> OrderResult:
    # THE ACTIVATION CHOKE POINT.
    ...
    enforce_broker_mutation_authorized(request, ...)
    result = self._mt5.order_send(request)
```

Its own comment is precise, and the precision is the point: *"Every broker mutation **the engine
performs** arrives here."* The guard runs **inside the GTOS Python process**, immediately before
delegating to the `MetaTrader5` module.

Therefore:

- An order placed by the **terminal's native AI** (2a) originates inside `terminal64.exe`. It never
  enters a GTOS process and never reaches `enforce_broker_mutation_authorized`.
- An order placed by a **third-party MCP server** (2b) is that server's own
  `MetaTrader5.order_send`, in its own process. Same conclusion.

**The activation token cannot see either.** It is not weakened, bypassed, or misconfigured — it is
simply guarding a different door. This is the same structural class as H6's raw-`order_send`
inventory, except that the new call sites would not be in this repository at all.

Two second-order consequences worth having in front of you:

1. **The config digest does not help.** The token binds `config_digest_sha256`, so editing GTOS's
   config invalidates it. An MCP order changes no GTOS config, so nothing invalidates and nothing
   notices.
2. **The three YAML gates do not help either.** `live_broker_authority: false` suppresses mutation
   inside `book_owner.py` (H8). A terminal-side AI order does not traverse `book_owner.py`.

**So the entire GTOS brake stack — three config booleans, the activation token, the kill flags — is
blind to an order that does not come from GTOS.** The only controls that bind are the terminal's
own AI-trading permission and the broker's `trade_allowed`.

---

## 5. Security posture: read-only, and read-only by construction

The recommended posture, in order of strength:

**R1 — Decide the terminal's AI-trading permission before the build arrives.** This is not a GTOS
engineering task and it does not wait on anything below. It is one setting per terminal, and the
right value on a funded prop account carrying real positions is **prohibit** (not "require manual
confirmation" — an unattended VPS has nobody to confirm, so that setting degrades to a queue of
blocked actions and an operator who eventually clicks). Owner decision; see §8 OD-BC-1.

**R2 — Do not install a third-party MT5 MCP server on the live host. Ever.** §2b: trading on by
default, credentials in plaintext, no gate. There is no configuration of it that is safe on an armed
account, and the read-only value it offers is available from a server GTOS controls.

**R3 — If GTOS wants an MCP surface, GTOS owns it and it has no order code.** This is the design in
§6. The distinction that carries the weight: a model *instructed* not to trade is a policy, and a
policy is defeated by any instruction that reaches the model — including one carried in a symbol
comment, a deal comment, or a news headline the agent reads. A server with **no order-sending
function in it** is a mechanism. Only the second survives.

The prototype makes that structural rather than promised:

- `scripts/gtos_mt5_mcp_readonly.py` imports no `MetaTrader5`, holds no connection, and dispatches
  through an allow-list;
- every known mutating tool name — `create_order`, `order_send`, `modify_order`, `close_position`,
  `cancel_order`, `modify_position`, `order_check` — is **enumerated and refused with a reason**, so
  a caller gets a refusal that ends the conversation rather than a lookup failure it retries under
  another spelling;
- `tests/ultimate_book/test_gtos_mt5_mcp_readonly.py` pins all of it, including a source assertion
  that the file contains no mutation construct. (A source-substring test is the wrong tool almost
  everywhere in this estate — it passes against a wrong implementation. It is the *right* tool for
  "this file must not contain X", which is exactly the claim.)

**R4 — Watch `terminal_info.build`.** `get_terminal` puts it on the read-only surface and
`gtos_command_center.py` prints it per account. A build crossing 5836 → 6060+ is the trigger for
R1's setting to be re-read, because a new build may reset or introduce it.

---

## 6. The wiring plan

Four stages. Each is independently valuable and none of the later ones is a prerequisite for the
command center, which already works from exports today.

### Stage 0 — decide the permission (no code)

Owner decision OD-BC-1 (§8) plus a host read of both terminals' current build and AI settings, as
part of the orchestrator's next ceremony. **This is the only stage with a deadline, and the deadline
is set by MetaQuotes, not by us.**

### Stage 1 — the read-only contract, backed by exports *(delivered this session)*

`scripts/gtos_mt5_mcp_readonly.py`. Seven tools:

| tool | answers |
|---|---|
| `get_account` | balance, equity, margin, account identity |
| `get_terminal` | **build**, connected, trade_allowed, mqid, ping |
| `get_positions` | open positions with SL/TP/magic |
| `get_pending_orders` | pending orders |
| `get_history_deals` | recent deals, with the broker-clock semantics declared at delivery |
| `get_symbol_info` | contract spec for one symbol |
| `get_authority_state` | **GTOS-specific**: gates, effective sleeve union, heartbeat |

`get_authority_state` is the one that justifies a GTOS-owned server rather than a generic MT5 one.
An agent that re-derived the armed set from the raw launcher log would walk straight into
`launcher.py:328` — a cycle record's `tags` is only the tags whose *timeframe advanced that tick*.
On the 2026-07-25 export the last redacted_account record says **10** and the union says **32**. The tool
hands back the union, the completeness flag, and `last_single_record_would_have_said`, so a caller
cannot make that mistake quietly.

### Stage 2 — swap the backend, keep the contract

Replace the export reader with a live `MetaTrader5` read behind the same seven signatures. The
contract, the refusal layer and the tests do not change. This is the only stage that runs on the
VPS, and the properties that make it safe are already fixed by Stage 1:

- read-only by construction, not by configuration;
- **stdio only, launched by its client — no listening socket, no port, no inbound path**;
- runs as a separate process from the books, holding no GTOS config and no token directory;
- if it dies, nothing about trading changes.

An explicit non-goal: this server must **not** be given a write mode later "for convenience". If a
future need for agent-initiated mutation appears, it goes through
`RealMT5.order_send` and the activation token like everything else, or it does not happen.

### Stage 3 — the command center consumes it

`gtos_command_center.py` gains an optional `--mcp` source that fills the accounts panel from live
tool calls instead of the export, leaving every other panel export-backed and clearly labelled with
its own age. Two freshnesses on one page, each stated — never one blended "as of".

---

## 7. What this does NOT propose

- **No agent with trading authority, at any stage.** Not behind a confirmation prompt, not behind a
  token, not "for closes only". §4 is the reason: it would be a second order path, and the estate's
  entire brake stack is built around there being exactly one.
- **No listening socket on the VPS.** stdio only.
- **No MQL5.community AI provider for GTOS's own use.** It routes account and market context to a
  third party under terms nobody here has read.
- **No replacement of the export ceremony.** §3.

---

## 8. Owner decisions and host reads this raises

| id | question | why it cannot wait on engineering |
|---|---|---|
| **OD-BC-1** | On both live terminals, should AI-initiated trading be **prohibited**, or allowed with manual confirmation? Recommendation: **prohibited**, on the grounds that an unattended VPS cannot confirm. | The setting exists in 6060 and the build is arriving on MetaQuotes' schedule. Deciding after arrival means the default decided it. |
| **OD-BC-2** | Is a terminal build upgrade on an armed, funded host acceptable at all, or should the accounts be flattened and gated first? | Live Update cannot be disabled, so this is a question about a scheduled event, not a proposed one. It interacts with H8: *flatten first, then gate* — never the reverse. |
| **HR-BC-1** | Host read: `terminal_info.build` on both terminals, now. | Five-day-old evidence on a question whose answer changes weekly. |
| **HR-BC-2** | Host read: if either terminal is on 6060+, the current value of the AI-trading permission and of the network/command-line permissions. | The default is undisclosed; it must be observed, not assumed. |

---

## 9. What I got wrong, and what stayed unverified

- **I initially read MQL5 article 21905's 14-tool surface as a description of the terminal's native
  MCP.** It is not — it is a third-party Python server built on the `MetaTrader5` module, with
  opposite security properties (trading on by default, no disable). §2 exists because that
  conflation nearly reached this document's recommendations, and it would have understated the
  native path's controls while overstating the third-party path's.
- **The build-6060 release date is cited two ways by two MetaQuotes-adjacent sources** (23 vs 24
  July). I have not resolved it and it does not matter to any conclusion, so it is reported as a
  range rather than silently picked.
- **The AI-trading permission default is not disclosed anywhere I could find.** Every recommendation
  here is written so that it does not depend on knowing it — which is why HR-BC-2 is a host read
  rather than an assumption.
- **"Live Update cannot be disabled" is [TRANSFERRED], not measured.** It rests on MQL5 forum
  consensus across several threads, not on a test against a terminal. If it is wrong, OD-BC-2 gets
  easier, and nothing else in this document changes.
- **Whether the VPS terminals have already updated is [UNVERIFIED].** This session did not touch the
  VPS, by standing instruction. It is HR-BC-1 and it is one command.
- **`mqid: true` is a measured field; the inference that it satisfies 6060's AI sign-in
  prerequisite is not.** It is stated as a reason to check.

---

## 10. Provenance

| claim | source |
|---|---|
| terminal build 5836, `mqid`, `dlls_allowed`, connected, trade_allowed | `vps-export-20260725/extracted/09_mt5_api/{ftmo,redacted_account}_terminal_info.json` |
| build 6060 ships native MCP; three-state AI-trading permission; separate network/CLI permissions; MQL5.community sign-in | [MetaTrader 5 Build 6060 release notes](https://www.metatrader5.com/en/releasenotes/terminal/2447) · [MQL5 forum 512830](https://www.mql5.com/en/forum/512830) |
| the third-party 14-tool surface, stdio, `config.json` with plaintext credentials, trading on by default | [MQL5 article 21905](https://www.mql5.com/en/articles/21905) · [Qoyyuum/mcp-metatrader5-server](https://github.com/Qoyyuum/mcp-metatrader5-server) · [ariadng/metatrader-mcp-server](https://github.com/ariadng/metatrader-mcp-server) |
| Live Update cannot be disabled | [MQL5 forum 457195](https://www.mql5.com/en/forum/457195) · [MQL5 forum 285411](https://www.mql5.com/en/forum/285411) · [MT5 Help: Live Update](https://www.metatrader5.com/en/terminal/help/start_advanced/autoupdate) |
| the activation choke point runs inside the GTOS process | `src/mt5/mt5_real.py:475-497`, read directly 2026-07-30 |
| the launcher single-record trap | `src/components/ultimate_book/launcher.py:328`, and the measurement in `SESSION_BC_COMMAND_CENTER_RESULT.md` §2 |
| the prototype and its refusal layer | `scripts/gtos_mt5_mcp_readonly.py`, `tests/ultimate_book/test_gtos_mt5_mcp_readonly.py` (24 tests) |
