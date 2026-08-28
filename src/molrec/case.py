"""Case -- one conformance example."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Case[M: BaseModel](BaseModel):
    """A model instance plus what it is meant to catch.

    ``expect_violation`` marks a negative case: the implementation is required
    to reject the input, and a run that quietly accepts it fails. Building one
    usually means ``model_construct()``, since the models enforce the very
    invariant the case is trying to break.

    ``backends`` scopes a case to the backends it can honestly run on. Not
    every backend carries every payload -- a dense numeric series cannot hold
    an image reference -- and pretending otherwise would either fail a
    conforming implementation or force a backend to grow an encoding the spec
    never asked for. Empty means every backend.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    id: str
    model: M
    exercises: str = ""
    expect_violation: str = ""
    backends: tuple[str, ...] = ()

    def applies_to(self, backend: str) -> bool:
        return not self.backends or backend in self.backends
