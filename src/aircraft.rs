//! Python binding for the `Aircraft` aggregate root.

use icao_shared_kernel::Aircraft as DomainAircraft;
use pyo3::prelude::*;
use uuid::Uuid;

use crate::aircraft_registration::AircraftRegistration;
use crate::aircraft_type::AircraftType;
use crate::error::to_py_err;

/// Aircraft reference entity: ICAO-universal identity and descriptors.
#[pyclass(eq, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq)]
pub struct Aircraft(pub(crate) DomainAircraft);

#[pymethods]
impl Aircraft {
    #[new]
    #[pyo3(signature = (aircraft_type, registration, id=None))]
    fn new(
        aircraft_type: &AircraftType,
        registration: &AircraftRegistration,
        id: Option<Uuid>,
    ) -> PyResult<Self> {
        let id = id.unwrap_or_else(Uuid::new_v4);
        Ok(Self(DomainAircraft::with(
            id,
            aircraft_type.0.clone(),
            registration.0.clone(),
        )))
    }

    /// Convenience constructor from raw strings, validating each part.
    #[staticmethod]
    fn create(type_designator: &str, nationality: &str, registration: &str) -> PyResult<Self> {
        DomainAircraft::create(type_designator, nationality, registration)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn id(&self) -> Uuid {
        self.0.id
    }

    #[getter]
    fn aircraft_type(&self) -> AircraftType {
        AircraftType(self.0.aircraft_type.clone())
    }

    #[getter]
    fn registration(&self) -> AircraftRegistration {
        AircraftRegistration(self.0.registration.clone())
    }

    fn __repr__(&self) -> String {
        format!("Aircraft({:?})", self.0.to_string())
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}
