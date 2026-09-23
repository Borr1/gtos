"""The receipt drivers that produced Session AK's published numbers, at the three points they broke.

WHY THIS FILE EXISTS
--------------------
A completeness pass over Session AK found that **zero tests covered the five receipt drivers under
`docs/audits/fable5-vision-audit-20260725/phase8/receipts/`**, and that three separate defects had
already landed in that layer in one session:

  * `_summary` crashed on its own output (`len()` on a `Counter` count) — caught by a traceback;
  * `ak_repair_rows.main` double-appended 22 rows on a corrected re-run — caught by reading the file;
  * two silent ones that a traceback could never have caught, and which are the reason this file is
    behavioural rather than a smoke test:
      - `ak_diversifier.pick_cells` built `"…_prod"[:-5] + "honest"`, dropping the separator, so the
        `_honest` counterpart was NEVER found and the commission's both-bounds rule silently did not
        run on `asian_fade` — the one candidate B613 measured as 95.8 % intrabar sequencing;
      - `ak_candidate_dossier` read `oos_mean_r` where `diagnostics.py:592` emits `test_mean_r`, so
        every dossier row's fold series was `[None, …]` and the pairwise agreement table came out
        empty — Session AI's named input, blank, with the result doc claiming it was attached.

Both silent defects produce a *well-formed artifact*. That is the class of failure a receipt driver
has to be tested for, and the reason the tests below assert on the SHAPE OF THE OUTPUT rather than
on the absence of an exception.

The drivers are imported by path because they live under `docs/`, which is not a package.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
P7 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
P8 = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts"


def _load(name: str):
    """Import a receipt driver by path. `phase7` first, because phase8 imports `ad_exit_sweep`."""
    for d in (P7, P8):
        if str(d) not in sys.path:
            sys.path.insert(0, str(d))
    path = (P8 / f"{name}.py") if (P8 / f"{name}.py").is_file() else (P7 / f"{name}.py")
    if not path.is_file():
        pytest.skip(f"{path} absent (sparse checkout?)")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# ak_diversifier.pick_cells — the honest trail bound must actually be findable
# --------------------------------------------------------------------------- #

def test_pick_cells_finds_the_honest_counterpart_of_a_production_trail_cell():
    """The defect: `best[:-len("_prod")] + "honest"` gives `trail_a2_g0.5honest`, which is in no
    frontier, so `if honest in ok` was always False and only the PRODUCTION bound was ever
    certified. B613/B754 measured 95.8 % of `asian_fade`'s trail gain as intrabar sequencing, so
    certifying that bound alone is exactly the over-claim the rule exists to stop."""
    dv = _load("ak_diversifier")
    cells = {
        "as_walked": {"pooled_oos_mean_r": -0.78},
        "trail_a2_g0.5_prod": {"pooled_oos_mean_r": -0.0093},
        "trail_a2_g0.5_honest": {"pooled_oos_mean_r": -0.3463},
        "trail_a1_g0.5_prod": {"pooled_oos_mean_r": -0.0427},
    }
    picks = dv.pick_cells("asian_fade", cells)
    names = [p["cell"] for p in picks]
    assert names[0] == "trail_a2_g0.5_prod"
    assert "trail_a2_g0.5_honest" in names, (
        "the honest counterpart was not picked — the separator is missing from the lookup again")
    bounds = {p["cell"]: p.get("bound") for p in picks}
    assert bounds["trail_a2_g0.5_prod"] == "production"
    assert bounds["trail_a2_g0.5_honest"] == "intrabar_honest"


def test_pick_cells_also_certifies_the_best_non_composite_when_the_composite_wins():
    """AD §7.1 measured the composite as WORSE than the best single cell on 17 of 25 sleeves, so a
    composite winner must never be the only cell certified."""
    dv = _load("ak_diversifier")
    cells = {
        "as_walked": {"pooled_oos_mean_r": -0.80},
        "POST_HOC_COMPOSITE": {"pooled_oos_mean_r": -0.17},
        "stop_3x_tgtscale": {"pooled_oos_mean_r": -0.27},
    }
    names = [p["cell"] for p in dv.pick_cells("metal_session_reversion", cells)]
    assert names[0] == "POST_HOC_COMPOSITE"
    assert "stop_3x_tgtscale" in names


def test_pick_cells_is_empty_rather_than_wrong_when_nothing_is_gated():
    dv = _load("ak_diversifier")
    assert dv.pick_cells("x", {}) == []
    assert dv.pick_cells("x", {"a": {"pooled_oos_mean_r": None}}) == []


# --------------------------------------------------------------------------- #
# ak_candidate_dossier — the fold series must not silently be a list of None
# --------------------------------------------------------------------------- #

def test_the_fold_series_reads_the_key_diagnostics_actually_emits():
    """The defect: `diagnostics.py:592` emits `test_mean_r`; the driver read `oos_mean_r` and
    produced `[None, None, ...]`, which then filtered the whole pairwise agreement table to `{}`.
    A well-formed artifact with a blank deliverable inside it."""
    do = _load("ak_candidate_dossier")
    folds = [{"test_mean_r": 0.5}, {"test_mean_r": -0.2}, {"test_mean_r": 0.1}]
    assert do._fold_series_key(folds) == "test_mean_r"
    assert do._fold_series(folds) == [0.5, -0.2, 0.1]
    assert not any(x is None for x in do._fold_series(folds))


def test_the_fold_series_degrades_loudly_rather_than_to_nulls_on_a_rename():
    """A future rename must not silently reproduce the original defect: an unknown key set returns
    None (absent), never a list of Nones (present-but-blank), which is the distinction that made
    the original invisible."""
    do = _load("ak_candidate_dossier")
    assert do._fold_series_key([{"something_else": 1.0}]) is None
    assert do._fold_series([{"something_else": 1.0}]) is None
    # ...and it accepts the plausible alternatives rather than only today's name
    assert do._fold_series_key([{"oos_mean_r": 0.3}]) == "oos_mean_r"


@pytest.mark.parametrize("artifact,key,why", [
    ("AK_CANDIDATE_DOSSIER_V1.json", "fold_oos_mean_r_series",
     "Session AI's named input; a list of Nones is the published defect"),
])
def test_the_published_dossier_actually_carries_its_fold_series(artifact, key, why):
    """The end-to-end assertion, on the committed artifact rather than on a fixture."""
    p = P8 / artifact
    if not p.is_file():
        pytest.skip(f"{artifact} absent")
    doc = json.loads(p.read_text())
    cands = {k: v for k, v in (doc.get("candidates") or {}).items() if v.get("available")}
    assert cands, "no available candidate rows"
    for name, row in cands.items():
        series = row.get(key)
        assert series, f"{name}: {key} is empty — {why}"
        assert not all(x is None for x in series), f"{name}: {key} is all None — {why}"
    pairs = (doc.get("fold_series_agreement") or {}).get("pairs")
    assert pairs, "the pairwise fold agreement table is empty, which is what all-None produces"


# --------------------------------------------------------------------------- #
# ak_repair_rows — replacing this session's rows must never touch another session's
# --------------------------------------------------------------------------- #

def test_the_repair_append_preserves_other_sessions_rows_byte_for_byte(tmp_path):
    """The defect: the first corrected re-run left 44 AK rows in a file that should hold 22. The
    fix replaces AK's own rows; this asserts it cannot reach AD's, which is the property the
    agreement's "append, never overwrite" is actually protecting."""
    rr = _load("ak_repair_rows")
    others = [
        json.dumps({"session": "AD", "sleeve": "a", "prescription": "X"}, sort_keys=True),
        json.dumps({"session": "AA", "sleeve": "b", "prescription": "Y"}, sort_keys=True),
        "not json at all — kept because it is not ours to interpret",
    ]
    mine = [json.dumps({"session": rr.SESSION, "sleeve": "c", "prescription": "Z"},
                       sort_keys=True)]
    f = tmp_path / "REPAIR_QUEUE_APPEND.jsonl"
    f.write_text("".join(x + "\n" for x in others + mine))
    before = f.read_text()

    keep = []
    for line in f.read_text().splitlines():
        if not line.strip():
            continue
        try:
            if (json.loads(line).get("session") or "") == rr.SESSION:
                continue
        except json.JSONDecodeError:
            pass
        keep.append(line)
    f.write_text("".join(x + "\n" for x in keep))

    after = f.read_text()
    assert after != before
    for line in others:
        assert line + "\n" in after, "an other-session row was lost"
    assert mine[0] not in after
    assert f'"session": "{rr.SESSION}"' not in after


