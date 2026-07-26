//! Python binding for the `DeviceDesignation` value object.

use icao_shared_kernel::DeviceDesignation as DomainDeviceDesignation;
use pyo3::prelude::*;

use crate::error::to_py_err;

/// Free-text identification of a physical training device — typically
/// manufacturer, model, and serial number. Only non-emptiness is enforced.
#[pyclass(eq, hash, frozen, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct DeviceDesignation(pub(crate) DomainDeviceDesignation);

#[pymethods]
impl DeviceDesignation {
    #[new]
    fn new(designation: &str) -> PyResult<Self> {
        DomainDeviceDesignation::parse(designation)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn designation(&self) -> &str {
        self.0.as_str()
    }

    fn __repr__(&self) -> String {
        format!("DeviceDesignation({:?})", self.0.as_str())
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}
