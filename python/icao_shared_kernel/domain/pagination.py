"""Pagination primitives shared across repository protocols.

Repository ``find_*`` methods return :class:`Page` and accept a query model
that inherits the pagination fields from :class:`_PageRequest` (``limit``
plus an opaque ``cursor``).

Pagination is **keyset**, not offset:

- Each repo documents a fixed sort tuple, ending in ``id`` as a tiebreaker.
- ``next_cursor`` encodes the sort key of the last returned record. The
  format is private to the implementation and must be treated as opaque
  by consumers.
- ``next_cursor is None`` means no further pages.

Keyset semantics are stable across concurrent writes — paging will not
skip or duplicate rows when other writers insert near the cursor — at the
cost of forward-only iteration (no random-access ``page=47`` jump).

Plain ``dataclasses``, not Pydantic — this crate has no runtime dependency
beyond PyO3 (see task 0001-python-support-plan.md); pulling in Pydantic
just for these two types would break that.
"""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """A keyset-paginated slice of a repository result set.

    ``items`` holds up to ``query.limit`` records in the repository's
    documented sort order. ``next_cursor`` is opaque to consumers — pass
    it back to the same ``find_*`` call to fetch the next page; ``None``
    means there are no more results.
    """

    items: list[T]
    next_cursor: str | None = None


@dataclass
class _PageRequest:
    """Shared pagination fields for repository query models.

    Concrete ``*Query`` models inherit from this and add typed filter
    fields. ``cursor`` is opaque; consumers do not construct or inspect
    it — they pass back whatever ``next_cursor`` the previous page returned.
    """

    limit: int = 100
    cursor: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
