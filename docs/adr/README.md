# Architecture Decision Records

Each significant architectural decision is recorded as a numbered file.
Accepted ADRs are never edited; a changed decision gets a new ADR that
supersedes the old one. This index is updated as ADRs are added.

## Index

| ADR  | Title                                               | Status   |
| ---- | --------------------------------------------------- | -------- |
| 0001 | Record architecture decisions                       | Accepted |
| 0002 | System boundaries and repository layout             | Accepted |
| 0003 | Platform database: PostgreSQL, SQLAlchemy, Alembic  | Accepted |
| 0004 | Platform authentication                             | Accepted |
| 0005 | Generated apps and user-owned Supabase              | Accepted |
| 0006 | Sandbox and project file persistence                | Accepted |
| 0007 | Job execution model                                 | Accepted |
| 0008 | Streaming with SSE over persisted events            | Accepted |
| 0009 | Distinct identifiers for distinct lifecycles        | Accepted |
| 0010 | Agent runtime: Deep Agents on LangGraph with Claude | Accepted |
| 0011 | Observability: LangSmith tracing                    | Accepted |

## Open decisions (to be recorded when decided)

| Topic                    | Options under consideration                                    | Needed by         |
| ------------------------ | -------------------------------------------------------------- | ----------------- |
| Memory                   | LangMem + LangGraph Store vs Mem0 vs custom pgvector           | After milestone 1 |
| Queue at scale           | Postgres queue vs Redis Streams vs RabbitMQ                    | When load demands |
| Durable execution        | Leases/heartbeats, resume from checkpoints, idempotency ledger | After milestone 1 |
| Versioning & R2 layout   | Content-addressed blobs + version manifests                    | After milestone 1 |
| Sandbox retention policy | Warm time, idle timeout, pause vs kill                         | Sandbox step      |
| Capacity targets         | Validate realistic concurrency before any RPS target           | Before launch     |

## Background

`lovable_clone_architecture_handoff_nov_2026.pdf` (Nov 3–11, 2026 discussions)
and the architecture sessions of Nov 9–11, 2026.
