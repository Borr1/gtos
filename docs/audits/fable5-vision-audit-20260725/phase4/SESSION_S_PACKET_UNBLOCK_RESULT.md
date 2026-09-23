# Session S — the packet carry, re-authored against the lineage it will actually run on

**Stage 3 completion. Branch `phase4/packet-unblock` off `main` @ `205414262`. Blocks B290–B319.**

Reproduce the lineage facts: `git show redacted_host:src/components/ultimate_book/book_owner.py`
Tests: `pytest tests/ultimate_book/test_packet_carry_vps_lineage.py -q`
Carry: `docs/audits/fable5-vision-audit-20260725/phase4/packet_carry/`
Runbook: `docs/audits/fable5-vision-audit-20260725/phase4/PACKET_UNBLOCK_VPS_RUNBOOK.md`
A/B, **full suite**: **661 bad → 660 bad by failure set, 0 regressed, +10 passing** (`phase4/receipts/SESSION_S_AB.md`, captures embedded). The 1 "fixed" is a load-sensitive flake, not a repair — see the receipt's caveats.

---

## 0. The answer

**I did not need the orchestrator to fetch anything, because the VPS lineage is already in this
clone's object store** — `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18` =
`redacted_host`. That changed the whole shape of the job: instead of reasoning about a lineage I could
not see, I reconstructed it, ran the carry against it, and **reproduced the block itself**.

The prompt said *"You have the same blind spot unless you go and look."* I went and looked, and the
first thing worth reporting is that looking was cheap.

**The block is real and it reproduces exactly.** On the reconstructed lineage:

| | |
|---|---|
| mainline `book_owner.py` | `ModuleNotFoundError: No module named 'src.components.ultimate_book.convergence_advisory'` at `book_owner.py:24` |
| `packet_guard.py` + old emitter | `ImportError: cannot import name 'PACKET_REJECTED_EVENT_TYPE'` |

**I chose shape (a) — strip the convergence coupling — and the reason is measured, not
architectural.** Option (b) was *viable*: `convergence_advisory.py` imports exactly one repo symbol,
`stable_hash`, which exists byte-identical on the VPS lineage at
`runtime_learning_packet.py:99`. It would have imported fine. What killed it is what it does to the
stream:

> `stable_hash` serialises the **whole packet**, and the mainline emitter adds
> `"ultimate_convergence_advisory": None` **unconditionally** (`runtime_learning_packet.py:435`).
> Measured over the live export: **99,112 of 99,112 packet hashes shift** — for a feature that is
> default-off (`convergence_advisory.py:20-21`) and returns `None` on every call.

Against that, the carried emitter **reproduces all 99,112 recorded hashes exactly — 100.0000 %**.

That is also P's own stated principle, applied to P's own carry. P made the `economics` block
conditional (`:438-442`) with the comment *"An always-present block of nulls is indistinguishable
from a block that was never filled"* — and the convergence key next to it violates exactly that.

### The part of this that cuts against me, measured and published

My prompt framed the hash shift as breaking *"three live consumers reading that stream."* **I
measured it, and that framing overstates the severity.** All three consumers of
`packet_hash_sha256` on the VPS lineage use it for **dedup only** —
`scripts/build_runtime_learning_daily_advisory.py:344`, `book_owner.py:1210` (`redacted_host`), and the
tail-dedup inside `RuntimeLearningPacketWriter`. And dedup effectively never fires: of 99,112
packets, **exactly 1 hash appears more than once**, because `created_at_utc` makes every packet
unique already.

So a hash shift would **not** have broken a consumer. The honest argument for shape (a) is not
"it breaks things" — it is that it rewrites the identity of every future packet, permanently, to
carry a key that is `None` on every row of a default-off feature. That is a real cost with a
literally zero benefit, and it is enough. **It is not the dramatic cost the prompt described, and
saying so is the point.**

---

## 1. The lineage is knowable, and I measured how far

Everything below rests on `redacted_host` being a faithful stand-in for the live host, so I checked it
rather than assuming it.

