"""Smoke tests for the filesystem adapters' keyset pagination — adapted from
icao-shared-kernel's tests/infrastructure/filesystem/test_pagination.py,
updated for the PyO3 boundary (str ids, no Pydantic) and the new Flight
shape (departure/arrival: SignificantPoint, no flight_date/waypoints;
FlightQuery is id-only per task 0002 D4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from icao_shared_kernel import (
    Aircraft,
    AircraftRegistration,
    AircraftType,
    Flight,
    Licence,
    Pilot,
    SignificantPoint,
)
from icao_shared_kernel.domain.repositories.aircraft import AircraftQuery
from icao_shared_kernel.domain.repositories.flight import FlightQuery
from icao_shared_kernel.domain.repositories.pilot import PilotQuery
from icao_shared_kernel.infrastructure.filesystem.aircraft import (
    FilesystemAircraftRepository,
)
from icao_shared_kernel.infrastructure.filesystem.flight import (
    FilesystemFlightRepository,
)
from icao_shared_kernel.infrastructure.filesystem.pilot import (
    FilesystemPilotRepository,
)

pytestmark = pytest.mark.asyncio


def _aircraft(suffix: str) -> Aircraft:
    return Aircraft(AircraftType("C172"), AircraftRegistration("VH", suffix))


def _pilot(number: str) -> Pilot:
    return Pilot("Pilot " + number, licences=[Licence("AU", "CASA", number)])


def _flight(aircraft_id: str) -> Flight:
    return Flight(
        aircraft_id,
        SignificantPoint.designator("YSBK"),
        SignificantPoint.designator("YSCN"),
    )


async def test_aircraft_keyset_pagination(tmp_path: Path) -> None:
    repo = FilesystemAircraftRepository(tmp_path)
    saved = [_aircraft(s) for s in ("AAA", "BBB", "CCC", "DDD")]
    for a in saved:
        await repo.save_aircraft(a)
    expected = sorted(saved, key=lambda a: a.id)

    first = await repo.find_aircraft(AircraftQuery(limit=2))
    assert [a.id for a in first.items] == [a.id for a in expected[:2]]
    second = await repo.find_aircraft(AircraftQuery(limit=2, cursor=first.next_cursor))
    assert [a.id for a in second.items] == [a.id for a in expected[2:]]
    assert second.next_cursor is None
    assert await repo.count_aircraft(AircraftQuery()) == 4


async def test_aircraft_filter_by_type(tmp_path: Path) -> None:
    repo = FilesystemAircraftRepository(tmp_path)
    cessna = _aircraft("AAA")
    chopper = Aircraft(AircraftType("R44"), AircraftRegistration("VH", "BBB"))
    await repo.save_aircraft(cessna)
    await repo.save_aircraft(chopper)

    page = await repo.find_aircraft(AircraftQuery(type="R44"))
    assert [a.id for a in page.items] == [chopper.id]


async def test_aircraft_filter_by_registration(tmp_path: Path) -> None:
    repo = FilesystemAircraftRepository(tmp_path)
    cessna = _aircraft("AAA")
    other = _aircraft("BBB")
    await repo.save_aircraft(cessna)
    await repo.save_aircraft(other)

    page = await repo.find_aircraft(
        AircraftQuery(registration=AircraftRegistration("VH", "AAA"))
    )
    assert [a.id for a in page.items] == [cessna.id]


async def test_pilot_keyset_pagination_and_licence_lookup(tmp_path: Path) -> None:
    repo = FilesystemPilotRepository(tmp_path)
    saved = [_pilot(f"PPL-{i}") for i in range(3)]
    for p in saved:
        await repo.save_pilot(p)
    expected = sorted(saved, key=lambda p: p.id)

    first = await repo.find_pilots(PilotQuery(limit=2))
    assert [p.id for p in first.items] == [p.id for p in expected[:2]]
    second = await repo.find_pilots(PilotQuery(limit=2, cursor=first.next_cursor))
    assert [p.id for p in second.items] == [p.id for p in expected[2:]]
    assert second.next_cursor is None
    assert await repo.count_pilots(PilotQuery()) == 3

    found = await repo.get_pilot_by_licence(Licence("AU", "CASA", "PPL-1"))
    assert found is not None and found.licences[0].number == "PPL-1"
    assert (
        await repo.get_pilot_by_licence(Licence("AU", "CASA", "PPL-missing")) is None
    )


async def test_flight_keyset_pagination(tmp_path: Path) -> None:
    repo = FilesystemFlightRepository(tmp_path)
    aircraft_id = _aircraft("AAA").id
    saved = [_flight(aircraft_id) for _ in range(3)]
    for f in saved:
        await repo.save_flight(f)
    expected = sorted(saved, key=lambda f: f.id)

    first = await repo.find_flights(FlightQuery(limit=2))
    assert [f.id for f in first.items] == [f.id for f in expected[:2]]
    second = await repo.find_flights(FlightQuery(limit=2, cursor=first.next_cursor))
    assert [f.id for f in second.items] == [f.id for f in expected[2:]]
    assert second.next_cursor is None


async def test_flight_filter_by_aircraft_id(tmp_path: Path) -> None:
    repo = FilesystemFlightRepository(tmp_path)
    aircraft_a = _aircraft("AAA").id
    aircraft_b = _aircraft("BBB").id
    f1 = _flight(aircraft_a)
    f2 = _flight(aircraft_b)
    await repo.save_flight(f1)
    await repo.save_flight(f2)

    page = await repo.find_flights(FlightQuery(aircraft_id=aircraft_a))
    assert [f.id for f in page.items] == [f1.id]

    page = await repo.find_flights(FlightQuery(aircraft_ids=[aircraft_a, aircraft_b]))
    assert {f.id for f in page.items} == {f1.id, f2.id}


async def test_flight_aircraft_filters_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        FlightQuery(aircraft_id="a", aircraft_ids=["b"])


async def test_flight_get_by_id_and_delete(tmp_path: Path) -> None:
    repo = FilesystemFlightRepository(tmp_path)
    flight = _flight(_aircraft("AAA").id)
    await repo.save_flight(flight)

    got = await repo.get_flight_by_id(flight.id)
    assert got is not None and got.id == flight.id

    by_ids = await repo.get_flights_by_ids([flight.id, "missing"])
    assert set(by_ids) == {flight.id}

    assert await repo.delete_flight(flight.id) is True
    assert await repo.get_flight_by_id(flight.id) is None
    assert await repo.delete_flight(flight.id) is False
