# icao-shared-kernel-py — Working Instructions

Python bindings (PyO3) for the [`icao-shared-kernel-rs`](https://github.com/Open-Aviation-Solutions/icao-shared-kernel-rs)
domain crate. Sibling repo to `icao-shared-kernel-rs`; the design decisions
behind this crate are recorded in `tasks/0001-python-support-plan.md`.
Repository protocols/infra deliberately do **not** live here — see
`tasks/0002-repositories-belong-in-consuming-apps.md`.

## Purpose and scope

This crate is Python bindings only — it holds no domain logic of its own.
Every value object and aggregate root wraps the corresponding Rust type
from `icao-shared-kernel-rs` and delegates validation to it; this crate's
job is the boundary (constructors, getters, error mapping, `Uuid`/`Decimal`/
`datetime` conversions), not re-implementing rules.

Rust is the single source of truth for domain validation. The Python API is
fresh and idiomatic — it does not need to mirror the retired Pydantic
`icao_shared_kernel` package's surface. Downstream Python consumers
(`pilot-logbook`, `pilot-training`, admin views) will need updating to this
API; that migration is scoped separately, once this crate is usable.

## Conventions

- **Keep this crate free of domain logic.** A validation rule belongs in
  `icao-shared-kernel-rs`, not here. If a rule needs adding or changing,
  change it there first, then update the binding (usually no change needed,
  since bindings delegate).
- **Boundary type mapping is fixed** (see task 0001 for the reasoning):
  - `Uuid` ↔ Python `str`.
  - `rust_decimal::Decimal` ↔ Python `str`.
  - `time::UtcDateTime` ↔ aware Python `datetime.datetime` (UTC), via
    PyO3's built-in `time` feature — no hand-rolled conversion needed or
    wanted.
- **One `#[pyclass]` per value object / aggregate**, each in its own module
  file (mirrors the Rust crate's module layout), wrapping the domain type
  as a private tuple field: `pub struct Waypoint(pub(crate) DomainWaypoint);`
  with the domain type imported under a `Domain`-prefixed alias to avoid
  name clashes.
- **Errors**: every domain `ValidationError` variant maps to its own Python
  exception class (`src/error.rs`), all subclassing `ValidationError`.
  `PyErr` and the domain crate's `ValidationError` are both foreign types
  here, so the orphan rule rules out a `From` impl — call sites use
  `.map_err(to_py_err)` instead of `?`.
- **`SignificantPoint` is a PyO3 "complex enum"** (`Designator`/`Coordinate`
  as `isinstance`-able subclasses), not a flattened wrapper — matches the
  Rust enum shape and lets Python code `isinstance`/pattern-match on it.
- **`#[pyclass(skip_from_py_object)]`** on every class except `Waypoint` and
  `Coordinate`: PyO3's automatic `Clone`-based `FromPyObject` derive is
  deprecated crate-wide, so it's opted out everywhere it isn't needed.
  `Waypoint`/`Coordinate` opt in explicitly (`from_py_object`) because they
  are `SignificantPoint`'s complex-enum variant fields, which need it to
  extract constructor arguments.
- **Type stubs are hand-written** (`*.pyi`), not generated — see task 0001
  for why. Keep them in sync with `src/lib.rs`'s public surface by hand.

## Commands

```sh
make test   # cargo test has no meaning here; pytest against the built extension
make lint   # cargo clippy -- -D warnings
make fmt    # cargo fmt
make check  # lint + fmt check + pytest
```
