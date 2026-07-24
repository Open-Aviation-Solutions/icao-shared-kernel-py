//! Hand-written string conversions for the two boundary types with no
//! first-party PyO3 support and no chosen native Python equivalent.
//!
//! `Uuid` and `Decimal` cross as plain strings by design (not the native
//! `uuid.UUID` / `decimal.Decimal` Python types) — see task 0015. Movement
//! timestamps (`time::UtcDateTime`) need no such helper: PyO3's `time`
//! feature converts them directly to/from an aware Python `datetime.datetime`
//! in UTC.

use pyo3::exceptions::PyValueError;
use pyo3::PyResult;
use rust_decimal::Decimal;
use std::str::FromStr;
use uuid::Uuid;

pub(crate) fn parse_uuid(value: &str) -> PyResult<Uuid> {
    Uuid::parse_str(value).map_err(|err| PyValueError::new_err(format!("invalid UUID: {err}")))
}

pub(crate) fn parse_decimal(value: &str) -> PyResult<Decimal> {
    Decimal::from_str(value).map_err(|err| PyValueError::new_err(format!("invalid decimal: {err}")))
}
