//! Python binding for the `DeviceQualification` value object.

use icao_shared_kernel::DeviceQualification as DomainDeviceQualification;
use pyo3::prelude::*;
use time::Date;

use crate::error::to_py_err;

/// A qualification granted to a training device by a national aviation
/// authority, valid over a bounded period.
///
/// Qualifications expire, so `is_in_force_on(date)` — not a bare boolean — is
/// how you ask whether a device was qualified. `valid_from`/`valid_until` are
/// `datetime.date` values, inclusive at both ends.
#[pyclass(eq, hash, frozen, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct DeviceQualification(pub(crate) DomainDeviceQualification);

#[pymethods]
impl DeviceQualification {
    #[new]
    fn new(
        issuing_state: &str,
        issuing_authority: &str,
        level: &str,
        valid_from: Date,
        valid_until: Date,
    ) -> PyResult<Self> {
        DomainDeviceQualification::new(
            issuing_state,
            issuing_authority,
            level,
            valid_from,
            valid_until,
        )
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

    /// The qualification level as the authority expressed it — a string, not
    /// an enum, because the levels in use span several schemes.
    #[getter]
    fn level(&self) -> &str {
        self.0.level()
    }

    #[getter]
    fn valid_from(&self) -> Date {
        self.0.valid_from()
    }

    #[getter]
    fn valid_until(&self) -> Date {
        self.0.valid_until()
    }

    /// Whether the qualification was in force on `date`, inclusive of both
    /// end points.
    fn is_in_force_on(&self, date: Date) -> bool {
        self.0.is_in_force_on(date)
    }

    fn __repr__(&self) -> String {
        format!(
            "DeviceQualification({:?}, {:?}, {:?}, {}, {})",
            self.0.issuing_state(),
            self.0.issuing_authority(),
            self.0.level(),
            self.0.valid_from(),
            self.0.valid_until(),
        )
    }
}
