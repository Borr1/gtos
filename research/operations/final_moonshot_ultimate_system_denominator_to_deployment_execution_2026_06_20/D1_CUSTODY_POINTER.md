# Custody pointer — `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`

**If that file's sha256 does not match what a decision contract expects, read this before doing
anything.** You have almost certainly not found a bug.

**Custody of record:**
`docs/audits/fable5-vision-audit-20260725/receipts/D1_SLEEVE_REGISTRY_CUSTODY.json` (data)
and `…/D1_SLEEVE_REGISTRY_CUSTODY.md` (prose).
Enforced by `tests/test_d1_sleeve_registry_custody.py`.

## The short version

Two byte-distinct versions of this 205,754-byte / 82-row payload exist:

| sha256 | `generated_utc` | Who wants it |
|---|---|---|
| `19365f603bc06eb0…9d2998fa` | `2026-07-16T11:09:40Z` | **R1, R2, the selection-sizing contract, and `VERIFICATION_RESULT.json`** |
| `a5bcc0f81941a123…8588b54e` | `2026-07-13T01:27:31Z` | HEAD's LFS pointer — so this is what a fresh checkout hydrates |

They differ in **2 of 55 fields** — `generated_utc` and its derived `row_hash_sha256` — in all 82 rows.
The other 53 fields are identical in all 82 rows; the decision-bearing content digests identically
(`477aad6c…`). The H1 drift on this path is a **regeneration timestamp, not economic drift**. A
*second* drifted path is the real signal.

Either version regenerates the other byte-exactly (`jsonl_retime_and_rehash`; recipe and proof in the
JSON record, re-verified by the test on every run).

## Do not

- `git lfs prune` or `git gc --aggressive` — the `19365f60` LFS object is referenced by **no commit**
  (checked across all 8,083). This is audit item **D-1**.
- `git checkout` / `restore` / `stash` / `clean` on this path inside `/Users/borr/GTOSActive/repo` —
  that working file *is* the `19365f60` copy the sealed campaign resolves against
  (`replay_acceleration_attempt5_typed_sparse_runner.py:186`, `:1043-1046`), and it differs from its
  own HEAD.
- `git clean` or `git checkout` **anywhere in this route** — two `REPLAY_EXTENSION_*` paths here are
  load-bearing *by their absence*.

## Not at risk

`SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` in this same directory is **fully git-custodied** — working
tree, HEAD pointer OID, R2's expectation and the local LFS object all agree at
`64fd10148a1b656a…f7a09870` (5,995,223 B). It is not part of the D-1 exposure. Do not conflate the two
ledgers.
