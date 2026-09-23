# CF ceremony — the rename watchdog

**Read this line first: there is no ceremony to perform on the books.**

The repair Session CF was commissioned to build turned out to already exist in the file it would
have been added to. FTMO did not rename anything on 2026-07-31; the probe that reported it compared
GTOS **canonical** names against FTMO's tree, and FTMO has never used those as broker names. The
live profile already maps all five across, and every target was in FTMO's tree six days earlier.
Full evidence: `phase15/SESSION_CF_SYMBOL_RENAME_RESULT.md` §0, receipt
`phase15/receipts/CF_SYMBOL_RESOLUTION_V1.json`.

So this page transfers **code and tests only**:

- **no `config/agent_config.yaml` byte moves**
- **no `config/profiles/*.yaml` byte moves**
- **the activation-token digest is unchanged** — no re-mint, on either account
- **no `run_book.py` worker needs restarting** for the watchdog to be useful
- **nothing is armed, disarmed, resized or flattened**

The token re-mint due before 2026-08-05 still stands on its own schedule. **It does not ride this
change, and this change must not be used as a reason to bring it forward.**

---

## 1. The transfer set

Nothing here runs inside a book. The watchdog is read by
`scripts/gtos_command_center.py`, which is an operator page run on the research laptop against an
export — it holds no broker connection and no authority.

| file | status | R2-bound? |
|---|---|---|
| `src/components/ultimate_book/symbol_resolution_watch.py` | **new** | no |
| `scripts/gtos_command_center.py` | modified (panel 6 + two `Export` accessors + one constant) | no |
| `tests/ultimate_book/test_symbol_resolution_watch.py` | **new**, 17 tests | no |
| `tests/ultimate_book/test_symbol_rename_adoption_gap.py` | **new**, 3 tests | no |
| `docs/.../phase15/receipts/BROKER_SYMBOL_TREE_20260725.json` | **new** (fixture + broker-truth baseline) | no |
| `docs/.../phase15/receipts/CF_SYMBOL_RESOLUTION_V1.json` | **new** (evidence) | no |
| `docs/.../phase15/receipts/cf_resolution_probe.py` | **new** (regenerates the two above) | no |
| `docs/.../phase15/receipts/cf_revendor_symbol_tree_probe.py` | **new** (§3, for you) | no |

H1/R2 membership checked on every path, after `git lfs checkout` per the LFS caveat. Drift count
**1 before, 1 after** — the documented B905 standing hazard, unmoved.

**VPS carry: not required.** The book gains no code from this session. If a later carry ceremony is
run for other reasons, none of these files belong in it — the watchdog runs *on the export*, not on
the host, deliberately: an operator check that runs inside the thing it is checking is not a check.

---

## 2. Verifying the transfer (research laptop, ~40 s)

```bash
python3 -m pytest tests/ultimate_book/test_symbol_resolution_watch.py \
                  tests/ultimate_book/test_symbol_rename_adoption_gap.py \
                  tests/ultimate_book/test_gtos_command_center.py -q
# expect: 59 passed

python3 scripts/gtos_command_center.py \
    --export-root /Users/borr/GTOSActive/vps-export-20260725 \
    --now-utc 2026-07-31T14:00:00Z -o /tmp/cc.md
```

**PROVING lines — panel 6 on the 2026-07-25 export:**

```
| account        | state    | resolved OK | broker tree | unresolvable | armed |
| **FTMO**       | ✅ CLEAN |         135 |         167 |            0 |     0 |
| **redacted_account** | ✅ CLEAN |         104 |          76 |            0 |     0 |
```

Both CLEAN, both **0 unresolvable** — that is the whole finding rendered on the operator page.
Panel 6 also states the profile it used and whether it came from the **export** (host truth) or
this repo (a claim about the host). On this export it reads `export` for both accounts.

**What a real rename looks like on the same page** — pinned by
`test_synthetic_tree_diff_reproduces_the_rename_the_event_CLAIMED_and_fires`, which applies exactly
the `.cash`→bare change the event described to the vendored FTMO tree:

```
| **FTMO** | ⛔ STOP | … | 3 armed
  | sleeve             | canonical | resolves to  | armed   | broker offers instead |
  | sub_xvol_pullback  | SPX500    | US500.cash   | **YES** | US500                 |
```

STOP, the sleeve named, the member named, and a suggestion of what the broker now offers. Within
one cycle of running the page against a fresh export.

---

## 3. The one thing asked of the orchestrator (read-only, at your convenience)

