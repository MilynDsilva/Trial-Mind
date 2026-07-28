from typing import List, Optional
from pydantic import BaseModel, Field


class Criterion(BaseModel):
    id: str = Field(..., description="Criterion unique identifier (e.g. INC-01, EXC-02)")
    rule_type: str = Field(..., description="INCLUSION or EXCLUSION")
    description: str = Field(..., description="Raw text of the eligibility criterion")
    category: Optional[str] = Field(None, description="Category: Diagnosis, Biomarker, Lab, Age, PriorTherapy, Comorbidity")


class TrialProtocol(BaseModel):
    nct_id: str = Field(..., description="ClinicalTrials.gov NCT identifier (e.g. NCT05123456)")
    title: str = Field(..., description="Official title of the clinical trial study")
    phase: Optional[str] = Field(None, description="Trial Phase (Phase 1, Phase 2, Phase 3)")
    target_condition: str = Field(..., description="Primary condition targeted by trial")
    inclusion_criteria: List[Criterion] = Field(default_factory=list)
    exclusion_criteria: List[Criterion] = Field(default_factory=list)
