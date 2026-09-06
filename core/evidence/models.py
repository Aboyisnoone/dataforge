from dataclasses import dataclass, field
from typing import Any
from enum import Enum
import uuid

class EvidenceType(str, Enum):
    METRIC = "METRIC"
    QUERY = "QUERY"
    SAMPLE = "SAMPLE"
    COMPARISON = "COMPARISON"
    SCHEMA = "SCHEMA"
    HISTORY = "HISTORY"
    UNKNOWN = "UNKNOWN"

@dataclass
class Evidence:
    """
    Evidence provides traceable supporting material for a Finding.
    It answers 'Where did this information come from?' 
    and 'What was the specific measurement?'
    """
    type: EvidenceType
    source: str
    dataset_version: str
    metric: str
    value: Any
    description: str
    id: str = field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
