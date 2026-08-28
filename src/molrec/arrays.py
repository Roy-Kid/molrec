"""NumPy arrays as pydantic fields.

Column values are ndarrays, but a model that holds one must still validate,
serialize to JSON, and export a JSON Schema -- the schema files are the
language-neutral artifact, so a field that breaks ``model_json_schema()``
breaks the whole publishing story.

The array is carried by reference (never copied); JSON serialization renders
it as nested lists.
"""

from __future__ import annotations

from typing import Annotated, Any

import numpy as np
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


def _validate(value: Any) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return value
    if value is None:
        raise ValueError("array value must not be None")
    return np.asarray(value)


def _serialize(value: np.ndarray) -> list:
    return value.tolist()


class _NDArrayAnnotation:
    """Teaches pydantic how to validate, serialize, and describe an ndarray."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            _validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize,
                return_schema=core_schema.any_schema(),
                when_used="json",
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Nested lists of unspecified depth -- the dtype and shape live in
        # sibling fields, which is where a reader should look.
        return {"type": "array", "items": {}}


NDArray = Annotated[np.ndarray, _NDArrayAnnotation]


def arrays_equal(left: np.ndarray | None, right: np.ndarray | None) -> bool:
    """Value equality for column payloads.

    ``==`` on ndarrays yields an array, so every model holding one needs this
    instead of pydantic's default field comparison. NaN compares equal to NaN:
    a roundtrip that preserves a NaN has preserved it.
    """
    if left is None or right is None:
        return left is None and right is None
    if left.shape != right.shape:
        return False
    if left.dtype.kind in "fc" and right.dtype.kind in "fc":
        return bool(np.allclose(left, right, rtol=0, atol=0, equal_nan=True))
    return bool(np.array_equal(left, right))
