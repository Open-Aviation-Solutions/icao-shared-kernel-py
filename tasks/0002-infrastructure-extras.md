# Bring repository protocols, filesystem, and admin adapters into icao-shared-kernel-py

**Status:** ready

## Purpose

`icao-shared-kernel-py` (task `0001-python-support-plan.md`) covers the pure
domain only — value objects and aggregates, PyO3 bindings over
`icao-shared-kernel-rs`. Everything else the current Pydantic-based
`icao-shared-kernel` package ships — repository *protocols*
(`domain/repositories/*.py`) and their concrete adapters
(`infrastructure/{filesystem,postgres,admin}/`) — is pure Python with no
Rust equivalent, and none was planned (task 0014 excluded it deliberately).

`pilot-logbook`'s investigation into adopting this package
(`pilot-logbook/tasks/0006-investigate-icao-shared-kernel-py.md`) flagged
this as a structural gap: `pilot-logbook` depends on the infra layer at
least as heavily as the domain layer, and a "two-package forever" split
(Rust bindings for domain, old Pydantic package for everything else)
contradicts `0001`'s decision that this crate is the **sole** eventual
implementation. Since the infra code is pure Python already, there's no
reason it can't live here instead.

**This task's scope is repository protocols + filesystem adapters +
admin adapters**, for all three aggregates (`Aircraft`, `Pilot`, `Flight`).
**Postgres is out of scope** — see [Deferred](#deferred-postgres) below for
why and what's still open there.

## Decisions

### D1. Extras: `[admin]` added now, `[postgres]` deferred

Python's `[project.optional-dependencies]` is the extras mechanism
(equivalent to Cargo features in spirit, though weaker: it gates a
dependency being installed, not code being compiled out — the extra's
*code* always ships in the wheel; an unmet optional dependency has to be
handled by the code itself, e.g. a lazy/guarded import). The current
`icao-shared-kernel` package already uses this for `[postgres]` and
`[admin]`; filesystem ships in core (no third-party deps).

**Decision:** reuse the existing extras names. This task adds:

```toml
[project.optional-dependencies]
admin = ["sqlalchemy>=2.0", "starlette-admin>=0.16.0", "fastapi>=0.135.1", "uvicorn>=0.41.0"]
```

`[postgres]` is not added yet — deferred with the rest of that work (see
below). Filesystem needs no extra — it ships in core, same as today.

### D2. Mixed maturin layout, compiled extension renamed to `_icao_shared_kernel`

`icao-shared-kernel-py` is currently a maturin **pure-Rust** project — the
whole Python-visible surface is the compiled extension module, and
`icao_shared_kernel.pyi` at the repo root is auto-detected as its stub.
Pure-Python code (repository protocols, filesystem/admin adapters) can't
live inside a compiled extension module, so this requires switching to
maturin's **mixed layout** (`python/icao_shared_kernel/` alongside `src/`),
where a pure-Python package wraps and re-exports the compiled extension as
a submodule. This is a well-trodden pattern (`pydantic-core`,
`cryptography`, others use it) — mechanical, roughly half a day:

- Add `python-source = "python"` to `[tool.maturin]` in `pyproject.toml`.
- Create `python/icao_shared_kernel/__init__.py` re-exporting everything
  from the compiled submodule (`from ._icao_shared_kernel import *` plus
  an explicit `__all__`).
- Rename the compiled extension from the top-level module
  (`[lib] name = "icao_shared_kernel"` in `Cargo.toml`) to a submodule,
  **`_icao_shared_kernel`** — chosen over `_core`/`_native` because it's
  private either way (underscore-prefixed, not part of the public API
  surface), so the more descriptive name costs nothing.
- Move `icao_shared_kernel.pyi` into `python/icao_shared_kernel/__init__.pyi`
  (single combined stub, not split) — maturin auto-detects it there.
- `make dev` / `make check` keep working unchanged (still one
  `maturin develop` call). The existing 63 tests need no changes beyond
  confirming `import icao_shared_kernel` still resolves the same public
  names.

### D3. Repository protocols: retype against PyO3 classes and `str` ids

`AircraftRepository`, `PilotRepository`, `FlightRepository`
(`typing.Protocol`) plus their `*Query`/`Page`/`_PageRequest` pagination
types port with no third-party dependencies, retyped against the PyO3
classes and the `str`-based `Uuid`/`Decimal` boundary from task 0001 (ids
are `str`, not `UUID`, on both the protocol signatures and the query
filter fields — this also simplifies the admin views, see below).

### D4. `FlightQuery`: minimal — id-only sort, `aircraft_id` filter only

`Flight`'s shape moved (`departure`/`arrival: SignificantPoint`,
`first_movement`/`last_movement: datetime | None`, no more `flight_date`/
`start_waypoint`/`end_waypoint`), so the old `FlightQuery`'s
`(flight_date DESC, id DESC)` sort and date/waypoint filters have no
direct replacement.

