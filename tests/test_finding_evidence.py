from core.findings.models import Finding, FindingCategory, Severity
from core.evidence.models import Evidence, EvidenceType

def test_finding_evidence():
    # 1. Create a Finding (can start with zero evidence)
    finding = Finding(
        title="customer_id uniqueness violation",
        description="Duplicates found",
        category=FindingCategory.UNIQUENESS,
        severity=Severity.HIGH,
        confidence=0.99,
        impact_score=0.85,
        column="customer_id",
        rule="UniqueRule",
        observations=[] # Omit observations for this test focus
    )
    
    assert len(finding.evidence) == 0
    
    # 2. Create evidence items
    ev1 = Evidence(
        type=EvidenceType.METRIC,
        source="UniqueRule",
        dataset_version="v_100",
        metric="duplicate_fraction",
        value=0.041,
        description="4.1% of rows are duplicated"
    )
    
    ev2 = Evidence(
        type=EvidenceType.SAMPLE,
        source="DuplicateSampler",
        dataset_version="v_100",
        metric="duplicate_record_sample",
        value=[{"id": 101, "name": "Alice"}, {"id": 101, "name": "Alice"}],
        description="Sample showing duplicate record"
    )
    
    # 3. Add evidence
    finding.add_evidence(ev1)
    finding.add_evidence(ev2)
    
    # Assert multiple pieces are attached
    assert len(finding.evidence) == 2
    
    # Verify Evidence retains original dataset_version and source
    assert finding.evidence[0].dataset_version == "v_100"
    assert finding.evidence[1].source == "DuplicateSampler"
    
    # Verify Finding severity/impact remains independent of Evidence addition
    assert finding.severity == Severity.HIGH
    assert finding.impact_score == 0.85
