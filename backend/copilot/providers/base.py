from abc import ABC, abstractmethod
from backend.copilot.models import CopilotResponse
from backend.copilot.context import CopilotContext

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, context: CopilotContext, user_prompt: str) -> CopilotResponse:
        """
        Generates a structured copilot response based on the immutable context.
        Must enforce strict JSON schema matching CopilotResponse.
        Must never execute SQL or modify the investigation.
        """
        pass
