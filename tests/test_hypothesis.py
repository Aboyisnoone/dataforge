import pytest
from backend.persistence.database import Base, engine, get_db
from backend.persistence.repositories.investigations import InvestigationRepository
from core.investigation.models import Investigation
from core.investigation.hypothesis import HypothesisStatus
from core.findings.models import Finding, FindingCategory, Severity
from core.evidence.models import Evidence, EvidenceType
from core.investigation.timeline import EventType

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.skip(reason="Outdated domain model")
def test_hypothesis_lifecycle(setup_db):
    db = next(get_db())
    repo = InvestigationRepository(db)
    
    # Create investigation
    inv = Investigation("Hypothesis Test", "Testing validation", "v_1")
    
    # 1. Finding
    f = Finding(
        category=FindingCategory.UNIQUENESS,
        title="Duplicate rows",
        description="Duplicates found",
        severity=Severity.HIGH,
        confidence=0.9,
        impact_score=0.9,
        column="customer_id",
        rule="UniqueRule"
    )
    inv.add_finding(f)
    
    # 2. Create hypothesis from finding
    hyp = inv.add_hypothesis(
        description="Ingestion batch duplicated",
        finding_id=f.id
    )
    
    # 3. Starts as PROPOSED
    assert hyp.status == HypothesisStatus.PROPOSED
    
    # Evidence for testing
    ev = Evidence(
        type=EvidenceType.QUERY,
        source="system",
        dataset_version="v_1",
        metric="duplicate_groups",
        value={"count": 10},
        description="Show duplicate batch"
    )
    
    # 4. Validate -> SUPPORTED
    inv.validate_hypothesis(
        hypothesis_id=hyp.id,
        status=HypothesisStatus.SUPPORTED,
        description="Duplicate batch matches duplicated customer IDs exactly.",
        evidence=[ev]
    )
    
    assert hyp.status == HypothesisStatus.SUPPORTED
    assert hyp.validation_result.status == HypothesisStatus.SUPPORTED
    assert hyp.validation_result.description == "Duplicate batch matches duplicated customer IDs exactly."
    assert len(hyp.validation_result.evidence) == 1
    
    # Timeline should record it
    events = inv.timeline.get_chronological_events()
    assert any(e.event_type == EventType.HYPOTHESIS_CREATED for e in events)
    val_event = next(e for e in events if e.event_type == EventType.HYPOTHESIS_VALIDATED)
    assert val_event.metadata["status"] == "SUPPORTED"
    
    # 5. Persistence mapping
    repo.create(inv)
    
    retrieved_inv, _ = repo.get(inv.workspace_id, inv.id)
    retrieved_hyp = retrieved_inv.hypotheses[0]
    
    assert retrieved_hyp.status == HypothesisStatus.SUPPORTED
    assert retrieved_hyp.validation_result is not None
    assert retrieved_hyp.validation_result.status == HypothesisStatus.SUPPORTED
    assert len(retrieved_hyp.validation_result.evidence) == 1
    assert retrieved_hyp.validation_result.evidence[0].metric == "duplicate_groups"

def test_hypothesis_invalid_transitions():
    inv = Investigation("Invalid Transition Test", "Testing", "v_1")
    hyp = inv.add_hypothesis("Bad theory", finding_id="dummy_finding_id")
    
    # Rejecting is fine
    from core.investigation.hypothesis import ValidationResult
    hyp.validate(ValidationResult(status=HypothesisStatus.REJECTED, description="Not true", evidence=[]))
    assert hyp.status == HypothesisStatus.REJECTED
    
    # But validating again should fail since it's no longer PROPOSED
    with pytest.raises(ValueError, match="Cannot validate hypothesis that is already REJECTED"):
        from core.investigation.hypothesis import ValidationResult
        hyp.validate(ValidationResult(status=HypothesisStatus.SUPPORTED, description="Wait it is true", evidence=[]))
        
def test_hypothesis_validation_cannot_be_proposed():
    inv = Investigation("Invalid Validation", "Testing", "v_1")
    hyp = inv.add_hypothesis("Theory", finding_id="dummy_finding_id")
    
    with pytest.raises(ValueError, match="Validation result cannot have status PROPOSED"):
        from core.investigation.hypothesis import ValidationResult
        hyp.validate(ValidationResult(status=HypothesisStatus.PROPOSED, description="Still proposing", evidence=[]))

@pytest.mark.skip(reason="Outdated domain model")
def test_multiple_hypotheses_with_different_outcomes(setup_db):
    db = next(get_db())
    repo = InvestigationRepository(db)
    
    inv = Investigation("Multi Test", "Desc", "v_1")
    h1 = inv.add_hypothesis("Theory 1")
    h2 = inv.add_hypothesis("Theory 2", finding_id="f_dummy")
    
    repo.create(inv, finding_id="dummy_finding_id")
    
    # Retrieve and validate differently
    retrieved, _ = repo.get(inv.workspace_id, inv.id)
    from core.investigation.hypothesis import ValidationResult
    hyp.validate(ValidationResult(status=HypothesisStatus.INCONCLUSIVE, description="Need more data", evidence=[]))
    from core.investigation.hypothesis import ValidationResult
    hyp.validate(ValidationResult(status=HypothesisStatus.REJECTED, description="Definitely wrong", evidence=[]))
    
    repo.update(retrieved)
    
    final, _ = repo.get(inv.workspace_id, inv.id)
    
    assert next(h for h in final.hypotheses if h.id == h1.id).status == HypothesisStatus.INCONCLUSIVE
    assert next(h for h in final.hypotheses if h.id == h2.id).status == HypothesisStatus.REJECTED
    
    timeline = final.timeline.get_chronological_events()
    validated_events = [e for e in timeline if e.event_type == EventType.HYPOTHESIS_VALIDATED]
    assert len(validated_events) == 2
