# Repository protocols and infra belong in consuming apps, not here

**Status:** done

## Intent

This crate stays domain bindings only. Repository protocols
(`typing.Protocol` per aggregate), filesystem/Postgres adapters, and
admin views were built here in an earlier version of this task and then
removed: their shape (async, cursor pagination, starlette-admin, the
verb set) is `pilot-logbook`'s web-application shape, not something
intrinsic to "Python bindings for this domain." A different consumer
could reasonably want something else entirely. Each consuming
application owns its own repository protocol, the same way
`pilot-logbook` already owns `LogbookRepository` for its own aggregates —
`Aircraft`/`Pilot`/`Flight` don't need different treatment just because
they happen to be defined in a shared kernel.

The one thing from that removed work worth keeping: `Aircraft` and
`Flight` now accept an explicit `id: str | None = None` on construction
(matching `Pilot`'s existing pattern), backed by `Aircraft::with`/
`Flight::with` in `icao-shared-kernel-rs`. Any consumer reconstructing a
persisted instance needs this regardless of where its repository lives —
without it, `get_by_id` would silently return an object with a different
id than the one requested.

A trait-free serialisation helper (mirroring
`icao-shared-kernel-rs/tasks/0001-domain-serialisation-not-a-repository-trait.md`)
is still an open, YAGNI-gated question here too — not built, no consumer
has asked for it yet.

## Where the removed code went

Moved to `pilot-logbook` (see its own tasks) where it's actually used, to
the extent it's actually needed there.

## Acceptance criteria

- [x] `Aircraft`/`Flight` accept `id: str | None = None`.
- [x] No repository protocol, filesystem/Postgres adapter, or admin view
      in this crate.
