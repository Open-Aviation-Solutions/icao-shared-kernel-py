"""Unit tests for the shared admin form-validation helper.

icao-shared-kernel (Pydantic) built one FormValidationError from a single
model_validate() call's .errors() list. PyO3 constructors are fail-fast, so
build_or_collect() recovers the same "report every field's error at once"
behaviour by trying each field's constructor independently — these tests
are the guarantee that multiple simultaneous bad fields are all reported,
not just the first one encountered."""

from icao_shared_kernel import AircraftRegistration, AircraftType, ValidationError
from icao_shared_kernel.infrastructure.admin._base import build_or_collect


def test_all_valid_fields_collected() -> None:
    values, errors = build_or_collect(
        {
            "aircraft_type": lambda: AircraftType("C172"),
            "registration": lambda: AircraftRegistration("VH", "ABC"),
        }
    )
    assert errors == {}
    assert values["aircraft_type"].designator == "C172"
    assert values["registration"].nationality == "VH"


def test_single_invalid_field_reported() -> None:
    values, errors = build_or_collect(
        {
            "aircraft_type": lambda: AircraftType("C172"),
            "registration": lambda: AircraftRegistration("VH", ""),
        }
    )
    assert "aircraft_type" not in errors
    assert "registration" in errors
    assert "aircraft_type" in values
    assert "registration" not in values


def test_multiple_invalid_fields_all_reported() -> None:
    """The key behaviour Pydantic gave for free: both bad fields are
    reported from one call, not just whichever raises first."""
    values, errors = build_or_collect(
        {
            "aircraft_type": lambda: AircraftType(""),
            "registration": lambda: AircraftRegistration("VH", ""),
        }
    )
    assert set(errors) == {"aircraft_type", "registration"}
    assert values == {}


def test_non_validation_error_propagates() -> None:
    def boom() -> None:
        raise RuntimeError("not a domain error")

    try:
        build_or_collect({"field": boom})
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected RuntimeError to propagate uncaught")


def test_errors_are_instances_of_shared_base() -> None:
    try:
        AircraftType("")
    except ValidationError:
        pass
    else:
        raise AssertionError("expected ValidationError")
