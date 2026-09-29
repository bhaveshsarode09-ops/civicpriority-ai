"""Gemini AI Provider for CivicPriority AI.
Implements Google GenAI SDK integration with structured Pydantic outputs,
exponential backoff retry, rate-limit resilience, and zero API-key leakage.
"""

import json
import logging
import os
import time
from typing import Any, Optional
from pydantic import BaseModel, Field

from civicpriority.ai.base import BaseAIProvider
from civicpriority.ai.mock_provider import MockAIProvider
from civicpriority.models import ComplaintCategory, ComplaintRecord, ProcessedComplaint, utc_now
from civicpriority.privacy import sanitize_text_for_ai

logger = logging.getLogger("civicpriority.ai.gemini")


class ComplaintAnalysisSchema(BaseModel):
    """Structured Pydantic schema requested from Gemini."""
    detected_language: str = Field(description="ISO language code, e.g. en, hi, mr")
    translated_text: str = Field(description="Accurate English translation of the complaint")
    summary: str = Field(description="Factual one-sentence summary of the grievance")
    category: str = Field(description="Category from the 11 civic categories")
    subcategory: str = Field(description="Specific sub-category or infrastructure deficit")
    department: str = Field(description="Primary municipal or governmental agency responsible")
    severity_score: float = Field(ge=0.0, le=100.0, description="Severity score 0 to 100")
    urgency_score: float = Field(ge=0.0, le=100.0, description="Urgency score 0 to 100")
    estimated_people_affected: int = Field(ge=0, description="Estimated number of affected citizens")
    vulnerable_groups: list[str] = Field(description="Identified vulnerable groups, e.g. Children, Elderly")
    keywords: list[str] = Field(description="Key civic terms and problem keywords")
    entities: list[str] = Field(description="Named locations, schools, hospitals, or roads")
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence in classification")
    requires_human_review: bool = Field(description="True if grievance is ambiguous, sensitive, or low confidence")


class GeminiProvider(BaseAIProvider):
    """Google Gemini AI Provider utilizing modern @google/genai SDK."""

    MODEL_NAME = "gemini-3.8-flash"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.fallback_mock = MockAIProvider()
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("Failed to initialize Google GenAI Client: %s", type(e).__name__)
                self.client = None

    def _call_gemini_structured(self, prompt: str) -> Optional[ComplaintAnalysisSchema]:
        """Call Gemini with structured output format and retry logic."""
        if not self.client:
            return None

        from google.genai import types

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ComplaintAnalysisSchema,
                        temperature=0.2,
                    ),
                )
                if response and response.text:
                    parsed_dict = json.loads(response.text)
                    return ComplaintAnalysisSchema.model_validate(parsed_dict)
            except Exception as e:
                # Sanitized error logging that never reveals API keys
                err_msg = f"Gemini API attempt {attempt + 1} failed: {type(e).__name__}"
                logger.warning(err_msg)
                if attempt < max_retries - 1:
                    time.sleep(1.0 * (2 ** attempt))

        return None

    def process_complaint_full(self, record: ComplaintRecord) -> ProcessedComplaint:
        clean_text = sanitize_text_for_ai(record.original_text)

        # Attempt structured Gemini call
        if self.client:
            prompt = f"""
You are an expert civic grievance triage AI for a municipal government.
Analyze this citizen complaint:

Locality: {record.locality}
Original Reported Language: {record.original_language}
Complaint Text:
{clean_text}

Allowed Categories:
- Roads and transport
- Water and sanitation
- Education
- Healthcare
- Agriculture
- Electricity
- Pollution and environment
- Public safety
- Housing
- Digital public infrastructure
- Other

Provide accurate translation to English, classify into the closest category, estimate severity and urgency (0-100), identify vulnerable demographics (e.g. Children, Elderly, Patients, Women), extract entities and responsible department.
"""
            analysis = self._call_gemini_structured(prompt)
            if analysis:
                # Match category to valid enum or fallback
                matched_category = ComplaintCategory.OTHER
                for cat in ComplaintCategory:
                    if cat.value.lower() == analysis.category.lower():
                        matched_category = cat
                        break

                infra_score = min(100.0, max(10.0, analysis.severity_score * 0.95))

                return ProcessedComplaint(
                    complaint_id=record.id,
                    language=analysis.detected_language,
                    translated_text=analysis.translated_text,
                    summary=analysis.summary,
                    category=matched_category,
                    subcategory=analysis.subcategory,
                    location=record.locality,
                    department=analysis.department,
                    severity_score=analysis.severity_score,
                    urgency_score=analysis.urgency_score,
                    estimated_people_affected=analysis.estimated_people_affected,
                    vulnerable_groups=analysis.vulnerable_groups,
                    infrastructure_gap_score=infra_score,
                    keywords=analysis.keywords,
                    entities=analysis.entities,
                    ai_confidence=analysis.confidence,
                    requires_human_review=analysis.requires_human_review or (analysis.confidence < 0.70),
                    processing_errors=[],
                    processed_at=utc_now(),
                )

        # Fallback to Mock provider if Gemini fails or is unconfigured
        result = self.fallback_mock.process_complaint_full(record)
        if self.client:
            result.processing_errors.append("Gemini provider timed out or failed; deterministic fallback used.")
            result.requires_human_review = True
        return result

    def detect_language(self, text: str) -> str:
        clean = sanitize_text_for_ai(text)
        return self.fallback_mock.detect_language(clean)

    def translate(self, text: str, target_language: str = "en") -> str:
        clean = sanitize_text_for_ai(text)
        return self.fallback_mock.translate(clean, target_language)

    def summarize(self, text: str) -> str:
        clean = sanitize_text_for_ai(text)
        return self.fallback_mock.summarize(clean)

    def extract_information(self, text: str) -> dict[str, Any]:
        clean = sanitize_text_for_ai(text)
        return self.fallback_mock.extract_information(clean)

    def classify_complaint(self, text: str) -> ComplaintCategory:
        clean = sanitize_text_for_ai(text)
        return self.fallback_mock.classify_complaint(clean)

    def estimate_severity(self, text: str) -> float:
        clean = sanitize_text_for_ai(text)
        return self.fallback_mock.estimate_severity(clean)

    def estimate_urgency(self, text: str) -> float:
        clean = sanitize_text_for_ai(text)
        return self.fallback_mock.estimate_urgency(clean)

    def estimate_people_affected(self, text: str) -> int:
        clean = sanitize_text_for_ai(text)
        return self.fallback_mock.estimate_people_affected(clean)

    def identify_vulnerable_groups(self, text: str) -> list[str]:
        clean = sanitize_text_for_ai(text)
        return self.fallback_mock.identify_vulnerable_groups(clean)

    def generate_priority_explanation(self, cluster_data: dict[str, Any]) -> str:
        return self.fallback_mock.generate_priority_explanation(cluster_data)
