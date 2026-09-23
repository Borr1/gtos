# Session CL — pass-surface result (wave 17, B2650–B2699)

Commission `phase17/SESSION_CL_PASS_SURFACE.md`; owner directive
`phase17/OD_ALL_IN_20260801.md`. Branch `phase17/pass-surface`.

Nothing was armed. The VPS was untouched, no broker-capable script ran, neither token-bound
config moved, and March 2026 outcomes plus the live-forward TEST stream stayed unread.

## 0. Findings first

1. **The approved direct-addition set is empty on both accounts.** That is the priced answer,
   not a refusal to execute OD-ALL-IN. JPY and metals-core make the primary pass surface
   worse; metals-softband has a useful sensitivity but remains carry-conditional; VP is still
   structurally unpriceable; FTMO MX is already in the baseline; redacted_account MX fails the
   historical-primary gate.
2. **The current FTMO book is positive at actual realised hold and fragile at W7 maximum
   carry.** Primary pre-2025 economics are L4 `p_pass=0.7791`, P2 two-step `0.6499`,
   `+0.4196%/calendar month`, and 449 median calendar days among passing paths. Maximum-carry
   stress cuts that to P2 `0.2611` and `-0.0407%/month`.
3. **The priceable redacted_account subset is negative before 2025:** L4 `0.4299`, P2 `0.2376`,
   `-0.2935%/month`. That grid is explicitly PARTIAL because the broker cost artifact does
   not support every row of the current four-sleeve book. It is rejection evidence on the
   observed subset, not full-book authority.
4. **The payout-clock result is conditional.** Every published clock is the median among
   paths that passed. A lower clock paired with lower `p_pass` is survivorship bias, not a
   faster path to payout. The receipt places the probability, expectancy and clock together
   for every set so the shorter number cannot travel alone.
5. **Two ideas merit incubation work and neither merits live arming today.** ETH target-5R and
   Asia PDL stop-2.5/native/no-time-stop are registered as `PROPOSED` at confidence `0.025`.
   They consume zero capacity, have pre-registered fidelity/loss/gross-negative stops, and
   remain blocked on exact live-contract parity and account-local factory evidence.
6. **The ceremony is a sealed no-op.** Its manifest has no payload and no copy order. It
   captures the host's actual bytes/hashtable/worker lines, verifies the current five/four
   set and startup proofs, and stops. It authorizes no supervisor edit, ledger clear, flag,
   restart, config change or token action.

## 1. What the grid says

The tool imports `scripts/mc_firm_rules.py::mc` unchanged and runs 20,000 paths per cell at
the live 2% dial, half-Kelly, firm-true L4/P2 rules, actual-hold and W7-max-carry variants. The
current live weights remain:

- FTMO: `crypto .85`, `energy_agri .80`, `sub_xvol_pullback .45`,
  `sub_mid_dn_revert .20`, `mx_btcusd_d1_donchian_20_breakout .025`.
- redacted_account: the same first four, without MX.

Primary, actual-realised-hold P2 deltas versus those baselines:

| candidate set | FTMO Δ P2 | redacted_account Δ P2 | disposition |
|---|---:|---:|---|
| `fx_jpy` | **-0.0410** | -0.0158 partial | do not arm |
| `fx_jpy_ny` | **-0.0759** | **-0.0430** partial | do not arm |
| both JPY | **-0.1121** | **-0.0704** partial | do not arm |
| `metals_core ×0.50` | **-0.1198** | **-0.0596** partial | do not reintroduce |
| `metals_softband ×0.50` | +0.0449 | +0.0673 partial | do not arm; carry-conditional |
| FN `mx_btcusd@target_5R` | already in baseline | +0.0039 partial | do not arm; factory gate fails |
| `vp_euidx_pocgrav` | not priceable | not priceable | do not arm; UK100 unblock remains |

The 2025–May-2026 grid is reported separately as used-once VAL. Its larger baseline numbers
(FTMO +2.5355%/month; redacted_account partial +1.7116%) are not promoted to expectation. March,
label shoulders into March, post-VAL labels and live forward were rejected before outcome
access. Full tables and coverage are in
`phase17/receipts/CL_PASS_SURFACE_PRICING_V1.md`; the bound machine receipt is its `.json`.

## 2. Incubation, not ceremony

`mx_ethusd_d1_donchian_20_breakout@target_5R@FTMO` has attractive arithmetic (n=217,
+0.456628 R/day, recent-two +1.010822) but REJECTS robustness/significance and has no live
target-5R contract, parity receipt or redacted_account account-local measurement.

`asia_pdl_fade@stop2.5_native_no_ts@FTMO` has n=2,827, +0.084626 R/day and 5/5 positive folds,
but REJECTS significance; live exposes the wrong weight, stop/exit and time-stop contract.

