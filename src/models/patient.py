from typing import List, Optional
from pydantic import BaseModel, Field


class Demographics(BaseModel):
    age: Optional[int] = Field(None, description="Patient age in years")
    gender: Optional[str] = Field(None, description="Patient biological sex / gender")


class Diagnosis(BaseModel):
    condition_name: str = Field(..., description="Primary disease or cancer diagnosis (e.g. Non-Small Cell Lung Cancer)")
    stage: Optional[str] = Field(None, description="Cancer stage if applicable (e.g. Stage IV)")
    histology: Optional[str] = Field(None, description="Histological type or pathology detail")
    date_of_diagnosis: Optional[str] = Field(None, description="Date of initial diagnosis")


class Biomarker(BaseModel):
    gene_mutation: str = Field(..., description="Gene or biomarker symbol (e.g. EGFR, KRAS, PD-L1)")
    variant_or_status: str = Field(..., description="Mutation variant or status (e.g. G12C, Exon 19 deletion, >= 50%)")
    test_type: Optional[str] = Field(None, description="NGS, IHC, PCR, etc.")


class LabResult(BaseModel):
    test_name: str = Field(..., description="Lab test name (e.g. Platelets, eGFR, ALT, AST)")
    value: float = Field(..., description="Numeric lab value")
    unit: str = Field(..., description="Unit of measurement (e.g. /uL, mL/min)")
    is_normal: Optional[bool] = Field(None, description="Whether the lab result is within normal reference range")


class TreatmentHistory(BaseModel):
    therapy_name: str = Field(..., description="Name of drug, regimen, or treatment line (e.g. Pembrolizumab, Cisplatin)")
    treatment_type: Optional[str] = Field(None, description="Immunotherapy, Chemotherapy, Targeted, Surgery, Radiation")
    response_or_status: Optional[str] = Field(None, description="Completed, Progressed, Discontinued due to toxicity")


class PatientRecord(BaseModel):
    anonymized_id: str = Field(..., description="De-identified patient tracking ID")
    demographics: Demographics
    diagnosis: Diagnosis
    biomarkers: List[Biomarker] = Field(default_factory=list)
    lab_results: List[LabResult] = Field(default_factory=list)
    prior_treatments: List[TreatmentHistory] = Field(default_factory=list)
    comorbidities: List[str] = Field(default_factory=list, description="Existing secondary conditions or medical history")
    page_source_notes: List[str] = Field(default_factory=list, description="Source page numbers and reference notes")
