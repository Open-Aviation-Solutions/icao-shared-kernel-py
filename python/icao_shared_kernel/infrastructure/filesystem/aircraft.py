"""Filesystem implementation of AircraftRepository."""

from pathlib import Path

from ... import Aircraft
from ...domain.pagination import Page
from ...domain.repositories.aircraft import AircraftQuery
from .._codec import aircraft_from_dict, aircraft_to_dict
from .._cursor import decode_cursor, encode_cursor
from ._base import _FilesystemRepository


class FilesystemAircraftRepository(_FilesystemRepository):
    """Stores each aircraft as a JSON file under {base_dir}/aircraft/{id}.json."""

    def __init__(self, base_dir: Path) -> None:
        super().__init__(base_dir / "aircraft")

    async def save_aircraft(self, aircraft: Aircraft) -> Aircraft:
        self._write(self._path(aircraft.id), aircraft, aircraft_to_dict)
        return aircraft

    async def get_aircraft_by_id(self, aircraft_id: str) -> Aircraft | None:
        return self._read(self._path(aircraft_id), aircraft_from_dict)

    async def find_aircraft(self, query: AircraftQuery) -> Page[Aircraft]:
        matches = self._matches(query)
        if query.cursor is not None:
            cursor = decode_cursor(query.cursor)
            last_id = cursor["id"]
            matches = [a for a in matches if a.id > last_id]
        page = matches[: query.limit]
        next_cursor = (
            encode_cursor({"id": page[-1].id}) if len(matches) > query.limit else None
        )
        return Page(items=page, next_cursor=next_cursor)

    async def count_aircraft(self, query: AircraftQuery) -> int:
        return len(self._matches(query))

    async def delete_aircraft(self, aircraft_id: str) -> bool:
        return self._delete(self._path(aircraft_id))

    def _matches(self, query: AircraftQuery) -> list[Aircraft]:
        items: list[Aircraft] = []
        for path in self._dir.glob("*.json"):
            aircraft = self._read(path, aircraft_from_dict)
            if aircraft is None:
                continue
            if (
                query.type is not None
                and aircraft.aircraft_type.designator != query.type
            ):
                continue
            if query.registration is not None and aircraft.registration != query.registration:
                continue
            items.append(aircraft)
        items.sort(key=lambda a: a.id)
        return items
