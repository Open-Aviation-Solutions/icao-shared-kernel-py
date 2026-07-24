//! Python binding for the `FlightDuration` value object.

use icao_shared_kernel::FlightDuration as DomainFlightDuration;
use pyo3::prelude::*;

/// A flight duration in whole minutes.
#[pyclass(
    eq,
    ord,
    hash,
    frozen,
    skip_from_py_object,
    module = "icao_shared_kernel"
)]
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct FlightDuration(pub(crate) DomainFlightDuration);

#[pymethods]
impl FlightDuration {
    #[new]
    fn new(total_minutes: i64) -> Self {
        Self(DomainFlightDuration::new(total_minutes))
    }

    /// Build a duration from whole hours and minutes (e.g. `1h 30m` -> 90).
    #[staticmethod]
    fn from_hours_minutes(hours: i64, minutes: i64) -> Self {
        Self(DomainFlightDuration::from_hours_minutes(hours, minutes))
    }

    #[getter]
    fn total_minutes(&self) -> i64 {
        self.0.total_minutes()
    }

    #[getter]
    fn hours(&self) -> i64 {
        self.0.hours()
    }

    #[getter]
    fn minutes(&self) -> i64 {
        self.0.minutes()
    }

    /// Exact decimal number of hours (e.g. 90 minutes -> `"1.5"`), as a
    /// string for the same reason `Coordinate` uses strings.
    #[getter]
    fn decimal_hours(&self) -> String {
        self.0.decimal_hours().to_string()
    }

    fn __repr__(&self) -> String {
        format!("FlightDuration({})", self.0.total_minutes())
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}
