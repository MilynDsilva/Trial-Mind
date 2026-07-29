import os
import json
from typing import Union, Optional
from google import genai
from google.genai import types
from pydantic import ValidationError

from src.models.patient import PatientRecord


class GeminiExtractor:
    """Multimodal EHR Patient Record Extractor powered by Gemini 1.5."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is required. Please set it in your environment or .env file."
            )
        
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def extract_patient_from_text(self, medical_text: str) -> PatientRecord:
        """Ingests raw unstructured clinical notes and returns a validated PatientRecord model."""
        system_instruction = (
            "You are an expert clinical oncology NLP system. Analyze the medical chart text "
            "and extract all structured patient information including demographics, primary diagnosis, "
            "genomic/biomarker status, lab results, prior therapies, comorbidities, and page/source citations. "
            "Ensure all Protected Health Information (PHI) like names or SSNs are de-identified."
        )

        prompt = f"Analyze the following medical record and extract all patient attributes:\n\n{medical_text}"

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=PatientRecord,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )

        # Parse JSON response into Pydantic model
        try:
            return PatientRecord.model_validate_json(response.text)
        except ValidationError as e:
            # Fallback parsing in case response wrapping occurs
            data = json.loads(response.text)
            return PatientRecord.model_validate(data)

    def extract_patient_from_pdf(self, pdf_path: str) -> PatientRecord:
        """Ingests a PDF file (scanned or native text) and extracts a validated PatientRecord model."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

        # Use PyMuPDF to extract text content with page numbers
        import fitz
        doc = fitz.open(pdf_path)
        extracted_pages = []
        
        for i, page in enumerate(doc):
            extracted_pages.append(f"--- PAGE {i+1} ---\n{page.get_text()}")
        
        full_text = "\n\n".join(extracted_pages)
        return self.extract_patient_from_text(full_text)
