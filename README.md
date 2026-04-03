# MolRec

MolRec is a backend-neutral record specification for atomistic data.

The documentation entry point is:

- `docs/index.md`

The site configuration is:

- `zensical.toml`

The current draft defines a MolRec-specific model centered on:

- root-level `meta`
- one canonical `frame` composed of named collections
- root-level `box` with static or trajectory-aligned cell data
- packed `trajectory` collections interpreted as a logical list of frames
- arbitrary `observables` as `name` and `meta.name` pairs with typed metadata
- typed `method` metadata for classical, ML, electronic-structure, workflow, and custom records
