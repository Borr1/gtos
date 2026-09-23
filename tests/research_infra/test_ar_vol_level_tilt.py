"""Session AR (wave 11, B1452) — the vol-LEVEL sizing tilt, behaviourally.

WHAT THESE TESTS ARE FOR
------------------------
Three things, in decreasing order of how much they matter.

1. **The default path is byte-identical.** Two accounts are trading real money on three
   sleeves, one of which is `sub_xvol_pullback`. The tilt is default-OFF and adding it must
   not move one unit of anyone's size. `test_default_path_*` asserts that on the sized
   output, not on the source.

2. **The deployed constants ARE the declared constants.** `admission.py` carries its own
   literals and `VOL_LEVEL_TILT_DECLARATION_V1.json` carries the declaration; nothing imports
   one from the other on purpose, so `test_deployed_constants_match_the_declaration` is what
   makes a later edit to either side fail loudly instead of silently re-fitting the tilt after
   it was priced.

3. **The tilt's shape.** Monotone, centred at 2.0 exactly, clamped both ways, no-op off-sleeve
   and no-op on a missing/garbage `vr`, and — the one that is easy to get wrong — a SHRINK
   survives the `OVERLAY_SIZEUP_MAX` cap instead of being discarded by it.

No market data, no config read, no broker import.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from src.components.ultimate_book import admission as A

REPO = Path(__file__).resolve().parents[2]
DECL = (REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
        / "VOL_LEVEL_TILT_DECLARATION_V1.json")

XVOL = "sub_xvol_pullback"


def _intent(sleeve=XVOL, *, vr=None, day="2026-01-05", symbol="XAUUSD", **kw):
    return A.TradeIntent(sleeve=sleeve, symbol=symbol, direction=1, decision_day=day,
                         stop_dist=10.0, target_dist=30.0, vr=vr, **kw)


# ---------------------------------------------------------------------------------------
# 1. the default path


def test_default_path_is_a_no_op_even_when_vr_is_populated():
    """The generator now always populates `vr`. That alone must change nothing."""
    it = _intent(vr=1.75)
    assert A.vol_level_tilt_for(it) == (1.0, ())
    assert A.vol_level_tilt_for(it, enabled=False) == (1.0, ())


def test_default_path_sizes_identically_with_and_without_vr():
    """A sized unit is identical whether or not the intent carries `vr`, tilt off."""
    for kelly in (False, True):
        for overlays in (False, True):
            bare = A.size_correlated_units(
                [_intent(vr=None)], base_risk_per_unit=0.02,
                include_clean3=True, kelly_lite=kelly, overlays=overlays)
            withvr = A.size_correlated_units(
                [_intent(vr=2.3)], base_risk_per_unit=0.02,
                include_clean3=True, kelly_lite=kelly, overlays=overlays)
            assert [u.unit_risk_pct for u in bare] == [u.unit_risk_pct for u in withvr]
            assert [u.confidence for u in bare] == [u.confidence for u in withvr]
            assert [u.overlays_applied for u in bare] == [u.overlays_applied for u in withvr]


def test_admit_and_size_reports_the_flag_and_defaults_it_off():
    st = A.GovernorState(equity=100_000.0, high_water=100_000.0, realized_today_pct=0.0,
                         open_risk_pct=0.0, max_dd_reference_equity=100_000.0)
    out = A.admit_and_size([_intent(vr=2.2)], st, include_clean3=True)
    assert out["vol_level_tilt"] is False


# ---------------------------------------------------------------------------------------
# 2. the deployed constants are the declared constants


def test_deployed_constants_match_the_declaration():
    """`admission.py` and the declaration artifact must not drift apart.

    They deliberately do not import each other: the declaration is a research receipt frozen
    at a commit that contained no economics, and production code must not depend on a receipt.
    So the agreement is asserted here instead.
    """
    d = json.loads(DECL.read_text())
    c = d["constants"]
    assert c["TILT_SLEEVE"] == XVOL
    assert set(A.VOL_LEVEL_TILT_SLEEVES) == {c["TILT_SLEEVE"]}
    assert A.VOL_LEVEL_TILT_CENTRE == c["TILT_CENTRE"] == 2.0
    assert A.VOL_LEVEL_TILT_MIN == c["TILT_MIN"] == 0.80
    assert A.VOL_LEVEL_TILT_MAX == c["TILT_MAX"] == 1.20
    assert c["TILT_EXPONENT"] == 1


def test_the_centre_is_ABs_published_xhi_band_value_in_production_source():
    """2.0 is not a number this session chose; `dials.py` publishes it.

    Read from the module rather than the source text, because a grep for "2.0" would pass
    against a wrong implementation (engineering rule: behavioural over source-string).
    """
    from src.research_infra.regime_spine import dials as D

    xhi = None
    for dial in getattr(D, "DIALS", ()) or ():
        bands = getattr(dial, "bands", None)
        if isinstance(bands, dict) and "xhi" in bands:
            xhi = bands["xhi"]
    if xhi is None:  # the dial registry moved; say so rather than passing vacuously
        pytest.fail("no dial with an `xhi` band found in regime_spine.dials — "
                    "the tilt's centre provenance claim can no longer be checked here")
    assert xhi == A.VOL_LEVEL_TILT_CENTRE == 2.0


# ---------------------------------------------------------------------------------------
# 3. the tilt's shape


def test_unit_point_is_exactly_the_centre():
    m, names = A.vol_level_tilt_for(_intent(vr=2.0), enabled=True)
    assert m == 1.0
    assert names and names[0].startswith("vol_level_tilt_")


def test_monotone_over_the_sleeves_own_firing_range():
    """`vol=xhi` is vr >= 1.6 with no ceiling; the archive range is [1.6001, 2.3747]."""
    vals = [1.6001, 1.70, 1.834, 1.95, 2.0, 2.15, 2.3747]
    ms = [A.vol_level_tilt_for(_intent(vr=v), enabled=True)[0] for v in vals]
    assert ms == sorted(ms)
    assert len(set(ms)) == len(ms), "strictly monotone over distinct vr inside the range"


def test_the_declared_direction_is_DOWN_over_the_firing_range():
    """The band floor is 1.6 and the centre is 2.0, so most of the range shrinks.

    This is the fact the owner package leads with and it is asserted, not narrated.
    """
    assert A.vol_level_tilt_for(_intent(vr=1.6001), enabled=True)[0] < 1.0
    assert A.vol_level_tilt_for(_intent(vr=1.834), enabled=True)[0] < 1.0   # archive median
    assert A.vol_level_tilt_for(_intent(vr=2.3747), enabled=True)[0] > 1.0  # archive max


def test_clamp_binds_both_ways_but_not_inside_the_observed_range():
    assert A.vol_level_tilt_for(_intent(vr=0.5), enabled=True)[0] == A.VOL_LEVEL_TILT_MIN
    assert A.vol_level_tilt_for(_intent(vr=99.0), enabled=True)[0] == A.VOL_LEVEL_TILT_MAX
    # the archive extremes sit strictly inside, so the clamp is a safety bound not a shape
    lo = A.vol_level_tilt_for(_intent(vr=1.600136704193), enabled=True)[0]
    hi = A.vol_level_tilt_for(_intent(vr=2.374734084273), enabled=True)[0]
    assert A.VOL_LEVEL_TILT_MIN < lo < 1.0 < hi < A.VOL_LEVEL_TILT_MAX


@pytest.mark.parametrize("sleeve", ["crypto", "energy_agri", "sub_mid_dn_revert", "metals_core"])
def test_no_op_off_sleeve(sleeve):
    """Scoped by declaration. `sub_mid_dn_revert` computes vr and is deliberately excluded."""
    assert A.vol_level_tilt_for(_intent(sleeve=sleeve, vr=2.4), enabled=True) == (1.0, ())


@pytest.mark.parametrize("bad", [None, "", "abc", float("nan"), float("inf"),
                                 float("-inf"), 0.0, -1.0])
def test_fail_closed_to_no_op_on_an_unusable_vr(bad):
    """Absent or garbage vr sizes as today rather than guessing a vol level."""
    assert A.vol_level_tilt_for(_intent(vr=bad), enabled=True) == (1.0, ())


def test_a_shrink_is_not_discarded_by_the_sizeup_cap():
    """THE BUG THIS TEST EXISTS FOR.

    `su_combined` is capped at OVERLAY_SIZEUP_MAX. If the tilt were folded INSIDE that cap, a
    shrink would be silently dropped on any intent whose other multipliers already sat at the
    ceiling. This test constructs that state deliberately (both confluence overlays 1.5 x 1.15 =
    1.725, four distinct sleeves so Kelly-lite takes its top bin) and asserts the shrink survives.

    THE STATE IS LATENT AND TWO INDEPENDENT CHANGES AWAY, not one config key — corrected twice by
    adversarial passes. Live runs `ultimate_book_overlays: false` (`config/agent_config.yaml:1289`)
    and `kelly_conservative: true` (`:1304`, top bin 1.241), so the live product is at most 1.241
    against a 1.75 cap. And structurally: the only live `sub_xvol_pullback` generator
    (`sleeves/substrate.py::_generate`) populates neither `ll_impulse` nor `decision_hour`, and
    each overlay needs one — `overlay_sizeup_for(live_shape_intent, overlays=True)` returns
    `(1.0, ())`. So reaching the cap needs a config flip AND a generator change. The test still
    belongs: it makes a size-cap defect on a live-money path impossible rather than merely absent.
    """
    kw = dict(base_risk_per_unit=0.02, include_clean3=True, overlays=True, kelly_lite=True)
    # 4 distinct sleeves on the day -> Kelly bin 1.60; xvol also takes both confluence overlays.
    others = [_intent(sleeve=s, symbol=sym) for s, sym in
              (("crypto", "BTCUSD"), ("energy_agri", "CORN_c"), ("metals_core", "XAUUSD"))]
    hot = _intent(vr=1.6001, ll_impulse=A.LEADER_IMPULSE_NONE, decision_hour=8)
    off = A.size_correlated_units([hot] + others, **kw)
    on = A.size_correlated_units([hot] + others, vol_level_tilt=True, **kw)

    def xvol_unit(units):
        return next(u for u in units if XVOL in u.sleeve_members)

    u_off, u_on = xvol_unit(off), xvol_unit(on)
    assert u_off.unit_risk_pct > 0.0
    assert u_on.unit_risk_pct < u_off.unit_risk_pct, (
        "the shrink was discarded by the size-up cap — the tilt is applied after the cap")
    # `rel_tol` is 1e-4 and not tighter ON PURPOSE: `size_correlated_units` rounds `confidence`
    # to 6 dp and `unit_risk_pct` to 8 dp (`:1220-1221`), so a RATIO of two rounded quantities
    # cannot reproduce the multiplier better than ~2e-5 at this magnitude. The multiplier itself
    # is asserted exactly in `test_clamp_binds_both_ways_but_not_inside_the_observed_range`;
    # what this line checks is that the WHOLE of it reaches the unit, not part of it.
    assert math.isclose(u_on.unit_risk_pct / u_off.unit_risk_pct, 0.800068352096,
                        rel_tol=1e-4), "the surviving shrink is not the declared multiplier"


def test_the_tilt_can_never_push_a_unit_past_the_governor_safe_cap():
    """The size-UP side still lives inside OVERLAY_SIZEUP_MAX."""
    kw = dict(base_risk_per_unit=0.02, include_clean3=True, overlays=True, kelly_lite=True)
    others = [_intent(sleeve=s, symbol=sym) for s, sym in
              (("crypto", "BTCUSD"), ("energy_agri", "CORN_c"), ("metals_core", "XAUUSD"))]
    hot = _intent(vr=99.0, ll_impulse=A.LEADER_IMPULSE_NONE, decision_hour=8)
    on = A.size_correlated_units([hot] + others, vol_level_tilt=True, **kw)
    u = next(x for x in on if XVOL in x.sleeve_members)
    conf_cap = A.confidence_for(XVOL, A.effective_registry(include_clean3=True)) * A.OVERLAY_SIZEUP_MAX
    assert u.confidence <= conf_cap + 1e-9


def test_the_reason_string_carries_the_vr_and_the_multiplier():
    """Audit trail: a unit's `overlays_applied` must say what the tilt did, not just that it ran."""
    units = A.size_correlated_units([_intent(vr=2.30)], base_risk_per_unit=0.02,
                                    include_clean3=True, vol_level_tilt=True)
    tags = units[0].overlays_applied
    assert any(t.startswith("vol_level_tilt_vr2.3000_x1.15") for t in tags), tags


