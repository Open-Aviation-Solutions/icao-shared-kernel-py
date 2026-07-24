//! Python bindings (PyO3) for the `icao-shared-kernel` Rust domain crate.
//!
//! Exposes the value objects and aggregate roots as Python classes with the
//! same parse-don't-validate constructors as the Rust crate: invalid
//! instances cannot be built from Python either. This is a fresh, idiomatic
//! Python API — it does not mirror the retired Pydantic package's surface.
//! See `icao-shared-kernel/tasks/0015-python-support-plan.md` for the design
//! decisions behind this crate.

mod aircraft;
mod aircraft_registration;
mod aircraft_type;
mod convert;
mod coordinate;
mod error;
mod flight;
mod flight_duration;
mod licence;
mod pilot;
mod significant_point;
mod waypoint;

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[pymodule]
fn icao_shared_kernel(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<waypoint::Waypoint>()?;
    m.add_class::<coordinate::Coordinate>()?;
    m.add_class::<significant_point::SignificantPoint>()?;
    m.add_class::<flight_duration::FlightDuration>()?;
    m.add_class::<aircraft_type::AircraftType>()?;
    m.add_class::<aircraft_registration::AircraftRegistration>()?;
    m.add_class::<licence::Licence>()?;
    m.add_class::<flight::Flight>()?;
    m.add_class::<aircraft::Aircraft>()?;
    m.add_class::<pilot::Pilot>()?;

    m.add_function(wrap_pyfunction!(waypoint::validate_waypoint_code, m)?)?;

    m.add("ValidationError", py.get_type::<error::ValidationError>())?;
    m.add(
        "WaypointLengthError",
        py.get_type::<error::WaypointLengthError>(),
    )?;
    m.add(
        "WaypointCharsetError",
        py.get_type::<error::WaypointCharsetError>(),
    )?;
    m.add(
        "InvalidAircraftTypeError",
        py.get_type::<error::InvalidAircraftTypeError>(),
    )?;
    m.add("FieldLengthError", py.get_type::<error::FieldLengthError>())?;
    m.add("EmptyFieldError", py.get_type::<error::EmptyFieldError>())?;
    m.add(
        "IssuingStateError",
        py.get_type::<error::IssuingStateError>(),
    )?;
    m.add("LatitudeError", py.get_type::<error::LatitudeError>())?;
    m.add("LongitudeError", py.get_type::<error::LongitudeError>())?;

    Ok(())
}
