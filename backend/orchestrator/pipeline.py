from fastapi import UploadFile
from sqlalchemy.orm import Session
import uuid

from backend.datasets.service import DatasetService
from backend.persistence.repositories.datasets import DatasetRepository
from backend.persistence.repositories.investigations import InvestigationRepository

from core.dataset.models import DatasetVersion
from core.diff import HistoricalDiffEngine, DatasetDiff
from core.attribution.engine import AttributionEngine
from core.evidence.models import Evidence, EvidenceType
from core.investigation.models import Investigation, InvestigationStatus
from core.investigation.hypothesis import Hypothesis, HypothesisStatus
from core.findings.models import Finding, FindingCategory, Severity

class PipelineOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.ds_repo = DatasetRepository(db)
        self.inv_repo = InvestigationRepository(db)
        self.ds_service = DatasetService(self.ds_repo)

    def process_new_version(self, dataset_id: str, file: UploadFile, workspace_id: str) -> DatasetVersion:
        dataset = self.ds_repo.get_dataset_by_id(dataset_id, workspace_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        v2 = self.ds_service.upload_dataset(file, dataset.name, workspace_id)
        
        v1 = None
        if v2.version_number > 1:
            from backend.persistence import models
            v1_orm = self.db.query(models.DatasetVersionORM).filter(
                models.DatasetVersionORM.dataset_id == dataset.id,
                models.DatasetVersionORM.version_number == v2.version_number - 1
            ).first()
            if v1_orm:
                v1 = self.ds_repo._to_domain_version(v1_orm)

        diff = None
        if v1:
            diff_engine = HistoricalDiffEngine()
            diff = diff_engine.compare(v1, v2)
            print("Diff computed:", diff.summary)
        else:
            print("V1 not found! v2 version is", v2.version_number, "dataset versions:", [v.version_number for v in dataset.versions])


        findings = []
        if diff:
            if diff.column_changes:
                for change in diff.column_changes:
                    if change.change_type == "null_rate_shift" and change.absolute_delta > 0.05:
                        findings.append(Finding(
                            title=f"Spike in null rate on {change.column}",
                            description=f"Null rate increased by {change.absolute_delta*100:.1f}% (now {change.current_value*100:.1f}%)",
                            category=FindingCategory.COMPLETENESS,
                            severity=Severity.HIGH,
                            confidence=0.9,
                            impact_score=0.8,
                            column=change.column,
                            rule="NullRateShiftRule",
                            observations=[],
                            evidence=[]
                        ))
                    elif change.change_type == "cardinality_shift" and change.absolute_delta < -0.05:
                        findings.append(Finding(
                            title=f"Uniqueness degradation on {change.column}",
                            description=f"Unique fraction dropped by {-change.absolute_delta*100:.1f}% (now {change.current_value*100:.1f}%)",
                            category=FindingCategory.UNIQUENESS,
                            severity=Severity.HIGH,
                            confidence=0.9,
                            impact_score=0.8,
                            column=change.column,
                            rule="UniquenessDropRule",
                            observations=[],
                            evidence=[]
                        ))
                    elif change.change_type == "distribution_shift" and abs(change.relative_delta) > 0.1:
                        findings.append(Finding(
                            title=f"Data drift on {change.column}",
                            description=f"Mean shifted by {change.relative_delta*100:.1f}% (from {change.previous_value:.2f} to {change.current_value:.2f})",
                            category=FindingCategory.DISTRIBUTION,
                            severity=Severity.MEDIUM,
                            confidence=0.8,
                            impact_score=0.5,
                            column=change.column,
                            rule="DistributionShiftRule",
                            observations=[],
                            evidence=[]
                        ))
            if diff.schema_changes:
                for sch in diff.schema_changes:
                    if sch.change_type == "type_changed":
                        findings.append(Finding(
                            title=f"Schema drift: {sch.column} type changed",
                            description=f"Column {sch.column} type changed from {sch.previous_type} to {sch.current_type}",
                            category=FindingCategory.SCHEMA,
                            severity=Severity.CRITICAL,
                            confidence=1.0,
                            impact_score=0.9,
                            column=sch.column,
                            rule="SchemaDriftRule",
                            observations=[],
                            evidence=[]
                        ))
                    elif sch.change_type == "removed":
                        findings.append(Finding(
                            title=f"Schema drift: {sch.column} removed",
                            description=f"Column {sch.column} was removed",
                            category=FindingCategory.SCHEMA,
                            severity=Severity.HIGH,
                            confidence=1.0,
                            impact_score=0.8,
                            column=sch.column,
                            rule="SchemaDropRule",
                            observations=[],
                            evidence=[]
                        ))
                    elif sch.change_type == "added":
                        findings.append(Finding(
                            title=f"Schema change: {sch.column} added",
                            description=f"New column {sch.column} of type {sch.current_type} was added",
                            category=FindingCategory.SCHEMA,
                            severity=Severity.LOW,
                            confidence=1.0,
                            impact_score=0.2,
                            column=sch.column,
                            rule="SchemaAddRule",
                            observations=[],
                            evidence=[]
                        ))

        print("FINDINGS:", len(findings), [f.title for f in findings])
        if not findings:
            return v2

        # 1. Initialize Investigation early so we can build the timeline correctly
        from core.investigation.timeline import InvestigationEvent, EventType, EventSource
        
        inv = Investigation(
            title=f"Automated Investigation: {dataset.name} v{v2.version_number}",
            description=f"System detected {len(findings)} anomalies in the latest dataset version.",
            dataset_version=v2.id,
            status=InvestigationStatus.OPEN
        )
        
        # 2. Log Dataset upload
        if v1:
            inv.timeline.append(InvestigationEvent(
                event_type=EventType.DATASET_VERSION_CREATED,
                source=EventSource.SYSTEM,
                entity_id=v2.id,
                description=f"Dataset version {v2.version_number} created.",
                metadata={"previous_version": v1.id}
            ))

        # 3. Log Diff
        if diff:
            inv.timeline.append(InvestigationEvent(
                event_type=EventType.HISTORICAL_CHANGE_DISCOVERED,
                source=EventSource.SYSTEM,
                entity_id=v2.id,
                description=f"Historical diff calculated (v{v1.version_number} -> v{v2.version_number}). Found {len(diff.schema_changes)} schema changes, {len(diff.column_changes)} column shifts.",
                metadata={"schema_changes": len(diff.schema_changes), "column_changes": len(diff.column_changes)}
            ))

        # 4. Process Findings & Attributions
        attr_engine = AttributionEngine()

        for finding in findings:
            inv.add_finding(finding) # This logs FINDING_DETECTED
            
            q_ev = Evidence(
                type=EvidenceType.METRIC,
                source="DataQualityEngine",
                dataset_version=v2.id,
                metric="null_fraction",
                value=finding.description,
                description="Anomaly detected by baseline rules"
            )
            finding.evidence.append(q_ev)
            inv.timeline.append(InvestigationEvent(
                event_type=EventType.EVIDENCE_COLLECTED,
                source=EventSource.SYSTEM,
                entity_id=q_ev.id,
                description=f"Evidence generated: {q_ev.description}"
            ))

            if diff:
                finding_attrs = attr_engine.evaluate(finding, diff)
                
                for attr in finding_attrs:
                    attr_ev = Evidence(
                        type=EvidenceType.HISTORY,
                        source="HistoricalDiffEngine",
                        dataset_version=v2.id,
                        metric="attribution_match",
                        value=attr.relevance_score.name,
                        description=f"Attribution match: {attr.reason}"
                    )
                    finding.evidence.append(attr_ev)
                    inv.timeline.append(InvestigationEvent(
                        event_type=EventType.ATTRIBUTION_GENERATED,
                        source=EventSource.SYSTEM,
                        entity_id=attr.id,
                        description=f"Attribution completed: {attr.reason} -> {attr.relevance_score.name}",
                        metadata={"relevance": attr.relevance_score.name}
                    ))
                    
                    # This logs HYPOTHESIS_CREATED
                    inv.add_hypothesis(
                        description=f"System generated hypothesis based on historical change: {attr.reason}",
                        finding_id=finding.id,
                        attribution_id=attr.id
                    )

        self.inv_repo.create(inv, [])
        return v2