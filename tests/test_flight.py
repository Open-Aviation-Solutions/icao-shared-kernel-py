"""Flight aggregate construction, rendering, and derived duration — adapted
from icao-shared-kernel-rs tests/flight.rs."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

import icao_shared_kernel as k


def test_defaults_id_and_no_movement_times() -> None:
    flight = k.Flight.create(str(uuid4()), "YSBK", "YSCN")
    assert flight.first_movement is None
    assert flight.last_movement is None
    assert flight.id != "00000000-0000-0000-0000-000000000000"


def test_route_summary() -> None:
    flight = k.Flight.create(str(uuid4()), "YSBK", "YSCN")
    assert flight.route_summary() == "YSBK-YSCN"


def test_duration_is_none_without_both_movements() -> None:
    flight = k.Flight.create(str(uuid4()), "YSBK", "YSCN")
    assert flight.duration() is None


def test_duration_derived_from_movements() -> None:
    flight = k.Flight(
        str(uuid4()),
        k.SignificantPoint.designator("YSBK"),
        k.SignificantPoint.designator("YSCN"),
        datetime(2026, 4, 19, 3, 0, tzinfo=timezone.utc),
        datetime(2026, 4, 19, 4, 30, tzinfo=timezone.utc),
    )
    duration = flight.duration()
    assert duration is not None
    assert duration.total_minutes == 90


def test_display_without_movement_time_omits_date() -> None:
    flight = k.Flight.create(str(uuid4()), "YSBK", "YSCN")
    assert str(flight) == "Flight: YSBK-YSCN"


def test_display_with_movement_time_shows_date() -> None:
    flight = k.Flight(
        str(uuid4()),
        k.SignificantPoint.designator("YSBK"),
        k.SignificantPoint.designator("YSCN"),
        datetime(2026, 4, 19, 3, 0, tzinfo=timezone.utc),
        None,
    )
    assert str(flight) == "Flight 2026-04-19: YSBK-YSCN"


@pytest.mark.parametrize(
    "departure, arrival",
    [
        ("ybth", "YSCN"),  # invalid departure designator
        ("YSBK", "YS-BK"),  # invalid arrival designator
    ],
)
def test_invalid_designators_rejected(departure: str, arrival: str) -> None:
    with pytest.raises(k.ValidationError):
        k.Flight.create(str(uuid4()), departure, arrival)


def test_coordinate_endpoint_supported() -> None:
    coordinate = k.Coordinate("-33.9461", "151.1772")
    flight = k.Flight(
        str(uuid4()),
        k.SignificantPoint.Coordinate(coordinate),
        k.SignificantPoint.designator("YSCN"),
    )
    assert flight.route_summary() == "-33.9461,151.1772-YSCN"


def test_movement_times_round_trip_as_aware_utc_datetimes() -> None:
    first = datetime(2026, 4, 19, 3, 0, tzinfo=timezone.utc)
    flight = k.Flight(
        str(uuid4()),
        k.SignificantPoint.designator("YSBK"),
        k.SignificantPoint.designator("YSCN"),
        first,
        None,
    )
    assert flight.first_movement == first
    assert flight.first_movement.tzinfo is timezone.utc


def test_naive_datetime_rejected() -> None:
    with pytest.raises((TypeError, ValueError)):
        k.Flight(
            str(uuid4()),
            k.SignificantPoint.designator("YSBK"),
            k.SignificantPoint.designator("YSCN"),
            datetime(2026, 4, 19, 3, 0),  # no tzinfo
            None,
        )