Both dossiers are schema-valid `OWNER_RISK_ACCEPTED` proposals at 0.025. Their stop rules are
already written: zero fidelity mismatches; cumulative loss at -6.035R / -3R; or non-positive
gross after at least 20 fills across 8 day blocks. Promotion is historical-primary on the
exact contract at both firms, with live data only a veto and a fresh owner ceremony always
required. The registry remains 1 armed of 5. Two unbilled, existing-measurement carry rows
were appended to the iteration ledger; nothing was graduated or billed.

## 3. What was built

| deliverable | artifact |
|---|---|
| candidate inventory + firm-true MC grid | `phase17/receipts/CL_PASS_SURFACE_PRICING_V1.{json,md}` and `cl_pass_surface.py` |
| two bounded proposals + official disclosures | `phase17/receipts/CL_INCUBATION_PROPOSALS_V1.{json,md}`, `cl_incubation_dossiers.py`, registry + iteration ledger |
| zero-mutation ceremony | `phase17/activation_pass_surface/` — manifest, approved set, exact empty diff, capture, verifier, ceremony page |
| behavioural gates | three `tests/research_infra/test_cl_*.py` files; 14 focused tests |
| evidence index | `IMPLEMENTATION_STATE.md` B2650–B2688; CL in-flight row retired |

## 4. Verification

The three Session-CL test files pass 14/14; with the block-citation guard the focused closure
passes 24/24. The package builder and `verify_pass_surface.py --check package` both pass. The
mandatory tool-emitted `gtos-ab-receipt-v1` fence is embedded in
`phase17/receipts/SESSION_CL_AB_RECEIPT.md`: **215 passed → 215 passed, 0 bad → 0 bad,
0 regressed** on the shared copy-back scope. The three HEAD-only suites pass **14/14**
separately. `SESSION_CL_AB_SCOPE.md` records the exact base-byte restoration and why both
tool captures name the same unmoved commit; the embedded fence remains the authority.

## 5. What I got wrong

1. **My first candidate merge could let an absent extension inherit the baseline's days.** A
   candidate with no priceable series could then receive an apparently valid MC cell. I added
   a completeness guard: every requested extension must contribute its own series or emit
   `NOT_PRICEABLE`/`ALREADY_IN_BASELINE`. VP now has no fabricated number.
2. **I initially read a shorter conditional payout clock as a possible speed benefit.** The
   paths that fail never enter that median, so a worse book can look faster. The generated
   report now labels the denominator at the top and the result uses pass probability plus
   expectancy before the conditional clock.
3. **I expected the latest live supervisor bytes to be reconstructable locally.** Host commit
   `267cccc94` is not an object in this worktree, the local supervisor is stale, and the live
   receipt commits only SHA prefix `63079cec`. I did not guess the missing hashtable key or
   copy local bytes into a package. The ceremony now captures the literal host `$books` block
   and requires byte identity; drift means rebuild.
4. **A small positive MC delta looked like a reason to test FN MX live.** Its primary partial
   ΔP2 is +0.0039, but CH's broker-local historical-primary gate is negative OOS and lifetime
   at every band. The gate outranks the sensitivity. It is screened out, not incubated.
5. **Four free incubation slots looked like an invitation to fill more of them.** The vr1.4
   xvol row is not independently stoppable from an already-armed parent, while redacted_account
   Asia has no account-local dossier. I filed two distinct proposals and left the other slots
   empty; capacity is a ceiling, not a target.

## 6. Exact orchestrator handoff

This CL package should run only if no later CM/CN/CO ceremony has changed the host first. If
one has, CL preflight must refuse and the no-op baseline should be rebuilt/composed—not forced.

1. On the research laptop, run `activation_pass_surface/build_package.py`, then
   `verify_pass_surface.py --check package`. Stop on any hash or empty-set failure.
2. On the host, the orchestrator runs only `capture_host_preflight.ps1` and returns
   `HOST_PREFLIGHT.json`. It is an evidence capture; it imports no GTOS/MetaTrader module.
3. On the research laptop, run `verify_pass_surface.py --check preflight --host-preflight
   HOST_PREFLIGHT.json`. It must prove host branch/head/supervisor, one worker per namespace,
   exact tags/frontier/floor and all startup banners/timeframes.
4. **Stop.** Do not edit or back up the supervisor, hold flags, clear a firing ledger,
   stop/restart anything, copy runtime files, or inspect/re-mint a token. The authorized diff
   is empty.
5. Capture `HOST_POSTFLIGHT.json` with the same evidence script and run
   `verify_pass_surface.py --check postflight --host-preflight HOST_PREFLIGHT.json
   --host-postflight HOST_POSTFLIGHT.json`. Exact stable-state equality is the ceremony
   receipt. Any movement is an incident, not an activation success.

The next productive build is contract parity: wire and prove ETH target-5R; make Asia's
stop-2.5/native/no-time-stop plus 0.025 weight addressable; then obtain account-local
redacted_account economics. Only after those vetoes clear does OD-ALL-IN have a non-empty direct
ceremony to execute.
