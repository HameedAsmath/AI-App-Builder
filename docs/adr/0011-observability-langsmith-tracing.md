# ADR-0011: Observability — LangSmith for agent tracing

- Status: Accepted
- Date: 2026-11-11

## Context

Agent runs are long, multi-step and non-deterministic. Debugging requires
seeing every model call, tool call, input/output, latency and token count.
The agent runtime is Deep Agents on LangGraph (ADR-0010). The Nov 9 handoff
preferred Langfuse; LangSmith Deployment was rejected on cost (ADR-0007).

## Decision

- Use hosted LangSmith for agent tracing only, starting on the free
  Developer plan (5k base traces/month, 14-day retention).
- Tracing is enabled purely by configuration (`LANGSMITH_TRACING`,
  `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`) and can be switched off per
  environment with no code changes.
- Each trace is tagged with `run_id`, `project_id` and `conversation_id` so a
  platform run can be found in LangSmith and vice versa.
- Separation of concerns:
  - LangSmith: traces, spans, latency, token visibility, evaluations.
  - PostgreSQL: the authoritative record of runs, events and state.
  - Our own usage table (planned): tokens and cost per user/project for
    quotas and billing. LangSmith is never the billing source.
  - Application code: retries, recovery, cancellation (ADR-0007).
- Secrets never appear in prompts, tool inputs or tool outputs, so they never
  appear in traces (ADR-0005 keeps OAuth tokens out of model context).
- LangSmith Deployment is NOT used (ADR-0007).

## Alternatives considered

- Langfuse (Nov 9 preference): open source and runtime-agnostic. Self-hosting
  requires PostgreSQL, ClickHouse, Redis and object storage; the hosted tier
  is comparable to LangSmith for our needs.
- OpenTelemetry + Grafana/Tempo: general-purpose, but no LLM-aware views
  (prompts, token usage, tool trees) without extra work.
- No tracing: agent failures would be very hard to diagnose.

## Consequences

- Near-zero setup with LangGraph; rich run trees for debugging.
- Low lock-in: tracing is a side channel; removing it changes no behavior.

* Traces contain user prompts and generated code and are stored by LangChain
  (hosted). Must be disclosed in the privacy policy before public launch.
* Free-tier trace limits and short retention; paid plans or Langfuse may be
  needed as usage grows.
* Self-hosting LangSmith requires an Enterprise plan.
