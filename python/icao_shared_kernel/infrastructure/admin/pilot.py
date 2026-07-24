"""Admin view for Pilot."""

from collections.abc import Sequence
from html import escape
from typing import Any

from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import CollectionField, ListField, StringField

from ... import Licence, Pilot, ValidationError
from ...domain.repositories.pilot import PilotQuery, PilotRepository
from ._base import PilotAdminBase, route_collection_error

# display_name/legal_name have no dedicated value-object constructor in the
# Rust domain crate (unlike every other field on every aggregate) — they're
# plain strings validated inline by Pilot's own constructor, so they can't
# be checked independently via build_or_collect. Pilot's ValidationError
# messages for these fields always start with the field name itself (see
# icao-shared-kernel-rs src/error.rs's FieldLength/Empty variants), so we
# route the error to the matching form field on a best-effort basis.
_PILOT_SCALAR_FIELDS = ("display_name", "legal_name")
_LICENCE_FIELDS = ("issuing_state", "issuing_authority", "number")


def _parse_licences(
    items: list[dict[str, Any]],
) -> tuple[list[Licence], dict[int, dict[str, str]]]:
    licences: list[Licence] = []
    # ListField's own error rendering does error.get(loop.index0) expecting
    # int keys, then hands that value to the CollectionField below it, which
    # does error.get(field.name) in turn — hence the two-level nesting.
    errors: dict[int, dict[str, str]] = {}
    for i, item in enumerate(items):
        try:
            licences.append(
                Licence(
                    item.get("issuing_state", ""),
                    item.get("issuing_authority", ""),
                    item.get("number", ""),
                )
            )
        except ValidationError as exc:
            errors[i] = route_collection_error(exc, _LICENCE_FIELDS)
    return licences, errors


def _route_scalar_error(exc: ValidationError) -> dict[str, str]:
    leading_word = str(exc).split(maxsplit=1)[0] if str(exc) else ""
    field = leading_word if leading_word in _PILOT_SCALAR_FIELDS else "display_name"
    return {field: str(exc)}


class PilotAdminView(PilotAdminBase):
    """Admin CRUD view for Pilot, delegating to PilotRepository."""

    identity = "pilot"
    name = "Pilot"
    label = "Pilots"
    icon = "fa fa-user"
    pk_attr = "id"

    fields = [
        StringField("id", read_only=True, exclude_from_list=True),
        StringField("display_name", required=True),
        StringField("legal_name", required=False),
        ListField(
            CollectionField(
                "licences",
                fields=[
                    StringField("issuing_state", required=True),
                    StringField("issuing_authority", required=True),
                    StringField("number", required=True),
                ],
            ),
        ),
    ]

    searchable_fields = ["display_name"]
    sortable_fields = ["display_name"]

    def __init__(self, repo: PilotRepository) -> None:
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
        page = await self._repo.find_pilots(PilotQuery(limit=min(skip + limit, 1000)))
        return page.items[skip : skip + limit]

    async def count(
        self,
        request: Request,
        where: dict[str, Any] | str | None = None,
    ) -> int:
        return await self._repo.count_pilots(PilotQuery())

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        return await self._repo.get_pilot_by_id(str(pk))

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        results = []
        for pk in pks:
            item = await self._repo.get_pilot_by_id(str(pk))
            if item is not None:
                results.append(item)
        return results

    async def create(self, request: Request, data: dict[str, Any]) -> Any:
        licences, licence_errors = _parse_licences(data.get("licences") or [])
        if licence_errors:
            raise FormValidationError({"licences": licence_errors})
        try:
            pilot = Pilot(
                data["display_name"],
                legal_name=data.get("legal_name") or None,
                licences=licences,
            )
        except ValidationError as exc:
            raise FormValidationError(_route_scalar_error(exc)) from exc
        return await self._repo.save_pilot(pilot)

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        licences, licence_errors = _parse_licences(data.get("licences") or [])
        if licence_errors:
            raise FormValidationError({"licences": licence_errors})
        try:
            pilot = Pilot(
                data["display_name"],
                legal_name=data.get("legal_name") or None,
                licences=licences,
                id=str(pk),
            )
        except ValidationError as exc:
            raise FormValidationError(_route_scalar_error(exc)) from exc
        return await self._repo.save_pilot(pilot)

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        deleted = 0
        for pk in pks:
            if await self._repo.delete_pilot(str(pk)):
                deleted += 1
        return deleted

    async def repr(self, obj: Any, request: Request) -> str:
        licences = ", ".join(
            f"{licence.issuing_state}/{licence.issuing_authority} {licence.number}"
            for licence in obj.licences
        )
        return f"{obj.display_name} ({licences})" if licences else obj.display_name

    async def select2_result(self, obj: Any, request: Request) -> str:
        return f"<span>{escape(await self.repr(obj, request))}</span>"
