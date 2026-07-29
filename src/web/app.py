import os
import json
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.models.patient import PatientRecord
from src.models.trial import TrialProtocol
from src.models.match import MatchReport
from src.services.gemini_client import GeminiExtractor
from src.services.trial_fetcher import TrialFetcher
from src.engine.matcher import ClinicalTrialMatcher
from src.reports.pdf_generator import PDFReportExporter

app = FastAPI(
    title="TrialMind Web Dashboard",
    description="Autonomous Multimodal AI Agent for Clinical Trial Matching & EHR Intelligence",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class MatchRequestPayload(BaseModel):
    patient_text: Optional[str] = None
    trial_input: str  # NCT ID or JSON string
    model_name: str = "gemini-1.5-flash"


@app.get("/", response_class=HTMLResponse)
def index():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrialMind — Autonomous AI Clinical Trial Matcher</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .glow-blue { box-shadow: 0 0 25px rgba(56, 189, 248, 0.15); }
    </style>
</head>
<body class="min-h-screen pb-12">
    <!-- Header -->
    <header class="border-b border-slate-800 bg-slate-900/80 sticky top-0 z-50 backdrop-blur">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <span class="text-3xl">🏥</span>
                <div>
                    <h1 class="text-xl font-bold text-white tracking-tight">TrialMind</h1>
                    <p class="text-xs text-cyan-400 font-medium">Autonomous Clinical Trial Matching Agent</p>
                </div>
            </div>
            <div class="flex items-center space-x-3">
                <span class="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold rounded-full">Gemini 1.5 Powered</span>
                <span class="px-3 py-1 bg-slate-800 text-slate-300 text-xs font-semibold rounded-full border border-slate-700">v0.1.0</span>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 pt-8">
        <!-- Dashboard Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            <!-- Left Column: Inputs -->
            <div class="space-y-6">
                <!-- Patient EHR Box -->
                <div class="glass rounded-2xl p-6 glow-blue">
                    <h2 class="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
                        <span>📄</span> 1. Patient Medical Record (EHR)
                    </h2>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-xs font-medium text-slate-400 mb-1">Paste Unstructured Medical Notes</label>
                            <textarea id="patientText" rows="7" class="w-full bg-slate-900/90 border border-slate-700 rounded-xl p-3 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 font-mono" placeholder="Paste progress note, pathology report, or oncology summary..."></textarea>
                        </div>
                        
                        <div class="text-center text-xs text-slate-500 font-semibold uppercase tracking-wider">— OR —</div>
                        
                        <div>
                            <label class="block text-xs font-medium text-slate-400 mb-1">Upload Patient Record PDF</label>
                            <input type="file" id="patientFile" accept=".pdf,.txt" class="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-cyan-500/10 file:text-cyan-400 hover:file:bg-cyan-500/20 cursor-pointer bg-slate-900/50 border border-slate-800 rounded-xl">
                        </div>

                        <button onclick="loadSamplePatient()" class="text-xs text-cyan-400 hover:underline font-medium">✨ Load Synthetic Oncology Sample Patient</button>
                    </div>
                </div>

                <!-- Clinical Trial Protocol Box -->
                <div class="glass rounded-2xl p-6">
                    <h2 class="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
                        <span>🔬</span> 2. Target Clinical Trial Protocol
                    </h2>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-xs font-medium text-slate-400 mb-1">ClinicalTrials.gov NCT ID (e.g. NCT05123456) or Protocol JSON</label>
                            <input type="text" id="trialInput" value="NCT05123456" class="w-full bg-slate-900/90 border border-slate-700 rounded-xl p-3 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">
                        </div>
                        <button onclick="loadSampleTrial()" class="text-xs text-cyan-400 hover:underline font-medium">✨ Load Sample KRAS G12C Trial Protocol</button>
                    </div>
                </div>

                <!-- Execute Button -->
                <button id="runMatchBtn" onclick="runMatching()" class="w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold rounded-xl shadow-lg transition-all flex items-center justify-center space-x-2 text-base">
                    <span>🚀</span> <span>Run AI Match Evaluation Engine</span>
                </button>
            </div>

            <!-- Right Column: Results & Matrix -->
            <div class="space-y-6">
                <div id="resultsCard" class="glass rounded-2xl p-6 hidden">
                    <div class="flex items-center justify-between mb-4 border-b border-slate-800 pb-4">
                        <div>
                            <span class="text-xs text-slate-400 uppercase font-semibold tracking-wider">Evaluation Output</span>
                            <div id="statusBadge" class="text-2xl font-extrabold mt-1">ELIGIBLE</div>
                        </div>
                        <div class="text-right">
                            <span class="text-xs text-slate-400 block font-medium">Confidence Score</span>
                            <span id="confidenceScore" class="text-xl font-bold text-cyan-400">94.0%</span>
                        </div>
                    </div>

                    <!-- Summary -->
                    <div class="mb-6">
                        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Executive Summary</h3>
                        <p id="summaryText" class="text-sm text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-xl border border-slate-800"></p>
                    </div>

                    <!-- Actions Bar -->
                    <div class="flex space-x-3 mb-6">
                        <button onclick="downloadPDF()" class="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-xl flex items-center justify-center space-x-2 transition">
                            <span>📄</span> <span>Export Physician PDF Report</span>
                        </button>
                    </div>

                    <!-- Evaluation Table -->
                    <div>
                        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Criteria Matrix Evaluation</h3>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs border-collapse">
                                <thead>
                                    <tr class="border-b border-slate-800 text-slate-400 font-semibold bg-slate-900/50">
                                        <th class="p-2">ID</th>
                                        <th class="p-2">Type</th>
                                        <th class="p-2">Status</th>
                                        <th class="p-2">Clinical Evidence</th>
                                    </tr>
                                </thead>
                                <tbody id="criteriaTableBody" class="divide-y divide-slate-800/60"></tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Initial Empty State -->
                <div id="emptyState" class="glass rounded-2xl p-12 text-center text-slate-500">
                    <span class="text-5xl block mb-4">🩺</span>
                    <h3 class="text-base font-semibold text-slate-300">Ready to Evaluate Patient Eligibility</h3>
                    <p class="text-xs text-slate-400 mt-2 max-w-sm mx-auto">Provide a patient medical record and clinical trial protocol on the left to begin automated evaluation.</p>
                </div>
            </div>
        </div>
    </main>

    <script>
        const samplePatientText = `--- CLINICAL ONCOLOGY PROGRESS NOTE ---
Patient ID: ANON-NSCLC-2024-001
Age: 62 | Gender: Male
DIAGNOSIS: Stage IV Non-Small Cell Lung Cancer (NSCLC), Adenocarcinoma
BIOMARKERS: KRAS G12C positive (Exon 2), EGFR Wild-type, PD-L1 TPS 65%
LABS: ANC 2,400 /uL, Platelets 210,000 /uL, eGFR 78 mL/min
PRIOR TREATMENTS: Discontinued Pembrolizumab (Keytruda) due to progression.
COMORBIDITIES: Hypertension. Brain MRI clear (no brain metastases).`;

        let currentReport = null;

        function loadSamplePatient() {
            document.getElementById('patientText').value = samplePatientText;
        }

        function loadSampleTrial() {
            document.getElementById('trialInput').value = "NCT05123456";
        }

        async function runMatching() {
            const btn = document.getElementById('runMatchBtn');
            const patientText = document.getElementById('patientText').value;
            const patientFile = document.getElementById('patientFile').files[0];
            const trialInput = document.getElementById('trialInput').value;

            if (!patientText && !patientFile) {
                alert("Please paste medical notes or upload a patient PDF file.");
                return;
            }

            btn.disabled = true;
            btn.innerHTML = `<span>⏳</span><span>Analyzing with Gemini 1.5...</span>`;

            try {
                const formData = new FormData();
                if (patientFile) {
                    formData.append('patient_file', patientFile);
                } else {
                    formData.append('patient_text', patientText);
                }
                formData.append('trial_input', trialInput);

                const res = await fetch('/api/match', { method: 'POST', body: formData });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Match request failed.");
                }

                const data = await res.json();
                currentReport = data;
                renderReport(data.report);
            } catch (err) {
                alert("Error: " + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<span>🚀</span> <span>Run AI Match Evaluation Engine</span>`;
            }
        }

        function renderReport(report) {
            document.getElementById('emptyState').classList.add('hidden');
            const resultsCard = document.getElementById('resultsCard');
            resultsCard.classList.remove('hidden');

            const badge = document.getElementById('statusBadge');
            badge.innerText = report.overall_status;
            if (report.overall_status === 'ELIGIBLE') {
                badge.className = "text-2xl font-extrabold mt-1 text-emerald-400";
            } else if (report.overall_status === 'POTENTIALLY_ELIGIBLE') {
                badge.className = "text-2xl font-extrabold mt-1 text-amber-400";
            } else {
                badge.className = "text-2xl font-extrabold mt-1 text-red-500";
            }

            document.getElementById('confidenceScore').innerText = (report.confidence_score * 100).toFixed(1) + "%";
            document.getElementById('summaryText').innerText = report.summary;

            const tbody = document.getElementById('criteriaTableBody');
            tbody.innerHTML = '';

            report.evaluations.forEach(ev => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/40";
                
                let statusBadge = ev.status === 'MET' ? '<span class="text-emerald-400 font-bold">MET</span>' : 
                                 (ev.status === 'NOT_MET' ? '<span class="text-red-400 font-bold">NOT MET</span>' : '<span class="text-amber-400 font-bold">MISSING</span>');

                tr.innerHTML = `
                    <td class="p-2 text-slate-500 font-mono">${ev.criterion_id}</td>
                    <td class="p-2 font-medium text-slate-300">${ev.rule_type}</td>
                    <td class="p-2">${statusBadge}</td>
                    <td class="p-2 text-slate-300">${ev.reasoning}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function downloadPDF() {
            if (!currentReport) return;
            const res = await fetch('/api/report/pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentReport)
            });
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `TrialMind_Report_${currentReport.report.nct_id}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/match")
async def api_match(
    patient_text: Optional[str] = Form(None),
    patient_file: Optional[UploadFile] = File(None),
    trial_input: str = Form("NCT05123456"),
    model_name: str = Form("gemini-1.5-flash"),
):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY is not configured in .env")

    # Extract Patient Record
    extractor = GeminiExtractor(api_key=api_key, model_name=model_name)
    if patient_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf" if patient_file.filename.endswith(".pdf") else ".txt") as tmp:
            tmp.write(await patient_file.read())
            tmp_path = tmp.name
        try:
            if tmp_path.endswith(".pdf"):
                patient_record = extractor.extract_patient_from_pdf(tmp_path)
            else:
                with open(tmp_path, "r", encoding="utf-8") as f:
                    patient_record = extractor.extract_patient_from_text(f.read())
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    elif patient_text:
        patient_record = extractor.extract_patient_from_text(patient_text)
    else:
        raise HTTPException(status_code=400, detail="Must provide patient_text or patient_file")

    # Fetch Trial Protocol
    if trial_input.startswith("NCT"):
        trial_protocol = TrialFetcher.fetch_from_clinicaltrials_gov(trial_input)
    elif os.path.exists(trial_input):
        trial_protocol = TrialFetcher.load_from_file(trial_input)
    else:
        try:
            data = json.loads(trial_input)
            trial_protocol = TrialProtocol.model_validate(data)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Could not load trial protocol from input '{trial_input}'")

    # Match Evaluation
    matcher = ClinicalTrialMatcher(api_key=api_key, model_name=model_name)
    report = matcher.evaluate_match(patient_record, trial_protocol)

    return {
        "report": report.model_dump(),
        "patient": patient_record.model_dump(),
        "trial": trial_protocol.model_dump(),
    }


@app.post("/api/report/pdf")
def api_download_pdf(payload: dict):
    try:
        report = MatchReport.model_validate(payload["report"])
        patient = PatientRecord.model_validate(payload["patient"])
        trial = TrialProtocol.model_validate(payload["trial"])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name

        PDFReportExporter.generate_pdf(report, patient, trial, pdf_path)
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"TrialMind_Report_{trial.nct_id}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {e}")
