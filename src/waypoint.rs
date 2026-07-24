//! Python binding for the `Waypoint` value object.

use icao_shared_kernel::Waypoint as DomainWaypoint;
use pyo3::prelude::*;

use crate::error::to_py_err;

/// A validated ICAO waypoint designator (e.g. `YSBK`, `RIVET`).
#[pyclass(eq, hash, frozen, from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct Waypoint(pub(crate) DomainWaypoint);

#[pymethods]
impl Waypoint {
    #[new]
    fn new(designator: &str) -> PyResult<Self> {
        DomainWaypoint::parse(designator)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn designator(&self) -> &str {
        self.0.as_str()
    }

    fn __repr__(&self) -> String {
        format!("Waypoint({:?})", self.0.as_str())
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}

/// Validate a waypoint designator without constructing a `Waypoint`.
#[pyfunction]
pub(crate) fn validate_waypoint_code(code: &str) -> PyResult<()> {
    icao_shared_kernel::validate_waypoint_code(code).map_err(to_py_err)
}
