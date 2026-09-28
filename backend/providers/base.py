"""Provider abstraction layer base classes."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for a provider."""

    base_url: str
    api_key: str
    timeout: int = 120
    max_retries: int = 3


class Provider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        json_mode: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate text from prompt.

        Args:
            prompt: User prompt
            model: Model ID
            system: System prompt
            json_mode: Force JSON output
            **kwargs: Additional model parameters

        Returns:
            Dict with 'text', 'usage', 'latency_ms'
        """
        pass

    @abstractmethod
    async def embed(self, texts: List[str], model: str) -> List[List[float]]:
        """Generate embeddings.

        Args:
            texts: List of texts to embed
            model: Embedding model ID

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def recognize(
        self, image_bytes: bytes, prompt: str, model: str, **kwargs
    ) -> Dict[str, Any]:
        """Vision-language model recognition.

        Args:
            image_bytes: Image data
            prompt: Recognition prompt
            model: VLM model ID
            **kwargs: Additional parameters

        Returns:
            Dict with 'text', 'confidence', 'usage', 'latency_ms'
        """
        pass
