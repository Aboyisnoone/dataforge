import pytest
from datetime import datetime
from core.investigation.models import Investigation, InvestigationStatus, Resolution, InvalidTransitionError

def test_investigation_transitions():
    inv = Investigation(
        title="Test Inv",
        description="Testing transitions",
        dataset_version="v_1"
    )
    
    assert inv.status == InvestigationStatus.OPEN
    
    # Invalid transition (OPEN -> RESOLVED directly)
    with pytest.raises(InvalidTransitionError):
        inv.transition_to(InvestigationStatus.RESOLVED, resolution=Resolution("cause", "type", datetime.now(), "valid"))
        
    # Valid transition (OPEN -> INVESTIGATING)
    inv.transition_to(InvestigationStatus.INVESTIGATING)
    assert inv.status == InvestigationStatus.INVESTIGATING
    
    # Missing resolution data
    with pytest.raises(ValueError):
        inv.transition_to(InvestigationStatus.RESOLVED)
        
    # Valid transition (INVESTIGATING -> RESOLVED)
    inv.transition_to(InvestigationStatus.RESOLVED, resolution=Resolution("root", "fix", datetime.now(), "tested"))
    assert inv.status == InvestigationStatus.RESOLVED
