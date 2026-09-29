"""Deterministic Mock AI Provider for CivicPriority AI.
Operates reliably offline without external API keys for deterministic testing and reproducible demos.
"""

import re
from typing import Any, Optional

from civicpriority.ai.base import BaseAIProvider
from civicpriority.models import ComplaintCategory


class MockAIProvider(BaseAIProvider):
    """Rule and keyword-based AI provider implementation."""

    def __init__(self, simulate_low_confidence: bool = False, force_review: bool = False):
        self.simulate_low_confidence = simulate_low_confidence
        self.force_review = force_review

    def detect_language(self, text: str) -> str:
        if not text:
            return "en"
        # Check Devanagari Unicode range (U+0900 - U+097F)
        devanagari_chars = sum(1 for ch in text if "\u0900" <= ch <= "\u097f")
        if devanagari_chars > 3:
            # Check Marathi specific characters / keywords
            marathi_keywords = ["शाळेत", "मुलांच्या", "पाणी", "नाही", "आहेत", "रस्त्यावर", "गळती"]
            if any(k in text for k in marathi_keywords) and "शाळेत" in text:
                return "mr"
            return "hi"
        return "en"

    def translate(self, text: str, target_language: str = "en") -> str:
        if not text or target_language != "en":
            return text

        # Exact match or pattern match for the core Hindi Ward 12 complaint
        if "वार्ड 12" in text and "सरकारी स्कूल" in text and ("पर्याप्त कक्षाएं" in text or "पीने का साफ पानी" in text):
            return "The government school in Ward 12 lacks adequate classrooms for children and also lacks clean drinking water."

        # Other Hindi translations
        translations_map = {
            "वार्ड 12 प्राथमिक विद्यालय में पीने का पानी दूषित है": "In Ward 12 primary school, drinking water is contaminated and there is no room to sit in classrooms. Children are falling ill.",
            "वार्ड 7 बाजार वाली सड़क पर बड़ा गड्ढा हो गया है": "There is a large dangerous pothole on the Ward 7 market road, severe accidents could happen anytime. Please repair immediately.",
            "वार्ड 7 की मुख्य सड़क पर दो फीट गहरा गड्ढा है": "There is a two-foot deep crater on the main road of Ward 7 causing bike riders to crash every day.",
            "वार्ड 4 में पीने के पानी की मुख्य पाइपलाइन टूट गई है": "The main drinking water pipeline in Ward 4 has ruptured. Contaminated water is entering homes and drinking water is being wasted.",
            "वार्ड 9 प्राथमिक स्वास्थ्य केंद्र में कोई डॉक्टर नहीं है": "There is no doctor at Ward 9 primary health center, only one nurse, and essential medicines like fever tablets and antibiotics are out of stock.",
            "वार्ड 15 में ट्रांसफार्मर जलने से 2 दिन से बिजली गुल है": "Power has been out for 2 days in Ward 15 due to a burned transformer. Children have board exams and inverters have shut down.",
            "वार्ड 12 में नालियों की सफाई नहीं होने से सड़क पर गंदा बदबूदार पानी भर गया है": "Due to uncleaned drains in Ward 12, foul-smelling dirty water has accumulated on the street.",
            "वार्ड 9 में रात को अंधेरा रहता है, स्ट्रीट लाइट खराब होने से": "It is dark at night in Ward 9, broken streetlights cause fear of theft and insecurity.",
            "वार्ड 15 के पास कारखाने का जहरीला गंदा पानी खेतों में जा रहा है": "Toxic industrial waste water is entering farm fields near Ward 15, destroying crops.",
            "वार्ड 12 पार्क में कोई सार्वजनिक शौचालय नहीं है": "There is no public toilet in Ward 12 park, causing immense hardship for elderly and women.",
            "वार्ड 15 में बिजली के तार झूल रहे हैं": "Electric wires are sagging dangerously in Ward 15, risking fire from short circuits.",
            "वार्ड 12 रेलवे फुटब्रिज पर रेलिंग टूटी हुई है": "Safety railings on Ward 12 railway footbridge are broken, posing falling risk for children and seniors.",
        }

        for hi_phrase, en_trans in translations_map.items():
            if hi_phrase in text:
                return en_trans

        # Marathi translations
        marathi_map = {
            "वार्ड 12 शाळेत पिण्याचे स्वच्छ पाणी नाही": "In Ward 12 school there is no clean drinking water and severe shortage of classrooms, affecting child health.",
            "वार्ड 7 मुख्य बाजार मार्ग पूर्णपणे तुटलेला आहे": "Ward 7 main market road is completely broken. Ambulances are getting stranded.",
            "वार्ड 4 मधील जलवाहिनी फुटल्यामुळे": "Due to burst water pipeline in Ward 4, severe shortage of drinking water has emerged across the settlement.",
            "वार्ड 9 आरोग्य केंद्रात वैद्यकीय अधिकाऱ्यांची तातडीने नियुक्ती": "Citizens unanimously demand urgent appointment of medical officer at Ward 9 health center.",
            "वार्ड 4 प्राथमिक शाळेच्या छताची गळती": "Demands made to repair leaking roof and construct protective boundary wall at Ward 4 primary school.",
            "वार्ड 9 सरकारी शाळेतील संगणक प्रयोगशाळा बंद आहे": "Computer lab in Ward 9 government school is closed and lacks internet connectivity.",
            "वार्ड 7 कचरा पेटी भरून रस्त्यावर कचरा पसरला आहे": "Garbage bins overflowing on Ward 7 road, spreading stench and disease risk.",
        }

        for mr_phrase, en_trans in marathi_map.items():
            if mr_phrase in text:
                return en_trans

        # If already English or unmapped, return text
        return text

    def summarize(self, text: str) -> str:
        clean = text.strip()
        first_sentence = clean.split(".")[0].strip()
        if len(first_sentence) > 100:
            return first_sentence[:97] + "..."
        return first_sentence + "."

    def classify_complaint(self, text: str) -> ComplaintCategory:
        t = text.lower()
        if any(w in t for w in ["school", "classroom", "teacher", "student", "education", "books", "blackboard"]):
            return ComplaintCategory.EDUCATION
        if any(w in t for w in ["water", "pipe", "pipeline", "drinking water", "tap", "sewage", "sewer", "drain", "drainage"]):
            return ComplaintCategory.WATER_AND_SANITATION
        if any(w in t for w in ["road", "pothole", "bridge", "traffic", "bus", "transport", "footbridge", "transit"]):
            return ComplaintCategory.ROADS_AND_TRANSPORT
        if any(w in t for w in ["doctor", "health", "hospital", "clinic", "medicine", "nurse", "dispensary"]):
            return ComplaintCategory.HEALTHCARE
        if any(w in t for w in ["electricity", "power", "transformer", "blackout", "voltage", "streetlight", "wires"]):
            return ComplaintCategory.ELECTRICITY
        if any(w in t for w in ["pollution", "factory", "toxic", "chemical", "garbage", "trash", "waste"]):
            return ComplaintCategory.POLLUTION_AND_ENVIRONMENT
        if any(w in t for w in ["farm", "crop", "agriculture", "farmer", "irrigation"]):
            return ComplaintCategory.AGRICULTURE
        if any(w in t for w in ["police", "stray dog", "safety", "theft", "crime"]):
            return ComplaintCategory.PUBLIC_SAFETY
        if any(w in t for w in ["housing", "slum", "roof", "building shelter"]):
            return ComplaintCategory.HOUSING
        if any(w in t for w in ["internet", "broadband", "digital", "computer lab", "portal"]):
            return ComplaintCategory.DIGITAL_PUBLIC_INFRASTRUCTURE
        return ComplaintCategory.OTHER

    def extract_information(self, text: str) -> dict[str, Any]:
        t = text.lower()
        keywords = []
        entities = []
        department = "General Administration"
        subcategory = "Civic Infrastructure"

        # Keywords
        candidate_kw = ["school", "classroom", "water", "drinking water", "pothole", "road", "doctor",
                        "hospital", "electricity", "transformer", "sewage", "drainage", "bridge", "stray dog"]
        for kw in candidate_kw:
            if kw in t:
                keywords.append(kw)

        # Entities
        loc_match = re.search(r"(Ward\s+\d+|Sector\s+\d+|[A-Z][a-z]+\s+(?:School|Hospital|Market|Road|Canal))", text)
        if loc_match:
            entities.append(loc_match.group(1))

        # Departments & Subcategories
        if "school" in t or "classroom" in t:
            department = "Department of School Education"
            subcategory = "Classroom Shortage & Sanitation"
        elif "pipeline" in t or "drinking water" in t:
            department = "Water Supply & Sewerage Board"
            subcategory = "Drinking Water Distribution"
        elif "road" in t or "pothole" in t:
            department = "Public Works Department (Roads)"
            subcategory = "Road Maintenance & Pothole Repair"
        elif "doctor" in t or "hospital" in t:
            department = "Department of Health & Family Welfare"
            subcategory = "Primary Healthcare Staffing"
        elif "electricity" in t or "transformer" in t or "power" in t:
            department = "Electricity Distribution Corporation"
            subcategory = "Power Distribution & Transformer Failure"

        confidence = 0.55 if self.simulate_low_confidence else 0.92
        requires_review = self.force_review or self.simulate_low_confidence

        return {
            "keywords": keywords,
            "entities": entities,
            "department": department,
            "subcategory": subcategory,
            "confidence": confidence,
            "requires_human_review": requires_review,
        }

    def estimate_severity(self, text: str) -> float:
        t = text.lower()
        score = 50.0

        # Critical multipliers
        if any(w in t for w in ["death", "collapse", "severe accident", "toxic", "poisonous", "emergency"]):
            score += 40.0
        elif any(w in t for w in ["no clean water", "no doctor", "children", "overcrowded", "crater", "blackout", "rupture"]):
            score += 35.0
        elif any(w in t for w in ["broken", "pothole", "dirty water", "dark", "leaking"]):
            score += 20.0

        return min(100.0, max(0.0, score))

    def estimate_urgency(self, text: str) -> float:
        t = text.lower()
        score = 45.0

        if any(w in t for w in ["immediate", "urgent", "emergency", "today", "now", "falling ill"]):
            score += 45.0
        elif any(w in t for w in ["days", "weeks", "school", "children", "accident", "ambulance"]):
            score += 35.0
        elif any(w in t for w in ["repair", "maintenance", "request"]):
            score += 15.0

        return min(100.0, max(0.0, score))

    def estimate_people_affected(self, text: str) -> int:
        t = text.lower()
        if "school" in t or "students" in t:
            return 650
        if "main road" in t or "arterial" in t or "market" in t:
            return 3500
        if "pipeline" in t or "transformer" in t or "households" in t:
            return 1200
        if "health center" in t or "dispensary" in t:
            return 800
        return 150

    def identify_vulnerable_groups(self, text: str) -> list[str]:
        t = text.lower()
        groups = []
        if any(w in t for w in ["child", "children", "student", "students", "school", "kids", "बच्चे", "बच्चों", "मुलांच्या"]):
            groups.append("Children")
        if any(w in t for w in ["elderly", "senior", "pensioner", "old age", "बुजुर्ग", "वृद्ध"]):
            groups.append("Elderly")
        if any(w in t for w in ["patient", "patients", "pregnant", "sick", "मरीज", "आजारी"]):
            groups.append("Patients")
        if any(w in t for w in ["women", "girls", "महिला"]):
            groups.append("Women & Girls")
        if any(w in t for w in ["farmer", "farmers", "किसान", "शेतकरी"]):
            groups.append("Smallholder Farmers")
        return groups

    def generate_priority_explanation(self, cluster_data: dict[str, Any]) -> str:
        cat = cluster_data.get("category", "General")
        locality = cluster_data.get("locality", "Local Ward")
        vulnerable = cluster_data.get("vulnerable_groups", [])
        count = cluster_data.get("complaint_count", 1)
        score = cluster_data.get("priority_score", 50.0)

        vuln_text = f" impacting vulnerable groups ({', '.join(vulnerable)})" if vulnerable else ""
        return (
            f"Ranked at priority score {score:.1f}/100 based on {count} independent citizen reports "
            f"in {locality} regarding {cat}{vuln_text}. Requires prompt administrative intervention "
            f"due to elevated civic impact."
        )
