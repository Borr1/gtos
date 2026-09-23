# F5 CHAIR HANDOFF — redacted_account usage dark
Written: 2026-09-01 13:15 ICT by redacted_account (chair). Owner asked: leave this note, Cursor agents take over.

**You are acting chair until redacted_account has usage again.** Writer still prints. Occupancy HOLD is dead. Later spoken word wins. Payout is the objective.

## Do not
- Flatten from fear. Do not park. Do not remint spent tickets.
- BE/trail gold on first MFE. Owner 2026-08-31 20:16 ICT: let overlap breathe. Later word beats “take at 2R if tape stopped” on this overlap.
- Restart writer unless pair is actually dead. Persist orig first. Do not hunt PIDs 10384/2760.
- Remint 180155576 / 180274922 / 180318564.
- Place from seats as a panic. Isolated re-entry after 15m is a **new named fire**, not a remint.
- Recreate Pulse / Walter Eye. Second filtered-stream socket (429).
- Mint new HOLD laws from one sweep/BE instance.

## Identity
- Login **0** / ns **operator** / magic **0** / unit **$250** / pass **$105k**
- Portable only `C:\MT5\FTMO` (FTMO-Server3)
- Writer **GTOS_F5_FTMO** Running, pair child **8928** (do not restart 10384/2760)
- Owner full approval 2026-08-31 19:00 ICT: send / place / manage / isolated re-entry

## Live book at 13:14 ICT (sit this, then refresh)
bal **96400.15** eq **96500.56** float **+100** day_net ~**+$243** to_pass **~$8600**
OPEN3 PENDING0

| ticket | symbol | side | vol | entry | orig SL | TP | mark 13:14 | float | word |
|---|---|---|---|---|---|---|---|---|---|
| **180322126** | XAUUSD | LONG `dsp_bleed_acc` | 0.30 | 4426.21 | **4418.26** | 4473.91 | 4432.56 | +$190.5 | **LEAVE orig** |
| **180324886** | UK100.cash | LONG `idxrev` | 3.37 | 10774.75 | **10720.04** | 10815.78 | 10763.8 | −$50 | **LEAVE orig** |
| **180335205** | ETHUSD | LONG `orb_crypto_lo` | 1.84 | 2480.60 | **2466.44** | 2508.92 | 2478.42 | −$40 | **LEAVE orig** (NULL crypto, not class) |

### Gold 180322126
- Rest BUY_LIMIT tagged. Fill LEAVE 11:57 ICT.
- R_orig 7.95pts / ~$238.50. MFE **2.47R @ 4445.87** (15:57 broker).
- 13:05 ICT take exam **overridden**: 9pt fade was ~50% of the 15:30–15:45 impulse, not a stop. London 14:00 still ahead. Capture had decayed; invalidation is still orig 4418.26.
- Atlas saw live_sl 4427.33 BE-trail; broker was already orig 4418.26 when chair checked. **If writer trails again, restore orig 4418.26** (`TRADE_ACTION_SLTP`). Do not lock first MFE.
- Do not take just because MFE≥2R. Take only if tape actually stopped (no new highs, structure broken), not a breathe retrace.

### UK100 180324886
- Market BUY (not rest) 12:00 ICT. Fill LEAVE 12:06. Leave orig 10720.04. Do not flatten.

### ETH 180335205
- Market BUY 12:46 ICT deal 169045181. Fill LEAVE 12:49. Atlas: NULL crypto, not class. Leave orig 2466.44.

### US30 180318564 — SPENT
- Orig SL 12:00 ICT −$255.50 (−1.029R). Isolated re-entry after **12:15 ICT is OPEN**. New named fire only if writer prints one. Do not remint this ticket.

## Tuesday paid / spent (instance memory, not new laws)
- XAU **180274922** SHORT taken 09:22 ICT @ 4447.67, net **+$516.06** (~2.05R). Re-entry after 09:37. Do not remint.
- US30 **180318564** orig SL as above.
- Gold **180155576** owner pulled 05:26 ICT. Do not remint.

## Next clocks
- **London session-open 14:00 ICT** (F5 Session Open routine). Sit it.
- **ISM T-15 20:45 ICT** Sep 1 (ISM Manufacturing + JOLTS 21:00). Join XAU / US30 / USD FX. Do not flatten the live three into ISM from fear; sit T-15 as its own plate.
- NFP T-15 Sep 4 19:15 ICT.

## How to sit
```
ssh gtos-vps
C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe host-local\redacted_host\repo\scripts\f5_desk\chair_desk.py sit --mt5
```
MT5 path: `C:\MT5\FTMO\terminal64.exe`. Login must be 0.
Restore orig example: `TRADE_ACTION_SLTP` on ticket with sl=orig, keep tp.
Take: `TRADE_ACTION_DEAL` only with a number and a reason (tape stopped / owner word). Comment `chair_take_mfe`.

## Writer / emit
- Persist orig before any writer restart (`dr/orig_sl_*.json` + `chair_orig_sl.json`).
- Book-event watcher v4: live login 0 only, tickets ≥ 180000000. Harvest glob is gone. Do not re-enable harvest glob.
- Pair dead → persist orig, restart **GTOS_F5_FTMO only**.

## Seats (if Grok still has crumbs)
- Fillpath `6ac65da7` — writer + emit. **Acting chair while redacted_account is dark.**
- Atlas `c4c4deb0` — class N/1/$X once per fill. Does not place.
- Markets `4e049af6` — tape / HIGH veto. ISM join.
- redacted_account `6a1b47f3` — dark on usage. Do not wait for it.

## Owner law (later spoken word wins)
- 2026-08-31 19:00 ICT: full approval including send/place/manage; payout is the objective.
- 2026-08-31 20:16 ICT: do not put SL immediately; overlap has huge potential; do not BE on first MFE.
- 2026-09-01 ~13:13 ICT: redacted_account almost out of usage; this handoff; Cursor agents take over.

Payout remains the objective. Sit the three. London is next.
