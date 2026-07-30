"""Aircraft type, registration, and aggregate behaviour — adapted from
icao-shared-kernel-rs tests/aircraft.rs."""

from uuid import UUID, uuid4

import pytest

import icao_shared_kernel as k


def test_registration_renders_and_exposes_marks() -> None:
    reg = k.AircraftRegistration("VH", "ABC")
    assert reg.nationality == "VH"
    assert reg.registration == "ABC"
    assert str(reg) == "VH-ABC"


def test_aircraft_creation_and_display() -> None:
    aircraft = k.Aircraft.create("C172", "VH", "XYZ")
    assert aircraft.aircraft_type.designator == "C172"
    assert str(aircraft) == "C172 VH-XYZ"


@pytest.mark.parametrize(
    "value",
    ["C172", "B738", "R44", "ZZZZ"],  # ZZZZ: sentinel for unassigned designator
)
def test_valid_designators_accepted(value: str) -> None:
    aircraft_type = k.AircraftType(value)
    assert aircraft_type.designator == value


@pytest.mark.parametrize(
    "value",
    [
        "",  # empty
        "C",  # single char
        "C1729",  # too long
        "172",  # no leading letter
        "c172",  # lowercase
        "C-72",  # non-alphanumeric
    ],
)
def test_invalid_designators_rejected(value: str) -> None:
    with pytest.raises(k.InvalidAircraftTypeError):
        k.AircraftType(value)


def test_new_from_parts() -> None:
    aircraft_type = k.AircraftType("C172")
    registration = k.AircraftRegistration("VH", "ABC")
    aircraft = k.Aircraft(aircraft_type, registration)
    assert aircraft.aircraft_type.designator == "C172"
    assert aircraft.registration.registration == "ABC"


def test_id_is_a_native_uuid_and_round_trips() -> None:
    # Ids cross the boundary as uuid.UUID, not as strings — consumers hold
    # UUID in their own aggregates and must not have to convert.
    given = uuid4()
    aircraft = k.Aircraft(
        k.AircraftType("C172"), k.AircraftRegistration("VH", "ABC"), given
    )
    assert isinstance(aircraft.id, UUID)
    assert aircraft.id == given


def test_id_rejects_a_uuid_shaped_string() -> None:
    # Guards the contract: were the getter to fall back to str, this would
    # silently start passing again.
    with pytest.raises(TypeError):
        k.Aircraft(
            k.AircraftType("C172"),
            k.AircraftRegistration("VH", "ABC"),
            str(uuid4()),  # type: ignore[arg-type]
        )
