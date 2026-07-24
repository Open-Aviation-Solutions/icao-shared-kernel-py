"""Repository protocol interface for flight operations."""

from dataclasses import dataclass
from typing import Protocol

from ... import Flight
from ..pagination import Page, _PageRequest


@dataclass
class FlightQuery(_PageRequest):
    """Filter + pagination for :meth:`FlightRepository.find_flights`.

    All filter fields are AND-combined; unset fields contribute no
    constraint. ``aircraft_id`` (single) and ``aircraft_ids`` (bulk) are
    mutually exclusive — set at most one. Pilot-scoped lookups are
    intentionally absent: ``Flight`` has no ``pilot_id`` field — that link
    lives in ``pilot-logbook``'s ``LogbookFlight``.

    No date/waypoint filters (per task 0002 D4, YAGNI): ``Flight``'s route
    is now ``departure``/``arrival: SignificantPoint`` and its timing is
    ``first_movement``/``last_movement: datetime | None`` — neither has a
    settled query design yet, and no consumer has asked for Flight-scoped
    date filtering. Revisit when one does.

    Sort order: ``(id ASC)``.
    """

    aircraft_id: str | None = None
    aircraft_ids: list[str] | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.aircraft_id is not None and self.aircraft_ids is not None:
            raise ValueError(
                "FlightQuery.aircraft_id and aircraft_ids are mutually exclusive"
            )


class FlightRepository(Protocol):
    """Protocol interface for flight persistence and retrieval operations.

    Follows clean architecture principles by defining domain-focused operations
    without specifying implementation details.
    """

    async def save_flight(self, flight: Flight) -> Flight:
        """Upsert a flight record.

        If a flight with the same id already exists it is replaced;
        otherwise a new record is created.

        Args:
            flight: The flight to save.

        Returns:
            The saved flight.
        """
        ...

    async def get_flight_by_id(self, flight_id: str) -> Flight | None:
        """Retrieve a flight by its ID.

        Args:
            flight_id: Unique identifier for the flight

        Returns:
            The flight if found, None otherwise
        """
        ...

    async def get_flights_by_ids(self, flight_ids: list[str]) -> dict[str, Flight]:
        """Bulk load flights by their IDs.

        IDs that do not correspond to existing flights are omitted from the
        returned dict; no error is raised for missing IDs.

        Args:
            flight_ids: List of flight IDs to retrieve.

        Returns:
            Dictionary mapping flight_id to Flight for each found flight.
        """
        ...

    async def find_flights(self, query: FlightQuery) -> Page[Flight]:
        """Page flight records matching the typed filters in ``query``.

        Sort order is fixed at ``(id ASC)``. Iteration is keyset-based:
        pass the returned ``Page.next_cursor`` back as ``query.cursor`` to
        fetch the following page. ``next_cursor`` is opaque and must not
        be parsed by consumers.

        Args:
            query: Filter fields plus ``limit`` and ``cursor``.

        Returns:
            A page of up to ``query.limit`` matching flights.
        """
        ...

    async def count_flights(self, query: FlightQuery) -> int:
        """Count flight records matching the typed filters in ``query``.

        ``query.limit`` and ``query.cursor`` are ignored — the count is
        over the entire filtered set.
        """
        ...

    async def delete_flight(self, flight_id: str) -> bool:
        """Delete a flight record.

        Args:
            flight_id: Unique identifier for the flight to delete

        Returns:
            True if flight was deleted, False if not found
        """
        ...
