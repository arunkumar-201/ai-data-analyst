"""JSON response helpers for data that may contain non-finite numbers."""
import math
from collections.abc import Mapping
from numbers import Real
from typing import Any

from fastapi.responses import JSONResponse


def sanitize_json_value(value: Any) -> Any:
    """Replace NaN and infinity with JSON-compatible null values."""
    if isinstance(value, Real) and not isinstance(value, bool):
        return value if math.isfinite(float(value)) else None
    if isinstance(value, Mapping):
        return {key: sanitize_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_json_value(item) for item in value]
    return value


class SafeJSONResponse(JSONResponse):
    """JSONResponse that never emits non-compliant float values."""

    def render(self, content: Any) -> bytes:
        return super().render(sanitize_json_value(content))