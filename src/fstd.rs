//! Python binding for the `FlightSimulationTrainingDevice` aggregate root.

use icao_shared_kernel::{
    FlightSimulationTrainingDevice as DomainFstd, FstdKind as DomainFstdKind,
};
use pyo3::prelude::*;
use uuid::Uuid;

use crate::device_designation::DeviceDesignation;
use crate::device_qualification::DeviceQualification;
use crate::error::to_py_err;

/// The kind of apparatus a flight simulation training device is — the three
/// types named by the ICAO Annex 1 definition.
// `from_py_object` is opted into deliberately: unlike the wrapper classes,
// `FstdKind` is passed *into* constructors as an argument, so it needs to
// convert from a Python object.
#[pyclass(eq, hash, frozen, from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub enum FstdKind {
    FlightSimulator,
    FlightProceduresTrainer,
    BasicInstrumentFlightTrainer,
}

impl From<FstdKind> for DomainFstdKind {
    fn from(kind: FstdKind) -> Self {
        match kind {
            FstdKind::FlightSimulator => Self::FlightSimulator,
            FstdKind::FlightProceduresTrainer => Self::FlightProceduresTrainer,
            FstdKind::BasicInstrumentFlightTrainer => Self::BasicInstrumentFlightTrainer,
        }
    }
}

impl From<DomainFstdKind> for FstdKind {
    fn from(kind: DomainFstdKind) -> Self {
        match kind {
            DomainFstdKind::FlightSimulator => Self::FlightSimulator,
            DomainFstdKind::FlightProceduresTrainer => Self::FlightProceduresTrainer,
            DomainFstdKind::BasicInstrumentFlightTrainer => Self::BasicInstrumentFlightTrainer,
        }
    }
}

/// A ground-based apparatus in which flight conditions are simulated (ICAO
/// Annex 1). Not an `Aircraft`: it has no Doc 8643 designator and no
/// registration marks.
///
/// `qualification` is optional and `None` is a first-class case, not missing
/// data — an unqualified personal device is loggable, it simply earns no
/// regulatory credit.
#[pyclass(eq, skip_from_py_object, module = "icao_shared_kernel")]
#[derive(Clone, PartialEq)]
pub struct FlightSimulationTrainingDevice(pub(crate) DomainFstd);

#[pymethods]
impl FlightSimulationTrainingDevice {
    #[new]
    #[pyo3(signature = (kind, designation, qualification=None, id=None))]
    fn new(
        kind: FstdKind,
        designation: &DeviceDesignation,
        qualification: Option<&DeviceQualification>,
        id: Option<Uuid>,
    ) -> PyResult<Self> {
        let id = id.unwrap_or_else(Uuid::new_v4);
        Ok(Self(DomainFstd::with(
            id,
            kind.into(),
            designation.0.clone(),
            qualification.map(|q| q.0.clone()),
        )))
    }

    /// Convenience constructor for an unqualified device, validating the
    /// designation.
    #[staticmethod]
    fn create(kind: FstdKind, designation: &str) -> PyResult<Self> {
        DomainFstd::create(kind.into(), designation)
            .map(Self)
            .map_err(to_py_err)
    }

    #[getter]
    fn id(&self) -> Uuid {
        self.0.id
    }

    #[getter]
    fn kind(&self) -> FstdKind {
        self.0.kind.into()
    }

    #[getter]
    fn designation(&self) -> DeviceDesignation {
        DeviceDesignation(self.0.designation.clone())
    }

    #[getter]
    fn qualification(&self) -> Option<DeviceQualification> {
        self.0.qualification.clone().map(DeviceQualification)
    }

    fn __repr__(&self) -> String {
        format!(
            "FlightSimulationTrainingDevice({:?})",
            self.0.designation.as_str()
        )
    }

    fn __str__(&self) -> String {
        self.0.to_string()
    }
}
