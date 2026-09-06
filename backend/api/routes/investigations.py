from backend.api.auth import get_current_workspace
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.persistence.database import get_db
from backend.persistence.repositories.investigations import InvestigationRepository
from backend.api.schemas.investigations import (
    ExperimentSchema, ExperimentResultSchema,
    InvestigationCreateRequest, 
    InvestigationResponse,
    InvestigationActionSchema,
    TimelineEventSchema
)
from backend.api.schemas.findings import FindingSchema
from core.loader import load_dataset_version
from core.profiler import Profiler
from core.quality.engine import QualityEngine, UniqueRule, NotNullRule
from core.investigation.models import Investigation, InvestigationStatus
from core.investigation.recommender import InvestigationRecommender

from backend.persistence.repositories.datasets import DatasetRepository
from backend.datasets.service import DatasetService

router = APIRouter(prefix="/investigations", tags=["Investigations"])

@router.post("", response_model=InvestigationResponse)
def create_investigation(req: InvestigationCreateRequest, db: Session = Depends(get_db)):
    try:
        dataset_repo = DatasetRepository(db)
        dataset_svc = DatasetService(dataset_repo)
        version = dataset_svc.get_latest_version(req.dataset_id)
        if not version:
            raise HTTPException(status_code=404, detail="Dataset not found or has no versions")
            
        inv = Investigation(
            title=req.title,
            description=req.description,
            dataset_version=version.version_id,
            status=InvestigationStatus.OPEN
        )
        
        rules = []
        for col in version.stats['columns'].keys():
            rules.append(NotNullRule(col))
            rules.append(UniqueRule(col))
            
        q_engine = QualityEngine()
        findings = q_engine.evaluate_rules(version, rules)
        inv.findings.extend(findings)
        
        inv.findings.sort(key=lambda f: f.impact_score, reverse=True)
        
        recommendations = []
        for f in inv.findings:
            actions = InvestigationRecommender.recommend(f)
            recommendations.extend(actions)
            
        repo = InvestigationRepository(db)
        repo.create(inv, recommendations)
        
        return InvestigationResponse(
            id=inv.id,
            title=inv.title,
            description=inv.description,
        dataset_version=inv.dataset_version,
        status=inv.status,
        created_at=inv.created_at,
        resolution=inv.resolution,
        findings=[FindingSchema.model_validate(f) for f in inv.findings],
        timeline=[TimelineEventSchema.model_validate(e) for e in inv.timeline.get_chronological_events()],
        hypotheses=[
              {
                  "id": h.id, 
                  "description": h.description, 
                  "status": h.status.value, 
                  "finding_id": h.finding_id, 
                  "attribution_id": h.attribution_id,
                  "validation_result": {
                      "status": h.validation_result.status.value,
                      "description": h.validation_result.description,
                      "evidence": [e.__dict__ for e in h.validation_result.evidence]
                  } if h.validation_result else None
              } for h in inv.hypotheses
          ],
        experiments=[ExperimentSchema.model_validate(e) for e in getattr(inv, "experiments", [])],
        recommendations=[InvestigationActionSchema.model_validate(a) for a in recommendations]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{id}", response_model=InvestigationResponse)
def get_investigation(id: str, workspace_id: str = Depends(get_current_workspace), db: Session = Depends(get_db)):
    repo = InvestigationRepository(db)
    from backend.persistence.repositories.datasets import DatasetRepository
    ds_repo = DatasetRepository(db)
    
    inv, recommendations = repo.get(id, workspace_id)
    
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    ds_name = "Unknown Dataset"
    ds_version_num = 0
    dv = ds_repo.get_version_by_id(inv.dataset_version, workspace_id)
    if dv:
        ds_version_num = dv.version_number
        ds = ds_repo.get_dataset_by_id(dv.dataset_id, workspace_id)
        if ds:
            ds_name = ds.name

    highest_severity = None
    severity_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    max_sev_val = 0
    for f in inv.findings:
        val = severity_map.get(f.severity.value, 0)
        if val > max_sev_val:
            max_sev_val = val
            highest_severity = f.severity.value

    strong_cands = sum(1 for h in inv.hypotheses if h.status.value == "SUPPORTED")
        
    return InvestigationResponse(
        dataset_name=ds_name,
        dataset_version_number=ds_version_num,
        highest_severity=highest_severity,
        strong_candidates_count=strong_cands,
        id=inv.id,
        title=inv.title,
        description=inv.description,
        dataset_version=inv.dataset_version,
        status=inv.status,
        created_at=inv.created_at,
        resolution=inv.resolution,
        findings=[FindingSchema.model_validate(f) for f in inv.findings],
        timeline=[TimelineEventSchema.model_validate(e) for e in inv.timeline.get_chronological_events()],
        hypotheses=[
              {
                  "id": h.id, 
                  "description": h.description, 
                  "status": h.status.value, 
                  "finding_id": h.finding_id, 
                  "attribution_id": h.attribution_id,
                  "validation_result": {
                      "status": h.validation_result.status.value,
                      "description": h.validation_result.description,
                      "evidence": [e.__dict__ for e in h.validation_result.evidence]
                  } if h.validation_result else None
              } for h in inv.hypotheses
          ],
        experiments=[ExperimentSchema.model_validate(e) for e in getattr(inv, "experiments", [])],
        recommendations=[InvestigationActionSchema.model_validate(a) for a in recommendations]
    )

from fastapi import Query
from typing import Optional
from core.findings.models import Severity
from core.investigation.models import Resolution
from backend.api.schemas.investigations import InvestigationUpdateRequest, PaginatedInvestigations

@router.patch("/{id}", response_model=InvestigationResponse)
def update_investigation(id: str, req: InvestigationUpdateRequest, workspace_id: str = Depends(get_current_workspace), db: Session = Depends(get_db)):
    repo = InvestigationRepository(db)
    inv, recommendations = repo.get(id, workspace_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    try:
        if req.resolution:
            res = Resolution(
                root_cause=req.resolution.root_cause,
                resolution_type=req.resolution.resolution_type,
                resolved_at=req.resolution.resolved_at,
                validation_result=req.resolution.validation_result
            )
            inv.transition_to(req.status, resolution=res)
        else:
            inv.transition_to(req.status)
            

        
        repo.update(inv)

        return InvestigationResponse(
            id=inv.id,
            title=inv.title,
            description=inv.description,
            dataset_version=inv.dataset_version,
            status=inv.status,
            created_at=inv.created_at,
            resolution=inv.resolution,
            findings=[FindingSchema.model_validate(f) for f in inv.findings],
            timeline=[TimelineEventSchema.model_validate(e) for e in inv.timeline.get_chronological_events()],
            hypotheses=[
              {
                  "id": h.id, 
                  "description": h.description, 
                  "status": h.status.value, 
                  "finding_id": h.finding_id, 
                  "attribution_id": h.attribution_id,
                  "validation_result": {
                      "status": h.validation_result.status.value,
                      "description": h.validation_result.description,
                      "evidence": [e.__dict__ for e in h.validation_result.evidence]
                  } if h.validation_result else None
              } for h in inv.hypotheses
          ],
        experiments=[ExperimentSchema.model_validate(e) for e in getattr(inv, "experiments", [])],
            recommendations=[InvestigationActionSchema.model_validate(a) for a in recommendations]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=PaginatedInvestigations)
def list_investigations(
    status: Optional[InvestigationStatus] = None,
    severity: Optional[Severity] = None,
    dataset_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    workspace_id: str = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    repo = InvestigationRepository(db)
    from backend.persistence.repositories.datasets import DatasetRepository
    ds_repo = DatasetRepository(db)
    
    invs, total = repo.list(workspace_id=workspace_id, status=status, severity=severity, dataset_id=dataset_id, search=search, page=page, page_size=page_size)
    
    items = []
    for inv, recs in invs:
        ds_name = "Unknown Dataset"
        ds_version_num = 0
        
        # Look up dataset version
        dv = ds_repo.get_version_by_id(inv.dataset_version, workspace_id)
        if dv:
            ds_version_num = dv.version_number
            ds = ds_repo.get_dataset_by_id(dv.dataset_id, workspace_id)
            if ds:
                ds_name = ds.name

        # Calculate enrichment stats
        highest_severity = None
        severity_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        max_sev_val = 0
        for f in inv.findings:
            val = severity_map.get(f.severity.value, 0)
            if val > max_sev_val:
                max_sev_val = val
                highest_severity = f.severity.value

        strong_cands = sum(1 for h in inv.hypotheses if h.status.value == "SUPPORTED")

        items.append(InvestigationResponse(
            id=inv.id,
            title=inv.title,
            description=inv.description,
            dataset_version=inv.dataset_version,
            status=inv.status,
            created_at=inv.created_at,
            resolution=inv.resolution,
            findings=[FindingSchema.model_validate(f) for f in inv.findings],
            timeline=[TimelineEventSchema.model_validate(e) for e in inv.timeline.get_chronological_events()],
            hypotheses=[
              {
                  "id": h.id, 
                  "description": h.description, 
                  "status": h.status.value, 
                  "finding_id": h.finding_id, 
                  "attribution_id": h.attribution_id,
                  "validation_result": {
                      "status": h.validation_result.status.value,
                      "description": h.validation_result.description,
                      "evidence": [e.__dict__ for e in h.validation_result.evidence]
                  } if h.validation_result else None
              } for h in inv.hypotheses
          ],
        experiments=[ExperimentSchema.model_validate(e) for e in getattr(inv, "experiments", [])],
            recommendations=[InvestigationActionSchema.model_validate(a) for a in recs],
            dataset_name=ds_name,
            dataset_version_number=ds_version_num,
            highest_severity=highest_severity,
            strong_candidates_count=strong_cands
        ))
        
    return PaginatedInvestigations(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

from pydantic import BaseModel
from core.investigation.experiment import Experiment, ExperimentStatus, ExperimentResult
from backend.copilot.service import CopilotService
from backend.copilot.providers.gemini import GeminiProvider, LLMRateLimitError, LLMProviderError
from backend.copilot.models import CopilotResponse
import time
from datetime import datetime, timezone

class CopilotRequest(BaseModel):
    query: str
    context: Optional[dict] = None

# Simple in-memory rate limiter: max 5 requests per 60 seconds globally 
# (In production, use Redis or slowapi keyed by IP/User)
_rate_limits = {"tokens": 5, "last_refill": time.time()}

def rate_limit_check():
    now = time.time()
    elapsed = now - _rate_limits["last_refill"]
    
    # Refill 1 token per 12 seconds (5 per min)
    _rate_limits["tokens"] = min(5.0, _rate_limits["tokens"] + (elapsed / 12.0))
    _rate_limits["last_refill"] = now
    
    if _rate_limits["tokens"] < 1.0:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a few seconds.")
    
    _rate_limits["tokens"] -= 1.0

@router.post("/{id}/copilot", response_model=CopilotResponse)
def ask_copilot(id: str, req: CopilotRequest, workspace_id: str = Depends(get_current_workspace), db: Session = Depends(get_db)):
    rate_limit_check()
    
    try:
        llm = GeminiProvider()
        service = CopilotService(db, llm)
        return service.ask(id, req.query, workspace_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except LLMRateLimitError as e:
        raise HTTPException(status_code=503, detail="The AI provider is currently overloaded. Please try again later.")
    except LLMProviderError as e:
        raise HTTPException(status_code=503, detail="The AI provider failed to generate a response.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        # We never expose full stack traces from the AI orchestration
        raise HTTPException(status_code=500, detail="Copilot failed to generate a response.")


class ExperimentCreateRequest(BaseModel):
    sql_query: str
    requested_by: str = "Copilot"

@router.post("/{id}/hypotheses/{hypothesis_id}/experiments", response_model=ExperimentSchema)
def create_experiment(id: str, hypothesis_id: str, request: ExperimentCreateRequest, workspace_id: str = Depends(get_current_workspace), db: Session = Depends(get_db)):
    repo = InvestigationRepository(db)
    inv, recs = repo.get(id, workspace_id)
    if not inv:
        raise HTTPException(404, "Investigation not found")
        
    exp = Experiment(
        hypothesis_id=hypothesis_id,
        sql_query=request.sql_query,
        requested_by=request.requested_by
    )
    inv.experiments.append(exp)
    
    repo.update(inv)

    return ExperimentSchema.model_validate(exp)

@router.post("/{id}/experiments/{experiment_id}/run", response_model=ExperimentSchema)
def run_experiment(id: str, experiment_id: str, workspace_id: str = Depends(get_current_workspace), db: Session = Depends(get_db)):
    repo = InvestigationRepository(db)
    inv, recs = repo.get(id, workspace_id)
    if not inv:
        raise HTTPException(404)
        
    exp = next((e for e in inv.experiments if e.id == experiment_id), None)
    if not exp:
        raise HTTPException(404)
        
    from core.execution.warehouse import ExperimentExecutionEngine
    from backend.persistence.models import DatasetVersionORM
    
    dv_orm = db.query(DatasetVersionORM).filter(DatasetVersionORM.id == inv.dataset_version).first()
    if not dv_orm:
        raise HTTPException(500, "Dataset version missing")
        
    engine = ExperimentExecutionEngine(dv_orm.storage_path)
    result = engine.execute_query(exp.sql_query)
    
    exp.result = result
    if result.error_message:
        exp.status = ExperimentStatus.FAILED
    else:
        exp.status = ExperimentStatus.COMPLETED
    exp.completed_at = datetime.now(timezone.utc)
    
    hyp = next((h for h in inv.hypotheses if h.id == exp.hypothesis_id), None)
    finding = next((f for f in inv.findings if f.id == hyp.finding_id), None) if hyp else None
    
    if hyp and finding:
        
        validation_result = HypothesisValidator.evaluate(exp, hyp, finding)
        
        # update dataset version in evidence accurately
        for ev in validation_result.evidence:
            ev.dataset_version = inv.dataset_version
            
        hyp.status = validation_result.status
        hyp.validation_result = validation_result
        
    from core.investigation.timeline import InvestigationEvent, EventType, EventSource
    inv.timeline.append(InvestigationEvent(
        event_type=EventType.EVIDENCE_COLLECTED,
        source=EventSource.SYSTEM,
        entity_id=exp.id,
        description=f"Experiment executed with {result.row_count} rows returned.",
        metadata={"sql": exp.sql_query, "success": not bool(result.error_message)}
    ))
    
    
    # Root Cause Candidates are re-evaluated dynamically during Copilot synthesis.
    
    repo.update(inv)

    return ExperimentSchema.model_validate(exp)



class MemoryRetrievalSchema(BaseModel):
    investigation_id: str
    title: str
    dataset_name: str
    similarity_score: float
    matched_factors: List[str]
    resolution_root_cause: Optional[str]
    resolved_at: Optional[datetime]

@router.get("/{id}/memory", response_model=List[MemoryRetrievalSchema])
def get_investigation_memory(id: str, workspace_id: str = Depends(get_current_workspace), db: Session = Depends(get_db)):
    repo = InvestigationRepository(db)
    from backend.persistence.repositories.datasets import DatasetRepository
    ds_repo = DatasetRepository(db)
    
    current_inv, _ = repo.get(id, workspace_id)
    if not current_inv:
        raise HTTPException(404, "Investigation not found")
        
    all_invs, _ = repo.list(workspace_id, page_size=1000) # In prod we'd use vector search or DB query
    
    def get_ds(dv_id):
        dv = ds_repo.get_version_by_id(dv_id, workspace_id)
        if not dv: return None
        return ds_repo.get_dataset_by_id(dv.dataset_id, workspace_id)
        
    from core.investigation.memory import MemoryEngine
    engine = MemoryEngine([i for i, _ in all_invs], get_ds)
    similar = engine.retrieve_similar(current_inv, limit=5)
    
    return [MemoryRetrievalSchema(**s.__dict__) for s in similar]

class HypothesisValidator:

    @staticmethod
    def evaluate(experiment, hypothesis, finding):
        from core.investigation.models import HypothesisStatus
        from core.evidence.models import Evidence, EvidenceType
        from core.investigation.hypothesis import ValidationResult
        
        if experiment.result and experiment.result.error_message:
            status = HypothesisStatus.REJECTED
            desc = f"Experiment failed to execute: {experiment.result.error_message}"
        elif experiment.result and experiment.result.row_count > 0:
            status = HypothesisStatus.SUPPORTED
            desc = f"Experiment found {experiment.result.row_count} rows supporting the hypothesis."
        else:
            status = HypothesisStatus.REJECTED
            desc = "Experiment executed successfully but returned 0 rows, contradicting the hypothesis."
            
        evidence = Evidence(
            type=EvidenceType.QUERY,
            source="ExperimentEngine",
            dataset_version="v2",
            metric="sql_experiment_result",
            value={"rows": experiment.result.row_count if experiment.result else 0, "error": experiment.result.error_message if experiment.result else None},
            description=desc
        )
        
        result = ValidationResult(status=status, description=desc)
        result.evidence.append(evidence)
        return result