from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    POTENTIALLY_ELIGIBLE = "POTENTIALLY_ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


class CriterionEvaluation(BaseModel):
    criterion_id: str = Field(..., description="ID of evaluated criterion")
    rule_type: str = Field(..., description="INCLUSION or EXCLUSION")
    criterion_text: str = Field(..., description="Text of the rule")
    status: str = Field(..., description="MET, NOT_MET, or MISSING_DATA")
    reasoning: str = Field(..., description="Detailed medical reasoning for decision")
    evidence_quote: Optional[str] = Field(None, description="Direct quote from patient chart")
    page_citation: Optional[str] = Field(None, description="Page number and section reference")


class MatchReport(BaseModel):
    patient_id: str = Field(..., description="Patient de-identified ID")
    nct_id: str = Field(..., description="Trial NCT identifier")
    overall_status: MatchStatus = Field(..., description="Final match status")
    confidence_score: float = Field(..., description="Match confidence between 0.0 and 1.0")
    summary: str = Field(..., description="Executive summary of the trial match evaluation")
    evaluations: List[CriterionEvaluation] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list, description="Follow-up tests or missing data required")
