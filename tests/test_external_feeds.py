import json
import shutil
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.components.external_feeds import (
    CftcCotFeed,
    ExternalFeedSchemaError,
    ExternalFeedStore,
    FeedStatus,
    FlashAlphaGexFeed,
    FredFeed,
    HttpResponse,
    LbmaFixCalendar,
    WgcGoldhubImport,
    build_feature_snapshot,
    cftc_publication_utc,
    ensure_utc,
    external_feed_env_status,
    fred_daily_market_publication_utc,
    select_asof_row,
    validate_required_fields,
)
from scripts.fetch_external_feeds import (
    DEFAULT_FLASHALPHA_PROXIES,
    DEFAULT_FRED_SERIES,
    build_parser,
    next_monthly_options_expiration,
    parse_contract_map,
    parse_proxy_map,
)
from scripts.build_external_feed_snapshots_historical import (
    DEFAULT_SYMBOLS,
    build_snapshot_from_index,
    build_historical_snapshots,
    load_candle_closes,
    parse_group_filters,
    parse_symbol_aliases,
    prepare_snapshot_index,
    write_historical_snapshots,
)
from scripts.build_external_feed_validation_dataset import (
    Candle,
    build_validation_rows,
    load_mt5_candles,
    validate_snapshot_no_lookahead,
)
from scripts.build_external_feed_candidate_dataset import (
    TradeRecordOutcome,
    build_candidate_validation_rows,
    load_trade_record_index,
    load_validation_index,
    normalize_candidate_candle_close,
)
from scripts.analyze_external_feed_candidate_diagnostics import (
    build_candidate_diagnostics,
    summarize_numeric_field,
)
from scripts.export_mt5_research_ohlcv import (
    SymbolSpec,
    export_research_ohlcv,
    parse_symbol_specs,
    parse_timeframe_names,
)
from src.utils.broker_clock import fixed_offset_rule
from scripts.inspect_mt5_history_availability import inspect_history_availability


@pytest.fixture
def tmp_path():
    """Repo-local tmp path for this module.

    The trading workstation can deny pytest's default Windows temp root under
    sandboxed runs. Keep these external-feed tests isolated without touching
    production paths.
    """

    path = Path(".test_tmp") / f"external_feeds_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


class FakeHttpClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, *, headers=None, timeout=30):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        return HttpResponse(
            status_code=200,
            content=json.dumps(self.payload).encode("utf-8"),
            headers={},
            url=url,
        )


def test_store_writes_raw_normalized_status_and_feature_snapshot(tmp_path):
    store = ExternalFeedStore(tmp_path / "external")
    fetched_at = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)

    artifact = store.write_raw(
        "fred",
        "DGS10.json",
        b'{"observations":[]}',
        fetched_at_utc=fetched_at,
    )
    assert artifact.checksum_sha256
    assert artifact.size_bytes == len(b'{"observations":[]}')
    assert (tmp_path / "external" / "raw" / "fred" / "DGS10.json").exists()
    assert (
        tmp_path / "external" / "raw" / "fred" / "DGS10.json.meta.json"
    ).exists()

    normalized = store.write_normalized_rows(
        "fred",
        "observations",
        [{"source": "fred", "series_id": "DGS10", "value": 4.1}],
        fetched_at_utc=fetched_at,
    )
    assert store.read_jsonl(normalized)[0]["series_id"] == "DGS10"

    status = FeedStatus(
        source="fred",
        status="fresh",
        fetched_at_utc=fetched_at,
        row_count=1,
        message="ok",
    )
    store.write_status(status)
    assert store.read_status("fred").message == "ok"
    keyed_status = FeedStatus(
        source="fred",
        status_key="DGS10",
        status="fresh",
        fetched_at_utc=fetched_at,
        row_count=1,
        message="series ok",
    )
    keyed_path = store.write_status(keyed_status)
    assert keyed_path.name == "fred__DGS10.json"
    assert store.read_status("fred", "DGS10").status_id == "fred:DGS10"
    assert store.list_statuses()[0].source == "fred"
    assert {status.status_id for status in store.list_statuses("fred")} == {
        "fred",
        "fred:DGS10",
    }

    feature_path = store.write_feature_snapshot(
        "XAUUSD",
        fetched_at,
        {"symbol": "XAUUSD", "candle_close_utc": fetched_at.isoformat()},
    )
    assert feature_path.exists()


def test_store_reads_latest_normalized_rows_per_table(tmp_path):
    store = ExternalFeedStore(tmp_path / "external")
    old_time = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)
    new_time = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)

    store.write_normalized_rows(
        "fred",
        "DGS10_observations",
        [{"source": "fred", "series_id": "DGS10", "value": 4.0}],
        fetched_at_utc=old_time,
    )
    store.write_normalized_rows(
        "fred",
        "DGS10_observations",
        [{"source": "fred", "series_id": "DGS10", "value": 4.1}],
        fetched_at_utc=new_time,
    )
    store.write_normalized_rows(
        "fred",
        "VIXCLS_observations",
        [{"source": "fred", "series_id": "VIXCLS", "value": 18.0}],
        fetched_at_utc=old_time,
    )

    rows = store.read_latest_normalized_rows("fred")

    assert {row["series_id"] for row in rows} == {"DGS10", "VIXCLS"}
    assert next(row for row in rows if row["series_id"] == "DGS10")["value"] == 4.1


def test_validate_required_fields_rejects_missing_required_field():
    with pytest.raises(ExternalFeedSchemaError):
        validate_required_fields(
            [{"source": "fred"}],
            ("source", "series_id"),
            source="fred",
        )


def test_select_asof_row_uses_publication_time_not_observation_date():
    rows = [
        {
            "gtos_symbol": "XAUUSD",
            "observation_date": "2026-04-01",
            "published_at_utc": "2026-04-05T00:00:00+00:00",
            "value": "future publication",
        },
        {
            "gtos_symbol": "XAUUSD",
            "observation_date": "2026-03-25",
            "published_at_utc": "2026-03-29T00:00:00+00:00",
            "value": "available",
        },
    ]

    selected = select_asof_row(
        rows,
        "2026-04-02T12:00:00+00:00",
        symbol="XAUUSD",
    )
    assert selected["value"] == "available"

    selected_after_publication = select_asof_row(
        rows,
        "2026-04-06T12:00:00+00:00",
        symbol="XAUUSD",
    )
    assert selected_after_publication["value"] == "future publication"


def test_build_feature_snapshot_prefixes_sources_and_marks_missing():
    snapshot = build_feature_snapshot(
        symbol="NAS100",
        candle_close_utc="2026-04-30T16:00:00Z",
        source_rows={
            "flashalpha_gex": [
                {
                    "source": "flashalpha_gex",
                    "gtos_symbol": "NAS100",
                    "proxy_symbol": "QQQ",
                    "as_of_utc": "2026-04-30T15:45:00Z",
                    "net_gex": -10.0,
                }
            ],
            "fred": [],
        },
    )

    assert snapshot["symbol"] == "NAS100"
    assert snapshot["flashalpha_gex__available"] is True
    assert snapshot["flashalpha_gex__net_gex"] == -10.0
    assert snapshot["fred__available"] is False


