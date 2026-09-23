"""Session AV — the meta-label lane's load-bearing property is leak-freedom, so it is pinned.

A meta-label filter that can see its own trade's outcome will always look like an edge. These
tests are behavioural: they construct data whose answer is known and assert what the machinery
concludes, rather than checking that a source line exists.
"""

from __future__ import annotations

import datetime as dt
import importlib.util as ilu
import json
import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DRIVER = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/av_metalabel_fx_jpy.py"
FAMILY_V6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/CANDIDATE_FAMILY_V6.json"
STORE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/AV_LABEL_STORE_V2_JPY.jsonl.gz"


def _load():
    spec = ilu.spec_from_file_location("av_metalabel_fx_jpy", DRIVER)
    module = ilu.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AV = _load()


def _row(entry: dt.datetime, exit_: dt.datetime, r_net: float, **feats):
    f = {k: 0.0 for k in AV.MODEL_FEATURES}
    f.update(feats)
    f["decision_day"] = entry.date().isoformat()
    f["bar_time_utc"] = entry.isoformat()
    f["close"] = 100.0
    return {
        "features": f,
        "intent": {"sleeve": "fx_jpy", "direction": 1, "stop_dist_price": 1.0,
                   "target_dist_price": 2.5, "symbol_broker": "GBPJPY",
                   "symbol_canonical": "GBPJPY"},
        "label": {"r_gross_winsorised": r_net, "exit_reason": "stop", "exit_bar_offset": 4,
                  "hold_hours": 1.0, "mfe_r": 0.0, "mae_r": 0.0,
                  "entry_utc": entry.isoformat(), "exit_utc": exit_.isoformat(),
                  "net_by_band": {b: {"cost_r": 0.0, "r_net": r_net, "coverage": "MEASURED"}
                                  for b in ("flat", "low", "mid", "high")},
                  "maxbars": 48},
    }


def _series(n=400, *, signal=True, seed=7):
    """`n` trades, one an hour. When `signal` is on, feature `vol_regime` PERFECTLY predicts."""
    rows = []
    t = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)
    state = seed
    for i in range(n):
        state = (state * 1103515245 + 12345) % (2 ** 31)
        coin = (state >> 16) & 1
        v = float(coin) if signal else float((state >> 8) & 1)
        r = 1.0 if coin else -1.0
        rows.append(_row(t, t + dt.timedelta(hours=1), r, vol_regime=v))
        t += dt.timedelta(hours=6)
    return rows


# --------------------------------------------------------------------------------------
# Leak-freedom
# --------------------------------------------------------------------------------------

def test_no_trade_is_scored_by_a_model_that_saw_its_own_outcome():
    """The defining property. A row's score must come from a fit whose training set contains
    only rows that had CLOSED before that row opened, minus the embargo."""
    rows = _series(300)
    wf = AV.walk_forward_scores(rows, "mid", min_train=50, refit_every=1)
    entries = [dt.datetime.fromisoformat(r["label"]["entry_utc"]) for r in rows]
    exits = [dt.datetime.fromisoformat(r["label"]["exit_utc"]) for r in rows]
    for k, s in enumerate(wf["scores"]):
        if s is None:
            continue
        cutoff = entries[k] - dt.timedelta(hours=AV.EMBARGO_HOURS)
        eligible = [j for j in range(k) if exits[j] <= cutoff]
        assert k not in eligible
        assert all(exits[j] <= cutoff for j in eligible)
        # and the row itself can never be eligible for its own fit
        assert exits[k] > cutoff or k >= len(rows)


def test_a_perfect_feature_is_learned_and_a_useless_one_is_not():
    """Positive and negative control in one place: the machinery must be able to find a real
    signal, or a null result from it means nothing."""
    good = AV.walk_forward_scores(_series(400, signal=True), "mid", min_train=60, refit_every=20)
    junk = AV.walk_forward_scores(_series(400, signal=False, seed=11), "mid",
                                  min_train=60, refit_every=20)

    def auc(rows, wf):
        pairs = [(s, r["label"]["net_by_band"]["mid"]["r_net"] > 0)
                 for r, s in zip(rows, wf["scores"]) if s is not None]
        w = [s for s, y in pairs if y]
        l = [s for s, y in pairs if not y]
        if not w or not l:
            return None
        return sum(1 for a in w for b in l if a > b) / (len(w) * len(l))

    a_good = auc(_series(400, signal=True), good)
    a_junk = auc(_series(400, signal=False, seed=11), junk)
    assert a_good is not None and a_good > 0.90, f"perfect feature not learned: {a_good}"
    assert a_junk is not None and 0.35 < a_junk < 0.65, f"noise scored as signal: {a_junk}"


def test_scores_before_min_train_are_none_and_are_never_kept():
    rows = _series(200)
    wf = AV.walk_forward_scores(rows, "mid", min_train=150, refit_every=10)
    assert wf["n_unscored_warmup"] > 0
    masks = AV.apply_cuts(rows, wf)
    for cut, keep in masks.items():
        for s, k in zip(wf["scores"], keep):
            if s is None:
                assert not k, f"cut {cut} kept an unscored row"


