"""Post-correction module: lexicon correction, transliteration, translation,
entity extraction, date normalisation, and domain glossary."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from backend.core.logging import get_logger

logger = get_logger(__name__)

# Era offsets relative to CE (positive = era starts after CE 0, negative = before)
_ERA_OFFSETS: Dict[str, int] = {
    "saka": 78,       # Saka era started in 78 CE
    "kali": -3101,    # Kali Yuga started ~3102 BCE
    "tamil": 8,       # Tamil era ~ 8 CE
    "chola": 476,     # Chola era ~ 476 CE
    "vijayanagara": 1454,
}

# Minimum edit distance threshold for lexicon match
_LEX_DISTANCE_THRESHOLD = 0.35


# ─── Lexicon Corrector ─────────────────────────────────────────────────────────

class LexiconCorrector:
    """Correct OCR text using a small domain lexicon via Levenshtein distance."""

    def __init__(self, threshold: float = _LEX_DISTANCE_THRESHOLD) -> None:
        self.threshold = threshold

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        m, n = len(a), len(b)
        if m == 0:
            return n
        if n == 0:
            return m
        dp = list(range(n + 1))
        for i in range(1, m + 1):
            prev = dp[0]
            dp[0] = i
            for j in range(1, n + 1):
                tmp = dp[j]
                cost = 0 if a[i - 1] == b[j - 1] else 1
                dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
                prev = tmp
        return dp[n]

    def correct(
        self,
        text: str,
        lexicon: Optional[Set[str]] = None,
        script: str = "tam",
    ) -> Dict[str, Any]:
        """Return corrected text and list of applied corrections.

        Args:
            text: OCR output to correct.
            lexicon: Set of reference words; correction is skipped if empty.
            script: Indic script code (used for context, not currently).

        Returns:
            {"text": str, "diffs": [{"original": str, "corrected": str}, ...]}
        """
        if not lexicon:
            return {"text": text, "diffs": []}

        words = text.split()
        diffs: List[Dict[str, str]] = []
        corrected_words: List[str] = []

        for word in words:
            best_word = word
            best_dist = len(word) + 1  # worse than identity
            for lex_word in lexicon:
                d = self._levenshtein(word, lex_word)
                # Normalise by max length so short words aren't over-corrected
                norm = d / max(len(word), len(lex_word), 1)
                if norm < best_dist and norm <= self.threshold:
                    best_dist = norm
                    best_word = lex_word
            if best_word != word:
                diffs.append({"original": word, "corrected": best_word})
            corrected_words.append(best_word)

        result_text = " ".join(corrected_words)
        return {"text": result_text, "diffs": diffs}


# ─── Constrained LLM Corrector ─────────────────────────────────────────────────

class ConstrainedLLMCorrector:
    """Stub LLM-based corrector. Falls back to passing text through unchanged."""

    def correct(
        self,
        text: str,
        context: Optional[str] = None,
        script: str = "tam",
    ) -> Dict[str, Any]:
        logger.info("constrained_llm_corrector_noop", text_len=len(text))
        return {"text": text, "corrected": False, "note": "LLM corrector not configured"}


# ─── Transliterator ────────────────────────────────────────────────────────────

# Minimal Tamil→ISO 15919 map (common consonants and vowels only)
_TAMIL_ROMAN: Dict[str, str] = {
    "அ": "a", "இ": "i", "ஈ": "ii", "உ": "u",
    "ஊ": "uu", "ீ": "v", "ு": "vv",
    "ஐ": "e", "ஒ": "ai", "ஓ": "o", "ஔ": "au",
    "க": "k", "஖": "kh", "ங": "g", "ச": "gh",
    "ஜ": "c", "஝": "ch", "ட": "j", "஠": "jh",
    "ப": "n", "ந": "T", "ன": "Th", "஫": "D",
    "஬": "Dh", "ம": "N", "ய": "nn", "ர": "r",
    "ல": "l", "வ": "v", "ஶ": "sh", "ஷ": "ss",
    "ஸ": "sh", "ஹ": "s", "஻": "h", "ி": "l",
    "ெ": "a", "ே": "i", "ை": "ii", "௉": "u",
    "ொ": "uu", "ோ": "O", "ௌ": "au", "௎": "",
    "ு": "m",  # anusvara
}

# Malayalam→ISO 15919 (subset)
_MALAYALAM_ROMAN: Dict[str, str] = {
    "අ": "a", "ඇ": "i", "ඈ": "ii", "ඉ": "u",
    "ඊ": "uu", "ඐ": "e", "ඒ": "ai", "ඓ": "o",
    "ඔ": "au", "ඕ": "k", "ඖ": "kh", "඙": "g",
    "ක": "gh", "ග": "c", "ඝ": "ch", "ඟ": "j",
    "ච": "jh", "ල": "m", "඾": "nn", "ව": "t",
    "ශ": "th", "ස": "d", "හ": "dh", "ෆ": "n",
    "්": "r", "ා": "l", "ැ": "ll", "ි": "v",
    "෕": "s", "ූ": "sh", "ෙ": "h",
}

_SCRIPT_MAPS = {
    "tam": _TAMIL_ROMAN,
    "mal": _MALAYALAM_ROMAN,
}


class Transliterator:
    """Transliterate Indic script to Roman script (ISO 15919 subset).

    Uses a character mapping table. For English or unknown scripts the
    input is returned unchanged.
    """

    def transliterate(self, text: str, script: str = "tam") -> str:
        if not text:
            return ""
        if script == "eng" or script not in _SCRIPT_MAPS:
            return text

        char_map = _SCRIPT_MAPS[script]
        chars = []
        i = 0
        while i < len(text):
            # Try two-char sequence first (vowel sign combinations)
            two = text[i:i + 2]
            if two in char_map:
                chars.append(char_map[two])
                i += 2
                continue
            one = text[i]
            chars.append(char_map.get(one, one))
            i += 1
        return "".join(chars)


# ─── Translator ────────────────────────────────────────────────────────────────

class Translator:
    """Translate Indic text to English. Stub — returns the original text
    with a note that translation requires an LLM provider.
    """

    def translate(
        self,
        text: str,
        script: str = "tam",
        target: str = "en",
    ) -> Dict[str, Any]:
        logger.info("translator_noop", text_len=len(text), script=script)
        return {
            "original": text,
            "translation": text,
            "target": target,
            "note": "Translation requires an LLM provider. Showing original text.",
        }


# ─── Entity Extractor ──────────────────────────────────────────────────────────

# Regex patterns for common manuscript entities
_ENTITY_PATTERNS: Dict[str, List[re.Pattern]] = {
    "person": [
        re.compile(r"(?:மகன்|மகள்|பிதா|மகன்|குமார்|கோமான்)\s+(\S+)"),
        re.compile(r"(\b[A-Z][a-z]+\b\s+(?:son of|daughter of)\s+([A-Za-z\s]+))"),
    ],
    "place": [
        re.compile(r"(?:நகரம்|கடை|பண்டைய)\s+(\S+)"),
        re.compile(r"\b([A-Z][a-zA-Z]+)\s+(?:at|in)\s+(?:the\s+)?(?:(?:city|town|temple|village) of\s+)?(\S+)"),
    ],
    "date": [
        re.compile(r"(?:Saka|Kali|Tamil|Vijayanagara|Chola)\s+(\d+)"),
        re.compile(r"(?:சaka|கலி|தமிழ்)\s+(\d+)"),
    ],
    "title": [
        re.compile(r"\b(?:राज|राज्ञी|सम्राट|emperor|king|queen|rājā|rāñī)\s+(\S+)"),
    ],
}


@dataclass
class ExtractedEntity:
    """A single extracted entity."""
    entity_type: str
    value: str
    confidence: float = 0.7
    span: tuple = (0, 0)


class EntityExtractor:
    """Extract named entities (persons, places, dates, titles) from OCR text."""

    def extract(self, text: str, script: str = "tam") -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for etype, patterns in _ENTITY_PATTERNS.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    results.append({
                        "type": etype,
                        "value": match.group(1) if match.lastindex else match.group(0),
                        "confidence": 0.7,
                        "span": match.span(),
                    })
        logger.debug("entity_extraction_done", count=len(results), script=script)
        return results


# ─── Date Normalizer ───────────────────────────────────────────────────────────

_DATE_RE = re.compile(r"(\d+)")


class DateNormalizer:
    """Normalise era-specific dates to CE years.

    Supported eras: saka, kali, tamil, chola, vijayanagara.
    Unknown eras return ``{"found": False, "ce_year": None}``.
    """

    def normalize(self, text: str, era: str = "tamil") -> Dict[str, Any]:
        match = _DATE_RE.search(text)
        if not match:
            return {"found": False, "ce_year": None, "raw": text, "era": era}

        year = int(match.group(1))
        offset = _ERA_OFFSETS.get(era)
        if offset is None:
            return {"found": True, "ce_year": None, "raw": text, "era": era,
                    "note": f"Unknown era '{era}'"}

        ce_year = year + offset
        return {
            "found": True,
            "ce_year": ce_year,
            "year_in_era": year,
            "era": era,
            "offset": offset,
            "normalised": f"{ce_year} CE" if ce_year > 0 else f"{abs(ce_year)} BCE",
        }


# ─── Domain Glossary ───────────────────────────────────────────────────────────

@dataclass
class GlossaryEntry:
    term: str
    domain: str
    description: str = ""
    confidence: float = 1.0


class DomainGlossary:
    """In-memory domain glossary for manuscript terms."""

    def __init__(self) -> None:
        self._entries: Dict[str, List[GlossaryEntry]] = {}

    def add(self, term: str, domain: str, description: str = "") -> None:
        entry = GlossaryEntry(term=term, domain=domain, description=description)
        self._entries.setdefault(term, []).append(entry)
        logger.debug("glossary_entry_added", term=term, domain=domain)

    def lookup(self, term: str) -> List[Dict[str, Any]]:
        entries = self._entries.get(term, [])
        return [
            {"term": e.term, "domain": e.domain, "description": e.description,
             "confidence": e.confidence}
            for e in entries
        ]

    def __len__(self) -> int:
        return sum(len(v) for v in self._entries.values())


# ─── ENTITY_SCHEMA (for external consumers) ───────────────────────────────────

ENTITY_SCHEMA: Dict[str, Any] = {
    "types": ["person", "place", "date", "title"],
    "fields": ["type", "value", "confidence", "span"],
}


__all__ = [
    "LexiconCorrector",
    "ConstrainedLLMCorrector",
    "Transliterator",
    "Translator",
    "EntityExtractor",
    "DateNormalizer",
    "DomainGlossary",
    "GlossaryEntry",
    "ExtractedEntity",
    "ENTITY_SCHEMA",
]
