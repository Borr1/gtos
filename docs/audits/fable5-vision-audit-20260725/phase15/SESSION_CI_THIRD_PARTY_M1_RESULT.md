# Session CI — third-party M1 ingest and the vp comparability stop (wave 15, B2500–B2549)

**Result: `NOT_EVALUABLE` still.** The time-depth blockade is solved: provenance-bound GER40 and
UK100 M1 now exists locally from 2024-01-01. The strategy gate is not permitted because UK100's
decision-relevant volume-profile POC remains structurally unlike FTMO even after a parameter-free
raw-tick-count repair. Nothing armed. No VPS contact, broker-capable script, protected config edit,
R2-bound edit, March 2026 outcome read, hybrid gate view, strategy outcome, cost arm, incubation
dossier or family bill occurred.

---

## 0. Findings, in the order they decide the work

### 1. The missing history exists now, with its identity and clock stated rather than inferred

Dukascopy's public daily feed supplied **942 payloads and 1,356,480 UTC M1 BID candles per
symbol**, 2024-01-01 through 2026-07-30:

| GTOS symbol | source code | source instrument | quote | what it is not |
|---|---|---|---|---|
| GER40 | `DEUIDXEUR` | Germany 40 Index CFD | EUR | not FTMO, not the cash reference index, not a future |
| UK100 | `GBRIDXGBP` | UK 100 Index CFD | GBP | not FTMO, not the cash reference index, not a future |

The source URLs, official identity/trading-hours pages, fetch date, 1,884 raw-object hashes,
converted hashes, source span and sanctioned `true_utc` sidecars are bound in
`receipts/CI_THIRD_PARTY_SOURCE_V1.json`. The downloader is resumable and hard-capped at two
workers. The landed span fulfills the requested 2024+ depth; it is deliberately not called the
provider's absolute history origin.

The raw and converted bytes are local, under the intentionally ignored
`data/mt5_research_exports/thirdparty_m1_ger40_uk100_20260731/`. The committed receipt is the
portable boundary: re-fetching can reproduce the declared URLs, but an upstream historical
correction may change their hashes.

### 2. Price and sessions match closely; the signal input does not

The overlap comparison was committed with its rule before its result. Both independent pairs have
**90,000 common minute stamps and 100 % broker-stamp coverage**:

| condition | GER40 | UK100 | declared bar |
|---|---:|---:|---:|
| active-minute Jaccard | 0.9556 | 0.9437 | ≥ 0.50 |
| common active share of FTMO | 0.9764 | 0.9759 | ≥ 0.70 |
| close absolute divergence p95 | 3.695 bps | 4.295 bps | ≤ 30 bps |
| common daily profiles | 80 | 79 | ≥ 10 |
| VAH absolute divergence p95 | 37.746 bps | 33.681 bps | reported |
| VAL absolute divergence p95 | 37.135 bps | 38.778 bps | reported |
| **POC absolute divergence p95** | **64.947 bps** | **72.435 bps** | **≤ 40 bps** |

All OHLC, active-gap, session and sample conditions pass. Both POCs fail. Ten of 80 GER40 days
and 14 of 79 UK100 days exceed 40 bps; the POC medians are only 3.121 and 4.326 bps, so the failure
is sparse and discontinuous rather than a simple level offset. That distinction does not rescue a
sleeve whose direction and target are defined from the POC.

The 2026 spring DST transition is **not observable** in the independent overlap: FTMO M1 begins
after the US/EU disagreement ended. The receipt says that instead of transferring true-UTC price
agreement into an unmeasured transition claim.

### 3. The first conversion hid unlike volume semantics behind an estate-compatible column name

Dukascopy's official `IBar.getVolume()` definition is the **sum of volumes at the best price for
each tick in the bar**. FTMO's MT5 `tick_volume`, which GTOS puts into `Bar.v`, is a **tick count**.
The initial converted file had to use the estate CSV field name `tick_volume`; before correction,
that name made the source float look semantically identical when it was not. The source receipt and
sidecars now state the mismatch explicitly and bind the captured official definition.

