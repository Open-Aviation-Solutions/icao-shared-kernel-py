"""Factory for the FastAPI application with starlette-admin mounted at /admin."""

from fastapi import FastAPI
from starlette_admin import BaseAdmin

from icao_shared_kernel.infrastructure.admin.aircraft import AircraftAdminView
from icao_shared_kernel.infrastructure.admin.flight import FlightAdminView
from icao_shared_kernel.infrastructure.admin.pilot import PilotAdminView
from icao_shared_kernel.infrastructure.filesystem.container import (
    make_aircraft_repo,
    make_flight_repo,
    make_pilot_repo,
)


def make_admin_app() -> FastAPI:
    """Create a FastAPI app with the admin interface mounted at /admin."""
    app = FastAPI(title="ICAO Shared Kernel Admin")

    admin = BaseAdmin(title="ICAO Shared Kernel")

    admin.add_view(AircraftAdminView(make_aircraft_repo()))
    admin.add_view(PilotAdminView(make_pilot_repo()))
    admin.add_view(FlightAdminView(make_flight_repo()))

    admin.mount_to(app)

    return app
