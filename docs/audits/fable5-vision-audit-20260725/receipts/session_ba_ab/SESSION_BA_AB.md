# Session BA (B1900-B1913) — scoped A/B: the weekend-holding policy

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `5e3061ae4` | `69271c6c6` |
| captured (UTC) | 2026-07-30T17:17:08Z | 2026-07-30T17:30:46Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 371 | 371 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_vig_trial_ledger_prospective.py",
  "tests/safety/test_activation_token_attacks.py",
  "tests/scripts/test_pytest_failset_parsing.py",
  "tests/test_run_book_importable.py",
  "tests/ultimate_book/test_activation_carry_vps_lineage.py",
  "tests/ultimate_book/test_book_owner.py",
  "tests/ultimate_book/test_book_sleeve_telemetry.py",
  "tests/ultimate_book/test_breach_flatten.py",
  "tests/ultimate_book/test_frontier_exit_contracts.py",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py",
  "tests/ultimate_book/test_packet_carry_vps_lineage.py",
  "tests/ultimate_book/test_packet_emitter_hardening.py",
  "tests/ultimate_book/test_pre_gap_bar_wiring.py",
  "tests/ultimate_book/test_runtime_learning_packet.py",
  "tests/ultimate_book/test_time_stop_rehydration.py"
 ],
 "before": {
  "commit": "5e3061ae400cdc80018413712a280b3b133930d8",
  "commit_subject": "AW receipt: the tool fence appended (70/70 at the merged tree; first capture attempt refused by the tool's own empty-set guard)",
  "captured_utc": "2026-07-30T17:17:08Z",
  "dirty": true,
  "totals": {
   "passed": 371,
   "xfailed": 1
  }
 },
 "after": {
  "commit": "69271c6c6146e7154b471ad16dfb0f65c649e133",
  "commit_subject": "Session BA: the redacted_account weekend solution (B1900-B1913) \u2014 priced, built, default-off",
  "captured_utc": "2026-07-30T17:30:46Z",
  "dirty": true,
  "totals": {
   "passed": 371,
   "xfailed": 1
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": []
}
```

## Scope note (Session BA)

The two captures share **one** 15-file scope — `scope_ab.json`, this directory. It is
`pytest_failset.py scope --base HEAD --include-worktree` **minus this session's own new test
file**, which cannot exist on the before side (it imports the module the change adds) and whose
presence would make the two scopes differ, which `receipt` refuses. Its **80** tests are the
net-new passing side and are captured separately in `after_newfile.json`:

```
tests/ultimate_book/test_ba_weekend_policy.py -> 0 failed / 0 errored, 80 passed
```

So the whole A/B reads: **0 bad → 0 bad, 0 regressed, 371 → 371 passing in shared scope, +80
net new passing.** The before side was produced by copy-back (`git show HEAD:<path>` for the two
modified files, the two new files moved aside), never by `git checkout` — wave-11 agreement §2.
