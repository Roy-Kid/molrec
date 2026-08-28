"""L0-L2 models: Column, Block, Box, Frame, Meta, Record.

These models *are* the specification. The JSON Schema published for other
languages is generated from them, and the conformance suite compares against
them -- so a change here is a change to the contract.

Nothing in this module reads or writes anything. There is no container
library: no ``Frame`` you build a molecule with, no block algebra, no
compute. Storage lives in ``bindings/``.

The structural invariants are enforced as validators, which means a
deliberately malformed negative case has to be built with
``model_construct()`` to bypass them.
"""

from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from molrec.arrays import NDArray, arrays_equal

DType = Literal[
    "f16",
    "f32",
    "f64",
    "i8",
    "i16",
    "i32",
    "i64",
    "u8",
    "u16",
    "u32",
    "u64",
    "bool",
    "string",
    "c64",
    "c128",
]

#: The dtype set is closed and every numeric width is explicit. A tool that
#: cannot represent one natively must preserve it rather than silently narrow
#: it -- reading f32 back as f64 doubles the file and reading f64 back as f32
#: destroys data, and both are conformance failures.
#:
#: ``bytes`` is deliberately absent: it has no Zarr V3 specification, so a
#: contract that included it would not be portable.
DTYPES: tuple[DType, ...] = (
    "f16",
    "f32",
    "f64",
    "i8",
    "i16",
    "i32",
    "i64",
    "u8",
    "u16",
    "u32",
    "u64",
    "bool",
    "string",
    "c64",
    "c128",
)

#: The in-memory equivalent of each spec dtype.
NUMPY_DTYPE: dict[DType, str] = {
    "f16": "float16",
    "f32": "float32",
    "f64": "float64",
    "i8": "int8",
    "i16": "int16",
    "i32": "int32",
    "i64": "int64",
    "u8": "uint8",
    "u16": "uint16",
    "u32": "uint32",
    "u64": "uint64",
    "bool": "bool",
    "string": "str",
    "c64": "complex64",
    "c128": "complex128",
}

_FROM_NUMPY: dict[str, DType] = {
    numpy_name: spec_name for spec_name, numpy_name in NUMPY_DTYPE.items() if spec_name != "string"
}


def dtype_of(dtype: np.dtype) -> DType:
    """The spec dtype an in-memory array carries.

    UTF-8 strings reach us in more than one numpy spelling (``StringDType``,
    fixed-width ``<U``, object arrays), and all of them are one spec dtype.
    """
    if dtype.kind in ("U", "T", "O", "S"):
        return "string"
    if dtype.name not in _FROM_NUMPY:
        raise ValueError(
            f"dtype {dtype.name!r} is outside the closed molrec set {DTYPES}; "
            "preserve it rather than narrowing it, or declare a module for it"
        )
    return _FROM_NUMPY[dtype.name]


class ColumnModel(BaseModel):
    """A typed N-dimensional array.

    The leading axis length is the owning block's count; trailing axes are
    per-entity structure, so ``Float[count][3]`` is one column, not three.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    dtype: DType
    shape: tuple[int, ...] = Field(min_length=1)
    values: NDArray | None = None

    @model_validator(mode="after")
    def _values_match_declaration(self) -> ColumnModel:
        if self.values is None:
            return self
        if tuple(self.values.shape) != self.shape:
            raise ValueError(f"values have shape {self.values.shape}, declared {self.shape}")
        carried = dtype_of(self.values.dtype)
        if carried != self.dtype:
            raise ValueError(f"values carry dtype {carried!r}, declared {self.dtype!r}")
        return self

    @property
    def count(self) -> int:
        return self.shape[0]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ColumnModel):
            return NotImplemented
        if self.dtype != other.dtype or self.shape != other.shape:
            return False
        return arrays_equal(self.values, other.values)

    __hash__ = None  # type: ignore[assignment]


class BlockModel(BaseModel):
    """Named columns sharing one count, plus an optional structural shape.

    A plain table has implicit shape ``[count]``. A volumetric block declares
    ``structural_shape = (nx, ny, nz)`` with ``nx * ny * nz == count`` -- the
    only thing that makes a flat column reshapable after a roundtrip.

    A block imposes no meaning on its column names.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True, extra="allow")

    count: int = Field(ge=0)
    columns: dict[str, ColumnModel] = Field(default_factory=dict)
    structural_shape: tuple[int, ...] | None = None

    @model_validator(mode="after")
    def _columns_share_the_count(self) -> BlockModel:
        for name, column in self.columns.items():
            if column.count != self.count:
                raise ValueError(
                    f"column {name!r} has {column.count} rows, block count is {self.count}"
                )
        if self.structural_shape is not None:
            product = math.prod(self.structural_shape)
            if product != self.count:
                raise ValueError(
                    f"structural shape {self.structural_shape} has product {product}, "
                    f"block count is {self.count}"
                )
        return self