# ---------------------------------------------------------------------------------------
# 4. the wiring, end to end, without a broker


def test_the_launcher_flag_reaches_the_bridge_without_a_config_byte():
    """`--vol-level-tilt` -> engine -> INJECTED runtime key -> bridge -> admit_and_size.

    Asserted through the engine's own attribute and the bridge's own reader, because the point
    of the design is that `config/agent_config.yaml` is never consulted for this flag.
    """
    from src.components.ultimate_book import bridge as B
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

    eng_off = UltimateBookLiveEngine({}, None, ".", namespace="t")
    eng_on = UltimateBookLiveEngine({}, None, ".", namespace="t", vol_level_tilt=True)
    assert eng_off._vol_level_tilt is False
    assert eng_on._vol_level_tilt is True
    # the injected key is what the bridge reads, and it is read from a COPY
    base = {"ultimate_book_enabled": True}
    eng_on.config = base
    injected = dict(eng_on.config, ultimate_book_vol_level_tilt=True)
    assert B._bool(injected, "ultimate_book_vol_level_tilt") is True
    assert B._bool(base, "ultimate_book_vol_level_tilt") is False
    assert "ultimate_book_vol_level_tilt" not in base, "self.config must not be mutated"


def test_the_flag_is_not_in_any_committed_config():
    """No config file may carry the key — that is the whole reason the flag exists.

    A key in `agent_config.yaml` or `profiles/redacted_account.yaml` would move a live activation
    token's config digest and stop an armed book placing.
    """
    for rel in ("config/agent_config.yaml", "config/profiles/redacted_account.yaml",
                "config/profiles/operator_profile.yaml", "config/profiles/ftmo.yaml"):
        p = REPO / rel
        if p.is_file():
            assert "ultimate_book_vol_level_tilt" not in p.read_text(), rel


