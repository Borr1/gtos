# GTOS command center

**⛔ STOP** · exit code `1` · generated `2026-07-26T06:00:00+00:00`

Host state read from `/Users/borr/GTOSActive/vps-export-20260725/extracted`, exported `2026-07-25T23:28:21.811265Z` — **0.3 days old**

> Everything below is a MESSAGE. This page holds no broker connection and no authority: it cannot arm, disarm, resize, flatten or restart anything. Every action it names is a ceremony the orchestrator performs and Borhen authorises.

> Every age on this page is measured against **the export**, not against now. A stale export makes a healthy book look dead.

## What needs you

- **⛔ STOP** · `ARMED` · FTMO — the running worker has NO effective --tags (absent) — it is trading the whole registry, not a bounded set
  <br>*run_book.py:340 treats an empty --tags as falsy and falls back to every BUILT sleeve. Nothing else on this page means anything until this is right. Read the launch command on the host with your own eyes before believing any figure.*
- **⛔ STOP** · `ARMED` · redacted_account — the running worker has NO effective --tags (absent) — it is trading the whole registry, not a bounded set
  <br>*run_book.py:340 treats an empty --tags as falsy and falls back to every BUILT sleeve. Nothing else on this page means anything until this is right. Read the launch command on the host with your own eyes before believing any figure.*
- **⛔ STOP** · `SLEEVES` · FTMO::fx_jpy — cumulative net -6.686 R is at or below the pre-registered RISK floor -3.000 R over 17 fills
  <br>*A risk bound, not an inference: the owner has paid what he pre-registered as the price of finding out. This floor fires 74% of the time on a sleeve running at exactly its archive expectancy, so it says nothing about the sleeve.*
- **⛔ STOP** · `SLEEVES` · redacted_account::fx_jpy — cumulative net -3.022 R is at or below the pre-registered RISK floor -3.000 R over 9 fills
  <br>*A risk bound, not an inference: the owner has paid what he pre-registered as the price of finding out. This floor fires 77% of the time on a sleeve running at exactly its archive expectancy, so it says nothing about the sleeve.*
- **⚠️ ALERT** · `LIVENESS` · FTMO — last launcher cycle was 7.9 h ago (alert above 1.0 h)
  <br>*This is the ALIVE question, not the quiet one. A book that stopped emitting is broken; check the supervisor. NOTE: the age is measured against the EXPORT, so a stale export produces a stale heartbeat — read the export age at the top of the page before treating this as a live outage.*
- **⚠️ ALERT** · `LIVENESS` · redacted_account — last launcher cycle was 33.2 h ago (alert above 1.0 h)
  <br>*This is the ALIVE question, not the quiet one. A book that stopped emitting is broken; check the supervisor. NOTE: the age is measured against the EXPORT, so a stale export produces a stale heartbeat — read the export age at the top of the page before treating this as a live outage.*
- **⚠️ ALERT** · `SLEEVES` · FTMO::fx_jpy — longest run of stop-outs is 7 (alert 6, stop 9)
  <br>*these fills are day-clustered, so independence understates the run probability. The threshold is deliberately loose for that reason.*
- **❔ UNCHECKED** · `ACCOUNTS` · redacted_account — max-DD basis is TRANSFERRED, not MEASURED — the headroom figure assumes a STATIC floor
  <br>*the max-DD BASIS for redacted_account is TRANSFERRED (secondary_audit), not a captured page. If it is TRAILING rather than static, this floor rises with every new equity peak and the headroom above is an over-statement.*

## 1 · The armed set — three independent reads

Expected: `crypto,energy_agri,fx_jpy,sub_mid_dn_revert,sub_xvol_pullback` · union window 168 h

| account | worker `--tags` (running process) | launcher union (window) | config include flags | verdict |
|---|---|---|---|---|
| **FTMO** | **ABSENT** | 32 | `include_clean3=False` | ⛔ STOP |
| **redacted_account** | **ABSENT** | 32 | `include_clean3=False` | ⛔ STOP |

- `FTMO` — reading a single launcher record instead of the union would have said between 9 and 32 depending which tick you read; the union says 32.
- `redacted_account` — reading a single launcher record instead of the union would have said between 10 and 32 depending which tick you read; the union says 32.

