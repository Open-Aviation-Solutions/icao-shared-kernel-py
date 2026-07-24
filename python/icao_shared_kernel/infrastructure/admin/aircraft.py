"""Admin view for Aircraft."""

from collections.abc import Sequence
from typing import Any

from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import CollectionField, StringField

from ... import Aircraft, AircraftRegistration, AircraftType, ValidationError
from ...domain.repositories.aircraft import AircraftQuery, AircraftRepository
from ._base import PilotAdminBase, route_collection_error


class AircraftAdminView(PilotAdminBase):
    """Admin CRUD view for Aircraft, delegating to AircraftRepository."""

    identity = "aircraft"
    name = "Aircraft"
    label = "Aircraft"
    icon = "fa fa-plane"
    pk_attr = "id"

    fields = [
        StringField("id", read_only=True, exclude_from_list=True),
        CollectionField(
            "aircraft_type",
            fields=[StringField("designator", required=True)],
            required=True,
        ),
        CollectionField(
            "registration",
            fields=[
                StringField("nationality", required=True),
                StringField("registration", required=True),
            ],
            required=True,
        ),
    ]

    searchable_fields = ["aircraft_type"]
    sortable_fields = ["aircraft_type"]

    def __init__(self, repo: AircraftRepository) -> None:
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
        # Admin lists are bounded (max page size 1000); deeper pages would need
        # to switch to keyset paging via cursor — not exercised by starlette-admin.
        page = await self._repo.find_aircraft(
            AircraftQuery(limit=min(skip + limit, 1000))
        )
        return page.items[skip : skip + limit]

    async def count(
        self,
        request: Request,
        where: dict[str, Any] | str | None = None,
    ) -> int:
        return await self._repo.count_aircraft(AircraftQuery())

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        return await self._repo.get_aircraft_by_id(str(pk))

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        results = []
        for pk in pks:
            item = await self._repo.get_aircraft_by_id(str(pk))
            if item is not None:
                results.append(item)
        return results

    @staticmethod
    def _parse_fields(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        aircraft_type_data = data.get("aircraft_type") or {}
        registration_data = data.get("registration") or {}
        values: dict[str, Any] = {}
        errors: dict[str, Any] = {}
        try:
            values["aircraft_type"] = AircraftType(
                aircraft_type_data.get("designator", "")
            )
        except ValidationError as exc:
            errors["aircraft_type"] = route_collection_error(exc, ("designator",))
        try:
            values["registration"] = AircraftRegistration(
                registration_data.get("nationality", ""),
                registration_data.get("registration", ""),
            )
        except ValidationError as exc:
            errors["registration"] = route_collection_error(
                exc, ("nationality", "registration")
            )
        return values, errors

    async def create(self, request: Request, data: dict[str, Any]) -> Any:
        values, errors = self._parse_fields(data)
        if errors:
            raise FormValidationError(errors)
        aircraft = Aircraft(values["aircraft_type"], values["registration"])
        return await self._repo.save_aircraft(aircraft)

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        values, errors = self._parse_fields(data)
        if errors:
            raise FormValidationError(errors)
        aircraft = Aircraft(
            values["aircraft_type"], values["registration"], id=str(pk)
        )
        return await self._repo.save_aircraft(aircraft)

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        deleted = 0
        for pk in pks:
            if await self._repo.delete_aircraft(str(pk)):
                deleted += 1
        return deleted

    async def repr(self, obj: Any, request: Request) -> str:
        return f"{obj.registration} {obj.aircraft_type.designator}"