I did not tune the 40 bps bar after seeing the failure. I declared one no-fit repair: fetch raw
Dukascopy `ITick` objects, count records per UTC minute, keep the already-bound BID OHLC, and re-run
the same structural rule. The overlap-only repair fetched **4,608 of 4,608 hourly objects**,
**12,465,712 ticks**, 59.84 MB compressed, with zero errors:

| repaired condition | GER40 | UK100 | result |
|---|---:|---:|---|
| POC p50 | 2.078 bps | 2.257 bps | reported |
| POC p95 | **37.798 bps** | **59.755 bps** | GER40 passes; UK100 fails |
| days POC > 40 bps | 4 / 80 | 8 / 79 | reported |
| VAH p95 | 18.635 bps | 22.699 bps | both below 40 |
| VAL p95 | 19.447 bps | 25.099 bps | both below 40 |

The repair is real—GER40 crosses the declared bar—and insufficient—UK100 does not. A one-symbol
vp run would be an outcome-informed population change to the declared GER40+UK100 member, not a
data repair. Full 2024+ raw-tick acquisition therefore did not run.

### 4. The honest verdict is `NOT_EVALUABLE`, not `STAYS_DEAD`

CI-4 never crossed its input gate. There are no generated candidates, P1–P5 arms, chronological
folds, maxbars figures, FTMO cost applications, zero-carry counterfactuals or strategy outcomes.
Calling this `STAYS_DEAD` would convert a missing broker-comparable UK100 volume history into an
economic verdict. Calling the strong OHLC overlap sufficient would ignore the only field this
sleeve exists to trade.

The exact unblock is now narrower than “wait until September”: obtain UK100 M1 with
broker-comparable tick-volume structure from at least 2025-12-01, preferably 2024+ for the requested
fold depth, and clear the same overlap rule before generation. That may be a real broker backfill or
a different independent provider. GER40's raw-tick-count surface is evidence that the method can
work; it does not authorize filtering away UK100.

### 5. The candidate-family ratchet did not move

`vp_euidx_pocgrav` is the same `CANDIDATE_BOOK_V1` member whose look Session CA already marked
**TAKEN**. Extending data does not add a member, un-take it, or take it twice: new members **0**,
family high-water delta **0**, billed looks **0**. In this run even the intended unbilled iteration
row is absent, because no strategy outcome existed to log. The data/comparability work is a source
qualification, not a gate look wearing a different name.

No `REVIVAL_CANDIDATE` exists, so the commission's CC-shape incubation dossier is correctly absent.

---

## 1. Delivered evidence

| artifact | role |
|---|---|
| `receipts/ci_thirdparty_m1.py` | resumable two-worker candle ingest, deterministic conversion, unchanged structural comparator, splice refusal and terminal verifier |
| `receipts/CI_THIRD_PARTY_SOURCE_V1.json` | exact source identity, clock, URLs, raw/converted hashes and volume-semantics disclosure |
| `receipts/CI_THIRD_PARTY_OVERLAP_V1.json` | original independent OHLC/gap/session/DST/POC comparison and `gate_permitted: false` |
| `receipts/ci_tick_count_repair.py` | preregistered, parameter-free raw-tick-count repair |
| `receipts/CI_TICK_COUNT_FETCH_OVERLAP_V1.json` | 4,608-object / 12.47-million-tick manifest summary |
| `receipts/CI_TICK_COUNT_SOURCE_OVERLAP_V1.json` | repaired converted hashes and sidecars |
| `receipts/CI_TICK_COUNT_REPAIR_OVERLAP_V1.json` | unchanged-rule partial repair and final false gate |
| `receipts/CI_THIRD_PARTY_VERIFY_V1.json` | PASS: source/repair hashes, both false gates, no downstream artifacts, no protected/R2 edits |
| `receipts/ci_vp_generate.py`, `receipts/ci_vp_gate.py` | prepared but deliberately unexecuted offline CI-4 drivers; the former refuses March-touching label horizons before replay, the latter inherits CA's gate rather than re-authoring it |
| `tests/research_infra/test_ci_thirdparty_m1.py` | decoder, UTC/sidecar/front-door, worker cap, comparator, tick-count repair, March fence and verdict tests |
| `receipts/SESSION_CI_AB_RECEIPT.md` | mandatory scoped A/B, tool-emitted `gtos-ab-receipt-v1` fence |
| `receipts/SESSION_CI_COPYBACK_AB_RECEIPT.md` | shared pre-existing surface, actual copy-back: 9 → 9 passed, 0 regressed |

