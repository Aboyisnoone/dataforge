import pytest
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.persistence.database import Base
from backend.persistence.models import *
from backend.persistence.repositories.investigations import InvestigationRepository

from core.investigation.models import Investigation, InvestigationStatus, Resolution
from core.findings.models import Finding, FindingCategory, Severity, Observation
from core.evidence.models import Evidence, EvidenceType
from core.investigation.recommender import InvestigationAction, ActionPriority

# Use a purely in-memory SQLite DB for tests
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()
    yield db_session
    db_session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.mark.skip(reason="Outdated domain model")
def test_persistence_workflow(db):
    repo = InvestigationRepository(db)
    
    # 1. Create a complete investigation graph
    inv = Investigation(
        title="Test Investigation",
        description="Testing persistence",
        dataset_version="v_test",
        status=InvestigationStatus.OPEN
    )
    
    obs = Observation(
        metric="duplicate_count",
        value=5,
        column="user_id",
        dataset_version="v_test",
        description="Found 5 duplicates"
    )
    
    ev = Evidence(
        type=EvidenceType.QUERY,
        source="UniqueRule",
        dataset_version="v_test",
        metric="exec_query",
        value="SELECT * FROM table",
        description="Query used"
    )
    
    finding = Finding(
        title="user_id uniqueness violation",
        description="Duplicates found",
        category=FindingCategory.UNIQUENESS,
        severity=Severity.HIGH,
        confidence=0.95,
        impact_score=0.8,
        column="user_id",
        rule="UniqueRule",
        observations=[obs],
        evidence=[ev]
    )
    inv.findings.append(finding)
    
    rec = InvestigationAction(
        type="COMPARE",
        target="created_at",
        rationale="Check dates",
        priority=ActionPriority.P1
    )
    
    # Persist it
    repo.create(inv, recommendations=[rec])
    
    # 2. Retrieve it in a new repository (simulate new request)
    db.expunge_all() # Ensure we hit the DB, not cache
    
    new_repo = InvestigationRepository(db)
    retrieved_inv, retrieved_recs = new_repo.get(inv.workspace_id, inv.id)
    
    assert retrieved_inv is not None
    assert retrieved_inv.title == "Test Investigation"
    assert retrieved_inv.status == InvestigationStatus.OPEN
    
    assert len(retrieved_inv.findings) == 1
    f = retrieved_inv.findings[0]
    assert f.title == "user_id uniqueness violation"
    assert f.severity == Severity.HIGH
    
    assert len(f.observations) == 1
    assert f.observations[0].metric == "duplicate_count"
    
    assert len(f.evidence) == 1
    assert f.evidence[0].type == EvidenceType.QUERY
    
    assert len(retrieved_recs) == 1
    assert retrieved_recs[0].type == "COMPARE"
    
    # 3. Update status and confirm survival
    retrieved_inv.transition_to(InvestigationStatus.INVESTIGATING)
    new_repo.update(retrieved_inv)
    
    db.expunge_all()
    
    third_repo = InvestigationRepository(db)
    updated_inv, _ = third_repo.get(inv.workspace_id, inv.id)
    assert updated_inv.status == InvestigationStatus.INVESTIGATING
