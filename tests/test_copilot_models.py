import pytest
from backend.copilot.models import (
    CopilotResponse,
    CopilotClaim,
    CopilotCitation,
    CopilotHypothesisDraft,
    CopilotExperimentDraft,
)
from pydantic import ValidationError

def test_copilot_response_valid_contract():
    payload = {
        "answer": "Based on the evidence, the ingestion pipeline introduced duplicates.",
        "claims": [
            {
                "text": "Duplicates jumped by 4.1%",
                "citation_ids": ["c1"]
            }
        ],
        "hypotheses": [
            {
                "description": "Ingestion retry introduced duplicate records",
                "rationale": "The batch timestamp aligns with the degradation.",
                "attribution_id": "attr_123"
            }
        ],
        "experiments": [
            {
                "description": "Verify exact duplicates across batch IDs",
                "sql_query": "SELECT batch_id, count(*) FROM table GROUP BY batch_id HAVING count(*) > 1;",
                "expected_outcome": "We should see a specific batch_id accounting for all new duplicates.",
                "hypothesis_index": 0
            }
        ],
        "citations": [
            {
                "id": "c1",
                "source_type": "Evidence",
                "reference_id": "ev_abc",
                "context": "Evidence showing 4.1% duplicate increase."
            }
        ]
    }
    
    response = CopilotResponse.model_validate(payload)
    
    assert response.answer == "Based on the evidence, the ingestion pipeline introduced duplicates."
    assert len(response.claims) == 1
    assert response.claims[0].text == "Duplicates jumped by 4.1%"
    assert response.claims[0].citation_ids == ["c1"]
    
    assert len(response.hypotheses) == 1
    assert response.hypotheses[0].attribution_id == "attr_123"
    
    assert len(response.experiments) == 1
    assert response.experiments[0].sql_query.startswith("SELECT")
    assert response.experiments[0].hypothesis_index == 0
    
    assert len(response.citations) == 1
    assert response.citations[0].source_type == "Evidence"
    assert response.citations[0].reference_id == "ev_abc"

def test_copilot_response_minimal_contract():
    payload = {
        "answer": "I don't have enough information to form a hypothesis."
    }
    
    # Optional arrays should default to empty lists
    response = CopilotResponse.model_validate(payload)
    
    assert response.answer == payload["answer"]
    assert response.claims == []
    assert response.hypotheses == []
    assert response.experiments == []
    assert response.citations == []

def test_copilot_response_invalid_missing_fields():
    with pytest.raises(ValidationError):
        # Missing required 'answer'
        CopilotResponse.model_validate({"claims": []})

def test_copilot_experiment_missing_sql():
    payload = {
        "answer": "Here is an experiment.",
        "experiments": [
            {
                "description": "Verify exact duplicates",
                # missing sql_query
                "expected_outcome": "Duplications"
            }
        ]
    }
    with pytest.raises(ValidationError):
        CopilotResponse.model_validate(payload)
