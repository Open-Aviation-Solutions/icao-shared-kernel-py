# Give the remaining classes value equality

**Status:** done — implemented and passing (86 tests).

## Why

`Aircraft` and `FlightSimulationTrainingDevice` were declared
`#[pyclass(eq, …)]`; `Pilot`, `Flight`, `FstdSession` and `SignificantPoint`
were not. Nothing justified the split — **all six derive `PartialEq` in
`icao-shared-kernel-rs` already**, so the omission was in this crate's
`#[pyclass]` attributes alone, not in the domain.

The failure mode is quiet. Without `eq`, `==` does not raise; it falls back
to identity comparison and answers a different question. In `pilot-logbook`
a repository round-trip assertion silently became "is this the same object",
which is never true after a read, and the workaround was to compare field by
field:

```python
assert retrieved.id == saved.id
assert retrieved.display_name == saved.display_name
assert [licence.number for licence in retrieved.licences] == ["12345"]
```

That is three assertions that drift out of date as fields are added, in place
of one that cannot.

## What changed

`eq` added to the `#[pyclass]` attribute and `PartialEq` to the derive on:

- `Flight`
- `Pilot`
- `FstdSession`
- `SignificantPoint` (a complex enum; both variant payloads, `Waypoint` and
  `Coordinate`, were already comparable)

No Rust domain change was needed. No stub change either — `__eq__` is on
`object`, so the `.pyi` files were already accurate.

`FlightDuration` looked like a fifth gap in a quick scan but already had
`eq`, `ord` and `hash` spread across a multi-line attribute.

## Acceptance criteria

- [x] Every `#[pyclass]` whose domain type derives `PartialEq` declares `eq`.
- [x] Tests assert equality is **by value** for each type — a reconstructed
      instance with the same id equals the original.
- [x] Tests assert each field participates, so a future field added to the
      Rust struct without thought cannot silently drop out of comparison.
- [x] `make check` passes (clippy `-D warnings`, fmt, 86 pytest tests).

## Related

- `INSTRUCTIONS.md` — records the convention, so new classes opt in.
- `pilot-logbook` PR #2 — carries the field-by-field workaround this
  removes; it can be reverted to a plain `==` once this lands.
- Task `0003` — the same shape of problem (a boundary detail quietly pushed
  onto consumers), found the same way.
