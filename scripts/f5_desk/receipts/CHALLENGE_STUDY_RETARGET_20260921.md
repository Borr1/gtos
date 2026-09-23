# Receipt — Nightly Decide / f5_study Challenge retarget (2026-09-21)

**Claim.** GitHub study/decide paths default to FTMO Challenge login **0**.
Verification **0** cannot be the LIVE default and fail-closes if a study
body is stamped with it.

**Scope.** Challenge-only. redacted_account out of scope. No broker-send.

**Why.** Chair already retargeted VPS `f5_study` LIVE and `nightly_study.ps1`.
`origin/main` had **no** `scripts/f5_desk/`. The closest GitHub copy was
`origin/f5-leftover-ship` @ `37056de60`, which still leaked verification:

| leftover-ship path | leak |
|---|---|
| `scripts/f5_desk/JUDGE-CHARTER.md:3` | `FTMO 0` |
| `scripts/f5_desk/chair_mt5.py:13` | `LOGIN = 0` (chair I/O; **not** landed) |
| `scripts/f5_desk/nightly_study.ps1` | no LIVE pin; called `C:\Users\trader\redacted_host\f5_study.py` |
| `scripts/f5_desk/decide.py` | no login gate; imported `C:\Users\trader\redacted_host` at module load |

`f5_study.py` itself was never in git (`git log --all -- '*f5_study*'` empty).
This PR lands the study/decide pin on `main` so a VPS pull cannot drift back.

## What landed

| path | role |
|---|---|
| `scripts/f5_desk/challenge_identity.py` | `LIVE = CHALLENGE_LOGIN = 0` |
| `scripts/f5_desk/f5_study.py` | default login Challenge; refuses 0; no MT5 import |
| `scripts/f5_desk/decide.py` | leftover KEEP/OFF arithmetic + verification fail-closed |
| `scripts/f5_desk/nightly_study.ps1` | `$LIVE = 0`; throws on verification env |
| `scripts/f5_desk/JUDGE-CHARTER.md` | identity stamp Challenge; $250-era labeled historical |
| `tests/f5_desk/test_challenge_login_retarget.py` | behaviour + grep-proof |
| `.github/workflows/f5-study-challenge-login.yml` | smoke + pytest |

**Not landed.** leftover-ship chair desk (`chair_mt5.py`, composer, shim,
scoreboard, inbox_gates). Those are not study/decide. `chair_mt5.LOGIN` on
leftover-ship remains verification until a separate chair PR.

## Proof commands

```bash
python scripts/f5_desk/f5_study.py --smoke --out /tmp/f5-study-smoke
python scripts/f5_desk/decide.py /tmp/f5-study-smoke /tmp/f5-study-smoke
python -m pytest tests/f5_desk -q
```

Ran 2026-09-21 on this checkout:

```
$ python3 -m pytest tests/f5_desk -q
.............                                                            [100%]
13 passed in 0.65s

$ python3 scripts/f5_desk/f5_study.py --smoke --out /tmp/f5-study-smoke
LIVE=0 smoke wrote /tmp/f5-study-smoke/f5_study.json

$ python3 scripts/f5_desk/decide.py /tmp/f5-study-smoke /tmp/f5-study-smoke
# F5 DECISIONS — 2026-09-21 01:21Z
- LIVE=0 Challenge login 0. Verification 0 quarantined.
study LIVE=0 login=0
decide status=OK account.login=0

$ python3 scripts/f5_desk/f5_study.py --login 0 --smoke --out /tmp/f5-study-bad
REFUSED: verification login 0 is quarantined; Challenge LIVE is 0
exit 2
```

## Hard rules this receipt does not relax

- No `order_send` / place / remint / flatten from these scripts.
- redacted_account is not a study surface.
- KEEP/OFF still requires n≥40 and \|mean R\| > 2·SE.
