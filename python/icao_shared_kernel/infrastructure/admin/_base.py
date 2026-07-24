"""Shared base class and validation helper for all admin views.

PyO3 constructors are fail-fast (first bad argument raises, no batching),
unlike Pydantic's ``model_validate`` which reports every field's error in
one call. ``build_or_collect`` recovers the same admin-form UX: try each
field's own value-object constructor independently, collecting every
failure — since all 8 domain exceptions share one ``ValidationError`` base
(see ``icao_shared_kernel.pyi``), a single generic loop works for every
aggregate. See task 0002-infrastructure-extras.md.
"""

from typing import Any, Callable

from starlette.requests import Request
from starlette_admin import RequestAction
from starlette_admin.fields import BaseField, HasOne, JSONField
from starlette_admin.views import BaseModelView

from ... import Aircraft, Flight, Licence, Pilot, ValidationError
from .._codec import (
    aircraft_to_dict,
    flight_to_dict,
    licence_to_dict,
    pilot_to_dict,
)

_TO_DICT: dict[type, Callable[[Any], dict]] = {
    Aircraft: aircraft_to_dict,
    Pilot: pilot_to_dict,
    Flight: flight_to_dict,
    Licence: licence_to_dict,
}


def build_or_collect(
    fields: dict[str, Callable[[], Any]],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Try each field constructor independently, collecting values and errors.

    Returns ``(values, errors)`` — ``values`` holds the successfully built
    value objects keyed by field name; ``errors`` holds
    ``{field: message}`` for the rest, in the shape
    ``starlette_admin.exceptions.FormValidationError`` expects directly.
    """
    values: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for name, construct in fields.items():
        try:
            values[name] = construct()
        except ValidationError as exc:
            errors[name] = str(exc)
    return values, errors


class _WithRelations:
    """Proxy that substitutes pre-fetched related objects for HasOne fields."""

    def __init__(self, obj: Any, overrides: dict[str, Any]) -> None:
        self._obj = obj
        self._overrides = overrides

    def __getattr__(self, name: str) -> Any:
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._obj, name)


class PilotAdminBase(BaseModelView):
    """BaseModelView subclass that serialises PyO3 aggregates in JSONFields."""

    async def serialize(
        self,
        obj: Any,
        request: Request,
        action: RequestAction,
        include_relationships: bool = True,
        include_select2: bool = False,
    ) -> dict[str, Any]:
        if include_relationships:
            overrides: dict[str, Any] = {}
            for field in self.get_fields_list(request, action):
                if isinstance(field, HasOne) and field.identity is not None:
                    fk_value = getattr(obj, field.name, None)
                    if fk_value is not None:
                        foreign_model = self._find_foreign_model(field.identity)
                        full_obj = await foreign_model.find_by_pk(
                            request, str(fk_value)
                        )
                        if full_obj is not None:
                            overrides[field.name] = full_obj
            await self._augment_overrides(obj, overrides, request, action)
            if overrides:
                obj = _WithRelations(obj, overrides)
        return await super().serialize(
            obj, request, action, include_relationships, include_select2
        )

    async def _augment_overrides(
        self,
        obj: Any,
        overrides: dict[str, Any],
        request: Request,
        action: RequestAction,
    ) -> None:
        """Override to inject extra virtual attributes into the _WithRelations proxy."""

    async def _resolve_fk(self, val: Any, identity: str, request: Request) -> Any:
        """Return the full related object.

        val is either the raw id (a str — stored FK, when repr is called
        outside serialize or when include_relationships=False) or already a
        domain object (when called inside serialize after _WithRelations
        substitution; domain objects are never plain str).
        """
        if isinstance(val, str):
            view = self._find_foreign_model(identity)
            return await view.find_by_pk(request, val)
        return val

    async def get_serialized_pk_value(self, request: Request, obj: Any) -> Any:
        return str(await self.get_pk_value(request, obj))

    async def serialize_field_value(
        self,
        value: Any,
        field: BaseField,
        action: RequestAction,
        request: Request,
    ) -> Any:
        if isinstance(field, JSONField) and value is not None:
            to_dict = _TO_DICT.get(type(value))
            if to_dict is not None:
                return to_dict(value)
            if isinstance(value, list):
                return [
                    _TO_DICT[type(item)](item) if type(item) in _TO_DICT else item
                    for item in value
                ]
        return await super().serialize_field_value(value, field, action, request)
