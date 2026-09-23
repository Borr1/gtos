# redacted_account pull list — Challenge-true tape LANDED; Wave E **PROVED_SHADOW**

Owner lock 2026-09-17: **shadow score first, then wire.** These pulls feed
the prove receipt (`scripts/jev_wire_prove.py`). They do not apply a wire.

**2026-09-17T10:52:04Z — both wires `PROVED_SHADOW` (tie). `wire_apply` still false.
Ticket 293332188 leave orig / log_only / live_size_tilt=1.0. APPLY waits owner NAME.**

Do not place, remint, flatten, or write inbox from these pulls.

1. Live XAUUSD M15 / H4 / D1 **LANDED** (`XAUUSD_*.csv`, 1597/75/56). `time_utc` already −3h. Do not use April repo M15.
2. Slate body **LANDED** `slate_20260917T104105Z_bddc8ff9fad4a254.json` (`slate_id` `bddc8ff9fad4a254`).
3. `events_since_20260915.jsonl` landed (7729). Optional; deals used for score.
4. Host `--tags` argv + `$KILL` / `F5_HARD_OFF_SLEEVES` (BTCUSD `kz_london_cry` filled today — LABEL as host drift, do not invent a new choke)
5. Deals **LANDED** `deals_since_20260909.jsonl` (46 closed / 1 open). Open `293332188` skipped here — sit owns leave-orig.
6. Host `f5_high_calendar.v1` ingested. Challenge news axis.
7. **LANDED 2026-09-18** Challenge-true M15/H4 for `EURUSD`, `GBPUSD`, `EURGBP`, `USDJPY`, `GBPJPY`, `US30` under `multi/` (`time_utc` already −3h). `n_non_xau_sufficient=45` after rematerialize. GBPJPY has tape and no pack rows. UK100 / BTCUSD / ETHUSD still not landed. Loader + `gold_state.peers` (`HOST_A_PEERS_USDJPY.md`) consume the landed USDJPY pair. Receipt `judgment/astra/oss_harvest/MULTI_BOOKS_LANDING_20260918.json`. Do **not** pull BTCUSD as a trade surface (house_hard_off). `ENV-US30` stays. Do **not** invent DXY/yields/OB. Do **not** wear April `data/historical/USDJPY_*.csv`.
8. **Work item:** news_calendar repair = official FF this-week snapshot only. Never overwrite June `data/news_calendar.json`. Empty spine ≠ no HIGH.
9. **Work item:** f5-live ceremony prep landed (`wires/F5_LIVE_CEREMONY_PREP.md`). APPLY still closed. Ticket 293332188 leave orig. BOE ~11:01Z still open ~+0.6R leave orig.
10. **TypeSafe:** key already provided on redacted_account **and VPS `redacted_host`** (fp `00000000`: User env, `secrets\TYPESAFE_API_KEY.txt`, `.env.typesafe`). This Cloud VM still does not inherit it (`http=never_sent`, **not a 403**). Route `python scripts/jev_host_systemone_shadow.py` through redacted_account/VPS. No more `abstain:no_key` as a limitation.

Re-run:

```bash
python3 scripts/jev_challenge_shadow.py \
  --sit judgment/astra/lab/challenge_shadow_20260917/sit_20260917.json \
  --slate judgment/astra/lab/challenge_shadow_20260917/slate_20260917T104105Z_bddc8ff9fad4a254.json \
  --deals judgment/astra/lab/challenge_shadow_20260917/deals_since_20260909.jsonl
python3 scripts/jev_wire_prove.py
```
