"""Behavioural tests for `scripts/book_sleeve_telemetry.py` and the AS-1 stop conditions.

Every test here drives the REAL evaluator against synthetic fills and asserts on what it decides.
None of them greps the source: a source-string assertion passes against a wrong implementation, and
the whole point of this tool is that it must be right on the first post-arming export.

The properties pinned, in the order they matter:

  1. zero post-arming fills is UNCHECKED and exit 3, never CLEAN and 0.
  2. the wrong `--tags` is a STOP, and it is a STOP even when every sleeve looks healthy.
  3. S2 needs BOTH weightings negative — a trade-weighted-only loss on a day-clustered corpus
     does not trip it, which is the exact repair the fx_jpy live record forced.
  4. the pre-arming prior never enters a stop-condition evaluation.
  5. the S1 floor trips on the pre-registered number and not on a number this test invents.
  6. the exact sign-flip permutation reports its own resolution floor and refuses to admit at it.
  7. the de-arm text says what removing a tag does NOT do, because that is the half that costs
     money if it is wrong.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/audits/fable5-vision-audit-20260725"
CONDITIONS = AUDIT / "phase11/receipts/FIVE_SLEEVE_STOP_CONDITIONS_V1.json"
BASIS = AUDIT / "phase11/receipts/AS_LIVE_SLEEVE_BASIS_V1.json"
#: The two accounts no longer run the same book. FTMO gained
#: `mx_btcusd_d1_donchian_20_breakout` on --frontier-exits at 2026-07-31 ~01:26Z
#: (phase13/receipts/MX_ACTIVATION_20260731.md); redacted_account was untouched by that
#: ceremony and runs the four. Both sets postdate the fx_jpy pull (2026-07-30 ~14:57Z).
ARMED_UTC = "2026-07-31T01:26:00Z"


def _load_module():
    path = ROOT / "scripts/book_sleeve_telemetry.py"
    spec = importlib.util.spec_from_file_location("book_sleeve_telemetry", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["book_sleeve_telemetry"] = mod
    spec.loader.exec_module(mod)
    return mod


tel = _load_module()


pytestmark = pytest.mark.skipif(
    not CONDITIONS.is_file() or not BASIS.is_file(),
    reason="AS-1 artifacts absent; generate with phase11/receipts/as_live_basis.py",
)


# ---------------------------------------------------------------------------
class Args:
    """The argparse Namespace `build_page` consumes, without argparse."""

    def __init__(self, fills=None, armed_utc=ARMED_UTC, ftmo=None, fn=None):
        self.fills = fills
        self.conditions = CONDITIONS
        self.basis = BASIS
        self.armed_utc = armed_utc
        self.launch_tags_ftmo = ftmo
        self.launch_tags_redacted_account = fn
        self.output = None
        self.json = None


CORE4 = "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert"
MX = "mx_btcusd_d1_donchian_20_breakout"
#: FTMO's armed `--tags`, and redacted_account's. `ARMED` is kept as the FTMO one because
#: every test that used it was written for the account with the larger book.
ARMED_FTMO = f"{CORE4},{MX}"
ARMED_FN = CORE4
ARMED = ARMED_FTMO


def fill(sleeve, account, *, day, gross, net, cost=0.05, hold_h=1.0, reason="sl",
         swap=0.0, hour=8):
    """One row in the shape `w7_live_forensics.py` emits."""
    entry = dt.datetime(2026, 8, day, hour, 0, tzinfo=dt.timezone.utc)
    exit_ = entry + dt.timedelta(hours=hold_h)
    return {
        "sleeve_id": sleeve, "account": account,
        "day_key_broker_server": f"2026-08-{day:02d}", "day_key_utc": f"2026-08-{day:02d}",
        "entry_time_utc": entry.isoformat(), "exit_time_utc": exit_.isoformat(),
        "gross_r": gross, "realized_r": net, "cost_r": cost,
        "holding_seconds": hold_h * 3600.0, "close_reason": reason, "swap": swap,
        "stack_era": "w7_book",
    }


def write(tmp_path, rows):
    p = tmp_path / "fills.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return p


# ---------------------------------------------------------------------------
# 1. silence is UNCHECKED, not clean
# ---------------------------------------------------------------------------
def test_no_post_arming_fill_is_unchecked_and_exit_3(tmp_path):
    page = tel.build_page(Args(fills=write(tmp_path, []), ftmo=ARMED_FTMO, fn=ARMED_FN))
    assert page["n_post_arming_fills"] == 0
    assert page["verdict"] == tel.UNCHECKED
    assert page["exit_code"] == 3, "silence must never render as a clean bill"
    for row in page["per_sleeve"].values():
        assert row["checks"]["ALL"]["state"] == tel.UNCHECKED


def test_the_historical_corpus_contributes_zero_post_arming_fills():
    """The only live corpus on this machine predates arming by a month. It must land entirely in
    the prior, or the tool would present a pre-arming loss as a post-arming verdict."""
    corpus = AUDIT / "phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl"
    if not corpus.is_file():
        pytest.skip("live corpus absent")
    page = tel.build_page(Args(fills=corpus, ftmo=ARMED_FTMO, fn=ARMED_FN))
    assert page["n_rows_read"] > 0
    assert page["n_post_arming_fills"] == 0
    assert page["verdict"] == tel.UNCHECKED
    # and the prior IS populated for the one armed sleeve that has a live record
    # `fx_jpy` was PULLED on 2026-07-30 ~14:57Z, so the tool must not carry a row for it at
    # all — not a clean one and not a quiet one. Its 21 FTMO / 11 redacted_account live fills are
    # the only live record any armed sleeve ever had, and they belong to a book that is no
    # longer running; presenting them under the current armed set would be the pre-arming
    # merge this whole tool exists to refuse, one level up.
    assert "FTMO::fx_jpy" not in page["prior"]
    assert "redacted_account::fx_jpy" not in page["prior"]
    assert page["prior"]["FTMO::crypto"] is None
    # and the sleeves that ARE armed all have a prior slot, empty or not
    for tag in CORE4.split(","):
        assert f"FTMO::{tag}" in page["prior"]


# ---------------------------------------------------------------------------
# 2. composition is a STOP and it dominates
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tags,expect_stop", [
    (ARMED, False),
    ("crypto,energy_agri,sub_xvol_pullback", True),                     # the pre-expansion three
    ("", True),                                                          # falsy -> ALL BUILT
    (CORE4 + ",metals_core", True),                                      # one sleeve too many
    (CORE4, True),        # redacted_account's book on FTMO: right sleeves, wrong ACCOUNT's set
])
def test_composition_verdict(tmp_path, tags, expect_stop):
    page = tel.build_page(Args(fills=write(tmp_path, []), ftmo=tags, fn=ARMED_FN))
    stops = [f for f in page["findings"] if f["condition"] == "S6"]
    assert bool(stops) is expect_stop
    if expect_stop:
        assert stops[0]["level"] == tel.STOP
        assert page["exit_code"] == 1


def test_composition_unchecked_when_tags_not_supplied(tmp_path):
    page = tel.build_page(Args(fills=write(tmp_path, [])))
    for blk in page["composition"]["per_account"].values():
        assert blk["state"] == tel.UNCHECKED
    assert page["exit_code"] == 3


def test_a_healthy_book_with_wrong_tags_still_stops(tmp_path):
    """The condition that makes everything else meaningless must not be outvoted by good news."""
    rows = [fill("crypto", "ftmo", day=d, gross=2.0, net=1.9, reason="tp") for d in range(1, 26)]
    page = tel.build_page(Args(fills=write(tmp_path, rows), ftmo="crypto", fn=ARMED))
    assert page["verdict"] == tel.STOP
    assert any(f["condition"] == "S6" for f in page["findings"])


# ---------------------------------------------------------------------------
# 3. S2 requires BOTH weightings — the fx_jpy repair
# ---------------------------------------------------------------------------
def test_s2_does_not_trip_when_only_the_trade_weighting_is_negative(tmp_path):
    """The exact shape of the live fx_jpy record: losing days carry many fills, winning days one.

    Trade-weighted negative, day-weighted positive. A tripwire reading only the first would call
    this sleeve dead on a number its own day structure does not support.
    """
    rows = []
    for d in range(1, 11):          # 10 losing days x 4 fills at -1.0  -> -40 R
        rows += [fill("crypto", "ftmo", day=d, gross=-1.0, net=-1.05, hour=8 + i)
                 for i in range(4)]
    for d in range(11, 21):         # 10 winning days x 1 fill at +2.5  -> +25 R
        rows.append(fill("crypto", "ftmo", day=d, gross=2.5, net=2.45, reason="tp"))
    # trade-weighted -15/50 = -0.30 ; day-weighted (10*-1.0 + 10*+2.5)/20 = +0.75
    page = tel.build_page(Args(fills=write(tmp_path, rows), ftmo=ARMED_FTMO, fn=ARMED_FN))
    chk = page["per_sleeve"]["FTMO::crypto"]["checks"]["S2"]
    assert chk["gross_trade_weighted"] < 0
    assert chk["gross_day_weighted"] > 0
    assert chk["both_negative"] is False
    assert chk["state"] == tel.CLEAN
    assert not [f for f in page["findings"] if f["condition"] == "S2"]


def test_s2_trips_when_both_weightings_are_negative(tmp_path):
    rows = [fill("crypto", "ftmo", day=d, gross=-0.4, net=-0.45) for d in range(1, 26)]
    page = tel.build_page(Args(fills=write(tmp_path, rows), ftmo=ARMED_FTMO, fn=ARMED_FN))
    chk = page["per_sleeve"]["FTMO::crypto"]["checks"]["S2"]
    assert chk["both_negative"] is True and chk["state"] == tel.STOP
    f = [x for x in page["findings"] if x["condition"] == "S2"][0]
    assert "before any cost" in f["why"]
    # the power disclosure must be present and must name the floor
    assert "floor" in f["why"]


def test_s2_is_unchecked_below_its_declared_sample(tmp_path):
    rows = [fill("crypto", "ftmo", day=d, gross=-1.0, net=-1.05) for d in range(1, 6)]
    page = tel.build_page(Args(fills=write(tmp_path, rows), ftmo=ARMED_FTMO, fn=ARMED_FN))
    chk = page["per_sleeve"]["FTMO::crypto"]["checks"]["S2"]
    assert chk["state"] == tel.UNCHECKED and "needs >=" in chk["reason"]


# ---------------------------------------------------------------------------
# 4. the prior never enters an evaluation
# ---------------------------------------------------------------------------
def test_pre_arming_losses_do_not_trip_any_condition(tmp_path):
    """40 pre-arming fills at -1 R each. Every stop condition must stay UNCHECKED."""
    rows = []
    for d in range(1, 21):
        e = dt.datetime(2026, 7, d, 8, tzinfo=dt.timezone.utc)
        rows += [{**fill("crypto", "ftmo", day=1, gross=-1.0, net=-1.1),
                  "entry_time_utc": e.isoformat(),
                  "exit_time_utc": (e + dt.timedelta(hours=1)).isoformat(),
                  "day_key_broker_server": f"2026-07-{d:02d}"} for _ in range(2)]
    page = tel.build_page(Args(fills=write(tmp_path, rows), ftmo=ARMED_FTMO, fn=ARMED_FN))
    assert page["n_post_arming_fills"] == 0
    assert not [f for f in page["findings"] if f["condition"].startswith("S1")]
    assert not [f for f in page["findings"] if f["condition"] == "S2"]
    assert page["verdict"] == tel.UNCHECKED
    assert page["prior"]["FTMO::crypto"]["n_fills"] == 40


# ---------------------------------------------------------------------------
# 5. S1 trips on the pre-registered floor
# ---------------------------------------------------------------------------
def test_s1a_trips_at_the_committed_risk_floor_and_not_before(tmp_path):
    conds = json.loads(CONDITIONS.read_text())
    floor = float(conds["conditions"]["S1a_risk_floor"]
                  ["per_sleeve_account"]["FTMO::sub_mid_dn_revert"]["cumulative_net_r_floor"])
    assert floor < 0
    per = floor / 10.0          # ten fills lands exactly on the floor

    nine = [fill("sub_mid_dn_revert", "ftmo", day=d, gross=per + 0.05, net=per) for d in range(1, 10)]
    page = tel.build_page(Args(fills=write(tmp_path, nine), ftmo=ARMED_FTMO, fn=ARMED_FN))
    chk = page["per_sleeve"]["FTMO::sub_mid_dn_revert"]["checks"]["S1a"]
    assert chk["state"] == tel.CLEAN and chk["headroom_r"] > 0

    ten = nine + [fill("sub_mid_dn_revert", "ftmo", day=10, gross=per + 0.05, net=per)]
    page = tel.build_page(Args(fills=write(tmp_path, ten), ftmo=ARMED_FTMO, fn=ARMED_FN))
    chk = page["per_sleeve"]["FTMO::sub_mid_dn_revert"]["checks"]["S1a"]
    assert chk["state"] == tel.STOP
    assert chk["net_r_total"] == pytest.approx(floor, abs=1e-9)
    assert page["exit_code"] == 1


def test_a_risk_floor_trip_discloses_its_own_false_alarm_rate(tmp_path):
    """The whole reason S1a and S1b are separate. A trip on the risk floor must SAY that it fires
    most of the time on a healthy sleeve, or a reader will treat it as evidence."""
    conds = json.loads(CONDITIONS.read_text())
    floor = float(conds["conditions"]["S1a_risk_floor"]
                  ["per_sleeve_account"]["FTMO::sub_mid_dn_revert"]["cumulative_net_r_floor"])
    rows = [fill("sub_mid_dn_revert", "ftmo", day=d, gross=floor / 5 + 0.05, net=floor / 5)
            for d in range(1, 7)]
    page = tel.build_page(Args(fills=write(tmp_path, rows), ftmo=ARMED_FTMO, fn=ARMED_FN))
    f = [x for x in page["findings"] if x["condition"] == "S1a"][0]
    assert "says nothing about the sleeve" in f["why"].lower()
    assert "%" in f["why"], "the measured false-alarm rate must appear in the finding"


def test_the_evidence_floor_is_deeper_than_the_risk_floor_where_the_sleeve_is_noisy(tmp_path):
    """On the near-zero-expectancy sleeves the two must differ, and by a lot — that gap IS the
    finding. On the high-expectancy sleeves they may coincide, and that is also correct."""
    conds = json.loads(CONDITIONS.read_text())
    a = conds["conditions"]["S1a_risk_floor"]["per_sleeve_account"]
    b = conds["conditions"]["S1b_evidence_floor"]["per_sleeve_account"]
    assert b["FTMO::fx_jpy"]["evidence_floor_r"] < a["FTMO::fx_jpy"]["cumulative_net_r_floor"] - 5
    assert b["FTMO::sub_mid_dn_revert"]["evidence_floor_r"] < \
        a["FTMO::sub_mid_dn_revert"]["cumulative_net_r_floor"] - 5
    # and on crypto, whose expectancy dwarfs its dispersion, the risk floor is already safe
    assert b["FTMO::crypto"]["evidence_floor_r"] == pytest.approx(
        a["FTMO::crypto"]["cumulative_net_r_floor"], abs=0.01)


def test_every_floor_publishes_a_measured_false_trip_rate():
    """A stop condition without a measured false-alarm rate is a number somebody liked."""
    conds = json.loads(CONDITIONS.read_text())
    for cid in ("S1a_risk_floor", "S1b_evidence_floor"):
        for key, row in conds["conditions"][cid]["per_sleeve_account"].items():
            p = row.get("measured_false_trip_probability_within_60_fills")
            assert p is not None, f"{cid} {key} has no measured false-trip rate"
            assert 0.0 <= p <= 1.0
    # and the evidence floors all sit at or under the declared target
    target = conds["conditions"]["S1b_evidence_floor"]["method"]["target_false_trip_rate"]
    for key, row in conds["conditions"]["S1b_evidence_floor"]["per_sleeve_account"].items():
        assert row["measured_false_trip_probability_within_60_fills"] <= target + 0.01, key


def test_s1a_floor_is_not_a_preference(tmp_path):
    """Every risk floor must be derivable from the basis field it names, so nobody moves it
    quietly."""
    conds = json.loads(CONDITIONS.read_text())
    basis = json.loads(BASIS.read_text())
    for key, row in conds["conditions"]["S1a_risk_floor"]["per_sleeve_account"].items():
        if row.get("added_by"):
            # Session CA's rows are derived from the gate's own diagnose=True decomposition
            # rather than from AS's carry_basis (which mixes two archives and has no entry
            # for a sleeve with no W7 cache rows). The floor must still follow the SAME
            # formula from the expectancy the row itself publishes.
            e = row["archive_net_r_per_trade_at_measured_carry"]
            assert row["cumulative_net_r_floor"] == pytest.approx(
                -max(3.0, 12.0 * abs(e)), abs=1e-3), key
            continue
        cb = basis["carry_basis"][key]
        expect = cb["archive_gross_r_per_trade"] - cb["true_cost_ex_swap_r"] \
            - cb["swap_r_per_night"] * cb["measured_nights_mean"]
        assert row["archive_net_r_per_trade_at_measured_carry"] == pytest.approx(expect, abs=1e-5)
        assert row["cumulative_net_r_floor"] == pytest.approx(
            -max(3.0, 12.0 * abs(expect)), abs=1e-3)


# ---------------------------------------------------------------------------
# 6. the permutation reports its floor and cannot admit at it
# ---------------------------------------------------------------------------
def test_signflip_reports_its_resolution_floor():
    out = tel.signflip_p([-1.0] * 4, 0.0)
    assert out["n_blocks"] == 4 and out["achievable_assignments"] == 16
    assert out["resolution_floor"] == pytest.approx(1 / 16)
    assert out["p"] == pytest.approx(1 / 16)
    assert out["at_or_below_floor"] is True, \
        "an all-negative 4-block sample sits ON its own floor and must be flagged as such"


def test_signflip_refuses_only_when_there_is_nothing_to_test():
    assert tel.signflip_p([], 0.0)["p"] is None


def test_signflip_above_the_exact_limit_still_reports_a_p():
    """More data must not produce a weaker statement. A first cut returned None above 20 blocks —
    which is the NORMAL case after a month of trading, not an edge case."""
    out = tel.signflip_p([-0.4] * 25, 0.0)
    assert out["p"] is not None
    assert out["method"].startswith("seeded_monte_carlo")
    assert out["achievable_assignments"] == 2 ** 25
    assert out["resolution_floor"] == pytest.approx(1 / 200_000)
    assert out["p"] <= out["resolution_floor"], "25 all-negative blocks is as extreme as it gets"
    assert out["at_or_below_floor"] is True


def test_signflip_monte_carlo_is_deterministic():
    """The seed is derived from the data, so the number on the page is reproducible."""
    blocks = [0.3, -1.2, 0.05, 2.0] * 6 + [-0.4]
    assert len(blocks) > tel._EXACT_BLOCK_LIMIT
    a = tel.signflip_p(blocks, 0.0)
    b = tel.signflip_p(list(blocks), 0.0)
    assert a["p"] == b["p"] and a["method"] == b["method"]


def test_signflip_monte_carlo_agrees_with_the_exact_test_at_the_boundary():
    """At 20 blocks the exact test runs; the MC on the same data must land close to it."""
    blocks = [0.5, -1.0, 0.2, -0.3, 0.9, -1.4, 0.1, 0.7, -0.6, 0.4,
              -0.2, 1.1, -0.8, 0.3, -1.2, 0.6, -0.1, 0.8, -0.5, 0.2]
    exact = tel.signflip_p(blocks, 0.0)
    assert exact["method"] == "exact_enumeration"
    saved = tel._EXACT_BLOCK_LIMIT
    try:
        tel._EXACT_BLOCK_LIMIT = 5
        mc = tel.signflip_p(blocks, 0.0)
    finally:
        tel._EXACT_BLOCK_LIMIT = saved
    assert mc["method"].startswith("seeded_monte_carlo")
    assert mc["p"] == pytest.approx(exact["p"], abs=0.01)


def test_signflip_is_shift_equivariant():
    """p against a null of m must equal p of the shifted sample against zero. If this fails, every
    'vs archive gross' number on the page is wrong."""
    blocks = [0.4, -0.2, 0.9, -1.1, 0.05]
    a = tel.signflip_p(blocks, 0.3)["p"]
    b = tel.signflip_p([x - 0.3 for x in blocks], 0.0)["p"]
    assert a == pytest.approx(b)


# ---------------------------------------------------------------------------
# 7. the de-arm text carries the expensive half
# ---------------------------------------------------------------------------
def test_de_arm_text_states_what_removing_a_tag_does_not_do():
    conds = json.loads(CONDITIONS.read_text())
    da = conds["de_arm_mechanism"]
    assert "exit management" in da["what_it_does_NOT_stop"]
    assert "active_specs(None" in da["what_it_does_NOT_stop"]
    assert "max(na, override)" in da["same_day_size_consequence"]
    assert "live_broker_authority" in da["never"] and "Flatten first" in da["never"]


def test_de_arm_claims_match_the_source():
    """The source claims the de-arm procedure rests on, checked against the files.

    Rewritten at the wave-12 train (line numbers -> structure), and REWRITTEN AGAIN
    2026-08-25 (root cause: STALE EXPECTATION), because the previous version's own failure
    message asked for exactly this: "the de-arm procedure's claim that a de-tagged sleeve
    stays exit-managed must be re-verified". Re-verified: THE CLAIM IS INVERTED on the live
    lineage. The f5-live truth snapshot (`68bad3751`, committed under
    docs/audits/fable-20260825/OWNER-GRANT-20260825.md; shipped `79c8ecb75`,
    CEREMONY-RECEIPT-20260825.md) scoped `_manageable_pairs` to the launcher-set
    `_generation_tags` — manage-what-you-generate. That scoping is load-bearing for the F5
    book: its tag set includes the dsp_*/xa_* cohorts which `active_specs(None)` does NOT
    resolve (measured: 11 sleeves, no dsp/xa), so the OLD tag-blind resolver would have
    left every open dsp/xa position unmanaged. The cost, pinned below so nobody trusts the
    old receipt: a DE-TAGGED sleeve's open position now leaves the manage scope on restart
    (broker SL/TP set at entry still stands — H8; `_alert_out_of_universe` fires when its
    symbol leaves the universe). De-arm therefore means FLATTEN FIRST or keep the tag until
    flat; FIVE_SLEEVE_STOP_CONDITIONS_V1.json's `what_it_does_NOT_stop` describes the
    pre-snapshot world and is superseded on this tree.
    """
    engine = (ROOT / "src/components/ultimate_book/book_engine.py").read_text().splitlines()
    owner_path = ROOT / "src/components/ultimate_book/book_owner.py"
    owner = owner_path.read_text().splitlines()
    # 1. generation applies tags: an active_specs( call whose next line passes tags,
    assert any(
        "active_specs(" in ln and "tags," in engine[i + 1]
        for i, ln in enumerate(engine[:-1])
    ), "book_engine.py no longer shows a tags-filtered active_specs call; re-verify the de-arm procedure"

    # 2. exit management scopes to the launcher's generation tags — BEHAVIOURAL, on the real
    #    resolver: a sleeve outside _generation_tags contributes no manageable pair.
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    class _Stub:
        base_config = {}
        def _candidate_book_sleeves(self): return ()
        def _market_expansion_sleeves(self): return ()
        def _profile_supports_symbol(self, s): return True

    tagged = _Stub(); tagged._generation_tags = ("crypto",); tagged._manageable_pairs_cache = None
    assert {sl for _, sl in UltimateBookOwner._manageable_pairs(tagged)} == {"crypto"}, \
        "_manageable_pairs no longer scopes to _generation_tags; the manage surface and the " \
        "generation surface have diverged — re-verify the de-arm procedure"
    detagged = _Stub(); detagged._generation_tags = ("energy_agri",); detagged._manageable_pairs_cache = None
    assert "crypto" not in {sl for _, sl in UltimateBookOwner._manageable_pairs(detagged)}, (
        "a de-tagged sleeve is back in the manage scope: if this is deliberate, the de-arm "
        "doctrine (flatten first) and this test must BOTH be revisited together"
    )
    unscoped = _Stub(); unscoped._generation_tags = None; unscoped._manageable_pairs_cache = None
    assert "crypto" in {sl for _, sl in UltimateBookOwner._manageable_pairs(unscoped)}, \
        "an untagged (fail-open) worker must still manage the BUILT universe"

    # 3. the wiring that feeds it: the launcher hands its resolved tag scope to the owner.
    launcher_src = (ROOT / "src/components/ultimate_book/launcher.py").read_text()
    assert "self.owner._generation_tags = generation_tags or None" in launcher_src, \
        "BookLauncher no longer wires _generation_tags; _manageable_pairs would silently " \
        "fall back to the 11-sleeve BUILT universe and drop the dsp_*/xa_* cohorts"

    # 4. the safety net that replaced the old stays-managed guarantee: the out-of-universe
    #    alert derives its universe from the SAME scoped resolver, so a de-tagged sleeve
    #    whose symbol leaves the universe is at least surfaced.
    owner_src = "\n".join(owner)
    alert_body = owner_src.split("def _alert_out_of_universe", 1)[1].split("\n    def ", 1)[0]
    assert "self._manageable_pairs()" in alert_body, \
        "_alert_out_of_universe no longer reads _manageable_pairs; an orphaned de-tagged " \
        "position would ride the broker SL/TP with no alert at all"

    # 5. the one remaining active_specs(None...) site is DEAD CODE (`_manageable_symbols`,
    #    zero callers — FIVE_SLEEVE_STOP_CONDITIONS_V1.json `citation_corrected` already
    #    recorded it): it must not be cited as exit-management coverage again.
    assert "self._manageable_symbols(" not in owner_src, \
        "_manageable_symbols grew a caller; if exit management now uses it, re-derive the " \
        "de-arm claims (it resolves active_specs(None) and would widen the manage scope)"


# ---------------------------------------------------------------------------
# the armed set is not this tool's opinion
# ---------------------------------------------------------------------------
def test_the_expected_tags_are_per_account_and_name_the_ceremony_that_set_them():
    """The two accounts run different books, and one flat list cannot say so.

    Before this was per-account, S6 — the condition whose own text is "read this first;
    nothing below matters if it is wrong" — would have fired CRITICAL on BOTH accounts
    against a correct host read, because the list still held `fx_jpy` (pulled) and not
    `mx_btcusd` (armed).
    """
    conds = json.loads(CONDITIONS.read_text())
    exp = conds["conditions"]["S6_book_composition"]["expected_tags"]
    assert isinstance(exp, dict), "a flat list cannot express two different books"
    assert exp["FTMO"] == ARMED_FTMO.split(",")
    assert exp["redacted_account"] == ARMED_FN.split(",")
    assert MX in exp["FTMO"] and MX not in exp["redacted_account"], \
        "the frontier contract is FTMO-only"
    assert "fx_jpy" not in exp["FTMO"] and "fx_jpy" not in exp["redacted_account"]
    # every set names the ceremony receipt that set it, so nobody has to trust this file
    prov = conds["conditions"]["S6_book_composition"]["expected_tags_provenance"]
    assert "MX_ACTIVATION_20260731" in prov["FTMO"]
    assert "FN_ARMING_20260730" in prov["redacted_account"]
    # and `armed_tags` is the union, which is what the evaluator iterates
    assert sorted(conds["armed_tags"]) == sorted(set(exp["FTMO"]) | set(exp["redacted_account"]))


def test_expected_tags_accepts_the_flat_legacy_form_and_fails_closed_on_a_gap():
    """Every artifact before 2026-07-31 used a flat list; those must still evaluate. An
    account a MAPPING omits must read UNCHECKED — never CLEAN, which would be a live book
    with no composition check and no sign of one."""
    flat = {"conditions": {"S6_book_composition": {"expected_tags": ["a", "b"]}}}
    assert tel.expected_tags_for(flat, "FTMO") == ["a", "b"]
    assert tel.expected_tags_for(flat, "redacted_account") == ["a", "b"]
    gap = {"conditions": {"S6_book_composition": {"expected_tags": {"FTMO": ["a"]}}}}
    assert tel.expected_tags_for(gap, "FTMO") == ["a"]
    assert tel.expected_tags_for(gap, "redacted_account") is None
    findings, out = tel.check_composition(gap, {"FTMO": ["a"], "redacted_account": ["a"]})
    assert out["per_account"]["redacted_account"]["state"] == tel.UNCHECKED
    assert out["per_account"]["FTMO"]["state"] == tel.CLEAN
    assert [f["condition"] for f in [f.as_dict() for f in findings]] == ["S6"]


def test_every_armed_sleeve_has_a_floor_ON_THE_ACCOUNT_IT_IS_ARMED_ON():
    """The gap this caught: `mx_btcusd` went live on FTMO on 2026-07-31 with no row in this
    artifact at all — no risk floor, no evidence floor, no carry alert, no promotion rule.
    Session CA derived them (phase14/receipts/CA_MX_INCUBATION_V1.json). A sleeve armed on
    real money with no pre-registered stop is what the Training Lane §4 forbids."""
    conds = json.loads(CONDITIONS.read_text())
    basis = json.loads(BASIS.read_text())
    exp = conds["conditions"]["S6_book_composition"]["expected_tags"]
    floors = conds["conditions"]["S1a_risk_floor"]["per_sleeve_account"]
    evidence = conds["conditions"]["S1b_evidence_floor"]["per_sleeve_account"]
    for acct, tags in exp.items():
        for tag in tags:
            assert f"{acct}::{tag}" in floors, f"{acct}::{tag} armed with no risk floor"
            assert f"{acct}::{tag}" in evidence, f"{acct}::{tag} armed with no evidence floor"
    # the live contract table is AS's and predates mx; every OTHER armed sleeve is in it
    for tag in set(exp["FTMO"]) | set(exp["redacted_account"]):
        if tag == MX:
            continue
        assert tag in basis["live_contract"], tag


def test_the_promotion_rule_exists_for_the_incubant():
    """Training Lane §4: an incubant carries pre-registered stop AND promotion rules. Without
    the second half an incubant can only ever be killed, which is not an incubation lane."""
    conds = json.loads(CONDITIONS.read_text())
    p1 = conds["conditions"].get("P1_promotion")
    assert p1, "no promotion rule exists at all"
    row = p1["per_sleeve_account"][f"FTMO::{MX}"]
    assert row["cumulative_net_r_ceiling"] > 0
    assert 0.0 < row["measured_false_promotion_probability"] <= 0.11
    # a promotion ceiling must be harder to reach than the stop floor is to hit
    floor = conds["conditions"]["S1a_risk_floor"]["per_sleeve_account"][f"FTMO::{MX}"]
    assert row["cumulative_net_r_ceiling"] > abs(floor["cumulative_net_r_floor"])


def test_the_time_stop_unit_is_reported_in_own_bars_not_clock_hours():
    """`time_stop_bars` counts PRINTED M15 bars. The basis must not present it as calendar hours —
    that conflation is the defect AQ measured at B1400."""
    basis = json.loads(BASIS.read_text())
    for tag, blk in basis["live_contract"].items():
        assert "time_stop_trading_hours" in blk
        assert "time_stop_hours_if_continuous" not in blk
        assert blk["time_stop_own_bars"] is not None, tag
    # the four H4 armed sleeves sit exactly on the research horizon; fx_jpy is inside it
    assert basis["live_contract"]["crypto"]["time_stop_own_bars"] == 80
    assert basis["live_contract"]["fx_jpy"]["time_stop_own_bars"] == 48
