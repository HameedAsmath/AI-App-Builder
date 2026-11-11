# ADR-0005: Generated apps use Next.js and the user's own Supabase (via OAuth)

- Status: Accepted
- Date: 2026-11-11

## Context

Generated applications need a frontend, server-side logic and a database.
Milestone 1 target: "create a todo application" produces a working app whose
database tables exist in a real database.

## Decision

- Generated apps: Next.js (App Router) + TypeScript + Tailwind + Supabase
  client. The app's backend is Next.js server-side code (server actions /
  route handlers) talking to Supabase.
- Users connect their OWN Supabase account via OAuth. They choose or create a
  Supabase project for each platform project.
- OAuth access/refresh tokens are encrypted at rest in our database, with an
  encryption key held outside the database (environment/secret manager).
  Tokens are decrypted only inside backend code that needs them.
- Migrations:
  - The agent writes SQL migration files into the project
    (`supabase/migrations/NNNN_description.sql`).
  - Migrations are applied by a backend-side tool via the Supabase Management
    API using the user's OAuth token — never from inside the sandbox.
  - Generated-app migrations are completely separate from platform Alembic
    migrations.
- Only the project's public URL and public (anon/publishable) key are placed
  in the sandbox / generated app environment. OAuth tokens and service-role
  (secret) keys never enter the sandbox or the model context.
- Exact OAuth scopes and Management API endpoints are confirmed against
  Supabase's documentation when implemented.

## Alternatives considered

- Platform-provisioned Supabase projects: smoother onboarding, but we pay for,
  own and are responsible for every user's data.
- A shared platform database for all generated apps: no isolation between
  users; mixes platform and customer data.
- Running migrations from inside the sandbox with a secret key: exposes
  privileged credentials to generated (untrusted) code.

## Consequences

- Users own their data and billing; strong isolation between users.
- Privileged credentials never reach untrusted code.

* Requires registering a Supabase OAuth app and handling token refresh and
  revocation.
* Restoring generated code does not roll back the user's database schema;
  this must be surfaced to the user (later, with versioning).
