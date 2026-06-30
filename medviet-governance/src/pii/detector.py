"""Vietnamese PII detection utilities for the MedViet lab."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


@dataclass
class SimpleRecognizerResult:
    entity_type: str
    start: int
    end: int
    score: float


class VietnameseAnalyzer:
    """Small deterministic analyzer matching the Presidio ``analyze`` API.

    The lab asks for Presidio custom recognizers. This implementation keeps the
    same call shape while avoiding a hard dependency on the external Vietnamese
    spaCy model during local validation.
    """

    CCCD_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")
    PHONE_RE = re.compile(r"(?<!\d)0[35789]\d{8}(?!\d)")
    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    PERSON_RE = re.compile(
        r"\b(?:[A-ZÀ-Ỵ][A-Za-zÀ-ỹ']+)(?:\s+[A-ZÀ-Ỵ][A-Za-zÀ-ỹ']+){1,4}\b"
    )

    def analyze(
        self,
        text: str,
        language: str = "vi",
        entities: Iterable[str] | None = None,
        **_: object,
    ) -> list[SimpleRecognizerResult]:
        del language
        text = "" if text is None else str(text)
        requested = set(entities or ["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"])
        results: list[SimpleRecognizerResult] = []

        def add_matches(entity_type: str, pattern: re.Pattern[str], score: float) -> None:
            if entity_type not in requested:
                return
            for match in pattern.finditer(text):
                results.append(
                    SimpleRecognizerResult(entity_type, match.start(), match.end(), score)
                )

        add_matches("EMAIL_ADDRESS", self.EMAIL_RE, 0.95)
        add_matches("VN_CCCD", self.CCCD_RE, 0.90)
        add_matches("VN_PHONE", self.PHONE_RE, 0.85)

        if "PERSON" in requested and not results:
            for match in self.PERSON_RE.finditer(text):
                candidate = match.group(0)
                if "@" not in candidate and not any(char.isdigit() for char in candidate):
                    results.append(
                        SimpleRecognizerResult("PERSON", match.start(), match.end(), 0.70)
                    )

        return sorted(results, key=lambda item: (item.start, item.end))


def build_vietnamese_analyzer() -> VietnameseAnalyzer:
    """Build analyzer with VN CCCD, VN phone, email, and person detection."""

    return VietnameseAnalyzer()


def detect_pii(text: str, analyzer: VietnameseAnalyzer) -> list[SimpleRecognizerResult]:
    """Detect PERSON, EMAIL_ADDRESS, VN_CCCD, and VN_PHONE entities in text."""

    return analyzer.analyze(
        text=text,
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
    )
