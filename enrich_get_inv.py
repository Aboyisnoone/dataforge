import re

with open('backend/api/routes/investigations.py', 'r') as f:
    text = f.read()

bad_str = '''@router.get("/{id}", response_model=InvestigationResponse)
def get_investigation(id: str, db: Session = Depends(get_db)):
    repo = InvestigationRepository(db)
    inv, recommendations = repo.get(id)
    
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    return InvestigationResponse('''

good_str = '''@router.get("/{id}", response_model=InvestigationResponse)
def get_investigation(id: str, db: Session = Depends(get_db)):
    repo = InvestigationRepository(db)
    from backend.persistence.repositories.datasets import DatasetRepository
    ds_repo = DatasetRepository(db)
    
    inv, recommendations = repo.get(id)
    
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    ds_name = "Unknown Dataset"
    ds_version_num = 0
    dv = ds_repo.get_version_by_id(inv.dataset_version)
    if dv:
        ds_version_num = dv.version_number
        ds = ds_repo.get_dataset_by_id(dv.dataset_id)
        if ds:
            ds_name = ds.name

    highest_severity = None
    severity_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    max_sev_val = 0
    for f in inv.findings:
        val = severity_map.get(f.severity.value, 0)
        if val > max_sev_val:
            max_sev_val = val
            highest_severity = f.severity.value

    strong_cands = sum(1 for h in inv.hypotheses if h.status.value == "SUPPORTED")
        
    return InvestigationResponse(
        dataset_name=ds_name,
        dataset_version_number=ds_version_num,
        highest_severity=highest_severity,
        strong_candidates_count=strong_cands,'''

text = text.replace(bad_str, good_str)

with open('backend/api/routes/investigations.py', 'w') as f:
    f.write(text)
