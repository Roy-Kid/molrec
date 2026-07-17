# MolRec fixtures

Golden records for cross-repo alignment live here (later phases). Paths are
conventional; binary payloads may be added without changing names.

| Path | Shape | Expected sections |
|------|--------|-------------------|
| `fixtures/structure-minimal/` | Structure | `meta`, `frame` (with `box` if present — never `simbox`) |
| `fixtures/system-frame-minimal/` | System + snapshot | `meta`, `system`, `frame` |
| `fixtures/trajectory-coords-only/` | Trajectory without system | `meta`, `trajectory` (frames carry coords; optional full blocks) |
| `fixtures/run-minimal/` | Run | `meta`, `status`, and `metrics` and/or `method` (no `frame` required) |

All new fixtures: `meta.record_schema_version = 1`. No root `parameters/`.

Until fixtures are populated, this file is the contract for names and shapes.
Consumers (molrs, molpy, molnex) SHOULD treat these paths as the shared test
vectors once files land.