def test_the_substrate_generator_populates_vr_and_the_field_exists():
    """The plumbing: `vr` is a TradeIntent field and the replay adapter passes it through."""
    assert "vr" in A.TradeIntent.__dataclass_fields__
    from src.research_infra.replay_policy.core import PolicyCandidate
    from src.research_infra.replay_policy.sleeve_book import _to_trade_intent

    cand = PolicyCandidate(sleeve=XVOL, symbol="XAUUSD", direction=1,
                           decision_day="2026-01-05", stop_dist=10.0,
                           features={"vr": 2.25})
    assert _to_trade_intent(cand).vr == 2.25


def test_vr_survives_the_INVERSE_adapter_round_trip():
    """THE LATENT DEFECT THIS TEST EXISTS FOR — armed-but-inert, the worst class here.

    `sleeve_book._to_trade_intent` is the FORWARD adapter and forwards any `features` key naming
    a `TradeIntent` field, which is why `book_replay`'s pricing lane worked. The INVERSE adapter
    `generation._to_policy_candidate` enumerates its feature names explicitly, and `vr` was not
    among them — so the live-generation lane
    (`LiveGeneration.generate` -> `_to_policy_candidate` -> `_to_trade_intent`) rebuilt the intent
    with `vr=None`. In that lane the tilt was a silent no-op EVEN WHEN ARMED, while
    `SleeveBookPolicy.describe()["dial"]` reported it True. Found by an adversarial pass over AR's
    own wiring, not by AR.
    """
    from src.research_infra.replay_policy.generation import _to_policy_candidate
    from src.research_infra.replay_policy.sleeve_book import _to_trade_intent

    it = _intent(vr=1.6001)
    cand = _to_policy_candidate(it, {"decision_day": "2026-01-05", "last_close": 2000.0})
    assert cand.features.get("vr") == 1.6001, "the inverse adapter dropped vr"
    back = _to_trade_intent(cand)
    assert back.vr == 1.6001, "vr did not survive the round trip"
    #  and the tilt actually fires on the round-tripped intent
    m, names = A.vol_level_tilt_for(back, enabled=True)
    assert m == pytest.approx(0.80005, abs=1e-5) and names