**How to read this table.** The worker column is the only one that BOUNDS the book; it is read off the running process's command line, not typed by anyone. The launcher union is what the engine resolved, over a window — never a single record (`launcher.py:328` emits only the tags whose timeframe advanced that tick) — and it is **pre-DF-1**, so it over-reports what can actually fire by up to the three clean_3 sleeves when `include_clean3` is false. The two answer different questions and the page keeps them apart deliberately.

## 2 · The two accounts

| | equity | balance | open P/L | positions | pending | to target | static headroom | daily allowance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **FTMO** | $107,879.56 | $107,879.56 | $0.00 | 0 | 0 | $2,120 | $17,880 | $5,000 |
| **redacted_account** | $96,229.28 | $96,229.28 | $0.00 | 0 | 0 | $11,771 | $6,229 | $5,000 |

**FTMO** — $100k FTMO Challenge 2-Step · login `531325516` · `FTMO-Server3` · terminal build `5836` · connected `True` · trade_allowed `True`

- phase **1** (product '$100k FTMO Challenge 2-Step' names the PROGRAMME (2-Step) but not the current phase; assuming phase 1 — override with --phase if the account has advanced); target 10.0% = $110,000, **$2,120 to go** (+2.12% of initial)
- max-DD floor $90,000 (static (not trailing) for 2-Step, coverage MEASURED) — headroom **$17,880**
- daily allowance $5,000 (Initial Simulated Capital (a FIXED cash amount)), resets 00:00 CE(S)T
  <br>*today's CONSUMED daily loss needs the day-start equity on this firm's own reset calendar, which no export field carries. Supply --day-start-equity ACCOUNT=VALUE, or read it off the terminal. The ALLOWANCE above is a firm rule and is exact.*
- minimum trading days required **4** · **19** distinct trading days in this export, on the CE(S)T calendar (19 on UTC)
  <br>*counted over the WHOLE deal history in this export, not the current phase — the export carries no phase boundary, so read it as an upper bound on progress toward the requirement, never as satisfaction of it. Balance operations are excluded; the day boundary is the firm's own reset calendar, not UTC.*

**redacted_account** — redacted_account-STLR 2-Step P1- Borhen Benltaief · login `0` · `redacted_account-Server 2` · terminal build `5836` · connected `True` · trade_allowed `True`

