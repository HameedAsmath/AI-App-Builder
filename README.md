# loveable-v2

An AI application builder: users describe an app in natural language, and an
AI agent generates a Next.js + Supabase application, applies its database
migrations to the user's own Supabase project, and previews it live in an
isolated E2B sandbox.

## Repository layout

| Path               | Purpose                                                     |
| ------------------ | ----------------------------------------------------------- |
| `apps/api`         | FastAPI backend: auth, projects, agent runs, SSE (Python)   |
| `apps/web`         | Platform UI (Next.js, shadcn/ui, Tailwind) — UI only        |
| `sandbox-template` | E2B template: Next.js + Supabase starter for generated apps |
| `infra`            | Local infrastructure (Docker Compose)                       |
| `docs/adr`         | Architecture Decision Records                               |

## Milestone 1 (happy path)

Sign up → create project → prompt "create a todo app" → connect Supabase
via OAuth → agent generates code and runs migrations → live preview.