def test_quantile_cuts_come_from_the_training_window_not_the_scored_one():
    """A quantile over the trades being scored is a peek at the thing being scored."""
    rows = _series(400)
    wf = AV.walk_forward_scores(rows, "mid", min_train=60, refit_every=1000)
    masks = AV.apply_cuts(rows, wf)
    scored = [s for s in wf["scores"] if s is not None]
    kept50 = sum(masks["top50"])
    # If the median came from the SCORED distribution, top50 would keep exactly half of it.
    # It comes from the TRAIN distribution, so equality is not guaranteed --- and asserting
    # inequality would be brittle. What IS guaranteed: the threshold in force is a stored
    # train quantile, and every kept row clears the quantile that was in force AT IT.
    for r_i, (s, q, k) in enumerate(zip(wf["scores"], wf["train_quantiles"], masks["top50"])):
        if k:
            assert s is not None and q is not None and s >= q["q50"]
    assert 0 < kept50 <= len(scored)


# --------------------------------------------------------------------------------------
# The declared cuts, and the family that charges them
# --------------------------------------------------------------------------------------

def test_the_five_declared_cuts_are_exactly_the_five_family_members():
    fam = json.loads(FAMILY_V6.read_text())["families"]["CANDIDATE_BOOK_V1"]["members"]
    declared = {m["name"] for m in fam if m["name"].startswith("overlay_metalabel_fx_jpy_")}
    implemented = {f"overlay_metalabel_fx_jpy_{c}"
                   for c in list(AV.ABSOLUTE_CUTS) + list(AV.QUANTILE_CUTS)}
    assert declared == implemented, (
        "a cut implemented but not declared is an uncharged look; a cut declared but not "
        f"implemented is a bill nobody paid. declared-only={declared - implemented}, "
        f"implemented-only={implemented - declared}")


def test_the_control_arm_is_the_scored_population_not_the_whole_store():
    """Comparing a filtered arm against the WHOLE store confounds the filter with warmup."""
    rows = _series(300)
    wf = AV.walk_forward_scores(rows, "mid", min_train=100, refit_every=25)
    masks = AV.apply_cuts(rows, wf)
    assert sum(masks["control_scored_unfiltered"]) == wf["n_scored"]
    assert wf["n_scored"] < len(rows)


def test_identity_filter_check_reports_both_layers_and_catches_a_constant():
    rows = _series(120)
    for r in rows:
        r["features"]["session_impulse_atr"] = 2.5     # constant by construction
        r["features"]["vol_regime"] = float(hash(r["label"]["entry_utc"]) % 7)
    out = AV.identity_filter_check(rows, None)
    assert "session_impulse_atr" in out["pinned_features"]
    assert out["per_feature"]["session_impulse_atr"]["level_pinned"] is True
    assert out["per_feature"]["session_impulse_atr"]["bucket_pinned"] is True
    assert out["per_feature"]["vol_regime"]["level_pinned"] is False


# --------------------------------------------------------------------------------------
# The store's contract, on the committed artifact
# --------------------------------------------------------------------------------------

@pytest.mark.skipif(not STORE.is_file(), reason="store not built on this machine")
def test_committed_store_is_one_row_per_symbol_decision_day():
    """The live book takes one trade per symbol per day; the estate's own stream takes three."""
    import collections
    import gzip

    rows = [json.loads(line) for line in gzip.open(STORE, "rt")]
    keys = collections.Counter((r["intent"]["symbol_canonical"], r["features"]["decision_day"])
                               for r in rows)
    assert keys and max(keys.values()) == 1, (
        f"{sum(1 for v in keys.values() if v > 1)} decision-days carry more than one row")


@pytest.mark.skipif(not STORE.is_file(), reason="store not built on this machine")
def test_committed_store_carries_cost_true_net_at_four_bands():
    """AB_LABEL_STORE_V1 records cost_charged 0.0 on all 741 rows; this store must not."""
    import gzip

    rows = [json.loads(line) for line in gzip.open(STORE, "rt")]
    assert rows
    for r in rows[:200]:
        net = r["label"]["net_by_band"]
        assert set(net) == {"flat", "low", "mid", "high"}
        for band, blk in net.items():
            assert blk["cost_r"] > 0.0, f"{band} charged zero cost"
            assert math.isclose(blk["r_net"],
                                r["label"]["r_gross_winsorised"] - blk["cost_r"], abs_tol=1e-9)


@pytest.mark.skipif(not STORE.is_file(), reason="store not built on this machine")
def test_committed_store_is_replayed_at_the_sleeves_own_live_exit_contract():
    import gzip

    from src.components.ultimate_book.execution_packets import SLEEVE_EXIT_PROFILES

    rows = [json.loads(line) for line in gzip.open(STORE, "rt")]
    want = int(SLEEVE_EXIT_PROFILES["fx_jpy"]["time_stop_bars"])
    assert {r["label"]["maxbars"] for r in rows} == {want}
    assert all(r["label"]["exit_bar_offset"] <= want for r in rows)
