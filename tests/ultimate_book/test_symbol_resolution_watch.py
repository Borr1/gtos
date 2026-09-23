"""Session CF — the broker-symbol-rename watchdog, and the false alarm it exists to prevent.

Two halves:

  * the watch fires on a REAL rename, within one cycle, naming the members (synthetic tree diffs);
  * the watch does NOT fire on the 2026-07-31 "FTMO renamed its indices" event, because that
    event was a canonical-vs-broker name-space error in the probe. That half is a regression pin
    on live profiles and the vendored broker tree, not a mock: if anyone ever rebuilds this check
    against canonical names it goes red here instead of on an armed book.
"""
import json
from pathlib import Path

import pytest
import yaml

from src.components.ultimate_book.sleeves.registry import (
    BUILT, CANDIDATE_BUILT, MARKET_EXPANSION_BUILT,
)
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.components.ultimate_book.symbol_resolution_watch import (
    ALARM_NO_TREE, ALARM_UNRESOLVABLE, ALERT, CLEAN, STOP, UNCHECKED,
    build_slots, rename_candidates, watch,
)

REPO = Path(__file__).resolve().parents[2]
FIXTURE = (REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts"
           / "BROKER_SYMBOL_TREE_20260725.json")
FTMO_PROFILE = REPO / "config/profiles/operator_profile.yaml"
FN_PROFILE = REPO / "config/profiles/redacted_account.yaml"

#: The five canonical names the 2026-07-31 probe asked FTMO for, and their FTMO broker names.
EVENT_MAP = {"SPX500": "US500.cash", "UK100": "UK100.cash", "GER40": "GER40.cash",
             "JP225": "JP225.cash", "NAS100": "US100.cash"}
FTMO_ARMED = ["crypto", "energy_agri", "sub_xvol_pullback",
              "mx_btcusd_d1_donchian_20_breakout"]


class _Spec:
    """Minimal stand-in for SleeveSpec — the watch only reads .tag and .on_surface."""

    def __init__(self, tag, on_surface):
        self.tag = tag
        self.on_surface = tuple(on_surface)


def _resolver(table, *, supports_all=True):
    def resolve(canonical):
        return table.get(canonical, canonical)
    resolve.supports = lambda c: True if supports_all else (c in table)
    return resolve


def _tree(account):
    return set(json.loads(FIXTURE.read_text(encoding="utf-8"))["symbols"][account])


def _all_specs():
    d = {}
    d.update(BUILT)
    d.update(CANDIDATE_BUILT)
    d.update(MARKET_EXPANSION_BUILT)
    return list(d.values())


# ---------------------------------------------------------------------------
# the real rename: what the watch is FOR
# ---------------------------------------------------------------------------
def test_real_rename_on_an_armed_sleeve_is_a_STOP_naming_the_members():
    specs = [_Spec("sub_xvol_pullback", ["SPX500", "XAUUSD"]), _Spec("crypto", ["BTCUSD"])]
    resolve = _resolver({"SPX500": "US500.cash"})
    slots = build_slots(specs, resolve, armed_tags=["sub_xvol_pullback", "crypto"])

    # the broker drops US500.cash and starts serving US500.spot instead
    out = watch(slots, {"US500.spot", "XAUUSD", "BTCUSD"}, account="FTMO")

    assert out["state"] == STOP
    assert out["alarm"] == ALARM_UNRESOLVABLE
    assert [u["canonical"] for u in out["unresolvable"]] == ["SPX500"]
    assert out["unresolvable"][0]["broker"] == "US500.cash"
    assert out["unresolvable_armed"] == out["unresolvable"]
    assert "SPX500->US500.cash" in out["summary"]
    assert "sub_xvol_pullback" in out["summary"]
    assert out["resolved_ok"] == 2


def test_rename_on_an_unarmed_sleeve_is_an_ALERT_not_a_STOP():
    specs = [_Spec("idxrev", ["SPX500"]), _Spec("crypto", ["BTCUSD"])]
    slots = build_slots(specs, _resolver({"SPX500": "US500.cash"}), armed_tags=["crypto"])
    out = watch(slots, {"BTCUSD"}, account="FTMO")
    assert out["state"] == ALERT
    assert out["alarm"] == ALARM_UNRESOLVABLE
    assert out["unresolvable_armed"] == []


def test_synthetic_tree_diff_reproduces_the_rename_the_event_CLAIMED_and_fires():
    """Had FTMO actually done what the event described, the watch would have caught it.

    The claimed change was `.cash` -> bare. Apply exactly that to the vendored FTMO tree and the
    armed book's index members must go STOP.
    """
    tree = _tree("FTMO")
    renamed = {n for n in tree if not n.endswith(".cash")}
    renamed |= {n[: -len(".cash")] for n in tree if n.endswith(".cash")}

    prof = yaml.safe_load(FTMO_PROFILE.read_text(encoding="utf-8"))
    slots = build_slots(_all_specs(), build_broker_symbol_resolver(prof), armed_tags=FTMO_ARMED)

    before = watch(slots, tree, account="FTMO")
    after = watch(slots, renamed, account="FTMO")

    assert before["state"] == CLEAN
    assert after["state"] == STOP
    hit = {u["canonical"] for u in after["unresolvable_armed"]}
    assert {"SPX500", "UK100", "GER40"} <= hit          # sub_xvol_pullback's index members
    assert "sub_xvol_pullback" in after["summary"]


