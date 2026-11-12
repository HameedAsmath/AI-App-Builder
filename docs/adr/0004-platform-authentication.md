# ADR-0004: Platform authentication — email/password with server-side sessions

- Status: Accepted
- Date: 2026-11-11

## Context

Users sign in to OUR platform. Scope for v1 is intentionally small: users and
projects only — no teams, workspaces or organizations. OAuth sign-in
(Google/GitHub) may be added later. This is unrelated to the generated apps'
authentication and to the Supabase OAuth integration (ADR-0005).

## Decision

- Credentials: email + password. Passwords hashed with Argon2id.
- Emails are normalized (trimmed, lower-cased) and unique.
- `users.password_hash` is nullable, so OAuth-only accounts can exist later
  without inventing placeholder passwords.
- Sessions are server-side, stored in PostgreSQL:
  - A random session token (≥ 256 bits) is generated at login.
  - Only a SHA-256 hash of the token is stored; a database leak does not
    expose usable sessions.
  - The browser holds the token in a cookie: HttpOnly, Secure (in
    production), SameSite=Lax, Path=/.
  - Sessions have an absolute expiry and are deleted on logout
    (instant revocation).
- FastAPI issues and validates sessions. Next.js proxies `/api/*`, so cookies
  are first-party and no CORS configuration is needed.
- Login responses do not reveal whether an email exists (same error and
  similar timing for unknown email vs wrong password).
- Every project-scoped query filters by the authenticated user's id;
  ownership is checked on every API and job operation.
- When OAuth sign-in is added: a separate `auth_accounts` table holds provider
  identities; an OAuth identity is never linked to an existing account solely
  because email strings match — linking requires a verified, explicit flow.

## Alternatives considered

- JWT access/refresh tokens (discussed earlier): stateless, but revocation and
  logout are hard, and tokens in JavaScript-readable storage are exposed to XSS.
- Managed providers (Clerk/Auth0): faster and safer by default, but recurring
  cost and less learning.
- Supabase Auth for the platform: risks confusing the platform with
  generated apps' Supabase projects.

## Consequences

- Sessions are revocable instantly; no tokens readable by JavaScript.
- Simple mental model: one cookie, one table lookup per request.

* One database lookup per authenticated request (acceptable; can cache later).
* We own security work: login rate limiting, password reset and email
  verification are our responsibility (planned after milestone 1).

## Update (2026-11-12)

Switched to stateless JWT (HS256) in an httpOnly SameSite=Lax cookie, 7-day expiry.
Trade-off accepted: logout/ban is not instant; the token stays valid until expiry.
