"""Output formatting for the Morpheus CLI.

Two modes: human-readable (default) and JSON (``--json`` flag). Each command
calls ``emit`` with a Python value; the global ``output_mode`` determines
how it gets rendered to stdout.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any
from uuid import UUID


# Set by the root click group based on the --json flag.
_json_mode: bool = False


def set_json_mode(enabled: bool) -> None:
    global _json_mode
    _json_mode = enabled


def is_json_mode() -> bool:
    return _json_mode


def _default(obj: Any) -> Any:
    """JSON encoder for types graphiti uses (UUID, datetime, pydantic)."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, 'model_dump'):
        return obj.model_dump(mode='json')
    raise TypeError(f'cannot serialize {type(obj).__name__}')


def emit_json(value: Any) -> None:
    json.dump(value, sys.stdout, default=_default, indent=2, sort_keys=False)
    sys.stdout.write('\n')


def emit(value: Any, *, human: str | None = None) -> None:
    """Emit a result. JSON mode → JSON; human mode → ``human`` if provided
    else a fallback string representation."""
    if _json_mode:
        emit_json(value)
        return
    if human is not None:
        sys.stdout.write(human)
        if not human.endswith('\n'):
            sys.stdout.write('\n')
        return
    # Fallback: pretty-print as JSON in human mode if no explicit string given.
    emit_json(value)
