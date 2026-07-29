"""FSTD device and session bindings — the Python side of the boundary
mapping (str ids, datetime.date validity, optional qualification)."""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

import icao_shared_kernel as k


def _qualification(
    valid_from: date = date(2026, 1, 1), valid_until: date = date(2026, 12, 31)
) -> k.DeviceQualification:
    return k.DeviceQualification("AU", "CASA", "Level D", valid_from, valid_until)


def test_unqualified_device_is_valid() -> None:
    device = k.FlightSimulationTrainingDevice.create(
        k.FstdKind.BasicInstrumentFlightTrainer, "Home sim"
    )
    assert device.qualification is None
    assert device.designation.designation == "Home sim"
    assert str(device) == "Home sim"


def test_empty_designation_rejected() -> None:
    with pytest.raises(k.EmptyFieldError):
        k.DeviceDesignation("")


def test_device_round_trips_kind_and_qualification() -> None:
    device = k.FlightSimulationTrainingDevice(
        k.FstdKind.FlightSimulator,
        k.DeviceDesignation("CAE 7000XR B738 s/n 1234"),
        _qualification(),
    )
    assert device.kind == k.FstdKind.FlightSimulator
    assert device.qualification is not None
    assert device.qualification.issuing_authority == "CASA"
    assert device.qualification.level == "Level D"


def test_explicit_id_preserved() -> None:
    device_id = str(uuid4())
    device = k.FlightSimulationTrainingDevice(
        k.FstdKind.FlightProceduresTrainer,
        k.DeviceDesignation("FNPT II"),
        None,
        device_id,
    )
    assert device.id == device_id


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2025, 12, 31), False),
        (date(2026, 1, 1), True),
        (date(2026, 6, 15), True),
        (date(2026, 12, 31), True),
        (date(2027, 1, 1), False),
    ],
)
def test_is_in_force_on_is_inclusive(day: date, expected: bool) -> None:
    assert _qualification().is_in_force_on(day) is expected


def test_validity_period_ending_before_start_rejected() -> None:
    with pytest.raises(k.ValidityPeriodError):
        k.DeviceQualification(
            "AU", "CASA", "Level D", date(2026, 3, 1), date(2026, 2, 28)
        )


def test_qualification_rejects_malformed_issuing_state() -> None:
    with pytest.raises(k.IssuingStateError):
        k.DeviceQualification(
            "AUS", "CASA", "Level D", date(2026, 1, 1), date(2026, 12, 31)
        )


def test_session_defaults_are_all_empty() -> None:
    session = k.FstdSession(str(uuid4()))
    assert session.simulated_aircraft_type is None
    assert session.departure is None
    assert session.route_summary() is None
    assert session.duration() is None
    assert str(session) == "FSTD session"


def test_one_device_simulates_different_types_across_sessions() -> None:
    device_id = str(uuid4())
    cessna = k.FstdSession.create(device_id, "C172")
    boeing = k.FstdSession.create(device_id, "B738")

    assert cessna.device_id == boeing.device_id
    assert cessna.simulated_aircraft_type is not None
    assert cessna.simulated_aircraft_type.designator == "C172"
    assert boeing.simulated_aircraft_type is not None
    assert boeing.simulated_aircraft_type.designator == "B738"


def test_session_create_rejects_invalid_designator() -> None:
    with pytest.raises(k.InvalidAircraftTypeError):
        k.FstdSession.create(str(uuid4()), "c172")


def test_session_duration_and_route() -> None:
    session = k.FstdSession(
        str(uuid4()),
        k.AircraftType("B738"),
        k.SignificantPoint.Designator(k.Waypoint("YSSY")),
        k.SignificantPoint.Designator(k.Waypoint("YMML")),
        datetime(2026, 5, 1, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 5, 1, 2, 30, tzinfo=timezone.utc),
    )
    assert session.route_summary() == "YSSY-YMML"
    duration = session.duration()
    assert duration is not None
    assert duration.total_minutes == 90
