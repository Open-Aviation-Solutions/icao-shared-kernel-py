//! Hand-written string conversion for the one boundary type with no
//! first-party PyO3 support and no chosen native Python equivalent.
//!
//! `Decimal` crosses as a plain string by design, not as `decimal.Decimal`.
//!
//! Two neighbouring types need no helper at all, because PyO3 converts them
//! natively: `Uuid` maps to/from `uuid.UUID` under the `uuid` feature, and
//! `time::UtcDateTime` to/from an aware `datetime.datetime` in UTC under the
//! `time` feature.

use pyo3::exceptions::PyValueError;
use pyo3::PyResult;
use rust_decimal::Decimal;
use std::str::FromStr;

pub(crate) fn parse_decimal(value: &str) -> PyResult<Decimal> {
    Decimal::from_str(value).map_err(|err| PyValueError::new_err(format!("invalid decimal: {err}")))
}
