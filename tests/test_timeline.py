import pytest
from datetime import datetime, timezone
from backend.persistence.database import Base, engine, get_db
from backend.persistence.repositories.investigations import InvestigationRepository
from core.investigation.models import Investigation, InvestigationStatus, Resolution
from core.findings.models import Finding, FindingCategory, Severity
from core.investigation.timeline import EventType, EventSource

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.skip(reason="Outdated domain model")
def test_timeline_lifecycle(setup_db):
    # Setup
    db = next(get_db())
    repo = InvestigationRepository(db)
    
    # 1. Investigation created (adds STATUS_CHANGED event in __post_init__)
    inv = Investigation(
        title="Timeline Test",
        description="Testing the timeline",
        dataset_version="v_123"
    )
    
    # 2. Finding detected
    f = Finding(
        category=FindingCategory.UNIQUENESS,
        title="Duplicate customer_id",
        description="test",
        severity=Severity.HIGH,
        impact_score=0.9,
        confidence=0.9,
        column="customer_id",
        rule="UniqueRule"
    )
    inv.add_finding(f)
    
    # 3. Hypothesis created
    hyp = inv.add_hypothesis("A new ingestion batch duplicated rows", finding_id="dummy")
    
    # 4. Status changed
    inv.transition_to(InvestigationStatus.INVESTIGATING, finding_id="dummy_finding_id")
    
    # 5. Resolution
    res = Resolution(
        root_cause="Duplicate batch",
        resolution_type="Fix upstream",
        resolved_at=datetime.now(timezone.utc),
        validation_result="Cleaned"
    )
    inv.transition_to(InvestigationStatus.RESOLVED, resolution=res)
    
    # Persist
    repo.create(inv)
    
    # Retrieve
    retrieved_inv, _ = repo.get(inv.workspace_id, inv.id)
    
    # Verify timeline
    events = retrieved_inv.timeline.get_chronological_events()
    
    assert len(events) == 6
    
    # Check sequences and determinism
    for i, e in enumerate(events):
        assert e.sequence_number == i + 1
        
    assert events[0].event_type == EventType.STATUS_CHANGED
    assert events[0].metadata["status"] == InvestigationStatus.OPEN.value
    
    assert events[1].event_type == EventType.FINDING_DETECTED
    assert events[1].entity_id == f.id
    
    assert events[2].event_type == EventType.HYPOTHESIS_CREATED
    assert events[2].entity_id == hyp.id
    
    assert events[3].event_type == EventType.STATUS_CHANGED
    assert events[3].metadata["new_status"] == InvestigationStatus.INVESTIGATING.value
    
    assert events[4].event_type == EventType.STATUS_CHANGED
    assert events[4].metadata["new_status"] == InvestigationStatus.RESOLVED.value
    
    assert events[5].event_type == EventType.RESOLUTION_CREATED
    assert events[5].metadata["root_cause"] == "Duplicate batch"
    
@pytest.mark.skip(reason="Outdated domain model")
def test_timeline_identical_timestamps(setup_db):
    db = next(get_db())
    repo = InvestigationRepository(db)
    
    inv = Investigation("Test", "Test", "v_123")
    # Add multiple hypotheses rapidly, so they might share the same millisecond timestamp
    h1 = inv.add_hypothesis("First", finding_id="dummy")
    h2 = inv.add_hypothesis("Second", finding_id="dummy")
    h3 = inv.add_hypothesis("Third", finding_id="dummy")
    
    repo.create(inv, finding_id="dummy_finding_id")
    retrieved_inv, _ = repo.get(inv.workspace_id, inv.id)
    events = retrieved_inv.timeline.get_chronological_events()
    
    # The first event is creation
    assert len(events) == 4
    assert events[1].entity_id == h1.id
    assert events[1].sequence_number == 2
    
    assert events[2].entity_id == h2.id
    assert events[2].sequence_number == 3
    
    assert events[3].entity_id == h3.id
    assert events[3].sequence_number == 4
    
    # Even if we artificially force identical timestamps...
    now = datetime.now()
    events[1].timestamp = now
    events[2].timestamp = now
    events[3].timestamp = now
    
    # get_chronological_events uses (timestamp, sequence_number) sorting
    sorted_events = retrieved_inv.timeline.get_chronological_events()
    assert sorted_events[1].sequence_number == 2
    assert sorted_events[2].sequence_number == 3
    assert sorted_events[3].sequence_number == 4
    
@pytest.mark.skip(reason="Outdated domain model")
def test_timeline_append_only_updates(setup_db):
    db = next(get_db())
    repo = InvestigationRepository(db)
    
    inv = Investigation("Update Test", "Desc", "v_1")
    repo.create(inv)
    
    retrieved, _ = repo.get(inv.workspace_id, inv.id)
    
    # Add an event and update
    retrieved.add_hypothesis("A theory", finding_id="dummy")
    repo.update(retrieved, finding_id="dummy_finding_id")
    
    final_inv, _ = repo.get(inv.workspace_id, inv.id)
    assert len(final_inv.timeline.events) == 2
    assert final_inv.timeline.events[1].event_type == EventType.HYPOTHESIS_CREATED
    # Ensure no duplicates
    
    # Update without any changes
    repo.update(final_inv)
    final_final_inv, _ = repo.get(inv.workspace_id, inv.id)
    assert len(final_final_inv.timeline.events) == 2
