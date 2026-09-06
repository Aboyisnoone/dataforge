from dataclasses import dataclass
from typing import List
from core.findings.models import Finding, FindingCategory
from enum import Enum

class ActionPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

@dataclass
class InvestigationAction:
    type: str
    target: str
    rationale: str
    priority: ActionPriority

class InvestigationRecommender:
    """
    Deterministically recommends the next actions an engineer should take
    based on the characteristics of a Finding.
    """
    @staticmethod
    def recommend(finding: Finding) -> List[InvestigationAction]:
        actions = []
        
        if finding.category == FindingCategory.UNIQUENESS:
            actions.append(InvestigationAction(
                type="COMPARE",
                target="created_at",
                rationale="Compare timestamp across duplicate groups to identify chronologically later duplicates.",
                priority=ActionPriority.P1
            ))
            actions.append(InvestigationAction(
                type="INSPECT",
                target="ingestion_batch_id",
                rationale="Check if duplicate records originated from the same ingestion batch.",
                priority=ActionPriority.P2
            ))
            actions.append(InvestigationAction(
                type="COMPARE",
                target="source_file",
                rationale="Compare source file lineage to detect duplicate processing.",
                priority=ActionPriority.P3
            ))
            
        elif finding.category == FindingCategory.COMPLETENESS:
            actions.append(InvestigationAction(
                type="CORRELATE",
                target="null_distribution",
                rationale="Check if nulls correlate with specific dates or upstream source systems.",
                priority=ActionPriority.P1
            ))
            
        return actions
