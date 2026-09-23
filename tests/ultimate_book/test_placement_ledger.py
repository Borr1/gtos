"""PlacementLedger idempotency: bar-level dedup + the per-(sleeve,symbol,day) one-entry cap that enforces
the validated one-unit-per-sleeve-per-day model (sleeve-day-reentry-overrisk / COMP-2 same-sleeve)."""
from src.components.ultimate_book.placement_ledger import PlacementLedger


def test_bar_level_dedup(tmp_path):
    pl = PlacementLedger(str(tmp_path), "ns")
    bar = "2026-06-16T08:00:00+00:00"
    assert not pl.already_placed("crypto", "BTCUSD", bar)
    pl.record("crypto", "BTCUSD", bar, decision_day="2026-06-16", ticket=1)
    assert pl.already_placed("crypto", "BTCUSD", bar)
    assert not pl.already_placed("crypto", "BTCUSD", "2026-06-16T12:00:00+00:00")  # a different bar


def test_one_entry_per_sleeve_per_day_cap(tmp_path):
    pl = PlacementLedger(str(tmp_path), "ns")
    assert not pl.already_placed_today("crypto", "BTCUSD", "2026-06-16")
    pl.record("crypto", "BTCUSD", "2026-06-16T08:00:00+00:00", decision_day="2026-06-16", ticket=1)
    # ANY later bar on the SAME day is capped (the over-risk the bar-granular dedup missed)...
    assert pl.already_placed_today("crypto", "BTCUSD", "2026-06-16")
    assert pl.already_placed_today("crypto", "BTCUSD", "2026-06-16T16:00:00+00:00")  # iso also accepted
    # ...but the NEXT day, a DIFFERENT symbol, and a DIFFERENT sleeve are all free to place.
    assert not pl.already_placed_today("crypto", "BTCUSD", "2026-06-17")
    assert not pl.already_placed_today("crypto", "ETHUSD", "2026-06-16")
    assert not pl.already_placed_today("idxrev", "BTCUSD", "2026-06-16")


def test_cluster_cap_allows_same_bar_unit_blocks_later_bar(tmp_path):
    """COMP-2: a correlation cluster is one realized unit per day. ALL members of the SAME bar's unit may
    place; a LATER-bar same-cluster re-fire is blocked. cluster is resolved from the sleeve."""
    clusters = {"metals_core": "metals", "metals_softband": "metals", "crypto": "crypto"}
    pl = PlacementLedger(str(tmp_path), "ns", cluster_resolver=lambda s: clusters.get(s))
    bar1 = "2026-06-16T08:00:00+00:00"
    bar2 = "2026-06-16T12:00:00+00:00"
    # nothing placed yet
    assert not pl.cluster_placed_today_other_bar("metals", "2026-06-16", bar1)
    # metals_core places on bar1
    pl.record("metals_core", "XAUUSD", bar1, decision_day="2026-06-16", ticket=1)
    # a SAME-bar sibling (metals_softband, same unit/bar) is NOT blocked (no OTHER bar yet)
    assert not pl.cluster_placed_today_other_bar("metals", "2026-06-16", bar1)
    pl.record("metals_softband", "XAUUSD", bar1, decision_day="2026-06-16", ticket=2)
    # a LATER bar (bar2) same cluster IS blocked -> would be a 2nd correlated unit
    assert pl.cluster_placed_today_other_bar("metals", "2026-06-16", bar2)
    # a DIFFERENT cluster on a later bar is free
    assert not pl.cluster_placed_today_other_bar("crypto", "2026-06-16", bar2)
    # next day is free
    assert not pl.cluster_placed_today_other_bar("metals", "2026-06-17", "2026-06-17T08:00:00+00:00")


def test_cluster_cap_reconstructs_from_old_rows_via_resolver(tmp_path):
    """A pre-change row lacks an explicit 'cluster'; on reload the resolver reconstructs it so a mid-day
    restart still enforces the cap."""
    clusters = {"metals_core": "metals", "metals_softband": "metals"}
    pl = PlacementLedger(str(tmp_path), "ns", cluster_resolver=lambda s: clusters.get(s))
    pl.record("metals_core", "XAUUSD", "2026-06-16T08:00:00+00:00", decision_day="2026-06-16", ticket=1)
    pl2 = PlacementLedger(str(tmp_path), "ns", cluster_resolver=lambda s: clusters.get(s))  # fresh process
    assert pl2.cluster_placed_today_other_bar("metals", "2026-06-16", "2026-06-16T12:00:00+00:00")


def test_day_cap_persists_across_reload_and_date_fallback(tmp_path):
    pl = PlacementLedger(str(tmp_path), "ns")
    pl.record("crypto", "BTCUSD", "2026-06-16T08:00:00+00:00", decision_day="2026-06-16", ticket=1)
    # a record WITHOUT an explicit decision_day falls back to the bar iso's date
    pl.record("idxrev", "JP225", "2026-06-16T12:00:00+00:00", ticket=2)
    pl2 = PlacementLedger(str(tmp_path), "ns")            # fresh process reloads from disk
    assert pl2.already_placed_today("crypto", "BTCUSD", "2026-06-16")
    assert pl2.already_placed_today("idxrev", "JP225", "2026-06-16")
    assert pl2.already_placed("crypto", "BTCUSD", "2026-06-16T08:00:00+00:00")


def test_ticket_row_index_persists_full_placement_context(tmp_path):
    pl = PlacementLedger(str(tmp_path), "ns")
    pl.record(
        "crypto",
        "BTCUSD",
        "2026-06-16T08:00:00+00:00",
        decision_day="2026-06-16",
        cluster="crypto",
        candidate_id="cand-1",
        ticket=42,
        ts="2026-06-16T08:01:02+00:00",
    )

    row = pl.row_for_ticket(42)
    assert row["candidate_id"] == "cand-1"
    assert row["decision_bar_iso"] == "2026-06-16T08:00:00+00:00"
    assert row["cluster"] == "crypto"

    pl2 = PlacementLedger(str(tmp_path), "ns")
    assert pl2.row_for_ticket(42)["ts"] == "2026-06-16T08:01:02+00:00"