def test_build_feature_snapshot_groups_multi_series_sources():
    snapshot = build_feature_snapshot(
        symbol="XAUUSD",
        candle_close_utc="2026-04-30T16:00:00Z",
        source_rows={
            "fred": [
                {
                    "source": "fred",
                    "series_id": "DGS10",
                    "observation_date": "2026-04-01",
                    "published_at_utc": "2026-04-30T15:00:00Z",
                    "value": 4.0,
                },
                {
                    "source": "fred",
                    "series_id": "DGS10",
                    "observation_date": "2026-04-30",
                    "published_at_utc": "2026-04-30T15:00:00Z",
                    "value": 4.12,
                },
                {
                    "source": "fred",
                    "series_id": "VIXCLS",
                    "observation_date": "2026-04-30",
                    "published_at_utc": "2026-04-30T15:00:00Z",
                    "value": 18.5,
                },
                {
                    "source": "fred",
                    "series_id": "DGS2",
                    "observation_date": "2026-04-30",
                    "published_at_utc": "2026-04-30T17:00:00Z",
                    "value": 3.8,
                },
            ],
        },
    )

    assert snapshot["fred__available"] is True
    assert snapshot["fred__DGS10__value"] == 4.12
    assert snapshot["fred__VIXCLS__value"] == 18.5
    assert snapshot["fred__DGS2__available"] is False


def test_fred_build_url_and_parse_observations():
    url = FredFeed.build_observations_url(
        "DGS10",
        "key value",
        start_date=date(2026, 1, 1),
        end_date="2026-01-31",
    )
    assert "series_id=DGS10" in url
    assert "api_key=key+value" in url
    assert "observation_start=2026-01-01" in url

    rows = FredFeed.parse_observations(
        {
            "observations": [
                {
                    "realtime_start": "2026-04-30",
                    "realtime_end": "2026-04-30",
                    "date": "2026-04-29",
                    "value": ".",
                },
                {
                    "realtime_start": "2026-04-30",
                    "realtime_end": "2026-04-30",
                    "date": "2026-04-30",
                    "value": "4.12",
                },
            ]
        },
        series_id="DGS10",
        fetched_at_utc=datetime(2026, 4, 30, tzinfo=timezone.utc),
    )
    assert rows[0]["value"] is None
    assert rows[1]["value"] == 4.12
    assert rows[1]["series_id"] == "DGS10"
    assert rows[1]["published_at_utc"] == "2026-05-01T00:00:00+00:00"
    assert rows[1]["publication_time_model"] == "observation_date_plus_1d_utc"


def test_fred_fetch_series_writes_raw_normalized_and_status(tmp_path):
    fake_http = FakeHttpClient(
        {
            "observations": [
                {
                    "realtime_start": "2026-04-30",
                    "realtime_end": "2026-04-30",
                    "date": "2026-04-30",
                    "value": "4.12",
                }
            ]
        }
    )
    store = ExternalFeedStore(tmp_path / "external")
    feed = FredFeed(store, http_client=fake_http, env={"FRED_API_KEY": "k"})

    rows = feed.fetch_series("DGS10")

    assert len(rows) == 1
    assert "api_key=k" in fake_http.calls[0]["url"]
    assert list((tmp_path / "external" / "raw" / "fred").glob("*.json"))
    assert list((tmp_path / "external" / "normalized" / "fred").glob("*.jsonl"))
    assert store.read_status("fred", "DGS10").row_count == 1


def test_flashalpha_parse_gex_normalizes_walls_and_asof():
    row = FlashAlphaGexFeed.parse_gex(
        {
            "symbol": "QQQ",
            "underlying_price": 450.25,
            "gamma_flip": 448.0,
            "net_gex": -123456.0,
            "net_gex_label": "negative",
            "call_wall": {"strike": 455, "gex": 10},
            "put_wall": {"strike": 440, "gex": -12},
            "as_of": "2026-04-30T20:00:00Z",
        },
        proxy_symbol="QQQ",
        gtos_symbol="NAS100",
        expiration="2026-05-15",
    )

    assert row["source"] == "flashalpha_gex"
    assert row["gtos_symbol"] == "NAS100"
    assert row["expiration"] == "2026-05-15"
    assert row["call_wall"] == 455.0
    assert row["put_wall"] == 440.0
    assert row["as_of_utc"] == "2026-04-30T20:00:00+00:00"


def test_flashalpha_fetch_gex_writes_raw_normalized_and_status(tmp_path):
    fake_http = FakeHttpClient(
        {
            "underlying_price": 450.25,
            "gamma_flip": 448.0,
            "net_gex": -123456.0,
            "net_gex_label": "negative",
            "as_of": "2026-04-30T20:00:00Z",
        }
    )
    store = ExternalFeedStore(tmp_path / "external")
    feed = FlashAlphaGexFeed(
        store,
        http_client=fake_http,
        env={"FLASHALPHA_API_KEY": "flash-key"},
    )

    row = feed.fetch_gex("QQQ", gtos_symbol="NAS100", expiration="2026-05-15")

    assert row["gtos_symbol"] == "NAS100"
    assert fake_http.calls[0]["headers"] == {"X-Api-Key": "flash-key"}
    assert "expiration=2026-05-15" in fake_http.calls[0]["url"]
    assert list((tmp_path / "external" / "normalized" / "flashalpha_gex").glob("*.jsonl"))
    assert store.read_status(
        "flashalpha_gex",
        "QQQ_NAS100_2026-05-15",
    ).row_count == 1


def test_cftc_parse_rows_maps_gold_and_computes_nets():
    rows = CftcCotFeed.parse_rows(
        [
            {
                "cftc_contract_market_code": "088691",
                "report_date_as_yyyy_mm_dd": "2026-04-28T00:00:00.000",
                "market_and_exchange_names": "GOLD - COMMODITY EXCHANGE INC.",
                "open_interest_all": "1000",
                "m_money_positions_long_all": "700",
                "m_money_positions_short_all": "450",
                "m_money_positions_spread_all": "50",
                "prod_merc_positions_long_all": "200",
                "prod_merc_positions_short_all": "500",
                "swap_positions_long_all": "100",
                "swap__positions_short_all": "150",
            },
            {
                "cftc_contract_market_code": "UNMAPPED",
                "report_date_as_yyyy_mm_dd": "2026-04-28",
            },
        ],
        report_type="disagg_combined",
        contract_map={"088691": "XAUUSD"},
        fetched_at_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )

    assert len(rows) == 1
    assert rows[0]["gtos_symbol"] == "XAUUSD"
    assert rows[0]["managed_money_net"] == 250
    assert rows[0]["producer_merchant_net"] == -300
    assert rows[0]["swap_dealer_net"] == -50
    assert rows[0]["published_at_utc"] == "2026-05-01T19:30:00+00:00"
    assert rows[0]["publication_time_model"] == "cftc_release_schedule_1530_et"


