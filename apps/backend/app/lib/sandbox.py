import asyncio

from e2b import Sandbox

from app.lib.config import get_settings

APP_DIR = "/home/user/app"
PORT = 3000
LIFETIME = 60 * 60  # sandbox stays alive 1 hour after last use


def _create() -> Sandbox:
    """New sandbox: scaffold a Next.js app and start the dev server."""
    sb = Sandbox.create(api_key=get_settings().e2b_api_key, timeout=LIFETIME)
    sb.commands.run("npx --yes create-next-app@latest app --yes", cwd="/home/user", timeout=600)
    # background=True → keeps running after this call returns
    sb.commands.run(f"npx next dev -H 0.0.0.0 -p {PORT}", cwd=APP_DIR, background=True)
    return sb


def _connect(sandbox_id: str) -> Sandbox | None:
    """Reconnect to an existing sandbox, or None if it has expired."""
    try:
        sb = Sandbox.connect(sandbox_id, api_key=get_settings().e2b_api_key)
        sb.set_timeout(LIFETIME)  # extend its life
        return sb
    except Exception:
        return None


async def get_sandbox(sandbox_id: str | None) -> Sandbox:
    # The E2B client used here is blocking, so run it in a thread to keep FastAPI responsive
    if sandbox_id:
        sb = await asyncio.to_thread(_connect, sandbox_id)
        if sb:
            return sb
    return await asyncio.to_thread(_create)


def preview_url(sb: Sandbox) -> str:
    return f"https://{sb.get_host(PORT)}"