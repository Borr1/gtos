# AZ-1 — the carry set, enumerated by diff

**Session AZ, wave 13, B1850–B1858.** Read this before `MX_ACTIVATION_CEREMONY.md`; the
ceremony implements it and `ORDERING_AND_PARTIAL_STATES.md` orders it.

The question is not "which files did wave 11 and 12 touch". It is **"what does THIS host run
today, and what is the smallest change to it that makes the estate's one standing admission
runnable"**. Those give different answers, and the difference is the whole document.

---

## 0. The three findings, in order of how much they matter

**1. `execution.py` must NOT be carried, and the commission's premise about it is inverted.**
The commission says the package *"must also carry AS's `execution.py` adopt-path fix — it is a
live-crash fix independent of the activation"*. Measured against the host's own bytes, Session
AS's `KeyError('trigger_r')` is **real on mainline and unreachable on this host**: the host's
`execution.py` carries an explicit `if selected_policy == "time_stop":` branch that sets
`trigger_r = 0.0` and guards `final_target_r`, from lineage commit **`b36d9ab92`** ("Fix
targetless time-stop rehydration after restart") — **an ancestor of `redacted_host` and not of
`main`.** Driving the host's own `hydrate_vnext_dynamic_policy_from_record` on an armed
`time_stop` sleeve returns `hydrated: True` today. Carrying mainline's replacement would fix
nothing and would move two live values on every adopted position of four armed sleeves. §3.

**2. `run_book.py`'s host bytes are pinned by no artifact, and the fix is a variant table, not
a guess.** The Stage-0 token ceremony (`phase3/TOKEN_CARRY.md`) recorded **line counts and no
sha256**. But the host's state is *bounded*: its `book_owner.__init__` accepts neither
`recover_pre_gap_bar` nor `vol_level_tilt`, so any `run_book` from Session AI onward would
raise `TypeError` at startup on both namespaces — and both books are alive. That leaves exactly
**four** committed versions. The package ships a payload for each, with its own before/after
sha256; `verify_carry.py --check preflight` reads the host's actual sha256 and names the one to
copy, and an unrecognised sha256 is a **STOP with the bytes printed**. §4.

**3. A launch-time crash was found in mainline and fixed here (B1852).** `run_book.py`'s
frontier banner rendered `float(_o["final_target_r"])` unconditionally, and **six of the eight
wired frontier sleeves carry no such key** — they are `time_stop_*` cells. So
`--frontier-exits vol_compression` (or any of the five `mx_*` short horizons) raised
`KeyError('final_target_r')` **at launch, after `parse_frontier_exits` had already accepted the
name**: the worker dies before `BookLauncher`, the supervisor restarts a missing book forever,
and `manage_open_positions` never runs on either namespace. The two that work are `mx_btcusd`
and `sub_xvol_pullback`, which is why AU's 43 tests did not see it. Rendering now lives in
`execution_packets.describe_frontier_contract`, and the invariant pinned is the one that
matters: **what validation accepts, the next line can render.** §5.

---

## 1. What the host is

`origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18` @ **`redacted_host`**, plus three
executed carries, plus host-branch commits that touch config and the supervisor only:

| what | evidence |
|---|---|
| Stage-0 token carry — 5 files incl. `run_book.py` | `phase3/TOKEN_CARRY.md`; **line counts, no sha256** |
| Session S packet carry — 5 files incl. `book_owner.py` | `phase4/packet_carry/MANIFEST.json`, after-bytes **verified on the running host 2026-07-30** |
| Session AC activation carry — 5 files incl. `execution.py`, `book_engine.py` | `phase5/activation_carry/MANIFEST.json`, same verification |
| host commits `118071eaa` → `eb7c28516` → `f855250cd` → `7017c6745` | arming, FN arming, 5-sleeve expansion, `fx_jpy` pull — `config/agent_config.yaml`, `config/profiles/redacted_account.yaml`, `scripts/run_book_supervisor.ps1` |

So for every path this carry touches, "the host's bytes" is a **committed artifact**, except
`run_book.py`. The reconstruction used throughout is
`receipts/az_carry_probe.py::materialise`, and it is the tree every measurement below was taken
on.

---

## 2. The four carried files

| # | destination | host bytes today | after | shape |
|---|---|---|---|---|
| 1 | `src\components\ultimate_book\execution_packets.py` | lineage `e533f162d` (20,349 B) | 38,376 B | **mainline whole** |
| 2 | `src\components\ultimate_book\order_router.py` | lineage `af2e696c1` (5,094 B) | 5,916 B | **mainline whole** |
| 3 | `src\components\ultimate_book\book_owner.py` | Session S payload `2b9aab7b…` (224,757 B) | 226,002 B | **host file + 4 anchored edits** |
| 4 | `run_book.py` | one of four (§4) | variant | **host file + 2 anchored edits** |

Exact sha256s are in `MANIFEST.json`; unified diffs against the **host's** bytes (not
mainline's) are in `diffs/`.

### 2.1 Why two files carry whole and two do not

A whole-file copy is safe only when the file's diff against the host is exactly the change
being carried **and** its import closure is already satisfied there. Both hold for files 1
and 2 and for nothing else:

* `execution_packets.py` — diff against the lineage is **exactly** AQ's time-stop unit repair
  (B1404), AU's frontier registry (B1550) and AZ's banner renderer (B1852). Its import header
  is **byte-identical** to the lineage's, so it adds no edge to the host's module graph.
  Pinned by `test_the_two_whole_file_payloads_import_only_what_the_lineage_already_imports`.
* `order_router.py` — 14 lines of diff, both hunks AU's, same import header. It **must** land
  after file 1: carried alone it produces a *silent total placement outage* rather than a crash,
  because `place()` catches its own `TypeError` and returns `placed: False,
  reason: router_exception:…` on every unit while the heartbeat stays healthy
  (`ORDERING_AND_PARTIAL_STATES.md` §1).
* `book_owner.py` — mainline is **~330 lines** of diff and four thousand lines longer, carrying
  wave 5–12 work whose closure this host does not have. Four anchored edits instead: the
  `frontier_exits` kwarg, the instance field, the router construction, the adopt-rehydration
  call. That is the *whole* of AU's threading through this file.
* `run_book.py` — §4.

### 2.2 Every mainline change riding along in a carried file, named and classified

`execution_packets.py` is the only carried whole file with more than one change in it. Against
the host's bytes it carries three, and the blast radius of all three together was **measured**
over every sleeve the host's registry resolves (`receipts/AZ_CARRY_PROBE_V1.json` →
`blast_radius`; 34 sleeves compared, exit profile + adopt instrumentation + full placement dict
each):

