from core.findings.models import Finding, FindingCategory, Severity
from core.investigation.recommender import InvestigationRecommender, ActionPriority

def test_recommender_uniqueness():
    finding = Finding(
        title="customer_id uniqueness violation",
        description="Duplicates",
        category=FindingCategory.UNIQUENESS,
        severity=Severity.HIGH,
        confidence=0.99,
        impact_score=0.85,
        column="customer_id",
        rule="UniqueRule"
    )
    
    actions = InvestigationRecommender.recommend(finding)
    
    assert len(actions) == 3
    
    # Verify expected actions are returned in the correct order
    assert actions[0].target == "created_at"
    assert actions[0].priority == ActionPriority.P1
    
    assert actions[1].target == "ingestion_batch_id"
    assert actions[1].priority == ActionPriority.P2
    
    assert actions[2].target == "source_file"
    assert actions[2].priority == ActionPriority.P3
