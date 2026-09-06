import pytest
from backend.copilot.models import CopilotResponse, CopilotClaim, CopilotCitation, CopilotHypothesisDraft, CopilotExperimentDraft
from backend.copilot.context import CopilotContext
from backend.copilot.validator import CopilotValidator

@pytest.fixture
def mock_context():
    return CopilotContext(
        investigation_id="inv_123",
        user_query="Why did this happen?",
        synthesis_markdown="# Synthesis\nCandidates: PLAUSIBLE.",
        schema_context={"user_id": "VARCHAR", "revenue": "FLOAT"},
        active_hypotheses=[
            {"id": "hyp_1", "description": "A bug", "status": "PROPOSED", "validation_note": None, "attribution_id": None}
        ],
        evidence_catalog=[
            {"id": "ev_1", "attached_to": "f_1", "type": "QUERY", "metric": "row_count", "description": "Query"}
        ],
        attributions=[
            {"id": "attr_1", "finding_id": "f_1", "reason": "Change", "confidence": 0.9, "relevance": "HIGH"}
        ]
    )

def test_grounded_answer(mock_context):
    response = CopilotResponse(
        answer="The row_count dropped.",
        claims=[CopilotClaim(text="Dropped by 10%.", citation_ids=["c1"])],
        hypotheses=[],
        experiments=[],
        citations=[CopilotCitation(id="c1", source_type="Evidence", reference_id="ev_1", context="Drop in rows")]
    )
    # Should not raise
    CopilotValidator.validate(response, mock_context)

def test_invented_column(mock_context):
    response = CopilotResponse(
        answer="The column 'fake_id' dropped.",
        claims=[],
        hypotheses=[],
        experiments=[],
        citations=[]
    )
    with pytest.raises(ValueError, match="Copilot invented column: 'fake_id' is not in the dataset schema"):
        CopilotValidator.validate(response, mock_context)

def test_invented_metric(mock_context):
    response = CopilotResponse(
        answer="The metric 'magic_score' dropped.",
        claims=[],
        hypotheses=[],
        experiments=[],
        citations=[]
    )
    with pytest.raises(ValueError, match="Copilot invented metric: 'magic_score' is not recognized"):
        CopilotValidator.validate(response, mock_context)

def test_root_cause_overclaim(mock_context):
    response = CopilotResponse(
        answer="This is a strong root cause.",
        claims=[],
        hypotheses=[],
        experiments=[],
        citations=[]
    )
    # mock_context doesn't have "STRONG" in synthesis
    with pytest.raises(ValueError, match="Copilot asserted a STRONG root cause, but the deterministic engine did not provide one"):
        CopilotValidator.validate(response, mock_context)

def test_invalid_sql(mock_context):
    response = CopilotResponse(
        answer="I will drop the table.",
        claims=[],
        hypotheses=[],
        experiments=[
            CopilotExperimentDraft(
                description="Drop table",
                sql_query="DROP TABLE users;",
                expected_outcome="Gone"
            )
        ],
        citations=[]
    )
    with pytest.raises(ValueError, match="Copilot generated unsafe mutation SQL: contains 'DROP'"):
        CopilotValidator.validate(response, mock_context)

def test_unsupported_hypothesis(mock_context):
    response = CopilotResponse(
        answer="The hypothesis is confirmed.",
        claims=[],
        hypotheses=[],
        experiments=[],
        citations=[]
    )
    with pytest.raises(ValueError, match="Copilot claimed a hypothesis is confirmed, but it lacks SUPPORTED validation"):
        CopilotValidator.validate(response, mock_context)

def test_hallucinated_citation(mock_context):
    response = CopilotResponse(
        answer="Here is a claim.",
        claims=[],
        hypotheses=[],
        experiments=[],
        citations=[CopilotCitation(id="c1", source_type="Evidence", reference_id="fake_ev", context="Fake")]
    )
    with pytest.raises(ValueError, match="Copilot hallucinated citation: fake_ev"):
        CopilotValidator.validate(response, mock_context)