| change | classification | measured blast radius |
|---|---|---|
| **AQ's time-stop unit repair** (`96` → `time_stop_m15(80,"D1")` = 7680) | **NEEDED for the activation** — the admission's own cell is measured at the 80-D1-bar horizon, and at 96 it REJECTS at all four cost bands (AQ §0.3) | exactly the **14** `mx_*` sleeves, on exactly **one** field (`time_stop_bars` and its two derived copies). **No armed sleeve moves.** Registry size 32 → 32. |
| **AU's `FRONTIER_EXIT_OVERRIDES` + `resolve_exit_profile`** | **NEEDED** — it is the activation | **zero** with no selection: `resolve_exit_profile(s)` returns the committed object *itself* for every sleeve. Under `frontier_exits=(mx_btcusd,)` the placement of all four armed sleeves is identical key-for-key. |
| **AZ's `describe_frontier_contract`** (B1852) | **HARMLESS + repairs a launch crash** | a new pure function; no caller on the host until `run_book.py` lands |
| AU's six `time_stop_*` overrides for other `mx_*` sleeves | **HARMLESS** — default-off entries in a map, none on an armed sleeve, every cell REJECTs at the ratified rule (AU §3) | none unless named on the launcher line |
| `sub_xvol_pullback @ target_4R` | **HARMLESS AS CARRIED, MUST NOT BE SELECTED** — the sleeve is ARMED at 3R and its 4R cell **REJECTS at all four cost bands** at the ratified rule, p 0.0080 against a 0.002083 bar (AU §1.3; AS §0.3 independently). The committed 3R is untouched and asserted so. | none unless named |

`order_router.py` and `book_owner.py` carry AU's hunks and nothing else, by construction —
`order_router` because its whole diff is those hunks, `book_owner` because the payload is the
host's own bytes with four named replacements.

---

## 3. Why `execution.py` is NOT carried

### 3.1 The two files, side by side

`hydrate_vnext_dynamic_policy_from_record`, the adopt-rehydration path
(`book_owner._rehydrate_policy` → `hyd(rec)`, called with **no try/except** when
`_live_broker_authority()` is true, which it is on both accounts):

