"""Test the provider abstraction layer."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.core.exceptions import ProviderException
from backend.providers.base import ProviderConfig
from backend.providers.omniroute import OmniRouteProvider


@pytest.fixture
def provider_config():
    """Create test provider config."""
    return ProviderConfig(
        base_url="https://test.api.com/v1",
        api_key="test_key",
        timeout=30,
        max_retries=2,
    )


@pytest.fixture
def provider(provider_config):
    """Create OmniRoute provider instance."""
    return OmniRouteProvider(provider_config)


@pytest.mark.asyncio
async def test_generate_success(provider):
    """Test successful text generation."""
    # Mock OpenAI client response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Generated text"))]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

    provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await provider.generate(
        prompt="Test prompt",
        model="test-model"
    )

    assert result["text"] == "Generated text"
    assert result["usage"]["total_tokens"] == 30
    assert "latency_ms" in result
    assert result["model"] == "test-model"


@pytest.mark.asyncio
async def test_generate_with_system_prompt(provider):
    """Test generation with system prompt."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)

    provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await provider.generate(
        prompt="User prompt",
        model="test-model",
        system="System instruction"
    )

    assert result["text"] == "Response"

    # Verify system message was included
    call_args = provider.client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


@pytest.mark.asyncio
async def test_generate_json_mode(provider):
    """Test JSON mode generation."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"key": "value"}'))]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)

    provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await provider.generate(
        prompt="Generate JSON",
        model="test-model",
        json_mode=True
    )

    assert result["text"] == '{"key": "value"}'

    # Verify JSON format was requested
    call_args = provider.client.chat.completions.create.call_args
    assert call_args[1]["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_generate_failure(provider):
    """Test generation failure raises ProviderException."""
    provider.client.chat.completions.create = AsyncMock(
        side_effect=Exception("API error")
    )

    with pytest.raises(ProviderException) as exc_info:
        await provider.generate(prompt="Test", model="test-model")

    assert "Generation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_embed_success(provider):
    """Test successful embedding generation."""
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(embedding=[0.1, 0.2, 0.3]),
        MagicMock(embedding=[0.4, 0.5, 0.6]),
    ]

    provider.client.embeddings.create = AsyncMock(return_value=mock_response)

    embeddings = await provider.embed(
        texts=["text 1", "text 2"],
        model="test-embed-model"
    )

    assert len(embeddings) == 2
    assert embeddings[0] == [0.1, 0.2, 0.3]
    assert embeddings[1] == [0.4, 0.5, 0.6]


@pytest.mark.asyncio
async def test_cache_key_generation(provider):
    """Test cache key generation is consistent."""
    key1 = provider._cache_key("test", "args", {"param": "value"})
    key2 = provider._cache_key("test", "args", {"param": "value"})
    key3 = provider._cache_key("test", "different", {"param": "value"})

    assert key1 == key2  # Same inputs produce same key
    assert key1 != key3  # Different inputs produce different key
    assert len(key1) == 64  # SHA256 hex digest length
