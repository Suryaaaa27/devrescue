from unittest.mock import MagicMock

from agent.llm.client import OpenAICompatibleClient


def test_openai_compatible_client_uses_configured_endpoint():

    client = OpenAICompatibleClient(
        base_url="http://localhost:8081/v1",
        api_key="test-key",
        model="gemini-3.5-flash-thinking",
    )

    client.client = MagicMock()

    client.client.chat.completions.create.return_value = (
        MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"result": "ok"}'
                    )
                )
            ]
        )
    )

    result = client.generate(
        system_prompt="You are a test assistant.",
        user_prompt="Return JSON.",
    )

    assert result == {
        "result": "ok"
    }

    client.client.chat.completions.create.assert_called_once()

    call = (
        client.client
        .chat
        .completions
        .create
        .call_args
    )

    assert call.kwargs["model"] == (
        "gemini-3.5-flash-thinking"
    )

    assert call.kwargs["messages"][0]["role"] == "system"
    assert call.kwargs["messages"][1]["role"] == "user"


def test_client_rejects_invalid_json():

    client = OpenAICompatibleClient(
        base_url="http://localhost:8081/v1",
        api_key="test-key",
        model="gemini-3.5-flash-thinking",
    )

    client.client = MagicMock()

    client.client.chat.completions.create.return_value = (
        MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="not valid json"
                    )
                )
            ]
        )
    )

    try:
        client.generate(
            system_prompt="system",
            user_prompt="user",
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "invalid JSON" in str(exc)
        
def test_client_rejects_markdown_response():

    client = OpenAICompatibleClient(
        base_url="http://localhost:8081/v1",
        api_key="test-key",
        model="gemini-3.5-flash-thinking",
    )

    client.client = MagicMock()

    client.client.chat.completions.create.return_value = (
        MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content=(
                            "## Conclusion\n"
                            "Invalid payment input\n"
                        )
                    )
                )
            ]
        )
    )

    try:
        client.generate(
            system_prompt="system",
            user_prompt="user",
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "invalid JSON" in str(exc)