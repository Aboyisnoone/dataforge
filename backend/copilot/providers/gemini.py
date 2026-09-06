import os
import logging
from core.config import settings
from google import genai
from google.genai import types
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.copilot.providers.base import LLMProvider
from backend.copilot.models import CopilotResponse
from backend.copilot.context import CopilotContext

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
You are an expert Data Engineer AI Copilot for DataForge.
Your job is to reason over the provided deterministic investigation graph and answer the user's questions.

CRITICAL RULES:
1. Never invent evidence, metrics, or column names not present in the context.
2. Every factual claim you make MUST be backed by a specific citation_id from the context.
3. If proposing an experiment, draft READ-ONLY (SELECT) SQL queries. NEVER generate INSERT, UPDATE, DELETE, or DROP.
4. You cannot confirm or declare a root cause as 'SUPPORTED'. Only the deterministic engine can do that. You may only rank things as plausible candidates pending validation.
5. You may receive 'historical_memories' in the context. You MUST treat past resolved investigations as PRECEDENT, never as current proof. You may suggest hypotheses based on past resolutions, but explicitly state that it must be validated for the current incident.
"""

class LLMProviderError(Exception):
    pass

class LLMRateLimitError(LLMProviderError):
    pass

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "gemini-3.6-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Cannot initialize Copilot.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(LLMRateLimitError),
        reraise=True
    )
    def generate(self, context: CopilotContext, user_prompt: str) -> CopilotResponse:
        prompt_content = f"""
        INVESTIGATION CONTEXT (IMMUTABLE FACTS):
        {context.model_dump_json(indent=2)}

        USER QUESTION:
        {user_prompt}
        """

        # Hard limit on context window to prevent massive dataset leaks or cost spikes
        MAX_CHARS = 100_000
        if len(prompt_content) > MAX_CHARS:
            logger.warning("Context size exceeded limit", extra={"length": len(prompt_content)})
            raise ValueError(f"Context exceeds the maximum allowed length of {MAX_CHARS} characters.")

        logger.info("Sending request to Gemini API", extra={
            "investigation_id": context.investigation_id,
            "prompt_length": len(prompt_content),
            "model": self.model
        })

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CopilotResponse,
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_LOW_AND_ABOVE",
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_HATE_SPEECH",
                            threshold="BLOCK_LOW_AND_ABOVE",
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_HARASSMENT",
                            threshold="BLOCK_LOW_AND_ABOVE",
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            threshold="BLOCK_LOW_AND_ABOVE",
                        )
                    ]
                )
            )

            if not response.text:
                raise ValueError("Received empty response from Gemini.")

            if response.usage_metadata:
                logger.info("Gemini usage metadata", extra={
                    "telemetry": {
                        "type": "llm_usage",
                        "provider": "gemini",
                        "model": self.model,
                        "prompt_tokens": response.usage_metadata.prompt_token_count,
                        "completion_tokens": response.usage_metadata.candidates_token_count,
                        "total_tokens": response.usage_metadata.total_token_count
                    }
                })

            return CopilotResponse.model_validate_json(response.text)
            
        except ValidationError as e:
            logger.error("LLM Structural Violation", extra={"error": str(e)})
            raise RuntimeError(f"Gemini returned a malformed structured response: {str(e)}")
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "rate" in error_str:
                logger.warning(f"Gemini Rate Limit hit, triggering retry. Error: {str(e)}")
                raise LLMRateLimitError(f"Rate limited by provider: {str(e)}")
            
            logger.error(f"LLM Provider Failure: {str(e)}")
            raise LLMProviderError(f"Failed to generate copilot response: {str(e)}")