def test_rename_candidates_points_at_the_successor_without_rewriting_anything():
    out = watch(build_slots([_Spec("s", ["SPX500"])], _resolver({"SPX500": "US500"})),
                {"US500.cash", "XAUUSD"})
    cands = rename_candidates(out["unresolvable"], {"US500.cash", "XAUUSD"})
    assert cands == {"US500": ["US500.cash"]}


# ---------------------------------------------------------------------------
# the false alarm: canonical names are NOT broker names
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("canonical,broker", sorted(EVENT_MAP.items()))
def test_the_five_event_names_are_absent_bare_and_present_resolved_on_ftmo(canonical, broker):
    """The 2026-07-31 probe's exact reads, against the tree from SIX DAYS EARLIER.

    Bare absent + resolved present, already, before the alleged rename. This is the whole
    refutation in one assertion per name.
    """
    tree = _tree("FTMO")
    prof = yaml.safe_load(FTMO_PROFILE.read_text(encoding="utf-8"))
    resolve = build_broker_symbol_resolver(prof)
    assert resolve(canonical) == broker
    assert canonical not in tree          # what the probe saw, and misread
    assert broker in tree                 # what the book actually asks for


def test_redacted_account_is_the_same_instant_control_and_is_the_other_way_round():
    """Same export, same code, same moment — FN carries the bare names and no .cash at all."""
    fn = _tree("redacted_account")
    assert {"SPX500", "UK100", "JP225"} <= fn
    assert not any(n.endswith(".cash") for n in fn)
    prof = yaml.safe_load(FN_PROFILE.read_text(encoding="utf-8"))
    resolve = build_broker_symbol_resolver(prof)
    assert resolve("SPX500") == "SPX500"
    assert resolve("GER40") == "GER30"


def test_full_registry_resolves_clean_on_both_accounts_against_the_vendored_tree():
    """137 slots, 34 declared sleeves, both live profiles: ZERO unresolvable. No member is mute."""
    specs = _all_specs()
    for account, profile, armed in (("FTMO", FTMO_PROFILE, FTMO_ARMED),
                                    ("redacted_account", FN_PROFILE, FTMO_ARMED[:3])):
        prof = yaml.safe_load(profile.read_text(encoding="utf-8"))
        slots = build_slots(specs, build_broker_symbol_resolver(prof), armed_tags=armed)
        out = watch(slots, _tree(account), account=account)
        assert out["unresolvable"] == [], f"{account}: {out['summary']}"
        assert out["state"] == CLEAN
        assert out["alarm"] is None


def test_profile_unsupported_is_reported_separately_and_never_as_a_rename():
    """redacted_account's missing crosses are a standing config fact, not a broker emergency.

    `book_engine.py:526-541` already counts these as `profile_missing_instrument_config`. If the
    watch folded them into the rename alarm, FN would raise a broker alarm every single cycle.
    """
    prof = yaml.safe_load(FN_PROFILE.read_text(encoding="utf-8"))
    slots = build_slots(_all_specs(), build_broker_symbol_resolver(prof), armed_tags=FTMO_ARMED[:3])
    out = watch(slots, _tree("redacted_account"), account="redacted_account")
    assert out["state"] == CLEAN
    assert out["unresolvable"] == []
    assert len(out["profile_unsupported"]) > 0
    assert {"XAUEUR", "CORN_c"} <= {s["canonical"] for s in out["profile_unsupported"]}


# ---------------------------------------------------------------------------
# fail-closed on ignorance
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tree", [None, set(), []])
def test_unreadable_or_empty_tree_is_UNCHECKED_never_CLEAN(tree):
    slots = build_slots([_Spec("crypto", ["BTCUSD"])], _resolver({}), armed_tags=["crypto"])
    out = watch(slots, tree, account="FTMO")
    assert out["state"] == UNCHECKED
    assert out["alarm"] == ALARM_NO_TREE
    assert out["unresolvable"] == []
    assert "NOT checked" in out["summary"]


def test_unknown_armed_set_over_reports_and_empty_armed_set_is_honoured():
    specs = [_Spec("idxrev", ["SPX500"])]
    resolve = _resolver({"SPX500": "US500.cash"})
    unknown = watch(build_slots(specs, resolve, armed_tags=None), {"XAUUSD"})
    none_armed = watch(build_slots(specs, resolve, armed_tags=[]), {"XAUUSD"})
    assert unknown["state"] == STOP            # unknown -> treat as armed -> loudest
    assert none_armed["state"] == ALERT        # explicitly nothing armed -> still reported


def test_a_resolver_that_raises_cannot_mute_the_watch():
    def hostile(_c):
        raise RuntimeError("boom")
    hostile.supports = lambda _c: True
    out = watch(build_slots([_Spec("crypto", ["BTCUSD"])], hostile, armed_tags=["crypto"]),
                {"BTCUSD"})
    assert out["state"] == STOP
    assert out["unresolvable"][0]["broker"] is None