**Decision (YAGNI):** don't design a `first_movement`-based sort/filter
scheme now — no real consumer has asked for Flight date-range filtering
yet (`pilot-logbook` is itself blocked/stale, per task 0006). Match
`Aircraft`/`Pilot`'s existing `(id ASC)` sort, keep the `aircraft_id`
filter (still valid — `aircraft_id: str` on the new shape), drop
`flight_date_from/to`, `start_waypoint`, `end_waypoint`. Revisit with a
real design (sort tuple, `NULLS LAST` handling for optional
`first_movement`) when an actual consumer needs Flight-scoped filtering.

### D5. Sequencing: protocols → filesystem → admin, all three aggregates, in this task

Filesystem has the fewest moving parts (no serialisation library, no
schema/migration questions, no form validation) — the natural first slice,
and `admin/app.py`'s `make_admin_app()` wires the filesystem repos in
directly, so filesystem has to land first regardless. Both layers, for all
three aggregates, are in scope for this task. Postgres is a separate,
later task — see below.

## Filesystem adapter rewrite, concretely

Read against the actual `icao-shared-kernel` implementations
(`infrastructure/filesystem/{_base,flight}.py`) to scope this precisely
rather than estimate blind:

- `_base.py`'s `_write`/`_read` are one-line Pydantic calls
  (`model.model_dump_json()` / `model_cls.model_validate_json(...)`).
  PyO3 classes have neither, so each aggregate needs a hand-written
  `to_dict(obj) -> dict` / `from_dict(data: dict) -> T` pair built from
  PyO3 getters and the constructor. Bounded — roughly 20–40 lines per
  aggregate depending on nesting:
  - `Aircraft`: flat (`aircraft_type.designator`, `registration.nationality`/`.registration`).
  - `Pilot`: one list field (`licences: list[Licence]`) — iterate and
    serialise each.
  - `Flight`: `departure`/`arrival: SignificantPoint` is a tagged
    union (`Designator` vs `Coordinate` variant) — needs an
    `isinstance` check both directions; `first_movement`/`last_movement`
    are `datetime | None`, straightforward `isoformat()`/`fromisoformat()`.
- `_matches`/filter logic in `flight.py` (lines 63–101) filters on
  `aircraft_id`, `flight_date_from/to`, `start_waypoint`, `end_waypoint` —
  per D4, only the `aircraft_id` filter carries over; the rest is dropped,
  not ported.
- `_FilesystemRepository` base class itself (directory handling, `_path`,
  `_delete`) is unchanged — none of it is Pydantic-specific.

These `to_dict`/`from_dict` pairs are written once per aggregate and
**reused directly by the admin layer below** (`serialize_field_value`
needs the same dict shape for `JSONField`s) — do filesystem first partly
because admin depends on this output.

## Admin adapter rewrite, concretely

Read against `infrastructure/admin/{_base,app,aircraft}.py`. The rewrite
is smaller than an earlier draft of this task suggested — that draft
overstated it as "genuinely bespoke"; see the corrected picture below.

**Form validation (`create`/`edit` in each view).** Pydantic's
`Aircraft.model_validate(data)` validates every field in one call and
returns them all via `.errors()`; PyO3 constructors are fail-fast (first
bad argument raises, no batching). But all 8 domain exceptions already
share one common base (`ValidationError` — see `icao_shared_kernel.pyi`),
so a single generic helper, written once in a shared admin base module and
reused by all three views, recovers the same behaviour:

```python
def _build_or_collect(fields: dict[str, Callable[[], object]]) -> tuple[dict, dict[str, str]]:
    values, errors = {}, {}
    for name, construct in fields.items():
        try:
            values[name] = construct()
        except ValidationError as exc:
            errors[name] = str(exc)
    return values, errors
```

Try each sub-value-object constructor individually (`Waypoint(...)`,
`AircraftType(...)`, ...), catch the shared base, collect a
`{field: message}` dict — exactly what `FormValidationError` already
wants. The one genuine wrinkle is list fields (`Pilot.licences`), which
need indexed keys (`licences[0]`) rather than a flat field name — a small
addition to the same helper, not a different approach.

**`_base.py`'s `serialize_field_value`** currently does
`isinstance(value, BaseModel)` → `.model_dump(mode="json")` for
`JSONField`s. Replace with a call into the same `to_dict` helper written
for filesystem (per the aggregate type) — no new serialisation logic
needed here, just routing to the existing one.

