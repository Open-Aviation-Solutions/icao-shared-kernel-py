"""Shared base for filesystem-backed repository implementations.

PyO3 classes have no ``.model_dump()``/``.model_validate()`` (unlike the
Pydantic models this replaces), so each repository passes the aggregate's
``to_dict``/``from_dict`` pair from ``infrastructure._codec`` explicitly
rather than this base class knowing about a model class.
"""

import json
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")


class _FilesystemRepository:
    """Base class providing shared read/write/delete helpers for filesystem repos."""

    def __init__(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self._dir = directory

    def _path(self, *parts: str) -> Path:
        """Build a .json file path relative to this repository's directory."""
        return self._dir.joinpath(*parts).with_suffix(".json")

    def _write(self, path: Path, obj: T, to_dict: Callable[[T], dict]) -> None:
        """Serialise an aggregate to JSON and write it to path, creating parent dirs."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(to_dict(obj)), encoding="utf-8")

    def _read(self, path: Path, from_dict: Callable[[dict], T]) -> T | None:
        """Read and deserialise an aggregate from path, returning None if not found."""
        if not path.exists():
            return None
        return from_dict(json.loads(path.read_text(encoding="utf-8")))

    def _delete(self, path: Path) -> bool:
        """Delete the file at path. Returns True if deleted, False if not found."""
        if not path.exists():
            return False
        path.unlink()
        return True
