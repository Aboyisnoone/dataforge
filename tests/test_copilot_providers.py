import pytest
from unittest.mock import MagicMock, patch
from backend.copilot.providers.gemini import GeminiProvider, LLMProviderError
from backend.copilot.context import CopilotContext
from backend.copilot.models import CopilotResponse
from pydantic import ValidationError

@pytest.fixture
def mock_context():
    return CopilotContext(
        investigation_id="inv_123",
        user_query="What happened?",
        synthesis_markdown="# Synthesis",
        schema_context={"col1": "INTEGER"},
        active_hypotheses=[],
        evidence_catalog=[],
        attributions=[]
    )

@pytest.mark.skip(reason="Outdated domain model")
def test_gemini_provider_success(mock_context):
    with patch("backend.copilot.providers.gemini.genai.Client") as MockClient:
        # Set up mock response
        mock_client_instance = MockClient.return_value
        mock_response = MagicMock()
        mock_response.text = """
        {
            "answer": "A factual answer",
            "claims": [],
            "hypotheses": [],
            "experiments": [],
            "citations": []
        }
        """
        mock_client_instance.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key="fake")
        response = provider.generate(mock_context, "What happened?")
        
        assert isinstance(response, CopilotResponse)
        assert response.answer == "A factual answer"
        assert len(response.claims) == 0
        
        # Ensure it called with structured outputs config
        kwargs = mock_client_instance.models.generate_content.call_args.kwargs
        assert kwargs["model"] == "gemini-2.5-flash"
        assert kwargs["config"].response_mime_type == "application/json"
        assert kwargs["config"].response_schema == CopilotResponse
        assert kwargs["config"].temperature == 0.0

def test_gemini_provider_malformed_response(mock_context):
    with patch("backend.copilot.providers.gemini.genai.Client") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_response = MagicMock()
        # Invalid JSON (missing required 'answer' field for the schema)
        mock_response.text = '{"claims": []}'
        mock_client_instance.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key="fake")
        
        with pytest.raises(RuntimeError, match="Gemini returned a malformed structured response"):
            provider.generate(mock_context, "Query")

def test_gemini_provider_empty_response(mock_context):
    with patch("backend.copilot.providers.gemini.genai.Client") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client_instance.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key="fake")
        
        with pytest.raises(LLMProviderError, match="Received empty response from Gemini"):
            provider.generate(mock_context, "Query")

def test_gemini_provider_api_error(mock_context):
    with patch("backend.copilot.providers.gemini.genai.Client") as MockClient:
        mock_client_instance = MockClient.return_value
        mock_client_instance.models.generate_content.side_effect = Exception("API Outage")
        
        provider = GeminiProvider(api_key="fake")
        
        with pytest.raises(LLMProviderError, match="Failed to generate copilot response: API Outage"):
            provider.generate(mock_context, "Query")