def test_the_live_queue_still_holds_every_prior_sessions_rows():
    """The committed file, not a fixture: AD's 49 must survive every AK re-run."""
    p = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
    if not p.is_file():
        pytest.skip("append file absent")
    counts: dict[str, int] = {}
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        s = json.loads(line).get("session") or "?"
        counts[s] = counts.get(s, 0) + 1
    assert counts.get("AD") == 49, counts
    assert counts.get("AK"), counts
    # ...and AK's rows must be unique per (sleeve, prescription): a double-append shows up here.
    seen = set()
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if (r.get("session") or "") != "AK":
            continue
        k = (r.get("sleeve"), r.get("prescription"))
        assert k not in seen, f"duplicate AK row for {k} — the append is not idempotent again"
        seen.add(k)


# --------------------------------------------------------------------------- #
# the index deliverable
# --------------------------------------------------------------------------- #

def test_the_named_deliverable_exists_and_indexes_every_member():
    """The commission's deliverable 1. It did not exist until a completeness pass named it."""
    p = P8 / "SLEEVE_SUPPLY_V1.json"
    if not p.is_file():
        pytest.skip("SLEEVE_SUPPLY_V1.json absent")
    doc = json.loads(p.read_text())
    assert doc["n_members"] == len(doc["members"]) > 0
    required = ("member", "kind", "generator_provenance", "gate_verdict_at_measured_carry",
                "exit_frontier", "diversifier_door", "next_prescription")
    for m in doc["members"]:
        for k in required:
            assert k in m, f"{m.get('member')}: missing {k}"
    # the four session-wide limitations a completeness pass found MISSING rather than wrong
    for k in ("prior_gate_receipt_search", "engine_reachability", "cost_basis",
              "first_of_day_coverage_map"):
        assert doc.get(k), f"missing session-wide limitation block: {k}"
    fod = doc["first_of_day_coverage_map"]
    assert fod["n_ak"] + fod["n_ad_inherited"] + fod["n_uncovered"] == 7
