//! The Python exception hierarchy mirroring the Rust `ValidationError` enum.
//!
//! One exception class per Rust variant, all subclassing a common
//! `ValidationError` base so callers can catch broadly or narrowly.

use icao_shared_kernel::ValidationError as DomainValidationError;
use pyo3::create_exception;
use pyo3::exceptions::PyValueError;
use pyo3::PyErr;

create_exception!(
    icao_shared_kernel,
    ValidationError,
    PyValueError,
    "Base class for every icao_shared_kernel validation error."
);
create_exception!(
    icao_shared_kernel,
    WaypointLengthError,
    ValidationError,
    "A waypoint designator outside the 2-5 character range."
);
create_exception!(
    icao_shared_kernel,
    WaypointCharsetError,
    ValidationError,
    "A waypoint designator that is not uppercase alphanumeric, or has no letter."
);
create_exception!(
    icao_shared_kernel,
    InvalidAircraftTypeError,
    ValidationError,
    "An aircraft type designator that does not match the ICAO Doc 8643 shape."
);
create_exception!(
    icao_shared_kernel,
    FieldLengthError,
    ValidationError,
    "A string field whose length falls outside its bounds."
);
create_exception!(
    icao_shared_kernel,
    EmptyFieldError,
    ValidationError,
    "A required string field that was empty."
);
create_exception!(
    icao_shared_kernel,
    IssuingStateError,
    ValidationError,
    "An issuing state that is not a two-letter ISO 3166-1 alpha-2 code."
);
create_exception!(
    icao_shared_kernel,
    LatitudeError,
    ValidationError,
    "A latitude outside the valid -90..=90 degree range."
);
create_exception!(
    icao_shared_kernel,
    LongitudeError,
    ValidationError,
    "A longitude outside the valid -180..=180 degree range."
);

// `PyErr` and `DomainValidationError` are both foreign types here, so the
// orphan rule rules out `impl From<DomainValidationError> for PyErr`; call
// sites use `.map_err(to_py_err)` instead of relying on `?` conversion.
pub(crate) fn to_py_err(err: DomainValidationError) -> PyErr {
    let message = err.to_string();
    match err {
        DomainValidationError::WaypointLength(_) => WaypointLengthError::new_err(message),
        DomainValidationError::WaypointCharset(_) => WaypointCharsetError::new_err(message),
        DomainValidationError::AircraftType(_) => InvalidAircraftTypeError::new_err(message),
        DomainValidationError::FieldLength { .. } => FieldLengthError::new_err(message),
        DomainValidationError::Empty { .. } => EmptyFieldError::new_err(message),
        DomainValidationError::IssuingState(_) => IssuingStateError::new_err(message),
        DomainValidationError::Latitude(_) => LatitudeError::new_err(message),
        DomainValidationError::Longitude(_) => LongitudeError::new_err(message),
    }
}
