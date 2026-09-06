from sqlalchemy.orm import Session
from typing import Tuple, List, Optional
from backend.persistence import models
from core.investigation.models import Investigation, InvestigationStatus, Resolution
from core.investigation.experiment import Experiment, ExperimentStatus, ExperimentResult
from core.investigation.hypothesis import Hypothesis, HypothesisStatus
from core.investigation.hypothesis import ValidationResult
from core.investigation.timeline import InvestigationEvent, EventType, EventSource
from core.findings.models import Finding, FindingCategory, Severity, Observation
from core.evidence.models import Evidence, EvidenceType
from core.investigation.recommender import InvestigationAction, ActionPriority
import json

class InvestigationRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, orm: models.InvestigationORM) -> Tuple[Investigation, List[InvestigationAction]]:
        # Initialize directly to avoid triggering __post_init__ events
        inv = Investigation.__new__(Investigation)
        inv.id = orm.id
        inv.title = orm.title
        inv.description = orm.description
        inv.dataset_version = orm.dataset_version
        inv.status = InvestigationStatus(orm.status)
        inv.created_at = orm.created_at
        inv.findings = []
        inv.hypotheses = []
        inv.experiments = []
        inv.resolution = None
        
        # We manually setup the timeline
        from core.investigation.timeline import InvestigationTimeline
        inv.timeline = InvestigationTimeline(investigation_id=inv.id)

        if orm.res_root_cause:
            inv.resolution = Resolution(
                root_cause=orm.res_root_cause,
                resolution_type=orm.res_resolution_type,
                resolved_at=orm.res_resolved_at,
                validation_result=orm.res_validation_result
            )
            
        for f_orm in orm.findings:
            f = Finding(
                id=f_orm.id,
                title=f_orm.title,
                description=f_orm.description,
                category=FindingCategory(f_orm.category),
                severity=Severity(f_orm.severity),
                confidence=f_orm.confidence,
                impact_score=f_orm.impact_score,
                column=f_orm.column_name,
                rule=f_orm.rule_name,
                observations=[],
                evidence=[]
            )
            for o_orm in f_orm.observations:
                obs = Observation(
                    id=o_orm.id,
                    metric=o_orm.metric,
                    value=o_orm.value_json,
                    column=o_orm.column_name,
                    dataset_version=o_orm.dataset_version,
                    description=o_orm.description
                )
                f.observations.append(obs)
                
            for e_orm in f_orm.evidence:
                ev = Evidence(
                    id=e_orm.id,
                    type=EvidenceType(e_orm.type),
                    source=e_orm.source,
                    dataset_version=e_orm.dataset_version,
                    metric=e_orm.metric,
                    value=e_orm.value_json,
                    description=e_orm.description
                )
                f.evidence.append(ev)
                
            inv.findings.append(f)
            
        for h_orm in orm.hypotheses:
            h = Hypothesis(
                investigation_id=inv.id,
                finding_id=h_orm.finding_id,
                attribution_id=h_orm.attribution_id,
                description=h_orm.description,
                status=HypothesisStatus(h_orm.status),
                created_at=h_orm.created_at,
                id=h_orm.id
            )
            
            if h_orm.validation_result:
                v_orm = h_orm.validation_result
                evs = []
                for e_orm in v_orm.evidence:
                    evs.append(Evidence(
                        id=e_orm.id,
                        type=EvidenceType(e_orm.type),
                        source=e_orm.source,
                        dataset_version=e_orm.dataset_version,
                        metric=e_orm.metric,
                        value=e_orm.value_json,
                        description=e_orm.description
                    ))
                h.validation_result = ValidationResult(status=HypothesisStatus(v_orm.status), description=v_orm.description, evidence=evs),
                h.validation_result = ValidationResult(status=HypothesisStatus(v_orm.status), description=v_orm.description, evidence=evs)
            inv.hypotheses.append(h)
            
        for t_orm in sorted(orm.timeline_events, key=lambda x: x.sequence_number):
            evt = InvestigationEvent(
                id=t_orm.id,
                event_type=EventType(t_orm.event_type),
                source=EventSource(t_orm.source),
                entity_id=t_orm.entity_id,
                description=t_orm.description,
                metadata=t_orm.metadata_json,
                timestamp=t_orm.timestamp,
                sequence_number=t_orm.sequence_number
            )
            inv.timeline.events.append(evt)
            inv.timeline._current_sequence = max(inv.timeline._current_sequence, t_orm.sequence_number)
            
        recs = []
        for r_orm in orm.recommendations:
            recs.append(InvestigationAction(
                type=r_orm.type,
                target=r_orm.target,
                rationale=r_orm.rationale,
                priority=ActionPriority(r_orm.priority)
            ))
            

        if hasattr(orm, "experiments") and orm.experiments:
            for exp_orm in orm.experiments:
                exp = Experiment(
                    id=exp_orm.id,
                    hypothesis_id=exp_orm.hypothesis_id,
                    sql_query=exp_orm.sql_query,
                    requested_by=exp_orm.requested_by,
                    status=ExperimentStatus(exp_orm.status),
                    created_at=exp_orm.created_at,
                    completed_at=exp_orm.completed_at
                )
                if exp_orm.result_json:
                    exp.result = ExperimentResult(**exp_orm.result_json)
                inv.experiments.append(exp)

        return inv, recs

    def create(self, inv: Investigation, recommendations: List[InvestigationAction] = None) -> None:
        db_inv = models.InvestigationORM(
            id=inv.id,
            title=inv.title,
            description=inv.description,
            dataset_version=inv.dataset_version,
            status=inv.status.value,
            created_at=inv.created_at
        )
        if inv.resolution:
            db_inv.res_root_cause = inv.resolution.root_cause
            db_inv.res_resolution_type = inv.resolution.resolution_type
            db_inv.res_resolved_at = inv.resolution.resolved_at
            db_inv.res_validation_result = inv.resolution.validation_result
            
        for f in inv.findings:
            db_f = models.FindingORM(
                id=f.id,
                title=f.title,
                description=f.description,
                category=f.category.value,
                severity=f.severity.value,
                confidence=f.confidence,
                impact_score=f.impact_score,
                column_name=f.column,
                rule_name=f.rule
            )
            for o in f.observations:
                db_f.observations.append(models.ObservationORM(
                    id=o.id,
                    metric=o.metric,
                    value_json=o.value,
                    column_name=o.column,
                    dataset_version=o.dataset_version,
                    description=o.description
                ))
            for e in f.evidence:
                db_f.evidence.append(models.EvidenceORM(
                    id=e.id,
                    type=e.type.value,
                    source=e.source,
                    dataset_version=e.dataset_version,
                    metric=e.metric,
                    value_json=e.value,
                    description=e.description
                ))
            db_inv.findings.append(db_f)
            
        if recommendations:
            for r in recommendations:
                db_inv.recommendations.append(models.RecommendationORM(
                    type=r.type,
                    target=r.target,
                    rationale=r.rationale,
                    priority=r.priority.value
                ))
                
        for h in inv.hypotheses:
            h_orm = models.HypothesisORM(
                id=h.id,
                finding_id=h.finding_id,
                attribution_id=h.attribution_id,
                description=h.description,
                status=h.status.value,
                created_at=h.created_at
            )
            if h.validation_result:
                v = h.validation_result
                v_orm = models.ValidationResultORM(
                    id=getattr(v, "id", "val_" + __import__("uuid").uuid4().hex[:8]),
                    status=v.status.value,
                    description=v.description,
                    validated_at=getattr(v, "validated_at", __import__("datetime").datetime.now(__import__("datetime").timezone.utc))
                )
                for e in v.evidence:
                    v_orm.evidence.append(models.ValidationEvidenceORM(
                        id=e.id,
                        type=e.type.value,
                        source=e.source,
                        dataset_version=e.dataset_version,
                        metric=e.metric,
                        value_json=e.value,
                        description=e.description
                    ))
                h_orm.validation_result = v_orm
                
            db_inv.hypotheses.append(h_orm)
            
        for t in inv.timeline.events:
            db_inv.timeline_events.append(models.TimelineEventORM(
                id=t.id,
                event_type=t.event_type.value,
                source=t.source.value,
                entity_id=t.entity_id,
                description=t.description,
                metadata_json=t.metadata,
                timestamp=t.timestamp,
                sequence_number=t.sequence_number
            ))
                

        if hasattr(inv, "experiments") and inv.experiments:
            for exp in inv.experiments:
                db_inv.experiments.append(models.ExperimentORM(
                    id=exp.id,
                    hypothesis_id=exp.hypothesis_id,
                    sql_query=exp.sql_query,
                    requested_by=exp.requested_by,
                    status=exp.status.value,
                    created_at=exp.created_at,
                    completed_at=exp.completed_at,
                    result_json=exp.result.__dict__ if exp.result else None
                ))


        if hasattr(inv, "experiments") and inv.experiments:
            for exp in inv.experiments:
                db_inv.experiments.append(models.ExperimentORM(
                    id=exp.id,
                    hypothesis_id=exp.hypothesis_id,
                    sql_query=exp.sql_query,
                    requested_by=exp.requested_by,
                    status=exp.status.value,
                    created_at=exp.created_at,
                    completed_at=exp.completed_at,
                    result_json=exp.result.__dict__ if exp.result else None
                ))
        self.db.add(db_inv)

        self.db.commit()

    def get(self, id: str, workspace_id: str) -> Tuple[Optional[Investigation], List[InvestigationAction]]:
        orm = self.db.query(models.InvestigationORM).filter(models.InvestigationORM.id == id, models.InvestigationORM.workspace_id == workspace_id).first()
        if not orm:
            return None, []
        return self._to_domain(orm)

    def update(self, inv: Investigation) -> None:
        orm = self.db.query(models.InvestigationORM).filter(models.InvestigationORM.id == inv.id).first()
        if not orm:
            raise ValueError("Investigation not found")
            
        orm.status = inv.status.value
        if inv.resolution:
            orm.res_root_cause = inv.resolution.root_cause
            orm.res_resolution_type = inv.resolution.resolution_type
            orm.res_resolved_at = inv.resolution.resolved_at
            orm.res_validation_result = inv.resolution.validation_result
            
        # Update Hypotheses
        existing_hyps = {h.id: h for h in orm.hypotheses}
        for h in inv.hypotheses:
            if h.id not in existing_hyps:
                h_orm = models.HypothesisORM(
                    id=h.id,
                    finding_id=h.finding_id,
                    attribution_id=h.attribution_id,
                    description=h.description,
                    status=h.status.value,
                    created_at=h.created_at
                )
                orm.hypotheses.append(h_orm)
                existing_hyps[h.id] = h_orm
            
            # Update existing status
            existing_hyps[h.id].status = h.status.value
            
            # Add Validation Result if missing in DB but present in domain
            h_orm = existing_hyps[h.id]
            if h.validation_result and not h_orm.validation_result:
                v = h.validation_result
                v_orm = models.ValidationResultORM(
                    id=getattr(v, "id", "val_" + __import__("uuid").uuid4().hex[:8]),
                    status=v.status.value,
                    description=v.description,
                    validated_at=getattr(v, "validated_at", __import__("datetime").datetime.now(__import__("datetime").timezone.utc))
                )
                for e in v.evidence:
                    v_orm.evidence.append(models.ValidationEvidenceORM(
                        id=e.id,
                        type=e.type.value,
                        source=e.source,
                        dataset_version=e.dataset_version,
                        metric=e.metric,
                        value_json=e.value,
                        description=e.description
                    ))
                h_orm.validation_result = v_orm
                
        # Update Timeline Events
        existing_evt_ids = {e.id for e in orm.timeline_events}
        for t in inv.timeline.events:
            if t.id not in existing_evt_ids:
                orm.timeline_events.append(models.TimelineEventORM(
                    id=t.id,
                    event_type=t.event_type.value,
                    source=t.source.value,
                    entity_id=t.entity_id,
                    description=t.description,
                    metadata_json=t.metadata,
                    timestamp=t.timestamp,
                    sequence_number=t.sequence_number
                ))
            


        existing_exps = {e.id for e in orm.experiments} if hasattr(orm, "experiments") else set()
        if hasattr(inv, "experiments") and inv.experiments:
            for exp in inv.experiments:
                if exp.id not in existing_exps:
                    orm.experiments.append(models.ExperimentORM(
                        id=exp.id,
                        hypothesis_id=exp.hypothesis_id,
                        sql_query=exp.sql_query,
                        requested_by=exp.requested_by,
                        status=exp.status.value,
                        created_at=exp.created_at,
                        completed_at=exp.completed_at,
                        result_json=exp.result.__dict__ if exp.result else None
                    ))
                else:
                    for exp_orm in orm.experiments:
                        if exp_orm.id == exp.id:
                            exp_orm.status = exp.status.value
                            exp_orm.completed_at = exp.completed_at
                            exp_orm.result_json = exp.result.__dict__ if exp.result else None
                            break
        self.db.commit()

    def list(self, workspace_id: str, status: Optional[InvestigationStatus] = None, 
             severity: Optional[Severity] = None,
             dataset_id: Optional[str] = None,
             search: Optional[str] = None,
             page: int = 1, page_size: int = 10) -> Tuple[List[Tuple[Investigation, List[InvestigationAction]]], int]:
             
        query = self.db.query(models.InvestigationORM).filter(models.InvestigationORM.workspace_id == workspace_id)
        
        if status:
            query = query.filter(models.InvestigationORM.status == status.value)
            
        if dataset_id:
            query = query.join(models.DatasetVersionORM, models.InvestigationORM.dataset_version == models.DatasetVersionORM.id).filter(models.DatasetVersionORM.dataset_id == dataset_id)
            
        if search:
            query = query.filter(
                (models.InvestigationORM.title.ilike(f"%{search}%")) | 
                (models.InvestigationORM.description.ilike(f"%{search}%"))
            )
            
        if severity:
            query = query.join(models.FindingORM).filter(models.FindingORM.severity == severity.value)
            
        # Order by newest first
        query = query.order_by(models.InvestigationORM.created_at.desc())
            
        total = query.count()
        
        orms = query.offset((page - 1) * page_size).limit(page_size).all()
        
        results = []
        for orm in orms:
            results.append(self._to_domain(orm))
            
        return results, total