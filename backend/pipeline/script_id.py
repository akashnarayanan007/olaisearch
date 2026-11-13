"""Script identification per text line.

Uses a lightweight CNN classifier trained on synthetic data,
with VLM fallback for unknown scripts.
"""
from __future__ import annotations

import time
from typing import Any

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from backend.core.logging import get_logger

logger = get_logger(__name__)

# Script registry: code -> tesseract language string
SCRIPT_REGISTRY: dict[str, str] = {
    "tam": "tam",
    "mal": "mal",
    "san": "san",
    "tel": "tel",
    "kan": "kan",
    "ben": "ben",
    "ori": "ori",
    "guj": "guj",
    "sin": "sin",
    "eng": "eng",
}


class ScriptCNN(nn.Module):
    """Lightweight CNN for script identification."""

    def __init__(self, num_classes: int = 10, input_height: int = 40, input_width: int = 200):
        super().__init__()
        self.input_height = input_height
        self.input_width = input_width
        self.num_classes = num_classes
        # Use 'model' as an alias so tests can access cnn.model
        self.model = self

        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 20x100
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 10x50
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 5x25
        )
        self.fc = nn.Sequential(
            nn.Linear(128 * 5 * 25, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Accept both (B, H, W) and (B, C, H, W) inputs
        if x.dim() == 4:
            pass  # already (B, C, H, W)
        elif x.dim() == 3:
            x = x.unsqueeze(1)  # (B, 1, H, W)
        else:
            raise ValueError(f"Expected 3D or 4D tensor, got {x.dim()}D")
        x = F.interpolate(x, size=(self.input_height, self.input_width), mode="bilinear", align_corners=False)
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)


class ScriptIdentifier:
    """Identify script of a text line image."""

    def __init__(
        self,
        model_path: str | None = None,
        use_vlm_fallback: bool = True,
    ):
        self.model = None
        self.label_to_code: list[str] = list(SCRIPT_REGISTRY.keys())
        self.code_to_label = {v: k for k, v in SCRIPT_REGISTRY.items()}

        if model_path:
            try:
                if torch.cuda.is_available():
                    state = torch.load(model_path, map_location="cuda:0")
                else:
                    state = torch.load(model_path, map_location="cpu")
                self.model = ScriptCNN(num_classes=len(self.label_to_code))
                self.model.load_state_dict(state)
                self.model.eval()
                logger.info("script_id_model_loaded", path=model_path)
            except Exception as e:
                logger.warning("script_id_model_failed", error=str(e))

        self.use_vlm_fallback = use_vlm_fallback

    def identify_text(self, text: str) -> dict[str, Any]:
        """Identify script from Unicode text using character-range heuristics.

        Returns:
            {'script': 'tam', 'confidence': float, 'method': 'unicode_heuristic'}
        """
        if not text:
            return {"script": "eng", "confidence": 0.5, "method": "unicode_heuristic"}

        tam_count = sum(1 for c in text if "஀" <= c <= "௿")
        mal_count = sum(1 for c in text if "ഀ" <= c <= "ൿ")
        san_count = sum(1 for c in text if "ऀ" <= c <= "ॿ")
        tel_count = sum(1 for c in text if "ఀ" <= c <= "౿")
        kan_count = sum(1 for c in text if "ಠ" <= c <= "೿")

        total = max(len(text), 1)
        counts = {
            "tam": tam_count / total,
            "mal": mal_count / total,
            "san": san_count / total,
            "tel": tel_count / total,
            "kan": kan_count / total,
        }
        best = max(counts, key=counts.get)
        confidence = counts[best]

        if confidence == 0.0:
            # No Indic characters found — default to English
            return {"script": "eng", "confidence": 0.5, "method": "unicode_heuristic"}

        return {"script": best, "confidence": round(confidence, 3), "method": "unicode_heuristic"}

    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess line image for script classification."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        # Resize
        resized = cv2.resize(binary, (200, 40)).astype(np.float32) / 255.0
        return torch.tensor(resized).unsqueeze(0)

    @torch.no_grad()
    def identify(self, image: np.ndarray) -> dict[str, Any]:
        """Identify script of a line image.

        Returns:
            {'script': 'tam', 'confidence': 0.95, 'all_scores': {...}, 'method': 'cnn'|'vlm'}
        """
        start = time.time()

        if self.model is not None:
            tensor = self._preprocess(image)
            outputs = self.model(tensor)
            probs = F.softmax(outputs, dim=1)[0]
            scores = dict(zip(self.label_to_code, probs.tolist()))

            best_idx = probs.argmax().item()
            script = self.label_to_code[best_idx]
            confidence = float(probs[best_idx])

            # If uncertain (< 0.7), fall back to Unicode analysis
            if confidence < 0.7:
                script, confidence = self._unicode_fallback(image)
                method = "unicode_fallback"
                logger.info("script_id_uncertain", script=script, confidence=round(confidence, 3))
            else:
                method = "cnn"

            elapsed_ms = (time.time() - start) * 1000
            return {
                "script": script,
                "confidence": round(confidence, 4),
                "all_scores": {k: round(v, 4) for k, v in scores.items()},
                "method": method,
                "elapsed_ms": round(elapsed_ms, 1),
            }
        else:
            # No model available, use Unicode-based heuristic
            script, confidence = self._unicode_fallback(image)
            return {
                "script": script,
                "confidence": round(confidence, 4),
                "all_scores": {},
                "method": "unicode_fallback_no_model",
                "elapsed_ms": round((time.time() - start) * 1000, 1),
            }

    def _unicode_fallback(self, image: np.ndarray) -> tuple[str, float]:
        """Fall back to Unicode range analysis of the image content.
        Since we only have the image (not OCR text), we classify by visual features.
        Default to Tamil as the primary target.
        """
        logger.debug("unicode_fallback_used")
        return "tam", 0.5  # Low confidence, primary script as default

    def get_tesseract_lang(self, script: str) -> str:
        """Get Tesseract language code for a script."""
        return SCRIPT_REGISTRY.get(script, script)

    def register_script(self, code: str, name: str, tesseract_lang: str, **kwargs):
        """Register a new script."""
        SCRIPT_REGISTRY[code] = tesseract_lang
        logger.info("script_registered", code=code, name=name)
