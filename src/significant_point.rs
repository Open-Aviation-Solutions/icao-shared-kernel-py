//! Python binding for the `SignificantPoint` value object — a PyO3 "complex
//! enum": `Designator`/`Coordinate` are exposed as `isinstance`-able
//! subclasses of `SignificantPoint`, not flattened into one wrapper.

use icao_shared_kernel::SignificantPoint as DomainSignificantPoint;
use pyo3::prelude::*;

use crate::coordinate::Coordinate;
use crate::error::to_py_err;
use crate::waypoint::Waypoint;

/// An ICAO route/flight-path point: a coded designator or a lat/long.
#[pyclass(eq, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq)]
pub enum SignificantPoint {
    Designator(Waypoint),
    Coordinate(Coordinate),
}

#[pymethods]
impl SignificantPoint {
    /// Parse a coded designator directly into a significant point.
    #[staticmethod]
    fn designator(value: &str) -> PyResult<Self> {
        DomainSignificantPoint::designator(value)
            .map(Self::from)
            .map_err(to_py_err)
    }
}

impl From<DomainSignificantPoint> for SignificantPoint {
    fn from(value: DomainSignificantPoint) -> Self {
        match value {
            DomainSignificantPoint::Designator(waypoint) => Self::Designator(Waypoint(waypoint)),
            DomainSignificantPoint::Coordinate(coordinate) => {
                Self::Coordinate(Coordinate(coordinate))
            }
        }
    }
}

impl SignificantPoint {
    pub(crate) fn to_domain(&self) -> DomainSignificantPoint {
        match self {
            Self::Designator(waypoint) => DomainSignificantPoint::Designator(waypoint.0.clone()),
            Self::Coordinate(coordinate) => {
                DomainSignificantPoint::Coordinate(coordinate.0.clone())
            }
        }
    }
}
