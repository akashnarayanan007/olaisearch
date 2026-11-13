"""Core data models."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(UTC)


class BoundingBox(BaseModel):
    """Bounding box coordinates."""

    x: int
    y: int
    width: int
    height: int


class OCRAlternative(BaseModel):
    """Alternative OCR reading."""

    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class OCRResult(BaseModel):
    """OCR recognition result."""

    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    char_confidences: list[float] = Field(default_factory=list)
    alternatives: list[OCRAlternative] = Field(default_factory=list)
    recognizer: str = "unknown"
    processing_time_ms: float = 0.0


class Line(BaseModel):
    """Text line in a manuscript."""

    id: str
    text: str
    bbox: BoundingBox
    confidence: float = Field(ge=0.0, le=1.0)
    script: str | None = None
    alternatives: list[OCRAlternative] = Field(default_factory=list)
    char_confidences: list[float] = Field(default_factory=list)
    ocr: OCRResult | None = None


class Manuscript(BaseModel):
    """Palm-leaf manuscript."""

    id: str
    image_path: str
    restored_image_path: str | None = None
    language: str
    script: str
    lines: list[Line] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class SearchResult(BaseModel):
    """Search result."""

    manuscript_id: str
    line_id: str
    text: str
    score: float
    bbox: BoundingBox
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """Citation in chat response."""

    tier: str  # "manuscript", "archive", "background"
    manuscript_id: str | None = None
    line_id: str | None = None
    text: str
    bbox: BoundingBox | None = None
    confidence: float | None = None


class ChatResponse(BaseModel):
    """ManuscriptChat response."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_tiers_used: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)

    @property
    def response(self) -> str:
        """Alias for ``answer`` to support attribute-style access."""
        return self.answer