def test_cftc_fetch_dataset_uses_app_token_and_writes_status(tmp_path):
    fake_http = FakeHttpClient(
        [
            {
                "cftc_contract_market_code": "088691",
                "report_date_as_yyyy_mm_dd": "2026-04-28T00:00:00.000",
                "market_and_exchange_names": "GOLD - COMMODITY EXCHANGE INC.",
                "open_interest_all": "1000",
                "m_money_positions_long_all": "700",
                "m_money_positions_short_all": "450",
            }
        ]
    )
    store = ExternalFeedStore(tmp_path / "external")
    feed = CftcCotFeed(store, http_client=fake_http, env={"SOCRATA_APP_TOKEN": "tok"})

    rows = feed.fetch_dataset(
        dataset_id=CftcCotFeed.DISAGG_COMBINED,
        report_type="disagg_combined",
        contract_map={"088691": "XAUUSD"},
    )

    assert len(rows) == 1
    assert fake_http.calls[0]["headers"] == {"X-App-Token": "tok"}
    assert "%24limit=50000" in fake_http.calls[0]["url"]
    assert list((tmp_path / "external" / "normalized" / "cftc_cot").glob("*.jsonl"))
    assert store.read_status(
        "cftc_cot",
        "disagg_combined_088691_XAUUSD",
    ).row_count == 1


def test_cftc_fetch_dataset_accepts_operator_socrata_alias(tmp_path):
    fake_http = FakeHttpClient(
        [
            {
                "cftc_contract_market_code": "088691",
                "report_date_as_yyyy_mm_dd": "2026-04-28",
            }
        ]
    )
    store = ExternalFeedStore(tmp_path / "external")
    feed = CftcCotFeed(store, http_client=fake_http, env={"SOCRATA_TOKEN": "tok"})

    feed.fetch_dataset(
        dataset_id=CftcCotFeed.DISAGG_COMBINED,
        report_type="disagg_combined",
        contract_map={"088691": "XAUUSD"},
    )

    assert fake_http.calls[0]["headers"] == {"X-App-Token": "tok"}


def test_wgc_import_csv_normalizes_goldhub_rows_and_writes_status(tmp_path):
    csv_path = tmp_path / "goldhub_etf_flows.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Month,Region,Flow tonnes,Fund flows US$mn,Total holdings tonnes,Published Date",
                'Mar-26,North America,"1,234.5",(56.7),3000.1,2026-04-08',
            ]
        ),
        encoding="utf-8",
    )
    store = ExternalFeedStore(tmp_path / "external")
    importer = WgcGoldhubImport(store)

    rows = importer.import_csv_file(csv_path, dataset="gold_etf_flows")

    assert rows[0]["source"] == "wgc"
    assert rows[0]["dataset"] == "gold_etf_flows"
    assert rows[0]["observation_date"] == "2026-03-31"
    assert rows[0]["published_at_utc"] == "2026-04-08T00:00:00+00:00"
    assert rows[0]["flow_tonnes"] == 1234.5
    assert rows[0]["flow_usd_mn"] == -56.7
    assert rows[0]["gtos_symbol"] == "XAUUSD"
    assert list((tmp_path / "external" / "raw" / "wgc").glob("*.csv"))
    assert list((tmp_path / "external" / "normalized" / "wgc").glob("*.jsonl"))
    assert store.read_status("wgc", "gold_etf_flows").row_count == 1

    snapshot = build_feature_snapshot(
        symbol="XAUUSD",
        candle_close_utc="2026-04-09T00:00:00Z",
        source_rows={"wgc": rows},
    )
    assert snapshot["wgc__available"] is True
    assert snapshot["wgc__gold_etf_flows__flow_tonnes"] == 1234.5


def test_wgc_gold_etf_xlsx_parsers_normalize_summary_and_monthly_rows():
    fetched_at = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    periods = WgcGoldhubImport._parse_periods(
        [
            ["DB Name", "Title", "From", "To"],
            ["1MONTH", "Mar 26", 46081, 46112],
            ["QTD_FULLMONTH", "Q1 26", 46022, 46112],
        ]
    )
    key_rows = [
        [None, "Mar 26", None, None, None, None, "As of 31/03/2026", None, "Q1 26"],
        [
            None,
            None,
            "Total AUM (bn)",
            "Fund Flows (US$mn)",
            "Holdings (tonnes)",
            "Demand (tonnes)",
            "Demand (% of holdings)",
            None,
            None,
            "Total AUM (bn)",
            "Fund Flows (US$mn)",
            "Holdings (tonnes)",
            "Demand (tonnes)",
            "Demand (% of holdings)",
        ],
        [],
        [
            None,
            "Total",
            606.5,
            -11834.8,
            4087.79,
            -84.83,
            -0.0203,
            None,
            "Total",
            606.5,
            12291.6,
            4087.79,
            62.0,
            0.0154,
        ],
    ]
    summary_rows = WgcGoldhubImport._parse_gold_etf_key_tables(
        key_rows,
        periods=periods,
        source_name="ETF_Flows_March_2026.xlsx",
        default_gtos_symbol="XAUUSD",
        fetched_at_utc=fetched_at,
    )

    assert summary_rows[0]["dataset"] == "gold_etf_flows_mar_26_total"
    assert summary_rows[0]["observation_date"] == "2026-03-31"
    assert summary_rows[0]["flow_tonnes"] == -84.83
    assert summary_rows[0]["assets_usd_mn"] == 606500.0

    chart_rows = WgcGoldhubImport._parse_gold_etf_charts_data(
        [
            ["Bar chart"],
            ["Date", "North America", "Europe", "Asia", "Other"],
            [46112, -1000000, 2000000, 3000000, -500000, 3123.4, None, None, None, 46112, -1.0, 2.0, 3.0, -0.5],
        ],
        source_name="ETF_Flows_March_2026.xlsx",
        default_gtos_symbol="XAUUSD",
        fetched_at_utc=fetched_at,
    )

    total = next(row for row in chart_rows if row["region"] == "Total")
    assert total["dataset"] == "gold_etf_flows_monthly_total"
    assert total["observation_date"] == "2026-03-31"
    assert total["flow_usd_mn"] == 3.5
    assert total["flow_tonnes"] == 3.5


def test_wgc_gold_demand_trends_wide_parser_normalizes_periods():
    fetched_at = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    rows = WgcGoldhubImport._parse_gdt_wide_table(
        [
            [None, "Gold supply and demand WGC presentation"],
            [None, None, 2025, "Year-on-year % change", None, None, "Q1'26"],
            [None, "Total Supply", 5143.8, 1.7, None, None, 1195.9],
        ],
        sheet_name="Gold Balance",
        unit="tonnes",
        source_name="GDT_Tables_Q126_EN.xlsx",
        default_gtos_symbol="XAUUSD",
        fetched_at_utc=fetched_at,
    )

    annual = next(row for row in rows if row["frequency"] == "annual")
    quarterly = next(row for row in rows if row["frequency"] == "quarterly")
    assert annual["dataset"] == "gold_demand_trends_gold_balance_total_supply_annual"
    assert annual["observation_date"] == "2025-12-31"
    assert annual["flow_tonnes"] == 5143.8
    assert quarterly["observation_date"] == "2026-03-31"
    assert quarterly["value"] == 1195.9


