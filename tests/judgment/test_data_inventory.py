from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.components.ultimate_book.primitives import Bar
from src.judgment.bars import (
    MULTI_SYMBOL_OPTIONAL,
    MULTI_SYMBOL_PRIORITY,
    StampedBar,
    books_for_symbol,
    challenge_tape_present,
    landed_challenge_symbols,
    resolve_challenge_tf,
)
from src.judgment.data_inventory import (
    LOCK,
    MARKDOWN_COLUMNS,
    SCHEMA,
    collect_inventory,
    gtos_24_from_source,
    jev_watch_symbols,
    render_markdown,
    write_markdown,
)
from src.judgment.gold_state import assemble_gold_state_v0

# Chair 2026-09-18 XAU refresh last M15=04:15Z. Pin so lag notes stay stable.
PINNED_NOW = datetime(2026, 9, 18, 4, 20, tzinfo=timezone.utc)


def test_lock_flags_refuse_place_and_apply():
    assert LOCK["never_place"] is True
    assert LOCK["never_remint"] is True
    assert LOCK["never_flatten"] is True
    assert LOCK["never_apply_size"] is True
    assert LOCK["never_invent_news_protocol"] is True
    assert LOCK["never_import_selector_v4"] is True
    assert LOCK["never_import_v4_timewarp"] is True


def test_collector_does_not_import_bound_modules():
    text = Path("src/judgment/data_inventory.py").read_text(encoding="utf-8")
    assert "from src.research_infra" not in text
    assert "import src.research_infra" not in text
    assert not any(
        line.strip().startswith(("import ", "from ")) and "selector_v4" in line
        for line in text.splitlines()
    )
    assert LOCK["never_import_selector_v4"] is True
    assert LOCK["never_import_v4_timewarp"] is True


def test_april_historical_is_not_challenge_tape():
    challenge = resolve_challenge_tf("GBPUSD", "M15")
    assert "data/" not in str(challenge) or not challenge.is_file()
    assert not str(challenge).endswith("data/GBPUSD_M15.csv")
    hist = Path("data/GBPUSD_M15.csv")
    if hist.is_file() and challenge.is_file():
        assert challenge.resolve() != hist.resolve()


def test_non_xau_books_landed_after_chair_zips():
    landed = landed_challenge_symbols()
    assert "XAUUSD" in landed
    for sym in ("EURUSD", "GBPUSD", "USDJPY", "US30", "EURGBP", "GBPJPY"):
        assert challenge_tape_present(sym) is True
        books = books_for_symbol(sym)
        assert books is not None
        assert books["m15"]
        assert "XAUUSD" not in books["m15"][0].source_path
    assert challenge_tape_present("UK100") is False
    inv = collect_inventory(now=PINNED_NOW)
    assert inv["disk"]["non_xau_books_present"] is True
    assert inv["disk"]["vps_peer_csvs_on_this_clone"] is True


def test_books_for_symbol_never_substitutes_xau():
    xau = books_for_symbol("XAUUSD")
    assert xau is not None
    assert xau["m15"]
    gbp = books_for_symbol("GBPUSD")
    assert gbp is not None
    assert gbp["m15"]
    assert xau["m15"][0].source_path != gbp["m15"][0].source_path
    assert "XAUUSD" in xau["m15"][0].source_path
    assert "GBPUSD" in gbp["m15"][0].source_path


def test_multi_symbol_matches_bars():
    inv = collect_inventory(now=PINNED_NOW)
    assert tuple(inv["code_universes"]["multi_symbol_priority"]) == MULTI_SYMBOL_PRIORITY
    assert tuple(inv["code_universes"]["multi_symbol_optional"]) == MULTI_SYMBOL_OPTIONAL
    assert inv["schema"] == SCHEMA


def test_gtos_24_extracted_without_importing_timewarp():
    surface = gtos_24_from_source()
    assert len(surface) == 24
    assert "XAUUSD" in surface
    assert "GBPUSD" in surface
    assert "US30_cash" in surface
    inv = collect_inventory(now=PINNED_NOW)
    assert inv["code_universes"]["gtos_24"] == list(surface)
    assert inv["code_universes"]["gtos_24_matches_vnext_24"] is True


def test_xau_admit_at_now_parent_equals_multi():
    inv = collect_inventory(now=PINNED_NOW)
    xau = next(r for r in inv["jev_rows"] if r["symbol"] == "XAUUSD")
    assert xau["challenge_tape_present"] is True
    assert xau["admit"]["sit_as_of"] is True
    assert xau["admit"]["now"] is True
    assert xau["bars"]["now"]["m15"]["has_time_utc"] is True
    assert xau["bars"]["now"]["m15"]["n"] == 2000
    assert xau["bars"]["now"]["m15"]["last_utc"] == "2026-09-18T04:15:00Z"
    assert xau["bars"]["now"]["m15"]["fresh_at_as_of"] is True
    assert "m15_stale_vs_now" not in xau["gaps"]
    assert "parent_shadows_fresher_multi" not in xau["gaps"]
    assert not xau.get("unused_newer_multi")
    assert inv["disk"]["xau_parent_vs_multi"]["parent_equals_multi"] is True


