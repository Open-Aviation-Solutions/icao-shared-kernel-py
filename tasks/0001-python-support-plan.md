# Python bindings for the Rust shared kernel

**Status:** in progress — bindings, stubs, and a first pytest slice landed
in `icao-shared-kernel-py`; not yet committed/pushed, and downstream
migration hasn't started

## Purpose

Task `0014-rust-wasm-portable-domain-core.md` ported the pure domain to
Rust (`icao-shared-kernel-rs`) with the decision that **Rust becomes the
eventual single source of truth** for kernel validation, Pydantic retired
from that role. This task is the "feel the boundary" step for Python
specifically (step 3 of 0014's sequencing, PyO3 half only — WASM stays a
separate, still-undecided question).

## Context

- `icao-shared-kernel-rs` (`Open-Aviation-Solutions/icao-shared-kernel-rs`,
  merged PR #1) holds the ported domain: value objects (`Waypoint`,
  `Coordinate`, `SignificantPoint`, `FlightDuration`, `AircraftType`,
  `AircraftRegistration`, `Licence`), aggregate roots (`Flight`, `Aircraft`,
  `Pilot`), and a single `ValidationError` enum (8 variants — see
  `src/error.rs`).
- The Python `icao_shared_kernel` package in *this* repo (Pydantic-based)
  is unpublished and already documented as superseded by the Rust crate
  (see 0014). This task replaces it rather than wrapping it.

## Decisions

1. **Separate crate, separate repo**: `icao-shared-kernel-py`, sibling to
   `icao-shared-kernel-rs`, depending on it as a normal Cargo dependency.
   Keeps `icao-shared-kernel-rs` free of `pyo3`/CPython linkage for other
   consumers (a future WASM build, other Rust consumers).
2. **Rust is the sole implementation.** The Python-facing API is fresh and
   idiomatic — it does not need to mimic the old Pydantic surface.
   Downstream consumers (`pilot-logbook`, `pilot-training`, admin views,
   etc.) will need updating to the new API; that migration is accepted as
   a follow-on cost, scoped separately once the bindings exist.
3. **Boundary type mapping:**
   - `Uuid` ↔ Python `str`.
   - `rust_decimal::Decimal` ↔ Python `str` (round-trips exactly through
     `decimal.Decimal(str)`, no float precision loss).
   - `time::UtcDateTime` (`Flight.first_movement` / `last_movement`) ↔
     Python `datetime.datetime` (aware, UTC), no string intermediate.
     **Implementation note**: PyO3 turned out to already ship this exact
     conversion as a first-party, non-default `time` feature
     (`pyo3::conversions::time`) — it requires an aware UTC datetime and
     round-trips exactly, so it's used directly instead of hand-rolling the
     same field-by-field logic. Confirmed working end to end (see
     `icao-shared-kernel-py` `tests/test_flight.py`).
   - `ValidationError` → one Python exception per Rust variant, all
     subclassing a common base so callers can catch broadly or narrowly.
     Today's 8 variants: `WaypointLength`, `WaypointCharset`,
     `AircraftType`, `FieldLength`, `Empty`, `IssuingState`, `Latitude`,
     `Longitude`.
   - `SignificantPoint` → a PyO3 "complex enum" (data-carrying `#[pyclass]`
     enum; `Designator`/`Coordinate` variants exposed as `isinstance`-able
     subclasses), not a flattened wrapper.
4. **Smart constructors stay smart.** Every value object's Python `__new__`
   calls through the real Rust constructor; there is no way to build an
   invalid instance from Python either.
5. **Type stubs are hand-written**, not generated via `pyo3-stub-gen`.
   Reasoning: it's a third-party crate that lags/breaks against PyO3
   releases independently, needs its own macros stacked on top plus a
   separate generation build step, and doesn't remove the manual work we
   already have for the Uuid/Decimal/datetime/complex-enum cases above.
   The surface is small (11 classes, 8 exception types) — cheap to
   hand-maintain. Revisit only if the surface grows enough that drift
   becomes a real risk.
6. **Tests**: a pytest suite adapting the original
   `aviation-core/tests/models/` pytest cases where they still apply, run
   against the compiled extension (`maturin develop` in CI, then
   `pytest`) — the same parity-suite pattern used for the Rust port
   itself.

## Open questions (not yet decided)

- Exact PyPI package / import name (`icao_shared_kernel` is the obvious
  choice, but confirm no conflict and decide whether the old Python
  package name is retired or reused).
- Which downstream repos need updating, and in what order — a separate
  task once the bindings exist and are usable.
- Minimum supported Python version / `abi3` baseline.
- CI wheel matrix / publishing target (PyPI vs private index) — not
  needed for initial development; affects `maturin-action` config later.

## Acceptance criteria

- [x] `icao-shared-kernel-py` repo created (sibling to
      `icao-shared-kernel-rs`), depending on it via Cargo (git dependency,
      `main` branch).
- [x] `maturin develop` builds and installs the extension locally.
- [x] All 7 value objects + 3 aggregates exposed as `#[pyclass]`es with
      smart-constructor `#[new]` methods.
- [x] `ValidationError` exposed as a base + 8 per-variant Python exception
      classes.
- [x] `SignificantPoint` exposed as a complex enum.
- [x] Uuid / Decimal / datetime conversions implemented at the boundary.
- [x] Hand-written `.pyi` stubs covering the public API
      (`icao_shared_kernel.pyi` at the crate root — maturin's convention
      for a pure-Rust project, auto-detected by `maturin develop`).
- [x] pytest suite adapted — from `icao-shared-kernel-rs`'s own Rust test
      tables (`tests/*.rs`), which already mirror the original
      `aviation-core/tests/models/` cases updated for the reshaped domain
      (Licence identity, SignificantPoint, movement timestamps). 63 cases,
      all passing. Not yet a full 1:1 port of every historical case —
      covers the primary validation/construction paths for every type.
- [x] `Makefile` with `help`/`dev`/`check` targets, consistent with
      `icao-shared-kernel-rs` (plus a `venv` target provisioning
      maturin/pytest, since `make dev` must work with no manual setup).
- [x] CI workflow building and testing on push/PR — not yet verified green
      on GitHub Actions (only run locally so far; push and check once
      committed).

Not done / explicitly deferred:
- Not committed or pushed to `icao-shared-kernel-py` yet — left in the
  working tree for review.
- Open questions above (PyPI naming, downstream migration order, `abi3`
  baseline, wheel/publishing matrix) remain unresolved; none blocked this
  slice.

## Notes for the implementer

- Source of truth for the current type/variant list:
  `icao-shared-kernel-rs/src/lib.rs` (public re-exports — exactly what to
  bind) and `src/error.rs` (the 8 `ValidationError` variants).
- `rust_decimal::Decimal` (`Coordinate` lat/long, `FlightDuration`) has no
  first-party PyO3 support — crosses as `str`, hand-written
  (`src/convert.rs`). `Uuid` likewise (also `str`, also hand-written) even
  though PyO3 *does* have an official `uuid` conversions feature — not used,
  since the decision above is `str`, not the native `uuid.UUID` type.
  `time::UtcDateTime` needed no hand-written conversion in the end — see
  the implementation note on decision 3 above.
- Same repo conventions as `icao-shared-kernel-rs`: `INSTRUCTIONS.md` +
  `.claude/CLAUDE.md` symlink, `make check` running lint/fmt-check/test
  (+ pytest here), CI mirroring that repo's `.github/workflows/ci.yml`.
