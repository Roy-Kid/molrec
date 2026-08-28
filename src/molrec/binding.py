"""Binding -- one (module x backend) pair.

L4 is no longer "the Zarr binding". Every module can land in more than one
backend (frames in Zarr or HDF5; metrics in JSONL, Zarr, or SQLite; datasets
in Parquet or DuckDB), so a binding is the unit that owns:

* how to mint a :class:`~molrec.store.Store` for that pair, and
* the official codec -- the arbiter that turns a model into bytes and back.

Adding a backend means adding one binding module. No model changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from molrec.store import Store


class Codec(ABC):
    """The official model <-> store translation for one binding.

    This is the arbiter every conformance comparison runs through, which is
    why it must stay thin enough to read end to end. Convenience methods do
    not belong here.
    """

    @abstractmethod
    def write(self, model: BaseModel, store: Store) -> None: ...

    @abstractmethod
    def read(self, store: Store) -> BaseModel: ...


class Binding(ABC):
    """Ties a module to a backend."""

    module: ClassVar[str]
    backend: ClassVar[str]

    @abstractmethod
    def new_store(self, workdir: Path) -> Store:
        """Mint an empty store. ``workdir`` is suite-owned scratch space."""

    @abstractmethod
    def codec(self) -> Codec: ...

    @property
    def key(self) -> tuple[str, str]:
        return (self.module, self.backend)
