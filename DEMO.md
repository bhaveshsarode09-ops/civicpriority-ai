# CivicPriority AI — End-to-End System Demonstration & Verification Guide

> **System Status**: Fully Operational · 54 Automated Tests Passing · Dual Vite/FastAPI Engine Active
> **Mandatory Disclaimer**: *DEMONSTRATION SYSTEM: Uses a privacy-sanitized Kaggle benchmark for simulation. Not connected to live municipal dispatch.*

---

## 1. Executive Summary & Purpose

CivicPriority AI transforms messy, fragmented citizen grievances into transparent, explainable, and ranked policy priorities for municipal commissioners and district collectors.

Traditional grievance systems suffer from:
1. **Channel fragmentation**: Town halls, written letters, WhatsApp messages, and web portals remain in separate silos.
2. **Vocal minority bias**: Affluent, digitally-connected wards file hundreds of complaints about minor issues (e.g., cosmetic gardening), while life-safety crises in underserved areas are reported only once or twice.
3. **Privacy risks**: Citizen phone numbers and personal emails are exposed to frontline clerks and contractors.
4. **Black-box decisions**: Citizens have no insight into why their issue is ignored while another is fixed.

CivicPriority AI solves this with:
- **Multilingual NLU** (Hindi, Marathi, English).
- **Zero-leak automated PII scrubbing** (phone numbers and emails replaced before triage; contacts securely salted and hashed).
- **TF-IDF + Ward graph clustering** merging reports about the same underlying civic failure.
- **Logarithmic population scaling & equity safeguards** preventing population density from crowding out rural emergencies.
- **Open mathematical score breakdown** showing exactly how every point ($/100$) was calculated.

---

## 2. Key Demonstration Walkthroughs

### Walkthrough 1: The Ward 12 Government School Crisis (Consolidation Across 5 Channels)
1. Navigate to the **Policy Dashboard** tab.
2. Observe the ranked cluster: **"Classroom Shortage & Sanitation crisis at Ward 12"**.
3. Notice the metadata:
   - **Composite Score**: **`70.1 / 100`** (High Priority).
   - **Consolidated Reports**: 6 distinct complaints (`CMP-SYN-001` through `CMP-SYN-006`).
   - **Reporting Channels**: `public_meeting`, `direct_web`, `messaging`, `letter_pdf`, `social_media`.
   - **Vulnerable Demographic**: Automatically flagged for **`Children`**.
4. Click **"Review Policy Breakdown & Evidence"** to open the modal:
   - **Points Breakdown**:
     - Severity: $+20.2$ pts ($30\%$ weight on $67.5/100$ severity)
     - People Affected: $+17.6$ pts ($25\%$ weight on $\sim 650$ affected students using $\log_{10}$ scaling)
     - Urgency: $+16.7$ pts ($20\%$ weight on $83.3/100$ urgency)
     - Infrastructure Deficit: $+9.6$ pts ($15\%$ weight on $64.1/100$ infrastructure gap)
     - Repeat Volume: $+6.0$ pts ($10\%$ weight on 6 consolidated reports)
     - **Total**: $70.1 / 100$
   - **Underlying Complaints**: Inspect both Hindi and English reports (`वार्ड 12 के प्राथमिक विद्यालय में पीने का पानी नहीं है...`). Observe how phone numbers are masked to `[PHONE_REDACTED]` and contact hashes are preserved.

---

### Walkthrough 2: Zero-Leak Privacy & Automated PII Scrubbing
1. Open the **Citizen Grievance Intake** tab.
2. In the complaint text area, type:
   > *"Emergency: Sewage pipeline ruptured near central park. Call Ramesh immediately at 9876543210 or email ramesh.kumar@example.com."*
3. Watch the **Real-Time PII Masking Preview** box below the text area:
   - The phone number is dynamically replaced with **`[PHONE_REDACTED]`**.
   - The email is dynamically replaced with **`[EMAIL_REDACTED]`**.
4. Click **"Submit & Auto-Triage"**:
   - The complaint is assigned a permanent identifier (e.g. `CMP-DIR-0056`).
   - The citizen contact is salted and hashed into a 64-character SHA-256 string.
   - The raw contact is never stored in plain text or transmitted to external AI models.