class BoxModel(BaseModel):
    """The triclinic cell. Columns of ``vectors`` are the lattice vectors.

    A box belongs to a frame, so fixed-cell and variable-cell runs are both
    natural -- each frame in a trajectory carries its own.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    vectors: NDArray
    origin: NDArray | None = None
    boundary: tuple[bool, ...] | None = None

    @model_validator(mode="after")
    def _square_and_filled_in(self) -> BoxModel:
        """Shape check, then materialize the defaults.

        Leaving ``origin`` and ``boundary`` absent looks harmless until two
        implementations disagree about what absent means -- one writes zeros
        and all-periodic, the other writes nothing, and a round trip that
        should be lossless reports a difference. So absence is resolved here,
        once: an unstated origin is the coordinate origin, and an unstated
        boundary is periodic on every axis.
        """
        shape = tuple(self.vectors.shape)
        if len(shape) != 2 or shape[0] != shape[1]:
            raise ValueError(f"vectors must be [ndim][ndim], found {shape}")
        ndim = shape[0]

        if self.origin is None:
            object.__setattr__(self, "origin", np.zeros(ndim, dtype="float64"))
        elif tuple(self.origin.shape) != (ndim,):
            raise ValueError(f"origin must be [{ndim}], found {tuple(self.origin.shape)}")

        if self.boundary is None:
            object.__setattr__(self, "boundary", (True,) * ndim)
        elif len(self.boundary) != ndim:
            raise ValueError(f"boundary must have {ndim} flags, found {len(self.boundary)}")
        return self

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BoxModel):
            return NotImplemented
        return (
            arrays_equal(self.vectors, other.vectors)
            and arrays_equal(self.origin, other.origin)
            and self.boundary == other.boundary
        )

    __hash__ = None  # type: ignore[assignment]


class FrameModel(BaseModel):
    """A map of names to blocks, plus free-form meta and an optional box.

    A frame enforces no relationship between blocks: block counts are
    independent and any block name is legal.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True, extra="allow")

    blocks: dict[str, BlockModel] = Field(default_factory=dict)
    box: BoxModel | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class MetaModel(BaseModel):
    """The record's identity document.

    ``extra="allow"`` is not convenience -- it is the preserve-the-unknown
    invariant: a reader must keep keys it does not recognize.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True, extra="allow")

    record_schema_version: int = Field(ge=1)
    format_name: Literal["molrec"] | None = None
    record_id: str | None = None
    content_hash: str | None = None


class RecordModel(BaseModel):
    """The record root.

    ``meta`` is always required, plus at least one substantive section. The
    other sections arrive with their own modules; this module owns ``frame``
    and ``system``.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True, extra="allow")

    meta: MetaModel
    frame: FrameModel | None = None
    system: FrameModel | None = None

    @model_validator(mode="after")
    def _has_a_section(self) -> RecordModel:
        if self.frame is None and self.system is None:
            raise ValueError("a record needs at least one of frame, system")
        return self
