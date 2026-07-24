"""Filesystem-backed repository factory functions for icao-shared-kernel entities.

Configuration:
    ICAO_SHARED_KERNEL_DATA  Path to the data directory (default: "data")
"""

import os
from pathlib import Path

from .aircraft import FilesystemAircraftRepository
from .flight import FilesystemFlightRepository
from .pilot import FilesystemPilotRepository

_DATA = Path(os.getenv("ICAO_SHARED_KERNEL_DATA", "data"))


def make_pilot_repo() -> FilesystemPilotRepository:
    return FilesystemPilotRepository(_DATA)


def make_aircraft_repo() -> FilesystemAircraftRepository:
    return FilesystemAircraftRepository(_DATA)


def make_flight_repo() -> FilesystemFlightRepository:
    return FilesystemFlightRepository(_DATA)