---

### Walkthrough 3: Spatial Equity & Fairness Safeguards
1. Filter the **Policy Dashboard** by **Ward 15** or **Ward 4**.
2. Locate high-severity issues with low report volume (e.g. collapsed sewer cover, sparking transformer, or open borewell).
3. Notice the gold **Fairness Safeguard Active** banner:
   > *"Fairness Alert: High-severity grievance with low report count. Flagged to prevent demographic and frequency bias against underserved areas."*
4. The system guarantees that an urgent issue reported by a single marginalized citizen at a town hall is not deprioritized against dozens of minor cosmetic complaints from wealthy subdivisions.

---

### Walkthrough 4: Priority Formula Weight Simulation
1. On the **Policy Dashboard**, click **"Tune Weights ▼"** to expand the slider panel.
2. Current policy defaults:
   - Issue Severity: **30%**
   - People Affected (Log scale): **25%**
   - Time Urgency: **20%**
   - Infrastructure Gap: **15%**
   - Repeat Volume: **10%**
3. Shift the **Time Urgency** slider up to **50%** and **Repeat Volume** down to **5%**.
4. Click **"Recalculate Rankings"**:
   - The backend runs `POST /api/pipeline/recluster` with the new formula.
   - Immediate life-safety emergencies surge to the top of the ranked list.
5. Click **"Reset Defaults"** to restore standard municipal policy weights.

---

### Walkthrough 5: Public Transparency & Citizen Tracking
1. Switch to the **Public Transparency View** tab.
2. Citizens can read the plain-language guide detailing the 5 pillars of municipal prioritization.
3. In the **"Track Your Grievance Status & Public Impact"** search box:
   - Enter `CMP-SYN-001`.
   - Click **"Track Grievance"**.
   - The portal instantly informs the citizen:
     > *"Found! Consolidated into Municipal Action Cluster: CLU-WARD12-EDUCATION-19: Classroom Shortage & Sanitation crisis at Ward 12."*
     > *Current Status: Under Review · Assigned to Department of School Education.*

---

### Walkthrough 6: Administrative Workflow & Department Dispatch
1. Click on any cluster card (e.g. Ward 7 Road Crater).
2. In the modal, locate the **Administrative Triage & Department Dispatch** section.
3. Select **Workflow Status**: Change from `Open` $\to$ `Under Review` $\to$ `In Progress`.
4. Select **Responsible Department**: Assign to `Public Works Department (Roads)`.
5. Enter **Audit Notes**: *"Pothole repair team dispatched with 2 metric tons of asphalt. Inspection scheduled for tomorrow 10:00 AM."*
6. Click **"Save Status & Dispatch"**:
   - Updates persist to the SQLite database via `PATCH /api/clusters/{id}`.
   - Status updates are instantly reflected across both the Policy Dashboard and the Public Transparency portal.

---

## 3. Automated Test Verification Summary

The codebase includes 54 comprehensive automated tests verifying all functionality:

| Test File | Focus | Test Count | Status |
|:---|:---|:---:|:---:|
| `test_models.py` | Data validation, Pydantic bounds, SQLite roundtrip | 7 | **PASSED** |
| `test_privacy.py` | Phone, email, Aadhaar masking, salted contact hashing | 8 | **PASSED** |
| `test_scoring.py` | Multi-factor formula, log scaling, fairness warnings | 6 | **PASSED** |
| `test_connectors.py` | CSV, text, meeting transcript, social media, messaging | 7 | **PASSED** |
| `test_clustering.py` | TF-IDF text similarity, ward matching, cross-ward isolation | 5 | **PASSED** |
| `test_ai_providers.py` | Multilingual NLU, Hindi/Marathi extraction, confidence | 5 | **PASSED** |
| `test_api.py` | FastAPI endpoints, filtering, pagination, patch workflow | 9 | **PASSED** |
| `test_e2e_flow.py` | End-to-end 9-step demonstration lifecycle | 7 | **PASSED** |
| **Total** | | **54 tests** | **100% Pass** |

Run the full suite at any time using:
```bash
PYTHONPATH=backend/src /opt/venv/bin/pytest backend/tests/ -v
```
