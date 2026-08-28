"""Adapters that put molrs under molrec's conformance suite.

Two methods per module and no assertions. The conversions report what molrs
actually returns -- they never repair it. An adapter that quietly fixed up a
narrowed integer or a widened float would turn a red suite green while the
files on disk stayed wrong, which is the one failure mode this whole harness
exists to prevent.
"""

from __future__ import annotations

from typing import Any

import molrs
import numpy as np

import molrec

_NUMPY_TO_MOLREC = {
    "float16": "f16",
    "float32": "f32",
    "float64": "f64",
    "int8": "i8",
    "int16": "i16",
    "int32": "i32",
    "int64": "i64",
    "uint8": "u8",
    "uint16": "u16",
    "uint32": "u32",
    "uint64": "u64",
    "bool": "bool",
    "complex64": "c64",
    "complex128": "c128",
}


def _dtype_of(values: np.ndarray) -> str:
    if values.dtype.kind in ("U", "T", "O", "S"):
        return "string"
    return _NUMPY_TO_MOLREC[values.dtype.name]


def _to_frame(model: molrec.FrameModel) -> molrs.Frame:
    frame = molrs.Frame()
    for name, block in model.blocks.items():
        native = molrs.Block()
        if not block.columns:
            native.resize(block.count)
        for column, payload in block.columns.items():
            native.insert(column, payload.values)
        if block.structural_shape is not None:
            native.set_shape(list(block.structural_shape))
        frame[name] = native
    if model.box is not None:
        frame.box = molrs.Box(
            model.box.vectors,
            model.box.origin,
            None if model.box.boundary is None else np.array(model.box.boundary),
        )
    if model.meta:
        frame.meta = model.meta
    return frame


def _from_frame(frame: molrs.Frame | None) -> dict[str, Any] | None:
    if frame is None:
        return None

    blocks: dict[str, Any] = {}
    for name in frame.keys():  # noqa: SIM118 (molrs Frame has no __iter__)
        native = frame[name]
        columns = {}
        for column in native.keys():  # noqa: SIM118
            values = np.asarray(native.view(column))
            columns[column] = {
                "dtype": _dtype_of(values),
                "shape": tuple(values.shape),
                "values": values,
            }
        structural = native.structural_shape
        blocks[name] = {
            "count": native.nrows if native.nrows is not None else 0,
            "columns": columns,
            "structural_shape": tuple(structural) if structural is not None else None,
        }

    box = None
    if frame.box is not None:
        box = {
            "vectors": np.asarray(frame.box.h),
            "origin": np.asarray(frame.box.origin),
            "boundary": tuple(bool(flag) for flag in np.asarray(frame.box.pbc)),
        }

    raw_meta = dict(frame.meta) if frame.meta else {}
    meta = {
        key: (value.value if hasattr(value, "value") else value) for key, value in raw_meta.items()
    }
    return {"blocks": blocks, "box": box, "meta": meta}


class MolrsRecordAdapter(molrec.RecordAdapter):
    """The whole record -- the shape molrs actually emits."""

    backends = ("zarr",)

    def write(self, model: molrec.RecordModel, store) -> None:
        record = molrs.Record()
        record.meta = model.meta.model_dump(mode="json", exclude_none=True)
        if model.frame is not None:
            record.set_frame(_to_frame(model.frame))
        if model.system is not None:
            record.set_system(_to_frame(model.system))
        record.write(store.uri)

    def read(self, store) -> Any:
        record = molrs.Record.read(store.uri)
        return {
            "meta": dict(record.meta),
            "frame": _from_frame(record.frame),
            "system": _from_frame(record.system),
        }


class Molrs(molrec.Implementation):
    name = "molrs"
    version = "0.14.0"
    # No frame adapter: molrs has no public door for a bare frame at a store
    # root, and inventing one to satisfy a suite would test something nobody
    # ships. The frame cases run inside records instead.
    record = MolrsRecordAdapter()
