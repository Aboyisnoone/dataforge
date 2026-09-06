import os
os.environ["GEMINI_API_KEY"] = "dummy_key"

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.api.main import app
from backend.copilot.models import CopilotResponse, CopilotClaim, CopilotCitation
from core.investigation.models import Investigation, InvestigationStatus
from core.dataset.models import DatasetVersion, Profile
from core.findings.models import Finding, FindingCategory, Severity
from datetime import datetime, timezone

client = TestClient(app)

@pytest.fixture
def mock_investigation_data():
    # Mock repositories
    patcher_inv = patch("backend.copilot.service.InvestigationRepository")
    patcher_ds = patch("backend.copilot.service.DatasetRepository")
    mock_inv_repo = patcher_inv.start()
    mock_ds_repo = patcher_ds.start()
    
    inv = Investigation("Test", "Desc", "v_1")
    inv.id = "inv_123"
    
    f = Finding(
        category=FindingCategory.UNIQUENESS,
        title="Dupe",
        description="Dupe rows",
        severity=Severity.HIGH,
        confidence=1.0,
        impact_score=1.0,
        column="c1",
        rule="Unique"
    )
    inv.add_finding(f)
    
    dv = DatasetVersion(
        id="v_1",
        dataset_id="ds_1",
        version_number=1,
        file_hash="hash",
        file_size=10,
        storage_path="path",
        format="csv",
        schema={"c1": "INTEGER"},
        row_count=100,
        created_at=datetime.now(timezone.utc),
        stats={"row_count": 100}
    )
    
    mock_inv_repo.return_value.get.return_value = (inv, [])
    mock_ds_repo.return_value.get_version.return_value = dv
    mock_ds_repo.return_value.get.return_value = None # No previous version needed for mock
    
    yield inv, mock_inv_repo, mock_ds_repo
    
    patcher_inv.stop()
    patcher_ds.stop()

@pytest.mark.skip(reason="Outdated domain model")
def test_ask_copilot_success(mock_investigation_data):
    inv, _, _ = mock_investigation_data
    
    # Mock the LLM Provider generate method
    mock_response = CopilotResponse(
        answer="I have checked the investigation.",
        claims=[],
        hypotheses=[],
        experiments=[],
        citations=[]
    )
    
    with patch("backend.copilot.providers.gemini.GeminiProvider.generate") as mock_provider:
        mock_provider.return_value = mock_response
        
        resp = client.post(f"/investigations/{inv.id}/copilot", json={"query": "What happened?"})
        
        if resp.status_code != 200:
            print("Response:", resp.json())
            
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "I have checked the investigation."
        assert mock_provider.called

@pytest.mark.skip(reason="Outdated domain model")
def test_ask_copilot_not_found(mock_investigation_data):
    inv, mock_inv_repo, _ = mock_investigation_data
    
    # Force not found
    mock_inv_repo.return_value.get.return_value = (None, None)
    
    resp = client.post("/investigations/missing_123/copilot", json={"query": "Hello"})
    
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

@pytest.mark.skip(reason="Outdated domain model")
def test_ask_copilot_llm_failure(mock_investigation_data):
    inv, _, _ = mock_investigation_data
    
    with patch("backend.copilot.providers.gemini.GeminiProvider.generate") as mock_provider:
        mock_provider.side_effect = RuntimeError("API Outage")
        
        resp = client.post(f"/investigations/{inv.id}/copilot", json={"query": "What happened?"})
        
        # API should shield 500s safely
        assert resp.status_code == 500
        assert resp.json()["detail"] == "Copilot failed to generate a response."

