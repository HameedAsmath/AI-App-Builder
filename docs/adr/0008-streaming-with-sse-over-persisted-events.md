# ADR-0008: Streaming with Server-Sent Events over persisted run events

- Status: Accepted
- Date: 2026-11-11

## Context

Users must see progress while the agent works: status, tool activity,
file changes, command output, preview readiness, completion or failure.
The agent runs in a worker process, not in the API process that holds the
browser connection. Browsers refresh and connections drop.

## Decision

- Commands (create project, send message, cancel) use ordinary HTTP.
- Progress uses Server-Sent Events (SSE): `GET /api/runs/{run_id}/events`.
- Every event the worker produces is appended to `run_events`
  (`run_id`, per-run sequence number `seq`, `type`, JSON `payload`,
  `created_at`).
- The SSE endpoint replays events after the client's last seen sequence
  (`Last-Event-ID`) and then follows new events, so refresh/reconnect never
  loses progress.
- The SSE connection is not the job. Runs continue whether or not anyone is
  connected.
- High-frequency text deltas are coalesced (flushed every few hundred
  milliseconds) instead of one row per token.
- Initial event types: `run.started`, `agent.message`, `tool.started`,
  `tool.finished`, `file.changed`, `command.output`, `preview.ready`,
  `run.succeeded`, `run.failed`, `run.cancelled`.
- When the agent needs user input (later), the question is an SSE event and
  the answer is a normal HTTP POST.

## Alternatives considered

- WebSockets: two-way, but we only need server→client; adds connection
  management without removing the need for persisted events.
- Polling a status endpoint: simple, but laggy and wasteful.
- Redis pub/sub as the only channel: messages are lost while nobody is
  subscribed; can be added later for fan-out, with PostgreSQL remaining the
  record.

## Consequences

- Reconnect and replay work across API instances and processes.
- The event log doubles as a debugging and audit trail for each run.

* Event rows accumulate; a retention policy is needed later.
* Tail latency depends on polling or LISTEN/NOTIFY between processes.