def test_lbma_calendar_handles_2026_dst_transitions():
    rows = LbmaFixCalendar.generate(
        "2026-03-27", "2026-03-30", metals=("gold", "silver")
    )
    am_rows = [row for row in rows if row["fix_name"] == "AM"]
    silver_rows = [row for row in rows if row["metal"] == "silver"]

    before_bst = next(row for row in am_rows if row["trading_date_london"] == "2026-03-27")
    after_bst = next(row for row in am_rows if row["trading_date_london"] == "2026-03-30")
    silver_after_bst = next(
        row for row in silver_rows if row["trading_date_london"] == "2026-03-30"
    )

    assert before_bst["fix_time_utc"].endswith("10:30:00+00:00")
    assert after_bst["fix_time_utc"].endswith("09:30:00+00:00")
    assert after_bst["gtos_symbol"] == "XAUUSD"
    assert silver_after_bst["fix_name"] == "DAILY"
    assert silver_after_bst["gtos_symbol"] == "XAGUSD"
    assert silver_after_bst["fix_time_utc"].endswith("11:00:00+00:00")
    assert after_bst["uk_us_dst_misalignment"] is False

    snapshot = build_feature_snapshot(
        symbol="XAUUSD",
        candle_close_utc="2026-03-30T12:30:00Z",
        source_rows={"lbma_calendar": rows},
    )
    assert snapshot["lbma_calendar__available"] is True
    assert snapshot["lbma_calendar__metal"] == "gold"
    assert snapshot["lbma_calendar__fix_name"] == "AM"

    october_rows = LbmaFixCalendar.generate("2026-10-26", "2026-10-26", metals=("gold",))
    october_am = next(row for row in october_rows if row["fix_name"] == "AM")
    assert october_am["fix_time_utc"].endswith("10:30:00+00:00")
    assert october_am["uk_us_dst_misalignment"] is True


def test_external_feed_env_status_does_not_expose_values():
    status = external_feed_env_status(
        {
            "FRED_API_KEY": "secret",
            "FLASHALPHA_API_KEY": "",
            "SOCRATA_APP_TOKEN": "token",
        }
    )

    assert status["fred"]["FRED_API_KEY"] is True
    assert status["flashalpha_gex"]["FLASHALPHA_API_KEY"] is False
    assert status["cftc_cot"]["SOCRATA_APP_TOKEN"] is True
    assert "secret" not in json.dumps(status)


def test_fetch_script_mapping_parsers():
    assert parse_contract_map(["123456:USDJPY"]) == {
        "088691": "XAUUSD",
        "123456": "USDJPY",
    }
    assert parse_proxy_map(["QQQ:NAS100", "DIA:US30"]) == [
        ("QQQ", "NAS100"),
        ("DIA", "US30"),
    ]
    assert DEFAULT_FRED_SERIES == (
        "DGS10",
        "DGS2",
        "DFII10",
        "T10YIE",
        "VIXCLS",
        "GVZCLS",
        "DTWEXBGS",
    )
    assert DEFAULT_FLASHALPHA_PROXIES == (
        "QQQ:NAS100",
        "DIA:US30",
        "SPY:US30",
        "GLD:XAUUSD",
        "SLV:XAGUSD",
    )
    assert next_monthly_options_expiration(date(2026, 5, 1)).isoformat() == "2026-05-15"
    assert next_monthly_options_expiration(date(2026, 5, 16)).isoformat() == "2026-06-19"


def test_historical_snapshot_defaults_cover_frozen_calendar_macro_symbols():
    assert {
        "XAUUSD",
        "XAGUSD",
        "GBPUSD",
        "USDJPY",
        "GBPJPY",
    }.issubset(set(DEFAULT_SYMBOLS))


def test_ensure_utc_accepts_z_suffix_and_naive_datetime():
    assert ensure_utc("2026-04-30T20:00:00Z").tzinfo == timezone.utc
    assert (
        ensure_utc(datetime(2026, 4, 30, 20, 0)).isoformat()
        == "2026-04-30T20:00:00+00:00"
    )


def test_publication_time_models_are_conservative_and_handle_cftc_catchup():
    assert (
        fred_daily_market_publication_utc("2026-04-30").isoformat()
        == "2026-05-01T00:00:00+00:00"
    )
    assert (
        cftc_publication_utc("2026-04-28").isoformat()
        == "2026-05-01T19:30:00+00:00"
    )
    assert (
        cftc_publication_utc("2025-10-21").isoformat()
        == "2025-12-02T20:30:00+00:00"
    )


def test_daily_fetch_wrapper_runs_shadow_steps(tmp_path, monkeypatch, capsys):
    calls = {"fred": [], "cftc": [], "flashalpha": []}

    def fake_fred_fetch(self, series_id, *, start_date=None, end_date=None, api_key=None):
        calls["fred"].append((series_id, start_date, end_date))
        return [{"series_id": series_id}]

    def fake_cftc_fetch(
        self,
        *,
        dataset_id,
        report_type,
        contract_map,
        where=None,
        limit=50_000,
    ):
        calls["cftc"].append((dataset_id, report_type, contract_map, where, limit))
        return [{"report_type": report_type}]

    def fake_flashalpha_fetch(
        self,
        proxy_symbol,
        *,
        gtos_symbol=None,
        expiration=None,
        api_key=None,
    ):
        calls["flashalpha"].append((proxy_symbol, gtos_symbol, expiration))
        return {"proxy_symbol": proxy_symbol}

    monkeypatch.setattr(FredFeed, "fetch_series", fake_fred_fetch)
    monkeypatch.setattr(CftcCotFeed, "fetch_dataset", fake_cftc_fetch)
    monkeypatch.setattr(FlashAlphaGexFeed, "fetch_gex", fake_flashalpha_fetch)

    args = build_parser().parse_args(
        [
            "daily",
            "--root",
            str(tmp_path / "external"),
            "--fred-series",
            "DGS10",
            "--fred-start",
            "2026-01-01",
            "--lbma-start",
            "2026-05-01",
            "--lbma-days",
            "1",
            "--proxy",
            "QQQ:NAS100",
            "--expiration",
            "2026-05-15",
        ]
    )

    assert args.func(args) == 0
    output = capsys.readouterr().out

    assert calls["fred"] == [("DGS10", "2026-01-01", None)]
    assert calls["cftc"][0][1] == "disagg_combined"
    assert calls["flashalpha"] == [("QQQ", "NAS100", "2026-05-15")]
    assert "wgc: operator_required" in output


