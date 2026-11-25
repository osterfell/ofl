"""The filter language of `ofl search`.

    vram>=80 region=eu gpus=4 price<1.2 gpu=a100

Terms are separated by spaces and all have to hold. A value with spaces can
be quoted: gpu="rtx 4090".
"""

from __future__ import annotations

import re
import shlex
from typing import Any

FIELDS = {
    "gpu": str,
    "gpus": int,
    "vram": int,
    "vcpu": int,
    "ram": int,
    "disk": int,
    "price": float,
    "region": str,
    "uptime": float,
    "interruptible": bool,
}
OPERATORS = {">=": "gte", "<=": "lte", "!=": "ne", ">": "gt", "<": "lt", "=": "eq"}
_TERM = re.compile(r"^([a-z_]+)\s*(>=|<=|!=|>|<|=)\s*(.+)$")


class QueryError(ValueError):
    pass


def _value(field: str, text: str) -> Any:
    kind = FIELDS[field]
    if kind is bool:
        if text.lower() in ("true", "yes", "1"):
            return True
        if text.lower() in ("false", "no", "0"):
            return False
        raise QueryError(f"{field}: expected true or false, got {text!r}")
    try:
        return kind(text)
    except ValueError:
        raise QueryError(f"{field}: expected a {kind.__name__}, got {text!r}") from None


def parse(query: str) -> dict[str, dict[str, Any]]:
    """Turn a query string into the filter object the API takes:
    {"vram": {"gte": 80}, "region": {"eq": "eu"}}."""
    filters: dict[str, dict[str, Any]] = {}
    for term in shlex.split(query):
        match = _TERM.match(term)
        if not match:
            raise QueryError(f"cannot read {term!r}: expected field, operator, value")
        field, operator, text = match.groups()
        if field not in FIELDS:
            raise QueryError(f"unknown field {field!r} (known: {', '.join(sorted(FIELDS))})")
        if FIELDS[field] in (str, bool) and operator not in ("=", "!="):
            raise QueryError(f"{field} only supports = and !=")
        filters.setdefault(field, {})[OPERATORS[operator]] = _value(field, text)
    return filters
