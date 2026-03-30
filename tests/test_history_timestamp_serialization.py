from datetime import datetime, timedelta, timezone

from src.api.routes.history import _serialize_utc_datetime


def test_serialize_utc_datetime_treats_naive_values_as_utc():
    value = datetime(2026, 3, 30, 7, 46, 0)

    assert _serialize_utc_datetime(value) == "2026-03-30T07:46:00Z"


def test_serialize_utc_datetime_normalizes_aware_values_to_utc():
    shanghai = timezone(timedelta(hours=8))
    value = datetime(2026, 3, 30, 15, 46, 0, tzinfo=shanghai)

    assert _serialize_utc_datetime(value) == "2026-03-30T07:46:00Z"
