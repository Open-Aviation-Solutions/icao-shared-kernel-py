//! Python binding for the `Licence` value object.

use icao_shared_kernel::Licence as DomainLicence;
use pyo3::prelude::*;

use crate::error::to_py_err;

/// The ICAO-universal identity of a pilot licence (Annex 1): the triple
/// `(issuing_state, issuing_authority, number)`.
#[pyclass(eq, hash, frozen, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct Licence(pub(crate) DomainLicence);

#[pymethods]
impl Licence {
    #[new]
    fn new(issuing_state: &str, issuing_authority: &str, number: &str) -> PyResult<Self> {
        DomainLicence::new(issuing_state, issuing_authority, number)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn issuing_state(&self) -> &str {
        self.0.issuing_state()
    }

    #[getter]
    fn issuing_authority(&self) -> &str {
        self.0.issuing_authority()
    }

    #[getter]
    fn number(&self) -> &str {
        self.0.number()
    }

    fn __repr__(&self) -> String {
        format!(
            "Licence({:?}, {:?}, {:?})",
            self.0.issuing_state(),
            self.0.issuing_authority(),
            self.0.number()
        )
    }
}
