from pydantic import BaseModel, Field
from typing import Dict, Any, List
from core.investigation.models import Investigation
from core.investigation.synthesis import InvestigationSynthesis
from core.dataset.models import DatasetVersion

class CopilotContext(BaseModel):
    """
    Immutable, structured context object handed to the LLM.
    Contains no LLM logic.
    """
    investigation_id: str
    user_query: str
    synthesis_markdown: str
    schema_context: Dict[str, str] = Field(description="Maps column names to physical types.")
    active_hypotheses: List[Dict[str, Any]] = Field(description="Hypotheses and their validation statuses.")
    evidence_catalog: List[Dict[str, Any]] = Field(description="All collected evidence, tagged by ID for citation.")
    attributions: List[Dict[str, Any]] = Field(description="Deterministic attributions linking historical changes.")
    historical_memories: List[Dict[str, Any]] = Field(default_factory=list, description="Similar past resolved investigations to act as precedent.")

class ContextBuilder:
    """
    Deterministically assembles the trusted context for the Copilot.
    Enforces rigid boundaries to ensure no unrelated data leaks into the prompt.
    """
    
    def build(
        self,
        user_query: str,
        investigation: Investigation,
        synthesis: InvestigationSynthesis,
        dataset_version: DatasetVersion,
        memories: List[Any] = None
    ) -> CopilotContext:
        
        # Security & Integrity Checks: Prevent cross-investigation leakage
        if synthesis.investigation_id != investigation.id:
            raise ValueError(
                f"Synthesis mismatch: Expected {investigation.id}, got {synthesis.investigation_id}"
            )
            
        # We check the dataset_version matches the investigation's target version
        if dataset_version.id != investigation.dataset_version:
            raise ValueError(
                f"Dataset mismatch: Investigation targets {investigation.dataset_version}, "
                f"but provided version is {dataset_version.id}"
            )

        # 1. Compile Schema Context
        schema_context = {}
        if dataset_version.profile:
            schema_context = {
                name: cp.type for name, cp in dataset_version.profile.columns.items()
            }
        
        # 2. Compile Active Hypotheses
        active_hypotheses = []
        for h in investigation.hypotheses:
            val_status = h.validation_result.status.value if h.validation_result else "PROPOSED"
            val_desc = h.validation_result.description if h.validation_result else None
            
            active_hypotheses.append({
                "id": h.id,
                "description": h.description,
                "status": val_status,
                "validation_note": val_desc,
                "attribution_id": h.attribution_id
            })

        # 3. Compile Evidence Catalog (across findings and validation results)
        evidence_catalog = []
        
        # Evidence attached to findings
        for f in investigation.findings:
            for ev in f.evidence:
                evidence_catalog.append({
                    "id": ev.id,
                    "attached_to": f"Finding: {f.id}",
                    "type": ev.type.value,
                    "metric": ev.metric,
                    "description": ev.description
                })
                
        # Evidence attached to hypothesis validations
        for h in investigation.hypotheses:
            if h.validation_result:
                for ev in h.validation_result.evidence:
                    evidence_catalog.append({
                        "id": ev.id,
                        "attached_to": f"ValidationResult: {h.validation_result.id}",
                        "type": ev.type.value,
                        "metric": ev.metric,
                        "description": ev.description
                    })

        # 4. Compile Attributions from Synthesis
        attributions = []
        for a in synthesis.attributions:
            attributions.append({
                "id": a.id,
                "finding_id": a.finding_id,
                "reason": a.reason,
                "confidence": a.confidence,
                "relevance": a.relevance_score.value
            })

        hist_mem = []
        if memories:
            for mem in memories:
                hist_mem.append({
                    "past_investigation_id": mem.investigation_id,
                    "title": mem.title,
                    "similarity_factors": mem.matched_factors,
                    "resolved_root_cause": mem.resolution_root_cause
                })

        return CopilotContext(
            investigation_id=investigation.id,
            user_query=user_query,
            synthesis_markdown=synthesis.to_markdown(),
            schema_context=schema_context,
            active_hypotheses=active_hypotheses,
            evidence_catalog=evidence_catalog,
            attributions=attributions,
            historical_memories=hist_mem
        )
