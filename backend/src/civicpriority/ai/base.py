"""Abstract AI Provider protocol for CivicPriority AI.
Declares standardized interfaces for language detection, translation, summarization,
entity extraction, classification, severity/urgency scoring, and full complaint processing.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from civicpriority.models import ComplaintCategory, ComplaintRecord, ProcessedComplaint, utc_now
from civicpriority.privacy import sanitize_text_for_ai


class BaseAIProvider(ABC):
    """Protocol for AI-assisted grievance processing."""

    @abstractmethod
    def detect_language(self, text: str) -> str:
        """Detect language code (e.g. 'en', 'hi', 'mr')."""
        pass

    @abstractmethod
    def translate(self, text: str, target_language: str = "en") -> str:
        """Translate text into target language."""
        pass

    @abstractmethod
    def summarize(self, text: str) -> str:
        """Generate a concise one-sentence factual summary."""
        pass

    @abstractmethod
    def extract_information(self, text: str) -> dict[str, Any]:
        """Extract keywords, named entities, subcategory, and responsible department."""
        pass

    @abstractmethod
    def classify_complaint(self, text: str) -> ComplaintCategory:
        """Classify complaint into one of the 11 configurable categories."""
        pass

    @abstractmethod
    def estimate_severity(self, text: str) -> float:
        """Estimate severity score (0.0 to 100.0)."""
        pass

    @abstractmethod
    def estimate_urgency(self, text: str) -> float:
        """Estimate urgency score (0.0 to 100.0)."""
        pass

    @abstractmethod
    def estimate_people_affected(self, text: str) -> int:
        """Estimate number of affected citizens."""
        pass

    @abstractmethod
    def identify_vulnerable_groups(self, text: str) -> list[str]:
        """Identify vulnerable demographics mentioned (e.g., children, elderly)."""
        pass

    @abstractmethod
    def generate_priority_explanation(self, cluster_data: dict[str, Any]) -> str:
        """Generate a transparent human-readable explanation of why an issue is ranked at its level."""
        pass

    def process_complaint_full(self, record: ComplaintRecord) -> ProcessedComplaint:
        """Process a raw ComplaintRecord end-to-end into a structured ProcessedComplaint.
        Ensures PII is scrubbed before any AI analysis.
        """
        # Scrub any PII before model analysis
        clean_text = sanitize_text_for_ai(record.original_text)

        detected_lang = self.detect_language(clean_text) or record.original_language or "en"
        if detected_lang != "en":
            translated_text = self.translate(clean_text, target_language="en")
        else:
            translated_text = clean_text

        summary = self.summarize(translated_text)
        category = self.classify_complaint(translated_text)
        info = self.extract_information(translated_text)
        severity = self.estimate_severity(translated_text)
        urgency = self.estimate_urgency(translated_text)
        people_affected = self.estimate_people_affected(translated_text)
        vulnerable = self.identify_vulnerable_groups(translated_text)

        # Baseline infrastructure gap score from severity + context
        infra_score = min(100.0, max(10.0, severity * 0.95))

        return ProcessedComplaint(
            complaint_id=record.id,
            language=detected_lang,
            translated_text=translated_text,
            summary=summary,
            category=category,
            subcategory=info.get("subcategory"),
            location=record.locality,
            department=info.get("department", "Municipal Administration"),
            severity_score=severity,
            urgency_score=urgency,
            estimated_people_affected=people_affected,
            vulnerable_groups=vulnerable,
            infrastructure_gap_score=infra_score,
            keywords=info.get("keywords", []),
            entities=info.get("entities", []),
            ai_confidence=info.get("confidence", 0.90),
            requires_human_review=info.get("requires_human_review", False),
            processing_errors=[],
            processed_at=utc_now(),
        )
