"""Waypoint designator validation — adapted from icao-shared-kernel-rs
tests/waypoint.rs, which itself mirrors the original aviation-core pytest
cases."""

import pytest

import icao_shared_kernel as k


@pytest.mark.parametrize(
    "value",
    ["YSBK", "AB", "ABCDE", "RIVET", "DCT01", "WAY99"],
)
def test_valid_codes_accepted(value: str) -> None:
    waypoint = k.Waypoint(value)
    assert waypoint.designator == value


@pytest.mark.parametrize(
    "value",
    [
        "ybth",  # lowercase
        "Ybth",  # mixed case
        "A",  # too short
        "ABCDEF",  # too long
        "",  # empty
        "YS-BK",  # non-alphanumeric
    ],
)
def test_invalid_codes_rejected(value: str) -> None:
    with pytest.raises(k.ValidationError):
        k.Waypoint(value)


def test_length_error_type_and_message() -> None:
    with pytest.raises(k.WaypointLengthError, match="Waypoint 'A' must be 2-5 characters long"):
        k.Waypoint("A")


def test_charset_error_type_and_message() -> None:
    with pytest.raises(
        k.WaypointCharsetError, match="Waypoint 'ybth' must be uppercase alphanumeric"
    ):
        k.Waypoint("ybth")


def test_all_digit_code_rejected() -> None:
    # No letters at all: str.isupper()-equivalent semantics reject it.
    with pytest.raises(k.WaypointCharsetError):
        k.Waypoint("12345")


def test_validate_waypoint_code_free_function() -> None:
    k.validate_waypoint_code("YSBK")
    with pytest.raises(k.WaypointLengthError):
        k.validate_waypoint_code("A")
