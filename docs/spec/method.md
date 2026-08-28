# Method

## Purpose

`method` stores the **scientific / training context** needed to interpret a
record. It is part of the **run surface** (with [Status](status.md) and
[Metrics](metrics.md)) — see [Run surface](run.md).

It is a recommended record section: a convention layered on the general model
([Overview](overview.md)).

It answers:

- what class of method produced this record
- which engine wrote it
- which force field, model, or solver was used
- which settings define the calculation

`method` is descriptive metadata. Result arrays stay in `frame`, `trajectory`,
or `observables`. System-defining parameter tables live under
`system/parameters` (see [System](system.md)), not as a root `parameters/` or
`forcefield/` section.

Physical form: **Zarr group attributes** on `method/` — see
[Storage](storage.md). The logical document is one JSON object.

## Structure

```text
method
+-- type: string                      # required — selects parse rules
+-- description: string               # required
+-- engine                            # required
|   +-- name: string
|   \-- (version: string)
+-- (order: string[])                 # stage ids for workflow type
\-- (stages)
    \-- <stage_id>
        +-- type: string
        +-- description: string
        \-- ...
```

Field types are plain JSON.

## Typed schemas

Interpretation is driven by `method.type`, not by hard-coded subtree names alone.

Rules:

1. `method.type` is required when the section exists.
2. `method.description` is required.
3. `method.engine.name` is required.
4. Custom method types MUST document parse rules under `meta.modules`.
5. Result arrays stay in `frame`, `trajectory`, or `observables`.

Standard types (open vocabulary; not a closed enum):

| Type | Typical content |
|------|-----------------|
| `classical` | force field, bonded/nonbonded choices, integrator, thermostat, barostat, cutoffs |
| `ml` | model family, checkpoint id, representation, inference precision, training provenance |
| `electronic_structure` | HF/DFT/MP2 family, functional, basis, ECP, SCF, spin, thresholds |
| `workflow` | multi-stage composite (see below) |

Any custom type is valid if its parse rules are declared in a module under
`meta.modules`.

### `workflow`

Required when `type = "workflow"`:

- `method.order` — ordered list of stage ids
- `method.stages.<stage_id>.type` — each stage is itself a typed method block

Typical content: stage names and order, per-stage engines/methods, inputs and
outputs, targets such as `/frame/atoms` or `/observables/free_energy`.

## Example

```json
{
  "type": "workflow",
  "description": "Geometry relaxation followed by single-point DFT",
  "engine": { "name": "MolFlow" },
  "order": ["relax", "single_point"],
  "stages": {
    "relax": {
      "type": "classical",
      "description": "Pre-relaxation with a classical force field",
      "force_field": "GAFF"
    },
    "single_point": {
      "type": "electronic_structure",
      "description": "Single-point DFT evaluation",
      "family": "DFT",
      "functional": "PBE",
      "basis": "def2-SVP",
      "spin": "restricted"
    }
  }
}
```
