# Overview

## Purpose

MolRec defines the meaning of a molecular record.

The central idea is simple:

- `frame` stores a canonical snapshot as named collections, optional grids, and an optional box
- `trajectory` stores a packed list of frame-like snapshots grouped by collection
- `observables` stores arbitrary derived or reported data (scalar, vector, or grid)
- `method` stores typed scientific context that explains how the record was produced
- `meta` stores record-level metadata and audit information

This is a semantic specification. It exists to make records interpretable across projects and
languages.

## Core definitions

### Record

A MolRec record is the complete logical object rooted at:

```text
/
\-- meta
\-- frame
\-- (trajectory)
\-- (observables)
\-- (method)
\-- (parameters)
```

### Canonical frame

The canonical frame is the reference snapshot of the system.

It may represent:

- an initial structure
- a relaxed structure
- a canonical snapshot extracted from a run
- a static molecular structure

The canonical frame defines the default entity ordering for any canonical collection reused by the
record.

### Box

`box` is a property of each `frame`.

Each frame carries its own simulation cell (cell vectors, origin, and periodic boundary conditions).
For trajectory data, each frame stores its own box, naturally supporting both fixed-cell and
variable-cell workflows.

### Grid

`Grid` is a data structure for values on a uniform 3-D spatial grid.

A grid is defined by:

- `dim`: grid dimensions `[nx, ny, nz]`
- `origin`: Cartesian origin
- `cell`: cell vectors defining the spatial extent
- `pbc`: periodic boundary flags
- named scalar arrays, each of length `nx * ny * nz`

Grid appears in two places:

- **In frame**: as part of the canonical snapshot (e.g., charge density read from a file).
- **In observables**: as `kind: "grid"`, carrying semantic metadata (description, unit, etc.).

### Trajectory

A trajectory is conceptually a list of frames.

In storage, it is packed into aligned arrays grouped by collection. The fundamental interpretation
is still:

> `trajectory` is a list of frame-like snapshots compressed into shared arrays, not a requirement to
> duplicate full frame objects per timestep.

Writers should prefer packed storage over literal per-frame object repetition. This keeps trajectory
reads efficient and avoids metadata duplication while preserving frame-like semantics.

### Observable

An observable is any recorded quantity outside the core frame/trajectory definition.

MolRec supports three observable data kinds:

- **Scalar**: a single value or 1-D array (e.g., total energy, temperature)
- **Vector**: an N-D array of components (e.g., dipole moment, stress tensor)
- **Grid**: a volumetric field on a spatial grid (e.g., electron density, spin density)

### Method

The method group describes how the record was produced.

Examples:

- classical force field and integrator
- ML potential and model metadata
- electronic-structure method, basis, and solver settings
- custom typed schemas documented in [Types](types.md)

## Design decisions

### Bonded collections live in frame

If a snapshot needs per-bond, per-angle, or per-dihedral information, those arrays belong in
`frame`, because they are part of the stored snapshot or reference structure.

### Box lives on frame

The simulation cell is a property of each frame, not a separate root-level concept. This simplifies
the data model: every frame is self-contained with its own atoms, grids, and cell.

### Grid is a data structure, not an observable kind

Grid itself is a pure data container (dimensions, cell, arrays). It carries no unit or description.
When a Grid appears in observables, the semantic metadata (unit, description, sampling, domain)
lives on the `ObservableRecord` wrapper, not on the Grid object itself.

### Trajectories are collection-based, not atoms-only

MolRec does not require trajectory data to be stored only as atom vectors.

Any named collection may appear in `trajectory` if its metadata defines:

- whether it is aligned to a canonical frame collection or dynamic over time
- what its entity axis means
- how any additional axes should be interpreted

### No standalone frame dimension field

MolRec does not use a separate `frame.dimension` field.

Spatial dimension is inferred from array shapes such as:

- `position[N][ndim]`
- `box/vectors[ndim][ndim]`
- `trajectory/atoms/position[ntimestep][N][ndim]`

## Normative invariants

The following invariants define MolRec 0.1:

1. Every record has exactly one canonical `frame`.
2. `frame` contains zero or more named canonical collections, each with its own count and default
   entity order.
3. `box` is a property of each frame, carrying cell vectors, origin, and boundary conditions.
4. `trajectory` is interpreted as a list of frame-like snapshots packed into aligned arrays by
   collection.
5. `trajectory` is not atoms-only. Any named collection may appear if its metadata defines axis and
   alignment semantics.
6. A trajectory collection is either canonical-aligned or dynamic, and its metadata must state which
   mode applies.
7. Every observable dataset `observables/<name>` must have a corresponding metadata entry
   `observables/meta/<name>`.
8. `method` stores typed scientific context, not result arrays.
9. Any custom typed schema used by `method` or an extension module must define parse rules in
   [Types](types.md) or in a declared module specification.
