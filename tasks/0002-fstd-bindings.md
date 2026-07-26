# Bindings for the FSTD device and session aggregates

**Status:** in progress — implemented and passing; the Cargo dependency is
pinned to an unmerged `icao-shared-kernel-rs` branch (see Before merging).

## Purpose

`icao-shared-kernel-rs` task `0001` added two aggregates —
`FlightSimulationTrainingDevice` and `FstdSession` — so a training session
flown on a simulator can be recorded without pretending the device is an
`Aircraft`. This exposes them to Python, following task `0001`'s existing
one-module-per-type layout and boundary mapping.

`pilot-logbook` task `0008` is the consumer waiting on this.

## What's exposed

Five new classes, plus one new exception:

| Rust | Python |
| --- | --- |
| `DeviceDesignation` | `DeviceDesignation` |
| `DeviceQualification` | `DeviceQualification` |
| `FstdKind` | `FstdKind` |
| `FlightSimulationTrainingDevice` | `FlightSimulationTrainingDevice` |
| `FstdSession` | `FstdSession` |
| `ValidationError::ValidityPeriod` | `ValidityPeriodError` |

### Boundary notes

- **`time::Date` ↔ `datetime.date`.** New at this boundary — task `0001`
  mapped `UtcDateTime` ↔ aware `datetime`, but no type needed a plain date
  until `DeviceQualification`'s validity period. PyO3's `time` feature
  (already enabled) covers `Date` as well, so no hand-rolled conversion.
- **`FstdKind` is a plain `#[pyclass]` enum**, not a PyO3 complex enum. It
  carries no data, unlike `SignificantPoint`, so the simple form is right.
  It does opt into `from_py_object`, unlike every other class here: it is
  passed *into* constructors as an argument rather than only returned, so it
  needs to convert from a Python object. Without that opt-in, PyO3 0.29 emits
  a deprecation warning and the derive goes away in a later release.
- **`qualification` is `Optional`.** `None` is a first-class case — an
  unqualified personal device is loggable, it simply earns no regulatory
  credit — not an error and not missing data.
- **`is_in_force_on(date)` rather than a boolean property.** Qualifications
  expire, so there is no date-free way to ask whether a device was qualified.
  The binding preserves that shape deliberately.

## Before merging

`Cargo.toml` pins `icao-shared-kernel` to `branch = "add-fstd-aggregates"`.
Once `icao-shared-kernel-rs` PR #3 merges, **repoint it to `branch = "main"`**
and re-run `make check`. The pin is the only reason this can't merge as-is.

### Verifying locally

Cargo cannot fetch the git dependency from a sandboxed environment (SSH auth
is unavailable to its subprocess). To build and test against a local
`icao-shared-kernel-rs` checkout, temporarily swap the dependency for a path
one:

```toml
icao-shared-kernel = { path = "../icao-shared-kernel-rs" }
```

Restore the git line before committing. A `[patch]` section does *not* work
here — cargo still tries to update the git source to resolve the branch.

## Acceptance criteria

- [x] Five classes registered in `lib.rs`, each in its own module.
- [x] `ValidityPeriodError` mapped from the new `ValidationError` variant and
      exported.
- [x] `icao_shared_kernel.pyi` stubs updated by hand, including the `date`
      import.
- [x] `tests/test_fstd.py` — unqualified device, empty designation, validity
      inclusivity at both ends, invalid period, malformed issuing state,
      one device across two simulated types, session route and duration.
- [x] `make check` passes (clippy `-D warnings`, fmt, 78 pytest tests).
- [ ] Dependency repointed to `main` after PR #3 merges.

## Related

- `icao-shared-kernel-rs` task `0001` / PR #3 — the aggregates.
- `au-casa` task `0002` / PR #1 — the CASA recognition layer, which needs its
  own bindings crate (`au-casa-py`) before `pilot-logbook` can use it.
- `pilot-logbook` task `0008` — the consumer.
