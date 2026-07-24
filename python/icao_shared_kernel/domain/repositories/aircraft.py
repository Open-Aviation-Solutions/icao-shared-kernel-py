"""Repository protocol interface for aircraft operations."""

from dataclasses import dataclass
from typing import Protocol

from ... import Aircraft, AircraftRegistration
from ..pagination import Page, _PageRequest


@dataclass
class AircraftQuery(_PageRequest):
    """Filter + pagination for :meth:`AircraftRepository.find_aircraft`.

    All filter fields are exact matches and are AND-combined. Unset fields
    do not contribute to the filter. ``type`` matches the ICAO Doc 8643
    designator; ``registration`` matches both the nationality prefix and the
    registration marks together.

    Sort order: ``(id ASC)``.
    """

    type: str | None = None
    registration: AircraftRegistration | None = None


class AircraftRepository(Protocol):
    """Protocol interface for aircraft persistence and retrieval operations."""

    async def save_aircraft(self, aircraft: Aircraft) -> Aircraft:
        """Upsert an aircraft record.

        If an aircraft with the same id already exists it is replaced;
        otherwise a new record is created.

        Args:
            aircraft: The aircraft to save.

        Returns:
            The saved aircraft.
        """
        ...

    async def get_aircraft_by_id(self, aircraft_id: str) -> Aircraft | None:
        """Retrieve an aircraft by its ID.

        Args:
            aircraft_id: Unique identifier for the aircraft.

        Returns:
            The aircraft if found, None otherwise.
        """
        ...

    async def find_aircraft(self, query: AircraftQuery) -> Page[Aircraft]:
        """Page aircraft records matching the typed filters in ``query``.

        Sort order is fixed at ``(id ASC)``. Iteration is keyset-based:
        pass the returned ``Page.next_cursor`` back as ``query.cursor`` to
        fetch the following page. ``next_cursor`` is opaque and must not
        be parsed by consumers.

        Args:
            query: Filter fields plus ``limit`` and ``cursor``.

        Returns:
            A page of up to ``query.limit`` matching aircraft.
        """
        ...

    async def count_aircraft(self, query: AircraftQuery) -> int:
        """Count aircraft records matching the typed filters in ``query``.

        ``query.limit`` and ``query.cursor`` are ignored — the count is
        over the entire filtered set.
        """
        ...

    async def delete_aircraft(self, aircraft_id: str) -> bool:
        """Delete an aircraft record.

        Args:
            aircraft_id: Unique identifier for the aircraft to delete.

        Returns:
            True if the aircraft was deleted, False if not found.
        """
        ...
