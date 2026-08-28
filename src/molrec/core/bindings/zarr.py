"""The Zarr V3 binding for the core module.

Layout::

    <frame root>/               group attributes = the frame's meta document
    ├── <block>/                group attributes: count, structural_shape
    │   └── <column>            array
    └── box/
        ├── vectors             array
        ├── origin              array (optional)
        └──                     group attributes: boundary

Blocks are flat children of the frame group. The frame's meta document is the
group's attribute map rather than a child, so ``box`` is the only reserved
name in that namespace -- a block may be called ``meta``, ``atoms``,
``values`` or anything else. A block named ``box`` is refused at write time
rather than silently overwriting the cell.

Two things are stored that a naive writer would think are derivable, and are
not:

* ``count`` -- a block with no columns still has one.
* ``structural_shape`` -- without it a volumetric column reads back flat and
  can never be reshaped. That is data loss, not an inconvenience.

The dtype mapping is exact and total in both directions, with every numeric
width explicit. Nothing molrec-specific is stashed in attributes to recover
it: an implementation that writes the mapped Zarr dtype is readable by anyone
who has read the spec, which is the entire point of a binding.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import ClassVar

import numpy as np
import zarr

from molrec.binding import Binding, Codec
from molrec.chunking import plan
from molrec.core.model import (
    NUMPY_DTYPE,
    BlockModel,
    BoxModel,
    ColumnModel,
    DType,
    FrameModel,
    MetaModel,
    RecordModel,
    dtype_of,
)
from molrec.core.store import FrameStore, RecordStore
from molrec.registry import REGISTRY

BOX_GROUP = "box"

#: molrec dtype -> the Zarr V3 dtype a conforming writer emits.
TO_ZARR: dict[DType, str] = {**NUMPY_DTYPE, "string": "string"}


def _itemsize(dtype: DType) -> int | None:
    """Bytes per element, or ``None`` for a variable-width dtype."""
    if dtype == "string":
        return None
    return np.dtype(NUMPY_DTYPE[dtype]).itemsize


class ZarrFrameStore(FrameStore):
    """A Zarr V3 root holding one frame."""

    backend: ClassVar[str] = "zarr"

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def uri(self) -> str:
        """For bindings that take a path -- PyO3, the C ABI, a CLI."""
        return str(self._path)

    @property
    def path(self) -> Path:
        return self._path

    def root(self, mode: str = "a") -> zarr.Group:
        """For consumers already speaking zarr-python."""
        return zarr.open_group(store=self._path, mode=mode)

    def clear(self) -> None:
        if self._path.exists():
            shutil.rmtree(self._path)


class ZarrFrameCodec(Codec):
    """The official translation. Kept thin -- it is the arbiter."""

    def write(self, model: FrameModel, store: ZarrFrameStore) -> None:
        store.clear()
        self.write_into(store.root(mode="w"), model)

    def read(self, store: ZarrFrameStore) -> FrameModel:
        return self.read_from(store.root(mode="r"))

    def write_into(self, root: zarr.Group, model: FrameModel) -> None:
        """Lay a frame out under an already-opened group.

        Split out so the record codec reuses it: a frame section inside a
        record and a bare frame at a store root are the same bytes, and one
        description of that is better than two that can drift.
        """
        root.attrs.update(model.meta)

        for name, block in model.blocks.items():
            if name == BOX_GROUP:
                raise ValueError(
                    f"{BOX_GROUP!r} names the cell in a frame group; a block cannot take it"
                )
            self._write_block(root, name, block)

        if model.box is not None:
            self._write_box(root, model.box)

    def read_from(self, root: zarr.Group) -> FrameModel:
        blocks = {
            name: self._read_block(member)
            for name, member in root.members()
            if isinstance(member, zarr.Group) and name != BOX_GROUP
        }

        box = self._read_box(root[BOX_GROUP]) if BOX_GROUP in root else None
        return FrameModel(blocks=blocks, box=box, meta=dict(root.attrs))

    def _write_block(self, parent: zarr.Group, name: str, block: BlockModel) -> None:
        group = parent.create_group(name)
        group.attrs["count"] = block.count
        if block.structural_shape is not None:
            group.attrs["structural_shape"] = list(block.structural_shape)

        for column_name, column in block.columns.items():
            self._write_column(group, column_name, column)

    def _write_column(self, group: zarr.Group, name: str, column: ColumnModel) -> None:
        chunks, shards = plan(column.shape, _itemsize(column.dtype))
        options: dict = {}
        if chunks is not None:
            options["chunks"] = chunks
        if shards is not None:
            options["shards"] = shards

        array = group.create_array(name, shape=column.shape, dtype=TO_ZARR[column.dtype], **options)
        if column.values is not None:
            array[...] = column.values

    def _read_block(self, group: zarr.Group) -> BlockModel:
        attrs = dict(group.attrs)
        if "count" not in attrs:
            raise ValueError(f"block {group.name!r} has no count attribute")

        columns = {
            name: self._read_column(member)
            for name, member in group.members()
            if isinstance(member, zarr.Array)
        }
        structural = attrs.get("structural_shape")
        return BlockModel(
            count=int(attrs["count"]),
            columns=columns,
            structural_shape=tuple(structural) if structural is not None else None,
        )

    def _read_column(self, array: zarr.Array) -> ColumnModel:
        return ColumnModel(
            dtype=dtype_of(np.dtype(array.dtype)),
            shape=tuple(int(n) for n in array.shape),
            values=array[...],
        )

    def _write_box(self, root: zarr.Group, box: BoxModel) -> None:
        group = root.create_group(BOX_GROUP)
        vectors = group.create_array("vectors", shape=box.vectors.shape, dtype="float64")
        vectors[...] = box.vectors
        if box.origin is not None:
            origin = group.create_array("origin", shape=box.origin.shape, dtype="float64")
            origin[...] = box.origin
        if box.boundary is not None:
            group.attrs["boundary"] = list(box.boundary)

    def _read_box(self, group: zarr.Group) -> BoxModel:
        boundary = group.attrs.get("boundary")
        origin = group["origin"][...] if "origin" in group else None
        return BoxModel(
            vectors=group["vectors"][...],
            origin=origin,
            boundary=tuple(bool(flag) for flag in boundary) if boundary is not None else None,
        )


@REGISTRY.binding
class ZarrFrameBinding(Binding):
    module: ClassVar[str] = "core"
    backend: ClassVar[str] = "zarr"

    def new_store(self, workdir: Path) -> ZarrFrameStore:
        store = ZarrFrameStore(workdir.with_suffix(".zarr"))
        store.clear()
        return store

    def codec(self) -> ZarrFrameCodec:
        return ZarrFrameCodec()


RECORD_META = "meta"
RECORD_FRAME = "frame"
RECORD_SYSTEM = "system"


class ZarrRecordStore(RecordStore):
    """A Zarr V3 root holding a whole record.

    This is the shape a real producer writes. A bare frame at a store root is
    a useful unit to pin down on its own, but nothing ships one -- an
    implementation writes a record, and the frame is a section inside it.
    """

    backend: ClassVar[str] = "zarr"

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def uri(self) -> str:
        return str(self._path)

    @property
    def path(self) -> Path:
        return self._path

    def root(self, mode: str = "a") -> zarr.Group:
        return zarr.open_group(store=self._path, mode=mode)

    def clear(self) -> None:
        if self._path.exists():
            shutil.rmtree(self._path)


class ZarrRecordCodec(Codec):
    """The official record translation.

    Document sections are group attribute maps, not child arrays -- ``meta``
    is a JSON document and Zarr already has a place for those. Frame-shaped
    sections delegate to the frame codec, so there is exactly one description
    of how blocks are laid out.
    """

    def __init__(self) -> None:
        self._frames = ZarrFrameCodec()

    def write(self, model: RecordModel, store: ZarrRecordStore) -> None:
        store.clear()
        root = store.root(mode="w")
        root.create_group(RECORD_META).attrs.update(
            model.meta.model_dump(mode="json", exclude_none=True)
        )
        for name, frame in (
            (RECORD_FRAME, model.frame),
            (RECORD_SYSTEM, model.system),
        ):
            if frame is not None:
                self._frames.write_into(root.create_group(name), frame)

    def read(self, store: ZarrRecordStore) -> RecordModel:
        root = store.root(mode="r")
        return RecordModel(
            meta=MetaModel.model_validate(dict(root[RECORD_META].attrs)),
            frame=self._section(root, RECORD_FRAME),
            system=self._section(root, RECORD_SYSTEM),
        )

    def _section(self, root: zarr.Group, name: str) -> FrameModel | None:
        if name not in root:
            return None
        return self._frames.read_from(root[name])


@REGISTRY.binding
class ZarrRecordBinding(Binding):
    module: ClassVar[str] = "record"
    backend: ClassVar[str] = "zarr"

    def new_store(self, workdir: Path) -> ZarrRecordStore:
        store = ZarrRecordStore(workdir.with_suffix(".zarr"))
        store.clear()
        return store

    def codec(self) -> ZarrRecordCodec:
        return ZarrRecordCodec()