**FK/id handling gets *simpler*, not harder.** `_base.py`'s `_resolve_fk`
and every view's `find_by_pk`/`delete` currently wrap `pk` in
`UUID(str(pk))` before calling the repository. Since ids are `str` end to
end now (task 0001's boundary decision), that wrapping is just dropped —
`str(pk)` directly, no `UUID(...)` parsing/validation step at all.

**`app.py`'s `make_admin_app()`** wiring (mounting the three views + their
filesystem repos into a FastAPI app via starlette-admin) is structurally
unchanged — it just imports the rewritten views and repos.

**No existing tests to adapt.** `icao-shared-kernel` has no
`tests/infrastructure/admin/` at all — there's no baseline to port, so
this task should add at least: one test per aggregate for
`_build_or_collect` (valid input, and one invalid field producing the
expected `{field: message}`), and one create/edit round-trip per view
using starlette's test client, since this is new coverage rather than
adapted coverage.

## Deferred: Postgres

Not building this now; flagging what's known so a future task doesn't
start from zero. Same `to_dict`/`from_dict` need as filesystem/admin
(`postgres/base.py`'s `to_jsonb`/`from_jsonb` are the same one-line
Pydantic calls — directly reusable once written), plus a schema question
independent of the PyO3 swap: the `flights` table's promoted `flight_date`
column and its JSONB-path filter clauses reference fields that no longer
exist on `Flight`. Needs a real migration once D4's query design is
revisited. `[postgres]` extra to be added when this lands.

## Relationship to other tasks

- Once protocols + filesystem + admin land here, resolves the filesystem/
  admin portion of the "no infra equivalent" blocker noted in
  `pilot-logbook/tasks/0006-investigate-icao-shared-kernel-py.md` — but
  not that task's independent blocker (CASA-enum removal blocked on the
  not-yet-existing `au-casa` package), and not Postgres (deferred above).
- Both packages already install under the same PyPI/distribution name
  (`icao-shared-kernel`) — consistent with task `0001`'s "sole
  implementation" decision; this package is meant to fully replace the
  Pydantic one eventually, not sit alongside it.

## Acceptance criteria

- [ ] Mixed maturin layout adopted: `python-source = "python"`,
      `python/icao_shared_kernel/__init__.py` re-exporting the compiled
      submodule (renamed `_icao_shared_kernel`), stub moved to
      `python/icao_shared_kernel/__init__.pyi`. `make dev`/`make check`
      pass; existing 63 tests pass unchanged against the new layout.
- [ ] Repository protocols added: `AircraftRepository`, `PilotRepository`,
      `FlightRepository` (`Protocol`), `AircraftQuery`, `PilotQuery`,
      `FlightQuery`, `Page`, `_PageRequest` — ids typed `str`, matching the
      PyO3 boundary.
- [ ] `FlightQuery`: `(id ASC)` sort, `aircraft_id` filter only (per D4).
- [ ] `FilesystemAircraftRepository`, `FilesystemPilotRepository`,
      `FilesystemFlightRepository` implemented, each with a `to_dict`/
      `from_dict` pair per the concrete breakdown above.
- [ ] Filesystem tests adapted from `icao-shared-kernel`'s
      `tests/infrastructure/filesystem/test_pagination.py` (keyset
      pagination smoke tests across all three repos), updated for the new
      `Flight` shape and `FlightQuery`'s reduced filter set.
- [ ] `[admin]` extra added to `pyproject.toml` (per D1).
- [ ] Shared `_build_or_collect` validation helper added (admin base
      module), used by all three admin views' `create`/`edit`.
- [ ] `AircraftAdminView`, `PilotAdminView`, `FlightAdminView`, and
      `make_admin_app()` ported — `UUID(...)` id parsing dropped in favour
      of plain `str`, `serialize_field_value` routed through the
      `to_dict` helpers.
- [ ] New admin tests added per aggregate (validation helper + one
      create/edit round-trip), since there's no existing baseline.
- [ ] `INSTRUCTIONS.md` updated to document the mixed layout, the
      filesystem adapter pattern (`to_dict`/`from_dict`), and the admin
      validation helper.

## Notes for the implementer

- Do the mixed-layout migration (D2) first, as its own commit, before any
  infra code lands — verify `maturin develop` and all existing tests pass
  against the new layout in isolation, so a later regression is
  attributable to the infra code, not the layout change.
- `SignificantPoint`'s tagged-union serialisation
  (`isinstance(point, SignificantPoint.Designator)` /
  `SignificantPoint.Coordinate`) is worth writing as one shared helper up
  front — used by `Flight`'s `to_dict`/`from_dict` and needed again by
  admin's `serialize_field_value` and (later) Postgres.
- Write filesystem's `to_dict`/`from_dict` pairs with admin's reuse in
  mind (D5) — same function, not a parallel implementation.
