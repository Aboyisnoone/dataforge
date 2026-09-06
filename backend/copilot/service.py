from typing import Optional
from sqlalchemy.orm import Session
from backend.persistence.repositories.investigations import InvestigationRepository
from backend.persistence.repositories.datasets import DatasetRepository
from backend.copilot.context import ContextBuilder
from backend.copilot.providers.base import LLMProvider
from backend.copilot.models import CopilotResponse
from core.investigation.synthesis import InvestigationSynthesizer
from core.diff import HistoricalDiffEngine
from core.attribution.engine import AttributionEngine
from core.attribution.root_cause import RootCauseEngine

class CopilotService:
    def __init__(self, db: Session, llm_provider: LLMProvider):
        self.db = db
        self.inv_repo = InvestigationRepository(db)
        self.ds_repo = DatasetRepository(db)
        self.llm_provider = llm_provider

    def ask(self, investigation_id: str, prompt: str, workspace_id: str = 'ws_local_dev') -> CopilotResponse:
        inv, _ = self.inv_repo.get(investigation_id, workspace_id)
        if not inv:
            raise ValueError(f"Investigation {investigation_id} not found")
            
        current_version = self.ds_repo.get_version_by_id(inv.dataset_version, workspace_id)
        if not current_version:
            raise ValueError(f"Dataset version {inv.dataset_version} not found")
            
        dataset = self.ds_repo.get_dataset_by_id(current_version.dataset_id, workspace_id)
        
        # Determine previous version
        prev_version = None
        if dataset and current_version.version_number > 1:
            prev_version = next(
                (v for v in dataset.versions if v.version_number == current_version.version_number - 1),
                None
            )
            
        # 1. Historical Diff
        diff = None
        if prev_version:
            diff_engine = HistoricalDiffEngine()
            diff = diff_engine.diff(prev_version, current_version)
            
        # 2. Attributions
        attributions = []
        if diff:
            attr_engine = AttributionEngine()
            for finding in inv.findings:
                attributions.extend(attr_engine.attribute(finding, diff))
                
        # 3. Root Cause Candidates
        rc_engine = RootCauseEngine()
        candidates = []
        for finding in inv.findings:
            finding_attributions = [a for a in attributions if a.finding_id == finding.id]
            finding_hypotheses = [h for h in inv.hypotheses if h.finding_id == finding.id]
            candidates.extend(rc_engine.rank_candidates(finding, finding_attributions, finding_hypotheses))
            
        # 4. Synthesis
        synthesizer = InvestigationSynthesizer()
        synthesis = synthesizer.synthesize(
            investigation=inv,
            diff=diff,
            attributions=attributions,
            candidates=candidates
        )
        
        # 5. Retrieve Memory
        from core.investigation.memory import MemoryEngine
        all_invs, _ = self.inv_repo.list(workspace_id=workspace_id, page_size=1000)
        
        def get_ds(dv_id):
            dv = self.ds_repo.get_version_by_id(dv_id, workspace_id)
            if not dv: return None
            return self.ds_repo.get_dataset_by_id(dv.dataset_id, workspace_id)
            
        mem_engine = MemoryEngine([i for i, _ in all_invs], get_ds)
        memories = mem_engine.retrieve_similar(inv, limit=3)
        
        # 6. Context Building
        builder = ContextBuilder()
        context = builder.build(
            user_query=prompt,
            investigation=inv,
            synthesis=synthesis,
            dataset_version=current_version,
            memories=memories
        )
        
        # 7. LLM Generation
        response = self.llm_provider.generate(context, prompt)
        
        # 8. Post-generation Safety Validation
        from backend.copilot.validator import CopilotValidator
        CopilotValidator.validate(response, context)
        
        return response
