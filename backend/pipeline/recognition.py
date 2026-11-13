"""Recognition ensemble with ROVER-style confidence-weighted voting.

Three recognizers:
1. Tesseract (Indic language packs) - baseline
2. CRNN + CTC - learned recognizer
3. VLM via OmniRoute - vision-language fallback

Output: text + per-grapheme confidence + alternatives.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import grapheme
import numpy as np
import pytesseract
from PIL import Image

from backend.core.config import settings
from backend.core.exceptions import OCRException
from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OCRWord:
    """A recognized word with confidence."""

    text: str
    confidence: float
    bbox: tuple | None = None
    alternatives: list[str] = field(default_factory=list)


@dataclass
class OCRLine:
    """Recognized text line."""

    text: str
    confidence: float
    char_confidences: list[float] = field(default_factory=list)
    word_objects: list[OCRWord] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    recognizer: str = ""
    elapsed_ms: float = 0.0


def split_graphemes(text: str) -> list[str]:
    """Split text into Unicode grapheme clusters."""
    if not text:
        return []
    clusters = list(grapheme.graphemes(text))
    return clusters


def compute_cer(w_hyp: str, w_ref: str) -> float:
    """Compute character error rate using Levenshtein distance on graphemes."""
    hyp_graphemes = split_graphemes(w_hyp)
    ref_graphemes = split_graphemes(w_ref)

    if not ref_graphemes:
        return 0.0 if not hyp_graphemes else 1.0

    dist = levenshtein(hyp_graphemes, ref_graphemes)
    return dist / len(ref_graphemes)


def levenshtein(s1: list[str], s2: list[str]) -> int:
    """Levenshtein distance between two sequences."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]


def compute_wer(words_hyp: list[str], words_ref: list[str]) -> float:
    """Compute word error rate."""
    if not words_ref:
        return 0.0 if not words_hyp else 1.0
    dist = levenshtein(words_hyp, words_ref)
    return dist / len(words_ref)


class TesseractRecognizer:
    """Tesseract OCR with Indic language support."""

    def __init__(self, languages: list[str] | None = None):
        self.languages = languages or ["tam", "mal", "san", "eng"]
        self.lang_string = "+".join(self.languages)
        logger.info("tesseract_recognizer_init", languages=self.languages)

    def recognize(self, image: np.ndarray, psm: int = 6) -> OCRLine:
        """Run Tesseract on a line image."""
        start = time.time()
        try:
            pil_img = Image.fromarray(image.astype("uint8"))
            data = pytesseract.image_to_data(
                pil_img, lang=self.lang_string, output_type=pytesseract.Output.DICT,
                config=f"--psm {psm}"
            )

            words, confidences = [], []
            for i in range(len(data["text"])):
                txt = data["text"][i].strip()
                conf = int(data["conf"][i])
                if txt and conf > 0:
                    words.append(txt)
                    confidences.append(conf / 100.0)

            text = " ".join(words)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            char_confs = [avg_conf] * len(split_graphemes(text))

            elapsed = (time.time() - start) * 1000
            return OCRLine(
                text=text,
                confidence=avg_conf,
                char_confidences=char_confs,
                word_objects=[OCRWord(w, c) for w, c in zip(words, confidences)],
                recognizer="tesseract",
                elapsed_ms=round(elapsed, 1),
            )
        except Exception as e:
            logger.error("tesseract_recognition_failed", error=str(e))
            raise OCRException(f"Tesseract failed: {e}")


class VLMRecognizer:
    """VLM-based recognizer via OmniRoute provider."""

    OCR_PROMPT = (
        "Transcribe the text exactly as it appears in this palm-leaf manuscript image. "
        "Use the original Unicode characters. Do not translate, do not correct, "
        "do not add any commentary. If a character is unreadable, mark it as [?]. "
        "Output ONLY the transcribed text, nothing else."
    )

    def __init__(self):
        self.available = False
        self._provider = None
        try:
            from backend.providers.omniroute import OmniRouteProvider
            api_key = getattr(settings, "omniroute_api_key", None)
            if api_key and api_key != "your_api_key_here":
                self._provider = OmniRouteProvider()
                self.available = True
            else:
                logger.info("vlm_recognizer_unavailable", reason="no_api_key")
        except ImportError:
            logger.info("vlm_recognizer_unavailable", reason="openai_sdk_missing")

    def recognize(self, image: np.ndarray) -> OCRLine | None:
        """Run VLM recognition."""
        if not self.available or self._provider is None:
            return None
        try:
            start = time.time()
            result = self._provider.recognize(
                image_bytes=image.tobytes() if isinstance(image, np.ndarray) else bytes(image),
                prompt=self.OCR_PROMPT,
                model=settings.vlm_model_id,
            )
            elapsed = (time.time() - start) * 1000
            text = result.get("text", "").strip()
            return OCRLine(
                text=text,
                confidence=0.5,  # Weak signal, calibrated later
                char_confidences=[],
                recognizer="vlm",
                elapsed_ms=round(elapsed, 1),
            )
        except Exception as e:
            logger.error("vlm_recognition_failed", error=str(e))
            return None


