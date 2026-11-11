# ADR-0002: System boundaries and repository layout

- Status: Accepted
- Date: 2026-11-11

## Context

The product is a Lovable-style AI app builder. Two different things exist and
must never be confused:

| Platform (our product)                                   | Generated application (the user's artifact)         |
| -------------------------------------------------------- | --------------------------------------------------- |
| Accounts, auth, projects, conversations, messages, jobs, | Source code the agent writes: frontend, server-side |
| agent orchestration, sandbox lifecycle, storage,         | logic, dependencies, runtime config, migrations,    |
| observability, integrations, limits.                     | and the user's own database (see ADR-0005).         |

The platform has a web UI, an HTTP API, a background agent worker, and an E2B
sandbox template. It is built by one developer.

## Decision

- One Git repository (monorepo):
  - `apps/api` — FastAPI backend + background worker (Python 3.12, uv).
  - `apps/web` — platform UI: Next.js (React), shadcn/ui, Tailwind CSS.
  - `sandbox-template` — E2B template: starter for generated apps.
  - `infra` — local infrastructure (Docker Compose).
  - `docs/adr` — architecture decision records.
- FastAPI is the ONLY backend. Next.js is used as UI only: no business logic,
  database access or secrets in Next.js server actions or route handlers.
- The browser reaches the API through Next.js rewrites (`/api/*` → FastAPI) so
  it sees a single origin.
- The browser is never the source of truth for job state or project files.
- No monorepo tooling (Turborepo/Nx/pnpm workspaces) until a second
  JavaScript package exists (likely a generated API client).

## Alternatives considered

- Polyrepo: cross-app changes need coordinated commits; no benefit for one team.
- Vite SPA for the UI: viable; Next.js chosen for developer familiarity and
  parity with the generated apps' stack.
- Next.js as a second backend (server actions/route handlers with DB access):
  splits auth and business rules across two runtimes.
- TypeScript backend (e.g. with Vercel eve): single language, but eve was in
  beta and the developer prefers Python for the backend.

## Consequences

- One place for all code; atomic cross-app changes and reviews.
- Auth, authorization and business rules live in exactly one place.

* Two languages (Python, TypeScript); API types must be kept in sync
  (later: generate a TypeScript client from FastAPI's OpenAPI schema).
