//! Python binding for the `AircraftRegistration` value object.

use icao_shared_kernel::AircraftRegistration as DomainAircraftRegistration;
use pyo3::prelude::*;

use crate::error::to_py_err;

/// Aircraft nationality and registration marks (ICAO Annex 7).
#[pyclass(eq, hash, frozen, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct AircraftRegistration(pub(crate) DomainAircraftRegistration);

#[pymethods]
impl AircraftRegistration {
    #[new]
    fn new(nationality: &str, registration: &str) -> PyResult<Self> {
        DomainAircraftRegistration::new(nationality, registration)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn nationality(&self) -> &str {
        self.0.nationality()
    }

    #[getter]
    fn registration(&self) -> &str {
        self.0.registration()
    }

    fn __repr__(&self) -> String {
        format!(
            "AircraftRegistration({:?}, {:?})",
            self.0.nationality(),
            self.0.registration()
        )
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}
