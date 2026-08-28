# Status

## Purpose

`status` stores **execution state** for a record. It is part of the **run
surface** (with [Metrics](metrics.md) and [Method](method.md)) — see
[Run surface](run.md).

It is a recommended record section: a convention layered on the general model
([Overview](overview.md)), not part of L0–L2.

Use it for monitoring, resume decisions, and UI summaries. It is **not** the
place for scientific result arrays (those belong in `frame`, `trajectory`, or
`observables`) or for time series of measurements (those belong in `metrics`).

Physical form: **Zarr group attributes** on `status/` — see
[Storage](storage.md). The logical document is one JSON object.

## Structure

```text
status
+-- state: string                     # required when status exists
+-- (stage: string)
+-- (epoch: number)
+-- (global_step: number)
+-- (steps_since_last_eval: number)
+-- (message: string)
+-- (started_at: string)              # ISO-8601
+-- (updated_at: string)
+-- (finished_at: string)
+-- (progress)                        # object — extra counters
|   \-- ...
+-- (history)                         # array of events, or object keyed by id
|   \-- <event>
|       +-- state: string
|       +-- timestamp: string
|       +-- (stage: string)
|       +-- (message: string)
|       \-- ...
+-- (tasks)                           # object keyed by task_id
|   \-- <task_id>
|       +-- state: string
|       +-- (stage: string)
|       +-- (progress)
|       +-- (message: string)
|       \-- ...
+-- (error)
|   +-- type: string
|   +-- message: string
|   +-- (timestamp: string)
|   \-- ...
\-- ...                               # producer extensions
```

Field types are plain JSON. Writers SHOULD keep the object small (current
snapshot); long series go in `metrics`.

`status.state` is **required** whenever the `status` section exists.

## Lifecycle states

Lowercase vocabulary:

| State | Meaning |
|-------|---------|
| `pending` | Created but not started |
| `running` | Currently executing |
| `succeeded` | Finished successfully |
| `failed` | Finished with an error |
| `cancelled` | Stopped by user or scheduler |
| `skipped` | Intentionally not executed |

Writers may preserve custom states. Readers should treat unknown states as
terminal only if a module specification declares them terminal.

## Stages

`status.stage` describes the current execution phase, independent of lifecycle
state.

Reserved MolNex stage vocabulary: `train`, `eval`, `test`, `predict`.

Additional stages (`prepare`, `simulate`, `relax`, `analyze`, …) are valid when
documented by `method` or a declared module.

## Progress keys

Reserved counters live directly under `status`:

| Key | Meaning |
|-----|---------|
| `epoch` | Current epoch index (zero-based when training semantics apply) |
| `global_step` | Monotonically increasing step across the run |
| `steps_since_last_eval` | Steps since the last evaluation pass |

Extra counters go under `status.progress` with clear names; do not reuse
reserved keys with different meanings.

## History

Optional ordered event log. Each event SHOULD include `state` and `timestamp`,
and MAY include `stage`, `message`, and producer-specific fields.

History is append-oriented. Updating the current `status.state` does not require
rewriting previous events.

## Task status

`status.tasks.<task_id>` holds per-task or per-stage state for workflows. Task
IDs SHOULD match identifiers in `method.stages`, workflow assets, or the
producing engine. Each task entry uses the same basic fields as root status
(`state`, optional `stage` / `progress` / `message`).

## Relationship to metrics

| Section | Role |
|---------|------|
| `status` | compact **current** lifecycle and progress |
| `metrics` | append-oriented measurements over time |

Examples:

- `status.global_step = 4000` — where execution is now
- `metrics` records `train/loss` at many steps
- `status.state = "failed"` and `status.error.message` — current failure summary

## Example

Attribute object on the `status/` Zarr group (golden:
`fixtures/run-minimal/attrs/status.json`):

```json
{
  "state": "succeeded",
  "stage": "train",
  "global_step": 2,
  "started_at": "2026-08-04T00:00:00+00:00",
  "finished_at": "2026-08-04T00:00:02+00:00"
}
```

## Rule

> `status` records lifecycle and progress state; measurements over time belong
> in `metrics`.
