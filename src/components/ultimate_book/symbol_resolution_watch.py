"""Broker-symbol-rename watchdog: does every symbol the armed book can ASK FOR still exist?

Why this module exists, and the one mistake it is built to prevent
------------------------------------------------------------------
On 2026-07-31 a live read-only probe asked both terminals for `SPX500`, `UK100`, `GER40`,
`JP225` and `NAS100`, got `symbol_info = None` from FTMO for all five, and concluded FTMO had
renamed its index symbols that morning and silently muted four armed members.

It had not. Those five are GTOS **canonical** names — the broker-agnostic registry vocabulary
(`sleeves/registry.py` -> `spec.on_surface`) — and they have never been FTMO broker names. The
FTMO profile has always mapped them across:

    SPX500 -> US500.cash   UK100 -> UK100.cash   GER40 -> GER40.cash
    JP225  -> JP225.cash   NAS100 -> US100.cash

and every one of those targets was present in the FTMO tree in the read-only 2026-07-25 export,
**six days before the alleged rename** (`09_mt5_api/ftmo_symbols_get.jsonl`, 167 symbols, pulled
2026-07-25T23:28:21Z from login 531325516 on FTMO-Server3). The same export is its own control:
redacted_account, probed at the same instant by the same code, DOES carry the bare `SPX500/UK100/JP225`
and carries no `.cash` variant at all — which is exactly what the two profiles encode.

So the whole event was a **name-space error in the probe**, and this module's contract is the
lesson: *a symbol watch compares RESOLVED BROKER names against the broker's tree. Comparing
canonical names produces a false alarm on every correctly-configured cross-broker mapping GTOS
has.* `symbol_map.build_broker_symbol_resolver` is the only sanctioned crossing; this module
takes it as an argument rather than re-deriving it, so the watch can never drift from the fetch.

What a REAL rename looks like, and why nothing else catches it
--------------------------------------------------------------
The generation path is silent when a broker symbol vanishes. `bar_provider.get_closed_bars`
returns `([], [])` on any feed failure (`bar_provider.py:120-125`, a bare
`except Exception: return [], []`), and `book_engine.py:563` then does
`if not bars or not enough(bars, spec.cluster): continue` — no log, no counter, no skip record.
A member whose broker symbol no longer exists therefore generates nothing, forever, while every
heartbeat, every launcher cycle record and every equity read stays perfectly healthy.

The neighbouring failure IS reported: when the *profile* has no instrument config for a canonical
name, `book_engine.py:526-541` counts it as `broker_unsupported_symbol_slot_count` and appends a
`profile_missing_instrument_config` skip. That is a different condition — the profile not naming
the symbol, rather than the broker not serving it — and this module keeps the two apart, because
conflating them is how a standing redacted_account configuration fact would get re-reported every cycle
as a broker emergency.

Read-only: no MT5 import, no network, no filesystem. The caller supplies the symbol-name set,
whether from `mt5.symbols_get()` on a live host or from an export's `*_symbols_get.jsonl`.
"""
from __future__ import annotations

from typing import Callable, Iterable, Mapping, Optional, Sequence

#: The alarm a vanished broker symbol raises. Named so an operator page, a log line and a test
#: all say the same word; `profile_missing_instrument_config` (the engine's own, different
#: condition) is deliberately NOT reused here.
ALARM_UNRESOLVABLE = "broker_symbol_surface_unresolvable"

#: Raised instead when the caller could not read a symbol tree at all. A watch that cannot see
#: the broker reports UNCHECKED, never CLEAN — "I could not look" must not render as "nothing
#: wrong", which is the failure this whole module exists to end.
ALARM_NO_TREE = "broker_symbol_tree_unreadable"

CLEAN, UNCHECKED, ALERT, STOP = "CLEAN", "UNCHECKED", "ALERT", "STOP"


class Slot:
    """One (sleeve, canonical symbol) generation slot and where it resolves on this account."""

    __slots__ = ("sleeve", "canonical", "broker", "profile_supported", "armed")

    def __init__(self, sleeve: str, canonical: str, broker: Optional[str],
                 profile_supported: bool, armed: bool):
        self.sleeve = sleeve
        self.canonical = canonical
        self.broker = broker
        self.profile_supported = profile_supported
        self.armed = armed

    def as_dict(self) -> dict:
        return {"sleeve": self.sleeve, "canonical": self.canonical, "broker": self.broker,
                "profile_supported": self.profile_supported, "armed": self.armed}


