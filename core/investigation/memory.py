import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from core.investigation.models import Investigation, InvestigationStatus

logger = logging.getLogger(__name__)

@dataclass
class MemoryRetrieval:
    investigation_id: str
    title: str
    dataset_name: str
    similarity_score: float
    matched_factors: List[str]
    resolution_root_cause: Optional[str]
    resolved_at: Optional[datetime]
    url: Optional[str] = None

class MemoryEngine:
    def __init__(self, all_investigations: List[Investigation], get_dataset_func):
        self.all_investigations = all_investigations
        self.get_dataset_func = get_dataset_func # function to fetch dataset info by version ID

    def retrieve_similar(self, current_inv: Investigation, limit: int = 3) -> List[MemoryRetrieval]:
        # Only look at resolved past investigations
        resolved = [inv for inv in self.all_investigations if inv.status == InvestigationStatus.RESOLVED and inv.id != current_inv.id]
        
        current_ds = self.get_dataset_func(current_inv.dataset_version)
        current_ds_name = current_ds.name if current_ds else ""
        
        current_metrics = set(ev.metric for f in current_inv.findings for ev in f.evidence if ev.metric)
        current_cols = set(f.column_name for f in current_inv.findings if hasattr(f, 'column_name') and f.column_name)

        results = []
        for past_inv in resolved:
            score = 0.0
            factors = []
            
            past_ds = self.get_dataset_func(past_inv.dataset_version)
            past_ds_name = past_ds.name if past_ds else ""
            
            # 1. Dataset similarity
            if current_ds_name and past_ds_name and current_ds_name.lower() == past_ds_name.lower():
                score += 0.5
                factors.append(f"Same dataset ({current_ds_name})")
                
            # 2. Finding metric overlap
            past_metrics = set(ev.metric for f in past_inv.findings for ev in f.evidence if ev.metric)
            metric_overlap = current_metrics.intersection(past_metrics)
            if metric_overlap:
                score += 0.3 * len(metric_overlap)
                factors.append(f"Similar metrics: {', '.join(metric_overlap)}")
                
            # 3. Column overlap
            past_cols = set(f.column_name for f in past_inv.findings if hasattr(f, 'column_name') and f.column_name)
            col_overlap = current_cols.intersection(past_cols)
            if col_overlap:
                score += 0.3 * len(col_overlap)
                factors.append(f"Affected columns: {', '.join(col_overlap)}")
                
            if score > 0:
                results.append(
                    MemoryRetrieval(
                        investigation_id=past_inv.id,
                        title=past_inv.title,
                        dataset_name=past_ds_name,
                        similarity_score=min(1.0, score),
                        matched_factors=factors,
                        resolution_root_cause=past_inv.resolution.root_cause if past_inv.resolution else None,
                        resolved_at=past_inv.resolution.resolved_at if past_inv.resolution else None
                    )
                )
                
        # Sort by score descending
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