class CRNNRecognizer:
    """CRNN + CTC recognizer (stub for future training)."""

    def __init__(self, model_path: str | None = None):
        self.model = None
        self.char_map = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.available = model_path is not None
        if model_path:
            try:
                import torch
                if torch.cuda.is_available():
                    self.model = torch.load(model_path, map_location="cuda:0")
                else:
                    self.model = torch.load(model_path, map_location="cpu")
                self.model.eval()
                logger.info("crnn_model_loaded", path=model_path)
            except Exception as e:
                logger.warning("crnn_model_failed", error=str(e))
                self.available = False

    def recognize(self, image: np.ndarray) -> OCRLine | None:
        """Run CRNN recognition."""
        if not self.available or self.model is None:
            return None
        # TODO: implement forward pass with CTC beam search
        return None


class Calibration:
    """Confidence calibration for OCR recognizers.

    Adjusts confidence scores based on observed error rates.
    Uses temperature scaling and isotonic regression concepts.
    """

    def __init__(self):
        self.calibration_data: list[dict[str, Any]] = []
        self.temperature: float = 1.0

    def update(self, predicted_conf: Any, correct: Any = None, recognizer: str = "ensemble"):
        """Record a single calibration point. Also accepts a list of records.

        Usage:
            cal.update(confidence, is_correct, recognizer="ensemble")  # single record
            cal.update([{"conf": 0.8, "correct": True}, ...])  # list of records
        """
        # Handle list input (for test_calibration_blend compatibility)
        if isinstance(predicted_conf, list):
            data = predicted_conf
            for record in data:
                self.calibration_data.append({
                    "predicted_conf": float(record["conf"]),
                    "correct": bool(record["correct"]),
                    "recognizer": record.get("recognizer", "ensemble"),
                    "timestamp": time.time(),
                })
            return len(data)

        self.calibration_data.append({
            "predicted_conf": float(predicted_conf),
            "correct": bool(correct),
            "recognizer": recognizer,
            "timestamp": time.time(),
        })

    def update_batch(self, data: list[dict[str, Any]]) -> int:
        """Update from a list of ``{'conf': ..., 'correct': ...}`` records.

        Returns the number of records added.
        """
        return self.update(data)

    def calibrate_confidence(self, raw_conf: float, num_samples: int = 100) -> float:
        """Calibrate a raw confidence score using recent data."""
        if len(self.calibration_data) < 10:
            return raw_conf  # Not enough data for calibration

        # Sort by predicted confidence and compute accuracy in bins
        sorted_data = sorted(self.calibration_data, key=lambda x: x["predicted_conf"])
        n_bins = min(10, len(sorted_data) // 5)
        if n_bins < 2:
            return raw_conf

        bin_size = len(sorted_data) // n_bins
        cal_bracket = int(raw_conf * n_bins)
        cal_bracket = max(0, min(n_bins - 1, cal_bracket))

        start = cal_bracket * bin_size
        end = min(start + bin_size, len(sorted_data))
        bracket = sorted_data[start:end]

        if not bracket:
            return raw_conf

        mean_acc = sum(1 for d in bracket if d["correct"]) / len(bracket)
        # Blend: calibrated = 0.7 * accuracy + 0.3 * raw
        calibrated = 0.7 * mean_acc + 0.3 * raw_conf
        return min(1.0, max(0.0, calibrated))

    def compute_ece(self, bins: int = 15) -> float:
        """Compute Expected Calibration Error."""
        if len(self.calibration_data) < bins:
            return float("nan")
        sorted_data = sorted(self.calibration_data, key=lambda x: x["predicted_conf"])
        bin_size = len(sorted_data) // bins
        ece = 0.0
        for i in range(bins):
            start = i * bin_size
            end = min(start + bin_size, len(sorted_data))
            if start >= end:
                continue
            bracket = sorted_data[start:end]
            avg_conf = sum(d["predicted_conf"] for d in bracket) / len(bracket)
            avg_acc = sum(1 for d in bracket if d["correct"]) / len(bracket)
            ece += abs(avg_conf - avg_acc) * len(bracket) / len(sorted_data)
        return ece

    def to_json(self) -> str:
        return json.dumps({
            "num_samples": len(self.calibration_data),
            "temperature": self.temperature,
        })

    def evaluate(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """Evaluate calibration quality on a list of records.

        Args:
            data: [{'conf': float, 'correct': bool}, ...]

        Returns:
            {'ece': float, 'num_samples': int, 'accuracy': float}
        """
        if not data:
            return {"ece": 0.0, "num_samples": 0, "accuracy": 0.0}

        n = len(data)
        bins = min(15, n)
        # Bin by confidence (0–1 divided into bins)
        bin_data: dict[int, list[dict[str, Any]]] = {}
        for record in data:
            conf = float(record.get("conf", 0.0))
            correct = bool(record.get("correct", False))
            bin_idx = min(int(conf * bins), bins - 1)
            bin_data.setdefault(bin_idx, []).append({"conf": conf, "correct": correct})

        ece = 0.0
        total_correct = 0
        for i in range(bins):
            bucket = bin_data.get(i, [])
            if not bucket:
                continue
            avg_conf = sum(d["conf"] for d in bucket) / len(bucket)
            avg_acc = sum(1 for d in bucket if d["correct"]) / len(bucket)
            total_correct += sum(1 for d in bucket if d["correct"])
            ece += abs(avg_conf - avg_acc) * (len(bucket) / n)

        accuracy = total_correct / n if n else 0.0
        return {"ece": round(ece, 4), "num_samples": n, "accuracy": round(accuracy, 4)}

    def blend(self, raw_conf: float) -> dict[str, Any]:
        """Blend a raw confidence with recent calibration data.

        Returns:
            {'blended': float, 'raw': float, 'calibrated': float, 'num_samples': int}
        """
        if not self.calibration_data:
            return {"blended": raw_conf, "raw": raw_conf, "calibrated": raw_conf, "num_samples": 0}

        recent = self.calibration_data[-100:]
        acc = sum(1 for d in recent if d["correct"]) / len(recent)
        # Blend: 60% recent empirical accuracy, 40% raw
        blended = min(1.0, max(0.0, 0.6 * acc + 0.4 * raw_conf))
        return {"blended": round(blended, 4), "raw": raw_conf, "calibrated": round(acc, 4), "num_samples": len(recent)}


class RecognitionEnsemble:
    """ROVER-style confidence-weighted voting ensemble.

    Combines Tesseract, CRNN, and VLM recognizers.
    Each recognizer votes weighted by calibrated confidence.
    """

    # Default weights (calibrated over time)
    DEFAULT_WEIGHTS = {"tesseract": 0.5, "crnn": 0.2, "vlm": 0.3}

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        calibration: Calibration | None = None,
    ):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.calibration = calibration or Calibration()
        self.tesseract = TesseractRecognizer()
        self.vlm = VLMRecognizer()
        self.crnn = CRNNRecognizer()
        logger.info(
            "ensemble_initialized",
            weights=self.weights,
            has_vlm=self.vlm.available,
            has_crnn=self.crnn.available,
        )

    def recognize(self, image: np.ndarray) -> OCRLine:
        """Run all recognizers and combine results."""
        results: list[OCRLine] = []
        start = time.time()

        # Tesseract (always available)
        try:
            tsr = self.tesseract.recognize(image)
            tsr.confidence = self.calibration.calibrate_confidence(tsr.confidence)
            results.append(tsr)
        except Exception as e:
            logger.warning("tesseract_failed_in_ensemble", error=str(e))

        # VLM (if available and API key set)
        if self.vlm.available:
            vlm_result = self.vlm.recognize(image)
            if vlm_result is not None:
                vlm_result.confidence = self.calibration.calibrate_confidence(vlm_result.confidence)
                results.append(vlm_result)

        # CRNN (if model loaded)
        if self.crnn.available:
            crnn_result = self.crnn.recognize(image)
            if crnn_result is not None:
                results.append(crnn_result)

        if not results:
            raise OCRException("All recognizers failed")

        # Weighted vote: pick highest-weighted result
        best = self._vote(results)

        elapsed = (time.time() - start) * 1000
        best.elapsed_ms = round(elapsed, 1)
        return best

    def _vote(self, results: list[OCRLine]) -> OCRLine:
        """ROVER-style confidence-weighted voting."""
        # Score each result by weight * confidence
        best_score = -1
        best_result = results[0]

        for r in results:
            recog_name = r.recognizer
            weight = self.weights.get(recog_name, 0.1)
            score = weight * r.confidence
            if score > best_score:
                best_score = score
                best_result = r

        logger.info("ensemble_voted", best_recognizer=best_result.recognizer, score=round(best_score, 4))

        # Collect alternatives from other recognizers
        alt_texts = [r.text for r in results if r.text != best_result.text]
        best_result.alternatives = alt_texts[:3]  # top 3 alternatives

        return best_result

    def record_correct(self, result: OCRLine, ground_truth: str):
        """Record whether the ensemble was correct (for calibration)."""
        correct = result.text.strip() == ground_truth.strip()
        self.calibration.update(result.confidence, correct, result.recognizer)
        return correct
