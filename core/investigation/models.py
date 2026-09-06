import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from core.investigation.timeline import InvestigationTimeline, InvestigationEvent, EventType, EventSource
from core.findings.models import Finding
from core.investigation.hypothesis import Hypothesis, HypothesisStatus, ValidationResult
from core.investigation.experiment import Experiment

class InvestigationStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"

@dataclass
class Resolution:
    root_cause: str
    resolution_type: str = "FIXED"
    resolved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validation_result: Optional[str] = None

class InvalidTransitionError(Exception):
    pass

@dataclass
class Investigation:
    dataset_version: str
    workspace_id: str = "ws_local_dev"
    title: str = "Untitled Investigation"
    description: str = ""
    findings: List[Finding] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    experiments: List[Experiment] = field(default_factory=list)
    status: InvestigationStatus = InvestigationStatus.OPEN
    resolution: Optional[Resolution] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:8]}")
    timeline: InvestigationTimeline = field(init=False)

    def __post_init__(self):
        self.timeline = InvestigationTimeline(investigation_id=self.id)
        if not self.timeline.events:
            self.timeline.append(InvestigationEvent(
                event_type=EventType.STATUS_CHANGED,
                source=EventSource.SYSTEM,
                entity_id=self.id,
                description=f"Investigation created with status {self.status.value}",
                metadata={"status": self.status.value}
            ))

    def transition_to(self, new_status: InvestigationStatus, resolution: Optional[Resolution] = None):
        valid_transitions = {
            InvestigationStatus.OPEN: [InvestigationStatus.INVESTIGATING, InvestigationStatus.REJECTED],
            InvestigationStatus.INVESTIGATING: [InvestigationStatus.RESOLVED, InvestigationStatus.REJECTED],
            InvestigationStatus.RESOLVED: [],
            InvestigationStatus.REJECTED: []
        }
        
        if new_status not in valid_transitions.get(self.status, []):
            raise InvalidTransitionError(f"Cannot transition from {self.status.value} to {new_status.value}")
            
        if new_status == InvestigationStatus.RESOLVED and not resolution:
            raise ValueError("Resolution metadata is required when resolving an investigation.")
            
        self.status = new_status
        
        self.timeline.append(InvestigationEvent(
            event_type=EventType.STATUS_CHANGED,
            source=EventSource.ENGINEER,
            entity_id=self.id,
            description=f"Status changed to {self.status.value}",
            metadata={"status": self.status.value}
        ))
        
        if resolution:
            self.resolution = resolution
            self.timeline.append(InvestigationEvent(
                event_type=EventType.RESOLUTION_CREATED,
                source=EventSource.ENGINEER,
                entity_id=self.id,
                description=f"Investigation resolved: {resolution.root_cause}",
                metadata={"resolution_type": resolution.resolution_type}
            ))

    def add_finding(self, finding: Finding):
        self.findings.append(finding)
        self.timeline.append(InvestigationEvent(
            event_type=EventType.FINDING_DETECTED,
            source=EventSource.SYSTEM,
            entity_id=finding.id,
            description=f"Finding detected: {finding.title}",
            metadata={"severity": finding.severity.value, "category": finding.category.value}
        ))

    def add_hypothesis(self, description: str, finding_id: str, attribution_id: Optional[str] = None) -> Hypothesis:
        h = Hypothesis(
            investigation_id=self.id,
            finding_id=finding_id,
            attribution_id=attribution_id,
            description=description
        )
        self.hypotheses.append(h)
        self.timeline.append(InvestigationEvent(
            event_type=EventType.HYPOTHESIS_CREATED,
            source=EventSource.SYSTEM,
            entity_id=h.id,
            description=f"Hypothesis created: {description}"
        ))
        return h
