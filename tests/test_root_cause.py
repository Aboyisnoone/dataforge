import pytest
from core.attribution.root_cause import RootCauseEngine, CandidateStatus
from core.attribution.models import Attribution, Relevance
from core.diff import ColumnChange
from core.findings.models import Finding, FindingCategory, Severity
from core.investigation.hypothesis import Hypothesis, HypothesisStatus
from core.investigation.hypothesis import ValidationResult
from core.evidence.models import Evidence, EvidenceType

def create_finding(id="f1") -> Finding:
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
    f.id = id
    return f

@pytest.mark.skip(reason="Outdated domain model")
def test_root_cause_ranking():
    finding = create_finding()
    engine = RootCauseEngine()
    
    # 1. Strong attribution + Supported Hypothesis
    attr1 = Attribution(
        finding_id=finding.id,
        change=ColumnChange("customer_id", "unique_fraction", 1.0, 0.8, -0.2, -0.2, "cardinality_shift"),
        relevance_score=Relevance.HIGH,
        confidence=0.9,
        reason="Cardinality shift exactly matches uniqueness issue"
    )
    
    hyp1 = Hypothesis(
        investigation_id="inv1",
        finding_id=finding.id,
        attribution_id=attr1.id,
        description="Ingestion retry introduced duplicate records"
    )
    vr1 = ValidationResult(
        hypothesis_id=hyp1.id,
        status=HypothesisStatus.SUPPORTED,
        description="Duplicate fraction matches ingestion batch",
        evidence=[Evidence(EvidenceType.QUERY, "sys", "v2", "dup_groups", 10, "Found 10")]
    )
    hyp1.validate(vr1)
    
    # 2. Medium attribution + Proposed Hypothesis (Plausible)
    attr2 = Attribution(
        finding_id=finding.id,
        change=ColumnChange("customer_id", "null_fraction", 0.0, 0.1, 0.1, 1.0, "null_rate_shift"),
        relevance_score=Relevance.MEDIUM,
        confidence=0.6,
        reason="Null rate shift might explain uniqueness drop"
    )
    hyp2 = Hypothesis(
        investigation_id="inv1",
        finding_id=finding.id,
        attribution_id=attr2.id,
        description="Upstream join duplication"
    )
    
    # 3. Weak attribution + Rejected Hypothesis (Disqualified)
    attr3 = Attribution(
        finding_id=finding.id,
        change=ColumnChange("revenue", "mean", 10.0, 15.0, 5.0, 0.5, "distribution_shift"),
        relevance_score=Relevance.LOW,
        confidence=0.3,
        reason="Unrelated shift"
    )
    hyp3 = Hypothesis(
        investigation_id="inv1",
        finding_id=finding.id,
        attribution_id=attr3.id,
        description="Schema migration"
    )
    vr3 = ValidationResult(
        hypothesis_id=hyp3.id,
        status=HypothesisStatus.REJECTED,
        description="Schema is totally fine",
        evidence=[]
    )
    hyp3.validate(vr3)
    
    # Run engine
    candidates = engine.rank_candidates(finding, [attr1, attr2, attr3], [hyp1, hyp2, hyp3])
    
    assert len(candidates) == 3
    
    # Assert Order & Status
    # Rank 1: Strong / Supported
    assert candidates[0].hypothesis_id == hyp1.id
    assert candidates[0].status == CandidateStatus.STRONG
    assert candidates[0].score == 1.0  # 0.6 (HIGH) + 0.4 (SUPPORTED)
    assert candidates[0].confidence == 0.9
    assert len(candidates[0].supporting_evidence) == 1
    
    # Rank 2: Plausible / Proposed
    assert candidates[1].hypothesis_id == hyp2.id
    assert candidates[1].status == CandidateStatus.PLAUSIBLE
    assert candidates[1].score == 0.4  # 0.4 (MEDIUM) + 0.0
    
    # Rank 3: Disqualified / Rejected
    assert candidates[2].hypothesis_id == hyp3.id
    assert candidates[2].status == CandidateStatus.DISQUALIFIED
    assert candidates[2].score == 0.0  # 0.2 (LOW) - 0.8 clamped to 0
    assert "rejected" in candidates[2].explanation.lower()

def test_system_proposed_candidate():
    finding = create_finding()
    engine = RootCauseEngine()
    
    # Attribution without a hypothesis
    attr = Attribution(
        finding_id=finding.id,
        change=ColumnChange("customer_id", "unique_fraction", 1.0, 0.8, -0.2, -0.2, "cardinality_shift"),
        relevance_score=Relevance.HIGH,
        confidence=0.8,
        reason="Uniqueness dropped"
    )
    
    candidates = engine.rank_candidates(finding, [attr], [])
    
    assert len(candidates) == 1
    assert candidates[0].hypothesis_id is None
    assert candidates[0].attribution_id == attr.id
    assert candidates[0].status == CandidateStatus.PLAUSIBLE
    assert candidates[0].score == 0.6
    assert candidates[0].confidence == 0.8