def test_historical_snapshot_generator_uses_candle_close_no_lookahead(tmp_path):
    store = ExternalFeedStore(tmp_path / "external")
    fetched_at = datetime(2026, 5, 1, tzinfo=timezone.utc)
    store.write_normalized_rows(
        "fred",
        "DGS10_observations",
        [
            {
                "source": "fred",
                "series_id": "DGS10",
                "observation_date": "2026-04-30",
                "published_at_utc": "2026-05-01T00:00:00Z",
                "value": 4.0,
            },
            {
                "source": "fred",
                "series_id": "DGS10",
                "observation_date": "2026-05-01",
                "published_at_utc": "2026-05-01T02:00:00Z",
                "value": 4.2,
            },
        ],
        fetched_at_utc=fetched_at,
    )
    data_dir = tmp_path / "historical"
    data_dir.mkdir()
    (data_dir / "XAUUSD_M15.csv").write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-05-01 01:30:00,1,2,1,2,10",
                "2026-05-01 01:45:00,1,2,1,2,10",
            ]
        ),
        encoding="utf-8",
    )

    snapshots = build_historical_snapshots(
        store=store,
        data_dir=data_dir,
        symbols=["XAUUSD"],
        sources=["fred"],
        start="2026-05-01T01:45:00Z",
        end="2026-05-01T02:00:00Z",
    )["XAUUSD"]

    assert snapshots[0]["bar_time_utc"] == "2026-05-01T01:30:00+00:00"
    assert snapshots[0]["candle_close_utc"] == "2026-05-01T01:45:00+00:00"
    assert snapshots[0]["fred__DGS10__value"] == 4.0
    assert snapshots[1]["candle_close_utc"] == "2026-05-01T02:00:00+00:00"
    assert snapshots[1]["fred__DGS10__value"] == 4.2


def test_historical_snapshot_index_filters_grouped_wgc_rows():
    index = prepare_snapshot_index(
        {
            "wgc": [
                {
                    "source": "wgc",
                    "dataset": "gold_etf_flows_monthly_total",
                    "gtos_symbol": "XAUUSD",
                    "published_at_utc": "2026-05-01T00:00:00Z",
                    "observation_date": "2026-03-31",
                    "flow_tonnes": 10.0,
                },
                {
                    "source": "wgc",
                    "dataset": "exploratory_not_frozen",
                    "gtos_symbol": "XAUUSD",
                    "published_at_utc": "2026-05-01T00:00:00Z",
                    "observation_date": "2026-03-31",
                    "flow_tonnes": 99.0,
                },
            ]
        },
        group_filters=parse_group_filters(None),
    )

    snapshot = build_snapshot_from_index(
        symbol="XAUUSD",
        candle_close_utc="2026-05-01T01:00:00Z",
        snapshot_index=index,
    )

    assert snapshot["wgc__available"] is True
    assert snapshot["wgc__gold_etf_flows_monthly_total__flow_tonnes"] == 10.0
    assert "wgc__exploratory_not_frozen__flow_tonnes" not in snapshot


def test_historical_snapshot_lbma_calendar_exposes_known_next_fix():
    index = prepare_snapshot_index(
        {
            "lbma_calendar": LbmaFixCalendar.generate(
                "2026-03-30",
                "2026-03-30",
                metals=("gold",),
            )
        }
    )

    before_fix = build_snapshot_from_index(
        symbol="XAUUSD",
        candle_close_utc="2026-03-30T09:15:00Z",
        snapshot_index=index,
    )
    after_fix = build_snapshot_from_index(
        symbol="XAUUSD",
        candle_close_utc="2026-03-30T09:45:00Z",
        snapshot_index=index,
    )

    assert before_fix["lbma_calendar__available"] is True
    assert "lbma_calendar__fix_time_utc" not in before_fix
    assert before_fix["lbma_calendar__next_fix_time_utc"] == "2026-03-30T09:30:00+00:00"
    assert before_fix["lbma_calendar__minutes_to_next_fix"] == 15.0
    assert before_fix["lbma_calendar__in_fix_window_30m"] is True
    assert after_fix["lbma_calendar__fix_time_utc"] == "2026-03-30T09:30:00+00:00"
    assert after_fix["lbma_calendar__minutes_since_previous_fix"] == 15.0
    assert after_fix["lbma_calendar__next_fix_time_utc"] == "2026-03-30T14:00:00+00:00"


def test_historical_snapshot_writer_and_alias_parser(tmp_path):
    data_dir = tmp_path / "historical"
    data_dir.mkdir()
    csv_path = data_dir / "US30_cash_M5.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-05-01 01:00:00,1,2,1,2,10",
            ]
        ),
        encoding="utf-8",
    )

    closes = load_candle_closes(csv_path, timeframe="M5")
    assert closes == [
        {
            "bar_time_utc": "2026-05-01T01:00:00+00:00",
            "candle_close_utc": "2026-05-01T01:05:00+00:00",
        }
    ]
    assert parse_symbol_aliases(["US30_cash:US30"])["US30_cash"] == "US30"

    store = ExternalFeedStore(tmp_path / "external")
    paths = write_historical_snapshots(
        store=store,
        snapshots_by_symbol={"US30_cash": [{"symbol": "US30", "x": 1}]},
        timeframe="M5",
        label="unit_test",
    )
    assert paths["US30_cash"].exists()
    assert json.loads(paths["US30_cash"].read_text(encoding="utf-8")) == {
        "symbol": "US30",
        "x": 1,
    }


