"""Internal cursor encoding helpers shared by repository adapters.

Cursors are opaque to consumers; this module's encoded shape is private
to the infrastructure layer and must not be relied upon by downstream
packages.
"""

import base64
import binascii
import json
from typing import Any


def encode_cursor(payload: dict[str, Any]) -> str:
    """Serialise the keyset payload to an opaque, URL-safe string."""
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Parse an opaque cursor back into the keyset payload."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        loaded = json.loads(raw.decode("utf-8"))
    except (binascii.Error, ValueError) as exc:
        raise ValueError("invalid cursor") from exc
    if not isinstance(loaded, dict):
        raise ValueError("invalid cursor")
    return loaded