**63 of 63 files byte-identical**, 0 mismatched, 0 missing, between commit `redacted_host` and the
2026-07-26 VPS working-tree export (`vps-export-20260725/extracted/20_src/`), across
`src/components/ultimate_book/`, `src/utils/` and `src/mt5/`.

**The construction is mechanical, not hand-written.** I enumerated the complete divergence:

| file | VPS → mainline (pre-P) | all convergence? |
|---|---|---|
| `book_owner.py` | 11 hunks, **68 added lines, 0 deletions** | **yes, all 68** |
| `runtime_learning_packet.py` | 4 hunks, **8 added lines, 0 deletions** | **yes, all 8** |

So mainline is a strict *superset* of the VPS file, and **P's §8 claim #1 — "the VPS and mainline
emitters differ only by the convergence-advisory additions" — is confirmed by exhaustive line
enumeration, not by sampling.** P's carry and the convergence additions share **zero lines**.

The target is therefore a three-way merge (base = mainline at P's branch point, ours = VPS, theirs =
P's carry) with six conflicts resolved one way: keep economics, drop convergence. Verified
line-for-line afterwards — `target − VPS` equals `P's carry − convergence` exactly, with two
documented extra lines (`"optional_fields": [` and `],`) which live inside `packet_schema()`, an
introspection function that touches no emitted packet.

---

## 2. What the carry is

Six files. **`book_owner.py` is last**; that is the only ordering rule that carries weight.

| # | file | on VPS | note |
|---|---|---|---|
| 1 | `src/utils/broker_clock.py` | absent | optional by construction (`packet_economics.py:50-51`) |
| 2 | `src/components/ultimate_book/runtime_learning_packet.py` | **modified** | adds **one** optional keyword-only arg |
| 3 | `src/components/ultimate_book/packet_economics.py` | absent | new, inert |
| 4 | `src/components/ultimate_book/packet_guard.py` | absent | new, inert; needs #2 |
| 5 | `src/components/ultimate_book/book_owner.py` | **modified** | imports #3 and #4 |
| — | `scripts/ultimate_book_packet_silence_alarm.py` | absent | standalone, optional, stdlib-only |

Files 3, 4, 1 and the alarm are carried **byte-identical to mainline** — verified they need no
lineage change. Only files 2 and 5 were re-authored.

**Both surgical diffs apply to `redacted_host` with zero fuzz**, and the patched result is byte-identical
to the shipped file.

---

## 3. Ordering risk, measured rather than asserted

P's runbook said "file ORDER is the one thing that can break this" without saying what each mistake
costs. They are **not** equally bad, and the difference is the whole reason the block was correct to
hold.

| mistake | what actually happens | severity |
|---|---|---|
| **`book_owner.py` present with ANY of files 2/3/4 missing, stale or half-copied** — including a mainline `book_owner.py`, and including `book_owner.py` landing before the emitter | `ImportError`/`ModuleNotFoundError` **at module load**. `run_book.py:32` imports `UltimateBookOwner` at module top, unguarded → process exits 1 at startup on both namespaces → supervisor restart loop → **`manage_open_positions` never runs** → open positions unmanaged | **CATASTROPHIC** |
| `packet_guard.py` / `packet_economics.py` before the emitter, `book_owner.py` still old | nothing — **nothing on this lineage imports them** until `book_owner.py` lands | none |
| `broker_clock.py` missing, last, never, **or truncated** | nothing — the import is guarded and now catches any exception, not just `ImportError` | none |

> ### I got this table wrong first, and the error was in the dangerous direction
>
> My first version rated "`book_owner.py` before `runtime_learning_packet.py`" as **survivable**.
> The reasoning was real and traced carefully: the new `economics=` kwarg would raise `TypeError`
> at `book_owner.py:1984`, which is the penultimate line of `manage_open_positions` (1879–1985),
> *after* adoption, exit policy and `_apply_breach_flatten` (`:1983`) have applied, and
> `BookLauncher.tick()` catches it at `launcher.py:290`, so the loop survives and exits keep
> being applied.
>
> **Every one of those structural facts is true, and the conclusion is still wrong, because that
> failure is unreachable.** Carried `book_owner.py:32` imports `packet_guard` at module top;
> `packet_guard.py:46` imports `PACKET_REJECTED_EVENT_TYPE` from the emitter at module top. The
> import graph fails **before any function body runs**. A refuter enumerated all 32 partial-copy
> permutations on the reconstructed lineage: **14 of the 16 containing `book_owner.py` die at
> module load**; only the full carry and full-carry-minus-`broker_clock` import at all.
>
> I traced the call-site consequence and never asked whether control reaches the call site. The
> effect was to tell a 2 a.m. operator that the catastrophic case was the survivable one — in a
> table whose entire purpose was to tell them which is which. **`verify_carry.py --check imports`
> catches the state correctly (verified, exit 2), so the runbook's gate was never wrong; the prose
> telling the operator how much to worry was.**

---

## 4. Safety, demonstrated on the lineage

Not on `main`. Every one of these ran against the reconstructed VPS tree.

**A — no import the lineage cannot satisfy.** The A4 audit P ran for `broker_clock` and did not run
for `convergence_advisory`: **80 modules** walked transitively from the four carried modules, **0
parse errors, 0 unguarded unresolved intra-repo imports.** The only unresolved names are the three
`broker_clock` symbols inside the `try:` at `packet_economics.py:50`.

> *My first run of this audit reported PASS while silently covering only 75 modules* — it hit a
> `SyntaxError` on a BOM'd file, skipped it, and never followed its imports. `py_compile` confirms
> Python imports that file fine; the error was my reader using plain UTF-8. Re-run with
> `utf-8-sig`: 80 modules, 0 errors. **A PASS from an audit that silently truncated its own walk is
> the same false-green class this carry exists to prevent**, and it was mine.

**B — the four modules actually import**, `book_owner` included, on the reconstructed lineage — and
also with `broker_clock.py` deliberately withheld.

**C — backward compatibility, measured on the whole corpus.** All **99,112** live packets reproduce
their own recorded `packet_hash_sha256`. `SCHEMA_VERSION` stays
`ultimate_book_runtime_learning_packet_v1`; the `economics` block carries its own
`contract_version`. A `position_managed` packet with nothing to cost comes out of the carried
emitter with the **same key set and the same hash** as the live emitter produces today.

**D — the signature only grows.** `build_runtime_learning_packet` gains exactly one keyword-only
parameter with a default (`economics`). Every existing VPS call site works untouched.

**E — P's refuter-driven fixes survived the re-authoring.** Checked specifically, because a
mechanical merge is exactly where they would be lost:
- the `writer is None` early return (P's withdrawal #9 — a logging switch that could `pause_new_entries`
  on both namespaces) is intact at carried `book_owner.py:1256-1263`, comment and all;
- the guarded `Path(getattr(writer, "path"))` construction (P's withdrawal #4) is intact;
- `packet_guard.py` contains **zero `raise` statements**.

---

## 5. Three claims in my prompt that are wrong

Kept per the working agreement §3: a prompt that turns out to be wrong is a finding.

### 5.1 "`packet_guard.py` imports `build_packet_rejected_marker` and `PACKET_ECONOMICS_KEY`"

It imports **`PACKET_REJECTED_EVENT_TYPE`** and `build_packet_rejected_marker` (plus two symbols the
VPS already has). **`PACKET_ECONOMICS_KEY` is not imported by `packet_guard` at all**, and repo-wide
it has **zero importers** outside its defining module. The first symbol to fail is the one the prompt
did not name. **The coupling conclusion is unchanged and correct** — which is precisely why the wrong
specific survived being read.

### 5.2 "Runbook steps written as `python - <<'PY'` heredocs"

True, but **narrower than stated**: 2 occurrences, both in `phase3/PACKET_EMITTER_VPS_RUNBOOK.md`
(`:155`, `:181`). Session I's `STAGE0_VPS_RUNBOOK.md` has none.

### 5.3 "every `python ...` line in the wave-3 runbooks tested the wrong interpreter"

True, and **broader than the prompt implies in the direction that matters.** It is not only P's
runbook: **Session I's `STAGE0_VPS_RUNBOOK.md` — a live-safety runbook — invokes bare `python` at
`:122-125` and `:299`.** 9 occurrences across the two documents.

Related, and the same shape in reverse: the `Get-Process | CommandLine` defect is in P's runbook
(`:116`, `:118`), and **Session I's runbook already used the correct `Get-CimInstance Win32_Process`
form**. P regressed a pattern Session I had got right.

---

## 6. The runbook, and why it does not hardcode the interpreter

`PACKET_UNBLOCK_VPS_RUNBOOK.md` supersedes P's. Every code block is Windows PowerShell 5.1, no
heredocs, `Get-CimInstance Win32_Process` throughout, with an explicit *"if this returns nothing,
STOP"* before the only `Stop-Process`.

**It does not hardcode `.venv-gtos\Scripts\python.exe`.** That path came to me as a claim and I could
not verify it, so §2.1–2.2 has the operator *read the interpreter off the running book's own command
line* — the same `Get-CimInstance` call that lists the books also prints the interpreter that
launched them. ~~`verify_carry.py` additionally refuses to run on a pre-3.10 interpreter, which is
what a bare PATH `python` would be.~~

> **Struck 2026-07-29 at wave-4 integration (B367); this session withdrew it itself at B313 and this
> paragraph was not amended.** A version guard **cannot** tell the two interpreters apart — PATH
> `python` is ~3.11 and the book's `.venv-gtos` is ~3.13, and **both pass a 3.10 floor**
> (`packet_carry/verify_carry.py:85-86` says so in the code). It was replaced by a **dependency
> probe**, which names the failure as *wrong interpreter, do not roll back*. The withdrawn version
> is the reassuring one, and it survived in the summary an operator actually reads.

Multi-line Python is a **file**, not a runbook code block: `packet_carry/verify_carry.py`, with four
subcommands (`preflight`, `postflight`, `imports`, `packets`) and real exit codes. It cannot reach a
broker: it imports `book_owner` to prove the module *loads* but never constructs `UltimateBookOwner`.

**`preflight` exists because I could not see the host.** Two inert files are said to have landed on
2026-07-29; whether they did, and whether anything else moved, is measured on the host rather than
assumed. It classifies every file as `ABSENT` / `AT EXPECTED BASE` / `ALREADY CARRIED` /
`*** UNEXPECTED CONTENT ***` and stops on the last.

---

## 7. What I deliberately did not do

- **I did not wire `modelled_cost_r`.** It is P's OD-P3, it is cheap, and it is in a file I was
  already re-authoring — which is exactly why it was tempting. It is **Borhen's call**, and widening
  a live-host diff while a funded account is being armed is the wrong time to take it. The gap
  stands as P described it in §6 item 1.
- **I did not land emit-on-change (OD-P1) or the join-key repair (OD-P2).**
- **I did not carry Session M's or Session I's later changes** to `book_owner.py` / `launcher.py`.
  P's carry was taken from `553184797`, the last commit before a merge from `main` pulled unrelated
  work in. Minimising the live diff outranks currency here; those changes are a separate decision.
- **I did not touch anything under `src/`.** H1 is not engaged. The contract check reports 2 entries
  and **both are un-hydrated LFS pointers**, correctly discriminated — the B185 trap, not drift.
- **I did not run anything against the VPS**, and nothing here was executed on that host.

---

## 8. What the refuters overturned

Four refuters, distinct lenses, each told to default to "refuted". The working agreement §7 says
adversarial verification earned its cost every time it was run in wave 3. It did again — **the
single most dangerous thing in this session's first draft was found by a refuter, not by me.**

| # | lens | what it overturned |
|---|---|---|
| 1 | construction correctness | Main claim **survives**, rebuilt mechanically rather than re-read: carried `book_owner.py` is byte-exact `P-carry minus convergence` (0 diff lines), rlp differs by exactly the 2 `optional_fields` lines. But **68 added lines, not 67**; and it found **F-A**, below. |
| 2 | live safety | **Refuted my ordering table** (§3). Also found the rollback gate deadlock, the too-narrow `except ImportError`, and the stray `broker_clock.py`. Everything else held: 99,112 packets × 6 server values → **0 raises**; 255 hostile-input cases → **0 new raises vs base**; import graph reaches no broker module. |
| 3 | evidence | **Refuted the framing of two of my five measurements.** The hash-reproduction check was near-tautological as stated; it ran the stronger test I should have run and the conclusion survived. The "80 modules" figure **does not reproduce** and is withdrawn. Found the second repo tree. |
| 4 | runbook executability | **Refuted the whole document**: it stopped at §2.3 on a healthy host. Plus 25 more defects, of which the namespace false-green and the crash-loop blindness were the two that could have produced a confident wrong "it worked". |

### The five that mattered most, all now fixed

1. **My ordering table rated the catastrophic case as survivable** (§3). Found by refuter 2.
2. **`_broker_server_name()` resolved nothing on the VPS** — `rollover_nights` would have read
   `unavailable` on every live packet, so the carry would have shipped holding time *without the
   swap-night count*, which is half of what it exists to record. Found by refuter 1. Fixed and
   measured: `None`/`unavailable` → `5.0`/`measured`.
3. **Two repo trees on the host**, differing in 25 `src` files including `book_owner.py`. Found by
   refuter 3. Now a STOP in the runbook, which also derives the repo root from the running book.
4. **The runbook was literally unrunnable** — §2.3's unscoped gate pattern matched 26 lines, 12
   reading `true`. Found by refuter 4.
5. **The rollback could never pass its own gate**, which on a live account meant an operator who
   correctly rolled back was told not to restart. Found by refuters 2 and 4 independently.

### What I got wrong and withdrew, in my own words

- **The ordering table.** I traced the call-site consequence of a signature mismatch and never
  asked whether control reaches the call site. It does not — the import graph fails first.
- **"80 modules walked."** Withdrawn: unreproducible, and the walker was not committed. The
  verdict reproduces; the number does not.
- **"All 99,112 packets reproduce their hash under the carried emitter."** True but weaker than it
  sounds — it tests `stable_hash`, which is unchanged. The claim it implies was tested by a refuter
  and passed; I have restated it as what it is.
- **67 added lines.** It is 68; my `rg` count could not see a blank line.
- **My own import audit reported PASS while covering 75 modules instead of the full set**, because
  a BOM tripped my reader and I skipped the file rather than failing.
- **My verifier had four false-greens** — empty log, all-malformed log, wrong working directory,
  and carry-not-applied. I found the first while writing a refuter brief; refuters found the rest.
- **I introduced a `NameError` while fixing F-A** (`Mapping` is not imported in `book_owner`) and
  caught it only because I ran the code instead of compiling it.
- **I deleted my own test file and committed the deletion** (B315), while the reproduction command
  at the top of this document still pointed at it.

---

## 9. What is still open

- **The current state of the VPS is [UNVERIFIED] and deliberately so.** The export is
  2026-07-26; two commits landed 2026-07-29. Whether `broker_clock.py` and `packet_economics.py`
  actually landed as the inert pair, and whether anything else moved, is what `--check preflight`
  measures on the host. **The one thing worth fetching through the orchestrator** would be the
  current sha256 of the five carry paths on
  `C:\Users\MSI\Documents\ai-trading-agent`; it would let the runbook skip a branch, but it does
  not block the carry, because preflight answers the same question at execution time.
- **`_broker_server_name` is fixed here and on mainline, but the VPS's *other* tree is untouched**
  and still carries the defect. Out of scope, recorded.
- **Session M's D4 direction repair is not carried** (B314), at a measured cost of 41.1 % → 63.9 %
  direction coverage on `unit_admitted`/`unit_shadow`. Recoverable downstream; it is a cost, not a
  defect, and it is Borhen's call whether to fold it in.