def test_validation_dataset_labels_use_future_bars_only():
    candles = [
        Candle(
            bar_time_utc=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
            candle_close_utc=datetime(2026, 5, 1, 0, 15, tzinfo=timezone.utc),
            open=100.0,
            high=1000.0,
            low=99.0,
            close=100.0,
        ),
        Candle(
            bar_time_utc=datetime(2026, 5, 1, 0, 15, tzinfo=timezone.utc),
            candle_close_utc=datetime(2026, 5, 1, 0, 30, tzinfo=timezone.utc),
            open=100.0,
            high=106.0,
            low=98.0,
            close=104.0,
        ),
        Candle(
            bar_time_utc=datetime(2026, 5, 1, 0, 30, tzinfo=timezone.utc),
            candle_close_utc=datetime(2026, 5, 1, 0, 45, tzinfo=timezone.utc),
            open=104.0,
            high=105.0,
            low=97.0,
            close=102.0,
        ),
    ]
    rows, summary = build_validation_rows(
        snapshot_rows=[
            {
                "schema_version": "external_feeds_v1",
                "symbol": "XAUUSD",
                "file_symbol": "XAUUSD",
                "candle_close_utc": "2026-05-01T00:15:00Z",
                "fred__available": True,
                "fred__DGS10__published_at_utc": "2026-05-01T00:00:00Z",
            }
        ],
        candles=candles,
        horizons=[1, 2],
        bundle_id="calendar_macro_bundle_v1",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["label_h1__forward_return"] == pytest.approx(0.04)
    assert row["label_h1__max_up_return"] == pytest.approx(0.06)
    assert row["label_h2__forward_return"] == pytest.approx(0.02)
    assert row["label_h2__realized_range_return"] == pytest.approx(0.09)
    assert row["fold_month"] == "2026-05"
    assert summary["label_coverage"]["1"]["available_rows"] == 1
    assert summary["source_availability"]["fred__available"] == 1


def test_validation_dataset_rejects_future_source_timestamp():
    with pytest.raises(ValueError, match="future source timestamp"):
        validate_snapshot_no_lookahead(
            {
                "symbol": "XAUUSD",
                "candle_close_utc": "2026-05-01T00:15:00Z",
                "fred__DGS10__published_at_utc": "2026-05-01T00:16:00Z",
            },
            "2026-05-01T00:15:00Z",
        )


def test_validation_dataset_loads_mt5_csv_and_marks_tail_horizon(tmp_path):
    csv_path = tmp_path / "XAUUSD_M15.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-05-01 00:00:00,100,102,99,101,10",
                "2026-05-01 00:15:00,101,103,100,102,11",
            ]
        ),
        encoding="utf-8",
    )
    candles = load_mt5_candles(csv_path, timeframe="M15")

    rows, summary = build_validation_rows(
        snapshot_rows=[
            {
                "symbol": "XAUUSD",
                "file_symbol": "XAUUSD",
                "candle_close_utc": "2026-05-01T00:15:00Z",
            },
            {
                "symbol": "XAUUSD",
                "file_symbol": "XAUUSD",
                "candle_close_utc": "2026-05-01T00:30:00Z",
            },
        ],
        candles=candles,
        horizons=[1],
        bundle_id="calendar_macro_bundle_v1",
    )

    assert [c.candle_close_utc.isoformat() for c in candles] == [
        "2026-05-01T00:15:00+00:00",
        "2026-05-01T00:30:00+00:00",
    ]
    assert rows[0]["label_h1__has_full_horizon"] is True
    assert rows[0]["label_h1__forward_points"] == pytest.approx(1.0)
    assert rows[1]["label_h1__has_full_horizon"] is False
    assert rows[1]["label_h1__forward_return"] is None
    assert summary["label_coverage"]["1"] == {
        "available_rows": 1,
        "missing_rows": 1,
    }


def test_candidate_join_normalizes_seconds_and_attaches_outcome():
    validation_rows = {
        (
            "XAUUSD",
            "2026-05-01T13:15:00+00:00",
        ): {
            "schema_version": "external_feeds_v1",
            "symbol": "XAUUSD",
            "file_symbol": "XAUUSD",
            "candle_close_utc": "2026-05-01T13:15:00+00:00",
            "fred__available": True,
            "label_h1__forward_return": 0.01,
        }
    }
    trade_records = {
        (
            "XAUUSD",
            "2026-05-01T13:15:00+00:00",
        ): TradeRecordOutcome(
            path="knowledge_base/trade_records/XAUUSD/example.json",
            trade_id="XAUUSD_2026-05-01_ny_1315",
            final_outcome="FILLED",
            realized_r=1.5,
            level2_passed=True,
        )
    }

    rows, summary = build_candidate_validation_rows(
        candidate_rows=[
            {
                "timestamp_utc": "2026-05-01T13:15:52.698253+00:00",
                "symbol": "XAUUSD",
                "evaluation_id": "xau_eval",
                "decision": "CANDIDATE",
                "framework": "ob_retest",
                "kill_zone": "ny",
                "trade_parameters": {
                    "direction": "LONG",
                    "entry_price": 3300.0,
                    "stop_loss": 3290.0,
                    "take_profit_1": 3315.0,
                    "risk_reward_ratio": 1.5,
                },
            }
        ],
        validation_index=validation_rows,
        trade_record_index=trade_records,
    )

    assert len(rows) == 1
    assert rows[0]["external_validation_matched"] is True
    assert rows[0]["candidate__candle_close_utc"] == "2026-05-01T13:15:00+00:00"
    assert rows[0]["candidate__realized_r"] == pytest.approx(1.5)
    assert rows[0]["candidate__final_outcome"] == "FILLED"
    assert rows[0]["candidate__direction"] == "LONG"
    assert summary["validation_matched"] == 1
    assert summary["realized_r_available"] == 1


def test_candidate_join_can_simulate_opportunity_realized_r(tmp_path):
    csv_path = tmp_path / "XAUUSD_M15.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-05-01 13:30:00,101,102,99,100,10",
                "2026-05-01 13:45:00,100,111,99,110,11",
            ]
        ),
        encoding="utf-8",
    )

    rows, summary = build_candidate_validation_rows(
        candidate_rows=[
            {
                "timestamp_utc": "2026-05-01T13:15:05+00:00",
                "symbol": "XAUUSD",
                "decision": "CANDIDATE",
                "framework": "ob_retest",
                "trade_parameters": {
                    "direction": "LONG",
                    "entry_price": 100.0,
                    "stop_loss": 95.0,
                    "take_profit_1": 110.0,
                },
            }
        ],
        validation_index={
            ("XAUUSD", "2026-05-01T13:15:00+00:00"): {
                "symbol": "XAUUSD",
                "file_symbol": "XAUUSD",
                "candle_close_utc": "2026-05-01T13:15:00+00:00",
            }
        },
        trade_record_index={},
        simulate_opportunity=True,
        ohlcv_dir=tmp_path,
        max_hold_bars=4,
    )

    assert rows[0]["candidate__synthetic_outcome"] == "TP"
    assert rows[0]["candidate__synthetic_realized_r"] == pytest.approx(2.0)
    assert summary["synthetic_realized_r_available"] == 1
    assert summary["synthetic_outcomes"] == {"TP": 1}


def test_candidate_join_can_simulate_opportunity_on_m5_files(tmp_path):
    csv_path = tmp_path / "XAUUSD_M5.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-05-01 13:20:00,101,100.5,99.8,100.2,10",
                "2026-05-01 13:25:00,100.2,102.2,100.1,102.0,11",
            ]
        ),
        encoding="utf-8",
    )

    rows, summary = build_candidate_validation_rows(
        candidate_rows=[
            {
                "timestamp_utc": "2026-05-01T13:15:05+00:00",
                "symbol": "XAUUSD",
                "decision": "CANDIDATE",
                "framework": "ob_retest",
                "trade_parameters": {
                    "direction": "LONG",
                    "entry_price": 100.0,
                    "stop_loss": 99.0,
                    "take_profit_1": 102.0,
                },
            }
        ],
        validation_index={
            ("XAUUSD", "2026-05-01T13:15:00+00:00"): {
                "symbol": "XAUUSD",
                "file_symbol": "XAUUSD",
                "candle_close_utc": "2026-05-01T13:15:00+00:00",
            }
        },
        trade_record_index={},
        timeframe="M5",
        simulate_opportunity=True,
        ohlcv_dir=tmp_path,
        max_hold_bars=12,
    )

    assert rows[0]["candidate__synthetic_outcome"] == "TP"
    assert rows[0]["candidate__synthetic_realized_r"] == pytest.approx(2.0)
    assert rows[0]["candidate__synthetic_ohlcv_dir"] == str(tmp_path)
    assert summary["timeframe"] == "M5"
    assert summary["synthetic_realized_r_available"] == 1