`CI_THIRD_PARTY_VERIFY_V1.json` records 43 R2-bound paths, **2 standing drifted ledgers**, and zero
CI-changed bound paths. No `src/` path, protected config, or broker-capable path changed.

---

## 2. What I got wrong

1. **I initially called the Dukascopy candle float tick volume because the estate CSV column is
   named `tick_volume`.** That was false. The official API says it is summed best-price volume.
   The mistake mattered: POC is the decision input, and provider-local volume semantics are exactly
   where the first comparison failed. I corrected the source receipt and sidecars, captured the
   official definition, and tested the only parameter-free semantic repair before stopping.

2. **My first validator design treated OHLC/gaps as the structural decision.** Those are necessary
   and not sufficient for a volume-profile sleeve. Before running it, I added the production POC/VA
   computation independently on each provider and committed a 40 bps POC bar. Without that change,
   this session would have gated unlike data and likely called the extra folds evidence.

3. **My first downloader opened fresh TLS for every 10–20 KB daily object.** The projected runtime
   was hours. One persistent session per worker preserved the two-connection ceiling and completed
   the same hash-validated object set. Network plumbing is not evidence, but bad plumbing can stop
   evidence from existing.

4. **My first deterministic-artifact claim was wrong.** `gzip.open` embeds wall-clock mtime, so two
   identical conversions had different hashes. The writer now fixes gzip mtime to zero, and the
   behavioral test converts twice and requires identical SHA-256.

5. **The prepared generator had an unqualified `Counter` in final receipt assembly.** It would have
   spent the full generation run and then failed at the last line. A pre-run audit caught it and the
   fix was committed before any CI-4 run. The stopped structural gate means that driver remains
   deliberately unexecuted.

---

## 3. A/B

**0 bad → 0 bad, 0 regressed.** `receipts/SESSION_CI_AB_RECEIPT.md` compares the committed
whole-suite ZERO baseline (12,476 passed / 0 bad) to the mechanically computed two-file after
scope (**22 passed / 0 bad**) and carries the tool-emitted `gtos-ab-receipt-v1` fence. The new
CI-only test cannot exist on the before side; the shared pre-existing citation test therefore has
its own mandated, same-scope copy-back receipt at `receipts/SESSION_CI_COPYBACK_AB_RECEIPT.md`:
**9 → 9 passed, 0 regressed**, with every final path byte-compared after restoration and no
`git checkout` used.

---

## 4. Handoff

1. **Do not run `ci_vp_generate.py` or `ci_vp_gate.py` on the current surface.** The terminal
   verifier should continue to say `STOPPED_STRUCTURAL_DIVERGENCE`.
2. **Acquire one honest UK100 alternative, not a threshold tweak:** at least 2025-12-01 through the
   broker join, preferably 2024+, with a declared clock/instrument/volume definition. Run it through
   the same `_overlap_for` rule. If it fails, stop again.
3. **If and only if both symbols pass**, fetch/bind the full repaired span, build the hybrid view,
   run the prepared generation control (all 33 CA post-join decisions must reproduce exactly), then
   inherit CA P1–P5 and FTMO pricing. The existing `CANDIDATE_BOOK_V1` look stays TAKEN.
4. Preserve the local data root or re-fetch from the bound manifests. The committed repository does
   not contain 118+ MB of raw/converted market data.
5. Nothing needs carrying to a VPS. Nothing needs a token, config ceremony, arm, restart or dossier.
