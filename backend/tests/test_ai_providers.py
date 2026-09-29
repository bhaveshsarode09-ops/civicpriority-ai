"""Unit tests for Phase 4 AI Provider Layer.
Tests MockAIProvider and GeminiProvider with English and Hindi inputs.
"""

import pytest

from civicpriority.ai import GeminiProvider, MockAIProvider
from civicpriority.models import ComplaintCategory, ComplaintRecord, ComplaintSource


def test_ward_12_hindi_complaint_processing():
    """Verify the core Hindi Ward 12 school complaint is correctly translated,
    classified into Education, linked to children as a vulnerable group,
    and assigned reasonable severity & urgency.
    """
    hindi_text = "वार्ड 12 के सरकारी स्कूल में बच्चों के लिए पर्याप्त कक्षाएं नहीं हैं और पीने का साफ पानी भी नहीं है।"
    provider = MockAIProvider()

    # 1. Language detection
    detected_lang = provider.detect_language(hindi_text)
    assert detected_lang == "hi"

    # 2. Translation
    translated = provider.translate(hindi_text, target_language="en")
    assert "school" in translated.lower()
    assert "classrooms" in translated.lower()
    assert "drinking water" in translated.lower()

    # 3. Classification
    category = provider.classify_complaint(translated)
    assert category == ComplaintCategory.EDUCATION

    # 4. Vulnerable groups identification
    vulnerable = provider.identify_vulnerable_groups(translated)
    assert "Children" in vulnerable

    # 5. Severity & Urgency
    severity = provider.estimate_severity(translated)
    urgency = provider.estimate_urgency(translated)
    assert 70.0 <= severity <= 100.0
    assert 70.0 <= urgency <= 100.0


def test_process_complaint_full_integration():
    """Verify end-to-end processing from ComplaintRecord to ProcessedComplaint."""
    record = ComplaintRecord(
        id="CMP-TEST-HI-01",
        source=ComplaintSource.PUBLIC_MEETING,
        original_text="वार्ड 12 के सरकारी स्कूल में बच्चों के लिए पर्याप्त कक्षाएं नहीं हैं और पीने का साफ पानी भी नहीं है। Call 9876543210",
        original_language="hi",
        locality="Ward 12",
        consent_obtained=True,
    )
    provider = MockAIProvider()
    processed = provider.process_complaint_full(record)

    assert processed.complaint_id == record.id
    assert processed.language == "hi"
    assert "9876543210" not in processed.translated_text  # PII masked
    assert "[PHONE_REDACTED]" in processed.translated_text or "classrooms" in processed.translated_text
    assert processed.category == ComplaintCategory.EDUCATION
    assert "Children" in processed.vulnerable_groups
    assert processed.severity_score >= 75.0
    assert processed.urgency_score >= 75.0
    assert processed.estimated_people_affected >= 500
    assert processed.department == "Department of School Education"
    assert processed.requires_human_review is False


def test_low_confidence_and_review_flags():
    """Verify simulate_low_confidence and force_review trigger human review flags."""
    record = ComplaintRecord(
        id="CMP-TEST-REVIEW",
        source=ComplaintSource.DIRECT_WEB,
        original_text="Streetlight broken on corner.",
        locality="Ward 4",
    )

    # Standard provider
    std_provider = MockAIProvider()
    std_res = std_provider.process_complaint_full(record)
    assert std_res.requires_human_review is False
    assert std_res.ai_confidence > 0.80

    # Low-confidence provider
    low_conf_provider = MockAIProvider(simulate_low_confidence=True)
    low_res = low_conf_provider.process_complaint_full(record)
    assert low_res.requires_human_review is True
    assert low_res.ai_confidence < 0.70

    # Forced review provider
    forced_provider = MockAIProvider(force_review=True)
    forced_res = forced_provider.process_complaint_full(record)
    assert forced_res.requires_human_review is True


def test_gemini_provider_resilience():
    """Verify GeminiProvider handles calls safely without leaking secrets or failing."""
    provider = GeminiProvider()
    assert provider is not None

    record = ComplaintRecord(
        id="CMP-TEST-GEMINI",
        source=ComplaintSource.DIRECT_WEB,
        original_text="Water pipeline burst near Ward 4 market flooding roads.",
        locality="Ward 4",
    )
    processed = provider.process_complaint_full(record)
    assert processed.complaint_id == "CMP-TEST-GEMINI"
    assert processed.category in [ComplaintCategory.WATER_AND_SANITATION, ComplaintCategory.ROADS_AND_TRANSPORT]
    assert processed.severity_score >= 50.0


def test_priority_explanation_generation():
    """Verify transparent human-readable priority explanation."""
    provider = MockAIProvider()
    explanation = provider.generate_priority_explanation({
        "category": "Education",
        "locality": "Ward 12",
        "vulnerable_groups": ["Children"],
        "complaint_count": 6,
        "priority_score": 92.5,
    })
    assert "92.5/100" in explanation
    assert "Ward 12" in explanation
    assert "Children" in explanation
    assert "Education" in explanation
