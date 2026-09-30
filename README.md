# CivicPriority AI — From Citizen Voice to Government Action

[![Tests](https://img.shields.io/badge/pytest-54%20passed-success)](backend/tests/)
[![Python](https://img.shields.io/badge/python-3.11-blue)](backend/)
[![React](https://img.shields.io/badge/react-19-cyan)](src/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal)](backend/src/civicpriority/api.py)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **Mandatory Disclaimer**: *DEMONSTRATION SYSTEM: Uses a privacy-sanitized Kaggle benchmark for simulation. Not connected to live municipal dispatch.*

## Dataset and ML Framework Disclosure

This prototype uses the **Kaggle Civic and Municipality Complaint System Dataset** for **data simulation, benchmark analysis, and demonstration of the ML framework**:

- **Kaggle source:** [Civic and Municipality Complaint System Dataset](https://www.kaggle.com/datasets/wajahattaj/civic-and-municipality-complaint-system-dataset)
- **Dataset size:** 1,100 municipal complaint records with issue descriptions, issue types, locations, departments, severity, priority labels, and citizen-report counts.
- **How it is used:** The privacy-sanitized records are used to demonstrate complaint classification, issue grouping, municipal prioritization, transparent scoring, and the frontend fallback dataset when the backend API is unavailable.
- **Privacy:** Resident names, resident IDs, email addresses, and phone numbers were removed before inclusion in this repository.
- **Scope:** The Kaggle records are a benchmark dataset covering multiple US cities. They are **not live Indian government data, not official municipal records, and not evidence of real deployments**.
- **Production requirement:** A real deployment would require authorized, locally relevant Indian datasets, official APIs, consent, data-sharing agreements, and privacy/security review.

The ML framework and scoring logic are dataset-agnostic. The Kaggle data is used only to simulate inputs and validate the workflow; it does not replace the need for authorized local data.

CivicPriority AI is an open-source, explainable decision support system designed for municipal commissioners, district collectors, and urban planners. It ingests messy, multilingual citizen grievances across multiple reporting channels (public meetings, paper petitions, WhatsApp/SMS helplines, web portals, and social media), automatically redacts personal identifiable information (PII), clusters duplicate reports about shared civic failures, and ranks interventions using a transparent, multi-criteria mathematical formula with built-in fairness safeguards.

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   Citizen Grievance Ingestion Channels                 │
│  [Town Hall Transcripts]  [Paper Letters]  [WhatsApp/SMS]  [Web Portal] │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Privacy, Anonymization & Security Layer                  │
│   • Regex PII Masking: [PHONE_REDACTED], [EMAIL_REDACTED]             │
│   • Deterministic Salted SHA-256 Citizen Contact Hashing               │
│   • Zero PII Transmission to External Language Models                  │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Multilingual NLU & Entity Extraction                   │
│   • Supported: Hindi (हिंदी), Marathi (मराठी), English (en)            │
│   • 11 Civic Categories (Water, Education, Roads, Health, Power, etc.) │
│   • Automated Severity & Urgency Scoring (0–100)                       │
│   • Vulnerable Demographic Flagging (Children, Elderly, Patients)     │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Graph-Based Issue Clustering                       │
│   • Locality & Category Partitioning (e.g. Ward 12 + Education)       │
│   • TF-IDF Vectorization + Cosine Similarity Graph Construction        │
│   • Connected Component Clustering with Multi-Source Aggregation       │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│           Transparent Multi-Criteria Prioritization Formula            │
│   Score = 0.30×Severity + 0.25×Log(People) + 0.20×Urgency +           │
│           0.15×InfraGap + 0.10×RepeatVolume                            │
│   • Proactive Fairness Alerts for Low-Volume / High-Severity Wards     │
│   • Dynamic Policy Weight Simulation with Instant Recalculation        │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Policy & Public Dashboard (React 19)                │
│   • Policy Dashboard: Prioritized clusters, explainability, dispatch   │
│   • Public Transparency: Citizen status tracking & open score math     │
│   • Citizen Grievance Intake: Real-time live PII redaction preview     │
│   • Records Explorer & Multi-Channel Batch Ingestion                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Features & Algorithms

### 1. Zero-Leak Privacy & Salted Contact Hashing
- **Phone Number Redaction**: Detects standard 10-digit Indian numbers starting with 6–9, `+91` country prefixes, spaced formats (`98765 43210`), and international formats.
- **Email Redaction**: Replaces addresses with `[EMAIL_REDACTED]`.
- **Deterministic Salted Hashing**: Computes `SHA256(phone_or_email + salt)` so duplicate reports from the same citizen can be correlated without ever exposing or persisting their real identity.

### 2. Ward & Spatial Isolation
Grievances occurring in different wards (e.g., a broken water pipe in Ward 4 vs. Ward 12) never cross-cluster, preserving strict spatial boundaries and department routing.

### 3. Logarithmic Demographic Scaling
To prevent densely populated wards from completely dominating municipal budgets:
$$\text{Score}_{\text{people}} = \min\left(100, \frac{\log_{10}(\text{people} + 1)}{\log_{10}(10001)} \times 100\right)$$
An issue affecting 500 children in an underserved rural school receives 67.5% of the maximum population score, preventing it from being overshadowed by a non-urgent complaint in an apartment complex of 10,000 residents.

### 4. Proactive Spatial Equity Safeguards
If an issue has `complaint_count <= 2` but `severity >= 70` in an underserved ward, the system flags a **Fairness Safeguard Active** alert to protect vulnerable citizens who may face barriers to filing digital complaints.

---

## 📊 5-Part Mathematical Scoring Formula

$$\text{Priority Score} = w_s \cdot S + w_p \cdot P_{\text{log}} + w_u \cdot U + w_i \cdot I + w_r \cdot R$$

| Factor | Default Weight | Description |
|:---|:---:|:---|
| **Severity ($S$)** | 30% | Direct physical danger, health hazards, structural failures |
| **Population ($P_{\text{log}}$)** | 25% | Logarithmically scaled estimated affected population |
| **Urgency ($U$)** | 20% | Time-criticality (e.g. ongoing contamination, open crater) |
| **Infrastructure Gap ($I$)** | 15% | Historical deficit in ward infrastructure |
| **Repeat Volume ($R$)** | 10% | Volume of validated reports across distinct channels |

---

## 🧪 Comprehensive Automated Test Suite (54 Tests)

All 54 tests run locally with 100% pass rate:

```bash
# Run the complete test suite
PYTHONPATH=backend/src python3 -m pytest backend/tests/ -v
```

- `test_models.py` (7 tests): Data integrity, Pydantic score boundaries, SQLite persistence.
- `test_privacy.py` (8 tests): Regex masking, salted contact hashing, PII sanitization.
- `test_scoring.py` (6 tests): Mathematical score formula, log scaling, fairness safeguards.
- `test_connectors.py` (7 tests): CSV, transcript, written letter, social media, messaging.
- `test_clustering.py` (5 tests): TF-IDF text similarity, ward matching, cross-ward isolation.
- `test_ai_providers.py` (5 tests): Multilingual extraction, Hindi/Marathi NLU, confidence scores.
- `test_api.py` (9 tests): FastAPI endpoints, filtering, pagination, patch workflow.
- `test_e2e_flow.py` (7 tests): Complete 9-step end-to-end verification lifecycle.

---

## 🚀 Running the Application

The dev server concurrently runs both the FastAPI backend (port 5050) and the Vite React frontend (port 3000):

```bash
# Start both backend and frontend
npm run dev
```

- Frontend available at: `http://localhost:3000`
- Backend API routed through Vite proxy: `http://localhost:3000/api/health`

### Hosted/demo fallback

If the frontend is deployed without the FastAPI service, the app automatically falls back to a privacy-sanitized benchmark derived from the [Kaggle Civic and Municipality Complaint System Dataset](https://www.kaggle.com/datasets/wajahattaj/civic-and-municipality-complaint-system-dataset). This prevents a missing `/api` service from producing a blank dashboard or a 404 on complaint submission. The header shows **Demo Dataset Active** in this mode. The benchmark is based on municipal records from multiple US cities and is not official Indian government data; production use requires authorized local data.

---

## 📖 Walkthrough Guide
For detailed instructions on testing the Ward 12 school consolidation, PII masking, and weight simulation, see [DEMO.md](DEMO.md).
