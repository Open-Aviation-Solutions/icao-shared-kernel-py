"""Create/edit round-trip tests for the admin views, using starlette's
TestClient. No baseline to adapt from — icao-shared-kernel has no
tests/infrastructure/admin/ at all (see task 0002-infrastructure-extras.md
D5) — so this is new coverage, not a port."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin

from icao_shared_kernel.infrastructure.admin.aircraft import AircraftAdminView
from icao_shared_kernel.infrastructure.admin.flight import FlightAdminView
from icao_shared_kernel.infrastructure.admin.pilot import PilotAdminView
from icao_shared_kernel.infrastructure.filesystem.aircraft import (
    FilesystemAircraftRepository,
)
from icao_shared_kernel.infrastructure.filesystem.flight import (
    FilesystemFlightRepository,
)
from icao_shared_kernel.infrastructure.filesystem.pilot import (
    FilesystemPilotRepository,
)


def _make_client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    admin = BaseAdmin(title="test")
    admin.add_view(AircraftAdminView(FilesystemAircraftRepository(tmp_path)))
    admin.add_view(PilotAdminView(FilesystemPilotRepository(tmp_path)))
    admin.add_view(FlightAdminView(FilesystemFlightRepository(tmp_path)))
    admin.mount_to(app)
    return TestClient(app)


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return _make_client(tmp_path)


def test_aircraft_create_list_edit_delete(client: TestClient) -> None:
    r = client.post(
        "/admin/aircraft/create",
        data={
            "aircraft_type.designator": "C172",
            "registration.nationality": "VH",
            "registration.registration": "ABC",
        },
    )
    assert r.status_code == 200

    items = client.get("/admin/api/aircraft").json()["items"]
    assert len(items) == 1
    assert items[0]["aircraft_type"] == {"designator": "C172"}
    assert items[0]["registration"] == {"nationality": "VH", "registration": "ABC"}
    aircraft_id = items[0]["id"]

    r = client.post(
        f"/admin/aircraft/edit/{aircraft_id}",
        data={
            "aircraft_type.designator": "B738",
            "registration.nationality": "VH",
            "registration.registration": "ABC",
        },
    )
    assert r.status_code == 200
    edited = client.get("/admin/api/aircraft").json()["items"][0]
    assert edited["id"] == aircraft_id
    assert edited["aircraft_type"] == {"designator": "B738"}


def test_aircraft_create_rejects_invalid_type(client: TestClient) -> None:
    r = client.post(
        "/admin/aircraft/create",
        data={
            "aircraft_type.designator": "",
            "registration.nationality": "VH",
            "registration.registration": "ABC",
        },
    )
    assert r.status_code == 422
    assert client.get("/admin/api/aircraft").json()["total"] == 0


def test_pilot_create_with_licence(client: TestClient) -> None:
    r = client.post(
        "/admin/pilot/create",
        data={
            "display_name": "Jane Doe",
            "licences.0.issuing_state": "AU",
            "licences.0.issuing_authority": "CASA",
            "licences.0.number": "12345",
        },
    )
    assert r.status_code == 200

    items = client.get("/admin/api/pilot").json()["items"]
    assert items[0]["display_name"] == "Jane Doe"
    assert items[0]["licences"] == [
        {"issuing_state": "AU", "issuing_authority": "CASA", "number": "12345"}
    ]


def test_pilot_create_rejects_invalid_licence(client: TestClient) -> None:
    r = client.post(
        "/admin/pilot/create",
        data={
            "display_name": "Jane Doe",
            "licences.0.issuing_state": "AUS",  # not a 2-letter code
            "licences.0.issuing_authority": "CASA",
            "licences.0.number": "12345",
        },
    )
    assert r.status_code == 422
    assert client.get("/admin/api/pilot").json()["total"] == 0


def test_flight_create_list_edit(client: TestClient) -> None:
    client.post(
        "/admin/aircraft/create",
        data={
            "aircraft_type.designator": "C172",
            "registration.nationality": "VH",
            "registration.registration": "ABC",
        },
    )
    aircraft_id = client.get("/admin/api/aircraft").json()["items"][0]["id"]

    r = client.post(
        "/admin/flight/create",
        data={"aircraft_id": aircraft_id, "departure": "YSBK", "arrival": "YSCN"},
    )
    assert r.status_code == 200

    items = client.get("/admin/api/flight").json()["items"]
    assert items[0]["departure"] == "YSBK"
    assert items[0]["arrival"] == "YSCN"
    flight_id = items[0]["id"]

    r = client.post(
        f"/admin/flight/edit/{flight_id}",
        data={"aircraft_id": aircraft_id, "departure": "YMMB", "arrival": "YSCN"},
    )
    assert r.status_code == 200
    edited = client.get("/admin/api/flight").json()["items"][0]
    assert edited["departure"] == "YMMB"


def test_flight_create_rejects_invalid_designator(client: TestClient) -> None:
    client.post(
        "/admin/aircraft/create",
        data={
            "aircraft_type.designator": "C172",
            "registration.nationality": "VH",
            "registration.registration": "ABC",
        },
    )
    aircraft_id = client.get("/admin/api/aircraft").json()["items"][0]["id"]

    r = client.post(
        "/admin/flight/create",
        data={"aircraft_id": aircraft_id, "departure": "bad-code", "arrival": "YSCN"},
    )
    assert r.status_code == 422
    assert client.get("/admin/api/flight").json()["total"] == 0
