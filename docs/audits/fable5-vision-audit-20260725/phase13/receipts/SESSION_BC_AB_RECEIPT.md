# Session BC A/B — command center + MT5 MCP read-only contract (B2000-B2049)

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `5e3061ae4` | `76177dc51` |
| captured (UTC) | 2026-07-30T16:52:51Z | 2026-07-30T17:08:19Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 896 | 959 |
| skipped | 3 | 3 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/ultimate_book"
 ],
 "before": {
  "commit": "5e3061ae400cdc80018413712a280b3b133930d8",
  "commit_subject": "AW receipt: the tool fence appended (70/70 at the merged tree; first capture attempt refused by the tool's own empty-set guard)",
  "captured_utc": "2026-07-30T16:52:51Z",
  "dirty": true,
  "totals": {
   "passed": 896,
   "skipped": 3,
   "xfailed": 2
  }
 },
 "after": {
  "commit": "76177dc51cd13887eccd438ceafaff4da75548e2",
  "commit_subject": "Session BC: the command center \u2014 and the armed set stops being something the operator types",
  "captured_utc": "2026-07-30T17:08:19Z",
  "dirty": true,
  "totals": {
   "passed": 959,
   "skipped": 3,
   "xfailed": 2
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

---

## Cross-directory check, run because the scoped A/B could not cover it

Every file this session added is new, so the only breakage class outside `tests/ultimate_book` is
**import-level** — which is precisely what B2012 was. Verified separately:

```
pytest tests/ultimate_book/test_gtos_command_center.py \
       tests/ultimate_book/test_gtos_mt5_mcp_readonly.py \
       tests/ultimate_book/test_defect_register_repairs.py \
       tests/test_mc_firm_rules.py tests/test_armed_set_mc.py tests/test_w7_recost.py
-> 170 passed, 1 xfailed, 0 failed, 0 skipped
```

The three `tests/test_*.py` files chosen are the ones that put `scripts/` on `sys.path` themselves;
`test_defect_register_repairs.py` is the file whose two `pytest.importorskip` tests B2012 silently
skipped. This combination failed once — on an **over-strict assertion of mine**, not on a real
defect: the regression test asserted the process-wide invariant "`scripts/` is never on sys.path",
which those three files legitimately violate (they pre-warm `sys.modules` with the correct
`research` package first). The invariant this session owns is narrower — *importing
`gtos_command_center` must not put it there, and must not break `research.operations`* — and is now
asserted in a clean **subprocess**, so it does not depend on collection order.

The regression test was then verified to be capable of failing: reintroducing the defect in its
subtler **append** form turns it red, and removing it turns it green again.
