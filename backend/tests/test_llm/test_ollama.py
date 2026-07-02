from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.llm.providers.ollama import OllamaProvider
from backend.utils.exceptions import LLMError


@pytest.mark.asyncio
async def test_ollama_generate_success():
    provider = OllamaProvider()

    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "Hello World"}}

    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await provider.generate(
            model="llama3.1:8b", messages=[{"role": "user", "content": "Hi"}]
        )

        assert result == "Hello World"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "llama3.1:8b"
        assert kwargs["json"]["stream"] is False


@pytest.mark.asyncio
async def test_ollama_generate_http_error():
    provider = OllamaProvider()

    with patch.object(provider.client, "post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )

        with pytest.raises(LLMError) as exc:
            await provider.generate(model="test", messages=[])

        assert exc.value.error_code == "OLLAMA_HTTP_ERROR"
