//! Python binding for the `AircraftType` value object.

use icao_shared_kernel::AircraftType as DomainAircraftType;
use pyo3::prelude::*;

use crate::error::to_py_err;

/// An ICAO Doc 8643 aircraft type designator (e.g. `C172`, `B738`).
#[pyclass(eq, hash, frozen, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct AircraftType(pub(crate) DomainAircraftType);

#[pymethods]
impl AircraftType {
    #[new]
    fn new(designator: &str) -> PyResult<Self> {
        DomainAircraftType::parse(designator)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn designator(&self) -> &str {
        self.0.as_str()
    }

    fn __repr__(&self) -> String {
        format!("AircraftType({:?})", self.0.as_str())
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}