def test_gbpusd_with_tape_is_sufficient():
    inv = collect_inventory(now=PINNED_NOW)
    gbp = next(r for r in inv["jev_rows"] if r["symbol"] == "GBPUSD")
    assert gbp["challenge_tape_present"] is True
    assert gbp["admit"]["sit_as_of"] is True
    assert gbp["admit"]["now"] is True
    assert gbp["state_assembled"]["sit_as_of"]["books_for_symbol_substituted_xau"] is False
    assert "challenge_m15_h4_missing" not in gbp["gaps"]
    assert gbp["bars"]["now"]["m15"]["has_time_utc"] is True


def test_gbpjpy_landed_on_jev_watch():
    watch = jev_watch_symbols()
    assert "GBPJPY" in watch
    inv = collect_inventory(now=PINNED_NOW)
    jpy = next(r for r in inv["jev_rows"] if r["symbol"] == "GBPJPY")
    assert jpy["challenge_tape_present"] is True
    assert jpy["admit"]["now"] is True
    assert jpy["role"] == "chair_landed"
    assert jpy["state_assembled"]["now"]["family_class"] == "house_keep"


def test_gbpusd_m15_h4_without_d1_is_sufficient():
    as_of = datetime(2026, 9, 17, 11, 5, tzinfo=timezone.utc)

    def _tf_book(n: int, start: datetime, step_hours: float) -> list[StampedBar]:
        out = []
        for i in range(n):
            utc = start + timedelta(hours=step_hours * i)
            out.append(
                StampedBar(
                    broker_naive=utc.replace(tzinfo=None) + timedelta(hours=3),
                    utc=utc,
                    bar=Bar(o=1.0, h=1.1, l=0.9, c=1.0, v=1.0),
                    source_path="tmp",
                )
            )
        return out

    books = {
        "m15": _tf_book(16, datetime(2026, 9, 17, 7, 0, tzinfo=timezone.utc), 0.25),
        "h4": _tf_book(16, datetime(2026, 9, 16, 1, 0, tzinfo=timezone.utc), 4.0),
        "d1": [],
    }
    state = assemble_gold_state_v0(
        as_of_utc=as_of,
        side="long",
        sleeve="vss_fxcross_london_up_low",
        symbol="GBPUSD",
        origin_organism="f5_challenge",
        books=books,
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        geometry={"entry": 1.34, "stop": 1.338, "stop_dist": 0.002},
        cost={"spread_r_of_stop": 0.05},
        sleeve_features={"tag": "vss_fxcross_london_up_low"},
    )
    assert state["completeness"]["state_sufficient_for_live"] is True
    assert "timeframes.d1" in state["completeness"]["missing_fields"]


def test_next_pull_drops_landed_peers_keeps_uk100_and_april_lock():
    inv = collect_inventory(now=PINNED_NOW)
    items = [row["item"] for row in inv["next_pull"]]
    joined = " ".join(items)
    assert "UK100" in joined
    assert any("Do not pull BTCUSD" in item for item in items)
    assert any("April" in item for item in items)
    assert not any("Promote" in item and "XAUUSD" in item for item in items)
    assert not any("XAUUSD M15 refresh" in item for item in items)
    for phrase in (
        "EURUSD M15+H4 Challenge-true",
        "GBPUSD M15+H4 Challenge-true",
        "USDJPY M15+H4 Challenge-true",
        "EURGBP M15+H4 Challenge-true",
        "GBPJPY M15+H4 Challenge-true",
    ):
        assert not any(phrase in item for item in items)


def test_markdown_columns_and_score_slate_april_default(tmp_path):
    inv = collect_inventory(now=PINNED_NOW)
    md = render_markdown(inv)
    for col in MARKDOWN_COLUMNS:
        assert col in md
    assert "load_gold_books()" in md
    assert "April XAU" in md
    assert "never_apply_size=True" in md
    assert "PR #13" in md
    assert "PR #15" in md
    assert "Non-XAU Challenge books present: **True**" in md
    assert "parent_equals_multi=True" in md
    assert "admit_now=yes" in md
    assert "parent_shadows_fresher_multi" not in md
    assert "Promote multi/" not in md
    receipt = write_markdown(tmp_path / "inv.md", tmp_path / "inv.json", inv=inv)
    assert receipt["never_place"] is True
    assert receipt["never_apply_size"] is True
    assert receipt["non_xau_books_present"] is True
    written = (tmp_path / "inv.md").read_text(encoding="utf-8")
    assert "| symbol | bars present | state assembled | scored live | gaps | next pull |" in written
    payload = (tmp_path / "inv.json").read_text(encoding="utf-8")
    assert SCHEMA in payload


def test_jev_watch_includes_priority_and_xau():
    watch = jev_watch_symbols()
    assert watch[0] == "XAUUSD"
    for sym in MULTI_SYMBOL_PRIORITY:
        assert sym in watch
    assert "USDJPY" in watch
    assert "XAGUSD" in watch
    assert "GBPJPY" in watch
