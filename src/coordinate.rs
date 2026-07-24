//! Python binding for the `Coordinate` value object.

use icao_shared_kernel::Coordinate as DomainCoordinate;
use pyo3::prelude::*;

use crate::convert::parse_decimal;
use crate::error::to_py_err;

/// A latitude/longitude position in decimal degrees (WGS-84).
///
/// Latitude and longitude cross as strings, round-tripping exactly through
/// Python's `decimal.Decimal(str(...))` with no binary-float precision loss.
#[pyclass(eq, hash, frozen, from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct Coordinate(pub(crate) DomainCoordinate);

#[pymethods]
impl Coordinate {
    #[new]
    fn new(latitude: &str, longitude: &str) -> PyResult<Self> {
        let latitude = parse_decimal(latitude)?;
        let longitude = parse_decimal(longitude)?;
        DomainCoordinate::new(latitude, longitude)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn latitude(&self) -> String {
        self.0.latitude().to_string()
    }

    #[getter]
    fn longitude(&self) -> String {
        self.0.longitude().to_string()
    }

    fn __repr__(&self) -> String {
        format!("Coordinate({}, {})", self.0.latitude(), self.0.longitude())
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}
