"""Repository protocol interface for pilot operations."""

from dataclasses import dataclass
from typing import Protocol

from ... import Licence, Pilot
from ..pagination import Page, _PageRequest


@dataclass
class PilotQuery(_PageRequest):
    """Pagination for :meth:`PilotRepository.find_pilots`.

    No domain filter fields exist in v1 — interesting Pilot lookups are
    single-key (:meth:`PilotRepository.get_pilot_by_id`,
    :meth:`PilotRepository.get_pilot_by_licence`). The model is
    kept for consistency with the other repositories and to leave room
    for filters later without a signature change.

    Sort order: ``(id ASC)``.
    """


class PilotRepository(Protocol):
    """Protocol interface for pilot persistence and retrieval operations."""

    async def save_pilot(self, pilot: Pilot) -> Pilot:
        """Upsert a pilot record.

        If a pilot with the same id already exists it is replaced;
        otherwise a new record is created.

        Args:
            pilot: The pilot to save.

        Returns:
            The saved pilot.
        """
        ...

    async def get_pilot_by_id(self, pilot_id: str) -> Pilot | None:
        """Retrieve a pilot by their ID.

        Args:
            pilot_id: Unique identifier for the pilot.

        Returns:
            The pilot if found, None otherwise.
        """
        ...

    async def get_pilot_by_licence(self, licence: Licence) -> Pilot | None:
        """Retrieve a pilot by one of their licences (natural key).

        Matches a :class:`Licence` within the pilot's ``licences`` by its full
        identity. The ``(issuing_authority, number)`` pair is unique, so this
        returns at most one record.

        Args:
            licence: The licence to look up, matched by its full identity.

        Returns:
            The pilot if found, None otherwise.
        """
        ...

    async def find_pilots(self, query: PilotQuery) -> Page[Pilot]:
        """Page pilot records.

        Sort order is fixed at ``(id ASC)``. Iteration is keyset-based:
        pass the returned ``Page.next_cursor`` back as ``query.cursor``
        to fetch the following page. ``next_cursor`` is opaque and must
        not be parsed by consumers.

        Args:
            query: Pagination request (``limit`` and ``cursor``).

        Returns:
            A page of up to ``query.limit`` pilots.
        """
        ...

    async def count_pilots(self, query: PilotQuery) -> int:
        """Count pilot records.

        ``query.limit`` and ``query.cursor`` are ignored — the count is
        over the entire collection (no filter fields exist in v1).
        """
        ...

    async def delete_pilot(self, pilot_id: str) -> bool:
        """Delete a pilot record.

        Args:
            pilot_id: Unique identifier for the pilot to delete.

        Returns:
            True if the pilot was deleted, False if not found.
        """
        ...
