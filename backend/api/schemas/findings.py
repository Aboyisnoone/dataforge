from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from core.findings.models import FindingCategory, Severity
from core.evidence.models import EvidenceType

class ObservationSchema(BaseModel):
    id: str
    metric: str
    value: Any
    column: str
    dataset_version: str
    description: str
    model_config = ConfigDict(from_attributes=True)

class EvidenceSchema(BaseModel):
    id: str
    type: EvidenceType
    source: str
    dataset_version: str
    metric: str
    value: Any
    description: str
    model_config = ConfigDict(from_attributes=True)

class FindingSchema(BaseModel):
    id: str
    title: str
    description: str
    category: FindingCategory
    severity: Severity
    confidence: float
    impact_score: float
    column: Optional[str]
    rule: Optional[str]
    observations: List[ObservationSchema]
    evidence: List[EvidenceSchema]
    model_config = ConfigDict(from_attributes=True)