def test_candidate_join_ohlcv_fallback_rejects_large_date_gap(tmp_path):
    stale_dir = tmp_path / "stale"
    good_dir = tmp_path / "good"
    stale_dir.mkdir()
    good_dir.mkdir()
    (stale_dir / "XAUUSD_M15.csv").write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-05-10 13:30:00,101,102,99,100,10",
            ]
        ),
        encoding="utf-8",
    )
    (good_dir / "XAUUSD_M15.csv").write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-05-01 13:30:00,101,102,99,100,10",
                "2026-05-01 13:45:00,100,111,99,110,11",
            ]
        ),
        encoding="utf-8",
    )

    rows, summary = build_candidate_validation_rows(
        candidate_rows=[
            {
                "timestamp_utc": "2026-05-01T13:15:05+00:00",
                "symbol": "XAUUSD",
                "decision": "CANDIDATE",
                "framework": "ob_retest",
                "trade_parameters": {
                    "direction": "LONG",
                    "entry_price": 100.0,
                    "stop_loss": 95.0,
                    "take_profit_1": 110.0,
                },
            }
        ],
        validation_index={},
        simulate_opportunity=True,
        ohlcv_dirs=[stale_dir, good_dir],
        max_hold_bars=4,
    )

    assert rows[0]["candidate__synthetic_outcome"] == "TP"
    assert rows[0]["candidate__synthetic_ohlcv_dir"] == str(good_dir)
    assert summary["synthetic_realized_r_available"] == 1


def test_candidate_join_leaves_off_boundary_timestamp_unmatched():
    assert normalize_candidate_candle_close("2026-05-01T00:25:03Z") is None

    rows, summary = build_candidate_validation_rows(
        candidate_rows=[
            {
                "timestamp_utc": "2026-05-01T00:25:03Z",
                "symbol": "USDJPY",
                "decision": "CANDIDATE",
                "framework": "breaker_re_entry",
                "trade_parameters": {"direction": "SHORT"},
            }
        ],
        validation_index={},
        trade_record_index={},
    )

    assert rows[0]["external_validation_matched"] is False
    assert rows[0]["external_validation_missing_reason"] == "candidate_timestamp_not_m15_aligned"
    assert rows[0]["candidate__realized_r_missing_reason"] == "trade_record_not_found"
    assert summary["validation_missing_reasons"] == {
        "candidate_timestamp_not_m15_aligned": 1
    }


def test_candidate_join_prefers_logged_canonical_candle_close():
    key = ("USDJPY", "2026-05-01T00:15:00+00:00")
    rows, summary = build_candidate_validation_rows(
        candidate_rows=[
            {
                "timestamp_utc": "2026-05-01T00:25:03Z",
                "candle_close_utc": "2026-05-01T00:15:00+00:00",
                "symbol": "USDJPY",
                "decision": "CANDIDATE",
                "framework": "breaker_re_entry",
                "trade_parameters": {"direction": "SHORT"},
            }
        ],
        validation_index={
            key: {
                "symbol": "USDJPY",
                "candle_close_utc": "2026-05-01T00:15:00+00:00",
                "fred__available": True,
            }
        },
        trade_record_index={},
    )

    assert rows[0]["external_validation_matched"] is True
    assert rows[0]["candidate__candle_close_utc"] == "2026-05-01T00:15:00+00:00"
    assert rows[0]["candidate__logged_candle_close_utc"] == "2026-05-01T00:15:00+00:00"
    assert summary["validation_matched"] == 1


def test_trade_record_index_prefers_canonical_candle_close(tmp_path):
    trade_dir = tmp_path / "records" / "USDJPY"
    trade_dir.mkdir(parents=True)
    record_path = trade_dir / "trade.json"
    record_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "symbol": "USDJPY",
                    "trade_id": "USDJPY_test",
                    "candle_time": "2026-05-01T00:25:03+00:00",
                    "candle_close_utc": "2026-05-01T00:15:00+00:00",
                },
                "decision_pipeline": {"final_outcome": "REJECTED_L2"},
                "exit": {"realized_R": 0.738},
            }
        ),
        encoding="utf-8",
    )

    index = load_trade_record_index(tmp_path / "records")

    assert ("USDJPY", "2026-05-01T00:15:00+00:00") in index
    assert index[("USDJPY", "2026-05-01T00:15:00+00:00")].trade_id == "USDJPY_test"
    assert index[("USDJPY", "2026-05-01T00:15:00+00:00")].realized_r == 0.738


