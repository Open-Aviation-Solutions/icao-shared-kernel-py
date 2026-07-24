"""Hand-written (de)serialisation for the PyO3 aggregates and their nested
value objects, filling in for Pydantic's ``.model_dump()`` /
``.model_validate()`` (see task 0002-infrastructure-extras.md D2/D5).

Written once per aggregate here and reused by both the filesystem adapters
(``infrastructure.filesystem``) and the admin views' ``JSONField``
serialisation (``infrastructure.admin``) — do not duplicate this logic in
either place.
"""

from datetime import datetime

from .. import (
    Aircraft,
    AircraftRegistration,
    AircraftType,
    Coordinate,
    Flight,
    Licence,
    Pilot,
    SignificantPoint,
)


def significant_point_to_dict(point: SignificantPoint) -> dict:
    match point:
        case SignificantPoint.Designator(waypoint):
            return {"kind": "designator", "value": waypoint.designator}
        case SignificantPoint.Coordinate(coordinate):
            return {
                "kind": "coordinate",
                "latitude": coordinate.latitude,
                "longitude": coordinate.longitude,
            }
    raise ValueError(f"unhandled SignificantPoint variant: {point!r}")


def significant_point_from_dict(data: dict) -> SignificantPoint:
    kind = data["kind"]
    if kind == "designator":
        return SignificantPoint.designator(data["value"])
    if kind == "coordinate":
        return SignificantPoint.Coordinate(
            Coordinate(data["latitude"], data["longitude"])
        )
    raise ValueError(f"unknown SignificantPoint kind: {kind!r}")


def aircraft_to_dict(aircraft: Aircraft) -> dict:
    return {
        "id": aircraft.id,
        "aircraft_type": aircraft.aircraft_type.designator,
        "registration": {
            "nationality": aircraft.registration.nationality,
            "registration": aircraft.registration.registration,
        },
    }


def aircraft_from_dict(data: dict) -> Aircraft:
    registration = data["registration"]
    return Aircraft(
        AircraftType(data["aircraft_type"]),
        AircraftRegistration(
            registration["nationality"], registration["registration"]
        ),
        id=data["id"],
    )


def licence_to_dict(licence: Licence) -> dict:
    return {
        "issuing_state": licence.issuing_state,
        "issuing_authority": licence.issuing_authority,
        "number": licence.number,
    }


def licence_from_dict(data: dict) -> Licence:
    return Licence(data["issuing_state"], data["issuing_authority"], data["number"])


def pilot_to_dict(pilot: Pilot) -> dict:
    return {
        "id": pilot.id,
        "display_name": pilot.display_name,
        "legal_name": pilot.legal_name,
        "licences": [licence_to_dict(licence) for licence in pilot.licences],
    }


def pilot_from_dict(data: dict) -> Pilot:
    return Pilot(
        data["display_name"],
        legal_name=data["legal_name"],
        licences=[licence_from_dict(item) for item in data["licences"]],
        id=data["id"],
    )


def flight_to_dict(flight: Flight) -> dict:
    return {
        "id": flight.id,
        "aircraft_id": flight.aircraft_id,
        "departure": significant_point_to_dict(flight.departure),
        "arrival": significant_point_to_dict(flight.arrival),
        "first_movement": (
            flight.first_movement.isoformat() if flight.first_movement else None
        ),
        "last_movement": (
            flight.last_movement.isoformat() if flight.last_movement else None
        ),
    }


def flight_from_dict(data: dict) -> Flight:
    return Flight(
        data["aircraft_id"],
        significant_point_from_dict(data["departure"]),
        significant_point_from_dict(data["arrival"]),
        first_movement=(
            datetime.fromisoformat(data["first_movement"])
            if data["first_movement"]
            else None
        ),
        last_movement=(
            datetime.fromisoformat(data["last_movement"])
            if data["last_movement"]
            else None
        ),
        id=data["id"],
    )
