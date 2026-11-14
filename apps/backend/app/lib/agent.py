from deepagents import create_deep_agent
from e2b import Sandbox
from langchain_anthropic import ChatAnthropic
from langchain_e2b import E2BSandbox

from app.lib.config import get_settings

SYSTEM_PROMPT = """You are an expert Next.js engineer building the user's app.

The app is a Next.js (App Router, TypeScript, Tailwind) project at /home/user/app.
The dev server is already running with hot reload, so the user sees your changes instantly.

Rules:
- Read existing files before editing them.
- Put pages in /home/user/app/app/, components in /home/user/app/components/.
- Install packages with: cd /home/user/app && npm install <pkg>
- Never start or restart the dev server.
- Keep state in the browser for now (no database yet).
- When done, briefly tell the user what you built."""


def build_agent(sandbox: Sandbox):
    settings = get_settings()
    model = ChatAnthropic(
        model=settings.agent_model,
        api_key=settings.anthropic_api_key,
        max_tokens=16000,
    )
    return create_deep_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        backend=E2BSandbox(sandbox=sandbox),  # file tools and shell run inside the sandbox
    )