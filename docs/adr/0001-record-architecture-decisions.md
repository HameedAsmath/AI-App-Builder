# ADR-0001: Record architecture decisions

- Status: Accepted
- Date: 2026-11-11

## Context

This project involves many interdependent technical decisions (agent runtime,
job execution, sandboxing, storage, authentication). Several were revised
during exploration between Nov 3 and Nov 11, 2026 (e.g. MongoDB → PostgreSQL,
Supabase Storage → Cloudflare R2). Without a record, the reasoning behind each
choice is lost and settled questions get re-debated.

## Decision

- Record each significant architectural decision as a numbered Markdown file
  in `docs/adr/`.
- Sections: Status, Date, Context, Decision, Alternatives considered,
  Consequences.
- Status values: Proposed, Accepted, Superseded by ADR-XXXX, Deprecated.
- Accepted ADRs are immutable. A changed decision gets a new ADR that marks
  the old one as superseded.
- Undecided topics are tracked in the "Open decisions" table of
  `docs/adr/README.md` until they are decided.
- A decision is "significant" if it is hard to reverse, affects more than one
  component, or a future maintainer would reasonably ask "why?".

## Consequences

- Decisions, alternatives and known limitations are versioned with the code.
- Revisions are visible as a history rather than silent rewrites.

* Requires discipline: every significant decision needs an ADR.
