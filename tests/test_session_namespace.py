from __future__ import annotations

import pytest

from src.components.session_namespace import (
    canonical_utc_hour_bucket_token,
    utc_hour_bucket_aliases,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("h00_01", "h00_01"),
        ("h18_19", "h18_19"),
        ("moonshot_h23_00", "h23_00"),
        ("H08-09", "h08_09"),
    ),
)
def test_canonical_utc_hour_bucket_token(value: str, expected: str) -> None:
    assert canonical_utc_hour_bucket_token(value) == expected
    assert utc_hour_bucket_aliases(value) == {expected, f"moonshot_{expected}"}


@pytest.mark.parametrize(
    "value",
    ("h18_20", "h24_01", "h1_02", "h01_2", "hello_", "off_configured_session"),
)
def test_invalid_utc_hour_bucket_token_is_rejected(value: str) -> None:
    assert canonical_utc_hour_bucket_token(value) is None
    assert utc_hour_bucket_aliases(value) == set()
