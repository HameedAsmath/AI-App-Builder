# ADR-0010: Agent runtime — LangChain Deep Agents on LangGraph, with Claude models

- Status: Accepted
- Date: 2026-11-11

## Context

The agent must turn a prompt into a working Next.js + Supabase app: read and
edit many files, run commands (install, typecheck, build), delegate subtasks,
keep long contexts manageable, and later ask the user questions or request
approval. File and shell tools must act on the E2B sandbox (ADR-0006), never
on platform hosts. The agent runs inside the worker process (ADR-0007).

An earlier direction (Nov 9 handoff) preferred the Claude Agent SDK and
cautioned against adding LangChain/LangGraph without a concrete need. The
concrete needs identified since: tools that act on a remote sandbox while the
loop and secrets stay on our worker, and built-in persistence/interrupt
primitives for later durability and human-in-the-loop.

## Decision

- Harness: `deepagents` (`create_deep_agent`): built-in file tools
  (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`), `execute`
  via a sandbox backend, subagents (`task`), automatic summarization, and
  `interrupt_on` for approvals.
- Runtime: LangGraph. Used directly where we need it (checkpointer, `Command`
  to resume interrupts, streaming); declared as explicit dependencies.
- Sandbox backend: E2B via `langchain-e2b`. The agent loop, API keys and user
  credentials stay on the worker; only file/shell operations reach the sandbox.
- Platform-side custom tools run on the worker, never in the sandbox
  (e.g. `apply_migration` using the user's Supabase OAuth token, ADR-0005).
- Model: Claude via `langchain-anthropic`. The model id is configuration,
  not code, so it can be changed per environment.
- Conversation state: LangGraph's PostgreSQL checkpointer, with the agent
  thread id mapped 1:1 to `conversation_id` (ADR-0009), so follow-up messages
  continue the same agent context. Automatic crash resume from checkpoints is
  NOT part of milestone 1 (ADR-0007).
- Containment of the framework:
  - All LangChain/LangGraph imports live in one module (`app/agent/`).
  - The rest of the platform talks to it through a narrow interface
    (start a run, stream events, cancel).
  - Exact versions are pinned in the lock file and upgraded deliberately.
- Verified against current package documentation at implementation time.

## Alternatives considered

- Claude Agent SDK (Nov 9 preference): the strongest coding harness for
  Claude, but its built-in tools execute where its CLI subprocess runs. Using
  it safely means running it inside the sandbox (plus a model-key proxy) or
  re-implementing its file/shell tools against E2B.
- Vercel eve: sandbox-aware design with built-in durability, but
  TypeScript-only and in beta.
- Own agent loop on the Anthropic Messages API: maximum control, but we would
  build file tools, compaction and subagents ourselves.
- Pydantic AI + DBOS/Temporal: strongest durability, no built-in file/shell
  tools or compaction.
- OpenAI Agents SDK (sandbox agents): oriented to OpenAI models.

## Consequences

- Loop and secrets outside the sandbox; a sandbox crash does not kill the agent.
- Built-in file tools, subagents and summarization reduce what we build.
- LangGraph checkpoints and interrupts give a direct path to durable runs and
  human-in-the-loop later.

* Larger dependency surface; LangChain packages change often (mitigated by
  pinning and the `app/agent/` boundary).
* The harness is model-agnostic rather than tuned specifically for Claude;
  output quality must be evaluated, not assumed.
* The LangGraph checkpointer uses its own PostgreSQL driver (psycopg)
  alongside SQLAlchemy's asyncpg — two connection pools to the same database.
