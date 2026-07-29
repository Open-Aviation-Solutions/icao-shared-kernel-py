//! Python binding for the `FstdSession` aggregate root.

use icao_shared_kernel::FstdSession as DomainFstdSession;
use pyo3::prelude::*;
use time::UtcDateTime;
use uuid::Uuid;

use crate::aircraft_type::AircraftType;
use crate::convert::parse_uuid;
use crate::error::to_py_err;
use crate::flight_duration::FlightDuration;
use crate::significant_point::SignificantPoint;

/// A training session flown on a flight simulation training device — the
/// sibling of `Flight`, not a variant of it.
///
/// Every field but `device_id` is optional: a session may be an hour of
/// manoeuvre practice representing no particular aircraft and flying no
/// particular route. `simulated_aircraft_type` is recorded per session
/// because an unqualified device is routinely flown as a different type each
/// time.
#[pyclass(skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone)]
pub struct FstdSession(pub(crate) DomainFstdSession);

#[pymethods]
impl FstdSession {
    #[new]
    #[pyo3(signature = (device_id, simulated_aircraft_type=None, departure=None, arrival=None, start=None, end=None, id=None))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        device_id: &str,
        simulated_aircraft_type: Option<&AircraftType>,
        departure: Option<PyRef<'_, SignificantPoint>>,
        arrival: Option<PyRef<'_, SignificantPoint>>,
        start: Option<UtcDateTime>,
        end: Option<UtcDateTime>,
        id: Option<&str>,
    ) -> PyResult<Self> {
        let device_id = parse_uuid(device_id)?;
        let id = match id {
            Some(id) => parse_uuid(id)?,
            None => Uuid::new_v4(),
        };
        Ok(Self(DomainFstdSession::with(
            id,
            device_id,
            simulated_aircraft_type.map(|t| t.0.clone()),
            departure.map(|p| p.to_domain()),
            arrival.map(|p| p.to_domain()),
            start,
            end,
        )))
    }

    /// Convenience constructor for a session with no route and no times
    /// recorded, validating the simulated type designator.
    #[staticmethod]
    fn create(device_id: &str, simulated_type: &str) -> PyResult<Self> {
        let device_id = parse_uuid(device_id)?;
        DomainFstdSession::create(device_id, simulated_type)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn id(&self) -> String {
        self.0.id.to_string()
    }

    #[getter]
    fn device_id(&self) -> String {
        self.0.device_id.to_string()
    }

    #[getter]
    fn simulated_aircraft_type(&self) -> Option<AircraftType> {
        self.0.simulated_aircraft_type.clone().map(AircraftType)
    }

    #[getter]
    fn departure(&self) -> Option<SignificantPoint> {
        self.0.departure.clone().map(SignificantPoint::from)
    }

    #[getter]
    fn arrival(&self) -> Option<SignificantPoint> {
        self.0.arrival.clone().map(SignificantPoint::from)
    }

    #[getter]
    fn start(&self) -> Option<UtcDateTime> {
        self.0.start
    }

    #[getter]
    fn end(&self) -> Option<UtcDateTime> {
        self.0.end
    }

    /// Canonical short route string, e.g. `YSBK-YSCN` — `None` unless both
    /// endpoints were recorded.
    fn route_summary(&self) -> Option<String> {
        self.0.route_summary()
    }

    /// Session time, derived from the timestamps — `None` unless both are
    /// recorded.
    fn duration(&self) -> Option<FlightDuration> {
        self.0.duration().map(FlightDuration)
    }

    fn __repr__(&self) -> String {
        format!("FstdSession({:?})", self.0.to_string())
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}
