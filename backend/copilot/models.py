from pydantic import BaseModel, Field
from typing import List, Optional

class CopilotCitation(BaseModel):
    """
    References an explicit deterministic fact from DataForge's internal state.
    """
    id: str = Field(description="A unique local ID for this citation within the response (e.g. 'c1').")
    source_type: str = Field(description="Must be one of: 'Evidence', 'Attribution', 'Observation', 'ValidationResult', 'Finding'.")
    reference_id: str = Field(description="The actual UUID/ID of the deterministic entity.")
    context: str = Field(description="Short human-readable context of what this citation represents.")

class CopilotClaim(BaseModel):
    """
    A factual statement made by the AI, which MUST be backed by citations.
    """
    text: str = Field(description="The factual claim being asserted.")
    citation_ids: List[str] = Field(description="List of citation IDs from the response's citations array that back this claim.")

class CopilotHypothesisDraft(BaseModel):
    """
    A suggested hypothesis that the engineer can approve to be added to the investigation graph.
    """
    description: str = Field(description="The hypothesis text.")
    rationale: str = Field(description="Why the AI thinks this hypothesis is plausible.")
    attribution_id: Optional[str] = Field(default=None, description="The ID of the historical attribution this hypothesis relates to, if any.")

class CopilotExperimentDraft(BaseModel):
    """
    A read-only SQL query draft designed to find evidence for a hypothesis.
    """
    description: str = Field(description="What this query aims to find.")
    sql_query: str = Field(description="A READ-ONLY (SELECT) SQL query.")
    expected_outcome: str = Field(description="What result from this query would support the hypothesis.")
    hypothesis_index: Optional[int] = Field(default=None, description="Index of the hypothesis in the response this experiment targets.")

class CopilotResponse(BaseModel):
    """
    The strict contract for all AI Copilot interactions. 
    Guarantees structural separation of analysis, claims, hypotheses, and experiments.
    """
    answer: str = Field(description="The conversational, natural language response to the user's query.")
    claims: List[CopilotClaim] = Field(default_factory=list, description="Factual claims made in the answer, independently mapped to citations.")
    hypotheses: List[CopilotHypothesisDraft] = Field(default_factory=list, description="Suggested hypotheses.")
    experiments: List[CopilotExperimentDraft] = Field(default_factory=list, description="Suggested read-only SQL validation queries.")
    citations: List[CopilotCitation] = Field(default_factory=list, description="The deterministic facts underpinning the response.")
