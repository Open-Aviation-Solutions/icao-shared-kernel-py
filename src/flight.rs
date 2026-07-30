//! Python binding for the `Flight` aggregate root — the Shared Kernel thin
//! hub for the physical flight event.

use icao_shared_kernel::Flight as DomainFlight;
use pyo3::prelude::*;
use time::UtcDateTime;
use uuid::Uuid;

use crate::error::to_py_err;
use crate::flight_duration::FlightDuration;
use crate::significant_point::SignificantPoint;

/// Which aircraft flew, from where to where, and when it first and last
/// moved under its own power. `first_movement`/`last_movement` are aware
/// `datetime.datetime` values in UTC.
#[pyclass(eq, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq)]
pub struct Flight(pub(crate) DomainFlight);

#[pymethods]
impl Flight {
    #[new]
    #[pyo3(signature = (aircraft_id, departure, arrival, first_movement=None, last_movement=None, id=None))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        aircraft_id: Uuid,
        departure: PyRef<'_, SignificantPoint>,
        arrival: PyRef<'_, SignificantPoint>,
        first_movement: Option<UtcDateTime>,
        last_movement: Option<UtcDateTime>,
        id: Option<Uuid>,
    ) -> PyResult<Self> {
        let id = id.unwrap_or_else(Uuid::new_v4);
        Ok(Self(DomainFlight::with(
            id,
            aircraft_id,
            departure.to_domain(),
            arrival.to_domain(),
            first_movement,
            last_movement,
        )))
    }

    /// Convenience constructor from coded designator strings, with no
    /// movement times recorded.
    #[staticmethod]
    fn create(aircraft_id: Uuid, departure: &str, arrival: &str) -> PyResult<Self> {
        DomainFlight::create(aircraft_id, departure, arrival)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn id(&self) -> Uuid {
        self.0.id
    }

    #[getter]
    fn aircraft_id(&self) -> Uuid {
        self.0.aircraft_id
    }

    #[getter]
    fn departure(&self) -> SignificantPoint {
        SignificantPoint::from(self.0.departure.clone())
    }

    #[getter]
    fn arrival(&self) -> SignificantPoint {
        SignificantPoint::from(self.0.arrival.clone())
    }

    #[getter]
    fn first_movement(&self) -> Option<UtcDateTime> {
        self.0.first_movement
    }

    #[getter]
    fn last_movement(&self) -> Option<UtcDateTime> {
        self.0.last_movement
    }

    /// Canonical short route string, e.g. `YSBK-YSCN`.
    fn route_summary(&self) -> String {
        self.0.route_summary()
    }

    /// Block time, derived from the movement timestamps — `None` unless both
    /// are recorded.
    fn duration(&self) -> Option<FlightDuration> {
        self.0.duration().map(FlightDuration)
    }

    fn __repr__(&self) -> String {
        format!("Flight({:?})", self.0.route_summary())
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}
