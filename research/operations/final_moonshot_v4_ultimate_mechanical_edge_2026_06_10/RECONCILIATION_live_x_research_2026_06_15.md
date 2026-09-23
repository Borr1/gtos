# RECONCILIATION — live handoff × research (2026-06-15), principal-verified

I (research principal) personally read + verified the handoff source (not just the subagent digests; the
live orchestrator's own subagents mis-stated its §2/§4, so digests are a lens, not truth). This connects
the live reality to the 58-cycle research — the connections only the principal carries.

## MERGE POSTURE (settled, safe — NOT a big-bang merge)
- **PRESERVE all live runtime work** (deploy-live `de040e475..7d886e32f`, 56 commits): the W7 ultimate_book
  build, symbol resolver, FIX-1..4, FN follower, **static-90k governor**, **4% gross cap**, running-count
  Kelly, supervisor/monitor, native-exit management. All load-bearing live-failure fixes. Never revert.
- **Clean-add my research infra** — `src/research_infra/validation_integrity/` (the 4-guard machine, 75
  tests) has **0 overlap** with the live branch → merges with zero conflict.
- **DO NOT auto-merge** the deleted halt-flags (keep research halted) or the gate flags (live-authorized
  only). The 2 staged-unloaded commits (`d7f1285a7` pid-lock, `7d886e32f` ledger TOCTOU) load on next restart.
- **Route↔src parity**: `ultimate_book_live_package.py` must stay byte-parity with `src/components/
  ultimate_book/` SLEEVE_CONF (self-test asserts it). Any book change goes to both.
- This is **surgical port + reconcile**, not a 300-commit merge over a live money system.

## VERIFIED FACTS THAT UPDATE RESEARCH CONCLUSIONS (I checked these against source)
1. **Real execution costs are 3–10× cheaper than my retail estimate** (`admission.py TICK_SPREAD_FLOOR_R`,
   measured on the bridge): index CFDs **0.004–0.017R** live, XAUUSD 0.0118R, BTCUSD 0.0001R, USDJPY 0.0841R
   (commission-heavy on tight stops). My c44–46 intraday harness charged ~0.05–0.07R. **→ REOPENS intraday
   breadth**: the c45 time-of-day INDEX drift (gross OOS +0.056R, needed cost ≤~0.04R) CLEARS at real index
   cost. My intraday-cost-gating verdict was built on too-conservative costs — the cost-layer version of
   the owner's "too conservative" critique. (Caveat: tight-stop FX intraday stays cost-heavy via commission.)
2. **Max-DD is a STATIC 90k floor, not trailing** (owner rule, governor fixed `64b9e6a69`). My c51/57/58 MC
   used TRAILING (peak−eq)/peak. → I must re-run with the static floor. For a fresh account climbing to +8%,
   static is MORE lenient than trailing (you can give back from a peak to 90k) → my aggressive numbers were
   if anything CONSERVATIVE for fresh accounts. For FTMO (started −2.87%, only **7.1% runway**), static is
   CLOSER → tighter.
3. **Live MC (W7 book, static floor):** dial→pass/fail_dd/median-days, NO DD-defense: 1.25%→0.994/0.006/71d,
   1.50%→0.986/0.014/58d, 1.75%→0.973/0.028/49d, 2.00%→0.959/0.041/42d. FTMO from −2.87%: **0.9901 / 98d**;
   FN fresh: 0.9983 / 71d; joint P(both) **0.9902**. (My docs' 0.99+ at 1.25% match; the FTMO start-state
   asymmetry I had NOT modeled.)
4. **The live book is the index-short factor right now** (idxrev + vp_euidx_pocgrav open). idxrev is ALREADY
   demoted to 0.15 (breadth_falsified) in the live registry — ALIGNS with my c25 (index = leak). But the live
   `clean3_w7` profile has clean_3 ENABLED (owner flipped it at go-live); the first trade was vp_euidx_pocgrav
   — a clean_3 sleeve my c24/25 flagged as cell-selection glow → **DROP**. metals_core (conviction 1.00, my
   robust core) is gated off this regime (ac60 0.029<0.10) so it isn't firing — the open risk sits on the
   weak factor by regime, not design.
5. **The hard-halt (−$859.69/77 trades) 8 failure mechanisms are each W7-fixed** (curated universe + cost
   gate + static governor + 4% cap + native exits + independent processes + monitor); ~30h live, no repeat.
   My corrections must NOT reintroduce: open-universe loading, removed regime gates, gross cap >4%, the cost
   gate. (They don't — they're orthogonal: book composition + sizing schedule.)

## THE CRUX RECONCILIATION (answers the owner's "too conservative")
The live held 1.25% because, **without DD-defense**, higher base degrades pass (live MC: 2%→0.959/fail_dd
0.041). My c55–58 proved **DD-defense (de-risk → 0 near the wall) holds fail_dd ≈ 0 at higher base** —
because it makes the floor near-unreachable, flipping the binding constraint to the daily limit (which the
tame distribution leaves huge headroom under). **The live governor already HAS a band DD-defense (full size
to 7% DD, linear to 0 at 10%)** — but the dial-validation MC didn't model it. → **Re-run the live W7-book MC
WITH DD-defense, static floor, per-account start** to find the safe-aggressive base per account. Expected:
the DD-defended book runs ~1.75–2.0% (FN; toward 2%+ fresh) at maintained pass + ~0 fail_dd → **time-to-pass
~halves (FN 71→~45d, FTMO 98→~55d)**; FTMO's thin 7.1% runway caps it lower than FN. This is the precise,
account-specific, owner-decision-enabling number — the next deliverable (CYCLE 59).

## NEXT-LEVEL ACTIONS (research × live, both rise)
- **A. Corrected aggressive-sizing MC** (c59): live W7-book distribution + DD-defense + static 90k + actual
  account states (FN fresh, FTMO −2.87%) → safe-aggressive base per account. Feeds the owner's sizing decision.
- **B. Reopen intraday breadth at REAL costs** (c60): re-run the c45 index time-of-day / reversion edges at
  0.004–0.017R (not retail) → which now certify? Genuine new breadth the cost-conservatism had hidden.
- **C. Book correction** (owner-gated): demote/disable clean_3 (vp_euidx_pocgrav etc.) → prioritize the robust
  core (metals_core+softband+us_equity); idxrev already at 0.15. Surface for owner: the `clean3_w7` profile
  carries my-flagged-weak sleeves.
- **D. Close the live #1 residual**: rebuild W2/W3 stream caches + run the real KB7 harness → confirm the
  running-count safety + the absolute FTMO odds (currently a calibrated reconstruction).
- **E. Clean-add the 4-guard machine** to the merged tree (every future edge passes it).

## OWNER JUDGMENT-CALLS (not mechanical — need your input)
1. **RESOLVED (owner 2026-06-15):** FTMO Phase-1 target = **+10% (110k)**, FN Phase-1 = **+8% (108k)**, Phase-2 = +5% both.
   Both governed by the SAME binding risk: **−5% daily, −10% max-DD from initial 100k (static 90k floor)** — so the target does NOT change the sizing-safety conclusion (only the climb time). c59 re-run with the correct per-account targets: FTMO +10% is slower (116d at 1.25%) but smooth-DD-defense @3% ~halves it to 59d (pass 1.0, 0 fail-dd, 0 daily-breach); FN +8% @3% = 32d.
2. **FN product rules UNCONFIRMED** (inherits FTMO 100k/5%/10%/+8% by hardcoded default; FN consistency rule
   not encoded) — confirm before treating joint odds as matched.
3. **FTMO thin cushion (−2.87%, 7.1% runway):** you accepted it ("not resetting, not going conservative").
   Aggressive sizing there is genuinely tighter (the static floor + 7%-DD de-risk band engage sooner) — the
   c59 MC will quantify the safe FTMO base vs the fresh-FN base.
4. **`clean3_w7` includes the 3 clean_3 sleeves my research flags as glow** — keep, or switch to the 8-sleeve
   core (clean_3 off) / honest core?
5. **Aggressive sizing (4.5–5% from c57) vs the live 1.25%:** c57 was a FRESH account, trailing DD, 2-class
   core. The live is the W7 book (std 0.758 vs my core 0.426 — more volatile), static floor, thin FTMO. The
   c59 MC reconciles these to the right per-account number — likely well above 1.25% with DD-defense, but
   account-specific and below the naive 4.5%.
