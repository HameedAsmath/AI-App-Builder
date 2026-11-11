# ADR-0007: Job execution model — separate worker process with a PostgreSQL-backed queue

- Status: Accepted
- Date: 2026-11-11

## Context

An agent run takes minutes. HTTP requests must return quickly, and runs must
continue independently of the browser connection. Full durable execution
(leases, heartbeats, checkpoint-based resume, retries, idempotency) is
deliberately deferred until after milestone 1, but the design must not block
it.

FastAPI in-process background tasks are unsuitable even for v1: an API
restart — including every `uvicorn --reload` during development — kills
in-flight runs.

## Decision

- Two process types from the same codebase (`apps/api`):
  - API process (Uvicorn): validates requests, creates run rows, serves SSE.
  - Worker process: claims and executes agent runs.
- The queue is the `agent_runs` table in PostgreSQL:
  - The API inserts a run with status `queued` in a short transaction and
    returns `202` with the run id immediately.
  - Workers claim runs with
    `SELECT ... FOR UPDATE SKIP LOCKED` inside a short transaction that sets
    status `running` and records the worker id and start time.
  - Workers poll briefly (≈1 s) for new runs; LISTEN/NOTIFY may replace polling.
- Milestone 1 run states: queued → running → succeeded | failed | cancelled.
- Cancellation: a `cancel_requested` flag on the run, checked by the worker
  between agent steps.
- Crash handling in milestone 1: on startup, a worker marks runs left in
  `running` by a dead worker as `failed` (reason recorded). Runs fail
  visibly instead of hanging; there is no automatic resume yet.
- Bounded concurrency: each worker executes at most N runs concurrently
  (configurable, default 2); each run uses its own database session.
- One active run per project at a time; further messages are queued behind it.
- Transaction boundaries follow ADR-0003: no transaction spans model calls,
  sandbox commands or other slow I/O.

## Planned (after milestone 1)

Leases with heartbeats and automatic requeue, agent checkpoints and resume,
retry policy with backoff, a tool-call idempotency ledger, waiting states
(input/approval), terminal-failure inspection (dead-letter).

## Alternatives considered

- FastAPI BackgroundTasks / asyncio tasks in the API process: lost on every
  restart or deploy; couples API latency to agent load.
- Redis Streams or RabbitMQ (discussed Nov 6): good brokers, but an extra
  service; a queue message must not be the only record of a job anyway, so
  the job row is required regardless. Revisit when throughput demands it.
- Kafka: far beyond v1 needs.
- Celery / arq / Dramatiq: add a broker and their own retry semantics without
  removing the need for a durable job row.
- Durable workflow engines (Temporal, DBOS) and LangSmith Deployment:
  powerful, but extra infrastructure or cost (~$250–400/month for LangSmith
  Deployment) before the product exists.

## Consequences

- Runs survive API restarts and deploys; API and workers scale independently.
- The run row is the single durable record of a job from day one.
- No new infrastructure beyond PostgreSQL.

* KNOWN LIMITATION (milestone 1): a worker crash fails its in-flight runs;
  there is no automatic resume.
* Polling adds up to ~1 s of start latency.
* The early 10,000 requests/second figure is an unvalidated target; capacity
  will be measured (model rate limits, sandbox quotas, pool sizes) before any
  target is promised.
