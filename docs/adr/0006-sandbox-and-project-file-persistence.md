# ADR-0006: E2B sandboxes for execution; durable project files outside the sandbox

- Status: Accepted
- Date: 2026-11-11

## Context

Generated code and shell commands are untrusted. The agent needs a
filesystem, shell, package installation, a dev server and a preview URL.
E2B provides isolated execution and preview infrastructure — not the product
itself (orchestration, persistence, UI and lifecycle remain ours).
Sandbox filesystems disappear when sandboxes expire or are terminated.

## Decision

- Execution: one E2B sandbox per active project, created from a custom
  template (Next.js + Supabase starter with dependencies preinstalled) for
  fast startup.
- No generated code or shell command ever runs on platform hosts.
- The sandbox is a disposable working copy, NOT the source of truth.
- Durable project files for milestone 1:
  - At the end of each successful run, the full set of source files is saved
    to PostgreSQL (`project_files`: project, path, content, sha256, size).
  - Build outputs and dependencies (`node_modules`, `.next`) are never saved;
    they are rebuilt.
- Lifecycle:
  - The sandbox id and its expiry are stored with the project.
  - On demand, reconnect to a live sandbox; otherwise create a new one from
    the template and restore the saved files.
  - Sandboxes have CPU/memory/lifetime limits; abandoned sandboxes are
    terminated; deleting a project kills its sandbox.
- Milestone 1 preview URLs are E2B's unguessable per-sandbox URLs; access
  restrictions are revisited before launch.
- Later (planned): Cloudflare R2 with content-addressed blobs and version
  manifests, enabling version history and restore; checkpoints at
  meaningful milestones rather than after every tool call.

## Alternatives considered

- Self-hosted Docker/gVisor/Firecracker sandboxes: we would operate isolation,
  networking and scheduling infrastructure ourselves.
- Treating the sandbox filesystem as persistent: work is lost on expiry.
- Supabase Storage for persistence (earlier option): superseded by the plan
  for Cloudflare R2 (S3-compatible API, no egress fees).
- R2 from day one: correct long-term, but not needed for the happy path;
  PostgreSQL storage is simpler for small text-file projects.

## Consequences

- Untrusted code is isolated; a lost sandbox is a cache miss, not data loss.

* Storing file contents in PostgreSQL does not scale to large or binary
  assets; migration to R2 is planned.
* Milestone 1 has no version history: each run overwrites the saved files.
