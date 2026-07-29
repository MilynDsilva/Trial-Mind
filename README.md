# 🏥 TrialMind

> **Autonomous Multimodal AI Agent for Clinical Trial Matching & EHR Intelligence**

**TrialMind** is an enterprise-grade AI agent powered by Google's **Gemini 1.5** models. It bridges the gap between complex, unstructured patient Electronic Health Records (EHR) and clinical trial protocols to automate patient eligibility evaluation with audit-ready citations.

---

## 🎯 Problem Statement

- **Recruitment Bottleneck:** Over 80% of clinical trials fail or experience severe delays due to delayed patient recruitment.
- **Data Fragmentation:** Patient records contain hundreds of pages of unstructured data across scanned paper notes, pathology PDFs, genomic panels, and lab results.
- **Criteria Complexity:** Clinical trial protocols specify 30+ complex inclusion and exclusion rules.
- **Manual Overhead:** Oncologists and research nurses spend hours manually reviewing charts to evaluate trial eligibility.

---

## 💡 Solution: TrialMind

TrialMind automates the clinical trial matching workflow using Gemini's long-context vision and structured reasoning capabilities.

```
┌─────────────────────────────┐       ┌──────────────────────────────┐
│  Patient EHR (PDF / Image)  │       │ Clinical Trial Protocol (NCT)│
└──────────────┬──────────────┘       └──────────────┬───────────────┘
               │                                     │
               ▼                                     ▼
┌─────────────────────────────┐       ┌──────────────────────────────┐
│  Multimodal EHR Extractor   │       │ Protocol Criteria Compiler   │
└──────────────┬──────────────┘       └──────────────┬───────────────┘
               │                                     │
               └──────────────────┬──────────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ TrialMind Matching Engine     │
                  │ (Gemini 1.5 Pro / Flash)      │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ Audit Report & Citation Output│
                  │ (Eligible / Action Required)  │
                  └───────────────────────────────┘
```

---

## ✨ Key Features

- 📄 **Multimodal Document Parsing:** Ingests raw PDFs, faxed documents, scanned charts, and lab images natively using Gemini Vision.
- 🔒 **De-Identification & Privacy:** Pre-processes records to strip Protected Health Information (PHI) prior to analysis.
- 🧬 **Genomic & Biomarker Extraction:** Extracts disease stage, histology, and mutation status (e.g., *EGFR*, *KRAS G12C*, *PD-L1* expression).
- 🎯 **Deterministic Matching:** Evaluates criteria line-by-line and outputs verified status (`Eligible`, `Potentially Eligible`, `Ineligible`).
- 📍 **Page-Level Audit Trail:** Links every decision to exact page numbers and evidence quotes from the patient record for instant clinical verification.

---

## 🛠️ Technology Stack

- **AI Core:** Google Gemini 1.5 Pro / Flash (via Google Cloud Vertex AI or GenAI SDK)
- **Backend:** Python 3.10+, FastAPI, Pydantic (Structured JSON Outputs)
- **Document Processing:** PyMuPDF (`fitz`), `pdfplumber`
- **Orchestration:** LangGraph / Deterministic State Machine
- **Testing & Evals:** PyTest, DeepEval

---

## 🗺️ Project Roadmap & Current Progress

- [x] **Phase 1: Project Setup & Agent Guidelines** (`AGENTS.md`)
- [x] **Phase 2: Core Data Models & Gemini Extraction Pipeline** (`src/models/`, `src/services/gemini_client.py`)
- [x] **Phase 3: Trial Protocol Parser & Rule Engine** (`src/services/trial_fetcher.py`, `src/engine/matcher.py`)
- [ ] **Phase 4: Audit & Citation Report Generator** (PDF Exporter & Evidence Citations)
- [ ] **Phase 5: CLI & FastAPI Web Dashboard**

---

## ⚠️ Medical Disclaimer

TrialMind is an AI clinical decision-support tool built for research and administrative acceleration. It does **not** provide formal medical diagnoses or replace clinical judgment. All trial eligibility determinations must be verified by a licensed clinician.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
