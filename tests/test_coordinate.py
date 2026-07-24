"""Coordinate range validation — adapted from icao-shared-kernel-rs
tests/significant_point.rs (the JSON round-trip cases don't apply here;
this crate doesn't expose serialisation at the Python boundary)."""

import pytest

import icao_shared_kernel as k


@pytest.mark.parametrize(
    "lat, lon",
    [
        ("-33.9461", "151.1772"),
        ("90", "180"),
        ("-90", "-180"),
        ("0", "0"),
    ],
)
def test_valid_coordinates_accepted(lat: str, lon: str) -> None:
    coordinate = k.Coordinate(lat, lon)
    assert coordinate.latitude == lat
    assert coordinate.longitude == lon


@pytest.mark.parametrize(
    "lat, lon, error",
    [
        ("90.1", "0", k.LatitudeError),  # latitude too high
        ("-90.1", "0", k.LatitudeError),  # latitude too low
        ("0", "180.1", k.LongitudeError),  # longitude too high
        ("0", "-180.1", k.LongitudeError),  # longitude too low
    ],
)
def test_out_of_range_coordinates_rejected(lat: str, lon: str, error: type) -> None:
    with pytest.raises(error):
        k.Coordinate(lat, lon)
