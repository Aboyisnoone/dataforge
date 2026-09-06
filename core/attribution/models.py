from dataclasses import dataclass, field
from typing import Union, Any
from enum import Enum
from core.diff import SchemaChange, ColumnChange

class Relevance(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"
    
    @property
    def score(self) -> int:
        return {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}[self.value]

@dataclass
class Attribution:
    finding_id: str
    change: Union[SchemaChange, ColumnChange]
    relevance_score: Relevance
    confidence: float
    reason: str
    id: str = field(default_factory=lambda: f"attr_{__import__('uuid').uuid4().hex[:8]}")
