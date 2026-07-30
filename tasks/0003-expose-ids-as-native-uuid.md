# Expose aggregate ids as `uuid.UUID`, not `str`

**Status:** done — implemented and passing (80 tests).

## Why

Every aggregate id crossed the boundary as a string:

```rust
#[getter]
fn id(&self) -> String {
    self.0.id.to_string()
}
```

Both sides of that conversion are UUIDs — `Uuid` in Rust, `uuid.UUID` in
Python — so the string was pure boundary friction. It was never a decision:
task `0001` fixed the mapping as `Uuid ↔ str` at a point when PyO3 had no
`uuid` support, and it was not revisited when the feature arrived. PyO3 0.29
ships `features = ["uuid"]`, converting `uuid::Uuid` to and from
`uuid.UUID` directly, and `uuid 1.24` was already a dependency here.

The cost of not revisiting it landed downstream. `pilot-logbook` models its
own aggregates (`LogbookFlight`, `MedicalCertificate`, `FlightAssessment`)
with Pydantic `UUID` fields, so adopting this package left it holding two
representations of the same identity — `flight.id` a `str`, the
`logbook_flight.flight_id` pointing at it a `UUID`. That produced three
logged bugs before anyone questioned the mapping (its task `0007`, "Known
follow-on issues"):

- `Path.joinpath(uuid_obj)` in `filesystem/logbook_query.py`, raising at
  runtime.
- `_resolve_fk`'s `isinstance(val, str)` FK-resolution check, correct for
  kernel ids and wrong for the repo's own.
- `get_flights_by_ids` typed `list[str]` but passed `UUID`s.

The alternative under consideration was for `pilot-logbook` to drop to `str`
ids throughout to match. That is the domain conforming to an infrastructure
detail, and it would have made `pilot_id` and `flight_id` interchangeable to
mypy across three aggregates that each carry both. Fixing the boundary was
cheaper (8 sites) and removes the mismatch rather than picking a side of it.

## What changed

- `Cargo.toml`: added `uuid` to the pyo3 features.
- The 8 id sites across `aircraft.rs`, `pilot.rs`, `flight.rs`, `fstd.rs`,
  `fstd_session.rs` — getters return `Uuid`; `id`, `aircraft_id` and
  `device_id` parameters take `Uuid`/`Option<Uuid>`.
- `convert.rs`: `parse_uuid` deleted. Only `parse_decimal` remains, and the
  module doc now explains that `Uuid` and `UtcDateTime` are handled by PyO3
  features rather than by hand.
- `icao_shared_kernel.pyi`: `str` → `UUID` on every id.
- Tests: `str(uuid4())` → `uuid4()` throughout.

## Compatibility

**On-disk and wire formats are unchanged.** `str(UUID)` and the old
stringified id are byte-identical, so any consumer serialising through
`str()` needs no migration — only the in-memory type differs.

`test_defaults_id_and_no_movement_times` previously asserted
`flight.id != "00000000-…"`. Against a `UUID` that comparison is vacuously
true, so it was tightened to `isinstance` plus `!= UUID(int=0)`.

## Acceptance criteria

- [x] Every id getter returns `uuid.UUID`; every id parameter accepts one.
- [x] `parse_uuid` removed; no hand-rolled UUID conversion remains.
- [x] Stubs updated.
- [x] A test pins the contract both ways — a `UUID` round-trips, and a
      UUID-shaped `str` raises `TypeError` rather than being coerced.
- [x] `make check` passes (clippy `-D warnings`, fmt, 80 pytest tests).

## Related

- Task `0001` — set the original `Uuid ↔ str` mapping this supersedes.
- `pilot-logbook` tasks `0007` and `0008` — the consumer whose id mismatch
  prompted this; both were blocked on deciding how to reconcile the two
  representations, and this removes the question.
- `INSTRUCTIONS.md` — records the general rule: prefer a PyO3 feature to a
  hand-rolled string conversion.
