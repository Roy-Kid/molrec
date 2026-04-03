# MolRec

MolRec is a backend-neutral record specification for atomistic data.

It defines **what** a molecular record means — not how to implement it. Any project that stores atoms, trajectories, force fields, or computed observables can adopt MolRec as its semantic layer.

## Why MolRec?

Atomistic simulations produce diverse data: atom coordinates, cell vectors, charge densities, energy time-series, force-field parameters, and more. Different codes store these in different formats with different conventions. MolRec provides a single, language-agnostic semantic model so that:

- A record written by one tool can be interpreted by another without guessing what the arrays mean.
- Metadata is always explicit — the spec never infers meaning from array shape or dataset name alone.
- The model is extensible to classical MD, ML potentials, electronic structure, and multi-stage workflows.

## Record structure

```text
/
+-- meta                  # record-level metadata (required)
+-- frame                 # canonical snapshot (required)
|   +-- atoms/            #   named collection: atoms
|   +-- bonds/            #   named collection: bonds
|   +-- <grids>/          #   named volumetric grids
|   +-- box               #   simulation cell (SimBox)
+-- trajectory            # time-series frames (optional)
+-- observables           # derived quantities (optional)
|   +-- <scalar>          #   e.g. total energy per step
|   +-- <vector>          #   e.g. dipole moment
|   +-- <grid>            #   e.g. charge density field
+-- method                # scientific context (optional)
+-- parameters            # workflow parameters (optional)
```

`meta` and `frame` are mandatory. Everything else is optional.

## Key design principles

- **Collections, not just atoms.** A frame can hold atoms, bonds, angles, beads, fragments, or any named entity set.
- **Grid as a first-class type.** Volumetric data (charge density, electrostatic potential, etc.) is stored as `Grid` — both inside `frame` and as `ObservableKind::Grid` in observables.
- **Metadata is mandatory for observables.** Every observable carries explicit `kind`, `description`, and `time_dependent` fields.
- **Box lives on frame.** The simulation cell (`SimBox`) is a property of each frame, not a separate root-level concept.
- **Backend-neutral.** The spec does not mandate a storage format. The reference implementation uses Zarr v3, but HDF5, SQL, or any other backend can implement the same semantics.

## Documentation

Full specification: [docs/index.md](docs/index.md)

## Reference implementation

[molrs](https://github.com/MolCrafts/molrs) provides a Rust + Python implementation of MolRec with Zarr v3 as the storage backend.

## License

BSD-3-Clause
