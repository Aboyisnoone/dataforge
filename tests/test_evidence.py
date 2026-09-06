from core.evidence.models import Evidence, EvidenceType

def test_evidence_model():
    ev = Evidence(
        type=EvidenceType.METRIC,
        source="UniqueRule",
        dataset_version="v_100",
        metric="duplicate_fraction",
        value=0.041,
        description="4.1% of rows belong to duplicate customer IDs"
    )
    
    assert ev.type == EvidenceType.METRIC
    assert ev.source == "UniqueRule"
    assert ev.dataset_version == "v_100"
    assert ev.metric == "duplicate_fraction"
    assert ev.value == 0.041
    
    # Verify it does not contain severity or impact logic
    assert not hasattr(ev, "severity")
    assert not hasattr(ev, "impact")
    assert not hasattr(ev, "status")
