# F5 desk — study / decide (Challenge LIVE only)

Chair retargeted VPS `f5_study` LIVE and `nightly_study.ps1` to FTMO Challenge
**0**. This directory is the GitHub pin so those paths cannot drift
back to verification **0**.

| Pin | Value |
|---|---|
| LIVE / login | `0` |
| Verification (quarantined) | `0` |
| Magic | `0` |
| Namespace | `operator` |
| Pass | `$110k` |
| redacted_account | out of scope |
| Broker-send | never from these scripts |

## Scripts

- `challenge_identity.py` — single source of truth. `LIVE = 0`.
- `f5_study.py` — in-repo study entry. Defaults `--login 0`. Refuses
  verification. On a VPS it may *delegate* to `F5_STUDY_IMPL` / redacted_host after
  exporting LIVE; the wrapper itself never imports MetaTrader5.
- `decide.py` — leftover-ship KEEP/OFF arithmetic (`n≥40` and `|mean R| > 2·SE`).
  Fail-closes if the study body is stamped verification. Reads `$out` then `$src`.
- `nightly_study.ps1` — nightly launcher. Sets `LIVE` / `F5_STUDY_LOGIN` to
  `0` and throws if an env override is verification.
- `JUDGE-CHARTER.md` — identity stamp is Challenge `0`. The $250-era
  paragraph is labeled historical (verification-era), not the current LIVE pin.

## Smoke

```bash
python scripts/f5_desk/f5_study.py --smoke --out /tmp/f5-study-smoke
python scripts/f5_desk/decide.py /tmp/f5-study-smoke /tmp/f5-study-smoke
python -m pytest tests/f5_desk -q
```

`leftover-ship` still has `chair_mt5.py LOGIN = 0`. That file is **not**
landed here. Chair desk I/O is not a study/decide path.
