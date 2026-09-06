from core.findings.models import Observation, Finding, FindingCategory, Severity

def test_finding_model():
    # 1. Create observations (Facts)
    obs_dup = Observation(
        metric="duplicate_fraction",
        value=0.041,
        column="customer_id",
        dataset_version="v_100",
        description="4.1% of rows belong to duplicate identifier groups"
    )
    
    obs_count = Observation(
        metric="duplicate_groups",
        value=12481,
        column="customer_id",
        dataset_version="v_100",
        description="12,481 distinct duplicate groups found"
    )
    
    # 2. Create finding (Interpretation)
    finding = Finding(
        title="customer_id uniqueness violation",
        description="The primary identifier customer_id contains duplicates.",
        category=FindingCategory.UNIQUENESS,
        severity=Severity.HIGH,
        confidence=0.99,
        impact_score=85.5, # We'll calculate this properly later
        column="customer_id",
        rule="UniqueRule",
        observations=[obs_dup, obs_count]
    )
    
    # Assertions
    # A Finding can contain severity/confidence/impact
    assert finding.severity == Severity.HIGH
    assert finding.confidence == 0.99
    assert finding.impact_score == 85.5
    
    # A finding can reference multiple observations
    assert len(finding.observations) == 2
    
    # An Observation can be attached to a Finding
    assert finding.observations[0].metric == "duplicate_fraction"
    
    # The original Observation remains unchanged (and lacks interpretation fields)
    assert not hasattr(obs_dup, "severity")
    assert obs_dup.value == 0.041
