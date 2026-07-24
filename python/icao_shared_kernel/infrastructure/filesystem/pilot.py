"""Filesystem implementation of PilotRepository."""

from pathlib import Path

from ... import Licence, Pilot
from ...domain.pagination import Page
from ...domain.repositories.pilot import PilotQuery
from .._codec import pilot_from_dict, pilot_to_dict
from .._cursor import decode_cursor, encode_cursor
from ._base import _FilesystemRepository


class FilesystemPilotRepository(_FilesystemRepository):
    """Stores each pilot as a JSON file under {base_dir}/pilots/{id}.json."""

    def __init__(self, base_dir: Path) -> None:
        super().__init__(base_dir / "pilots")

    async def save_pilot(self, pilot: Pilot) -> Pilot:
        self._write(self._path(pilot.id), pilot, pilot_to_dict)
        return pilot

    async def get_pilot_by_id(self, pilot_id: str) -> Pilot | None:
        return self._read(self._path(pilot_id), pilot_from_dict)

    async def get_pilot_by_licence(self, licence: Licence) -> Pilot | None:
        for pilot in self._all():
            if licence in pilot.licences:
                return pilot
        return None

    async def find_pilots(self, query: PilotQuery) -> Page[Pilot]:
        items = self._all()
        if query.cursor is not None:
            cursor = decode_cursor(query.cursor)
            last_id = cursor["id"]
            items = [p for p in items if p.id > last_id]
        page = items[: query.limit]
        next_cursor = (
            encode_cursor({"id": page[-1].id}) if len(items) > query.limit else None
        )
        return Page(items=page, next_cursor=next_cursor)

    async def count_pilots(self, query: PilotQuery) -> int:
        return len(self._all())

    async def delete_pilot(self, pilot_id: str) -> bool:
        return self._delete(self._path(pilot_id))

    def _all(self) -> list[Pilot]:
        pilots: list[Pilot] = []
        for path in self._dir.glob("*.json"):
            pilot = self._read(path, pilot_from_dict)
            if pilot is not None:
                pilots.append(pilot)
        pilots.sort(key=lambda p: p.id)
        return pilots