- phase **1** (from the broker's own product string 'redacted_account-STLR 2-Step P1- Borhen Benltaief'); target 8.0% = $108,000, **$11,771 to go** (+11.77% of initial)
- max-DD floor $90,000 (unstated, coverage TRANSFERRED) — headroom **$6,229**
  <br>*the max-DD BASIS for redacted_account is TRANSFERRED (secondary_audit), not a captured page. If it is TRAILING rather than static, this floor rises with every new equity peak and the headroom above is an over-statement.*
- daily allowance $5,000 (Initial Balance (a FIXED cash amount), PLUS today's realized profit), resets 00:00 server time
  <br>*today's CONSUMED daily loss needs the day-start equity on this firm's own reset calendar, which no export field carries. Supply --day-start-equity ACCOUNT=VALUE, or read it off the terminal. The ALLOWANCE above is a firm rule and is exact.*
- minimum trading days required **5** · **26** distinct trading days in this export, on the server midnight (redacted_account-Server 2) calendar (28 on UTC)
  <br>*counted over the WHOLE deal history in this export, not the current phase — the export carries no phase boundary, so read it as an upper bound on progress toward the requirement, never as satisfaction of it. Balance operations are excluded; the day boundary is the firm's own reset calendar, not UTC.*

## 3 · Authority — gates, flags, tokens

| account | enabled | apply_to_execution | live_activation_allowed | live_broker_authority | as of | profile |
|---|---|---|---|---|---|---|
| **FTMO** | `True` | `False` | `False` | `False` | 2026-07-25T22:05 | `clean3_w7_ceiling_nom2p00` |
| **redacted_account** | `True` | `False` | `False` | `False` | 2026-07-24T20:45 | `clean3_w7_ceiling_nom2p00` |

*These are the gates the **running worker** resolved, from its own launcher record — not the config file on disk. When the two disagree the process is right about now and the file is what a restart would apply; the disagreement is reported above.*

- kill/halt flags probed: **6**, present: **0**
  <br>*absence of a kill flag is the NORMAL running state; it is not a brake. The brake is the gates plus the activation token.*
- activation tokens: **UNCHECKED** — no --token-dir supplied. The live books' tokens are on the VPS, outside every export by design. Expiry is UNCHECKED here — read it on the host with scripts/gtos_activation_token.py list.

## 4 · Alive, and quiet — two different questions

| account | last cycle | heartbeat age | cycles | intents | placed | days since placement | quiet |
|---|---|---:|---:|---:|---:|---:|---|
| **FTMO** | 2026-07-25T22:05 | 7.9 h | 2654 | 720 | 80 | 24.2 | ❔ UNCHECKED |
| **redacted_account** | 2026-07-24T20:45 | 33.2 h | 2583 | 709 | 67 | 24.2 | ❔ UNCHECKED |

*Quiet is **UNJUDGED**: no --quiet-basis artifact. The 'abnormally quiet' threshold is Session BB's to measure (wave 13, B1950-B1999); this page computes the observable quiet metrics now and adopts BB's threshold the moment the artifact exists.*

<details><summary>The artifact this page will adopt (<code>gtos.live.quiet_basis.v1</code>)</summary>

```json
{
  "schema": "gtos.live.quiet_basis.v1",
  "generated_utc": "<iso>",
  "provenance": "<what measured it>",
  "book_level": {
    "<ACCOUNT>": {
      "expected_fills_per_week": "<float>",
      "alarm_days_without_fill": "<float \u2014 the day count at which silence is abnormal>",
      "alarm_false_trip_probability": "<float \u2014 how often it fires on a HEALTHY book>"
    }
  },
  "per_account_sleeve": {
    "<ACCOUNT>::<sleeve>": {
      "expected_fills_per_week": "<float>",
      "alarm_days_without_fill": "<float>",
      "alarm_false_trip_probability": "<float>"
    }
  }
}
```

A threshold with no measured `alarm_false_trip_probability` is **refused**, not adopted. `FIVE_SLEEVE_OPERATOR_PAGE.md` §S1 is why: a floor that fires 74 % of the time on a healthy sleeve is a coin flip wearing a threshold's clothes.
</details>

## 5 · Per-sleeve economics and the pre-registered stop conditions

Delegated to `scripts/book_sleeve_telemetry.py` (armed 2026-06-18T00:00:00Z) · 300 rows read · **26** post-arming fills.

| sleeve · account | n | net R | gross R/fill (trade / day) | med hold | conditions |
|---|---:|---:|---|---:|---|
| `FTMO::fx_jpy` | 17 | -6.686 | -0.2454 / -0.1944 | 0.56 h | S1a:S S1b:C S2:U S3:C S4:C S5:A |
| `redacted_account::fx_jpy` | 9 | -3.022 | -0.2232 / -0.0005 | 0.51 h | S1a:S S1b:C S2:U S3:C S4:C S5:C |

<details><summary>If you decide to take a sleeve back off</summary>

- **how** — remove the sleeve from `--tags` in scripts/run_book_supervisor.ps1 on the host and restart the supervisor (the orchestrator's ceremony)
- **what_it_stops** — NEW generation only — book_engine.py:493 applies tags
- **what_it_does_NOT_stop** — exit management of an already-open position. `_manageable_pairs` (book_owner.py:2694) calls active_specs(None, ...) with tags NOT applied, and its consumers are manage_open_positions (:1985) and _alert_out_of_universe (:2093) — so a de-tagged sleeve's open position stays adopted and exit-managed. This is the SAFE direction and is why de-arming does not need a flatten.
- **same_day_size_consequence** — narrowing --tags mid-day does NOT reduce that day's Kelly-lite conviction count: RunningConvictionLedger.update_and_count unions the day's firing sleeves and admission.py:1210 takes na = max(na, override). The other four sleeves keep the 5-sleeve multiplier until the decision day rolls. De-arm at a day boundary if the size step matters.
- **never** — do NOT reach for live_broker_authority: false — H8. At HEAD the flatten suppression is book_owner.py:2382 (the marker row; the return follows) and the observe-only degradation is :2544. Flatten first, confirm flat, THEN shut a gate. (CLAUDE.md's :2364-2373 / :2526 are one commit stale; the behaviour is unchanged.)

</details>

---

*This page imported no broker module, opened no socket, and wrote no config. It cannot arm, disarm, resize, flatten or restart anything.*

*Companion pages: `phase4/CANARY_OPERATOR_PAGE.md` (is it armed, is it alive, what is the headroom, is the cost model still right) and `phase11/FIVE_SLEEVE_OPERATOR_PAGE.md` (what is each armed sleeve doing). This page is the union of what they see plus the three reads neither could make without asking you to type the answer.*