def build_slots(specs: Iterable, resolve: Callable[[str], str], *,
                armed_tags: Optional[Sequence[str]] = None) -> list[Slot]:
    """Expand sleeve specs into per-symbol slots, resolved through `resolve`.

    `specs` is any iterable of objects carrying `.tag` and `.on_surface` — i.e. `SleeveSpec`,
    without importing the registry here (this module stays free of the generator import graph so
    an operator page can use it on a host that cannot import a sleeve).

    `armed_tags=None` means "the armed set is unknown"; every slot is then treated as armed, so
    an unknown armed set can only ever over-report. `armed_tags=[]` means "nothing is armed" and
    is honoured literally — the caller must distinguish the two, and the `--tags`-is-falsy
    fail-open at `run_book.py:340` is exactly why that distinction is spelled out rather than
    left to a truthiness test.
    """
    armed_set = None if armed_tags is None else {str(t) for t in armed_tags}
    supports = getattr(resolve, "supports", None)
    slots: list[Slot] = []
    for spec in specs:
        tag = str(getattr(spec, "tag", "") or "")
        armed = True if armed_set is None else (tag in armed_set)
        for canonical in (getattr(spec, "on_surface", ()) or ()):
            ok = True
            if callable(supports):
                try:
                    ok = bool(supports(canonical))
                except Exception:
                    ok = True          # a resolver that cannot answer must not mute the watch
            broker = None
            if ok:
                try:
                    broker = str(resolve(canonical))
                except Exception:
                    # A resolver that BLOWS UP is not "the profile does not carry this symbol" —
                    # it is a slot whose broker name is unknown, which is strictly worse. Leave
                    # `profile_supported` True so the slot stays in the diff and reports as
                    # unresolvable; demoting it here would mute the watch, which is the exact
                    # failure this module exists to end.
                    broker = None
            slots.append(Slot(tag, str(canonical), broker, ok, armed))
    return slots


def watch(slots: Sequence[Slot], broker_names: Optional[Iterable[str]], *,
          account: str = "?") -> dict:
    """Diff resolved broker names against the broker's own symbol tree.

    Returns a JSON-ready verdict. `broker_names=None` (tree unreadable) yields UNCHECKED with
    `ALARM_NO_TREE`; an EMPTY-but-readable tree is treated the same way, because a terminal that
    answers `symbols_get()` with nothing is not evidence that every symbol vanished — it is
    evidence the read failed. Both are `unchecked`, never `unresolvable`.
    """
    if broker_names is None:
        tree = None
    else:
        tree = {str(n) for n in broker_names if n}
        if not tree:
            tree = None

    if tree is None:
        return {
            "schema": "gtos.live.symbol_resolution_watch.v1",
            "account": account, "state": UNCHECKED, "alarm": ALARM_NO_TREE,
            "n_slots": len(slots), "n_tree": 0,
            "unresolvable": [], "unresolvable_armed": [],
            "profile_unsupported": [s.as_dict() for s in slots if not s.profile_supported],
            "resolved_ok": 0,
            "summary": f"{account}: symbol tree unreadable — resolution NOT checked",
        }

    unresolvable: list[dict] = []
    ok = 0
    for s in slots:
        if not s.profile_supported:
            continue
        if s.broker in tree:
            ok += 1
        else:
            unresolvable.append(s.as_dict())

    armed_bad = [u for u in unresolvable if u["armed"]]
    if armed_bad:
        state = STOP
    elif unresolvable:
        state = ALERT
    else:
        state = CLEAN

    if state == CLEAN:
        summary = (f"{account}: all {ok} resolved broker symbols present in a "
                   f"{len(tree)}-symbol tree")
    else:
        sleeves = sorted({u["sleeve"] for u in (armed_bad or unresolvable)})
        pairs = ", ".join(f"{u['canonical']}->{u['broker']}"
                          for u in (armed_bad or unresolvable)[:8])
        scope = "ARMED " if armed_bad else ""
        summary = (f"{account}: {len(armed_bad or unresolvable)} {scope}member(s) resolve to "
                   f"broker symbols the terminal does not serve — {pairs}"
                   f"{' …' if len(armed_bad or unresolvable) > 8 else ''} "
                   f"(sleeves: {', '.join(sleeves)})")

    return {
        "schema": "gtos.live.symbol_resolution_watch.v1",
        "account": account, "state": state,
        "alarm": ALARM_UNRESOLVABLE if unresolvable else None,
        "n_slots": len(slots), "n_tree": len(tree),
        "unresolvable": unresolvable, "unresolvable_armed": armed_bad,
        "profile_unsupported": [s.as_dict() for s in slots if not s.profile_supported],
        "resolved_ok": ok,
        "summary": summary,
    }


def rename_candidates(unresolvable: Sequence[Mapping], broker_names: Iterable[str]) -> dict:
    """Best-effort 'what did it become?' for a real rename — suffix/stem neighbours only.

    Deliberately a HINT, not a mapping: it proposes names, it never rewrites a profile. A rename
    repair is a token-bound profile edit and therefore an owner ceremony (the token binds
    `config/agent_config.yaml` and both live profiles' bytes), so the most this layer may do is
    hand the operator the candidate list it would otherwise assemble by hand at 3 a.m.
    """
    tree = sorted({str(n) for n in broker_names if n})
    out: dict[str, list[str]] = {}
    for u in unresolvable:
        want = str(u.get("broker") or u.get("canonical") or "")
        if not want:
            continue
        stem = want.split(".")[0].split("_")[0].upper()
        if not stem:
            continue
        hits = [n for n in tree
                if n.upper() == stem
                or n.upper().split(".")[0].split("_")[0] == stem
                or (len(stem) >= 4 and stem in n.upper())]
        out[want] = hits[:8]
    return out
