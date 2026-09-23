# GTOS VPS OPERATOR — READINESS REPORT (2026-06-14)

Resident operator session on the Windows VPS (repo root C:\Users\MSI\Documents\ai-trading-agent).
Posture: **PREPARE / OPERATE — never EXCEED.** System hard-halted, default-off throughout. No order placed.

## Branch
- `deploy-live` @ HEAD **3c564a8c6** (8 local commits ahead of origin/deploy-live `86cccd08`; **not pushed** — push needs owner approval). Base verified == origin at start. Pre-existing `main` work safe in `stash@{0}`.

## What I fixed (all committed, all reversible)
1. `wave1` hardcoded dev-Mac path → preflight was FAILING on this VPS (2 parity tests). Path-portable now; preflight exit 0.
2. `.env.*` gitignore gap — per-account broker cred files were NOT ignored. Hardened.
3. Dual-adapter symbol map reconciled to LIVE truth (FTMO oil 1000/2→100/3 bug; FN oil USOIL.c→USOUSD; GBPJPY).
4. **Curated 27-symbol universe** (book sleeve union): +10 expansion (metals crosses, DASHUSD, CORN_c/COTTON_c, EU50/FRA40/US2000_cash), −7 non-JPY pure-FX. config + all 3 profiles, every spec live-verified.
5. **Contract-size-aware follower sizer** — the 10× index / ETH mis-size hazard is fixed in code (`follower_volume_for`, floored, below-min→skip), tested.
6. Config staged: broad selector disabled (Step5) + ultimate_book block default-off (Step6).

## Pre-flight + tests (venv .venv-gtos, python 3.13)
- `GOLIVE_preflight_verify.py` → **exit 0** (PASS). `--require-broad-selector-off` → **exit 0** (broad selector now off).
- Full matrix **195 passed** (`test_ultimate_book_live_package` + `test_ultimate_book_runtime_bridge` + `GOLIVE_vps_deploy/tests`). Parity asserts parity_ok=True.
- All 3 halt flags PRESENT (GTOS_HARD_PRODUCTION_HALT, RESEARCH_RUNTIME_HALT, AUTOSTART_DISABLED).

## Terminals (both open, read-only verified — NO orders)
| Role | Path | Account / Server | Balance | Symbols | Clock→UTC |
|---|---|---|---|---|---|
| FTMO PRIMARY | C:\MT5\FTMO\terminal64.exe | 531325516 / FTMO-Server3 | $97,052.38 | 166 | +179 min |
| FN FOLLOWER | C:\MT5\redacted_account\terminal64.exe | 0 / redacted_account-Server 2 | $99,965.20 | 76 | +180 min |
- VPS OS clock = UTC, NTP-synced (w32time). FTMO confirmed PRIMARY. Both offsets known integers.
- Curated universe live coverage: FTMO primary all 27; FN follower 20 (7 FTMO-only → follower skips, isolated).

## Parity ledgers — first readings
- live-vs-replay (primary) and FTMO-vs-redacted_account (follower): **0 rows** — no live trades (halted by design). The ledger interfaces + the contract-size follower translation are built + unit-tested; they populate on the first shadow/live cycle.

## Broker / runtime AUTHORITY gate (Step 9)
| # | Item | Status |
|---|---|---|
| 9.1 | Hard-halt forensic (why broad lost −113.4R) | Evidence in repo (hard_halt_reconciliation 06-03, failure_intelligence 06-04); replacement = narrow 27-sym book + broad selector DISABLED. **Owner signs.** |
| 9.2 | V3-vs-live authority gap audit | V3 + broad selector/scheduler now all apply_to_execution=false (config verified). **Owner signs.** |
| 9.3 | Dual-broker architecture audit | **Substantially DONE** — FTMO-primary/FN-follower verified live; symbol/spec/contract/clock differences mapped; follower isolation + contract-size sizing built + tested. |
| 9.4 | Production-return dossier (signed) | **Owner-domain.** |
| 9.5 | Creds + 2 accounts + VPS + NTP | **DONE** (both terminals connected, NTP synced). Owner confirms account types + that these are the go-live accounts. |

## GO / NO-GO
**NO-GO for a live order — correctly, by design.** Everything technical is GREEN, STAGED, and DEFAULT-OFF. Remaining blockers (all owner-domain):
1. Explicit owner **"GO LIVE"** in this session.
2. **Step-9 authority sign-off**: signed production-return dossier (9.4) + confirm 9.1/9.2 + confirm the two accounts (9.5).
3. **Step-7c src fold** (STEP7_SRC_FOLD_INTEGRATION_SPEC.md): the reviewed merge of ultimate_book admission into src + dual adapter into src/mt5 — inert until flip, pairs with the go-live review.
4. (Recommended) Re-measure per-broker spread R-floors during full market hours (indices/oil were off-hours at measurement).

Until all clear + explicit GO LIVE: stay halted / default-off, keep validating. Sizing dial at flip = 1.25% half-Kelly first cycle, FTMO only; follower up after parity confirms; 2.0% hard ceiling.