def test_the_inverse_adapter_drops_vr_when_the_generator_did_not_set_it():
    """Adding `vr` must not invent one. A sleeve that does not compute it stays absent."""
    from src.research_infra.replay_policy.generation import _to_policy_candidate

    cand = _to_policy_candidate(_intent(sleeve="crypto", vr=None),
                                {"decision_day": "2026-01-05"})
    assert "vr" not in cand.features


def test_the_replay_policy_describes_the_tilt_it_ran():
    """A replay that armed the tilt must not describe itself like one that did not."""
    from src.research_infra.replay_policy.sleeve_book import SleeveBookPolicy

    cfg = {k: False for k in SleeveBookPolicy.DIAL_KEYS}
    cfg["ultimate_book_profile"] = "clean3_w7_ceiling_nom2p00"
    cfg["ultimate_book_derisk_mode"] = "smooth"
    off = SleeveBookPolicy(cfg).describe()["dial"]
    on = SleeveBookPolicy(dict(cfg, ultimate_book_vol_level_tilt=True)).describe()["dial"]
    assert "ultimate_book_vol_level_tilt" in off and "ultimate_book_vol_level_tilt" in on
    assert off["ultimate_book_vol_level_tilt"] in (None, False)
    assert on["ultimate_book_vol_level_tilt"] is True


def test_strict_config_still_accepts_a_caller_that_predates_the_tilt():
    """The key must NOT be required: its off-value is the live book, so absence is correct."""
    from src.research_infra.replay_policy.sleeve_book import SleeveBookPolicy

    cfg = {k: False for k in SleeveBookPolicy.DIAL_KEYS}
    cfg["ultimate_book_profile"] = "clean3_w7_ceiling_nom2p00"
    cfg["ultimate_book_derisk_mode"] = "smooth"
    SleeveBookPolicy(cfg, strict_config=True)  # must not raise