```
HOST (execution.py @ Session AC payload)      MAINLINE (after Session AS's B1535 fix)
------------------------------------------    ---------------------------------------
if selected_policy == "time_stop":            trigger_r = params.get("trigger_r")
    trigger_r = 0.0                           if trigger_r is None:
    final_target_r = float(                       trigger_r = payload.get(
        params.get("final_target_r") or 0.0)          "gtos_vnext_dynamic_be_trigger_r")
else:                                         if trigger_r in (None, ""):
    trigger_r = float(params["trigger_r"])        trigger_r = params.get("final_target_r") or 0.0
    final_target_r = float(                   trade.…be_trigger_r = float(trigger_r)
        params["final_target_r"])             trade.…final_target_r = float(
                                                  params["final_target_r"])

take_profit_1 = 0.0 if selected_policy        take_profit_1 = 0.0 if no_broker_tp and
    == "time_stop" else …be_trigger_price         selected_policy == "time_stop" else …
```

The host's branch came from **`b36d9ab92`**, which `git merge-base --is-ancestor` places inside
`redacted_host` and outside `main`. It is a **live-lineage-only fix** — the two-stacks fork the
Fable audit named, showing up in the one function this activation's adopt path runs through.

### 3.2 What carrying it would do, measured

`receipts/az_carry_probe.py --stage as-control` applies mainline's hunk to the host's own
`execution.py` as an anchored edit and re-runs the adopt probe. Nothing was inferred:

| adopt-missing-record on | host today | with mainline's hunk carried |
|---|---|---|
| **`crypto`** (ARMED, `time_stop`) | `hydrated ✓  be_trigger_r 0.0  take_profit_1 0.0` | `hydrated ✓  be_trigger_r 4.0  take_profit_1 3040.0` |
| `mx_btcusd`, committed 2R | `be_trigger_r 0.0  take_profit_1 0.0` | `be_trigger_r 2.0  take_profit_1 3020.0` |
| `mx_btcusd` + the 5R selection | `be_trigger_r 0.0  take_profit_1 0.0` | `be_trigger_r 5.0  take_profit_1 3050.0` |

**Three of three probes move and none of them raised beforehand.** `take_profit_1` going from
`0.0` to a price on an adopted position of an armed sleeve is a live behaviour change, on the
path AS's own handoff already flagged (*"the fix makes the adopt path reach the broker-TP
modification it previously crashed before … a behaviour change on live money"*) — except that
on this host it never crashed, so the change buys nothing.

### 3.3 What this does not say

AS's finding is **not wrong**; it is right about mainline, and mainline is where the ten
package-admission tests and every laptop-side harness run. It is filed here as a
**host-inapplicable** repair rather than a closed one, and the mainline fix stays exactly where
it is. What changes is that no ceremony should carry it to this host without first
re-measuring §3.2, and `test_the_host_execution_py_cannot_raise_the_KeyError_AS_fixed` fails
loudly if the host's branch ever stops being there.

`FXJPY_PULL_20260730.md` §"Ceremony discipline" reads *"AS's adopt-path `KeyError('trigger_r')`
fix is not yet carried to the host, so a restart must only happen with zero open positions
until it is."* The premise is false and **the conclusion is still the right operating rule** —
for a different reason, given in the ceremony page §4.

### 3.4 And the part of `execution.py` the activation depends on is already identical

AQ's repaired `7680` is consumed by `ExecutionEngine._trading_m15_bars_since`, which is
**byte-identical** between the host's copy and mainline's (pinned by
`test_the_time_stop_engine_the_carry_relies_on_is_identical_on_the_host`). The host's
`check_time_stop_and_close` is a **superset** — same decision logic, plus a time-stop clock
diagnostic layer mainline never received. So the repair means on the host exactly what AQ's
receipt says it means, with no carry at all.

---

## 4. `run_book.py` — the file no artifact pins

### 4.1 What is known

The host's `run_book.py` is **not** the lineage's: the books log
`activation context declared (namespace=…, config_digest=…, token_dir=…)`, and mainline's
`run_book.py` is the **only** site in the tree that emits `config_digest=`
(`phase8/receipts/VPS_CEREMONY_COMPLETED.md` quotes it, FTMO `ffe16657feaf`, FN
`e184a81d3b1b`). That block was added by `7c85c3105` and carried by Stage 0.

### 4.2 What bounds it

The host's `book_owner.__init__` — the Session S payload, verified on the running host — is:

```python
def __init__(self, base_config, mt5, repo_root, namespace="operator_profile",
             engine_factory=None):
```

No `recover_pre_gap_bar`, no `vol_level_tilt`. So a `run_book.py` from Session AI (21,143 B) or
later would raise `TypeError` at startup **on both namespaces**, and both books are alive. Over
the whole of `run_book.py`'s git history, the versions that construct the owner with
`namespace=` alone **and** declare the activation context are exactly four:

| sha256 | bytes | commit | what it is | payload |
|---|---:|---|---|---|
| `262014f24dee…` | 18,032 | `7c85c3105` | Phase 0 item 4 — the token invert (the Stage-0 branch's own state) | `files/run_book.variant_262014f24dee.py` |
| `a850baf45cab…` | 18,700 | `637e2e094` | Session M — F30/Q7 notification authorization | `files/run_book.variant_a850baf45cab.py` |
| `96ac1b566dc8…` | 19,218 | `52aa3fb34` | Session I safety spine | `files/run_book.variant_96ac1b566dc8.py` |
| **`014ce9df03fa…`** | **19,886** | `dcb54cbab` | **wave-3 integration (I+M merged) — the most likely state; CLAUDE.md records `run_book.py` at 19,886 B at that HEAD** | **`files/run_book.py`** (primary) |

The derivation is re-run in the suite
(`test_the_variant_table_is_exactly_the_owner_compatible_versions`), so a new committed version
cannot silently make the table wrong in either direction.

### 4.3 What the operator does

`--check preflight` prints the host's sha256 and **names the payload**. An unrecognised sha256
is a `FAIL` that says, in the output: *do not copy the primary payload over it — that payload
is built from a different base and would silently revert whatever this host has*, and prints
the bytes to send back. Building a fifth variant from a returned sha256 is one edit to
`RUN_BOOK_VARIANTS` in `build_carry.py` and one rebuild.

### 4.4 The two edits

Both are pure additions, applied at anchors that are unique in all four bases:

1. after `p.add_argument("--once", …)` — the `--frontier-exits` argument;
2. replacing `owner = UltimateBookOwner(merged, mt5, ".", namespace=args.namespace)` — the
   launch-time `parse_frontier_exits` validation (exit `4`, this file's existing "refusing to
   start" code), the `frontier_exits=` kwarg, and the banner.

Deliberately **not** carried from mainline: `--recover-pre-gap-bar` and `--vol-level-tilt`,
whose kwargs the host's owner rejects. Pinned by
`test_every_variant_payload_carries_the_flag_and_only_the_flag`.

---

## 5. The launch crash this session found and fixed (B1852)

```
$ --frontier-exits vol_compression
  parse_frontier_exits  -> accepted ("vol_compression" IS wired)
  banner                -> KeyError('final_target_r')
  worker                -> dead, before BookLauncher, on both namespaces
```

Six of the eight wired sleeves are `time_stop_*` cells carrying `time_stop_bars` and no
`final_target_r`. The repair is `execution_packets.describe_frontier_contract(sleeve)`, which
renders whichever contract keys the override has and returns `"contract override"` for a future
kind that has neither. Three tests pin it, and the one that matters is not the instance but the
invariant: **`parse_frontier_exits` accepts exactly the set the banner can render.**

It is fixed on mainline as well as in the carried payload, because mainline is where the next
session will read it.

---

## 6. What this carry does NOT touch, and why

| path | why not |
|---|---|
| `config/agent_config.yaml` | hashed into the live activation token's config digest — one byte and the armed book stops placing until the token is re-minted. **Nothing needs it**: `mx_btcusd_d1_donchian_20_breakout` is ALREADY in the host's effective registry (`ultimate_book_include_market_expansion_book: true` + policy `positive_weighted12_after_swap` → 12 sleeves, and `mx_btcusd` is one of them). Driving the host's OWN `book_engine._active_sleeve_names()` with the host's own config values returns **32 sleeves including `mx_btcusd`**. |
| `config/profiles/redacted_account.yaml` | same, and redacted_account is out of scope for this activation |
| `src/components/execution.py` | §3 |
| `src/components/ultimate_book/book_engine.py`, `governor_state.py`, `admission.py`, `sleeves/*` | unchanged by this activation; the host's copies already resolve the sleeve |
| the activation token, `src/safety/activation_token.py`, `src/mt5/mt5_real.py` | the token binds a *config* digest, not source; carrying `activation_token.py` could change how that digest is computed and fail-close the armed book |

---

## 7. Seal exposure

All four carried paths are **unbound** by every mechanism, re-checked this session:

| mechanism | result |
|---|---|
| R2 `input_bindings` (43 paths) | none of the four |
| R1 `input_bindings` (44 paths) | none |
| `code_authority_paths` (21, `replay_acceleration_attempt5_typed_sparse_runner.py`) | none |
| `config_file_hashes` → `shared_execution_contract_digest_sha256` | no config file is touched |

H1/R2 drift: **2 `UNHYDRATED-LFS` at session start and 2 at session end** — unchanged.