def test_candidate_validation_index_streams_only_needed_keys(tmp_path):
    validation_path = tmp_path / "validation.jsonl"
    validation_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "schema_version": "external_feeds_v1",
                        "symbol": "US30",
                        "file_symbol": "US30_cash",
                        "candle_close_utc": "2026-05-01T13:30:00Z",
                        "fred__available": True,
                        "fred__DGS10__published_at_utc": "2026-05-01T00:00:00Z",
                    }
                ),
                json.dumps(
                    {
                        "schema_version": "external_feeds_v1",
                        "symbol": "US30",
                        "file_symbol": "US30_cash",
                        "candle_close_utc": "2026-05-01T13:45:00Z",
                        "fred__available": True,
                        "fred__DGS10__published_at_utc": "2026-05-01T00:00:00Z",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    index = load_validation_index(
        [validation_path],
        needed_keys={("US30", "2026-05-01T13:30:00+00:00")},
    )

    assert sorted(index) == [("US30", "2026-05-01T13:30:00+00:00")]
    assert index[("US30", "2026-05-01T13:30:00+00:00")]["file_symbol"] == "US30_cash"


def test_mt5_research_export_parses_aliases_and_timeframes():
    assert parse_symbol_specs(["NAS100:NDX100", "XAUUSD"]) == [
        SymbolSpec(file_symbol="NAS100", mt5_symbol="NDX100"),
        SymbolSpec(file_symbol="XAUUSD", mt5_symbol="XAUUSD"),
    ]
    assert parse_timeframe_names("M15,H1,D1") == ["M15", "H1", "D1"]


def test_mt5_research_export_chunks_dedupes_and_filters_range(tmp_path):
    class FakeMT5:
        TIMEFRAME_M15 = 15

        def __init__(self):
            self.calls = []

        def symbol_select(self, symbol, enable):
            assert symbol == "NDX100"
            assert enable is True
            return True

        def copy_rates_range(self, symbol, timeframe, start, end):
            self.calls.append((start, end))
            if len(self.calls) == 1:
                return [
                    {
                        "time": int(datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc).timestamp()),
                        "open": 1.0,
                        "high": 2.0,
                        "low": 0.5,
                        "close": 1.5,
                        "tick_volume": 10,
                    },
                    {
                        "time": int(datetime(2026, 5, 1, 0, 15, tzinfo=timezone.utc).timestamp()),
                        "open": 1.5,
                        "high": 2.5,
                        "low": 1.0,
                        "close": 2.0,
                        "tick_volume": 11,
                    },
                ]
            return [
                {
                    "time": int(datetime(2026, 5, 1, 0, 15, tzinfo=timezone.utc).timestamp()),
                    "open": 1.5,
                    "high": 2.5,
                    "low": 1.0,
                    "close": 2.0,
                    "tick_volume": 11,
                },
                {
                    "time": int(datetime(2026, 5, 1, 0, 30, tzinfo=timezone.utc).timestamp()),
                    "open": 2.0,
                    "high": 3.0,
                    "low": 1.5,
                    "close": 2.5,
                    "tick_volume": 12,
                },
            ]

        def last_error(self):
            return (0, "ok")

    result = export_research_ohlcv(
        mt5_module=FakeMT5(),
        specs=[SymbolSpec(file_symbol="NAS100", mt5_symbol="NDX100")],
        timeframe_names=["M15"],
        start=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 5, 1, 0, 30, tzinfo=timezone.utc),
        output_dir=tmp_path / "export",
        chunk=timedelta(minutes=15),
        clock=fixed_offset_rule(0, evidence="test fixture: bars are already true UTC, so a declared zero-offset clock keeps this test about chunking/manifest rather than the clock"),
    )

    stats = result["files"]["NAS100_M15"]
    assert stats["chunks_requested"] == 2
    assert stats["raw_rows_returned"] == 4
    assert stats["duplicate_rows_dropped"] == 1
    assert stats["rows"] == 2
    assert stats["first"] == "2026-05-01 00:00:00"
    assert stats["last"] == "2026-05-01 00:15:00"

    csv_rows = (tmp_path / "export" / "NAS100_M15.csv").read_text(encoding="utf-8").splitlines()
    assert csv_rows == [
        "time,open,high,low,close,volume",
        "2026-05-01 00:00:00,1.0,2.0,0.5,1.5,10",
        "2026-05-01 00:15:00,1.5,2.5,1.0,2.0,11",
    ]


def test_candidate_diagnostics_suppresses_promotion_and_summarizes_sources():
    rows = [
        {
            "symbol": "XAUUSD",
            "candidate__symbol": "XAUUSD",
            "candidate__framework": "ob_retest",
            "candidate__kill_zone": "ny",
            "candidate__synthetic_realized_r": 1.5,
            "candidate__realized_r": None,
            "external_validation_matched": True,
            "fred__available": True,
            "lbma_calendar__available": True,
        },
        {
            "symbol": "XAUUSD",
            "candidate__symbol": "XAUUSD",
            "candidate__framework": "ob_retest",
            "candidate__kill_zone": "ny",
            "candidate__synthetic_realized_r": -1.0,
            "candidate__realized_r": None,
            "external_validation_matched": True,
            "fred__available": True,
            "lbma_calendar__available": True,
        },
        {
            "symbol": "USDJPY",
            "candidate__symbol": "USDJPY",
            "candidate__framework": "breaker_re_entry",
            "candidate__kill_zone": "tokyo",
            "candidate__synthetic_realized_r": None,
            "candidate__realized_r": None,
            "external_validation_matched": False,
            "fred__available": False,
            "lbma_calendar__available": False,
        },
    ]

    diagnostic = build_candidate_diagnostics(rows, input_path="candidate_join.jsonl")

    assert diagnostic["methodology_gate"]["verdict"] == "SUPPRESSED_DIAGNOSTIC_ONLY"
    assert diagnostic["methodology_gate"]["promotion_allowed"] is False
    assert "actual_candidate_realized_r_absent" in diagnostic["methodology_gate"]["reasons"]
    assert diagnostic["baseline"]["n"] == 2
    assert diagnostic["baseline"]["mean_r"] == pytest.approx(0.25)
    assert diagnostic["coverage"]["source_availability"]["fred__available"] == {
        "all_rows_available": 2,
        "target_rows_available": 2,
    }
    symbol_groups = diagnostic["categorical_strata"]["symbol"]["groups"]
    assert symbol_groups["XAUUSD"]["n"] == 2
    assert symbol_groups["USDJPY"]["target_missing"] == 1


def test_candidate_numeric_diagnostic_reports_median_split_and_rank():
    rows = [
        {"candidate__synthetic_realized_r": -1.0, "fred__VIXCLS__value": 10.0},
        {"candidate__synthetic_realized_r": -0.5, "fred__VIXCLS__value": 12.0},
        {"candidate__synthetic_realized_r": 1.0, "fred__VIXCLS__value": 20.0},
        {"candidate__synthetic_realized_r": 1.5, "fred__VIXCLS__value": 25.0},
    ]

    stats = summarize_numeric_field(
        rows,
        target_field="candidate__synthetic_realized_r",
        numeric_field="fred__VIXCLS__value",
        min_n=2,
    )

    assert stats["eligible"] is True
    assert stats["x_distinct"] == 4
    assert stats["lower_or_equal_median"]["mean_r"] == pytest.approx(-0.75)
    assert stats["upper_median"]["mean_r"] == pytest.approx(1.25)
    assert stats["upper_minus_lower_mean_r"] == pytest.approx(2.0)
    assert stats["spearman_r"] == pytest.approx(1.0)


def test_mt5_history_availability_probe_reports_range_without_writing():
    class FakeMT5:
        TIMEFRAME_M15 = 15

        def __init__(self):
            self.selected = []

        def symbol_select(self, symbol, enable):
            self.selected.append((symbol, enable))
            return True

        def copy_rates_range(self, symbol, timeframe, start, end):
            assert symbol == "XAUUSD"
            assert timeframe == 15
            return [
                {"time": int(datetime(2026, 5, 1, 13, 15, tzinfo=timezone.utc).timestamp())},
                {"time": int(datetime(2026, 5, 1, 13, 30, tzinfo=timezone.utc).timestamp())},
            ]

        def last_error(self):
            return (0, "ok")

    result = inspect_history_availability(
        mt5_module=FakeMT5(),
        specs=[SymbolSpec(file_symbol="XAUUSD", mt5_symbol="XAUUSD")],
        timeframe_names=["M15"],
        start=datetime(2026, 5, 1, 13, 15, tzinfo=timezone.utc),
        end=datetime(2026, 5, 1, 13, 45, tzinfo=timezone.utc),
    )

    stats = result["files"]["XAUUSD_M15"]
    assert stats["rows"] == 2
    assert stats["first"] == "2026-05-01T13:15:00+00:00"
    assert stats["last"] == "2026-05-01T13:30:00+00:00"
    assert stats["has_rows_in_requested_range"] is True
    assert stats["covers_requested_start"] is True
    assert stats["reaches_requested_end"] is True
    assert result["errors"] == []
