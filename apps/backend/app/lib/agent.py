from functools import lru_cache

from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic

from app.lib.config import get_settings

SYSTEM_PROMPT = """You are an expert full-stack engineer who builds Next.js apps.
For now you cannot run code or create files. Explain your plan and show the code you would write.
Be concise."""


@lru_cache
def get_agent():
    settings = get_settings()
    model = ChatAnthropic(
        model=settings.agent_model,
        api_key=settings.anthropic_api_key,
        max_tokens=16000,
    )
    return create_deep_agent(model=model, system_prompt=SYSTEM_PROMPT)