# Frame

## Purpose

`frame` stores a canonical snapshot.

It is the place for structure-like data:

- per-entity arrays for any canonical collection
- per-bond arrays
- per-angle arrays
- per-dihedral arrays
- other snapshot-resolved arrays tied to the canonical configuration

`frame` is not restricted to atoms only.

## Structure

```text
frame
\-- atoms
|   \-- meta
|   |   +-- count: Integer[]
|   |   +-- entity_kind: String[] = "atom"
|   \-- (id: Integer[N])
|   \-- (element: String[N])
|   \-- (atomic_number: Integer[N])
|   \-- (name: String[N])
|   \-- (position: Float[N][ndim])
|   \-- (mass: Float[N])
|   \-- (charge: Float[N])
|   \-- ...
\-- (bonds)
|   \-- meta
|   |   +-- count: Integer[]
|   |   +-- entity_kind: String[] = "bond"
|   \-- (index: Integer[count][2])
|   \-- ...
\-- (angles)
|   \-- meta
|   |   +-- count: Integer[]
|   |   +-- entity_kind: String[] = "angle"
|   \-- (index: Integer[count][3])
|   \-- ...
\-- (dihedrals)
|   \-- meta
|   |   +-- count: Integer[]
|   |   +-- entity_kind: String[] = "dihedral"
|   \-- (index: Integer[count][4])
|   \-- ...
\-- (fragments)
|   \-- meta
|   |   +-- count: Integer[]
|   |   +-- entity_kind: String[] = "fragment"
|   \-- ...
\-- ...
```

The names above are examples. A canonical collection may represent atoms, beads, fragments, rigid
bodies, virtual sites, QM atoms, coarse-grained sites, or any other named entity set.

## Canonical collections

Each collection under `frame` is a collection of aligned per-entity arrays.

Rules:

- `frame/<collection>/meta/count` defines the canonical entity count for that collection
- every dataset in `frame/<collection>` except `meta` has leading dimension `count`
- `frame/<collection>` defines the canonical entity order reused by aligned trajectory or
  observable data

The conventional `atoms` collection is still common, but it is not privileged over other
collections in the specification.

## Tuple-based collections

MolRec allows tuple-based collections directly under `frame`.

This includes:

- `frame/bonds`
- `frame/angles`
- `frame/dihedrals`
- other implementation-defined tuple collections

Each collection may contain:

- an `index` array defining the participating entity tuples
- aligned arrays of labels, parameters, or properties

Tuple collections are not restricted to atom tuples. The same pattern may be used for bead tuples,
fragment tuples, or other implementation-defined relations.

Examples:

- bond order
- equilibrium length
- angle equilibrium value
- dihedral periodicity

## Box

`box` is not part of `frame`.

It is stored as a root-level sibling:

```text
box
\-- meta
|   +-- time_dependent: Bool[]
\-- vectors: Float[ndim][ndim] | Float[ntimestep][ndim][ndim]
\-- (origin: Float[ndim] | Float[ntimestep][ndim])
\-- (boundary: String[ndim] | String[ntimestep][ndim])
```

If `box/meta/time_dependent = true`, every box array uses the shared trajectory timestep axis.

## Interpretation

`frame` should be read as:

> the canonical stored snapshot of the system, including any static or snapshot-level collections that
> belong with it.
