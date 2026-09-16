import os

from agent.llm.client import OpenAICompatibleClient


def create_llm_client():
    base_url = os.getenv(
        "DEVRESCUE_LLM_BASE_URL",
        "http://127.0.0.1:8081/v1",
    )

    api_key = os.getenv(
        "DEVRESCUE_LLM_API_KEY",
        "sk-devrescue",
    )

    model = os.getenv(
        "DEVRESCUE_LLM_MODEL",
        "gemini-3.5-flash-thinking",
    )

    return OpenAICompatibleClient(
        base_url=base_url,
        api_key=api_key,
        model=model,
    )