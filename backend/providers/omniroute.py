"""OmniRoute provider implementation with retry, caching, and tracking."""
import base64
import hashlib
import json
import time
from typing import Any

from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.core.exceptions import ProviderException
from backend.core.logging import get_logger
from backend.providers.base import Provider, ProviderConfig

logger = get_logger(__name__)


class OmniRouteProvider(Provider):
    """OmniRoute provider with OpenAI-compatible client."""

    def __init__(self, config: ProviderConfig | None = None):
        """Initialize OmniRoute provider.

        Args:
            config: Provider configuration. Uses settings if None.
        """
        if config is None:
            config = ProviderConfig(
                base_url=settings.omniroute_base_url,
                api_key=settings.omniroute_api_key,
                timeout=settings.provider_timeout_seconds,
                max_retries=settings.provider_max_retries,
            )

        self.config = config
        self.client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
        )
        # TODO: Initialize cache and tracker
        logger.info("omniroute_provider_initialized", base_url=config.base_url)

    def _cache_key(self, *args: Any) -> str:
        """Generate cache key from arguments."""
        content = json.dumps(args, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        model: str,
        system: str | None = None,
        json_mode: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate text from prompt with retry logic.

        Args:
            prompt: User prompt
            model: Model ID
            system: System prompt
            json_mode: Force JSON output
            **kwargs: Additional parameters

        Returns:
            Dict with 'text', 'usage', 'latency_ms'

        Raises:
            ProviderException: If generation fails after retries
        """
        start = time.time()

        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            params = {"model": model, "messages": messages, **kwargs}

            if json_mode:
                params["response_format"] = {"type": "json_object"}

            logger.info(
                "omniroute_generate_request",
                model=model,
                prompt_length=len(prompt),
                json_mode=json_mode,
            )

            response = await self.client.chat.completions.create(**params)

            latency_ms = (time.time() - start) * 1000

            result = {
                "text": response.choices[0].message.content or "",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens
                    if response.usage
                    else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                "latency_ms": latency_ms,
                "model": model,
            }

            logger.info(
                "omniroute_generate_success",
                model=model,
                latency_ms=latency_ms,
                tokens=result["usage"]["total_tokens"],
            )

            return result

        except Exception as e:
            logger.error("omniroute_generate_error", model=model, error=str(e))
            raise ProviderException(f"Generation failed: {str(e)}") from e

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        """Generate embeddings.

        Args:
            texts: List of texts to embed
            model: Embedding model ID

        Returns:
            List of embedding vectors

        Raises:
            ProviderException: If embedding fails
        """
        start = time.time()

        try:
            logger.info("omniroute_embed_request", model=model, num_texts=len(texts))

            response = await self.client.embeddings.create(model=model, input=texts)

            latency_ms = (time.time() - start) * 1000

            embeddings = [item.embedding for item in response.data]

            logger.info(
                "omniroute_embed_success",
                model=model,
                num_texts=len(texts),
                latency_ms=latency_ms,
            )

            return embeddings

        except Exception as e:
            logger.error("omniroute_embed_error", model=model, error=str(e))
            raise ProviderException(f"Embedding failed: {str(e)}") from e

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def recognize(
        self, image_bytes: bytes, prompt: str, model: str, **kwargs
    ) -> dict[str, Any]:
        """Vision-language model recognition.

        Args:
            image_bytes: Image data
            prompt: Recognition prompt
            model: VLM model ID
            **kwargs: Additional parameters

        Returns:
            Dict with 'text', 'confidence', 'usage', 'latency_ms'

        Raises:
            ProviderException: If recognition fails
        """
        start = time.time()

        try:
            # Encode image as base64
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            logger.info(
                "omniroute_recognize_request",
                model=model,
                image_size_kb=len(image_bytes) / 1024,
            )

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                            },
                        ],
                    }
                ],
                **kwargs,
            )

            latency_ms = (time.time() - start) * 1000

            result = {
                "text": response.choices[0].message.content or "",
                "confidence": 0.5,  # Placeholder - will be calibrated
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens
                    if response.usage
                    else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                "latency_ms": latency_ms,
                "model": model,
            }

            logger.info(
                "omniroute_recognize_success",
                model=model,
                latency_ms=latency_ms,
                text_length=len(result["text"]),
            )

            return result

        except Exception as e:
            logger.error("omniroute_recognize_error", model=model, error=str(e))
            raise ProviderException(f"Recognition failed: {str(e)}") from e
