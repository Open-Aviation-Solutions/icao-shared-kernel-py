# icao-shared-kernel (Python bindings)

Python bindings (PyO3) for the [`icao-shared-kernel-rs`](https://github.com/Open-Aviation-Solutions/icao-shared-kernel-rs)
Rust domain crate: the ICAO shared-kernel value objects and aggregate
roots, exposed as native Python classes.

This is the **sole** Python implementation of the kernel — Rust is the
single source of truth for validation. The API is fresh and idiomatic; it
does not mirror the retired Pydantic package.

## What's here

- Value objects: `Waypoint`, `Coordinate`, `SignificantPoint` (a "complex
  enum": `SignificantPoint.Designator` / `SignificantPoint.Coordinate`),
  `FlightDuration`, `AircraftType`, `AircraftRegistration`, `Licence`.
- Aggregate roots: `Flight`, `Aircraft`, `Pilot`.
- A `ValidationError` base exception plus one subclass per Rust
  `ValidationError` variant (`WaypointLengthError`, `WaypointCharsetError`,
  `InvalidAircraftTypeError`, `FieldLengthError`, `EmptyFieldError`,
  `IssuingStateError`, `LatitudeError`, `LongitudeError`).

Every constructor is a smart constructor: invalid instances cannot be built
from Python.

## Boundary type mapping

- `Uuid` and `Decimal` cross as plain `str` (round-trips exactly via
  `decimal.Decimal(str(...))`, no float precision loss).
- Flight movement timestamps cross as aware `datetime.datetime` in UTC
  (PyO3's built-in `time` feature conversion — no string intermediate).

See `icao-shared-kernel/tasks/0015-python-support-plan.md` for the full
design decisions behind this crate.

## Development

Requires a Rust toolchain, a C linker, and Python 3.9+.

```sh
make help   # list targets
make dev    # build the extension and install it into .venv
make test   # run the pytest suite
make check  # clippy + fmt check + pytest
```
