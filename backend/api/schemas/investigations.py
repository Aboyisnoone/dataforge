from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from core.investigation.models import InvestigationStatus
from backend.api.schemas.findings import FindingSchema
from core.investigation.recommender import ActionPriority

class InvestigationCreateRequest(BaseModel):
    title: str
    description: str
    dataset_id: str

class ResolutionSchema(BaseModel):
    root_cause: str
    resolution_type: str
    resolved_at: datetime
    validation_result: str
    model_config = ConfigDict(from_attributes=True)

class InvestigationActionSchema(BaseModel):
    type: str
    target: str
    rationale: str
    priority: ActionPriority
    model_config = ConfigDict(from_attributes=True)

class TimelineEventSchema(BaseModel):
    event_type: str
    source: str
    entity_id: str
    description: str
    metadata: dict
    timestamp: datetime
    sequence_number: int
    id: str
    model_config = ConfigDict(from_attributes=True)


class ExperimentResultSchema(BaseModel):
    row_count: int
    columns: List[str]
    sample_rows: List[dict]
    execution_time_ms: float
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ExperimentSchema(BaseModel):
    id: str
    hypothesis_id: str
    sql_query: str
    requested_by: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[ExperimentResultSchema] = None
    model_config = ConfigDict(from_attributes=True)

class ValidationResultSchema(BaseModel):
    status: str
    description: str
    evidence: List[dict] = []
    model_config = ConfigDict(from_attributes=True)

class HypothesisSchema(BaseModel):
    id: str
    description: str
    status: str
    finding_id: Optional[str] = None
    attribution_id: Optional[str] = None
    validation_result: Optional[ValidationResultSchema] = None
    model_config = ConfigDict(from_attributes=True)

class InvestigationResponse(BaseModel):
    id: str
    title: str
    description: str
    dataset_version: str
    status: InvestigationStatus
    created_at: datetime
    resolution: Optional[ResolutionSchema] = None
    findings: List[FindingSchema]
    timeline: List[TimelineEventSchema] = []
    hypotheses: List[HypothesisSchema] = []
    experiments: List[ExperimentSchema] = []
    recommendations: List[InvestigationActionSchema] = []
    
    # Enrichment fields for Inbox
    dataset_name: Optional[str] = None
    dataset_version_number: Optional[int] = None
    strong_candidates_count: int = 0
    highest_severity: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class InvestigationUpdateRequest(BaseModel):
    status: InvestigationStatus
    resolution: Optional[ResolutionSchema] = None

class PaginatedInvestigations(BaseModel):
    items: List[InvestigationResponse]
    total: int
    page: int
    page_size: int
