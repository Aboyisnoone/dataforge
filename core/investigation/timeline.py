from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List
import uuid

class EventType(str, Enum):
    DATASET_VERSION_CREATED = "DATASET_VERSION_CREATED"
    FINDING_DETECTED = "FINDING_DETECTED"
    HISTORICAL_CHANGE_DISCOVERED = "HISTORICAL_CHANGE_DISCOVERED"
    ATTRIBUTION_GENERATED = "ATTRIBUTION_GENERATED"
    HYPOTHESIS_CREATED = "HYPOTHESIS_CREATED"
    HYPOTHESIS_VALIDATED = "HYPOTHESIS_VALIDATED"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    STATUS_CHANGED = "STATUS_CHANGED"
    RESOLUTION_CREATED = "RESOLUTION_CREATED"

class EventSource(str, Enum):
    SYSTEM = "SYSTEM"
    ENGINEER = "ENGINEER"

@dataclass
class InvestigationEvent:
    event_type: EventType
    source: EventSource
    entity_id: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_number: int = 0
    id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")

@dataclass
class InvestigationTimeline:
    investigation_id: str
    events: List[InvestigationEvent] = field(default_factory=list)
    _current_sequence: int = 0

    def append(self, event: InvestigationEvent):
        self._current_sequence += 1
        event.sequence_number = self._current_sequence
        self.events.append(event)
        
    def get_chronological_events(self) -> List[InvestigationEvent]:
        # Sort by timestamp first, then sequence number for deterministic ordering
        def safe_ts(e):
            if e.timestamp.tzinfo is None:
                from datetime import timezone
                return (e.timestamp.replace(tzinfo=timezone.utc), e.sequence_number)
            return (e.timestamp, e.sequence_number)
        return sorted(self.events, key=safe_ts)
