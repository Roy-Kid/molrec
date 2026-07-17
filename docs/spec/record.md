# Record

## Purpose

A **Record** is the top-level unit of interchange in MolRec: one self-describing
package of scientific or operational data that any MolCrafts tool may read
without guessing private layouts.

A Record is **not** a store product, a file format brand, or a class named
`MolStore` / `SimStore`. Those names are forbidden in this specification.
Implementations may expose APIs such as `open_record` or
`RecordReader` / `RecordWriter`; the **contract** is the layout and semantics
below.

## Root layout

```text
<record-root>/
├── meta/                 # required — identity, schema version, modules
├── system/               # recommended — system definition (see system.md)
├── frame/                # recommended — instantaneous snapshot (see frame.md)
├── trajectory/           # optional — ordered frames (see trajectory.md)
├── observables/          # optional — scientific results (see observables.md)
├── method/               # optional — how it was produced (see method.md)
├── status/               # optional — lifecycle / progress (see status.md)
└── metrics/              # optional — append-only run measurements (see metrics.md)
```

There is **no** record-root `parameters/` section. Scientific / force-field /
model parameters live under `system/parameters`. How a job is run lives under
`method/`.

Section names above are **conventional record keys**. Unknown sibling sections
MUST be preserved by readers that do not understand them.

## Versioning

`meta` **MUST** carry (for writers of new records):

| Key | Meaning |
|-----|---------|
| `record_schema_version` | **Sole** schema version integer for the whole record (layout + L1 encoding). Starts at **1**. |
| `format_name` | Optional binding id when using the Zarr reference layout: `molrec` — never a product name like `molpy-zarr` |

There is **no** parallel `frame_schema_version` in the contract. New writers
MUST NOT emit it. Readers of the new contract do **not** implement
backward-compatible dual-key decoding; migrate old files offline.

## Minimum record shapes

| Shape | Required sections | Typical use |
|-------|-------------------|-------------|
| Structure | `meta` + `frame` | Single conformation / snapshot |
| System def | `meta` + `system` | Topology / types without coordinates |
| Trajectory | `meta` + `trajectory` (+ optional `system`) | MD time series |
| Run | `meta` + `status` (+ `metrics` and/or `method`) | Training job / workflow run |
| Full | any combination | Reproducible experiment package |

Rules:

1. **`meta` is always required.**
2. A record MUST include **at least one of** `frame`, `system`, or `status`.
3. A **Run**-shaped record does **not** require `frame`.
4. Instantaneous Cartesian coordinates belong on `frame` / `trajectory`, not as
   required content of `system` (see [System](system.md)).
5. When both `system/` and `trajectory/` are present, trajectory **SHOULD**
   carry state updates only (coordinates, instantaneous properties, instantaneous
   Box) and not restate topology.
6. Trajectory **MAY** omit `system/`; frames may then embed full blocks
   (compatible with frame-sequence writers).
7. The cell type/key in the contract is **`Box` / `box` only** — not `simbox`.

## Relationship to L1 containers

Record sections are built from the same containers as the rest of MolRec:

- **Column / Block / Frame** — [Types](types.md), [Frame](frame.md)
- Domain meaning of block names — [Conventions](conventions.md)

A `frame/` section is an L1 Frame. A `system/` section is a conventional tree
that may embed Blocks without time-dependent coordinates.

## Backend binding (non-normative)

The reference storage binding is **Zarr V3**, implemented in
[molrs](https://github.com/MolCrafts/molrs). The specification does not require
Zarr; any backend that preserves section semantics is conforming.

Current molrs public Zarr helpers primarily persist **frame sequences**. A full
record-root aggregate (all sections under one root) is a planned alignment with
this chapter — not a second, parallel product name.

## See also

- [Overview](overview.md) — L0–L4 layering
- [System](system.md) — system definition section
- [Run surface](run.md) — training / job logs as records
