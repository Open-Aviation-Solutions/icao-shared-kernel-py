# icao-shared-kernel-py — Working Instructions

Python bindings (PyO3) for the [`icao-shared-kernel-rs`](https://github.com/Open-Aviation-Solutions/icao-shared-kernel-rs)
domain crate. Sibling repo to `icao-shared-kernel-rs`; the design decisions
behind the domain bindings are recorded in `tasks/0001-python-support-plan.md`;
the repository protocols and infrastructure adapters (filesystem, admin) in
`tasks/0002-infrastructure-extras.md`.

## Purpose and scope

The compiled extension (`_icao_shared_kernel`, wrapped by
`python/icao_shared_kernel/__init__.py`) is bindings only — it holds no
domain logic of its own. Every value object and aggregate root wraps the
corresponding Rust type from `icao-shared-kernel-rs` and delegates
validation to it; this crate's job is the boundary (constructors, getters,
error mapping, `Uuid`/`Decimal`/`datetime` conversions), not
re-implementing rules.

Rust is the single source of truth for domain validation. The Python API is
fresh and idiomatic — it does not need to mirror the retired Pydantic
`icao_shared_kernel` package's surface.

Repository protocols (`domain/repositories/`) and infrastructure adapters
(`infrastructure/filesystem/`, `infrastructure/admin/`) are pure Python,
layered on top of the compiled extension — see the "Infrastructure layer"
section below. This package is meant to fully replace
`icao-shared-kernel`'s Pydantic-based package eventually (task 0001's "sole
implementation" decision) — both packages install under the same
distribution name (`icao-shared-kernel`). Downstream Python consumers
(`pilot-logbook`, `pilot-training`) will need updating to this API; that
migration is scoped separately, per consumer.

## Project layout

Mixed maturin Rust/Python project (not pure-Rust): `src/` is the PyO3
crate, compiled to a submodule named `_icao_shared_kernel`;
`python/icao_shared_kernel/__init__.py` wraps and re-exports it, and holds
every pure-Python module (`domain/`, `infrastructure/`). The compiled
submodule is intentionally not the top-level package — pure-Python code
couldn't otherwise sit above it. See task 0002 D2 for the migration
rationale if this needs revisiting.

`python/icao_shared_kernel/__init__.pyi` is the hand-written stub covering
the compiled extension's public surface (classes, exceptions, the one free
function) — maturin auto-detects it there. Pure-Python modules don't need
separate stubs; their own source is the type information.

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

## Infrastructure layer

`domain/repositories/`, `infrastructure/filesystem/`, and
`infrastructure/admin/` are plain Python — no PyO3 involved — layered on
top of the compiled extension's classes. See task 0002 for the full
rationale; the load-bearing conventions:

- **No `.model_dump()`/`.model_validate()`.** PyO3 classes have neither.
  `infrastructure/_codec.py` holds one hand-written `to_dict`/`from_dict`
  pair per aggregate (built from PyO3 getters and constructors) — written
  once there and reused by **both** the filesystem adapters and the admin
  views' `JSONField` serialisation. Don't duplicate this logic in either
  place; if an aggregate's shape changes, `_codec.py` is the only place
  that needs updating.
- **`Page`/`_PageRequest`/`*Query` are plain `dataclasses`, not Pydantic.**
  This crate has no runtime dependency beyond PyO3 (task 0001) — pulling in
  Pydantic just for pagination types would break that.
- **Repository protocols and query filter fields use `str` ids**, matching
  the PyO3 boundary — never `uuid.UUID`.
- **Admin form validation**: PyO3 constructors are fail-fast (first bad
  argument raises, no batching), unlike Pydantic's `model_validate`.
  `infrastructure/admin/_base.py` has two helpers built around the fact
  that every domain exception shares one `ValidationError` base:
  - `build_or_collect(fields)` — for **flat** fields (a plain
    `StringField`/`DateTimeField` directly on the aggregate, e.g.
    `Flight.departure`): try each field's constructor independently,
    collect every failure into `{field: message}`.
  - `route_collection_error(exc, sub_fields)` — for fields backed by a
    `CollectionField` (e.g. `Aircraft.registration`) or `ListField` (e.g.
    `Pilot.licences`): starlette-admin's own templates
    (`forms/collection.html`, `forms/list.html`) expect the error nested
    one level deeper (`{field: {sub_field: message}}`, or
    `{field: {index: {sub_field: message}}}` for a list) — a flat string
    there raises `AttributeError` when the template tries to drill into
    it. Rust reports one error per constructor call, not per argument, so
    this parses the field name every domain error message leads with
    (`error.rs`'s `FieldLength`/`Empty` variants) to pick the right
    sub-field.

  Getting this wrong doesn't fail loudly in review — it 500s only when a
  user actually submits an invalid value through that specific field, so
  any new `CollectionField`/`ListField` needs a create-rejection test
  (`tests/test_admin_views.py`) to catch it, not just a "does the happy
  path work" check.

## Commands

```sh
make test   # cargo test has no meaning here; pytest against the built extension
make lint   # cargo clippy -- -D warnings
make fmt    # cargo fmt
make check  # lint + fmt check + pytest
```
