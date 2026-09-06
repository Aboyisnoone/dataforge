from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid

class ExperimentStatus(Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class ExperimentResult:
    row_count: int
    columns: List[str]
    sample_rows: List[Dict[str, Any]]
    execution_time_ms: float
    error_message: Optional[str] = None

@dataclass
class Experiment:
    hypothesis_id: str
    sql_query: str
    requested_by: str
    id: str = field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:8]}")
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[ExperimentResult] = None
