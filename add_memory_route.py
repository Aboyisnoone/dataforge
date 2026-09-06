import re

with open('backend/api/routes/investigations.py', 'r') as f:
    text = f.read()

new_route = '''
class MemoryRetrievalSchema(BaseModel):
    investigation_id: str
    title: str
    dataset_name: str
    similarity_score: float
    matched_factors: List[str]
    resolution_root_cause: Optional[str]
    resolved_at: Optional[datetime]

@router.get("/{id}/memory", response_model=List[MemoryRetrievalSchema])
def get_investigation_memory(id: str, db: Session = Depends(get_db)):
    repo = InvestigationRepository(db)
    from backend.persistence.repositories.datasets import DatasetRepository
    ds_repo = DatasetRepository(db)
    
    current_inv, _ = repo.get(id)
    if not current_inv:
        raise HTTPException(404, "Investigation not found")
        
    all_invs = repo.list(limit=1000) # In prod we'd use vector search or DB query
    
    def get_ds(dv_id):
        dv = ds_repo.get_version_by_id(dv_id)
        if not dv: return None
        return ds_repo.get_dataset_by_id(dv.dataset_id)
        
    from core.investigation.memory import MemoryEngine
    engine = MemoryEngine([i for i, _ in all_invs], get_ds)
    similar = engine.retrieve_similar(current_inv, limit=5)
    
    return [MemoryRetrievalSchema(**s.__dict__) for s in similar]

class HypothesisValidator:
'''

text = text.replace('class HypothesisValidator:', new_route)

with open('backend/api/routes/investigations.py', 'w') as f:
    f.write(text)
