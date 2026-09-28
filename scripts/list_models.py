"""Script to list available models from OmniRoute."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AsyncOpenAI
from backend.core.config import settings
from backend.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def list_models():
    """Query and display available models from OmniRoute."""
    client = AsyncOpenAI(
        base_url=settings.omniroute_base_url,
        api_key=settings.omniroute_api_key,
    )

    try:
        logger.info("Querying OmniRoute for available models...")
        models = await client.models.list()

        print("\n" + "=" * 80)
        print("AVAILABLE MODELS FROM OMNIROUTE")
        print("=" * 80 + "\n")

        # Group models by type
        text_models = []
        vision_models = []
        embedding_models = []
        other_models = []

        for model in models.data:
            model_id = model.id
            if "vision" in model_id.lower() or "gpt-4" in model_id.lower():
                vision_models.append(model_id)
            elif "embedding" in model_id.lower() or "ada" in model_id.lower():
                embedding_models.append(model_id)
            elif any(
                x in model_id.lower()
                for x in ["gpt", "claude", "llama", "mistral", "gemini", "qwen"]
            ):
                text_models.append(model_id)
            else:
                other_models.append(model_id)

        if text_models:
            print("TEXT MODELS (for chat, translation, correction):")
            for model in sorted(text_models):
                print(f"  • {model}")
            print()

        if vision_models:
            print("VISION MODELS (for VLM OCR):")
            for model in sorted(vision_models):
                print(f"  • {model}")
            print()

        if embedding_models:
            print("EMBEDDING MODELS (for search):")
            for model in sorted(embedding_models):
                print(f"  • {model}")
            print()

        if other_models:
            print("OTHER MODELS:")
            for model in sorted(other_models):
                print(f"  • {model}")
            print()

        print("=" * 80)
        print(f"\nTotal models available: {len(models.data)}")
        print("\nUpdate config/models.yaml with the model IDs you want to use.")
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        print(f"\nERROR: {e}")
        print("\nPlease check:")
        print("  1. Your .env file has OMNIROUTE_API_KEY set correctly")
        print("  2. Your OMNIROUTE_BASE_URL is correct")
        print(f"  3. Current API key starts with: {settings.omniroute_api_key[:20]}...")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(list_models())
