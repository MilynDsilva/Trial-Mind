import json
import os
from typing import Optional
from google import genai
from google.genai import types

from src.models.patient import PatientRecord
from src.models.trial import TrialProtocol
from src.models.match import MatchReport, MatchStatus, CriterionEvaluation


class ClinicalTrialMatcher:
    """Deterministic & AI-reasoned matching engine comparing PatientRecord against TrialProtocol."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY is required for ClinicalTrialMatcher.")
        
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def evaluate_match(self, patient: PatientRecord, trial: TrialProtocol) -> MatchReport:
        """Evaluates patient attributes against trial eligibility criteria and generates a MatchReport."""
        system_instruction = (
            "You are an expert clinical oncology trial matching system. Your job is to strictly "
            "and deterministically compare a patient's extracted medical profile against the inclusion "
            "and exclusion criteria of a clinical trial. For every single criterion:\n"
            "1. Determine status: MET, NOT_MET, or MISSING_DATA.\n"
            "2. Provide clear clinical reasoning.\n"
            "3. Cite evidence quotes from patient record where applicable.\n\n"
            "Determine overall status:\n"
            "- ELIGIBLE: All inclusion criteria MET, zero exclusion criteria MET.\n"
            "- POTENTIALLY_ELIGIBLE: Minor missing data or test required (e.g. recent lab work).\n"
            "- INELIGIBLE: Fails any hard inclusion criterion or triggers an exclusion criterion."
        )

        patient_json = patient.model_dump_json(indent=2)
        trial_json = trial.model_dump_json(indent=2)

        prompt = (
            f"--- PATIENT RECORD ---\n{patient_json}\n\n"
            f"--- TRIAL PROTOCOL ---\n{trial_json}\n\n"
            "Evaluate patient eligibility line-by-line and produce the structured MatchReport."
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=MatchReport,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        try:
            report = MatchReport.model_validate_json(response.text)
        except Exception:
            data = json.loads(response.text)
            report = MatchReport.model_validate(data)

        return report