Refresh the vendored broker truth. `BROKER_SYMBOL_SPEC_COMPARISON.json` (2026-07-26) is **absent
from this tree**, not merely stale — its `research/operations/vps_broker_truth_2026_07_26/` path
does not exist at HEAD; the file survives in git history at `1b52e4b6b` and its data survives in
the export. Treat it as superseded by `BROKER_SYMBOL_TREE_20260725.json` plus this probe's output.

`phase15/receipts/cf_revendor_symbol_tree_probe.py` — **CF wrote it and did not run it.** Three
read-only MT5 calls (`initialize`, `symbols_get`, `terminal_info`/`account_info`), nothing else; it
asserts at run time that its own source contains no `order_send`, `order_check`, `order_calc_*`,
`positions_close`, `Buy`/`Sell`, and it never calls `symbol_select` — selecting a symbol mutates
Market Watch, which is a visible state change on an armed host, and `symbols_get()` needs no
selection.

```powershell
# per terminal, against the ALREADY-RUNNING instance — no login, no credentials in the file
python cf_revendor_symbol_tree_probe.py --terminal "C:\MT5\FTMO\terminal64.exe" `
    --account FTMO --out ftmo_symbol_tree.json
python cf_revendor_symbol_tree_probe.py --terminal "C:\MT5\redacted_account\terminal64.exe" `
    --account redacted_account --out redacted_account_symbol_tree.json
```

Copy both back, then on the laptop:

```bash
python3 docs/audits/.../phase15/receipts/cf_revendor_symbol_tree_probe.py \
  --merge ftmo_symbol_tree.json redacted_account_symbol_tree.json \
  --out docs/audits/.../phase15/receipts/BROKER_SYMBOL_TREE_20260731.json
```

Same schema, so panel 6 and the tests read it unchanged. **If it comes back with any
`unresolvable`, do not edit a profile on the spot** — that is a token-bound edit and therefore
Borhen's ceremony. Bring the panel output; §4 is the sequence.

---

## 4. If a rename ever IS real — the sequence, held in reserve

Not needed today. Written down so it is not improvised at 3 a.m.

1. **Confirm from the broker, not from a page.** Re-run §3's probe. A rename is two facts: the old
   name is gone *and* a plausible successor is present. `rename_candidates` in the panel proposes
   successors; it never applies one.
2. **Check for open positions on the affected members first.** A position opened under the old name
   is **not adopted and not exit-managed** after the rename (F-CF-4) — it keeps only the
   broker-side SL/TP set at entry, and loses its time stop, scale-outs, trail/BE and the governor
   breach-flatten. It *will* raise `out_of_universe` in the book's own log and an operator card.
   **Deal with those positions before touching config.** Per H8, flatten first, confirm flat, then
   change anything — never shut the gate first.
3. **The edit is one line per member** in the affected account's profile:
   `instruments.<CANONICAL>.market.mt5_symbol: <new broker name>`. Canonical names never change —
   the registry, the bar archive and every sealed replay export key on them, and renaming those
   would break seals (H1/H4) for no gain.
4. **Re-mint the token.** The profile is token-bound; one byte changes the digest and the book
   refuses to place. `python scripts/gtos_activation_token.py …` for that profile.
5. **Restart the affected worker**, and re-check `--tags` on the command line — not the `.ps1` on
   disk. Restarting mid-day inherits that day's wider `firing_sleeves.json` conviction count
   (+25.2 % on every unit under the half-Kelly bins), so **restart at a decision-day boundary** or
   delete that namespace's `firing_sleeves.json` first.
6. **PROVE it**, then release: panel 6 CLEAN with 0 unresolvable on the fresh export, and the
   affected members appearing in a launcher cycle record for their decision timeframe.
7. **Rollback** is the same edit reversed plus a re-mint — and the position check in step 2 applies
   in reverse too.

---

## 5. redacted_account

**Unaffected today, and structurally unaffected by this class of event.** Its profile maps the same
canonical names to its own bare broker names (`SPX500→SPX500`, `GER40→GER30`, `NAS100→NDX100`) and
its tree carries them; the 2026-07-25 export shows it holding no `.cash` symbol at all. It is the
control that proves the FTMO reading was a name-space error rather than a broker change.

The watchdog covers redacted_account from day one on identical terms. Its **33 profile-unsupported slots**
— the crosses and softs FN does not offer, including 7 on armed sleeves (`crypto`/`DASHUSD`,
`sub_xvol_pullback`/`CORN_c`, `COTTON_c`, `XAUEUR`, `XAGEUR`, `XAUAUD`, `XAGAUD`) — are reported as
the standing configuration fact they are, in their own column, **never as a rename alarm**. The
engine already counts them as `profile_missing_instrument_config` (`book_engine.py:526-541`); panel
6 agrees with the engine rather than inventing a second opinion.
