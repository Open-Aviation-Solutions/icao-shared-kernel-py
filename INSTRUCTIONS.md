# icao-shared-kernel-py — Working Instructions

Python bindings (PyO3) for the [`icao-shared-kernel-rs`](https://github.com/Open-Aviation-Solutions/icao-shared-kernel-rs)
domain crate. Sibling repo to `icao-shared-kernel-rs`; the design decisions
behind this crate are recorded in `tasks/0001-python-support-plan.md`.
Repository protocols and infrastructure adapters (filesystem, admin, etc.)
deliberately do not live here — that's each consuming application's own
decision (e.g. `pilot-logbook` owns its own), not this crate's.

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
- **Boundary type mapping is fixed** (see task 0001 for the reasoning, and
  task 0003 for the `Uuid` revision):
  - `Uuid` ↔ Python `uuid.UUID`, via PyO3's built-in `uuid` feature.
  - `time::UtcDateTime` ↔ aware Python `datetime.datetime` (UTC), via
    PyO3's built-in `time` feature.
  - `rust_decimal::Decimal` ↔ Python `str` — the one remaining hand-rolled
    conversion, in `convert.rs`.

  **Prefer a PyO3 feature to a hand-rolled string conversion.** Ids used to
  cross as `str` simply because nobody checked; the feature existed. Where a
  native Python type exists and PyO3 supports it, use it — a stringified type
  pushes conversion (and a class of quiet bugs) onto every consumer.
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
- **`#[pyclass(eq)]` on everything the domain crate compares.** Every
  aggregate and value object derives `PartialEq` in `icao-shared-kernel-rs`,
  so Python gets value equality too. Without `eq`, `==` silently falls back
  to identity — it does not fail, it just quietly answers the wrong
  question, and consumers end up comparing field by field to work around it
  (see task 0004). When adding a class, opt in unless the domain type
  genuinely has no `PartialEq`.
- **Type stubs are hand-written** (`*.pyi`), not generated — see task 0001
  for why. Keep them in sync with `src/lib.rs`'s public surface by hand.

## Commands

```sh
make test   # cargo test has no meaning here; pytest against the built extension
make lint   # cargo clippy -- -D warnings
make fmt    # cargo fmt
make check  # lint + fmt check + pytest
```
