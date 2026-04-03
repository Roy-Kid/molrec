# MolRec

MolRec is a specification for atomistic records.

This documentation is written for developers. Its purpose is to define what a MolRec record means,
not to prescribe one implementation strategy or one code architecture.

## Scope

MolRec defines:

- what a canonical frame is
- how static and time-dependent box information is attached to a record
- how trajectory data relate to frames without assuming atoms-only storage
- how observables are represented as `name` and `meta.name` pairs with a minimum metadata contract
- how typed `method` metadata covers classical, ML, electronic-structure, workflow, and custom workflows

MolRec does not define:

- one mandatory storage backend
- one mandatory class hierarchy
- one mandatory API surface
- one mandatory internal implementation

## Root structure

The root-level structure of a MolRec record is:

```text
/
\-- meta
\-- frame
\-- (box)
\-- (trajectory)
\-- (observables)
\-- (method)
\-- (parameters)
```

`meta` and `frame` are mandatory. The other groups are optional.

## Reading guide

- [Overview](spec/overview.md) defines the core ideas and invariants.
- [Meta](spec/meta.md) defines record-level metadata and audit information.
- [Types](spec/types.md) defines observable data kinds, typed schema blocks, and the metadata needed to interpret them.
- [Frame](spec/frame.md) defines canonical snapshots and named collections, including tuple-based collections such as bonds and angles.
- [Trajectory](spec/trajectory.md) defines time-series data as logical lists of frames packed by collection.
- [Observables](spec/observables.md) defines the `name` and `meta.name` pairing and the minimum metadata contract for observables.
- [Method](spec/method.md) defines typed method metadata for standard and custom workflows.
