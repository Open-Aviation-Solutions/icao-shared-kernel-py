"""Filesystem implementation of FlightRepository."""

from pathlib import Path

from ... import Flight
from ...domain.pagination import Page
from ...domain.repositories.flight import FlightQuery
from .._codec import flight_from_dict, flight_to_dict
from .._cursor import decode_cursor, encode_cursor
from ._base import _FilesystemRepository


class FilesystemFlightRepository(_FilesystemRepository):
    """Stores each flight as a JSON file under {base_dir}/flights/{id}.json."""

    def __init__(self, base_dir: Path) -> None:
        super().__init__(base_dir / "flights")

    async def save_flight(self, flight: Flight) -> Flight:
        self._write(self._path(flight.id), flight, flight_to_dict)
        return flight

    async def get_flight_by_id(self, flight_id: str) -> Flight | None:
        return self._read(self._path(flight_id), flight_from_dict)

    async def get_flights_by_ids(self, flight_ids: list[str]) -> dict[str, Flight]:
        result: dict[str, Flight] = {}
        for flight_id in flight_ids:
            flight = self._read(self._path(flight_id), flight_from_dict)
            if flight is not None:
                result[flight_id] = flight
        return result

    async def find_flights(self, query: FlightQuery) -> Page[Flight]:
        matches = self._matches(query)
        if query.cursor is not None:
            cursor = decode_cursor(query.cursor)
            last_id = cursor["id"]
            matches = [f for f in matches if f.id > last_id]
        page = matches[: query.limit]
        next_cursor = (
            encode_cursor({"id": page[-1].id}) if len(matches) > query.limit else None
        )
        return Page(items=page, next_cursor=next_cursor)

    async def count_flights(self, query: FlightQuery) -> int:
        return len(self._matches(query))

    async def delete_flight(self, flight_id: str) -> bool:
        return self._delete(self._path(flight_id))

    def _matches(self, query: FlightQuery) -> list[Flight]:
        aircraft_ids: set[str] | None
        if query.aircraft_id is not None:
            aircraft_ids = {query.aircraft_id}
        elif query.aircraft_ids is not None:
            aircraft_ids = set(query.aircraft_ids)
        else:
            aircraft_ids = None

        items: list[Flight] = []
        for path in self._dir.glob("*.json"):
            flight = self._read(path, flight_from_dict)
            if flight is None:
                continue
            if aircraft_ids is not None and flight.aircraft_id not in aircraft_ids:
                continue
            items.append(flight)
        items.sort(key=lambda f: f.id)
        return items
