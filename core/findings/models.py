from dataclasses import dataclass, field
from typing import Any, List, Optional
import uuid
from enum import Enum

@dataclass
class Observation:
    """
    An Observation is a raw fact or measurement about the data.
    It does not contain interpretation, severity, or judgment.
    """
    metric: str
    value: Any
    column: str
    dataset_version: str
    description: str
    id: str = field(default_factory=lambda: f"obs_{uuid.uuid4().hex[:8]}")

class FindingCategory(str, Enum):
    COMPLETENESS = "COMPLETENESS"
    UNIQUENESS = "UNIQUENESS"
    VALIDITY = "VALIDITY"
    CONSISTENCY = "CONSISTENCY"
    DISTRIBUTION = "DISTRIBUTION"
    SCHEMA = "SCHEMA"
    FRESHNESS = "FRESHNESS"
    PII = "PII"
    REFERENTIAL_INTEGRITY = "REFERENTIAL_INTEGRITY"
    VOLUME = "VOLUME"
    UNKNOWN = "UNKNOWN"

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

from core.evidence.models import Evidence

@dataclass
class Finding:
    """
    A Finding is an interpretation of one or more Observations.
    It provides a product-level understanding of what went wrong, including severity and impact.
    """
    title: str
    description: str
    category: FindingCategory
    severity: Severity
    confidence: float
    impact_score: float
    column: Optional[str]
    rule: Optional[str]
    observations: List[Observation] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    id: str = field(default_factory=lambda: f"fnd_{uuid.uuid4().hex[:8]}")
    
    def add_evidence(self, ev: Evidence) -> None:
        self.evidence.append(ev)

