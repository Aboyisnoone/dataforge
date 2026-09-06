from core.findings.models import Observation

def test_observation_model():
    # 1. Customer ID Observation
    obs_id = Observation(
        metric="duplicate_fraction",
        value=0.041,
        column="customer_id",
        dataset_version="v_100",
        description="4.1% of rows belong to duplicate identifier groups"
    )
    
    assert obs_id.metric == "duplicate_fraction"
    assert obs_id.value == 0.041
    assert obs_id.column == "customer_id"
    assert obs_id.dataset_version == "v_100"
    
    # Prove that it does not contain severity or interpretation
    assert not hasattr(obs_id, "severity")
    assert not hasattr(obs_id, "status")
    
    # 2. Revenue Observation
    obs_rev = Observation(
        metric="null_fraction",
        value=0.02,
        column="revenue",
        dataset_version="v_100",
        description="2.0% of rows are null"
    )
    
    assert obs_rev.metric == "null_fraction"
    assert obs_rev.value == 0.02
    assert obs_rev.column == "revenue"
    assert not hasattr(obs_rev, "severity")
