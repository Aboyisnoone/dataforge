from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Any
import uuid

class HypothesisStatus(Enum):
    PROPOSED = "PROPOSED"
    SUPPORTED = "SUPPORTED"
    REJECTED = "REJECTED"

@dataclass
class ValidationResult:
    status: HypothesisStatus
    description: str
    evidence: List[Any] = field(default_factory=list)

@dataclass
class Hypothesis:
    investigation_id: str
    description: str
    finding_id: Optional[str] = None
    attribution_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    validation_result: Optional[ValidationResult] = None
    id: str = field(default_factory=lambda: f"hyp_{uuid.uuid4().hex[:8]}")

    def validate(self, result: ValidationResult):
        if self.status != HypothesisStatus.PROPOSED:
            raise ValueError(f"Cannot validate hypothesis that is already {self.status.value}")
            
        if result.status == HypothesisStatus.PROPOSED:
            raise ValueError("Validation result cannot have status PROPOSED")
            
        self.status = result.status
        self.validation_result = result
