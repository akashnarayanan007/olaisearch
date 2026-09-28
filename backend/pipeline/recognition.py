"""Tesseract OCR integration for the vertical slice."""
import io
from typing import List, Optional
import pytesseract
from PIL import Image
import numpy as np

from backend.core.logging import get_logger
from backend.core.models import OCRResult, OCRAlternative
from backend.core.exceptions import OCRException

logger = get_logger(__name__)


class TesseractRecognizer:
    """Tesseract OCR recognizer with Indic language support."""

    def __init__(self, languages: Optional[List[str]] = None):
        """Initialize Tesseract recognizer.

        Args:
            languages: List of Tesseract language codes (e.g., ['tam', 'mal', 'san'])
                      Defaults to Tamil, Malayalam, Sanskrit
        """
        self.languages = languages or ['tam', 'mal', 'san', 'eng']
        self.lang_string = '+'.join(self.languages)
        logger.info("tesseract_initialized", languages=self.languages)

    def recognize_line(self, image: np.ndarray) -> OCRResult:
        """Recognize text from a line image.

        Args:
            image: Line image as numpy array (H, W, 3) or (H, W)

        Returns:
            OCRResult with text and confidence

        Raises:
            OCRException: If OCR fails
        """
        try:
            # Convert numpy array to PIL Image
            if len(image.shape) == 2:
                pil_image = Image.fromarray(image)
            else:
                pil_image = Image.fromarray(image.astype('uint8'))

            # Get detailed OCR data
            data = pytesseract.image_to_data(
                pil_image,
                lang=self.lang_string,
                output_type=pytesseract.Output.DICT
            )

            # Extract text and confidences
            words = []
            confidences = []
            for i in range(len(data['text'])):
                word = data['text'][i].strip()
                conf = int(data['conf'][i])
                if word and conf > 0:  # Filter empty and failed recognitions
                    words.append(word)
                    confidences.append(conf / 100.0)  # Normalize to 0-1

            text = ' '.join(words)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(
                "tesseract_recognition_success",
                text_length=len(text),
                confidence=avg_confidence,
                num_words=len(words)
            )

            return OCRResult(
                text=text,
                confidence=avg_confidence,
                char_confidences=[],  # TODO: Compute per-character confidences
                alternatives=[],  # Tesseract doesn't provide alternatives easily
                recognizer="tesseract",
                processing_time_ms=0  # Will be set by caller
            )

        except Exception as e:
            logger.error("tesseract_recognition_error", error=str(e))
            raise OCRException(f"Tesseract recognition failed: {str(e)}") from e

    def recognize_page(self, image_bytes: bytes) -> str:
        """Recognize all text from a full page image.

        Args:
            image_bytes: Image bytes (JPG/PNG)

        Returns:
            Recognized text

        Raises:
            OCRException: If OCR fails
        """
        try:
            # Open image
            pil_image = Image.open(io.BytesIO(image_bytes))

            # Run OCR
            text = pytesseract.image_to_string(
                pil_image,
                lang=self.lang_string
            )

            logger.info(
                "tesseract_page_recognition_success",
                text_length=len(text)
            )

            return text.strip()

        except Exception as e:
            logger.error("tesseract_page_recognition_error", error=str(e))
            raise OCRException(f"Tesseract page recognition failed: {str(e)}") from e
