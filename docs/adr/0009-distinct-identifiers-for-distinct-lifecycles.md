# ADR-0009: Distinct identifiers for distinct lifecycles

- Status: Accepted
- Date: 2026-11-11

## Context

Several "session"-like concepts exist and were easy to conflate in early
discussions (Nov 5): a login session, a chat, an agent's conversation state,
an E2B sandbox, a background job. They have different owners, lifetimes and
failure modes.

## Decision

Each concept has its own identifier and table/column; none is reused for
another purpose:

| Identifier           | Represents                                      | Lifetime                           |
| -------------------- | ----------------------------------------------- | ---------------------------------- |
| `user_id`            | A platform account                              | Until account deletion             |
| auth session token   | A browser login (ADR-0004)                      | Until logout/expiry                |
| `project_id`         | One generated application                       | Until project deletion             |
| `conversation_id`    | One chat thread within a project                | Until deleted; a new chat = new id |
| `message_id`         | One user or assistant message                   | With its conversation              |
| `run_id`             | One agent job triggered by a message (ADR-0007) | Until finished; kept as history    |
| agent thread id      | The agent runtime's conversation state          | Mapped 1:1 to `conversation_id`    |
| `sandbox_id`         | One E2B sandbox (ADR-0006)                      | Minutes to hours; disposable       |
| Supabase project ref | The user's database project (ADR-0005)          | Owned by the user, outside us      |

Relationships: user 1─* projects 1─* conversations 1─\* messages;
a user message 0─1 runs; a project 0─1 active sandbox.

## Alternatives considered

- Reusing the auth session as the chat/agent session: logging out would
  end the chat; logging in on two devices would split it.
- Reusing the sandbox id as the project's identity: sandboxes are disposable.

## Consequences

- Each lifecycle can expire, fail or be replaced without corrupting the others.

* More identifiers to map, which is deliberate.
