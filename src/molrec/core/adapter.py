"""Adapter bases for the core module."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, ClassVar

from molrec.adapter import Adapter
from molrec.core.model import FrameModel, RecordModel
from molrec.core.store import FrameStore, RecordStore


class FrameAdapter(Adapter):
    """Implement this to have your frame serialization judged.

        class MolrsFrameAdapter(molrec.FrameAdapter):
            backends = ("zarr",)

            def write(self, model, store):
                molrs.write_frame(self._build(model), store.uri)

            def read(self, store):
                return self._describe(molrs.read_frame(store.uri))

    ``read`` may return any duck shaped like ``FrameModel``.
    """

    module: ClassVar[str] = "core"

    @abstractmethod
    def write(self, model: FrameModel, store: FrameStore) -> None: ...

    @abstractmethod
    def read(self, store: FrameStore) -> Any: ...


class RecordAdapter(Adapter):
    """Same contract, one level up: the whole record root."""

    module: ClassVar[str] = "record"

    @abstractmethod
    def write(self, model: RecordModel, store: RecordStore) -> None: ...

    @abstractmethod
    def read(self, store: RecordStore) -> Any: ...
