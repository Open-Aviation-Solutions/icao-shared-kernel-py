//! Python binding for the `Pilot` aggregate root.

use icao_shared_kernel::Pilot as DomainPilot;
use pyo3::prelude::*;
use uuid::Uuid;

use crate::error::to_py_err;
use crate::licence::Licence;

/// Pilot identity and the licences they hold. A pilot can hold licences from
/// multiple States simultaneously (ICAO Annex 1 imposes no single-State
/// restriction).
#[pyclass(eq, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq)]
pub struct Pilot(pub(crate) DomainPilot);

#[pymethods]
impl Pilot {
    #[new]
    #[pyo3(signature = (display_name, legal_name=None, licences=None, id=None))]
    fn new(
        display_name: &str,
        legal_name: Option<&str>,
        licences: Option<Vec<PyRef<'_, Licence>>>,
        id: Option<Uuid>,
    ) -> PyResult<Self> {
        let id = id.unwrap_or_else(Uuid::new_v4);
        let licences = licences
            .unwrap_or_default()
            .iter()
            .map(|licence| licence.0.clone())
            .collect();
        DomainPilot::with(id, display_name, legal_name.map(str::to_string), licences)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn id(&self) -> Uuid {
        self.0.id
    }

    #[getter]
    fn display_name(&self) -> &str {
        self.0.display_name()
    }

    #[getter]
    fn legal_name(&self) -> Option<&str> {
        self.0.legal_name()
    }

    #[getter]
    fn licences(&self) -> Vec<Licence> {
        self.0.licences.iter().cloned().map(Licence).collect()
    }

    fn __repr__(&self) -> String {
        format!("Pilot({:?})", self.0.display_name())
    }
}
