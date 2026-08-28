"""How big a chunk should be.

Zarr's automatic chunking is not always in a good band, and the difference is
measurable: on a 1M x 3 float32 column, 196 KB chunks served a random row in
0.49 ms where 1.5 MB chunks took 1.49 ms and the automatic choice took
0.99 ms.

Two rules, and only the first is backed by measurement:

* **Target a chunk size in bytes.** Roughly a quarter to one megabyte. Too
  small and per-chunk overhead dominates; too large and every read drags a
  whole chunk through the codec.
* **Chunk the leading axis only.** Trailing axes are per-entity structure --
  the three components of a coordinate -- and splitting them means a single
  entity spans several chunks. Locally that costs nothing measurable; over
  HTTP it is the difference between one range request and three. Kept because
  it is simpler and cannot be worse, not because a local benchmark proved it.

Sharding then bounds the file count: many chunks land in one file, at
identical throughput (measured: 12 files to 3, no change in MB/s).

None of this is contractual. A conforming reader must open any chunking, and
two stores of the same data are expected to differ byte for byte.
"""

from __future__ import annotations

import math

TARGET_CHUNK_BYTES = 512 * 1024

#: Beyond this many chunks, collapse them into one shard file.
SHARD_ABOVE = 4


def plan(
    shape: tuple[int, ...], itemsize: int | None
) -> tuple[tuple[int, ...] | None, tuple[int, ...] | None]:
    """Return ``(chunks, shards)``, either of which may be ``None``.

    ``itemsize`` of ``None`` means a variable-width dtype, where a byte target
    is not computable -- leave the choice to the backend.
    """
    if not shape or itemsize is None or shape[0] == 0:
        return None, None

    trailing = math.prod(shape[1:]) if len(shape) > 1 else 1
    row_bytes = max(1, trailing * itemsize)

    rows = min(shape[0], max(1, TARGET_CHUNK_BYTES // row_bytes))
    chunks = (rows, *shape[1:])

    chunk_count = math.ceil(shape[0] / rows)
    if chunk_count <= SHARD_ABOVE:
        return chunks, None

    # A shard must be a whole multiple of its inner chunk.
    return chunks, (rows * chunk_count, *shape[1:])
