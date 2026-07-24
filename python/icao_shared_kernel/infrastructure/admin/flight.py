"""Admin view for Flight."""

from collections.abc import Sequence
from typing import Any

from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import DateTimeField, HasOne, StringField

from ... import Flight, SignificantPoint, ValidationError
from ...domain.repositories.flight import FlightQuery, FlightRepository
from .._codec import significant_point_to_dict
from ._base import PilotAdminBase, build_or_collect


def _significant_point_display(point: SignificantPoint) -> str:
    """Human-readable form for list/detail display — 'YSBK', or 'lat,lon'
    for a coordinate endpoint (see the class docstring: coordinates display
    fine, they're just not editable through this form)."""
    data = significant_point_to_dict(point)
    if data["kind"] == "designator":
        return data["value"]
    return f"{data['latitude']},{data['longitude']}"


class FlightAdminView(PilotAdminBase):
    """Admin CRUD view for Flight, delegating to FlightRepository.

    ``departure``/``arrival`` are edited as coded designator strings only —
    ``SignificantPoint``'s coordinate variant has no form representation
    here (no current consumer needs to create coordinate-based routes
    through the admin UI); flights already stored with a coordinate
    endpoint still display and save correctly, they just can't be *edited*
    into a different coordinate via this form.
    """

    identity = "flight"
    name = "Flight"
    label = "Flights"
    icon = "fa fa-route"
    pk_attr = "id"

    fields = [
        StringField("id", read_only=True, exclude_from_list=True),
        HasOne("aircraft_id", identity="aircraft", label="Aircraft", required=True),
        StringField("departure", required=True),
        StringField("arrival", required=True),
        DateTimeField("first_movement", required=False),
        DateTimeField("last_movement", required=False),
    ]

    searchable_fields = ["aircraft_id"]
    sortable_fields = ["id"]

    def __init__(self, repo: FlightRepository) -> None:
        self._repo = repo
        super().__init__()

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: dict[str, Any] | str | None = None,
        order_by: list[str] | None = None,
    ) -> Sequence[Any]:
        page = await self._repo.find_flights(
            FlightQuery(limit=min(skip + limit, 1000))
        )
        return page.items[skip : skip + limit]

    async def count(
        self,
        request: Request,
        where: dict[str, Any] | str | None = None,
    ) -> int:
        return await self._repo.count_flights(FlightQuery())

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        return await self._repo.get_flight_by_id(str(pk))

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        flight_ids = [str(pk) for pk in pks]
        flights_by_id = await self._repo.get_flights_by_ids(flight_ids)
        return list(flights_by_id.values())

    async def _augment_overrides(
        self, obj: Any, overrides: dict[str, Any], request: Request, action: Any
    ) -> None:
        overrides["departure"] = _significant_point_display(obj.departure)
        overrides["arrival"] = _significant_point_display(obj.arrival)

    async def create(self, request: Request, data: dict[str, Any]) -> Any:
        values, errors = build_or_collect(
            {
                "departure": lambda: SignificantPoint.designator(data["departure"]),
                "arrival": lambda: SignificantPoint.designator(data["arrival"]),
            }
        )
        if errors:
            raise FormValidationError(errors)
        try:
            flight = Flight(
                str(data["aircraft_id"]),
                values["departure"],
                values["arrival"],
                first_movement=data.get("first_movement"),
                last_movement=data.get("last_movement"),
            )
        except ValidationError as exc:
            raise FormValidationError({"aircraft_id": str(exc)}) from exc
        return await self._repo.save_flight(flight)

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        values, errors = build_or_collect(
            {
                "departure": lambda: SignificantPoint.designator(data["departure"]),
                "arrival": lambda: SignificantPoint.designator(data["arrival"]),
            }
        )
        if errors:
            raise FormValidationError(errors)
        try:
            flight = Flight(
                str(data["aircraft_id"]),
                values["departure"],
                values["arrival"],
                first_movement=data.get("first_movement"),
                last_movement=data.get("last_movement"),
                id=str(pk),
            )
        except ValidationError as exc:
            raise FormValidationError({"aircraft_id": str(exc)}) from exc
        return await self._repo.save_flight(flight)

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        deleted = 0
        for pk in pks:
            if await self._repo.delete_flight(str(pk)):
                deleted += 1
        return deleted

    async def repr(self, obj: Any, request: Request) -> str:
        aircraft = await self._resolve_fk(obj.aircraft_id, "aircraft", request)
        rego = (
            f"{aircraft.registration} ({aircraft.aircraft_type.designator})"
            if aircraft
            else obj.aircraft_id
        )
        return f"{rego}: {obj.route_summary()}"
